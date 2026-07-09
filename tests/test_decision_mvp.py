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
    ReportViewItem,
    SchoolClaim,
    StructuralVerdict,
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


def test_l0_records_child_missing_fields_when_required_sections_are_absent() -> None:
    run = run_decision_mvp("")

    assert "$BASE" in run.chart_ledger.missing_fields
    assert "$BASE.命式" in run.chart_ledger.missing_fields
    assert "$FOUR" in run.chart_ledger.missing_fields
    assert "$FOUR.Y" in run.chart_ledger.missing_fields
    assert "$FOUR.M" in run.chart_ledger.missing_fields
    assert "$FOUR.D" in run.chart_ledger.missing_fields
    assert "$FOUR.H" in run.chart_ledger.missing_fields
    assert "$DY_LOOP" in run.chart_ledger.missing_fields



def test_l0_treats_empty_base_and_four_values_as_missing() -> None:
    run = run_decision_mvp("""
$BASE
命式:
$FOUR
Y:
M:乙丑
D:丙寅
H:丁卯
$DY_LOOP
# 1998-2007 辛巳
""".strip())

    assert "$BASE.命式" in run.chart_ledger.missing_fields
    assert "$FOUR.year" in run.chart_ledger.missing_fields



def test_l0_context_strips_known_facts_and_focus_text() -> None:
    context = build_context_ledger(
        {"KNOWN_FACTS": "  已知事业变化  ", "FOCUS": "  事业  "},
        [],
    )

    assert context.known_fact_text == "已知事业变化"
    assert context.analysis_focus_text == "事业"



def test_l0_preserves_captured_at_on_raw_payload() -> None:
    from engine.decision import parse_wenzhen_l0

    payload, _, _ = parse_wenzhen_l0("", captured_at="2026-07-09T00:00:00Z")

    assert payload.captured_at == "2026-07-09T00:00:00Z"



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
    assert routed["duan_jianye"].role in {"co_lead", "lead"}
    assert routed["gao_dechen"].role == "abstain"
    assert routed["gao_dechen"].blockers
    assert all(item.reasons for item in routed.values())


def test_l1_incomplete_four_pillars_downgrades_non_abstain_schools_to_evidence_only() -> None:
    from engine.decision.models import ChartFactLedger, ContextFactLedger

    routed = route_schools(
        ChartFactLedger(four_pillars={"year": "甲子", "month": "_", "day": "丙寅", "hour": "丁卯"}),
        ContextFactLedger(analysis_focus_text="事业"),
    )

    assert all(item.role in {"evidence_only", "abstain"} for item in routed)
    assert any(item.role == "evidence_only" for item in routed)



def test_l1_focus_domains_understands_health_synonyms() -> None:
    from engine.decision.models import ChartFactLedger, ContextFactLedger

    routed = {item.school: item for item in route_schools(
        ChartFactLedger(four_pillars={"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"}),
        ContextFactLedger(analysis_focus_text="身体疾病"),
    )}

    assert routed["ren_fuhong"].role != "abstain"



def test_l2_skips_unknown_school_profile() -> None:
    from engine.decision.models import ChartFactLedger, SchoolApplicability

    claims = build_school_claims(
        "C-TEST",
        [SchoolApplicability(school="unknown_school", role="co_lead", applicable_domains=["事业"])],  # type: ignore[arg-type]
        ChartFactLedger(four_pillars={"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"}),
    )

    assert claims == []



def test_l3_reject_confidence_stays_low() -> None:
    verdict = build_structural_verdicts(
        "C-TEST",
        [
            SchoolClaim(
                claim_id="claim-low-confidence",
                school="ziping",
                role_granted_by_l1="lead",
                domain="事业",
                claim_type="structure",
                statement="极低置信结构命题。",
                confidence=0.05,
            )
        ],
    )[0]

    assert verdict.verdict == "reject"
    assert verdict.confidence <= 0.1



def test_l2_evidence_only_role_does_not_emit_structure_claim() -> None:
    from engine.decision.models import ChartFactLedger, SchoolApplicability

    claims = build_school_claims(
        "C-TEST",
        [
            SchoolApplicability(
                school="ziping",
                role="evidence_only",
                applicable_domains=["事业"],
                applicability_score=0.35,
            )
        ],
        ChartFactLedger(four_pillars={"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"}),
    )

    assert len(claims) == 1
    assert claims[0].claim_type == "evidence"
    assert "旁证" in claims[0].statement



