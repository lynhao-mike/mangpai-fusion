"""任付红《地支四墓库的使用方法》原文例盘黄金测试。

每个用例只断言原文作者分析时引用到的客观事实能被 地址 + 边 id + 细则出处 精确定位，
并断言作者明确排除的情形没有被误标为入墓。出处：
sources/ren/MinerU_markdown_16、任付红-民间实用八字-地支四墓库的使用方法_2056026785004060672.md
"""
from __future__ import annotations

import pytest

from engine.facts import build_relation_graph, chart_from_pillars, edge_by_id, edges_between, muku_at
from engine.facts.types import MukuCandidate, MukuFact, RelationGraph

REN = "sources/ren/MinerU_markdown_16、任付红-民间实用八字-地支四墓库的使用方法_2056026785004060672.md"


def _graph(pillars: list[str], gender: str, **kw) -> RelationGraph:
    return build_relation_graph(chart_from_pillars(pillars, gender), **kw)


def _cand(muku: MukuFact, addr: str) -> MukuCandidate:
    found = [c for c in muku.candidates if c.addr == addr]
    assert len(found) == 1, f"{muku.addr} 中应有且只有一个 {addr} 候选：{[c.addr for c in muku.candidates]}"
    return found[0]


def _effects(c: MukuCandidate) -> set[str]:
    return {h.effect for h in c.rule_hits}


def _refs(c: MukuCandidate) -> set[str]:
    return {h.source_ref for h in c.rule_hits}


def _kind_ids(graph: RelationGraph, ids: tuple[str, ...]) -> set[str]:
    return {edge_by_id(graph, i).kind for i in ids}


def _single_edge(graph: RelationGraph, kind: str, *addrs: str):
    found = [e for e in edges_between(graph, *addrs) if e.kind == kind]
    assert len(found) == 1, f"{addrs} 之间应有一条 {kind} 边：{[e.kind for e in edges_between(graph, *addrs)]}"
    return found[0]


def test_case1_hai_enters_chen_and_chen_not_opened():
    """乾 甲辰 乙亥 丁丑 丁未：亥见辰入墓库，墓库不开；己卯运亥卯未三合局穿辰墓（:31-35）。"""
    g = _graph(["甲辰", "乙亥", "丁丑", "丁未"], "乾")
    chen = muku_at(g, "Y.b")
    assert set(chen.ku_of) == {"水", "土"}
    hai = _cand(chen, "M.b")
    assert hai.char_class == "四生支" and _effects(hai) == {"入墓"}
    assert f"{REN}:29" in _refs(hai)
    assert chen.openers == (), "原文：墓库不开"
    # 丑未辰齐见：丑未相冲，丑未都不论入辰墓（第五条）
    for addr in ("D.b", "H.b"):
        c = _cand(chen, addr)
        assert c.excluded and "不论入墓" in _effects(c)

    g4 = _graph(["甲辰", "乙亥", "丁丑", "丁未"], "乾", dayun_index=4)
    assert dict(g4.nodes)["DY4.b"] == "卯"
    full = [e for e in g4.edges if e.kind == "sanhe" and e.completeness == "full"]
    assert [e.members for e in full] == [("M.b", "DY4.b", "H.b")]
    chuan = _single_edge(g4, "chuan", "Y.b", "DY4.b")
    assert chuan.scope == "dayun"
    assert chuan.id in muku_at(g4, "Y.b").chuan_po


def test_case2_si_enters_xu_and_xu_bound_by_month_mao():
    """乾 丁酉 癸卯 癸巳 壬戌：巳见戌则入库，戌又被月令卯木合住（:51-57）。"""
    g = _graph(["丁酉", "癸卯", "癸巳", "壬戌"], "乾")
    xu = muku_at(g, "H.b")
    si = _cand(xu, "D.b")
    assert si.char_class == "四生支" and _effects(si) == {"入墓"} and not si.excluded
    he = _single_edge(g, "liuhe", "M.b", "H.b")
    assert he.chars == ("卯", "戌") and he.distance == 2 and he.between == ("D.b",)
    assert he.id in xu.binders
    assert xu.openers == ()


def test_case3_zi_gong_ju_but_damaged_by_wei_chuan_and_mao_po():
    """坤 乙卯 戊子 戊辰 己未：子辰拱局，但未穿子、卯子破，子水受伤当作入辰墓看（:63-69）。"""
    g = _graph(["乙卯", "戊子", "戊辰", "己未"], "坤")
    chen = muku_at(g, "D.b")
    zi = _cand(chen, "M.b")
    assert zi.char_class == "四正支"
    assert _effects(zi) == {"一般作拱局"} and f"{REN}:61" in _refs(zi)
    assert zi.requires_judgment, "极弱（受伤）与否必须交给调用方判断"
    link = edge_by_id(g, zi.ku_link_edges[0])
    assert link.kind == "sanhe" and link.completeness == "half_mu"
    wei_chuan = _single_edge(g, "chuan", "M.b", "H.b")
    mao_po = _single_edge(g, "po", "Y.b", "M.b")
    assert "duan" in mao_po.attrs["systems"]
    assert {wei_chuan.id, mao_po.id} <= set(zi.damaged_by_edges)
    # 天干戊辰、戊子不应被当作入墓
    assert all(c.addr not in ("M.s", "D.s") or c.excluded for c in chen.candidates)


