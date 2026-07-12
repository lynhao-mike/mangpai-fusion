from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from engine.evaluation.capability import build_capability_posteriors

import pytest

from engine.evaluation.experiments import run_four_group_experiment
from engine.evaluation.models import BlindPrediction, BlindSchoolOutput, BlindTask, RevealedLabel, ScoreRecord
from engine.evaluation.scoring import score_output
from engine.evaluation.task_catalog import load_task_catalog


def task(method: str, *, high_risk: bool = False, schema: dict | None = None) -> BlindTask:
    defaults = {
        "ordinal": {"type": "ordinal", "labels": ["low", "medium", "high"]},
        "time_window": {"type": "time_window", "event": "event"},
        "portrait_agreement": {},
        "multiclass_probability": {"type": "categorical", "labels": ["low", "moderate", "high"], "high_risk_labels": ["high"]},
    }
    return BlindTask("task", "domain", "portrait" if method == "portrait_agreement" else "claim", method, method != "portrait_agreement", high_risk, ["annual"], [], defaults[method] if schema is None else schema, "test")


def prediction(label: str, probability: float = 1.0, window: dict | None = None, suffix: str = "") -> BlindPrediction:
    return BlindPrediction("p" + suffix, label, probability, window or {}, [], "falsifier")


def output(school: str, predictions: list[BlindPrediction], *, state: str = "claim") -> BlindSchoolOutput:
    return BlindSchoolOutput("C", school, "task", state, "rationale", predictions if state == "claim" else [])


def label(value: object, *, quantifiable: bool = True) -> RevealedLabel:
    return RevealedLabel("C", "task", value, "2026-01-01", "feedback", "A", quantifiable, "none", "reviewer-1")


def rows(method: str, outputs: list[BlindSchoolOutput], observed: object, *, high_risk: bool = False):
    result = run_four_group_experiment(outputs, [label(observed, quantifiable=method != "portrait_agreement")], [task(method, high_risk=high_risk)], ["a", "b"], eligible_case_tasks=[("C", "task")], baseline_prevalence={"task": 0.5})
    return {row.group_id: row for row in result.rows}, result


def test_revealed_label_requires_non_empty_reviewer() -> None:
    with pytest.raises((TypeError, ValueError), match="reviewer"):
        RevealedLabel("C", "task", "x", "2026", "source", "A", True, "none")
    with pytest.raises(ValueError, match="reviewer"):
        label("x").__class__("C", "task", "x", "2026", "source", "A", True, "none", " ")


def test_ordinal_fusion_averages_rank_round_half_up_and_membership_changes() -> None:
    grouped, _ = rows("ordinal", [output("a", [prediction("low")]), output("b", [prediction("medium")])], "medium")
    assert grouped["all_schools"].score == 1.0  # mean rank 1.5 -> 2
    assert grouped["leave_one_school_out:b"].score == 0.5


def test_time_window_fusion_averages_each_boundary_and_scores_fused_window() -> None:
    grouped, _ = rows("time_window", [output("a", [prediction("event", window={"start_year": 2019, "end_year": 2021})]), output("b", [prediction("event", window={"start_year": 2020, "end_year": 2024})])], {"occurred": True, "year": 2023})
    assert grouped["all_schools"].score == 1.0  # [2020, 2023]
    assert grouped["leave_one_school_out:b"].score == pytest.approx(1 / 3)


def test_time_window_non_occurrence_is_high_risk_false_positive_and_abstain_is_safe() -> None:
    claim = score_output(output("a", [prediction("event", window={"start_year": 2020, "end_year": 2021})]), task("time_window", high_risk=True), label({"occurred": False, "year": None}))
    abstain = score_output(output("a", [], state="abstain"), task("time_window", high_risk=True), label({"occurred": False, "year": None}))
    assert claim.timing_score == 0.0 and claim.utility == -2.0
    assert abstain.utility == 0.0


def test_portrait_fusion_majority_tie_lexical_and_never_enters_utility() -> None:
    grouped, result = rows("portrait_agreement", [output("a", [prediction("z")]), output("b", [prediction("a")])], "a")
    assert grouped["all_schools"].score == 1.0
    assert grouped["all_schools"].utility is None
    assert result.mean_utility_by_group == {}


def test_multiclass_high_risk_argmax_false_positive_has_double_negative_cost() -> None:
    predictions = [prediction("low", 0.1, suffix="1"), prediction("moderate", 0.2, suffix="2"), prediction("high", 0.7, suffix="3")]
    score = score_output(output("a", predictions), task("multiclass_probability", high_risk=True), label("low"))
    assert score.utility == pytest.approx(-1.4)


def test_catalog_declares_health_high_risk_labels_and_time_window_label_shape() -> None:
    catalog = {item.task_id: item for item in load_task_catalog(Path("mapping/school-capability-task-catalog-v1.yaml"))}
    assert catalog["health.system_risk"].label_schema["high_risk_labels"] == ("high",)
    for item in catalog.values():
        if item.scoring_method == "time_window":
            assert item.label_schema["required"] == ("occurred", "year")


def test_experiment_rows_audit_requested_contributing_and_excluded_members() -> None:
    grouped, _ = rows(
        "ordinal",
        [output("a", [prediction("low")]), output("b", [], state="unsupported")],
        "low",
    )
    all_row = grouped["all_schools"]
    assert all_row.requested_members == ("a", "b")
    assert all_row.contributing_members == ("a",)
    assert all_row.excluded_members == ("b",)
    leave_a = grouped["leave_one_school_out:a"]
    assert leave_a.requested_members == ("b",)
    assert leave_a.contributing_members == ()
    assert leave_a.excluded_members == ("b",)


def test_calibration_requires_five_actual_binary_claims_per_six_dimensional_identity() -> None:
    def record(case: str, prototype: str, state: str = "claim") -> ScoreRecord:
        return ScoreRecord(case, "a", "task", "claim", state, state == "abstain", state != "unsupported", prototype, "annual", "complete", probability_score=1.0 if state == "claim" else None, observed_positive=True if state == "claim" else None)

    scores = [record(f"A-{i}", "A") for i in range(5)] + [record(f"B-{i}", "B") for i in range(4)] + [record("B-X", "B", "abstain")]
    probabilities = {(item.case_id, item.task_id, item.school_id): 1.0 for item in scores if item.state == "claim"}
    identities = {
        ("a", "task", prototype, "claim", "annual", "complete"): {item.case_id for item in scores if item.chart_prototype_id == prototype}
        for prototype in ("A", "B")
    }
    posteriors = {item.chart_prototype_id: item for item in build_capability_posteriors(scores, "A", "now", claim_probabilities=probabilities, eligible_case_ids=identities)}
    assert posteriors["A"].calibration_error == 0.0
    assert posteriors["B"].calibration_error is None
