"""Seal the exact governance capability used by a prospective run.

This module deliberately keeps capability identity separate from prediction
results.  A prospective artifact may refer to a capability only after the
governance result, its explicit task projection, and the source claim have
been sealed under one repository authority.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from engine.application.governance_shadow_types import (
    GovernanceShadowResult,
    shadow_result_digest,
)
from engine.evaluation.governance_shadow_adapter import (
    GovernanceShadowTaskProjection,
    ShadowPredictionBinding,
)
from engine.evaluation.prospective_artifacts import (
    ArtifactRef,
    _authority_root,
    _repository_authority,
    _RepositoryAuthority,
    publish_new_json,
    validate_parent_ref,
)
from engine.governance.governance_claim import GovernanceClaim
from engine.governance.governance_claim_values import (
    AdapterProvenance,
    ClaimEvidenceGrade,
    ClaimKind,
)

_IDENTITY_SCHEMA = "prospective-capability-identity/v1"
_SOURCE_SCHEMA = "prospective-governance-capability-source/v1"
_SHA256 = re.compile(r"[0-9a-f]{64}")
_IDENTITY_FIELDS = frozenset(
    {
        "schema_version",
        "artifact_path",
        "created_at",
        "parents",
        "governance_source_ref",
        "source_claim_id",
        "source_claim_content_digest",
        "school_id",
        "task_id",
        "claim_kind",
        "evidence_grade",
        "capability_version",
        "artifact_sha256",
    }
)
_SOURCE_FIELDS = frozenset(
    {
        "schema_version",
        "artifact_path",
        "created_at",
        "parents",
        "source_claim",
        "governance_result",
        "governance_projection",
        "artifact_sha256",
    }
)


@dataclass(frozen=True, slots=True)
class CapabilityIdentity:
    """The immutable identity of one governance-backed capability."""

    source_claim_id: str
    source_claim_content_digest: str
    governance_source_ref: ArtifactRef
    school_id: str
    task_id: str
    claim_kind: ClaimKind
    evidence_grade: ClaimEvidenceGrade
    capability_version: str


# Keep the longer name available to callers that want to make the artifact
# boundary explicit without forcing the prospective pipeline to know a second
# representation.
ProspectiveCapabilityIdentity = CapabilityIdentity


def _text(value: object, field: str) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{field} must be non-empty exact text")
    return value


def _digest(value: object, field: str) -> str:
    value = _text(value, field)
    if _SHA256.fullmatch(value) is None:
        raise ValueError(f"{field} must be a lowercase SHA-256")
    return value


def _utc(value: object, field: str) -> str:
    value = _text(value, field)
    if not value.endswith("Z"):
        raise ValueError(f"{field} must be an ISO 8601 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO 8601 UTC timestamp") from error
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError(f"{field} must be an ISO 8601 UTC timestamp")
    return value


def _reference(value: object, field: str) -> ArtifactRef:
    if type(value) is not ArtifactRef:
        raise TypeError(f"{field} must be an exact ArtifactRef")
    _text(value.artifact_path, f"{field}.artifact_path")
    _digest(value.artifact_sha256, f"{field}.artifact_sha256")
    return value


def _claim_fields(claim: GovernanceClaim) -> dict[str, str]:
    if type(claim) is not GovernanceClaim:
        raise TypeError("claim must be an exact GovernanceClaim")
    provenance = claim.adapter_provenance
    if type(provenance) is not AdapterProvenance:
        raise ValueError("capability claim must have adapter provenance")
    return {
        "claim_id": _text(claim.claim_id, "source_claim_id"),
        "content_digest": _digest(
            claim.content_digest.value, "source_claim_content_digest"
        ),
        "school_id": _text(claim.school_id, "school_id"),
        "task_id": _text(claim.task_id, "task_id"),
        "claim_kind": claim.claim_kind.value,
        "evidence_grade": claim.evidence_grade.value,
        "capability_version": _text(
            provenance.adapter_version, "capability_version"
        ),
    }


def _projection_fields(
    projection: GovernanceShadowTaskProjection,
    claim: GovernanceClaim,
    result: GovernanceShadowResult,
) -> dict[str, Any]:
    if type(projection) is not GovernanceShadowTaskProjection:
        raise TypeError("governance_projection must be an exact projection")
    if type(result) is not GovernanceShadowResult:
        raise TypeError("governance_result must be an exact shadow result")
    if shadow_result_digest(result) != result.result_digest:
        raise ValueError("governance result digest is invalid")
    if projection.schema_version != "governance-shadow-task-projection/v1":
        raise ValueError("governance projection schema is invalid")
    if projection.expected_result_digest != result.result_digest:
        raise ValueError("governance projection result binding is invalid")
    if (
        projection.expected_fact_snapshot_id != result.fact_snapshot_id
        or projection.expected_fact_snapshot_digest != result.fact_snapshot_digest
        or projection.expected_input_digest != result.input_digest
    ):
        raise ValueError("governance projection snapshot binding is invalid")
    if projection.source_execution_state != "executed":
        raise ValueError("capability identity requires an executed projection")
    if projection.capability_state != "certified":
        raise ValueError("capability identity requires a certified projection")
    if projection.school_id != claim.school_id or projection.task_id != claim.task_id:
        raise ValueError("governance projection does not own the source claim")

    matching_traces = [
        trace
        for trace in result.claims
        if trace.claim_id == claim.claim_id
        and trace.content_digest == claim.content_digest.value
    ]
    if len(matching_traces) != 1:
        raise ValueError("governance result does not contain one exact source claim")

    prediction = projection.prediction
    if type(prediction) is not ShadowPredictionBinding:
        raise ValueError("capability identity requires an explicit prediction binding")
    if type(prediction.source_claim) is not GovernanceClaim:
        raise ValueError("prediction binding source claim is invalid")
    if (
        prediction.source_claim.claim_id != claim.claim_id
        or prediction.source_claim.content_digest.value != claim.content_digest.value
    ):
        raise ValueError("prediction binding source claim differs from claim")

    return {
        "schema_version": projection.schema_version,
        "case_id": _text(projection.case_id, "projection.case_id"),
        "school_id": _text(projection.school_id, "projection.school_id"),
        "task_id": _text(projection.task_id, "projection.task_id"),
        "task_catalog_version": _text(
            projection.task_catalog_version, "projection.task_catalog_version"
        ),
        "rule_version": _text(projection.rule_version, "projection.rule_version"),
        "calculator_version": _text(
            projection.calculator_version, "projection.calculator_version"
        ),
        "expected_result_digest": projection.expected_result_digest,
        "expected_fact_snapshot_id": projection.expected_fact_snapshot_id,
        "expected_fact_snapshot_digest": projection.expected_fact_snapshot_digest,
        "expected_input_digest": projection.expected_input_digest,
        "source_execution_state": projection.source_execution_state,
        "capability_state": projection.capability_state,
        "rationale": _text(projection.rationale, "projection.rationale"),
        "prediction": {
            "source_claim_id": claim.claim_id,
            "source_claim_content_digest": claim.content_digest.value,
            "event_conclusion_id": prediction.event_conclusion_id,
            "probability": prediction.probability,
            "horizon": prediction.horizon,
            "start_year": prediction.start_year,
            "end_year": prediction.end_year,
            "evidence_refs": list(prediction.evidence_refs),
            "fact_refs": list(prediction.fact_refs),
            "falsifier": prediction.falsifier,
        },
    }


def _source_document(
    *,
    source_path: Path,
    created_at: str,
    claim_fields: Mapping[str, str],
    result: GovernanceShadowResult,
    projection_fields: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": _SOURCE_SCHEMA,
        "artifact_path": source_path.as_posix(),
        "created_at": created_at,
        "parents": [],
        "source_claim": dict(claim_fields),
        "governance_result": {
            "schema_version": result.schema_version,
            "runner_version": result.runner_version,
            "status": result.status,
            "result_digest": result.result_digest,
            "canonical": result.to_canonical(),
        },
        "governance_projection": dict(projection_fields),
    }


def _identity_payload(
    *,
    output_path: Path,
    created_at: str,
    claim_fields: Mapping[str, str],
    source_ref: ArtifactRef,
) -> dict[str, Any]:
    source_value = {
        "artifact_path": source_ref.artifact_path,
        "artifact_sha256": source_ref.artifact_sha256,
    }
    return {
        "schema_version": _IDENTITY_SCHEMA,
        "artifact_path": output_path.as_posix(),
        "created_at": created_at,
        "parents": [source_value],
        "governance_source_ref": source_value,
        "source_claim_id": claim_fields["claim_id"],
        "source_claim_content_digest": claim_fields["content_digest"],
        "school_id": claim_fields["school_id"],
        "task_id": claim_fields["task_id"],
        "claim_kind": claim_fields["claim_kind"],
        "evidence_grade": claim_fields["evidence_grade"],
        "capability_version": claim_fields["capability_version"],
    }


def _identity_from_document(
    document: Mapping[str, Any], source_ref: ArtifactRef
) -> CapabilityIdentity:
    if document.get("schema_version") != _IDENTITY_SCHEMA:
        raise ValueError("capability identity schema is invalid")
    try:
        claim_kind = ClaimKind(document["claim_kind"])
        evidence_grade = ClaimEvidenceGrade(document["evidence_grade"])
    except (KeyError, ValueError) as error:
        raise ValueError("capability identity enum field is invalid") from error
    return CapabilityIdentity(
        source_claim_id=_text(document.get("source_claim_id"), "source_claim_id"),
        source_claim_content_digest=_digest(
            document.get("source_claim_content_digest"),
            "source_claim_content_digest",
        ),
        governance_source_ref=source_ref,
        school_id=_text(document.get("school_id"), "school_id"),
        task_id=_text(document.get("task_id"), "task_id"),
        claim_kind=claim_kind,
        evidence_grade=evidence_grade,
        capability_version=_text(
            document.get("capability_version"), "capability_version"
        ),
    )


def _validate_source_binding(
    source: Mapping[str, Any], identity: CapabilityIdentity, source_ref: ArtifactRef
) -> None:
    if set(source) != _SOURCE_FIELDS:
        raise ValueError("governance source schema fields are invalid")
    if source.get("schema_version") != _SOURCE_SCHEMA:
        raise ValueError("governance source schema is invalid")
    if source.get("artifact_path") != source_ref.artifact_path:
        raise ValueError("governance source artifact path is invalid")
    _utc(source.get("created_at"), "governance source created_at")
    source_claim = source.get("source_claim")
    if not isinstance(source_claim, Mapping):
        raise TypeError("governance source claim is missing")
    expected = {
        "claim_id": identity.source_claim_id,
        "content_digest": identity.source_claim_content_digest,
        "school_id": identity.school_id,
        "task_id": identity.task_id,
        "claim_kind": identity.claim_kind.value,
        "evidence_grade": identity.evidence_grade.value,
        "capability_version": identity.capability_version,
    }
    if dict(source_claim) != expected:
        raise ValueError("governance source claim differs from capability identity")
    result = source.get("governance_result")
    projection = source.get("governance_projection")
    if not isinstance(result, Mapping) or not isinstance(projection, Mapping):
        raise TypeError("governance source is incomplete")
    if result.get("schema_version") != "governance.shadow-result.v1":
        raise ValueError("governance source result schema is invalid")
    result_digest = result.get("result_digest")
    if not isinstance(result_digest, str) or _SHA256.fullmatch(result_digest) is None:
        raise ValueError("governance source result digest is invalid")
    if projection.get("expected_result_digest") != result_digest:
        raise ValueError("governance source result binding is invalid")
    if projection.get("school_id") != identity.school_id or projection.get(
        "task_id"
    ) != identity.task_id:
        raise ValueError("governance source projection differs from identity")
    prediction = projection.get("prediction")
    if (
        not isinstance(prediction, Mapping)
        or prediction.get("source_claim_id") != identity.source_claim_id
        or prediction.get("source_claim_content_digest")
        != identity.source_claim_content_digest
    ):
        raise ValueError("governance source prediction binding differs from identity")


def _validate_capability_identity_ref_with_authority(
    ref: ArtifactRef,
    *,
    authority: _RepositoryAuthority,
) -> CapabilityIdentity:
    """Authenticate one identity artifact and all of its governance parents."""
    if type(authority) is not _RepositoryAuthority:
        raise TypeError("authority must be an exact repository authority")
    _reference(ref, "capability identity ref")
    admitted_root = _authority_root(authority)
    document = validate_parent_ref(ref, admitted_root=admitted_root)
    if set(document) != _IDENTITY_FIELDS:
        raise ValueError("capability identity schema fields are invalid")
    if document.get("artifact_path") != ref.artifact_path:
        raise ValueError("capability identity artifact path differs from reference")
    _utc(document.get("created_at"), "capability identity created_at")
    source_value = document.get("governance_source_ref")
    if not isinstance(source_value, Mapping) or set(source_value) != {
        "artifact_path",
        "artifact_sha256",
    }:
        raise ValueError("capability identity governance source reference is invalid")
    source_ref = ArtifactRef(
        str(source_value["artifact_path"]), str(source_value["artifact_sha256"])
    )
    if document.get("parents") != [dict(source_value)]:
        raise ValueError("capability identity parent lineage is invalid")
    identity = _identity_from_document(document, source_ref)
    source = validate_parent_ref(source_ref, admitted_root=admitted_root)
    _validate_source_binding(source, identity, source_ref)
    return identity


def validate_capability_identity_ref(ref: ArtifactRef) -> CapabilityIdentity:
    """Validate an identity using the process' canonical repository authority."""
    return _validate_capability_identity_ref_with_authority(
        ref, authority=_repository_authority()
    )


