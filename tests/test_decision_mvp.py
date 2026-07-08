from __future__ import annotations

from engine.decision import (
    build_arbitration_decisions,
    build_context_ledger,
    build_event_hypotheses,
    build_report_items,
    build_school_claims,
    build_structural_verdicts,
    build_timing_probabilities,
    route_schools,
    run_decision_mvp,
)
from engine.decision.models import (
    ArbitrationDecision,
    CalibrationAction,
    EventHypothesis,
    FeedbackAttribution,
    FeedbackSignal,
    SchoolClaim,
    TimingProbability,
)


def test_decision_mvp_builds_unbroken_l0_to_l7_trace() -> None:
    raw = """
$BASE
命式: 乾
公历: 1990-01-01 08:00
起运: 8岁
$FOUR
Y:庚午
M:戊寅
D:壬子
H:辛丑
$DY_LOOP
# 1998-2007 辛巳
> 2026 丙午
$KNOWN_FACTS
关注事业、财富、婚姻。
$FOCUS
事业与财富
$EXTRA
原样保留
""".strip()

    run = run_decision_mvp(raw)

    assert run.raw_payload.raw_hash == run.chart_ledger.raw_source_hash
    assert run.chart_ledger.four_pillars == {
        "year": "庚午",
        "month": "戊寅",
        "day": "壬子",
        "hour": "辛丑",
    }
    assert len(run.school_applicability) >= 6
    assert len(run.school_claims) >= 3
    assert len(run.structural_verdicts) >= 3
    assert len(run.event_hypotheses) >= 2
    assert len(run.timing_probabilities) >= 1
    assert len(run.arbitration_decisions) >= 1
    assert len(run.report_items) >= 1
    assert len(run.feedback_signals) == len(run.report_items)
    assert len(run.feedback_attributions) == len(run.feedback_signals)
    assert run.validate_trace() == []


def test_l2_to_l7_modules_are_composable() -> None:
    run = run_decision_mvp("""
$BASE
命式: 乾
$FOUR
Y:庚午
M:戊寅
D:壬子
H:辛丑
$DY_LOOP
# 1998-2007 辛巳
""".strip())

    claims = build_school_claims(run.case_id, run.school_applicability, run.chart_ledger)
    verdicts = build_structural_verdicts(run.case_id, claims)
    events = build_event_hypotheses(run.case_id, verdicts, claims)
    timings = build_timing_probabilities(run.case_id, events)
    decisions = build_arbitration_decisions(run.case_id, events, run.school_applicability)
    report_items = build_report_items(run.case_id, decisions, timings)

    assert claims
    assert verdicts
    assert events
    assert timings
    assert decisions
    assert report_items


def test_decision_mvp_records_missing_fields_without_judging() -> None:
    raw = """
$BASE
命式: _
$FOUR
Y:甲子
M:_
D:丙寅
H:丁卯
$DY_LOOP
# _
""".strip()

    run = run_decision_mvp(raw)

    assert "$BASE.命式" in run.chart_ledger.missing_fields
    assert "$FOUR.month" in run.chart_ledger.missing_fields
    assert "$DY_LOOP.1" in run.chart_ledger.missing_fields
    assert run.validate_trace() == []


def test_l0_context_ledger_keeps_free_text_out_of_chart_facts() -> None:
    context = build_context_ledger(
        {"KNOWN_FACTS": "已知事业变化", "FOCUS": "事业", "EXTRA": "原文保留"},
        ["EXTRA"],
    )

    assert context.known_fact_text == "已知事业变化"
    assert context.analysis_focus_text == "事业"
    assert context.preserved_text_blocks == ["$EXTRA\n原文保留"]


def test_l1_router_assigns_roles_and_abstains_irrelevant_schools() -> None:
    run = run_decision_mvp("""
$BASE
命式: 乾
$FOUR
Y:庚午
M:戊寅
D:壬子
H:辛丑
$DY_LOOP
# 1998-2007 辛巳
$FOCUS
事业
""".strip())

    routed = {item.school: item for item in route_schools(run.chart_ledger, run.context_ledger)}

    assert routed["ziping"].role == "lead"
    assert routed["ditiansui"].role == "lead"
    assert routed["duan_jianye"].role == "co_lead"
    assert routed["gao_dechen"].role == "abstain"
    assert routed["gao_dechen"].blockers
    assert all(item.reasons for item in routed.values())


def test_l3_structure_can_reject_very_low_confidence_claim() -> None:
    verdict = build_structural_verdicts(
        "C-TEST",
        [
            SchoolClaim(
                claim_id="claim-low",
                school="ziping",
                role_granted_by_l1="lead",
                domain="事业",
                claim_type="structure",
                statement="低置信结构命题",
                confidence=0.05,
            )
        ],
    )[0]

    assert verdict.verdict == "reject"
    assert verdict.blocking_factors


def test_l3_marks_evidence_claim_as_unknown_not_structural_weaken() -> None:
    verdict = build_structural_verdicts(
        "C-TEST",
        [
            SchoolClaim(
                claim_id="claim-evidence",
                school="gao_dechen",
                role_granted_by_l1="evidence_only",
                domain="健康",
                claim_type="evidence",
                statement="旁证命题只提供补强材料。",
                confidence=0.8,
            )
        ],
    )[0]

    assert verdict.verdict == "unknown"
    assert "旁证" in verdict.structural_reason



