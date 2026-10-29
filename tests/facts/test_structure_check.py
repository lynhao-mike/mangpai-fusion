"""StructureCheck 第 4 层：目录驱动的构成要件核对 + 段派做功候选。"""
from __future__ import annotations

from dataclasses import fields

import pytest

from engine.facts import build_relation_graph, build_strength_facts, chart_from_pillars
from engine.facts.chart_facts import wuxing_relation
from engine.facts.relation_graph import edge_by_id, muku_at
from engine.facts.structure_check import (
    CheckItem,
    StructureCheck,
    build_duan_zuogong_candidates,
    check_structure,
    check_structures,
    load_structures,
    tiyong_view,
)
from engine.predicates.types import GAN_TO_WUXING, ZHI_TO_WUXING

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

    hua = next(c for c in cands if c.mode == "化用" and c.members == ("D.b", "H.b"))
    assert hua.ten_gods == ("偏印", "七杀") and hua.actor == "D.b"   # T-181：actor=化者（辰，受生端）
    by_layer = {b.layer: b.direction for b in hua.binzhu}
    assert by_layer[2] == "正向"         # 日柱为主，辰印（化者）在主位、巳杀（被化者）在宾位
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
def test_zuogong_includes_body_body_t179(pillars):
    """T-179 ①：体-体关系不再被丢（ADR-007 D1 的同体用过滤被 T-179 取代，不是放宽断言）。"""
    chart = chart_from_pillars(pillars, "乾")
    cands = build_duan_zuogong_candidates(chart, build_relation_graph(chart))
    assert cands
    body_body = [c for c in cands if tuple(c.tiyong) == ("体", "体")]
    assert body_body, "体-体候选必须在（体-体不再被过滤）"
    assert all(len(c.members) == 2 for c in body_body)


def test_zuogong_includes_dual_dual_t179():
    """T-179 ①：双属-双属关系不再被丢（ADR-007 D1 的双属过滤被 T-179 取代）。"""
    chart = chart_from_pillars(["甲子", "丙寅", "丙辰", "戊戌"], "乾")
    cands = build_duan_zuogong_candidates(chart, build_relation_graph(chart))
    assert cands
    dual_dual = [c for c in cands if tuple(c.tiyong) == ("双属", "双属")]
    assert dual_dual, "双属-双属候选必须在（双属不再被过滤）"
    assert any(c.mode == "制用" and c.relation_kind == "chong" for c in dual_dual)


# ── T-179 ②：同柱 / 相邻柱「生」进入候选 ──────────────────────────────────────

def test_zuogong_same_and_adjacent_sheng_as_directed_candidates():
    """T-179 ②：同柱/相邻柱相生生成 mode="sheng"，actor=生者、members[1]=被生者。"""
    chart = chart_from_pillars(["壬子", "壬寅", "庚辰", "辛巳"], "乾")
    cands = build_duan_zuogong_candidates(chart, build_relation_graph(chart))

    adjacent = next(c for c in cands if c.mode == "sheng" and c.members == ("H.b", "D.b"))
    assert adjacent.relation_kind == "sheng"
    assert adjacent.actor == "H.b"            # 巳火生辰土
    assert adjacent.chars == ("巳", "辰")
    assert adjacent.distance == 1
    assert adjacent.edge_id is None           # 关系图不建地支生边

    same = next(c for c in cands if c.mode == "sheng" and c.members == ("M.s", "M.b"))
    assert same.actor == "M.s"                # 壬水生日支寅木
    assert same.chars == ("壬", "寅")
    assert same.distance == 0


def test_zuogong_sheng_not_generated_beyond_adjacent_pillars():
    """T-179 ②：跨柱两柱以上不新增 mode="sheng"（既有 sheng(main_qi) 远距离分支保留）。"""
    chart = chart_from_pillars(["庚申", "戊寅", "壬子", "辛丑"], "乾")
    cands = build_duan_zuogong_candidates(chart, build_relation_graph(chart))
    assert all((c.distance or 0) <= 1 for c in cands if c.mode == "sheng")
    # 申（年支）生子（日支）跨两柱：只保留既有 sheng(main_qi) 推得，不新增 mode="sheng"
    assert not any(c.mode == "sheng" and c.members == ("Y.b", "D.b") for c in cands)
    assert any(c.relation_kind == "sheng(main_qi)" and c.members == ("Y.b", "D.b") for c in cands)


