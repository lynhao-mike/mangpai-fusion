"""事件影响裁决、状态转移以及事实/假设双快照。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from engine.asof.event_candidate import (
    CompletionMode,
    LifeEventCandidate,
    RootLevel,
    VerificationStatus,
)
from engine.asof.reality_track import PathState, RealityStateEntry, RealityTrack, build_reality_track


class ImpactLevel(str, Enum):
    MINOR = "MINOR"
    SIGNIFICANT = "SIGNIFICANT"
    MAJOR = "MAJOR"
    TURNING_POINT = "TURNING_POINT"


class Persistence(str, Enum):
    INSTANT = "INSTANT"
    SHORT_TERM = "SHORT_TERM"
    REMAINDER_OF_DAIYUN = "REMAINDER_OF_DAIYUN"
    CROSS_DAIYUN = "CROSS_DAIYUN"
    PERMANENT = "PERMANENT"


class ImpactScope(str, Enum):
    PRIMARY_DOMAIN = "PRIMARY_DOMAIN"
    RELATED_DOMAINS = "RELATED_DOMAINS"
    GLOBAL_BASELINE = "GLOBAL_BASELINE"


class DecisionAction(str, Enum):
    OUTPUT = "OUTPUT"
    CONDITIONAL = "CONDITIONAL"
    ASK = "ASK"
    ABSTAIN = "ABSTAIN"
    HUMAN_REVIEW = "HUMAN_REVIEW"


@dataclass(frozen=True, slots=True)
class AsOfRequest:
    """显式截止日请求；``as_of_date`` 无默认值且不读取系统时钟。"""

    case_id: str
    as_of_date: date


@dataclass(frozen=True, slots=True)
class EventImpactAssessment:
    """分类式影响裁决；系统冻结建议与人工最终裁决并存。"""

    event_id: str
    event_date: date
    event_type: str
    root_level: RootLevel
    completion_mode: CompletionMode
    system_suggested_impact: ImpactLevel
    system_suggested_persistence: Persistence
    system_suggested_scope: ImpactScope
    practitioner_final_impact: ImpactLevel | None = None
    practitioner_final_persistence: Persistence | None = None
    practitioner_final_scope: ImpactScope | None = None
    adjustment_reason: str | None = None
    short_term_until: date | None = None
    state_value: str = ""
    opened_path_ids: tuple[str, ...] = ()
    closed_path_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        finals = (
            self.practitioner_final_impact,
            self.practitioner_final_persistence,
            self.practitioner_final_scope,
        )
        if any(item is not None for item in finals) and not all(item is not None for item in finals):
            raise ValueError("practitioner final assessment must set impact, persistence and scope together")
        if all(item is not None for item in finals) and not (self.adjustment_reason or "").strip():
            raise ValueError("manual adjustment requires a reason while preserving system suggestions")
        if self.effective_persistence is Persistence.SHORT_TERM and self.short_term_until is None:
            raise ValueError("short-term persistence requires an explicit expiry")
        if self.effective_impact is ImpactLevel.TURNING_POINT and not (
            self.opened_path_ids or self.closed_path_ids
        ):
            raise ValueError("turning-point impact requires an explicit path change")

    @property
    def effective_impact(self) -> ImpactLevel:
        return self.practitioner_final_impact or self.system_suggested_impact

    @property
    def effective_persistence(self) -> Persistence:
        return self.practitioner_final_persistence or self.system_suggested_persistence

    @property
    def effective_scope(self) -> ImpactScope:
        return self.practitioner_final_scope or self.system_suggested_scope


@dataclass(frozen=True, slots=True)
class EventLedgerEntry:
    candidate: LifeEventCandidate
    assessment: EventImpactAssessment

    def __post_init__(self) -> None:
        if self.candidate.candidate_id != self.assessment.event_id:
            raise ValueError("candidate and impact assessment event ids differ")


@dataclass(frozen=True, slots=True)
class VerifiedState:
    """正式后运主线唯一事实起点；无未核验候选字段。"""

    case_id: str
    as_of_date: date
    reality_track: RealityTrack
    current_center: str
    reasonable_range: tuple[str, ...]
    verified_event_ids: tuple[str, ...]
    active_state_ids: tuple[str, ...]
    decision_action: DecisionAction


@dataclass(frozen=True, slots=True)
class HypothesisState:
    """未核验重大候选成立时的独立竞争分支。"""

    case_id: str
    as_of_date: date
    candidate_id: str
    condition: str
    difference_from_verified: str
    changed_fundamentals: tuple[str, ...]
    changed_future_conclusions: tuple[str, ...]
    minimum_question: str
    falsifier: str
    decision_action: DecisionAction

    def __post_init__(self) -> None:
        if self.decision_action not in {DecisionAction.CONDITIONAL, DecisionAction.ASK}:
            raise ValueError("hypothesis branch must remain conditional or ask")
        if not all((self.condition, self.difference_from_verified, self.minimum_question, self.falsifier)):
            raise ValueError("hypothesis branch requires condition, delta, question and falsifier")


def _state_until(assessment: EventImpactAssessment, daiyun_end: date) -> date | None:
    persistence = assessment.effective_persistence
    if persistence is Persistence.SHORT_TERM:
        return assessment.short_term_until
    if persistence is Persistence.REMAINDER_OF_DAIYUN:
        return daiyun_end
    if persistence in {Persistence.CROSS_DAIYUN, Persistence.PERMANENT}:
        return None
    return assessment.event_date


def _confirmed_state(entry: EventLedgerEntry, daiyun_end: date) -> RealityStateEntry | None:
    candidate = entry.candidate
    assessment = entry.assessment
    if candidate.verification_status is not VerificationStatus.CONFIRMED:
        return None
    if assessment.effective_impact is ImpactLevel.MINOR:
        return None
    if assessment.effective_persistence is Persistence.INSTANT:
        return None
    return RealityStateEntry(
        state_id=f"state:{assessment.event_id}",
        domain=candidate.domain,
        value=assessment.state_value or candidate.event_type,
        source_event_id=assessment.event_id,
        effective_from=assessment.event_date,
        effective_until=_state_until(assessment, daiyun_end),
        verified=True,
    )


def build_verified_state(
    request: AsOfRequest,
    *,
    entries: tuple[EventLedgerEntry, ...],
    daiyun_end: date,
    current_center: str,
    reasonable_range: tuple[str, ...] = (),
) -> VerifiedState:
    """只归并截止日前已确认且仍有效的事件后果。"""

    eligible_entries = tuple(
        entry
        for entry in entries
        if entry.assessment.event_date <= request.as_of_date
        and entry.candidate.verification_status is VerificationStatus.CONFIRMED
    )
    states = tuple(
        state
        for entry in eligible_entries
        if (state := _confirmed_state(entry, daiyun_end)) is not None
    )
    paths: list[PathState] = []
    for entry in eligible_entries:
        assessment = entry.assessment
        if assessment.effective_impact is not ImpactLevel.TURNING_POINT:
            continue
        paths.extend(PathState(path_id, "open", assessment.event_id) for path_id in assessment.opened_path_ids)
        paths.extend(PathState(path_id, "closed", assessment.event_id) for path_id in assessment.closed_path_ids)
    reality = build_reality_track(
        case_id=request.case_id,
        as_of_date=request.as_of_date,
        states=states,
        path_states=tuple(paths),
    )
    return VerifiedState(
        case_id=request.case_id,
        as_of_date=request.as_of_date,
        reality_track=reality,
        current_center=current_center,
        reasonable_range=reasonable_range,
        verified_event_ids=reality.verified_event_ids,
        active_state_ids=tuple(state.state_id for state in reality.active_states),
        decision_action=DecisionAction.OUTPUT,
    )


def admit_hypothesis_branch(
    request: AsOfRequest,
    *,
    candidate: LifeEventCandidate,
    assessment: EventImpactAssessment,
    condition: str,
    difference_from_verified: str,
    changed_fundamentals: tuple[str, ...],
    changed_future_conclusions: tuple[str, ...],
    minimum_question: str,
    falsifier: str,
) -> HypothesisState | None:
    """执行分支准入门；未核验候选永不写入 ``VerifiedState``。"""

    if candidate.verification_status in {VerificationStatus.CONFIRMED, VerificationStatus.REJECTED}:
        return None
    if assessment.effective_impact not in {ImpactLevel.MAJOR, ImpactLevel.TURNING_POINT}:
        return None
    if assessment.effective_persistence not in {
        Persistence.REMAINDER_OF_DAIYUN,
        Persistence.CROSS_DAIYUN,
        Persistence.PERMANENT,
    }:
        return None
    if not changed_fundamentals or not changed_future_conclusions or not minimum_question.strip():
        return None
    return HypothesisState(
        case_id=request.case_id,
        as_of_date=request.as_of_date,
        candidate_id=candidate.candidate_id,
        condition=condition,
        difference_from_verified=difference_from_verified,
        changed_fundamentals=changed_fundamentals,
        changed_future_conclusions=changed_future_conclusions,
        minimum_question=minimum_question,
        falsifier=falsifier,
        decision_action=DecisionAction.CONDITIONAL,
    )
