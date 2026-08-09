from __future__ import annotations

import ast
import copy
import datetime
import hashlib
import inspect
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

import engine.evaluation.prospective_asof as prospective_asof


CASE_ID = "P-GO-2026-001-乾-甲子乙丑丙寅丁卯"
SESSION_CASE_ID = "C-2026-001-乾-甲子乙丑丙寅丁卯"
SUBJECT_HASH = "1" * 64
CREATED_AT = "2020-01-01T00:00:00Z"
SESSION_ID = "S-20200101T000000Z-0123abcd"
REPO_ROOT = Path(__file__).parents[2]
PARAM_COUNTS = {
    "test_asof_bundle_first_proof_exact_bundle_and_parent_binding": 1,
    "test_asof_bundle_first_proof_bundle_tamper_fails_closed": 6,
    "test_asof_bundle_first_proof_request_closed_validation": 4,
    "test_asof_bundle_first_proof_freeze_delegates_exactly_once": 1,
    "test_asof_bundle_first_proof_hash_is_process_stable": 1,
    "test_asof_bundle_first_proof_create_only_paths": 3,
    "test_asof_bundle_first_proof_release_parent_is_exact": 3,
    "test_asof_bundle_first_proof_invalid_release_never_reads_custody": 3,
    "test_asof_bundle_first_proof_valid_release_reads_custody_once": 1,
    "test_asof_bundle_first_proof_event_only_verified_result": 1,
    "test_asof_bundle_first_proof_ast_accounting": 7,
}


@pytest.fixture
def tmp_path() -> Path:
    trusted = prospective_asof._TRUSTED_WORKSPACE_ROOT
    root = Path(tempfile.mkdtemp(prefix="asof-first-proof-", dir=trusted))
    try:
        relative = root.resolve(strict=True).relative_to(trusted)
        current = trusted
        assert not prospective_asof._is_link(current)
        for part in relative.parts:
            current = current / part
            assert not prospective_asof._is_link(current)
        yield relative
    finally:
        shutil.rmtree(root)


def _document_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")


def _artifact_digest(value: dict[str, object]) -> str:
    payload = {key: item for key, item in value.items() if key != "artifact_sha256"}
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_document_bytes(value))


def _request() -> dict[str, object]:
    return {
        "schema_version": "prospective-asof-request/v1",
        "case_id": CASE_ID,
        "session_case_id": SESSION_CASE_ID,
        "subject_id_hash": SUBJECT_HASH,
        "as_of_date": "2020-01-01",
        "session_id": SESSION_ID,
        "chart_source": "wenzhen_structured_v1",
        "hidden_stems_by_pillar": {
            "year": ["甲"], "month": ["乙"], "day": ["丙"], "hour": ["丁"],
        },
        "changsheng_by_pillar": {
            "year": "长生", "month": "沐浴", "day": "冠带", "hour": "临官",
        },
        "daiyun": [{
            "sequence": 1, "stem": "戊", "branch": "辰",
            "start_date": "2010-01-01", "end_date": "2020-01-01",
        }],
        "created_at": CREATED_AT,
    }


def _parent_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "dataset" / CASE_ID / f"{CASE_ID}--blind-bundle--v001"
    del monkeypatch
    chart = {
        "case_id": CASE_ID,
        "sex_marker": "乾",
        "four_pillars": {
            "year": {"stem": "甲", "branch": "子"},
            "month": {"stem": "乙", "branch": "丑"},
            "day": {"stem": "丙", "branch": "寅"},
            "hour": {"stem": "丁", "branch": "卯"},
        },
    }
    question_path = (
        tmp_path / "dataset" / CASE_ID
        / f"{CASE_ID}--future-question-registration--v001.json"
    )
    question_payload = {
        "schema_version": "prospective-future-question/v1",
        "case_id": CASE_ID,
        "subject_id_hash": SUBJECT_HASH,
        "created_at": CREATED_AT,
        "artifact_path": question_path.as_posix(),
        "future_task_id": "career-event",
        "question_text_redacted": "Will the defined event occur in the observation window?",
        "outcome_type": "binary",
        "positive_definition": "The defined event occurs.",
        "negative_definition": "The defined event does not occur.",
        "verification_source_requirements": ["independent source"],
        "observation_window": {
            "start_at": CREATED_AT,
            "end_at": "2020-02-01T00:00:00Z",
        },
        "parents": [],
    }
    question = {
        **question_payload,
        "artifact_sha256": _artifact_digest(question_payload),
    }
    task = {
        "task_id": "career-event",
        "domain": "career",
        "claim_type": "binary_event",
        "scoring_method": "exact_binary",
        "quantifiable": True,
        "high_risk": False,
        "allowed_time_horizons": ["three_months"],
        "required_input_fields": ["four_pillars"],
        "label_schema": {"type": "binary"},
        "evaluation_note": "Score only the registered event.",
    }
    documents = {
        "intake.json": {
            "schema_version": "school-capability-blind-intake/v1",
            "schools": ["ditiansui", "duan", "gao", "ren", "yang", "ziping"],
            "records": [{"case_id": CASE_ID, "task_ids": ["career-event"]}],
        },
        "tasks.json": {
            "schema_version": "school-capability-task-catalog/v1",
            "tasks": [task],
        },
        "rule-snapshot.json": {
            "rule_snapshot_id": "synthetic-blind-safe-v1",
            "sha256": "2" * 64,
        },
        "future-question.json": question,
        f"cases/{CASE_ID}/chart.json": chart,
    }
    files = {name: _canonical_bytes(document) for name, document in documents.items()}
    manifest_path = root / "bundle-manifest.json"
    manifest_payload = {
        "schema_version": "prospective-single-case-blind-bundle/v1",
        "case_id": CASE_ID,
        "subject_id_hash": SUBJECT_HASH,
        "created_at": CREATED_AT,
        "artifact_path": (
            prospective_asof._TRUSTED_WORKSPACE_ROOT / manifest_path
        ).as_posix(),
        "case_count": 1,
        "future_question_count": 1,
        "schools": ["ditiansui", "duan", "gao", "ren", "yang", "ziping"],
        "parents": [
            {
                "artifact_path": (
                    tmp_path / "dataset" / CASE_ID / f"{CASE_ID}--intake--v001.json"
                ).as_posix(),
                "artifact_sha256": "3" * 64,
            },
            {
                "artifact_path": question["artifact_path"],
                "artifact_sha256": question["artifact_sha256"],
            },
        ],
        "files": {name: hashlib.sha256(content).hexdigest() for name, content in files.items()},
        "bundle_sha256": hashlib.sha256(_canonical_bytes(
            {name: hashlib.sha256(content).hexdigest() for name, content in files.items()}
        )).hexdigest(),
    }
    manifest = {
        **manifest_payload,
        "artifact_sha256": _artifact_digest(manifest_payload),
    }
    for name, content in files.items():
        destination = root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    _write_json(manifest_path, manifest)
    return root


