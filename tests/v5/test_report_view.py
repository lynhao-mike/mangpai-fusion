"""结构化 run/decision 到报告 ViewModel 的出口契约测试。"""

from __future__ import annotations

import json
import re

from engine.application.run_comparison import (
    DimensionDifference,
    RunComparison,
    RunComparisonItem,
)
from engine.decision.l6_staged_arbitration import StageDecision
from engine.evaluation.models import BlindPrediction, BlindSchoolOutput, BlindTask, FrozenBlindRun
from engine.v5.report_view import build_comparison_summary, build_report_context_from_frozen_run


DOMAINS = ("学业", "事业", "财富", "婚姻", "健康", "性格")


def _task(domain: str, *, high_risk: bool = False) -> BlindTask:
    return BlindTask(
        task_id=f"task-{domain}",
        domain=domain,
        claim_type="event_claim",
        scoring_method="binary",
        quantifiable=False,
        high_risk=high_risk,
        allowed_time_horizons=["annual"],
        required_input_fields=[],
        label_schema={},
        evaluation_note="报告出口测试",
    )


def _prediction(domain: str, suffix: str) -> BlindPrediction:
    return BlindPrediction(
        prediction_id=f"prediction-{suffix * 20}",
        event_label=f"{domain}结构化判断",
        probability=0.7,
        time_window={"start_year": 2028, "end_year": 2030, "label": "测试窗口"},
        evidence_refs=[f"evidence-{domain}"],
        falsifier="若窗口内未发生则失验",
    )


def _output(domain: str, school_id: str, state: str, suffix: str = "a") -> BlindSchoolOutput:
    predictions = [_prediction(domain, suffix)] if state == "claim" else []
    return BlindSchoolOutput(
        case_id="C-REPORT-001",
        school_id=school_id,
        task_id=f"task-{domain}",
        state=state,
        rationale=f"{domain}由结构化证据支持",
        predictions=predictions,
    )


def _frozen_run() -> tuple[FrozenBlindRun, list[BlindTask]]:
    tasks = [_task(domain, high_risk=domain == "健康") for domain in DOMAINS]
    outputs = [
        _output("学业", "ziping", "claim", "a"),
        _output("事业", "gao_dechen", "claim", "b"),
        _output("事业", "duan_jianye", "claim", "c"),
        _output("财富", "yang_qingjuan", "abstain"),
        _output("婚姻", "ren_tieshu", "unsupported"),
        _output("健康", "gao_dechen", "claim", "d"),
        _output("性格", "ditiansui", "claim", "e"),
    ]
    return (
        FrozenBlindRun(
            task_catalog_version="test-v1",
            rule_snapshot_id="rules-test",
            frozen_at="2026-07-15T00:00:00Z",
            outputs=outputs,
            freeze_hash="freeze-test",
        ),
        tasks,
    )


def test_build_context_covers_six_domains_and_marks_missing_evidence() -> None:
    frozen_run, tasks = _frozen_run()

    context = build_report_context_from_frozen_run(frozen_run, tasks)

    assert set(context["domains"]) == set(DOMAINS)
    assert "证据不足/本派克制" in json.dumps(context["domains"]["财富"], ensure_ascii=False)
    assert "证据不足/本派克制" in json.dumps(context["domains"]["婚姻"], ensure_ascii=False)
    assert not any("unsupported" in str(value) for value in context["domains"].values())


def test_stage_decisions_produce_three_summaries_and_keep_minority_demoted() -> None:
    frozen_run, tasks = _frozen_run()
    decisions = [
        StageDecision(
            stage="structure",
            domain="事业",
            result="winner",
            task_id="task-事业",
            winner_claim_ids=("prediction-" + "b" * 20,),
            minority_claim_ids=("prediction-" + "c" * 20,),
            rationale="结构段形成主结论",
        ),
        StageDecision(
            stage="event",
            domain="事业",
            result="conflict_resolved",
            task_id="task-事业",
            winner_claim_ids=("prediction-" + "b" * 20,),
            minority_claim_ids=("prediction-" + "c" * 20,),
            conflict_type="occurrence_opposition",
            resolution_rule_id="CR-TEST",
            rationale="事件段冲突已消解",
        ),
        StageDecision(
            stage="timing",
            domain="事业",
            result="coexist",
            task_id="task-事业",
            winner_claim_ids=("prediction-" + "b" * 20, "prediction-" + "c" * 20),
            rationale="应期段并列保留",
        ),
    ]

    context = build_report_context_from_frozen_run(frozen_run, tasks, decisions)
    rendered_career = json.dumps(context["domains"]["事业"], ensure_ascii=False)

    assert context["structure_summary"]
    assert context["event_summary"]
    assert context["timing_summary"]
    assert "少数派观点" in rendered_career
    assert "冲突" in rendered_career


def test_high_risk_claims_are_separated_and_explicitly_warned() -> None:
    frozen_run, tasks = _frozen_run()

    context = build_report_context_from_frozen_run(frozen_run, tasks)
    health = context["domains"]["健康"]

    assert health["conclusions"] == []
    assert health["high_risk_notes"]
    assert any("风险" in text or "需关注" in text for text in health["high_risk_notes"])


def test_context_never_leaks_internal_identifiers() -> None:
    frozen_run, tasks = _frozen_run()
    context = build_report_context_from_frozen_run(frozen_run, tasks)
    rendered = json.dumps(context, ensure_ascii=False)

    forbidden_patterns = [
        r"claim-[0-9a-f]{20,}",
        r"prediction-[0-9a-f]{20,}",
        r"statement_id",
        r"statement_index",
        r"capability_posterior",
        r"school_capability snapshot",
        r"Agent 工作记录",
    ]
    for pattern in forbidden_patterns:
        assert not re.search(pattern, rendered), f"内部 ID 泄漏：{pattern}"


def _diff(status: str, legacy: object, claim: object) -> DimensionDifference:
    return DimensionDifference(status=status, legacy=legacy, claim=claim)  # type: ignore[arg-type]


def test_build_comparison_summary_extracts_public_differences_without_ids() -> None:
    item = RunComparisonItem(
        task_id="task-事业",
        school_id="gao_dechen",
        domain="事业",
        task_coverage=_diff("only_claim", None, True),
        claim_state=_diff("differ", "abstain", "claim"),
        event_label=_diff("differ", "旧事业判断", "新事业判断"),
        polarity=_diff("same", "positive", "positive"),
        time_window=_diff("same", {"label": "2028"}, {"label": "2028"}),
        risk_flag=_diff("differ", False, True),
        evidence_completeness=_diff("same", "full", "full"),
    )
    comparison = RunComparison(case_id="C-REPORT-001", items=(item,))

    summary = build_comparison_summary(comparison)
    rendered = json.dumps(summary, ensure_ascii=False)

    assert summary["coverage_delta"]
    assert summary["state_diff"]
    assert summary["high_risk_diff"]
    assert "事业" in rendered
    assert "claim_id" not in rendered
    assert not re.search(r"(?:claim|prediction)-[0-9a-f]{16,}", rendered)
