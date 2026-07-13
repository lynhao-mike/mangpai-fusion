from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from engine.decision.l1_school_router import _chart_signals
from engine.decision.models import ChartFactLedger
from engine.features import ChartFeatureVector, build_chart_feature_vector
from engine.predicates.palace import get_shishen
from engine.v5.ziping_runner import _shishen


REAL_CHARTS = {
    "C-2026-001": ChartFactLedger(
        sex_marker="乾",
        solar_datetime="1980-02-09 02:00",
        four_pillars={"year": "庚申", "month": "戊寅", "day": "壬子", "hour": "辛丑"},
    ),
    "C-2026-002": ChartFactLedger(
        sex_marker="坤",
        solar_datetime="1982-10-12 07:20",
        four_pillars={"year": "壬戌", "month": "庚戌", "day": "戊辰", "hour": "丙辰"},
    ),
    "C-2026-014": ChartFactLedger(
        sex_marker="乾",
        solar_datetime="2006-12-12 09:45",
        four_pillars={"year": "丙戌", "month": "庚子", "day": "乙亥", "hour": "辛巳"},
    ),
}


def test_feature_vector_is_frozen_validated_and_json_round_trips() -> None:
    vector = build_chart_feature_vector(REAL_CHARTS["C-2026-001"])

    assert ChartFeatureVector.from_dict(vector.to_dict()) == vector
    assert isinstance(vector.chong_pairs, tuple)
    assert isinstance(vector.element_counts, dict) is False
    with pytest.raises(FrozenInstanceError):
        vector.day_master = "甲"  # type: ignore[misc]
    with pytest.raises(TypeError):
        vector.element_counts["木"] = 99  # type: ignore[index]

    with pytest.raises(ValueError, match="element_energy"):
        replace(vector, element_energy={"木": 0.2, "火": 0.2, "土": 0.2, "金": 0.2, "水": 0.1})
    with pytest.raises(ValueError, match="evidence_completeness"):
        replace(vector, evidence_completeness="unknown")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cold_warm_axis"):
        replace(vector, cold_warm_axis=1.01)
    with pytest.raises(ValueError, match="dry_wet_axis"):
        replace(vector, dry_wet_axis=-1.01)

    invalid = vector.to_dict()
    invalid["chong_pairs"] = [["子"]]
    with pytest.raises(ValueError, match="chong_pairs"):
        ChartFeatureVector.from_dict(invalid)


def test_same_chart_and_schema_produce_stable_identity_and_payload() -> None:
    first = build_chart_feature_vector(REAL_CHARTS["C-2026-001"])
    second = build_chart_feature_vector(REAL_CHARTS["C-2026-001"])
    next_schema = build_chart_feature_vector(REAL_CHARTS["C-2026-001"], schema_version="cfv-v2-test")

    assert first == second
    assert first.chart_id == second.chart_id
    assert first.chart_id != next_schema.chart_id
    assert first.to_dict() == second.to_dict()


def test_real_chart_001_has_expected_element_energy_ten_gods_and_neutral_signals() -> None:
    vector = build_chart_feature_vector(REAL_CHARTS["C-2026-001"])

    assert dict(vector.element_counts) == {"木": 1, "火": 0, "土": 2, "金": 3, "水": 2}
    assert dict(vector.element_energy) == pytest.approx(
        {"木": 1 / 9.5, "火": 0.3 / 9.5, "土": 2.4 / 9.5, "金": 3.2 / 9.5, "水": 2.6 / 9.5}
    )
    assert vector.dominant_element == "金"
    assert vector.missing_elements == ("火",)
    assert vector.element_concentration == pytest.approx(3 / 8)
    assert vector.day_master == "壬"
    assert vector.day_master_element == "水"
    assert vector.month_branch == "寅"
    assert vector.month_lord == "甲"
    assert vector.rooted_count == 3
    assert vector.supporting_count == 5
    assert vector.draining_count == 3
    assert vector.monthly_command_favorable is False
    assert dict(vector.ten_god_counts) == {
        "比肩": 2,
        "劫财": 2,
        "食神": 1,
        "伤官": 0,
        "正财": 0,
        "偏财": 1,
        "正官": 1,
        "七杀": 3,
        "正印": 2,
        "偏印": 2,
    }
    assert vector.has_official and vector.has_wealth and vector.has_output and vector.has_resource
    assert vector.mixed_official_kill
    assert vector.chong_pairs == (("申", "寅"),)
    assert ("子", "丑") in vector.he_pairs
    assert vector.has_hour_pillar
    assert vector.evidence_completeness == "full"
    assert vector.climate_extreme is False


@pytest.mark.parametrize(
    ("case_id", "day_master", "month_branch", "expected_chong", "expected_extreme"),
    [
        ("C-2026-001", "壬", "寅", ("申", "寅"), False),
        ("C-2026-002", "戊", "戌", ("戌", "辰"), True),
        ("C-2026-014", "乙", "子", ("巳", "亥"), True),
    ],
)
def test_three_real_case_goldens(
    case_id: str,
    day_master: str,
    month_branch: str,
    expected_chong: tuple[str, str],
    expected_extreme: bool,
) -> None:
    vector = build_chart_feature_vector(REAL_CHARTS[case_id])

    assert vector.day_master == day_master
    assert vector.month_branch == month_branch
    assert expected_chong in vector.chong_pairs or tuple(reversed(expected_chong)) in vector.chong_pairs
    assert vector.climate_extreme is expected_extreme
    assert sum(vector.element_energy.values()) == pytest.approx(1.0, abs=1e-12)
    assert 0.0 <= vector.branch_conflict_intensity <= 1.0
    assert -1.0 <= vector.cold_warm_axis <= 1.0
    assert -1.0 <= vector.dry_wet_axis <= 1.0


def test_no_hour_chart_is_supported_without_inventing_an_hour_pillar() -> None:
    chart = ChartFactLedger(
        sex_marker="乾",
        four_pillars={"year": "庚申", "month": "戊寅", "day": "壬子", "hour": "_"},
        missing_fields=["$FOUR.hour"],
    )

    vector = build_chart_feature_vector(chart)

    assert vector.has_hour_pillar is False
    assert vector.evidence_completeness == "no_hour"
    assert sum(vector.element_counts.values()) == 6
    assert vector.supporting_count + vector.draining_count == 6


def test_wuwei_liuhe_is_preserved_even_without_a_fixed_transformation_element() -> None:
    vector = build_chart_feature_vector(
        ChartFactLedger(
            four_pillars={"year": "甲午", "month": "辛未", "day": "丙寅", "hour": "戊戌"},
        )
    )

    assert ("午", "未") in vector.he_pairs


def test_feature_vector_covers_legacy_l1_structural_signals() -> None:
    for chart in (
        REAL_CHARTS["C-2026-001"],
        ChartFactLedger(four_pillars={"year": "甲寅", "month": "乙卯", "day": "甲寅", "hour": "乙卯"}),
    ):
        legacy = _chart_signals(chart)
        vector = build_chart_feature_vector(chart)
        vector_skewed = vector.element_concentration >= 0.5 or len(vector.missing_elements) >= 2

        assert bool(vector.chong_pairs) is legacy["has_chong"]
        assert vector_skewed is legacy["skewed"]
        assert len(vector.missing_elements) == legacy["missing_count"]
        assert (vector.evidence_completeness == "full") is legacy["complete"]


def test_ziping_and_feature_layer_share_one_ten_god_function() -> None:
    for day_master in "甲乙丙丁戊己庚辛壬癸":
        for target in "甲乙丙丁戊己庚辛壬癸":
            assert _shishen(day_master, target) == get_shishen(target, day_master)
