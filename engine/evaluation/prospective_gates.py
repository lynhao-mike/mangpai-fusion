from __future__ import annotations

import hashlib
import json
import math
import re
from collections import defaultdict
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.evaluation.freeze import verify_frozen_run
from engine.evaluation.models import FrozenBlindRun
from engine.evaluation.prospective_evidence import _validate_future_completion_chain
from engine.evaluation.prospective_artifacts import (
    ArtifactRef,
    authenticate_path,
    canonical_artifact_sha256,
    validate_parent_ref,
)
from engine.evaluation.prospective_capability_identity import (
    validate_capability_identity_ref,
)
from engine.governance.governance_claim_values import ClaimEvidenceGrade, ClaimKind


COHORT_GATE_IDS = [
    "prediction_capability_candidate_gate_v1",
    "future_empirical_gate_v1",
    "historical_platform_baseline_2026_07_15",
]
_COMPLETION_SCHEMA = "prospective-case-completion/v1"
_STOP_SCHEMA = "prospective-stop-incident/v1"
_MANIFEST_SCHEMA = "prospective-cohort-manifest/v1"
_SHA256 = re.compile(r"[0-9a-f]{64}")
_IMMEDIATE_SCHEMAS = {
    "prospective-immediate-retrospective-bound/v1",
    "prospective-immediate-retrospective-reviewed/v1",
}
_FUTURE_SCHEMAS = {
    "prospective-future-observation-bound/v1",
    "prospective-future-observation-reviewed/v1",
}
_FROZEN_SCHEMA = "school-capability-single-case-staged-run/v1"
_HISTORICAL_NAMES = {
    "six-month-platform-gate-2026-07-15.md",
    "six-month-platform-gate-2026-07-15.json",
}
_HISTORICAL_PATHS = {Path("META") / name for name in _HISTORICAL_NAMES}
_HISTORICAL_SCHEMA = "six-month-platform-gate/v1"


_GATE_EVIDENCE_CLASS = "prediction_first_immediate_retrospective"
_FUTURE_EVIDENCE_CLASS = "future_observation"
_GATE_SCORE_SCHEMA = "prospective-immediate-score-rows/v1"
_GATE_HOLDOUT_SCHEMA = "prospective-competition-holdout/v1"
_GATE_AUDIT_SCHEMA = "prospective-candidate-audits/v1"
_GATE_RESULT_SCHEMA = "prediction-capability-candidate-gate/v1"
_FUTURE_SCORE_SCHEMA = "prospective-future-score-rows/v1"
_FUTURE_HOLDOUT_SCHEMA = "prospective-future-competition-holdout/v1"
_FUTURE_AUDIT_SCHEMA = "prospective-future-candidate-audits/v1"
_FUTURE_RESULT_SCHEMA = "future-empirical-gate/v1"


class FrozenMapping(Mapping[str, Any]):
    """Small recursively safe mapping used by the public gate DTO."""

    __slots__ = ("_items",)

    def __init__(self, value: dict[str, Any]) -> None:
        if type(value) is not dict:
            raise TypeError("immutable mapping input must be an exact dict")
        items: list[tuple[str, Any]] = []
        for key, child in value.items():
            if type(key) is not str:
                raise TypeError("immutable mapping keys must be exact str values")
            if type(child) is dict:
                child = FrozenMapping(child)
            elif type(child) is list:
                child = tuple(child)
            elif isinstance(child, (Mapping, list)):
                raise TypeError("immutable mapping rejects mutable mapping/list subclasses")
            items.append((key, child))
        self._items = tuple(items)

    def __getitem__(self, key: str) -> Any:
        for candidate, value in self._items:
            if candidate == key:
                return value
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return (key for key, _ in self._items)

    def __len__(self) -> int:
        return len(self._items)


@dataclass(frozen=True)
class GateEvidence:
    """Derived candidate-gate facts authenticated from cohort-backed disk artifacts."""

    evidence_class: str
    unique_completed_subjects: int
    task_label_counts: Mapping[str, int]
    positive_counts: Mapping[str, int]
    negative_counts: Mapping[str, int]
    no_data_counts: Mapping[str, int]
    calibration_error_by_task: Mapping[str, float | None]
    competitive_count_by_task: Mapping[str, int]
    selection_change_count: int
    learned_utility: float
    static_utility: float
    high_risk_review_status: str
    hash_audit_status: str
    witness_audit_status: str
    leakage_audit_status: str
    parents: tuple[Mapping[str, str], ...]
    parent_created_at: tuple[str, ...]
    capability_identity_ref: Mapping[str, str] | None = None
    governance_source_ref: ArtifactRef | None = None
    school_id: str | None = None
    task_id: str | None = None
    claim_kind: ClaimKind | None = None
    evidence_grade: ClaimEvidenceGrade | None = None
    capability_version: str | None = None
    provenance_verified: bool = False
    claim_rows: int = 0
    abstain_rows: int = 0
    unsupported_rows: int = 0

    def __post_init__(self) -> None:
        mapping_fields = (
            "task_label_counts",
            "positive_counts",
            "negative_counts",
            "no_data_counts",
            "calibration_error_by_task",
            "competitive_count_by_task",
        )
        for field in mapping_fields:
            value = getattr(self, field)
            if isinstance(value, FrozenMapping):
                continue
            if type(value) is not dict:
                raise TypeError(f"{field} must be an exact dict or immutable mapping")
            object.__setattr__(self, field, FrozenMapping(value))
        if type(self.parents) is not tuple:
            raise TypeError("parents must be an exact immutable tuple")
        immutable_parents: list[FrozenMapping] = []
        for value in self.parents:
            if isinstance(value, FrozenMapping):
                immutable_parents.append(value)
            elif type(value) is dict:
                immutable_parents.append(FrozenMapping(value))
            else:
                raise TypeError("parent refs must be exact dict or immutable mapping values")
        object.__setattr__(self, "parents", tuple(immutable_parents))
        identity = self.capability_identity_ref
        if identity is not None and not isinstance(identity, FrozenMapping):
            if type(identity) is not dict:
                raise TypeError("capability identity ref must be an exact dict or immutable mapping")
            object.__setattr__(self, "capability_identity_ref", FrozenMapping(identity))


class CohortHoldError(ValueError):
    """An auditable capacity HOLD which must not publish a formal manifest."""

    def __init__(self, plan: Mapping[str, Any]):
        self.plan = dict(plan)
        super().__init__(
            f"HOLD: {self.plan['eligible_count']} eligible retrospective completions; "
            f"exactly 10 required (missing {self.plan['missing_count']})"
        )


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


def _ref(document: Mapping[str, Any]) -> dict[str, str]:
    path = document.get("artifact_path")
    digest = document.get("artifact_sha256")
    if (
        not isinstance(path, str)
        or not path
        or not isinstance(digest, str)
        or _SHA256.fullmatch(digest) is None
    ):
        raise ValueError("artifact reference is invalid")
    return {"artifact_path": path, "artifact_sha256": digest}


def _trusted_root(admitted_root: Path) -> Path:
    if not isinstance(admitted_root, Path):
        raise TypeError("admitted_root must be a pathlib.Path")
    if not admitted_root.is_absolute():
        raise ValueError("admitted_root must be absolute")
    return admitted_root


def _load_sealed(
    source: str | Path | ArtifactRef, *, admitted_root: Path
) -> dict[str, Any]:
    root = _trusted_root(admitted_root)
    if isinstance(source, ArtifactRef):
        reference = source
    elif isinstance(source, (str, Path)):
        path = authenticate_path(
            Path(source), admitted_root=root, destination=False
        )
        try:
            supplied = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(
                f"completion parent must be valid UTF-8 JSON: {path}"
            ) from error
        if not isinstance(supplied, dict):
            raise ValueError("completion parent must be a JSON object")
        if Path(str(supplied.get("artifact_path", ""))) != path:
            raise ValueError("completion artifact_path differs from actual disk path")
        reference = ArtifactRef(
            path.as_posix(), str(supplied.get("artifact_sha256", ""))
        )
    else:
        raise TypeError(
            "member completion must be an actual disk path or explicit ArtifactRef"
        )
    document = validate_parent_ref(reference, admitted_root=root)
    if Path(str(document.get("artifact_path", ""))) != Path(reference.artifact_path):
        raise ValueError("sealed artifact_path differs from referenced disk path")
    return document


def _validated_direct_parents(
    document: Mapping[str, Any], description: str, *, admitted_root: Path
) -> list[dict[str, Any]]:
    values = document.get("parents")
    if not isinstance(values, list) or not values:
        raise ValueError(f"{description} parent lineage is missing")
    parents: list[dict[str, Any]] = []
    for value in values:
        if not isinstance(value, Mapping):
            raise ValueError(f"{description} parent lineage is invalid")
        parents.append(
            _load_sealed(ArtifactRef(**_ref(value)), admitted_root=admitted_root)
        )
    return parents


