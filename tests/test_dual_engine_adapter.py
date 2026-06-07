from __future__ import annotations

from engine.application.dual_engine_adapter import analyze_dual_engine
from engine.domain.analysis import AnalysisOutput
from engine.domain.dual_engine import BlindFindings, FusionFindings, TheoryFindings
from engine.pipeline import run_pipeline
from tests.fixtures.cases import load_case


def test_dual_engine_adapter_outputs_three_layers() -> None:
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    output = run_pipeline(parsed, write_findings=False)

    theory, blind, fusion = analyze_dual_engine(
        parsed=parsed,
        energy=output.energy,
        picture=output.picture,
        gate_results=output.gate_results,
        support=output.support,
        parallel_analysis=output.parallel_analysis,
    )

    assert isinstance(theory, TheoryFindings)
    assert isinstance(blind, BlindFindings)
    assert isinstance(fusion, FusionFindings)
    assert theory.case_id == output.case_id
    assert blind.case_id == output.case_id
    assert fusion.case_id == output.case_id
    assert theory.triggered_rules
    assert blind.energy_summary["layer_count"] == output.energy.layer_count
    assert fusion.parallel_analysis is output.parallel_analysis
    assert fusion.conclusions


def test_run_pipeline_attaches_dual_engine_findings() -> None:
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    output = run_pipeline(parsed, write_findings=False)

    assert isinstance(output.theory_findings, TheoryFindings)
    assert isinstance(output.blind_findings, BlindFindings)
    assert isinstance(output.fusion_findings, FusionFindings)
    assert output.parallel_analysis is output.fusion_findings.parallel_analysis


def test_analysis_output_round_trips_dual_engine_findings() -> None:
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    output = run_pipeline(parsed, write_findings=False)

    restored = AnalysisOutput.from_dict(output.to_dict())

    assert isinstance(restored.theory_findings, TheoryFindings)
    assert isinstance(restored.blind_findings, BlindFindings)
    assert isinstance(restored.fusion_findings, FusionFindings)
    assert restored.theory_findings.evidence_rule_ids == output.theory_findings.evidence_rule_ids
    assert restored.blind_findings.upstream_hashes == output.blind_findings.upstream_hashes
    assert restored.fusion_findings.parallel_analysis is not None
    assert restored.fusion_findings.conclusions == output.fusion_findings.conclusions
