"""ZiPing Fusion Engine v5 并行核心。

v5 当前采用 Staged clean path：作为独立核心可运行、可测试、可落盘，
但不替换既有正式报告出口。
"""

from __future__ import annotations

from engine.v5.domain import (
    V5ArbitrationResult,
    V5Claim,
    V5Confidence,
    V5Evidence,
    V5LearningSignal,
    V5Output,
    V5Prediction,
    V5PredictionLedger,
    V5StructureGraph,
)
from engine.v5.runner import run_v5

__all__ = [
    "V5ArbitrationResult",
    "V5Claim",
    "V5Confidence",
    "V5Evidence",
    "V5LearningSignal",
    "V5Output",
    "V5Prediction",
    "V5PredictionLedger",
    "V5StructureGraph",
    "run_v5",
]
