from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import engine.evaluation.prospective_artifacts as prospective_artifacts
from engine.evaluation.prospective_artifacts import (
    ArtifactRef,
    canonical_artifact_sha256,
    publish_new_json,
    single_case_artifact_path,
    validate_parent_ref,
)
import engine.evaluation.prospective_evidence as prospective_evidence
from engine.evaluation.prospective_capability_identity import (
    build_capability_identity_artifact,
)
from engine.evaluation.prospective_evidence import (
    apply_high_risk_final_label,
    build_case_completion,
    build_feedback_release_credential,
    collect_future_observation,
    evaluate_feedback_release,
    verify_single_case_freeze_chain,
)
from engine.evaluation.prospective_single_case import (
    ContaminationError,
    SIX_SCHOOLS,
    build_single_case_intake,
    build_single_case_staged_frozen_run,
    prepare_single_case_blind_bundle,
)
from tools.school_capability_dataset import append_witness_event
from tests.evaluation.test_governance_shadow_adapter import (
    _claim as governance_claim_fixture,
    _projection as governance_projection_fixture,
    _shadow as governance_shadow_fixture,
)


TASKS = Path("META/prospective-go-task-catalog-v1.json")
RULES = Path("META/prospective-go-rule-snapshot-v1.json")
FIXTURE_KEY = b"TEST-FIXTURE-KEY-NOT-REAL"
INDEPENDENT_ROLES = {
    "witness": "human-witness-01",
    "intake_operator": "human-intake-01",
    "runner_operator": "human-runner-01",
    "outcome_custodian": "human-custodian-01",
}


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: dict) -> None:
    path.write_bytes(
        (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )


def _registry(events: list[dict], key: bytes = FIXTURE_KEY) -> dict:
    result = None
    for event in events:
        result = append_witness_event(result, event, key)
    assert result is not None
    return result


@pytest.fixture(autouse=True)
def prospective_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        prospective_evidence,
        "_now_utc",
        lambda: prospective_evidence._utc("2026-11-01T00:00:00Z", "test clock"),
    )


@pytest.fixture()
def authority_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("prospective-evidence-authority").absolute()


@pytest.fixture()
def tmp_path(authority_root: Path) -> Path:
    return authority_root


