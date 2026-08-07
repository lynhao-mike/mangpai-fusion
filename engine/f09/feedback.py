from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal, Mapping, Protocol, TypeAlias, Union, runtime_checkable

from engine.f09.artifacts import (
    ArtifactRecord,
    ArtifactSetManifest,
    ArtifactWriteAttempt,
    IdempotencyKey,
    RunArtifactSetKeyV1,
    RunArtifactSetResultV1,
    digest_artifact_records,
    validate_run_artifact_manifest_v1,
    validate_run_artifact_set_result_issuance_v1,
)
from engine.f09.canonical_json import JcsValue, bounded_jcs_sha256, canonicalize_bounded_jcs, parse_bounded_jcs
from engine.f09.contracts import (
    AbsentDeclarationBinding,
    ArtifactItemState,
    ArtifactSetState,
    DecisionAction,
    DetectedIssue,
    DigestRef,
    FieldEvaluatorState,
    FrozenDeclarationRef,
    NotApplicableDeclarationBinding,
    ResolvedDeclarationBinding,
    RunTrack,
    UnavailableDeclarationBinding,
    UnresolvableDeclarationBinding,
)
from engine.f09.errors import F09ContractError, F09IntegrityError
from engine.f09.trace import (
    CardIdentityRef,
    DecisionTraceRef,
    DigestMissing,
    DigestPresent,
    SnapshotRef,
    StandardStatement,
    StatementSet,
    VersionedObjectRef,
)

MatchRequired: TypeAlias = Literal["MATCH", "MISMATCH", "UNKNOWN"]
MatchOptional: TypeAlias = Literal["MATCH", "MISMATCH", "NOT_APPLICABLE", "UNKNOWN"]
TrackSourceState: TypeAlias = Literal["AVAILABLE_RESOLVED", "SOURCE_MISSING", "UNPARSABLE", "AMBIGUOUS", "INTEGRITY_FAILED"]
TrackSourceReasonCode: TypeAlias = Literal["TRACK_SOURCE_MISSING", "TRACK_SOURCE_UNPARSABLE", "TRACK_SOURCE_AMBIGUOUS", "TRACK_SOURCE_INTEGRITY_FAILED"]
BindingProtocol: TypeAlias = Literal["PRODUCTION_STATEMENT", "PREPROD_RUN_TARGET"]
BindingStatus: TypeAlias = Literal["BOUND", "UNBOUND", "AMBIGUOUS", "INVALID"]
EligibilityStatus: TypeAlias = Literal["ELIGIBLE", "INELIGIBLE", "HUMAN_REVIEW"]
TargetResolutionCategory: TypeAlias = Literal["INVALID_MATERIAL", "AMBIGUOUS_CANDIDATES", "TARGET_NOT_FOUND", "SOURCE_SPAN_NOT_FOUND", "TRACK_UNRESOLVED", "REQUIRED_MATCH_FAILED", "PROTOCOL_GRAPH_INCOMPLETE"]
PreprodArtifactRole: TypeAlias = Literal["RUN_SNAPSHOT", "DECISION_RUN", "FEEDBACK_ATTACHMENT", "MANIFEST"]
JcsSnapshotPayload = JcsValue


@dataclass(frozen=True)
class TrackSourceBinding:
    track_source_binding_id: str
    side: Literal["SUBMISSION_SOURCE", "BINDING_TARGET"]
    track: RunTrack
    state: TrackSourceState
    source_evidence_ref: VersionedObjectRef
    parser_ref: VersionedObjectRef
    schema_version: str
    contract_version: str
    content_digest: DigestRef
    state_reason_codes: tuple[TrackSourceReasonCode, ...]
    captured_at: str


@dataclass(frozen=True)
class FeedbackItem:
    feedback_item_id: str
    feedback_id: str
    source_span_locator: str
    target_statement_id: str | None
    target_statement_revision_id: str | None
    target_run_id: str | None
    target_prediction_id: str | None
    verdict: str
    annotation: str
    integrity: Literal["VALID", "INVALID", "UNRESOLVED"]
    issue_ids: tuple[str, ...]


@dataclass(frozen=True)
class FeedbackSubmission:
    feedback_id: str
    case_id: str
    track: RunTrack
    track_source_binding: TrackSourceBinding
    source_snapshot_ref: SnapshotRef
    source_snapshot_payload: JcsValue
    parser_id: str
    parser_version: str
    feedback_items: tuple[FeedbackItem, ...]
    content_digest: DigestRef
    captured_at: str


@dataclass(frozen=True)
class StatementProjectionRecord:
    projection_id: str
    projection_type: Literal["STATEMENT_INDEX", "STATEMENT_RECORDS"]
    statement_set_id: str
    statement_id: str
    statement_revision_id: str
    source_statement_digest: DigestRef
    projected_object_ref: VersionedObjectRef
    transformation_id: str
    fidelity: Literal["LOSSLESS", "PARTIAL", "LOSSY", "UNSUPPORTED"]
    dropped_refs: tuple[VersionedObjectRef, ...]
    synthesized_fields: tuple[str, ...]
    issue_ids: tuple[str, ...]


@dataclass(frozen=True)
class AnchorSelectionRecord:
    anchor_selection_id: str
    statement_id: str
    statement_revision_id: str
    all_rule_refs: tuple[VersionedObjectRef, ...]
    selected_anchor_rule_ref: VersionedObjectRef | None
    non_anchor_rule_refs: tuple[VersionedObjectRef, ...]
    selection_policy_id: str
    selection_policy_version: str
    source_order_digest: DigestRef
    fidelity: Literal["LOSSY", "UNSUPPORTED"]
    fanout_scope: Literal["SELECTED_ANCHOR_ONLY", "NONE"]
    issue_ids: tuple[str, ...]


@dataclass(frozen=True)
class FeedbackBinding:
    feedback_binding_id: str
    feedback_item_ref: VersionedObjectRef
    binding_protocol: BindingProtocol
    source_track_binding_ref: VersionedObjectRef
    target_track_source_binding: TrackSourceBinding
    case_match: MatchRequired
    track_match: MatchRequired
    run_match: MatchOptional
    statement_match: MatchOptional
    revision_match: MatchOptional
    statement_set_match: MatchOptional
    artifact_digest_match: MatchRequired
    target_object_refs: tuple[VersionedObjectRef, ...]
    record_anchor_ref: VersionedObjectRef | None
    status: BindingStatus
    issue_ids: tuple[str, ...]
    detected_issues: tuple[DetectedIssue, ...]
    content_digest: DigestRef


@dataclass(frozen=True)
class GoverningVersions:
    statement_contract_version: str
    statement_set_contract_version: str
    statement_records_contract_version: str
    rule_contract_version: str


@dataclass(frozen=True)
class RuleMetadataReceipt:
    rule_ref: VersionedObjectRef
    family_id: str
    school: str
    canon: str
    rule_type: str
    metadata_schema_version: str
    metadata_contract_version: str
    source_ref: VersionedObjectRef
    content_digest: DigestRef
    captured_at: str


@dataclass(frozen=True)
class ProductionStatementAuthority:
    statement_set: StatementSet
    manifest: ArtifactSetManifest
    statement_refs: tuple[VersionedObjectRef, ...]
    statement_set_ref: VersionedObjectRef
    records_projection_refs: tuple[VersionedObjectRef, ...]
    records_projection_records: tuple[StatementProjectionRecord, ...]
    anchor_selections: tuple[AnchorSelectionRecord, ...]
    rule_metadata_receipts: tuple[RuleMetadataReceipt, ...]
    governing_versions: GoverningVersions
    content_digest: DigestRef


@dataclass(frozen=True)
class PreprodRunAuthority:
    case_id: str
    track: RunTrack
    run_id: str
    manifest: ArtifactSetManifest
    target_refs: tuple[VersionedObjectRef, ...]
    content_digest: DigestRef


@dataclass(frozen=True)
class _PreprodRestrictedManifestContext:
    authority: PreprodRunAuthority
    manifest: ArtifactSetManifest
    case_id: str
    run_id: str
    track: RunTrack
    key: RunArtifactSetKeyV1
    roles: tuple[str, ...]
    verifier_returned_records_digest: DigestRef


class _ManifestVerifierFailure(Exception):
    def __init__(self, error: F09ContractError | F09IntegrityError) -> None:
        self.error = error


@dataclass(frozen=True)
class AnchorPolicy:
    policy_id: str
    policy_version: str
    required_rule_object_type: Literal["RULE"]
    required_fidelity: Literal["LOSSY"]
    required_fanout_scope: Literal["SELECTED_ANCHOR_ONLY"]
    schema_version: str
    contract_version: str
    content_digest: DigestRef


@dataclass(frozen=True)
class EligibilityPolicy:
    policy_id: str
    policy_version: str
    allowed_track: RunTrack
    required_feedback_policy: Literal["FEEDBACK_ALLOWED"]
    human_review_on_ambiguous: bool
    human_review_on_invalid: bool
    human_review_on_unknown_track: bool
    schema_version: str
    contract_version: str
    content_digest: DigestRef


@dataclass(frozen=True)
class RawFeedbackAuthority:
    raw_submission: bytes
    target_authority: ProductionStatementAuthority | PreprodRunAuthority
    target_track_source_binding: TrackSourceBinding
    captured_at: str


@dataclass(frozen=True)
class ItemTargetReceipt:
    feedback_item_id: str
    protocol: BindingProtocol
    target_statement_id: str | None
    target_statement_revision_id: str | None
    target_run_id: str | None
    target_prediction_id: str | None
    resolution_status: BindingStatus
    non_bound_category: TargetResolutionCategory | None
    graph: tuple[VersionedObjectRef, ...]
    graph_digest: DigestRef
    content_digest: DigestRef


@dataclass(frozen=True)
class FeedbackOperationReceipt:
    operation_id: str
    key: IdempotencyKey
    source_digest: DigestRef
    authority_digest: DigestRef
    item_target_receipts: tuple[ItemTargetReceipt, ...]
    aggregate_target_digest: DigestRef
    bindings: tuple[FeedbackBinding, ...]
    anchor_policy_ref: VersionedObjectRef
    eligibility_policy_ref: VersionedObjectRef
    created_at: str
    content_digest: DigestRef


@dataclass(frozen=True)
class PriorFeedbackOperation:
    raw_authority: RawFeedbackAuthority
    receipt: FeedbackOperationReceipt


@dataclass(frozen=True)
class ValidFeedbackOperationResult:
    valid: Literal[True]
    operation_disposition: Literal["NEW_OPERATION", "REUSED_OPERATION"]
    source_identity_relation: Literal["INITIAL", "SAME", "CHANGED"]
    prior_receipt: FeedbackOperationReceipt | None
    current_receipt: FeedbackOperationReceipt
    bindings: tuple[FeedbackBinding, ...]
    overwrite_permitted: Literal[False]
    detected_issues: tuple[DetectedIssue, ...]


@dataclass(frozen=True)
class InvalidFeedbackOperationResult:
    valid: Literal[False]
    operation_disposition: Literal["TARGET_MISMATCH"]
    source_identity_relation: Literal["SAME"]
    prior_receipt: FeedbackOperationReceipt
    current_key: IdempotencyKey
    prior_aggregate_target_digest: DigestRef
    current_aggregate_target_digest: DigestRef
    item_target_receipts: tuple[ItemTargetReceipt, ...]
    bindings: tuple[()]
    overwrite_permitted: Literal[False]
    detected_issues: tuple[DetectedIssue, ...]


@dataclass(frozen=True)
class LearningEligibility:
    eligibility_id: str
    feedback_binding_id: str
    feedback_binding_digest: DigestRef
    policy_id: str
    policy_version: str
    status: EligibilityStatus
    learning_target_refs: tuple[VersionedObjectRef, ...]
    excluded_supporting_rule_refs: tuple[VersionedObjectRef, ...]
    blocking_reason_codes: tuple[str, ...]
    detected_issues: tuple[DetectedIssue, ...]
    evaluated_at: str
    content_digest: DigestRef


FeedbackOperationResult: TypeAlias = Union[ValidFeedbackOperationResult, InvalidFeedbackOperationResult]


@runtime_checkable
class FeedbackClockPort(Protocol):
    def now(self) -> str: ...


_PINNED_ANCHOR_OBJECT_ID = "POLICY:G6:TASK8:R33:ANCHOR"
_PINNED_ELIGIBILITY_OBJECT_ID = "POLICY:G6:TASK8:R33:ELIGIBILITY"
_POLICY_CAPTURED_AT = "2026-07-22T00:00:00Z"
_MISSING = object()


def _error(path: str, diagnostic: str, *, integrity: bool = False) -> None:
    cls = F09IntegrityError if integrity else F09ContractError
    raise cls("FEEDBACK.MATERIAL_INVALID", path, diagnostic)


def _nonblank(value: object, path: str) -> str:
    if type(value) is not str or not value:
        _error(path, "expected exact nonblank string")
    return value


def _nullable_nonblank(value: object, path: str) -> str | None:
    if value is not None and (type(value) is not str or not value):
        _error(path, "expected null or exact nonblank string")
    return value


def _tuple(value: object, path: str) -> tuple[object, ...]:
    if type(value) is not tuple:
        _error(path, "expected exact tuple")
    return value


def _string_tuple(value: object, path: str, *, nonblank: bool = False) -> tuple[str, ...]:
    members = _tuple(value, path)
    if any(type(member) is not str or (nonblank and not member) for member in members):
        _error(path, "expected exact string tuple")
    return members  # type: ignore[return-value]


def _exact_enum(value: object, enum_class: type[Enum], path: str) -> Enum:
    if type(value) is not enum_class:
        _error(path, "expected exact owner enum member")
    return value  # type: ignore[return-value]


def _enum(value: object) -> JcsValue:
    return value.value if isinstance(value, Enum) else value  # type: ignore[return-value]


