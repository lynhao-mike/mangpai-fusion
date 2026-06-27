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

from engine.predicates.types import (
    GAN_TO_WUXING,
    ZHI_CANGGAN_TABLE,
    ZHI_TO_WUXING,
)
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

# 十神映射：日主天干 × 对方天干 → 十神名称
_GAN_WUXING = GAN_TO_WUXING  # 复用
_GAN_YINYANG: dict[str, str] = {
    "甲": "阳", "乙": "阴", "丙": "阳", "丁": "阴", "戊": "阳",
    "己": "阴", "庚": "阳", "辛": "阴", "壬": "阳", "癸": "阴",
}

# 五行相生：a → b（a 生 b）
_SHENG: dict[str, str] = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
# 五行相克：a → b（a 克 b）
_KE: dict[str, str] = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}


def _shishen(day_master: str, target: str) -> str:
    """计算 target 天干相对于 day_master 的十神。"""
    dm_wx = _GAN_WUXING.get(day_master, "")
    t_wx = _GAN_WUXING.get(target, "")
    dm_yin = _GAN_YINYANG.get(day_master, "")
    t_yin = _GAN_YINYANG.get(target, "")

    if dm_wx == t_wx:
        return "比肩" if dm_yin == t_yin else "劫财"
    if _SHENG.get(dm_wx) == t_wx:
        return "食神" if dm_yin == t_yin else "伤官"
    if _KE.get(dm_wx) == t_wx:
        return "偏财" if dm_yin == t_yin else "正财"
    if _SHENG.get(t_wx) == dm_wx:
        return "偏印" if dm_yin == t_yin else "正印"
    if _KE.get(t_wx) == dm_wx:
        return "七杀" if dm_yin == t_yin else "正官"
    return "未知"


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

    if not day_gan or not month_gan or not month_zhi:
        return {"pattern": "未知", "yongshen": "待判", "rationale": "信息不足"}

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
) -> V5Claim:
    eid = _stable_id("ev", case_id, domain, claim[:30])
    cid = _stable_id("cl", case_id, domain, claim[:30])
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
        metadata={
            "case_id": case_id,
            "runner_state": "ziping_independent",
            "source_scope": "ziping_independent_runner",
        },
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
