from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from engine.application import parallel_domain_orchestrator, parallel_domain_runner
from engine.application.domain_analyzers import (
    DEFAULT_DOMAINS,
    DEFAULT_EXPERT_ORDER,
    DomainAnalysisContext,
    DomainAnalyzerRegistry,
    get_wiring_status,
)
from engine.application.parallel_domain_runner import ParallelDomainRunResult, run_parallel_domain_analysis
from engine.application.parallel_execution import ParallelExecutionConfig
from engine.domain.parallel import DomainName, EvidenceItem, ExpertReading, ExpertSystem, ParallelConfidence


@dataclass(frozen=True)
class ParsedStub:
    case_id: str
    meta: dict[str, Any] = field(default_factory=dict)


class SupportAnalyzer:
    def __init__(self, expert_system: ExpertSystem, expert_name: str, confidence: float) -> None:
        self.expert_system: ExpertSystem = expert_system
        self.expert_name = expert_name
        self.confidence = confidence

    def analyze(self, parsed: Any, domain: DomainName, context: DomainAnalysisContext) -> ExpertReading:
        return ExpertReading(
            reading_id=f"RD-{context.case_id}-{domain}-{self.expert_system}",
            case_id=context.case_id,
            domain=domain,
            expert_system=self.expert_system,
            expert_name=self.expert_name,
            stance="support",
            claim=f"{domain}域支持测试结论",
            polarity="positive",
            confidence=ParallelConfidence(raw=self.confidence, star=4, percent=int(self.confidence * 100)),
            evidence_items=[
                EvidenceItem(
                    evidence_type="runtime_finding",
                    ref=f"{self.expert_system}-mock",
                    summary="mock analyzer evidence",
                    strength="high",
                )
            ],
            axis_refs=["mock_axis"],
            scope_limit="mock only",
            falsifiable="测试反馈相反则失验。",
            source_engine="mock",
        )

    def is_wired(self) -> bool:
        return True


def test_parallel_domain_runner_collects_three_expert_readings_with_abstain_fallback() -> None:
    registry = DomainAnalyzerRegistry()
    registry.register("婚姻", "blind", SupportAnalyzer("blind", "盲派综合组", 0.80))
    registry.register("婚姻", "ziping", SupportAnalyzer("ziping", "子平格局派", 0.72))

    output = run_parallel_domain_analysis(
        ParsedStub(case_id="C-TEST"),
        domains=["婚姻"],
        registry=registry,
    )

    analysis = output.domain_analyses[0]
    assert output.case_id == "C-TEST"
    assert analysis.domain == "婚姻"
    assert len(analysis.readings) == 3
    assert [reading.expert_system for reading in analysis.readings] == [
        "blind",
        "ziping",
        "tiaohou_ditiansui",
    ]
    assert analysis.readings[2].stance == "abstain"
    assert analysis.adjudication_result.decision == "yes"
    assert analysis.consensus.layer == "双专家共识"


def test_parallel_domain_runner_defaults_to_all_abstain_without_registry() -> None:
    output = run_parallel_domain_analysis(
        ParsedStub(case_id="C-TEST"),
        domains=["财运"],
    )

    analysis = output.domain_analyses[0]
    assert len(analysis.readings) == 3
    assert all(reading.stance == "abstain" for reading in analysis.readings)
    assert analysis.adjudication_result.decision == "no_output"
    assert analysis.consensus.layer == "不输出"


class MutatingAnalyzer(SupportAnalyzer):
    def analyze(self, parsed: Any, domain: DomainName, context: DomainAnalysisContext) -> ExpertReading:
        context.base_context["seen_by"] = self.expert_system
        context.base_context.setdefault("nested", {}).setdefault("visits", []).append(self.expert_system)
        if hasattr(parsed, "meta"):
            parsed.meta.setdefault("visits", []).append(self.expert_system)
        return super().analyze(parsed, domain, context)