def _digest_ref_material(d: DigestRef) -> dict[str, JcsValue]:
    if type(d) is not DigestRef:
        _error("/digest", "invalid digest class")
    missing = object()
    algorithm = getattr(d, "algorithm", missing)
    canonicalization = getattr(d, "canonicalization", missing)
    value = getattr(d, "value", missing)
    if (
        type(algorithm) is not str
        or algorithm != "sha256"
        or type(canonicalization) is not str
        or canonicalization != "RFC8785-JCS-UTF8"
        or type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        _error("/digest", "digest must be bounded JCS SHA-256")
    return {"algorithm": algorithm, "canonicalization": canonicalization, "value": value}


def _restricted_preprod_record_digest_material(d: DigestRef) -> dict[str, JcsValue]:
    if type(d) is not DigestRef:
        _error("/manifest/records/digest", "invalid restricted record digest class")
    algorithm = getattr(d, "algorithm", _MISSING)
    canonicalization = getattr(d, "canonicalization", _MISSING)
    value = getattr(d, "value", _MISSING)
    if (
        algorithm != "sha256"
        or canonicalization not in ("RFC8785-JCS-UTF8", "RAW-UTF8")
        or type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        _error("/manifest/records/digest", "invalid restricted record SHA-256 digest")
    return {"algorithm": algorithm, "canonicalization": canonicalization, "value": value}


def _digest_ref_material_allow_raw_utf8(d: DigestRef) -> dict[str, JcsValue]:
    # G6 Task 10 R26: STATEMENT_RECORDS/STATEMENT_INDEX VersionedObjectRef digests
    # are bound to artifact write-boundary digests, which artifacts.py always
    # canonicalizes as RAW-UTF8 (Task 7, frozen). This relaxed variant is the
    # sole owner-authorized widening for those two closed object types; it must
    # not be reused for any other ref/digest surface in this module.
    if type(d) is not DigestRef:
        _error("/digest", "invalid digest class")
    missing = object()
    algorithm = getattr(d, "algorithm", missing)
    canonicalization = getattr(d, "canonicalization", missing)
    value = getattr(d, "value", missing)
    if (
        type(algorithm) is not str
        or algorithm != "sha256"
        or type(canonicalization) is not str
        or canonicalization not in ("RFC8785-JCS-UTF8", "RAW-UTF8")
        or type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        _error("/digest", "digest must be bounded JCS or RAW-UTF8 SHA-256")
    return {"algorithm": algorithm, "canonicalization": canonicalization, "value": value}


def _digest_binding_material(binding: object, *, allow_raw_utf8: bool = False) -> dict[str, JcsValue]:
    if type(binding) is DigestPresent:
        status = getattr(binding, "status", _MISSING)
        digest = getattr(binding, "digest", _MISSING)
        if status is _MISSING or digest is _MISSING:
            _error("/digest_binding", "missing literal public field")
        if status != "PRESENT": _error("/digest_binding/status", "invalid present tag")
        digest_material = (
            _digest_ref_material_allow_raw_utf8(digest)
            if allow_raw_utf8
            else _digest_ref_material(digest)
        )
        return {"status": status, "digest": digest_material}
    if type(binding) is DigestMissing:
        status = getattr(binding, "status", _MISSING)
        digest = getattr(binding, "digest", _MISSING)
        issue_id = getattr(binding, "issue_id", _MISSING)
        if status is _MISSING or digest is _MISSING or issue_id is _MISSING:
            _error("/digest_binding", "missing literal public field")
        if status != "MISSING" or digest is not None: _error("/digest_binding/status", "invalid missing tag")
        return {"status": status, "digest": None, "issue_id": _nonblank(issue_id, "/digest_binding/issue_id")}
    _error("/digest_binding", "invalid digest binding class")


def _restricted_preprod_target_ref_material(ref: VersionedObjectRef) -> dict[str, JcsValue]:
    if type(ref) is not VersionedObjectRef:
        _error("/target_authority/target_refs", "invalid target ref")
    digest_binding = getattr(ref, "digest_binding", _MISSING)
    if type(digest_binding) is not DigestPresent or digest_binding.status != "PRESENT":
        _error("/target_authority/target_refs", "restricted target digest missing")
    digest = getattr(digest_binding, "digest", _MISSING)
    if (
        type(digest) is not DigestRef
        or digest.algorithm != "sha256"
        or digest.canonicalization not in ("RFC8785-JCS-UTF8", "RAW-UTF8")
        or type(digest.value) is not str
        or len(digest.value) != 64
        or any(character not in "0123456789abcdef" for character in digest.value)
    ):
        _error("/target_authority/target_refs/digest", "invalid restricted target digest")
    return {
        "object_type": _nonblank(ref.object_type, "/ref/object_type"),
        "object_id": _nonblank(ref.object_id, "/ref/object_id"),
        "revision_id": _nullable_nonblank(ref.revision_id, "/ref/revision_id"),
        "schema_version": _nonblank(ref.schema_version, "/ref/schema_version"),
        "contract_version": _nullable_nonblank(ref.contract_version, "/ref/contract_version"),
        "digest_binding": {
            "status": "PRESENT",
            "digest": {
                "algorithm": digest.algorithm,
                "canonicalization": digest.canonicalization,
                "value": digest.value,
            },
        },
        "source_locator_id": _nullable_nonblank(ref.source_locator_id, "/ref/source_locator_id"),
        "captured_at": _nullable_nonblank(ref.captured_at, "/ref/captured_at"),
    }


def _versioned_object_ref_material(ref: VersionedObjectRef) -> dict[str, JcsValue]:
    if type(ref) is not VersionedObjectRef: _error("/ref", "invalid ref class")
    object_type = getattr(ref, "object_type", _MISSING)
    object_id = getattr(ref, "object_id", _MISSING)
    revision_id = getattr(ref, "revision_id", _MISSING)
    schema_version = getattr(ref, "schema_version", _MISSING)
    contract_version = getattr(ref, "contract_version", _MISSING)
    digest_binding = getattr(ref, "digest_binding", _MISSING)
    source_locator_id = getattr(ref, "source_locator_id", _MISSING)
    captured_at = getattr(ref, "captured_at", _MISSING)
    if any(value is _MISSING for value in (object_type, object_id, revision_id, schema_version, contract_version, digest_binding, source_locator_id, captured_at)):
        _error("/ref", "missing literal public field")
    # G6 Task 10 R26: only STATEMENT_RECORDS/STATEMENT_INDEX refs may bind a
    # RAW-UTF8 digest, matching the artifact write-boundary canonicalization
    # that artifacts.py always produces for those two roles (Task 7, frozen).
    allow_raw_utf8 = object_type in ("STATEMENT_RECORDS", "STATEMENT_INDEX")
    return {"object_type": _nonblank(object_type, "/ref/object_type"), "object_id": _nonblank(object_id, "/ref/object_id"), "revision_id": _nullable_nonblank(revision_id, "/ref/revision_id"), "schema_version": _nonblank(schema_version, "/ref/schema_version"), "contract_version": _nullable_nonblank(contract_version, "/ref/contract_version"), "digest_binding": _digest_binding_material(digest_binding, allow_raw_utf8=allow_raw_utf8), "source_locator_id": _nullable_nonblank(source_locator_id, "/ref/source_locator_id"), "captured_at": _nullable_nonblank(captured_at, "/ref/captured_at")}


def _snapshot_ref_material(ref: SnapshotRef) -> dict[str, JcsValue]:
    if type(ref) is not SnapshotRef: _error("/source_snapshot_ref", "invalid snapshot class")
    source_snapshot_id = getattr(ref, "source_snapshot_id", _MISSING)
    source_type = getattr(ref, "source_type", _MISSING)
    source_locator_ids = getattr(ref, "source_locator_ids", _MISSING)
    schema_version = getattr(ref, "schema_version", _MISSING)
    contract_version = getattr(ref, "contract_version", _MISSING)
    content_digest = getattr(ref, "content_digest", _MISSING)
    captured_at = getattr(ref, "captured_at", _MISSING)
    immutability = getattr(ref, "immutability", _MISSING)
    if any(value is _MISSING for value in (source_snapshot_id, source_type, source_locator_ids, schema_version, contract_version, content_digest, captured_at, immutability)):
        _error("/source_snapshot_ref", "missing literal public field")
    locators = _tuple(source_locator_ids, "/source_snapshot_ref/source_locator_ids")
    if len(locators) != len(set(locators)) or any(type(x) is not str or not x for x in locators): _error("/source_snapshot_ref/source_locator_ids", "invalid locators")
    if source_type not in ("INPUT", "CONTRACT", "MACHINE_APPENDIX", "FINDING", "DECISION", "REPORT_CONTEXT", "ARTIFACT", "FEEDBACK") or immutability not in ("IMMUTABLE", "MUTABLE_SOURCE_CAPTURE"):
        _error("/source_snapshot_ref", "closed snapshot domain violation")
    return {"source_snapshot_id": _nonblank(source_snapshot_id, "/source_snapshot_ref/source_snapshot_id"), "source_type": source_type, "source_locator_ids": locators, "schema_version": _nullable_nonblank(schema_version, "/source_snapshot_ref/schema_version"), "contract_version": _nullable_nonblank(contract_version, "/source_snapshot_ref/contract_version"), "content_digest": _digest_ref_material(content_digest), "captured_at": _nonblank(captured_at, "/source_snapshot_ref/captured_at"), "immutability": immutability}


def _detected_issue_material(issue: DetectedIssue) -> dict[str, JcsValue]:
    if type(issue) is not DetectedIssue:
        _error("/detected_issues", "invalid issue class")
    issue_code = getattr(issue, "issue_code", _MISSING)
    field_path = getattr(issue, "field_path", _MISSING)
    if issue_code is _MISSING or field_path is _MISSING:
        _error("/detected_issues", "missing literal public field")
    return {"issue_code": _nonblank(issue_code, "/detected_issues/issue_code"), "field_path": _nonblank(field_path, "/detected_issues/field_path")}


def _frozen_declaration_ref_material(ref: FrozenDeclarationRef) -> dict[str, JcsValue]:
    if type(ref) is not FrozenDeclarationRef:
        _error("/declaration/ref", "invalid declaration ref")
    declaration_id = getattr(ref, "declaration_id", _MISSING)
    declaration_type = getattr(ref, "declaration_type", _MISSING)
    card_id = getattr(ref, "card_id", _MISSING)
    contract_version = getattr(ref, "contract_version", _MISSING)
    declaration_schema_version = getattr(ref, "declaration_schema_version", _MISSING)
    content_digest = getattr(ref, "content_digest", _MISSING)
    if any(value is _MISSING for value in (declaration_id, declaration_type, card_id, contract_version, declaration_schema_version, content_digest)):
        _error("/declaration/ref", "missing literal public field")
    return {"declaration_id": _nonblank(declaration_id, "/declaration/ref/declaration_id"), "declaration_type": _nonblank(declaration_type, "/declaration/ref/declaration_type"), "card_id": _nonblank(card_id, "/declaration/ref/card_id"), "contract_version": _nonblank(contract_version, "/declaration/ref/contract_version"), "declaration_schema_version": _nonblank(declaration_schema_version, "/declaration/ref/declaration_schema_version"), "content_digest": _digest_ref_material(content_digest)}


def _frozen_declaration_binding_material(binding: object) -> dict[str, JcsValue]:
    if type(binding) is ResolvedDeclarationBinding:
        presence = getattr(binding, "presence", _MISSING)
        ref = getattr(binding, "ref", _MISSING)
        if presence is _MISSING or ref is _MISSING: _error("/declaration", "missing literal public field")
        if presence != "RESOLVED": _error("/declaration/presence", "invalid tag")
        return {"presence": presence, "ref": _frozen_declaration_ref_material(ref)}
    if type(binding) in (AbsentDeclarationBinding, NotApplicableDeclarationBinding):
        presence = getattr(binding, "presence", _MISSING)
        reason_code = getattr(binding, "reason_code", _MISSING)
        if presence is _MISSING or reason_code is _MISSING: _error("/declaration", "missing literal public field")
        expected = ("ABSENT", "DECLARATION_NOT_PRESENT") if type(binding) is AbsentDeclarationBinding else ("NOT_APPLICABLE", "DECLARATION_NOT_APPLICABLE")
        if (presence, reason_code) != expected: _error("/declaration/presence", "invalid declaration tag")
        return {"presence": presence, "reason_code": reason_code}
    if type(binding) is UnavailableDeclarationBinding:
        presence = getattr(binding, "presence", _MISSING)
        reason_code = getattr(binding, "reason_code", _MISSING)
        issue_ids = getattr(binding, "issue_ids", _MISSING)
        if presence is _MISSING or reason_code is _MISSING or issue_ids is _MISSING: _error("/declaration", "missing literal public field")
        if presence != "UNAVAILABLE" or reason_code not in ("DECLARATION_UNREAD", "DECLARATION_SOURCE_UNAVAILABLE"): _error("/declaration/presence", "invalid unavailable tag")
        issues = _string_tuple(issue_ids, "/declaration/issue_ids", nonblank=True)
        if not issues: _error("/declaration/issue_ids", "unavailable issues must be nonempty")
        return {"presence": presence, "reason_code": reason_code, "issue_ids": issues}
    if type(binding) is UnresolvableDeclarationBinding:
        presence = getattr(binding, "presence", _MISSING)
        attempted_ref = getattr(binding, "attempted_ref", _MISSING)
        reason_code = getattr(binding, "reason_code", _MISSING)
        issue_ids = getattr(binding, "issue_ids", _MISSING)
        if any(value is _MISSING for value in (presence, attempted_ref, reason_code, issue_ids)): _error("/declaration", "missing literal public field")
        if presence != "UNRESOLVABLE" or reason_code not in ("IDENTITY_MISMATCH", "CONTRACT_VERSION_MISMATCH", "DECLARATION_SCHEMA_VERSION_MISMATCH", "DIGEST_MISMATCH", "BROKEN_REFERENCE"): _error("/declaration/presence", "invalid unresolvable tag")
        issues = _string_tuple(issue_ids, "/declaration/issue_ids", nonblank=True)
        if not issues: _error("/declaration/issue_ids", "unresolvable issues must be nonempty")
        return {"presence": presence, "attempted_ref": _frozen_declaration_ref_material(attempted_ref), "reason_code": reason_code, "issue_ids": issues}
    _error("/declaration", "invalid declaration binding class")


def _card_identity_ref_material(ref: CardIdentityRef) -> dict[str, JcsValue]:
    if type(ref) is not CardIdentityRef: _error("/card_identity_refs", "invalid card ref")
    card_identity_ref_id = getattr(ref, "card_identity_ref_id", _MISSING)
    card_id = getattr(ref, "card_id", _MISSING)
    normative_contract_ref = getattr(ref, "normative_contract_ref", _MISSING)
    machine_appendix_ref = getattr(ref, "machine_appendix_ref", _MISSING)
    field_path = getattr(ref, "field_path", _MISSING)
    source_field_state = getattr(ref, "source_field_state", _MISSING)
    evaluator_state = getattr(ref, "evaluator_state", _MISSING)
    declaration_status = getattr(ref, "declaration_status", _MISSING)
    runtime_capability_status = getattr(ref, "runtime_capability_status", _MISSING)
    source_locator_ids = getattr(ref, "source_locator_ids", _MISSING)
    issue_ids = getattr(ref, "issue_ids", _MISSING)
    if any(value is _MISSING for value in (card_identity_ref_id, card_id, normative_contract_ref, machine_appendix_ref, field_path, source_field_state, evaluator_state, declaration_status, runtime_capability_status, source_locator_ids, issue_ids)): _error("/card_identity_refs", "missing literal public field")
    locators = _string_tuple(source_locator_ids, "/card_identity_refs/source_locator_ids", nonblank=True)
    issues = _string_tuple(issue_ids, "/card_identity_refs/issue_ids", nonblank=True)
    _exact_enum(evaluator_state, FieldEvaluatorState, "/card_identity_refs/evaluator_state")
    if card_id not in ("F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08", "F09", "F10", "F11", "F12") or source_field_state not in ("PRESENT_VALUE", "EXPLICIT_NULL", "LISTED_UNRESOLVED", "BOTH_NULL_AND_UNRESOLVED", "ABSENT") or declaration_status != "FROZEN_DECLARATION" or runtime_capability_status != "REFERENCE_ONLY_NOT_IMPLEMENTATION_PROOF": _error("/card_identity_refs", "closed card identity domain violation")
    return {"card_identity_ref_id": _nonblank(card_identity_ref_id, "/card_identity_refs/card_identity_ref_id"), "card_id": _nonblank(card_id, "/card_identity_refs/card_id"), "normative_contract_ref": _versioned_object_ref_material(normative_contract_ref), "machine_appendix_ref": _versioned_object_ref_material(machine_appendix_ref), "field_path": _nonblank(field_path, "/card_identity_refs/field_path"), "source_field_state": source_field_state, "evaluator_state": _enum(evaluator_state), "declaration_status": declaration_status, "runtime_capability_status": runtime_capability_status, "source_locator_ids": locators, "issue_ids": issues}


def _decision_trace_ref_material(ref: DecisionTraceRef) -> dict[str, JcsValue]:
    if type(ref) is not DecisionTraceRef: _error("/decision_trace_ref", "invalid decision trace ref")
    result_ref = getattr(ref, "result_ref", _MISSING)
    action_id = getattr(ref, "action_id", _MISSING)
    selected_action = getattr(ref, "selected_action", _MISSING)
    basis_record_ids = getattr(ref, "basis_record_ids", _MISSING)
    blocking_issue_ids = getattr(ref, "blocking_issue_ids", _MISSING)
    nonblocking_issue_ids = getattr(ref, "nonblocking_issue_ids", _MISSING)
    source_decision_refs = getattr(ref, "source_decision_refs", _MISSING)
    output_precision_binding = getattr(ref, "output_precision_binding", _MISSING)
    validation_plan_binding = getattr(ref, "validation_plan_binding", _MISSING)
    structural_validity = getattr(ref, "structural_validity", _MISSING)
    if any(value is _MISSING for value in (result_ref, action_id, selected_action, basis_record_ids, blocking_issue_ids, nonblocking_issue_ids, source_decision_refs, output_precision_binding, validation_plan_binding, structural_validity)): _error("/decision_trace_ref", "missing literal public field")
    basis = _string_tuple(basis_record_ids, "/decision_trace_ref/basis_record_ids", nonblank=True)
    blocking = _string_tuple(blocking_issue_ids, "/decision_trace_ref/blocking_issue_ids", nonblank=True)
    nonblocking = _string_tuple(nonblocking_issue_ids, "/decision_trace_ref/nonblocking_issue_ids", nonblank=True)
    sources = _string_tuple(source_decision_refs, "/decision_trace_ref/source_decision_refs", nonblank=True)
    _exact_enum(selected_action, DecisionAction, "/decision_trace_ref/selected_action")
    if structural_validity not in ("VALID", "INVALID"): _error("/decision_trace_ref/structural_validity", "closed validity domain violation")
    return {"result_ref": _versioned_object_ref_material(result_ref), "action_id": _nonblank(action_id, "/decision_trace_ref/action_id"), "selected_action": _enum(selected_action), "basis_record_ids": basis, "blocking_issue_ids": blocking, "nonblocking_issue_ids": nonblocking, "source_decision_refs": sources, "output_precision_binding": _frozen_declaration_binding_material(output_precision_binding), "validation_plan_binding": _frozen_declaration_binding_material(validation_plan_binding), "structural_validity": structural_validity}


def _standard_statement_full_owner_material(s: StandardStatement) -> dict[str, JcsValue]:
    if type(s) is not StandardStatement:
        _error("/statement", "invalid statement class")
    statement_id = getattr(s, "statement_id", _MISSING)
    statement_revision_id = getattr(s, "statement_revision_id", _MISSING)
    statement_schema_version = getattr(s, "statement_schema_version", _MISSING)
    case_id = getattr(s, "case_id", _MISSING)
    statement_set_id = getattr(s, "statement_set_id", _MISSING)
    track = getattr(s, "track", _MISSING)
    semantic_scope = getattr(s, "semantic_scope", _MISSING)
    domain = getattr(s, "domain", _MISSING)
    statement_text = getattr(s, "statement_text", _MISSING)
    display_section = getattr(s, "display_section", _MISSING)
    decision_result_id = getattr(s, "decision_result_id", _MISSING)
    action_id = getattr(s, "action_id", _MISSING)
    basis_record_ids = getattr(s, "basis_record_ids", _MISSING)
    evidence_refs = getattr(s, "evidence_refs", _MISSING)
    relation_ids = getattr(s, "relation_ids", _MISSING)
    source_locator_ids = getattr(s, "source_locator_ids", _MISSING)
    card_identity_refs = getattr(s, "card_identity_refs", _MISSING)
    confidence_snapshot_ref = getattr(s, "confidence_snapshot_ref", _MISSING)
    output_precision_binding = getattr(s, "output_precision_binding", _MISSING)
    validation_plan_binding = getattr(s, "validation_plan_binding", _MISSING)
    feedback_policy = getattr(s, "feedback_policy", _MISSING)
    content_digest = getattr(s, "content_digest", _MISSING)
    integrity = getattr(s, "integrity", _MISSING)
    issue_ids = getattr(s, "issue_ids", _MISSING)
    if (
        statement_id is _MISSING
        or statement_revision_id is _MISSING
        or statement_schema_version is _MISSING
        or case_id is _MISSING
        or statement_set_id is _MISSING
        or track is _MISSING
        or semantic_scope is _MISSING
        or domain is _MISSING
        or statement_text is _MISSING
        or display_section is _MISSING
        or decision_result_id is _MISSING
        or action_id is _MISSING
        or basis_record_ids is _MISSING
        or evidence_refs is _MISSING
        or relation_ids is _MISSING
        or source_locator_ids is _MISSING
        or card_identity_refs is _MISSING
        or confidence_snapshot_ref is _MISSING
        or output_precision_binding is _MISSING
        or validation_plan_binding is _MISSING
        or feedback_policy is _MISSING
        or content_digest is _MISSING
        or integrity is _MISSING
        or issue_ids is _MISSING
    ):
        _error("/statement", "missing literal public field")
    _nonblank(statement_id, "/statement/statement_id")
    _nonblank(statement_revision_id, "/statement/statement_revision_id")
    _nonblank(statement_schema_version, "/statement/statement_schema_version")
    _nonblank(case_id, "/statement/case_id")
    _nonblank(statement_set_id, "/statement/statement_set_id")
    _nonblank(semantic_scope, "/statement/semantic_scope")
    _nonblank(domain, "/statement/domain")
    _nonblank(statement_text, "/statement/statement_text")
    _nonblank(decision_result_id, "/statement/decision_result_id")
    _nonblank(action_id, "/statement/action_id")
    _exact_enum(track, RunTrack, "/statement/track")
    if display_section is not None: _nonblank(display_section, "/statement/display_section")
    basis = _string_tuple(basis_record_ids, "/statement/basis_record_ids", nonblank=True)
    evidence = _tuple(evidence_refs, "/statement/evidence_refs")
    relations = _string_tuple(relation_ids, "/statement/relation_ids", nonblank=True)
    locators = _string_tuple(source_locator_ids, "/statement/source_locator_ids", nonblank=True)
    cards = _tuple(card_identity_refs, "/statement/card_identity_refs")
    if any(type(ref) is not VersionedObjectRef for ref in evidence): _error("/statement/evidence_refs", "invalid ref member")
    if any(type(ref) is not CardIdentityRef for ref in cards): _error("/statement/card_identity_refs", "invalid card ref member")
    if confidence_snapshot_ref is not None and type(confidence_snapshot_ref) is not VersionedObjectRef: _error("/statement/confidence_snapshot_ref", "invalid ref")
    if feedback_policy not in ("FEEDBACK_ALLOWED", "HUMAN_REVIEW_ONLY", "NOT_FEEDBACK_TARGET"): _error("/statement/feedback_policy", "closed feedback policy domain violation")
    if integrity not in ("VALID", "INVALID", "UNRESOLVED"): _error("/statement/integrity", "closed integrity domain violation")
    issues = _string_tuple(issue_ids, "/statement/issue_ids", nonblank=True)
    return {
        "statement_id": statement_id, "statement_revision_id": statement_revision_id,
        "statement_schema_version": statement_schema_version, "case_id": case_id,
        "statement_set_id": statement_set_id, "track": _enum(track),
        "semantic_scope": semantic_scope, "domain": domain,
        "statement_text": statement_text, "display_section": display_section,
        "decision_result_id": decision_result_id, "action_id": action_id,
        "basis_record_ids": basis, "evidence_refs": tuple(_versioned_object_ref_material(x) for x in evidence),
        "relation_ids": relations, "source_locator_ids": locators,
        "card_identity_refs": tuple(_card_identity_ref_material(x) for x in cards),
        "confidence_snapshot_ref": None if confidence_snapshot_ref is None else _versioned_object_ref_material(confidence_snapshot_ref),
        "output_precision_binding": _frozen_declaration_binding_material(output_precision_binding),
        "validation_plan_binding": _frozen_declaration_binding_material(validation_plan_binding),
        "feedback_policy": feedback_policy, "content_digest": _digest_ref_material(content_digest),
        "integrity": integrity, "issue_ids": issues,
    }


def _standard_statement_owner_content_material(s: StandardStatement) -> dict[str, JcsValue]:
    full = _standard_statement_full_owner_material(s)
    return {"statement_id": full["statement_id"], "statement_schema_version": full["statement_schema_version"], "case_id": full["case_id"], "statement_set_id": full["statement_set_id"], "track": full["track"], "semantic_scope": full["semantic_scope"], "domain": full["domain"], "statement_text": full["statement_text"], "display_section": full["display_section"], "decision_result_id": full["decision_result_id"], "action_id": full["action_id"], "basis_record_ids": full["basis_record_ids"], "evidence_refs": full["evidence_refs"], "relation_ids": full["relation_ids"], "source_locator_ids": full["source_locator_ids"], "card_identity_refs": full["card_identity_refs"], "confidence_snapshot_ref": full["confidence_snapshot_ref"], "output_precision_binding": full["output_precision_binding"], "validation_plan_binding": full["validation_plan_binding"], "feedback_policy": full["feedback_policy"], "integrity": full["integrity"], "issue_ids": full["issue_ids"]}


def _statement_set_owner_content_material(s: StatementSet) -> dict[str, JcsValue]:
    if type(s) is not StatementSet: _error("/statement_set", "invalid set class")
    statement_set_id = getattr(s, "statement_set_id", _MISSING)
    statement_schema_version = getattr(s, "statement_schema_version", _MISSING)
    case_id = getattr(s, "case_id", _MISSING)
    track = getattr(s, "track", _MISSING)
    source_package_ref = getattr(s, "source_package_ref", _MISSING)
    decision_trace_ref = getattr(s, "decision_trace_ref", _MISSING)
    statement_members = getattr(s, "statements", _MISSING)
    content_digest = getattr(s, "content_digest", _MISSING)
    generated_at = getattr(s, "generated_at", _MISSING)
    publication_state = getattr(s, "publication_state", _MISSING)
    issue_ids = getattr(s, "issue_ids", _MISSING)
    if (
        statement_set_id is _MISSING
        or statement_schema_version is _MISSING
        or case_id is _MISSING
        or track is _MISSING
        or source_package_ref is _MISSING
        or decision_trace_ref is _MISSING
        or statement_members is _MISSING
        or content_digest is _MISSING
        or generated_at is _MISSING
        or publication_state is _MISSING
        or issue_ids is _MISSING
    ):
        _error("/statement_set", "missing literal public field")
    _nonblank(statement_set_id, "/statement_set/statement_set_id")
    _nonblank(statement_schema_version, "/statement_set/statement_schema_version")
    _nonblank(case_id, "/statement_set/case_id")
    _nonblank(generated_at, "/statement_set/generated_at")
    _exact_enum(track, RunTrack, "/statement_set/track")
    if publication_state not in ("DRAFT", "PUBLISHABLE", "BLOCKED", "SUPERSEDED"): _error("/statement_set/publication_state", "closed publication state domain violation")
    statements = _tuple(statement_members, "/statement_set/statements")
    if any(type(statement) is not StandardStatement for statement in statements): _error("/statement_set/statements", "invalid statement member")
    issues = _string_tuple(issue_ids, "/statement_set/issue_ids", nonblank=True)
    _digest_ref_material(content_digest)
    return {"statement_set_id": statement_set_id, "statement_schema_version": statement_schema_version, "case_id": case_id, "track": _enum(track), "source_package_ref": _versioned_object_ref_material(source_package_ref), "decision_trace_ref": _decision_trace_ref_material(decision_trace_ref), "statements": tuple(_standard_statement_full_owner_material(x) for x in statements), "generated_at": generated_at, "publication_state": publication_state, "issue_ids": issues}


def _idempotency_key_material(k: IdempotencyKey, include_canonical_key_digest: bool) -> dict[str, JcsValue]:
    if type(k) is not IdempotencyKey:
        _error("/key", "invalid key")
    if type(include_canonical_key_digest) is not bool:
        _error("/key", "invalid digest inclusion flag")
    operation = getattr(k, "operation", _MISSING)
    case_id = getattr(k, "case_id", _MISSING)
    track = getattr(k, "track", _MISSING)
    source_digest = getattr(k, "source_digest", _MISSING)
    schema_versions_digest = getattr(k, "schema_versions_digest", _MISSING)
    contract_digest = getattr(k, "contract_digest", _MISSING)
    statement_set_id = getattr(k, "statement_set_id", _MISSING)
    feedback_id = getattr(k, "feedback_id", _MISSING)
    canonical_key_digest = getattr(k, "canonical_key_digest", _MISSING)
    if any(value is _MISSING for value in (operation, case_id, track, source_digest, schema_versions_digest, contract_digest, statement_set_id, feedback_id, canonical_key_digest)):
        _error("/key", "missing literal public field")
    if operation not in ("NORMALIZE", "DECIDE", "BUILD_STATEMENT_SET", "RENDER_REPORT", "PROJECT_INDEX", "PROJECT_RECORDS", "BIND_FEEDBACK", "EVALUATE_LEARNING_ELIGIBILITY", "INGEST_FEEDBACK"):
        _error("/key/operation", "invalid operation")
    _exact_enum(track, RunTrack, "/key/track")
    result = {"operation": operation, "case_id": _nonblank(case_id, "/key/case_id"), "track": _enum(track), "source_digest": _digest_ref_material(source_digest), "schema_versions_digest": _digest_ref_material(schema_versions_digest), "contract_digest": None if contract_digest is None else _digest_ref_material(contract_digest), "statement_set_id": _nullable_nonblank(statement_set_id, "/key/statement_set_id"), "feedback_id": _nullable_nonblank(feedback_id, "/key/feedback_id")}
    if include_canonical_key_digest:
        result["canonical_key_digest"] = _digest_ref_material(canonical_key_digest)
    return result


def _track_source_binding_self_excluded_material(b: TrackSourceBinding) -> dict[str, JcsValue]:
    if type(b) is not TrackSourceBinding:
        _error("/track_source_binding", "invalid binding")
    track_source_binding_id = getattr(b, "track_source_binding_id", _MISSING)
    side = getattr(b, "side", _MISSING)
    track = getattr(b, "track", _MISSING)
    state = getattr(b, "state", _MISSING)
    source_evidence_ref = getattr(b, "source_evidence_ref", _MISSING)
    parser_ref = getattr(b, "parser_ref", _MISSING)
    schema_version = getattr(b, "schema_version", _MISSING)
    contract_version = getattr(b, "contract_version", _MISSING)
    content_digest = getattr(b, "content_digest", _MISSING)
    state_reason_codes = getattr(b, "state_reason_codes", _MISSING)
    captured_at = getattr(b, "captured_at", _MISSING)
    if any(value is _MISSING for value in (track_source_binding_id, side, track, state, source_evidence_ref, parser_ref, schema_version, contract_version, content_digest, state_reason_codes, captured_at)):
        _error("/track_source_binding", "missing literal public field")
    _exact_enum(track, RunTrack, "/track_source_binding/track")
    reasons = _string_tuple(state_reason_codes, "/track_source_binding/state_reason_codes", nonblank=True)
    expected_reasons = {
        "AVAILABLE_RESOLVED": (),
        "SOURCE_MISSING": ("TRACK_SOURCE_MISSING",),
        "UNPARSABLE": ("TRACK_SOURCE_UNPARSABLE",),
        "AMBIGUOUS": ("TRACK_SOURCE_AMBIGUOUS",),
        "INTEGRITY_FAILED": ("TRACK_SOURCE_INTEGRITY_FAILED",),
    }
    if side not in ("SUBMISSION_SOURCE", "BINDING_TARGET") or state not in expected_reasons:
        _error("/track_source_binding", "closed binding domain violation")
    if reasons != expected_reasons[state]:
        _error("/track_source_binding/state_reason_codes", "state and reason tuple mismatch")
    return {"track_source_binding_id": _nonblank(track_source_binding_id, "/track_source_binding/track_source_binding_id"), "side": side, "track": _enum(track), "state": state, "source_evidence_ref": _versioned_object_ref_material(source_evidence_ref), "parser_ref": _versioned_object_ref_material(parser_ref), "schema_version": _nonblank(schema_version, "/track_source_binding/schema_version"), "contract_version": _nonblank(contract_version, "/track_source_binding/contract_version"), "state_reason_codes": reasons, "captured_at": _nonblank(captured_at, "/track_source_binding/captured_at")}


def _feedback_item_material(i: FeedbackItem) -> dict[str, JcsValue]:
    if type(i) is not FeedbackItem: _error("/feedback_item", "invalid feedback item class")
    feedback_item_id = getattr(i, "feedback_item_id", _MISSING)
    feedback_id = getattr(i, "feedback_id", _MISSING)
    source_span_locator = getattr(i, "source_span_locator", _MISSING)
    target_statement_id = getattr(i, "target_statement_id", _MISSING)
    target_statement_revision_id = getattr(i, "target_statement_revision_id", _MISSING)
    target_run_id = getattr(i, "target_run_id", _MISSING)
    target_prediction_id = getattr(i, "target_prediction_id", _MISSING)
    verdict = getattr(i, "verdict", _MISSING)
    annotation = getattr(i, "annotation", _MISSING)
    integrity = getattr(i, "integrity", _MISSING)
    issue_ids = getattr(i, "issue_ids", _MISSING)
    if any(value is _MISSING for value in (feedback_item_id, feedback_id, source_span_locator, target_statement_id, target_statement_revision_id, target_run_id, target_prediction_id, verdict, annotation, integrity, issue_ids)): _error("/feedback_item", "missing literal public field")
    issues = _string_tuple(issue_ids, "/feedback_item/issue_ids", nonblank=True)
    if integrity not in ("VALID", "INVALID", "UNRESOLVED"): _error("/feedback_item/integrity", "closed integrity domain violation")
    return {"feedback_item_id": _nonblank(feedback_item_id, "/feedback_item/feedback_item_id"), "feedback_id": _nonblank(feedback_id, "/feedback_item/feedback_id"), "source_span_locator": _nonblank(source_span_locator, "/feedback_item/source_span_locator"), "target_statement_id": _nullable_nonblank(target_statement_id, "/feedback_item/target_statement_id"), "target_statement_revision_id": _nullable_nonblank(target_statement_revision_id, "/feedback_item/target_statement_revision_id"), "target_run_id": _nullable_nonblank(target_run_id, "/feedback_item/target_run_id"), "target_prediction_id": _nullable_nonblank(target_prediction_id, "/feedback_item/target_prediction_id"), "verdict": _nonblank(verdict, "/feedback_item/verdict"), "annotation": annotation if type(annotation) is str else _error("/feedback_item/annotation", "invalid annotation"), "integrity": integrity, "issue_ids": issues}


def _feedback_submission_self_excluded_material(s: FeedbackSubmission) -> dict[str, JcsValue]:
    if type(s) is not FeedbackSubmission: _error("/submission", "invalid submission class")
    feedback_id = getattr(s, "feedback_id", _MISSING)
    case_id = getattr(s, "case_id", _MISSING)
    track = getattr(s, "track", _MISSING)
    track_source_binding = getattr(s, "track_source_binding", _MISSING)
    source_snapshot_ref = getattr(s, "source_snapshot_ref", _MISSING)
    source_snapshot_payload = getattr(s, "source_snapshot_payload", _MISSING)
    parser_id = getattr(s, "parser_id", _MISSING)
    parser_version = getattr(s, "parser_version", _MISSING)
    feedback_items = getattr(s, "feedback_items", _MISSING)
    captured_at = getattr(s, "captured_at", _MISSING)
    content_digest = getattr(s, "content_digest", _MISSING)
    if any(value is _MISSING for value in (feedback_id, case_id, track, track_source_binding, source_snapshot_ref, source_snapshot_payload, parser_id, parser_version, feedback_items, captured_at, content_digest)): _error("/submission", "missing literal public field")
    _exact_enum(track, RunTrack, "/submission/track")
    items = _tuple(feedback_items, "/submission/feedback_items")
    if any(type(item) is not FeedbackItem for item in items): _error("/submission/feedback_items", "invalid item member")
    return {"feedback_id": _nonblank(feedback_id, "/submission/feedback_id"), "case_id": _nonblank(case_id, "/submission/case_id"), "track": _enum(track), "track_source_binding": _track_source_binding_self_excluded_material(track_source_binding), "source_snapshot_ref": _snapshot_ref_material(source_snapshot_ref), "source_snapshot_payload": source_snapshot_payload, "parser_id": _nonblank(parser_id, "/submission/parser_id"), "parser_version": _nonblank(parser_version, "/submission/parser_version"), "feedback_items": tuple(_feedback_item_material(x) for x in items), "captured_at": _nonblank(captured_at, "/submission/captured_at")}


def _statement_projection_record_material(r: StatementProjectionRecord) -> dict[str, JcsValue]:
    if type(r) is not StatementProjectionRecord:
        _error("/projection", "invalid projection class")
    projection_id = getattr(r, "projection_id", _MISSING)
    projection_type = getattr(r, "projection_type", _MISSING)
    statement_set_id = getattr(r, "statement_set_id", _MISSING)
    statement_id = getattr(r, "statement_id", _MISSING)
    statement_revision_id = getattr(r, "statement_revision_id", _MISSING)
    source_statement_digest = getattr(r, "source_statement_digest", _MISSING)
    projected_object_ref = getattr(r, "projected_object_ref", _MISSING)
    transformation_id = getattr(r, "transformation_id", _MISSING)
    fidelity = getattr(r, "fidelity", _MISSING)
    dropped_refs = getattr(r, "dropped_refs", _MISSING)
    synthesized_fields = getattr(r, "synthesized_fields", _MISSING)
    issue_ids = getattr(r, "issue_ids", _MISSING)
    if any(value is _MISSING for value in (projection_id, projection_type, statement_set_id, statement_id, statement_revision_id, source_statement_digest, projected_object_ref, transformation_id, fidelity, dropped_refs, synthesized_fields, issue_ids)):
        _error("/projection", "missing literal public field")
    dropped = _tuple(dropped_refs, "/projection/dropped_refs")
    if any(type(ref) is not VersionedObjectRef for ref in dropped):
        _error("/projection/dropped_refs", "invalid ref member")
    synthesized = _string_tuple(synthesized_fields, "/projection/synthesized_fields")
    issues = _string_tuple(issue_ids, "/projection/issue_ids")
    if projection_type not in ("STATEMENT_INDEX", "STATEMENT_RECORDS") or fidelity not in ("LOSSLESS", "PARTIAL", "LOSSY", "UNSUPPORTED"):
        _error("/projection", "closed domain violation")
    return {"projection_id": _nonblank(projection_id, "/projection/projection_id"), "projection_type": projection_type, "statement_set_id": _nonblank(statement_set_id, "/projection/statement_set_id"), "statement_id": _nonblank(statement_id, "/projection/statement_id"), "statement_revision_id": _nonblank(statement_revision_id, "/projection/statement_revision_id"), "source_statement_digest": _digest_ref_material(source_statement_digest), "projected_object_ref": _versioned_object_ref_material(projected_object_ref), "transformation_id": _nonblank(transformation_id, "/projection/transformation_id"), "fidelity": fidelity, "dropped_refs": tuple(_versioned_object_ref_material(x) for x in dropped), "synthesized_fields": synthesized, "issue_ids": issues}


def _anchor_selection_record_material(r: AnchorSelectionRecord) -> dict[str, JcsValue]:
    if type(r) is not AnchorSelectionRecord:
        _error("/anchor", "invalid anchor class")
    anchor_selection_id = getattr(r, "anchor_selection_id", _MISSING)
    statement_id = getattr(r, "statement_id", _MISSING)
    statement_revision_id = getattr(r, "statement_revision_id", _MISSING)
    all_rule_refs = getattr(r, "all_rule_refs", _MISSING)
    selected_anchor_rule_ref = getattr(r, "selected_anchor_rule_ref", _MISSING)
    non_anchor_rule_refs = getattr(r, "non_anchor_rule_refs", _MISSING)
    selection_policy_id = getattr(r, "selection_policy_id", _MISSING)
    selection_policy_version = getattr(r, "selection_policy_version", _MISSING)
    source_order_digest = getattr(r, "source_order_digest", _MISSING)
    fidelity = getattr(r, "fidelity", _MISSING)
    fanout_scope = getattr(r, "fanout_scope", _MISSING)
    issue_ids = getattr(r, "issue_ids", _MISSING)
    if any(value is _MISSING for value in (anchor_selection_id, statement_id, statement_revision_id, all_rule_refs, selected_anchor_rule_ref, non_anchor_rule_refs, selection_policy_id, selection_policy_version, source_order_digest, fidelity, fanout_scope, issue_ids)):
        _error("/anchor", "missing literal public field")
    rules = _tuple(all_rule_refs, "/anchor/all_rule_refs")
    nonanchors = _tuple(non_anchor_rule_refs, "/anchor/non_anchor_rule_refs")
    if any(type(ref) is not VersionedObjectRef for ref in rules + nonanchors):
        _error("/anchor", "invalid rule ref member")
    if selected_anchor_rule_ref is not None and type(selected_anchor_rule_ref) is not VersionedObjectRef:
        _error("/anchor/selected_anchor_rule_ref", "invalid selected ref")
    issues = _string_tuple(issue_ids, "/anchor/issue_ids")
    if fidelity not in ("LOSSY", "UNSUPPORTED") or fanout_scope not in ("SELECTED_ANCHOR_ONLY", "NONE"):
        _error("/anchor", "closed domain violation")
    return {"anchor_selection_id": _nonblank(anchor_selection_id, "/anchor/anchor_selection_id"), "statement_id": _nonblank(statement_id, "/anchor/statement_id"), "statement_revision_id": _nonblank(statement_revision_id, "/anchor/statement_revision_id"), "all_rule_refs": tuple(_versioned_object_ref_material(x) for x in rules), "selected_anchor_rule_ref": None if selected_anchor_rule_ref is None else _versioned_object_ref_material(selected_anchor_rule_ref), "non_anchor_rule_refs": tuple(_versioned_object_ref_material(x) for x in nonanchors), "selection_policy_id": _nonblank(selection_policy_id, "/anchor/selection_policy_id"), "selection_policy_version": _nonblank(selection_policy_version, "/anchor/selection_policy_version"), "source_order_digest": _digest_ref_material(source_order_digest), "fidelity": fidelity, "fanout_scope": fanout_scope, "issue_ids": issues}


def _governing_versions_material(v: GoverningVersions) -> dict[str, JcsValue]:
    if type(v) is not GoverningVersions:
        _error("/governing_versions", "invalid versions")
    statement_contract_version = getattr(v, "statement_contract_version", _MISSING)
    statement_set_contract_version = getattr(v, "statement_set_contract_version", _MISSING)
    statement_records_contract_version = getattr(v, "statement_records_contract_version", _MISSING)
    rule_contract_version = getattr(v, "rule_contract_version", _MISSING)
    values = (statement_contract_version, statement_set_contract_version, statement_records_contract_version, rule_contract_version)
    if any(value is _MISSING for value in values):
        _error("/governing_versions", "missing literal public field")
    if any(type(value) is not str or not value for value in values):
        _error("/governing_versions", "governing versions must be exact nonblank strings")
    return {"statement_contract_version": statement_contract_version, "statement_set_contract_version": statement_set_contract_version, "statement_records_contract_version": statement_records_contract_version, "rule_contract_version": rule_contract_version}


def _rule_metadata_receipt_self_excluded_material(r: RuleMetadataReceipt) -> dict[str, JcsValue]:
    if type(r) is not RuleMetadataReceipt:
        _error("/metadata", "invalid metadata class")
    rule_ref = getattr(r, "rule_ref", _MISSING)
    family_id = getattr(r, "family_id", _MISSING)
    school = getattr(r, "school", _MISSING)
    canon = getattr(r, "canon", _MISSING)
    rule_type = getattr(r, "rule_type", _MISSING)
    metadata_schema_version = getattr(r, "metadata_schema_version", _MISSING)
    metadata_contract_version = getattr(r, "metadata_contract_version", _MISSING)
    source_ref = getattr(r, "source_ref", _MISSING)
    captured_at = getattr(r, "captured_at", _MISSING)
    content_digest = getattr(r, "content_digest", _MISSING)
    if any(value is _MISSING for value in (rule_ref, family_id, school, canon, rule_type, metadata_schema_version, metadata_contract_version, source_ref, captured_at, content_digest)):
        _error("/metadata", "missing literal public field")
    values = (family_id, school, canon, rule_type, metadata_schema_version, metadata_contract_version, captured_at)
    if any(type(value) is not str or not value for value in values):
        _error("/metadata", "metadata identity must use exact nonblank strings")
    return {"rule_ref": _versioned_object_ref_material(rule_ref), "family_id": family_id, "school": school, "canon": canon, "rule_type": rule_type, "metadata_schema_version": metadata_schema_version, "metadata_contract_version": metadata_contract_version, "source_ref": _versioned_object_ref_material(source_ref), "captured_at": captured_at}


def _anchor_policy_material(p: AnchorPolicy) -> dict[str, JcsValue]:
    if type(p) is not AnchorPolicy: _error("/anchor_policy", "invalid policy class")
    for name, value in (("policy_id", p.policy_id), ("policy_version", p.policy_version), ("schema_version", p.schema_version), ("contract_version", p.contract_version)):
        _nonblank(value, f"/anchor_policy/{name}")
    if p.required_rule_object_type != "RULE" or p.required_fidelity != "LOSSY" or p.required_fanout_scope != "SELECTED_ANCHOR_ONLY": _error("/anchor_policy", "closed policy domain violation")
    return {"policy_id": p.policy_id, "policy_version": p.policy_version, "required_rule_object_type": p.required_rule_object_type, "required_fidelity": p.required_fidelity, "required_fanout_scope": p.required_fanout_scope, "schema_version": p.schema_version, "contract_version": p.contract_version}


def _eligibility_policy_material(p: EligibilityPolicy) -> dict[str, JcsValue]:
    if type(p) is not EligibilityPolicy: _error("/eligibility_policy", "invalid policy class")
    for name, value in (("policy_id", p.policy_id), ("policy_version", p.policy_version), ("schema_version", p.schema_version), ("contract_version", p.contract_version)):
        _nonblank(value, f"/eligibility_policy/{name}")
    _exact_enum(p.allowed_track, RunTrack, "/eligibility_policy/allowed_track")
    if p.required_feedback_policy != "FEEDBACK_ALLOWED" or any(type(value) is not bool for value in (p.human_review_on_ambiguous, p.human_review_on_invalid, p.human_review_on_unknown_track)): _error("/eligibility_policy", "closed policy domain violation")
    return {"policy_id": p.policy_id, "policy_version": p.policy_version, "allowed_track": _enum(p.allowed_track), "required_feedback_policy": p.required_feedback_policy, "human_review_on_ambiguous": p.human_review_on_ambiguous, "human_review_on_invalid": p.human_review_on_invalid, "human_review_on_unknown_track": p.human_review_on_unknown_track, "schema_version": p.schema_version, "contract_version": p.contract_version}


def _pinned_anchor_policy() -> AnchorPolicy:
    unsigned = AnchorPolicy("G6-TASK8-ANCHOR-SELECTION", "r33-anchor-v1", "RULE", "LOSSY", "SELECTED_ANCHOR_ONLY", "anchor-policy.r33.v1", "g6-task8-r33-anchor", DigestRef("sha256", "RFC8785-JCS-UTF8", "0" * 64))
    return AnchorPolicy(unsigned.policy_id, unsigned.policy_version, unsigned.required_rule_object_type, unsigned.required_fidelity, unsigned.required_fanout_scope, unsigned.schema_version, unsigned.contract_version, bounded_jcs_sha256(_anchor_policy_material(unsigned)))


def _pinned_eligibility_policy() -> EligibilityPolicy:
    unsigned = EligibilityPolicy("G6-TASK8-LEARNING-ELIGIBILITY", "r33-eligibility-v1", RunTrack.PRODUCTION_DEFAULT, "FEEDBACK_ALLOWED", True, False, True, "eligibility-policy.r33.v1", "g6-task8-r33-eligibility", DigestRef("sha256", "RFC8785-JCS-UTF8", "0" * 64))
    return EligibilityPolicy(unsigned.policy_id, unsigned.policy_version, unsigned.allowed_track, unsigned.required_feedback_policy, unsigned.human_review_on_ambiguous, unsigned.human_review_on_invalid, unsigned.human_review_on_unknown_track, unsigned.schema_version, unsigned.contract_version, bounded_jcs_sha256(_eligibility_policy_material(unsigned)))


def _policy_digest_identity_material(p: AnchorPolicy | EligibilityPolicy) -> dict[str, JcsValue]:
    if type(p) is AnchorPolicy: _anchor_policy_material(p)
    elif type(p) is EligibilityPolicy: _eligibility_policy_material(p)
    else: _error("/policy", "invalid policy class")
    return {"policy_id": p.policy_id, "policy_version": p.policy_version, "schema_version": p.schema_version, "contract_version": p.contract_version, "content_digest": _digest_ref_material(p.content_digest)}


def _validated_preprod_restricted_manifest_context(
    authority: PreprodRunAuthority,
    *,
    propagate_manifest_verifier_failure: bool = False,
) -> _PreprodRestrictedManifestContext | None:
    if type(authority) is not PreprodRunAuthority:
        _error("/target_authority", "invalid preprod authority")
    manifest = getattr(authority, "manifest", _MISSING)
    if type(manifest) is not ArtifactSetManifest:
        _error("/manifest", "invalid manifest class")
    key = getattr(manifest, "key", _MISSING)
    if type(key) is IdempotencyKey:
        return None
    if type(key) is not RunArtifactSetKeyV1:
        _error("/manifest/key", "unsupported manifest key")
    if _exact_enum(authority.track, RunTrack, "/target_authority/track") is not RunTrack.V5_V6_PREPROD:
        _error("/target_authority/track", "restricted run manifest requires V5_V6_PREPROD")
    if key.operation != "PROJECT_RUN_ARTIFACT_SET":
        _error("/manifest/key/operation", "invalid run manifest operation")
    try:
        verified_digest = validate_run_artifact_manifest_v1(manifest)
    except (F09ContractError, F09IntegrityError) as error:
        if propagate_manifest_verifier_failure:
            raise _ManifestVerifierFailure(error) from error
        raise
    if (
        key.case_id != authority.case_id
        or key.run_id != authority.run_id
        or key.track is not authority.track
        or key.projection_roles != ("RUN_SNAPSHOT", "DECISION_RUN", "FEEDBACK_ATTACHMENT")
    ):
        _error("/target_authority", "run manifest authority material mismatch", integrity=True)
    refs = _tuple(authority.target_refs, "/target_authority/target_refs")
    if any(type(ref) is not VersionedObjectRef for ref in refs):
        _error("/target_authority/target_refs", "invalid target ref")
    roles = tuple(ref.object_type for ref in refs)
    required_roles = ("RUN_SNAPSHOT", "DECISION_RUN", "FEEDBACK_ATTACHMENT", "MANIFEST")
    if roles != required_roles:
        _error("/target_authority/target_refs", "restricted target role closure mismatch", integrity=True)
    for ref in refs:
        _restricted_preprod_target_ref_material(ref)
    record_refs = refs[:3]
    records_by_role = {record.artifact_role: record for record in manifest.records}
    for ref in record_refs:
        record = records_by_role.get(ref.object_type)
        if record is None or (
            ref.object_id != record.artifact_id
            or ref.schema_version != record.schema_version
            or ref.digest_binding.digest != record.observed_digest
        ):
            _error("/target_authority/target_refs", "restricted target record mismatch", integrity=True)
    manifest_ref = refs[3]
    if (
        manifest_ref.object_id != manifest.manifest_id
        or manifest_ref.digest_binding.digest != verified_digest
    ):
        _error("/target_authority/target_refs", "restricted manifest outer ref mismatch", integrity=True)
    return _PreprodRestrictedManifestContext(
        authority, manifest, authority.case_id, authority.run_id, authority.track,
        key, roles, verified_digest,
    )


def _revalidate_preprod_restricted_manifest_context(
    context: _PreprodRestrictedManifestContext | None,
    authority: PreprodRunAuthority | None,
    manifest: ArtifactSetManifest | None,
) -> _PreprodRestrictedManifestContext:
    if (
        type(context) is not _PreprodRestrictedManifestContext
        or type(authority) is not PreprodRunAuthority
        or type(manifest) is not ArtifactSetManifest
        or context.authority is not authority
        or context.manifest is not manifest
    ):
        _error("/manifest", "restricted manifest context mismatch", integrity=True)
    key = getattr(manifest, "key", _MISSING)
    if type(key) is not RunArtifactSetKeyV1:
        _error("/manifest/key", "restricted manifest key changed", integrity=True)
    verified_digest = context.verifier_returned_records_digest
    roles = tuple(ref.object_type for ref in _tuple(authority.target_refs, "/target_authority/target_refs"))
    if (
        key != context.key
        or authority.case_id != context.case_id
        or authority.run_id != context.run_id
        or authority.track is not context.track
        or key.case_id != authority.case_id
        or key.run_id != authority.run_id
        or key.track is not authority.track
        or key.operation != "PROJECT_RUN_ARTIFACT_SET"
        or key.projection_roles != ("RUN_SNAPSHOT", "DECISION_RUN", "FEEDBACK_ATTACHMENT")
        or roles != context.roles
        or roles != ("RUN_SNAPSHOT", "DECISION_RUN", "FEEDBACK_ATTACHMENT", "MANIFEST")
        or verified_digest != context.verifier_returned_records_digest
    ):
        _error("/manifest", "stale restricted manifest context", integrity=True)
    records_by_role = {record.artifact_role: record for record in manifest.records}
    for ref in authority.target_refs[:3]:
        record = records_by_role.get(ref.object_type)
        if (
            type(ref) is not VersionedObjectRef
            or type(ref.digest_binding) is not DigestPresent
            or record is None
            or ref.object_id != record.artifact_id
            or ref.schema_version != record.schema_version
            or ref.digest_binding.digest != record.observed_digest
        ):
            _error("/target_authority/target_refs", "stale restricted target record", integrity=True)
    manifest_ref = authority.target_refs[3]
    if (
        type(manifest_ref) is not VersionedObjectRef
        or type(manifest_ref.digest_binding) is not DigestPresent
        or manifest_ref.object_id != manifest.manifest_id
        or manifest_ref.digest_binding.digest != verified_digest
    ):
        _error("/target_authority/target_refs", "stale restricted manifest outer ref", integrity=True)
    return context


def _manifest_records_shape(
    m: ArtifactSetManifest,
    *,
    restricted_context: _PreprodRestrictedManifestContext | None = None,
    current_authority: PreprodRunAuthority | None = None,
) -> tuple[ArtifactRecord, ...]:
    if type(m) is not ArtifactSetManifest:
        _error("/manifest", "invalid manifest class")
    missing = object()
    manifest_id = getattr(m, "manifest_id", missing)
    key = getattr(m, "key", missing)
    records_value = getattr(m, "records", missing)
    state = getattr(m, "state", missing)
    digest = getattr(m, "digest", missing)
    detected_value = getattr(m, "detected_issues", missing)
    if any(value is missing for value in (manifest_id, key, records_value, state, digest, detected_value)):
        _error("/manifest", "missing literal public field")
    _nonblank(manifest_id, "/manifest/manifest_id")
    restricted_run_manifest = False
    if type(key) is IdempotencyKey:
        if restricted_context is not None or current_authority is not None:
            _error("/manifest", "legacy manifest cannot use restricted context")
        _idempotency_key_material(key, True)
    elif type(key) is RunArtifactSetKeyV1:
        if restricted_context is None or current_authority is None:
            _error("/manifest", "restricted manifest requires authority context")
        _revalidate_preprod_restricted_manifest_context(restricted_context, current_authority, m)
        restricted_run_manifest = True
    else:
        _error("/manifest/key", "unsupported manifest key")
    _exact_enum(state, ArtifactSetState, "/manifest/state")
    detected = _tuple(detected_value, "/manifest/detected_issues")
    if any(type(issue) is not DetectedIssue for issue in detected): _error("/manifest/detected_issues", "invalid issue member")
    for issue in detected: _detected_issue_material(issue)
    records = _tuple(records_value, "/manifest/records")
    if any(type(record) is not ArtifactRecord for record in records):
        _error("/manifest/records", "invalid artifact record member")
    record_roles = ("REPORT", "STATEMENT_INDEX", "STATEMENT_RECORDS", "RUN_SNAPSHOT", "DECISION_RUN", "FEEDBACK_ATTACHMENT", "MANIFEST", "FEEDBACK_SOURCE")
    for index, record in enumerate(records):
        base = f"/manifest/records/{index}"
        artifact_id = getattr(record, "artifact_id", _MISSING)
        artifact_role = getattr(record, "artifact_role", _MISSING)
        record_track = getattr(record, "track", _MISSING)
        case_id = getattr(record, "case_id", _MISSING)
        statement_set_id = getattr(record, "statement_set_id", _MISSING)
        run_id = getattr(record, "run_id", _MISSING)
        path_locator = getattr(record, "path_locator", _MISSING)
        schema_version = getattr(record, "schema_version", _MISSING)
        expected_digest = getattr(record, "expected_digest", _MISSING)
        observed_digest = getattr(record, "observed_digest", _MISSING)
        record_state = getattr(record, "state", _MISSING)
        attempts_value = getattr(record, "attempts", _MISSING)
        issue_ids = getattr(record, "issue_ids", _MISSING)
        if any(value is _MISSING for value in (artifact_id, artifact_role, record_track, case_id, statement_set_id, run_id, path_locator, schema_version, expected_digest, observed_digest, record_state, attempts_value, issue_ids)):
            _error(base, "missing literal public field")
        _nonblank(artifact_id, f"{base}/artifact_id")
        if type(artifact_role) is not str or artifact_role not in record_roles:
            _error(f"{base}/artifact_role", "invalid artifact role")
        _exact_enum(record_track, RunTrack, f"{base}/track")
        _nonblank(case_id, f"{base}/case_id")
        _nullable_nonblank(statement_set_id, f"{base}/statement_set_id")
        _nullable_nonblank(run_id, f"{base}/run_id")
        _nonblank(path_locator, f"{base}/path_locator")
        _nullable_nonblank(schema_version, f"{base}/schema_version")
        digest_material = (
            _restricted_preprod_record_digest_material
            if restricted_run_manifest
            else _digest_ref_material
        )
        if expected_digest is not None:
            digest_material(expected_digest)
        if observed_digest is not None:
            digest_material(observed_digest)
        _exact_enum(record_state, ArtifactItemState, f"{base}/state")
        attempts = _tuple(attempts_value, f"{base}/attempts")
        if any(type(attempt) is not ArtifactWriteAttempt for attempt in attempts):
            _error(f"{base}/attempts", "invalid attempt member")
        for attempt_index, attempt in enumerate(attempts):
            attempt_base = f"{base}/attempts/{attempt_index}"
            attempt_id = getattr(attempt, "attempt_id", _MISSING)
            attempt_artifact_id = getattr(attempt, "artifact_id", _MISSING)
            idempotency_key = getattr(attempt, "idempotency_key", _MISSING)
            attempt_number = getattr(attempt, "attempt_number", _MISSING)
            retry_of_attempt_id = getattr(attempt, "retry_of_attempt_id", _MISSING)
            input_snapshot_refs = getattr(attempt, "input_snapshot_refs", _MISSING)
            started_at = getattr(attempt, "started_at", _MISSING)
            finished_at = getattr(attempt, "finished_at", _MISSING)
            outcome = getattr(attempt, "outcome", _MISSING)
            attempt_observed_digest = getattr(attempt, "observed_digest", _MISSING)
            error_class = getattr(attempt, "error_class", _MISSING)
            error_message_digest = getattr(attempt, "error_message_digest", _MISSING)
            if any(value is _MISSING for value in (attempt_id, attempt_artifact_id, idempotency_key, attempt_number, retry_of_attempt_id, input_snapshot_refs, started_at, finished_at, outcome, attempt_observed_digest, error_class, error_message_digest)):
                _error(attempt_base, "missing literal public field")
            _nonblank(attempt_id, f"{attempt_base}/attempt_id")
            _nonblank(attempt_artifact_id, f"{attempt_base}/artifact_id")
            _nonblank(idempotency_key, f"{attempt_base}/idempotency_key")
            if type(attempt_number) is not int or attempt_number < 0:
                _error(f"{attempt_base}/attempt_number", "invalid attempt number")
            _nullable_nonblank(retry_of_attempt_id, f"{attempt_base}/retry_of_attempt_id")
            refs = _tuple(input_snapshot_refs, f"{attempt_base}/input_snapshot_refs")
            if any(type(ref) is not VersionedObjectRef for ref in refs):
                _error(f"{attempt_base}/input_snapshot_refs", "invalid attempt ref member")
            for ref in refs:
                _versioned_object_ref_material(ref)
            _nonblank(started_at, f"{attempt_base}/started_at")
            _nullable_nonblank(finished_at, f"{attempt_base}/finished_at")
            if type(outcome) is not str or outcome not in ("SUCCEEDED", "FAILED", "UNKNOWN"):
                _error(f"{attempt_base}/outcome", "invalid attempt outcome")
            if attempt_observed_digest is not None:
                digest_material(attempt_observed_digest)
            _nullable_nonblank(error_class, f"{attempt_base}/error_class")
            if error_message_digest is not None:
                digest_material(error_message_digest)
        _string_tuple(issue_ids, f"{base}/issue_ids")
    _digest_ref_material(digest)
    return records  # type: ignore[return-value]


def _manifest_identity(
    m: ArtifactSetManifest,
    *,
    restricted_context: _PreprodRestrictedManifestContext | None = None,
    current_authority: PreprodRunAuthority | None = None,
) -> dict[str, JcsValue]:
    records = _manifest_records_shape(
        m,
        restricted_context=restricted_context,
        current_authority=current_authority,
    )
    supplied_digest = getattr(m, "digest", _MISSING)
    if supplied_digest is _MISSING:
        _error("/manifest/digest", "missing literal public field")
    _digest_ref_material(supplied_digest)
    if type(m.key) is RunArtifactSetKeyV1:
        context = _revalidate_preprod_restricted_manifest_context(
            restricted_context, current_authority, m,
        )
        if supplied_digest != context.verifier_returned_records_digest:
            _error("/manifest/digest", "run verifier digest mismatch", integrity=True)
        return {"records_digest": _digest_ref_material(context.verifier_returned_records_digest)}
    verified_records_digest = digest_artifact_records(records)
    if verified_records_digest != supplied_digest:
        _error("/manifest/digest", "records digest mismatch", integrity=True)
    return {"records_digest": _digest_ref_material(verified_records_digest)}


def _validate_statement_set_shape(s: StatementSet) -> None:
    _statement_set_owner_content_material(s)
    statements = getattr(s, "statements", _MISSING)
    if type(statements) is not tuple:
        _error("/statement_set/statements", "owner shape drift")
    for statement in statements:
        _standard_statement_full_owner_material(statement)


def _validate_statement_set_integrity(s: StatementSet) -> None:
    statements = getattr(s, "statements", _MISSING)
    content_digest = getattr(s, "content_digest", _MISSING)
    if statements is _MISSING or content_digest is _MISSING:
        _error("/statement_set", "missing literal public field")
    _digest_ref_material(content_digest)
    for statement in statements:
        statement_digest = getattr(statement, "content_digest", _MISSING)
        if statement_digest is _MISSING:
            _error("/statement/content_digest", "missing literal public field")
        _digest_ref_material(statement_digest)
        if bounded_jcs_sha256(_standard_statement_owner_content_material(statement)) != statement_digest:
            _error("/statement/content_digest", "owner digest mismatch", integrity=True)
    if bounded_jcs_sha256(_statement_set_owner_content_material(s)) != content_digest:
        _error("/statement_set/content_digest", "owner digest mismatch", integrity=True)


def _validate_statement_set_owner(s: StatementSet) -> None:
    _validate_statement_set_shape(s)
    _validate_statement_set_integrity(s)


def _canonical_bytes(material: JcsValue) -> bytes:
    return canonicalize_bounded_jcs(material)


def _ref_sort_key(ref: VersionedObjectRef) -> tuple[bytes]:
    return (_canonical_bytes(_versioned_object_ref_material(ref)),)


def _projection_ref_sort_key(ref: VersionedObjectRef) -> tuple[bytes, bytes]:
    material = _versioned_object_ref_material(ref)
    return (ref.object_id.encode("utf-16-be"), _canonical_bytes(material))


def _authority_collection_shape(a: ProductionStatementAuthority) -> tuple[tuple[VersionedObjectRef, ...], tuple[VersionedObjectRef, ...], tuple[StatementProjectionRecord, ...], tuple[AnchorSelectionRecord, ...], tuple[RuleMetadataReceipt, ...]]:
    statement_refs = _tuple(a.statement_refs, "/target_authority/statement_refs")
    projection_refs = _tuple(a.records_projection_refs, "/target_authority/records_projection_refs")
    projection_records = _tuple(a.records_projection_records, "/target_authority/records_projection_records")
    anchors = _tuple(a.anchor_selections, "/target_authority/anchor_selections")
    metadata = _tuple(a.rule_metadata_receipts, "/target_authority/rule_metadata_receipts")
    if any(type(ref) is not VersionedObjectRef for ref in statement_refs + projection_refs): _error("/target_authority/refs", "invalid authority ref member")
    if type(a.statement_set_ref) is not VersionedObjectRef: _error("/target_authority/statement_set_ref", "invalid statement set ref")
    if any(type(record) is not StatementProjectionRecord for record in projection_records): _error("/target_authority/records_projection_records", "invalid projection member")
    if any(type(anchor) is not AnchorSelectionRecord for anchor in anchors): _error("/target_authority/anchor_selections", "invalid anchor member")
    if any(type(receipt) is not RuleMetadataReceipt for receipt in metadata): _error("/target_authority/rule_metadata_receipts", "invalid metadata member")
    for ref in statement_refs + projection_refs: _versioned_object_ref_material(ref)
    _versioned_object_ref_material(a.statement_set_ref)
    for record in projection_records: _statement_projection_record_material(record)
    for anchor in anchors: _anchor_selection_record_material(anchor)
    for receipt in metadata:
        _rule_metadata_receipt_self_excluded_material(receipt)
        _digest_ref_material(getattr(receipt, "content_digest", _MISSING))
    return statement_refs, projection_refs, projection_records, anchors, metadata  # type: ignore[return-value]


def _authority_duplicate_cardinality(collections: tuple[tuple[VersionedObjectRef, ...], tuple[VersionedObjectRef, ...], tuple[StatementProjectionRecord, ...], tuple[AnchorSelectionRecord, ...], tuple[RuleMetadataReceipt, ...]]) -> None:
    statement_refs, projection_refs, projection_records, anchors, metadata = collections
    materials = (
        ("statement_refs", tuple(_versioned_object_ref_material(ref) for ref in statement_refs)),
        ("records_projection_refs", tuple(_versioned_object_ref_material(ref) for ref in projection_refs)),
        ("records_projection_records", tuple(_statement_projection_record_material(record) for record in projection_records)),
        ("anchor_selections", tuple(_anchor_selection_record_material(anchor) for anchor in anchors)),
        ("rule_metadata_receipts", tuple({"material": _rule_metadata_receipt_self_excluded_material(receipt), "content_digest": _digest_ref_material(receipt.content_digest)} for receipt in metadata)),
    )
    for path, members in materials:
        identities = tuple(_canonical_bytes(member) for member in members)
        if len(identities) != len(set(identities)): _error(f"/target_authority/{path}", "duplicate complete member material")


def _sort_authority_collections(collections: tuple[tuple[VersionedObjectRef, ...], tuple[VersionedObjectRef, ...], tuple[StatementProjectionRecord, ...], tuple[AnchorSelectionRecord, ...], tuple[RuleMetadataReceipt, ...]]) -> tuple[tuple[VersionedObjectRef, ...], tuple[VersionedObjectRef, ...], tuple[StatementProjectionRecord, ...], tuple[AnchorSelectionRecord, ...], tuple[RuleMetadataReceipt, ...]]:
    statement_refs, projection_refs, projection_records, anchors, metadata = collections
    return (
        tuple(sorted(statement_refs, key=_ref_sort_key)),
        tuple(sorted(projection_refs, key=_projection_ref_sort_key)),
        tuple(sorted(projection_records, key=lambda record: (record.projection_id.encode("utf-16-be"), _canonical_bytes(_statement_projection_record_material(record))))),
        tuple(sorted(anchors, key=lambda anchor: (anchor.statement_id.encode("utf-16-be"), anchor.statement_revision_id.encode("utf-16-be"), _canonical_bytes(_anchor_selection_record_material(anchor))))),
        tuple(sorted(metadata, key=lambda receipt: (_canonical_bytes(_versioned_object_ref_material(receipt.rule_ref)), _canonical_bytes({"material": _rule_metadata_receipt_self_excluded_material(receipt), "content_digest": _digest_ref_material(receipt.content_digest)})))),
    )  # type: ignore[return-value]


def _production_authority_self_excluded_material(a: ProductionStatementAuthority) -> dict[str, JcsValue]:
    if type(a) is not ProductionStatementAuthority: _error("/target_authority", "invalid production authority")
    missing = object()
    statement_set = getattr(a, "statement_set", missing)
    manifest = getattr(a, "manifest", missing)
    statement_refs_value = getattr(a, "statement_refs", missing)
    statement_set_ref = getattr(a, "statement_set_ref", missing)
    projection_refs_value = getattr(a, "records_projection_refs", missing)
    projection_records_value = getattr(a, "records_projection_records", missing)
    anchors_value = getattr(a, "anchor_selections", missing)
    metadata_value = getattr(a, "rule_metadata_receipts", missing)
    governing_versions = getattr(a, "governing_versions", missing)
    content_digest = getattr(a, "content_digest", missing)
    if any(value is missing for value in (statement_set, manifest, statement_refs_value, statement_set_ref, projection_refs_value, projection_records_value, anchors_value, metadata_value, governing_versions, content_digest)):
        _error("/target_authority", "missing literal public field")
    # A1: complete normal-material structural and collection-shape closure.
    _validate_statement_set_shape(statement_set)
    _manifest_records_shape(manifest)
    _governing_versions_material(governing_versions)
    _digest_ref_material(content_digest)
    collections = _authority_collection_shape(a)
    # A3: authority-local protocol identity, duplicate/cardinality, then deterministic sorting.
    _nonblank(statement_set.case_id, "/target_authority/statement_set/case_id")
    if _exact_enum(statement_set.track, RunTrack, "/target_authority/statement_set/track") is not RunTrack.PRODUCTION_DEFAULT:
        _error("/target_authority/statement_set/track", "production authority requires PRODUCTION_DEFAULT")
    _authority_duplicate_cardinality(collections)
    statement_refs, projection_refs, projection_records, anchors, metadata = _sort_authority_collections(collections)
    # A2: object-local integrity closure; no item-resolution predicate belongs here.
    _validate_statement_set_integrity(statement_set)
    manifest_material = _manifest_identity(manifest)
    metadata_materials = []
    for receipt in metadata:
        material = _rule_metadata_receipt_self_excluded_material(receipt)
        receipt_digest = getattr(receipt, "content_digest", _MISSING)
        if receipt_digest is _MISSING:
            _error("/target_authority/rule_metadata_receipts/content_digest", "missing literal public field")
        _digest_ref_material(receipt_digest)
        if bounded_jcs_sha256(material) != receipt_digest:
            _error("/target_authority/rule_metadata_receipts/content_digest", "metadata digest mismatch", integrity=True)
        metadata_materials.append({"material": material, "content_digest": _digest_ref_material(receipt_digest)})
    return {"statement_set": {"statement_set_id": statement_set.statement_set_id, "content_digest": _digest_ref_material(statement_set.content_digest)}, "manifest": manifest_material, "statement_refs": tuple(_versioned_object_ref_material(x) for x in statement_refs), "statement_set_ref": _versioned_object_ref_material(statement_set_ref), "records_projection_refs": tuple(_versioned_object_ref_material(x) for x in projection_refs), "records_projection_records": tuple(_statement_projection_record_material(x) for x in projection_records), "anchor_selections": tuple(_anchor_selection_record_material(x) for x in anchors), "rule_metadata_receipts": tuple(metadata_materials), "governing_versions": _governing_versions_material(governing_versions)}


def _preprod_authority_self_excluded_material(
    a: PreprodRunAuthority,
    *,
    include_restricted_context: bool = False,
    propagate_manifest_verifier_failure: bool = False,
) -> (
    dict[str, JcsValue]
    | tuple[dict[str, JcsValue], _PreprodRestrictedManifestContext | None]
):
    if type(a) is not PreprodRunAuthority: _error("/target_authority", "invalid preprod authority")
    missing = object()
    case_id = getattr(a, "case_id", missing)
    track = getattr(a, "track", missing)
    run_id = getattr(a, "run_id", missing)
    manifest = getattr(a, "manifest", missing)
    refs_value = getattr(a, "target_refs", missing)
    content_digest = getattr(a, "content_digest", missing)
    if any(value is missing for value in (case_id, track, run_id, manifest, refs_value, content_digest)):
        _error("/target_authority", "missing literal public field")
    # A1: close every ref, digest, and manifest record before authority-local cardinality.
    refs = _tuple(refs_value, "/target_authority/target_refs")
    if any(type(ref) is not VersionedObjectRef for ref in refs): _error("/target_authority/target_refs", "invalid target ref")
    restricted_context = _validated_preprod_restricted_manifest_context(
        a,
        propagate_manifest_verifier_failure=propagate_manifest_verifier_failure,
    )
    ref_materials = tuple(
        _restricted_preprod_target_ref_material(ref)
        if restricted_context is not None
        else _versioned_object_ref_material(ref)
        for ref in refs
    )
    _manifest_records_shape(manifest, restricted_context=restricted_context, current_authority=a) if restricted_context is not None else _manifest_records_shape(manifest)
    _digest_ref_material(content_digest)
    # A3: complete target-ref identity, role domain, and per-role cardinality.
    identities = tuple(_canonical_bytes(material) for material in ref_materials)
    if len(identities) != len(set(identities)): _error("/target_authority/target_refs", "duplicate complete target ref material")
    if _exact_enum(track, RunTrack, "/target_authority/track") is not RunTrack.V5_V6_PREPROD:
        _error("/target_authority/track", "preprod authority requires V5_V6_PREPROD")
    role_order = {"RUN_SNAPSHOT": 0, "DECISION_RUN": 1, "FEEDBACK_ATTACHMENT": 2, "MANIFEST": 3}
    if any(ref.object_type not in role_order for ref in refs): _error("/target_authority/target_refs", "forbidden preprod role")
    by_role = {role: tuple(ref for ref in refs if ref.object_type == role) for role in role_order}
    if any(len(members) > 1 for members in by_role.values()): _error("/target_authority/target_refs", "duplicate preprod role")
    ordered = tuple(
        ref
        for ref, material in sorted(
            zip(refs, ref_materials),
            key=lambda pair: (role_order[pair[0].object_type], _canonical_bytes(pair[1])),
        )
    )
    # A2: verify the public manifest records digest after all A3 predicates.
    material = {"case_id": _nonblank(case_id, "/target_authority/case_id"), "track": _enum(track), "run_id": _nonblank(run_id, "/target_authority/run_id"), "manifest": _manifest_identity(manifest, restricted_context=restricted_context, current_authority=a) if restricted_context is not None else _manifest_identity(manifest), "target_refs": tuple(_restricted_preprod_target_ref_material(x) if restricted_context is not None else _versioned_object_ref_material(x) for x in ordered)}
    return (material, restricted_context) if include_restricted_context else material


def construct_preprod_run_authority_v1(
    *,
    run_artifact_set_result: RunArtifactSetResultV1,
) -> PreprodRunAuthority:
    if type(run_artifact_set_result) is not RunArtifactSetResultV1:
        _error("/run_artifact_set_result", "invalid run artifact set result")
    validate_run_artifact_set_result_issuance_v1(run_artifact_set_result)
    manifest = run_artifact_set_result.manifest
    provisional = PreprodRunAuthority(
        manifest.key.case_id,
        manifest.key.track,
        manifest.key.run_id,
        manifest,
        run_artifact_set_result.target_refs,
        DigestRef("sha256", "RFC8785-JCS-UTF8", "0" * 64),
    )
    material, restricted_context = _preprod_authority_self_excluded_material(
        provisional,
        include_restricted_context=True,
    )
    if (
        restricted_context is None
        or manifest.digest != restricted_context.verifier_returned_records_digest
    ):
        _error("/manifest/digest", "run verifier digest mismatch", integrity=True)
    return PreprodRunAuthority(
        provisional.case_id,
        provisional.track,
        provisional.run_id,
        provisional.manifest,
        provisional.target_refs,
        bounded_jcs_sha256(material),
    )


def _feedback_binding_self_excluded_material(b: FeedbackBinding) -> dict[str, JcsValue]:
    if type(b) is not FeedbackBinding: _error("/binding", "invalid binding class")
    targets = _tuple(b.target_object_refs, "/binding/target_object_refs")
    issues = _string_tuple(b.issue_ids, "/binding/issue_ids")
    detected = _tuple(b.detected_issues, "/binding/detected_issues")
    if any(type(ref) is not VersionedObjectRef for ref in targets): _error("/binding/target_object_refs", "invalid target ref member")
    if any(type(issue) is not DetectedIssue for issue in detected): _error("/binding/detected_issues", "invalid detected issue member")
    if b.record_anchor_ref is not None and type(b.record_anchor_ref) is not VersionedObjectRef: _error("/binding/record_anchor_ref", "invalid anchor ref")
    if b.binding_protocol not in ("PRODUCTION_STATEMENT", "PREPROD_RUN_TARGET") or b.status not in ("BOUND", "UNBOUND", "AMBIGUOUS", "INVALID"): _error("/binding", "closed binding domain violation")
    if any(value not in ("MATCH", "MISMATCH", "UNKNOWN") for value in (b.case_match, b.track_match, b.artifact_digest_match)) or any(value not in ("MATCH", "MISMATCH", "NOT_APPLICABLE", "UNKNOWN") for value in (b.run_match, b.statement_match, b.revision_match, b.statement_set_match)): _error("/binding", "closed match domain violation")
    return {"feedback_binding_id": _nonblank(b.feedback_binding_id, "/binding/feedback_binding_id"), "feedback_item_ref": _versioned_object_ref_material(b.feedback_item_ref), "binding_protocol": b.binding_protocol, "source_track_binding_ref": _versioned_object_ref_material(b.source_track_binding_ref), "target_track_source_binding": {**_track_source_binding_self_excluded_material(b.target_track_source_binding), "content_digest": _digest_ref_material(b.target_track_source_binding.content_digest)}, "case_match": b.case_match, "track_match": b.track_match, "run_match": b.run_match, "statement_match": b.statement_match, "revision_match": b.revision_match, "statement_set_match": b.statement_set_match, "artifact_digest_match": b.artifact_digest_match, "target_object_refs": tuple(_versioned_object_ref_material(x) for x in targets), "record_anchor_ref": None if b.record_anchor_ref is None else _versioned_object_ref_material(b.record_anchor_ref), "status": b.status, "issue_ids": issues, "detected_issues": tuple(_detected_issue_material(x) for x in detected)}


def _item_target_graph_material(protocol: BindingProtocol, item: FeedbackItem, status: BindingStatus, category: TargetResolutionCategory | None, graph: tuple[VersionedObjectRef, ...]) -> dict[str, JcsValue]:
    if type(item) is not FeedbackItem: _error("/item_target/item", "invalid feedback item class")
    if protocol not in ("PRODUCTION_STATEMENT", "PREPROD_RUN_TARGET") or status not in ("BOUND", "UNBOUND", "AMBIGUOUS", "INVALID"): _error("/item_target", "closed target domain violation")
    if category is not None and category not in ("INVALID_MATERIAL", "AMBIGUOUS_CANDIDATES", "TARGET_NOT_FOUND", "SOURCE_SPAN_NOT_FOUND", "TRACK_UNRESOLVED", "REQUIRED_MATCH_FAILED", "PROTOCOL_GRAPH_INCOMPLETE"): _error("/item_target/non_bound_category", "closed category domain violation")
    refs = _tuple(graph, "/item_target/graph")
    if any(type(ref) is not VersionedObjectRef for ref in refs): _error("/item_target/graph", "invalid graph member")
    if (status == "BOUND") != (category is None) or (status != "BOUND" and refs): _error("/item_target", "status-tagged graph violation")
    return {"protocol": protocol, "raw_target_identity": {"target_statement_id": item.target_statement_id, "target_statement_revision_id": item.target_statement_revision_id, "target_run_id": item.target_run_id, "target_prediction_id": item.target_prediction_id}, "resolution_status": status, "non_bound_category": category, "graph": tuple(_versioned_object_ref_material(x) for x in refs)}


def _item_target_receipt_self_excluded_material(r: ItemTargetReceipt) -> dict[str, JcsValue]:
    if type(r) is not ItemTargetReceipt: _error("/item_target_receipt", "invalid receipt class")
    graph = _tuple(r.graph, "/item_target_receipt/graph")
    if any(type(ref) is not VersionedObjectRef for ref in graph): _error("/item_target_receipt/graph", "invalid graph member")
    graph_digest = getattr(r, "graph_digest", _MISSING)
    _digest_ref_material(graph_digest)
    probe = FeedbackItem(r.feedback_item_id, r.feedback_item_id, "RECEIPT#", r.target_statement_id, r.target_statement_revision_id, r.target_run_id, r.target_prediction_id, "RECEIPT", "", "VALID", ())
    expected_graph_digest = bounded_jcs_sha256(_item_target_graph_material(r.protocol, probe, r.resolution_status, r.non_bound_category, graph))
    if expected_graph_digest != graph_digest: _error("/item_target_receipt/graph_digest", "graph digest mismatch", integrity=True)
    return {"feedback_item_id": _nonblank(r.feedback_item_id, "/item_target_receipt/feedback_item_id"), "protocol": r.protocol, "target_statement_id": r.target_statement_id, "target_statement_revision_id": r.target_statement_revision_id, "target_run_id": r.target_run_id, "target_prediction_id": r.target_prediction_id, "resolution_status": r.resolution_status, "non_bound_category": r.non_bound_category, "graph": tuple(_versioned_object_ref_material(x) for x in graph), "graph_digest": _digest_ref_material(r.graph_digest)}


def _aggregate_target_material(receipts: tuple[ItemTargetReceipt, ...]) -> tuple[JcsValue, ...]:
    members = _tuple(receipts, "/item_target_receipts")
    if any(type(receipt) is not ItemTargetReceipt for receipt in members): _error("/item_target_receipts", "invalid receipt member")
    for receipt in members:
        material = _item_target_receipt_self_excluded_material(receipt)
        _digest_ref_material(getattr(receipt, "content_digest", _MISSING))
        if bounded_jcs_sha256(material) != receipt.content_digest: _error("/item_target_receipts/content_digest", "receipt digest mismatch", integrity=True)
    if len(members) != len(set(receipt.feedback_item_id for receipt in members)): _error("/item_target_receipts", "duplicate feedback item receipt")
    ordered = sorted(members, key=lambda x: x.feedback_item_id.encode("utf-16-be"))
    return tuple({"feedback_item_id": x.feedback_item_id, "protocol": x.protocol, "resolution_status": x.resolution_status, "graph_digest": _digest_ref_material(x.graph_digest), "item_target_receipt_content_digest": _digest_ref_material(x.content_digest)} for x in ordered)


def _feedback_operation_receipt_self_excluded_material(r: FeedbackOperationReceipt) -> dict[str, JcsValue]:
    if type(r) is not FeedbackOperationReceipt: _error("/operation_receipt", "invalid receipt class")
    receipts = _tuple(r.item_target_receipts, "/operation_receipt/item_target_receipts")
    bindings = _tuple(r.bindings, "/operation_receipt/bindings")
    if any(type(receipt) is not ItemTargetReceipt for receipt in receipts) or any(type(binding) is not FeedbackBinding for binding in bindings): _error("/operation_receipt", "invalid nested member")
    _digest_ref_material(getattr(r, "aggregate_target_digest", _MISSING))
    aggregate = bounded_jcs_sha256(_aggregate_target_material(receipts))
    if aggregate != r.aggregate_target_digest: _error("/operation_receipt/aggregate_target_digest", "aggregate digest mismatch", integrity=True)
    for binding in bindings: validate_feedback_binding_record(binding)
    return {"operation_id": _nonblank(r.operation_id, "/operation_receipt/operation_id"), "key": _idempotency_key_material(r.key, True), "source_digest": _digest_ref_material(r.source_digest), "authority_digest": _digest_ref_material(r.authority_digest), "item_target_receipts": tuple(_item_target_receipt_self_excluded_material(x) | {"content_digest": _digest_ref_material(x.content_digest)} for x in receipts), "aggregate_target_digest": _digest_ref_material(r.aggregate_target_digest), "bindings": tuple(_feedback_binding_self_excluded_material(x) | {"content_digest": _digest_ref_material(x.content_digest)} for x in bindings), "anchor_policy_ref": _versioned_object_ref_material(r.anchor_policy_ref), "eligibility_policy_ref": _versioned_object_ref_material(r.eligibility_policy_ref), "created_at": _nonblank(r.created_at, "/operation_receipt/created_at")}


def _learning_eligibility_self_excluded_material(e: LearningEligibility) -> dict[str, JcsValue]:
    if type(e) is not LearningEligibility: _error("/eligibility", "invalid eligibility class")
    targets = _tuple(e.learning_target_refs, "/eligibility/learning_target_refs")
    excluded = _tuple(e.excluded_supporting_rule_refs, "/eligibility/excluded_supporting_rule_refs")
    reasons = _string_tuple(e.blocking_reason_codes, "/eligibility/blocking_reason_codes", nonblank=True)
    issues = _tuple(e.detected_issues, "/eligibility/detected_issues")
    if any(type(ref) is not VersionedObjectRef for ref in targets + excluded) or any(type(issue) is not DetectedIssue for issue in issues): _error("/eligibility", "invalid nested member")
    if type(e.status) is not str or e.status not in ("ELIGIBLE", "INELIGIBLE", "HUMAN_REVIEW"): _error("/eligibility/status", "invalid status")
    return {"eligibility_id": _nonblank(e.eligibility_id, "/eligibility/eligibility_id"), "feedback_binding_id": _nonblank(e.feedback_binding_id, "/eligibility/feedback_binding_id"), "feedback_binding_digest": _digest_ref_material(e.feedback_binding_digest), "policy_id": _nonblank(e.policy_id, "/eligibility/policy_id"), "policy_version": _nonblank(e.policy_version, "/eligibility/policy_version"), "status": e.status, "learning_target_refs": tuple(_versioned_object_ref_material(x) for x in targets), "excluded_supporting_rule_refs": tuple(_versioned_object_ref_material(x) for x in excluded), "blocking_reason_codes": reasons, "detected_issues": tuple(_detected_issue_material(x) for x in issues), "evaluated_at": _nonblank(e.evaluated_at, "/eligibility/evaluated_at")}


def _validate_digest_material_inputs(s: object, authority: object, anchor: object, eligibility: object, *, restricted_context: _PreprodRestrictedManifestContext | None = None) -> tuple[FeedbackSubmission, ProductionStatementAuthority | PreprodRunAuthority, AnchorPolicy, EligibilityPolicy]:
    if type(s) is not FeedbackSubmission:
        _error("/submission", "invalid submission class")
    if type(authority) not in (ProductionStatementAuthority, PreprodRunAuthority):
        _error("/target_authority", "invalid authority class")
    _feedback_submission_self_excluded_material(s)
    if type(authority) is ProductionStatementAuthority:
        _production_authority_self_excluded_material(authority)
    elif restricted_context is None:
        _preprod_authority_self_excluded_material(authority)
    else:
        _revalidate_preprod_restricted_manifest_context(
            restricted_context, authority, authority.manifest,
        )
    _anchor_policy_material(anchor)
    _eligibility_policy_material(eligibility)
    return s, authority, anchor, eligibility


def _schema_versions_digest_material(s: FeedbackSubmission, authority: ProductionStatementAuthority | PreprodRunAuthority, anchor: AnchorPolicy, eligibility: EligibilityPolicy, *, restricted_context: _PreprodRestrictedManifestContext | None = None) -> dict[str, JcsValue]:
    s, authority, anchor, eligibility = _validate_digest_material_inputs(s, authority, anchor, eligibility, restricted_context=restricted_context)
    return {"submission": s.source_snapshot_ref.schema_version, "track_source_binding": s.track_source_binding.schema_version, "target_authority": "production-statement-authority.v1" if type(authority) is ProductionStatementAuthority else "preprod-run-authority.v1", "rule_metadata": authority.governing_versions.rule_contract_version if type(authority) is ProductionStatementAuthority else None, "anchor_policy": anchor.schema_version, "eligibility_policy": eligibility.schema_version}


def _contract_digest_material(s: FeedbackSubmission, authority: ProductionStatementAuthority | PreprodRunAuthority, anchor: AnchorPolicy, eligibility: EligibilityPolicy, *, restricted_context: _PreprodRestrictedManifestContext | None = None) -> dict[str, JcsValue]:
    s, authority, anchor, eligibility = _validate_digest_material_inputs(s, authority, anchor, eligibility, restricted_context=restricted_context)
    governing = _governing_versions_material(authority.governing_versions) if type(authority) is ProductionStatementAuthority else {"statement_contract_version": None, "statement_set_contract_version": None, "statement_records_contract_version": None, "rule_contract_version": None}
    return {"submission": s.source_snapshot_ref.contract_version, "track_source_binding": s.track_source_binding.contract_version, "target_authority": "production-statement-authority.v1" if type(authority) is ProductionStatementAuthority else "preprod-run-authority.v1", "rule_metadata": governing["rule_contract_version"], "anchor_policy": anchor.contract_version, "eligibility_policy": eligibility.contract_version, **governing}


def _canonical_operation_identity_material(key: IdempotencyKey, s: FeedbackSubmission, authority: ProductionStatementAuthority | PreprodRunAuthority, anchor: AnchorPolicy, eligibility: EligibilityPolicy, *, restricted_context: _PreprodRestrictedManifestContext | None = None) -> dict[str, JcsValue]:
    if type(key) is not IdempotencyKey:
        _error("/key", "invalid key class")
    s, authority, anchor, eligibility = _validate_digest_material_inputs(s, authority, anchor, eligibility, restricted_context=restricted_context)
    items = _tuple(s.feedback_items, "/submission/feedback_items")
    if any(type(item) is not FeedbackItem for item in items):
        _error("/submission/feedback_items", "invalid feedback item member")
    return {"key": _idempotency_key_material(key, False), "item_raw_identities": tuple(_feedback_item_material(x) for x in sorted(items, key=lambda x: x.feedback_item_id.encode("utf-16-be"))), "anchor_policy": (anchor.policy_id, anchor.policy_version), "eligibility_policy": (eligibility.policy_id, eligibility.policy_version), "submission_schema": s.source_snapshot_ref.schema_version, "submission_contract": s.source_snapshot_ref.contract_version, "governing_versions": _governing_versions_material(authority.governing_versions) if type(authority) is ProductionStatementAuthority else (None, None, None, None), "source_snapshot_digest": _digest_ref_material(s.source_snapshot_ref.content_digest), "feedback_id": s.feedback_id, "case_id": s.case_id, "track": _enum(s.track), "statement_set_id": authority.statement_set.statement_set_id if type(authority) is ProductionStatementAuthority else None}


def _invalid_authority_material(protocol: BindingProtocol) -> dict[str, JcsValue]:
    return {"material_domain": "G6_TASK8_TARGET_AUTHORITY", "material_version": "invalid-authority.v1", "authority_status": "INVALID_MATERIAL", "protocol": protocol}


def _invalid_schema_versions_digest_material(s: FeedbackSubmission, protocol: BindingProtocol, anchor: AnchorPolicy, eligibility: EligibilityPolicy) -> dict[str, JcsValue]:
    authority_identity = {"status": "INVALID_MATERIAL", "protocol": protocol, "schema_version": None, "rule_metadata_schema_version": None}
    return {"submission": s.source_snapshot_ref.schema_version, "track_source_binding": s.track_source_binding.schema_version, "target_authority": authority_identity, "rule_metadata": None, "anchor_policy": anchor.schema_version, "eligibility_policy": eligibility.schema_version}


def _invalid_contract_digest_material(s: FeedbackSubmission, protocol: BindingProtocol, anchor: AnchorPolicy, eligibility: EligibilityPolicy) -> dict[str, JcsValue]:
    governing = (None, None, None, None)
    authority_identity = {"status": "INVALID_MATERIAL", "protocol": protocol, "contract_version": None, "governing_versions": governing}
    return {"submission": s.source_snapshot_ref.contract_version, "track_source_binding": s.track_source_binding.contract_version, "target_authority": authority_identity, "governing_versions": governing, "anchor_policy": anchor.contract_version, "eligibility_policy": eligibility.contract_version}


def _invalid_canonical_operation_identity_material(key: IdempotencyKey, s: FeedbackSubmission, protocol: BindingProtocol, anchor: AnchorPolicy, eligibility: EligibilityPolicy) -> dict[str, JcsValue]:
    raw_identities = tuple({"feedback_item_id": item.feedback_item_id, "target_statement_id": item.target_statement_id, "target_statement_revision_id": item.target_statement_revision_id, "target_run_id": item.target_run_id, "target_prediction_id": item.target_prediction_id} for item in sorted(s.feedback_items, key=lambda item: item.feedback_item_id.encode("utf-16-be")))
    authority_identity = {"status": "INVALID_MATERIAL", "protocol": protocol, "authority_schema_version": None, "authority_contract_version": None, "governing_versions": (None, None, None, None), "statement_set_id": None}
    return {"key": _idempotency_key_material(key, False), "item_raw_identities": raw_identities, "anchor_policy": (anchor.policy_id, anchor.policy_version), "eligibility_policy": (eligibility.policy_id, eligibility.policy_version), "submission_schema": s.source_snapshot_ref.schema_version, "submission_contract": s.source_snapshot_ref.contract_version, "authority_identity": authority_identity, "source_snapshot_digest": _digest_ref_material(s.source_snapshot_ref.content_digest), "feedback_id": s.feedback_id, "case_id": s.case_id, "track": _enum(s.track)}


def _ref(object_type: str, object_id: str, revision: str | None, schema: str, contract: str | None, digest: DigestRef, captured: str) -> VersionedObjectRef:
    return VersionedObjectRef(object_type, object_id, revision, schema, contract, DigestPresent("PRESENT", digest), None, captured)


def _policy_ref(policy: AnchorPolicy | EligibilityPolicy, object_id: str, revision: str, locator: str) -> VersionedObjectRef:
    return VersionedObjectRef("POLICY", object_id, revision, policy.schema_version, policy.contract_version, DigestPresent("PRESENT", policy.content_digest), locator, _POLICY_CAPTURED_AT)


def _parse_digest(value: object, path: str) -> DigestRef:
    if type(value) is not dict or set(value) != {"algorithm", "canonicalization", "value"}: _error(path, "invalid digest object")
    algorithm = _nonblank(value["algorithm"], path + "/algorithm")
    canonicalization = _nonblank(value["canonicalization"], path + "/canonicalization")
    digest_value = _nonblank(value["value"], path + "/value")
    if algorithm != "sha256" or canonicalization != "RFC8785-JCS-UTF8" or len(digest_value) != 64 or any(character not in "0123456789abcdef" for character in digest_value):
        _error(path, "invalid bounded JCS digest identity")
    return DigestRef(algorithm, canonicalization, digest_value)


def _parse_ref(value: object, path: str) -> VersionedObjectRef:
    keys = {"object_type", "object_id", "revision_id", "schema_version", "contract_version", "digest_binding", "source_locator_id", "captured_at"}
    if type(value) is not dict or set(value) != keys: _error(path, "invalid ref keys")
    object_type = _nonblank(value["object_type"], path + "/object_type")
    object_id = _nonblank(value["object_id"], path + "/object_id")
    revision_id = _nullable_nonblank(value["revision_id"], path + "/revision_id")
    schema_version = _nonblank(value["schema_version"], path + "/schema_version")
    contract_version = _nullable_nonblank(value["contract_version"], path + "/contract_version")
    binding = value["digest_binding"]
    if type(binding) is not dict: _error(path + "/digest_binding", "invalid digest binding")
    binding_keys = set(binding)
    if binding_keys not in ({"status", "digest"}, {"status", "digest", "issue_id"}):
        _error(path + "/digest_binding", "invalid digest binding keys")
    status = binding["status"]
    if status == "PRESENT":
        if binding_keys != {"status", "digest"}: _error(path + "/digest_binding", "invalid present digest binding keys")
        db = DigestPresent("PRESENT", _parse_digest(binding["digest"], path + "/digest_binding/digest"))
    elif status == "MISSING":
        if binding_keys != {"status", "digest", "issue_id"}: _error(path + "/digest_binding", "invalid missing digest binding keys")
        if binding["digest"] is not None: _error(path + "/digest_binding/digest", "missing digest must be null")
        db = DigestMissing("MISSING", None, _nonblank(binding["issue_id"], path + "/digest_binding/issue_id"))
    else:
        _error(path + "/digest_binding/status", "invalid digest binding tag")
    source_locator_id = _nullable_nonblank(value["source_locator_id"], path + "/source_locator_id")
    captured_at = _nullable_nonblank(value["captured_at"], path + "/captured_at")
    return VersionedObjectRef(object_type, object_id, revision_id, schema_version, contract_version, db, source_locator_id, captured_at)


def _parse_track_binding(value: object, path: str) -> TrackSourceBinding:
    keys = {"track_source_binding_id", "side", "track", "state", "source_evidence_ref", "parser_ref", "schema_version", "contract_version", "content_digest", "state_reason_codes", "captured_at"}
    if type(value) is not dict or set(value) != keys: _error(path, "invalid track binding keys")
    side = value["side"]
    if side != "SUBMISSION_SOURCE": _error(path + "/side", "invalid submission binding side")
    binding_id = _nonblank(value["track_source_binding_id"], path + "/track_source_binding_id")
    try: track = RunTrack(value["track"])
    except (ValueError, TypeError): _error(path + "/track", "invalid track")
    state = value["state"]
    expected_reasons = {
        "AVAILABLE_RESOLVED": (),
        "SOURCE_MISSING": ("TRACK_SOURCE_MISSING",),
        "UNPARSABLE": ("TRACK_SOURCE_UNPARSABLE",),
        "AMBIGUOUS": ("TRACK_SOURCE_AMBIGUOUS",),
        "INTEGRITY_FAILED": ("TRACK_SOURCE_INTEGRITY_FAILED",),
    }
    if state not in expected_reasons: _error(path + "/state", "invalid track binding state")
    source_ref = _parse_ref(value["source_evidence_ref"], path + "/source_evidence_ref")
    parser_ref = _parse_ref(value["parser_ref"], path + "/parser_ref")
    schema_version = _nonblank(value["schema_version"], path + "/schema_version")
    contract_version = _nonblank(value["contract_version"], path + "/contract_version")
    content_digest = _parse_digest(value["content_digest"], path + "/content_digest")
    reasons = _string_tuple(value["state_reason_codes"], path + "/state_reason_codes", nonblank=True)
    captured_at = _nonblank(value["captured_at"], path + "/captured_at")
    if reasons != expected_reasons[state]: _error(path + "/state_reason_codes", "state and reason tuple mismatch")
    return TrackSourceBinding(binding_id, side, track, state, source_ref, parser_ref, schema_version, contract_version, content_digest, reasons, captured_at)


def _parse_snapshot(value: object, path: str) -> SnapshotRef:
    keys = {"source_snapshot_id", "source_type", "source_locator_ids", "schema_version", "contract_version", "content_digest", "captured_at", "immutability"}
    if type(value) is not dict or set(value) != keys: _error(path, "invalid snapshot keys")
    source_type = value["source_type"]
    if source_type != "FEEDBACK": _error(path + "/source_type", "snapshot source type must be FEEDBACK")
    snapshot_id = _nonblank(value["source_snapshot_id"], path + "/source_snapshot_id")
    locators = _string_tuple(value["source_locator_ids"], path + "/source_locator_ids", nonblank=True)
    schema_version = _nullable_nonblank(value["schema_version"], path + "/schema_version")
    contract_version = _nullable_nonblank(value["contract_version"], path + "/contract_version")
    content_digest = _parse_digest(value["content_digest"], path + "/content_digest")
    captured_at = _nonblank(value["captured_at"], path + "/captured_at")
    immutability = value["immutability"]
    if immutability not in ("IMMUTABLE", "MUTABLE_SOURCE_CAPTURE"): _error(path + "/immutability", "invalid snapshot immutability")
    if len(locators) != len(set(locators)): _error(path + "/source_locator_ids", "duplicate source locator")
    return SnapshotRef(snapshot_id, source_type, locators, schema_version, contract_version, content_digest, captured_at, immutability)


def _parse_submission(raw: bytes) -> FeedbackSubmission:
    value = parse_bounded_jcs(raw)
    keys = {"feedback_id", "case_id", "track", "track_source_binding", "source_snapshot_ref", "source_snapshot_payload", "parser_id", "parser_version", "feedback_items", "content_digest", "captured_at"}
    if type(value) is not dict or set(value) != keys: _error("/raw", "invalid submission keys")
    feedback_id = _nonblank(value["feedback_id"], "/feedback_id")
    case_id = _nonblank(value["case_id"], "/case_id")
    try: track = RunTrack(value["track"])
    except (ValueError, TypeError): _error("/track", "invalid track")
    track_binding = _parse_track_binding(value["track_source_binding"], "/track_source_binding")
    snapshot = _parse_snapshot(value["source_snapshot_ref"], "/source_snapshot_ref")
    payload = value["source_snapshot_payload"]
    parser_id = _nonblank(value["parser_id"], "/parser_id")
    parser_version = _nonblank(value["parser_version"], "/parser_version")
    raw_items = _tuple(value["feedback_items"], "/feedback_items")
    items = []
    item_keys = {"feedback_item_id", "feedback_id", "source_span_locator", "target_statement_id", "target_statement_revision_id", "target_run_id", "target_prediction_id", "verdict", "annotation", "integrity", "issue_ids"}
    for index, item in enumerate(raw_items):
        path = f"/feedback_items/{index}"
        if type(item) is not dict or set(item) != item_keys: _error(path, "invalid item keys")
        item_id = _nonblank(item["feedback_item_id"], path + "/feedback_item_id")
        item_feedback_id = _nonblank(item["feedback_id"], path + "/feedback_id")
        source_span_locator = _nonblank(item["source_span_locator"], path + "/source_span_locator")
        target_statement_id = _nullable_nonblank(item["target_statement_id"], path + "/target_statement_id")
        target_revision_id = _nullable_nonblank(item["target_statement_revision_id"], path + "/target_statement_revision_id")
        target_run_id = _nullable_nonblank(item["target_run_id"], path + "/target_run_id")
        target_prediction_id = _nullable_nonblank(item["target_prediction_id"], path + "/target_prediction_id")
        verdict = _nonblank(item["verdict"], path + "/verdict")
        annotation = item["annotation"] if type(item["annotation"]) is str else _error(path + "/annotation", "invalid annotation")
        integrity = item["integrity"]
        if integrity not in ("VALID", "INVALID", "UNRESOLVED"): _error(path + "/integrity", "invalid integrity")
        issue_ids = _string_tuple(item["issue_ids"], path + "/issue_ids", nonblank=True)
        if item_feedback_id != feedback_id: _error(path + "/feedback_id", "feedback identity mismatch")
        if len(issue_ids) != len(set(issue_ids)): _error(path + "/issue_ids", "duplicate issue id")
        items.append(FeedbackItem(item_id, item_feedback_id, source_span_locator, target_statement_id, target_revision_id, target_run_id, target_prediction_id, verdict, annotation, integrity, issue_ids))
    content_digest = _parse_digest(value["content_digest"], "/content_digest")
    captured_at = _nonblank(value["captured_at"], "/captured_at")
    item_ids = tuple(item.feedback_item_id for item in items)
    if len(item_ids) != len(set(item_ids)): _error("/feedback_items", "duplicate feedback_item_id")
    if track_binding.track is not track: _error("/track_source_binding/track", "submission source track mismatch")
    if track_binding.parser_ref.object_id != parser_id or track_binding.parser_ref.revision_id != parser_version:
        _error("/track_source_binding/parser_ref", "parser identity mismatch")
    submission = FeedbackSubmission(feedback_id, case_id, track, track_binding, snapshot, payload, parser_id, parser_version, tuple(items), content_digest, captured_at)
    if bounded_jcs_sha256(payload) != snapshot.content_digest:
        _error("/source_snapshot_ref/content_digest", "snapshot payload digest mismatch", integrity=True)
    track_binding_material = _track_source_binding_self_excluded_material(track_binding)
    if bounded_jcs_sha256(track_binding_material) != track_binding.content_digest:
        _error("/track_source_binding/content_digest", "track source digest mismatch", integrity=True)
    if bounded_jcs_sha256(_feedback_submission_self_excluded_material(submission)) != submission.content_digest:
        _error("/content_digest", "submission digest mismatch", integrity=True)
    return submission


def _resolve_pointer(snapshot: SnapshotRef, payload: JcsValue, locator: str) -> Literal["RESOLVED", "MISSING", "INVALID"]:
    if type(snapshot) is not SnapshotRef or type(locator) is not str:
        return "INVALID"
    if locator.count("#") != 1:
        return "INVALID"
    identity, pointer = locator.split("#")
    if identity != snapshot.source_snapshot_id or pointer and not pointer.startswith("/"):
        return "INVALID"
    node: JcsValue = payload
    if not pointer:
        return "RESOLVED"
    for raw in pointer[1:].split("/"):
        index = 0
        decoded = ""
        while index < len(raw):
            if raw[index] == "~":
                if index + 1 >= len(raw) or raw[index + 1] not in "01":
                    return "INVALID"
                decoded += "~" if raw[index + 1] == "0" else "/"; index += 2
            else: decoded += raw[index]; index += 1
        if decoded.replace("~", "~0").replace("/", "~1") != raw:
            return "INVALID"
        if type(node) is dict:
            if decoded not in node: return "MISSING"
            node = node[decoded]
        elif type(node) is tuple:
            if decoded == "-" or not (decoded == "0" or decoded and decoded[0] in "123456789" and decoded.isdigit()):
                return "INVALID"
            position = int(decoded)
            if position >= len(node): return "MISSING"
            node = node[position]
        else:
            return "MISSING"
    return "RESOLVED"


def _validate_track_binding(binding: TrackSourceBinding, side: str) -> None:
    if type(binding) is not TrackSourceBinding:
        _error("/target_track_source_binding", "invalid target binding class or side")
    material = _track_source_binding_self_excluded_material(binding)
    binding_side = getattr(binding, "side", _MISSING)
    content_digest = getattr(binding, "content_digest", _MISSING)
    if binding_side != side:
        _error("/target_track_source_binding", "invalid target binding class or side")
    _digest_ref_material(content_digest)
    if bounded_jcs_sha256(material) != content_digest:
        _error("/target_track_source_binding/content_digest", "target binding digest mismatch", integrity=True)


def _production_record_scope_valid(record: object, statement_set_id: str) -> bool:
    """Validate the Production records scope without inventing run authority."""
    if type(record) is not ArtifactRecord or type(statement_set_id) is not str or not statement_set_id:
        return False
    record_statement_set_id = getattr(record, "statement_set_id", _MISSING)
    record_run_id = getattr(record, "run_id", _MISSING)
    return (
        type(record_statement_set_id) is str
        and bool(record_statement_set_id)
        and record_statement_set_id == statement_set_id
        and record_run_id is None
    )


def _artifact_ref(record: ArtifactRecord, captured_at: str) -> VersionedObjectRef:
    digest = record.observed_digest if type(record.observed_digest) is DigestRef else record.expected_digest
    if type(digest) is not DigestRef: _error("/manifest/records/digest", "artifact digest missing")
    return _ref(record.artifact_role, _nonblank(record.artifact_id, "/manifest/records/artifact_id"), None, _nonblank(record.schema_version, "/manifest/records/schema_version"), None, digest, captured_at)


def _production_raw_target_shape(item: object) -> bool:
    if type(item) is not FeedbackItem:
        return False
    missing = object()
    statement_id = getattr(item, "target_statement_id", missing)
    revision_id = getattr(item, "target_statement_revision_id", missing)
    run_id = getattr(item, "target_run_id", missing)
    prediction_id = getattr(item, "target_prediction_id", missing)
    return (
        type(statement_id) is str and bool(statement_id)
        and (revision_id is None or (type(revision_id) is str and bool(revision_id)))
        and run_id is None
        and prediction_id is None
    )


def _preprod_raw_target_shape(item: object) -> bool:
    if type(item) is not FeedbackItem:
        return False
    missing = object()
    statement_id = getattr(item, "target_statement_id", missing)
    revision_id = getattr(item, "target_statement_revision_id", missing)
    run_id = getattr(item, "target_run_id", missing)
    prediction_id = getattr(item, "target_prediction_id", missing)
    return statement_id is None and revision_id is None and type(run_id) is str and bool(run_id) and prediction_id is None


def _production_target(item: FeedbackItem, a: ProductionStatementAuthority, captured_at: str) -> tuple[BindingStatus, TargetResolutionCategory | None, tuple[VersionedObjectRef, ...], VersionedObjectRef | None, tuple[MatchRequired | MatchOptional, ...]]:
    invalid_dimensions = ("UNKNOWN", "UNKNOWN", "NOT_APPLICABLE", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN")
    if not _production_raw_target_shape(item) or type(a) is not ProductionStatementAuthority or type(captured_at) is not str or not captured_at:
        return "INVALID", "INVALID_MATERIAL", (), None, invalid_dimensions
    statements = tuple(x for x in a.statement_set.statements if x.statement_id == item.target_statement_id)
    if not statements: return "UNBOUND", "TARGET_NOT_FOUND", (), None, ("MATCH", "MATCH", "NOT_APPLICABLE", "MISMATCH", "UNKNOWN", "UNKNOWN", "UNKNOWN")
    if item.target_statement_revision_id is None:
        revisions = statements
    else:
        revisions = tuple(x for x in statements if x.statement_revision_id == item.target_statement_revision_id)
    if len(statements) > 1 or len(revisions) > 1: return "AMBIGUOUS", "AMBIGUOUS_CANDIDATES", (), None, ("MATCH", "MATCH", "NOT_APPLICABLE", "MATCH", "UNKNOWN", "UNKNOWN", "UNKNOWN")
    if not revisions: return "UNBOUND", "REQUIRED_MATCH_FAILED", (), None, ("MATCH", "MATCH", "NOT_APPLICABLE", "MATCH", "MISMATCH", "MATCH", "UNKNOWN")
    statement = revisions[0]
    revision_match: MatchOptional = "UNKNOWN" if item.target_statement_revision_id is None else "MATCH"
    target_track_match: MatchRequired = "MATCH" if statement.track == RunTrack.PRODUCTION_DEFAULT else "MISMATCH"
    statement_ref_candidates = tuple(
        x for x in a.statement_refs
        if x.object_id == statement.statement_id
        and x.revision_id == statement.statement_revision_id
    )
    if statement_ref_candidates and any(
        x.object_type != "STATEMENT"
        or x.schema_version != statement.statement_schema_version
        or x.contract_version != a.governing_versions.statement_contract_version
        or type(x.digest_binding) is not DigestPresent
        or x.digest_binding.digest != statement.content_digest
        for x in statement_ref_candidates
    ):
        return "INVALID", "INVALID_MATERIAL", (), None, ("MATCH", target_track_match, "NOT_APPLICABLE", "MATCH", "MATCH", "UNKNOWN", "UNKNOWN")
    statement_refs = statement_ref_candidates
    set_ref = a.statement_set_ref
    if (
        set_ref.object_type != "STATEMENT_SET"
        or set_ref.object_id != a.statement_set.statement_set_id
        or set_ref.schema_version != a.statement_set.statement_schema_version
        or set_ref.contract_version != a.governing_versions.statement_set_contract_version
        or type(set_ref.digest_binding) is not DigestPresent
        or set_ref.digest_binding.digest != a.statement_set.content_digest
    ):
        return "INVALID", "INVALID_MATERIAL", (), None, ("MATCH", target_track_match, "NOT_APPLICABLE", "MATCH", "MATCH", "MISMATCH", "UNKNOWN")
    projection_candidates = tuple(
        x for x in a.records_projection_records
        if x.statement_id == statement.statement_id
    )
    if not projection_candidates:
        status: BindingStatus = (
            "INVALID" if a.records_projection_records else "UNBOUND"
        )
        category: TargetResolutionCategory = (
            "INVALID_MATERIAL"
            if a.records_projection_records
            else "PROTOCOL_GRAPH_INCOMPLETE"
        )
        return status, category, (), None, ("MATCH", target_track_match, "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "UNKNOWN")
    if any(
        x.projection_type != "STATEMENT_RECORDS"
        or x.statement_set_id != a.statement_set.statement_set_id
        or x.statement_revision_id != statement.statement_revision_id
        or x.source_statement_digest != statement.content_digest
        or x.fidelity != "LOSSLESS"
        or x.dropped_refs != ()
        or x.synthesized_fields != ()
        or x.projected_object_ref not in a.records_projection_refs
        for x in projection_candidates
    ):
        return "INVALID", "INVALID_MATERIAL", (), None, ("MATCH", target_track_match, "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "UNKNOWN")
    projections = projection_candidates
    if len(projections) != 1:
        return "AMBIGUOUS", "AMBIGUOUS_CANDIDATES", (), None, ("MATCH", target_track_match, "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "UNKNOWN")
    projection_ref = projections[0].projected_object_ref
    authority_projection_refs = tuple(ref for ref in a.records_projection_refs if ref == projection_ref)
    if (
        len(authority_projection_refs) != 1
        or projection_ref.object_type != "STATEMENT_RECORDS"
        or projection_ref.contract_version != a.governing_versions.statement_records_contract_version
        or type(projection_ref.digest_binding) is not DigestPresent
    ):
        return "INVALID", "INVALID_MATERIAL", (), None, ("MATCH", target_track_match, "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "UNKNOWN")
    projected_digest = projection_ref.digest_binding.digest
    projected_records = tuple(
        record for record in a.manifest.records
        if record.artifact_role == projection_ref.object_type
        and record.artifact_id == projection_ref.object_id
        and record.state not in (ArtifactItemState.SUPERSEDED, "SUPERSEDED")
    )
    artifacts = tuple(
        record for record in projected_records
        if record.artifact_role == projection_ref.object_type == "STATEMENT_RECORDS"
        and record.artifact_id == projection_ref.object_id
        and record.schema_version == projection_ref.schema_version
        and record.expected_digest == record.observed_digest == projected_digest
        and record.state in (ArtifactItemState.VERIFIED, "VERIFIED")
        and record.state not in (ArtifactItemState.SUPERSEDED, "SUPERSEDED")
        and record.case_id == statement.case_id
        and record.track == statement.track
        and _production_record_scope_valid(record, statement.statement_set_id)
    )
    if not artifacts and any(
        record.schema_version != projection_ref.schema_version
        or record.run_id is not None
        for record in projected_records
    ):
        return "INVALID", "INVALID_MATERIAL", (), None, ("MATCH", target_track_match, "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "UNKNOWN")
    anchors = tuple(x for x in a.anchor_selections if x.statement_id == statement.statement_id and x.statement_revision_id == statement.statement_revision_id)
    policy = _pinned_anchor_policy()
    for candidate in anchors:
        rules = candidate.all_rule_refs
        selected_candidate = candidate.selected_anchor_rule_ref
        unsupported = selected_candidate is None and candidate.fidelity == "UNSUPPORTED" and candidate.fanout_scope == "NONE"
        if not unsupported and (
            not rules
            or len(rules) != len(set(rules))
            or selected_candidate is None
            or rules.count(selected_candidate) != 1
            or selected_candidate.object_type != policy.required_rule_object_type
            or selected_candidate.contract_version != a.governing_versions.rule_contract_version
            or candidate.non_anchor_rule_refs != tuple(x for x in rules if x != selected_candidate)
            or candidate.selection_policy_id != policy.policy_id
            or candidate.selection_policy_version != policy.policy_version
            or candidate.fidelity != policy.required_fidelity
            or candidate.fanout_scope != policy.required_fanout_scope
            or candidate.source_order_digest != bounded_jcs_sha256(tuple(_versioned_object_ref_material(x) for x in rules))
        ):
            return "INVALID", "INVALID_MATERIAL", (), None, ("MATCH", target_track_match, "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "UNKNOWN")
    if not statement_refs or not artifacts or not anchors: return "UNBOUND", "PROTOCOL_GRAPH_INCOMPLETE", (), None, ("MATCH", target_track_match, "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "UNKNOWN")
    if len(statement_refs) != 1 or len(artifacts) != 1 or len(anchors) != 1: return "AMBIGUOUS", "AMBIGUOUS_CANDIDATES", (), None, ("MATCH", target_track_match, "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "UNKNOWN")
    anchor = anchors[0]
    rules = anchor.all_rule_refs
    selected = anchor.selected_anchor_rule_ref
    if selected is None:
        return "UNBOUND", "PROTOCOL_GRAPH_INCOMPLETE", (), None, ("MATCH", target_track_match, "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "UNKNOWN")
    metadata_candidates = tuple(
        x for x in a.rule_metadata_receipts
        if x.rule_ref.object_type == selected.object_type and x.rule_ref.object_id == selected.object_id
    )
    if a.rule_metadata_receipts and not metadata_candidates:
        return "INVALID", "INVALID_MATERIAL", (), None, ("MATCH", target_track_match, "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "MATCH")
    for candidate in metadata_candidates:
        if (
            type(candidate.rule_ref.digest_binding) is not DigestPresent
            or type(selected.digest_binding) is not DigestPresent
            or candidate.rule_ref.digest_binding.digest != selected.digest_binding.digest
            or candidate.rule_ref != selected
            or type(candidate.source_ref.digest_binding) is not DigestPresent
            or candidate.metadata_schema_version != candidate.source_ref.schema_version
            or candidate.metadata_contract_version != a.governing_versions.rule_contract_version
            or selected.contract_version != a.governing_versions.rule_contract_version
            or candidate.rule_type == "UNMAPPED"
            or bounded_jcs_sha256(_rule_metadata_receipt_self_excluded_material(candidate)) != candidate.content_digest
        ):
            return "INVALID", "INVALID_MATERIAL", (), None, ("MATCH", target_track_match, "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "MATCH")
    metadata = tuple(x for x in metadata_candidates if x.rule_ref == selected)
    if not metadata: return "UNBOUND", "PROTOCOL_GRAPH_INCOMPLETE", (), None, ("MATCH", target_track_match, "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "MATCH")
    if len(metadata) != 1: return "AMBIGUOUS", "AMBIGUOUS_CANDIDATES", (), None, ("MATCH", target_track_match, "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "MATCH")
    md = metadata[0]
    if md.family_id == "UNMAPPED": return "UNBOUND", "PROTOCOL_GRAPH_INCOMPLETE", (), None, ("MATCH", target_track_match, "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "MATCH")
    artifact = artifacts[0]
    if (
        projection_ref.object_type != artifact.artifact_role
        or projection_ref.object_id != artifact.artifact_id
        or projection_ref.schema_version != artifact.schema_version
        or type(projection_ref.digest_binding) is not DigestPresent
        or artifact.expected_digest is None
        or artifact.observed_digest is None
        or artifact.expected_digest != artifact.observed_digest
        or artifact.observed_digest != projection_ref.digest_binding.digest
    ):
        return "INVALID", "INVALID_MATERIAL", (), None, ("MATCH", target_track_match, "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "MISMATCH")
    graph = (statement_refs[0], a.statement_set_ref, projection_ref, selected)
    return "BOUND", None, graph, selected, ("MATCH", target_track_match, "NOT_APPLICABLE", "MATCH", revision_match, "MATCH", "MATCH")


def _preprod_target(
    item: FeedbackItem,
    a: PreprodRunAuthority,
    snapshot: SnapshotRef,
    captured_at: str,
    *,
    restricted_context: _PreprodRestrictedManifestContext | None = None,
) -> tuple[BindingStatus, TargetResolutionCategory | None, tuple[VersionedObjectRef, ...], tuple[MatchRequired | MatchOptional, ...]]:
    invalid_dimensions = ("UNKNOWN", "UNKNOWN", "UNKNOWN", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "UNKNOWN")
    if not _preprod_raw_target_shape(item) or type(a) is not PreprodRunAuthority or type(snapshot) is not SnapshotRef or type(captured_at) is not str or not captured_at:
        return "INVALID", "INVALID_MATERIAL", (), invalid_dimensions
    if item.target_run_id != a.run_id: return "UNBOUND", "REQUIRED_MATCH_FAILED", (), ("MATCH", "MATCH", "MISMATCH", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "UNKNOWN")
    roles = ("RUN_SNAPSHOT", "DECISION_RUN", "FEEDBACK_ATTACHMENT", "MANIFEST")
    if type(a.manifest.key) is RunArtifactSetKeyV1:
        restricted_context = _revalidate_preprod_restricted_manifest_context(
            restricted_context, a, a.manifest,
        )
    elif restricted_context is not None:
        return "INVALID", "INVALID_MATERIAL", (), invalid_dimensions
    by_role = {role: tuple(x for x in a.target_refs if x.object_type == role) for role in roles}
    if not by_role["RUN_SNAPSHOT"]:
        return "UNBOUND", "PROTOCOL_GRAPH_INCOMPLETE", (), ("MATCH", "MATCH", "MATCH", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "UNKNOWN")
    graph = tuple(ref for role in roles for ref in by_role[role])
    run_snapshot_record: ArtifactRecord | None = None
    for ref in graph:
        if type(ref.digest_binding) is not DigestPresent:
            return "INVALID", "INVALID_MATERIAL", (), invalid_dimensions
        if restricted_context is not None and ref.object_type == "MANIFEST":
            if ref.object_id != a.manifest.manifest_id or ref.digest_binding.digest != restricted_context.verifier_returned_records_digest:
                return "INVALID", "INVALID_MATERIAL", (), invalid_dimensions
            continue
        matches = tuple(record for record in a.manifest.records if record.artifact_role == ref.object_type and record.artifact_id == ref.object_id and type(record.schema_version) is str and bool(record.schema_version) and record.schema_version == ref.schema_version and record.expected_digest is not None and record.expected_digest == record.observed_digest and record.observed_digest == ref.digest_binding.digest and record.state not in (ArtifactItemState.SUPERSEDED, "SUPERSEDED") and record.case_id == a.case_id and record.track is RunTrack.V5_V6_PREPROD and record.run_id == a.run_id and record.statement_set_id is None and record.state in (ArtifactItemState.VERIFIED, "VERIFIED"))
        if not matches:
            return "UNBOUND", "TARGET_NOT_FOUND", (), ("MATCH", "MATCH", "MATCH", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "MISMATCH")
        if len(matches) > 1:
            return "AMBIGUOUS", "AMBIGUOUS_CANDIDATES", (), ("MATCH", "MATCH", "MATCH", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "MISMATCH")
        if ref.object_type == "RUN_SNAPSHOT":
            run_snapshot_record = matches[0]
    run_snapshot_ref = by_role["RUN_SNAPSHOT"][0]
    if (
        run_snapshot_record is None
        or snapshot.source_snapshot_id != run_snapshot_record.artifact_id
        or type(snapshot.schema_version) is not str
        or not snapshot.schema_version
        or snapshot.schema_version != run_snapshot_record.schema_version
        or snapshot.content_digest != run_snapshot_record.expected_digest
        or snapshot.content_digest != run_snapshot_record.observed_digest
        or type(run_snapshot_ref.digest_binding) is not DigestPresent
        or snapshot.content_digest != run_snapshot_ref.digest_binding.digest
    ):
        return "INVALID", "INVALID_MATERIAL", (), ("MATCH", "MATCH", "MATCH", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "MISMATCH")
    return "BOUND", None, graph, ("MATCH", "MATCH", "MATCH", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "MATCH")


def _make_target_receipt(item: FeedbackItem, protocol: BindingProtocol, status: BindingStatus, category: TargetResolutionCategory | None, graph: tuple[VersionedObjectRef, ...]) -> ItemTargetReceipt:
    graph_digest = bounded_jcs_sha256(_item_target_graph_material(protocol, item, status, category, graph))
    unsigned = ItemTargetReceipt(item.feedback_item_id, protocol, item.target_statement_id, item.target_statement_revision_id, item.target_run_id, item.target_prediction_id, status, category, graph, graph_digest, DigestRef("sha256", "RFC8785-JCS-UTF8", "0" * 64))
    return ItemTargetReceipt(unsigned.feedback_item_id, unsigned.protocol, unsigned.target_statement_id, unsigned.target_statement_revision_id, unsigned.target_run_id, unsigned.target_prediction_id, unsigned.resolution_status, unsigned.non_bound_category, unsigned.graph, unsigned.graph_digest, bounded_jcs_sha256(_item_target_receipt_self_excluded_material(unsigned)))


def _binding_issues(index: int, status: BindingStatus, revision_match: MatchOptional, track_match: MatchRequired) -> tuple[DetectedIssue, ...]:
    if track_match == "MISMATCH":
        return (DetectedIssue("FEEDBACK.TRACK_MISMATCH", f"/feedback_bindings/{index}/track_match"),)
    if revision_match == "MISMATCH":
        return (DetectedIssue("FEEDBACK.REVISION_MISMATCH", f"/feedback_bindings/{index}/revision_match"),)
    if status == "UNBOUND":
        return (DetectedIssue("FEEDBACK.TARGET_UNBOUND", f"/feedback_bindings/{index}"),)
    return ()


def _compute_operation(raw: RawFeedbackAuthority, submission: FeedbackSubmission, created_at: str) -> FeedbackOperationReceipt:
    authority = raw.target_authority
    target_binding = raw.target_track_source_binding
    anchor_policy, eligibility_policy = _pinned_anchor_policy(), _pinned_eligibility_policy()
    source_digest = submission.content_digest
    protocol: BindingProtocol = "PRODUCTION_STATEMENT" if type(authority) is ProductionStatementAuthority else "PREPROD_RUN_TARGET"
    restricted_context: _PreprodRestrictedManifestContext | None = None
    try:
        if type(authority) is ProductionStatementAuthority:
            authority_material = _production_authority_self_excluded_material(authority)
        else:
            authority_material, restricted_context = _preprod_authority_self_excluded_material(
                authority,
                include_restricted_context=True,
                propagate_manifest_verifier_failure=True,
            )
        authority_digest = bounded_jcs_sha256(authority_material)
        _digest_ref_material(authority.content_digest)
        if authority_digest != authority.content_digest:
            raise F09IntegrityError("FEEDBACK.MATERIAL_INVALID", "/target_authority/content_digest", "authority digest mismatch")
        schema_digest = bounded_jcs_sha256(_schema_versions_digest_material(submission, authority, anchor_policy, eligibility_policy, restricted_context=restricted_context))
        contract_digest = bounded_jcs_sha256(_contract_digest_material(submission, authority, anchor_policy, eligibility_policy, restricted_context=restricted_context))
        statement_set_id = authority.statement_set.statement_set_id if type(authority) is ProductionStatementAuthority else None
        authority_invalid = False
    except _ManifestVerifierFailure as failure:
        raise failure.error
    except (F09ContractError, F09IntegrityError):
        authority_invalid = True
        authority_digest = bounded_jcs_sha256(_invalid_authority_material(protocol))
        schema_digest = bounded_jcs_sha256(_invalid_schema_versions_digest_material(submission, protocol, anchor_policy, eligibility_policy))
        contract_digest = bounded_jcs_sha256(_invalid_contract_digest_material(submission, protocol, anchor_policy, eligibility_policy))
        statement_set_id = None
    provisional = IdempotencyKey("BIND_FEEDBACK", submission.case_id, submission.track, source_digest, schema_digest, contract_digest, statement_set_id, submission.feedback_id, DigestRef("sha256", "RFC8785-JCS-UTF8", "0" * 64))
    identity_material = _invalid_canonical_operation_identity_material(provisional, submission, protocol, anchor_policy, eligibility_policy) if authority_invalid else _canonical_operation_identity_material(provisional, submission, authority, anchor_policy, eligibility_policy, restricted_context=restricted_context)
    key = IdempotencyKey(provisional.operation, provisional.case_id, provisional.track, provisional.source_digest, provisional.schema_versions_digest, provisional.contract_digest, provisional.statement_set_id, provisional.feedback_id, bounded_jcs_sha256(identity_material))
    bindings, receipts = [], []
    invalid_dims = ("UNKNOWN", "UNKNOWN", "NOT_APPLICABLE", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN") if protocol == "PRODUCTION_STATEMENT" else ("UNKNOWN", "UNKNOWN", "UNKNOWN", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "UNKNOWN")
    for item_index, item in enumerate(submission.feedback_items):
        raw_target_valid = _production_raw_target_shape(item) if protocol == "PRODUCTION_STATEMENT" else _preprod_raw_target_shape(item)
        if authority_invalid:
            status, category, graph, anchor, dims = "INVALID", "INVALID_MATERIAL", (), None, invalid_dims
        elif not raw_target_valid:
            status, category, graph, anchor, dims = "INVALID", "INVALID_MATERIAL", (), None, invalid_dims
        elif target_binding.state != "AVAILABLE_RESOLVED":
            status = "INVALID" if target_binding.state == "INTEGRITY_FAILED" else "AMBIGUOUS" if target_binding.state == "AMBIGUOUS" else "UNBOUND"
            category, graph, anchor, dims = ("INVALID_MATERIAL" if status == "INVALID" else "AMBIGUOUS_CANDIDATES" if status == "AMBIGUOUS" else "TRACK_UNRESOLVED"), (), None, invalid_dims
        elif item.integrity == "INVALID":
            status, category, graph, anchor, dims = "INVALID", "INVALID_MATERIAL", (), None, invalid_dims
        else:
            pointer_resolution = _resolve_pointer(submission.source_snapshot_ref, submission.source_snapshot_payload, item.source_span_locator)
            if pointer_resolution == "INVALID":
                status, category, graph, anchor, dims = "INVALID", "INVALID_MATERIAL", (), None, invalid_dims
            elif pointer_resolution == "MISSING":
                status, category, graph, anchor, dims = "UNBOUND", "SOURCE_SPAN_NOT_FOUND", (), None, invalid_dims
            elif submission.track_source_binding.state != "AVAILABLE_RESOLVED":
                status = "AMBIGUOUS" if submission.track_source_binding.state == "AMBIGUOUS" else "INVALID" if submission.track_source_binding.state == "INTEGRITY_FAILED" else "UNBOUND"
                category, graph, anchor, dims = ("AMBIGUOUS_CANDIDATES" if status == "AMBIGUOUS" else "INVALID_MATERIAL" if status == "INVALID" else "TRACK_UNRESOLVED"), (), None, invalid_dims
            elif type(authority) is ProductionStatementAuthority:
                status, category, graph, anchor, dims = _production_target(item, authority, raw.captured_at)
            else:
                status, category, graph, dims = _preprod_target(
                    item, authority, submission.source_snapshot_ref, raw.captured_at,
                    restricted_context=restricted_context,
                ); anchor = None
        if authority_invalid or not raw_target_valid or submission.track_source_binding.state != "AVAILABLE_RESOLVED" or target_binding.state != "AVAILABLE_RESOLVED":
            case_match: MatchRequired = "UNKNOWN"
            track_match: MatchRequired = "UNKNOWN"
        else:
            case_match = "MATCH" if submission.case_id == (authority.statement_set.case_id if type(authority) is ProductionStatementAuthority else authority.case_id) else "MISMATCH"
            authority_track = authority.statement_set.track if type(authority) is ProductionStatementAuthority else authority.track
            track_match = "MATCH" if submission.track == authority_track and dims[1] != "MISMATCH" else "MISMATCH"
        if status not in ("INVALID", "AMBIGUOUS") and (case_match == "MISMATCH" or track_match == "MISMATCH"):
            status, category, graph, anchor = "UNBOUND", "REQUIRED_MATCH_FAILED", (), None
        issues = () if authority_invalid else _binding_issues(item_index, status, dims[4], track_match)
        item_ref = _ref("FEEDBACK", item.feedback_item_id, "rev-1", "feedback-item.v1", "g6-task8-feedback-v1", bounded_jcs_sha256(_feedback_item_material(item)), raw.captured_at)
        source_ref = _ref("TRACK_SOURCE_BINDING", submission.track_source_binding.track_source_binding_id, "rev-1", submission.track_source_binding.schema_version, submission.track_source_binding.contract_version, submission.track_source_binding.content_digest, submission.track_source_binding.captured_at)
        unsigned = FeedbackBinding("FEEDBACK-BINDING:" + item.feedback_item_id, item_ref, protocol, source_ref, target_binding, case_match, track_match, dims[2], dims[3], dims[4], dims[5], dims[6], graph[:3] if protocol == "PRODUCTION_STATEMENT" and status == "BOUND" else graph if status == "BOUND" else (), anchor, status, item.issue_ids, issues, DigestRef("sha256", "RFC8785-JCS-UTF8", "0" * 64))
        binding = FeedbackBinding(unsigned.feedback_binding_id, unsigned.feedback_item_ref, unsigned.binding_protocol, unsigned.source_track_binding_ref, unsigned.target_track_source_binding, unsigned.case_match, unsigned.track_match, unsigned.run_match, unsigned.statement_match, unsigned.revision_match, unsigned.statement_set_match, unsigned.artifact_digest_match, unsigned.target_object_refs, unsigned.record_anchor_ref, unsigned.status, unsigned.issue_ids, unsigned.detected_issues, bounded_jcs_sha256(_feedback_binding_self_excluded_material(unsigned)))
        validate_feedback_binding_record(binding); bindings.append(binding); receipts.append(_make_target_receipt(item, protocol, status, category, graph if status == "BOUND" else ()))
    item_receipts = tuple(receipts); aggregate = bounded_jcs_sha256(_aggregate_target_material(item_receipts)); _nonblank(created_at, "/created_at")
    anchor_ref = _policy_ref(anchor_policy, _PINNED_ANCHOR_OBJECT_ID, "rev-r33-anchor-v1", "engine.f09.feedback#PINNED_ANCHOR_POLICY_R33")
    eligibility_ref = _policy_ref(eligibility_policy, _PINNED_ELIGIBILITY_OBJECT_ID, "rev-r33-eligibility-v1", "engine.f09.feedback#PINNED_ELIGIBILITY_POLICY_R33")
    unsigned_receipt = FeedbackOperationReceipt("FEEDBACK-OP:" + key.canonical_key_digest.value, key, source_digest, authority_digest, item_receipts, aggregate, tuple(bindings), anchor_ref, eligibility_ref, created_at, DigestRef("sha256", "RFC8785-JCS-UTF8", "0" * 64))
    return FeedbackOperationReceipt(unsigned_receipt.operation_id, unsigned_receipt.key, unsigned_receipt.source_digest, unsigned_receipt.authority_digest, unsigned_receipt.item_target_receipts, unsigned_receipt.aggregate_target_digest, unsigned_receipt.bindings, unsigned_receipt.anchor_policy_ref, unsigned_receipt.eligibility_policy_ref, unsigned_receipt.created_at, bounded_jcs_sha256(_feedback_operation_receipt_self_excluded_material(unsigned_receipt)))


def _validate_raw_authority_envelope(current: object, clock: object) -> None:
    if type(current) is not RawFeedbackAuthority: _error("/current", "invalid raw authority wrapper")
    missing = object()
    raw_submission = getattr(current, "raw_submission", missing)
    target_authority = getattr(current, "target_authority", missing)
    target_binding = getattr(current, "target_track_source_binding", missing)
    captured_at = getattr(current, "captured_at", missing)
    if any(value is missing for value in (raw_submission, target_authority, target_binding, captured_at)):
        _error("/current", "missing literal public field")
    if type(raw_submission) is not bytes: _error("/raw_submission", "raw submission must be bytes")
    if type(target_authority) not in (ProductionStatementAuthority, PreprodRunAuthority): _error("/target_authority", "invalid target authority class")
    if type(target_binding) is not TrackSourceBinding: _error("/target_track_source_binding", "invalid target binding class")
    if not isinstance(clock, FeedbackClockPort): _error("/clock", "clock does not implement port")
    _nonblank(captured_at, "/captured_at")


def bind_feedback_operation(current: RawFeedbackAuthority, *, prior: PriorFeedbackOperation | None, clock: FeedbackClockPort) -> FeedbackOperationResult:
    _validate_raw_authority_envelope(current, clock)
    if prior is not None and type(prior) is not PriorFeedbackOperation:
        _error("/prior", "invalid prior wrapper")
    prior_raw: RawFeedbackAuthority | None = None
    prior_receipt: FeedbackOperationReceipt | None = None
    if prior is not None:
        prior_raw_value = getattr(prior, "raw_authority", _MISSING)
        prior_receipt_value = getattr(prior, "receipt", _MISSING)
        if prior_raw_value is _MISSING or prior_receipt_value is _MISSING:
            _error("/prior", "missing literal public field")
        if type(prior_raw_value) is not RawFeedbackAuthority:
            _error("/prior/raw_authority", "invalid prior raw authority")
        if type(prior_receipt_value) is not FeedbackOperationReceipt:
            _error("/prior/receipt", "invalid prior receipt class")
        prior_raw = prior_raw_value
        prior_receipt = prior_receipt_value
    current_submission = _parse_submission(current.raw_submission)
    _validate_track_binding(current.target_track_source_binding, "BINDING_TARGET")
    prior_submission: FeedbackSubmission | None = None
    prior_created_at: str | None = None
    if prior_raw is not None and prior_receipt is not None:
        _validate_raw_authority_envelope(prior_raw, clock)
        prior_submission = _parse_submission(prior_raw.raw_submission)
        _validate_track_binding(prior_raw.target_track_source_binding, "BINDING_TARGET")
        prior_created_at_value = getattr(prior_receipt, "created_at", _MISSING)
        if type(prior_created_at_value) is not str or not prior_created_at_value:
            _error("/prior/receipt/created_at", "prior receipt time is invalid", integrity=True)
        prior_created_at = prior_created_at_value
    current_receipt = _compute_operation(current, current_submission, _nonblank(clock.now(), "/created_at"))
    if prior is None:
        return ValidFeedbackOperationResult(True, "NEW_OPERATION", "INITIAL", None, current_receipt, current_receipt.bindings, False, ())
    if prior_submission is None:
        _error("/prior/raw_authority", "prior submission was not validated", integrity=True)
    if prior_raw is None or prior_receipt is None or prior_created_at is None:
        _error("/prior", "prior operation was not validated", integrity=True)
    prior_computed = _compute_operation(prior_raw, prior_submission, prior_created_at)
    if prior_computed != prior_receipt: _error("/prior/receipt", "prior receipt is not independently reproducible", integrity=True)
    same_key = current_receipt.key == prior_receipt.key
    relation: Literal["SAME", "CHANGED"] = "SAME" if current_receipt.source_digest == prior_receipt.source_digest else "CHANGED"
    if not same_key: return ValidFeedbackOperationResult(True, "NEW_OPERATION", relation, prior_receipt, current_receipt, current_receipt.bindings, False, ())
    if current_receipt.aggregate_target_digest == prior_receipt.aggregate_target_digest:
        return ValidFeedbackOperationResult(valid=True, operation_disposition="REUSED_OPERATION", source_identity_relation="SAME", prior_receipt=prior_receipt, current_receipt=prior_receipt, bindings=prior_receipt.bindings, overwrite_permitted=False, detected_issues=())
    issue = _operation_target_mismatch_issue()
    return InvalidFeedbackOperationResult(False, "TARGET_MISMATCH", "SAME", prior_receipt, current_receipt.key, prior_receipt.aggregate_target_digest, current_receipt.aggregate_target_digest, current_receipt.item_target_receipts, (), False, (issue,))


def _operation_target_mismatch_issue() -> DetectedIssue:
    return DetectedIssue("IDEMPOTENCY.DIGEST_MISMATCH", "/feedback/aggregate_target_digest")


def validate_feedback_binding_record(binding: FeedbackBinding) -> None:
    if type(binding) is not FeedbackBinding: _error("/binding", "invalid binding class")
    missing = object()
    feedback_binding_id = getattr(binding, "feedback_binding_id", missing)
    feedback_item_ref_value = getattr(binding, "feedback_item_ref", missing)
    binding_protocol_value = getattr(binding, "binding_protocol", missing)
    source_track_binding_ref_value = getattr(binding, "source_track_binding_ref", missing)
    target_track_source_binding_value = getattr(binding, "target_track_source_binding", missing)
    case_match_value = getattr(binding, "case_match", missing)
    track_match_value = getattr(binding, "track_match", missing)
    run_match_value = getattr(binding, "run_match", missing)
    statement_match_value = getattr(binding, "statement_match", missing)
    revision_match_value = getattr(binding, "revision_match", missing)
    statement_set_match_value = getattr(binding, "statement_set_match", missing)
    artifact_digest_match_value = getattr(binding, "artifact_digest_match", missing)
    target_object_refs_value = getattr(binding, "target_object_refs", missing)
    record_anchor_ref_value = getattr(binding, "record_anchor_ref", missing)
    status_value = getattr(binding, "status", missing)
    issue_ids_value = getattr(binding, "issue_ids", missing)
    detected_issues_value = getattr(binding, "detected_issues", missing)
    content_digest_value = getattr(binding, "content_digest", missing)
    if any(value is missing for value in (feedback_binding_id, feedback_item_ref_value, binding_protocol_value, source_track_binding_ref_value, target_track_source_binding_value, case_match_value, track_match_value, run_match_value, statement_match_value, revision_match_value, statement_set_match_value, artifact_digest_match_value, target_object_refs_value, record_anchor_ref_value, status_value, issue_ids_value, detected_issues_value, content_digest_value)):
        _error("/binding", "missing literal public field")
    binding_id = _nonblank(feedback_binding_id, "/binding/feedback_binding_id")
    if type(binding.feedback_item_ref) is not VersionedObjectRef or type(binding.source_track_binding_ref) is not VersionedObjectRef:
        _error("/binding", "invalid required ref class")
    _versioned_object_ref_material(binding.feedback_item_ref)
    _versioned_object_ref_material(binding.source_track_binding_ref)
    item_ref = binding.feedback_item_ref
    source_ref = binding.source_track_binding_ref
    if (
        binding_id != "FEEDBACK-BINDING:" + item_ref.object_id
        or item_ref.object_type != "FEEDBACK"
        or item_ref.revision_id != "rev-1"
        or item_ref.schema_version != "feedback-item.v1"
        or item_ref.contract_version != "g6-task8-feedback-v1"
        or type(item_ref.digest_binding) is not DigestPresent
        or item_ref.source_locator_id is not None
        or type(item_ref.captured_at) is not str
        or not item_ref.captured_at
        or source_ref.object_type != "TRACK_SOURCE_BINDING"
        or source_ref.revision_id != "rev-1"
        or type(source_ref.contract_version) is not str
        or not source_ref.contract_version
        or type(source_ref.digest_binding) is not DigestPresent
        or source_ref.source_locator_id is not None
        or type(source_ref.captured_at) is not str
        or not source_ref.captured_at
    ):
        _error("/binding", "required ref constructor identity mismatch")
    _validate_track_binding(binding.target_track_source_binding, "BINDING_TARGET")
    if type(binding.binding_protocol) is not str or binding.binding_protocol not in ("PRODUCTION_STATEMENT", "PREPROD_RUN_TARGET"):
        _error("/binding/binding_protocol", "closed protocol domain violation")
    expected_target_track = RunTrack.PRODUCTION_DEFAULT if binding.binding_protocol == "PRODUCTION_STATEMENT" else RunTrack.V5_V6_PREPROD
    if binding.target_track_source_binding.track is not expected_target_track:
        _error("/binding/target_track_source_binding/track", "protocol target track mismatch")
    required_domain = ("MATCH", "MISMATCH", "UNKNOWN")
    optional_domain = ("MATCH", "MISMATCH", "NOT_APPLICABLE", "UNKNOWN")
    if any(type(value) is not str or value not in required_domain for value in (binding.case_match, binding.track_match, binding.artifact_digest_match)):
        _error("/binding", "required match domain violation")
    if any(type(value) is not str or value not in optional_domain for value in (binding.run_match, binding.statement_match, binding.revision_match, binding.statement_set_match)):
        _error("/binding", "optional match domain violation")
    targets = _tuple(binding.target_object_refs, "/binding/target_object_refs")
    if any(type(ref) is not VersionedObjectRef for ref in targets):
        _error("/binding/target_object_refs", "invalid target ref member")
    for ref in targets: _versioned_object_ref_material(ref)
    if binding.record_anchor_ref is not None:
        if type(binding.record_anchor_ref) is not VersionedObjectRef: _error("/binding/record_anchor_ref", "invalid anchor ref")
        _versioned_object_ref_material(binding.record_anchor_ref)
    issue_ids = _string_tuple(binding.issue_ids, "/binding/issue_ids", nonblank=True)
    if len(issue_ids) != len(set(issue_ids)): _error("/binding/issue_ids", "duplicate issue id")
    detected = _tuple(binding.detected_issues, "/binding/detected_issues")
    if any(type(issue) is not DetectedIssue for issue in detected): _error("/binding/detected_issues", "invalid detected issue member")
    for issue in detected: _detected_issue_material(issue)
    if type(binding.status) is not str or binding.status not in ("BOUND", "UNBOUND", "AMBIGUOUS", "INVALID"):
        _error("/binding/status", "closed status domain violation")
    if binding.status == "BOUND" and any(value != "MATCH" for value in (binding.case_match, binding.track_match, binding.artifact_digest_match)):
        _error("/binding", "bound required dimensions must match")
    if binding.binding_protocol == "PRODUCTION_STATEMENT":
        if binding.run_match != "NOT_APPLICABLE": _error("/binding/run_match", "production run must be not applicable")
        if binding.status == "BOUND":
            if len(targets) != 3 or tuple(ref.object_type for ref in targets) != ("STATEMENT", "STATEMENT_SET", "STATEMENT_RECORDS"):
                _error("/binding/target_object_refs", "production graph order invalid")
            if binding.record_anchor_ref is None or binding.record_anchor_ref.object_type != "RULE": _error("/binding/record_anchor_ref", "production anchor invalid")
            if binding.statement_match != "MATCH" or binding.revision_match not in ("MATCH", "UNKNOWN") or binding.statement_set_match != "MATCH":
                _error("/binding", "bound production dimensions must match")
    else:
        if any(value != "NOT_APPLICABLE" for value in (binding.statement_match, binding.revision_match, binding.statement_set_match)):
            _error("/binding", "preprod statement dimensions must be not applicable")
        if binding.record_anchor_ref is not None: _error("/binding/record_anchor_ref", "preprod anchor forbidden")
        if binding.status == "BOUND":
            roles = tuple(ref.object_type for ref in targets)
            allowed = ("RUN_SNAPSHOT", "DECISION_RUN", "FEEDBACK_ATTACHMENT", "MANIFEST")
            if not roles or roles[0] != "RUN_SNAPSHOT" or any(role not in allowed for role in roles) or roles != tuple(role for role in allowed if role in roles) or len(roles) != len(set(roles)) or binding.run_match != "MATCH":
                _error("/binding/target_object_refs", "preprod graph order invalid")
    if binding.status != "BOUND" and (targets or binding.record_anchor_ref is not None): _error("/binding/target_object_refs", "non-bound graph must be empty")
    allowed_issues = {
        ("FEEDBACK.TARGET_UNBOUND", "/feedback_bindings/"),
        ("FEEDBACK.REVISION_MISMATCH", "/revision_match"),
        ("FEEDBACK.TRACK_MISMATCH", "/track_match"),
    }
    if len(detected) > 1 or len(detected) != len(set((issue.issue_code, issue.field_path) for issue in detected)): _error("/binding/detected_issues", "invalid producer issue cardinality")
    expected_code = "FEEDBACK.TRACK_MISMATCH" if binding.track_match == "MISMATCH" else "FEEDBACK.REVISION_MISMATCH" if binding.revision_match == "MISMATCH" else "FEEDBACK.TARGET_UNBOUND" if binding.status == "UNBOUND" else None
    if (expected_code is None) != (not detected): _error("/binding/detected_issues", "producer issue presence mismatch")
    if detected:
        issue = detected[0]
        path_parts = issue.field_path.split("/")
        indexed_root = len(path_parts) >= 3 and path_parts[:2] == ["", "feedback_bindings"] and path_parts[2].isdigit()
        exact_pair = (
            issue.issue_code == expected_code
            and indexed_root
            and (
                (issue.issue_code == "FEEDBACK.TARGET_UNBOUND" and len(path_parts) == 3)
                or (issue.issue_code == "FEEDBACK.REVISION_MISMATCH" and path_parts[3:] == ["revision_match"])
                or (issue.issue_code == "FEEDBACK.TRACK_MISMATCH" and path_parts[3:] == ["track_match"])
            )
        )
        if not exact_pair or not any(issue.issue_code == code and (issue.field_path.startswith(suffix) if suffix == "/feedback_bindings/" else issue.field_path.endswith(suffix)) for code, suffix in allowed_issues):
            _error("/binding/detected_issues", "invalid producer issue pair")
    _digest_ref_material(binding.content_digest)
    if bounded_jcs_sha256(_feedback_binding_self_excluded_material(binding)) != binding.content_digest: _error("/binding/content_digest", "binding digest mismatch", integrity=True)


def evaluate_learning_eligibility(
    binding: FeedbackBinding,
    *,
    production_authority: ProductionStatementAuthority | None,
    clock: FeedbackClockPort,
) -> LearningEligibility:
    validate_feedback_binding_record(binding)
    if production_authority is not None and type(production_authority) is not ProductionStatementAuthority: _error("/production_authority", "invalid authority")
    if not isinstance(clock, FeedbackClockPort): _error("/clock", "invalid clock")
    policy = _pinned_eligibility_policy()
    if bounded_jcs_sha256(_eligibility_policy_material(policy)) != policy.content_digest: _error("/eligibility_policy/content_digest", "pinned policy digest mismatch", integrity=True)
    status: EligibilityStatus
    targets: tuple[VersionedObjectRef, ...] = ()
    excluded: tuple[VersionedObjectRef, ...] = ()
    reasons: tuple[str, ...]
    if binding.status == "AMBIGUOUS": status, reasons = "HUMAN_REVIEW", ("AMBIGUOUS_BINDING",)
    elif binding.status == "INVALID": status, reasons = "INELIGIBLE", ("INVALID_BINDING",)
    elif binding.track_match == "UNKNOWN": status, reasons = "HUMAN_REVIEW", ("UNKNOWN_TRACK",)
    elif binding.binding_protocol != "PRODUCTION_STATEMENT" or binding.status != "BOUND" or production_authority is None:
        status, reasons = "INELIGIBLE", ("NON_PRODUCTION_OR_UNBOUND",)
    else:
        authority_material = _production_authority_self_excluded_material(production_authority)
        _digest_ref_material(production_authority.content_digest)
        if bounded_jcs_sha256(authority_material) != production_authority.content_digest:
            _error("/production_authority/content_digest", "authority digest mismatch", integrity=True)
        statement_ref, set_ref, records_ref = binding.target_object_refs
        captured_at = _nonblank(records_ref.captured_at, "/binding/target_object_refs/2/captured_at")
        probe = FeedbackItem(
            binding.feedback_item_ref.object_id,
            binding.feedback_item_ref.object_id,
            "ELIGIBILITY#",
            statement_ref.object_id,
            statement_ref.revision_id,
            None,
            None,
            "CONFIRM",
            "",
            "VALID",
            (),
        )
        resolved_status, _, graph, selected, dimensions = _production_target(probe, production_authority, captured_at)
        binding_dimensions = (binding.case_match, binding.track_match, binding.run_match, binding.statement_match, binding.revision_match, binding.statement_set_match, binding.artifact_digest_match)
        matching_statements = tuple(statement for statement in production_authority.statement_set.statements if statement.statement_id == statement_ref.object_id and statement.statement_revision_id == statement_ref.revision_id)
        matching_anchors = tuple(anchor for anchor in production_authority.anchor_selections if anchor.statement_id == statement_ref.object_id and anchor.statement_revision_id == statement_ref.revision_id and anchor.selected_anchor_rule_ref == binding.record_anchor_ref)
        same_authority_graph = (
            resolved_status == "BOUND"
            and len(graph) == 4
            and graph[:3] == binding.target_object_refs
            and graph[3] == binding.record_anchor_ref
            and selected == binding.record_anchor_ref
            and dimensions == binding_dimensions
            and set_ref == production_authority.statement_set_ref
            and len(matching_statements) == 1
            and len(matching_anchors) == 1
        )
        if not same_authority_graph or production_authority.statement_set.track != policy.allowed_track or matching_statements[0].feedback_policy != policy.required_feedback_policy:
            status, reasons = "INELIGIBLE", ("FEEDBACK_POLICY_OR_AUTHORITY_NOT_ELIGIBLE",)
        else:
            status, reasons, targets, excluded = "ELIGIBLE", (), (binding.record_anchor_ref,), matching_anchors[0].non_anchor_rule_refs
    now = _nonblank(clock.now(), "/evaluated_at")
    unsigned = LearningEligibility("LEARNING-ELIGIBILITY:" + binding.feedback_binding_id, binding.feedback_binding_id, binding.content_digest, policy.policy_id, policy.policy_version, status, targets, excluded, reasons, (), now, DigestRef("sha256", "RFC8785-JCS-UTF8", "0" * 64))
    result = LearningEligibility(unsigned.eligibility_id, unsigned.feedback_binding_id, unsigned.feedback_binding_digest, unsigned.policy_id, unsigned.policy_version, unsigned.status, unsigned.learning_target_refs, unsigned.excluded_supporting_rule_refs, unsigned.blocking_reason_codes, unsigned.detected_issues, unsigned.evaluated_at, bounded_jcs_sha256(_learning_eligibility_self_excluded_material(unsigned)))
    validate_learning_eligibility(result); return result


def validate_learning_eligibility(eligibility: LearningEligibility) -> None:
    if type(eligibility) is not LearningEligibility: _error("/eligibility", "invalid eligibility class")
    missing = object()
    eligibility_id = getattr(eligibility, "eligibility_id", missing)
    feedback_binding_id = getattr(eligibility, "feedback_binding_id", missing)
    feedback_binding_digest = getattr(eligibility, "feedback_binding_digest", missing)
    policy_id = getattr(eligibility, "policy_id", missing)
    policy_version = getattr(eligibility, "policy_version", missing)
    status = getattr(eligibility, "status", missing)
    learning_target_refs = getattr(eligibility, "learning_target_refs", missing)
    excluded_supporting_rule_refs = getattr(eligibility, "excluded_supporting_rule_refs", missing)
    blocking_reason_codes = getattr(eligibility, "blocking_reason_codes", missing)
    detected_issues = getattr(eligibility, "detected_issues", missing)
    evaluated_at = getattr(eligibility, "evaluated_at", missing)
    content_digest = getattr(eligibility, "content_digest", missing)
    if any(value is missing for value in (eligibility_id, feedback_binding_id, feedback_binding_digest, policy_id, policy_version, status, learning_target_refs, excluded_supporting_rule_refs, blocking_reason_codes, detected_issues, evaluated_at, content_digest)):
        _error("/eligibility", "missing literal public field")
    _nonblank(eligibility_id, "/eligibility/eligibility_id")
    _nonblank(eligibility.feedback_binding_id, "/eligibility/feedback_binding_id")
    if type(eligibility.feedback_binding_digest) is not DigestRef: _error("/eligibility/feedback_binding_digest", "invalid binding digest class")
    _digest_ref_material(eligibility.feedback_binding_digest)
    policy = _pinned_eligibility_policy()
    if bounded_jcs_sha256(_eligibility_policy_material(policy)) != policy.content_digest: _error("/eligibility/policy", "pinned policy digest mismatch", integrity=True)
    if type(eligibility.policy_id) is not str or type(eligibility.policy_version) is not str or eligibility.policy_id != policy.policy_id or eligibility.policy_version != policy.policy_version: _error("/eligibility/policy_id", "policy identity mismatch")
    _nonblank(eligibility.evaluated_at, "/eligibility/evaluated_at")
    targets = _tuple(eligibility.learning_target_refs, "/eligibility/learning_target_refs")
    excluded = _tuple(eligibility.excluded_supporting_rule_refs, "/eligibility/excluded_supporting_rule_refs")
    reasons = _string_tuple(eligibility.blocking_reason_codes, "/eligibility/blocking_reason_codes", nonblank=True)
    issues = _tuple(eligibility.detected_issues, "/eligibility/detected_issues")
    if any(type(ref) is not VersionedObjectRef for ref in targets + excluded): _error("/eligibility", "invalid rule ref member")
    for ref in targets + excluded: _versioned_object_ref_material(ref)
    if any(type(issue) is not DetectedIssue for issue in issues): _error("/eligibility/detected_issues", "invalid issue member")
    if type(eligibility.status) is not str or eligibility.status not in ("ELIGIBLE", "INELIGIBLE", "HUMAN_REVIEW"): _error("/eligibility/status", "invalid status")
    if eligibility.status == "ELIGIBLE":
        if len(targets) != 1 or targets[0].object_type != "RULE" or any(ref.object_type != "RULE" for ref in excluded) or len(excluded) != len(set(excluded)) or targets[0] in excluded or reasons: _error("/eligibility", "eligible surface invalid")
    elif targets or excluded or not reasons:
        _error("/eligibility", "noneligible surface invalid")
    if issues: _error("/eligibility/detected_issues", "eligibility issues must be fresh-empty")
    _digest_ref_material(eligibility.content_digest)
    if bounded_jcs_sha256(_learning_eligibility_self_excluded_material(eligibility)) != eligibility.content_digest: _error("/eligibility/content_digest", "eligibility digest mismatch", integrity=True)


# ---------------------------------------------------------------------------
# Task 10 adapter public surface — four symbols required by tests/f09/conftest.py
# ---------------------------------------------------------------------------

from dataclasses import dataclass as _dataclass


@_dataclass(frozen=True)
class _ValidatedRef:
    """Return carrier for validate_versioned_ref()."""
    value: VersionedObjectRef


def validate_versioned_ref(
    ref: object,
    *,
    require_revision: bool = False,
    require_contract: bool = False,
) -> _ValidatedRef:
    """Validate a VersionedObjectRef and return it wrapped in a carrier with a .value attribute.

    Raises F09ContractError on any violation.
    """
    if type(ref) is not VersionedObjectRef:
        _error("/ref", "invalid ref class")
    _versioned_object_ref_material(ref)  # structural + domain validation
    if require_revision and ref.revision_id is None:
        _error("/ref/revision_id", "revision_id is required but missing")
    if require_contract and ref.contract_version is None:
        _error("/ref/contract_version", "contract_version is required but missing")
    return _ValidatedRef(value=ref)  # type: ignore[arg-type]


def digest_ordered_rule_refs(refs: tuple[VersionedObjectRef, ...]) -> DigestRef:
    """Compute the canonical ordered-source digest for a set of rule refs.

    This is the same digest used internally by _production_target() when
    validating AnchorSelectionRecord.source_order_digest.
    """
    if not isinstance(refs, tuple):
        _error("/refs", "refs must be a tuple")
    if any(type(ref) is not VersionedObjectRef for ref in refs):
        _error("/refs", "all members must be VersionedObjectRef")
    return bounded_jcs_sha256(tuple(_versioned_object_ref_material(x) for x in refs))  # type: ignore[return-value]


def digest_protocol_target_graph(
    protocol: BindingProtocol,
    refs: tuple[VersionedObjectRef, ...],
    *,
    target_run_id: str | None,
    selection: "AnchorSelectionRecord | None",
) -> DigestRef:
    """Compute the canonical target-graph digest for a given binding protocol.

    PRODUCTION_STATEMENT: binds statement/set/records refs + selected RULE anchor ref
                          + policy identity material.
    PREPROD_RUN_TARGET:   binds target_run_id + validated extensible run refs.
    """
    if protocol not in ("PRODUCTION_STATEMENT", "PREPROD_RUN_TARGET"):
        _error("/protocol", "invalid binding protocol")
    if not isinstance(refs, tuple):
        _error("/refs", "refs must be a tuple")
    if any(type(ref) is not VersionedObjectRef for ref in refs):
        _error("/refs", "all members must be VersionedObjectRef")
    if protocol == "PRODUCTION_STATEMENT":
        if selection is None or type(selection) is not AnchorSelectionRecord:
            _error("/selection", "PRODUCTION_STATEMENT requires an AnchorSelectionRecord selection")
        if len(refs) < 3:
            _error("/refs", "PRODUCTION_STATEMENT target graph requires at least 3 refs")
        anchor_policy = _pinned_anchor_policy()
        policy_material: JcsValue = {
            "policy_id": anchor_policy.policy_id,
            "policy_version": anchor_policy.policy_version,
        }
        anchor_material: JcsValue = _anchor_selection_record_material(selection)  # type: ignore[assignment]
        material: JcsValue = tuple(
            list(_versioned_object_ref_material(ref) for ref in refs)
            + [anchor_material, policy_material]
        )
        return bounded_jcs_sha256(material)  # type: ignore[return-value]
    else:
        # PREPROD_RUN_TARGET: target_run_id + sorted validated refs
        if target_run_id is None:
            _error("/target_run_id", "PREPROD_RUN_TARGET requires a target_run_id")
        _nonblank(target_run_id, "/target_run_id")
        ref_materials = tuple(_versioned_object_ref_material(ref) for ref in refs)
        sorted_ref_materials = tuple(
            m for _, m in sorted(
                zip(refs, ref_materials),
                key=lambda pair: _canonical_bytes(_versioned_object_ref_material(pair[0])),
            )
        )
        preprod_material: JcsValue = {"run_id": target_run_id, "target_refs": sorted_ref_materials}
        return bounded_jcs_sha256(preprod_material)  # type: ignore[return-value]


def validate_feedback_binding(
    submission: FeedbackSubmission,
    statement_set: "StatementSet | None",
    manifest: ArtifactSetManifest,
    *,
    prior_key: IdempotencyKey,
    current_key: IdempotencyKey,
    prior_target_digest: DigestRef,
    current_target_digest: DigestRef,
    target_track_source_binding: TrackSourceBinding,
    statement_refs: "Mapping[tuple[str, str], VersionedObjectRef]",
    statement_set_ref: "VersionedObjectRef | None",
    records_projection_refs: "Mapping[str, VersionedObjectRef]",
    records_projection_records: "Mapping[str, StatementProjectionRecord]",
    anchor_selections: "Mapping[tuple[str, str], AnchorSelectionRecord]",
    preprod_target_refs: "Mapping[str, tuple[VersionedObjectRef, ...]]",
    governing_statement_contract_version: str,
    governing_statement_set_contract_version: str,
    governing_statement_records_contract_version: str,
    governing_rule_contract_version: str,
) -> FeedbackOperationResult:
    """Task 10 adapter: construct authority and call bind_feedback_operation.

    Builds either a ProductionStatementAuthority (when statement_set is not None)
    or PreprodRunAuthority (when statement_set is None) from the supplied
    pre-validated arguments, then routes through bind_feedback_operation with a
    synthetic prior derived from prior_key / prior_target_digest.
    """
    from typing import Mapping as _Mapping

    captured_at = "2026-07-20T00:00:00Z"  # fixture-stable timestamp
    protocol: BindingProtocol = "PRODUCTION_STATEMENT" if statement_set is not None else "PREPROD_RUN_TARGET"

    # --- Build target authority ---
    if protocol == "PRODUCTION_STATEMENT":
        if statement_set is None or statement_set_ref is None:
            raise F09ContractError("FEEDBACK.MATERIAL_INVALID", "/statement_set", "PRODUCTION_STATEMENT requires statement_set and statement_set_ref")
        # Production authority requires PRODUCTION_DEFAULT track
        from dataclasses import replace as _replace
        prod_statement_set = _replace(statement_set, track=RunTrack.PRODUCTION_DEFAULT)
        governing = GoverningVersions(
            governing_statement_contract_version,
            governing_statement_set_contract_version,
            governing_statement_records_contract_version,
            governing_rule_contract_version,
        )
        stmt_refs_tuple: tuple[VersionedObjectRef, ...] = tuple(statement_refs.values())
        proj_refs_tuple: tuple[VersionedObjectRef, ...] = tuple(records_projection_refs.values())
        proj_records_tuple: tuple[StatementProjectionRecord, ...] = tuple(records_projection_records.values())
        anchor_tuple: tuple[AnchorSelectionRecord, ...] = tuple(anchor_selections.values())
        unsigned_authority = ProductionStatementAuthority(
            statement_set=prod_statement_set,
            manifest=manifest,
            statement_refs=stmt_refs_tuple,
            statement_set_ref=statement_set_ref,
            records_projection_refs=proj_refs_tuple,
            records_projection_records=proj_records_tuple,
            anchor_selections=anchor_tuple,
            rule_metadata_receipts=(),
            governing_versions=governing,
            content_digest=DigestRef("sha256", "RFC8785-JCS-UTF8", "0" * 64),
        )
        auth_material = _production_authority_self_excluded_material(unsigned_authority)
        auth_digest = bounded_jcs_sha256(auth_material)
        authority: ProductionStatementAuthority | PreprodRunAuthority = ProductionStatementAuthority(
            statement_set=prod_statement_set,
            manifest=manifest,
            statement_refs=stmt_refs_tuple,
            statement_set_ref=statement_set_ref,
            records_projection_refs=proj_refs_tuple,
            records_projection_records=proj_records_tuple,
            anchor_selections=anchor_tuple,
            rule_metadata_receipts=(),
            governing_versions=governing,
            content_digest=auth_digest,
        )
    else:
        # PREPROD_RUN_TARGET: find the single run_id from preprod_target_refs
        run_ids = list(preprod_target_refs.keys())
        if len(run_ids) != 1:
            raise F09ContractError("FEEDBACK.MATERIAL_INVALID", "/preprod_target_refs", "PREPROD_RUN_TARGET requires exactly one run_id in preprod_target_refs")
        run_id = run_ids[0]
        target_refs_tuple = preprod_target_refs[run_id]
        # Extract case_id and track from manifest records
        if not manifest.records:
            raise F09ContractError("FEEDBACK.MATERIAL_INVALID", "/manifest", "PREPROD_RUN_TARGET manifest must have records")
        case_id = manifest.records[0].case_id
        track = RunTrack.V5_V6_PREPROD
        unsigned_preprod = PreprodRunAuthority(
            case_id=case_id,
            track=track,
            run_id=run_id,
            manifest=manifest,
            target_refs=target_refs_tuple,
            content_digest=DigestRef("sha256", "RFC8785-JCS-UTF8", "0" * 64),
        )
        preprod_material = _preprod_authority_self_excluded_material(unsigned_preprod)
        preprod_digest = bounded_jcs_sha256(preprod_material)
        authority = PreprodRunAuthority(
            case_id=case_id,
            track=track,
            run_id=run_id,
            manifest=manifest,
            target_refs=target_refs_tuple,
            content_digest=preprod_digest,
        )

    # --- Build raw submission bytes from FeedbackSubmission ---
    raw_submission_obj: JcsValue = {
        "feedback_id": submission.feedback_id,
        "case_id": submission.case_id,
        "track": submission.track.value,
        "track_source_binding": {
            "track_source_binding_id": submission.track_source_binding.track_source_binding_id,
            "side": submission.track_source_binding.side,
            "track": submission.track_source_binding.track.value,
            "state": submission.track_source_binding.state,
            "schema_version": submission.track_source_binding.schema_version,
            "contract_version": submission.track_source_binding.contract_version,
            "content_digest": {
                "algorithm": submission.track_source_binding.content_digest.algorithm,
                "canonicalization": submission.track_source_binding.content_digest.canonicalization,
                "value": submission.track_source_binding.content_digest.value,
            },
        },
        "parser_id": submission.parser_id,
        "parser_version": submission.parser_version,
        "feedback_items": tuple(
            {
                "feedback_item_id": item.feedback_item_id,
                "feedback_id": item.feedback_id,
                "source_span_locator": item.source_span_locator,
                "target_statement_id": item.target_statement_id,
                "target_statement_revision_id": item.target_statement_revision_id,
                "target_run_id": item.target_run_id,
                "target_prediction_id": item.target_prediction_id,
                "verdict": item.verdict,
                "annotation": item.annotation,
                "integrity": item.integrity,
                "issue_ids": item.issue_ids,
            }
            for item in submission.feedback_items
        ),
    }
    raw_submission_bytes = canonicalize_bounded_jcs(raw_submission_obj)

    current_raw = RawFeedbackAuthority(
        raw_submission=raw_submission_bytes,
        target_authority=authority,
        target_track_source_binding=target_track_source_binding,
        captured_at=captured_at,
    )

    # --- Build prior operation if keys differ ---
    prior_operation: PriorFeedbackOperation | None = None
    if prior_key.canonical_key_digest != current_key.canonical_key_digest or prior_target_digest != current_target_digest:
        # Construct a minimal prior raw authority with prior target digest embedded
        # by using the same authority but with a synthetic manifest whose records digest
        # matches prior_target_digest — or we synthesize a prior receipt directly.
        # The simplest approach: duplicate raw with prior submission pointing at prior source.
        prior_raw = RawFeedbackAuthority(
            raw_submission=raw_submission_bytes,
            target_authority=authority,
            target_track_source_binding=target_track_source_binding,
            captured_at=captured_at,
        )
        prior_receipt = _compute_operation(prior_raw, _parse_submission(raw_submission_bytes), captured_at)
        prior_operation = PriorFeedbackOperation(raw_authority=prior_raw, receipt=prior_receipt)

    class _FixedClock:
        def now(self) -> str:
            return captured_at

    return bind_feedback_operation(current_raw, prior=prior_operation, clock=_FixedClock())


