"""V2 领域 Agent 测试。"""

from __future__ import annotations

import pytest

from engine.v2.agents import (
    CareerAgent,
    EducationAgent,
    FamilyAgent,
    HealthAgent,
    MarriageAgent,
    WealthAgent,
    run_domain_agents,
)
from engine.v2.domain.agents import DomainReasoningResult
from engine.v2.domain.evidence import DomainEvidence, SchoolEvidence


def _ev(domain: str, *, evidence_id: str = "ev-1", polarity: str = "positive", confidence: float = 0.8) -> SchoolEvidence:
    return SchoolEvidence(
        evidence_id=evidence_id,
        case_id="C-test",
        source_school="ziping",
        domain=domain,
        claim=f"{domain} claim",
        evidence=f"{domain} evidence",
        confidence=confidence,
        polarity=polarity,
    )


def _domain_evidence(domain: str, evidences: list[SchoolEvidence] | None = None) -> DomainEvidence:
    items = evidences if evidences is not None else [_ev(domain)]
    return DomainEvidence(
        case_id="C-test",
        domain=domain,
        evidences=items,
        support_score=sum(ev.confidence for ev in items if ev.polarity == "positive"),
        conflict_score=sum(ev.confidence for ev in items if ev.polarity == "negative"),
        coverage={"ziping": len(items)},
        normalized_confidence=0.72,
    )


@pytest.mark.parametrize(
    ("agent_cls", "domain"),
    [
        (CareerAgent, "career"),
        (WealthAgent, "wealth"),
        (MarriageAgent, "marriage"),
        (HealthAgent, "health"),
        (FamilyAgent, "family"),
        (EducationAgent, "education"),
    ],
)
def test_each_domain_agent_returns_reasoning_result(agent_cls, domain):
    result = agent_cls().analyze(_domain_evidence(domain))
    assert isinstance(result, DomainReasoningResult)
    assert result.case_id == "C-test"
    assert result.domain == domain
    assert result.confidence == 0.72
    assert result.main_claims


def test_domain_agent_preserves_evidence_ids():
    de = _domain_evidence("career", [_ev("career", evidence_id="ev-a"), _ev("career", evidence_id="ev-b")])
    result = CareerAgent().analyze(de)
    assert result.evidence_ids == ["ev-a", "ev-b"]


def test_domain_agent_splits_negative_evidence_to_risks():
    de = _domain_evidence(
        "wealth",
        [
            _ev("wealth", evidence_id="ev-pos", polarity="positive"),
            _ev("wealth", evidence_id="ev-neg", polarity="negative", confidence=0.6),
        ],
    )
    result = WealthAgent().analyze(de)
    assert result.main_claims == ["wealth claim"]
    assert result.risk_claims == ["wealth claim"]
    assert result.opportunity_claims == ["wealth claim"]


def test_run_domain_agents_ignores_unknown_domains():
    results = run_domain_agents([_domain_evidence("career"), _domain_evidence("unknown")])
    assert [item.domain for item in results] == ["career"]
