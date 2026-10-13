from __future__ import annotations

import base64
import hashlib
import os
from collections.abc import Mapping
from dataclasses import dataclass, replace
from types import MappingProxyType
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Literal
from uuid import uuid4

from engine.f09.contracts import (
    AbsentDeclarationBinding,
    ArtifactItemState,
    ArtifactSetState,
    DetectedIssue,
    DigestRef,
    FrozenDeclarationRef,
    NotApplicableDeclarationBinding,
    ResolvedDeclarationBinding,
    RunTrack,
    UnavailableDeclarationBinding,
    UnresolvableDeclarationBinding,
)
from engine.f09.decision import DecisionEvaluationResult
from engine.f09.evidence import NormalizedEvidencePackage
from engine.f09.canonical_json import JcsValue, canonicalize_bounded_jcs
from engine.f09.errors import F09ContractError, F09IntegrityError, F09WriteError
from engine.f09.canonical_json import bounded_jcs_sha256
from engine.f09.trace import (
    DigestMissing,
    CardIdentityRef,
    DigestPresent,
    ProjectionValidationResult,
    StandardStatement,
    StatementSet,
    TraceEnvelope,
    VersionedObjectRef,
    validate_statement_projection,
)


_REQUIRED_ROLES = ("REPORT", "STATEMENT_RECORDS", "STATEMENT_INDEX")
_ROLE_FILENAMES = {
    "REPORT": "report.bin",
    "STATEMENT_RECORDS": "statement_records.bin",
    "STATEMENT_INDEX": "statement_index.bin",
}
_LEGAL_ITEM_STATE_VALUES = (
    "NOT_ATTEMPTED",
    "WRITING",
    "WRITTEN_UNVERIFIED",
    "VERIFIED",
    "FAILED",
    "STALE",
    "MISMATCH",
    "SUPERSEDED",
)


@dataclass(frozen=True)
class IdempotencyKey:
    operation: Literal[
        "NORMALIZE",
        "DECIDE",
        "BUILD_STATEMENT_SET",
        "RENDER_REPORT",
        "PROJECT_INDEX",
        "PROJECT_RECORDS",
        "PROJECT_ARTIFACT_SET",
        "BIND_FEEDBACK",
        "EVALUATE_LEARNING_ELIGIBILITY",
        "INGEST_FEEDBACK",
    ]
    case_id: str
    track: RunTrack
    source_digest: DigestRef
    schema_versions_digest: DigestRef
    contract_digest: DigestRef | None
    statement_set_id: str | None
    feedback_id: str | None
    canonical_key_digest: DigestRef


@dataclass(frozen=True)
class RunArtifactSetKeyV1:
    operation: Literal["PROJECT_RUN_ARTIFACT_SET"]
    case_id: str
    track: RunTrack
    run_id: str
    source_digest: DigestRef
    schema_versions_digest: DigestRef
    contract_digest: DigestRef
    input_snapshot_refs_graph_digest: DigestRef
    projection_roles: tuple[Literal["RUN_SNAPSHOT", "DECISION_RUN", "FEEDBACK_ATTACHMENT"], ...]
    projection_digest_by_role: Mapping[str, DigestRef]
    canonical_key_digest: DigestRef


@dataclass(frozen=True)
class RunArtifactSetRequestV1:
    key: RunArtifactSetKeyV1
    run_id: str
    input_snapshot_refs: tuple[VersionedObjectRef, ...]
    schema_version: str
    projections: Mapping[Literal["RUN_SNAPSHOT", "DECISION_RUN", "FEEDBACK_ATTACHMENT"], bytes]


@dataclass(frozen=True)
class RunArtifactTargetRefsRequestV1:
    run_snapshot_ref: VersionedObjectRef
    decision_run_ref: VersionedObjectRef
    feedback_attachment_ref: VersionedObjectRef


@dataclass(frozen=True)
class ManifestOuterRefRequestV1:
    revision_id: str | None
    schema_version: str
    contract_version: str | None
    source_locator_id: str | None
    captured_at: str | None


@dataclass(frozen=True)
class RunArtifactSetPublicKeyV1:
    key_id: str
    public_key_b64url: str
    status: Literal["ACTIVE", "REVOKED"]


@dataclass(frozen=True)
class RunArtifactSetPublicKeyRegistryV1:
    registry_version: str
    keys_by_id: Mapping[str, RunArtifactSetPublicKeyV1]


@dataclass(frozen=True)
class IssuedRunArtifactSetProofV1:
    algorithm: Literal["Ed25519"]
    key_id: str
    signature_b64url: str


@dataclass(frozen=True)
class RunArtifactSetResultV1:
    manifest: ArtifactSetManifest
    target_refs: tuple[VersionedObjectRef, ...]
    issuance_proof: IssuedRunArtifactSetProofV1


_RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1: RunArtifactSetPublicKeyRegistryV1 | None = None
_RUN_ARTIFACT_SET_SIGNER_PORT_V1: object | None = None


def _base64url_decode(value: str, *, field_path: str) -> bytes:
    if type(value) is not str or not value or "=" in value or any(character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for character in value):
        raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", field_path, "expected unpadded base64url")
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except Exception as error:
        raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", field_path, "invalid base64url") from error
    if base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii") != value:
        raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", field_path, "noncanonical base64url")
    return decoded


def _install_run_artifact_set_public_key_registry_v1(*, registry: RunArtifactSetPublicKeyRegistryV1) -> None:
    global _RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1
    if _RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1 is not None:
        raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof", "registry already installed")
    if (
        type(registry) is not RunArtifactSetPublicKeyRegistryV1
        or type(registry.registry_version) is not str
        or not registry.registry_version.strip()
        or type(registry.keys_by_id) is not MappingProxyType
    ):
        raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof", "invalid registry")
    copied: dict[str, RunArtifactSetPublicKeyV1] = {}
    for key_id, key in registry.keys_by_id.items():
        if type(key_id) is not str or not key_id.strip() or type(key) is not RunArtifactSetPublicKeyV1 or type(key.key_id) is not str or key.key_id != key_id or type(key.status) is not str or key.status not in ("ACTIVE", "REVOKED") or len(_base64url_decode(key.public_key_b64url, field_path="issuance_proof")) != 32:
            raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof", "invalid public key")
        copied[key_id] = RunArtifactSetPublicKeyV1(key.key_id, key.public_key_b64url, key.status)
    _RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1 = RunArtifactSetPublicKeyRegistryV1(registry.registry_version, MappingProxyType(copied))


def get_run_artifact_set_public_key_registry_v1() -> RunArtifactSetPublicKeyRegistryV1:
    if _RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1 is None:
        raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_UNAVAILABLE", "issuance_proof", "registry is not provisioned")
    return _RUN_ARTIFACT_SET_PUBLIC_KEY_REGISTRY_V1


def _install_run_artifact_set_signer_port_v1(*, key_id: str, private_key: object) -> None:
    global _RUN_ARTIFACT_SET_SIGNER_PORT_V1
    if _RUN_ARTIFACT_SET_SIGNER_PORT_V1 is not None:
        raise F09ContractError("RUN_ARTIFACT_SET_SIGNING_KEY_INVALID", "issuance_proof", "signer already installed")
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        registry = get_run_artifact_set_public_key_registry_v1()
        if type(key_id) is not str or not key_id.strip() or not isinstance(private_key, Ed25519PrivateKey):
            raise ValueError("invalid signer material")
        public_key = registry.keys_by_id.get(key_id)
        public_key_b64url = base64.urlsafe_b64encode(
            private_key.public_key().public_bytes(
                serialization.Encoding.Raw,
                serialization.PublicFormat.Raw,
            )
        ).rstrip(b"=").decode("ascii")
        if (
            type(public_key) is not RunArtifactSetPublicKeyV1
            or type(public_key.status) is not str
            or public_key.status != "ACTIVE"
            or type(public_key.key_id) is not str
            or public_key.key_id != key_id
            or type(public_key.public_key_b64url) is not str
            or public_key.public_key_b64url != public_key_b64url
        ):
            raise ValueError("signing key does not match active registry key")
    except Exception as error:
        raise F09ContractError(
            "RUN_ARTIFACT_SET_SIGNING_KEY_INVALID",
            "issuance_proof",
            "invalid signing key",
        ) from error
    _RUN_ARTIFACT_SET_SIGNER_PORT_V1 = (key_id, private_key.sign)


@dataclass(frozen=True)
class ArtifactOperationAuthority:
    projections: Mapping[str, bytes]
    key: IdempotencyKey


def build_artifact_operation_authority(
    package: NormalizedEvidencePackage,
    decision: DecisionEvaluationResult,
    trace: TraceEnvelope,
    statement_set: StatementSet,
    *,
    normative_contract_ref: VersionedObjectRef,
    machine_appendix_ref: VersionedObjectRef,
) -> ArtifactOperationAuthority:
    guards = (
        (package, NormalizedEvidencePackage, "/artifact_authority/package"),
        (decision, DecisionEvaluationResult, "/artifact_authority/decision"),
        (trace, TraceEnvelope, "/artifact_authority/trace"),
        (statement_set, StatementSet, "/artifact_authority/statement_set"),
        (normative_contract_ref, VersionedObjectRef, "/artifact_authority/normative_contract_ref"),
        (machine_appendix_ref, VersionedObjectRef, "/artifact_authority/machine_appendix_ref"),
    )
    for value, expected_type, field_path in guards:
        if type(value) is not expected_type:
            raise F09ContractError(
                "ARTIFACT.AUTHORITY_INVALID",
                field_path,
                "artifact authority requires exact top-level runtime types",
            )
    projection_validation = validate_statement_projection(
        statement_set,
        trace,
        decision,
        package,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
    )
    if (
        type(projection_validation) is not ProjectionValidationResult
        or projection_validation.valid is not True
        or projection_validation.detected_issues != ()
    ):
        raise F09IntegrityError(
            "ARTIFACT.PROJECTION_VALIDATION_FAILED",
            "/artifact_authority/projection_validation",
            "statement projection validation did not return strict success",
        )
    for ordinal, statement in enumerate(statement_set.statements):
        if type(statement.card_identity_refs) is not tuple or len(statement.card_identity_refs) != 1:
            raise F09ContractError(
                "ARTIFACT.AUTHORITY_INVALID",
                f"/artifact_authority/statements/{ordinal}/card_identity_refs",
                "artifact authority requires exactly one card identity ref material container per statement",
            )
        if type(statement.card_identity_refs[0]) is not CardIdentityRef:
            raise _authority_material_error("/artifact_authority/projection_material")
    material_path = "/artifact_authority/projection_material"
    try:
        roots = {
            "REPORT": _artifact_root_material(
                "REPORT", statement_set, decision, normative_contract_ref, machine_appendix_ref
            ),
            "STATEMENT_RECORDS": _artifact_root_material(
                "STATEMENT_RECORDS", statement_set, decision, normative_contract_ref, machine_appendix_ref
            ),
            "STATEMENT_INDEX": _artifact_root_material(
                "STATEMENT_INDEX", statement_set, decision, normative_contract_ref, machine_appendix_ref
            ),
        }
    except (AttributeError, TypeError) as error:
        raise _authority_material_error(material_path) from error
    projections = {role: canonicalize_bounded_jcs(roots[role]) for role in _REQUIRED_ROLES}
    projection_digests = {
        role: DigestRef("sha256", "RAW-UTF8", sha256(projections[role]).hexdigest())
        for role in _REQUIRED_ROLES
    }
    source_digest = bounded_jcs_sha256(
        {
            "operation": "PROJECT_ARTIFACT_SET",
            "case_id": statement_set.case_id,
            "track": statement_set.track.value,
            "statement_set_id": statement_set.statement_set_id,
            "statement_set_content_digest": _digest_material(statement_set.content_digest, field_path=material_path),
            "projection_digests": tuple(
                {"artifact_role": role, "digest": _digest_material(projection_digests[role], field_path=material_path)}
                for role in _REQUIRED_ROLES
            ),
        }
    )
    schema_versions_digest = bounded_jcs_sha256(
        {
            "authority_schema_version": "f09.artifact-operation-authority.v1",
            "projection_contract_version": "f09.artifact-projection.v1",
            "projection_schemas": tuple(
                {
                    "artifact_role": role,
                    "schema_version": _artifact_role_material(role, field_path=material_path)["schema_version"],
                    "statement_schema_version": statement_set.statement_schema_version,
                    "trace_schema_version": trace.trace_schema_version,
                }
                for role in _REQUIRED_ROLES
            ),
        }
    )
    contract_digest = bounded_jcs_sha256(
        {
            "normative_contract_ref": _versioned_object_ref_material(normative_contract_ref, field_path=material_path),
            "machine_appendix_ref": _versioned_object_ref_material(machine_appendix_ref, field_path=material_path),
            "decision_contract_ref": {
                "normative_contract_path": decision.contract_ref.normative_contract_path,
                "machine_appendix_path": decision.contract_ref.machine_appendix_path,
                "contract_version": decision.contract_ref.contract_version,
                "content_digest": decision.contract_ref.content_digest,
            },
        }
    )
    key_material = {
        "operation": "PROJECT_ARTIFACT_SET",
        "case_id": statement_set.case_id,
        "track": statement_set.track.value,
        "source_digest": _digest_material(source_digest, field_path=material_path),
        "schema_versions_digest": _digest_material(schema_versions_digest, field_path=material_path),
        "contract_digest": _digest_material(contract_digest, field_path=material_path),
        "statement_set_id": statement_set.statement_set_id,
        "feedback_id": None,
    }
    canonical_key_bytes = canonicalize_bounded_jcs(key_material)
    canonical_key_value = sha256(canonical_key_bytes).hexdigest()
    if _independent_sha256(canonical_key_bytes) != canonical_key_value:
        raise F09IntegrityError(
            "IDEMPOTENCY.DIGEST_MISMATCH",
            "/artifact_authority/key/canonical_key_digest",
            "artifact authority canonical key digest mismatch",
        )
    key = IdempotencyKey(
        "PROJECT_ARTIFACT_SET",
        statement_set.case_id,
        statement_set.track,
        source_digest,
        schema_versions_digest,
        contract_digest,
        statement_set.statement_set_id,
        None,
        DigestRef("sha256", "RFC8785-JCS-UTF8", canonical_key_value),
    )
    return ArtifactOperationAuthority(MappingProxyType(dict(projections)), key)


