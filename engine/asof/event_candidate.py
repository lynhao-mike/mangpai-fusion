"""年度作用轨迹、事业事件候选与根源×完成方式证据门。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from engine.asof.natal_capacity import EvidenceRef, SourceCitation


class RootLevel(str, Enum):
    STRONG_ROOT = "STRONG_ROOT"
    WEAK_ROOT = "WEAK_ROOT"
    NO_ROOT = "NO_ROOT"


class CompletionMode(str, Enum):
    ACTIVATE_EXISTING = "ACTIVATE_EXISTING"
    COMPLETE_LATENT = "COMPLETE_LATENT"
    REPAIR_DEFECT = "REPAIR_DEFECT"
    TEMPORARY_SUBSTITUTE = "TEMPORARY_SUBSTITUTE"
    INVALID_COMPLETION = "INVALID_COMPLETION"


class VerificationStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    FROZEN = "FROZEN"
    PARTIAL_HIT = "PARTIAL_HIT"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"
    WITHHELD = "WITHHELD"


class ExtensionBoundary(str, Enum):
    """根源等级对纯命理未来延伸范围的实际约束。"""

    CROSS_DAIYUN_ELIGIBLE = "CROSS_DAIYUN_ELIGIBLE"
    REMAINDER_ONLY_RECHECK_CROSS_DAIYUN = "REMAINDER_ONLY_RECHECK_CROSS_DAIYUN"
    SHORT_TERM_ONLY = "SHORT_TERM_ONLY"


@dataclass(frozen=True, slots=True)
class AnnualInteractionTrace:
    """可审计年度命理作用轨迹；触发强度不等于现实影响度。"""

    year: int
    liunian: str
    dayun_ganzhi: str
    relations: tuple[EvidenceRef, ...]
    activated_node_ids: tuple[str, ...]
    domains: tuple[str, ...]
    supporting_evidence: tuple[EvidenceRef, ...]
    counter_evidence: tuple[EvidenceRef, ...]
    trigger_strength: str
    crossed_candidate_gate: bool

    def __post_init__(self) -> None:
        if self.year < 1 or not self.liunian.strip() or not self.dayun_ganzhi.strip():
            raise ValueError("annual trace requires year, liunian and dayun")
        if self.trigger_strength not in {"low", "medium", "high"}:
            raise ValueError("trigger strength must remain a categorical structural signal")
        if self.crossed_candidate_gate and not (self.relations and self.activated_node_ids):
            raise ValueError("a crossed gate requires an作用 chain and activated natal nodes")


@dataclass(frozen=True, slots=True)
class LifeEventCandidate:
    """已冻结或待核验的事业事件候选，不承担现实后果裁决。"""

    candidate_id: str
    domain: str
    event_type: str
    window_start: date
    window_end: date
    natal_evidence: tuple[EvidenceRef, ...]
    daiyun_evidence: tuple[EvidenceRef, ...]
    annual_trace: AnnualInteractionTrace
    root_level: RootLevel
    root_evidence: tuple[EvidenceRef, ...]
    source_citations: tuple[SourceCitation, ...]
    completion_mode: CompletionMode
    supporting_evidence: tuple[EvidenceRef, ...]
    counter_evidence: tuple[EvidenceRef, ...]
    alternative_hypotheses: tuple[str, ...]
    frozen_version: str
    verification_status: VerificationStatus
    extension_boundary: ExtensionBoundary
    is_primary_event: bool

    def __post_init__(self) -> None:
        if self.domain != "career":
            raise ValueError("prototype event candidates are career-only")
        if self.window_start > self.window_end:
            raise ValueError("event window is reversed")
        if not self.natal_evidence or not self.root_evidence or not self.source_citations:
            raise ValueError("candidate requires both chart and primary-source evidence")
        if self.is_primary_event and self.completion_mode is CompletionMode.INVALID_COMPLETION:
            raise ValueError("invalid completion cannot produce a primary event")


@dataclass(frozen=True, slots=True)
class CandidateDecision:
    accepted: bool
    reason_code: str
    candidate: LifeEventCandidate | None


REGISTERED_COMBINATIONS = frozenset(
    {
        (RootLevel.STRONG_ROOT, CompletionMode.ACTIVATE_EXISTING),
        (RootLevel.STRONG_ROOT, CompletionMode.REPAIR_DEFECT),
        (RootLevel.WEAK_ROOT, CompletionMode.COMPLETE_LATENT),
        (RootLevel.WEAK_ROOT, CompletionMode.TEMPORARY_SUBSTITUTE),
        (RootLevel.NO_ROOT, CompletionMode.TEMPORARY_SUBSTITUTE),
    }
)


def extension_boundary_for(root_level: RootLevel) -> ExtensionBoundary:
    """根源约束推演延伸，但不能用于否认已核验现实。"""

    return {
        RootLevel.STRONG_ROOT: ExtensionBoundary.CROSS_DAIYUN_ELIGIBLE,
        RootLevel.WEAK_ROOT: ExtensionBoundary.REMAINDER_ONLY_RECHECK_CROSS_DAIYUN,
        RootLevel.NO_ROOT: ExtensionBoundary.SHORT_TERM_ONLY,
    }[root_level]


def evaluate_event_candidate(
    *,
    candidate_id: str,
    event_type: str,
    window_start: date,
    window_end: date,
    annual_trace: AnnualInteractionTrace,
    root_level: RootLevel,
    completion_mode: CompletionMode,
    natal_evidence: tuple[EvidenceRef, ...],
    daiyun_evidence: tuple[EvidenceRef, ...],
    root_evidence: tuple[EvidenceRef, ...],
    source_citations: tuple[SourceCitation, ...],
    supporting_evidence: tuple[EvidenceRef, ...],
    counter_evidence: tuple[EvidenceRef, ...] = (),
    alternative_hypotheses: tuple[str, ...] = (),
    frozen_version: str = "asof-prototype-v1",
) -> CandidateDecision:
    """执行白名单和双证据门；不读取现实履历，也不计算加权分。

    `INVALID_COMPLETION` 被登记用于反证审计，但绝不生成目标主事件。
    其他未登记组合直接逻辑拒绝，不创建候选对象。
    """

    if root_level is RootLevel.NO_ROOT and completion_mode is CompletionMode.ACTIVATE_EXISTING:
        return CandidateDecision(False, "LOGICAL_CONTRADICTION_NO_EXISTING_FUNCTION", None)
    if root_level is RootLevel.NO_ROOT and completion_mode is CompletionMode.COMPLETE_LATENT:
        return CandidateDecision(False, "NO_ROOT_CANNOT_COMPLETE_LATENT", None)
    is_invalid = completion_mode is CompletionMode.INVALID_COMPLETION
    if not is_invalid and (root_level, completion_mode) not in REGISTERED_COMBINATIONS:
        return CandidateDecision(False, "UNREGISTERED_COMBINATION", None)
    if not natal_evidence or not root_evidence:
        return CandidateDecision(False, "MISSING_CHART_STRUCTURE_EVIDENCE", None)
    if not source_citations:
        return CandidateDecision(False, "MISSING_PRIMARY_SOURCE_EVIDENCE", None)
    if not annual_trace.crossed_candidate_gate and not is_invalid:
        return CandidateDecision(False, "ANNUAL_TRACE_BELOW_CANDIDATE_GATE", None)
    candidate = LifeEventCandidate(
        candidate_id=candidate_id,
        domain="career",
        event_type=event_type,
        window_start=window_start,
        window_end=window_end,
        natal_evidence=natal_evidence,
        daiyun_evidence=daiyun_evidence,
        annual_trace=annual_trace,
        root_level=root_level,
        root_evidence=root_evidence,
        source_citations=source_citations,
        completion_mode=completion_mode,
        supporting_evidence=supporting_evidence,
        counter_evidence=counter_evidence,
        alternative_hypotheses=alternative_hypotheses,
        frozen_version=frozen_version,
        verification_status=(VerificationStatus.WITHHELD if is_invalid else VerificationStatus.FROZEN),
        extension_boundary=extension_boundary_for(root_level),
        is_primary_event=not is_invalid,
    )
    return CandidateDecision(True, "INVALID_COMPLETION_WITHHELD" if is_invalid else "CANDIDATE_FROZEN", candidate)
