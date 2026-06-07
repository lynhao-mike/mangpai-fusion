"""V2 pipeline 兼容性测试：确保旧链路完全不受影响。"""

from __future__ import annotations

from tests.fixtures.cases import load_case
from engine.application.pipeline_runner import run_pipeline
from engine.v2.application.runner import run_v2_reasoning
from engine.v2.domain.agents import DomainReasoningResult
from engine.v2.domain.output import V2AnalysisOutput
from engine.v2.domain.evidence import SchoolEvidence, DomainEvidence
from engine.v2.domain.events import EventCandidate


def test_run_pipeline_result_unchanged():
    """run_pipeline 引入 V2 runner 前后结果应相同。"""
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    out = run_pipeline(parsed)
    assert out.case_id
    assert out.energy is not None
    assert out.picture is not None


def test_run_v2_reasoning_returns_v2_output():
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    out = run_pipeline(parsed)
    v2 = run_v2_reasoning(
        parsed=parsed,
        energy=out.energy,
        picture=out.picture,
        gate_results=out.gate_results,
        support=out.support,
    )
    assert isinstance(v2, V2AnalysisOutput)
    assert v2.case_id == out.case_id or v2.case_id == ""


def test_v2_school_evidences_are_school_evidence_instances():
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    out = run_pipeline(parsed)
    v2 = run_v2_reasoning(
        parsed=parsed,
        energy=out.energy,
        picture=out.picture,
        gate_results=out.gate_results,
        support=out.support,
    )
    assert all(isinstance(ev, SchoolEvidence) for ev in v2.school_evidences)


def test_v2_domain_evidences_are_domain_evidence_instances():
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    out = run_pipeline(parsed)
    v2 = run_v2_reasoning(
        parsed=parsed,
        energy=out.energy,
        picture=out.picture,
        gate_results=out.gate_results,
        support=out.support,
    )
    assert all(isinstance(de, DomainEvidence) for de in v2.domain_evidences)
    assert len(v2.domain_evidences) > 0


def test_v2_event_candidates_are_event_candidate_instances():
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    out = run_pipeline(parsed)
    v2 = run_v2_reasoning(
        parsed=parsed,
        energy=out.energy,
        picture=out.picture,
        gate_results=out.gate_results,
        support=out.support,
    )
    assert all(isinstance(event, EventCandidate) for event in v2.event_candidates)
    assert len(v2.event_candidates) > 0


def test_v2_domain_results_are_reasoning_result_instances():
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    out = run_pipeline(parsed)
    v2 = run_v2_reasoning(
        parsed=parsed,
        energy=out.energy,
        picture=out.picture,
        gate_results=out.gate_results,
        support=out.support,
    )
    assert all(isinstance(result, DomainReasoningResult) for result in v2.domain_results)
    assert len(v2.domain_results) > 0


def test_v2_evidences_do_not_produce_final_conclusions():
    """V2 M2 阶段只输出领域推理结果，不应自动生成最终结论。"""
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    out = run_pipeline(parsed)
    v2 = run_v2_reasoning(
        parsed=parsed,
        energy=out.energy,
        picture=out.picture,
        gate_results=out.gate_results,
        support=out.support,
    )
    assert v2.final_conclusions == []
    assert v2.arbitration_results == []


def test_v2_output_round_trip():
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    out = run_pipeline(parsed)
    v2 = run_v2_reasoning(
        parsed=parsed,
        energy=out.energy,
        picture=out.picture,
        gate_results=out.gate_results,
        support=out.support,
    )
    restored = V2AnalysisOutput.from_json(v2.to_json())
    assert restored.case_id == v2.case_id
    assert len(restored.school_evidences) == len(v2.school_evidences)
    assert len(restored.domain_evidences) == len(v2.domain_evidences)
    assert len(restored.domain_results) == len(v2.domain_results)
    assert len(restored.event_candidates) == len(v2.event_candidates)
