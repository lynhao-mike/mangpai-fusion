import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from engine.evaluation.freeze import freeze_outputs
from engine.evaluation.models import BlindSchoolOutput
from tools.school_capability_dataset import (
    append_witness_event,
    bind_labels_after_freeze,
    build_evaluation_config,
    build_inventory,
    build_reviewed_manifest,
    build_unbound_labels,
    prepare_blind_bundle,
    register_prospective_intake,
    validate_dataset,
    verify_witness_registry,
)


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


def _inventory_record(case_id: str, classification: str = "historical_blind") -> dict:
    return {
        "case_id": case_id, "birth_info_complete": True, "feedback_present": True,
        "feedback_grade": "A", "development_contaminated": classification == "development_only",
        "contamination_evidence": [], "classification": classification, "notes": "",
        "reviewed_by": "human-a", "reviewed_at": "2026-07-12T00:00:00Z",
        "provenance_evidence": ["cases/raw_feedback/source/sample.md:1"],
    }


def _route() -> dict:
    return {
        "school_id": "ziping", "task_id": "career.role_change",
        "chart_prototype_id": "balanced", "claim_type": "binary_event",
        "time_horizon": "ten_year", "evidence_completeness_band": "complete",
    }


def test_build_reviewed_manifest_has_exact_score_schema_and_empty_development_routes() -> None:
    inventory = {"schema_version": "school-capability-case-inventory/v1", "records": [
        _inventory_record("C-CLEAN-001"), _inventory_record("C-DEV-001", "development_only"),
    ]}

    manifest = build_reviewed_manifest(inventory, "human-a", ["ziping"], {"C-CLEAN-001": [_route()]})

    assert set(manifest) == {"schema_version", "generated_at", "reviewed_by", "expected_schools", "records"}
    assert set(manifest["records"][0]) == {
        "case_id", "has_input", "has_feedback", "has_statement_index", "has_existing_report",
        "feedback_quantifiable", "contamination_flags", "eligibility", "evidence_notes", "eligible_routes",
    }
    assert manifest["records"][0]["eligibility"] == "historical_blind_candidate"
    assert manifest["records"][1]["eligible_routes"] == []


def test_automated_reviewer_cannot_build_promoted_manifest() -> None:
    inventory = {"schema_version": "school-capability-case-inventory/v1", "records": [_inventory_record("C-CLEAN-001")]}
    with pytest.raises(ValueError, match="automated reviewer"):
        build_reviewed_manifest(inventory, "automated-bot", ["ziping"], {"C-CLEAN-001": [_route()]})


def test_build_evaluation_config_exactly_covers_manifest_routes_and_outputs() -> None:
    manifest = build_reviewed_manifest(
        {"schema_version": "school-capability-case-inventory/v1", "records": [_inventory_record("C-CLEAN-001")]},
        "human-a", ["ziping"], {"C-CLEAN-001": [_route()]},
    )
    config = build_evaluation_config(manifest, {"career.role_change": 0.25}, "A", "2026-07-12T00:00:00Z")

    assert config["gate_thresholds"] == {
        "coverage_complete": 1.0,
        "calibration_min_samples": 5,
        "calibration_max_error": 0.2,
        "high_risk_min_utility": 0.0,
    }
    assert config["eligible_case_tasks"] == [["C-CLEAN-001", "career.role_change"]]
    key = "C-CLEAN-001|career.role_change|ziping"
    assert config["case_metadata"][key] == {
        "chart_prototype_id": "balanced", "time_horizon": "ten_year",
        "evidence_completeness_band": "complete",
    }
    assert config["score_weights"][key] == 1
    assert set(config) == {"schema_version", "eligible_case_tasks", "baseline_prevalence_by_task", "case_metadata", "evidence_grade", "evaluated_at", "score_weights", "gate_thresholds"}


def test_bind_labels_after_freeze_requires_verified_hash() -> None:
    unbound = build_unbound_labels([_observation()], _catalog())
    frozen = _frozen_outputs(["C-CLEAN-001"])

    bound = bind_labels_after_freeze(unbound, frozen)

    assert bound == {"schema_version": "school-capability-labels/v1", "freeze_hash": frozen["freeze_hash"], "labels": unbound["labels"]}
    with pytest.raises(ValueError, match="freeze hash mismatch"):
        bind_labels_after_freeze(unbound, {**frozen, "freeze_hash": "a" * 64})


def test_witness_trust_boundary_is_explicitly_documented() -> None:
    documentation = Path("tools/README.md").read_text(encoding="utf-8")

    assert "受信独立见证边界" in documentation
    assert "密钥泄漏" in documentation
    assert "恶意见证" in documentation
    assert "本地完整性模型" in documentation
    assert "registry root" in documentation
    assert "外部备份" in documentation
    assert "无限防恶意管理员" in documentation


def test_validate_dataset_never_goes_without_external_witness_and_bundle_root() -> None:
    case_ids = [f"C-{index:03d}" for index in range(30)]
    manifest = _manifest_for(case_ids, prospective=True)
    labels = [_observation(case_id=case_id) for case_id in case_ids]
    intake, bundle = _intake_and_bundle(case_ids)
    frozen = _frozen_outputs(
        case_ids,
        task_catalog_version=bundle["files"]["tasks.json"],
        rule_snapshot_id=bundle["files"]["rule-snapshot.json"],
    )
    bound = {"schema_version": "school-capability-labels/v1", "freeze_hash": frozen["freeze_hash"], "labels": labels}
    provenance = _reveal_provenance(bound, frozen)

    result = validate_dataset(manifest, bound, frozen, intake, bundle, provenance)
    assert result["status"] == "HOLD"
    assert any("witness" in reason for reason in result["reasons"])
    assert any("bundle root" in reason for reason in result["reasons"])
    assert validate_dataset(manifest, {**bound, "labels": labels[:29]}, frozen, intake, bundle, _reveal_provenance({**bound, "labels": labels[:29]}, frozen))["status"] == "HOLD"
    with pytest.raises(ValueError, match="freeze hash"):
        validate_dataset(manifest, {**bound, "freeze_hash": "c" * 64}, frozen, intake, bundle, provenance)


