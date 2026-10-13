from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tools.career_relation_expert_annotation import (
    agreement_gate,
    canonical_sha256,
    finalize_annotations,
    prepare_blind_packet,
    status,
    submit_annotation,
    validate_annotation,
)


ROOT = Path(__file__).resolve().parents[1]
DISPOSITION = ROOT / "META/as-of-evaluation/career-relation-model-v1-disposition.json"


def _chart() -> dict[str, Any]:
    return {
        "case_id": "SYNTHETIC-TEST-001",
        "sex": "乾",
        "pillars": {
            "year": "甲子",
            "month": "乙丑",
            "day": "丙寅",
            "hour": "丁卯",
        },
        "hidden_stems": {"year": ["癸"], "month": ["己", "癸", "辛"]},
    }


def _theory_refs() -> list[dict[str, str]]:
    return [
        {
            "path": "theory/raw/gao/promoted/appendix-zhiye.md",
            "sha256": "a" * 64,
            "scope": "five-stage locator and six left-pillar nature categories",
        },
        {
            "path": "engine/contracts/15-career-relation-inference-v1.md",
            "sha256": "b" * 64,
            "scope": "frozen structural locator contract",
        },
    ]


def _annotation(
    reviewer_id: str,
    *,
    career_pillar: str | None = "month",
    selected_stage: str | None = "step_1_self_officer_killing",
    left_pillar: str | None = "year",
    key_relations: list[str] | None = None,
    nature_labels: list[str] | None = None,
    abstention_reason: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "career-relation-expert-annotation/v1",
        "case_id": "SYNTHETIC-TEST-001",
        "blind_packet_sha256": "c" * 64,
        "reviewer_id": reviewer_id,
        "career_pillar": career_pillar,
        "selected_stage": selected_stage,
        "left_pillar": left_pillar,
        "key_relations": key_relations if key_relations is not None else ["combination:month-year"],
        "nature_labels": nature_labels if nature_labels is not None else ["印"],
        "strength_state": "unresolved",
        "semantic_layers": {
            "career_type": {"status": "annotated", "value": "官杀关联类型"},
            "career_nature": {"status": "annotated", "value": "印性质"},
            "income_mode": {"status": "unresolved", "value": None},
            "organization_form": {"status": "unresolved", "value": None},
            "reality_state": {"status": "out_of_scope", "value": None},
        },
        "unresolved_items": ["generic_tomb_entry_predicate"],
        "conflicts": [],
        "abstention_reason": abstention_reason,
        "signed_at": "2026-07-31T00:00:00Z",
    }


def _adjudication() -> dict[str, Any]:
    return {
        "schema_version": "career-relation-expert-adjudication/v1",
        "case_id": "SYNTHETIC-TEST-001",
        "blind_packet_sha256": "c" * 64,
        "adjudicator_id": "human-adjudicator-c",
        "resolution": _annotation("human-adjudicator-c"),
        "rationale": "基于两份原始标注逐项裁决，保留分歧记录。",
        "signed_at": "2026-08-01T00:00:00Z",
    }


@pytest.mark.parametrize(
    "leaked_key",
    [
        "occupation",
        "feedback",
        "known_facts",
        "career_label",
        "model_prediction",
        "reality_state",
    ],
)
def test_blind_packet_rejects_recursive_leakage(leaked_key: str) -> None:
    chart = _chart()
    chart["nested"] = {leaked_key: "forbidden"}

    with pytest.raises(ValueError, match="leakage"):
        prepare_blind_packet(chart, _theory_refs())


def test_blind_packet_hash_is_deterministic_and_default_is_dry_run(tmp_path: Path) -> None:
    target = tmp_path / "blind-packet.json"

    first = prepare_blind_packet(_chart(), _theory_refs(), output=target)
    second = prepare_blind_packet(_chart(), list(reversed(_theory_refs())), output=target)

    assert first == second
    assert first["manifest"]["content_sha256"] == canonical_sha256(first["packet"])
    assert first["manifest"]["production_switch_permitted"] is False
    assert not target.exists()


def test_blind_packet_is_create_only_and_rejects_symlink(tmp_path: Path) -> None:
    target = tmp_path / "blind-packet.json"
    prepare_blind_packet(_chart(), _theory_refs(), output=target, dry_run=False)

    with pytest.raises(ValueError, match="must not exist"):
        prepare_blind_packet(_chart(), _theory_refs(), output=target, dry_run=False)

    source = tmp_path / "source.json"
    source.write_text("{}", encoding="utf-8")
    link = tmp_path / "linked.json"
    try:
        link.symlink_to(source)
    except OSError:
        pytest.skip("symlink creation is unavailable on this Windows host")
    with pytest.raises(ValueError, match="symlink"):
        prepare_blind_packet(_chart(), _theory_refs(), output=link, dry_run=False)


def test_annotation_requires_separate_semantic_layers_and_rejects_terminal_compression() -> None:
    annotation = _annotation("human-reviewer-a")
    validate_annotation(annotation)

    assert set(annotation["semantic_layers"]) == {
        "career_type",
        "career_nature",
        "income_mode",
        "organization_form",
        "reality_state",
    }

    annotation["employment_inclined"] = True
    with pytest.raises(ValueError, match="terminal|unsupported|field"):
        validate_annotation(annotation)


def test_annotation_validates_six_natures_and_five_locator_stages() -> None:
    for nature in ["正财", "偏财", "印", "食伤", "官杀", "比劫"]:
        validate_annotation(_annotation("human-reviewer-a", nature_labels=[nature]))

    invalid = _annotation("human-reviewer-a")
    invalid["selected_stage"] = "step_6_invented"
    with pytest.raises(ValueError, match="selected_stage"):
        validate_annotation(invalid)


