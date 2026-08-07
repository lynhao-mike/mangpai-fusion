from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields
import inspect
from pathlib import Path
from typing import get_type_hints

import pytest


P2B_DISPOSITIONS = (
    ("P2B-F01", "Direct"),
    ("P2B-F02", "Hybrid"),
    ("P2B-F03", "Direct"),
    ("P2B-F04", "Prerequisite"),
    ("P2B-F05", "Direct"),
    ("P2B-F06", "Prerequisite"),
    ("P2B-F07", "Hybrid"),
    ("P2B-F08", "Direct"),
    ("P2B-F09", "Direct"),
    ("P2B-F10", "Hybrid"),
    ("P2B-F11", "Direct"),
    ("P2B-F12", "Hybrid"),
    ("P2B-F13", "Prerequisite"),
    ("P2B-F14", "Direct"),
    ("P2B-F15", "Hybrid"),
    ("P2B-F16", "Direct"),
)


def _request(application, **changes):
    values = {
        "case_id": "CASE-P2",
        "mode": "PREPROD_SHADOW",
        "chart_records": (),
        "hypothesis_records": (),
        "normalized_evidence_port": object(),
        "frozen_contract_port": object(),
        "request_id": "REQUEST-P2",
        "contract_ref": object(),
        "normative_contract_ref": object(),
        "machine_appendix_ref": object(),
        "artifact_projections": {"REPORT": b"report"},
        "artifact_key": object(),
        "existing_manifest": None,
        "attempt_id": "ATTEMPT-P2",
        "enable_f09": True,
        "artifact_root": Path("artifacts"),
        "now": "2026-07-25T00:00:00Z",
    }
    values.update(changes)
    return application.F09RunRequest(**values)


def _legacy_result(application, request, *, stopped_at=None):
    return application.F09RunResult(request, None, None, None, None, None, (), stopped_at)


def _versioned_inputs(artifacts, request, *, track):
    key = object.__new__(artifacts.RunArtifactSetKeyV1)
    object.__setattr__(key, "case_id", request.case_id)
    object.__setattr__(key, "run_id", "RUN-P2")
    object.__setattr__(key, "track", track)
    run_artifact_request = object.__new__(artifacts.RunArtifactSetRequestV1)
    object.__setattr__(run_artifact_request, "key", key)
    object.__setattr__(run_artifact_request, "run_id", "RUN-P2")
    return {
        "run_artifact_request": run_artifact_request,
        "target_refs_request": object(),
        "manifest_outer_ref_request": object(),
        "existing_run_manifest": None,
        "gate_inputs": (object(),),
        "competition_input": object(),
        "root_input": object(),
        "timing_input": object(),
    }


def _owner_calls(monkeypatch, application, legacy, *, r41, r40):
    calls = []

    def legacy_owner(actual_request, **kwargs):
        calls.append(("LEGACY", actual_request, kwargs))
        return legacy

    monkeypatch.setattr(application, "run_f09_slice", legacy_owner)
    monkeypatch.setattr(application, "coordinate_run_artifact_set_with_target_refs_v1", r41)
    monkeypatch.setattr(application, "construct_preprod_run_authority_v1", r40)
    return calls


def _versioned_definition():
    tree = ast.parse(Path("engine/f09/application.py").read_text(encoding="utf-8"))
    return next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "run_f09_slice_with_execution_authority_v1"
    )


def _parametrized_instances(function):
    multiplier = 1
    for decorator in function.decorator_list:
        if (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Attribute)
            and decorator.func.attr == "parametrize"
        ):
            values = decorator.args[1]
            assert isinstance(values, (ast.Tuple, ast.List))
            multiplier *= len(values.elts)
    return multiplier


