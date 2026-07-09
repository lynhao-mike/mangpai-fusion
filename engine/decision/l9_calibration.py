"""L9 校准治理最小实现。

ponytail: 不自动改规则；只把 L8 归因转成 review/freeze 候选动作。
"""

from __future__ import annotations

from engine.decision.models import (
    ArbitrationDecision,
    CalibrationAction,
    FeedbackAttribution,
    FeedbackSignal,
    ReportViewItem,
)


def build_calibration_actions(case_id: str, attributions: list[FeedbackAttribution]) -> list[CalibrationAction]:
    """根据 L8 归因生成最小治理动作。"""

    reviewable = [
        item
        for item in attributions
        if item.requires_human_review and item.affected_layer in {"L1", "L2", "L3", "L4", "L5", "L6", "L7"} and item.affected_object_id
    ]
    by_target: dict[tuple[str, str], list[FeedbackAttribution]] = {}
    for item in reviewable:
        by_target.setdefault((item.affected_layer, item.affected_object_id), []).append(item)

    actions: list[CalibrationAction] = []
    for idx, items in enumerate(by_target.values(), start=1):
        item = items[0]
        target_type = {
            "L1": "router",
            "L2": "rule",
            "L3": "structure_policy",
            "L4": "event_mapping",
            "L5": "timing_policy",
            "L6": "arbitration_policy",
            "L7": "report_policy",
        }[item.affected_layer]
        action = "freeze" if len(items) >= 3 else "review"
        actions.append(
            CalibrationAction(
                action_id=f"cal-{case_id}-{idx:03d}",
                target_type=target_type,  # type: ignore[arg-type]
                target_id=item.affected_object_id,
                action=action,
                reason="；".join(sorted({entry.attribution_reason for entry in items if entry.attribution_reason})),
                evidence_feedback_ids=sorted(entry.feedback_id for entry in items),
            )
        )
    return actions


def build_router_calibration_actions(
    case_id: str,
    report_items: list[ReportViewItem],
    decisions: list[ArbitrationDecision],
    feedback_signals: list[FeedbackSignal],
) -> list[CalibrationAction]:
    """把单 run 内 miss 反馈回打到责任流派，产出 router 校准动作。"""

    decision_by_id = {d.decision_id: d for d in decisions}
    report_by_id = {r.report_item_id: r for r in report_items}

    per_school: dict[str, list[str]] = {}
    for signal in feedback_signals:
        if signal.verdict != "miss" or not signal.feedback_id:
            continue
        report_item = report_by_id.get(signal.report_item_id)
        if report_item is None:
            continue
        decision = decision_by_id.get(report_item.decision_id)
        if decision is None:
            continue
        for applicability in decision.school_applicability_snapshot:
            if applicability.role in {"lead", "co_lead"} and applicability.school:
                per_school.setdefault(applicability.school, []).append(signal.feedback_id)

    actions: list[CalibrationAction] = []
    for idx, (school, feedback_ids) in enumerate(sorted(per_school.items()), start=1):
        evidence = sorted(set(feedback_ids))
        actions.append(
            CalibrationAction(
                action_id=f"router-cal-{case_id}-{idx:03d}",
                target_type="router",
                target_id=school,
                action="downgrade" if len(evidence) >= 3 else "review",
                reason="该流派在本命盘被 L1 授权主审 / 副主审，但对应报告条目失验，回打路由角色。",
                evidence_feedback_ids=evidence,
            )
        )
    return actions