class RaisingAnalyzer(SupportAnalyzer):
    def analyze(self, parsed: Any, domain: DomainName, context: DomainAnalysisContext) -> ExpertReading:
        raise RuntimeError("mock failure")


def test_parallel_domain_runner_isolates_context_and_catches_exceptions() -> None:
    registry = DomainAnalyzerRegistry()
    registry.register("事业", "blind", MutatingAnalyzer("blind", "盲派综合组", 0.80))
    registry.register("事业", "ziping", RaisingAnalyzer("ziping", "子平格局派", 0.72))
    registry.register("事业", "tiaohou_ditiansui", MutatingAnalyzer("tiaohou_ditiansui", "滴天髓调候派", 0.70))
    base_context: dict[str, Any] = {"seed": "stable"}

    output = run_parallel_domain_analysis(
        ParsedStub(case_id="C-TEST"),
        domains=["事业"],
        registry=registry,
        base_context=base_context,
    )

    analysis = output.domain_analyses[0]
    assert base_context == {"seed": "stable"}
    assert [reading.stance for reading in analysis.readings] == ["support", "abstain", "support"]
    assert "mock failure" in analysis.readings[1].claim
    assert "execution_audit=" in analysis.readings[1].notes
    assert analysis.adjudication_result.decision == "yes"


class NestedMutationClaimAnalyzer(SupportAnalyzer):
    def analyze(self, parsed: Any, domain: DomainName, context: DomainAnalysisContext) -> ExpertReading:
        context.base_context.setdefault("nested", {}).setdefault("visits", []).append(self.expert_system)
        if hasattr(parsed, "meta"):
            parsed.meta.setdefault("visits", []).append(self.expert_system)
        reading = super().analyze(parsed, domain, context)
        data = reading.to_dict()
        data["claim"] = ",".join(context.base_context["nested"]["visits"])
        data["notes"] = ",".join(getattr(parsed, "meta", {}).get("visits", []))
        return ExpertReading.from_dict(data)


def test_parallel_domain_runner_deep_copies_nested_context_and_parsed_per_analyzer() -> None:
    registry = DomainAnalyzerRegistry()
    registry.register("财运", "blind", NestedMutationClaimAnalyzer("blind", "盲派综合组", 0.80))
    registry.register("财运", "ziping", NestedMutationClaimAnalyzer("ziping", "子平格局派", 0.72))
    registry.register("财运", "tiaohou_ditiansui", NestedMutationClaimAnalyzer("tiaohou_ditiansui", "滴天髓调候派", 0.70))
    parsed = ParsedStub(case_id="C-TEST", meta={"visits": []})
    base_context: dict[str, Any] = {"nested": {"visits": []}}

    output = run_parallel_domain_analysis(
        parsed,
        domains=["财运"],
        registry=registry,
        base_context=base_context,
    )

    readings = output.domain_analyses[0].readings
    claims = [reading.claim for reading in readings]
    parsed_notes = [reading.notes.split("；", maxsplit=1)[0] for reading in readings]
    assert claims == ["blind", "ziping", "tiaohou_ditiansui"]
    assert parsed_notes == ["blind", "ziping", "tiaohou_ditiansui"]
    assert base_context == {"nested": {"visits": []}}
    assert parsed.meta == {"visits": []}


class SlowAnalyzer(SupportAnalyzer):
    def analyze(self, parsed: Any, domain: DomainName, context: DomainAnalysisContext) -> ExpertReading:
        time.sleep(0.03)
        return super().analyze(parsed, domain, context)


