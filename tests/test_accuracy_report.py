from __future__ import annotations

import dataclasses

from engine.decision import run_decision_mvp
from engine.decision.accuracy_report import AccuracyReport, build_accuracy_report


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
    signals = list(run.feedback_signals)
    assert len(signals) >= len(verdicts), "样例反馈信号不足以注入所需 verdict"
    for i, verdict in enumerate(verdicts):
        notes = "流派选错 主审失验" if verdict == "miss" else ""
        signals[i] = dataclasses.replace(signals[i], verdict=verdict, notes=notes)
    return dataclasses.replace(run, feedback_signals=signals)


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
