from __future__ import annotations

from engine.decision import decision_run_from_v5
from engine.v5 import run_v5
from engine.v5.domain import V5ArbitrationResult, V5Claim, V5Confidence, V5Output, V5Prediction, V5PredictionLedger


def test_decision_run_from_v5_preserves_trace() -> None:
    output = run_v5({"case_id": "C-TEST-DECISION-V5", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})

    run = decision_run_from_v5(output)

    assert run.case_id == output.case_id
    assert run.raw_payload.parser_version == "decision-v5-adapter"
    assert len(run.school_applicability) >= 5
    assert len(run.school_claims) == len([c for c in output.claims if c.stance != "abstain"])
    assert len(run.timing_probabilities) == len(output.prediction_ledger.predictions)
    assert run.report_items
    assert len(run.feedback_signals) == len(run.report_items)
    assert len(run.feedback_attributions) == len(run.feedback_signals)
    assert run.calibration_actions == []
    assert run.validate_trace() == []


def test_v5_adapter_keeps_prediction_probability_ranges() -> None:
    output = run_v5({"case_id": "C-TEST-DECISION-V5-PROB", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})

    run = decision_run_from_v5(output)

    assert [item.probability_range for item in run.timing_probabilities] == [
        item.probability_range for item in output.prediction_ledger.predictions
    ]



def test_v5_adapter_builds_one_report_item_per_event_realization_decision() -> None:
    output = run_v5({"case_id": "C-TEST-DECISION-V5-L7", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})

    run = decision_run_from_v5(output)

    event_domains = {item.domain for item in run.event_hypotheses}
    expected = [item for item in output.arbitration_results if item.stage == "event_realization" and item.domain in event_domains]
    assert len(run.report_items) == len(expected)



def test_v5_adapter_does_not_create_orphan_events_without_claims() -> None:
    output = V5Output(
        case_id="C-TEST-V5-NO-CLAIMS",
        prediction_ledger=V5PredictionLedger(
            case_id="C-TEST-V5-NO-CLAIMS",
            predictions=[
                V5Prediction(
                    prediction_id="p-orphan",
                    domain="事业",
                    event_label="无命题来源的预测",
                    probability_range=(0.3, 0.6),
                    confidence=V5Confidence(score=0.5),
                )
            ],
        ),
    )

    run = decision_run_from_v5(output)

    assert run.event_hypotheses == []
    assert run.timing_probabilities == []
    assert run.arbitration_decisions == []
    assert run.report_items == []
    assert run.validate_trace() == []



def test_v5_adapter_keeps_all_domain_events_as_winners_and_report_items_when_v5_has_winning_schools() -> None:
    output = V5Output(
        case_id="C-TEST-V5-MULTI-WINNER",
        claims=[
            V5Claim(
                claim_id="c-ziping",
                school="ziping",
                domain="事业",
                claim="事业结构成立",
                claim_type="event_claim",
                confidence=V5Confidence(score=0.7),
            ),
            V5Claim(
                claim_id="c-duan",
                school="duan_jianye",
                domain="事业",
                claim="事业事件可落地",
                claim_type="event_claim",
                confidence=V5Confidence(score=0.68),
            ),
        ],
        arbitration_results=[
            V5ArbitrationResult(
                domain="事业",
                stage="event_realization",
                conclusion="事业事件成立",
                winning_schools=["ziping", "duan_jianye"],
            )
        ],
        prediction_ledger=V5PredictionLedger(
            case_id="C-TEST-V5-MULTI-WINNER",
            predictions=[
                V5Prediction(
                    prediction_id="p-career-a",
                    domain="事业",
                    event_label="事业变化 A",
                    probability_range=(0.6, 0.8),
                    confidence=V5Confidence(score=0.7),
                ),
                V5Prediction(
                    prediction_id="p-career-b",
                    domain="事业",
                    event_label="事业变化 B",
                    probability_range=(0.3, 0.6),
                    confidence=V5Confidence(score=0.55),
                ),
            ],
        ),
    )

    run = decision_run_from_v5(output)

    assert len(run.arbitration_decisions) == 1
    assert run.arbitration_decisions[0].winner_ids == [item.event_id for item in run.event_hypotheses]
    assert [item.prediction_id for item in run.report_items] == ["p-career-a", "p-career-b"]
    assert run.validate_trace() == []



def test_l8_more_practical_keywords_route_to_layers() -> None:
    from engine.decision import attribute_feedback
    from engine.decision.models import FeedbackSignal

    cases = [
        ("事实录入错", "L0"),
        ("流派不适用", "L1"),
        ("事件落点错", "L4"),
        ("月份偏差", "L5"),
        ("措辞过满", "L7"),
    ]

    for notes, layer in cases:
        attribution = attribute_feedback(FeedbackSignal(feedback_id=f"fb-{layer}", report_item_id="rv", verdict="miss", notes=notes))
        assert attribution.affected_layer == layer
        assert attribution.requires_human_review is True



def test_l8_l9_turn_miss_into_review_action() -> None:
    from engine.decision import attribute_feedback, build_calibration_actions
    from engine.decision.models import FeedbackSignal

    signal = FeedbackSignal(feedback_id="fb-test", report_item_id="rv-test", verdict="miss")
    attribution = attribute_feedback(signal)
    actions = build_calibration_actions("C-TEST", [attribution])

    assert attribution.affected_layer == "L6"
    assert attribution.requires_human_review is True
    assert actions[0].target_type == "arbitration_policy"
    assert actions[0].action == "review"