def _validate_completion_lineage(
    document: Mapping[str, Any], *, admitted_root: Path
) -> None:
    parents = _validated_direct_parents(
        document, "case completion", admitted_root=admitted_root
    )
    retrospective_complete = (
        document.get("retrospective_completion_status")
        == "CASE_COMPLETE_FOR_RETROSPECTIVE"
    )
    future_status = document.get("future_completion_status", "PENDING")
    future_complete = future_status == "CASE_COMPLETE_FOR_FUTURE"
    immediate_matches = [
        parent
        for parent in parents
        if parent.get("schema_version") in _IMMEDIATE_SCHEMAS
    ]
    future_matches = [
        parent for parent in parents if parent.get("schema_version") in _FUTURE_SCHEMAS
    ]
    if retrospective_complete != (len(immediate_matches) == 1):
        raise ValueError(
            "retrospective completion status must bind exactly one immediate retrospective parent"
        )
    if len(future_matches) > 1 or (future_complete and len(future_matches) != 1):
        raise ValueError(
            "future completion status must bind exactly one future observation parent"
        )
    if not retrospective_complete and not future_complete:
        raise ValueError(
            "case completion must complete retrospective or future evidence"
        )
    if any(
        parent.get("case_id") != document.get("case_id")
        or parent.get("subject_id_hash") != document.get("subject_id_hash")
        for parent in (*immediate_matches, *future_matches)
    ):
        raise ValueError("case completion parent lineage identity mismatch")


def _validate_stop_lineage(
    document: Mapping[str, Any], *, admitted_root: Path
) -> None:
    parents = _validated_direct_parents(
        document, "STOP incident", admitted_root=admitted_root
    )
    if any(
        parent.get("case_id") != document.get("case_id")
        or parent.get("subject_id_hash") != document.get("subject_id_hash")
        for parent in parents
    ):
        raise ValueError("STOP incident parent lineage identity mismatch")


def _raw_historical(
    ref: ArtifactRef, *, admitted_root: Path
) -> dict[str, str]:
    if not isinstance(ref, ArtifactRef):
        raise TypeError("historical refs must be explicit ArtifactRef values")
    path = authenticate_path(
        Path(ref.artifact_path), admitted_root=admitted_root, destination=False
    )
    if path.name not in _HISTORICAL_NAMES:
        raise ValueError(
            "historical baseline refs must bind the current 2026-07-15 MD and JSON files"
        )
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != ref.artifact_sha256:
        raise ValueError("historical baseline actual byte hash mismatch")
    return {"artifact_path": path.as_posix(), "artifact_sha256": actual}


def _future_parent(
    completion: Mapping[str, Any], *, admitted_root: Path
) -> dict[str, str] | None:
    for value in completion.get("parents", []):
        if not isinstance(value, Mapping):
            continue
        try:
            parent = validate_parent_ref(
                ArtifactRef(**_ref(value)), admitted_root=admitted_root
            )
        except (TypeError, ValueError):
            raise
        if parent.get("schema_version") in _FUTURE_SCHEMAS:
            return _ref(parent)
    return None


def _stopped_audit(document: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "case_id": document["case_id"],
        "subject_id_hash": document["subject_id_hash"],
        "parent": _ref(document),
    }


def _hold_plan(eligible: int, stopped: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "prospective-cohort-hold-plan/v1",
        "status": "HOLD",
        "eligible_count": eligible,
        "required_count": 10,
        "missing_count": max(0, 10 - eligible),
        "stopped_audit": stopped,
        "formal_manifest_created": False,
        "next_action": "collect additional unique retrospective-complete non-STOP cases",
    }


def build_cohort_manifest(
    member_completions: Sequence[str | Path | ArtifactRef],
    historical_refs: Sequence[ArtifactRef],
    *,
    created_at: str,
    admitted_root: Path | None = None,
) -> dict[str, Any]:
    """Build a ten-member cohort from authenticated disk artifacts, never supplied documents."""
    created = _utc(created_at, "created_at")
    root = (
        _trusted_root(admitted_root)
        if admitted_root is not None
        else Path.cwd().absolute()
    )
    historical = sorted(
        (_raw_historical(ref, admitted_root=root) for ref in historical_refs),
        key=lambda item: item["artifact_path"],
    )
    if {
        Path(item["artifact_path"]).name for item in historical
    } != _HISTORICAL_NAMES or len(historical) != 2:
        raise ValueError(
            "historical baseline requires exactly the current two read-only refs"
        )

    completions: list[dict[str, Any]] = []
    stopped: list[dict[str, Any]] = []
    for source in member_completions:
        document = _load_sealed(source, admitted_root=root)
        schema = document.get("schema_version")
        if schema == _STOP_SCHEMA and document.get("status") == "STOP":
            _validate_stop_lineage(document, admitted_root=root)
            stopped.append(_stopped_audit(document))
            continue
        if schema != _COMPLETION_SCHEMA:
            raise ValueError("cohort parent must be a case completion or STOP incident")
        if document.get("retrospective_completion_status") not in {
            "CASE_COMPLETE_FOR_RETROSPECTIVE",
            "PENDING",
        }:
            raise ValueError("cohort member retrospective status is invalid")
        if document.get("future_completion_status", "PENDING") not in {
            "CASE_COMPLETE_FOR_FUTURE",
            "PENDING",
        }:
            raise ValueError("cohort member future status is invalid")
        _validate_completion_lineage(document, admitted_root=root)
        completions.append(document)

    case_ids = [str(item.get("case_id", "")) for item in completions]
    subjects = [str(item.get("subject_id_hash", "")) for item in completions]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("duplicate case_id in cohort parents")
    if len(subjects) != len(set(subjects)):
        raise ValueError("duplicate subject_id_hash in cohort parents")
    if any(not case_id for case_id in case_ids) or any(
        _SHA256.fullmatch(subject) is None for subject in subjects
    ):
        raise ValueError("cohort member case or subject identity is invalid")
    if len(completions) < 10:
        raise CohortHoldError(
            _hold_plan(
                len(completions), sorted(stopped, key=lambda item: item["case_id"])
            )
        )
    if len(completions) != 10:
        raise ValueError(
            "cohort requires exactly 10 eligible retrospective completions"
        )
    if any(
        created < _utc(item.get("created_at"), "completion parent created_at")
        for item in completions
    ):
        raise ValueError("created_at cannot predate any completion parent")

    ordered = sorted(
        completions, key=lambda item: (item["case_id"], item["subject_id_hash"])
    )
    member_set_sha256 = canonical_artifact_sha256(
        {
            "members": [[item["case_id"], item["subject_id_hash"]] for item in ordered],
        }
    )
    cohort_id = f"cohort-{ordered[0]['case_id']}-{ordered[-1]['case_id']}"
    members = []
    for item in ordered:
        future = _future_parent(item, admitted_root=root)
        members.append(
            {
                "case_id": item["case_id"],
                "subject_id_hash": item["subject_id_hash"],
                "parent_created_at": item["created_at"],
                "evidence_availability": {
                    "immediate_retrospective": item.get(
                        "retrospective_completion_status"
                    )
                    == "CASE_COMPLETE_FOR_RETROSPECTIVE",
                    "future_observation": item.get("future_completion_status")
                    == "CASE_COMPLETE_FOR_FUTURE"
                    and future is not None,
                },
                "parents": {"completion": _ref(item), "future": future},
            }
        )
    payload: dict[str, Any] = {
        "schema_version": _MANIFEST_SCHEMA,
        "cohort_id": cohort_id,
        "created_at": created_at,
        "member_set_sha256": member_set_sha256,
        "cohort_size": len(members),
        "candidate_gate_minimum_subjects": 20,
        "candidate_gate_eligible": False,
        "status": "READY_FOR_TASK_10_AGGREGATION",
        "members": members,
        "stopped_audit": sorted(stopped, key=lambda item: item["case_id"]),
        "gate_ids": list(COHORT_GATE_IDS),
        "historical_baseline_refs": historical,
    }
    return {**payload, "artifact_sha256": canonical_artifact_sha256(payload)}


def verify_cohort_manifest(
    manifest: Mapping[str, Any], *, admitted_root: Path | None = None
) -> dict[str, Any]:
    """Verify identity and every immutable parent; report all drift as cohort STOP."""
    drifted: list[dict[str, str]] = []
    try:
        if (
            not isinstance(manifest, Mapping)
            or manifest.get("schema_version") != _MANIFEST_SCHEMA
        ):
            raise ValueError("cohort manifest schema is invalid")
        if manifest.get("artifact_sha256") != canonical_artifact_sha256(manifest):
            raise ValueError("cohort manifest canonical hash mismatch")
        if manifest.get("gate_ids") != COHORT_GATE_IDS:
            raise ValueError("cohort gate IDs changed")
        rebuilt = build_cohort_manifest(
            [
                ArtifactRef(**member["parents"]["completion"])
                for member in manifest["members"]
            ]
            + [
                ArtifactRef(**item["parent"])
                for item in manifest.get("stopped_audit", [])
            ],
            [ArtifactRef(**item) for item in manifest["historical_baseline_refs"]],
            created_at=str(manifest["created_at"]),
            admitted_root=admitted_root,
        )
        if dict(manifest) != rebuilt:
            raise ValueError(
                "cohort manifest differs from authenticated parent reconstruction"
            )
    except Exception as error:
        drifted.append({"error": str(error)})
        return {
            "schema_version": "prospective-cohort-verification/v1",
            "cohort_id": str(manifest.get("cohort_id", ""))
            if isinstance(manifest, Mapping)
            else "",
            "status": "STOP",
            "drifted_parents": drifted,
        }
    return {
        "schema_version": "prospective-cohort-verification/v1",
        "cohort_id": str(manifest["cohort_id"]),
        "status": "VERIFIED",
        "member_set_sha256": str(manifest["member_set_sha256"]),
        "drifted_parents": [],
    }


