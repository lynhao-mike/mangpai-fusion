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
from engine.evaluation.prospective_artifacts import canonical_artifact_sha256, publish_new_json
from engine.evaluation.prospective_single_case import (
    ContaminationError,
    SIX_SCHOOLS,
    build_single_case_intake,
    build_single_case_staged_frozen_run,
    prepare_single_case_blind_bundle,
)
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
    dry = subprocess.run(
        [*command, "--dry-run"], check=False, capture_output=True, text=True,
        encoding="utf-8", env=environment,
    )
    assert dry.returncode == 0, dry.stderr
    assert not output.exists()
    assert verify_witness_registry(json.loads(dry.stdout), key) is True
    first = subprocess.run(
        command, check=False, capture_output=True, text=True, encoding="utf-8", env=environment,
    )
    assert first.returncode == 0, first.stderr
    original = output.read_bytes()
    second = subprocess.run(
        command, check=False, capture_output=True, text=True, encoding="utf-8", env=environment,
    )
    assert second.returncode != 0
    assert "already exists" in second.stderr
    assert output.read_bytes() == original
    assert "external-witness-secret" not in output.read_text(encoding="utf-8")


def _single_case_bundle(
    tmp_path: Path,
    *,
    created_at: str = "2026-07-15T23:59:58Z",
    freeze_at: str = "2026-07-16T00:00:00Z",
) -> tuple[Path, dict, dict]:
    case_id = "P-GO-2026-001-乾-甲子乙丑丙寅丁卯"
    input_path = tmp_path / "source" / case_id / "input.md"
    input_path.parent.mkdir(parents=True)
    input_path.write_text(
        "Sex:乾\n$FOUR\nY:比肩,甲,子,正印\nM:劫财,乙,丑,正财\n"
        "D:元男,丙,寅,偏印\nH:伤官,丁,卯,正印\n$DY_LOOP\n"
        "#2026,8岁,戊辰,食神\n> 2026,丙午,食神\n",
        encoding="utf-8",
    )
    tasks = _read(TASKS)
    question_draft = {
        "future_task_id": "career.role_change",
        "question_text_redacted": "未来三个月是否发生显著岗位角色变化？",
        "outcome_type": "binary",
        "positive_definition": "发生并有雇佣资料或本人确认",
        "negative_definition": "完整窗口结束且核验来源确认未发生",
        "verification_source_requirements": ["custody://structured-interview"],
        "observation_window": {
            "start_at": freeze_at,
            "end_at": "2026-10-16T00:00:00Z",
        },
    }
    intake, question = build_single_case_intake(
        input_path,
        tasks,
        SIX_SCHOOLS,
        "human-test",
        {"P-GO-2026-001": ["career.role_change", "career.change_window"]},
        question_draft,
        created_at=created_at,
        case_root=tmp_path / "parents",
    )
    publish_new_json(Path(question["artifact_path"]), question, dry_run=False)
    publish_new_json(Path(intake["artifact_path"]), intake, dry_run=False)
    root = Path(intake["artifact_path"]).with_name(
        f"{case_id}--blind-bundle--v001"
    )
    prepare_single_case_blind_bundle(intake, question, TASKS, RULES, root, dry_run=False)
    return root, intake, question


