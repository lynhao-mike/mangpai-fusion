"""engine/v5/ziping_runner.py · 子平独立分析 runner。

从 chart DTO 直接推导子平核心两层：
  L1: 月令旺衰判断（得令/得地/偏弱/偏旺）
  L2: 格局用神识别（七杀/正官/财格等主要格局 + 用神天干）

不依赖旧 D1-D4 流程，直接输出 V5Claim 列表，
可作为 build_default_claims() 的替代性子平命题来源。

ponytail: 只实现能改善 V5Claim 精度的最小推导，
不写完整命理专家系统。
"""

from __future__ import annotations

import hashlib
from typing import Any

from engine.predicates.palace import get_shishen
from engine.predicates.types import (
    GAN_TO_WUXING,
    ZHI_CANGGAN_TABLE,
    ZHI_TO_WUXING,
)
from engine.claims import Claim, Evidence, TaskUnsupported, TimeWindow, stable_claim_id, validate_claim_evidence
from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindTask
from engine.features import ChartFeatureVector
from engine.v5.domain import (
    V5Claim,
    V5Confidence,
    V5Evidence,
)

# ── 基础常量 ────────────────────────────────────────────────────────────────

_MONTH_ZHIS = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")

# 月令主气天干（各月司令主气）
_MONTH_ZHI_LORD: dict[str, str] = {
    "子": "癸", "丑": "己",
    "寅": "甲", "卯": "乙",
    "辰": "戊", "巳": "丙",
    "午": "丁", "未": "己",
    "申": "庚", "酉": "辛",
    "戌": "戊", "亥": "壬",
}

_GAN_WUXING = GAN_TO_WUXING  # 复用

# 五行相生：a → b（a 生 b）
_SHENG: dict[str, str] = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
# 五行相克：a → b（a 克 b）
_KE: dict[str, str] = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def _shishen(day_master: str, target: str) -> str:
    """兼容旧私有入口；十神算法统一复用共用谓词。"""
    return get_shishen(target, day_master)  # type: ignore[arg-type]


def _stable_id(*parts: object) -> str:
    raw = "|".join(str(p) for p in parts)
    return "zipcl-" + hashlib.sha256(raw.encode()).hexdigest()[:12]


# ── L1: 月令旺衰判断 ─────────────────────────────────────────────────────────

