"""ZiPing Fusion Engine v5 数据契约。

v5 的核心产物不是报告文本，而是五派命题、结构图、仲裁结果、
受限概率预测账本与学习信号。该模块只定义可序列化的数据对象，
不实现具体命理规则。
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Literal

V5_SCHEMA_VERSION = "5.0.0-five-school-mvp"

V5School = Literal[
    "ziping",
    "ditiansui",
    "gao_dechen",
    "duan_jianye",
    "yang_qingjuan",
]

V5_SCHOOLS: tuple[str, ...] = (
    "ziping",
    "ditiansui",
    "gao_dechen",
    "duan_jianye",
    "yang_qingjuan",
)

V5SchoolRole = Literal[
    "structure_law",
    "qi_momentum",
    "work_transformation",
    "event_framework",
    "image_detail",
]

V5_SCHOOL_ROLES: dict[str, str] = {
    "ziping": "structure_law",
    "ditiansui": "qi_momentum",
    "gao_dechen": "work_transformation",
    "duan_jianye": "event_framework",
    "yang_qingjuan": "image_detail",
}

V5ClaimType = Literal[
    "structure_claim",
    "event_claim",
    "timing_claim",
    "evidence_claim",
    "counter_claim",
]

V5Stance = Literal["support", "oppose", "mixed", "abstain"]
V5Polarity = Literal["positive", "negative", "mixed", "neutral"]
V5ArbitrationStage = Literal[
    "structure_legality",
    "event_realization",
    "probability_timing",
]
V5FeedbackState = Literal["pending", "hit", "miss", "partial", "skipped"]


@dataclass(frozen=True)
class V5Confidence:
    """v5 双轨置信度：等级与百分比并存，但不等同于事件概率。"""

    tier: str = "★★"
    score: float = 0.5
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"tier": self.tier, "score": self.score, "note": self.note}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "V5Confidence":
        if data is None:
            return cls()
        return cls(
            tier=str(data.get("tier", "★★")),
            score=float(data.get("score", 0.5)),
            note=str(data.get("note", "")),
        )


@dataclass(frozen=True)
class V5Evidence:
    """结构图中的可追溯证据片段。"""

    evidence_id: str
    source: str
    text: str
    node_refs: list[str] = field(default_factory=list)
    rule_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "text": self.text,
            "node_refs": list(self.node_refs),
            "rule_ids": list(self.rule_ids),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "V5Evidence":
        return cls(
            evidence_id=str(data["evidence_id"]),
            source=str(data.get("source", "")),
            text=str(data.get("text", "")),
            node_refs=[str(x) for x in data.get("node_refs", [])],
            rule_ids=[str(x) for x in data.get("rule_ids", [])],
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class V5Claim:
    """五派独立 runner 的唯一标准输出。"""

    claim_id: str
    school: V5School
    domain: str
    claim: str
    claim_type: V5ClaimType
    stance: V5Stance = "support"
    polarity: V5Polarity = "neutral"
    confidence: V5Confidence = field(default_factory=V5Confidence)
    evidence: list[V5Evidence] = field(default_factory=list)
    counter_evidence: list[V5Evidence] = field(default_factory=list)
    timing_hints: list[dict[str, Any]] = field(default_factory=list)
    probabilistic: bool = False
    falsifiable: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def role(self) -> str:
        return V5_SCHOOL_ROLES[self.school]

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "school": self.school,
            "school_role": self.role,
            "domain": self.domain,
            "claim": self.claim,
            "claim_type": self.claim_type,
            "stance": self.stance,
            "polarity": self.polarity,
            "confidence": self.confidence.to_dict(),
            "evidence": [item.to_dict() for item in self.evidence],
            "counter_evidence": [item.to_dict() for item in self.counter_evidence],
            "timing_hints": [dict(item) for item in self.timing_hints],
            "probabilistic": self.probabilistic,
            "falsifiable": self.falsifiable,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "V5Claim":
        return cls(
            claim_id=str(data["claim_id"]),
            school=data["school"],
            domain=str(data.get("domain", "")),
            claim=str(data.get("claim", "")),
            claim_type=data.get("claim_type", "event_claim"),
            stance=data.get("stance", "support"),
            polarity=data.get("polarity", "neutral"),
            confidence=V5Confidence.from_dict(data.get("confidence")),
            evidence=[V5Evidence.from_dict(x) for x in data.get("evidence", [])],
            counter_evidence=[V5Evidence.from_dict(x) for x in data.get("counter_evidence", [])],
            timing_hints=[dict(x) for x in data.get("timing_hints", [])],
            probabilistic=bool(data.get("probabilistic", False)),
            falsifiable=str(data.get("falsifiable", "")),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class V5StructureGraph:
    """v5 命题图：chart、claim、evidence、domain 与关系边。"""

    case_id: str
    nodes: list[dict[str, Any]] = field(default_factory=list)
    edges: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "nodes": [dict(item) for item in self.nodes],
            "edges": [dict(item) for item in self.edges],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "V5StructureGraph":
        return cls(
            case_id=str(data.get("case_id", "")),
            nodes=[dict(x) for x in data.get("nodes", [])],
            edges=[dict(x) for x in data.get("edges", [])],
        )


@dataclass(frozen=True)
class V5ArbitrationResult:
    """三段式仲裁结果。"""

    domain: str
    stage: V5ArbitrationStage
    conclusion: str
    winning_schools: list[str] = field(default_factory=list)
    minority_claims: list[str] = field(default_factory=list)
    support_score: float = 0.0
    opposition_score: float = 0.0
    conflict_type: str = "none"
    confidence: V5Confidence = field(default_factory=V5Confidence)
    rationale: str = ""
    probabilistic_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "stage": self.stage,
            "conclusion": self.conclusion,
            "winning_schools": list(self.winning_schools),
            "minority_claims": list(self.minority_claims),
            "support_score": self.support_score,
            "opposition_score": self.opposition_score,
            "conflict_type": self.conflict_type,
            "confidence": self.confidence.to_dict(),
            "rationale": self.rationale,
            "probabilistic_allowed": self.probabilistic_allowed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "V5ArbitrationResult":
        return cls(
            domain=str(data.get("domain", "")),
            stage=data.get("stage", "event_realization"),
            conclusion=str(data.get("conclusion", "")),
            winning_schools=[str(x) for x in data.get("winning_schools", [])],
            minority_claims=[str(x) for x in data.get("minority_claims", [])],
            support_score=float(data.get("support_score", 0.0)),
            opposition_score=float(data.get("opposition_score", 0.0)),
            conflict_type=str(data.get("conflict_type", "none")),
            confidence=V5Confidence.from_dict(data.get("confidence")),
            rationale=str(data.get("rationale", "")),
            probabilistic_allowed=bool(data.get("probabilistic_allowed", False)),
        )


@dataclass(frozen=True)
class V5Prediction:
    """受限概率预测条目。

    prediction-first 要求主要事件先登记预测，再等待反馈校准。
    因此预测条目必须携带时间窗、触发条件、证伪口径与反馈状态。
    """

    prediction_id: str
    domain: str
    event_label: str
    probability_range: tuple[float, float]
    confidence: V5Confidence
    time_window: dict[str, Any] = field(default_factory=dict)
    trigger_conditions: list[str] = field(default_factory=list)
    falsifier: str = ""
    calibration_note: str = ""
    feedback_state: V5FeedbackState = "pending"

    def to_dict(self) -> dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "domain": self.domain,
            "event_label": self.event_label,
            "probability_range": list(self.probability_range),
            "confidence": self.confidence.to_dict(),
            "time_window": dict(self.time_window),
            "trigger_conditions": list(self.trigger_conditions),
            "falsifier": self.falsifier,
            "calibration_note": self.calibration_note,
            "feedback_state": self.feedback_state,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "V5Prediction":
        raw_range = data.get("probability_range", [0.0, 0.0])
        return cls(
            prediction_id=str(data["prediction_id"]),
            domain=str(data.get("domain", "")),
            event_label=str(data.get("event_label", "")),
            probability_range=(float(raw_range[0]), float(raw_range[1])),
            confidence=V5Confidence.from_dict(data.get("confidence")),
            time_window=dict(data.get("time_window", {})),
            trigger_conditions=[str(x) for x in data.get("trigger_conditions", [])],
            falsifier=str(data.get("falsifier", "")),
            calibration_note=str(data.get("calibration_note", "")),
            feedback_state=data.get("feedback_state", "pending"),
        )


@dataclass(frozen=True)
class V5PredictionLedger:
    """v5 可反馈预测账本。"""

    case_id: str
    predictions: list[V5Prediction] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "predictions": [item.to_dict() for item in self.predictions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "V5PredictionLedger":
        return cls(
            case_id=str(data.get("case_id", "")),
            predictions=[V5Prediction.from_dict(x) for x in data.get("predictions", [])],
        )


@dataclass(frozen=True)
class V5LearningSignal:
    """反馈学习前置记录；小样本阶段只记录，不自动改核心规则。"""

    signal_id: str
    case_id: str
    target_id: str
    signal_type: str
    value: str
    note: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "case_id": self.case_id,
            "target_id": self.target_id,
            "signal_type": self.signal_type,
            "value": self.value,
            "note": self.note,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "V5LearningSignal":
        return cls(
            signal_id=str(data["signal_id"]),
            case_id=str(data.get("case_id", "")),
            target_id=str(data.get("target_id", "")),
            signal_type=str(data.get("signal_type", "")),
            value=str(data.get("value", "")),
            note=str(data.get("note", "")),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class V5Output:
    """v5 并行核心完整输出。"""

    case_id: str
    chart: dict[str, Any] = field(default_factory=dict)
    claims: list[V5Claim] = field(default_factory=list)
    structure_graph: V5StructureGraph = field(default_factory=lambda: V5StructureGraph(case_id=""))
    arbitration_results: list[V5ArbitrationResult] = field(default_factory=list)
    prediction_ledger: V5PredictionLedger = field(default_factory=lambda: V5PredictionLedger(case_id=""))
    learning_signals: list[V5LearningSignal] = field(default_factory=list)
    schema_version: str = V5_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "chart": dict(self.chart),
            "claims": [item.to_dict() for item in self.claims],
            "structure_graph": self.structure_graph.to_dict(),
            "arbitration_results": [item.to_dict() for item in self.arbitration_results],
            "prediction_ledger": self.prediction_ledger.to_dict(),
            "learning_signals": [item.to_dict() for item in self.learning_signals],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "V5Output":
        case_id = str(data.get("case_id", ""))
        return cls(
            case_id=case_id,
            chart=dict(data.get("chart", {})),
            claims=[V5Claim.from_dict(x) for x in data.get("claims", [])],
            structure_graph=V5StructureGraph.from_dict(data.get("structure_graph", {"case_id": case_id})),
            arbitration_results=[V5ArbitrationResult.from_dict(x) for x in data.get("arbitration_results", [])],
            prediction_ledger=V5PredictionLedger.from_dict(data.get("prediction_ledger", {"case_id": case_id})),
            learning_signals=[V5LearningSignal.from_dict(x) for x in data.get("learning_signals", [])],
            schema_version=str(data.get("schema_version", V5_SCHEMA_VERSION)),
        )

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_json(cls, value: str) -> "V5Output":
        return cls.from_dict(json.loads(value))

    def hash(self) -> str:
        canonical = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
