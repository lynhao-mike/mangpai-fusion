from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import replace
from pathlib import Path

import pytest

from engine.application.pipeline_runner import run_pipeline
from engine.claims.runner_registry import DEFAULT_RUNNER_REGISTRY
from engine.decision.ren_career_timing_slice import (
    build_ren_career_timing_slice,
    to_blind_output,
)
from engine.evaluation.freeze import canonical_json, freeze_outputs, verify_frozen_run
from engine.evaluation.models import BlindPrediction, BlindSchoolOutput
from engine.features import build_chart_feature_vector


def _sha256(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _build(case_id, chart, event, *, task_id="career.role_change"):
    return build_ren_career_timing_slice(
        case_id,
        chart,
        build_chart_feature_vector(chart),
        event,
        task_id=task_id,
    )


def _freeze(output: BlindSchoolOutput):
    return freeze_outputs(
        [output],
        "prospective-go-task-catalog/v1",
        "ren-career-timing-rules/v1",
    )


def test_first_falsifier_produces_zero_l5(no_trigger_chart, career_event) -> None:
    result, timings = _build("C-REN-NO-TRIGGER", no_trigger_chart, career_event)

    assert result.publication_state.value != "emit"
    assert timings == ()


def test_emit_builds_exactly_one_l5(trigger_chart, career_event) -> None:
    result, timings = _build("C-REN-TIMING-001", trigger_chart, career_event)

    assert result.publication_state.value == "emit"
    assert len(timings) == 1
    assert timings[0].event_id == career_event.event_id


def test_blind_output_projects_exact_contract_and_separates_evidence_accounts(
    trigger_chart, career_event
) -> None:
    result, timings = _build("C-REN-TIMING-001", trigger_chart, career_event)

    output = to_blind_output("C-REN-TIMING-001", result, timings)

    assert isinstance(output, BlindSchoolOutput)
    assert output.case_id == "C-REN-TIMING-001"
    assert output.school_id == "ren"
    assert output.task_id == "career.role_change"
    assert output.state == "claim"
    assert output.rationale.strip()
    assert len(output.predictions) == 1
    prediction = output.predictions[0]
    assert isinstance(prediction, BlindPrediction)
    assert prediction.prediction_id == timings[0].prediction_id
    assert prediction.event_label == "career.role_change"
    assert prediction.probability == timings[0].confidence
    assert prediction.time_window == timings[0].time_window
    assert prediction.falsifier == timings[0].falsifier
    assert prediction.evidence_refs
    assert prediction.fact_refs
    assert all("#" in ref for ref in prediction.evidence_refs)
    assert all("#" not in ref for ref in prediction.fact_refs)
    assert sorted((*prediction.evidence_refs, *prediction.fact_refs)) == sorted(
        timings[0].trigger_conditions
    )


def test_staged_freeze_hash_verifies_and_rerun_is_byte_stable(
    trigger_chart, career_event
) -> None:
    result, timings = _build("C-REN-TIMING-001", trigger_chart, career_event)
    output = to_blind_output("C-REN-TIMING-001", result, timings)

    first = _freeze(output)
    second = _freeze(output)

    verify_frozen_run(first)
    verify_frozen_run(second)
    assert first.freeze_hash == second.freeze_hash
    assert canonical_json(first.to_dict()).encode("utf-8") == canonical_json(
        second.to_dict()
    ).encode("utf-8")


def test_liunian_permutation_keeps_result_l5_and_frozen_bytes_stable(
    trigger_chart, career_event
) -> None:
    reversed_chart = replace(
        trigger_chart,
        liunian_steps=list(reversed(trigger_chart.liunian_steps)),
    )

    left = _build("C-REN-PERMUTE", trigger_chart, career_event)
    right = _build("C-REN-PERMUTE", reversed_chart, career_event)
    left_output = to_blind_output("C-REN-PERMUTE", *left)
    right_output = to_blind_output("C-REN-PERMUTE", *right)

    assert left[0].to_dict() == right[0].to_dict()
    assert [item.to_dict() for item in left[1]] == [item.to_dict() for item in right[1]]
    assert left[1][0].prediction_id == right[1][0].prediction_id
    assert left[1][0].trigger_conditions == right[1][0].trigger_conditions
    assert left_output.to_dict() == right_output.to_dict()
    assert canonical_json(_freeze(left_output).to_dict()) == canonical_json(
        _freeze(right_output).to_dict()
    )


@pytest.mark.parametrize(
    ("case_id", "event", "task_id", "expected_state"),
    [
        ("C-REN-ABSTAIN", None, "career.role_change", "abstain"),
        ("C-REN-UNSUPPORTED", "career_event", "marriage.event", "unsupported"),
    ],
)
def test_abstain_and_unsupported_blind_outputs_never_contain_predictions(
    request, trigger_chart, case_id, event, task_id, expected_state
) -> None:
    selected_event = request.getfixturevalue(event) if event else None
    result, timings = _build(case_id, trigger_chart, selected_event, task_id=task_id)

    output = to_blind_output(case_id, result, timings)

    assert timings == ()
    assert output.state == expected_state
    assert output.predictions == ()
    assert output.rationale.strip()


def test_ren_staged_work_starts_from_unchanged_production_boundaries() -> None:
    registrations = sorted(
        (school, task, fn.__module__ + "." + fn.__name__)
        for (school, task), fn in DEFAULT_RUNNER_REGISTRY._runners.items()
    )
    assert hashlib.sha256(json.dumps(registrations, separators=(",", ":")).encode()).hexdigest() == (
        "88779529d0d470d80558b2005a79089950adfc4deaf3d96e7b7d20bd78c0b16d"
    )
    assert "ren_career_timing" not in str(inspect.signature(run_pipeline))
    assert _sha256("theory/production/claim-rules-v1.yaml") == (
        "6396883d8db0b8d24c6c15435c130c6f9ae045c8c6d1fe8d2a84748c5b0bebef"
    )
