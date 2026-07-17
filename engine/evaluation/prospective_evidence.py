from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.evaluation.freeze import verify_frozen_run
from engine.evaluation.models import FrozenBlindRun
from engine.evaluation.prospective_artifacts import (
    ArtifactRef,
    canonical_artifact_sha256,
    single_case_artifact_path,
    validate_parent_ref,
)
from engine.evaluation.prospective_single_case import (
    ContaminationError,
    validate_future_question_registration,
    validate_single_case_intake,
    verify_single_case_bundle,
)
from tools.school_capability_dataset import verify_witness_registry


_SHA256 = re.compile(r"[0-9a-f]{64}")
_AUTOMATED_IDENTITY_PREFIXES = ("automated", "agent", "ai-")
_IMMEDIATE_EVIDENCE_CLASS = "prediction_first_immediate_retrospective"
_FUTURE_EVIDENCE_CLASS = "future_observation"
_FUTURE_LABELS = frozenset({"occurred", "not_observed", "no_data"})
_CUSTODY_SCHEMA = "prospective-immediate-retrospective-custody/v1"
_CUSTODY_FIELDS = frozenset({"schema_version", "case_id", "facts"})
_CUSTODY_FACT_FIELDS = frozenset({
    "task_id", "label", "occurred_at", "relative_time", "source_refs",
})
_FORBIDDEN_EVIDENCE_FIELDS = frozenset({
    "prediction", "probability", "rationale", "report", "runner", "reviewer",
    "evidence_class",
})
_REQUIRED_ROLES = frozenset({
    "witness", "intake_operator", "runner_operator", "outcome_custodian",
})
_OPTIONAL_REVIEW_ROLES = frozenset({"reviewer_a", "reviewer_b", "adjudicator"})


def _stop(message: str) -> ContaminationError:
    return ContaminationError(f"STOP: {message}")


