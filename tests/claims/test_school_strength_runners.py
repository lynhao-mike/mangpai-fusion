from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from engine.claims import TaskUnsupported, validate_claim_evidence
from engine.claims.orchestrator import generate_blind_outputs
from engine.claims.runner_registry import DEFAULT_RUNNER_REGISTRY
from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindTask
from engine.features import ChartFeatureVector, build_chart_feature_vector
from engine.v5.ditiansui_runner import (
    generate_claims as generate_ditiansui_claims,
    run_ditiansui_independent,
)
from engine.v5.gao_runner import generate_claims as generate_gao_claims
from engine.v5.yang_runner import generate_claims as generate_yang_claims


HIGH_RISK_CONFIDENCE_CAP = 0.62
LIFETIME = (1900, 2100, "lifetime")


def _task(task_id: str) -> BlindTask:
    definitions = {
        "structure.overview": ("总体", False, "structure_claim", "portrait_agreement", {}, ["four_pillars"]),
        "wealth.debt": (
            "财富", True, "binary_event", "binary_probability",
            {"type": "boolean", "positive_label": "occurred", "negative_label": "not_observed"},
            ["four_pillars"],
        ),
        "health.system_risk": (
            "健康", True, "categorical_state", "multiclass_probability",
            {"type": "categorical", "labels": ["low", "moderate", "high"]},
            ["four_pillars", "sex_marker"],
        ),
        "marriage.divorce_or_remarriage": (
            "婚姻", True, "binary_event", "binary_probability",
            {"type": "boolean", "positive_label": "occurred", "negative_label": "not_observed"},
            ["four_pillars", "sex_marker"],
        ),
    }
    domain, high_risk, claim_type, scoring, label_schema, required = definitions.get(
        task_id, ("总体", False, "event", "binary_probability", {"type": "boolean"}, ["four_pillars"])
    )
    return BlindTask(
        task_id=task_id,
        domain=domain,
        claim_type=claim_type,
        scoring_method=scoring,
        quantifiable=bool(label_schema),
        high_risk=high_risk,
        allowed_time_horizons=["lifetime"],
        required_input_fields=required,
        label_schema=label_schema,
        evaluation_note="school strength runner fixture",
    )


def _chart(*, sex_marker: str = "乾") -> ChartFactLedger:
    return ChartFactLedger(
        sex_marker=sex_marker,
        four_pillars={"year": "庚申", "month": "戊寅", "day": "壬子", "hour": "辛丑"},
    )


def _features(chart: ChartFactLedger | None = None, **changes: object) -> ChartFeatureVector:
    return replace(build_chart_feature_vector(chart or _chart()), **changes)


def _ten_gods(chart: ChartFactLedger | None = None, **changes: int) -> dict[str, int]:
    counts = dict(build_chart_feature_vector(chart or _chart()).ten_god_counts)
    counts.update(changes)
    return counts


def _assert_single_valid(generator, chart: ChartFactLedger, features: ChartFeatureVector, task: BlindTask):
    first = generator(chart, features, task)
    second = generator(chart, features, task)
    assert first == second
    assert len(first) == 1
    claim = first[0]
    assert claim.evidence and claim.statement and claim.falsifier and claim.confidence_basis
    assert claim.applicability_snapshot
    validate_claim_evidence(claim, chart, features)
    return claim


def test_ditiansui_emits_only_discriminative_structure_claims() -> None:
    chart = _chart()
    climate = _features(
        chart,
        cold_warm_axis=-0.82,
        dry_wet_axis=-0.72,
        climate_extreme=True,
        evidence_completeness="full",
    )
    claim = _assert_single_valid(generate_ditiansui_claims, chart, climate, _task("structure.overview"))
    assert claim.school_id == "ditiansui"
    assert claim.claim_type == "structure_claim"
    assert claim.time_window is None
    assert "寒" in claim.statement or "湿" in claim.statement
    assert "同一特征版本独立复核" in claim.falsifier

    concentrated = _features(
        chart,
        cold_warm_axis=0.0,
        dry_wet_axis=0.0,
        climate_extreme=False,
        element_concentration=0.625,
        dominant_element="金",
        missing_elements=("火", "木"),
        element_energy={"木": 0.05, "火": 0.0, "土": 0.15, "金": 0.65, "水": 0.15},
    )
    qi_claim = _assert_single_valid(generate_ditiansui_claims, chart, concentrated, _task("structure.overview"))
    assert "金" in qi_claim.statement
    assert "偏枯" in qi_claim.statement or "集中" in qi_claim.statement

    neutral = _features(
        chart,
        cold_warm_axis=0.05,
        dry_wet_axis=-0.05,
        climate_extreme=False,
        element_concentration=0.30,
        missing_elements=(),
        element_energy={"木": 0.2, "火": 0.2, "土": 0.2, "金": 0.2, "水": 0.2},
    )
    assert generate_ditiansui_claims(chart, neutral, _task("structure.overview")) == []
    assert generate_ditiansui_claims(chart, replace(climate, evidence_completeness="partial"), _task("structure.overview")) == []