def _sealed_chain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, dict[str, object], dict[str, object]]:
    parent = _parent_bundle(tmp_path, monkeypatch)
    request = _request()
    plan = prospective_asof.prepare_asof_blind_bundle(
        parent_bundle_root=parent,
        asof_request=request,
        target_dir=parent.parent / f"{CASE_ID}--asof-blind-bundle--v001",
        dry_run=False,
    )
    bundle_root = prospective_asof._stored_path(plan["manifest"]["artifact_path"]).parent
    frozen = prospective_asof.build_asof_frozen_artifact(bundle_root=bundle_root)
    _write_json(prospective_asof._stored_path(frozen["artifact_path"]), frozen)
    release = prospective_asof.build_asof_feedback_release(
        frozen_artifact=frozen, created_at="2020-01-01T00:00:01.1Z",
    )
    assert release["created_at"] == "2020-01-01T00:00:01.1Z"
    _write_json(prospective_asof._stored_path(release["artifact_path"]), release)
    return bundle_root, frozen, release


def _custody(frozen: dict[str, object]) -> dict[str, object]:
    events = frozen["freeze_package"]["events"]
    return {
        "schema_version": "prospective-asof-custody/v1",
        "case_id": frozen["case_id"],
        "session_case_id": frozen["session_case_id"],
        "subject_id_hash": frozen["subject_id_hash"],
        "session_id": frozen["session_id"],
        "freeze_package_sha256": frozen["freeze_package_sha256"],
        "verifications": [{
            "schema_version": "asof-career-verification/v1",
            "freeze_package_sha256": frozen["freeze_package_sha256"],
            "item_id": event["candidate"]["candidate_id"],
            "verdict": "CONFIRMED",
            "actual_landing": event["landing_set"]["center"],
            "reality_constraint": None,
            "taxonomy_evidence": [],
        } for event in events],
    }


