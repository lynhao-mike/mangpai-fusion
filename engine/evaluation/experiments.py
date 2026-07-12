from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal, ROUND_HALF_UP
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field

from engine.evaluation.models import BlindPrediction, BlindSchoolOutput, BlindTask, RevealedLabel
from engine.evaluation.scoring import HIGH_RISK_FALSE_POSITIVE_MULTIPLIER, score_output


@dataclass(frozen=True)
class ExperimentRow:
    group_id: str
    case_id: str
    task_id: str
    probability: float | None
    score: float | None
    utility: float | None = None
    requested_members: tuple[str, ...] = ()
    contributing_members: tuple[str, ...] = ()
    excluded_members: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExperimentResult:
    rows: tuple[ExperimentRow, ...]
    fusion_policy: str = "equal_weight_evaluation_baseline"
    mean_utility_by_group: Mapping[str, float] = field(default_factory=dict)
    incremental_gain_by_school: Mapping[str, float] = field(default_factory=dict)

    def capability_incremental_gain_by_school_task(self) -> dict[tuple[str, str], float]:
        grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
        for row in self.rows:
            if row.utility is None:
                continue
            school = "all_schools" if row.group_id == "all_schools" else row.group_id.removeprefix("leave_one_school_out:")
            if row.group_id == "all_schools" or row.group_id.startswith("leave_one_school_out:"):
                grouped[(school, row.task_id)].append(row.utility)
        all_means = {task: sum(values) / len(values) for (school, task), values in grouped.items() if school == "all_schools"}
        return {(school, task): all_means[task] - sum(values) / len(values) for (school, task), values in sorted(grouped.items()) if school != "all_schools" and task in all_means}


def _schools(schools: Iterable[str]) -> tuple[str, ...]:
    supplied = tuple(schools)
    if len(set(supplied)) != len(supplied):
        raise ValueError("duplicate school_id")
    if any(not school for school in supplied):
        raise ValueError("school_id must be non-empty")
    return tuple(sorted(supplied))


def experiment_group_ids(schools: Iterable[str]) -> set[str]:
    ordered = _schools(schools)
    return {"all_schools", *(f"school_only:{school}" for school in ordered), *(f"leave_one_school_out:{school}" for school in ordered), *(f"baseline_plus_school:{school}" for school in ordered)}


def _unique_map(items: Sequence, key, name: str) -> dict:
    result = {}
    for item in items:
        identity = key(item)
        if identity in result:
            raise ValueError(f"duplicate {name} identity")
        result[identity] = item
    return result