def test_ditiansui_rejects_other_tasks_and_preserves_legacy_v5_entry() -> None:
    chart = _chart()
    with pytest.raises(TaskUnsupported, match="ditiansui does not support task"):
        generate_ditiansui_claims(chart, build_chart_feature_vector(chart), _task("wealth.debt"))

    legacy = run_ditiansui_independent(
        {"pillars": {"year": "庚申", "month": "戊寅", "day": "壬子", "hour": "辛丑"}},
        "C-DTS-LEGACY",
    )
    assert len(legacy) == 2
    assert all(item.school == "ditiansui" for item in legacy)


def test_gao_debt_requires_multiple_independent_pressure_signals() -> None:
    chart = _chart()
    positive = _features(
        chart,
        ten_god_counts=_ten_gods(chart, 正财=1, 偏财=2, 比肩=2, 劫财=2),
        has_wealth=True,
        supporting_count=1,
        draining_count=7,
        branch_conflict_intensity=0.7,
        chong_pairs=(("寅", "申"),),
        element_concentration=0.55,
        missing_elements=("火", "木"),
    )
    claim = _assert_single_valid(generate_gao_claims, chart, positive, _task("wealth.debt"))
    assert claim.school_id == "gao" and claim.claim_type == "event_claim"
    assert (claim.time_window.start_year, claim.time_window.end_year, claim.time_window.label) == LIFETIME
    assert claim.high_risk is True and claim.confidence <= HIGH_RISK_CONFIDENCE_CAP
    assert "债务风险" in claim.statement or "财富承压旁证" in claim.statement
    assert "必负债" not in claim.statement and "必破产" not in claim.statement
    assert "没有可核验的显著债务、长期负债或债务危机记录" in claim.falsifier

    wealth_only = _features(
        chart,
        ten_god_counts=_ten_gods(chart, 正财=1, 偏财=1, 比肩=0, 劫财=0),
        has_wealth=True,
        supporting_count=4,
        draining_count=4,
        branch_conflict_intensity=0.0,
        chong_pairs=(),
        element_concentration=0.3,
        missing_elements=(),
    )
    assert generate_gao_claims(chart, wealth_only, _task("wealth.debt")) == []
    conflict_only = replace(wealth_only, branch_conflict_intensity=0.8, chong_pairs=(("寅", "申"),))
    assert generate_gao_claims(chart, conflict_only, _task("wealth.debt")) == []
    assert generate_gao_claims(chart, replace(positive, evidence_completeness="partial"), _task("wealth.debt")) == []


def test_gao_health_outputs_only_moderate_or_high_structural_risk() -> None:
    chart = _chart()
    high = _features(
        chart,
        supporting_count=1,
        draining_count=7,
        cold_warm_axis=0.85,
        dry_wet_axis=0.72,
        climate_extreme=True,
        element_concentration=0.625,
        dominant_element="火",
        missing_elements=("水", "金"),
        branch_conflict_intensity=0.75,
        chong_pairs=(("子", "午"),),
    )
    claim = _assert_single_valid(generate_gao_claims, chart, high, _task("health.system_risk"))
    assert claim.school_id == "gao" and claim.claim_type == "event_claim"
    assert claim.applicability_snapshot["predicted_label"] == "high"
    assert claim.applicability_snapshot["predicted_label"] in {"moderate", "high"}
    assert claim.high_risk is True and claim.confidence <= HIGH_RISK_CONFIDENCE_CAP
    forbidden = ("诊断", "死亡", "寿限", "手术必然", "大灾")
    assert not any(token in claim.statement for token in forbidden)
    assert "医学结论" in claim.falsifier

    moderate = replace(high, climate_extreme=False, cold_warm_axis=0.2, dry_wet_axis=0.1, branch_conflict_intensity=0.1, chong_pairs=())
    moderate_claim = _assert_single_valid(generate_gao_claims, chart, moderate, _task("health.system_risk"))
    assert moderate_claim.applicability_snapshot["predicted_label"] == "moderate"

    neutral = _features(
        chart,
        supporting_count=4,
        draining_count=4,
        climate_extreme=False,
        cold_warm_axis=0.0,
        dry_wet_axis=0.0,
        element_concentration=0.3,
        missing_elements=(),
        branch_conflict_intensity=0.0,
        chong_pairs=(),
    )
    assert generate_gao_claims(chart, neutral, _task("health.system_risk")) == []
    assert generate_gao_claims(chart, replace(high, evidence_completeness="partial"), _task("health.system_risk")) == []


