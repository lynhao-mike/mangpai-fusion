from __future__ import annotations

import pytest

from engine.evaluation.experiments import experiment_group_ids, run_four_group_experiment
from engine.evaluation.models import BlindPrediction, BlindSchoolOutput, BlindTask, RevealedLabel


SCHOOLS = ["ziping", "yang_qingjuan"]


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


def _output(school: str, probability: float, *, state: str = "claim") -> BlindSchoolOutput:
    predictions = []
    if state == "claim":
        predictions = [BlindPrediction("P-1", "yes", probability, {}, [], "no")]
    return BlindSchoolOutput("C-1", school, "education.credentials", state, "test", predictions)


def _label(value: str = "yes") -> RevealedLabel:
    return RevealedLabel("C-1", "education.credentials", value, "2026-01-01", "feedback", "A", True, "none")


def test_four_group_protocol_is_complete() -> None:
    assert experiment_group_ids(SCHOOLS) == {
        "school_only:ziping",
        "school_only:yang_qingjuan",
        "all_schools",
        "leave_one_school_out:ziping",
        "leave_one_school_out:yang_qingjuan",
        "baseline_plus_school:ziping",
        "baseline_plus_school:yang_qingjuan",
    }


def test_protocol_ids_are_deterministic_and_reject_duplicate_schools() -> None:
    assert experiment_group_ids(reversed(SCHOOLS)) == experiment_group_ids(SCHOOLS)
    with pytest.raises(ValueError, match="duplicate"):
        experiment_group_ids(["ziping", "ziping"])


def test_equal_weight_fusion_excludes_nonclaims_and_uses_explicit_development_prevalence() -> None:
    outputs = [_output("ziping", 0.8), _output("yang_qingjuan", 0.2), _output("ignored", 0.9, state="unsupported")]
    prevalence = {"education.credentials": 0.3}

    result = run_four_group_experiment(outputs, [_label("yes")], [_task()], SCHOOLS, baseline_prevalence=prevalence)
    rows = {row.group_id: row for row in result.rows}

    assert rows["all_schools"].probability == pytest.approx(0.5)
    assert rows["leave_one_school_out:ziping"].probability == pytest.approx(0.2)
    assert rows["baseline_plus_school:ziping"].probability == pytest.approx(0.55)
    assert rows["school_only:ziping"].score == pytest.approx(0.96)
    assert result.fusion_policy == "equal_weight_evaluation_baseline"


def test_baseline_is_never_inferred_from_evaluated_labels() -> None:
    with pytest.raises(TypeError):
        run_four_group_experiment([_output("ziping", 0.8)], [_label()], [_task()], SCHOOLS)


def test_experiment_is_deterministic_and_no_claim_is_no_output() -> None:
    outputs = [_output("ziping", 0.8), _output("yang_qingjuan", 0.2, state="abstain")]
    kwargs = {"baseline_prevalence": {"education.credentials": 0.3}}
    forward = run_four_group_experiment(outputs, [_label()], [_task()], SCHOOLS, **kwargs)
    backward = run_four_group_experiment(list(reversed(outputs)), [_label()], [_task()], list(reversed(SCHOOLS)), **kwargs)

    assert forward == backward
    rows = {row.group_id: row for row in forward.rows}
    assert rows["school_only:yang_qingjuan"].probability is None
    assert rows["school_only:yang_qingjuan"].score is None
