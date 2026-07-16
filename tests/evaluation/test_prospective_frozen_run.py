from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from engine.evaluation.freeze import verify_frozen_run
from engine.evaluation.models import FrozenBlindRun
from tools.school_capability_dataset import (
    append_witness_event,
    prepare_blind_bundle,
    register_prospective_intake,
    verify_witness_registry,
)
from tools import school_capability_prospective as prospective
from tools.school_capability_prospective import build_staged_frozen_run


TASKS = Path("META/prospective-go-task-catalog-v1.json")
RULES = Path("META/prospective-go-rule-snapshot-v1.json")
SCHOOLS = ["ziping", "ditiansui", "duan", "ren", "gao", "yang"]


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _bundle(tmp_path: Path, *, task_ids: list[str] | None = None) -> tuple[Path, dict]:
    case_id = "P-GO-TEST-001-乾-甲子乙丑丙寅丁卯"
    input_path = tmp_path / "source" / case_id / "input.md"
    input_path.parent.mkdir(parents=True)
    input_path.write_text("四柱：甲子 乙丑 丙寅 丁卯\n性别：乾\n", encoding="utf-8")
    tasks = _read(TASKS)
    intake = register_prospective_intake(
        [input_path], tasks, SCHOOLS, "human-test",
        tasks_by_case={case_id: task_ids} if task_ids else None,
    )
    root = tmp_path / "bundle"
    manifest = prepare_blind_bundle(intake, TASKS, RULES, root)
    return root, manifest


