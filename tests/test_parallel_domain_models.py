from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from engine.application.adjudication import (
    adjudicate_domain,
    build_domain_consensus,
    build_weight_profile,
    load_domain_weight_profile_payload,
)
from engine.application.weight_profile_service import WeightProfileService, load_expert_weight_profile_payload
from engine.domain.parallel import DomainName, EvidenceItem, ExpertReading, ExpertSystem, ParallelConfidence, ReadingStance


def _reading(
    *,
    expert_system: ExpertSystem,
    stance: ReadingStance,
    confidence: float,
    domain: DomainName = "财运",
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


def _canonical_payload() -> dict:
    return load_domain_weight_profile_payload()


def _write_profile(tmp_path: Path, mutation: dict) -> None:
    payload = _canonical_payload()
    payload.update(mutation)
    path = tmp_path / "engine" / "expert-weights.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_expert_reading_roundtrip_keeps_isolation_boundary() -> None:
    reading = _reading(expert_system="ziping", stance="support", confidence=0.78)

    restored = ExpertReading.from_dict(json.loads(json.dumps(reading.to_dict(), ensure_ascii=False)))

    assert restored.expert_system == "ziping"
    assert restored.isolation_boundary == "external_protocol_only"
    assert restored.evidence_items[0].ref == "REF-ziping"


def test_default_weight_profile_is_loaded_from_canonical_expert_weights_yaml() -> None:
    payload = load_domain_weight_profile_payload()
    profile = build_weight_profile("财运")

    assert payload["status"] == "active"
    assert payload["profile_id"] == "expert-domain-prior-2026-06-09"
    assert profile.profile_id == payload["profile_id"]
    assert profile.profile_version == payload["profile_version"]
    assert profile.source == "engine/expert-weights.yaml"
    assert profile.domain_weights == payload["weights"]["财运"]
    assert profile.feedback_overlay_version == "no-feedback-overlay"
    assert set(profile.n_eff_summary) == {"blind", "ziping", "tiaohou_ditiansui"}
    assert abs(sum(profile.domain_weights.values()) - 1.0) < 1e-6


def test_weight_profile_can_merge_human_confirmed_feedback_overlay_for_inline_prior() -> None:
    prior_weights = {
        "财运": {"blind": 0.30, "ziping": 0.45, "tiaohou_ditiansui": 0.25},
        "婚姻": {"blind": 0.40, "ziping": 0.30, "tiaohou_ditiansui": 0.30},
    }
    overlay = {
        "profile_id": "domain-prior-test+feedback-overlay",
        "profile_version": "test-v1+feedback-overlay",
        "source": "tmp/feedback_overlay.json",
        "status": "human_confirmed",
        "weights": {
            "财运": {"blind": 0.21, "ziping": 0.585, "tiaohou_ditiansui": 0.25},
        },
    }

    profile = build_weight_profile("财运", weights_by_domain=prior_weights, feedback_overlay=overlay)
    untouched = build_weight_profile("婚姻", weights_by_domain=prior_weights, feedback_overlay=overlay)

    assert profile.profile_id == "domain-prior-test+feedback-overlay"
    assert profile.profile_version == "test-v1+feedback-overlay"
    assert profile.source == "tmp/feedback_overlay.json"
    assert round(sum(profile.domain_weights.values()), 6) == 1.0
    assert profile.domain_weights["ziping"] > prior_weights["财运"]["ziping"]
    assert profile.domain_weights["blind"] < prior_weights["财运"]["blind"]
    assert untouched.domain_weights == prior_weights["婚姻"]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"status": "review_draft"}, "status 必须为 active"),
        ({"weights": {"学业": {"blind": 0.30, "ziping": 0.45}}}, "缺少专家权重"),
        (
            {"weights": {"学业": {"blind": 0.30, "ziping": 0.45, "tiaohou_ditiansui": 0.30}}},
            "权重和必须为 1.0",
        ),
    ],
)
def test_weight_profile_loader_rejects_invalid_canonical_yaml(
    tmp_path: Path,
    mutation: dict,
    message: str,
) -> None:
    _write_profile(tmp_path, mutation)

    with pytest.raises(ValueError, match=message):
        load_expert_weight_profile_payload(workspace_root=tmp_path)


def test_weight_profile_service_rejects_legacy_four_school_matrix() -> None:
    with pytest.raises(ValueError, match="legacy four-school arbitration matrix"):
        WeightProfileService(source_path="engine/domain-weights.yaml")


def test_weight_profile_service_rejects_raw_review_draft_runtime_source() -> None:
    with pytest.raises(ValueError, match="raw review draft"):
        WeightProfileService(source_path="theory/raw/yaml/domain_weight_profile_2026-06-05.yaml")


def test_feedback_overlay_adjusts_runtime_weight_and_audit_summary() -> None:
    overlay = {
        "version": "feedback-overlay-test-v1",
        "source_path": "tmp/feedback-overlay.yaml",
        "min_effective_sample_for_adjustment": 11,
        "low_sample_max_delta": 0.02,
        "mature_sample_max_delta": 0.15,
        "entries": [
            {
                "expert_system": "ziping",
                "domain": "财运",
                "rule_group": "wealth-structure",
                "n_eff": 20,
                "success_count": 18,
                "failure_count": 2,
                "beta_alpha": 19,
                "beta_beta": 3,
                "beta_mean": 0.86,
            }
        ],
    }

    profile = build_weight_profile("财运", feedback_overlay=overlay)

    assert profile.feedback_overlay_version == "feedback-overlay-test-v1"
    assert profile.feedback_overlay_source_path == "tmp/feedback-overlay.yaml"
    assert profile.n_eff_summary["ziping"]["n_eff"] == 20
    assert profile.feedback_modulations["ziping"] > 1.0
    assert profile.domain_weights["ziping"] > 0.45
    assert round(sum(profile.domain_weights.values()), 6) == 1.0


