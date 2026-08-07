from __future__ import annotations

from dataclasses import replace
import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from engine.f09.canonical_json import bounded_jcs_sha256, canonicalize_bounded_jcs, parse_bounded_jcs
from engine.f09.contracts import ArtifactSetState, DetectedIssue
from engine.f09.errors import F09ContractError, F09WriteError


def _request(application, root: Path | None, **changes):
    values = {
        "case_id": "CASE-G10-R2",
        "mode": "STAGED_AUDIT",
        "chart_records": (),
        "hypothesis_records": (),
        "normalized_evidence_port": object(),
        "frozen_contract_port": object(),
        "request_id": "REQUEST-G10-R2",
        "contract_ref": object(),
        "normative_contract_ref": object(),
        "machine_appendix_ref": object(),
        "artifact_projections": {"REPORT": b"report"},
        "artifact_key": object(),
        "existing_manifest": None,
        "attempt_id": "ATTEMPT-G10-R2",
        "enable_f09": True,
        "markdown_path": Path("contract.md"),
        "snapshot_path": Path("snapshot.json"),
        "artifact_root": root,
        "now": "2026-07-27T00:00:00Z",
    }
    values.update(changes)
    return application.F09RunRequest(**values)


def _inputs():
    return {
        "gate_inputs": (object(),),
        "competition_input": object(),
        "root_input": object(),
        "timing_input": object(),
    }


def _locator(request) -> Path:
    identity = {
        "schema_version": "f09.operator-phase-observation-locator.v1",
        "case_id": request.case_id,
        "request_id": request.request_id,
        "attempt_id": request.attempt_id,
        "mode": request.mode,
    }
    digest = bounded_jcs_sha256(identity)
    return request.artifact_root / "operator-diagnostics" / f"{digest.value}.json"


def _read_log(request):
    target = _locator(request)
    raw = target.read_bytes()
    assert canonicalize_bounded_jcs(parse_bounded_jcs(raw)) == raw
    return parse_bounded_jcs(raw)


def _install_phase_owners(monkeypatch, application, terminal_phase: str | None):
    def maybe_fail(phase, value):
        if terminal_phase == phase:
            raise F09ContractError(f"{phase}.FAILED", f"/{phase.lower()}")
        return value

    monkeypatch.setattr(
        application,
        "build_f09_evidence_package",
        lambda **kwargs: maybe_fail("EVIDENCE", object()),
    )
    monkeypatch.setattr(
        application,
        "evaluate_f09",
        lambda *args, **kwargs: maybe_fail("DECISION", object()),
    )
    monkeypatch.setattr(
        application,
        "build_trace",
        lambda *args, **kwargs: maybe_fail("TRACE", object()),
    )
    monkeypatch.setattr(application, "build_statement_set", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        application,
        "validate_statement_projection",
        lambda *args, **kwargs: SimpleNamespace(valid=True, detected_issues=()),
    )

    def artifact_owner(*args, **kwargs):
        if terminal_phase == "ARTIFACT":
            return SimpleNamespace(
                state=ArtifactSetState.PARTIAL,
                detected_issues=(DetectedIssue("ARTIFACT.FAILED", "/artifact"),),
            )
        return SimpleNamespace(state=ArtifactSetState.COMPLETE_VERIFIED, detected_issues=())

    monkeypatch.setattr(application, "coordinate_artifact_operation", artifact_owner)


@pytest.mark.parametrize(
    ("terminal_phase", "request_changes", "expected_status"),
    (
        ("SOURCE_PREFLIGHT", {"enable_f09": False}, "REJECTED"),
        ("EVIDENCE", {}, "FAILED"),
        ("DECISION", {}, "FAILED"),
        ("TRACE", {}, "FAILED"),
        ("ARTIFACT", {}, "FAILED"),
    ),
)
def test_d1_d2_every_controlled_terminal_phase_is_persisted(
    tmp_path, monkeypatch, terminal_phase, request_changes, expected_status
):
    import engine.f09.application as application

    root = tmp_path / terminal_phase.lower()
    request = _request(application, root, **request_changes)
    _install_phase_owners(monkeypatch, application, terminal_phase)

    result = application.run_f09_slice(request, **_inputs())
    material = _read_log(request)

    terminal = tuple(
        observation
        for observation in material["observations"]
        if observation["status"] in ("FAILED", "REJECTED")
    )
    assert result.stopped_at == terminal_phase
    assert material["stopped_at"] == terminal_phase
    assert material["completed"] is False
    assert len(terminal) == 1
    assert terminal[0]["phase"] == terminal_phase
    assert terminal[0]["status"] == expected_status
    assert terminal[0]["case_id"] == request.case_id
    assert terminal[0]["mode"] == request.mode
    assert terminal[0]["issue_codes"]
    assert all(type(code) is str and code for code in terminal[0]["issue_codes"])


def test_d1_success_persists_all_five_phases_at_deterministic_locator(tmp_path, monkeypatch):
    import engine.f09.application as application

    request = _request(application, tmp_path / "success")
    _install_phase_owners(monkeypatch, application, None)

    result = application.run_f09_slice(request, **_inputs())
    material = _read_log(request)

    assert result.stopped_at is None
    assert material["completed"] is True
    assert material["stopped_at"] is None
    assert tuple(item["phase"] for item in material["observations"]) == (
        "SOURCE_PREFLIGHT",
        "EVIDENCE",
        "DECISION",
        "TRACE",
        "ARTIFACT",
    )
    assert tuple(item["status"] for item in material["observations"]) == ("SUCCEEDED",) * 5
    assert tuple(_locator(request).parent.glob("*.json")) == (_locator(request),)