def _assess_daymaster_strength(chart: dict[str, Any]) -> dict[str, Any]:
    """轻量评估日主旺衰，只用月令 + 天干 + 藏干基础判断。

    返回：
        strength: "偏旺" / "中和" / "偏弱"
        score: 0.0-1.0（>0.6=偏旺，0.4-0.6=中和，<0.4=偏弱）
        rationale: 可读说明
    """
    pillars_raw = chart.get("pillars") or {}
    # ponytail: 兼容 dict（{"year":"庚申",...}）与 list（["庚申","戊寅","壬子","辛丑"]）两种形态
    if isinstance(pillars_raw, list):
        keys = ("year", "month", "day", "hour")
        pillars: dict[str, str] = {k: str(v) for k, v in zip(keys, pillars_raw)}
    elif isinstance(pillars_raw, dict):
        pillars = {k: str(v) for k, v in pillars_raw.items()}
    else:
        return {"strength": "中和", "score": 0.5, "rationale": "四柱格式不支持"}

    day_gan = pillars.get("day", "")[:1] if pillars.get("day") else str(chart.get("day_stem", ""))
    month_zhi_full = pillars.get("month", "") if pillars.get("month") else ""
    month_zhi = month_zhi_full[1] if len(month_zhi_full) >= 2 else str(chart.get("month_branch", ""))

    if not day_gan or not month_zhi:
        return {"strength": "中和", "score": 0.5, "rationale": "日主或月支未知"}

    dm_wx = _GAN_WUXING.get(day_gan, "")
    score = 0.5  # base

    # 得令：月令司令是否帮扶日主
    lord_gan = _MONTH_ZHI_LORD.get(month_zhi, "")
    lord_wx = _GAN_WUXING.get(lord_gan, "")
    if lord_wx == dm_wx or _SHENG.get(lord_wx) == dm_wx:
        score += 0.20

    # 月支五行
    month_wx = ZHI_TO_WUXING.get(month_zhi, "")
    if month_wx == dm_wx:
        score += 0.15
    elif _SHENG.get(month_wx) == dm_wx:
        score += 0.10
    elif _KE.get(month_wx) == dm_wx:
        score -= 0.15

    # 扫描四干（年月时干）帮扶 / 克制
    year_gan = str(pillars.get("year", ""))[:1] if isinstance(pillars.get("year"), str) else str(chart.get("year_stem", ""))
    month_gan = str(pillars.get("month", ""))[:1] if isinstance(pillars.get("month"), str) else str(chart.get("month_stem", ""))
    hour_gan = str(pillars.get("hour", ""))[:1] if isinstance(pillars.get("hour"), str) else str(chart.get("hour_stem", ""))

    for gan in (year_gan, month_gan, hour_gan):
        wx = _GAN_WUXING.get(gan, "")
        if not wx:
            continue
        if wx == dm_wx or _SHENG.get(wx) == dm_wx:
            score += 0.05
        elif _KE.get(wx) == dm_wx:
            score -= 0.05

    # 扫描四支藏干
    for pillar_key in ("year", "month", "day", "hour"):
        zhi_full = str(pillars.get(pillar_key, ""))
        zhi = zhi_full[1] if len(zhi_full) >= 2 else ""
        for (cang_gan, cang_type, _) in ZHI_CANGGAN_TABLE.get(zhi, []):
            cang_wx = _GAN_WUXING.get(cang_gan, "")
            weight = 0.04 if cang_type == "主气" else 0.02
            if cang_wx == dm_wx or _SHENG.get(cang_wx) == dm_wx:
                score += weight
            elif _KE.get(cang_wx) == dm_wx:
                score -= weight

    score = max(0.1, min(0.9, score))
    if score >= 0.62:
        strength = "偏旺"
    elif score <= 0.42:
        strength = "偏弱"
    else:
        strength = "中和"

    return {
        "strength": strength,
        "score": round(score, 2),
        "day_master": day_gan,
        "month_zhi": month_zhi,
        "month_lord": lord_gan,
        "rationale": f"日主{day_gan}（{dm_wx}），月令{month_zhi}司令{lord_gan}（{lord_wx}），月支帮扶={_SHENG.get(lord_wx)==dm_wx or lord_wx==dm_wx}，综合得分{score:.2f}→{strength}",
    }


# ── L2: 格局用神识别 ─────────────────────────────────────────────────────────

def _identify_pattern_yongshen(chart: dict[str, Any]) -> dict[str, Any]:
    """识别主要格局与用神。

    逻辑：月干透出的十神 → 月令格；
    用神 = 克制格神或扶助日主的天干。
    """
    pillars_raw = chart.get("pillars") or {}
    if isinstance(pillars_raw, list):
        keys = ("year", "month", "day", "hour")
        pillars: dict[str, str] = {k: str(v) for k, v in zip(keys, pillars_raw)}
    elif isinstance(pillars_raw, dict):
        pillars = {k: str(v) for k, v in pillars_raw.items()}
    else:
        return {"pattern": "未知", "yongshen": "待判", "rationale": "四柱格式不支持"}

    day_gan = pillars.get("day", "")[:1] if pillars.get("day") else str(chart.get("day_stem", ""))
    month_gan = pillars.get("month", "")[:1] if pillars.get("month") else str(chart.get("month_stem", ""))
    month_zhi_full = pillars.get("month", "") if pillars.get("month") else ""
    month_zhi = month_zhi_full[1] if len(month_zhi_full) >= 2 else str(chart.get("month_branch", ""))

    if (
        day_gan not in _GAN_WUXING
        or month_gan not in _GAN_WUXING
        or month_zhi not in _MONTH_ZHIS
    ):
        return {
            "pattern": "未知",
            "pattern_shen": "",
            "yongshen": "待判",
            "month_gan_shen": "未知",
            "month_lord_shen": "未知",
            "rationale": "干支信息不足或包含无效字符",
        }

    # 月干十神
    month_gan_shen = _shishen(day_gan, month_gan)

    # 月令藏干十神（主气）
    lord_gan = _MONTH_ZHI_LORD.get(month_zhi, "")
    month_lord_shen = _shishen(day_gan, lord_gan) if lord_gan else "未知"

    # 格局：月干或月令主气
    pattern_shen = month_gan_shen if month_gan_shen not in ("比肩", "劫财") else month_lord_shen

    # 用神推断：
    # 七杀/正官格 → 用印（克制官杀）或用食（制七杀）
    # 财格 → 用官（财生官）或用食（食生财）
    yongshen_map: dict[str, str] = {
        "七杀": "偏印/正印",
        "正官": "正印/偏印",
        "偏财": "食神/伤官",
        "正财": "正官/七杀",
        "食神": "偏财/正财",
        "伤官": "偏财/正财",
        "偏印": "食神/伤官",
        "正印": "食神/伤官",
    }
    yongshen = yongshen_map.get(pattern_shen, "待判")

    return {
        "pattern": f"{pattern_shen}格",
        "pattern_shen": pattern_shen,
        "yongshen": yongshen,
        "month_gan_shen": month_gan_shen,
        "month_lord_shen": month_lord_shen,
        "rationale": f"月干{month_gan}为{month_gan_shen}，月令{month_zhi}主气{lord_gan}为{month_lord_shen}，格局={pattern_shen}格，用神={yongshen}",
    }


