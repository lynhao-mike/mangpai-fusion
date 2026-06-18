"""engine/domain/prediction.py · v4.2 预测层领域实体

仅含纯数据结构（dataclass），无 I/O、无业务逻辑。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ZipingPredictionSignal:
    """D1 + 理论规则 → 结构压力信号（0-1）。"""
    career_pressure: float
    wealth_activity: float
    relationship_tension: float
    day_master_strength: float
    rule_signal_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "career_pressure": round(self.career_pressure, 4),
            "wealth_activity": round(self.wealth_activity, 4),
            "relationship_tension": round(self.relationship_tension, 4),
            "day_master_strength": round(self.day_master_strength, 4),
            "rule_signal_count": self.rule_signal_count,
        }


@dataclass
class DttPredictionSignal:
    """D2 调候 / 气势 → 风险区间信号（0-1）。"""
    imbalance_index: float
    seasonal_pressure: float
    transformation_likelihood: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "imbalance_index": round(self.imbalance_index, 4),
            "seasonal_pressure": round(self.seasonal_pressure, 4),
            "transformation_likelihood": round(self.transformation_likelihood, 4),
        }


@dataclass
class SymbolicEventCandidate:
    symbol: str
    meaning_candidates: list[str]
    probability_weight: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "meaning_candidates": self.meaning_candidates,
            "probability_weight": round(self.probability_weight, 4),
        }


@dataclass
class MpPredictionSignal:
    """D1-D3 应期触发 → 象法候选事件信号。"""
    symbolic_events: list[SymbolicEventCandidate] = field(default_factory=list)
    max_passed_layers: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbolic_events": [e.to_dict() for e in self.symbolic_events],
            "max_passed_layers": self.max_passed_layers,
        }


@dataclass
class EventCandidate:
    event: str
    probability: float
    source_school: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "probability": round(self.probability, 4),
            "source_school": self.source_school,
        }


@dataclass
class FinalPrediction:
    event_candidates: list[EventCandidate] = field(default_factory=list)
    explanation_chain: dict[str, Any] = field(default_factory=dict)
    conflict_resolution_used: bool = False
    overall_confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_candidates": [e.to_dict() for e in self.event_candidates],
            "explanation_chain": self.explanation_chain,
            "conflict_resolution_used": self.conflict_resolution_used,
            "overall_confidence": round(self.overall_confidence, 4),
        }


@dataclass
class TimeWindow:
    start_year: int
    end_year: int
    peak_year: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_year": self.start_year,
            "end_year": self.end_year,
            "peak_year": self.peak_year,
        }


@dataclass
class PredictionOutput:
    """v4.2 最终预测输出，挂载到 AnalysisOutput 动态属性 ``prediction``。"""
    event_candidates: list[dict[str, Any]] = field(default_factory=list)
    probability_distribution: dict[str, float] = field(default_factory=dict)
    time_window: dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    explanation_chain: dict[str, Any] = field(default_factory=dict)
    conflict_resolution_used: bool = False
    learning_feedback_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_candidates": self.event_candidates,
            "probability_distribution": {
                k: round(v, 4) for k, v in self.probability_distribution.items()
            },
            "time_window": self.time_window,
            "confidence_score": round(self.confidence_score, 4),
            "explanation_chain": self.explanation_chain,
            "conflict_resolution_used": self.conflict_resolution_used,
            "learning_feedback_id": self.learning_feedback_id,
        }
