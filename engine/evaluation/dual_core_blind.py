"""Immutable sealing and review statistics for dual-core blind validation."""
from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from engine.evaluation.prospective_artifacts import (
    ArtifactRef,
    publish_new_json,
    validate_parent_ref,
)


_SCHEMA_VERSION = "dual_core_blind_seal.v1"
_MATTER_CATEGORIES = frozenset(
    {"career", "wealth", "marriage", "health", "education", "family"}
)
_DIRECTIONS = frozenset({"positive", "negative", "mixed"})
_RECORD_FIELDS = frozenset(
    {
        "case_id",
        "round_index",
        "matter_category",
        "time_scope",
        "direction",
        "conclusion",
        "rationale",
        "applied_rules",
    }
)
_RULE_FIELDS = frozenset({"rule_id", "school", "rule_direction", "rule_statement"})


def seal_blind_run(
    *,
    case_id: str,
    matter_category: str,
    rounds: Sequence[Mapping[str, Any]],
    verification_records: Sequence[Mapping[str, Any]],
    expected_round_count: int,
    revealed_at: str,
    output_path: Path,
    admitted_root: Path,
    parent_refs: Sequence[ArtifactRef] = (),
) -> ArtifactRef:
    """Validate and publish all blind rounds atomically as a create-only seal.

    Verification records are required: this function is called at the first
    reveal boundary, and publishes the blind rounds and revealed evidence in
    one immutable artifact rather than exposing an intermediate mutable state.
    """
    _require_nonempty_string(case_id, "case_id")
    case_digest = hashlib.sha256(case_id.encode("utf-8")).hexdigest()
    canonical_output_path = (
        admitted_root / ".dual-core-blind-seals" / f"{case_digest}.json"
    )
    if output_path != canonical_output_path:
        raise ValueError(
            "output_path must be the canonical seal path for this case"
        )
    if matter_category not in _MATTER_CATEGORIES:
        raise ValueError("matter_category is outside the contract whitelist")
    if isinstance(expected_round_count, bool) or not isinstance(expected_round_count, int) or expected_round_count < 1:
        raise ValueError("expected_round_count must be a positive integer")
    _require_nonempty_string(revealed_at, "revealed_at")

    if not isinstance(rounds, Sequence) or isinstance(rounds, (str, bytes)):
        raise ValueError("rounds must be a sequence of structured records")
    if len(rounds) != expected_round_count:
        raise ValueError("round indexes must form the complete expected round grid")
    normalized_rounds = [_validate_round(record, case_id, matter_category) for record in rounds]
    indexes = [record["round_index"] for record in normalized_rounds]
    if sorted(indexes) != list(range(1, expected_round_count + 1)):
        raise ValueError("round indexes must form the complete expected round grid")
    normalized_rounds.sort(key=lambda record: record["round_index"])
    for record in normalized_rounds:
        rule_directions: dict[str, str] = {}
        for rule in record["applied_rules"]:
            previous_direction = rule_directions.get(rule["rule_id"])
            if previous_direction is not None and previous_direction != rule["rule_direction"]:
                raise ValueError(
                    "conflicting rule_direction for duplicate rule_id in one round"
                )
            rule_directions[rule["rule_id"]] = rule["rule_direction"]

    if not isinstance(verification_records, Sequence) or isinstance(verification_records, (str, bytes)):
        raise ValueError("verification_records must be a sequence")
    if not verification_records:
        raise ValueError("verification_records are required at first reveal")
    normalized_verification = [_validate_round(record, case_id, matter_category) for record in verification_records]

    if not isinstance(parent_refs, Sequence) or isinstance(parent_refs, (str, bytes)):
        raise ValueError("parent_refs must be a sequence")
    parents: list[dict[str, str]] = []
    seen_parent_paths: set[str] = set()
    for ref in parent_refs:
        if type(ref) is not ArtifactRef:
            raise TypeError("parent_refs must contain exact ArtifactRef values")
        validate_parent_ref(ref, admitted_root=admitted_root)
        if ref.artifact_path in seen_parent_paths:
            raise ValueError("duplicate parent artifact reference")
        seen_parent_paths.add(ref.artifact_path)
        parents.append(
            {"artifact_path": ref.artifact_path, "artifact_sha256": ref.artifact_sha256}
        )

    payload = {
        "schema_version": _SCHEMA_VERSION,
        "case_id": case_id,
        "matter_category": matter_category,
        "expected_round_count": expected_round_count,
        "rounds": normalized_rounds,
        "verification_records": normalized_verification,
        "revealed_at": revealed_at,
        "sealed": True,
        "parents": parents,
    }
    return publish_new_json(
        output_path,
        payload,
        dry_run=False,
        admitted_root=admitted_root,
    )