# ── L3: 格局类型识别（正格 / 从格 / 特殊格）────────────────────────────────────

# 从格判断依据：日主在四柱中几乎无根且无印比帮扶
_CONG_GE_SHISHEN = frozenset(("七杀", "正官", "偏财", "正财", "食神", "伤官"))
_FU_SHEN_SHISHEN = frozenset(("比肩", "劫财", "正印", "偏印"))


def _identify_geju_type(chart: dict[str, Any], l1: dict[str, Any], l2: dict[str, Any]) -> dict[str, Any]:
    """识别格局大类：正格 / 从格 / 特殊格。

    正格：日主有根、有印比帮扶，月令格神成立。
    从格：日主极弱（score<0.32），无印比、无根，全局一色。
    特殊格：一气专旺（曲直/炎上/稼穑/从革/润下）等。
    """
    strength_score = float(l1.get("score", 0.5))
    pattern_shen = str(l2.get("pattern_shen", ""))
    day_master = str(l1.get("day_master", ""))
    dm_wx = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
             "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}.get(day_master, "")

    # 一气专旺特殊格粗判（四柱五行只有1-2种）
    pillars_raw = chart.get("pillars") or {}
    if isinstance(pillars_raw, list):
        pillars_text = "".join(str(p) for p in pillars_raw)
    elif isinstance(pillars_raw, dict):
        pillars_text = "".join(str(v) for v in pillars_raw.values())
    else:
        pillars_text = ""

    wuxing_present = sum(
        1 for wx, chars in [("木","甲乙寅卯"),("火","丙丁巳午"),("土","戊己辰戌丑未"),
                             ("金","庚辛申酉"),("水","壬癸亥子")]
        if any(ch in pillars_text for ch in chars)
    )

    # favor / avoid：机器可读的十神方向，供仲裁器过滤矛盾事件命题
    if wuxing_present <= 2 and strength_score >= 0.75:
        geju_type = "特殊格（一气偏旺）"
        constraint = "从旺、专旺方向，忌克泄，喜比印或流通"
        favor = ["比肩", "劫财", "正印", "偏印"]
        avoid = ["正官", "七杀", "正财", "偏财"]
        confidence = 0.55
    elif strength_score < 0.32 and pattern_shen in _CONG_GE_SHISHEN:
        geju_type = "从格"
        constraint = f"从{pattern_shen}方向，喜{pattern_shen}类生助，忌印比反克"
        # 从格：顺从旺神方向，喜财官食伤，忌印比帮身
        favor = ["正官", "七杀", "正财", "偏财", "食神", "伤官"]
        avoid = ["比肩", "劫财", "正印", "偏印"]
        confidence = 0.58
    else:
        geju_type = "正格"
        constraint = f"取{l2.get('yongshen','待判')}为用，日主{l1.get('strength','中和')}方向调配"
        # 正格：偏弱喜印比，偏旺喜财官食伤
        strength = str(l1.get("strength", "中和"))
        if strength == "偏弱":
            favor = ["正印", "偏印", "比肩", "劫财"]
            avoid = ["正官", "七杀", "正财", "偏财"]
        elif strength == "偏旺":
            favor = ["正官", "七杀", "正财", "偏财", "食神", "伤官"]
            avoid = ["正印", "偏印", "比肩", "劫财"]
        else:
            favor = []  # 中和格局不强约束事件方向
            avoid = []
        confidence = 0.65

    return {
        "geju_type": geju_type,
        "constraint": constraint,
        "favor": favor,
        "avoid": avoid,
        "confidence": confidence,
        "rationale": f"日主{day_master}（{dm_wx}），旺衰分={strength_score:.2f}，"
                     f"五行覆盖={wuxing_present}种，格局大类={geju_type}",
    }


