"""分层命理决策学习系统入口。"""

from __future__ import annotations

from engine.decision.accuracy_report import AccuracyReport, build_accuracy_report, render_accuracy_markdown
from engine.decision.models import (
    ArbitrationDecision,
    CalibrationAction,
    ChartFactLedger,
    ContextFactLedger,
    DecisionRun,
    EventHypothesis,
    FeedbackAttribution,
    FeedbackSignal,
    RawWenzhenPayload,
    ReportViewItem,
    SchoolApplicability,
    SchoolClaim,
    StructuralVerdict,
    TimingProbability,
)
from engine.decision.l0_context import build_context_ledger
from engine.decision.l0_wenzhen import parse_wenzhen_l0
from engine.decision.l1_school_router import RoutePlan, RoutingRiskConfig, TaskRoute, build_route_plan, route_schools
from engine.decision.capability_registry import CapabilityQuery, CapabilityRegistry
from engine.decision.chart_prototype import PrototypeAssignment, classify_prototype
from engine.decision.l2_claims import build_school_claims
from engine.decision.l3_structure import build_structural_verdicts
from engine.decision.l4_events import build_event_hypotheses
from engine.decision.l5_timing import build_timing_probabilities
from engine.decision.l6_arbitration import build_arbitration_decisions
from engine.decision.l7_report_view import build_report_items
from engine.decision.l8_feedback_attribution import attribute_feedback, build_feedback_attributions, build_feedback_signals
from engine.decision.l9_calibration import build_calibration_actions, build_router_calibration_actions
from engine.decision.orchestrator import run_decision_mvp
from engine.decision.v5_adapter import decision_run_from_snapshot, decision_run_from_v5

__all__ = [
    "AccuracyReport",
    "ArbitrationDecision",
    "CalibrationAction",
    "CapabilityQuery",
    "CapabilityRegistry",
    "ChartFactLedger",
    "ContextFactLedger",
    "DecisionRun",
    "EventHypothesis",
    "FeedbackAttribution",
    "FeedbackSignal",
    "PrototypeAssignment",
    "RawWenzhenPayload",
    "ReportViewItem",
    "RoutePlan",
    "RoutingRiskConfig",
    "SchoolApplicability",
    "SchoolClaim",
    "StructuralVerdict",
    "TaskRoute",
    "TimingProbability",
    "attribute_feedback",
    "build_arbitration_decisions",
    "build_accuracy_report",
    "build_context_ledger",
    "build_calibration_actions",
    "build_router_calibration_actions",
    "build_event_hypotheses",
    "build_feedback_attributions",
    "build_feedback_signals",
    "build_report_items",
    "build_route_plan",
    "build_school_claims",
    "build_structural_verdicts",
    "build_timing_probabilities",
    "classify_prototype",
    "parse_wenzhen_l0",
    "render_accuracy_markdown",
    "route_schools",
    "decision_run_from_snapshot",
    "decision_run_from_v5",
    "run_decision_mvp",
]
