from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal, Mapping, Protocol, TypeAlias, Union, runtime_checkable

if TYPE_CHECKING:
    from engine.f09.evidence import EvidenceRecord, NormalizedEvidencePackage

FunctionId: TypeAlias = Literal[
    "F01", "F02", "F03", "F04", "F05", "F06",
    "F07", "F08", "F09", "F10", "F11", "F12",
]
SourceFieldState: TypeAlias = Literal[
    "PRESENT_VALUE",
    "EXPLICIT_NULL",
    "LISTED_UNRESOLVED",
    "BOTH_NULL_AND_UNRESOLVED",
    "ABSENT",
]

class RunTrack(str, Enum):
    PRODUCTION_DEFAULT = "PRODUCTION_DEFAULT"
    PARALLEL_DOMAIN = "PARALLEL_DOMAIN"
    STAGED_L6 = "STAGED_L6"
    V5_V6_PREPROD = "V5_V6_PREPROD"
    MANUAL_IMPORT = "MANUAL_IMPORT"

class EvidenceTrack(str, Enum):
    CHART_STRUCTURE = "CHART_STRUCTURE"
    REALITY_FACT = "REALITY_FACT"
    UNVERIFIED_HYPOTHESIS = "UNVERIFIED_HYPOTHESIS"

class GateEvidenceState(str, Enum):
    SATISFIED = "SATISFIED"
    MISSING = "MISSING"
    CONFLICT = "CONFLICT"
    UNKNOWN = "UNKNOWN"

class FieldEvaluatorState(str, Enum):
    EVALUATED = "EVALUATED"
    MISSING = "MISSING"
    CONFLICT = "CONFLICT"
    UNKNOWN = "UNKNOWN"
    NOT_EVALUATED = "NOT_EVALUATED"

class DecisionAction(str, Enum):
    OUTPUT = "OUTPUT"
    CONDITIONAL = "CONDITIONAL"
    ASK = "ASK"
    ABSTAIN = "ABSTAIN"
    HUMAN_REVIEW = "HUMAN_REVIEW"

class ArtifactItemState(str, Enum):
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    WRITING = "WRITING"
    WRITTEN_UNVERIFIED = "WRITTEN_UNVERIFIED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    STALE = "STALE"
    MISMATCH = "MISMATCH"
    SUPERSEDED = "SUPERSEDED"

class ArtifactSetState(str, Enum):
    COMPLETE_VERIFIED = "COMPLETE_VERIFIED"
    PARTIAL = "PARTIAL"
    STALE_MIXED_REVISION = "STALE_MIXED_REVISION"
    DIGEST_MISMATCH = "DIGEST_MISMATCH"
    FAILED = "FAILED"
@dataclass(frozen=True)
class ContractVersionRef:
    normative_contract_path: str
    machine_appendix_path: str
    contract_version: str
    content_digest: str


@dataclass(frozen=True)
class DigestRef:
    algorithm: str
    canonicalization: str
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("value must be a string")
        if len(self.value) != 64 or any(char not in "0123456789abcdef" for char in self.value):
            raise ValueError("value must be a lowercase 64-hex digest")


@dataclass(frozen=True)
class FrozenCardFieldRef:
    card_id: FunctionId
    contract_id: str
    contract_version: str
    field_path: str
    declared_state: SourceFieldState
    declared_value: object
    source_locator_id: str


@dataclass(frozen=True)
class FrozenConstraintRef:
    card_id: FunctionId
    contract_id: str
    contract_version: str
    constraint_path: str
    source_locator_id: str


@dataclass(frozen=True)
class ContractIntegrityResult:
    state: Literal["VALID", "INVALID"]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class FrozenFieldObservation:
    ref: FrozenCardFieldRef
    source_state: SourceFieldState
    value: object
    unresolved_state_ref: str | None
    source_location: str

    def __post_init__(self) -> None:
        if not isinstance(self.ref, FrozenCardFieldRef):
            raise TypeError("ref must be FrozenCardFieldRef")
        if self.source_state not in (
            "PRESENT_VALUE", "EXPLICIT_NULL", "LISTED_UNRESOLVED",
            "BOTH_NULL_AND_UNRESOLVED", "ABSENT",
        ):
            raise ValueError("invalid source_state")
        if type(self.source_location) is not str or not self.source_location:
            raise ValueError("source_location must be a nonempty string")


