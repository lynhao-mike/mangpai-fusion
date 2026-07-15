from __future__ import annotations

from dataclasses import replace

import pytest

from engine.claims import TaskUnsupported, validate_claim_evidence
from engine.claims.orchestrator import generate_blind_outputs
from engine.claims.runner_registry import DEFAULT_RUNNER_REGISTRY
from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindTask
from engine.features import ChartFeatureVector, build_chart_feature_vector
from engine.v5.duan_runner import generate_claims as generate_duan_claims

EVENT_TASKS = (
    "career.role_change",
    "career.path_type",
    "wealth.debt",
    "marriage.divorce_or_remarriage",
)
TIMING_TASKS = (
    "career.change_window",
    "marriage.event_window",
    "health.event_window",
    "wealth.major_loss_window",
)
HIGH_RISK_CONFIDENCE_CAP = 0.62


def _task(task_id: str) -> BlindTask:
    domains = {
        "career.role_change": "事业",
        "career.path_type": "事业",
        "wealth.debt": "财富",
        "marriage.divorce_or_remarriage": "婚姻",
        "career.change_window": "事业",
        "marriage.event_window": "婚姻",
        "health.event_window": "健康",
        "wealth.major_loss_window": "财富",
    }
    categorical = task_id == "career.path_type"
    timing = task_id in TIMING_TASKS
    return BlindTask(
        task_id=task_id,
        domain=domains.get(task_id, "总体"),
        claim_type="event_timing" if timing else "event",
        scoring_method="time_window" if timing else ("categorical" if categorical else "binary_event"),
        quantifiable=True,
        high_risk=task_id in {"wealth.debt", "marriage.divorce_or_remarriage", "health.event_window", "wealth.major_loss_window"},
        allowed_time_horizons=["ten_year", "annual"] if timing else ["lifetime", "ten_year"],
        required_input_fields=["four_pillars", "sex_marker"] if task_id == "marriage.divorce_or_remarriage" else ["four_pillars"],
        label_schema=(
            {"type": "categorical", "labels": ["employment", "entrepreneurship", "mixed"]}
            if categorical
            else {"type": "boolean", "positive_label": "occurred", "negative_label": "not_observed"}
        ),
        evaluation_note="duan runner fixture",
    )


def _chart() -> ChartFactLedger:
    return ChartFactLedger(
        sex_marker="乾",
        four_pillars={"year": "庚申", "month": "戊寅", "day": "壬子", "hour": "辛丑"},
    )


def _features(**changes: object) -> ChartFeatureVector:
    """从真实 CFV 起步；仅为精确判别边界替换相互一致的聚合代理。"""
    base = build_chart_feature_vector(_chart())
    return replace(base, **changes)


def _ten_gods(**changes: int) -> dict[str, int]:
    counts = dict(build_chart_feature_vector(_chart()).ten_god_counts)
    counts.update(changes)
    return counts


def _assert_single_valid_claim(task_id: str, features: ChartFeatureVector):
    task = _task(task_id)
    first = generate_duan_claims(_chart(), features, task)
    second = generate_duan_claims(_chart(), features, task)
    assert first == second
    assert len(first) == 1
    claim = first[0]
    assert claim.school_id == "duan"
    assert claim.task_id == task_id
    assert claim.claim_type == "event_claim"
    assert claim.time_window is not None and claim.time_window.label == "lifetime"
    assert claim.evidence and claim.falsifier and claim.confidence_basis
    assert claim.applicability_snapshot
    validate_claim_evidence(claim, _chart(), features)
    return claim


def test_role_change_requires_career_structure_plus_computable_action_signal() -> None:
    counts = _ten_gods(食神=2, 伤官=1, 正官=1, 七杀=1)
    positive = _features(
        ten_god_counts=counts,
        has_official=True,
        has_output=True,
        mixed_official_kill=True,
        branch_conflict_intensity=0.5,
        chong_pairs=(("寅", "申"),),
    )
    claim = _assert_single_valid_claim("career.role_change", positive)
    assert "无显著岗位、职责或职业角色变化" in claim.falsifier

    conflict_only = _features(
        ten_god_counts=_ten_gods(食神=0, 伤官=0, 正官=0, 七杀=0),
        has_official=False,
        has_output=False,
        mixed_official_kill=False,
        branch_conflict_intensity=0.8,
        chong_pairs=(("寅", "申"),),
    )
    assert generate_duan_claims(_chart(), conflict_only, _task("career.role_change")) == []

    weak_action = replace(positive, branch_conflict_intensity=0.0, chong_pairs=(), mixed_official_kill=False)
    assert generate_duan_claims(_chart(), weak_action, _task("career.role_change")) == []


@pytest.mark.parametrize(
    ("features", "expected_label"),
    [
        (
            _features(
                ten_god_counts=_ten_gods(正官=3, 七杀=0, 正印=2, 偏印=1, 食神=0, 伤官=0, 正财=0, 偏财=0),
                has_official=True, has_resource=True, has_output=False, has_wealth=False,
                mixed_official_kill=False, branch_conflict_intensity=0.0,
            ),
            "employment",
        ),
        (
            _features(
                ten_god_counts=_ten_gods(正官=0, 七杀=0, 正印=0, 偏印=0, 食神=3, 伤官=2, 正财=2, 偏财=2),
                has_official=False, has_resource=False, has_output=True, has_wealth=True,
                mixed_official_kill=False, branch_conflict_intensity=0.0,
            ),
            "entrepreneurship",
        ),
        (
            _features(
                ten_god_counts=_ten_gods(正官=2, 七杀=0, 正印=2, 偏印=0, 食神=2, 伤官=1, 正财=2, 偏财=1),
                has_official=True, has_resource=True, has_output=True, has_wealth=True,
                mixed_official_kill=False, branch_conflict_intensity=0.5,
            ),
            "mixed",
        ),
    ],
)
def test_path_type_emits_only_catalog_labels(features: ChartFeatureVector, expected_label: str) -> None:
    claim = _assert_single_valid_claim("career.path_type", features)
    assert claim.applicability_snapshot["predicted_label"] == expected_label
    assert expected_label in {"employment", "entrepreneurship", "mixed"}


