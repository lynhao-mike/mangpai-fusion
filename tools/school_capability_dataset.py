"""Prepare reviewed school-capability evaluation data without running inference."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.evaluation.case_audit import audit_cases
from engine.evaluation.freeze import verify_frozen_run
from engine.evaluation.manifest_validation import (
    GATE_THRESHOLDS_POLICY,
    validate_reviewed_manifest,
    validate_routes,
)
from engine.evaluation.models import FrozenBlindRun
from engine.evaluation.prospective_artifacts import (
    ArtifactRef,
    canonical_artifact_sha256,
    publish_new_json,
    validate_parent_ref,
)
from engine.evaluation.prospective_single_case import (
    build_single_case_intake,
    prepare_single_case_blind_bundle,
)

_INVENTORY_SCHEMA = "school-capability-case-inventory/v1"
_DECISIONS_SCHEMA = "school-capability-review-decisions/v1"
_LABELS_SCHEMA = "school-capability-labels-unbound/v1"
_MANIFEST_SCHEMA = "school-capability-case-manifest/v1"
_CONFIG_SCHEMA = "school-capability-evaluation-config/v1"
_BOUND_LABELS_SCHEMA = "school-capability-labels/v1"
_PROSPECTIVE_SCHEMA = "school-capability-prospective-intake/v1"
_BLIND_BUNDLE_SCHEMA = "school-capability-blind-bundle/v1"
_CLEAN = {"historical_blind", "prospective"}
_FORBIDDEN_INTAKE_MARKERS = ("feedback", "labels", "report", "known facts", "known_facts", "known-facts")
_ELIGIBILITIES = {"blind_candidate", "historical_blind_candidate", "development_only"}
_EVIDENCE_GRADES = {"A", "B", "C"}
_ROUTE_FIELDS = {"school_id", "task_id", "chart_prototype_id", "claim_type", "time_horizon", "evidence_completeness_band"}
_MANIFEST_RECORD_FIELDS = {"case_id", "has_input", "has_feedback", "has_statement_index", "has_existing_report", "feedback_quantifiable", "contamination_flags", "eligibility", "evidence_notes", "eligible_routes"}
_INTAKE_RECORD_FIELDS = {"case_id", "input_file", "input_sha256", "subject_id_hash", "task_ids"}
_TASK_BUNDLE_FIELDS = (
    "task_id", "domain", "claim_type", "scoring_method", "quantifiable", "high_risk",
    "allowed_time_horizons", "required_input_fields", "label_schema",
)
_WITNESS_SCHEMA = "school-capability-witness-registry/v1"
_WITNESS_PAYLOAD_FIELDS = {
    "registered": {"case_id", "input_sha256", "subject_id_hash"},
    "prepared": {"case_id", "bundle_sha256"},
    "freeze": {"case_id", "freeze_hash"},
    "reveal": {"case_id", "freeze_hash", "unbound_labels_sha256"},
}
_STEMS = "甲乙丙丁戊己庚辛壬癸"
_BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
_VALID_PILLARS = {
    _STEMS[index % 10] + _BRANCHES[index % 12]
    for index in range(60)
}
_REQUIRED_LABEL_FIELDS = {
    "case_id", "task_id", "label", "source", "observed_at", "confidence_grade",
    "quantifiable", "conflict_state", "reviewer",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _decision_map(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if document.get("schema_version") != _DECISIONS_SCHEMA or not isinstance(document.get("records"), list):
        raise ValueError(f"review decisions must use {_DECISIONS_SCHEMA}")
    result: dict[str, dict[str, Any]] = {}
    for item in document["records"]:
        if not isinstance(item, dict) or not isinstance(item.get("case_id"), str) or item["case_id"] in result:
            raise ValueError("review decisions require unique case_id records")
        result[item["case_id"]] = item
    return result


def build_inventory(cases_dir: Path, reports_dir: Path, review_decisions: dict[str, Any]) -> dict[str, Any]:
    decisions = _decision_map(review_decisions)
    records = []
    for audit in audit_cases(cases_dir, reports_dir):
        decision = decisions.get(audit.case_id, {})
        explicit_contamination = audit.eligibility == "development_only"
        requested = decision.get("classification")
        reviewer = decision.get("reviewed_by")
        human_clean = (
            requested in _CLEAN
            and isinstance(reviewer, str) and bool(reviewer.strip())
            and not reviewer.lower().startswith(("automated", "agent", "ai-"))
            and isinstance(decision.get("reviewed_at"), str) and decision["reviewed_at"].endswith("Z")
            and isinstance(decision.get("provenance_evidence"), list)
            and any(isinstance(item, str) and ":" in item for item in decision["provenance_evidence"])
        )
        evidence = list(audit.contamination_flags)
        if not human_clean:
            evidence.append("human_clean_review_missing")
        if explicit_contamination:
            classification = "development_only"
        elif audit.eligibility == "not_scorable":
            classification = "not_scorable"
        elif human_clean:
            classification = requested
        else:
            classification = "development_only"
        records.append({
            "case_id": audit.case_id,
            "birth_info_complete": audit.has_input and "missing_birth_input" not in audit.contamination_flags,
            "feedback_present": audit.has_feedback,
            "feedback_grade": decision.get("feedback_grade", "unreviewed"),
            "development_contaminated": classification not in _CLEAN,
            "contamination_evidence": sorted(set(evidence)),
            "classification": classification,
            "notes": decision.get("notes", "; ".join(audit.evidence_notes)),
            "reviewed_by": decision.get("reviewed_by", ""),
            "reviewed_at": decision.get("reviewed_at", ""),
        })
    return {"schema_version": _INVENTORY_SCHEMA, "generated_at": _now(), "records": records}


def _is_utc_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00").tzinfo == timezone.utc
    except ValueError:
        return False


def _task_map(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tasks = catalog.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("task catalog requires tasks")
    result = {item.get("task_id"): item for item in tasks if isinstance(item, dict)}
    if len(result) != len(tasks) or None in result:
        raise ValueError("task catalog requires unique task_id values")
    return result


def build_unbound_labels(observations: list[dict[str, Any]], task_catalog: dict[str, Any]) -> dict[str, Any]:
    tasks = _task_map(task_catalog)
    labels = []
    seen = set()
    for item in observations:
        if item.get("disposition") == "no_data":
            continue
        missing = _REQUIRED_LABEL_FIELDS - set(item)
        if missing:
            raise ValueError(f"label observation missing field: {sorted(missing)[0]}")
        task = tasks.get(item["task_id"])
        if task is None:
            raise ValueError(f"unknown task_id: {item['task_id']}")
        identity = item["case_id"], item["task_id"]
        if identity in seen:
            raise ValueError("duplicate label identity")
        seen.add(identity)
        for field in ("case_id", "task_id", "source", "observed_at", "confidence_grade", "reviewer"):
            if not isinstance(item[field], str) or not item[field].strip():
                raise ValueError(f"{field} must be a non-empty string")
        if type(item["quantifiable"]) is not bool:
            raise ValueError("quantifiable must be a boolean")
        if item["confidence_grade"] not in {"A", "B", "C"}:
            raise ValueError("confidence_grade must be A, B, or C")
        if item["conflict_state"] not in {"none", "conflicting_sources"}:
            raise ValueError("conflict_state is invalid")
        source = item["source"].replace("\\", "/")
        if not source.startswith(("cases/raw_feedback/source/", "cases/")) or any(marker in source for marker in ("reports/", "analysis.md", "school-claims", "statement_index")) or ":" not in source:
            raise ValueError("source must reference raw feedback or feedback.md with a line number")
        if item["conflict_state"] == "conflicting_sources" and item["quantifiable"]:
            raise ValueError("conflicting_sources label cannot be quantifiable")
        if task.get("high_risk") and (item.get("confidence_grade") != "A" or not item.get("secondary_reviewed_by")):
            raise ValueError("high-risk label requires A grade and secondary_reviewed_by")
        schema = task.get("label_schema", {})
        method = task.get("scoring_method")
        label = item["label"]
        if method == "binary_probability" and label not in {schema.get("positive_label"), schema.get("negative_label")}:
            raise ValueError("binary label does not match task schema")
        if method == "ordinal" and label not in schema.get("labels", []):
            raise ValueError("ordinal label does not match task schema")
        if method == "multiclass_probability" and label not in schema.get("labels", []):
            raise ValueError("categorical label does not match task schema")
        if method == "time_window":
            if not isinstance(label, dict) or type(label.get("occurred")) is not bool:
                raise ValueError("time_window label requires occurred boolean and year")
            year = label.get("year")
            if (label["occurred"] and type(year) is not int) or (not label["occurred"] and year is not None):
                raise ValueError("time_window year is invalid")
        labels.append({field: item[field] for field in _REQUIRED_LABEL_FIELDS})
    return {"schema_version": _LABELS_SCHEMA, "generated_at": _now(), "labels": labels}


def _human_reviewer(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not value.lower().startswith(("automated", "agent", "ai-"))


def _validate_routes(routes: object) -> list[dict[str, str]]:
    return validate_routes(routes)


def build_reviewed_manifest(inventory: dict[str, Any], reviewed_by: str, expected_schools: list[str], routes_by_case: dict[str, list[dict[str, str]]] | None = None) -> dict[str, Any]:
    if inventory.get("schema_version") != _INVENTORY_SCHEMA or not isinstance(inventory.get("records"), list):
        raise ValueError(f"inventory must use {_INVENTORY_SCHEMA}")
    if not _human_reviewer(reviewed_by):
        raise ValueError("automated reviewer cannot promote cases")
    if not expected_schools or any(not isinstance(item, str) or not item for item in expected_schools) or len(set(expected_schools)) != len(expected_schools):
        raise ValueError("expected_schools must be unique non-empty strings")
    routes_by_case = routes_by_case or {}
    if not isinstance(routes_by_case, dict):
        raise ValueError("routes_by_case must be an object")
    inventory_case_ids = {
        item.get("case_id") for item in inventory["records"] if isinstance(item, dict)
    }
    unknown_route_cases = set(routes_by_case) - inventory_case_ids
    if unknown_route_cases:
        raise ValueError(f"routes_by_case references unknown case: {sorted(unknown_route_cases)[0]}")
    records = []
    seen_cases = set()
    for source in inventory["records"]:
        if not isinstance(source, dict) or not isinstance(source.get("case_id"), str) or not source["case_id"].strip() or source["case_id"] in seen_cases:
            raise ValueError("inventory record requires unique case_id")
        seen_cases.add(source["case_id"])
        clean = source.get("classification") in _CLEAN and source.get("development_contaminated") is False
        if clean:
            if not _human_reviewer(source.get("reviewed_by")) or not _is_utc_timestamp(source.get("reviewed_at")) or not isinstance(source.get("provenance_evidence"), list) or not source["provenance_evidence"] or any(not isinstance(item, str) or ":" not in item for item in source["provenance_evidence"]):
                raise ValueError("clean inventory requires human review provenance")
            if "human_clean_review_missing" in source.get("contamination_evidence", []):
                raise ValueError("clean inventory contains human_clean_review_missing")
        routes = _validate_routes(routes_by_case.get(source["case_id"], [])) if clean else []
        records.append({
            "case_id": source["case_id"], "has_input": bool(source.get("birth_info_complete")),
            "has_feedback": bool(source.get("feedback_present")), "has_statement_index": False,
            "has_existing_report": False, "feedback_quantifiable": source.get("feedback_grade") in {"A", "B"},
            "contamination_flags": list(source.get("contamination_evidence", [])),
            "eligibility": "historical_blind_candidate" if source.get("classification") == "historical_blind" and clean else "blind_candidate" if source.get("classification") == "prospective" and clean else "development_only",
            "evidence_notes": [source["notes"]] if source.get("notes") else [], "eligible_routes": routes,
        })
    return {"schema_version": _MANIFEST_SCHEMA, "generated_at": _now(), "reviewed_by": reviewed_by, "expected_schools": expected_schools, "records": records}


def _validate_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return validate_reviewed_manifest(manifest)


def build_evaluation_config(
    manifest: dict[str, Any], baseline_prevalence_by_task: dict[str, float],
    evidence_grade: str, evaluated_at: str, task_catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    records = _validate_manifest(manifest)
    tasks_by_id = _task_map(task_catalog) if task_catalog is not None else None
    if evidence_grade not in _EVIDENCE_GRADES:
        raise ValueError("evidence_grade must be A, B, or C")
    if not _is_utc_timestamp(evaluated_at):
        raise ValueError("evaluated_at must be an ISO 8601 UTC timestamp")
    grid: set[tuple[str, str]] = set()
    metadata: dict[str, Any] = {}
    weights: dict[str, int] = {}
    for row in records:
        if row["eligibility"] not in {"blind_candidate", "historical_blind_candidate"}:
            continue
        for route in row["eligible_routes"]:
            if tasks_by_id is not None:
                task = tasks_by_id.get(route["task_id"])
                if task is None or route["claim_type"] != task.get("claim_type") or route["time_horizon"] not in task.get("allowed_time_horizons", []):
                    raise ValueError("route does not match task catalog")
            grid.add((row["case_id"], route["task_id"]))
            key = "|".join((row["case_id"], route["task_id"], route["school_id"]))
            metadata[key] = {field: route[field] for field in ("chart_prototype_id", "time_horizon", "evidence_completeness_band")}
            weights[key] = 1
    tasks = {task_id for _, task_id in grid}
    if set(baseline_prevalence_by_task) != tasks or any(type(value) not in (int, float) or type(value) is bool or not 0 <= value <= 1 for value in baseline_prevalence_by_task.values()):
        raise ValueError("baseline prevalence must exactly cover eligible tasks")
    return {"schema_version": _CONFIG_SCHEMA, "eligible_case_tasks": [list(item) for item in sorted(grid)], "baseline_prevalence_by_task": baseline_prevalence_by_task, "case_metadata": metadata, "evidence_grade": evidence_grade, "evaluated_at": evaluated_at, "score_weights": weights, "gate_thresholds": dict(GATE_THRESHOLDS_POLICY)}


def _verified_run(document: dict[str, Any]) -> FrozenBlindRun:
    run = FrozenBlindRun.from_dict(document)
    verify_frozen_run(run)
    return run


def bind_labels_after_freeze(unbound_labels: dict[str, Any], frozen_run: dict[str, Any]) -> dict[str, Any]:
    if set(unbound_labels) != {"schema_version", "generated_at", "labels"} and set(unbound_labels) != {"schema_version", "labels"}:
        raise ValueError("unbound labels schema is invalid")
    if unbound_labels.get("schema_version") != _LABELS_SCHEMA or not isinstance(unbound_labels.get("labels"), list):
        raise ValueError("unbound labels schema is invalid")
    run = _verified_run(frozen_run)
    return {"schema_version": _BOUND_LABELS_SCHEMA, "freeze_hash": run.freeze_hash, "labels": unbound_labels["labels"]}


def validate_dataset(
    manifest: dict[str, Any], labels: dict[str, Any], frozen_run: dict[str, Any],
    prospective_intake: dict[str, Any] | None = None,
    blind_bundle_manifest: dict[str, Any] | None = None,
    reveal_provenance: dict[str, Any] | None = None,
    blind_bundle_root: Path | None = None,
    witness_registry: dict[str, Any] | None = None,
    witness_key: bytes | None = None,
) -> dict[str, Any]:
    records = _validate_manifest(manifest)
    run = _verified_run(frozen_run)
    if not _is_utc_timestamp(run.frozen_at):
        raise ValueError("frozen_at must be an ISO 8601 UTC timestamp")
    if set(labels) != {"schema_version", "freeze_hash", "labels"} or labels.get("schema_version") != _BOUND_LABELS_SCHEMA or not isinstance(labels.get("labels"), list):
        raise ValueError("bound labels schema is invalid")
    if labels.get("freeze_hash") != run.freeze_hash:
        raise ValueError("revealed labels freeze hash does not match frozen run")
    routes = {(row["case_id"], route["task_id"], route["school_id"]) for row in records if row["eligibility"] in {"blind_candidate", "historical_blind_candidate"} for route in row["eligible_routes"]}
    outputs = {(output.case_id, output.task_id, output.school_id) for output in run.outputs}
    if outputs != routes or len(outputs) != len(run.outputs):
        raise ValueError("frozen outputs must exactly cover manifest routes")
    eligible = {row["case_id"] for row in records if row["eligibility"] in {"blind_candidate", "historical_blind_candidate"}}
    route_tasks = {(case_id, task_id) for case_id, task_id, _ in routes}
    identities = set()
    for item in labels["labels"]:
        if not isinstance(item, dict) or set(item) != _REQUIRED_LABEL_FIELDS:
            raise ValueError("label record has invalid schema")
        identity = item["case_id"], item["task_id"]
        if identity in identities:
            raise ValueError("duplicate label identity")
        if identity not in route_tasks:
            raise ValueError("label must correspond to an eligible manifest route")
        identities.add(identity)
    labelled_cases = {case_id for case_id, _ in identities if case_id in eligible}
    reasons = []
    if prospective_intake is None or blind_bundle_manifest is None or reveal_provenance is None:
        reasons.append("prospective intake, blind bundle manifest, and reveal provenance are required for GO")
    else:
        _validate_go_provenance(
            records, labels, run, prospective_intake, blind_bundle_manifest,
            reveal_provenance, Path(blind_bundle_root) if blind_bundle_root is not None else None,
        )
    if blind_bundle_root is None:
        reasons.append("actual blind bundle root is required for GO")
    if witness_registry is None or not witness_key:
        reasons.append("witness registry and external witness key are required for GO")
    else:
        verify_witness_registry(witness_registry, witness_key)
        if prospective_intake is None or blind_bundle_manifest is None:
            reasons.append("prospective intake and blind bundle manifest are required for witness validation")
        else:
            _validate_witness_timeline(
                records, run, reveal_provenance, witness_registry,
                prospective_intake, blind_bundle_manifest,
            )
    if len(eligible) < 30:
        reasons.append("fewer than 30 blind eligible cases")
    if len(labelled_cases) < 30:
        reasons.append("fewer than 30 labelled blind eligible cases")
    return {"status": "GO" if not reasons else "HOLD", "blind_eligible_count": len(eligible), "labelled_count": len(labelled_cases), "reasons": reasons}


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()



def _canonical_sha(value: object) -> str:
    return _sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _parse_utc(value: object, name: str) -> datetime:
    if not _is_utc_timestamp(value):
        raise ValueError(f"{name} must be an ISO 8601 UTC timestamp")
    return datetime.fromisoformat(str(value)[:-1] + "+00:00")


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _validate_witness_event(event: object, *, stored: bool) -> dict[str, Any]:
    envelope = {"event_type", "occurred_at", "payload"}
    if stored:
        envelope |= {"previous_hash", "event_hash", "hmac_sha256"}
    if not isinstance(event, dict) or set(event) != envelope:
        raise ValueError("witness event schema is invalid")
    event_type = event.get("event_type")
    payload = event.get("payload")
    if event_type not in _WITNESS_PAYLOAD_FIELDS or not _is_utc_timestamp(event.get("occurred_at")):
        raise ValueError("witness event schema is invalid")
    if not isinstance(payload, dict) or set(payload) != _WITNESS_PAYLOAD_FIELDS[event_type]:
        raise ValueError("witness event payload schema is invalid")
    _validate_case_id(payload.get("case_id"))
    if any(not _is_sha256(value) for key, value in payload.items() if key != "case_id"):
        raise ValueError("witness event payload digest is invalid")
    if stored and any(not _is_sha256(event.get(key)) for key in ("previous_hash", "event_hash", "hmac_sha256")):
        raise ValueError("witness event authentication schema is invalid")
    return event


def append_witness_event(
    registry: dict[str, Any] | None, event: dict[str, Any], witness_key: bytes,
) -> dict[str, Any]:
    """Return a new append-only HMAC authenticated hash-chain registry."""
    if not isinstance(witness_key, bytes) or not witness_key:
        raise ValueError("witness key must be non-empty bytes")
    current = {"schema_version": _WITNESS_SCHEMA, "events": []} if registry is None else json.loads(json.dumps(registry))
    verify_witness_registry(current, witness_key)
    _validate_witness_event(event, stored=False)
    previous_hash = current["events"][-1]["event_hash"] if current["events"] else "0" * 64
    unsigned = {**event, "previous_hash": previous_hash}
    event_hash = _canonical_sha(unsigned)
    signature = hmac.new(witness_key, event_hash.encode("ascii"), hashlib.sha256).hexdigest()
    current["events"].append({**unsigned, "event_hash": event_hash, "hmac_sha256": signature})
    return current


def verify_witness_registry(registry: dict[str, Any], witness_key: bytes) -> bool:
    """Verify registry schema, chain continuity, event hashes, and HMACs."""
    if not isinstance(witness_key, bytes) or not witness_key:
        raise ValueError("witness key must be non-empty bytes")
    base_fields = {"schema_version", "events"}
    artifact_fields = {
        "case_id", "subject_id_hash", "created_at", "artifact_path", "parents",
        "artifact_sha256",
    }
    if (
        not isinstance(registry, dict)
        or set(registry) not in (base_fields, base_fields | artifact_fields)
        or registry.get("schema_version") != _WITNESS_SCHEMA
        or not isinstance(registry.get("events"), list)
    ):
        raise ValueError("witness registry schema is invalid")
    if set(registry) == base_fields | artifact_fields:
        if (
            not isinstance(registry.get("case_id"), str)
            or not _is_sha256(registry.get("subject_id_hash"))
            or not _is_utc_timestamp(registry.get("created_at"))
            or not isinstance(registry.get("artifact_path"), str)
            or not registry["artifact_path"]
            or not isinstance(registry.get("parents"), list)
            or registry.get("artifact_sha256") != canonical_artifact_sha256(registry)
        ):
            raise ValueError("witness registry artifact contract is invalid")
    previous_hash = "0" * 64
    for event in registry["events"]:
        _validate_witness_event(event, stored=True)
        if event["previous_hash"] != previous_hash:
            raise ValueError("witness hash chain is broken")
        unsigned = {key: value for key, value in event.items() if key not in {"event_hash", "hmac_sha256"}}
        expected_hash = _canonical_sha(unsigned)
        expected_hmac = hmac.new(witness_key, expected_hash.encode("ascii"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(str(event["hmac_sha256"]), expected_hmac):
            raise ValueError("witness HMAC verification failed")
        if not hmac.compare_digest(str(event["event_hash"]), expected_hash):
            raise ValueError("witness event hash is invalid")
        previous_hash = expected_hash
    return True


def _validate_witness_timeline(
    records: list[dict[str, Any]], run: FrozenBlindRun,
    provenance: dict[str, Any] | None, registry: dict[str, Any],
    intake: dict[str, Any], bundle: dict[str, Any],
) -> None:
    if provenance is None:
        raise ValueError("reveal provenance is required for witness validation")
    intake_by_case = {row["case_id"]: row for row in intake["records"]}
    for row in records:
        if row["eligibility"] != "blind_candidate":
            continue
        case_id = row["case_id"]
        events = [event for event in registry["events"] if event["payload"]["case_id"] == case_id]
        by_type = {
            event_type: [event for event in events if event["event_type"] == event_type]
            for event_type in _WITNESS_PAYLOAD_FIELDS
        }
        if any(len(by_type[event_type]) != 1 for event_type in _WITNESS_PAYLOAD_FIELDS) or len(events) != 4:
            raise ValueError(f"witness requires exactly one registered, prepared, freeze, reveal: {case_id}")
        registered, prepared, freeze, reveal = (
            by_type[event_type][0]
            for event_type in ("registered", "prepared", "freeze", "reveal")
        )
        times = [
            _parse_utc(event["occurred_at"], f"witness {event['event_type']} occurred_at")
            for event in (registered, prepared, freeze, reveal)
        ]
        if not times[0] < times[1] < times[2] < times[3]:
            raise ValueError(f"witness times must strictly increase registered -> prepared -> freeze -> reveal: {case_id}")
        intake_row = intake_by_case[case_id]
        expected_registered = {
            "case_id": case_id,
            "input_sha256": intake_row["input_sha256"],
            "subject_id_hash": intake_row["subject_id_hash"],
        }
        if registered["payload"] != expected_registered:
            raise ValueError(f"witness registered payload does not match actual intake/bundle: {case_id}")
        if prepared["payload"] != {"case_id": case_id, "bundle_sha256": bundle["bundle_sha256"]}:
            raise ValueError(f"witness prepared payload does not match actual bundle: {case_id}")
        if freeze["payload"] != {"case_id": case_id, "freeze_hash": run.freeze_hash} or times[2] != _parse_utc(run.frozen_at, "frozen_at"):
            raise ValueError(f"witness freeze payload does not match frozen run: {case_id}")
        expected_reveal = {
            "case_id": case_id, "freeze_hash": run.freeze_hash,
            "unbound_labels_sha256": provenance["unbound_labels_sha256"],
        }
        if reveal["payload"] != expected_reveal or times[3] != _parse_utc(provenance.get("bound_at"), "bound_at"):
            raise ValueError(f"witness reveal payload does not match reveal provenance: {case_id}")


def _verify_actual_bundle(bundle_root: Path, expected_manifest: dict[str, Any]) -> None:
    _reject_symlink(bundle_root, "bundle root")
    if not bundle_root.is_dir():
        raise ValueError("actual bundle root must be a directory")
    manifest_path = bundle_root / "bundle-manifest.json"
    _reject_symlink(manifest_path, "actual bundle manifest")
    try:
        actual_manifest = _read_json(manifest_path)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("actual bundle manifest is missing or invalid") from error
    if actual_manifest != expected_manifest:
        raise ValueError("actual bundle manifest does not canonically match supplied manifest")
    expected_files = expected_manifest["files"]
    actual_names = {
        relative
        for path in bundle_root.rglob("*")
        if path.is_file()
        for relative in (path.relative_to(bundle_root).as_posix(),)
        if relative != "bundle-manifest.json"
    }
    if actual_names != set(expected_files):
        raise ValueError("actual bundle files do not match manifest")
    for name, expected_hash in expected_files.items():
        path = bundle_root / name
        _reject_symlink(path, "actual bundle file")
        if _sha256(path.read_bytes()) != expected_hash:
            raise ValueError(f"actual bundle file hash mismatch: {name}")


def _validate_go_provenance(
    records: list[dict[str, Any]], labels: dict[str, Any], run: FrozenBlindRun,
    intake: dict[str, Any], bundle: dict[str, Any], provenance: dict[str, Any],
    bundle_root: Path | None,
) -> None:
    if set(intake) != {"schema_version", "generated_at", "operator", "schools", "task_catalog_sha256", "records"} or intake.get("schema_version") != _PROSPECTIVE_SCHEMA or not isinstance(intake.get("records"), list):
        raise ValueError("prospective intake schema is invalid")
    _parse_utc(intake.get("generated_at"), "intake generated_at")
    intake_rows: dict[str, dict[str, Any]] = {}
    subjects: set[str] = set()
    for row in intake["records"]:
        if not isinstance(row, dict) or set(row) != _INTAKE_RECORD_FIELDS:
            raise ValueError("prospective intake record is invalid")
        case_id = _validate_case_id(row["case_id"])
        if case_id in intake_rows:
            raise ValueError("prospective intake requires unique cases")
        if not isinstance(row["input_sha256"], str) or not isinstance(row["subject_id_hash"], str) or len(row["subject_id_hash"]) != 64 or row["subject_id_hash"] in subjects or not isinstance(row["task_ids"], list) or not row["task_ids"] or len(set(row["task_ids"])) != len(row["task_ids"]):
            raise ValueError("prospective intake record values or duplicate subject are invalid")
        subjects.add(row["subject_id_hash"])
        intake_rows[case_id] = row
    prospective = {row["case_id"]: row for row in records if row["eligibility"] == "blind_candidate"}
    if set(prospective) != set(intake_rows):
        raise ValueError("eligible cases must exactly match prospective intake records")
    if set(bundle) != {"schema_version", "bundle_sha256", "files"} or bundle.get("schema_version") != _BLIND_BUNDLE_SCHEMA or not isinstance(bundle.get("files"), dict):
        raise ValueError("blind bundle manifest schema is invalid")
    files = bundle["files"]
    base_files = {"tasks.json", "rule-snapshot.json"} | {f"cases/{case_id}/chart.json" for case_id in intake_rows}
    allowed_file_sets = (base_files, base_files | {"intake.json"})
    if set(files) not in allowed_file_sets or any(not isinstance(value, str) or len(value) != 64 for value in files.values()):
        raise ValueError("blind bundle files do not exactly match intake")
    if bundle["bundle_sha256"] != _canonical_sha(files):
        raise ValueError("blind bundle hash mismatch")
    if bundle_root is not None:
        _verify_actual_bundle(bundle_root, bundle)
    if run.task_catalog_version != files["tasks.json"]:
        raise ValueError("frozen task catalog hash does not match bundle")
    if run.rule_snapshot_id != files["rule-snapshot.json"]:
        raise ValueError("frozen rule snapshot hash does not match bundle")
    for case_id, row in intake_rows.items():
        if bundle_root is not None:
            chart = validate_canonical_chart(
                _read_json(bundle_root / f"cases/{case_id}/chart.json"), case_id,
            )
            subject_id_hash = _canonical_sha({
                key: chart[key] for key in ("four_pillars", "sex_marker")
            })
            if subject_id_hash != row["subject_id_hash"]:
                raise ValueError(f"case canonical chart does not match intake subject: {case_id}")
        route_tasks = {route["task_id"] for route in prospective[case_id]["eligible_routes"]}
        if route_tasks != set(row["task_ids"]):
            raise ValueError(f"case tasks do not match intake: {case_id}")
    if set(provenance) != {"freeze_hash", "bound_at", "unbound_labels_sha256"}:
        raise ValueError("reveal provenance schema is invalid")
    if provenance["freeze_hash"] != run.freeze_hash:
        raise ValueError("reveal provenance freeze hash does not match frozen run")
    if _parse_utc(provenance["bound_at"], "bound_at") < _parse_utc(run.frozen_at, "frozen_at"):
        raise ValueError("bound_at must not be earlier than frozen_at")
    unbound = {"schema_version": _LABELS_SCHEMA, "labels": labels["labels"]}
    if provenance["unbound_labels_sha256"] != _canonical_sha(unbound):
        raise ValueError("unbound labels hash does not match revealed labels")


def _reject_symlink(path: Path, description: str) -> None:
    absolute = path.absolute()
    for candidate in (absolute, *absolute.parents):
        if candidate.is_symlink():
            raise ValueError(f"{description} must not be or traverse a symlink: {path}")


def _contains_forbidden_field(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            any(marker in str(key).lower().replace("_", " ").replace("-", " ") for marker in _FORBIDDEN_INTAKE_MARKERS)
            or _contains_forbidden_field(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_field(item) for item in value)
    if isinstance(value, str):
        normalized = value.lower().replace("_", " ").replace("-", " ")
        return any(marker.lower().replace("_", " ").replace("-", " ") in normalized for marker in _FORBIDDEN_INTAKE_MARKERS)
    return False


def _validate_case_id(case_id: object) -> str:
    if not isinstance(case_id, str) or not case_id or case_id in {".", ".."} or "/" in case_id or "\\" in case_id or Path(case_id).name != case_id:
        raise ValueError("case_id must be a safe path component")
    return case_id


def validate_canonical_chart(chart: object, expected_case_id: str) -> dict[str, Any]:
    """Validate the canonical chart contract and its expected case binding."""
    expected_case_id = _validate_case_id(expected_case_id)
    required = {"case_id", "four_pillars", "sex_marker"}
    optional = {"solar_datetime", "start_luck", "dayun_steps", "liunian_steps"}
    if not isinstance(chart, dict) or not required <= set(chart) or set(chart) - required - optional:
        raise ValueError(f"case canonical chart schema is invalid: {expected_case_id}")
    try:
        case_id = _validate_case_id(chart["case_id"])
    except ValueError as error:
        raise ValueError(f"case canonical chart case_id is invalid: {expected_case_id}") from error
    pillars = chart["four_pillars"]
    if (
        case_id != expected_case_id
        or not isinstance(pillars, list)
        or len(pillars) != 4
        or any(not isinstance(pillar, str) or pillar not in _VALID_PILLARS for pillar in pillars)
        or chart["sex_marker"] not in {"乾", "坤"}
        or any(not isinstance(chart.get(field, ""), str) for field in ("solar_datetime", "start_luck"))
        or any(not isinstance(chart.get(field, []), list) for field in ("dayun_steps", "liunian_steps"))
    ):
        raise ValueError(f"case canonical chart values are invalid: {expected_case_id}")
    return chart


def parse_canonical_chart(content: str, case_id: str) -> dict[str, Any]:
    """Parse supported intake text into the validated canonical chart contract."""
    pillar_matches = re.findall(r"^\s*四柱\s*[：:]\s*([^\r\n]+?)\s*$", content, re.MULTILINE)
    sex_matches = re.findall(r"^\s*(?:性别|命式)\s*[：:]\s*([^\s\r\n]+)\s*$", content, re.MULTILINE)
    extended: dict[str, Any] = {}
    if not pillar_matches and not sex_matches:
        sex_matches = [match.removesuffix("造") for match in re.findall(
            r"^Sex\s*:\s*([乾坤](?:造)?)\s*$", content, re.MULTILINE,
        )]
        four_section = content.partition("$FOUR")[2].partition("$DY_LOOP")[0]
        rows = {
            marker: (stem, branch)
            for marker, stem, branch in re.findall(
                r"^([YMDH]):[^,\r\n]*,([甲乙丙丁戊己庚辛壬癸]),([子丑寅卯辰巳午未申酉戌亥]),",
                four_section,
                re.MULTILINE,
            )
        }
        if set(rows) == {"Y", "M", "D", "H"}:
            pillar_matches = [" ".join("".join(rows[marker]) for marker in "YMDH")]
        solar = re.findall(r"^Solar\s*:\s*([^\r\n]+?)\s*$", content, re.MULTILINE)
        start = re.findall(r"^Start\s*:\s*([^,\r\n]+)", content, re.MULTILINE)
        dayun_steps: list[dict[str, Any]] = []
        liunian_steps: list[dict[str, Any]] = []
        current_dayun = ""
        loop = content.partition("$DY_LOOP")[2]
        for line in loop.splitlines():
            dayun = re.fullmatch(r"\s*>?\s*#(\d{4}),[^,]*,([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]),.*", line)
            if dayun:
                current_dayun = dayun.group(2)
                dayun_steps.append({"ganzhi": current_dayun, "start_year": int(dayun.group(1))})
                continue
            liunian = re.fullmatch(r"\s*>\s*(\d{4}),([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]),.*", line)
            if liunian:
                step: dict[str, Any] = {"year": int(liunian.group(1)), "ganzhi": liunian.group(2)}
                if current_dayun:
                    step["dayun"] = current_dayun
                liunian_steps.append(step)
        extended = {
            "solar_datetime": solar[0] if len(solar) == 1 else "",
            "start_luck": start[0].strip() if len(start) == 1 else "",
            "dayun_steps": dayun_steps,
            "liunian_steps": liunian_steps,
        }
    if len(pillar_matches) != 1 or len(sex_matches) != 1:
        raise ValueError(f"cannot strictly extract canonical chart: {case_id}")
    return validate_canonical_chart({
        "case_id": case_id,
        "four_pillars": pillar_matches[0].split(),
        "sex_marker": sex_matches[0],
        **extended,
    }, case_id)


def register_prospective_intake(
    input_files: list[Path],
    tasks: dict[str, Any],
    schools: list[str],
    operator: str,
    *,
    tasks_by_case: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Register prediction-first cases while rejecting known outcomes and labels."""
    if not input_files:
        raise ValueError("prospective intake requires input files")
    if not _human_reviewer(operator):
        raise ValueError("operator must be a named human")
    if not schools or len(set(schools)) != len(schools) or any(not isinstance(item, str) or not item for item in schools):
        raise ValueError("schools must be unique non-empty strings")
    task_ids = set(_task_map(tasks))
    intake_safe_tasks = {
        **tasks,
        "tasks": [
            {key: value for key, value in task.items() if key != "label_schema"}
            for task in tasks["tasks"]
        ],
    }
    if _contains_forbidden_field(intake_safe_tasks):
        raise ValueError("tasks contain forbidden feedback/labels/report/known facts fields")
    tasks_by_case = tasks_by_case or {}
    input_case_ids = [_validate_case_id(Path(raw_path).parent.name) for raw_path in input_files]
    short_slot_pattern = re.compile(r"^(P-GO-\d{4})-(\d{3})$")
    short_slots: list[tuple[str, int]] = []
    unmatched_short_slots: list[str] = []
    resolved_tasks: dict[str, list[str]] = {}
    for assignment_key, selected_tasks in tasks_by_case.items():
        assignment_key = _validate_case_id(assignment_key)
        if (
            not isinstance(selected_tasks, list)
            or not selected_tasks
            or any(not isinstance(task_id, str) for task_id in selected_tasks)
            or len(set(selected_tasks)) != len(selected_tasks)
        ):
            raise ValueError(f"case tasks must be unique and non-empty: {assignment_key}")
        unknown = set(selected_tasks) - task_ids
        if unknown:
            raise ValueError(f"unknown task: {sorted(unknown)[0]}")
        short_match = short_slot_pattern.fullmatch(assignment_key)
        if short_match:
            short_slots.append((short_match.group(1), int(short_match.group(2))))
        matches = [
            case_id for case_id in input_case_ids
            if case_id == assignment_key or case_id.startswith(f"{assignment_key}-")
        ]
        if not matches:
            if short_match:
                unmatched_short_slots.append(assignment_key)
                continue
            raise ValueError(f"tasks_by_case references unknown case: {assignment_key}")
        if len(matches) > 1:
            raise ValueError(f"ambiguous tasks_by_case slot: {assignment_key}")
        case_id = matches[0]
        if case_id in resolved_tasks:
            raise ValueError(f"duplicate tasks_by_case resolution: {case_id}")
        resolved_tasks[case_id] = selected_tasks
    if unmatched_short_slots:
        batches = {batch for batch, _ in short_slots}
        slot_numbers = sorted(number for _, number in short_slots)
        is_frozen_preregistration = (
            len(short_slots) == len(tasks_by_case)
            and len(batches) == 1
            and slot_numbers == list(range(1, len(slot_numbers) + 1))
            and bool(resolved_tasks)
            and all(case_id.startswith(f"{next(iter(batches))}-") for case_id in input_case_ids)
            and len(resolved_tasks) == len(input_case_ids)
        )
        if not is_frozen_preregistration:
            raise ValueError(f"tasks_by_case references unknown case: {unmatched_short_slots[0]}")
    records = []
    seen: set[str] = set()
    seen_subjects: set[str] = set()
    for raw_path in input_files:
        path = Path(raw_path)
        _reject_symlink(path, "input source")
        if not path.is_file() or path.name.lower() != "input.md":
            raise ValueError(f"input file must be a regular input.md: {path}")
        if any(marker in part.lower().replace("_", " ").replace("-", " ") for part in path.parts for marker in _FORBIDDEN_INTAKE_MARKERS):
            raise ValueError(f"input path contains forbidden feedback/labels/report/known facts marker: {path}")
        content = path.read_bytes()
        text = content.decode("utf-8")
        lowered = text.lower().replace("_", " ").replace("-", " ")
        if any(marker.replace("_", " ").replace("-", " ") in lowered for marker in _FORBIDDEN_INTAKE_MARKERS):
            raise ValueError(f"input contains forbidden feedback/labels/report/known facts content: {path}")
        case_id = _validate_case_id(path.parent.name)
        if case_id in seen:
            raise ValueError(f"duplicate case: {case_id}")
        seen.add(case_id)
        chart = parse_canonical_chart(text, case_id)
        subject_id_hash = _canonical_sha({key: chart[key] for key in ("four_pillars", "sex_marker")})
        if subject_id_hash in seen_subjects:
            raise ValueError(f"duplicate subject: {case_id}")
        seen_subjects.add(subject_id_hash)
        selected = resolved_tasks.get(case_id, sorted(task_ids))
        if not selected or len(set(selected)) != len(selected):
            raise ValueError(f"case tasks must be unique and non-empty: {case_id}")
        unknown = set(selected) - task_ids
        if unknown:
            raise ValueError(f"unknown task: {sorted(unknown)[0]}")
        records.append({
            "case_id": case_id,
            "input_file": str(path.absolute()),
            "input_sha256": _sha256(content),
            "subject_id_hash": subject_id_hash,
            "task_ids": sorted(selected),
        })
    clean_tasks = [{field: task[field] for field in _TASK_BUNDLE_FIELDS} for task in tasks["tasks"]]
    bundle_tasks = {"schema_version": tasks.get("schema_version"), "tasks": clean_tasks}
    return {
        "schema_version": _PROSPECTIVE_SCHEMA,
        "generated_at": _now(),
        "operator": operator,
        "schools": schools,
        "task_catalog_sha256": _canonical_sha(bundle_tasks),
        "records": sorted(records, key=lambda item: item["case_id"]),
    }


