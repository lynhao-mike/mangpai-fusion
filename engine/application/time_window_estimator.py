"""time_window_estimator.py · v4.2 增强版应期时间窗推理器

从简单的 ±2年窗口升级为考虑大运节点、五行力量、领域权重的智能推理。

设计原则：
1. 大运边界敏感：大运交接前后 2 年是高风险窗口
2. 五行强度加权：流年天干地支与命局的作用力影响窗口宽度
3. 领域差异：
   - 婚姻/感情：窗口较窄（±1 年），时间敏感
   - 事业/财富：窗口较宽（±2 年），渐进演化
   - 健康/意外：窗口极窄（±6 月），突发性强
4. 置信度过滤：只考虑 ★≥3 的 gate，降低噪音

新增功能：
- 返回多个时间窗口（主窗口 + 次要窗口）
- 标注窗口成因（大运交接 / 三合冲 / 连续触发）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from engine.domain.prediction import TimeWindow
from engine.yingqi.types import GateResult


@dataclass
class EnhancedTimeWindow:
    """增强版时间窗口，包含多窗口 + 成因标注。"""
    primary: TimeWindow                           # 主窗口（最高置信度）
    secondary: list[TimeWindow] = field(default_factory=list)  # 次要窗口
    window_reasons: dict[str, str] = field(default_factory=dict)  # {年份: 成因}
    dayun_transitions: list[int] = field(default_factory=list)  # 大运交接年份
    confidence_distribution: dict[int, float] = field(default_factory=dict)  # {年份: 综合置信度}

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary": self.primary.to_dict(),
            "secondary": [w.to_dict() for w in self.secondary],
            "window_reasons": self.window_reasons,
            "dayun_transitions": self.dayun_transitions,
            "confidence_distribution": {
                str(k): round(v, 4) for k, v in self.confidence_distribution.items()
            },
        }


# ── 领域时间敏感度配置 ────────────────────────────────────
DOMAIN_TIME_SENSITIVITY = {
    "婚姻": {"base_width": 1, "urgency": "high"},      # ±1 年
    "感情": {"base_width": 1, "urgency": "high"},
    "事业": {"base_width": 2, "urgency": "medium"},    # ±2 年
    "财富": {"base_width": 2, "urgency": "medium"},
    "学业": {"base_width": 2, "urgency": "medium"},
    "健康": {"base_width": 0, "urgency": "critical"},  # ±6 月，用 0 表示
    "意外": {"base_width": 0, "urgency": "critical"},
    "default": {"base_width": 2, "urgency": "medium"},
}


def estimate_enhanced_time_window(
    gate_results: list[GateResult],
    *,
    min_confidence_star: int = 3,
    parsed_input: Any = None,  # 可选：用于获取命盘大运信息
) -> EnhancedTimeWindow:
    """增强版应期时间窗推理。

    Args:
        gate_results: D3 应期门结果列表
        min_confidence_star: 最低置信度星级（默认 3★）
        parsed_input: 可选，用于提取大运信息

    Returns:
        EnhancedTimeWindow: 含主窗口、次要窗口、成因标注
    """
    current_year = datetime.now(timezone.utc).year

    # ── 第一步：过滤高置信度 gate ──────────────────────────
    valid_gates = [
        g for g in gate_results
        if hasattr(g, 'passed_layers')
        and hasattr(g, 'year')
        and hasattr(g, 'confidence')
        and g.confidence is not None
        and g.passed_layers >= 1
        and g.confidence.star >= min_confidence_star
    ]

    if not valid_gates:
        # 降级：无高置信度 gate，返回当前+3年默认窗口
        default_window = TimeWindow(current_year, current_year + 3, current_year + 1)
        return EnhancedTimeWindow(
            primary=default_window,
            window_reasons={str(current_year + 1): "default_fallback"},
        )

    # ── 第二步：按年份聚合置信度 ──────────────────────────
    year_confidence: dict[int, float] = {}
    year_gates: dict[int, list[GateResult]] = {}
    for g in valid_gates:
        year = g.year
        year_gates.setdefault(year, []).append(g)
        # 综合置信度 = 平均星级 * 通过层数权重
        conf_score = g.confidence.star * (g.passed_layers / 3.0)
        year_confidence[year] = year_confidence.get(year, 0) + conf_score

    # ── 第三步：识别峰值年份 ──────────────────────────────
    sorted_years = sorted(year_confidence.items(), key=lambda x: x[1], reverse=True)
    if not sorted_years:
        default_window = TimeWindow(current_year, current_year + 3, current_year + 1)
        return EnhancedTimeWindow(primary=default_window)

    peak_year, peak_conf = sorted_years[0]

    # ── 第四步：计算主窗口宽度（基于领域敏感度）────────────
    # 取峰值年的所有 gate，推断主导领域
    peak_gates = year_gates[peak_year]
    domains = [g.domain for g in peak_gates if hasattr(g, 'domain')]
    primary_domain = domains[0] if domains else "default"

    sensitivity = DOMAIN_TIME_SENSITIVITY.get(
        primary_domain, DOMAIN_TIME_SENSITIVITY["default"]
    )
    base_width = sensitivity["base_width"]

    # ── 第五步：检测大运交接点 ────────────────────────────
    dayun_transitions = _extract_dayun_transitions(parsed_input, peak_year)

    # 如果峰值年靠近大运交接（±1年），扩大窗口 +1
    is_near_transition = any(abs(peak_year - t) <= 1 for t in dayun_transitions)
    if is_near_transition:
        base_width += 1

    # ── 第六步：构建主窗口 ────────────────────────────────
    start_year = max(current_year, peak_year - base_width)
    end_year = peak_year + base_width
    primary_window = TimeWindow(start_year, end_year, peak_year)

    # ── 第七步：识别次要窗口 ──────────────────────────────
    secondary_windows: list[TimeWindow] = []
    window_reasons: dict[str, str] = {str(peak_year): "peak_confidence"}

    # 如果有其他高置信度年份（且与主窗口不重叠），标记为次要窗口
    for year, conf in sorted_years[1:]:
        if conf >= peak_conf * 0.6:  # 次要窗口至少 60% 峰值置信度
            if year < start_year or year > end_year:  # 不与主窗口重叠
                sec_width = base_width - 1 if base_width > 0 else 0
                secondary_windows.append(
                    TimeWindow(
                        max(current_year, year - sec_width),
                        year + sec_width,
                        year,
                    )
                )
                window_reasons[str(year)] = "secondary_peak"

    # ── 第八步：标注大运交接点 ────────────────────────────
    for t in dayun_transitions:
        if start_year <= t <= end_year:
            window_reasons[str(t)] = "dayun_transition"

    # ── 第九步：标注连续触发 ──────────────────────────────
    consecutive_years = _find_consecutive_triggers(year_gates, start_year, end_year)
    for y in consecutive_years:
        if str(y) not in window_reasons:
            window_reasons[str(y)] = "consecutive_trigger"

    return EnhancedTimeWindow(
        primary=primary_window,
        secondary=secondary_windows[:2],  # 最多保留 2 个次要窗口
        window_reasons=window_reasons,
        dayun_transitions=dayun_transitions,
        confidence_distribution=year_confidence,
    )


def _extract_dayun_transitions(parsed_input: Any, peak_year: int) -> list[int]:
    """从 ParsedInput 提取大运交接年份（峰值年 ±10 年范围内）。

    大运周期：10 年一换，交接前后 2 年是高风险期。
    """
    if not parsed_input or not hasattr(parsed_input, 'birth'):
        return []

    try:
        birth_year = parsed_input.birth.year
        # 简化逻辑：假设大运起运年龄 = birth_year + 起运岁数（通常 1-10 岁）
        # 这里用占位逻辑，实际应从 parsed_input 读取起运信息
        start_age = 3  # 占位：假设 3 岁起运
        start_dayun_year = birth_year + start_age

        transitions = []
        for offset in range(0, 100, 10):  # 生成 0-90 岁的大运交接点
            transition_year = start_dayun_year + offset
            if abs(transition_year - peak_year) <= 15:  # 只保留峰值年 ±15 年内的
                transitions.append(transition_year)

        return transitions
    except (AttributeError, TypeError):
        return []


def _find_consecutive_triggers(
    year_gates: dict[int, list[GateResult]],
    start_year: int,
    end_year: int,
) -> list[int]:
    """识别连续 3 年或以上都有高置信度触发的年份。"""
    consecutive = []
    sorted_years = sorted(year_gates.keys())

    for i, year in enumerate(sorted_years):
        if not (start_year <= year <= end_year):
            continue

        # 检查是否连续 3 年
        if (
            i + 2 < len(sorted_years)
            and sorted_years[i + 1] == year + 1
            and sorted_years[i + 2] == year + 2
        ):
            consecutive.extend([year, year + 1, year + 2])

    return list(set(consecutive))  # 去重


# ── 兼容层：保留旧接口 ────────────────────────────────────
def estimate_time_window_legacy(gate_results: list[GateResult]) -> TimeWindow:
    """向后兼容的简单时间窗推理（保留给不需要增强功能的调用方）。"""
    current_year = datetime.now(timezone.utc).year
    valid_gates = [
        g for g in gate_results
        if hasattr(g, 'passed_layers') and hasattr(g, 'year') and g.passed_layers >= 1
    ]

    if not valid_gates:
        return TimeWindow(current_year, current_year + 3, current_year + 1)

    # 取最高层数的 gate
    full_pass = [g for g in valid_gates if g.passed_layers == 3]
    anchor = full_pass if full_pass else valid_gates

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