def test_l8_notes_can_route_to_l4_or_l7() -> None:
    from engine.decision import attribute_feedback
    from engine.decision.models import FeedbackSignal

    event_type = attribute_feedback(
        FeedbackSignal(feedback_id="fb-l4", report_item_id="rv", verdict="miss", notes="事件类型错")
    )
    expression = attribute_feedback(
        FeedbackSignal(feedback_id="fb-l7", report_item_id="rv", verdict="partial", notes="表达太绝对")
    )

    assert event_type.affected_layer == "L4"
    assert expression.affected_layer == "L7"


def test_l8_input_conflict_notes_route_to_l0() -> None:
    from engine.decision import attribute_feedback
    from engine.decision.models import FeedbackSignal

    attribution = attribute_feedback(
        FeedbackSignal(feedback_id="fb-l0", report_item_id="rv", verdict="miss", notes="命主补充事实与输入矛盾")
    )

    assert attribution.affected_layer == "L0"
    assert attribution.requires_human_review is True



def test_l8_school_routing_failure_notes_route_to_l1() -> None:
    from engine.decision import attribute_feedback
    from engine.decision.models import FeedbackSignal

    attribution = attribute_feedback(
        FeedbackSignal(feedback_id="fb-l1", report_item_id="rv", verdict="miss", notes="某派主审连续失验，可能流派选错")
    )

    assert attribution.affected_layer == "L1"
    assert attribution.requires_human_review is True



def test_l8_weak_original_claim_notes_route_to_l2() -> None:
    from engine.decision import attribute_feedback
    from engine.decision.models import FeedbackSignal

    attribution = attribute_feedback(
        FeedbackSignal(feedback_id="fb-l2", report_item_id="rv", verdict="miss", notes="事件和年份都错，原命题也弱")
    )

    assert attribution.affected_layer == "L2"
    assert attribution.requires_human_review is True



def test_l8_arbitration_conflict_notes_route_to_l6() -> None:
    from engine.decision import attribute_feedback
    from engine.decision.models import FeedbackSignal

    attribution = attribute_feedback(
        FeedbackSignal(feedback_id="fb-l6", report_item_id="rv", verdict="partial", notes="两派冲突，系统选错一方")
    )

    assert attribution.affected_layer == "L6"
    assert attribution.requires_human_review is True



def test_l8_batch_keyword_routes() -> None:
    from engine.decision import attribute_feedback
    from engine.decision.models import FeedbackSignal

    cases = [
        ("fb-l2-more", "命题不成立", "L2"),
        ("fb-l3-more", "结构审查误放行", "L3"),
        ("fb-l5-more", "时间窗错", "L5"),
        ("fb-l6-more", "仲裁选错", "L6"),
        ("fb-l7-more", "报告失真", "L7"),
    ]

    for feedback_id, notes, layer in cases:
        attribution = attribute_feedback(FeedbackSignal(feedback_id=feedback_id, report_item_id="rv", verdict="miss", notes=notes))
        assert attribution.affected_layer == layer
        assert attribution.requires_human_review is True



def test_l8_tendency_expression_notes_route_to_l7() -> None:
    from engine.decision import attribute_feedback
    from engine.decision.models import FeedbackSignal

    attribution = attribute_feedback(
        FeedbackSignal(feedback_id="fb-l7-tendency", report_item_id="rv", verdict="partial", notes="实际只是倾向")
    )

    assert attribution.affected_layer == "L7"
    assert attribution.requires_human_review is True



def test_l8_structural_problem_notes_route_to_l3() -> None:
    from engine.decision import attribute_feedback
    from engine.decision.models import FeedbackSignal

    attribution = attribute_feedback(
        FeedbackSignal(feedback_id="fb-l3", report_item_id="rv", verdict="miss", notes="结构基础不成立，原局结构弱")
    )

    assert attribution.affected_layer == "L3"
    assert attribution.requires_human_review is True



def test_l8_time_deviation_notes_route_to_l5() -> None:
    from engine.decision import attribute_feedback
    from engine.decision.models import FeedbackSignal

    attribution = attribute_feedback(
        FeedbackSignal(feedback_id="fb-l5", report_item_id="rv", verdict="miss", observed_time="年份偏差两年")
    )

    assert attribution.affected_layer == "L5"
    assert attribution.requires_human_review is True



def test_l9_keeps_same_target_id_separate_across_layers() -> None:
    from engine.decision import build_calibration_actions
    from engine.decision.models import FeedbackAttribution

    attributions = [
        FeedbackAttribution(
            attribution_id="attr-l4",
            feedback_id="fb-l4",
            affected_layer="L4",
            affected_object_id="same-target",
            attribution_reason="事件落地失验",
            requires_human_review=True,
        ),
        FeedbackAttribution(
            attribution_id="attr-l7",
            feedback_id="fb-l7",
            affected_layer="L7",
            affected_object_id="same-target",
            attribution_reason="报告表达失真",
            requires_human_review=True,
        ),
    ]

    actions = build_calibration_actions("C-TEST", attributions)

    assert [(item.target_type, item.target_id, item.evidence_feedback_ids) for item in actions] == [
        ("event_mapping", "same-target", ["fb-l4"]),
        ("report_policy", "same-target", ["fb-l7"]),
    ]



def test_l9_freezes_repeated_review_target() -> None:
    from engine.decision import build_calibration_actions
    from engine.decision.models import FeedbackAttribution

    attributions = [
        FeedbackAttribution(
            attribution_id=f"attr-{idx}",
            feedback_id=f"fb-{idx}",
            affected_layer="L6",
            affected_object_id="same-target",
            attribution_reason="重复失验",
            requires_human_review=True,
        )
        for idx in range(3)
    ]

    actions = build_calibration_actions("C-TEST", attributions)

    assert len(actions) == 1
    assert actions[0].action == "freeze"
    assert actions[0].target_id == "same-target"
    assert actions[0].evidence_feedback_ids == ["fb-0", "fb-1", "fb-2"]