def test_parallel_domain_runner_sequential_and_concurrent_modes_keep_same_reading_order() -> None:
    registry = DomainAnalyzerRegistry()
    registry.register("婚姻", "blind", SlowAnalyzer("blind", "盲派综合组", 0.80))
    registry.register("婚姻", "ziping", SupportAnalyzer("ziping", "子平格局派", 0.72))
    registry.register("婚姻", "tiaohou_ditiansui", SupportAnalyzer("tiaohou_ditiansui", "滴天髓调候派", 0.70))

    sequential = run_parallel_domain_analysis(
        ParsedStub(case_id="C-TEST"),
        domains=["婚姻"],
        registry=registry,
        execution_config=ParallelExecutionConfig(mode="sequential"),
    )
    concurrent = run_parallel_domain_analysis(
        ParsedStub(case_id="C-TEST"),
        domains=["婚姻"],
        registry=registry,
        execution_config=ParallelExecutionConfig(enable_concurrency=True, max_workers=2, timeout_seconds=1.0),
    )

    assert [reading.expert_system for reading in sequential.domain_analyses[0].readings] == [
        reading.expert_system for reading in concurrent.domain_analyses[0].readings
    ]
    assert [reading.reading_id for reading in sequential.domain_analyses[0].readings] == [
        reading.reading_id for reading in concurrent.domain_analyses[0].readings
    ]


def test_parallel_domain_runner_threaded_mode_keeps_expert_order_and_audit() -> None:
    registry = DomainAnalyzerRegistry()
    registry.register("婚姻", "blind", SupportAnalyzer("blind", "盲派综合组", 0.80))
    registry.register("婚姻", "ziping", SupportAnalyzer("ziping", "子平格局派", 0.72))
    registry.register("婚姻", "tiaohou_ditiansui", SupportAnalyzer("tiaohou_ditiansui", "滴天髓调候派", 0.70))

    result = run_parallel_domain_analysis(
        ParsedStub(case_id="C-TEST"),
        domains=["婚姻"],
        registry=registry,
        execution_config=ParallelExecutionConfig(mode="threaded", max_workers=2, timeout_seconds=1.0),
        include_audit=True,
    )

    assert isinstance(result, ParallelDomainRunResult)
    analysis = result.output.domain_analyses[0]
    assert [reading.expert_system for reading in analysis.readings] == [
        "blind",
        "ziping",
        "tiaohou_ditiansui",
    ]
    assert [audit.status for audit in result.execution_audit] == ["success", "success", "success"]
    assert [audit.expert_system for audit in result.execution_audit] == ["blind", "ziping", "tiaohou_ditiansui"]


def test_parallel_domain_runner_timeout_fallback_abstain() -> None:
    registry = DomainAnalyzerRegistry()
    registry.register("健康", "blind", SlowAnalyzer("blind", "盲派综合组", 0.80))

    result = run_parallel_domain_analysis(
        ParsedStub(case_id="C-TEST"),
        domains=["健康"],
        registry=registry,
        timeout_seconds=0.001,
        include_audit=True,
    )

    assert isinstance(result, ParallelDomainRunResult)
    reading = result.output.domain_analyses[0].readings[0]
    assert reading.stance == "abstain"
    assert result.execution_audit[0].status == "timeout"
    assert result.execution_audit[0].error_type == "TimeoutError"


def test_domain_analyzer_wiring_status_marks_registered_and_abstain_only() -> None:
    registry = DomainAnalyzerRegistry()
    registry.register("婚姻", "blind", SupportAnalyzer("blind", "盲派综合组", 0.80))

    status = get_wiring_status(registry)

    assert status["婚姻"]["blind"] == "wired"
    assert status["婚姻"]["ziping"] == "abstain_only"
    assert status["财运"]["blind"] == "abstain_only"


def test_parallel_domain_canonical_constants_are_single_module_exports() -> None:
    assert DEFAULT_DOMAINS == ("学业", "事业", "财运", "婚姻", "健康", "性格")
    assert DEFAULT_EXPERT_ORDER == ("blind", "ziping", "tiaohou_ditiansui")
    assert parallel_domain_runner.DEFAULT_DOMAINS is DEFAULT_DOMAINS
    assert parallel_domain_runner.DEFAULT_EXPERT_ORDER is DEFAULT_EXPERT_ORDER
    assert parallel_domain_orchestrator.DEFAULT_DOMAINS is DEFAULT_DOMAINS
