"""StructureCheck 第 4 层：目录驱动的构成要件核对 + 段派做功候选。"""
from __future__ import annotations

from dataclasses import fields

import pytest

from engine.facts import build_relation_graph, build_strength_facts, chart_from_pillars
from engine.facts.relation_graph import edge_by_id
from engine.facts.structure_check import (
    CheckItem,
    StructureCheck,
    build_duan_zuogong_candidates,
    check_structure,
    check_structures,
    load_structures,
    tiyong_view,
)

ZIPING_EIGHT = {
    "ziping_zhengguan", "ziping_cai", "ziping_yin", "ziping_shishen",
    "ziping_qisha", "ziping_shangguan", "ziping_yangren", "ziping_jianlu",
}


def _check(sid, pillars, gender="乾"):
    chart = chart_from_pillars(pillars, gender)
    graph = build_relation_graph(chart)
    return check_structure(sid, chart, graph, build_strength_facts(chart)), graph


def _items(sc: StructureCheck) -> dict[str, CheckItem]:
    return {i.id: i for i in sc.items}


# ── 契约 ────────────────────────────────────────────────────────────────────

def test_catalog_has_eight_ziping_structures_with_source_refs():
    catalog = load_structures()
    assert ZIPING_EIGHT <= set(catalog)
    for sid in ZIPING_EIGHT:
        refs = catalog[sid]["source_refs"]
        assert refs and all(r.startswith("sources/ziping/《子平真诠》.md:") for r in refs)


def test_structure_check_has_no_verdict_fields():
    names = {f.name for f in fields(StructureCheck)} | {f.name for f in fields(CheckItem)}
    assert not names & {"is_formed", "score", "layer", "level", "grade"}


def test_all_structures_evaluate_with_controlled_status():
    chart = chart_from_pillars(["丁卯", "己酉", "甲子", "壬申"], "乾")
    for sc in check_structures(chart, build_relation_graph(chart), build_strength_facts(chart)):
        for item in sc.items:
            assert item.status in ("met", "unmet", "not_evaluable", "needs_judgment")
            assert item.kind in ("requirement", "breaker", "rescuer")


# ── 《子平真诠》:53 甲日酉官、丁伤克官、壬合丁护辛 ───────────────────────────

def test_zhengguan_broken_then_rescued_by_ren_he_ding():
    sc, graph = _check("ziping_zhengguan", ["丁卯", "己酉", "甲子", "壬申"])
    it = _items(sc)
    assert it["req_month_guan"].status == "met" and "M.b" in it["req_month_guan"].evidence
    assert it["brk_shangguan_jian_guan"].status == "met"
    assert {"Y.s", "M.b"} <= set(it["brk_shangguan_jian_guan"].evidence)
    he = it["rsc_he_qu_shang"]
    assert he.status == "met"
    assert {edge_by_id(graph, e).kind for e in he.evidence} == {"wuhe"}
    assert set(edge_by_id(graph, he.evidence[0]).members) == {"Y.s", "H.s"}
    assert it["rsc_yin_zhi_shang"].status == "met"          # 壬偏印克丁
    assert it["brk_sha_hun_guan"].status == "unmet"
    assert "sources/ziping/《子平真诠》.md:53" in sc.source_refs
    assert sc.judgment_points


def test_zhengguan_broken_without_rescuer():
    sc, _ = _check("ziping_zhengguan", ["丁卯", "己酉", "甲子", "戊辰"])
    it = _items(sc)
    assert it["brk_shangguan_jian_guan"].status == "met"
    assert it["rsc_he_qu_shang"].status == "unmet"
    assert it["rsc_yin_zhi_shang"].status == "unmet"


# ── 七杀格：食神制杀 vs 枭神夺食 ──────────────────────────────────────────────

def test_qisha_with_shishen_control():
    sc, graph = _check("ziping_qisha", ["丙子", "丙申", "甲寅", "庚午"])
    it = _items(sc)
    assert it["req_month_sha"].status == "met"
    zhi = it["xs_shishen_zhi_sha"]
    assert zhi.status == "met"
    edges = [edge_by_id(graph, e) for e in zhi.evidence]
    assert all(e.kind == "ke" and e.members[1] == "H.s" for e in edges)
    assert it["brk_xiao_duo_shi"].status == "unmet"