def test_l2_evidence_only_role_does_not_emit_timing_claim() -> None:
    from engine.decision.models import ChartFactLedger, SchoolApplicability

    claims = build_school_claims(
        "C-TEST",
        [
            SchoolApplicability(
                school="ren_fuhong",
                role="evidence_only",
                applicable_domains=["应期"],
                applicability_score=0.35,
            )
        ],
        ChartFactLedger(four_pillars={"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"}),
    )

    assert len(claims) == 1
    assert claims[0].claim_type == "evidence"
    assert "旁证" in claims[0].statement



def test_l2_evidence_only_role_does_not_emit_event_claim() -> None:
    from engine.decision.models import ChartFactLedger, SchoolApplicability

    claims = build_school_claims(
        "C-TEST",
        [
            SchoolApplicability(
                school="duan_jianye",
                role="evidence_only",
                applicable_domains=["事业"],
                applicability_score=0.4,
            )
        ],
        ChartFactLedger(four_pillars={"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"}),
    )

    assert len(claims) == 1
    assert claims[0].claim_type == "evidence"
    assert "旁证" in claims[0].statement



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


def test_l6_arbitration_groups_events_by_domain() -> None:
    base = dict(
        source_verdict_ids=["v1"],
        event_type="test",
        subject="test",
        concrete_event="test",
        landing_path="test",
        confidence=0.6,
    )

    decisions = build_arbitration_decisions(
        "C-TEST",
        [
            EventHypothesis(event_id="career", domain="事业", **base),
            EventHypothesis(event_id="wealth", domain="财富", **base),
        ],
        [],
    )

    assert [item.domain for item in decisions] == ["事业", "财富"]
    assert [item.competing_event_ids for item in decisions] == [["career"], ["wealth"]]



def test_l4_event_claim_uses_only_same_domain_structural_support() -> None:
    career_claim = SchoolClaim(
        claim_id="claim-career-event",
        school="duan_jianye",
        role_granted_by_l1="co_lead",
        domain="事业",
        claim_type="event",
        statement="事业事件命题。",
        confidence=0.7,
    )
    health_structure = SchoolClaim(
        claim_id="claim-health-structure",
        school="ditiansui",
        role_granted_by_l1="lead",
        domain="健康",
        claim_type="structure",
        statement="健康结构命题。",
        confidence=0.7,
    )
    verdict = build_structural_verdicts("C-TEST", [health_structure])[0]

    assert build_event_hypotheses("C-TEST", [verdict], [career_claim, health_structure]) == []



def test_decision_run_validate_trace_checks_required_ids_and_domains() -> None:
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
    patched = type(run)(
        **{
            **run.__dict__,
            "school_applicability": [type(run.school_applicability[0])(**{**run.school_applicability[0].__dict__, "school": ""})],
            "school_claims": [type(run.school_claims[0])(**{**run.school_claims[0].__dict__, "claim_id": ""})],
            "event_hypotheses": [type(run.event_hypotheses[0])(**{**run.event_hypotheses[0].__dict__, "event_id": "", "domain": ""})],
            "timing_probabilities": [type(run.timing_probabilities[0])(**{**run.timing_probabilities[0].__dict__, "prediction_id": ""})],
            "arbitration_decisions": [],
            "report_items": [],
            "feedback_signals": [],
            "feedback_attributions": [],
            "calibration_actions": [],
        }
    )

    issues = patched.validate_trace()

    assert any("L1 school_applicability 缺少 school" in issue for issue in issues)
    assert any("L2 claim 缺少 claim_id" in issue for issue in issues)
    assert any("L4 event 缺少 event_id" in issue for issue in issues)
    assert any("L4 event 缺少 domain" in issue for issue in issues)
    assert any("L5 timing 缺少 prediction_id" in issue for issue in issues)



def test_l5_skips_event_without_event_id() -> None:
    event = EventHypothesis(
        event_id="",
        source_verdict_ids=["v1"],
        domain="事业",
        event_type="test",
        subject="test",
        concrete_event="test",
        landing_path="test",
        confidence=0.5,
    )

    assert build_timing_probabilities("C-TEST", [event]) == []



