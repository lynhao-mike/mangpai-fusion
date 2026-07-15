"""engine/v5/ditiansui_runner.py · 滴天髓独立分析 runner。

从 chart DTO 直接推导滴天髓核心两层：
  L1: 气势/流通判断（五行偏枯/流通/一气/两停）
  L2: 寒暖调候判断（冬火需暖 / 夏水需润 / 燥湿平衡）

不依赖旧 D1-D4 流程，直接输出 V5Claim 列表，
与 ziping_runner 平级作为结构合法性命题来源。

ponytail: 只实现能改善 V5Claim 精度的最小推导，
不写完整命理专家系统。
"""

from __future__ import annotations

import hashlib
from typing import Any

from engine.claims import Claim, Evidence, TaskUnsupported, stable_claim_id, validate_claim_evidence
from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindTask
from engine.features import ChartFeatureVector
from engine.v5.domain import V5Claim, V5Confidence, V5Evidence


# ── 常量 ──────────────────────────────────────────────────────────────────────

_WUXING_CHARS: dict[str, str] = {
    "木": "甲乙寅卯",
    "火": "丙丁巳午",
    "土": "戊己辰戌丑未",
    "金": "庚辛申酉",
    "水": "壬癸亥子",
}

# 月支 → 季节冷暖属性
_MONTH_TEMPERATURE: dict[str, str] = {
    "亥": "寒", "子": "寒", "丑": "寒",  # 冬季
    "寅": "温", "卯": "温", "辰": "温",  # 春季
    "巳": "热", "午": "热", "未": "热",  # 夏季
    "申": "凉", "酉": "凉", "戌": "凉",  # 秋季
}

# 月支 → 燥湿属性（辰戌丑未四库特殊）
_MONTH_MOISTURE: dict[str, str] = {
    "辰": "湿", "丑": "湿", "亥": "湿", "子": "湿", "壬": "湿",  # 水土之月
    "戌": "燥", "未": "燥", "午": "燥", "巳": "燥",  # 火燥之月
}


def _stable_id(*parts: object) -> str:
    raw = "|".join(str(p) for p in parts)
    return "dtscl-" + hashlib.sha256(raw.encode()).hexdigest()[:12]


def _chart_pillars_text(chart: dict[str, Any]) -> str:
    pillars = chart.get("pillars") or {}
    if isinstance(pillars, dict):
        return "".join(str(pillars.get(key, "")) for key in ("year", "month", "day", "hour"))
    if isinstance(pillars, list):
        return "".join(str(p) for p in pillars)
    return ""


def _month_zhi(chart: dict[str, Any]) -> str:
    pillars = chart.get("pillars") or {}
    if isinstance(pillars, dict):
        month = str(pillars.get("month", ""))
        return month[1] if len(month) >= 2 else str(chart.get("month_branch", ""))
    if isinstance(pillars, list) and len(pillars) >= 2:
        return str(pillars[1])[1] if len(str(pillars[1])) >= 2 else ""
    return ""


def _day_gan(chart: dict[str, Any]) -> str:
    pillars = chart.get("pillars") or {}
    if isinstance(pillars, dict):
        day = str(pillars.get("day", ""))
        return day[:1] if day else str(chart.get("day_stem", ""))
    if isinstance(pillars, list) and len(pillars) >= 3:
        return str(pillars[2])[:1]
    return ""


def _wuxing_counts(pillars_text: str) -> dict[str, int]:
    return {wx: sum(1 for c in pillars_text if c in chars) for wx, chars in _WUXING_CHARS.items()}


# ── L1: 气势 / 流通判断 ────────────────────────────────────────────────────────

