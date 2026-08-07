import ast
import base64
import inspect
import os
from collections.abc import Mapping
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from typing import get_args, get_type_hints
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import engine.f09.artifacts as artifacts
from engine.f09.canonical_json import bounded_jcs_sha256, canonicalize_bounded_jcs, parse_bounded_jcs
from engine.f09.contracts import (
    AbsentDeclarationBinding,
    ArtifactItemState,
    ArtifactSetState,
    DecisionAction,
    DetectedIssue,
    DigestRef,
    NotApplicableDeclarationBinding,
    ResolvedDeclarationBinding,
    RunTrack,
    UnavailableDeclarationBinding,
    UnresolvableDeclarationBinding,
)
from engine.f09.errors import F09ContractError, F09Error, F09IntegrityError, F09WriteError
from engine.f09.trace import (
    DecisionTraceRef,
    DigestMissing,
    DigestPresent,
    StatementSet,
    VersionedObjectRef,
)


NOW = "2026-07-21T00:00:00Z"
ROLES = ("REPORT", "STATEMENT_RECORDS", "STATEMENT_INDEX")
RAW_CANONICALIZATION = "RAW-UTF8"
KEY_CANONICALIZATION = "RFC8785-JCS-UTF8"
_AUTHORITY_OWNER_NAMES = {
    "build_artifact_operation_authority",
    "_independent_sha256",
    "_artifact_root_material",
    "_artifact_payload_material",
    "_versioned_object_ref_material",
    "_frozen_declaration_ref_material",
    "_declaration_binding_material",
    "_card_identity_ref_material",
    "_standard_statement_material",
    "_report_section_material",
    "_statement_index_material",
    "_authority_material_error",
    "_digest_material",
    "_digest_binding_material",
    "_artifact_role_material",
}
_AUTHORITY_FORBIDDEN_NAMES = {
    "Path", "open", "time", "datetime", "uuid4", "random", "subprocess",
    "socket", "requests", "tools", "pickle", "json", "asdict", "repr", "vars",
    "evaluate_learning_eligibility", "validate_learning_eligibility", "__import__",
}
_AUTHORITY_FORBIDDEN_MEMBERS = {
    "read_bytes", "read_text", "write_bytes", "write_text", "open", "__dict__",
    "__dataclass_fields__", "fields",
}


def _authority_owner_ast_violations(module):
    owner_nodes = [
        node for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in _AUTHORITY_OWNER_NAMES
    ]
    return {
        "names": {
            node.id
            for owner in owner_nodes
            for node in ast.walk(owner)
            if isinstance(node, ast.Name) and node.id in _AUTHORITY_FORBIDDEN_NAMES
        },
        "members": {
            node.attr
            for owner in owner_nodes
            for node in ast.walk(owner)
            if isinstance(node, ast.Attribute) and node.attr in _AUTHORITY_FORBIDDEN_MEMBERS
        },
        "calls": {
            node.func.id
            for owner in owner_nodes
            for node in ast.walk(owner)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in _AUTHORITY_FORBIDDEN_NAMES
        },
    }


def _validator_call_count(module):
    builder = next(
        node for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "build_artifact_operation_authority"
    )
    return sum(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "validate_statement_projection"
        for node in ast.walk(builder)
    )


def _digest(payload: bytes, canonicalization: str = RAW_CANONICALIZATION) -> DigestRef:
    return DigestRef("sha256", canonicalization, sha256(payload).hexdigest())


def _canonical_artifact_graph(decision_case):
    from engine.f09.decision import evaluate_f09
    from engine.f09.evidence import build_f09_evidence_package
    from engine.f09.trace import DigestPresent, build_statement_set, build_trace

    contract_path = Path("engine/contracts/12-real-world-function-evidence-cards-v1.md")
    appendix_path = Path("mapping/real-world-function-evidence-cards-v1.yaml")
    normative_contract_ref = VersionedObjectRef(
        "CONTRACT",
        "F09-NORMATIVE-CONTRACT",
        "rev-frozen",
        "markdown-contract.v1",
        "real-world-function-evidence-cards-v1",
        DigestPresent("PRESENT", _digest(contract_path.read_bytes(), "RAW-BYTES")),
        contract_path.as_posix(),
        "2026-07-19T00:00:00Z",
    )
    machine_appendix_ref = VersionedObjectRef(
        "MACHINE_APPENDIX",
        "F09-MACHINE-APPENDIX",
        "rev-frozen",
        "machine-appendix.v1",
        "real-world-function-evidence-cards-v1",
        DigestPresent("PRESENT", _digest(appendix_path.read_bytes(), "RAW-BYTES")),
        appendix_path.as_posix(),
        "2026-07-19T00:00:00Z",
    )
    package = build_f09_evidence_package(
        case_id=decision_case["package"].case_id,
        track=RunTrack.MANUAL_IMPORT,
        markdown_path=contract_path,
        snapshot_path=Path("plans/production-implementation-pi-300-f09-source-snapshots-v1.json"),
        chart_records=(),
        hypothesis_records=(),
    )
    decision = replace(
        evaluate_f09(**decision_case, request_id="REQUEST-ARTIFACT-1"),
        package_id=package.package_id,
    )
    trace = build_trace(
        package,
        decision,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
        created_at="2026-07-19T00:00:00Z",
    )
    statement_set = build_statement_set(
        trace,
        decision,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
        generated_at="2026-07-19T00:00:00Z",
    )
    return package, decision, trace, statement_set, normative_contract_ref, machine_appendix_ref


def _oracle_digest(digest):
    return {
        "algorithm": digest.algorithm,
        "canonicalization": digest.canonicalization,
        "value": digest.value,
    }


def _oracle_digest_binding(binding):
    if type(binding) is DigestPresent:
        return {"status": "PRESENT", "digest": _oracle_digest(binding.digest)}
    if type(binding) is DigestMissing:
        return {"status": "MISSING", "digest": None, "issue_id": binding.issue_id}
    raise AssertionError("oracle received unsupported digest binding")


def _oracle_ref(ref):
    return {
        "object_type": ref.object_type,
        "object_id": ref.object_id,
        "revision_id": ref.revision_id,
        "schema_version": ref.schema_version,
        "contract_version": ref.contract_version,
        "digest_binding": _oracle_digest_binding(ref.digest_binding),
        "source_locator_id": ref.source_locator_id,
        "captured_at": ref.captured_at,
    }


def _oracle_declaration_ref(ref):
    return {
        "declaration_id": ref.declaration_id,
        "declaration_type": ref.declaration_type,
        "card_id": ref.card_id,
        "contract_version": ref.contract_version,
        "declaration_schema_version": ref.declaration_schema_version,
        "content_digest": _oracle_digest(ref.content_digest),
    }


def _oracle_declaration(binding):
    if type(binding) is ResolvedDeclarationBinding:
        return {"presence": binding.presence, "ref": _oracle_declaration_ref(binding.ref)}
    if type(binding) in (AbsentDeclarationBinding, NotApplicableDeclarationBinding):
        return {"presence": binding.presence, "reason_code": binding.reason_code}
    if type(binding) is UnavailableDeclarationBinding:
        return {
            "presence": binding.presence,
            "reason_code": binding.reason_code,
            "issue_ids": tuple(binding.issue_ids),
        }
    if type(binding) is UnresolvableDeclarationBinding:
        return {
            "presence": binding.presence,
            "attempted_ref": _oracle_declaration_ref(binding.attempted_ref),
            "reason_code": binding.reason_code,
            "issue_ids": tuple(binding.issue_ids),
        }
    raise AssertionError("oracle received unsupported declaration binding")


def _oracle_card(ref):
    return {
        "card_identity_ref_id": ref.card_identity_ref_id,
        "card_id": ref.card_id,
        "normative_contract_ref": _oracle_ref(ref.normative_contract_ref),
        "machine_appendix_ref": _oracle_ref(ref.machine_appendix_ref),
        "field_path": ref.field_path,
        "source_field_state": ref.source_field_state,
        "evaluator_state": ref.evaluator_state.value,
        "declaration_status": ref.declaration_status,
        "runtime_capability_status": ref.runtime_capability_status,
        "source_locator_ids": tuple(ref.source_locator_ids),
        "issue_ids": tuple(ref.issue_ids),
    }


def _oracle_statement(statement):
    return {
        "statement_id": statement.statement_id,
        "statement_revision_id": statement.statement_revision_id,
        "statement_schema_version": statement.statement_schema_version,
        "case_id": statement.case_id,
        "statement_set_id": statement.statement_set_id,
        "track": statement.track.value,
        "semantic_scope": statement.semantic_scope,
        "domain": statement.domain,
        "statement_text": statement.statement_text,
        "display_section": statement.display_section,
        "decision_result_id": statement.decision_result_id,
        "action_id": statement.action_id,
        "basis_record_ids": tuple(statement.basis_record_ids),
        "evidence_refs": tuple(_oracle_ref(ref) for ref in statement.evidence_refs),
        "relation_ids": tuple(statement.relation_ids),
        "source_locator_ids": tuple(statement.source_locator_ids),
        "card_identity_refs": tuple(_oracle_card(ref) for ref in statement.card_identity_refs),
        "confidence_snapshot_ref": (
            None if statement.confidence_snapshot_ref is None
            else _oracle_ref(statement.confidence_snapshot_ref)
        ),
        "output_precision_binding": _oracle_declaration(statement.output_precision_binding),
        "validation_plan_binding": _oracle_declaration(statement.validation_plan_binding),
        "feedback_policy": statement.feedback_policy,
        "content_digest": _oracle_digest(statement.content_digest),
        "integrity": statement.integrity,
        "issue_ids": tuple(statement.issue_ids),
    }


def _oracle_decision_trace_ref(ref):
    return {
        "result_ref": _oracle_ref(ref.result_ref),
        "action_id": ref.action_id,
        "selected_action": ref.selected_action.value,
        "basis_record_ids": tuple(ref.basis_record_ids),
        "blocking_issue_ids": tuple(ref.blocking_issue_ids),
        "nonblocking_issue_ids": tuple(ref.nonblocking_issue_ids),
        "source_decision_refs": tuple(ref.source_decision_refs),
        "output_precision_binding": _oracle_declaration(ref.output_precision_binding),
        "validation_plan_binding": _oracle_declaration(ref.validation_plan_binding),
        "structural_validity": ref.structural_validity,
    }


def _oracle_sign_statement(statement):
    revision_material = _oracle_statement(statement)
    for field_name in ("statement_set_id", "statement_revision_id", "content_digest"):
        revision_material.pop(field_name)
    revision_digest = bounded_jcs_sha256(revision_material)
    revised = replace(statement, statement_revision_id=f"rev-{revision_digest.value[:16]}")
    content_material = _oracle_statement(revised)
    for field_name in ("statement_revision_id", "content_digest"):
        content_material.pop(field_name)
    return replace(revised, content_digest=bounded_jcs_sha256(content_material))


def _oracle_statement_set_content_digest(statement_set):
    return bounded_jcs_sha256({
        "statement_set_id": statement_set.statement_set_id,
        "statement_schema_version": statement_set.statement_schema_version,
        "case_id": statement_set.case_id,
        "track": statement_set.track.value,
        "source_package_ref": _oracle_ref(statement_set.source_package_ref),
        "decision_trace_ref": _oracle_decision_trace_ref(statement_set.decision_trace_ref),
        "statements": tuple(_oracle_statement(statement) for statement in statement_set.statements),
        "generated_at": statement_set.generated_at,
        "publication_state": statement_set.publication_state,
        "issue_ids": tuple(statement_set.issue_ids),
    })


def _oracle_resign_projection_graph(
    trace,
    statement_set,
    *,
    statement_text=None,
    publication_state=None,
    output_precision_binding=None,
):
    statement = statement_set.statements[0]
    statement_ref_replacement = None
    if output_precision_binding is not None:
        statement_set = replace(
            statement_set,
            decision_trace_ref=replace(
                statement_set.decision_trace_ref,
                output_precision_binding=output_precision_binding,
            ),
        )
        statement = replace(statement, output_precision_binding=output_precision_binding)
    if statement_text is not None or output_precision_binding is not None:
        statement = _oracle_sign_statement(replace(
            statement,
            statement_text=(statement.statement_text if statement_text is None else statement_text),
        ))
        identity_digest = bounded_jcs_sha256({
            "case_id": statement_set.case_id,
            "decision_result_ref": _oracle_ref(statement_set.decision_trace_ref.result_ref),
            "statement_revision_ids": (statement.statement_revision_id,),
        })
        statement_set_id = f"STATEMENT-SET-{identity_digest.value[:20]}"
        statement = _oracle_sign_statement(replace(statement, statement_set_id=statement_set_id))
        old_statement_ref = next(
            node.object_ref for node in trace.nodes
            if node.object_ref.object_type == "STATEMENT"
        )
        statement_ref_replacement = VersionedObjectRef(
            "STATEMENT",
            statement.statement_id,
            statement.statement_revision_id,
            statement.statement_schema_version,
            "pi-230-v1",
            DigestPresent("PRESENT", statement.content_digest),
            None,
            trace.created_at,
        )
    else:
        statement_set_id = statement_set.statement_set_id
    changed_set = replace(
        statement_set,
        statement_set_id=statement_set_id,
        statements=(statement,),
        publication_state=(
            statement_set.publication_state if publication_state is None else publication_state
        ),
    )
    changed_set = replace(
        changed_set,
        content_digest=_oracle_statement_set_content_digest(changed_set),
    )
    changed_set_ref = VersionedObjectRef(
        "STATEMENT_SET",
        changed_set.statement_set_id,
        f"rev-{changed_set.content_digest.value[:16]}",
        changed_set.statement_schema_version,
        "pi-230-v1",
        DigestPresent("PRESENT", changed_set.content_digest),
        None,
        trace.created_at,
    )
    replacements = {trace.statement_set_ref: changed_set_ref}
    if statement_ref_replacement is not None:
        replacements[old_statement_ref] = statement_ref_replacement
    changed_trace = replace(
        trace,
        statement_set_ref=changed_set_ref,
        nodes=tuple(
            replace(node, object_ref=replacements.get(node.object_ref, node.object_ref))
            for node in trace.nodes
        ),
        edges=tuple(
            replace(
                edge,
                from_ref=replacements.get(edge.from_ref, edge.from_ref),
                to_ref=replacements.get(edge.to_ref, edge.to_ref),
            )
            for edge in trace.edges
        ),
    )
    return changed_trace, changed_set


def _oracle_projection_roots(statement_set, normative_contract_ref, machine_appendix_ref):
    schemas = {
        "REPORT": "f09.report-projection.v1",
        "STATEMENT_RECORDS": "f09.statement-records-projection.v1",
        "STATEMENT_INDEX": "f09.statement-index-projection.v1",
    }
    statements = statement_set.statements
    payloads = {
        "REPORT": {
            "generated_at": statement_set.generated_at,
            "publication_state": statement_set.publication_state,
            "statement_count": str(len(statements)),
            "sections": tuple({
                "statement_id": statement.statement_id,
                "statement_revision_id": statement.statement_revision_id,
                "domain": statement.domain,
                "semantic_scope": statement.semantic_scope,
                "display_section": statement.display_section,
                "statement_text": statement.statement_text,
                "feedback_policy": statement.feedback_policy,
                "integrity": statement.integrity,
                "issue_ids": tuple(statement.issue_ids),
                "content_digest": _oracle_digest(statement.content_digest),
            } for statement in statements),
        },
        "STATEMENT_RECORDS": {
            "generated_at": statement_set.generated_at,
            "publication_state": statement_set.publication_state,
            "statements": tuple(_oracle_statement(statement) for statement in statements),
        },
        "STATEMENT_INDEX": {
            "generated_at": statement_set.generated_at,
            "publication_state": statement_set.publication_state,
            "entries": tuple({
                "ordinal": str(ordinal),
                "statement_id": statement.statement_id,
                "statement_revision_id": statement.statement_revision_id,
                "statement_schema_version": statement.statement_schema_version,
                "domain": statement.domain,
                "semantic_scope": statement.semantic_scope,
                "display_section": statement.display_section,
                "feedback_policy": statement.feedback_policy,
                "integrity": statement.integrity,
                "content_digest": _oracle_digest(statement.content_digest),
            } for ordinal, statement in enumerate(statements, 1)),
        },
    }
    return {
        role: {
            "artifact_role": role,
            "schema_version": schemas[role],
            "contract_version": "f09.artifact-projection.v1",
            "case_id": statement_set.case_id,
            "track": statement_set.track.value,
            "statement_set_id": statement_set.statement_set_id,
            "statement_set_schema_version": statement_set.statement_schema_version,
            "statement_set_content_digest": _oracle_digest(statement_set.content_digest),
            "source_package_ref": _oracle_ref(statement_set.source_package_ref),
            "normative_contract_ref": _oracle_ref(normative_contract_ref),
            "machine_appendix_ref": _oracle_ref(machine_appendix_ref),
            "payload": payloads[role],
        }
        for role in ROLES
    }


def _ref(identity: str = "current") -> VersionedObjectRef:
    digest = _digest(identity.encode(), KEY_CANONICALIZATION)
    return VersionedObjectRef(
        object_type="NORMALIZED_EVIDENCE_PACKAGE",
        object_id=f"PACKAGE:{identity}",
        revision_id=f"REVISION:{identity}",
        schema_version=f"source-schema:{identity}",
        contract_version=f"contract:{identity}",
        digest_binding=DigestPresent("PRESENT", digest),
        source_locator_id=f"SOURCE:{identity}",
        captured_at=NOW,
    )


def _statement_set(identity: str = "current") -> StatementSet:
    source_ref = _ref(identity)
    absent = AbsentDeclarationBinding("ABSENT", "DECLARATION_NOT_PRESENT")
    decision_ref = VersionedObjectRef(
        object_type="DECISION_RESULT",
        object_id=f"DECISION:{identity}",
        revision_id=f"DECISION-REVISION:{identity}",
        schema_version=f"schema:{identity}",
        contract_version=f"contract:{identity}",
        digest_binding=DigestPresent(
            "PRESENT", _digest(f"decision:{identity}".encode(), KEY_CANONICALIZATION)
        ),
        source_locator_id=None,
        captured_at=NOW,
    )
    return StatementSet(
        statement_set_id=f"STATEMENT-SET:{identity}",
        statement_schema_version=f"schema:{identity}",
        case_id="CASE:F09:ARTIFACTS",
        track=RunTrack.PRODUCTION_DEFAULT,
        source_package_ref=source_ref,
        decision_trace_ref=DecisionTraceRef(
            result_ref=decision_ref,
            action_id=f"ACTION:{identity}",
            selected_action=DecisionAction.OUTPUT,
            basis_record_ids=(f"BASIS:{identity}",),
            blocking_issue_ids=(),
            nonblocking_issue_ids=(),
            source_decision_refs=(decision_ref.object_id,),
            output_precision_binding=absent,
            validation_plan_binding=absent,
            structural_validity="VALID",
        ),
        statements=(),
        content_digest=_digest(f"statement-set:{identity}".encode(), KEY_CANONICALIZATION),
        generated_at=NOW,
        publication_state="PUBLISHABLE",
        issue_ids=(),
    )


def _key(identity: str = "current", *, statement_set_id: str | None = None):
    return artifacts.IdempotencyKey(
        operation="RENDER_REPORT",
        case_id="CASE:F09:ARTIFACTS",
        track=RunTrack.PRODUCTION_DEFAULT,
        source_digest=_digest(f"source:{identity}".encode(), KEY_CANONICALIZATION),
        schema_versions_digest=_digest(f"schema:{identity}".encode(), KEY_CANONICALIZATION),
        contract_digest=_digest(f"contract:{identity}".encode(), KEY_CANONICALIZATION),
        statement_set_id=statement_set_id or f"STATEMENT-SET:{identity}",
        feedback_id=None,
        canonical_key_digest=_digest(f"key:{identity}".encode(), KEY_CANONICALIZATION),
    )


def _projections(suffix: bytes = b"") -> dict[str, bytes]:
    return {
        "REPORT": b"report" + suffix,
        "STATEMENT_RECORDS": b"records" + suffix,
        "STATEMENT_INDEX": b"index" + suffix,
    }


def _write(tmp_path: Path, identity: str = "current", *, fail_after: str | None = None):
    statement_set = _statement_set(identity)
    key = _key(identity, statement_set_id=statement_set.statement_set_id)
    manifest = artifacts.write_artifact_set(
        tmp_path,
        statement_set,
        _projections(),
        key=key,
        attempt_id=f"ATTEMPT:{identity}",
        now=NOW,
        fail_after=fail_after,
    )
    return statement_set, key, manifest


def _issue_pair(manifest) -> tuple[tuple[str, str], ...]:
    assert all(isinstance(issue, DetectedIssue) for issue in manifest.detected_issues)
    return tuple((issue.issue_code, issue.field_path) for issue in manifest.detected_issues)


def _unsafe_digest(*, algorithm="sha256", canonicalization=KEY_CANONICALIZATION, value="0" * 64):
    digest = object.__new__(DigestRef)
    object.__setattr__(digest, "algorithm", algorithm)
    object.__setattr__(digest, "canonicalization", canonicalization)
    object.__setattr__(digest, "value", value)
    return digest


def _retry(tmp_path: Path, manifest, projections, statement_set, key, *, attempt_id="RETRY"):
    return artifacts.retry_artifact_set(
        tmp_path,
        manifest,
        projections,
        key=key,
        current_frozen_input_refs=(statement_set.source_package_ref,),
        current_schema_version=statement_set.statement_schema_version,
        current_statement_set_id=statement_set.statement_set_id,
        current_contract_digest=key.contract_digest,
        attempt_id=attempt_id,
        now=NOW,
    )


def test_public_dataclass_shapes_are_frozen_and_exact():
    expected = {
        artifacts.ArtifactOperationAuthority: ("projections", "key"),
        artifacts.IdempotencyKey: (
            "operation", "case_id", "track", "source_digest",
            "schema_versions_digest", "contract_digest", "statement_set_id",
            "feedback_id", "canonical_key_digest",
        ),
        artifacts.ArtifactWriteAttempt: (
            "attempt_id", "artifact_id", "idempotency_key", "attempt_number",
            "retry_of_attempt_id", "input_snapshot_refs", "started_at", "finished_at",
            "outcome", "observed_digest", "error_class", "error_message_digest",
        ),
        artifacts.ArtifactRecord: (
            "artifact_id", "artifact_role", "track", "case_id", "statement_set_id",
            "run_id", "path_locator", "schema_version", "expected_digest",
            "observed_digest", "state", "attempts", "issue_ids",
        ),
        artifacts.ArtifactSetManifest: (
            "manifest_id", "key", "records", "state", "digest", "detected_issues",
        ),
    }
    for cls, names in expected.items():
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
        assert tuple(field.name for field in fields(cls)) == names
    hints = {cls: get_type_hints(cls) for cls in expected}
    assert hints[artifacts.ArtifactOperationAuthority]["projections"] == Mapping[str, bytes]
    assert hints[artifacts.ArtifactOperationAuthority]["key"] is artifacts.IdempotencyKey
    assert hints[artifacts.IdempotencyKey]["track"] is RunTrack
    assert hints[artifacts.IdempotencyKey]["source_digest"] is DigestRef
    assert hints[artifacts.ArtifactWriteAttempt]["input_snapshot_refs"] == tuple[VersionedObjectRef, ...]
    assert hints[artifacts.ArtifactRecord]["state"] is ArtifactItemState
    assert hints[artifacts.ArtifactSetManifest]["state"] is ArtifactSetState
    assert hints[artifacts.ArtifactSetManifest]["detected_issues"] == tuple[DetectedIssue, ...]
    assert set(get_args(hints[artifacts.ArtifactWriteAttempt]["outcome"])) == {
        "SUCCEEDED", "FAILED", "UNKNOWN"
    }
    assert set(get_args(hints[artifacts.ArtifactRecord]["artifact_role"])) == {
        "REPORT", "STATEMENT_INDEX", "STATEMENT_RECORDS", "RUN_SNAPSHOT",
        "DECISION_RUN", "FEEDBACK_ATTACHMENT", "MANIFEST", "FEEDBACK_SOURCE",
    }
    assert set(get_args(hints[artifacts.IdempotencyKey]["operation"])) == {
        "NORMALIZE", "DECIDE", "BUILD_STATEMENT_SET", "RENDER_REPORT",
        "PROJECT_INDEX", "PROJECT_RECORDS", "PROJECT_ARTIFACT_SET",
        "BIND_FEEDBACK", "EVALUATE_LEARNING_ELIGIBILITY", "INGEST_FEEDBACK",
    }
    assert ArtifactItemState.__module__ == "engine.f09.contracts"
    assert ArtifactSetState.__module__ == "engine.f09.contracts"
    assert RunTrack.__module__ == "engine.f09.contracts"
    assert DigestRef.__module__ == "engine.f09.contracts"
    assert DetectedIssue.__module__ == "engine.f09.contracts"
    assert VersionedObjectRef.__module__ == "engine.f09.trace"
    key = _key()
    with pytest.raises(FrozenInstanceError):
        key.case_id = "MUTATED"


def test_artifact_operation_authority_builder_has_the_frozen_public_signature():
    signature = inspect.signature(artifacts.build_artifact_operation_authority)
    assert tuple(signature.parameters) == (
        "package",
        "decision",
        "trace",
        "statement_set",
        "normative_contract_ref",
        "machine_appendix_ref",
    )
    assert signature.parameters["normative_contract_ref"].kind is inspect.Parameter.KEYWORD_ONLY
    assert signature.parameters["machine_appendix_ref"].kind is inspect.Parameter.KEYWORD_ONLY
    assert get_type_hints(artifacts.build_artifact_operation_authority)["return"] is artifacts.ArtifactOperationAuthority


def test_artifact_authority_rejects_nonexact_package_before_validation(monkeypatch):
    sentinel = object()
    calls = []

    def validator(*args, **kwargs):
        calls.append((args, kwargs))
        return sentinel

    monkeypatch.setattr(artifacts, "validate_statement_projection", validator)
    with pytest.raises(F09ContractError) as caught:
        artifacts.build_artifact_operation_authority(
            {},
            object(),
            object(),
            object(),
            normative_contract_ref=object(),
            machine_appendix_ref=object(),
        )
    assert caught.value.issue_code == "ARTIFACT.AUTHORITY_INVALID"
    assert caught.value.field_path == "/artifact_authority/package"
    assert not calls


def test_artifact_authority_wraps_nonexact_validator_return_after_exact_guards(monkeypatch):
    from engine.f09.decision import DecisionEvaluationResult
    from engine.f09.evidence import NormalizedEvidencePackage
    from engine.f09.trace import TraceEnvelope

    package = object.__new__(NormalizedEvidencePackage)
    decision = object.__new__(DecisionEvaluationResult)
    trace = object.__new__(TraceEnvelope)
    statement_set = object.__new__(StatementSet)
    normative_contract_ref = object.__new__(VersionedObjectRef)
    machine_appendix_ref = object.__new__(VersionedObjectRef)
    calls = []

    def validator(*args, **kwargs):
        calls.append((args, kwargs))
        return None

    monkeypatch.setattr(artifacts, "validate_statement_projection", validator)
    with pytest.raises(F09IntegrityError) as caught:
        artifacts.build_artifact_operation_authority(
            package,
            decision,
            trace,
            statement_set,
            normative_contract_ref=normative_contract_ref,
            machine_appendix_ref=machine_appendix_ref,
        )
    assert caught.value.issue_code == "ARTIFACT.PROJECTION_VALIDATION_FAILED"
    assert caught.value.field_path == "/artifact_authority/projection_validation"
    assert caught.value.diagnostic == "statement projection validation did not return strict success"
    assert calls == [
        (
            (statement_set, trace, decision, package),
            {
                "normative_contract_ref": normative_contract_ref,
                "machine_appendix_ref": machine_appendix_ref,
            },
        )
    ]


def test_artifact_authority_propagates_validator_exception_identity(monkeypatch):
    from engine.f09.decision import DecisionEvaluationResult
    from engine.f09.evidence import NormalizedEvidencePackage
    from engine.f09.trace import TraceEnvelope

    package = object.__new__(NormalizedEvidencePackage)
    decision = object.__new__(DecisionEvaluationResult)
    trace = object.__new__(TraceEnvelope)
    statement_set = object.__new__(StatementSet)
    normative_contract_ref = object.__new__(VersionedObjectRef)
    machine_appendix_ref = object.__new__(VersionedObjectRef)
    sentinel = RuntimeError("validator failure")

    def validator(*args, **kwargs):
        raise sentinel

    monkeypatch.setattr(artifacts, "validate_statement_projection", validator)
    with pytest.raises(RuntimeError) as caught:
        artifacts.build_artifact_operation_authority(
            package,
            decision,
            trace,
            statement_set,
            normative_contract_ref=normative_contract_ref,
            machine_appendix_ref=machine_appendix_ref,
        )
    assert caught.value is sentinel