def test_l6_skips_events_without_domain() -> None:
    event = EventHypothesis(
        event_id="event-no-domain",
        source_verdict_ids=["v1"],
        domain="",
        event_type="test",
        subject="test",
        concrete_event="test",
        landing_path="test",
        confidence=0.5,
    )

    assert build_arbitration_decisions("C-TEST", [event], []) == []



def test_l4_requires_passed_or_weakened_verdict_for_event_claim() -> None:
    event_claim = SchoolClaim(
        claim_id="claim-event",
        school="duan_jianye",
        role_granted_by_l1="co_lead",
        domain="事业",
        claim_type="event",
        statement="事业事件命题。",
        confidence=0.7,
    )
    rejected = StructuralVerdict(
        verdict_id="verdict-reject",
        claim_id="claim-event",
        verdict="reject",
        structural_reason="结构不成立。",
    )

    assert build_event_hypotheses("C-TEST", [], [event_claim]) == []
    assert build_event_hypotheses("C-TEST", [rejected], [event_claim]) == []



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



def test_decision_run_validate_trace_checks_required_run_and_l9_ids() -> None:
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
    feedback = FeedbackSignal(feedback_id="fb-action", report_item_id=run.report_items[0].report_item_id, verdict="miss")
    attribution = FeedbackAttribution(
        attribution_id="attr-action",
        feedback_id="fb-action",
        affected_layer="L6",
        affected_object_id=feedback.report_item_id,
        attribution_reason="test",
        requires_human_review=True,
    )
    action = CalibrationAction(
        action_id="",
        target_type="arbitration_policy",
        target_id="",
        action="review",
        reason="test",
        evidence_feedback_ids=["fb-action"],
    )
    patched = type(run)(
        **{
            **run.__dict__,
            "run_id": "",
            "case_id": "",
            "schema_version": "",
            "feedback_signals": [feedback],
            "feedback_attributions": [attribution],
            "calibration_actions": [action],
        }
    )

    issues = patched.validate_trace()

    assert any("DecisionRun 缺少 run_id" in issue for issue in issues)
    assert any("DecisionRun 缺少 case_id" in issue for issue in issues)
    assert any("DecisionRun 缺少 schema_version" in issue for issue in issues)
    assert any("L9 calibration action 缺少 action_id" in issue for issue in issues)
    assert any("L9 calibration action 缺少 target_id" in issue for issue in issues)



def test_decision_run_to_dict_contains_l0_to_l9_keys() -> None:
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

    assert set(run.to_dict()) == {
        "schema_version",
        "run_id",
        "case_id",
        "raw_payload",
        "chart_ledger",
        "context_ledger",
        "school_applicability",
        "school_claims",
        "structural_verdicts",
        "event_hypotheses",
        "timing_probabilities",
        "arbitration_decisions",
        "report_items",
        "feedback_signals",
        "feedback_attributions",
        "calibration_actions",
    }



def test_l9_merges_reasons_for_same_target_stably() -> None:
    from engine.decision import build_calibration_actions

    attributions = [
        FeedbackAttribution(
            attribution_id="attr-b",
            feedback_id="fb-b",
            affected_layer="L6",
            affected_object_id="same-target",
            attribution_reason="原因B",
            requires_human_review=True,
        ),
        FeedbackAttribution(
            attribution_id="attr-a",
            feedback_id="fb-a",
            affected_layer="L6",
            affected_object_id="same-target",
            attribution_reason="原因A",
            requires_human_review=True,
        ),
    ]

    actions = build_calibration_actions("C-TEST", attributions)

    assert actions[0].reason == "原因A；原因B"



def test_l7_skips_decision_without_competing_events() -> None:
    decision = ArbitrationDecision(
        decision_id="d-empty",
        domain="事业",
        competing_event_ids=[],
        result="unresolved",
    )

    assert build_report_items("C-TEST", [decision], []) == []



