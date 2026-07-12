import json
import subprocess
import sys
from pathlib import Path

import pytest

from engine.evaluation.freeze import freeze_outputs
from engine.evaluation.models import BlindPrediction, BlindSchoolOutput

FIXTURE_ROOT = Path("tests/fixtures/school_capability")
MODULE = "tools.school_capability_baseline"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", MODULE, *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _output() -> BlindSchoolOutput:
    return BlindSchoolOutput(
        case_id="C-TEST-001",
        school_id="ziping",
        task_id="marriage.divorce_or_remarriage",
        state="claim",
        rationale="blind rationale",
        predictions=[BlindPrediction(
            prediction_id="P-001",
            event_label="occurred",
            probability=0.7,
            time_window={},
            evidence_refs=["F-001"],
            falsifier="not occurred",
        )],
    )


def test_cli_audit_writes_manifest_without_mutating_cases(tmp_path: Path) -> None:
    output = tmp_path / "manifest.json"
    input_path = FIXTURE_ROOT / "cases/C-TEST-001/input.md"
    before = input_path.read_bytes()

    result = _run(
        "audit",
        "--cases-dir", str(FIXTURE_ROOT / "cases"),
        "--reports-dir", str(FIXTURE_ROOT / "reports"),
        "--out", str(output),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "school-capability-case-manifest/v1"
    assert payload["records"][0]["eligibility"] == "development_only"
    assert input_path.read_bytes() == before


@pytest.mark.parametrize(
    "target",
    [
        "cases/forbidden.json",
        "theory/forbidden.json",
        "META/forbidden.json",
        "engine/expert-weights.yaml",
        "engine/domain-weights.yaml",
    ],
)
def test_cli_rejects_resolved_production_output_paths(tmp_path: Path, target: str) -> None:
    link = tmp_path / "redirect"
    try:
        link.symlink_to(Path(target).parent.resolve(), target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is unavailable")

    result = _run(
        "audit",
        "--cases-dir", str(FIXTURE_ROOT / "cases"),
        "--reports-dir", str(FIXTURE_ROOT / "reports"),
        "--out", str(link / Path(target).name),
    )

    assert result.returncode != 0
    assert "forbidden output path" in result.stderr


def test_cli_score_verifies_frozen_run_before_reading_labels(tmp_path: Path) -> None:
    run = freeze_outputs([_output()], "tasks-v1", "rules-v1").to_dict()
    run["outputs"][0]["rationale"] = "tampered"
    frozen_path = tmp_path / "frozen.json"
    frozen_path.write_text(json.dumps(run), encoding="utf-8")

    result = _run(
        "score",
        "--frozen-run", str(frozen_path),
        "--labels", str(tmp_path / "missing-labels.json"),
        "--tasks", "mapping/school-capability-task-catalog-v1.yaml",
        "--out", str(tmp_path / "scores.json"),
    )

    assert result.returncode != 0
    assert "freeze hash mismatch" in result.stderr
    assert "missing-labels" not in result.stderr


def test_cli_score_binary_json_contract_is_explicit(tmp_path: Path) -> None:
    run = freeze_outputs([_output()], "tasks-v1", "rules-v1")
    frozen_path = tmp_path / "frozen.json"
    frozen_path.write_text(json.dumps(run.to_dict()), encoding="utf-8")
    labels_path = tmp_path / "labels.json"
    labels_path.write_text(json.dumps({
        "schema_version": "school-capability-labels/v1",
        "freeze_hash": run.freeze_hash,
        "labels": [{
            "case_id": "C-TEST-001",
            "task_id": "marriage.divorce_or_remarriage",
            "label": "occurred",
            "observed_at": "2026-01-01",
            "source": "fixture",
            "confidence_grade": "A",
            "quantifiable": True,
            "conflict_state": "none",
        }],
    }), encoding="utf-8")
    tasks_path = tmp_path / "tasks.json"
    tasks_path.write_text(json.dumps({
        "schema_version": "school-capability-cli-tasks/v1",
        "tasks": [{
            "task_id": "marriage.divorce_or_remarriage",
            "domain": "marriage",
            "claim_type": "event",
            "scoring_method": "binary_probability",
            "quantifiable": True,
            "high_risk": False,
            "allowed_time_horizons": ["lifetime"],
            "required_input_fields": [],
            "label_schema": {"positive_label": "occurred", "negative_label": "not_occurred"},
            "evaluation_note": "fixture",
        }],
        "eligible_case_tasks": [["C-TEST-001", "marriage.divorce_or_remarriage"]],
        "score_weights": {"C-TEST-001|marriage.divorce_or_remarriage|ziping": 0.5},
    }), encoding="utf-8")
    output = tmp_path / "scores.json"

    result = _run(
        "score", "--frozen-run", str(frozen_path), "--labels", str(labels_path),
        "--tasks", str(tasks_path), "--out", str(output),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "school-capability-scores/v1"
    assert payload["eligible_case_tasks"] == [["C-TEST-001", "marriage.divorce_or_remarriage"]]
    assert payload["claim_probabilities"]["C-TEST-001|marriage.divorce_or_remarriage|ziping"] == 0.7
    assert payload["score_weights"]["C-TEST-001|marriage.divorce_or_remarriage|ziping"] == 0.5


def test_cli_freeze_and_report_round_trip(tmp_path: Path) -> None:
    outputs_path = tmp_path / "outputs.json"
    outputs_path.write_text(json.dumps({
        "schema_version": "school-capability-outputs/v1",
        "outputs": [_output().to_dict()],
    }), encoding="utf-8")
    tasks_path = tmp_path / "tasks.json"
    tasks_path.write_text(json.dumps({"task_catalog_version": "tasks-v1"}), encoding="utf-8")
    snapshot_path = tmp_path / "snapshot.json"
    snapshot_path.write_text(json.dumps({"rule_snapshot_id": "rules-v1"}), encoding="utf-8")
    frozen_path = tmp_path / "frozen.json"

    frozen = _run(
        "freeze", "--outputs", str(outputs_path), "--tasks", str(tasks_path),
        "--rule-snapshot", str(snapshot_path), "--out", str(frozen_path),
    )
    assert frozen.returncode == 0, frozen.stderr

    scores_path = tmp_path / "scores.json"
    scores_path.write_text(json.dumps({
        "schema_version": "school-capability-scores/v1",
        "experiment_summary": {},
        "posteriors": [],
    }), encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({
        "schema_version": "school-capability-case-manifest/v1",
        "records": [{"eligibility": "development_only"}],
    }), encoding="utf-8")
    report_path = tmp_path / "baseline.md"

    reported = _run(
        "report", "--scores", str(scores_path), "--manifest", str(manifest_path),
        "--out", str(report_path),
    )
    assert reported.returncode == 0, reported.stderr
    assert "HOLD" in report_path.read_text(encoding="utf-8")
