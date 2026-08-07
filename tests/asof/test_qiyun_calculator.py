from __future__ import annotations

from datetime import datetime

import pytest

from engine.asof.qiyun_calculator import (
    JIE_NAMES,
    _rough_start_age,
    calc_qiyun,
)


@pytest.mark.parametrize(
    ("gender", "stem", "expected"),
    [
        ("M", "甲", True),
        ("男", "乙", False),
        ("F", "丙", False),
        ("女", "丁", True),
    ],
)
def test_direction_follows_gender_and_year_stem(
    gender: str, stem: str, expected: bool
) -> None:
    result = calc_qiyun(datetime(2000, 3, 10, 12, 0), gender, stem)

    assert result.is_shunpai is expected


def test_only_twelve_jie_are_exposed_and_qi_are_excluded() -> None:
    assert len(JIE_NAMES) == 12
    assert "雨水" not in JIE_NAMES
    assert "春分" not in JIE_NAMES
    assert "谷雨" not in JIE_NAMES

    # 阳年男顺排：2 月 10 日之后先遇雨水，但雨水是“气”，必须跳到惊蛰。
    result = calc_qiyun(datetime(2000, 2, 10, 12, 0), "M", "庚")
    assert result.ref_jie_name == "惊蛰"

    # 阳年女逆排：3 月 25 日之前先遇春分，但春分是“气”，必须跳到惊蛰。
    reverse = calc_qiyun(datetime(2000, 3, 25, 12, 0), "F", "庚")
    assert reverse.ref_jie_name == "惊蛰"


@pytest.mark.parametrize(
    ("diff_days", "expected"),
    [
        (0.0, 1),
        (1.99, 1),
        (4.0, 1),
        (5.0, 2),
        (7.0, 2),
        (8.0, 3),
        (29.0, 10),
        (40.0, 10),
    ],
)
def test_mang_pai_rough_age_boundaries(diff_days: float, expected: int) -> None:
    assert _rough_start_age(diff_days) == expected


def test_invalid_inputs_return_explanatory_result_instead_of_raising() -> None:
    result = calc_qiyun(datetime(2000, 1, 1), "unknown", "甲")

    assert result.ref_jie_name == ""
    assert result.hk_tw_start_datetime == ""
    assert "无法计算" in result.mang_pai_method


@pytest.mark.parametrize(
    (
        "birth_dt",
        "stem",
        "expected_forward",
        "expected_jie",
        "expected_rough_age",
        "expected_precise_years",
    ),
    [
        (datetime(1997, 4, 2, 1, 57), "丁", False, "惊蛰", 9, 9.067797068),
        (datetime(2002, 10, 11, 20, 30), "壬", True, "立冬", 9, 9.025883488),
        (datetime(1998, 3, 20, 0, 0), "戊", True, "清明", 5, 5.440960648),
    ],
)
def test_three_blocking_cases_real_calculation(
    birth_dt: datetime,
    stem: str,
    expected_forward: bool,
    expected_jie: str,
    expected_rough_age: int,
    expected_precise_years: float,
) -> None:
    result = calc_qiyun(birth_dt, "M", stem)

    assert result.is_shunpai is expected_forward
    assert result.ref_jie_name == expected_jie
    assert result.mang_pai_start_age == expected_rough_age
    assert result.hk_tw_start_years == pytest.approx(expected_precise_years, abs=1e-9)
