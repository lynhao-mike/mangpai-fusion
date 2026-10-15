from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest

from engine.evaluation.prospective_artifacts import (
    ArtifactRef,
    canonical_artifact_sha256,
    publish_new_json,
    validate_parent_ref,
)


def _api(name: str):
    try:
        module = importlib.import_module("engine.evaluation.dual_core_blind")
    except ModuleNotFoundError:
        pytest.fail("dual_core_blind sealing API is not implemented yet", pytrace=False)
    function = getattr(module, name, None)
    if not callable(function):
        pytest.fail(f"dual_core_blind.{name} is not implemented yet", pytrace=False)
    return function


def _round(index: int, *, rules: list[dict[str, str]] | None = None) -> dict[str, Any]:
    return {
        "case_id": "C-SYNTH-DUAL-001",
        "round_index": index,
        "matter_category": "career",
        "time_scope": "natal",
        "direction": "positive",
        "conclusion": f"synthetic round {index}",
        "rationale": "synthetic evidence only",
        "applied_rules": rules or [
            {
                "rule_id": "ZP-SYNTH-CAREER-001",
                "school": "ziping",
                "rule_direction": "positive",
                "rule_statement": "synthetic rule",
            }
        ],
    }


def _verification_record(index: int) -> dict[str, Any]:
    return {
        "case_id": "C-SYNTH-DUAL-001",
        "round_index": index,
        "matter_category": "career",
        "time_scope": "natal",
        "direction": "positive",
        "conclusion": f"synthetic verification {index}",
        "rationale": "synthetic evidence only",
        "applied_rules": [],
    }


def _canonical_seal_path(root: Path, case_id: str = "C-SYNTH-DUAL-001") -> Path:
    case_digest = hashlib.sha256(case_id.encode("utf-8")).hexdigest()
    return root / ".dual-core-blind-seals" / f"{case_digest}.json"


def _seal(
    *,
    output_path: Path,
    rounds: list[dict[str, Any]] | None = None,
    verification_records: list[dict[str, Any]] | None = None,
    parent_refs: list[ArtifactRef] | None = None,
    matter_category: str = "career",
    expected_round_count: int = 2,
    canonicalize_path: bool = True,
):
    seal = _api("seal_blind_run")
    return seal(
        case_id="C-SYNTH-DUAL-001",
        matter_category=matter_category,
        rounds=rounds if rounds is not None else [_round(1), _round(2)],
        verification_records=verification_records if verification_records is not None else [
            _verification_record(3),
        ],
        expected_round_count=expected_round_count,
        revealed_at="2026-10-14T00:00:00Z",
        output_path=(
            _canonical_seal_path(output_path.parent)
            if canonicalize_path
            else output_path
        ),
        admitted_root=output_path.parent,
        parent_refs=parent_refs or [],
    )


def test_seal_rejects_matter_category_outside_contract_whitelist(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="matter_category"):
        _seal(output_path=tmp_path / "invalid-category.json", matter_category="personality")


def test_seal_requires_complete_unique_round_grid(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="round indexes"):
        _seal(
            output_path=tmp_path / "round-gap.json",
            rounds=[_round(1), _round(3)],
            expected_round_count=2,
        )


def test_seal_rejects_unstructured_or_out_of_whitelist_direction(tmp_path: Path) -> None:
    invalid_round = _round(1)
    invalid_round["applied_rules"] = [
        {
            "rule_id": "ZP-SYNTH-CAREER-001",
            "school": "ziping",
            "rule_direction": "uncertain",
            "rule_statement": "synthetic rule",
        }
    ]
    with pytest.raises(ValueError, match="rule_direction"):
        _seal(
            output_path=tmp_path / "invalid-direction.json",
            rounds=[invalid_round, _round(2)],
        )


def test_seal_rejects_verification_records_with_non_contract_fields(tmp_path: Path) -> None:
    invalid = {
        "case_id": "C-SYNTH-DUAL-001",
        "round_index": 3,
        "matter_category": "career",
        "time_scope": "natal",
        "direction": "positive",
        "conclusion": "synthetic verification",
        "rationale": "synthetic evidence only",
        "applied_rules": [],
        "independent_hit": True,
    }
    with pytest.raises(ValueError, match="exactly the structured contract fields"):
        _seal(output_path=tmp_path / "invalid-verification.json", verification_records=[invalid])


