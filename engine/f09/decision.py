from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from typing import Literal, Mapping, TypeAlias, Union

from engine.f09.canonical_json import bounded_jcs_sha256
from engine.f09.contracts import (
    ContractIntegrityResult,
    ContractVersionRef,
    DecisionAction,
    DigestRef,
    EvidenceRelation,
    EvidenceTrack,
    FieldEvaluatorState,
    FunctionCandidate,
    FrozenCardFieldRef,
    FrozenConstraintRef,
    FrozenContractReadPort,
    FrozenDeclarationBinding,
    FrozenFieldObservation,
    FrozenGateEvaluationBinding,
    FrozenParticipationRoleBinding,
    FrozenRootTimingOutcomeBinding,
    FunctionId,
    GateEvidenceState,
    NormalizedEvidenceReadPort,
    ResolvedDeclarationBinding,
    SourceFieldState,
    thaw_frozen_json,
)
from engine.f09.evidence import EvidenceRecord, IntegrityState, NormalizedEvidencePackage

StructuralReadinessState: TypeAlias = Literal["READY", "INCOMPLETE", "DISPUTED", "BLOCKED"]
ConstraintCheckState: TypeAlias = Literal["SATISFIED", "VIOLATED", "UNKNOWN", "NOT_APPLICABLE"]
ParticipationRole: TypeAlias = Literal[
    "SINGLE_SCHOOL_COMPLETE_NATAL_CHAIN",
    "DAIYUN_STAGE_EFFECT",
    "LIUNIAN_SPECIFIC_EVENT_TRIGGER",
    "REAL_WORLD_FUNCTION_GATE",
    "BREAK_CONDITION_OR_VALID_FALSIFIER",
    "SOURCE_GATE",
]
ParticipationState: TypeAlias = Literal["SATISFIED", "MISSING", "CONFLICT", "UNKNOWN", "NOT_APPLICABLE"]
ParticipationAuthorityBindingId: TypeAlias = tuple[ParticipationRole, str]
RootTimingAuthorityBindingId: TypeAlias = tuple[str, str]
BasisRecordIds: TypeAlias = tuple[str, ...]
FieldPathIssueRef: TypeAlias = str
CompetitionDimension: TypeAlias = Literal[
    "primary_responsibility",
    "primary_action",
    "direct_object",
    "primary_deliverable",
    "primary_uncertainty",
    "stable_input",
    "strongest_competing_explanation",
]
CompetitionDimensionState: TypeAlias = Literal["UNOBSERVED", "PARTIAL", "READY_FOR_DECISION", "DISPUTED"]

SIX_MEMBERS = ("RESOURCE", "OBJECT", "ALLOCATION", "RISK", "ATTRIBUTION", "TENSE")
PARTICIPATION_ROLES: tuple[ParticipationRole, ...] = (
    "SINGLE_SCHOOL_COMPLETE_NATAL_CHAIN",
    "DAIYUN_STAGE_EFFECT",
    "LIUNIAN_SPECIFIC_EVENT_TRIGGER",
    "REAL_WORLD_FUNCTION_GATE",
    "BREAK_CONDITION_OR_VALID_FALSIFIER",
    "SOURCE_GATE",
)
REGISTERED_REASON_CODES = frozenset(
    {
        "INTEGRITY.PACKAGE_NOT_CONSUMABLE", "INTEGRITY.REFERENCE_BROKEN",
        "INTEGRITY.TRACK_CONTAMINATION", "INTEGRITY.CARD_BINDING_INVALID",
        "INTEGRITY.CONTRACT_VERSION_MISMATCH", "FIELD.ABSENT",
        "FIELD.EXPLICIT_NULL_PRESERVED", "FIELD.UNRESOLVED_PRESERVED",
        "FIELD.NULL_AND_UNRESOLVED_PRESERVED", "FIELD.EVALUATOR_UNKNOWN",
        "FIELD.CONFLICTING_VALUES", "GATE.RECORD_MISSING",
        "GATE.MEMBER_DECLARATION_INVALID", "GATE.MEMBER_CARDINALITY_INVALID",
        "GATE.MEMBER_BINDING_MISMATCH", "GATE.PERMUTATION_BINDING_INVALID",
        "GATE.EVIDENCE_MISSING", "GATE.EVIDENCE_CONFLICT", "GATE.STATE_UNKNOWN",
        "GATE.REALITY_FACT_REFERENCE_REQUIRED", "COMPETITION.DIMENSION_UNOBSERVED",
        "COMPETITION.DIMENSION_PARTIAL", "COMPETITION.DIMENSION_DISPUTED",
        "COMPETITION.DISPOSITION_UNRESOLVED", "COUNTEREVIDENCE.REFERENCE_PRESENT",
        "COUNTEREVIDENCE.RELATION_MISSING", "ROOT.ENTRY_MISSING",
        "ROOT.SOURCE_TRACK_INVALID", "TIMING.ENTRY_MISSING",
        "TIMING.ROOT_REFERENCE_BROKEN", "TIMING.CONSTRAINT_UNKNOWN",
        "TIMING.CONSTRAINT_VIOLATED", "ACTION.PAYLOAD_TYPE_MISMATCH",
        "ACTION.BASIS_MISSING", "ACTION.BLOCKING_ISSUE_PRESENT",
        "ACTION.QUESTION_NOT_BOUND_TO_ISSUE", "ACTION.REVIEW_SCOPE_MISSING",
        "ADAPTER.SOURCE_SEMANTICS_UNMAPPABLE", "ADAPTER.LEGACY_DECISION_NOT_REUSED",
        "ADAPTER.CONFIDENCE_NOT_RECOMPUTED",
    }
)


@dataclass(frozen=True)
class GateInputState:
    allocation_state: str; risk_state: str; reality_state: str; attribution_state: str; source_state: str; temporal_state: str
    risk_reason_codes: tuple[str, ...]; allocation_reason_codes: tuple[str, ...]; member_ids: tuple[str, ...]
    declared_member_ids: tuple[str, ...]; gate_definition_ref: str; record_gate_definition_refs: tuple[str, ...]
    evaluation_binding_digests: tuple[str, ...]; supporting_evidence_tracks: tuple[str, ...]; path_complete: bool


@dataclass(frozen=True)
class DeclarationInputState:
    precision_presence: str; precision_value: str | None; precision_unresolved: bool; precision_type: str
    precision_digest: str; precision_contract_version: str; validation_type: str; validation_digest: str
    attempted_digest: str | None; identity_complete: bool; statement_precision_digest: str; trace_precision_digest: str


@dataclass(frozen=True)
class DecisionInputState:
    selected_action: str; payload_type: str; payload_issue_ids: tuple[str, ...]; question_paths: tuple[str, ...]
    basis_gate_ids: tuple[str, ...]; basis_participation_ids: tuple[str, ...]; disposition_refs: tuple[str, ...]
    candidate_ids: tuple[str, ...]; dispositions: tuple[str, ...]; f08_runtime_objects: tuple[str, ...]
    require_two_candidates: bool; consequence_only: bool


@dataclass(frozen=True)
class ParticipationInputState:
    role_ids: tuple[str, ...]
    role_authority_binding_ids: tuple[ParticipationAuthorityBindingId, ...]
    scenario_id: str


@dataclass(frozen=True)
class RootTimingInputState:
    root_state: str; root_reason_code: str | None; root_issue_path: str | None
    timing_state: str; timing_reason_code: str | None; timing_issue_path: str | None; timing_rewrites_root: bool
    authority_binding_ids: tuple[RootTimingAuthorityBindingId, ...]


@dataclass(frozen=True)
class SourceInputState:
    locator_available: bool; reality_track: str; state_object_id: str; state_pointer: str; state_fields: tuple[str, ...]
    event_object_id: str; event_pointer: str; event_fields: tuple[str, ...]; outcome_fields: tuple[str, ...]
    snapshot_id: str; snapshot_schema_version: str; contract_version: str; content_digest: str; captured_at: str
    payload_digest: str; source_field_present: bool; source_kind: str; canonical_nested_binding: bool


@dataclass(frozen=True)
class GateEvaluationInput:
    gate: GateInputState
    declarations: DeclarationInputState
    participation: ParticipationInputState
    source: SourceInputState


@dataclass(frozen=True)
class CompetitionInput:
    decision: DecisionInputState
    source: SourceInputState


@dataclass(frozen=True)
class RootInput:
    root_timing: RootTimingInputState
    source: SourceInputState


@dataclass(frozen=True)
class TimingInput:
    root_timing: RootTimingInputState
    source: SourceInputState


@dataclass(frozen=True)
class PackageConsumptionCheck:
    package_id: str
    pi210_integrity: IntegrityState
    contract_integrity: ContractIntegrityResult
    candidate_reference_integrity: Literal["VALID", "INVALID"]
    evidence_reference_integrity: Literal["VALID", "INVALID"]
    relation_reference_integrity: Literal["VALID", "INVALID"]
    consumable: bool
    blocking_issue_ids: tuple[str, ...]


