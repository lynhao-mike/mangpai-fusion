from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

import engine.evaluation.prospective_artifacts as prospective_artifacts
from engine.evaluation.prospective_artifacts import (
    canonical_artifact_sha256,
    publish_new_json,
    validate_revision_metadata,
)
from engine.evaluation.prospective_single_case import (
    SIX_SCHOOLS,
    ContaminationError,
    build_single_case_intake,
    prepare_single_case_blind_bundle,
    validate_future_question_registration,
    validate_single_case_intake,
    verify_single_case_bundle,
)


CASE_ID = "P-GO-2026-001-乾-甲子乙丑丙寅丁卯"
CREATED_AT = "2026-07-16T00:00:00Z"
TASK_CATALOG = Path("META/prospective-go-task-catalog-v1.json")
_CONTRACT = Path(
    ".omo/drafts/"
    "w2-c4-governance-promotion-remediation-r3-"
    "admission-contract-2026-08-08.md"
)
_RULE_SNAPSHOT = Path("META/prospective-go-rule-snapshot-v1.json")


@pytest.fixture(autouse=True)
def _repository_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path.absolute()
    anchors = {
        Path("META/project-state.json"): Path("META/project-state.json"),
        _CONTRACT: _CONTRACT,
        Path("META/prospective-go-task-catalog-v1.json"): TASK_CATALOG,
        Path("META/prospective-go-rule-snapshot-v1.json"): _RULE_SNAPSHOT,
    }
    for relative, source in anchors.items():
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        expected = source.read_bytes()
        destination.write_bytes(expected)
        assert destination.read_bytes() == expected

    monkeypatch.setattr(
        prospective_artifacts, "_trusted_repository_root", lambda: root
    )
    monkeypatch.setattr(
        sys.modules[__name__],
        "TASK_CATALOG",
        root / "META/prospective-go-task-catalog-v1.json",
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


def _tasks() -> dict[str, object]:
    return json.loads(TASK_CATALOG.read_text(encoding="utf-8"))


def _input(tmp_path: Path, *, case_id: str = CASE_ID, extra: str = "") -> Path:
    path = tmp_path / case_id / "input.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "四柱：甲子 乙丑 丙寅 丁卯\n性别：乾\n" + extra,
        encoding="utf-8",
    )
    return path


def _question(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "future_task_id": "career.role_change",
        "question_text_redacted": "未来三个月是否发生显著岗位角色变化？",
        "outcome_type": "binary",
        "positive_definition": "发生并有雇佣资料或本人确认",
        "negative_definition": "完整窗口结束且核验来源确认未发生",
        "verification_source_requirements": ["custody://structured-interview"],
        "observation_window": {
            "start_at": CREATED_AT,
            "end_at": "2026-10-16T00:00:00Z",
        },
    }
    value.update(overrides)
    return value


def _build(tmp_path: Path, **overrides: object) -> tuple[dict[str, object], dict[str, object]]:
    values: dict[str, object] = {
        "input_file": _input(tmp_path),
        "tasks": _tasks(),
        "schools": SIX_SCHOOLS,
        "operator": "human-intake-01",
        "tasks_by_case": {"P-GO-2026-001": ["career.role_change", "career.change_window"]},
        "future_question": _question(),
        "created_at": CREATED_AT,
        "case_root": tmp_path / "published",
    }
    values.update(overrides)
    return build_single_case_intake(**values)  # type: ignore[arg-type]


def test_single_intake_has_one_record_six_schools_and_real_question_ref(tmp_path: Path) -> None:
    intake, question = _build(tmp_path)

    expected_path = (
        tmp_path
        / "published"
        / CASE_ID
        / f"{CASE_ID}--future-question-registration--v001.json"
    )
    assert len(intake["records"]) == 1
    assert intake["schools"] == list(SIX_SCHOOLS)
    assert intake["future_question"] == {
        "artifact_path": expected_path.as_posix(),
        "artifact_sha256": question["artifact_sha256"],
    }
    assert intake["parents"] == [intake["future_question"]]
    assert question["artifact_path"] == expected_path.as_posix()
    assert question["future_task_id"] == "career.role_change"


