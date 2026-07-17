"""Independent human review gate for prospective high-risk observations."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Mapping


HIGH_RISK_TASK_IDS = {
    "wealth.debt",
    "marriage.divorce_or_remarriage",
    "health.system_risk",
}
_REVIEW_SCHEMA = "school-capability-high-risk-review/v2"
_LEGACY_REVIEW_SCHEMA = "school-capability-high-risk-review/v1"
_ADJUDICATION_SCHEMA = "school-capability-high-risk-adjudication/v2"
_LEGACY_ADJUDICATION_SCHEMA = "school-capability-high-risk-adjudication/v1"
_PACKET_SCHEMA = "school-capability-high-risk-review-packet/v2"
_LEGACY_EVIDENCE_CLASS = "legacy_non_prospective"
_EVIDENCE_CLASSES = {
    "prediction_first_immediate_retrospective",
    "future_observation",
    _LEGACY_EVIDENCE_CLASS,
}
_LINEAGE_FIELDS = {
    "observation_sha256", "evidence_class", "label_identity", "review_packet_sha256",
}
_REVIEW_FIELDS = {
    "schema_version", "case_id", "task_id", *_LINEAGE_FIELDS,
    "reviewer", "decision", "source_refs", "rationale", "signed_at",
}
_LEGACY_REVIEW_FIELDS = _REVIEW_FIELDS - {
    "evidence_class", "label_identity", "review_packet_sha256",
}
_ADJUDICATION_FIELDS = {
    "schema_version", "case_id", "task_id", *_LINEAGE_FIELDS,
    "adjudicator", "decision", "source_refs", "rationale", "signed_at",
}
_LEGACY_ADJUDICATION_FIELDS = _ADJUDICATION_FIELDS - {
    "evidence_class", "label_identity", "review_packet_sha256",
}
_FORBIDDEN_MARKERS = {
    "probability", "prediction", "runner output", "runner_output",
    "school output", "school_output", "report", "claim", "other review",
    "other_review",
}
_ALLOWED_DECISIONS: dict[str, set[str]] = {
    "wealth.debt": {"occurred", "not_observed"},
    "marriage.divorce_or_remarriage": {"occurred", "not_observed"},
    "health.system_risk": {"low", "moderate", "high"},
}


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _human(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value.lower().startswith(("automated", "agent", "ai-"))
    ):
        raise ValueError(f"{field} must identify a named independent human")
    return value


def _timestamp(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"{field} must be an ISO 8601 UTC timestamp")
    try:
        datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO 8601 UTC timestamp") from exc
    return value


def _task(task_id: object) -> str:
    if task_id not in HIGH_RISK_TASK_IDS:
        raise ValueError(f"task is not a supported high-risk task: {task_id}")
    return str(task_id)


def _decision(task_id: str, value: object) -> object:
    if value not in _ALLOWED_DECISIONS[task_id]:
        raise ValueError(f"decision does not match high-risk task schema: {task_id}")
    return value


def _source_refs(value: object) -> list[str]:
    if (
        not isinstance(value, (list, tuple))
        or not value
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise ValueError("source_refs must contain at least one non-empty reference")
    return list(value)


def _assert_no_leakage(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).lower().replace("-", " ")
            if any(marker in normalized for marker in _FORBIDDEN_MARKERS):
                raise ValueError(f"review leakage detected in field: {key}")
            _assert_no_leakage(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_leakage(item)


def _digest(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _evidence_class(value: object) -> str:
    if value not in _EVIDENCE_CLASSES:
        raise ValueError("evidence_class is invalid")
    return str(value)


def _adapt_legacy_review(review: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(review)
    if value.get("schema_version") != _LEGACY_REVIEW_SCHEMA or set(value) != _LEGACY_REVIEW_FIELDS:
        return value
    identity = canonical_sha256({
        "case_id": value.get("case_id"), "task_id": value.get("task_id"),
        "observation_sha256": value.get("observation_sha256"), "legacy": True,
    })
    return {
        **value, "schema_version": _REVIEW_SCHEMA,
        "evidence_class": _LEGACY_EVIDENCE_CLASS, "label_identity": identity,
        "review_packet_sha256": canonical_sha256({"label_identity": identity, "reviewer": value.get("reviewer")}),
    }


def validate_review(
    review: Mapping[str, Any], *, disallowed_reviewers: set[str] | None = None
) -> dict[str, Any]:
    """Validate one independent review without reading predictions or reports."""
    if not isinstance(review, Mapping):
        raise ValueError("review must be an object")
    _assert_no_leakage(review)
    value = _adapt_legacy_review(review)
    if set(value) != _REVIEW_FIELDS or value.get("schema_version") != _REVIEW_SCHEMA:
        raise ValueError("review schema is invalid")
    task_id = _task(value.get("task_id"))
    reviewer = _human(value.get("reviewer"), "reviewer")
    if reviewer in (disallowed_reviewers or set()):
        raise ValueError("reviewer violates required role separation")
    if not isinstance(value.get("case_id"), str) or not value["case_id"].strip():
        raise ValueError("case_id is required")
    _digest(value.get("observation_sha256"), "observation_sha256")
    _evidence_class(value.get("evidence_class"))
    _digest(value.get("label_identity"), "label_identity")
    _digest(value.get("review_packet_sha256"), "review_packet_sha256")
    _decision(task_id, value.get("decision"))
    _source_refs(value.get("source_refs"))
    if not isinstance(value.get("rationale"), str) or not value["rationale"].strip():
        raise ValueError("rationale is required")
    _timestamp(value.get("signed_at"), "signed_at")
    return value


def validate_adjudication(adjudication: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(adjudication, Mapping):
        raise ValueError("adjudication must be an object")
    _assert_no_leakage(adjudication)
    value = dict(adjudication)
    if value.get("schema_version") == _LEGACY_ADJUDICATION_SCHEMA and set(value) == _LEGACY_ADJUDICATION_FIELDS:
        identity = canonical_sha256({
            "case_id": value.get("case_id"), "task_id": value.get("task_id"),
            "observation_sha256": value.get("observation_sha256"), "legacy": True,
        })
        value.update({
            "schema_version": _ADJUDICATION_SCHEMA, "evidence_class": _LEGACY_EVIDENCE_CLASS,
            "label_identity": identity, "review_packet_sha256": [],
        })
    if set(value) != _ADJUDICATION_FIELDS or value.get("schema_version") != _ADJUDICATION_SCHEMA:
        raise ValueError("adjudication schema is invalid")
    task_id = _task(value.get("task_id"))
    _human(value.get("adjudicator"), "adjudicator")
    if not isinstance(value.get("case_id"), str) or not value["case_id"].strip():
        raise ValueError("case_id is required")
    _digest(value.get("observation_sha256"), "observation_sha256")
    _evidence_class(value.get("evidence_class"))
    _digest(value.get("label_identity"), "label_identity")
    packets = value.get("review_packet_sha256")
    if not isinstance(packets, list) or len(packets) not in {0, 2}:
        raise ValueError("review_packet_sha256 must bind both review packets")
    for digest in packets:
        _digest(digest, "review_packet_sha256")
    _decision(task_id, value.get("decision"))
    _source_refs(value.get("source_refs"))
    if not isinstance(value.get("rationale"), str) or not value["rationale"].strip():
        raise ValueError("rationale is required")
    _timestamp(value.get("signed_at"), "signed_at")
    return value


def validate_observation(observation: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a freeze-after observation packet and scan it for prediction leakage."""
    if not isinstance(observation, Mapping):
        raise ValueError("observation must be an object")
    _assert_no_leakage(observation)
    required = {
        "schema_version",
        "case_id",
        "task_id",
        "label",
        "observed_at",
        "observation_window",
        "source_refs",
        "quantifiable",
        "conflict_state",
        "custodian",
    }
    if set(observation) != required or observation.get("schema_version") != "prospective-observation/v1":
        raise ValueError("observation schema is invalid")
    task_id = _task(observation.get("task_id"))
    _decision(task_id, observation.get("label"))
    _human(observation.get("custodian"), "custodian")
    _timestamp(observation.get("observed_at"), "observed_at")
    window = observation.get("observation_window")
    if not isinstance(window, Mapping) or set(window) != {"started_at", "ended_at"}:
        raise ValueError("observation_window is invalid")
    _timestamp(window.get("started_at"), "observation_window.started_at")
    _timestamp(window.get("ended_at"), "observation_window.ended_at")
    _source_refs(observation.get("source_refs"))
    if type(observation.get("quantifiable")) is not bool:
        raise ValueError("quantifiable must be boolean")
    return dict(observation)


