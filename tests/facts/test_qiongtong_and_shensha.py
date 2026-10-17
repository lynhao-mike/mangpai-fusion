"""WP-6A：穷通 120 条调候表与独立神煞算子。"""
from __future__ import annotations

from engine.facts.chart_facts import chart_from_pillars, hour_stem_for, month_stem_for
from engine.facts.shensha import build_shensha_facts, find_shensha
from engine.facts.strength_facts import build_strength_facts, load_qiongtong, lookup_tiaohou

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "寅卯辰巳午未申酉戌亥子丑"


def _chart(day_stem: str, month_branch: str, *, day_branch: str | None = None, hour_branch: str = "亥"):
    year_stem, year_branch = "甲", "子"
    month_stem = month_stem_for(year_stem, month_branch)
    if day_branch is None:
        day_branch = "子" if day_stem in set("甲丙戊庚壬") else "丑"
    hour_stem = hour_stem_for(day_stem, hour_branch)
    return chart_from_pillars(
        [
            f"{year_stem}{year_branch}",
            f"{month_stem}{month_branch}",
            f"{day_stem}{day_branch}",
            f"{hour_stem}{hour_branch}",
        ],
        "乾",
    )


def test_qiongtong_table_has_120_entries_with_source_ref():
    table = load_qiongtong()
    assert table is not None
    entries = table["entries"]
    assert set(entries) == set(STEMS)
    for stem in STEMS:
        assert set(entries[stem]) == set(BRANCHES), stem
        for branch in BRANCHES:
            item = entries[stem][branch]
            assert item["listed_stems"], f"{stem}{branch} listed_stems 为空"
            assert all(s in STEMS for s in item["listed_stems"])
            ref = item["source_ref"]
            assert ref.startswith("sources/ziping/穷通宝鉴")
            assert ":" in ref


def test_tiaohou_lookup_never_none_for_any_day_stem_month_branch():
    for stem in STEMS:
        for month in BRANCHES:
            chart = _chart(stem, month)
            hit = lookup_tiaohou(chart)
            assert hit is not None, f"{stem}日 {month}月"
            assert hit.day_stem == stem and hit.month_branch == month
            assert hit.listed_stems and hit.source_ref
            climate = build_strength_facts(chart).climate.tiaohou_lookup
            assert climate is not None
            assert climate.listed_stems == hit.listed_stems


def test_build_shensha_facts_returns_non_empty_hits_with_trace():
    chart = chart_from_pillars(["庚申", "戊寅", "壬子", "辛丑"], "乾")
    facts = build_shensha_facts(chart)
    assert facts.hits == find_shensha(chart)
    assert facts.hits
    for hit in facts.hits:
        assert hit.name and hit.anchor_addr and hit.target_addr
        assert hit.method_note and hit.source_ref


def test_core_shensha_tables_cover_taiji_wenchang_jinyu_lu_and_day_sha():
    c001 = find_shensha(chart_from_pillars(["庚申", "戊寅", "壬子", "辛丑"], "乾"))
    assert any(h.name == "金舆" and h.anchor_addr == "D.s" and h.target_addr == "H.b" for h in c001)
    assert any(h.name == "文昌" and h.anchor_addr == "D.s" and h.target_addr == "M.b" for h in c001)
    assert any(h.name == "太极贵人" and h.anchor_addr == "D.s" and h.target_addr == "Y.b" for h in c001)

    lu_chart = chart_from_pillars(["甲子", "乙亥", "壬寅", "丙午"], "乾")
    assert any(
        h.name == "禄神" and h.anchor_addr == "D.s" and h.target_addr == "M.b"
        for h in find_shensha(lu_chart)
    )

    yincha = find_shensha(chart_from_pillars(["甲子", "丙寅", "丙子", "丁酉"], "乾"))
    assert any(h.name == "阴差阳错" and h.anchor_addr == "D" and h.target_addr == "D" for h in yincha)

    dabai = find_shensha(chart_from_pillars(["乙丑", "戊子", "甲辰", "丁卯"], "乾"))
    assert any(h.name == "十恶大败" and h.anchor_addr == "D" and h.target_addr == "D" for h in dabai)
