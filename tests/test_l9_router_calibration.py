from __future__ import annotations

import dataclasses

from engine.decision import decision_run_from_v5, run_decision_mvp
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


def test_router_calibration_empty_when_no_miss() -> None:
    run = run_decision_mvp(WENZHEN)

    actions = build_router_calibration_actions(
        run.case_id, run.report_items, run.arbitration_decisions, run.feedback_signals
    )

    assert actions == []


def test_router_calibration_targets_lead_school_on_miss() -> None:
    run = run_decision_mvp(WENZHEN)
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