def _load_gate_artifact(
    path: str | Path, description: str, *, admitted_root: Path
) -> tuple[dict[str, Any], dict[str, str]]:
    source = authenticate_path(
        Path(path), admitted_root=_trusted_root(admitted_root), destination=False
    )
    try:
        document = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{description} must be valid UTF-8 JSON") from error
    if not isinstance(document, dict):
        raise ValueError(f"{description} must be a JSON object")
    digest = document.get("artifact_sha256")
    if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
        raise ValueError(f"{description} artifact hash is invalid")
    validated = validate_parent_ref(
        ArtifactRef(source.as_posix(), digest), admitted_root=admitted_root
    )
    return validated, {"artifact_path": source.as_posix(), "artifact_sha256": digest}


def _require_exact_parents(
    document: Mapping[str, Any],
    expected: Sequence[Mapping[str, str]],
    description: str,
) -> None:
    parents = document.get("parents")
    if not isinstance(parents, list) or parents != [dict(item) for item in expected]:
        raise ValueError(f"{description} parent lineage is inconsistent")


def _require_capability_identity(
    document: Mapping[str, Any],
    expected: Mapping[str, str] | None,
    description: str,
) -> None:
    actual = document.get("capability_identity_ref")
    if expected is None:
        if actual is not None:
            raise ValueError(f"{description} has an untraceable capability identity")
        return
    if actual != dict(expected):
        raise ValueError(f"{description} capability identity lineage is inconsistent")


def _require_governance_source(
    document: Mapping[str, Any],
    expected: ArtifactRef | None,
    description: str,
) -> None:
    actual = document.get("governance_source_ref")
    if expected is None:
        if actual is not None:
            raise ValueError(f"{description} has an untraceable governance source")
        return
    if actual != {
        "artifact_path": expected.artifact_path,
        "artifact_sha256": expected.artifact_sha256,
    }:
        raise ValueError(f"{description} governance source lineage is inconsistent")


def _finite_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a finite number and bool is forbidden")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite")
    return result


def _bool(value: object, field: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field} must be bool")
    return value


def _label_rows_from_manifests(
    manifests: Sequence[Mapping[str, Any]], *, admitted_root: Path
) -> tuple[
    dict[tuple[str, str, str], dict[str, Any]],
    set[str],
    set[str],
    dict[str, dict[str, Any]],
]:
    labels: dict[tuple[str, str, str], dict[str, Any]] = {}
    cases: set[str] = set()
    subjects: set[str] = set()
    frozen_by_case: dict[str, dict[str, Any]] = {}
    for manifest in manifests:
        for member in manifest["members"]:
            case_id = str(member["case_id"])
            subject = str(member["subject_id_hash"])
            if not member.get("evidence_availability", {}).get(
                "immediate_retrospective"
            ):
                continue
            if case_id in cases or subject in subjects:
                raise ValueError(
                    "duplicate case_id or subject_id_hash across verified cohorts"
                )
            cases.add(case_id)
            subjects.add(subject)
            completion = _load_sealed(
                ArtifactRef(**member["parents"]["completion"]),
                admitted_root=admitted_root,
            )
            _validate_completion_lineage(completion, admitted_root=admitted_root)
            completion_parents = _validated_direct_parents(
                completion, "retrospective completion", admitted_root=admitted_root
            )
            immediate = next(
                parent
                for parent in completion_parents
                if parent.get("schema_version") in _IMMEDIATE_SCHEMAS
            )
            frozen_matches = [
                parent
                for parent in completion_parents
                if parent.get("schema_version") == _FROZEN_SCHEMA
            ]
            if len(frozen_matches) != 1:
                raise ValueError(
                    "retrospective completion must bind exactly one frozen prediction parent"
                )
            frozen = frozen_matches[0]
            try:
                run = FrozenBlindRun.from_dict(frozen["frozen_run"])
                verify_frozen_run(run)
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError("frozen prediction parent is invalid") from error
            if (
                frozen.get("case_id") != case_id
                or frozen.get("subject_id_hash") != subject
            ):
                raise ValueError("frozen prediction parent identity mismatch")
            frozen_by_case[case_id] = frozen
            if immediate.get("evidence_class") != _GATE_EVIDENCE_CLASS:
                raise ValueError("immediate parent evidence_class is invalid")
            facts = immediate.get("facts")
            if not isinstance(facts, list):
                raise ValueError("immediate parent facts are missing")
            for fact in facts:
                if not isinstance(fact, Mapping):
                    raise ValueError("immediate fact is invalid")
                task = fact.get("task_id")
                identity = fact.get("label_identity")
                if (
                    not isinstance(task, str)
                    or not task
                    or not isinstance(identity, str)
                    or _SHA256.fullmatch(identity) is None
                ):
                    raise ValueError("immediate fact task or label_identity is invalid")
                key = (case_id, task, identity)
                if key in labels or any(existing[2] == identity for existing in labels):
                    raise ValueError("duplicate label_identity across verified cohorts")
                classification = fact.get("classification")
                scorable = _bool(fact.get("scorable"), "fact.scorable")
                if classification == "no_data":
                    if scorable:
                        raise ValueError("no_data fact cannot be scorable")
                    observed = None
                elif classification == "immediate_fact" and scorable:
                    label = fact.get("label")
                    if label not in {"occurred", "not_observed"}:
                        raise ValueError("scorable immediate label must be binary")
                    observed = label == "occurred"
                elif classification == "immediate_fact" and not scorable:
                    observed = None
                else:
                    raise ValueError("immediate fact classification is inconsistent")
                labels[key] = {
                    "case_id": case_id,
                    "subject_id_hash": subject,
                    "task_id": task,
                    "label_identity": identity,
                    "scorable": scorable,
                    "observed_positive": observed,
                    "classification": classification,
                    "high_risk": fact.get("high_risk") is True,
                }
    return labels, cases, subjects, frozen_by_case


def _future_label_rows_from_manifests(
    manifests: Sequence[Mapping[str, Any]], *, admitted_root: Path
) -> tuple[
    dict[tuple[str, str, str], dict[str, Any]],
    set[str],
    set[str],
    dict[str, dict[str, Any]],
]:
    """Reload future bound/reviewed labels and their frozen prediction parents."""
    labels: dict[tuple[str, str, str], dict[str, Any]] = {}
    cases: set[str] = set()
    subjects: set[str] = set()
    frozen_by_case: dict[str, dict[str, Any]] = {}
    all_cases: set[str] = set()
    all_subjects: set[str] = set()
    for manifest in manifests:
        for member in manifest["members"]:
            case_id = str(member["case_id"])
            subject = str(member["subject_id_hash"])
            if member.get("parents", {}).get("future") is None:
                continue
            if case_id in all_cases or subject in all_subjects:
                raise ValueError(
                    "duplicate case_id or subject_id_hash across verified cohorts"
                )
            all_cases.add(case_id)
            all_subjects.add(subject)
            completion = _load_sealed(
                ArtifactRef(**member["parents"]["completion"]),
                admitted_root=admitted_root,
            )
            completion_parents = _validated_direct_parents(
                completion, "future completion", admitted_root=admitted_root
            )
            frozen_matches = [
                parent
                for parent in completion_parents
                if parent.get("schema_version") == _FROZEN_SCHEMA
            ]
            future_matches = [
                parent
                for parent in completion_parents
                if parent.get("schema_version") in _FUTURE_SCHEMAS
            ]
            if len(frozen_matches) != 1 or len(future_matches) != 1:
                raise ValueError(
                    "future completion must bind exactly one frozen prediction and future label parent"
                )
            frozen, future = frozen_matches[0], future_matches[0]
            try:
                verify_frozen_run(FrozenBlindRun.from_dict(frozen["frozen_run"]))
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(
                    "future frozen prediction parent is invalid"
                ) from error
            if any(
                parent.get("case_id") != case_id
                or parent.get("subject_id_hash") != subject
                for parent in (frozen, future)
            ):
                raise ValueError("future completion parent lineage identity mismatch")
            if future.get("evidence_class") != _FUTURE_EVIDENCE_CLASS:
                raise ValueError("future parent evidence_class is invalid")
            _validate_future_completion_chain(future)
            observation = future.get("observation")
            if not isinstance(observation, Mapping):
                raise ValueError("future observation is missing")
            window = observation.get("observation_window")
            if not isinstance(window, Mapping) or set(window) != {"start_at", "end_at"}:
                raise ValueError("future observation window is missing")
            start_at = _utc(
                window.get("start_at"), "future observation_window.start_at"
            )
            end_at = _utc(window.get("end_at"), "future observation_window.end_at")
            collected_at = _utc(
                observation.get("collected_at"), "future observation collected_at"
            )
            if end_at <= start_at:
                raise ValueError("future observation window end must be after start")
            if observation.get("label") == "not_observed" and collected_at < end_at:
                raise ValueError(
                    "future not_observed label cannot predate window maturity"
                )
            task = observation.get("future_task_id")
            identity = future.get("label_identity")
            if (
                not isinstance(task, str)
                or not task
                or not isinstance(identity, str)
                or _SHA256.fullmatch(identity) is None
            ):
                raise ValueError("future task or label_identity is invalid")
            key = (case_id, task, identity)
            if key in labels or any(existing[2] == identity for existing in labels):
                raise ValueError(
                    "duplicate future label_identity across verified cohorts"
                )
            label = observation.get("label")
            scorable = _bool(observation.get("scorable"), "future observation.scorable")
            if label == "no_data":
                if scorable:
                    raise ValueError("future no_data cannot be scorable")
                observed = None
            elif label in {"occurred", "not_observed"} and scorable:
                observed = label == "occurred"
            elif (
                label in {"occurred", "not_observed"}
                and observation.get("high_risk") is True
            ):
                observed = None
            else:
                raise ValueError(
                    "future observation label/scorable state is inconsistent"
                )
            if completion.get("future_completion_status") == "CASE_COMPLETE_FOR_FUTURE":
                if not scorable:
                    raise ValueError(
                        "future completion status cannot count an unscorable label"
                    )
                cases.add(case_id)
                subjects.add(subject)
            elif completion.get("future_completion_status") != "PENDING":
                raise ValueError("future completion status is invalid")
            labels[key] = {
                "case_id": case_id,
                "subject_id_hash": subject,
                "task_id": task,
                "label_identity": identity,
                "scorable": scorable,
                "observed_positive": observed,
                "classification": label,
                "high_risk": observation.get("high_risk") is True,
                "review_status": observation.get("review_status"),
            }
            frozen_by_case[case_id] = frozen
    return labels, cases, subjects, frozen_by_case


