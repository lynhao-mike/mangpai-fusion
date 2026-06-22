from __future__ import annotations

import inspect
from typing import Any, cast

from engine.application.parallel_domain_orchestrator import analyze_parallel_domains
from engine.domain.analysis import AnalysisOutput
from engine.application.production_rule_loader import ProductionRuleLibrary
from engine.domain.parallel import ParallelAnalysisOutput
from engine.energy.types import EnergyFindings
from engine.pangzheng.types import SupportFindings
from engine.picture.types import PictureFindings
from engine.yingqi.types import GateResult
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


def test_parallel_domain_orchestrator_calls_canonical_runner(monkeypatch) -> None:
    calls: dict[str, Any] = {}

    class LibraryStub:
        def triggered_rules(self, *, parsed: Any, energy: Any, picture: Any) -> list[Any]:
            calls["triggered_rules"] = {"parsed": parsed, "energy": energy, "picture": picture}
            return ["RULE-STUB"]

    class EnergyStub:
        case_id = "C-ADAPTER"

    def fake_runner(*args: Any, **kwargs: Any) -> ParallelAnalysisOutput:
        calls["runner_args"] = args
        calls["runner_kwargs"] = kwargs
        return ParallelAnalysisOutput(case_id=kwargs["case_id"], domain_analyses=[])

    monkeypatch.setattr("engine.application.parallel_domain_orchestrator.run_parallel_domain_analysis", fake_runner)

    output = analyze_parallel_domains(
        parsed=None,
        energy=cast(EnergyFindings, EnergyStub()),
        picture=cast(PictureFindings, object()),
        gate_results=[cast(GateResult, object())],
        support=cast(SupportFindings, object()),
        production_library=cast(ProductionRuleLibrary, LibraryStub()),
        domains=["财运"],
    )

    assert output.case_id == "C-ADAPTER"
    assert calls["runner_args"] == (None,)
    assert calls["runner_kwargs"]["case_id"] == "C-ADAPTER"
    assert calls["runner_kwargs"]["domains"] == ["财运"]
    assert calls["runner_kwargs"]["base_context"]["production_rules"] == ["RULE-STUB"]


def test_parallel_domain_orchestrator_stays_compatibility_adapter_only() -> None:
    source = inspect.getsource(analyze_parallel_domains)

    assert "run_parallel_domain_analysis" in source
    assert "adjudicate_domain" not in source
    assert "build_domain_consensus" not in source
    assert "detect_cross_expert_conflicts" not in source
    assert "evaluate_cross_domain_consistency" not in source


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

    assert "# 📌 归档信息与命盘结构" in report
    assert output.case_id in report

    statement_index = tmp_path / output.case_id / "statement_index.json"
    data = statement_index.read_text(encoding="utf-8")
    assert "parallel_domain_adjudication" in data
    assert "reading_ids" in data
    assert "adjudication_id" in data