def test_asof_bundle_first_proof_exact_bundle_and_parent_binding(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    parent = _parent_bundle(tmp_path, monkeypatch)
    target = parent.parent / f"{CASE_ID}--asof-blind-bundle--v001"
    plan = prospective_asof.prepare_asof_blind_bundle(
        parent_bundle_root=parent, asof_request=_request(), target_dir=target, dry_run=False,
    )
    verified = prospective_asof.verify_asof_blind_bundle(bundle_root=target)
    parent_chart = parent / f"cases/{CASE_ID}/chart.json"
    assert (target / "chart.json").read_bytes() == parent_chart.read_bytes()
    assert set(path.name for path in target.iterdir()) == {
        "parent-bundle-ref.json", "asof-request.json", "chart.json", "bundle-manifest.json",
    }
    assert verified["manifest"] == plan["manifest"]
    assert verified["manifest"]["parents"][0]["artifact_path"] == (
        parent / "bundle-manifest.json"
    ).as_posix()
    assert verified["identity"].case_id == SESSION_CASE_ID


@pytest.mark.parametrize("mutation", ["extra", "missing", "symlink", "parent", "hash", "marker"])
def test_asof_bundle_first_proof_bundle_tamper_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    parent = _parent_bundle(tmp_path, monkeypatch)
    target = parent.parent / f"{CASE_ID}--asof-blind-bundle--v001"
    prospective_asof.prepare_asof_blind_bundle(
        parent_bundle_root=parent, asof_request=_request(), target_dir=target, dry_run=False,
    )
    if mutation == "extra":
        (target / "extra.json").write_text("{}", encoding="utf-8")
    elif mutation == "missing":
        (target / "chart.json").unlink()
    elif mutation == "symlink":
        try:
            (target / "extra-link").symlink_to(target / "chart.json")
        except OSError as error:
            pytest.fail(f"symlink oracle unavailable: {type(error).__name__}")
    else:
        path = target / ("parent-bundle-ref.json" if mutation == "parent" else "bundle-manifest.json")
        path.write_bytes(path.read_bytes() + (b" " if mutation != "marker" else b"marker"))
    with pytest.raises(Exception):
        prospective_asof.verify_asof_blind_bundle(bundle_root=target)


@pytest.mark.parametrize("mutation", ["unknown", "identity", "daiyun", "date"])
def test_asof_bundle_first_proof_request_closed_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    parent = _parent_bundle(tmp_path, monkeypatch)
    request = _request()
    if mutation == "unknown":
        request["unknown"] = True
    elif mutation == "identity":
        request["session_case_id"] = "C-2026-002-乾-甲子乙丑丙寅丁卯"
    elif mutation == "daiyun":
        request["daiyun"][0]["stem"] = []
    else:
        request["session_id"] = "S-20200102T000000Z-0123abcd"
    with pytest.raises(prospective_asof._AsOfError) as caught:
        prospective_asof.prepare_asof_blind_bundle(
            parent_bundle_root=parent, asof_request=request,
            target_dir=parent.parent / f"{CASE_ID}--asof-blind-bundle--v001", dry_run=True,
        )
    assert caught.value.category in {"ASOF_SCHEMA_ERROR", "ASOF_IDENTITY_ERROR"}
    if mutation == "unknown":
        target = parent.parent / f"{CASE_ID}--asof-blind-bundle--v001"
        prospective_asof.prepare_asof_blind_bundle(
            parent_bundle_root=parent, asof_request=_request(), target_dir=target, dry_run=False,
        )
        valid_package = prospective_asof.build_asof_frozen_artifact(
            bundle_root=target,
        )["freeze_package"]
        bad_date = copy.deepcopy(valid_package)
        bad_date["identity"]["as_of_date"] = "not-a-date"
        bad_enum = copy.deepcopy(valid_package)
        bad_enum["events"][0]["candidate"]["root_level"] = "NOT_A_ROOT"
        bad_constructor = copy.deepcopy(valid_package)
        bad_constructor["events"][0]["candidate"]["annual_trace"]["relations"] = None
        malformed_packages = (
            None,
            {"schema_version": "asof-career-freeze-package/v1"},
            bad_date,
            bad_enum,
            bad_constructor,
        )
        for malformed in malformed_packages:
            with pytest.raises(prospective_asof._AsOfError) as nested:
                prospective_asof._package_from_mapping(malformed)
            assert nested.value.category == "ASOF_SCHEMA_ERROR"


def test_asof_bundle_first_proof_freeze_delegates_exactly_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    parent = _parent_bundle(tmp_path, monkeypatch)
    target = parent.parent / f"{CASE_ID}--asof-blind-bundle--v001"
    prospective_asof.prepare_asof_blind_bundle(
        parent_bundle_root=parent, asof_request=_request(), target_dir=target, dry_run=False,
    )
    calls = 0
    original = prospective_asof.build_career_blind_draft

    def counted(*, blind_input: object, identity: object) -> object:
        nonlocal calls
        calls += 1
        return original(blind_input=blind_input, identity=identity)

    monkeypatch.setattr(prospective_asof, "build_career_blind_draft", counted)
    frozen = prospective_asof.build_asof_frozen_artifact(bundle_root=target)
    assert calls == 1
    assert len(frozen["freeze_package"]["fundamentals"]) == 1
    assert len(frozen["freeze_package"]["events"]) == 1


def test_asof_bundle_first_proof_hash_is_process_stable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    parent = _parent_bundle(tmp_path, monkeypatch)
    target = parent.parent / f"{CASE_ID}--asof-blind-bundle--v001"
    prospective_asof.prepare_asof_blind_bundle(
        parent_bundle_root=parent, asof_request=_request(), target_dir=target, dry_run=False,
    )
    left = prospective_asof.build_asof_frozen_artifact(bundle_root=target)
    package = left["freeze_package"]
    assert set(package) == {"schema_version", "identity", "blind_input_sha256", "fundamentals", "events"}
    assert package["schema_version"] == "asof-career-freeze-package/v1"
    assert package["identity"] == {
        "schema_version": "asof-session/v1", "case_id": SESSION_CASE_ID,
        "as_of_date": "2020-01-01", "session_id": SESSION_ID,
    }
    assert package["blind_input_sha256"] == left["blind_input_sha256"]
    assert len(package["fundamentals"]) == len(package["events"]) == 1
    fundamental = package["fundamentals"][0]
    event = package["events"][0]
    candidate = event["candidate"]
    landing = event["landing_set"]
    pillar_token = "甲子乙丑丙寅丁卯"
    probe_token = (
        f"{SESSION_CASE_ID}|2020-01-01|{pillar_token}|1|戊辰|"
        "2010-01-01|2020-01-01"
    )
    probe_digest = hashlib.sha256(probe_token.encode("utf-8")).hexdigest()
    center = datetime.date.fromordinal(
        (datetime.date(2010, 1, 1).toordinal() + datetime.date(2020, 1, 1).toordinal()) // 2
    ).isoformat()
    natal = {"source": "blind-input", "locator": "pillars", "excerpt": pillar_token}
    daiyun = {
        "source": "blind-input", "locator": "daiyun[1]",
        "excerpt": "戊辰|2010-01-01|2020-01-01",
    }
    assert fundamental == {
        "fundamental_id": "career-fundamental-" + probe_digest[:16],
        "window_start": "2010-01-01", "window_end": "2020-01-01",
        "window_center": center, "center": "STRUCTURAL_PROBE_ONLY",
        "reasonable_range": ["STRUCTURAL_PROBE_ONLY"],
        "strongest_alternative": "NO_CAREER_INFERENCE",
        "falsifiers": ["PROOF_SEAM_IS_NOT_A_CAREER_PREDICTION"],
    }
    assert candidate == {
        "candidate_id": "career-event-" + probe_digest[:16], "domain": "career",
        "event_type": "STRUCTURAL_PROBE_ONLY", "window_start": "2010-01-01",
        "window_end": "2020-01-01", "natal_evidence": [natal],
        "daiyun_evidence": [daiyun],
        "annual_trace": {
            "year": 2020, "liunian": "STRUCTURAL_PROBE_ONLY", "dayun_ganzhi": "戊辰",
            "relations": [daiyun], "activated_node_ids": ["daiyun-1"],
            "domains": ["career"], "supporting_evidence": [natal, daiyun],
            "counter_evidence": [], "trigger_strength": "low", "crossed_candidate_gate": True,
        },
        "root_level": "WEAK_ROOT", "root_evidence": [natal],
        "source_citations": [{
            "source_path": "plans/as-of-blind-bundle-first-proof-point-contract-2026-08-07.md",
            "line": 1, "excerpt": "# as-of blind-bundle First Proof Point 合同（2026-08-07）",
        }],
        "completion_mode": "COMPLETE_LATENT", "supporting_evidence": [natal],
        "counter_evidence": [], "alternative_hypotheses": ["NO_CAREER_INFERENCE"],
        "frozen_version": "prospective-asof-structural-probe/v1",
        "verification_status": "FROZEN",
        "extension_boundary": "REMAINDER_ONLY_RECHECK_CROSS_DAIYUN",
        "is_primary_event": True,
    }
    assert landing == {
        "function_candidate": "STRUCTURAL_PROBE_ONLY",
        "center": {"name": "STRUCTURAL_PROBE_ONLY", "domain": "career", "direction": "structural-probe"},
        "alternatives": [], "weak_hit_boundary": "EXACT_PROBE_LABEL_ONLY",
        "falsifiers": ["ANY_REAL_CAREER_CLAIM"], "exclusions": ["ACCURACY_INFERENCE"],
        "frozen_version": "prospective-asof-structural-probe/v1",
    }
    contract_path = (
        REPO_ROOT
        / "plans/as-of-blind-bundle-first-proof-point-contract-2026-08-07.md"
    )
    assert contract_path.read_text(encoding="utf-8").splitlines()[0] == candidate[
        "source_citations"
    ][0]["excerpt"]
    script = f'''import datetime, hashlib\nfrom engine.asof.session_contract import blind_chart_input_from_mapping, SessionIdentity, SESSION_SCHEMA_VERSION\nfrom engine.evaluation.prospective_asof import build_career_blind_draft\nfrom engine.asof.consultation_freeze import CareerFreezePackage, FREEZE_PACKAGE_SCHEMA_VERSION, freeze_package_to_canonical_bytes\nmapping = {repr(prospective_asof._blind_mapping(_request(), json.loads((target / "chart.json").read_text(encoding="utf-8"))))}\nblind = blind_chart_input_from_mapping(mapping)\nidentity = SessionIdentity(SESSION_SCHEMA_VERSION, {SESSION_CASE_ID!r}, datetime.date(2020, 1, 1), {SESSION_ID!r})\ndraft = build_career_blind_draft(blind_input=blind, identity=identity)\npackage = CareerFreezePackage(FREEZE_PACKAGE_SCHEMA_VERSION, identity, {left["blind_input_sha256"]!r}, draft.fundamentals, draft.events)\nraw = freeze_package_to_canonical_bytes(package)\nprint(raw.hex())\nprint(hashlib.sha256(raw).hexdigest())'''
    output = subprocess.check_output([sys.executable, "-c", script], cwd=REPO_ROOT, text=True).splitlines()
    canonical = _canonical_bytes(left["freeze_package"])
    assert bytes.fromhex(output[0]) == canonical
    assert output[1] == left["freeze_package_sha256"] == hashlib.sha256(canonical).hexdigest()
    assert left["artifact_sha256"] == _artifact_digest(left)


@pytest.mark.parametrize("kind", ["request", "bundle", "frozen"])
def test_asof_bundle_first_proof_create_only_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str,
) -> None:
    if kind == "bundle":
        original_write = Path.write_bytes
        original_read = Path.read_bytes
        for fault in ("staging-write", "staging-read", "publish", "post-read"):
            with monkeypatch.context() as scoped:
                parent = _parent_bundle(tmp_path / fault, scoped)
                target = parent.parent / f"{CASE_ID}--asof-blind-bundle--v001"
                if fault == "staging-write":
                    def failed_write(path: Path, data: bytes) -> int:
                        if path.parent.name.startswith(".asof-stage-"):
                            raise OSError("injected")
                        return original_write(path, data)
                    scoped.setattr(Path, "write_bytes", failed_write)
                elif fault == "staging-read":
                    def failed_read(path: Path) -> bytes:
                        if path.parent.name.startswith(".asof-stage-"):
                            raise OSError("injected")
                        return original_read(path)
                    scoped.setattr(Path, "read_bytes", failed_read)
                elif fault == "publish":
                    scoped.setattr(
                        prospective_asof, "_publish_directory_no_replace",
                        lambda source, destination: (_ for _ in ()).throw(OSError("injected")),
                    )
                else:
                    scoped.setattr(
                        prospective_asof, "verify_asof_blind_bundle",
                        lambda **kwargs: (_ for _ in ()).throw(OSError("injected")),
                    )
                with pytest.raises(prospective_asof._AsOfError) as orphaned:
                    prospective_asof.prepare_asof_blind_bundle(
                        parent_bundle_root=parent, asof_request=_request(),
                        target_dir=target, dry_run=False,
                    )
                assert orphaned.value.category == "ASOF_IO_ERROR"
                assert orphaned.value.reason == "ORPHANED_SEALED_PREREQUISITE"
                assert (parent.parent / f"{CASE_ID}--asof-request--v001.json").is_file()
                assert not any(path.name.startswith(".asof-stage-") for path in parent.parent.iterdir())
        return
    parent = _parent_bundle(tmp_path, monkeypatch)
    target = parent.parent / f"{CASE_ID}--asof-blind-bundle--v001"
    if kind == "request":
        Path(parent.parent / f"{CASE_ID}--asof-request--v001.json").write_text("sealed", encoding="utf-8")
    else:
        prospective_asof.prepare_asof_blind_bundle(
            parent_bundle_root=parent, asof_request=_request(), target_dir=target, dry_run=False,
        )
        frozen = prospective_asof.build_asof_frozen_artifact(bundle_root=target)
        frozen_path = prospective_asof._stored_path(frozen["artifact_path"])
        frozen_path.write_text("sealed", encoding="utf-8")
        with pytest.raises(Exception):
            from tools.as_of_prospective import publish_new_json_artifact
            publish_new_json_artifact(frozen_path, frozen)
        return
    with pytest.raises(Exception):
        prospective_asof.prepare_asof_blind_bundle(
            parent_bundle_root=parent, asof_request=_request(), target_dir=target, dry_run=False,
        )


