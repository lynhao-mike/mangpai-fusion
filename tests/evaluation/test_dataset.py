import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools.school_capability_dataset import build_inventory, build_unbound_labels


def _write_case(root: Path, case_id: str, *, report: str = "") -> None:
    case = root / "cases" / case_id
    case.mkdir(parents=True)
    (case / "input.md").write_text("四柱：甲子 乙丑 丙寅 丁卯\n性别：乾\n", encoding="utf-8")
    (case / "feedback.md").write_text("2023 年：入职结果已确认。\n", encoding="utf-8")
    if report:
        reports = root / "reports"
        reports.mkdir(exist_ok=True)
        (reports / f"{case_id}-content-report.md").write_text(report, encoding="utf-8")


def _catalog(*, high_risk: bool = False) -> dict:
    return {
        "schema_version": "school-capability-cli-tasks/v1",
        "tasks": [{
            "task_id": "career.role_change",
            "domain": "事业",
            "claim_type": "binary_event",
            "scoring_method": "binary_probability",
            "quantifiable": True,
            "high_risk": high_risk,
            "allowed_time_horizons": ["ten_year"],
            "required_input_fields": ["four_pillars"],
            "label_schema": {"positive_label": "occurred", "negative_label": "not_observed"},
            "evaluation_note": "fixture",
        }],
    }


def _observation(**updates: object) -> dict:
    item = {
        "case_id": "C-CLEAN-001",
        "task_id": "career.role_change",
        "label": "occurred",
        "source": "cases/C-CLEAN-001/feedback.md:1",
        "observed_at": "2023-01-01",
        "confidence_grade": "A",
        "quantifiable": True,
        "conflict_state": "none",
        "reviewer": "human-a",
    }
    item.update(updates)
    return item


def test_inventory_defaults_unreviewed_case_to_development_only(tmp_path: Path) -> None:
    _write_case(tmp_path, "C-CLEAN-001")
    (tmp_path / "reports").mkdir(exist_ok=True)

    inventory = build_inventory(tmp_path / "cases", tmp_path / "reports", {
        "schema_version": "school-capability-review-decisions/v1", "records": [],
    })

    row = inventory["records"][0]
    assert row["classification"] == "development_only"
    assert "human_clean_review_missing" in row["contamination_evidence"]


def test_explicit_contamination_cannot_be_overridden_by_review(tmp_path: Path) -> None:
    _write_case(tmp_path, "C-CONTAMINATED-001", report="本报告含反馈校准。")
    decisions = {
        "schema_version": "school-capability-review-decisions/v1",
        "records": [{
            "case_id": "C-CONTAMINATED-001",
            "classification": "historical_blind",
            "reviewed_by": "human-a",
            "reviewed_at": "2026-07-12",
            "provenance_evidence": ["source predates report"],
            "notes": "review fixture",
        }],
    }

    row = build_inventory(tmp_path / "cases", tmp_path / "reports", decisions)["records"][0]

    assert row["classification"] == "development_only"
    assert row["development_contaminated"] is True


def test_automated_reviewer_cannot_promote_clean_case(tmp_path: Path) -> None:
    _write_case(tmp_path, "C-CLEAN-001")
    (tmp_path / "reports").mkdir(exist_ok=True)
    decisions = {
        "schema_version": "school-capability-review-decisions/v1",
        "records": [{
            "case_id": "C-CLEAN-001", "classification": "historical_blind",
            "reviewed_by": "automated-bot", "reviewed_at": "2026-07-12T00:00:00Z",
            "provenance_evidence": ["cases/raw_feedback/source/sample.md:1"], "notes": "",
        }],
    }

    row = build_inventory(tmp_path / "cases", tmp_path / "reports", decisions)["records"][0]

    assert row["classification"] == "development_only"


def test_build_unbound_labels_requires_complete_metadata() -> None:
    labels = build_unbound_labels([_observation()], _catalog())

    assert labels["labels"][0]["label"] == "occurred"
    assert labels["labels"][0]["reviewer"] == "human-a"


def test_no_data_is_omitted_not_coerced_to_negative() -> None:
    labels = build_unbound_labels([_observation(label=None, disposition="no_data", quantifiable=False)], _catalog())

    assert labels["labels"] == []


def test_high_risk_label_requires_secondary_review() -> None:
    with pytest.raises(ValueError, match="secondary_reviewed_by"):
        build_unbound_labels([_observation()], _catalog(high_risk=True))


def test_conflicting_source_cannot_be_quantifiable() -> None:
    with pytest.raises(ValueError, match="conflicting_sources"):
        build_unbound_labels([_observation(conflict_state="conflicting_sources")], _catalog())


def test_time_window_label_schema_is_strict() -> None:
    catalog = _catalog()
    catalog["tasks"][0].update({
        "scoring_method": "time_window",
        "label_schema": {"type": "object", "required": ["occurred", "year"]},
    })
    with pytest.raises(ValueError, match="time_window"):
        build_unbound_labels([_observation(label={"occurred": "yes", "year": "2023"})], catalog)


def test_label_source_cannot_reference_system_output() -> None:
    with pytest.raises(ValueError, match="source"):
        build_unbound_labels([_observation(source="reports/leaked.md:1")], _catalog())


def test_label_metadata_types_are_strict() -> None:
    with pytest.raises(ValueError, match="quantifiable"):
        build_unbound_labels([_observation(quantifiable="yes")], _catalog())


def test_inventory_cli_dry_run_does_not_write(tmp_path: Path) -> None:
    _write_case(tmp_path, "C-CLEAN-001")
    (tmp_path / "reports").mkdir(exist_ok=True)
    decisions = tmp_path / "decisions.json"
    decisions.write_text(json.dumps({
        "schema_version": "school-capability-review-decisions/v1", "records": [],
    }), encoding="utf-8")
    target = tmp_path / "inventory.json"

    result = subprocess.run([
        sys.executable, "-m", "tools.school_capability_dataset", "inventory",
        "--cases-dir", str(tmp_path / "cases"), "--reports-dir", str(tmp_path / "reports"),
        "--review-decisions", str(decisions), "--out", str(target), "--dry-run",
    ], check=False, capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
    assert not target.exists()
