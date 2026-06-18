"""prediction_signals.py · v4.2 三流派预测信号提取层

从现有 D1-D4 findings 中提取三流派可融合预测信号。
不改变任何上游 findings；只做数值提炼与归一化。
"""
from __future__ import annotations

from engine.domain.dual_engine import TheoryFindings
from engine.domain.prediction import (
    DttPredictionSignal,
    MpPredictionSignal,
    SymbolicEventCandidate,
    ZipingPredictionSignal,
)
from engine.energy.types import EnergyFindings
from engine.picture.types import PictureFindings
from engine.yingqi.types import GateResult


# ── 提取函数 ──────────────────────────────────────────────────

def extract_ziping_signal(
    energy: EnergyFindings,
    theory: TheoryFindings,
) -> ZipingPredictionSignal:
    """从 D1 能量 + 理论触发规则提取子平预测信号。"""
    dms = theory.day_master_strength  # 0-1，来自 calc_gan_strength

    # 身强 → 事业压力大（须外泄），身弱 → 财运压力大
    career_pressure = dms if dms >= 0.5 else (1.0 - dms) * 0.6
    wealth_activity = energy.energy_level.score * (1.0 - abs(dms - 0.5))

    # 冲突规则比例 → 婚姻张力
    ziping_count = theory.rule_count_by_system.get("ziping", 0)
    total_count = sum(theory.rule_count_by_system.values()) or 1
    relationship_tension = min(ziping_count / total_count, 1.0) * 0.8

    return ZipingPredictionSignal(
        career_pressure=min(career_pressure, 1.0),
        wealth_activity=min(wealth_activity, 1.0),
        relationship_tension=relationship_tension,
        day_master_strength=dms,
        rule_signal_count=total_count,
    )


def extract_dtt_signal(picture: PictureFindings) -> DttPredictionSignal:
    """从 D2 画像（调候、五合）提取滴天髓预测信号。"""
    tiaohou = picture.tiaohou
    if tiaohou is None:
        return DttPredictionSignal(
            imbalance_index=0.5,
            seasonal_pressure=0.5,
            transformation_likelihood=0.0,
        )

    # tiaohou 有 balance_score（越接近1越平衡）
    balance = getattr(tiaohou, "balance_score", 0.5)
    imbalance = 1.0 - float(balance)

    # 五合成化数量 → 转化概率
    wuhe_count = len(picture.wuhe_relations)
    transformation = min(wuhe_count * 0.25, 1.0)

    # 调候缺失的五行数 → 季节压力
    missing = getattr(tiaohou, "missing_elements", [])
    seasonal = min(len(missing) * 0.2, 1.0)

    return DttPredictionSignal(
        imbalance_index=min(imbalance, 1.0),
        seasonal_pressure=seasonal,
        transformation_likelihood=transformation,
    )


# Domain → meaning candidates 映射（最小集）
_DOMAIN_MEANINGS: dict[str, list[str]] = {
    "婚姻": ["婚变/离合", "情感纠葛", "配偶健康"],
    "财运": ["财源增减", "投资置业", "破财风险"],
    "事业": ["职位变动", "创业机遇", "事业受挫"],
    "健康": ["伤病风险", "手术外伤", "慢性耗损"],
    "学业": ["考学升迁", "学业受阻"],
    "六亲": ["六亲变故", "人际争端"],
    "其他": ["意外变化"],
}


def extract_mp_signal(gate_results: list[GateResult]) -> MpPredictionSignal:
    """从 D3 应期门结果提取盲派象法预测信号。"""
    if not gate_results:
        return MpPredictionSignal()

    max_layers = max(g.passed_layers for g in gate_results)
    events: list[SymbolicEventCandidate] = []

    for gate in gate_results:
        if gate.passed_layers < 1:
            continue
        symbol = f"{gate.candidate_event}({gate.year}年)"
        weight = gate.passed_layers / 3.0
        if gate.confidence is not None:
            weight = (weight + gate.confidence.percent) / 2.0
        meanings = (
            list(gate.event_type_hypotheses)
            if gate.event_type_hypotheses
            else _DOMAIN_MEANINGS.get(gate.domain, ["事件待定"])
        )
        events.append(SymbolicEventCandidate(
            symbol=symbol,
            meaning_candidates=meanings,
            probability_weight=min(weight, 1.0),
        ))

    return MpPredictionSignal(symbolic_events=events, max_passed_layers=max_layers)
