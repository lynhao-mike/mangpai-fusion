from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from engine.evaluation.capability import build_capability_posteriors
from engine.evaluation.experiments import run_four_group_experiment
from engine.evaluation.freeze import freeze_outputs, reveal_labels
from engine.evaluation.models import (
    BlindPrediction,
    BlindSchoolOutput,
    BlindTask,
    CapabilityPosterior,
    RevealedLabel,
    ScoreRecord,
)
from engine.evaluation.report import render_capability_report

MODULE = "tools.school_capability_baseline"
TASK_ID = "education.credentials"
SCHOOLS = ("ziping", "yang_qingjuan")


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", MODULE, *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _task(
    scoring_method: str = "binary_probability",
    *,
    task_id: str = TASK_ID,
    high_risk: bool = False,
) -> BlindTask:
    schemas = {
        "binary_probability": {"positive_label": "yes", "negative_label": "no"},
        "multiclass_probability": {"labels": ["academic", "vocational", "other"]},
        "ordinal": {"labels": ["1", "2", "3", "4", "5"]},
        "time_window": {"type": "year"},
        "portrait_agreement": {"type": "agreement"},
    }
    return BlindTask(
        task_id, "education", "binary_event", scoring_method,
        scoring_method != "portrait_agreement", high_risk, ["lifetime"], [],
        schemas[scoring_method], "test",
    )


def _prediction(label: str = "yes", probability: float = 0.8) -> BlindPrediction:
    return BlindPrediction("P-1", label, probability, {"start_year": 2020, "end_year": 2022}, ["F-1"], "falsifier")


def _output(
    school: str = "ziping",
    *,
    case_id: str = "C-1",
    task_id: str = TASK_ID,
    state: str = "claim",
    predictions: list[BlindPrediction] | None = None,
) -> BlindSchoolOutput:
    return BlindSchoolOutput(
        case_id, school, task_id, state, "rationale",
        ([_prediction()] if predictions is None else predictions) if state == "claim" else [],
    )


def _label(value: object = "yes", *, case_id: str = "C-1", task_id: str = TASK_ID) -> RevealedLabel:
    return RevealedLabel(case_id, task_id, value, "2026-01-01", "fixture", "A", True, "none")


def _score(case_id: str, probability_score: float, observed: bool) -> ScoreRecord:
    return ScoreRecord(
        case_id, "ziping", TASK_ID, "binary_event", "claim", False, True,
        "prototype-a", "lifetime", "complete", probability_score=probability_score,
        observed_positive=observed,
    )


def test_score_cli_requires_manifest_argument() -> None:
    result = _run("score", "--help")
    assert result.returncode == 0
    assert "--manifest" in result.stdout


def test_reveal_labels_v1_rejects_unknown_top_level_record_keys_non_list_and_duplicates(tmp_path: Path) -> None:
    run = freeze_outputs([_output()], "tasks-v1", "rules-v1")
    valid = {
        "case_id": "C-1", "task_id": TASK_ID, "label": "yes", "observed_at": "2026-01-01",
        "source": "fixture", "confidence_grade": "A", "quantifiable": True, "conflict_state": "none",
    }
    documents = [
        {"schema_version": "school-capability-labels/v1", "freeze_hash": run.freeze_hash, "labels": [], "extra": 1},
        {"schema_version": "school-capability-labels/v1", "freeze_hash": run.freeze_hash, "labels": {}},
        {"schema_version": "school-capability-labels/v1", "freeze_hash": run.freeze_hash, "labels": [{**valid, "extra": 1}]},
        {"schema_version": "school-capability-labels/v1", "freeze_hash": run.freeze_hash, "labels": [valid, valid]},
    ]
    for index, document in enumerate(documents):
        path = tmp_path / f"labels-{index}.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        with pytest.raises(ValueError):
            reveal_labels(run, path)


def test_experiment_requires_exactly_one_output_per_eligible_case_task_and_school() -> None:
    with pytest.raises(ValueError, match="exactly one output"):
        run_four_group_experiment(
            [_output("ziping")], [_label()], [_task()], SCHOOLS,
            eligible_case_tasks={("C-1", TASK_ID)}, baseline_prevalence={TASK_ID: 0.3},
        )


