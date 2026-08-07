from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Literal, TypeAlias, Union

from engine.f09.canonical_json import JcsValue, bounded_jcs_sha256
from engine.f09.contracts import (
    ContractVersionRef,
    DecisionAction,
    DetectedIssue,
    DigestRef,
    EvidenceTrack,
    FieldEvaluatorState,
    FieldMapping,
    FrozenDeclarationBinding,
    FunctionId,
    ImmutableJsonSourceBinding,
    ObjectRef,
    RunTrack,
    SourceFieldState,
    TransformationRecord,
)
from engine.f09.decision import (
    BasisRecordIds,
    DecisionActionEnvelope,
    DecisionEvaluationResult,
)
from engine.f09.errors import F09ContractError, F09IntegrityError, F09SourceError
from engine.f09.evidence import NormalizedEvidencePackage, validate_for_pi220


@dataclass(frozen=True)
class DigestPresent:
    status: Literal["PRESENT"]
    digest: DigestRef


@dataclass(frozen=True)
class DigestMissing:
    status: Literal["MISSING"]
    digest: None
    issue_id: str


DigestBinding: TypeAlias = Union[DigestPresent, DigestMissing]


@dataclass(frozen=True)
class VersionedObjectRef:
    object_type: str
    object_id: str
    revision_id: str | None
    schema_version: str
    contract_version: str | None
    digest_binding: DigestBinding
    source_locator_id: str | None
    captured_at: str | None


@dataclass(frozen=True)
class SnapshotRef:
    source_snapshot_id: str
    source_type: Literal["INPUT", "CONTRACT", "MACHINE_APPENDIX", "FINDING", "DECISION", "REPORT_CONTEXT", "ARTIFACT", "FEEDBACK"]
    source_locator_ids: tuple[str, ...]
    schema_version: str | None
    contract_version: str | None
    content_digest: DigestRef
    captured_at: str
    immutability: Literal["IMMUTABLE", "MUTABLE_SOURCE_CAPTURE"]


@dataclass(frozen=True)
class DecisionTraceRef:
    result_ref: VersionedObjectRef
    action_id: str
    selected_action: DecisionAction
    basis_record_ids: BasisRecordIds
    blocking_issue_ids: tuple[str, ...]
    nonblocking_issue_ids: tuple[str, ...]
    source_decision_refs: tuple[str, ...]
    output_precision_binding: FrozenDeclarationBinding
    validation_plan_binding: FrozenDeclarationBinding
    structural_validity: Literal["VALID", "INVALID"]


@dataclass(frozen=True)
class TraceNode:
    object_ref: VersionedObjectRef
    object_role: Literal["SOURCE", "NORMALIZED_EVIDENCE", "DECISION_INPUT", "DECISION_OUTPUT", "STANDARD_STATEMENT", "ARTIFACT", "FEEDBACK", "LEARNING_ELIGIBILITY"]
    track: RunTrack
    integrity: Literal["VALID", "INVALID", "UNRESOLVED"]


@dataclass(frozen=True)
class TraceEdge:
    edge_id: str
    edge_type: Literal["LOCATED_AT", "SNAPSHOT_OF", "NORMALIZED_FROM", "DERIVED_FROM", "EVALUATED_BY", "BASIS_FOR", "RENDERED_AS", "PROJECTED_TO", "ANCHORED_TO", "FEEDBACK_TARGETS", "VALIDATED_AGAINST", "ELIGIBLE_FOR", "SUPERSEDES"]
    from_ref: VersionedObjectRef
    to_ref: VersionedObjectRef
    transformation_id: str | None
    fidelity: Literal["LOSSLESS", "PARTIAL", "LOSSY", "UNSUPPORTED"]
    track_crossing: Literal["NONE", "AUDIT_ONLY"]
    issue_ids: tuple[str, ...]


@dataclass(frozen=True)
class TraceEnvelope:
    trace_id: str
    trace_schema_version: str
    case_id: str
    track: RunTrack
    source_snapshot_refs: tuple[SnapshotRef, ...]
    normalized_package_ref: VersionedObjectRef
    decision_result_ref: VersionedObjectRef
    statement_set_ref: VersionedObjectRef | None
    nodes: tuple[TraceNode, ...]
    edges: tuple[TraceEdge, ...]
    transformations: tuple[TransformationRecord, ...]
    artifacts: tuple[ArtifactRecord, ...]
    feedback_bindings: tuple[FeedbackBinding, ...]
    integrity: Literal["VALID", "INVALID", "UNRESOLVED"]
    blocking_issue_ids: tuple[str, ...]
    created_at: str


@dataclass(frozen=True)
class CardIdentityRef:
    card_identity_ref_id: str
    card_id: FunctionId
    normative_contract_ref: VersionedObjectRef
    machine_appendix_ref: VersionedObjectRef
    field_path: str
    source_field_state: SourceFieldState
    evaluator_state: FieldEvaluatorState
    declaration_status: Literal["FROZEN_DECLARATION"]
    runtime_capability_status: Literal["REFERENCE_ONLY_NOT_IMPLEMENTATION_PROOF"]
    source_locator_ids: tuple[str, ...]
    issue_ids: tuple[str, ...]


@dataclass(frozen=True)
class StandardStatement:
    statement_id: str
    statement_revision_id: str
    statement_schema_version: str
    case_id: str
    statement_set_id: str
    track: RunTrack
    semantic_scope: str
    domain: str
    statement_text: str
    display_section: str | None
    decision_result_id: str
    action_id: str
    basis_record_ids: BasisRecordIds
    evidence_refs: tuple[VersionedObjectRef, ...]
    relation_ids: tuple[str, ...]
    source_locator_ids: tuple[str, ...]
    card_identity_refs: tuple[CardIdentityRef, ...]
    confidence_snapshot_ref: VersionedObjectRef | None
    output_precision_binding: FrozenDeclarationBinding
    validation_plan_binding: FrozenDeclarationBinding
    feedback_policy: Literal["FEEDBACK_ALLOWED", "HUMAN_REVIEW_ONLY", "NOT_FEEDBACK_TARGET"]
    content_digest: DigestRef
    integrity: Literal["VALID", "INVALID", "UNRESOLVED"]
    issue_ids: tuple[str, ...]


@dataclass(frozen=True)
class StatementSet:
    statement_set_id: str
    statement_schema_version: str
    case_id: str
    track: RunTrack
    source_package_ref: VersionedObjectRef
    decision_trace_ref: DecisionTraceRef
    statements: tuple[StandardStatement, ...]
    content_digest: DigestRef
    generated_at: str
    publication_state: Literal["DRAFT", "PUBLISHABLE", "BLOCKED", "SUPERSEDED"]
    issue_ids: tuple[str, ...]


@dataclass(frozen=True)
class ProjectionValidationResult:
    valid: bool
    detected_issues: tuple[DetectedIssue, ...]


