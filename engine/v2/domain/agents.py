"""V2 领域推理结果契约。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DomainReasoningResult:
    """单领域 Agent 推理输出。Agent 只基于 DomainEvidence，不直接读取规则库。"""

    case_id: str
    domain: str
    main_claims: list[str] = field(default_factory=list)
    risk_claims: list[str] = field(default_factory=list)
    opportunity_claims: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    confidence: float = 0.0
    reasoning_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "domain": self.domain,
            "main_claims": list(self.main_claims),
            "risk_claims": list(self.risk_claims),
            "opportunity_claims": list(self.opportunity_claims),
            "evidence_ids": list(self.evidence_ids),
            "confidence": self.confidence,
            "reasoning_notes": list(self.reasoning_notes),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DomainReasoningResult":
        return cls(
            case_id=str(data.get("case_id", "")),
            domain=str(data.get("domain", "")),
            main_claims=[str(x) for x in data.get("main_claims", [])],
            risk_claims=[str(x) for x in data.get("risk_claims", [])],
            opportunity_claims=[str(x) for x in data.get("opportunity_claims", [])],
            evidence_ids=[str(x) for x in data.get("evidence_ids", [])],
            confidence=float(data.get("confidence", 0.0)),
            reasoning_notes=[str(x) for x in data.get("reasoning_notes", [])],
        )
