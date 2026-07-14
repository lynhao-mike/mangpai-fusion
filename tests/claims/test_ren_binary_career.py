"""RED test: ren runner must support career.role_change as a binary_event task.

Currently ren only supports timing tasks (career.change_window, etc).
For L1 routing to have competitive coverage, ren must also produce a
binary claim for career.role_change based on the same岁运冲合 triggers.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from engine.claims.domain import Claim, TaskUnsupported
from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindTask
from engine.features import build_chart_feature_vector
from engine.v5.ren_runner import generate_claims as generate_ren_claims


def _task(task_id: str = "career.role_change", **overrides: object) -> BlindTask:
    defaults = {
        "task_id": task_id,
        "domain": "事业",
        "claim_type": "binary_event",
        "scoring_method": "binary_probability",
        "quantifiable": True,
        "high_risk": False,
        "allowed_time_horizons": ["ten_year", "annual"],
        "required_input_fields": ["four_pillars"],
        "label_schema": {"type": "boolean", "positive_label": "occurred", "negative_label": "not_observed"},
        "evaluation_note": "fixture",
    }
    defaults.update(overrides)
    return BlindTask(**defaults)  # type: ignore[arg-type]


def _triggered_chart() -> ChartFactLedger:
    """A chart where liunian 甲辰 clashes with day branch 戌 → strong trigger."""
    return ChartFactLedger(
        four_pillars={"year": "癸未", "month": "甲寅", "day": "壬戌", "hour": "丙午"},
        dayun_steps=[{"ganzhi": "丙辰", "start_year": 2018, "end_year": 2027}],
        liunian_steps=[{"year": 2024, "ganzhi": "甲辰", "dayun": "丙辰"}],
    )


def _quiet_chart() -> ChartFactLedger:
    """No岁运冲合 trigger → should abstain (return [])."""
    return ChartFactLedger(
        four_pillars={"year": "甲子", "month": "乙丑", "day": "戊辰", "hour": "己未"},
        liunian_steps=[{"year": 2025, "ganzhi": "乙巳"}],
    )


def test_ren_produces_binary_event_claim_for_career_role_change() -> None:
    """Ren must not raise TaskUnsupported for career.role_change."""
    chart = _triggered_chart()
    features = build_chart_feature_vector(chart)
    task = _task()

    claims = generate_ren_claims(chart, features, task)

    assert len(claims) >= 1
    claim = claims[0]
    assert claim.school_id == "ren"
    assert claim.task_id == "career.role_change"
    # Binary event claim type, not timing
    assert claim.claim_type == "event_claim"
    # Must have evidence grounded in liunian triggers
    assert claim.evidence
    assert any("liunian" in ref for ev in claim.evidence for ref in ev.fact_refs)
    # Must have a falsifier
    assert claim.falsifier


def test_ren_binary_career_abstains_on_quiet_chart() -> None:
    """No trigger → empty claims (orchestrator maps to abstain)."""
    chart = _quiet_chart()
    features = build_chart_feature_vector(chart)

    claims = generate_ren_claims(chart, features, _task())

    assert claims == []


def test_ren_binary_career_uses_dayun_trigger_when_liunian_is_unavailable() -> None:
    """历史冻结批次只有大运序列；大运与原局发生关系时仍应形成二元事件命题。"""
    chart = ChartFactLedger(
        four_pillars={"year": "癸未", "month": "甲寅", "day": "壬戌", "hour": "丙午"},
        dayun_steps=[{"ganzhi": "丙辰"}],  # 辰冲日支戌
        liunian_steps=[],
    )
    features = build_chart_feature_vector(chart)

    claims = generate_ren_claims(chart, features, _task())

    assert len(claims) == 1
    assert claims[0].claim_type == "event_claim"
    assert any("dayun_steps.0" in ref for ev in claims[0].evidence for ref in ev.fact_refs)
    assert claims[0].time_window is not None
    assert claims[0].time_window.label == "lifetime"


def test_ren_binary_career_is_deterministic() -> None:
    """Same input always produces same output."""
    chart = _triggered_chart()
    features = build_chart_feature_vector(chart)
    task = _task()

    first = generate_ren_claims(chart, features, task)
    second = generate_ren_claims(chart, features, task)

    assert first == second
