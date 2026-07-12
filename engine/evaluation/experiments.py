from __future__ import annotations

from collections import defaultdict
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field

from engine.evaluation.models import BlindSchoolOutput, BlindTask, RevealedLabel
from engine.evaluation.scoring import binary_observed_value, brier_score


@dataclass(frozen=True)
class ExperimentRow:
    group_id: str
    case_id: str
    task_id: str
    probability: float | None
    score: float | None
    utility: float | None = None


@dataclass(frozen=True)
class ExperimentResult:
    rows: tuple[ExperimentRow, ...]
    fusion_policy: str = "equal_weight_evaluation_baseline"
    mean_utility_by_group: Mapping[str, float] = field(default_factory=dict)
    incremental_gain_by_school: Mapping[str, float] = field(default_factory=dict)

    def capability_incremental_gain_by_school_task(self) -> dict[tuple[str, str], float]:
        """Return task-level gains; callers expand these into six-dimensional identities."""
        grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
        for row in self.rows:
            if row.group_id == "all_schools" and row.utility is not None:
                grouped[("all_schools", row.task_id)].append(row.utility)
            elif row.group_id.startswith("leave_one_school_out:") and row.utility is not None:
                grouped[(row.group_id.removeprefix("leave_one_school_out:"), row.task_id)].append(row.utility)
        all_means = {task: sum(values) / len(values) for (school, task), values in grouped.items() if school == "all_schools"}
        return {
            (school, task): all_means[task] - sum(values) / len(values)
            for (school, task), values in sorted(grouped.items())
            if school != "all_schools" and task in all_means
        }


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


def _unique_map(items: Sequence, key, name: str) -> dict:
    result = {}
    for item in items:
        identity = key(item)
        if identity in result:
            raise ValueError(f"duplicate {name} identity")
        result[identity] = item
    return result


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
    eligible_case_tasks: Collection[tuple[str, str]],
    baseline_prevalence: Mapping[str, float],
) -> ExperimentResult:
    """Run deterministic equal-weight evaluation baselines over an explicit grid."""
    ordered_schools = _schools(schools)
    eligible_grid = tuple(eligible_case_tasks)
    if len(set(eligible_grid)) != len(eligible_grid):
        raise ValueError("duplicate eligible case-task identity")
    task_map = _unique_map(tasks, lambda task: task.task_id, "task")
    label_map = _unique_map(labels, lambda label: (label.case_id, label.task_id), "label")
    output_map = _unique_map(outputs, lambda output: (output.case_id, output.task_id, output.school_id), "output")

    known_tasks = set(task_map)
    referenced_tasks = {task_id for _, task_id in eligible_grid} | {label.task_id for label in labels} | {output.task_id for output in outputs}
    unknown = referenced_tasks - known_tasks
    if unknown:
        raise ValueError(f"unknown task: {sorted(unknown)[0]}")

    rows: list[ExperimentRow] = []
    for case_id, task_id in sorted(eligible_grid):
        task = task_map[task_id]
        if task.scoring_method != "binary_probability":
            continue
        if task_id not in baseline_prevalence:
            raise ValueError(f"missing development baseline prevalence for {task_id}")
        baseline = baseline_prevalence[task_id]
        if not 0.0 <= baseline <= 1.0:
            raise ValueError("baseline prevalence must be between 0 and 1")
        label = label_map.get((case_id, task_id))
        observed_positive = None
        if label is not None and label.quantifiable:
            observed_positive = binary_observed_value(task, label.label)

        school_probabilities = {
            school: _claim_probability(output_map[(case_id, task_id, school)])
            for school in ordered_schools
            if (case_id, task_id, school) in output_map
        }
        groups: dict[str, list[float]] = {"all_schools": [value for value in school_probabilities.values() if value is not None]}
        for school in ordered_schools:
            own = school_probabilities.get(school)
            groups[f"school_only:{school}"] = [] if own is None else [own]
            groups[f"leave_one_school_out:{school}"] = [value for other, value in school_probabilities.items() if other != school and value is not None]
            groups[f"baseline_plus_school:{school}"] = [baseline] if own is None else [baseline, own]

        for group_id in sorted(groups):
            values = groups[group_id]
            probability = sum(values) / len(values) if values else None
            score = None if probability is None or observed_positive is None else 1.0 - brier_score(probability, observed_positive)
            utility = None if probability is None or observed_positive is None else (probability if observed_positive else -probability)
            rows.append(ExperimentRow(group_id, case_id, task_id, probability, score, utility))

    utilities: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if row.utility is not None:
            utilities[row.group_id].append(row.utility)
    means = {group: sum(values) / len(values) for group, values in sorted(utilities.items())}
    gains = {
        school: means["all_schools"] - means[group]
        for school in ordered_schools
        if "all_schools" in means and (group := f"leave_one_school_out:{school}") in means
    }
    return ExperimentResult(tuple(rows), mean_utility_by_group=means, incremental_gain_by_school=gains)