_PI300_DIGEST = DigestRef(
    "sha256",
    "RFC8785-JCS-UTF8",
    "67517fe2d04fb0fe580e031643dab2ad53fcdb8c90707ba4d496c316dd87f5e7",
)
_PI300_CAPTURED_AT = "2026-07-19T00:00:00Z"
_SOURCE_LAYOUT = (
    (
        "SOURCE-STATE-1",
        ("SRCLOC-STATE-LEVEL", "SRCLOC-STATE-POSITION", "SRCLOC-STATE-AS-OF"),
        (("/value/level", "/payload/value/level"), ("/value/position", "/payload/value/position"), ("/value/as_of", "/temporal_scope/as_of/value")),
    ),
    (
        "SOURCE-EVENT-1",
        ("SRCLOC-EVENT-LEVEL", "SRCLOC-EVENT-CHANGE", "SRCLOC-EVENT-START", "SRCLOC-EVENT-END", "SRCLOC-EVENT-START-INCLUSIVE", "SRCLOC-EVENT-END-INCLUSIVE"),
        (("/value/level", "/payload/value/level"), ("/value/change", "/payload/value/change"), ("/value/interval/start", "/temporal_scope/interval/start/value"), ("/value/interval/end", "/temporal_scope/interval/end/value"), ("/value/interval/start_inclusive", "/temporal_scope/interval/start_inclusive"), ("/value/interval/end_inclusive", "/temporal_scope/interval/end_inclusive")),
    ),
    (
        "SOURCE-OUTCOME-1",
        ("SRCLOC-OUTCOME-AXIS", "SRCLOC-OUTCOME-ACTION", "SRCLOC-OUTCOME-OBJECT", "SRCLOC-OUTCOME-TENSE"),
        (("/value/axis", "/payload/value/axis"), ("/value/action", "/payload/value/action"), ("/value/object", "/payload/value/object"), ("/value/tense", "/payload/value/tense")),
    ),
)


def _canonical_digest(value: object, *, field_path: str) -> DigestRef:
    try:
        return bounded_jcs_sha256(_canonical_value(value))
    except F09ContractError as error:
        raise F09ContractError(
            error.issue_code,
            field_path,
            "canonical identity payload is invalid",
        ) from None


def _statement_text(action: DecisionAction) -> str:
    return {
        DecisionAction.OUTPUT: "axis action object tense",
        DecisionAction.CONDITIONAL: "conditional decision audit",
        DecisionAction.ASK: "question request audit",
        DecisionAction.ABSTAIN: "abstention audit",
        DecisionAction.HUMAN_REVIEW: "human review audit",
    }[action]


def _canonical_value(value: object) -> JcsValue:
    if value is None or type(value) in (bool, str):
        return value
    if isinstance(value, Enum):
        return _canonical_value(value.value)
    if type(value) is tuple:
        return tuple(_canonical_value(item) for item in value)
    if isinstance(value, Mapping):
        if not all(type(key) is str for key in value):
            raise F09ContractError(
                "STATEMENT.RECORD_INVALID",
                "/statements/0",
                "canonical mapping keys must be exact strings",
            )
        return {
            key: _canonical_value(item)
            for key, item in value.items()
        }
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _canonical_value(getattr(value, field.name))
            for field in fields(value)
        }
    raise F09ContractError(
        "STATEMENT.RECORD_INVALID",
        "/statements/0",
        "statement canonical payload contains an unsupported value",
    )


def _statement_identity(
    case_id: str,
    semantic_scope: str,
    basis_record_ids: tuple[str, ...],
) -> str:
    identity_digest = bounded_jcs_sha256(
        {
            "case_id": case_id,
            "semantic_scope": semantic_scope,
            "normalized_basis_identity": basis_record_ids,
        }
    )
    return f"STATEMENT-{identity_digest.value[:20]}"


def _statement_revision_digest(statement: StandardStatement) -> DigestRef:
    payload = {
        field.name: _canonical_value(getattr(statement, field.name))
        for field in fields(statement)
        if field.name not in (
            "statement_set_id",
            "statement_revision_id",
            "content_digest",
        )
    }
    return bounded_jcs_sha256(payload)


def _statement_content_digest(statement: StandardStatement) -> DigestRef:
    payload = {
        field.name: _canonical_value(getattr(statement, field.name))
        for field in fields(statement)
        if field.name not in ("statement_revision_id", "content_digest")
    }
    return bounded_jcs_sha256(payload)


def _sign_statement(statement: StandardStatement) -> StandardStatement:
    revision_digest = _statement_revision_digest(statement)
    revised = replace(
        statement,
        statement_revision_id=f"rev-{revision_digest.value[:16]}",
    )
    return replace(revised, content_digest=_statement_content_digest(revised))


def _digest_ref_shape_valid(digest: object) -> bool:
    return (
        isinstance(digest, DigestRef)
        and type(digest.algorithm) is str
        and bool(digest.algorithm)
        and type(digest.canonicalization) is str
        and bool(digest.canonicalization)
        and type(digest.value) is str
        and len(digest.value) == 64
        and all(char in "0123456789abcdef" for char in digest.value)
    )


def _digest_binding_shape_valid(binding: object) -> bool:
    if isinstance(binding, DigestPresent):
        return binding.status == "PRESENT" and _digest_ref_shape_valid(binding.digest)
    if isinstance(binding, DigestMissing):
        return (
            binding.status == "MISSING"
            and binding.digest is None
            and type(binding.issue_id) is str
            and bool(binding.issue_id)
        )
    return False


