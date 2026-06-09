from __future__ import annotations

from typing import Any

from engine.application.adjudication import adjudicate_domain, build_domain_consensus
from engine.application.conflict_detection import conflict_penalties_from_conflicts, detect_cross_expert_conflicts
from engine.application.cross_domain_consistency import evaluate_cross_domain_consistency
from engine.application.domain_analyzers import DomainAnalysisContext, DomainAnalyzerRegistry
from engine.application.parallel_domain_runner import run_parallel_domain_analysis
from engine.domain.parallel import DomainAnalysis, DomainName, EvidenceItem, ExpertReading, ExpertSystem, ParallelConfidence, ReadingStance


class StaticAnalyzer:
    def __init__(self, expert_system: ExpertSystem, stance: ReadingStance, confidence: float, claim: str) -> None:
        self.expert_system = expert_system
        self.stance = stance
        self.confidence = confidence
        self.claim = claim

    def analyze(self, parsed: Any, domain: DomainName, context: DomainAnalysisContext) -> ExpertReading:
        return _reading(
            expert_system=self.expert_system,
            stance=self.stance,
            confidence=self.confidence,
            domain=domain,
            claim=self.claim,
        )

    def is_wired(self) -> bool:
        return True


class ParsedStub:
    case_id = "C-TEST"


def _reading(
    *,
    expert_system: ExpertSystem,
    stance: ReadingStance,
    confidence: float,
    domain: DomainName,
    claim: str,
) -> ExpertReading:
    return ExpertReading(
        reading_id=f"RD-C-TEST-{domain}-{expert_system}",
        case_id="C-TEST",
        domain=domain,
        expert_system=expert_system,
        expert_name={
            "blind": "盲派综合组",
            "ziping": "子平格局派",
            "tiaohou_ditiansui": "滴天髓调候派",
        }[expert_system],
        stance=stance,
        claim=claim,
        polarity="positive" if stance == "support" else "negative",
        confidence=ParallelConfidence(raw=confidence, star=4, percent=int(confidence * 100)),
        evidence_items=[
            EvidenceItem(
                evidence_type="runtime_finding",
                ref=f"REF-{expert_system}",
                summary="测试证据",
                strength="high",
            )
        ],
        axis_refs=["structure"],
        scope_limit="测试边界",
        falsifiable="若实际反馈相反则失验。",
        source_engine="test",
    )


def _analysis(domain: DomainName, readings: list[ExpertReading]) -> DomainAnalysis:
    adjudication = adjudicate_domain(case_id="C-TEST", domain=domain, readings=readings)
    consensus = build_domain_consensus(case_id="C-TEST", domain=domain, readings=readings, adjudication=adjudication)
    conflicts = detect_cross_expert_conflicts(case_id="C-TEST", domain=domain, readings=readings)
    return DomainAnalysis(
        domain=domain,
        readings=readings,
        adjudication_result=adjudication,
        consensus=consensus,
        conflicts=conflicts,
    )


def test_detect_cross_expert_conflicts_from_strong_yes_no_opposition() -> None:
    readings = [
        _reading(expert_system="blind", stance="support", confidence=0.82, domain="财运", claim="财运可用"),
        _reading(expert_system="ziping", stance="oppose", confidence=0.76, domain="财运", claim="财运难聚"),
        _reading(expert_system="tiaohou_ditiansui", stance="abstain", confidence=0.0, domain="财运", claim="调候不表态"),
    ]

    conflicts = detect_cross_expert_conflicts(case_id="C-TEST", domain="财运", readings=readings)
    penalties = conflict_penalties_from_conflicts(conflicts)

    assert len(conflicts) == 1
    assert conflicts[0].domain == "财运"
    assert conflicts[0].conflict_type == "evidence"
    assert set(conflicts[0].involved_experts) == {"blind", "ziping"}
    assert "yes/no 强对立" in conflicts[0].arbitration_reason
    assert penalties["blind"] > 0
    assert penalties["ziping"] > 0
    assert "tiaohou_ditiansui" not in penalties


def test_parallel_domain_runner_records_conflicts_and_feeds_penalty() -> None:
    registry = DomainAnalyzerRegistry()
    registry.register("财运", "blind", StaticAnalyzer("blind", "support", 0.82, "财运可用"))
    registry.register("财运", "ziping", StaticAnalyzer("ziping", "oppose", 0.76, "财运难聚"))
    registry.register("财运", "tiaohou_ditiansui", StaticAnalyzer("tiaohou_ditiansui", "abstain", 0.0, "调候不表态"))

    output = run_parallel_domain_analysis(ParsedStub(), domains=["财运"], registry=registry)

    analysis = output.domain_analyses[0]
    assert analysis.conflicts
    assert {j.expert_system for j in analysis.adjudication_result.judgements if j.conflict_penalty > 0} == {"blind", "ziping"}
    assert analysis.adjudication_result.arbitration_reason is not None
    assert "conflict_penalty_total" in analysis.adjudication_result.arbitration_reason.winner_reason


def test_detect_cross_expert_conflicts_preserves_high_evidence_minority_after_adjudication() -> None:
    readings = [
        _reading(expert_system="blind", stance="support", confidence=0.82, domain="事业", claim="事业走强"),
        _reading(expert_system="ziping", stance="support", confidence=0.78, domain="事业", claim="事业平台增强"),
        _reading(expert_system="tiaohou_ditiansui", stance="mixed", confidence=0.56, domain="事业", claim="事业强但需看调候边界"),
    ]
    adjudication = adjudicate_domain(case_id="C-TEST", domain="事业", readings=readings)

    conflicts = detect_cross_expert_conflicts(
        case_id="C-TEST",
        domain="事业",
        readings=readings,
        adjudication_result=adjudication,
    )

    assert conflicts
    assert conflicts[0].conflict_type == "scope"
    assert conflicts[0].loser == "tiaohou_ditiansui"
    assert "证据链达到保留阈值" in conflicts[0].arbitration_reason


    career = _analysis("事业", [
        _reading(expert_system="blind", stance="support", confidence=0.86, domain="事业", claim="事业平台明显走强"),
        _reading(expert_system="ziping", stance="support", confidence=0.80, domain="事业", claim="事业职级增强"),
    ])
    wealth = _analysis("财运", [
        _reading(expert_system="blind", stance="oppose", confidence=0.82, domain="财运", claim="财运弱，现金流难聚"),
        _reading(expert_system="ziping", stance="oppose", confidence=0.76, domain="财运", claim="资产兑现不稳"),
    ])

    notes = evaluate_cross_domain_consistency([career, wealth], case_id="C-TEST")

    assert notes
    note = notes[0].to_dict()
    assert note["severity"] == "warning"
    assert note["domains"] == ["事业", "财运"]
    assert "禁止直接推出高财富兑现" in note["message"]
    assert set(note["related_adjudication_ids"]) == {
        career.adjudication_result.adjudication_id,
        wealth.adjudication_result.adjudication_id,
    }
