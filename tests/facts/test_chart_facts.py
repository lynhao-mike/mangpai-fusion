"""ChartFacts 构造、校验、口径差异与关系图位置模型测试。"""
from __future__ import annotations

from datetime import datetime

import pytest

from engine.facts import (
    ChartInputError,
    binzhu_side,
    build_relation_graph,
    chart_from_pillars,
    chart_from_solar,
    edges_between,
)
from engine.facts.chart_facts import hour_stem_for, load_profiles, month_stem_for
from engine.predicates.cycles import (
    CycleOutOfRange,
    PreQiyun,
    ganzhi_at,
    get_dayun_at_age,
    get_dayun_at_year,
    liunian_ganzhi,
)
from engine.predicates.types import Dayun, DayunStep, GanZhi


# ── 构造与校验 ──────────────────────────────────────────────────────────────

def test_pillars_entry_builds_positions_and_ten_gods():
    c = chart_from_pillars(["庚申", "戊寅", "壬子", "辛丑"], "乾")
    assert [p.palace for p in c.pillars] == ["year", "month", "day", "hour"]
    assert [p.stem.addr for p in c.pillars] == ["Y.s", "M.s", "D.s", "H.s"]
    assert c.pillars[2].stem.ten_god == "日主"
    assert c.pillars[1].stem.ten_god == "七杀"
    assert [h.char for h in c.pillars[3].branch.hidden] == ["己", "癸", "辛"]
    assert c.pillars[3].branch.hidden[0].qi == "本气"
    assert c.cycles is not None and c.cycles.direction == "顺"
    assert [s.ganzhi for s in c.cycles.dayun[:3]] == ["己卯", "庚辰", "辛巳"]


@pytest.mark.parametrize("pillars,needle", [
    (["庚申", "戊寅", "壬丑", "辛丑"], "非六十甲子"),
    (["庚申", "甲寅", "壬子", "辛丑"], "五虎遁"),
    (["庚申", "戊寅", "壬子", "癸丑"], "五鼠遁"),
])
def test_pillars_entry_rejects_invalid_input(pillars, needle):
    with pytest.raises(ChartInputError, match=needle):
        chart_from_pillars(pillars, "乾")


def test_supplied_dayun_must_match_month_sequence():
    with pytest.raises(ChartInputError, match="不一致"):
        chart_from_pillars(["庚申", "戊寅", "壬子", "辛丑"], "乾", dayun=["丁丑", "丙子"])
    c = chart_from_pillars(["庚申", "戊寅", "壬子", "辛丑"], "坤", dayun=["丁丑", "丙子"], dayun_start_year=1988)
    assert c.cycles.direction == "逆"
    assert (c.cycles.dayun[1].start_year, c.cycles.dayun[1].end_year) == (1998, 2007)


def test_late_zi_hour_stem_from_next_day_is_accepted_with_warning():
    # 甲子日晚子时：时干按次日乙日五鼠遁为丙子（《开山之作》:960）
    c = chart_from_pillars(["甲子", "丙子", "甲子", "丙子"], "乾")
    assert [w.kind for w in c.boundary_warnings] == ["hour_stem_next_day"]


def test_five_tiger_and_five_rat_tables():
    assert month_stem_for("甲", "寅") == "丙" and month_stem_for("戊", "子") == "甲"
    assert hour_stem_for("甲", "子") == "甲" and hour_stem_for("戊", "亥") == "癸"


def test_gender_must_be_recognized():
    with pytest.raises(ChartInputError):
        chart_from_pillars(["庚申", "戊寅", "壬子", "辛丑"], "X")


# ── 事实字段 ────────────────────────────────────────────────────────────────

def test_self_sit_marks_and_source_tags():
    c = chart_from_pillars(["丁亥", "壬寅", "甲午", "丙寅"], "乾")
    year, _, day, hour = c.pillars
    assert year.self_sit.stem_branch_relation == "支克干"
    assert any(t.tag == "干支自合·支合克干" and t.source_ref.endswith(":1338") for t in year.source_tags)
    assert any(t.tag == "干支自合·干合支" for t in day.source_tags)
    assert any(t.tag == "带象(干生支)" for t in day.source_tags)
    assert "坐长生" in hour.self_sit.marks
    assert "坐禄" in chart_from_pillars(["甲子", "丙寅", "甲寅", "丙寅"], "乾").pillars[2].self_sit.marks