def test_gao_accepts_registered_timing_tasks_and_rejects_other_unregistered_tasks() -> None:
    chart = _chart()
    features = build_chart_feature_vector(chart)
    for task_id in ("wealth.major_loss_window", "health.event_window", "career.change_window"):
        assert generate_gao_claims(chart, features, _task(task_id)) == []
        assert DEFAULT_RUNNER_REGISTRY.resolve("gao", task_id) is generate_gao_claims

    for task_id in ("structure.overview", "career.role_change"):
        with pytest.raises(TaskUnsupported, match="gao does not support task"):
            generate_gao_claims(chart, features, _task(task_id))
        assert DEFAULT_RUNNER_REGISTRY.resolve("gao", task_id) is None


def _yang_positive(sex_marker: str) -> tuple[ChartFactLedger, ChartFeatureVector]:
    chart = _chart(sex_marker=sex_marker)
    male = sex_marker in {"乾", "男", "男命", "乾造", "M"}
    spouse_counts = {"正财": 0, "偏财": 0, "正官": 2, "七杀": 2} if not male else {"正财": 1, "偏财": 0, "正官": 0, "七杀": 0}
    features = _features(
        chart,
        ten_god_counts=_ten_gods(chart, **spouse_counts, 比肩=2, 劫财=2, 食神=2, 伤官=2),
        has_wealth=male,
        has_official=not male,
        has_output=True,
        mixed_official_kill=not male,
        branch_conflict_intensity=0.7,
        chong_pairs=(("子", "午"),),
        xing_hai_pairs=(("寅", "巳"),),
    )
    return chart, features


@pytest.mark.parametrize(("sex_marker", "expected_basis"), [("乾", "wealth"), ("坤", "official")])
def test_yang_uses_gender_specific_spouse_star_and_two_independent_signals(
    sex_marker: str, expected_basis: str,
) -> None:
    chart, features = _yang_positive(sex_marker)
    claim = _assert_single_valid(generate_yang_claims, chart, features, _task("marriage.divorce_or_remarriage"))
    assert claim.school_id == "yang" and claim.claim_type == "event_claim"
    assert (claim.time_window.start_year, claim.time_window.end_year, claim.time_window.label) == LIFETIME
    assert claim.high_risk is True and claim.confidence <= HIGH_RISK_CONFIDENCE_CAP
    assert claim.applicability_snapshot["spouse_star_basis"] == expected_basis
    assert claim.applicability_snapshot["independent_signal_count"] >= 2
    assert "存在离婚或再婚事件风险，但不作必然判断" in claim.statement
    assert "必离" not in claim.statement and "多婚命" not in claim.statement
    assert "婚姻史中没有离婚或再婚记录" in claim.falsifier


def test_yang_abstains_for_single_signal_relationship_pressure_or_missing_gender() -> None:
    chart = _chart(sex_marker="乾")
    spouse_present = _ten_gods(chart, 正财=2, 偏财=0, 比肩=0, 劫财=0, 食神=0, 伤官=0)
    palace_conflict_only = _features(
        chart,
        ten_god_counts=spouse_present,
        has_wealth=True,
        has_output=False,
        mixed_official_kill=False,
        chong_pairs=(("子", "午"),),
        xing_hai_pairs=(),
        branch_conflict_intensity=0.5,
    )
    task = _task("marriage.divorce_or_remarriage")
    assert generate_yang_claims(chart, palace_conflict_only, task) == []

    spouse_weak_only = replace(
        palace_conflict_only,
        ten_god_counts=_ten_gods(chart, 正财=0, 偏财=0, 比肩=0, 劫财=0, 食神=0, 伤官=0),
        has_wealth=False,
        chong_pairs=(),
        branch_conflict_intensity=0.0,
    )
    assert generate_yang_claims(chart, spouse_weak_only, task) == []

    pressure_only = replace(spouse_weak_only, ten_god_counts=_ten_gods(chart, 正财=2, 偏财=0, 比肩=3, 劫财=1), has_wealth=True)
    assert generate_yang_claims(chart, pressure_only, task) == []

    missing_gender = _chart(sex_marker="")
    missing_features = replace(spouse_weak_only, chart_id=build_chart_feature_vector(missing_gender).chart_id)
    assert generate_yang_claims(missing_gender, missing_features, task) == []
    assert generate_yang_claims(chart, replace(palace_conflict_only, evidence_completeness="partial"), task) == []