def build_gate_evidence_from_cohorts(
    cohort_paths: Sequence[str | Path],
    *,
    scoring_artifact: str | Path,
    holdout_artifact: str | Path,
    audit_artifact: str | Path,
    admitted_root: Path,
) -> GateEvidence:
    """Derive gate evidence only from verified manifests and their recursive sealed lineage."""
    root = _trusted_root(admitted_root)
    if (
        not isinstance(cohort_paths, Sequence)
        or isinstance(cohort_paths, (str, bytes))
        or not cohort_paths
    ):
        raise ValueError("one or more cohort manifest paths are required")
    manifests: list[dict[str, Any]] = []
    manifest_refs: list[dict[str, str]] = []
    parent_times: list[str] = []
    for path in cohort_paths:
        manifest, reference = _load_gate_artifact(
            path, "cohort manifest", admitted_root=root
        )
        verification = verify_cohort_manifest(manifest, admitted_root=root)
        if verification["status"] != "VERIFIED":
            raise ValueError(
                "cohort manifest is not verified against its parent reconstruction"
            )
        manifests.append(manifest)
        manifest_refs.append(reference)
        parent_times.append(str(manifest["created_at"]))
    labels, cases, subjects, frozen_by_case = _label_rows_from_manifests(
        manifests, admitted_root=root
    )
    identity_refs = {
        (
            str(document["capability_identity_ref"]["artifact_path"]),
            str(document["capability_identity_ref"]["artifact_sha256"]),
        )
        for document in frozen_by_case.values()
        if isinstance(document.get("capability_identity_ref"), Mapping)
    }
    if identity_refs and len(identity_refs) != 1:
        raise ValueError("cohorts contain multiple capability identities")
    capability_identity = None
    identity_ref = None
    if identity_refs:
        identity_ref = ArtifactRef(*next(iter(identity_refs)))
        capability_identity = validate_capability_identity_ref(
            identity_ref,
            admitted_root=root,
        )
        expected_ref = {
            "artifact_path": identity_ref.artifact_path,
            "artifact_sha256": identity_ref.artifact_sha256,
        }
        if any(
            document.get("capability_identity_ref") != expected_ref
            for document in frozen_by_case.values()
        ):
            raise ValueError(
                "cohort frozen runs do not share one exact capability identity"
            )
    if len(cases) != len(subjects) or len(subjects) < 20:
        raise ValueError(
            "candidate evidence requires at least 20 unique completed cohort subjects"
        )

    score, score_ref = _load_gate_artifact(
        scoring_artifact, "scoring artifact", admitted_root=root
    )
    if (
        score.get("schema_version") != _GATE_SCORE_SCHEMA
        or score.get("evidence_class") != _GATE_EVIDENCE_CLASS
    ):
        raise ValueError("scoring artifact schema or evidence_class is invalid")
    expected_identity_ref = (
        None
        if identity_ref is None
        else {
            "artifact_path": identity_ref.artifact_path,
            "artifact_sha256": identity_ref.artifact_sha256,
        }
    )
    expected_source_ref = (
        None
        if capability_identity is None
        else capability_identity.governance_source_ref
    )
    _require_exact_parents(score, manifest_refs, "scoring artifact")
    _require_capability_identity(score, expected_identity_ref, "scoring artifact")
    _require_governance_source(score, expected_source_ref, "scoring artifact")
    score_rows = score.get("rows")
    if not isinstance(score_rows, list):
        raise ValueError("scoring rows are invalid")
    allowed_score_fields = {
        "case_id",
        "subject_id_hash",
        "task_id",
        "label_identity",
        "observed_positive",
        "scorable",
        "frozen_prediction",
        *(
            ()
            if expected_identity_ref is None
            else (
                "capability_identity_ref",
                "governance_source_ref",
            )
        ),
    }
    seen_rows: set[tuple[str, str, str]] = set()
    output_states: defaultdict[str, int] = defaultdict(int)
    task_counts: defaultdict[str, int] = defaultdict(int)
    positives: defaultdict[str, int] = defaultdict(int)
    negatives: defaultdict[str, int] = defaultdict(int)
    no_data: defaultdict[str, int] = defaultdict(int)
    calibration: defaultdict[str, list[float]] = defaultdict(list)
    for row in score_rows:
        if not isinstance(row, Mapping) or set(row) != allowed_score_fields:
            raise ValueError(
                "scoring row schema forbids self-attested prediction, calibration, or utility fields"
            )
        key = (
            str(row.get("case_id", "")),
            str(row.get("task_id", "")),
            str(row.get("label_identity", "")),
        )
        if key in seen_rows:
            raise ValueError("duplicate scoring label_identity row")
        seen_rows.add(key)
        source = labels.get(key)
        if source is None or row.get("subject_id_hash") != source["subject_id_hash"]:
            raise ValueError(
                "scoring row has no matching recursive cohort label lineage"
            )
        _require_capability_identity(row, expected_identity_ref, "scoring row")
        _require_governance_source(row, expected_source_ref, "scoring row")
        scorable = _bool(row.get("scorable"), "row.scorable")
        if (
            scorable != source["scorable"]
            or row.get("observed_positive") is not source["observed_positive"]
        ):
            raise ValueError(
                "scoring row label or scorable total is inconsistent with parent lineage"
            )
        task = key[1]
        prediction_ref = row.get("frozen_prediction")
        if not isinstance(prediction_ref, Mapping) or set(prediction_ref) != {
            "artifact_path",
            "artifact_sha256",
            "school_id",
            "prediction_id",
        }:
            raise ValueError("scoring row frozen prediction reference is invalid")
        frozen = frozen_by_case[key[0]]
        if _ref(frozen) != {
            name: prediction_ref[name] for name in ("artifact_path", "artifact_sha256")
        }:
            raise ValueError(
                "scoring row does not bind its completion frozen prediction parent"
            )
        run = FrozenBlindRun.from_dict(frozen["frozen_run"])
        outputs = [
            output
            for output in run.outputs
            if output.case_id == key[0]
            and output.task_id == task
            and output.school_id == prediction_ref["school_id"]
        ]
        if len(outputs) != 1:
            raise ValueError(
                "scoring row frozen output identity is missing or ambiguous"
            )
        output_states[outputs[0].state] += 1
        if not scorable:
            if source["classification"] == "no_data":
                no_data[task] += 1
            continue
        predictions = [
            prediction
            for prediction in outputs[0].predictions
            if prediction.prediction_id == prediction_ref["prediction_id"]
        ]
        if len(predictions) != 1:
            raise ValueError(
                "scoring row frozen prediction identity is missing or ambiguous"
            )
        probability = _finite_number(
            predictions[0].probability, "frozen prediction probability"
        )
        observed = bool(source["observed_positive"])
        task_counts[task] += 1
        positives[task] += int(observed)
        negatives[task] += int(not observed)
        calibration[task].append(abs(probability - float(observed)))
    expected_scorable = {key for key, row in labels.items() if row["scorable"]}
    if (
        seen_rows != set(labels)
        or {key for key in seen_rows if labels[key]["scorable"]} != expected_scorable
    ):
        raise ValueError(
            "scoring row totals are inconsistent with recursive cohort labels"
        )
    if any(
        task_counts[task] != positives[task] + negatives[task] for task in task_counts
    ):
        raise ValueError("task label totals are inconsistent")
    if not calibration:
        raise ValueError("scoring artifact has no valid scorable labels")

    holdout, holdout_ref = _load_gate_artifact(
        holdout_artifact, "holdout artifact", admitted_root=root
    )
    if (
        holdout.get("schema_version") != _GATE_HOLDOUT_SCHEMA
        or holdout.get("evidence_class") != _GATE_EVIDENCE_CLASS
    ):
        raise ValueError("holdout artifact schema or evidence_class is invalid")
    _require_exact_parents(holdout, [score_ref], "holdout artifact")
    _require_capability_identity(holdout, expected_identity_ref, "holdout artifact")
    _require_governance_source(holdout, expected_source_ref, "holdout artifact")
    competitive: defaultdict[str, int] = defaultdict(int)
    learned_values: list[float] = []
    static_values: list[float] = []
    selection_changes = 0
    holdout_rows = holdout.get("rows")
    allowed_holdout_fields = {
        "case_id",
        "subject_id_hash",
        "task_id",
        "eligible",
        "competitive",
        "training_subject_ids",
        "static_selection",
        "learned_selection",
        "static_utility",
        "learned_utility",
    }
    if not isinstance(holdout_rows, list):
        raise ValueError("holdout rows are invalid")
    holdout_identities: set[tuple[str, str]] = set()
    for row in holdout_rows:
        if not isinstance(row, Mapping) or set(row) != allowed_holdout_fields:
            raise ValueError("holdout row schema is invalid or not traceable")
        identity = (str(row.get("case_id", "")), str(row.get("task_id", "")))
        if identity in holdout_identities:
            raise ValueError("duplicate holdout case/task row")
        holdout_identities.add(identity)
        matching_labels = [
            value
            for key, value in labels.items()
            if key[0] == identity[0] and key[1] == identity[1]
        ]
        if (
            len(matching_labels) != 1
            or row.get("subject_id_hash") != matching_labels[0]["subject_id_hash"]
        ):
            raise ValueError("holdout row has no traceable cohort score lineage")
        training_subjects = row.get("training_subject_ids")
        if (
            not isinstance(training_subjects, list)
            or not training_subjects
            or len(training_subjects) != len(set(training_subjects))
        ):
            raise ValueError("holdout training subject schema is invalid")
        if any(
            not isinstance(value, str) or value not in subjects
            for value in training_subjects
        ):
            raise ValueError("holdout training subject is outside verified cohorts")
        if row["subject_id_hash"] in training_subjects:
            raise ValueError("holdout training/selection leakage detected")
        eligible = _bool(row.get("eligible"), "holdout.eligible")
        is_competitive = _bool(row.get("competitive"), "holdout.competitive")
        static = _finite_number(row.get("static_utility"), "holdout.static_utility")
        learned = _finite_number(row.get("learned_utility"), "holdout.learned_utility")
        if eligible and is_competitive:
            competitive[identity[1]] += 1
            static_values.append(static)
            learned_values.append(learned)
            selection_changes += int(
                row.get("static_selection") != row.get("learned_selection")
            )
    if not learned_values:
        raise ValueError("holdout artifact has no eligible competitive utility rows")

    audit, audit_ref = _load_gate_artifact(
        audit_artifact, "audit artifact", admitted_root=root
    )
    if (
        audit.get("schema_version") != _GATE_AUDIT_SCHEMA
        or audit.get("evidence_class") != _GATE_EVIDENCE_CLASS
    ):
        raise ValueError("audit artifact schema or evidence_class is invalid")
    component_parents = audit.get("parents")
    if not isinstance(component_parents, list) or len(component_parents) != 4:
        raise ValueError("audit artifact requires four component audit parents")
    components = [
        _load_sealed(
            ArtifactRef(**_ref(reference)), admitted_root=root
        )
        for reference in component_parents
    ]
    _require_capability_identity(
        audit, expected_identity_ref, "aggregate audit artifact"
    )
    _require_governance_source(audit, expected_source_ref, "aggregate audit artifact")
    statuses = {}
    for field in (
        "high_risk_review_status",
        "hash_audit_status",
        "witness_audit_status",
        "leakage_audit_status",
    ):
        value = audit.get(field)
        allowed = (
            {"PASS", "FAIL", "HOLD", "NOT_APPLICABLE"}
            if field == "high_risk_review_status"
            else {"PASS", "FAIL", "HOLD"}
        )
        if value not in allowed:
            raise ValueError(f"{field} is invalid")
        expected_schema = (
            f"prospective-{field.replace('_status', '').replace('_', '-')}/v1"
        )
        matches = [
            component
            for component in components
            if component.get("schema_version") == expected_schema
        ]
        if len(matches) != 1 or matches[0].get("status") != value:
            raise ValueError(f"{field} component audit is missing or inconsistent")
        _require_exact_parents(matches[0], [holdout_ref], f"{field} component audit")
        _require_capability_identity(
            matches[0], expected_identity_ref, f"{field} component audit"
        )
        _require_governance_source(
            matches[0], expected_source_ref, f"{field} component audit"
        )
        statuses[field] = value
    has_high_risk = any(value["high_risk"] for value in labels.values())
    if has_high_risk == (statuses["high_risk_review_status"] == "NOT_APPLICABLE"):
        raise ValueError(
            "high-risk audit status does not match presence of high-risk labels"
        )
    for document in (score, holdout, *components, audit):
        parent_times.append(str(document.get("created_at", "")))
        _utc(document.get("created_at"), "artifact created_at")
    all_parents = tuple(
        [
            *manifest_refs,
            score_ref,
            holdout_ref,
            *[_ref(item) for item in components],
            audit_ref,
        ]
    )
    return GateEvidence(
        evidence_class=_GATE_EVIDENCE_CLASS,
        unique_completed_subjects=len(subjects),
        task_label_counts=dict(sorted(task_counts.items())),
        positive_counts=dict(sorted(positives.items())),
        negative_counts=dict(sorted(negatives.items())),
        no_data_counts=dict(sorted(no_data.items())),
        calibration_error_by_task={
            task: round(sum(values) / len(values), 12)
            for task, values in sorted(calibration.items())
        },
        competitive_count_by_task=dict(sorted(competitive.items())),
        selection_change_count=selection_changes,
        learned_utility=sum(learned_values) / len(learned_values),
        static_utility=sum(static_values) / len(static_values),
        parents=all_parents,
        parent_created_at=tuple(parent_times),
        capability_identity_ref=(
            None
            if identity_ref is None
            else {
                "artifact_path": identity_ref.artifact_path,
                "artifact_sha256": identity_ref.artifact_sha256,
            }
        ),
        governance_source_ref=(
            None
            if capability_identity is None
            else capability_identity.governance_source_ref
        ),
        school_id=None
        if capability_identity is None
        else capability_identity.school_id,
        task_id=None if capability_identity is None else capability_identity.task_id,
        claim_kind=None
        if capability_identity is None
        else capability_identity.claim_kind,
        evidence_grade=None
        if capability_identity is None
        else capability_identity.evidence_grade,
        capability_version=(
            None
            if capability_identity is None
            else capability_identity.capability_version
        ),
        provenance_verified=True,
        claim_rows=output_states["claim"],
        abstain_rows=output_states["abstain"],
        unsupported_rows=output_states["unsupported"],
        **statuses,
    )


