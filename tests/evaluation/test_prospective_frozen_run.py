from __future__ import annotations

import ast
import hashlib
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from dataclasses import replace

from engine.evaluation.freeze import verify_frozen_run
from engine.evaluation.models import FrozenBlindRun
import engine.evaluation.prospective_artifacts as prospective_artifacts
import engine.evaluation.prospective_single_case as prospective_single_case
from engine.evaluation.prospective_artifacts import (
    canonical_artifact_sha256,
    publish_new_json,
    single_case_artifact_path,
)
from engine.evaluation.prospective_capability_identity import (
    build_capability_identity_artifact,
    validate_capability_identity_ref,
)
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
from tests.evaluation.test_governance_shadow_adapter import (
    _claim as governance_claim_fixture,
    _projection as governance_projection_fixture,
    _shadow as governance_shadow_fixture,
)


TASKS = Path("META/prospective-go-task-catalog-v1.json")
RULES = Path("META/prospective-go-rule-snapshot-v1.json")
SCHOOLS = ["ziping", "ditiansui", "duan", "ren", "gao", "yang"]


@pytest.fixture(autouse=True)
def _repository_authority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path.absolute()
    state = root / "META" / "project-state.json"
    contract = (
        root
        / ".omo"
        / "drafts"
        / ("w2-c4-governance-promotion-remediation-r3-admission-contract-2026-08-08.md")
    )
    state.parent.mkdir(parents=True, exist_ok=True)
    contract.parent.mkdir(parents=True, exist_ok=True)
    state.write_bytes(Path("META/project-state.json").read_bytes())
    contract.write_bytes(
        Path(
            ".omo/drafts/w2-c4-governance-promotion-remediation-r3-admission-contract-2026-08-08.md"
        ).read_bytes()
    )
    monkeypatch.setattr(prospective_artifacts, "_trusted_repository_root", lambda: root)


def _identity_ref(tmp_path: Path, claim: object):
    shadow = governance_shadow_fixture(claim)
    projection = governance_projection_fixture(shadow, claim)
    _, reference = build_capability_identity_artifact(
        claim,  # type: ignore[arg-type]
        governance_result=shadow,
        governance_projection=projection,
        created_at="2026-08-08T00:00:00Z",
        source_output_path=tmp_path / "governance-source.json",
        output_path=tmp_path / "capability-identity.json",
        dry_run=False,
    )
    return reference


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _bundle(tmp_path: Path, *, task_ids: list[str] | None = None) -> tuple[Path, dict]:
    case_id = "P-GO-TEST-001-乾-甲子乙丑丙寅丁卯"
    input_path = tmp_path / "source" / case_id / "input.md"
    input_path.parent.mkdir(parents=True)
    input_path.write_text("四柱：甲子 乙丑 丙寅 丁卯\n性别：乾\n", encoding="utf-8")
    tasks = _read(TASKS)
    intake = register_prospective_intake(
        [input_path],
        tasks,
        SCHOOLS,
        "human-test",
        tasks_by_case={case_id: task_ids} if task_ids else None,
    )
    root = tmp_path / "bundle"
    manifest = prepare_blind_bundle(intake, TASKS, RULES, root)
    return root, manifest


