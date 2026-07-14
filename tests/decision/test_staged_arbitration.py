from __future__ import annotations

import json
from dataclasses import replace

import pytest

from engine.claims import Claim, Evidence, TimeWindow
from engine.decision.l6_arbitration import build_arbitration_decisions
from engine.decision.models import EventHypothesis
from engine.decision.l6_staged_arbitration import (
    ApplicabilityPlan,
    ConflictRule,
    ConflictRuleSet,
    StageDecision,
    StagedArbitrationResult,
    arbitrate_staged,
    detect_opposition,
)


def _claim(
    claim_id: str,
    *,
    school_id: str,
    claim_type: str,
    task_id: str,
    domain: str,
    stance: str = "support",
    polarity: str = "neutral",
    magnitude: float | None = None,
    confidence: float = 0.8,
    evidence_count: int = 1,
) -> Claim:
    evidence = tuple(
        Evidence(
            evidence_id=f"{claim_id}-E-{index}",
            fact_refs=(f"four_pillars.{index}",),
            feature_refs=(),
            rule_id=f"RULE-{claim_id}-{index}",
            text=f"{claim_id} evidence {index}",
        )
        for index in range(evidence_count)
    )
    return Claim(
        claim_id=claim_id,
        school_id=school_id,
        task_id=task_id,
        claim_type=claim_type,  # type: ignore[arg-type]
        stance=stance,  # type: ignore[arg-type]
        statement=f"statement for {claim_id}",
        evidence=evidence,
        falsifier=f"falsifier for {claim_id}",
        time_window=(TimeWindow(2026, 2026) if claim_type in {"event_claim", "timing_claim"} else None),
        confidence_basis=f"basis for {claim_id}",
        applicability_snapshot={"domain": domain, "magnitude": magnitude, "confidence": confidence},
        domain=domain,
        polarity=polarity,  # type: ignore[arg-type]
        magnitude=magnitude,
        confidence=confidence,
    )


def _rules(*rules: ConflictRule) -> ConflictRuleSet:
    return ConflictRuleSet(rules=tuple(rules))


def test_staged_contract_round_trips_and_requires_exactly_three_ordered_stages() -> None:
    empty = [
        StageDecision.empty("structure"),
        StageDecision.empty("event"),
        StageDecision.empty("timing"),
    ]
    result = StagedArbitrationResult(
        case_id="C-L6-001",
        stages=tuple(empty),
        weight_source="uniform_fallback",
    )

    restored = StagedArbitrationResult.from_dict(json.loads(json.dumps(result.to_dict(), ensure_ascii=False)))

    assert restored == result
    with pytest.raises(ValueError, match="exactly three"):
        StagedArbitrationResult("C-L6-001", tuple(empty[:2]), "uniform_fallback")
    with pytest.raises(ValueError, match="structure, event, timing"):
        StagedArbitrationResult("C-L6-001", tuple(reversed(empty)), "uniform_fallback")
    with pytest.raises(ValueError, match="invalid stage"):
        replace(empty[0], stage="portrait")


def test_detect_opposition_uses_structured_claim_fields_not_wording() -> None:
    positive = _claim("positive", school_id="ziping", claim_type="structure_claim", task_id="strength", domain="总体", polarity="positive")
    negative = _claim("negative", school_id="ditiansui", claim_type="structure_claim", task_id="strength", domain="总体", polarity="negative")
    light = _claim("light", school_id="duan_jianye", claim_type="event_claim", task_id="wealth.loss", domain="财富", magnitude=0.2)
    severe = _claim("severe", school_id="gao_dechen", claim_type="event_claim", task_id="wealth.loss", domain="财富", magnitude=0.9)
    occurs = _claim("occurs", school_id="yang_qingjuan", claim_type="event_claim", task_id="marriage.divorce", domain="婚姻", stance="support")
    not_occurs = _claim("not-occurs", school_id="ren_fuhong", claim_type="event_claim", task_id="marriage.divorce", domain="婚姻", stance="oppose")

    assert detect_opposition([positive, negative]) == "polarity_opposition"
    assert detect_opposition([light, severe]) == "magnitude_opposition"
    assert detect_opposition([occurs, not_occurs]) == "occurrence_opposition"
    assert detect_opposition([positive, replace(positive, claim_id="same")]) == "none"
    assert detect_opposition([positive, replace(negative, task_id="different")]) == "none"


