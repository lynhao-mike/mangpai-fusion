from __future__ import annotations

from engine.decision.l2_v5_claims import to_school_claim
from engine.v5.domain import V5Claim, V5Confidence, V5Evidence


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
