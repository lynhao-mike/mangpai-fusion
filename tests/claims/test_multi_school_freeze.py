from __future__ import annotations

import ast
import json
from dataclasses import replace
from pathlib import Path

import pytest

from engine.claims import Claim, Evidence, TimeWindow, claim_to_blind_output
from engine.claims.orchestrator import generate_frozen_claim_run
from engine.decision.models import ChartFactLedger
from engine.evaluation.freeze import canonical_json, verify_frozen_run
from engine.evaluation.models import BlindTask
from engine.evaluation.task_catalog import load_task_catalog


CATALOG_PATH = Path("mapping/school-capability-task-catalog-v1.yaml")
TASK_IDS = (
    "structure.overview",
    "career.role_change",
    "marriage.divorce_or_remarriage",
    "wealth.debt",
    "career.path_type",
    "health.system_risk",
    "career.change_window",
    "marriage.event_window",
    "health.event_window",
    "wealth.major_loss_window",
)
SCHOOLS = ("ziping", "ditiansui", "duan", "ren", "gao", "yang")


def _catalog_tasks() -> list[BlindTask]:
    indexed = {task.task_id: task for task in load_task_catalog(CATALOG_PATH)}
    return [indexed[task_id] for task_id in TASK_IDS]


def _task(
    task_id: str,
    *,
    claim_type: str,
    scoring_method: str,
    label_schema: dict[str, object],
    allowed_time_horizons: tuple[str, ...] = ("lifetime", "ten_year", "annual"),
) -> BlindTask:
    return BlindTask(
        task_id=task_id,
        domain="测试",
        claim_type=claim_type,
        scoring_method=scoring_method,
        quantifiable=bool(label_schema),
        high_risk=False,
        allowed_time_horizons=list(allowed_time_horizons),
        required_input_fields=["four_pillars"],
        label_schema=label_schema,
        evaluation_note="Task 6 adapter boundary fixture",
    )


def _evidence(evidence_id: str) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        fact_refs=("four_pillars.day",),
        feature_refs=(),
        rule_id="TEST-RULE-V1",
        text=f"evidence {evidence_id}",
    )


def _claim(
    task: BlindTask,
    *,
    claim_id: str = "claim-stable-adapter-boundary",
    school_id: str = "gao",
    claim_type: str = "event_claim",
    confidence: float = 0.37,
    time_window: TimeWindow | None = TimeWindow(1900, 2100, "lifetime"),
    predicted_label: str | None = None,
    evidence_ids: tuple[str, ...] = ("evidence-first",),
) -> Claim:
    snapshot: dict[str, object] = {"fixture": True}
    if predicted_label is not None:
        snapshot["predicted_label"] = predicted_label
    return Claim(
        claim_id=claim_id,
        school_id=school_id,
        task_id=task.task_id,
        claim_type=claim_type,  # type: ignore[arg-type]
        stance="support",
        statement="稳定自然语言断语，不得替代机器分类标签。",
        evidence=tuple(_evidence(item) for item in evidence_ids),
        falsifier="若独立事实不支持则证伪。",
        time_window=time_window,
        confidence_basis="由原始证据强度直接确定。",
        applicability_snapshot=snapshot,
        confidence=confidence,
    )


def test_binary_event_uses_positive_label_and_exact_claim_confidence() -> None:
    task = _task(
        "wealth.debt",
        claim_type="binary_event",
        scoring_method="binary_probability",
        label_schema={"type": "boolean", "positive_label": "occurred", "negative_label": "not_observed"},
    )
    output = claim_to_blind_output(_claim(task, confidence=0.41), case_id="C-ADAPTER-BINARY", task=task)

    prediction = output.predictions[0]
    assert prediction.event_label == "occurred"
    assert prediction.probability == 0.41
    assert prediction.time_window == {"start_year": 1900, "end_year": 2100, "label": "lifetime"}