def _prospective_input(root: Path, case_id: str, text: str = "四柱：甲子 乙丑 丙寅 丁卯\n性别：乾\n") -> Path:
    path = root / case_id / "input.md"
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_register_prospective_intake_accepts_sectioned_raw_chart_format(tmp_path: Path) -> None:
    raw = """$BASE
Sex:乾造
Solar:1999-01-12 05:15
Start:出生后7年9月18日12时起运

$FOUR
Y:偏财,戊,寅,比肩 食神 偏财
M:劫财,乙,丑,正财 正印 正官
D:元男,甲,子,正印
H:伤官,丁,卯,劫财

$DY_LOOP
#2006,8岁,丙寅,食神
> 2006,丙戌,食神
"""
    input_path = _prospective_input(tmp_path, "P-2026-001-乾-戊寅乙丑甲子丁卯", raw)

    intake = register_prospective_intake(
        [input_path], _catalog(), ["ziping", "ren"], "human-reviewer-01",
    )
    tasks_path = tmp_path / "tasks.json"
    tasks_path.write_text(json.dumps(_catalog(), ensure_ascii=False), encoding="utf-8")
    snapshot = tmp_path / "rules.json"
    snapshot.write_text('{"rule_snapshot_id":"rules-v1"}', encoding="utf-8")
    prepare_blind_bundle(intake, tasks_path, snapshot, tmp_path / "bundle")
    chart = json.loads((tmp_path / "bundle" / "cases" / input_path.parent.name / "chart.json").read_text(encoding="utf-8"))

    assert len(intake["records"]) == 1
    assert len(intake["records"][0]["subject_id_hash"]) == 64
    assert chart["solar_datetime"] == "1999-01-12 05:15"
    assert chart["start_luck"] == "出生后7年9月18日12时起运"
    assert chart["dayun_steps"] == [{"ganzhi": "丙寅", "start_year": 2006}]
    assert chart["liunian_steps"] == [{"year": 2006, "ganzhi": "丙戌", "dayun": "丙寅"}]


def test_register_prospective_intake_rejects_known_facts_and_duplicate_cases(tmp_path: Path) -> None:
    leaked = _prospective_input(tmp_path, "C-P-001", "四柱：甲子 乙丑 丙寅 丁卯\nknown facts: 已婚\n")
    with pytest.raises(ValueError, match="known facts"):
        register_prospective_intake([leaked], _catalog(), ["ziping"], "human-a")

    first = _prospective_input(tmp_path / "one", "C-P-002")
    duplicate = _prospective_input(tmp_path / "two", "C-P-002")
    with pytest.raises(ValueError, match="duplicate case"):
        register_prospective_intake([first, duplicate], _catalog(), ["ziping"], "human-a")


def test_register_prospective_intake_rejects_unknown_task(tmp_path: Path) -> None:
    input_path = _prospective_input(tmp_path, "C-P-001")
    with pytest.raises(ValueError, match="unknown task"):
        register_prospective_intake(
            [input_path], _catalog(), ["ziping"], "human-a",
            tasks_by_case={"C-P-001": ["missing.task"]},
        )


def test_prepare_blind_bundle_whitelists_files_and_has_stable_hash(tmp_path: Path) -> None:
    input_path = _prospective_input(tmp_path / "source", "C-P-001")
    (input_path.parent / "feedback.md").write_text("诱饵：已婚且升职。\n", encoding="utf-8")
    tasks_path = tmp_path / "tasks.json"
    tasks_path.write_text(json.dumps(_catalog(), ensure_ascii=False), encoding="utf-8")
    snapshot = tmp_path / "rules.json"
    snapshot.write_text('{"rule_snapshot_id":"rules-v1","snapshot":"v1"}\n', encoding="utf-8")
    intake = register_prospective_intake([input_path], _catalog(), ["ziping"], "human-a")

    first = prepare_blind_bundle(intake, tasks_path, snapshot, tmp_path / "bundle-one")
    second = prepare_blind_bundle(intake, tasks_path, snapshot, tmp_path / "bundle-two")

    assert first["bundle_sha256"] == second["bundle_sha256"]
    assert (tmp_path / "bundle-one" / "cases" / "C-P-001" / "chart.json").exists()
    assert not (tmp_path / "bundle-one" / "cases" / "C-P-001" / "input.md").exists()
    assert not (tmp_path / "bundle-one" / "cases" / "C-P-001" / "feedback.md").exists()
    assert {path.relative_to(tmp_path / "bundle-one").as_posix() for path in (tmp_path / "bundle-one").rglob("*") if path.is_file()} == {
        "bundle-manifest.json", "cases/C-P-001/chart.json", "intake.json", "rule-snapshot.json", "tasks.json",
    }


