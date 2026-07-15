from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from engine.claims import TaskUnsupported, TimeWindow, validate_claim_evidence
from engine.claims.orchestrator import generate_blind_outputs
from engine.claims.runner_registry import DEFAULT_RUNNER_REGISTRY
from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindTask
from engine.features import ChartFeatureVector, build_chart_feature_vector
from engine.v5.duan_runner import generate_claims as generate_duan_claims
from engine.v5.duan_timing import generate_timing_claims
from engine.v5.ren_runner import generate_claims as generate_ren_claims

TIMING_TASKS = (
    "career.change_window",
    "marriage.event_window",
    "health.event_window",
    "wealth.major_loss_window",
)
HIGH_RISK_TASKS = {"health.event_window", "wealth.major_loss_window"}
HIGH_RISK_CONFIDENCE_CAP = 0.55


def _task(task_id: str) -> BlindTask:
    domains = {
        "career.change_window": "事业",
        "marriage.event_window": "婚姻",
        "health.event_window": "健康",
        "wealth.major_loss_window": "财富",
    }
    return BlindTask(
        task_id=task_id,
        domain=domains.get(task_id, "总体"),
        claim_type="event_timing",
        scoring_method="time_window",
        quantifiable=True,
        high_risk=task_id in HIGH_RISK_TASKS,
        allowed_time_horizons=["annual"],
        required_input_fields=["four_pillars"],
        label_schema={"type": "object", "required": ["occurred", "year"]},
        evaluation_note="duan timing fixture",
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


def _features(chart: ChartFactLedger, task_id: str, *, anchored: bool = True) -> ChartFeatureVector:
    base = build_chart_feature_vector(chart)
    if not anchored:
        return replace(
            base,
            ten_god_counts=_counts(
                chart,
                正官=0,
                七杀=0,
                食神=0,
                伤官=0,
                正财=0,
                偏财=0,
                比肩=0,
                劫财=0,
            ),
            has_official=False,
            has_output=False,
            has_wealth=False,
            mixed_official_kill=False,
            supporting_count=4,
            draining_count=4,
            branch_conflict_intensity=0.0,
            chong_pairs=(),
            xing_hai_pairs=(),
            climate_extreme=False,
            element_concentration=0.3,
        )
    if task_id == "career.change_window":
        return replace(
            base,
            ten_god_counts=_counts(chart, 正官=2, 七杀=1, 食神=2, 伤官=1),
            has_official=True,
            has_output=True,
            mixed_official_kill=True,
            branch_conflict_intensity=0.6,
        )
    if task_id == "marriage.event_window":
        return replace(
            base,
            ten_god_counts=_counts(chart, 正官=2, 七杀=2),
            has_official=True,
            mixed_official_kill=True,
            chong_pairs=(("辰", "戌"),),
            xing_hai_pairs=(("寅", "巳"),),
            branch_conflict_intensity=0.7,
        )
    if task_id == "health.event_window":
        return replace(
            base,
            supporting_count=1,
            draining_count=7,
            climate_extreme=True,
            element_concentration=0.62,
            branch_conflict_intensity=0.6,
        )
    return replace(
        base,
        ten_god_counts=_counts(chart, 正财=2, 偏财=2, 比肩=3, 劫财=2),
        has_wealth=True,
        supporting_count=1,
        draining_count=7,
        branch_conflict_intensity=0.7,
    )


@pytest.mark.parametrize("task_id", TIMING_TASKS)
def test_each_timing_task_emits_exactly_one_valid_domain_anchored_claim(task_id: str) -> None:
    chart = _chart()
    features = _features(chart, task_id)

    claims = generate_timing_claims(chart, features, _task(task_id))

    assert claims == generate_timing_claims(chart, features, _task(task_id))
    assert len(claims) == 1
    claim = claims[0]
    assert claim.school_id == "duan"
    assert claim.task_id == task_id
    assert claim.claim_type == "timing_claim"
    assert claim.time_window is not None
    assert claim.time_window.label == "annual"
    assert claim.time_window.start_year == claim.time_window.end_year
    assert claim.time_window.start_year not in {1900, 2100}
    assert claim.evidence and claim.falsifier and claim.confidence_basis
    snapshot = claim.applicability_snapshot
    assert snapshot["trigger_year"] == claim.time_window.start_year
    assert snapshot["liunian_ganzhi"]
    assert snapshot["domain_anchor"]
    assert snapshot["relation_types"]
    assert snapshot["candidate_score"] > 0
    assert snapshot["evidence_completeness"] == features.evidence_completeness
    refs = claim.evidence[0].fact_refs
    assert any(ref.startswith("liunian_steps.") for ref in refs)
    assert any(ref.startswith("four_pillars.") for ref in refs)
    validate_claim_evidence(claim, chart, features)


def test_duan_and_ren_are_independent_timing_methods_on_the_same_chart() -> None:
    chart = _chart()
    task = _task("career.change_window")
    features = _features(chart, task.task_id)

    duan = generate_timing_claims(chart, features, task)[0]
    ren = generate_ren_claims(chart, features, task)[0]

    assert duan.school_id != ren.school_id
    assert duan.claim_id != ren.claim_id
    assert duan.evidence[0].rule_id != ren.evidence[0].rule_id
    assert duan.confidence_basis != ren.confidence_basis
    assert dict(duan.applicability_snapshot) != dict(ren.applicability_snapshot)
    assert "领域锚点" in duan.confidence_basis


def test_module_is_statically_isolated_from_ren_feedback_and_reports() -> None:
    tree = ast.parse(Path("engine/v5/duan_timing.py").read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    forbidden = ("ren_runner", "feedback", "render_report", "report_view", "reports")
    assert not any(token in imported for imported in imports for token in forbidden)


def test_window_year_comes_from_valid_liunian_input_not_fixed_text() -> None:
    first_chart = _chart(liunian_steps=[{"year": 2024, "ganzhi": "甲辰", "dayun": "丙辰"}])
    second_chart = _chart(liunian_steps=[{"year": 2036, "ganzhi": "丙辰", "dayun": "丙辰"}])
    task = _task("marriage.event_window")

    first = generate_timing_claims(first_chart, _features(first_chart, task.task_id), task)[0]
    second = generate_timing_claims(second_chart, _features(second_chart, task.task_id), task)[0]

    assert first.time_window == TimeWindow(2024, 2024, "annual")
    assert second.time_window == TimeWindow(2036, 2036, "annual")
    assert "2024" in first.statement and "2036" in second.statement


@pytest.mark.parametrize(
    "steps",
    [
        [],
        [{"ganzhi": "甲辰"}],
        [{"year": "2024", "ganzhi": "甲辰"}],
        [{"year": True, "ganzhi": "甲辰"}],
        [{"year": 2024, "ganzhi": "甲X"}],
        [{"year": 2024, "ganzhi": "辰"}],
    ],
)
def test_missing_or_invalid_liunian_facts_abstain(steps: list[dict[str, object]]) -> None:
    chart = _chart(liunian_steps=steps)
    task = _task("career.change_window")
    assert generate_timing_claims(chart, _features(chart, task.task_id), task) == []


@pytest.mark.parametrize("task_id", TIMING_TASKS)
def test_relation_without_corresponding_domain_anchor_abstains(task_id: str) -> None:
    chart = _chart()
    assert generate_timing_claims(chart, _features(chart, task_id, anchored=False), _task(task_id)) == []


@pytest.mark.parametrize(
    ("task_id", "quiet_ganzhi"),
    [
        ("career.change_window", "乙卯"),
        ("marriage.event_window", "甲子"),
        ("health.event_window", "甲子"),
        ("wealth.major_loss_window", "甲辰"),
    ],
)
def test_domain_anchor_without_key_palace_or_dayun_trigger_abstains(task_id: str, quiet_ganzhi: str) -> None:
    chart = replace(_chart(liunian_steps=[{"year": 2025, "ganzhi": quiet_ganzhi}]), dayun_steps=[])
    assert generate_timing_claims(chart, _features(chart, task_id), _task(task_id)) == []


def test_multiple_candidates_use_score_year_and_input_index_stable_order() -> None:
    chart = _chart(
        liunian_steps=[
            {"year": 2030, "ganzhi": "庚辰", "dayun": "丙辰"},
            {"year": 2024, "ganzhi": "甲辰", "dayun": "丙辰"},
            {"year": 2024, "ganzhi": "丙辰", "dayun": "丙辰"},
        ]
    )
    task = _task("marriage.event_window")
    features = _features(chart, task.task_id)

    first = generate_timing_claims(chart, features, task)
    second = generate_timing_claims(chart, features, task)

    assert first == second
    assert len(first) == 1
    assert first[0].time_window == TimeWindow(2024, 2024, "annual")
    assert "liunian_steps.1" in first[0].evidence[0].fact_refs


def test_dayun_relation_is_backed_by_resolvable_dayun_reference() -> None:
    chart = replace(
        _chart(liunian_steps=[{"year": 2025, "ganzhi": "乙巳", "dayun": "戊申"}]),
        dayun_steps=[{"ganzhi": "戊申", "start_year": 2018, "end_year": 2027}],
    )
    task = _task("career.change_window")
    features = _features(chart, task.task_id)

    claim = generate_timing_claims(chart, features, task)[0]

    assert "dayun_steps.0" in claim.evidence[0].fact_refs
    assert "four_pillars.month" in claim.evidence[0].fact_refs
    validate_claim_evidence(claim, chart, features)


@pytest.mark.parametrize("task_id", sorted(HIGH_RISK_TASKS))
def test_high_risk_windows_inherit_flag_and_use_conservative_language(task_id: str) -> None:
    chart = _chart()
    claim = generate_timing_claims(chart, _features(chart, task_id), _task(task_id))[0]

    assert claim.high_risk is True
    assert claim.confidence <= HIGH_RISK_CONFIDENCE_CAP
    assert "风险窗口" in claim.statement or "需关注" in claim.statement
    assert "窗口内没有可核验" in claim.falsifier
    forbidden = ("必发生", "必病", "大灾", "死亡", "破产", "癌", "心脏病")
    assert not any(token in claim.statement for token in forbidden)


def test_marriage_window_preserves_event_category_uncertainty() -> None:
    chart = _chart()
    claim = generate_timing_claims(chart, _features(chart, "marriage.event_window"), _task("marriage.event_window"))[0]
    assert all(token in claim.statement for token in ("结婚", "分合", "关系重组"))
    assert "离婚年" not in claim.statement


def test_duan_unified_entry_delegates_timing_and_preserves_event_handler() -> None:
    chart = _chart()
    timing_task = _task("career.change_window")
    timing_features = _features(chart, timing_task.task_id)
    assert generate_duan_claims(chart, timing_features, timing_task) == generate_timing_claims(
        chart, timing_features, timing_task
    )

    event_task = BlindTask(
        task_id="career.role_change",
        domain="事业",
        claim_type="event",
        scoring_method="binary_event",
        quantifiable=True,
        high_risk=False,
        allowed_time_horizons=["lifetime"],
        required_input_fields=["four_pillars"],
        label_schema={"type": "boolean"},
        evaluation_note="event regression",
    )
    event_features = replace(
        build_chart_feature_vector(chart),
        ten_god_counts=_counts(chart, 食神=2, 伤官=1, 正官=1, 七杀=1),
        has_official=True,
        has_output=True,
        mixed_official_kill=True,
        branch_conflict_intensity=0.5,
    )
    event_claims = generate_duan_claims(chart, event_features, event_task)
    assert len(event_claims) == 1 and event_claims[0].claim_type == "event_claim"

    with pytest.raises(TaskUnsupported):
        generate_duan_claims(chart, timing_features, replace(timing_task, task_id="structure.overview"))


def test_registry_exactly_registers_four_duan_timing_tasks_to_unified_entry() -> None:
    for task_id in TIMING_TASKS:
        assert DEFAULT_RUNNER_REGISTRY.resolve("duan", task_id) is generate_duan_claims
    assert DEFAULT_RUNNER_REGISTRY.resolve("duan", "career.any_window") is None


def test_orchestrator_reports_claim_abstain_and_unsupported_for_duan_timing() -> None:
    triggered = _chart(liunian_steps=[{"year": 2025, "ganzhi": "乙巳", "dayun": "丙辰"}])
    task = _task("career.change_window")
    # 编排器构建真实 CFV；该原局官杀、食伤与混杂信号形成事业锚点，巳刑月支寅。
    claim_rows = generate_blind_outputs(triggered, [task], case_id="C-DUAN-TIMING-CLAIM", schools=["duan"])
    assert claim_rows[0].state == "claim"
    assert claim_rows[0].predictions[0].time_window["start_year"] == 2025

    quiet = replace(triggered, liunian_steps=[])
    abstain_rows = generate_blind_outputs(quiet, [task], case_id="C-DUAN-TIMING-ABSTAIN", schools=["duan"])
    assert abstain_rows[0].state == "abstain"

    unsupported_task = replace(task, task_id="marriage.unknown_window")
    unsupported_rows = generate_blind_outputs(
        triggered, [unsupported_task], case_id="C-DUAN-TIMING-UNSUPPORTED", schools=["duan"]
    )
    assert unsupported_rows[0].state == "unsupported"