def test_timing_event_uses_catalog_event_and_preserves_exact_window() -> None:
    task = _task(
        "career.change_window",
        claim_type="event_timing",
        scoring_method="time_window",
        label_schema={"type": "object", "event": "career_change"},
        allowed_time_horizons=("ten_year", "annual"),
    )
    claim = _claim(
        task,
        claim_type="timing_claim",
        confidence=0.53,
        time_window=TimeWindow(2027, 2027, "annual"),
    )

    prediction = claim_to_blind_output(claim, case_id="C-ADAPTER-TIMING", task=task).predictions[0]
    assert prediction.event_label == "career_change"
    assert prediction.fact_refs == tuple(sorted({
        ref for evidence in claim.evidence for ref in evidence.fact_refs
    }))
    assert prediction.probability == 0.53
    assert prediction.time_window == {"start_year": 2027, "end_year": 2027, "label": "annual"}


def test_categorical_event_uses_validated_predicted_label() -> None:
    task = _task(
        "health.system_risk",
        claim_type="categorical_state",
        scoring_method="multiclass_probability",
        label_schema={"type": "categorical", "labels": ["low", "moderate", "high"]},
    )
    output = claim_to_blind_output(
        _claim(task, predicted_label="moderate", confidence=0.58),
        case_id="C-ADAPTER-CATEGORICAL",
        task=task,
    )
    assert output.predictions[0].event_label == "moderate"
    assert output.predictions[0].probability == 0.58


@pytest.mark.parametrize(
    ("predicted_label", "message"),
    [(None, "predicted_label"), ("critical", "allowed labels")],
)
def test_categorical_event_rejects_missing_or_illegal_predicted_label(
    predicted_label: str | None, message: str,
) -> None:
    task = _task(
        "health.system_risk",
        claim_type="categorical_state",
        scoring_method="multiclass_probability",
        label_schema={"type": "categorical", "labels": ["low", "moderate", "high"]},
    )
    with pytest.raises(ValueError, match=message):
        claim_to_blind_output(
            _claim(task, predicted_label=predicted_label),
            case_id="C-ADAPTER-BAD-LABEL",
            task=task,
        )


def test_structure_claim_has_empty_window_and_statement_payload() -> None:
    task = _task(
        "structure.overview",
        claim_type="structure_claim",
        scoring_method="portrait_agreement",
        label_schema={},
        allowed_time_horizons=("lifetime",),
    )
    claim = _claim(task, claim_type="structure_claim", time_window=None, confidence=0.71)

    prediction = claim_to_blind_output(claim, case_id="C-ADAPTER-STRUCTURE", task=task).predictions[0]
    assert prediction.event_label == claim.statement
    assert prediction.probability == 0.71
    assert prediction.time_window == {}


def test_claim_and_task_type_incompatibility_is_rejected_explicitly() -> None:
    task = _task(
        "career.change_window",
        claim_type="event_timing",
        scoring_method="time_window",
        label_schema={"type": "object", "event": "career_change"},
        allowed_time_horizons=("ten_year", "annual"),
    )
    incompatible = _claim(task, claim_type="event_claim", time_window=TimeWindow(1900, 2100, "lifetime"))

    with pytest.raises(ValueError, match=r"event_claim.*event_timing"):
        claim_to_blind_output(incompatible, case_id="C-ADAPTER-TYPE", task=task)


def test_evidence_order_is_complete_and_prediction_id_is_claim_derived() -> None:
    task = _task(
        "wealth.debt",
        claim_type="binary_event",
        scoring_method="binary_probability",
        label_schema={"type": "boolean", "positive_label": "occurred"},
    )
    claim = _claim(task, evidence_ids=("evidence-z", "evidence-a", "evidence-m"))

    first = claim_to_blind_output(claim, case_id="C-ADAPTER-EVIDENCE", task=task)
    second = claim_to_blind_output(claim, case_id="C-ADAPTER-EVIDENCE", task=task)
    other = claim_to_blind_output(
        replace(claim, claim_id="claim-other-school-task-rule", school_id="duan"),
        case_id="C-ADAPTER-EVIDENCE",
        task=task,
    )

    assert first.predictions[0].evidence_refs == ("evidence-z", "evidence-a", "evidence-m")
    assert first.predictions[0].prediction_id == second.predictions[0].prediction_id
    assert first.predictions[0].prediction_id != other.predictions[0].prediction_id