def test_artifact_authority_propagates_f09_error_identity(monkeypatch):
    from engine.f09.decision import DecisionEvaluationResult
    from engine.f09.evidence import NormalizedEvidencePackage
    from engine.f09.trace import ProjectionValidationResult, TraceEnvelope

    package = object.__new__(NormalizedEvidencePackage)
    decision = object.__new__(DecisionEvaluationResult)
    trace = object.__new__(TraceEnvelope)
    statement_set = object.__new__(StatementSet)
    normative_contract_ref = object.__new__(VersionedObjectRef)
    machine_appendix_ref = object.__new__(VersionedObjectRef)
    sentinel = F09ContractError("TRACE.TEST", "/trace/test", "validator failure")

    def validator(*args, **kwargs):
        raise sentinel

    monkeypatch.setattr(artifacts, "validate_statement_projection", validator)
    with pytest.raises(F09Error) as caught:
        artifacts.build_artifact_operation_authority(
            package,
            decision,
            trace,
            statement_set,
            normative_contract_ref=normative_contract_ref,
            machine_appendix_ref=machine_appendix_ref,
        )
    assert caught.value is sentinel


def test_digest_binding_material_rejects_missing_present_digest_with_caller_path():
    malformed = object.__new__(DigestPresent)
    with pytest.raises(F09ContractError) as caught:
        artifacts._digest_binding_material(
            malformed,
            field_path="/artifact_authority/projection_material",
        )
    assert caught.value.issue_code == "ARTIFACT.AUTHORITY_INVALID"
    assert caught.value.field_path == "/artifact_authority/projection_material"
    assert caught.value.diagnostic == "artifact authority projection material is not serialization-closed"


def test_digest_binding_material_rejects_unknown_variant_with_caller_path():
    with pytest.raises(F09ContractError) as caught:
        artifacts._digest_binding_material(
            object(),
            field_path="/artifact_authority/projection_material",
        )
    assert caught.value.issue_code == "ARTIFACT.AUTHORITY_INVALID"
    assert caught.value.field_path == "/artifact_authority/projection_material"
    assert caught.value.diagnostic == "artifact authority projection material is not serialization-closed"


def test_artifact_role_material_rejects_unknown_role_with_caller_path():
    with pytest.raises(F09ContractError) as caught:
        artifacts._artifact_role_material(
            "RUN_SNAPSHOT",
            field_path="/artifact_authority/projection_material",
        )
    assert caught.value.issue_code == "ARTIFACT.AUTHORITY_INVALID"
    assert caught.value.field_path == "/artifact_authority/projection_material"
    assert caught.value.diagnostic == "artifact authority projection material is not serialization-closed"


def test_artifact_authority_projection_bytes_digests_and_key_match_independent_oracle(decision_case):
    package, decision, trace, statement_set, normative_contract_ref, machine_appendix_ref = (
        _canonical_artifact_graph(decision_case)
    )
    authority = artifacts.build_artifact_operation_authority(
        package,
        decision,
        trace,
        statement_set,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
    )
    expected_roots = _oracle_projection_roots(
        statement_set,
        normative_contract_ref,
        machine_appendix_ref,
    )
    expected_projections = {
        role: canonicalize_bounded_jcs(expected_roots[role])
        for role in ROLES
    }
    expected_projection_digests = {
        role: DigestRef("sha256", "RAW-UTF8", sha256(expected_projections[role]).hexdigest())
        for role in ROLES
    }
    expected_source_digest = bounded_jcs_sha256({
        "operation": "PROJECT_ARTIFACT_SET",
        "case_id": statement_set.case_id,
        "track": statement_set.track.value,
        "statement_set_id": statement_set.statement_set_id,
        "statement_set_content_digest": _oracle_digest(statement_set.content_digest),
        "projection_digests": tuple({
            "artifact_role": role,
            "digest": _oracle_digest(expected_projection_digests[role]),
        } for role in ROLES),
    })
    schemas = {
        "REPORT": "f09.report-projection.v1",
        "STATEMENT_RECORDS": "f09.statement-records-projection.v1",
        "STATEMENT_INDEX": "f09.statement-index-projection.v1",
    }
    expected_schema_digest = bounded_jcs_sha256({
        "authority_schema_version": "f09.artifact-operation-authority.v1",
        "projection_contract_version": "f09.artifact-projection.v1",
        "projection_schemas": tuple({
            "artifact_role": role,
            "schema_version": schemas[role],
            "statement_schema_version": statement_set.statement_schema_version,
            "trace_schema_version": trace.trace_schema_version,
        } for role in ROLES),
    })
    expected_contract_digest = bounded_jcs_sha256({
        "normative_contract_ref": _oracle_ref(normative_contract_ref),
        "machine_appendix_ref": _oracle_ref(machine_appendix_ref),
        "decision_contract_ref": {
            "normative_contract_path": decision.contract_ref.normative_contract_path,
            "machine_appendix_path": decision.contract_ref.machine_appendix_path,
            "contract_version": decision.contract_ref.contract_version,
            "content_digest": decision.contract_ref.content_digest,
        },
    })
    expected_key_material = {
        "operation": "PROJECT_ARTIFACT_SET",
        "case_id": statement_set.case_id,
        "track": statement_set.track.value,
        "source_digest": _oracle_digest(expected_source_digest),
        "schema_versions_digest": _oracle_digest(expected_schema_digest),
        "contract_digest": _oracle_digest(expected_contract_digest),
        "statement_set_id": statement_set.statement_set_id,
        "feedback_id": None,
    }
    expected_key = artifacts.IdempotencyKey(
        "PROJECT_ARTIFACT_SET",
        statement_set.case_id,
        statement_set.track,
        expected_source_digest,
        expected_schema_digest,
        expected_contract_digest,
        statement_set.statement_set_id,
        None,
        DigestRef(
            "sha256",
            KEY_CANONICALIZATION,
            sha256(canonicalize_bounded_jcs(expected_key_material)).hexdigest(),
        ),
    )

    assert dict(authority.projections) == expected_projections
    assert authority.key == expected_key
    records = parse_bounded_jcs(authority.projections["STATEMENT_RECORDS"])
    assert records["payload"]["statements"][0]["card_identity_refs"][0] == _oracle_card(
        statement_set.statements[0].card_identity_refs[0]
    )


def test_artifact_authority_generated_at_provenance_and_all_digest_dependencies_are_sensitive(
    decision_case,
):
    from engine.f09.trace import build_statement_set, build_trace

    package, decision, trace, statement_set, normative_contract_ref, machine_appendix_ref = (
        _canonical_artifact_graph(decision_case)
    )
    changed_trace = build_trace(
        package,
        decision,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
        created_at="2026-07-20T00:00:00Z",
    )
    changed_statement_set = build_statement_set(
        changed_trace,
        decision,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
        generated_at="2026-07-20T00:00:00Z",
    )

    def expected_authority_material(current_statement_set):
        roots = _oracle_projection_roots(
            current_statement_set,
            normative_contract_ref,
            machine_appendix_ref,
        )
        projections = {
            role: canonicalize_bounded_jcs(roots[role])
            for role in ROLES
        }
        projection_digests = {
            role: DigestRef(
                "sha256",
                RAW_CANONICALIZATION,
                sha256(projections[role]).hexdigest(),
            )
            for role in ROLES
        }
        source_digest = bounded_jcs_sha256({
            "operation": "PROJECT_ARTIFACT_SET",
            "case_id": current_statement_set.case_id,
            "track": current_statement_set.track.value,
            "statement_set_id": current_statement_set.statement_set_id,
            "statement_set_content_digest": _oracle_digest(current_statement_set.content_digest),
            "projection_digests": tuple({
                "artifact_role": role,
                "digest": _oracle_digest(projection_digests[role]),
            } for role in ROLES),
        })
        key_material = {
            "operation": "PROJECT_ARTIFACT_SET",
            "case_id": current_statement_set.case_id,
            "track": current_statement_set.track.value,
            "source_digest": _oracle_digest(source_digest),
            "schema_versions_digest": None,
            "contract_digest": None,
            "statement_set_id": current_statement_set.statement_set_id,
            "feedback_id": None,
        }
        return projections, projection_digests, source_digest, key_material

    baseline = artifacts.build_artifact_operation_authority(
        package,
        decision,
        trace,
        statement_set,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
    )
    changed = artifacts.build_artifact_operation_authority(
        package,
        decision,
        changed_trace,
        changed_statement_set,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
    )
    baseline_projections, baseline_raw, baseline_source, baseline_key_material = (
        expected_authority_material(statement_set)
    )
    changed_projections, changed_raw, changed_source, changed_key_material = (
        expected_authority_material(changed_statement_set)
    )

    assert all(
        parse_bounded_jcs(changed.projections[role])["payload"]["generated_at"]
        == changed_statement_set.generated_at
        for role in ROLES
    )
    assert dict(baseline.projections) == baseline_projections
    assert dict(changed.projections) == changed_projections
    assert all(baseline_projections[role] != changed_projections[role] for role in ROLES)
    assert all(baseline_raw[role] != changed_raw[role] for role in ROLES)
    assert baseline.key.source_digest == baseline_source
    assert changed.key.source_digest == changed_source
    assert baseline_source != changed_source

    baseline_key_material["schema_versions_digest"] = _oracle_digest(
        baseline.key.schema_versions_digest
    )
    baseline_key_material["contract_digest"] = _oracle_digest(baseline.key.contract_digest)
    changed_key_material["schema_versions_digest"] = _oracle_digest(
        changed.key.schema_versions_digest
    )
    changed_key_material["contract_digest"] = _oracle_digest(changed.key.contract_digest)
    expected_baseline_key_digest = DigestRef(
        "sha256",
        KEY_CANONICALIZATION,
        sha256(canonicalize_bounded_jcs(baseline_key_material)).hexdigest(),
    )
    expected_changed_key_digest = DigestRef(
        "sha256",
        KEY_CANONICALIZATION,
        sha256(canonicalize_bounded_jcs(changed_key_material)).hexdigest(),
    )
    assert baseline.key.canonical_key_digest == expected_baseline_key_digest
    assert changed.key.canonical_key_digest == expected_changed_key_digest
    assert expected_baseline_key_digest != expected_changed_key_digest


def _oracle_authority_sensitivity(authority, statement_set, normative_contract_ref, machine_appendix_ref):
    roots = _oracle_projection_roots(
        statement_set,
        normative_contract_ref,
        machine_appendix_ref,
    )
    projections = {role: canonicalize_bounded_jcs(roots[role]) for role in ROLES}
    raw_digests = {
        role: DigestRef("sha256", RAW_CANONICALIZATION, sha256(projections[role]).hexdigest())
        for role in ROLES
    }
    source_digest = bounded_jcs_sha256({
        "operation": "PROJECT_ARTIFACT_SET",
        "case_id": statement_set.case_id,
        "track": statement_set.track.value,
        "statement_set_id": statement_set.statement_set_id,
        "statement_set_content_digest": _oracle_digest(statement_set.content_digest),
        "projection_digests": tuple({
            "artifact_role": role,
            "digest": _oracle_digest(raw_digests[role]),
        } for role in ROLES),
    })
    key_digest = DigestRef(
        "sha256",
        KEY_CANONICALIZATION,
        sha256(canonicalize_bounded_jcs({
            "operation": "PROJECT_ARTIFACT_SET",
            "case_id": statement_set.case_id,
            "track": statement_set.track.value,
            "source_digest": _oracle_digest(source_digest),
            "schema_versions_digest": _oracle_digest(authority.key.schema_versions_digest),
            "contract_digest": _oracle_digest(authority.key.contract_digest),
            "statement_set_id": statement_set.statement_set_id,
            "feedback_id": None,
        })).hexdigest(),
    )
    return projections, raw_digests, source_digest, key_digest


def test_artifact_authority_publication_state_provenance_and_digest_dependencies_are_sensitive(
    decision_case,
):
    package, decision, trace, statement_set, normative_contract_ref, machine_appendix_ref = (
        _canonical_artifact_graph(decision_case)
    )
    changed_trace, changed_set = _oracle_resign_projection_graph(
        trace,
        statement_set,
        publication_state="PUBLISHABLE",
    )
    baseline = artifacts.build_artifact_operation_authority(
        package,
        decision,
        trace,
        statement_set,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
    )
    changed = artifacts.build_artifact_operation_authority(
        package,
        decision,
        changed_trace,
        changed_set,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
    )
    baseline_oracle = _oracle_authority_sensitivity(
        baseline, statement_set, normative_contract_ref, machine_appendix_ref
    )
    changed_oracle = _oracle_authority_sensitivity(
        changed, changed_set, normative_contract_ref, machine_appendix_ref
    )

    assert statement_set.publication_state != changed_set.publication_state
    assert all(
        parse_bounded_jcs(changed.projections[role])["payload"]["publication_state"]
        == changed_set.publication_state
        for role in ROLES
    )
    assert dict(baseline.projections) == baseline_oracle[0]
    assert dict(changed.projections) == changed_oracle[0]
    assert all(baseline_oracle[0][role] != changed_oracle[0][role] for role in ROLES)
    assert all(baseline_oracle[1][role] != changed_oracle[1][role] for role in ROLES)
    assert baseline.key.source_digest == baseline_oracle[2]
    assert changed.key.source_digest == changed_oracle[2]
    assert baseline_oracle[2] != changed_oracle[2]
    assert baseline.key.canonical_key_digest == baseline_oracle[3]
    assert changed.key.canonical_key_digest == changed_oracle[3]
    assert baseline_oracle[3] != changed_oracle[3]


def test_artifact_authority_statement_text_and_all_dependent_digests_are_sensitive(decision_case):
    package, decision, trace, statement_set, normative_contract_ref, machine_appendix_ref = (
        _canonical_artifact_graph(decision_case)
    )
    changed_text = statement_set.statements[0].statement_text + " confirmed"
    changed_trace, changed_set = _oracle_resign_projection_graph(
        trace,
        statement_set,
        statement_text=changed_text,
    )
    baseline = artifacts.build_artifact_operation_authority(
        package,
        decision,
        trace,
        statement_set,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
    )
    changed = artifacts.build_artifact_operation_authority(
        package,
        decision,
        changed_trace,
        changed_set,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
    )
    baseline_oracle = _oracle_authority_sensitivity(
        baseline, statement_set, normative_contract_ref, machine_appendix_ref
    )
    changed_oracle = _oracle_authority_sensitivity(
        changed, changed_set, normative_contract_ref, machine_appendix_ref
    )

    assert changed_set.statements[0].statement_text == changed_text
    assert dict(baseline.projections) == baseline_oracle[0]
    assert dict(changed.projections) == changed_oracle[0]
    assert baseline_oracle[0]["REPORT"] != changed_oracle[0]["REPORT"]
    assert baseline_oracle[0]["STATEMENT_RECORDS"] != changed_oracle[0]["STATEMENT_RECORDS"]
    assert baseline_oracle[1]["REPORT"] != changed_oracle[1]["REPORT"]
    assert baseline_oracle[1]["STATEMENT_RECORDS"] != changed_oracle[1]["STATEMENT_RECORDS"]
    assert baseline.key.source_digest == baseline_oracle[2]
    assert changed.key.source_digest == changed_oracle[2]
    assert baseline_oracle[2] != changed_oracle[2]
    assert baseline.key.canonical_key_digest == baseline_oracle[3]
    assert changed.key.canonical_key_digest == changed_oracle[3]
    assert baseline_oracle[3] != changed_oracle[3]


@pytest.mark.parametrize("declaration_variant", ["RESOLVED", "UNRESOLVABLE"])
def test_artifact_authority_nested_declaration_identity_changes_records_and_key_oracles(
    decision_case,
    monkeypatch,
    declaration_variant,
):
    package, decision, trace, statement_set, normative_contract_ref, machine_appendix_ref = (
        _canonical_artifact_graph(decision_case)
    )
    original = statement_set.statements[0].output_precision_binding
    if declaration_variant == "RESOLVED":
        baseline_binding = original
        changed_binding = replace(original, ref=replace(
            original.ref,
            declaration_id=original.ref.declaration_id + "-changed",
        ))
    else:
        baseline_binding = UnresolvableDeclarationBinding(
            "UNRESOLVABLE",
            original.ref,
            "BROKEN_REFERENCE",
            ("DECLARATION-UNRESOLVABLE",),
        )
        changed_binding = replace(
            baseline_binding,
            attempted_ref=replace(
                baseline_binding.attempted_ref,
                declaration_id=baseline_binding.attempted_ref.declaration_id + "-changed",
            ),
        )
    baseline_trace, baseline_set = _oracle_resign_projection_graph(
        trace,
        statement_set,
        output_precision_binding=baseline_binding,
    )
    changed_trace, changed_set = _oracle_resign_projection_graph(
        trace,
        statement_set,
        output_precision_binding=changed_binding,
    )
    validator_calls = []

    def strict_success(*args, **kwargs):
        validator_calls.append((args, kwargs))
        return artifacts.ProjectionValidationResult(True, ())

    monkeypatch.setattr(artifacts, "validate_statement_projection", strict_success)
    baseline = artifacts.build_artifact_operation_authority(
        package,
        decision,
        baseline_trace,
        baseline_set,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
    )
    changed = artifacts.build_artifact_operation_authority(
        package,
        decision,
        changed_trace,
        changed_set,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
    )
    baseline_oracle = _oracle_authority_sensitivity(
        baseline, baseline_set, normative_contract_ref, machine_appendix_ref
    )
    changed_oracle = _oracle_authority_sensitivity(
        changed, changed_set, normative_contract_ref, machine_appendix_ref
    )

    assert len(validator_calls) == 2
    assert dict(baseline.projections) == baseline_oracle[0]
    assert dict(changed.projections) == changed_oracle[0]
    assert baseline_oracle[0]["STATEMENT_RECORDS"] != changed_oracle[0]["STATEMENT_RECORDS"]
    assert baseline_oracle[1]["STATEMENT_RECORDS"] != changed_oracle[1]["STATEMENT_RECORDS"]
    assert baseline.key.source_digest == baseline_oracle[2]
    assert changed.key.source_digest == changed_oracle[2]
    assert baseline_oracle[2] != changed_oracle[2]
    assert baseline.key.canonical_key_digest == baseline_oracle[3]
    assert changed.key.canonical_key_digest == changed_oracle[3]
    assert baseline_oracle[3] != changed_oracle[3]


def test_artifact_authority_report_schema_literal_changes_schema_digest_and_key_oracles(
    decision_case,
):
    package, decision, trace, statement_set, normative_contract_ref, machine_appendix_ref = (
        _canonical_artifact_graph(decision_case)
    )
    authority = artifacts.build_artifact_operation_authority(
        package,
        decision,
        trace,
        statement_set,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
    )

    def schema_digest(report_schema):
        schemas = {
            "REPORT": report_schema,
            "STATEMENT_RECORDS": "f09.statement-records-projection.v1",
            "STATEMENT_INDEX": "f09.statement-index-projection.v1",
        }
        return bounded_jcs_sha256({
            "authority_schema_version": "f09.artifact-operation-authority.v1",
            "projection_contract_version": "f09.artifact-projection.v1",
            "projection_schemas": tuple({
                "artifact_role": role,
                "schema_version": schemas[role],
                "statement_schema_version": statement_set.statement_schema_version,
                "trace_schema_version": trace.trace_schema_version,
            } for role in ROLES),
        })

    def key_digest(current_schema_digest):
        return DigestRef(
            "sha256",
            KEY_CANONICALIZATION,
            sha256(canonicalize_bounded_jcs({
                "operation": "PROJECT_ARTIFACT_SET",
                "case_id": statement_set.case_id,
                "track": statement_set.track.value,
                "source_digest": _oracle_digest(authority.key.source_digest),
                "schema_versions_digest": _oracle_digest(current_schema_digest),
                "contract_digest": _oracle_digest(authority.key.contract_digest),
                "statement_set_id": statement_set.statement_set_id,
                "feedback_id": None,
            })).hexdigest(),
        )

    baseline_schema_digest = schema_digest("f09.report-projection.v1")
    changed_schema_digest = schema_digest("f09.report-projection.v2-mutant")
    baseline_key_digest = key_digest(baseline_schema_digest)
    changed_key_digest = key_digest(changed_schema_digest)

    assert authority.key.schema_versions_digest == baseline_schema_digest
    assert baseline_schema_digest != changed_schema_digest
    assert authority.key.canonical_key_digest == baseline_key_digest
    assert baseline_key_digest != changed_key_digest


def test_artifact_authority_contract_content_changes_contract_digest_and_key_oracles(
    decision_case,
):
    changed_case = dict(decision_case)
    original_contract_digest = decision_case["contract_ref"].content_digest
    changed_case["contract_ref"] = replace(
        decision_case["contract_ref"],
        content_digest=("0" if original_contract_digest[0] != "0" else "1")
        + original_contract_digest[1:],
    )
    baseline_graph = _canonical_artifact_graph(decision_case)
    changed_graph = _canonical_artifact_graph(changed_case)

    def build_and_oracle(graph):
        package, decision, trace, statement_set, normative_contract_ref, machine_appendix_ref = graph
        authority = artifacts.build_artifact_operation_authority(
            package,
            decision,
            trace,
            statement_set,
            normative_contract_ref=normative_contract_ref,
            machine_appendix_ref=machine_appendix_ref,
        )
        contract_digest = bounded_jcs_sha256({
            "normative_contract_ref": _oracle_ref(normative_contract_ref),
            "machine_appendix_ref": _oracle_ref(machine_appendix_ref),
            "decision_contract_ref": {
                "normative_contract_path": decision.contract_ref.normative_contract_path,
                "machine_appendix_path": decision.contract_ref.machine_appendix_path,
                "contract_version": decision.contract_ref.contract_version,
                "content_digest": decision.contract_ref.content_digest,
            },
        })
        key_digest = DigestRef(
            "sha256",
            KEY_CANONICALIZATION,
            sha256(canonicalize_bounded_jcs({
                "operation": "PROJECT_ARTIFACT_SET",
                "case_id": statement_set.case_id,
                "track": statement_set.track.value,
                "source_digest": _oracle_digest(authority.key.source_digest),
                "schema_versions_digest": _oracle_digest(authority.key.schema_versions_digest),
                "contract_digest": _oracle_digest(contract_digest),
                "statement_set_id": statement_set.statement_set_id,
                "feedback_id": None,
            })).hexdigest(),
        )
        return authority, contract_digest, key_digest

    baseline, baseline_contract, baseline_key = build_and_oracle(baseline_graph)
    changed, changed_contract, changed_key = build_and_oracle(changed_graph)

    assert baseline.key.contract_digest == baseline_contract
    assert changed.key.contract_digest == changed_contract
    assert baseline_contract != changed_contract
    assert baseline.key.canonical_key_digest == baseline_key
    assert changed.key.canonical_key_digest == changed_key
    assert baseline_key != changed_key


def test_artifact_authority_projection_roles_roots_payloads_and_public_surface_are_exact(decision_case):
    package, decision, trace, statement_set, normative_contract_ref, machine_appendix_ref = (
        _canonical_artifact_graph(decision_case)
    )
    authority = artifacts.build_artifact_operation_authority(
        package,
        decision,
        trace,
        statement_set,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
    )

    expected_root_keys = {
        "artifact_role",
        "schema_version",
        "contract_version",
        "case_id",
        "track",
        "statement_set_id",
        "statement_set_schema_version",
        "statement_set_content_digest",
        "source_package_ref",
        "normative_contract_ref",
        "machine_appendix_ref",
        "payload",
    }
    expected_payload_keys = {
        "REPORT": {"generated_at", "publication_state", "statement_count", "sections"},
        "STATEMENT_RECORDS": {"generated_at", "publication_state", "statements"},
        "STATEMENT_INDEX": {"generated_at", "publication_state", "entries"},
    }

    assert tuple(authority.projections) == ROLES
    for role in ROLES:
        root = parse_bounded_jcs(authority.projections[role])
        assert type(root) is dict
        assert set(root) == expected_root_keys
        assert root["artifact_role"] == role
        assert type(root["payload"]) is dict
        assert set(root["payload"]) == expected_payload_keys[role]

    module = ast.parse(Path(inspect.getsourcefile(artifacts)).read_text(encoding="utf-8"))
    public_functions = {
        node.name
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }
    assert public_functions == {
        "resolve_artifact_operation_root",
        "canonicalize_artifact_records",
        "digest_artifact_records",
        "write_artifact_set",
        "inspect_artifact_set",
        "retry_artifact_set",
        "coordinate_artifact_operation",
        "build_artifact_operation_authority",
        "coordinate_run_artifact_set_v1",
        "coordinate_run_artifact_set_with_target_refs_v1",
        "get_run_artifact_set_public_key_registry_v1",
        "canonicalize_run_artifact_set_issuance_payload_v1",
        "validate_run_artifact_set_result_issuance_v1",
        "provision_verified_run_manifest_fixture_v1",
        "inspect_run_artifact_set_v1",
        "validate_run_artifact_manifest_v1",
        "reconcile_run_artifact_set_v1",
    }


def test_artifact_authority_invalid_contract_ref_stops_after_contract_read_prefix(
    decision_case,
    monkeypatch,
):
    package, decision, trace, statement_set, normative_contract_ref, machine_appendix_ref = (
        _canonical_artifact_graph(decision_case)
    )
    changed_contract_ref = replace(
        normative_contract_ref,
        object_id=normative_contract_ref.object_id + "-drift",
    )
    reads = []
    real_read_bytes = Path.read_bytes

    def observed_read_bytes(path):
        reads.append(path.as_posix())
        return real_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", observed_read_bytes)
    with pytest.raises(F09IntegrityError) as caught:
        artifacts.build_artifact_operation_authority(
            package,
            decision,
            trace,
            statement_set,
            normative_contract_ref=changed_contract_ref,
            machine_appendix_ref=machine_appendix_ref,
        )

    assert caught.value.issue_code == "ARTIFACT.PROJECTION_VALIDATION_FAILED"
    assert caught.value.field_path == "/artifact_authority/projection_validation"
    assert len(reads) == 1
    assert reads[0].endswith("engine/contracts/12-real-world-function-evidence-cards-v1.md")


@pytest.mark.parametrize("failure_phase", ["G1", "V4", "P1-CARD"])
def test_artifact_authority_precanonical_failures_neither_canonicalize_nor_write(
    decision_case,
    monkeypatch,
    failure_phase,
):
    package, decision, trace, statement_set, normative_contract_ref, machine_appendix_ref = (
        _canonical_artifact_graph(decision_case)
    )
    if failure_phase == "G1":
        package = {}
    elif failure_phase == "V4":
        monkeypatch.setattr(
            artifacts,
            "validate_statement_projection",
            lambda *args, **kwargs: artifacts.ProjectionValidationResult(False, ()),
        )
    else:
        monkeypatch.setattr(
            artifacts,
            "validate_statement_projection",
            lambda *args, **kwargs: artifacts.ProjectionValidationResult(True, ()),
        )
        statement_set = replace(
            statement_set,
            statements=(replace(statement_set.statements[0], card_identity_refs=()),),
        )
    effects = {"canonicalize": 0, "write": 0}

    def forbidden_canonicalize(value):
        effects["canonicalize"] += 1
        raise AssertionError("canonicalization must not run before strict success")

    def forbidden_write(*args, **kwargs):
        effects["write"] += 1
        raise AssertionError("write must not run in authority construction")

    monkeypatch.setattr(artifacts, "canonicalize_bounded_jcs", forbidden_canonicalize)
    monkeypatch.setattr(artifacts, "write_artifact_set", forbidden_write)
    with pytest.raises((F09ContractError, F09IntegrityError)):
        artifacts.build_artifact_operation_authority(
            package,
            decision,
            trace,
            statement_set,
            normative_contract_ref=normative_contract_ref,
            machine_appendix_ref=machine_appendix_ref,
        )

    assert effects == {"canonicalize": 0, "write": 0}


