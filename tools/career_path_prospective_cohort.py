"""真正未见职业路径 cohort 的采集、隔离、双审、裁决与受控准入。

本工具不推断标签、不运行模型、不评分、不切换生产。所有写操作默认 dry-run，
正式写入必须显式 ``--write``，且只允许 create-only 普通文件/目录。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any, Sequence

DEFAULT_REGISTRY = Path("META/as-of-evaluation/career-path-dataset-registry-v1.json")
HUMAN_ID = re.compile(r"^human-[A-Za-z0-9][A-Za-z0-9._-]*$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SAFE_INTAKE_FIELDS = {
    "case_id", "pillars", "sex", "birth", "chart_source", "as_of_date", "dayun_intervals"
}
FORBIDDEN_KEYS = {
    "occupation", "feedback", "known_fact", "known_facts", "knownfacts", "label", "labels",
    "career_label", "report", "reports", "model_prediction", "model_predictions", "prediction",
    "predictions", "reality_state", "reality_status", "reality", "status",
}
LABELS = {"employment", "entrepreneurship", "mixed", "unknown"}
BINARY_LABELS = {"employment", "entrepreneurship"}
REALITY_STATES = {"employed", "entrepreneurial", "mixed", "transitioning", "unknown"}
PILLAR_KEYS = {"year", "month", "day", "hour"}


def _normal_key(value: object) -> str:
    return re.sub(r"[\s-]+", "_", str(value).strip().lower())


def _canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    path = Path(path)
    _reject_symlink_chain(path, "input path")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def _timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO-8601 timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include timezone")
    return parsed


def _date(value: object, field: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO date") from exc


def _require_human(value: object, role: str) -> str:
    if not isinstance(value, str) or not HUMAN_ID.fullmatch(value):
        raise ValueError(f"{role} must identify a human using human-*")
    return value


def _reject_symlink_chain(path: Path, description: str) -> None:
    current = Path(path)
    while True:
        if current.is_symlink():
            raise ValueError(f"{description} must not contain a symlink: {current}")
        if current.parent == current:
            return
        current = current.parent


def _write_new(path: Path, content: bytes, *, write: bool) -> None:
    path = Path(path)
    _reject_symlink_chain(path, "output path")
    if path.exists() or path.is_symlink():
        raise ValueError(f"output target must not exist: {path}")
    if not write:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    _reject_symlink_chain(path.parent, "output parent")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.rename(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _write_new_json(path: Path, value: object, *, write: bool) -> None:
    _write_new(path, json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8") + b"\n", write=write)


def _assert_no_leakage(value: object, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if _normal_key(key) in FORBIDDEN_KEYS:
                raise ValueError(f"intake leakage field at {path}.{key}")
            _assert_no_leakage(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_leakage(child, f"{path}[{index}]")


def _validate_pillars(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != PILLAR_KEYS:
        raise ValueError("pillars must contain exactly year, month, day, hour")
    if any(not isinstance(item, str) or len(item.strip()) != 2 for item in value.values()):
        raise ValueError("each pillar must be a two-character Ganzhi string")
    return {key: str(value[key]).strip() for key in ("year", "month", "day", "hour")}


def identity_fingerprint(payload: dict[str, Any]) -> str:
    pillars = _validate_pillars(payload.get("pillars"))
    sex = payload.get("sex")
    if sex not in {"乾", "坤"}:
        raise ValueError("sex must be 乾 or 坤")
    stable = {"sex": sex, "pillars": pillars}
    return canonical_sha256(stable)


def _development_identity(registry: dict[str, Any]) -> tuple[set[str], set[str]]:
    datasets = registry.get("development_datasets")
    if not isinstance(datasets, list):
        raise ValueError("registry.development_datasets must be a list")
    ids: set[str] = set()
    fingerprints: set[str] = set()
    for dataset in datasets:
        if not isinstance(dataset, dict) or dataset.get("classification") != "development_replay_only":
            raise ValueError("development datasets must be development_replay_only")
        if dataset.get("promotion_eligible") is not False or dataset.get("holdout_eligible") is not False:
            raise ValueError("development datasets must remain excluded")
        ids.update(str(value) for value in dataset.get("case_ids", []))
        for identity in dataset.get("identities", []):
            if isinstance(identity, str):
                fingerprints.add(hashlib.sha256(identity.encode("utf-8")).hexdigest())
        fingerprints.update(str(value) for value in dataset.get("identity_fingerprints", []))
    return ids, fingerprints


def validate_temporal_observation(observation: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(observation, dict):
        raise ValueError("temporal observation must be an object")
    required = {"case_id", "as_of_date", "reality_state", "dayun_intervals", "career_transition_events"}
    if set(observation) != required:
        raise ValueError("temporal observation fields mismatch")
    _date(observation["as_of_date"], "as_of_date")
    if observation["reality_state"] not in REALITY_STATES:
        raise ValueError("reality_state is invalid")
    intervals = observation["dayun_intervals"]
    if not isinstance(intervals, list):
        raise ValueError("dayun_intervals must be a list")
    previous_end: date | None = None
    for index, interval in enumerate(intervals):
        if not isinstance(interval, dict) or set(interval) != {"start", "end", "pillar"}:
            raise ValueError("dayun interval fields mismatch")
        start = _date(interval["start"], f"dayun_intervals[{index}].start")
        end = _date(interval["end"], f"dayun_intervals[{index}].end")
        if start > end:
            raise ValueError("dayun closed interval start must not exceed end")
        if previous_end is not None and start <= previous_end:
            raise ValueError("dayun closed intervals must not overlap")
        previous_end = end
    events = observation["career_transition_events"]
    if not isinstance(events, list):
        raise ValueError("career_transition_events must be a list")
    for event in events:
        if not isinstance(event, dict) or set(event) != {"date", "state", "verified_by"}:
            raise ValueError("career transition event fields mismatch")
        _date(event["date"], "career transition event date")
        if event["state"] not in REALITY_STATES:
            raise ValueError("career transition event state is invalid")
        _require_human(event["verified_by"], "career transition event verified_by")
    return observation


def _validate_safe_intake(payload: dict[str, Any]) -> None:
    _assert_no_leakage(payload)
    unknown = set(payload) - SAFE_INTAKE_FIELDS
    missing = {"case_id", "pillars", "sex", "as_of_date", "dayun_intervals"} - set(payload)
    if unknown or missing:
        raise ValueError(f"intake field mismatch; unknown={sorted(unknown)}, missing={sorted(missing)}")
    if not isinstance(payload["case_id"], str) or not payload["case_id"].strip():
        raise ValueError("case_id is required")
    identity_fingerprint(payload)
    _date(payload["as_of_date"], "as_of_date")
    temporal_shape = {
        "case_id": payload["case_id"],
        "as_of_date": payload["as_of_date"],
        "reality_state": "unknown",
        "dayun_intervals": payload["dayun_intervals"],
        "career_transition_events": [],
    }
    validate_temporal_observation(temporal_shape)


def intake_candidate(
    source: Path,
    output: Path,
    *,
    registry: dict[str, Any] | None = None,
    registry_path: Path = DEFAULT_REGISTRY,
    write: bool = False,
    ingested_at: str | None = None,
) -> dict[str, Any]:
    """Whitelist one real blind-safe candidate and bind its original bytes."""
    source = Path(source)
    _reject_symlink_chain(source, "source path")
    payload = _read_json(source)
    _validate_safe_intake(payload)
    registry = registry if registry is not None else _read_json(registry_path)
    development_ids, development_fingerprints = _development_identity(registry)
    fingerprint = identity_fingerprint(payload)
    if payload["case_id"] in development_ids or fingerprint in development_fingerprints:
        raise ValueError("candidate overlaps development data")
    timestamp = ingested_at or datetime.now().astimezone().isoformat()
    _timestamp(timestamp, "ingested_at")
    record = {
        "schema_version": "career-path-prospective-intake/v1",
        "case_id": payload["case_id"],
        "safe_input": payload,
        "identity_fingerprint": fingerprint,
        "source_path": str(source.resolve()),
        "source_sha256": _file_sha256(source),
        "ingested_at": timestamp,
        "labels_revealed": False,
        "development_replay_only_excluded": True,
        "formal_scoring_permitted": False,
        "production_switch_permitted": False,
    }
    _write_new_json(Path(output), record, write=write)
    return record


def _validate_intake_record(path: Path) -> dict[str, Any]:
    record = _read_json(path)
    if record.get("schema_version") != "career-path-prospective-intake/v1":
        raise ValueError("intake schema mismatch")
    source = Path(str(record.get("source_path")))
    _reject_symlink_chain(source, "bound source path")
    if not source.is_file() or _file_sha256(source) != record.get("source_sha256"):
        raise ValueError("bound source hash mismatch")
    safe_input = record.get("safe_input")
    if not isinstance(safe_input, dict):
        raise ValueError("safe_input is required")
    _validate_safe_intake(safe_input)
    if identity_fingerprint(safe_input) != record.get("identity_fingerprint"):
        raise ValueError("identity fingerprint mismatch")
    _timestamp(record.get("ingested_at"), "ingested_at")
    return record


def build_candidate_manifest(
    intake_paths: Sequence[Path],
    *,
    cohort_id: str,
    registry: dict[str, Any] | None = None,
    registry_path: Path = DEFAULT_REGISTRY,
    output: Path | None = None,
    write: bool = False,
) -> dict[str, Any]:
    """Build an immutable time-ordered candidate manifest without claiming readiness."""
    if not cohort_id:
        raise ValueError("cohort_id is required")
    registry = registry if registry is not None else _read_json(registry_path)
    development_ids, development_fingerprints = _development_identity(registry)
    records = [_validate_intake_record(Path(path)) for path in intake_paths]
    records.sort(key=lambda row: (_timestamp(row["ingested_at"], "ingested_at"), row["case_id"]))
    case_ids = [row["case_id"] for row in records]
    fingerprints = [row["identity_fingerprint"] for row in records]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("duplicate case_id in candidate cohort")
    if len(fingerprints) != len(set(fingerprints)):
        raise ValueError("duplicate identity fingerprint; changed-ID reentry is forbidden")
    if set(case_ids) & development_ids or set(fingerprints) & development_fingerprints:
        raise ValueError("candidate cohort overlaps development data")
    by_id = {_read_json(Path(path))["case_id"]: Path(path) for path in intake_paths}
    entries = []
    for row in records:
        path = by_id[row["case_id"]]
        entries.append({
            "case_id": row["case_id"],
            "identity_fingerprint": row["identity_fingerprint"],
            "ingested_at": row["ingested_at"],
            "intake_path": str(path),
            "intake_sha256": _file_sha256(path),
            "source_path": row["source_path"],
            "source_sha256": row["source_sha256"],
        })
    manifest = {
        "schema_version": "career-path-cohort-candidate-manifest/v1",
        "cohort_id": cohort_id,
        "status": "collecting",
        "ready": False,
        "case_count": len(records),
        "case_ids": case_ids,
        "entries": entries,
        "labels_revealed": False,
        "development_set_disjoint": True,
        "formal_scoring_permitted": False,
        "production_switch_permitted": False,
    }
    manifest["content_sha256"] = canonical_sha256(manifest)
    if output is not None:
        _write_new_json(Path(output), manifest, write=write)
    return manifest


def submit_label_review(review: dict[str, Any], output: Path | None = None, *, write: bool = False) -> dict[str, Any]:
    required = {"schema_version", "case_id", "reviewer_id", "label", "signed_at"}
    if not isinstance(review, dict) or set(review) != required:
        raise ValueError("label review fields mismatch")
    if review["schema_version"] != "career-path-label-review/v1":
        raise ValueError("label review schema mismatch")
    if not isinstance(review["case_id"], str) or not review["case_id"]:
        raise ValueError("case_id is required")
    _require_human(review["reviewer_id"], "reviewer_id")
    if review["label"] not in LABELS:
        raise ValueError("label must be employment/entrepreneurship/mixed/unknown")
    _timestamp(review["signed_at"], "signed_at")
    if output is not None:
        _write_new_json(Path(output), review, write=write)
    return dict(review)


def finalize_label(
    review_a: dict[str, Any],
    review_b: dict[str, Any],
    adjudication: dict[str, Any] | None = None,
    *,
    temporal_observation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    left, right = submit_label_review(review_a), submit_label_review(review_b)
    if left["case_id"] != right["case_id"]:
        raise ValueError("reviews must bind the same case_id")
    if left["reviewer_id"] == right["reviewer_id"]:
        raise ValueError("two different independent reviewers are required")
    reviewers = [left["reviewer_id"], right["reviewer_id"]]
    labels = [left["label"], right["label"]]
    if labels[0] != labels[1]:
        if adjudication is None:
            return {
                "status": "not_ready", "reason": "adjudication_required", "case_id": left["case_id"],
                "raw_reviews": [left, right], "production_switch_permitted": False,
            }
        required = {"schema_version", "case_id", "adjudicator_id", "label", "rationale", "signed_at"}
        if not isinstance(adjudication, dict) or set(adjudication) != required:
            raise ValueError("adjudication fields mismatch")
        if adjudication["schema_version"] != "career-path-label-adjudication/v1":
            raise ValueError("adjudication schema mismatch")
        adjudicator = _require_human(adjudication["adjudicator_id"], "adjudicator_id")
        if adjudicator in reviewers:
            raise ValueError("adjudicator must be a third independent human")
        if adjudication["case_id"] != left["case_id"] or adjudication["label"] not in LABELS:
            raise ValueError("adjudication case or label is invalid")
        if not isinstance(adjudication["rationale"], str) or not adjudication["rationale"].strip():
            raise ValueError("adjudication rationale is required")
        _timestamp(adjudication["signed_at"], "signed_at")
        final_label = adjudication["label"]
        review_status = "adjudicated"
    else:
        if adjudication is not None:
            raise ValueError("adjudication is only allowed for a disagreement")
        final_label = labels[0]
        review_status = "double_review_agreed"
    temporal_status = "not_ready_for_temporal_metrics"
    if temporal_observation is not None:
        validate_temporal_observation(temporal_observation)
        if temporal_observation["case_id"] != left["case_id"]:
            raise ValueError("temporal observation case_id mismatch")
        temporal_status = "ready_for_temporal_metrics"
    result = {
        "status": "ready",
        "case_id": left["case_id"],
        "label": final_label,
        "review_status": review_status,
        "reviewers": reviewers,
        "reviewer_labels": labels,
        "raw_reviews": [left, right],
        "temporal_status": temporal_status,
        "temporal_observation": temporal_observation,
        "production_switch_permitted": False,
    }
    if review_status == "adjudicated":
        result["adjudicator"] = adjudication["adjudicator_id"]
        result["adjudicated_label"] = final_label
        result["adjudication"] = adjudication
    return result


def finalize_cohort(
    finalized_labels: Sequence[dict[str, Any]],
    *,
    cohort_id: str,
    output_dir: Path,
    frozen_at: str | None = None,
    write: bool = False,
    minimum_cases: int = 30,
    minimum_per_class: int = 10,
) -> dict[str, Any]:
    """Finalize only genuine completed reviews; mixed/unknown remain retained rows."""
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for final in finalized_labels:
        if final.get("status") != "ready":
            raise ValueError("all labels must be ready before cohort finalization")
        case_id = final.get("case_id")
        if not isinstance(case_id, str) or case_id in seen:
            raise ValueError("final labels require unique case_ids")
        seen.add(case_id)
        row = {key: final[key] for key in ("case_id", "label", "review_status", "reviewers", "reviewer_labels")}
        for key in ("adjudicator", "adjudicated_label"):
            if key in final:
                row[key] = final[key]
        row["temporal_status"] = final.get("temporal_status", "not_ready_for_temporal_metrics")
        rows.append(row)
    rows.sort(key=lambda row: row["case_id"])
    counts = Counter(row["label"] for row in rows if row["label"] in BINARY_LABELS)
    strict_count = sum(counts.values())
    ready = strict_count >= minimum_cases and all(counts[label] >= minimum_per_class for label in BINARY_LABELS)
    metrics = {
        "retained_cases": len(rows),
        "strict_binary_cases": strict_count,
        "employment_cases": counts["employment"],
        "entrepreneurship_cases": counts["entrepreneurship"],
        "nonbinary_retained_cases": len(rows) - strict_count,
        "temporal_ready_cases": sum(row["temporal_status"] == "ready_for_temporal_metrics" for row in rows),
    }
    result: dict[str, Any] = {
        "status": "ready" if ready else "not_ready",
        "ready": ready,
        "metrics": metrics,
        "production_switch_permitted": False,
        "formal_scoring_permitted": False,
    }
    if not ready:
        result["failures"] = [
            name for name, passed in (
                ("minimum_strict_binary_cases", strict_count >= minimum_cases),
                ("minimum_cases_per_class", all(counts[label] >= minimum_per_class for label in BINARY_LABELS)),
            ) if not passed
        ]
        return result
    timestamp = frozen_at or datetime.now().astimezone().isoformat()
    _timestamp(timestamp, "frozen_at")
    output_dir = Path(output_dir)
    _reject_symlink_chain(output_dir, "output directory")
    if output_dir.exists() or output_dir.is_symlink():
        raise ValueError(f"output target must not exist: {output_dir}")
    labels_bytes = b"".join(_canonical(row) + b"\n" for row in rows)
    labels_name = "labels.jsonl"
    manifest_name = "manifest.json"
    labels_hash = hashlib.sha256(labels_bytes).hexdigest()
    manifest = {
        "schema_version": "career-path-holdout-manifest/v1",
        "cohort_id": cohort_id,
        "frozen_at": timestamp,
        "case_ids": [row["case_id"] for row in rows],
        "case_count": len(rows),
        "strict_binary_case_count": strict_count,
        "labels_path": labels_name,
        "labels_sha256": labels_hash,
        "labels_revealed": False,
        "one_shot_freeze": True,
        "production_switch_permitted": False,
    }
    manifest["cohort_sha256"] = canonical_sha256(manifest)
    if write:
        output_dir.mkdir(parents=True, exist_ok=False)
        try:
            _write_new(output_dir / labels_name, labels_bytes, write=True)
            _write_new_json(output_dir / manifest_name, manifest, write=True)
        except BaseException:
            for child in output_dir.iterdir():
                child.unlink()
            output_dir.rmdir()
            raise
    result.update({"manifest": manifest, "labels": rows, "labels_sha256": labels_hash})
    return result


def register_finalized_holdout(
    registry_path: Path,
    *,
    finalized: dict[str, Any],
    manifest_path: Path,
    labels_path: Path,
    reviewed_by: str,
    write: bool = False,
    output: Path | None = None,
) -> dict[str, Any]:
    """Create a reviewed successor registry; never overwrite the registry in place."""
    _require_human(reviewed_by, "reviewed_by")
    if finalized.get("status") != "ready" or finalized.get("ready") is not True:
        raise ValueError("only a ready finalized holdout may be registered")
    manifest_path, labels_path = Path(manifest_path), Path(labels_path)
    manifest = _read_json(manifest_path)
    if _file_sha256(labels_path) != manifest.get("labels_sha256"):
        raise ValueError("labels hash mismatch")
    registry = _read_json(Path(registry_path))
    if registry.get("unseen_holdout", {}).get("status") != "not_ready":
        raise ValueError("registry unseen_holdout is not in not_ready state")
    successor = dict(registry)
    successor["unseen_holdout"] = {
        "dataset_id": manifest.get("cohort_id"),
        "status": "frozen_awaiting_predictions",
        "case_count": manifest.get("case_count"),
        "manifest_path": str(manifest_path),
        "labels_path": str(labels_path),
        "labels_sha256": manifest.get("labels_sha256"),
        "promotion_eligible": False,
        "reviewed_by": reviewed_by,
        "production_switch_permitted": False,
    }
    if output is None:
        if write:
            raise ValueError("controlled registry update requires a new --out path; in-place overwrite is forbidden")
    else:
        if Path(output).resolve() == Path(registry_path).resolve():
            raise ValueError("registry update must not overwrite the source registry")
        _write_new_json(Path(output), successor, write=write)
    return successor


def repository_status(registry_path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    registry = _read_json(Path(registry_path))
    holdout = registry.get("unseen_holdout", {})
    ready = holdout.get("status") != "not_ready" and int(holdout.get("case_count", 0)) >= 30
    return {
        "status": "ready" if ready else "not_ready",
        "case_count": int(holdout.get("case_count", 0)),
        "production_switch_permitted": False,
        "formal_scoring_permitted": False,
        "failures": [] if ready else ["no_qualifying_unseen_holdout"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    status_parser = sub.add_parser("status")
    status_parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    intake = sub.add_parser("intake")
    intake.add_argument("--source", type=Path, required=True)
    intake.add_argument("--out", type=Path, required=True)
    intake.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    intake.add_argument("--ingested-at")
    intake.add_argument("--write", action="store_true")
    manifest = sub.add_parser("build-manifest")
    manifest.add_argument("--intake", type=Path, action="append", required=True)
    manifest.add_argument("--cohort-id", required=True)
    manifest.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    manifest.add_argument("--out", type=Path, required=True)
    manifest.add_argument("--write", action="store_true")
    review = sub.add_parser("submit-review")
    review.add_argument("--review", type=Path, required=True)
    review.add_argument("--out", type=Path, required=True)
    review.add_argument("--write", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "status":
            result = repository_status(args.registry)
        elif args.command == "intake":
            result = intake_candidate(
                args.source, args.out, registry_path=args.registry, write=args.write, ingested_at=args.ingested_at
            )
        elif args.command == "build-manifest":
            result = build_candidate_manifest(
                args.intake, cohort_id=args.cohort_id, registry_path=args.registry, output=args.out, write=args.write
            )
        else:
            result = submit_label_review(_read_json(args.review), args.out, write=args.write)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "rejected", "error": str(exc), "production_switch_permitted": False}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("status") not in {"not_ready", "rejected"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
