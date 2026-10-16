"""engine/facts/strength_facts.py · 原子能量事实层 StrengthFacts（strength-facts/v1）。

合并仓库原有四套旺衰口径（predicates/strength 的加权归一、features 的无月令加权、
ten_god_profile 的月支 ×1.5、v5 ziping_runner 的 0.5 起步加减分），统一改为原子事实：

- 每个天干：月令长生、月令本气对它的生克关系、通根明细、印气明细、透干帮扶与透干印；
- 阵营与五行：按 天干 / 本气 / 中气 / 余气 分层计数，不加权、不归一化、不打折；
- 气候：月令季节、燥土与湿土所在地址、《穷通宝鉴》日干×月支原文所列用字及其在盘中的位置。

刻意不输出：旺衰总分、偏旺/中和/偏弱定性、寒暖燥湿浮点系数。
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from lunar_python import Solar

import yaml

from engine.facts.chart_facts import alternatives, changsheng, json_diff, validate_profile, wuxing_relation
from engine.facts.types import (
    Addr,
    ChartFacts,
    ClimateFacts,
    FiveRelation,
    LayeredCount,
    Pillar,
    ProfileSet,
    Root,
    SilingFact,
    StemStrengthFacts,
    StrengthFacts,
    TiaohouHit,
    Variant,
)
from engine.predicates.types import GAN_TO_WUXING, WUXING_LIST, ZHI_CANGGAN_TABLE

SCHEMA_VERSION = "strength-facts/v1"
QIONGTONG_PATH = Path(__file__).parent / "data" / "qiongtong_table.yaml"

_SEASON = {"寅": "春", "卯": "春", "辰": "春", "巳": "夏", "午": "夏", "未": "夏",
           "申": "秋", "酉": "秋", "戌": "秋", "亥": "冬", "子": "冬", "丑": "冬"}
_DRY_EARTH = frozenset("戌未")
_WET_EARTH = frozenset("辰丑")
_QI_FIELD = {"本气": "main_qi", "中气": "mid_qi", "余气": "residual_qi"}
_QI_LABEL = {"主气": "本气", "中气": "中气", "余气": "余气"}
_SILING_SEGMENTS: dict[str, tuple[tuple[str, str, str, int], ...]] = {
    "寅": (("艮土", "戊", "戊", 5), ("丙火", "丙", "丙", 5), ("甲木", "甲", "甲", 20)),
    "卯": (("甲木", "甲", "甲", 7), ("乙木", "乙", "乙", 23)),
    "辰": (("乙木", "乙", "乙", 7), ("壬水墓库", "壬", "癸", 5), ("戊土", "戊", "戊", 18)),
    "巳": (("戊土", "戊", "戊", 7), ("庚金", "庚", "庚", 5), ("丙火", "丙", "丙", 18)),
    "午": (("丙火", "丙", "丙", 7), ("丁火", "丁", "丁", 23)),
    "未": (("丁火", "丁", "丁", 7), ("甲木墓库", "甲", "乙", 5), ("己土", "己", "己", 18)),
    "申": (("坤土", "戊", "戊", 5), ("壬水", "壬", "壬", 5), ("庚金", "庚", "庚", 20)),
    "酉": (("庚金", "庚", "庚", 7), ("辛金", "辛", "辛", 23)),
    "戌": (("辛金", "辛", "辛", 7), ("丙火墓库", "丙", "丁", 5), ("戊土", "戊", "戊", 18)),
    "亥": (("戊土", "戊", "戊", 5), ("甲木", "甲", "甲", 5), ("壬水", "壬", "壬", 20)),
    "子": (("壬水", "壬", "壬", 7), ("癸水", "癸", "癸", 23)),
    "丑": (("癸水", "癸", "癸", 7), ("庚金墓库", "庚", "辛", 5), ("己土", "己", "己", 18)),
}
_REF_SILING = "sources/ziping/《三命通会》.md:14"

# 以日主为我的十神阵营（按五行关系；不分阴阳）
_CAMPS: dict[str, frozenset[str]] = {
    "印比": frozenset({"同我", "生我"}),
    "食伤": frozenset({"我生"}),
    "财": frozenset({"我克"}),
    "官杀": frozenset({"克我"}),
    "比劫": frozenset({"同我"}),
    "印": frozenset({"生我"}),
}


# ── 基础关系 ────────────────────────────────────────────────────────────────

def relation_to(me: str, other: str) -> FiveRelation:
    """站在五行 ``me`` 的立场看 ``other``：同我 / 生我 / 我生 / 我克 / 克我。"""
    rel = wuxing_relation(other, me)       # other 对 me
    return {"同": "同我", "生": "生我", "被生": "我生", "克": "克我", "被克": "我克"}[rel]  # type: ignore[return-value]


def _hidden(zhi: str) -> list[tuple[str, str]]:
    return [(g, _QI_LABEL[t]) for g, t, _ in ZHI_CANGGAN_TABLE[zhi]]


def _siling(chart: ChartFacts) -> Optional[SilingFact]:
    if chart.input.mode != "solar" or not chart.input.solar_datetime:
        return None

    birth = datetime.fromisoformat(chart.input.solar_datetime)
    lunar = Solar.fromYmdHms(
        birth.year, birth.month, birth.day, birth.hour, birth.minute, birth.second
    ).getLunar()
    jie_solar = lunar.getPrevJie().getSolar()
    jie = datetime(
        jie_solar.getYear(), jie_solar.getMonth(), jie_solar.getDay(),
        jie_solar.getHour(), jie_solar.getMinute(), jie_solar.getSecond(),
    )
    days_since_jie = (birth - jie).total_seconds() / 86400

    month = chart.pillars[1].branch.char
    elapsed = 0.0
    for source_term, commanding_stem, hidden_stem, segment_days in _SILING_SEGMENTS[month]:
        elapsed += segment_days
        if days_since_jie < elapsed:
            return SilingFact(
                month_branch=month,
                days_since_jie=days_since_jie,
                commanding_stem=commanding_stem,
                normalized_hidden_stem=hidden_stem,
                segment_days=segment_days,
                source_ref=_REF_SILING,
                source_term=source_term,
            )

    source_term, commanding_stem, hidden_stem, segment_days = _SILING_SEGMENTS[month][-1]
    return SilingFact(
        month_branch=month,
        days_since_jie=days_since_jie,
        commanding_stem=commanding_stem,
        normalized_hidden_stem=hidden_stem,
        segment_days=segment_days,
        source_ref=_REF_SILING,
        source_term=source_term,
    )


# ── 单干事实 ────────────────────────────────────────────────────────────────

def _stem_facts(chart: ChartFacts, pillar: Pillar, profile: ProfileSet) -> StemStrengthFacts:
    gan = pillar.stem.char
    wx = GAN_TO_WUXING[gan]
    month = chart.pillars[1].branch.char
    month_main = ZHI_CANGGAN_TABLE[month][0][0]

    roots: list[Root] = []
    resource: list[Root] = []
    for other in chart.pillars:
        zhi = other.branch.char
        status = changsheng(gan, zhi, profile)
        for hidden_char, qi in _hidden(zhi):
            rel = relation_to(wx, GAN_TO_WUXING[hidden_char])
            if rel not in ("同我", "生我"):
                continue
            root = Root(addr=other.branch.addr, hidden_char=hidden_char, qi=qi,  # type: ignore[arg-type]
                        changsheng=status, distance=abs(other.index - pillar.index))
            (roots if rel == "同我" else resource).append(root)

    tou_same: list[Addr] = []
    tou_res: list[Addr] = []
    for other in chart.pillars:
        if other.index == pillar.index:          # 严格排除自身所在柱
            continue
        rel = relation_to(wx, GAN_TO_WUXING[other.stem.char])
        if rel == "同我":
            tou_same.append(other.stem.addr)
        elif rel == "生我":
            tou_res.append(other.stem.addr)

    return StemStrengthFacts(
        addr=pillar.stem.addr,
        char=gan,
        wuxing=wx,
        month_changsheng=changsheng(gan, month, profile),
        month_main_qi_relation=relation_to(wx, GAN_TO_WUXING[month_main]),
        siling=_siling(chart),
        roots=tuple(roots),
        resource_in_branches=tuple(resource),
        tou_same_wuxing=tuple(tou_same),
        tou_resource=tuple(tou_res),
    )


# ── 分层计数 ────────────────────────────────────────────────────────────────

def _layered(chart: ChartFacts, wanted, *, include_day_stem: bool) -> LayeredCount:
    """``wanted(gan) -> bool``；四支藏干逐个按气位计 1，不折算。"""
    counts = {"stems": 0, "main_qi": 0, "mid_qi": 0, "residual_qi": 0}
    for p in chart.pillars:
        if (include_day_stem or p.index != 2) and wanted(p.stem.char):
            counts["stems"] += 1
        for hidden_char, qi in _hidden(p.branch.char):
            if wanted(hidden_char):
                counts[_QI_FIELD[qi]] += 1
    month_main = ZHI_CANGGAN_TABLE[chart.pillars[1].branch.char][0][0]
    return LayeredCount(**counts, month_main_qi=bool(wanted(month_main)))


def _camp_counts(chart: ChartFacts) -> dict[str, LayeredCount]:
    dm_wx = GAN_TO_WUXING[chart.day_master]
    return {
        name: _layered(chart, lambda g, rels=rels: relation_to(dm_wx, GAN_TO_WUXING[g]) in rels,
                       include_day_stem=False)
        for name, rels in _CAMPS.items()
    }


def _wuxing_layered(chart: ChartFacts) -> dict[str, LayeredCount]:
    return {wx: _layered(chart, lambda g, wx=wx: GAN_TO_WUXING[g] == wx, include_day_stem=True)
            for wx in WUXING_LIST}


# ── 调候查表 ────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def load_qiongtong() -> Optional[dict[str, Any]]:
    """读取《穷通宝鉴》日干×月支查表；文件不存在时返回 None（调用方得到 tiaohou_lookup=None）。"""
    if not QIONGTONG_PATH.exists():
        return None
    return yaml.safe_load(QIONGTONG_PATH.read_text(encoding="utf-8"))


def lookup_tiaohou(chart: ChartFacts) -> Optional[TiaohouHit]:
    table = load_qiongtong()
    if table is None:
        return None
    month = chart.pillars[1].branch.char
    entry = (table.get("entries") or {}).get(chart.day_master, {}).get(month)
    if not entry:
        return None
    listed = tuple(entry["listed_stems"])
    present: dict[str, tuple[Addr, ...]] = {}
    for stem in listed:
        addrs = [p.stem.addr for p in chart.pillars if p.stem.char == stem]
        addrs += [p.branch.addr for p in chart.pillars if stem in (h.char for h in p.branch.hidden)]
        present[stem] = tuple(addrs)
    return TiaohouHit(
        day_stem=chart.day_master, month_branch=month, listed_stems=listed, present=present,
        raw_excerpt=str(entry.get("raw_excerpt", "")), source_ref=str(entry["source_ref"]),
    )


def _climate(chart: ChartFacts) -> ClimateFacts:
    month = chart.pillars[1].branch.char
    return ClimateFacts(
        month_branch=month,
        season=_SEASON[month],  # type: ignore[arg-type]
        wuxing_layered=_wuxing_layered(chart),
        dry_earth=tuple(p.branch.addr for p in chart.pillars if p.branch.char in _DRY_EARTH),
        wet_earth=tuple(p.branch.addr for p in chart.pillars if p.branch.char in _WET_EARTH),
        tiaohou_lookup=lookup_tiaohou(chart),
    )


# ── 入口 ────────────────────────────────────────────────────────────────────

def _stem_layer(chart: ChartFacts, profile: ProfileSet) -> tuple[StemStrengthFacts, dict[Addr, StemStrengthFacts]]:
    facts = {p.stem.addr: _stem_facts(chart, p, profile) for p in chart.pillars}
    day = facts.pop("D.s")
    return day, facts


def build_strength_facts(chart: ChartFacts) -> StrengthFacts:
    """在 ChartFacts 上构造原子能量事实。

    口径差异：对 ``yin_changsheng``、``tu_jigong`` 的每个其他取值重算长生相关字段，
    只把与默认口径不同的 JSON 路径写进 ``variants``；没有差异不写。
    （当前注册的两种 tu_jigong 取值下戊己长生都随火起于寅，因此该轴通常不产生差异。）
    """
    profile = validate_profile(chart.profile)
    day, stems = _stem_layer(chart, profile)
    base = {"day_master": day.to_dict(), "stems": {k: v.to_dict() for k, v in stems.items()}}

    variants: list[Variant] = []
    for axis in ("yin_changsheng", "tu_jigong"):
        for alt in alternatives(axis, getattr(profile, axis)):
            alt_day, alt_stems = _stem_layer(chart, replace(profile, **{axis: alt}))
            other = {"day_master": alt_day.to_dict(), "stems": {k: v.to_dict() for k, v in alt_stems.items()}}
            diffs = json_diff(base, other)
            if diffs:
                variants.append(Variant(axis, alt, tuple(diffs)))

    return StrengthFacts(
        schema_version=SCHEMA_VERSION,
        chart_id=chart.chart_id,
        profile=profile,
        day_master=day,
        stems=stems,
        camp_counts=_camp_counts(chart),
        climate=_climate(chart),
        variants=tuple(variants),
    )


__all__ = ["build_strength_facts", "load_qiongtong", "lookup_tiaohou", "relation_to"]