def test_artifact_authority_focused_fixture_uses_only_public_producer_chain():
    fixture = ast.parse(inspect.getsource(_canonical_artifact_graph))
    calls = {
        node.func.id
        for node in ast.walk(fixture)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    private_calls = {
        node.func.attr
        for node in ast.walk(fixture)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr.startswith("_")
    }

    assert {
        "build_f09_evidence_package",
        "evaluate_f09",
        "build_trace",
        "build_statement_set",
    }.issubset(calls)
    assert private_calls == set()


def test_artifact_authority_builds_immutable_three_projection_authority(decision_case):
    package, decision, trace, statement_set, normative_contract_ref, machine_appendix_ref = (
        _canonical_artifact_graph(decision_case)
    )

    authority = artifacts.build_artifact_operation_authority(
        package,
        decision,
        trace,
        statement_set,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
    )

    assert type(authority) is artifacts.ArtifactOperationAuthority
    assert type(authority.projections).__name__ == "mappingproxy"
    assert tuple(authority.projections) == ROLES
    assert all(type(projection) is bytes for projection in authority.projections.values())
    assert authority.key.operation == "PROJECT_ARTIFACT_SET"
    with pytest.raises(TypeError):
        authority.projections["REPORT"] = b"mutated"


def test_artifact_authority_success_has_frozen_call_and_validator_read_accounting(
    decision_case,
    monkeypatch,
):
    import engine.f09.canonical_json as canonical_json
    import engine.f09.trace as trace_module

    package, decision, trace, statement_set, normative_contract_ref, machine_appendix_ref = (
        _canonical_artifact_graph(decision_case)
    )
    counts = {"validator": 0, "bounded": 0, "direct": 0, "transitive": 0}
    reads = []
    real_validator = artifacts.validate_statement_projection
    real_artifact_bounded = artifacts.bounded_jcs_sha256
    real_trace_bounded = trace_module.bounded_jcs_sha256
    real_direct = artifacts.canonicalize_bounded_jcs
    real_transitive = canonical_json.canonicalize_bounded_jcs
    real_read_bytes = Path.read_bytes

    def observed_validator(*args, **kwargs):
        counts["validator"] += 1
        return real_validator(*args, **kwargs)

    def observed_artifact_bounded(value):
        counts["bounded"] += 1
        return real_artifact_bounded(value)

    def observed_trace_bounded(value):
        counts["bounded"] += 1
        return real_trace_bounded(value)

    def observed_direct(value):
        counts["direct"] += 1
        return real_direct(value)

    def observed_transitive(value):
        counts["transitive"] += 1
        return real_transitive(value)

    def observed_read_bytes(path):
        reads.append(path.as_posix())
        return real_read_bytes(path)

    monkeypatch.setattr(artifacts, "validate_statement_projection", observed_validator)
    monkeypatch.setattr(artifacts, "bounded_jcs_sha256", observed_artifact_bounded)
    monkeypatch.setattr(trace_module, "bounded_jcs_sha256", observed_trace_bounded)
    monkeypatch.setattr(artifacts, "canonicalize_bounded_jcs", observed_direct)
    monkeypatch.setattr(canonical_json, "canonicalize_bounded_jcs", observed_transitive)
    monkeypatch.setattr(Path, "read_bytes", observed_read_bytes)

    authority = artifacts.build_artifact_operation_authority(
        package,
        decision,
        trace,
        statement_set,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
    )

    assert type(authority) is artifacts.ArtifactOperationAuthority
    assert counts == {"validator": 1, "bounded": 10, "direct": 4, "transitive": 10}
    assert len(reads) == 2
    assert reads[0].endswith("engine/contracts/12-real-world-function-evidence-cards-v1.md")
    assert reads[1].endswith("mapping/real-world-function-evidence-cards-v1.yaml")


def test_artifact_authority_c2_rejects_independent_digest_disagreement(decision_case, monkeypatch):
    package, decision, trace, statement_set, normative_contract_ref, machine_appendix_ref = (
        _canonical_artifact_graph(decision_case)
    )
    monkeypatch.setattr(artifacts, "_independent_sha256", lambda payload: "0" * 64)

    with pytest.raises(F09IntegrityError) as caught:
        artifacts.build_artifact_operation_authority(
            package,
            decision,
            trace,
            statement_set,
            normative_contract_ref=normative_contract_ref,
            machine_appendix_ref=machine_appendix_ref,
        )

    assert caught.value.issue_code == "IDEMPOTENCY.DIGEST_MISMATCH"
    assert caught.value.field_path == "/artifact_authority/key/canonical_key_digest"
    assert caught.value.diagnostic == "artifact authority canonical key digest mismatch"


def test_artifact_authority_owner_ast_has_no_forbidden_authority_or_reflection():
    module = ast.parse(Path(inspect.getsourcefile(artifacts)).read_text(encoding="utf-8"))
    owner_nodes = [
        node for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in _AUTHORITY_OWNER_NAMES
    ]

    assert _authority_owner_ast_violations(module) == {
        "names": set(),
        "members": set(),
        "calls": set(),
    }
    assert _validator_call_count(module) == 1


@pytest.mark.parametrize(
    "mutation",
    ["delete", "duplicate", "retry", "second_validation"],
)
def test_artifact_authority_fixed_call_count_gate_rejects_validator_call_site_mutants(
    mutation,
):
    module = ast.parse(Path(inspect.getsourcefile(artifacts)).read_text(encoding="utf-8"))
    builder = next(
        node for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "build_artifact_operation_authority"
    )
    validator_call = next(
        node for node in ast.walk(builder)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "validate_statement_projection"
    )
    if mutation == "delete":
        validator_call.func.id = "deleted_validator_call"
    elif mutation == "duplicate":
        builder.body.insert(0, ast.Expr(value=validator_call))
    elif mutation == "retry":
        builder.body.insert(0, ast.Try(
            body=[ast.Pass()],
            handlers=[ast.ExceptHandler(type=None, name=None, body=[ast.Expr(value=validator_call)])],
            orelse=[],
            finalbody=[],
        ))
    else:
        builder.body.append(ast.Expr(value=validator_call))

    assert _validator_call_count(module) != 1


@pytest.mark.parametrize(
    ("owner_name", "mutant_statement", "category", "forbidden"),
    [
        ("_artifact_root_material", "Path", "names", "Path"),
        ("build_artifact_operation_authority", "open()", "calls", "open"),
        ("_artifact_payload_material", "authority.read_bytes", "members", "read_bytes"),
        ("_artifact_payload_material", "authority.read_text", "members", "read_text"),
        ("build_artifact_operation_authority", "time", "names", "time"),
        ("build_artifact_operation_authority", "datetime", "names", "datetime"),
        ("build_artifact_operation_authority", "uuid4()", "calls", "uuid4"),
        ("_artifact_root_material", "random", "names", "random"),
        (
            "build_artifact_operation_authority",
            "evaluate_learning_eligibility()",
            "calls",
            "evaluate_learning_eligibility",
        ),
        (
            "build_artifact_operation_authority",
            "validate_learning_eligibility()",
            "calls",
            "validate_learning_eligibility",
        ),
    ],
)
def test_artifact_authority_fixed_ast_gate_rejects_each_single_source_mutant(
    owner_name,
    mutant_statement,
    category,
    forbidden,
):
    module = ast.parse(Path(inspect.getsourcefile(artifacts)).read_text(encoding="utf-8"))
    owner = next(
        node for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == owner_name
    )
    owner.body.insert(0, ast.parse(mutant_statement).body[0])

    violations = _authority_owner_ast_violations(module)

    assert forbidden in violations[category]


def test_artifact_authority_rejects_empty_card_container_after_strict_validation(monkeypatch):
    from engine.f09.decision import DecisionEvaluationResult
    from engine.f09.evidence import NormalizedEvidencePackage
    from engine.f09.trace import ProjectionValidationResult, TraceEnvelope

    package = object.__new__(NormalizedEvidencePackage)
    decision = object.__new__(DecisionEvaluationResult)
    trace = object.__new__(TraceEnvelope)
    statement_set = object.__new__(StatementSet)

    class Statement:
        card_identity_refs = ()

    object.__setattr__(statement_set, "statements", (Statement(),))
    normative_contract_ref = object.__new__(VersionedObjectRef)
    machine_appendix_ref = object.__new__(VersionedObjectRef)
    monkeypatch.setattr(
        artifacts,
        "validate_statement_projection",
        lambda *args, **kwargs: ProjectionValidationResult(True, ()),
    )
    with pytest.raises(F09ContractError) as caught:
        artifacts.build_artifact_operation_authority(
            package,
            decision,
            trace,
            statement_set,
            normative_contract_ref=normative_contract_ref,
            machine_appendix_ref=machine_appendix_ref,
        )
    assert caught.value.issue_code == "ARTIFACT.AUTHORITY_INVALID"
    assert caught.value.field_path == "/artifact_authority/statements/0/card_identity_refs"
    assert caught.value.diagnostic == (
        "artifact authority requires exactly one card identity ref material container per statement"
    )


def test_artifact_authority_rejects_nonexact_card_member_after_strict_validation(monkeypatch):
    from engine.f09.decision import DecisionEvaluationResult
    from engine.f09.evidence import NormalizedEvidencePackage
    from engine.f09.trace import ProjectionValidationResult, TraceEnvelope

    package = object.__new__(NormalizedEvidencePackage)
    decision = object.__new__(DecisionEvaluationResult)
    trace = object.__new__(TraceEnvelope)
    statement_set = object.__new__(StatementSet)

    class Statement:
        card_identity_refs = (object(),)

    object.__setattr__(statement_set, "statements", (Statement(),))
    normative_contract_ref = object.__new__(VersionedObjectRef)
    machine_appendix_ref = object.__new__(VersionedObjectRef)
    monkeypatch.setattr(
        artifacts,
        "validate_statement_projection",
        lambda *args, **kwargs: ProjectionValidationResult(True, ()),
    )
    with pytest.raises(F09ContractError) as caught:
        artifacts.build_artifact_operation_authority(
            package,
            decision,
            trace,
            statement_set,
            normative_contract_ref=normative_contract_ref,
            machine_appendix_ref=machine_appendix_ref,
        )
    assert caught.value.issue_code == "ARTIFACT.AUTHORITY_INVALID"
    assert caught.value.field_path == "/artifact_authority/projection_material"
    assert caught.value.diagnostic == "artifact authority projection material is not serialization-closed"


@pytest.mark.parametrize(
    "port",
    [
        artifacts.write_artifact_set,
        artifacts.inspect_artifact_set,
        artifacts.retry_artifact_set,
        artifacts.coordinate_artifact_operation,
    ],
)
def test_four_lifecycle_ports_are_public_callables_without_readiness_booleans(port):
    assert callable(port)
    names = tuple(inspect.signature(port).parameters)
    assert not any("feedback" in name or "learning" in name or "readiness" in name for name in names)


def test_operation_root_resolver_is_a_public_preflight_port():
    assert callable(artifacts.resolve_artifact_operation_root)
    assert tuple(inspect.signature(artifacts.resolve_artifact_operation_root).parameters) == ("root", "key")


@pytest.mark.parametrize("state", list(ArtifactItemState))
def test_all_eight_item_states_are_accepted_by_inspection(tmp_path, state):
    _, _, manifest = _write(tmp_path)
    record = replace(manifest.records[0], state=state)
    inspected = artifacts.inspect_artifact_set(tmp_path, replace(manifest, records=(record,)))
    assert inspected.records[0].state == state


@pytest.mark.parametrize("state", list(ArtifactSetState))
def test_all_five_set_states_are_closed_canonical_members(state):
    assert isinstance(state, ArtifactSetState)
    assert state.value in {
        "COMPLETE_VERIFIED", "PARTIAL", "STALE_MIXED_REVISION", "DIGEST_MISMATCH", "FAILED"
    }


@pytest.mark.parametrize("illegal_state", ["NOT_STARTED", "WRITTEN"])
def test_noncanonical_item_states_fail_closed(tmp_path, illegal_state):
    _, _, manifest = _write(tmp_path)
    malformed = replace(manifest.records[0], state=illegal_state)
    with pytest.raises(F09ContractError) as caught:
        artifacts.inspect_artifact_set(tmp_path, replace(manifest, records=(malformed,)))
    assert (caught.value.issue_code, caught.value.field_path) == (
        "ARTIFACT.STATE_INVALID", "/artifacts/0/state"
    )


@pytest.mark.parametrize(
    "digest",
    [
        _unsafe_digest(algorithm="SHA256"),
        _unsafe_digest(canonicalization="RAW-UTF8"),
        _unsafe_digest(value=""),
        _unsafe_digest(value="A" * 64),
        _unsafe_digest(value="../" + "0" * 61),
        _unsafe_digest(value="a/" + "0" * 62),
        _unsafe_digest(value="a\\" + "0" * 62),
        _unsafe_digest(value="C:" + "0" * 62),
    ],
)
def test_r19_rejects_noncanonical_or_path_shaped_key_before_mutation(tmp_path, digest):
    root = tmp_path / "not-created"
    statement_set = _statement_set()
    key = replace(_key(statement_set_id=statement_set.statement_set_id), canonical_key_digest=digest)
    with pytest.raises((F09ContractError, F09IntegrityError)) as caught:
        artifacts.write_artifact_set(
            root, statement_set, _projections(), key=key, attempt_id="ATTEMPT", now=NOW
        )
    assert (caught.value.issue_code, caught.value.field_path) == (
        "IDEMPOTENCY.DIGEST_MISMATCH", "/canonical_key_digest"
    )
    assert not root.exists()


def test_distinct_valid_keys_resolve_to_disjoint_single_component_children(tmp_path):
    first = artifacts.resolve_artifact_operation_root(tmp_path, _key("first"))
    second = artifacts.resolve_artifact_operation_root(tmp_path, _key("second"))
    assert first != second
    assert first.parent == tmp_path.resolve()
    assert second.parent == tmp_path.resolve()
    assert len(first.relative_to(tmp_path.resolve()).parts) == 1
    assert len(second.relative_to(tmp_path.resolve()).parts) == 1


def test_writer_uses_same_directory_temp_flush_fsync_replace_post_verify_and_cleans_temp(
    tmp_path, monkeypatch
):
    events = []
    real_open = Path.open
    real_fsync = os.fsync
    real_replace = os.replace

    class ObservedFile:
        def __init__(self, handle, path):
            self._handle = handle
            self._path = path

        def __getattr__(self, name):
            return getattr(self._handle, name)

        def __enter__(self):
            self._handle.__enter__()
            return self

        def __exit__(self, *args):
            return self._handle.__exit__(*args)

        def flush(self):
            events.append(("flush", self._path))
            return self._handle.flush()

    def observed_open(path, *args, **kwargs):
        handle = real_open(path, *args, **kwargs)
        mode = args[0] if args else kwargs.get("mode", "r")
        events.append(("open", Path(path), mode))
        return ObservedFile(handle, Path(path))

    def observed_fsync(fd):
        events.append(("fsync", fd))
        return real_fsync(fd)

    def observed_replace(source, destination):
        events.append(("replace", Path(source), Path(destination)))
        return real_replace(source, destination)

    monkeypatch.setattr(Path, "open", observed_open)
    monkeypatch.setattr(os, "fsync", observed_fsync)
    monkeypatch.setattr(os, "replace", observed_replace)

    _, key, manifest = _write(tmp_path)

    assert manifest.state is ArtifactSetState.COMPLETE_VERIFIED
    replaces = [event for event in events if event[0] == "replace"]
    assert len(replaces) == 3
    for _, source, destination in replaces:
        assert source.parent == destination.parent
        assert source != destination
        assert destination.parent == tmp_path / key.canonical_key_digest.value
    previous_replace_index = -1
    for current_replace in replaces:
        replace_index = events.index(current_replace)
        write_window = events[previous_replace_index + 1:replace_index]
        assert any(event[0] == "flush" for event in write_window)
        assert any(event[0] == "fsync" for event in write_window)
        previous_replace_index = replace_index
    operation_root = tmp_path / key.canonical_key_digest.value
    assert {path.name for path in operation_root.iterdir()} == {
        "report.bin", "statement_records.bin", "statement_index.bin"
    }
    assert all(record.state is ArtifactItemState.VERIFIED for record in manifest.records)
    assert all(Path(record.path_locator).read_bytes() == _projections()[record.artifact_role] for record in manifest.records)


def test_replace_corruption_cannot_be_reported_as_verified(tmp_path, monkeypatch):
    real_replace = os.replace

    def corrupt_after_replace(source, destination):
        real_replace(source, destination)
        if Path(destination).name == "report.bin":
            Path(destination).write_bytes(b"corrupted-after-replace")

    monkeypatch.setattr(os, "replace", corrupt_after_replace)
    with pytest.raises(F09IntegrityError) as caught:
        _write(tmp_path)
    assert (caught.value.issue_code, caught.value.field_path) == (
        "ARTIFACT.DIGEST_MISMATCH", "/artifacts/observed_digest"
    )
    operation_roots = tuple(tmp_path.iterdir())
    assert len(operation_roots) == 1
    assert (operation_roots[0] / "report.bin").read_bytes() == b"corrupted-after-replace"
    assert not tuple(operation_roots[0].glob("*.tmp"))


def test_report_filesystem_failure_returns_failed_audit_without_phase_issue(tmp_path, monkeypatch):
    real_open = Path.open
    failed = False

    def fail_first_write(path, *args, **kwargs):
        nonlocal failed
        mode = args[0] if args else kwargs.get("mode", "r")
        if not failed and "w" in mode:
            failed = True
            raise OSError("report boundary unavailable")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail_first_write)
    _, _, manifest = _write(tmp_path)
    assert manifest.state is ArtifactSetState.FAILED
    assert _issue_pair(manifest) == ()
    assert len(manifest.records) == 1
    record = manifest.records[0]
    attempt = record.attempts[-1]
    assert record.artifact_role == "REPORT"
    assert record.state is ArtifactItemState.FAILED
    assert attempt.outcome == "FAILED"
    assert attempt.finished_at == NOW
    assert attempt.error_class == "OSError"
    assert attempt.error_message_digest is not None


@pytest.mark.parametrize(
    "failed_role,expected_roles,issue_path",
    [
        ("STATEMENT_RECORDS", ("REPORT", "STATEMENT_RECORDS"), "/artifacts/STATEMENT_RECORDS"),
        ("STATEMENT_INDEX", ROLES, "/artifacts/STATEMENT_INDEX"),
    ],
)
def test_t21_t22_failure_keeps_prior_files_stops_later_roles_and_returns_exact_pair(
    tmp_path, failed_role, expected_roles, issue_path
):
    _, key, manifest = _write(tmp_path, fail_after=failed_role)
    assert manifest.state is ArtifactSetState.PARTIAL
    assert tuple(record.artifact_role for record in manifest.records) == expected_roles
    assert manifest.records[-1].state is ArtifactItemState.FAILED
    assert manifest.records[-1].attempts[-1].outcome == "FAILED"
    assert _issue_pair(manifest) == (("ARTIFACT.WRITE_FAILED", issue_path),)
    operation_root = tmp_path / key.canonical_key_digest.value
    written = {path.name for path in operation_root.iterdir()}
    assert "report.bin" in written
    if failed_role == "STATEMENT_RECORDS":
        assert "statement_records.bin" not in written
        assert "statement_index.bin" not in written
    else:
        assert "statement_records.bin" in written
        assert "statement_index.bin" not in written


@pytest.mark.parametrize(
    "scenario,expected_state,expected_pair",
    [
        ("T23", ArtifactSetState.STALE_MIXED_REVISION, (("ARTIFACT.STALE_REVISION", "/artifacts/STATEMENT_INDEX"),)),
        ("T24", ArtifactSetState.DIGEST_MISMATCH, (("ARTIFACT.DIGEST_MISMATCH", "/artifacts/observed_digest"),)),
        ("T67", ArtifactSetState.COMPLETE_VERIFIED, ()),
        ("T70", ArtifactSetState.STALE_MIXED_REVISION, (("ARTIFACT.STALE_REVISION", "/artifacts/0"),)),
        ("T71", ArtifactSetState.DIGEST_MISMATCH, (("ARTIFACT.DIGEST_MISMATCH", "/artifacts/0/observed_digest"),)),
        ("T72", ArtifactSetState.COMPLETE_VERIFIED, ()),
    ],
)
def test_inspection_has_exact_t23_t24_t67_t70_t71_t72_receipts(
    tmp_path, scenario, expected_state, expected_pair
):
    _, _, manifest = _write(tmp_path)
    records = manifest.records
    if scenario == "T23":
        records = records[:2] + (replace(records[2], statement_set_id="STATEMENT-SET:old"),)
    elif scenario == "T24":
        records = (replace(records[0], observed_digest=_digest(b"different")),) + records[1:]
    elif scenario == "T70":
        records = (replace(records[0], state=ArtifactItemState.STALE),) + records[1:]
    elif scenario == "T71":
        records = (replace(records[0], state=ArtifactItemState.MISMATCH),) + records[1:]
    elif scenario == "T72":
        records = (replace(records[0], state=ArtifactItemState.SUPERSEDED),) + records[1:]
    inspected = artifacts.inspect_artifact_set(tmp_path, replace(manifest, records=records))
    assert inspected.state is expected_state
    assert _issue_pair(inspected) == expected_pair
    if scenario == "T72":
        assert inspected.records[0] == records[0]


def test_changed_key_coordinates_to_new_identity_without_overwriting_old_files(tmp_path):
    old_set, old_key, old_manifest = _write(tmp_path, "old")
    old_files = {path: path.read_bytes() for path in (tmp_path / old_key.canonical_key_digest.value).iterdir()}
    new_set = _statement_set("new")
    new_key = _key("new", statement_set_id=new_set.statement_set_id)
    new_manifest = artifacts.coordinate_artifact_operation(
        tmp_path,
        new_set,
        _projections(b"-new"),
        existing_manifest=old_manifest,
        key=new_key,
        attempt_id="ATTEMPT:new",
        now=NOW,
    )
    assert new_manifest.key == new_key
    assert new_manifest.manifest_id != old_manifest.manifest_id
    assert (tmp_path / new_key.canonical_key_digest.value).is_dir()
    assert all(path.read_bytes() == payload for path, payload in old_files.items())
    assert old_set.statement_set_id != new_set.statement_set_id


def test_t27_same_key_complete_verified_is_issue_free_no_write(tmp_path, monkeypatch):
    statement_set, key, manifest = _write(tmp_path)

    def forbidden_replace(*args, **kwargs):
        raise AssertionError("T27 no-op must not replace any target")

    monkeypatch.setattr(os, "replace", forbidden_replace)
    result = _retry(tmp_path, manifest, _projections(), statement_set, key)
    assert result.records == manifest.records
    assert result.state is ArtifactSetState.COMPLETE_VERIFIED
    assert _issue_pair(result) == ()


def test_public_coordinate_same_key_same_projections_is_noop_with_distinct_source_and_artifact_schema(
    tmp_path, monkeypatch
):
    statement_set, key, manifest = _write(tmp_path)
    assert statement_set.source_package_ref.schema_version != statement_set.statement_schema_version
    assert all(
        record.schema_version != record.attempts[0].input_snapshot_refs[0].schema_version
        for record in manifest.records
    )
    monkeypatch.setattr(Path, "open", lambda *args, **kwargs: pytest.fail("no-op must not open temp"))
    monkeypatch.setattr(os, "replace", lambda *args, **kwargs: pytest.fail("no-op must not replace"))
    result = artifacts.coordinate_artifact_operation(
        tmp_path,
        statement_set,
        _projections(),
        existing_manifest=manifest,
        key=key,
        attempt_id="ATTEMPT:no-op",
        now=NOW,
    )
    assert result.records == manifest.records
    assert result.digest == artifacts.digest_artifact_records(result.records)
    assert result.state is ArtifactSetState.COMPLETE_VERIFIED
    assert _issue_pair(result) == ()


def test_retry_noop_allows_distinct_refs_to_share_one_revision_id(tmp_path, monkeypatch):
    statement_set, key, manifest = _write(tmp_path)
    first = statement_set.source_package_ref
    refs = (
        first,
        replace(
            _ref("shared-revision"),
            revision_id=first.revision_id,
            contract_version=first.contract_version,
        ),
    )
    records = tuple(
        replace(
            record,
            attempts=tuple(
                replace(attempt, input_snapshot_refs=refs)
                for attempt in record.attempts
            ),
        )
        for record in manifest.records
    )
    retained = replace(manifest, records=records)
    operation_root = tmp_path / key.canonical_key_digest.value
    real_open = Path.open
    real_read_bytes = Path.read_bytes
    snapshot = {
        path.relative_to(operation_root): real_read_bytes(path)
        for path in operation_root.rglob("*")
        if path.is_file()
    }

    def read_only_open(path, *args, **kwargs):
        mode = args[0] if args else kwargs.get("mode", "r")
        if any(flag in mode for flag in "wax+"):
            pytest.fail("no-op must not open a filesystem path for mutation")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", lambda *args, **kwargs: pytest.fail("no-op must not mkdir"))
    monkeypatch.setattr(Path, "open", read_only_open)
    monkeypatch.setattr(os, "replace", lambda *args, **kwargs: pytest.fail("no-op must not replace"))
    monkeypatch.setattr(Path, "unlink", lambda *args, **kwargs: pytest.fail("no-op must not unlink"))
    monkeypatch.setattr(os, "remove", lambda *args, **kwargs: pytest.fail("no-op must not remove"))
    monkeypatch.setattr(os, "unlink", lambda *args, **kwargs: pytest.fail("no-op must not os.unlink"))

    result = artifacts.retry_artifact_set(
        tmp_path,
        retained,
        _projections(),
        key=key,
        current_frozen_input_refs=refs,
        current_schema_version=statement_set.statement_schema_version,
        current_statement_set_id=statement_set.statement_set_id,
        current_contract_digest=key.contract_digest,
        attempt_id="RETRY:shared-revision",
        now=NOW,
    )

    after = {
        path.relative_to(operation_root): real_read_bytes(path)
        for path in operation_root.rglob("*")
        if path.is_file()
    }
    assert after == snapshot
    assert result.records == retained.records
    assert tuple(record.attempts for record in result.records) == tuple(
        record.attempts for record in retained.records
    )
    assert result.state is ArtifactSetState.COMPLETE_VERIFIED
    assert _issue_pair(result) == ()


def test_retry_noop_allows_refs_with_distinct_contract_versions(tmp_path, monkeypatch):
    statement_set, key, manifest = _write(tmp_path)
    first = statement_set.source_package_ref
    refs = (
        first,
        replace(
            _ref("distinct-contract"),
            revision_id="REVISION:distinct-contract",
            contract_version="contract:other",
        ),
    )
    records = tuple(
        replace(
            record,
            attempts=tuple(
                replace(attempt, input_snapshot_refs=refs)
                for attempt in record.attempts
            ),
        )
        for record in manifest.records
    )
    retained = replace(manifest, records=records)
    operation_root = tmp_path / key.canonical_key_digest.value
    real_open = Path.open
    real_read_bytes = Path.read_bytes
    snapshot = {
        path.relative_to(operation_root): real_read_bytes(path)
        for path in operation_root.rglob("*")
        if path.is_file()
    }

    def read_only_open(path, *args, **kwargs):
        mode = args[0] if args else kwargs.get("mode", "r")
        if any(flag in mode for flag in "wax+"):
            pytest.fail("no-op must not open a filesystem path for mutation")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", lambda *args, **kwargs: pytest.fail("no-op must not mkdir"))
    monkeypatch.setattr(Path, "open", read_only_open)
    monkeypatch.setattr(os, "replace", lambda *args, **kwargs: pytest.fail("no-op must not replace"))
    monkeypatch.setattr(Path, "unlink", lambda *args, **kwargs: pytest.fail("no-op must not unlink"))
    monkeypatch.setattr(os, "remove", lambda *args, **kwargs: pytest.fail("no-op must not remove"))
    monkeypatch.setattr(os, "unlink", lambda *args, **kwargs: pytest.fail("no-op must not os.unlink"))

    result = artifacts.retry_artifact_set(
        tmp_path,
        retained,
        _projections(),
        key=key,
        current_frozen_input_refs=refs,
        current_schema_version=statement_set.statement_schema_version,
        current_statement_set_id=statement_set.statement_set_id,
        current_contract_digest=key.contract_digest,
        attempt_id="RETRY:distinct-contract",
        now=NOW,
    )

    after = {
        path.relative_to(operation_root): real_read_bytes(path)
        for path in operation_root.rglob("*")
        if path.is_file()
    }
    assert after == snapshot
    assert result.records == retained.records
    assert tuple(record.attempts for record in result.records) == tuple(
        record.attempts for record in retained.records
    )
    assert result.state is ArtifactSetState.COMPLETE_VERIFIED
    assert _issue_pair(result) == ()


