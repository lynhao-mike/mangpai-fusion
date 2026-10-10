from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from engine.claims import (
    Claim,
    Evidence,
    TaskUnsupported,
    TimeWindow,
    claim_to_blind_output,
    stable_claim_id,
    validate_claim_evidence,
)
from engine.claims.orchestrator import generate_blind_outputs, generate_frozen_claim_run
from engine.decision.models import ChartFactLedger
from engine.evaluation.freeze import freeze_outputs
from engine.evaluation.models import BlindTask, RevealedLabel
from engine.evaluation.scoring import score_output
from engine.evaluation.task_catalog import load_task_catalog
from engine.features import build_chart_feature_vector
from engine.v5 import run_v5
from engine.v5.ren_runner import generate_claims as generate_ren_claims
from engine.v5.ziping_runner import generate_claims as generate_ziping_claims


def _task(
    task_id: str,
    *,
    domain: str = "总体",
    claim_type: str = "structure",
    scoring_method: str = "portrait_agreement",
    quantifiable: bool = False,
) -> BlindTask:
    label_schema: dict[str, object] = {}
    if scoring_method == "time_window":
        label_schema = {
            "type": "object",
            "required": ["occurred", "year"],
            "occurred": "boolean",
            "year": "integer_or_null",
        }
    return BlindTask(
        task_id=task_id,
        domain=domain,
        claim_type=claim_type,
        scoring_method=scoring_method,
        quantifiable=quantifiable,
        high_risk=False,
        allowed_time_horizons=["annual"],
        required_input_fields=["four_pillars"],
        label_schema=label_schema,
        evaluation_note="claim-engine fixture",
    )


def _full_chart(**overrides: object) -> ChartFactLedger:
    values = {
        "sex_marker": "乾",
        "four_pillars": {"year": "庚申", "month": "庚申", "day": "甲午", "hour": "辛酉"},
    }
    values.update(overrides)
    return ChartFactLedger(**values)


def test_claim_contract_rejects_dangling_evidence_and_has_stable_identity() -> None:
    chart = _full_chart()
    features = build_chart_feature_vector(chart)
    task = _task("structure.overview")
    evidence = Evidence(
        evidence_id="E-1",
        fact_refs=("four_pillars.day",),
        feature_refs=("supporting_count",),
        rule_id="ZIPING-STRENGTH-V1",
        text="日主生扶计数可解析。",
    )
    claim = Claim(
        claim_id=stable_claim_id("ziping", task.task_id, features.chart_id, evidence.rule_id),
        school_id="ziping",
        task_id=task.task_id,
        claim_type="structure_claim",
        stance="support",
        statement="身弱结构主线。",
        evidence=(evidence,),
        falsifier="若独立复核不呈身弱结构，则证伪。",
        time_window=None,
        confidence_basis="生扶少于克泄耗且无根。",
        applicability_snapshot={"supporting_count": features.supporting_count},
    )

    validate_claim_evidence(claim, chart, features)
    assert claim.claim_id == stable_claim_id("ziping", task.task_id, features.chart_id, evidence.rule_id)
    assert replace(claim).to_dict() == claim.to_dict()

    dangling = replace(
        claim,
        evidence=(replace(evidence, feature_refs=("strength.nonexistent",)),),
    )
    with pytest.raises(ValueError, match="strength.nonexistent"):
        validate_claim_evidence(dangling, chart, features)

    with pytest.raises(ValueError, match="evidence"):
        replace(claim, evidence=())
    with pytest.raises(ValueError, match="time_window"):
        replace(claim, claim_type="timing_claim")

    other_chart = ChartFactLedger(
        four_pillars={"year": "甲子", "month": "乙丑", "day": "戊辰", "hour": "己未"}
    )
    with pytest.raises(ValueError, match="same chart"):
        validate_claim_evidence(claim, other_chart, features)


def test_ziping_generates_feature_derived_structure_claims_and_abstains_at_boundaries() -> None:
    weak_chart = _full_chart()
    weak_features = build_chart_feature_vector(weak_chart)
    task = _task("structure.overview")

    first = generate_ziping_claims(weak_chart, weak_features, task)
    second = generate_ziping_claims(weak_chart, weak_features, task)

    assert first == second
    assert first
    assert any("身弱" in claim.statement for claim in first)
    assert all(claim.school_id == "ziping" and claim.task_id == task.task_id for claim in first)
    assert all(claim.evidence and claim.falsifier for claim in first)
    for claim in first:
        validate_claim_evidence(claim, weak_chart, weak_features)

    neutral_chart = ChartFactLedger(
        four_pillars={"year": "庚申", "month": "戊寅", "day": "壬子", "hour": "辛丑"}
    )
    neutral_claims = generate_ziping_claims(
        neutral_chart,
        build_chart_feature_vector(neutral_chart),
        task,
    )
    assert not any("身强结构主线" in claim.statement or "身弱结构主线" in claim.statement for claim in neutral_claims)

    no_hour_chart = ChartFactLedger(
        four_pillars={"year": "庚申", "month": "庚申", "day": "甲午", "hour": "_"},
        missing_fields=["$FOUR.hour"],
    )
    assert generate_ziping_claims(
        no_hour_chart,
        build_chart_feature_vector(no_hour_chart),
        task,
    ) == []

    with pytest.raises(TaskUnsupported):
        generate_ziping_claims(weak_chart, weak_features, _task("marriage.event_window"))


