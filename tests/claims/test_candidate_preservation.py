"""Synthetic-only orchestration checks; no case, feedback, or rule evidence fixtures."""

from dataclasses import FrozenInstanceError, replace
from itertools import permutations

import pytest

from engine.claims.blind_adapter import claim_to_blind_output
from engine.claims.domain import Claim, Evidence, TaskUnsupported
from engine.claims.orchestrator import (
    ClaimCandidateSet,
    generate_blind_outputs,
    generate_claim_candidates,
    generate_frozen_claim_run,
)
from engine.claims.runner_registry import RunnerRegistry
from engine.decision.models import ChartFactLedger
from engine.evaluation.freeze import verify_frozen_run
from engine.evaluation.models import BlindTask


CASE_ID = "synthetic-candidate-preservation"
SCHOOL_ID = "synthetic-school"


def _task(task_id="synthetic.structure", *, required_input_fields=()):
    return BlindTask(
        task_id=task_id,
        domain="synthetic",
        claim_type="structure",
        scoring_method="synthetic-only",
        quantifiable=False,
        high_risk=False,
        allowed_time_horizons=[],
        required_input_fields=list(required_input_fields),
        label_schema={},
        evaluation_note="Artificial unit-test task; no observed outcomes.",
    )


def _chart():
    # Arbitrary pillars exercise the existing feature builder, not a real person.
    return ChartFactLedger(
        four_pillars={"year": "甲子", "month": "丙寅", "day": "戊辰", "hour": "庚午"},
    )


def _claim(claim_id, task, *, school_id=SCHOOL_ID, confidence=0.5, evidence_count=1):
    return Claim(
        claim_id=claim_id,
        school_id=school_id,
        task_id=task.task_id,
        claim_type="structure_claim",
        stance="support",
        statement=f"Artificial candidate {claim_id}",
        evidence=tuple(
            Evidence(
                evidence_id=f"synthetic-evidence-{claim_id}-{index}",
                fact_refs=("chart.four_pillars.day",),
                feature_refs=(),
                rule_id=f"synthetic-rule-{index}",
                text="Artificial evidence with no observed outcome.",
            )
            for index in range(evidence_count)
        ),
        falsifier="Synthetic counterexample would falsify this candidate.",
        time_window=None,
        confidence_basis=f"Synthetic basis for {claim_id}",
        applicability_snapshot={"synthetic": True},
        confidence=confidence,
    )


def _registry(task, claims):
    return RunnerRegistry({(SCHOOL_ID, task.task_id): lambda chart, features, requested: claims})


@pytest.mark.parametrize("order", list(permutations(range(3))))
def test_competing_candidates_are_all_retained_and_always_abstain(order):
    task = _task()
    candidates = [
        _claim("candidate-a", task, confidence=0.2),
        _claim("candidate-m", task, confidence=0.99, evidence_count=2),
        _claim("candidate-z", task, confidence=0.6, evidence_count=3),
    ]
    supplied = [candidates[index] for index in order]
    kwargs = dict(case_id=CASE_ID, schools=[SCHOOL_ID], registry=_registry(task, supplied))

    sets = generate_claim_candidates(_chart(), [task], **kwargs)
    assert len(sets) == 1
    candidate_set = sets[0]
    assert isinstance(candidate_set, ClaimCandidateSet)
    assert (candidate_set.case_id, candidate_set.school_id, candidate_set.task_id) == (
        CASE_ID, SCHOOL_ID, task.task_id,
    )
    assert candidate_set.state == "candidates"
    assert candidate_set.claims == tuple(candidates)
    assert all(actual is expected for actual, expected in zip(candidate_set.claims, candidates))
    assert supplied == [candidates[index] for index in order]
    with pytest.raises(FrozenInstanceError):
        candidate_set.state = "abstain"

    output, = generate_blind_outputs(_chart(), [task], **kwargs)
    assert output.state == "abstain"
    assert output.predictions == ()
    assert output.rationale == (
        f"unresolved competition among candidates for the same task {task.task_id}; "
        "candidate IDs: candidate-a, candidate-m, candidate-z"
    )


