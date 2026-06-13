from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.application.feedback_parser import StatementFeedback
from engine.application.minimal_learning_loop import (
    FeedbackNormalizationError,
    analysis_pipeline,
    normalize_feedback_entries,
    update_confidence,
)
from engine.statement_runtime import enforce_statement_record


def _record() -> dict[str, object]:
    return {
        "statement_id": "S-001-abcdef",
        "case_id": "C-PHASE-A-001",
        "rule_id": "M1-D-001",
        "family_id": "FAM-M1-D",
        "school": "段",
        "canon": "duan",
        "rule_type": "runtime_rule",
        "statement_text": "事业有技术型输出。",
        "timestamp": "2026-06-13T00:00:00Z",
        "confidence_snapshot": {"percent": 50, "posterior_mean": 0.5},
    }


def test_statement_record_enforcement_marks_missing_as_unmapped() -> None:
    enforced = enforce_statement_record({"statement_id": "S-001-abcdef", "case_id": "C-PHASE-A-001"})

    assert enforced["statement_id"] == "S-001-abcdef"
    assert enforced["case_id"] == "C-PHASE-A-001"
    for field in ("rule_id", "family_id", "school", "canon", "rule_type", "statement_text", "timestamp"):
        assert enforced[field] == "UNMAPPED"


def test_feedback_normalization_accepts_only_structured_verdicts() -> None:
    feedbacks = [
        StatementFeedback("S-001-abcdef", "y", "hit"),
        StatementFeedback("S-001-bbbbbb", "n", "miss"),
        StatementFeedback("S-001-cccccc", "partial", "abstain"),
        StatementFeedback("S-001-dddddd", "skip", "no_data"),
    ]

    normalized = normalize_feedback_entries(feedbacks, case_id="C-PHASE-A-001", timestamp="2026-06-13T00:00:00Z")

    assert [item["verdict"] for item in normalized] == ["y", "n", "partial", "skip"]
    assert all(set(item) == {"statement_id", "case_id", "verdict", "timestamp"} for item in normalized)


@pytest.mark.parametrize("source_text", ["只是自然语言反馈", "✅"])
def test_feedback_normalization_rejects_unstructured_feedback(source_text: str) -> None:
    with pytest.raises(FeedbackNormalizationError):
        normalize_feedback_entries([], case_id="C-PHASE-A-001", source_text=source_text)


def test_update_confidence_applies_phase_a_formula_and_clamps() -> None:
    record = _record()
    state, log_y = update_confidence(record, {"case_id": "C-PHASE-A-001", "statement_id": "S-001-abcdef", "verdict": "y", "timestamp": "2026-06-13T00:00:00Z"})
    assert state["rule_confidence"]["M1-D-001"] == 0.55
    assert state["family_confidence"]["FAM-M1-D"] == 0.52
    assert log_y and log_y["changed"] is True

    state, log_n = update_confidence(record, {"case_id": "C-PHASE-A-001", "statement_id": "S-001-abcdef", "verdict": "n", "timestamp": "2026-06-13T00:00:01Z"}, state)
    assert state["rule_confidence"]["M1-D-001"] == 0.45
    assert state["family_confidence"]["FAM-M1-D"] == 0.47
    assert log_n and log_n["changed"] is True

    state, log_partial = update_confidence(record, {"case_id": "C-PHASE-A-001", "statement_id": "S-001-abcdef", "verdict": "partial"}, state)
    assert state["rule_confidence"]["M1-D-001"] == 0.45
    assert state["family_confidence"]["FAM-M1-D"] == 0.47
    assert log_partial and log_partial["changed"] is False

    state, log_skip = update_confidence(record, {"case_id": "C-PHASE-A-001", "statement_id": "S-001-abcdef", "verdict": "skip"}, state)
    assert log_skip is None


def test_analysis_pipeline_writes_minimal_storage_and_observable_change(tmp_path: Path) -> None:
    case_dir = tmp_path / "C-PHASE-A-001"
    envelope = {
        "schema_version": "statement_record.v1",
        "case_id": "C-PHASE-A-001",
        "records": [_record()],
    }
    feedbacks = [StatementFeedback("S-001-abcdef", "y", "hit")]

    result = analysis_pipeline(envelope, feedbacks, case_dir=case_dir)

    assert result["learning_summary"]["statement_record_count"] == 1
    assert result["learning_summary"]["updated_count"] == 1
    assert result["learning_summary"]["observable_confidence_changes"]

    learning_log = json.loads((case_dir / "learning_log.json").read_text(encoding="utf-8"))
    confidence_state = json.loads((case_dir / "updated_confidence_state.json").read_text(encoding="utf-8"))
    assert learning_log[0]["rule_confidence_before"] == 0.5
    assert learning_log[0]["rule_confidence_after"] == 0.55
    assert confidence_state["rule_confidence"]["M1-D-001"] == 0.55