def test_ren_generates_reproducible_timing_claim_only_from_computable_trigger() -> None:
    task = _task(
        "career.change_window",
        domain="事业",
        claim_type="event_timing",
        scoring_method="time_window",
        quantifiable=True,
    )
    triggered_chart = _full_chart(
        four_pillars={"year": "癸未", "month": "甲寅", "day": "壬戌", "hour": "丙午"},
        dayun_steps=[{"ganzhi": "丙辰", "start_year": 2018, "end_year": 2027}],
        liunian_steps=[{"year": 2024, "ganzhi": "甲辰", "dayun": "丙辰"}],
    )
    features = build_chart_feature_vector(triggered_chart)

    claims = generate_ren_claims(triggered_chart, features, task)

    assert claims == generate_ren_claims(triggered_chart, features, task)
    assert len(claims) == 1
    claim = claims[0]
    assert claim.claim_type == "timing_claim"
    assert claim.time_window == TimeWindow(start_year=2024, end_year=2024, label="annual")
    assert "2024" in claim.statement
    assert "该时间窗内未发生" in claim.falsifier
    assert any("liunian_steps.0" in ref for evidence in claim.evidence for ref in evidence.fact_refs)
    validate_claim_evidence(claim, triggered_chart, features)

    quiet_chart = ChartFactLedger(
        four_pillars={"year": "甲子", "month": "乙丑", "day": "戊辰", "hour": "己未"},
        liunian_steps=[{"year": 2025, "ganzhi": "乙巳"}],
    )
    assert generate_ren_claims(quiet_chart, build_chart_feature_vector(quiet_chart), task) == []

    changed_chart = replace(triggered_chart, liunian_steps=[{"year": 2030, "ganzhi": "庚戌", "dayun": "丁巳"}])
    changed = generate_ren_claims(changed_chart, build_chart_feature_vector(changed_chart), task)
    assert changed and changed[0].time_window != claim.time_window