def test_l5_probability_range_follows_event_confidence() -> None:
    base = dict(
        source_verdict_ids=["v1"],
        domain="事业",
        event_type="test",
        subject="test",
        concrete_event="test",
        landing_path="test",
    )

    low = EventHypothesis(event_id="e-low", confidence=0.2, **base)
    mid = EventHypothesis(event_id="e-mid", confidence=0.5, **base)
    high = EventHypothesis(event_id="e-high", confidence=0.7, **base)

    timings = build_timing_probabilities("C-TEST", [low, mid, high])

    assert [item.probability_range for item in timings] == [(0.1, 0.3), (0.3, 0.6), (0.6, 0.8)]
    assert [item.event_id for item in timings] == ["e-low", "e-mid", "e-high"]



def test_l6_arbitration_supports_non_winner_results() -> None:
    base = dict(
        source_verdict_ids=["v1"],
        domain="事业",
        event_type="test",
        subject="test",
        concrete_event="test",
        landing_path="test",
    )

    coexist = build_arbitration_decisions(
        "C-TEST",
        [EventHypothesis(event_id="e1", confidence=0.5, **base), EventHypothesis(event_id="e2", confidence=0.53, **base)],
        [],
    )[0]
    unresolved = build_arbitration_decisions(
        "C-TEST",
        [EventHypothesis(event_id="e1", confidence=0.8, **base), EventHypothesis(event_id="e2", confidence=0.2, **base)],
        [],
    )[0]
    rejected = build_arbitration_decisions(
        "C-TEST",
        [EventHypothesis(event_id="e1", confidence=0.05, **base), EventHypothesis(event_id="e2", confidence=0.1, **base)],
        [],
    )[0]

    assert coexist.result == "coexist"
    assert unresolved.result == "unresolved"
    assert rejected.result == "reject_all"


def test_l4_does_not_turn_evidence_only_claim_into_event() -> None:
    evidence_claim = SchoolClaim(
        claim_id="claim-evidence",
        school="gao_dechen",
        role_granted_by_l1="evidence_only",
        domain="健康",
        claim_type="evidence",
        statement="神煞旁证只能补强，不能单独落成事件。",
        confidence=0.8,
    )

    events = build_event_hypotheses("C-TEST", [], [evidence_claim])

    assert events == []



def test_l4_fallback_does_not_turn_evidence_verdict_into_event() -> None:
    evidence_claim = SchoolClaim(
        claim_id="claim-evidence",
        school="gao_dechen",
        role_granted_by_l1="evidence_only",
        domain="健康",
        claim_type="evidence",
        statement="旁证只作为补强材料。",
        confidence=0.8,
    )
    verdicts = build_structural_verdicts("C-TEST", [evidence_claim])

    events = build_event_hypotheses("C-TEST", verdicts, [evidence_claim])

    assert events == []



def test_l7_report_items_follow_each_arbitration_decision_and_matching_timing() -> None:
    decision_a = ArbitrationDecision(
        decision_id="d-a",
        domain="事业",
        competing_event_ids=["e-a"],
        result="winner",
        winner_ids=["e-a"],
    )
    decision_b = ArbitrationDecision(
        decision_id="d-b",
        domain="财富",
        competing_event_ids=["e-b"],
        result="winner",
        winner_ids=["e-b"],
    )
    timing_b = TimingProbability(prediction_id="t-b", event_id="e-b")
    timing_a = TimingProbability(prediction_id="t-a", event_id="e-a")

    items = build_report_items("C-TEST", [decision_a, decision_b], [timing_b, timing_a])

    assert [item.decision_id for item in items] == ["d-a", "d-b"]
    assert [item.prediction_id for item in items] == ["t-a", "t-b"]
    assert all(item.display_text for item in items)



def test_decision_run_validate_trace_checks_l8_l9_links() -> None:
    run = run_decision_mvp("""
$BASE
命式: 乾
$FOUR
Y:庚午
M:戊寅
D:壬子
H:辛丑
$DY_LOOP
# 1998-2007 辛巳
""".strip())

    broken_feedback = FeedbackSignal(feedback_id="fb-broken", report_item_id="missing-report", verdict="unknown")
    broken_attr = FeedbackAttribution(
        attribution_id="attr-broken",
        feedback_id="missing-feedback",
        affected_layer="L8",
        affected_object_id="x",
        attribution_reason="test",
    )
    broken_action = CalibrationAction(
        action_id="cal-broken",
        target_type="report_policy",
        target_id="x",
        action="review",
        reason="test",
        evidence_feedback_ids=["missing-feedback"],
    )
    patched = type(run)(
        **{
            **run.__dict__,
            "feedback_signals": [broken_feedback],
            "feedback_attributions": [broken_attr],
            "calibration_actions": [broken_action],
        }
    )

    issues = patched.validate_trace()

    assert any("L8 feedback signal" in issue for issue in issues)
    assert any("L8 attribution" in issue for issue in issues)
    assert any("L9 calibration action" in issue for issue in issues)