@pytest.fixture(autouse=True)
def _repository_authority(
    authority_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = authority_root
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

    site_directory = root / "test-pythonpath"
    site_directory.mkdir()
    (site_directory / "sitecustomize.py").write_text(
        "from pathlib import Path\n"
        "from engine.evaluation import prospective_artifacts\n"
        f"prospective_artifacts._trusted_repository_root = lambda: Path({str(root)!r})\n",
        encoding="utf-8",
    )
    original_run = subprocess.run
    repository_path = str(Path.cwd())

    def authority_bound_run(
        *args: object, **kwargs: object
    ) -> subprocess.CompletedProcess:
        environment = dict(kwargs.get("env") or os.environ)
        existing = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = os.pathsep.join(
            part for part in (str(site_directory), repository_path, existing) if part
        )
        kwargs["env"] = environment
        return original_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", authority_bound_run)


@pytest.fixture()
def freeze_chain(authority_root: Path) -> dict:
    tmp_path = authority_root
    case_id = "P-GO-2026-001-乾-甲子乙丑丙寅丁卯"
    input_path = tmp_path / "source" / case_id / "input.md"
    input_path.parent.mkdir(parents=True)
    input_path.write_text(
        "Sex:乾\n$FOUR\nY:比肩,甲,子,正印\nM:劫财,乙,丑,正财\n"
        "D:元男,丙,寅,偏印\nH:伤官,丁,卯,正印\n$DY_LOOP\n"
        "#2026,8岁,戊辰,食神\n> 2026,丙午,食神\n",
        encoding="utf-8",
    )
    question_draft = {
        "future_task_id": "career.role_change",
        "question_text_redacted": "未来三个月是否发生显著岗位角色变化？",
        "outcome_type": "binary",
        "positive_definition": "发生并有雇佣资料或本人确认",
        "negative_definition": "完整窗口结束且核验来源确认未发生",
        "verification_source_requirements": ["custody://structured-interview"],
        "observation_window": {
            "start_at": "2026-07-16T00:00:00Z",
            "end_at": "2026-10-16T00:00:00Z",
        },
    }
    intake, question = build_single_case_intake(
        input_path,
        _read(TASKS),
        SIX_SCHOOLS,
        "human-intake-01",
        {"P-GO-2026-001": ["career.role_change", "career.change_window"]},
        question_draft,
        created_at="2026-07-15T23:59:58Z",
        case_root=tmp_path / "parents",
    )
    publish_new_json(Path(question["artifact_path"]), question, dry_run=False)
    publish_new_json(Path(intake["artifact_path"]), intake, dry_run=False)
    bundle_root = tmp_path / "bundle"
    manifest = prepare_single_case_blind_bundle(
        intake,
        question,
        TASKS,
        RULES,
        bundle_root,
        dry_run=False,
    )
    frozen = build_single_case_staged_frozen_run(bundle_root)
    frozen_path = Path(frozen["artifact_path"])
    publish_new_json(frozen_path, frozen, dry_run=False)
    frozen = _read(frozen_path)
    events = [
        {
            "event_type": "registered",
            "occurred_at": "2026-07-15T23:59:58Z",
            "payload": {
                "case_id": case_id,
                "input_sha256": intake["records"][0]["input_sha256"],
                "subject_id_hash": intake["subject_id_hash"],
            },
        },
        {
            "event_type": "prepared",
            "occurred_at": "2026-07-15T23:59:59Z",
            "payload": {"case_id": case_id, "bundle_sha256": manifest["bundle_sha256"]},
        },
        {
            "event_type": "freeze",
            "occurred_at": "2026-07-16T00:00:00Z",
            "payload": {
                "case_id": case_id,
                "freeze_hash": frozen["frozen_run"]["freeze_hash"],
            },
        },
    ]
    registry_path = tmp_path / "witness.json"
    registry_body = _registry(events)
    registry_payload = {
        **registry_body,
        "case_id": case_id,
        "subject_id_hash": intake["subject_id_hash"],
        "created_at": events[-1]["occurred_at"],
        "artifact_path": registry_path.as_posix(),
        "parents": [],
    }
    registry = {
        **registry_payload,
        "artifact_sha256": canonical_artifact_sha256(registry_payload),
    }
    _write(registry_path, registry)
    return {
        "intake_path": Path(intake["artifact_path"]),
        "bundle_root": bundle_root,
        "frozen_run_path": frozen_path,
        "registry_path": registry_path,
        "expected_external_root": registry["events"][-1]["event_hash"],
        "verified_at": "2026-07-16T01:00:00Z",
        "verifier": "human-witness-01",
        "events": events,
        "case_id": case_id,
    }


def _verify(chain: dict, **overrides: object) -> dict:
    arguments = {
        key: value for key, value in chain.items() if key not in {"events", "case_id"}
    }
    arguments.update(overrides)
    return verify_single_case_freeze_chain(**arguments, witness_key=FIXTURE_KEY)


@pytest.fixture()
def release_credential(freeze_chain: dict) -> dict:
    verification = _verify(freeze_chain)
    verification_path = Path(verification["artifact_path"])
    publish_new_json(
        verification_path,
        {key: value for key, value in verification.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    release = build_feedback_release_credential(
        _read(verification_path),
        INDEPENDENT_ROLES,
        {"marker_count": 0, "status": "PASS"},
        created_at="2026-07-16T01:05:00Z",
    )
    release_path = Path(release["artifact_path"])
    publish_new_json(
        release_path,
        {key: value for key, value in release.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    return _read(release_path)


def test_w2_c4_evidence_lineage_has_no_rootless_parent_read_or_self_selected_root() -> (
    None
):
    module = ast.parse(
        Path("engine/evaluation/prospective_evidence.py").read_text("utf-8")
    )
    rootless_parent_reads = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "validate_parent_ref"
        and not any(keyword.arg == "admitted_root" for keyword in node.keywords)
    ]
    self_selected_roots = [
        node
        for node in ast.walk(module)
        if isinstance(node, ast.Attribute)
        and node.attr == "parent"
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "parent"
    ]

    assert rootless_parent_reads == []
    assert self_selected_roots == []


def test_verification_and_completion_recursively_preserve_capability_identity(
    freeze_chain: dict,
    tmp_path: Path,
) -> None:
    claim = governance_claim_fixture()
    shadow = governance_shadow_fixture(claim)
    projection = governance_projection_fixture(shadow, claim)
    identity, identity_ref = build_capability_identity_artifact(
        claim,
        governance_result=shadow,
        governance_projection=projection,
        created_at="2026-07-16T00:00:00Z",
        source_output_path=tmp_path / "governance-source.json",
        output_path=tmp_path / "capability-identity.json",
        dry_run=False,
    )
    frozen_path = freeze_chain["frozen_run_path"]
    frozen = _read(frozen_path)
    identity_value = {
        "artifact_path": identity_ref.artifact_path,
        "artifact_sha256": identity_ref.artifact_sha256,
    }
    source_value = {
        "artifact_path": identity.governance_source_ref.artifact_path,
        "artifact_sha256": identity.governance_source_ref.artifact_sha256,
    }
    frozen["capability_identity_ref"] = identity_value
    frozen["governance_source_ref"] = source_value
    frozen["parents"].extend((identity_value, source_value))
    frozen.pop("artifact_sha256")
    frozen["artifact_sha256"] = canonical_artifact_sha256(frozen)
    _write(frozen_path, frozen)

    verification = _verify(freeze_chain)
    assert verification["capability_identity_ref"] == identity_value
    assert verification["governance_source_ref"] == source_value
    assert verification["parents"].count(identity_value) == 1
    assert verification["parents"].count(source_value) == 1
    verification_path = Path(verification["artifact_path"])
    publish_new_json(
        verification_path,
        {key: value for key, value in verification.items() if key != "artifact_sha256"},
        dry_run=False,
    )

    completion = build_case_completion(
        freeze_verification=_read(verification_path),
        immediate_bound=None,
        future_bound=None,
        stopped_incident=None,
        created_at="2026-07-16T02:00:00Z",
    )
    assert completion["capability_identity_ref"] == identity_value
    assert completion["governance_source_ref"] == source_value

    Path(source_value["artifact_path"]).unlink()
    with pytest.raises(
        (ValueError, ContaminationError), match="source|parent|UNREADABLE|unreadable"
    ):
        build_case_completion(
            freeze_verification=_read(verification_path),
            immediate_bound=None,
            future_bound=None,
            stopped_incident=None,
            created_at="2026-07-16T02:00:00Z",
        )


def test_case_completion_explicitly_propagates_one_exact_repository_authority(
    freeze_chain: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verification = _verify(freeze_chain)
    verification_path = Path(verification["artifact_path"])
    publish_new_json(
        verification_path,
        {key: value for key, value in verification.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    expected_authority = prospective_artifacts._repository_authority()
    resolver_calls = 0
    observed: list[object] = []
    original_actual_sealed = prospective_evidence._actual_sealed_artifact
    original_validate_tree = prospective_evidence._validate_parent_tree

    def operation_start_authority() -> object:
        nonlocal resolver_calls
        resolver_calls += 1
        if resolver_calls != 1:
            raise AssertionError(
                "completion downstream reacquired repository authority"
            )
        return expected_authority

    def actual_sealed_probe(
        path: Path,
        description: str,
        *,
        authority: object,
    ) -> dict:
        assert authority is expected_authority
        observed.append(authority)
        return original_actual_sealed(path, description, authority=authority)

    def validate_tree_probe(
        document: dict,
        *,
        authority: object,
        visited: set[tuple[str, str]] | None = None,
    ) -> None:
        assert authority is expected_authority
        observed.append(authority)
        original_validate_tree(document, authority=authority, visited=visited)

    monkeypatch.setattr(
        prospective_evidence, "_repository_authority", operation_start_authority
    )
    monkeypatch.setattr(
        prospective_evidence, "_actual_sealed_artifact", actual_sealed_probe
    )
    monkeypatch.setattr(
        prospective_evidence, "_validate_parent_tree", validate_tree_probe
    )

    completion = prospective_evidence.build_case_completion(
        freeze_verification=_read(verification_path),
        immediate_bound=None,
        future_bound=None,
        stopped_incident=None,
        created_at="2026-07-16T02:00:00Z",
    )

    assert completion["schema_version"] == "prospective-case-completion/v1"
    assert resolver_calls == 1
    assert len(observed) >= 2
    assert all(authority is expected_authority for authority in observed)


def _custody_payload(case_id: str, facts: list[dict] | None = None) -> dict:
    return {
        "schema_version": "prospective-immediate-retrospective-custody/v1",
        "case_id": case_id,
        "facts": facts
        or [
            {
                "task_id": "career.role_change",
                "label": "occurred",
                "occurred_at": "2026-07-15T12:00:00Z",
                "relative_time": "before_or_at_freeze",
                "source_refs": ["custody://structured-interview/001"],
            }
        ],
    }


def test_verify_requires_actual_three_events_external_root_and_correct_fixture_key(
    freeze_chain: dict,
) -> None:
    verification = _verify(freeze_chain)

    assert (
        verification["schema_version"]
        == "prospective-single-case-freeze-verification/v1"
    )
    assert verification["status"] == "VERIFIED"
    assert verification["case_id"] == freeze_chain["case_id"]
    assert verification["freeze_at"] == "2026-07-16T00:00:00Z"
    assert verification["witness_identity_ref"] == "human-witness-01"
    assert len(verification["parents"]) == 4
    for parent in verification["parents"]:
        validate_parent_ref(ArtifactRef(**parent))
    assert verification["witness_event_types"] == ["registered", "prepared", "freeze"]
    assert (
        verification["external_registry_root"] == freeze_chain["expected_external_root"]
    )
    assert verification["artifact_sha256"]
    serialized = json.dumps(verification, ensure_ascii=False).lower()
    assert "fixture-key" not in serialized
    assert FIXTURE_KEY.decode().lower() not in serialized


@pytest.mark.parametrize("key", [b"", b"WRONG-TEST-KEY"])
def test_wrong_or_empty_key_never_verifies_or_releases(
    freeze_chain: dict, key: bytes
) -> None:
    arguments = {
        name: value
        for name, value in freeze_chain.items()
        if name not in {"events", "case_id"}
    }
    with pytest.raises(ValueError, match="key|HMAC"):
        verify_single_case_freeze_chain(**arguments, witness_key=key)


@pytest.mark.parametrize(
    "mutation", ["missing", "duplicate", "out-of-order", "wrong-case"]
)
def test_event_segment_must_be_exact_ordered_and_single_case(
    freeze_chain: dict, mutation: str
) -> None:
    events = copy.deepcopy(freeze_chain["events"])
    if mutation == "missing":
        events.pop(1)
    elif mutation == "duplicate":
        events.insert(1, copy.deepcopy(events[0]))
    elif mutation == "out-of-order":
        events[0], events[1] = events[1], events[0]
    else:
        for event in events:
            event["payload"]["case_id"] = "P-GO-2026-002-坤-戊辰己巳庚午辛未"
    registry_body = _registry(events)
    registry_payload = {
        **registry_body,
        "case_id": freeze_chain["case_id"],
        "subject_id_hash": "a" * 64,
        "created_at": events[-1]["occurred_at"],
        "artifact_path": freeze_chain["registry_path"].as_posix(),
        "parents": [],
    }
    registry = {
        **registry_payload,
        "artifact_sha256": canonical_artifact_sha256(registry_payload),
    }
    _write(freeze_chain["registry_path"], registry)

    with pytest.raises(
        (ContaminationError, ValueError), match="event|case|three|segment|order"
    ):
        _verify(
            freeze_chain, expected_external_root=registry["events"][-1]["event_hash"]
        )


def test_parent_byte_change_and_external_root_mismatch_fail_closed(
    freeze_chain: dict,
) -> None:
    with pytest.raises(ContaminationError, match="root"):
        _verify(freeze_chain, expected_external_root="f" * 64)

    freeze_chain["intake_path"].write_bytes(
        freeze_chain["intake_path"].read_bytes() + b" "
    )
    with pytest.raises((ContaminationError, ValueError), match="parent|drift|hash"):
        _verify(freeze_chain)


def test_each_verification_parent_drift_is_recomputed(freeze_chain: dict) -> None:
    verification = _verify(freeze_chain)
    for parent in verification["parents"]:
        path = Path(parent["artifact_path"])
        original = path.read_bytes()
        try:
            path.write_bytes(original + b" ")
            with pytest.raises(
                (ContaminationError, ValueError), match="parent|drift|hash|bundle"
            ):
                _verify(freeze_chain)
        finally:
            path.write_bytes(original)


def test_verification_must_postdate_freeze_and_use_named_human_identity(
    freeze_chain: dict,
) -> None:
    for verified_at in ("2026-07-15T23:59:59Z", "2026-07-16T00:00:00Z"):
        with pytest.raises(ValueError, match="later than freeze"):
            _verify(freeze_chain, verified_at=verified_at)
    for verifier in ("automated-verifier", "agent-verify-01", "ai-verifier"):
        with pytest.raises(ValueError, match="named human"):
            _verify(freeze_chain, verifier=verifier)


def test_frozen_run_itself_opens_feedback_intake(freeze_chain: dict) -> None:
    frozen = _read(freeze_chain["frozen_run_path"])

    release = build_feedback_release_credential(
        frozen,
        created_at="2026-07-16T01:05:00Z",
    )

    assert release["schema_version"] == "prospective-feedback-release/v2"
    assert release["release_status"] == "RELEASED"
    assert release["freeze_at"] == frozen["freeze_at"]
    assert release["parents"] == [
        {
            "artifact_path": frozen["artifact_path"],
            "artifact_sha256": frozen["artifact_sha256"],
        }
    ]
    assert "verification" not in json.dumps(release).lower()
    assert "witness" not in json.dumps(release).lower()


def test_v2_release_collects_immediate_retrospective_from_mixed_frozen_parents(
    freeze_chain: dict,
) -> None:
    frozen = _read(freeze_chain["frozen_run_path"])
    release = build_feedback_release_credential(
        frozen,
        created_at="2026-07-16T01:05:00Z",
    )
    release_path = Path(release["artifact_path"])
    publish_new_json(
        release_path,
        {key: value for key, value in release.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    release = _read(release_path)

    result = prospective_evidence.collect_immediate_retrospective(
        release,
        lambda: _custody_payload(release["case_id"]),
        collected_at="2026-07-16T02:00:00Z",
        custodian="human-custodian-01",
    )

    assert result["facts"][0]["task_id"] == "career.role_change"
    assert result["facts"][0]["classification"] == "immediate_fact"


def test_release_requires_verified_independent_roles_and_strict_clean_scan(
    freeze_chain: dict,
) -> None:
    verification = _verify(freeze_chain)
    release = build_feedback_release_credential(
        verification,
        INDEPENDENT_ROLES,
        {"marker_count": 0, "status": "PASS"},
        created_at="2026-07-16T01:05:00Z",
    )

    assert release["schema_version"] == "prospective-feedback-release/v1"
    assert release["release_status"] == "RELEASED"
    assert release["case_id"] == verification["case_id"]
    assert release["freeze_at"] == verification["freeze_at"]
    assert release["parents"] == [
        {
            "artifact_path": verification["artifact_path"],
            "artifact_sha256": verification["artifact_sha256"],
        }
    ]
    assert release["artifact_sha256"]

    with pytest.raises(ValueError, match="VERIFIED"):
        build_feedback_release_credential(
            {**verification, "status": "HOLD"},
            INDEPENDENT_ROLES,
            {"marker_count": 0, "status": "PASS"},
            created_at="2026-07-16T01:05:00Z",
        )
    with pytest.raises(ValueError, match="role separation"):
        build_feedback_release_credential(
            verification,
            {**INDEPENDENT_ROLES, "outcome_custodian": "human-witness-01"},
            {"marker_count": 0, "status": "PASS"},
            created_at="2026-07-16T01:05:00Z",
        )
    with pytest.raises(ValueError, match="named human"):
        build_feedback_release_credential(
            verification,
            {**INDEPENDENT_ROLES, "runner_operator": "automated-runner"},
            {"marker_count": 0, "status": "PASS"},
            created_at="2026-07-16T01:05:00Z",
        )
    for scan in (
        {"marker_count": 1, "status": "PASS"},
        {"marker_count": 0},
        {"marker_count": 0, "status": "FAIL"},
        {"marker_count": False, "status": "PASS"},
        {"marker_count": 0, "status": "PASS", "nested": {"marker_count": 1}},
    ):
        with pytest.raises(ContaminationError, match="leakage"):
            build_feedback_release_credential(
                verification,
                INDEPENDENT_ROLES,
                scan,
                created_at="2026-07-16T01:05:00Z",
            )


def test_release_gate_reads_feedback_only_after_verified() -> None:
    opened: list[Path] = []

    def forbidden_reader(path: Path) -> str:
        opened.append(path)
        raise AssertionError("feedback was opened before verification")

    result = evaluate_feedback_release(
        {"status": "HOLD"},
        roles=INDEPENDENT_ROLES,
        leakage_scan={"marker_count": 0, "status": "PASS"},
        feedback_reader=forbidden_reader,
    )

    assert result.status == "HOLD"
    assert opened == []


def test_release_gate_holds_without_reading_feedback_on_unexpected_gate_exception() -> (
    None
):
    opened: list[Path] = []

    class ExplodingRoles(dict):
        def __iter__(self):
            raise RuntimeError("malformed role source")

    result = evaluate_feedback_release(
        {"created_at": "2026-07-16T01:05:00Z", "feedback_path": "feedback.md"},
        roles=ExplodingRoles(INDEPENDENT_ROLES),
        leakage_scan={"marker_count": 0, "status": "PASS"},
        feedback_reader=lambda path: opened.append(path),
    )

    assert result.status == "HOLD"
    assert opened == []


def test_cli_verification_and_release_are_create_only_and_never_leak_key(
    freeze_chain: dict,
    tmp_path: Path,
) -> None:
    verification_path = tmp_path / "verification.json"
    key_text = FIXTURE_KEY.decode()
    environment = {**os.environ, "PYTHONUTF8": "1", "FIXTURE_WITNESS_KEY": key_text}
    verify_command = [
        sys.executable,
        "-m",
        "tools.school_capability_dataset",
        "witness-verify-single-case",
        "--intake",
        str(freeze_chain["intake_path"]),
        "--bundle-root",
        str(freeze_chain["bundle_root"]),
        "--frozen-run",
        str(freeze_chain["frozen_run_path"]),
        "--registry",
        str(freeze_chain["registry_path"]),
        "--external-root",
        freeze_chain["expected_external_root"],
        "--verifier",
        "human-witness-01",
        "--verified-at",
        "2026-07-16T01:00:00Z",
        "--out",
        str(verification_path),
        "--witness-key-env",
        "FIXTURE_WITNESS_KEY",
    ]
    dry = subprocess.run(
        [*verify_command, "--dry-run"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )
    assert dry.returncode == 0, dry.stderr
    assert not verification_path.exists()
    assert json.loads(dry.stdout)["status"] == "VERIFIED"
    first = subprocess.run(
        verify_command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )
    assert first.returncode == 0, first.stderr
    original = verification_path.read_bytes()
    second = subprocess.run(
        verify_command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )
    assert second.returncode != 0
    assert verification_path.read_bytes() == original
    assert key_text not in (
        dry.stdout
        + dry.stderr
        + first.stdout
        + first.stderr
        + verification_path.read_text(encoding="utf-8")
    )

    roles_path = tmp_path / "roles.json"
    scan_path = tmp_path / "scan.json"
    release_path = tmp_path / "release.json"
    _write(roles_path, INDEPENDENT_ROLES)
    _write(scan_path, {"marker_count": 0, "status": "PASS"})
    release_command = [
        sys.executable,
        "-m",
        "tools.school_capability_dataset",
        "issue-feedback-release",
        "--verification",
        str(verification_path),
        "--roles",
        str(roles_path),
        "--leakage-scan",
        str(scan_path),
        "--created-at",
        "2026-07-16T01:05:00Z",
        "--out",
        str(release_path),
    ]
    released = subprocess.run(
        release_command, check=False, capture_output=True, text=True, encoding="utf-8"
    )
    assert released.returncode == 0, released.stderr
    assert _read(release_path)["release_status"] == "RELEASED"
    assert "feedback" not in {
        option
        for action in __import__(
            "tools.school_capability_dataset", fromlist=["_parser"]
        )
        ._parser()
        ._actions
        for option in action.option_strings
        if "path" in option
    }
    assert key_text not in (
        released.stdout + released.stderr + release_path.read_text(encoding="utf-8")
    )


def test_cli_error_repr_does_not_echo_key_value(
    freeze_chain: dict, tmp_path: Path
) -> None:
    secret = "TEST-FIXTURE-CLI-SECRET-NOT-REAL"
    output = tmp_path / "verification.json"
    environment = {**os.environ, "PYTHONUTF8": "1", "FIXTURE_WITNESS_KEY": secret}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.school_capability_dataset",
            "witness-verify-single-case",
            "--intake",
            str(freeze_chain["intake_path"]),
            "--bundle-root",
            str(freeze_chain["bundle_root"]),
            "--frozen-run",
            str(freeze_chain["frozen_run_path"]),
            "--registry",
            str(freeze_chain["registry_path"]),
            "--external-root",
            freeze_chain["expected_external_root"],
            "--verifier",
            "human-witness-01",
            "--verified-at",
            "2026-07-16T01:00:00Z",
            "--out",
            str(output),
            "--witness-key-env",
            "FIXTURE_WITNESS_KEY",
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )

    assert result.returncode != 0
    assert secret not in result.stdout + result.stderr
    assert "Traceback" not in result.stderr
    assert not output.exists()


def test_cli_missing_key_environment_fails_without_artifact_or_secret_echo(
    freeze_chain: dict,
    tmp_path: Path,
) -> None:
    output = tmp_path / "verification.json"
    environment = {
        key: value for key, value in os.environ.items() if key != "ABSENT_WITNESS_KEY"
    }
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.school_capability_dataset",
            "witness-verify-single-case",
            "--intake",
            str(freeze_chain["intake_path"]),
            "--bundle-root",
            str(freeze_chain["bundle_root"]),
            "--frozen-run",
            str(freeze_chain["frozen_run_path"]),
            "--registry",
            str(freeze_chain["registry_path"]),
            "--external-root",
            freeze_chain["expected_external_root"],
            "--verifier",
            "human-witness-01",
            "--verified-at",
            "2026-07-16T01:00:00Z",
            "--out",
            str(output),
            "--witness-key-env",
            "ABSENT_WITNESS_KEY",
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )

    assert result.returncode != 0
    assert not output.exists()
    assert FIXTURE_KEY.decode() not in result.stdout + result.stderr


def test_immediate_retrospective_classifies_only_facts_at_or_before_freeze(
    release_credential: dict,
) -> None:
    result = prospective_evidence.collect_immediate_retrospective(
        release_credential,
        lambda: _custody_payload(
            release_credential["case_id"],
            facts=[
                {
                    "task_id": "career.role_change",
                    "label": "occurred",
                    "occurred_at": "2026-07-15T12:00:00Z",
                    "relative_time": "before_or_at_freeze",
                    "source_refs": ["custody://structured-interview/001"],
                },
                {
                    "task_id": "wealth.debt",
                    "label": "unknown",
                    "occurred_at": None,
                    "relative_time": "unknown",
                    "source_refs": ["custody://structured-interview/002"],
                },
            ],
        ),
        collected_at="2026-07-16T02:00:00Z",
        custodian="human-custodian-01",
    )

    assert result["evidence_class"] == "prediction_first_immediate_retrospective"
    assert result["fact_cutoff_at"] == release_credential["freeze_at"]
    assert result["collected_after_verification"] is True
    assert result["custodian"] == "human-custodian-01"
    assert result["facts"][0]["classification"] == "immediate_fact"
    assert result["facts"][1]["classification"] == "no_data"
    assert result["facts"][1]["scorable"] is False

    def all_keys(value: object) -> set[str]:
        if isinstance(value, dict):
            return set(value) | set().union(
                *(all_keys(item) for item in value.values())
            )
        if isinstance(value, list):
            return set().union(*(all_keys(item) for item in value))
        return set()

    for forbidden in (
        "prediction",
        "probability",
        "rationale",
        "report",
        "runner",
        "reviewer",
    ):
        assert forbidden not in all_keys(result)


def test_after_freeze_fact_is_rejected_instead_of_becoming_pseudo_future(
    release_credential: dict,
) -> None:
    custody = _custody_payload(
        release_credential["case_id"],
        facts=[
            {
                "task_id": "career.role_change",
                "label": "occurred",
                "occurred_at": "2026-07-16T00:00:01Z",
                "relative_time": "after_freeze",
                "source_refs": ["custody://structured-interview/003"],
            }
        ],
    )

    with pytest.raises(ValueError, match="after freeze|immediate"):
        prospective_evidence.collect_immediate_retrospective(
            release_credential,
            lambda: custody,
            collected_at="2026-07-16T02:00:00Z",
            custodian="human-custodian-01",
        )


def test_invalid_or_drifted_release_never_invokes_custody_reader(
    release_credential: dict,
) -> None:
    opened = 0

    def forbidden_reader() -> dict:
        nonlocal opened
        opened += 1
        raise AssertionError("custody opened before release validation")

    invalid = {**release_credential, "release_status": "HOLD"}
    with pytest.raises(
        (ValueError, ContaminationError), match="release|RELEASED|hash|drift"
    ):
        prospective_evidence.collect_immediate_retrospective(
            invalid,
            forbidden_reader,
            collected_at="2026-07-16T02:00:00Z",
            custodian="human-custodian-01",
        )
    assert opened == 0

    Path(release_credential["artifact_path"]).write_bytes(
        Path(release_credential["artifact_path"]).read_bytes() + b" "
    )
    with pytest.raises((ValueError, ContaminationError), match="release|hash|drift"):
        prospective_evidence.collect_immediate_retrospective(
            release_credential,
            forbidden_reader,
            collected_at="2026-07-16T02:00:00Z",
            custodian="human-custodian-01",
        )
    assert opened == 0


def test_custody_schema_rejects_prediction_fields_and_future_evidence_class(
    release_credential: dict,
) -> None:
    for forbidden_field in (
        "prediction",
        "probability",
        "rationale",
        "report",
        "runner",
        "reviewer",
    ):
        custody = _custody_payload(release_credential["case_id"])
        custody["facts"][0][forbidden_field] = "forbidden"
        with pytest.raises(ValueError, match="field|schema|forbidden"):
            prospective_evidence.collect_immediate_retrospective(
                release_credential,
                lambda custody=custody: custody,
                collected_at="2026-07-16T02:00:00Z",
                custodian="human-custodian-01",
            )

    custody = _custody_payload(release_credential["case_id"])
    custody["evidence_class"] = "future_outcome"
    with pytest.raises(ValueError, match="field|schema|future"):
        prospective_evidence.collect_immediate_retrospective(
            release_credential,
            lambda: custody,
            collected_at="2026-07-16T02:00:00Z",
            custodian="human-custodian-01",
        )


def test_label_identity_is_stable_and_duplicate_fact_identity_is_rejected(
    release_credential: dict,
) -> None:
    custody = _custody_payload(release_credential["case_id"])
    first = prospective_evidence.collect_immediate_retrospective(
        release_credential,
        lambda: copy.deepcopy(custody),
        collected_at="2026-07-16T02:00:00Z",
        custodian="human-custodian-01",
    )
    second = prospective_evidence.collect_immediate_retrospective(
        release_credential,
        lambda: copy.deepcopy(custody),
        collected_at="2026-07-16T03:00:00Z",
        custodian="human-custodian-01",
    )
    assert first["facts"][0]["label_identity"] == second["facts"][0]["label_identity"]

    duplicate = _custody_payload(
        release_credential["case_id"],
        facts=[copy.deepcopy(custody["facts"][0]), copy.deepcopy(custody["facts"][0])],
    )
    with pytest.raises(ValueError, match="duplicate label identity"):
        prospective_evidence.collect_immediate_retrospective(
            release_credential,
            lambda: duplicate,
            collected_at="2026-07-16T02:00:00Z",
            custodian="human-custodian-01",
        )


def test_bind_immediate_labels_keeps_no_data_unscored_and_never_emits_future_class(
    release_credential: dict,
) -> None:
    unbound = prospective_evidence.collect_immediate_retrospective(
        release_credential,
        lambda: _custody_payload(
            release_credential["case_id"],
            facts=[
                {
                    "task_id": "wealth.debt",
                    "label": "unknown",
                    "occurred_at": None,
                    "relative_time": "unknown",
                    "source_refs": ["custody://structured-interview/004"],
                }
            ],
        ),
        collected_at="2026-07-16T02:00:00Z",
        custodian="human-custodian-01",
    )
    bound = prospective_evidence.bind_immediate_labels(unbound)

    assert bound["evidence_class"] == "prediction_first_immediate_retrospective"
    assert bound["facts"][0]["classification"] == "no_data"
    assert bound["facts"][0]["scorable"] is False
    assert bound["scorable_label_count"] == 0
    assert "future_outcome" not in json.dumps(bound, ensure_ascii=False)


def test_immediate_cli_validates_release_before_template_write_or_custody_open(
    release_credential: dict,
    tmp_path: Path,
) -> None:
    invalid_release_path = tmp_path / "invalid-release.json"
    invalid_release = {**release_credential, "release_status": "HOLD"}
    invalid_release["artifact_sha256"] = canonical_artifact_sha256(invalid_release)
    _write(invalid_release_path, invalid_release)
    missing_custody = tmp_path / "must-not-open.json"
    output = tmp_path / "must-not-exist.json"

    collect = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.school_capability_dataset",
            "collect-immediate-retrospective",
            "--release",
            str(invalid_release_path),
            "--custody-input",
            str(missing_custody),
            "--collected-at",
            "2026-07-16T02:00:00Z",
            "--custodian",
            "human-custodian-01",
            "--out",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert collect.returncode != 0
    assert "release" in collect.stderr.lower() or "released" in collect.stderr.lower()
    assert "must-not-open" not in collect.stderr
    assert not output.exists()

    template = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.school_capability_dataset",
            "release-immediate-retrospective-template",
            "--release",
            str(invalid_release_path),
            "--out",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert template.returncode != 0
    assert not output.exists()


def test_immediate_cli_template_collect_and_dry_run_are_create_only(
    release_credential: dict,
    tmp_path: Path,
) -> None:
    template_output = tmp_path / "custody-template.json"
    release_template_command = [
        sys.executable,
        "-m",
        "tools.school_capability_dataset",
        "release-immediate-retrospective-template",
        "--release",
        release_credential["artifact_path"],
        "--out",
        str(template_output),
    ]
    environment = {**os.environ, "PYTHONUTF8": "1"}
    dry = subprocess.run(
        [*release_template_command, "--dry-run"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )
    assert dry.returncode == 0, dry.stderr
    assert not template_output.exists()
    assert json.loads(dry.stdout)["case_id"] == release_credential["case_id"]
    released = subprocess.run(
        release_template_command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )
    assert released.returncode == 0, released.stderr
    custody = _read(template_output)
    custody["facts"] = _custody_payload(release_credential["case_id"])["facts"]
    _write(template_output, custody)

    collected_output = Path(
        prospective_evidence.collect_immediate_retrospective(
            release_credential,
            lambda: copy.deepcopy(custody),
            collected_at="2026-07-16T02:00:00Z",
            custodian="human-custodian-01",
        )["artifact_path"]
    )
    collect_command = [
        sys.executable,
        "-m",
        "tools.school_capability_dataset",
        "collect-immediate-retrospective",
        "--release",
        release_credential["artifact_path"],
        "--custody-input",
        str(template_output),
        "--collected-at",
        "2026-07-16T02:00:00Z",
        "--custodian",
        "human-custodian-01",
        "--out",
        str(collected_output),
    ]
    dry_collect = subprocess.run(
        [*collect_command, "--dry-run"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )
    assert dry_collect.returncode == 0, dry_collect.stderr
    assert not collected_output.exists()
    assert "prediction" not in {
        key for fact in json.loads(dry_collect.stdout)["facts"] for key in fact
    }
    collected = subprocess.run(
        collect_command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )
    assert collected.returncode == 0, collected.stderr
    assert (
        _read(collected_output)["evidence_class"]
        == "prediction_first_immediate_retrospective"
    )
    original = collected_output.read_bytes()
    duplicate = subprocess.run(
        collect_command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )
    assert duplicate.returncode != 0
    assert collected_output.read_bytes() == original


def test_release_validation_recomputes_verification_grandparents_before_custody(
    release_credential: dict,
) -> None:
    opened = 0

    def forbidden_reader() -> dict:
        nonlocal opened
        opened += 1
        return _custody_payload(release_credential["case_id"])

    release_parent = validate_parent_ref(
        ArtifactRef(**release_credential["parents"][0])
    )
    frozen_parent = next(
        parent
        for parent in release_parent["parents"]
        if "frozen-run" in parent["artifact_path"]
    )
    frozen_path = Path(frozen_parent["artifact_path"])
    frozen_path.write_bytes(frozen_path.read_bytes() + b" ")

    with pytest.raises(
        (ContaminationError, ValueError), match="parent|drift|hash|freeze"
    ):
        prospective_evidence.collect_immediate_retrospective(
            release_credential,
            forbidden_reader,
            collected_at="2026-07-16T02:00:00Z",
            custodian="human-custodian-01",
        )
    assert opened == 0


@pytest.mark.parametrize(
    ("task_id", "label"),
    [
        ("career.role_change", "changed_before_freeze"),
        ("career.path_type", "contractor"),
        ("health.system_risk", "critical"),
        ("career.change_window", {"occurred": True, "year": "2026"}),
    ],
)
def test_custody_label_must_match_the_bound_task_schema(
    release_credential: dict,
    task_id: str,
    label: object,
) -> None:
    custody = _custody_payload(
        release_credential["case_id"],
        facts=[
            {
                "task_id": task_id,
                "label": label,
                "occurred_at": "2026-07-15T12:00:00Z",
                "relative_time": "before_or_at_freeze",
                "source_refs": ["custody://structured-interview/schema"],
            }
        ],
    )

    with pytest.raises(ValueError, match="label|schema|task"):
        prospective_evidence.collect_immediate_retrospective(
            release_credential,
            lambda: custody,
            collected_at="2026-07-16T02:00:00Z",
            custodian="human-custodian-01",
        )


def test_time_window_label_schema_is_accepted_without_prediction_content(
    release_credential: dict,
) -> None:
    custody = _custody_payload(
        release_credential["case_id"],
        facts=[
            {
                "task_id": "career.change_window",
                "label": {"occurred": True, "year": 2026},
                "occurred_at": "2026-07-15T12:00:00Z",
                "relative_time": "before_or_at_freeze",
                "source_refs": ["custody://structured-interview/window"],
            }
        ],
    )

    result = prospective_evidence.collect_immediate_retrospective(
        release_credential,
        lambda: custody,
        collected_at="2026-07-16T02:00:00Z",
        custodian="human-custodian-01",
    )
    assert result["facts"][0]["label"] == {"occurred": True, "year": 2026}


def test_nested_prediction_material_in_structured_label_is_rejected(
    release_credential: dict,
) -> None:
    custody = _custody_payload(
        release_credential["case_id"],
        facts=[
            {
                "task_id": "career.change_window",
                "label": {
                    "occurred": True,
                    "year": 2026,
                    "prediction": "runner said yes",
                },
                "occurred_at": "2026-07-15T12:00:00Z",
                "relative_time": "before_or_at_freeze",
                "source_refs": ["custody://structured-interview/nested"],
            }
        ],
    )

    with pytest.raises(ValueError, match="forbidden|prediction|schema"):
        prospective_evidence.collect_immediate_retrospective(
            release_credential,
            lambda: custody,
            collected_at="2026-07-16T02:00:00Z",
            custodian="human-custodian-01",
        )


@pytest.mark.parametrize(
    "occurred_at", ["2026-07-15T12:00:00", "2026-07-15T20:00:00+08:00"]
)
def test_custody_time_requires_explicit_utc_z(
    release_credential: dict,
    occurred_at: str,
) -> None:
    custody = _custody_payload(release_credential["case_id"])
    custody["facts"][0]["occurred_at"] = occurred_at
    with pytest.raises(ValueError, match="UTC|timestamp"):
        prospective_evidence.collect_immediate_retrospective(
            release_credential,
            lambda: custody,
            collected_at="2026-07-16T02:00:00Z",
            custodian="human-custodian-01",
        )


def test_fact_exactly_at_freeze_is_immediate_and_scorable(
    release_credential: dict,
) -> None:
    custody = _custody_payload(release_credential["case_id"])
    custody["facts"][0]["occurred_at"] = release_credential["freeze_at"]
    result = prospective_evidence.collect_immediate_retrospective(
        release_credential,
        lambda: custody,
        collected_at="2026-07-16T02:00:00Z",
        custodian="human-custodian-01",
    )
    assert result["facts"][0]["classification"] == "immediate_fact"
    assert result["facts"][0]["scorable"] is True


def test_unknown_relative_time_cannot_hide_a_timestamped_fact(
    release_credential: dict,
) -> None:
    custody = _custody_payload(release_credential["case_id"])
    custody["facts"][0]["relative_time"] = "unknown"
    with pytest.raises(ValueError, match="unknown|occurred_at|conflict"):
        prospective_evidence.collect_immediate_retrospective(
            release_credential,
            lambda: custody,
            collected_at="2026-07-16T02:00:00Z",
            custodian="human-custodian-01",
        )


def test_published_label_identity_cannot_be_reused_by_another_artifact(
    release_credential: dict,
) -> None:
    custody = _custody_payload(release_credential["case_id"])
    first = prospective_evidence.collect_immediate_retrospective(
        release_credential,
        lambda: copy.deepcopy(custody),
        collected_at="2026-07-16T02:00:00Z",
        custodian="human-custodian-01",
    )
    publish_new_json(
        Path(first["artifact_path"]),
        {key: value for key, value in first.items() if key != "artifact_sha256"},
        dry_run=False,
    )

    with pytest.raises(
        ValueError, match="duplicate label identity|already exists|global"
    ):
        prospective_evidence.collect_immediate_retrospective(
            release_credential,
            lambda: copy.deepcopy(custody),
            collected_at="2026-07-16T03:00:00Z",
            custodian="human-custodian-01",
        )


def test_bind_keeps_unreviewed_high_risk_immediate_label_unscorable(
    release_credential: dict,
) -> None:
    unbound = prospective_evidence.collect_immediate_retrospective(
        release_credential,
        lambda: _custody_payload(
            release_credential["case_id"],
            facts=[
                {
                    "task_id": "wealth.debt",
                    "label": "occurred",
                    "occurred_at": "2026-07-15T12:00:00Z",
                    "relative_time": "before_or_at_freeze",
                    "source_refs": ["custody://structured-interview/high-risk"],
                }
            ],
        ),
        collected_at="2026-07-16T02:00:00Z",
        custodian="human-custodian-01",
    )
    bound = prospective_evidence.bind_immediate_labels(unbound)

    assert bound["facts"][0]["scorable"] is False
    assert bound["facts"][0]["review_status"] == "pending_independent_dual_review"
    assert bound["scorable_label_count"] == 0


def _final_high_risk_label(
    *,
    case_id: str,
    task_id: str,
    evidence_class: str,
    label_identity: str,
    label: str = "occurred",
) -> dict:
    return {
        "status": "GO",
        "reason": "dual_review_agreement",
        "label": {
            "case_id": case_id,
            "task_id": task_id,
            "label": label,
            "observed_at": "2026-10-01T00:00:00Z",
            "source": "high-risk-review://sha256:" + "f" * 64,
            "confidence_grade": "A",
            "quantifiable": True,
            "conflict_state": "none",
            "reviewer": "human-reviewer-a+human-reviewer-b",
            "observation_sha256": "a" * 64,
            "evidence_class": evidence_class,
            "label_identity": label_identity,
            "review_packet_sha256": ["b" * 64, "c" * 64],
        },
        "reviews": [{"rationale": "A"}, {"rationale": "B"}],
        "adjudication": None,
    }


def test_reviewed_high_risk_immediate_becomes_scorable_without_cross_ledger_reuse(
    release_credential: dict,
    tmp_path: Path,
) -> None:
    unbound = prospective_evidence.collect_immediate_retrospective(
        release_credential,
        lambda: _custody_payload(
            release_credential["case_id"],
            facts=[
                {
                    "task_id": "wealth.debt",
                    "label": "occurred",
                    "occurred_at": "2026-07-15T12:00:00Z",
                    "relative_time": "before_or_at_freeze",
                    "source_refs": ["custody://structured-interview/high-risk"],
                }
            ],
        ),
        collected_at="2026-07-16T02:00:00Z",
        custodian="human-custodian-01",
    )
    publish_new_json(
        Path(unbound["artifact_path"]),
        {key: value for key, value in unbound.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    bound = prospective_evidence.bind_immediate_labels(unbound)
    publish_new_json(
        Path(bound["artifact_path"]),
        {key: value for key, value in bound.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    bound = _read(Path(bound["artifact_path"]))
    identity = bound["facts"][0]["label_identity"]
    final = _final_high_risk_label(
        case_id=bound["case_id"],
        task_id="wealth.debt",
        evidence_class="prediction_first_immediate_retrospective",
        label_identity=identity,
    )
    final["label"]["observation_sha256"] = bound["artifact_sha256"]
    review_paths = [tmp_path / "review-a.json", tmp_path / "review-b.json"]
    for index, path in enumerate(review_paths):
        path.write_text(
            json.dumps(
                {
                    "schema_version": "school-capability-high-risk-review/v2",
                    "review_packet_sha256": final["label"]["review_packet_sha256"][
                        index
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    final_path = tmp_path / "finalization.json"
    final_payload = {
        "schema_version": "school-capability-high-risk-finalization/v2",
        "created_at": "2026-10-01T00:00:00Z",
        "artifact_path": final_path.as_posix(),
        "parents": [
            {
                "artifact_path": path.as_posix(),
                "artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in review_paths
        ],
        "result": final,
    }
    publish_new_json(final_path, final_payload, dry_run=False)

    reviewed = apply_high_risk_final_label(bound, _read(final_path))

    assert reviewed["facts"][0]["scorable"] is True
    assert reviewed["facts"][0]["review_status"] == "approved_independent_dual_review"
    assert reviewed["scorable_label_count"] == 1
    assert reviewed["facts"][0]["review_lineage"]["label_identity"] == identity

    future = _final_high_risk_label(
        case_id=bound["case_id"],
        task_id="wealth.debt",
        evidence_class="future_observation",
        label_identity=identity,
    )
    with pytest.raises(
        ValueError, match="evidence class|ledger|identity|actual|artifact"
    ):
        apply_high_risk_final_label(bound, future)


def test_high_risk_apply_rejects_forged_dict_without_actual_bound_and_final_parents(
    release_credential: dict,
) -> None:
    unbound = prospective_evidence.collect_immediate_retrospective(
        release_credential,
        lambda: _custody_payload(
            release_credential["case_id"],
            facts=[
                {
                    "task_id": "wealth.debt",
                    "label": "occurred",
                    "occurred_at": "2026-07-15T12:00:00Z",
                    "relative_time": "before_or_at_freeze",
                    "source_refs": ["custody://structured-interview/high-risk"],
                }
            ],
        ),
        collected_at="2026-07-16T02:00:00Z",
        custodian="human-custodian-01",
    )
    bound = prospective_evidence.bind_immediate_labels(unbound)
    forged = _final_high_risk_label(
        case_id=bound["case_id"],
        task_id="wealth.debt",
        evidence_class="prediction_first_immediate_retrospective",
        label_identity=bound["facts"][0]["label_identity"],
    )

    with pytest.raises(
        (ValueError, ContaminationError), match="actual|artifact|parent|sealed"
    ):
        apply_high_risk_final_label(bound, forged)


@pytest.mark.parametrize("status,grade", [("HOLD", "A"), ("GO", "B")])
def test_pending_high_risk_stays_unscorable_without_valid_a_final(
    release_credential: dict,
    status: str,
    grade: str,
) -> None:
    unbound = prospective_evidence.collect_immediate_retrospective(
        release_credential,
        lambda: _custody_payload(
            release_credential["case_id"],
            facts=[
                {
                    "task_id": "wealth.debt",
                    "label": "occurred",
                    "occurred_at": "2026-07-15T12:00:00Z",
                    "relative_time": "before_or_at_freeze",
                    "source_refs": ["custody://structured-interview/high-risk"],
                }
            ],
        ),
        collected_at="2026-07-16T02:00:00Z",
        custodian="human-custodian-01",
    )
    bound = prospective_evidence.bind_immediate_labels(unbound)
    final = _final_high_risk_label(
        case_id=bound["case_id"],
        task_id="wealth.debt",
        evidence_class="prediction_first_immediate_retrospective",
        label_identity=bound["facts"][0]["label_identity"],
    )
    final["status"] = status
    final["label"]["confidence_grade"] = grade
    with pytest.raises(ValueError, match="A-grade|GO"):
        apply_high_risk_final_label(bound, final)


def _future_parents(freeze_chain: dict) -> tuple[dict, dict]:
    frozen = _read(freeze_chain["frozen_run_path"])
    question_ref = next(
        parent
        for parent in frozen["parents"]
        if "future-question-registration" in parent["artifact_path"]
    )
    return validate_parent_ref(ArtifactRef(**question_ref)), frozen


def _future_observation(question: dict, label: str = "occurred") -> dict:
    return {
        "future_task_id": question["future_task_id"],
        "label": label,
        "observed_at": "2026-08-01T00:00:00Z"
        if label == "occurred"
        else question["observation_window"]["end_at"],
        "source_refs": ["custody://structured-interview/future-follow-up/001"],
        "source_coverage": {
            "start_at": question["observation_window"]["start_at"],
            "end_at": question["observation_window"]["end_at"],
        },
        "contact_state": "available",
        "conflict_state": "none",
    }


def test_future_observation_reloads_and_binds_actual_question_and_frozen_parent(
    freeze_chain: dict,
) -> None:
    question, frozen = _future_parents(freeze_chain)
    result = collect_future_observation(
        question,
        frozen,
        _future_observation(question),
        collected_at="2026-08-01T00:00:01Z",
    )

    assert result["schema_version"] == "prospective-future-observation-unbound/v1"
    assert result["evidence_class"] == "future_observation"
    assert result["observation"]["label"] == "occurred"
    assert result["observation"]["scorable"] is True
    assert result["parents"] == [
        {
            "artifact_path": question["artifact_path"],
            "artifact_sha256": question["artifact_sha256"],
        },
        {
            "artifact_path": frozen["artifact_path"],
            "artifact_sha256": frozen["artifact_sha256"],
        },
    ]
    immediate_identity = canonical_artifact_sha256(
        {
            "case_id": question["case_id"],
            "evidence_class": "prediction_first_immediate_retrospective",
            "future_task_id": question["future_task_id"],
            "observed_at": result["observation"]["observed_at"],
        }
    )
    assert result["label_identity"] != immediate_identity

    with pytest.raises(
        (ValueError, ContaminationError), match="question|parent|binding|supplied|drift"
    ):
        collect_future_observation(
            {**question, "question_text_redacted": "tampered"},
            frozen,
            _future_observation(question),
            collected_at="2026-08-01T00:00:01Z",
        )


def test_future_window_semantics_and_forced_no_data(freeze_chain: dict) -> None:
    question, frozen = _future_parents(freeze_chain)
    before_freeze = _future_observation(question)
    before_freeze["observed_at"] = "2026-07-15T23:59:59Z"
    after_window = _future_observation(question)
    after_window["observed_at"] = "2026-10-16T00:00:01Z"
    early_negative = _future_observation(question, "not_observed")
    early_negative["observed_at"] = "2026-08-01T00:00:00Z"
    incomplete_negative = _future_observation(question, "not_observed")
    incomplete_negative["source_coverage"]["start_at"] = "2026-07-17T00:00:00Z"

    for observation, message in (
        (before_freeze, "freeze|window"),
        (after_window, "window"),
        (early_negative, "window has not matured"),
        (incomplete_negative, "coverage|window"),
    ):
        with pytest.raises(ValueError, match=message):
            collect_future_observation(
                question,
                frozen,
                observation,
                collected_at="2026-10-16T00:00:01Z",
            )

    for mutation in (
        {"contact_state": "lost_contact"},
        {"conflict_state": "conflicting_sources"},
        {"observed_at": None},
    ):
        observation = {**_future_observation(question), **mutation}
        result = collect_future_observation(
            question,
            frozen,
            observation,
            collected_at="2026-08-01T00:00:01Z",
        )
        assert result["observation"]["label"] == "no_data"
        assert result["observation"]["scorable"] is False


def test_future_observation_rejects_invalid_time_label_and_global_duplicate(
    freeze_chain: dict,
) -> None:
    question, frozen = _future_parents(freeze_chain)
    observation = _future_observation(question)
    for label in ("yes", "immediate_fact", "unknown"):
        with pytest.raises(ValueError, match="label"):
            collect_future_observation(
                question,
                frozen,
                {**observation, "label": label},
                collected_at="2026-08-01T00:00:01Z",
            )
    with pytest.raises(ValueError, match="collected_at|observed_at"):
        collect_future_observation(
            question,
            frozen,
            observation,
            collected_at="2026-07-31T23:59:59Z",
        )

    first = collect_future_observation(
        question,
        frozen,
        observation,
        collected_at="2026-08-01T00:00:01Z",
    )
    publish_new_json(
        Path(first["artifact_path"]),
        {key: value for key, value in first.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    with pytest.raises(ValueError, match="duplicate label identity|already exists"):
        collect_future_observation(
            question,
            frozen,
            copy.deepcopy(observation),
            collected_at="2026-08-02T00:00:00Z",
        )


def test_v2_release_can_anchor_immediate_case_completion(freeze_chain: dict) -> None:
    frozen = _read(freeze_chain["frozen_run_path"])
    release = build_feedback_release_credential(
        frozen,
        created_at="2026-07-16T01:05:00Z",
    )
    publish_new_json(
        Path(release["artifact_path"]),
        {key: value for key, value in release.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    release = _read(Path(release["artifact_path"]))
    immediate = prospective_evidence.collect_immediate_retrospective(
        release,
        lambda: _custody_payload(release["case_id"]),
        collected_at="2026-07-16T02:00:00Z",
        custodian="human-custodian-01",
    )
    publish_new_json(
        Path(immediate["artifact_path"]),
        {key: value for key, value in immediate.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    bound = prospective_evidence.bind_immediate_labels(
        _read(Path(immediate["artifact_path"])),
    )
    publish_new_json(
        Path(bound["artifact_path"]),
        {key: value for key, value in bound.items() if key != "artifact_sha256"},
        dry_run=False,
    )

    completion = build_case_completion(
        freeze_verification=release,
        immediate_bound=_read(Path(bound["artifact_path"])),
        future_bound=None,
        stopped_incident=None,
        created_at="2026-07-16T02:00:01Z",
    )

    assert (
        completion["retrospective_completion_status"]
        == "CASE_COMPLETE_FOR_RETROSPECTIVE"
    )
    assert completion["future_completion_status"] == "PENDING"
    assert completion["parents"][0] == {
        "artifact_path": release["artifact_path"],
        "artifact_sha256": release["artifact_sha256"],
    }


def test_v2_release_completion_propagates_one_exact_operation_authority(
    freeze_chain: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frozen = _read(freeze_chain["frozen_run_path"])
    release = build_feedback_release_credential(
        frozen,
        created_at="2026-07-16T01:05:00Z",
    )
    publish_new_json(
        Path(release["artifact_path"]),
        {key: value for key, value in release.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    release = _read(Path(release["artifact_path"]))
    expected_authority = prospective_artifacts._repository_authority()
    resolver_calls = 0
    observed: list[object] = []
    original_release = getattr(
        prospective_evidence, "_validate_release_credential_with_authority", None
    )
    original_actual = prospective_evidence._actual_supplied_artifact
    original_tree = prospective_evidence._validate_parent_tree

    def operation_start_authority() -> object:
        nonlocal resolver_calls
        resolver_calls += 1
        if resolver_calls != 1:
            raise AssertionError(
                "completion downstream reacquired repository authority"
            )
        return expected_authority

    def release_probe(
        document: dict, *, authority: object
    ) -> tuple[dict[str, object], dict[str, object]]:
        assert authority is expected_authority
        observed.append(authority)
        assert original_release is not None
        return original_release(document, authority=authority)

    def actual_probe(
        document: dict, description: str, *, authority: object
    ) -> dict[str, object]:
        assert authority is expected_authority
        observed.append(authority)
        return original_actual(document, description, authority=authority)

    def tree_probe(
        document: dict,
        *,
        authority: object,
        visited: set[tuple[str, str]] | None = None,
    ) -> None:
        assert authority is expected_authority
        observed.append(authority)
        original_tree(document, authority=authority, visited=visited)

    monkeypatch.setattr(
        prospective_evidence, "_repository_authority", operation_start_authority
    )
    monkeypatch.setattr(
        prospective_evidence,
        "_validate_release_credential_with_authority",
        release_probe,
        raising=False,
    )
    monkeypatch.setattr(prospective_evidence, "_actual_supplied_artifact", actual_probe)
    monkeypatch.setattr(prospective_evidence, "_validate_parent_tree", tree_probe)

    completion = build_case_completion(
        freeze_verification=release,
        immediate_bound=None,
        future_bound=None,
        stopped_incident=None,
        created_at="2026-07-16T01:05:01Z",
    )

    assert completion["parents"][0]["artifact_sha256"] == release["artifact_sha256"]
    assert resolver_calls == 1
    assert observed
    assert all(authority is expected_authority for authority in observed)


def test_case_completion_has_separate_ledgers_and_no_completed_boolean(
    freeze_chain: dict,
) -> None:
    verification = _verify(freeze_chain)
    publish_new_json(
        Path(verification["artifact_path"]),
        {key: value for key, value in verification.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    actual_verification = _read(Path(verification["artifact_path"]))
    pending = build_case_completion(
        freeze_verification=actual_verification,
        immediate_bound=None,
        future_bound=None,
        stopped_incident=None,
        created_at="2026-07-16T01:00:01Z",
    )
    assert pending["retrospective_completion_status"] == "PENDING"
    assert pending["future_completion_status"] == "PENDING"
    assert "completed" not in pending
    assert pending["parents"] == [
        {
            "artifact_path": actual_verification["artifact_path"],
            "artifact_sha256": actual_verification["artifact_sha256"],
        }
    ]

    with pytest.raises(ContaminationError, match="STOP"):
        build_case_completion(
            freeze_verification=actual_verification,
            immediate_bound=None,
            future_bound=None,
            stopped_incident={"status": "STOP"},
            created_at="2026-07-16T01:00:01Z",
        )
    with pytest.raises(ValueError, match="created_at|verification"):
        build_case_completion(
            freeze_verification=actual_verification,
            immediate_bound=None,
            future_bound=None,
            stopped_incident=None,
            created_at="2026-07-16T00:59:59Z",
        )


def test_completion_rejects_unbound_evidence_artifacts(
    freeze_chain: dict,
    release_credential: dict,
) -> None:
    verification_path = Path(release_credential["parents"][0]["artifact_path"])
    actual_verification = _read(verification_path)
    immediate = prospective_evidence.collect_immediate_retrospective(
        release_credential,
        lambda: _custody_payload(release_credential["case_id"]),
        collected_at="2026-07-16T02:00:00Z",
        custodian="human-custodian-01",
    )
    publish_new_json(
        Path(immediate["artifact_path"]),
        {key: value for key, value in immediate.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    question, frozen = _future_parents(freeze_chain)
    future = collect_future_observation(
        question,
        frozen,
        _future_observation(question),
        collected_at="2026-08-01T00:00:01Z",
    )
    publish_new_json(
        Path(future["artifact_path"]),
        {key: value for key, value in future.items() if key != "artifact_sha256"},
        dry_run=False,
    )

    with pytest.raises((ValueError, ContaminationError), match="bound|schema|review"):
        build_case_completion(
            freeze_verification=actual_verification,
            immediate_bound=_read(Path(immediate["artifact_path"])),
            future_bound=None,
            stopped_incident=None,
            created_at="2026-08-01T00:00:02Z",
        )
    with pytest.raises((ValueError, ContaminationError), match="bound|schema|review"):
        build_case_completion(
            freeze_verification=actual_verification,
            immediate_bound=None,
            future_bound=_read(Path(future["artifact_path"])),
            stopped_incident=None,
            created_at="2026-08-01T00:00:02Z",
        )


def test_future_collected_at_cannot_claim_a_time_later_than_now(
    freeze_chain: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        prospective_evidence,
        "_now_utc",
        lambda: prospective_evidence._utc("2026-07-16T17:00:00Z", "test clock"),
    )
    question, frozen = _future_parents(freeze_chain)
    observation = _future_observation(question)

    with pytest.raises(ValueError, match="current|future|collected_at"):
        collect_future_observation(
            question,
            frozen,
            observation,
            collected_at="2026-08-01T00:00:01Z",
        )


def test_conflict_forces_no_data_before_negative_coverage_scoring_gates(
    freeze_chain: dict,
) -> None:
    question, frozen = _future_parents(freeze_chain)
    observation = _future_observation(question, "not_observed")
    observation["conflict_state"] = "conflicting_sources"
    observation["observed_at"] = "2026-08-01T00:00:00Z"
    observation["source_coverage"] = {"start_at": "forged", "end_at": "forged"}

    result = collect_future_observation(
        question,
        frozen,
        observation,
        collected_at="2026-08-01T00:00:01Z",
    )

    assert result["observation"]["label"] == "no_data"
    assert result["observation"]["scorable"] is False
    assert result["observation"]["no_data_reason"] == "conflicting_sources"


def test_not_observed_coverage_must_bind_registered_source_requirements(
    freeze_chain: dict,
) -> None:
    question, frozen = _future_parents(freeze_chain)
    observation = _future_observation(question, "not_observed")
    observation["source_refs"] = ["custody://unregistered-source/forged"]

    with pytest.raises(ValueError, match="source|coverage|requirement"):
        collect_future_observation(
            question,
            frozen,
            observation,
            collected_at="2026-10-16T00:00:01Z",
        )


def test_future_high_risk_is_pending_dual_review_and_cannot_complete(
    freeze_chain: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    question, frozen = _future_parents(freeze_chain)
    monkeypatch.setattr(
        prospective_evidence,
        "_future_task",
        lambda frozen_parent, task_id: {"task_id": task_id, "high_risk": True},
    )

    result = collect_future_observation(
        question,
        frozen,
        _future_observation(question),
        collected_at="2026-08-01T00:00:01Z",
    )

    assert result["observation"]["high_risk"] is True
    assert result["observation"]["scorable"] is False
    assert result["observation"]["review_status"] == "pending_independent_dual_review"


def test_future_bind_cli_is_canonical_create_only(freeze_chain: dict) -> None:
    question, frozen = _future_parents(freeze_chain)
    unbound = collect_future_observation(
        question,
        frozen,
        _future_observation(question),
        collected_at="2026-08-01T00:00:01Z",
    )
    publish_new_json(
        Path(unbound["artifact_path"]),
        {key: value for key, value in unbound.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    output = Path(unbound["artifact_path"]).with_name(
        f"{question['case_id']}--future-observation-bound--v001.json"
    )
    command = [
        sys.executable,
        "-m",
        "tools.school_capability_dataset",
        "bind-future-observation",
        "--unbound",
        unbound["artifact_path"],
        "--out",
        str(output),
    ]
    environment = {**os.environ, "PYTHONUTF8": "1"}

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
    assert (
        json.loads(dry.stdout)["schema_version"]
        == "prospective-future-observation-bound/v1"
    )
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
    assert output.read_bytes() == original


def test_completion_rejects_unreadable_or_foreign_stop_incident(
    freeze_chain: dict,
    tmp_path: Path,
) -> None:
    verification = _verify(freeze_chain)
    publish_new_json(
        Path(verification["artifact_path"]),
        {key: value for key, value in verification.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    forged_path = tmp_path / "missing-stop.json"
    forged = {
        "schema_version": "prospective-stop-incident/v1",
        "case_id": verification["case_id"],
        "subject_id_hash": verification["subject_id_hash"],
        "artifact_path": forged_path.as_posix(),
        "artifact_sha256": "f" * 64,
        "status": "STOP",
    }

    with pytest.raises(
        (ValueError, ContaminationError), match="parent|drift|unreadable|STOP"
    ):
        build_case_completion(
            freeze_verification=_read(Path(verification["artifact_path"])),
            immediate_bound=None,
            future_bound=None,
            stopped_incident=forged,
            created_at="2026-07-16T01:00:01Z",
        )


def test_future_no_data_cannot_complete_case(freeze_chain: dict) -> None:
    question, frozen = _future_parents(freeze_chain)
    verification = _verify(freeze_chain)
    publish_new_json(
        Path(verification["artifact_path"]),
        {key: value for key, value in verification.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    no_data_input = {**_future_observation(question), "contact_state": "lost_contact"}
    future = collect_future_observation(
        question,
        frozen,
        no_data_input,
        collected_at="2026-08-01T00:00:01Z",
    )
    publish_new_json(
        Path(future["artifact_path"]),
        {key: value for key, value in future.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    bound = prospective_evidence.bind_future_observation(
        _read(Path(future["artifact_path"]))
    )
    publish_new_json(
        Path(bound["artifact_path"]),
        {key: value for key, value in bound.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    completion = build_case_completion(
        freeze_verification=_read(Path(verification["artifact_path"])),
        immediate_bound=None,
        future_bound=_read(Path(bound["artifact_path"])),
        stopped_incident=None,
        created_at="2026-08-01T00:00:02Z",
    )
    assert completion["future_completion_status"] == "PENDING"


def test_future_completion_chain_propagates_one_exact_operation_authority(
    freeze_chain: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    question, frozen = _future_parents(freeze_chain)
    verification = _verify(freeze_chain)
    publish_new_json(
        Path(verification["artifact_path"]),
        {key: value for key, value in verification.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    future = collect_future_observation(
        question,
        frozen,
        _future_observation(question),
        collected_at="2026-08-01T00:00:01Z",
    )
    publish_new_json(
        Path(future["artifact_path"]),
        {key: value for key, value in future.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    bound = prospective_evidence.bind_future_observation(
        _read(Path(future["artifact_path"]))
    )
    publish_new_json(
        Path(bound["artifact_path"]),
        {key: value for key, value in bound.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    expected_authority = prospective_artifacts._repository_authority()
    resolver_calls = 0
    observed: list[object] = []
    original_actual = prospective_evidence._actual_supplied_artifact
    original_tree = prospective_evidence._validate_parent_tree
    original_future_parents = prospective_evidence._validated_future_parents
    original_future_chain = prospective_evidence._validate_future_completion_chain

    def operation_start_authority() -> object:
        nonlocal resolver_calls
        resolver_calls += 1
        if resolver_calls != 1:
            raise AssertionError(
                "completion downstream reacquired repository authority"
            )
        return expected_authority

    def exact(authority: object) -> None:
        assert authority is expected_authority
        observed.append(authority)

    def actual_probe(
        document: dict, description: str, *, authority: object
    ) -> dict[str, object]:
        exact(authority)
        return original_actual(document, description, authority=authority)

    def tree_probe(
        document: dict,
        *,
        authority: object,
        visited: set[tuple[str, str]] | None = None,
    ) -> None:
        exact(authority)
        original_tree(document, authority=authority, visited=visited)

    def future_parents_probe(
        registration: dict, frozen_run: dict, *, authority: object
    ) -> tuple[dict[str, object], dict[str, object]]:
        exact(authority)
        return original_future_parents(registration, frozen_run, authority=authority)

    def future_chain_probe(document: dict, *, authority: object) -> None:
        exact(authority)
        original_future_chain(document, authority=authority)

    monkeypatch.setattr(
        prospective_evidence, "_repository_authority", operation_start_authority
    )
    monkeypatch.setattr(prospective_evidence, "_actual_supplied_artifact", actual_probe)
    monkeypatch.setattr(prospective_evidence, "_validate_parent_tree", tree_probe)
    monkeypatch.setattr(
        prospective_evidence, "_validated_future_parents", future_parents_probe
    )
    monkeypatch.setattr(
        prospective_evidence, "_validate_future_completion_chain", future_chain_probe
    )

    completion = build_case_completion(
        freeze_verification=_read(Path(verification["artifact_path"])),
        immediate_bound=None,
        future_bound=_read(Path(bound["artifact_path"])),
        stopped_incident=None,
        created_at="2026-08-01T00:00:02Z",
    )

    assert completion["future_completion_status"] == "CASE_COMPLETE_FOR_FUTURE"
    assert resolver_calls == 1
    assert observed
    assert all(authority is expected_authority for authority in observed)


def test_completion_rejects_hand_forged_future_bound_without_registered_freeze_chain(
    freeze_chain: dict,
) -> None:
    verification = _verify(freeze_chain)
    publish_new_json(
        Path(verification["artifact_path"]),
        {key: value for key, value in verification.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    question, _ = _future_parents(freeze_chain)
    forged_path = Path(question["artifact_path"]).with_name(
        f"{question['case_id']}--future-observation-bound--v001.json"
    )
    publish_new_json(
        forged_path,
        {
            "schema_version": "prospective-future-observation-bound/v1",
            "case_id": question["case_id"],
            "subject_id_hash": question["subject_id_hash"],
            "created_at": "2026-08-01T00:00:01Z",
            "artifact_path": forged_path.as_posix(),
            "parents": [],
            "evidence_class": "future_observation",
            "label_identity": "f" * 64,
            "observation": {
                "future_task_id": question["future_task_id"],
                "label": "occurred",
                "scorable": True,
                "observed_at": "2026-08-01T00:00:00Z",
                "collected_at": "2026-08-01T00:00:01Z",
                "observation_window": dict(question["observation_window"]),
            },
        },
        dry_run=False,
    )

    with pytest.raises(
        (ValueError, ContaminationError),
        match="future|parent|lineage|unbound|registration|frozen",
    ):
        build_case_completion(
            freeze_verification=_read(Path(verification["artifact_path"])),
            immediate_bound=None,
            future_bound=_read(forged_path),
            stopped_incident=None,
            created_at="2026-08-01T00:00:02Z",
        )


def test_future_and_completion_clis_are_canonical_create_only_and_dry_run(
    freeze_chain: dict,
    tmp_path: Path,
) -> None:
    question, frozen = _future_parents(freeze_chain)
    observation_path = tmp_path / "future-observation-input.json"
    cli_observation = _future_observation(question)
    cli_observation["observed_at"] = "2026-07-16T17:00:00Z"
    _write(observation_path, cli_observation)
    future_output = single_case_artifact_path(
        tmp_path, question["case_id"], "future-observation-unbound", 1
    )
    future_command = [
        sys.executable,
        "-m",
        "tools.school_capability_dataset",
        "collect-future-observation",
        "--future-question",
        question["artifact_path"],
        "--frozen-run",
        frozen["artifact_path"],
        "--observation",
        str(observation_path),
        "--collected-at",
        "2026-07-16T17:00:01Z",
        "--out",
        str(future_output),
    ]
    environment = {**os.environ, "PYTHONUTF8": "1"}
    dry_future = subprocess.run(
        [*future_command, "--dry-run"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )
    assert dry_future.returncode == 0, dry_future.stderr
    assert not future_output.exists()
    assert json.loads(dry_future.stdout)["evidence_class"] == "future_observation"
    created_future = subprocess.run(
        future_command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )
    assert created_future.returncode == 0, created_future.stderr
    future_bytes = future_output.read_bytes()
    duplicate_future = subprocess.run(
        future_command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )
    assert duplicate_future.returncode != 0
    assert future_output.read_bytes() == future_bytes

    verification = _verify(freeze_chain)
    publish_new_json(
        Path(verification["artifact_path"]),
        {key: value for key, value in verification.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    completion_output = single_case_artifact_path(
        tmp_path, verification["case_id"], "case-completion", 1
    )
    bound_future = prospective_evidence.bind_future_observation(_read(future_output))
    bound_future_output = Path(bound_future["artifact_path"])
    publish_new_json(
        bound_future_output,
        {key: value for key, value in bound_future.items() if key != "artifact_sha256"},
        dry_run=False,
    )
    completion_command = [
        sys.executable,
        "-m",
        "tools.school_capability_dataset",
        "build-case-completion",
        "--freeze-verification",
        verification["artifact_path"],
        "--future-bound",
        str(bound_future_output),
        "--created-at",
        "2026-07-16T17:00:02Z",
        "--out",
        str(completion_output),
    ]
    dry_completion = subprocess.run(
        [*completion_command, "--dry-run"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )
    assert dry_completion.returncode == 0, dry_completion.stderr
    assert not completion_output.exists()
    dry_document = json.loads(dry_completion.stdout)
    assert dry_document["future_completion_status"] == "CASE_COMPLETE_FOR_FUTURE"
    assert "completed" not in dry_document
    created_completion = subprocess.run(
        completion_command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )
    assert created_completion.returncode == 0, created_completion.stderr
    completion_bytes = completion_output.read_bytes()
    duplicate_completion = subprocess.run(
        completion_command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )
    assert duplicate_completion.returncode != 0
    assert completion_output.read_bytes() == completion_bytes


def test_future_cli_does_not_require_immediate_release_or_feedback(
    freeze_chain: dict, tmp_path: Path
) -> None:
    question, frozen = _future_parents(freeze_chain)
    observation_path = tmp_path / "future.json"
    cli_observation = _future_observation(question)
    cli_observation["observed_at"] = "2026-07-16T17:00:00Z"
    _write(observation_path, cli_observation)
    parser = __import__(
        "tools.school_capability_dataset", fromlist=["_parser"]
    )._parser()
    future_action = next(
        action
        for action in parser._subparsers._group_actions[0]
        .choices["collect-future-observation"]
        ._actions
        if action.dest == "future_question"
    )
    assert future_action.required is True
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.school_capability_dataset",
            "collect-future-observation",
            "--future-question",
            question["artifact_path"],
            "--frozen-run",
            frozen["artifact_path"],
            "--observation",
            str(observation_path),
            "--collected-at",
            "2026-07-16T17:00:01Z",
            "--out",
            str(tmp_path / "noncanonical.json"),
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    assert result.returncode == 0, result.stderr
    assert "release" not in result.stderr.lower()
    assert "feedback" not in result.stderr.lower()


def test_collect_cli_rejects_noncanonical_formal_output_path(
    release_credential: dict,
    tmp_path: Path,
) -> None:
    custody_path = tmp_path / "custody.json"
    _write(custody_path, _custody_payload(release_credential["case_id"]))
    noncanonical = tmp_path / "arbitrary.json"
    environment = {**os.environ, "PYTHONUTF8": "1"}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.school_capability_dataset",
            "collect-immediate-retrospective",
            "--release",
            release_credential["artifact_path"],
            "--custody-input",
            str(custody_path),
            "--collected-at",
            "2026-07-16T02:00:00Z",
            "--custodian",
            "human-custodian-01",
            "--out",
            str(noncanonical),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=environment,
    )

    assert result.returncode != 0
    assert (
        "canonical" in result.stderr.lower() or "artifact_path" in result.stderr.lower()
    )
    assert not noncanonical.exists()
