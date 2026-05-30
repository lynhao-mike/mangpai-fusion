"""领域层置信度协议。

集中维护 06-confidence-model 中的 posterior/百分比/★ 映射，避免 engine 与 tools
各自复制阈值导致报告、规则生命周期和 lint 口径漂移。
"""
from __future__ import annotations

from typing import Optional


# 06-confidence-model § 二：posterior → ★ 的边界，输出百分比按左闭右闭区间表达。
STAR_RANGES_PERCENT: dict[int, tuple[int, int]] = {
    1: (0, 39),
    2: (40, 54),
    3: (55, 69),
    4: (70, 84),
    5: (85, 100),
}


POSTERIOR_THRESHOLDS: tuple[tuple[float, int], ...] = (
    (0.40, 1),
    (0.55, 2),
    (0.70, 3),
    (0.85, 4),
)


def posterior_to_star(posterior: float) -> int:
    """把 0.0-1.0 posterior 映射为 1-5 ★。"""
    try:
        p = float(posterior)
    except (TypeError, ValueError):
        return 1

    for upper, star in POSTERIOR_THRESHOLDS:
        if p < upper:
            return star
    return 5


def percent_to_star(percent: int | float) -> int:
    """把 0-100 百分比映射为 1-5 ★。越界值沿用历史 lint 行为返回 1。"""
    try:
        pct = int(round(float(percent)))
    except (TypeError, ValueError):
        return 1

    for star in (5, 4, 3, 2, 1):
        lo, hi = STAR_RANGES_PERCENT[star]
        if lo <= pct <= hi:
            return star
    return 1


def expected_pct_range(star: int) -> tuple[int, int]:
    """返回某个 ★ 等级的百分比闭区间；未知等级退回全范围。"""
    return STAR_RANGES_PERCENT.get(int(star), (0, 100))


def is_star_percent_consistent(star: int, percent: int | float) -> bool:
    """判断 ★ 等级与百分比是否落在同一置信区间。"""
    if star not in STAR_RANGES_PERCENT:
        return False
    try:
        pct = int(round(float(percent)))
    except (TypeError, ValueError):
        return False
    lo, hi = STAR_RANGES_PERCENT[star]
    return lo <= pct <= hi


def clamp_posterior(value: float, *, lo: float = 0.0, hi: float = 0.95) -> float:
    """posterior 通用钳制工具，默认上限保持现有 engine 口径 0.95。"""
    try:
        v = float(value)
    except (TypeError, ValueError):
        v = lo
    return max(lo, min(hi, v))
