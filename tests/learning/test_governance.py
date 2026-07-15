from __future__ import annotations

from pathlib import Path

import pytest

from engine.evaluation.models import CapabilityPosterior
from engine.learning.governance import decide_learning_tier, load_learning_thresholds
from engine.learning.models import ConditionalIdentity, ConditionalLearningSignal, LearningThresholds


def _identity() -> ConditionalIdentity:
    return ConditionalIdentity(
        school_id="ziping",
        task_id="career.role_change",
        chart_prototype_id="prototype-balanced",
        claim_type="binary_event",
        time_horizon="annual",
        evidence_completeness_band="complete",
    )


def _signal(verdict: str = "hit", quality: float = 1.0, *, attributable: bool = True) -> ConditionalLearningSignal:
    return ConditionalLearningSignal(
        signal_id=f"sig-{verdict}-{quality}",
        feedback_observation_id="obs-001",
        claim_id="claim-001",
        rule_id="rule-001",
        identity=_identity(),
        verdict=verdict,
        feedback_quality=quality,
        attributable=attributable,
    )


def _posterior(n_eff: float, mean: float = 0.6) -> CapabilityPosterior:
    return CapabilityPosterior(
        school_id="ziping",
        task_id="career.role_change",
        chart_prototype_id="prototype-balanced",
        claim_type="binary_event",
        time_horizon="annual",
        evidence_completeness_band="complete",
        coverage_rate=1.0,
        discrimination_score=0.3,
        accuracy_score=mean,
        calibration_error=0.1,
        posterior_mean=mean,
        credible_interval=(0.4, 0.8),
        n_eff=n_eff,
        evidence_grade="E3",
        last_evaluated_at="2026-07-15T00:00:00Z",
    )


@pytest.fixture
def thresholds() -> LearningThresholds:
    return LearningThresholds(
        medium_n_eff=5,
        mature_n_eff=20,
        partial_weight=0.5,
        max_posterior_delta=0.08,
        large_change_delta=0.05,
    )


def test_low_sample_is_record_only_and_never_proposes_delta(thresholds: LearningThresholds) -> None:
    decision = decide_learning_tier(_signal(), _posterior(3.5), thresholds, is_high_risk=False)
    assert decision.n_eff_after == 4.5
    assert decision.update_tier == "record_only"
    assert decision.proposed_delta == 0.0
    assert decision.applied is False


def test_medium_sample_adjusts_only_applicability(thresholds: LearningThresholds) -> None:
    decision = decide_learning_tier(_signal(), _posterior(4.0), thresholds, is_high_risk=False)
    assert decision.n_eff_after == 5.0
    assert decision.update_tier == "adjust_applicability"
    assert decision.requires_human_approval is False
    assert decision.applied is True


def test_mature_sample_rule_prior_requires_human_approval(thresholds: LearningThresholds) -> None:
    decision = decide_learning_tier(_signal(), _posterior(19.0), thresholds, is_high_risk=False)
    assert decision.n_eff_after == 20.0
    assert decision.update_tier == "adjust_rule_prior"
    assert decision.requires_human_approval is True
    assert decision.applied is False


def test_high_risk_requires_approval_at_any_n_eff(thresholds: LearningThresholds) -> None:
    decision = decide_learning_tier(_signal(), _posterior(50.0), thresholds, is_high_risk=True)
    assert decision.update_tier == "adjust_rule_prior"
    assert decision.requires_human_approval is True
    assert decision.applied is False
    assert "high_risk" in decision.audit["review_reasons"]


def test_high_risk_medium_sample_cannot_auto_apply(thresholds: LearningThresholds) -> None:
    decision = decide_learning_tier(_signal(), _posterior(5.0), thresholds, is_high_risk=True)
    assert decision.update_tier == "adjust_applicability"
    assert decision.requires_human_approval is True
    assert decision.applied is False


def test_partial_verdict_adds_only_configured_effective_weight(thresholds: LearningThresholds) -> None:
    decision = decide_learning_tier(_signal("partial", quality=0.8), _posterior(4.0), thresholds, is_high_risk=False)
    assert decision.n_eff_after == pytest.approx(4.4)
    assert decision.audit["effective_weight"] == pytest.approx(0.4)


def test_no_data_does_not_increase_n_eff_or_create_delta(thresholds: LearningThresholds) -> None:
    decision = decide_learning_tier(
        _signal("no_data", quality=1.0, attributable=False),
        _posterior(12.0),
        thresholds,
        is_high_risk=False,
    )
    assert decision.update_tier == "manual_review"
    assert decision.n_eff_after == 12.0
    assert decision.proposed_delta == 0.0
    assert decision.applied is False
    assert "unattributable" in decision.audit["review_reasons"]


def test_single_update_delta_is_clamped_by_configuration(thresholds: LearningThresholds) -> None:
    decision = decide_learning_tier(_signal("hit"), _posterior(5.0, mean=0.05), thresholds, is_high_risk=False)
    assert abs(decision.proposed_delta) <= thresholds.max_posterior_delta
    assert decision.proposed_posterior_mean == pytest.approx(0.13)


def test_miss_moves_posterior_down(thresholds: LearningThresholds) -> None:
    decision = decide_learning_tier(_signal("miss"), _posterior(5.0, mean=0.8), thresholds, is_high_risk=False)
    assert decision.proposed_delta < 0


def test_production_thresholds_are_loaded_from_yaml() -> None:
    loaded = load_learning_thresholds(Path("engine/conditional-learning.yaml"))
    assert loaded.medium_n_eff > 0
    assert loaded.mature_n_eff > loaded.medium_n_eff
    assert 0 < loaded.partial_weight <= 1
    assert 0 < loaded.max_posterior_delta <= 1


def test_missing_threshold_key_fails_loudly(tmp_path: Path) -> None:
    config = tmp_path / "learning.yaml"
    config.write_text("thresholds:\n  medium_n_eff: 5\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mature_n_eff"):
        load_learning_thresholds(config)
