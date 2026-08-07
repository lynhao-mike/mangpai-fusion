"""职业路径分类器 v2：链式结构判别与对称大运门控。

规则只消费四柱、大运序列和求测日期。现实状态始终为 ``unknown``；本模块
不得读取标签、反馈、known facts 或 occupation。评分参数来自
``reports/career-path-error-analysis-v1.md`` 第四节，并在首次 holdout 前冻结。
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
from engine.predicates.ganzhi import get_canggan, is_gan, is_zhi
from engine.predicates.palace import get_shishen

SCORE_MARGIN = 1.5
OFFICIAL_NAMES = ("正官", "七杀")
RESOURCE_NAMES = ("正印", "偏印")
OUTPUT_NAMES = ("食神", "伤官")
WEALTH_NAMES = ("正财", "偏财")
PEER_NAMES = ("比肩", "劫财")


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


def _unknown_state(reason: str) -> CareerPathState:
    return CareerPathState(
        natal_inclination=NatalCareerInclination(False, False, ()),
        dayun_context=None,
        reality_status=RealityCareerStatus("unknown", (), ()),
        abstain_reason=reason,
    )


def _structure(pillars: tuple[str, str, str, str], day_master: str) -> dict[str, Any]:
    visible: list[str] = []
    hidden: list[str] = []
    hidden_by_branch: list[set[str]] = []
    for index, pillar in enumerate(pillars):
        if index != 2:  # 日干是主体，不作为额外比劫透干重复计数。
            visible.append(get_shishen(pillar[0], day_master))  # type: ignore[arg-type]
        branch_gods = {
            get_shishen(item.gan, day_master)  # type: ignore[arg-type]
            for item in get_canggan(pillar[1])  # type: ignore[arg-type]
        }
        hidden.extend(branch_gods)
        hidden_by_branch.append(branch_gods)

    def any_god(names: tuple[str, ...], values: list[str]) -> bool:
        return any(name in names for name in values)

    return {
        "visible": visible,
        "hidden": hidden,
        "official_visible": any_god(OFFICIAL_NAMES, visible),
        "official_hidden": any_god(OFFICIAL_NAMES, hidden),
        "resource_visible": any_god(RESOURCE_NAMES, visible),
        "resource_present": any_god(RESOURCE_NAMES, visible + hidden),
        "output_visible": any_god(OUTPUT_NAMES, visible),
        "output_present": any_god(OUTPUT_NAMES, visible + hidden),
        "output_hidden": any_god(OUTPUT_NAMES, hidden),
        "wealth_visible": any_god(WEALTH_NAMES, visible),
        "wealth_present": any_god(WEALTH_NAMES, visible + hidden),
        "wealth_hidden": any_god(WEALTH_NAMES, hidden),
        "peer_visible": any_god(PEER_NAMES, visible),
        "peer_hidden": any_god(PEER_NAMES, hidden),
        # 日支为主体宫位；其中有食伤/财，即主体宫直接进入输出或交易环节。
        "subject_palace_participates": any_god(OUTPUT_NAMES + WEALTH_NAMES, list(hidden_by_branch[2])),
        "mixed_official_kill": "正官" in visible + hidden and "七杀" in visible + hidden,
    }


def _natal_scores(structure: dict[str, Any]) -> tuple[float, float, tuple[str, ...]]:
    """实现误差报告第四节判别器 1、2 的冻结计分草案。"""
    employment = 0.0
    entrepreneurship = 0.0
    refs: list[str] = []

    official_present = structure["official_visible"] or structure["official_hidden"]
    stable_official = not (
        structure["mixed_official_kill"]
        and not structure["output_present"]
        and not structure["resource_present"]
    )
    if official_present and structure["official_hidden"] and structure["resource_present"] and stable_official:
        employment += 2.0
        refs.append("detector_1:rooted_official_resource_chain")
    if structure["official_visible"] and structure["resource_visible"] and stable_official:
        employment += 1.5
        refs.append("detector_1:visible_official_resource_chain")
    if official_present and structure["output_visible"] and not structure["resource_present"]:
        employment -= 1.0
        refs.append("detector_1:strong_output_breaks_official_without_resource_rescue")
    if structure["mixed_official_kill"] and not stable_official:
        refs.append("detector_1:mixed_official_kill_without_control_or_resource")

    subject_participates = (
        structure["peer_visible"]
        or structure["peer_hidden"]
        or structure["subject_palace_participates"]
    )
    output_usable = structure["output_visible"] or structure["output_hidden"]
    work_chain = output_usable and structure["wealth_present"] and subject_participates
    if work_chain:
        entrepreneurship += 2.0
        refs.append("detector_2:usable_output_directly_generates_wealth")
        if structure["wealth_hidden"] and (structure["output_visible"] or structure["output_hidden"]):
            entrepreneurship += 1.0
            refs.append("detector_2:rooted_continuous_output_wealth_chain")
        entrepreneurship += 1.0
        refs.append("detector_2:peer_or_subject_participation")
    elif structure["wealth_present"]:
        entrepreneurship += 0.5
        refs.append("detector_2:wealth_only_cap")

    refs.extend((
        f"employment_score={employment:.1f}",
        f"entrepreneurship_score={entrepreneurship:.1f}",
    ))
    return employment, entrepreneurship, tuple(refs)


def _dayun_context(
    day_master: str,
    segment: dict | None,
    *,
    natal_resource_can_receive: bool,
    natal_subject_can_bear: bool,
) -> DayunCareerContext | None:
    """实现机制 C：官杀运抑制经营，食伤财运对称开放经营。"""
    if segment is None:
        return None
    ganzhi = segment.get("ganzhi")
    if not isinstance(ganzhi, str) or len(ganzhi.strip()) < 2:
        return None
    ganzhi = ganzhi.strip()
    if not is_gan(ganzhi[0]) or not is_zhi(ganzhi[1]):
        return None
    gods = {get_shishen(ganzhi[0], day_master)}  # type: ignore[arg-type]
    gods.update(get_shishen(item.gan, day_master) for item in get_canggan(ganzhi[1]))  # type: ignore[arg-type]
    official = any(name in OFFICIAL_NAMES for name in gods)
    output_or_wealth = any(name in OUTPUT_NAMES + WEALTH_NAMES for name in gods)

    if official and natal_resource_can_receive:
        return DayunCareerContext(
            opens_employment=True,
            opens_entrepreneurship=False,
            suppresses_employment=False,
            suppresses_entrepreneurship=True,
            mechanism=f"detector_3:current_dayun:{ganzhi};official_kill_with_resource_receiver",
        )
    if official:
        return DayunCareerContext(
            opens_employment=False,
            opens_entrepreneurship=False,
            suppresses_employment=False,
            suppresses_entrepreneurship=False,
            mechanism=f"detector_3:current_dayun:{ganzhi};official_pressure_without_receiver",
        )
    if output_or_wealth and natal_subject_can_bear:
        return DayunCareerContext(
            opens_employment=False,
            opens_entrepreneurship=True,
            suppresses_employment=True,
            suppresses_entrepreneurship=False,
            mechanism=f"mechanism_c:current_dayun:{ganzhi};output_wealth_with_subject_capacity",
        )
    return DayunCareerContext(
        opens_employment=False,
        opens_entrepreneurship=False,
        suppresses_employment=False,
        suppresses_entrepreneurship=False,
        mechanism=f"current_dayun:{ganzhi};no_path_switch",
    )


def classify_career_path(
    pillars: tuple[str, str, str, str],
    dayun_sequence: list[dict],
    as_of_date: datetime | None = None,
) -> CareerPathState:
    """仅由排盘信息推断职业路径；不读取 known_facts、occupation 或反馈。"""
    if (
        not isinstance(pillars, tuple)
        or len(pillars) != 4
        or any(
            not isinstance(item, str)
            or len(item.strip()) != 2
            or not is_gan(item.strip()[0])
            or not is_zhi(item.strip()[1])
            for item in pillars
        )
    ):
        return _unknown_state("insufficient_information")

    pillars = tuple(item.strip() for item in pillars)  # type: ignore[assignment]
    try:
        ledger = chart_ledger_from_mapping({"four_pillars": list(pillars)})
        features = build_chart_feature_vector(ledger)
        structure = _structure(pillars, features.day_master)
    except (TypeError, ValueError, KeyError):
        return _unknown_state("insufficient_information")

    employment_score, entrepreneurship_score, refs = _natal_scores(structure)
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

    context = _dayun_context(
        features.day_master,
        _current_dayun(dayun_sequence, as_of_date),
        natal_resource_can_receive=structure["resource_present"],
        natal_subject_can_bear=(
            structure["peer_visible"]
            or structure["peer_hidden"]
            or structure["subject_palace_participates"]
        ),
    )
    if context is not None:
        opposed = (
            context.suppresses_entrepreneurship
            and natal.entrepreneurship_inclined
            and not natal.employment_inclined
        ) or (
            context.suppresses_employment
            and natal.employment_inclined
            and not natal.entrepreneurship_inclined
        )
        if opposed:
            abstain_reason = "mixed_signal"

    return CareerPathState(
        natal_inclination=natal,
        dayun_context=context,
        reality_status=RealityCareerStatus("unknown", (), ()),
        abstain_reason=abstain_reason,
    )


__all__ = ("SCORE_MARGIN", "classify_career_path")
