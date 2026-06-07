"""V2 领域 Agent 基类与六个领域 Agent 实现。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from engine.v2.domain.agents import DomainReasoningResult
from engine.v2.domain.evidence import DomainEvidence


class BaseDomainAgent(ABC):
    """所有领域 Agent 的基类。只接收 DomainEvidence，不直接读取规则库。"""

    @property
    @abstractmethod
    def domain(self) -> str: ...

    def analyze(self, domain_evidence: DomainEvidence) -> DomainReasoningResult:
        ev_ids = [e.evidence_id for e in domain_evidence.evidences]
        main, risks, opps = self._reason(domain_evidence)
        return DomainReasoningResult(
            case_id=domain_evidence.case_id,
            domain=self.domain,
            main_claims=main,
            risk_claims=risks,
            opportunity_claims=opps,
            evidence_ids=ev_ids,
            confidence=round(domain_evidence.normalized_confidence, 4),
            reasoning_notes=[f"基于 {len(ev_ids)} 条证据推理，coverage={list(domain_evidence.coverage.keys())}"],
        )

    def _reason(self, de: DomainEvidence) -> tuple[list[str], list[str], list[str]]:
        pos = [e.claim for e in de.evidences if e.polarity == "positive" and e.claim]
        neg = [e.claim for e in de.evidences if e.polarity == "negative" and e.claim]
        neu = [e.claim for e in de.evidences if e.polarity not in ("positive", "negative") and e.claim]
        return pos or neu[:3], neg[:3], pos[:2] if neg else []


class CareerAgent(BaseDomainAgent):
    domain = "career"


class WealthAgent(BaseDomainAgent):
    domain = "wealth"


class MarriageAgent(BaseDomainAgent):
    domain = "marriage"


class HealthAgent(BaseDomainAgent):
    domain = "health"


class FamilyAgent(BaseDomainAgent):
    domain = "family"


class EducationAgent(BaseDomainAgent):
    domain = "education"


_REGISTRY: dict[str, BaseDomainAgent] = {
    "career": CareerAgent(),
    "wealth": WealthAgent(),
    "marriage": MarriageAgent(),
    "health": HealthAgent(),
    "family": FamilyAgent(),
    "education": EducationAgent(),
}


def run_domain_agents(domain_evidences: list[DomainEvidence]) -> list[DomainReasoningResult]:
    """对每个有匹配 Agent 的领域 DomainEvidence 运行推理。"""
    results: list[DomainReasoningResult] = []
    for de in domain_evidences:
        agent = _REGISTRY.get(de.domain)
        if agent is not None:
            results.append(agent.analyze(de))
    return results
