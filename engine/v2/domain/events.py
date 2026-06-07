"""V2 事件候选契约。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EventCandidate:
    """由领域推理结果映射出的结构化事件候选，不等同最终断语。"""

    event_id: str
    case_id: str
    domain: str
    event_type: str
    title: str
    description: str
    source_claim: str
    evidence_ids: list[str] = field(default_factory=list)
    confidence: float = 0.0
    polarity: str = "neutral"
    tags: list[str] = field(default_factory=list)
    time_scope: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "case_id": self.case_id,
            "domain": self.domain,
            "event_type": self.event_type,
            "title": self.title,
            "description": self.description,
            "source_claim": self.source_claim,
            "evidence_ids": list(self.evidence_ids),
            "confidence": self.confidence,
            "polarity": self.polarity,
            "tags": list(self.tags),
            "time_scope": dict(self.time_scope) if self.time_scope is not None else None,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EventCandidate":
        return cls(
            event_id=str(data.get("event_id", "")),
            case_id=str(data.get("case_id", "")),
            domain=str(data.get("domain", "")),
            event_type=str(data.get("event_type", "")),
            title=str(data.get("title", "")),
            description=str(data.get("description", "")),
            source_claim=str(data.get("source_claim", "")),
            evidence_ids=[str(x) for x in data.get("evidence_ids", [])],
            confidence=float(data.get("confidence", 0.0)),
            polarity=str(data.get("polarity", "neutral")),
            tags=[str(x) for x in data.get("tags", [])],
            time_scope=dict(data["time_scope"]) if data.get("time_scope") is not None else None,
            metadata=dict(data.get("metadata", {})),
        )
