"""Build a deterministic staged frozen run from a verified prospective blind bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from engine.claims.orchestrator import generate_blind_outputs
from engine.evaluation.freeze import canonical_json, freeze_outputs, verify_frozen_run
from engine.evaluation.models import BlindSchoolOutput, BlindTask, FrozenBlindRun
from tools.school_capability_dataset import (
    append_witness_event,
    validate_canonical_chart,
    verify_witness_registry,
)

_BUNDLE_SCHEMA = "school-capability-blind-bundle/v1"
_INTAKE_SCHEMA = "school-capability-blind-intake/v1"
_STAGED_SCHEMA = "school-capability-prospective-staged-run/v1"
_TASK_SCHEMA = "school-capability-cli-tasks/v1"
_FORMAL_INTAKE_SCHEMA = "school-capability-prospective-intake/v1"
_WITNESS_EVENT_TYPES = ("registered", "prepared", "freeze")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _verified_bundle(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError("bundle root must be an existing non-symlink directory")
    manifest = _read_json(root / "bundle-manifest.json")
    if set(manifest) != {"schema_version", "bundle_sha256", "files"} or manifest.get("schema_version") != _BUNDLE_SCHEMA or not isinstance(manifest.get("files"), dict):
        raise ValueError("blind bundle manifest schema is invalid")
    files = manifest["files"]
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.relative_to(root).as_posix() != "bundle-manifest.json"
    }
    if actual != set(files):
        raise ValueError("actual bundle files do not match manifest")
    for name, expected in files.items():
        path = root / name
        if path.is_symlink() or not isinstance(expected, str) or len(expected) != 64:
            raise ValueError(f"invalid bundle file entry: {name}")
        if _sha256(path.read_bytes()) != expected:
            raise ValueError(f"actual bundle file hash mismatch: {name}")
    encoded_files = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if _sha256(encoded_files) != manifest["bundle_sha256"]:
        raise ValueError("blind bundle hash mismatch")
    return manifest, _read_json(root / "tasks.json"), _read_json(root / "rule-snapshot.json"), _read_json(root / "intake.json")


def _tasks(document: dict[str, Any]) -> tuple[str, dict[str, BlindTask]]:
    if document.get("schema_version") != _TASK_SCHEMA or not isinstance(document.get("task_catalog_version"), str):
        raise ValueError("bundled task catalog schema/version is invalid")
    rows = document.get("tasks")
    if not isinstance(rows, list):
        raise ValueError("bundled task catalog requires tasks")
    tasks = [BlindTask.from_dict({**row, "evaluation_note": row.get("evaluation_note", "")}) for row in rows]
    indexed = {task.task_id: task for task in tasks}
    if len(indexed) != len(tasks):
        raise ValueError("bundled task catalog has duplicate task_id")
    return document["task_catalog_version"], indexed


def _contract_safe(output: BlindSchoolOutput, task: BlindTask) -> BlindSchoolOutput:
    if output.state != "claim":
        return output
    predictions = output.predictions
    if task.scoring_method == "multiclass_probability":
        expected = set(task.label_schema.get("labels", ()))
        actual = {prediction.event_label for prediction in predictions}
        if actual != expected or abs(sum(prediction.probability for prediction in predictions) - 1.0) > 1e-9:
            return BlindSchoolOutput(output.case_id, output.school_id, output.task_id, "abstain", "runner claim rejected by frozen scoring contract")
    return output


def build_staged_frozen_run(bundle_root: Path) -> dict[str, Any]:
    root = Path(bundle_root)
    manifest, task_document, snapshot, intake = _verified_bundle(root)
    task_version, task_map = _tasks(task_document)
    if set(intake) != {"schema_version", "schools", "records"} or intake.get("schema_version") != _INTAKE_SCHEMA:
        raise ValueError("bundled intake schema is invalid")
    schools = intake.get("schools")
    if not isinstance(schools, list) or not schools or len(set(schools)) != len(schools):
        raise ValueError("bundled schools are invalid")
    snapshot_schools = snapshot.get("schools")
    if (
        not isinstance(snapshot_schools, list)
        or set(schools) != set(snapshot_schools)
        or set(snapshot.get("runners", {})) != set(snapshot_schools)
    ):
        raise ValueError("bundled schools do not match rule snapshot")
    schools = snapshot_schools
    snapshot_id = snapshot.get("rule_snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise ValueError("bundled rule snapshot id is invalid")
    records = intake.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("bundled intake requires records")
    outputs: list[BlindSchoolOutput] = []
    assignments: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in sorted(records, key=lambda item: item.get("case_id", "")):
        if not isinstance(row, dict) or set(row) != {"case_id", "task_ids"}:
            raise ValueError("bundled intake record is invalid")
        case_id, task_ids = row["case_id"], row["task_ids"]
        if not isinstance(case_id, str) or case_id in seen or not isinstance(task_ids, list) or not task_ids or len(set(task_ids)) != len(task_ids):
            raise ValueError("bundled intake record values are invalid")
        seen.add(case_id)
        unknown = set(task_ids) - set(task_map)
        if unknown:
            raise ValueError(f"unknown bundled task: {sorted(unknown)[0]}")
        chart = validate_canonical_chart(_read_json(root / f"cases/{case_id}/chart.json"), case_id)
        selected = [task_map[task_id] for task_id in sorted(task_ids)]
        generated: list[BlindSchoolOutput] = []
        for school in schools:
            for task in selected:
                try:
                    output = generate_blind_outputs(chart, [task], case_id=case_id, schools=[school])[0]
                except ValueError as error:
                    if "is not allowed for task" not in str(error):
                        raise
                    output = BlindSchoolOutput(
                        case_id, school, task.task_id, "abstain",
                        f"runner claim rejected by frozen task contract: {error}",
                    )
                generated.append(output)
        outputs.extend(_contract_safe(output, task_map[output.task_id]) for output in generated)
        assignments.append({"case_id": case_id, "task_ids": sorted(task_ids)})
    task_hash = manifest["files"]["tasks.json"]
    rule_hash = manifest["files"]["rule-snapshot.json"]
    bundle_frozen_at = datetime.fromtimestamp(
        (root / "bundle-manifest.json").stat().st_mtime_ns / 1_000_000_000,
        timezone.utc,
    ).isoformat(timespec="microseconds").replace("+00:00", "Z")
    run = freeze_outputs(
        outputs,
        f"{task_version}@sha256:{task_hash}",
        f"{snapshot_id}@sha256:{rule_hash}",
        frozen_at=bundle_frozen_at,
    )
    verify_frozen_run(run)
    payload: dict[str, Any] = {
        "schema_version": _STAGED_SCHEMA,
        "bundle_sha256": manifest["bundle_sha256"],
        "task_catalog_sha256": task_hash,
        "rule_snapshot_sha256": rule_hash,
        "case_task_assignments": assignments,
        "frozen_run": run.to_dict(),
    }
    return {**payload, "artifact_sha256": _sha256(canonical_json(payload).encode("utf-8"))}


def _parse_utc(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"{field} must be an ISO 8601 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO 8601 UTC timestamp") from error
    if parsed.tzinfo != timezone.utc:
        raise ValueError(f"{field} must be an ISO 8601 UTC timestamp")
    return parsed


def _utc(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _verified_staged_artifact(path: Path, manifest: dict[str, Any]) -> tuple[dict[str, Any], FrozenBlindRun, set[str]]:
    artifact = _read_json(path)
    required = {
        "schema_version", "bundle_sha256", "task_catalog_sha256", "rule_snapshot_sha256",
        "case_task_assignments", "frozen_run", "artifact_sha256",
    }
    if set(artifact) != required or artifact.get("schema_version") != _STAGED_SCHEMA:
        raise ValueError("staged artifact schema is invalid")
    unsigned = {key: value for key, value in artifact.items() if key != "artifact_sha256"}
    if artifact.get("artifact_sha256") != _sha256(canonical_json(unsigned).encode("utf-8")):
        raise ValueError("staged artifact hash mismatch")
    if (
        artifact.get("bundle_sha256") != manifest["bundle_sha256"]
        or artifact.get("task_catalog_sha256") != manifest["files"].get("tasks.json")
        or artifact.get("rule_snapshot_sha256") != manifest["files"].get("rule-snapshot.json")
    ):
        raise ValueError("staged artifact hash does not match verified bundle")
    run = FrozenBlindRun.from_dict(artifact.get("frozen_run"))
    verify_frozen_run(run)
    assignments = artifact.get("case_task_assignments")
    if not isinstance(assignments, list) or any(
        not isinstance(row, dict) or set(row) != {"case_id", "task_ids"}
        for row in assignments
    ):
        raise ValueError("staged artifact case assignments are invalid")
    cases = {row["case_id"] for row in assignments}
    if len(cases) != len(assignments) or {output.case_id for output in run.outputs} != cases:
        raise ValueError("staged artifact case set is inconsistent")
    return artifact, run, cases


def _validate_existing_witness_prefix(registry: dict[str, Any], key: bytes) -> set[str]:
    verify_witness_registry(registry, key)
    events = registry["events"]
    completed: set[str] = set()
    for offset in range(0, len(events), 3):
        segment = events[offset:offset + 3]
        if len(segment) != 3 or tuple(event["event_type"] for event in segment) != _WITNESS_EVENT_TYPES:
            raise ValueError("existing witness events must be complete registered -> prepared -> freeze segments")
        case_ids = {event["payload"]["case_id"] for event in segment}
        if len(case_ids) != 1:
            raise ValueError("existing witness segment case set is inconsistent")
        case_id = next(iter(case_ids))
        if case_id in completed:
            raise ValueError(f"existing witness contains duplicate case: {case_id}")
        times = [_parse_utc(event["occurred_at"], "witness occurred_at") for event in segment]
        if not times[0] < times[1] < times[2]:
            raise ValueError("existing witness event order is invalid")
        completed.add(case_id)
    return completed


def build_witness_freeze_registry(
    intake_path: Path,
    bundle_root: Path,
    staged_run_path: Path,
    witness_key: bytes,
    *,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build or append exact per-case registered/prepared/freeze witness segments."""
    intake = _read_json(Path(intake_path))
    if (
        intake.get("schema_version") != _FORMAL_INTAKE_SCHEMA
        or not isinstance(intake.get("records"), list)
        or not intake["records"]
    ):
        raise ValueError("formal prospective intake schema is invalid")
    registered_at = _parse_utc(intake.get("generated_at"), "intake generated_at")
    manifest, _, _, blind_intake = _verified_bundle(Path(bundle_root))
    _, run, staged_cases = _verified_staged_artifact(Path(staged_run_path), manifest)
    rows: dict[str, dict[str, Any]] = {}
    for row in intake["records"]:
        if not isinstance(row, dict) or set(row) != {
            "case_id", "input_file", "input_sha256", "subject_id_hash", "task_ids",
        } or row.get("case_id") in rows:
            raise ValueError("formal prospective intake record is invalid")
        input_path = Path(row["input_file"])
        if not input_path.is_file() or input_path.is_symlink() or _sha256(input_path.read_bytes()) != row["input_sha256"]:
            raise ValueError(f"formal intake input hash mismatch: {row.get('case_id')}")
        rows[row["case_id"]] = row
    bundle_cases = {row.get("case_id") for row in blind_intake.get("records", [])}
    chart_cases = {
        name.split("/")[1]
        for name in manifest["files"]
        if name.startswith("cases/") and name.endswith("/chart.json")
    }
    if set(rows) != bundle_cases or set(rows) != chart_cases or set(rows) != staged_cases:
        raise ValueError("intake, bundle, and staged artifact case sets do not match")
    frozen_at = _parse_utc(run.frozen_at, "frozen_run.frozen_at")
    if frozen_at - registered_at < timedelta(microseconds=2):
        raise ValueError("freeze time must leave room for strictly increasing witness events")
    prepared_at = registered_at + (frozen_at - registered_at) / 2
    current = registry
    if current is not None:
        existing_cases = _validate_existing_witness_prefix(current, witness_key)
        overlap = existing_cases & set(rows)
        if overlap:
            raise ValueError(f"existing witness already contains case: {sorted(overlap)[0]}")
    for case_id in sorted(rows):
        row = rows[case_id]
        events = (
            {
                "event_type": "registered", "occurred_at": _utc(registered_at),
                "payload": {
                    "case_id": case_id,
                    "input_sha256": row["input_sha256"],
                    "subject_id_hash": row["subject_id_hash"],
                },
            },
            {
                "event_type": "prepared", "occurred_at": _utc(prepared_at),
                "payload": {"case_id": case_id, "bundle_sha256": manifest["bundle_sha256"]},
            },
            {
                "event_type": "freeze", "occurred_at": run.frozen_at,
                "payload": {"case_id": case_id, "freeze_hash": run.freeze_hash},
            },
        )
        for event in events:
            current = append_witness_event(current, event, witness_key)
    assert current is not None
    verify_witness_registry(current, witness_key)
    return current