def test_d1_persistence_failure_is_typed_and_fail_closed(tmp_path, monkeypatch):
    diagnostics = importlib.import_module("engine.f09.operator_diagnostics")
    import engine.f09.application as application

    request = _request(application, tmp_path / "write-failure", enable_f09=False)

    def fail_replace(source, target):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(diagnostics.os, "replace", fail_replace)

    with pytest.raises(F09WriteError) as caught:
        application.run_f09_slice(request, **_inputs())

    assert caught.value.issue_code == "APPLICATION.OBSERVATION_PERSISTENCE_FAILED"
    assert caught.value.field_path == "/artifact_root/operator-diagnostics"
    assert not _locator(request).exists()
    diagnostics_root = request.artifact_root / "operator-diagnostics"
    assert not diagnostics_root.exists() or not tuple(diagnostics_root.glob("*.tmp"))


def test_d1_readback_mismatch_is_typed_and_fail_closed(tmp_path, monkeypatch):
    diagnostics = importlib.import_module("engine.f09.operator_diagnostics")
    import engine.f09.application as application

    request = _request(application, tmp_path / "readback-failure", enable_f09=False)
    target = _locator(request)
    real_read_bytes = Path.read_bytes

    def mismatched_readback(path):
        if path == target:
            return b"simulated mismatch"
        return real_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", mismatched_readback)

    with pytest.raises(F09WriteError) as caught:
        application.run_f09_slice(request, **_inputs())

    assert caught.value.issue_code == "APPLICATION.OBSERVATION_PERSISTENCE_FAILED"
    assert caught.value.field_path == "/artifact_root/operator-diagnostics"
    assert target.exists()
    assert not tuple(target.parent.glob("*.tmp"))


def test_d1_missing_root_has_no_fallback_persistence(tmp_path, monkeypatch):
    import engine.f09.application as application

    monkeypatch.chdir(tmp_path)
    request = _request(application, None)
    result = application.run_f09_slice(request, **_inputs())

    assert result.stopped_at == "SOURCE_PREFLIGHT"
    assert result.observations[-1].issue_codes == ("APPLICATION.ARTIFACT_ROOT_REQUIRED",)
    assert not (tmp_path / "operator-diagnostics").exists()
    assert not (tmp_path / "artifacts").exists()


def test_d3_d4_d5_real_attempt_ledger_closes_failure_identity_and_retry_chain(tmp_path, monkeypatch):
    import engine.f09.artifacts as artifacts

    fixture = artifacts.provision_verified_run_manifest_fixture_v1()
    projections = {
        "RUN_SNAPSHOT": b"f09.run-fixture.run-snapshot.v1",
        "DECISION_RUN": b"f09.run-fixture.decision-run.v1",
        "FEEDBACK_ATTACHMENT": b"f09.run-fixture.feedback-attachment.v1",
    }
    request = artifacts.RunArtifactSetRequestV1(
        fixture.key,
        fixture.key.run_id,
        fixture.records[0].attempts[0].input_snapshot_refs,
        "f09.run-artifact-fixture.v1",
        projections,
    )
    real_write = artifacts._atomic_write_verified
    calls = []

    def fail_second_write(target, payload):
        calls.append(target)
        if len(calls) == 2:
            raise OSError("simulated ledger failure")
        return real_write(target, payload)

    monkeypatch.setattr(artifacts, "_atomic_write_verified", fail_second_write)
    failed_manifest = artifacts.coordinate_run_artifact_set_v1(
        tmp_path,
        request,
        existing_manifest=None,
        attempt_id="INITIAL",
        now="2026-07-27T00:00:00Z",
    )
    failed_attempt = failed_manifest.records[1].attempts[-1]

    assert failed_attempt.outcome == "FAILED"
    assert failed_attempt.finished_at
    assert failed_attempt.observed_digest is None
    assert failed_attempt.error_class == "OSError"
    assert failed_attempt.error_message_digest is not None
    assert failed_attempt.artifact_id == failed_manifest.records[1].artifact_id
    assert failed_attempt.idempotency_key == fixture.key.canonical_key_digest.value
    assert failed_attempt.input_snapshot_refs == request.input_snapshot_refs
    assert failed_attempt.attempt_number == 1
    assert failed_attempt.retry_of_attempt_id is None

    retried = artifacts.coordinate_run_artifact_set_v1(
        tmp_path,
        request,
        existing_manifest=failed_manifest,
        attempt_id="RETRY",
        now="2026-07-27T00:00:01Z",
    )
    attempts = retried.records[1].attempts

    assert tuple(attempt.attempt_number for attempt in attempts) == (1, 2)
    assert attempts[1].retry_of_attempt_id == attempts[0].attempt_id
    assert artifacts.validate_run_artifact_manifest_v1(retried) == retried.digest
    canonical = artifacts.canonicalize_artifact_records(retried.records)
    assert attempts[0].attempt_id.encode() in canonical
    assert attempts[0].idempotency_key.encode() in canonical
