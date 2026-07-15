from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from engine.learning.models import (
    ConditionalIdentity,
    ConditionalLearningSignal,
    LearningDecision,
    LearningThresholds,
    ManualReviewItem,
)


def identity(**changes: str) -> ConditionalIdentity:
    values = {
        "school_id": "ziping",
        "task_id": "career.role_change",
        "chart_prototype_id": "prototype-balanced",
        "claim_type": "binary_event",
        "time_horizon": "annual",
        "evidence_completeness_band": "complete",
    }
    values.update(changes)
    return ConditionalIdentity(**values)


def signal(**changes: object) -> ConditionalLearningSignal:
    values: dict[str, object] = {
        "signal_id": "sig-001",
        "feedback_observation_id": "obs-001",
        "claim_id": "claim-001",
        "rule_id": "rule-001",
        "identity": identity(),
        "verdict": "hit",
        "feedback_quality": 1.0,
        "attributable": True,
        "time_error": None,
        "metadata": {"source": "l8"},
    }
    values.update(changes)
    return ConditionalLearningSignal(**values)


@pytest.mark.parametrize(
    "field",
    [
        "school_id",
        "task_id",
        "chart_prototype_id",
        "claim_type",
        "time_horizon",
        "evidence_completeness_band",
    ],
)
def test_conditional_identity_requires_all_six_dimensions(field: str) -> None:
    with pytest.raises(ValueError, match=field):
        identity(**{field: " "})


def test_identity_has_stable_six_dimension_key() -> None:
    assert identity().key == (
        "ziping|career.role_change|prototype-balanced|binary_event|annual|complete"
    )


@pytest.mark.parametrize("verdict", ["unknown", "", "HIT"])
def test_signal_rejects_unknown_verdict(verdict: str) -> None:
    with pytest.raises(ValueError, match="verdict"):
        signal(verdict=verdict)


def test_unattributable_signal_must_be_no_data() -> None:
    with pytest.raises(ValueError, match="no_data"):
        signal(attributable=False, verdict="hit")


def test_unattributable_no_data_signal_carries_no_update_weight() -> None:
    item = signal(attributable=False, verdict="no_data", feedback_quality=0.8)
    assert item.effective_weight == 0.0


@pytest.mark.parametrize("quality", [-0.01, 1.01])
def test_signal_rejects_feedback_quality_outside_probability_range(quality: float) -> None:
    with pytest.raises(ValueError, match="feedback_quality"):
        signal(feedback_quality=quality)


def test_contracts_round_trip_without_losing_types() -> None:
    thresholds = LearningThresholds(
        medium_n_eff=5,
        mature_n_eff=20,
        partial_weight=0.5,
        max_posterior_delta=0.08,
        large_change_delta=0.05,
    )
    decision = LearningDecision(
        decision_id="decision-001",
        signal_id="sig-001",
        target_identity=identity(),
        update_tier="adjust_applicability",
        proposed_delta=0.04,
        proposed_posterior_mean=0.64,
        proposed_credible_interval=(0.42, 0.81),
        n_eff_before=4.0,
        n_eff_after=5.0,
        applied=True,
        requires_human_approval=False,
        snapshot_ref="sha256:abc",
        rationale="medium sample",
        audit={"verdict": "hit"},
    )
    review = ManualReviewItem(
        review_id="review-001",
        signal_id="sig-001",
        decision_id="decision-001",
        reason="high_risk",
        target_identity=identity(),
        context={"task_id": "career.role_change"},
    )

    for item in (identity(), signal(), thresholds, decision, review):
        assert type(item).from_dict(item.to_dict()) == item


def test_nested_mapping_fields_are_deeply_frozen() -> None:
    item = signal(metadata={"source": "l8", "labels": ["verified"]})
    with pytest.raises(TypeError):
        item.metadata["source"] = "tampered"  # type: ignore[index]
    with pytest.raises(AttributeError):
        item.metadata["labels"].append("late")  # type: ignore[union-attr]


def test_contracts_are_frozen_dataclasses() -> None:
    with pytest.raises(FrozenInstanceError):
        replace(identity(), school_id="ren").school_id = "ziping"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"medium_n_eff": -1}, "medium_n_eff"),
        ({"medium_n_eff": 20, "mature_n_eff": 5}, "mature_n_eff"),
        ({"partial_weight": 1.1}, "partial_weight"),
        ({"max_posterior_delta": 0}, "max_posterior_delta"),
    ],
)
def test_thresholds_validate_ranges(changes: dict[str, float], message: str) -> None:
    values = {
        "medium_n_eff": 5.0,
        "mature_n_eff": 20.0,
        "partial_weight": 0.5,
        "max_posterior_delta": 0.08,
        "large_change_delta": 0.05,
    }
    values.update(changes)
    with pytest.raises(ValueError, match=message):
        LearningThresholds(**values)