def test_yang_rejects_uncovered_marriage_tasks() -> None:
    chart = _chart()
    features = build_chart_feature_vector(chart)
    for task_id in ("marriage.relationship_pressure", "marriage.event_window", "marriage.late_marriage"):
        with pytest.raises(TaskUnsupported, match="yang does not support task"):
            generate_yang_claims(chart, features, _task(task_id))
        assert DEFAULT_RUNNER_REGISTRY.resolve("yang", task_id) is None


def test_registry_preserves_task5_capabilities_and_adds_gao_timing() -> None:
    assert DEFAULT_RUNNER_REGISTRY.resolve("ditiansui", "structure.overview") is generate_ditiansui_claims
    assert DEFAULT_RUNNER_REGISTRY.resolve("gao", "wealth.debt") is generate_gao_claims
    assert DEFAULT_RUNNER_REGISTRY.resolve("gao", "health.system_risk") is generate_gao_claims
    assert DEFAULT_RUNNER_REGISTRY.resolve("yang", "marriage.divorce_or_remarriage") is generate_yang_claims

    assert DEFAULT_RUNNER_REGISTRY.resolve("ditiansui", "wealth.debt") is None
    for task_id in (
        "career.change_window",
        "marriage.event_window",
        "health.event_window",
        "wealth.major_loss_window",
    ):
        assert DEFAULT_RUNNER_REGISTRY.resolve("gao", task_id) is generate_gao_claims
    assert DEFAULT_RUNNER_REGISTRY.resolve("gao", "structure.overview") is None
    assert DEFAULT_RUNNER_REGISTRY.resolve("gao", "career.role_change") is None
    assert DEFAULT_RUNNER_REGISTRY.resolve("yang", "marriage.event_window") is None
    assert DEFAULT_RUNNER_REGISTRY.resolve("yang", "marriage.relationship_pressure") is None


def test_default_orchestrator_preserves_task5_claim_abstain_and_unsupported() -> None:
    extreme_chart = ChartFactLedger(
        sex_marker="乾",
        four_pillars={"year": "丙午", "month": "丙午", "day": "丁巳", "hour": "丙午"},
    )
    rows = generate_blind_outputs(
        extreme_chart,
        [_task("structure.overview"), _task("wealth.debt")],
        case_id="C-TASK5-ORCHESTRATOR",
        schools=["ditiansui", "gao", "yang"],
    )
    indexed = {(row.school_id, row.task_id): row for row in rows}
    assert indexed[("ditiansui", "structure.overview")].state == "claim"
    assert indexed[("gao", "wealth.debt")].state == "abstain"
    assert indexed[("yang", "structure.overview")].state == "unsupported"
    assert indexed[("ditiansui", "structure.overview")].predictions[0].evidence_refs


def test_new_school_runners_are_statically_isolated_from_forbidden_inputs_and_other_runners() -> None:
    forbidden = ("feedback", "render_report", "report_view", "reports", "labels")
    other_runners = ("duan_runner", "ren_runner", "ziping_runner", "gao_runner", "yang_runner", "ditiansui_runner")
    for relative in (
        "engine/v5/ditiansui_runner.py",
        "engine/v5/gao_runner.py",
        "engine/v5/yang_runner.py",
    ):
        own_module = Path(relative).stem
        tree = ast.parse(Path(relative).read_text(encoding="utf-8"))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        assert not any(token in imported for imported in imports for token in forbidden)
        assert not any(token in imported for imported in imports for token in other_runners if token != own_module)

    assert "engine.pangzheng" not in Path("engine/v5/gao_runner.py").read_text(encoding="utf-8")
    assert "engine.picture" not in Path("engine/v5/yang_runner.py").read_text(encoding="utf-8")