# ── L5: 病药识别（命局核心矛盾 + 解决方向）────────────────────────────────────

def _identify_bingyao(chart: dict[str, Any], l1: dict[str, Any], l2: dict[str, Any], l3: dict[str, Any]) -> dict[str, Any]:
    """识别命局核心矛盾（病）和解决方向（药）。

    八层框架第五层：只有找准病，才能定药；病药是所有事件判断的基础约束。
    """
    strength = str(l1.get("strength", "中和"))
    strength_score = float(l1.get("score", 0.5))
    pattern_shen = str(l2.get("pattern_shen", ""))
    yongshen = str(l2.get("yongshen", "待判"))
    geju_type = str(l3.get("geju_type", "正格"))

    bing_list: list[str] = []
    yao_list: list[str] = []

    # 病1：日主偏弱无依
    if strength == "偏弱" and strength_score < 0.38:
        bing_list.append("日主偏弱，缺乏根基与印比帮扶")
        yao_list.append("需印比扶身，忌财官过重消耗")

    # 病2：日主偏旺无制
    if strength == "偏旺" and strength_score > 0.72:
        bing_list.append("日主偏旺，需官杀或食伤流通制化")
        yao_list.append("以官杀为药（制旺）或食伤流通为药")

    # 病3：官杀混杂
    if pattern_shen in ("七杀", "正官") and strength == "偏弱":
        bing_list.append("官杀透出而日主弱，官杀为病")
        yao_list.append("以印化杀（正印/偏印）为药")

    # 病4：从格误用扶身
    if "从格" in geju_type:
        bing_list.append("从格命局若强行扶身则逆势为病")
        yao_list.append(f"顺势取{pattern_shen}方向，以顺用为药")

    # 无明确病时给出通用描述
    if not bing_list:
        bing_list.append("命局无显著极端偏差，主要矛盾在岁运引动")
        yao_list.append("重点观察大运流年是否引动格神或用神")

    # 药方向十神（供仲裁器给对应事件命题加分）
    yao_favor_shishen: list[str] = []
    if strength == "偏弱" and strength_score < 0.38:
        yao_favor_shishen.extend(["正印", "偏印", "比肩", "劫财"])
    if strength == "偏旺" and strength_score > 0.72:
        yao_favor_shishen.extend(["正官", "七杀", "食神", "伤官"])
    if pattern_shen in ("七杀", "正官") and strength == "偏弱":
        yao_favor_shishen.extend(["正印", "偏印"])
    if "从格" in geju_type:
        yao_favor_shishen.extend([pattern_shen])

    bing = "；".join(bing_list)
    yao = "；".join(yao_list)

    return {
        "bing": bing,
        "yao": yao,
        "yao_favor_shishen": list(dict.fromkeys(yao_favor_shishen)),  # 去重
        "rationale": f"病={bing}｜药={yao}",
        "confidence": 0.60 if len(bing_list) >= 2 else 0.52,
    }


# ── claim 构造 ────────────────────────────────────────────────────────────────

