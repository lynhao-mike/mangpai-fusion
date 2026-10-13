"""职业路径的原局先验、大运约束与现实状态数据契约。

本模块只定义 as-of 数据边界，不实现命理推理，也不从职业事实反推原局结构。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


CareerRealityValue = Literal[
    "employed",
    "entrepreneurial",
    "mixed",
    "transitioning",
    "unknown",
]


@dataclass(frozen=True, slots=True)
class NatalCareerInclination:
    """原局职业倾向（先验，不等于现实状态）。"""

    employment_inclined: bool
    entrepreneurship_inclined: bool
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DayunCareerContext:
    """大运阶段对职业路径的约束。"""

    opens_employment: bool
    opens_entrepreneurship: bool
    suppresses_employment: bool
    suppresses_entrepreneurship: bool
    mechanism: str


@dataclass(frozen=True, slots=True)
class RealityCareerStatus:
    """截至求测日的现实职业状态。

    ``mixed`` 是双轨并存或已有转换历史的有效状态，不是脏数据。
    """

    current: CareerRealityValue
    verified_events: tuple[str, ...]
    transition_history: tuple[dict, ...]


@dataclass(frozen=True, slots=True)
class CareerPathState:
    """职业路径四层状态：原局先验、大运约束、现实位置与弃权原因。"""

    natal_inclination: NatalCareerInclination
    dayun_context: DayunCareerContext | None
    reality_status: RealityCareerStatus
    abstain_reason: str | None


__all__ = (
    "CareerPathState",
    "CareerRealityValue",
    "DayunCareerContext",
    "NatalCareerInclination",
    "RealityCareerStatus",
)