def test_prepare_blind_bundle_rejects_existing_target_and_symlink_source(tmp_path: Path) -> None:
    input_path = _prospective_input(tmp_path / "source", "C-P-001")
    tasks_path = tmp_path / "tasks.json"
    tasks_path.write_text(json.dumps(_catalog()), encoding="utf-8")
    snapshot = tmp_path / "rules.json"
    snapshot.write_text('{"rule_snapshot_id":"rules-v1"}', encoding="utf-8")
    intake = register_prospective_intake([input_path], _catalog(), ["ziping"], "human-a")
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(ValueError, match="must not exist"):
        prepare_blind_bundle(intake, tasks_path, snapshot, existing)

    linked = tmp_path / "linked-rules.json"
    try:
        linked.symlink_to(snapshot)
    except OSError:
        pytest.skip("symlink creation is unavailable")
    with pytest.raises(ValueError, match="symlink"):
        prepare_blind_bundle(intake, tasks_path, linked, tmp_path / "bundle")


def test_prepare_blind_bundle_dry_run_writes_nothing(tmp_path: Path) -> None:
    input_path = _prospective_input(tmp_path / "source", "C-P-001")
    tasks_path = tmp_path / "tasks.json"
    tasks_path.write_text(json.dumps(_catalog()), encoding="utf-8")
    snapshot = tmp_path / "rules.json"
    snapshot.write_text('{"rule_snapshot_id":"rules-v1"}', encoding="utf-8")
    intake = register_prospective_intake([input_path], _catalog(), ["ziping"], "human-a")
    target = tmp_path / "bundle"

    result = prepare_blind_bundle(intake, tasks_path, snapshot, target, dry_run=True)

    assert len(result["bundle_sha256"]) == 64
    assert not target.exists()


def test_prepare_blind_bundle_persists_only_safe_case_task_assignments(tmp_path: Path) -> None:
    input_path = _prospective_input(tmp_path / "source", "C-P-001")
    tasks = _catalog()
    tasks_path = tmp_path / "tasks.json"
    tasks_path.write_text(json.dumps(tasks), encoding="utf-8")
    snapshot = tmp_path / "rules.json"
    snapshot.write_text('{"rule_snapshot_id":"rules-v1"}', encoding="utf-8")
    intake = register_prospective_intake(
        [input_path], tasks, ["ziping"], "human-a",
        tasks_by_case={"C-P-001": ["career.role_change"]},
    )
    bundle_root = tmp_path / "bundle"

    manifest = prepare_blind_bundle(intake, tasks_path, snapshot, bundle_root)

    assignments = json.loads((bundle_root / "intake.json").read_text(encoding="utf-8"))
    assert assignments == {
        "schema_version": "school-capability-blind-intake/v1",
        "schools": ["ziping"],
        "records": [{"case_id": "C-P-001", "task_ids": ["career.role_change"]}],
    }
    assert manifest["files"]["intake.json"] == hashlib.sha256(
        (bundle_root / "intake.json").read_bytes()
    ).hexdigest()
    assert "input_file" not in json.dumps(assignments)
    assert "subject_id_hash" not in json.dumps(assignments)


def test_manifest_cli_rejects_symlink_output(tmp_path: Path) -> None:
    inventory = tmp_path / "inventory.json"
    inventory.write_text(json.dumps({"schema_version": "school-capability-case-inventory/v1", "records": []}), encoding="utf-8")
    real = tmp_path / "real.json"
    real.write_text("untouched", encoding="utf-8")
    link = tmp_path / "manifest.json"
    try:
        link.symlink_to(real)
    except OSError:
        pytest.skip("symlink creation is unavailable")
    result = subprocess.run([
        sys.executable, "-m", "tools.school_capability_dataset", "manifest", "--inventory", str(inventory),
        "--reviewed-by", "human-a", "--expected-school", "ziping", "--out", str(link),
    ], check=False, capture_output=True, text=True)
    assert result.returncode == 1
    assert "symlink" in result.stderr
    assert real.read_text(encoding="utf-8") == "untouched"

def _frozen_outputs(
    case_ids: list[str], *, school_id: str = "ziping",
    task_catalog_version: str = "tasks-v1", rule_snapshot_id: str = "rules-v1",
    frozen_at: str = "2026-07-12T00:00:00Z",
) -> dict:
    return freeze_outputs([
        BlindSchoolOutput(case_id, school_id, "career.role_change", "abstain", "fixture")
        for case_id in case_ids
    ], task_catalog_version, rule_snapshot_id, frozen_at=frozen_at).to_dict()



def _manifest_for(case_ids: list[str], *, prospective: bool = False) -> dict:
    return {
        "schema_version": "school-capability-case-manifest/v1",
        "generated_at": "2026-07-12T00:00:00Z",
        "reviewed_by": "human-a",
        "expected_schools": ["ziping"],
        "records": [{
            "case_id": case_id, "has_input": True, "has_feedback": not prospective,
            "has_statement_index": False, "has_existing_report": False,
            "feedback_quantifiable": not prospective, "contamination_flags": [],
            "eligibility": "blind_candidate" if prospective else "historical_blind_candidate", "evidence_notes": [],
            "eligible_routes": [_route()],
        } for case_id in case_ids],
    }


def _canonical_sha(value: object) -> str:
    content = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(content).hexdigest()



def _intake_and_bundle(case_ids: list[str]) -> tuple[dict, dict]:
    tasks_sha = "1" * 64
    rules_sha = "2" * 64
    records = [{
        "case_id": case_id, "input_file": f"C:/{case_id}/input.md",
        "input_sha256": hashlib.sha256(case_id.encode()).hexdigest(),
        "subject_id_hash": hashlib.sha256(("subject:" + case_id).encode()).hexdigest(),
        "task_ids": ["career.role_change"],
    } for case_id in case_ids]
    intake = {
        "schema_version": "school-capability-prospective-intake/v1",
        "generated_at": "2026-07-11T00:00:00Z", "operator": "human-a", "schools": ["ziping"],
        "task_catalog_sha256": tasks_sha, "records": records,
    }
    files = {"tasks.json": tasks_sha, "rule-snapshot.json": rules_sha}
    files.update({f"cases/{row['case_id']}/chart.json": hashlib.sha256(("chart:" + row["case_id"]).encode()).hexdigest() for row in records})
    bundle = {
        "schema_version": "school-capability-blind-bundle/v1",
        "bundle_sha256": _canonical_sha(files), "files": files,
    }
    return intake, bundle



