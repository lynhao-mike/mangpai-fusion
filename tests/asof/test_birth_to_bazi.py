from __future__ import annotations

from datetime import datetime

import pytest

from engine.asof.birth_to_bazi import calc_bazi


def test_calc_bazi_returns_known_pillars_and_real_dayun_rows() -> None:
    result = calc_bazi(datetime(1990, 1, 1, 12, 0), "M")

    assert result.pillars == ("己巳", "丙子", "丙寅", "甲午")
    assert result.gender == "M"
    assert result.birth_datetime == "1990-01-01 12:00:00"
    assert result.dayun_method == "default_3day_1year"
    assert result.dayun[0] == {"ganzhi": "乙亥", "start_year": 1998}
    assert all(item["ganzhi"] for item in result.dayun)


def test_calc_bazi_uses_midnight_day_boundary() -> None:
    before_midnight = calc_bazi(datetime(1990, 1, 1, 23, 30), "F")
    at_midnight = calc_bazi(datetime(1990, 1, 2, 0, 0), "F")

    assert before_midnight.pillars[2] == "丙寅"
    assert at_midnight.pillars[2] == "丁卯"


def test_calc_bazi_rejects_unknown_gender() -> None:
    with pytest.raises(ValueError, match="gender"):
        calc_bazi(datetime(1990, 1, 1, 12, 0), "")
