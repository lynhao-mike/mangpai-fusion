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


def _task_document() -> dict:
    return {
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
    }


def _evaluation_config() -> dict:
    return {
        "schema_version": "school-capability-evaluation-config/v1",
        "eligible_case_tasks": [["C-TEST-001", "marriage.divorce_or_remarriage"]],
        "baseline_prevalence_by_task": {"marriage.divorce_or_remarriage": 0.25},
        "case_metadata": {
            "C-TEST-001|marriage.divorce_or_remarriage|ziping": {
                "chart_prototype_id": "strong_day_master",
                "time_horizon": "lifetime",
                "evidence_completeness_band": "complete",
            },
        },
        "evidence_grade": "A",
        "evaluated_at": "2026-07-12T00:00:00Z",
        "score_weights": {"C-TEST-001|marriage.divorce_or_remarriage|ziping": 0.5},
        "gate_thresholds": {"coverage_complete": 1.0, "calibration_min_samples": 1, "calibration_max_error": 1.0, "high_risk_min_utility": -2.0},
    }


def _route(case_id: str = "C-TEST-001", prototype: str = "strong_day_master") -> dict:
    return {
        "school_id": "ziping",
        "task_id": "marriage.divorce_or_remarriage",
        "chart_prototype_id": prototype,
        "claim_type": "event",
        "time_horizon": "lifetime",
        "evidence_completeness_band": "complete",
    }


def _manifest() -> dict:
    return {
        "schema_version": "school-capability-case-manifest/v1",
        "generated_at": "2026-07-12T00:00:00Z",
        "reviewed_by": "reviewer-fixture",
        "expected_schools": ["ziping"],
        "records": [{
            "case_id": "C-TEST-001", "has_input": True, "has_feedback": True,
            "has_statement_index": False, "has_existing_report": False,
            "feedback_quantifiable": True, "contamination_flags": [],
            "eligibility": "blind_candidate", "evidence_notes": [],
            "eligible_routes": [_route()],
        }],
    }


def _write_score_inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path, Path]:
    tasks = _task_document()
    snapshot = {"rule_snapshot_id": "rules-v1", "rules": [{"id": "R-1"}]}
    from tools.school_capability_baseline import _canonical_digest
    run = freeze_outputs(
        [_output()],
        f"tasks-v1@sha256:{_canonical_digest(tasks)}",
        f"rules-v1@sha256:{_canonical_digest(snapshot)}",
    )
    frozen_path = tmp_path / "frozen.json"
    frozen_path.write_text(json.dumps(run.to_dict()), encoding="utf-8")
    labels_path = tmp_path / "labels.json"
    labels_path.write_text(json.dumps({
        "schema_version": "school-capability-labels/v1",
        "freeze_hash": run.freeze_hash,
        "labels": [{
            "case_id": "C-TEST-001", "task_id": "marriage.divorce_or_remarriage",
            "label": "occurred", "observed_at": "2026-01-01", "source": "fixture",
            "confidence_grade": "A", "quantifiable": True, "conflict_state": "none",
            "reviewer": "reviewer-fixture",
        }],
    }), encoding="utf-8")
    tasks_path = tmp_path / "tasks.json"
    tasks_path.write_text(json.dumps(tasks), encoding="utf-8")
    snapshot_path = tmp_path / "rule-snapshot.json"
    snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
    config_path = tmp_path / "evaluation-config.json"
    config_path.write_text(json.dumps(_evaluation_config()), encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_manifest()), encoding="utf-8")
    return frozen_path, labels_path, tasks_path, config_path, manifest_path, snapshot_path


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
    assert set(payload) == {"schema_version", "generated_at", "records"}
    assert payload["schema_version"] == "school-capability-case-audit/v1"
    assert payload["generated_at"].endswith("Z")
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

    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(_evaluation_config()), encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_manifest()), encoding="utf-8")
    snapshot_path = tmp_path / "snapshot.json"
    snapshot_path.write_text(json.dumps({"rule_snapshot_id": "rules-v1"}), encoding="utf-8")
    result = _run(
        "score",
        "--frozen-run", str(frozen_path),
        "--manifest", str(manifest_path),
        "--labels", str(tmp_path / "missing-labels.json"),
        "--tasks", "mapping/school-capability-task-catalog-v1.yaml",
        "--rule-snapshot", str(snapshot_path),
        "--evaluation-config", str(config_path),
        "--out", str(tmp_path / "scores.json"),
    )

    assert result.returncode != 0
    assert "freeze hash mismatch" in result.stderr
    assert "missing-labels" not in result.stderr