def _reveal_provenance(labels: dict, frozen: dict, *, bound_at: str = "2026-07-12T00:00:01Z") -> dict:
    unbound = {"schema_version": "school-capability-labels-unbound/v1", "labels": labels["labels"]}
    return {
        "freeze_hash": frozen["freeze_hash"], "bound_at": bound_at,
        "unbound_labels_sha256": _canonical_sha(unbound),
    }



def test_bind_and_validate_reject_tampered_or_incomplete_frozen_outputs() -> None:
    case_ids = [f"C-{index:03d}" for index in range(30)]
    manifest = _manifest_for(case_ids)
    frozen = _frozen_outputs(case_ids)
    labels = {"schema_version": "school-capability-labels/v1", "freeze_hash": frozen["freeze_hash"], "labels": [
        _observation(case_id=case_id) for case_id in case_ids
    ]}
    tampered = json.loads(json.dumps(frozen))
    tampered["outputs"][0]["rationale"] = "tampered"

    with pytest.raises(ValueError, match="freeze hash mismatch"):
        bind_labels_after_freeze({"schema_version": "school-capability-labels-unbound/v1", "labels": labels["labels"]}, tampered)
    with pytest.raises(ValueError, match="freeze hash mismatch"):
        validate_dataset(manifest, labels, tampered)

    incomplete = _frozen_outputs(case_ids[:-1])
    incomplete_labels = {**labels, "freeze_hash": incomplete["freeze_hash"]}
    with pytest.raises(ValueError, match="exactly cover manifest routes"):
        validate_dataset(manifest, incomplete_labels, incomplete)


def test_validate_rejects_invalid_duplicate_or_wrong_route_labels() -> None:
    manifest = _manifest_for(["C-001"])
    frozen = _frozen_outputs(["C-001"])
    valid = _observation(case_id="C-001")
    base = {"schema_version": "school-capability-labels/v1", "freeze_hash": frozen["freeze_hash"]}

    with pytest.raises(ValueError, match="label record has invalid schema"):
        validate_dataset(manifest, {**base, "labels": [{**valid, "extra": True}]}, frozen)
    with pytest.raises(ValueError, match="duplicate label identity"):
        validate_dataset(manifest, {**base, "labels": [valid, valid]}, frozen)
    with pytest.raises(ValueError, match="eligible manifest route"):
        validate_dataset(manifest, {**base, "labels": [{**valid, "task_id": "other.task"}]}, frozen)


def test_manifest_validation_is_strict_about_types_uniqueness_eligibility_and_routes() -> None:
    manifest = _manifest_for(["C-001"])
    for mutate, message in [
        (lambda value: value["records"][0].update(has_input="yes"), "manifest record value types"),
        (lambda value: value["records"][0].update(eligibility="eligible"), "eligibility"),
        (lambda value: value["records"].append(dict(value["records"][0])), "unique case_id"),
        (lambda value: value["records"][0]["eligible_routes"].append(dict(_route())), "unique"),
    ]:
        changed = json.loads(json.dumps(manifest))
        mutate(changed)
        with pytest.raises(ValueError, match=message):
            build_evaluation_config(changed, {"career.role_change": 0.2}, "A", "2026-07-12T00:00:00Z")


def test_config_requires_strict_grade_utc_route_school_and_no_duplicate_grid() -> None:
    manifest = _manifest_for(["C-001"])
    with pytest.raises(ValueError, match="evidence_grade"):
        build_evaluation_config(manifest, {"career.role_change": 0.2}, "excellent", "2026-07-12T00:00:00Z")
    with pytest.raises(ValueError, match="UTC"):
        build_evaluation_config(manifest, {"career.role_change": 0.2}, "A", "2026-07-12")
    wrong_school = json.loads(json.dumps(manifest))
    wrong_school["records"][0]["eligible_routes"][0]["school_id"] = "unknown"
    with pytest.raises(ValueError, match="expected_schools"):
        build_evaluation_config(wrong_school, {"career.role_change": 0.2}, "A", "2026-07-12T00:00:00Z")


def test_prepare_blind_rejects_path_traversal_and_recursive_string_leaks(tmp_path: Path) -> None:
    input_path = _prospective_input(tmp_path / "source", "C-P-001")
    tasks_path = tmp_path / "tasks.json"
    snapshot = tmp_path / "rules.json"
    clean_snapshot = tmp_path / "clean-rules.json"
    tasks = _catalog()
    tasks_path.write_text(json.dumps(tasks), encoding="utf-8")
    clean_snapshot.write_text('{"rule_snapshot_id":"rules-v1"}', encoding="utf-8")
    snapshot.write_text(json.dumps({"rule_snapshot_id": "rules-v1", "nested": [{"text": "known facts: married"}]}), encoding="utf-8")
    intake = register_prospective_intake([input_path], tasks, ["ziping"], "human-a")
    traversing = json.loads(json.dumps(intake))
    traversing["records"][0]["case_id"] = "../../escape"
    with pytest.raises(ValueError, match="case_id"):
        prepare_blind_bundle(traversing, tasks_path, clean_snapshot, tmp_path / "bundle")

    prepared = prepare_blind_bundle(intake, tasks_path, snapshot, tmp_path / "bundle-two")
    assert len(prepared["files"]["rule-snapshot.json"]) == 64
    assert "known facts" not in (tmp_path / "bundle-two" / "rule-snapshot.json").read_text(encoding="utf-8")


