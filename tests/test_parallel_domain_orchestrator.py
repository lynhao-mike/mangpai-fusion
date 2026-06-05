from __future__ import annotations

from engine.application.parallel_domain_orchestrator import analyze_parallel_domains
from engine.domain.analysis import AnalysisOutput
from engine.domain.parallel import ParallelAnalysisOutput
from engine.pipeline import run_pipeline
from tests.fixtures.cases import load_case
from tools.render_report import render_from_output


def test_parallel_domain_orchestrator_outputs_all_default_domains() -> None:
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    output = run_pipeline(parsed, write_findings=False)

    parallel = output.parallel_analysis

    assert parallel is not None
    assert isinstance(parallel, ParallelAnalysisOutput)
    assert [analysis.domain for analysis in parallel.domain_analyses] == [
        "学业",
        "事业",
        "财运",
        "婚姻",
        "健康",
        "性格",
    ]
    assert all(analysis.readings for analysis in parallel.domain_analyses)
    assert any(
        reading.expert_system == "ziping" and reading.stance == "support"
        for analysis in parallel.domain_analyses
        for reading in analysis.readings
    )
    assert any(
        reading.expert_system == "tiaohou_ditiansui" and reading.stance == "support"
        for analysis in parallel.domain_analyses
        for reading in analysis.readings
    )


def test_analysis_output_round_trips_parallel_analysis() -> None:
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    output = run_pipeline(parsed, write_findings=False)

    restored = AnalysisOutput.from_dict(output.to_dict())

    assert restored.parallel_analysis is not None
    assert restored.parallel_analysis.case_id == output.case_id
    assert len(restored.parallel_analysis.domain_analyses) == 6
    assert restored.to_dict()["parallel_analysis"]["domain_analyses"]


def test_parallel_domain_render_and_statement_index(tmp_path) -> None:
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    output = run_pipeline(parsed, write_findings=False)

    report = render_from_output(
        output,
        lint_before=False,
        cases_dir=tmp_path,
        skip_findings_save=True,
    )

    assert "### 多专家功能域裁判（v1.5 旁路）" in report
    assert "| 功能域 | 裁判层级 | 主结论 | 采纳专家 | 置信 | 证据 |" in report

    statement_index = tmp_path / output.case_id / "statement_index.json"
    data = statement_index.read_text(encoding="utf-8")
    assert "parallel_domain_adjudication" in data
    assert "reading_ids" in data
    assert "adjudication_id" in data
