from __future__ import annotations

import dataclasses

from engine.decision import (
    StructuralVerdict,
    build_arbitration_decisions,
    build_calibration_actions,
    build_event_hypotheses,
    build_feedback_attributions,
    build_feedback_signals,
    build_report_items,
    build_timing_probabilities,
    decision_run_from_v5,
    run_decision_mvp,
)
from engine.decision.l9_calibration import build_router_calibration_actions
from engine.v5 import run_v5


WENZHEN = """
$BASE
命式: 乾
$FOUR
Y:甲寅
M:乙卯
D:丙子
H:戊午
$DY_LOOP
# 1998-2007 甲寅
$FOCUS
事业
""".strip()


def _valid_nonempty_decision_run():
    """生成事件逐一绑定自身 pass/weaken verdict 的合法非空链。"""

    run = run_decision_mvp(WENZHEN)
    verdicts_by_claim = {item.claim_id: item for item in run.structural_verdicts}
    event_claims = [
        claim for claim in run.school_claims if claim.claim_type in {"event", "event_claim"}
    ]
    for index, claim in enumerate(event_claims):
        verdicts_by_claim[claim.claim_id] = StructuralVerdict(
            verdict_id=f"verdict-l9-event-{index}",
            claim_id=claim.claim_id,
            verdict="weaken" if index == 0 else "pass",
            structural_reason="L9 测试夹具显式确认事件命题通过自身结构审查。",
            confidence=claim.confidence,
        )
    verdicts = list(verdicts_by_claim.values())
    events = build_event_hypotheses(run.case_id, verdicts, run.school_claims)
    timings = build_timing_probabilities(run.case_id, events)
    decisions = build_arbitration_decisions(run.case_id, events, run.school_applicability)
    report_items = build_report_items(run.case_id, decisions, timings)
    feedback_signals = build_feedback_signals(run.case_id, report_items)
    feedback_attributions = build_feedback_attributions(feedback_signals)
    calibration_actions = build_calibration_actions(run.case_id, feedback_attributions)
    valid_run = dataclasses.replace(
        run,
        structural_verdicts=verdicts,
        event_hypotheses=events,
        timing_probabilities=timings,
        arbitration_decisions=decisions,
        report_items=report_items,
        feedback_signals=feedback_signals,
        feedback_attributions=feedback_attributions,
        calibration_actions=calibration_actions,
    )
    assert valid_run.validate_trace() == []
    assert valid_run.feedback_signals
    return valid_run


def test_router_calibration_empty_when_no_miss() -> None:
    run = run_decision_mvp(WENZHEN)

    actions = build_router_calibration_actions(
        run.case_id, run.report_items, run.arbitration_decisions, run.feedback_signals
    )

    assert actions == []


def test_router_calibration_targets_lead_school_on_miss() -> None:
    run = _valid_nonempty_decision_run()
    signals = list(run.feedback_signals)
    assert signals, "样例 run 应至少有一条反馈信号"
    signals[0] = dataclasses.replace(signals[0], verdict="miss", notes="流派选错 主审失验")

    actions = build_router_calibration_actions(
        run.case_id, run.report_items, run.arbitration_decisions, signals
    )

    assert actions, "miss 反馈应产出至少一条 router 校准动作"
    assert all(a.target_type == "router" for a in actions)
    assert all(a.target_id for a in actions)
    assert all(a.evidence_feedback_ids for a in actions)
    assert all(a.action in {"review", "downgrade"} for a in actions)


def test_run_decision_mvp_default_has_no_router_calibration() -> None:
    run = run_decision_mvp(WENZHEN)

    router_actions = [a for a in run.calibration_actions if a.target_type == "router"]

    assert router_actions == []
    assert run.validate_trace() == []


def test_v5_adapter_default_has_no_router_calibration() -> None:
    output = run_v5({"case_id": "C-TEST-R3-V5", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})

    run = decision_run_from_v5(output)

    router_actions = [a for a in run.calibration_actions if a.target_type == "router"]
    assert router_actions == []
    assert run.validate_trace() == []