@pytest.mark.parametrize("pillars", [["甲子", "丙寅", "丙辰", "戊戌"], ["庚申", "戊寅", "壬子", "辛丑"]])
def test_zuogong_branch_ke_candidate_without_branch_ke_edge(pillars):
    """T-183 取代 T-179 的「不生成支克候选」约束：关系图仍不建支克边（G3 不变），
    但按本气五行推得 `zhi_ke` 候选，actor=克方、members=(克方,被克方)、edge_id=None。
    """
    chart = chart_from_pillars(pillars, "乾")
    graph = build_relation_graph(chart)
    pillar_index = {head: i for i, head in enumerate("YMDH")}
    branch_addrs = {p.branch.addr for p in chart.pillars}
    ke_pairs = [(p.branch.char, q.branch.char) for p in chart.pillars for q in chart.pillars
                if p.index != q.index
                and wuxing_relation(ZHI_TO_WUXING[p.branch.char], ZHI_TO_WUXING[q.branch.char]) == "克"]
    assert ke_pairs, "该盘地支五行应有克对（否则本测试无判别力）"
    assert not [e for e in graph.edges if e.kind == "ke" and set(e.members) <= branch_addrs]

    cands = build_duan_zuogong_candidates(chart, graph)
    zhi_ke = [c for c in cands if c.relation_kind == "zhi_ke"]
    assert zhi_ke, "本气五行有克对时必须出 zhi_ke 候选"
    for cand in zhi_ke:
        assert cand.mode == "制用" and cand.edge_id is None
        assert cand.actor == cand.members[0]
        assert set(cand.members) <= branch_addrs
        assert wuxing_relation(ZHI_TO_WUXING[cand.chars[0]], ZHI_TO_WUXING[cand.chars[1]]) == "克"
        assert cand.distance == abs(pillar_index[cand.members[0][0]] - pillar_index[cand.members[1][0]])
    # 同对已有冲/刑/合边候选时仍各列一条（T-179「既克且冲各列一条」约定延续），不合并、不去重
    assert [c for c in zhi_ke if any(o is not c and set(o.members) == set(c.members) for o in cands)]


def test_zuogong_gan_ke_zhi_candidate_all_pairs():
    """T-183：天干克地支（含同柱盖头）推得 `gan_ke_zhi` 候选，actor=天干、不建边。"""
    chart = chart_from_pillars(["乙巳", "戊子", "丁巳", "庚戌"], "坤")
    graph = build_relation_graph(chart)
    cands = build_duan_zuogong_candidates(chart, graph)
    gan_ke = [c for c in cands if c.relation_kind == "gan_ke_zhi"]
    assert gan_ke
    for cand in gan_ke:
        assert cand.mode == "制用" and cand.edge_id is None
        assert cand.actor == cand.members[0]
        assert cand.members[0].endswith(".s") and cand.members[1].endswith(".b")
        assert wuxing_relation(GAN_TO_WUXING[cand.chars[0]], ZHI_TO_WUXING[cand.chars[1]]) == "克"
    same_pillar = next(c for c in gan_ke if c.members == ("M.s", "M.b"))
    assert same_pillar.chars == ("戊", "子") and same_pillar.distance == 0    # 同柱盖头


def test_zuogong_ke_candidate_precedes_wuhe_for_same_pair_t183():
    """T-183：同一对天干既有 ke 又有 wuhe 时，ke 候选排在 wuhe 前（不去重、不改 edges）。"""
    chart = chart_from_pillars(["丙午", "辛卯", "丁卯", "壬子"], "乾")
    graph = build_relation_graph(chart)
    cands = build_duan_zuogong_candidates(chart, graph)
    pair = {"Y.s", "M.s"}                      # 丙辛：ke e002（丙）与 wuhe e001 同 members
    same = [c for c in cands if set(c.members) == pair]
    assert [c.relation_kind for c in same] == ["ke", "wuhe"]
    assert same[0].actor == "Y.s" and same[0].chars == ("丙", "辛") and same[0].edge_id == "e002"
    assert same[1].actor is None               # 合仍无向（T-178 契约保持）
    assert {e.kind for e in graph.edges if set(e.members) == pair} == {"ke", "wuhe"}


def test_zuogong_muku_actor_is_ku_t179():
    """T-178 审计：墓用候选 members=(库, 入库方)、actor=库；relations.muku 事实层不动。"""
    chart = chart_from_pillars(["庚申", "戊寅", "壬子", "辛丑"], "乾")
    graph = build_relation_graph(chart)
    cands = build_duan_zuogong_candidates(chart, graph)
    mu = next(c for c in cands if c.mode == "墓用" and "Y.s" in c.members)
    assert mu.members == ("H.b", "Y.s")        # 丑库 → 庚金
    assert mu.actor == "H.b"
    assert mu.chars == ("丑", "庚")
    assert "Y.s" in {c.addr for c in muku_at(graph, "H.b").candidates}