def _environment_witness_key(variable: str) -> bytes:
    value = os.environ.get(variable)
    if not value:
        raise ValueError(f"witness key environment variable is missing: {variable}")
    return value.encode("utf-8")


def _write_new(path: Path, payload: dict[str, Any]) -> None:
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
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    stage = commands.add_parser("stage-frozen-run")
    stage.add_argument("--bundle-root", required=True)
    stage.add_argument("--out", required=True)
    stage.add_argument("--dry-run", action="store_true")
    witness = commands.add_parser("witness-freeze-chain")
    witness.add_argument("--intake", required=True)
    witness.add_argument("--bundle-root", required=True)
    witness.add_argument("--staged-run", required=True)
    witness.add_argument("--registry")
    witness.add_argument("--out", required=True)
    witness.add_argument("--witness-key-env", default="SCHOOL_CAPABILITY_WITNESS_KEY")
    witness.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "stage-frozen-run":
        payload = build_staged_frozen_run(Path(args.bundle_root))
        result = payload["artifact_sha256"]
    else:
        existing = _read_json(Path(args.registry)) if args.registry else None
        payload = build_witness_freeze_registry(
            Path(args.intake), Path(args.bundle_root), Path(args.staged_run),
            _environment_witness_key(args.witness_key_env), registry=existing,
        )
        result = payload["events"][-1]["event_hash"]
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _write_new(Path(args.out), payload)
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
