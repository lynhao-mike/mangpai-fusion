"""Chart-only structure adjudication; no case or observed-outcome fixtures."""

from dataclasses import replace

import pytest

from engine.claims.domain import Claim, Evidence
from engine.claims.orchestrator import (
    ChartAdjudication,
    generate_chart_adjudication,
)
from engine.claims.runner_registry import RunnerRegistry
from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindTask


CASE_ID = "synthetic-chart-adjudication"


def _task(task_id: str = "structure.overview", claim_type: str = "structure") -> BlindTask:
    return BlindTask(
        task_id=task_id,
        domain="总体",
        claim_type=claim_type,
        scoring_method="portrait_agreement",
        quantifiable=False,
        high_risk=False,
        allowed_time_horizons=[],
        required_input_fields=["four_pillars"],
        label_schema={},
        evaluation_note="Synthetic chart-only adjudication test.",
    )


def _chart() -> ChartFactLedger:
    return ChartFactLedger(
        four_pillars={"year": "甲子", "month": "丙寅", "day": "戊辰", "hour": "庚午"},
    )


def _claim(claim_id: str, task: BlindTask, school_id: str = "synthetic") -> Claim:
    return Claim(
        claim_id=claim_id,
        school_id=school_id,
        task_id=task.task_id,
        claim_type="structure_claim",
        stance="support",
        statement=f"Synthetic structure claim {claim_id}",
        evidence=(Evidence(
            evidence_id=f"evidence-{claim_id}",
            fact_refs=("chart.four_pillars.day",),
            feature_refs=(),
            rule_id="synthetic-structure-rule",
            text="Synthetic chart fact only.",
        ),),
        falsifier="A synthetic counterexample would falsify this claim.",
        time_window=None,
        confidence_basis="Synthetic structure basis.",
        applicability_snapshot={"synthetic": True},
    )


def _registry(task: BlindTask, claims: list[Claim], school_id: str = "synthetic") -> RunnerRegistry:
    return RunnerRegistry({
        (school_id, task.task_id): lambda chart, features, requested: claims,
    })


def test_unique_chart_structure_claim_is_exposed_as_primary_without_outcome_mapping():
    task = _task()
    claim = _claim("only", task)
    result = generate_chart_adjudication(
        _chart(), task, case_id=CASE_ID, schools=["synthetic"],
        registry=_registry(task, [claim]),
    )

    assert isinstance(result, ChartAdjudication)
    assert result.state == "primary"
    assert result.primary_claim == claim
    assert result.candidate_sets[0].claims == (claim,)
    assert "primary_claim" in result.to_dict()


def test_competing_chart_claims_are_preserved_and_never_reduced_by_confidence():
    task = _task()
    low = replace(_claim("candidate-a", task), polarity="positive")
    high = replace(_claim("candidate-z", task), confidence=0.99, polarity="negative")
    result = generate_chart_adjudication(
        _chart(), task, case_id=CASE_ID, schools=["synthetic"],
        registry=_registry(task, [high, low]),
    )

    assert result.state == "unresolved"
    assert result.primary_claim is None
    assert [claim.claim_id for claim in result.candidate_sets[0].claims] == [
        "candidate-a", "candidate-z",
    ]
    assert "candidate-a, candidate-z" in result.rationale


def test_claims_from_two_schools_are_not_treated_as_a_single_winner():
    task = _task()
    first = replace(_claim("ziping-claim", task, school_id="ziping"), polarity="positive")
    second = replace(_claim("ditiansui-claim", task, school_id="ditiansui"), polarity="negative")
    registry = RunnerRegistry({
        ("ziping", task.task_id): lambda *args: [first],
        ("ditiansui", task.task_id): lambda *args: [second],
    })

    result = generate_chart_adjudication(
        _chart(), task, case_id=CASE_ID,
        schools=["ditiansui", "ziping"], registry=registry,
    )

    assert result.state == "unresolved"
    assert result.primary_claim is None
    assert [item.school_id for item in result.candidate_sets] == ["ditiansui", "ziping"]


def test_different_targets_can_form_coexisting_primary_claims():
    task = _task()
    first = replace(_claim("strength", task), target_id="structure.strength", polarity="positive")
    second = replace(_claim("relation", task), target_id="structure.relation", polarity="negative")
    registry = RunnerRegistry({
        ("synthetic", task.task_id): lambda *args: [first, second],
    })

    result = generate_chart_adjudication(
        _chart(), task, case_id=CASE_ID, schools=["synthetic"], registry=registry,
    )

    assert result.state == "primary"
    assert result.primary_claim is None
    assert {claim.claim_id for claim in result.primary_claims} == {"strength", "relation"}
    assert len(result.arbitration.stage("structure").domain_decisions) == 2


def test_chart_adjudication_preserves_abstain_and_unsupported_states():
    task = _task()
    unsupported = generate_chart_adjudication(
        _chart(), task, case_id=CASE_ID, schools=["missing"], registry=RunnerRegistry({}),
    )
    assert unsupported.state == "unsupported"
    assert unsupported.primary_claim is None

    missing_fact = replace(task, required_input_fields=["sex_marker"])
    abstain = generate_chart_adjudication(
        _chart(), missing_fact, case_id=CASE_ID, schools=["missing"],
        registry=RunnerRegistry({("missing", task.task_id): lambda *args: []}),
    )
    assert abstain.state == "abstain"
    assert abstain.candidate_sets[0].rationale == "missing required chart facts: sex_marker"


@pytest.mark.parametrize("bad_task", [_task("career.role_change"), _task(claim_type="binary")])
def test_chart_adjudication_rejects_non_structure_tasks(bad_task: BlindTask):
    with pytest.raises(ValueError):
        generate_chart_adjudication(
            _chart(), bad_task, case_id=CASE_ID, schools=["synthetic"],
            registry=RunnerRegistry({}),
        )