def _freeze_json(value: object, active: set[int] | None = None) -> object:
    """Freeze the closed, number-free binding JSON graph without changing its JSON value."""
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise TypeError("record_payload numbers are outside the bounded JCS schema")
    if active is None:
        active = set()
    if type(value) is list:
        identity = id(value)
        if identity in active:
            raise ValueError("record_payload cycle detected")
        active.add(identity)
        try:
            return tuple(_freeze_json(item, active) for item in value)
        finally:
            active.remove(identity)
    if type(value) is dict:
        identity = id(value)
        if identity in active:
            raise ValueError("record_payload cycle detected")
        if not all(type(key) is str for key in value):
            raise TypeError("record_payload object keys must be exact strings")
        active.add(identity)
        try:
            return MappingProxyType({key: _freeze_json(item, active) for key, item in value.items()})
        finally:
            active.remove(identity)
    raise TypeError("record_payload must be an exact built-in JSON graph")


def thaw_frozen_json(value: object) -> object:
    """Restore a frozen binding payload to the standard graph accepted by bounded JCS."""
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is tuple:
        return tuple(thaw_frozen_json(item) for item in value)
    if type(value) is MappingProxyType:
        return {key: thaw_frozen_json(item) for key, item in value.items()}
    raise TypeError("value is not a frozen binding JSON graph")


@dataclass(frozen=True)
class FrozenGateEvaluationBinding:
    binding_id: str
    binding_version: str
    immutable_source_digest: DigestRef
    canonical_record_digest: DigestRef
    record_payload: Mapping[str, object]
    source_locator_id: str

    def __post_init__(self) -> None:
        for name in ("binding_id", "binding_version", "source_locator_id"):
            if type(getattr(self, name)) is not str or not getattr(self, name):
                raise ValueError(f"{name} must be a nonempty string")
        if not isinstance(self.immutable_source_digest, DigestRef):
            raise TypeError("immutable_source_digest must be DigestRef")
        if not isinstance(self.canonical_record_digest, DigestRef):
            raise TypeError("canonical_record_digest must be DigestRef")
        if type(self.record_payload) is not dict:
            raise TypeError("record_payload must be an exact built-in dict")
        required = {
            "candidate_id", "gate_definition_ref", "declared_member_id", "state",
            "supporting_evidence_ids", "counterevidence_ids", "conflict_relation_ids",
            "missing_paths", "conflict_paths", "unknown_paths", "reason_codes",
            "source_decision_ref",
        }
        if set(self.record_payload) != required:
            raise ValueError("record_payload must use the closed gate record schema")
        payload = _freeze_json(self.record_payload)
        if not isinstance(payload, Mapping):
            raise TypeError("record_payload must be a mapping")
        for name in ("candidate_id", "declared_member_id"):
            if type(payload[name]) is not str or not payload[name]:
                raise ValueError(f"record_payload.{name} must be a nonempty string")
        if payload["state"] not in ("SATISFIED", "MISSING", "CONFLICT", "UNKNOWN"):
            raise ValueError("record_payload.state is invalid")
        source_decision = payload["source_decision_ref"]
        if source_decision is not None and (type(source_decision) is not str or not source_decision):
            raise ValueError("record_payload.source_decision_ref must be null or a nonempty string")
        sequence_fields = (
            "supporting_evidence_ids", "counterevidence_ids", "conflict_relation_ids",
            "missing_paths", "conflict_paths", "unknown_paths", "reason_codes",
        )
        for name in sequence_fields:
            value = payload[name]
            if type(value) is not tuple or not all(type(item) is str and item for item in value):
                raise ValueError(f"record_payload.{name} must be a string sequence")
            if len(value) != len(set(value)):
                raise ValueError(f"record_payload.{name} must not contain duplicates")
        gate_ref = payload["gate_definition_ref"]
        gate_ref_fields = {
            "card_id", "contract_id", "contract_version", "field_path", "declared_state",
            "declared_value", "source_locator_id",
        }
        if type(gate_ref) is not MappingProxyType or set(gate_ref) != gate_ref_fields:
            raise ValueError("record_payload.gate_definition_ref must use the closed field-ref schema")
        for name in gate_ref_fields - {"declared_value"}:
            if type(gate_ref[name]) is not str or not gate_ref[name]:
                raise ValueError(f"record_payload.gate_definition_ref.{name} must be a nonempty string")
        if gate_ref["card_id"] != "F09":
            raise ValueError("record_payload.gate_definition_ref.card_id must be F09")
        if gate_ref["declared_state"] not in (
            "PRESENT_VALUE", "EXPLICIT_NULL", "LISTED_UNRESOLVED",
            "BOTH_NULL_AND_UNRESOLVED", "ABSENT",
        ):
            raise ValueError("record_payload.gate_definition_ref.declared_state is invalid")
        object.__setattr__(self, "record_payload", payload)