@dataclass(frozen=True)
class GateEvaluationBindingRef:
    binding_id: str
    binding_schema_version: str
    binding_version: str
    canonical_record_digest: DigestRef
    immutable_source_digest: DigestRef


@dataclass(frozen=True)
class GateDeclaredMember:
    declared_member_id: str
    declared_member_value: object
    gate_definition_ref: FrozenCardFieldRef


@dataclass(frozen=True)
class GateMemberDeclarationSet:
    declaration_set_id: str
    declaration_source_id: str
    declaration_schema_version: str
    declaration_version: str
    content_digest: DigestRef
    members: tuple[GateDeclaredMember, ...]


@dataclass(frozen=True)
class GateEvaluationRecord:
    gate_record_id: str
    candidate_id: str
    gate_definition_ref: FrozenCardFieldRef
    declared_member_id: str
    evaluation_binding_ref: GateEvaluationBindingRef
    state: GateEvidenceState
    supporting_evidence_ids: tuple[str, ...]
    counterevidence_ids: tuple[str, ...]
    conflict_relation_ids: tuple[str, ...]
    missing_paths: tuple[FieldPathIssueRef, ...]
    conflict_paths: tuple[FieldPathIssueRef, ...]
    unknown_paths: tuple[FieldPathIssueRef, ...]
    reason_codes: tuple[str, ...]
    source_decision_ref: str | None


@dataclass(frozen=True)
class GateEvaluationSet:
    candidate_id: str
    function_id: FunctionId
    gate_definition_refs: tuple[FrozenCardFieldRef, ...]
    member_declaration_set: GateMemberDeclarationSet
    records: tuple[GateEvaluationRecord, ...]
    set_state: StructuralReadinessState
    issue_ids: tuple[str, ...]


@dataclass(frozen=True)
class ParticipationRoleRecord:
    participation_record_id: str
    participation_set_id: str
    role: ParticipationRole
    authority_binding_id: str
    frozen_definition_refs: tuple[FrozenCardFieldRef, ...]
    state: ParticipationState
    supporting_evidence_ids: tuple[str, ...]
    counterevidence_ids: tuple[str, ...]
    missing_issue_ids: tuple[str, ...]
    conflict_issue_ids: tuple[str, ...]
    unknown_issue_ids: tuple[str, ...]
    relation_ids: tuple[str, ...]
    source_decision_ref: str


@dataclass(frozen=True)
class MinimumSufficientParticipationSet:
    participation_set_id: str
    candidate_id: str
    function_id: FunctionId
    required_roles: tuple[ParticipationRole, ...]
    role_records: tuple[ParticipationRoleRecord, ...]
    structural_state: StructuralReadinessState
    issue_ids: tuple[str, ...]


@dataclass(frozen=True)
class CompetitionDimensionEvaluation:
    dimension: CompetitionDimension
    candidate_evidence: Mapping[str, tuple[str, ...]]
    candidate_counterevidence: Mapping[str, tuple[str, ...]]
    comparison_relation_ids: tuple[str, ...]
    state: CompetitionDimensionState
    missing_paths: tuple[FieldPathIssueRef, ...]
    conflict_paths: tuple[FieldPathIssueRef, ...]
    unknown_paths: tuple[FieldPathIssueRef, ...]


@dataclass(frozen=True)
class CounterevidenceReference:
    reference_id: str
    candidate_id: str
    evidence_id: str
    relation_ids: tuple[str, ...]
    affected_gate_record_ids: tuple[str, ...]
    affected_dimension_records: tuple[str, ...]
    source_track: EvidenceTrack
    source_locator: str


@dataclass(frozen=True)
class CandidateDisposition:
    candidate_id: str
    disposition: Literal["INCLUDED", "CONDITIONAL", "EXCLUDED", "UNRESOLVED"]
    source_decision_ref: str
    supporting_record_ids: tuple[str, ...]
    limiting_record_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class CompetitionSet:
    competition_id: str
    candidate_ids: tuple[str, ...]
    relation_ids: tuple[str, ...]
    dimension_records: tuple[CompetitionDimensionEvaluation, ...]
    counterevidence_records: tuple[CounterevidenceReference, ...]
    candidate_dispositions: tuple[CandidateDisposition, ...]
    structural_state: StructuralReadinessState
    issue_ids: tuple[str, ...]


@dataclass(frozen=True)
class RootLedgerEntry:
    root_evidence_id: str
    vocabulary_scope: Literal["COMMON", "CARD_SPECIFIC"]
    label: str
    card_id: FunctionId | None
    object_refs: tuple[str, ...]
    rationale_source_refs: tuple[str, ...]
    source_track: Literal["CHART_STRUCTURE"]


@dataclass(frozen=True)
class RootConstraintLedger:
    candidate_id: str
    root_entries: tuple[RootLedgerEntry, ...]
    issue_ids: tuple[str, ...]


@dataclass(frozen=True)
class TimingLedgerEntry:
    timing_evidence_id: str
    completion_mode: Literal["ACTIVATE_EXISTING", "COMPLETE_LATENT", "REPAIR_DEFECT", "TEMPORARY_SUBSTITUTE", "INVALID_COMPLETION"]
    target_root_evidence_id: str | None
    timing_object_refs: tuple[str, ...]
    source_track: Literal["CHART_STRUCTURE"]


@dataclass(frozen=True)
class TimingConstraintLedger:
    candidate_id: str
    timing_entries: tuple[TimingLedgerEntry, ...]
    issue_ids: tuple[str, ...]


