"""L6 冲突仲裁层最小实现。"""

from __future__ import annotations

import hashlib

from engine.decision.models import ArbitrationDecision, EventHypothesis, SchoolApplicability


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]}"


def build_arbitration_decisions(case_id: str, events: list[EventHypothesis], applicability: list[SchoolApplicability]) -> list[ArbitrationDecision]:
    """L6 是裁判层，不做融合话术。"""

    if not events:
        return []
    first = events[0]
    return [
        ArbitrationDecision(
            decision_id=_stable_id("dad", case_id, first.domain),
            domain=first.domain,
            competing_event_ids=[item.event_id for item in events],
            result="winner",
            winner_ids=[first.event_id],
            rejected_ids=[],
            unresolved_ids=[item.event_id for item in events[1:]],
            arbitration_rule="MVP：优先选择结构链路完整且置信度最高的事件；不做全局综合评分。",
            school_applicability_snapshot=applicability,
            reason="L6 是裁判层，不是融合层；冲突不写成中庸话术。",
        )
    ]