@pytest.mark.parametrize("questions", [[], [_question(), _question()]])
def test_single_intake_rejects_question_count_not_one(
    tmp_path: Path, questions: list[dict[str, object]],
) -> None:
    with pytest.raises(ValueError, match="exactly one future question"):
        _build(tmp_path, future_question=questions)


def test_single_intake_requires_exact_six_schools_and_does_not_guess_question(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="exactly six schools"):
        _build(tmp_path, schools=SIX_SCHOOLS[:-1])
    with pytest.raises(ValueError, match="exactly one future question"):
        _build(tmp_path, future_question=None)


def test_single_intake_rejects_existing_subject_hash_across_case(tmp_path: Path) -> None:
    intake, _ = _build(tmp_path / "first")
    subject_hash = intake["subject_id_hash"]
    changed_case = "P-GO-2026-002-乾-甲子乙丑丙寅丁卯"

    with pytest.raises(ValueError, match="duplicate subject_id_hash"):
        _build(
            tmp_path / "second",
            input_file=_input(tmp_path / "second", case_id=changed_case),
            tasks_by_case={"P-GO-2026-002": ["career.role_change"]},
            existing_subject_hashes={subject_hash},
        )


def test_forbidden_marker_is_rejected_before_any_publication(tmp_path: Path) -> None:
    root = tmp_path / "published"
    with pytest.raises(ValueError, match="forbidden"):
        _build(
            tmp_path,
            case_root=root,
            future_question=_question(question_text_redacted="根据 feedback 判断是否升职"),
        )
    assert not root.exists()


def test_forbidden_marker_does_not_reject_non_leakage_report_substring(tmp_path: Path) -> None:
    _, question = _build(
        tmp_path,
        future_question=_question(
            verification_source_requirements=["custody://self-reported-employment-record"],
        ),
    )

    assert question["verification_source_requirements"] == [
        "custody://self-reported-employment-record"
    ]


