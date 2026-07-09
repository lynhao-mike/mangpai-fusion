"""分层决策最小编排器。

ponytail: 不迁移生产入口，不重写 v5；只串起 L0-L9 最小链路。
"""

from __future__ import annotations

import hashlib

from engine.decision.l0_wenzhen import parse_wenzhen_l0
from engine.decision.l1_school_router import route_schools
from engine.decision.l2_claims import build_school_claims
from engine.decision.l3_structure import build_structural_verdicts
from engine.decision.l4_events import build_event_hypotheses
from engine.decision.l5_timing import build_timing_probabilities
from engine.decision.l6_arbitration import build_arbitration_decisions
from engine.decision.l7_report_view import build_report_items
from engine.decision.l8_feedback_attribution import build_feedback_attributions, build_feedback_signals
from engine.decision.l9_calibration import build_calibration_actions, build_router_calibration_actions
from engine.decision.models import ChartFactLedger, DecisionRun


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]}"


def _case_id(chart: ChartFactLedger) -> str:
    pillars = "".join(chart.four_pillars.get(key, "") for key in ("year", "month", "day", "hour"))
    marker = chart.sex_marker or "乾坤"
    return f"DECISION-MVP-{marker}-{pillars or 'UNKNOWN'}"


def run_decision_mvp(raw_wenzhen_text: str, *, captured_at: str = "") -> DecisionRun:
    """运行 L0-L9 内存最小证明物。"""

    payload, chart, context = parse_wenzhen_l0(raw_wenzhen_text, captured_at=captured_at)
    case_id = _case_id(chart)
    applicability = route_schools(chart, context)
    claims = build_school_claims(case_id, applicability, chart)
    verdicts = build_structural_verdicts(case_id, claims)
    events = build_event_hypotheses(case_id, verdicts, claims)
    timings = build_timing_probabilities(case_id, events)
    decisions = build_arbitration_decisions(case_id, events, applicability)
    report_items = build_report_items(case_id, decisions, timings)
    feedback_signals = build_feedback_signals(case_id, report_items)
    feedback_attributions = build_feedback_attributions(feedback_signals)
    calibration_actions = build_calibration_actions(case_id, feedback_attributions)
    calibration_actions = calibration_actions + build_router_calibration_actions(
        case_id, report_items, decisions, feedback_signals
    )
    return DecisionRun(
        run_id=_stable_id("drun", case_id, payload.raw_hash),
        case_id=case_id,
        raw_payload=payload,
        chart_ledger=chart,
        context_ledger=context,
        school_applicability=applicability,
        school_claims=claims,
        structural_verdicts=verdicts,
        event_hypotheses=events,
        timing_probabilities=timings,
        arbitration_decisions=decisions,
        report_items=report_items,
        feedback_signals=feedback_signals,
        feedback_attributions=feedback_attributions,
        calibration_actions=calibration_actions,
    )