def _make_claim(
    case_id: str,
    domain: str,
    claim: str,
    claim_type: str,
    confidence_score: float,
    confidence_tier: str,
    confidence_note: str,
    rule_note: str,
    probabilistic: bool = False,
    extra_metadata: dict[str, Any] | None = None,
) -> V5Claim:
    eid = _stable_id("ev", case_id, domain, claim[:30])
    cid = _stable_id("cl", case_id, domain, claim[:30])
    metadata: dict[str, Any] = {
        "case_id": case_id,
        "runner_state": "ziping_independent",
        "source_scope": "ziping_independent_runner",
    }
    if extra_metadata:
        metadata.update(extra_metadata)
    return V5Claim(
        claim_id=cid,
        school="ziping",
        domain=domain,
        claim=claim,
        claim_type=claim_type,  # type: ignore[arg-type]
        stance="support",
        polarity="neutral",
        confidence=V5Confidence(tier=confidence_tier, score=confidence_score, note=confidence_note),
        evidence=[
            V5Evidence(
                evidence_id=eid,
                source="engine/v5/ziping_runner.py",
                text=rule_note,
                node_refs=["chart:root"],
                rule_ids=[],
                metadata={"source_scope": "ziping_independent_runner"},
            )
        ],
        probabilistic=probabilistic,
        falsifiable="若反馈显示该结构条件长期不能提升对应领域命中率，则本命题需降权。",
        metadata=metadata,
    )


# ── 主入口 ────────────────────────────────────────────────────────────────────

def run_ziping_independent(chart: dict[str, Any], case_id: str) -> list[V5Claim]:
    """子平独立分析 runner：输入 chart DTO，输出 V5Claim 列表。

    ponytail: 只做两层：旺衰判断 + 格局用神识别。
    输出两条结构命题，覆盖"总体"与"事业"域。
    后续可扩展更多层。
    """
    claims: list[V5Claim] = []

    # L1: 月令旺衰
    l1 = _assess_daymaster_strength(chart)
    dm = l1.get("day_master", "")
    strength = l1.get("strength", "中和")
    score = float(l1.get("score", 0.5))
    rationale = str(l1.get("rationale", ""))
    confidence_score = min(0.72, max(0.38, 0.55 + (score - 0.5) * 0.4))

    claims.append(_make_claim(
        case_id=case_id,
        domain="总体",
        claim=f"子平独立推导：日主{dm}月令旺衰判定={strength}（得分{score:.2f}）。{rationale}",
        claim_type="structure_claim",
        confidence_score=confidence_score,
        confidence_tier="★★★★" if confidence_score >= 0.65 else "★★★",
        confidence_note="子平独立 L1 旺衰判断，基于月令/四干/藏干轻量权重",
        rule_note=rationale,
    ))

    # L2: 格局用神
    l2 = _identify_pattern_yongshen(chart)
    pattern = l2.get("pattern", "未知")
    yongshen = l2.get("yongshen", "待判")
    l2_rationale = str(l2.get("rationale", ""))

    claims.append(_make_claim(
        case_id=case_id,
        domain="事业",
        claim=f"子平独立推导：{pattern}，用神={yongshen}。{l2_rationale}",
        claim_type="structure_claim",
        confidence_score=0.60,
        confidence_tier="★★★",
        confidence_note="子平独立 L2 格局用神识别，轻量推导，需结合五派仲裁复核",
        rule_note=l2_rationale,
    ))

    # L3: 格局类型（正格 / 从格 / 特殊格）
    l3 = _identify_geju_type(chart, l1, l2)
    l3_rationale = str(l3.get("rationale", ""))
    geju_type = str(l3.get("geju_type", "正格"))
    constraint = str(l3.get("constraint", ""))
    l3_score = float(l3.get("confidence", 0.55))
    l3_tier = "★★★★" if l3_score >= 0.65 else "★★★"

    claims.append(_make_claim(
        case_id=case_id,
        domain="总体",
        claim=f"格局大类裁决：{geju_type}。约束方向:{constraint}。{l3_rationale}",
        claim_type="structure_claim",
        confidence_score=l3_score,
        confidence_tier=l3_tier,
        confidence_note="子平独立 L3 格局类型识别；正格/从格/特殊格为后续事件判断设定约束",
        rule_note=l3_rationale,
        extra_metadata={
            "layer": "L3_geju_type",
            "geju_type": geju_type,
            "favor_shishen": list(l3.get("favor", [])),
            "avoid_shishen": list(l3.get("avoid", [])),
            "constraint_text": constraint,
        },
    ))

    # L5: 病药识别（命局核心矛盾 + 解决方向）
    l5 = _identify_bingyao(chart, l1, l2, l3)
    l5_rationale = str(l5.get("rationale", ""))
    bing = str(l5.get("bing", ""))
    yao = str(l5.get("yao", ""))
    l5_score = float(l5.get("confidence", 0.52))
    l5_tier = "★★★★" if l5_score >= 0.65 else "★★★"

    claims.append(_make_claim(
        case_id=case_id,
        domain="总体",
        claim=f"病药裁决——病：{bing}。药：{yao}。",
        claim_type="structure_claim",
        confidence_score=l5_score,
        confidence_tier=l5_tier,
        confidence_note="子平独立 L5 病药识别；命局核心矛盾与解决方向，约束所有事件命题",
        rule_note=l5_rationale,
        extra_metadata={
            "layer": "L5_bingyao",
            "yao_favor_shishen": list(l5.get("yao_favor_shishen", [])),
        },
    ))

    return claims


