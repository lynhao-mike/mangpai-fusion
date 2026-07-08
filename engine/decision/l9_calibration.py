"""L9 校准治理最小实现。

ponytail: 不自动改规则；只把 L8 归因转成 review/freeze 候选动作。
"""

from __future__ import annotations

from engine.decision.models import CalibrationAction, FeedbackAttribution


def build_calibration_actions(case_id: str, attributions: list[FeedbackAttribution]) -> list[CalibrationAction]:
    """根据 L8 归因生成最小治理动作。"""

    actions: list[CalibrationAction] = []
    for idx, item in enumerate(attributions, start=1):
        if item.affected_layer not in {"L1", "L2", "L3", "L4", "L5", "L6", "L7"}:
            continue
        if not item.requires_human_review:
            continue
        target_type = {
            "L1": "router",
            "L2": "rule",
            "L3": "structure_policy",
            "L4": "event_mapping",
            "L5": "timing_policy",
            "L6": "arbitration_policy",
            "L7": "report_policy",
        }[item.affected_layer]
        actions.append(
            CalibrationAction(
                action_id=f"cal-{case_id}-{idx:03d}",
                target_type=target_type,  # type: ignore[arg-type]
                target_id=item.affected_object_id,
                action="review",
                reason=item.attribution_reason,
                evidence_feedback_ids=[item.feedback_id],
            )
        )
    return actions