def _independent_sha256(payload: bytes) -> str:
    return hashlib.new("sha256", payload).hexdigest()


def _artifact_root_material(
    role: Literal["REPORT", "STATEMENT_RECORDS", "STATEMENT_INDEX"],
    statement_set: StatementSet,
    decision: DecisionEvaluationResult,
    normative_contract_ref: VersionedObjectRef,
    machine_appendix_ref: VersionedObjectRef,
) -> dict[str, JcsValue]:
    path = "/artifact_authority/projection_material"
    root = _artifact_role_material(role, field_path=path)
    root.update(
        {
            "case_id": statement_set.case_id,
            "track": statement_set.track.value,
            "statement_set_id": statement_set.statement_set_id,
            "statement_set_schema_version": statement_set.statement_schema_version,
            "statement_set_content_digest": _digest_material(statement_set.content_digest, field_path=path),
            "source_package_ref": _versioned_object_ref_material(statement_set.source_package_ref, field_path=path),
            "normative_contract_ref": _versioned_object_ref_material(normative_contract_ref, field_path=path),
            "machine_appendix_ref": _versioned_object_ref_material(machine_appendix_ref, field_path=path),
            "payload": _artifact_payload_material(role, statement_set, path),
        }
    )
    return root


def _artifact_payload_material(role: str, statement_set: StatementSet, field_path: str) -> dict[str, JcsValue]:
    statements = statement_set.statements
    common = {
        "generated_at": statement_set.generated_at,
        "publication_state": statement_set.publication_state,
    }
    if role == "REPORT":
        return {
            **common,
            "statement_count": str(len(statements)),
            "sections": tuple(_report_section_material(statement, field_path) for statement in statements),
        }
    if role == "STATEMENT_RECORDS":
        return {**common, "statements": tuple(_standard_statement_material(statement, field_path) for statement in statements)}
    if role == "STATEMENT_INDEX":
        return {
            **common,
            "entries": tuple(
                _statement_index_material(index, statement, field_path)
                for index, statement in enumerate(statements, 1)
            ),
        }
    raise _authority_material_error(field_path)


def _versioned_object_ref_material(ref: VersionedObjectRef, *, field_path: str) -> dict[str, JcsValue]:
    if type(ref) is not VersionedObjectRef:
        raise _authority_material_error(field_path)
    return {
        "object_type": ref.object_type,
        "object_id": ref.object_id,
        "revision_id": ref.revision_id,
        "schema_version": ref.schema_version,
        "contract_version": ref.contract_version,
        "digest_binding": _digest_binding_material(ref.digest_binding, field_path=field_path),
        "source_locator_id": ref.source_locator_id,
        "captured_at": ref.captured_at,
    }


def _frozen_declaration_ref_material(ref: FrozenDeclarationRef, *, field_path: str) -> dict[str, JcsValue]:
    if type(ref) is not FrozenDeclarationRef:
        raise _authority_material_error(field_path)
    return {
        "declaration_id": ref.declaration_id,
        "declaration_type": ref.declaration_type,
        "card_id": ref.card_id,
        "contract_version": ref.contract_version,
        "declaration_schema_version": ref.declaration_schema_version,
        "content_digest": _digest_material(ref.content_digest, field_path=field_path),
    }


def _declaration_binding_material(binding: object, *, field_path: str) -> dict[str, JcsValue]:
    if type(binding) is ResolvedDeclarationBinding:
        return {"presence": binding.presence, "ref": _frozen_declaration_ref_material(binding.ref, field_path=field_path)}
    if type(binding) in (AbsentDeclarationBinding, NotApplicableDeclarationBinding):
        return {"presence": binding.presence, "reason_code": binding.reason_code}
    if type(binding) is UnavailableDeclarationBinding:
        return {"presence": binding.presence, "reason_code": binding.reason_code, "issue_ids": tuple(binding.issue_ids)}
    if type(binding) is UnresolvableDeclarationBinding:
        return {
            "presence": binding.presence,
            "attempted_ref": _frozen_declaration_ref_material(binding.attempted_ref, field_path=field_path),
            "reason_code": binding.reason_code,
            "issue_ids": tuple(binding.issue_ids),
        }
    raise _authority_material_error(field_path)


def _card_identity_ref_material(ref: CardIdentityRef, *, field_path: str) -> dict[str, JcsValue]:
    if type(ref) is not CardIdentityRef:
        raise _authority_material_error(field_path)
    return {
        "card_identity_ref_id": ref.card_identity_ref_id,
        "card_id": ref.card_id,
        "normative_contract_ref": _versioned_object_ref_material(ref.normative_contract_ref, field_path=field_path),
        "machine_appendix_ref": _versioned_object_ref_material(ref.machine_appendix_ref, field_path=field_path),
        "field_path": ref.field_path,
        "source_field_state": ref.source_field_state,
        "evaluator_state": ref.evaluator_state.value,
        "declaration_status": ref.declaration_status,
        "runtime_capability_status": ref.runtime_capability_status,
        "source_locator_ids": tuple(ref.source_locator_ids),
        "issue_ids": tuple(ref.issue_ids),
    }


def _standard_statement_material(statement: StandardStatement, field_path: str) -> dict[str, JcsValue]:
    if type(statement) is not StandardStatement:
        raise _authority_material_error(field_path)
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
        "evidence_refs": tuple(_versioned_object_ref_material(ref, field_path=field_path) for ref in statement.evidence_refs),
        "relation_ids": tuple(statement.relation_ids),
        "source_locator_ids": tuple(statement.source_locator_ids),
        "card_identity_refs": tuple(_card_identity_ref_material(ref, field_path=field_path) for ref in statement.card_identity_refs),
        "confidence_snapshot_ref": None if statement.confidence_snapshot_ref is None else _versioned_object_ref_material(statement.confidence_snapshot_ref, field_path=field_path),
        "output_precision_binding": _declaration_binding_material(statement.output_precision_binding, field_path=field_path),
        "validation_plan_binding": _declaration_binding_material(statement.validation_plan_binding, field_path=field_path),
        "feedback_policy": statement.feedback_policy,
        "content_digest": _digest_material(statement.content_digest, field_path=field_path),
        "integrity": statement.integrity,
        "issue_ids": tuple(statement.issue_ids),
    }


def _report_section_material(statement: StandardStatement, field_path: str) -> dict[str, JcsValue]:
    if type(statement) is not StandardStatement:
        raise _authority_material_error(field_path)
    return {
        "statement_id": statement.statement_id,
        "statement_revision_id": statement.statement_revision_id,
        "domain": statement.domain,
        "semantic_scope": statement.semantic_scope,
        "display_section": statement.display_section,
        "statement_text": statement.statement_text,
        "feedback_policy": statement.feedback_policy,
        "integrity": statement.integrity,
        "issue_ids": tuple(statement.issue_ids),
        "content_digest": _digest_material(statement.content_digest, field_path=field_path),
    }


def _statement_index_material(ordinal: int, statement: StandardStatement, field_path: str) -> dict[str, JcsValue]:
    if type(statement) is not StandardStatement:
        raise _authority_material_error(field_path)
    return {
        "ordinal": str(ordinal),
        "statement_id": statement.statement_id,
        "statement_revision_id": statement.statement_revision_id,
        "statement_schema_version": statement.statement_schema_version,
        "domain": statement.domain,
        "semantic_scope": statement.semantic_scope,
        "display_section": statement.display_section,
        "feedback_policy": statement.feedback_policy,
        "integrity": statement.integrity,
        "content_digest": _digest_material(statement.content_digest, field_path=field_path),
    }


def _authority_material_error(field_path: str) -> F09ContractError:
    return F09ContractError(
        "ARTIFACT.AUTHORITY_INVALID",
        field_path,
        "artifact authority projection material is not serialization-closed",
    )


def _digest_material(digest: DigestRef, *, field_path: str) -> dict[str, JcsValue]:
    if type(digest) is not DigestRef:
        raise _authority_material_error(field_path)
    return {
        "algorithm": digest.algorithm,
        "canonicalization": digest.canonicalization,
        "value": digest.value,
    }


def _digest_binding_material(
    binding: DigestPresent | DigestMissing,
    *,
    field_path: str,
) -> dict[str, JcsValue]:
    if type(binding) is DigestPresent:
        try:
            digest = binding.digest
        except AttributeError as error:
            raise _authority_material_error(field_path) from error
        return {
            "status": "PRESENT",
            "digest": _digest_material(digest, field_path=field_path),
        }
    if type(binding) is DigestMissing:
        try:
            issue_id = binding.issue_id
        except AttributeError as error:
            raise _authority_material_error(field_path) from error
        return {"status": "MISSING", "digest": None, "issue_id": issue_id}
    raise _authority_material_error(field_path)


def _artifact_role_material(
    role: Literal["REPORT", "STATEMENT_RECORDS", "STATEMENT_INDEX"],
    *,
    field_path: str,
) -> dict[str, JcsValue]:
    roles = {
        "REPORT": ("f09.report-projection.v1", "f09.artifact-projection.v1"),
        "STATEMENT_RECORDS": ("f09.statement-records-projection.v1", "f09.artifact-projection.v1"),
        "STATEMENT_INDEX": ("f09.statement-index-projection.v1", "f09.artifact-projection.v1"),
    }
    if type(role) is not str or role not in roles:
        raise _authority_material_error(field_path)
    schema_version, contract_version = roles[role]
    return {
        "artifact_role": role,
        "schema_version": schema_version,
        "contract_version": contract_version,
    }


@dataclass(frozen=True)
class ArtifactWriteAttempt:
    attempt_id: str
    artifact_id: str
    idempotency_key: str
    attempt_number: int
    retry_of_attempt_id: str | None
    input_snapshot_refs: tuple[VersionedObjectRef, ...]
    started_at: str
    finished_at: str | None
    outcome: Literal["SUCCEEDED", "FAILED", "UNKNOWN"]
    observed_digest: DigestRef | None
    error_class: str | None
    error_message_digest: DigestRef | None


@dataclass(frozen=True)
class ArtifactRecord:
    artifact_id: str
    artifact_role: Literal[
        "REPORT",
        "STATEMENT_INDEX",
        "STATEMENT_RECORDS",
        "RUN_SNAPSHOT",
        "DECISION_RUN",
        "FEEDBACK_ATTACHMENT",
        "MANIFEST",
        "FEEDBACK_SOURCE",
    ]
    track: RunTrack
    case_id: str
    statement_set_id: str | None
    run_id: str | None
    path_locator: str
    schema_version: str | None
    expected_digest: DigestRef | None
    observed_digest: DigestRef | None
    state: ArtifactItemState
    attempts: tuple[ArtifactWriteAttempt, ...]
    issue_ids: tuple[str, ...]


