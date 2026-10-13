"""出生输入到领域分析上下文的行为测试。"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from engine.asof.birth_to_bazi import BaziResult
from engine.v5.domain_slices.context import build_analysis_context
from engine.v5.domain_slices.contract import DomainAnalysisRequest


def _request(**overrides: object) -> DomainAnalysisRequest:
    values: dict[str, object] = {
        "gender": "乾",
        "birth_datetime": datetime(1990, 1, 1, 12, 0),
        "as_of_date": date(2026, 7, 31),
        "domains": ("career", "wealth", "marriage"),
        "output_dir": "reports/domain-analysis",
    }
    values.update(overrides)
    return DomainAnalysisRequest(**values)  # type: ignore[arg-type]


def test_build_context_maps_gender_and_derives_current_dayun(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, object] = {}

    def fake_calc(birth_datetime: datetime, gender: str) -> BaziResult:
        observed.update(birth_datetime=birth_datetime, gender=gender)
        return BaziResult(
            pillars=("己巳", "丙子", "丙寅", "甲午"),
            dayun=(
                {"ganzhi": "癸酉", "start_year": 2018},
                {"ganzhi": "壬申", "start_year": 2028},
            ),
            gender=gender,
            birth_datetime=birth_datetime.isoformat(sep=" ", timespec="seconds"),
        )

    monkeypatch.setattr("engine.v5.domain_slices.context.calc_bazi", fake_calc)

    context = build_analysis_context(_request())

    assert observed == {"birth_datetime": datetime(1990, 1, 1, 12, 0), "gender": "M"}
    assert context.current_dayun == {"ganzhi": "癸酉", "start_year": 2018, "end_year": 2027}
    assert context.future_years == ((2026, "丙午"), (2027, "丁未"), (2028, "戊申"))
    assert context.case_id.startswith("DA-乾-己巳丙子丙寅甲午-")


def test_build_context_maps_kun_to_female_calculator_input(monkeypatch: pytest.MonkeyPatch) -> None:
    genders: list[str] = []

    def fake_calc(birth_datetime: datetime, gender: str) -> BaziResult:
        genders.append(gender)
        return BaziResult(
            pillars=("己巳", "丙子", "丙寅", "甲午"),
            dayun=({"ganzhi": "甲戌", "start_year": 2020}, {"ganzhi": "乙亥", "start_year": 2030}),
            gender=gender,
            birth_datetime=birth_datetime.isoformat(sep=" ", timespec="seconds"),
        )

    monkeypatch.setattr("engine.v5.domain_slices.context.calc_bazi", fake_calc)

    build_analysis_context(_request(gender="坤"))

    assert genders == ["F"]


def test_build_context_fails_when_as_of_date_precedes_first_dayun(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "engine.v5.domain_slices.context.calc_bazi",
        lambda birth_datetime, gender: BaziResult(
            pillars=("己巳", "丙子", "丙寅", "甲午"),
            dayun=({"ganzhi": "甲戌", "start_year": 2030},),
            gender=gender,
            birth_datetime=birth_datetime.isoformat(sep=" ", timespec="seconds"),
        ),
    )

    with pytest.raises(ValueError, match="current dayun"):
        build_analysis_context(_request())
