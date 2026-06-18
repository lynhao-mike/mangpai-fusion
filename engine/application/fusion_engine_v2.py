"""fusion_engine_v2.py · v4.2 三体系融合决策器

加权集成 ziping / dtt / mp 三流派预测信号，输出 final_prediction。
冲突解决：贝叶斯加权；fallback：结构优先（D1 energy 为准）。
"""
from __future__ import annotations

import math
from typing import Any

from engine.domain.prediction import (
    DttPredictionSignal,
    EventCandidate,
    FinalPrediction,
    MpPredictionSignal,
    ZipingPredictionSignal,
)
from engine.infrastructure.weight_repository import load_school_weights

_EVENT_DOMAIN_MAP: dict[str, str] = {
    "career_pressure": "事业",
    "wealth_activity": "财运",
    "relationship_tension": "婚姻",
    "imbalance_index": "健康",
    "seasonal_pressure": "性格",
    "transformation_likelihood": "财运",
}


def _bayesian_combine(signals: list[tuple[float, float]]) -> float:
    """贝叶斯加权合并：signals = [(probability, weight), ...]。
    
    使用对数优势（log-odds）加权平均后转回概率，避免 naive 乘法过度极端化。
    """
    if not signals:
        return 0.5
    log_odds_sum = 0.0
    weight_sum = 0.0
    for prob, weight in signals:
        prob = max(0.001, min(0.999, prob))
        log_odds_sum += weight * math.log(prob / (1.0 - prob))
        weight_sum += weight
    if weight_sum == 0:
        return 0.5
    combined_log_odds = log_odds_sum / weight_sum
    return 1.0 / (1.0 + math.exp(-combined_log_odds))


def _detect_conflict(
    ziping_val: float,
    dtt_val: float,
    mp_val: float,
    threshold: float = 0.35,
) -> bool:
    """三派信号差距超过阈值时视为冲突。"""
    vals = sorted([ziping_val, dtt_val, mp_val])
    return (vals[-1] - vals[0]) >= threshold


def build_final_prediction(
    ziping: ZipingPredictionSignal,
    dtt: DttPredictionSignal,
    mp: MpPredictionSignal,
    *,
    domain_hint: str = "事业",
    runtime_school_weights: dict[str, float] | None = None,
) -> FinalPrediction:
    """融合三流派信号，输出 FinalPrediction。

    Args:
        ziping: 子平预测信号。
        dtt: 滴天髓预测信号。
        mp: 盲派象法预测信号。
        domain_hint: 主分析领域（用于加载对应权重）。
        runtime_school_weights: RL 更新后的动态权重（覆盖文件权重）。
    """
    weights = runtime_school_weights or load_school_weights(domain_hint)
    wz = weights.get("ziping", 0.42)
    wd = weights.get("tiaohou_ditiansui", 0.32)
    wm = weights.get("blind", 0.26)

    # ── 核心事件候选合并 ─────────────────────────────────────────
    candidates: list[EventCandidate] = []
    conflict_used = False

    # 1. 事业压力
    career_signals = [(ziping.career_pressure, wz), (dtt.seasonal_pressure, wd)]
    if _detect_conflict(ziping.career_pressure, dtt.seasonal_pressure, dtt.imbalance_index):
        conflict_used = True
        # fallback: 子平结构优先（D1 energy 权重 ×1.5）
        career_prob = _bayesian_combine([(ziping.career_pressure, wz * 1.5), (dtt.seasonal_pressure, wd)])
    else:
        career_prob = _bayesian_combine(career_signals)
    candidates.append(EventCandidate("career_change", career_prob, "ziping+dtt"))

    # 2. 财运活跃
    wealth_prob = _bayesian_combine([
        (ziping.wealth_activity, wz),
        (dtt.transformation_likelihood, wd),
    ])
    candidates.append(EventCandidate("wealth_shift", wealth_prob, "ziping+dtt"))

    # 3. 婚姻张力
    rel_prob = _bayesian_combine([
        (ziping.relationship_tension, wz),
        (dtt.imbalance_index * 0.6, wd),
    ])
    candidates.append(EventCandidate("relationship_shift", rel_prob, "ziping+dtt"))

    # 4. 盲派象法候选事件（mp 信号贡献）
    for sym_event in mp.symbolic_events:
        mp_prob = _bayesian_combine([
            (sym_event.probability_weight, wm),
            (mp.max_passed_layers / 3.0, wm * 0.5),
        ])
        for meaning in sym_event.meaning_candidates[:2]:  # 最多取前2个候选
            candidates.append(EventCandidate(meaning, mp_prob, "blind_mp"))

    # ── 排序 + 去重（保留最高概率）───────────────────────────────
    seen: dict[str, float] = {}
    for c in candidates:
        if c.event not in seen or c.probability > seen[c.event]:
            seen[c.event] = c.probability
    deduped = sorted(
        [EventCandidate(e, p, "fusion") for e, p in seen.items()],
        key=lambda x: x.probability,
        reverse=True,
    )

    # ── 整体置信度：三派信号熵加权均值 ───────────────────────────
    signal_probs = [
        ziping.career_pressure, ziping.wealth_activity,
        dtt.imbalance_index, dtt.transformation_likelihood,
    ]
    if mp.symbolic_events:
        signal_probs.append(
            sum(e.probability_weight for e in mp.symbolic_events) / len(mp.symbolic_events)
        )
    overall_confidence = sum(signal_probs) / len(signal_probs) if signal_probs else 0.5

    explanation_chain = {
        "ziping_reason": {
            "career_pressure": ziping.career_pressure,
            "wealth_activity": ziping.wealth_activity,
            "day_master_strength": ziping.day_master_strength,
            "rule_signal_count": ziping.rule_signal_count,
        },
        "dtt_reason": {
            "imbalance_index": dtt.imbalance_index,
            "seasonal_pressure": dtt.seasonal_pressure,
            "transformation_likelihood": dtt.transformation_likelihood,
        },
        "mp_reason": {
            "symbolic_events": [e.to_dict() for e in mp.symbolic_events],
            "max_passed_layers": mp.max_passed_layers,
        },
        "weights_used": {"ziping": wz, "tiaohou_ditiansui": wd, "blind": wm},
    }

    return FinalPrediction(
        event_candidates=deduped,
        explanation_chain=explanation_chain,
        conflict_resolution_used=conflict_used,
        overall_confidence=min(overall_confidence, 1.0),
    )
