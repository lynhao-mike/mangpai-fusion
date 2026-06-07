"""V2 Evidence Builder 与适配器测试。"""

from __future__ import annotations

from engine.v2.evidence.builder import build_domain_evidences
from engine.v2.domain.evidence import SchoolEvidence


def _ev(school, domain, confidence=0.7, polarity="positive", evidence_id=None):
    return SchoolEvidence(
        evidence_id=evidence_id or f"v2ev-{school}-{domain}",
        case_id="C-test",
        source_school=school,
        domain=domain,
        claim=f"{school} claim",
        evidence=f"{school} evidence",
        confidence=confidence,
        polarity=polarity,
    )


def test_build_domain_evidences_groups_by_domain():
    evs = [_ev("ziping", "career"), _ev("duan", "career"), _ev("yang", "wealth")]
    result = build_domain_evidences(evs)
    domains = {de.domain for de in result}
    assert "career" in domains and "wealth" in domains


def test_build_domain_evidences_coverage():
    evs = [_ev("ziping", "career"), _ev("duan", "career")]
    result = build_domain_evidences(evs)
    career = next(de for de in result if de.domain == "career")
    assert career.coverage == {"duan": 1, "ziping": 1}


def test_build_domain_evidences_deduplicates():
    ev = _ev("ziping", "career", evidence_id="dup-id")
    result = build_domain_evidences([ev, ev])
    career = next(de for de in result if de.domain == "career")
    assert len(career.evidences) == 1


def test_build_domain_evidences_conflict_score():
    evs = [
        _ev("ziping", "career", confidence=0.8, polarity="positive"),
        _ev("duan", "career", confidence=0.6, polarity="negative"),
    ]
    result = build_domain_evidences(evs)
    career = next(de for de in result if de.domain == "career")
    assert career.conflict_score > 0
    assert career.support_score > 0


def test_build_domain_evidences_empty():
    assert build_domain_evidences([]) == []