def test_p2_public_abi_legacy_isolation_and_key_types_are_exact():
    import engine.f09 as package
    import engine.f09.application as application
    from engine.f09.artifacts import (
        IdempotencyKey,
        ManifestOuterRefRequestV1,
        RunArtifactSetKeyV1,
        RunArtifactSetRequestV1,
        RunArtifactTargetRefsRequestV1,
    )
    from engine.f09.decision import CompetitionInput, GateEvaluationInput, RootInput, TimingInput
    from engine.f09.feedback import PreprodRunAuthority

    assert tuple(field.name for field in fields(application.F09RunExecutionResultV1)) == (
        "run_result",
        "preprod_authority",
        "unsupported_reason",
    )
    assert get_type_hints(application.F09RunExecutionResultV1) == {
        "run_result": application.F09RunResult,
        "preprod_authority": PreprodRunAuthority | None,
        "unsupported_reason": application.Literal["STAGED_L6_UNSUPPORTED"] | None,
    }
    envelope = application.F09RunExecutionResultV1(object(), None, None)
    with pytest.raises(FrozenInstanceError):
        envelope.preprod_authority = object()
    assert get_type_hints(application.run_f09_slice_with_execution_authority_v1) == {
        "request": application.F09RunRequest,
        "run_artifact_request": RunArtifactSetRequestV1,
        "target_refs_request": RunArtifactTargetRefsRequestV1,
        "manifest_outer_ref_request": ManifestOuterRefRequestV1,
        "existing_run_manifest": application.ArtifactSetManifest | None,
        "gate_inputs": tuple[GateEvaluationInput, ...],
        "competition_input": CompetitionInput,
        "root_input": RootInput,
        "timing_input": TimingInput,
        "return": application.F09RunExecutionResultV1,
    }
    legacy_signature = inspect.signature(application.run_f09_slice)
    assert tuple(field.name for field in fields(application.F09RunResult)) == (
        "request", "evidence", "decision", "trace", "statement_set", "manifest",
        "observations", "stopped_at",
    )
    assert tuple(legacy_signature.parameters) == (
        "request", "gate_inputs", "competition_input", "root_input", "timing_input",
    )
    assert legacy_signature.return_annotation is application.F09RunResult
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
    assert IdempotencyKey is not RunArtifactSetKeyV1


@pytest.mark.parametrize("stopped_at", ("SOURCE_PREFLIGHT", "EVIDENCE", "DECISION", "TRACE", "ARTIFACT"))
def test_p2_legacy_stop_returns_exact_envelope_and_calls_no_authority_owner(monkeypatch, stopped_at):
    import engine.f09.application as application
    import engine.f09.artifacts as artifacts

    request = _request(application)
    legacy = _legacy_result(application, request, stopped_at=stopped_at)
    calls = _owner_calls(
        monkeypatch,
        application,
        legacy,
        r41=lambda *args, **kwargs: calls.append("R41"),
        r40=lambda **kwargs: calls.append("R40"),
    )
    result = application.run_f09_slice_with_execution_authority_v1(
        request,
        **_versioned_inputs(artifacts, request, track=artifacts.RunTrack.V5_V6_PREPROD),
    )

    assert len(calls) == 1
    assert calls[0][0] == "LEGACY"
    assert calls[0][1] is request
    assert result.run_result is legacy
    assert result.preprod_authority is result.unsupported_reason is None


def test_p2_staged_l6_is_exactly_unsupported_before_authority_owners(monkeypatch):
    import engine.f09.application as application
    import engine.f09.artifacts as artifacts

    request = _request(application, mode="STAGED_AUDIT")
    legacy = _legacy_result(application, request)
    calls = _owner_calls(
        monkeypatch,
        application,
        legacy,
        r41=lambda *args, **kwargs: calls.append("R41"),
        r40=lambda **kwargs: calls.append("R40"),
    )
    result = application.run_f09_slice_with_execution_authority_v1(
        request,
        **_versioned_inputs(artifacts, request, track=artifacts.RunTrack.STAGED_L6),
    )

    assert [call[0] if isinstance(call, tuple) else call for call in calls] == ["LEGACY"]
    assert result.run_result is legacy
    assert result.preprod_authority is None
    assert result.unsupported_reason == "STAGED_L6_UNSUPPORTED"