def _assess_qi_flow(chart: dict[str, Any]) -> dict[str, Any]:
    """滴天髓气势与流通判断。

    返回 pattern：
      - 一气偏旺（single_dominant）：某行占 >= 5 个字位
      - 两停偏枯（bi_polar）：两行合计 >= 6，其他不显
      - 流通畅达（circulating）：五行覆盖 >= 4 种
      - 偏枯不通（imbalanced）：五行缺 2 种以上
    """
    pillars_text = _chart_pillars_text(chart)
    counts = _wuxing_counts(pillars_text)
    total = sum(counts.values())
    present = sum(1 for v in counts.values() if v > 0)
    dominant_wx, dominant_n = max(counts.items(), key=lambda kv: kv[1])
    missing = [wx for wx, n in counts.items() if n == 0]

    if dominant_n >= 5:
        pattern = "一气偏旺"
        constraint = f"{dominant_wx}气一片，忌逆制冲克，喜顺势流通"
        confidence = 0.62
    elif len(missing) >= 3:
        pattern = "偏枯不通"
        constraint = f"缺{','.join(missing)}，气势不周流，喜岁运补偏"
        confidence = 0.58
    elif present >= 4 and total >= 8:
        pattern = "流通畅达"
        constraint = "五行流通有情，格局清正，喜岁运不逆气势"
        confidence = 0.65
    elif len(missing) == 2:
        pattern = "两停偏枯"
        constraint = f"缺{','.join(missing)}，气势两停，喜岁运引化未见之行"
        confidence = 0.55
    else:
        pattern = "中和可流通"
        constraint = "气势中和，重点看岁运引动"
        confidence = 0.52

    return {
        "pattern": pattern,
        "constraint": constraint,
        "confidence": confidence,
        "counts": counts,
        "missing": missing,
        "dominant": dominant_wx,
        "rationale": f"五行统计={counts}；覆盖={present}种；主气={dominant_wx}({dominant_n})；缺={missing}；气势={pattern}",
    }


# ── L2: 寒暖调候判断 ──────────────────────────────────────────────────────────

def _assess_tiaohou(chart: dict[str, Any], l1: dict[str, Any]) -> dict[str, Any]:
    """寒暖燥湿调候判断。

    冬火（寒月火弱）→ 需暖调候
    夏水（热月水弱）→ 需润调候
    """
    month_zhi = _month_zhi(chart)
    day_gan = _day_gan(chart)
    counts = l1.get("counts", {})

    temperature = _MONTH_TEMPERATURE.get(month_zhi, "")
    moisture = _MONTH_MOISTURE.get(month_zhi, "")

    dm_wx = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
             "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}.get(day_gan, "")

    imbalance_type = "无"
    remedy: list[str] = []
    remedy_wuxing: list[str] = []

    # 冬火寒重 → 需暖
    if temperature == "寒" and dm_wx in ("火", "木") and counts.get("火", 0) < 2:
        imbalance_type = "寒重"
        remedy.append("需火暖局")
        remedy_wuxing.append("火")

    # 夏水弱 → 需润
    if temperature == "热" and dm_wx in ("水", "金") and counts.get("水", 0) < 2:
        imbalance_type = "热重"
        remedy.append("需水润局")
        remedy_wuxing.append("水")

    # 燥重 → 需水润
    if moisture == "燥" and counts.get("水", 0) == 0:
        imbalance_type = "燥重" if imbalance_type == "无" else imbalance_type + "+燥重"
        remedy.append("燥土无水，需癸壬润泽")
        remedy_wuxing.append("水")

    # 湿重 → 需火暖或土制
    if moisture == "湿" and counts.get("火", 0) == 0:
        imbalance_type = "湿重" if imbalance_type == "无" else imbalance_type + "+湿重"
        remedy.append("湿土无火，需丙丁暖之")
        remedy_wuxing.append("火")

    if imbalance_type == "无":
        remedy.append("寒暖燥湿基本平衡，重点看岁运引动")
        confidence = 0.5
    else:
        confidence = 0.6

    return {
        "imbalance_type": imbalance_type,
        "remedy": "；".join(remedy),
        "remedy_wuxing": list(dict.fromkeys(remedy_wuxing)),
        "temperature": temperature,
        "moisture": moisture,
        "confidence": confidence,
        "rationale": f"月支{month_zhi}({temperature}/{moisture})；日主{day_gan}({dm_wx})；失衡={imbalance_type}；补救={'/'.join(remedy)}",
    }


# ── claim 构造 ────────────────────────────────────────────────────────────────