def build_future_gate_evidence_from_cohorts(
    cohort_paths: Sequence[str | Path],
    *,
    scoring_artifact: str | Path,
    holdout_artifact: str | Path,
    audit_artifact: str | Path,
    admitted_root: Path,
) -> GateEvidence:
    """Recompute future evidence from future labels, frozen predictions, and sealed audits."""
    root = _trusted_root(admitted_root)
    if not cohort_paths:
        raise ValueError("one or more future cohort manifests are required")
    manifests: list[dict[str, Any]] = []
    manifest_refs: list[dict[str, str]] = []
    parent_times: list[str] = []
    for path in cohort_paths:
        manifest, reference = _load_gate_artifact(
            path, "future cohort manifest", admitted_root=root
        )
        if verify_cohort_manifest(manifest, admitted_root=root)["status"] != "VERIFIED":
            raise ValueError("future cohort manifest is not verified")
        manifests.append(manifest)
        manifest_refs.append(reference)
        parent_times.append(str(manifest["created_at"]))
    labels, completed_cases, completed_subjects, frozen_by_case = (
        _future_label_rows_from_manifests(manifests, admitted_root=root)
    )
    identity_refs = {
        (
            str(document["capability_identity_ref"]["artifact_path"]),
            str(document["capability_identity_ref"]["artifact_sha256"]),
        )
        for document in frozen_by_case.values()
        if isinstance(document.get("capability_identity_ref"), Mapping)
    }
    if identity_refs and len(identity_refs) != 1:
        raise ValueError("future cohorts contain multiple capability identities")
    capability_identity = None
    identity_ref = None
    if identity_refs:
        identity_ref = ArtifactRef(*next(iter(identity_refs)))
        capability_identity = validate_capability_identity_ref(
            identity_ref,
            admitted_root=root,
        )
        expected_identity_ref = {
            "artifact_path": identity_ref.artifact_path,
            "artifact_sha256": identity_ref.artifact_sha256,
        }
        if any(
            document.get("capability_identity_ref") != expected_identity_ref
            for document in frozen_by_case.values()
        ):
            raise ValueError(
                "future cohort frozen runs do not share one exact capability identity"
            )
    else:
        expected_identity_ref = None

    score, score_ref = _load_gate_artifact(
        scoring_artifact, "future scoring artifact", admitted_root=root
    )
    if (
        score.get("schema_version") != _FUTURE_SCORE_SCHEMA
        or score.get("evidence_class") != _FUTURE_EVIDENCE_CLASS
    ):
        raise ValueError("future scoring artifact schema or evidence_class is invalid")
    expected_source_ref = (
        None
        if capability_identity is None
        else capability_identity.governance_source_ref
    )
    _require_exact_parents(score, manifest_refs, "future scoring artifact")
    _require_capability_identity(
        score, expected_identity_ref, "future scoring artifact"
    )
    _require_governance_source(score, expected_source_ref, "future scoring artifact")
    rows = score.get("rows")
    allowed_score_fields = {
        "case_id",
        "subject_id_hash",
        "task_id",
        "label_identity",
        "observed_positive",
        "scorable",
        "frozen_prediction",
        *(
            ()
            if expected_identity_ref is None
            else (
                "capability_identity_ref",
                "governance_source_ref",
            )
        ),
    }
    if not isinstance(rows, list):
        raise ValueError("future scoring rows are invalid")
    seen: set[tuple[str, str, str]] = set()
    output_states: defaultdict[str, int] = defaultdict(int)
    task_counts: defaultdict[str, int] = defaultdict(int)
    positives: defaultdict[str, int] = defaultdict(int)
    negatives: defaultdict[str, int] = defaultdict(int)
    no_data: defaultdict[str, int] = defaultdict(int)
    calibration: defaultdict[str, list[float]] = defaultdict(list)
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != allowed_score_fields:
            raise ValueError("future scoring row schema forbids self-attested metrics")
        key = (
            str(row.get("case_id", "")),
            str(row.get("task_id", "")),
            str(row.get("label_identity", "")),
        )
        if key in seen:
            raise ValueError("duplicate future scoring row")
        seen.add(key)
        source = labels.get(key)
        if source is None or row.get("subject_id_hash") != source["subject_id_hash"]:
            raise ValueError("future scoring row has no bound/reviewed label lineage")
        _require_capability_identity(row, expected_identity_ref, "future scoring row")
        _require_governance_source(row, expected_source_ref, "future scoring row")
        scorable = _bool(row.get("scorable"), "future row.scorable")
        if (
            scorable != source["scorable"]
            or row.get("observed_positive") is not source["observed_positive"]
        ):
            raise ValueError("future scoring row differs from actual future label")
        task = key[1]
        prediction_ref = row.get("frozen_prediction")
        if not isinstance(prediction_ref, Mapping) or set(prediction_ref) != {
            "artifact_path",
            "artifact_sha256",
            "school_id",
            "prediction_id",
        }:
            raise ValueError(
                "future scoring row frozen prediction reference is invalid"
            )
        frozen = frozen_by_case[key[0]]
        if _ref(frozen) != {
            name: prediction_ref[name] for name in ("artifact_path", "artifact_sha256")
        }:
            raise ValueError(
                "future scoring row does not bind its frozen prediction parent"
            )
        run = FrozenBlindRun.from_dict(frozen["frozen_run"])
        outputs = [
            output
            for output in run.outputs
            if output.case_id == key[0]
            and output.task_id == task
            and output.school_id == prediction_ref["school_id"]
        ]
        if len(outputs) != 1:
            raise ValueError("future frozen output identity is missing or ambiguous")
        output_states[outputs[0].state] += 1
        if not scorable:
            if source["classification"] == "no_data":
                no_data[task] += 1
            continue
        predictions = [
            prediction
            for prediction in outputs[0].predictions
            if prediction.prediction_id == prediction_ref["prediction_id"]
        ]
        if len(predictions) != 1:
            raise ValueError(
                "future frozen prediction identity is missing or ambiguous"
            )
        probability = _finite_number(
            predictions[0].probability, "future frozen prediction probability"
        )
        observed = bool(source["observed_positive"])
        task_counts[task] += 1
        positives[task] += int(observed)
        negatives[task] += int(not observed)
        calibration[task].append(abs(probability - float(observed)))
    if seen != set(labels):
        raise ValueError("future scoring rows must cover all bound/reviewed labels")
    if not calibration:
        raise ValueError("future scoring artifact has no scorable future labels")

    holdout, holdout_ref = _load_gate_artifact(
        holdout_artifact, "future holdout artifact", admitted_root=root
    )
    if (
        holdout.get("schema_version") != _FUTURE_HOLDOUT_SCHEMA
        or holdout.get("evidence_class") != _FUTURE_EVIDENCE_CLASS
    ):
        raise ValueError("future holdout artifact schema or evidence_class is invalid")
    _require_exact_parents(holdout, [score_ref], "future holdout artifact")
    _require_capability_identity(
        holdout, expected_identity_ref, "future holdout artifact"
    )
    _require_governance_source(holdout, expected_source_ref, "future holdout artifact")
    holdout_rows = holdout.get("rows")
    if not isinstance(holdout_rows, list):
        raise ValueError("future holdout rows are invalid")
    allowed_holdout_fields = {
        "case_id",
        "subject_id_hash",
        "task_id",
        "eligible",
        "competitive",
        "training_subject_ids",
        "static_selection",
        "learned_selection",
        "static_utility",
        "learned_utility",
    }
    all_subjects = {value["subject_id_hash"] for value in labels.values()}
    competitive: defaultdict[str, int] = defaultdict(int)
    learned_values: list[float] = []
    static_values: list[float] = []
    selection_changes = 0
    holdout_ids: set[tuple[str, str]] = set()
    for row in holdout_rows:
        if not isinstance(row, Mapping) or set(row) != allowed_holdout_fields:
            raise ValueError("future holdout row schema is invalid")
        identity = (str(row.get("case_id", "")), str(row.get("task_id", "")))
        if identity in holdout_ids:
            raise ValueError("duplicate future holdout case/task row")
        holdout_ids.add(identity)
        matches = [value for key, value in labels.items() if key[:2] == identity]
        if (
            len(matches) != 1
            or row.get("subject_id_hash") != matches[0]["subject_id_hash"]
        ):
            raise ValueError("future holdout row has no future label lineage")
        training = row.get("training_subject_ids")
        if (
            not isinstance(training, list)
            or not training
            or len(training) != len(set(training))
        ):
            raise ValueError("future holdout training subjects are invalid")
        if (
            any(subject not in all_subjects for subject in training)
            or row["subject_id_hash"] in training
        ):
            raise ValueError("future holdout training/selection leakage detected")
        eligible = _bool(row.get("eligible"), "future holdout.eligible")
        is_competitive = _bool(row.get("competitive"), "future holdout.competitive")
        static = _finite_number(
            row.get("static_utility"), "future holdout.static_utility"
        )
        learned = _finite_number(
            row.get("learned_utility"), "future holdout.learned_utility"
        )
        if eligible and is_competitive:
            competitive[identity[1]] += 1
            static_values.append(static)
            learned_values.append(learned)
            selection_changes += int(
                row.get("static_selection") != row.get("learned_selection")
            )

    audit, audit_ref = _load_gate_artifact(
        audit_artifact, "future audit artifact", admitted_root=root
    )
    if (
        audit.get("schema_version") != _FUTURE_AUDIT_SCHEMA
        or audit.get("evidence_class") != _FUTURE_EVIDENCE_CLASS
    ):
        raise ValueError("future audit artifact schema or evidence_class is invalid")
    component_refs = audit.get("parents")
    if not isinstance(component_refs, list) or len(component_refs) != 4:
        raise ValueError("future audit requires four component parents")
    components = [
        _load_sealed(ArtifactRef(**_ref(reference)), admitted_root=root)
        for reference in component_refs
    ]
    _require_capability_identity(
        audit, expected_identity_ref, "future aggregate audit artifact"
    )
    _require_governance_source(
        audit, expected_source_ref, "future aggregate audit artifact"
    )
    statuses: dict[str, str] = {}
    for field in (
        "high_risk_review_status",
        "hash_audit_status",
        "witness_audit_status",
        "leakage_audit_status",
    ):
        value = audit.get(field)
        allowed = (
            {"PASS_FUTURE", "FAIL", "HOLD", "NOT_APPLICABLE"}
            if field == "high_risk_review_status"
            else {"PASS", "FAIL", "HOLD"}
        )
        if value not in allowed:
            raise ValueError(f"future {field} is invalid")
        schema = f"prospective-{field.replace('_status', '').replace('_', '-')}/v1"
        matches = [
            component
            for component in components
            if component.get("schema_version") == schema
        ]
        if len(matches) != 1 or matches[0].get("status") != value:
            raise ValueError(f"future {field} component is inconsistent")
        _require_exact_parents(matches[0], [holdout_ref], f"future {field} component")
        _require_capability_identity(
            matches[0], expected_identity_ref, f"future {field} component"
        )
        _require_governance_source(
            matches[0], expected_source_ref, f"future {field} component"
        )
        if (
            field == "high_risk_review_status"
            and value == "PASS_FUTURE"
            and matches[0].get("evidence_class") != _FUTURE_EVIDENCE_CLASS
        ):
            raise ValueError(
                "future high-risk review must be independent future review"
            )
        statuses[field] = str(value)
    has_high_risk = any(value["high_risk"] for value in labels.values())
    if has_high_risk and statuses["high_risk_review_status"] != "PASS_FUTURE":
        pass
    elif not has_high_risk and statuses["high_risk_review_status"] != "NOT_APPLICABLE":
        raise ValueError("future no-high-risk audit must use NOT_APPLICABLE")
    for document in (score, holdout, *components, audit):
        parent_times.append(str(document.get("created_at", "")))
        _utc(document.get("created_at"), "future artifact created_at")
    parents = tuple(
        [
            *manifest_refs,
            score_ref,
            holdout_ref,
            *[_ref(item) for item in components],
            audit_ref,
        ]
    )
    return GateEvidence(
        evidence_class=_FUTURE_EVIDENCE_CLASS,
        unique_completed_subjects=len(completed_subjects),
        task_label_counts=dict(sorted(task_counts.items())),
        positive_counts=dict(sorted(positives.items())),
        negative_counts=dict(sorted(negatives.items())),
        no_data_counts=dict(sorted(no_data.items())),
        calibration_error_by_task={
            task: round(sum(values) / len(values), 12)
            for task, values in sorted(calibration.items())
        },
        competitive_count_by_task=dict(sorted(competitive.items())),
        selection_change_count=selection_changes,
        learned_utility=sum(learned_values) / len(learned_values)
        if learned_values
        else 0.0,
        static_utility=sum(static_values) / len(static_values)
        if static_values
        else 0.0,
        parents=parents,
        parent_created_at=tuple(parent_times),
        capability_identity_ref=expected_identity_ref,
        governance_source_ref=(
            None
            if capability_identity is None
            else capability_identity.governance_source_ref
        ),
        school_id=None
        if capability_identity is None
        else capability_identity.school_id,
        task_id=None if capability_identity is None else capability_identity.task_id,
        claim_kind=None
        if capability_identity is None
        else capability_identity.claim_kind,
        evidence_grade=None
        if capability_identity is None
        else capability_identity.evidence_grade,
        capability_version=None
        if capability_identity is None
        else capability_identity.capability_version,
        provenance_verified=True,
        claim_rows=output_states["claim"],
        abstain_rows=output_states["abstain"],
        unsupported_rows=output_states["unsupported"],
        **statuses,
    )


