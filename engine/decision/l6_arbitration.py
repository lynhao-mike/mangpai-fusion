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
    if all(item.confidence <= 0.1 for item in events):
        result = "reject_all"
        winner_ids: list[str] = []
        rejected_ids = [item.event_id for item in events]
        unresolved_ids: list[str] = []
    elif len(events) == 1:
        result = "winner"
        winner_ids = [first.event_id]
        rejected_ids = []
        unresolved_ids = []
    elif max(item.confidence for item in events) - min(item.confidence for item in events) <= 0.05:
        result = "coexist"
        winner_ids = [item.event_id for item in events]
        rejected_ids = []
        unresolved_ids = []
    else:
        result = "unresolved"
        winner_ids = []
        rejected_ids = []
        unresolved_ids = [item.event_id for item in events]
    return [
        ArbitrationDecision(
            decision_id=_stable_id("dad", case_id, first.domain),
            domain=first.domain,
            competing_event_ids=[item.event_id for item in events],
            result=result,  # type: ignore[arg-type]
            winner_ids=winner_ids,
            rejected_ids=rejected_ids,
            unresolved_ids=unresolved_ids,
            arbitration_rule="MVP：按事件置信差距选择 winner / coexist / unresolved / reject_all；不做全局综合评分。",
            school_applicability_snapshot=applicability,
            reason="L6 是裁判层，不是融合层；冲突不写成中庸话术。",
        )
    ]
