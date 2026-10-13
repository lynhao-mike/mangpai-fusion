"""as-of 盲断闭环 · 候选库截止态可核验性预扫描。

背景：审计报告 reports/as-of-post-2026-07-18-alignment-audit.md §4.1 确认
2/3 新鲜候选因反馈无截止日现状描述而记为职业基本面 ABSTAIN，根源是候选
筛选流程没有把"是否含截止态"当作预筛选条件。本模块扫描 cases/ 目录下所有
已有 feedback.md 的案例，按启发式规则分类为"可能含截止态"和"仅含历史事件"
两类，供扩样前的候选池健康度评估。

本模块只读文件，不修改任何案例数据，不是 as-of 两阶段协议的组成部分。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

__all__ = (
    "FeedbackCurrentStateSignal",
    "ScanResult",
    "analyze_feedback_current_state",
    "scan_feedback_current_state",
)

_YEAR_ROW_RE = re.compile(r"^\s*\|\s*(\d{4})\s*\|.*$", re.MULTILINE)
_STATE_WORD_RE = re.compile(
    r"职业|就业|工作|岗位|失业|在职|创业|无业|负债|债务|收入|工资|薪|月薪|年薪|"
    r"结婚|未婚|离婚|在读|读书|学校|升学|考研|考公|入职|辞职|跳槽|经营|开店"
)
_HEURISTIC_NOTE = "本结果仅为启发式初步分类，不是绝对准入判定，仍需人工核验反馈语境。"


@dataclass(frozen=True, slots=True)
class FeedbackCurrentStateSignal:
    """单个反馈文件中的截止态信号。"""

    case_id: str
    feedback_path: str
    max_year_in_table: int
    has_recent_year: bool
    has_state_word: bool
    likely_has_current_state: bool
    note: str


@dataclass(frozen=True, slots=True)
class ScanResult:
    """反馈库截止态信号的互斥分类汇总。"""

    likely_has_current_state: tuple[FeedbackCurrentStateSignal, ...]
    likely_historical_only: tuple[FeedbackCurrentStateSignal, ...]
    no_year_table: tuple[FeedbackCurrentStateSignal, ...]
    total_scanned: int
    cutoff_year: int
    note: str


def analyze_feedback_current_state(
    content: str,
    *,
    case_id: str,
    feedback_path: str,
    cutoff_year: int = 2024,
) -> FeedbackCurrentStateSignal:
    """分析一份反馈文本，返回截止态启发式信号。"""

    year_rows = [(int(match.group(1)), match.group(0)) for match in _YEAR_ROW_RE.finditer(content)]
    max_year = max((year for year, _ in year_rows), default=0)
    has_recent_year = max_year >= cutoff_year
    latest_rows = (row for year, row in year_rows if year == max_year)
    state_words = tuple(
        dict.fromkeys(
            match.group(0)
            for row in latest_rows
            for match in _STATE_WORD_RE.finditer(row)
        )
    )
    has_state_word = bool(state_words) and has_recent_year
    likely_has_current_state = has_recent_year and has_state_word

    if max_year == 0:
        detail = "未找到含四位数字年份的 Markdown 表格行。"
    elif likely_has_current_state:
        detail = f"最大年份 {max_year} 达到截止线，检测到状态词：{'、'.join(state_words)}。"
    elif has_recent_year:
        detail = f"最大年份 {max_year} 达到截止线，但该年份行未检测到状态词。"
    else:
        detail = f"最大年份 {max_year} 早于截止线 {cutoff_year}。"

    return FeedbackCurrentStateSignal(
        case_id=case_id,
        feedback_path=feedback_path,
        max_year_in_table=max_year,
        has_recent_year=has_recent_year,
        has_state_word=has_state_word,
        likely_has_current_state=likely_has_current_state,
        note=f"{detail}{_HEURISTIC_NOTE}",
    )


def scan_feedback_current_state(
    cases_root: Path,
    *,
    cutoff_year: int = 2024,
) -> ScanResult:
    """扫描 cases_root 下所有 feedback.md，按截止态信号分类。"""

    signals: list[FeedbackCurrentStateSignal] = []
    for feedback_path in sorted(cases_root.rglob("feedback.md")):
        relative_to_cases = feedback_path.relative_to(cases_root)
        if "_TEMPLATE" in relative_to_cases.parts:
            continue

        display_path = (Path(cases_root.name) / relative_to_cases).as_posix()
        signals.append(
            analyze_feedback_current_state(
                feedback_path.read_text(encoding="utf-8"),
                case_id=feedback_path.parent.name,
                feedback_path=display_path,
                cutoff_year=cutoff_year,
            )
        )

    likely_current = tuple(signal for signal in signals if signal.likely_has_current_state)
    no_year = tuple(signal for signal in signals if signal.max_year_in_table == 0)
    historical_only = tuple(
        signal
        for signal in signals
        if signal.max_year_in_table != 0 and not signal.likely_has_current_state
    )

    return ScanResult(
        likely_has_current_state=likely_current,
        likely_historical_only=historical_only,
        no_year_table=no_year,
        total_scanned=len(signals),
        cutoff_year=cutoff_year,
        note=_HEURISTIC_NOTE,
    )
