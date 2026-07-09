"""分层命理决策学习系统的最小数据契约。

本模块只定义 L0-L7 的可序列化对象与链路校验，不实现命理规则。
它是 plans/layered-decision-system.md 的第一阶段落地：先立分层边界，
再逐步把现有 v5 runner 拆入各层。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

DecisionLayer = Literal["L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7", "L8", "L9"]
SchoolRole = Literal["lead", "co_lead", "evidence_only", "abstain"]
StructuralVerdictValue = Literal["pass", "weaken", "reject", "unknown"]
ArbitrationResultValue = Literal["winner", "coexist", "unresolved", "reject_all"]
FeedbackVerdict = Literal["hit", "miss", "partial", "unknown", "skipped"]
CalibrationActionValue = Literal["upgrade", "downgrade", "freeze", "deprecate", "split", "merge", "review"]
CalibrationTargetType = Literal[
    "rule",
    "school_profile",
    "router",
    "structure_policy",
    "event_mapping",
    "timing_policy",
    "arbitration_policy",
    "report_policy",
]


@dataclass(frozen=True)
class RawWenzhenPayload:
    raw_text: str
    raw_hash: str
    captured_at: str = ""
    parser_version: str = "decision-l0-mvp"

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class ChartFactLedger:
    sex_marker: str = ""
    solar_datetime: str = ""
    four_pillars: dict[str, str] = field(default_factory=dict)
    pillar_details: dict[str, Any] = field(default_factory=dict)
    siling: str = ""
    void_by_pillar: dict[str, Any] = field(default_factory=dict)
    start_luck: str = ""
    dayun_steps: list[dict[str, Any]] = field(default_factory=list)
    liunian_steps: list[dict[str, Any]] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    unknown_blocks: list[str] = field(default_factory=list)
    raw_source_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "sex_marker": self.sex_marker,
            "solar_datetime": self.solar_datetime,
            "four_pillars": dict(self.four_pillars),
            "pillar_details": dict(self.pillar_details),
            "siling": self.siling,
            "void_by_pillar": dict(self.void_by_pillar),
            "start_luck": self.start_luck,
            "dayun_steps": [dict(item) for item in self.dayun_steps],
            "liunian_steps": [dict(item) for item in self.liunian_steps],
            "missing_fields": list(self.missing_fields),
            "unknown_blocks": list(self.unknown_blocks),
            "raw_source_hash": self.raw_source_hash,
        }


@dataclass(frozen=True)
class ContextFactLedger:
    known_fact_text: str = ""
    analysis_focus_text: str = ""
    conflict_notes: list[str] = field(default_factory=list)
    preserved_text_blocks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "known_fact_text": self.known_fact_text,
            "analysis_focus_text": self.analysis_focus_text,
            "conflict_notes": list(self.conflict_notes),
            "preserved_text_blocks": list(self.preserved_text_blocks),
        }


@dataclass(frozen=True)
class SchoolApplicability:
    school: str
    role: SchoolRole
    applicable_domains: list[str] = field(default_factory=list)
    applicability_score: float = 0.0
    reasons: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    confidence: float = 0.0
    falsifier: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "school": self.school,
            "role": self.role,
            "applicable_domains": list(self.applicable_domains),
            "applicability_score": self.applicability_score,
            "reasons": list(self.reasons),
            "blockers": list(self.blockers),
            "confidence": self.confidence,
            "falsifier": self.falsifier,
        }


@dataclass(frozen=True)
class SchoolClaim:
    claim_id: str
    school: str
    role_granted_by_l1: SchoolRole
    domain: str
    claim_type: str
    statement: str
    evidence_refs: list[str] = field(default_factory=list)
    confidence: float = 0.0
    falsifier: str = ""
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "school": self.school,
            "role_granted_by_l1": self.role_granted_by_l1,
            "domain": self.domain,
            "claim_type": self.claim_type,
            "statement": self.statement,
            "evidence_refs": list(self.evidence_refs),
            "confidence": self.confidence,
            "falsifier": self.falsifier,
            "dependencies": list(self.dependencies),
        }


@dataclass(frozen=True)
class StructuralVerdict:
    verdict_id: str
    claim_id: str
    verdict: StructuralVerdictValue
    structural_reason: str
    blocking_factors: list[str] = field(default_factory=list)
    required_support: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict_id": self.verdict_id,
            "claim_id": self.claim_id,
            "verdict": self.verdict,
            "structural_reason": self.structural_reason,
            "blocking_factors": list(self.blocking_factors),
            "required_support": list(self.required_support),
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class EventHypothesis:
    event_id: str
    source_verdict_ids: list[str]
    domain: str
    event_type: str
    subject: str
    concrete_event: str
    landing_path: str
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "source_verdict_ids": list(self.source_verdict_ids),
            "domain": self.domain,
            "event_type": self.event_type,
            "subject": self.subject,
            "concrete_event": self.concrete_event,
            "landing_path": self.landing_path,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class TimingProbability:
    prediction_id: str
    event_id: str
    time_window: dict[str, Any] = field(default_factory=dict)
    trigger_conditions: list[str] = field(default_factory=list)
    probability_range: tuple[float, float] = (0.0, 0.0)
    confidence: float = 0.0
    falsifier: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "event_id": self.event_id,
            "time_window": dict(self.time_window),
            "trigger_conditions": list(self.trigger_conditions),
            "probability_range": list(self.probability_range),
            "confidence": self.confidence,
            "falsifier": self.falsifier,
        }


@dataclass(frozen=True)
class ArbitrationDecision:
    decision_id: str
    domain: str
    competing_event_ids: list[str]
    result: ArbitrationResultValue
    winner_ids: list[str] = field(default_factory=list)
    rejected_ids: list[str] = field(default_factory=list)
    unresolved_ids: list[str] = field(default_factory=list)
    arbitration_rule: str = ""
    school_applicability_snapshot: list[SchoolApplicability] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "domain": self.domain,
            "competing_event_ids": list(self.competing_event_ids),
            "result": self.result,
            "winner_ids": list(self.winner_ids),
            "rejected_ids": list(self.rejected_ids),
            "unresolved_ids": list(self.unresolved_ids),
            "arbitration_rule": self.arbitration_rule,
            "school_applicability_snapshot": [item.to_dict() for item in self.school_applicability_snapshot],
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ReportViewItem:
    report_item_id: str
    decision_id: str
    prediction_id: str = ""
    display_text: str = ""
    confidence_display: str = ""
    evidence_summary: str = ""
    feedback_prompt: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class FeedbackSignal:
    feedback_id: str
    report_item_id: str
    verdict: FeedbackVerdict
    observed_fact: str = ""
    observed_time: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class FeedbackAttribution:
    attribution_id: str
    feedback_id: str
    affected_layer: DecisionLayer
    affected_object_id: str
    attribution_reason: str
    confidence: float = 0.0
    requires_human_review: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class CalibrationAction:
    action_id: str
    target_type: CalibrationTargetType
    target_id: str
    action: CalibrationActionValue
    reason: str
    evidence_feedback_ids: list[str] = field(default_factory=list)
    effective_from: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "action": self.action,
            "reason": self.reason,
            "evidence_feedback_ids": list(self.evidence_feedback_ids),
            "effective_from": self.effective_from,
        }


@dataclass(frozen=True)
class DecisionRun:
    run_id: str
    case_id: str
    raw_payload: RawWenzhenPayload
    chart_ledger: ChartFactLedger
    context_ledger: ContextFactLedger = field(default_factory=ContextFactLedger)
    school_applicability: list[SchoolApplicability] = field(default_factory=list)
    school_claims: list[SchoolClaim] = field(default_factory=list)
    structural_verdicts: list[StructuralVerdict] = field(default_factory=list)
    event_hypotheses: list[EventHypothesis] = field(default_factory=list)
    timing_probabilities: list[TimingProbability] = field(default_factory=list)
    arbitration_decisions: list[ArbitrationDecision] = field(default_factory=list)
    report_items: list[ReportViewItem] = field(default_factory=list)
    feedback_signals: list[FeedbackSignal] = field(default_factory=list)
    feedback_attributions: list[FeedbackAttribution] = field(default_factory=list)
    calibration_actions: list[CalibrationAction] = field(default_factory=list)
    schema_version: str = "decision-run-v1"

    def validate_trace(self) -> list[str]:
        """返回链路断点；空列表表示 L7→L0 最小链路不断。"""

        issues: list[str] = []
        applicability = {item.school for item in self.school_applicability}
        claims = {item.claim_id for item in self.school_claims}
        verdicts = {item.verdict_id for item in self.structural_verdicts}
        verdict_by_id = {item.verdict_id: item for item in self.structural_verdicts}
        events = {item.event_id for item in self.event_hypotheses}
        timings = {item.prediction_id for item in self.timing_probabilities}
        timing_event_by_prediction = {item.prediction_id: item.event_id for item in self.timing_probabilities}
        event_ids_by_decision = {item.decision_id: set(item.competing_event_ids) for item in self.arbitration_decisions}
        decisions = {item.decision_id for item in self.arbitration_decisions}
        report_items = {item.report_item_id for item in self.report_items}
        feedbacks = {item.feedback_id for item in self.feedback_signals}
        attributions = {item.attribution_id for item in self.feedback_attributions}

        if not self.raw_payload.raw_hash or self.chart_ledger.raw_source_hash != self.raw_payload.raw_hash:
            issues.append("L0 raw payload 与 chart ledger 未绑定")
        for claim in self.school_claims:
            if claim.school not in applicability:
                issues.append(f"L2 claim 未绑定 L1 school_applicability: {claim.claim_id}")
            if claim.role_granted_by_l1 == "abstain":
                issues.append(f"L2 claim 使用 abstain 流派发言: {claim.claim_id}")
        for verdict in self.structural_verdicts:
            if verdict.claim_id not in claims:
                issues.append(f"L3 verdict 未绑定 L2 claim: {verdict.verdict_id}")
        for event in self.event_hypotheses:
            if not event.source_verdict_ids:
                issues.append(f"L4 event 缺少 L3 verdict 来源: {event.event_id}")
            missing = [item for item in event.source_verdict_ids if item not in verdicts]
            if missing:
                issues.append(f"L4 event 未绑定 L3 verdict: {event.event_id}")
            blocked = [
                item
                for item in event.source_verdict_ids
                if item in verdict_by_id and verdict_by_id[item].verdict not in {"pass", "weaken"}
            ]
            if blocked:
                issues.append(f"L4 event 绑定未通过的 L3 verdict: {event.event_id}")
        for timing in self.timing_probabilities:
            if timing.event_id not in events:
                issues.append(f"L5 timing 未绑定 L4 event: {timing.prediction_id}")
        for decision in self.arbitration_decisions:
            missing = [item for item in decision.competing_event_ids if item not in events]
            if missing:
                issues.append(f"L6 decision 未绑定 L4 event: {decision.decision_id}")
            result_missing = [
                item
                for item in decision.winner_ids + decision.rejected_ids + decision.unresolved_ids
                if item not in events
            ]
            if result_missing:
                issues.append(f"L6 decision 结果 ID 未绑定 L4 event: {decision.decision_id}")
        for item in self.report_items:
            if item.decision_id not in decisions:
                issues.append(f"L7 report item 未绑定 L6 decision: {item.report_item_id}")
            if item.prediction_id and item.prediction_id not in timings:
                issues.append(f"L7 report item 未绑定 L5 timing: {item.report_item_id}")
            elif item.prediction_id and timing_event_by_prediction[item.prediction_id] not in event_ids_by_decision.get(item.decision_id, set()):
                issues.append(f"L7 report item 的 L5 timing 不属于 L6 decision: {item.report_item_id}")
        for signal in self.feedback_signals:
            if signal.report_item_id not in report_items:
                issues.append(f"L8 feedback signal 未绑定 L7 report item: {signal.feedback_id}")
        for attribution in self.feedback_attributions:
            if attribution.feedback_id not in feedbacks:
                issues.append(f"L8 attribution 未绑定 feedback signal: {attribution.attribution_id}")
        for action in self.calibration_actions:
            missing = [item for item in action.evidence_feedback_ids if item not in feedbacks]
            if missing:
                issues.append(f"L9 calibration action 未绑定 feedback signal: {action.action_id}")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "case_id": self.case_id,
            "raw_payload": self.raw_payload.to_dict(),
            "chart_ledger": self.chart_ledger.to_dict(),
            "context_ledger": self.context_ledger.to_dict(),
            "school_applicability": [item.to_dict() for item in self.school_applicability],
            "school_claims": [item.to_dict() for item in self.school_claims],
            "structural_verdicts": [item.to_dict() for item in self.structural_verdicts],
            "event_hypotheses": [item.to_dict() for item in self.event_hypotheses],
            "timing_probabilities": [item.to_dict() for item in self.timing_probabilities],
            "arbitration_decisions": [item.to_dict() for item in self.arbitration_decisions],
            "report_items": [item.to_dict() for item in self.report_items],
            "feedback_signals": [item.to_dict() for item in self.feedback_signals],
            "feedback_attributions": [item.to_dict() for item in self.feedback_attributions],
            "calibration_actions": [item.to_dict() for item in self.calibration_actions],
        }
