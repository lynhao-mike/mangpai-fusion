from __future__ import annotations

import json

from engine.application.adjudication import adjudicate_domain, build_domain_consensus
from engine.domain.parallel import EvidenceItem, ExpertReading, ParallelConfidence


def _reading(
    *,
    expert_system: str,
    stance: str,
    confidence: float,
    domain: str = "财运",
    claim: str = "财运总体可用，但兑现并非线性稳定",
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
                evidence_type="candidate_rule" if expert_system != "blind" else "runtime_finding",
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


def test_expert_reading_roundtrip_keeps_isolation_boundary() -> None:
    reading = _reading(expert_system="ziping", stance="support", confidence=0.78)

    restored = ExpertReading.from_dict(json.loads(json.dumps(reading.to_dict(), ensure_ascii=False)))

    assert restored.expert_system == "ziping"
    assert restored.isolation_boundary == "external_protocol_only"
    assert restored.evidence_items[0].ref == "REF-ziping"


def test_adjudication_uses_domain_weights_and_preserves_minority() -> None:
    readings = [
        _reading(expert_system="blind", stance="support", confidence=0.70),
        _reading(expert_system="ziping", stance="support", confidence=0.82),
        _reading(
            expert_system="tiaohou_ditiansui",
            stance="oppose",
            confidence=0.60,
            claim="气势偏滞导致财运兑现不稳定",
        ),
    ]

    result = adjudicate_domain(case_id="C-TEST", domain="财运", readings=readings)
    consensus = build_domain_consensus(
        case_id="C-TEST",
        domain="财运",
        readings=readings,
        adjudication=result,
    )

    assert result.decision == "yes"
    assert result.weight_profile.domain_weights["ziping"] == 0.45
    assert "ziping" in result.winning_experts
    assert result.minority_views[0].expert_system == "tiaohou_ditiansui"
    assert consensus.layer == "双专家共识"
    assert consensus.weight_profile is not None


def test_adjudication_no_output_when_all_experts_abstain() -> None:
    readings = [
        _reading(expert_system="blind", stance="abstain", confidence=0.0),
        _reading(expert_system="ziping", stance="abstain", confidence=0.0),
        _reading(expert_system="tiaohou_ditiansui", stance="abstain", confidence=0.0),
    ]

    result = adjudicate_domain(case_id="C-TEST", domain="财运", readings=readings)

    assert result.decision == "no_output"
    assert sorted(result.abstained_experts) == ["blind", "tiaohou_ditiansui", "ziping"]