# ── L2 统一命题契约 ──────────────────────────────────────────────────────────

_ZIPING_STRUCTURE_TASKS = {"structure.overview"}
_ZIPING_BINARY_TASKS = {"marriage.late_marriage", "career.role_change"}


def _claim_evidence(
    features: ChartFeatureVector,
    *,
    rule_id: str,
    feature_refs: tuple[str, ...],
    text: str,
) -> Evidence:
    raw = "|".join((features.chart_id, rule_id, *feature_refs))
    return Evidence(
        evidence_id="evidence-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20],
        fact_refs=("four_pillars.day", "four_pillars.month"),
        feature_refs=feature_refs,
        rule_id=rule_id,
        text=text,
    )


def _generate_binary_claims(
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    task: BlindTask,
) -> list[Claim]:
    """从四柱十神结构推导二元事件命题（晚婚/职业变动）。"""
    if task.task_id == "marriage.late_marriage":
        return _late_marriage_claim(chart, features, task)
    if task.task_id == "career.role_change":
        return _role_change_claim(chart, features, task)
    return []


def _late_marriage_claim(
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    task: BlindTask,
) -> list[Claim]:
    """晚婚推导：配偶星弱 + 日支被冲/刑 → 晚婚概率高。"""
    sex = chart.sex_marker
    # 男命看财星（正财+偏财），女命看官星（正官+七杀）
    if sex in ("乾", "男", "M"):
        spouse_count = features.ten_god_counts.get("正财", 0) + features.ten_god_counts.get("偏财", 0)
        spouse_label = "财星"
    elif sex in ("坤", "女", "F"):
        spouse_count = features.ten_god_counts.get("正官", 0) + features.ten_god_counts.get("七杀", 0)
        spouse_label = "官星"
    else:
        return []

    # 日支是否被冲
    day_pillar = str(chart.four_pillars.get("day", ""))
    day_branch = day_pillar[1] if len(day_pillar) >= 2 else ""
    day_branch_clashed = any(
        day_branch in pair for pair in features.chong_pairs
    ) if day_branch else False

    # 触发条件：配偶星少（≤1）且日支被冲，或配偶星完全不见
    triggers: list[str] = []
    if spouse_count == 0:
        triggers.append(f"四柱不见{spouse_label}")
    if spouse_count <= 1 and day_branch_clashed:
        triggers.append(f"{spouse_label}仅{spouse_count}处且日支{day_branch}被冲")
    if features.branch_conflict_intensity >= 0.6 and spouse_count <= 1:
        triggers.append(f"地支冲突强度={features.branch_conflict_intensity:.2f}且{spouse_label}薄弱")

    if not triggers:
        return []

    rule_id = "ZIPING-LATE-MARRIAGE-V1"
    description = "；".join(triggers)
    evidence = _claim_evidence(
        features,
        rule_id=rule_id,
        feature_refs=("ten_god_counts.正财", "ten_god_counts.偏财", "ten_god_counts.正官", "ten_god_counts.七杀", "branch_conflict_intensity"),
        text=f"晚婚信号：{description}。",
    )
    # 使用宽泛 lifetime 窗口
    window = TimeWindow(start_year=1900, end_year=2100, label="lifetime")
    claim = Claim(
        claim_id=stable_claim_id("ziping", task.task_id, features.chart_id, rule_id),
        school_id="ziping",
        task_id=task.task_id,
        claim_type="event_claim",
        stance="support",
        statement=f"子平命局{spouse_label}结构指向晚婚倾向：{description}。",
        evidence=(evidence,),
        falsifier="若命主在统一年龄阈值前已婚，则本命题证伪。",
        time_window=window,
        confidence_basis=f"基于四柱{spouse_label}计数与日支冲合关系的确定性推导。",
        domain=task.domain,
        polarity="negative",
        magnitude=min(1.0, 0.4 + 0.2 * len(triggers)),
        confidence=0.7,
        high_risk=task.high_risk,
        applicability_snapshot={
            "sex_marker": sex,
            "spouse_count": spouse_count,
            "day_branch_clashed": day_branch_clashed,
            "branch_conflict_intensity": features.branch_conflict_intensity,
        },
    )
    validate_claim_evidence(claim, chart, features)
    return [claim]


