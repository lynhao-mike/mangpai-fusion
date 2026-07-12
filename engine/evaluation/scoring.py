from __future__ import annotations

import math
from typing import Any

from engine.evaluation.models import BlindSchoolOutput, BlindTask, RevealedLabel, ScoreRecord

ABSTENTION_OPPORTUNITY_COST = 0.1
HIGH_RISK_FALSE_POSITIVE_MULTIPLIER = 2.0


def _validate_probability(probability: float) -> None:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be between 0 and 1")


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
    if start <= observed_year <= end:
        return 1.0
    distance = start - observed_year if observed_year < start else observed_year - end
    return 1.0 / (1.0 + distance)


def ordinal_score(predicted_rank: int, observed_rank: int, max_rank: int) -> float:
    if max_rank <= 1:
        raise ValueError("max_rank must be greater than 1")
    if not 1 <= predicted_rank <= max_rank or not 1 <= observed_rank <= max_rank:
        raise ValueError("rank must be between 1 and max_rank")
    return 1.0 - abs(predicted_rank - observed_rank) / (max_rank - 1)


def _valid_label(label: RevealedLabel | None, task: BlindTask) -> bool:
    return label is not None and label.case_id.strip() != "" and label.task_id == task.task_id


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
    label_is_valid = _valid_label(labels, task)

    if output.state == "unsupported":
        return _base_record(output, task)
    if output.state == "abstain":
        utility = -ABSTENTION_OPPORTUNITY_COST if label_is_valid and labels is not None and labels.quantifiable else None
        return _base_record(output, task, utility=utility)
    if not label_is_valid or labels is None:
        return _base_record(output, task)

    prediction = output.predictions[0]
    observed = labels.label
    if task.scoring_method == "portrait_agreement":
        agreement = float(observed)
        if not 0.0 <= agreement <= 1.0:
            raise ValueError("portrait agreement must be between 0 and 1")
        return _base_record(output, task, portrait_agreement=agreement)
    if not task.quantifiable or not labels.quantifiable:
        return _base_record(output, task)

    if task.scoring_method == "binary_probability":
        observed_positive = bool(observed)
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
        return _base_record(output, task, timing_score=time_window_score(prediction.time_window, int(observed)))
    if task.scoring_method == "ordinal":
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
        observed_positive = prediction.event_label == observed
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
    raise ValueError(f"unsupported scoring method: {task.scoring_method}")
