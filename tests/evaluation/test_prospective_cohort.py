from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from engine.evaluation import prospective_artifacts
from engine.evaluation.prospective_artifacts import ArtifactRef, publish_new_json
from engine.evaluation.prospective_gates import (
    CohortHoldError,
    build_cohort_manifest,
    cohort_output_dir,
    verify_cohort_manifest,
)


@pytest.fixture(autouse=True)
def _repository_authority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path.absolute()
    state = root / "META" / "project-state.json"
    contract = (
        root
        / ".omo"
        / "drafts"
        / "w2-c4-governance-promotion-remediation-r3-admission-contract-2026-08-08.md"
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


CREATED_AT = "2026-08-01T00:00:00Z"
GATE_IDS = [
    "prediction_capability_candidate_gate_v1",
    "future_empirical_gate_v1",
    "historical_platform_baseline_2026_07_15",
]


def _raw_ref(path: Path) -> ArtifactRef:
    return ArtifactRef(path.as_posix(), hashlib.sha256(path.read_bytes()).hexdigest())


def _historical_refs(tmp_path: Path) -> list[ArtifactRef]:
    md = tmp_path / "META" / "six-month-platform-gate-2026-07-15.md"
    js = tmp_path / "META" / "six-month-platform-gate-2026-07-15.json"
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text("# immutable baseline\n", encoding="utf-8")
    js.write_text('{"status":"HOLD"}\n', encoding="utf-8")
    return [_raw_ref(md), _raw_ref(js)]


def _completion(
    root: Path,
    index: int,
    *,
    subject: str | None = None,
    future: bool = False,
    created_at: str = "2026-07-31T00:00:00Z",
) -> Path:
    case_id = f"P-GO-2026-{index:03d}-乾-甲子乙丑丙寅丁卯"
    path = root / case_id / f"{case_id}--case-completion--v001.json"
    subject_hash = subject or hashlib.sha256(f"subject-{index}".encode()).hexdigest()
    immediate_path = path.with_name(
        f"{case_id}--immediate-retrospective-bound--v001.json"
    )
    immediate_payload = {
        "schema_version": "prospective-immediate-retrospective-bound/v1",
        "case_id": case_id,
        "subject_id_hash": subject_hash,
        "created_at": "2026-07-30T00:00:00Z",
        "artifact_path": immediate_path.as_posix(),
        "parents": [],
        "evidence_class": "prediction_first_immediate_retrospective",
    }
    immediate_ref = publish_new_json(immediate_path, immediate_payload, dry_run=False)
    parents = [immediate_ref.__dict__]
    if future:
        future_path = path.with_name(f"{case_id}--future-observation-bound--v001.json")
        future_ref = publish_new_json(
            future_path,
            {
                "schema_version": "prospective-future-observation-bound/v1",
                "case_id": case_id,
                "subject_id_hash": subject_hash,
                "created_at": "2026-07-30T00:00:00Z",
                "artifact_path": future_path.as_posix(),
                "parents": [],
                "evidence_class": "future_observation",
                "label_identity": hashlib.sha256(
                    f"future-{index}".encode()
                ).hexdigest(),
                "observation": {
                    "future_task_id": "career.role_change",
                    "label": "occurred",
                    "scorable": True,
                },
            },
            dry_run=False,
        )
        parents.append(future_ref.__dict__)
    payload = {
        "schema_version": "prospective-case-completion/v1",
        "case_id": case_id,
        "subject_id_hash": subject_hash,
        "created_at": created_at,
        "artifact_path": path.as_posix(),
        "parents": parents,
        "retrospective_completion_status": "CASE_COMPLETE_FOR_RETROSPECTIVE",
        "future_completion_status": "CASE_COMPLETE_FOR_FUTURE" if future else "PENDING",
    }
    publish_new_json(path, payload, dry_run=False)
    return path


def _ten(root: Path, *, future: bool = False) -> list[Path]:
    return [_completion(root, index, future=future) for index in range(1, 11)]


def _stop(root: Path, index: int = 11) -> Path:
    case_id = f"P-GO-2026-{index:03d}-乾-甲子乙丑丙寅丁卯"
    path = root / case_id / f"{case_id}--stop-incident--v001.json"
    subject_hash = hashlib.sha256(f"subject-{index}".encode()).hexdigest()
    verification_path = path.with_name(f"{case_id}--freeze-verification--v001.json")
    verification_payload = {
        "schema_version": "prospective-single-case-freeze-verification/v1",
        "case_id": case_id,
        "subject_id_hash": subject_hash,
        "created_at": "2026-07-30T00:00:00Z",
        "artifact_path": verification_path.as_posix(),
        "parents": [],
        "status": "STOP",
    }
    verification_ref = publish_new_json(
        verification_path, verification_payload, dry_run=False
    )
    payload = {
        "schema_version": "prospective-stop-incident/v1",
        "case_id": case_id,
        "subject_id_hash": subject_hash,
        "created_at": "2026-07-31T00:00:00Z",
        "artifact_path": path.as_posix(),
        "parents": [verification_ref.__dict__],
        "status": "STOP",
    }
    publish_new_json(path, payload, dry_run=False)
    return path


def test_cohort_manifest_contains_only_parent_refs_and_required_metadata(
    tmp_path: Path,
) -> None:
    manifest = build_cohort_manifest(
        _ten(tmp_path / "cases"), _historical_refs(tmp_path), created_at=CREATED_AT
    )

    assert len(manifest["members"]) == 10
    assert all(
        set(parent) == {"artifact_path", "artifact_sha256"}
        for member in manifest["members"]
        for parent in member["parents"].values()
        if parent is not None
    )
    encoded = json.dumps(manifest)
    assert '"completed"' not in encoded
    assert '"labels"' not in encoded
    assert '"predictions"' not in encoded
    assert manifest["gate_ids"] == GATE_IDS
    assert manifest["created_at"] >= max(
        row["parent_created_at"] for row in manifest["members"]
    )
    assert manifest["status"] == "READY_FOR_TASK_10_AGGREGATION"


def test_build_requires_actual_disk_paths_or_explicit_artifact_refs(
    tmp_path: Path,
) -> None:
    paths = _ten(tmp_path / "cases")
    refs = [_raw_ref(path) for path in paths]
    # Sealed artifacts use canonical artifact hashes, not raw-byte hashes.
    refs = [
        ArtifactRef(
            ref.artifact_path,
            json.loads(Path(ref.artifact_path).read_text(encoding="utf-8"))[
                "artifact_sha256"
            ],
        )
        for ref in refs
    ]
    first = build_cohort_manifest(
        paths, _historical_refs(tmp_path), created_at=CREATED_AT
    )
    second = build_cohort_manifest(
        refs, _historical_refs(tmp_path), created_at=CREATED_AT
    )
    assert first == second

    supplied = json.loads(paths[0].read_text(encoding="utf-8"))
    with pytest.raises(TypeError, match="path|ArtifactRef"):
        build_cohort_manifest(
            [supplied, *paths[1:]], _historical_refs(tmp_path), created_at=CREATED_AT
        )


def test_nine_members_hold_without_formal_manifest(tmp_path: Path) -> None:
    paths = [_completion(tmp_path / "cases", index) for index in range(1, 10)]
    with pytest.raises(CohortHoldError, match="9.*10|10.*9") as error:
        build_cohort_manifest(paths, _historical_refs(tmp_path), created_at=CREATED_AT)
    assert error.value.plan["status"] == "HOLD"
    assert error.value.plan["eligible_count"] == 9
    assert error.value.plan["missing_count"] == 1


def test_duplicate_case_or_subject_is_rejected(tmp_path: Path) -> None:
    paths = _ten(tmp_path / "case-duplicate")
    with pytest.raises(ValueError, match="duplicate case"):
        build_cohort_manifest(
            [*paths[:-1], paths[0]],
            _historical_refs(tmp_path / "h1"),
            created_at=CREATED_AT,
        )

    shared = hashlib.sha256(b"same-subject").hexdigest()
    subject_paths = [
        _completion(
            tmp_path / "subject-duplicate",
            index,
            subject=shared if index in {1, 2} else None,
        )
        for index in range(1, 11)
    ]
    with pytest.raises(ValueError, match="duplicate subject"):
        build_cohort_manifest(
            subject_paths, _historical_refs(tmp_path / "h2"), created_at=CREATED_AT
        )


def test_stop_is_audited_but_cannot_fill_tenth_slot(tmp_path: Path) -> None:
    parents = [_completion(tmp_path / "cases", index) for index in range(1, 10)] + [
        _stop(tmp_path / "cases")
    ]
    with pytest.raises(CohortHoldError) as error:
        build_cohort_manifest(
            parents, _historical_refs(tmp_path), created_at=CREATED_AT
        )
    assert error.value.plan["eligible_count"] == 9
    assert error.value.plan["stopped_audit"] == [
        {
            "case_id": "P-GO-2026-011-乾-甲子乙丑丙寅丁卯",
            "subject_id_hash": hashlib.sha256(b"subject-11").hexdigest(),
            "parent": {
                "artifact_path": parents[-1].as_posix(),
                "artifact_sha256": json.loads(parents[-1].read_text(encoding="utf-8"))[
                    "artifact_sha256"
                ],
            },
        }
    ]


def test_member_set_hash_id_and_output_path_are_stable_under_parent_order(
    tmp_path: Path,
) -> None:
    parents = _ten(tmp_path / "cases")
    historical = _historical_refs(tmp_path)
    first = build_cohort_manifest(parents, historical, created_at=CREATED_AT)
    second = build_cohort_manifest(
        list(reversed(parents)), list(reversed(historical)), created_at=CREATED_AT
    )
    assert first == second
    assert (
        cohort_output_dir(Path("META/prospective-go/cohorts"), first)
        .as_posix()
        .endswith(f"{first['cohort_id']}--{first['member_set_sha256'][:12]}")
    )


def test_verify_returns_stop_on_parent_or_historical_byte_drift(tmp_path: Path) -> None:
    parents = _ten(tmp_path / "cases")
    historical = _historical_refs(tmp_path)
    manifest = build_cohort_manifest(parents, historical, created_at=CREATED_AT)
    assert verify_cohort_manifest(manifest)["status"] == "VERIFIED"

    parents[0].write_text("{}\n", encoding="utf-8")
    stopped = verify_cohort_manifest(manifest)
    assert stopped["status"] == "STOP"
    assert stopped["drifted_parents"]


def test_historical_refs_must_bind_exact_current_two_files_by_actual_byte_hash(
    tmp_path: Path,
) -> None:
    parents = _ten(tmp_path / "cases")
    historical = _historical_refs(tmp_path)
    wrong = ArtifactRef(historical[0].artifact_path, "0" * 64)
    with pytest.raises(ValueError, match="historical.*hash|hash.*historical"):
        build_cohort_manifest(parents, [wrong, historical[1]], created_at=CREATED_AT)
    other = tmp_path / "META" / "old-platform-gate.md"
    other.write_text("old", encoding="utf-8")
    with pytest.raises(ValueError, match="historical.*two|baseline"):
        build_cohort_manifest(
            parents, [_raw_ref(other), historical[1]], created_at=CREATED_AT
        )


def _build_command(
    parents: list[Path], historical: list[ArtifactRef], out: Path
) -> list[str]:
    command = [sys.executable, "-m", "tools.school_capability_cohort", "build"]
    for parent in parents:
        command.extend(("--completion", str(parent)))
    by_suffix = {
        Path(ref.artifact_path).suffix: ref.artifact_path for ref in historical
    }
    command.extend(
        (
            "--historical-md",
            by_suffix[".md"],
            "--historical-json",
            by_suffix[".json"],
            "--out-dir",
            str(out),
            "--created-at",
            CREATED_AT,
        )
    )
    return command


def test_cli_dry_run_hold_and_create_then_verify_existing(tmp_path: Path) -> None:
    parents = _ten(tmp_path / "cases")
    historical = _historical_refs(tmp_path)
    root = tmp_path / "cohorts"
    command = _build_command(parents, historical, root)

    dry = subprocess.run(
        [*command, "--dry-run"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert dry.returncode == 0, dry.stderr
    dry_result = json.loads(dry.stdout)
    assert dry_result["status"] == "DRY_RUN"
    assert not root.exists()

    first = subprocess.run(
        command, check=False, capture_output=True, text=True, encoding="utf-8"
    )
    assert first.returncode == 0, first.stderr
    first_result = json.loads(first.stdout)
    manifest_path = Path(first_result["manifest_path"])
    original = manifest_path.read_bytes()
    second = subprocess.run(
        command, check=False, capture_output=True, text=True, encoding="utf-8"
    )
    assert second.returncode == 0, second.stderr
    assert json.loads(second.stdout)["status"] == "VERIFIED_EXISTING"
    assert manifest_path.read_bytes() == original

    hold_command = _build_command(parents[:9], historical, tmp_path / "nine")
    hold = subprocess.run(
        [*hold_command, "--dry-run"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert hold.returncode == 0, hold.stderr
    assert json.loads(hold.stdout)["status"] == "HOLD"
    assert not (tmp_path / "nine").exists()


def test_score_writes_parent_inventory_by_class_but_no_future_without_future_evidence(
    tmp_path: Path,
) -> None:
    parents = _ten(tmp_path / "cases")
    historical = _historical_refs(tmp_path)
    root = tmp_path / "cohorts"
    built = subprocess.run(
        _build_command(parents, historical, root),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert built.returncode == 0, built.stderr
    manifest_path = Path(json.loads(built.stdout)["manifest_path"])
    score_dir = tmp_path / "scores"
    score = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.school_capability_cohort",
            "score",
            "--manifest",
            str(manifest_path),
            "--out-dir",
            str(score_dir),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert score.returncode == 0, score.stderr
    result = json.loads(score.stdout)
    assert result["status"] == "INVENTORY_ONLY_HOLD"
    assert (score_dir / "immediate-parent-inventory.json").exists()
    assert not (score_dir / "future-score.json").exists()
    assert not (score_dir / "immediate-gate.json").exists()
    assert not (score_dir / "future-gate.json").exists()
    assert "GO" not in json.dumps(result)


def test_verify_and_report_cli_fail_closed_without_claiming_go(tmp_path: Path) -> None:
    parents = _ten(tmp_path / "cases")
    historical = _historical_refs(tmp_path)
    root = tmp_path / "cohorts"
    built = subprocess.run(
        _build_command(parents, historical, root),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert built.returncode == 0, built.stderr
    manifest_path = Path(json.loads(built.stdout)["manifest_path"])

    verified = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.school_capability_cohort",
            "verify",
            "--manifest",
            str(manifest_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert verified.returncode == 0, verified.stderr
    assert json.loads(verified.stdout)["status"] == "VERIFIED"

    immediate = tmp_path / "immediate-gate.json"
    future = tmp_path / "future-gate.json"
    manifest_document = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_ref = {
        "artifact_path": manifest_path.as_posix(),
        "artifact_sha256": manifest_document["artifact_sha256"],
    }
    immediate_payload = {
        "schema_version": "prediction-capability-candidate-gate/v1",
        "gate_id": "prediction_capability_candidate_gate_v1",
        "status": "GO",
        "parents": [manifest_ref],
    }
    future_payload = {
        "schema_version": "future-empirical-gate/v1",
        "gate_id": "future_empirical_gate_v1",
        "status": "GO",
        "parents": [manifest_ref],
    }
    publish_new_json(immediate, immediate_payload, dry_run=False)
    publish_new_json(future, future_payload, dry_run=False)
    report_path = tmp_path / "report.json"
    report = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.school_capability_cohort",
            "report",
            "--manifest",
            str(manifest_path),
            "--immediate-gate",
            str(immediate),
            "--future-gate",
            str(future),
            "--out",
            str(report_path),
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert report.returncode == 0, report.stderr
    payload = json.loads(report.stdout)["report"]
    assert payload["status"] == "HOLD_PENDING_TASK_10_AND_11_GATE_EVALUATION"
    assert payload["production_switch"] is False
    assert not report_path.exists()


def test_created_at_cannot_predate_any_parent(tmp_path: Path) -> None:
    parents = _ten(tmp_path / "cases")
    with pytest.raises(ValueError, match="created_at.*parent"):
        build_cohort_manifest(
            parents, _historical_refs(tmp_path), created_at="2026-07-30T00:00:00Z"
        )


def test_completion_status_cannot_replace_authentic_bound_parent_chain(
    tmp_path: Path,
) -> None:
    parents = _ten(tmp_path / "cases")
    forged = json.loads(parents[0].read_text(encoding="utf-8"))
    forged["parents"] = []
    forged.pop("artifact_sha256")
    parents[0].unlink()
    publish_new_json(parents[0], forged, dry_run=False)
    with pytest.raises(ValueError, match="retrospective.*parent|parent.*lineage"):
        build_cohort_manifest(
            parents, _historical_refs(tmp_path), created_at=CREATED_AT
        )


def test_stop_audit_rejects_parentless_claimed_incident(tmp_path: Path) -> None:
    parents = [_completion(tmp_path / "cases", index) for index in range(1, 10)] + [
        _stop(tmp_path / "cases")
    ]
    forged = json.loads(parents[-1].read_text(encoding="utf-8"))
    forged["parents"] = []
    forged.pop("artifact_sha256")
    parents[-1].unlink()
    publish_new_json(parents[-1], forged, dry_run=False)
    with pytest.raises(ValueError, match="STOP.*parent|parent.*STOP|lineage"):
        build_cohort_manifest(
            parents, _historical_refs(tmp_path), created_at=CREATED_AT
        )


def test_cli_hold_never_creates_outdir_even_without_dry_run(tmp_path: Path) -> None:
    parents = [_completion(tmp_path / "cases", index) for index in range(1, 10)]
    historical = _historical_refs(tmp_path)
    out = tmp_path / "nine"
    result = subprocess.run(
        _build_command(parents, historical, out),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 3, result.stderr
    assert json.loads(result.stdout)["status"] == "HOLD"
    assert not out.exists()


def test_existing_publication_rejects_extra_files_as_pollution(tmp_path: Path) -> None:
    parents = _ten(tmp_path / "cases")
    historical = _historical_refs(tmp_path)
    command = _build_command(parents, historical, tmp_path / "cohorts")
    first = subprocess.run(
        command, check=False, capture_output=True, text=True, encoding="utf-8"
    )
    assert first.returncode == 0, first.stderr
    manifest_path = Path(json.loads(first.stdout)["manifest_path"])
    (manifest_path.parent / "foreign.txt").write_text("pollution", encoding="utf-8")

    rerun = subprocess.run(
        command, check=False, capture_output=True, text=True, encoding="utf-8"
    )
    assert rerun.returncode != 0
    assert "pollution" in rerun.stderr.lower() or "unexpected" in rerun.stderr.lower()


def test_report_rejects_forged_gate_documents(tmp_path: Path) -> None:
    parents = _ten(tmp_path / "cases")
    historical = _historical_refs(tmp_path)
    built = subprocess.run(
        _build_command(parents, historical, tmp_path / "cohorts"),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert built.returncode == 0, built.stderr
    manifest_path = Path(json.loads(built.stdout)["manifest_path"])
    immediate = tmp_path / "immediate-gate.json"
    future = tmp_path / "future-gate.json"
    immediate.write_text('{"status":"GO"}\n', encoding="utf-8")
    future.write_text('{"status":"GO"}\n', encoding="utf-8")

    report = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.school_capability_cohort",
            "report",
            "--manifest",
            str(manifest_path),
            "--immediate-gate",
            str(immediate),
            "--future-gate",
            str(future),
            "--out",
            str(tmp_path / "report.json"),
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert report.returncode != 0
    assert "gate" in report.stderr.lower()
    assert "go" not in report.stdout.lower()


def test_manifest_preserves_completion_index_for_recursive_label_and_freeze_access(
    tmp_path: Path,
) -> None:
    manifest = build_cohort_manifest(
        _ten(tmp_path / "cases"), _historical_refs(tmp_path), created_at=CREATED_AT
    )
    for member in manifest["members"]:
        completion = json.loads(
            Path(member["parents"]["completion"]["artifact_path"]).read_text(
                encoding="utf-8"
            )
        )
        assert completion["parents"]
        assert any(
            "immediate-retrospective" in parent["artifact_path"]
            for parent in completion["parents"]
        )


def test_single_cohort_is_explicitly_not_candidate_gate_go(tmp_path: Path) -> None:
    manifest = build_cohort_manifest(
        _ten(tmp_path / "cases"), _historical_refs(tmp_path), created_at=CREATED_AT
    )
    assert manifest["cohort_size"] == 10
    assert manifest["candidate_gate_minimum_subjects"] == 20
    assert manifest["candidate_gate_eligible"] is False
    assert "GO" not in manifest["status"]


def test_future_complete_members_are_not_excluded_when_retrospective_is_pending(
    tmp_path: Path,
) -> None:
    parents = _ten(tmp_path / "cases", future=True)
    for path in parents:
        completion = json.loads(path.read_text(encoding="utf-8"))
        completion["retrospective_completion_status"] = "PENDING"
        completion["parents"] = [
            parent
            for parent in completion["parents"]
            if "immediate-retrospective" not in parent["artifact_path"]
        ]
        completion.pop("artifact_sha256")
        path.unlink()
        publish_new_json(path, completion, dry_run=False)

    manifest = build_cohort_manifest(
        parents, _historical_refs(tmp_path), created_at=CREATED_AT
    )

    assert manifest["cohort_size"] == 10
    assert all(
        not member["evidence_availability"]["immediate_retrospective"]
        for member in manifest["members"]
    )
    assert all(
        member["evidence_availability"]["future_observation"]
        for member in manifest["members"]
    )


def test_report_rejects_self_hashed_gate_without_manifest_parent(
    tmp_path: Path,
) -> None:
    parents = _ten(tmp_path / "cases")
    historical = _historical_refs(tmp_path)
    built = subprocess.run(
        _build_command(parents, historical, tmp_path / "cohorts"),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert built.returncode == 0, built.stderr
    manifest_path = Path(json.loads(built.stdout)["manifest_path"])
    immediate = tmp_path / "immediate-gate.json"
    future = tmp_path / "future-gate.json"
    publish_new_json(
        immediate,
        {
            "schema_version": "prediction-capability-candidate-gate/v1",
            "gate_id": "prediction_capability_candidate_gate_v1",
            "status": "GO",
            "parents": [],
        },
        dry_run=False,
    )
    publish_new_json(
        future,
        {
            "schema_version": "future-empirical-gate/v1",
            "gate_id": "future_empirical_gate_v1",
            "status": "GO",
            "parents": [],
        },
        dry_run=False,
    )

    report = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.school_capability_cohort",
            "report",
            "--manifest",
            str(manifest_path),
            "--immediate-gate",
            str(immediate),
            "--future-gate",
            str(future),
            "--out",
            str(tmp_path / "report.json"),
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert report.returncode != 0
    assert "manifest parent" in report.stderr.lower()
