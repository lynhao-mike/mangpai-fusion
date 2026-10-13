"""六源三领域分析 run snapshot 的命理师单份 Markdown 视图。"""

from __future__ import annotations

from engine.v5.domain import V5RunSnapshot
from engine.v5.domain_report_view import ClaimCardView, build_domain_report_view


def _render_card(card: ClaimCardView) -> list[str]:
    lines = [
        f"#### {card.school_name}",
        "",
        f"- 判断：{card.judgment}",
        f"- 证据：{'；'.join(card.evidence_texts)}",
        f"- 立场：{card.stance_name}",
        f"- 双轨置信度：{card.confidence_text}",
    ]
    lines.extend(
        [
            f"- 应期：{'；'.join(card.timing_texts)}",
            f"- 反证条件：{card.falsifier}",
        ]
    )
    if card.status_reason:
        lines.append(f"- 原因：{card.status_reason}")
    if card.timing_only:
        lines.append("- 角色边界：时点验证，不参与结构裁决。")
    if card.high_risk:
        lines.append("- ⚠ 高风险提示：需人工复核后方可用于重大决策。")
        lines.append(f"- 高风险门禁：{card.high_risk_gate_status}；原因：{card.high_risk_gate_reason}。")
        lines.append("- 门禁边界：门禁通过不表示现实准确，仅表示当前工程证据条件满足。")
    lines.append("")
    return lines


def render_domain_analysis_report(snapshot: V5RunSnapshot) -> str:
    """从白名单 ViewModel 渲染单份报告，不直接暴露快照内部字段。"""

    view = build_domain_report_view(snapshot)
    lines = [
        f"# 六源三领域命理分析报告（{view.gender_marker}造）",
        "",
        "> 六源三领域切片已接入；命题缺少可靠证据时显式弃权，不以占位文本补造判断。双轨置信度只表达当前证据强度与系统确信等级，不表示事件必然发生。",
        "",
        "## 命盘与时间范围",
        "",
        f"- 出生时间：{view.birth_datetime}",
        f"- 四柱：{view.pillars_text}",
        f"- 分析截止日：{view.as_of_date}",
        f"- 当前大运：{view.current_dayun}",
        f"- 未来三年：{view.future_years_text}",
        "",
    ]
    for domain in view.domains:
        lines.extend(
            [
                f"## {domain.name}分析",
                "",
                f"融合结论：**{domain.conclusion}**",
                f"融合判断：**{domain.conclusion}**",
                "",
                f"- 目标级裁决状态：{domain.adjudication_status}",
                f"- 目标级裁决说明：{domain.adjudication_summary}",
                f"- 现实映射状态：{domain.mapping_status}",
                f"- 现实映射说明：{domain.mapping_summary}",
                f"- 融合双轨置信度：{domain.conclusion_confidence}",
                f"- 冲突摘要：{domain.conflict_summary}",
                f"- 裁决说明：{domain.conflict_rationale}",
                "",
                "### 六源逐命题工作台",
                "",
            ]
        )
        for card in domain.cards:
            lines.extend(_render_card(card))
    lines.extend(
        [
            "## 使用边界",
            "",
            "- 高风险命题须由命理师结合现实资料人工复核。",
            "- 弃权或暂不支持表示当前能力或证据不足，不等同于反对命题。",
            "- 本报告为单份公开 Markdown；审计身份与完整性绑定保留在配套结构化快照中。",
            "",
        ]
    )
    return "\n".join(lines)