def test_agent_cannot_submit_as_expert_and_raw_submission_is_create_only(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="human reviewer"):
        submit_annotation(_annotation("agent-roo"), tmp_path / "agent.json", dry_run=False)

    target = tmp_path / "review-a.json"
    submit_annotation(_annotation("human-reviewer-a"), target, dry_run=False)
    original = target.read_bytes()
    with pytest.raises(ValueError, match="must not exist"):
        submit_annotation(_annotation("human-reviewer-a"), target, dry_run=False)
    assert target.read_bytes() == original


def test_duplicate_reviewer_is_rejected() -> None:
    review = _annotation("human-reviewer-a")
    with pytest.raises(ValueError, match="different independent reviewers"):
        finalize_annotations(review, review)


def test_missing_dual_review_returns_not_ready() -> None:
    result = agreement_gate([(_annotation("human-reviewer-a"), None)])

    assert result["status"] == "not_ready"
    assert result["failures"] == ["missing_dual_review"]
    assert all(metric["denominator"] == 0 for metric in result["metrics"].values())
    assert all(metric["value"] is None for metric in result["metrics"].values())


def test_unresolved_disagreement_requires_third_party_adjudication() -> None:
    review_a = _annotation("human-reviewer-a")
    review_b = _annotation("human-reviewer-b", career_pillar="hour", left_pillar="day")

    final = finalize_annotations(review_a, review_b)
    assert final["status"] == "not_ready"
    assert final["reason"] == "adjudication_required"

    bad = _adjudication()
    bad["adjudicator_id"] = "human-reviewer-a"
    with pytest.raises(ValueError, match="third independent human"):
        finalize_annotations(review_a, review_b, bad)

    resolved = finalize_annotations(review_a, review_b, _adjudication())
    assert resolved["status"] == "ready"
    assert resolved["raw_annotations"] == [review_a, review_b]
    assert resolved["conflict_state"] == "resolved_by_adjudication"


def test_agreement_metrics_have_explicit_denominators_and_jaccard() -> None:
    review_a = _annotation(
        "human-reviewer-a",
        key_relations=["combination:month-year", "clash:day-hour"],
        nature_labels=["印", "官杀"],
    )
    review_b = _annotation(
        "human-reviewer-b",
        key_relations=["combination:month-year", "harm:year-day"],
        nature_labels=["印"],
    )

    result = agreement_gate([(review_a, review_b)], adjudications=[_adjudication()])

    assert result["status"] == "ready"
    assert result["metrics"]["career_pillar"] == {"numerator": 1, "denominator": 1, "value": 1.0}
    assert result["metrics"]["selected_stage"] == {"numerator": 1, "denominator": 1, "value": 1.0}
    assert result["metrics"]["left_pillar"] == {"numerator": 1, "denominator": 1, "value": 1.0}
    assert result["metrics"]["key_relation_set"] == {
        "numerator": 1.0 / 3.0,
        "denominator": 1,
        "value": 1.0 / 3.0,
    }
    assert result["metrics"]["nature_label_set"] == {"numerator": 0.5, "denominator": 1, "value": 0.5}
    assert result["metrics"]["abstention"] == {"numerator": 1, "denominator": 1, "value": 1.0}


def test_missing_metric_values_are_excluded_not_scored_as_zero() -> None:
    review_a = _annotation(
        "human-reviewer-a",
        career_pillar=None,
        selected_stage=None,
        left_pillar=None,
        key_relations=[],
        nature_labels=[],
        abstention_reason="insufficient_structural_evidence",
    )
    review_b = _annotation(
        "human-reviewer-b",
        career_pillar=None,
        selected_stage=None,
        left_pillar=None,
        key_relations=[],
        nature_labels=[],
        abstention_reason="insufficient_structural_evidence",
    )

    result = agreement_gate([(review_a, review_b)])

    assert result["status"] == "not_ready"
    for name in ["career_pillar", "selected_stage", "left_pillar", "key_relation_set", "nature_label_set"]:
        assert result["metrics"][name] == {"numerator": 0, "denominator": 0, "value": None}
    assert result["metrics"]["abstention"] == {"numerator": 1, "denominator": 1, "value": 1.0}


def test_current_repository_status_is_not_ready_and_v1_stays_invalidated() -> None:
    result = status(disposition_path=DISPOSITION)

    assert result["status"] == "not_ready"
    assert result["failures"] == ["no_human_annotations"]
    assert result["model_id"] == "career-path-relation-model-v1"
    assert result["model_decision"] == "invalidated_requires_new_model_id"
    assert result["promotion_eligible"] is False
    assert result["production_switch_permitted"] is False

    disposition = json.loads(DISPOSITION.read_text(encoding="utf-8"))
    assert disposition["formal_scoring_status"] == "invalidated"
    assert disposition["holdout_scoring_permitted"] is False
    assert disposition["historical_identity_frozen"] is True

    assert result["permitted_uses"] == [
        "structural_mechanism_audit",
        "new_model_id_design",
    ]


def test_status_fails_closed_if_disposition_attempts_to_rehabilitate_v1(tmp_path: Path) -> None:
    disposition = json.loads(DISPOSITION.read_text(encoding="utf-8"))
    disposition["promotion_eligible"] = True
    disposition["production_switch_permitted"] = True
    path = tmp_path / "disposition.json"
    path.write_text(json.dumps(disposition, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="invalidated model-v1|frozen disposition"):
        status(disposition_path=path)