def test_l7_reject_all_uses_rejected_ids_as_feedback_points() -> None:
    decision = ArbitrationDecision(
        decision_id="d-reject-all",
        domain="事业",
        competing_event_ids=["e-a", "e-b"],
        result="reject_all",
        rejected_ids=["e-b"],
    )
    timing_b = TimingProbability(prediction_id="t-b", event_id="e-b")

    items = build_report_items("C-TEST", [decision], [timing_b])

    assert [item.prediction_id for item in items] == ["t-b"]



def test_l8_build_feedback_signals_skips_empty_report_item_id() -> None:
    from engine.decision import build_feedback_signals

    signals = build_feedback_signals(
        "C-TEST",
        [ReportViewItem(report_item_id="", decision_id="d-empty")],
    )

    assert signals == []



def test_l8_skipped_feedback_stays_in_l8_without_review() -> None:
    from engine.decision import attribute_feedback

    attribution = attribute_feedback(FeedbackSignal(feedback_id="fb-skip", report_item_id="rv", verdict="skipped"))

    assert attribution.affected_layer == "L8"
    assert attribution.requires_human_review is False



def test_l9_ignores_non_review_attributions_and_sorts_evidence_feedback_ids() -> None:
    from engine.decision import build_calibration_actions

    attributions = [
        FeedbackAttribution(
            attribution_id="attr-no-review",
            feedback_id="fb-no-review",
            affected_layer="L6",
            affected_object_id="same-target",
            attribution_reason="命中样本。",
            requires_human_review=False,
        ),
        FeedbackAttribution(
            attribution_id="attr-2",
            feedback_id="fb-2",
            affected_layer="L6",
            affected_object_id="same-target",
            attribution_reason="重复失验。",
            requires_human_review=True,
        ),
        FeedbackAttribution(
            attribution_id="attr-0",
            feedback_id="fb-0",
            affected_layer="L6",
            affected_object_id="same-target",
            attribution_reason="重复失验。",
            requires_human_review=True,
        ),
        FeedbackAttribution(
            attribution_id="attr-1",
            feedback_id="fb-1",
            affected_layer="L6",
            affected_object_id="same-target",
            attribution_reason="重复失验。",
            requires_human_review=True,
        ),
    ]

    actions = build_calibration_actions("C-TEST", attributions)

    assert len(actions) == 1
    assert actions[0].action == "freeze"
    assert actions[0].evidence_feedback_ids == ["fb-0", "fb-1", "fb-2"]



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



def test_l8_build_feedback_signals_returns_empty_for_empty_report_items() -> None:
    from engine.decision import build_feedback_signals

    assert build_feedback_signals("C-TEST", []) == []



def test_decision_run_validate_trace_checks_l6_result_ids_stay_inside_competing_events() -> None:
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
    event_ids = [item.event_id for item in run.event_hypotheses]
    patched = type(run)(
        **{
            **run.__dict__,
            "arbitration_decisions": [
                ArbitrationDecision(
                    decision_id="d-outside-result",
                    domain="事业",
                    competing_event_ids=[event_ids[0]],
                    result="winner",
                    winner_ids=[event_ids[1]],
                    rejected_ids=[event_ids[1]],
                    unresolved_ids=[event_ids[1]],
                )
            ],
            "report_items": [],
            "feedback_signals": [],
            "feedback_attributions": [],
            "calibration_actions": [],
        }
    )

    issues = patched.validate_trace()

    assert any("L6 decision 结果 ID 不在 competing_event_ids" in issue for issue in issues)



def test_decision_run_validate_trace_checks_l8_layer_is_not_reviewable() -> None:
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
    feedback = FeedbackSignal(feedback_id="fb-l8", report_item_id=run.report_items[0].report_item_id, verdict="unknown")
    attribution = FeedbackAttribution(
        attribution_id="attr-l8-review",
        feedback_id="fb-l8",
        affected_layer="L8",
        affected_object_id=feedback.report_item_id,
        attribution_reason="反馈不足。",
        requires_human_review=True,
    )
    patched = type(run)(
        **{
            **run.__dict__,
            "feedback_signals": [feedback],
            "feedback_attributions": [attribution],
            "calibration_actions": [],
        }
    )

    issues = patched.validate_trace()

    assert any("L8 attribution 不应要求人工治理" in issue for issue in issues)