@dataclass(frozen=True)
class ArtifactSetManifest:
    manifest_id: str
    key: IdempotencyKey | RunArtifactSetKeyV1
    records: tuple[ArtifactRecord, ...]
    state: ArtifactSetState
    digest: DigestRef
    detected_issues: tuple[DetectedIssue, ...]


def resolve_artifact_operation_root(root: Path, key: IdempotencyKey) -> Path:
    if not isinstance(root, Path) or not isinstance(key, IdempotencyKey):
        raise F09ContractError(
            "ARTIFACT.STATE_INVALID",
            "/canonical_key_digest",
            "operation-root input has invalid shape",
        )
    digest = key.canonical_key_digest
    value = digest.value if isinstance(digest, DigestRef) else ""
    component = Path(value)
    if (
        not isinstance(digest, DigestRef)
        or digest.algorithm != "sha256"
        or digest.canonicalization != "RFC8785-JCS-UTF8"
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
        or component.is_absolute()
        or bool(component.drive)
        or bool(component.anchor)
        or component.parts != (value,)
        or value in (".", "..")
    ):
        raise F09IntegrityError(
            "IDEMPOTENCY.DIGEST_MISMATCH",
            "/canonical_key_digest",
            "operation identity is not one lowercase SHA-256 path component",
        )
    resolved_root = root.resolve(strict=False)
    candidate = (resolved_root / value).resolve(strict=False)
    try:
        contained = candidate.is_relative_to(resolved_root)
    except AttributeError:
        contained = resolved_root in candidate.parents
    if candidate == resolved_root or not contained:
        raise F09IntegrityError(
            "IDEMPOTENCY.DIGEST_MISMATCH",
            "/canonical_key_digest",
            "operation root escapes the authorized artifact root",
        )
    return candidate


def _digest_ref_material(digest: DigestRef | None) -> object:
    if digest is None:
        return None
    return {
        "algorithm": digest.algorithm,
        "canonicalization": digest.canonicalization,
        "value": digest.value,
    }


def _versioned_ref_material(ref: VersionedObjectRef) -> dict[str, object]:
    binding = ref.digest_binding
    return {
        "object_type": ref.object_type,
        "object_id": ref.object_id,
        "revision_id": ref.revision_id,
        "schema_version": ref.schema_version,
        "contract_version": ref.contract_version,
        "digest_status": binding.status,
        "digest": _digest_ref_material(binding.digest),
        "source_locator_id": ref.source_locator_id,
        "captured_at": ref.captured_at,
    }


def _digest_run_input_snapshot_refs_v1(refs: tuple[VersionedObjectRef, ...]) -> DigestRef:
    if type(refs) is not tuple or any(type(ref) is not VersionedObjectRef for ref in refs):
        raise F09ContractError(
            "RUN_ARTIFACT.REFS_INVALID",
            "/input_snapshot_refs",
            "run input snapshot refs must be an exact tuple of versioned object refs",
        )
    return DigestRef(
        "sha256",
        "RFC8785-JCS-UTF8",
        sha256(canonicalize_bounded_jcs(tuple(_versioned_ref_material(ref) for ref in refs))).hexdigest(),
    )


def _run_digest_material(digest: DigestRef, field_path: str) -> dict[str, JcsValue]:
    if type(digest) is not DigestRef or not _digest_ref_shape_valid(digest):
        raise F09ContractError("RUN_ARTIFACT.KEY_INVALID", field_path, "run key requires canonical digest refs")
    return {
        "algorithm": digest.algorithm,
        "canonicalization": digest.canonicalization,
        "value": digest.value,
    }


def _digest_run_artifact_set_key_v1(
    *,
    operation: str,
    case_id: str,
    track: RunTrack,
    run_id: str,
    source_digest: DigestRef,
    schema_versions_digest: DigestRef,
    contract_digest: DigestRef,
    input_snapshot_refs_graph_digest: DigestRef,
    projection_roles: tuple[str, ...],
    projection_digest_by_role: Mapping[str, DigestRef],
) -> DigestRef:
    roles = ("RUN_SNAPSHOT", "DECISION_RUN", "FEEDBACK_ATTACHMENT")
    if (
        operation != "PROJECT_RUN_ARTIFACT_SET"
        or not all(isinstance(value, str) and value.strip() for value in (case_id, run_id))
        or type(track) is not RunTrack
        or type(projection_roles) is not tuple
        or projection_roles not in (roles[:2], roles)
        or not isinstance(projection_digest_by_role, Mapping)
        or tuple(projection_digest_by_role) != projection_roles
    ):
        raise F09ContractError("RUN_ARTIFACT.KEY_INVALID", "/key", "run key has invalid closed identity material")
    digest_by_role = {
        role: _run_digest_material(projection_digest_by_role[role], f"/key/projection_digest_by_role/{role}")
        for role in projection_roles
    }
    material: JcsValue = {
        "domain": "f09.run-artifact-set.key.v1",
        "operation": operation,
        "case_id": case_id,
        "track": track.value,
        "run_id": run_id,
        "source_digest": _run_digest_material(source_digest, "/key/source_digest"),
        "schema_versions_digest": _run_digest_material(schema_versions_digest, "/key/schema_versions_digest"),
        "contract_digest": _run_digest_material(contract_digest, "/key/contract_digest"),
        "input_snapshot_refs_graph_digest": _run_digest_material(
            input_snapshot_refs_graph_digest, "/key/input_snapshot_refs_graph_digest"
        ),
        "projection_roles": projection_roles,
        "projection_digest_by_role": digest_by_role,
    }
    return DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(canonicalize_bounded_jcs(material)).hexdigest())


def _digest_run_artifact_set_key_v1_from_key(key: RunArtifactSetKeyV1) -> DigestRef:
    if type(key) is not RunArtifactSetKeyV1:
        raise F09ContractError("RUN_ARTIFACT.KEY_INVALID", "/key", "run key requires exact carrier type")
    return _digest_run_artifact_set_key_v1(
        operation=key.operation,
        case_id=key.case_id,
        track=key.track,
        run_id=key.run_id,
        source_digest=key.source_digest,
        schema_versions_digest=key.schema_versions_digest,
        contract_digest=key.contract_digest,
        input_snapshot_refs_graph_digest=key.input_snapshot_refs_graph_digest,
        projection_roles=key.projection_roles,
        projection_digest_by_role=key.projection_digest_by_role,
    )


def canonicalize_artifact_records(records: tuple[ArtifactRecord, ...]) -> bytes:
    if not isinstance(records, tuple) or any(
        not isinstance(record, ArtifactRecord) for record in records
    ):
        raise F09ContractError(
            "ARTIFACT.STATE_INVALID",
            "/artifacts/0/state",
            "artifact records must be a tuple of canonical records",
        )
    material: list[JcsValue] = []
    for record in records:
        material.append(
            {
                "artifact_id": record.artifact_id,
                "artifact_role": record.artifact_role,
                "track": record.track.value if isinstance(record.track, Enum) else record.track,
                "case_id": record.case_id,
                "statement_set_id": record.statement_set_id,
                "run_id": record.run_id,
                "path_locator": record.path_locator,
                "schema_version": record.schema_version,
                "expected_digest": _digest_ref_material(record.expected_digest),
                "observed_digest": _digest_ref_material(record.observed_digest),
                "state": record.state.value if isinstance(record.state, Enum) else record.state,
                "attempts": tuple(
                    {
                        "attempt_id": attempt.attempt_id,
                        "artifact_id": attempt.artifact_id,
                        "idempotency_key": attempt.idempotency_key,
                        "attempt_number": str(attempt.attempt_number),
                        "retry_of_attempt_id": attempt.retry_of_attempt_id,
                        "input_snapshot_refs": tuple(
                            _versioned_ref_material(ref)
                            for ref in attempt.input_snapshot_refs
                        ),
                        "started_at": attempt.started_at,
                        "finished_at": attempt.finished_at,
                        "outcome": attempt.outcome,
                        "observed_digest": _digest_ref_material(attempt.observed_digest),
                        "error_class": attempt.error_class,
                        "error_message_digest": _digest_ref_material(
                            attempt.error_message_digest
                        ),
                    }
                    for attempt in record.attempts
                ),
                "issue_ids": record.issue_ids,
            }
        )
    return canonicalize_bounded_jcs(tuple(material))


def digest_artifact_records(records: tuple[ArtifactRecord, ...]) -> DigestRef:
    return DigestRef(
        "sha256",
        "RFC8785-JCS-UTF8",
        sha256(canonicalize_artifact_records(records)).hexdigest(),
    )


def _payload_digest(payload: bytes) -> DigestRef:
    return DigestRef("sha256", "RAW-UTF8", sha256(payload).hexdigest())


def _error_digest(error: OSError) -> DigestRef:
    material = (type(error).__name__ + ":" + str(error)).encode("utf-8")
    return DigestRef("sha256", "RAW-UTF8", sha256(material).hexdigest())


def _validate_projections(projections: Mapping[str, bytes]) -> None:
    if (
        not isinstance(projections, Mapping)
        or set(projections) != set(_REQUIRED_ROLES)
        or any(not isinstance(projections[role], bytes) for role in _REQUIRED_ROLES)
    ):
        raise F09ContractError(
            "ARTIFACT.STATE_INVALID",
            "/artifacts/0/state",
            "artifact projections must contain exactly the three required byte roles",
        )


def _atomic_write_verified(target: Path, payload: bytes) -> DigestRef:
    temp = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
    committed = False
    try:
        with temp.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, target)
        committed = True
        observed_bytes = target.read_bytes()
    except OSError:
        if not committed:
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass
        raise
    expected = _payload_digest(payload)
    observed = _payload_digest(observed_bytes)
    if observed_bytes != payload or observed != expected:
        raise F09IntegrityError(
            "ARTIFACT.DIGEST_MISMATCH",
            "/artifacts/observed_digest",
            "committed artifact failed byte and RAW-UTF8 digest verification",
        )
    return observed


def _attempt(
    *,
    attempt_id: str,
    role: str,
    artifact_id: str,
    key: IdempotencyKey,
    number: int,
    retry_of: str | None,
    refs: tuple[VersionedObjectRef, ...],
    now: str,
    outcome: Literal["SUCCEEDED", "FAILED"],
    observed_digest: DigestRef | None,
    error: OSError | None,
) -> ArtifactWriteAttempt:
    return ArtifactWriteAttempt(
        attempt_id=attempt_id + ":" + role,
        artifact_id=artifact_id,
        idempotency_key=key.canonical_key_digest.value,
        attempt_number=number,
        retry_of_attempt_id=retry_of,
        input_snapshot_refs=refs,
        started_at=now,
        finished_at=now,
        outcome=outcome,
        observed_digest=observed_digest,
        error_class=None if error is None else type(error).__name__,
        error_message_digest=None if error is None else _error_digest(error),
    )


def _record(
    *,
    artifact_id: str,
    role: str,
    key: IdempotencyKey,
    target: Path,
    schema_version: str,
    expected_digest: DigestRef,
    observed_digest: DigestRef | None,
    state: ArtifactItemState,
    attempts: tuple[ArtifactWriteAttempt, ...],
) -> ArtifactRecord:
    return ArtifactRecord(
        artifact_id=artifact_id,
        artifact_role=role,
        track=key.track,
        case_id=key.case_id,
        statement_set_id=key.statement_set_id,
        run_id=None,
        path_locator=target.as_posix(),
        schema_version=schema_version,
        expected_digest=expected_digest,
        observed_digest=observed_digest,
        state=state,
        attempts=attempts,
        issue_ids=(),
    )


def _write_issue(role: str) -> tuple[DetectedIssue, ...]:
    if role == "REPORT":
        return ()
    return (DetectedIssue("ARTIFACT.WRITE_FAILED", f"/artifacts/{role}"),)


def _manifest_state_for_failure(role: str) -> ArtifactSetState:
    return ArtifactSetState.FAILED if role == "REPORT" else ArtifactSetState.PARTIAL


