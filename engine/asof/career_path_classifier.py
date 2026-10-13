"""仅由四柱和大运推断职业路径倾向的极简冻结候选。

本模块不读取现实职业事实。返回值中的现实状态固定为 ``unknown``；调用方不得把
原局倾向或大运开放误写成已经发生的职业经历。
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from engine.asof.career_path_state import (
    CareerPathState,
    DayunCareerContext,
    NatalCareerInclination,
    RealityCareerStatus,
)
from engine.claims.orchestrator import chart_ledger_from_mapping
from engine.features import build_chart_feature_vector
from engine.predicates.palace import get_shishen


SCORE_MARGIN = 1.5
OFFICIAL_NAMES = ("正官", "七杀")
RESOURCE_NAMES = ("正印", "偏印")
OUTPUT_NAMES = ("食神", "伤官")
WEALTH_NAMES = ("正财", "偏财")
PEER_NAMES = ("比肩", "劫财")
BRANCH_MAIN_GAN = {
    "子": "癸", "丑": "己", "寅": "甲", "卯": "乙", "辰": "戊", "巳": "丙",
    "午": "丁", "未": "己", "申": "庚", "酉": "辛", "戌": "戊", "亥": "壬",
}


def _count(counts: Any, names: tuple[str, ...]) -> int:
    return sum(int(counts.get(name, 0)) for name in names)


def _parse_date(value: object) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


def _current_dayun(dayun_sequence: list[dict], as_of_date: datetime | None) -> dict | None:
    if as_of_date is None:
        return None
    target = as_of_date.date()
    for segment in dayun_sequence:
        if not isinstance(segment, dict):
            continue
        start = _parse_date(segment.get("start") or segment.get("start_date"))
        end = _parse_date(segment.get("end") or segment.get("end_date"))
        if start is not None and end is not None and start <= target <= end:
            return segment
    return None


def _official_dayun_context(day_master: str, segment: dict | None) -> DayunCareerContext | None:
    if segment is None:
        return None
    ganzhi = segment.get("ganzhi")
    if not isinstance(ganzhi, str) or len(ganzhi.strip()) < 2:
        return None
    ganzhi = ganzhi.strip()
    stem_god = get_shishen(ganzhi[0], day_master)  # type: ignore[arg-type]
    branch_main = BRANCH_MAIN_GAN.get(ganzhi[1])
    branch_god = get_shishen(branch_main, day_master) if branch_main else None  # type: ignore[arg-type]
    official = stem_god in OFFICIAL_NAMES or branch_god in OFFICIAL_NAMES
    if not official:
        return DayunCareerContext(
            opens_employment=False,
            opens_entrepreneurship=False,
            suppresses_employment=False,
            suppresses_entrepreneurship=False,
            mechanism=f"current_dayun:{ganzhi};no_official_kill_constraint",
        )
    return DayunCareerContext(
        opens_employment=True,
        opens_entrepreneurship=False,
        suppresses_employment=False,
        suppresses_entrepreneurship=True,
        mechanism=f"current_dayun:{ganzhi};official_kill_in_command",
    )


def _unknown_state(reason: str) -> CareerPathState:
    return CareerPathState(
        natal_inclination=NatalCareerInclination(False, False, ()),
        dayun_context=None,
        reality_status=RealityCareerStatus("unknown", (), ()),
        abstain_reason=reason,
    )


def classify_career_path(
    pillars: tuple[str, str, str, str],
    dayun_sequence: list[dict],
    as_of_date: datetime | None = None,
) -> CareerPathState:
    """从排盘信息推断职业路径状态。

    不读取任何known_facts、occupation字段或反馈文本。
    """
    if len(pillars) != 4 or any(not isinstance(item, str) or len(item.strip()) != 2 for item in pillars):
        return _unknown_state("insufficient_information")

    try:
        ledger = chart_ledger_from_mapping({"four_pillars": list(pillars)})
        features = build_chart_feature_vector(ledger)
    except (TypeError, ValueError, KeyError):
        return _unknown_state("insufficient_information")

    counts = features.ten_god_counts
    official = _count(counts, OFFICIAL_NAMES)
    resource = _count(counts, RESOURCE_NAMES)
    output = _count(counts, OUTPUT_NAMES)
    wealth = _count(counts, WEALTH_NAMES)
    peer = _count(counts, PEER_NAMES)

    employment_score = float(official)
    if official and resource:
        employment_score += 2.0
    if official and features.monthly_command_favorable:
        employment_score += 0.5

    entrepreneurship_score = 0.5 * wealth
    if output and wealth:
        entrepreneurship_score += 2.0 + 0.5 * min(output, wealth)
    if output and wealth and peer:
        entrepreneurship_score += 1.0

    refs = (
        f"official={official}",
        f"resource={resource}",
        f"output={output}",
        f"wealth={wealth}",
        f"peer={peer}",
        f"employment_score={employment_score:.1f}",
        f"entrepreneurship_score={entrepreneurship_score:.1f}",
    )
    margin = employment_score - entrepreneurship_score
    if abs(margin) < SCORE_MARGIN:
        natal = NatalCareerInclination(True, True, refs)
        abstain_reason: str | None = "score_margin_below_threshold"
    elif margin > 0:
        natal = NatalCareerInclination(True, False, refs)
        abstain_reason = None
    else:
        natal = NatalCareerInclination(False, True, refs)
        abstain_reason = None

    context = _official_dayun_context(features.day_master, _current_dayun(dayun_sequence, as_of_date))
    if context is not None and context.suppresses_entrepreneurship and natal.entrepreneurship_inclined:
        abstain_reason = "mixed_signal"

    return CareerPathState(
        natal_inclination=natal,
        dayun_context=context,
        reality_status=RealityCareerStatus("unknown", (), ()),
        abstain_reason=abstain_reason,
    )


__all__ = ("SCORE_MARGIN", "classify_career_path")
