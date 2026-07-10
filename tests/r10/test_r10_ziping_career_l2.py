from __future__ import annotations

import pytest

from engine.decision.l2_v5_claims import build_ziping_career_claims, to_school_claim
from engine.decision.models import SchoolApplicability
from engine.v5.domain import V5Claim, V5Confidence, V5Evidence


CHART = {
    "case_id": "C-R10-ZIPING",
    "pillars": {"year": "庚申", "month": "戊寅", "day": "壬子", "hour": "辛丑"},
    "current_dayun": "壬午",
    "current_year": "丙午（2026 年）",
}


def test_to_school_claim_preserves_v5_reasoning_paths_exactly() -> None:
    paths = {
        "wangshuai_path": {"strength": "偏弱", "score": 0.34},
        "yongshen_path": {"pattern": "七杀格", "yongshen": "正印"},
        "geju_bingyao_path": {"geju": "七杀格", "disease": "杀旺", "medicine": "印化"},
        "zuogong_path": {"source": "官杀", "target": "印", "mode": "杀印相生"},
    }
    source = V5Claim(
        claim_id="v5cl-career-1",
        school="ziping",
        domain="事业",
        claim="七杀格以印化杀，事业取组织平台路径。",
        claim_type="structure_claim",
        stance="mixed",
        polarity="positive",
        confidence=V5Confidence(tier="★★★★", score=0.71, note="source-note"),
        evidence=[V5Evidence(evidence_id="ev-1", source="ziping", text="source evidence")],
        counter_evidence=[
            V5Evidence(
                evidence_id="counter-1",
                source="ziping",
                text="source counter evidence",
                metadata={"nested": {"weight": 0.2}},
            )
        ],
        timing_hints=[{"window": {"start": 2026, "end": 2028}}],
        probabilistic=True,
        falsifiable="现实事业长期不呈组织平台路径则降权。",
        metadata={"reasoning_paths": paths, "geju_type": "正格", "nested": {"items": [1, 2]}},
    )

    actual = to_school_claim(source, "lead")

    assert actual.claim_id == source.claim_id
    assert actual.school == source.school
    assert actual.role_granted_by_l1 == "lead"
    assert actual.domain == source.domain
    assert actual.claim_type == source.claim_type
    assert actual.statement == source.claim
    assert actual.evidence_refs == ["ev-1"]
    assert actual.confidence == source.confidence.score
    assert actual.falsifier == source.falsifiable
    assert actual.dependencies == [f"v5:{source.claim_id}"]
    assert actual.metadata["reasoning_paths"] == paths
    assert actual.metadata["geju_type"] == source.metadata["geju_type"]
    assert actual.metadata["nested"] == source.metadata["nested"]
    assert actual.metadata["v5_payload"] == {
        "stance": source.stance,
        "polarity": source.polarity,
        "counter_evidence": [item.to_dict() for item in source.counter_evidence],
        "timing_hints": source.timing_hints,
        "probabilistic": source.probabilistic,
    }
    assert set(actual.metadata["v5_payload"]) == {
        "stance",
        "polarity",
        "counter_evidence",
        "timing_hints",
        "probabilistic",
    }

    actual.metadata["reasoning_paths"]["wangshuai_path"]["score"] = 0.99
    actual.metadata["nested"]["items"].append(3)
    actual.metadata["v5_payload"]["counter_evidence"][0]["metadata"]["nested"]["weight"] = 0.9
    actual.metadata["v5_payload"]["timing_hints"][0]["window"]["start"] = 2030

    assert source.metadata["reasoning_paths"]["wangshuai_path"]["score"] == 0.34
    assert source.metadata["nested"]["items"] == [1, 2]
    assert source.counter_evidence[0].metadata["nested"]["weight"] == 0.2
    assert source.timing_hints[0]["window"]["start"] == 2026


@pytest.mark.parametrize("score", [1.25, -0.01])
def test_to_school_claim_rejects_out_of_range_confidence_with_claim_context(score: float) -> None:
    source = V5Claim(
        claim_id=f"v5cl-invalid-confidence-{score}",
        school="ziping",
        domain="事业",
        claim="越界置信度不得进入 L2。",
        claim_type="structure_claim",
        confidence=V5Confidence(score=score),
    )

    with pytest.raises(ValueError) as exc_info:
        to_school_claim(source, "lead")

    message = str(exc_info.value)
    assert source.claim_id in message
    assert str(score) in message
    assert "confidence" in message.lower()


def test_to_school_claim_rejects_reserved_v5_payload_in_source_metadata() -> None:
    reserved_payload = {"source_owned": {"nested": ["must-not-overwrite"]}}
    source = V5Claim(
        claim_id="v5cl-reserved-payload-conflict",
        school="ziping",
        domain="事业",
        claim="来源 metadata 使用了边界保留键。",
        claim_type="structure_claim",
        confidence=V5Confidence(score=0.6),
        metadata={"v5_payload": reserved_payload, "other": {"kept": True}},
    )

    with pytest.raises(ValueError) as exc_info:
        to_school_claim(source, "co_lead")

    message = str(exc_info.value)
    assert source.claim_id in message
    assert "v5_payload" in message
    assert source.metadata["v5_payload"] == reserved_payload


def test_to_school_claim_does_not_invent_missing_reasoning_paths() -> None:
    source = V5Claim(
        claim_id="v5cl-career-empty",
        school="ziping",
        domain="事业",
        claim="来源只给出一条结构命题。",
        claim_type="structure_claim",
        confidence=V5Confidence(score=0.6),
        metadata={},
    )

    actual = to_school_claim(source, "co_lead")

    assert "reasoning_paths" not in actual.metadata
    assert "wangshuai_path" not in actual.metadata
    assert "yongshen_path" not in actual.metadata
    assert "geju_bingyao_path" not in actual.metadata
    assert "zuogong_path" not in actual.metadata
    assert actual.metadata == {
        "v5_payload": {
            "stance": source.stance,
            "polarity": source.polarity,
            "counter_evidence": [],
            "timing_hints": [],
            "probabilistic": source.probabilistic,
        }
    }


def test_build_ziping_career_claims_uses_l1_role_and_keeps_global_context() -> None:
    applicability = [
        SchoolApplicability(
            school="ziping",
            role="lead",
            applicable_domains=["事业"],
            applicability_score=0.9,
            confidence=0.9,
        )
    ]

    claims = build_ziping_career_claims(CHART, "C-R10-ZIPING", applicability)

    assert claims
    assert {claim.school for claim in claims} == {"ziping"}
    assert {claim.domain for claim in claims} == {"总体", "事业"}
    assert {claim.role_granted_by_l1 for claim in claims} == {"lead"}
    assert any("旺衰" in claim.statement for claim in claims)
    assert any("用神=" in claim.statement for claim in claims)
    assert all(claim.metadata["source_scope"] == "ziping_independent_runner" for claim in claims)


def test_build_ziping_career_claims_emits_nothing_when_l1_abstains_or_is_missing() -> None:
    applicability = [SchoolApplicability(school="ziping", role="abstain")]

    assert build_ziping_career_claims(CHART, "C-R10-ZIPING", applicability) == []
    assert build_ziping_career_claims(CHART, "C-R10-ZIPING", []) == []