def write_artifact_set(
    root: Path,
    statement_set: StatementSet,
    projections: Mapping[str, bytes],
    *,
    key: IdempotencyKey,
    attempt_id: str,
    now: str,
    fail_after: str | None = None,
) -> ArtifactSetManifest:
    if (
        not isinstance(statement_set, StatementSet)
        or not isinstance(key, IdempotencyKey)
        or not isinstance(key.track, RunTrack)
        or key.case_id != statement_set.case_id
        or key.track != statement_set.track
        or key.statement_set_id != statement_set.statement_set_id
        or type(attempt_id) is not str
        or not attempt_id
        or type(now) is not str
        or not now
    ):
        raise F09ContractError(
            "ARTIFACT.STATE_INVALID",
            "/artifacts/0/state",
            "artifact write prerequisite has invalid shape or identity",
        )
    _validate_projections(projections)
    if fail_after not in (None, "STATEMENT_RECORDS", "STATEMENT_INDEX"):
        raise F09ContractError(
            "ARTIFACT.STATE_INVALID",
            "/artifacts/0/state",
            "failure injection is restricted to phase-owned projection roles",
        )
    operation_root = resolve_artifact_operation_root(root, key)
    records: tuple[ArtifactRecord, ...] = ()
    for role in _REQUIRED_ROLES:
        payload = projections[role]
        expected = _payload_digest(payload)
        target = operation_root / _ROLE_FILENAMES[role]
        artifact_id = f"ARTIFACT:{key.canonical_key_digest.value}:{role}"
        try:
            operation_root.mkdir(parents=True, exist_ok=True)
            if fail_after == role:
                raise OSError("injected canonical write-boundary failure for " + role)
            observed = _atomic_write_verified(target, payload)
        except OSError as error:
            failed_attempt = _attempt(
                attempt_id=attempt_id,
                role=role,
                artifact_id=artifact_id,
                key=key,
                number=1,
                retry_of=None,
                refs=(statement_set.source_package_ref,),
                now=now,
                outcome="FAILED",
                observed_digest=None,
                error=error,
            )
            failed_record = _record(
                artifact_id=artifact_id,
                role=role,
                key=key,
                target=target,
                schema_version=statement_set.statement_schema_version,
                expected_digest=expected,
                observed_digest=None,
                state=ArtifactItemState.FAILED,
                attempts=(failed_attempt,),
            )
            returned_records = records + (failed_record,)
            return ArtifactSetManifest(
                manifest_id="MANIFEST:" + key.canonical_key_digest.value,
                key=key,
                records=returned_records,
                state=_manifest_state_for_failure(role),
                digest=digest_artifact_records(returned_records),
                detected_issues=_write_issue(role),
            )
        successful_attempt = _attempt(
            attempt_id=attempt_id,
            role=role,
            artifact_id=artifact_id,
            key=key,
            number=1,
            retry_of=None,
            refs=(statement_set.source_package_ref,),
            now=now,
            outcome="SUCCEEDED",
            observed_digest=observed,
            error=None,
        )
        records += (
            _record(
                artifact_id=artifact_id,
                role=role,
                key=key,
                target=target,
                schema_version=statement_set.statement_schema_version,
                expected_digest=expected,
                observed_digest=observed,
                state=ArtifactItemState.VERIFIED,
                attempts=(successful_attempt,),
            ),
        )
    return ArtifactSetManifest(
        manifest_id="MANIFEST:" + key.canonical_key_digest.value,
        key=key,
        records=records,
        state=ArtifactSetState.COMPLETE_VERIFIED,
        digest=digest_artifact_records(records),
        detected_issues=(),
    )


def inspect_artifact_set(root: Path, manifest: ArtifactSetManifest) -> ArtifactSetManifest:
    if (
        not isinstance(root, Path)
        or not isinstance(manifest, ArtifactSetManifest)
        or not isinstance(manifest.records, tuple)
        or any(not isinstance(record, ArtifactRecord) for record in manifest.records)
    ):
        raise F09ContractError(
            "ARTIFACT.STATE_INVALID",
            "/artifacts/0/state",
            "artifact manifest has invalid shape",
        )
    _validate_item_states(manifest.records)
    for role in _REQUIRED_ROLES:
        current = tuple(
            record
            for record in manifest.records
            if record.artifact_role == role
            and record.state not in (ArtifactItemState.SUPERSEDED, "SUPERSEDED")
        )
        if len(current) > 1:
            raise F09ContractError(
                "ARTIFACT.STATE_INVALID",
                f"/artifacts/{role}",
                "inspection found multiple current records for one required role",
            )
    records_digest = digest_artifact_records(manifest.records)
    statement_records = tuple(
        record
        for record in manifest.records
        if record.artifact_role == "STATEMENT_RECORDS"
        and record.state not in (ArtifactItemState.SUPERSEDED, "SUPERSEDED")
    )
    statement_indexes = tuple(
        record
        for record in manifest.records
        if record.artifact_role == "STATEMENT_INDEX"
        and record.state not in (ArtifactItemState.SUPERSEDED, "SUPERSEDED")
    )
    record_revisions = tuple(
        record.statement_set_id
        for record in statement_records
        if record.statement_set_id is not None
    )
    stale_index = bool(
        record_revisions
        and any(
            record.statement_set_id is not None
            and record.statement_set_id not in record_revisions
            for record in statement_indexes
        )
    )
    if stale_index:
        return replace(
            manifest,
            state=ArtifactSetState.STALE_MIXED_REVISION,
            digest=records_digest,
            detected_issues=(
                DetectedIssue("ARTIFACT.STALE_REVISION", "/artifacts/STATEMENT_INDEX"),
            ),
        )
    if any(
        record.expected_digest is not None
        and record.observed_digest is not None
        and record.expected_digest != record.observed_digest
        for record in manifest.records
    ):
        return replace(
            manifest,
            state=ArtifactSetState.DIGEST_MISMATCH,
            digest=records_digest,
            detected_issues=(
                DetectedIssue(
                    "ARTIFACT.DIGEST_MISMATCH", "/artifacts/observed_digest"
                ),
            ),
        )
    if manifest.records and manifest.records[0].state in (
        ArtifactItemState.STALE,
        "STALE",
    ):
        return replace(
            manifest,
            state=ArtifactSetState.STALE_MIXED_REVISION,
            digest=records_digest,
            detected_issues=(
                DetectedIssue("ARTIFACT.STALE_REVISION", "/artifacts/0"),
            ),
        )
    if manifest.records and manifest.records[0].state in (
        ArtifactItemState.MISMATCH,
        "MISMATCH",
    ):
        return replace(
            manifest,
            state=ArtifactSetState.DIGEST_MISMATCH,
            digest=records_digest,
            detected_issues=(
                DetectedIssue(
                    "ARTIFACT.DIGEST_MISMATCH", "/artifacts/0/observed_digest"
                ),
            ),
        )
    return replace(manifest, digest=records_digest, detected_issues=())


def _validate_item_states(records: tuple[ArtifactRecord, ...]) -> None:
    if any(
        not (
            isinstance(record.state, ArtifactItemState)
            or isinstance(record.state, str)
            and record.state in _LEGAL_ITEM_STATE_VALUES
        )
        for record in records
    ):
        raise F09ContractError(
            "ARTIFACT.STATE_INVALID",
            "/artifacts/0/state",
            "artifact item state is outside the eight legal values",
        )


def _attempt_outcome_closed(attempt: ArtifactWriteAttempt) -> bool:
    if attempt.outcome == "SUCCEEDED":
        return (
            attempt.finished_at is not None
            and attempt.observed_digest is not None
            and attempt.error_class is None
            and attempt.error_message_digest is None
        )
    if attempt.outcome == "FAILED":
        return (
            attempt.finished_at is not None
            and attempt.observed_digest is None
            and bool(attempt.error_class)
            and attempt.error_message_digest is not None
        )
    if attempt.outcome == "UNKNOWN":
        return (
            attempt.finished_at is None
            and attempt.observed_digest is None
            and attempt.error_class is None
            and attempt.error_message_digest is None
        )
    return False


def _digest_ref_shape_valid(digest: object) -> bool:
    return (
        type(digest) is DigestRef
        and type(digest.algorithm) is str
        and bool(digest.algorithm)
        and type(digest.canonicalization) is str
        and bool(digest.canonicalization)
        and type(digest.value) is str
        and len(digest.value) == 64
        and all(character in "0123456789abcdef" for character in digest.value)
    )


def _digest_binding_shape_valid(binding: object) -> bool:
    if type(binding) is DigestPresent:
        return binding.status == "PRESENT" and _digest_ref_shape_valid(binding.digest)
    if type(binding) is DigestMissing:
        return (
            binding.status == "MISSING"
            and binding.digest is None
            and type(binding.issue_id) is str
            and bool(binding.issue_id)
        )
    return False


def _versioned_ref_shape_valid(ref: object) -> bool:
    return (
        type(ref) is VersionedObjectRef
        and type(ref.object_type) is str
        and bool(ref.object_type)
        and type(ref.object_id) is str
        and bool(ref.object_id)
        and (ref.revision_id is None or type(ref.revision_id) is str)
        and type(ref.schema_version) is str
        and bool(ref.schema_version)
        and (ref.contract_version is None or type(ref.contract_version) is str)
        and _digest_binding_shape_valid(ref.digest_binding)
        and (ref.source_locator_id is None or type(ref.source_locator_id) is str)
        and (ref.captured_at is None or type(ref.captured_at) is str)
    )


def _validate_retained_history(records: tuple[ArtifactRecord, ...]) -> None:
    all_attempt_ids: set[str] = set()
    invalid = False
    for record in records:
        if (
            not isinstance(record, ArtifactRecord)
            or not isinstance(record.attempts, tuple)
            or not record.attempts
            or not record.schema_version
            or any(type(attempt) is not ArtifactWriteAttempt for attempt in record.attempts)
        ):
            invalid = True
            break
        local_key = record.attempts[0].idempotency_key
        local_refs = record.attempts[0].input_snapshot_refs
        path_parent_key = Path(record.path_locator).parent.name
        local_attempt_ids: set[str] = set()
        for attempt_index, attempt in enumerate(record.attempts):
            valid_refs = (
                isinstance(attempt.input_snapshot_refs, tuple)
                and bool(attempt.input_snapshot_refs)
                and all(
                    _versioned_ref_shape_valid(ref)
                    for ref in attempt.input_snapshot_refs
                )
                and attempt.input_snapshot_refs == local_refs
            )
            valid_key = (
                type(attempt.idempotency_key) is str
                and len(attempt.idempotency_key) == 64
                and all(character in "0123456789abcdef" for character in attempt.idempotency_key)
                and attempt.idempotency_key == local_key
                and path_parent_key == local_key
            )
            valid_attempt_id = (
                type(attempt.attempt_id) is str
                and bool(attempt.attempt_id)
                and attempt.attempt_id not in local_attempt_ids
                and attempt.attempt_id not in all_attempt_ids
            )
            if (
                attempt.artifact_id != record.artifact_id
                or type(attempt.attempt_number) is not int
                or attempt.attempt_number <= 0
                or attempt.attempt_number != attempt_index + 1
                or attempt.retry_of_attempt_id
                != (None if attempt_index == 0 else record.attempts[attempt_index - 1].attempt_id)
                or not valid_refs
                or not valid_key
                or not valid_attempt_id
                or type(attempt.started_at) is not str
                or not attempt.started_at
                or not _attempt_outcome_closed(attempt)
            ):
                invalid = True
                break
            local_attempt_ids.add(attempt.attempt_id)
            all_attempt_ids.add(attempt.attempt_id)
        if invalid:
            break
    if invalid:
        raise F09ContractError(
            "ARTIFACT.STATE_INVALID",
            "/artifacts/0/attempts",
            "every retained record must preserve one coherent record-local history identity",
        )


def _replace_current_record(
    records: tuple[ArtifactRecord, ...],
    previous: ArtifactRecord | None,
    replacement: ArtifactRecord,
) -> tuple[ArtifactRecord, ...]:
    if previous is None:
        return records + (replacement,)
    return tuple(replacement if record is previous else record for record in records)