def test_task_catalog_recursive_strings_cannot_leak_outcomes(tmp_path: Path) -> None:
    input_path = _prospective_input(tmp_path, "C-P-001")
    catalog = _catalog()
    catalog["tasks"][0]["evaluation_note"] = "Uses feedback from known facts"
    with pytest.raises(ValueError, match="forbidden"):
        register_prospective_intake([input_path], catalog, ["ziping"], "human-a")


def test_task_catalog_allows_label_schema_metadata_without_treating_it_as_revealed_labels(tmp_path: Path) -> None:
    input_path = _prospective_input(tmp_path, "C-P-001")
    catalog = _catalog()
    catalog["tasks"][0]["label_schema"] = {
        "type": "boolean",
        "positive_label": "occurred",
        "negative_label": "not_observed",
    }

    intake = register_prospective_intake([input_path], catalog, ["ziping"], "human-a")

    assert intake["records"][0]["task_ids"] == ["career.role_change"]


def test_build_reviewed_manifest_rejects_forged_clean_inventory() -> None:
    forged = _inventory_record("C-CLEAN-001")
    forged.update(reviewed_by="", reviewed_at="", provenance_evidence=[])
    inventory = {"schema_version": "school-capability-case-inventory/v1", "records": [forged]}
    with pytest.raises(ValueError, match="human review provenance"):
        build_reviewed_manifest(inventory, "human-a", ["ziping"], {"C-CLEAN-001": [_route()]})

    forged.update(reviewed_by="human-a", reviewed_at="2026-07-12T00:00:00Z", provenance_evidence=["source.md:1"], contamination_evidence=["human_clean_review_missing"])
    with pytest.raises(ValueError, match="human_clean_review_missing"):
        build_reviewed_manifest(inventory, "human-a", ["ziping"], {"C-CLEAN-001": [_route()]})