def _validate_future_gate_evidence(
    evidence: GateEvidence, *, admitted_root: Path
) -> None:
    if (
        not isinstance(evidence, GateEvidence)
        or evidence.provenance_verified is not True
        or not evidence.parents
    ):
        raise ValueError("future gate evidence must come from verified cohort lineage")
    cohort_paths: list[str] = []
    scoring_path = holdout_path = audit_path = None
    for reference in evidence.parents:
        document = validate_parent_ref(
            ArtifactRef(**reference), admitted_root=admitted_root
        )
        schema = document.get("schema_version")
        if schema == _MANIFEST_SCHEMA:
            cohort_paths.append(reference["artifact_path"])
        elif schema == _FUTURE_SCORE_SCHEMA:
            scoring_path = reference["artifact_path"]
        elif schema == _FUTURE_HOLDOUT_SCHEMA:
            holdout_path = reference["artifact_path"]
        elif schema == _FUTURE_AUDIT_SCHEMA:
            audit_path = reference["artifact_path"]
        elif schema in {
            "prospective-high-risk-review/v1",
            "prospective-hash-audit/v1",
            "prospective-witness-audit/v1",
            "prospective-leakage-audit/v1",
        }:
            continue
        else:
            raise ValueError(
                "future gate evidence contains an unexpected parent schema"
            )
    if (
        not cohort_paths
        or scoring_path is None
        or holdout_path is None
        or audit_path is None
    ):
        raise ValueError("future gate evidence parent set is incomplete")
    rebuilt = build_future_gate_evidence_from_cohorts(
        cohort_paths,
        scoring_artifact=scoring_path,
        holdout_artifact=holdout_path,
        audit_artifact=audit_path,
        admitted_root=admitted_root,
    )
    if rebuilt != evidence:
        raise ValueError(
            "future gate evidence differs from authenticated reconstruction"
        )
    if evidence.evidence_class != _FUTURE_EVIDENCE_CLASS:
        raise ValueError("future gate evidence_class must be future_observation")


