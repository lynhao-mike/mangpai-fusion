from __future__ import annotations

import math

import pytest

from engine.evaluation.models import BlindPrediction, BlindSchoolOutput, BlindTask, RevealedLabel
from engine.evaluation.scoring import (
    ABSTENTION_OPPORTUNITY_COST,
    HIGH_RISK_FALSE_POSITIVE_MULTIPLIER,
    brier_score,
    log_loss,
    ordinal_score,
    score_output,
    time_window_score,
)


def _task(
    scoring_method: str = "binary_probability",
    *,
    quantifiable: bool = True,
    high_risk: bool = False,
) -> BlindTask:
    schema = {"type": "boolean"} if quantifiable else {}
    if scoring_method == "ordinal":
        schema = {"type": "ordinal", "labels": ["low", "medium", "high"]}
    return BlindTask(
        task_id="test.task",
        domain="test",
        claim_type="portrait" if scoring_method == "portrait_agreement" else "binary_event",
        scoring_method=scoring_method,
        quantifiable=quantifiable,
        high_risk=high_risk,
        allowed_time_horizons=["lifetime"],
        required_input_fields=[],
        label_schema=schema,
        evaluation_note="test",
    )


def _prediction(
    probability: float = 0.8,
    *,
    event_label: str = "occurred",
    time_window: dict[str, int | str] | None = None,
) -> BlindPrediction:
    return BlindPrediction(
        prediction_id="P-001",
        event_label=event_label,
        probability=probability,
        time_window=time_window or {},
        evidence_refs=[],
        falsifier="not observed",
    )


def _output(state: str = "claim", prediction: BlindPrediction | None = None) -> BlindSchoolOutput:
    return BlindSchoolOutput(
        case_id="C-001",
        school_id="ziping",
        task_id="test.task",
        state=state,
        rationale="test rationale",
        predictions=[prediction or _prediction()] if state == "claim" else [],
    )


def _label(value: object, *, quantifiable: bool = True) -> RevealedLabel:
    return RevealedLabel(
        case_id="C-001",
        task_id="test.task",
        label=value,
        observed_at="2026-01-01",
        source="feedback",
        confidence_grade="A",
        quantifiable=quantifiable,
        conflict_state="none",
    )


def test_probability_scores_reward_calibrated_correct_prediction_and_boundaries() -> None:
    assert brier_score(0.8, True) == 0.04
    assert brier_score(0.2, True) == 0.64
    assert brier_score(0.0, False) == 0.0
    assert brier_score(1.0, True) == 0.0
    assert log_loss(0.8, True) < log_loss(0.2, True)
    assert math.isfinite(log_loss(0.0, True))
    assert math.isfinite(log_loss(1.0, False))
    for probability in (-0.01, 1.01):
        with pytest.raises(ValueError, match="probability"):
            brier_score(probability, True)
        with pytest.raises(ValueError, match="probability"):
            log_loss(probability, True)
    with pytest.raises(ValueError, match="epsilon"):
        log_loss(0.5, True, epsilon=0.0)


def test_time_window_scores_inside_outside_and_rejects_malformed_windows() -> None:
    window = {"start_year": 2015, "end_year": 2020}
    assert time_window_score(window, 2018) == 1.0
    assert time_window_score(window, 2021) == 0.5
    assert time_window_score(window, 2021) > time_window_score(window, 2025)
    assert 0.0 <= time_window_score(window, 2025) <= 1.0
    for malformed in ({}, {"start_year": 2020}, {"start_year": 2021, "end_year": 2020}, {"start_year": "2020", "end_year": 2021}):
        with pytest.raises(ValueError, match="window"):
            time_window_score(malformed, 2020)  # type: ignore[arg-type]


def test_ordinal_score_is_normalized_and_validates_range() -> None:
    assert ordinal_score(5, 5, 15) == 1.0
    assert ordinal_score(1, 15, 15) == 0.0
    for args in ((0, 1, 3), (1, 4, 3), (1, 1, 1)):
        with pytest.raises(ValueError, match="rank"):
            ordinal_score(*args)


def test_score_output_claim_scores_binary_probability() -> None:
    score = score_output(_output(), _task(), _label(True))
    assert score.state == "claim"
    assert score.probability_score == 0.96
    assert score.utility == 0.8
    assert score.observed_positive is True
    assert score.abstained is False
    assert score.knowledge_coverage is True


def test_score_output_abstain_and_unsupported_have_no_fabricated_accuracy() -> None:
    abstained = score_output(_output("abstain"), _task(), _label(True))
    assert abstained.abstained is True
    assert abstained.knowledge_coverage is True
    assert abstained.probability_score is None
    assert abstained.utility == -ABSTENTION_OPPORTUNITY_COST

    no_valid_label = score_output(_output("abstain"), _task(), None)
    assert no_valid_label.utility is None
    unsupported = score_output(_output("unsupported"), _task(), _label(True))
    assert unsupported.abstained is False
    assert unsupported.knowledge_coverage is False
    assert unsupported.probability_score is None
    assert unsupported.utility is None


def test_high_risk_false_positive_uses_named_two_x_multiplier() -> None:
    assert HIGH_RISK_FALSE_POSITIVE_MULTIPLIER == 2.0
    ordinary = score_output(_output(), _task(), _label(False))
    high_risk = score_output(_output(), _task(high_risk=True), _label(False))
    assert ordinary.utility == -0.8
    assert high_risk.utility == ordinary.utility * HIGH_RISK_FALSE_POSITIVE_MULTIPLIER


def test_non_quantifiable_portrait_emits_agreement_but_not_accuracy() -> None:
    task = _task("portrait_agreement", quantifiable=False)
    score = score_output(_output(prediction=_prediction(probability=0.75)), task, _label(0.6, quantifiable=False))
    assert score.portrait_agreement == 0.6
    assert score.probability_score is None
    assert score.timing_score is None
    assert score.ordinal_score is None
    assert score.utility is None


def test_score_output_dispatches_time_window_and_ordinal_methods() -> None:
    timing = score_output(
        _output(prediction=_prediction(time_window={"start_year": 2020, "end_year": 2022})),
        _task("time_window"),
        _label(2021),
    )
    assert timing.timing_score == 1.0

    ordinal = score_output(
        _output(prediction=_prediction(event_label="medium")),
        _task("ordinal"),
        _label("high"),
    )
    assert ordinal.ordinal_score == 0.5