def test_validate_rejects_forged_go_without_bound_provenance_or_bundle_chain() -> None:
    case_ids = [f"C-{index:03d}" for index in range(30)]
    manifest = _manifest_for(case_ids, prospective=True)
    intake, bundle = _intake_and_bundle(case_ids)
    frozen = _frozen_outputs(case_ids, task_catalog_version="1" * 64, rule_snapshot_id="2" * 64)
    labels = {"schema_version": "school-capability-labels/v1", "freeze_hash": frozen["freeze_hash"], "labels": [_observation(case_id=case_id) for case_id in case_ids]}
    provenance = _reveal_provenance(labels, frozen)

    assert validate_dataset(manifest, labels, frozen)["status"] == "HOLD"
    with pytest.raises(ValueError, match="bound_at"):
        validate_dataset(manifest, labels, frozen, intake, bundle, {**provenance, "bound_at": "2026-07-11T23:59:59Z"})
    with pytest.raises(ValueError, match="unbound labels hash"):
        validate_dataset(manifest, labels, frozen, intake, bundle, {**provenance, "unbound_labels_sha256": "a" * 64})

    changed = json.loads(json.dumps(bundle))
    changed["files"]["cases/C-000/chart.json"] = "f" * 64
    changed["bundle_sha256"] = _canonical_sha(changed["files"])
    changed_root = validate_dataset(manifest, labels, frozen, intake, changed, provenance)
    assert changed_root["status"] == "HOLD"
    assert any("bundle root" in reason for reason in changed_root["reasons"])
    changed = json.loads(json.dumps(bundle))
    changed["bundle_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="bundle hash"):
        validate_dataset(manifest, labels, frozen, intake, changed, provenance)



def test_validate_requires_exact_intake_cases_and_frozen_bundle_hashes() -> None:
    case_ids = [f"C-{index:03d}" for index in range(30)]
    manifest = _manifest_for(case_ids, prospective=True)
    intake, bundle = _intake_and_bundle(case_ids)
    frozen = _frozen_outputs(case_ids, task_catalog_version="1" * 64, rule_snapshot_id="2" * 64)
    labels = {"schema_version": "school-capability-labels/v1", "freeze_hash": frozen["freeze_hash"], "labels": [_observation(case_id=case_id) for case_id in case_ids]}
    provenance = _reveal_provenance(labels, frozen)

    extra = json.loads(json.dumps(intake))
    extra["records"].append({
        **extra["records"][0], "case_id": "C-EXTRA", "subject_id_hash": "e" * 64,
    })
    with pytest.raises(ValueError, match="eligible cases.*intake"):
        validate_dataset(manifest, labels, frozen, extra, bundle, provenance)
    wrong_tasks = _frozen_outputs(case_ids, task_catalog_version="3" * 64, rule_snapshot_id="2" * 64)
    with pytest.raises(ValueError, match="task catalog hash"):
        validate_dataset(manifest, {**labels, "freeze_hash": wrong_tasks["freeze_hash"]}, wrong_tasks, intake, bundle, _reveal_provenance({**labels, "freeze_hash": wrong_tasks["freeze_hash"]}, wrong_tasks))



def test_manifest_candidate_invariants_and_unknown_routes_are_rejected() -> None:
    inventory = {"schema_version": "school-capability-case-inventory/v1", "records": [_inventory_record("C-P-001", "prospective")]}
    inventory["records"][0].update(feedback_present=False, feedback_grade="unreviewed")
    with pytest.raises(ValueError, match="unknown case"):
        build_reviewed_manifest(inventory, "human-a", ["ziping"], {"C-UNKNOWN": [_route()]})

    manifest = build_reviewed_manifest(inventory, "human-a", ["ziping"], {"C-P-001": [_route()]})
    assert manifest["records"][0]["eligibility"] == "blind_candidate"
    bad = json.loads(json.dumps(manifest))
    bad["records"][0]["has_feedback"] = True
    with pytest.raises(ValueError, match="prospective candidate"):
        build_evaluation_config(bad, {"career.role_change": 0.2}, "A", "2026-07-12T00:00:00Z", _catalog())



def test_routes_are_unique_by_case_task_school_and_match_task_catalog() -> None:
    inventory = {"schema_version": "school-capability-case-inventory/v1", "records": [_inventory_record("C-001")]}
    duplicate = {**_route(), "chart_prototype_id": "different"}
    with pytest.raises(ValueError, match="case/task/school"):
        build_reviewed_manifest(inventory, "human-a", ["ziping"], {"C-001": [_route(), duplicate]})

    manifest = build_reviewed_manifest(inventory, "human-a", ["ziping"], {"C-001": [_route()]})
    wrong_claim = json.loads(json.dumps(manifest))
    wrong_claim["records"][0]["eligible_routes"][0]["claim_type"] = "wrong"
    with pytest.raises(ValueError, match="task catalog"):
        build_evaluation_config(wrong_claim, {"career.role_change": 0.2}, "A", "2026-07-12T00:00:00Z", _catalog())



def test_config_rejects_boolean_baseline_and_manifest_generated_at_must_be_utc() -> None:
    manifest = _manifest_for(["C-001"])
    with pytest.raises(ValueError, match="baseline prevalence"):
        build_evaluation_config(manifest, {"career.role_change": True}, "A", "2026-07-12T00:00:00Z", _catalog())
    manifest["generated_at"] = "2026-07-12"
    with pytest.raises(ValueError, match="generated_at.*UTC"):
        build_evaluation_config(manifest, {"career.role_change": 0.2}, "A", "2026-07-12T00:00:00Z", _catalog())



def _witness_event(event_type: str, occurred_at: str, **payload: str) -> dict:
    return {"event_type": event_type, "occurred_at": occurred_at, "payload": payload}


def test_witness_event_payload_uses_exact_schema_per_event_type() -> None:
    key = b"external-secret"
    registered = _witness_event(
        "registered", "2026-07-11T00:00:00Z", case_id="C-P-001",
        input_sha256="b" * 64, subject_id_hash="a" * 64,
    )
    assert verify_witness_registry(append_witness_event(None, registered, key), key) is True

    for malformed in (
        {**registered, "payload": {**registered["payload"], "extra": "forbidden"}},
        _witness_event("registered", "2026-07-11T00:00:00Z", case_id="C-P-001"),
        _witness_event("prepared", "2026-07-11T00:00:01Z", case_id="C-P-001", bundle_sha256="e" * 64, freeze_hash="f" * 64),
    ):
        with pytest.raises(ValueError, match="schema"):
            append_witness_event(None, malformed, key)


def test_witness_registry_detects_forged_hmac_broken_chain_and_bad_order() -> None:
    key = b"external-secret"
    registry = append_witness_event(None, _witness_event(
        "registered", "2026-07-11T00:00:00Z", case_id="C-P-001",
        input_sha256="b" * 64, subject_id_hash="a" * 64,
    ), key)
    registry = append_witness_event(registry, _witness_event(
        "prepared", "2026-07-11T00:00:01Z", case_id="C-P-001", bundle_sha256="e" * 64,
    ), key)
    registry = append_witness_event(registry, _witness_event(
        "freeze", "2026-07-12T00:00:00Z", case_id="C-P-001", freeze_hash="f" * 64,
    ), key)
    registry = append_witness_event(registry, _witness_event(
        "reveal", "2026-07-12T00:00:01Z", case_id="C-P-001",
        freeze_hash="f" * 64, unbound_labels_sha256="1" * 64,
    ), key)

    assert verify_witness_registry(registry, key) is True
    forged = json.loads(json.dumps(registry))
    forged["events"][0]["payload"]["case_id"] = "C-FORGED"
    with pytest.raises(ValueError, match="HMAC"):
        verify_witness_registry(forged, key)
    broken = json.loads(json.dumps(registry))
    broken["events"][1]["previous_hash"] = "f" * 64
    with pytest.raises(ValueError, match="chain"):
        verify_witness_registry(broken, key)


def test_prospective_intake_rejects_duplicate_subject_and_bundle_contains_only_canonical_data(tmp_path: Path) -> None:
    first = _prospective_input(tmp_path / "one", "C-P-001", "四柱：甲子 乙丑 丙寅 丁卯\n性别：乾\n职业：医生\n")
    second = _prospective_input(tmp_path / "two", "C-P-002", "四柱：甲子 乙丑 丙寅 丁卯\n性别：乾\n职业：律师\n")
    with pytest.raises(ValueError, match="duplicate subject"):
        register_prospective_intake([first, second], _catalog(), ["ziping"], "human-a")

    intake = register_prospective_intake([first], _catalog(), ["ziping"], "human-a")
    assert len(intake["records"][0]["subject_id_hash"]) == 64
    tasks_path = tmp_path / "tasks.json"
    tasks_path.write_text(json.dumps(_catalog(), ensure_ascii=False), encoding="utf-8")
    snapshot = tmp_path / "rules.json"
    snapshot.write_text(json.dumps({"rule_snapshot_id": "rules-v1", "rules": [{"answer": "命主会升职"}]}, ensure_ascii=False), encoding="utf-8")
    bundle_root = tmp_path / "bundle"

    manifest = prepare_blind_bundle(intake, tasks_path, snapshot, bundle_root)

    chart = json.loads((bundle_root / "cases" / "C-P-001" / "chart.json").read_text(encoding="utf-8"))
    assert chart == {"case_id": "C-P-001", "four_pillars": ["甲子", "乙丑", "丙寅", "丁卯"], "sex_marker": "乾"}
    assert not (bundle_root / "cases" / "C-P-001" / "input.md").exists()
    task_bundle = json.loads((bundle_root / "tasks.json").read_text(encoding="utf-8"))
    assert "evaluation_note" not in task_bundle["tasks"][0]
    assert intake["task_catalog_sha256"] == manifest["files"]["tasks.json"]
    rule_ref = json.loads((bundle_root / "rule-snapshot.json").read_text(encoding="utf-8"))
    assert rule_ref == {"rule_snapshot_id": "rules-v1", "sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest()}
    assert set(manifest["files"]) == {"tasks.json", "rule-snapshot.json", "intake.json", "cases/C-P-001/chart.json"}
    assert "医生" not in "".join(path.read_text(encoding="utf-8") for path in bundle_root.rglob("*.json"))


def _go_fixture(tmp_path: Path) -> tuple[dict, dict, dict, dict, dict, Path, dict, bytes]:
    input_path = _prospective_input(tmp_path / "source", "C-P-001")
    tasks = _catalog()
    tasks_path = tmp_path / "tasks.json"
    tasks_path.write_text(json.dumps(tasks), encoding="utf-8")
    snapshot = tmp_path / "rules.json"
    snapshot.write_text(json.dumps({"rule_snapshot_id": "rules-v1", "rules": []}), encoding="utf-8")
    intake = register_prospective_intake([input_path], tasks, ["ziping"], "human-a")
    bundle_root = tmp_path / "bundle"
    bundle = prepare_blind_bundle(intake, tasks_path, snapshot, bundle_root)
    frozen = _frozen_outputs(["C-P-001"], task_catalog_version=bundle["files"]["tasks.json"], rule_snapshot_id=bundle["files"]["rule-snapshot.json"])
    labels = {"schema_version": "school-capability-labels/v1", "freeze_hash": frozen["freeze_hash"], "labels": [_observation(case_id="C-P-001")]}
    provenance = _reveal_provenance(labels, frozen)
    manifest = _manifest_for(["C-P-001"], prospective=True)
    key = b"external-secret"
    case_id = "C-P-001"
    registry = append_witness_event(None, _witness_event(
        "registered", "2026-07-11T00:00:00Z", case_id=case_id,
        input_sha256=intake["records"][0]["input_sha256"],
        subject_id_hash=intake["records"][0]["subject_id_hash"],
    ), key)
    registry = append_witness_event(registry, _witness_event(
        "prepared", "2026-07-11T00:00:01Z", case_id=case_id,
        bundle_sha256=bundle["bundle_sha256"],
    ), key)
    registry = append_witness_event(registry, _witness_event(
        "freeze", frozen["frozen_at"], case_id=case_id, freeze_hash=frozen["freeze_hash"],
    ), key)
    registry = append_witness_event(registry, _witness_event(
        "reveal", provenance["bound_at"], case_id=case_id,
        freeze_hash=frozen["freeze_hash"], unbound_labels_sha256=provenance["unbound_labels_sha256"],
    ), key)
    return manifest, labels, frozen, intake, bundle, bundle_root, registry, key


def test_validate_go_requires_witness_key_registry_and_rehashes_bundle_root(tmp_path: Path) -> None:
    manifest, labels, frozen, intake, bundle, bundle_root, registry, key = _go_fixture(tmp_path)
    provenance = _reveal_provenance(labels, frozen)

    assert validate_dataset(manifest, labels, frozen, intake, bundle, provenance, bundle_root, registry, key)["status"] == "HOLD"
    assert "witness" in validate_dataset(manifest, labels, frozen, intake, bundle, provenance, bundle_root, None, None)["reasons"][0]
    (bundle_root / "cases" / "C-P-001" / "chart.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="actual bundle"):
        validate_dataset(manifest, labels, frozen, intake, bundle, provenance, bundle_root, registry, key)


@pytest.mark.parametrize("chart", [
    {"case_id": "C-FORGED", "four_pillars": ["甲子", "乙丑", "丙寅", "丁卯"], "sex_marker": "乾"},
    {"case_id": "C-P-001", "four_pillars": ["甲子", "乙丑", "丙寅", "甲丑"], "sex_marker": "乾"},
    {"case_id": "C-P-001", "four_pillars": ["甲子", "乙丑", "丙寅"], "sex_marker": "乾"},
    {"case_id": "C-P-001", "four_pillars": ["甲子", "乙丑", "丙寅", "丁卯"], "sex_marker": "男"},
])
def test_validate_go_rejects_forged_canonical_chart_even_with_rehashed_chain(tmp_path: Path, chart: dict) -> None:
    manifest, labels, frozen, intake, bundle, bundle_root, registry, key = _go_fixture(tmp_path)
    provenance = _reveal_provenance(labels, frozen)
    chart_path = bundle_root / "cases" / "C-P-001" / "chart.json"
    chart_path.write_text(json.dumps(chart, ensure_ascii=False), encoding="utf-8")
    bundle["files"]["cases/C-P-001/chart.json"] = hashlib.sha256(chart_path.read_bytes()).hexdigest()
    bundle["bundle_sha256"] = _canonical_sha(bundle["files"])
    (bundle_root / "bundle-manifest.json").write_text(json.dumps(bundle), encoding="utf-8")
    intake["records"][0]["subject_id_hash"] = _canonical_sha({
        "four_pillars": chart["four_pillars"], "sex_marker": chart["sex_marker"],
    })

    with pytest.raises(ValueError, match="canonical chart"):
        validate_dataset(manifest, labels, frozen, intake, bundle, provenance, bundle_root, registry, key)


def test_validly_resigned_replacement_remains_invalid_in_append_only_registry(tmp_path: Path) -> None:
    manifest, labels, frozen, intake, bundle, bundle_root, registry, key = _go_fixture(tmp_path)
    provenance = _reveal_provenance(labels, frozen)
    chart_path = bundle_root / "cases" / "C-P-001" / "chart.json"
    replacement = {
        "case_id": "C-P-001", "four_pillars": ["乙丑", "丙寅", "丁卯", "戊辰"],
        "sex_marker": "乾",
    }
    chart_path.write_text(json.dumps(replacement, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    replacement_subject = _canonical_sha({
        "four_pillars": replacement["four_pillars"], "sex_marker": replacement["sex_marker"],
    })
    intake["records"][0]["subject_id_hash"] = replacement_subject
    chart_sha = hashlib.sha256(chart_path.read_bytes()).hexdigest()
    bundle["files"]["cases/C-P-001/chart.json"] = chart_sha
    bundle["bundle_sha256"] = _canonical_sha(bundle["files"])
    (bundle_root / "bundle-manifest.json").write_text(json.dumps(bundle), encoding="utf-8")
    registry = append_witness_event(registry, _witness_event(
        "registered", "2026-07-12T00:00:02Z", case_id="C-P-001",
        input_sha256=intake["records"][0]["input_sha256"],
        subject_id_hash=replacement_subject,
    ), key)
    registry = append_witness_event(registry, _witness_event(
        "prepared", "2026-07-12T00:00:03Z", case_id="C-P-001",
        bundle_sha256=bundle["bundle_sha256"],
    ), key)

    with pytest.raises(ValueError, match="exactly one registered.*prepared.*freeze.*reveal"):
        validate_dataset(manifest, labels, frozen, intake, bundle, provenance, bundle_root, registry, key)


def test_validate_go_rejects_nested_bundle_manifest_as_extra_file(tmp_path: Path) -> None:
    manifest, labels, frozen, intake, bundle, bundle_root, registry, key = _go_fixture(tmp_path)
    provenance = _reveal_provenance(labels, frozen)
    nested = bundle_root / "cases" / "C-P-001" / "bundle-manifest.json"
    nested.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="actual bundle files"):
        validate_dataset(manifest, labels, frozen, intake, bundle, provenance, bundle_root, registry, key)


def test_validate_go_rejects_tampered_root_bundle_manifest(tmp_path: Path) -> None:
    manifest, labels, frozen, intake, bundle, bundle_root, registry, key = _go_fixture(tmp_path)
    provenance = _reveal_provenance(labels, frozen)
    (bundle_root / "bundle-manifest.json").write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="actual bundle manifest"):
        validate_dataset(manifest, labels, frozen, intake, bundle, provenance, bundle_root, registry, key)


def test_witness_append_cli_reads_secret_only_from_environment(tmp_path: Path) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(_witness_event(
        "registered", "2026-07-11T00:00:00Z", case_id="C-P-001",
        input_sha256="b" * 64, subject_id_hash="a" * 64,
    )), encoding="utf-8")
    registry_path = tmp_path / "registry.json"
    command = [
        sys.executable, "-m", "tools.school_capability_dataset", "witness-append",
        "--event", str(event_path), "--out", str(registry_path),
    ]

    missing = subprocess.run(command, check=False, capture_output=True, text=True, env={})
    assert missing.returncode != 0
    assert "environment" in missing.stderr
    environment = dict(__import__("os").environ)
    environment["SCHOOL_CAPABILITY_WITNESS_KEY"] = "external-secret"
    created = subprocess.run(command, check=False, capture_output=True, text=True, env=environment)

    assert created.returncode == 0, created.stderr
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert verify_witness_registry(registry, b"external-secret") is True
    assert "external-secret" not in registry_path.read_text(encoding="utf-8")


def test_prepare_blind_bundle_revalidates_intake_source_and_hash_chain(tmp_path: Path) -> None:
    input_path = _prospective_input(tmp_path / "source", "C-P-001")
    tasks = _catalog()
    tasks_path = tmp_path / "tasks.json"
    tasks_path.write_text(json.dumps(tasks), encoding="utf-8")
    snapshot = tmp_path / "rules.json"
    snapshot.write_text('{"rule_snapshot_id":"rules-v1"}', encoding="utf-8")
    intake = register_prospective_intake([input_path], tasks, ["ziping"], "human-a")

    renamed = input_path.with_name("chart.md")
    input_path.rename(renamed)
    intake["records"][0]["input_file"] = str(renamed)
    with pytest.raises(ValueError, match="input.md"):
        prepare_blind_bundle(intake, tasks_path, snapshot, tmp_path / "bundle-one")

    renamed.rename(input_path)
    intake["records"][0]["input_file"] = str(input_path)
    input_path.write_text("known facts: promoted", encoding="utf-8")
    intake["records"][0]["input_sha256"] = hashlib.sha256(input_path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="forbidden"):
        prepare_blind_bundle(intake, tasks_path, snapshot, tmp_path / "bundle-two")

    input_path.write_text("四柱：甲子 乙丑 丙寅 丁卯\n性别：乾\n", encoding="utf-8")
    intake["records"][0]["input_sha256"] = hashlib.sha256(input_path.read_bytes()).hexdigest()
    intake["task_catalog_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="task catalog hash"):
        prepare_blind_bundle(intake, tasks_path, snapshot, tmp_path / "bundle-three")