_PARTICIPATION_ROLES = frozenset({
    "SINGLE_SCHOOL_COMPLETE_NATAL_CHAIN",
    "DAIYUN_STAGE_EFFECT",
    "LIUNIAN_SPECIFIC_EVENT_TRIGGER",
    "REAL_WORLD_FUNCTION_GATE",
    "BREAK_CONDITION_OR_VALID_FALSIFIER",
    "SOURCE_GATE",
})
_PARTICIPATION_STATES = frozenset({"SATISFIED", "MISSING", "CONFLICT", "UNKNOWN", "NOT_APPLICABLE"})
_CONSTRAINT_CHECK_STATES = frozenset({"SATISFIED", "VIOLATED", "UNKNOWN", "NOT_APPLICABLE"})
_FIELD_REF_FIELDS = frozenset({
    "card_id", "contract_id", "contract_version", "field_path", "declared_state",
    "declared_value", "source_locator_id",
})
_CONSTRAINT_REF_FIELDS = frozenset({
    "card_id", "contract_id", "contract_version", "constraint_path", "source_locator_id",
})


def _validate_authority_envelope(binding: object) -> Mapping[str, object]:
    for name in ("binding_id", "binding_version", "source_locator_id"):
        value = getattr(binding, name)
        if type(value) is not str or not value:
            raise ValueError(f"{name} must be a nonempty string")
    for name in ("immutable_source_digest", "canonical_record_digest"):
        digest = getattr(binding, name)
        if type(digest) is not DigestRef:
            raise TypeError(f"{name} must be DigestRef")
        if type(digest.algorithm) is not str or not digest.algorithm:
            raise ValueError(f"{name}.algorithm must be a nonempty string")
        if type(digest.canonicalization) is not str or not digest.canonicalization:
            raise ValueError(f"{name}.canonicalization must be a nonempty string")
    canonical_digest = getattr(binding, "canonical_record_digest")
    if canonical_digest.algorithm != "sha256" or canonical_digest.canonicalization != "RFC8785-JCS-UTF8":
        raise ValueError("canonical_record_digest must use lowercase sha256 over RFC8785-JCS-UTF8")
    payload = getattr(binding, "record_payload")
    if type(payload) is not dict:
        raise TypeError("record_payload must be an exact built-in dict")
    frozen = _freeze_json(payload)
    if not isinstance(frozen, Mapping):
        raise TypeError("record_payload must be a mapping")
    return frozen


def _validate_string_tuple(payload: Mapping[str, object], name: str, *, nonempty: bool = False) -> tuple[str, ...]:
    value = payload[name]
    if type(value) is not tuple or not all(type(item) is str and item for item in value):
        raise ValueError(f"record_payload.{name} must be a string sequence")
    if nonempty and not value:
        raise ValueError(f"record_payload.{name} must be nonempty")
    if len(value) != len(set(value)):
        raise ValueError(f"record_payload.{name} must not contain duplicates")
    return value


def _validate_expanded_field_ref(value: object) -> None:
    if type(value) is not MappingProxyType or set(value) != _FIELD_REF_FIELDS:
        raise ValueError("frozen_definition_refs must contain closed field refs")
    for name in _FIELD_REF_FIELDS - {"declared_value"}:
        if type(value[name]) is not str or not value[name]:
            raise ValueError(f"frozen_definition_refs.{name} must be a nonempty string")
    if value["card_id"] != "F09":
        raise ValueError("frozen_definition_refs.card_id must be F09")
    if value["declared_state"] not in (
        "PRESENT_VALUE", "EXPLICIT_NULL", "LISTED_UNRESOLVED",
        "BOTH_NULL_AND_UNRESOLVED", "ABSENT",
    ):
        raise ValueError("frozen_definition_refs.declared_state is invalid")


