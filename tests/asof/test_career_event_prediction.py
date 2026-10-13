from __future__ import annotations

import inspect
from dataclasses import replace

import pytest

from engine.asof.career_event_prediction import (
    CAREER_ROLE_CHANGE_MODEL_ID,
    CareerPredictionWindow,
    predict_career_role_change,
)
from engine.decision.models import ChartFactLedger
from engine.v5.ren_runner import generate_claims as generate_legacy_ren_claims
from engine.evaluation.models import BlindTask
from engine.features import build_chart_feature_vector


def _career_task() -> BlindTask:
    return BlindTask(
        task_id="career.role_change",
        domain="事业",
        claim_type="event",
        scoring_method="binary_event",
        quantifiable=True,
        high_risk=False,
        allowed_time_horizons=["lifetime", "annual"],
        required_input_fields=["four_pillars"],
        label_schema={"type": "boolean"},
        evaluation_note="legacy comparison fixture",
    )


def _chart(
    *,
    pillars: dict[str, str] | None = None,
    liunian_steps: list[dict[str, object]] | None = None,
) -> ChartFactLedger:
    return ChartFactLedger(
        sex_marker="乾",
        four_pillars=pillars
        or {"year": "癸未", "month": "甲寅", "day": "壬戌", "hour": "丙午"},
        dayun_steps=[{"ganzhi": "丙辰", "start_year": 2018, "end_year": 2027}],
        liunian_steps=liunian_steps
        if liunian_steps is not None
        else [
            {"year": 2024, "ganzhi": "甲辰", "dayun": "丙辰"},
            {"year": 2030, "ganzhi": "庚戌", "dayun": "丁巳"},
        ],
    )


def test_structure_gate_blocks_timing_only_false_positive() -> None:
    chart = _chart(
        pillars={"year": "庚申", "month": "戊寅", "day": "壬子", "hour": "辛丑"},
        liunian_steps=[{"year": 2024, "ganzhi": "甲辰", "dayun": "丙辰"}],
    )
    features = build_chart_feature_vector(chart)
    legacy = generate_legacy_ren_claims(chart, features, _career_task())
    assert legacy, "旧 Ren 路径会从岁运关系直接生成职业事件"

    result = predict_career_role_change(
        case_id="C-SHARED-NEGATIVE-STRUCTURE",
        chart=chart,
        window=CareerPredictionWindow(2024, 2024, "historical"),
    )

    assert result.status == "structure_abstain"
    assert result.structure_claims == ()
    assert result.event_hypotheses == ()
    assert result.timing_probabilities == ()
    assert result.timing_result.routing_blockers == ("qualified_career_event_required",)


def test_qualified_structure_then_real_annual_trigger_emits_complete_chain() -> None:
    result = predict_career_role_change(
        case_id="C-SHARED-CHAIN",
        chart=_chart(),
        window=CareerPredictionWindow(2024, 2024, "historical"),
    )

    assert result.model_id == CAREER_ROLE_CHANGE_MODEL_ID
    assert result.status == "predicted"
    assert len(result.structure_claims) == 1
    assert len(result.structural_verdicts) == 1
    assert len(result.event_hypotheses) == 1
    assert len(result.timing_probabilities) == 1
    claim = result.structure_claims[0]
    verdict = result.structural_verdicts[0]
    event = result.event_hypotheses[0]
    timing = result.timing_probabilities[0]
    assert verdict.claim_id == claim.claim_id
    assert event.source_verdict_ids == [verdict.verdict_id]
    assert event.event_type == "career.role_change"
    assert timing.event_id == event.event_id
    assert timing.time_window == {"start_year": 2024, "end_year": 2024, "label": "annual"}
    assert timing.trigger_conditions
    assert any("liunian_steps[year=2024" in ref for ref in timing.trigger_conditions)


def test_qualified_structure_without_window_trigger_abstains_only_at_timing() -> None:
    result = predict_career_role_change(
        case_id="C-SHARED-NO-TIMING",
        chart=_chart(liunian_steps=[{"year": 2024, "ganzhi": "甲辰", "dayun": "丙辰"}]),
        window=CareerPredictionWindow(2025, 2025, "future"),
    )

    assert result.status == "timing_abstain"
    assert len(result.structure_claims) == 1
    assert len(result.event_hypotheses) == 1
    assert result.timing_probabilities == ()
    assert "liunian_required" in result.timing_result.input_blockers


def test_historical_and_future_modes_share_same_predictor_and_structure_identity() -> None:
    chart = _chart()
    historical = predict_career_role_change(
        case_id="C-SHARED-MODES",
        chart=chart,
        window=CareerPredictionWindow(2024, 2024, "historical"),
    )
    future = predict_career_role_change(
        case_id="C-SHARED-MODES",
        chart=chart,
        window=CareerPredictionWindow(2030, 2030, "future"),
    )

    assert historical.features.chart_id == future.features.chart_id
    assert historical.structure_claims[0].claim_id == future.structure_claims[0].claim_id
    assert historical.event_hypotheses[0].event_id == future.event_hypotheses[0].event_id
    assert historical.timing_probabilities[0].time_window["start_year"] == 2024
    assert future.timing_probabilities[0].time_window["start_year"] == 2030
    assert historical.window.mode == "historical"
    assert future.window.mode == "future"


def test_window_filter_is_order_independent_and_excludes_out_of_window_years() -> None:
    chart = _chart()
    reversed_chart = replace(chart, liunian_steps=list(reversed(chart.liunian_steps)))
    window = CareerPredictionWindow(2024, 2024, "historical")

    left = predict_career_role_change(case_id="C-SHARED-ORDER", chart=chart, window=window)
    right = predict_career_role_change(
        case_id="C-SHARED-ORDER",
        chart=reversed_chart,
        window=window,
    )

    assert left.to_dict() == right.to_dict()
    assert left.timing_probabilities[0].time_window["start_year"] == 2024
    assert all("2030" not in ref for ref in left.timing_probabilities[0].trigger_conditions)


def test_public_api_has_no_reality_label_or_feedback_inputs() -> None:
    parameters = set(inspect.signature(predict_career_role_change).parameters)
    forbidden = {
        "known_facts",
        "known_fact_text",
        "feedback",
        "verification",
        "labels",
        "revealed_labels",
        "calibration",
    }
    assert parameters == {"case_id", "chart", "window"}
    assert parameters.isdisjoint(forbidden)


@pytest.mark.parametrize(
    ("start_year", "end_year", "mode", "error"),
    [
        (2025, 2024, "historical", ValueError),
        (2024, 2024, "calibrated", ValueError),
        (2024.0, 2024, "future", TypeError),
    ],
)
def test_window_contract_fails_closed(
    start_year: object,
    end_year: object,
    mode: object,
    error: type[Exception],
) -> None:
    with pytest.raises(error):
        CareerPredictionWindow(start_year, end_year, mode)  # type: ignore[arg-type]