def test_t27_latest_unknown_matching_final_is_read_only_reconciled_without_attempt_mutation(
    tmp_path, monkeypatch
):
    statement_set, key, manifest = _write(tmp_path)
    report = manifest.records[0]
    unknown = replace(
        report.attempts[-1], finished_at=None, outcome="UNKNOWN",
        observed_digest=None, error_class=None, error_message_digest=None,
    )
    manifest = replace(manifest, records=(replace(report, attempts=(unknown,)),) + manifest.records[1:])
    attempts_before = manifest.records[0].attempts
    target = Path(report.path_locator)
    real_open = Path.open

    def final_read_only_open(path, *args, **kwargs):
        mode = args[0] if args else kwargs.get("mode", "r")
        if path != target or any(flag in mode for flag in "wax+"):
            pytest.fail("reconciliation may only read the committed final")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", final_read_only_open)
    monkeypatch.setattr(os, "replace", lambda *args, **kwargs: pytest.fail("reconciliation must not replace"))
    result = _retry(tmp_path, manifest, _projections(), statement_set, key)
    reconciled = result.records[0]
    assert reconciled.attempts == attempts_before == (unknown,)
    assert reconciled.attempts[-1].outcome == "UNKNOWN"
    assert reconciled.observed_digest == _digest(_projections()["REPORT"])
    assert reconciled.state is ArtifactItemState.VERIFIED
    assert result.digest == artifacts.digest_artifact_records(result.records)


@pytest.mark.parametrize("final_state", ["missing", "mismatch"])
def test_t27_latest_unknown_missing_or_mismatched_final_fails_closed_without_mutation(
    tmp_path, monkeypatch, final_state
):
    statement_set, key, manifest = _write(tmp_path)
    report = manifest.records[0]
    unknown = replace(
        report.attempts[-1], finished_at=None, outcome="UNKNOWN",
        observed_digest=None, error_class=None, error_message_digest=None,
    )
    manifest = replace(manifest, records=(replace(report, attempts=(unknown,)),) + manifest.records[1:])
    target = Path(report.path_locator)
    target.unlink() if final_state == "missing" else target.write_bytes(b"mismatch")
    final_before = None if final_state == "missing" else target.read_bytes()
    records_before = manifest.records
    real_open = Path.open

    def final_read_only_open(path, *args, **kwargs):
        mode = args[0] if args else kwargs.get("mode", "r")
        if path != target or any(flag in mode for flag in "wax+"):
            pytest.fail("failed reconciliation may only read the committed final")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", final_read_only_open)
    monkeypatch.setattr(os, "replace", lambda *args, **kwargs: pytest.fail("failed reconciliation must not replace"))
    with pytest.raises(F09IntegrityError) as caught:
        _retry(tmp_path, manifest, _projections(), statement_set, key)
    assert type(caught.value) is F09IntegrityError
    assert (caught.value.issue_code, caught.value.field_path) == (
        "ARTIFACT.DIGEST_MISMATCH", "/artifacts/observed_digest"
    )
    assert manifest.records == records_before
    assert manifest.records[0].attempts == (unknown,)
    assert target.exists() is (final_state == "mismatch")
    if final_before is not None:
        assert target.read_bytes() == final_before
    assert not tuple(target.parent.glob("*.tmp"))


def test_t28_same_key_different_target_digest_blocks_every_write(tmp_path, monkeypatch):
    statement_set, key, manifest = _write(tmp_path)

    def forbidden_open(*args, **kwargs):
        raise AssertionError("T28 must return before any filesystem open")

    monkeypatch.setattr(Path, "open", forbidden_open)
    result = _retry(tmp_path, manifest, _projections(b"-changed"), statement_set, key)
    assert result.records == manifest.records
    assert result.state is ArtifactSetState.DIGEST_MISMATCH
    assert _issue_pair(result) == (("IDEMPOTENCY.DIGEST_MISMATCH", "/canonical_key_digest"),)


@pytest.mark.parametrize(
    "failed_role,rewritten_roles",
    [
        ("STATEMENT_RECORDS", ("STATEMENT_RECORDS", "STATEMENT_INDEX")),
        ("STATEMENT_INDEX", ("STATEMENT_INDEX",)),
    ],
)
def test_t21_t22_retry_writes_only_failed_or_missing_roles_and_appends_attempts(
    tmp_path, monkeypatch, failed_role, rewritten_roles
):
    statement_set, key, partial = _write(tmp_path, fail_after=failed_role)
    before = {record.artifact_role: record for record in partial.records}
    replaced_destinations = []
    real_replace = os.replace

    def observed_replace(source, destination):
        replaced_destinations.append(Path(destination).name)
        return real_replace(source, destination)

    monkeypatch.setattr(os, "replace", observed_replace)
    result = _retry(tmp_path, partial, _projections(), statement_set, key)
    assert result.state is ArtifactSetState.COMPLETE_VERIFIED
    assert tuple(name.removesuffix(".bin").upper() for name in replaced_destinations) == rewritten_roles
    after = {record.artifact_role: record for record in result.records}
    assert after["REPORT"] == before["REPORT"]
    if failed_role == "STATEMENT_INDEX":
        assert after["STATEMENT_RECORDS"] == before["STATEMENT_RECORDS"]
    failed_before = before[failed_role]
    failed_after = after[failed_role]
    assert failed_after.attempts[:-1] == failed_before.attempts
    assert failed_after.attempts[-1].attempt_number == len(failed_before.attempts) + 1
    assert failed_after.attempts[-1].retry_of_attempt_id == failed_before.attempts[-1].attempt_id


@pytest.mark.parametrize(
    "mutation",
    [
        "empty", "record_schema", "attempt_type", "artifact_id", "number", "number_bool", "retry_chain", "input_refs",
        "idempotency", "object_type", "object_id", "revision", "schema", "contract",
        "content_digest", "source_locator", "empty_attempt_id", "duplicate_attempt_id",
        "succeeded_fields", "failed_fields", "unknown_fields",
    ],
)
def test_retry_validates_each_retained_record_local_history_before_current_selection(
    tmp_path, mutation
):
    statement_set, key, manifest = _write(tmp_path)
    superseded = replace(manifest.records[0], state=ArtifactItemState.SUPERSEDED)
    attempts = superseded.attempts
    if mutation == "empty":
        attempts = ()
    elif mutation == "attempt_type":
        attempts = (object(),)
    elif mutation == "artifact_id":
        attempts = (replace(attempts[0], artifact_id="OTHER"),)
    elif mutation == "number":
        attempts = (replace(attempts[0], attempt_number=2),)
    elif mutation == "number_bool":
        attempts = (replace(attempts[0], attempt_number=True),)
    elif mutation == "retry_chain":
        attempts = (replace(attempts[0], retry_of_attempt_id="MISSING"),)
    elif mutation == "input_refs":
        attempts = (replace(attempts[0], input_snapshot_refs=()),)
    elif mutation == "idempotency":
        attempts = (replace(attempts[0], idempotency_key="not-a-key"),)
    elif mutation in (
        "object_type", "object_id", "revision", "schema", "contract",
        "content_digest", "source_locator",
    ):
        first = attempts[0]
        ref = first.input_snapshot_refs[0]
        if mutation == "content_digest":
            drifted_ref = replace(
                ref,
                digest_binding=DigestPresent(
                    "PRESENT", _digest(b"drift", KEY_CANONICALIZATION)
                ),
            )
        else:
            field = {
                "object_type": "object_type",
                "object_id": "object_id",
                "revision": "revision_id",
                "schema": "schema_version",
                "contract": "contract_version",
                "source_locator": "source_locator_id",
            }[mutation]
            drifted_ref = replace(ref, **{field: "drift"})
        attempts = (
            first,
            replace(
                first,
                attempt_id=f"ATTEMPT:drift:{mutation}",
                attempt_number=2,
                retry_of_attempt_id=first.attempt_id,
                input_snapshot_refs=(drifted_ref,),
            ),
        )
    elif mutation == "empty_attempt_id":
        attempts = (replace(attempts[0], attempt_id=""),)
    elif mutation == "duplicate_attempt_id":
        first = attempts[0]
        attempts = (first, replace(first, attempt_number=2, retry_of_attempt_id=first.attempt_id))
    elif mutation == "succeeded_fields":
        attempts = (replace(attempts[0], observed_digest=None),)
    elif mutation == "failed_fields":
        attempts = (replace(attempts[0], outcome="FAILED", observed_digest=None),)
    elif mutation == "unknown_fields":
        attempts = (replace(attempts[0], outcome="UNKNOWN"),)
    malformed = replace(
        superseded,
        schema_version="" if mutation == "record_schema" else superseded.schema_version,
        attempts=attempts,
    )
    root = tmp_path / "retry-must-not-mutate"
    with pytest.raises(F09ContractError) as caught:
        _retry(root, replace(manifest, records=(malformed,) + manifest.records[1:]), _projections(), statement_set, key)
    assert type(caught.value) is F09ContractError
    assert (caught.value.issue_code, caught.value.field_path) == (
        "ARTIFACT.STATE_INVALID", "/artifacts/0/attempts"
    )
    assert not root.exists()


@pytest.mark.parametrize("illegal_state", ["NOT_STARTED", "WRITTEN"])
def test_retry_rejects_illegal_state_before_current_selection_or_mutation(tmp_path, illegal_state):
    statement_set, key, manifest = _write(tmp_path)
    malformed = replace(manifest.records[0], state=illegal_state)
    root = tmp_path / "illegal-retry"
    with pytest.raises(F09ContractError) as caught:
        _retry(root, replace(manifest, records=(malformed,) + manifest.records[1:]), _projections(), statement_set, key)
    assert (caught.value.issue_code, caught.value.field_path) == (
        "ARTIFACT.STATE_INVALID", "/artifacts/0/state"
    )
    assert not root.exists()


def test_retry_rejects_invalid_r19_key_before_mutation(tmp_path):
    statement_set, key, manifest = _write(tmp_path)
    invalid_key = replace(key, canonical_key_digest=_unsafe_digest(value="A" * 64))
    root = tmp_path / "invalid-retry-key"
    with pytest.raises(F09IntegrityError) as caught:
        _retry(root, replace(manifest, key=invalid_key), _projections(), statement_set, invalid_key)
    assert (caught.value.issue_code, caught.value.field_path) == (
        "IDEMPOTENCY.DIGEST_MISMATCH", "/canonical_key_digest"
    )
    assert not root.exists()


def test_inspection_rejects_duplicate_current_required_role(tmp_path):
    _, _, manifest = _write(tmp_path)
    duplicate = replace(manifest.records[0], artifact_id="ARTIFACT:DUPLICATE:REPORT")
    with pytest.raises(F09ContractError) as caught:
        artifacts.inspect_artifact_set(tmp_path, replace(manifest, records=manifest.records + (duplicate,)))
    assert (caught.value.issue_code, caught.value.field_path) == (
        "ARTIFACT.STATE_INVALID", "/artifacts/REPORT"
    )


def test_retry_preserves_old_identity_superseded_history_and_excludes_it_from_current(tmp_path):
    statement_set, key, partial = _write(tmp_path, fail_after="STATEMENT_INDEX")
    historical_ref = _ref("historical")
    current_report = partial.records[0]
    historical_attempt = replace(
        current_report.attempts[0],
        attempt_id="ATTEMPT:historical:REPORT",
        input_snapshot_refs=(historical_ref,),
        idempotency_key="f" * 64,
    )
    superseded = replace(
        current_report,
        artifact_id="ARTIFACT:HISTORICAL:REPORT",
        statement_set_id="STATEMENT-SET:historical",
        path_locator=(tmp_path / ("f" * 64) / "report.bin").as_posix(),
        schema_version="schema:historical",
        state=ArtifactItemState.SUPERSEDED,
        attempts=(replace(historical_attempt, artifact_id="ARTIFACT:HISTORICAL:REPORT"),),
    )
    with_history = replace(partial, records=(superseded,) + partial.records)
    result = _retry(tmp_path, with_history, _projections(), statement_set, key)
    assert result.records[0] == superseded
    assert sum(record.state is ArtifactItemState.SUPERSEDED for record in result.records) == 1
    assert _issue_pair(result) == ()


def test_missing_current_role_uses_explicit_current_authority_not_historical_attempt(tmp_path):
    statement_set, key, partial = _write(tmp_path, fail_after="STATEMENT_RECORDS")
    report, failed_records = partial.records
    historical = replace(
        failed_records,
        artifact_id="ARTIFACT:HISTORICAL:STATEMENT_INDEX",
        artifact_role="STATEMENT_INDEX",
        statement_set_id="STATEMENT-SET:historical",
        path_locator=(tmp_path / ("e" * 64) / "statement_index.bin").as_posix(),
        schema_version="schema:historical",
        state=ArtifactItemState.SUPERSEDED,
        attempts=(replace(
            failed_records.attempts[0],
            attempt_id="ATTEMPT:historical:STATEMENT_INDEX",
            artifact_id="ARTIFACT:HISTORICAL:STATEMENT_INDEX",
            idempotency_key="e" * 64,
            input_snapshot_refs=(_ref("historical"),),
        ),),
    )
    result = _retry(
        tmp_path,
        replace(partial, records=(historical, report, failed_records)),
        _projections(),
        statement_set,
        key,
    )
    current_index = next(
        record for record in result.records
        if record.artifact_role == "STATEMENT_INDEX" and record.state is not ArtifactItemState.SUPERSEDED
    )
    assert current_index.schema_version == statement_set.statement_schema_version
    assert current_index.statement_set_id == statement_set.statement_set_id
    assert current_index.attempts[0].input_snapshot_refs == (statement_set.source_package_ref,)
    assert result.records[0] == historical


def test_retry_manifest_digest_is_recomputed_from_exact_returned_ordered_records(tmp_path):
    statement_set, key, partial = _write(tmp_path, fail_after="STATEMENT_RECORDS")
    result = _retry(tmp_path, partial, _projections(), statement_set, key)
    assert result.digest == artifacts.digest_artifact_records(result.records)
    assert result.digest != partial.digest
    reversed_records = tuple(reversed(result.records))
    assert artifacts.digest_artifact_records(reversed_records) != result.digest


@pytest.mark.parametrize("boundary", ["open", "write", "flush", "fsync", "replace", "post_read"])
def test_atomic_write_failure_boundaries_preserve_old_or_committed_final_and_never_verify(
    tmp_path, monkeypatch, boundary
):
    statement_set = _statement_set()
    key = _key(statement_set_id=statement_set.statement_set_id)
    operation_root = tmp_path / key.canonical_key_digest.value
    operation_root.mkdir(parents=True)
    target = operation_root / "report.bin"
    old_final = b"old-final"
    target.write_bytes(old_final)
    real_open = Path.open
    real_fsync = os.fsync
    real_replace = os.replace
    real_read_bytes = Path.read_bytes

    class FailingHandle:
        def __init__(self, handle):
            self.handle = handle
        def __enter__(self):
            self.handle.__enter__()
            return self
        def __exit__(self, *args):
            return self.handle.__exit__(*args)
        def __getattr__(self, name):
            return getattr(self.handle, name)
        def write(self, payload):
            if boundary == "write":
                raise OSError("write boundary")
            return self.handle.write(payload)
        def flush(self):
            if boundary == "flush":
                raise OSError("flush boundary")
            return self.handle.flush()

    def controlled_open(path, *args, **kwargs):
        mode = args[0] if args else kwargs.get("mode", "r")
        if boundary == "open" and "w" in mode:
            raise OSError("open boundary")
        handle = real_open(path, *args, **kwargs)
        return FailingHandle(handle) if "w" in mode else handle

    def controlled_fsync(fd):
        if boundary == "fsync":
            raise OSError("fsync boundary")
        return real_fsync(fd)

    def controlled_replace(source, destination):
        if boundary == "replace":
            raise OSError("replace boundary")
        return real_replace(source, destination)

    def controlled_read(path):
        if boundary == "post_read" and Path(path).name == "report.bin":
            raise OSError("post-read boundary")
        return real_read_bytes(path)

    monkeypatch.setattr(Path, "open", controlled_open)
    monkeypatch.setattr(os, "fsync", controlled_fsync)
    monkeypatch.setattr(os, "replace", controlled_replace)
    monkeypatch.setattr(Path, "read_bytes", controlled_read)
    manifest = artifacts.write_artifact_set(
        tmp_path,
        statement_set,
        _projections(),
        key=key,
        attempt_id="ATTEMPT:atomic-failure",
        now=NOW,
    )
    assert manifest.state is ArtifactSetState.FAILED
    assert manifest.records[0].state is ArtifactItemState.FAILED
    assert manifest.records[0].attempts[-1].outcome == "FAILED"
    assert all(record.state is not ArtifactItemState.VERIFIED for record in manifest.records)
    assert not tuple(operation_root.glob("*.tmp"))
    assert real_read_bytes(target) == (
        _projections()["REPORT"] if boundary == "post_read" else old_final
    )
    assert _issue_pair(manifest) == ()


def test_post_commit_byte_digest_verification_failure_keeps_committed_final_and_never_verifies(
    tmp_path, monkeypatch
):
    statement_set = _statement_set()
    key = _key(statement_set_id=statement_set.statement_set_id)
    operation_root = tmp_path / key.canonical_key_digest.value
    operation_root.mkdir(parents=True)
    target = operation_root / "report.bin"
    target.write_bytes(b"old-final")
    real_payload_digest = artifacts._payload_digest
    digest_calls = 0

    def mismatched_observed_digest(payload):
        nonlocal digest_calls
        digest_calls += 1
        digest = real_payload_digest(payload)
        if digest_calls == 3:
            return replace(digest, value="0" * 64)
        return digest

    monkeypatch.setattr(artifacts, "_payload_digest", mismatched_observed_digest)
    with pytest.raises(F09IntegrityError) as caught:
        artifacts.write_artifact_set(
            tmp_path,
            statement_set,
            _projections(),
            key=key,
            attempt_id="ATTEMPT:post-commit-digest",
            now=NOW,
        )
    assert type(caught.value) is F09IntegrityError
    assert (caught.value.issue_code, caught.value.field_path) == (
        "ARTIFACT.DIGEST_MISMATCH", "/artifacts/observed_digest"
    )
    assert target.read_bytes() == _projections()["REPORT"]
    assert not tuple(operation_root.glob("*.tmp"))


def test_artifact_public_contract_does_not_infer_feedback_or_learning_readiness():
    public_types = (
        artifacts.IdempotencyKey,
        artifacts.ArtifactWriteAttempt,
        artifacts.ArtifactRecord,
        artifacts.ArtifactSetManifest,
    )
    forbidden = {"feedback_ready", "learning_ready", "feedback_readiness", "learning_readiness"}
    for cls in public_types:
        assert forbidden.isdisjoint(field.name for field in fields(cls))
    assert not hasattr(artifacts.ArtifactSetManifest, "is_feedback_ready")
    assert not hasattr(artifacts.ArtifactSetManifest, "is_learning_ready")


def test_run_artifact_key_is_independent_and_canonicalizable():
    refs = (_ref("run-input"),)
    roles = ("RUN_SNAPSHOT", "DECISION_RUN")
    payload_digests = {role: _digest(role.encode("utf-8")) for role in roles}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        operation="PROJECT_RUN_ARTIFACT_SET",
        case_id="CASE:F09:RUN",
        track=RunTrack.PRODUCTION_DEFAULT,
        run_id="RUN:current",
        source_digest=_digest(b"run-source", KEY_CANONICALIZATION),
        schema_versions_digest=_digest(b"run-schema", KEY_CANONICALIZATION),
        contract_digest=_digest(b"run-contract", KEY_CANONICALIZATION),
        input_snapshot_refs_graph_digest=refs_digest,
        projection_roles=roles,
        projection_digest_by_role=payload_digests,
        canonical_key_digest=artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET",
            case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT,
            run_id="RUN:current",
            source_digest=_digest(b"run-source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"run-schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"run-contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest,
            projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )

    assert key.canonical_key_digest == artifacts._digest_run_artifact_set_key_v1_from_key(key)
    assert not isinstance(key, artifacts.IdempotencyKey)


def test_coordinate_run_artifact_set_writes_and_public_verifier_rebuilds_graph(tmp_path):
    refs = (_ref("run-write"),)
    projections = {"RUN_SNAPSHOT": b"run", "DECISION_RUN": b"decision"}
    roles = tuple(projections)
    payload_digests = {role: _digest(payload) for role, payload in projections.items()}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        operation="PROJECT_RUN_ARTIFACT_SET",
        case_id="CASE:F09:RUN",
        track=RunTrack.PRODUCTION_DEFAULT,
        run_id="RUN:write",
        source_digest=_digest(b"run-source", KEY_CANONICALIZATION),
        schema_versions_digest=_digest(b"run-schema", KEY_CANONICALIZATION),
        contract_digest=_digest(b"run-contract", KEY_CANONICALIZATION),
        input_snapshot_refs_graph_digest=refs_digest,
        projection_roles=roles,
        projection_digest_by_role=payload_digests,
        canonical_key_digest=artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:write",
            source_digest=_digest(b"run-source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"run-schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"run-contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    request = artifacts.RunArtifactSetRequestV1(
        key=key, run_id=key.run_id, input_snapshot_refs=refs,
        schema_version="f09.run-artifact.v1", projections=projections,
    )

    manifest = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=None, attempt_id="RUN-ATTEMPT", now=NOW
    )

    assert manifest.key is key
    assert manifest.state is ArtifactSetState.COMPLETE_VERIFIED
    assert artifacts.validate_run_artifact_manifest_v1(manifest) == manifest.digest
    assert artifacts.inspect_run_artifact_set_v1(tmp_path, manifest).state is ArtifactSetState.COMPLETE_VERIFIED


def test_public_verified_run_manifest_fixture_is_fresh_pure_and_verifier_accepted(monkeypatch):
    signature = inspect.signature(artifacts.provision_verified_run_manifest_fixture_v1)
    assert tuple(signature.parameters) == ()
    assert get_type_hints(artifacts.provision_verified_run_manifest_fixture_v1)["return"] is artifacts.ArtifactSetManifest

    def forbidden(*args, **kwargs):
        raise AssertionError("fixture must not use filesystem or run lifecycle ports")

    for name in (
        "coordinate_run_artifact_set_v1",
        "inspect_run_artifact_set_v1",
        "reconcile_run_artifact_set_v1",
        "_atomic_write_verified",
    ):
        monkeypatch.setattr(artifacts, name, forbidden)

    first = artifacts.provision_verified_run_manifest_fixture_v1()
    second = artifacts.provision_verified_run_manifest_fixture_v1()

    assert type(first) is artifacts.ArtifactSetManifest
    assert first is not second
    assert first.key is not second.key
    assert first.records is not second.records
    assert first.key.projection_digest_by_role is not second.key.projection_digest_by_role
    assert first.records[0] is not second.records[0]
    assert first.records[0].attempts[0] is not second.records[0].attempts[0]
    assert first.records[0].attempts[0].input_snapshot_refs is not second.records[0].attempts[0].input_snapshot_refs
    assert first.key.track is RunTrack.V5_V6_PREPROD
    assert first.key.operation == "PROJECT_RUN_ARTIFACT_SET"
    assert first.key.projection_roles == ("RUN_SNAPSHOT", "DECISION_RUN", "FEEDBACK_ATTACHMENT")
    assert tuple(record.artifact_role for record in first.records) == first.key.projection_roles
    assert first.state is ArtifactSetState.COMPLETE_VERIFIED
    assert all(record.state is ArtifactItemState.VERIFIED for record in first.records)
    assert all(len(record.attempts) == 1 and record.attempts[0].outcome == "SUCCEEDED" for record in first.records)
    assert artifacts.validate_run_artifact_manifest_v1(first) == first.digest
    assert artifacts.validate_run_artifact_manifest_v1(second) == second.digest

    for forged in (
        replace(first.key, operation="PROJECT_ARTIFACT_SET"),
        replace(first.key, projection_roles=("RUN_SNAPSHOT", "DECISION_RUN")),
    ):
        tampered = replace(first, key=forged)
        try:
            artifacts.validate_run_artifact_manifest_v1(tampered)
        except F09ContractError:
            pass
        else:
            pytest.fail("fixture key operation and role-closure mutations must fail closed")

    invalid_key = replace(first.key, canonical_key_digest=_digest(b"forged-key", KEY_CANONICALIZATION))
    with pytest.raises(F09IntegrityError):
        artifacts.validate_run_artifact_manifest_v1(replace(first, key=invalid_key))

    for field, value in (
        ("case_id", "CASE:F09:OTHER"),
        ("track", RunTrack.PRODUCTION_DEFAULT),
        ("run_id", "RUN:F09:OTHER"),
    ):
        forged_record = replace(first.records[0], **{field: value})
        forged_records = (forged_record,) + first.records[1:]
        with pytest.raises(F09IntegrityError):
            artifacts.validate_run_artifact_manifest_v1(
                replace(first, records=forged_records, digest=artifacts.digest_artifact_records(forged_records))
            )

    reordered_records = (first.records[1], first.records[0], first.records[2])
    with pytest.raises(F09IntegrityError):
        artifacts.validate_run_artifact_manifest_v1(
            replace(first, records=reordered_records, digest=artifacts.digest_artifact_records(reordered_records))
        )

    replaced_role_record = replace(first.records[0], artifact_role="FEEDBACK_ATTACHMENT")
    replaced_role_records = (replaced_role_record,) + first.records[1:]
    replaced_role_manifest = replace(
        first,
        records=replaced_role_records,
        digest=artifacts.digest_artifact_records(replaced_role_records),
    )
    assert replaced_role_manifest.key.canonical_key_digest == first.key.canonical_key_digest
    with pytest.raises(F09IntegrityError):
        artifacts.validate_run_artifact_manifest_v1(replaced_role_manifest)

    for forged_record in (
        replace(first.records[0], expected_digest=_digest(b"forged-record")),
        replace(first.records[0], state=ArtifactItemState.FAILED),
    ):
        forged_records = (forged_record,) + first.records[1:]
        with pytest.raises(F09IntegrityError):
            artifacts.validate_run_artifact_manifest_v1(
                replace(first, records=forged_records, digest=artifacts.digest_artifact_records(forged_records))
            )

    tampered_attempt = replace(first.records[0].attempts[0], input_snapshot_refs=())
    tampered_record = replace(first.records[0], attempts=(tampered_attempt,))
    tampered_records = (tampered_record,) + first.records[1:]
    with pytest.raises(F09IntegrityError):
        artifacts.validate_run_artifact_manifest_v1(
            replace(first, records=tampered_records, digest=artifacts.digest_artifact_records(tampered_records))
        )

    for tampered_manifest in (
        replace(first, digest=_digest(b"forged-manifest")),
        replace(first, state=ArtifactSetState.PARTIAL),
    ):
        with pytest.raises(F09IntegrityError):
            artifacts.validate_run_artifact_manifest_v1(tampered_manifest)