def test_low_n_eff_feedback_overlay_only_weakly_modulates_prior() -> None:
    overlay = {
        "version": "feedback-overlay-low-n",
        "source_path": "tmp/feedback-overlay.yaml",
        "min_effective_sample_for_adjustment": 11,
        "low_sample_max_delta": 0.02,
        "mature_sample_max_delta": 0.15,
        "entries": [
            {
                "expert_system": "ziping",
                "domain": "财运",
                "rule_group": "wealth-structure",
                "n_eff": 3,
                "success_count": 3,
                "failure_count": 0,
                "beta_alpha": 4,
                "beta_beta": 1,
                "beta_mean": 1.0,
                "wilson_lower_bound": 1.0,
            }
        ],
    }

    profile = build_weight_profile("财运", feedback_overlay=overlay)

    assert profile.feedback_modulations["ziping"] <= 1.02
    assert profile.domain_weights["ziping"] < 0.46


def test_high_n_eff_success_feedback_increases_adjusted_score() -> None:
    baseline = adjudicate_domain(
        case_id="C-TEST",
        domain="财运",
        readings=[_reading(expert_system="ziping", stance="support", confidence=0.82)],
    )
    overlay = {
        "version": "feedback-overlay-high-success",
        "source_path": "tmp/feedback-overlay.yaml",
        "min_effective_sample_for_adjustment": 11,
        "mature_sample_max_delta": 0.15,
        "entries": [
            {
                "expert_system": "ziping",
                "domain": "财运",
                "rule_group": "wealth-structure",
                "n_eff": 30,
                "success_count": 27,
                "failure_count": 3,
                "beta_alpha": 28,
                "beta_beta": 4,
                "beta_mean": 0.875,
            }
        ],
    }
    boosted_profile = build_weight_profile("财运", feedback_overlay=overlay)
    boosted = adjudicate_domain(
        case_id="C-TEST",
        domain="财运",
        readings=[_reading(expert_system="ziping", stance="support", confidence=0.82)],
        weight_profile=boosted_profile,
    )

    assert boosted.judgements[0].feedback_weight > 1.0
    assert boosted.judgements[0].adjusted_score > baseline.judgements[0].adjusted_score


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
    assert result.weight_profile.source == "engine/expert-weights.yaml"
    assert "ziping" in result.winning_experts
    assert result.minority_views[0].expert_system == "tiaohou_ditiansui"
    assert consensus.layer == "双专家共识"
    assert consensus.weight_profile is not None


def test_high_n_eff_failure_feedback_decreases_adjusted_score() -> None:
    baseline = adjudicate_domain(
        case_id="C-TEST",
        domain="财运",
        readings=[_reading(expert_system="ziping", stance="support", confidence=0.82)],
    )
    overlay = {
        "version": "feedback-overlay-high-failure",
        "source_path": "tmp/feedback-overlay.yaml",
        "min_effective_sample_for_adjustment": 11,
        "mature_sample_max_delta": 0.15,
        "entries": [
            {
                "expert_system": "ziping",
                "domain": "财运",
                "rule_group": "wealth-structure",
                "n_eff": 30,
                "success_count": 3,
                "failure_count": 27,
                "beta_alpha": 4,
                "beta_beta": 28,
                "beta_mean": 0.125,
                "wilson_lower_bound": 0.05,
            }
        ],
    }
    reduced_profile = build_weight_profile("财运", feedback_overlay=overlay)
    reduced = adjudicate_domain(
        case_id="C-TEST",
        domain="财运",
        readings=[_reading(expert_system="ziping", stance="support", confidence=0.82)],
        weight_profile=reduced_profile,
    )

    assert reduced.judgements[0].feedback_weight < 1.0
    assert reduced.judgements[0].adjusted_score < baseline.judgements[0].adjusted_score


def test_adjudication_uses_conflict_penalty_input() -> None:
    readings = [
        _reading(expert_system="ziping", stance="support", confidence=0.82),
        _reading(expert_system="tiaohou_ditiansui", stance="oppose", confidence=0.60),
    ]

    result = adjudicate_domain(
        case_id="C-TEST",
        domain="财运",
        readings=readings,
        conflict_penalties={"ziping": 0.05},
    )

    ziping = next(j for j in result.judgements if j.expert_system == "ziping")
    other = next(j for j in result.judgements if j.expert_system == "tiaohou_ditiansui")
    assert ziping.conflict_penalty == 0.05
    assert other.conflict_penalty == 0.0


def test_weight_profile_rejects_feedback_overlay_without_weights_for_inline_prior() -> None:
    with pytest.raises(ValueError, match="feedback overlay 缺少 weights mapping"):
        build_weight_profile(
            "财运",
            weights_by_domain={"财运": {"blind": 0.30, "ziping": 0.45, "tiaohou_ditiansui": 0.25}},
            feedback_overlay={"status": "human_confirmed"},
        )


def test_adjudication_no_output_when_all_experts_abstain() -> None:
    readings = [
        _reading(expert_system="blind", stance="abstain", confidence=0.0),
        _reading(expert_system="ziping", stance="abstain", confidence=0.0),
        _reading(expert_system="tiaohou_ditiansui", stance="abstain", confidence=0.0),
    ]

    result = adjudicate_domain(case_id="C-TEST", domain="财运", readings=readings)

    assert result.decision == "no_output"
    assert sorted(result.abstained_experts) == ["blind", "tiaohou_ditiansui", "ziping"]
