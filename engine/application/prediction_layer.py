"""prediction_layer.py · v4.2 概率预测输出层（增强版）

接收 FinalPrediction + FusionFindings，生成可序列化的 PredictionOutput。
含事件候选列表、概率分布、增强时间窗口估算与 learning_feedback_id。

v4.2 增强功能：
- 使用 time_window_estimator.estimate_enhanced_time_window()
- 使用 probability_calibrator 校准概率
- 使用 event_semantics_loader 加载外部化事件语义
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from engine.domain.dual_engine import FusionFindings
from engine.domain.prediction import FinalPrediction, PredictionOutput, TimeWindow
from engine.yingqi.types import GateResult

# v4.2 增强模块导入
try:
    from engine.application.time_window_estimator import (
        estimate_enhanced_time_window,
        estimate_time_window_legacy,
    )
    from engine.application.probability_calibrator import ProbabilityCalibrator
    _ENHANCED_FEATURES_AVAILABLE = True
except ImportError:
    _ENHANCED_FEATURES_AVAILABLE = False


# ── 全局校准器实例（延迟加载）──────────────────────────────
_CALIBRATOR: ProbabilityCalibrator | None = None


def _get_calibrator() -> ProbabilityCalibrator | None:
    """获取全局校准器实例（延迟加载）。"""
    global _CALIBRATOR
    if _CALIBRATOR is None and _ENHANCED_FEATURES_AVAILABLE:
        try:
            calibration_path = Path("engine/calibration_params.json")
            _CALIBRATOR = ProbabilityCalibrator.load(calibration_path)
        except Exception:
            # 降级：校准器加载失败，返回 None
            _CALIBRATOR = None
    return _CALIBRATOR


def _estimate_time_window(
    gate_results: list[GateResult],
    *,
    use_enhanced: bool = True,
    parsed_input: any = None,
) -> TimeWindow:
    """时间窗口估算（支持增强版与遗留版）。

    Args:
        gate_results: D3 应期门结果
        use_enhanced: 是否使用增强版推理（默认 True）
        parsed_input: 可选，用于大运信息提取

    Returns:
        TimeWindow 或 EnhancedTimeWindow（降级为 primary 窗口）
    """
    if use_enhanced and _ENHANCED_FEATURES_AVAILABLE:
        try:
            enhanced = estimate_enhanced_time_window(
                gate_results,
                min_confidence_star=3,
                parsed_input=parsed_input,
            )
            return enhanced.primary  # 返回主窗口
        except Exception:
            # 降级到遗留版
            pass

    # 遗留版本（向后兼容）
    if _ENHANCED_FEATURES_AVAILABLE:
        return estimate_time_window_legacy(gate_results)
    
    # 完全降级：内嵌简化逻辑
    current_year = datetime.now(timezone.utc).year
    valid_gates = [g for g in gate_results if hasattr(g, 'passed_layers') and hasattr(g, 'year')]
    passed = [g for g in valid_gates if g.passed_layers >= 1]
    
    if not passed:
        return TimeWindow(current_year, current_year + 3, current_year + 1)

    full_pass = [g for g in passed if g.passed_layers == 3]
    anchor = full_pass if full_pass else passed
    
    future = [g for g in anchor if g.year >= current_year]
    if future:
        peak_gate = min(future, key=lambda g: g.year)
    else:
        peak_gate = max(anchor, key=lambda g: g.passed_layers)

    peak_year = peak_gate.year
    return TimeWindow(
        start_year=max(current_year, peak_year - 1),
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
    *,
    use_calibration: bool = True,
    parsed_input: any = None,
) -> PredictionOutput:
    """将融合决策器输出包装为 PredictionOutput（v4.2 增强版）。
    
    Args:
        final_prediction: 融合决策器输出
        fusion_findings: 融合 findings
        gate_results: 应期门结果
        use_calibration: 是否使用概率校准（默认 True）
        parsed_input: 可选，用于增强时间窗推理
    
    Returns:
        PredictionOutput 含校准后概率和增强时间窗
    """
    # ── 概率分布：应用校准 ────────────────────────────────────
    calibrator = _get_calibrator() if use_calibration else None
    prob_dist = {}
    
    for c in final_prediction.event_candidates:
        raw_prob = c.probability
        
        # 推断领域（从事件名称）
        domain = _infer_domain_from_event(c.event)
        
        if calibrator:
            calibrated_prob = calibrator.calibrate(
                raw_prob,
                domain,
                method="temperature",  # 默认使用温度缩放
            )
        else:
            calibrated_prob = raw_prob
        
        prob_dist[c.event] = round(calibrated_prob, 4)
    
    # ── 时间窗口：使用增强版推理 ──────────────────────────────
    time_window = _estimate_time_window(
        gate_results,
        use_enhanced=True,
        parsed_input=parsed_input,
    )

    return PredictionOutput(
        event_candidates=[c.to_dict() for c in final_prediction.event_candidates],
        probability_distribution=prob_dist,
        time_window=time_window.to_dict(),
        confidence_score=final_prediction.overall_confidence,
        explanation_chain=final_prediction.explanation_chain,
        conflict_resolution_used=final_prediction.conflict_resolution_used,
        learning_feedback_id=_make_feedback_id(fusion_findings.case_id),
    )


def _infer_domain_from_event(event_name: str) -> str:
    """从事件名称推断领域（简化逻辑）。"""
    keywords = {
        "婚姻": ["婚", "离", "配偶", "恋", "夫妻"],
        "财运": ["财", "钱", "投资", "置业", "破财"],
        "事业": ["职", "升", "创业", "工作", "官"],
        "健康": ["病", "伤", "手术", "健康", "外伤"],
        "学业": ["考", "学", "升学", "毕业"],
        "六亲": ["父", "母", "子", "女", "兄弟"],
    }
    
    for domain, kws in keywords.items():
        if any(kw in event_name for kw in kws):
            return domain
    
    return "其他"