def _round_half_up(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _fuse(outputs: list[BlindSchoolOutput], task: BlindTask, baseline: float | None = None) -> BlindSchoolOutput | None:
    claims = [output for output in outputs if output.state == "claim"]
    if not claims and baseline is None:
        return None
    if task.scoring_method == "multiclass_probability":
        labels = tuple(task.label_schema["labels"])
        probabilities = {label: [] for label in labels}
        for output in claims:
            by_label = {prediction.event_label: prediction.probability for prediction in output.predictions}
            for label in labels:
                probabilities[label].append(by_label[label])
        if baseline is not None:
            for label in labels:
                probabilities[label].append(baseline if label == labels[0] else (1.0 - baseline) / (len(labels) - 1))
        predictions = [BlindPrediction(f"fused-{index}", label, sum(values) / len(values), {}, (), "evaluation fusion") for index, (label, values) in enumerate(probabilities.items())]
    else:
        source = [output.predictions[0] for output in claims]
        if task.scoring_method == "binary_probability":
            values = [prediction.probability for prediction in source] + ([] if baseline is None else [baseline])
            predictions = [BlindPrediction("fused", source[0].event_label if source else str(task.label_schema["positive_label"]), sum(values) / len(values), source[0].time_window if source else {}, (), "evaluation fusion")]
        elif task.scoring_method == "ordinal" and source:
            labels = tuple(task.label_schema["labels"])
            ranks = [labels.index(item.event_label) + 1 for item in source]
            rank = _round_half_up(sum(ranks) / len(ranks))
            predictions = [BlindPrediction("fused", labels[rank - 1], 1.0, {}, (), "evaluation fusion")]
        elif task.scoring_method == "time_window" and source:
            starts = [item.time_window["start_year"] for item in source]
            ends = [item.time_window["end_year"] for item in source]
            start, end = _round_half_up(sum(starts) / len(starts)), _round_half_up(sum(ends) / len(ends))
            if start > end:
                raise ValueError("fused window requires start_year <= end_year")
            predictions = [BlindPrediction("fused", source[0].event_label, 1.0, {"start_year": start, "end_year": end}, (), "evaluation fusion")]
        elif task.scoring_method == "portrait_agreement" and source:
            counts = Counter(item.event_label for item in source)
            winner = min(counts, key=lambda item: (-counts[item], item))
            predictions = [BlindPrediction("fused", winner, 1.0, {}, (), "evaluation fusion")]
        elif source:
            predictions = [source[0]]
        else:
            return None
    return BlindSchoolOutput("fused", "group", task.task_id, "claim", "equal-weight evaluation fusion", predictions)


def _proper_value(output: BlindSchoolOutput | None, task: BlindTask, label: RevealedLabel | None) -> tuple[float | None, float | None, float | None]:
    if output is None or label is None:
        return None, None, None
    bound_output = BlindSchoolOutput(label.case_id, output.school_id, task.task_id, output.state, output.rationale, output.predictions)
    record = score_output(bound_output, task, label)
    value = next((item for item in (record.probability_score, record.timing_score, record.ordinal_score, record.portrait_agreement) if item is not None), None)
    if task.scoring_method == "portrait_agreement":
        utility = None
    elif task.scoring_method in {"time_window", "multiclass_probability"} and record.utility is not None:
        utility = record.utility
    else:
        utility = value
        if task.high_risk and record.observed_positive is False and value is not None:
            utility = 1.0 - HIGH_RISK_FALSE_POSITIVE_MULTIPLIER * (1.0 - value)
    probability = output.predictions[0].probability if task.scoring_method == "binary_probability" else None
    return probability, value, utility


def run_four_group_experiment(
    outputs: Sequence[BlindSchoolOutput],
    labels: Sequence[RevealedLabel],
    tasks: Sequence[BlindTask],
    schools: Iterable[str],
    *,
    eligible_case_tasks: Collection[tuple[str, str]],
    baseline_prevalence: Mapping[str, float],
) -> ExperimentResult:
    ordered_schools = _schools(schools)
    eligible_grid = tuple(eligible_case_tasks)
    if len(set(eligible_grid)) != len(eligible_grid):
        raise ValueError("duplicate eligible case-task identity")
    task_map = _unique_map(tasks, lambda task: task.task_id, "task")
    label_map = _unique_map(labels, lambda label: (label.case_id, label.task_id), "label")
    output_map = _unique_map(outputs, lambda output: (output.case_id, output.task_id, output.school_id), "output")
    referenced = {task_id for _, task_id in eligible_grid} | {item.task_id for item in labels} | {item.task_id for item in outputs}
    unknown = referenced - set(task_map)
    if unknown:
        raise ValueError(f"unknown task: {sorted(unknown)[0]}")
    expected = {(case_id, task_id, school) for case_id, task_id in eligible_grid for school in ordered_schools}
    if set(output_map) != expected:
        raise ValueError("each eligible case-task and expected school requires exactly one output")

    rows = []
    for case_id, task_id in sorted(eligible_grid):
        task = task_map[task_id]
        baseline = baseline_prevalence.get(task_id)
        if task.scoring_method == "binary_probability" and (not isinstance(baseline, (int, float)) or not 0.0 <= baseline <= 1.0):
            raise ValueError(f"missing or invalid development baseline prevalence for {task_id}")
        school_outputs = {school: output_map[(case_id, task_id, school)] for school in ordered_schools}
        groups = {"all_schools": list(school_outputs.values())}
        for school in ordered_schools:
            groups[f"school_only:{school}"] = [school_outputs[school]]
            groups[f"leave_one_school_out:{school}"] = [value for other, value in school_outputs.items() if other != school]
            groups[f"baseline_plus_school:{school}"] = [school_outputs[school]]
        for group_id, group_outputs in sorted(groups.items()):
            group_baseline = baseline if group_id.startswith("baseline_plus_school:") and task.scoring_method == "binary_probability" else None
            fused = _fuse(group_outputs, task, group_baseline)
            probability, score, utility = _proper_value(fused, task, label_map.get((case_id, task_id)))
            requested = tuple(sorted(output.school_id for output in group_outputs))
            contributing = tuple(sorted(output.school_id for output in group_outputs if output.state == "claim"))
            excluded = tuple(sorted(set(requested) - set(contributing)))
            rows.append(ExperimentRow(group_id, case_id, task_id, probability, score, utility, requested, contributing, excluded))

    utilities: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if row.utility is not None:
            utilities[row.group_id].append(row.utility)
    means = {group: sum(values) / len(values) for group, values in sorted(utilities.items())}
    gains = {school: means["all_schools"] - means[group] for school in ordered_schools if "all_schools" in means and (group := f"leave_one_school_out:{school}") in means}
    return ExperimentResult(tuple(rows), mean_utility_by_group=means, incremental_gain_by_school=gains)