def test_frozen_ten_slots_only_map_arrived_case_and_do_not_become_records(tmp_path: Path) -> None:
    assignments = json.loads(
        Path("META/prospective-go/prospective-go-b01-tasks-by-case.json").read_text(encoding="utf-8")
    )
    intake, _ = _build(tmp_path, tasks_by_case=assignments)

    assert [row["case_id"] for row in intake["records"]] == [CASE_ID]
    assert intake["records"][0]["task_ids"] == sorted(assignments["P-GO-2026-001"])


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"outcome_type": "ordinal"}, "binary"),
        ({"positive_definition": ""}, "positive_definition"),
        ({"negative_definition": "  "}, "negative_definition"),
        ({"verification_source_requirements": []}, "source requirements"),
        ({"verification_source_requirements": [""]}, "source requirements"),
        ({"observation_window": {"start_at": "2026-07-16", "end_at": "2026-07-17T00:00:00Z"}}, "UTC"),
        ({"observation_window": {"start_at": CREATED_AT, "end_at": CREATED_AT}}, "later"),
        ({"observation_window": {"start_at": CREATED_AT, "end_at": "2026-10-16T00:00:01Z"}}, "three calendar months"),
    ],
)
def test_future_question_validation_rejects_invalid_contract(
    tmp_path: Path, mutation: dict[str, object], message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        _build(tmp_path, future_question=_question(**mutation))


def test_future_question_freeze_binding_requires_same_start_and_three_month_limit(tmp_path: Path) -> None:
    _, question = _build(tmp_path)
    validated = validate_future_question_registration(question, freeze_at=CREATED_AT)
    assert validated == question

    with pytest.raises(ValueError, match="start_at must equal freeze_at"):
        validate_future_question_registration(question, freeze_at="2026-07-16T00:00:01Z")


def test_future_question_planned_freeze_cannot_predate_registration(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="start_at must not predate created_at"):
        _build(
            tmp_path,
            created_at="2026-07-16T00:00:01Z",
            future_question=_question(),
        )


@pytest.mark.parametrize(
    ("start_at", "end_at"),
    [
        ("2026-01-31T12:00:00Z", "2026-04-30T12:00:00Z"),
        ("2023-11-30T12:00:00Z", "2024-02-29T12:00:00Z"),
        ("2024-11-30T12:00:00Z", "2025-02-28T12:00:00Z"),
    ],
)
def test_three_calendar_month_limit_clamps_month_end_and_leap_year(
    tmp_path: Path, start_at: str, end_at: str,
) -> None:
    _, question = _build(
        tmp_path,
        created_at=start_at,
        future_question=_question(
            observation_window={"start_at": start_at, "end_at": end_at},
        ),
    )

    assert question["observation_window"] == {"start_at": start_at, "end_at": end_at}

    with pytest.raises(ValueError, match="three calendar months"):
        _build(
            tmp_path / "late",
            created_at=start_at,
            future_question=_question(
                observation_window={
                    "start_at": start_at,
                    "end_at": end_at.replace("00Z", "01Z"),
                },
            ),
        )


def test_future_question_digest_and_timestamps_are_canonical(tmp_path: Path) -> None:
    _, question = _build(tmp_path)

    assert question["created_at"] == CREATED_AT
    assert datetime.fromisoformat(str(question["created_at"]).replace("Z", "+00:00")).tzinfo == timezone.utc
    assert question["artifact_sha256"] == canonical_artifact_sha256(question)


def test_v002_intake_and_question_require_and_bind_distinct_superseded_parents(
    tmp_path: Path,
) -> None:
    v001_intake, v001_question = _build(tmp_path)
    publish_new_json(Path(v001_question["artifact_path"]), v001_question, dry_run=False)
    publish_new_json(Path(v001_intake["artifact_path"]), v001_intake, dry_run=False)
    freeze_at = "2026-07-17T05:30:00Z"

    v002_intake, v002_question = _build(
        tmp_path,
        version=2,
        created_at="2026-07-17T05:29:58Z",
        future_question=_question(observation_window={
            "start_at": freeze_at,
            "end_at": "2026-10-17T05:30:00Z",
        }),
        question_revision={
            "supersedes": v001_question["artifact_path"],
            "supersedes_sha256": v001_question["artifact_sha256"],
            "reason": "Bind observation start to the actual freeze instant",
            "approved_by": "human-approver-01",
        },
        intake_revision={
            "supersedes": v001_intake["artifact_path"],
            "supersedes_sha256": v001_intake["artifact_sha256"],
            "reason": "Bind intake to the corrected future-question registration",
            "approved_by": "human-approver-01",
        },
    )

    assert v002_question["artifact_path"].endswith("--future-question-registration--v002.json")
    assert v002_intake["artifact_path"].endswith("--intake--v002.json")
    validate_revision_metadata(v002_question, 2)
    validate_revision_metadata(v002_intake, 2)
    assert v002_intake["future_question"]["artifact_sha256"] == v002_question["artifact_sha256"]
    assert Path(v001_question["artifact_path"]).read_bytes()
    assert Path(v001_intake["artifact_path"]).read_bytes()


def _write_cli_inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    input_path = _input(tmp_path / "source")
    tasks_path = tmp_path / "tasks.json"
    tasks_path.write_text(json.dumps(_tasks(), ensure_ascii=False), encoding="utf-8")
    assignments_path = tmp_path / "assignments.json"
    assignments_path.write_text(
        json.dumps({"P-GO-2026-001": ["career.role_change"]}, ensure_ascii=False),
        encoding="utf-8",
    )
    question_path = tmp_path / "question-draft.json"
    question_path.write_text(json.dumps(_question(), ensure_ascii=False), encoding="utf-8")
    return input_path, tasks_path, assignments_path, question_path


def _cli_command(tmp_path: Path) -> tuple[list[str], Path]:
    input_path, tasks_path, assignments_path, question_path = _write_cli_inputs(tmp_path)
    root = tmp_path / "published"
    command = [
        sys.executable,
        "-m",
        "tools.school_capability_dataset",
        "single-case-intake",
        "--input",
        str(input_path),
        "--tasks",
        str(tasks_path),
    ]
    for school in SIX_SCHOOLS:
        command.extend(("--school", school))
    command.extend(
        (
            "--operator",
            "human-intake-01",
            "--tasks-by-case",
            str(assignments_path),
            "--future-question",
            str(question_path),
            "--case-root",
            str(root),
            "--created-at",
            CREATED_AT,
        )
    )
    return command, root


def test_single_case_cli_parser_exposes_v002_supersedes_arguments() -> None:
    from tools.school_capability_dataset import _parser

    help_text = _parser().format_help()
    choices = _parser()._subparsers._group_actions[0].choices
    single_help = choices["single-case-intake"].format_help()
    bundle_help = choices["prepare-single-case-blind"].format_help()

    assert "single-case-intake" in help_text
    for option in (
        "--version", "--question-supersedes", "--question-supersedes-sha256",
        "--intake-supersedes", "--intake-supersedes-sha256", "--reason", "--approved-by",
    ):
        assert option in single_help
    for option in (
        "--supersedes", "--supersedes-sha256", "--reason", "--approved-by",
    ):
        assert option in bundle_help


def test_single_case_cli_rejects_existing_subject_under_different_case_id(tmp_path: Path) -> None:
    first_command, root = _cli_command(tmp_path)
    first = subprocess.run(first_command, check=False, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr

    second_case_id = "P-GO-2026-002-乾-甲子乙丑丙寅丁卯"
    input_path = _input(tmp_path / "second-source", case_id=second_case_id)
    assignments_path = tmp_path / "second-assignments.json"
    assignments_path.write_text(
        json.dumps({"P-GO-2026-002": ["career.role_change"]}, ensure_ascii=False),
        encoding="utf-8",
    )
    question_path = tmp_path / "second-question.json"
    question_path.write_text(json.dumps(_question(), ensure_ascii=False), encoding="utf-8")
    command = [
        sys.executable, "-m", "tools.school_capability_dataset", "single-case-intake",
        "--input", str(input_path), "--tasks", str(tmp_path / "tasks.json"),
    ]
    for school in SIX_SCHOOLS:
        command.extend(("--school", school))
    command.extend((
        "--operator", "human-intake-02",
        "--tasks-by-case", str(assignments_path),
        "--future-question", str(question_path),
        "--case-root", str(root),
        "--created-at", CREATED_AT,
        "--dry-run",
    ))

    result = subprocess.run(command, check=False, capture_output=True, text=True)

    assert result.returncode != 0
    assert "duplicate subject_id_hash" in result.stderr
    assert not (root / second_case_id).exists()


def test_single_case_cli_v002_dry_run_does_not_reject_same_case_subject(tmp_path: Path) -> None:
    command, root = _cli_command(tmp_path)
    first = subprocess.run(command, check=False, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    published = json.loads(first.stdout)
    question = published["future_question"]["document"]
    intake = published["intake"]["document"]
    question_draft = Path(command[command.index("--future-question") + 1])
    draft = json.loads(question_draft.read_text(encoding="utf-8"))
    draft["observation_window"] = {
        "start_at": "2026-07-17T05:40:00Z",
        "end_at": "2026-10-17T05:40:00Z",
    }
    question_draft.write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")
    revised = [
        *command[:-1], "2026-07-17T05:39:58Z",
        "--version", "2",
        "--question-supersedes", question["artifact_path"],
        "--question-supersedes-sha256", question["artifact_sha256"],
        "--intake-supersedes", intake["artifact_path"],
        "--intake-supersedes-sha256", intake["artifact_sha256"],
        "--reason", "Bind observation start to actual freeze time",
        "--approved-by", "human-approver-01",
        "--dry-run",
    ]

    result = subprocess.run(revised, check=False, capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["future_question"]["artifact_path"].endswith("--v002.json")
    assert payload["intake"]["artifact_path"].endswith("--v002.json")
    assert not (root / CASE_ID / f"{CASE_ID}--intake--v002.json").exists()


def test_single_case_cli_dry_run_emits_two_documents_and_paths_without_writing(tmp_path: Path) -> None:
    command, root = _cli_command(tmp_path)

    result = subprocess.run([*command, "--dry-run"], check=False, capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["status"] == "DRY_RUN"
    assert output["publication_order"] == ["future_question", "intake"]
    assert output["future_question"]["artifact_path"].endswith("--future-question-registration--v001.json")
    assert output["intake"]["artifact_path"].endswith("--intake--v001.json")
    assert not root.exists()


def test_single_case_cli_formal_is_create_only_in_question_then_intake_order(tmp_path: Path) -> None:
    command, root = _cli_command(tmp_path)

    first = subprocess.run(command, check=False, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    result = json.loads(first.stdout)
    question_path = Path(result["future_question"]["artifact_path"])
    intake_path = Path(result["intake"]["artifact_path"])
    question_bytes = question_path.read_bytes()
    intake_bytes = intake_path.read_bytes()

    second = subprocess.run(command, check=False, capture_output=True, text=True)
    assert second.returncode != 0
    assert question_path.read_bytes() == question_bytes
    assert intake_path.read_bytes() == intake_bytes
    assert root.exists()


def test_cli_recovery_rejects_byte_drift_in_published_question_parent(tmp_path: Path) -> None:
    command, root = _cli_command(tmp_path)
    intake_path = root / CASE_ID / f"{CASE_ID}--intake--v001.json"
    intake_path.parent.mkdir(parents=True)
    intake_path.write_text('{"preexisting":true}\n', encoding="utf-8")
    first = subprocess.run(command, check=False, capture_output=True, text=True)
    assert first.returncode != 0

    question_path = root / CASE_ID / f"{CASE_ID}--future-question-registration--v001.json"
    question = json.loads(question_path.read_text(encoding="utf-8"))
    question_path.write_text(json.dumps(question, ensure_ascii=False), encoding="utf-8")
    intake_path.unlink()

    retry = subprocess.run(command, check=False, capture_output=True, text=True)

    assert retry.returncode != 0
    assert "byte drift" in retry.stderr
    assert not intake_path.exists()


def test_cli_second_publication_failure_keeps_first_artifact_and_reports_auditable_hold(tmp_path: Path) -> None:
    command, root = _cli_command(tmp_path)
    intake_path = root / CASE_ID / f"{CASE_ID}--intake--v001.json"
    intake_path.parent.mkdir(parents=True)
    intake_path.write_text('{"preexisting":true}\n', encoding="utf-8")
    original_intake = intake_path.read_bytes()

    result = subprocess.run(command, check=False, capture_output=True, text=True)

    question_path = root / CASE_ID / f"{CASE_ID}--future-question-registration--v001.json"
    assert result.returncode != 0
    assert question_path.exists()
    assert intake_path.read_bytes() == original_intake
    assert "RECOVERABLE_HOLD" in result.stderr
    assert question_path.as_posix() in result.stderr.replace("\\", "/")

    intake_path.unlink()
    retry = subprocess.run(command, check=False, capture_output=True, text=True)

    assert retry.returncode == 0, retry.stderr
    assert question_path.exists()
    assert intake_path.exists()


def _single_bundle_sources(tmp_path: Path) -> tuple[dict[str, object], dict[str, object], Path, Path]:
    intake, question = _build(tmp_path / "registration")
    publish_new_json(Path(question["artifact_path"]), question, dry_run=False)
    publish_new_json(Path(intake["artifact_path"]), intake, dry_run=False)
    tasks_path = tmp_path / "tasks.json"
    tasks_path.write_text(json.dumps(_tasks(), ensure_ascii=False), encoding="utf-8")
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(
        json.dumps(
            {
                "rule_snapshot_id": "single-case-rules-v1",
                "schools": list(reversed(SIX_SCHOOLS)),
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return intake, question, tasks_path, rules_path


def test_bundle_has_exact_single_case_whitelist_and_manifest_contract(tmp_path: Path) -> None:
    intake, question, tasks_path, rules_path = _single_bundle_sources(tmp_path)
    target = tmp_path / "bundle"

    manifest = prepare_single_case_blind_bundle(
        intake, question, tasks_path, rules_path, target, dry_run=False,
    )

    case_id = str(intake["case_id"])
    expected_files = {
        "intake.json",
        "tasks.json",
        "rule-snapshot.json",
        "future-question.json",
        f"cases/{case_id}/chart.json",
    }
    assert set(manifest["files"]) == expected_files
    assert manifest["case_id"] == intake["case_id"]
    assert manifest["subject_id_hash"] == intake["subject_id_hash"]
    assert manifest["created_at"] >= intake["created_at"]
    assert manifest["artifact_path"] == (target / "bundle-manifest.json").as_posix()
    assert manifest["artifact_sha256"] == canonical_artifact_sha256(manifest)
    assert manifest["case_count"] == 1
    assert manifest["future_question_count"] == 1
    assert manifest["schools"] == sorted(SIX_SCHOOLS)
    assert manifest["parents"] == [
        {
            "artifact_path": intake["artifact_path"],
            "artifact_sha256": intake["artifact_sha256"],
        },
        {
            "artifact_path": question["artifact_path"],
            "artifact_sha256": question["artifact_sha256"],
        },
    ]
    assert {
        path.relative_to(target).as_posix()
        for path in target.rglob("*")
        if path.is_file()
    } == expected_files | {"bundle-manifest.json"}
    verified = verify_single_case_bundle(target)
    assert verified["manifest"] == manifest
    assert verified["chart"]["case_id"] == case_id


@pytest.mark.parametrize("extra", ["feedback.json", "report.md", "known-facts.json", "input.md"])
def test_bundle_extra_revealed_file_is_stop(tmp_path: Path, extra: str) -> None:
    intake, question, tasks_path, rules_path = _single_bundle_sources(tmp_path)
    target = tmp_path / "bundle"
    prepare_single_case_blind_bundle(intake, question, tasks_path, rules_path, target, dry_run=False)
    (target / extra).write_text("revealed", encoding="utf-8")

    with pytest.raises(ContaminationError, match="STOP"):
        verify_single_case_bundle(target)


def test_bundle_extra_empty_directory_is_stop(tmp_path: Path) -> None:
    intake, question, tasks_path, rules_path = _single_bundle_sources(tmp_path)
    target = tmp_path / "bundle"
    prepare_single_case_blind_bundle(intake, question, tasks_path, rules_path, target, dry_run=False)
    (target / "cases" / "unexpected" / "nested").mkdir(parents=True)

    with pytest.raises(ContaminationError, match="STOP"):
        verify_single_case_bundle(target)


def test_single_case_bundle_rejects_multiple_intake_records(tmp_path: Path) -> None:
    intake, question, tasks_path, rules_path = _single_bundle_sources(tmp_path)
    intake["records"] = [intake["records"][0], dict(intake["records"][0])]
    intake["artifact_sha256"] = canonical_artifact_sha256(intake)

    with pytest.raises(ContaminationError, match="exactly one record"):
        prepare_single_case_blind_bundle(
            intake, question, tasks_path, rules_path, tmp_path / "bundle", dry_run=True,
        )


def test_single_case_bundle_rejects_future_question_parent_mismatch(tmp_path: Path) -> None:
    intake, question, tasks_path, rules_path = _single_bundle_sources(tmp_path)
    changed = dict(question)
    changed["case_id"] = "P-GO-2026-002-乾-甲子乙丑丙寅丁卯"
    changed["artifact_sha256"] = canonical_artifact_sha256(changed)

    with pytest.raises(ContaminationError, match="parent mismatch"):
        prepare_single_case_blind_bundle(
            intake, changed, tasks_path, rules_path, tmp_path / "bundle", dry_run=True,
        )


def test_single_case_bundle_dry_run_writes_nothing(tmp_path: Path) -> None:
    intake, question, tasks_path, rules_path = _single_bundle_sources(tmp_path)
    target = tmp_path / "bundle"

    manifest = prepare_single_case_blind_bundle(
        intake, question, tasks_path, rules_path, target, dry_run=True,
    )

    assert manifest["case_count"] == 1
    assert not target.exists()


def test_v002_bundle_manifest_requires_supersedes_v001_manifest(tmp_path: Path) -> None:
    intake, question, tasks_path, rules_path = _single_bundle_sources(tmp_path)
    v001_target = tmp_path / f"{CASE_ID}--blind-bundle--v001"
    v001 = prepare_single_case_blind_bundle(
        intake, question, tasks_path, rules_path, v001_target, dry_run=False,
    )
    v002_intake, v002_question = _build(
        tmp_path / "v002-registration",
        version=2,
        created_at="2026-07-17T05:29:58Z",
        future_question=_question(observation_window={
            "start_at": "2026-07-17T05:30:00Z",
            "end_at": "2026-10-17T05:30:00Z",
        }),
        question_revision={
            "supersedes": question["artifact_path"],
            "supersedes_sha256": question["artifact_sha256"],
            "reason": "Correct planned freeze binding",
            "approved_by": "human-approver-01",
        },
        intake_revision={
            "supersedes": intake["artifact_path"],
            "supersedes_sha256": intake["artifact_sha256"],
            "reason": "Bind corrected future question",
            "approved_by": "human-approver-01",
        },
    )
    publish_new_json(Path(v002_question["artifact_path"]), v002_question, dry_run=False)
    publish_new_json(Path(v002_intake["artifact_path"]), v002_intake, dry_run=False)
    v002_target = tmp_path / f"{CASE_ID}--blind-bundle--v002"

    manifest = prepare_single_case_blind_bundle(
        v002_intake,
        v002_question,
        tasks_path,
        rules_path,
        v002_target,
        dry_run=True,
        revision={
            "supersedes": v001["artifact_path"],
            "supersedes_sha256": v001["artifact_sha256"],
            "reason": "Replace future planned start with immediate freeze chain",
            "approved_by": "human-approver-01",
        },
    )

    validate_revision_metadata(manifest, 2)
    assert manifest["supersedes"] == v001["artifact_path"]
    assert not v002_target.exists()


def test_single_case_bundle_formal_is_create_only_and_preserves_first_bytes(tmp_path: Path) -> None:
    intake, question, tasks_path, rules_path = _single_bundle_sources(tmp_path)
    target = tmp_path / "bundle"
    prepare_single_case_blind_bundle(intake, question, tasks_path, rules_path, target, dry_run=False)
    first_bytes = {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in target.rglob("*")
        if path.is_file()
    }

    with pytest.raises(ValueError, match="must not exist|already exists"):
        prepare_single_case_blind_bundle(
            intake, question, tasks_path, rules_path, target, dry_run=False,
        )

    assert {
        path.relative_to(target).as_posix(): path.read_bytes()
        for path in target.rglob("*")
        if path.is_file()
    } == first_bytes


def test_single_case_bundle_recomputes_published_parent_from_disk(tmp_path: Path) -> None:
    intake, question, tasks_path, rules_path = _single_bundle_sources(tmp_path)
    intake_path = Path(intake["artifact_path"])
    changed = json.loads(intake_path.read_text(encoding="utf-8"))
    changed["operator"] = "tampered-operator"
    changed["artifact_sha256"] = canonical_artifact_sha256(changed)
    intake_path.write_text(json.dumps(changed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(ContaminationError, match="parent"):
        prepare_single_case_blind_bundle(
            intake, question, tasks_path, rules_path, tmp_path / "bundle", dry_run=True,
        )


def test_single_case_bundle_rejects_nested_forbidden_task_content(tmp_path: Path) -> None:
    tasks = _tasks()
    tasks["tasks"][0]["label_schema"] = {
        "labels": ["safe", {"nested": "known_facts must not enter blind bundle"}]
    }
    intake, question = _build(tmp_path / "registration", tasks=tasks)
    publish_new_json(Path(question["artifact_path"]), question, dry_run=False)
    publish_new_json(Path(intake["artifact_path"]), intake, dry_run=False)
    tasks_path = tmp_path / "tasks.json"
    tasks_path.write_text(json.dumps(tasks, ensure_ascii=False), encoding="utf-8")
    rules_path = tmp_path / "rules.json"
    rules_path.write_text(json.dumps({"rule_snapshot_id": "rules-v1"}), encoding="utf-8")

    with pytest.raises(ContaminationError, match="forbidden"):
        prepare_single_case_blind_bundle(
            intake, question, tasks_path, rules_path, tmp_path / "bundle", dry_run=True,
        )


def test_single_case_bundle_stops_on_input_hash_change_and_symlink(tmp_path: Path) -> None:
    intake, question, tasks_path, rules_path = _single_bundle_sources(tmp_path)
    row = validate_single_case_intake(intake)
    Path(row["input_file"]).write_text("四柱：甲子 乙丑 丙寅 丁卯\n性别：乾\n污染", encoding="utf-8")
    with pytest.raises(ContaminationError, match="hash changed"):
        prepare_single_case_blind_bundle(
            intake, question, tasks_path, rules_path, tmp_path / "changed", dry_run=True,
        )

    intake, question, tasks_path, rules_path = _single_bundle_sources(
        tmp_path / "linked"
    )
    real_target = tmp_path / "real-bundle-target"
    real_target.mkdir()
    linked_target = tmp_path / "linked-bundle"
    try:
        linked_target.symlink_to(real_target, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is unavailable")
    with pytest.raises(ValueError, match="LINK_LIKE|symlink"):
        prepare_single_case_blind_bundle(
            intake,
            question,
            tasks_path,
            rules_path,
            linked_target,
            dry_run=True,
        )


def test_single_case_bundle_publish_race_is_create_only_and_cleans_temporary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    intake, question, tasks_path, rules_path = _single_bundle_sources(tmp_path)
    target = tmp_path / "bundle"
    real_rename = __import__("os").rename

    def lose_race(source: Path, destination: Path) -> None:
        destination.mkdir()
        (destination / "winner.txt").write_text("winner", encoding="utf-8")
        real_rename(source, destination)

    monkeypatch.setattr("engine.evaluation.prospective_single_case.os.rename", lose_race)

    with pytest.raises(ValueError, match="must not exist"):
        prepare_single_case_blind_bundle(
            intake, question, tasks_path, rules_path, target, dry_run=False,
        )

    assert (target / "winner.txt").read_text(encoding="utf-8") == "winner"
    assert not list(tmp_path.glob(".bundle.*"))


def _reseal_bundle_file(bundle: Path, name: str, document: dict[str, object]) -> None:
    path = bundle / name
    path.write_text(
        json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    manifest_path = bundle / "bundle-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][name] = __import__("hashlib").sha256(path.read_bytes()).hexdigest()
    manifest["bundle_sha256"] = __import__("hashlib").sha256(
        json.dumps(
            manifest["files"], ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    manifest["artifact_sha256"] = canonical_artifact_sha256(manifest)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_single_case_bundle_stops_on_forbidden_content_even_when_rehashed(tmp_path: Path) -> None:
    intake, question, tasks_path, rules_path = _single_bundle_sources(tmp_path)
    target = tmp_path / "bundle"
    prepare_single_case_blind_bundle(intake, question, tasks_path, rules_path, target, dry_run=False)
    question_path = target / "future-question.json"
    changed = json.loads(question_path.read_text(encoding="utf-8"))
    changed["question_text_redacted"] = "根据 feedback 判断结果"
    changed["artifact_sha256"] = canonical_artifact_sha256(changed)
    _reseal_bundle_file(target, "future-question.json", changed)

    with pytest.raises(ContaminationError, match="forbidden"):
        verify_single_case_bundle(target)


def test_single_case_bundle_stops_on_rehashed_future_parent_mismatch(tmp_path: Path) -> None:
    intake, question, tasks_path, rules_path = _single_bundle_sources(tmp_path)
    target = tmp_path / "bundle"
    prepare_single_case_blind_bundle(intake, question, tasks_path, rules_path, target, dry_run=False)
    question_path = target / "future-question.json"
    changed = json.loads(question_path.read_text(encoding="utf-8"))
    changed["case_id"] = "P-GO-2026-002-乾-甲子乙丑丙寅丁卯"
    changed["artifact_sha256"] = canonical_artifact_sha256(changed)
    _reseal_bundle_file(target, "future-question.json", changed)

    with pytest.raises(ContaminationError, match="parent mismatch"):
        verify_single_case_bundle(target)