@pytest.mark.parametrize("mutation", ["mapping", "wrong-schema", "tampered"])
def test_asof_bundle_first_proof_release_parent_is_exact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    bundle_root, frozen, _ = _sealed_chain(tmp_path, monkeypatch)
    if mutation == "mapping":
        prospective_asof._stored_path(frozen["artifact_path"]).unlink()
    elif mutation == "wrong-schema":
        frozen["schema_version"] = "prospective-feedback-release/v2"
    else:
        frozen["freeze_package_sha256"] = "f" * 64
    with pytest.raises(Exception):
        prospective_asof.build_asof_feedback_release(
            frozen_artifact=frozen, created_at="2020-01-01T00:00:02Z",
        )
    assert bundle_root.exists()


@pytest.mark.parametrize("mutation", ["hold", "tampered", "exception"])
def test_asof_bundle_first_proof_invalid_release_never_reads_custody(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    _, _, release = _sealed_chain(tmp_path, monkeypatch)
    calls = 0

    def reader() -> dict[str, object]:
        nonlocal calls
        calls += 1
        raise RuntimeError("must remain unreachable")

    if mutation == "hold":
        release["release_status"] = "HOLD"
    elif mutation == "tampered":
        release["artifact_sha256"] = "f" * 64
    else:
        release["artifact_path"] = (
            Path(release["artifact_path"]).parent / "noncanonical-release.json"
        ).as_posix()
    with pytest.raises(prospective_asof._AsOfError):
        prospective_asof.collect_asof_verification(
            release=release, custody_reader=reader, collected_at="2020-01-01T00:00:03Z",
        )
    assert calls == 0
    if mutation == "hold":
        _, _, valid_release = _sealed_chain(tmp_path / "time-priority", monkeypatch)
        with pytest.raises(prospective_asof._AsOfError) as caught:
            prospective_asof.collect_asof_verification(
                release=valid_release, custody_reader=reader, collected_at=CREATED_AT,
            )
        assert caught.value.category == "ASOF_TIME_ERROR" and calls == 0


def test_asof_bundle_first_proof_valid_release_reads_custody_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _, frozen, release = _sealed_chain(tmp_path, monkeypatch)
    calls = 0

    def reader() -> dict[str, object]:
        nonlocal calls
        calls += 1
        return _custody(frozen)

    result = prospective_asof.collect_asof_verification(
        release=release, custody_reader=reader, collected_at="2020-01-01T00:00:03.01Z",
    )
    assert calls == 1
    assert result["collected_at"] == "2020-01-01T00:00:03.01Z"
    assert result["verification_status"] == "VERIFIED_RESULT_SEALED"


@pytest.mark.parametrize("event_count", [1], ids=["one-event"])
def test_asof_bundle_first_proof_event_only_verified_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, event_count: int,
) -> None:
    _, frozen, release = _sealed_chain(tmp_path, monkeypatch)
    custody = _custody(frozen)
    calls = {"open": 0, "input": 0, "record": 0}
    for name, key in (
        ("open_verification", "open"),
        ("verification_input_from_mapping", "input"),
        ("record_career_verification", "record"),
    ):
        original = getattr(prospective_asof, name)
        def counted(*args: object, _original: object = original, _key: str = key, **kwargs: object) -> object:
            calls[_key] += 1
            return _original(*args, **kwargs)
        monkeypatch.setattr(prospective_asof, name, counted)
    result = prospective_asof.collect_asof_verification(
        release=release, custody_reader=lambda: custody,
        collected_at="2020-01-01T00:00:03Z",
    )
    assert calls == {"open": event_count, "input": event_count, "record": event_count}
    assert len(result["records"]) == event_count
    assert [row["item_id"] for row in result["records"]] == [
        event["candidate"]["candidate_id"] for event in frozen["freeze_package"]["events"]
    ]
    expected_record_keys = [
        "envelope", "freeze_package_sha256", "item_id", "verdict", "actual_landing",
        "reality_constraint", "taxonomy_evidence", "landing_verdict", "frozen_landing_name",
        "reason_code",
    ]
    assert list(result["records"][0]) == expected_record_keys
    for record, verification, event in zip(
        result["records"], custody["verifications"], frozen["freeze_package"]["events"], strict=True,
    ):
        assert record == {
            "envelope": {
                "identity": {
                    "schema_version": "asof-session/v1", "case_id": SESSION_CASE_ID,
                    "as_of_date": "2020-01-01", "session_id": SESSION_ID,
                },
                "blind_input_sha256": frozen["blind_input_sha256"], "state": "VERIFICATION_OPEN",
            },
            "freeze_package_sha256": frozen["freeze_package_sha256"],
            "item_id": event["candidate"]["candidate_id"], "verdict": verification["verdict"],
            "actual_landing": verification["actual_landing"], "reality_constraint": None,
            "taxonomy_evidence": [], "landing_verdict": "CENTER_HIT",
            "frozen_landing_name": event["landing_set"]["center"]["name"],
            "reason_code": "CENTER_MATCHED",
        }
        assert isinstance(record["taxonomy_evidence"], list)
        assert "fundamental" not in json.dumps(record).lower()


