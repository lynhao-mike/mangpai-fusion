"""StrengthFacts 原子能量事实层测试。"""
from __future__ import annotations

import json
from dataclasses import fields

import pytest

from engine.facts import chart_from_pillars
from engine.facts.strength_facts import build_strength_facts, relation_to
from engine.facts.types import StrengthFacts
from engine.predicates.types import ZHI_CANGGAN_TABLE

C001 = ["庚申", "戊寅", "壬子", "辛丑"]          # 壬日寅月


def _sf(pillars, gender="乾") -> StrengthFacts:
    return build_strength_facts(chart_from_pillars(pillars, gender))


def test_relation_to_direction():
    assert relation_to("水", "金") == "生我"
    assert relation_to("水", "木") == "我生"
    assert relation_to("水", "火") == "我克"
    assert relation_to("水", "土") == "克我"
    assert relation_to("水", "水") == "同我"


def test_day_master_month_facts():
    sf = _sf(C001)
    dm = sf.day_master
    assert (dm.addr, dm.char, dm.wuxing) == ("D.s", "壬", "水")
    assert dm.month_changsheng == "病"                    # 壬在寅
    assert dm.month_main_qi_relation == "我生"            # 寅本气甲木
    assert dm.siling is None
    assert set(sf.stems) == {"Y.s", "M.s", "H.s"}


def test_tou_same_wuxing_never_includes_own_pillar():
    # 丙日、月干也是丙：日主只能看到月干，月干也只能看到日干，绝不看到自己
    sf = _sf(["甲子", "丙寅", "丙寅", "庚寅"])
    assert sf.day_master.tou_same_wuxing == ("M.s",)
    assert sf.stems["M.s"].tou_same_wuxing == ("D.s",)
    sf2 = _sf(["丙寅", "庚寅", "丙子", "戊子"])
    assert sf2.stems["Y.s"].tou_same_wuxing == ("D.s",)
    assert sf2.day_master.tou_same_wuxing == ("Y.s",)
    for facts in [sf2.day_master, *sf2.stems.values()]:
        assert facts.addr not in facts.tou_same_wuxing
    # 旧 bug 场景：非日干且全盘无同五行他干 → 必须为空
    assert _sf(C001).stems["M.s"].tou_same_wuxing == ()   # 戊：其余天干庚壬辛无土


def test_roots_and_resource_are_separate():
    sf = _sf(C001)
    dm = sf.day_master
    root_set = {(r.addr, r.hidden_char) for r in dm.roots}
    res_set = {(r.addr, r.hidden_char) for r in dm.resource_in_branches}
    assert root_set == {("Y.b", "壬"), ("D.b", "癸"), ("H.b", "癸")}
    assert res_set == {("Y.b", "庚"), ("H.b", "辛")}
    assert root_set.isdisjoint(res_set)
    assert all(r.distance == abs(["Y.b", "M.b", "D.b", "H.b"].index(r.addr) - 2) for r in dm.roots)
    assert dm.tou_resource == ("Y.s", "H.s")              # 庚、辛透干生壬


def test_root_changsheng_follows_profile():
    dm = _sf(C001).day_master
    assert {r.addr: r.changsheng for r in dm.roots} == {"Y.b": "长生", "D.b": "帝旺", "H.b": "衰"}


def _expected_layer(pillars, wanted, include_day_stem):
    counts = {"stems": 0, "main_qi": 0, "mid_qi": 0, "residual_qi": 0}
    field = {"主气": "main_qi", "中气": "mid_qi", "余气": "residual_qi"}
    for i, gz in enumerate(pillars):
        if (include_day_stem or i != 2) and wanted(gz[0]):
            counts["stems"] += 1
        for g, t, _ in ZHI_CANGGAN_TABLE[gz[1]]:
            if wanted(g):
                counts[field[t]] += 1
    return counts


def test_counts_are_plain_integers_without_discount():
    sf = _sf(C001)
    for layered in [*sf.camp_counts.values(), *sf.climate.wuxing_layered.values()]:
        for f in ("stems", "main_qi", "mid_qi", "residual_qi"):
            assert isinstance(getattr(layered, f), int)
    water = sf.climate.wuxing_layered["水"]
    # 壬(D.s) + 申中壬(中气) + 子中癸(本气) + 丑中癸(中气)
    assert (water.stems, water.main_qi, water.mid_qi, water.residual_qi) == (1, 1, 2, 0)
    earth = sf.climate.wuxing_layered["土"]
    # 戊(M.s) + 申中戊(余气) + 寅中戊(余气) + 丑中己(本气)
    assert (earth.stems, earth.main_qi, earth.mid_qi, earth.residual_qi) == (1, 1, 0, 2)
    assert sf.climate.wuxing_layered["木"].month_main_qi is True