def _validate_gate_evidence(evidence: GateEvidence, *, admitted_root: Path) -> None:
    if (
        not isinstance(evidence, GateEvidence)
        or evidence.provenance_verified is not True
        or not evidence.parents
    ):
        raise ValueError("gate evidence must come from verified cohort lineage")
    cohort_paths: list[str] = []
    scoring_path: str | None = None
    holdout_path: str | None = None
    audit_path: str | None = None
    for reference in evidence.parents:
        document = validate_parent_ref(
            ArtifactRef(**reference), admitted_root=admitted_root
        )
        schema = document.get("schema_version")
        if schema == _MANIFEST_SCHEMA:
            cohort_paths.append(reference["artifact_path"])
        elif schema == _GATE_SCORE_SCHEMA:
            scoring_path = reference["artifact_path"]
        elif schema == _GATE_HOLDOUT_SCHEMA:
            holdout_path = reference["artifact_path"]
        elif schema == _GATE_AUDIT_SCHEMA:
            audit_path = reference["artifact_path"]
        elif schema in {
            "prospective-high-risk-review/v1",
            "prospective-hash-audit/v1",
            "prospective-witness-audit/v1",
            "prospective-leakage-audit/v1",
        }:
            continue
        else:
            raise ValueError("gate evidence contains an unexpected parent schema")
    if (
        not cohort_paths
        or scoring_path is None
        or holdout_path is None
        or audit_path is None
    ):
        raise ValueError("gate evidence parent set is incomplete")
    rebuilt = build_gate_evidence_from_cohorts(
        cohort_paths,
        scoring_artifact=scoring_path,
        holdout_artifact=holdout_path,
        audit_artifact=audit_path,
        admitted_root=admitted_root,
    )
    if rebuilt != evidence:
        raise ValueError(
            "gate evidence differs from authenticated cohort reconstruction"
        )
    if evidence.evidence_class != _GATE_EVIDENCE_CLASS:
        raise ValueError(
            "gate evidence_class must be prediction-first immediate retrospective"
        )
    integer_values = [
        evidence.unique_completed_subjects,
        evidence.selection_change_count,
    ]
    integer_values.extend(evidence.task_label_counts.values())
    integer_values.extend(evidence.positive_counts.values())
    integer_values.extend(evidence.negative_counts.values())
    integer_values.extend(evidence.no_data_counts.values())
    integer_values.extend(evidence.competitive_count_by_task.values())
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in integer_values
    ):
        raise ValueError(
            "gate counts must be non-negative integers and bool is forbidden"
        )
    for task, count in evidence.task_label_counts.items():
        if count != evidence.positive_counts.get(
            task, 0
        ) + evidence.negative_counts.get(task, 0):
            raise ValueError("gate task totals are inconsistent")
    numeric = [evidence.learned_utility, evidence.static_utility]
    numeric.extend(
        value
        for value in evidence.calibration_error_by_task.values()
        if value is not None
    )
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        for value in numeric
    ):
        raise ValueError("gate metrics must be finite numbers")
    if any(
        value is not None and not 0.0 <= float(value) <= 1.0
        for value in evidence.calibration_error_by_task.values()
    ):
        raise ValueError("calibration errors must be within [0, 1]")
    if not evidence.parent_created_at or len(evidence.parents) != len(
        evidence.parent_created_at
    ):
        raise ValueError("gate parent timestamps are inconsistent")
    for timestamp in evidence.parent_created_at:
        _utc(timestamp, "parent created_at")


