from __future__ import annotations

import math

import pytest

from engine.evaluation.models import BlindPrediction, BlindSchoolOutput, BlindTask, RevealedLabel
from engine.evaluation.scoring import (
    ABSTENTION_OPPORTUNITY_COST,
    HIGH_RISK_FALSE_POSITIVE_MULTIPLIER,
    binary_observed_value,
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
    label_schema: dict[str, object] | None = None,
) -> BlindTask:
    schema = {"type": "boolean", "positive_label": "observed", "negative_label": "not_observed"} if quantifiable else {}
    if scoring_method == "ordinal":
        schema = {"type": "ordinal", "labels": ["low", "medium", "high"]}
    elif scoring_method == "multiclass_probability":
        schema = {"type": "categorical", "labels": ["academic", "vocational", "mixed"]}
    if label_schema is not None:
        schema = label_schema
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


def _output(
    state: str = "claim",
    prediction: BlindPrediction | None = None,
    *,
    predictions: list[BlindPrediction] | None = None,
    case_id: str = "C-001",
    task_id: str = "test.task",
) -> BlindSchoolOutput:
    return BlindSchoolOutput(
        case_id=case_id,
        school_id="ziping",
        task_id=task_id,
        state=state,
        rationale="test rationale",
        predictions=(predictions if predictions is not None else [prediction or _prediction()]) if state == "claim" else [],
    )


