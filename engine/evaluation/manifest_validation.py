"""Strict shared validation for reviewed school-capability manifests."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

MANIFEST_SCHEMA = "school-capability-case-manifest/v1"
ELIGIBILITIES = {"blind_candidate", "historical_blind_candidate", "development_only"}
ROUTE_FIELDS = {
    "school_id", "task_id", "chart_prototype_id", "claim_type",
    "time_horizon", "evidence_completeness_band",
}
MANIFEST_RECORD_FIELDS = {
    "case_id", "has_input", "has_feedback", "has_statement_index",
    "has_existing_report", "feedback_quantifiable", "contamination_flags",
    "eligibility", "evidence_notes", "eligible_routes",
}
GATE_THRESHOLDS_POLICY: dict[str, float | int] = {
    "coverage_complete": 1.0,
    "calibration_min_samples": 5,
    "calibration_max_error": 0.2,
    "high_risk_min_utility": 0.0,
}


def _is_utc_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00").tzinfo == timezone.utc
    except ValueError:
        return False


def _human_reviewer(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and not value.lower().startswith(("automated", "agent", "ai-"))
    )


def validate_routes(routes: object) -> list[dict[str, str]]:
    if not isinstance(routes, list):
        raise ValueError("eligible routes must be a list")
    identities: set[tuple[str, str]] = set()
    for route in routes:
        if (
            not isinstance(route, dict)
            or set(route) != ROUTE_FIELDS
            or any(not isinstance(route[field], str) or not route[field].strip() for field in ROUTE_FIELDS)
        ):
            raise ValueError("eligible route schema is invalid")
        identity = route["task_id"], route["school_id"]
        if identity in identities:
            raise ValueError("eligible routes must be unique by case/task/school")
        identities.add(identity)
    return routes


def validate_reviewed_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    expected_top_level = {"schema_version", "generated_at", "reviewed_by", "expected_schools", "records"}
    if set(manifest) != expected_top_level or manifest.get("schema_version") != MANIFEST_SCHEMA:
        raise ValueError("manifest top-level schema is invalid")
    if not _is_utc_timestamp(manifest.get("generated_at")):
        raise ValueError("manifest generated_at must be an ISO 8601 UTC timestamp")
    if not _human_reviewer(manifest.get("reviewed_by")):
        raise ValueError("reviewed manifest requires a human reviewer")

    expected_schools = manifest.get("expected_schools")
    if (
        not isinstance(expected_schools, list)
        or not expected_schools
        or len(set(expected_schools)) != len(expected_schools)
        or any(not isinstance(item, str) or not item.strip() for item in expected_schools)
    ):
        raise ValueError("expected_schools must be unique non-empty strings")

    records = manifest.get("records")
    if not isinstance(records, list) or any(
        not isinstance(row, dict) or set(row) != MANIFEST_RECORD_FIELDS for row in records
    ):
        raise ValueError("manifest records have invalid schema")

    seen_cases: set[str] = set()
    for row in records:
        case_id = row["case_id"]
        if not isinstance(case_id, str) or not case_id.strip() or case_id in seen_cases:
            raise ValueError("manifest requires unique case_id")
        seen_cases.add(case_id)
        if any(
            type(row[field]) is not bool
            for field in ("has_input", "has_feedback", "has_statement_index", "has_existing_report", "feedback_quantifiable")
        ) or any(
            not isinstance(row[field], list) or any(not isinstance(item, str) for item in row[field])
            for field in ("contamination_flags", "evidence_notes")
        ):
            raise ValueError("manifest record value types are invalid")
        if row["eligibility"] not in ELIGIBILITIES:
            raise ValueError("manifest eligibility is invalid")

        routes = validate_routes(row["eligible_routes"])
        if row["eligibility"] == "development_only" and routes:
            raise ValueError("development_only routes must be empty")
        if row["eligibility"] in {"blind_candidate", "historical_blind_candidate"}:
            if not row["has_input"]:
                raise ValueError("manifest candidate must have input")
            if row["contamination_flags"]:
                raise ValueError("manifest candidate must have no contamination")
            if row["eligibility"] == "historical_blind_candidate" and (
                not row["has_feedback"] or not row["feedback_quantifiable"]
            ):
                raise ValueError("historical candidate requires quantifiable feedback")
            if row["eligibility"] == "blind_candidate" and row["has_feedback"]:
                raise ValueError("prospective candidate must not have feedback")
        if any(route["school_id"] not in expected_schools for route in routes):
            raise ValueError("route school_id must be in expected_schools")
    return records