def test_l9_does_not_create_action_for_empty_target_id() -> None:
    from engine.decision import build_calibration_actions

    actions = build_calibration_actions(
        "C-TEST",
        [
            FeedbackAttribution(
                attribution_id="attr-empty-target",
                feedback_id="fb-empty-target",
                affected_layer="L6",
                affected_object_id="",
                attribution_reason="无目标。",
                requires_human_review=True,
            )
        ],
    )

    assert actions == []



def test_decision_run_validate_trace_checks_l6_result_semantics() -> None:
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
    event_id = run.event_hypotheses[0].event_id
    patched = type(run)(
        **{
            **run.__dict__,
            "arbitration_decisions": [
                ArbitrationDecision(decision_id="d-winner-empty", domain="事业", competing_event_ids=[event_id], result="winner"),
                ArbitrationDecision(decision_id="d-reject-empty", domain="事业", competing_event_ids=[event_id], result="reject_all"),
                ArbitrationDecision(decision_id="d-unresolved-empty", domain="事业", competing_event_ids=[event_id], result="unresolved"),
            ],
            "report_items": [],
            "feedback_signals": [],
            "feedback_attributions": [],
            "calibration_actions": [],
        }
    )

    issues = patched.validate_trace()

    assert any("L6 winner 裁决缺少 winner_ids" in issue for issue in issues)
    assert any("L6 reject_all 裁决缺少 rejected_ids" in issue for issue in issues)
    assert any("L6 unresolved 裁决缺少 unresolved_ids" in issue for issue in issues)



def test_decision_run_validate_trace_checks_l5_probability_range() -> None:
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
    event_id = run.event_hypotheses[0].event_id
    patched = type(run)(
        **{
            **run.__dict__,
            "timing_probabilities": [
                TimingProbability(prediction_id="t-reversed", event_id=event_id, probability_range=(0.8, 0.6)),
                TimingProbability(prediction_id="t-out-of-range", event_id=event_id, probability_range=(-0.1, 1.2)),
            ],
            "arbitration_decisions": [],
            "report_items": [],
            "feedback_signals": [],
            "feedback_attributions": [],
            "calibration_actions": [],
        }
    )

    issues = patched.validate_trace()

    assert any("L5 probability_range 非法" in issue for issue in issues)



def test_decision_run_validate_trace_checks_more_required_layer_ids() -> None:
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
    event_id = run.event_hypotheses[0].event_id
    patched = type(run)(
        **{
            **run.__dict__,
            "school_claims": [type(run.school_claims[0])(**{**run.school_claims[0].__dict__, "domain": ""})],
            "structural_verdicts": [type(run.structural_verdicts[0])(**{**run.structural_verdicts[0].__dict__, "verdict_id": ""})],
            "arbitration_decisions": [
                ArbitrationDecision(
                    decision_id="",
                    domain="",
                    competing_event_ids=[event_id],
                    result="winner",
                    winner_ids=[event_id],
                )
            ],
            "report_items": [ReportViewItem(report_item_id="", decision_id="")],
            "feedback_signals": [],
            "feedback_attributions": [],
            "calibration_actions": [],
        }
    )

    issues = patched.validate_trace()

    assert any("L2 claim 缺少 domain" in issue for issue in issues)
    assert any("L3 verdict 缺少 verdict_id" in issue for issue in issues)
    assert any("L6 decision 缺少 decision_id" in issue for issue in issues)
    assert any("L6 decision 缺少 domain" in issue for issue in issues)
    assert any("L7 report item 缺少 report_item_id" in issue for issue in issues)



def test_decision_run_validate_trace_checks_confidence_ranges() -> None:
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
    patched = type(run)(
        **{
            **run.__dict__,
            "school_applicability": [type(run.school_applicability[0])(**{**run.school_applicability[0].__dict__, "applicability_score": 1.2, "confidence": -0.1})],
            "school_claims": [type(run.school_claims[0])(**{**run.school_claims[0].__dict__, "confidence": 1.1})],
            "structural_verdicts": [type(run.structural_verdicts[0])(**{**run.structural_verdicts[0].__dict__, "confidence": -0.1})],
            "event_hypotheses": [type(run.event_hypotheses[0])(**{**run.event_hypotheses[0].__dict__, "confidence": 1.1})],
            "timing_probabilities": [],
            "arbitration_decisions": [],
            "report_items": [],
            "feedback_signals": [],
            "feedback_attributions": [],
            "calibration_actions": [],
        }
    )

    issues = patched.validate_trace()

    assert any("L1 applicability_score 非法" in issue for issue in issues)
    assert any("L1 confidence 非法" in issue for issue in issues)
    assert any("L2 confidence 非法" in issue for issue in issues)
    assert any("L3 confidence 非法" in issue for issue in issues)
    assert any("L4 confidence 非法" in issue for issue in issues)