def _label(
    value: object,
    *,
    quantifiable: bool = True,
    case_id: str = "C-001",
    task_id: str = "test.task",
) -> RevealedLabel:
    return RevealedLabel(
        case_id=case_id,
        task_id=task_id,
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
    score = score_output(_output(), _task(), _label("observed"))
    assert score.state == "claim"
    assert score.probability_score == 0.96
    assert score.utility == 0.8
    assert score.observed_positive is True
    assert score.abstained is False
    assert score.knowledge_coverage is True


def test_score_output_abstain_and_unsupported_have_no_fabricated_accuracy() -> None:
    abstained = score_output(_output("abstain"), _task(), _label("observed"))
    assert abstained.abstained is True
    assert abstained.knowledge_coverage is True
    assert abstained.probability_score is None
    assert abstained.utility == -ABSTENTION_OPPORTUNITY_COST

    no_valid_label = score_output(_output("abstain"), _task(), None)
    assert no_valid_label.utility is None
    unsupported = score_output(_output("unsupported"), _task(), _label("observed"))
    assert unsupported.abstained is False
    assert unsupported.knowledge_coverage is False
    assert unsupported.probability_score is None
    assert unsupported.utility is None


def test_high_risk_false_positive_uses_named_two_x_multiplier() -> None:
    assert HIGH_RISK_FALSE_POSITIVE_MULTIPLIER == 2.0
    ordinary = score_output(_output(), _task(), _label("not_observed"))
    high_risk = score_output(_output(), _task(high_risk=True), _label("not_observed"))
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


def test_binary_labels_are_explicitly_mapped_and_unknown_values_are_rejected() -> None:
    task = _task()
    assert binary_observed_value(task, "observed") is True
    assert binary_observed_value(task, "not_observed") is False
    negative = score_output(_output(), task, _label("not_observed"))
    assert negative.observed_positive is False
    with pytest.raises(ValueError, match="binary label"):
        binary_observed_value(task, "unknown")
    with pytest.raises(ValueError, match="binary label"):
        score_output(_output(), task, _label("unknown"))


def test_score_output_requires_label_output_and_task_identity_to_match() -> None:
    with pytest.raises(ValueError, match="case_id"):
        score_output(_output(), _task(), _label("observed", case_id="C-OTHER"))
    with pytest.raises(ValueError, match="task_id"):
        score_output(_output(), _task(), _label("observed", task_id="other.task"))
    with pytest.raises(ValueError, match="task_id"):
        score_output(_output(task_id="other.task"), _task(), _label("observed"))


@pytest.mark.parametrize("method,label", [("binary_probability", "observed"), ("time_window", 2021), ("ordinal", "high")])
def test_single_prediction_methods_reject_multiple_predictions(method: str, label: object) -> None:
    predictions = [_prediction(), _prediction(event_label="other")]
    with pytest.raises(ValueError, match="exactly one prediction"):
        score_output(_output(predictions=predictions), _task(method), _label(label))


def test_portrait_agreement_uses_event_label_and_rejects_multiple_predictions() -> None:
    task = _task("portrait_agreement", quantifiable=False)
    score = score_output(_output(prediction=_prediction(event_label="agree")), task, _label("agree", quantifiable=False))
    assert score.portrait_agreement == 1.0
    with pytest.raises(ValueError, match="exactly one prediction"):
        score_output(_output(predictions=[_prediction(event_label="agree"), _prediction(event_label="disagree")]), task, _label("agree", quantifiable=False))


def test_multiclass_probability_uses_complete_mean_brier_score() -> None:
    predictions = [_prediction(0.7, event_label="academic"), _prediction(0.2, event_label="vocational"), _prediction(0.1, event_label="mixed")]
    score = score_output(_output(predictions=predictions), _task("multiclass_probability"), _label("academic"))
    assert score.probability_score == pytest.approx(1.0 - ((0.7 - 1) ** 2 + 0.2**2 + 0.1**2) / 3)


@pytest.mark.parametrize(
    "predictions,label,error",
    [
        ([_prediction(1.0, event_label="academic")], "academic", "schema labels"),
        ([_prediction(0.5, event_label="academic"), _prediction(0.5, event_label="academic")], "academic", "schema labels"),
        (
            [_prediction(0.6, event_label="academic"), _prediction(0.3, event_label="vocational"), _prediction(0.2, event_label="mixed")],
            "academic",
            "sum",
        ),
        (
            [_prediction(0.5, event_label="academic"), _prediction(0.3, event_label="vocational"), _prediction(0.2, event_label="mixed")],
            "outside",
            "observed label",
        ),
    ],
)
def test_multiclass_probability_validates_protocol(predictions: list[BlindPrediction], label: str, error: str) -> None:
    with pytest.raises(ValueError, match=error):
        score_output(_output(predictions=predictions), _task("multiclass_probability"), _label(label))


@pytest.mark.parametrize(
    "schema",
    [
        {"type": "categorical"},
        {"type": "categorical", "labels": ["academic"]},
        {"type": "categorical", "labels": ["academic", "academic"]},
        {"type": "categorical", "labels": ["academic", ""]},
    ],
)
def test_multiclass_probability_rejects_invalid_schema_labels(schema: dict[str, object]) -> None:
    predictions = [_prediction(0.5, event_label="academic"), _prediction(0.5, event_label="vocational")]
    with pytest.raises(ValueError, match="schema labels"):
        score_output(_output(predictions=predictions), _task("multiclass_probability", label_schema=schema), _label("academic"))


@pytest.mark.parametrize(
    "predictions",
    [
        [_prediction(1.0, event_label="academic")],
        [
            _prediction(0.5, event_label="academic"),
            _prediction(0.25, event_label="vocational"),
            _prediction(0.25, event_label="outside"),
        ],
    ],
)
def test_multiclass_probability_requires_predictions_to_match_schema_exactly(predictions: list[BlindPrediction]) -> None:
    with pytest.raises(ValueError, match="schema labels"):
        score_output(_output(predictions=predictions), _task("multiclass_probability"), _label("academic"))


@pytest.mark.parametrize(
    "schema",
    [
        {"type": "boolean", "negative_label": "not_observed"},
        {"type": "boolean", "positive_label": "observed"},
        {"type": "boolean", "positive_label": None, "negative_label": "not_observed"},
        {"type": "boolean", "positive_label": "observed", "negative_label": None},
        {"type": "boolean", "positive_label": "same", "negative_label": "same"},
        {"type": "boolean", "positive_label": "", "negative_label": "not_observed"},
        {"type": "boolean", "positive_label": "observed", "negative_label": ""},
    ],
)
def test_binary_probability_rejects_invalid_label_schema(schema: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="binary label schema"):
        score_output(_output(), _task(label_schema=schema), _label("observed"))


@pytest.mark.parametrize("observed", [True, 2021.0, "2021"])
def test_time_window_score_rejects_non_integer_observed_year(observed: object) -> None:
    with pytest.raises(ValueError, match="observed_year"):
        time_window_score({"start_year": 2020, "end_year": 2022}, observed)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_year"):
        score_output(_output(prediction=_prediction(time_window={"start_year": 2020, "end_year": 2022})), _task("time_window"), _label(observed))


@pytest.mark.parametrize("args", [(True, 1, 3), (1, True, 3), (1, 1, True), (1.0, 1, 3), (1, 1.0, 3), (1, 1, 3.0)])
def test_ordinal_score_rejects_bool_and_non_integer_ranks(args: tuple[object, object, object]) -> None:
    with pytest.raises(ValueError, match="integer"):
        ordinal_score(*args)  # type: ignore[arg-type]
