"""V2 案例相似度契约。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SimilarCaseProfile:
    """用于相似度计算的轻量案例画像。"""

    case_id: str
    domains: list[str] = field(default_factory=list)
    event_types: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "domains": list(self.domains),
            "event_types": list(self.event_types),
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SimilarCaseProfile":
        return cls(
            case_id=str(data.get("case_id", "")),
            domains=[str(x) for x in data.get("domains", [])],
            event_types=[str(x) for x in data.get("event_types", [])],
            tags=[str(x) for x in data.get("tags", [])],
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class SimilarCase:
    """V2 相似案例候选。只作参考证据，不等同最终裁判。"""

    case_id: str
    score: float
    matched_domains: list[str] = field(default_factory=list)
    matched_event_types: list[str] = field(default_factory=list)
    matched_tags: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "score": self.score,
            "matched_domains": list(self.matched_domains),
            "matched_event_types": list(self.matched_event_types),
            "matched_tags": list(self.matched_tags),
            "reasons": list(self.reasons),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SimilarCase":
        return cls(
            case_id=str(data.get("case_id", "")),
            score=float(data.get("score", 0.0)),
            matched_domains=[str(x) for x in data.get("matched_domains", [])],
            matched_event_types=[str(x) for x in data.get("matched_event_types", [])],
            matched_tags=[str(x) for x in data.get("matched_tags", [])],
            reasons=[str(x) for x in data.get("reasons", [])],
            metadata=dict(data.get("metadata", {})),
        )