def test_build_staged_run_uses_bundle_only_and_preserves_total_six_source_grid(tmp_path: Path) -> None:
    root, manifest = _bundle(tmp_path, task_ids=["career.role_change", "health.system_risk"])

    artifact = build_staged_frozen_run(root)

    assert artifact["schema_version"] == "school-capability-prospective-staged-run/v1"
    assert artifact["bundle_sha256"] == manifest["bundle_sha256"]
    assert artifact["task_catalog_sha256"] == manifest["files"]["tasks.json"]
    assert artifact["rule_snapshot_sha256"] == manifest["files"]["rule-snapshot.json"]
    assert artifact["case_task_assignments"] == [{
        "case_id": "P-GO-TEST-001-乾-甲子乙丑丙寅丁卯",
        "task_ids": ["career.role_change", "health.system_risk"],
    }]
    run = FrozenBlindRun.from_dict(artifact["frozen_run"])
    verify_frozen_run(run)
    assert run.task_catalog_version == (
        "prospective-go-tasks-v1@sha256:" + manifest["files"]["tasks.json"]
    )
    assert run.rule_snapshot_id == (
        "prospective-go-six-source-ten-task-rules-v1@sha256:" + manifest["files"]["rule-snapshot.json"]
    )
    assert len(run.outputs) == 12
    assert {output.school_id for output in run.outputs} == set(SCHOOLS)
    assert {output.task_id for output in run.outputs} == {"career.role_change", "health.system_risk"}
    assert {output.state for output in run.outputs} <= {"claim", "abstain", "unsupported"}
    assert artifact["artifact_sha256"] == hashlib.sha256(json.dumps(
        {key: value for key, value in artifact.items() if key != "artifact_sha256"},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    assert build_staged_frozen_run(root) == artifact


def test_build_staged_run_rejects_manifest_tampering_and_extra_files(tmp_path: Path) -> None:
    root, _ = _bundle(tmp_path)
    chart = next((root / "cases").glob("*/chart.json"))
    chart.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        build_staged_frozen_run(root)

    root, _ = _bundle(tmp_path / "extra")
    (root / "unexpected.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="files do not match manifest"):
        build_staged_frozen_run(root)


def test_cli_dry_run_writes_nothing_and_formal_run_refuses_overwrite(tmp_path: Path) -> None:
    root, _ = _bundle(tmp_path)
    output = tmp_path / "staged-run.json"
    command = [
        sys.executable, "-m", "tools.school_capability_prospective", "stage-frozen-run",
        "--bundle-root", str(root), "--out", str(output),
    ]

    dry = subprocess.run([*command, "--dry-run"], check=False, capture_output=True, text=True)
    assert dry.returncode == 0, dry.stderr
    assert not output.exists()
    assert json.loads(dry.stdout)["schema_version"] == "school-capability-prospective-staged-run/v1"

    first = subprocess.run(command, check=False, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    original = output.read_bytes()
    second = subprocess.run(command, check=False, capture_output=True, text=True)
    assert second.returncode != 0
    assert "already exists" in second.stderr
    assert output.read_bytes() == original


def _witness_fixture(tmp_path: Path) -> tuple[Path, Path, Path, dict, dict]:
    case_specs = {
        "P-GO-TEST-001-乾-甲子乙丑丙寅丁卯": "四柱：甲子 乙丑 丙寅 丁卯\n性别：乾\n",
        "P-GO-TEST-002-坤-戊辰己巳庚午辛未": "四柱：戊辰 己巳 庚午 辛未\n性别：坤\n",
    }
    inputs = []
    for case_id, content in case_specs.items():
        input_path = tmp_path / "source" / case_id / "input.md"
        input_path.parent.mkdir(parents=True)
        input_path.write_text(content, encoding="utf-8")
        inputs.append(input_path)
    intake = register_prospective_intake(inputs, _read(TASKS), SCHOOLS, "human-test")
    intake_path = tmp_path / "intake.json"
    intake_path.write_text(json.dumps(intake), encoding="utf-8")
    bundle_root = tmp_path / "bundle"
    manifest = prepare_blind_bundle(intake, TASKS, RULES, bundle_root)
    staged = build_staged_frozen_run(bundle_root)
    staged_path = tmp_path / "staged-run.json"
    staged_path.write_text(json.dumps(staged), encoding="utf-8")
    return intake_path, bundle_root, staged_path, intake, manifest


def test_build_witness_freeze_registry_generates_exact_per_case_chain(tmp_path: Path) -> None:
    intake_path, bundle_root, staged_path, intake, manifest = _witness_fixture(tmp_path)
    key = b"external-witness-secret"

    registry = prospective.build_witness_freeze_registry(
        intake_path, bundle_root, staged_path, key,
    )

    assert verify_witness_registry(registry, key) is True
    assert [event["event_type"] for event in registry["events"]] == [
        "registered", "prepared", "freeze", "registered", "prepared", "freeze",
    ]
    assert "reveal" not in {event["event_type"] for event in registry["events"]}
    intake_by_case = {row["case_id"]: row for row in intake["records"]}
    frozen = _read(staged_path)["frozen_run"]
    for case_id in sorted(intake_by_case):
        events = [event for event in registry["events"] if event["payload"]["case_id"] == case_id]
        assert [event["event_type"] for event in events] == ["registered", "prepared", "freeze"]
        assert events[0]["payload"] == {
            "case_id": case_id,
            "input_sha256": intake_by_case[case_id]["input_sha256"],
            "subject_id_hash": intake_by_case[case_id]["subject_id_hash"],
        }
        assert events[1]["payload"] == {"case_id": case_id, "bundle_sha256": manifest["bundle_sha256"]}
        assert events[2]["payload"] == {"case_id": case_id, "freeze_hash": frozen["freeze_hash"]}
        assert events[0]["occurred_at"] < events[1]["occurred_at"] < events[2]["occurred_at"]
        assert events[2]["occurred_at"] == frozen["frozen_at"]


def test_witness_freeze_registry_rejects_tamper_case_and_hash_mismatch(tmp_path: Path) -> None:
    intake_path, bundle_root, staged_path, _, _ = _witness_fixture(tmp_path)
    key = b"external-witness-secret"

    tampered = _read(staged_path)
    tampered["frozen_run"]["freeze_hash"] = "f" * 64
    staged_path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ValueError, match="frozen run|artifact hash"):
        prospective.build_witness_freeze_registry(intake_path, bundle_root, staged_path, key)

    staged_path.write_text(json.dumps(build_staged_frozen_run(bundle_root)), encoding="utf-8")
    mismatched = _read(intake_path)
    mismatched["records"] = mismatched["records"][:1]
    intake_path.write_text(json.dumps(mismatched), encoding="utf-8")
    with pytest.raises(ValueError, match="case set"):
        prospective.build_witness_freeze_registry(intake_path, bundle_root, staged_path, key)


def test_witness_freeze_registry_rejects_wrong_existing_order_and_cli_is_no_overwrite(tmp_path: Path) -> None:
    intake_path, bundle_root, staged_path, intake, manifest = _witness_fixture(tmp_path)
    key = b"external-witness-secret"
    case_id = intake["records"][0]["case_id"]
    wrong = append_witness_event(None, {
        "event_type": "prepared",
        "occurred_at": intake["generated_at"],
        "payload": {"case_id": case_id, "bundle_sha256": manifest["bundle_sha256"]},
    }, key)
    with pytest.raises(ValueError, match="order|existing witness"):
        prospective.build_witness_freeze_registry(
            intake_path, bundle_root, staged_path, key, registry=wrong,
        )

    output = tmp_path / "witness.json"
    command = [
        sys.executable, "-m", "tools.school_capability_prospective", "witness-freeze-chain",
        "--intake", str(intake_path), "--bundle-root", str(bundle_root),
        "--staged-run", str(staged_path), "--out", str(output),
    ]
    environment = {
        **os.environ,
        "PYTHONUTF8": "1",
        "SCHOOL_CAPABILITY_WITNESS_KEY": "external-witness-secret",
    }
    dry = subprocess.run([*command, "--dry-run"], check=False, capture_output=True, text=True, env=environment)
    assert dry.returncode == 0, dry.stderr
    assert not output.exists()
    assert verify_witness_registry(json.loads(dry.stdout), key) is True
    first = subprocess.run(command, check=False, capture_output=True, text=True, env=environment)
    assert first.returncode == 0, first.stderr
    original = output.read_bytes()
    second = subprocess.run(command, check=False, capture_output=True, text=True, env=environment)
    assert second.returncode != 0
    assert "already exists" in second.stderr
    assert output.read_bytes() == original
    assert "external-witness-secret" not in output.read_text(encoding="utf-8")
