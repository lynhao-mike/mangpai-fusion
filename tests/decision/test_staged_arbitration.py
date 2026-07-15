from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from engine.claims import Claim, Evidence, TimeWindow
from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindTask
from engine.features import build_chart_feature_vector
from engine.v5.ren_runner import generate_claims as generate_ren_claims
from engine.v5.ziping_runner import generate_claims as generate_ziping_claims
from engine.decision.l6_arbitration import build_arbitration_decisions
from engine.decision.l1_school_router import PrototypeAssignment, RoutePlan, TaskRoute
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
    high_risk: bool = False,
    target_id: str | None = None,
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
        high_risk=high_risk,
        target_id=target_id or task_id.split(".", 1)[0],
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
        high_risk=True,
    )
    not_occurs = _claim(
        "health-not-occurs",
        school_id="ren_fuhong",
        claim_type="event_claim",
        task_id="health.severe",
        domain="健康",
        stance="oppose",
        high_risk=True,
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


def test_route_plan_is_consumed_without_test_only_adapter() -> None:
    route = TaskRoute(
        task_id="strength",
        primary_schools=("ziping",),
        counter_school="ditiansui",
        abstain_candidates=(),
        unsupported_schools=(),
        evidence_status="sufficient",
        rationale="fixture",
        school_scores={"ziping": 0.82, "ditiansui": 0.4},
    )
    plan = RoutePlan(
        primary_schools=("ziping",),
        counter_school="ditiansui",
        abstain_candidates=(),
        unsupported_schools=(),
        route_rationale="fixture",
        capability_snapshot_id="cap-v1",
        prototype_assignment=PrototypeAssignment("balanced", (), 0.8, ()),
        per_task_routes={"strength": route},
    )
    claims = [
        _claim("route-winner", school_id="ziping", claim_type="structure_claim", task_id="strength", domain="总体", polarity="positive"),
        _claim("route-minority", school_id="ditiansui", claim_type="structure_claim", task_id="strength", domain="总体", polarity="negative"),
    ]
    rule = ConflictRule("CR-ROUTE", "structure", "polarity_opposition", "structure_claim", "capability_weighted", 0.15, "失验则作废")

    result = arbitrate_staged("C-L6-ROUTE", claims, plan, conflict_rules=_rules(rule))

    assert result.weight_source == "l1_capability"
    assert result.stage("structure").winner_claim_ids == ("route-winner",)


def test_structure_precedence_is_domain_scoped() -> None:
    claims = [
        _claim("career-structure-bad", school_id="ziping", claim_type="structure_claim", task_id="career.structure", domain="事业", confidence=0.05),
        _claim("health-structure-good", school_id="ditiansui", claim_type="structure_claim", task_id="health.structure", domain="健康"),
        _claim("career-event", school_id="duan_jianye", claim_type="event_claim", task_id="career.event", domain="事业"),
        _claim("health-event", school_id="gao_dechen", claim_type="event_claim", task_id="health.event", domain="健康"),
    ]

    result = arbitrate_staged("C-L6-DOMAIN", claims, None, conflict_rules=ConflictRuleSet.empty())
    event_by_domain = {item.domain: item for item in result.stage("event").domain_decisions}

    assert event_by_domain["事业"].result == "reject_all"
    assert event_by_domain["事业"].rejected_claim_ids == ("career-event",)
    assert event_by_domain["健康"].result == "winner"
    assert event_by_domain["健康"].winner_claim_ids == ("health-event",)


def test_multiple_domains_resolved_by_different_rules_round_trip_without_losing_rule_ids() -> None:
    claims = [
        _claim("career-pos", school_id="ziping", claim_type="structure_claim", task_id="career.structure", domain="事业", polarity="positive", evidence_count=2),
        _claim("career-neg", school_id="ditiansui", claim_type="structure_claim", task_id="career.structure", domain="事业", polarity="negative"),
        _claim("health-pos", school_id="gao_dechen", claim_type="structure_claim", task_id="health.structure", domain="健康", polarity="positive"),
        _claim("health-neg", school_id="ditiansui", claim_type="structure_claim", task_id="health.structure", domain="健康", polarity="negative", evidence_count=2),
    ]
    rules = _rules(
        ConflictRule("CR-CAREER", "structure", "polarity_opposition", "structure_claim", "evidence_completeness", 0.0, "失验则作废", domains=("事业",)),
        ConflictRule("CR-HEALTH", "structure", "polarity_opposition", "structure_claim", "evidence_completeness", 0.0, "失验则作废", domains=("健康",)),
    )

    result = arbitrate_staged("C-L6-MULTI", claims, None, conflict_rules=rules)
    restored = StagedArbitrationResult.from_dict(result.to_dict())
    decisions = restored.stage("structure").domain_decisions

    assert {item.resolution_rule_id for item in decisions} == {"CR-CAREER", "CR-HEALTH"}
    assert all(item.result == "conflict_resolved" for item in decisions)


def test_structure_precedence_strategy_uses_same_domain_structure_winner() -> None:
    structure = _claim("structure-positive", school_id="ziping", claim_type="structure_claim", task_id="career.direction", domain="事业", polarity="positive")
    event_positive = _claim("event-positive", school_id="duan_jianye", claim_type="event_claim", task_id="career.direction", domain="事业", polarity="positive")
    event_negative = _claim("event-negative", school_id="ditiansui", claim_type="event_claim", task_id="career.direction", domain="事业", polarity="negative")
    rule = ConflictRule("CR-PRECEDENCE", "event", "polarity_opposition", "event_claim", "structure_precedence", 0.0, "结构失验则作废")

    decision = arbitrate_staged("C-L6-PRECEDENCE", [structure, event_positive, event_negative], None, conflict_rules=_rules(rule)).stage("event")

    assert decision.result == "conflict_resolved"
    assert decision.winner_claim_ids == ("event-positive",)
    assert decision.resolution_rule_id == "CR-PRECEDENCE"


def test_high_risk_major_loss_requires_overwhelming_weight_gap() -> None:
    occurs = _claim("loss", school_id="ren", claim_type="event_claim", task_id="wealth.major_loss", domain="财富", stance="support", high_risk=True)
    safe = _claim("safe", school_id="ziping", claim_type="event_claim", task_id="wealth.major_loss", domain="财富", stance="oppose", high_risk=True)
    rule = ConflictRule(
        "CR-HIGH-RISK-LOSS", "event", "occurrence_opposition", "event_claim",
        "conservative_high_risk", 0.6, "风险政策变化则复核", high_risk_only=True,
    )

    unresolved = arbitrate_staged(
        "C-L6-LOSS-HOLD", [occurs, safe],
        ApplicabilityPlan({"wealth.major_loss": {"ren": 0.8, "ziping": 0.4}}),
        conflict_rules=_rules(rule),
    ).stage("event")
    resolved = arbitrate_staged(
        "C-L6-LOSS-GO", [occurs, safe],
        ApplicabilityPlan({"wealth.major_loss": {"ren": 1.0, "ziping": 0.2}}),
        conflict_rules=_rules(rule),
    ).stage("event")

    assert unresolved.result == "unresolved"
    assert resolved.result == "conflict_resolved"
    assert resolved.winner_claim_ids == ("loss",)


def test_result_can_be_persisted_and_loaded_from_json_file(tmp_path: Path) -> None:
    result = arbitrate_staged(
        "C-L6-FILE",
        [_claim("persisted", school_id="ziping", claim_type="structure_claim", task_id="strength", domain="总体")],
        None,
        conflict_rules=ConflictRuleSet.empty(),
    )
    path = tmp_path / "staged-arbitration.json"

    result.save_json(path)
    restored = StagedArbitrationResult.load_json(path)

    assert restored == result


def test_real_l2_runners_emit_arbitration_fields_and_feed_l6() -> None:
    chart = ChartFactLedger(
        sex_marker="乾",
        four_pillars={"year": "庚申", "month": "庚申", "day": "甲午", "hour": "辛酉"},
        dayun_steps=[{"ganzhi": "丙辰", "start_year": 2018, "end_year": 2027}],
        liunian_steps=[{"year": 2026, "ganzhi": "丙午", "dayun": "丙辰"}],
    )
    features = build_chart_feature_vector(chart)
    structure_task = BlindTask(
        task_id="structure.overview", domain="总体", claim_type="structure", scoring_method="portrait_agreement",
        quantifiable=False, high_risk=False, allowed_time_horizons=["lifetime"],
        required_input_fields=["four_pillars"], label_schema={}, evaluation_note="fixture",
    )
    timing_task = BlindTask(
        task_id="health.event_window", domain="健康", claim_type="event_timing", scoring_method="time_window",
        quantifiable=True, high_risk=True, allowed_time_horizons=["annual"],
        required_input_fields=["four_pillars", "liunian_steps"],
        label_schema={"type": "object"}, evaluation_note="fixture",
    )

    claims = generate_ziping_claims(chart, features, structure_task) + generate_ren_claims(chart, features, timing_task)
    result = arbitrate_staged("C-L6-REAL", claims, None, conflict_rules=ConflictRuleSet.empty())

    assert claims
    assert all(claim.domain and 0.0 <= claim.confidence <= 1.0 for claim in claims)
    assert any(claim.high_risk and claim.domain == "健康" for claim in claims)
    assert result.stage("structure").winner_claim_ids or result.stage("structure").result == "coexist"
    assert result.stage("timing").winner_claim_ids


def test_same_domain_multiple_tasks_are_arbitrated_independently() -> None:
    claims = [
        _claim("role-yes", school_id="ren", claim_type="event_claim", task_id="career.role", domain="事业", stance="support"),
        _claim("role-no", school_id="ziping", claim_type="event_claim", task_id="career.role", domain="事业", stance="oppose"),
        _claim("promotion-yes", school_id="duan_jianye", claim_type="event_claim", task_id="career.promotion", domain="事业", stance="support"),
        _claim("promotion-no", school_id="ditiansui", claim_type="event_claim", task_id="career.promotion", domain="事业", stance="oppose"),
    ]
    rule = ConflictRule("CR-MULTI-TASK", "event", "occurrence_opposition", "event_claim", "capability_weighted", 0.15, "失验则作废")
    plan = ApplicabilityPlan({
        "career.role": {"ren": 0.8, "ziping": 0.4},
        "career.promotion": {"duan_jianye": 0.3, "ditiansui": 0.8},
    })

    result = arbitrate_staged("C-L6-MULTI-TASK", claims, plan, conflict_rules=_rules(rule))
    leaves = result.stage("event").domain_decisions

    assert len(leaves) == 2
    assert {item.winner_claim_ids for item in leaves} == {("role-yes",), ("promotion-no",)}


def test_structure_precedence_uses_structured_winner_side_after_structure_conflict() -> None:
    claims = [
        _claim("structure-pos", school_id="ziping", claim_type="structure_claim", task_id="career.direction", domain="事业", polarity="positive", evidence_count=2),
        _claim("structure-neg", school_id="ditiansui", claim_type="structure_claim", task_id="career.direction", domain="事业", polarity="negative"),
        _claim("event-pos", school_id="duan_jianye", claim_type="event_claim", task_id="career.direction", domain="事业", polarity="positive"),
        _claim("event-neg", school_id="ren", claim_type="event_claim", task_id="career.direction", domain="事业", polarity="negative"),
    ]
    rules = _rules(
        ConflictRule("CR-STRUCT-WINNER", "structure", "polarity_opposition", "structure_claim", "evidence_completeness", 0.0, "失验则作废"),
        ConflictRule("CR-EVENT-PRECEDENCE", "event", "polarity_opposition", "event_claim", "structure_precedence", 0.0, "失验则作废"),
    )

    decision = arbitrate_staged("C-L6-STRUCT-WINNER", claims, None, conflict_rules=rules).stage("event")

    assert decision.result == "conflict_resolved"
    assert decision.winner_claim_ids == ("event-pos",)


def test_partial_l1_weights_fall_back_uniform_and_are_marked() -> None:
    claims = [
        _claim("known", school_id="ziping", claim_type="structure_claim", task_id="strength", domain="总体", polarity="positive"),
        _claim("missing", school_id="ditiansui", claim_type="structure_claim", task_id="strength", domain="总体", polarity="negative"),
    ]
    rule = ConflictRule("CR-PARTIAL", "structure", "polarity_opposition", "structure_claim", "capability_weighted", 0.15, "失验则作废")

    result = arbitrate_staged("C-L6-PARTIAL", claims, ApplicabilityPlan({"strength": {"ziping": 0.9}}), conflict_rules=_rules(rule))

    assert result.weight_source == "uniform_fallback"
    assert result.stage("structure").result == "unresolved"


def test_uniform_high_risk_majority_cannot_masquerade_as_overwhelming_capability() -> None:
    claims = [
        _claim("risk-a", school_id="ren", claim_type="event_claim", task_id="health.event", domain="健康", stance="support", high_risk=True),
        _claim("risk-b", school_id="gao", claim_type="event_claim", task_id="health.event", domain="健康", stance="support", high_risk=True),
        _claim("safe", school_id="ziping", claim_type="event_claim", task_id="health.event", domain="健康", stance="oppose", high_risk=True),
    ]
    rule = ConflictRule("CR-HIGH-UNIFORM", "event", "occurrence_opposition", "event_claim", "conservative_high_risk", 0.6, "风险政策变更则复核", high_risk_only=True)

    decision = arbitrate_staged("C-L6-HIGH-UNIFORM", claims, None, conflict_rules=_rules(rule)).stage("event")

    assert decision.result == "unresolved"


def test_default_rules_conservatively_hold_high_risk_timing_conflict() -> None:
    claims = [
        _claim("timing-risk", school_id="ren", claim_type="timing_claim", task_id="wealth.major_loss_window", domain="财富", stance="support", high_risk=True),
        _claim("timing-safe", school_id="ziping", claim_type="timing_claim", task_id="wealth.major_loss_window", domain="财富", stance="oppose", high_risk=True),
    ]

    decision = arbitrate_staged(
        "C-L6-HIGH-TIMING", claims, None,
        conflict_rules=ConflictRuleSet.from_yaml("engine/decision/conflict-rules.yaml"),
    ).stage("timing")

    assert decision.result == "unresolved"
    assert decision.resolution_rule_id == "CR-TIMING-HIGH-RISK-001"


def test_structure_rejection_only_propagates_to_matching_target() -> None:
    claims = [
        _claim("role-structure-bad", school_id="ziping", claim_type="structure_claim", task_id="career.role.structure", target_id="career-role", domain="事业", confidence=0.05),
        _claim("role-event", school_id="ren", claim_type="event_claim", task_id="career.role.event", target_id="career-role", domain="事业"),
        _claim("promotion-event", school_id="duan_jianye", claim_type="event_claim", task_id="career.promotion", target_id="career-promotion", domain="事业"),
    ]

    result = arbitrate_staged("C-L6-TARGET", claims, None, conflict_rules=ConflictRuleSet.empty())
    leaves = {item.target_id: item for item in result.stage("event").domain_decisions}

    assert leaves["career-role"].result == "reject_all"
    assert leaves["career-promotion"].result == "winner"


def test_conflict_decision_preserves_low_confidence_rejections() -> None:
    claims = [
        _claim("yes", school_id="ren", claim_type="event_claim", task_id="career.role", domain="事业", stance="support"),
        _claim("no", school_id="ziping", claim_type="event_claim", task_id="career.role", domain="事业", stance="oppose"),
        _claim("too-low", school_id="gao", claim_type="event_claim", task_id="career.role", domain="事业", confidence=0.05),
    ]
    rule = ConflictRule("CR-REJECTED", "event", "occurrence_opposition", "event_claim", "capability_weighted", 0.15, "失验则作废")
    plan = ApplicabilityPlan({"career.role": {"ren": 0.8, "ziping": 0.4, "gao": 0.1}})

    decision = arbitrate_staged("C-L6-REJECTED", claims, plan, conflict_rules=_rules(rule)).stage("event")

    assert decision.rejected_claim_ids == ("too-low",)


def test_claim_rejects_non_boolean_high_risk() -> None:
    with pytest.raises(ValueError, match="high_risk"):
        replace(_claim("risk", school_id="ren", claim_type="event_claim", task_id="health.event", domain="健康"), high_risk="yes")


def test_high_risk_magnitude_conflict_uses_default_conservative_guard() -> None:
    claims = [
        _claim("light", school_id="ziping", claim_type="event_claim", task_id="health.loss", domain="健康", magnitude=0.2, high_risk=True),
        _claim("heavy", school_id="gao", claim_type="event_claim", task_id="health.loss", domain="健康", magnitude=0.9, high_risk=True),
    ]
    ordinary = ConflictRule("GEN-MAG", "event", "magnitude_opposition", "event_claim", "capability_weighted", 0.15, "失验则作废")

    decision = arbitrate_staged(
        "C-L6-HIGH-MAG", claims,
        ApplicabilityPlan({"health.loss": {"ziping": 0.2, "gao": 0.9}}),
        conflict_rules=_rules(ordinary),
    ).stage("event")

    assert decision.result == "unresolved"
    assert decision.resolution_rule_id.startswith("CR-HIGH-RISK-DEFAULT-")


def test_multi_task_stage_summary_does_not_invent_rule_id() -> None:
    claims = [
        _claim("role-pos", school_id="ziping", claim_type="structure_claim", task_id="career.role", domain="事业", polarity="positive", evidence_count=2),
        _claim("role-neg", school_id="ren", claim_type="structure_claim", task_id="career.role", domain="事业", polarity="negative"),
        _claim("promotion-pos", school_id="duan", claim_type="structure_claim", task_id="career.promotion", domain="事业", polarity="positive", evidence_count=2),
        _claim("promotion-neg", school_id="ditiansui", claim_type="structure_claim", task_id="career.promotion", domain="事业", polarity="negative"),
    ]
    rule = ConflictRule("CR-REAL", "structure", "polarity_opposition", "structure_claim", "evidence_completeness", 0.0, "失验则作废")

    stage = arbitrate_staged("C-L6-SUMMARY", claims, None, conflict_rules=_rules(rule)).stage("structure")

    assert stage.resolution_rule_id is None
    assert {item.resolution_rule_id for item in stage.domain_decisions} == {"CR-REAL"}


def test_conflict_rule_rejects_non_boolean_high_risk_only() -> None:
    with pytest.raises(ValueError, match="high_risk_only"):
        ConflictRule.from_dict({
            "rule_id": "CR-BAD-BOOL",
            "applies_to_stage": "event",
            "conflict_type": "occurrence_opposition",
            "target_claim_type": "event_claim",
            "resolution_strategy": "conservative_high_risk",
            "min_weight_gap": 0.8,
            "falsifier": "fixture",
            "high_risk_only": "false",
        })


def test_conflict_rule_direct_constructor_rejects_non_boolean_high_risk_only() -> None:
    with pytest.raises(ValueError, match="high_risk_only"):
        ConflictRule(
            "CR-BAD-DIRECT", "event", "occurrence_opposition", "event_claim",
            "conservative_high_risk", 0.8, "fixture", high_risk_only="false",
        )


def test_same_task_different_targets_are_not_collided() -> None:
    claims = [
        _claim("target-a", school_id="ren", claim_type="event_claim", task_id="career.change", target_id="role-a", domain="事业", stance="support"),
        _claim("target-b", school_id="ziping", claim_type="event_claim", task_id="career.change", target_id="role-b", domain="事业", stance="oppose"),
    ]

    stage = arbitrate_staged("C-L6-DIFFERENT-TARGETS", claims, None, conflict_rules=ConflictRuleSet.empty()).stage("event")

    assert len(stage.domain_decisions) == 2
    assert {item.target_id for item in stage.domain_decisions} == {"role-a", "role-b"}
    assert all(item.result == "winner" for item in stage.domain_decisions)