def prepare_blind_bundle(
    intake: dict[str, Any], tasks: Path, rule_snapshot: Path, target_dir: Path, *, dry_run: bool = False,
) -> dict[str, Any]:
    """Create a whitelist-only bundle of canonical charts and artifact references."""
    if intake.get("schema_version") != _PROSPECTIVE_SCHEMA or not isinstance(intake.get("records"), list):
        raise ValueError("prospective intake schema is invalid")
    if _contains_forbidden_field(intake):
        raise ValueError("intake contains forbidden feedback/labels/report/known facts fields")
    target = Path(target_dir)
    _reject_symlink(target, "bundle target")
    if target.exists():
        raise ValueError(f"bundle target must not exist: {target}")
    files: dict[str, bytes] = {}
    task_source, rule_source = Path(tasks), Path(rule_snapshot)
    for source in (task_source, rule_source):
        _reject_symlink(source, "bundle source")
        if not source.is_file():
            raise ValueError(f"bundle source must be a regular file: {source}")
    task_bytes, rule_bytes = task_source.read_bytes(), rule_source.read_bytes()
    task_document = json.loads(task_bytes.decode("utf-8"))
    rule_document = json.loads(rule_bytes.decode("utf-8"))
    intake_safe_tasks = {
        **task_document,
        "tasks": [
            {key: value for key, value in task.items() if key != "label_schema"}
            for task in task_document.get("tasks", [])
        ],
    }
    if _contains_forbidden_field(intake_safe_tasks):
        raise ValueError("tasks contain forbidden feedback/labels/report/known facts fields or strings")
    known_tasks = set(_task_map(task_document))
    try:
        clean_tasks = [{field: task[field] for field in _TASK_BUNDLE_FIELDS} for task in task_document["tasks"]]
    except KeyError as error:
        raise ValueError(f"task catalog missing scoring field: {error.args[0]}") from error
    snapshot_id = rule_document.get("rule_snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise ValueError("rule snapshot requires rule_snapshot_id")
    bundled_task_document = {"schema_version": task_document.get("schema_version"), "tasks": clean_tasks}
    if isinstance(task_document.get("task_catalog_version"), str) and task_document["task_catalog_version"]:
        bundled_task_document["task_catalog_version"] = task_document["task_catalog_version"]
    files["tasks.json"] = json.dumps(
        bundled_task_document, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    legacy_tasks = json.dumps(
        {"schema_version": task_document.get("schema_version"), "tasks": clean_tasks},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    if intake.get("task_catalog_sha256") not in {_sha256(files["tasks.json"]), _sha256(legacy_tasks)}:
        raise ValueError("intake task catalog hash does not match canonical bundled tasks")
    bundled_rule_reference: dict[str, Any] = {
        "rule_snapshot_id": snapshot_id,
        "sha256": _sha256(rule_bytes),
    }
    if isinstance(rule_document.get("schools"), list):
        bundled_rule_reference["schools"] = rule_document["schools"]
    if isinstance(rule_document.get("runners"), dict):
        bundled_rule_reference["runners"] = rule_document["runners"]
    files["rule-snapshot.json"] = json.dumps(
        bundled_rule_reference, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    safe_intake = {
        "schema_version": "school-capability-blind-intake/v1",
        "schools": sorted(intake.get("schools", [])),
        "records": [
            {"case_id": row.get("case_id"), "task_ids": sorted(row.get("task_ids", []))}
            for row in intake["records"] if isinstance(row, dict)
        ],
    }
    files["intake.json"] = json.dumps(
        safe_intake, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    seen: set[str] = set()
    seen_subjects: set[str] = set()
    for row in intake["records"]:
        if not isinstance(row, dict) or set(row) != _INTAKE_RECORD_FIELDS:
            raise ValueError("prospective intake record is invalid")
        case_id = _validate_case_id(row["case_id"])
        if case_id in seen:
            raise ValueError(f"duplicate case: {case_id}")
        seen.add(case_id)
        if set(row["task_ids"]) - known_tasks:
            raise ValueError(f"unknown task in case: {case_id}")
        source = Path(row["input_file"])
        _reject_symlink(source, "case input source")
        if not source.is_file() or source.name != "input.md":
            raise ValueError(f"case input source must be a regular input.md: {case_id}")
        if source.parent.name != case_id:
            raise ValueError(f"case input parent must equal case_id: {case_id}")
        content = source.read_bytes()
        try:
            normalized = content.decode("utf-8").lower().replace("_", " ").replace("-", " ")
        except UnicodeDecodeError as error:
            raise ValueError(f"case input must be UTF-8 text: {case_id}") from error
        if any(marker.replace("_", " ").replace("-", " ") in normalized for marker in _FORBIDDEN_INTAKE_MARKERS):
            raise ValueError(f"case input contains forbidden feedback/labels/report/known facts content: {case_id}")
        if _sha256(content) != row["input_sha256"]:
            raise ValueError(f"case input hash changed: {case_id}")
        chart = parse_canonical_chart(content.decode("utf-8"), case_id)
        subject_hash = _canonical_sha({key: chart[key] for key in ("four_pillars", "sex_marker")})
        if subject_hash != row["subject_id_hash"]:
            raise ValueError(f"case subject hash changed: {case_id}")
        if subject_hash in seen_subjects:
            raise ValueError(f"duplicate subject: {case_id}")
        seen_subjects.add(subject_hash)
        files[f"cases/{case_id}/chart.json"] = json.dumps(
            chart, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
    hashes = {name: _sha256(content) for name, content in sorted(files.items())}
    bundle_hash = _sha256(json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    manifest = {"schema_version": _BLIND_BUNDLE_SCHEMA, "bundle_sha256": bundle_hash, "files": hashes}
    if dry_run:
        return manifest
    target.parent.mkdir(parents=True, exist_ok=True)
    _reject_symlink(target, "bundle target")
    temporary = Path(tempfile.mkdtemp(prefix=f".{target.name}.", dir=target.parent))
    try:
        for name, content in files.items():
            destination = temporary / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        (temporary / "bundle-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if target.exists() or target.is_symlink():
            raise ValueError(f"bundle target must not exist: {target}")
        os.replace(temporary, target)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return manifest


def _safe_output(path: Path) -> Path:
    if path.is_symlink():
        raise ValueError(f"output target must not be a symlink: {path}")
    _reject_symlink(path.parent, "output parent")
    return path.resolve()


def _write(path: Path, payload: dict[str, Any], dry_run: bool) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if dry_run:
        print(text, end="")
        return
    target = _safe_output(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        if target.is_symlink() or target.parent.resolve() != target.parent:
            raise ValueError("output path changed or became a symlink before replace")
        os.replace(temporary, target)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _prospective_intake_command(args: argparse.Namespace) -> None:
    assignments = _read_json(Path(args.tasks_by_case)) if args.tasks_by_case else None
    payload = register_prospective_intake(
        [Path(item) for item in args.input], _read_json(Path(args.tasks)), args.school,
        args.operator, tasks_by_case=assignments,
    )
    _write(Path(args.out), payload, args.dry_run)


def _single_case_intake_command(args: argparse.Namespace) -> None:
    assignments = _read_json(Path(args.tasks_by_case))
    case_root = Path(args.case_root)
    existing_subject_hashes: set[str] = set()
    if case_root.exists():
        _reject_symlink(case_root, "single-case root")
        for candidate in case_root.glob("*/*--intake--v*.json"):
            _reject_symlink(candidate, "existing single-case intake")
            document = _read_json(candidate)
            if document.get("schema_version") != "prospective-single-case-intake/v1":
                continue
            subject_hash = document.get("subject_id_hash")
            if not _is_sha256(subject_hash):
                raise ValueError(f"existing single-case intake has invalid subject_id_hash: {candidate}")
            existing_subject_hashes.add(subject_hash)
    intake, question = build_single_case_intake(
        Path(args.input),
        _read_json(Path(args.tasks)),
        args.school,
        args.operator,
        assignments,
        _read_json(Path(args.future_question)),
        created_at=args.created_at,
        case_root=case_root,
        existing_subject_hashes=existing_subject_hashes,
    )
    question_path = Path(question["artifact_path"])
    intake_path = Path(intake["artifact_path"])
    result = {
        "status": "DRY_RUN" if args.dry_run else "PUBLISHED",
        "publication_order": ["future_question", "intake"],
        "future_question": {
            "artifact_path": question_path.as_posix(),
            "document": question,
        },
        "intake": {
            "artifact_path": intake_path.as_posix(),
            "document": intake,
        },
    }
    if args.dry_run:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if question_path.exists() and not question_path.is_symlink():
        question_ref = ArtifactRef(
            artifact_path=question_path.as_posix(),
            artifact_sha256=str(question["artifact_sha256"]),
        )
        existing_question = validate_parent_ref(question_ref)
        if existing_question != question:
            raise ValueError(f"output already exists with different content: {question_path}")
    else:
        question_ref = publish_new_json(question_path, question, dry_run=False)
    try:
        publish_new_json(intake_path, intake, dry_run=False)
    except BaseException as error:
        raise ValueError(
            "RECOVERABLE_HOLD: future question published but intake publication failed; "
            f"published_parent={question_ref.artifact_path}@sha256:{question_ref.artifact_sha256}; "
            f"cause={error}"
        ) from error
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _prepare_blind_command(args: argparse.Namespace) -> None:
    payload = prepare_blind_bundle(
        _read_json(Path(args.intake)), Path(args.tasks), Path(args.rule_snapshot),
        Path(args.target_dir), dry_run=args.dry_run,
    )
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _prepare_single_case_blind_command(args: argparse.Namespace) -> None:
    payload = prepare_single_case_blind_bundle(
        _read_json(Path(args.intake)),
        _read_json(Path(args.future_question)),
        Path(args.tasks),
        Path(args.rule_snapshot),
        Path(args.target_dir),
        dry_run=args.dry_run,
    )
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _inventory_command(args: argparse.Namespace) -> None:
    payload = build_inventory(Path(args.cases_dir), Path(args.reports_dir), _read_json(Path(args.review_decisions)))
    _write(Path(args.out), payload, args.dry_run)


def _labels_command(args: argparse.Namespace) -> None:
    observations = [json.loads(line) for line in Path(args.observations).read_text(encoding="utf-8").splitlines() if line.strip()]
    payload = build_unbound_labels(observations, _read_json(Path(args.tasks)))
    _write(Path(args.out), payload, args.dry_run)


def _manifest_command(args: argparse.Namespace) -> None:
    routes = _read_json(Path(args.routes)).get("routes_by_case", {}) if args.routes else {}
    payload = build_reviewed_manifest(_read_json(Path(args.inventory)), args.reviewed_by, args.expected_school, routes)
    _write(Path(args.out), payload, args.dry_run)


def _config_command(args: argparse.Namespace) -> None:
    payload = build_evaluation_config(
        _read_json(Path(args.manifest)), _read_json(Path(args.baseline)),
        args.evidence_grade, args.evaluated_at,
        _read_json(Path(args.tasks)) if args.tasks else None,
    )
    _write(Path(args.out), payload, args.dry_run)


def _bind_command(args: argparse.Namespace) -> None:
    payload = bind_labels_after_freeze(_read_json(Path(args.labels)), _read_json(Path(args.frozen_run)))
    _write(Path(args.out), payload, args.dry_run)


def _environment_witness_key(variable: str) -> bytes:
    value = os.environ.get(variable)
    if not value:
        raise ValueError(f"witness key environment variable is missing: {variable}")
    return value.encode("utf-8")


def _witness_append_command(args: argparse.Namespace) -> None:
    existing = _read_json(Path(args.registry)) if args.registry else None
    payload = append_witness_event(existing, _read_json(Path(args.event)), _environment_witness_key(args.witness_key_env))
    _write(Path(args.out), payload, args.dry_run)


def _witness_verify_command(args: argparse.Namespace) -> None:
    verify_witness_registry(_read_json(Path(args.registry)), _environment_witness_key(args.witness_key_env))
    print("VALID")


def _witness_verify_single_case_command(args: argparse.Namespace) -> None:
    from engine.evaluation.prospective_evidence import verify_single_case_freeze_chain

    payload = verify_single_case_freeze_chain(
        intake_path=Path(args.intake),
        bundle_root=Path(args.bundle_root),
        frozen_run_path=Path(args.frozen_run),
        registry_path=Path(args.registry),
        witness_key=_environment_witness_key(args.witness_key_env),
        expected_external_root=args.external_root,
        verified_at=args.verified_at,
        verifier=args.verifier,
    )
    output = Path(args.out)
    payload = {
        **payload,
        "artifact_path": output.as_posix(),
    }
    payload["artifact_sha256"] = canonical_artifact_sha256(payload)
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        unsigned = {key: value for key, value in payload.items() if key != "artifact_sha256"}
        publish_new_json(output, unsigned, dry_run=False)
        print(payload["artifact_sha256"])


def _issue_feedback_release_command(args: argparse.Namespace) -> None:
    from engine.evaluation.prospective_evidence import build_feedback_release_credential

    payload = build_feedback_release_credential(
        _read_json(Path(args.verification)),
        _read_json(Path(args.roles)),
        _read_json(Path(args.leakage_scan)),
        created_at=args.created_at,
    )
    output = Path(args.out)
    payload = {
        **payload,
        "artifact_path": output.as_posix(),
    }
    payload["artifact_sha256"] = canonical_artifact_sha256(payload)
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        unsigned = {key: value for key, value in payload.items() if key != "artifact_sha256"}
        publish_new_json(output, unsigned, dry_run=False)
        print(payload["artifact_sha256"])


def _require_canonical_artifact_output(payload: dict[str, Any], output: Path) -> None:
    expected = Path(payload["artifact_path"])
    if output != expected:
        raise ValueError(f"formal artifact output must use canonical artifact_path: {expected}")


def _release_immediate_template_command(args: argparse.Namespace) -> None:
    from engine.evaluation.prospective_evidence import validate_release_credential

    release, _ = validate_release_credential(_read_json(Path(args.release)))
    template = _read_json(Path("templates/prospective-immediate-retrospective-v1.json"))
    payload = {
        **template,
        "case_id": release["case_id"],
        "facts": [],
    }
    _write(Path(args.out), payload, args.dry_run)


def _collect_immediate_retrospective_command(args: argparse.Namespace) -> None:
    from engine.evaluation.prospective_evidence import (
        collect_immediate_retrospective,
        validate_release_credential,
    )

    release = _read_json(Path(args.release))
    validate_release_credential(release)
    payload = collect_immediate_retrospective(
        release,
        lambda: _read_json(Path(args.custody_input)),
        collected_at=args.collected_at,
        custodian=args.custodian,
    )
    output = Path(args.out)
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _require_canonical_artifact_output(payload, output)
        unsigned = {key: value for key, value in payload.items() if key != "artifact_sha256"}
        publish_new_json(output, unsigned, dry_run=False)
        print(payload["artifact_sha256"])


def _publish_canonical_artifact(payload: dict[str, Any], output: Path, *, dry_run: bool) -> None:
    if dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    _require_canonical_artifact_output(payload, output)
    unsigned = {key: value for key, value in payload.items() if key != "artifact_sha256"}
    publish_new_json(output, unsigned, dry_run=False)
    print(payload["artifact_sha256"])


def _collect_future_observation_command(args: argparse.Namespace) -> None:
    from engine.evaluation.prospective_evidence import collect_future_observation

    payload = collect_future_observation(
        _read_json(Path(args.future_question)),
        _read_json(Path(args.frozen_run)),
        _read_json(Path(args.observation)),
        collected_at=args.collected_at,
    )
    _publish_canonical_artifact(payload, Path(args.out), dry_run=args.dry_run)


def _bind_future_observation_command(args: argparse.Namespace) -> None:
    from engine.evaluation.prospective_evidence import bind_future_observation

    payload = bind_future_observation(_read_json(Path(args.unbound)))
    _publish_canonical_artifact(payload, Path(args.out), dry_run=args.dry_run)


def _build_case_completion_command(args: argparse.Namespace) -> None:
    from engine.evaluation.prospective_evidence import build_case_completion

    payload = build_case_completion(
        freeze_verification=_read_json(Path(args.freeze_verification)),
        immediate_bound=_read_json(Path(args.immediate_bound)) if args.immediate_bound else None,
        future_bound=_read_json(Path(args.future_bound)) if args.future_bound else None,
        stopped_incident=_read_json(Path(args.stopped_incident)) if args.stopped_incident else None,
        created_at=args.created_at,
    )
    _publish_canonical_artifact(payload, Path(args.out), dry_run=args.dry_run)


def _validate_command(args: argparse.Namespace) -> int:
    key_value = os.environ.get(args.witness_key_env) if args.witness_key_env else None
    result = validate_dataset(
        _read_json(Path(args.manifest)), _read_json(Path(args.labels)), _read_json(Path(args.frozen_run)),
        _read_json(Path(args.prospective_intake)) if args.prospective_intake else None,
        _read_json(Path(args.blind_bundle_manifest)) if args.blind_bundle_manifest else None,
        _read_json(Path(args.reveal_provenance)) if args.reveal_provenance else None,
        Path(args.blind_bundle_root) if args.blind_bundle_root else None,
        _read_json(Path(args.witness_registry)) if args.witness_registry else None,
        key_value.encode("utf-8") if key_value else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "GO" else 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prospective = commands.add_parser("prospective-intake")
    prospective.add_argument("--input", action="append", required=True)
    prospective.add_argument("--tasks", required=True)
    prospective.add_argument("--school", action="append", required=True)
    prospective.add_argument("--operator", required=True)
    prospective.add_argument("--tasks-by-case")
    prospective.add_argument("--out", required=True)
    prospective.add_argument("--dry-run", action="store_true")
    prospective.set_defaults(handler=_prospective_intake_command)
    single_case = commands.add_parser("single-case-intake")
    single_case.add_argument("--input", required=True)
    single_case.add_argument("--tasks", required=True)
    single_case.add_argument("--school", action="append", required=True)
    single_case.add_argument("--operator", required=True)
    single_case.add_argument("--tasks-by-case", required=True)
    single_case.add_argument("--future-question", required=True)
    single_case.add_argument("--case-root", required=True)
    single_case.add_argument("--created-at", required=True)
    single_case.add_argument("--dry-run", action="store_true")
    single_case.set_defaults(handler=_single_case_intake_command)
    blind = commands.add_parser("prepare-blind")
    blind.add_argument("--intake", required=True)
    blind.add_argument("--tasks", required=True)
    blind.add_argument("--rule-snapshot", required=True)
    blind.add_argument("--target-dir", required=True)
    blind.add_argument("--dry-run", action="store_true")
    blind.set_defaults(handler=_prepare_blind_command)
    single_blind = commands.add_parser("prepare-single-case-blind")
    single_blind.add_argument("--intake", required=True)
    single_blind.add_argument("--future-question", required=True)
    single_blind.add_argument("--tasks", required=True)
    single_blind.add_argument("--rule-snapshot", required=True)
    single_blind.add_argument("--target-dir", required=True)
    single_blind.add_argument("--dry-run", action="store_true")
    single_blind.set_defaults(handler=_prepare_single_case_blind_command)
    inventory = commands.add_parser("inventory")
    inventory.add_argument("--cases-dir", required=True)
    inventory.add_argument("--reports-dir", required=True)
    inventory.add_argument("--review-decisions", required=True)
    inventory.add_argument("--out", required=True)
    inventory.add_argument("--dry-run", action="store_true")
    inventory.set_defaults(handler=_inventory_command)
    labels = commands.add_parser("labels")
    labels.add_argument("--observations", required=True)
    labels.add_argument("--tasks", required=True)
    labels.add_argument("--out", required=True)
    labels.add_argument("--dry-run", action="store_true")
    labels.set_defaults(handler=_labels_command)
    manifest = commands.add_parser("manifest")
    manifest.add_argument("--inventory", required=True)
    manifest.add_argument("--reviewed-by", required=True)
    manifest.add_argument("--expected-school", action="append", required=True)
    manifest.add_argument("--routes")
    manifest.add_argument("--out", required=True)
    manifest.add_argument("--dry-run", action="store_true")
    manifest.set_defaults(handler=_manifest_command)
    config = commands.add_parser("evaluation-config")
    config.add_argument("--manifest", required=True)
    config.add_argument("--baseline", required=True)
    config.add_argument("--tasks")
    config.add_argument("--evidence-grade", required=True)
    config.add_argument("--evaluated-at", required=True)
    config.add_argument("--out", required=True)
    config.add_argument("--dry-run", action="store_true")
    config.set_defaults(handler=_config_command)
    bind = commands.add_parser("bind-labels")
    bind.add_argument("--labels", required=True)
    bind.add_argument("--frozen-run", required=True)
    bind.add_argument("--out", required=True)
    bind.add_argument("--dry-run", action="store_true")
    bind.set_defaults(handler=_bind_command)
    witness_append = commands.add_parser("witness-append")
    witness_append.add_argument("--registry")
    witness_append.add_argument("--event", required=True)
    witness_append.add_argument("--out", required=True)
    witness_append.add_argument("--witness-key-env", default="SCHOOL_CAPABILITY_WITNESS_KEY")
    witness_append.add_argument("--dry-run", action="store_true")
    witness_append.set_defaults(handler=_witness_append_command)
    witness_verify = commands.add_parser("witness-verify")
    witness_verify.add_argument("--registry", required=True)
    witness_verify.add_argument("--witness-key-env", default="SCHOOL_CAPABILITY_WITNESS_KEY")
    witness_verify.set_defaults(handler=_witness_verify_command)
    single_verify = commands.add_parser("witness-verify-single-case")
    single_verify.add_argument("--intake", required=True)
    single_verify.add_argument("--bundle-root", required=True)
    single_verify.add_argument("--frozen-run", required=True)
    single_verify.add_argument("--registry", required=True)
    single_verify.add_argument("--external-root", required=True)
    single_verify.add_argument("--verifier", required=True)
    single_verify.add_argument("--verified-at", required=True)
    single_verify.add_argument("--out", required=True)
    single_verify.add_argument("--witness-key-env", default="SCHOOL_CAPABILITY_WITNESS_KEY")
    single_verify.add_argument("--dry-run", action="store_true")
    single_verify.set_defaults(handler=_witness_verify_single_case_command)
    feedback_release = commands.add_parser("issue-feedback-release")
    feedback_release.add_argument("--verification", required=True)
    feedback_release.add_argument("--roles", required=True)
    feedback_release.add_argument("--leakage-scan", required=True)
    feedback_release.add_argument("--created-at", required=True)
    feedback_release.add_argument("--out", required=True)
    feedback_release.add_argument("--dry-run", action="store_true")
    feedback_release.set_defaults(handler=_issue_feedback_release_command)
    immediate_template = commands.add_parser("release-immediate-retrospective-template")
    immediate_template.add_argument("--release", required=True)
    immediate_template.add_argument("--out", required=True)
    immediate_template.add_argument("--dry-run", action="store_true")
    immediate_template.set_defaults(handler=_release_immediate_template_command)
    immediate_collect = commands.add_parser("collect-immediate-retrospective")
    immediate_collect.add_argument("--release", required=True)
    immediate_collect.add_argument("--custody-input", required=True)
    immediate_collect.add_argument("--collected-at", required=True)
    immediate_collect.add_argument("--custodian", required=True)
    immediate_collect.add_argument("--out", required=True)
    immediate_collect.add_argument("--dry-run", action="store_true")
    immediate_collect.set_defaults(handler=_collect_immediate_retrospective_command)
    future_collect = commands.add_parser("collect-future-observation")
    future_collect.add_argument("--future-question", required=True)
    future_collect.add_argument("--frozen-run", required=True)
    future_collect.add_argument("--observation", required=True)
    future_collect.add_argument("--collected-at", required=True)
    future_collect.add_argument("--out", required=True)
    future_collect.add_argument("--dry-run", action="store_true")
    future_collect.set_defaults(handler=_collect_future_observation_command)
    future_bind = commands.add_parser("bind-future-observation")
    future_bind.add_argument("--unbound", required=True)
    future_bind.add_argument("--out", required=True)
    future_bind.add_argument("--dry-run", action="store_true")
    future_bind.set_defaults(handler=_bind_future_observation_command)
    completion = commands.add_parser("build-case-completion")
    completion.add_argument("--freeze-verification", required=True)
    completion.add_argument("--immediate-bound")
    completion.add_argument("--future-bound")
    completion.add_argument("--stopped-incident")
    completion.add_argument("--created-at", required=True)
    completion.add_argument("--out", required=True)
    completion.add_argument("--dry-run", action="store_true")
    completion.set_defaults(handler=_build_case_completion_command)
    validate = commands.add_parser("validate")
    validate.add_argument("--manifest", required=True)
    validate.add_argument("--labels", required=True)
    validate.add_argument("--frozen-run", required=True)
    validate.add_argument("--prospective-intake")
    validate.add_argument("--blind-bundle-manifest")
    validate.add_argument("--blind-bundle-root")
    validate.add_argument("--reveal-provenance")
    validate.add_argument("--witness-registry")
    validate.add_argument("--witness-key-env", default="SCHOOL_CAPABILITY_WITNESS_KEY")
    validate.set_defaults(handler=_validate_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        result = args.handler(args)
        return result if isinstance(result, int) else 0
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        print(f"INVALID: {error}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