def test_public_verified_run_manifest_fixture_static_boundary_is_exact():
    module = ast.parse(Path(inspect.getsourcefile(artifacts)).read_text(encoding="utf-8"))
    definitions = {
        node.name: node for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    fixture = definitions["provision_verified_run_manifest_fixture_v1"]

    def direct_calls(node):
        return {
            child.func.id for child in ast.walk(node)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
        }

    forbidden_calls = {
        "coordinate_artifact_operation", "write_artifact_set", "inspect_artifact_set",
        "retry_artifact_set", "coordinate_run_artifact_set_v1",
        "inspect_run_artifact_set_v1", "reconcile_run_artifact_set_v1",
        "_atomic_write_verified", "_resolve_run_artifact_root_v1",
        "evaluate_learning_eligibility", "validate_learning_eligibility",
        "bind_feedback_operation", "validate_feedback_binding_record", "open", "exec",
        "eval", "compile", "__import__",
    }
    forbidden_members = {
        "open", "read_bytes", "read_text", "write_bytes", "write_text", "mkdir",
        "unlink", "replace", "resolve", "is_file", "exists", "glob", "rglob",
        "iterdir", "walk", "listdir", "scandir", "getenv", "environ", "time",
        "monotonic", "perf_counter", "sleep", "random", "randint", "randrange",
        "choice", "choices", "token_bytes", "token_hex", "uuid4", "connect",
        "request", "urlopen", "send", "recv", "system", "popen", "run",
    }

    def boundary_violations(definition_map, root_name):
        reachable = set()
        pending = [root_name]
        while pending:
            name = pending.pop()
            if name in reachable:
                continue
            reachable.add(name)
            pending.extend(direct_calls(definition_map[name]) & definition_map.keys())
        reachable_nodes = tuple(definition_map[name] for name in reachable)
        reachable_calls = set().union(*(direct_calls(node) for node in reachable_nodes))
        reachable_members = {
            child.attr for node in reachable_nodes for child in ast.walk(node)
            if isinstance(child, ast.Attribute)
        }
        return reachable, reachable_calls & forbidden_calls, reachable_members & forbidden_members

    calls = direct_calls(fixture)
    private_calls = {name for name in calls if name.startswith("_")}
    imported_private_names = {
        alias.name for node in module.body if isinstance(node, ast.ImportFrom)
        for alias in node.names if alias.name.startswith("_")
    }
    reachable, forbidden_reachable_calls, forbidden_reachable_members = boundary_violations(
        definitions, "provision_verified_run_manifest_fixture_v1"
    )
    mutant = ast.parse(
        "def provision_verified_run_manifest_fixture_v1():\n"
        "    return _digest_run_input_snapshot_refs_v1()\n\n"
        "def _digest_run_input_snapshot_refs_v1():\n"
        "    open('forbidden')\n"
        "    return os.environ['FIXTURE_DRIFT']\n"
    )
    mutant_definitions = {
        node.name: node for node in mutant.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    mutant_reachable, mutant_calls, mutant_members = boundary_violations(
        mutant_definitions, "provision_verified_run_manifest_fixture_v1"
    )

    assert fixture.args.posonlyargs == []
    assert fixture.args.args == []
    assert fixture.args.kwonlyargs == []
    assert fixture.args.vararg is None
    assert fixture.args.kwarg is None
    assert private_calls == {
        "_digest_run_input_snapshot_refs_v1",
        "_digest_run_artifact_set_key_v1",
    }
    assert not forbidden_reachable_calls
    assert not forbidden_reachable_members
    assert mutant_reachable == {
        "provision_verified_run_manifest_fixture_v1",
        "_digest_run_input_snapshot_refs_v1",
    }
    assert mutant_calls == {"open"}
    assert mutant_members == {"environ"}
    assert {name for name in reachable if name.startswith("_")} <= {
        "_digest_ref_material", "_digest_ref_shape_valid", "_digest_run_input_snapshot_refs_v1",
        "_digest_run_artifact_set_key_v1", "_digest_run_artifact_set_key_v1_from_key",
        "_run_digest_material", "_versioned_ref_material",
    }
    assert imported_private_names == set()


def test_run_request_rejects_role_closure_before_creating_root(tmp_path):
    refs = (_ref("run-invalid"),)
    roles = ("RUN_SNAPSHOT",)
    payload_digests = {"RUN_SNAPSHOT": _digest(b"run")}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
        track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:invalid",
        source_digest=_digest(b"source", KEY_CANONICALIZATION),
        schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
        contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
        input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
        projection_digest_by_role=payload_digests,
        canonical_key_digest=_digest(b"fixed-key", KEY_CANONICALIZATION),
    )
    request = artifacts.RunArtifactSetRequestV1(
        key=key, run_id=key.run_id, input_snapshot_refs=refs,
        schema_version="f09.run-artifact.v1", projections={"RUN_SNAPSHOT": b"run"},
    )

    with pytest.raises(F09ContractError):
        artifacts.coordinate_run_artifact_set_v1(
            tmp_path / "must-not-exist", request, existing_manifest=None,
            attempt_id="ATTEMPT", now=NOW,
        )

    assert not (tmp_path / "must-not-exist").exists()


def test_run_public_verifier_rejects_attempt_receipt_from_another_key(tmp_path):
    refs = (_ref("run-receipt"),)
    projections = {"RUN_SNAPSHOT": b"run", "DECISION_RUN": b"decision"}
    roles = tuple(projections)
    payload_digests = {role: _digest(payload) for role, payload in projections.items()}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
        track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:receipt",
        source_digest=_digest(b"source", KEY_CANONICALIZATION),
        schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
        contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
        input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
        projection_digest_by_role=payload_digests,
        canonical_key_digest=artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:receipt",
            source_digest=_digest(b"source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    request = artifacts.RunArtifactSetRequestV1(
        key=key, run_id=key.run_id, input_snapshot_refs=refs,
        schema_version="f09.run-artifact.v1", projections=projections,
    )
    manifest = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=None, attempt_id="ATTEMPT", now=NOW
    )
    first = manifest.records[0]
    forged_attempt = replace(first.attempts[0], idempotency_key="0" * 64)
    forged_record = replace(first, attempts=(forged_attempt,))
    forged_records = (forged_record,) + manifest.records[1:]
    forged = replace(manifest, records=forged_records, digest=artifacts.digest_artifact_records(forged_records))

    with pytest.raises(F09IntegrityError):
        artifacts.validate_run_artifact_manifest_v1(forged)


def test_existing_verified_run_manifest_is_returned_without_writing(tmp_path, monkeypatch):
    refs = (_ref("run-noop"),)
    projections = {"RUN_SNAPSHOT": b"run", "DECISION_RUN": b"decision"}
    roles = tuple(projections)
    payload_digests = {role: _digest(payload) for role, payload in projections.items()}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
        track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:noop",
        source_digest=_digest(b"source", KEY_CANONICALIZATION),
        schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
        contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
        input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
        projection_digest_by_role=payload_digests,
        canonical_key_digest=artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:noop",
            source_digest=_digest(b"source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    request = artifacts.RunArtifactSetRequestV1(key, key.run_id, refs, "f09.run-artifact.v1", projections)
    manifest = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=None, attempt_id="INITIAL", now=NOW
    )

    def fail_write(*_args, **_kwargs):
        raise AssertionError("verified run no-op must not write")

    monkeypatch.setattr(artifacts, "_atomic_write_verified", fail_write)
    assert artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=manifest, attempt_id="RETRY", now=NOW
    ) is manifest

    (artifacts._resolve_run_artifact_root_v1(tmp_path, key) / "run_snapshot.bin").unlink()
    with pytest.raises(F09IntegrityError):
        artifacts.coordinate_run_artifact_set_v1(
            tmp_path, request, existing_manifest=manifest, attempt_id="RETRY", now=NOW
        )


def test_reconcile_run_unknown_receipt_verifies_committed_final_without_writing(tmp_path, monkeypatch):
    refs = (_ref("run-unknown"),)
    projections = {"RUN_SNAPSHOT": b"run", "DECISION_RUN": b"decision"}
    roles = tuple(projections)
    payload_digests = {role: _digest(payload) for role, payload in projections.items()}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
        track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:unknown",
        source_digest=_digest(b"source", KEY_CANONICALIZATION),
        schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
        contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
        input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
        projection_digest_by_role=payload_digests,
        canonical_key_digest=artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:unknown",
            source_digest=_digest(b"source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    request = artifacts.RunArtifactSetRequestV1(key, key.run_id, refs, "f09.run-artifact.v1", projections)
    manifest = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=None, attempt_id="INITIAL", now=NOW
    )
    unknown_source = manifest.records[1]
    unknown_attempt = replace(unknown_source.attempts[0], outcome="UNKNOWN", finished_at=None, observed_digest=None)
    unknown_record = replace(
        unknown_source, state=ArtifactItemState.WRITTEN_UNVERIFIED,
        observed_digest=None, attempts=(unknown_attempt,),
    )
    unknown_records = (manifest.records[0], unknown_record)
    unknown_manifest = replace(
        manifest, records=unknown_records, state=ArtifactSetState.PARTIAL,
        digest=artifacts.digest_artifact_records(unknown_records),
        detected_issues=(DetectedIssue("RUN_ARTIFACT.WRITE_FAILED", "/records/DECISION_RUN"),),
    )

    def fail_write(*_args, **_kwargs):
        raise AssertionError("UNKNOWN reconciliation must only read back")

    monkeypatch.setattr(artifacts, "_atomic_write_verified", fail_write)
    reconciled = artifacts.reconcile_run_artifact_set_v1(tmp_path, request, unknown_manifest)

    assert reconciled.state is ArtifactSetState.COMPLETE_VERIFIED
    assert reconciled.records[0].attempts[0].outcome == "SUCCEEDED"
    assert artifacts.validate_run_artifact_manifest_v1(reconciled) == reconciled.digest


def test_reconcile_run_unknown_receipt_rejects_missing_final(tmp_path):
    refs = (_ref("run-unknown-missing"),)
    projections = {"RUN_SNAPSHOT": b"run", "DECISION_RUN": b"decision"}
    roles = tuple(projections)
    payload_digests = {role: _digest(payload) for role, payload in projections.items()}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        "PROJECT_RUN_ARTIFACT_SET", "CASE:F09:RUN", RunTrack.PRODUCTION_DEFAULT,
        "RUN:unknown-missing", _digest(b"source", KEY_CANONICALIZATION),
        _digest(b"schema", KEY_CANONICALIZATION), _digest(b"contract", KEY_CANONICALIZATION),
        refs_digest, roles, payload_digests,
        artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:unknown-missing",
            source_digest=_digest(b"source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    request = artifacts.RunArtifactSetRequestV1(key, key.run_id, refs, "f09.run-artifact.v1", projections)
    manifest = artifacts.coordinate_run_artifact_set_v1(tmp_path, request, existing_manifest=None, attempt_id="INITIAL", now=NOW)
    first = manifest.records[0]
    unknown = replace(first.attempts[0], outcome="UNKNOWN", finished_at=None, observed_digest=None)
    unknown_record = replace(first, state=ArtifactItemState.WRITTEN_UNVERIFIED, observed_digest=None, attempts=(unknown,))
    records = (unknown_record,) + manifest.records[1:]
    partial = replace(
        manifest, records=records, state=ArtifactSetState.PARTIAL,
        digest=artifacts.digest_artifact_records(records),
        detected_issues=(DetectedIssue("RUN_ARTIFACT.WRITE_FAILED", "/records/RUN_SNAPSHOT"),),
    )
    target = artifacts._resolve_run_artifact_root_v1(tmp_path, key) / "run_snapshot.bin"
    target.unlink()

    with pytest.raises(F09IntegrityError):
        artifacts.reconcile_run_artifact_set_v1(tmp_path, request, partial)


def test_coordinate_run_write_failure_returns_recoverable_failed_receipt(tmp_path, monkeypatch):
    refs = (_ref("run-failed-receipt"),)
    projections = {"RUN_SNAPSHOT": b"run", "DECISION_RUN": b"decision"}
    roles = tuple(projections)
    payload_digests = {role: _digest(payload) for role, payload in projections.items()}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        "PROJECT_RUN_ARTIFACT_SET", "CASE:F09:RUN", RunTrack.PRODUCTION_DEFAULT,
        "RUN:failed-receipt", _digest(b"source", KEY_CANONICALIZATION),
        _digest(b"schema", KEY_CANONICALIZATION), _digest(b"contract", KEY_CANONICALIZATION),
        refs_digest, roles, payload_digests,
        artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:failed-receipt",
            source_digest=_digest(b"source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    request = artifacts.RunArtifactSetRequestV1(
        key, key.run_id, refs, "f09.run-artifact.v1", projections
    )
    real_write = artifacts._atomic_write_verified
    calls: list[Path] = []

    def fail_second_write(target, payload):
        calls.append(target)
        if len(calls) == 2:
            raise OSError("simulated write failure")
        return real_write(target, payload)

    monkeypatch.setattr(artifacts, "_atomic_write_verified", fail_second_write)
    manifest = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=None, attempt_id="INITIAL", now=NOW
    )

    assert len(calls) == 2
    assert manifest.state is ArtifactSetState.PARTIAL
    assert tuple(record.artifact_role for record in manifest.records) == roles
    assert manifest.records[0].state is ArtifactItemState.VERIFIED
    failed = manifest.records[1]
    assert failed.state is ArtifactItemState.FAILED
    assert failed.observed_digest is None
    assert failed.attempts[0].outcome == "FAILED"
    assert failed.attempts[0].idempotency_key == key.canonical_key_digest.value
    assert failed.attempts[0].artifact_id == failed.artifact_id
    assert failed.attempts[0].error_class == "OSError"


def test_coordinate_run_retries_failed_receipt_without_rewriting_verified_role(tmp_path, monkeypatch):
    refs = (_ref("run-retry-receipt"),)
    projections = {"RUN_SNAPSHOT": b"run", "DECISION_RUN": b"decision"}
    roles = tuple(projections)
    payload_digests = {role: _digest(payload) for role, payload in projections.items()}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        "PROJECT_RUN_ARTIFACT_SET", "CASE:F09:RUN", RunTrack.PRODUCTION_DEFAULT,
        "RUN:retry-receipt", _digest(b"source", KEY_CANONICALIZATION),
        _digest(b"schema", KEY_CANONICALIZATION), _digest(b"contract", KEY_CANONICALIZATION),
        refs_digest, roles, payload_digests,
        artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:retry-receipt",
            source_digest=_digest(b"source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    request = artifacts.RunArtifactSetRequestV1(
        key, key.run_id, refs, "f09.run-artifact.v1", projections
    )
    real_write = artifacts._atomic_write_verified
    calls: list[Path] = []

    def fail_once(target, payload):
        calls.append(target)
        if len(calls) == 2:
            raise OSError("simulated write failure")
        return real_write(target, payload)

    monkeypatch.setattr(artifacts, "_atomic_write_verified", fail_once)
    failed = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=None, attempt_id="INITIAL", now=NOW
    )
    retained_target = artifacts._resolve_run_artifact_root_v1(tmp_path, key) / "run_snapshot.bin"
    retained_target.unlink()
    with pytest.raises(F09IntegrityError):
        artifacts.coordinate_run_artifact_set_v1(
            tmp_path, request, existing_manifest=failed, attempt_id="RETRY", now="2026-01-01T00:00:01Z"
        )
    retained_target.write_bytes(projections["RUN_SNAPSHOT"])
    retried = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=failed, attempt_id="RETRY", now="2026-01-01T00:00:01Z"
    )

    assert len(calls) == 3
    assert retried.state is ArtifactSetState.COMPLETE_VERIFIED
    assert len(retried.records[0].attempts) == 1
    assert retried.records[1].attempts[-1].attempt_number == 2
    assert retried.records[1].attempts[-1].retry_of_attempt_id == "INITIAL:DECISION_RUN"
    assert artifacts.validate_run_artifact_manifest_v1(retried) == retried.digest


def test_coordinate_run_post_commit_failure_returns_unknown_receipt(tmp_path, monkeypatch):
    refs = (_ref("run-unknown-receipt"),)
    projections = {"RUN_SNAPSHOT": b"run", "DECISION_RUN": b"decision"}
    roles = tuple(projections)
    payload_digests = {role: _digest(payload) for role, payload in projections.items()}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        "PROJECT_RUN_ARTIFACT_SET", "CASE:F09:RUN", RunTrack.PRODUCTION_DEFAULT,
        "RUN:unknown-receipt", _digest(b"source", KEY_CANONICALIZATION),
        _digest(b"schema", KEY_CANONICALIZATION), _digest(b"contract", KEY_CANONICALIZATION),
        refs_digest, roles, payload_digests,
        artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:unknown-receipt",
            source_digest=_digest(b"source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    request = artifacts.RunArtifactSetRequestV1(
        key, key.run_id, refs, "f09.run-artifact.v1", projections
    )
    real_write = artifacts._atomic_write_verified

    def commit_then_fail(target, payload):
        real_write(target, payload)
        raise OSError("simulated post-commit uncertainty")

    monkeypatch.setattr(artifacts, "_atomic_write_verified", commit_then_fail)
    manifest = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=None, attempt_id="INITIAL", now=NOW
    )

    assert manifest.state is ArtifactSetState.PARTIAL
    unknown = manifest.records[0]
    assert unknown.state is ArtifactItemState.WRITTEN_UNVERIFIED
    assert unknown.attempts[0].outcome == "UNKNOWN"
    assert unknown.attempts[0].finished_at is None
    assert unknown.attempts[0].observed_digest is None


def test_coordinate_run_reconciles_unknown_final_before_retrying(tmp_path, monkeypatch):
    refs = (_ref("run-unknown-coordinate"),)
    projections = {"RUN_SNAPSHOT": b"run", "DECISION_RUN": b"decision"}
    roles = tuple(projections)
    payload_digests = {role: _digest(payload) for role, payload in projections.items()}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        "PROJECT_RUN_ARTIFACT_SET", "CASE:F09:RUN", RunTrack.PRODUCTION_DEFAULT,
        "RUN:unknown-coordinate", _digest(b"source", KEY_CANONICALIZATION),
        _digest(b"schema", KEY_CANONICALIZATION), _digest(b"contract", KEY_CANONICALIZATION),
        refs_digest, roles, payload_digests,
        artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:unknown-coordinate",
            source_digest=_digest(b"source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    request = artifacts.RunArtifactSetRequestV1(
        key, key.run_id, refs, "f09.run-artifact.v1", projections
    )
    real_write = artifacts._atomic_write_verified

    def commit_then_fail(target, payload):
        real_write(target, payload)
        raise OSError("simulated post-commit uncertainty")

    monkeypatch.setattr(artifacts, "_atomic_write_verified", commit_then_fail)
    partial = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=None, attempt_id="INITIAL", now=NOW
    )

    writes: list[Path] = []

    def allow_only_missing_role(target, payload):
        writes.append(target)
        assert target.name == "decision_run.bin"
        return real_write(target, payload)

    monkeypatch.setattr(artifacts, "_atomic_write_verified", allow_only_missing_role)
    reconciled = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=partial, attempt_id="RETRY", now="2026-01-01T00:00:01Z"
    )

    assert writes and len(writes) == 1
    assert reconciled.state is ArtifactSetState.COMPLETE_VERIFIED
    assert reconciled.records[0].attempts[0].outcome == "SUCCEEDED"
    assert len(reconciled.records[0].attempts) == 1


def test_reconcile_run_rejects_forged_unknown_receipt_before_filesystem_read(tmp_path, monkeypatch):
    refs = (_ref("run-forged-unknown"),)
    projections = {"RUN_SNAPSHOT": b"run", "DECISION_RUN": b"decision"}
    roles = tuple(projections)
    payload_digests = {role: _digest(payload) for role, payload in projections.items()}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        "PROJECT_RUN_ARTIFACT_SET", "CASE:F09:RUN", RunTrack.PRODUCTION_DEFAULT,
        "RUN:forged-unknown", _digest(b"source", KEY_CANONICALIZATION),
        _digest(b"schema", KEY_CANONICALIZATION), _digest(b"contract", KEY_CANONICALIZATION),
        refs_digest, roles, payload_digests,
        artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:forged-unknown",
            source_digest=_digest(b"source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    request = artifacts.RunArtifactSetRequestV1(key, key.run_id, refs, "f09.run-artifact.v1", projections)
    complete = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=None, attempt_id="INITIAL", now=NOW
    )
    first = complete.records[0]
    unknown_attempt = replace(first.attempts[0], outcome="UNKNOWN", finished_at=None, observed_digest=None)
    forged_record = replace(
        first, artifact_id="FORGED", state=ArtifactItemState.WRITTEN_UNVERIFIED,
        observed_digest=None, attempts=(unknown_attempt,),
    )
    records = (forged_record,) + complete.records[1:]
    partial = replace(
        complete, records=records, state=ArtifactSetState.PARTIAL,
        digest=artifacts.digest_artifact_records(records),
    )

    def fail_filesystem(*_args, **_kwargs):
        raise AssertionError("malformed receipt must fail before filesystem access")

    monkeypatch.setattr(artifacts, "_resolve_run_artifact_root_v1", fail_filesystem)
    with pytest.raises(F09IntegrityError):
        artifacts.reconcile_run_artifact_set_v1(tmp_path, request, partial)


def test_coordinate_run_mkdir_failure_returns_recoverable_failed_receipt(tmp_path, monkeypatch):
    refs = (_ref("run-mkdir-failure"),)
    projections = {"RUN_SNAPSHOT": b"run", "DECISION_RUN": b"decision"}
    roles = tuple(projections)
    payload_digests = {role: _digest(payload) for role, payload in projections.items()}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        "PROJECT_RUN_ARTIFACT_SET", "CASE:F09:RUN", RunTrack.PRODUCTION_DEFAULT,
        "RUN:mkdir-failure", _digest(b"source", KEY_CANONICALIZATION),
        _digest(b"schema", KEY_CANONICALIZATION), _digest(b"contract", KEY_CANONICALIZATION),
        refs_digest, roles, payload_digests,
        artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:mkdir-failure",
            source_digest=_digest(b"source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    request = artifacts.RunArtifactSetRequestV1(key, key.run_id, refs, "f09.run-artifact.v1", projections)

    real_mkdir = Path.mkdir

    def fail_mkdir(self, *args, **kwargs):
        raise OSError("simulated directory failure")

    monkeypatch.setattr(Path, "mkdir", fail_mkdir)
    manifest = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=None, attempt_id="INITIAL", now=NOW
    )

    assert manifest.state is ArtifactSetState.PARTIAL
    assert len(manifest.records) == 1
    failed = manifest.records[0]
    assert failed.artifact_role == "RUN_SNAPSHOT"
    assert failed.state is ArtifactItemState.FAILED
    assert failed.attempts[0].outcome == "FAILED"
    assert failed.attempts[0].error_class == "OSError"

    monkeypatch.setattr(Path, "mkdir", real_mkdir)
    retried = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=manifest, attempt_id="RETRY", now="2026-01-01T00:00:01Z"
    )

    assert retried.state is ArtifactSetState.COMPLETE_VERIFIED
    assert retried.records[0].attempts[-1].attempt_number == 2
    assert retried.records[0].attempts[-1].retry_of_attempt_id == "INITIAL:RUN_SNAPSHOT"


def test_coordinate_run_write_failure_with_unreadable_final_returns_unknown_receipt(tmp_path, monkeypatch):
    refs = (_ref("run-unreadable-final"),)
    projections = {"RUN_SNAPSHOT": b"run", "DECISION_RUN": b"decision"}
    roles = tuple(projections)
    payload_digests = {role: _digest(payload) for role, payload in projections.items()}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        "PROJECT_RUN_ARTIFACT_SET", "CASE:F09:RUN", RunTrack.PRODUCTION_DEFAULT,
        "RUN:unreadable-final", _digest(b"source", KEY_CANONICALIZATION),
        _digest(b"schema", KEY_CANONICALIZATION), _digest(b"contract", KEY_CANONICALIZATION),
        refs_digest, roles, payload_digests,
        artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:unreadable-final",
            source_digest=_digest(b"source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    request = artifacts.RunArtifactSetRequestV1(key, key.run_id, refs, "f09.run-artifact.v1", projections)

    def fail_write(*_args, **_kwargs):
        raise OSError("simulated write failure")

    def unreadable_final(_target, _expected):
        raise OSError("simulated readback failure")

    monkeypatch.setattr(artifacts, "_atomic_write_verified", fail_write)
    monkeypatch.setattr(artifacts, "_run_final_matches_expected_v1", unreadable_final)
    manifest = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=None, attempt_id="INITIAL", now=NOW
    )

    assert manifest.state is ArtifactSetState.PARTIAL
    assert manifest.records[0].state is ArtifactItemState.WRITTEN_UNVERIFIED
    assert manifest.records[0].attempts[0].outcome == "UNKNOWN"


def test_coordinate_run_rejects_forged_partial_before_filesystem_resolve(tmp_path, monkeypatch):
    refs = (_ref("run-forged-coordinate"),)
    projections = {"RUN_SNAPSHOT": b"run", "DECISION_RUN": b"decision"}
    roles = tuple(projections)
    payload_digests = {role: _digest(payload) for role, payload in projections.items()}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        "PROJECT_RUN_ARTIFACT_SET", "CASE:F09:RUN", RunTrack.PRODUCTION_DEFAULT,
        "RUN:forged-coordinate", _digest(b"source", KEY_CANONICALIZATION),
        _digest(b"schema", KEY_CANONICALIZATION), _digest(b"contract", KEY_CANONICALIZATION),
        refs_digest, roles, payload_digests,
        artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:forged-coordinate",
            source_digest=_digest(b"source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    request = artifacts.RunArtifactSetRequestV1(key, key.run_id, refs, "f09.run-artifact.v1", projections)
    complete = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=None, attempt_id="INITIAL", now=NOW
    )
    forged = replace(complete.records[0], artifact_id="FORGED")
    records = (forged,) + complete.records[1:]
    partial = replace(
        complete, records=records, state=ArtifactSetState.PARTIAL,
        digest=artifacts.digest_artifact_records(records),
    )

    def fail_resolve(*_args, **_kwargs):
        raise AssertionError("malformed partial receipt must fail before resolver")

    monkeypatch.setattr(artifacts, "_resolve_run_artifact_root_v1", fail_resolve)
    with pytest.raises(F09IntegrityError):
        artifacts.coordinate_run_artifact_set_v1(
            tmp_path, request, existing_manifest=partial, attempt_id="RETRY", now="2026-01-01T00:00:01Z"
        )


def test_coordinate_run_rejects_forged_verified_receipt_before_filesystem_resolve(tmp_path, monkeypatch):
    refs = (_ref("run-forged-verified"),)
    projections = {"RUN_SNAPSHOT": b"run", "DECISION_RUN": b"decision"}
    roles = tuple(projections)
    payload_digests = {role: _digest(payload) for role, payload in projections.items()}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        "PROJECT_RUN_ARTIFACT_SET", "CASE:F09:RUN", RunTrack.PRODUCTION_DEFAULT,
        "RUN:forged-verified", _digest(b"source", KEY_CANONICALIZATION),
        _digest(b"schema", KEY_CANONICALIZATION), _digest(b"contract", KEY_CANONICALIZATION),
        refs_digest, roles, payload_digests,
        artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:forged-verified",
            source_digest=_digest(b"source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    request = artifacts.RunArtifactSetRequestV1(key, key.run_id, refs, "f09.run-artifact.v1", projections)
    complete = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=None, attempt_id="INITIAL", now=NOW
    )
    verified = replace(
        complete.records[0], observed_digest=None,
        attempts=(replace(complete.records[0].attempts[0], observed_digest=None),),
    )
    failed_attempt = replace(
        complete.records[1].attempts[0], outcome="FAILED", observed_digest=None,
        error_class="OSError", error_message_digest=_digest(b"failure"),
    )
    failed = replace(
        complete.records[1], observed_digest=None, state=ArtifactItemState.FAILED,
        attempts=(failed_attempt,),
    )
    records = (verified, failed)
    partial = replace(
        complete, records=records, state=ArtifactSetState.PARTIAL,
        digest=artifacts.digest_artifact_records(records),
        detected_issues=(DetectedIssue("RUN_ARTIFACT.WRITE_FAILED", "/records/DECISION_RUN"),),
    )

    def fail_resolve(*_args, **_kwargs):
        raise AssertionError("forged verified receipt must fail before resolver")

    monkeypatch.setattr(artifacts, "_resolve_run_artifact_root_v1", fail_resolve)
    with pytest.raises(F09IntegrityError):
        artifacts.coordinate_run_artifact_set_v1(
            tmp_path, request, existing_manifest=partial, attempt_id="RETRY", now="2026-01-01T00:00:01Z"
        )


