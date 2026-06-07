"""V2 Evidence 契约。

V2 的硬性原则：所有流派只产 Evidence，不直接产最终结论。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

EvidencePolarity = Literal["positive", "negative", "mixed", "neutral"]
SchoolName = Literal[
    "ziping",
    "tiaohou_ditiansui",
    "duan",
    "yang",
    "ren",
    "gao",
]


@dataclass(frozen=True)
class SchoolEvidence:
    """单一流派产出的标准证据。

    字段 domain/claim/evidence/confidence 对齐用户指定的最小 Evidence 协议，
    其余字段用于可追溯、去重与后续裁判。
    """

    evidence_id: str
    case_id: str
    source_school: SchoolName
    domain: str
    claim: str
    evidence: str
    confidence: float
    source_rule_id: str | None = None
    trace_ids: list[str] = field(default_factory=list)
    time_scope: dict[str, Any] | None = None
    polarity: EvidencePolarity = "neutral"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "case_id": self.case_id,
            "source_school": self.source_school,
            "domain": self.domain,
            "claim": self.claim,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "source_rule_id": self.source_rule_id,
            "trace_ids": list(self.trace_ids),
            "time_scope": dict(self.time_scope) if self.time_scope is not None else None,
            "polarity": self.polarity,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SchoolEvidence":
        return cls(
            evidence_id=str(data["evidence_id"]),
            case_id=str(data.get("case_id", "")),
            source_school=data["source_school"],
            domain=str(data.get("domain", "")),
            claim=str(data.get("claim", "")),
            evidence=str(data.get("evidence", "")),
            confidence=float(data.get("confidence", 0.0)),
            source_rule_id=(str(data["source_rule_id"]) if data.get("source_rule_id") is not None else None),
            trace_ids=[str(x) for x in data.get("trace_ids", [])],
            time_scope=(dict(data["time_scope"]) if data.get("time_scope") is not None else None),
            polarity=data.get("polarity", "neutral"),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class DomainEvidence:
    """Evidence Builder 归一化后的单领域证据包。"""

    case_id: str
    domain: str
    evidences: list[SchoolEvidence]
    support_score: float = 0.0
    conflict_score: float = 0.0
    coverage: dict[str, int] = field(default_factory=dict)
    normalized_confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "domain": self.domain,
            "evidences": [item.to_dict() for item in self.evidences],
            "support_score": self.support_score,
            "conflict_score": self.conflict_score,
            "coverage": dict(self.coverage),
            "normalized_confidence": self.normalized_confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DomainEvidence":
        return cls(
            case_id=str(data.get("case_id", "")),
            domain=str(data.get("domain", "")),
            evidences=[SchoolEvidence.from_dict(x) for x in data.get("evidences", [])],
            support_score=float(data.get("support_score", 0.0)),
            conflict_score=float(data.get("conflict_score", 0.0)),
            coverage={str(k): int(v) for k, v in data.get("coverage", {}).items()},
            normalized_confidence=float(data.get("normalized_confidence", 0.0)),
        )
