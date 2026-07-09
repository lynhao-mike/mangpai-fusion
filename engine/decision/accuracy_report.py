"""分层准确率看板（Phase R4）。

只读 DecisionRun 现有字段做跨 run 聚合，不改任何层、不持久化。
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from engine.decision.models import DecisionRun

_SCORED = {"hit", "miss", "partial"}


@dataclass(frozen=True)
class AccuracyReport:
    total_feedback: int = 0
    verdict_counts: dict[str, int] = field(default_factory=dict)
    scored: int = 0
    overall_hit_rate: float = 0.0
    miss_by_layer: dict[str, int] = field(default_factory=dict)
    hit_rate_by_domain: dict[str, float] = field(default_factory=dict)
    hit_rate_by_event_type: dict[str, float] = field(default_factory=dict)
    scored_by_domain: dict[str, int] = field(default_factory=dict)
    scored_by_event_type: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_feedback": self.total_feedback,
            "verdict_counts": dict(self.verdict_counts),
            "scored": self.scored,
            "overall_hit_rate": self.overall_hit_rate,
            "miss_by_layer": dict(self.miss_by_layer),
            "hit_rate_by_domain": dict(self.hit_rate_by_domain),
            "hit_rate_by_event_type": dict(self.hit_rate_by_event_type),
            "scored_by_domain": dict(self.scored_by_domain),
            "scored_by_event_type": dict(self.scored_by_event_type),
        }


def _rate(hit: int, scored: int) -> float:
    return round(hit / scored, 3) if scored else 0.0


def build_accuracy_report(runs: list[DecisionRun]) -> AccuracyReport:
    verdict_counts: dict[str, int] = defaultdict(int)
    miss_by_layer: dict[str, int] = defaultdict(int)
    hit_by_domain: dict[str, int] = defaultdict(int)
    scored_by_domain: dict[str, int] = defaultdict(int)
    hit_by_event: dict[str, int] = defaultdict(int)
    scored_by_event: dict[str, int] = defaultdict(int)
    total = 0
    hit_total = 0
    scored_total = 0

    for run in runs:
        report_by_id = {r.report_item_id: r for r in run.report_items}
        decision_by_id = {d.decision_id: d for d in run.arbitration_decisions}
        event_type_by_id = {e.event_id: e.event_type for e in run.event_hypotheses}
        layer_by_feedback = {a.feedback_id: a.affected_layer for a in run.feedback_attributions}

        for signal in run.feedback_signals:
            total += 1
            verdict_counts[signal.verdict] += 1
            is_scored = signal.verdict in _SCORED
            is_hit = signal.verdict == "hit"
            if is_scored:
                scored_total += 1
                if is_hit:
                    hit_total += 1
            if signal.verdict == "miss":
                layer = layer_by_feedback.get(signal.feedback_id)
                if layer:
                    miss_by_layer[layer] += 1

            report_item = report_by_id.get(signal.report_item_id)
            decision = decision_by_id.get(report_item.decision_id) if report_item else None
            if decision and is_scored:
                scored_by_domain[decision.domain] += 1
                if is_hit:
                    hit_by_domain[decision.domain] += 1
                for event_id in decision.competing_event_ids:
                    event_type = event_type_by_id.get(event_id)
                    if event_type:
                        scored_by_event[event_type] += 1
                        if is_hit:
                            hit_by_event[event_type] += 1

    return AccuracyReport(
        total_feedback=total,
        verdict_counts=dict(verdict_counts),
        scored=scored_total,
        overall_hit_rate=_rate(hit_total, scored_total),
        miss_by_layer=dict(miss_by_layer),
        hit_rate_by_domain={d: _rate(hit_by_domain[d], scored_by_domain[d]) for d in scored_by_domain},
        hit_rate_by_event_type={e: _rate(hit_by_event[e], scored_by_event[e]) for e in scored_by_event},
        scored_by_domain=dict(scored_by_domain),
        scored_by_event_type=dict(scored_by_event),
    )


def render_accuracy_markdown(report: AccuracyReport) -> str:
    lines = ["# 分层准确率看板", ""]
    if report.scored == 0:
        lines += ["> 尚无可计分反馈（hit/miss/partial 为 0）；以下仅反映反馈登记情况，不代表准确率。", ""]

    lines += [
        f"- 反馈总数：{report.total_feedback}",
        f"- 可计分数（hit/miss/partial）：{report.scored}",
        f"- 总体命中率：{report.overall_hit_rate}",
        "",
        "## 按层 miss 分布",
    ]
    lines += [f"- {k}：{report.miss_by_layer[k]}" for k in sorted(report.miss_by_layer)] or ["- 无 miss 记录"]
    lines += ["", "## 按域命中率"]
    lines += [
        f"- {k}：命中率 {report.hit_rate_by_domain[k]}（计分 {report.scored_by_domain.get(k, 0)}）"
        for k in sorted(report.hit_rate_by_domain)
    ] or ["- 无可计分域"]
    lines += ["", "## 按事件类型命中率"]
    lines += [
        f"- {k}：命中率 {report.hit_rate_by_event_type[k]}（计分 {report.scored_by_event_type.get(k, 0)}）"
        for k in sorted(report.hit_rate_by_event_type)
    ] or ["- 无可计分事件类型"]
    lines.append("")
    return "\n".join(lines)
