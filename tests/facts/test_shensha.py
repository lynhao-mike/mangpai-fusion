"""神煞事实查表算子：只验证命中与出处，不涉及吉凶解释。"""
from __future__ import annotations

from engine.facts.chart_facts import chart_from_pillars
from engine.facts.shensha import find_shensha


def test_travel_horse_scans_year_and_day_anchors_independently():
    # 年支申起马在寅；日支子起马在寅；月支寅同时命中两种口径。
    chart = chart_from_pillars(["庚申", "戊寅", "壬子", "辛丑"], "乾")
    hits = [h for h in find_shensha(chart) if h.name == "驿马" and h.target_addr == "M.b"]
    assert {(h.anchor_addr, h.target_addr) for h in hits} == {
        ("Y.b", "M.b"), ("D.b", "M.b")
    }
    assert all("盲派神煞应用宝典.md:584" in h.source_ref for h in hits)
    assert all(h.method_note and h.name == "驿马" for h in hits)


def test_yang_yin_and_flying_blades_keep_distinct_names_and_anchors():
    yang_chart = chart_from_pillars(["丙午", "癸巳", "壬子", "丙午"], "乾")
    yang_hits = find_shensha(yang_chart)
    assert any(h.name == "羊刃" and h.anchor_addr == "D.s" and h.target_addr == "D.b" for h in yang_hits)
    assert any(h.name == "飞刃(阳)" and h.anchor_addr == "D.s" and h.target_addr == "Y.b" for h in yang_hits)

    yin_chart = chart_from_pillars(["丙午", "癸巳", "癸丑", "己未"], "乾")
    yin_hits = find_shensha(yin_chart)
    assert any(h.name == "阴刃" and h.anchor_addr == "D.s" and h.target_addr == "D.b" for h in yin_hits)
    assert any(h.name == "飞刃(阴)" and h.anchor_addr == "D.s" and h.target_addr == "H.b" for h in yin_hits)
    assert all("盲派神煞应用宝典.md:1095" in h.source_ref for h in (*yang_hits, *yin_hits) if "刃" in h.name)


def test_tianyi_supports_distinct_classic_and_day_night_methods():
    chart = chart_from_pillars(["乙酉", "甲申", "丙辰", "甲午"], "乾")
    hits = [h for h in find_shensha(chart) if h.name.startswith("天乙贵人")]
    assert any(h.name == "天乙贵人" and h.anchor_addr == "D.s" and h.target_addr == "Y.b" for h in hits)
    assert any(h.name == "天乙贵人(昼夜贵人)" for h in hits)
    assert all(h.source_ref and "盲派神煞应用宝典.md:" in h.source_ref for h in hits)


def test_monthly_virtues_and_kui_gang_are_separate_objective_hits():
    virtue_chart = chart_from_pillars(["甲子", "壬申", "癸丑", "壬子"], "乾")
    virtue_hits = find_shensha(virtue_chart)
    assert any(h.name == "天德贵人" and h.anchor_addr == "M.b" and h.target_addr == "D.s" for h in virtue_hits)
    assert any(h.name == "月德贵人" and h.anchor_addr == "M.b" and h.target_addr == "M.s" for h in virtue_hits)

    kui_gang_chart = chart_from_pillars(["甲子", "丙寅", "庚辰", "壬午"], "乾")
    kui_gang_hits = find_shensha(kui_gang_chart)
    assert any(h.name == "魁罡" and h.anchor_addr == "D" and h.target_addr == "D" for h in kui_gang_hits)


def test_flower_scans_year_and_day_anchors_independently():
    # 年支子所属申子辰，日支辰所属申子辰，桃花酉；两处酉分别保留两种起法。
    chart = chart_from_pillars(["甲子", "癸酉", "庚辰", "乙酉"], "乾")
    flower_hits = [h for h in find_shensha(chart) if h.name == "桃花" and h.target_addr in {"M.b", "H.b"}]
    assert {(h.anchor_addr, h.target_addr) for h in flower_hits} == {
        ("Y.b", "M.b"), ("Y.b", "H.b"), ("D.b", "M.b"), ("D.b", "H.b")
    }