@dataclass(frozen=True)
class FrozenParticipationRoleBinding:
    binding_id: str
    binding_version: str
    immutable_source_digest: DigestRef
    canonical_record_digest: DigestRef
    record_payload: Mapping[str, object]
    source_locator_id: str

    def __post_init__(self) -> None:
        payload = _validate_authority_envelope(self)
        required = {
            "participation_record_id", "participation_set_id", "role",
            "frozen_definition_refs", "state", "supporting_evidence_ids",
            "counterevidence_ids", "missing_issue_ids", "conflict_issue_ids",
            "unknown_issue_ids", "relation_ids", "source_decision_ref",
        }
        if set(payload) != required:
            raise ValueError("record_payload must use the closed participation role schema")
        for name in ("participation_record_id", "participation_set_id", "source_decision_ref"):
            if type(payload[name]) is not str or not payload[name]:
                raise ValueError(f"record_payload.{name} must be a nonempty string")
        if payload["role"] not in _PARTICIPATION_ROLES:
            raise ValueError("record_payload.role is invalid")
        if payload["state"] not in _PARTICIPATION_STATES:
            raise ValueError("record_payload.state is invalid")
        definition_refs = payload["frozen_definition_refs"]
        if type(definition_refs) is not tuple or not definition_refs:
            raise ValueError("record_payload.frozen_definition_refs must be a nonempty sequence")
        for ref in definition_refs:
            _validate_expanded_field_ref(ref)
        surfaces = {
            name: _validate_string_tuple(payload, name)
            for name in (
                "supporting_evidence_ids", "counterevidence_ids", "missing_issue_ids",
                "conflict_issue_ids", "unknown_issue_ids", "relation_ids",
            )
        }
        state = payload["state"]
        required_nonempty = {
            "SATISFIED": ("supporting_evidence_ids",),
            "MISSING": ("missing_issue_ids",),
            "CONFLICT": ("supporting_evidence_ids", "counterevidence_ids", "conflict_issue_ids", "relation_ids"),
            "UNKNOWN": ("unknown_issue_ids",),
            "NOT_APPLICABLE": (),
        }[state]
        required_empty = {
            "SATISFIED": ("missing_issue_ids", "conflict_issue_ids", "unknown_issue_ids"),
            "MISSING": ("supporting_evidence_ids", "conflict_issue_ids", "unknown_issue_ids"),
            "CONFLICT": ("missing_issue_ids", "unknown_issue_ids"),
            "UNKNOWN": ("missing_issue_ids", "conflict_issue_ids"),
            "NOT_APPLICABLE": tuple(surfaces),
        }[state]
        if any(not surfaces[name] for name in required_nonempty) or any(surfaces[name] for name in required_empty):
            raise ValueError("record_payload violates the participation state surface")
        object.__setattr__(self, "record_payload", payload)


@dataclass(frozen=True)
class FrozenRootTimingOutcomeBinding:
    binding_id: str
    binding_version: str
    immutable_source_digest: DigestRef
    canonical_record_digest: DigestRef
    record_payload: Mapping[str, object]
    source_locator_id: str

    def __post_init__(self) -> None:
        payload = _validate_authority_envelope(self)
        required = {
            "check_id", "constraint_ref", "root_entry_ids", "timing_entry_ids", "state",
            "source_decision_ref", "missing_paths", "conflict_paths", "unknown_paths", "reason_codes",
        }
        if set(payload) != required:
            raise ValueError("record_payload must use the closed root/timing outcome schema")
        for name in ("check_id", "source_decision_ref"):
            if type(payload[name]) is not str or not payload[name]:
                raise ValueError(f"record_payload.{name} must be a nonempty string")
        if payload["state"] not in _CONSTRAINT_CHECK_STATES:
            raise ValueError("record_payload.state is invalid")
        constraint_ref = payload["constraint_ref"]
        if type(constraint_ref) is not MappingProxyType or set(constraint_ref) != _CONSTRAINT_REF_FIELDS:
            raise ValueError("record_payload.constraint_ref must use the closed constraint-ref schema")
        for name in _CONSTRAINT_REF_FIELDS:
            if type(constraint_ref[name]) is not str or not constraint_ref[name]:
                raise ValueError(f"record_payload.constraint_ref.{name} must be a nonempty string")
        if constraint_ref["card_id"] != "F09":
            raise ValueError("record_payload.constraint_ref.card_id must be F09")
        surfaces = {
            name: _validate_string_tuple(payload, name, nonempty=name in ("root_entry_ids", "timing_entry_ids"))
            for name in (
                "root_entry_ids", "timing_entry_ids", "missing_paths", "conflict_paths",
                "unknown_paths", "reason_codes",
            )
        }
        state = payload["state"]
        required_nonempty = {
            "SATISFIED": (),
            "VIOLATED": ("conflict_paths", "reason_codes"),
            "UNKNOWN": ("unknown_paths", "reason_codes"),
            "NOT_APPLICABLE": ("reason_codes",),
        }[state]
        required_empty = {
            "SATISFIED": ("missing_paths", "conflict_paths", "unknown_paths", "reason_codes"),
            "VIOLATED": ("missing_paths", "unknown_paths"),
            "UNKNOWN": ("missing_paths", "conflict_paths"),
            "NOT_APPLICABLE": ("missing_paths", "conflict_paths", "unknown_paths"),
        }[state]
        if any(not surfaces[name] for name in required_nonempty) or any(surfaces[name] for name in required_empty):
            raise ValueError("record_payload violates the root/timing state surface")
        object.__setattr__(self, "record_payload", payload)


