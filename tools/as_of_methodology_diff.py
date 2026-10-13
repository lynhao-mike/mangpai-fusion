"""as-of 盲断闭环 · 方法论差异评分工具。

自动读取旧方法论和新工具链两批冻结文件，计算三个偏离指标：
- center_or_count：职业中心描述中'或'连接词数量（偏离A）
- max_event_window_months：事件候选最大窗口跨度（偏离B）
- has_incomplete_realization_guard：是否有兑现不稳备选（偏离D）

不修改任何案例文件，只读。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean
from typing import Any

from tools.as_of_contract_gate import (
    check_center_statement_breadth,
    check_completion_realization_guard,
    check_event_window,
)

__all__ = (
    "FreezeMetrics",
    "MethodologyDiffReport",
    "compute_freeze_metrics",
    "build_methodology_diff_report",
)


@dataclass(frozen=True, slots=True)
class FreezeMetrics:
    case_id: str
    center_or_count: int
    max_event_window_months: float
    has_incomplete_realization_guard: bool
    methodology: str
    freeze_path: str


@dataclass(frozen=True, slots=True)
class MethodologyDiffReport:
    old_cases: tuple[FreezeMetrics, ...]
    new_cases: tuple[FreezeMetrics, ...]
    old_avg_or_count: float
    new_avg_or_count: float
    old_avg_window_months: float
    new_avg_window_months: float
    old_guard_rate: float
    new_guard_rate: float
    summary: str


def _load_freeze(freeze_path: Path) -> dict[str, Any]:
    with freeze_path.open(encoding="utf-8") as stream:
        document = json.load(stream)
    if not isinstance(document, dict):
        raise ValueError(f"freeze JSON root must be an object: {freeze_path}")
    return document


def _event_window_months(candidate: dict[str, Any]) -> float:
    window = candidate["window"]
    if not isinstance(window, str) or window.count("/") != 1:
        raise ValueError(f"invalid event window: {window!r}")
    window_start, window_end = window.split("/")
    finding = check_event_window(
        str(candidate.get("candidate_id", "")),
        window_start,
        window_end,
        str(candidate.get("center_event", "")),
    )
    return finding.window_months


def compute_freeze_metrics(
    freeze_path: Path,
    *,
    methodology: str,
) -> FreezeMetrics:
    """从冻结JSON计算单案例的三个偏离指标。"""

    if methodology not in {"old", "new"}:
        raise ValueError("methodology must be 'old' or 'new'")

    document = _load_freeze(freeze_path)

    # 兼容两种 schema：
    # 旧 schema：primary_landing_set / frozen_event_candidates
    # 新 schema（RF000417+）：career_baseline / events
    if "primary_landing_set" in document:
        landing_set = document["primary_landing_set"]
        center = landing_set["center"]
        center_statement = center["statement"]
        alternatives = landing_set["alternatives"]
        alternative_statements = tuple(item["statement"] for item in alternatives)
        event_candidates = document.get("frozen_event_candidates", [])
        completion_mode = str(center.get("completion_mode", ""))
    elif "career_baseline" in document:
        # 新 schema：gate_observation 已预计算三个偏离指标，直接读取；
        # 不重复计算，避免因字段结构差异产生误差。
        contract = document.get("contract", {})
        gate_obs = contract.get("gate_observation", {})
        _or_count = int(gate_obs.get("center_or_count", 0))
        _months = float(gate_obs.get("months", 0.0))
        _guard = bool(gate_obs.get("has_incomplete_alt", False))
        case_id_str = str(document.get("case_id", ""))
        return FreezeMetrics(
            case_id=case_id_str,
            center_or_count=_or_count,
            max_event_window_months=_months,
            has_incomplete_realization_guard=_guard,
            methodology=methodology,
            freeze_path=str(freeze_path),
        )
    else:
        raise ValueError(
            f"Unrecognized freeze schema in {freeze_path}: "
            "expected 'primary_landing_set' or 'career_baseline'"
        )

    if not isinstance(center_statement, str):
        raise ValueError("center statement must be a string")
    if not isinstance(event_candidates, list):
        raise ValueError("event candidates must be an array")

    center_or_count = check_center_statement_breadth(center_statement).or_count
    window_months = tuple(_event_window_months(candidate) for candidate in event_candidates)
    guard = check_completion_realization_guard(
        completion_mode,
        alternative_statements,
    ).has_incomplete_realization_alt

    return FreezeMetrics(
        case_id=str(document["case_id"]),
        center_or_count=center_or_count,
        max_event_window_months=max(window_months, default=0.0),
        has_incomplete_realization_guard=guard,
        methodology=methodology,
        freeze_path=str(freeze_path),
    )


def _average(cases: tuple[FreezeMetrics, ...], attribute: str) -> float:
    if not cases:
        raise ValueError("each methodology batch must contain at least one freeze path")
    return fmean(float(getattr(case, attribute)) for case in cases)


def build_methodology_diff_report(
    old_freeze_paths: tuple[Path, ...],
    new_freeze_paths: tuple[Path, ...],
) -> MethodologyDiffReport:
    """对比两批冻结文件，生成方法论差异报告。"""

    old_cases = tuple(
        compute_freeze_metrics(path, methodology="old") for path in old_freeze_paths
    )
    new_cases = tuple(
        compute_freeze_metrics(path, methodology="new") for path in new_freeze_paths
    )
    old_avg_or_count = _average(old_cases, "center_or_count")
    new_avg_or_count = _average(new_cases, "center_or_count")
    old_avg_window_months = _average(old_cases, "max_event_window_months")
    new_avg_window_months = _average(new_cases, "max_event_window_months")
    old_guard_rate = _average(old_cases, "has_incomplete_realization_guard")
    new_guard_rate = _average(new_cases, "has_incomplete_realization_guard")

    improved_count = sum(
        (
            new_avg_or_count < old_avg_or_count,
            new_avg_window_months < old_avg_window_months,
            new_guard_rate > old_guard_rate,
        )
    )
    summary = f"新工具链在三个可量化偏离指标中改善了{improved_count}项。"

    return MethodologyDiffReport(
        old_cases=old_cases,
        new_cases=new_cases,
        old_avg_or_count=old_avg_or_count,
        new_avg_or_count=new_avg_or_count,
        old_avg_window_months=old_avg_window_months,
        new_avg_window_months=new_avg_window_months,
        old_guard_rate=old_guard_rate,
        new_guard_rate=new_guard_rate,
        summary=summary,
    )