@dataclass(frozen=True)
class RootTimingConstraintCheck:
    check_id: str
    authority_binding_id: str
    constraint_ref: FrozenConstraintRef
    root_entry_ids: tuple[str, ...]
    timing_entry_ids: tuple[str, ...]
    state: ConstraintCheckState
    source_decision_ref: str
    missing_paths: tuple[FieldPathIssueRef, ...]
    conflict_paths: tuple[FieldPathIssueRef, ...]
    unknown_paths: tuple[FieldPathIssueRef, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class RootTimingConstraintSet:
    candidate_id: str
    checks: tuple[RootTimingConstraintCheck, ...]
    structural_state: StructuralReadinessState
    issue_ids: tuple[str, ...]


@dataclass(frozen=True)
class FieldPathIssue:
    issue_id: str
    issue_class: Literal["MISSING", "CONFLICT", "UNKNOWN"]
    severity: Literal["INFO", "BLOCKING"]
    owner_type: Literal["PACKAGE", "CANDIDATE", "GATE", "COMPETITION_DIMENSION", "ROOT_ENTRY", "TIMING_ENTRY", "ROOT_TIMING_CHECK", "ACTION"]
    owner_id: str
    source_object_type: str
    source_object_id: str
    path_dialect: Literal["JSON_POINTER"]
    field_path: str
    source_state: SourceFieldState
    evaluator_state: FieldEvaluatorState
    evidence_ids: tuple[str, ...]
    relation_ids: tuple[str, ...]
    frozen_field_refs: tuple[FrozenCardFieldRef, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class OutputPayload:
    included_candidate_ids: tuple[str, ...]
    disposition_refs: tuple[str, ...]
    scope_refs: tuple[str, ...]


@dataclass(frozen=True)
class ConditionalPayload:
    included_candidate_ids: tuple[str, ...]
    disposition_refs: tuple[str, ...]
    condition_refs: tuple[str, ...]
    unresolved_issue_ids: tuple[str, ...]
    scope_refs: tuple[str, ...]


@dataclass(frozen=True)
class QuestionRequest:
    question_id: str
    target_issue_ids: tuple[str, ...]
    requested_field_paths: tuple[str, ...]
    expected_answer_shape: str


@dataclass(frozen=True)
class AskPayload:
    question_requests: tuple[QuestionRequest, ...]
    unresolved_issue_ids: tuple[str, ...]
    resume_token: str


@dataclass(frozen=True)
class AbstainPayload:
    abstained_candidate_ids: tuple[str, ...]
    blocking_issue_ids: tuple[str, ...]
    abstention_scope: str


@dataclass(frozen=True)
class HumanReviewPayload:
    review_case_id: str
    review_issue_ids: tuple[str, ...]
    review_record_ids: tuple[str, ...]
    requested_review_scope: str


DecisionPayload: TypeAlias = Union[OutputPayload, ConditionalPayload, AskPayload, AbstainPayload, HumanReviewPayload]


@dataclass(frozen=True)
class DecisionActionEnvelope:
    action_id: str
    selected_action: DecisionAction
    subject_candidate_ids: tuple[str, ...]
    payload: DecisionPayload
    basis_record_ids: BasisRecordIds
    blocking_issue_ids: tuple[str, ...]
    nonblocking_issue_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    source_decision_refs: tuple[str, ...]
    output_precision_binding: FrozenDeclarationBinding
    validation_plan_binding: FrozenDeclarationBinding
    structural_validity: Literal["VALID", "INVALID"]
    validation_errors: tuple[str, ...]


@dataclass(frozen=True)
class DecisionEvaluationResult:
    result_id: str
    request_id: str
    package_id: str
    contract_ref: ContractVersionRef
    consumption_check: PackageConsumptionCheck
    gate_sets: tuple[GateEvaluationSet, ...]
    participation_sets: tuple[MinimumSufficientParticipationSet, ...]
    competition_sets: tuple[CompetitionSet, ...]
    root_ledgers: tuple[RootConstraintLedger, ...]
    timing_ledgers: tuple[TimingConstraintLedger, ...]
    root_timing_checks: tuple[RootTimingConstraintSet, ...]
    issues: tuple[FieldPathIssue, ...]
    action_envelope: DecisionActionEnvelope
    produced_at: str


def _plain(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, DigestRef):
        return {"algorithm": value.algorithm, "canonicalization": value.canonicalization, "value": value.value}
    if is_dataclass(value):
        return {key: _plain(item) for key, item in asdict(value).items()}
    if type(value) is dict:
        return {key: _plain(item) for key, item in value.items()}
    if type(value) in (tuple, list):
        return tuple(_plain(item) for item in value)
    return value


def _digest(value: object) -> DigestRef:
    return bounded_jcs_sha256(_plain(value))


def _digest_from_text(value: str) -> DigestRef:
    if len(value) == 64 and all(char in "0123456789abcdef" for char in value):
        return DigestRef("sha256", "RFC8785-JCS-UTF8", value)
    return _digest(value)


def derive_member_id(member_name: str, declaration_version: str, declaration_digest: DigestRef) -> str:
    identity = {"member_name": member_name, "declaration_version": declaration_version, "declaration_digest": _plain(declaration_digest)}
    return f"F09-MEMBER-{_digest(identity).value[:24]}"


def _record_payload(record: GateEvaluationRecord) -> dict[str, object]:
    return {
        "candidate_id": record.candidate_id,
        "gate_definition_ref": _plain(record.gate_definition_ref),
        "declared_member_id": record.declared_member_id,
        "state": record.state.value,
        "supporting_evidence_ids": record.supporting_evidence_ids,
        "counterevidence_ids": record.counterevidence_ids,
        "conflict_relation_ids": record.conflict_relation_ids,
        "missing_paths": record.missing_paths,
        "conflict_paths": record.conflict_paths,
        "unknown_paths": record.unknown_paths,
        "reason_codes": record.reason_codes,
        "source_decision_ref": record.source_decision_ref,
    }


def record_digest(record: GateEvaluationRecord) -> DigestRef:
    return _digest(_record_payload(record))


def _state_for_member(gate: GateInputState, member: str) -> GateEvidenceState:
    raw = {
        "RESOURCE": gate.reality_state, "OBJECT": gate.source_state,
        "ALLOCATION": gate.allocation_state, "RISK": gate.risk_state,
        "ATTRIBUTION": gate.attribution_state, "TENSE": gate.temporal_state,
    }[member]
    return GateEvidenceState(raw)


def _reason_for_member(gate: GateInputState, member: str, state: GateEvidenceState) -> tuple[str, ...]:
    explicit = gate.allocation_reason_codes if member == "ALLOCATION" else gate.risk_reason_codes if member == "RISK" else ()
    if explicit:
        return explicit
    return {
        GateEvidenceState.MISSING: ("GATE.EVIDENCE_MISSING",),
        GateEvidenceState.CONFLICT: ("GATE.EVIDENCE_CONFLICT",),
        GateEvidenceState.UNKNOWN: ("GATE.STATE_UNKNOWN",),
        GateEvidenceState.SATISFIED: (),
    }[state]


def _validate_gate_state_surface(
    state: GateEvidenceState,
    supporting: tuple[str, ...],
    counter: tuple[str, ...],
    relations: tuple[str, ...],
    missing_paths: tuple[str, ...],
    conflict_paths: tuple[str, ...],
    unknown_paths: tuple[str, ...],
    source_decision: object,
) -> None:
    if state is GateEvidenceState.SATISFIED:
        _require(bool(supporting) and bool(source_decision), "GATE.REALITY_FACT_REFERENCE_REQUIRED")
        _require(not (counter or relations or missing_paths or conflict_paths or unknown_paths), "GATE.REALITY_FACT_REFERENCE_REQUIRED")
    elif state is GateEvidenceState.MISSING:
        _require(bool(missing_paths), "GATE.EVIDENCE_MISSING")
        _require(not (supporting or counter or relations or conflict_paths or unknown_paths), "GATE.EVIDENCE_MISSING")
    elif state is GateEvidenceState.CONFLICT:
        _require(bool(conflict_paths), "GATE.EVIDENCE_CONFLICT")
        _require(bool(relations) or (bool(supporting) and bool(counter)), "GATE.EVIDENCE_CONFLICT")
        _require(not (missing_paths or unknown_paths), "GATE.EVIDENCE_CONFLICT")
    else:
        _require(bool(unknown_paths), "GATE.STATE_UNKNOWN")
        _require(not (supporting or counter or relations or missing_paths or conflict_paths), "GATE.STATE_UNKNOWN")


def _gate_conflict_relation_valid(
    relation: EvidenceRelation,
    member_evidence_ids: frozenset[str],
) -> bool:
    return (
        relation.relation_type in ("COUNTERS", "COMPETES_WITH")
        and relation.status in ("ASSERTED", "OBSERVED")
        and relation.scope.function_id == "F09"
        and relation.to_ref.object_type == "EVIDENCE"
        and relation.to_ref.object_id in member_evidence_ids
        and relation.from_ref.object_type == "EVIDENCE"
        and relation.from_ref.object_id != relation.to_ref.object_id
        and bool(relation.source_refs)
    )


def _build_gate_set(
    candidate_id: str,
    data: GateEvaluationInput,
    *,
    normalized_evidence_port: NormalizedEvidenceReadPort,
    ref: FrozenCardFieldRef,
    candidate: FunctionCandidate,
    evidence_index: Mapping[str, EvidenceRecord],
    relation_index: Mapping[str, EvidenceRelation],
) -> GateEvaluationSet:
    declaration_version = data.declarations.precision_contract_version
    declaration_digest = _digest_from_text(data.declarations.validation_digest)
    members = tuple(
        GateDeclaredMember(derive_member_id(name, declaration_version, declaration_digest), name, ref)
        for name in SIX_MEMBERS
    )
    declared = GateMemberDeclarationSet(
        declaration_set_id=f"DECL-{candidate_id}", declaration_source_id=data.source.snapshot_id,
        declaration_schema_version=data.source.snapshot_schema_version,
        declaration_version=declaration_version, content_digest=declaration_digest, members=members,
    )
    _require(
        len(data.gate.member_ids) == len(data.gate.evaluation_binding_digests) == 6
        and len(set(data.gate.member_ids)) == 6,
        "GATE.MEMBER_CARDINALITY_INVALID",
    )
    supplied_binding = dict(zip(data.gate.member_ids, data.gate.evaluation_binding_digests))
    records = []
    for member in members:
        expected_state = _state_for_member(data.gate, str(member.declared_member_value))
        binding_id = supplied_binding.get(member.declared_member_id)
        _require(binding_id is not None, "GATE.MEMBER_BINDING_MISMATCH")
        try:
            binding = normalized_evidence_port.get_gate_evaluation_binding(binding_id)
        except (KeyError, LookupError):
            raise ValueError("GATE.MEMBER_BINDING_MISMATCH") from None
        _require(isinstance(binding, FrozenGateEvaluationBinding), "GATE.MEMBER_BINDING_MISMATCH")
        _require(binding.binding_id == binding_id, "GATE.MEMBER_BINDING_MISMATCH")
        _require(binding.binding_version == declaration_version, "GATE.MEMBER_BINDING_MISMATCH")
        _require(binding.source_locator_id == data.source.snapshot_id, "GATE.PERMUTATION_BINDING_INVALID")
        _require(binding.immutable_source_digest == _digest_from_text(data.source.payload_digest), "GATE.PERMUTATION_BINDING_INVALID")
        payload = binding.record_payload
        _require(binding.canonical_record_digest == _digest(thaw_frozen_json(payload)), "GATE.PERMUTATION_BINDING_INVALID")
        state = GateEvidenceState(str(payload["state"]))
        supporting = tuple(str(item) for item in payload["supporting_evidence_ids"])
        counter = tuple(str(item) for item in payload["counterevidence_ids"])
        relations = tuple(str(item) for item in payload["conflict_relation_ids"])
        missing_paths = tuple(str(item) for item in payload["missing_paths"])
        conflict_paths = tuple(str(item) for item in payload["conflict_paths"])
        unknown_paths = tuple(str(item) for item in payload["unknown_paths"])
        reasons = _reason_for_member(data.gate, str(member.declared_member_value), expected_state)
        authorized_reality_ids = frozenset(candidate.reality_evidence_ids)
        expected_supporting = tuple(
            evidence_id for evidence_id in candidate.reality_evidence_ids
            if evidence_id in evidence_index
            and evidence_index[evidence_id].track is EvidenceTrack.REALITY_FACT
            and member.declared_member_value in evidence_index[evidence_id].gate_members
        ) if expected_state in (GateEvidenceState.SATISFIED, GateEvidenceState.CONFLICT) else ()
        source_decision = payload["source_decision_ref"]
        expected_payload = {
            "candidate_id": candidate_id,
            "gate_definition_ref": _plain(ref),
            "declared_member_id": member.declared_member_id,
            "state": expected_state.value,
            "supporting_evidence_ids": expected_supporting,
            "counterevidence_ids": counter,
            "conflict_relation_ids": relations,
            "missing_paths": missing_paths,
            "conflict_paths": conflict_paths,
            "unknown_paths": unknown_paths,
            "reason_codes": reasons,
            "source_decision_ref": source_decision,
        }
        _require(payload == expected_payload, "GATE.PERMUTATION_BINDING_INVALID")
        _require(all(item in evidence_index for item in supporting + counter), "INTEGRITY.REFERENCE_BROKEN")
        _require(all(item in authorized_reality_ids for item in supporting), "GATE.PERMUTATION_BINDING_INVALID")
        member_evidence_ids = frozenset(supporting + counter)
        _require(all(item in relation_index for item in relations), "INTEGRITY.REFERENCE_BROKEN")
        _require(
            all(_gate_conflict_relation_valid(relation_index[item], member_evidence_ids) for item in relations),
            "GATE.PERMUTATION_BINDING_INVALID",
        )
        _validate_gate_state_surface(
            state, supporting, counter, relations, missing_paths, conflict_paths,
            unknown_paths, source_decision,
        )
        if state is GateEvidenceState.SATISFIED:
            _require(all(evidence_index[item].track is EvidenceTrack.REALITY_FACT for item in supporting), "INTEGRITY.TRACK_CONTAMINATION")
        records.append(GateEvaluationRecord(
            gate_record_id=f"GATE-{candidate_id}-{member.declared_member_id}", candidate_id=candidate_id,
            gate_definition_ref=ref, declared_member_id=member.declared_member_id,
            evaluation_binding_ref=GateEvaluationBindingRef(
                binding.binding_id, "gate-evaluation-binding.v1", binding.binding_version,
                binding.canonical_record_digest, binding.immutable_source_digest,
            ),
            state=state, supporting_evidence_ids=supporting, counterevidence_ids=counter,
            conflict_relation_ids=relations, missing_paths=missing_paths,
            conflict_paths=conflict_paths, unknown_paths=unknown_paths,
            reason_codes=reasons, source_decision_ref=source_decision,
        ))
    declared_ids = tuple(member.declared_member_id for member in members)
    structural = "READY"
    if set(data.gate.declared_member_ids) != set(declared_ids) or len(data.gate.declared_member_ids) != 6:
        structural = "BLOCKED"
    if set(data.gate.member_ids) != set(declared_ids) or len(data.gate.member_ids) != 6:
        structural = "BLOCKED"
    if len(data.gate.record_gate_definition_refs) != 6 or any(item != data.gate.gate_definition_ref for item in data.gate.record_gate_definition_refs):
        structural = "BLOCKED"
    if not data.gate.path_complete:
        structural = "INCOMPLETE"
    if any(record.state is GateEvidenceState.CONFLICT for record in records) and structural == "READY":
        structural = "DISPUTED"
    return GateEvaluationSet(candidate_id, "F09", (ref,), declared, tuple(records), structural, ())


def _expanded_field_ref(value: object) -> FrozenCardFieldRef:
    _require(isinstance(value, Mapping), "GATE.PERMUTATION_BINDING_INVALID")
    try:
        return FrozenCardFieldRef(**dict(value))
    except (TypeError, ValueError):
        raise ValueError("GATE.PERMUTATION_BINDING_INVALID") from None


def _expanded_constraint_ref(value: object) -> FrozenConstraintRef:
    _require(isinstance(value, Mapping), "TIMING.CONSTRAINT_UNKNOWN")
    try:
        return FrozenConstraintRef(**dict(value))
    except (TypeError, ValueError):
        raise ValueError("TIMING.CONSTRAINT_UNKNOWN") from None


def _validate_participation_state_surface(record: ParticipationRoleRecord) -> None:
    _require(
        record.state in ("SATISFIED", "MISSING", "CONFLICT", "UNKNOWN", "NOT_APPLICABLE"),
        "INTEGRITY.REFERENCE_BROKEN",
    )
    surfaces = {
        "supporting_evidence_ids": record.supporting_evidence_ids,
        "counterevidence_ids": record.counterevidence_ids,
        "missing_issue_ids": record.missing_issue_ids,
        "conflict_issue_ids": record.conflict_issue_ids,
        "unknown_issue_ids": record.unknown_issue_ids,
        "relation_ids": record.relation_ids,
    }
    required_nonempty = {
        "SATISFIED": ("supporting_evidence_ids",),
        "MISSING": ("missing_issue_ids",),
        "CONFLICT": ("supporting_evidence_ids", "counterevidence_ids", "conflict_issue_ids", "relation_ids"),
        "UNKNOWN": ("unknown_issue_ids",),
        "NOT_APPLICABLE": (),
    }[record.state]
    required_empty = {
        "SATISFIED": ("missing_issue_ids", "conflict_issue_ids", "unknown_issue_ids"),
        "MISSING": ("supporting_evidence_ids", "conflict_issue_ids", "unknown_issue_ids"),
        "CONFLICT": ("missing_issue_ids", "unknown_issue_ids"),
        "UNKNOWN": ("missing_issue_ids", "conflict_issue_ids"),
        "NOT_APPLICABLE": tuple(surfaces),
    }[record.state]
    _require(all(surfaces[name] for name in required_nonempty), "INTEGRITY.REFERENCE_BROKEN")
    _require(all(not surfaces[name] for name in required_empty), "INTEGRITY.REFERENCE_BROKEN")


def _validate_root_timing_state_surface(check: RootTimingConstraintCheck) -> None:
    _require(
        check.state in ("SATISFIED", "VIOLATED", "UNKNOWN", "NOT_APPLICABLE"),
        "TIMING.CONSTRAINT_UNKNOWN",
    )
    required_nonempty = {
        "SATISFIED": (),
        "VIOLATED": (check.conflict_paths, check.reason_codes),
        "UNKNOWN": (check.unknown_paths, check.reason_codes),
        "NOT_APPLICABLE": (check.reason_codes,),
    }[check.state]
    required_empty = {
        "SATISFIED": (check.missing_paths, check.conflict_paths, check.unknown_paths, check.reason_codes),
        "VIOLATED": (check.missing_paths, check.unknown_paths),
        "UNKNOWN": (check.missing_paths, check.conflict_paths),
        "NOT_APPLICABLE": (check.missing_paths, check.conflict_paths, check.unknown_paths),
    }[check.state]
    _require(all(required_nonempty), "TIMING.CONSTRAINT_UNKNOWN")
    _require(all(not value for value in required_empty), "TIMING.CONSTRAINT_UNKNOWN")


def _build_participation(
    candidate_id: str,
    data: GateEvaluationInput,
    ref: FrozenCardFieldRef,
    *,
    normalized_evidence_port: NormalizedEvidenceReadPort,
    evidence_index: Mapping[str, EvidenceRecord],
    relation_index: Mapping[str, EvidenceRelation],
) -> MinimumSufficientParticipationSet:
    set_id = f"PART-{candidate_id}"
    roles = data.participation.role_ids
    pairs = data.participation.role_authority_binding_ids
    _require(set(roles) == set(PARTICIPATION_ROLES) and len(roles) == len(set(roles)) == 6, "INTEGRITY.REFERENCE_BROKEN")
    _require(
        len(pairs) == 6
        and {role for role, _ in pairs} == set(PARTICIPATION_ROLES)
        and len({role for role, _ in pairs}) == 6
        and all(type(binding_id) is str and binding_id for _, binding_id in pairs)
        and len({binding_id for _, binding_id in pairs}) == 6,
        "INTEGRITY.REFERENCE_BROKEN",
    )
    binding_by_role = dict(pairs)
    records = []
    used_evidence_ids: set[str] = set()
    for role in PARTICIPATION_ROLES:
        binding_id = binding_by_role[role]
        try:
            binding = normalized_evidence_port.get_participation_role_binding(binding_id)
        except (KeyError, LookupError, ValueError, TypeError):
            raise ValueError("INTEGRITY.REFERENCE_BROKEN") from None
        _require(type(binding) is FrozenParticipationRoleBinding, "INTEGRITY.REFERENCE_BROKEN")
        _require(binding.binding_id == binding_id and binding.binding_version == data.declarations.precision_contract_version, "INTEGRITY.REFERENCE_BROKEN")
        _require(binding.source_locator_id == data.source.snapshot_id, "GATE.PERMUTATION_BINDING_INVALID")
        _require(binding.immutable_source_digest == _digest_from_text(data.source.payload_digest), "GATE.PERMUTATION_BINDING_INVALID")
        payload = binding.record_payload
        _require(binding.canonical_record_digest == _digest(thaw_frozen_json(payload)), "GATE.PERMUTATION_BINDING_INVALID")
        definition_refs = tuple(_expanded_field_ref(item) for item in payload["frozen_definition_refs"])
        supporting = tuple(payload["supporting_evidence_ids"])
        counter = tuple(payload["counterevidence_ids"])
        evidence_ids = set(supporting + counter)
        _require(not (used_evidence_ids & evidence_ids), "INTEGRITY.REFERENCE_BROKEN")
        used_evidence_ids.update(evidence_ids)
        _require(evidence_ids <= set(evidence_index), "INTEGRITY.REFERENCE_BROKEN")
        relation_ids = tuple(payload["relation_ids"])
        _require(set(relation_ids) <= set(relation_index), "INTEGRITY.REFERENCE_BROKEN")
        expected_record_id = f"{set_id}-{role}"
        _require(
            payload["participation_record_id"] == expected_record_id
            and payload["participation_set_id"] == set_id
            and payload["role"] == role
            and definition_refs == (ref,),
            "INTEGRITY.REFERENCE_BROKEN",
        )
        records.append(ParticipationRoleRecord(
            expected_record_id, set_id, role, binding_id, definition_refs, payload["state"],
            supporting, counter, tuple(payload["missing_issue_ids"]), tuple(payload["conflict_issue_ids"]),
            tuple(payload["unknown_issue_ids"]), relation_ids, payload["source_decision_ref"],
        ))
    return MinimumSufficientParticipationSet(set_id, candidate_id, "F09", PARTICIPATION_ROLES, tuple(records), "READY", ())


def _build_competition(data: CompetitionInput, gate_sets: tuple[GateEvaluationSet, ...], relation_ids: tuple[str, ...]) -> CompetitionSet:
    candidate_ids = data.decision.candidate_ids
    dispositions = tuple(
        CandidateDisposition(candidate, disposition, f"DECISION-{candidate}", (), (), ())
        for candidate, disposition in zip(candidate_ids, data.decision.dispositions)
    )
    state: StructuralReadinessState = "READY"
    if len(candidate_ids) != len(set(candidate_ids)) or len(dispositions) != len(candidate_ids):
        state = "BLOCKED"
    if data.decision.require_two_candidates and len(candidate_ids) < 2:
        state = "INCOMPLETE"
    dimensions = tuple(
        CompetitionDimensionEvaluation(dimension, {candidate: () for candidate in candidate_ids}, {candidate: () for candidate in candidate_ids}, (), "READY_FOR_DECISION", (), (), ())
        for dimension in ("primary_responsibility", "primary_action", "direct_object", "primary_deliverable", "primary_uncertainty", "stable_input", "strongest_competing_explanation")
    )
    return CompetitionSet("COMP-F09", candidate_ids, relation_ids, dimensions, (), dispositions, state, ())


def _issue(
    issue_id: str,
    issue_class: Literal["MISSING", "CONFLICT", "UNKNOWN"],
    owner_id: str,
    path: str,
    ref: FrozenCardFieldRef,
    reason: str,
    evidence_ids: tuple[str, ...] = (),
) -> FieldPathIssue:
    evaluator = {"MISSING": FieldEvaluatorState.MISSING, "CONFLICT": FieldEvaluatorState.CONFLICT, "UNKNOWN": FieldEvaluatorState.UNKNOWN}[issue_class]
    return FieldPathIssue(issue_id, issue_class, "BLOCKING", "ACTION", owner_id, "F09_INPUT", owner_id, "JSON_POINTER", path, ref.declared_state, evaluator, evidence_ids, (), (ref,), (reason,))


def _payload(decision: DecisionInputState, issues: tuple[FieldPathIssue, ...], result_id: str) -> DecisionPayload:
    action = DecisionAction(decision.selected_action)
    candidates = decision.candidate_ids
    if action is DecisionAction.OUTPUT:
        return OutputPayload(candidates, decision.disposition_refs, ("F09",))
    if action is DecisionAction.CONDITIONAL:
        return ConditionalPayload(candidates, decision.disposition_refs, decision.question_paths, decision.payload_issue_ids, ("F09",))
    if action is DecisionAction.ASK:
        questions = tuple(
            QuestionRequest(f"QUESTION-{index + 1}", decision.payload_issue_ids, (path,), "SCALAR_OR_STRUCTURED_FACT")
            for index, path in enumerate(decision.question_paths)
        )
        return AskPayload(questions, decision.payload_issue_ids, f"RESUME-{result_id}")
    if action is DecisionAction.ABSTAIN:
        return AbstainPayload(candidates, decision.payload_issue_ids, "F09_DECISION")
    return HumanReviewPayload(f"REVIEW-{result_id}", decision.payload_issue_ids, decision.basis_gate_ids + decision.basis_participation_ids, "F09_CONFLICT_RECORDS")


def evaluate_f09(
    package: NormalizedEvidencePackage,
    *,
    normalized_evidence_port: NormalizedEvidenceReadPort,
    frozen_contract_port: FrozenContractReadPort,
    request_id: str,
    contract_ref: ContractVersionRef,
    gate_inputs: tuple[GateEvaluationInput, ...],
    competition_input: CompetitionInput,
    root_input: RootInput,
    timing_input: TimingInput,
    produced_at: str,
) -> DecisionEvaluationResult:
    if type(package) is not NormalizedEvidencePackage:
        raise TypeError("package must be the exact NormalizedEvidencePackage runtime type")
    if not isinstance(normalized_evidence_port, NormalizedEvidenceReadPort):
        raise TypeError("normalized_evidence_port must implement NormalizedEvidenceReadPort")
    if not isinstance(frozen_contract_port, FrozenContractReadPort):
        raise TypeError("frozen_contract_port must implement FrozenContractReadPort")
    if not gate_inputs:
        raise ValueError("gate_inputs must be nonempty")

    authoritative_package = normalized_evidence_port.get_package(package.package_id)
    _require(type(authoritative_package) is NormalizedEvidencePackage, "INTEGRITY.PACKAGE_NOT_CONSUMABLE")
    _require(
        authoritative_package == package
        and authoritative_package.package_id == package.package_id
        and authoritative_package.case_id == package.case_id
        and authoritative_package.track is package.track,
        "INTEGRITY.PACKAGE_NOT_CONSUMABLE",
    )
    pi210 = normalized_evidence_port.validate_for_pi220(authoritative_package.package_id)
    _require(pi210 in ("READY", "INVALID", "BLOCKED"), "INTEGRITY.PACKAGE_NOT_CONSUMABLE")
    _require(pi210 == "READY", "INTEGRITY.PACKAGE_NOT_CONSUMABLE")
    contract_integrity = frozen_contract_port.verify_contract_version(contract_ref)
    _require(isinstance(contract_integrity, ContractIntegrityResult), "INTEGRITY.CONTRACT_VERSION_MISMATCH")
    _require(contract_integrity.state == "VALID", "INTEGRITY.CONTRACT_VERSION_MISMATCH")

    candidate_ids = competition_input.decision.candidate_ids
    _require(bool(candidate_ids), "INTEGRITY.REFERENCE_BROKEN")
    candidates: list[FunctionCandidate] = []
    evidence_index: dict[str, EvidenceRecord] = {}
    relation_index: dict[str, EvidenceRelation] = {}
    for candidate_id in candidate_ids:
        candidate = normalized_evidence_port.get_candidate(candidate_id)
        _require(
            type(candidate) is FunctionCandidate
            and candidate.candidate_id == candidate_id
            and candidate.case_id == authoritative_package.case_id
            and candidate.function_id == "F09",
            "INTEGRITY.REFERENCE_BROKEN",
        )
        candidates.append(candidate)
        for track in EvidenceTrack:
            for record in normalized_evidence_port.list_evidence(candidate_id, track):
                _require(type(record) is EvidenceRecord, "INTEGRITY.REFERENCE_BROKEN")
                evidence_id = record.evidence_id
                _require(record.track is track, "INTEGRITY.TRACK_CONTAMINATION")
                existing = evidence_index.setdefault(evidence_id, record)
                _require(existing == record, "INTEGRITY.REFERENCE_BROKEN")
        for record in normalized_evidence_port.list_counterevidence(candidate_id):
            _require(type(record) is EvidenceRecord, "INTEGRITY.REFERENCE_BROKEN")
            evidence_id = record.evidence_id
            existing = evidence_index.setdefault(evidence_id, record)
            _require(existing == record, "INTEGRITY.REFERENCE_BROKEN")
        for relation in normalized_evidence_port.list_relations(candidate_id):
            _require(type(relation) is EvidenceRelation, "INTEGRITY.REFERENCE_BROKEN")
            relation_id = relation.relation_id
            existing = relation_index.setdefault(relation_id, relation)
            _require(existing == relation, "INTEGRITY.REFERENCE_BROKEN")
    _require(bool(relation_index), "INTEGRITY.REFERENCE_BROKEN")

    first_input = gate_inputs[0]
    field_ref = normalized_evidence_port.get_card_field_ref("F09", first_input.gate.gate_definition_ref)
    _require(isinstance(field_ref, FrozenCardFieldRef), "INTEGRITY.CARD_BINDING_INVALID")
    field_observation = frozen_contract_port.get_field(field_ref)
    _require(isinstance(field_observation, FrozenFieldObservation), "INTEGRITY.CARD_BINDING_INVALID")
    _require(
        field_observation.ref == field_ref
        and field_observation.source_state == field_ref.declared_state
        and field_observation.value == field_ref.declared_value
        and field_ref.contract_version == contract_ref.contract_version,
        "INTEGRITY.CARD_BINDING_INVALID",
    )
    output_precision_binding = normalized_evidence_port.get_output_precision_binding("F09")
    validation_plan_binding = normalized_evidence_port.get_validation_plan_binding("F09")
    _require(output_precision_binding == authoritative_package.output_precision.binding, "INTEGRITY.CARD_BINDING_INVALID")
    _require(validation_plan_binding == authoritative_package.validation_plan.binding, "INTEGRITY.CARD_BINDING_INVALID")

    _require(root_input.source.reality_track == "CHART_STRUCTURE", "ROOT.SOURCE_TRACK_INVALID")
    _require(timing_input.source.reality_track == "CHART_STRUCTURE", "ROOT.SOURCE_TRACK_INVALID")
    _require(root_input.root_timing.root_state in ("STRONG_ROOT", "WEAK_ROOT", "NO_ROOT"), "ROOT.ENTRY_MISSING")
    _require(
        timing_input.root_timing.timing_state in (
            "ACTIVATE_EXISTING", "COMPLETE_LATENT", "REPAIR_DEFECT",
            "TEMPORARY_SUBSTITUTE", "INVALID_COMPLETION",
        ),
        "TIMING.CONSTRAINT_UNKNOWN",
    )
    _require(not timing_input.root_timing.timing_rewrites_root, "TIMING.CONSTRAINT_VIOLATED")
    constraint_ref = frozen_contract_port.get_constraint_ref("F09", "/root_timing")
    _require(
        isinstance(constraint_ref, FrozenConstraintRef)
        and constraint_ref.card_id == "F09"
        and constraint_ref.contract_version == contract_ref.contract_version
        and constraint_ref.constraint_path == "/root_timing",
        "INTEGRITY.CONTRACT_VERSION_MISMATCH",
    )

    for item in gate_inputs:
        _require(item.gate.gate_definition_ref == field_ref.field_path, "INTEGRITY.CARD_BINDING_INVALID")
        _require(
            len(item.gate.supporting_evidence_tracks) == 6
            and all(track == "REALITY_FACT" for track in item.gate.supporting_evidence_tracks),
            "INTEGRITY.TRACK_CONTAMINATION",
        )

    result_id = f"F09-RESULT-{_digest((authoritative_package.package_id, request_id, produced_at)).value[:20]}"
    gate_sets = tuple(
        _build_gate_set(
            candidate_ids[min(index, len(candidate_ids) - 1)], item,
            normalized_evidence_port=normalized_evidence_port,
            ref=field_ref,
            candidate=candidates[min(index, len(candidates) - 1)],
            evidence_index=evidence_index,
            relation_index=relation_index,
        )
        for index, item in enumerate(gate_inputs)
    )
    participation_sets = tuple(
        _build_participation(
            item.candidate_id, gate_inputs[index], field_ref,
            normalized_evidence_port=normalized_evidence_port,
            evidence_index=evidence_index,
            relation_index=relation_index,
        )
        for index, item in enumerate(gate_sets)
    )
    competition = _build_competition(competition_input, gate_sets, tuple(relation_index))
    root_entries = tuple(
        RootLedgerEntry(f"ROOT-{candidate}", "COMMON", root_input.root_timing.root_state, None, (root_input.source.state_object_id,), (root_input.source.snapshot_id,), root_input.source.reality_track)
        for candidate in candidate_ids
    )
    root_ledgers = tuple(RootConstraintLedger(candidate, (root_entries[index],), ()) for index, candidate in enumerate(candidate_ids))
    timing_entries = tuple(
        TimingLedgerEntry(f"TIMING-{candidate}", timing_input.root_timing.timing_state, f"ROOT-{candidate}" if timing_input.root_timing.timing_state != "INVALID_COMPLETION" else None, (timing_input.source.event_object_id,), timing_input.source.reality_track)
        for candidate in candidate_ids
    )
    timing_ledgers = tuple(TimingConstraintLedger(candidate, (timing_entries[index],), ()) for index, candidate in enumerate(candidate_ids))
    root_pairs = root_input.root_timing.authority_binding_ids
    timing_pairs = timing_input.root_timing.authority_binding_ids
    _require(root_pairs == timing_pairs, "TIMING.CONSTRAINT_UNKNOWN")
    _require(
        len(root_pairs) == len(candidate_ids)
        and {candidate for candidate, _ in root_pairs} == set(candidate_ids)
        and len({candidate for candidate, _ in root_pairs}) == len(candidate_ids)
        and all(type(binding_id) is str and binding_id for _, binding_id in root_pairs)
        and len({binding_id for _, binding_id in root_pairs}) == len(candidate_ids),
        "TIMING.CONSTRAINT_UNKNOWN",
    )
    root_ids_by_candidate = {ledger.candidate_id: tuple(entry.root_evidence_id for entry in ledger.root_entries) for ledger in root_ledgers}
    timing_ids_by_candidate = {ledger.candidate_id: tuple(entry.timing_evidence_id for entry in ledger.timing_entries) for ledger in timing_ledgers}
    check_binding_by_candidate = dict(root_pairs)
    check_sets = []
    for candidate in candidate_ids:
        binding_id = check_binding_by_candidate[candidate]
        try:
            binding = normalized_evidence_port.get_root_timing_outcome_binding(binding_id)
        except (KeyError, LookupError, ValueError, TypeError):
            raise ValueError("TIMING.CONSTRAINT_UNKNOWN") from None
        _require(type(binding) is FrozenRootTimingOutcomeBinding, "TIMING.CONSTRAINT_UNKNOWN")
        _require(binding.binding_id == binding_id and binding.binding_version == contract_ref.contract_version, "TIMING.CONSTRAINT_UNKNOWN")
        _require(binding.source_locator_id == root_input.source.snapshot_id == timing_input.source.snapshot_id, "TIMING.CONSTRAINT_UNKNOWN")
        _require(
            binding.immutable_source_digest == _digest_from_text(root_input.source.payload_digest)
            == _digest_from_text(timing_input.source.payload_digest),
            "TIMING.CONSTRAINT_UNKNOWN",
        )
        check_payload = binding.record_payload
        _require(binding.canonical_record_digest == _digest(thaw_frozen_json(check_payload)), "TIMING.CONSTRAINT_UNKNOWN")
        payload_constraint_ref = _expanded_constraint_ref(check_payload["constraint_ref"])
        expected_check_id = f"CHECK-{candidate}"
        _require(
            check_payload["check_id"] == expected_check_id
            and payload_constraint_ref == constraint_ref
            and tuple(check_payload["root_entry_ids"]) == root_ids_by_candidate[candidate]
            and tuple(check_payload["timing_entry_ids"]) == timing_ids_by_candidate[candidate],
            "TIMING.CONSTRAINT_UNKNOWN",
        )
        check_sets.append(RootTimingConstraintSet(candidate, (RootTimingConstraintCheck(
            expected_check_id, binding_id, payload_constraint_ref,
            tuple(check_payload["root_entry_ids"]), tuple(check_payload["timing_entry_ids"]),
            check_payload["state"], check_payload["source_decision_ref"],
            tuple(check_payload["missing_paths"]), tuple(check_payload["conflict_paths"]),
            tuple(check_payload["unknown_paths"]), tuple(check_payload["reason_codes"]),
        ),), "READY", ()))
    checks = tuple(check_sets)
    first_ref = gate_sets[0].gate_definition_refs[0]
    conflict_evidence_ids = tuple(evidence_index)[:2]
    issues = tuple(
        _issue(
            issue_id,
            "CONFLICT" if "CONFLICT" in issue_id else "UNKNOWN",
            result_id,
            competition_input.decision.question_paths[index] if index < len(competition_input.decision.question_paths) else "/decision",
            first_ref,
            "FIELD.CONFLICTING_VALUES" if "CONFLICT" in issue_id else "FIELD.EVALUATOR_UNKNOWN",
            conflict_evidence_ids if "CONFLICT" in issue_id else (),
        )
        for index, issue_id in enumerate(competition_input.decision.payload_issue_ids)
    )
    f08_runtime = bool(competition_input.decision.f08_runtime_objects) or any(candidate == "F08" or candidate.startswith("F08-") for candidate in candidate_ids)
    refs_valid = not f08_runtime and all(item.set_state != "BLOCKED" for item in gate_sets)
    referenced_evidence = {
        evidence_id for gate_set in gate_sets for record in gate_set.records
        for evidence_id in record.supporting_evidence_ids + record.counterevidence_ids
    }
    referenced_evidence.update(
        evidence_id for participation_set in participation_sets for record in participation_set.role_records
        for evidence_id in record.supporting_evidence_ids + record.counterevidence_ids
    )
    evidence_valid = referenced_evidence <= set(evidence_index)
    relation_refs = {
        relation_id for gate_set in gate_sets for record in gate_set.records
        for relation_id in record.conflict_relation_ids
    }
    relation_refs.update(competition.relation_ids)
    relation_valid = bool(relation_index) and relation_refs <= set(relation_index)
    blocking_ids = tuple(issue.issue_id for issue in issues)
    consumption = PackageConsumptionCheck(
        authoritative_package.package_id, pi210, contract_integrity,
        "VALID" if refs_valid else "INVALID", "VALID" if evidence_valid else "INVALID",
        "VALID" if relation_valid else "INVALID",
        pi210 == "READY" and refs_valid and evidence_valid and relation_valid, blocking_ids,
    )
    decision = competition_input.decision
    selected_action = DecisionAction(decision.selected_action)
    payload = _payload(decision, issues, result_id)
    basis = decision.basis_gate_ids + decision.basis_participation_ids
    errors = []
    if decision.payload_type != type(payload).__name__:
        errors.append("ACTION.PAYLOAD_TYPE_MISMATCH")
    if not basis:
        errors.append("ACTION.BASIS_MISSING")
    if f08_runtime:
        errors.append("INTEGRITY.REFERENCE_BROKEN")
    if selected_action in (DecisionAction.OUTPUT, DecisionAction.CONDITIONAL) and (not consumption.consumable or blocking_ids):
        errors.append("ACTION.BLOCKING_ISSUE_PRESENT")
    envelope = DecisionActionEnvelope(
        f"ACTION-{result_id}", selected_action, decision.candidate_ids, payload, basis,
        blocking_ids, (), tuple(dict.fromkeys(errors)),
        tuple(record.source_decision_ref for item in participation_sets for record in item.role_records),
        output_precision_binding, validation_plan_binding,
        "INVALID" if errors else "VALID", tuple(errors),
    )
    result = DecisionEvaluationResult(
        result_id, request_id, authoritative_package.package_id, contract_ref, consumption, gate_sets,
        participation_sets, (competition,), root_ledgers, timing_ledgers, checks, issues,
        envelope, produced_at,
    )
    validate_decision_result(result)
    return result


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _all_reason_codes(result: DecisionEvaluationResult) -> tuple[str, ...]:
    values = list(result.consumption_check.contract_integrity.reason_codes)
    values.extend(result.action_envelope.reason_codes)
    for gate_set in result.gate_sets:
        for record in gate_set.records:
            values.extend(record.reason_codes)
    for competition in result.competition_sets:
        for disposition in competition.candidate_dispositions:
            values.extend(disposition.reason_codes)
    for check_set in result.root_timing_checks:
        for check in check_set.checks:
            values.extend(check.reason_codes)
    for issue in result.issues:
        values.extend(issue.reason_codes)
    return tuple(values)


def validate_decision_result(result: DecisionEvaluationResult) -> None:
    if not isinstance(result, DecisionEvaluationResult):
        raise TypeError("result must be DecisionEvaluationResult")
    unknown = set(_all_reason_codes(result)) - REGISTERED_REASON_CODES
    _require(not unknown, f"unknown reason codes: {sorted(unknown)}")
    envelope = result.action_envelope
    payload_types = {
        DecisionAction.OUTPUT: OutputPayload, DecisionAction.CONDITIONAL: ConditionalPayload,
        DecisionAction.ASK: AskPayload, DecisionAction.ABSTAIN: AbstainPayload,
        DecisionAction.HUMAN_REVIEW: HumanReviewPayload,
    }
    _require(type(envelope.payload) is payload_types[envelope.selected_action], "ACTION.PAYLOAD_TYPE_MISMATCH")
    _require(bool(envelope.basis_record_ids), "ACTION.BASIS_MISSING")
    _require(len(envelope.basis_record_ids) == len(set(envelope.basis_record_ids)), "ACTION.BASIS_MISSING")
    _require(isinstance(envelope.output_precision_binding, ResolvedDeclarationBinding), "output precision must be RESOLVED")
    _require(isinstance(envelope.validation_plan_binding, ResolvedDeclarationBinding), "validation plan must be RESOLVED")
    issue_by_id = {issue.issue_id: issue for issue in result.issues}
    _require(len(issue_by_id) == len(result.issues), "INTEGRITY.REFERENCE_BROKEN")
    all_record_ids: set[str] = set(issue_by_id)
    for gate_set in result.gate_sets:
        _require(gate_set.function_id == "F09", "F08 runtime candidate forbidden")
        members = gate_set.member_declaration_set.members
        records = gate_set.records
        _require(len(members) == 6 and len(records) == 6, "GATE.MEMBER_CARDINALITY_INVALID")
        member_ids = tuple(member.declared_member_id for member in members)
        member_values = tuple(member.declared_member_value for member in members)
        _require(len(set(member_ids)) == 6 and set(member_values) == set(SIX_MEMBERS), "GATE.MEMBER_CARDINALITY_INVALID")
        _require(len(set(member_values)) == 6, "GATE.MEMBER_CARDINALITY_INVALID")
        declaration = gate_set.member_declaration_set
        for member in members:
            expected_id = derive_member_id(str(member.declared_member_value), declaration.declaration_version, declaration.content_digest)
            _require(member.declared_member_id == expected_id, "GATE.MEMBER_DECLARATION_INVALID")
        record_ids = tuple(record.gate_record_id for record in records)
        _require(not (set(record_ids) & all_record_ids), "INTEGRITY.REFERENCE_BROKEN")
        all_record_ids.update(record_ids)
        _require(len(set(record.declared_member_id for record in records)) == 6 and set(record.declared_member_id for record in records) == set(member_ids), "GATE.MEMBER_CARDINALITY_INVALID")
        member_by_id = {member.declared_member_id: member for member in members}
        definition_refs = set(gate_set.gate_definition_refs)
        _require(bool(definition_refs) and definition_refs == {member.gate_definition_ref for member in members} == {record.gate_definition_ref for record in records}, "GATE.MEMBER_BINDING_MISMATCH")
        for record in records:
            _require(record.candidate_id == gate_set.candidate_id, "candidate mismatch")
            _require(record.gate_definition_ref == member_by_id[record.declared_member_id].gate_definition_ref, "GATE.MEMBER_BINDING_MISMATCH")
            binding = record.evaluation_binding_ref
            _require(binding.binding_schema_version == "gate-evaluation-binding.v1", "GATE.MEMBER_BINDING_MISMATCH")
            _require(binding.binding_version == declaration.declaration_version, "GATE.MEMBER_BINDING_MISMATCH")
            _require(binding.canonical_record_digest == record_digest(record), "GATE.PERMUTATION_BINDING_INVALID")
            _require(binding.immutable_source_digest != binding.canonical_record_digest, "GATE.PERMUTATION_BINDING_INVALID")
            _validate_gate_state_surface(
                record.state, record.supporting_evidence_ids,
                record.counterevidence_ids, record.conflict_relation_ids,
                record.missing_paths, record.conflict_paths, record.unknown_paths,
                record.source_decision_ref,
            )
    candidates = {gate_set.candidate_id for gate_set in result.gate_sets}
    _require(not any(candidate == "F08" or candidate.startswith("F08-") for candidate in candidates), "F08 runtime candidate forbidden")
    all_record_ids.update(candidates)
    _require(len(result.participation_sets) == len(candidates), "INTEGRITY.REFERENCE_BROKEN")
    participation_candidates: set[str] = set()
    participation_binding_ids: set[str] = set()
    participation_evidence_ids: set[str] = set()
    for participation_set in result.participation_sets:
        _require(participation_set.candidate_id in candidates and participation_set.candidate_id not in participation_candidates, "INTEGRITY.REFERENCE_BROKEN")
        participation_candidates.add(participation_set.candidate_id)
        _require(participation_set.required_roles == PARTICIPATION_ROLES, "INTEGRITY.REFERENCE_BROKEN")
        _require(len(participation_set.role_records) == 6, "INTEGRITY.REFERENCE_BROKEN")
        roles = tuple(record.role for record in participation_set.role_records)
        _require(set(roles) == set(PARTICIPATION_ROLES) and len(set(roles)) == 6, "INTEGRITY.REFERENCE_BROKEN")
        for record in participation_set.role_records:
            _require(record.participation_set_id == participation_set.participation_set_id, "INTEGRITY.REFERENCE_BROKEN")
            _require(type(record.authority_binding_id) is str and bool(record.authority_binding_id), "INTEGRITY.REFERENCE_BROKEN")
            _require(record.authority_binding_id not in participation_binding_ids, "INTEGRITY.REFERENCE_BROKEN")
            participation_binding_ids.add(record.authority_binding_id)
            current_evidence = set(record.supporting_evidence_ids + record.counterevidence_ids)
            _require(not (current_evidence & participation_evidence_ids), "INTEGRITY.REFERENCE_BROKEN")
            participation_evidence_ids.update(current_evidence)
            _require(type(record.source_decision_ref) is str and bool(record.source_decision_ref), "INTEGRITY.REFERENCE_BROKEN")
            _validate_participation_state_surface(record)
            all_record_ids.add(record.participation_record_id)
    for competition in result.competition_sets:
        _require(not any(candidate == "F08" or candidate.startswith("F08-") for candidate in competition.candidate_ids), "F08 runtime candidate forbidden")
        _require(len(competition.candidate_ids) == len(set(competition.candidate_ids)), "duplicate competition candidate")
        _require(bool(competition.relation_ids), "INTEGRITY.REFERENCE_BROKEN")
        _require(len(competition.relation_ids) == len(set(competition.relation_ids)), "INTEGRITY.REFERENCE_BROKEN")
        all_record_ids.add(competition.competition_id)
    root_entries = {entry.root_evidence_id: entry for ledger in result.root_ledgers for entry in ledger.root_entries}
    all_record_ids.update(root_entries)
    for entry in root_entries.values():
        _require(entry.source_track == "CHART_STRUCTURE", "ROOT.SOURCE_TRACK_INVALID")
    for ledger in result.timing_ledgers:
        for entry in ledger.timing_entries:
            _require(entry.source_track == "CHART_STRUCTURE", "ROOT.SOURCE_TRACK_INVALID")
            _require(entry.completion_mode in ("ACTIVATE_EXISTING", "COMPLETE_LATENT", "REPAIR_DEFECT", "TEMPORARY_SUBSTITUTE", "INVALID_COMPLETION"), "TIMING.CONSTRAINT_UNKNOWN")
            all_record_ids.add(entry.timing_evidence_id)
            if entry.target_root_evidence_id is not None:
                _require(entry.target_root_evidence_id in root_entries, "TIMING.ROOT_REFERENCE_BROKEN")
    timing_entries = {entry.timing_evidence_id for ledger in result.timing_ledgers for entry in ledger.timing_entries}
    _require(len(result.root_timing_checks) == len(candidates), "TIMING.CONSTRAINT_UNKNOWN")
    check_candidates: set[str] = set()
    check_binding_ids: set[str] = set()
    for check_set in result.root_timing_checks:
        _require(check_set.candidate_id in candidates and check_set.candidate_id not in check_candidates, "TIMING.CONSTRAINT_UNKNOWN")
        check_candidates.add(check_set.candidate_id)
        _require(len(check_set.checks) == 1, "TIMING.CONSTRAINT_UNKNOWN")
        for check in check_set.checks:
            _require(isinstance(check.constraint_ref, FrozenConstraintRef), "constraint_ref must be FrozenConstraintRef")
            _require(type(check.authority_binding_id) is str and bool(check.authority_binding_id), "TIMING.CONSTRAINT_UNKNOWN")
            _require(check.authority_binding_id not in check_binding_ids, "TIMING.CONSTRAINT_UNKNOWN")
            check_binding_ids.add(check.authority_binding_id)
            _require(bool(check.root_entry_ids) and set(check.root_entry_ids) <= set(root_entries), "TIMING.ROOT_REFERENCE_BROKEN")
            _require(bool(check.timing_entry_ids) and set(check.timing_entry_ids) <= timing_entries, "TIMING.CONSTRAINT_UNKNOWN")
            _require(type(check.source_decision_ref) is str and bool(check.source_decision_ref), "TIMING.CONSTRAINT_UNKNOWN")
            _validate_root_timing_state_surface(check)
            all_record_ids.add(check.check_id)
    for issue in result.issues:
        _require(issue.path_dialect == "JSON_POINTER" and issue.field_path.startswith("/"), "issue path must be JSON Pointer")
        _require(issue.source_state in ("PRESENT_VALUE", "EXPLICIT_NULL", "LISTED_UNRESOLVED", "BOTH_NULL_AND_UNRESOLVED", "ABSENT"), "invalid SourceFieldState")
        _require(not issue.relation_ids, "INTEGRITY.REFERENCE_BROKEN")
    _require(set(envelope.basis_record_ids) <= all_record_ids, "ACTION.BASIS_MISSING")
    _require(set(envelope.blocking_issue_ids) <= set(issue_by_id), "INTEGRITY.REFERENCE_BROKEN")
    payload = envelope.payload
    if isinstance(payload, OutputPayload):
        _require(bool(payload.included_candidate_ids) and bool(payload.disposition_refs) and bool(payload.scope_refs), "ACTION.BASIS_MISSING")
        _require(set(payload.included_candidate_ids) <= candidates, "INTEGRITY.REFERENCE_BROKEN")
        _require(set(payload.disposition_refs) <= all_record_ids, "INTEGRITY.REFERENCE_BROKEN")
        _require(result.consumption_check.consumable, "INTEGRITY.PACKAGE_NOT_CONSUMABLE")
        _require(not envelope.blocking_issue_ids, "ACTION.BLOCKING_ISSUE_PRESENT")
        _require(
            all(
                gate_set.set_state == "READY"
                and len(gate_set.records) == 6
                and all(record.state is GateEvidenceState.SATISFIED for record in gate_set.records)
                for gate_set in result.gate_sets
            ),
            "ACTION.BLOCKING_ISSUE_PRESENT",
        )
        _require(
            all(
                item.structural_state == "READY"
                and len(item.role_records) == 6
                and all(record.state == "SATISFIED" for record in item.role_records)
                for item in result.participation_sets
            ),
            "ACTION.BLOCKING_ISSUE_PRESENT",
        )
        _require(all(item.structural_state == "READY" for item in result.competition_sets), "ACTION.BLOCKING_ISSUE_PRESENT")
        _require(
            all(
                item.structural_state == "READY"
                and len(item.checks) == 1
                and all(check.state == "SATISFIED" for check in item.checks)
                for item in result.root_timing_checks
            ),
            "ACTION.BLOCKING_ISSUE_PRESENT",
        )
    elif isinstance(payload, ConditionalPayload):
        _require(result.consumption_check.consumable, "INTEGRITY.PACKAGE_NOT_CONSUMABLE")
        _require(bool(payload.included_candidate_ids) and bool(payload.condition_refs) and bool(payload.scope_refs), "ACTION.BASIS_MISSING")
        _require(set(payload.included_candidate_ids) <= candidates, "INTEGRITY.REFERENCE_BROKEN")
        _require(set(payload.disposition_refs) <= all_record_ids, "INTEGRITY.REFERENCE_BROKEN")
        _require(set(payload.unresolved_issue_ids) <= set(issue_by_id), "INTEGRITY.REFERENCE_BROKEN")
    elif isinstance(payload, AskPayload):
        _require(bool(payload.question_requests) and bool(payload.resume_token), "ACTION.QUESTION_NOT_BOUND_TO_ISSUE")
        _require(set(payload.unresolved_issue_ids) <= set(issue_by_id), "ACTION.QUESTION_NOT_BOUND_TO_ISSUE")
        for question in payload.question_requests:
            _require(bool(question.target_issue_ids) and bool(question.requested_field_paths), "ACTION.QUESTION_NOT_BOUND_TO_ISSUE")
            _require(all(issue_id in issue_by_id and issue_by_id[issue_id].issue_class in ("MISSING", "UNKNOWN") for issue_id in question.target_issue_ids), "ACTION.QUESTION_NOT_BOUND_TO_ISSUE")
            issue_paths = {issue_by_id[issue_id].field_path for issue_id in question.target_issue_ids}
            _require(set(question.requested_field_paths) <= issue_paths, "ACTION.QUESTION_NOT_BOUND_TO_ISSUE")
    elif isinstance(payload, AbstainPayload):
        _require(bool(payload.abstained_candidate_ids) and bool(payload.blocking_issue_ids) and bool(payload.abstention_scope), "ACTION.BLOCKING_ISSUE_PRESENT")
        _require(set(payload.abstained_candidate_ids) <= candidates, "INTEGRITY.REFERENCE_BROKEN")
        _require(all(issue_id in issue_by_id and issue_by_id[issue_id].severity == "BLOCKING" for issue_id in payload.blocking_issue_ids), "ACTION.BLOCKING_ISSUE_PRESENT")
    else:
        _require(bool(payload.review_issue_ids) and bool(payload.review_record_ids) and bool(payload.requested_review_scope), "ACTION.REVIEW_SCOPE_MISSING")
        _require(set(payload.review_record_ids) <= all_record_ids, "INTEGRITY.REFERENCE_BROKEN")
        for issue_id in payload.review_issue_ids:
            _require(issue_id in issue_by_id and issue_by_id[issue_id].issue_class == "CONFLICT", "ACTION.REVIEW_SCOPE_MISSING")
            _require(len(set(issue_by_id[issue_id].evidence_ids)) >= 2, "ACTION.REVIEW_SCOPE_MISSING")