def test_seal_rejects_conflicting_directions_for_same_rule_in_one_round(tmp_path: Path) -> None:
    conflicting = _round(
        2,
        rules=[
            {
                "rule_id": "ZP-SYNTH-CAREER-001",
                "school": "ziping",
                "rule_direction": "positive",
                "rule_statement": "synthetic rule",
            },
            {
                "rule_id": "ZP-SYNTH-CAREER-001",
                "school": "ziping",
                "rule_direction": "negative",
                "rule_statement": "synthetic rule",
            },
        ],
    )
    with pytest.raises(ValueError, match="conflicting rule_direction"):
        _seal(output_path=tmp_path / "conflicting-rule.json", rounds=[_round(1), conflicting])


def test_seal_publishes_all_rounds_once_with_parent_chain_and_canonical_hash(tmp_path: Path) -> None:
    parent_path = tmp_path / "synthetic-parent.json"
    parent_ref = publish_new_json(
        parent_path,
        {"schema_version": "synthetic.parent.v1", "parents": []},
        dry_run=False,
        admitted_root=tmp_path,
    )
    sealed_ref = _seal(
        output_path=tmp_path / "sealed.json",
        parent_refs=[parent_ref],
    )

    sealed = validate_parent_ref(sealed_ref, admitted_root=tmp_path)
    assert sealed["schema_version"] == "dual_core_blind_seal.v1"
    assert sealed["sealed"] is True
    assert sealed["revealed_at"] == "2026-10-14T00:00:00Z"
    assert [record["round_index"] for record in sealed["rounds"]] == [1, 2]
    assert sealed["verification_records"] == [_verification_record(3)]
    assert set(sealed["verification_records"][0]) == {
        "case_id",
        "round_index",
        "matter_category",
        "time_scope",
        "direction",
        "conclusion",
        "rationale",
        "applied_rules",
    }
    assert sealed["parents"] == [
        {
            "artifact_path": parent_ref.artifact_path,
            "artifact_sha256": parent_ref.artifact_sha256,
        }
    ]
    assert sealed["artifact_sha256"] == canonical_artifact_sha256(sealed)
    assert json.loads((tmp_path / "synthetic-parent.json").read_text(encoding="utf-8"))

    with pytest.raises(ValueError, match="already exists"):
        _seal(output_path=tmp_path / "sealed.json")


def test_seal_rejects_second_path_for_already_sealed_case(tmp_path: Path) -> None:
    _seal(output_path=tmp_path / "first-name-is-ignored.json")

    with pytest.raises(ValueError, match="canonical seal path"):
        _seal(
            output_path=tmp_path / "alternate.json",
            canonicalize_path=False,
        )


def test_seal_rejects_parent_hash_drift_without_publishing(tmp_path: Path) -> None:
    parent_path = tmp_path / "synthetic-parent.json"
    parent_ref = publish_new_json(
        parent_path,
        {"schema_version": "synthetic.parent.v1", "parents": []},
        dry_run=False,
        admitted_root=tmp_path,
    )
    parent_path.write_text('{"artifact_sha256":"' + "0" * 64 + '"}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="digest mismatch|canonical digest mismatch|byte drift"):
        _seal(
            output_path=tmp_path / "must-not-publish.json",
            parent_refs=[parent_ref],
        )
    assert not (tmp_path / "must-not-publish.json").exists()


def test_review_statistics_use_unique_case_matter_rule_and_null_zero_denominator() -> None:
    compute = _api("compute_rule_review_statistics")
    empty = compute(rounds=[], independent_rule_outcomes=[])
    assert empty["reversal_count"] == 0
    assert empty["arbitration_miss_rate"] is None
    assert empty["arbitration_correction_rate"] is None

    rounds = [
        _round(
            1,
            rules=[
                {
                    "rule_id": "RULE-HIT",
                    "school": "ziping",
                    "rule_direction": "positive",
                    "rule_statement": "hit rule",
                },
                {
                    "rule_id": "RULE-MISS",
                    "school": "duan",
                    "rule_direction": "positive",
                    "rule_statement": "miss rule",
                },
            ],
        ),
        _round(
            2,
            rules=[
                {
                    "rule_id": "RULE-HIT",
                    "school": "ziping",
                    "rule_direction": "positive",
                    "rule_statement": "hit rule",
                }
            ],
        ),
    ]
    independent_rule_outcomes = [
        {"case_id": "C-SYNTH-DUAL-001", "matter_category": "career", "rule_id": "RULE-HIT", "independent_hit": True},
        {"case_id": "C-SYNTH-DUAL-001", "matter_category": "career", "rule_id": "RULE-MISS", "independent_hit": False},
    ]
    stats = compute(rounds=rounds, independent_rule_outcomes=independent_rule_outcomes)
    assert stats["reversal_count"] == 1
    assert stats["independent_misses_reversed"] == 1
    assert stats["independent_hits_reversed"] == 0
    assert stats["arbitration_miss_rate"] == 0.0
    assert stats["arbitration_correction_rate"] == 1.0
