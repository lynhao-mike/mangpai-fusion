from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from engine.claims import validate_claim_evidence
from engine.claims.runner_registry import DEFAULT_RUNNER_REGISTRY
from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindTask
from engine.features import ChartFeatureVector, build_chart_feature_vector
from engine.v5.duan_runner import generate_claims as generate_duan_claims
from engine.v5.gao_runner import generate_claims as generate_gao_claims
from engine.v5.gao_timing import generate_timing_claims
from engine.v5.ren_runner import generate_claims as generate_ren_claims

TIMING_TASKS = (
    "career.change_window",
    "marriage.event_window",
    "health.event_window",
    "wealth.major_loss_window",
)
HIGH_RISK_TASKS = {"health.event_window", "wealth.major_loss_window"}


def _task(task_id: str) -> BlindTask:
    domains = {
        "career.change_window": "事业",
        "marriage.event_window": "婚姻",
        "health.event_window": "健康",
        "wealth.major_loss_window": "财富",
    }
    return BlindTask(
        task_id=task_id,
        domain=domains[task_id],
        claim_type="event_timing",
        scoring_method="time_window",
        quantifiable=True,
        high_risk=task_id in HIGH_RISK_TASKS,
        allowed_time_horizons=["annual"],
        required_input_fields=["four_pillars"],
        label_schema={"type": "object", "required": ["occurred", "year"]},
        evaluation_note="gao timing fixture",
    )


def _chart(*, liunian_steps: list[dict[str, object]] | None = None) -> ChartFactLedger:
    return ChartFactLedger(
        sex_marker="乾",
        four_pillars={"year": "癸未", "month": "甲寅", "day": "壬戌", "hour": "丙午"},
        dayun_steps=[{"ganzhi": "丙辰", "start_year": 2018, "end_year": 2027}],
        liunian_steps=(
            liunian_steps
            if liunian_steps is not None
            else [
                {"year": 2026, "ganzhi": "丙午", "dayun": "丙辰"},
                {"year": 2024, "ganzhi": "甲辰", "dayun": "丙辰"},
                {"year": 2025, "ganzhi": "乙巳", "dayun": "丙辰"},
            ]
        ),
    )


def _counts(chart: ChartFactLedger, **changes: int) -> dict[str, int]:
    counts = dict(build_chart_feature_vector(chart).ten_god_counts)
    counts.update(changes)
    return counts


def _features(chart: ChartFactLedger, task_id: str) -> ChartFeatureVector:
    base = build_chart_feature_vector(chart)
    if task_id == "career.change_window":
        return replace(
            base,
            ten_god_counts=_counts(chart, 正官=2, 七杀=1, 食神=2, 伤官=1),
            has_official=True,
            has_output=True,
            branch_conflict_intensity=0.6,
        )
    if task_id == "marriage.event_window":
        return replace(
            base,
            ten_god_counts=_counts(chart, 正官=2, 七杀=1, 正财=1, 偏财=0),
            has_official=True,
            has_wealth=True,
            chong_pairs=(("辰", "戌"),),
            xing_hai_pairs=(),
            branch_conflict_intensity=0.6,
        )
    if task_id == "health.event_window":
        return replace(base, supporting_count=1, draining_count=7, climate_extreme=True)
    return replace(
        base,
        ten_god_counts=_counts(chart, 正财=2, 偏财=1, 比肩=3, 劫财=1),
        has_wealth=True,
        supporting_count=1,
        draining_count=6,
        branch_conflict_intensity=0.6,
    )