def retry_artifact_set(
    root: Path,
    manifest: ArtifactSetManifest,
    projections: Mapping[str, bytes],
    *,
    key: IdempotencyKey,
    current_frozen_input_refs: tuple[VersionedObjectRef, ...],
    current_schema_version: str,
    current_statement_set_id: str,
    current_contract_digest: DigestRef | None,
    attempt_id: str,
    now: str,
) -> ArtifactSetManifest:
    if (
        not isinstance(root, Path)
        or not isinstance(manifest, ArtifactSetManifest)
        or not isinstance(manifest.records, tuple)
        or not isinstance(key, IdempotencyKey)
        or key != manifest.key
        or not isinstance(current_frozen_input_refs, tuple)
        or not current_frozen_input_refs
        or any(
            not isinstance(ref, VersionedObjectRef)
            for ref in current_frozen_input_refs
        )
        or type(current_schema_version) is not str
        or not current_schema_version
        or type(current_statement_set_id) is not str
        or not current_statement_set_id
        or key.statement_set_id != current_statement_set_id
        or key.contract_digest != current_contract_digest
        or type(attempt_id) is not str
        or not attempt_id
        or type(now) is not str
        or not now
    ):
        raise F09ContractError(
            "ARTIFACT.STATE_INVALID",
            "/artifacts/0/state",
            "retry accepts only one canonical manifest and explicit current authority",
        )
    _validate_projections(projections)
    _validate_item_states(manifest.records)
    _validate_retained_history(manifest.records)
    operation_root = resolve_artifact_operation_root(root, key)

    current_records = tuple(
        record
        for record in manifest.records
        if record.state not in (ArtifactItemState.SUPERSEDED, "SUPERSEDED")
    )
    if any(
        record.case_id != key.case_id
        or record.track != key.track
        or record.statement_set_id != current_statement_set_id
        or any(
            attempt.idempotency_key != key.canonical_key_digest.value
            for attempt in record.attempts
        )
        for record in current_records
    ):
        raise F09ContractError(
            "ARTIFACT.STATE_INVALID",
            "/artifacts/0/attempts/0/idempotency_key",
            "current records do not match the incoming operation identity",
        )
    if any(
        record.schema_version != current_schema_version
        or any(
            attempt.input_snapshot_refs != current_frozen_input_refs
            for attempt in record.attempts
        )
        for record in current_records
    ):
        raise F09ContractError(
            "ARTIFACT.STATE_INVALID",
            "/artifacts/0/attempts/0/input_snapshot_refs",
            "current records do not match explicit frozen refs and schema",
        )
    records_by_role = {
        role: tuple(
            record
            for record in current_records
            if record.artifact_role == role
        )
        for role in _REQUIRED_ROLES
    }
    if any(len(records_by_role[role]) > 1 for role in _REQUIRED_ROLES):
        raise F09ContractError(
            "ARTIFACT.STATE_INVALID",
            "/artifacts/0/state",
            "retry has multiple current records for one required role",
        )
    if any(
        record.artifact_role not in _REQUIRED_ROLES
        for record in current_records
    ):
        raise F09ContractError(
            "ARTIFACT.STATE_INVALID",
            "/artifacts/0/state",
            "retry contains a noncanonical current artifact role",
        )
    projection_digests = {
        role: _payload_digest(projections[role]) for role in _REQUIRED_ROLES
    }
    if any(
        records_by_role[role]
        and records_by_role[role][0].expected_digest != projection_digests[role]
        for role in _REQUIRED_ROLES
    ):
        return replace(
            manifest,
            state=ArtifactSetState.DIGEST_MISMATCH,
            digest=digest_artifact_records(manifest.records),
            detected_issues=(
                DetectedIssue(
                    "IDEMPOTENCY.DIGEST_MISMATCH", "/canonical_key_digest"
                ),
            ),
        )
    records = manifest.records
    for role in _REQUIRED_ROLES:
        if not records_by_role[role]:
            continue
        previous = records_by_role[role][0]
        if previous.attempts[-1].outcome != "UNKNOWN":
            continue
        target = operation_root / _ROLE_FILENAMES[role]
        try:
            observed_bytes = target.read_bytes()
        except OSError as error:
            raise F09IntegrityError(
                "ARTIFACT.DIGEST_MISMATCH",
                "/artifacts/observed_digest",
                "UNKNOWN attempt has no readable committed final for reconciliation",
            ) from error
        observed = _payload_digest(observed_bytes)
        if observed_bytes != projections[role] or observed != projection_digests[role]:
            raise F09IntegrityError(
                "ARTIFACT.DIGEST_MISMATCH",
                "/artifacts/observed_digest",
                "UNKNOWN attempt final does not match the expected bytes and digest",
            )
        reconciled_record = replace(
            previous,
            observed_digest=observed,
            state=ArtifactItemState.VERIFIED,
            issue_ids=(),
        )
        records = _replace_current_record(records, previous, reconciled_record)
        records_by_role[role] = (reconciled_record,)

    roles_requiring_write = tuple(
        role
        for role in _REQUIRED_ROLES
        if not records_by_role[role]
        or records_by_role[role][0].state
        not in (ArtifactItemState.VERIFIED, "VERIFIED")
        or records_by_role[role][0].observed_digest != projection_digests[role]
    )
    if not roles_requiring_write:
        return replace(
            manifest,
            records=records,
            state=ArtifactSetState.COMPLETE_VERIFIED,
            digest=digest_artifact_records(records),
            detected_issues=(),
        )
    for role in roles_requiring_write:
        previous = records_by_role[role][0] if records_by_role[role] else None
        artifact_id = (
            previous.artifact_id
            if previous is not None
            else f"ARTIFACT:{key.canonical_key_digest.value}:{role}"
        )
        target = operation_root / _ROLE_FILENAMES[role]
        number = 1 if previous is None else len(previous.attempts) + 1
        retry_of = None if previous is None else previous.attempts[-1].attempt_id
        prior_attempts = () if previous is None else previous.attempts
        try:
            operation_root.mkdir(parents=True, exist_ok=True)
            observed = _atomic_write_verified(target, projections[role])
        except OSError as error:
            failed_attempt = _attempt(
                attempt_id=attempt_id,
                role=role,
                artifact_id=artifact_id,
                key=key,
                number=number,
                retry_of=retry_of,
                refs=current_frozen_input_refs,
                now=now,
                outcome="FAILED",
                observed_digest=None,
                error=error,
            )
            failed_record = _record(
                artifact_id=artifact_id,
                role=role,
                key=key,
                target=target,
                schema_version=current_schema_version,
                expected_digest=projection_digests[role],
                observed_digest=None,
                state=ArtifactItemState.FAILED,
                attempts=prior_attempts + (failed_attempt,),
            )
            returned_records = _replace_current_record(
                records, previous, failed_record
            )
            return ArtifactSetManifest(
                manifest_id=manifest.manifest_id,
                key=key,
                records=returned_records,
                state=_manifest_state_for_failure(role),
                digest=digest_artifact_records(returned_records),
                detected_issues=_write_issue(role),
            )
        successful_attempt = _attempt(
            attempt_id=attempt_id,
            role=role,
            artifact_id=artifact_id,
            key=key,
            number=number,
            retry_of=retry_of,
            refs=current_frozen_input_refs,
            now=now,
            outcome="SUCCEEDED",
            observed_digest=observed,
            error=None,
        )
        verified_record = _record(
            artifact_id=artifact_id,
            role=role,
            key=key,
            target=target,
            schema_version=current_schema_version,
            expected_digest=projection_digests[role],
            observed_digest=observed,
            state=ArtifactItemState.VERIFIED,
            attempts=prior_attempts + (successful_attempt,),
        )
        records = _replace_current_record(records, previous, verified_record)
    return replace(
        manifest,
        records=records,
        state=ArtifactSetState.COMPLETE_VERIFIED,
        digest=digest_artifact_records(records),
        detected_issues=(),
    )


def coordinate_artifact_operation(
    root: Path, statement_set: StatementSet, projections: Mapping[str, bytes], *,
    existing_manifest: ArtifactSetManifest | None, key: IdempotencyKey, attempt_id: str, now: str,
) -> ArtifactSetManifest:
    if existing_manifest is None or existing_manifest.key != key:
        return write_artifact_set(root, statement_set, projections, key=key, attempt_id=attempt_id, now=now)
    return retry_artifact_set(root, existing_manifest, projections, key=key,
        current_frozen_input_refs=(statement_set.source_package_ref,),
        current_schema_version=statement_set.statement_schema_version,
        current_statement_set_id=statement_set.statement_set_id,
        current_contract_digest=key.contract_digest, attempt_id=attempt_id, now=now)


_RUN_FILENAMES = {"RUN_SNAPSHOT": "run_snapshot.bin", "DECISION_RUN": "decision_run.bin", "FEEDBACK_ATTACHMENT": "feedback_attachment.bin"}


def provision_verified_run_manifest_fixture_v1() -> ArtifactSetManifest:
    roles = ("RUN_SNAPSHOT", "DECISION_RUN", "FEEDBACK_ATTACHMENT")
    refs = (
        VersionedObjectRef(
            object_type="NORMALIZED_EVIDENCE_PACKAGE",
            object_id="PACKAGE:F09:RUN-FIXTURE",
            revision_id="REVISION:F09:RUN-FIXTURE",
            schema_version="f09.run-fixture.source.v1",
            contract_version="f09.run-fixture.contract.v1",
            digest_binding=DigestPresent(
                "PRESENT",
                DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(b"f09.run-fixture.ref.v1").hexdigest()),
            ),
            source_locator_id="SOURCE:F09:RUN-FIXTURE",
            captured_at="2026-07-23T00:00:00Z",
        ),
    )
    projections = {
        "RUN_SNAPSHOT": b"f09.run-fixture.run-snapshot.v1",
        "DECISION_RUN": b"f09.run-fixture.decision-run.v1",
        "FEEDBACK_ATTACHMENT": b"f09.run-fixture.feedback-attachment.v1",
    }
    projection_digests = MappingProxyType({
        role: DigestRef("sha256", "RAW-UTF8", sha256(projections[role]).hexdigest())
        for role in roles
    })
    source_digest = DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(b"f09.run-fixture.source.v1").hexdigest())
    schema_versions_digest = DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(b"f09.run-fixture.schema-versions.v1").hexdigest())
    contract_digest = DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(b"f09.run-fixture.contract.v1").hexdigest())
    refs_digest = _digest_run_input_snapshot_refs_v1(refs)
    key = RunArtifactSetKeyV1(
        operation="PROJECT_RUN_ARTIFACT_SET",
        case_id="CASE:F09:RUN-FIXTURE",
        track=RunTrack.V5_V6_PREPROD,
        run_id="RUN:F09:RUN-FIXTURE",
        source_digest=source_digest,
        schema_versions_digest=schema_versions_digest,
        contract_digest=contract_digest,
        input_snapshot_refs_graph_digest=refs_digest,
        projection_roles=roles,
        projection_digest_by_role=projection_digests,
        canonical_key_digest=_digest_run_artifact_set_key_v1(
            operation="PROJECT_RUN_ARTIFACT_SET",
            case_id="CASE:F09:RUN-FIXTURE",
            track=RunTrack.V5_V6_PREPROD,
            run_id="RUN:F09:RUN-FIXTURE",
            source_digest=source_digest,
            schema_versions_digest=schema_versions_digest,
            contract_digest=contract_digest,
            input_snapshot_refs_graph_digest=refs_digest,
            projection_roles=roles,
            projection_digest_by_role=projection_digests,
        ),
    )
    records: tuple[ArtifactRecord, ...] = ()
    for role in roles:
        artifact_id = f"RUN-ARTIFACT:{key.canonical_key_digest.value}:{role}"
        digest = projection_digests[role]
        attempt = ArtifactWriteAttempt(
            attempt_id=f"FIXTURE:{role}",
            artifact_id=artifact_id,
            idempotency_key=key.canonical_key_digest.value,
            attempt_number=1,
            retry_of_attempt_id=None,
            input_snapshot_refs=refs,
            started_at="2026-07-23T00:00:00Z",
            finished_at="2026-07-23T00:00:00Z",
            outcome="SUCCEEDED",
            observed_digest=digest,
            error_class=None,
            error_message_digest=None,
        )
        records += (
            ArtifactRecord(
                artifact_id=artifact_id,
                artifact_role=role,
                track=key.track,
                case_id=key.case_id,
                statement_set_id=None,
                run_id=key.run_id,
                path_locator="/".join(("run-artifacts", key.canonical_key_digest.value, _RUN_FILENAMES[role])),
                schema_version="f09.run-artifact-fixture.v1",
                expected_digest=digest,
                observed_digest=digest,
                state=ArtifactItemState.VERIFIED,
                attempts=(attempt,),
                issue_ids=(),
            ),
        )
    manifest = ArtifactSetManifest(
        manifest_id=f"RUN-MANIFEST:{key.canonical_key_digest.value}",
        key=key,
        records=records,
        state=ArtifactSetState.COMPLETE_VERIFIED,
        digest=digest_artifact_records(records),
        detected_issues=(),
    )
    validate_run_artifact_manifest_v1(manifest)
    return manifest


