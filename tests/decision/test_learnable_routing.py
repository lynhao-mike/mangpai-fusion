from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from engine.decision.capability_registry import CapabilityRegistry
from engine.decision.l1_school_router import RoutingRiskConfig, build_route_plan, route_schools
from engine.decision.models import ChartFactLedger, ContextFactLedger
from engine.evaluation.models import BlindTask
from engine.features import ChartFeatureVector


def _vector() -> ChartFeatureVector:
    return ChartFeatureVector(
        schema_version="cfv-v1",
        chart_id="routing-chart",
        element_counts={"木": 2, "火": 2, "土": 2, "金": 1, "水": 1},
        element_energy={"木": 0.2, "火": 0.2, "土": 0.2, "金": 0.2, "水": 0.2},
        dominant_element="木",
        missing_elements=(),
        element_concentration=0.25,
        day_master="甲",
        day_master_element="木",
        month_branch="辰",
        month_lord="戊",
        rooted_count=1,
        supporting_count=4,
        draining_count=4,
        monthly_command_favorable=False,
        ten_god_counts={name: 0 for name in ("比肩", "劫财", "食神", "伤官", "正财", "偏财", "正官", "七杀", "正印", "偏印")},
        has_official=False,
        has_wealth=False,
        has_output=False,
        has_resource=False,
        mixed_official_kill=False,
        chong_pairs=(),
        he_pairs=(),
        xing_hai_pairs=(),
        branch_conflict_intensity=0.1,
        cold_warm_axis=0.0,
        dry_wet_axis=0.0,
        climate_extreme=False,
        has_hour_pillar=True,
        evidence_completeness="full",
    )


def _task(task_id: str = "career.role_change", *, high_risk: bool = False) -> BlindTask:
    return BlindTask(
        task_id=task_id,
        domain="事业",
        claim_type="binary_event",
        scoring_method="binary_probability",
        quantifiable=True,
        high_risk=high_risk,
        allowed_time_horizons=["lifetime"],
        required_input_fields=["four_pillars"],
        label_schema={"type": "boolean"},
        evaluation_note="routing test",
    )


def _row(
    school: str,
    mean: float,
    interval: tuple[float, float],
    *,
    n_eff: float = 10,
    gain: float = 0.0,
    coverage: float = 1.0,
    grade: str = "E3",
) -> dict[str, object]:
    return {
        "school_id": school,
        "task_id": "career.role_change",
        "chart_prototype_id": "prototype-balanced",
        "claim_type": "binary_event",
        "time_horizon": "lifetime",
        "evidence_completeness_band": "complete",
        "coverage_rate": coverage,
        "discrimination_score": 0.3,
        "accuracy_score": mean,
        "calibration_error": 0.1,
        "posterior_mean": mean,
        "credible_interval": list(interval),
        "n_eff": n_eff,
        "evidence_grade": grade,
        "last_evaluated_at": "2026-07-14T00:00:00Z",
        "incremental_gain": gain,
    }


def _registry(tmp_path: Path, rows: list[dict[str, object]]) -> CapabilityRegistry:
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps({"schema_version": "school-capability-scores/v1", "freeze_hash": "frozen", "posteriors": rows}), encoding="utf-8")
    return CapabilityRegistry.from_snapshot(path)


def test_high_capability_low_uncertainty_school_becomes_primary(tmp_path: Path) -> None:
    registry = _registry(tmp_path, [_row("ziping", 0.82, (0.72, 0.9)), _row("ren", 0.62, (0.52, 0.72))])

    plan = build_route_plan(
        feature_vector=_vector(),
        tasks=[_task()],
        evidence_completeness_band="complete",
        registry=registry,
        risk_config=RoutingRiskConfig(schools=("ziping", "ren")),
    )

    route = plan.per_task_routes["career.role_change"]
    assert route.primary_schools[0] == "ziping"
    assert route.evidence_status == "sufficient"
    assert plan.capability_snapshot_id == registry.snapshot_id
    assert "prototype-balanced" in plan.route_rationale


def test_high_mean_wide_interval_is_penalized_below_calibrated_school(tmp_path: Path) -> None:
    registry = _registry(tmp_path, [_row("ziping", 0.9, (0.1, 1.0)), _row("ren", 0.72, (0.64, 0.8))])

    route = build_route_plan(
        feature_vector=_vector(), tasks=[_task()], evidence_completeness_band="complete", registry=registry,
        risk_config=RoutingRiskConfig(schools=("ziping", "ren"), risk_factor=0.6),
    ).per_task_routes["career.role_change"]

    assert route.primary_schools[0] == "ren"
    assert route.school_scores["ren"] > route.school_scores["ziping"]


def test_positive_incremental_gain_selects_counter_school(tmp_path: Path) -> None:
    registry = _registry(
        tmp_path,
        [
            _row("ziping", 0.82, (0.72, 0.9), gain=0.02),
            _row("ren", 0.7, (0.6, 0.8), gain=0.16),
            _row("gao_dechen", 0.55, (0.45, 0.65), gain=-0.1),
        ],
    )

    route = build_route_plan(
        feature_vector=_vector(), tasks=[_task()], evidence_completeness_band="complete", registry=registry,
        risk_config=RoutingRiskConfig(schools=("ziping", "ren", "gao_dechen")),
    ).per_task_routes["career.role_change"]

    assert route.primary_schools[0] == "ziping"
    assert route.counter_school == "ren"


def test_all_insufficient_evidence_abstains_instead_of_forcing_static_winner(tmp_path: Path) -> None:
    registry = _registry(tmp_path, [_row("ziping", 0.9, (0.2, 1.0), n_eff=2, grade="E1"), _row("ren", 0.8, (0.1, 1.0), n_eff=1, grade="E0")])

    route = build_route_plan(
        feature_vector=_vector(), tasks=[_task(high_risk=True)], evidence_completeness_band="complete", registry=registry,
        risk_config=RoutingRiskConfig(schools=("ziping", "ren")),
    ).per_task_routes["career.role_change"]

    assert route.primary_schools == ()
    assert route.evidence_status == "insufficient"
    assert set(route.abstain_candidates) == {"ziping", "ren"}
    assert "证据不足" in route.rationale


def test_static_mode_remains_default_and_learned_mode_is_explicit(tmp_path: Path) -> None:
    chart = ChartFactLedger(four_pillars={"year": "甲子", "month": "丁丑", "day": "庚辰", "hour": "癸未"})
    context = ContextFactLedger(analysis_focus_text="事业")
    static_default = route_schools(chart, context)
    static_explicit = route_schools(chart, context, routing_mode="static")
    assert static_default == static_explicit

    registry = _registry(tmp_path, [_row("ziping", 0.82, (0.72, 0.9)), _row("ren", 0.62, (0.52, 0.72))])
    learned = route_schools(
        chart,
        context,
        routing_mode="learned",
        tasks=[_task()],
        registry=registry,
        risk_config=RoutingRiskConfig(schools=("ziping", "ren")),
    )
    assert learned.capability_snapshot_id == registry.snapshot_id
    assert learned.per_task_routes["career.role_change"].primary_schools
