from dataclasses import replace

import pytest

from engine.decision.models import ChartFactLedger
from engine.features.chart_feature_vector import build_chart_feature_vector


@pytest.fixture
def chart() -> ChartFactLedger:
    return ChartFactLedger(
        sex_marker="乾",
        solar_datetime="1990-06-15 12:00",
        four_pillars={"year": "庚午", "month": "壬午", "day": "甲寅", "hour": "庚午"},
        pillar_details={
            "year": {"pillar": "庚午"},
            "month": {"pillar": "壬午"},
            "day": {"pillar": "甲寅"},
            "hour": {"pillar": "庚午"},
        },
        siling="午",
        void_by_pillar={"year": [], "month": [], "day": [], "hour": []},
        start_luck="6岁",
        dayun_steps=[{"pillar": "癸未", "start_age": 6}],
        liunian_steps=[{"year": 2026, "pillar": "丙午"}],
        missing_fields=[],
        unknown_blocks=[],
        raw_source_hash="ziping-career-task-2-fixture",
    )


@pytest.fixture
def base_features(chart: ChartFactLedger):
    return build_chart_feature_vector(chart)


@pytest.fixture
def supported_features(base_features):
    return replace(
        base_features,
        ten_god_counts={
            "正官": 1,
            "七杀": 0,
            "食神": 0,
            "伤官": 1,
            "正财": 0,
            "偏财": 0,
            "正印": 0,
            "偏印": 0,
        },
        has_official=True,
        has_output=True,
        has_wealth=False,
        has_resource=False,
        mixed_official_kill=False,
        evidence_completeness="full",
    )


@pytest.fixture
def coarse_trigger_without_output_features(supported_features):
    return replace(
        supported_features,
        ten_god_counts={
            "正官": 1,
            "七杀": 0,
            "食神": 0,
            "伤官": 0,
            "正财": 0,
            "偏财": 0,
            "正印": 0,
            "偏印": 0,
        },
        has_output=False,
    )


@pytest.fixture
def protected_features(supported_features):
    return replace(
        supported_features,
        ten_god_counts={
            "正官": 1,
            "七杀": 0,
            "食神": 0,
            "伤官": 1,
            "正财": 1,
            "偏财": 0,
            "正印": 1,
            "偏印": 0,
        },
        has_wealth=True,
        has_resource=True,
    )