def _make_dts_claim(
    case_id: str,
    domain: str,
    claim: str,
    confidence_score: float,
    confidence_note: str,
    rule_note: str,
    extra_metadata: dict[str, Any] | None = None,
) -> V5Claim:
    eid = _stable_id("ev", case_id, domain, claim[:30])
    cid = _stable_id("cl", case_id, domain, claim[:30])
    tier = "★★★★" if confidence_score >= 0.65 else "★★★" if confidence_score >= 0.5 else "★★"
    metadata: dict[str, Any] = {
        "case_id": case_id,
        "runner_state": "ditiansui_independent",
        "source_scope": "ditiansui_independent_runner",
    }
    if extra_metadata:
        metadata.update(extra_metadata)
    return V5Claim(
        claim_id=cid,
        school="ditiansui",
        domain=domain,
        claim=claim,
        claim_type="structure_claim",
        stance="support",
        polarity="neutral",
        confidence=V5Confidence(tier=tier, score=confidence_score, note=confidence_note),
        evidence=[
            V5Evidence(
                evidence_id=eid,
                source="engine/v5/ditiansui_runner.py",
                text=rule_note,
                node_refs=["chart:root"],
                rule_ids=[],
                metadata={"source_scope": "ditiansui_independent_runner"},
            )
        ],
        probabilistic=False,
        falsifiable="若反馈显示该气势/调候判断长期不能解释格局层次，则本命题需降权。",
        metadata=metadata,
    )


# ── 主入口 ────────────────────────────────────────────────────────────────────

def run_ditiansui_independent(chart: dict[str, Any], case_id: str) -> list[V5Claim]:
    """滴天髓独立分析 runner。

    ponytail: 只做两层：气势/流通 + 寒暖调候。
    输出两条结构命题，与 ziping_runner 平级。
    """
    claims: list[V5Claim] = []

    # L1: 气势 / 流通
    l1 = _assess_qi_flow(chart)
    pattern = str(l1.get("pattern", ""))
    constraint = str(l1.get("constraint", ""))
    l1_score = float(l1.get("confidence", 0.55))
    l1_rationale = str(l1.get("rationale", ""))

    claims.append(_make_dts_claim(
        case_id=case_id,
        domain="总体",
        claim=f"滴天髓气势裁决：{pattern}。{constraint}。{l1_rationale}",
        confidence_score=l1_score,
        confidence_note="滴天髓独立 L1 气势/流通判断",
        rule_note=l1_rationale,
        extra_metadata={
            "layer": "DTS_L1_qi_flow",
            "qi_pattern": pattern,
            "dominant_wuxing": l1.get("dominant", ""),
            "missing_wuxing": list(l1.get("missing", [])),
        },
    ))

    # L2: 寒暖调候
    l2 = _assess_tiaohou(chart, l1)
    imbalance = str(l2.get("imbalance_type", "无"))
    remedy = str(l2.get("remedy", ""))
    l2_score = float(l2.get("confidence", 0.5))
    l2_rationale = str(l2.get("rationale", ""))

    claims.append(_make_dts_claim(
        case_id=case_id,
        domain="总体",
        claim=f"滴天髓调候裁决：寒暖失衡={imbalance}。补救方向：{remedy}。{l2_rationale}",
        confidence_score=l2_score,
        confidence_note="滴天髓独立 L2 寒暖燥湿调候判断",
        rule_note=l2_rationale,
        extra_metadata={
            "layer": "DTS_L2_tiaohou",
            "imbalance_type": imbalance,
            "remedy_wuxing": list(l2.get("remedy_wuxing", [])),
        },
    ))

    return claims


# ── 统一 L2 Claim 入口 ───────────────────────────────────────────────────────

_DTS_CLIMATE_THRESHOLD = 0.65
_DTS_CONCENTRATION_THRESHOLD = 0.50


def _l2_evidence(
    features: ChartFeatureVector,
    *,
    rule_id: str,
    feature_refs: tuple[str, ...],
    text: str,
) -> Evidence:
    raw = f"ditiansui|structure.overview|{features.chart_id}|{rule_id}|{'|'.join(feature_refs)}"
    return Evidence(
        evidence_id="evidence-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20],
        fact_refs=("four_pillars.month",),
        feature_refs=feature_refs,
        rule_id=rule_id,
        text=text,
    )


