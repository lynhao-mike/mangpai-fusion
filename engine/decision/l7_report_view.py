"""L7 报告表达层最小实现。"""

from __future__ import annotations

import hashlib

from engine.decision.models import ArbitrationDecision, ReportViewItem, TimingProbability


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]}"


def build_report_items(case_id: str, decisions: list[ArbitrationDecision], timings: list[TimingProbability]) -> list[ReportViewItem]:
    """L7 只消费裁判结果和时间窗，不新增命理推理。"""

    timing_by_event = {item.event_id: item for item in timings}
    items: list[ReportViewItem] = []
    for decision in decisions:
        event_ids = decision.winner_ids or decision.competing_event_ids
        for idx, event_id in enumerate(event_ids, start=1):
            timing = timing_by_event.get(event_id)
            items.append(
                ReportViewItem(
                    report_item_id=_stable_id("drv", case_id, decision.decision_id, idx),
                    decision_id=decision.decision_id,
                    prediction_id=timing.prediction_id if timing else "",
                    display_text="分层决策 MVP 已形成一条可追溯裁判链。",
                    confidence_display="中（★★★☆☆）",
                    evidence_summary="报告层只消费 L6 裁判与 L5 时间窗，不新增命理推理。",
                    feedback_prompt="请反馈该事件是否发生、发生时间与偏差原因。",
                )
            )
    return items