def test_capability_weighted_rule_resolves_conflict_and_preserves_minority() -> None:
    stronger = _claim("stronger", school_id="ziping", claim_type="structure_claim", task_id="strength", domain="总体", polarity="positive")
    minority = _claim("minority", school_id="ditiansui", claim_type="structure_claim", task_id="strength", domain="总体", polarity="negative")
    rule = ConflictRule(
        rule_id="CR-STRUCT-STRENGTH-001",
        applies_to_stage="structure",
        conflict_type="polarity_opposition",
        target_claim_type="structure_claim",
        resolution_strategy="capability_weighted",
        min_weight_gap=0.15,
        falsifier="若高权重方持续劣于对立方则作废。",
    )
    applicability = ApplicabilityPlan(
        task_school_weights={"strength": {"ziping": 0.8, "ditiansui": 0.4}},
        source="l1_capability",
    )

    result = arbitrate_staged("C-L6-002", [stronger, minority], applicability, conflict_rules=_rules(rule))
    decision = result.stage("structure")

    assert result.weight_source == "l1_capability"
    assert decision.result == "conflict_resolved"
    assert decision.conflict_type == "polarity_opposition"
    assert decision.resolution_rule_id == rule.rule_id
    assert decision.winner_claim_ids == ("stronger",)
    assert decision.minority_claim_ids == ("minority",)
    assert decision.weighted_support == pytest.approx(0.8)
    assert decision.weighted_oppose == pytest.approx(0.4)


def test_capability_gap_below_rule_threshold_is_unresolved_without_averaging() -> None:
    left = _claim("left", school_id="ziping", claim_type="structure_claim", task_id="strength", domain="总体", polarity="positive")
    right = _claim("right", school_id="ditiansui", claim_type="structure_claim", task_id="strength", domain="总体", polarity="negative")
    rule = ConflictRule(
        rule_id="CR-STRUCT-STRENGTH-001",
        applies_to_stage="structure",
        conflict_type="polarity_opposition",
        target_claim_type="structure_claim",
        resolution_strategy="capability_weighted",
        min_weight_gap=0.15,
        falsifier="盲测失效则作废。",
    )
    applicability = ApplicabilityPlan(
        task_school_weights={"strength": {"ziping": 0.55, "ditiansui": 0.5}},
        source="l1_capability",
    )

    decision = arbitrate_staged("C-L6-003", [left, right], applicability, conflict_rules=_rules(rule)).stage("structure")

    assert decision.result == "unresolved"
    assert decision.winner_claim_ids == ()
    assert set(decision.minority_claim_ids) == {"left", "right"}
    assert "平均" not in decision.rationale


def test_high_risk_conflict_is_conservatively_unresolved() -> None:
    occurs = _claim("occurs", school_id="yang_qingjuan", claim_type="event_claim", task_id="marriage.divorce", domain="婚姻", stance="support")
    stable = _claim("stable", school_id="ren_fuhong", claim_type="event_claim", task_id="marriage.divorce", domain="婚姻", stance="oppose")
    rule = ConflictRule(
        rule_id="CR-HIGH-RISK-001",
        applies_to_stage="event",
        conflict_type="occurrence_opposition",
        target_claim_type="event_claim",
        resolution_strategy="conservative_high_risk",
        min_weight_gap=0.0,
        falsifier="风险政策变更时复核。",
    )

    decision = arbitrate_staged(
        "C-L6-004",
        [occurs, stable],
        ApplicabilityPlan.uniform(),
        conflict_rules=_rules(rule),
    ).stage("event")

    assert decision.result == "unresolved"
    assert decision.resolution_rule_id == rule.rule_id
    assert set(decision.minority_claim_ids) == {"occurs", "stable"}
    assert "高风险" in decision.rationale


