from __future__ import annotations

import importlib

import pytest


def _module():
    try:
        return importlib.import_module("engine.decision.routing_holdout")
    except ModuleNotFoundError as exc:
        pytest.fail(f"routing holdout evaluator is missing: {exc}")


def _record(case_id: str, static_utility: float, learned_utility: float, *, high_risk: bool = False, static_fp: bool = False, learned_fp: bool = False):
    module = _module()
    return module.HoldoutRoutingRecord(
        case_id=case_id,
        task_id="career.role_change",
        static_utility=static_utility,
        learned_utility=learned_utility,
        static_calibration_error=0.12,
        learned_calibration_error=0.1,
        high_risk=high_risk,
        static_false_positive=static_fp,
        learned_false_positive=learned_fp,
        prototype_id="prototype-balanced",
    )


def test_training_and_holdout_case_ids_must_be_disjoint() -> None:
    module = _module()

    with pytest.raises(ValueError, match="leakage"):
        module.evaluate_holdout(
            records=[_record("C-1", 0.5, 0.7)],
            training_case_ids={"C-1"},
            minimum_holdout_cases=1,
        )


def test_insufficient_holdout_is_hold_not_go() -> None:
    module = _module()

    result = module.evaluate_holdout(
        records=[_record("C-1", 0.5, 0.7)],
        training_case_ids=set(),
        minimum_holdout_cases=2,
    )

    assert result.status == "HOLD"
    assert any("样本不足" in reason for reason in result.reasons)


def test_go_requires_non_worse_utility_calibration_and_high_risk_false_positives() -> None:
    module = _module()
    records = [
        _record("C-1", 0.5, 0.7),
        _record("C-2", 0.6, 0.75, high_risk=True, static_fp=False, learned_fp=False),
    ]

    result = module.evaluate_holdout(records=records, training_case_ids={"TRAIN-1"}, minimum_holdout_cases=2)

    assert result.status == "GO"
    assert result.learned_mean_utility > result.static_mean_utility
    assert result.learned_calibration_error <= result.static_calibration_error
    assert result.learned_high_risk_false_positives <= result.static_high_risk_false_positives


def test_training_only_gain_or_high_risk_regression_stops() -> None:
    module = _module()
    worse = [
        _record("C-1", 0.7, 0.6),
        _record("C-2", 0.7, 0.8, high_risk=True, static_fp=False, learned_fp=True),
    ]

    result = module.evaluate_holdout(records=worse, training_case_ids=set(), minimum_holdout_cases=2)

    assert result.status == "STOP"
    assert any("假阳性" in reason or "效用" in reason for reason in result.reasons)


def test_markdown_report_contains_gate_evidence_without_internal_route_ids() -> None:
    module = _module()
    result = module.evaluate_holdout(
        records=[_record("C-1", 0.5, 0.7), _record("C-2", 0.6, 0.75)],
        training_case_ids=set(),
        minimum_holdout_cases=2,
    )

    report = module.render_holdout_comparison(result)

    assert "# L1 可学习路由留出集对照" in report
    assert "GO" in report
    assert "静态基线" in report
    assert "learned" in report
    assert "capability_snapshot_id" not in report
