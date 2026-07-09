from __future__ import annotations

from engine.decision.l1_school_router import _chart_signals
from engine.decision.models import ChartFactLedger


def test_chart_signals_detects_complete_and_chong() -> None:
    chart = ChartFactLedger(four_pillars={"year": "甲寅", "month": "乙卯", "day": "丙子", "hour": "戊午"})

    signals = _chart_signals(chart)

    assert signals["complete"] is True
    assert signals["has_chong"] is True


def test_chart_signals_detects_skew_and_missing() -> None:
    chart = ChartFactLedger(four_pillars={"year": "甲寅", "month": "乙卯", "day": "甲寅", "hour": "乙卯"})

    signals = _chart_signals(chart)

    assert signals["skewed"] is True
    assert signals["missing_count"] >= 2


def test_chart_signals_incomplete_marks_not_complete() -> None:
    chart = ChartFactLedger(four_pillars={"year": "甲子", "month": "_", "day": "丙寅", "hour": "丁卯"})

    signals = _chart_signals(chart)

    assert signals["complete"] is False


def test_route_schools_upgrades_ditiansui_score_on_skewed_chart() -> None:
    from engine.decision.l1_school_router import route_schools
    from engine.decision.models import ContextFactLedger

    skewed = {"year": "甲寅", "month": "乙卯", "day": "甲寅", "hour": "乙卯"}
    balanced = {"year": "甲子", "month": "丁丑", "day": "庚辰", "hour": "壬午"}

    skewed_dt = next(i for i in route_schools(ChartFactLedger(four_pillars=skewed), ContextFactLedger()) if i.school == "ditiansui")
    balanced_dt = next(i for i in route_schools(ChartFactLedger(four_pillars=balanced), ContextFactLedger()) if i.school == "ditiansui")

    assert skewed_dt.applicability_score > balanced_dt.applicability_score
    assert any("偏枯" in r or "气势" in r for r in skewed_dt.reasons)


def test_route_schools_upgrades_duan_ren_role_on_chong_chart() -> None:
    from engine.decision.l1_school_router import route_schools
    from engine.decision.models import ContextFactLedger

    chong = {"year": "甲寅", "month": "乙卯", "day": "丙子", "hour": "戊午"}
    routed = {i.school: i for i in route_schools(ChartFactLedger(four_pillars=chong), ContextFactLedger())}

    assert routed["duan_jianye"].role == "lead"
    assert any("冲" in r for r in routed["duan_jianye"].reasons)


def test_different_chart_structures_produce_different_role_distributions() -> None:
    from engine.decision.l1_school_router import route_schools
    from engine.decision.models import ContextFactLedger

    chong = {"year": "甲寅", "month": "乙卯", "day": "丙子", "hour": "戊午"}
    no_chong = {"year": "甲子", "month": "丁丑", "day": "庚辰", "hour": "癸酉"}

    roles_chong = {i.school: i.role for i in route_schools(ChartFactLedger(four_pillars=chong), ContextFactLedger())}
    roles_plain = {i.school: i.role for i in route_schools(ChartFactLedger(four_pillars=no_chong), ContextFactLedger())}

    assert (roles_chong["duan_jianye"], roles_chong["ren_fuhong"]) != (
        roles_plain["duan_jianye"],
        roles_plain["ren_fuhong"],
    )
