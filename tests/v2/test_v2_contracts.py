"""V2 数据契约测试：SchoolEvidence / DomainEvidence / V2AnalysisOutput round-trip。"""

from __future__ import annotations

import pytest

from engine.v2.domain.evidence import DomainEvidence, SchoolEvidence
from engine.v2.domain.output import V2AnalysisOutput
from engine.v2 import V2_SCHEMA_VERSION


def _sample_school_evidence(**kwargs) -> SchoolEvidence:
    defaults = dict(
        evidence_id="v2ev-abc123",
        case_id="C-2026-001",
        source_school="ziping",
        domain="career",
        claim="日主得令可从事管理。",
        evidence="日主壬水，月令亥水，得令旺相。",
        confidence=0.75,
        source_rule_id="ZP-PROD-20260605-001",
        trace_ids=["ZP-PROD-20260605-001"],
        polarity="positive",
        metadata={"title": "测试规则"},
    )
    defaults.update(kwargs)
    return SchoolEvidence(**defaults)


def test_school_evidence_round_trip():
    ev = _sample_school_evidence()
    assert SchoolEvidence.from_dict(ev.to_dict()) == ev


def test_school_evidence_minimal():
    ev = SchoolEvidence.from_dict({"evidence_id": "x", "source_school": "duan"})
    assert ev.domain == ""
    assert ev.confidence == 0.0
    assert ev.polarity == "neutral"
    assert ev.trace_ids == []


def test_school_evidence_time_scope_round_trip():
    ev = _sample_school_evidence(time_scope={"type": "liunian", "label": "2026", "start_year": 2026, "end_year": 2026})
    restored = SchoolEvidence.from_dict(ev.to_dict())
    assert restored.time_scope == ev.time_scope


def test_domain_evidence_round_trip():
    de = DomainEvidence(
        case_id="C-2026-001",
        domain="career",
        evidences=[_sample_school_evidence()],
        support_score=0.75,
        conflict_score=0.0,
        coverage={"ziping": 1},
        normalized_confidence=0.68,
    )
    assert DomainEvidence.from_dict(de.to_dict()) == de


def test_domain_evidence_empty():
    de = DomainEvidence.from_dict({"case_id": "C-x", "domain": "general"})
    assert de.evidences == []
    assert de.normalized_confidence == 0.0


def test_v2_output_round_trip():
    ev = _sample_school_evidence()
    de = DomainEvidence(case_id="C-2026-001", domain="career", evidences=[ev])
    out = V2AnalysisOutput(case_id="C-2026-001", school_evidences=[ev], domain_evidences=[de])
    restored = V2AnalysisOutput.from_dict(out.to_dict())
    assert restored == out


def test_v2_output_schema_version():
    out = V2AnalysisOutput(case_id="C-2026-001")
    assert out.schema_version == V2_SCHEMA_VERSION


def test_v2_output_json_round_trip():
    ev = _sample_school_evidence()
    out = V2AnalysisOutput(case_id="C-2026-001", school_evidences=[ev])
    assert V2AnalysisOutput.from_json(out.to_json()) == out


def test_v2_output_hash_stable():
    out = V2AnalysisOutput(case_id="C-2026-001")
    assert out.hash() == out.hash()
    assert len(out.hash()) == 16