def test_yang_ren_mark_and_yin_ren_tag():
    # 壬子日：壬刃在子 → marks 标坐羊刃
    c = chart_from_pillars(["庚申", "戊寅", "壬子", "辛丑"], "乾")
    assert "坐羊刃" in c.pillars[2].self_sit.marks
    # 癸丑日：高派阴刃（癸刃在丑）只作带出处的标签，不进 marks
    c2 = chart_from_pillars(["甲辰", "丙子", "癸丑", "壬子"], "乾")
    day = c2.pillars[2]
    assert "坐羊刃" not in day.self_sit.marks
    tag = [t for t in day.source_tags if t.tag == "坐阴刃"]
    assert len(tag) == 1 and tag[0].school == "gao" and tag[0].source_ref.endswith(":1095")


def test_kongwang_day_and_year():
    c = chart_from_pillars(["庚申", "戊寅", "壬子", "辛丑"], "乾")
    assert c.kongwang.by_day_xun == ("寅", "卯")       # 壬子在甲辰旬
    assert c.kongwang.by_year_xun == ("子", "丑")      # 庚申在甲寅旬
    assert ("M.b", "day") in c.kongwang.hits and ("D.b", "year") in c.kongwang.hits


def test_yin_changsheng_variant_only_lists_diffs():
    c = chart_from_pillars(["庚申", "戊寅", "壬子", "辛丑"], "乾")
    v = [v for v in c.variants if v.axis == "yin_changsheng"]
    assert len(v) == 1
    # 辛在丑：阴逆为养，从阳（庚）为墓
    assert ("/pillars/3/self_sit/stem_changsheng", "墓") in v[0].diffs
    assert all("/pillars/2/" not in path for path, _ in v[0].diffs), "阳干日柱不应有差异"


def test_profiles_registry_has_sources_for_every_value():
    for axis in load_profiles()["axes"].values():
        for body in axis["values"].values():
            assert body["source_refs"]


@pytest.mark.parametrize("layer,expected_main", [
    (1, {"D.s"}),
    (2, {"D.s", "D.b"}),
    (3, {"D.s", "D.b", "H.s", "H.b"}),
])
def test_binzhu_side_layers(layer, expected_main):
    natal = [f"{p}.{l}" for p in "YMDH" for l in "sb"]
    assert {a for a in natal if binzhu_side(a, layer) == "主"} == expected_main


def test_binzhu_layer4_cycles_are_guest():
    assert binzhu_side("Y.s", 4) == "主" and binzhu_side("DY3.b", 4) == "宾"
    with pytest.raises(ValueError):
        binzhu_side("LN2025.s", 1)


# ── 公历入口 ────────────────────────────────────────────────────────────────

def test_solar_entry_matches_lunar_python_and_has_qiyun_variants():
    c = chart_from_solar(datetime(1980, 2, 9, 2, 0), "乾")
    assert c.input.mode == "solar"
    assert [m.method for m in c.cycles.qiyun] == ["mangpai_rough", "precise"]
    # lunar-python 第 0 步（起运前、无干支）被过滤，真实大运与四柱入口一样从 1 编号
    assert c.cycles.dayun[0].index == 1 and c.cycles.dayun[0].ganzhi == "己卯"
    assert all(s.start_year is not None for s in c.cycles.dayun)


def test_solar_late_zi_produces_alt_chart():
    c = chart_from_solar(datetime(2024, 1, 10, 23, 30), "乾")
    assert [p.ganzhi for p in c.pillars] == ["癸卯", "乙丑", "癸酉", "甲子"]
    assert any(w.kind == "late_zi" for w in c.boundary_warnings)
    v = [v for v in c.variants if v.axis == "zi_shi"]
    assert len(v) == 1 and v[0].alt_chart_id and v[0].alt_chart_id != c.chart_id
    assert ("/pillars/2/ganzhi", "甲戌") in v[0].diffs


def test_solar_near_jie_warning():
    c = chart_from_solar(datetime(2024, 2, 4, 16, 0), "坤")   # 立春 16:27:07
    assert any(w.kind == "near_jie" and "立春" in w.detail for w in c.boundary_warnings)


def test_solar_rejects_aware_datetime():
    from datetime import timezone
    with pytest.raises(ChartInputError):
        chart_from_solar(datetime(2024, 1, 1, tzinfo=timezone.utc), "乾")


# ── 关系图位置模型 ──────────────────────────────────────────────────────────