def build_capability_identity_artifact(
    claim: GovernanceClaim,
    *,
    governance_result: GovernanceShadowResult,
    governance_projection: GovernanceShadowTaskProjection,
    created_at: str,
    source_output_path: Path,
    output_path: Path,
    dry_run: bool = False,
) -> tuple[CapabilityIdentity, ArtifactRef]:
    """Create a source artifact and a sealed capability identity artifact.

    The source artifact is written first and becomes the sole parent of the
    identity artifact.  ``dry_run`` computes both references without writing;
    it never weakens the type or lineage checks.
    """
    if type(dry_run) is not bool:
        raise TypeError("dry_run must be bool")
    created = _utc(created_at, "created_at")
    claim_fields = _claim_fields(claim)
    projection_fields = _projection_fields(
        governance_projection, claim, governance_result
    )
    if not isinstance(source_output_path, Path) or not isinstance(output_path, Path):
        raise TypeError("source_output_path and output_path must be Path values")
    if source_output_path == output_path:
        raise ValueError("source and identity output paths must differ")

    authority = _repository_authority()
    admitted_root = _authority_root(authority)
    source_path = source_output_path.absolute()
    identity_path = output_path.absolute()
    source_payload = _source_document(
        source_path=source_path,
        created_at=created,
        claim_fields=claim_fields,
        result=governance_result,
        projection_fields=projection_fields,
    )
    source_ref = publish_new_json(
        source_path,
        source_payload,
        dry_run=dry_run,
        admitted_root=admitted_root,
    )
    identity_payload = _identity_payload(
        output_path=identity_path,
        created_at=created,
        claim_fields=claim_fields,
        source_ref=source_ref,
    )
    identity_ref = publish_new_json(
        identity_path,
        identity_payload,
        dry_run=dry_run,
        admitted_root=admitted_root,
    )
    identity = _identity_from_document(identity_payload, source_ref)
    return identity, identity_ref


__all__ = [
    "CapabilityIdentity",
    "ProspectiveCapabilityIdentity",
    "build_capability_identity_artifact",
    "validate_capability_identity_ref",
]