def test_path_type_abstains_when_signals_are_close_or_insufficient() -> None:
    ambiguous = _features(
        ten_god_counts=_ten_gods(正官=1, 七杀=0, 正印=1, 偏印=0, 食神=1, 伤官=0, 正财=1, 偏财=0),
        has_official=True, has_resource=True, has_output=True, has_wealth=True,
        mixed_official_kill=False, branch_conflict_intensity=0.0,
    )
    assert generate_duan_claims(_chart(), ambiguous, _task("career.path_type")) == []

    insufficient = _features(
        ten_god_counts=_ten_gods(正官=0, 七杀=0, 正印=0, 偏印=0, 食神=0, 伤官=0, 正财=0, 偏财=0),
        has_official=False, has_resource=False, has_output=False, has_wealth=False,
    )
    assert generate_duan_claims(_chart(), insufficient, _task("career.path_type")) == []


def test_debt_requires_wealth_pressure_and_action_imbalance_and_is_conservative() -> None:
    positive = _features(
        ten_god_counts=_ten_gods(正财=1, 偏财=2, 比肩=3, 劫财=2),
        has_wealth=True,
        supporting_count=1,
        draining_count=7,
        rooted_count=0,
        branch_conflict_intensity=0.7,
        chong_pairs=(("寅", "申"),),
        element_concentration=0.5,
    )
    claim = _assert_single_valid_claim("wealth.debt", positive)
    assert claim.high_risk is True
    assert claim.confidence <= HIGH_RISK_CONFIDENCE_CAP
    assert "没有可核验的显著债务、长期负债或债务危机记录" in claim.falsifier
    assert "必负债" not in claim.statement and "必破产" not in claim.statement

    wealth_weak_only = replace(positive, branch_conflict_intensity=0.0, chong_pairs=(), draining_count=3, supporting_count=3)
    assert generate_duan_claims(_chart(), wealth_weak_only, _task("wealth.debt")) == []

    pressure_without_wealth = replace(positive, has_wealth=False, ten_god_counts=_ten_gods(正财=0, 偏财=0, 比肩=3, 劫财=2))
    assert generate_duan_claims(_chart(), pressure_without_wealth, _task("wealth.debt")) == []


def test_divorce_requires_two_independent_signals_not_relationship_pressure_alone() -> None:
    positive = _features(
        ten_god_counts=_ten_gods(正官=2, 七杀=2),
        has_official=True,
        mixed_official_kill=True,
        branch_conflict_intensity=0.7,
        chong_pairs=(("子", "午"),),
        xing_hai_pairs=(("寅", "巳"),),
    )
    claim = _assert_single_valid_claim("marriage.divorce_or_remarriage", positive)
    assert claim.high_risk is True
    assert claim.confidence <= HIGH_RISK_CONFIDENCE_CAP
    assert "没有离婚或再婚记录" in claim.falsifier
    assert "必离" not in claim.statement

    # 日支冲/关系压力仅一个信号，必须 abstain。
    relationship_pressure_only = _features(
        ten_god_counts=_ten_gods(正官=0, 七杀=0),
        has_official=False,
        mixed_official_kill=False,
        branch_conflict_intensity=0.5,
        chong_pairs=(("子", "午"),),
        xing_hai_pairs=(),
    )
    assert generate_duan_claims(_chart(), relationship_pressure_only, _task("marriage.divorce_or_remarriage")) == []

    mixed_only = replace(relationship_pressure_only, chong_pairs=(), branch_conflict_intensity=0.0, mixed_official_kill=True)
    assert generate_duan_claims(_chart(), mixed_only, _task("marriage.divorce_or_remarriage")) == []


def test_all_event_tasks_abstain_on_partial_evidence() -> None:
    base = _features(evidence_completeness="partial")
    for task_id in EVENT_TASKS:
        assert generate_duan_claims(_chart(), base, _task(task_id)) == []


def test_non_event_tasks_raise_unsupported_and_timing_remains_unregistered() -> None:
    features = build_chart_feature_vector(_chart())
    for task_id in (*TIMING_TASKS, "structure.overview"):
        with pytest.raises(TaskUnsupported, match="duan does not support task"):
            generate_duan_claims(_chart(), features, _task(task_id))
    for task_id in TIMING_TASKS:
        assert DEFAULT_RUNNER_REGISTRY.resolve("duan", task_id) is None


def test_default_registry_registers_exactly_the_four_duan_event_tasks() -> None:
    for task_id in EVENT_TASKS:
        assert DEFAULT_RUNNER_REGISTRY.resolve("duan", task_id) is generate_duan_claims
    assert DEFAULT_RUNNER_REGISTRY.resolve("duan", "marriage.relationship_pressure") is None


def test_orchestrator_preserves_claim_abstain_and_unsupported_for_duan() -> None:
    chart = _chart()
    rows = generate_blind_outputs(
        chart,
        [_task("career.role_change"), _task("career.change_window")],
        case_id="C-DUAN-ORCHESTRATOR",
        schools=["duan"],
    )
    indexed = {row.task_id: row.state for row in rows}
    assert indexed["career.role_change"] in {"claim", "abstain"}
    assert indexed["career.change_window"] == "unsupported"
