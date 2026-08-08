"""Build, verify, inventory, and report a parent-reference-only prospective cohort."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from engine.evaluation.prospective_artifacts import ArtifactRef, canonical_artifact_sha256, publish_new_json
from engine.evaluation.prospective_gates import (
    CohortHoldError,
    build_cohort_manifest,
    build_future_gate_evidence_from_cohorts,
    build_gate_evidence_from_cohorts,
    build_three_gate_report,
    cohort_output_dir,
    evaluate_future_empirical,
    evaluate_prediction_capability_candidate,
    verify_cohort_manifest,
)


def _read_json(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"JSON input must be a regular non-symlink file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _raw_ref(path: Path) -> ArtifactRef:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"historical baseline must be a regular non-symlink file: {path}")
    return ArtifactRef(path.as_posix(), hashlib.sha256(path.read_bytes()).hexdigest())


def _write_new_json(path: Path, payload: object, *, dry_run: bool) -> None:
    if dry_run:
        return
    if path.exists() or path.is_symlink():
        raise ValueError(f"output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            stream.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists() or path.is_symlink():
            raise ValueError(f"output already exists: {path}")
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def _created_at(value: str | None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _emit(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def _build(args: argparse.Namespace) -> int:
    historical = [_raw_ref(args.historical_md), _raw_ref(args.historical_json)]
    try:
        manifest = build_cohort_manifest(
            args.completion,
            historical,
            created_at=_created_at(args.created_at),
            admitted_root=args.admitted_root,
        )
    except CohortHoldError as error:
        _emit(error.plan)
        return 0 if args.dry_run else 3

    target = cohort_output_dir(args.out_dir, manifest)
    manifest_path = target / "cohort-manifest.json"
    if args.dry_run:
        _emit({
            "status": "DRY_RUN",
            "manifest_path": manifest_path.as_posix(),
            "manifest": manifest,
        })
        return 0
    if target.exists() or target.is_symlink():
        if not target.is_dir() or manifest_path.is_symlink() or not manifest_path.is_file():
            raise ValueError(f"existing cohort output is not a verifiable publication: {target}")
        actual_entries = {item.name for item in target.iterdir()}
        if actual_entries != {manifest_path.name}:
            raise ValueError(f"existing cohort output contains unexpected pollution: {target}")
        existing = _read_json(manifest_path)
        verification = verify_cohort_manifest(
            existing, admitted_root=args.admitted_root
        )
        if verification["status"] != "VERIFIED" or existing != manifest:
            raise ValueError("existing cohort output differs or has parent drift")
        _emit({
            "status": "VERIFIED_EXISTING",
            "manifest_path": manifest_path.as_posix(),
            "verification": verification,
        })
        return 0
    _write_new_json(manifest_path, manifest, dry_run=False)
    _emit({"status": "CREATED", "manifest_path": manifest_path.as_posix()})
    return 0


def _verify(args: argparse.Namespace) -> int:
    manifest = _read_json(args.manifest)
    result = verify_cohort_manifest(
        manifest, admitted_root=args.admitted_root
    )
    _emit(result)
    return 0 if result["status"] == "VERIFIED" else 4


def _inventory(manifest: dict[str, Any]) -> dict[str, Any]:
    immediate = [
        {
            "case_id": member["case_id"],
            "subject_id_hash": member["subject_id_hash"],
            "completion_parent": member["parents"]["completion"],
        }
        for member in manifest["members"]
        if member["evidence_availability"]["immediate_retrospective"]
    ]
    future = [
        {
            "case_id": member["case_id"],
            "subject_id_hash": member["subject_id_hash"],
            "future_parent": member["parents"]["future"],
        }
        for member in manifest["members"]
        if member["evidence_availability"]["future_observation"]
    ]
    return {
        "schema_version": "prospective-cohort-parent-inventory/v1",
        "cohort_id": manifest["cohort_id"],
        "member_set_sha256": manifest["member_set_sha256"],
        "status": "INVENTORY_ONLY_HOLD",
        "assumed_gate_status": None,
        "classes": {
            "prediction_first_immediate_retrospective": immediate,
            "future_observation": future,
        },
    }


def _score(args: argparse.Namespace) -> int:
    manifest = _read_json(args.manifest)
    verification = verify_cohort_manifest(
        manifest, admitted_root=args.admitted_root
    )
    if verification["status"] != "VERIFIED":
        _emit(verification)
        return 4
    inventory = _inventory(manifest)
    immediate_path = args.out_dir / "immediate-parent-inventory.json"
    future_path = args.out_dir / "future-parent-inventory.json"
    if args.dry_run:
        _emit({**inventory, "dry_run": True})
        return 0
    if args.out_dir.exists() or args.out_dir.is_symlink():
        raise ValueError(f"score output directory already exists: {args.out_dir}")
    _write_new_json(immediate_path, {
        **inventory,
        "classes": {
            "prediction_first_immediate_retrospective": inventory["classes"]["prediction_first_immediate_retrospective"]
        },
    }, dry_run=False)
    if inventory["classes"]["future_observation"]:
        _write_new_json(future_path, {
            **inventory,
            "classes": {"future_observation": inventory["classes"]["future_observation"]},
        }, dry_run=False)
    _emit({
        "status": "INVENTORY_ONLY_HOLD",
        "immediate_inventory": immediate_path.as_posix(),
        "future_inventory": future_path.as_posix() if future_path.exists() else None,
        "gate_outputs_created": False,
    })
    return 0


def _gate(args: argparse.Namespace) -> int:
    if args.out.name != "prediction-capability-candidate-gate-v1.json":
        raise ValueError("gate output filename must be canonical: prediction-capability-candidate-gate-v1.json")
    evidence = build_gate_evidence_from_cohorts(
        args.manifest,
        scoring_artifact=args.scores,
        holdout_artifact=args.holdout,
        audit_artifact=args.audit,
        admitted_root=args.admitted_root,
    )
    result = evaluate_prediction_capability_candidate(
        evidence,
        evaluated_at=_created_at(args.evaluated_at),
        admitted_root=args.admitted_root,
    )
    if args.dry_run:
        _emit({"status": "DRY_RUN", "result": result, "out": args.out.as_posix()})
        return 0
    if args.out.exists() or args.out.is_symlink():
        raise ValueError(f"output already exists: {args.out}")
    publish_new_json(
        args.out,
        {key: value for key, value in result.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    _emit({"status": "CREATED", "result": result, "out": args.out.as_posix()})
    return 0


def _future_gate(args: argparse.Namespace) -> int:
    if args.out.name != "future-empirical-gate-v1.json":
        raise ValueError("future gate output filename must be canonical: future-empirical-gate-v1.json")
    evidence = build_future_gate_evidence_from_cohorts(
        args.manifest,
        scoring_artifact=args.scores,
        holdout_artifact=args.holdout,
        audit_artifact=args.audit,
        admitted_root=args.admitted_root,
    )
    result = evaluate_future_empirical(
        evidence,
        evaluated_at=_created_at(args.evaluated_at),
        admitted_root=args.admitted_root,
    )
    if args.dry_run:
        _emit({"status": "DRY_RUN", "result": result, "out": args.out.as_posix()})
        return 0
    if args.out.exists() or args.out.is_symlink():
        raise ValueError(f"output already exists: {args.out}")
    publish_new_json(
        args.out, {key: value for key, value in result.items() if key != "artifact_sha256"}, dry_run=False,
    )
    _emit({"status": "CREATED", "result": result, "out": args.out.as_posix()})
    return 0


def _validated_gate(
    path: Path, *, gate_id: str, manifest: dict[str, Any], manifest_path: Path,
) -> dict[str, Any]:
    gate = _read_json(path)
    if gate.get("gate_id") != gate_id:
        raise ValueError(f"gate artifact has wrong gate_id: expected {gate_id}")
    digest = gate.get("artifact_sha256")
    if not isinstance(digest, str) or digest != canonical_artifact_sha256(gate):
        raise ValueError(f"gate artifact canonical hash is invalid: {path}")
    expected_parent = {
        "artifact_path": manifest_path.as_posix(),
        "artifact_sha256": manifest["artifact_sha256"],
    }
    parents = gate.get("parents")
    if not isinstance(parents, list) or expected_parent not in parents:
        raise ValueError(f"gate artifact must bind the verified cohort manifest parent: {path}")
    return gate


def _report(args: argparse.Namespace) -> int:
    if args.manifest is not None:
        manifest = _read_json(args.manifest)
        verification = verify_cohort_manifest(
            manifest, admitted_root=args.admitted_root
        )
        if verification["status"] != "VERIFIED":
            _emit(verification)
            return 4
        immediate = _validated_gate(
            args.immediate_gate, gate_id="prediction_capability_candidate_gate_v1",
            manifest=manifest, manifest_path=args.manifest,
        )
        future = _validated_gate(
            args.future_gate, gate_id="future_empirical_gate_v1",
            manifest=manifest, manifest_path=args.manifest,
        )
        payload = {
            "schema_version": "prospective-cohort-task9-report/v1",
            "cohort": {
                "cohort_id": manifest["cohort_id"],
                "member_set_sha256": manifest["member_set_sha256"],
            },
            "status": "HOLD_PENDING_TASK_10_AND_11_GATE_EVALUATION",
            "gate_parent_refs": [
                _raw_ref(args.immediate_gate).__dict__, _raw_ref(args.future_gate).__dict__,
            ],
            "observed_gate_statuses": {
                "immediate": immediate.get("status"), "future": future.get("status"),
            },
            "production_switch": False,
        }
        payload["artifact_sha256"] = canonical_artifact_sha256(payload)
        _write_new_json(args.out, payload, dry_run=args.dry_run)
        _emit({"status": "DRY_RUN" if args.dry_run else "CREATED", "report": payload})
        return 0
    if args.historical_json is None:
        raise ValueError("three-gate report requires --historical-json")
    if args.out.name != "three-gate-report-v1.md":
        raise ValueError("report output filename must be canonical: three-gate-report-v1.md")
    immediate = _read_json(args.immediate_gate)
    future = _read_json(args.future_gate)
    text = build_three_gate_report(
        immediate,
        future,
        _raw_ref(args.historical_json),
        admitted_root=args.admitted_root,
    )
    if args.dry_run:
        print(text, end="")
        return 0
    if args.out.exists() or args.out.is_symlink():
        raise ValueError(f"output already exists: {args.out}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8", newline="")
    _emit({"status": "CREATED", "out": args.out.as_posix()})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage parent-reference-only prospective cohorts")
    commands = parser.add_subparsers(dest="command", required=True)

    def require_admitted_root(command: argparse.ArgumentParser) -> None:
        command.add_argument("--admitted-root", type=Path, required=True)

    build = commands.add_parser("build")
    build.add_argument("--completion", type=Path, action="append", required=True)
    build.add_argument("--historical-md", type=Path, required=True)
    build.add_argument("--historical-json", type=Path, required=True)
    build.add_argument("--out-dir", type=Path, required=True)
    build.add_argument("--created-at")
    build.add_argument("--dry-run", action="store_true")
    require_admitted_root(build)
    build.set_defaults(handler=_build)

    verify = commands.add_parser("verify")
    verify.add_argument("--manifest", type=Path, required=True)
    require_admitted_root(verify)
    verify.set_defaults(handler=_verify)

    score = commands.add_parser("score")
    score.add_argument("--manifest", type=Path, required=True)
    score.add_argument("--out-dir", type=Path, required=True)
    score.add_argument("--dry-run", action="store_true")
    require_admitted_root(score)
    score.set_defaults(handler=_score)

    gate = commands.add_parser("gate")
    gate.add_argument("--manifest", type=Path, action="append", required=True)
    gate.add_argument("--scores", type=Path, required=True)
    gate.add_argument("--holdout", type=Path, required=True)
    gate.add_argument("--audit", type=Path, required=True)
    gate.add_argument("--evaluated-at")
    gate.add_argument("--out", type=Path, required=True)
    gate.add_argument("--dry-run", action="store_true")
    require_admitted_root(gate)
    gate.set_defaults(handler=_gate)

    future_gate = commands.add_parser("future-gate")
    future_gate.add_argument("--manifest", type=Path, action="append", required=True)
    future_gate.add_argument("--scores", type=Path, required=True)
    future_gate.add_argument("--holdout", type=Path, required=True)
    future_gate.add_argument("--audit", type=Path, required=True)
    future_gate.add_argument("--evaluated-at")
    future_gate.add_argument("--out", type=Path, required=True)
    future_gate.add_argument("--dry-run", action="store_true")
    require_admitted_root(future_gate)
    future_gate.set_defaults(handler=_future_gate)

    report = commands.add_parser("report")
    report.add_argument("--manifest", type=Path)
    report.add_argument("--immediate-gate", type=Path, required=True)
    report.add_argument("--future-gate", type=Path, required=True)
    report.add_argument("--historical-json", type=Path)
    report.add_argument("--out", type=Path, required=True)
    report.add_argument("--dry-run", action="store_true")
    require_admitted_root(report)
    report.set_defaults(handler=_report)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except (FileNotFoundError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