def _versioned_ref_shape_valid(ref: object) -> bool:
    return (
        isinstance(ref, VersionedObjectRef)
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


def _statement_set_identity(
    case_id: str,
    result_ref: VersionedObjectRef,
    statement_revision_ids: tuple[str, ...],
) -> tuple[str, DigestRef]:
    identity_digest = bounded_jcs_sha256(
        {
            "case_id": case_id,
            "decision_result_ref": _canonical_value(result_ref),
            "statement_revision_ids": statement_revision_ids,
        }
    )
    return f"STATEMENT-SET-{identity_digest.value[:20]}", identity_digest


def _statement_set_content_digest(statement_set: StatementSet) -> DigestRef:
    payload = {
        field.name: _canonical_value(getattr(statement_set, field.name))
        for field in fields(statement_set)
        if field.name != "content_digest"
    }
    return bounded_jcs_sha256(payload)


def _versioned_ref(
    object_type: str,
    object_id: str,
    *,
    source_locator_id: str | None = None,
    captured_at: str | None = None,
    digest: DigestRef,
    revision_id: str | None = "rev-1",
    schema_version: str = "f09.trace.v1",
    contract_version: str | None = "pi-230-v1",
) -> VersionedObjectRef:
    return VersionedObjectRef(
        object_type=object_type,
        object_id=object_id,
        revision_id=revision_id,
        schema_version=schema_version,
        contract_version=contract_version,
        digest_binding=DigestPresent("PRESENT", digest),
        source_locator_id=source_locator_id,
        captured_at=captured_at,
    )


def _contract_ref_shape_valid(ref: object) -> bool:
    return (
        isinstance(ref, ContractVersionRef)
        and type(ref.normative_contract_path) is str
        and bool(ref.normative_contract_path)
        and type(ref.machine_appendix_path) is str
        and bool(ref.machine_appendix_path)
        and type(ref.contract_version) is str
        and bool(ref.contract_version)
        and type(ref.content_digest) is str
        and len(ref.content_digest) == 64
        and all(char in "0123456789abcdef" for char in ref.content_digest)
    )


def _authoritative_card_source_ref(object_type: str) -> VersionedObjectRef | None:
    root = Path(__file__).resolve().parents[2]
    if object_type == "CONTRACT":
        path = Path("engine/contracts/12-real-world-function-evidence-cards-v1.md")
        object_id = "F09-NORMATIVE-CONTRACT"
        schema_version = "markdown-contract.v1"
    elif object_type == "MACHINE_APPENDIX":
        path = Path("mapping/real-world-function-evidence-cards-v1.yaml")
        object_id = "F09-MACHINE-APPENDIX"
        schema_version = "machine-appendix.v1"
    else:
        return None
    try:
        digest = DigestRef(
            "sha256",
            "RAW-BYTES",
            hashlib.sha256((root / path).read_bytes()).hexdigest(),
        )
    except OSError:
        return None
    return VersionedObjectRef(
        object_type=object_type,
        object_id=object_id,
        revision_id="rev-frozen",
        schema_version=schema_version,
        contract_version="real-world-function-evidence-cards-v1",
        digest_binding=DigestPresent("PRESENT", digest),
        source_locator_id=path.as_posix(),
        captured_at="2026-07-19T00:00:00Z",
    )


def _card_source_ref_valid(ref: object, object_type: str) -> bool:
    authoritative_ref = _authoritative_card_source_ref(object_type)
    return (
        authoritative_ref is not None
        and _versioned_ref_shape_valid(ref)
        and isinstance(ref.digest_binding, DigestPresent)
        and ref == authoritative_ref
    )


def _build_standard_statement(
    *,
    case_id: str,
    track: RunTrack,
    statement_set_id: str,
    result: DecisionEvaluationResult,
    evidence_refs: tuple[VersionedObjectRef, ...],
    normative_contract_ref: VersionedObjectRef,
    machine_appendix_ref: VersionedObjectRef,
) -> StandardStatement:
    action = result.action_envelope
    statement_id = _statement_identity(
        case_id,
        "F09",
        action.basis_record_ids,
    )
    card_ref = CardIdentityRef(
        card_identity_ref_id="CARD-REF-F09",
        card_id="F09",
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
        field_path="/cards/F09",
        source_field_state="PRESENT_VALUE",
        evaluator_state=FieldEvaluatorState.NOT_EVALUATED,
        declaration_status="FROZEN_DECLARATION",
        runtime_capability_status="REFERENCE_ONLY_NOT_IMPLEMENTATION_PROOF",
        source_locator_ids=_SOURCE_LAYOUT[0][1],
        issue_ids=(),
    )
    unsigned = StandardStatement(
        statement_id=statement_id,
        statement_revision_id="UNSIGNED",
        statement_schema_version="standard-statement.v1",
        case_id=case_id,
        statement_set_id=statement_set_id,
        track=track,
        semantic_scope="F09",
        domain="decision-audit",
        statement_text=_statement_text(action.selected_action),
        display_section=None,
        decision_result_id=result.result_id,
        action_id=action.action_id,
        basis_record_ids=action.basis_record_ids,
        evidence_refs=evidence_refs,
        relation_ids=(),
        source_locator_ids=tuple(
            ref.source_locator_id
            for ref in evidence_refs
            if ref.source_locator_id is not None
        ),
        card_identity_refs=(card_ref,),
        confidence_snapshot_ref=None,
        output_precision_binding=action.output_precision_binding,
        validation_plan_binding=action.validation_plan_binding,
        feedback_policy="HUMAN_REVIEW_ONLY",
        content_digest=DigestRef(
            "sha256",
            "RFC8785-JCS-UTF8",
            "0" * 64,
        ),
        integrity="VALID" if action.structural_validity == "VALID" else "INVALID",
        issue_ids=action.blocking_issue_ids + action.nonblocking_issue_ids,
    )
    return _sign_statement(unsigned)


def _build_statement_set_projection(
    *,
    case_id: str,
    track: RunTrack,
    package_ref: VersionedObjectRef,
    result_ref: VersionedObjectRef,
    result: DecisionEvaluationResult,
    evidence_refs: tuple[VersionedObjectRef, ...],
    normative_contract_ref: VersionedObjectRef,
    machine_appendix_ref: VersionedObjectRef,
    generated_at: str,
) -> StatementSet:
    provisional_statement = _build_standard_statement(
        case_id=case_id,
        track=track,
        statement_set_id="UNRESOLVED",
        result=result,
        evidence_refs=evidence_refs,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
    )
    statement_set_id, _ = _statement_set_identity(
        case_id,
        result_ref,
        (provisional_statement.statement_revision_id,),
    )
    statement = _build_standard_statement(
        case_id=case_id,
        track=track,
        statement_set_id=statement_set_id,
        result=result,
        evidence_refs=evidence_refs,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
    )
    action = result.action_envelope
    decision_trace_ref = DecisionTraceRef(
        result_ref=result_ref,
        action_id=action.action_id,
        selected_action=action.selected_action,
        basis_record_ids=action.basis_record_ids,
        blocking_issue_ids=action.blocking_issue_ids,
        nonblocking_issue_ids=action.nonblocking_issue_ids,
        source_decision_refs=action.source_decision_refs,
        output_precision_binding=action.output_precision_binding,
        validation_plan_binding=action.validation_plan_binding,
        structural_validity=action.structural_validity,
    )
    unsigned_set = StatementSet(
        statement_set_id=statement_set_id,
        statement_schema_version="standard-statement.v1",
        case_id=case_id,
        track=track,
        source_package_ref=package_ref,
        decision_trace_ref=decision_trace_ref,
        statements=(statement,),
        content_digest=DigestRef("sha256", "RFC8785-JCS-UTF8", "0" * 64),
        generated_at=generated_at,
        publication_state="DRAFT" if action.structural_validity == "VALID" else "BLOCKED",
        issue_ids=action.blocking_issue_ids + action.nonblocking_issue_ids,
    )
    return replace(unsigned_set, content_digest=_statement_set_content_digest(unsigned_set))


def build_trace(
    package: NormalizedEvidencePackage,
    result: DecisionEvaluationResult,
    *,
    normative_contract_ref: VersionedObjectRef,
    machine_appendix_ref: VersionedObjectRef,
    created_at: str,
) -> TraceEnvelope:
    if not isinstance(package, NormalizedEvidencePackage):
        raise F09ContractError("TRACE.PACKAGE_INVALID", "/normalized_package", "trace requires a normalized package")
    if not isinstance(result, DecisionEvaluationResult):
        raise F09ContractError("TRACE.RESULT_INVALID", "/decision_result", "trace requires a decision result")
    if not isinstance(result.action_envelope, DecisionActionEnvelope):
        raise F09ContractError("TRACE.RESULT_INVALID", "/decision_result/action_envelope", "trace requires a decision action envelope")
    if not _contract_ref_shape_valid(result.contract_ref):
        raise F09ContractError("TRACE.RESULT_INVALID", "/decision_result/contract_ref", "trace requires a closed decision contract ref")
    if not _card_source_ref_valid(normative_contract_ref, "CONTRACT"):
        raise F09ContractError("CARD.IDENTITY_INVALID", "/card_identity_refs/0/normative_contract_ref", "card contract source ref must bind immutable content")
    if not _card_source_ref_valid(machine_appendix_ref, "MACHINE_APPENDIX"):
        raise F09ContractError("CARD.IDENTITY_INVALID", "/card_identity_refs/0/machine_appendix_ref", "card appendix source ref must bind immutable content")
    if result.package_id != package.package_id:
        raise F09IntegrityError("TRACE.PACKAGE_MISMATCH", "/decision_result/package_id", "decision result must consume the traced package")
    if validate_for_pi220(package) != "READY":
        raise F09SourceError(
            "SOURCE.IDENTITY_MISMATCH",
            "/source_locators/binding",
            "trace requires a currently consumable canonical PI-210 package",
        )
    if type(created_at) is not str or not created_at:
        raise F09ContractError("TRACE.CREATED_AT_INVALID", "/created_at", "created_at must be a nonempty string")

    package_digest = _canonical_digest(package, field_path="/normalized_package")
    result_digest = _canonical_digest(result, field_path="/decision_result")
    package_ref = _versioned_ref(
        "PACKAGE",
        package.package_id,
        captured_at=created_at,
        digest=package_digest,
        revision_id=f"rev-{package_digest.value[:16]}",
        schema_version="normalized-evidence-package.v1",
        contract_version="pi-210-v1",
    )
    result_ref = _versioned_ref(
        "DECISION",
        result.result_id,
        captured_at=result.produced_at,
        digest=result_digest,
        revision_id=f"rev-{result_digest.value[:16]}",
        schema_version="decision-evaluation-result.v1",
        contract_version=result.contract_ref.contract_version,
    )
    records_by_object = {
        source_id: tuple(
            record
            for expected_locator_id, (expected_path, _) in zip(locator_ids, mappings)
            for record in package.records
            if record.locator.source_id == expected_locator_id
            and record.locator.object_id == source_id
            and record.locator.field_path == expected_path
        )
        for source_id, locator_ids, mappings in _SOURCE_LAYOUT
    }
    if any(
        len(records_by_object[source_id]) != len(mappings)
        or tuple(record.locator.source_id for record in records_by_object[source_id]) != locator_ids
        or tuple(record.locator.field_path for record in records_by_object[source_id]) != tuple(source_path for source_path, _ in mappings)
        for source_id, locator_ids, mappings in _SOURCE_LAYOUT
    ):
        raise F09SourceError("SOURCE.POINTER_UNRESOLVED", "/transformations/LOSSLESS_COPY", "all 13 canonical F09 source fields are required")
    canonical_records = tuple(record for source_id, _, _ in _SOURCE_LAYOUT for record in records_by_object[source_id])
    bindings = tuple(record.locator.binding for record in canonical_records)
    if (
        any(record.track is not EvidenceTrack.REALITY_FACT or record.transformation != "LOSSLESS_COPY" for record in canonical_records)
        or any(not isinstance(binding, ImmutableJsonSourceBinding) for binding in bindings)
        or any(binding != bindings[0] for binding in bindings[1:])
    ):
        raise F09SourceError("SOURCE.IDENTITY_MISMATCH", "/source_locators/binding", "canonical records must share one immutable snapshot binding")
    source_binding = bindings[0]
    if (
        source_binding.source_snapshot_id != "PI-300-F09-SOURCE-SNAPSHOT-V1"
        or source_binding.source_schema_version != "reality-fact-source-snapshot.v1"
        or source_binding.contract_version != "pi-300-f09-source-snapshots-v1"
        or source_binding.captured_at != _PI300_CAPTURED_AT
        or source_binding.content_digest != _PI300_DIGEST
    ):
        raise F09SourceError("SOURCE.IDENTITY_MISMATCH", "/source_locators/binding", "canonical snapshot identity drifted")

    source_refs = tuple(
        _versioned_ref(
            "SOURCE_OBJECT",
            source_id,
            source_locator_id=locator_ids[0],
            captured_at=source_binding.captured_at,
            digest=source_binding.content_digest,
            schema_version=source_binding.source_schema_version,
            contract_version=source_binding.contract_version,
        )
        for source_id, locator_ids, _ in _SOURCE_LAYOUT
    )
    evidence_refs_by_object = {
        source_id: tuple(
            _versioned_ref(
                "EVIDENCE",
                record.evidence_id,
                source_locator_id=record.locator.source_id,
                captured_at=source_binding.captured_at,
                digest=source_binding.content_digest,
                schema_version=source_binding.source_schema_version,
                contract_version=source_binding.contract_version,
            )
            for record in records_by_object[source_id]
        )
        for source_id, _, _ in _SOURCE_LAYOUT
    }
    evidence_refs = tuple(
        ref
        for source_id, _, _ in _SOURCE_LAYOUT
        for ref in evidence_refs_by_object[source_id]
    )
    projected_set = _build_statement_set_projection(
        case_id=package.case_id,
        track=package.track,
        package_ref=package_ref,
        result_ref=result_ref,
        result=result,
        evidence_refs=evidence_refs,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
        generated_at=created_at,
    )
    statement = projected_set.statements[0]
    statement_set_id = projected_set.statement_set_id
    statement_set_digest = projected_set.content_digest
    statement_set_ref = _versioned_ref(
        "STATEMENT_SET",
        statement_set_id,
        captured_at=created_at,
        digest=statement_set_digest,
        revision_id=f"rev-{statement_set_digest.value[:16]}",
        schema_version="standard-statement.v1",
    )
    statement_ref = _versioned_ref(
        "STATEMENT",
        statement.statement_id,
        captured_at=created_at,
        digest=statement.content_digest,
        revision_id=statement.statement_revision_id,
        schema_version=statement.statement_schema_version,
    )
    transformations = tuple(
        TransformationRecord(
            transformation_id=f"COPY-{source_id}",
            adapter_id="f09-pi210-lossless-copy",
            adapter_version="v1",
            source_object_refs=(ObjectRef("SOURCE_OBJECT", source_id, False, locator_ids[0]),),
            target_object_refs=tuple(ObjectRef("EVIDENCE", ref.object_id, False, ref.source_locator_id) for ref in evidence_refs_by_object[source_id]),
            fidelity="LOSSLESS",
            field_mappings=tuple(FieldMapping(source, target, "COPY", "LOSSLESS") for source, target in mappings),
            dropped_fields=(),
            dropped_object_refs=(),
            synthesized_fields=(),
            issues=(),
            transformed_at=source_binding.captured_at,
        )
        for source_id, locator_ids, mappings in _SOURCE_LAYOUT
    )
    nodes = (
        tuple(TraceNode(ref, "SOURCE", package.track, "VALID") for ref in source_refs)
        + tuple(TraceNode(ref, "NORMALIZED_EVIDENCE", package.track, "VALID") for ref in evidence_refs)
        + (
            TraceNode(package_ref, "NORMALIZED_EVIDENCE", package.track, "VALID"),
            TraceNode(result_ref, "DECISION_OUTPUT", package.track, "VALID"),
            TraceNode(statement_set_ref, "STANDARD_STATEMENT", package.track, "VALID"),
            TraceNode(statement_ref, "STANDARD_STATEMENT", package.track, "VALID"),
        )
    )
    edges = (
        tuple(
            TraceEdge(
                f"EDGE-{item.transformation_id}-{target.object_id}",
                "NORMALIZED_FROM",
                source_refs[index],
                evidence_refs_by_object[_SOURCE_LAYOUT[index][0]][target_index],
                item.transformation_id,
                "LOSSLESS",
                "NONE",
                (),
            )
            for index, item in enumerate(transformations)
            for target_index, target in enumerate(item.target_object_refs)
        )
        + tuple(
            TraceEdge(f"EDGE-{ref.object_id}-PACKAGE", "DERIVED_FROM", ref, package_ref, None, "LOSSLESS", "NONE", ())
            for ref in evidence_refs
        )
        + (
            TraceEdge("EDGE-PACKAGE-DECISION", "EVALUATED_BY", package_ref, result_ref, None, "LOSSLESS", "NONE", ()),
            TraceEdge("EDGE-DECISION-STATEMENT-SET", "RENDERED_AS", result_ref, statement_set_ref, None, "LOSSLESS", "NONE", ()),
            TraceEdge("EDGE-STATEMENT-SET-STATEMENT", "RENDERED_AS", statement_set_ref, statement_ref, None, "LOSSLESS", "NONE", ()),
        )
    )
    snapshot = SnapshotRef(
        source_snapshot_id=source_binding.source_snapshot_id,
        source_type="INPUT",
        source_locator_ids=tuple(record.locator.source_id for record in canonical_records),
        schema_version=source_binding.source_schema_version,
        contract_version=source_binding.contract_version,
        content_digest=source_binding.content_digest,
        captured_at=source_binding.captured_at,
        immutability="IMMUTABLE",
    )
    return TraceEnvelope(
        trace_id=f"TRACE-{result.result_id}",
        trace_schema_version="trace-envelope.v1",
        case_id=package.case_id,
        track=package.track,
        source_snapshot_refs=(snapshot,),
        normalized_package_ref=package_ref,
        decision_result_ref=result_ref,
        statement_set_ref=statement_set_ref,
        nodes=nodes,
        edges=edges,
        transformations=transformations,
        artifacts=(),
        feedback_bindings=(),
        integrity="VALID" if package.integrity_state == "READY" else "UNRESOLVED",
        blocking_issue_ids=result.action_envelope.blocking_issue_ids,
        created_at=created_at,
    )


def build_statement_set(
    trace: TraceEnvelope,
    result: DecisionEvaluationResult,
    *,
    normative_contract_ref: VersionedObjectRef,
    machine_appendix_ref: VersionedObjectRef,
    generated_at: str,
) -> StatementSet:
    if not isinstance(trace, TraceEnvelope):
        raise F09ContractError("STATEMENT.TRACE_INVALID", "/trace", "statement set requires a trace")
    if not isinstance(result, DecisionEvaluationResult):
        raise F09ContractError("STATEMENT.RESULT_INVALID", "/decision_result", "statement set requires a decision result")
    if not _versioned_ref_shape_valid(trace.decision_result_ref):
        raise F09ContractError("STATEMENT.TRACE_INVALID", "/trace/decision_result_ref", "trace decision result ref has invalid shape")
    if not _versioned_ref_shape_valid(trace.normalized_package_ref):
        raise F09ContractError("STATEMENT.TRACE_INVALID", "/trace/normalized_package_ref", "trace package ref has invalid shape")
    if not isinstance(result.action_envelope, DecisionActionEnvelope):
        raise F09ContractError("STATEMENT.RESULT_INVALID", "/decision_result/action_envelope", "statement set requires a decision action envelope")
    if not _card_source_ref_valid(normative_contract_ref, "CONTRACT"):
        raise F09ContractError("CARD.IDENTITY_INVALID", "/card_identity_refs/0/normative_contract_ref", "card contract source ref must bind immutable content")
    if not _card_source_ref_valid(machine_appendix_ref, "MACHINE_APPENDIX"):
        raise F09ContractError("CARD.IDENTITY_INVALID", "/card_identity_refs/0/machine_appendix_ref", "card appendix source ref must bind immutable content")
    if trace.decision_result_ref.object_id != result.result_id:
        raise F09IntegrityError("TRACE.BINDING_MISMATCH", "/decision_result_ref", "trace and result identities differ")
    if type(generated_at) is not str or not generated_at:
        raise F09ContractError("STATEMENT.GENERATED_AT_INVALID", "/generated_at", "generated_at must be a nonempty string")
    if not isinstance(trace.nodes, tuple) or any(
        not isinstance(node, TraceNode) or not _versioned_ref_shape_valid(node.object_ref)
        for node in trace.nodes
    ):
        raise F09SourceError("SOURCE.POINTER_UNRESOLVED", "/trace/nodes", "trace nodes have invalid shape")
    evidence_refs = tuple(
        node.object_ref
        for node in trace.nodes
        if node.object_role == "NORMALIZED_EVIDENCE"
        and node.object_ref.object_type == "EVIDENCE"
    )
    return _build_statement_set_projection(
        case_id=trace.case_id,
        track=trace.track,
        package_ref=trace.normalized_package_ref,
        result_ref=trace.decision_result_ref,
        result=result,
        evidence_refs=evidence_refs,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
        generated_at=generated_at,
    )


def validate_statement_projection(
    statement_set: StatementSet,
    trace: TraceEnvelope,
    result: DecisionEvaluationResult,
    package: NormalizedEvidencePackage | None = None,
    *,
    normative_contract_ref: VersionedObjectRef | None = None,
    machine_appendix_ref: VersionedObjectRef | None = None,
) -> ProjectionValidationResult:
    if not isinstance(statement_set, StatementSet):
        raise F09ContractError(
            issue_code="STATEMENT.SET_INVALID",
            field_path="/statement_set",
            diagnostic="statement projection requires a StatementSet",
        )
    if (
        not statement_set.statement_set_id
        or not statement_set.statement_schema_version
        or not statement_set.case_id
        or not isinstance(statement_set.track, RunTrack)
        or not _versioned_ref_shape_valid(statement_set.source_package_ref)
        or statement_set.decision_trace_ref is None
        or not isinstance(statement_set.statements, tuple)
        or not isinstance(statement_set.content_digest, DigestRef)
        or not statement_set.generated_at
        or statement_set.publication_state not in ("DRAFT", "PUBLISHABLE", "BLOCKED", "SUPERSEDED")
        or not isinstance(statement_set.issue_ids, tuple)
    ):
        return ProjectionValidationResult(False, (DetectedIssue("STATEMENT.SET_INVALID", "/statement_set"),))
    if (
        not isinstance(statement_set.decision_trace_ref, DecisionTraceRef)
        or not _versioned_ref_shape_valid(statement_set.decision_trace_ref.result_ref)
    ):
        raise F09ContractError("STATEMENT.SET_INVALID", "/statement_set", "statement set decision_trace_ref has invalid shape")
    if not statement_set.statements:
        return ProjectionValidationResult(False, (DetectedIssue("STATEMENT.RECORD_INVALID", "/statements/0"),))
    statement = statement_set.statements[0]
    if not isinstance(statement, StandardStatement):
        raise F09ContractError("STATEMENT.RECORD_INVALID", "/statements/0", "first statement has invalid shape")
    if (
        not statement.statement_id
        or not statement.statement_revision_id
        or not statement.statement_schema_version
        or not statement.case_id
        or not statement.statement_set_id
        or not isinstance(statement.track, RunTrack)
        or not statement.semantic_scope
        or not statement.domain
        or not statement.statement_text
        or not statement.decision_result_id
        or not statement.action_id
        or not isinstance(statement.basis_record_ids, tuple)
        or not statement.basis_record_ids
        or not isinstance(statement.evidence_refs, tuple)
        or not isinstance(statement.relation_ids, tuple)
        or not isinstance(statement.source_locator_ids, tuple)
        or not isinstance(statement.card_identity_refs, tuple)
        or not isinstance(statement.output_precision_binding, type(statement_set.decision_trace_ref.output_precision_binding))
        or not isinstance(statement.validation_plan_binding, type(statement_set.decision_trace_ref.validation_plan_binding))
        or statement.feedback_policy not in ("FEEDBACK_ALLOWED", "HUMAN_REVIEW_ONLY", "NOT_FEEDBACK_TARGET")
        or not isinstance(statement.content_digest, DigestRef)
        or statement.integrity not in ("VALID", "INVALID", "UNRESOLVED")
        or not isinstance(statement.issue_ids, tuple)
    ):
        return ProjectionValidationResult(False, (DetectedIssue("STATEMENT.RECORD_INVALID", "/statements/0"),))
    if not isinstance(result, DecisionEvaluationResult):
        raise F09ContractError("TRACE.BINDING_MISMATCH", "/trace/declarations", "projection result has invalid shape")
    if not _contract_ref_shape_valid(result.contract_ref):
        raise F09ContractError("TRACE.BINDING_MISMATCH", "/decision_result/contract_ref", "decision contract ref has invalid shape")
    action_envelope = result.action_envelope
    if not isinstance(action_envelope, DecisionActionEnvelope):
        raise F09ContractError("TRACE.BINDING_MISMATCH", "/trace/declarations", "decision action_envelope has invalid shape")
    if not isinstance(trace, TraceEnvelope):
        raise F09SourceError("SOURCE.LOCATOR_MISMATCH", "/source_locators", "projection trace has invalid shape")
    if not isinstance(trace.transformations, tuple) or not isinstance(trace.nodes, tuple) or not isinstance(trace.edges, tuple) or not isinstance(trace.source_snapshot_refs, tuple):
        raise F09SourceError("SOURCE.POINTER_UNRESOLVED", "/transformations/LOSSLESS_COPY", "trace traversal collections have invalid shape")
    if any(not isinstance(item, TransformationRecord) for item in trace.transformations):
        raise F09IntegrityError("TRANSFORMATION.UNSUPPORTED", "/transformations/0", "trace contains a noncanonical transformation record")
    if (
        not _versioned_ref_shape_valid(trace.normalized_package_ref)
        or not _versioned_ref_shape_valid(trace.decision_result_ref)
        or not _versioned_ref_shape_valid(trace.statement_set_ref)
        or any(not isinstance(node, TraceNode) or not _versioned_ref_shape_valid(node.object_ref) for node in trace.nodes)
        or any(not isinstance(edge, TraceEdge) or not _versioned_ref_shape_valid(edge.from_ref) or not _versioned_ref_shape_valid(edge.to_ref) for edge in trace.edges)
    ):
        raise F09SourceError("TRACE.EDGE_MISSING", "/transformations/mappings", "trace node or edge has invalid shape")
    if any(not isinstance(snapshot, SnapshotRef) or not isinstance(snapshot.source_locator_ids, tuple) or not isinstance(snapshot.content_digest, DigestRef) for snapshot in trace.source_snapshot_refs):
        raise F09SourceError("SOURCE.IDENTITY_MISMATCH", "/source_locators/binding", "trace source snapshot has invalid shape")
    if any(not isinstance(ref, ObjectRef) for item in trace.transformations for ref in item.source_object_refs + item.target_object_refs) or any(not isinstance(mapping, FieldMapping) for item in trace.transformations for mapping in item.field_mappings):
        raise F09IntegrityError("TRANSFORMATION.UNSUPPORTED", "/transformations/0", "trace transformation members have invalid shape")
    if (
        any(not _versioned_ref_shape_valid(ref) for ref in statement.evidence_refs)
        or (
            statement.confidence_snapshot_ref is not None
            and not _versioned_ref_shape_valid(statement.confidence_snapshot_ref)
        )
        or any(
            not isinstance(card_ref, CardIdentityRef)
            or not _versioned_ref_shape_valid(card_ref.normative_contract_ref)
            or not _versioned_ref_shape_valid(card_ref.machine_appendix_ref)
            or not isinstance(card_ref.source_locator_ids, tuple)
            or not isinstance(card_ref.issue_ids, tuple)
            for card_ref in statement.card_identity_refs
        )
    ):
        raise F09ContractError("STATEMENT.RECORD_INVALID", "/statements/0", "statement reference members have invalid shape")

    lossless = tuple(item for item in trace.transformations if item.fidelity == "LOSSLESS")
    node_refs = tuple(node.object_ref for node in trace.nodes)
    node_keys = tuple((ref.object_type, ref.object_id) for ref in node_refs)
    source_locator_ids = tuple(ref.source_locator_id for item in lossless for ref in item.source_object_refs if ref.source_locator_id is not None)
    snapshot_locator_ids = tuple(locator_id for snapshot in trace.source_snapshot_refs for locator_id in snapshot.source_locator_ids)
    lossless_mappings = tuple(mapping for item in lossless for mapping in item.field_mappings)
    mapped_target_paths = tuple(mapping.target_field_path for mapping in lossless_mappings)
    lossless_ids = tuple(item.transformation_id for item in lossless)
    terminal_ids = tuple(edge.transformation_id for edge in trace.edges if edge.transformation_id is not None)
    transformation_source_keys = tuple((ref.object_type, ref.object_id) for item in lossless for ref in item.source_object_refs)
    transformation_target_keys = tuple((ref.object_type, ref.object_id) for item in lossless for ref in item.target_object_refs)
    statement_evidence_keys = tuple((ref.object_type, ref.object_id) for ref in statement.evidence_refs)
    edge_transformation_pairs = tuple(
        (edge.transformation_id, edge.from_ref.object_type, edge.from_ref.object_id, edge.to_ref.object_type, edge.to_ref.object_id)
        for edge in trace.edges
        if edge.transformation_id is not None
    )

    expected_package_ref = statement_set.source_package_ref
    result_digest = _canonical_digest(result, field_path="/decision_result")
    expected_result_ref = _versioned_ref(
        "DECISION",
        result.result_id,
        captured_at=result.produced_at,
        digest=result_digest,
        revision_id=f"rev-{result_digest.value[:16]}",
        schema_version="decision-evaluation-result.v1",
        contract_version=result.contract_ref.contract_version,
    )
    expected_statement_set_ref = _versioned_ref(
        "STATEMENT_SET",
        statement_set.statement_set_id,
        captured_at=trace.created_at,
        digest=statement_set.content_digest,
        revision_id=f"rev-{statement_set.content_digest.value[:16]}",
        schema_version=statement_set.statement_schema_version,
    )
    expected_statement_ref = _versioned_ref(
        "STATEMENT",
        statement.statement_id,
        captured_at=trace.created_at,
        digest=statement.content_digest,
        revision_id=statement.statement_revision_id,
        schema_version=statement.statement_schema_version,
    )
    expected_statement_id = _statement_identity(
        statement.case_id,
        statement.semantic_scope,
        statement.basis_record_ids,
    )
    if (
        not trace.trace_id
        or statement.statement_id != expected_statement_id
        or trace.trace_id != f"TRACE-{result.result_id}"
        or trace.trace_schema_version != "trace-envelope.v1"
        or trace.normalized_package_ref != expected_package_ref
        or trace.decision_result_ref != expected_result_ref
        or trace.statement_set_ref != expected_statement_set_ref
        or statement.statement_set_id != statement_set.statement_set_id
        or statement.decision_result_id != result.result_id
        or statement.decision_result_id != statement_set.decision_trace_ref.result_ref.object_id
        or statement.action_id != action_envelope.action_id
        or statement.action_id != statement_set.decision_trace_ref.action_id
        or statement.case_id != statement_set.case_id
        or statement.case_id != trace.case_id
        or statement.track is not statement_set.track
        or statement.track is not trace.track
        or statement_set.source_package_ref != trace.normalized_package_ref
        or statement_set.source_package_ref.object_id != result.package_id
        or trace.decision_result_ref.object_id != result.result_id
        or statement_set.decision_trace_ref.result_ref != trace.decision_result_ref
    ):
        return ProjectionValidationResult(False, (DetectedIssue("TRACE.BINDING_MISMATCH", "/trace/identity"),))
    if len(node_keys) != len(set(node_keys)):
        return ProjectionValidationResult(False, (DetectedIssue("TRACE.IDENTITY_DUPLICATE", "/trace/nodes"),))
    required_refs = (
        trace.normalized_package_ref,
        trace.decision_result_ref,
        trace.statement_set_ref,
        expected_statement_ref,
    )
    if any(
        (ref.object_type, ref.object_id) in node_keys and ref not in node_refs
        for ref in required_refs
    ):
        return ProjectionValidationResult(False, (DetectedIssue("TRACE.BINDING_MISMATCH", "/trace/identity"),))
    if any(ref not in node_refs for ref in required_refs):
        return ProjectionValidationResult(False, (DetectedIssue("SOURCE.POINTER_UNRESOLVED", "/trace/provenance"),))
    if any(key not in node_keys for key in transformation_source_keys + transformation_target_keys):
        return ProjectionValidationResult(False, (DetectedIssue("SOURCE.POINTER_UNRESOLVED", "/transformations/LOSSLESS_COPY"),))
    expected_edge_pairs = tuple(
        (item.transformation_id, source.object_type, source.object_id, target.object_type, target.object_id)
        for item in lossless
        for source in item.source_object_refs
        for target in item.target_object_refs
    )
    if set(edge_transformation_pairs) != set(expected_edge_pairs):
        return ProjectionValidationResult(False, (DetectedIssue("TRACE.EDGE_MISSING", "/transformations/mappings"),))
    if (
        not statement.evidence_refs
        or any(ref.object_type != "EVIDENCE" or ref.source_locator_id is None for ref in statement.evidence_refs)
        or set(statement_evidence_keys) != set(transformation_target_keys)
        or set(statement.source_locator_ids) != {ref.source_locator_id for ref in statement.evidence_refs}
        or any(key not in node_keys for key in statement_evidence_keys)
    ):
        return ProjectionValidationResult(False, (DetectedIssue("SOURCE.POINTER_UNRESOLVED", "/statements/0/evidence_refs"),))
    if any(
        not isinstance(ref.digest_binding, DigestPresent)
        or not any(ref.source_locator_id in snapshot.source_locator_ids and ref.digest_binding.digest == snapshot.content_digest for snapshot in trace.source_snapshot_refs)
        for ref in statement.evidence_refs
    ):
        return ProjectionValidationResult(False, (DetectedIssue("SOURCE.IDENTITY_MISMATCH", "/statements/0/evidence_refs"),))
    if any(ref not in node_refs for ref in statement.evidence_refs):
        return ProjectionValidationResult(False, (DetectedIssue("TRACE.BINDING_MISMATCH", "/trace/identity"),))
    required_provenance_edges = {
        *(
            ("DERIVED_FROM", ref, trace.normalized_package_ref)
            for ref in statement.evidence_refs
        ),
        ("EVALUATED_BY", trace.normalized_package_ref, trace.decision_result_ref),
        ("RENDERED_AS", trace.decision_result_ref, trace.statement_set_ref),
        ("RENDERED_AS", trace.statement_set_ref, expected_statement_ref),
    }
    actual_provenance_edges = {
        (edge.edge_type, edge.from_ref, edge.to_ref)
        for edge in trace.edges
        if edge.transformation_id is None
    }
    if not required_provenance_edges.issubset(actual_provenance_edges):
        return ProjectionValidationResult(False, (DetectedIssue("TRACE.EDGE_MISSING", "/trace/provenance"),))

    state_target_paths = ("/payload/value/level", "/payload/value/position", "/temporal_scope/as_of/value")
    event_target_paths = ("/payload/value/level", "/payload/value/change", "/temporal_scope/interval/start/value", "/temporal_scope/interval/end/value", "/temporal_scope/interval/start_inclusive", "/temporal_scope/interval/end_inclusive")
    outcome_target_paths = ("/payload/value/axis", "/payload/value/action", "/payload/value/object", "/payload/value/tense")
    state_transformations = tuple(item for item in lossless if tuple(mapping.target_field_path for mapping in item.field_mappings) == state_target_paths)
    event_transformations = tuple(item for item in lossless if tuple(mapping.target_field_path for mapping in item.field_mappings) == event_target_paths)
    state_source_refs = tuple(ref for item in state_transformations for ref in item.source_object_refs)
    event_source_refs = tuple(ref for item in event_transformations for ref in item.source_object_refs)
    t93 = (
        len(state_transformations) != 1
        or len(event_transformations) != 1
        or len(state_source_refs) != 1
        or len(event_source_refs) != 1
        or state_source_refs[0].object_id != "SOURCE-STATE-1"
        or event_source_refs[0].object_id != "SOURCE-EVENT-1"
        or tuple(mapping.source_field_path for mapping in state_transformations[0].field_mappings) != ("/value/level", "/value/position", "/value/as_of")
        or tuple(mapping.source_field_path for mapping in event_transformations[0].field_mappings) != ("/value/level", "/value/change", "/value/interval/start", "/value/interval/end", "/value/interval/start_inclusive", "/value/interval/end_inclusive")
    )
    t95 = any(not item.source_object_refs or any((ref.object_type, ref.object_id) not in node_keys for ref in item.source_object_refs) or any(not mapping.source_field_path.startswith("/") for mapping in item.field_mappings) for item in lossless)
    f09_source_snapshots = tuple(snapshot for snapshot in trace.source_snapshot_refs if "SRCLOC-STATE-LEVEL" in snapshot.source_locator_ids or "SRCLOC-EVENT-LEVEL" in snapshot.source_locator_ids)
    t96 = (
        len(f09_source_snapshots) != 1
        or f09_source_snapshots[0].source_snapshot_id != "PI-300-F09-SOURCE-SNAPSHOT-V1"
        or f09_source_snapshots[0].schema_version != "reality-fact-source-snapshot.v1"
        or f09_source_snapshots[0].contract_version != "pi-300-f09-source-snapshots-v1"
        or f09_source_snapshots[0].captured_at != "2026-07-19T00:00:00Z"
        or f09_source_snapshots[0].content_digest.algorithm != "sha256"
        or f09_source_snapshots[0].content_digest.canonicalization != "RFC8785-JCS-UTF8"
        or f09_source_snapshots[0].content_digest.value != "67517fe2d04fb0fe580e031643dab2ad53fcdb8c90707ba4d496c316dd87f5e7"
    ) or any(snapshot.content_digest.algorithm != "sha256" or snapshot.content_digest.canonicalization != "RFC8785-JCS-UTF8" or not snapshot.source_snapshot_id or not snapshot.schema_version or not snapshot.contract_version or not snapshot.captured_at for snapshot in trace.source_snapshot_refs) or any(not isinstance(ref.digest_binding, DigestPresent) or not any(ref.source_locator_id in snapshot.source_locator_ids and ref.digest_binding.digest == snapshot.content_digest for snapshot in trace.source_snapshot_refs) for ref in node_refs if ref.source_locator_id is not None)
    t97 = any(not item.field_mappings for item in lossless) or any(transformation_id not in terminal_ids for transformation_id in lossless_ids)
    t98 = any(path not in mapped_target_paths for path in outcome_target_paths)
    t99 = any(item.fidelity == "LOSSLESS" and any(ref.object_type not in ("SOURCE_OBJECT", "EVIDENCE", "CARD_FIELD") for ref in item.source_object_refs) for item in trace.transformations)
    t100 = any(ref.source_locator_id is None or ref.source_locator_id not in snapshot_locator_ids for item in lossless for ref in item.source_object_refs)
    legal_copy_fields_intact = all(path in mapped_target_paths for path in outcome_target_paths)
    t101 = action_envelope.selected_action is DecisionAction.OUTPUT and legal_copy_fields_intact and any(forbidden in statement.statement_text.lower() for forbidden in ("tool", "amount", "wealth outcome", "工具", "金额", "财富结果"))

    if statement_set.decision_trace_ref.selected_action is not action_envelope.selected_action:
        return ProjectionValidationResult(False, (DetectedIssue("TRACE.BINDING_MISMATCH", "/trace/selected_action"),))

    if action_envelope.selected_action is not DecisionAction.OUTPUT and statement.statement_text == "axis action object tense":
        return ProjectionValidationResult(False, (DetectedIssue("STATEMENT.RECORD_INVALID", "/statements/0"),))
    if statement.output_precision_binding != statement_set.decision_trace_ref.output_precision_binding or statement.validation_plan_binding != statement_set.decision_trace_ref.validation_plan_binding:
        return ProjectionValidationResult(False, (DetectedIssue("TRACE.BINDING_MISMATCH", "/statements/0/output_precision_binding"),))
    if len(statement.evidence_refs) > 1 and any(item.fidelity == "LOSSY" for item in trace.transformations):
        return ProjectionValidationResult(False, (DetectedIssue("PROJECTION.LOSSY", "/transformations/records"),))
    if any(card_ref.runtime_capability_status != "REFERENCE_ONLY_NOT_IMPLEMENTATION_PROOF" for card_ref in statement.card_identity_refs):
        return ProjectionValidationResult(False, (DetectedIssue("CARD.IDENTITY_INVALID", "/card_identity_refs/0/runtime_capability_status"),))
    if statement_set.decision_trace_ref.output_precision_binding != action_envelope.output_precision_binding or statement_set.decision_trace_ref.validation_plan_binding != action_envelope.validation_plan_binding:
        return ProjectionValidationResult(False, (DetectedIssue("TRACE.BINDING_MISMATCH", "/trace/declarations"),))
    if statement_set.decision_trace_ref.basis_record_ids != action_envelope.basis_record_ids or statement.basis_record_ids != statement_set.decision_trace_ref.basis_record_ids:
        return ProjectionValidationResult(False, (DetectedIssue("TRACE.BASIS_MISMATCH", "/statements/0/basis_record_ids"),))
    if t95:
        return ProjectionValidationResult(False, (DetectedIssue("SOURCE.POINTER_UNRESOLVED", "/transformations/LOSSLESS_COPY"),))
    if t100:
        return ProjectionValidationResult(False, (DetectedIssue("SOURCE.BINDING_INVALID", "/source_locators/0"),))
    if t93:
        return ProjectionValidationResult(False, (DetectedIssue("SOURCE.LOCATOR_MISMATCH", "/source_locators"),))
    if t96:
        return ProjectionValidationResult(False, (DetectedIssue("SOURCE.IDENTITY_MISMATCH", "/source_locators/binding"),))
    if t97:
        return ProjectionValidationResult(False, (DetectedIssue("TRACE.EDGE_MISSING", "/transformations/mappings"),))
    if t98:
        return ProjectionValidationResult(False, (DetectedIssue("SOURCE.FIELD_MISSING", "/outcome"),))
    if t99:
        return ProjectionValidationResult(False, (DetectedIssue("TRANSFORMATION.UNSUPPORTED", "/transformations/0"),))
    if t101:
        return ProjectionValidationResult(False, (DetectedIssue("OUTPUT.SCOPE_EXCEEDED", "/statements/0/statement_text"),))
    if not isinstance(package, NormalizedEvidencePackage):
        return ProjectionValidationResult(False, (DetectedIssue("TRACE.BINDING_MISMATCH", "/trace/package_digest"),))
    package_digest = _canonical_digest(package, field_path="/normalized_package")
    expected_package_ref = _versioned_ref(
        "PACKAGE",
        package.package_id,
        captured_at=trace.created_at,
        digest=package_digest,
        revision_id=f"rev-{package_digest.value[:16]}",
        schema_version="normalized-evidence-package.v1",
        contract_version="pi-210-v1",
    )
    if (
        statement_set.source_package_ref != expected_package_ref
        or trace.normalized_package_ref != expected_package_ref
    ):
        return ProjectionValidationResult(False, (DetectedIssue("TRACE.BINDING_MISMATCH", "/trace/package_digest"),))
    if (
        not _card_source_ref_valid(normative_contract_ref, "CONTRACT")
        or not _card_source_ref_valid(machine_appendix_ref, "MACHINE_APPENDIX")
        or any(
            card_ref.normative_contract_ref != normative_contract_ref
            or card_ref.machine_appendix_ref != machine_appendix_ref
            or card_ref.evaluator_state is not FieldEvaluatorState.NOT_EVALUATED
            for card_ref in statement.card_identity_refs
        )
    ):
        return ProjectionValidationResult(False, (DetectedIssue("CARD.IDENTITY_INVALID", "/card_identity_refs/0"),))
    expected_statement_revision_digest = _statement_revision_digest(statement)
    expected_statement_digest = _statement_content_digest(statement)
    expected_set_id, _ = _statement_set_identity(
        statement_set.case_id,
        statement_set.decision_trace_ref.result_ref,
        tuple(item.statement_revision_id for item in statement_set.statements),
    )
    if (
        statement.content_digest != expected_statement_digest
        or statement.statement_revision_id
        != f"rev-{expected_statement_revision_digest.value[:16]}"
        or statement_set.statement_set_id != expected_set_id
        or statement_set.content_digest != _statement_set_content_digest(statement_set)
    ):
        return ProjectionValidationResult(False, (DetectedIssue("TRACE.BINDING_MISMATCH", "/trace/identity"),))
    return ProjectionValidationResult(True, ())
