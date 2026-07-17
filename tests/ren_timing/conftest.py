from __future__ import annotations

import pytest

from engine.decision.models import ChartFactLedger, EventHypothesis
from engine.features import build_chart_feature_vector


@pytest.fixture
def career_event() -> EventHypothesis:
    return EventHypothesis(
        event_id="evt-career-role-change-001",
        source_verdict_ids=["sv-career-001"],
        domain="事业",
        event_type="career.role_change",
        subject="命主",
        concrete_event="职业角色或岗位发生显著变化",
        landing_path="上游事件资格已通过；任派只负责应期",
        confidence=0.72,
    )


@pytest.fixture
def trigger_chart() -> ChartFactLedger:
    return ChartFactLedger(
        sex_marker="乾",
        four_pillars={"year": "庚申", "month": "戊寅", "day": "壬子", "hour": "辛丑"},
        dayun_steps=[{"ganzhi": "甲午", "start_year": 2024, "end_year": 2033}],
        liunian_steps=[
            {"year": 2026, "ganzhi": "丙午", "dayun": "甲午"},
            {"year": 2028, "ganzhi": "戊申", "dayun": "甲午"},
        ],
    )


@pytest.fixture
def no_trigger_chart() -> ChartFactLedger:
    return ChartFactLedger(
        sex_marker="乾",
        four_pillars={"year": "甲子", "month": "丁卯", "day": "庚午", "hour": "己酉"},
        dayun_steps=[{"ganzhi": "丙辰", "start_year": 2024, "end_year": 2033}],
        liunian_steps=[{"year": 2027, "ganzhi": "丁巳", "dayun": "丙辰"}],
    )


@pytest.fixture
def partial_chart() -> ChartFactLedger:
    return ChartFactLedger(
        sex_marker="乾",
        four_pillars={"year": "庚申", "month": "戊寅", "day": "壬子", "hour": "辛丑"},
        dayun_steps=[],
        liunian_steps=[],
        missing_fields=["dayun", "liunian"],
    )


@pytest.fixture
def trigger_features(trigger_chart: ChartFactLedger):
    return build_chart_feature_vector(trigger_chart)