def test_p2_v5_v6_returns_actual_public_chain_without_copy_or_substitute(monkeypatch):
    import engine.f09.application as application
    import engine.f09.artifacts as artifacts

    request = _request(application)
    legacy = _legacy_result(application, request)
    inputs = _versioned_inputs(artifacts, request, track=artifacts.RunTrack.V5_V6_PREPROD)
    carrier = object.__new__(artifacts.RunArtifactSetResultV1)
    authority = object()
    calls = []

    def r41(root, actual_request, **kwargs):
        calls.append(("R41", root, actual_request, kwargs))
        return carrier

    def r40(**kwargs):
        calls.append(("R40", kwargs))
        return authority

    def legacy_owner(actual_request, **kwargs):
        calls.append(("LEGACY", actual_request, kwargs))
        return legacy

    monkeypatch.setattr(application, "run_f09_slice", legacy_owner)
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


@pytest.mark.parametrize(
    ("mismatch", "issue_code", "field_path"),
    (
        ("case", "APPLICATION.RUN_CASE_MISMATCH", "/run_artifact_request/key/case_id"),
        ("run", "APPLICATION.RUN_ID_MISMATCH", "/run_artifact_request/run_id"),
        ("track", "APPLICATION.RUN_TRACK_MISMATCH", "/run_artifact_request/key/track"),
        ("legacy_key", "APPLICATION.RUN_ARTIFACT_KEY_INVALID", "/run_artifact_request/key"),
    ),
)
def test_p2_identity_or_key_cross_use_fails_before_authority_owners(monkeypatch, mismatch, issue_code, field_path):
    import engine.f09.application as application
    import engine.f09.artifacts as artifacts
    from engine.f09.errors import F09ContractError

    request = _request(application)
    legacy = _legacy_result(application, request)
    inputs = _versioned_inputs(artifacts, request, track=artifacts.RunTrack.V5_V6_PREPROD)
    if mismatch == "case":
        object.__setattr__(inputs["run_artifact_request"].key, "case_id", "OTHER-CASE")
    elif mismatch == "run":
        object.__setattr__(inputs["run_artifact_request"].key, "run_id", "OTHER-RUN")
    elif mismatch == "track":
        object.__setattr__(inputs["run_artifact_request"].key, "track", artifacts.RunTrack.STAGED_L6)
    else:
        object.__setattr__(inputs["run_artifact_request"], "key", object.__new__(artifacts.IdempotencyKey))
    calls = _owner_calls(
        monkeypatch,
        application,
        legacy,
        r41=lambda *args, **kwargs: calls.append("R41"),
        r40=lambda **kwargs: calls.append("R40"),
    )

    with pytest.raises(F09ContractError) as caught:
        application.run_f09_slice_with_execution_authority_v1(request, **inputs)

    assert caught.value.issue_code == issue_code
    assert caught.value.field_path == field_path
    assert len(calls) == 1
    assert calls[0][0] == "LEGACY"


@pytest.mark.parametrize("failing_owner", ("R41", "R40"))
def test_p2_owner_failure_short_circuits_without_retry_or_envelope(monkeypatch, failing_owner):
    import engine.f09.application as application
    import engine.f09.artifacts as artifacts

    request = _request(application)
    legacy = _legacy_result(application, request)
    inputs = _versioned_inputs(artifacts, request, track=artifacts.RunTrack.V5_V6_PREPROD)
    carrier = object.__new__(artifacts.RunArtifactSetResultV1)
    failure = RuntimeError(f"{failing_owner} owner failure")
    calls = []

    def legacy_owner(actual_request, **kwargs):
        calls.append("LEGACY")
        return legacy

    def r41(*args, **kwargs):
        calls.append("R41")
        if failing_owner == "R41":
            raise failure
        return carrier

    def r40(**kwargs):
        calls.append("R40")
        raise failure

    monkeypatch.setattr(application, "run_f09_slice", legacy_owner)
    monkeypatch.setattr(application, "coordinate_run_artifact_set_with_target_refs_v1", r41)
    monkeypatch.setattr(application, "construct_preprod_run_authority_v1", r40)

    with pytest.raises(RuntimeError) as caught:
        application.run_f09_slice_with_execution_authority_v1(request, **inputs)

    assert caught.value is failure
    assert calls == (["LEGACY", "R41"] if failing_owner == "R41" else ["LEGACY", "R41", "R40"])