def test_decision_run_validate_trace_checks_more_confidence_ranges() -> None:
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
    report_item_id = run.report_items[0].report_item_id
    feedback = FeedbackSignal(feedback_id="fb-confidence", report_item_id=report_item_id, verdict="miss")
    patched = type(run)(
        **{
            **run.__dict__,
            "timing_probabilities": [type(run.timing_probabilities[0])(**{**run.timing_probabilities[0].__dict__, "confidence": 1.1})],
            "arbitration_decisions": [],
            "report_items": [ReportViewItem(report_item_id=report_item_id, decision_id="")],
            "feedback_signals": [feedback],
            "feedback_attributions": [
                FeedbackAttribution(
                    attribution_id="attr-confidence",
                    feedback_id="fb-confidence",
                    affected_layer="L6",
                    affected_object_id=report_item_id,
                    attribution_reason="test",
                    confidence=-0.1,
                    requires_human_review=True,
                )
            ],
            "calibration_actions": [],
        }
    )

    issues = patched.validate_trace()

    assert any("L5 confidence 非法" in issue for issue in issues)
    assert any("L8 attribution confidence 非法" in issue for issue in issues)



def test_decision_run_validate_trace_checks_enum_values() -> None:
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
    report_item_id = run.report_items[0].report_item_id
    feedback = FeedbackSignal(feedback_id="fb-enum", report_item_id=report_item_id, verdict="bad")  # type: ignore[arg-type]
    attribution = FeedbackAttribution(
        attribution_id="attr-enum",
        feedback_id="fb-enum",
        affected_layer="LX",  # type: ignore[arg-type]
        affected_object_id=report_item_id,
        attribution_reason="test",
    )
    action = CalibrationAction(
        action_id="cal-enum",
        target_type="bad_target",  # type: ignore[arg-type]
        target_id="target",
        action="bad_action",  # type: ignore[arg-type]
        reason="test",
        evidence_feedback_ids=["fb-enum"],
    )
    patched = type(run)(
        **{
            **run.__dict__,
            "school_applicability": [type(run.school_applicability[0])(**{**run.school_applicability[0].__dict__, "role": "bad"})],
            "school_claims": [type(run.school_claims[0])(**{**run.school_claims[0].__dict__, "role_granted_by_l1": "bad"})],
            "structural_verdicts": [type(run.structural_verdicts[0])(**{**run.structural_verdicts[0].__dict__, "verdict": "bad"})],
            "event_hypotheses": [],
            "timing_probabilities": [],
            "arbitration_decisions": [type(run.arbitration_decisions[0])(**{**run.arbitration_decisions[0].__dict__, "result": "bad"})],
            "report_items": [ReportViewItem(report_item_id=report_item_id, decision_id=run.arbitration_decisions[0].decision_id)],
            "feedback_signals": [feedback],
            "feedback_attributions": [attribution],
            "calibration_actions": [action],
        }
    )

    issues = patched.validate_trace()

    assert any("L1 role 非法" in issue for issue in issues)
    assert any("L2 role_granted_by_l1 非法" in issue for issue in issues)
    assert any("L3 verdict 非法" in issue for issue in issues)
    assert any("L6 result 非法" in issue for issue in issues)
    assert any("L8 feedback verdict 非法" in issue for issue in issues)
    assert any("L8 affected_layer 非法" in issue for issue in issues)
    assert any("L9 target_type 非法" in issue for issue in issues)
    assert any("L9 action 非法" in issue for issue in issues)



