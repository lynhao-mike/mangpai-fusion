"""职业路径分类器 v3：通根/透出/临近日主强度分级判别。

v1、v2 的根因诊断（见 reports/career-path-error-analysis-v1.md §四）：
  detector_2 使用"藏干全展开后任意位置出现食伤 AND 财 AND 比劫/主体"的二元判断，
  几乎对所有命盘成立，导致 entrepreneurship_score 恒为 4.0，任职 recall 固定在
  12.5%，无论怎么调权重都无法解决。

v3 修复方案（detector_2 分级强度）：
  - 食伤须满足"透出天干"或"月支司令"才算强度 2+；仅藏在非月支分支算强度 1。
  - 财星须满足"透出天干"或"月支藏干"才算强度 2+；仅在其他地支藏干算强度 1。
  - 主体参与须满足"比劫天干透出"或"日支主体宫食伤财藏干"；仅有其他地支藏干
    比劫算强度 1。
  - 经营链完整分（4.0）需食伤≥2 且财≥2 且主体≥2；部分匹配按比例减半或更低。
  - 仅满足食伤≥1 且财≥1 且主体≥1 的弱配置得 2.0（与任职链同量级，易被官印链覆盖）。
  - 仅有财星（无有效做功闭环）封顶 0.5。
  - 仅有孤立食伤（无财）封顶 0.5。
  - 以上变化使绝大多数"受雇典型"命盘的 entrepreneurship_score 下降到 ≤2，
    而"经营典型"命盘（月支有财/食伤透干）仍能达到 4。

其他判别器与 v2 保持一致：
  - detector_1：官印组织链（有根官杀+印绶承接）。
  - detector_3：大运路径门控（官杀运抑制经营；食伤财运开放经营）。
  - 弃权边界：|employment - entrepreneurship| < 1.5 或 mixed_signal。

本模块不读取标签、反馈、known_facts 或 occupation；现实状态始终为 unknown。
分类器参数在首次 holdout 前冻结，评分后禁止修改。
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

# 月支是命局司令，权重最高。索引 0=年柱地支，1=月柱地支，2=日柱地支，3=时柱地支。
_MONTH_BRANCH_INDEX = 1
_DAY_BRANCH_INDEX = 2


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


def _strength_analysis(
    pillars: tuple[str, str, str, str],
    day_master: str,
) -> dict[str, Any]:
    """为每类十神计算分级强度，区分"透出天干"、"月支司令"、"其他地支藏干"三档。

    Returns dict with keys:
      official_strength / resource_strength / output_strength /
      wealth_strength / peer_strength  ∈ {0, 1, 2, 3}

      3 = 天干透出（最强）
      2 = 藏在月支（司令，次强）
      1 = 藏在其他地支（年/日/时支，最弱）
      0 = 不存在

    以及：
      day_branch_gods: set of 十神 in day-branch hidden stems
      mixed_official_kill: 正官 and 七杀 both present (any position)
    """
    stems: list[str] = []
    branch_hidden: list[set[str]] = []  # per pillar [year, month, day, time]

    for idx, pillar in enumerate(pillars):
        stem_god = get_shishen(pillar[0], day_master)  # type: ignore[arg-type]
        if idx != 2:  # 日干是主体，不重复作为十神
            stems.append(stem_god)
        bh = {
            get_shishen(item.gan, day_master)  # type: ignore[arg-type]
            for item in get_canggan(pillar[1])  # type: ignore[arg-type]
        }
        branch_hidden.append(bh)

    month_branch_gods: set[str] = branch_hidden[_MONTH_BRANCH_INDEX]
    day_branch_gods: set[str] = branch_hidden[_DAY_BRANCH_INDEX]
    other_branch_gods: set[str] = branch_hidden[0] | branch_hidden[3]

    all_visible: set[str] = set(stems)
    all_month: set[str] = month_branch_gods
    all_other_hidden: set[str] = other_branch_gods | day_branch_gods

    def _strength(names: tuple[str, ...]) -> int:
        for name in names:
            if name in all_visible:
                return 3  # 天干透出
        for name in names:
            if name in all_month:
                return 2  # 月支藏干
        for name in names:
            if name in all_other_hidden:
                return 1  # 其他地支藏干
        return 0

    mixed_official_kill = (
        any(n in OFFICIAL_NAMES for n in all_visible | all_month | all_other_hidden)
        and "正官" in (all_visible | all_month | all_other_hidden)
        and "七杀" in (all_visible | all_month | all_other_hidden)
    )

    return {
        "official_strength": _strength(OFFICIAL_NAMES),
        "resource_strength": _strength(RESOURCE_NAMES),
        "output_strength": _strength(OUTPUT_NAMES),
        "wealth_strength": _strength(WEALTH_NAMES),
        "peer_strength": _strength(PEER_NAMES),
        "output_in_month": any(n in OUTPUT_NAMES for n in month_branch_gods),
        "wealth_in_month": any(n in WEALTH_NAMES for n in month_branch_gods),
        "peer_in_stems": any(n in PEER_NAMES for n in all_visible),
        "day_branch_has_output_wealth": any(
            n in OUTPUT_NAMES + WEALTH_NAMES for n in day_branch_gods
        ),
        "mixed_official_kill": mixed_official_kill,
        "output_breaks_official": (
            _strength(OUTPUT_NAMES) >= 3
            and _strength(OFFICIAL_NAMES) >= 1
            and _strength(RESOURCE_NAMES) == 0
        ),
    }


def _natal_scores_v3(
    s: dict[str, Any],
) -> tuple[float, float, tuple[str, ...]]:
    """v3 分级强度计分（与 v2 detector_1 保持一致；detector_2 改为分级）。"""
    employment = 0.0
    entrepreneurship = 0.0
    refs: list[str] = []

    # ─── Detector 1：官印组织链（与 v2 逻辑相同） ───────────────────────────────
    off = s["official_strength"]
    res = s["resource_strength"]
    out = s["output_strength"]

    if off >= 1 and res >= 1 and not s["mixed_official_kill"]:
        if off >= 2:  # 有根官杀（月支或天干）+ 印绶承接
            employment += 2.0
            refs.append("detector_1:rooted_official_resource_chain")
        else:  # 官杀仅其他地支藏，印绶存在
            employment += 1.0
            refs.append("detector_1:weak_official_resource_chain")
        if off >= 3 and res >= 3:  # 官印均透干
            employment += 1.5
            refs.append("detector_1:visible_official_resource_chain")
    if s["output_breaks_official"]:
        employment -= 1.0
        refs.append("detector_1:strong_output_breaks_official_without_resource_rescue")

    # ─── Detector 2 v3：食伤生财做功闭环（分级强度） ────────────────────────────
    # 主体参与强度（比劫透出 or 日支有食伤/财 = 强；其他 = 弱）
    wlth = s["wealth_strength"]
    subject_strong = s["peer_in_stems"] or s["day_branch_has_output_wealth"]
    subject_weak = s["peer_strength"] >= 1 and not subject_strong

    if out >= 2 and wlth >= 2 and subject_strong:
        # 食伤强（月支+或透干）+ 财强（月支+或透干）+ 主体积极参与 → 完整经营链
        entrepreneurship += 4.0
        refs.append("detector_2_v3:strong_output_wealth_chain_active_subject")
    elif out >= 2 and wlth >= 2 and subject_weak:
        # 食伤、财均强，但主体参与仅靠比劫藏干
        entrepreneurship += 2.5
        refs.append("detector_2_v3:strong_output_wealth_chain_weak_subject")
    elif (out >= 2 or wlth >= 2) and out >= 1 and wlth >= 1 and subject_strong:
        # 一项强、一项弱，但主体积极参与
        entrepreneurship += 2.0
        refs.append("detector_2_v3:mixed_strength_chain_active_subject")
    elif out >= 1 and wlth >= 1 and (subject_strong or subject_weak):
        # 食伤、财均只有藏干，主体参与任意
        entrepreneurship += 1.0
        refs.append("detector_2_v3:weak_output_wealth_chain")
    elif wlth >= 1:
        # 只有财星，无有效食伤闭环
        entrepreneurship += 0.5
        refs.append("detector_2_v3:wealth_only_cap")
    elif out >= 1:
        # 只有食伤，无财
        entrepreneurship += 0.5
        refs.append("detector_2_v3:output_only_cap")

    refs.append(f"employment_score={employment:.1f}")
    refs.append(f"entrepreneurship_score={entrepreneurship:.1f}")
    return employment, entrepreneurship, tuple(refs)


def _dayun_context_v3(
    day_master: str,
    segment: dict | None,
    *,
    natal_resource_strength: int,
    natal_subject_strong: bool,
) -> DayunCareerContext | None:
    """v3 大运路径门控（对称实现，逻辑与 v2 一致）。"""
    if segment is None:
        return None
    ganzhi = segment.get("ganzhi")
    if not isinstance(ganzhi, str) or len(ganzhi.strip()) < 2:
        return None
    ganzhi = ganzhi.strip()
    if not is_gan(ganzhi[0]) or not is_zhi(ganzhi[1]):
        return None
    gods: set[str] = {get_shishen(ganzhi[0], day_master)}  # type: ignore[arg-type]
    gods.update(
        get_shishen(item.gan, day_master)  # type: ignore[arg-type]
        for item in get_canggan(ganzhi[1])  # type: ignore[arg-type]
    )
    official = any(n in OFFICIAL_NAMES for n in gods)
    output_or_wealth = any(n in OUTPUT_NAMES + WEALTH_NAMES for n in gods)

    if official and natal_resource_strength >= 1:
        return DayunCareerContext(
            opens_employment=True,
            opens_entrepreneurship=False,
            suppresses_employment=False,
            suppresses_entrepreneurship=True,
            mechanism=f"detector_3:dayun:{ganzhi};official_kill_with_resource_receiver",
        )
    if official:
        return DayunCareerContext(
            opens_employment=False,
            opens_entrepreneurship=False,
            suppresses_employment=False,
            suppresses_entrepreneurship=False,
            mechanism=f"detector_3:dayun:{ganzhi};official_pressure_without_receiver",
        )
    if output_or_wealth and natal_subject_strong:
        return DayunCareerContext(
            opens_employment=False,
            opens_entrepreneurship=True,
            suppresses_employment=True,
            suppresses_entrepreneurship=False,
            mechanism=f"mechanism_c:dayun:{ganzhi};output_wealth_with_subject_capacity",
        )
    return DayunCareerContext(
        opens_employment=False,
        opens_entrepreneurship=False,
        suppresses_employment=False,
        suppresses_entrepreneurship=False,
        mechanism=f"dayun:{ganzhi};no_path_switch",
    )


def classify_career_path(
    pillars: tuple[str, str, str, str],
    dayun_sequence: list[dict],
    as_of_date: datetime | None = None,
) -> CareerPathState:
    """仅由排盘信息推断职业路径；不读取 known_facts、occupation 或反馈。

    v3 改进：detector_2 改为通根/透出/临近日主强度分级；解决 v2 经营链在
    所有命盘几乎均成立导致任职 recall 恒为 12.5% 的问题。
    """
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
        strength = _strength_analysis(pillars, features.day_master)
    except (TypeError, ValueError, KeyError):
        return _unknown_state("insufficient_information")

    employment_score, entrepreneurship_score, refs = _natal_scores_v3(strength)
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

    context = _dayun_context_v3(
        features.day_master,
        _current_dayun(dayun_sequence, as_of_date),
        natal_resource_strength=strength["resource_strength"],
        natal_subject_strong=strength["peer_in_stems"] or strength["day_branch_has_output_wealth"],
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
