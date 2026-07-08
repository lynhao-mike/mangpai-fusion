"""L8 反馈归因最小实现。

ponytail: 只做可解释的规则映射，不引入模型、不接数据库。
"""

from __future__ import annotations

from engine.decision.models import FeedbackAttribution, FeedbackSignal, ReportViewItem


def build_feedback_signals(case_id: str, report_items: list[ReportViewItem]) -> list[FeedbackSignal]:
    """为每个 L7 报告项生成待反馈信号。"""

    return [
        FeedbackSignal(
            feedback_id=f"fb-{case_id}-{idx:03d}",
            report_item_id=item.report_item_id,
            verdict="unknown",
            notes="等待命中 / 失验 / 半命中 / 跳过反馈。",
        )
        for idx, item in enumerate(report_items, start=1)
    ]


def attribute_feedback(signal: FeedbackSignal) -> FeedbackAttribution:
    """把反馈按最小规则归因到层。

    miss 默认先归因 L6/L5 需要人工复核；unknown/skipped 留在 L8。
    真正精细归因等反馈字段稳定后再做。
    """

    if signal.verdict == "miss":
        layer = "L6"
        reason = "结论失验，优先复核仲裁是否选错路径；若事件正确但时间错，再下钻 L5。"
        review = True
    elif signal.verdict == "partial":
        layer = "L5"
        reason = "半命中通常先复核时间窗、触发条件或概率区间。"
        review = True
    elif signal.verdict == "hit":
        layer = "L6"
        reason = "命中先登记为仲裁路径有效样本。"
        review = False
    else:
        layer = "L8"
        reason = "反馈不足，暂不回打上游层。"
        review = False
    return FeedbackAttribution(
        attribution_id=f"attr-{signal.feedback_id}",
        feedback_id=signal.feedback_id,
        affected_layer=layer,  # type: ignore[arg-type]
        affected_object_id=signal.report_item_id,
        attribution_reason=reason,
        confidence=0.4 if review else 0.3,
        requires_human_review=review,
    )


def build_feedback_attributions(signals: list[FeedbackSignal]) -> list[FeedbackAttribution]:
    return [attribute_feedback(signal) for signal in signals]
