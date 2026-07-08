from __future__ import annotations

from engine.decision import (
    build_arbitration_decisions,
    build_context_ledger,
    build_event_hypotheses,
    build_report_items,
    build_school_claims,
    build_structural_verdicts,
    build_timing_probabilities,
    run_decision_mvp,
)


def test_decision_mvp_builds_unbroken_l0_to_l7_trace() -> None:
    raw = """
$BASE
命式: 乾
公历: 1990-01-01 08:00
起运: 8岁
$FOUR
Y:庚午
M:戊寅
D:壬子
H:辛丑
$DY_LOOP
# 1998-2007 辛巳
> 2026 丙午
$KNOWN_FACTS
关注事业、财富、婚姻。
$FOCUS
事业与财富
$EXTRA
原样保留
""".strip()

    run = run_decision_mvp(raw)

    assert run.raw_payload.raw_hash == run.chart_ledger.raw_source_hash
    assert run.chart_ledger.four_pillars == {
        "year": "庚午",
        "month": "戊寅",
        "day": "壬子",
        "hour": "辛丑",
    }
    assert len(run.school_applicability) >= 6
    assert len(run.school_claims) >= 3
    assert len(run.structural_verdicts) >= 3
    assert len(run.event_hypotheses) >= 2
    assert len(run.timing_probabilities) >= 1
    assert len(run.arbitration_decisions) >= 1
    assert len(run.report_items) >= 1
    assert len(run.feedback_signals) == len(run.report_items)
    assert len(run.feedback_attributions) == len(run.feedback_signals)
    assert run.validate_trace() == []


def test_l2_to_l7_modules_are_composable() -> None:
    run = run_decision_mvp("""
$BASE
命式: 乾
$FOUR
Y:庚午
M:戊寅
D:壬子
H:辛丑
$DY_LOOP
# 1998-2007 辛巳
""".strip())

    claims = build_school_claims(run.case_id, run.school_applicability, run.chart_ledger)
    verdicts = build_structural_verdicts(run.case_id, claims)
    events = build_event_hypotheses(run.case_id, verdicts, claims)
    timings = build_timing_probabilities(run.case_id, events)
    decisions = build_arbitration_decisions(run.case_id, events, run.school_applicability)
    report_items = build_report_items(run.case_id, decisions, timings)

    assert claims
    assert verdicts
    assert events
    assert timings
    assert decisions
    assert report_items


def test_decision_mvp_records_missing_fields_without_judging() -> None:
    raw = """
$BASE
命式: _
$FOUR
Y:甲子
M:_
D:丙寅
H:丁卯
$DY_LOOP
# _
""".strip()

    run = run_decision_mvp(raw)

    assert "$BASE.命式" in run.chart_ledger.missing_fields
    assert "$FOUR.month" in run.chart_ledger.missing_fields
    assert "$DY_LOOP.1" in run.chart_ledger.missing_fields
    assert run.validate_trace() == []


def test_l0_context_ledger_keeps_free_text_out_of_chart_facts() -> None:
    context = build_context_ledger(
        {"KNOWN_FACTS": "已知事业变化", "FOCUS": "事业", "EXTRA": "原文保留"},
        ["EXTRA"],
    )

    assert context.known_fact_text == "已知事业变化"
    assert context.analysis_focus_text == "事业"
    assert context.preserved_text_blocks == ["$EXTRA\n原文保留"]