def test_decision_run_validate_trace_checks_feedback_and_attribution_required_ids() -> None:
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
    report_item_id = run.report_items[0].report_item_id
    patched = type(run)(
        **{
            **run.__dict__,
            "feedback_signals": [FeedbackSignal(feedback_id="", report_item_id=report_item_id, verdict="miss")],
            "feedback_attributions": [
                FeedbackAttribution(
                    attribution_id="",
                    feedback_id="",
                    affected_layer="L6",
                    affected_object_id=report_item_id,
                    attribution_reason="",
                    requires_human_review=True,
                )
            ],
            "calibration_actions": [],
        }
    )

    issues = patched.validate_trace()

    assert any("L8 feedback signal 缺少 feedback_id" in issue for issue in issues)
    assert any("L8 attribution 缺少 attribution_id" in issue for issue in issues)
    assert any("L8 attribution 缺少 attribution_reason" in issue for issue in issues)



def test_decision_run_validate_trace_checks_more_l9_required_fields() -> None:
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
    feedback = FeedbackSignal(feedback_id="fb-l9", report_item_id=run.report_items[0].report_item_id, verdict="miss")
    attribution = FeedbackAttribution(
        attribution_id="attr-l9",
        feedback_id="fb-l9",
        affected_layer="L6",
        affected_object_id=feedback.report_item_id,
        attribution_reason="test",
        requires_human_review=True,
    )
    action = CalibrationAction(
        action_id="cal-empty-fields",
        target_type="arbitration_policy",
        target_id="target",
        action="review",
        reason="",
        evidence_feedback_ids=[],
    )
    patched = type(run)(
        **{
            **run.__dict__,
            "feedback_signals": [feedback],
            "feedback_attributions": [attribution],
            "calibration_actions": [action],
        }
    )

    issues = patched.validate_trace()

    assert any("L9 calibration action 缺少 reason" in issue for issue in issues)
    assert any("L9 calibration action 缺少 evidence_feedback_ids" in issue for issue in issues)



def test_decision_run_validate_trace_checks_duplicate_ids() -> None:
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
    feedback = FeedbackSignal(feedback_id="fb-dup", report_item_id=run.report_items[0].report_item_id, verdict="miss")
    attribution = FeedbackAttribution(
        attribution_id="attr-dup",
        feedback_id="fb-dup",
        affected_layer="L6",
        affected_object_id=feedback.report_item_id,
        attribution_reason="test",
    )
    action = CalibrationAction(
        action_id="cal-dup",
        target_type="arbitration_policy",
        target_id="target",
        action="review",
        reason="test",
        evidence_feedback_ids=["fb-dup"],
    )
    patched = type(run)(
        **{
            **run.__dict__,
            "school_claims": [run.school_claims[0], run.school_claims[0]],
            "structural_verdicts": [run.structural_verdicts[0], run.structural_verdicts[0]],
            "event_hypotheses": [run.event_hypotheses[0], run.event_hypotheses[0]],
            "timing_probabilities": [run.timing_probabilities[0], run.timing_probabilities[0]],
            "arbitration_decisions": [run.arbitration_decisions[0], run.arbitration_decisions[0]],
            "report_items": [run.report_items[0], run.report_items[0]],
            "feedback_signals": [feedback, feedback],
            "feedback_attributions": [attribution, attribution],
            "calibration_actions": [action, action],
        }
    )

    issues = patched.validate_trace()

    assert any("L2 claim_id 重复" in issue for issue in issues)
    assert any("L3 verdict_id 重复" in issue for issue in issues)
    assert any("L4 event_id 重复" in issue for issue in issues)
    assert any("L5 prediction_id 重复" in issue for issue in issues)
    assert any("L6 decision_id 重复" in issue for issue in issues)
    assert any("L7 report_item_id 重复" in issue for issue in issues)
    assert any("L8 feedback_id 重复" in issue for issue in issues)
    assert any("L8 attribution_id 重复" in issue for issue in issues)
    assert any("L9 action_id 重复" in issue for issue in issues)



