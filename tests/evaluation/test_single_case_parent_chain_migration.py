from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

import engine.evaluation.prospective_artifacts as prospective_artifacts
from engine.evaluation.prospective_artifacts import publish_new_json
from engine.evaluation.prospective_single_case import SIX_SCHOOLS
import engine.evaluation.prospective_single_case as migration_module
from tools.school_capability_prospective import build_witness_freeze_registry


CASE_ID = "P-GO-2026-001-乾-甲子乙丑丙寅丁卯"
TASKS = Path("META/prospective-go-task-catalog-v1.json")
RULES = Path("META/prospective-go-rule-snapshot-v1.json")
FREEZE_AT = "2026-07-17T05:40:00Z"
_CONTRACT = Path(
    ".omo/drafts/"
    "w2-c4-governance-promotion-remediation-r3-"
    "admission-contract-2026-08-08.md"
)


@pytest.fixture(autouse=True)
def _repository_authority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path.absolute()
    anchors = {
        Path("META/project-state.json"): Path("META/project-state.json"),
        _CONTRACT: _CONTRACT,
        Path("META/prospective-go-task-catalog-v1.json"): TASKS,
        Path("META/prospective-go-rule-snapshot-v1.json"): RULES,
    }
    for relative, source in anchors.items():
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        expected = source.read_bytes()
        destination.write_bytes(expected)
        assert destination.read_bytes() == expected

    monkeypatch.setattr(prospective_artifacts, "_trusted_repository_root", lambda: root)
    monkeypatch.setattr(
        sys.modules[__name__],
        "TASKS",
        root / "META/prospective-go-task-catalog-v1.json",
    )
    monkeypatch.setattr(
        sys.modules[__name__],
        "RULES",
        root / "META/prospective-go-rule-snapshot-v1.json",
    )

    seam = root / "test-authority-seam"
    seam.mkdir()
    (seam / "sitecustomize.py").write_text(
        "from pathlib import Path\n"
        "import engine.evaluation.prospective_artifacts as artifacts\n"
        f"_ROOT = Path({str(root)!r})\n"
        "artifacts._trusted_repository_root = lambda: _ROOT\n",
        encoding="utf-8",
    )
    inherited = os.environ.get("PYTHONPATH")
    import_roots = [str(seam), str(Path.cwd().absolute())]
    if inherited:
        import_roots.append(inherited)
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join(import_roots))


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _input(root: Path) -> Path:
    path = root / "source" / CASE_ID / "input.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "Sex:乾\n$FOUR\nY:比肩,甲,子,正印\nM:劫财,乙,丑,正财\n"
        "D:元男,丙,寅,偏印\nH:伤官,丁,卯,正印\n$DY_LOOP\n"
        "#2026,8岁,戊辰,食神\n> 2026,丙午,食神\n",
        encoding="utf-8",
    )
    return path