def evaluate_prediction_capability_candidate(
    evidence: GateEvidence,
    *,
    evaluated_at: str,
    admitted_root: Path,
) -> dict[str, Any]:
    """Evaluate the Task-10 proposal gate; GO never changes production behavior."""
    _validate_gate_evidence(evidence, admitted_root=_trusted_root(admitted_root))
    evaluated = _utc(evaluated_at, "evaluated_at")
    if any(
        evaluated < _utc(value, "parent created_at")
        for value in evidence.parent_created_at
    ):
        raise ValueError("evaluated_at cannot predate any gate parent")
    eligible_tasks = {
        task
        for task, count in evidence.task_label_counts.items()
        if count >= 15
        and evidence.positive_counts.get(task, 0) > 0
        and evidence.negative_counts.get(task, 0) > 0
    }
    checks = {
        "evidence_class_is_immediate": evidence.evidence_class == _GATE_EVIDENCE_CLASS,
        "completed_subjects_at_least_20": evidence.unique_completed_subjects >= 20,
        "one_task_has_15_positive_and_negative": bool(eligible_tasks),
        "same_eligible_task_calibration_below_0_2": any(
            evidence.calibration_error_by_task.get(task) is not None
            and float(evidence.calibration_error_by_task[task]) < 0.2
            for task in eligible_tasks
        ),
        "high_risk_reviews_pass": evidence.high_risk_review_status
        in {"PASS", "NOT_APPLICABLE"},
        "one_competitive_task_at_least_5": max(
            evidence.competitive_count_by_task.values(),
            default=0,
        )
        >= 5,
        "selection_changed": evidence.selection_change_count >= 1,
        "utility_not_degraded": evidence.learned_utility >= evidence.static_utility,
        "hash_audit_pass": evidence.hash_audit_status == "PASS",
        "witness_audit_pass": evidence.witness_audit_status == "PASS",
        "leakage_audit_pass": evidence.leakage_audit_status == "PASS",
    }
    unmet = [name for name, passed in checks.items() if not passed]
    status = "GO" if not unmet else "HOLD"
    payload: dict[str, Any] = {
        "schema_version": _GATE_RESULT_SCHEMA,
        "gate_id": "prediction_capability_candidate_gate_v1",
        "evaluated_at": evaluated_at,
        "evidence_class": evidence.evidence_class,
        "status": status,
        "proposal_allowed": status == "GO",
        "production_switch": False,
        "parents": [dict(item) for item in evidence.parents],
        "checks": checks,
        "unmet_conditions": unmet,
        "evidence_summary": {
            "unique_completed_subjects": evidence.unique_completed_subjects,
            "task_label_counts": dict(evidence.task_label_counts),
            "positive_counts": dict(evidence.positive_counts),
            "negative_counts": dict(evidence.negative_counts),
            "no_data_counts": dict(evidence.no_data_counts),
            "calibration_error_by_task": dict(evidence.calibration_error_by_task),
            "competitive_count_by_task": dict(evidence.competitive_count_by_task),
            "selection_change_count": evidence.selection_change_count,
            "learned_utility": evidence.learned_utility,
            "static_utility": evidence.static_utility,
            "high_risk_review_status": evidence.high_risk_review_status,
            "hash_audit_status": evidence.hash_audit_status,
            "witness_audit_status": evidence.witness_audit_status,
            "leakage_audit_status": evidence.leakage_audit_status,
        },
    }
    return {**payload, "artifact_sha256": canonical_artifact_sha256(payload)}


def evaluate_future_empirical(
    evidence: GateEvidence,
    *,
    evaluated_at: str,
    admitted_root: Path,
) -> dict[str, Any]:
    """Evaluate only future observations; GO remains an offline result."""
    _validate_future_gate_evidence(
        evidence, admitted_root=_trusted_root(admitted_root)
    )
    evaluated = _utc(evaluated_at, "evaluated_at")
    if any(
        evaluated < _utc(value, "parent created_at")
        for value in evidence.parent_created_at
    ):
        raise ValueError("evaluated_at cannot predate any future gate parent")
    eligible_tasks = {
        task
        for task, count in evidence.task_label_counts.items()
        if count >= 8
        and evidence.positive_counts.get(task, 0) > 0
        and evidence.negative_counts.get(task, 0) > 0
    }
    checks = {
        "evidence_class_is_future_observation": evidence.evidence_class
        == _FUTURE_EVIDENCE_CLASS,
        "completed_subjects_at_least_10": evidence.unique_completed_subjects >= 10,
        "one_future_task_has_8_positive_and_negative": bool(eligible_tasks),
        "same_future_task_calibration_below_0_2": any(
            evidence.calibration_error_by_task.get(task) is not None
            and float(evidence.calibration_error_by_task[task]) < 0.2
            for task in eligible_tasks
        ),
        "fresh_high_risk_reviews_pass": evidence.high_risk_review_status
        in {
            "PASS_FUTURE",
            "NOT_APPLICABLE",
        },
        "one_competitive_task_at_least_5": max(
            evidence.competitive_count_by_task.values(),
            default=0,
        )
        >= 5,
        "selection_changed": evidence.selection_change_count >= 1,
        "utility_not_degraded": evidence.learned_utility >= evidence.static_utility,
        "hash_audit_pass": evidence.hash_audit_status == "PASS",
        "witness_audit_pass": evidence.witness_audit_status == "PASS",
        "leakage_audit_pass": evidence.leakage_audit_status == "PASS",
    }
    unmet = [name for name, passed in checks.items() if not passed]
    status = "GO" if not unmet else "HOLD"
    payload: dict[str, Any] = {
        "schema_version": _FUTURE_RESULT_SCHEMA,
        "gate_id": "future_empirical_gate_v1",
        "evaluated_at": evaluated_at,
        "evidence_class": evidence.evidence_class,
        "status": status,
        "proposal_allowed": status == "GO",
        "production_switch": False,
        "parents": [dict(item) for item in evidence.parents],
        "checks": checks,
        "unmet_conditions": unmet,
        "evidence_summary": {
            "unique_completed_subjects": evidence.unique_completed_subjects,
            "task_label_counts": dict(evidence.task_label_counts),
            "positive_counts": dict(evidence.positive_counts),
            "negative_counts": dict(evidence.negative_counts),
            "no_data_counts": dict(evidence.no_data_counts),
            "calibration_error_by_task": dict(evidence.calibration_error_by_task),
            "competitive_count_by_task": dict(evidence.competitive_count_by_task),
            "selection_change_count": evidence.selection_change_count,
            "learned_utility": evidence.learned_utility,
            "static_utility": evidence.static_utility,
            "high_risk_review_status": evidence.high_risk_review_status,
            "hash_audit_status": evidence.hash_audit_status,
            "witness_audit_status": evidence.witness_audit_status,
            "leakage_audit_status": evidence.leakage_audit_status,
        },
    }
    return {**payload, "artifact_sha256": canonical_artifact_sha256(payload)}


def build_three_gate_report(
    immediate_result: Mapping[str, Any],
    future_result: Mapping[str, Any],
    historical_ref: ArtifactRef,
    *,
    admitted_root: Path,
) -> str:
    """Render three isolated sections; historical status/hash are read from actual JSON bytes."""
    if immediate_result.get("gate_id") != "prediction_capability_candidate_gate_v1":
        raise ValueError("immediate gate result is invalid")
    if future_result.get("gate_id") != "future_empirical_gate_v1":
        raise ValueError("future gate result is invalid")
    root = _trusted_root(admitted_root)
    historical = _raw_historical(historical_ref, admitted_root=root)
    path = Path(historical["artifact_path"])
    if path != root / "META" / "six-month-platform-gate-2026-07-15.json":
        raise ValueError(
            "three-gate report historical reference must bind the canonical META JSON baseline path"
        )
    try:
        actual = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("historical baseline JSON is invalid") from error
    if (
        not isinstance(actual, Mapping)
        or actual.get("schema_version") != _HISTORICAL_SCHEMA
    ):
        raise ValueError("historical baseline actual schema is invalid")
    status = actual.get("status")
    if status not in {"GO", "HOLD"}:
        raise ValueError("historical baseline actual status is invalid")
    md_path = root / "META" / "six-month-platform-gate-2026-07-15.md"
    md_ref = _raw_historical(
        ArtifactRef(
            md_path.as_posix(),
            hashlib.sha256(md_path.read_bytes()).hexdigest(),
        ),
        admitted_root=root,
    )

    def scoped_status(result: Mapping[str, Any]) -> str:
        value = result.get("status")
        return (
            "离线候选门禁结果：GO（不代表平台 GO 或生产 GO）"
            if value == "GO"
            else f"离线候选门禁结果：{value}"
        )

    return "\n".join(
        (
            "## prediction capability candidate",
            f"预测能力候选 {immediate_result.get('status')}",
            scoped_status(immediate_result),
            "production_switch: false",
            "",
            "## future empirical",
            f"未来实证 {future_result.get('status')}",
            scoped_status(future_result),
            "production_switch: false",
            "",
            "## historical baseline（只读引用）",
            f"historical baseline（只读引用） {status}",
            f"actual_json_sha256: {historical['artifact_sha256']}",
            f"actual_md_sha256: {md_ref['artifact_sha256']}",
            "production_switch: false",
            "",
        )
    )


def cohort_output_dir(root: Path, manifest: Mapping[str, Any]) -> Path:
    return (
        Path(root)
        / f"{manifest['cohort_id']}--{str(manifest['member_set_sha256'])[:12]}"
    )