@pytest.mark.parametrize("mutation", ["digest", "non_prefix"])
def test_coordinate_run_rejects_noncanonical_partial_before_filesystem_resolve(tmp_path, monkeypatch, mutation):
    refs = (_ref(f"run-noncanonical-partial-{mutation}"),)
    projections = {
        "RUN_SNAPSHOT": b"run",
        "DECISION_RUN": b"decision",
        "FEEDBACK_ATTACHMENT": b"feedback",
    }
    roles = tuple(projections)
    payload_digests = {role: _digest(payload) for role, payload in projections.items()}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        "PROJECT_RUN_ARTIFACT_SET", "CASE:F09:RUN", RunTrack.PRODUCTION_DEFAULT,
        f"RUN:noncanonical-partial-{mutation}", _digest(b"source", KEY_CANONICALIZATION),
        _digest(b"schema", KEY_CANONICALIZATION), _digest(b"contract", KEY_CANONICALIZATION),
        refs_digest, roles, payload_digests,
        artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id=f"RUN:noncanonical-partial-{mutation}",
            source_digest=_digest(b"source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    request = artifacts.RunArtifactSetRequestV1(key, key.run_id, refs, "f09.run-artifact.v1", projections)
    complete = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=None, attempt_id="INITIAL", now=NOW
    )
    failed_attempt = replace(
        complete.records[1].attempts[0], outcome="FAILED", observed_digest=None,
        error_class="OSError", error_message_digest=_digest(b"failure"),
    )
    failed = replace(
        complete.records[1], observed_digest=None, state=ArtifactItemState.FAILED,
        attempts=(failed_attempt,),
    )
    if mutation == "digest":
        partial = replace(
            complete, records=(complete.records[0], failed), state=ArtifactSetState.PARTIAL,
            digest=_digest(b"forged-partial-digest"),
            detected_issues=(DetectedIssue("RUN_ARTIFACT.WRITE_FAILED", "/records/DECISION_RUN"),),
        )
    else:
        partial_records = (complete.records[0], failed, complete.records[2])
        partial = replace(
            complete, records=partial_records, state=ArtifactSetState.PARTIAL,
            digest=artifacts.digest_artifact_records(partial_records),
            detected_issues=(DetectedIssue("RUN_ARTIFACT.WRITE_FAILED", "/records/DECISION_RUN"),),
        )

    def fail_resolve(*_args, **_kwargs):
        raise AssertionError("noncanonical partial must fail before resolver")

    monkeypatch.setattr(artifacts, "_resolve_run_artifact_root_v1", fail_resolve)
    with pytest.raises(F09IntegrityError):
        artifacts.coordinate_run_artifact_set_v1(
            tmp_path, request, existing_manifest=partial, attempt_id="RETRY", now="2026-01-01T00:00:01Z"
        )


def test_run_public_verifier_rejects_blank_record_schema_version(tmp_path):
    refs = (_ref("run-schema-version"),)
    projections = {"RUN_SNAPSHOT": b"run", "DECISION_RUN": b"decision"}
    roles = tuple(projections)
    payload_digests = {role: _digest(payload) for role, payload in projections.items()}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        "PROJECT_RUN_ARTIFACT_SET", "CASE:F09:RUN", RunTrack.PRODUCTION_DEFAULT,
        "RUN:schema-version", _digest(b"source", KEY_CANONICALIZATION),
        _digest(b"schema", KEY_CANONICALIZATION), _digest(b"contract", KEY_CANONICALIZATION),
        refs_digest, roles, payload_digests,
        artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:schema-version",
            source_digest=_digest(b"source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    request = artifacts.RunArtifactSetRequestV1(key, key.run_id, refs, "f09.run-artifact.v1", projections)
    complete = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=None, attempt_id="INITIAL", now=NOW
    )
    records = (replace(complete.records[0], schema_version=""),) + complete.records[1:]
    forged = replace(complete, records=records, digest=artifacts.digest_artifact_records(records))

    with pytest.raises(F09IntegrityError):
        artifacts.validate_run_artifact_manifest_v1(forged)


def test_coordinate_run_rejects_existing_complete_with_different_request_schema_before_reuse(tmp_path, monkeypatch):
    refs = (_ref("run-schema-reuse"),)
    projections = {"RUN_SNAPSHOT": b"run", "DECISION_RUN": b"decision"}
    roles = tuple(projections)
    payload_digests = {role: _digest(payload) for role, payload in projections.items()}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        "PROJECT_RUN_ARTIFACT_SET", "CASE:F09:RUN", RunTrack.PRODUCTION_DEFAULT,
        "RUN:schema-reuse", _digest(b"source", KEY_CANONICALIZATION),
        _digest(b"schema", KEY_CANONICALIZATION), _digest(b"contract", KEY_CANONICALIZATION),
        refs_digest, roles, payload_digests,
        artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:schema-reuse",
            source_digest=_digest(b"source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    v1 = artifacts.RunArtifactSetRequestV1(key, key.run_id, refs, "f09.run-artifact.v1", projections)
    complete = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, v1, existing_manifest=None, attempt_id="INITIAL", now=NOW
    )
    v2 = artifacts.RunArtifactSetRequestV1(key, key.run_id, refs, "f09.run-artifact.v2", projections)

    with pytest.raises(F09IntegrityError):
        artifacts.coordinate_run_artifact_set_v1(
            tmp_path, v2, existing_manifest=complete, attempt_id="RETRY", now="2026-01-01T00:00:01Z"
        )

    malformed = replace(complete, records=(object(),))

    def fail_resolve(*_args, **_kwargs):
        raise AssertionError("malformed complete receipt must fail before resolver")

    monkeypatch.setattr(artifacts, "_resolve_run_artifact_root_v1", fail_resolve)
    with pytest.raises(F09IntegrityError):
        artifacts.coordinate_run_artifact_set_v1(
            tmp_path, v1, existing_manifest=malformed, attempt_id="RETRY", now="2026-01-01T00:00:01Z"
        )