def test_multi_relations_on_same_pair_are_separate_edges():
    g = build_relation_graph(chart_from_pillars(["庚申", "辛巳", "甲申", "丙寅"], "乾"))
    kinds = {e.kind: e for e in edges_between(g, "M.b", "D.b")}
    assert {"liuhe", "xing", "po"} <= set(kinds)
    assert kinds["xing"].completeness == "partial" and kinds["xing"].group == "寅巳申"
    assert kinds["xing"].attrs["group_full"] is True
    full = [e for e in g.edges if e.kind == "xing" and e.completeness == "full"]
    assert full and all(len(e.members) == 3 for e in full)
    yin_si = {e.kind for e in edges_between(g, "M.b", "H.b")}
    assert {"chuan", "xing"} <= yin_si


def test_distance_and_between_for_remote_stems():
    g = build_relation_graph(chart_from_pillars(["丁酉", "癸卯", "癸巳", "壬戌"], "乾"))
    he = [e for e in edges_between(g, "Y.s", "H.s") if e.kind == "wuhe"][0]
    assert he.distance == 3 and he.between == ("M.s", "D.s")
    assert he.attrs["month_branch_wuxing_is_huashen"] is True     # 卯木月，丁壬化木
    gz = [e for e in g.edges if e.kind == "ganzhi_zihe" and e.members == ("H.s", "H.b")][0]
    assert gz.attrs["requires_xing"] == "戌未刑" and gz.attrs["wei_present"] == []


def test_sanhe_completeness_variants():
    g = build_relation_graph(chart_from_pillars(["甲申", "丙子", "庚辰", "丙子"], "乾"))
    comps = {(e.members, e.completeness) for e in g.edges if e.kind == "sanhe"}
    assert (("Y.b", "M.b"), "half_sheng") in comps
    assert (("M.b", "D.b"), "half_mu") in comps
    assert (("Y.b", "D.b"), "gong") in comps
    assert (("Y.b", "M.b", "D.b"), "full") in comps


def test_liunian_and_dayun_nodes_have_no_distance():
    c = chart_from_pillars(["庚申", "戊寅", "壬子", "辛丑"], "乾", dayun_start_year=1988)
    g = build_relation_graph(c, dayun_index=4, liunian_year=2026)
    assert dict(g.nodes)["DY4.s"] == "壬" and dict(g.nodes)["LN2026.b"] == "午"
    chong = [e for e in edges_between(g, "D.b", "LN2026.b") if e.kind == "chong"][0]
    assert chong.scope == "liunian" and chong.distance is None
    with pytest.raises(ValueError):
        build_relation_graph(c, dayun_index=99)


def test_graph_is_json_serializable():
    import json
    g = build_relation_graph(chart_from_pillars(["甲辰", "乙亥", "丁丑", "丁未"], "乾"))
    json.dumps(g.to_dict(), ensure_ascii=False)


# ── cycles 修复 ─────────────────────────────────────────────────────────────

def _dayun() -> Dayun:
    steps = [DayunStep(序号=i + 1, 干支=GanZhi.parse(gz), 起岁=8 + 10 * i, 止岁=17 + 10 * i,
                       起讫年=(1988 + 10 * i, 1998 + 10 * i))
             for i, gz in enumerate(["己卯", "庚辰", "辛巳"])]
    return Dayun(起运岁=8.5, 起运年=1988, 顺逆="顺", 排布=steps)


def test_dayun_lookup_raises_instead_of_reusing_last_step():
    dy = _dayun()
    with pytest.raises(PreQiyun):
        get_dayun_at_age(dy, 5)
    with pytest.raises(CycleOutOfRange):
        get_dayun_at_age(dy, 60)
    with pytest.raises(CycleOutOfRange):
        get_dayun_at_year(dy, 1980, 2030)
    assert issubclass(CycleOutOfRange, ValueError) and issubclass(PreQiyun, ValueError)
    assert str(get_dayun_at_year(dy, 1980, 2010).干支) == "辛巳"


def test_liunian_exact_uses_lichun_moment():
    assert str(liunian_ganzhi(2024)) == "甲辰"
    assert [str(x) for x in ganzhi_at(datetime(2024, 2, 4, 16, 0))] == ["癸卯", "乙丑"]
    assert [str(x) for x in ganzhi_at(datetime(2024, 2, 4, 17, 0))] == ["甲辰", "丙寅"]
    assert str(ganzhi_at(datetime(2024, 1, 20))[0]) == "癸卯"