def test_p2_static_public_only_boundary_has_no_private_or_downstream_calls():
    definition = _versioned_definition()
    called_names = {
        node.func.id
        for node in ast.walk(definition)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called_attributes = {
        node.func.attr
        for node in ast.walk(definition)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert {
        "coordinate_run_artifact_set_with_target_refs_v1",
        "construct_preprod_run_authority_v1",
    } <= called_names
    assert called_names == {
        "run_f09_slice",
        "F09RunExecutionResultV1",
        "type",
        "F09ContractError",
        "coordinate_run_artifact_set_with_target_refs_v1",
        "construct_preprod_run_authority_v1",
    }
    assert called_attributes == {"get"}
    forbidden = {
        "validate_run_artifact_manifest_v1",
        "validate_run_artifact_set_result_issuance_v1",
        "bind_feedback_operation",
        "evaluate_learning_eligibility",
        "validate_learning_eligibility",
    }
    assert not (called_names & forbidden)
    assert not any(name.startswith("_") for name in called_names)


def test_p2_static_accounting_is_exactly_8_declarations_16_instances_and_16_dispositions():
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    declarations = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    ]
    expected_declaration_names = (
        "test_p2_public_abi_legacy_isolation_and_key_types_are_exact",
        "test_p2_legacy_stop_returns_exact_envelope_and_calls_no_authority_owner",
        "test_p2_staged_l6_is_exactly_unsupported_before_authority_owners",
        "test_p2_v5_v6_returns_actual_public_chain_without_copy_or_substitute",
        "test_p2_identity_or_key_cross_use_fails_before_authority_owners",
        "test_p2_owner_failure_short_circuits_without_retry_or_envelope",
        "test_p2_static_public_only_boundary_has_no_private_or_downstream_calls",
        "test_p2_static_accounting_is_exactly_8_declarations_16_instances_and_16_dispositions",
    )
    expected_dispositions = (
        ("P2B-F01", "Direct"),
        ("P2B-F02", "Hybrid"),
        ("P2B-F03", "Direct"),
        ("P2B-F04", "Prerequisite"),
        ("P2B-F05", "Direct"),
        ("P2B-F06", "Prerequisite"),
        ("P2B-F07", "Hybrid"),
        ("P2B-F08", "Direct"),
        ("P2B-F09", "Direct"),
        ("P2B-F10", "Hybrid"),
        ("P2B-F11", "Direct"),
        ("P2B-F12", "Hybrid"),
        ("P2B-F13", "Prerequisite"),
        ("P2B-F14", "Direct"),
        ("P2B-F15", "Hybrid"),
        ("P2B-F16", "Direct"),
    )
    forbidden_collection_hooks = {
        "pytest_collect_file",
        "pytest_collection_modifyitems",
        "pytest_generate_tests",
        "pytest_pycollect_makeitem",
    }
    module_function_names = {
        node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    disposition_ids = tuple(identifier for identifier, _category in P2B_DISPOSITIONS)
    categories = tuple(category for _identifier, category in P2B_DISPOSITIONS)

    assert tuple(function.name for function in declarations) == expected_declaration_names
    assert sum(_parametrized_instances(function) for function in declarations) == 16
    assert P2B_DISPOSITIONS == expected_dispositions
    assert disposition_ids == tuple(f"P2B-F{number:02d}" for number in range(1, 17))
    assert len(set(disposition_ids)) == 16
    assert categories.count("Direct") == 8
    assert categories.count("Hybrid") == 5
    assert categories.count("Prerequisite") == 3
    assert not (module_function_names & forbidden_collection_hooks)