@dataclass(frozen=True)
class MarkdownContractSourceBinding:
    binding_kind: Literal["MARKDOWN_CONTRACT"]
    binding_schema_version: Literal["source-binding.markdown.v1"]
    source_snapshot_id: str
    source_schema_version: Literal["markdown-source.commonmark-0.31.2-mdff-v1"]
    contract_version: str
    content_digest: DigestRef
    captured_at: str

    def __post_init__(self) -> None:
        if self.binding_kind != "MARKDOWN_CONTRACT":
            raise ValueError("binding_kind must be MARKDOWN_CONTRACT")
        if self.binding_schema_version != "source-binding.markdown.v1":
            raise ValueError("invalid markdown binding_schema_version")
        if self.source_schema_version != "markdown-source.commonmark-0.31.2-mdff-v1":
            raise ValueError("invalid markdown source_schema_version")
        if not isinstance(self.content_digest, DigestRef):
            raise TypeError("content_digest must be DigestRef")
@dataclass(frozen=True)
class ImmutableJsonSourceBinding:
    binding_kind: Literal["IMMUTABLE_JSON_SNAPSHOT"]
    binding_schema_version: Literal["source-binding.immutable-json.v1"]
    source_snapshot_id: str
    source_schema_version: str
    contract_version: str
    content_digest: DigestRef
    captured_at: str

    def __post_init__(self) -> None:
        if self.binding_kind != "IMMUTABLE_JSON_SNAPSHOT":
            raise ValueError("binding_kind must be IMMUTABLE_JSON_SNAPSHOT")
        if self.binding_schema_version != "source-binding.immutable-json.v1":
            raise ValueError("invalid immutable-json binding_schema_version")
        if not isinstance(self.content_digest, DigestRef):
            raise TypeError("content_digest must be DigestRef")
@dataclass(frozen=True)
class UnversionedSourceBinding:
    binding_kind: Literal["UNVERSIONED_SOURCE"]
    binding_schema_version: Literal["source-binding.unversioned.v1"]
    reason_code: Literal["SOURCE_IDENTITY_NOT_VERSIONED"]

    def __post_init__(self) -> None:
        if self.binding_kind != "UNVERSIONED_SOURCE":
            raise ValueError("binding_kind must be UNVERSIONED_SOURCE")
        if self.binding_schema_version != "source-binding.unversioned.v1":
            raise ValueError("invalid unversioned binding_schema_version")
        if self.reason_code != "SOURCE_IDENTITY_NOT_VERSIONED":
            raise ValueError("invalid unversioned reason_code")
SourceBinding: TypeAlias = Union[MarkdownContractSourceBinding, ImmutableJsonSourceBinding, UnversionedSourceBinding]
@dataclass(frozen=True)
class SourceLocator:
    source_id: str
    source_type: Literal["INPUT_FIELD", "FINDING_OBJECT", "CLAIM_OBJECT", "DECISION_OBJECT", "STATEMENT_OBJECT", "FEEDBACK_OBJECT", "FROZEN_CONTRACT_FIELD", "DECLARATIVE_APPENDIX_FIELD", "THEORY_RULE", "HUMAN_ATTESTATION", "TRANSFORMATION_OUTPUT"]
    path: str
    object_id: str | None
    field_path: str | None
    binding: SourceBinding

    def __post_init__(self) -> None:
        if not isinstance(self.binding, (MarkdownContractSourceBinding, ImmutableJsonSourceBinding, UnversionedSourceBinding)):
            raise TypeError("binding must be a closed SourceBinding member")