def _complete_chart() -> ChartFactLedger:
    return ChartFactLedger(
        sex_marker="乾",
        solar_datetime="1990-06-15T12:00:00+08:00",
        four_pillars={"year": "丙午", "month": "丙午", "day": "丁巳", "hour": "丙午"},
        start_luck="1998",
        dayun_steps=[{"ganzhi": "丙辰", "start_year": 2018, "end_year": 2027}],
        liunian_steps=[
            {"year": 2024, "ganzhi": "甲辰", "dayun": "丙辰"},
            {"year": 2025, "ganzhi": "乙巳", "dayun": "丙辰"},
            {"year": 2026, "ganzhi": "丙午", "dayun": "丙辰"},
        ],
    )


def test_default_six_school_ten_task_matrix_freezes_deterministically() -> None:
    kwargs = {
        "case_id": "C-TASK6-MULTI-SCHOOL",
        "task_catalog_version": "school-capability-tasks/v1",
        "rule_snapshot_id": "task6-runner-snapshot-v1",
        "schools": SCHOOLS,
    }
    first = generate_frozen_claim_run(_complete_chart(), _catalog_tasks(), **kwargs)
    second = generate_frozen_claim_run(_complete_chart(), _catalog_tasks(), **kwargs)

    assert len(first.outputs) == 60
    assert {row.school_id for row in first.outputs} == set(SCHOOLS)
    assert {row.task_id for row in first.outputs} == set(TASK_IDS)
    assert {row.state for row in first.outputs} == {"claim", "abstain", "unsupported"}
    assert [(row.case_id, row.task_id, row.school_id) for row in first.outputs] == sorted(
        (row.case_id, row.task_id, row.school_id) for row in first.outputs
    )
    for row in first.outputs:
        assert row.rationale
        if row.state == "claim":
            assert len(row.predictions) == 1
            prediction = row.predictions[0]
            assert prediction.prediction_id
            assert 0.0 <= prediction.probability <= 1.0
            assert prediction.evidence_refs
            assert prediction.falsifier
        else:
            assert row.predictions == ()

    verify_frozen_run(first)
    verify_frozen_run(second)
    assert first.freeze_hash == second.freeze_hash
    assert first.to_dict() == second.to_dict()
    assert canonical_json(first.to_dict()).encode("utf-8") == canonical_json(second.to_dict()).encode("utf-8")


def _imported_modules(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    return tuple(imported)


def test_freeze_chain_and_six_runners_are_statically_isolated_from_revealed_data() -> None:
    forbidden_import_tokens = (
        "feedback",
        "labels",
        "revealed_label",
        "render_report",
        "report_view",
        "cases",
        "school_claims",
    )
    files = (
        "engine/claims/blind_adapter.py",
        "engine/claims/orchestrator.py",
        "engine/claims/runner_registry.py",
        "engine/v5/ziping_runner.py",
        "engine/v5/ditiansui_runner.py",
        "engine/v5/duan_runner.py",
        "engine/v5/ren_runner.py",
        "engine/v5/gao_runner.py",
        "engine/v5/yang_runner.py",
    )
    for relative in files:
        imports = _imported_modules(Path(relative))
        assert not any(token in module.lower() for token in forbidden_import_tokens for module in imports), relative

    frozen = generate_frozen_claim_run(
        _complete_chart(),
        _catalog_tasks(),
        case_id="C-TASK6-LEAKAGE",
        task_catalog_version="school-capability-tasks/v1",
        rule_snapshot_id="task6-runner-snapshot-v1",
        schools=SCHOOLS,
    )
    serialized = json.dumps(frozen.to_dict(), ensure_ascii=False, sort_keys=True)
    forbidden_keys = ("feedback", "known_facts", "report_text", "revealed_labels", "school_claims")
    assert not any(f'"{key}"' in serialized for key in forbidden_keys)