def test_run_root_resolver_rejects_symlinked_namespace_escape(tmp_path):
    refs = (_ref("run-root-escape"),)
    roles = ("RUN_SNAPSHOT", "DECISION_RUN")
    payload_digests = {role: _digest(role.encode("utf-8")) for role in roles}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        "PROJECT_RUN_ARTIFACT_SET", "CASE:F09:RUN", RunTrack.PRODUCTION_DEFAULT,
        "RUN:root-escape", _digest(b"source", KEY_CANONICALIZATION),
        _digest(b"schema", KEY_CANONICALIZATION), _digest(b"contract", KEY_CANONICALIZATION),
        refs_digest, roles, payload_digests,
        artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id="RUN:root-escape",
            source_digest=_digest(b"source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    external = tmp_path.parent / f"{tmp_path.name}-external"
    external.mkdir()
    namespace = tmp_path / "run-artifacts"
    try:
        namespace.symlink_to(external, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")

    with pytest.raises(F09IntegrityError):
        artifacts._resolve_run_artifact_root_v1(tmp_path, key)


@pytest.mark.parametrize("mutation", ["manifest_id", "path_locator", "external_suffix_locator", "record_issue_ids"])
def test_run_public_verifier_rejects_forged_manifest_identity_fields(tmp_path, mutation):
    refs = (_ref(f"run-forged-{mutation}"),)
    projections = {"RUN_SNAPSHOT": b"run", "DECISION_RUN": b"decision"}
    roles = tuple(projections)
    payload_digests = {role: _digest(payload) for role, payload in projections.items()}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        "PROJECT_RUN_ARTIFACT_SET", "CASE:F09:RUN", RunTrack.PRODUCTION_DEFAULT,
        f"RUN:forged-{mutation}", _digest(b"source", KEY_CANONICALIZATION),
        _digest(b"schema", KEY_CANONICALIZATION), _digest(b"contract", KEY_CANONICALIZATION),
        refs_digest, roles, payload_digests,
        artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id=f"RUN:forged-{mutation}",
            source_digest=_digest(b"source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    request = artifacts.RunArtifactSetRequestV1(key, key.run_id, refs, "f09.run-artifact.v1", projections)
    complete = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=None, attempt_id="INITIAL", now=NOW
    )
    if mutation == "manifest_id":
        forged = replace(complete, manifest_id="FORGED")
    elif mutation == "record_issue_ids":
        records = (replace(complete.records[0], issue_ids=("FORGED",)),) + complete.records[1:]
        forged = replace(complete, records=records, digest=artifacts.digest_artifact_records(records))
    else:
        locator = "external/forged.bin"
        if mutation == "external_suffix_locator":
            locator = (
                tmp_path.parent / "external" / "run-artifacts" /
                key.canonical_key_digest.value / "run_snapshot.bin"
            ).as_posix()
        records = (replace(complete.records[0], path_locator=locator),) + complete.records[1:]
        forged = replace(complete, records=records, digest=artifacts.digest_artifact_records(records))

    with pytest.raises(F09IntegrityError):
        artifacts.validate_run_artifact_manifest_v1(forged)


@pytest.mark.parametrize(
    "mutation",
    ["manifest_id", "external_suffix_locator", "record_issue_ids", "detected_issues", "successful_prefix"],
)
@pytest.mark.parametrize("entrypoint", ["coordinate", "reconcile"])
def test_run_partial_receipt_identity_mutations_fail_before_filesystem_resolve(
    tmp_path, monkeypatch, mutation, entrypoint
):
    refs = (_ref(f"run-partial-identity-{entrypoint}-{mutation}"),)
    projections = {"RUN_SNAPSHOT": b"run", "DECISION_RUN": b"decision"}
    roles = tuple(projections)
    payload_digests = {role: _digest(payload) for role, payload in projections.items()}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        "PROJECT_RUN_ARTIFACT_SET", "CASE:F09:RUN", RunTrack.PRODUCTION_DEFAULT,
        f"RUN:partial-identity-{entrypoint}-{mutation}", _digest(b"source", KEY_CANONICALIZATION),
        _digest(b"schema", KEY_CANONICALIZATION), _digest(b"contract", KEY_CANONICALIZATION),
        refs_digest, roles, payload_digests,
        artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id=f"RUN:partial-identity-{entrypoint}-{mutation}",
            source_digest=_digest(b"source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    request = artifacts.RunArtifactSetRequestV1(key, key.run_id, refs, "f09.run-artifact.v1", projections)
    complete = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=None, attempt_id="INITIAL", now=NOW
    )
    failed_attempt = replace(
        complete.records[1].attempts[0], outcome="FAILED", observed_digest=None,
        error_class="OSError", error_message_digest=_digest(b"failure"),
    )
    records = (
        complete.records[0],
        replace(complete.records[1], observed_digest=None, state=ArtifactItemState.FAILED, attempts=(failed_attempt,)),
    )
    partial = replace(
        complete, records=records, state=ArtifactSetState.PARTIAL,
        digest=artifacts.digest_artifact_records(records),
        detected_issues=(DetectedIssue("RUN_ARTIFACT.WRITE_FAILED", "/records/DECISION_RUN"),),
    )
    if mutation == "manifest_id":
        partial = replace(partial, manifest_id="FORGED")
    elif mutation in ("detected_issues", "successful_prefix"):
        partial = replace(partial, detected_issues=())
        if mutation == "successful_prefix":
            records = (complete.records[0],)
            partial = replace(
                partial, records=records, digest=artifacts.digest_artifact_records(records),
            )
    elif mutation == "record_issue_ids":
        records = (replace(partial.records[0], issue_ids=("FORGED",)), partial.records[1])
        partial = replace(partial, records=records, digest=artifacts.digest_artifact_records(records))
    else:
        forged_locator = (
            tmp_path.parent / "external" / "run-artifacts" /
            key.canonical_key_digest.value / "run_snapshot.bin"
        ).as_posix()
        records = (replace(partial.records[0], path_locator=forged_locator), partial.records[1])
        partial = replace(partial, records=records, digest=artifacts.digest_artifact_records(records))

    def fail_resolve(*_args, **_kwargs):
        raise AssertionError("forged partial receipt must fail before resolver")

    monkeypatch.setattr(artifacts, "_resolve_run_artifact_root_v1", fail_resolve)
    with pytest.raises(F09IntegrityError):
        if entrypoint == "coordinate":
            artifacts.coordinate_run_artifact_set_v1(
                tmp_path, request, existing_manifest=partial, attempt_id="RETRY", now="2026-01-01T00:00:01Z"
            )
        else:
            artifacts.reconcile_run_artifact_set_v1(tmp_path, request, partial)


@pytest.mark.parametrize("entrypoint", ["inspect", "reconcile_unknown"])
def test_run_readback_oserror_is_typed_integrity_failure(tmp_path, monkeypatch, entrypoint):
    refs = (_ref(f"run-readback-oserror-{entrypoint}"),)
    projections = {"RUN_SNAPSHOT": b"run", "DECISION_RUN": b"decision"}
    roles = tuple(projections)
    payload_digests = {role: _digest(payload) for role, payload in projections.items()}
    refs_digest = artifacts._digest_run_input_snapshot_refs_v1(refs)
    key = artifacts.RunArtifactSetKeyV1(
        "PROJECT_RUN_ARTIFACT_SET", "CASE:F09:RUN", RunTrack.PRODUCTION_DEFAULT,
        f"RUN:readback-oserror-{entrypoint}", _digest(b"source", KEY_CANONICALIZATION),
        _digest(b"schema", KEY_CANONICALIZATION), _digest(b"contract", KEY_CANONICALIZATION),
        refs_digest, roles, payload_digests,
        artifacts._digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET", case_id="CASE:F09:RUN",
            track=RunTrack.PRODUCTION_DEFAULT, run_id=f"RUN:readback-oserror-{entrypoint}",
            source_digest=_digest(b"source", KEY_CANONICALIZATION),
            schema_versions_digest=_digest(b"schema", KEY_CANONICALIZATION),
            contract_digest=_digest(b"contract", KEY_CANONICALIZATION),
            input_snapshot_refs_graph_digest=refs_digest, projection_roles=roles,
            projection_digest_by_role=payload_digests,
        ),
    )
    request = artifacts.RunArtifactSetRequestV1(key, key.run_id, refs, "f09.run-artifact.v1", projections)
    complete = artifacts.coordinate_run_artifact_set_v1(
        tmp_path, request, existing_manifest=None, attempt_id="INITIAL", now=NOW
    )
    manifest = complete
    if entrypoint == "reconcile_unknown":
        unknown_attempt = replace(
            complete.records[1].attempts[0], outcome="UNKNOWN", finished_at=None, observed_digest=None,
        )
        unknown_record = replace(
            complete.records[1], state=ArtifactItemState.WRITTEN_UNVERIFIED,
            observed_digest=None, attempts=(unknown_attempt,),
        )
        records = (complete.records[0], unknown_record)
        manifest = replace(
            complete, records=records, state=ArtifactSetState.PARTIAL,
            digest=artifacts.digest_artifact_records(records),
            detected_issues=(DetectedIssue("RUN_ARTIFACT.WRITE_FAILED", "/records/DECISION_RUN"),),
        )

    def fail_read_bytes(_self):
        raise OSError("simulated readback failure")

    monkeypatch.setattr(Path, "read_bytes", fail_read_bytes)
    with pytest.raises(F09IntegrityError) as caught:
        if entrypoint == "inspect":
            artifacts.inspect_run_artifact_set_v1(tmp_path, manifest)
        else:
            artifacts.reconcile_run_artifact_set_v1(tmp_path, request, manifest)

    assert caught.value.issue_code == "RUN_ARTIFACT.READBACK_MISMATCH"


def test_r41_public_issuance_surface_is_defined_and_registry_fails_closed_before_provisioning():
    expected = {
        "RunArtifactTargetRefsRequestV1": (
            "run_snapshot_ref", "decision_run_ref", "feedback_attachment_ref",
        ),
        "ManifestOuterRefRequestV1": (
            "revision_id", "schema_version", "contract_version", "source_locator_id", "captured_at",
        ),
        "RunArtifactSetPublicKeyV1": ("key_id", "public_key_b64url", "status"),
        "RunArtifactSetPublicKeyRegistryV1": ("registry_version", "keys_by_id"),
        "IssuedRunArtifactSetProofV1": ("algorithm", "key_id", "signature_b64url"),
        "RunArtifactSetResultV1": ("manifest", "target_refs", "issuance_proof"),
    }
    for name, field_names in expected.items():
        value = getattr(artifacts, name)
        assert is_dataclass(value)
        assert tuple(field.name for field in fields(value)) == field_names

    for name in (
        "coordinate_run_artifact_set_with_target_refs_v1",
        "get_run_artifact_set_public_key_registry_v1",
        "canonicalize_run_artifact_set_issuance_payload_v1",
        "validate_run_artifact_set_result_issuance_v1",
    ):
        assert callable(getattr(artifacts, name))

    with pytest.raises(F09ContractError) as caught:
        artifacts.get_run_artifact_set_public_key_registry_v1()
    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_UNAVAILABLE"
    assert caught.value.field_path == "issuance_proof"


def test_r41_issuance_payload_serializes_verified_four_ref_closure():
    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    captured_at = "2026-07-24T00:00:00Z"
    capture_refs = tuple(
        VersionedObjectRef(
            object_type=record.artifact_role,
            object_id=record.artifact_id,
            revision_id=None,
            schema_version=record.schema_version,
            contract_version=None,
            digest_binding=DigestPresent("PRESENT", record.observed_digest),
            source_locator_id=None,
            captured_at=captured_at,
        )
        for record in manifest.records
    )
    records_digest = artifacts.validate_run_artifact_manifest_v1(manifest)
    target_refs = capture_refs + (
        VersionedObjectRef(
            object_type="MANIFEST",
            object_id=manifest.manifest_id,
            revision_id=None,
            schema_version="f09.run-manifest.v1",
            contract_version=None,
            digest_binding=DigestPresent("PRESENT", records_digest),
            source_locator_id=None,
            captured_at=captured_at,
        ),
    )

    payload = artifacts.canonicalize_run_artifact_set_issuance_payload_v1(manifest, target_refs)

    assert payload == canonicalize_bounded_jcs(parse_bounded_jcs(payload))
    assert parse_bounded_jcs(payload)["domain"] == "f09.run-artifact-set.issuance.v1"


def test_r41_public_verifier_accepts_actual_ed25519_proof(monkeypatch):
    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    captured_at = "2026-07-24T00:00:00Z"
    capture_refs = tuple(
        VersionedObjectRef(
            record.artifact_role, record.artifact_id, None, record.schema_version, None,
            DigestPresent("PRESENT", record.observed_digest), None, captured_at,
        )
        for record in manifest.records
    )
    records_digest = artifacts.validate_run_artifact_manifest_v1(manifest)
    target_refs = capture_refs + (
        VersionedObjectRef(
            "MANIFEST", manifest.manifest_id, None, "f09.run-manifest.v1", None,
            DigestPresent("PRESENT", records_digest), None, captured_at,
        ),
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw,
        )
    ).rstrip(b"=").decode("ascii")
    registry = artifacts.RunArtifactSetPublicKeyRegistryV1(
        "registry.v1",
        MappingProxyType({"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "ACTIVE")}),
    )
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1", registry)
    payload = artifacts.canonicalize_run_artifact_set_issuance_payload_v1(manifest, target_refs)
    proof = artifacts.IssuedRunArtifactSetProofV1(
        "Ed25519", "key-1", base64.urlsafe_b64encode(private_key.sign(payload)).rstrip(b"=").decode("ascii"),
    )

    artifacts.validate_run_artifact_set_result_issuance_v1(
        artifacts.RunArtifactSetResultV1(manifest, target_refs, proof)
    )


def test_r41_versioned_coordinator_returns_actual_manifest_bound_signed_result(tmp_path, monkeypatch):
    fixture = artifacts.provision_verified_run_manifest_fixture_v1()
    key = fixture.key
    projections = {
        "RUN_SNAPSHOT": b"f09.run-fixture.run-snapshot.v1",
        "DECISION_RUN": b"f09.run-fixture.decision-run.v1",
        "FEEDBACK_ATTACHMENT": b"f09.run-fixture.feedback-attachment.v1",
    }
    request = artifacts.RunArtifactSetRequestV1(
        key, key.run_id, fixture.records[0].attempts[0].input_snapshot_refs,
        "f09.run-artifact-fixture.v1", projections,
    )
    captured_at = "2026-07-24T00:00:00Z"
    refs = tuple(
        VersionedObjectRef(
            role, f"RUN-ARTIFACT:{key.canonical_key_digest.value}:{role}", None,
            "f09.run-artifact-fixture.v1", None,
            DigestPresent("PRESENT", key.projection_digest_by_role[role]), None, captured_at,
        )
        for role in key.projection_roles
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    registry = artifacts.RunArtifactSetPublicKeyRegistryV1(
        "registry.v1",
        MappingProxyType({"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "ACTIVE")}),
    )
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1", registry)
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_SIGNER_PORT_V1", ("key-1", private_key.sign))

    result = artifacts.coordinate_run_artifact_set_with_target_refs_v1(
        tmp_path, request,
        target_refs_request=artifacts.RunArtifactTargetRefsRequestV1(*refs),
        manifest_outer_ref_request=artifacts.ManifestOuterRefRequestV1(
            None, "f09.run-manifest.v1", None, None, captured_at,
        ),
        existing_manifest=None,
        attempt_id="R41-ATTEMPT",
        now=NOW,
    )

    assert result.manifest.key == key
    assert result.target_refs[:3] == refs
    artifacts.validate_run_artifact_set_result_issuance_v1(result)


def test_r41_versioned_coordinator_calls_manifest_verifier_once(tmp_path, monkeypatch):
    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    key = manifest.key
    request = artifacts.RunArtifactSetRequestV1(
        key,
        key.run_id,
        manifest.records[0].attempts[0].input_snapshot_refs,
        "f09.run-artifact-fixture.v1",
        {
            "RUN_SNAPSHOT": b"f09.run-fixture.run-snapshot.v1",
            "DECISION_RUN": b"f09.run-fixture.decision-run.v1",
            "FEEDBACK_ATTACHMENT": b"f09.run-fixture.feedback-attachment.v1",
        },
    )
    captured_at = "2026-07-24T00:00:00Z"
    refs = tuple(
        VersionedObjectRef(
            record.artifact_role,
            record.artifact_id,
            None,
            record.schema_version,
            None,
            DigestPresent("PRESENT", record.observed_digest),
            None,
            captured_at,
        )
        for record in manifest.records
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    monkeypatch.setattr(
        artifacts,
        "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1",
        artifacts.RunArtifactSetPublicKeyRegistryV1(
            "registry.v1",
            MappingProxyType({"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "ACTIVE")}),
        ),
    )
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_SIGNER_PORT_V1", ("key-1", private_key.sign))
    verifier_calls = 0
    real_verifier = artifacts.validate_run_artifact_manifest_v1

    def counted_verifier(value):
        nonlocal verifier_calls
        verifier_calls += 1
        return real_verifier(value)

    monkeypatch.setattr(artifacts, "coordinate_run_artifact_set_v1", lambda *_args, **_kwargs: manifest)
    monkeypatch.setattr(artifacts, "validate_run_artifact_manifest_v1", counted_verifier)

    result = artifacts.coordinate_run_artifact_set_with_target_refs_v1(
        tmp_path,
        request,
        target_refs_request=artifacts.RunArtifactTargetRefsRequestV1(*refs),
        manifest_outer_ref_request=artifacts.ManifestOuterRefRequestV1(
            None, "f09.run-manifest.v1", None, None, captured_at,
        ),
        existing_manifest=None,
        attempt_id="R41-COUNT",
        now=NOW,
    )

    assert result.manifest is manifest
    assert verifier_calls == 1


def test_r41_private_signer_installer_is_not_part_of_the_public_api_surface():
    installer = getattr(artifacts, "_install_run_artifact_set_signer_port_v1")

    assert callable(installer)
    assert tuple(inspect.signature(installer).parameters) == ("key_id", "private_key")
    assert inspect.signature(installer).parameters["key_id"].kind is inspect.Parameter.KEYWORD_ONLY
    assert inspect.signature(installer).parameters["private_key"].kind is inspect.Parameter.KEYWORD_ONLY
    assert "_install_run_artifact_set_signer_port_v1" not in artifacts.__all__ if hasattr(artifacts, "__all__") else True


def test_r41_coordinator_rejects_signer_port_not_backed_by_an_active_registry_key(tmp_path, monkeypatch):
    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    key = manifest.key
    request = artifacts.RunArtifactSetRequestV1(
        key,
        key.run_id,
        manifest.records[0].attempts[0].input_snapshot_refs,
        "f09.run-artifact-fixture.v1",
        {
            "RUN_SNAPSHOT": b"f09.run-fixture.run-snapshot.v1",
            "DECISION_RUN": b"f09.run-fixture.decision-run.v1",
            "FEEDBACK_ATTACHMENT": b"f09.run-fixture.feedback-attachment.v1",
        },
    )
    captured_at = "2026-07-24T00:00:00Z"
    refs = tuple(
        VersionedObjectRef(
            record.artifact_role, record.artifact_id, None, record.schema_version, None,
            DigestPresent("PRESENT", record.observed_digest), None, captured_at,
        )
        for record in manifest.records
    )
    private_key = Ed25519PrivateKey.generate()
    monkeypatch.setattr(artifacts, "coordinate_run_artifact_set_v1", lambda *_args, **_kwargs: manifest)
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_SIGNER_PORT_V1", ("unknown-key", private_key.sign))
    monkeypatch.setattr(
        artifacts,
        "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1",
        artifacts.RunArtifactSetPublicKeyRegistryV1("registry.v1", MappingProxyType({})),
    )

    with pytest.raises(F09ContractError) as caught:
        artifacts.coordinate_run_artifact_set_with_target_refs_v1(
            tmp_path,
            request,
            target_refs_request=artifacts.RunArtifactTargetRefsRequestV1(*refs),
            manifest_outer_ref_request=artifacts.ManifestOuterRefRequestV1(
                None, "f09.run-manifest.v1", None, None, captured_at,
            ),
            existing_manifest=None,
            attempt_id="R41-UNKNOWN-KEY",
            now=NOW,
        )

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_SIGNING_KEY_INVALID"


def test_r41_registry_installer_rejects_mutable_mapping(monkeypatch):
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    registry = artifacts.RunArtifactSetPublicKeyRegistryV1(
        "registry.v1",
        {"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "ACTIVE")},
    )
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1", None)

    with pytest.raises(F09ContractError) as caught:
        artifacts._install_run_artifact_set_public_key_registry_v1(registry=registry)

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_INVALID"
    assert caught.value.field_path == "issuance_proof"


def test_r41_non_preprod_request_stops_before_coordinator_or_manifest_verifier(tmp_path, monkeypatch):
    fixture = artifacts.provision_verified_run_manifest_fixture_v1()
    preprod_key = fixture.key
    non_preprod_key = replace(preprod_key, track=RunTrack.STAGED_L6)
    request = artifacts.RunArtifactSetRequestV1(
        non_preprod_key,
        non_preprod_key.run_id,
        fixture.records[0].attempts[0].input_snapshot_refs,
        "f09.run-artifact-fixture.v1",
        {
            "RUN_SNAPSHOT": b"f09.run-fixture.run-snapshot.v1",
            "DECISION_RUN": b"f09.run-fixture.decision-run.v1",
            "FEEDBACK_ATTACHMENT": b"f09.run-fixture.feedback-attachment.v1",
        },
    )
    calls = {"coordinator": 0, "verifier": 0}

    def unexpected_coordinator(*_args, **_kwargs):
        calls["coordinator"] += 1
        raise AssertionError("legacy coordinator must not run")

    def unexpected_verifier(*_args, **_kwargs):
        calls["verifier"] += 1
        raise AssertionError("manifest verifier must not run")

    monkeypatch.setattr(artifacts, "coordinate_run_artifact_set_v1", unexpected_coordinator)
    monkeypatch.setattr(artifacts, "validate_run_artifact_manifest_v1", unexpected_verifier)

    with pytest.raises(F09ContractError):
        artifacts.coordinate_run_artifact_set_with_target_refs_v1(
            tmp_path,
            request,
            target_refs_request=artifacts.RunArtifactTargetRefsRequestV1(
                *(
                    VersionedObjectRef(
                        record.artifact_role,
                        record.artifact_id,
                        None,
                        record.schema_version,
                        None,
                        DigestPresent("PRESENT", record.observed_digest),
                        None,
                        "2026-07-24T00:00:00Z",
                    )
                    for record in fixture.records
                )
            ),
            manifest_outer_ref_request=artifacts.ManifestOuterRefRequestV1(
                None, "f09.run-manifest.v1", None, None, "2026-07-24T00:00:00Z",
            ),
            existing_manifest=None,
            attempt_id="R41-NON-PREPROD",
            now=NOW,
        )

    assert calls == {"coordinator": 0, "verifier": 0}


def test_r41_private_signer_installer_installs_only_matching_active_key(monkeypatch):
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    registry = artifacts.RunArtifactSetPublicKeyRegistryV1(
        "registry.v1",
        MappingProxyType({"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "ACTIVE")}),
    )
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1", registry)
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_SIGNER_PORT_V1", None)

    artifacts._install_run_artifact_set_signer_port_v1(key_id="key-1", private_key=private_key)

    port = artifacts._RUN_ARTIFACT_SET_SIGNER_PORT_V1
    assert type(port) is tuple
    assert port[0] == "key-1"
    assert callable(port[1])
    assert len(port[1](b"r41 signer installer test")) == 64


def test_r41_registry_installer_rejects_nonexact_active_status(monkeypatch):
    class ActiveStatus(str):
        pass

    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    registry = artifacts.RunArtifactSetPublicKeyRegistryV1(
        "registry.v1",
        MappingProxyType(
            {"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, ActiveStatus("ACTIVE"))}
        ),
    )
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1", None)

    with pytest.raises(F09ContractError) as caught:
        artifacts._install_run_artifact_set_public_key_registry_v1(registry=registry)

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_INVALID"
    assert caught.value.field_path == "issuance_proof"


def test_r41_public_verifier_rejects_nonexact_ed25519_algorithm(monkeypatch):
    class Ed25519Algorithm(str):
        pass

    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    captured_at = "2026-07-24T00:00:00Z"
    capture_refs = tuple(
        VersionedObjectRef(
            record.artifact_role, record.artifact_id, None, record.schema_version, None,
            DigestPresent("PRESENT", record.observed_digest), None, captured_at,
        )
        for record in manifest.records
    )
    records_digest = artifacts.validate_run_artifact_manifest_v1(manifest)
    target_refs = capture_refs + (
        VersionedObjectRef(
            "MANIFEST", manifest.manifest_id, None, "f09.run-manifest.v1", None,
            DigestPresent("PRESENT", records_digest), None, captured_at,
        ),
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    monkeypatch.setattr(
        artifacts,
        "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1",
        artifacts.RunArtifactSetPublicKeyRegistryV1(
            "registry.v1",
            MappingProxyType({"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "ACTIVE")}),
        ),
    )
    payload = artifacts.canonicalize_run_artifact_set_issuance_payload_v1(manifest, target_refs)
    result = artifacts.RunArtifactSetResultV1(
        manifest,
        target_refs,
        artifacts.IssuedRunArtifactSetProofV1(
            Ed25519Algorithm("Ed25519"),
            "key-1",
            base64.urlsafe_b64encode(private_key.sign(payload)).rstrip(b"=").decode("ascii"),
        ),
    )

    with pytest.raises(F09ContractError) as caught:
        artifacts.validate_run_artifact_set_result_issuance_v1(result)

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_INVALID"
    assert caught.value.field_path == "issuance_proof"


def test_r41_registry_installer_rejects_nonexact_public_key_id(monkeypatch):
    class KeyId(str):
        pass

    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    registry = artifacts.RunArtifactSetPublicKeyRegistryV1(
        "registry.v1",
        MappingProxyType(
            {"key-1": artifacts.RunArtifactSetPublicKeyV1(KeyId("key-1"), public_key_b64url, "ACTIVE")}
        ),
    )
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1", None)

    with pytest.raises(F09ContractError) as caught:
        artifacts._install_run_artifact_set_public_key_registry_v1(registry=registry)

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_INVALID"
    assert caught.value.field_path == "issuance_proof"


def test_r41_public_verifier_calls_serializer_and_registry_getter_once(monkeypatch):
    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    captured_at = "2026-07-24T00:00:00Z"
    capture_refs = tuple(
        VersionedObjectRef(
            record.artifact_role, record.artifact_id, None, record.schema_version, None,
            DigestPresent("PRESENT", record.observed_digest), None, captured_at,
        )
        for record in manifest.records
    )
    records_digest = artifacts.validate_run_artifact_manifest_v1(manifest)
    target_refs = capture_refs + (
        VersionedObjectRef(
            "MANIFEST", manifest.manifest_id, None, "f09.run-manifest.v1", None,
            DigestPresent("PRESENT", records_digest), None, captured_at,
        ),
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    registry = artifacts.RunArtifactSetPublicKeyRegistryV1(
        "registry.v1",
        MappingProxyType({"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "ACTIVE")}),
    )
    payload = artifacts.canonicalize_run_artifact_set_issuance_payload_v1(manifest, target_refs)
    result = artifacts.RunArtifactSetResultV1(
        manifest,
        target_refs,
        artifacts.IssuedRunArtifactSetProofV1(
            "Ed25519",
            "key-1",
            base64.urlsafe_b64encode(private_key.sign(payload)).rstrip(b"=").decode("ascii"),
        ),
    )
    calls = {"serializer": 0, "registry": 0}
    serializer = artifacts.canonicalize_run_artifact_set_issuance_payload_v1

    def counted_serializer(value, refs):
        calls["serializer"] += 1
        return serializer(value, refs)

    def counted_registry_getter():
        calls["registry"] += 1
        return registry

    monkeypatch.setattr(artifacts, "canonicalize_run_artifact_set_issuance_payload_v1", counted_serializer)
    monkeypatch.setattr(artifacts, "get_run_artifact_set_public_key_registry_v1", counted_registry_getter)

    artifacts.validate_run_artifact_set_result_issuance_v1(result)

    assert calls == {"serializer": 1, "registry": 1}


def test_r41_versioned_coordinator_calls_legacy_coordinator_once(tmp_path, monkeypatch):
    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    key = manifest.key
    request = artifacts.RunArtifactSetRequestV1(
        key,
        key.run_id,
        manifest.records[0].attempts[0].input_snapshot_refs,
        "f09.run-artifact-fixture.v1",
        {
            "RUN_SNAPSHOT": b"f09.run-fixture.run-snapshot.v1",
            "DECISION_RUN": b"f09.run-fixture.decision-run.v1",
            "FEEDBACK_ATTACHMENT": b"f09.run-fixture.feedback-attachment.v1",
        },
    )
    captured_at = "2026-07-24T00:00:00Z"
    refs = tuple(
        VersionedObjectRef(
            record.artifact_role, record.artifact_id, None, record.schema_version, None,
            DigestPresent("PRESENT", record.observed_digest), None, captured_at,
        )
        for record in manifest.records
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    monkeypatch.setattr(
        artifacts,
        "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1",
        artifacts.RunArtifactSetPublicKeyRegistryV1(
            "registry.v1",
            MappingProxyType({"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "ACTIVE")}),
        ),
    )
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_SIGNER_PORT_V1", ("key-1", private_key.sign))
    calls = 0

    def counted_coordinator(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return manifest

    monkeypatch.setattr(artifacts, "coordinate_run_artifact_set_v1", counted_coordinator)

    result = artifacts.coordinate_run_artifact_set_with_target_refs_v1(
        tmp_path,
        request,
        target_refs_request=artifacts.RunArtifactTargetRefsRequestV1(*refs),
        manifest_outer_ref_request=artifacts.ManifestOuterRefRequestV1(
            None, "f09.run-manifest.v1", None, None, captured_at,
        ),
        existing_manifest=None,
        attempt_id="R41-LEGACY-COUNT",
        now=NOW,
    )

    assert result.manifest is manifest
    assert calls == 1


def test_r41_public_verifier_rejects_nonexact_active_registry_status(monkeypatch):
    class ActiveStatus(str):
        pass

    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    captured_at = "2026-07-24T00:00:00Z"
    capture_refs = tuple(
        VersionedObjectRef(
            record.artifact_role, record.artifact_id, None, record.schema_version, None,
            DigestPresent("PRESENT", record.observed_digest), None, captured_at,
        )
        for record in manifest.records
    )
    records_digest = artifacts.validate_run_artifact_manifest_v1(manifest)
    target_refs = capture_refs + (
        VersionedObjectRef(
            "MANIFEST", manifest.manifest_id, None, "f09.run-manifest.v1", None,
            DigestPresent("PRESENT", records_digest), None, captured_at,
        ),
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    monkeypatch.setattr(
        artifacts,
        "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1",
        artifacts.RunArtifactSetPublicKeyRegistryV1(
            "registry.v1",
            MappingProxyType(
                {"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, ActiveStatus("ACTIVE"))}
            ),
        ),
    )
    payload = artifacts.canonicalize_run_artifact_set_issuance_payload_v1(manifest, target_refs)
    result = artifacts.RunArtifactSetResultV1(
        manifest,
        target_refs,
        artifacts.IssuedRunArtifactSetProofV1(
            "Ed25519",
            "key-1",
            base64.urlsafe_b64encode(private_key.sign(payload)).rstrip(b"=").decode("ascii"),
        ),
    )

    with pytest.raises(F09ContractError) as caught:
        artifacts.validate_run_artifact_set_result_issuance_v1(result)

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_INVALID"
    assert caught.value.field_path == "issuance_proof"


def test_r41_coordinator_rejects_nonexact_active_registry_status(tmp_path, monkeypatch):
    class ActiveStatus(str):
        pass

    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    key = manifest.key
    request = artifacts.RunArtifactSetRequestV1(
        key,
        key.run_id,
        manifest.records[0].attempts[0].input_snapshot_refs,
        "f09.run-artifact-fixture.v1",
        {
            "RUN_SNAPSHOT": b"f09.run-fixture.run-snapshot.v1",
            "DECISION_RUN": b"f09.run-fixture.decision-run.v1",
            "FEEDBACK_ATTACHMENT": b"f09.run-fixture.feedback-attachment.v1",
        },
    )
    captured_at = "2026-07-24T00:00:00Z"
    refs = tuple(
        VersionedObjectRef(
            record.artifact_role, record.artifact_id, None, record.schema_version, None,
            DigestPresent("PRESENT", record.observed_digest), None, captured_at,
        )
        for record in manifest.records
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    monkeypatch.setattr(artifacts, "coordinate_run_artifact_set_v1", lambda *_args, **_kwargs: manifest)
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_SIGNER_PORT_V1", ("key-1", private_key.sign))
    monkeypatch.setattr(
        artifacts,
        "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1",
        artifacts.RunArtifactSetPublicKeyRegistryV1(
            "registry.v1",
            MappingProxyType(
                {"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, ActiveStatus("ACTIVE"))}
            ),
        ),
    )

    with pytest.raises(F09ContractError) as caught:
        artifacts.coordinate_run_artifact_set_with_target_refs_v1(
            tmp_path,
            request,
            target_refs_request=artifacts.RunArtifactTargetRefsRequestV1(*refs),
            manifest_outer_ref_request=artifacts.ManifestOuterRefRequestV1(
                None, "f09.run-manifest.v1", None, None, captured_at,
            ),
            existing_manifest=None,
            attempt_id="R41-NONEXACT-STATUS",
            now=NOW,
        )

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_SIGNING_KEY_INVALID"
    assert caught.value.field_path == "issuance_proof"


def test_r41_private_signer_installer_rejects_nonexact_active_registry_status(monkeypatch):
    class ActiveStatus(str):
        pass

    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    monkeypatch.setattr(
        artifacts,
        "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1",
        artifacts.RunArtifactSetPublicKeyRegistryV1(
            "registry.v1",
            MappingProxyType(
                {"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, ActiveStatus("ACTIVE"))}
            ),
        ),
    )
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_SIGNER_PORT_V1", None)

    with pytest.raises(F09ContractError) as caught:
        artifacts._install_run_artifact_set_signer_port_v1(key_id="key-1", private_key=private_key)

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_SIGNING_KEY_INVALID"
    assert caught.value.field_path == "issuance_proof"
    assert artifacts._RUN_ARTIFACT_SET_SIGNER_PORT_V1 is None


def test_r41_registry_installer_rejects_whitespace_only_key_id(monkeypatch):
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    registry = artifacts.RunArtifactSetPublicKeyRegistryV1(
        "registry.v1",
        MappingProxyType({" ": artifacts.RunArtifactSetPublicKeyV1(" ", public_key_b64url, "ACTIVE")}),
    )
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1", None)

    with pytest.raises(F09ContractError) as caught:
        artifacts._install_run_artifact_set_public_key_registry_v1(registry=registry)

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_INVALID"
    assert caught.value.field_path == "issuance_proof"


def test_r41_invalid_capture_role_order_stops_before_legacy_coordinator(tmp_path, monkeypatch):
    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    key = manifest.key
    request = artifacts.RunArtifactSetRequestV1(
        key,
        key.run_id,
        manifest.records[0].attempts[0].input_snapshot_refs,
        "f09.run-artifact-fixture.v1",
        {
            "RUN_SNAPSHOT": b"f09.run-fixture.run-snapshot.v1",
            "DECISION_RUN": b"f09.run-fixture.decision-run.v1",
            "FEEDBACK_ATTACHMENT": b"f09.run-fixture.feedback-attachment.v1",
        },
    )
    captured_at = "2026-07-24T00:00:00Z"
    refs = tuple(
        VersionedObjectRef(
            record.artifact_role, record.artifact_id, None, record.schema_version, None,
            DigestPresent("PRESENT", record.observed_digest), None, captured_at,
        )
        for record in manifest.records
    )
    malformed_refs = (replace(refs[0], object_type="DECISION_RUN"),) + refs[1:]
    calls = 0

    def unexpected_coordinator(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("legacy coordinator must not run")

    monkeypatch.setattr(artifacts, "coordinate_run_artifact_set_v1", unexpected_coordinator)

    with pytest.raises(F09ContractError) as caught:
        artifacts.coordinate_run_artifact_set_with_target_refs_v1(
            tmp_path,
            request,
            target_refs_request=artifacts.RunArtifactTargetRefsRequestV1(*malformed_refs),
            manifest_outer_ref_request=artifacts.ManifestOuterRefRequestV1(
                None, "f09.run-manifest.v1", None, None, captured_at,
            ),
            existing_manifest=None,
            attempt_id="R41-ROLE-ORDER",
            now=NOW,
        )

    assert caught.value.issue_code == "RUN_ARTIFACT.REQUEST_INVALID"
    assert calls == 0


def test_r41_registry_installer_rejects_nonexact_public_key_encoding(monkeypatch):
    class PublicKeyEncoding(str):
        pass

    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    registry = artifacts.RunArtifactSetPublicKeyRegistryV1(
        "registry.v1",
        MappingProxyType(
            {
                "key-1": artifacts.RunArtifactSetPublicKeyV1(
                    "key-1", PublicKeyEncoding(public_key_b64url), "ACTIVE"
                )
            }
        ),
    )
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1", None)

    with pytest.raises(F09ContractError) as caught:
        artifacts._install_run_artifact_set_public_key_registry_v1(registry=registry)

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_INVALID"
    assert caught.value.field_path == "issuance_proof"


def test_r41_nonexact_capture_digest_algorithm_stops_before_legacy_coordinator(tmp_path, monkeypatch):
    class Sha256Algorithm(str):
        pass

    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    key = manifest.key
    request = artifacts.RunArtifactSetRequestV1(
        key,
        key.run_id,
        manifest.records[0].attempts[0].input_snapshot_refs,
        "f09.run-artifact-fixture.v1",
        {
            "RUN_SNAPSHOT": b"f09.run-fixture.run-snapshot.v1",
            "DECISION_RUN": b"f09.run-fixture.decision-run.v1",
            "FEEDBACK_ATTACHMENT": b"f09.run-fixture.feedback-attachment.v1",
        },
    )
    captured_at = "2026-07-24T00:00:00Z"
    refs = tuple(
        VersionedObjectRef(
            record.artifact_role,
            record.artifact_id,
            None,
            record.schema_version,
            None,
            DigestPresent("PRESENT", record.observed_digest),
            None,
            captured_at,
        )
        for record in manifest.records
    )
    malformed_digest = replace(refs[0].digest_binding.digest, algorithm=Sha256Algorithm("sha256"))
    malformed_refs = (replace(refs[0], digest_binding=DigestPresent("PRESENT", malformed_digest)),) + refs[1:]
    calls = 0

    def unexpected_coordinator(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("legacy coordinator must not run")

    monkeypatch.setattr(artifacts, "coordinate_run_artifact_set_v1", unexpected_coordinator)

    with pytest.raises(F09ContractError) as caught:
        artifacts.coordinate_run_artifact_set_with_target_refs_v1(
            tmp_path,
            request,
            target_refs_request=artifacts.RunArtifactTargetRefsRequestV1(*malformed_refs),
            manifest_outer_ref_request=artifacts.ManifestOuterRefRequestV1(
                None, "f09.run-manifest.v1", None, None, captured_at,
            ),
            existing_manifest=None,
            attempt_id="R41-DIGEST-ALGORITHM",
            now=NOW,
        )

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_INVALID"
    assert calls == 0


def test_r41_serializer_rejects_nonexact_present_digest_status():
    class PresentStatus(str):
        pass

    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    captured_at = "2026-07-24T00:00:00Z"
    capture_refs = tuple(
        VersionedObjectRef(
            record.artifact_role,
            record.artifact_id,
            None,
            record.schema_version,
            None,
            DigestPresent("PRESENT", record.observed_digest),
            None,
            captured_at,
        )
        for record in manifest.records
    )
    records_digest = artifacts.validate_run_artifact_manifest_v1(manifest)
    malformed_refs = (
        replace(capture_refs[0], digest_binding=DigestPresent(PresentStatus("PRESENT"), capture_refs[0].digest_binding.digest)),
    ) + capture_refs[1:] + (
        VersionedObjectRef(
            "MANIFEST", manifest.manifest_id, None, "f09.run-manifest.v1", None,
            DigestPresent("PRESENT", records_digest), None, captured_at,
        ),
    )

    with pytest.raises(F09ContractError) as caught:
        artifacts.canonicalize_run_artifact_set_issuance_payload_v1(manifest, malformed_refs)

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_INVALID"


def test_r41_registry_installer_owns_a_copy_of_valid_key_material(monkeypatch):
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    source_key = artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "ACTIVE")
    registry = artifacts.RunArtifactSetPublicKeyRegistryV1(
        "registry.v1",
        MappingProxyType({"key-1": source_key}),
    )
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1", None)

    artifacts._install_run_artifact_set_public_key_registry_v1(registry=registry)
    object.__setattr__(source_key, "status", "REVOKED")

    installed = artifacts.get_run_artifact_set_public_key_registry_v1()

    assert installed.keys_by_id["key-1"].status == "ACTIVE"
    assert installed.keys_by_id["key-1"] is not source_key


def test_r41_duplicate_registry_install_preserves_installed_snapshot(monkeypatch):
    first_private_key = Ed25519PrivateKey.generate()
    first_public_key_b64url = base64.urlsafe_b64encode(
        first_private_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw,
        )
    ).rstrip(b"=").decode("ascii")
    second_private_key = Ed25519PrivateKey.generate()
    second_public_key_b64url = base64.urlsafe_b64encode(
        second_private_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw,
        )
    ).rstrip(b"=").decode("ascii")
    first_registry = artifacts.RunArtifactSetPublicKeyRegistryV1(
        "registry.v1",
        MappingProxyType(
            {
                "key-1": artifacts.RunArtifactSetPublicKeyV1(
                    "key-1", first_public_key_b64url, "ACTIVE",
                )
            }
        ),
    )
    replacement_registry = artifacts.RunArtifactSetPublicKeyRegistryV1(
        "registry.v2",
        MappingProxyType(
            {
                "key-2": artifacts.RunArtifactSetPublicKeyV1(
                    "key-2", second_public_key_b64url, "ACTIVE",
                )
            }
        ),
    )
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1", None)
    artifacts._install_run_artifact_set_public_key_registry_v1(registry=first_registry)
    installed_before_duplicate = artifacts.get_run_artifact_set_public_key_registry_v1()

    with pytest.raises(F09ContractError) as caught:
        artifacts._install_run_artifact_set_public_key_registry_v1(
            registry=replacement_registry,
        )

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_INVALID"
    assert caught.value.field_path == "issuance_proof"
    assert artifacts.get_run_artifact_set_public_key_registry_v1() is installed_before_duplicate
    assert tuple(installed_before_duplicate.keys_by_id) == ("key-1",)
    assert installed_before_duplicate.keys_by_id["key-1"].public_key_b64url == first_public_key_b64url


def test_r41_rotation_snapshot_only_adds_key_id_without_rewriting_old_key(monkeypatch):
    old_private_key = Ed25519PrivateKey.generate()
    old_public_key_b64url = base64.urlsafe_b64encode(
        old_private_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw,
        )
    ).rstrip(b"=").decode("ascii")
    new_private_key = Ed25519PrivateKey.generate()
    new_public_key_b64url = base64.urlsafe_b64encode(
        new_private_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw,
        )
    ).rstrip(b"=").decode("ascii")
    old_key = artifacts.RunArtifactSetPublicKeyV1(
        "key-old", old_public_key_b64url, "ACTIVE",
    )
    old_snapshot = artifacts.RunArtifactSetPublicKeyRegistryV1(
        "registry.v1", MappingProxyType({"key-old": old_key}),
    )
    rotated_snapshot = artifacts.RunArtifactSetPublicKeyRegistryV1(
        "registry.v2",
        MappingProxyType(
            {
                "key-old": old_key,
                "key-new": artifacts.RunArtifactSetPublicKeyV1(
                    "key-new", new_public_key_b64url, "ACTIVE",
                ),
            }
        ),
    )
    monkeypatch.setattr(
        artifacts, "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1", rotated_snapshot,
    )

    published = artifacts.get_run_artifact_set_public_key_registry_v1()

    assert set(published.keys_by_id) - set(old_snapshot.keys_by_id) == {"key-new"}
    assert published.keys_by_id["key-old"] == old_snapshot.keys_by_id["key-old"]
    assert published.keys_by_id["key-old"].status == "ACTIVE"


def test_r41_old_active_key_proof_remains_valid_under_add_only_rotation(monkeypatch):
    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    captured_at = "2026-07-24T00:00:00Z"
    capture_refs = tuple(
        VersionedObjectRef(
            record.artifact_role, record.artifact_id, None, record.schema_version, None,
            DigestPresent("PRESENT", record.observed_digest), None, captured_at,
        )
        for record in manifest.records
    )
    records_digest = artifacts.validate_run_artifact_manifest_v1(manifest)
    target_refs = capture_refs + (
        VersionedObjectRef(
            "MANIFEST", manifest.manifest_id, None, "f09.run-manifest.v1", None,
            DigestPresent("PRESENT", records_digest), None, captured_at,
        ),
    )
    old_private_key = Ed25519PrivateKey.generate()
    old_public_key_b64url = base64.urlsafe_b64encode(
        old_private_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw,
        )
    ).rstrip(b"=").decode("ascii")
    new_private_key = Ed25519PrivateKey.generate()
    new_public_key_b64url = base64.urlsafe_b64encode(
        new_private_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw,
        )
    ).rstrip(b"=").decode("ascii")
    payload = artifacts.canonicalize_run_artifact_set_issuance_payload_v1(
        manifest, target_refs,
    )
    result = artifacts.RunArtifactSetResultV1(
        manifest,
        target_refs,
        artifacts.IssuedRunArtifactSetProofV1(
            "Ed25519",
            "key-old",
            base64.urlsafe_b64encode(old_private_key.sign(payload)).rstrip(b"=").decode("ascii"),
        ),
    )
    monkeypatch.setattr(
        artifacts,
        "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1",
        artifacts.RunArtifactSetPublicKeyRegistryV1(
            "registry.v2",
            MappingProxyType(
                {
                    "key-old": artifacts.RunArtifactSetPublicKeyV1(
                        "key-old", old_public_key_b64url, "ACTIVE",
                    ),
                    "key-new": artifacts.RunArtifactSetPublicKeyV1(
                        "key-new", new_public_key_b64url, "ACTIVE",
                    ),
                }
            ),
        ),
    )

    artifacts.validate_run_artifact_set_result_issuance_v1(result)


@pytest.mark.parametrize("reconstruction", ["clone", "deserialize", "direct"])
def test_r41_issuance_proof_is_value_verifiable_after_reconstruction(
    monkeypatch, reconstruction,
):
    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    captured_at = "2026-07-24T00:00:00Z"
    capture_refs = tuple(
        VersionedObjectRef(
            record.artifact_role, record.artifact_id, None, record.schema_version, None,
            DigestPresent("PRESENT", record.observed_digest), None, captured_at,
        )
        for record in manifest.records
    )
    records_digest = artifacts.validate_run_artifact_manifest_v1(manifest)
    target_refs = capture_refs + (
        VersionedObjectRef(
            "MANIFEST", manifest.manifest_id, None, "f09.run-manifest.v1", None,
            DigestPresent("PRESENT", records_digest), None, captured_at,
        ),
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw,
        )
    ).rstrip(b"=").decode("ascii")
    monkeypatch.setattr(
        artifacts,
        "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1",
        artifacts.RunArtifactSetPublicKeyRegistryV1(
            "registry.v1",
            MappingProxyType(
                {
                    "key-1": artifacts.RunArtifactSetPublicKeyV1(
                        "key-1", public_key_b64url, "ACTIVE",
                    )
                }
            ),
        ),
    )
    payload = artifacts.canonicalize_run_artifact_set_issuance_payload_v1(
        manifest, target_refs,
    )
    original_proof = artifacts.IssuedRunArtifactSetProofV1(
        "Ed25519",
        "key-1",
        base64.urlsafe_b64encode(private_key.sign(payload)).rstrip(b"=").decode("ascii"),
    )
    original = artifacts.RunArtifactSetResultV1(
        manifest, target_refs, original_proof,
    )

    if reconstruction == "clone":
        reconstructed = replace(original, issuance_proof=replace(original_proof))
    elif reconstruction == "deserialize":
        wire_proof = parse_bounded_jcs(
            canonicalize_bounded_jcs(
                {
                    "algorithm": original_proof.algorithm,
                    "key_id": original_proof.key_id,
                    "signature_b64url": original_proof.signature_b64url,
                }
            )
        )
        reconstructed = artifacts.RunArtifactSetResultV1(
            manifest,
            tuple(target_refs),
            artifacts.IssuedRunArtifactSetProofV1(
                wire_proof["algorithm"],
                wire_proof["key_id"],
                wire_proof["signature_b64url"],
            ),
        )
    else:
        reconstructed = artifacts.RunArtifactSetResultV1(
            manifest,
            tuple(ref for ref in target_refs),
            artifacts.IssuedRunArtifactSetProofV1(
                original_proof.algorithm,
                original_proof.key_id,
                original_proof.signature_b64url,
            ),
        )

    assert reconstructed == original
    assert reconstructed is not original
    assert reconstructed.issuance_proof is not original.issuance_proof
    artifacts.validate_run_artifact_set_result_issuance_v1(reconstructed)


def test_r41_whitespace_capture_object_id_stops_before_legacy_coordinator(tmp_path, monkeypatch):
    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    key = manifest.key
    request = artifacts.RunArtifactSetRequestV1(
        key,
        key.run_id,
        manifest.records[0].attempts[0].input_snapshot_refs,
        "f09.run-artifact-fixture.v1",
        {
            "RUN_SNAPSHOT": b"f09.run-fixture.run-snapshot.v1",
            "DECISION_RUN": b"f09.run-fixture.decision-run.v1",
            "FEEDBACK_ATTACHMENT": b"f09.run-fixture.feedback-attachment.v1",
        },
    )
    captured_at = "2026-07-24T00:00:00Z"
    refs = tuple(
        VersionedObjectRef(
            record.artifact_role,
            record.artifact_id,
            None,
            record.schema_version,
            None,
            DigestPresent("PRESENT", record.observed_digest),
            None,
            captured_at,
        )
        for record in manifest.records
    )
    malformed_refs = (replace(refs[0], object_id=" "),) + refs[1:]
    calls = 0

    def unexpected_coordinator(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("legacy coordinator must not run")

    monkeypatch.setattr(artifacts, "coordinate_run_artifact_set_v1", unexpected_coordinator)

    with pytest.raises(F09ContractError) as caught:
        artifacts.coordinate_run_artifact_set_with_target_refs_v1(
            tmp_path,
            request,
            target_refs_request=artifacts.RunArtifactTargetRefsRequestV1(*malformed_refs),
            manifest_outer_ref_request=artifacts.ManifestOuterRefRequestV1(
                None, "f09.run-manifest.v1", None, None, captured_at,
            ),
            existing_manifest=None,
            attempt_id="R41-WHITESPACE-CAPTURE-ID",
            now=NOW,
        )

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_INVALID"
    assert calls == 0


def test_r41_public_verifier_rejects_signature_with_non_base64url_suffix(monkeypatch):
    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    captured_at = "2026-07-24T00:00:00Z"
    capture_refs = tuple(
        VersionedObjectRef(
            record.artifact_role,
            record.artifact_id,
            None,
            record.schema_version,
            None,
            DigestPresent("PRESENT", record.observed_digest),
            None,
            captured_at,
        )
        for record in manifest.records
    )
    records_digest = artifacts.validate_run_artifact_manifest_v1(manifest)
    target_refs = capture_refs + (
        VersionedObjectRef(
            "MANIFEST", manifest.manifest_id, None, "f09.run-manifest.v1", None,
            DigestPresent("PRESENT", records_digest), None, captured_at,
        ),
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    monkeypatch.setattr(
        artifacts,
        "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1",
        artifacts.RunArtifactSetPublicKeyRegistryV1(
            "registry.v1",
            MappingProxyType({"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "ACTIVE")}),
        ),
    )
    payload = artifacts.canonicalize_run_artifact_set_issuance_payload_v1(manifest, target_refs)
    signature_b64url = base64.urlsafe_b64encode(private_key.sign(payload)).rstrip(b"=").decode("ascii")
    result = artifacts.RunArtifactSetResultV1(
        manifest,
        target_refs,
        artifacts.IssuedRunArtifactSetProofV1("Ed25519", "key-1", signature_b64url + "!"),
    )

    with pytest.raises(F09ContractError) as caught:
        artifacts.validate_run_artifact_set_result_issuance_v1(result)

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_INVALID"


def test_r41_whitespace_manifest_outer_schema_stops_before_legacy_coordinator(tmp_path, monkeypatch):
    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    key = manifest.key
    request = artifacts.RunArtifactSetRequestV1(
        key,
        key.run_id,
        manifest.records[0].attempts[0].input_snapshot_refs,
        "f09.run-artifact-fixture.v1",
        {
            "RUN_SNAPSHOT": b"f09.run-fixture.run-snapshot.v1",
            "DECISION_RUN": b"f09.run-fixture.decision-run.v1",
            "FEEDBACK_ATTACHMENT": b"f09.run-fixture.feedback-attachment.v1",
        },
    )
    captured_at = "2026-07-24T00:00:00Z"
    refs = tuple(
        VersionedObjectRef(
            record.artifact_role,
            record.artifact_id,
            None,
            record.schema_version,
            None,
            DigestPresent("PRESENT", record.observed_digest),
            None,
            captured_at,
        )
        for record in manifest.records
    )
    calls = 0

    def unexpected_coordinator(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("legacy coordinator must not run")

    monkeypatch.setattr(artifacts, "coordinate_run_artifact_set_v1", unexpected_coordinator)

    with pytest.raises(F09ContractError) as caught:
        artifacts.coordinate_run_artifact_set_with_target_refs_v1(
            tmp_path,
            request,
            target_refs_request=artifacts.RunArtifactTargetRefsRequestV1(*refs),
            manifest_outer_ref_request=artifacts.ManifestOuterRefRequestV1(
                None, " ", None, None, captured_at,
            ),
            existing_manifest=None,
            attempt_id="R41-WHITESPACE-OUTER-SCHEMA",
            now=NOW,
        )

    assert caught.value.issue_code == "RUN_ARTIFACT.REQUEST_INVALID"
    assert calls == 0


def test_r41_public_verifier_rejects_public_key_with_non_base64url_suffix(monkeypatch):
    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    captured_at = "2026-07-24T00:00:00Z"
    capture_refs = tuple(
        VersionedObjectRef(
            record.artifact_role,
            record.artifact_id,
            None,
            record.schema_version,
            None,
            DigestPresent("PRESENT", record.observed_digest),
            None,
            captured_at,
        )
        for record in manifest.records
    )
    records_digest = artifacts.validate_run_artifact_manifest_v1(manifest)
    target_refs = capture_refs + (
        VersionedObjectRef(
            "MANIFEST", manifest.manifest_id, None, "f09.run-manifest.v1", None,
            DigestPresent("PRESENT", records_digest), None, captured_at,
        ),
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    monkeypatch.setattr(
        artifacts,
        "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1",
        artifacts.RunArtifactSetPublicKeyRegistryV1(
            "registry.v1",
            MappingProxyType({"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url + "!", "ACTIVE")}),
        ),
    )
    payload = artifacts.canonicalize_run_artifact_set_issuance_payload_v1(manifest, target_refs)
    result = artifacts.RunArtifactSetResultV1(
        manifest,
        target_refs,
        artifacts.IssuedRunArtifactSetProofV1(
            "Ed25519", "key-1", base64.urlsafe_b64encode(private_key.sign(payload)).rstrip(b"=").decode("ascii"),
        ),
    )

    with pytest.raises(F09ContractError) as caught:
        artifacts.validate_run_artifact_set_result_issuance_v1(result)

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_INVALID"


def test_r41_public_verifier_rejects_revoked_key(monkeypatch):
    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    captured_at = "2026-07-24T00:00:00Z"
    capture_refs = tuple(
        VersionedObjectRef(
            record.artifact_role,
            record.artifact_id,
            None,
            record.schema_version,
            None,
            DigestPresent("PRESENT", record.observed_digest),
            None,
            captured_at,
        )
        for record in manifest.records
    )
    records_digest = artifacts.validate_run_artifact_manifest_v1(manifest)
    target_refs = capture_refs + (
        VersionedObjectRef(
            "MANIFEST", manifest.manifest_id, None, "f09.run-manifest.v1", None,
            DigestPresent("PRESENT", records_digest), None, captured_at,
        ),
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    monkeypatch.setattr(
        artifacts,
        "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1",
        artifacts.RunArtifactSetPublicKeyRegistryV1(
            "registry.v1",
            MappingProxyType({"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "REVOKED")}),
        ),
    )
    payload = artifacts.canonicalize_run_artifact_set_issuance_payload_v1(manifest, target_refs)
    result = artifacts.RunArtifactSetResultV1(
        manifest,
        target_refs,
        artifacts.IssuedRunArtifactSetProofV1(
            "Ed25519", "key-1", base64.urlsafe_b64encode(private_key.sign(payload)).rstrip(b"=").decode("ascii"),
        ),
    )

    with pytest.raises(F09ContractError) as caught:
        artifacts.validate_run_artifact_set_result_issuance_v1(result)

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_INVALID"


def test_r41_public_verifier_wraps_malformed_registry_as_contract_error(monkeypatch):
    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    captured_at = "2026-07-24T00:00:00Z"
    capture_refs = tuple(
        VersionedObjectRef(
            record.artifact_role,
            record.artifact_id,
            None,
            record.schema_version,
            None,
            DigestPresent("PRESENT", record.observed_digest),
            None,
            captured_at,
        )
        for record in manifest.records
    )
    records_digest = artifacts.validate_run_artifact_manifest_v1(manifest)
    target_refs = capture_refs + (
        VersionedObjectRef(
            "MANIFEST", manifest.manifest_id, None, "f09.run-manifest.v1", None,
            DigestPresent("PRESENT", records_digest), None, captured_at,
        ),
    )
    proof = artifacts.IssuedRunArtifactSetProofV1("Ed25519", "key-1", "A" * 86)
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1", object())

    with pytest.raises(F09ContractError) as caught:
        artifacts.validate_run_artifact_set_result_issuance_v1(
            artifacts.RunArtifactSetResultV1(manifest, target_refs, proof)
        )

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_INVALID"


def test_r41_public_verifier_rejects_malformed_registry_version(monkeypatch):
    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    captured_at = "2026-07-24T00:00:00Z"
    capture_refs = tuple(
        VersionedObjectRef(
            record.artifact_role,
            record.artifact_id,
            None,
            record.schema_version,
            None,
            DigestPresent("PRESENT", record.observed_digest),
            None,
            captured_at,
        )
        for record in manifest.records
    )
    records_digest = artifacts.validate_run_artifact_manifest_v1(manifest)
    target_refs = capture_refs + (
        VersionedObjectRef(
            "MANIFEST", manifest.manifest_id, None, "f09.run-manifest.v1", None,
            DigestPresent("PRESENT", records_digest), None, captured_at,
        ),
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    registry = artifacts.RunArtifactSetPublicKeyRegistryV1(
        "registry.v1",
        MappingProxyType({"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "ACTIVE")}),
    )
    object.__setattr__(registry, "registry_version", " ")
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1", registry)
    payload = artifacts.canonicalize_run_artifact_set_issuance_payload_v1(manifest, target_refs)
    proof = artifacts.IssuedRunArtifactSetProofV1(
        "Ed25519", "key-1", base64.urlsafe_b64encode(private_key.sign(payload)).rstrip(b"=").decode("ascii"),
    )

    with pytest.raises(F09ContractError) as caught:
        artifacts.validate_run_artifact_set_result_issuance_v1(
            artifacts.RunArtifactSetResultV1(manifest, target_refs, proof)
        )

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_INVALID"


def test_r41_public_verifier_rejects_nonexact_registry_mapping_key(monkeypatch):
    class KeyId(str):
        pass

    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    captured_at = "2026-07-24T00:00:00Z"
    capture_refs = tuple(
        VersionedObjectRef(
            record.artifact_role,
            record.artifact_id,
            None,
            record.schema_version,
            None,
            DigestPresent("PRESENT", record.observed_digest),
            None,
            captured_at,
        )
        for record in manifest.records
    )
    records_digest = artifacts.validate_run_artifact_manifest_v1(manifest)
    target_refs = capture_refs + (
        VersionedObjectRef(
            "MANIFEST", manifest.manifest_id, None, "f09.run-manifest.v1", None,
            DigestPresent("PRESENT", records_digest), None, captured_at,
        ),
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    monkeypatch.setattr(
        artifacts,
        "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1",
        artifacts.RunArtifactSetPublicKeyRegistryV1(
            "registry.v1",
            MappingProxyType({KeyId("key-1"): artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "ACTIVE")}),
        ),
    )
    payload = artifacts.canonicalize_run_artifact_set_issuance_payload_v1(manifest, target_refs)
    proof = artifacts.IssuedRunArtifactSetProofV1(
        "Ed25519", "key-1", base64.urlsafe_b64encode(private_key.sign(payload)).rstrip(b"=").decode("ascii"),
    )

    with pytest.raises(F09ContractError) as caught:
        artifacts.validate_run_artifact_set_result_issuance_v1(
            artifacts.RunArtifactSetResultV1(manifest, target_refs, proof)
        )

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_INVALID"


def test_r41_public_verifier_rejects_malformed_unselected_registry_key(monkeypatch):
    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    captured_at = "2026-07-24T00:00:00Z"
    capture_refs = tuple(
        VersionedObjectRef(
            record.artifact_role,
            record.artifact_id,
            None,
            record.schema_version,
            None,
            DigestPresent("PRESENT", record.observed_digest),
            None,
            captured_at,
        )
        for record in manifest.records
    )
    records_digest = artifacts.validate_run_artifact_manifest_v1(manifest)
    target_refs = capture_refs + (
        VersionedObjectRef(
            "MANIFEST", manifest.manifest_id, None, "f09.run-manifest.v1", None,
            DigestPresent("PRESENT", records_digest), None, captured_at,
        ),
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    monkeypatch.setattr(
        artifacts,
        "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1",
        artifacts.RunArtifactSetPublicKeyRegistryV1(
            "registry.v1",
            MappingProxyType(
                {
                    "key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "ACTIVE"),
                    "broken": artifacts.RunArtifactSetPublicKeyV1("broken", public_key_b64url, "UNKNOWN"),
                }
            ),
        ),
    )
    payload = artifacts.canonicalize_run_artifact_set_issuance_payload_v1(manifest, target_refs)
    proof = artifacts.IssuedRunArtifactSetProofV1(
        "Ed25519", "key-1", base64.urlsafe_b64encode(private_key.sign(payload)).rstrip(b"=").decode("ascii"),
    )

    with pytest.raises(F09ContractError) as caught:
        artifacts.validate_run_artifact_set_result_issuance_v1(
            artifacts.RunArtifactSetResultV1(manifest, target_refs, proof)
        )

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_INVALID"


def test_r41_coordinator_wraps_malformed_registry_as_signing_key_error(tmp_path, monkeypatch):
    fixture = artifacts.provision_verified_run_manifest_fixture_v1()
    key = fixture.key
    request = artifacts.RunArtifactSetRequestV1(
        key,
        key.run_id,
        fixture.records[0].attempts[0].input_snapshot_refs,
        "f09.run-artifact-fixture.v1",
        {
            "RUN_SNAPSHOT": b"f09.run-fixture.run-snapshot.v1",
            "DECISION_RUN": b"f09.run-fixture.decision-run.v1",
            "FEEDBACK_ATTACHMENT": b"f09.run-fixture.feedback-attachment.v1",
        },
    )
    captured_at = "2026-07-24T00:00:00Z"
    refs = tuple(
        VersionedObjectRef(
            role,
            f"RUN-ARTIFACT:{key.canonical_key_digest.value}:{role}",
            None,
            "f09.run-artifact-fixture.v1",
            None,
            DigestPresent("PRESENT", key.projection_digest_by_role[role]),
            None,
            captured_at,
        )
        for role in key.projection_roles
    )
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1", object())
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_SIGNER_PORT_V1", ("key-1", lambda payload: b"A" * 64))

    with pytest.raises(F09ContractError) as caught:
        artifacts.coordinate_run_artifact_set_with_target_refs_v1(
            tmp_path,
            request,
            target_refs_request=artifacts.RunArtifactTargetRefsRequestV1(*refs),
            manifest_outer_ref_request=artifacts.ManifestOuterRefRequestV1(
                None, "f09.run-manifest.v1", None, None, captured_at,
            ),
            existing_manifest=None,
            attempt_id="R41-MALFORMED-REGISTRY",
            now=NOW,
        )

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_SIGNING_KEY_INVALID"


def test_r41_coordinator_rejects_malformed_registry_version(tmp_path, monkeypatch):
    fixture = artifacts.provision_verified_run_manifest_fixture_v1()
    key = fixture.key
    request = artifacts.RunArtifactSetRequestV1(
        key,
        key.run_id,
        fixture.records[0].attempts[0].input_snapshot_refs,
        "f09.run-artifact-fixture.v1",
        {
            "RUN_SNAPSHOT": b"f09.run-fixture.run-snapshot.v1",
            "DECISION_RUN": b"f09.run-fixture.decision-run.v1",
            "FEEDBACK_ATTACHMENT": b"f09.run-fixture.feedback-attachment.v1",
        },
    )
    captured_at = "2026-07-24T00:00:00Z"
    refs = tuple(
        VersionedObjectRef(
            role,
            f"RUN-ARTIFACT:{key.canonical_key_digest.value}:{role}",
            None,
            "f09.run-artifact-fixture.v1",
            None,
            DigestPresent("PRESENT", key.projection_digest_by_role[role]),
            None,
            captured_at,
        )
        for role in key.projection_roles
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    registry = artifacts.RunArtifactSetPublicKeyRegistryV1(
        "registry.v1",
        MappingProxyType({"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "ACTIVE")}),
    )
    object.__setattr__(registry, "registry_version", " ")
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1", registry)
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_SIGNER_PORT_V1", ("key-1", private_key.sign))

    with pytest.raises(F09ContractError) as caught:
        artifacts.coordinate_run_artifact_set_with_target_refs_v1(
            tmp_path,
            request,
            target_refs_request=artifacts.RunArtifactTargetRefsRequestV1(*refs),
            manifest_outer_ref_request=artifacts.ManifestOuterRefRequestV1(
                None, "f09.run-manifest.v1", None, None, captured_at,
            ),
            existing_manifest=None,
            attempt_id="R41-MALFORMED-REGISTRY-VERSION",
            now=NOW,
        )

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_SIGNING_KEY_INVALID"


def test_r41_coordinator_rejects_malformed_unselected_registry_key(tmp_path, monkeypatch):
    fixture = artifacts.provision_verified_run_manifest_fixture_v1()
    key = fixture.key
    request = artifacts.RunArtifactSetRequestV1(
        key,
        key.run_id,
        fixture.records[0].attempts[0].input_snapshot_refs,
        "f09.run-artifact-fixture.v1",
        {
            "RUN_SNAPSHOT": b"f09.run-fixture.run-snapshot.v1",
            "DECISION_RUN": b"f09.run-fixture.decision-run.v1",
            "FEEDBACK_ATTACHMENT": b"f09.run-fixture.feedback-attachment.v1",
        },
    )
    captured_at = "2026-07-24T00:00:00Z"
    refs = tuple(
        VersionedObjectRef(
            role,
            f"RUN-ARTIFACT:{key.canonical_key_digest.value}:{role}",
            None,
            "f09.run-artifact-fixture.v1",
            None,
            DigestPresent("PRESENT", key.projection_digest_by_role[role]),
            None,
            captured_at,
        )
        for role in key.projection_roles
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    monkeypatch.setattr(
        artifacts,
        "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1",
        artifacts.RunArtifactSetPublicKeyRegistryV1(
            "registry.v1",
            MappingProxyType(
                {
                    "key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "ACTIVE"),
                    "broken": artifacts.RunArtifactSetPublicKeyV1("broken", public_key_b64url, "UNKNOWN"),
                }
            ),
        ),
    )
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_SIGNER_PORT_V1", ("key-1", private_key.sign))

    with pytest.raises(F09ContractError) as caught:
        artifacts.coordinate_run_artifact_set_with_target_refs_v1(
            tmp_path,
            request,
            target_refs_request=artifacts.RunArtifactTargetRefsRequestV1(*refs),
            manifest_outer_ref_request=artifacts.ManifestOuterRefRequestV1(
                None, "f09.run-manifest.v1", None, None, captured_at,
            ),
            existing_manifest=None,
            attempt_id="R41-MALFORMED-UNSELECTED-REGISTRY-KEY",
            now=NOW,
        )

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_SIGNING_KEY_INVALID"


def test_r41_coordinator_rejects_whitespace_signer_key_id(tmp_path, monkeypatch):
    fixture = artifacts.provision_verified_run_manifest_fixture_v1()
    key = fixture.key
    request = artifacts.RunArtifactSetRequestV1(
        key,
        key.run_id,
        fixture.records[0].attempts[0].input_snapshot_refs,
        "f09.run-artifact-fixture.v1",
        {
            "RUN_SNAPSHOT": b"f09.run-fixture.run-snapshot.v1",
            "DECISION_RUN": b"f09.run-fixture.decision-run.v1",
            "FEEDBACK_ATTACHMENT": b"f09.run-fixture.feedback-attachment.v1",
        },
    )
    captured_at = "2026-07-24T00:00:00Z"
    refs = tuple(
        VersionedObjectRef(
            role,
            f"RUN-ARTIFACT:{key.canonical_key_digest.value}:{role}",
            None,
            "f09.run-artifact-fixture.v1",
            None,
            DigestPresent("PRESENT", key.projection_digest_by_role[role]),
            None,
            captured_at,
        )
        for role in key.projection_roles
    )
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_SIGNER_PORT_V1", (" ", lambda payload: b"A" * 64))

    with pytest.raises(F09ContractError) as caught:
        artifacts.coordinate_run_artifact_set_with_target_refs_v1(
            tmp_path,
            request,
            target_refs_request=artifacts.RunArtifactTargetRefsRequestV1(*refs),
            manifest_outer_ref_request=artifacts.ManifestOuterRefRequestV1(
                None, "f09.run-manifest.v1", None, None, captured_at,
            ),
            existing_manifest=None,
            attempt_id="R41-WHITESPACE-SIGNER-KEY",
            now=NOW,
        )

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_SIGNER_UNAVAILABLE"


def test_r41_public_verifier_rejects_target_ref_tamper_after_signing(monkeypatch):
    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    captured_at = "2026-07-24T00:00:00Z"
    capture_refs = tuple(
        VersionedObjectRef(
            record.artifact_role,
            record.artifact_id,
            None,
            record.schema_version,
            None,
            DigestPresent("PRESENT", record.observed_digest),
            None,
            captured_at,
        )
        for record in manifest.records
    )
    records_digest = artifacts.validate_run_artifact_manifest_v1(manifest)
    target_refs = capture_refs + (
        VersionedObjectRef(
            "MANIFEST", manifest.manifest_id, None, "f09.run-manifest.v1", None,
            DigestPresent("PRESENT", records_digest), None, captured_at,
        ),
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    monkeypatch.setattr(
        artifacts,
        "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1",
        artifacts.RunArtifactSetPublicKeyRegistryV1(
            "registry.v1",
            MappingProxyType({"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "ACTIVE")}),
        ),
    )
    payload = artifacts.canonicalize_run_artifact_set_issuance_payload_v1(manifest, target_refs)
    proof = artifacts.IssuedRunArtifactSetProofV1(
        "Ed25519", "key-1", base64.urlsafe_b64encode(private_key.sign(payload)).rstrip(b"=").decode("ascii"),
    )
    tampered_target_refs = (replace(target_refs[0], captured_at="2026-07-25T00:00:00Z"),) + target_refs[1:]

    with pytest.raises(F09ContractError) as caught:
        artifacts.validate_run_artifact_set_result_issuance_v1(
            artifacts.RunArtifactSetResultV1(manifest, tampered_target_refs, proof)
        )

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_SIGNING_FAILED"


def test_r41_public_verifier_rejects_signature_with_ignored_non_base64url_infix(monkeypatch):
    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    captured_at = "2026-07-24T00:00:00Z"
    capture_refs = tuple(
        VersionedObjectRef(
            record.artifact_role,
            record.artifact_id,
            None,
            record.schema_version,
            None,
            DigestPresent("PRESENT", record.observed_digest),
            None,
            captured_at,
        )
        for record in manifest.records
    )
    records_digest = artifacts.validate_run_artifact_manifest_v1(manifest)
    target_refs = capture_refs + (
        VersionedObjectRef(
            "MANIFEST", manifest.manifest_id, None, "f09.run-manifest.v1", None,
            DigestPresent("PRESENT", records_digest), None, captured_at,
        ),
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    monkeypatch.setattr(
        artifacts,
        "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1",
        artifacts.RunArtifactSetPublicKeyRegistryV1(
            "registry.v1",
            MappingProxyType({"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "ACTIVE")}),
        ),
    )
    payload = artifacts.canonicalize_run_artifact_set_issuance_payload_v1(manifest, target_refs)
    signature_b64url = base64.urlsafe_b64encode(private_key.sign(payload)).rstrip(b"=").decode("ascii")
    proof = artifacts.IssuedRunArtifactSetProofV1(
        "Ed25519", "key-1", signature_b64url[:8] + "!!!!" + signature_b64url[8:],
    )

    with pytest.raises(F09ContractError) as caught:
        artifacts.validate_run_artifact_set_result_issuance_v1(
            artifacts.RunArtifactSetResultV1(manifest, target_refs, proof)
        )

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_INVALID"


def test_r41_coordinator_rejects_non_64_byte_signer_output(tmp_path, monkeypatch):
    fixture = artifacts.provision_verified_run_manifest_fixture_v1()
    key = fixture.key
    request = artifacts.RunArtifactSetRequestV1(
        key,
        key.run_id,
        fixture.records[0].attempts[0].input_snapshot_refs,
        "f09.run-artifact-fixture.v1",
        {
            "RUN_SNAPSHOT": b"f09.run-fixture.run-snapshot.v1",
            "DECISION_RUN": b"f09.run-fixture.decision-run.v1",
            "FEEDBACK_ATTACHMENT": b"f09.run-fixture.feedback-attachment.v1",
        },
    )
    captured_at = "2026-07-24T00:00:00Z"
    refs = tuple(
        VersionedObjectRef(
            role,
            f"RUN-ARTIFACT:{key.canonical_key_digest.value}:{role}",
            None,
            "f09.run-artifact-fixture.v1",
            None,
            DigestPresent("PRESENT", key.projection_digest_by_role[role]),
            None,
            captured_at,
        )
        for role in key.projection_roles
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    monkeypatch.setattr(
        artifacts,
        "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1",
        artifacts.RunArtifactSetPublicKeyRegistryV1(
            "registry.v1",
            MappingProxyType({"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "ACTIVE")}),
        ),
    )
    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_SIGNER_PORT_V1", ("key-1", lambda payload: b"A" * 63))

    with pytest.raises(F09ContractError) as caught:
        artifacts.coordinate_run_artifact_set_with_target_refs_v1(
            tmp_path,
            request,
            target_refs_request=artifacts.RunArtifactTargetRefsRequestV1(*refs),
            manifest_outer_ref_request=artifacts.ManifestOuterRefRequestV1(
                None, "f09.run-manifest.v1", None, None, captured_at,
            ),
            existing_manifest=None,
            attempt_id="R41-INVALID-SIGNER-OUTPUT",
            now=NOW,
        )

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_SIGNING_FAILED"


def test_r41_coordinator_wraps_signer_exception(tmp_path, monkeypatch):
    fixture = artifacts.provision_verified_run_manifest_fixture_v1()
    key = fixture.key
    request = artifacts.RunArtifactSetRequestV1(
        key,
        key.run_id,
        fixture.records[0].attempts[0].input_snapshot_refs,
        "f09.run-artifact-fixture.v1",
        {
            "RUN_SNAPSHOT": b"f09.run-fixture.run-snapshot.v1",
            "DECISION_RUN": b"f09.run-fixture.decision-run.v1",
            "FEEDBACK_ATTACHMENT": b"f09.run-fixture.feedback-attachment.v1",
        },
    )
    captured_at = "2026-07-24T00:00:00Z"
    refs = tuple(
        VersionedObjectRef(
            role,
            f"RUN-ARTIFACT:{key.canonical_key_digest.value}:{role}",
            None,
            "f09.run-artifact-fixture.v1",
            None,
            DigestPresent("PRESENT", key.projection_digest_by_role[role]),
            None,
            captured_at,
        )
        for role in key.projection_roles
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    monkeypatch.setattr(
        artifacts,
        "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1",
        artifacts.RunArtifactSetPublicKeyRegistryV1(
            "registry.v1",
            MappingProxyType({"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "ACTIVE")}),
        ),
    )

    def fail_signer(payload):
        raise RuntimeError("signer failure")

    monkeypatch.setattr(artifacts, "_RUN_ARTIFACT_SET_SIGNER_PORT_V1", ("key-1", fail_signer))

    with pytest.raises(F09ContractError) as caught:
        artifacts.coordinate_run_artifact_set_with_target_refs_v1(
            tmp_path,
            request,
            target_refs_request=artifacts.RunArtifactTargetRefsRequestV1(*refs),
            manifest_outer_ref_request=artifacts.ManifestOuterRefRequestV1(
                None, "f09.run-manifest.v1", None, None, captured_at,
            ),
            existing_manifest=None,
            attempt_id="R41-SIGNER-EXCEPTION",
            now=NOW,
        )

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_SIGNING_FAILED"



def test_r41_public_verifier_rejects_noncanonical_base64url_signature_pad_bits(monkeypatch):
    manifest = artifacts.provision_verified_run_manifest_fixture_v1()
    captured_at = "2026-07-24T00:00:00Z"
    capture_refs = tuple(
        VersionedObjectRef(
            record.artifact_role,
            record.artifact_id,
            None,
            record.schema_version,
            None,
            DigestPresent("PRESENT", record.observed_digest),
            None,
            captured_at,
        )
        for record in manifest.records
    )
    records_digest = artifacts.validate_run_artifact_manifest_v1(manifest)
    target_refs = capture_refs + (
        VersionedObjectRef(
            "MANIFEST", manifest.manifest_id, None, "f09.run-manifest.v1", None,
            DigestPresent("PRESENT", records_digest), None, captured_at,
        ),
    )
    private_key = Ed25519PrivateKey.generate()
    public_key_b64url = base64.urlsafe_b64encode(
        private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).rstrip(b"=").decode("ascii")
    monkeypatch.setattr(
        artifacts,
        "_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1",
        artifacts.RunArtifactSetPublicKeyRegistryV1(
            "registry.v1",
            MappingProxyType({"key-1": artifacts.RunArtifactSetPublicKeyV1("key-1", public_key_b64url, "ACTIVE")}),
        ),
    )
    payload = artifacts.canonicalize_run_artifact_set_issuance_payload_v1(manifest, target_refs)
    signature_b64url = base64.urlsafe_b64encode(private_key.sign(payload)).rstrip(b"=").decode("ascii")
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    last_index = alphabet.index(signature_b64url[-1])
    noncanonical_signature_b64url = signature_b64url[:-1] + alphabet[(last_index & 0b110000) | ((last_index + 1) & 0b001111)]
    proof = artifacts.IssuedRunArtifactSetProofV1("Ed25519", "key-1", noncanonical_signature_b64url)

    with pytest.raises(F09ContractError) as caught:
        artifacts.validate_run_artifact_set_result_issuance_v1(
            artifacts.RunArtifactSetResultV1(manifest, target_refs, proof)
        )

    assert caught.value.issue_code == "RUN_ARTIFACT_SET_REGISTRY_INVALID"