@dataclass(frozen=True)
class FrozenDeclarationRef:
    declaration_id: str
    declaration_type: Literal["OUTPUT_PRECISION", "VALIDATION_PLAN"]
    card_id: Literal["F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08", "F09", "F10", "F11", "F12"]
    contract_version: str
    declaration_schema_version: str
    content_digest: DigestRef

    def __post_init__(self) -> None:
        if self.declaration_type not in ("OUTPUT_PRECISION", "VALIDATION_PLAN"):
            raise ValueError("invalid declaration_type")
        if self.card_id not in ("F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08", "F09", "F10", "F11", "F12"):
            raise ValueError("invalid card_id")
        if not isinstance(self.content_digest, DigestRef):
            raise TypeError("content_digest must be DigestRef")
@dataclass(frozen=True)
class ResolvedDeclarationBinding:
    presence: Literal["RESOLVED"]
    ref: FrozenDeclarationRef

    def __post_init__(self) -> None:
        if self.presence != "RESOLVED":
            raise ValueError("presence must be RESOLVED")
        if not isinstance(self.ref, FrozenDeclarationRef):
            raise TypeError("ref must be FrozenDeclarationRef")
@dataclass(frozen=True)
class AbsentDeclarationBinding:
    presence: Literal["ABSENT"]
    reason_code: Literal["DECLARATION_NOT_PRESENT"]

    def __post_init__(self) -> None:
        if self.presence != "ABSENT" or self.reason_code != "DECLARATION_NOT_PRESENT":
            raise ValueError("invalid ABSENT declaration binding")
@dataclass(frozen=True)
class NotApplicableDeclarationBinding:
    presence: Literal["NOT_APPLICABLE"]
    reason_code: Literal["DECLARATION_NOT_APPLICABLE"]

    def __post_init__(self) -> None:
        if self.presence != "NOT_APPLICABLE" or self.reason_code != "DECLARATION_NOT_APPLICABLE":
            raise ValueError("invalid NOT_APPLICABLE declaration binding")
@dataclass(frozen=True)
class UnavailableDeclarationBinding:
    presence: Literal["UNAVAILABLE"]
    reason_code: Literal["DECLARATION_UNREAD", "DECLARATION_SOURCE_UNAVAILABLE"]
    issue_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.presence != "UNAVAILABLE":
            raise ValueError("presence must be UNAVAILABLE")
        if self.reason_code not in ("DECLARATION_UNREAD", "DECLARATION_SOURCE_UNAVAILABLE"):
            raise ValueError("invalid UNAVAILABLE reason_code")
        if not isinstance(self.issue_ids, tuple) or not self.issue_ids:
            raise ValueError("issue_ids must be a nonempty tuple")
@dataclass(frozen=True)
class UnresolvableDeclarationBinding:
    presence: Literal["UNRESOLVABLE"]
    attempted_ref: FrozenDeclarationRef
    reason_code: Literal["IDENTITY_MISMATCH", "CONTRACT_VERSION_MISMATCH", "DECLARATION_SCHEMA_VERSION_MISMATCH", "DIGEST_MISMATCH", "BROKEN_REFERENCE"]
    issue_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.presence != "UNRESOLVABLE":
            raise ValueError("presence must be UNRESOLVABLE")
        if not isinstance(self.attempted_ref, FrozenDeclarationRef):
            raise TypeError("attempted_ref must be FrozenDeclarationRef")
        if self.reason_code not in ("IDENTITY_MISMATCH", "CONTRACT_VERSION_MISMATCH", "DECLARATION_SCHEMA_VERSION_MISMATCH", "DIGEST_MISMATCH", "BROKEN_REFERENCE"):
            raise ValueError("invalid UNRESOLVABLE reason_code")
        if not isinstance(self.issue_ids, tuple) or not self.issue_ids:
            raise ValueError("issue_ids must be a nonempty tuple")
FrozenDeclarationBinding: TypeAlias = Union[ResolvedDeclarationBinding, AbsentDeclarationBinding, NotApplicableDeclarationBinding, UnavailableDeclarationBinding, UnresolvableDeclarationBinding]
@dataclass(frozen=True)
class FrozenDeclarationPresenceBindings:
    output_precision_binding: FrozenDeclarationBinding
    validation_plan_binding: FrozenDeclarationBinding

    def __post_init__(self) -> None:
        members = (ResolvedDeclarationBinding, AbsentDeclarationBinding, NotApplicableDeclarationBinding, UnavailableDeclarationBinding, UnresolvableDeclarationBinding)
        if not isinstance(self.output_precision_binding, members):
            raise TypeError("output_precision_binding must be a closed FrozenDeclarationBinding member")
        if not isinstance(self.validation_plan_binding, members):
            raise TypeError("validation_plan_binding must be a closed FrozenDeclarationBinding member")