@pytest.mark.parametrize(
    "check", ["api", "imports", "calls", "paths", "cli", "evidence-byte", "forbidden-static"],
)
def test_asof_bundle_first_proof_ast_accounting(
    check: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    source_path = Path("engine/evaluation/prospective_asof.py")
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    if check == "api":
        expected = set(PARAM_COUNTS)
        assert sum(PARAM_COUNTS.values()) == 31 and len(expected) == 11
        expected_signatures = {
            "prepare_asof_blind_bundle": (
                (("parent_bundle_root", "Path"), ("asof_request", "Mapping[str, object]"),
                 ("target_dir", "Path"), ("dry_run", "bool")),
                "dict[str, object]",
            ),
            "verify_asof_blind_bundle": ((("bundle_root", "Path"),), "dict[str, object]"),
            "build_career_blind_draft": (
                (("blind_input", "BlindChartInput"), ("identity", "SessionIdentity")),
                "CareerBlindDraft",
            ),
            "build_asof_frozen_artifact": ((("bundle_root", "Path"),), "dict[str, object]"),
            "build_asof_feedback_release": (
                (("frozen_artifact", "Mapping[str, object]"), ("created_at", "str")),
                "dict[str, object]",
            ),
            "verify_asof_feedback_release": (
                (("release", "Mapping[str, object]"),),
                "tuple[dict[str, object], dict[str, object]]",
            ),
            "collect_asof_verification": (
                (("release", "Mapping[str, object]"),
                 ("custody_reader", "Callable[[], Mapping[str, object]]"),
                 ("collected_at", "str")),
                "dict[str, object]",
            ),
        }
        public = {
            name for name, value in vars(prospective_asof).items()
            if inspect.isfunction(value) and value.__module__ == prospective_asof.__name__ and not name.startswith("_")
        }
        assert public == set(expected_signatures)
        for function, (expected_parameters, expected_return) in expected_signatures.items():
            signature = inspect.signature(getattr(prospective_asof, function))
            assert tuple(
                (parameter.name, parameter.annotation)
                for parameter in signature.parameters.values()
            ) == expected_parameters
            assert all(
                parameter.kind is inspect.Parameter.KEYWORD_ONLY
                and parameter.default is inspect.Parameter.empty
                for parameter in signature.parameters.values()
            )
            assert signature.return_annotation == expected_return
    elif check == "imports":
        required = {
            "engine.asof.session_contract": {
                "blind_chart_input_from_mapping", "create_initial_envelope", "transition_session",
            },
            "engine.asof.consultation_freeze": {
                "freeze_career_draft", "freeze_package_to_canonical_bytes", "compute_freeze_package_sha256",
                "open_verification", "verification_input_from_mapping", "record_career_verification",
            },
            "engine.evaluation.prospective_single_case": {"verify_single_case_bundle"},
        }
        bindings: dict[str, str] = {}
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom) or node.module not in required:
                continue
            for alias in node.names:
                if alias.name not in required[node.module]:
                    continue
                assert alias.asname is None
                assert alias.name not in bindings
                bindings[alias.name] = f"{node.module}.{alias.name}"
        assert set(bindings) == set().union(*required.values())
        assert bindings == {
            name: f"{module}.{name}" for module, names in required.items() for name in names
        }
    elif check == "calls":
        functions = {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        expected = {
            "build_asof_frozen_artifact": {
                "verify_asof_blind_bundle": 1, "transition_session": 1,
                "build_career_blind_draft": 1, "freeze_career_draft": 1,
                "freeze_package_to_canonical_bytes": 1,
                "compute_freeze_package_sha256": 1, "create_initial_envelope": 0,
                "run_career_session": 0,
            },
            "verify_asof_blind_bundle": {
                "verify_single_case_bundle": 1, "blind_chart_input_from_mapping": 1,
                "create_initial_envelope": 1,
            },
            "collect_asof_verification": {
                "verify_asof_feedback_release": 1,
                "open_verification": 1,
                "verification_input_from_mapping": 1,
                "record_career_verification": 1,
            },
        }
        required = {
            "engine.asof.session_contract": {
                "blind_chart_input_from_mapping", "create_initial_envelope", "transition_session",
            },
            "engine.asof.consultation_freeze": {
                "freeze_career_draft", "freeze_package_to_canonical_bytes", "compute_freeze_package_sha256",
                "open_verification", "verification_input_from_mapping", "record_career_verification",
            },
            "engine.evaluation.prospective_single_case": {"verify_single_case_bundle"},
        }
        imported: dict[str, str] = {}
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom) or node.module not in required:
                continue
            for alias in node.names:
                if alias.name not in required[node.module]:
                    continue
                assert alias.asname is None
                assert alias.name not in imported
                imported[alias.name] = f"{node.module}.{alias.name}"
        assert set(imported) == set().union(*required.values())
        local = {name: f"engine.evaluation.prospective_asof.{name}" for name in functions}
        bindings = {**imported, **local}
        for function, counts in expected.items():
            calls = [
                bindings[node.func.id] for node in ast.walk(functions[function])
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in bindings
            ]
            for symbol, count in counts.items():
                qualified = bindings.get(symbol, symbol)
                assert calls.count(qualified) == count
    elif check == "paths":
        root_assignments = [
            node for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "_TRUSTED_WORKSPACE_ROOT" for target in node.targets)
        ]
        assert len(root_assignments) == 1
        assert ast.unparse(root_assignments[0].value) == "Path.cwd().resolve(strict=True)"
        assert sum(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "cwd"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "Path"
            for node in ast.walk(tree)
        ) == 1
        cli_tree = ast.parse(Path("tools/as_of_prospective.py").read_text(encoding="utf-8"))
        trusted_imports = [
            alias
            for node in cli_tree.body
            if isinstance(node, ast.ImportFrom)
            and node.module == "engine.evaluation.prospective_asof"
            for alias in node.names
            if alias.name == "_TRUSTED_WORKSPACE_ROOT"
        ]
        assert trusted_imports == []
        module_imports = [
            alias
            for node in cli_tree.body
            if isinstance(node, ast.Import)
            for alias in node.names
            if alias.name == "engine.evaluation.prospective_asof"
        ]
        assert len(module_imports) == 1 and module_imports[0].asname == "_prospective_asof"
        assert "--asof-request--v001.json" in source and "--asof-blind-bundle--v001" in source
        trusted_root = prospective_asof._TRUSTED_WORKSPACE_ROOT
        with pytest.raises(AttributeError):
            prospective_asof._TRUSTED_WORKSPACE_ROOT = Path("forbidden")
        assert prospective_asof._TRUSTED_WORKSPACE_ROOT is trusted_root
        with pytest.raises(AttributeError):
            del prospective_asof._TRUSTED_WORKSPACE_ROOT
        assert prospective_asof._TRUSTED_WORKSPACE_ROOT is trusted_root
        before = prospective_asof._stored_path((tmp_path / "sealed.json").as_posix())
        monkeypatch.chdir(prospective_asof._TRUSTED_WORKSPACE_ROOT / tmp_path)
        assert prospective_asof._stored_path((tmp_path / "sealed.json").as_posix()) == before
        for rejected in ("/absolute.json", "C:/drive.json", "//server/share.json", ".", "..", "../escape.json"):
            with pytest.raises(prospective_asof._AsOfError) as caught:
                prospective_asof._stored_path(rejected)
            assert caught.value.category == "ASOF_PATH_ERROR"
    elif check == "cli":
        import tools.as_of_prospective as cli_module

        assert cli_module._prospective_asof is prospective_asof
        for valid in ("2020-01-01T00:00:00Z", "2020-01-01T00:00:00.1Z", "2020-01-01T00:00:00.000001Z"):
            assert prospective_asof._timestamp(valid).tzinfo == datetime.timezone.utc
        for invalid in ("2020-01-01T00:00:00", "2020-01-01T00:00:00.Z", "2020-01-01T00:00:00,1Z", "2020-01-01T00:00:00+00:00"):
            with pytest.raises(prospective_asof._AsOfError) as caught:
                prospective_asof._timestamp(invalid)
            assert caught.value.category == "ASOF_TIME_ERROR"

        parser = cli_module._parser()
        bundle_name = (tmp_path / "bundle").as_posix()
        frozen_name = (tmp_path / "frozen.json").as_posix()
        release_name = (tmp_path / "release.json").as_posix()
        custody_name = (tmp_path / "custody.json").as_posix()
        verified_name = (tmp_path / "verified.json").as_posix()
        exact = {
            "freeze": ["freeze", "--bundle-root", bundle_name, "--out", frozen_name],
            "release": ["release", "--frozen", frozen_name, "--created-at", CREATED_AT, "--out", release_name],
            "verify": ["verify", "--release", release_name, "--custody", custody_name, "--collected-at", CREATED_AT, "--out", verified_name],
        }
        assert {name: vars(parser.parse_args(argv)) for name, argv in exact.items()} == {
            "freeze": {"command": "freeze", "bundle_root": bundle_name, "out": frozen_name},
            "release": {"command": "release", "frozen": frozen_name, "created_at": CREATED_AT, "out": release_name},
            "verify": {"command": "verify", "release": release_name, "custody": custody_name, "collected_at": CREATED_AT, "out": verified_name},
        }
        with pytest.raises(prospective_asof._AsOfError):
            parser.parse_args([*exact["freeze"], "--case-dir", "forbidden"])
        with pytest.raises(prospective_asof._AsOfError):
            parser.parse_args(["freeze", "--bundle-root", "bundle"])

        frozen_path = tmp_path / "frozen.json"
        _write_json(frozen_path, {"artifact_path": frozen_path.as_posix()})
        output = tmp_path / "release.json"
        seen: dict[str, object] = {}
        def release_builder(**kwargs: object) -> dict[str, object]:
            seen["sealed_input_path"] = kwargs["frozen_artifact"]["artifact_path"]
            return {"artifact_path": output.as_posix()}
        monkeypatch.setattr(cli_module, "build_asof_feedback_release", release_builder)
        monkeypatch.setattr(cli_module, "publish_new_json_artifact", lambda path, artifact: seen.update(path=path, artifact=artifact))
        monkeypatch.setattr(sys, "argv", ["as_of_prospective", *exact["release"]])
        assert cli_module.main() == 0
        assert seen == {
            "sealed_input_path": frozen_path.as_posix(),
            "path": prospective_asof._TRUSTED_WORKSPACE_ROOT / output,
            "artifact": {"artifact_path": output.as_posix()},
        }
        assert capsys.readouterr().err == ""
        assert output.exists() is False

        _write_json(tmp_path / "release.json", {"artifact_path": (tmp_path / "release.json").as_posix()})
        _write_json(tmp_path / "custody.json", {})
        for argv, command_output, builder_name in (
            (exact["freeze"], tmp_path / "frozen.json", "build_asof_frozen_artifact"),
            (exact["verify"], tmp_path / "verified.json", "collect_asof_verification"),
        ):
            if command_output.exists():
                command_output.unlink()
            command_seen: dict[str, object] = {}
            def command_builder(**kwargs: object) -> dict[str, object]:
                command_seen["kwargs"] = kwargs
                return {"artifact_path": command_output.as_posix()}
            monkeypatch.setattr(cli_module, builder_name, command_builder)
            monkeypatch.setattr(
                cli_module, "publish_new_json_artifact",
                lambda path, artifact: command_seen.update(path=path, artifact=artifact),
            )
            monkeypatch.setattr(sys, "argv", ["as_of_prospective", *argv])
            assert cli_module.main() == 0
            assert capsys.readouterr().err == ""
            assert command_output.exists() is False
            assert command_seen["path"] == prospective_asof._TRUSTED_WORKSPACE_ROOT / command_output
            assert command_seen["artifact"] == {"artifact_path": command_output.as_posix()}

        monkeypatch.setattr(sys, "argv", ["as_of_prospective", *exact["release"]])
        monkeypatch.setattr(cli_module, "build_asof_feedback_release", release_builder)
        monkeypatch.setattr(cli_module, "publish_new_json_artifact", lambda path, artifact: None)
        output.unlink()
        _write_json(frozen_path, {"artifact_path": "wrong/frozen.json"})
        assert cli_module.main() == 2
        assert capsys.readouterr().err == "ASOF_PATH_ERROR\n"
        _write_json(frozen_path, {"artifact_path": frozen_path.as_posix()})
        monkeypatch.setattr(cli_module, "build_asof_feedback_release", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("secret/path/payload")))
        assert cli_module.main() == 2
        assert capsys.readouterr().err == "ASOF_DOMAIN_ERROR\n"

        output.write_text("sealed", encoding="utf-8")
        assert cli_module.main() == 2
        assert capsys.readouterr().err == "ASOF_CONFLICT_ERROR\n"
        output.unlink()
        _write_json(frozen_path, {"artifact_path": frozen_path.as_posix()})
        monkeypatch.setattr(cli_module, "_is_link", lambda path: Path(path).name == output.name)
        assert cli_module.main() == 2
        assert capsys.readouterr().err == "ASOF_LINK_ERROR\n"
    elif check == "evidence-byte":
        assert (
            hashlib.sha256(
                Path("engine/evaluation/prospective_evidence.py").read_bytes()
            ).hexdigest()
            == "ee4581d1a8303bb3c2263ccac9a239388c7fc273aa27a0a82c2724462b49507d"
        )
    else:
        lowered = (source + Path("tools/as_of_prospective.py").read_text(encoding="utf-8")).lower()
        forbidden = (
            "rglob(", "glob(", "os.walk", "feedback" + ".md", "analysis" + ".md",
            "known" + "_facts", "reports" + "/", "production" + "_pipeline",
            "render" + "_report", "git" + "hub",
        )
        assert not any(token in lowered for token in forbidden)