def _validate_run_request_v1(request: RunArtifactSetRequestV1) -> None:
    if type(request) is not RunArtifactSetRequestV1 or type(request.key) is not RunArtifactSetKeyV1:
        raise F09ContractError("RUN_ARTIFACT.REQUEST_INVALID", "/request", "exact run request and key required")
    key = request.key
    if (request.run_id != key.run_id or type(request.schema_version) is not str or not request.schema_version
            or type(request.input_snapshot_refs) is not tuple or any(type(ref) is not VersionedObjectRef for ref in request.input_snapshot_refs)
            or not isinstance(request.projections, Mapping) or tuple(request.projections) != key.projection_roles
            or any(type(payload) is not bytes for payload in request.projections.values())):
        raise F09ContractError("RUN_ARTIFACT.REQUEST_INVALID", "/request", "invalid closed run request")
    if _digest_run_input_snapshot_refs_v1(request.input_snapshot_refs) != key.input_snapshot_refs_graph_digest:
        raise F09IntegrityError("RUN_ARTIFACT.REFS_MISMATCH", "/key/input_snapshot_refs_graph_digest", "run refs mismatch")
    if key.canonical_key_digest != _digest_run_artifact_set_key_v1_from_key(key):
        raise F09IntegrityError("RUN_ARTIFACT.KEY_MISMATCH", "/key/canonical_key_digest", "run key mismatch")
    if any(_payload_digest(payload) != key.projection_digest_by_role[role] for role, payload in request.projections.items()):
        raise F09IntegrityError("RUN_ARTIFACT.PAYLOAD_MISMATCH", "/projections", "run projection digest mismatch")


def _resolve_run_artifact_root_v1(root: Path, key: RunArtifactSetKeyV1) -> Path:
    if not isinstance(root, Path) or type(key) is not RunArtifactSetKeyV1:
        raise F09ContractError("RUN_ARTIFACT.ROOT_INVALID", "/root", "invalid run root")
    value = key.canonical_key_digest.value
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise F09IntegrityError("RUN_ARTIFACT.KEY_MISMATCH", "/key/canonical_key_digest", "invalid run root digest")
    resolved_root = root.resolve(strict=False)
    candidate = (resolved_root / "run-artifacts" / value).resolve(strict=False)
    try:
        contained = candidate.is_relative_to(resolved_root)
    except AttributeError:
        contained = resolved_root in candidate.parents
    if candidate == resolved_root or not contained:
        raise F09IntegrityError("RUN_ARTIFACT.ROOT_INVALID", "/root", "run artifact root escapes the authorized root")
    return candidate


def _run_final_matches_expected_v1(target: Path, expected: DigestRef) -> bool | None:
    try:
        return target.is_file() and _payload_digest(target.read_bytes()) == expected
    except OSError:
        return None


def validate_run_artifact_manifest_v1(manifest: ArtifactSetManifest) -> DigestRef:
    if type(manifest) is not ArtifactSetManifest or type(manifest.key) is not RunArtifactSetKeyV1:
        raise F09ContractError("RUN_ARTIFACT.MANIFEST_INVALID", "/manifest", "exact run manifest required")
    key = manifest.key
    if manifest.manifest_id != f"RUN-MANIFEST:{key.canonical_key_digest.value}":
        raise F09IntegrityError("RUN_ARTIFACT.MANIFEST_INVALID", "/manifest_id", "run manifest identity mismatch")
    if key.canonical_key_digest != _digest_run_artifact_set_key_v1_from_key(key):
        raise F09IntegrityError("RUN_ARTIFACT.KEY_MISMATCH", "/key/canonical_key_digest", "run key mismatch")
    if (type(manifest.records) is not tuple or any(type(record) is not ArtifactRecord for record in manifest.records)
            or tuple(record.artifact_role for record in manifest.records) != key.projection_roles):
        raise F09IntegrityError("RUN_ARTIFACT.ROLE_CLOSURE_INVALID", "/records", "invalid run role closure")
    for record in manifest.records:
        expected_artifact_id = f"RUN-ARTIFACT:{key.canonical_key_digest.value}:{record.artifact_role}"
        expected_locator = "/".join((
            "run-artifacts", key.canonical_key_digest.value, _RUN_FILENAMES[record.artifact_role],
        ))
        if (type(record) is not ArtifactRecord or record.path_locator != expected_locator
                or record.case_id != key.case_id or record.track != key.track or record.run_id != key.run_id
                or record.statement_set_id is not None or record.issue_ids != ()
                or type(record.schema_version) is not str or not record.schema_version
                or record.artifact_id != expected_artifact_id
                or record.expected_digest != key.projection_digest_by_role[record.artifact_role]
                or record.observed_digest != record.expected_digest or record.state is not ArtifactItemState.VERIFIED
                or type(record.attempts) is not tuple or not record.attempts):
            raise F09IntegrityError("RUN_ARTIFACT.RECORD_INVALID", "/records", "run record graph mismatch")
        for number, attempt in enumerate(record.attempts, start=1):
            previous = None if number == 1 else record.attempts[number - 2].attempt_id
            if (type(attempt) is not ArtifactWriteAttempt or attempt.artifact_id != expected_artifact_id
                    or attempt.idempotency_key != key.canonical_key_digest.value or attempt.attempt_number != number
                    or attempt.retry_of_attempt_id != previous or not isinstance(attempt.attempt_id, str) or not attempt.attempt_id
                    or not isinstance(attempt.started_at, str) or not attempt.started_at
                    or attempt.finished_at != attempt.started_at
                    or _digest_run_input_snapshot_refs_v1(attempt.input_snapshot_refs) != key.input_snapshot_refs_graph_digest):
                raise F09IntegrityError("RUN_ARTIFACT.ATTEMPT_INVALID", "/records", "run attempt receipt graph mismatch")
            if attempt is record.attempts[-1]:
                if (attempt.outcome != "SUCCEEDED" or attempt.observed_digest != record.expected_digest
                        or attempt.error_class is not None or attempt.error_message_digest is not None):
                    raise F09IntegrityError("RUN_ARTIFACT.ATTEMPT_INVALID", "/records", "run terminal attempt mismatch")
            elif (attempt.outcome != "FAILED" or attempt.observed_digest is not None
                    or attempt.error_class is None or attempt.error_message_digest is None):
                raise F09IntegrityError("RUN_ARTIFACT.ATTEMPT_INVALID", "/records", "run retry history mismatch")
    digest = digest_artifact_records(manifest.records)
    if manifest.digest != digest or manifest.state is not ArtifactSetState.COMPLETE_VERIFIED or manifest.detected_issues != ():
        raise F09IntegrityError("RUN_ARTIFACT.MANIFEST_INVALID", "/manifest", "invalid run manifest state")
    return digest


def inspect_run_artifact_set_v1(root: Path, manifest: ArtifactSetManifest) -> ArtifactSetManifest:
    validate_run_artifact_manifest_v1(manifest)
    for record in manifest.records:
        target = _resolve_run_artifact_root_v1(root, manifest.key) / _RUN_FILENAMES[record.artifact_role]
        try:
            matches = target.is_file() and _payload_digest(target.read_bytes()) == record.expected_digest
        except OSError as error:
            raise F09IntegrityError(
                "RUN_ARTIFACT.READBACK_MISMATCH", "/records", "run artifact readback mismatch"
            ) from error
        if not matches:
            raise F09IntegrityError("RUN_ARTIFACT.READBACK_MISMATCH", "/records", "run artifact readback mismatch")
    return manifest


def coordinate_run_artifact_set_v1(root: Path, request: RunArtifactSetRequestV1, *, existing_manifest: ArtifactSetManifest | None, attempt_id: str, now: str) -> ArtifactSetManifest:
    _validate_run_request_v1(request)
    if type(attempt_id) is not str or not attempt_id or type(now) is not str or not now:
        raise F09ContractError("RUN_ARTIFACT.REQUEST_INVALID", "/attempt", "nonblank attempt data required")
    if existing_manifest is not None:
        if type(existing_manifest) is not ArtifactSetManifest or existing_manifest.key != request.key:
            raise F09IntegrityError("RUN_ARTIFACT.EXISTING_MISMATCH", "/existing_manifest", "existing manifest mismatch")
        if existing_manifest.state is ArtifactSetState.COMPLETE_VERIFIED:
            validate_run_artifact_manifest_v1(existing_manifest)
        elif existing_manifest.state is ArtifactSetState.PARTIAL:
            _validate_run_partial_receipt_v1(request, existing_manifest)
        else:
            raise F09IntegrityError("RUN_ARTIFACT.EXISTING_MISMATCH", "/existing_manifest", "run retry requires partial receipt")
        if any(record.schema_version != request.schema_version for record in existing_manifest.records):
            raise F09IntegrityError("RUN_ARTIFACT.EXISTING_MISMATCH", "/existing_manifest/records", "run artifact schema mismatch")
        if existing_manifest.state is ArtifactSetState.COMPLETE_VERIFIED:
            return inspect_run_artifact_set_v1(root, existing_manifest)
        operation_root = _resolve_run_artifact_root_v1(root, request.key)
        retained_manifest = reconcile_run_artifact_set_v1(root, request, existing_manifest)
        if retained_manifest.state is ArtifactSetState.COMPLETE_VERIFIED:
            return inspect_run_artifact_set_v1(root, retained_manifest)
        for retained_record in retained_manifest.records:
            if (retained_record.state is ArtifactItemState.VERIFIED
                    and _run_final_matches_expected_v1(
                        operation_root / _RUN_FILENAMES[retained_record.artifact_role],
                        retained_record.expected_digest,
                    ) is not True):
                raise F09IntegrityError("RUN_ARTIFACT.READBACK_MISMATCH", "/records", "retained run artifact readback mismatch")
        retained = {record.artifact_role: record for record in retained_manifest.records}
        records: tuple[ArtifactRecord, ...] = ()
        try:
            operation_root.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            role = next(role for role in request.key.projection_roles if retained.get(role) is None or retained[role].state is not ArtifactItemState.VERIFIED)
            previous = retained.get(role)
            history = () if previous is None else previous.attempts
            artifact_id = f"RUN-ARTIFACT:{request.key.canonical_key_digest.value}:{role}"
            failed_attempt = ArtifactWriteAttempt(
                f"{attempt_id}:{role}", artifact_id, request.key.canonical_key_digest.value,
                len(history) + 1, None if not history else history[-1].attempt_id,
                request.input_snapshot_refs, now, now, "FAILED", None,
                type(error).__name__, _error_digest(error),
            )
            failed_record = ArtifactRecord(
                artifact_id, role, request.key.track, request.key.case_id, None, request.key.run_id,
                "/".join(("run-artifacts", request.key.canonical_key_digest.value, _RUN_FILENAMES[role])), request.schema_version,
                request.key.projection_digest_by_role[role], None, ArtifactItemState.FAILED,
                history + (failed_attempt,), (),
            )
            for current_role in request.key.projection_roles:
                if current_role == role:
                    records += (failed_record,)
                    break
                if retained.get(current_role) is not None:
                    records += (retained[current_role],)
            return ArtifactSetManifest(
                "RUN-MANIFEST:" + request.key.canonical_key_digest.value, request.key, records,
                ArtifactSetState.PARTIAL, digest_artifact_records(records),
                (DetectedIssue("RUN_ARTIFACT.WRITE_FAILED", f"/records/{role}"),),
            )
        for role in request.key.projection_roles:
            previous = retained.get(role)
            if previous is not None and previous.state is ArtifactItemState.VERIFIED:
                records += (previous,)
                continue
            target = operation_root / _RUN_FILENAMES[role]
            artifact_id = f"RUN-ARTIFACT:{request.key.canonical_key_digest.value}:{role}"
            history = () if previous is None else previous.attempts
            retry_of = None if not history else history[-1].attempt_id
            try:
                observed = _atomic_write_verified(target, request.projections[role])
            except OSError as error:
                try:
                    committed = _run_final_matches_expected_v1(
                        target, request.key.projection_digest_by_role[role]
                    )
                except OSError:
                    committed = None
                unknown = committed is not False
                failed_attempt = ArtifactWriteAttempt(
                    f"{attempt_id}:{role}", artifact_id, request.key.canonical_key_digest.value,
                    len(history) + 1, retry_of, request.input_snapshot_refs, now,
                    None if unknown else now, "UNKNOWN" if unknown else "FAILED", None,
                    None if unknown else type(error).__name__, None if unknown else _error_digest(error),
                )
                failed_record = ArtifactRecord(
                    artifact_id, role, request.key.track, request.key.case_id, None,
                    request.key.run_id, "/".join(("run-artifacts", request.key.canonical_key_digest.value, _RUN_FILENAMES[role])), request.schema_version,
                    request.key.projection_digest_by_role[role], None,
                    ArtifactItemState.WRITTEN_UNVERIFIED if unknown else ArtifactItemState.FAILED,
                    history + (failed_attempt,), (),
                )
                records += (failed_record,)
                return ArtifactSetManifest(
                    "RUN-MANIFEST:" + request.key.canonical_key_digest.value, request.key,
                    records, ArtifactSetState.PARTIAL, digest_artifact_records(records),
                    (DetectedIssue("RUN_ARTIFACT.WRITE_FAILED", f"/records/{role}"),),
                )
            attempt = ArtifactWriteAttempt(
                f"{attempt_id}:{role}", artifact_id, request.key.canonical_key_digest.value,
                len(history) + 1, retry_of, request.input_snapshot_refs, now, now, "SUCCEEDED", observed, None, None,
            )
            records += (ArtifactRecord(
                artifact_id, role, request.key.track, request.key.case_id, None, request.key.run_id,
                "/".join(("run-artifacts", request.key.canonical_key_digest.value, _RUN_FILENAMES[role])), request.schema_version, request.key.projection_digest_by_role[role],
                observed, ArtifactItemState.VERIFIED, history + (attempt,), (),
            ),)
        complete = ArtifactSetManifest(
            "RUN-MANIFEST:" + request.key.canonical_key_digest.value, request.key, records,
            ArtifactSetState.COMPLETE_VERIFIED, digest_artifact_records(records), (),
        )
        validate_run_artifact_manifest_v1(complete)
        return complete
    operation_root = _resolve_run_artifact_root_v1(root, request.key)
    first_role = request.key.projection_roles[0]
    first_target = operation_root / _RUN_FILENAMES[first_role]
    try:
        operation_root.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        artifact_id = f"RUN-ARTIFACT:{request.key.canonical_key_digest.value}:{first_role}"
        failed_attempt = ArtifactWriteAttempt(
            f"{attempt_id}:{first_role}", artifact_id, request.key.canonical_key_digest.value,
            1, None, request.input_snapshot_refs, now, now, "FAILED", None,
            type(error).__name__, _error_digest(error),
        )
        failed_record = ArtifactRecord(
            artifact_id, first_role, request.key.track, request.key.case_id, None,
            request.key.run_id, "/".join(("run-artifacts", request.key.canonical_key_digest.value, _RUN_FILENAMES[first_role])), request.schema_version,
            request.key.projection_digest_by_role[first_role], None, ArtifactItemState.FAILED,
            (failed_attempt,), (),
        )
        return ArtifactSetManifest(
            "RUN-MANIFEST:" + request.key.canonical_key_digest.value, request.key,
            (failed_record,), ArtifactSetState.PARTIAL, digest_artifact_records((failed_record,)),
            (DetectedIssue("RUN_ARTIFACT.WRITE_FAILED", f"/records/{first_role}"),),
        )
    records: tuple[ArtifactRecord, ...] = ()
    for role in request.key.projection_roles:
        target = operation_root / _RUN_FILENAMES[role]
        artifact_id = f"RUN-ARTIFACT:{request.key.canonical_key_digest.value}:{role}"
        try:
            observed = _atomic_write_verified(target, request.projections[role])
        except OSError as error:
            try:
                committed = _run_final_matches_expected_v1(
                    target, request.key.projection_digest_by_role[role]
                )
            except OSError:
                committed = None
            unknown = committed is not False
            failed_attempt = ArtifactWriteAttempt(
                f"{attempt_id}:{role}", artifact_id, request.key.canonical_key_digest.value,
                1, None, request.input_snapshot_refs, now, None if unknown else now,
                "UNKNOWN" if unknown else "FAILED", None,
                None if unknown else type(error).__name__, None if unknown else _error_digest(error),
            )
            failed_record = ArtifactRecord(
                artifact_id, role, request.key.track, request.key.case_id, None,
                request.key.run_id, "/".join(("run-artifacts", request.key.canonical_key_digest.value, _RUN_FILENAMES[role])), request.schema_version,
                request.key.projection_digest_by_role[role], None,
                ArtifactItemState.WRITTEN_UNVERIFIED if unknown else ArtifactItemState.FAILED,
                (failed_attempt,), (),
            )
            records += (failed_record,)
            return ArtifactSetManifest(
                "RUN-MANIFEST:" + request.key.canonical_key_digest.value, request.key,
                records, ArtifactSetState.PARTIAL, digest_artifact_records(records),
                (DetectedIssue("RUN_ARTIFACT.WRITE_FAILED", f"/records/{role}"),),
            )
        attempt = ArtifactWriteAttempt(f"{attempt_id}:{role}", artifact_id, request.key.canonical_key_digest.value, 1, None, request.input_snapshot_refs, now, now, "SUCCEEDED", observed, None, None)
        records += (ArtifactRecord(artifact_id, role, request.key.track, request.key.case_id, None, request.key.run_id, "/".join(("run-artifacts", request.key.canonical_key_digest.value, _RUN_FILENAMES[role])), request.schema_version, request.key.projection_digest_by_role[role], observed, ArtifactItemState.VERIFIED, (attempt,), ()),)
    return ArtifactSetManifest("RUN-MANIFEST:" + request.key.canonical_key_digest.value, request.key, records, ArtifactSetState.COMPLETE_VERIFIED, digest_artifact_records(records), ())