def test_claim_runners_are_statically_isolated_from_feedback_and_reports() -> None:
    forbidden = ("feedback", "render_report", "report_view", "reports")
    for relative in (
        "engine/v5/ziping_runner.py",
        "engine/v5/ren_runner.py",
        "engine/claims/orchestrator.py",
    ):
        tree = ast.parse(Path(relative).read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        assert not any(token in imported for imported in imports for token in forbidden)

    assert not any("feedback" in field for field in ChartFactLedger.__dataclass_fields__)


def test_generated_timing_claim_freezes_and_scores_in_blind_evaluation_chain() -> None:
    task = _task(
        "career.change_window",
        domain="事业",
        claim_type="event_timing",
        scoring_method="time_window",
        quantifiable=True,
    )
    chart = _full_chart(
        four_pillars={"year": "癸未", "month": "甲寅", "day": "壬戌", "hour": "丙午"},
        dayun_steps=[{"ganzhi": "丙辰", "start_year": 2018, "end_year": 2027}],
        liunian_steps=[{"year": 2024, "ganzhi": "甲辰", "dayun": "丙辰"}],
    )
    claim = generate_ren_claims(chart, build_chart_feature_vector(chart), task)[0]
    output = claim_to_blind_output(claim, case_id="C-L2-001", task=task)

    frozen = freeze_outputs([output], "school-capability-tasks/v1", "l2-claim-rules-v1")
    label = RevealedLabel(
        case_id="C-L2-001",
        task_id=task.task_id,
        label={"occurred": True, "year": 2024},
        observed_at="2026-01-01",
        source="independent-review",
        confidence_grade="A",
        quantifiable=True,
        conflict_state="none",
        reviewer="fixture-reviewer",
    )
    score = score_output(frozen.outputs[0], task, label)

    assert frozen.outputs[0].state == "claim"
    assert frozen.outputs[0].predictions[0].evidence_refs
    assert score.timing_score == 1.0


def test_default_v5_blind_adapter_generates_two_school_outputs_from_chart_not_manual_claim_json() -> None:
    structure_task = _task("structure.overview")
    timing_task = _task(
        "career.change_window",
        domain="事业",
        claim_type="event_timing",
        scoring_method="time_window",
        quantifiable=True,
    )
    chart = {
        "case_id": "C-L2-DEFAULT",
        "gender_marker": "乾",
        "pillars": {"year": "癸未", "month": "甲寅", "day": "壬戌", "hour": "丙午"},
        "dayun_steps": [{"ganzhi": "丙辰", "start_year": 2018, "end_year": 2027}],
        "liunian_steps": [{"year": 2024, "ganzhi": "甲辰", "dayun": "丙辰"}],
    }
    v5_output = run_v5(chart, case_id="C-L2-DEFAULT", claims=[])

    rows = generate_blind_outputs(
        v5_output.chart,
        [structure_task, timing_task],
        case_id=v5_output.case_id,
        schools=["ziping", "ren"],
    )
    indexed = {(row.school_id, row.task_id): row for row in rows}

    assert indexed[("ziping", "structure.overview")].state in {"claim", "abstain"}
    assert indexed[("ziping", "career.change_window")].state == "unsupported"
    assert indexed[("ren", "structure.overview")].state == "unsupported"
    assert indexed[("ren", "career.change_window")].state == "claim"
    ren_prediction = indexed[("ren", "career.change_window")].predictions[0]
    assert ren_prediction.time_window["start_year"] == 2024
    assert ren_prediction.evidence_refs
    assert all("manual" not in row.rationale.lower() for row in rows)

    frozen = generate_frozen_claim_run(
        v5_output.chart,
        [structure_task, timing_task],
        case_id=v5_output.case_id,
        task_catalog_version="school-capability-tasks/v1",
        rule_snapshot_id="l2-engine-rules-v1",
        schools=["ziping", "ren"],
    )
    assert len(frozen.outputs) == 4
    assert {item.case_id + "|" + item.school_id + "|" + item.task_id for item in frozen.outputs} == {
        item.case_id + "|" + item.school_id + "|" + item.task_id for item in rows
    }
    tree = ast.parse(Path("engine/claims/orchestrator.py").read_text(encoding="utf-8"))
    imported_modules = [
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    ]
    assert not any("report" in module or "feedback" in module for module in imported_modules)
    assert "engine.v5.domain" not in imported_modules


def test_default_blind_adapter_abstains_when_evidence_is_insufficient_without_reading_v5_claims() -> None:
    task = _task(
        "career.change_window",
        domain="事业",
        claim_type="event_timing",
        scoring_method="time_window",
        quantifiable=True,
    )
    output = run_v5(
        {
            "case_id": "C-L2-ABSTAIN",
            "pillars": {"year": "甲子", "month": "乙丑", "day": "戊辰", "hour": "己未"},
            "liunian_steps": [{"year": 2025, "ganzhi": "乙巳"}],
        },
        claims=[],
    )

    rows = generate_blind_outputs(output.chart, [task], case_id=output.case_id, schools=["ren"])

    assert len(rows) == 1
    assert rows[0].state == "abstain"
    assert rows[0].predictions == ()


def test_production_task_catalog_exposes_ziping_structure_task_for_default_orchestration() -> None:
    tasks = load_task_catalog(Path("mapping/school-capability-task-catalog-v1.yaml"))
    structure_task = next(task for task in tasks if task.task_id == "structure.overview")

    rows = generate_blind_outputs(
        {
            "pillars": {"year": "庚申", "month": "庚申", "day": "甲午", "hour": "辛酉"},
        },
        [structure_task],
        case_id="C-L2-CATALOG",
        schools=["ziping", "ren"],
    )

    indexed = {row.school_id: row for row in rows}
    assert indexed["ziping"].state == "abstain"
    assert indexed["ziping"].predictions == ()
    assert "unresolved competition" in indexed["ziping"].rationale
    assert indexed["ren"].state == "unsupported"


def test_default_orchestrator_abstains_when_task_required_chart_fact_is_missing() -> None:
    task = _task(
        "marriage.event_window",
        domain="婚姻",
        claim_type="event_timing",
        scoring_method="time_window",
        quantifiable=True,
    )
    task = replace(task, required_input_fields=("four_pillars", "sex_marker"))

    rows = generate_blind_outputs(
        {
            "pillars": {"year": "癸未", "month": "甲寅", "day": "壬戌", "hour": "丙午"},
            "liunian_steps": [{"year": 2024, "ganzhi": "甲辰", "dayun": "丙辰"}],
        },
        [task],
        case_id="C-L2-MISSING-SEX",
        schools=["ren"],
    )

    assert len(rows) == 1
    assert rows[0].state == "abstain"
    assert "sex_marker" in rows[0].rationale


def test_default_orchestrator_reports_unknown_school_as_unsupported_before_input_completeness() -> None:
    task = replace(_task("structure.overview"), required_input_fields=("four_pillars", "sex_marker"))

    rows = generate_blind_outputs(
        {"pillars": {"year": "庚申", "month": "庚申", "day": "甲午", "hour": "辛酉"}},
        [task],
        case_id="C-L2-UNKNOWN-SCHOOL",
        schools=["unknown-school"],
    )

    assert len(rows) == 1
    assert rows[0].state == "unsupported"
