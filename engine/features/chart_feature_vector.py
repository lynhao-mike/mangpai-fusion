"""从 L0 命盘事实确定性构建共享命局特征向量。

本模块只产生中立、可计算信号，不裁定身强身弱，不输出流派或事件结论。
藏干能量沿用 ``ZHI_CANGGAN_TABLE`` 的主气 1.0 / 中气 0.3 / 余气 0.2。
寒暖燥湿系数是 cfv-v1 的工程默认值，用于稳定分型，不代表流派铁律。
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from itertools import combinations
from typing import Iterable

from engine.decision.models import ChartFactLedger
from engine.features.types import ChartFeatureVector
from engine.predicates.ganzhi import gan_to_wuxing, get_canggan, is_gan, is_zhi, zhi_to_wuxing
from engine.predicates.palace import get_shishen
from engine.predicates.relations import relation_strength, zhi_chong, zhi_chuan, zhi_liuhe, zhi_xing
from engine.predicates.types import WUXING_LIST
from engine.predicates.wuxing import wuxing_relation

_PILLAR_ALIASES = (
    ("year", "年柱"),
    ("month", "月柱"),
    ("day", "日柱"),
    ("hour", "时柱"),
)
_TEN_GODS = ("比肩", "劫财", "食神", "伤官", "正财", "偏财", "正官", "七杀", "正印", "偏印")
_LIUHE_PAIRS = {
    frozenset(("子", "丑")), frozenset(("寅", "亥")), frozenset(("卯", "戌")),
    frozenset(("辰", "酉")), frozenset(("巳", "申")), frozenset(("午", "未")),
}
_COLD_WARM_MONTH = {
    "亥": -0.8, "子": -1.0, "丑": -0.7,
    "寅": -0.2, "卯": 0.0, "辰": 0.1,
    "巳": 0.7, "午": 1.0, "未": 0.6,
    "申": 0.2, "酉": 0.0, "戌": 0.2,
}
_DRY_WET_MONTH = {
    "亥": -0.8, "子": -1.0, "丑": -0.5,
    "寅": -0.2, "卯": -0.1, "辰": -0.3,
    "巳": 0.5, "午": 0.7, "未": 0.4,
    "申": 0.0, "酉": 0.2, "戌": 0.8,
}
_CLIMATE_EXTREME_THRESHOLD = 0.65


def _clamp(value: float) -> float:
    return max(-1.0, min(1.0, value))


def _pillar_values(chart: ChartFactLedger) -> list[str | None]:
    values: list[str | None] = []
    for english, chinese in _PILLAR_ALIASES:
        raw = chart.four_pillars.get(english, chart.four_pillars.get(chinese, ""))
        text = str(raw or "").strip()
        values.append(text if len(text) >= 2 and is_gan(text[0]) and is_zhi(text[1]) else None)
    return values


def _unique_pairs(pairs: Iterable[tuple[str, str]]) -> tuple[tuple[str, str], ...]:
    return tuple(dict.fromkeys(pairs))


def _chart_id(chart: ChartFactLedger, pillars: list[str | None], schema_version: str) -> str:
    identity = {
        "schema_version": schema_version,
        "four_pillars": pillars,
        "sex_marker": chart.sex_marker,
        "solar_datetime": chart.solar_datetime,
        "siling": chart.siling,
    }
    canonical = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "cfv-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]


def _element_features(gans: list[str], zhis: list[str]) -> tuple[dict[str, int], dict[str, float], str, tuple[str, ...], float]:
    counts = {element: 0 for element in WUXING_LIST}
    for gan in gans:
        counts[gan_to_wuxing(gan)] += 1
    for zhi in zhis:
        counts[zhi_to_wuxing(zhi)] += 1

    raw_energy = {element: 0.0 for element in WUXING_LIST}
    for gan in gans:
        raw_energy[gan_to_wuxing(gan)] += 1.0
    for zhi in zhis:
        for hidden in get_canggan(zhi):
            raw_energy[gan_to_wuxing(hidden.gan)] += hidden.li_liang
    total_energy = sum(raw_energy.values())
    energy = {element: raw_energy[element] / total_energy for element in WUXING_LIST}

    total_count = sum(counts.values())
    dominant = max(WUXING_LIST, key=lambda element: (counts[element], -WUXING_LIST.index(element)))
    missing = tuple(element for element in WUXING_LIST if counts[element] == 0)
    concentration = counts[dominant] / total_count
    return counts, energy, dominant, missing, concentration


def _ten_god_features(day_master: str, gans: list[str], zhis: list[str]) -> dict[str, int]:
    counts = Counter({name: 0 for name in _TEN_GODS})
    for gan in gans:
        counts[get_shishen(gan, day_master)] += 1
    for zhi in zhis:
        for hidden in get_canggan(zhi):
            counts[get_shishen(hidden.gan, day_master)] += 1
    return {name: counts[name] for name in _TEN_GODS}


def _day_master_signals(day_master: str, month_branch: str, gans: list[str], zhis: list[str]) -> tuple[str, int, int, int, bool]:
    dm_element = gan_to_wuxing(day_master)
    month_lord = get_canggan(month_branch)[0].gan
    rooted_count = sum(
        any(
            wuxing_relation(dm_element, gan_to_wuxing(hidden.gan)) == "同我"
            for hidden in get_canggan(zhi)
        )
        for zhi in zhis
    )
    supporting_count = 0
    draining_count = 0
    for element in [gan_to_wuxing(gan) for gan in gans] + [zhi_to_wuxing(zhi) for zhi in zhis]:
        if wuxing_relation(dm_element, element) in {"同我", "生我"}:
            supporting_count += 1
        else:
            draining_count += 1
    monthly_command_favorable = wuxing_relation(dm_element, gan_to_wuxing(month_lord)) in {"同我", "生我"}
    return month_lord, rooted_count, supporting_count, draining_count, monthly_command_favorable


def _branch_relations(zhis: list[str]) -> tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str], ...], tuple[tuple[str, str], ...], float]:
    chong: list[tuple[str, str]] = []
    he: list[tuple[str, str]] = []
    xing_hai: list[tuple[str, str]] = []
    conflict_strength = 0.0
    possible_pair_count = len(zhis) * (len(zhis) - 1) // 2

    for left, right in combinations(zhis, 2):
        pair = (left, right)
        if zhi_chong(left, right):
            chong.append(pair)
            conflict_strength += relation_strength("冲")
        if frozenset((left, right)) in _LIUHE_PAIRS:
            # zhi_liuhe("午", "未") 返回 None 是因为无固定化神，但六合事实仍成立。
            zhi_liuhe(left, right)
            he.append(pair)
        if zhi_xing(left, right) is not None:
            xing_hai.append(pair)
            conflict_strength += relation_strength("刑")
        if zhi_chuan(left, right):
            xing_hai.append(pair)
            conflict_strength += relation_strength("害")

    intensity = min(1.0, conflict_strength / possible_pair_count) if possible_pair_count else 0.0
    return _unique_pairs(chong), _unique_pairs(he), _unique_pairs(xing_hai), intensity


def _climate(month_branch: str, energy: dict[str, float]) -> tuple[float, float, bool]:
    cold_warm = _clamp(_COLD_WARM_MONTH[month_branch] + 0.5 * (energy["火"] - energy["水"]))
    dry_wet = _clamp(
        _DRY_WET_MONTH[month_branch]
        + 0.4 * (energy["火"] + energy["土"] - energy["水"] - energy["木"])
    )
    extreme = max(abs(cold_warm), abs(dry_wet)) >= _CLIMATE_EXTREME_THRESHOLD
    return cold_warm, dry_wet, extreme


def build_chart_feature_vector(
    chart: ChartFactLedger,
    *,
    schema_version: str = "cfv-v1",
) -> ChartFeatureVector:
    """构建不可变、无 IO、无时间依赖的命局特征向量。"""
    if not isinstance(chart, ChartFactLedger):
        raise TypeError("chart must be ChartFactLedger")
    if not schema_version.strip():
        raise ValueError("schema_version is required")

    pillars = _pillar_values(chart)
    if pillars[2] is None or pillars[1] is None:
        raise ValueError("month and day pillars are required to build ChartFeatureVector")
    valid_pillars = [pillar for pillar in pillars if pillar is not None]
    gans = [pillar[0] for pillar in valid_pillars]
    zhis = [pillar[1] for pillar in valid_pillars]
    day_master = pillars[2][0]
    month_branch = pillars[1][1]

    counts, energy, dominant, missing, concentration = _element_features(gans, zhis)
    ten_gods = _ten_god_features(day_master, gans, zhis)
    month_lord, rooted, supporting, draining, monthly_favorable = _day_master_signals(
        day_master, month_branch, gans, zhis
    )
    chong, he, xing_hai, conflict_intensity = _branch_relations(zhis)
    cold_warm, dry_wet, climate_extreme = _climate(month_branch, energy)

    has_hour = pillars[3] is not None
    if all(pillar is not None for pillar in pillars):
        completeness = "full"
    elif all(pillar is not None for pillar in pillars[:3]) and not has_hour:
        completeness = "no_hour"
    else:
        completeness = "partial"

    return ChartFeatureVector(
        schema_version=schema_version,
        chart_id=_chart_id(chart, pillars, schema_version),
        element_counts=counts,
        element_energy=energy,
        dominant_element=dominant,
        missing_elements=missing,
        element_concentration=concentration,
        day_master=day_master,
        day_master_element=gan_to_wuxing(day_master),
        month_branch=month_branch,
        month_lord=month_lord,
        rooted_count=rooted,
        supporting_count=supporting,
        draining_count=draining,
        monthly_command_favorable=monthly_favorable,
        ten_god_counts=ten_gods,
        has_official=bool(ten_gods["正官"] or ten_gods["七杀"]),
        has_wealth=bool(ten_gods["正财"] or ten_gods["偏财"]),
        has_output=bool(ten_gods["食神"] or ten_gods["伤官"]),
        has_resource=bool(ten_gods["正印"] or ten_gods["偏印"]),
        mixed_official_kill=bool(ten_gods["正官"] and ten_gods["七杀"]),
        chong_pairs=chong,
        he_pairs=he,
        xing_hai_pairs=xing_hai,
        branch_conflict_intensity=conflict_intensity,
        cold_warm_axis=cold_warm,
        dry_wet_axis=dry_wet,
        climate_extreme=climate_extreme,
        has_hour_pillar=has_hour,
        evidence_completeness=completeness,
    )