def test_camp_counts_match_independent_tally():
    pillars = ["丙戌", "庚子", "乙亥", "辛巳"]
    sf = _sf(pillars)
    from engine.predicates.types import GAN_TO_WUXING
    camps = {"印比": {"同我", "生我"}, "食伤": {"我生"}, "财": {"我克"}, "官杀": {"克我"},
             "比劫": {"同我"}, "印": {"生我"}}
    for name, rels in camps.items():
        exp = _expected_layer(pillars, lambda g, r=rels: relation_to("木", GAN_TO_WUXING[g]) in r, False)
        got = sf.camp_counts[name]
        assert (got.stems, got.main_qi, got.mid_qi, got.residual_qi) == tuple(exp.values()), name
    # 印比 = 比劫 + 印，逐层相加
    for f in ("stems", "main_qi", "mid_qi", "residual_qi"):
        assert getattr(sf.camp_counts["印比"], f) == getattr(sf.camp_counts["比劫"], f) + getattr(sf.camp_counts["印"], f)


def test_climate_season_earth_and_tiaohou():
    sf = _sf(["甲辰", "乙亥", "丁丑", "丁未"])
    cl = sf.climate
    assert (cl.month_branch, cl.season) == ("亥", "冬")
    assert cl.dry_earth == ("H.b",) and cl.wet_earth == ("Y.b", "D.b")
    th = cl.tiaohou_lookup
    assert th is not None and th.day_stem == "丁" and th.month_branch == "亥"
    assert th.listed_stems and th.source_ref.startswith("sources/ziping/穷通宝鉴")
    for stem, addrs in th.present.items():
        assert stem in th.listed_stems
        for a in addrs:
            assert a.endswith(".s") or a.endswith(".b")
    assert "Y.s" in th.present.get("甲", ())               # 甲透年干


def test_tiaohou_degrades_to_none_without_table(monkeypatch):
    from engine.facts import strength_facts
    monkeypatch.setattr(strength_facts, "load_qiongtong", lambda: None)
    assert strength_facts.build_strength_facts(chart_from_pillars(C001, "乾")).climate.tiaohou_lookup is None


def test_yin_day_master_variants_capture_changsheng_diff():
    # 乙日寅月：阴逆 乙在寅为 帝旺；从阳（甲）为 临官
    sf = _sf(["甲子", "丙寅", "乙卯", "己卯"])
    assert sf.day_master.month_changsheng == "帝旺"
    v = [v for v in sf.variants if v.axis == "yin_changsheng"]
    assert len(v) == 1 and v[0].alt_value == "yin_same_as_yang"
    diffs = dict(v[0].diffs)
    assert diffs["/day_master/month_changsheng"] == "临官"
    assert any(p.startswith("/day_master/roots/") and p.endswith("/changsheng") for p in diffs)


def test_yang_day_master_has_no_diff_on_day_master_path():
    sf = _sf(C001)
    for v in sf.variants:
        assert not any(path.startswith("/day_master/") for path, _ in v.diffs)


def test_no_scores_or_verdicts_in_output():
    banned = {"score", "verdict", "偏旺", "偏弱", "中和", "旺衰", "cold_warm", "dry_wet", "weight"}
    payload = _sf(C001).to_dict()
    payload.pop("schema_version")
    text = json.dumps(payload, ensure_ascii=False)
    for word in banned:
        assert word not in text, word
    assert not any(isinstance(getattr(x, f.name), float)
                   for x in [_sf(C001).day_master] for f in fields(x))


@pytest.mark.parametrize("pillars", [C001, ["甲辰", "乙亥", "丁丑", "丁未"], ["戊辰", "己未", "己丑", "丁卯"]])
def test_json_serializable(pillars):
    json.dumps(_sf(pillars).to_dict(), ensure_ascii=False)


# ── 旧 predicates/strength.py 修复回归 ───────────────────────────────────────

def _bazi(pillars):
    from engine.predicates.types import Bazi, GanZhi, _default_canggan_for
    b = Bazi(*(GanZhi.parse(p) for p in pillars))
    b.藏干 = _default_canggan_for(b)
    return b


def test_legacy_is_dewang_no_longer_self_supports():
    from engine.predicates.strength import is_dewang
    b = _bazi(C001)
    assert not is_dewang("戊", b)        # 旧实现恒 True
    assert not is_dewang("壬", b)
    assert is_dewang("庚", b)            # 辛同金


def test_legacy_wuxing_strength_no_double_discount():
    from engine.predicates.strength import calc_wuxing_strength
    raw = calc_wuxing_strength(_bazi(["甲子", "丙子", "甲子", "甲子"]))
    # 天干 甲3 丙1；子仅本气癸，月支 ×1.5：水 = 1+1.5+1+1 = 4.5；木 3；火 1 → 合计 8.5
    assert raw["水"] == pytest.approx(4.5 / 8.5)
    raw2 = calc_wuxing_strength(_bazi(["甲寅", "丙寅", "甲寅", "丙寅"]))
    # 寅：甲本 1.0 / 丙中 0.3 / 戊余 0.2（只乘一次）；月支 ×1.5
    wood = 2 + (1 + 1.5 + 1 + 1)
    fire = 2 + 0.3 * (1 + 1.5 + 1 + 1)
    earth = 0.2 * (1 + 1.5 + 1 + 1)
    assert raw2["土"] == pytest.approx(earth / (wood + fire + earth))


def test_legacy_gan_strength_counts_resource_not_self():
    from engine.predicates.strength import calc_gan_strength
    b = _bazi(C001)
    # 壬：不得令；得地（子帝旺）+0.30；其余天干无水；庚辛生水 +0.30
    assert calc_gan_strength("壬", b) == pytest.approx(0.60)