def test_cli_score_binary_json_contract_is_explicit_and_computed(tmp_path: Path) -> None:
    frozen_path, labels_path, tasks_path, config_path, manifest_path, snapshot_path = _write_score_inputs(tmp_path)
    output = tmp_path / "scores.json"

    result = _run(
        "score", "--frozen-run", str(frozen_path), "--manifest", str(manifest_path), "--labels", str(labels_path),
        "--tasks", str(tasks_path), "--rule-snapshot", str(snapshot_path), "--evaluation-config", str(config_path), "--out", str(output),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "school-capability-scores/v1"
    assert payload["eligible_case_tasks"] == [["C-TEST-001", "marriage.divorce_or_remarriage"]]
    assert payload["claim_probabilities"]["C-TEST-001|marriage.divorce_or_remarriage|ziping"] == 0.7
    assert payload["score_weights"]["C-TEST-001|marriage.divorce_or_remarriage|ziping"] == 0.5
    assert payload["scores"][0]["chart_prototype_id"] == "strong_day_master"
    assert payload["experiment_rows"]
    assert payload["experiment_summary"]
    assert payload["incremental_gains"] == {}  # one-school fixture has no assessable leave-one comparator
    assert payload["posteriors_computed"] is True
    assert len(payload["posteriors"]) == 1
    assert payload["posteriors"][0]["n_eff"] == 0.5
    identity = "ziping|marriage.divorce_or_remarriage|strong_day_master|event|lifetime|complete"
    assert payload["gate_input_summary"]["calibration_by_identity"][identity] == {
        "available": 1, "required": 1, "coverage": 1.0, "status": "available",
    }
    assert payload["gate_input_summary"]["coverage_by_identity"][identity] == 1.0
    assert payload["gate_input_summary"]["rule_snapshot_digest"].startswith("sha256:")


def test_cli_freeze_hash_binds_complete_task_and_rule_file_content(tmp_path: Path) -> None:
    outputs_path = tmp_path / "outputs.json"
    outputs_path.write_text(json.dumps({"schema_version": "school-capability-outputs/v1", "outputs": [_output().to_dict()]}), encoding="utf-8")
    tasks_path = tmp_path / "tasks.json"
    snapshot_path = tmp_path / "snapshot.json"
    tasks_path.write_text(json.dumps({"task_catalog_version": "tasks-v1", "extra": 1}), encoding="utf-8")
    snapshot_path.write_text(json.dumps({"rule_snapshot_id": "rules-v1", "rules": [1]}), encoding="utf-8")

    hashes = []
    for index in range(3):
        target = tmp_path / f"frozen-{index}.json"
        result = _run("freeze", "--outputs", str(outputs_path), "--tasks", str(tasks_path), "--rule-snapshot", str(snapshot_path), "--out", str(target))
        assert result.returncode == 0, result.stderr
        hashes.append(json.loads(target.read_text(encoding="utf-8"))["freeze_hash"])
        if index == 0:
            tasks_path.write_text(json.dumps({"task_catalog_version": "tasks-v1", "extra": 2}), encoding="utf-8")
        elif index == 1:
            snapshot_path.write_text(json.dumps({"rule_snapshot_id": "rules-v1", "rules": [2]}), encoding="utf-8")
    assert len(set(hashes)) == 3


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

    manifest_path = tmp_path / "manifest.json"
    manifest = {"schema_version": "school-capability-case-manifest/v1", "records": [{"eligibility": "development_only"}]}
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    from tools.school_capability_baseline import _canonical_digest
    scores_path = tmp_path / "scores.json"
    scores = {
        "schema_version": "school-capability-scores/v1",
        "experiment_summary": {},
        "posteriors_computed": True,
        "posteriors": [],
        "provenance": {"manifest_digest": f"sha256:{_canonical_digest(manifest)}", "task_catalog": "tasks@sha256:" + "0" * 64, "rule_snapshot": "rules@sha256:" + "0" * 64, "freeze_hash": "0" * 64},
        "gate_complete": False,
        "computed_gate_evidence": {},
    }
    scores["artifact_digest"] = f"sha256:{_canonical_digest(scores)}"
    scores_path.write_text(json.dumps(scores), encoding="utf-8")
    report_path = tmp_path / "baseline.md"

    reported = _run(
        "report", "--scores", str(scores_path), "--manifest", str(manifest_path),
        "--out", str(report_path),
    )
    assert reported.returncode == 0, reported.stderr
    assert "HOLD" in report_path.read_text(encoding="utf-8")


@pytest.mark.parametrize("scores", [
    {"schema_version": "school-capability-scores/v1"},
    {"schema_version": "school-capability-scores/v1", "posteriors": {}},
    {"schema_version": "school-capability-scores/v1", "posteriors": []},
])
def test_cli_report_rejects_uncomputed_or_invalid_posteriors(tmp_path: Path, scores: dict) -> None:
    scores_path = tmp_path / "scores.json"
    scores_path.write_text(json.dumps(scores), encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({"schema_version": "school-capability-case-manifest/v1", "generated_at": "now", "records": []}), encoding="utf-8")
    result = _run("report", "--scores", str(scores_path), "--manifest", str(manifest_path), "--out", str(tmp_path / "report.md"))
    assert result.returncode != 0
    assert "posteriors" in result.stderr


def test_cli_rejects_output_target_that_is_itself_a_symlink(tmp_path: Path) -> None:
    real = tmp_path / "real.json"
    link = tmp_path / "output.json"
    real.write_text("untouched", encoding="utf-8")
    try:
        link.symlink_to(real)
    except OSError:
        pytest.skip("symlink creation is unavailable")
    result = _run("audit", "--cases-dir", str(FIXTURE_ROOT / "cases"), "--reports-dir", str(FIXTURE_ROOT / "reports"), "--out", str(link))
    assert result.returncode != 0
    assert "symlink" in result.stderr
    assert real.read_text(encoding="utf-8") == "untouched"


def test_cli_score_rejects_forged_task_artifact_digest(tmp_path: Path) -> None:
    frozen_path, labels_path, tasks_path, config_path, manifest_path, snapshot_path = _write_score_inputs(tmp_path)
    run = json.loads(frozen_path.read_text(encoding="utf-8"))
    run["task_catalog_version"] = "tasks-v1@sha256:" + "0" * 64
    from engine.evaluation.freeze import compute_freeze_hash
    unsigned = dict(run)
    unsigned.pop("freeze_hash")
    run["freeze_hash"] = compute_freeze_hash(unsigned)
    frozen_path.write_text(json.dumps(run), encoding="utf-8")
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    labels["freeze_hash"] = run["freeze_hash"]
    labels_path.write_text(json.dumps(labels), encoding="utf-8")
    result = _run("score", "--frozen-run", str(frozen_path), "--manifest", str(manifest_path), "--labels", str(labels_path), "--tasks", str(tasks_path), "--rule-snapshot", str(snapshot_path), "--evaluation-config", str(config_path), "--out", str(tmp_path / "scores.json"))
    assert result.returncode != 0
    assert "task catalog digest mismatch" in result.stderr


@pytest.mark.parametrize("mutation,error", [
    (lambda thresholds: thresholds.pop("high_risk_min_utility"), "gate_complete"),
    (lambda thresholds: thresholds.__setitem__("unknown", 1), "unknown"),
    (lambda thresholds: thresholds.__setitem__("coverage_complete", True), "coverage_complete"),
])
def test_gate_threshold_schema_is_strict_but_missing_field_yields_hold_artifact(tmp_path: Path, mutation, error: str) -> None:
    frozen_path, labels_path, tasks_path, config_path, manifest_path, snapshot_path = _write_score_inputs(tmp_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    mutation(config["gate_thresholds"])
    config_path.write_text(json.dumps(config), encoding="utf-8")
    output = tmp_path / "scores.json"
    result = _run("score", "--frozen-run", str(frozen_path), "--manifest", str(manifest_path), "--labels", str(labels_path), "--tasks", str(tasks_path), "--rule-snapshot", str(snapshot_path), "--evaluation-config", str(config_path), "--out", str(output))
    if error == "gate_complete":
        assert result.returncode == 0, result.stderr
        payload = json.loads(output.read_text(encoding="utf-8"))
        assert payload["gate_complete"] is False
        assert payload["computed_gate_evidence"] == {}
    else:
        assert result.returncode != 0
        assert error in result.stderr


def test_reviewed_manifest_template_has_exact_cli_schema() -> None:
    template = json.loads(Path("templates/school-capability-case-manifest.json").read_text(encoding="utf-8"))
    assert set(template) == {"schema_version", "generated_at", "reviewed_by", "expected_schools", "records"}


def test_cli_report_rejects_tampered_manifest_and_hand_written_gate(tmp_path: Path) -> None:
    frozen_path, labels_path, tasks_path, config_path, manifest_path, snapshot_path = _write_score_inputs(tmp_path)
    scores_path = tmp_path / "scores.json"
    scored = _run("score", "--frozen-run", str(frozen_path), "--manifest", str(manifest_path), "--labels", str(labels_path), "--tasks", str(tasks_path), "--rule-snapshot", str(snapshot_path), "--evaluation-config", str(config_path), "--out", str(scores_path))
    assert scored.returncode == 0, scored.stderr
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["reviewed_by"] = "tampered"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    rejected = _run("report", "--scores", str(scores_path), "--manifest", str(manifest_path), "--out", str(tmp_path / "report.md"))
    assert rejected.returncode != 0
    assert "manifest digest mismatch" in rejected.stderr

    manifest_path.write_text(json.dumps(_manifest()), encoding="utf-8")
    scores = json.loads(scores_path.read_text(encoding="utf-8"))
    scores["computed_gate_evidence"] = {key: True for key in scores["computed_gate_evidence"]}
    scores_path.write_text(json.dumps(scores), encoding="utf-8")
    rejected = _run("report", "--scores", str(scores_path), "--manifest", str(manifest_path), "--out", str(tmp_path / "report.md"))
    assert rejected.returncode != 0
    assert "scores artifact digest mismatch" in rejected.stderr


def test_cli_report_recomputes_derived_gate_after_tamper_and_checksum_refresh(tmp_path: Path) -> None:
    frozen_path, labels_path, tasks_path, config_path, manifest_path, snapshot_path = _write_score_inputs(tmp_path)
    scores_path = tmp_path / "scores.json"
    scored = _run("score", "--frozen-run", str(frozen_path), "--manifest", str(manifest_path), "--labels", str(labels_path), "--tasks", str(tasks_path), "--rule-snapshot", str(snapshot_path), "--evaluation-config", str(config_path), "--out", str(scores_path))
    assert scored.returncode == 0, scored.stderr

    from tools.school_capability_baseline import _canonical_digest
    scores = json.loads(scores_path.read_text(encoding="utf-8"))
    scores["computed_gate_evidence"] = {
        "coverage_complete": True,
        "calibration_acceptable": True,
        "incremental_non_negative": True,
        "high_risk_safe": True,
        "provenance_valid": True,
    }
    scores.pop("artifact_digest")
    scores["artifact_digest"] = f"sha256:{_canonical_digest(scores)}"
    scores_path.write_text(json.dumps(scores), encoding="utf-8")

    report_path = tmp_path / "report.md"
    reported = _run("report", "--scores", str(scores_path), "--manifest", str(manifest_path), "--out", str(report_path))

    if reported.returncode == 0:
        text = report_path.read_text(encoding="utf-8")
        assert "**HOLD**" in text
        assert "READY_FOR_MANUAL_REVIEW" not in text
    else:
        assert "computed_gate_evidence mismatch" in reported.stderr


def test_cli_score_rejects_tampered_rule_snapshot_artifact(tmp_path: Path) -> None:
    frozen_path, labels_path, tasks_path, config_path, manifest_path, snapshot_path = _write_score_inputs(tmp_path)
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    snapshot["rules"].append({"id": "TAMPERED"})
    snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")

    result = _run(
        "score", "--frozen-run", str(frozen_path), "--manifest", str(manifest_path),
        "--labels", str(labels_path), "--tasks", str(tasks_path),
        "--rule-snapshot", str(snapshot_path), "--evaluation-config", str(config_path),
        "--out", str(tmp_path / "scores.json"),
    )

    assert result.returncode != 0
    assert "rule snapshot digest mismatch" in result.stderr


def test_high_risk_unassessable_forces_hold_and_is_audited(tmp_path: Path) -> None:
    frozen_path, labels_path, tasks_path, config_path, manifest_path, snapshot_path = _write_score_inputs(tmp_path)
    tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    tasks["tasks"][0]["high_risk"] = True
    tasks_path.write_text(json.dumps(tasks), encoding="utf-8")
    # Keep provenance valid while making the high-risk score unassessable.
    from tools.school_capability_baseline import _canonical_digest
    run = json.loads(frozen_path.read_text(encoding="utf-8"))
    run["task_catalog_version"] = f"tasks-v1@sha256:{_canonical_digest(tasks)}"
    from engine.evaluation.freeze import compute_freeze_hash
    unsigned = dict(run)
    unsigned.pop("freeze_hash")
    run["freeze_hash"] = compute_freeze_hash(unsigned)
    frozen_path.write_text(json.dumps(run), encoding="utf-8")
    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    labels["labels"][0]["quantifiable"] = False
    labels["freeze_hash"] = run["freeze_hash"]
    labels_path.write_text(json.dumps(labels), encoding="utf-8")

    output = tmp_path / "scores.json"
    result = _run("score", "--frozen-run", str(frozen_path), "--manifest", str(manifest_path), "--labels", str(labels_path), "--tasks", str(tasks_path), "--rule-snapshot", str(snapshot_path), "--evaluation-config", str(config_path), "--out", str(output))

    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    summary = payload["gate_input_summary"]
    assert summary["high_risk_assessable_count"] == 0
    assert summary["high_risk_unassessable_count"] == 1
    assert summary["high_risk_unassessable_task_ids"] == ["marriage.divorce_or_remarriage"]
    assert payload["computed_gate_evidence"]["high_risk_safe"] is False


def test_manifest_route_missing_eligible_case_lowers_only_that_identity_coverage(tmp_path: Path) -> None:
    frozen_path, labels_path, tasks_path, config_path, manifest_path, snapshot_path = _write_score_inputs(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    second = dict(manifest["records"][0])
    second["case_id"] = "C-TEST-002"
    second["eligible_routes"] = [_route("C-TEST-002")]
    manifest["records"].append(second)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    output = tmp_path / "scores.json"
    result = _run("score", "--frozen-run", str(frozen_path), "--manifest", str(manifest_path), "--labels", str(labels_path), "--tasks", str(tasks_path), "--rule-snapshot", str(snapshot_path), "--evaluation-config", str(config_path), "--out", str(output))

    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    identity = "ziping|marriage.divorce_or_remarriage|strong_day_master|event|lifetime|complete"
    assert payload["gate_input_summary"]["coverage_by_identity"][identity] == 0.5
    assert payload["computed_gate_evidence"]["coverage_complete"] is False