def _reseal_bundle(bundle: Path, name: str) -> None:
    from engine.evaluation.prospective_artifacts import canonical_artifact_sha256

    manifest_path = bundle / "bundle-manifest.json"
    manifest = _read(manifest_path)
    manifest["files"][name] = hashlib.sha256((bundle / name).read_bytes()).hexdigest()
    manifest["bundle_sha256"] = hashlib.sha256(json.dumps(
        manifest["files"], ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    manifest["artifact_sha256"] = canonical_artifact_sha256(manifest)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_single_case_frozen_run_is_complete_unique_parent_bound_grid(tmp_path: Path) -> None:
    root, intake, question = _single_case_bundle(tmp_path)

    artifact = build_single_case_staged_frozen_run(root)

    assignments = artifact["case_task_assignments"]
    outputs = artifact["frozen_run"]["outputs"]
    task_count = len(assignments[0]["task_ids"])
    assert len(assignments) == 1
    assert len(outputs) == 6 * task_count
    assert len({(row["case_id"], row["school_id"], row["task_id"]) for row in outputs}) == len(outputs)
    assert {row["state"] for row in outputs} <= {"claim", "abstain", "unsupported"}
    assert artifact["future_question_registration_sha256"] == question["artifact_sha256"]
    assert artifact["intake_sha256"] == intake["artifact_sha256"]
    assert artifact["task_catalog_sha256"] == _read(root / "bundle-manifest.json")["files"]["tasks.json"]
    assert artifact["rule_snapshot_sha256"] == _read(root / "bundle-manifest.json")["files"]["rule-snapshot.json"]
    assert artifact["bundle_manifest_sha256"] == _read(root / "bundle-manifest.json")["artifact_sha256"]
    assert artifact["parents"] == [
        {"artifact_path": intake["artifact_path"], "artifact_sha256": intake["artifact_sha256"]},
        {"artifact_path": question["artifact_path"], "artifact_sha256": question["artifact_sha256"]},
        {"artifact_path": (root / "tasks.json").as_posix(), "artifact_sha256": artifact["task_catalog_sha256"]},
        {"artifact_path": (root / "rule-snapshot.json").as_posix(), "artifact_sha256": artifact["rule_snapshot_sha256"]},
        {"artifact_path": (root / "bundle-manifest.json").as_posix(), "artifact_sha256": artifact["bundle_manifest_sha256"]},
    ]
    assert artifact["frozen_run"]["frozen_at"] == question["observation_window"]["start_at"]
    assert artifact["case_id"] == intake["case_id"]
    assert artifact["subject_id_hash"] == intake["subject_id_hash"]
    assert artifact["created_at"] == artifact["frozen_run"]["frozen_at"]
    assert artifact["artifact_path"].endswith(
        f"{intake['case_id']}--frozen-run--v001.json"
    )
    manifest = _read(root / "bundle-manifest.json")
    assert intake["created_at"] <= manifest["created_at"] < artifact["created_at"]
    assert question["created_at"] <= manifest["created_at"]
    from engine.evaluation.prospective_artifacts import ArtifactRef, validate_parent_ref
    assert validate_parent_ref(ArtifactRef(**artifact["parents"][-1])) == manifest
    assert build_single_case_staged_frozen_run(root) == artifact


def test_single_case_frozen_run_rejects_two_cases_even_if_manifest_is_resealed(tmp_path: Path) -> None:
    root, _, _ = _single_case_bundle(tmp_path)
    intake_path = root / "intake.json"
    intake = _read(intake_path)
    intake["records"].append({"case_id": "P-GO-2026-002-坤-戊辰己巳庚午辛未", "task_ids": ["career.role_change"]})
    intake_path.write_text(json.dumps(intake, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    _reseal_bundle(root, "intake.json")

    with pytest.raises(ContaminationError, match="STOP|exactly one"):
        build_single_case_staged_frozen_run(root)


@pytest.mark.parametrize("mutation", ["duplicate", "missing-school"])
def test_single_case_frozen_run_rejects_incomplete_or_duplicate_grid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    root, _, _ = _single_case_bundle(tmp_path)
    original = prospective.build_staged_frozen_run(root)
    outputs = original["frozen_run"]["outputs"]
    if mutation == "duplicate":
        outputs[-1] = dict(outputs[0])
    else:
        school = outputs[0]["school_id"]
        original["frozen_run"]["outputs"] = [row for row in outputs if row["school_id"] != school]
    monkeypatch.setattr(prospective, "build_staged_frozen_run", lambda _: original)

    with pytest.raises(ContaminationError, match="grid|duplicate|missing"):
        build_single_case_staged_frozen_run(root)


@pytest.mark.parametrize("parent", ["intake", "question", "tasks", "rule", "bundle"])
def test_single_case_frozen_run_stops_on_any_actual_parent_byte_change(
    tmp_path: Path, parent: str,
) -> None:
    root, intake, question = _single_case_bundle(tmp_path)
    paths = {
        "intake": Path(intake["artifact_path"]),
        "question": Path(question["artifact_path"]),
        "tasks": root / "tasks.json",
        "rule": root / "rule-snapshot.json",
        "bundle": root / "bundle-manifest.json",
    }
    paths[parent].write_bytes(paths[parent].read_bytes() + b" ")

    with pytest.raises((ContaminationError, ValueError), match="STOP|drift|hash|invalid"):
        build_single_case_staged_frozen_run(root)


def test_single_case_frozen_run_rejects_rehashed_future_question_drift(tmp_path: Path) -> None:
    root, _, _ = _single_case_bundle(tmp_path)
    question_path = root / "future-question.json"
    question = _read(question_path)
    question["question_text_redacted"] = "未来三个月是否调任其他岗位？"
    from engine.evaluation.prospective_artifacts import canonical_artifact_sha256
    question["artifact_sha256"] = canonical_artifact_sha256(question)
    question_path.write_text(json.dumps(question, ensure_ascii=False, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    _reseal_bundle(root, "future-question.json")

    with pytest.raises(ContaminationError, match="question|parent|drift"):
        build_single_case_staged_frozen_run(root)


def test_single_case_frozen_run_keeps_timing_claim_with_structured_liunian_fact_ref(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _, _ = _single_case_bundle(tmp_path)
    staged = prospective.build_staged_frozen_run(root)
    timing = next(row for row in staged["frozen_run"]["outputs"] if row["task_id"] == "career.change_window")
    timing.update({
        "state": "claim",
        "rationale": "timing derived from annual chart fact",
        "predictions": [{
            "prediction_id": "prediction-safe",
            "event_label": "career_change",
            "probability": 0.5,
            "time_window": {"start_year": 2026, "end_year": 2026, "label": "annual"},
            "evidence_refs": ["evidence-annual-trigger"],
            "fact_refs": ["liunian_steps.0", "four_pillars.day"],
            "falsifier": "window elapsed without event",
        }],
    })
    monkeypatch.setattr(prospective, "build_staged_frozen_run", lambda _: staged)

    artifact = build_single_case_staged_frozen_run(root)

    safe = next(row for row in artifact["frozen_run"]["outputs"] if (
        row["school_id"], row["task_id"]
    ) == (timing["school_id"], timing["task_id"]))
    assert safe["state"] == "claim"
    assert safe["predictions"][0]["fact_refs"] == ["liunian_steps.0", "four_pillars.day"]


def test_single_case_frozen_run_never_freezes_unresolved_liunian_fact_ref(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _, _ = _single_case_bundle(tmp_path)
    staged = prospective.build_staged_frozen_run(root)
    timing = next(row for row in staged["frozen_run"]["outputs"] if row["task_id"] == "career.change_window")
    timing.update({
        "state": "claim",
        "rationale": "timing cites a nonexistent annual chart fact",
        "predictions": [{
            "prediction_id": "prediction-unresolved",
            "event_label": "career_change",
            "probability": 0.5,
            "time_window": {"start_year": 2026, "end_year": 2026, "label": "annual"},
            "evidence_refs": ["evidence-invalid-annual-trigger"],
            "fact_refs": ["liunian_steps.999"],
            "falsifier": "window elapsed without event",
        }],
    })
    monkeypatch.setattr(prospective, "build_staged_frozen_run", lambda _: staged)

    artifact = build_single_case_staged_frozen_run(root)

    safe = next(row for row in artifact["frozen_run"]["outputs"] if (
        row["school_id"], row["task_id"]
    ) == (timing["school_id"], timing["task_id"]))
    assert safe["state"] == "abstain"
    assert safe["predictions"] == []
    assert "liunian_steps" in safe["rationale"]


def test_single_case_frozen_run_never_freezes_timing_claim_without_liunian_fact_ref(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _, _ = _single_case_bundle(tmp_path)
    staged = prospective.build_staged_frozen_run(root)
    timing = next(row for row in staged["frozen_run"]["outputs"] if row["task_id"] == "career.change_window")
    timing.update({
        "state": "claim",
        "rationale": "timing guessed from text",
        "predictions": [{
            "prediction_id": "prediction-unsafe",
            "event_label": "career_change",
            "probability": 0.5,
            "time_window": {"start_year": 2026, "end_year": 2026, "label": "annual"},
            "evidence_refs": ["opaque-evidence-id"],
            "falsifier": "window elapsed without event",
        }],
    })
    monkeypatch.setattr(prospective, "build_staged_frozen_run", lambda _: staged)

    artifact = build_single_case_staged_frozen_run(root)

    safe = next(row for row in artifact["frozen_run"]["outputs"] if (
        row["school_id"], row["task_id"]
    ) == (timing["school_id"], timing["task_id"]))
    assert safe["state"] == "abstain"
    assert safe["predictions"] == []
    assert "liunian_steps" in safe["rationale"]


def test_single_case_witness_registry_uses_current_artifact_schema(tmp_path: Path) -> None:
    root, intake, _ = _single_case_bundle(tmp_path)
    frozen = build_single_case_staged_frozen_run(root)
    frozen_path = Path(frozen["artifact_path"])
    publish_new_json(frozen_path, frozen, dry_run=False)
    registry_path = Path(intake["artifact_path"]).with_name(
        f"{intake['case_id']}--witness-registry--v001.json"
    )

    registry = prospective.build_witness_freeze_registry(
        Path(intake["artifact_path"]), root, frozen_path, b"TEST-FIXTURE-KEY-NOT-REAL",
        artifact_path=registry_path,
    )

    assert registry["case_id"] == intake["case_id"]
    assert registry["subject_id_hash"] == intake["subject_id_hash"]
    assert registry["artifact_path"] == registry_path.as_posix()
    assert len(registry["events"]) == 3
    assert [event["event_type"] for event in registry["events"]] == [
        "registered", "prepared", "freeze",
    ]
    assert registry["artifact_sha256"] == canonical_artifact_sha256(registry)


def test_single_case_cli_is_create_only_and_keeps_legacy_command(tmp_path: Path) -> None:
    root, intake, _ = _single_case_bundle(tmp_path)
    output = Path(intake["artifact_path"]).with_name(
        f"{intake['case_id']}--frozen-run--v001.json"
    )
    command = [
        sys.executable, "-m", "tools.school_capability_prospective",
        "stage-single-case-frozen-run", "--bundle-root", str(root), "--out", str(output),
        "--now-utc", "2026-07-16T00:00:00Z",
    ]
    dry = subprocess.run([*command, "--dry-run"], check=False, capture_output=True, text=True)
    assert dry.returncode == 0, dry.stderr
    assert not output.exists()
    assert json.loads(dry.stdout)["schema_version"] == "school-capability-single-case-staged-run/v1"

    first = subprocess.run(command, check=False, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    original = output.read_bytes()
    second = subprocess.run(command, check=False, capture_output=True, text=True)
    assert second.returncode != 0
    assert "already exists" in second.stderr
    assert output.read_bytes() == original
    assert "stage-frozen-run" in prospective._parser().format_help()


def test_single_case_cli_rejects_noncanonical_formal_output_path(tmp_path: Path) -> None:
    root, _, _ = _single_case_bundle(tmp_path)
    output = tmp_path / "single-frozen.json"
    command = [
        sys.executable, "-m", "tools.school_capability_prospective",
        "stage-single-case-frozen-run", "--bundle-root", str(root), "--out", str(output),
        "--now-utc", "2026-07-16T00:00:00Z",
    ]

    result = subprocess.run(command, check=False, capture_output=True, text=True)

    assert result.returncode != 0
    assert "canonical" in result.stderr.lower()
    assert not output.exists()


def _v002_single_case_bundle(
    tmp_path: Path, *, publish_v001_frozen: bool = True,
) -> tuple[Path, dict, dict, dict]:
    v001_root, v001_intake, v001_question = _single_case_bundle(
        tmp_path,
        created_at="2026-07-17T05:29:58Z",
        freeze_at="2026-07-17T05:30:00Z",
    )
    v001_frozen = build_single_case_staged_frozen_run(
        v001_root, now_utc="2026-07-17T05:30:00Z",
    )
    if publish_v001_frozen:
        publish_new_json(Path(v001_frozen["artifact_path"]), v001_frozen, dry_run=False)
    case_id = v001_intake["case_id"]
    input_path = tmp_path / "source" / case_id / "input.md"
    question_draft = {
        "future_task_id": "career.role_change",
        "question_text_redacted": "未来三个月是否发生显著岗位角色变化？",
        "outcome_type": "binary",
        "positive_definition": "发生并有雇佣资料或本人确认",
        "negative_definition": "完整窗口结束且核验来源确认未发生",
        "verification_source_requirements": ["custody://structured-interview"],
        "observation_window": {
            "start_at": "2026-07-17T05:40:00Z",
            "end_at": "2026-10-17T05:40:00Z",
        },
    }
    v002_intake, v002_question = build_single_case_intake(
        input_path,
        _read(TASKS),
        SIX_SCHOOLS,
        "human-test",
        {"P-GO-2026-001": ["career.role_change", "career.change_window"]},
        question_draft,
        created_at="2026-07-17T05:39:58Z",
        case_root=tmp_path / "parents",
        version=2,
        question_revision={
            "supersedes": v001_question["artifact_path"],
            "supersedes_sha256": v001_question["artifact_sha256"],
            "reason": "Bind observation start to actual revised freeze",
            "approved_by": "human-approver-01",
        },
        intake_revision={
            "supersedes": v001_intake["artifact_path"],
            "supersedes_sha256": v001_intake["artifact_sha256"],
            "reason": "Bind revised future question",
            "approved_by": "human-approver-01",
        },
    )
    publish_new_json(Path(v002_question["artifact_path"]), v002_question, dry_run=False)
    publish_new_json(Path(v002_intake["artifact_path"]), v002_intake, dry_run=False)
    v002_root = Path(v002_intake["artifact_path"]).with_name(
        f"{case_id}--blind-bundle--v002"
    )
    v001_manifest = _read(v001_root / "bundle-manifest.json")
    prepare_single_case_blind_bundle(
        v002_intake,
        v002_question,
        TASKS,
        RULES,
        v002_root,
        dry_run=False,
        revision={
            "supersedes": v001_manifest["artifact_path"],
            "supersedes_sha256": v001_manifest["artifact_sha256"],
            "reason": "Use the revised registered observation window",
            "approved_by": "human-approver-01",
        },
    )
    return v002_root, v002_intake, v002_question, v001_frozen


def test_v002_single_case_frozen_run_uses_canonical_versioned_path_and_revision_chain(
    tmp_path: Path,
) -> None:
    root, intake, _, v001_frozen = _v002_single_case_bundle(tmp_path)
    revision = {
        "supersedes": v001_frozen["artifact_path"],
        "supersedes_sha256": v001_frozen["artifact_sha256"],
        "reason": "Freeze revised registration and blind bundle",
        "approved_by": "human-approver-01",
    }

    artifact = build_single_case_staged_frozen_run(
        root, now_utc="2026-07-17T05:40:00Z", revision=revision,
    )

    assert artifact["artifact_path"].endswith(f"{intake['case_id']}--frozen-run--v002.json")
    assert artifact["executed_at"] == "2026-07-17T05:40:00Z"
    assert {field: artifact[field] for field in revision} == revision


def test_v002_migration_can_supersede_v001_bundle_when_no_formal_run_or_leakage_exists(
    tmp_path: Path,
) -> None:
    root, intake, _, _ = _v002_single_case_bundle(
        tmp_path, publish_v001_frozen=False,
    )
    v001_manifest = _read(root.with_name(root.name.replace("v002", "v001")) / "bundle-manifest.json")
    revision = {
        "supersedes": v001_manifest["artifact_path"],
        "supersedes_sha256": v001_manifest["artifact_sha256"],
        "reason": "Approved parent-chain migration before first formal freeze",
        "approved_by": "human-approver-01",
    }

    artifact = build_single_case_staged_frozen_run(
        root,
        freeze_at="2026-07-17T05:40:00Z",
        executed_at="2026-07-17T05:40:30Z",
        revision=revision,
        migration_context={
            "revision_scope": "parent_chain",
            "superseded_chain_terminal_kind": "blind-bundle",
        },
    )

    assert artifact["case_id"] == intake["case_id"]
    assert artifact["revision_scope"] == "parent_chain"
    assert artifact["superseded_chain_terminal_kind"] == "blind-bundle"
    assert artifact["freeze_at"] == "2026-07-17T05:40:00Z"
    assert artifact["executed_at"] == "2026-07-17T05:40:30Z"
    assert artifact["frozen_run"]["frozen_at"] == artifact["freeze_at"]
    assert artifact["supersedes"] == v001_manifest["artifact_path"]


def test_v002_migration_cannot_bypass_existing_formal_v001_frozen_run(tmp_path: Path) -> None:
    root, _, _, _ = _v002_single_case_bundle(tmp_path)
    v001_manifest = _read(root.with_name(root.name.replace("v002", "v001")) / "bundle-manifest.json")

    with pytest.raises((ContaminationError, ValueError), match="latest|frozen|supersedes|parent"):
        build_single_case_staged_frozen_run(
            root,
            freeze_at="2026-07-17T05:40:00Z",
            executed_at="2026-07-17T05:40:30Z",
            revision={
                "supersedes": v001_manifest["artifact_path"],
                "supersedes_sha256": v001_manifest["artifact_sha256"],
                "reason": "Must not bypass an existing formal run",
                "approved_by": "human-approver-01",
            },
            migration_context={
                "revision_scope": "parent_chain",
                "superseded_chain_terminal_kind": "blind-bundle",
            },
        )


@pytest.mark.parametrize(
    ("executed_at", "accepted"),
    [
        ("2026-07-17T05:39:59Z", False),
        ("2026-07-17T05:40:00Z", True),
        ("2026-07-17T05:41:00Z", True),
        ("2026-07-17T05:41:01Z", False),
    ],
)
def test_single_case_frozen_run_allows_execution_only_in_sixty_second_freeze_window(
    tmp_path: Path, executed_at: str, accepted: bool,
) -> None:
    root, _, _ = _single_case_bundle(
        tmp_path,
        created_at="2026-07-17T05:39:58Z",
        freeze_at="2026-07-17T05:40:00Z",
    )

    if not accepted:
        with pytest.raises((ContaminationError, ValueError), match="executed_at|60|freeze"):
            build_single_case_staged_frozen_run(
                root,
                freeze_at="2026-07-17T05:40:00Z",
                executed_at=executed_at,
            )
        return

    artifact = build_single_case_staged_frozen_run(
        root,
        freeze_at="2026-07-17T05:40:00Z",
        executed_at=executed_at,
    )
    assert artifact["freeze_at"] == "2026-07-17T05:40:00Z"
    assert artifact["executed_at"] == executed_at
    assert artifact["frozen_run"]["frozen_at"] == artifact["freeze_at"]


def test_v002_single_case_cli_dry_run_and_formal_publish_are_create_only(tmp_path: Path) -> None:
    root, _, _, v001_frozen = _v002_single_case_bundle(tmp_path)
    output = Path(v001_frozen["artifact_path"]).with_name(
        f"{v001_frozen['case_id']}--frozen-run--v002.json"
    )
    command = [
        sys.executable, "-m", "tools.school_capability_prospective",
        "stage-single-case-frozen-run",
        "--bundle-root", str(root),
        "--out", str(output),
        "--now-utc", "2026-07-17T05:40:00Z",
        "--supersedes", v001_frozen["artifact_path"],
        "--supersedes-sha256", v001_frozen["artifact_sha256"],
        "--reason", "Freeze revised registration and blind bundle",
        "--approved-by", "human-approver-01",
    ]

    dry = subprocess.run([*command, "--dry-run"], check=False, capture_output=True, text=True)
    assert dry.returncode == 0, dry.stderr
    assert not output.exists()
    assert json.loads(dry.stdout)["executed_at"] == "2026-07-17T05:40:00Z"

    first = subprocess.run(command, check=False, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    original = output.read_bytes()
    second = subprocess.run(command, check=False, capture_output=True, text=True)
    assert second.returncode != 0
    assert "already exists" in second.stderr
    assert output.read_bytes() == original