@dataclass(frozen=True)
class IntegrityIssue:
    issue_id: str
    code: str
    path: str
    message: str
    blocking: bool
@dataclass(frozen=True)
class DetectedIssue:
    issue_code: str
    field_path: str

    def __post_init__(self) -> None:
        if not isinstance(self.issue_code, str) or not self.issue_code.strip():
            raise ValueError("issue_code must be a nonempty string")
        if not isinstance(self.field_path, str) or not self.field_path.strip():
            raise ValueError("field_path must be a nonempty string")
@dataclass(frozen=True)
class ObjectRef:
    object_type: Literal["PACKAGE", "EVIDENCE", "RELATION", "CANDIDATE", "SOURCE_OBJECT", "FINDING", "CLAIM", "DECISION", "STATEMENT", "FEEDBACK", "CARD_FIELD"]
    object_id: str
    external: bool
    source_locator_id: str | None


@dataclass(frozen=True)
class RelationScope:
    function_id: FunctionId | None
    dimension: Literal[
        "primary_responsibility", "primary_action", "direct_object",
        "primary_deliverable", "primary_uncertainty", "stable_input",
        "strongest_competing_explanation",
    ] | None


@dataclass(frozen=True)
class TemporalPoint:
    value: str
    precision: Literal["YEAR", "MONTH", "DAY", "DATETIME", "AGE", "DAYUN_STEP", "TEXTUAL"]


@dataclass(frozen=True)
class TemporalInterval:
    start: TemporalPoint | None
    end: TemporalPoint | None
    start_inclusive: bool | None
    end_inclusive: bool | None


@dataclass(frozen=True)
class TemporalScope:
    mode: Literal["TIMELESS", "POINT", "INTERVAL", "AS_OF", "UNKNOWN"]
    point: TemporalPoint | None
    interval: TemporalInterval | None
    as_of: TemporalPoint | None
    source_precision: Literal["YEAR", "MONTH", "DAY", "DATETIME", "AGE", "DAYUN_STEP", "TEXTUAL", "UNKNOWN"]
    calendar: str | None
    timezone: str | None
    raw_expression: str | None


@dataclass(frozen=True)
class FieldMapping:
    source_field_path: str
    target_field_path: str
    operation: Literal["COPY", "RENAME", "TYPE_PRESERVING_PARSE", "STRUCTURAL_WRAP", "ENUM_EXACT_MAP", "TEXT_PRESERVE", "NO_MAP"]
    fidelity: Literal["LOSSLESS", "PARTIAL", "LOSSY", "UNSUPPORTED"]
@dataclass(frozen=True)
class TransformationRecord:
    transformation_id: str
    adapter_id: str
    adapter_version: str
    source_object_refs: tuple[ObjectRef, ...]
    target_object_refs: tuple[ObjectRef, ...]
    fidelity: Literal["LOSSLESS", "PARTIAL", "LOSSY", "UNSUPPORTED"]
    field_mappings: tuple[FieldMapping, ...]
    dropped_fields: tuple[str, ...]
    dropped_object_refs: tuple[ObjectRef, ...]
    synthesized_fields: tuple[str, ...]
    issues: tuple[str, ...]
    transformed_at: str

    def __post_init__(self) -> None:
        collections = (
            self.source_object_refs,
            self.target_object_refs,
            self.field_mappings,
            self.dropped_fields,
            self.dropped_object_refs,
            self.synthesized_fields,
            self.issues,
        )
        if any(not isinstance(value, tuple) for value in collections):
            raise TypeError("TransformationRecord collections must be tuples")


@dataclass(frozen=True)
class CompetitionDimensionRecord:
    dimension: Literal[
        "primary_responsibility", "primary_action", "direct_object",
        "primary_deliverable", "primary_uncertainty", "stable_input",
        "strongest_competing_explanation",
    ]
    evidence_ids: tuple[str, ...]
    counterevidence_ids: tuple[str, ...]
    comparison_state: Literal["UNOBSERVED", "PARTIAL", "READY_FOR_PI220", "DISPUTED"]


