from __future__ import annotations

from engine.decision import decision_run_from_v5
from engine.v5 import run_v5


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


def test_l8_time_deviation_notes_route_to_l5() -> None:
    from engine.decision import attribute_feedback
    from engine.decision.models import FeedbackSignal

    attribution = attribute_feedback(
        FeedbackSignal(feedback_id="fb-l5", report_item_id="rv", verdict="miss", observed_time="年份偏差两年")
    )

    assert attribution.affected_layer == "L5"
    assert attribution.requires_human_review is True



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