@pytest.mark.parametrize("task_id", TIMING_TASKS)
def test_rooted_liunian_trigger_emits_one_deterministic_valid_claim(task_id: str) -> None:
    chart = _chart()
    features = _features(chart, task_id)
    task = _task(task_id)

    first = generate_timing_claims(chart, features, task)
    second = generate_timing_claims(chart, features, task)

    assert first == second
    assert len(first) == 1
    claim = first[0]
    assert claim.school_id == "gao"
    assert claim.task_id == task_id
    assert claim.claim_type == "timing_claim"
    assert claim.time_window is not None
    assert claim.time_window.start_year == claim.time_window.end_year
    assert claim.applicability_snapshot["rooted_liunian"] is True
    assert claim.applicability_snapshot["candidate_score"] > 0
    assert any(ref.startswith("liunian_steps.") for ref in claim.evidence[0].fact_refs)
    assert any(ref.startswith("four_pillars.") for ref in claim.evidence[0].fact_refs)
    validate_claim_evidence(claim, chart, features)


def test_unrelated_liunian_branch_abstains() -> None:
    chart = _chart(liunian_steps=[{"year": 2025, "ganzhi": "乙卯"}])
    task = _task("career.change_window")
    assert generate_timing_claims(chart, _features(chart, task.task_id), task) == []


def test_liunian_without_same_element_root_abstains() -> None:
    chart = replace(
        _chart(liunian_steps=[{"year": 2025, "ganzhi": "乙卯"}]),
        four_pillars={"year": "庚申", "month": "辛酉", "day": "壬子", "hour": "癸亥"},
    )
    task = _task("career.change_window")
    features = replace(
        _features(chart, task.task_id),
        has_official=True,
        has_output=True,
        branch_conflict_intensity=0.6,
    )
    assert generate_timing_claims(chart, features, task) == []


def test_empty_liunian_and_partial_evidence_abstain() -> None:
    chart = _chart(liunian_steps=[])
    task = _task("career.change_window")
    features = _features(chart, task.task_id)
    assert generate_timing_claims(chart, features, task) == []

    complete_chart = _chart()
    partial = replace(_features(complete_chart, task.task_id), evidence_completeness="partial")
    assert generate_timing_claims(complete_chart, partial, task) == []


@pytest.mark.parametrize("task_id", sorted(HIGH_RISK_TASKS))
def test_high_risk_windows_are_capped_and_use_conservative_language(task_id: str) -> None:
    chart = _chart()
    claim = generate_timing_claims(chart, _features(chart, task_id), _task(task_id))[0]
    assert claim.high_risk is True
    assert claim.confidence <= 0.55
    assert "需关注" in claim.statement or "风险窗口" in claim.statement
    assert not any(token in claim.statement for token in ("必发生", "必病", "大灾", "死亡", "破产"))


def test_module_imports_are_statically_independent() -> None:
    tree = ast.parse(Path("engine/v5/gao_timing.py").read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    forbidden = (
        "ren_runner",
        "duan_runner",
        "duan_timing",
        "feedback",
        "labels",
        "report_view",
    )
    assert not any(token in imported for imported in imports for token in forbidden)


@pytest.mark.parametrize("task_id", TIMING_TASKS)
def test_claim_id_is_independent_from_ren_and_duan(task_id: str) -> None:
    chart = _chart()
    task = _task(task_id)
    features = _features(chart, task_id)
    gao = generate_timing_claims(chart, features, task)[0]
    ren = generate_ren_claims(chart, features, task)[0]
    duan = generate_duan_claims(chart, features, task)[0]
    assert len({gao.claim_id, ren.claim_id, duan.claim_id}) == 3


def test_registry_adds_four_timing_tasks_and_preserves_existing_exact_entries() -> None:
    for task_id in TIMING_TASKS:
        assert DEFAULT_RUNNER_REGISTRY.resolve("gao", task_id) is generate_gao_claims
    assert DEFAULT_RUNNER_REGISTRY.resolve("gao", "wealth.debt") is generate_gao_claims
    assert DEFAULT_RUNNER_REGISTRY.resolve("gao", "health.system_risk") is generate_gao_claims
    assert DEFAULT_RUNNER_REGISTRY.resolve("gao", "structure.overview") is None
    assert DEFAULT_RUNNER_REGISTRY.resolve("gao", "career.role_change") is None