def _question_draft(root: Path) -> Path:
    path = root / "question-v002.json"
    path.write_text(
        json.dumps(
            {
                "future_task_id": "career.role_change",
                "question_text_redacted": "未来三个月是否发生显著岗位角色变化？",
                "outcome_type": "binary",
                "positive_definition": "发生并有雇佣资料或本人确认",
                "negative_definition": "完整窗口结束且核验来源确认未发生",
                "verification_source_requirements": ["custody://structured-interview"],
                "observation_window": {
                    "start_at": "IGNORED-BY-MIGRATION",
                    "end_at": "IGNORED-BY-MIGRATION",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def _v001_chain(root: Path) -> dict[str, Path | dict]:
    from engine.evaluation.prospective_single_case import (
        build_single_case_intake,
        prepare_single_case_blind_bundle,
    )

    input_path = _input(root)
    draft = _read(_question_draft(root))
    draft["observation_window"] = {
        "start_at": "2026-07-17T05:30:00Z",
        "end_at": "2026-10-17T05:30:00Z",
    }
    intake, question = build_single_case_intake(
        input_path,
        _read(TASKS),
        SIX_SCHOOLS,
        "human-test",
        {"P-GO-2026-001": ["career.role_change", "career.change_window"]},
        draft,
        created_at="2026-07-17T05:29:58Z",
        case_root=root,
    )
    publish_new_json(Path(question["artifact_path"]), question, dry_run=False)
    publish_new_json(Path(intake["artifact_path"]), intake, dry_run=False)
    bundle_root = Path(intake["artifact_path"]).with_name(
        f"{CASE_ID}--blind-bundle--v001"
    )
    manifest = prepare_single_case_blind_bundle(
        intake,
        question,
        TASKS,
        RULES,
        bundle_root,
        dry_run=False,
    )
    return {
        "input_path": input_path,
        "question": question,
        "intake": intake,
        "bundle_root": bundle_root,
        "manifest": manifest,
        "formal_root": root,
    }


def _migration_kwargs(root: Path, chain: dict[str, Path | dict]) -> dict:
    return {
        "input_file": chain["input_path"],
        "tasks_path": TASKS,
        "rule_snapshot_path": RULES,
        "tasks_by_case": {
            "P-GO-2026-001": ["career.role_change", "career.change_window"]
        },
        "future_question_draft": _read(_question_draft(root)),
        "case_root": chain["formal_root"],
        "operator": "human-test",
        "approved_by": "human-approver-01",
        "reason": "Approved whole parent-chain revision before first formal freeze",
        "transaction_started_at": "2026-07-17T05:39:59.999997Z",
        "freeze_at": FREEZE_AT,
        "executed_at": "2026-07-17T05:40:30Z",
        "dry_run": True,
    }


def test_migration_dry_run_plans_four_v002_artifacts_without_formal_writes(
    tmp_path: Path,
) -> None:
    chain = _v001_chain(tmp_path)

    plan = migration_module.prepare_parent_chain_v002_migration(
        **_migration_kwargs(tmp_path, chain)
    )

    assert plan["status"] == "DRY_RUN"
    assert plan["publication_order"] == [
        "future_question",
        "intake",
        "blind_bundle",
        "frozen_run",
    ]
    assert plan["freeze_at"] == FREEZE_AT
    documents = plan["artifacts"]
    assert documents["future_question"]["observation_window"]["start_at"] == FREEZE_AT
    assert documents["frozen_run"]["freeze_at"] == FREEZE_AT
    assert documents["frozen_run"]["frozen_run"]["frozen_at"] == FREEZE_AT
    assert documents["frozen_run"]["executed_at"] == "2026-07-17T05:40:30Z"
    assert (
        documents["future_question"]["supersedes"] == chain["question"]["artifact_path"]
    )
    assert documents["intake"]["supersedes"] == chain["intake"]["artifact_path"]
    assert documents["blind_bundle"]["supersedes"] == chain["manifest"]["artifact_path"]
    assert documents["frozen_run"]["supersedes"] == chain["manifest"]["artifact_path"]
    for artifact in documents.values():
        assert not Path(artifact["artifact_path"]).exists()


@pytest.mark.parametrize(
    "forbidden_kind",
    [
        "frozen-run",
        "witness-registry",
        "verification",
        "feedback",
        "retrospective",
        "observation",
        "report",
        "label",
        "reveal",
    ],
)
def test_migration_fails_closed_on_forbidden_artifact_path_without_reading_it(
    tmp_path: Path,
    forbidden_kind: str,
) -> None:
    chain = _v001_chain(tmp_path)
    case_dir = Path(chain["formal_root"]) / CASE_ID
    forbidden = case_dir / f"{CASE_ID}--{forbidden_kind}--v001.json"
    forbidden.write_bytes(b"not-json-and-must-not-be-read")

    with pytest.raises(ValueError, match="forbidden|STOP|HOLD"):
        migration_module.prepare_parent_chain_v002_migration(
            **_migration_kwargs(tmp_path, chain)
        )


def test_formal_migration_preflights_all_targets_and_refuses_partial_start(
    tmp_path: Path,
) -> None:
    chain = _v001_chain(tmp_path)
    kwargs = _migration_kwargs(tmp_path, chain)
    kwargs["dry_run"] = False
    existing_target = (
        Path(chain["formal_root"]) / CASE_ID / f"{CASE_ID}--intake--v002.json"
    )
    existing_target.write_text('{"preexisting":true}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="must not exist|already exists"):
        migration_module.prepare_parent_chain_v002_migration(**kwargs)

    question_target = existing_target.with_name(
        f"{CASE_ID}--future-question-registration--v002.json"
    )
    bundle_target = existing_target.with_name(f"{CASE_ID}--blind-bundle--v002")
    frozen_target = existing_target.with_name(f"{CASE_ID}--frozen-run--v002.json")
    assert not question_target.exists()
    assert not bundle_target.exists()
    assert not frozen_target.exists()


def test_formal_migration_publishes_frozen_refs_matching_actual_bundle(
    tmp_path: Path,
) -> None:
    chain = _v001_chain(tmp_path)
    kwargs = _migration_kwargs(tmp_path, chain)
    kwargs["dry_run"] = False

    plan = migration_module.prepare_parent_chain_v002_migration(**kwargs)

    manifest_path = Path(plan["artifacts"]["blind_bundle"]["artifact_path"])
    frozen_path = (
        Path(chain["formal_root"]) / CASE_ID / f"{CASE_ID}--frozen-run--v002.json"
    )
    manifest = _read(manifest_path)
    frozen = _read(frozen_path)
    assert frozen["bundle_sha256"] == manifest["bundle_sha256"]
    assert frozen["bundle_manifest_sha256"] == manifest["artifact_sha256"]
    assert frozen["parents"][-1] == {
        "artifact_path": manifest["artifact_path"],
        "artifact_sha256": manifest["artifact_sha256"],
    }


def test_formal_migration_leaves_strict_witness_event_room_within_transaction_window(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chain = _v001_chain(tmp_path)
    transaction_started_at = datetime.fromisoformat("2026-07-17T05:39:59.999997+00:00")

    class TransactionClock(datetime):
        @classmethod
        def now(cls, tz: timezone | None = None) -> datetime:
            return transaction_started_at

    monkeypatch.setattr(migration_module, "datetime", TransactionClock)
    kwargs = _migration_kwargs(tmp_path, chain)
    kwargs["transaction_started_at"] = transaction_started_at.isoformat().replace(
        "+00:00", "Z"
    )
    kwargs["dry_run"] = False
    plan = migration_module.prepare_parent_chain_v002_migration(**kwargs)
    documents = plan["artifacts"]

    registry = build_witness_freeze_registry(
        Path(documents["intake"]["artifact_path"]),
        Path(documents["blind_bundle"]["artifact_path"]).parent,
        Path(chain["formal_root"]) / CASE_ID / f"{CASE_ID}--frozen-run--v002.json",
        b"TEST-PROCESS-ONLY-WITNESS-KEY-NOT-REAL",
    )

    event_times = [
        datetime.fromisoformat(event["occurred_at"].replace("Z", "+00:00"))
        for event in registry["events"]
    ]
    question_at = datetime.fromisoformat(
        documents["future_question"]["created_at"].replace("Z", "+00:00")
    )
    intake_at = datetime.fromisoformat(
        documents["intake"]["created_at"].replace("Z", "+00:00")
    )
    bundle_at = datetime.fromisoformat(
        documents["blind_bundle"]["created_at"].replace("Z", "+00:00")
    )
    freeze_at = datetime.fromisoformat(plan["freeze_at"].replace("Z", "+00:00"))
    executed_at = datetime.fromisoformat(
        documents["frozen_run"]["executed_at"].replace("Z", "+00:00")
    )
    assert transaction_started_at == question_at < intake_at < bundle_at < freeze_at
    assert event_times[0] == intake_at < event_times[1] < event_times[2] == freeze_at
    assert freeze_at <= executed_at
    assert 0 <= (executed_at - freeze_at).total_seconds() <= 60


def test_dry_run_artifacts_equal_fixed_time_formal_publication(tmp_path: Path) -> None:
    chain = _v001_chain(tmp_path)
    kwargs = _migration_kwargs(tmp_path, chain)

    dry_plan = migration_module.prepare_parent_chain_v002_migration(**kwargs)
    kwargs["dry_run"] = False
    formal_plan = migration_module.prepare_parent_chain_v002_migration(**kwargs)

    mismatches = []
    for kind, dry_artifact in dry_plan["artifacts"].items():
        formal_artifact = formal_plan["artifacts"][kind]
        formal_path = (
            Path(chain["formal_root"]) / CASE_ID / f"{CASE_ID}--frozen-run--v002.json"
            if kind == "frozen_run"
            else Path(formal_artifact["artifact_path"])
        )
        disk_artifact = _read(formal_path)
        if dry_artifact != formal_artifact or dry_artifact != disk_artifact:
            mismatches.append(kind)
    assert mismatches == []


def test_formal_migration_failure_keeps_published_items_and_reports_recoverable_hold(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chain = _v001_chain(tmp_path)
    kwargs = _migration_kwargs(tmp_path, chain)
    kwargs["dry_run"] = False
    import engine.evaluation.prospective_single_case as module

    real_publish = module._publish_json_with_authority
    calls = 0

    def fail_second(path: Path, payload: dict, *, authority: object, dry_run: bool):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected publish failure")
        return real_publish(path, payload, authority=authority, dry_run=dry_run)

    monkeypatch.setattr(module, "_publish_json_with_authority", fail_second)

    with pytest.raises(ValueError, match="RECOVERABLE_HOLD"):
        migration_module.prepare_parent_chain_v002_migration(**kwargs)

    case_dir = Path(chain["formal_root"]) / CASE_ID
    assert (case_dir / f"{CASE_ID}--future-question-registration--v002.json").exists()
    assert not (case_dir / f"{CASE_ID}--intake--v002.json").exists()
    assert not (case_dir / f"{CASE_ID}--blind-bundle--v002").exists()
    assert not (case_dir / f"{CASE_ID}--frozen-run--v002.json").exists()


def test_v003_dry_run_recovers_from_failed_v002_boundary_without_changing_v002(
    tmp_path: Path,
) -> None:
    chain = _v001_chain(tmp_path)
    publish_kwargs = _migration_kwargs(tmp_path, chain)
    publish_kwargs["dry_run"] = False
    v002_plan = migration_module.prepare_parent_chain_v002_migration(**publish_kwargs)
    v002_paths = [
        Path(v002_plan["artifacts"]["future_question"]["artifact_path"]),
        Path(v002_plan["artifacts"]["intake"]["artifact_path"]),
        Path(v002_plan["artifacts"]["blind_bundle"]["artifact_path"]),
        Path(chain["formal_root"]) / CASE_ID / f"{CASE_ID}--frozen-run--v002.json",
    ]
    v002_before = {path: path.read_bytes() for path in v002_paths}

    kwargs = _migration_kwargs(tmp_path, chain)
    kwargs["next_version"] = 3
    plan = migration_module.prepare_parent_chain_v002_migration(**kwargs)

    assert plan["status"] == "DRY_RUN"
    assert all(
        "--v003" in artifact["artifact_path"] for artifact in plan["artifacts"].values()
    )
    assert (
        plan["artifacts"]["future_question"]["supersedes"] == v002_paths[0].as_posix()
    )
    assert plan["artifacts"]["intake"]["supersedes"] == v002_paths[1].as_posix()
    assert plan["artifacts"]["blind_bundle"]["supersedes"] == v002_paths[2].as_posix()
    assert plan["artifacts"]["frozen_run"]["supersedes"] == v002_paths[2].as_posix()
    assert all(path.read_bytes() == v002_before[path] for path in v002_paths)
    assert all(
        not Path(artifact["artifact_path"]).exists()
        for artifact in plan["artifacts"].values()
    )


def test_migration_cli_help_and_dry_run_sample_one_timestamp_without_writes(
    tmp_path: Path,
) -> None:
    chain = _v001_chain(tmp_path)
    assignments = tmp_path / "assignments.json"
    assignments.write_text(
        json.dumps(
            {
                "P-GO-2026-001": ["career.role_change", "career.change_window"],
            }
        ),
        encoding="utf-8",
    )
    command = [
        sys.executable,
        "-m",
        "tools.school_capability_prospective",
        "migrate-single-case-parent-chain-v002",
        "--input",
        str(chain["input_path"]),
        "--tasks",
        str(TASKS),
        "--rule-snapshot",
        str(RULES),
        "--tasks-by-case",
        str(assignments),
        "--future-question",
        str(_question_draft(tmp_path)),
        "--case-root",
        str(chain["formal_root"]),
        "--operator",
        "human-test",
        "--approved-by",
        "human-approver-01",
        "--reason",
        "Approved whole parent-chain revision before first formal freeze",
        "--next-version",
        "2",
        "--dry-run",
    ]

    result = subprocess.run(command, check=False, capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
    plan = json.loads(result.stdout)
    assert (
        plan["freeze_at"]
        == plan["artifacts"]["future_question"]["observation_window"]["start_at"]
    )
    assert (
        plan["freeze_at"] == plan["artifacts"]["frozen_run"]["frozen_run"]["frozen_at"]
    )
    assert (
        "--next-version"
        in subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.school_capability_prospective",
                "migrate-single-case-parent-chain-v002",
                "--help",
            ],
            check=False,
            capture_output=True,
            text=True,
        ).stdout
    )
    for artifact in plan["artifacts"].values():
        assert not Path(artifact["artifact_path"]).exists()