def _role_change_claim(
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    task: BlindTask,
) -> list[Claim]:
    """职业变动推导：食伤制杀/官杀混杂/伤官见官 → 变动概率高。"""
    output_count = features.ten_god_counts.get("食神", 0) + features.ten_god_counts.get("伤官", 0)
    official_count = features.ten_god_counts.get("正官", 0) + features.ten_god_counts.get("七杀", 0)

    triggers: list[str] = []
    if features.mixed_official_kill:
        triggers.append("官杀混杂")
    if output_count >= 2 and official_count >= 1:
        triggers.append(f"食伤{output_count}处制杀{official_count}处")
    if features.ten_god_counts.get("伤官", 0) >= 1 and features.ten_god_counts.get("正官", 0) >= 1:
        triggers.append("伤官见官")
    if features.branch_conflict_intensity >= 0.5:
        triggers.append(f"地支冲突强度={features.branch_conflict_intensity:.2f}")

    if not triggers:
        return []

    rule_id = "ZIPING-ROLE-CHANGE-V1"
    description = "；".join(triggers)
    evidence = _claim_evidence(
        features,
        rule_id=rule_id,
        feature_refs=("ten_god_counts.食神", "ten_god_counts.伤官", "ten_god_counts.正官", "ten_god_counts.七杀", "mixed_official_kill", "branch_conflict_intensity"),
        text=f"职业变动信号：{description}。",
    )
    window = TimeWindow(start_year=1900, end_year=2100, label="lifetime")
    claim = Claim(
        claim_id=stable_claim_id("ziping", task.task_id, features.chart_id, rule_id),
        school_id="ziping",
        task_id=task.task_id,
        claim_type="event_claim",
        stance="support",
        statement=f"子平命局十神结构指向显著职业变动倾向：{description}。",
        evidence=(evidence,),
        falsifier="若命主职业历程中无显著角色或岗位变化记录，则本命题证伪。",
        time_window=window,
        confidence_basis="基于四柱官杀与食伤结构关系的确定性推导。",
        domain=task.domain,
        polarity="negative",
        magnitude=min(1.0, 0.4 + 0.15 * len(triggers)),
        confidence=0.7,
        high_risk=task.high_risk,
        applicability_snapshot={
            "output_count": output_count,
            "official_count": official_count,
            "mixed_official_kill": features.mixed_official_kill,
            "branch_conflict_intensity": features.branch_conflict_intensity,
        },
    )
    validate_claim_evidence(claim, chart, features)
    return [claim]