# ── T-181：化用候选 actor=化者（受生端），只翻化用 ─────────────────────────────

_HUA_CASES = [
    ("P1-H09", ["癸巳", "乙卯", "己巳", "己巳"], {
        (("Y.b", "M.b"), "Y.b"),
        (("D.b", "M.b"), "D.b"),
        (("H.b", "M.b"), "H.b"),
    }),
    ("P1-H10", ["戊午", "戊午", "戊午", "甲寅"], {
        (("Y.b", "H.b"), "Y.b"),
        (("M.b", "H.b"), "M.b"),
        (("D.b", "H.b"), "D.b"),
    }),
    ("P1-H11", ["乙巳", "己丑", "庚午", "庚辰"], {
        (("M.b", "Y.b"), "M.b"),
        (("H.b", "Y.b"), "H.b"),
        (("M.b", "D.b"), "M.b"),
        (("H.b", "D.b"), "H.b"),
    }),
]


@pytest.mark.parametrize("case_id,pillars,expected", _HUA_CASES)
def test_hua_candidate_actor_is_hua_zhe_t180_fixture(case_id, pillars, expected):
    """T-180 审计 fixture：P1-H09 巳化卯 / H10 午化寅 / H11 辰化巳，化者=受生端。

    契约：化用候选 members=(化者, 被化者)、actor=化者；被化者（生端）生入化者（受生端）。
    """
    chart = chart_from_pillars(pillars, "乾")
    cands = build_duan_zuogong_candidates(chart, build_relation_graph(chart))
    hua = [c for c in cands if c.mode == "化用"]
    assert {(c.members, c.actor) for c in hua} == expected
    for c in hua:
        assert c.actor == c.members[0]                              # 化用 actor=members[0]=化者
        assert wuxing_relation(ZHI_TO_WUXING[c.chars[1]], ZHI_TO_WUXING[c.chars[0]]) == "生", (
            f"{case_id} {c.chars}: 被化者必须生入化者（化者=受生端）"
        )
        assert c.ten_gods[0] in {"正印", "偏印"} and c.ten_gods[1] in {"正官", "七杀"}


def test_h12_cai_sha_hua_known_gap():
    """known_gap · P1-H12（乙巳 乙酉 戊子 甲寅）：财子水被寅化，化者=寅（受生端），引擎不识别。

    T-180 §3.2/§6.3：化用谓词只认官杀→印，财→杀 不在其内；本条只有 mode=生泄用、
    actor=子（生者=被化者，方向仍是 reversed）。T-181 不扩类，缺口留给另卡。
    """
    chart = chart_from_pillars(["乙巳", "乙酉", "戊子", "甲寅"], "乾")
    cands = build_duan_zuogong_candidates(chart, build_relation_graph(chart))
    assert not [c for c in cands if c.mode == "化用" and set(c.members) == {"D.b", "H.b"}]
    sheng = next(c for c in cands if c.mode == "生泄用" and c.members == ("D.b", "H.b"))
    assert sheng.chars == ("子", "寅") and sheng.ten_gods == ("正财", "七杀")
    assert sheng.actor == "D.b"        # 生者=子=被化者；化者寅未被识别（known_gap，不扩类）


def test_hua_flip_does_not_touch_sheng_or_shengxie_t181():
    """T-181：只翻 mode=化用；sheng / 生泄用 的 actor 仍是生者（规则表 §4.7），不得全局翻。

    同一对 巳→辰 同时以化用（actor=辰=化者）与生（actor=巳=生者）出现，正好区分两套约定。
    """
    chart = chart_from_pillars(["壬子", "壬寅", "庚辰", "辛巳"], "乾")
    cands = build_duan_zuogong_candidates(chart, build_relation_graph(chart))
    hua = next(c for c in cands if c.mode == "化用" and set(c.members) == {"D.b", "H.b"})
    sheng = next(c for c in cands if c.mode == "sheng" and c.members == ("H.b", "D.b"))
    sheng_qi = next(c for c in cands if c.mode == "生泄用" and c.members == ("M.s", "M.b"))
    assert hua.members == ("D.b", "H.b") and hua.actor == "D.b"        # 化者=辰（受生端）
    assert sheng.chars == ("巳", "辰") and sheng.actor == "H.b"         # 生者=巳
    assert sheng_qi.chars == ("壬", "寅") and sheng_qi.actor == "M.s"   # 生者=壬