@pytest.mark.parametrize("as_mapping", [False, True])
def test_single_candidate_is_identical_to_existing_adapter(as_mapping):
    task = _task()
    claim = _claim("only-candidate", task, confidence=0.73, evidence_count=2)
    chart = _chart().to_dict() if as_mapping else _chart()
    kwargs = dict(case_id=CASE_ID, schools=[SCHOOL_ID], registry=_registry(task, [claim]))

    candidate_set, = generate_claim_candidates(chart, [task], **kwargs)
    assert candidate_set.state == "candidates"
    assert candidate_set.claims == (claim,)
    assert generate_blind_outputs(chart, [task], **kwargs) == [
        claim_to_blind_output(claim, case_id=CASE_ID, task=task),
    ]


def test_single_candidate_still_uses_adapter_compatibility_validation():
    task = replace(_task(), claim_type="binary")
    claim = _claim("incompatible-single", task)
    with pytest.raises(ValueError, match="incompatible claim/task types"):
        generate_blind_outputs(
            _chart(), [task], case_id=CASE_ID, schools=[SCHOOL_ID],
            registry=_registry(task, [claim]),
        )


@pytest.mark.parametrize("entrypoint", [generate_claim_candidates, generate_blind_outputs])
def test_duplicate_claim_ids_are_rejected(entrypoint):
    task = _task()
    claim = _claim("duplicate-id", task)
    claims = [claim, replace(claim, statement="A different synthetic assertion")]
    with pytest.raises(ValueError, match="duplicate claim_id: duplicate-id"):
        entrypoint(
            _chart(), [task], case_id=CASE_ID, schools=[SCHOOL_ID],
            registry=_registry(task, claims),
        )


@pytest.mark.parametrize("entrypoint", [generate_claim_candidates, generate_blind_outputs])
@pytest.mark.parametrize("wrong_field", ["school_id", "task_id"])
@pytest.mark.parametrize("with_valid_candidate", [False, True])
def test_wrong_school_or_task_is_rejected_even_among_competitors(
    entrypoint, wrong_field, with_valid_candidate,
):
    task = _task()
    valid = _claim("candidate-a", task)
    invalid = replace(_claim("candidate-z", task), **{wrong_field: "synthetic-other"})
    claims = [valid, invalid] if with_valid_candidate else [invalid]
    with pytest.raises(ValueError, match="school_id/task_id must match requested"):
        entrypoint(
            _chart(), [task], case_id=CASE_ID, schools=[SCHOOL_ID],
            registry=_registry(task, claims),
        )


@pytest.mark.parametrize("entrypoint", [generate_claim_candidates, generate_blind_outputs])
@pytest.mark.parametrize("different_definition", [False, True])
def test_duplicate_task_ids_are_rejected_before_dispatch(entrypoint, different_definition):
    task = _task()
    duplicate = replace(task, claim_type="portrait") if different_definition else task

    def unexpected_runner(*args):
        pytest.fail("duplicate tasks must be rejected before dispatch")

    registry = RunnerRegistry({(SCHOOL_ID, task.task_id): unexpected_runner})
    with pytest.raises(ValueError, match="duplicate task_id: synthetic.structure"):
        entrypoint(_chart(), [task, duplicate], case_id=CASE_ID, schools=[SCHOOL_ID], registry=registry)


@pytest.mark.parametrize("different_school", [False, True])
def test_duplicate_claim_ids_across_candidate_sets_are_rejected(different_school):
    task = _task()
    other_task = task if different_school else _task("synthetic.other-task")
    other_school = "synthetic-other-school" if different_school else SCHOOL_ID
    first = _claim("reused-id", task)
    second = _claim("reused-id", other_task, school_id=other_school)
    registry = RunnerRegistry({
        (SCHOOL_ID, task.task_id): lambda *args: [first],
        (other_school, other_task.task_id): lambda *args: [second],
    })
    with pytest.raises(ValueError, match="duplicate claim_id: reused-id"):
        generate_claim_candidates(
            _chart(), [task] if different_school else [task, other_task],
            case_id=CASE_ID, schools=[SCHOOL_ID, other_school], registry=registry,
        )