def compute_rule_review_statistics(
    *,
    rounds: Sequence[Mapping[str, Any]],
    independent_rule_outcomes: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Compute deduplicated reversal counts and rates from structured records."""
    seen_rules: set[tuple[str, str, str]] = set()
    final_rules: dict[tuple[str, str, str], str] = {}
    final_directions: dict[tuple[str, str], tuple[int, str]] = {}

    for record in rounds:
        if not isinstance(record, Mapping):
            raise ValueError("round record must be structured")
        case_id = _require_nonempty_string(record.get("case_id"), "case_id")
        category = record.get("matter_category")
        if category not in _MATTER_CATEGORIES:
            raise ValueError("matter_category is outside the contract whitelist")
        round_index = record.get("round_index")
        if isinstance(round_index, bool) or not isinstance(round_index, int) or round_index < 1:
            raise ValueError("round_index must be a positive integer")
        direction = record.get("direction")
        if direction not in _DIRECTIONS:
            raise ValueError("direction must be positive, negative, or mixed")
        group = (case_id, category)
        if group not in final_directions or round_index > final_directions[group][0]:
            final_directions[group] = (round_index, direction)
        elif round_index == final_directions[group][0]:
            raise ValueError("duplicate final round index for case and matter")

        applied_rules = record.get("applied_rules")
        if not isinstance(applied_rules, list):
            raise ValueError("applied_rules must be a list")
        for rule in applied_rules:
            if not isinstance(rule, Mapping):
                raise ValueError("applied rule must be structured")
            rule_id = _require_nonempty_string(rule.get("rule_id"), "rule_id")
            rule_direction = rule.get("rule_direction")
            if rule_direction not in _DIRECTIONS:
                raise ValueError("rule_direction must be positive, negative, or mixed")
            identity = (case_id, category, rule_id)
            seen_rules.add(identity)

    for record in rounds:
        group = (record["case_id"], record["matter_category"])
        if record["round_index"] == final_directions[group][0]:
            for rule in record["applied_rules"]:
                identity = (record["case_id"], record["matter_category"], rule["rule_id"])
                final_rules[identity] = rule["rule_direction"]

    verification: dict[tuple[str, str, str], bool] = {}
    for record in independent_rule_outcomes:
        if not isinstance(record, Mapping):
            raise ValueError("verification record must be structured")
        case_id = _require_nonempty_string(record.get("case_id"), "case_id")
        category = record.get("matter_category")
        if category not in _MATTER_CATEGORIES:
            raise ValueError("matter_category is outside the contract whitelist")
        rule_id = _require_nonempty_string(record.get("rule_id"), "rule_id")
        independent_hit = record.get("independent_hit")
        if type(independent_hit) is not bool:
            raise ValueError("independent_hit must be an exact bool")
        identity = (case_id, category, rule_id)
        previous = verification.get(identity)
        if previous is not None and previous != independent_hit:
            raise ValueError("conflicting verification outcomes for unique case/matter/rule")
        verification[identity] = independent_hit
    if set(verification) != seen_rules:
        raise ValueError(
            "independent_rule_outcomes must cover every unique case/matter/rule"
        )

    reversed_rules: set[tuple[str, str, str]] = set()
    for identity in seen_rules:
        case_id, category, _rule_id = identity
        final_rule_direction = final_rules.get(identity)
        final_direction = final_directions[(case_id, category)][1]
        not_retained = final_rule_direction is None
        direction_opposed = (
            final_direction in {"positive", "negative"}
            and final_rule_direction in {"positive", "negative"}
            and final_rule_direction != final_direction
        )
        if not_retained or direction_opposed:
            reversed_rules.add(identity)

    hit_reversals = sum(verification.get(identity) is True for identity in reversed_rules)
    miss_reversals = sum(verification.get(identity) is False for identity in reversed_rules)
    reversal_count = len(reversed_rules)
    return {
        "unique_case_matter_rule_count": len(seen_rules),
        "reversal_count": reversal_count,
        "independent_hits_reversed": hit_reversals,
        "independent_misses_reversed": miss_reversals,
        "arbitration_miss_rate": hit_reversals / reversal_count if reversal_count else None,
        "arbitration_correction_rate": miss_reversals / reversal_count if reversal_count else None,
    }


def _validate_round(
    record: Mapping[str, Any], case_id: str, matter_category: str
) -> dict[str, Any]:
    if not isinstance(record, Mapping) or set(record) != _RECORD_FIELDS:
        raise ValueError("round record must contain exactly the structured contract fields")
    if record.get("case_id") != case_id:
        raise ValueError("round case_id does not match seal case_id")
    if record.get("matter_category") != matter_category:
        raise ValueError("round matter_category does not match seal matter_category")
    index = record.get("round_index")
    if isinstance(index, bool) or not isinstance(index, int) or index < 1:
        raise ValueError("round_index must be a positive integer")
    if record.get("direction") not in _DIRECTIONS:
        raise ValueError("direction must be positive, negative, or mixed")
    for field in ("time_scope", "conclusion", "rationale"):
        _require_nonempty_string(record.get(field), field)
    rules = record.get("applied_rules")
    if not isinstance(rules, list):
        raise ValueError("applied_rules must be a list")
    normalized_rules: list[dict[str, str]] = []
    for rule in rules:
        if not isinstance(rule, Mapping) or set(rule) != _RULE_FIELDS:
            raise ValueError("applied rule must contain exactly the structured contract fields")
        normalized = {
            field: _require_nonempty_string(rule.get(field), field)
            for field in _RULE_FIELDS
        }
        if normalized["rule_direction"] not in _DIRECTIONS:
            raise ValueError("rule_direction must be positive, negative, or mixed")
        normalized_rules.append(normalized)
    return {
        "case_id": case_id,
        "round_index": index,
        "matter_category": matter_category,
        "time_scope": record["time_scope"],
        "direction": record["direction"],
        "conclusion": record["conclusion"],
        "rationale": record["rationale"],
        "applied_rules": normalized_rules,
    }


def _require_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _require_exact_bool(value: Any, field: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field} must be an exact bool")
    return value
