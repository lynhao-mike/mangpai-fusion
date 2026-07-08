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