def test_qisha_xiao_duo_shi_breaker():
    sc, graph = _check("ziping_qisha", ["丙子", "丙申", "甲寅", "壬申"])
    it = _items(sc)
    assert it["req_month_sha"].status == "met"
    assert it["xs_shishen_zhi_sha"].status == "unmet"
    brk = it["brk_xiao_duo_shi"]
    assert brk.status == "met"
    assert {edge_by_id(graph, e).members for e in brk.evidence} == {("H.s", "Y.s"), ("H.s", "M.s")}
    assert it["rsc_cai_zhi_xiao"].status == "unmet"


def test_strength_comparisons_are_needs_judgment():
    sc, _ = _check("ziping_shishen", ["丙子", "丙申", "甲寅", "壬申"])
    item = _items(sc)["str_shen_wang_you_gen"]
    assert item.status == "needs_judgment"
    assert "D.s" in item.evidence


# ── 段派体用与做功候选 ────────────────────────────────────────────────────────

def test_tiyong_view_marks_shishang_as_dual():
    view = tiyong_view(chart_from_pillars(["丁卯", "己酉", "甲子", "丙寅"], "乾"))
    assert view["D.s"] == "体"
    assert view["M.b"] == "用"          # 酉 正官
    assert view["Y.s"] == "双属"        # 丁 伤官
    assert view["H.s"] == "双属"        # 丙 食神
    assert view["Y.b"] == "体"          # 卯 劫财


def test_zuogong_forward_zhi_yong():
    chart = chart_from_pillars(["壬子", "壬寅", "庚辰", "甲申"], "乾")
    cands = build_duan_zuogong_candidates(chart, build_relation_graph(chart))
    zhi = [c for c in cands if c.mode == "制用" and c.members == ("D.s", "H.s")]
    assert {c.relation_kind for c in zhi} == {"ke", "stem_chong"}   # 庚甲既克且冲，各列一条
    hit = next(c for c in zhi if c.relation_kind == "ke")
    assert hit.actor == "D.s"
    assert hit.ten_gods == ("日主", "偏财")
    layer1 = next(b for b in hit.binzhu if b.layer == 1)
    assert layer1.direction == "正向"
    assert hit.distance == 1


def test_zuogong_kaishan_1342_sha_sheng_yin_and_zihe():
    chart = chart_from_pillars(["壬子", "壬寅", "庚辰", "辛巳"], "乾")
    graph = build_relation_graph(chart)
    cands = build_duan_zuogong_candidates(chart, graph)

    hua = next(c for c in cands if c.mode == "化用" and c.members == ("H.b", "D.b"))
    assert hua.ten_gods == ("七杀", "偏印") and hua.actor == "H.b"
    by_layer = {b.layer: b.direction for b in hua.binzhu}
    assert by_layer[2] == "正向"         # 日柱为主，辰印在主位、巳杀在宾位
    assert by_layer[3] == "同在主位"

    he = next(c for c in cands if c.mode == "合用" and c.relation_kind == "ganzhi_zihe")
    assert he.members == ("H.s", "H.b") and he.edge_id is not None
    assert he.tiyong == ("体", "用")
    assert edge_by_id(graph, he.edge_id).attrs["branch_controls_stem"] is True


def test_zuogong_candidates_carry_no_layer_or_grade():
    chart = chart_from_pillars(["壬子", "壬寅", "庚辰", "辛巳"], "乾")
    for c in build_duan_zuogong_candidates(chart, build_relation_graph(chart)):
        d = c.to_dict()
        assert not set(d) & {"score", "layer_count", "grade", "fugui"}
        assert c.source_refs


@pytest.mark.parametrize("pillars", [["丁卯", "己酉", "甲子", "壬申"], ["庚申", "戊寅", "壬子", "辛丑"]])
def test_zuogong_only_crosses_ti_yong(pillars):
    chart = chart_from_pillars(pillars, "乾")
    for c in build_duan_zuogong_candidates(chart, build_relation_graph(chart)):
        assert set(c.tiyong) not in ({"体"}, {"用"})
