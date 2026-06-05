"""多流派并行功能域分析领域模型。

本模块是 v1.5 多专家系统的旁路模型层：
- 不接入默认 D1-D4 pipeline；
- 不读取或修改子平 / 滴天髓 / 盲派内部中间态；
- 只定义进入裁判层的统一外部输出协议。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

ExpertSystem = Literal["blind", "ziping", "tiaohou_ditiansui"]
BlindSubSchool = Literal["段", "杨", "任", "高"]
DomainName = Literal["财运", "事业", "婚姻", "健康", "性格", "学业"]
ReadingStance = Literal["support", "oppose", "mixed", "abstain", "timing_only"]
Ballot = Literal["yes", "no", "mixed", "abstain"]
AdjudicationDecision = Literal["yes", "no", "mixed", "no_output"]
ConsensusLayer = Literal["多专家共识", "双专家共识", "主专家胜出", "强证据少数派胜出", "冲突保留", "独门", "不输出"]
FeedbackState = Literal["hit", "miss", "no_data", "skip", "pending", "partial"]
OutputStrategy = Literal["primary_only", "primary_with_minority", "parallel", "downgraded", "phased"]
EvidenceType = Literal["source_excerpt", "candidate_rule", "case_feedback", "runtime_finding"]
EvidenceStrength = Literal["high", "medium", "low"]


@dataclass(frozen=True)
class ParallelConfidence:
    """裁判层置信度外壳，区分单派、合并与反馈后置信。"""

    raw: float
    merged: Optional[float] = None
    feedback_adjusted: Optional[float] = None
    star: int = 1
    percent: int = 0
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw": self.raw,
            "merged": self.merged,
            "feedback_adjusted": self.feedback_adjusted,
            "star": self.star,
            "percent": self.percent,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ParallelConfidence":
        return cls(
            raw=float(data.get("raw", 0.0)),
            merged=(float(data["merged"]) if data.get("merged") is not None else None),
            feedback_adjusted=(
                float(data["feedback_adjusted"])
                if data.get("feedback_adjusted") is not None
                else None
            ),
            star=int(data.get("star", 1)),
            percent=int(data.get("percent", 0)),
            reason=str(data.get("reason", "")),
        )


@dataclass(frozen=True)
class EvidenceItem:
    """专家 reading 或裁判结论的证据粒度项。"""

    evidence_type: EvidenceType
    ref: str
    summary: str
    strength: EvidenceStrength = "medium"

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_type": self.evidence_type,
            "ref": self.ref,
            "summary": self.summary,
            "strength": self.strength,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceItem":
        return cls(
            evidence_type=data["evidence_type"],
            ref=str(data["ref"]),
            summary=str(data["summary"]),
            strength=data.get("strength", "medium"),
        )


@dataclass(frozen=True)
class TimeScope:
    """时间分段外壳，用于大运、流年、阶段或事件窗口。"""

    type: Literal["static", "dayun", "liunian", "phase", "event_window"]
    label: str
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "label": self.label,
            "start_year": self.start_year,
            "end_year": self.end_year,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TimeScope":
        return cls(
            type=data["type"],
            label=str(data["label"]),
            start_year=(int(data["start_year"]) if data.get("start_year") is not None else None),
            end_year=(int(data["end_year"]) if data.get("end_year") is not None else None),
            description=str(data.get("description", "")),
        )


@dataclass(frozen=True)
class WeightProfile:
    """本次裁判使用的领域权重版本。"""

    profile_id: str
    profile_version: str
    source: str
    domain_weights: dict[ExpertSystem, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "source": self.source,
            "domain_weights": dict(self.domain_weights),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WeightProfile":
        version = data.get("profile_version", data.get("version", ""))
        return cls(
            profile_id=str(data["profile_id"]),
            profile_version=str(version),
            source=str(data.get("source", "")),
            domain_weights={k: float(v) for k, v in data.get("domain_weights", {}).items()},
        )


@dataclass(frozen=True)
class ExpertReading:
    """三大专家体系进入裁判模型的唯一统一外部协议。"""

    reading_id: str
    case_id: str
    domain: DomainName
    expert_system: ExpertSystem
    expert_name: str
    stance: ReadingStance
    claim: str
    polarity: Literal["positive", "negative", "mixed", "neutral"]
    confidence: ParallelConfidence
    evidence_items: list[EvidenceItem] = field(default_factory=list)
    axis_refs: list[str] = field(default_factory=list)
    scope_limit: str = ""
    falsifiable: str = ""
    source_engine: str = "theory_adapter"
    isolation_boundary: str = "external_protocol_only"
    sub_school: Optional[BlindSubSchool] = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "reading_id": self.reading_id,
            "case_id": self.case_id,
            "domain": self.domain,
            "expert_system": self.expert_system,
            "expert_name": self.expert_name,
            "stance": self.stance,
            "claim": self.claim,
            "polarity": self.polarity,
            "confidence": self.confidence.to_dict(),
            "evidence_items": [item.to_dict() for item in self.evidence_items],
            "axis_refs": list(self.axis_refs),
            "scope_limit": self.scope_limit,
            "falsifiable": self.falsifiable,
            "source_engine": self.source_engine,
            "isolation_boundary": self.isolation_boundary,
            "sub_school": self.sub_school,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExpertReading":
        return cls(
            reading_id=str(data["reading_id"]),
            case_id=str(data["case_id"]),
            domain=data["domain"],
            expert_system=data["expert_system"],
            expert_name=str(data["expert_name"]),
            stance=data["stance"],
            claim=str(data["claim"]),
            polarity=data.get("polarity", "neutral"),
            confidence=ParallelConfidence.from_dict(data["confidence"]),
            evidence_items=[EvidenceItem.from_dict(x) for x in data.get("evidence_items", [])],
            axis_refs=[str(x) for x in data.get("axis_refs", [])],
            scope_limit=str(data.get("scope_limit", "")),
            falsifiable=str(data.get("falsifiable", "")),
            source_engine=str(data.get("source_engine", "theory_adapter")),
            isolation_boundary=str(data.get("isolation_boundary", "external_protocol_only")),
            sub_school=data.get("sub_school"),
            notes=str(data.get("notes", "")),
        )


@dataclass(frozen=True)
class ExpertJudgement:
    """裁判模型对单条 ExpertReading 的评分明细。"""

    judgement_id: str
    reading_id: str
    expert_system: ExpertSystem
    domain: DomainName
    claim: str
    ballot: Ballot
    raw_score: float
    prior_domain_weight: float
    confidence_weight: float
    feedback_weight: float
    evidence_quality_weight: float
    conflict_penalty: float
    adjusted_score: float
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "judgement_id": self.judgement_id,
            "reading_id": self.reading_id,
            "expert_system": self.expert_system,
            "domain": self.domain,
            "claim": self.claim,
            "ballot": self.ballot,
            "raw_score": self.raw_score,
            "prior_domain_weight": self.prior_domain_weight,
            "confidence_weight": self.confidence_weight,
            "feedback_weight": self.feedback_weight,
            "evidence_quality_weight": self.evidence_quality_weight,
            "conflict_penalty": self.conflict_penalty,
            "adjusted_score": self.adjusted_score,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExpertJudgement":
        return cls(
            judgement_id=str(data["judgement_id"]),
            reading_id=str(data["reading_id"]),
            expert_system=data["expert_system"],
            domain=data["domain"],
            claim=str(data["claim"]),
            ballot=data["ballot"],
            raw_score=float(data["raw_score"]),
            prior_domain_weight=float(data["prior_domain_weight"]),
            confidence_weight=float(data["confidence_weight"]),
            feedback_weight=float(data["feedback_weight"]),
            evidence_quality_weight=float(data["evidence_quality_weight"]),
            conflict_penalty=float(data["conflict_penalty"]),
            adjusted_score=float(data["adjusted_score"]),
            rationale=str(data.get("rationale", "")),
        )


@dataclass(frozen=True)
class MinorityView:
    """未胜出但需要保留的少数派观点。"""

    expert_system: ExpertSystem
    claim: str
    reason_to_preserve: str
    confidence: float
    output_visibility: Literal["report_note", "internal_only", "suppressed"] = "report_note"

    def to_dict(self) -> dict[str, Any]:
        return {
            "expert_system": self.expert_system,
            "claim": self.claim,
            "reason_to_preserve": self.reason_to_preserve,
            "confidence": self.confidence,
            "output_visibility": self.output_visibility,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MinorityView":
        return cls(
            expert_system=data["expert_system"],
            claim=str(data["claim"]),
            reason_to_preserve=str(data["reason_to_preserve"]),
            confidence=float(data["confidence"]),
            output_visibility=data.get("output_visibility", "report_note"),
        )


@dataclass(frozen=True)
class ArbitrationReason:
    """裁判胜负、冲突类型与输出策略说明。"""

    winner_reason: str
    loser_reason: str = ""
    conflict_type: Literal["none", "priority", "scope", "evidence", "timing", "feedback"] = "none"
    output_strategy: OutputStrategy = "primary_only"

    def to_dict(self) -> dict[str, Any]:
        return {
            "winner_reason": self.winner_reason,
            "loser_reason": self.loser_reason,
            "conflict_type": self.conflict_type,
            "output_strategy": self.output_strategy,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ArbitrationReason":
        return cls(
            winner_reason=str(data.get("winner_reason", "")),
            loser_reason=str(data.get("loser_reason", "")),
            conflict_type=data.get("conflict_type", "none"),
            output_strategy=data.get("output_strategy", "primary_only"),
        )


@dataclass(frozen=True)
class AdjudicationResult:
    """裁判模型对单个功能域主命题的裁决结果。"""

    adjudication_id: str
    domain: DomainName
    claim: str
    decision: AdjudicationDecision
    judgements: list[ExpertJudgement]
    support_score: float
    oppose_score: float
    confidence: ParallelConfidence
    weight_profile: WeightProfile
    winning_experts: list[ExpertSystem] = field(default_factory=list)
    dissenting_experts: list[ExpertSystem] = field(default_factory=list)
    abstained_experts: list[ExpertSystem] = field(default_factory=list)
    minority_views: list[MinorityView] = field(default_factory=list)
    arbitration_reason: Optional[ArbitrationReason] = None
    feedback_state: FeedbackState = "pending"

    def to_dict(self) -> dict[str, Any]:
        return {
            "adjudication_id": self.adjudication_id,
            "domain": self.domain,
            "claim": self.claim,
            "decision": self.decision,
            "judgements": [j.to_dict() for j in self.judgements],
            "support_score": self.support_score,
            "oppose_score": self.oppose_score,
            "confidence": self.confidence.to_dict(),
            "weight_profile": self.weight_profile.to_dict(),
            "winning_experts": list(self.winning_experts),
            "dissenting_experts": list(self.dissenting_experts),
            "abstained_experts": list(self.abstained_experts),
            "minority_views": [view.to_dict() for view in self.minority_views],
            "arbitration_reason": self.arbitration_reason.to_dict() if self.arbitration_reason else None,
            "feedback_state": self.feedback_state,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AdjudicationResult":
        return cls(
            adjudication_id=str(data["adjudication_id"]),
            domain=data["domain"],
            claim=str(data["claim"]),
            decision=data["decision"],
            judgements=[ExpertJudgement.from_dict(x) for x in data.get("judgements", [])],
            support_score=float(data.get("support_score", 0.0)),
            oppose_score=float(data.get("oppose_score", 0.0)),
            confidence=ParallelConfidence.from_dict(data["confidence"]),
            weight_profile=WeightProfile.from_dict(data["weight_profile"]),
            winning_experts=list(data.get("winning_experts", [])),
            dissenting_experts=list(data.get("dissenting_experts", [])),
            abstained_experts=list(data.get("abstained_experts", [])),
            minority_views=[MinorityView.from_dict(x) for x in data.get("minority_views", [])],
            arbitration_reason=(
                ArbitrationReason.from_dict(data["arbitration_reason"])
                if data.get("arbitration_reason")
                else None
            ),
            feedback_state=data.get("feedback_state", "pending"),
        )


@dataclass(frozen=True)
class CrossExpertConflict:
    """三大专家体系之间的冲突登记。"""

    conflict_id: str
    domain: DomainName
    involved_experts: list[ExpertSystem]
    conflict_type: Literal["priority", "scope", "evidence", "timing", "feedback"]
    arbitration_reason: str
    winner: Optional[ExpertSystem] = None
    loser: Optional[ExpertSystem] = None
    output_strategy: OutputStrategy = "primary_with_minority"

    def to_dict(self) -> dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "domain": self.domain,
            "involved_experts": list(self.involved_experts),
            "conflict_type": self.conflict_type,
            "arbitration_reason": self.arbitration_reason,
            "winner": self.winner,
            "loser": self.loser,
            "output_strategy": self.output_strategy,
        }


@dataclass(frozen=True)
class DomainConsensus:
    """报告层可读的功能域最终结论。"""

    conclusion_id: str
    domain: DomainName
    headline: str
    final_statement: str
    layer: ConsensusLayer
    contributing_experts: list[ExpertSystem]
    dissenting_experts: list[ExpertSystem]
    confidence: ParallelConfidence
    evidence_items: list[EvidenceItem]
    falsifiable: str
    time_scope: Optional[TimeScope] = None
    feedback_state: FeedbackState = "pending"
    weight_profile: Optional[WeightProfile] = None
    minority_views: list[MinorityView] = field(default_factory=list)
    arbitration_reason: Optional[ArbitrationReason] = None
    output_strategy: OutputStrategy = "primary_only"

    def to_dict(self) -> dict[str, Any]:
        return {
            "conclusion_id": self.conclusion_id,
            "domain": self.domain,
            "headline": self.headline,
            "final_statement": self.final_statement,
            "layer": self.layer,
            "contributing_experts": list(self.contributing_experts),
            "dissenting_experts": list(self.dissenting_experts),
            "confidence": self.confidence.to_dict(),
            "evidence_items": [item.to_dict() for item in self.evidence_items],
            "falsifiable": self.falsifiable,
            "time_scope": self.time_scope.to_dict() if self.time_scope else None,
            "feedback_state": self.feedback_state,
            "weight_profile": self.weight_profile.to_dict() if self.weight_profile else None,
            "minority_views": [view.to_dict() for view in self.minority_views],
            "arbitration_reason": self.arbitration_reason.to_dict() if self.arbitration_reason else None,
            "output_strategy": self.output_strategy,
        }


@dataclass(frozen=True)
class DomainAnalysis:
    """一个功能域的完整多专家旁路分析结果。"""

    domain: DomainName
    readings: list[ExpertReading]
    adjudication_result: AdjudicationResult
    consensus: DomainConsensus
    conflicts: list[CrossExpertConflict] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "readings": [reading.to_dict() for reading in self.readings],
            "adjudication_result": self.adjudication_result.to_dict(),
            "consensus": self.consensus.to_dict(),
            "conflicts": [conflict.to_dict() for conflict in self.conflicts],
        }


@dataclass(frozen=True)
class ParallelAnalysisOutput:
    """多功能域旁路分析总输出。"""

    case_id: str
    domain_analyses: list[DomainAnalysis]
    schema_version: str = "parallel-domain-review-draft-2026-06-05"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "domain_analyses": [analysis.to_dict() for analysis in self.domain_analyses],
        }

    def to_json(self, *, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
