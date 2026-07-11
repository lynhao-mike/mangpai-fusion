from __future__ import annotations

import dataclasses

from engine.decision import (
    build_arbitration_decisions,
    build_event_hypotheses,
    build_feedback_attributions,
    build_feedback_signals,
    build_report_items,
    build_structural_verdicts,
    build_timing_probabilities,
    run_decision_mvp,
)
from engine.decision.accuracy_report import AccuracyReport, build_accuracy_report
from engine.decision.models import StructuralVerdict


WENZHEN = """
$BASE
命式: 乾
$FOUR
Y:甲寅
M:乙卯
D:丙子
H:戊午
$DY_LOOP
# 1998-2007 甲寅
$FOCUS
事业
""".strip()


def _run_with_verdicts(*verdicts: str):
    run = run_decision_mvp(WENZHEN)
    structural_by_claim = {
        item.claim_id: item
        for item in build_structural_verdicts(run.case_id, run.school_claims)
    }
    event_claims = [
        item for item in run.school_claims if item.claim_type in {"event", "event_claim"}
    ]
    for index, claim in enumerate(event_claims):
        structural_by_claim[claim.claim_id] = StructuralVerdict(
            verdict_id=f"accuracy-verdict-{index}",
            claim_id=claim.claim_id,
            verdict="pass",
            structural_reason="accuracy fixture 显式确认自身事件命题通过结构审查。",
            confidence=claim.confidence,
        )
    structural_verdicts = list(structural_by_claim.values())
    events = build_event_hypotheses(run.case_id, structural_verdicts, run.school_claims)
    timings = build_timing_probabilities(run.case_id, events)
    decisions = build_arbitration_decisions(run.case_id, events, run.school_applicability)
    report_items = build_report_items(run.case_id, decisions, timings)
    signals = build_feedback_signals(run.case_id, report_items)
    assert len(signals) >= len(verdicts), "样例反馈信号不足以注入所需 verdict"
    for i, verdict in enumerate(verdicts):
        notes = "流派选错 主审失验" if verdict == "miss" else ""
        signals[i] = dataclasses.replace(signals[i], verdict=verdict, notes=notes)
    attributions = build_feedback_attributions(signals)
    rebuilt = dataclasses.replace(
        run,
        structural_verdicts=structural_verdicts,
        event_hypotheses=events,
        timing_probabilities=timings,
        arbitration_decisions=decisions,
        report_items=report_items,
        feedback_signals=signals,
        feedback_attributions=attributions,
        calibration_actions=[],
    )
    verdict_by_claim = {item.claim_id: item.verdict_id for item in structural_verdicts}
    for event in events:
        source_claim_id = next(
            item.claim_id for item in run.school_claims if item.statement == event.concrete_event
        )
        assert event.source_verdict_ids == [verdict_by_claim[source_claim_id]]
    assert rebuilt.validate_trace() == []
    return rebuilt


def test_report_counts_verdicts_and_excludes_unknown_from_scored() -> None:
    report = build_accuracy_report([_run_with_verdicts("hit"), _run_with_verdicts("miss")])

    assert isinstance(report, AccuracyReport)
    assert report.verdict_counts.get("hit", 0) >= 1
    assert report.verdict_counts.get("miss", 0) >= 1
    assert report.scored == report.verdict_counts.get("hit", 0) + report.verdict_counts.get("miss", 0) + report.verdict_counts.get("partial", 0)
    assert 0.0 <= report.overall_hit_rate <= 1.0


def test_report_attributes_miss_to_layer() -> None:
    report = build_accuracy_report([_run_with_verdicts("miss")])

    assert sum(report.miss_by_layer.values()) >= 1


def test_report_empty_runs_is_safe() -> None:
    report = build_accuracy_report([])

    assert report.total_feedback == 0
    assert report.scored == 0
    assert report.overall_hit_rate == 0.0
    assert report.miss_by_layer == {}


def test_render_markdown_contains_all_sections() -> None:
    from engine.decision.accuracy_report import render_accuracy_markdown

    md = render_accuracy_markdown(build_accuracy_report([_run_with_verdicts("hit"), _run_with_verdicts("miss")]))

    assert "# 分层准确率看板" in md
    assert "总体命中率" in md
    assert "按层 miss" in md
    assert "按域命中率" in md
    assert "按事件类型命中率" in md


def test_render_markdown_flags_no_feedback() -> None:
    from engine.decision.accuracy_report import render_accuracy_markdown

    assert "尚无可计分反馈" in render_accuracy_markdown(build_accuracy_report([]))


def test_exports_from_decision_package() -> None:
    from engine.decision import AccuracyReport as ExportedReport
    from engine.decision import build_accuracy_report as exported_build
    from engine.decision import render_accuracy_markdown as exported_render

    assert ExportedReport is not None
    assert exported_build is not None
    assert exported_render is not None