def generate_claims(
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    task: BlindTask,
) -> list[Claim]:
    """从冻结命盘与 cfv-v1 推导子平命题（结构+二元事件）。"""
    if task.task_id in _ZIPING_BINARY_TASKS:
        if features.evidence_completeness == "partial":
            return []
        return _generate_binary_claims(chart, features, task)
    if task.task_id not in _ZIPING_STRUCTURE_TASKS:
        raise TaskUnsupported(f"ziping does not support task: {task.task_id}")
    if features.evidence_completeness != "full":
        return []

    claims: list[Claim] = []
    balance = features.supporting_count - features.draining_count
    strength_rule = "ZIPING-STRENGTH-V1"
    if balance <= -3 and features.rooted_count <= 1:
        strength = "身弱"
    elif balance >= 3 and features.rooted_count >= 2:
        strength = "身强"
    else:
        strength = ""
    if strength:
        evidence = _claim_evidence(
            features,
            rule_id=strength_rule,
            feature_refs=("supporting_count", "draining_count", "rooted_count", "monthly_command_favorable"),
            text=(f"生扶计数={features.supporting_count}，克泄耗计数={features.draining_count}，"
                  f"通根数={features.rooted_count}，月令帮扶={features.monthly_command_favorable}。"),
        )
        claim = Claim(
            claim_id=stable_claim_id("ziping", task.task_id, features.chart_id, strength_rule),
            school_id="ziping",
            task_id=task.task_id,
            claim_type="structure_claim",
            stance="support",
            statement=f"子平旺衰主线判为{strength}结构。",
            evidence=(evidence,),
            falsifier=f"若按同一子平口径独立复核不呈{strength}，则本结构命题证伪。",
            time_window=None,
            confidence_basis="旺衰由 cfv-v1 的生扶/克泄耗差、通根与月令信号共同形成。",
            domain=task.domain,
            polarity="positive" if strength == "身强" else "negative",
            magnitude=min(1.0, abs(balance) / 8.0),
            confidence=0.7,
            high_risk=task.high_risk,
            applicability_snapshot={
                "supporting_count": features.supporting_count,
                "draining_count": features.draining_count,
                "rooted_count": features.rooted_count,
                "monthly_command_favorable": features.monthly_command_favorable,
            },
        )
        validate_claim_evidence(claim, chart, features)
        claims.append(claim)

    relation_rule = "ZIPING-OUTPUT-OFFICIAL-V1"
    output_count = features.ten_god_counts.get("食神", 0) + features.ten_god_counts.get("伤官", 0)
    official_count = features.ten_god_counts.get("正官", 0) + features.ten_god_counts.get("七杀", 0)
    if output_count and official_count:
        evidence = _claim_evidence(
            features,
            rule_id=relation_rule,
            feature_refs=("ten_god_counts.食神", "ten_god_counts.伤官", "ten_god_counts.正官", "ten_god_counts.七杀"),
            text=f"食伤计数={output_count}，官杀计数={official_count}，两组结构同时存在。",
        )
        claim = Claim(
            claim_id=stable_claim_id("ziping", task.task_id, features.chart_id, relation_rule),
            school_id="ziping",
            task_id=task.task_id,
            claim_type="structure_claim",
            stance="support",
            statement="食伤与官杀并见，格局成立需审查制化与破格关系。",
            evidence=(evidence,),
            falsifier="若十神复核显示食伤或官杀任一结构不存在，则本命题证伪。",
            time_window=None,
            confidence_basis="仅陈述十神结构并见，不把并见直接判成唯一现实事件。",
            domain=task.domain,
            polarity="neutral",
            magnitude=min(1.0, (output_count + official_count) / 8.0),
            confidence=0.6,
            high_risk=task.high_risk,
            applicability_snapshot={"output_count": output_count, "official_count": official_count},
        )
        validate_claim_evidence(claim, chart, features)
        claims.append(claim)

    return claims


# ── self-check ────────────────────────────────────────────────────────────────

def _demo() -> None:  # ponytail: runnable self-check
    chart = {
        "case_id": "C-TEST-ZIPING-IND",
        "pillars": {"year": "庚申", "month": "戊寅", "day": "壬子", "hour": "辛丑"},
        "current_dayun": "壬午",
        "current_year": "丙午（2026 年）",
    }
    claims = run_ziping_independent(chart, "C-TEST-ZIPING-IND")
    print(f"[OK] ziping independent: {len(claims)} claims")
    for c in claims:
        print(f"  {c.domain}: {c.claim[:80]}")
        print(f"    confidence={c.confidence.tier} {c.confidence.score}")


if __name__ == "__main__":
    _demo()