def test_three_stages_are_independent_and_missing_stage_returns_empty_decision() -> None:
    structure = _claim("structure", school_id="ziping", claim_type="structure_claim", task_id="strength", domain="总体")
    timing = _claim("timing", school_id="ren_fuhong", claim_type="timing_claim", task_id="career.window", domain="事业")

    result = arbitrate_staged("C-L6-005", [structure, timing], None, conflict_rules=ConflictRuleSet.empty())

    assert [item.stage for item in result.stages] == ["structure", "event", "timing"]
    assert result.stage("structure").winner_claim_ids == ("structure",)
    assert result.stage("event").result == "reject_all"
    assert result.stage("event").rejected_claim_ids == ()
    assert result.stage("timing").winner_claim_ids == ("timing",)
    assert result.weight_source == "uniform_fallback"


def test_structure_reject_all_caps_downstream_claims() -> None:
    rejected_structure = _claim(
        "bad-structure",
        school_id="ziping",
        claim_type="structure_claim",
        task_id="career.structure",
        domain="事业",
        confidence=0.05,
    )
    downstream = _claim(
        "career-event",
        school_id="duan_jianye",
        claim_type="event_claim",
        task_id="career.event",
        domain="事业",
        confidence=0.95,
    )

    result = arbitrate_staged(
        "C-L6-006",
        [rejected_structure, downstream],
        None,
        conflict_rules=ConflictRuleSet.empty(),
    )

    assert result.stage("structure").result == "reject_all"
    assert result.stage("event").result == "reject_all"
    assert result.stage("event").rejected_claim_ids == ("career-event",)
    assert "结构段" in result.stage("event").rationale


def test_default_yaml_rules_load_and_evidence_completeness_breaks_tie() -> None:
    rules = ConflictRuleSet.from_yaml("engine/decision/conflict-rules.yaml")
    sparse = _claim(
        "sparse",
        school_id="ziping",
        claim_type="structure_claim",
        task_id="structure.overview",
        domain="总体",
        polarity="positive",
        evidence_count=1,
    )
    complete = _claim(
        "complete",
        school_id="ditiansui",
        claim_type="structure_claim",
        task_id="structure.overview",
        domain="总体",
        polarity="negative",
        evidence_count=2,
    )

    decision = arbitrate_staged("C-L6-007", [sparse, complete], None, conflict_rules=rules).stage("structure")

    assert decision.result == "conflict_resolved"
    assert decision.winner_claim_ids == ("complete",)
    assert decision.minority_claim_ids == ("sparse",)
    assert decision.resolution_rule_id == "CR-STRUCT-EVIDENCE-001"


def test_default_rules_prioritize_domain_specific_high_risk_policy() -> None:
    occurs = _claim(
        "health-occurs",
        school_id="gao_dechen",
        claim_type="event_claim",
        task_id="health.severe",
        domain="健康",
        stance="support",
    )
    not_occurs = _claim(
        "health-not-occurs",
        school_id="ren_fuhong",
        claim_type="event_claim",
        task_id="health.severe",
        domain="健康",
        stance="oppose",
    )
    rules = ConflictRuleSet.from_yaml("engine/decision/conflict-rules.yaml")
    plan = ApplicabilityPlan(
        task_school_weights={"health.severe": {"gao_dechen": 0.95, "ren_fuhong": 0.2}},
        source="l1_capability",
    )

    decision = arbitrate_staged("C-L6-HIGH-RISK", [occurs, not_occurs], plan, conflict_rules=rules).stage("event")

    assert decision.result == "unresolved"
    assert decision.resolution_rule_id == "CR-EVENT-HIGH-RISK-001"
    assert "高风险" in decision.rationale


def test_old_and_staged_l6_can_run_side_by_side() -> None:
    event = EventHypothesis(
        event_id="legacy-event",
        source_verdict_ids=["verdict-1"],
        domain="事业",
        event_type="career_change",
        subject="命主",
        concrete_event="岗位变化",
        landing_path="工作环境调整",
        confidence=0.8,
    )
    claim = _claim(
        "new-claim",
        school_id="duan_jianye",
        claim_type="event_claim",
        task_id="career.change",
        domain="事业",
    )

    legacy = build_arbitration_decisions("C-L6-008", [event], [])
    staged = arbitrate_staged("C-L6-008", [claim], None, conflict_rules=ConflictRuleSet.empty())

    assert legacy[0].result == "winner"
    assert staged.stage("event").result == "winner"
    assert json.loads(json.dumps(staged.to_dict(), ensure_ascii=False))["case_id"] == "C-L6-008"