def test_build_staged_run_uses_bundle_only_and_preserves_total_six_source_grid(
    tmp_path: Path,
) -> None:
    root, manifest = _bundle(
        tmp_path, task_ids=["career.role_change", "health.system_risk"]
    )

    artifact = build_staged_frozen_run(root)

    assert artifact["schema_version"] == "school-capability-prospective-staged-run/v1"
    assert artifact["bundle_sha256"] == manifest["bundle_sha256"]
    assert artifact["task_catalog_sha256"] == manifest["files"]["tasks.json"]
    assert artifact["rule_snapshot_sha256"] == manifest["files"]["rule-snapshot.json"]
    assert artifact["case_task_assignments"] == [
        {
            "case_id": "P-GO-TEST-001-乾-甲子乙丑丙寅丁卯",
            "task_ids": ["career.role_change", "health.system_risk"],
        }
    ]
    run = FrozenBlindRun.from_dict(artifact["frozen_run"])
    verify_frozen_run(run)
    assert run.task_catalog_version == (
        "prospective-go-tasks-v1@sha256:" + manifest["files"]["tasks.json"]
    )
    assert run.rule_snapshot_id == (
        "prospective-go-six-source-ten-task-rules-v1@sha256:"
        + manifest["files"]["rule-snapshot.json"]
    )
    assert len(run.outputs) == 12
    assert {output.school_id for output in run.outputs} == set(SCHOOLS)
    assert {output.task_id for output in run.outputs} == {
        "career.role_change",
        "health.system_risk",
    }
    assert {output.state for output in run.outputs} <= {
        "claim",
        "abstain",
        "unsupported",
    }
    assert (
        artifact["artifact_sha256"]
        == hashlib.sha256(
            json.dumps(
                {
                    key: value
                    for key, value in artifact.items()
                    if key != "artifact_sha256"
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
    )
    assert build_staged_frozen_run(root) == artifact


def test_build_staged_run_rejects_manifest_tampering_and_extra_files(
    tmp_path: Path,
) -> None:
    root, _ = _bundle(tmp_path)
    chart = next((root / "cases").glob("*/chart.json"))
    chart.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        build_staged_frozen_run(root)

    root, _ = _bundle(tmp_path / "extra")
    (root / "unexpected.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="files do not match manifest"):
        build_staged_frozen_run(root)


def test_cli_dry_run_writes_nothing_and_formal_run_refuses_overwrite(
    tmp_path: Path,
) -> None:
    root, _ = _bundle(tmp_path)
    output = tmp_path / "staged-run.json"
    command = [
        sys.executable,
        "-m",
        "tools.school_capability_prospective",
        "stage-frozen-run",
        "--bundle-root",
        str(root),
        "--out",
        str(output),
    ]

    dry = subprocess.run(
        [*command, "--dry-run"], check=False, capture_output=True, text=True
    )
    assert dry.returncode == 0, dry.stderr
    assert not output.exists()
    assert (
        json.loads(dry.stdout)["schema_version"]
        == "school-capability-prospective-staged-run/v1"
    )

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


def test_build_witness_freeze_registry_generates_exact_per_case_chain(
    tmp_path: Path,
) -> None:
    intake_path, bundle_root, staged_path, intake, manifest = _witness_fixture(tmp_path)
    key = b"external-witness-secret"

    registry = prospective.build_witness_freeze_registry(
        intake_path,
        bundle_root,
        staged_path,
        key,
    )

    assert verify_witness_registry(registry, key) is True
    assert [event["event_type"] for event in registry["events"]] == [
        "registered",
        "prepared",
        "freeze",
        "registered",
        "prepared",
        "freeze",
    ]
    assert "reveal" not in {event["event_type"] for event in registry["events"]}
    intake_by_case = {row["case_id"]: row for row in intake["records"]}
    frozen = _read(staged_path)["frozen_run"]
    for case_id in sorted(intake_by_case):
        events = [
            event
            for event in registry["events"]
            if event["payload"]["case_id"] == case_id
        ]
        assert [event["event_type"] for event in events] == [
            "registered",
            "prepared",
            "freeze",
        ]
        assert events[0]["payload"] == {
            "case_id": case_id,
            "input_sha256": intake_by_case[case_id]["input_sha256"],
            "subject_id_hash": intake_by_case[case_id]["subject_id_hash"],
        }
        assert events[1]["payload"] == {
            "case_id": case_id,
            "bundle_sha256": manifest["bundle_sha256"],
        }
        assert events[2]["payload"] == {
            "case_id": case_id,
            "freeze_hash": frozen["freeze_hash"],
        }
        assert (
            events[0]["occurred_at"]
            < events[1]["occurred_at"]
            < events[2]["occurred_at"]
        )
        assert events[2]["occurred_at"] == frozen["frozen_at"]


def test_witness_freeze_registry_rejects_tamper_case_and_hash_mismatch(
    tmp_path: Path,
) -> None:
    intake_path, bundle_root, staged_path, _, _ = _witness_fixture(tmp_path)
    key = b"external-witness-secret"

    tampered = _read(staged_path)
    tampered["frozen_run"]["freeze_hash"] = "f" * 64
    staged_path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ValueError, match="frozen run|artifact hash"):
        prospective.build_witness_freeze_registry(
            intake_path, bundle_root, staged_path, key
        )

    staged_path.write_text(
        json.dumps(build_staged_frozen_run(bundle_root)), encoding="utf-8"
    )
    mismatched = _read(intake_path)
    mismatched["records"] = mismatched["records"][:1]
    intake_path.write_text(json.dumps(mismatched), encoding="utf-8")
    with pytest.raises(ValueError, match="case set"):
        prospective.build_witness_freeze_registry(
            intake_path, bundle_root, staged_path, key
        )


def test_witness_freeze_registry_rejects_wrong_existing_order_and_cli_is_no_overwrite(
    tmp_path: Path,
) -> None:
    intake_path, bundle_root, staged_path, intake, manifest = _witness_fixture(tmp_path)
    key = b"external-witness-secret"
    case_id = intake["records"][0]["case_id"]
    wrong = append_witness_event(
        None,
        {
            "event_type": "prepared",
            "occurred_at": intake["generated_at"],
            "payload": {"case_id": case_id, "bundle_sha256": manifest["bundle_sha256"]},
        },
        key,
    )
    with pytest.raises(ValueError, match="order|existing witness"):
        prospective.build_witness_freeze_registry(
            intake_path,
            bundle_root,
            staged_path,
            key,
            registry=wrong,
        )

    output = tmp_path / "witness.json"
    command = [
        sys.executable,
        "-m",
        "tools.school_capability_prospective",
        "witness-freeze-chain",
        "--intake",
        str(intake_path),
        "--bundle-root",
        str(bundle_root),
        "--staged-run",
        str(staged_path),
        "--out",
        str(output),
    ]
    environment = {
        **os.environ,
        "PYTHONUTF8": "1",
        "SCHOOL_CAPABILITY_WITNESS_KEY": "external-witness-secret",
    }
    dry = subprocess.run(
        [*command, "--dry-run"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )
    assert dry.returncode == 0, dry.stderr
    assert not output.exists()
    assert verify_witness_registry(json.loads(dry.stdout), key) is True
    first = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )
    assert first.returncode == 0, first.stderr
    original = output.read_bytes()
    second = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
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
    task_ids: list[str] | None = None,
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
    assigned_tasks = task_ids or ["career.role_change", "career.change_window"]
    question_draft = {
        "future_task_id": assigned_tasks[0],
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
        {"P-GO-2026-001": assigned_tasks},
        question_draft,
        created_at=created_at,
        case_root=tmp_path / "parents",
    )
    publish_new_json(Path(question["artifact_path"]), question, dry_run=False)
    publish_new_json(Path(intake["artifact_path"]), intake, dry_run=False)
    root = Path(intake["artifact_path"]).with_name(f"{case_id}--blind-bundle--v001")
    prepare_single_case_blind_bundle(
        intake, question, TASKS, RULES, root, dry_run=False
    )
    return root, intake, question


def _reseal_bundle(bundle: Path, name: str) -> None:
    from engine.evaluation.prospective_artifacts import canonical_artifact_sha256

    manifest_path = bundle / "bundle-manifest.json"
    manifest = _read(manifest_path)
    manifest["files"][name] = hashlib.sha256((bundle / name).read_bytes()).hexdigest()
    manifest["bundle_sha256"] = hashlib.sha256(
        json.dumps(
            manifest["files"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    manifest["artifact_sha256"] = canonical_artifact_sha256(manifest)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def test_single_case_bundle_preserves_evaluation_note_with_legacy_intake_hash(
    tmp_path: Path,
) -> None:
    root, _, _ = _single_case_bundle(tmp_path)

    task_bytes = (root / "tasks.json").read_bytes()
    tasks = json.loads(task_bytes)
    divorce_task = next(
        task
        for task in tasks["tasks"]
        if task["task_id"] == "marriage.divorce_or_remarriage"
    )
    manifest = _read(root / "bundle-manifest.json")

    assert divorce_task["evaluation_note"] == "只评价是否发生，不把关系压力自动等同离婚"
    assert manifest["files"]["tasks.json"] == hashlib.sha256(task_bytes).hexdigest()


def test_single_case_legacy_mode_accepts_exact_explicit_governance_shadow_defaults(
    tmp_path: Path,
) -> None:
    root, _, _ = _single_case_bundle(tmp_path)

    implicit = build_single_case_staged_frozen_run(root)
    explicit = build_single_case_staged_frozen_run(
        root,
        governance_shadow_result=None,
        governance_shadow_projections=(),
    )

    assert explicit == implicit


def test_governance_single_case_requires_and_uniquely_binds_sealed_capability_identity(
    tmp_path: Path,
) -> None:
    root, intake, _ = _single_case_bundle(
        tmp_path,
        task_ids=["marriage.divorce_or_remarriage"],
    )
    baseline = build_single_case_staged_frozen_run(root)
    claim = governance_claim_fixture()
    shadow = governance_shadow_fixture(claim)
    projection = governance_projection_fixture(
        shadow,
        claim,
        case_id=intake["case_id"],
        task_catalog_version=baseline["frozen_run"]["task_catalog_version"],
        rule_version=baseline["frozen_run"]["rule_snapshot_id"],
    )
    identity, identity_ref = build_capability_identity_artifact(
        claim,
        governance_result=shadow,
        governance_projection=projection,
        created_at=baseline["created_at"],
        source_output_path=tmp_path / "governance-source.json",
        output_path=tmp_path / "capability-identity.json",
        dry_run=False,
    )

    with pytest.raises(ValueError, match="capability identity"):
        build_single_case_staged_frozen_run(
            root,
            governance_shadow_result=shadow,
            governance_shadow_projections=(projection,),
        )

    governed = build_single_case_staged_frozen_run(
        root,
        governance_shadow_result=shadow,
        governance_shadow_projections=(projection,),
        capability_identity_ref=identity_ref,
    )

    expected_ref = {
        "artifact_path": identity_ref.artifact_path,
        "artifact_sha256": identity_ref.artifact_sha256,
    }
    source_ref = {
        "artifact_path": identity.governance_source_ref.artifact_path,
        "artifact_sha256": identity.governance_source_ref.artifact_sha256,
    }
    assert governed["capability_identity_ref"] == expected_ref
    assert governed["governance_source_ref"] == source_ref
    assert governed["parents"].count(expected_ref) == 1
    assert governed["parents"].count(source_ref) == 1
    assert (
        validate_capability_identity_ref(identity_ref).source_claim_id == claim.claim_id
    )
    assert set(FrozenBlindRun.from_dict(governed["frozen_run"]).to_dict()) == {
        "schema_version",
        "task_catalog_version",
        "rule_snapshot_id",
        "frozen_at",
        "outputs",
        "freeze_hash",
    }


def test_single_case_governance_shadow_claim_replaces_only_yang_divorce_slot(
    tmp_path: Path,
) -> None:
    root, intake, _ = _single_case_bundle(
        tmp_path,
        task_ids=["marriage.divorce_or_remarriage", "career.role_change"],
    )
    baseline = build_single_case_staged_frozen_run(root)
    claim = governance_claim_fixture()
    shadow = governance_shadow_fixture(claim)
    projection = governance_projection_fixture(
        shadow,
        claim,
        case_id=intake["case_id"],
        task_catalog_version=baseline["frozen_run"]["task_catalog_version"],
        rule_version=baseline["frozen_run"]["rule_snapshot_id"],
    )

    governed = build_single_case_staged_frozen_run(
        root,
        governance_shadow_result=shadow,
        governance_shadow_projections=(projection,),
        capability_identity_ref=_identity_ref(tmp_path, claim),
    )
    baseline_rows = {
        (row["school_id"], row["task_id"]): row
        for row in baseline["frozen_run"]["outputs"]
    }
    governed_rows = {
        (row["school_id"], row["task_id"]): row
        for row in governed["frozen_run"]["outputs"]
    }
    target = governed_rows[("yang", "marriage.divorce_or_remarriage")]

    assert target["state"] == "claim"
    assert target["rationale"] == "显式投影提供完整事件绑定。"
    assert "yang_qingjuan" not in {row["school_id"] for row in governed_rows.values()}
    assert {
        identity: row
        for identity, row in governed_rows.items()
        if identity != ("yang", "marriage.divorce_or_remarriage")
    } == {
        identity: row
        for identity, row in baseline_rows.items()
        if identity != ("yang", "marriage.divorce_or_remarriage")
    }


@pytest.mark.parametrize(
    "invalid", ("half", "list", "empty", "multiple", "projection-subclass")
)
def test_single_case_governance_shadow_boundary_fails_closed(
    tmp_path: Path, invalid: str
) -> None:
    root, intake, _ = _single_case_bundle(
        tmp_path,
        task_ids=["marriage.divorce_or_remarriage"],
    )
    baseline = build_single_case_staged_frozen_run(root)
    claim = governance_claim_fixture()
    shadow = governance_shadow_fixture(claim)
    projection = governance_projection_fixture(
        shadow,
        claim,
        case_id=intake["case_id"],
        task_catalog_version=baseline["frozen_run"]["task_catalog_version"],
        rule_version=baseline["frozen_run"]["rule_snapshot_id"],
    )
    result = shadow
    projections: object = (projection,)
    if invalid == "half":
        result = None
    elif invalid == "list":
        projections = [projection]
    elif invalid == "empty":
        projections = ()
    elif invalid == "multiple":
        projections = (projection, projection)
    else:
        subclass = type("ProjectionSubclass", (type(projection),), {})
        projections = (
            subclass(
                **{
                    field: getattr(projection, field)
                    for field in projection.__dataclass_fields__
                }
            ),
        )

    with pytest.raises((TypeError, ValueError), match="governance|projection|tuple"):
        build_single_case_staged_frozen_run(
            root,
            governance_shadow_result=result,
            governance_shadow_projections=projections,  # type: ignore[arg-type]
            capability_identity_ref=_identity_ref(tmp_path, claim),
        )


def test_single_case_governance_shadow_binding_mismatches_fail_closed(
    tmp_path: Path,
) -> None:
    root, intake, _ = _single_case_bundle(
        tmp_path,
        task_ids=["marriage.divorce_or_remarriage"],
    )
    baseline = build_single_case_staged_frozen_run(root)
    claim = governance_claim_fixture()
    shadow = governance_shadow_fixture(claim)
    projection = governance_projection_fixture(
        shadow,
        claim,
        case_id=intake["case_id"],
        task_catalog_version=baseline["frozen_run"]["task_catalog_version"],
        rule_version=baseline["frozen_run"]["rule_snapshot_id"],
    )

    for change in (
        {"case_id": "other-case"},
        {"school_id": "yang"},
        {"task_id": "career.role_change"},
        {"task_catalog_version": "other-catalog"},
        {"rule_version": "other-rule"},
    ):
        with pytest.raises(ValueError, match="case|Yang|task|catalog|rule"):
            build_single_case_staged_frozen_run(
                root,
                governance_shadow_result=shadow,
                governance_shadow_projections=(replace(projection, **change),),
                capability_identity_ref=_identity_ref(tmp_path, claim),
            )


@pytest.mark.parametrize(
    ("projection_change", "expected_state"),
    (
        ({"prediction": None}, "abstain"),
        ({"prediction": None, "capability_state": "uncertified"}, "unsupported"),
    ),
)
def test_single_case_governance_shadow_nonclaim_states_replace_only_target(
    tmp_path: Path,
    projection_change: dict[str, object],
    expected_state: str,
) -> None:
    root, intake, _ = _single_case_bundle(
        tmp_path,
        task_ids=["marriage.divorce_or_remarriage", "career.role_change"],
    )
    baseline = build_single_case_staged_frozen_run(root)
    claim = governance_claim_fixture()
    shadow = governance_shadow_fixture(claim)
    projection = governance_projection_fixture(
        shadow,
        claim,
        case_id=intake["case_id"],
        task_catalog_version=baseline["frozen_run"]["task_catalog_version"],
        rule_version=baseline["frozen_run"]["rule_snapshot_id"],
    )

    governed = build_single_case_staged_frozen_run(
        root,
        governance_shadow_result=shadow,
        governance_shadow_projections=(replace(projection, **projection_change),),
        capability_identity_ref=_identity_ref(tmp_path, claim),
    )
    rows = {
        (row["school_id"], row["task_id"]): row
        for row in governed["frozen_run"]["outputs"]
    }

    assert rows[("yang", "marriage.divorce_or_remarriage")]["state"] == expected_state
    assert rows[("yang", "marriage.divorce_or_remarriage")]["predictions"] == []


def test_single_case_governance_shadow_replay_is_deterministic_and_prediction_changes_hash(
    tmp_path: Path,
) -> None:
    root, intake, _ = _single_case_bundle(
        tmp_path,
        task_ids=["marriage.divorce_or_remarriage"],
    )
    baseline = build_single_case_staged_frozen_run(root)
    claim = governance_claim_fixture()
    shadow = governance_shadow_fixture(claim)
    projection = governance_projection_fixture(
        shadow,
        claim,
        case_id=intake["case_id"],
        task_catalog_version=baseline["frozen_run"]["task_catalog_version"],
        rule_version=baseline["frozen_run"]["rule_snapshot_id"],
    )
    arguments = {
        "governance_shadow_result": shadow,
        "governance_shadow_projections": (projection,),
        "capability_identity_ref": _identity_ref(tmp_path, claim),
    }

    first = build_single_case_staged_frozen_run(root, **arguments)
    assert build_single_case_staged_frozen_run(root, **arguments) == first

    changed_binding = replace(projection.prediction, probability=0.64)
    changed = build_single_case_staged_frozen_run(
        root,
        governance_shadow_result=shadow,
        governance_shadow_projections=(
            replace(projection, prediction=changed_binding),
        ),
        capability_identity_ref=arguments["capability_identity_ref"],
    )
    assert changed["frozen_run"]["freeze_hash"] != first["frozen_run"]["freeze_hash"]
    assert changed["artifact_sha256"] != first["artifact_sha256"]


def test_single_case_governance_shadow_merge_precedes_timing_and_grid_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, intake, _ = _single_case_bundle(
        tmp_path,
        task_ids=["marriage.divorce_or_remarriage"],
    )
    baseline = build_single_case_staged_frozen_run(root)
    claim = governance_claim_fixture()
    shadow = governance_shadow_fixture(claim)
    projection = governance_projection_fixture(
        shadow,
        claim,
        case_id=intake["case_id"],
        task_catalog_version=baseline["frozen_run"]["task_catalog_version"],
        rule_version=baseline["frozen_run"]["rule_snapshot_id"],
    )
    import engine.evaluation.prospective_single_case as module

    original_timing = module._safe_timing_outputs
    original_grid = module._assert_complete_single_case_grid
    observed: list[str] = []

    def timing(run: FrozenBlindRun, task_ids: set[str], chart: dict) -> list:
        target = next(row for row in run.outputs if row.school_id == "yang")
        assert target.rationale == projection.rationale
        observed.append("timing")
        return original_timing(run, task_ids, chart)

    def grid(outputs: list, *, case_id: str, task_ids: list[str]) -> None:
        assert observed == ["timing"]
        observed.append("grid")
        original_grid(outputs, case_id=case_id, task_ids=task_ids)

    monkeypatch.setattr(module, "_safe_timing_outputs", timing)
    monkeypatch.setattr(module, "_assert_complete_single_case_grid", grid)

    build_single_case_staged_frozen_run(
        root,
        governance_shadow_result=shadow,
        governance_shadow_projections=(projection,),
        capability_identity_ref=_identity_ref(tmp_path, claim),
    )
    assert observed == ["timing", "grid"]


def test_single_case_w2_c4_parent_reads_and_publication_are_authority_bound() -> None:
    module = ast.parse(
        Path("engine/evaluation/prospective_single_case.py").read_text("utf-8")
    )
    functions = {
        node.name: node
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    owner_names = {
        "_single_case_parent_document",
        "build_single_case_staged_frozen_run",
    }
    calls = [
        node
        for owner_name in owner_names
        for node in ast.walk(functions[owner_name])
        if isinstance(node, ast.Call)
    ]

    rootless_parent_reads = [
        call
        for call in calls
        if isinstance(call.func, ast.Name)
        and call.func.id in {"validate_parent_ref", "_single_case_parent_document"}
        and not any(
            keyword.arg in {"admitted_root", "authority"} for keyword in call.keywords
        )
    ]
    self_selected_roots = [
        node
        for owner_name in owner_names
        for node in ast.walk(functions[owner_name])
        if isinstance(node, ast.Attribute)
        and node.attr == "parent"
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "parent"
    ]

    assert rootless_parent_reads == []
    assert self_selected_roots == []


def test_single_case_governance_shadow_api_and_static_dependencies_are_exact() -> None:
    module_path = Path("engine/evaluation/prospective_single_case.py")
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    signature = inspect.signature(build_single_case_staged_frozen_run)
    imports = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    serialized_keys = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }

    assert (
        signature.parameters["governance_shadow_result"].kind
        is inspect.Parameter.KEYWORD_ONLY
    )
    assert (
        signature.parameters["governance_shadow_projections"].kind
        is inspect.Parameter.KEYWORD_ONLY
    )
    assert imports & {
        "engine.application.governance_shadow_types",
        "engine.evaluation.governance_shadow_adapter",
        "engine.governance.school_registry",
    } == {
        "engine.application.governance_shadow_types",
        "engine.evaluation.governance_shadow_adapter",
        "engine.governance.school_registry",
    }
    assert not imports & {
        "engine.evaluation.scoring",
        "engine.evaluation.reveal",
        "tools.feedback_ingest",
        "tools.render_report",
    }
    assert not serialized_keys & {
        "governance_shadow_result",
        "governance_shadow_projections",
        "projection_custody",
        "governance_metadata",
    }


def test_single_case_frozen_run_is_complete_unique_parent_bound_grid(
    tmp_path: Path,
) -> None:
    root, intake, question = _single_case_bundle(tmp_path)

    artifact = build_single_case_staged_frozen_run(root)

    assignments = artifact["case_task_assignments"]
    outputs = artifact["frozen_run"]["outputs"]
    task_count = len(assignments[0]["task_ids"])
    assert len(assignments) == 1
    assert len(outputs) == 6 * task_count
    assert len(
        {(row["case_id"], row["school_id"], row["task_id"]) for row in outputs}
    ) == len(outputs)
    assert {row["state"] for row in outputs} <= {"claim", "abstain", "unsupported"}
    assert (
        artifact["future_question_registration_sha256"] == question["artifact_sha256"]
    )
    assert artifact["intake_sha256"] == intake["artifact_sha256"]
    assert (
        artifact["task_catalog_sha256"]
        == _read(root / "bundle-manifest.json")["files"]["tasks.json"]
    )
    assert (
        artifact["rule_snapshot_sha256"]
        == _read(root / "bundle-manifest.json")["files"]["rule-snapshot.json"]
    )
    assert (
        artifact["bundle_manifest_sha256"]
        == _read(root / "bundle-manifest.json")["artifact_sha256"]
    )
    assert artifact["parents"] == [
        {
            "artifact_path": intake["artifact_path"],
            "artifact_sha256": intake["artifact_sha256"],
        },
        {
            "artifact_path": question["artifact_path"],
            "artifact_sha256": question["artifact_sha256"],
        },
        {
            "artifact_path": (root / "tasks.json").as_posix(),
            "artifact_sha256": artifact["task_catalog_sha256"],
        },
        {
            "artifact_path": (root / "rule-snapshot.json").as_posix(),
            "artifact_sha256": artifact["rule_snapshot_sha256"],
        },
        {
            "artifact_path": (root / "bundle-manifest.json").as_posix(),
            "artifact_sha256": artifact["bundle_manifest_sha256"],
        },
    ]
    assert (
        artifact["frozen_run"]["frozen_at"]
        == question["observation_window"]["start_at"]
    )
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


def test_single_case_frozen_run_rejects_two_cases_even_if_manifest_is_resealed(
    tmp_path: Path,
) -> None:
    root, _, _ = _single_case_bundle(tmp_path)
    intake_path = root / "intake.json"
    intake = _read(intake_path)
    intake["records"].append(
        {
            "case_id": "P-GO-2026-002-坤-戊辰己巳庚午辛未",
            "task_ids": ["career.role_change"],
        }
    )
    intake_path.write_text(
        json.dumps(intake, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    _reseal_bundle(root, "intake.json")

    with pytest.raises(ContaminationError, match="STOP|exactly one"):
        build_single_case_staged_frozen_run(root)


@pytest.mark.parametrize("mutation", ["duplicate", "missing-school"])
def test_single_case_frozen_run_rejects_incomplete_or_duplicate_grid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    root, _, _ = _single_case_bundle(tmp_path)
    original = prospective.build_staged_frozen_run(root)
    outputs = original["frozen_run"]["outputs"]
    if mutation == "duplicate":
        outputs[-1] = dict(outputs[0])
    else:
        school = outputs[0]["school_id"]
        original["frozen_run"]["outputs"] = [
            row for row in outputs if row["school_id"] != school
        ]
    monkeypatch.setattr(prospective, "build_staged_frozen_run", lambda _: original)

    with pytest.raises(ContaminationError, match="grid|duplicate|missing"):
        build_single_case_staged_frozen_run(root)


@pytest.mark.parametrize("parent", ["intake", "question", "tasks", "rule", "bundle"])
def test_single_case_frozen_run_stops_on_any_actual_parent_byte_change(
    tmp_path: Path,
    parent: str,
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

    with pytest.raises(
        (ContaminationError, ValueError), match="STOP|drift|hash|invalid"
    ):
        build_single_case_staged_frozen_run(root)


def test_single_case_frozen_run_rejects_rehashed_future_question_drift(
    tmp_path: Path,
) -> None:
    root, _, _ = _single_case_bundle(tmp_path)
    question_path = root / "future-question.json"
    question = _read(question_path)
    question["question_text_redacted"] = "未来三个月是否调任其他岗位？"
    from engine.evaluation.prospective_artifacts import canonical_artifact_sha256

    question["artifact_sha256"] = canonical_artifact_sha256(question)
    question_path.write_text(
        json.dumps(question, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    _reseal_bundle(root, "future-question.json")

    with pytest.raises(ContaminationError, match="question|parent|drift"):
        build_single_case_staged_frozen_run(root)


def test_single_case_frozen_run_keeps_timing_claim_with_structured_liunian_fact_ref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _, _ = _single_case_bundle(tmp_path)
    staged = prospective.build_staged_frozen_run(root)
    timing = next(
        row
        for row in staged["frozen_run"]["outputs"]
        if row["task_id"] == "career.change_window"
    )
    timing.update(
        {
            "state": "claim",
            "rationale": "timing derived from annual chart fact",
            "predictions": [
                {
                    "prediction_id": "prediction-safe",
                    "event_label": "career_change",
                    "probability": 0.5,
                    "time_window": {
                        "start_year": 2026,
                        "end_year": 2026,
                        "label": "annual",
                    },
                    "evidence_refs": ["evidence-annual-trigger"],
                    "fact_refs": ["liunian_steps.0", "four_pillars.day"],
                    "falsifier": "window elapsed without event",
                }
            ],
        }
    )
    monkeypatch.setattr(prospective, "build_staged_frozen_run", lambda _: staged)

    artifact = build_single_case_staged_frozen_run(root)

    safe = next(
        row
        for row in artifact["frozen_run"]["outputs"]
        if (row["school_id"], row["task_id"])
        == (timing["school_id"], timing["task_id"])
    )
    assert safe["state"] == "claim"
    assert safe["predictions"][0]["fact_refs"] == [
        "liunian_steps.0",
        "four_pillars.day",
    ]


def test_single_case_frozen_run_never_freezes_unresolved_liunian_fact_ref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _, _ = _single_case_bundle(tmp_path)
    staged = prospective.build_staged_frozen_run(root)
    timing = next(
        row
        for row in staged["frozen_run"]["outputs"]
        if row["task_id"] == "career.change_window"
    )
    timing.update(
        {
            "state": "claim",
            "rationale": "timing cites a nonexistent annual chart fact",
            "predictions": [
                {
                    "prediction_id": "prediction-unresolved",
                    "event_label": "career_change",
                    "probability": 0.5,
                    "time_window": {
                        "start_year": 2026,
                        "end_year": 2026,
                        "label": "annual",
                    },
                    "evidence_refs": ["evidence-invalid-annual-trigger"],
                    "fact_refs": ["liunian_steps.999"],
                    "falsifier": "window elapsed without event",
                }
            ],
        }
    )
    monkeypatch.setattr(prospective, "build_staged_frozen_run", lambda _: staged)

    artifact = build_single_case_staged_frozen_run(root)

    safe = next(
        row
        for row in artifact["frozen_run"]["outputs"]
        if (row["school_id"], row["task_id"])
        == (timing["school_id"], timing["task_id"])
    )
    assert safe["state"] == "abstain"
    assert safe["predictions"] == []
    assert "liunian_steps" in safe["rationale"]


def test_single_case_frozen_run_never_freezes_timing_claim_without_liunian_fact_ref(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _, _ = _single_case_bundle(tmp_path)
    staged = prospective.build_staged_frozen_run(root)
    timing = next(
        row
        for row in staged["frozen_run"]["outputs"]
        if row["task_id"] == "career.change_window"
    )
    timing.update(
        {
            "state": "claim",
            "rationale": "timing guessed from text",
            "predictions": [
                {
                    "prediction_id": "prediction-unsafe",
                    "event_label": "career_change",
                    "probability": 0.5,
                    "time_window": {
                        "start_year": 2026,
                        "end_year": 2026,
                        "label": "annual",
                    },
                    "evidence_refs": ["opaque-evidence-id"],
                    "falsifier": "window elapsed without event",
                }
            ],
        }
    )
    monkeypatch.setattr(prospective, "build_staged_frozen_run", lambda _: staged)

    artifact = build_single_case_staged_frozen_run(root)

    safe = next(
        row
        for row in artifact["frozen_run"]["outputs"]
        if (row["school_id"], row["task_id"])
        == (timing["school_id"], timing["task_id"])
    )
    assert safe["state"] == "abstain"
    assert safe["predictions"] == []
    assert "liunian_steps" in safe["rationale"]


def test_single_case_witness_registry_uses_current_artifact_schema(
    tmp_path: Path,
) -> None:
    root, intake, _ = _single_case_bundle(tmp_path)
    frozen = build_single_case_staged_frozen_run(root)
    frozen_path = Path(frozen["artifact_path"])
    publish_new_json(frozen_path, frozen, dry_run=False)
    registry_path = Path(intake["artifact_path"]).with_name(
        f"{intake['case_id']}--witness-registry--v001.json"
    )

    registry = prospective.build_witness_freeze_registry(
        Path(intake["artifact_path"]),
        root,
        frozen_path,
        b"TEST-FIXTURE-KEY-NOT-REAL",
        artifact_path=registry_path,
    )

    assert registry["case_id"] == intake["case_id"]
    assert registry["subject_id_hash"] == intake["subject_id_hash"]
    assert registry["artifact_path"] == registry_path.as_posix()
    assert len(registry["events"]) == 3
    assert [event["event_type"] for event in registry["events"]] == [
        "registered",
        "prepared",
        "freeze",
    ]
    assert registry["artifact_sha256"] == canonical_artifact_sha256(registry)


def test_single_case_cli_is_create_only_and_keeps_legacy_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, intake, _ = _single_case_bundle(tmp_path)
    output = single_case_artifact_path(
        tmp_path.absolute(), intake["case_id"], "frozen-run", 1
    )
    command = [
        "stage-single-case-frozen-run",
        "--bundle-root",
        str(root),
        "--out",
        str(output),
        "--now-utc",
        "2026-07-16T00:00:00Z",
    ]
    monkeypatch.setattr(
        sys, "argv", ["school-capability-prospective", *command, "--dry-run"]
    )
    assert prospective.main() == 0
    dry = capsys.readouterr()
    assert not output.exists()
    assert (
        json.loads(dry.out)["schema_version"]
        == "school-capability-single-case-staged-run/v1"
    )

    monkeypatch.setattr(sys, "argv", ["school-capability-prospective", *command])
    assert prospective.main() == 0
    capsys.readouterr()
    original = output.read_bytes()
    with pytest.raises(ValueError, match="already exists"):
        prospective.main()
    assert output.read_bytes() == original
    assert "stage-frozen-run" in prospective._parser().format_help()


def test_single_case_cli_rejects_noncanonical_formal_output_path(
    tmp_path: Path,
) -> None:
    root, _, _ = _single_case_bundle(tmp_path)
    output = tmp_path / "single-frozen.json"
    command = [
        sys.executable,
        "-m",
        "tools.school_capability_prospective",
        "stage-single-case-frozen-run",
        "--bundle-root",
        str(root),
        "--out",
        str(output),
        "--now-utc",
        "2026-07-16T00:00:00Z",
    ]

    result = subprocess.run(command, check=False, capture_output=True, text=True)

    assert result.returncode != 0
    assert "canonical" in result.stderr.lower()
    assert not output.exists()


def _v002_single_case_bundle(
    tmp_path: Path,
    *,
    publish_v001_frozen: bool = True,
) -> tuple[Path, dict, dict, dict]:
    v001_root, v001_intake, v001_question = _single_case_bundle(
        tmp_path,
        created_at="2026-07-17T05:29:58Z",
        freeze_at="2026-07-17T05:30:00Z",
    )
    v001_frozen = build_single_case_staged_frozen_run(
        v001_root,
        now_utc="2026-07-17T05:30:00Z",
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
        root,
        now_utc="2026-07-17T05:40:00Z",
        revision=revision,
    )

    assert artifact["artifact_path"].endswith(
        f"{intake['case_id']}--frozen-run--v002.json"
    )
    assert artifact["executed_at"] == "2026-07-17T05:40:00Z"
    assert {field: artifact[field] for field in revision} == revision


def test_v002_migration_can_supersede_v001_bundle_when_no_formal_run_or_leakage_exists(
    tmp_path: Path,
) -> None:
    root, intake, _, _ = _v002_single_case_bundle(
        tmp_path,
        publish_v001_frozen=False,
    )
    v001_manifest = _read(
        root.with_name(root.name.replace("v002", "v001")) / "bundle-manifest.json"
    )
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


def test_parent_chain_migration_propagates_one_exact_authority_to_every_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, intake, question = _single_case_bundle(
        tmp_path,
        created_at="2026-07-17T05:29:58Z",
        freeze_at="2026-07-17T05:30:00Z",
    )
    expected_authority = prospective_artifacts._repository_authority()
    resolver_calls = 0
    observed: dict[str, list[object]] = {
        boundary: []
        for boundary in (
            "case_directory",
            "clean_scan",
            "migration_intake",
            "target_preflight",
            "staging_root",
            "bundle_files",
            "published_parent",
            "bundle_verification",
            "source_read",
            "staging_write",
            "temporary_bundle_write",
            "bundle_publication",
            "json_publication",
        )
    }
    original_bundle = (
        prospective_single_case._prepare_single_case_blind_bundle_with_authority
    )
    original_frozen = (
        prospective_single_case._build_single_case_staged_frozen_run_with_authority
    )
    original_bundle_files = prospective_single_case._single_bundle_files
    original_parent = prospective_single_case._validated_disk_parent
    original_verify = prospective_single_case.verify_single_case_bundle
    original_case_directory = getattr(
        prospective_single_case, "_authenticate_migration_case_directory", None
    )
    original_clean_scan = getattr(
        prospective_single_case, "_assert_migration_paths_clean", None
    )
    original_migration_intake = getattr(
        prospective_single_case, "_build_migration_single_case_intake", None
    )
    original_target_preflight = getattr(
        prospective_single_case, "_preflight_migration_targets", None
    )
    original_staging_root = getattr(
        prospective_single_case, "_create_migration_staging_root", None
    )
    original_read = getattr(prospective_single_case, "_read_bytes_with_authority", None)
    original_write = getattr(
        prospective_single_case, "_write_bytes_with_authority", None
    )
    original_bundle_publish = getattr(
        prospective_single_case, "_publish_bundle_directory_with_authority", None
    )
    original_json_publish = getattr(
        prospective_single_case, "_publish_json_with_authority", None
    )

    def operation_start_authority() -> object:
        nonlocal resolver_calls
        resolver_calls += 1
        if resolver_calls != 1:
            raise AssertionError("migration downstream reacquired repository authority")
        return expected_authority

    def exact(boundary: str, authority: object) -> None:
        assert authority is expected_authority
        observed[boundary].append(authority)

    def bundle_probe(*args: object, authority: object, **kwargs: object) -> dict:
        exact("bundle_files", authority)
        return original_bundle(*args, authority=authority, **kwargs)

    def frozen_probe(*args: object, authority: object, **kwargs: object) -> dict:
        exact("bundle_verification", authority)
        return original_frozen(*args, authority=authority, **kwargs)

    def bundle_files_probe(
        *args: object, authority: object, **kwargs: object
    ) -> tuple[dict[str, bytes], dict, dict]:
        exact("bundle_files", authority)
        return original_bundle_files(*args, authority=authority, **kwargs)

    def parent_probe(
        *args: object, authority: object, **kwargs: object
    ) -> dict[str, object]:
        exact("published_parent", authority)
        return original_parent(*args, authority=authority, **kwargs)

    def verify_probe(*args: object, authority: object, **kwargs: object) -> dict:
        exact("bundle_verification", authority)
        return original_verify(*args, authority=authority, **kwargs)

    def case_directory_probe(case_dir: Path, *, authority: object) -> Path:
        exact("case_directory", authority)
        assert original_case_directory is not None
        return original_case_directory(case_dir, authority=authority)

    def clean_scan_probe(
        case_dir: Path, *, previous_version: int, authority: object
    ) -> None:
        exact("clean_scan", authority)
        assert original_clean_scan is not None
        original_clean_scan(
            case_dir, previous_version=previous_version, authority=authority
        )

    def migration_intake_probe(
        *args: object, authority: object, **kwargs: object
    ) -> tuple[dict, dict]:
        exact("migration_intake", authority)
        assert original_migration_intake is not None
        return original_migration_intake(*args, authority=authority, **kwargs)

    def target_preflight_probe(targets: dict[str, Path], *, authority: object) -> None:
        exact("target_preflight", authority)
        assert original_target_preflight is not None
        original_target_preflight(targets, authority=authority)

    def staging_root_probe(case_dir: Path, *, version: int, authority: object) -> Path:
        exact("staging_root", authority)
        assert original_staging_root is not None
        return original_staging_root(case_dir, version=version, authority=authority)

    def read_probe(path: Path, *, authority: object, description: str) -> bytes:
        exact("source_read", authority)
        assert original_read is not None
        return original_read(path, authority=authority, description=description)

    def write_probe(
        path: Path, content: bytes, *, authority: object, description: str
    ) -> None:
        boundary = (
            "temporary_bundle_write" if ".b." in path.as_posix() else "staging_write"
        )
        exact(boundary, authority)
        assert original_write is not None
        original_write(path, content, authority=authority, description=description)

    def bundle_publication_probe(
        temporary: Path, target: Path, *, authority: object
    ) -> None:
        exact("bundle_publication", authority)
        assert original_bundle_publish is not None
        original_bundle_publish(temporary, target, authority=authority)

    def json_publication_probe(
        path: Path,
        payload: dict,
        *,
        authority: object,
        dry_run: bool,
    ) -> object:
        exact("json_publication", authority)
        assert original_json_publish is not None
        return original_json_publish(
            path, payload, authority=authority, dry_run=dry_run
        )

    monkeypatch.setattr(
        prospective_single_case, "_repository_authority", operation_start_authority
    )
    monkeypatch.setattr(
        prospective_single_case,
        "_prepare_single_case_blind_bundle_with_authority",
        bundle_probe,
    )
    monkeypatch.setattr(
        prospective_single_case,
        "_build_single_case_staged_frozen_run_with_authority",
        frozen_probe,
    )
    monkeypatch.setattr(
        prospective_single_case, "_single_bundle_files", bundle_files_probe
    )
    monkeypatch.setattr(prospective_single_case, "_validated_disk_parent", parent_probe)
    monkeypatch.setattr(
        prospective_single_case, "verify_single_case_bundle", verify_probe
    )
    monkeypatch.setattr(
        prospective_single_case,
        "_authenticate_migration_case_directory",
        case_directory_probe,
        raising=False,
    )
    monkeypatch.setattr(
        prospective_single_case,
        "_assert_migration_paths_clean",
        clean_scan_probe,
    )
    monkeypatch.setattr(
        prospective_single_case,
        "_build_migration_single_case_intake",
        migration_intake_probe,
        raising=False,
    )
    monkeypatch.setattr(
        prospective_single_case,
        "_preflight_migration_targets",
        target_preflight_probe,
        raising=False,
    )
    monkeypatch.setattr(
        prospective_single_case,
        "_create_migration_staging_root",
        staging_root_probe,
        raising=False,
    )
    monkeypatch.setattr(
        prospective_single_case, "_read_bytes_with_authority", read_probe, raising=False
    )
    monkeypatch.setattr(
        prospective_single_case,
        "_write_bytes_with_authority",
        write_probe,
        raising=False,
    )
    monkeypatch.setattr(
        prospective_single_case,
        "_publish_bundle_directory_with_authority",
        bundle_publication_probe,
        raising=False,
    )
    monkeypatch.setattr(
        prospective_single_case,
        "_publish_json_with_authority",
        json_publication_probe,
        raising=False,
    )

    admitted_tasks = tmp_path / "META" / TASKS.name
    admitted_rules = tmp_path / "META" / RULES.name
    admitted_tasks.parent.mkdir(parents=True, exist_ok=True)
    admitted_tasks.write_bytes(TASKS.read_bytes())
    admitted_rules.write_bytes(RULES.read_bytes())

    plan = prospective_single_case.prepare_parent_chain_v002_migration(
        input_file=tmp_path / "source" / intake["case_id"] / "input.md",
        tasks_path=admitted_tasks,
        rule_snapshot_path=admitted_rules,
        tasks_by_case={"P-GO-2026-001": ["career.role_change", "career.change_window"]},
        future_question_draft={
            key: value
            for key, value in question.items()
            if key
            in {
                "future_task_id",
                "question_text_redacted",
                "outcome_type",
                "positive_definition",
                "negative_definition",
                "verification_source_requirements",
                "observation_window",
            }
        },
        case_root=tmp_path / "parents",
        operator="human-test",
        approved_by="human-approver-01",
        reason="Approved whole parent-chain revision before first formal freeze",
        transaction_started_at="2026-07-17T05:39:59.999997Z",
        freeze_at="2026-07-17T05:40:00Z",
        executed_at="2026-07-17T05:40:30Z",
        dry_run=False,
    )

    assert plan["status"] == "PUBLISHED"
    assert resolver_calls == 1
    assert all(observed.values()), observed
    assert all(
        authority is expected_authority
        for authorities in observed.values()
        for authority in authorities
    )


def test_migration_intake_outside_authority_fails_before_source_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = prospective_artifacts._repository_authority()
    outside = (
        tmp_path.parent
        / "outside-authority"
        / "P-GO-2026-999-乾-甲子乙丑丙寅丁卯"
        / "input.md"
    )
    reads = 0

    def forbidden_read(self: Path) -> bytes:
        nonlocal reads
        reads += 1
        raise AssertionError("outside-root migration input was read")

    monkeypatch.setattr(Path, "read_bytes", forbidden_read)

    with pytest.raises(ValueError, match="PATH_OUTSIDE_ROOT"):
        prospective_single_case._build_migration_single_case_intake(
            outside,
            {"tasks": []},
            "human-test",
            {},
            {},
            authority=authority,
            created_at="2026-07-17T05:39:59.999998Z",
            question_created_at="2026-07-17T05:39:59.999997Z",
            case_root=tmp_path / "parents",
            version=2,
            question_revision={},
            intake_revision={},
        )

    assert reads == 0


def test_v002_migration_cannot_bypass_existing_formal_v001_frozen_run(
    tmp_path: Path,
) -> None:
    root, _, _, _ = _v002_single_case_bundle(tmp_path)
    v001_manifest = _read(
        root.with_name(root.name.replace("v002", "v001")) / "bundle-manifest.json"
    )

    with pytest.raises(
        (ContaminationError, ValueError), match="latest|frozen|supersedes|parent"
    ):
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
    tmp_path: Path,
    executed_at: str,
    accepted: bool,
) -> None:
    root, _, _ = _single_case_bundle(
        tmp_path,
        created_at="2026-07-17T05:39:58Z",
        freeze_at="2026-07-17T05:40:00Z",
    )

    if not accepted:
        with pytest.raises(
            (ContaminationError, ValueError), match="executed_at|60|freeze"
        ):
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


def test_v002_single_case_cli_dry_run_and_formal_publish_are_create_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root, _, _, v001_frozen = _v002_single_case_bundle(tmp_path)
    output = single_case_artifact_path(
        tmp_path.absolute(), v001_frozen["case_id"], "frozen-run", 2
    )
    command = [
        sys.executable,
        "-m",
        "tools.school_capability_prospective",
        "stage-single-case-frozen-run",
        "--bundle-root",
        str(root),
        "--out",
        str(output),
        "--now-utc",
        "2026-07-17T05:40:00Z",
        "--supersedes",
        v001_frozen["artifact_path"],
        "--supersedes-sha256",
        v001_frozen["artifact_sha256"],
        "--reason",
        "Freeze revised registration and blind bundle",
        "--approved-by",
        "human-approver-01",
    ]

    cli_args = [command[3], *command[4:]]
    monkeypatch.setattr(
        sys, "argv", ["school-capability-prospective", *cli_args, "--dry-run"]
    )
    assert prospective.main() == 0
    dry = capsys.readouterr()
    assert not output.exists()
    assert json.loads(dry.out)["executed_at"] == "2026-07-17T05:40:00Z"

    monkeypatch.setattr(sys, "argv", ["school-capability-prospective", *cli_args])
    assert prospective.main() == 0
    capsys.readouterr()
    original = output.read_bytes()
    with pytest.raises(ValueError, match="already exists"):
        prospective.main()
    assert output.read_bytes() == original
