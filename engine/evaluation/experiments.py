from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from engine.evaluation.models import BlindSchoolOutput, BlindTask, RevealedLabel
from engine.evaluation.scoring import brier_score


@dataclass(frozen=True)
class ExperimentRow:
    group_id: str
    case_id: str
    task_id: str
    probability: float | None
    score: float | None


@dataclass(frozen=True)
class ExperimentResult:
    rows: tuple[ExperimentRow, ...]
    fusion_policy: str = "equal_weight_evaluation_baseline"


def _schools(schools: Iterable[str]) -> tuple[str, ...]:
    supplied = tuple(schools)
    if len(set(supplied)) != len(supplied):
        raise ValueError("duplicate school_id")
    return tuple(sorted(supplied))


def experiment_group_ids(schools: Iterable[str]) -> set[str]:
    ordered = _schools(schools)
    return {
        "all_schools",
        *(f"school_only:{school}" for school in ordered),
        *(f"leave_one_school_out:{school}" for school in ordered),
        *(f"baseline_plus_school:{school}" for school in ordered),
    }


def _claim_probability(output: BlindSchoolOutput) -> float | None:
    if output.state != "claim":
        return None
    if len(output.predictions) != 1:
        raise ValueError("binary experiment output requires exactly one prediction")
    return output.predictions[0].probability


def run_four_group_experiment(
    outputs: Sequence[BlindSchoolOutput],
    labels: Sequence[RevealedLabel],
    tasks: Sequence[BlindTask],
    schools: Iterable[str],
    *,
    baseline_prevalence: Mapping[str, float],
) -> ExperimentResult:
    """Run deterministic equal-weight evaluation baselines, not production arbitration.

    ``baseline_prevalence`` must come from a designated development split. The
    evaluated labels are used only for scoring and never to estimate prevalence.
    """
    ordered_schools = _schools(schools)
    task_map = {task.task_id: task for task in tasks}
    label_map = {(label.case_id, label.task_id): label for label in labels}
    output_map = {(output.case_id, output.task_id, output.school_id): output for output in outputs}
    cases = sorted({(output.case_id, output.task_id) for output in outputs})
    rows: list[ExperimentRow] = []

    for case_id, task_id in cases:
        task = task_map[task_id]
        if task.scoring_method != "binary_probability":
            continue
        if task_id not in baseline_prevalence:
            raise ValueError(f"missing development baseline prevalence for {task_id}")
        baseline = baseline_prevalence[task_id]
        if not 0.0 <= baseline <= 1.0:
            raise ValueError("baseline prevalence must be between 0 and 1")
        school_probabilities = {
            school: _claim_probability(output_map[(case_id, task_id, school)])
            for school in ordered_schools
            if (case_id, task_id, school) in output_map
        }
        groups: dict[str, list[float]] = {"all_schools": [value for value in school_probabilities.values() if value is not None]}
        for school in ordered_schools:
            own = school_probabilities.get(school)
            groups[f"school_only:{school}"] = [] if own is None else [own]
            groups[f"leave_one_school_out:{school}"] = [
                value for other, value in school_probabilities.items() if other != school and value is not None
            ]
            groups[f"baseline_plus_school:{school}"] = [baseline] if own is None else [baseline, own]

        label = label_map.get((case_id, task_id))
        positive_label = task.label_schema.get("positive_label")
        for group_id in sorted(groups):
            values = groups[group_id]
            probability = sum(values) / len(values) if values else None
            score = None
            if probability is not None and label is not None and label.quantifiable:
                score = 1.0 - brier_score(probability, label.label == positive_label)
            rows.append(ExperimentRow(group_id, case_id, task_id, probability, score))
    return ExperimentResult(tuple(rows))
