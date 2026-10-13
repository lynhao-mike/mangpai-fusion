"""as-of 盲断闭环 · 冻结前逐年触发强度预览（基于已建立的 annual_trace 适配层）。

背景：审计报告 reports/as-of-post-2026-07-18-alignment-audit.md §3.2 确认
事件窗口设计是高严重度偏离——2～3 年+多选事件类型使精确应期不可核验，且修复
过一次又退化，说明没有机器引导就无法持续。本模块提供冻结前的结构性触发信号
预览：调用 engine.asof.annual_trace.build_annual_traces() 扫描逐年干支关系，
输出按强度倒序的年份列表，供冻结者参考选择候选年——而不是仅凭直觉画区间。

本模块不修改任何冻结产物，不读取任何 feedback.md，不构成 as-of 两阶段协议
的任何一步，只是协议开始前的一个独立参考工具。
"""
from __future__ import annotations

from dataclasses import dataclass

from engine.asof.annual_trace import build_annual_traces
from engine.predicates.types import ParsedInput

__all__ = (
    "YearTriggerSignal",
    "FreezePreflight",
    "run_freeze_preflight",
)


@dataclass(frozen=True, slots=True)
class YearTriggerSignal:
    """冻结者可直接查看的单年结构触发信号。"""

    year: int
    liunian: str
    dayun_ganzhi: str
    trigger_strength: str
    relation_count: int
    domain_hints: tuple[str, ...]
    relation_summaries: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FreezePreflight:
    """按触发强度分层的冻结前逐年预览。"""

    high_trigger_years: tuple[YearTriggerSignal, ...]
    medium_trigger_years: tuple[YearTriggerSignal, ...]
    low_trigger_years: tuple[YearTriggerSignal, ...]
    total_years_scanned: int
    note: str


def run_freeze_preflight(
    parsed_input: ParsedInput,
    *,
    as_of_year: int,
) -> FreezePreflight:
    """扫描截止 ``as_of_year`` 的逐年触发强度，按强度分层返回。

    本函数只把年度轨迹转换为独立、只读的预览对象，不越候选门，也不据此生成或
    修改冻结产物。分层结果只用于帮助人工比较年份，不能替代现实条件与反证核验。
    """

    traces = build_annual_traces(parsed_input, current_year=as_of_year)
    grouped: dict[str, list[YearTriggerSignal]] = {
        "high": [],
        "medium": [],
        "low": [],
    }

    for trace in traces:
        signal = YearTriggerSignal(
            year=trace.year,
            liunian=trace.liunian,
            dayun_ganzhi=trace.dayun_ganzhi,
            trigger_strength=trace.trigger_strength,
            relation_count=len(trace.relations),
            domain_hints=trace.domains,
            relation_summaries=tuple(relation.excerpt for relation in trace.relations),
        )
        grouped[trace.trigger_strength].append(signal)

    for signals in grouped.values():
        signals.sort(key=lambda signal: signal.year)

    return FreezePreflight(
        high_trigger_years=tuple(grouped["high"]),
        medium_trigger_years=tuple(grouped["medium"]),
        low_trigger_years=tuple(grouped["low"]),
        total_years_scanned=len(traces),
        note=(
            "本预览仅提供命盘与岁运关系形成的结构性触发信号参考，不等于‘这年必发事’；"
            "强触发年也可能因现实条件不足而无事发生，低触发年也可能因其他条件而有事。"
        ),
    )