def _read_json(path: Path, description: str) -> tuple[dict[str, Any], bytes]:
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise _stop(f"{description} must be a regular non-symlink file")
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _stop(f"{description} must be valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise _stop(f"{description} must be a JSON object")
    return value, raw


def _named_human_identity(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value.strip().lower().startswith(_AUTOMATED_IDENTITY_PREFIXES)
    ):
        raise ValueError(f"{field} must be a named human identity reference")
    return value.strip()


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _utc(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"{field} must be an ISO 8601 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO 8601 UTC timestamp") from error
    if parsed.tzinfo != timezone.utc:
        raise ValueError(f"{field} must be an ISO 8601 UTC timestamp")
    return parsed


def _artifact_ref(document: Mapping[str, Any]) -> dict[str, str]:
    path = document.get("artifact_path")
    digest = document.get("artifact_sha256")
    if not isinstance(path, str) or not path or not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
        raise _stop("artifact parent reference is invalid")
    return {"artifact_path": path, "artifact_sha256": digest}


def _validate_parent_tree(
    document: Mapping[str, Any], *, visited: set[tuple[str, str]] | None = None,
) -> None:
    """Re-read every reachable parent, including raw bundle files without embedded digests."""
    parents = document.get("parents", [])
    if not isinstance(parents, list):
        raise _stop("artifact parents must be a list")
    seen = set() if visited is None else visited
    for parent in parents:
        if not isinstance(parent, Mapping):
            raise _stop("artifact parent reference is invalid")
        reference = _artifact_ref(parent)
        identity = (reference["artifact_path"], reference["artifact_sha256"])
        if identity in seen:
            continue
        seen.add(identity)
        path = Path(reference["artifact_path"])
        if path.is_symlink() or not path.is_file():
            raise _stop("artifact parent must be a regular non-symlink file")
        try:
            raw = path.read_bytes()
            actual = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise _stop(f"artifact parent drift or hash mismatch: {error}") from error
        if not isinstance(actual, dict):
            raise _stop("artifact parent must be a JSON object")
        try:
            if "artifact_sha256" in actual:
                actual = validate_parent_ref(ArtifactRef(**reference))
            elif hashlib.sha256(raw).hexdigest() != reference["artifact_sha256"]:
                raise ValueError("raw parent digest mismatch")
        except (OSError, TypeError, ValueError) as error:
            raise _stop(f"artifact parent drift or hash mismatch: {error}") from error
        if "parents" in actual:
            _validate_parent_tree(actual, visited=seen)


def _actual_raw_json_parent(reference: Mapping[str, Any], description: str) -> dict[str, Any]:
    ref = _artifact_ref(reference)
    path = Path(ref["artifact_path"])
    if path.is_symlink() or not path.is_file():
        raise _stop(f"{description} must be a regular non-symlink file")
    try:
        raw = path.read_bytes()
        actual = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _stop(f"{description} must be valid UTF-8 JSON") from error
    if not isinstance(actual, dict) or hashlib.sha256(raw).hexdigest() != ref["artifact_sha256"]:
        raise _stop(f"{description} drift or hash mismatch")
    return actual


def _actual_sealed_artifact(path: Path, description: str) -> dict[str, Any]:
    document, _ = _read_json(path, description)
    reference = _artifact_ref(document)
    if Path(reference["artifact_path"]) != Path(path):
        raise _stop(f"{description} artifact_path differs from actual path")
    try:
        actual = validate_parent_ref(ArtifactRef(**reference))
    except (OSError, TypeError, ValueError) as error:
        raise _stop(f"{description} parent drift or hash mismatch: {error}") from error
    return actual


def _verify_frozen_parent(
    frozen_run_path: Path,
    *,
    intake: Mapping[str, Any],
    bundle: Mapping[str, Any],
) -> dict[str, Any]:
    frozen = _actual_sealed_artifact(frozen_run_path, "single-case frozen run")
    try:
        run = FrozenBlindRun.from_dict(frozen["frozen_run"])
        verify_frozen_run(run)
    except (KeyError, TypeError, ValueError) as error:
        raise _stop(f"single-case frozen run is invalid: {error}") from error
    manifest = bundle["manifest"]
    if (
        frozen.get("schema_version") != "school-capability-single-case-staged-run/v1"
        or frozen.get("case_id") != intake.get("case_id")
        or frozen.get("subject_id_hash") != intake.get("subject_id_hash")
        or frozen.get("intake_sha256") != intake.get("artifact_sha256")
        or frozen.get("bundle_sha256") != manifest.get("bundle_sha256")
        or frozen.get("bundle_manifest_sha256") != manifest.get("artifact_sha256")
        or frozen.get("created_at") != run.frozen_at
    ):
        raise _stop("single-case frozen run parent binding mismatch")
    expected_manifest_ref = {
        "artifact_path": bundle["manifest_path"].as_posix(),
        "artifact_sha256": manifest["artifact_sha256"],
    }
    if expected_manifest_ref not in frozen.get("parents", []):
        raise _stop("single-case frozen run does not bind the actual bundle manifest")
    return frozen


def verify_single_case_freeze_chain(
    *,
    intake_path: Path,
    bundle_root: Path,
    frozen_run_path: Path,
    registry_path: Path,
    witness_key: bytes,
    expected_external_root: str,
    verified_at: str,
    verifier: str,
) -> dict[str, Any]:
    """Re-read and authenticate one exact registered/prepared/freeze segment."""
    if not isinstance(witness_key, bytes) or not witness_key:
        raise ValueError("witness key must be non-empty bytes")
    if not isinstance(expected_external_root, str) or _SHA256.fullmatch(expected_external_root) is None:
        raise ValueError("expected external root must be a lowercase SHA-256")
    verification_time = _utc(verified_at, "verified_at")
    verifier_identity = _named_human_identity(verifier, "verifier")

    intake = _actual_sealed_artifact(Path(intake_path), "single-case intake")
    row = validate_single_case_intake(intake)
    bundle = verify_single_case_bundle(Path(bundle_root))
    manifest = bundle["manifest"]
    if (
        manifest.get("case_id") != intake.get("case_id")
        or manifest.get("subject_id_hash") != intake.get("subject_id_hash")
        or _artifact_ref(intake) not in manifest.get("parents", [])
    ):
        raise _stop("single-case bundle parent binding mismatch")
    frozen = _verify_frozen_parent(
        Path(frozen_run_path), intake=intake, bundle=bundle,
    )
    registry, _ = _read_json(Path(registry_path), "witness registry")
    registry_ref = _artifact_ref(registry)
    if Path(registry_ref["artifact_path"]) != Path(registry_path):
        raise _stop("witness registry artifact_path differs from actual path")
    try:
        actual_registry = validate_parent_ref(ArtifactRef(**registry_ref))
    except (OSError, TypeError, ValueError) as error:
        raise _stop(f"witness registry parent drift or hash mismatch: {error}") from error
    if (
        actual_registry.get("case_id") != row["case_id"]
        or actual_registry.get("subject_id_hash") != row["subject_id_hash"]
    ):
        raise _stop("witness registry artifact identity does not match actual single case")
    authenticated_registry = {
        "schema_version": actual_registry.get("schema_version"),
        "events": actual_registry.get("events"),
    }
    try:
        verify_witness_registry(authenticated_registry, witness_key)
    except (TypeError, ValueError) as error:
        raise ValueError(f"witness HMAC verification failed: {error}") from error

    events = actual_registry.get("events")
    if not isinstance(events, list) or len(events) != 3:
        raise _stop("witness registry requires exactly three events")
    if [event.get("event_type") for event in events if isinstance(event, dict)] != [
        "registered", "prepared", "freeze",
    ]:
        raise _stop("witness event segment order must be registered -> prepared -> freeze")
    if any(event.get("payload", {}).get("case_id") != row["case_id"] for event in events):
        raise _stop("witness event case does not match actual single case")

    expected_payloads = [
        {
            "case_id": row["case_id"],
            "input_sha256": row["input_sha256"],
            "subject_id_hash": row["subject_id_hash"],
        },
        {"case_id": row["case_id"], "bundle_sha256": manifest["bundle_sha256"]},
        {
            "case_id": row["case_id"],
            "freeze_hash": frozen["frozen_run"]["freeze_hash"],
        },
    ]
    if [event["payload"] for event in events] != expected_payloads:
        raise _stop("witness event payload does not match actual intake, bundle, and freeze")
    registered_at, prepared_at, freeze_at = (
        _utc(event["occurred_at"], f"witness {event['event_type']} occurred_at")
        for event in events
    )
    intake_at = _utc(intake["created_at"], "intake created_at")
    bundle_at = _utc(manifest["created_at"], "bundle created_at")
    actual_freeze_at = _utc(frozen["frozen_run"]["frozen_at"], "freeze_at")
    if verification_time <= actual_freeze_at:
        raise ValueError("verified_at must be later than freeze")
    if not (
        registered_at == intake_at
        and bundle_at <= prepared_at
        and registered_at < prepared_at < freeze_at
        and freeze_at == actual_freeze_at
    ):
        raise _stop("witness event times violate registered < prepared < freeze or freeze_at binding")
    actual_root = events[-1]["event_hash"]
    if not __import__("hmac").compare_digest(actual_root, expected_external_root):
        raise _stop("external registry root mismatch")

    artifact_path = single_case_artifact_path(
        Path(intake["artifact_path"]).parent.parent,
        row["case_id"],
        "freeze-verification",
        1,
    )
    payload: dict[str, Any] = {
        "schema_version": "prospective-single-case-freeze-verification/v1",
        "case_id": row["case_id"],
        "subject_id_hash": row["subject_id_hash"],
        "created_at": verified_at,
        "artifact_path": artifact_path.as_posix(),
        "parents": [
            _artifact_ref(intake),
            {
                "artifact_path": bundle["manifest_path"].as_posix(),
                "artifact_sha256": manifest["artifact_sha256"],
            },
            _artifact_ref(frozen),
            registry_ref,
        ],
        "status": "VERIFIED",
        "freeze_at": frozen["frozen_run"]["frozen_at"],
        "verified_at": verified_at,
        "witness_identity_ref": verifier_identity,
        "witness_event_types": ["registered", "prepared", "freeze"],
        "external_registry_root": actual_root,
    }
    return {**payload, "artifact_sha256": canonical_artifact_sha256(payload)}


def _validated_verification(verification: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(verification, Mapping):
        raise ValueError("feedback release requires a verification artifact")
    value = dict(verification)
    if value.get("status") != "VERIFIED":
        raise ValueError("feedback release requires VERIFIED freeze verification")
    if value.get("schema_version") != "prospective-single-case-freeze-verification/v1":
        raise ValueError("feedback release verification schema is invalid")
    if value.get("artifact_sha256") != canonical_artifact_sha256(value):
        raise ValueError("feedback release verification hash is invalid")
    _artifact_ref(value)
    _utc(value.get("freeze_at"), "freeze_at")
    return value


def _validate_roles(roles: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(roles, Mapping):
        raise ValueError("role separation requires a role mapping")
    result = dict(roles)
    keys = set(result)
    if not _REQUIRED_ROLES <= keys or keys - (_REQUIRED_ROLES | _OPTIONAL_REVIEW_ROLES):
        raise ValueError("role separation requires witness, intake, runner, and outcome custodian roles")
    for role, identity in result.items():
        _named_human_identity(identity, f"role separation {role}")
    if len(set(result.values())) != len(result):
        raise ValueError("role separation requires pairwise independent identities")
    if ("reviewer_a" in result) != ("reviewer_b" in result):
        raise ValueError("role separation requires reviewer A and B together")
    return result


def build_feedback_release_credential(
    frozen_or_verification: Mapping[str, Any],
    roles: Mapping[str, str] | None = None,
    leakage_scan: Mapping[str, Any] | None = None,
    *,
    created_at: str,
) -> dict[str, Any]:
    """Open feedback intake from an immutable freeze; v1 verification remains compatible."""
    if frozen_or_verification.get("schema_version") == "school-capability-single-case-staged-run/v1":
        frozen = _actual_supplied_artifact(frozen_or_verification, "frozen run")
        try:
            run = FrozenBlindRun.from_dict(frozen["frozen_run"])
            verify_frozen_run(run)
            _validate_parent_tree(frozen)
        except (KeyError, TypeError, ValueError) as error:
            raise _stop(f"frozen result is invalid: {error}") from error
        created = _utc(created_at, "created_at")
        if created < _utc(frozen["freeze_at"], "freeze_at"):
            raise ValueError("feedback release cannot predate freeze")
        parent_path = Path(frozen["artifact_path"])
        payload: dict[str, Any] = {
            "schema_version": "prospective-feedback-release/v2",
            "case_id": frozen["case_id"],
            "subject_id_hash": frozen["subject_id_hash"],
            "created_at": created_at,
            "artifact_path": single_case_artifact_path(
                parent_path.parent.parent, frozen["case_id"], "feedback-release", 1,
            ).as_posix(),
            "parents": [_artifact_ref(frozen)],
            "release_status": "RELEASED",
            "freeze_at": frozen["freeze_at"],
        }
        return {**payload, "artifact_sha256": canonical_artifact_sha256(payload)}

    verified = _validated_verification(frozen_or_verification)
    separated_roles = _validate_roles(roles)
    if (
        not isinstance(leakage_scan, Mapping)
        or type(leakage_scan.get("marker_count")) is not int
        or dict(leakage_scan) != {"marker_count": 0, "status": "PASS"}
    ):
        raise _stop("feedback leakage scan failed")
    _utc(created_at, "created_at")
    if _utc(created_at, "created_at") < _utc(verified["verified_at"], "verified_at"):
        raise ValueError("feedback release cannot predate verification")
    verification_path = Path(verified["artifact_path"])
    artifact_path = single_case_artifact_path(
        verification_path.parent.parent, verified["case_id"], "feedback-release", 1,
    )
    payload = {
        "schema_version": "prospective-feedback-release/v1",
        "case_id": verified["case_id"],
        "subject_id_hash": verified["subject_id_hash"],
        "created_at": created_at,
        "artifact_path": artifact_path.as_posix(),
        "parents": [_artifact_ref(verified)],
        "release_status": "RELEASED",
        "freeze_at": verified["freeze_at"],
        "roles": separated_roles,
        "leakage_scan": {"marker_count": 0, "status": "PASS"},
    }
    return {**payload, "artifact_sha256": canonical_artifact_sha256(payload)}


def validate_release_credential(release: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Re-read the actual release and verification parent before custody access."""
    if not isinstance(release, Mapping):
        raise ValueError("immediate retrospective requires a release credential")
    supplied = dict(release)
    if supplied.get("release_status") != "RELEASED":
        raise ValueError("immediate retrospective requires RELEASED credential")
    if supplied.get("schema_version") not in {
        "prospective-feedback-release/v1", "prospective-feedback-release/v2",
    }:
        raise ValueError("immediate retrospective release schema is invalid")
    if supplied.get("artifact_sha256") != canonical_artifact_sha256(supplied):
        raise ValueError("immediate retrospective release hash is invalid")
    reference = _artifact_ref(supplied)
    try:
        actual = validate_parent_ref(ArtifactRef(**reference))
    except (OSError, TypeError, ValueError) as error:
        raise _stop(f"release parent drift or hash mismatch: {error}") from error
    if actual != supplied:
        raise _stop("release credential differs from actual sealed release")
    parents = actual.get("parents")
    if not isinstance(parents, list) or len(parents) != 1 or not isinstance(parents[0], dict):
        raise ValueError("release credential requires one frozen parent")
    try:
        parent = validate_parent_ref(ArtifactRef(**parents[0]))
    except (OSError, TypeError, ValueError) as error:
        raise _stop(f"release parent drift or hash mismatch: {error}") from error
    if actual["schema_version"] == "prospective-feedback-release/v2":
        if parent.get("schema_version") != "school-capability-single-case-staged-run/v1":
            raise ValueError("v2 feedback release requires a frozen result parent")
        try:
            verify_frozen_run(FrozenBlindRun.from_dict(parent["frozen_run"]))
            _validate_parent_tree(parent)
        except (KeyError, TypeError, ValueError) as error:
            raise _stop(f"release frozen parent is invalid: {error}") from error
        if any(actual.get(field) != parent.get(field) for field in ("case_id", "subject_id_hash", "freeze_at")):
            raise _stop("release summary differs from actual frozen parent")
        if _utc(actual["created_at"], "release created_at") < _utc(parent["freeze_at"], "freeze_at"):
            raise ValueError("release cannot predate freeze")
        return actual, parent

    verified = _validated_verification(parent)
    _validate_parent_tree(verified)
    if any(actual.get(field) != verified.get(field) for field in ("case_id", "subject_id_hash", "freeze_at")):
        raise _stop("release summary differs from actual verification parent")
    if actual.get("created_at") is None or _utc(actual["created_at"], "release created_at") < _utc(
        verified["verified_at"], "verified_at",
    ):
        raise ValueError("release cannot predate verification")
    validated_roles = _validate_roles(actual.get("roles"))
    if actual.get("leakage_scan") != {"marker_count": 0, "status": "PASS"}:
        raise _stop("release leakage scan is invalid")
    return {**actual, "roles": validated_roles}, verified


def _contains_forbidden_evidence_field(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key).lower().replace("-", "_") in _FORBIDDEN_EVIDENCE_FIELDS
            or _contains_forbidden_evidence_field(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_evidence_field(item) for item in value)
    return False


def _task_catalog_for_release(release: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    release_parent = validate_parent_ref(ArtifactRef(**release["parents"][0]))
    for reference in release_parent.get("parents", []):
        parent = validate_parent_ref(ArtifactRef(**reference))
        if parent.get("schema_version") != "prospective-single-case-blind-bundle/v1":
            continue
        tasks_path = Path(reference["artifact_path"]).parent / "tasks.json"
        if tasks_path.is_symlink() or not tasks_path.is_file():
            raise _stop("actual task catalog is missing from the verified bundle")
        raw = tasks_path.read_bytes()
        expected = parent.get("files", {}).get("tasks.json")
        if hashlib.sha256(raw).hexdigest() != expected:
            raise _stop("actual task catalog differs from the verified bundle manifest")
        try:
            catalog = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise _stop("actual task catalog is invalid") from error
        tasks = catalog.get("tasks") if isinstance(catalog, dict) else None
        if not isinstance(tasks, list):
            raise _stop("actual task catalog requires tasks")
        result = {
            task.get("task_id"): task for task in tasks
            if isinstance(task, dict) and isinstance(task.get("task_id"), str)
        }
        if len(result) != len(tasks):
            raise _stop("actual task catalog requires unique task identities")
        return result
    raise _stop("verified chain does not contain the actual task catalog")


def _validate_task_label(task: Mapping[str, Any], label: object) -> None:
    method = task.get("scoring_method")
    schema = task.get("label_schema")
    if not isinstance(schema, Mapping):
        raise ValueError("task label schema is invalid")
    if method == "binary_probability":
        allowed = {schema.get("positive_label"), schema.get("negative_label")}
        valid = isinstance(label, str) and label in allowed
    elif method in {"ordinal", "multiclass_probability"}:
        valid = isinstance(label, str) and label in schema.get("labels", [])
    elif method == "time_window":
        valid = (
            isinstance(label, Mapping)
            and set(label) == {"occurred", "year"}
            and type(label.get("occurred")) is bool
            and (
                type(label.get("year")) is int
                if label.get("occurred") is True
                else label.get("year") is None
            )
        )
    else:
        valid = not task.get("quantifiable") and isinstance(label, (str, int, float, bool))
    if not valid:
        raise ValueError("custody fact label does not match task schema")


def _validate_custody_payload(
    raw: Mapping[str, Any], *, case_id: str, tasks: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(raw, Mapping) or set(raw) != _CUSTODY_FIELDS:
        raise ValueError("custody payload schema contains missing or forbidden field")
    if raw.get("schema_version") != _CUSTODY_SCHEMA or raw.get("case_id") != case_id:
        raise ValueError("custody payload schema or case identity is invalid")
    facts = raw.get("facts")
    if not isinstance(facts, list) or not facts:
        raise ValueError("custody payload requires facts")
    validated: list[dict[str, Any]] = []
    for fact in facts:
        if not isinstance(fact, Mapping) or set(fact) != _CUSTODY_FACT_FIELDS:
            raise ValueError("custody fact schema contains missing or forbidden field")
        if _contains_forbidden_evidence_field(fact):
            raise ValueError("custody fact contains nested forbidden prediction field")
        task_id = fact.get("task_id")
        label = fact.get("label")
        relative_time = fact.get("relative_time")
        source_refs = fact.get("source_refs")
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("custody fact task_id must be non-empty")
        task = tasks.get(task_id)
        if task is None:
            raise ValueError("custody fact task_id is not present in the verified task catalog")
        if relative_time not in {"before_or_at_freeze", "after_freeze", "unknown"}:
            raise ValueError("custody fact relative_time is invalid")
        if relative_time != "unknown":
            _validate_task_label(task, label)
        if (
            not isinstance(source_refs, list) or not source_refs
            or any(not isinstance(ref, str) or not ref.startswith("custody://") for ref in source_refs)
        ):
            raise ValueError("custody fact source_refs must be custody references")
        validated.append({**dict(fact), "high_risk": task.get("high_risk") is True})
    return validated


def _classify_immediate_fact(
    fact: Mapping[str, Any], *, case_id: str, cutoff: str,
) -> dict[str, Any]:
    occurred_at = fact.get("occurred_at")
    relative_time = fact["relative_time"]
    if occurred_at is None or relative_time == "unknown":
        if occurred_at is not None or relative_time != "unknown":
            raise ValueError("custody fact unknown relative_time conflicts with occurred_at")
        classification = "no_data"
        occurred_at = None
        scorable = False
    else:
        occurred = _utc(occurred_at, "custody fact occurred_at")
        if occurred > _utc(cutoff, "freeze_at") or relative_time == "after_freeze":
            raise ValueError("fact after freeze cannot enter immediate retrospective")
        if relative_time != "before_or_at_freeze":
            raise ValueError("custody fact relative_time conflicts with occurred_at")
        classification = "immediate_fact"
        scorable = fact.get("high_risk") is not True
    identity = canonical_artifact_sha256({
        "case_id": case_id,
        "evidence_class": _IMMEDIATE_EVIDENCE_CLASS,
        "task_id": fact["task_id"],
        "fact": {
            "label": fact["label"],
            "occurred_at": occurred_at,
            "relative_time": relative_time,
            "source_refs": fact["source_refs"],
        },
    })
    result = {
        **dict(fact),
        "occurred_at": occurred_at,
        "classification": classification,
        "scorable": scorable,
        "label_identity": identity,
    }
    if fact.get("high_risk") is True:
        result["review_status"] = "pending_independent_dual_review"
    return result


def collect_immediate_retrospective(
    release: Mapping[str, Any],
    custody_reader: Callable[[], Mapping[str, Any]],
    *,
    collected_at: str,
    custodian: str,
) -> dict[str, Any]:
    """Collect structured pre-freeze facts, opening custody only after release validation."""
    verified_release, release_parent = validate_release_credential(release)
    collection_time = _utc(collected_at, "collected_at")
    parent_ready_at = release_parent.get("verified_at", release_parent.get("freeze_at"))
    if collection_time < _utc(parent_ready_at, "release parent ready_at") or collection_time < _utc(
        verified_release["created_at"], "release created_at",
    ):
        raise ValueError("collected_at cannot predate freeze or release")
    custodian_identity = _named_human_identity(custodian, "custodian")
    released_roles = verified_release.get("roles")
    if released_roles is not None:
        if custodian_identity != released_roles["outcome_custodian"]:
            raise ValueError("custodian must match the released outcome custodian")
        if custodian_identity in {
            released_roles["witness"], released_roles["intake_operator"],
            released_roles["runner_operator"],
        }:
            raise ValueError("custodian must remain role-separated from release operations")

    tasks = _task_catalog_for_release(verified_release)
    raw = custody_reader()
    facts = [
        _classify_immediate_fact(
            fact, case_id=verified_release["case_id"], cutoff=verified_release["freeze_at"],
        )
        for fact in _validate_custody_payload(
            raw, case_id=verified_release["case_id"], tasks=tasks,
        )
    ]
    identities = [fact["label_identity"] for fact in facts]
    if len(set(identities)) != len(identities):
        raise ValueError("duplicate label identity")
    release_path = Path(verified_release["artifact_path"])
    existing_identities: set[str] = set()
    for path in release_path.parent.parent.rglob("*--immediate-retrospective-*--v*.json"):
        if path.is_symlink() or not path.is_file():
            continue
        document, _ = _read_json(path, "existing immediate retrospective artifact")
        for fact in document.get("facts", []):
            if isinstance(fact, Mapping) and isinstance(fact.get("label_identity"), str):
                existing_identities.add(fact["label_identity"])
    if existing_identities.intersection(identities):
        raise ValueError("duplicate label identity already exists in another artifact")
    artifact_path = single_case_artifact_path(
        release_path.parent.parent,
        verified_release["case_id"],
        "immediate-retrospective-unbound",
        1,
    )
    payload: dict[str, Any] = {
        "schema_version": "prospective-immediate-retrospective-unbound/v1",
        "case_id": verified_release["case_id"],
        "subject_id_hash": verified_release["subject_id_hash"],
        "created_at": collected_at,
        "artifact_path": artifact_path.as_posix(),
        "parents": [_artifact_ref(verified_release)],
        "evidence_class": _IMMEDIATE_EVIDENCE_CLASS,
        "fact_cutoff_at": verified_release["freeze_at"],
        "collected_after_verification": True,
        "custodian": custodian_identity,
        "facts": facts,
    }
    return {**payload, "artifact_sha256": canonical_artifact_sha256(payload)}


def bind_immediate_labels(unbound: Mapping[str, Any]) -> dict[str, Any]:
    """Bind only classified immediate facts; preserve no-data rows without scoring them."""
    if not isinstance(unbound, Mapping):
        raise ValueError("immediate unbound artifact is required")
    source = dict(unbound)
    if (
        source.get("schema_version") != "prospective-immediate-retrospective-unbound/v1"
        or source.get("evidence_class") != _IMMEDIATE_EVIDENCE_CLASS
        or source.get("artifact_sha256") != canonical_artifact_sha256(source)
    ):
        raise ValueError("immediate unbound artifact is invalid")
    facts = source.get("facts")
    if not isinstance(facts, list) or any(
        not isinstance(fact, dict)
        or fact.get("classification") not in {"immediate_fact", "no_data"}
        or fact.get("scorable") is not (
            fact.get("classification") == "immediate_fact"
            and fact.get("high_risk") is not True
        )
        or (
            fact.get("high_risk") is True
            and fact.get("review_status") != "pending_independent_dual_review"
        )
        for fact in facts
    ):
        raise ValueError("immediate facts are invalid")
    identities = [fact.get("label_identity") for fact in facts]
    if any(not isinstance(identity, str) or _SHA256.fullmatch(identity) is None for identity in identities):
        raise ValueError("immediate label identity is invalid")
    if len(set(identities)) != len(identities):
        raise ValueError("duplicate label identity")
    artifact_path = single_case_artifact_path(
        Path(source["artifact_path"]).parent.parent,
        source["case_id"],
        "immediate-retrospective-bound",
        1,
    )
    payload: dict[str, Any] = {
        "schema_version": "prospective-immediate-retrospective-bound/v1",
        "case_id": source["case_id"],
        "subject_id_hash": source["subject_id_hash"],
        "created_at": source["created_at"],
        "artifact_path": artifact_path.as_posix(),
        "parents": [_artifact_ref(source)],
        "evidence_class": _IMMEDIATE_EVIDENCE_CLASS,
        "fact_cutoff_at": source["fact_cutoff_at"],
        "custodian": source["custodian"],
        "facts": [dict(fact) for fact in facts],
        "scorable_label_count": sum(fact["scorable"] for fact in facts),
    }
    return {**payload, "artifact_sha256": canonical_artifact_sha256(payload)}


def _actual_supplied_artifact(document: Mapping[str, Any], description: str) -> dict[str, Any]:
    if not isinstance(document, Mapping):
        raise ValueError(f"{description} artifact is required")
    supplied = dict(document)
    reference = _artifact_ref(supplied)
    try:
        actual = validate_parent_ref(ArtifactRef(**reference))
    except (OSError, TypeError, ValueError) as error:
        raise _stop(f"{description} parent drift or hash mismatch: {error}") from error
    if actual != supplied:
        raise _stop(f"{description} supplied artifact differs from actual parent")
    return actual


def _validated_future_parents(
    registration: Mapping[str, Any], frozen_run: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    question = _actual_supplied_artifact(registration, "future-question")
    frozen = _actual_supplied_artifact(frozen_run, "frozen run")
    if frozen.get("schema_version") != "school-capability-single-case-staged-run/v1":
        raise ValueError("future observation frozen parent schema is invalid")
    try:
        run = FrozenBlindRun.from_dict(frozen["frozen_run"])
        verify_frozen_run(run)
    except (KeyError, TypeError, ValueError) as error:
        raise _stop(f"future observation frozen parent is invalid: {error}") from error
    try:
        validated_question = validate_future_question_registration(
            question, freeze_at=run.frozen_at,
        )
        _validate_parent_tree(frozen)
    except ValueError as error:
        raise _stop(f"future-question parent is invalid: {error}") from error
    question_ref = _artifact_ref(validated_question)
    if (
        frozen.get("case_id") != validated_question.get("case_id")
        or frozen.get("subject_id_hash") != validated_question.get("subject_id_hash")
        or frozen.get("created_at") != run.frozen_at
        or frozen.get("future_question_registration_sha256") != validated_question.get("artifact_sha256")
        or question_ref not in frozen.get("parents", [])
    ):
        raise _stop("future observation question/frozen case, subject, freeze, or hash binding mismatch")
    return validated_question, frozen


def _future_no_data_reason(observation: Mapping[str, Any]) -> str | None:
    if observation.get("contact_state") == "lost_contact":
        return "lost_contact"
    if observation.get("conflict_state") != "none":
        return "conflicting_sources"
    if observation.get("observed_at") is None:
        return "unknown_observation_time"
    return None


def _validate_future_sources(
    observation: Mapping[str, Any], question: Mapping[str, Any], *, require_registered_coverage: bool,
) -> list[str]:
    refs = observation.get("source_refs")
    if (
        not isinstance(refs, list) or not refs
        or any(not isinstance(ref, str) or not ref.startswith("custody://") for ref in refs)
    ):
        raise ValueError("future observation source_refs must be custody references")
    requirements = question.get("verification_source_requirements")
    if require_registered_coverage and (
        not isinstance(requirements, list) or any(
            not isinstance(requirement, str)
            or not any(ref == requirement or ref.startswith(requirement.rstrip("/") + "/") for ref in refs)
            for requirement in requirements
        )
    ):
        raise ValueError("future observation source coverage does not satisfy registered requirements")
    return list(refs)


def _future_task(frozen: Mapping[str, Any], task_id: str) -> dict[str, Any]:
    for reference in frozen.get("parents", []):
        if not isinstance(reference, Mapping) or not str(reference.get("artifact_path", "")).endswith("tasks.json"):
            continue
        path = Path(str(reference["artifact_path"]))
        try:
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != reference.get("artifact_sha256"):
                raise ValueError("task catalog hash mismatch")
            document = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            raise _stop(f"future task catalog parent is invalid: {error}") from error
        tasks = document.get("tasks") if isinstance(document, dict) else None
        matches = [task for task in tasks or [] if isinstance(task, dict) and task.get("task_id") == task_id]
        if len(matches) != 1:
            raise _stop("future task identity is missing or duplicated in frozen catalog")
        return matches[0]
    raise _stop("future frozen parent does not bind a task catalog")


def collect_future_observation(
    registration: Mapping[str, Any],
    frozen_run: Mapping[str, Any],
    observation: Mapping[str, Any],
    *,
    collected_at: str,
) -> dict[str, Any]:
    """Collect one release-independent future observation against immutable parents."""
    question, frozen = _validated_future_parents(registration, frozen_run)
    if not isinstance(observation, Mapping):
        raise ValueError("future observation must be an object")
    value = dict(observation)
    if value.get("future_task_id") != question["future_task_id"]:
        raise ValueError("future observation task binding mismatch")
    requested_label = value.get("label")
    if requested_label not in _FUTURE_LABELS:
        raise ValueError("invalid future observation label")
    _validate_future_sources(
        value, question, require_registered_coverage=requested_label == "not_observed",
    )
    if value.get("contact_state", "available") not in {"available", "lost_contact"}:
        raise ValueError("future observation contact_state is invalid")
    if value.get("conflict_state") not in {"none", "conflicting_sources"}:
        raise ValueError("future observation conflict_state is invalid")

    freeze_time = _utc(frozen["created_at"], "freeze_at")
    start_time = _utc(question["observation_window"]["start_at"], "observation_window.start_at")
    end_time = _utc(question["observation_window"]["end_at"], "observation_window.end_at")
    collection_time = _utc(collected_at, "collected_at")
    if collection_time > _now_utc():
        raise ValueError("collected_at cannot be later than the current time")
    if collection_time < freeze_time:
        raise ValueError("collected_at cannot predate freeze or future window")
    observed_raw = value.get("observed_at")
    observed_time = _utc(observed_raw, "observed_at") if observed_raw is not None else None
    if observed_time is not None and collection_time < observed_time:
        raise ValueError("collected_at must not be earlier than observed_at")

    no_data_reason = _future_no_data_reason(value)
    label = "no_data" if no_data_reason is not None else requested_label
    if label == "occurred":
        if observed_time is None or observed_time <= freeze_time or not start_time <= observed_time <= end_time:
            raise ValueError("occurred observation must be after freeze and inside the observation window")
    elif label == "not_observed":
        if collection_time < end_time or observed_time is None or observed_time < end_time:
            raise ValueError("window has not matured for not_observed")
        coverage = value.get("source_coverage")
        if not isinstance(coverage, Mapping) or dict(coverage) != {
            "start_at": question["observation_window"]["start_at"],
            "end_at": question["observation_window"]["end_at"],
        }:
            raise ValueError("not_observed requires source coverage for the complete window")
    elif label == "no_data" and observed_time is not None and observed_time < freeze_time:
        raise ValueError("future no_data observed_at cannot predate freeze")

    task = _future_task(frozen, question["future_task_id"])
    high_risk = task.get("high_risk") is True
    normalized = {
        **value,
        "label": label,
        "high_risk": high_risk,
        "scorable": label != "no_data" and not high_risk,
        "collected_at": collected_at,
        "observation_window": dict(question["observation_window"]),
    }
    if high_risk:
        normalized["review_status"] = "pending_independent_dual_review"
    if no_data_reason is not None:
        normalized["no_data_reason"] = no_data_reason
    label_identity = canonical_artifact_sha256({
        "case_id": question["case_id"],
        "evidence_class": _FUTURE_EVIDENCE_CLASS,
        "future_task_id": question["future_task_id"],
        "observed_at": observed_raw,
    })
    root = Path(question["artifact_path"]).parent.parent
    for path in root.rglob("*--future-observation-*--v*.json"):
        if path.is_symlink() or not path.is_file():
            continue
        existing, _ = _read_json(path, "existing future observation artifact")
        if existing.get("label_identity") == label_identity:
            raise ValueError("duplicate label identity already exists in another future artifact")

    artifact_path = single_case_artifact_path(
        root, question["case_id"], "future-observation-unbound", 1,
    )
    payload: dict[str, Any] = {
        "schema_version": "prospective-future-observation-unbound/v1",
        "case_id": question["case_id"],
        "subject_id_hash": question["subject_id_hash"],
        "created_at": collected_at,
        "artifact_path": artifact_path.as_posix(),
        "parents": [_artifact_ref(question), _artifact_ref(frozen)],
        "evidence_class": _FUTURE_EVIDENCE_CLASS,
        "label_identity": label_identity,
        "observation": normalized,
    }
    return {**payload, "artifact_sha256": canonical_artifact_sha256(payload)}


def bind_future_observation(unbound: Mapping[str, Any]) -> dict[str, Any]:
    """Bind a validated future observation without making pending review scorable."""
    source = _actual_supplied_artifact(unbound, "future observation unbound")
    if (
        source.get("schema_version") != "prospective-future-observation-unbound/v1"
        or source.get("evidence_class") != _FUTURE_EVIDENCE_CLASS
        or not isinstance(source.get("observation"), Mapping)
    ):
        raise ValueError("future observation unbound schema is invalid")
    _validate_parent_tree(source)
    observation = dict(source["observation"])
    if observation.get("high_risk") is True:
        observation["scorable"] = False
        observation["review_status"] = "pending_independent_dual_review"
    artifact_path = single_case_artifact_path(
        Path(source["artifact_path"]).parent.parent,
        source["case_id"], "future-observation-bound", 1,
    )
    payload: dict[str, Any] = {
        "schema_version": "prospective-future-observation-bound/v1",
        "case_id": source["case_id"],
        "subject_id_hash": source["subject_id_hash"],
        "created_at": source["created_at"],
        "artifact_path": artifact_path.as_posix(),
        "parents": [_artifact_ref(source)],
        "evidence_class": _FUTURE_EVIDENCE_CLASS,
        "label_identity": source["label_identity"],
        "observation": observation,
    }
    return {**payload, "artifact_sha256": canonical_artifact_sha256(payload)}


def apply_high_risk_final_label(
    bound: Mapping[str, Any], finalization: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a new immutable child after reloading both sealed evidence and finalization."""
    if not isinstance(bound, Mapping) or not isinstance(finalization, Mapping):
        raise ValueError("bound evidence and high-risk finalization are required")
    source = _actual_supplied_artifact(bound, "bound high-risk evidence")
    final_artifact = _actual_supplied_artifact(finalization, "high-risk finalization")
    if final_artifact.get("schema_version") != "school-capability-high-risk-finalization/v2":
        raise ValueError("high-risk finalization artifact schema is invalid")
    parents = final_artifact.get("parents")
    if not isinstance(parents, list) or len(parents) not in {2, 3}:
        raise ValueError("high-risk finalization requires actual review parents")
    actual_parents = []
    for reference in parents:
        if not isinstance(reference, Mapping):
            raise ValueError("high-risk finalization parent reference is invalid")
        actual_parents.append(_actual_raw_json_parent(reference, "high-risk finalization parent"))
    review_parents = [
        parent for parent in actual_parents
        if parent.get("schema_version") == "school-capability-high-risk-review/v2"
    ]
    if len(review_parents) != 2:
        raise ValueError("high-risk finalization requires two actual review parents")
    final = final_artifact.get("result")
    if not isinstance(final, Mapping):
        raise ValueError("high-risk finalization result is invalid")
    final = dict(final)
    label = final.get("label")
    if final.get("status") != "GO" or not isinstance(label, Mapping):
        raise ValueError("high-risk finalization must be GO with an A-grade label")
    if label.get("confidence_grade") != "A" or label.get("quantifiable") is not True:
        raise ValueError("high-risk finalization must contain an A-grade quantifiable label")
    evidence_class = source.get("evidence_class")
    if label.get("case_id") != source.get("case_id") or label.get("evidence_class") != evidence_class:
        raise ValueError("high-risk final label evidence class or case ledger mismatch")
    identity = label.get("label_identity")
    if not isinstance(identity, str) or _SHA256.fullmatch(identity) is None:
        raise ValueError("high-risk final label identity is invalid")
    packet_hashes = label.get("review_packet_sha256")
    if (
        not isinstance(packet_hashes, list) or len(packet_hashes) != 2
        or len(set(packet_hashes)) != 2
        or any(not isinstance(item, str) or _SHA256.fullmatch(item) is None for item in packet_hashes)
    ):
        raise ValueError("high-risk final label packet lineage is invalid")

    result = dict(source)
    if evidence_class == _IMMEDIATE_EVIDENCE_CLASS:
        if source.get("schema_version") != "prospective-immediate-retrospective-bound/v1":
            raise ValueError("immediate high-risk source must be a bound artifact")
        facts = [dict(item) for item in source.get("facts", []) if isinstance(item, Mapping)]
        matches = [item for item in facts if item.get("label_identity") == identity]
        if len(matches) != 1:
            raise ValueError("high-risk final label identity does not match one pending ledger row")
        row = matches[0]
    elif evidence_class == _FUTURE_EVIDENCE_CLASS:
        if source.get("schema_version") != "prospective-future-observation-bound/v1":
            raise ValueError("future high-risk source must be a bound artifact")
        if source.get("label_identity") != identity or not isinstance(source.get("observation"), Mapping):
            raise ValueError("high-risk final label identity does not match one pending ledger row")
        row = dict(source["observation"])
    else:
        raise ValueError("high-risk final label evidence class is not prospective")
    if (
        row.get("task_id", row.get("future_task_id")) != label.get("task_id")
        or row.get("high_risk") is not True
        or row.get("review_status") != "pending_independent_dual_review"
        or row.get("label") != label.get("label")
    ):
        raise ValueError("high-risk final label does not match pending task/label lineage")
    if label.get("observation_sha256") != source.get("artifact_sha256"):
        raise ValueError("high-risk final label observation hash does not match actual bound parent")
    parent_packet_hashes = [parent.get("review_packet_sha256") for parent in review_parents]
    if parent_packet_hashes != packet_hashes:
        raise ValueError("high-risk final label packet lineage does not match actual review parents")
    row.update({
        "scorable": True,
        "review_status": "approved_independent_dual_review",
        "review_lineage": {
            key: label[key] for key in (
                "observation_sha256", "evidence_class", "label_identity", "review_packet_sha256",
            )
        },
    })
    if evidence_class == _IMMEDIATE_EVIDENCE_CLASS:
        result["facts"] = [row if item.get("label_identity") == identity else item for item in facts]
        result["scorable_label_count"] = sum(item.get("scorable") is True for item in result["facts"])
    else:
        result["observation"] = row
    artifact_path = single_case_artifact_path(
        Path(source["artifact_path"]).parent.parent,
        source["case_id"],
        "immediate-retrospective-reviewed" if evidence_class == _IMMEDIATE_EVIDENCE_CLASS
        else "future-observation-reviewed",
        1,
    )
    result.update({
        "schema_version": (
            "prospective-immediate-retrospective-reviewed/v1"
            if evidence_class == _IMMEDIATE_EVIDENCE_CLASS
            else "prospective-future-observation-reviewed/v1"
        ),
        "artifact_path": artifact_path.as_posix(),
        "parents": [_artifact_ref(source), _artifact_ref(final_artifact)],
    })
    result.pop("artifact_sha256", None)
    result["artifact_sha256"] = canonical_artifact_sha256(result)
    return result


def _validate_future_completion_chain(document: Mapping[str, Any]) -> None:
    """Require bound/reviewed future evidence to descend from one real registration and freeze."""
    source = dict(document)
    if source.get("schema_version") == "prospective-future-observation-reviewed/v1":
        parents = source.get("parents")
        if not isinstance(parents, list):
            raise _stop("future reviewed parent lineage is invalid")
        bound_matches = []
        for reference in parents:
            if not isinstance(reference, Mapping):
                raise _stop("future reviewed parent lineage is invalid")
            try:
                parent = validate_parent_ref(ArtifactRef(**_artifact_ref(reference)))
            except (OSError, TypeError, ValueError) as error:
                raise _stop(f"future reviewed parent drift or hash mismatch: {error}") from error
            if parent.get("schema_version") == "prospective-future-observation-bound/v1":
                bound_matches.append(parent)
        if len(bound_matches) != 1:
            raise _stop("future reviewed evidence must bind exactly one future bound parent")
        source = bound_matches[0]

    parents = source.get("parents")
    if not isinstance(parents, list) or len(parents) != 1 or not isinstance(parents[0], Mapping):
        raise _stop("future bound evidence must bind exactly one unbound parent")
    try:
        unbound = validate_parent_ref(ArtifactRef(**_artifact_ref(parents[0])))
    except (OSError, TypeError, ValueError) as error:
        raise _stop(f"future unbound parent drift or hash mismatch: {error}") from error
    if (
        unbound.get("schema_version") != "prospective-future-observation-unbound/v1"
        or unbound.get("evidence_class") != _FUTURE_EVIDENCE_CLASS
        or unbound.get("case_id") != source.get("case_id")
        or unbound.get("subject_id_hash") != source.get("subject_id_hash")
        or unbound.get("label_identity") != source.get("label_identity")
        or unbound.get("observation") != source.get("observation")
    ):
        raise _stop("future bound/unbound lineage mismatch")
    unbound_parents = unbound.get("parents")
    if not isinstance(unbound_parents, list) or len(unbound_parents) != 2:
        raise _stop("future unbound evidence requires one registration and one frozen parent")
    try:
        actual = [
            validate_parent_ref(ArtifactRef(**_artifact_ref(reference)))
            for reference in unbound_parents if isinstance(reference, Mapping)
        ]
    except (OSError, TypeError, ValueError) as error:
        raise _stop(f"future unbound lineage parent drift or hash mismatch: {error}") from error
    questions = [item for item in actual if item.get("schema_version") == "prospective-future-question/v1"]
    frozen_runs = [item for item in actual if item.get("schema_version") == "school-capability-single-case-staged-run/v1"]
    if len(questions) != 1 or len(frozen_runs) != 1:
        raise _stop("future unbound evidence requires exactly one registration and frozen parent")
    question, frozen = _validated_future_parents(questions[0], frozen_runs[0])
    observation = unbound.get("observation")
    if (
        not isinstance(observation, Mapping)
        or observation.get("future_task_id") != question.get("future_task_id")
        or observation.get("observation_window") != question.get("observation_window")
        or unbound.get("label_identity") != canonical_artifact_sha256({
            "case_id": question["case_id"],
            "evidence_class": _FUTURE_EVIDENCE_CLASS,
            "future_task_id": question["future_task_id"],
            "observed_at": observation.get("observed_at"),
        })
    ):
        raise _stop("future observation does not match its registered question lineage")


def _validated_optional_completion_parent(
    document: Mapping[str, Any] | None,
    *,
    evidence_class: str,
    case_id: str,
    subject_id_hash: str,
) -> dict[str, Any] | None:
    if document is None:
        return None
    actual = _actual_supplied_artifact(document, f"{evidence_class} completion")
    expected_schemas = {
        _IMMEDIATE_EVIDENCE_CLASS: {
            "prospective-immediate-retrospective-bound/v1",
            "prospective-immediate-retrospective-reviewed/v1",
        },
        _FUTURE_EVIDENCE_CLASS: {
            "prospective-future-observation-bound/v1",
            "prospective-future-observation-reviewed/v1",
        },
    }[evidence_class]
    if (
        actual.get("schema_version") not in expected_schemas
        or actual.get("case_id") != case_id
        or actual.get("subject_id_hash") != subject_id_hash
        or actual.get("evidence_class") != evidence_class
    ):
        raise _stop(f"{evidence_class} completion parent binding or bound schema mismatch")
    _validate_parent_tree(actual)
    if evidence_class == _FUTURE_EVIDENCE_CLASS:
        _validate_future_completion_chain(actual)
    return actual


def build_case_completion(
    *,
    freeze_verification: Mapping[str, Any],
    immediate_bound: Mapping[str, Any] | None,
    future_bound: Mapping[str, Any] | None,
    stopped_incident: Mapping[str, Any] | None,
    created_at: str,
) -> dict[str, Any]:
    """Build a status ledger; retrospective and future completion never collapse."""
    if stopped_incident is not None:
        incident = _actual_supplied_artifact(stopped_incident, "STOP incident")
        if (
            incident.get("schema_version") != "prospective-stop-incident/v1"
            or incident.get("status") != "STOP"
            or incident.get("case_id") != freeze_verification.get("case_id")
            or incident.get("subject_id_hash") != freeze_verification.get("subject_id_hash")
        ):
            raise _stop("STOP incident parent binding mismatch")
        _validate_parent_tree(incident)
        raise ContaminationError("STOP case cannot produce completion")
    verification = _actual_supplied_artifact(freeze_verification, "freeze verification")
    verified = _validated_verification(verification)
    _validate_parent_tree(verified)
    immediate = _validated_optional_completion_parent(
        immediate_bound, evidence_class=_IMMEDIATE_EVIDENCE_CLASS,
        case_id=verified["case_id"], subject_id_hash=verified["subject_id_hash"],
    )
    future = _validated_optional_completion_parent(
        future_bound, evidence_class=_FUTURE_EVIDENCE_CLASS,
        case_id=verified["case_id"], subject_id_hash=verified["subject_id_hash"],
    )
    creation_time = _utc(created_at, "created_at")
    parents = [item for item in (verified, immediate, future) if item is not None]
    if any(creation_time < _utc(parent.get("created_at"), "completion parent created_at") for parent in parents):
        raise ValueError("completion created_at cannot predate verification or a bound parent")
    future_complete = (
        future is not None
        and isinstance(future.get("observation"), Mapping)
        and future["observation"].get("label") in {"occurred", "not_observed"}
        and future["observation"].get("scorable") is True
    )
    artifact_path = single_case_artifact_path(
        Path(verified["artifact_path"]).parent.parent,
        verified["case_id"], "case-completion", 1,
    )
    payload: dict[str, Any] = {
        "schema_version": "prospective-case-completion/v1",
        "case_id": verified["case_id"],
        "subject_id_hash": verified["subject_id_hash"],
        "created_at": created_at,
        "artifact_path": artifact_path.as_posix(),
        "parents": [_artifact_ref(parent) for parent in parents],
        "retrospective_completion_status": (
            "CASE_COMPLETE_FOR_RETROSPECTIVE" if immediate is not None else "PENDING"
        ),
        "future_completion_status": (
            "CASE_COMPLETE_FOR_FUTURE" if future_complete else "PENDING"
        ),
    }
    return {**payload, "artifact_sha256": canonical_artifact_sha256(payload)}


@dataclass(frozen=True)
class FeedbackReleaseEvaluation:
    status: str
    release: dict[str, Any] | None = None
    feedback: Any = None
    reason: str | None = None


def evaluate_feedback_release(
    parents: Mapping[str, Any],
    *,
    roles: Mapping[str, str],
    leakage_scan: Mapping[str, Any],
    feedback_reader: Callable[[Path], Any],
) -> FeedbackReleaseEvaluation:
    """Fail closed before invoking the feedback reader under every invalid gate."""
    try:
        verification = parents.get("verification", parents)
        created_at = parents.get("created_at")
        if not isinstance(created_at, str):
            return FeedbackReleaseEvaluation("HOLD", reason="release created_at is missing")
        release = build_feedback_release_credential(
            verification, roles, leakage_scan, created_at=created_at,
        )
        feedback_path = parents.get("feedback_path")
        if not isinstance(feedback_path, (str, Path)):
            return FeedbackReleaseEvaluation("RELEASED", release=release)
    except Exception as error:
        return FeedbackReleaseEvaluation("HOLD", reason=str(error))
    feedback = feedback_reader(Path(feedback_path))
    return FeedbackReleaseEvaluation("RELEASED", release=release, feedback=feedback)
