"""L5 应期概率层最小实现。"""

from __future__ import annotations

import hashlib

from engine.decision.models import EventHypothesis, TimingProbability


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]}"


def _probability_range_for_confidence(confidence: float) -> tuple[float, float]:
    if confidence < 0.3:
        return (0.1, 0.3)
    if confidence < 0.6:
        return (0.3, 0.6)
    return (0.6, 0.8)



def build_timing_probabilities(case_id: str, events: list[EventHypothesis]) -> list[TimingProbability]:
    """L5 只回答何时触发、概率多高；不改写事件内容。"""

    return [
        TimingProbability(
            prediction_id=_stable_id("dtp", case_id, event.event_id),
            event_id=event.event_id,
            time_window={"label": "当前大运至下一交运前", "basis": "MVP 默认时间窗"},
            trigger_conditions=["事件已通过 L4 登记", "反馈时必须验证时间窗"],
            probability_range=_probability_range_for_confidence(event.confidence),
            confidence=event.confidence,
            falsifier="若时间窗内该事件无现实对应，则 L5 失验；若事件类型也错，则回打 L4。",
        )
        for event in events
        if event.event_id
    ]
