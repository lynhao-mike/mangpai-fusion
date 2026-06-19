"""prediction_layer.py · v4.2 概率预测输出层

接收 FinalPrediction + FusionFindings，生成可序列化的 PredictionOutput。
含事件候选列表、概率分布、时间窗口估算与 learning_feedback_id。
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from engine.domain.dual_engine import FusionFindings
from engine.domain.prediction import FinalPrediction, PredictionOutput, TimeWindow
from engine.yingqi.types import GateResult


def _estimate_time_window(gate_results: list[GateResult]) -> TimeWindow:
    """复用 D3 三层门结果估算事件时间窗口。

    逻辑：取通过门最多的 gate 年份作为 peak；±2 年为窗口；
    L3 全通的 gate 年份优先。
    """
    current_year = datetime.now(timezone.utc).year
    
    # 防御：过滤无效 gate_results
    valid_gates = [g for g in gate_results if hasattr(g, 'passed_layers') and hasattr(g, 'year')]
    passed = [g for g in valid_gates if g.passed_layers >= 1]
    
    if not passed:
        return TimeWindow(current_year, current_year + 3, current_year + 1)

    # 优先选 L3 全通
    full_pass = [g for g in passed if g.passed_layers == 3]
    anchor = full_pass if full_pass else passed
    
    # 取最近未来年份 or 最高层年份
    future = [g for g in anchor if g.year >= current_year]
    if future:
        peak_gate = min(future, key=lambda g: g.year)
    else:
        peak_gate = max(anchor, key=lambda g: g.passed_layers)

    peak_year = peak_gate.year
    return TimeWindow(
        start_year=max(current_year, peak_year - 1),  # 不早于当前年
        end_year=peak_year + 2,
        peak_year=peak_year,
    )


def _make_feedback_id(case_id: str) -> str:
    """生成 learning_feedback_id：UUID4 + case_id 短 hash + timestamp。
    
    增加 timestamp 降低碰撞风险，确保同一 case 多次预测生成不同 ID。
    """
    short = hashlib.sha1(case_id.encode()).hexdigest()[:8]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"PFID-{short}-{timestamp}-{uuid.uuid4().hex[:6]}"


def build_prediction_output(
    final_prediction: FinalPrediction,
    fusion_findings: FusionFindings,
    gate_results: list[GateResult],
) -> PredictionOutput:
    """将融合决策器输出包装为 PredictionOutput。"""
    prob_dist = {
        c.event: round(c.probability, 4)
        for c in final_prediction.event_candidates
    }
    time_window = _estimate_time_window(gate_results)

    return PredictionOutput(
        event_candidates=[c.to_dict() for c in final_prediction.event_candidates],
        probability_distribution=prob_dist,
        time_window=time_window.to_dict(),
        confidence_score=final_prediction.overall_confidence,
        explanation_chain=final_prediction.explanation_chain,
        conflict_resolution_used=final_prediction.conflict_resolution_used,
        learning_feedback_id=_make_feedback_id(fusion_findings.case_id),
    )