def prepare_review_packets(
    observation: Mapping[str, Any],
    *,
    evidence_class: str = _LEGACY_EVIDENCE_CLASS,
    label_identity: str | None = None,
    reviewer_a: str,
    reviewer_b: str,
    disallowed_reviewers: set[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Create two reviewer-specific fact-only packets bound to one evidence ledger."""
    clean = validate_observation(observation)
    evidence = _evidence_class(evidence_class)
    if evidence != _LEGACY_EVIDENCE_CLASS and disallowed_reviewers is None:
        raise ValueError("prospective review requires explicit disallowed operational roles")
    if evidence != _LEGACY_EVIDENCE_CLASS and label_identity is None:
        raise ValueError("prospective review requires an explicit label_identity")
    identity = label_identity or canonical_sha256({
        "case_id": clean["case_id"], "task_id": clean["task_id"],
        "observation_sha256": canonical_sha256(clean), "legacy": True,
    })
    _digest(identity, "label_identity")
    first = _human(reviewer_a, "reviewer_a")
    second = _human(reviewer_b, "reviewer_b")
    if first == second:
        raise ValueError("review gate requires different independent reviewers")
    blocked = disallowed_reviewers or set()
    if first in blocked or second in blocked:
        raise ValueError("reviewer violates required role separation")
    digest = canonical_sha256(clean)
    fact_packet = {
        "facts": {"label": clean["label"], "quantifiable": clean["quantifiable"],
                  "conflict_state": clean["conflict_state"]},
        "sources": clean["source_refs"],
        "time": {"observed_at": clean["observed_at"], "observation_window": clean["observation_window"]},
        "task_definition": {"task_id": clean["task_id"]},
    }

    def packet(reviewer: str) -> dict[str, Any]:
        payload = {
            "schema_version": _PACKET_SCHEMA, "case_id": clean["case_id"],
            "task_id": clean["task_id"], "observation_sha256": digest,
            "evidence_class": evidence, "label_identity": identity,
            "reviewer": reviewer, "packet": fact_packet,
        }
        return {**payload, "review_packet_sha256": canonical_sha256(payload)}

    return {"reviewer_a": packet(first), "reviewer_b": packet(second)}


def review_from_packet(packet: Mapping[str, Any], decision: Mapping[str, Any]) -> dict[str, Any]:
    """Bind a human decision to one immutable reviewer-specific packet."""
    packet_fields = {
        "schema_version", "case_id", "task_id", "observation_sha256", "evidence_class",
        "label_identity", "review_packet_sha256", "reviewer", "packet",
    }
    if not isinstance(packet, Mapping) or set(packet) != packet_fields or packet.get("schema_version") != _PACKET_SCHEMA:
        raise ValueError("review packet schema is invalid")
    payload = {key: value for key, value in packet.items() if key != "review_packet_sha256"}
    if canonical_sha256(payload) != packet["review_packet_sha256"]:
        raise ValueError("review packet hash mismatch")
    _assert_no_leakage(packet["packet"])
    if set(packet["packet"]) != {"facts", "sources", "time", "task_definition"}:
        raise ValueError("review packet must contain facts, sources, time, and task definition only")
    if not isinstance(decision, Mapping) or set(decision) != {"decision", "source_refs", "rationale", "signed_at"}:
        raise ValueError("review decision schema is invalid")
    review = {
        "schema_version": _REVIEW_SCHEMA, "case_id": packet["case_id"],
        "task_id": packet["task_id"], "observation_sha256": packet["observation_sha256"],
        "evidence_class": packet["evidence_class"], "label_identity": packet["label_identity"],
        "review_packet_sha256": packet["review_packet_sha256"], "reviewer": packet["reviewer"],
        **dict(decision),
    }
    return validate_review(review)


def finalize_reviews(
    case_id: str,
    task_id: str,
    review_a: Mapping[str, Any],
    review_b: Mapping[str, Any],
    adjudication: Mapping[str, Any] | None = None,
    *,
    evidence_class: str | None = None,
    label_identity: str | None = None,
    disallowed_adjudicators: set[str] | None = None,
    disallowed_reviewers: set[str] | None = None,
) -> dict[str, Any]:
    """Produce an A-grade standard label only after valid dual review or adjudication."""
    task_id = _task(task_id)
    requested_class = evidence_class or review_a.get("evidence_class")
    first = validate_review(review_a, disallowed_reviewers=disallowed_reviewers)
    second = validate_review(review_b, disallowed_reviewers=disallowed_reviewers)
    expected_class = _evidence_class(evidence_class or first["evidence_class"])
    expected_identity = label_identity or first["label_identity"]
    _digest(expected_identity, "label_identity")
    for review in (first, second):
        if review["case_id"] != case_id or review["task_id"] != task_id:
            raise ValueError("review identity does not match requested case/task")
    if first["reviewer"] == second["reviewer"]:
        raise ValueError("review gate requires different independent reviewers")
    if first["observation_sha256"] != second["observation_sha256"]:
        raise ValueError("reviews must reference the same observation hash")
    if any(
        review["evidence_class"] != expected_class or review["label_identity"] != expected_identity
        for review in (first, second)
    ):
        raise ValueError("reviews must bind the same evidence class and label identity")
    if first["review_packet_sha256"] == second["review_packet_sha256"]:
        raise ValueError("reviews require independent packet lineage")

    conflict = first["decision"] != second["decision"]
    if conflict and adjudication is None:
        return {
            "status": "HOLD",
            "reason": "adjudication_required",
            "label": None,
            "reviewers": [first["reviewer"], second["reviewer"]],
            "reviews": [first, second],
            "adjudication": None,
        }
    if not conflict and adjudication is not None:
        raise ValueError("adjudication is only allowed for conflicting reviews")

    resolved = first["decision"]
    clean_adjudication: dict[str, Any] | None = None
    reviewer_text = f"{first['reviewer']}+{second['reviewer']}"
    conflict_state = "none"
    signed_at = max(first["signed_at"], second["signed_at"])
    if conflict:
        clean_adjudication = validate_adjudication(adjudication or {})
        expected_packets = [first["review_packet_sha256"], second["review_packet_sha256"]]
        if (
            clean_adjudication["case_id"] != case_id
            or clean_adjudication["task_id"] != task_id
            or clean_adjudication["observation_sha256"] != first["observation_sha256"]
            or clean_adjudication["evidence_class"] != expected_class
            or clean_adjudication["label_identity"] != expected_identity
            or clean_adjudication["review_packet_sha256"] not in (expected_packets, [])
        ):
            raise ValueError("adjudication identity or packet lineage does not match reviews")
        if clean_adjudication["adjudicator"] in {first["reviewer"], second["reviewer"]}:
            raise ValueError("adjudicator must differ from both reviewers")
        if clean_adjudication["adjudicator"] in (disallowed_adjudicators or set()):
            raise ValueError("adjudicator violates required role separation")
        resolved = clean_adjudication["decision"]
        reviewer_text += f"+{clean_adjudication['adjudicator']}"
        conflict_state = "resolved_by_adjudication"
        signed_at = max(signed_at, clean_adjudication["signed_at"])

    if (
        evidence_class is not None
        and requested_class != _LEGACY_EVIDENCE_CLASS
        and disallowed_reviewers is None
    ):
        raise ValueError("prospective finalization requires explicit disallowed operational roles")
    review_bundle = {
        "reviews": [first, second],
        "adjudication": clean_adjudication,
    }
    label = {
        "case_id": case_id,
        "task_id": task_id,
        "observation_sha256": first["observation_sha256"],
        "evidence_class": expected_class,
        "label_identity": expected_identity,
        "review_packet_sha256": [first["review_packet_sha256"], second["review_packet_sha256"]],
        "label": resolved,
        "observed_at": signed_at,
        "source": f"high-risk-review://sha256:{canonical_sha256(review_bundle)}",
        "confidence_grade": "A",
        "quantifiable": True,
        "conflict_state": conflict_state,
        "reviewer": reviewer_text,
    }
    return {
        "status": "GO",
        "reason": "dual_review_agreement" if not conflict else "third_party_adjudication",
        "label": label,
        "reviewers": [first["reviewer"], second["reviewer"]],
        "reviews": [first, second],
        "adjudication": clean_adjudication,
    }