def generate_claims(
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    task: BlindTask,
) -> list[Claim]:
    """从 cfv-v1 生成最多一条滴天髓结构命题；保留旧 V5 入口并存。"""
    if task.task_id != "structure.overview":
        raise TaskUnsupported(f"ditiansui does not support task: {task.task_id}")
    if features.evidence_completeness == "partial":
        return []

    axis = max(abs(features.cold_warm_axis), abs(features.dry_wet_axis))
    if features.climate_extreme and axis >= _DTS_CLIMATE_THRESHOLD:
        temperature = "寒" if features.cold_warm_axis <= -_DTS_CLIMATE_THRESHOLD else "热" if features.cold_warm_axis >= _DTS_CLIMATE_THRESHOLD else ""
        moisture = "湿" if features.dry_wet_axis <= -_DTS_CLIMATE_THRESHOLD else "燥" if features.dry_wet_axis >= _DTS_CLIMATE_THRESHOLD else ""
        pattern = "、".join(item for item in (temperature, moisture) if item)
        rule_id = "DITIANSUI-STRUCTURE-CLIMATE-EXTREME-V1"
        refs = ("cold_warm_axis", "dry_wet_axis", "climate_extreme", "evidence_completeness")
        evidence = _l2_evidence(
            features,
            rule_id=rule_id,
            feature_refs=refs,
            text=f"cfv-v1 寒暖轴={features.cold_warm_axis:.2f}、燥湿轴={features.dry_wet_axis:.2f}，达到极端阈值。",
        )
        statement = f"滴天髓结构判断：原局寒暖燥湿呈{pattern or '明显'}失衡，属于调候层面的显著结构约束。"
        snapshot = {
            "rule": "climate_extreme",
            "cold_warm_axis": features.cold_warm_axis,
            "dry_wet_axis": features.dry_wet_axis,
            "climate_extreme": features.climate_extreme,
            "evidence_completeness": features.evidence_completeness,
        }
        confidence = 0.66 if features.evidence_completeness == "full" else 0.58
        confidence_basis = "cfv-v1 气候极端标记与至少一条寒暖/燥湿轴达到明确阈值；残缺时降级。"
    elif (
        features.element_concentration >= _DTS_CONCENTRATION_THRESHOLD
        and (bool(features.dominant_element) or bool(features.missing_elements))
    ):
        rule_id = "DITIANSUI-STRUCTURE-QI-CONCENTRATION-V1"
        refs = (
            "element_concentration", "dominant_element", "missing_elements",
            "element_energy", "evidence_completeness",
        )
        missing = "、".join(features.missing_elements) or "无明确缺失"
        evidence = _l2_evidence(
            features,
            rule_id=rule_id,
            feature_refs=refs,
            text=f"主导五行为{features.dominant_element}，集中度={features.element_concentration:.3f}，缺失五行={missing}。",
        )
        statement = f"滴天髓结构判断：五行气势向{features.dominant_element}集中，并见{missing}，形成偏枯或集中结构。"
        snapshot = {
            "rule": "qi_concentration",
            "element_concentration": features.element_concentration,
            "dominant_element": features.dominant_element,
            "missing_elements": features.missing_elements,
            "element_energy": dict(features.element_energy),
            "evidence_completeness": features.evidence_completeness,
        }
        confidence = 0.64 if features.evidence_completeness == "full" else 0.56
        confidence_basis = "cfv-v1 五行集中度达到明确阈值，并可定位主导或缺失五行；残缺时降级。"
    else:
        return []

    claim = Claim(
        claim_id=stable_claim_id("ditiansui", task.task_id, features.chart_id, rule_id),
        school_id="ditiansui",
        task_id=task.task_id,
        claim_type="structure_claim",
        stance="support",
        statement=statement,
        evidence=(evidence,),
        falsifier="若按同一特征版本独立复核时不具备该寒暖燥湿或五行气势结构，则命题证伪。",
        time_window=None,
        confidence_basis=confidence_basis,
        applicability_snapshot=snapshot,
        domain=task.domain,
        polarity="neutral",
        confidence=confidence,
        high_risk=task.high_risk,
    )
    validate_claim_evidence(claim, chart, features)
    return [claim]


# ── self-check ────────────────────────────────────────────────────────────────

def _demo() -> None:
    chart = {
        "case_id": "C-TEST-DTS",
        "pillars": {"year": "庚申", "month": "戊寅", "day": "壬子", "hour": "辛丑"},
    }
    claims = run_ditiansui_independent(chart, "C-TEST-DTS")
    print(f"[OK] ditiansui independent: {len(claims)} claims")
    for c in claims:
        print(f"  {c.domain}: {c.claim[:100]}")
        print(f"    confidence={c.confidence.tier} {c.confidence.score}  meta_layer={c.metadata.get('layer')}")


if __name__ == "__main__":
    _demo()
