from __future__ import annotations

import math
from typing import Any

from engine.evaluation.models import BlindSchoolOutput, BlindTask, RevealedLabel, ScoreRecord

ABSTENTION_OPPORTUNITY_COST = 0.1
HIGH_RISK_FALSE_POSITIVE_MULTIPLIER = 2.0


def _validate_probability(probability: float) -> None:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be between 0 and 1")


def binary_observed_value(task: BlindTask, label: object) -> bool:
    positive_label = task.label_schema.get("positive_label")
    negative_label = task.label_schema.get("negative_label")
    if (
        not isinstance(positive_label, str)
        or not positive_label
        or not isinstance(negative_label, str)
        or not negative_label
        or positive_label == negative_label
    ):
        raise ValueError("binary label schema requires distinct non-empty string positive_label and negative_label")
    if label == positive_label:
        return True
    if label == negative_label:
        return False
    raise ValueError("binary label must match positive_label or negative_label")


def brier_score(probability: float, observed: bool) -> float:
    _validate_probability(probability)
    return round((probability - float(observed)) ** 2, 12)


def log_loss(probability: float, observed: bool, epsilon: float = 1e-15) -> float:
    _validate_probability(probability)
    if not 0.0 < epsilon < 0.5:
        raise ValueError("epsilon must be between 0 and 0.5")
    bounded = min(max(probability, epsilon), 1.0 - epsilon)
    return -math.log(bounded if observed else 1.0 - bounded)


def time_window_score(predicted: dict[str, int], observed_year: int) -> float:
    start = predicted.get("start_year")
    end = predicted.get("end_year")
    if type(start) is not int or type(end) is not int or start > end:
        raise ValueError("window requires integer start_year <= end_year")
    if type(observed_year) is not int:
        raise ValueError("observed_year must be an integer")
    if start <= observed_year <= end:
        return 1.0
    distance = start - observed_year if observed_year < start else observed_year - end
    return 1.0 / (1.0 + distance)


def ordinal_score(predicted_rank: int, observed_rank: int, max_rank: int) -> float:
    if any(type(value) is not int for value in (predicted_rank, observed_rank, max_rank)):
        raise ValueError("predicted_rank, observed_rank, and max_rank must be integers")
    if max_rank <= 1:
        raise ValueError("max_rank must be greater than 1")
    if not 1 <= predicted_rank <= max_rank or not 1 <= observed_rank <= max_rank:
        raise ValueError("rank must be between 1 and max_rank")
    return 1.0 - abs(predicted_rank - observed_rank) / (max_rank - 1)


def _validate_label_identity(label: RevealedLabel | None, output: BlindSchoolOutput, task: BlindTask) -> bool:
    if label is None:
        return False
    if label.case_id != output.case_id:
        raise ValueError("label and output case_id must match")
    if label.task_id != output.task_id or output.task_id != task.task_id:
        raise ValueError("label, output, and task task_id must match")
    return True


def _require_prediction_count(output: BlindSchoolOutput, minimum: int, maximum: int | None = None) -> None:
    count = len(output.predictions)
    if count < minimum:
        quantity = "two" if minimum == 2 else str(minimum)
        raise ValueError(f"scoring method requires at least {quantity} predictions")
    if maximum is not None and count > maximum:
        raise ValueError("scoring method requires exactly one prediction")


def _base_record(output: BlindSchoolOutput, task: BlindTask, **scores: Any) -> ScoreRecord:
    return ScoreRecord(
        case_id=output.case_id,
        school_id=output.school_id,
        task_id=output.task_id,
        claim_type=task.claim_type,
        state=output.state,
        abstained=output.state == "abstain",
        knowledge_coverage=output.state != "unsupported",
        **scores,
    )


def score_output(
    output: BlindSchoolOutput,
    task: BlindTask,
    labels: RevealedLabel | None,
) -> ScoreRecord:
    if output.task_id != task.task_id:
        raise ValueError("output and task task_id must match")
    label_is_valid = _validate_label_identity(labels, output, task)

    if output.state == "unsupported":
        return _base_record(output, task)
    if output.state == "abstain":
        utility = -ABSTENTION_OPPORTUNITY_COST if label_is_valid and labels is not None and labels.quantifiable else None
        return _base_record(output, task, utility=utility)
    if not label_is_valid or labels is None:
        return _base_record(output, task)

    observed = labels.label
    if task.scoring_method == "portrait_agreement":
        _require_prediction_count(output, 1, 1)
        if type(observed) in (int, float):
            agreement = float(observed)
            if not 0.0 <= agreement <= 1.0:
                raise ValueError("portrait agreement must be between 0 and 1")
        else:
            agreement = float(output.predictions[0].event_label == observed)
        return _base_record(output, task, portrait_agreement=agreement)
    if not task.quantifiable or not labels.quantifiable:
        return _base_record(output, task)

    if task.scoring_method == "binary_probability":
        _require_prediction_count(output, 1, 1)
        prediction = output.predictions[0]
        observed_positive = binary_observed_value(task, observed)
        accuracy = 1.0 - brier_score(prediction.probability, observed_positive)
        utility = prediction.probability if observed_positive else -prediction.probability
        if task.high_risk and not observed_positive:
            utility *= HIGH_RISK_FALSE_POSITIVE_MULTIPLIER
        return _base_record(
            output,
            task,
            probability_score=accuracy,
            utility=utility,
            observed_positive=observed_positive,
        )
    if task.scoring_method == "time_window":
        _require_prediction_count(output, 1, 1)
        if type(observed) is not int:
            raise ValueError("observed_year must be an integer")
        return _base_record(output, task, timing_score=time_window_score(output.predictions[0].time_window, observed))
    if task.scoring_method == "ordinal":
        _require_prediction_count(output, 1, 1)
        prediction = output.predictions[0]
        labels_in_order = task.label_schema.get("labels", [])
        try:
            predicted_rank = labels_in_order.index(prediction.event_label) + 1
            observed_rank = labels_in_order.index(observed) + 1
        except ValueError as error:
            raise ValueError("ordinal value is absent from task labels") from error
        return _base_record(
            output,
            task,
            ordinal_score=ordinal_score(predicted_rank, observed_rank, len(labels_in_order)),
        )
    if task.scoring_method == "multiclass_probability":
        schema_labels = task.label_schema.get("labels")
        if (
            not isinstance(schema_labels, (list, tuple))
            or len(schema_labels) < 2
            or any(not isinstance(label, str) or not label for label in schema_labels)
            or len(set(schema_labels)) != len(schema_labels)
        ):
            raise ValueError("multiclass schema labels must contain at least two unique non-empty strings")
        labels = [prediction.event_label for prediction in output.predictions]
        if len(labels) != len(schema_labels) or set(labels) != set(schema_labels):
            raise ValueError("multiclass prediction event_label set must exactly match schema labels")
        if not math.isclose(sum(prediction.probability for prediction in output.predictions), 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError("multiclass probabilities must sum to 1")
        if observed not in schema_labels:
            raise ValueError("observed label must be one of the schema labels")
        probabilities = {prediction.event_label: prediction.probability for prediction in output.predictions}
        mean_brier = sum(
            (probabilities[label] - float(label == observed)) ** 2
            for label in schema_labels
        ) / len(schema_labels)
        observed_prediction = next(prediction for prediction in output.predictions if prediction.event_label == observed)
        return _base_record(
            output,
            task,
            probability_score=round(1.0 - mean_brier, 12),
            utility=observed_prediction.probability,
            observed_positive=True,
        )
    raise ValueError(f"unsupported scoring method: {task.scoring_method}")