@dataclass(frozen=True)
class FunctionCandidate:
    candidate_id: str
    case_id: str
    function_id: FunctionId
    status: Literal["PROPOSED", "EVIDENCE_ATTACHED", "INCOMPLETE", "DISPUTED"]
    card_refs: tuple[FrozenCardFieldRef, ...]
    structure_evidence_ids: tuple[str, ...]
    reality_evidence_ids: tuple[str, ...]
    hypothesis_evidence_ids: tuple[str, ...]
    counterevidence_ids: tuple[str, ...]
    root_evidence_ids: tuple[str, ...]
    timing_evidence_ids: tuple[str, ...]
    competing_candidate_ids: tuple[str, ...]
    competition_dimensions: tuple[CompetitionDimensionRecord, ...]
    unresolved_fields: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.card_refs:
            raise ValueError("card_refs must be nonempty")
        collections = (
            self.card_refs, self.structure_evidence_ids, self.reality_evidence_ids,
            self.hypothesis_evidence_ids, self.counterevidence_ids,
            self.root_evidence_ids, self.timing_evidence_ids,
            self.competing_candidate_ids, self.competition_dimensions,
            self.unresolved_fields,
        )
        if any(not isinstance(value, tuple) for value in collections):
            raise TypeError("FunctionCandidate collections must be tuples")


@dataclass(frozen=True)
class EvidenceRelation:
    relation_id: str
    relation_type: Literal[
        "SUPPORTS", "COUNTERS", "CONTRADICTS", "COMPETES_WITH",
        "DERIVED_FROM", "CITES", "VERIFIES", "INVALIDATES",
        "HAS_ROOT_SIGNAL", "HAS_TIMING_SIGNAL", "COMPLETES_AT",
        "REFERS_TO_CARD_FIELD", "MAPS_FROM_SOURCE_OBJECT",
    ]
    from_ref: ObjectRef
    to_ref: ObjectRef
    scope: RelationScope
    source_refs: tuple[str, ...]
    status: Literal["ASSERTED", "OBSERVED", "PROPOSED", "DISPUTED"]
    temporal_scope: TemporalScope
    metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        if not self.source_refs:
            raise ValueError("source_refs must be nonempty")
        if not isinstance(self.source_refs, tuple):
            raise TypeError("source_refs must be a tuple")
        object.__setattr__(self, "metadata", _freeze_json(self.metadata))


IntegrityState: TypeAlias = Literal["READY", "INVALID", "BLOCKED"]


@runtime_checkable
class NormalizedEvidenceReadPort(Protocol):
    def get_package(self, package_id: str) -> "NormalizedEvidencePackage": ...
    def validate_for_pi220(self, package_id: str) -> IntegrityState: ...
    def get_candidate(self, candidate_id: str) -> FunctionCandidate: ...
    def list_candidates(self, case_id: str, function_ids: tuple[FunctionId, ...] | None = None) -> tuple[FunctionCandidate, ...]: ...
    def list_evidence(self, candidate_id: str, track: EvidenceTrack, kinds: tuple[str, ...] | None = None, as_of: str | None = None) -> tuple["EvidenceRecord", ...]: ...
    def list_counterevidence(self, candidate_id: str) -> tuple["EvidenceRecord", ...]: ...
    def get_card_field_ref(self, function_id: FunctionId, field_path: str) -> FrozenCardFieldRef: ...
    def get_unresolved_states(self, function_id: FunctionId) -> tuple[str, ...]: ...
    def get_validation_plan_binding(self, function_id: FunctionId) -> FrozenDeclarationBinding: ...
    def get_output_precision_binding(self, function_id: FunctionId) -> FrozenDeclarationBinding: ...
    def list_relations(self, object_id: str, relation_types: tuple[str, ...] | None = None) -> tuple[EvidenceRelation, ...]: ...
    def get_competition_dimensions(self, candidate_id: str) -> tuple[str, ...]: ...
    def get_gate_evaluation_binding(self, binding_id: str) -> FrozenGateEvaluationBinding: ...
    def get_participation_role_binding(self, binding_id: str) -> FrozenParticipationRoleBinding: ...
    def get_root_timing_outcome_binding(self, binding_id: str) -> FrozenRootTimingOutcomeBinding: ...


@runtime_checkable
class FrozenContractReadPort(Protocol):
    def get_field(self, ref: FrozenCardFieldRef) -> FrozenFieldObservation: ...
    def get_constraint_ref(self, function_id: FunctionId, constraint_path: str) -> FrozenConstraintRef: ...
    def verify_contract_version(self, ref: ContractVersionRef) -> ContractIntegrityResult: ...
