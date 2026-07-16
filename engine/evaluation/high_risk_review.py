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
_REVIEW_SCHEMA = "school-capability-high-risk-review/v1"
_ADJUDICATION_SCHEMA = "school-capability-high-risk-adjudication/v1"
_PACKET_SCHEMA = "school-capability-high-risk-review-packet/v1"
_REVIEW_FIELDS = {
    "schema_version",
    "case_id",
    "task_id",
    "observation_sha256",
    "reviewer",
    "decision",
    "source_refs",
    "rationale",
    "signed_at",
}
_ADJUDICATION_FIELDS = {
    "schema_version",
    "case_id",
    "task_id",
    "observation_sha256",
    "adjudicator",
    "decision",
    "source_refs",
    "rationale",
    "signed_at",
}
_FORBIDDEN_MARKERS = {
    "probability",
    "prediction",
    "runner output",
    "runner_output",
    "school output",
    "school_output",
    "report text",
    "report_text",
    "claim",
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


def validate_review(
    review: Mapping[str, Any], *, disallowed_reviewers: set[str] | None = None
) -> dict[str, Any]:
    """Validate one independent review without reading predictions or reports."""
    if not isinstance(review, Mapping):
        raise ValueError("review must be an object")
    _assert_no_leakage(review)
    if set(review) != _REVIEW_FIELDS or review.get("schema_version") != _REVIEW_SCHEMA:
        raise ValueError("review schema is invalid")
    task_id = _task(review.get("task_id"))
    reviewer = _human(review.get("reviewer"), "reviewer")
    if reviewer in (disallowed_reviewers or set()):
        raise ValueError("reviewer violates required role separation")
    if not isinstance(review.get("case_id"), str) or not review["case_id"].strip():
        raise ValueError("case_id is required")
    digest = review.get("observation_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("observation_sha256 must be a SHA-256 digest")
    _decision(task_id, review.get("decision"))
    _source_refs(review.get("source_refs"))
    if not isinstance(review.get("rationale"), str) or not review["rationale"].strip():
        raise ValueError("rationale is required")
    _timestamp(review.get("signed_at"), "signed_at")
    return dict(review)


def validate_adjudication(adjudication: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(adjudication, Mapping):
        raise ValueError("adjudication must be an object")
    _assert_no_leakage(adjudication)
    if (
        set(adjudication) != _ADJUDICATION_FIELDS
        or adjudication.get("schema_version") != _ADJUDICATION_SCHEMA
    ):
        raise ValueError("adjudication schema is invalid")
    task_id = _task(adjudication.get("task_id"))
    _human(adjudication.get("adjudicator"), "adjudicator")
    if not isinstance(adjudication.get("case_id"), str) or not adjudication["case_id"].strip():
        raise ValueError("case_id is required")
    digest = adjudication.get("observation_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("observation_sha256 must be a SHA-256 digest")
    _decision(task_id, adjudication.get("decision"))
    _source_refs(adjudication.get("source_refs"))
    if not isinstance(adjudication.get("rationale"), str) or not adjudication["rationale"].strip():
        raise ValueError("rationale is required")
    _timestamp(adjudication.get("signed_at"), "signed_at")
    return dict(adjudication)


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
    reviewer_a: str,
    reviewer_b: str,
    disallowed_reviewers: set[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Create two separate packets from the same observation, with no predictions."""
    clean = validate_observation(observation)
    first = _human(reviewer_a, "reviewer_a")
    second = _human(reviewer_b, "reviewer_b")
    if first == second:
        raise ValueError("review gate requires different independent reviewers")
    blocked = disallowed_reviewers or set()
    if first in blocked or second in blocked:
        raise ValueError("reviewer violates required role separation")
    digest = canonical_sha256(clean)

    def packet(reviewer: str) -> dict[str, Any]:
        return {
            "schema_version": _PACKET_SCHEMA,
            "case_id": clean["case_id"],
            "task_id": clean["task_id"],
            "observation_sha256": digest,
            "reviewer": reviewer,
            "observation": clean,
        }

    return {"reviewer_a": packet(first), "reviewer_b": packet(second)}


def review_from_packet(packet: Mapping[str, Any], decision: Mapping[str, Any]) -> dict[str, Any]:
    """Bind a human decision to one prepared packet."""
    if not isinstance(packet, Mapping) or set(packet) != {
        "schema_version", "case_id", "task_id", "observation_sha256", "reviewer", "observation"
    } or packet.get("schema_version") != _PACKET_SCHEMA:
        raise ValueError("review packet schema is invalid")
    clean_observation = validate_observation(packet["observation"])
    if canonical_sha256(clean_observation) != packet["observation_sha256"]:
        raise ValueError("review packet observation hash mismatch")
    if not isinstance(decision, Mapping) or set(decision) != {
        "decision", "source_refs", "rationale", "signed_at"
    }:
        raise ValueError("review decision schema is invalid")
    review = {
        "schema_version": _REVIEW_SCHEMA,
        "case_id": packet["case_id"],
        "task_id": packet["task_id"],
        "observation_sha256": packet["observation_sha256"],
        "reviewer": packet["reviewer"],
        **dict(decision),
    }
    return validate_review(review)


def finalize_reviews(
    case_id: str,
    task_id: str,
    review_a: Mapping[str, Any],
    review_b: Mapping[str, Any],
    adjudication: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Produce an A-grade standard label only after valid dual review or adjudication."""
    task_id = _task(task_id)
    first = validate_review(review_a)
    second = validate_review(review_b)
    for review in (first, second):
        if review["case_id"] != case_id or review["task_id"] != task_id:
            raise ValueError("review identity does not match requested case/task")
    if first["reviewer"] == second["reviewer"]:
        raise ValueError("review gate requires different independent reviewers")
    if first["observation_sha256"] != second["observation_sha256"]:
        raise ValueError("reviews must reference the same observation hash")

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
        if (
            clean_adjudication["case_id"] != case_id
            or clean_adjudication["task_id"] != task_id
            or clean_adjudication["observation_sha256"] != first["observation_sha256"]
        ):
            raise ValueError("adjudication identity or observation hash does not match reviews")
        if clean_adjudication["adjudicator"] in {first["reviewer"], second["reviewer"]}:
            raise ValueError("adjudicator must differ from both reviewers")
        resolved = clean_adjudication["decision"]
        reviewer_text += f"+{clean_adjudication['adjudicator']}"
        conflict_state = "resolved_by_adjudication"
        signed_at = max(signed_at, clean_adjudication["signed_at"])

    review_bundle = {
        "reviews": [first, second],
        "adjudication": clean_adjudication,
    }
    label = {
        "case_id": case_id,
        "task_id": task_id,
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
