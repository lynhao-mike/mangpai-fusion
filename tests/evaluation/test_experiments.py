from __future__ import annotations

from dataclasses import replace

import pytest

from engine.evaluation.experiments import experiment_group_ids, run_four_group_experiment
from engine.evaluation.models import BlindPrediction, BlindSchoolOutput, BlindTask, RevealedLabel

SCHOOLS = ["ziping", "yang_qingjuan"]
ELIGIBLE = {("C-1", "education.credentials")}


def _task() -> BlindTask:
    return BlindTask(
        task_id="education.credentials",
        domain="education",
        claim_type="binary_event",
        scoring_method="binary_probability",
        quantifiable=True,
        high_risk=False,
        allowed_time_horizons=["lifetime"],
        required_input_fields=[],
        label_schema={"positive_label": "yes", "negative_label": "no"},
        evaluation_note="test",
    )


def _output(school: str, probability: float, *, state: str = "claim", case_id: str = "C-1") -> BlindSchoolOutput:
    predictions = []
    if state == "claim":
        predictions = [BlindPrediction("P-1", "yes", probability, {}, [], "no")]
    return BlindSchoolOutput(case_id, school, "education.credentials", state, "test", predictions)


def _label(value: str = "yes", *, case_id: str = "C-1") -> RevealedLabel:
    return RevealedLabel(case_id, "education.credentials", value, "2026-01-01", "feedback", "A", True, "none")


def _run(outputs, labels=None, tasks=None, eligible=ELIGIBLE):
    return run_four_group_experiment(
        outputs,
        [_label()] if labels is None else labels,
        [_task()] if tasks is None else tasks,
        SCHOOLS,
        eligible_case_tasks=eligible,
        baseline_prevalence={"education.credentials": 0.3},
    )


def test_four_group_protocol_is_complete() -> None:
    assert experiment_group_ids(SCHOOLS) == {
        "school_only:ziping", "school_only:yang_qingjuan", "all_schools",
        "leave_one_school_out:ziping", "leave_one_school_out:yang_qingjuan",
        "baseline_plus_school:ziping", "baseline_plus_school:yang_qingjuan",
    }


def test_protocol_ids_are_deterministic_and_reject_duplicate_schools() -> None:
    assert experiment_group_ids(reversed(SCHOOLS)) == experiment_group_ids(SCHOOLS)
    with pytest.raises(ValueError, match="duplicate"):
        experiment_group_ids(["ziping", "ziping"])


def test_equal_weight_fusion_and_group_utility_gain_aggregation() -> None:
    result = _run([_output("ziping", 0.8), _output("yang_qingjuan", 0.2)])
    rows = {row.group_id: row for row in result.rows}

    assert rows["all_schools"].probability == pytest.approx(0.5)
    assert rows["leave_one_school_out:ziping"].probability == pytest.approx(0.2)
    assert rows["baseline_plus_school:ziping"].probability == pytest.approx(0.55)
    assert rows["school_only:ziping"].score == pytest.approx(0.96)
    assert result.mean_utility_by_group["all_schools"] == pytest.approx(0.75)
    assert result.incremental_gain_by_school == {"yang_qingjuan": pytest.approx(-0.21), "ziping": pytest.approx(0.39)}
    assert result.capability_incremental_gain_by_school_task() == {
        ("yang_qingjuan", "education.credentials"): pytest.approx(-0.21),
        ("ziping", "education.credentials"): pytest.approx(0.39),
    }


def test_complete_eligible_grid_rejects_missing_school_outputs() -> None:
    with pytest.raises(ValueError, match="exactly one output"):
        _run([], labels=[], eligible={("C-2", "education.credentials")})


def test_experiment_is_deterministic_and_no_claim_is_no_output() -> None:
    outputs = [_output("ziping", 0.8), _output("yang_qingjuan", 0.2, state="abstain")]
    forward = _run(outputs)
    backward = run_four_group_experiment(
        list(reversed(outputs)), [_label()], [_task()], list(reversed(SCHOOLS)),
        eligible_case_tasks=list(reversed(tuple(ELIGIBLE))), baseline_prevalence={"education.credentials": 0.3},
    )
    assert forward == backward
    rows = {row.group_id: row for row in forward.rows}
    assert rows["school_only:yang_qingjuan"].probability is None


@pytest.mark.parametrize(
    ("outputs", "labels", "tasks", "message"),
    [
        ([_output("ziping", 0.8)] * 2, [_label()], [_task()], "duplicate output"),
        ([_output("ziping", 0.8)], [_label()] * 2, [_task()], "duplicate label"),
        ([_output("ziping", 0.8)], [_label()], [_task()] * 2, "duplicate task"),
        ([], [], [_task()], "unknown task"),
    ],
)
def test_duplicate_identities_and_unknown_eligible_task_are_rejected(outputs, labels, tasks, message: str) -> None:
    eligible = {("C-1", "unknown")} if message == "unknown task" else ELIGIBLE
    with pytest.raises(ValueError, match=message):
        _run(outputs, labels, tasks, eligible)


def test_duplicate_eligible_case_task_identity_is_rejected_instead_of_deduplicated() -> None:
    with pytest.raises(ValueError, match="duplicate eligible case-task identity"):
        _run([], labels=[], eligible=[("C-1", "education.credentials"), ("C-1", "education.credentials")])


def test_unknown_output_and_label_tasks_are_rejected() -> None:
    unknown_output = replace(_output("ziping", 0.8), task_id="unknown")
    unknown_label = replace(_label(), task_id="unknown")
    with pytest.raises(ValueError, match="unknown task"):
        _run([unknown_output])
    with pytest.raises(ValueError, match="unknown task"):
        _run([], [unknown_label])


@pytest.mark.parametrize(
    ("task", "label", "message"),
    [
        (replace(_task(), label_schema={"positive_label": "yes", "negative_label": "yes"}), _label(), "binary label schema"),
        (_task(), _label("maybe"), "binary label"),
    ],
)
def test_binary_schema_and_label_follow_scoring_validation(task: BlindTask, label: RevealedLabel, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        _run([_output("ziping", 0.8), _output("yang_qingjuan", 0.6)], [label], [task])


def test_baseline_and_eligible_grid_are_explicit_keyword_only_inputs() -> None:
    with pytest.raises(TypeError):
        run_four_group_experiment([_output("ziping", 0.8)], [_label()], [_task()], SCHOOLS)