@pytest.mark.parametrize("scenario", ["empty", "missing", "features", "unregistered", "unsupported"])
def test_zero_candidate_and_unsupported_paths_preserve_existing_behavior(scenario):
    task = _task(required_input_fields=("sex_marker",) if scenario == "missing" else ())
    chart = ChartFactLedger() if scenario in {"features", "unregistered"} else _chart()

    def runner(*args):
        if scenario == "unsupported":
            raise TaskUnsupported("Synthetic task is outside this runner")
        if scenario != "empty":
            pytest.fail("incomplete or unregistered requests must not reach the runner")
        return []

    registry = RunnerRegistry({} if scenario == "unregistered" else {(SCHOOL_ID, task.task_id): runner})
    kwargs = dict(case_id=CASE_ID, schools=[SCHOOL_ID], registry=registry)
    candidate_set, = generate_claim_candidates(chart, [task], **kwargs)
    output, = generate_blind_outputs(chart, [task], **kwargs)
    expected_state, expected_rationale = {
        "empty": ("abstain", "runner covers this task but chart facts do not satisfy a production trigger"),
        "missing": ("abstain", "missing required chart facts: sex_marker"),
        "features": (
            "abstain", "chart facts are insufficient to build cfv-v1: "
            "month and day pillars are required to build ChartFeatureVector",
        ),
        "unregistered": ("unsupported", "no independent L2 claim generator is registered for this school"),
        "unsupported": ("unsupported", "Synthetic task is outside this runner"),
    }[scenario]
    assert candidate_set.claims == ()
    assert output.predictions == ()
    assert candidate_set.state == output.state == expected_state
    assert candidate_set.rationale == output.rationale == expected_rationale


def test_candidates_stay_in_requested_school_task_and_input_order_is_irrelevant():
    first, second = _task("synthetic.a"), _task("synthetic.z")
    schools = ["synthetic-a", "synthetic-z"]
    registrations = []
    expected = {}
    for school in schools:
        for task in (first, second):
            claims = [
                _claim(f"{school}-{task.task_id}-{index}", task, school_id=school)
                for index in range(2 if task == first else 1)
            ]
            expected[school, task.task_id] = tuple(claims)
            registrations.append((school, task.task_id, lambda *args, claims=claims: claims))
    registry = RunnerRegistry(registrations)

    forward = generate_claim_candidates(
        _chart(), [first, second], case_id=CASE_ID, schools=schools, registry=registry,
    )
    backward = generate_claim_candidates(
        _chart(), [second, first], case_id=CASE_ID, schools=schools[::-1] + schools, registry=registry,
    )
    assert forward == backward
    assert [(row.school_id, row.task_id) for row in forward] == sorted(expected)
    for row in forward:
        assert row.claims == expected[row.school_id, row.task_id]
    outputs = generate_blind_outputs(
        _chart(), [second, first], case_id=CASE_ID, schools=schools[::-1], registry=registry,
    )
    assert [(row.school_id, row.task_id) for row in outputs] == sorted(expected)
    for output in outputs:
        assert output.state == ("abstain" if output.task_id == first.task_id else "claim")


def test_frozen_entry_preserves_abstention_and_is_independent_of_candidate_order():
    task = _task()
    claims = [_claim("candidate-z", task), _claim("candidate-a", task)]
    kwargs = dict(
        case_id=CASE_ID, schools=[SCHOOL_ID], task_catalog_version="synthetic-v1",
        rule_snapshot_id="synthetic-rules-v1", frozen_at="2000-01-01T00:00:00Z",
    )
    first = generate_frozen_claim_run(_chart(), [task], registry=_registry(task, claims), **kwargs)
    second = generate_frozen_claim_run(_chart(), [task], registry=_registry(task, claims[::-1]), **kwargs)
    assert first == second
    verify_frozen_run(first)
    output, = first.outputs
    assert output.state == "abstain"
    assert output.predictions == ()
    assert "candidate-a, candidate-z" in output.rationale
