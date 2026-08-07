from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
import inspect
from pathlib import Path
from types import SimpleNamespace
from typing import get_type_hints

import pytest


def _request(application, **changes):
    values = {
        "case_id": "CASE-9",
        "mode": "STAGED_AUDIT",
        "chart_records": (),
        "hypothesis_records": (),
        "normalized_evidence_port": object(),
        "frozen_contract_port": object(),
        "request_id": "REQUEST-9",
        "contract_ref": object(),
        "normative_contract_ref": object(),
        "machine_appendix_ref": object(),
        "artifact_projections": {"REPORT": b"report"},
        "artifact_key": object(),
        "existing_manifest": None,
        "attempt_id": "ATTEMPT-9",
        "enable_f09": True,
        "markdown_path": Path("contract.md"),
        "snapshot_path": Path("snapshot.json"),
        "artifact_root": Path("artifacts"),
        "now": "2026-07-24T00:00:00Z",
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


def test_public_dtos_and_entrypoint_are_exact():
    import engine.f09.application as application
    import engine.f09 as package
    from engine.f09.decision import CompetitionInput, GateEvaluationInput, RootInput, TimingInput

    assert tuple(field.name for field in fields(application.F09RunRequest)) == (
        "case_id", "mode", "chart_records", "hypothesis_records",
        "normalized_evidence_port", "frozen_contract_port", "request_id",
        "contract_ref", "normative_contract_ref", "machine_appendix_ref",
        "artifact_projections", "artifact_key", "existing_manifest", "attempt_id",
        "enable_f09", "markdown_path", "snapshot_path", "artifact_root", "now",
    )
    assert tuple(field.name for field in fields(application.F09Observation)) == (
        "event", "case_id", "mode", "phase", "status", "issue_codes",
        "artifact_set_state",
    )
    assert tuple(field.name for field in fields(application.F09RunResult)) == (
        "request", "evidence", "decision", "trace", "statement_set", "manifest",
        "observations", "stopped_at",
    )
    legacy_hints = get_type_hints(application.run_f09_slice)
    assert legacy_hints == {
        "request": application.F09RunRequest,
        "gate_inputs": tuple[GateEvaluationInput, ...],
        "competition_input": CompetitionInput,
        "root_input": RootInput,
        "timing_input": TimingInput,
        "return": application.F09RunResult,
    }
    legacy_signature = inspect.signature(application.run_f09_slice)
    assert tuple(legacy_signature.parameters) == (
        "request", "gate_inputs", "competition_input", "root_input", "timing_input",
    )
    assert legacy_signature.parameters["request"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for name, parameter in legacy_signature.parameters.items()
        if name != "request"
    )
    assert tuple(
        name for name in package.__all__
        if name in {"F09Observation", "F09RunRequest", "F09RunResult", "run_f09_slice"}
    ) == (
        "F09Observation", "F09RunRequest", "F09RunResult", "run_f09_slice",
    )


@pytest.mark.parametrize(
    ("changes", "issue_code"),
    (
        ({"enable_f09": False}, "APPLICATION.OPT_IN_REQUIRED"),
        ({"mode": "PRODUCTION_DEFAULT"}, "APPLICATION.PRODUCTION_DEFAULT_FORBIDDEN"),
        ({"mode": "OTHER"}, "APPLICATION.MODE_UNSUPPORTED"),
        ({"artifact_root": None}, "APPLICATION.ARTIFACT_ROOT_REQUIRED"),
    ),
)
def test_preflight_rejects_before_any_owner_call(tmp_path, monkeypatch, changes, issue_code):
    import engine.f09.application as application

    calls = []
    for name in (
        "build_f09_evidence_package", "evaluate_f09", "build_trace",
        "build_statement_set", "validate_statement_projection",
        "coordinate_artifact_operation",
    ):
        monkeypatch.setattr(application, name, lambda *args, _name=name, **kwargs: calls.append(_name))

    request_changes = {"artifact_root": tmp_path / "artifacts", **changes}
    result = application.run_f09_slice(_request(application, **request_changes), **_inputs())

    assert calls == []
    assert result.stopped_at == "SOURCE_PREFLIGHT"
    assert result.evidence is result.decision is result.trace is result.statement_set is result.manifest is None
    assert result.observations == (
        application.F09Observation(
            "F09_SLICE_PHASE", "CASE-9", changes.get("mode", "STAGED_AUDIT"),
            "SOURCE_PREFLIGHT", "REJECTED", (issue_code,), None,
        ),
    )


def test_preflight_uses_contract_priority(monkeypatch):
    import engine.f09.application as application

    monkeypatch.setattr(application, "build_f09_evidence_package", lambda **kwargs: pytest.fail("owner called"))
    result = application.run_f09_slice(
        _request(application, enable_f09=False, mode="PRODUCTION_DEFAULT", artifact_root=None),
        **_inputs(),
    )
    assert result.observations[0].issue_codes == ("APPLICATION.OPT_IN_REQUIRED",)


def test_success_calls_canonical_owners_once_in_order_and_preserves_identities(tmp_path, monkeypatch):
    import engine.f09.application as application
    from engine.f09.contracts import ArtifactSetState

    calls = []
    evidence = object()
    decision = object()
    trace = object()
    statement_set = object()
    projections = {"REPORT": b"report"}
    request = _request(
        application,
        artifact_projections=projections,
        mode="PREPROD_SHADOW",
        artifact_root=tmp_path / "artifacts",
    )
    manifest = SimpleNamespace(state=ArtifactSetState.COMPLETE_VERIFIED, detected_issues=())

    def evidence_owner(**kwargs):
        calls.append(("EVIDENCE", kwargs))
        return evidence

    def decision_owner(actual_evidence, **kwargs):
        calls.append(("DECISION", actual_evidence, kwargs))
        return decision

    def trace_owner(actual_evidence, actual_decision, **kwargs):
        calls.append(("TRACE", actual_evidence, actual_decision, kwargs))
        return trace

    def statement_owner(actual_trace, actual_decision, **kwargs):
        calls.append(("STATEMENT", actual_trace, actual_decision, kwargs))
        return statement_set

    def validator(actual_set, actual_trace, actual_decision, actual_evidence, **kwargs):
        calls.append(("VALIDATE", actual_set, actual_trace, actual_decision, actual_evidence, kwargs))
        return SimpleNamespace(valid=True, detected_issues=())

    def artifact_owner(root, actual_set, actual_projections, **kwargs):
        calls.append(("ARTIFACT", root, actual_set, actual_projections, kwargs))
        return manifest

    monkeypatch.setattr(application, "build_f09_evidence_package", evidence_owner)
    monkeypatch.setattr(application, "evaluate_f09", decision_owner)
    monkeypatch.setattr(application, "build_trace", trace_owner)
    monkeypatch.setattr(application, "build_statement_set", statement_owner)
    monkeypatch.setattr(application, "validate_statement_projection", validator)
    monkeypatch.setattr(application, "coordinate_artifact_operation", artifact_owner)

    result = application.run_f09_slice(request, **_inputs())

    assert [call[0] for call in calls] == ["EVIDENCE", "DECISION", "TRACE", "STATEMENT", "VALIDATE", "ARTIFACT"]
    assert calls[0][1]["track"].value == "V5_V6_PREPROD"
    assert calls[1][2]["normalized_evidence_port"] is request.normalized_evidence_port
    assert calls[1][2]["frozen_contract_port"] is request.frozen_contract_port
    assert calls[2][3]["normative_contract_ref"] is request.normative_contract_ref
    assert calls[3][3]["machine_appendix_ref"] is request.machine_appendix_ref
    assert calls[5][3] is projections
    assert result.manifest is manifest
    assert result.stopped_at is None
    assert tuple(item.phase for item in result.observations) == (
        "SOURCE_PREFLIGHT", "EVIDENCE", "DECISION", "TRACE", "ARTIFACT",
    )
    assert tuple(item.status for item in result.observations) == ("SUCCEEDED",) * 5


def test_complete_manifest_with_returned_issues_stops_at_artifact(tmp_path, monkeypatch):
    import engine.f09.application as application
    from engine.f09.contracts import ArtifactSetState, DetectedIssue

    monkeypatch.setattr(application, "build_f09_evidence_package", lambda **kwargs: object())
    monkeypatch.setattr(application, "evaluate_f09", lambda *args, **kwargs: object())
    monkeypatch.setattr(application, "build_trace", lambda *args, **kwargs: object())
    monkeypatch.setattr(application, "build_statement_set", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        application,
        "validate_statement_projection",
        lambda *args, **kwargs: SimpleNamespace(valid=True, detected_issues=()),
    )
    manifest = SimpleNamespace(
        state=ArtifactSetState.COMPLETE_VERIFIED,
        detected_issues=(DetectedIssue("ARTIFACT.REVIEW_REQUIRED", "/artifact"),),
    )
    monkeypatch.setattr(application, "coordinate_artifact_operation", lambda *args, **kwargs: manifest)

    result = application.run_f09_slice(
        _request(application, artifact_root=tmp_path / "artifacts"),
        **_inputs(),
    )

    assert result.manifest is manifest
    assert result.stopped_at == "ARTIFACT"
    assert result.observations[-1] == application.F09Observation(
        "F09_SLICE_PHASE", "CASE-9", "STAGED_AUDIT", "ARTIFACT", "FAILED",
        ("ARTIFACT.REVIEW_REQUIRED",), "COMPLETE_VERIFIED",
    )


def test_invalid_projection_stops_before_artifact_and_projects_returned_issues(tmp_path, monkeypatch):
    import engine.f09.application as application
    from engine.f09.contracts import DetectedIssue

    monkeypatch.setattr(application, "build_f09_evidence_package", lambda **kwargs: object())
    monkeypatch.setattr(application, "evaluate_f09", lambda *args, **kwargs: object())
    monkeypatch.setattr(application, "build_trace", lambda *args, **kwargs: object())
    monkeypatch.setattr(application, "build_statement_set", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        application, "validate_statement_projection",
        lambda *args, **kwargs: SimpleNamespace(
            valid=False,
            detected_issues=(DetectedIssue("PROJECTION.BAD", "/projection"),),
        ),
    )
    monkeypatch.setattr(application, "coordinate_artifact_operation", lambda *args, **kwargs: pytest.fail("artifact called"))

    result = application.run_f09_slice(
        _request(application, artifact_root=tmp_path / "artifacts"),
        **_inputs(),
    )

    assert result.stopped_at == "TRACE"
    assert result.manifest is None
    assert result.observations[-1].phase == "TRACE"
    assert result.observations[-1].status == "FAILED"
    assert result.observations[-1].issue_codes == ("PROJECTION.BAD",)


def test_f09_errors_stop_at_owner_and_unexpected_errors_propagate(tmp_path, monkeypatch):
    import engine.f09.application as application
    from engine.f09.errors import F09ContractError

    monkeypatch.setattr(
        application, "build_f09_evidence_package",
        lambda **kwargs: (_ for _ in ()).throw(F09ContractError("SOURCE.BAD", "/source", "hidden")),
    )
    result = application.run_f09_slice(
        _request(application, artifact_root=tmp_path / "artifacts"),
        **_inputs(),
    )
    assert result.stopped_at == "EVIDENCE"
    assert result.observations[-1].issue_codes == ("SOURCE.BAD",)

    monkeypatch.setattr(application, "build_f09_evidence_package", lambda **kwargs: (_ for _ in ()).throw(ValueError("not projected")))
    with pytest.raises(ValueError, match="not projected"):
        application.run_f09_slice(_request(application), **_inputs())


def _versioned_inputs(application, artifacts, request, *, track):
    key = object.__new__(artifacts.RunArtifactSetKeyV1)
    object.__setattr__(key, "case_id", request.case_id)
    object.__setattr__(key, "run_id", "RUN-9")
    object.__setattr__(key, "track", track)
    run_artifact_request = object.__new__(artifacts.RunArtifactSetRequestV1)
    object.__setattr__(run_artifact_request, "key", key)
    object.__setattr__(run_artifact_request, "run_id", "RUN-9")
    target_refs_request = artifacts.RunArtifactTargetRefsRequestV1(object(), object(), object())
    manifest_outer_ref_request = artifacts.ManifestOuterRefRequestV1(
        "REV-9", "manifest.v1", "contract.v1", "SOURCE-9", request.now,
    )
    return {
        "run_artifact_request": run_artifact_request,
        "target_refs_request": target_refs_request,
        "manifest_outer_ref_request": manifest_outer_ref_request,
        "existing_run_manifest": None,
        **_inputs(),
    }


def _legacy_result(application, request, *, stopped_at=None):
    return application.F09RunResult(
        request, None, None, None, None, None, (), stopped_at,
    )


class _PoisonCapture:
    def __getattribute__(self, name):
        raise AssertionError(f"capture material consumed: {name}")

    def __iter__(self):
        raise AssertionError("capture material iterated")

    def __copy__(self):
        raise AssertionError("capture material copied")

    def __deepcopy__(self, memo):
        raise AssertionError("capture material deep-copied")


def _poison_capture_inputs(inputs):
    return {
        **inputs,
        "target_refs_request": _PoisonCapture(),
        "manifest_outer_ref_request": _PoisonCapture(),
    }


def test_versioned_public_dto_signature_and_export_are_exact():
    import engine.f09 as package
    import engine.f09.application as application
    from engine.f09.artifacts import (
        ArtifactSetManifest,
        ManifestOuterRefRequestV1,
        RunArtifactSetRequestV1,
        RunArtifactTargetRefsRequestV1,
    )
    from engine.f09.decision import CompetitionInput, GateEvaluationInput, RootInput, TimingInput
    from engine.f09.feedback import PreprodRunAuthority

    assert tuple(field.name for field in fields(application.F09RunExecutionResultV1)) == (
        "run_result", "preprod_authority", "unsupported_reason",
    )
    assert get_type_hints(application.F09RunExecutionResultV1) == {
        "run_result": application.F09RunResult,
        "preprod_authority": PreprodRunAuthority | None,
        "unsupported_reason": application.Literal["STAGED_L6_UNSUPPORTED"] | None,
    }
    frozen = application.F09RunExecutionResultV1(object(), None, None)
    with pytest.raises(FrozenInstanceError):
        frozen.preprod_authority = object()

    callable_hints = get_type_hints(application.run_f09_slice_with_execution_authority_v1)
    assert callable_hints == {
        "request": application.F09RunRequest,
        "run_artifact_request": RunArtifactSetRequestV1,
        "target_refs_request": RunArtifactTargetRefsRequestV1,
        "manifest_outer_ref_request": ManifestOuterRefRequestV1,
        "existing_run_manifest": ArtifactSetManifest | None,
        "gate_inputs": tuple[GateEvaluationInput, ...],
        "competition_input": CompetitionInput,
        "root_input": RootInput,
        "timing_input": TimingInput,
        "return": application.F09RunExecutionResultV1,
    }
    signature = inspect.signature(application.run_f09_slice_with_execution_authority_v1)
    assert tuple(signature.parameters) == (
        "request", "run_artifact_request", "target_refs_request",
        "manifest_outer_ref_request", "existing_run_manifest", "gate_inputs",
        "competition_input", "root_input", "timing_input",
    )
    assert signature.parameters["request"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for name, parameter in signature.parameters.items()
        if name != "request"
    )
    assert package.__all__ == (
        "F09Observation", "F09RunExecutionResultV1", "F09RunRequest",
        "F09RunResult", "run_f09_slice", "run_f09_slice_with_execution_authority_v1",
    )


@pytest.mark.parametrize(
    "stopped_at",
    ("SOURCE_PREFLIGHT", "EVIDENCE", "DECISION", "TRACE", "ARTIFACT"),
)
def test_versioned_legacy_stop_preserves_identity_and_calls_no_versioned_owner(monkeypatch, stopped_at):
    import engine.f09.application as application
    import engine.f09.artifacts as artifacts

    request = _request(application, mode="PREPROD_SHADOW")
    legacy = _legacy_result(application, request, stopped_at=stopped_at)
    inputs = _poison_capture_inputs(_versioned_inputs(
        application,
        artifacts,
        request,
        track=artifacts.RunTrack.V5_V6_PREPROD,
    ))
    calls = []

    def legacy_owner(actual_request, **kwargs):
        calls.append(("LEGACY", actual_request, kwargs))
        return legacy

    monkeypatch.setattr(application, "run_f09_slice", legacy_owner)
    monkeypatch.setattr(application, "coordinate_run_artifact_set_with_target_refs_v1", lambda *args, **kwargs: calls.append("R41"))
    monkeypatch.setattr(application, "construct_preprod_run_authority_v1", lambda **kwargs: calls.append("R40"))

    result = application.run_f09_slice_with_execution_authority_v1(
        request,
        **inputs,
    )

    assert len(calls) == 1
    assert calls[0][0] == "LEGACY"
    assert calls[0][1] is request
    assert calls[0][2]["gate_inputs"] is inputs["gate_inputs"]
    assert calls[0][2]["competition_input"] is inputs["competition_input"]
    assert calls[0][2]["root_input"] is inputs["root_input"]
    assert calls[0][2]["timing_input"] is inputs["timing_input"]
    assert result.run_result is legacy
    assert result.preprod_authority is result.unsupported_reason is None


def test_versioned_staged_success_is_pre_r41_unsupported(monkeypatch):
    import engine.f09.application as application
    import engine.f09.artifacts as artifacts

    request = _request(application, mode="STAGED_AUDIT")
    legacy = _legacy_result(application, request)
    calls = []
    monkeypatch.setattr(application, "run_f09_slice", lambda *args, **kwargs: calls.append("LEGACY") or legacy)
    monkeypatch.setattr(application, "coordinate_run_artifact_set_with_target_refs_v1", lambda *args, **kwargs: calls.append("R41"))
    monkeypatch.setattr(application, "construct_preprod_run_authority_v1", lambda **kwargs: calls.append("R40"))

    inputs = _poison_capture_inputs(
        _versioned_inputs(application, artifacts, request, track=artifacts.RunTrack.STAGED_L6)
    )
    result = application.run_f09_slice_with_execution_authority_v1(request, **inputs)

    assert calls == ["LEGACY"]
    assert result.run_result is legacy
    assert result.preprod_authority is None
    assert result.unsupported_reason == "STAGED_L6_UNSUPPORTED"


def test_versioned_preprod_hands_actual_ingress_to_r41_and_carrier_to_r40_once(monkeypatch):
    import engine.f09.application as application
    import engine.f09.artifacts as artifacts

    request = _request(application, mode="PREPROD_SHADOW")
    legacy = _legacy_result(application, request)
    inputs = _versioned_inputs(application, artifacts, request, track=artifacts.RunTrack.V5_V6_PREPROD)
    carrier = object.__new__(artifacts.RunArtifactSetResultV1)
    authority = object()
    calls = []

    def r41(root, actual_request, **kwargs):
        calls.append(("R41", root, actual_request, kwargs))
        return carrier

    def r40(**kwargs):
        calls.append(("R40", kwargs))
        return authority

    monkeypatch.setattr(application, "run_f09_slice", lambda *args, **kwargs: calls.append(("LEGACY", args, kwargs)) or legacy)
    monkeypatch.setattr(application, "coordinate_run_artifact_set_with_target_refs_v1", r41)
    monkeypatch.setattr(application, "construct_preprod_run_authority_v1", r40)

    result = application.run_f09_slice_with_execution_authority_v1(request, **inputs)

    assert [call[0] for call in calls] == ["LEGACY", "R41", "R40"]
    assert calls[1][1] is request.artifact_root
    assert calls[1][2] is inputs["run_artifact_request"]
    assert calls[1][3]["target_refs_request"] is inputs["target_refs_request"]
    assert calls[1][3]["manifest_outer_ref_request"] is inputs["manifest_outer_ref_request"]
    assert calls[1][3]["existing_manifest"] is inputs["existing_run_manifest"]
    assert calls[1][3]["attempt_id"] is request.attempt_id
    assert calls[1][3]["now"] is request.now
    assert calls[2][1]["run_artifact_set_result"] is carrier
    assert result.run_result is legacy
    assert result.preprod_authority is authority
    assert result.unsupported_reason is None


@pytest.mark.parametrize("mismatch", ["case", "run", "track"])
def test_versioned_pre_r41_identity_mismatch_calls_no_versioned_owner(monkeypatch, mismatch):
    import engine.f09.application as application
    import engine.f09.artifacts as artifacts
    from engine.f09.errors import F09ContractError

    request = _request(application, mode="PREPROD_SHADOW")
    legacy = _legacy_result(application, request)
    inputs = _versioned_inputs(application, artifacts, request, track=artifacts.RunTrack.V5_V6_PREPROD)
    key = inputs["run_artifact_request"].key
    if mismatch == "case":
        object.__setattr__(key, "case_id", "OTHER")
    elif mismatch == "run":
        object.__setattr__(key, "run_id", "OTHER")
    else:
        object.__setattr__(key, "track", artifacts.RunTrack.STAGED_L6)
    calls = []
    monkeypatch.setattr(application, "run_f09_slice", lambda *args, **kwargs: calls.append("LEGACY") or legacy)
    monkeypatch.setattr(application, "coordinate_run_artifact_set_with_target_refs_v1", lambda *args, **kwargs: calls.append("R41"))
    monkeypatch.setattr(application, "construct_preprod_run_authority_v1", lambda **kwargs: calls.append("R40"))

    with pytest.raises(F09ContractError):
        application.run_f09_slice_with_execution_authority_v1(request, **inputs)

    assert calls == ["LEGACY"]


def test_versioned_legacy_key_cross_use_fails_typed_before_versioned_owner(monkeypatch):
    import engine.f09.application as application
    import engine.f09.artifacts as artifacts
    from engine.f09.errors import F09ContractError

    request = _request(application, mode="PREPROD_SHADOW")
    legacy = _legacy_result(application, request)
    inputs = _versioned_inputs(
        application,
        artifacts,
        request,
        track=artifacts.RunTrack.V5_V6_PREPROD,
    )
    object.__setattr__(
        inputs["run_artifact_request"],
        "key",
        object.__new__(artifacts.IdempotencyKey),
    )
    calls = []
    monkeypatch.setattr(application, "run_f09_slice", lambda *args, **kwargs: calls.append("LEGACY") or legacy)
    monkeypatch.setattr(application, "coordinate_run_artifact_set_with_target_refs_v1", lambda *args, **kwargs: calls.append("R41"))
    monkeypatch.setattr(application, "construct_preprod_run_authority_v1", lambda **kwargs: calls.append("R40"))

    with pytest.raises(F09ContractError) as caught:
        application.run_f09_slice_with_execution_authority_v1(request, **inputs)

    assert caught.value.issue_code == "APPLICATION.RUN_ARTIFACT_KEY_INVALID"
    assert caught.value.field_path == "/run_artifact_request/key"
    assert calls == ["LEGACY"]


@pytest.mark.parametrize(
    "malformed_capture",
    ("target_refs_request", "manifest_outer_ref_request"),
)
def test_versioned_malformed_capture_is_handed_once_to_r41_owner_and_fails_before_r40(
    monkeypatch,
    malformed_capture,
):
    import engine.f09.application as application
    import engine.f09.artifacts as artifacts

    request = _request(application, mode="PREPROD_SHADOW")
    legacy = _legacy_result(application, request)
    inputs = _versioned_inputs(
        application,
        artifacts,
        request,
        track=artifacts.RunTrack.V5_V6_PREPROD,
    )
    malformed = object()
    inputs[malformed_capture] = malformed
    failure = RuntimeError(f"R41 rejected malformed {malformed_capture}")
    calls = []
    monkeypatch.setattr(
        application,
        "run_f09_slice",
        lambda *args, **kwargs: calls.append(("LEGACY", args, kwargs)) or legacy,
    )

    def r41(*args, **kwargs):
        calls.append(("R41", args, kwargs))
        assert kwargs[malformed_capture] is malformed
        raise failure

    monkeypatch.setattr(application, "coordinate_run_artifact_set_with_target_refs_v1", r41)
    monkeypatch.setattr(
        application,
        "construct_preprod_run_authority_v1",
        lambda **kwargs: calls.append(("R40", kwargs)),
    )

    with pytest.raises(RuntimeError) as caught:
        application.run_f09_slice_with_execution_authority_v1(request, **inputs)

    assert caught.value is failure
    assert [call[0] for call in calls] == ["LEGACY", "R41"]


def test_versioned_r41_failure_is_propagated_once_before_r40(monkeypatch):
    import engine.f09.application as application
    import engine.f09.artifacts as artifacts

    request = _request(application, mode="PREPROD_SHADOW")
    legacy = _legacy_result(application, request)
    failure = RuntimeError("R41-owned identity failure")
    calls = []
    monkeypatch.setattr(application, "run_f09_slice", lambda *args, **kwargs: calls.append("LEGACY") or legacy)

    def r41(*args, **kwargs):
        calls.append("R41")
        raise failure

    monkeypatch.setattr(application, "coordinate_run_artifact_set_with_target_refs_v1", r41)
    monkeypatch.setattr(application, "construct_preprod_run_authority_v1", lambda **kwargs: calls.append("R40"))

    with pytest.raises(RuntimeError) as caught:
        application.run_f09_slice_with_execution_authority_v1(
            request, **_versioned_inputs(application, artifacts, request, track=artifacts.RunTrack.V5_V6_PREPROD),
        )

    assert caught.value is failure
    assert calls == ["LEGACY", "R41"]


def test_versioned_r40_failure_is_propagated_once_without_envelope(monkeypatch):
    import engine.f09.application as application
    import engine.f09.artifacts as artifacts

    request = _request(application, mode="PREPROD_SHADOW")
    legacy = _legacy_result(application, request)
    carrier = object.__new__(artifacts.RunArtifactSetResultV1)
    failure = RuntimeError("R40-owned authority failure")
    calls = []
    monkeypatch.setattr(application, "run_f09_slice", lambda *args, **kwargs: calls.append("LEGACY") or legacy)
    monkeypatch.setattr(application, "coordinate_run_artifact_set_with_target_refs_v1", lambda *args, **kwargs: calls.append("R41") or carrier)

    def r40(**kwargs):
        calls.append("R40")
        raise failure

    monkeypatch.setattr(application, "construct_preprod_run_authority_v1", r40)

    with pytest.raises(RuntimeError) as caught:
        application.run_f09_slice_with_execution_authority_v1(
            request, **_versioned_inputs(application, artifacts, request, track=artifacts.RunTrack.V5_V6_PREPROD),
        )

    assert caught.value is failure
    assert calls == ["LEGACY", "R41", "R40"]