def test_decision_run_validate_trace_checks_l8_l9_semantics() -> None:
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
    feedback = FeedbackSignal(feedback_id="fb-ok", report_item_id=run.report_items[0].report_item_id, verdict="miss")
    attribution = FeedbackAttribution(
        attribution_id="attr-bad-object",
        feedback_id="fb-ok",
        affected_layer="L6",
        affected_object_id="missing-report-item",
        attribution_reason="test",
        requires_human_review=True,
    )
    action = CalibrationAction(
        action_id="cal-without-attribution",
        target_type="arbitration_policy",
        target_id="x",
        action="review",
        reason="test",
        evidence_feedback_ids=["fb-without-attribution"],
    )
    patched = type(run)(
        **{
            **run.__dict__,
            "feedback_signals": [feedback, FeedbackSignal(feedback_id="fb-without-attribution", report_item_id=feedback.report_item_id, verdict="miss")],
            "feedback_attributions": [attribution],
            "calibration_actions": [action],
        }
    )

    issues = patched.validate_trace()

    assert any("L8 attribution 未绑定 L7 report item" in issue for issue in issues)
    assert any("L9 calibration action 未绑定 L8 attribution" in issue for issue in issues)



def test_decision_run_validate_trace_checks_l4_event_source_verdict_status() -> None:
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
    rejected = StructuralVerdict(
        verdict_id="verdict-reject",
        claim_id=run.school_claims[0].claim_id,
        verdict="reject",
        structural_reason="结构不成立。",
    )
    empty_source_event = EventHypothesis(
        event_id="event-empty-source",
        source_verdict_ids=[],
        domain="事业",
        event_type="test",
        subject="test",
        concrete_event="test",
        landing_path="test",
    )
    rejected_source_event = EventHypothesis(
        event_id="event-rejected-source",
        source_verdict_ids=["verdict-reject"],
        domain="事业",
        event_type="test",
        subject="test",
        concrete_event="test",
        landing_path="test",
    )
    patched = type(run)(
        **{
            **run.__dict__,
            "structural_verdicts": [rejected],
            "event_hypotheses": [empty_source_event, rejected_source_event],
            "timing_probabilities": [],
            "arbitration_decisions": [],
            "report_items": [],
            "feedback_signals": [],
            "feedback_attributions": [],
            "calibration_actions": [],
        }
    )

    issues = patched.validate_trace()

    assert any("L4 event 缺少 L3 verdict 来源" in issue for issue in issues)
    assert any("L4 event 绑定未通过的 L3 verdict" in issue for issue in issues)



def test_decision_run_validate_trace_checks_l6_result_ids_and_l7_prediction_scope() -> None:
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
    event_ids = [item.event_id for item in run.event_hypotheses]
    assert len(event_ids) >= 2
    decision = ArbitrationDecision(
        decision_id="d-broken-scope",
        domain="事业",
        competing_event_ids=[event_ids[0]],
        result="winner",
        winner_ids=["missing-winner"],
        rejected_ids=["missing-rejected"],
        unresolved_ids=["missing-unresolved"],
    )
    timing = TimingProbability(prediction_id="t-other-event", event_id=event_ids[1])
    report_item = ReportViewItem(report_item_id="rv-wrong-scope", decision_id="d-broken-scope", prediction_id="t-other-event")
    patched = type(run)(
        **{
            **run.__dict__,
            "arbitration_decisions": [decision],
            "timing_probabilities": [timing],
            "report_items": [report_item],
            "feedback_signals": [],
            "feedback_attributions": [],
            "calibration_actions": [],
        }
    )

    issues = patched.validate_trace()

    assert any("L6 decision 结果 ID 未绑定 L4 event" in issue for issue in issues)
    assert any("L7 report item 的 L5 timing 不属于 L6 decision" in issue for issue in issues)



def test_l7_coexist_decision_keeps_each_winner_feedback_point() -> None:
    decision = ArbitrationDecision(
        decision_id="d-coexist",
        domain="事业",
        competing_event_ids=["e-a", "e-b"],
        result="coexist",
        winner_ids=["e-a", "e-b"],
    )
    timing_a = TimingProbability(prediction_id="t-a", event_id="e-a")
    timing_b = TimingProbability(prediction_id="t-b", event_id="e-b")

    items = build_report_items("C-TEST", [decision], [timing_a, timing_b])

    assert [item.prediction_id for item in items] == ["t-a", "t-b"]
    assert [item.decision_id for item in items] == ["d-coexist", "d-coexist"]



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
