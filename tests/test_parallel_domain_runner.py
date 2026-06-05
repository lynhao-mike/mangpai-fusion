from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine.application.domain_analyzers import DomainAnalysisContext, DomainAnalyzerRegistry
from engine.application.parallel_domain_runner import run_parallel_domain_analysis
from engine.domain.parallel import EvidenceItem, ExpertReading, ParallelConfidence


@dataclass(frozen=True)
class ParsedStub:
    case_id: str


class SupportAnalyzer:
    def __init__(self, expert_system: str, expert_name: str, confidence: float) -> None:
        self.expert_system = expert_system
        self.expert_name = expert_name
        self.confidence = confidence

    def analyze(self, parsed: Any, domain: str, context: DomainAnalysisContext) -> ExpertReading:
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