def coordinate_run_artifact_set_with_target_refs_v1(
    root: Path,
    request: RunArtifactSetRequestV1,
    *,
    target_refs_request: RunArtifactTargetRefsRequestV1,
    manifest_outer_ref_request: ManifestOuterRefRequestV1,
    existing_manifest: ArtifactSetManifest | None,
    attempt_id: str,
    now: str,
) -> RunArtifactSetResultV1:
    if (
        type(request) is not RunArtifactSetRequestV1
        or type(request.key) is not RunArtifactSetKeyV1
        or request.key.track is not RunTrack.V5_V6_PREPROD
        or type(target_refs_request) is not RunArtifactTargetRefsRequestV1
        or type(manifest_outer_ref_request) is not ManifestOuterRefRequestV1
    ):
        raise F09ContractError("RUN_ARTIFACT.REQUEST_INVALID", "issuance_proof", "invalid issuance coordinator input")
    capture_refs = (
        target_refs_request.run_snapshot_ref,
        target_refs_request.decision_run_ref,
        target_refs_request.feedback_attachment_ref,
    )
    for ref, role in zip(capture_refs, ("RUN_SNAPSHOT", "DECISION_RUN", "FEEDBACK_ATTACHMENT"), strict=True):
        _r41_ref_material(ref)
        if ref.object_type != role:
            raise F09ContractError("RUN_ARTIFACT.REQUEST_INVALID", "issuance_proof", "invalid capture ref role")
    outer = manifest_outer_ref_request
    if type(outer.schema_version) is not str or not outer.schema_version.strip():
        raise F09ContractError("RUN_ARTIFACT.REQUEST_INVALID", "issuance_proof", "invalid manifest outer ref")
    for value in (outer.revision_id, outer.contract_version, outer.source_locator_id, outer.captured_at):
        if value is not None and (type(value) is not str or not value.strip()):
            raise F09ContractError("RUN_ARTIFACT.REQUEST_INVALID", "issuance_proof", "invalid manifest outer ref")
    manifest = coordinate_run_artifact_set_v1(
        root, request, existing_manifest=existing_manifest, attempt_id=attempt_id, now=now,
    )
    records_digest = validate_run_artifact_manifest_v1(manifest)
    manifest_ref = VersionedObjectRef(
        "MANIFEST", manifest.manifest_id, outer.revision_id, outer.schema_version,
        outer.contract_version, DigestPresent("PRESENT", records_digest), outer.source_locator_id, outer.captured_at,
    )
    target_refs = capture_refs + (manifest_ref,)
    payload = _canonicalize_run_artifact_set_issuance_payload_v1(
        manifest,
        target_refs,
        records_digest=records_digest,
    )
    port = _RUN_ARTIFACT_SET_SIGNER_PORT_V1
    if type(port) is not tuple or len(port) != 2 or type(port[0]) is not str or not port[0].strip() or not callable(port[1]):
        raise F09ContractError("RUN_ARTIFACT_SET_SIGNER_UNAVAILABLE", "issuance_proof", "signer is not provisioned")
    registry = get_run_artifact_set_public_key_registry_v1()
    if (
        type(registry) is not RunArtifactSetPublicKeyRegistryV1
        or type(registry.registry_version) is not str
        or not registry.registry_version.strip()
        or type(registry.keys_by_id) is not MappingProxyType
    ):
        raise F09ContractError("RUN_ARTIFACT_SET_SIGNING_KEY_INVALID", "issuance_proof", "invalid signing registry")
    for registered_key_id, registered_key in registry.keys_by_id.items():
        if (
            type(registered_key_id) is not str
            or not registered_key_id.strip()
            or type(registered_key) is not RunArtifactSetPublicKeyV1
            or type(registered_key.key_id) is not str
            or registered_key.key_id != registered_key_id
            or type(registered_key.status) is not str
            or registered_key.status not in ("ACTIVE", "REVOKED")
        ):
            raise F09ContractError("RUN_ARTIFACT_SET_SIGNING_KEY_INVALID", "issuance_proof", "invalid signing registry")
        if len(_base64url_decode(registered_key.public_key_b64url, field_path="issuance_proof")) != 32:
            raise F09ContractError("RUN_ARTIFACT_SET_SIGNING_KEY_INVALID", "issuance_proof", "invalid signing registry")
    signing_key = registry.keys_by_id.get(port[0])
    if (
        type(signing_key) is not RunArtifactSetPublicKeyV1
        or type(signing_key.key_id) is not str
        or signing_key.key_id != port[0]
        or type(signing_key.status) is not str
        or signing_key.status != "ACTIVE"
    ):
        raise F09ContractError("RUN_ARTIFACT_SET_SIGNING_KEY_INVALID", "issuance_proof", "signer key is not active")
    try:
        signature = port[1](payload)
    except Exception as error:
        raise F09ContractError("RUN_ARTIFACT_SET_SIGNING_FAILED", "issuance_proof", "signer failed") from error
    if type(signature) is not bytes or len(signature) != 64:
        raise F09ContractError("RUN_ARTIFACT_SET_SIGNING_FAILED", "issuance_proof", "invalid signer output")
    return RunArtifactSetResultV1(
        manifest,
        target_refs,
        IssuedRunArtifactSetProofV1("Ed25519", port[0], base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")),
    )


def _r41_digest_material(digest: object) -> dict[str, str]:
    if (
        type(digest) is not DigestRef
        or type(digest.algorithm) is not str
        or digest.algorithm != "sha256"
        or type(digest.canonicalization) is not str
        or digest.canonicalization not in ("RFC8785-JCS-UTF8", "RAW-UTF8")
        or type(digest.value) is not str
        or len(digest.value) != 64
        or any(char not in "0123456789abcdef" for char in digest.value)
    ):
        raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof", "invalid digest material")
    return {"algorithm": digest.algorithm, "canonicalization": digest.canonicalization, "value": digest.value}


def _r41_ref_material(ref: object) -> dict[str, object]:
    if type(ref) is not VersionedObjectRef:
        raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof", "invalid target ref")
    for name in ("object_type", "object_id", "schema_version"):
        value = getattr(ref, name)
        if type(value) is not str or not value.strip():
            raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof", "invalid target ref")
    for name in ("revision_id", "contract_version", "source_locator_id", "captured_at"):
        value = getattr(ref, name)
        if value is not None and (type(value) is not str or not value.strip()):
            raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof", "invalid target ref")
    if (
        type(ref.digest_binding) is not DigestPresent
        or type(ref.digest_binding.status) is not str
        or ref.digest_binding.status != "PRESENT"
    ):
        raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof", "target digest must be present")
    return {
        "object_type": ref.object_type,
        "object_id": ref.object_id,
        "revision_id": ref.revision_id,
        "schema_version": ref.schema_version,
        "contract_version": ref.contract_version,
        "digest_binding": {"status": "PRESENT", "digest": _r41_digest_material(ref.digest_binding.digest)},
        "source_locator_id": ref.source_locator_id,
        "captured_at": ref.captured_at,
    }


def _r41_key_material(key: object) -> dict[str, object]:
    if type(key) is not RunArtifactSetKeyV1:
        raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof", "invalid run key")
    return {
        "operation": key.operation,
        "case_id": key.case_id,
        "track": key.track.value,
        "run_id": key.run_id,
        "source_digest": _r41_digest_material(key.source_digest),
        "schema_versions_digest": _r41_digest_material(key.schema_versions_digest),
        "contract_digest": _r41_digest_material(key.contract_digest),
        "input_snapshot_refs_graph_digest": _r41_digest_material(key.input_snapshot_refs_graph_digest),
        "projection_roles": tuple(key.projection_roles),
        "projection_digest_by_role": {
            role: _r41_digest_material(key.projection_digest_by_role[role]) for role in key.projection_roles
        },
        "canonical_key_digest": _r41_digest_material(key.canonical_key_digest),
    }


def _validate_r41_target_refs(
    manifest: object,
    target_refs: object,
    *,
    records_digest: DigestRef,
) -> None:
    if type(manifest) is not ArtifactSetManifest or type(target_refs) is not tuple or len(target_refs) != 4:
        raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof", "invalid target closure")
    roles = ("RUN_SNAPSHOT", "DECISION_RUN", "FEEDBACK_ATTACHMENT")
    for ref, record, role in zip(target_refs[:3], manifest.records, roles, strict=True):
        _r41_ref_material(ref)
        if (
            ref.object_type != role or record.artifact_role != role
            or ref.object_id != record.artifact_id or ref.schema_version != record.schema_version
            or ref.digest_binding.digest != record.observed_digest
        ):
            raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof", "target ref join mismatch")
    manifest_ref = target_refs[3]
    _r41_ref_material(manifest_ref)
    if (
        manifest_ref.object_type != "MANIFEST" or manifest_ref.object_id != manifest.manifest_id
        or manifest_ref.digest_binding.digest != records_digest
    ):
        raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof", "manifest outer ref mismatch")


def _canonicalize_run_artifact_set_issuance_payload_v1(
    manifest: ArtifactSetManifest,
    target_refs: tuple[VersionedObjectRef, ...],
    *,
    records_digest: DigestRef,
) -> bytes:
    _validate_r41_target_refs(manifest, target_refs, records_digest=records_digest)
    value: JcsValue = {
        "domain": "f09.run-artifact-set.issuance.v1",
        "manifest": {
            "manifest_id": manifest.manifest_id,
            "key": _r41_key_material(manifest.key),
            "records_canonical_b64url": base64.urlsafe_b64encode(canonicalize_artifact_records(manifest.records)).rstrip(b"=").decode("ascii"),
            "records_digest": _r41_digest_material(records_digest),
            "state": manifest.state.value,
            "detected_issues": (),
        },
        "target_refs": tuple(_r41_ref_material(ref) for ref in target_refs),
    }
    return canonicalize_bounded_jcs(value)


def canonicalize_run_artifact_set_issuance_payload_v1(
    manifest: ArtifactSetManifest,
    target_refs: tuple[VersionedObjectRef, ...],
) -> bytes:
    return _canonicalize_run_artifact_set_issuance_payload_v1(
        manifest,
        target_refs,
        records_digest=validate_run_artifact_manifest_v1(manifest),
    )


def validate_run_artifact_set_result_issuance_v1(result: RunArtifactSetResultV1) -> None:
    if type(result) is not RunArtifactSetResultV1 or type(result.issuance_proof) is not IssuedRunArtifactSetProofV1:
        raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof", "invalid issuance result")
    proof = result.issuance_proof
    if type(proof.algorithm) is not str or proof.algorithm != "Ed25519" or type(proof.key_id) is not str or not proof.key_id.strip():
        raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof", "invalid issuance proof")
    signature = _base64url_decode(proof.signature_b64url, field_path="issuance_proof")
    if len(signature) != 64:
        raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof", "invalid issuance signature")
    registry = get_run_artifact_set_public_key_registry_v1()
    if (
        type(registry) is not RunArtifactSetPublicKeyRegistryV1
        or type(registry.registry_version) is not str
        or not registry.registry_version.strip()
        or type(registry.keys_by_id) is not MappingProxyType
    ):
        raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof", "invalid issuance registry")
    for registered_key_id, registered_key in registry.keys_by_id.items():
        if (
            type(registered_key_id) is not str
            or not registered_key_id.strip()
            or type(registered_key) is not RunArtifactSetPublicKeyV1
            or type(registered_key.key_id) is not str
            or registered_key.key_id != registered_key_id
            or type(registered_key.status) is not str
            or registered_key.status not in ("ACTIVE", "REVOKED")
        ):
            raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof", "invalid issuance registry")
        if len(_base64url_decode(registered_key.public_key_b64url, field_path="issuance_proof")) != 32:
            raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof", "invalid issuance registry")
    key = registry.keys_by_id.get(proof.key_id)
    if type(key) is not RunArtifactSetPublicKeyV1 or type(key.key_id) is not str or key.key_id != proof.key_id or type(key.status) is not str or key.status != "ACTIVE":
        raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof", "unknown or inactive issuance key")
    public_key_bytes = _base64url_decode(key.public_key_b64url, field_path="issuance_proof")
    if len(public_key_bytes) != 32:
        raise F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof", "invalid issuance public key")
    payload = canonicalize_run_artifact_set_issuance_payload_v1(result.manifest, result.target_refs)
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        Ed25519PublicKey.from_public_bytes(public_key_bytes).verify(signature, payload)
    except F09ContractError:
        raise
    except Exception as error:
        raise F09ContractError(
            "RUN_ARTIFACT_SET_SIGNING_FAILED",
            "issuance_proof",
            "issuance signature verification failed",
        ) from error


def _validate_run_partial_receipt_v1(request: RunArtifactSetRequestV1, manifest: ArtifactSetManifest) -> None:
    if type(manifest) is not ArtifactSetManifest or manifest.key != request.key:
        raise F09IntegrityError("RUN_ARTIFACT.EXISTING_MISMATCH", "/manifest", "run reconciliation manifest mismatch")
    if manifest.manifest_id != f"RUN-MANIFEST:{request.key.canonical_key_digest.value}":
        raise F09IntegrityError("RUN_ARTIFACT.RECONCILE_INVALID", "/manifest_id", "partial run manifest identity invalid")
    if (manifest.state is not ArtifactSetState.PARTIAL or type(manifest.records) is not tuple
            or not manifest.records or manifest.digest != digest_artifact_records(manifest.records)):
        raise F09IntegrityError("RUN_ARTIFACT.RECONCILE_INVALID", "/manifest", "partial run receipt invalid")
    for index, record in enumerate(manifest.records):
        if (index >= len(request.key.projection_roles) or type(record) is not ArtifactRecord
                or record.artifact_role != request.key.projection_roles[index]):
            raise F09IntegrityError("RUN_ARTIFACT.RECONCILE_INVALID", "/records", "partial receipt role closure invalid")
        artifact_id = f"RUN-ARTIFACT:{request.key.canonical_key_digest.value}:{record.artifact_role}"
        expected_locator = "/".join((
            "run-artifacts", request.key.canonical_key_digest.value, _RUN_FILENAMES[record.artifact_role],
        ))
        if (record.artifact_id != artifact_id or record.path_locator != expected_locator
                or record.track != request.key.track or record.case_id != request.key.case_id
                or record.run_id != request.key.run_id or record.statement_set_id is not None or record.issue_ids != ()
                or record.schema_version != request.schema_version
                or record.expected_digest != request.key.projection_digest_by_role[record.artifact_role] or not record.attempts):
            raise F09IntegrityError("RUN_ARTIFACT.RECONCILE_INVALID", "/records", "partial receipt identity invalid")
        for number, attempt in enumerate(record.attempts, start=1):
            predecessor = None if number == 1 else record.attempts[number - 2].attempt_id
            if (type(attempt) is not ArtifactWriteAttempt or attempt.artifact_id != artifact_id
                    or attempt.idempotency_key != request.key.canonical_key_digest.value or attempt.attempt_number != number
                    or attempt.retry_of_attempt_id != predecessor or not isinstance(attempt.attempt_id, str)
                    or not attempt.attempt_id or not isinstance(attempt.started_at, str) or not attempt.started_at
                    or _digest_run_input_snapshot_refs_v1(attempt.input_snapshot_refs) != request.key.input_snapshot_refs_graph_digest):
                raise F09IntegrityError("RUN_ARTIFACT.RECONCILE_INVALID", "/records", "partial receipt attempt invalid")
            if attempt is not record.attempts[-1] and (
                attempt.outcome != "FAILED" or attempt.finished_at != attempt.started_at
                or attempt.observed_digest is not None or attempt.error_class is None
                or attempt.error_message_digest is None
            ):
                raise F09IntegrityError("RUN_ARTIFACT.RECONCILE_INVALID", "/records", "partial receipt history invalid")
        terminal = record.attempts[-1]
        if terminal.outcome == "UNKNOWN":
            valid = (record.state is ArtifactItemState.WRITTEN_UNVERIFIED and record.observed_digest is None
                     and terminal.finished_at is None and terminal.observed_digest is None
                     and terminal.error_class is None and terminal.error_message_digest is None)
        elif terminal.outcome == "FAILED":
            valid = (record.state is ArtifactItemState.FAILED and record.observed_digest is None
                     and terminal.finished_at == terminal.started_at and terminal.observed_digest is None
                     and terminal.error_class is not None and terminal.error_message_digest is not None)
        else:
            valid = (terminal.outcome == "SUCCEEDED" and record.state is ArtifactItemState.VERIFIED
                     and record.observed_digest == record.expected_digest
                     and terminal.finished_at == terminal.started_at
                     and terminal.observed_digest == record.expected_digest
                     and terminal.error_class is None and terminal.error_message_digest is None)
        if not valid:
            raise F09IntegrityError("RUN_ARTIFACT.RECONCILE_INVALID", "/records", "partial receipt terminal invalid")
        if terminal.outcome != "SUCCEEDED" and index != len(manifest.records) - 1:
            raise F09IntegrityError("RUN_ARTIFACT.RECONCILE_INVALID", "/records", "partial receipt is not a lifecycle prefix")
    terminal = manifest.records[-1].attempts[-1]
    if terminal.outcome not in ("FAILED", "UNKNOWN"):
        raise F09IntegrityError("RUN_ARTIFACT.RECONCILE_INVALID", "/records", "partial receipt terminal must be unresolved")
    expected_issue = DetectedIssue(
        "RUN_ARTIFACT.WRITE_FAILED", f"/records/{manifest.records[-1].artifact_role}"
    )
    if manifest.detected_issues != (expected_issue,):
        raise F09IntegrityError("RUN_ARTIFACT.RECONCILE_INVALID", "/detected_issues", "partial run receipt issues invalid")


def reconcile_run_artifact_set_v1(root: Path, request: RunArtifactSetRequestV1, manifest: ArtifactSetManifest) -> ArtifactSetManifest:
    _validate_run_request_v1(request)
    _validate_run_partial_receipt_v1(request, manifest)
    operation_root = _resolve_run_artifact_root_v1(root, request.key)
    records: tuple[ArtifactRecord, ...] = ()
    resolved_unknown = False
    for record in manifest.records:
        if record.artifact_role not in request.key.projection_roles or not record.attempts:
            raise F09IntegrityError("RUN_ARTIFACT.RECONCILE_INVALID", "/records", "invalid unknown receipt graph")
        attempt = record.attempts[-1]
        target = operation_root / _RUN_FILENAMES[record.artifact_role]
        if attempt.outcome == "UNKNOWN":
            try:
                matches = (target.is_file() and _payload_digest(target.read_bytes())
                           == request.key.projection_digest_by_role[record.artifact_role])
            except OSError as error:
                raise F09IntegrityError(
                    "RUN_ARTIFACT.READBACK_MISMATCH", "/records", "unknown run final is missing or mismatched"
                ) from error
            if not matches:
                raise F09IntegrityError("RUN_ARTIFACT.READBACK_MISMATCH", "/records", "unknown run final is missing or mismatched")
            observed = request.key.projection_digest_by_role[record.artifact_role]
            resolved_attempt = replace(attempt, outcome="SUCCEEDED", finished_at=attempt.started_at, observed_digest=observed)
            records += (replace(record, state=ArtifactItemState.VERIFIED, expected_digest=observed, observed_digest=observed, attempts=record.attempts[:-1] + (resolved_attempt,)),)
            resolved_unknown = True
        else:
            records += (record,)
    if not resolved_unknown:
        return manifest
    expected_roles = request.key.projection_roles
    if tuple(record.artifact_role for record in records) != expected_roles:
        return ArtifactSetManifest(
            manifest_id=manifest.manifest_id, key=request.key, records=records,
            state=ArtifactSetState.PARTIAL, digest=digest_artifact_records(records),
            detected_issues=manifest.detected_issues,
        )
    reconciled = ArtifactSetManifest(
        manifest_id=manifest.manifest_id, key=request.key, records=records,
        state=ArtifactSetState.COMPLETE_VERIFIED, digest=digest_artifact_records(records), detected_issues=(),
    )
    validate_run_artifact_manifest_v1(reconciled)
    return reconciled
