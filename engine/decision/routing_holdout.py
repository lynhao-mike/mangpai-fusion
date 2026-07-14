"""L1 learned/static 留出集对照门禁；只消费冻结后的评分结果。"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean
from typing import Iterable, Literal


@dataclass(frozen=True)
class HoldoutRoutingRecord:
    case_id: str
    task_id: str
    static_utility: float
    learned_utility: float
    static_calibration_error: float
    learned_calibration_error: float
    high_risk: bool
    static_false_positive: bool
    learned_false_positive: bool
    prototype_id: str

    def __post_init__(self) -> None:
        if not self.case_id or not self.task_id or not self.prototype_id:
            raise ValueError("case_id, task_id and prototype_id are required")
        for name in ("static_calibration_error", "learned_calibration_error"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")


@dataclass(frozen=True)
class HoldoutComparison:
    status: Literal["GO", "HOLD", "STOP"]
    case_count: int
    record_count: int
    static_mean_utility: float
    learned_mean_utility: float
    static_calibration_error: float
    learned_calibration_error: float
    static_high_risk_false_positives: int
    learned_high_risk_false_positives: int
    reasons: tuple[str, ...]
    prototype_count: int


def evaluate_holdout(
    *,
    records: Iterable[HoldoutRoutingRecord],
    training_case_ids: set[str] | frozenset[str],
    minimum_holdout_cases: int = 5,
) -> HoldoutComparison:
    """强制训练/留出隔离，并依据三项硬门禁返回 GO/HOLD/STOP。"""
    items = tuple(records)
    if not items:
        raise ValueError("holdout records cannot be empty")
    holdout_case_ids = {item.case_id for item in items}
    overlap = holdout_case_ids.intersection(training_case_ids)
    if overlap:
        raise ValueError(f"training/holdout leakage detected: {sorted(overlap)}")

    static_utility = fmean(item.static_utility for item in items)
    learned_utility = fmean(item.learned_utility for item in items)
    static_calibration = fmean(item.static_calibration_error for item in items)
    learned_calibration = fmean(item.learned_calibration_error for item in items)
    static_fp = sum(item.high_risk and item.static_false_positive for item in items)
    learned_fp = sum(item.high_risk and item.learned_false_positive for item in items)
    reasons: list[str] = []

    if len(holdout_case_ids) < minimum_holdout_cases:
        status: Literal["GO", "HOLD", "STOP"] = "HOLD"
        reasons.append(f"留出集样本不足：{len(holdout_case_ids)} < {minimum_holdout_cases}。")
    else:
        if learned_utility < static_utility:
            reasons.append("learned 路由留出集决策效用低于静态基线。")
        if learned_calibration > static_calibration:
            reasons.append("learned 路由校准误差恶化。")
        if learned_fp > static_fp:
            reasons.append("learned 路由高风险假阳性增加。")
        status = "STOP" if reasons else "GO"
        if status == "GO":
            reasons.append("留出集效用不低于静态基线，且校准误差与高风险假阳性均未恶化。")

    return HoldoutComparison(
        status=status,
        case_count=len(holdout_case_ids),
        record_count=len(items),
        static_mean_utility=static_utility,
        learned_mean_utility=learned_utility,
        static_calibration_error=static_calibration,
        learned_calibration_error=learned_calibration,
        static_high_risk_false_positives=static_fp,
        learned_high_risk_false_positives=learned_fp,
        reasons=tuple(reasons),
        prototype_count=len({item.prototype_id for item in items}),
    )


def render_holdout_comparison(result: HoldoutComparison) -> str:
    """渲染公开验收证据；不暴露快照 ID、内部路由索引或样本明细。"""
    reasons = "\n".join(f"- {reason}" for reason in result.reasons)
    return (
        "# L1 可学习路由留出集对照\n\n"
        f"**门禁结论：{result.status}**\n\n"
        "| 指标 | 静态基线 | learned |\n"
        "|---|---:|---:|\n"
        f"| 平均决策效用 | {result.static_mean_utility:.4f} | {result.learned_mean_utility:.4f} |\n"
        f"| 平均校准误差 | {result.static_calibration_error:.4f} | {result.learned_calibration_error:.4f} |\n"
        f"| 高风险假阳性 | {result.static_high_risk_false_positives} | {result.learned_high_risk_false_positives} |\n\n"
        f"留出案例：{result.case_count}；评分记录：{result.record_count}；覆盖原型：{result.prototype_count}。\n\n"
        "## 判定依据\n\n"
        f"{reasons}\n"
    )