def test_case4_water_many_enters_chen_and_chen_chong_xu():
    """乾 壬子 壬子 壬辰 庚戌：原局水多入辰库，辰冲制戌财库（:75-79）。"""
    g = _graph(["壬子", "壬子", "壬辰", "庚戌"], "乾")
    chen = muku_at(g, "D.b")
    for addr in ("Y.s", "M.s", "Y.b", "M.b"):
        c = _cand(chen, addr)
        assert "入墓" in _effects(c) and f"{REN}:73" in _refs(c)
        assert c.same_wuxing_count == 5
    # 日柱壬辰：壬坐本五行墓，第四条不论入墓
    assert chen.self_sit_excluded == ("D.s",)
    assert _cand(chen, "D.s").excluded
    chong = _single_edge(g, "chong", "D.b", "H.b")
    assert chong.id in chen.openers and chong.id in muku_at(g, "H.b").openers


def test_case5_wood_many_enters_wei_and_ding_ren_he_controls_wei():
    """乾 丙寅 庚寅 壬寅 丁未：寅木三个见未为木多入墓库；日主壬合丁，控制住未（:89-93）。

    丁为火、未为木库，丁坐未不是坐本五行之墓，因此不属于第四条"天干坐墓"，
    self_sit_excluded 应为空；"控制住未"由时柱天干参与的丁壬五合边表达。
    """
    g = _graph(["丙寅", "庚寅", "壬寅", "丁未"], "乾")
    wei = muku_at(g, "H.b")
    for addr in ("Y.b", "M.b", "D.b"):
        c = _cand(wei, addr)
        assert c.char_class == "四生支" and _effects(c) == {"入墓"} and c.same_wuxing_count == 3
    assert wei.self_sit_excluded == ()
    he = _single_edge(g, "wuhe", "D.s", "H.s")
    assert he.attrs["huashen"] == "木" and he.distance == 1
    assert wei.stem_he_on_pillar == (he.id,)


def test_case6a_wei_enters_chen_and_yi_sitting_wei_excluded():
    """乾 丙辰 甲午 乙未 戊寅：寅木劫财入未库，未又入年上辰库；乙未一柱乙不以入墓看（:107、:113-117）。"""
    g = _graph(["丙辰", "甲午", "乙未", "戊寅"], "乾")
    wei_into_chen = _cand(muku_at(g, "Y.b"), "D.b")
    assert _effects(wei_into_chen) == {"入墓"} and f"{REN}:111" in _refs(wei_into_chen)
    wei = muku_at(g, "D.b")
    assert "入墓" in _effects(_cand(wei, "H.b"))
    assert wei.self_sit_excluded == ("D.s",)
    yi = _cand(wei, "D.s")
    assert yi.excluded and f"{REN}:107" in _refs(yi)


def test_case6b_chou_wei_chong_so_neither_enters_chen():
    """乾 戊辰 己未 己丑 丁卯：因有未丑之冲，丑未都不入辰库（:133-137）。"""
    g = _graph(["戊辰", "己未", "己丑", "丁卯"], "乾")
    chen = muku_at(g, "Y.b")
    for addr in ("M.b", "D.b"):
        c = _cand(chen, addr)
        assert c.excluded
        assert any("丑未冲" in h.rule and h.source_ref == f"{REN}:111" for h in c.rule_hits)
    chong = _single_edge(g, "chong", "M.b", "D.b")
    assert set(_kind_ids(g, _cand(chen, "D.b").damaged_by_edges)) >= {"chong"}
    assert chong.id in muku_at(g, "D.b").openers


@pytest.mark.parametrize("pillars,gender", [
    (["甲辰", "乙亥", "丁丑", "丁未"], "乾"),
    (["丙辰", "甲午", "乙未", "戊寅"], "乾"),
])
def test_fire_earth_profile_drops_chou_wei_into_chen_as_variant(pillars, gender):
    """火土同宫口径下辰不作土库：丑未入辰墓的候选消失，并且只以 variants 差异呈现。"""
    g = _graph(pillars, gender)
    v = [v for v in g.variants if v.axis == "tu_jigong"]
    assert len(v) == 1 and v[0].alt_value == "fire_earth"
    assert all(path.startswith("/muku") for path, _ in v[0].diffs)