def test_experiment_supports_all_formal_scoring_methods() -> None:
    examples = {
        "binary_probability": ([_prediction("yes", 0.8)], "yes"),
        "multiclass_probability": ([
            _prediction("academic", 0.6), _prediction("vocational", 0.3), _prediction("other", 0.1),
        ], "academic"),
        "ordinal": ([_prediction("4", 0.8)], "4"),
        "time_window": ([_prediction("event", 0.8)], 2021),
        "portrait_agreement": ([_prediction("profile", 0.8)], 0.75),
    }
    for method, (predictions, observed) in examples.items():
        task_id = f"task.{method}"
        task = _task(method, task_id=task_id)
        outputs = [_output(school, task_id=task_id, predictions=predictions) for school in SCHOOLS]
        result = run_four_group_experiment(
            outputs, [_label(observed, task_id=task_id)], [task], SCHOOLS,
            eligible_case_tasks={("C-1", task_id)}, baseline_prevalence={task_id: 0.3},
        )
        assert result.rows
        assert any(row.score is not None for row in result.rows)


def test_experiment_uses_task_aware_proper_utility_and_doubles_high_risk_false_positive_cost() -> None:
    outputs = [_output(school, predictions=[_prediction("yes", 0.9)]) for school in SCHOOLS]
    normal = run_four_group_experiment(
        outputs, [_label("no")], [_task()], SCHOOLS,
        eligible_case_tasks={("C-1", TASK_ID)}, baseline_prevalence={TASK_ID: 0.3},
    )
    risky = run_four_group_experiment(
        outputs, [_label("no")], [_task(high_risk=True)], SCHOOLS,
        eligible_case_tasks={("C-1", TASK_ID)}, baseline_prevalence={TASK_ID: 0.3},
    )
    normal_utility = next(row.utility for row in normal.rows if row.group_id == "all_schools")
    risky_utility = next(row.utility for row in risky.rows if row.group_id == "all_schools")
    assert normal_utility == pytest.approx(1.0 - (0.9 ** 2))
    assert risky_utility == pytest.approx(1.0 - 2.0 * (0.9 ** 2))


def test_capability_coverage_uses_full_metadata_identity_and_beta_uses_discrete_hits() -> None:
    scores = [_score("C-1", 0.99, True), _score("C-2", 0.51, False)]
    identity = ("ziping", TASK_ID, "prototype-a", "binary_event", "lifetime", "complete")
    posterior = build_capability_posteriors(
        scores, "A", "now",
        claim_probabilities={("C-1", TASK_ID, "ziping"): 0.9, ("C-2", TASK_ID, "ziping"): 0.4},
        eligible_case_ids={identity: {"C-1", "C-2"}},
        score_weights={("C-1", TASK_ID, "ziping"): 0.5, ("C-2", TASK_ID, "ziping"): 1.0},
    )[0]
    assert posterior.accuracy_score == pytest.approx((0.5 * 0.99 + 1.0 * 0.51) / 1.5)
    assert posterior.posterior_mean == pytest.approx((1.0 + 1.5) / (2.0 + 1.5))


def test_report_never_emits_go_defaults_hold_and_deduplicates_posterior_rows() -> None:
    posterior = CapabilityPosterior(
        "ziping", TASK_ID, "prototype-a", "binary_event", "lifetime", "complete",
        1.0, 0.0, 0.9, None, 0.8, (0.6, 0.95), 20.0, "A", "now", 0.1,
    )
    text = render_capability_report({}, {}, [posterior])
    assert "GO（" not in text
    assert "READY_FOR_MANUAL_REVIEW" not in text
    assert "**HOLD**" in text
    assert text.count("ziping/education.credentials") == 1


def test_report_only_allows_ready_or_stop_with_complete_explicit_gate_evidence() -> None:
    ready = render_capability_report({}, {}, [], gate_evidence={
        "manifest_complete": True, "eligible_grid_complete": True,
        "provenance_complete": True, "quality_gate_passed": True,
        "stop_condition": False,
    })
    stopped = render_capability_report({}, {}, [], gate_evidence={
        "manifest_complete": True, "eligible_grid_complete": True,
        "provenance_complete": True, "quality_gate_passed": False,
        "stop_condition": True,
    })
    assert "**READY_FOR_MANUAL_REVIEW**" in ready
    assert "**STOP**" in stopped
    assert "GO" not in ready and "GO" not in stopped


def test_persisted_contracts_are_deeply_immutable() -> None:
    task = _task()
    output = _output()
    with pytest.raises((AttributeError, TypeError, FrozenInstanceError)):
        task.allowed_time_horizons.append("changed")
    with pytest.raises((AttributeError, TypeError, FrozenInstanceError)):
        task.label_schema["positive_label"] = "changed"
    with pytest.raises((AttributeError, TypeError, FrozenInstanceError)):
        output.predictions.append(_prediction("no", 0.2))
    with pytest.raises((AttributeError, TypeError, FrozenInstanceError)):
        output.predictions[0].time_window["start_year"] = 1999
