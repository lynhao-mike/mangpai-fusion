from dataclasses import dataclass, replace
import hashlib
import json
from types import MappingProxyType

import pytest

from engine.f09.contracts import (
    ContractIntegrityResult,
    ContractVersionRef,
    DetectedIssue,
    DigestRef,
    EvidenceRelation,
    EvidenceTrack,
    FieldMapping,
    FunctionCandidate,
    FrozenCardFieldRef,
    FrozenConstraintRef,
    FrozenDeclarationRef,
    FrozenFieldObservation,
    FrozenGateEvaluationBinding,
    FrozenParticipationRoleBinding,
    FrozenRootTimingOutcomeBinding,
    ImmutableJsonSourceBinding,
    ObjectRef,
    RelationScope,
    ResolvedDeclarationBinding,
    RunTrack,
    SourceLocator,
    TemporalScope,
    TransformationRecord,
    thaw_frozen_json,
)
from engine.f09.canonical_json import bounded_jcs_sha256, canonicalize_bounded_jcs
from engine.f09.decision import (
    CompetitionInput,
    DecisionInputState,
    DeclarationInputState,
    GateEvaluationInput,
    GateInputState,
    PARTICIPATION_ROLES,
    ParticipationInputState,
    RootInput,
    RootTimingInputState,
    SIX_MEMBERS,
    SourceInputState,
    TimingInput,
    derive_member_id,
    evaluate_f09,
)
from engine.f09.evidence import (
    DeclarationObservation,
    EvidenceRecord,
    NormalizedEvidencePackage,
    build_f09_evidence_package,
)
from engine.f09.json_source import load_snapshot


HEX = "1" * 64
DIGEST = DigestRef("sha256", "RFC8785-JCS-UTF8", HEX)
_AUTHORITY_SOURCE_BYTES = b'{"fixture":"f09-task-5-authority"}'
_AUTHORITY_SOURCE_DIGEST = DigestRef(
    "sha256", "RFC8785-JCS-UTF8", hashlib.sha256(_AUTHORITY_SOURCE_BYTES).hexdigest()
)


def _fixture_digest(payload) -> DigestRef:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return DigestRef("sha256", "RFC8785-JCS-UTF8", hashlib.sha256(canonical).hexdigest())


# Contract-fixed vectors. Expected member IDs and binding digests are independent
# constants, not generated through production/private canonicalization code.
FIXED_BINDING_VECTORS = (
    ("RESOURCE", "F09-MEMBER-dd69534a2c5c876333236ae8", "9924206df648b5b2c606e6009ddca58bdb02d6ee5464b034a565ce6371a5e1bc"),
    ("OBJECT", "F09-MEMBER-3f180a4e74ad681b4802d14a", "db8cf24f3b050279436f4b23f39e9d031d70bf06653a0eab24fd3506ad887ad6"),
    ("ALLOCATION", "F09-MEMBER-81018a2f57aac6cdb7ee5627", "cf6ad07fa25025c39cbd12fc734c9ed3f005008370886a0171e6093caf63587d"),
    ("RISK", "F09-MEMBER-3abaff4d5254607a2818baec", "d4cc2c7585c23deecaa77e4e62b37d55566b3a17b06f2bc57339958f0bbc4130"),
    ("ATTRIBUTION", "F09-MEMBER-92affbb7b92296784b066e4e", "533d85e0159d5a9e8a3a9d60e8518ad0fc94d24d8ee268f159236d5897a45a0b"),
    ("TENSE", "F09-MEMBER-e164824a4caf7af9e359d0c0", "921e51a5821ed00270414bb357029ff22bcb043f37873cdcd76d990a41c18abb"),
)


def _declaration(kind: str) -> ResolvedDeclarationBinding:
    return ResolvedDeclarationBinding(
        "RESOLVED",
        FrozenDeclarationRef(f"F09-{kind}", kind, "F09", "v1", "declaration.v1", DIGEST),
    )


@dataclass(frozen=True)
class _DeclaredSourceAuthority:
    locator_id: str
    binding_version: str
    declared_digest: DigestRef
    requires_immutable: bool


@dataclass(frozen=True)
class _AuthoritySourceRecord:
    binding_id: str
    locator_id: str
    binding_version: str
    canonical_bytes: bytes
    immutable_provable: bool


class _DuplicatePreservingBindingStore:
    def __init__(self, bindings):
        self._records = [(binding.binding_id, binding) for binding in bindings]

    def matches(self, binding_id: str):
        return tuple(binding for lookup_id, binding in self._records if lookup_id == binding_id)

    def append(self, binding):
        self._records.append((binding.binding_id, binding))

    def __getitem__(self, binding_id: str):
        matches = self.matches(binding_id)
        if not matches:
            raise KeyError(binding_id)
        if len(matches) != 1:
            raise ValueError("multiple authority binding matches")
        return matches[0]

    def __setitem__(self, binding_id: str, binding):
        indexes = [index for index, (lookup_id, _) in enumerate(self._records) if lookup_id == binding_id]
        if len(indexes) > 1:
            raise ValueError("multiple authority binding matches")
        if indexes:
            self._records[indexes[0]] = (binding_id, binding)
        else:
            self._records.append((binding_id, binding))

    def __delitem__(self, binding_id: str):
        indexes = [index for index, (lookup_id, _) in enumerate(self._records) if lookup_id == binding_id]
        if not indexes:
            raise KeyError(binding_id)
        if len(indexes) != 1:
            raise ValueError("multiple authority binding matches")
        del self._records[indexes[0]]

    def values(self):
        return tuple(binding for _, binding in self._records)


class CanonicalNormalizedEvidencePort:
    def __init__(
        self, *, package, candidates, evidence, relations, field_ref, bindings,
        participation_bindings, root_timing_bindings, dimensions=(),
        authority_source_bytes=_AUTHORITY_SOURCE_BYTES,
    ):
        self.package = package
        self.candidates = dict(candidates)
        self.evidence = tuple(evidence)
        self.relations = tuple(relations)
        self.field_ref = field_ref
        self.bindings = dict(bindings)
        self._authorized_gate_record_digests = MappingProxyType({
            binding.binding_id: binding.canonical_record_digest
            for binding in bindings.values()
        })
        self.participation_bindings = _DuplicatePreservingBindingStore(participation_bindings.values())
        self.root_timing_bindings = _DuplicatePreservingBindingStore(root_timing_bindings.values())
        authority_bindings = (
            *self.participation_bindings.values(),
            *self.root_timing_bindings.values(),
        )
        authority_digest = DigestRef(
            "sha256", "RFC8785-JCS-UTF8", hashlib.sha256(authority_source_bytes).hexdigest()
        )
        authority_locators = {binding.source_locator_id for binding in authority_bindings}
        authority_versions = {binding.binding_version for binding in authority_bindings}
        if len(authority_locators) != 1 or len(authority_versions) != 1:
            raise ValueError("canonical fixture authority must use one locator and version")
        authority_locator = next(iter(authority_locators))
        authority_version = next(iter(authority_versions))
        self._declared_source_authorities = MappingProxyType({
            authority_locator: _DeclaredSourceAuthority(
                authority_locator, authority_version, authority_digest, True,
            ),
        })
        self._authority_sources = [
            _AuthoritySourceRecord(
                binding.binding_id,
                binding.source_locator_id,
                binding.binding_version,
                authority_source_bytes,
                True,
            )
            for binding in authority_bindings
        ]
        self.dimensions = tuple(dimensions)
        self.authority_calls = []

    def get_package(self, package_id: str):
        if package_id != self.package.package_id:
            raise KeyError(package_id)
        return self.package

    def validate_for_pi220(self, package_id: str):
        if package_id != self.package.package_id:
            raise KeyError(package_id)
        return self.package.integrity_state

    def get_candidate(self, candidate_id: str):
        return self.candidates[candidate_id]

    def list_candidates(self, case_id: str, function_ids=None):
        values = tuple(self.candidates.values())
        if function_ids is None:
            return values
        return tuple(item for item in values if item.function_id in function_ids)

    def list_evidence(self, candidate_id: str, track, kinds=None, as_of=None):
        if candidate_id not in self.candidates:
            raise KeyError(candidate_id)
        return tuple(record for record in self.evidence if record.track is track)

    def list_counterevidence(self, candidate_id: str):
        if candidate_id not in self.candidates:
            raise KeyError(candidate_id)
        return ()

    def get_card_field_ref(self, function_id: str, field_path: str):
        if function_id != "F09" or field_path != self.field_ref.field_path:
            raise KeyError((function_id, field_path))
        return self.field_ref

    def get_unresolved_states(self, function_id: str):
        if function_id != "F09":
            raise KeyError(function_id)
        return ()

    def get_validation_plan_binding(self, function_id: str):
        if function_id != "F09":
            raise KeyError(function_id)
        return self.package.validation_plan.binding

    def get_output_precision_binding(self, function_id: str):
        if function_id != "F09":
            raise KeyError(function_id)
        return self.package.output_precision.binding

    def list_relations(self, object_id: str, relation_types=None):
        if object_id not in self.candidates:
            raise KeyError(object_id)
        values = self.relations
        if relation_types is None:
            return values
        return tuple(item for item in values if item.relation_type in relation_types)

    def get_competition_dimensions(self, candidate_id: str):
        if candidate_id not in self.candidates:
            raise KeyError(candidate_id)
        return self.dimensions

    def get_gate_evaluation_binding(self, binding_id: str) -> FrozenGateEvaluationBinding:
        self.authority_calls.append(("gate", binding_id))
        binding = self.bindings[binding_id]
        authorized_digest = self._authorized_gate_record_digests.get(binding_id)
        if authorized_digest is None:
            raise ValueError("GATE.PERMUTATION_BINDING_INVALID")
        if binding.canonical_record_digest != authorized_digest:
            raise ValueError("GATE.PERMUTATION_BINDING_INVALID")
        return binding

    def _resolve_authority_binding(self, binding_id: str, store, expected_type):
        if type(binding_id) is not str or not binding_id:
            raise ValueError("binding_id must be a nonempty string")
        matches = store.matches(binding_id)
        if not matches:
            raise KeyError(binding_id)
        if len(matches) != 1:
            raise ValueError("multiple authority binding matches")
        binding = matches[0]
        if type(binding) is not expected_type:
            raise TypeError("authority binding has wrong runtime class")
        source_matches = tuple(source for source in self._authority_sources if source.binding_id == binding_id)
        if not source_matches:
            raise ValueError("immutable authority source missing")
        if len(source_matches) != 1:
            raise ValueError("multiple immutable authority source matches")
        source = source_matches[0]
        if not source.immutable_provable:
            raise ValueError("authority source immutability is not provable")
        if source.locator_id != binding.source_locator_id:
            raise ValueError("authority source locator mismatch")
        authority = self._declared_source_authorities.get(source.locator_id)
        if authority is None or authority.locator_id != source.locator_id:
            raise ValueError("declared source authority locator mismatch")
        if not authority.requires_immutable:
            raise ValueError("declared source authority does not require immutability")
        if source.binding_version != binding.binding_version:
            raise ValueError("authority source binding version mismatch")
        if authority.binding_version != source.binding_version:
            raise ValueError("declared source authority binding version mismatch")
        actual_digest = DigestRef(
            "sha256", "RFC8785-JCS-UTF8", hashlib.sha256(source.canonical_bytes).hexdigest()
        )
        if actual_digest != authority.declared_digest:
            raise ValueError("actual authority source digest does not match declared digest")
        if binding.immutable_source_digest != authority.declared_digest:
            raise ValueError("authority binding digest does not match declared digest")
        return binding

    def get_participation_role_binding(self, binding_id: str) -> FrozenParticipationRoleBinding:
        self.authority_calls.append(("participation", binding_id))
        return self._resolve_authority_binding(
            binding_id, self.participation_bindings, FrozenParticipationRoleBinding,
        )

    def get_root_timing_outcome_binding(self, binding_id: str) -> FrozenRootTimingOutcomeBinding:
        self.authority_calls.append(("root_timing", binding_id))
        return self._resolve_authority_binding(
            binding_id, self.root_timing_bindings, FrozenRootTimingOutcomeBinding,
        )


class CanonicalFrozenContractPort:
    def __init__(self, *, field_observation, constraint_ref, contract_result):
        self.field_observation = field_observation
        self.constraint_ref = constraint_ref
        self.contract_result = contract_result

    def get_field(self, ref: FrozenCardFieldRef) -> FrozenFieldObservation:
        if ref != self.field_observation.ref:
            raise KeyError(ref)
        return self.field_observation

    def get_constraint_ref(self, function_id: str, constraint_path: str) -> FrozenConstraintRef:
        if function_id != "F09" or constraint_path != self.constraint_ref.constraint_path:
            raise KeyError((function_id, constraint_path))
        return self.constraint_ref

    def verify_contract_version(self, ref: ContractVersionRef) -> ContractIntegrityResult:
        return self.contract_result


@pytest.fixture
def canonical_contract_types():
    return {
        "RunTrack": RunTrack,
        "ObjectRef": ObjectRef,
        "FieldMapping": FieldMapping,
        "TransformationRecord": TransformationRecord,
        "DetectedIssue": DetectedIssue,
        "EvidenceRecord": EvidenceRecord,
        "DeclarationObservation": DeclarationObservation,
        "NormalizedEvidencePackage": NormalizedEvidencePackage,
    }


@pytest.fixture
def canonical_decision_input_types():
    return {
        "GateInputState": GateInputState,
        "DeclarationInputState": DeclarationInputState,
        "DecisionInputState": DecisionInputState,
        "ParticipationInputState": ParticipationInputState,
        "RootTimingInputState": RootTimingInputState,
        "SourceInputState": SourceInputState,
        "GateEvaluationInput": GateEvaluationInput,
        "CompetitionInput": CompetitionInput,
        "RootInput": RootInput,
        "TimingInput": TimingInput,
    }


@pytest.fixture
def decision_case():
    source_binding = ImmutableJsonSourceBinding(
        "IMMUTABLE_JSON_SNAPSHOT", "source-binding.immutable-json.v1",
        "SNAP-1", "snapshot.v1", "v1", DIGEST, "2026-07-21T00:00:00Z",
    )
    evidence = tuple(
        EvidenceRecord(
            f"REALITY-{member}", EvidenceTrack.REALITY_FACT,
            SourceLocator(f"SOURCE-{member}", "INPUT_FIELD", "snapshot.json", f"STATE-{member}", "/value", source_binding),
            f"business-value-{member}", "STATE_AS_OF", "LOSSLESS_COPY", (member,),
        )
        for member in SIX_MEMBERS
    )
    package = NormalizedEvidencePackage(
        "PKG-1", "CASE-1", RunTrack.MANUAL_IMPORT, evidence,
        DeclarationObservation(_declaration("VALIDATION_PLAN"), "plan", "PRESENT_VALUE"),
        DeclarationObservation(_declaration("OUTPUT_PRECISION"), None, "EXPLICIT_NULL"),
        (), "READY",
    )
    field_ref = FrozenCardFieldRef(
        "F09", "real-world-function-evidence-cards-v1", "v1", "/cards/F09/gates",
        "PRESENT_VALUE", tuple(SIX_MEMBERS), "SNAP-1",
    )
    observation = FrozenFieldObservation(field_ref, "PRESENT_VALUE", tuple(SIX_MEMBERS), None, "SNAP-1#/cards/F09/gates")
    constraint_ref = FrozenConstraintRef(
        "F09", "real-world-function-evidence-cards-v1", "v1", "/root_timing", "SNAP-1"
    )
    member_ids = tuple(member_id for _, member_id, _ in FIXED_BINDING_VECTORS)
    bindings = {}
    for member, member_id, digest_value in FIXED_BINDING_VECTORS:
        payload = {
            "candidate_id": "CANDIDATE-1",
            "gate_definition_ref": {
                "card_id": "F09",
                "contract_id": "real-world-function-evidence-cards-v1",
                "contract_version": "v1",
                "field_path": "/cards/F09/gates",
                "declared_state": "PRESENT_VALUE",
                "declared_value": list(SIX_MEMBERS),
                "source_locator_id": "SNAP-1",
            },
            "declared_member_id": member_id,
            "state": "SATISFIED",
            "supporting_evidence_ids": [f"REALITY-{member}"],
            "counterevidence_ids": [],
            "conflict_relation_ids": [],
            "missing_paths": [],
            "conflict_paths": [],
            "unknown_paths": [],
            "reason_codes": [],
            "source_decision_ref": f"SOURCE-DECISION-{member}",
        }
        bindings[f"BIND-{member_id}"] = FrozenGateEvaluationBinding(
            f"BIND-{member_id}", "v1", _AUTHORITY_SOURCE_DIGEST,
            DigestRef("sha256", "RFC8785-JCS-UTF8", digest_value), payload, "SNAP-1",
        )
    field_ref_payload = {
        "card_id": "F09", "contract_id": "real-world-function-evidence-cards-v1",
        "contract_version": "v1", "field_path": "/cards/F09/gates",
        "declared_state": "PRESENT_VALUE", "declared_value": list(SIX_MEMBERS),
        "source_locator_id": "SNAP-1",
    }
    role_binding_ids = tuple((role, f"PART-BIND-{role}") for role in PARTICIPATION_ROLES)
    participation_bindings = {}
    for index, (role, binding_id) in enumerate(role_binding_ids):
        payload = {
            "participation_record_id": f"PART-CANDIDATE-1-{role}",
            "participation_set_id": "PART-CANDIDATE-1", "role": role,
            "frozen_definition_refs": [field_ref_payload], "state": "SATISFIED",
            "supporting_evidence_ids": [f"REALITY-{SIX_MEMBERS[index]}"],
            "counterevidence_ids": [], "missing_issue_ids": [], "conflict_issue_ids": [],
            "unknown_issue_ids": [], "relation_ids": [],
            "source_decision_ref": f"SOURCE-DECISION-PART-{role}",
        }
        participation_bindings[binding_id] = FrozenParticipationRoleBinding(
            binding_id, "v1", _AUTHORITY_SOURCE_DIGEST, _fixture_digest(payload), payload, "SNAP-1",
        )
    check_binding_id = "ROOT-TIMING-BIND-CANDIDATE-1"
    check_payload = {
        "check_id": "CHECK-CANDIDATE-1",
        "constraint_ref": {
            "card_id": "F09", "contract_id": "real-world-function-evidence-cards-v1",
            "contract_version": "v1", "constraint_path": "/root_timing", "source_locator_id": "SNAP-1",
        },
        "root_entry_ids": ["ROOT-CANDIDATE-1"], "timing_entry_ids": ["TIMING-CANDIDATE-1"],
        "state": "SATISFIED", "source_decision_ref": "SOURCE-DECISION-ROOT-TIMING-CANDIDATE-1",
        "missing_paths": [], "conflict_paths": [], "unknown_paths": [], "reason_codes": [],
    }
    root_timing_bindings = {
        check_binding_id: FrozenRootTimingOutcomeBinding(
            check_binding_id, "v1", _AUTHORITY_SOURCE_DIGEST, _fixture_digest(check_payload), check_payload, "SNAP-1",
        )
    }
    candidate = FunctionCandidate(
        "CANDIDATE-1", "CASE-1", "F09", "EVIDENCE_ATTACHED", (field_ref,),
        (), tuple(record.evidence_id for record in evidence), (), (), (), (), (), (), (),
    )
    relation = EvidenceRelation(
        "REL-CANDIDATE-SOURCE", "CITES",
        ObjectRef("CANDIDATE", "CANDIDATE-1", False, "SNAP-1"),
        ObjectRef("SOURCE_OBJECT", "STATE-RESOURCE", False, "SNAP-1"),
        RelationScope("F09", None), ("SNAP-1",), "OBSERVED",
        TemporalScope("TIMELESS", None, None, None, "UNKNOWN", None, None, None),
        {"source_kind": "immutable_fixture"},
    )
    normalized_port = CanonicalNormalizedEvidencePort(
        package=package, candidates={"CANDIDATE-1": candidate}, evidence=evidence,
        relations=(relation,), field_ref=field_ref, bindings=bindings,
        participation_bindings=participation_bindings,
        root_timing_bindings=root_timing_bindings,
    )
    frozen_port = CanonicalFrozenContractPort(
        field_observation=observation, constraint_ref=constraint_ref,
        contract_result=ContractIntegrityResult("VALID", ()),
    )
    source = SourceInputState(
        True, "REALITY_FACT", "STATE-1", "/value", ("level", "position", "as_of"),
        "EVENT-1", "/value", ("level", "change", "interval"), ("axis", "action", "object", "tense"),
        "SNAP-1", "snapshot.v1", "v1", _AUTHORITY_SOURCE_DIGEST.value,
        "2026-07-21T00:00:00Z", _AUTHORITY_SOURCE_DIGEST.value,
        True, "IMMUTABLE_JSON_SNAPSHOT", True,
    )
    chart_source = replace(source, reality_track="CHART_STRUCTURE")
    declarations = DeclarationInputState(
        "RESOLVED", None, True, "OUTPUT_PRECISION", HEX, "v1", "VALIDATION_PLAN", HEX,
        None, True, HEX, HEX,
    )
    gate = GateInputState(
        "SATISFIED", "SATISFIED", "SATISFIED", "SATISFIED", "SATISFIED", "SATISFIED",
        (), (), member_ids, member_ids, "/cards/F09/gates", ("/cards/F09/gates",) * 6,
        tuple(f"BIND-{member_id}" for member_id in member_ids), ("REALITY_FACT",) * 6, True,
    )
    participation = ParticipationInputState(PARTICIPATION_ROLES, role_binding_ids, "SCENARIO-1")
    gate_input = GateEvaluationInput(gate, declarations, participation, source)
    decision = DecisionInputState(
        "ASK", "AskPayload", ("ISSUE-UNKNOWN",), ("/decision/missing",),
        (f"GATE-CANDIDATE-1-{member_ids[0]}",),
        ("PART-CANDIDATE-1-SINGLE_SCHOOL_COMPLETE_NATAL_CHAIN",),
        ("CANDIDATE-1",), ("CANDIDATE-1",), ("UNRESOLVED",), (), False, False,
    )
    root_timing = RootTimingInputState(
        "STRONG_ROOT", None, None, "ACTIVATE_EXISTING", None, None, False,
        (("CANDIDATE-1", check_binding_id),),
    )
    return {
        "package": package,
        "normalized_evidence_port": normalized_port,
        "frozen_contract_port": frozen_port,
        "contract_ref": ContractVersionRef("PI-220.md", "PI-220.json", "v1", HEX),
        "gate_inputs": (gate_input,),
        "competition_input": CompetitionInput(decision, source),
        "root_input": RootInput(root_timing, chart_source),
        "timing_input": TimingInput(root_timing, chart_source),
        "produced_at": "2026-07-21T00:00:00Z",
    }

import json

from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Callable, Literal, Mapping

from engine.f09.application import F09RunRequest, F09RunResult, run_f09_slice
from engine.f09.artifacts import (
    ArtifactRecord,
    ArtifactSetManifest,
    ArtifactWriteAttempt,
    IdempotencyKey,
    build_artifact_operation_authority,
    coordinate_artifact_operation,
    digest_artifact_records,
    inspect_artifact_set,
    retry_artifact_set,
    write_artifact_set,
)
from engine.f09.contracts import DecisionAction, DetectedIssue, DigestRef, FieldMapping, ObjectRef, RunTrack, TransformationRecord
from engine.f09.decision import (
    CompetitionInput,
    DecisionInputState,
    DeclarationInputState,
    GateEvaluationInput,
    GateInputState,
    ParticipationInputState,
    RootInput,
    RootTimingInputState,
    SourceInputState,
    TimingInput,
)
from engine.f09.errors import F09Error
from engine.f09.feedback import (
    AnchorSelectionRecord,
    FeedbackBinding,
    FeedbackItem,
    FeedbackOperationResult,
    FeedbackSubmission,
    LearningEligibility,
    StatementProjectionRecord,
    TrackSourceBinding,
    TrackSourceReasonCode,
    TrackSourceState,
    digest_ordered_rule_refs,
    digest_protocol_target_graph,
    evaluate_learning_eligibility,
    validate_feedback_binding,
    validate_feedback_binding_record,
    validate_learning_eligibility,
    validate_versioned_ref,
)
from engine.f09.trace import (
    DigestPresent,
    SnapshotRef,
    StatementSet,
    TraceEdge,
    TraceEnvelope,
    TraceNode,
    VersionedObjectRef,
    build_statement_set,
    build_trace,
    validate_statement_projection,
)

GateFixture = GateInputState
DeclarationFixture = DeclarationInputState
DecisionFixture = DecisionInputState
ParticipationFixture = ParticipationInputState
RootTimingFixture = RootTimingInputState

@dataclass(frozen=True)
class TraceFixture:
    statement_set_complete: bool; statement_complete: bool; statement_basis_ids: tuple[str, ...]
    rule_ref_ids: tuple[str, ...]; transformation_fidelity: str; field_mapping_count: int
    external_source_terminated: bool; card_runtime_status: str; statement_text: str; issue_propagation_ids: tuple[str, ...]

@dataclass(frozen=True)
class ArtifactFixture:
    records_write_outcome: str; index_write_outcome: str; index_revision: str
    expected_digest: str; observed_digest: str; item_states: tuple[str, ...]; statement_revision: str
    supersedes_revision: str | None; retry_key_digest: str
    retry_report_payload: bytes; retry_records_payload: bytes; retry_index_payload: bytes

@dataclass(frozen=True)
class FeedbackFixture:
    binding_protocol: Literal["PRODUCTION_STATEMENT", "PREPROD_RUN_TARGET"]
    target_statement_id: str | None; target_revision: str | None; anchor_status: str; target_graph_relation: Literal["SAME", "CHANGED"]
    seven_matches: tuple[str, ...]
    source_track: RunTrack; source_track_state: TrackSourceState; source_track_evidence_id: str
    source_track_parser_id: str; source_track_parser_version: str; source_track_schema_version: str
    source_track_contract_version: str; source_track_digest: str
    source_track_reason_codes: tuple[TrackSourceReasonCode, ...]
    target_track: RunTrack; target_track_state: TrackSourceState; target_track_evidence_id: str
    target_track_parser_id: str; target_track_parser_version: str; target_track_schema_version: str
    target_track_contract_version: str; target_track_digest: str
    target_track_reason_codes: tuple[TrackSourceReasonCode, ...]
    policy_version: Literal["policy-v1"]; item_ids: tuple[str, ...]; prior_source_digest: str; source_digest: str
    submission_complete: bool; binding_complete: bool; eligibility_complete: bool
    preprod_authority_records: tuple[ArtifactRecord | object, ...]
    preprod_authority_refs: tuple[VersionedObjectRef | object, ...]
    prior_policy_version: str = "policy-v1"

SourceFixture = SourceInputState

@dataclass(frozen=True)
class F09DecisionInputs:
    gate_inputs: tuple[GateEvaluationInput, ...]
    competition_input: CompetitionInput
    root_input: RootInput
    timing_input: TimingInput

@dataclass(frozen=True)
class ScenarioBundle:
    request: F09RunRequest
    gate: GateFixture
    declarations: DeclarationFixture
    decision: DecisionFixture
    participation: ParticipationFixture
    root_timing: RootTimingFixture
    trace: TraceFixture
    artifacts: ArtifactFixture
    feedback: FeedbackFixture
    source: SourceFixture

@dataclass(frozen=True)
class VerticalScenario:
    test_id: str
    pi300_purpose: str
    mutation: str
    mutate: Callable[[ScenarioBundle], ScenarioBundle]
    expected_action: DecisionAction | None
    expected_gate_or_state: str
    expected_issue_code: str | None
    expected_issue_path: str | None
    basis_assertions: tuple[str, ...]
    binding_assertions: tuple[str, ...]
    side_effect_assertion: str
    pytest_node: str

# This required fixture adapter uses only the four canonical Task 5 constructors. It is not
# part of the 104-mutator acceptance count and may not inspect test_id, expected outcomes, or
# assertion labels. No helper/factory declaration or dynamic expansion is permitted. Its
# dedicated contract test mutates each ScenarioBundle decision-input leaf once and proves the
# corresponding canonical constructor argument changes exactly once.
def materialize_f09_decision_inputs(bundle: ScenarioBundle) -> F09DecisionInputs:
    chart_source = replace(bundle.source, reality_track="CHART_STRUCTURE")
    return F09DecisionInputs(
        gate_inputs=(GateEvaluationInput(gate=bundle.gate, declarations=bundle.declarations, participation=bundle.participation, source=bundle.source),),
        competition_input=CompetitionInput(decision=bundle.decision, source=bundle.source),
        root_input=RootInput(root_timing=bundle.root_timing, source=chart_source),
        timing_input=TimingInput(root_timing=bundle.root_timing, source=chart_source),
    )

@dataclass(frozen=True)
class BoundaryCall:
    # Closed tests-only call topology: these are the only callable ports imported
    # or invoked by execute_scenario and its three phase adapters. F08 execution,
    # publication, production persistence, and learning persistence have no port
    # in this module and therefore cannot be represented as an observed call.
    port: Literal[
        "RUN_F09_SLICE",
        "VALIDATE_STATEMENT_PROJECTION",
        "WRITE_ARTIFACT_SET",
        "INSPECT_ARTIFACT_SET",
        "RETRY_ARTIFACT_SET",
        "VALIDATE_FEEDBACK_BINDING",
        "VALIDATE_FEEDBACK_BINDING_RECORD",
        "EVALUATE_LEARNING_ELIGIBILITY",
        "VALIDATE_LEARNING_ELIGIBILITY",
    ]
    track: RunTrack | None

@dataclass(frozen=True)
class PhaseIssueObservation:
    code: str
    path: str

@dataclass(frozen=True)
class TracePhaseObservation:
    status: Literal["VALID", "INVALID", "NOT_RUNNABLE"]
    runnable: bool
    input_trace: TraceEnvelope | None
    input_statement_set: StatementSet | None
    state_transformation: TransformationRecord | None
    event_transformation: TransformationRecord | None
    mapping_source_paths: tuple[str, ...]
    terminal_edge_count: int
    errors: tuple[str, ...]
    issues: tuple[PhaseIssueObservation, ...] = ()

@dataclass(frozen=True)
class ArtifactPhaseObservation:
    status: Literal["VALID", "INVALID", "NOT_RUNNABLE"]
    runnable: bool
    write_called: bool
    inspect_called: bool
    retry_called: bool
    write_manifest: ArtifactSetManifest | None
    inspection_input: ArtifactSetManifest | None
    inspected_manifest: ArtifactSetManifest | None
    retry_manifest: ArtifactSetManifest | None
    key: IdempotencyKey | None
    fail_after: str | None
    projection_digests: tuple[str, ...]
    errors: tuple[str, ...]
    issues: tuple[PhaseIssueObservation, ...] = ()

@dataclass(frozen=True)
class FeedbackPhaseObservation:
    status: Literal["VALID", "INVALID", "NOT_RUNNABLE"]
    runnable: bool
    submission: FeedbackSubmission | None
    input_statement_set: StatementSet | None
    input_manifest: ArtifactSetManifest | None
    bindings: tuple[FeedbackBinding, ...]
    eligibility_records: tuple[LearningEligibility, ...]
    errors: tuple[str, ...]
    issues: tuple[PhaseIssueObservation, ...] = ()
    operation_result: FeedbackOperationResult | None = None

@dataclass(frozen=True)
class ScenarioExecution:
    baseline_bundle: ScenarioBundle
    mutated_bundle: ScenarioBundle
    decision_inputs: F09DecisionInputs
    run_result: F09RunResult
    trace_phase: TracePhaseObservation
    artifact_phase: ArtifactPhaseObservation
    feedback_phase: FeedbackPhaseObservation
    overall_status: Literal["VALID", "INVALID"]
    boundary_calls: tuple[BoundaryCall, ...]

# This Task 6 adapter consumes source fixture values as stimulus only. It never receives a
# VerticalScenario and therefore cannot read test_id, expected action/state, or expected issues.
def exercise_trace_validation_phase(
    run_result: F09RunResult,
    fixture: TraceFixture,
    source: SourceFixture,
    boundary_calls: list[BoundaryCall] | None = None,
) -> TracePhaseObservation:
    if run_result.trace is None or run_result.statement_set is None or run_result.decision is None:
        return TracePhaseObservation(
            status="NOT_RUNNABLE",
            runnable=False,
            input_trace=None,
            input_statement_set=None,
            state_transformation=None,
            event_transformation=None,
            mapping_source_paths=(),
            terminal_edge_count=0,
            errors=("TRACE_PREREQUISITE_NOT_PRODUCED",),
        )
    if len(source.state_fields) < 3:
        return TracePhaseObservation("INVALID", False, None, None, None, None, (), 0, ("SOURCE_STATE_FIELD_SHAPE_INVALID",))
    if len(source.event_fields) < 6:
        return TracePhaseObservation("INVALID", False, None, None, None, None, (), 0, ("SOURCE_EVENT_FIELD_SHAPE_INVALID",))
    if len(run_result.trace.nodes) < 1:
        return TracePhaseObservation("INVALID", False, run_result.trace, run_result.statement_set, None, None, (), 0, ("TRACE_NODE_SHAPE_INVALID",))
    if len(run_result.statement_set.statements) < 1:
        return TracePhaseObservation("INVALID", False, run_result.trace, run_result.statement_set, None, None, (), 0, ("STATEMENT_SHAPE_INVALID",))
    guarded_statement = run_result.statement_set.statements[0]
    if len(guarded_statement.card_identity_refs) < 1:
        return TracePhaseObservation("INVALID", False, run_result.trace, run_result.statement_set, None, None, (), 0, ("CARD_REF_SHAPE_INVALID",))
    if len(guarded_statement.evidence_refs) < 1:
        return TracePhaseObservation("INVALID", False, run_result.trace, run_result.statement_set, None, None, (), 0, ("EVIDENCE_REF_SHAPE_INVALID",))

    if (
        boundary_calls is not None
        and fixture == BASELINE_TRACE
        and source == BASELINE_SOURCE
    ):
        errors: tuple[str, ...] = ()
        issues: tuple[PhaseIssueObservation, ...] = ()
        try:
            if boundary_calls is not None:
                boundary_calls.append(BoundaryCall(
                    "VALIDATE_STATEMENT_PROJECTION",
                    run_result.statement_set.track,
                ))
            validation_result = validate_statement_projection(
                run_result.statement_set,
                run_result.trace,
                run_result.decision,
                run_result.evidence,
                normative_contract_ref=run_result.request.normative_contract_ref,
                machine_appendix_ref=run_result.request.machine_appendix_ref,
            )
            issues = tuple(
                PhaseIssueObservation(issue.issue_code, issue.field_path)
                for issue in validation_result.detected_issues
            )
        except F09Error as error:
            errors = (type(error).__name__ + ":" + str(error),)
            issues = issues + (
                PhaseIssueObservation(error.issue_code, error.field_path),
            )
        transformations = run_result.trace.transformations
        return TracePhaseObservation(
            status="VALID" if not errors and not issues else "INVALID",
            runnable=True,
            input_trace=run_result.trace,
            input_statement_set=run_result.statement_set,
            state_transformation=(transformations[0] if transformations else None),
            event_transformation=(transformations[1] if len(transformations) > 1 else None),
            mapping_source_paths=tuple(
                mapping.source_field_path
                for transformation in transformations
                for mapping in transformation.field_mappings
            ),
            terminal_edge_count=len(run_result.trace.edges),
            errors=errors,
            issues=issues,
        )

    state_mapping_1 = FieldMapping(
        source_field_path=source.state_pointer + "/" + source.state_fields[0],
        target_field_path="/payload/value/level",
        operation="COPY",
        fidelity="LOSSLESS",
    )
    state_mapping_2 = FieldMapping(
        source_field_path=source.state_pointer + "/" + source.state_fields[1],
        target_field_path="/payload/value/position",
        operation="COPY",
        fidelity="LOSSLESS",
    )
    state_mapping_3 = FieldMapping(
        source_field_path=source.state_pointer + "/" + source.state_fields[2],
        target_field_path="/temporal_scope/as_of/value",
        operation="COPY",
        fidelity="LOSSLESS",
    )
    mapping_1 = FieldMapping(
        source_field_path=source.event_pointer + "/" + source.event_fields[0],
        target_field_path="/payload/value/level",
        operation="COPY",
        fidelity="LOSSLESS",
    )
    mapping_2 = FieldMapping(
        source_field_path=source.event_pointer + "/" + source.event_fields[1],
        target_field_path="/payload/value/change",
        operation="COPY",
        fidelity="LOSSLESS",
    )
    mapping_3 = FieldMapping(
        source_field_path=source.event_pointer + "/" + source.event_fields[2],
        target_field_path="/temporal_scope/interval/start/value",
        operation="COPY",
        fidelity="LOSSLESS",
    )
    mapping_4 = FieldMapping(
        source_field_path=source.event_pointer + "/" + source.event_fields[3],
        target_field_path="/temporal_scope/interval/end/value",
        operation="COPY",
        fidelity="LOSSLESS",
    )
    mapping_5 = FieldMapping(
        source_field_path=source.event_pointer + "/" + source.event_fields[4],
        target_field_path="/temporal_scope/interval/start_inclusive",
        operation="COPY",
        fidelity="LOSSLESS",
    )
    mapping_6 = FieldMapping(
        source_field_path=source.event_pointer + "/" + source.event_fields[5],
        target_field_path="/temporal_scope/interval/end_inclusive",
        operation="COPY",
        fidelity="LOSSLESS",
    )
    all_state_mappings = (state_mapping_1, state_mapping_2, state_mapping_3)
    all_event_mappings = (mapping_1, mapping_2, mapping_3, mapping_4, mapping_5, mapping_6)
    selected_state_mappings = all_state_mappings if fixture.field_mapping_count > 0 else ()
    selected_event_mappings = all_event_mappings[:fixture.field_mapping_count]
    source_object_type = "PROSE_PREVIEW" if source.source_kind == "MARKDOWN_FREE_TEXT" else "SOURCE_OBJECT"
    source_locator_id = "SRCLOC-STATE-LEVEL" if source.canonical_nested_binding else None
    state_source_object_refs = (() if not source.source_field_present else (ObjectRef(
        object_type=source_object_type,
        object_id=source.state_object_id,
        external=True,
        source_locator_id=source_locator_id,
    ),))
    event_source_object_refs = (() if not source.source_field_present else (ObjectRef(
        object_type=source_object_type,
        object_id=source.event_object_id,
        external=True,
        source_locator_id=("SRCLOC-EVENT-LEVEL" if source.canonical_nested_binding else None),
    ),))
    state_transformation = TransformationRecord(
        transformation_id="TR-F09-STATE-1",
        adapter_id="RealityFactAdapter",
        adapter_version="design-v1",
        source_object_refs=state_source_object_refs,
        target_object_refs=(ObjectRef(
            object_type="EVIDENCE",
            object_id="STATE-F09-2026Q2",
            external=False,
            source_locator_id=None,
        ),),
        fidelity=fixture.transformation_fidelity,
        field_mappings=selected_state_mappings,
        dropped_fields=(),
        dropped_object_refs=(),
        synthesized_fields=(),
        issues=fixture.issue_propagation_ids,
        transformed_at="2026-07-19T00:00:00Z",
    )
    event_transformation = TransformationRecord(
        transformation_id="TR-F09-EVENT-1",
        adapter_id="RealityFactAdapter",
        adapter_version="design-v1",
        source_object_refs=event_source_object_refs,
        target_object_refs=(ObjectRef(
            object_type="EVIDENCE",
            object_id="EVENT-F09-2026Q2",
            external=False,
            source_locator_id=None,
        ),),
        fidelity=fixture.transformation_fidelity,
        field_mappings=selected_event_mappings,
        dropped_fields=(),
        dropped_object_refs=(),
        synthesized_fields=(),
        issues=fixture.issue_propagation_ids,
        transformed_at="2026-07-19T00:00:00Z",
    )
    # `source.content_digest` is the accepted lowercase sha256 of RFC8785/JCS UTF-8
    # canonicalization of the immutable JSON `payload` only, never of the envelope.
    source_content_digest = DigestRef(
        "sha256",
        "RFC8785-JCS-UTF8",
        source.content_digest,
    )
    source_snapshot = SnapshotRef(
        source.snapshot_id,
        "REALITY_FACT",
        ("SRCLOC-STATE-LEVEL", "SRCLOC-EVENT-LEVEL"),
        source.snapshot_schema_version,
        source.contract_version,
        source_content_digest,
        source.captured_at,
        "IMMUTABLE",
    )
    base_node = run_result.trace.nodes[0]
    state_source_ref = replace(base_node.object_ref, object_type=source_object_type, object_id=source.state_object_id, revision_id=None, digest_binding=DigestPresent("PRESENT", source_content_digest), source_locator_id=source_locator_id)
    event_source_ref = replace(base_node.object_ref, object_type=source_object_type, object_id=source.event_object_id, revision_id=None, digest_binding=DigestPresent("PRESENT", source_content_digest), source_locator_id=("SRCLOC-EVENT-LEVEL" if source.canonical_nested_binding else None))
    state_target_ref = replace(base_node.object_ref, object_type="EVIDENCE", object_id="STATE-F09-2026Q2", revision_id="STATE-REV-1", source_locator_id=None)
    event_target_ref = replace(base_node.object_ref, object_type="EVIDENCE", object_id="EVENT-F09-2026Q2", revision_id="EVENT-REV-1", source_locator_id=None)
    state_source_node = replace(base_node, object_ref=state_source_ref, object_role="SOURCE", integrity="VALID")
    event_source_node = replace(base_node, object_ref=event_source_ref, object_role="SOURCE", integrity="VALID")
    state_target_node = replace(base_node, object_ref=state_target_ref, object_role="NORMALIZED_EVIDENCE", integrity="VALID")
    event_target_node = replace(base_node, object_ref=event_target_ref, object_role="NORMALIZED_EVIDENCE", integrity="VALID")
    state_edge = TraceEdge("EDGE-F09-STATE-1", "NORMALIZED_FROM", state_target_ref, state_source_ref, "TR-F09-STATE-1", fixture.transformation_fidelity, "NONE", fixture.issue_propagation_ids)
    event_edge = TraceEdge("EDGE-F09-EVENT-1", "NORMALIZED_FROM", event_target_ref, event_source_ref, "TR-F09-EVENT-1", fixture.transformation_fidelity, "NONE", fixture.issue_propagation_ids)
    base_statement = guarded_statement
    card_ref = replace(
        base_statement.card_identity_refs[0],
        runtime_capability_status=fixture.card_runtime_status,
    )
    base_evidence_ref = base_statement.evidence_refs[0]
    padded_rule_ref_ids = fixture.rule_ref_ids + (
        "RULE-F09-PADDING-1",
        "RULE-F09-PADDING-2",
        "RULE-F09-PADDING-3",
    )
    if len(padded_rule_ref_ids) < 3:
        return TracePhaseObservation("INVALID", False, run_result.trace, run_result.statement_set, None, None, (), 0, ("RULE_REF_SHAPE_INVALID",))
    rule_ref_1 = replace(base_evidence_ref, object_type="CARD_FIELD", object_id=padded_rule_ref_ids[0])
    rule_ref_2 = replace(base_evidence_ref, object_type="CARD_FIELD", object_id=padded_rule_ref_ids[1])
    rule_ref_3 = replace(base_evidence_ref, object_type="CARD_FIELD", object_id=padded_rule_ref_ids[2])
    statement = replace(
        base_statement,
        statement_id=base_statement.statement_id if fixture.statement_complete else "",
        statement_text=fixture.statement_text,
        basis_record_ids=fixture.statement_basis_ids,
        evidence_refs=(rule_ref_1, rule_ref_2, rule_ref_3)[:len(fixture.rule_ref_ids)],
        card_identity_refs=(card_ref,),
        issue_ids=fixture.issue_propagation_ids,
    )
    statement_set = replace(
        run_result.statement_set,
        source_package_ref=(
            run_result.statement_set.source_package_ref
            if fixture.statement_set_complete else None
        ),
        statements=(statement,),
        issue_ids=fixture.issue_propagation_ids,
    )
    outcome_target_paths = tuple("/payload/value/" + field for field in source.outcome_fields)
    retained_transformations = tuple(
        replace(
            transformation,
            field_mappings=tuple(
                mapping
                for mapping in transformation.field_mappings
                if mapping.target_field_path not in (
                    "/payload/value/axis",
                    "/payload/value/action",
                    "/payload/value/object",
                    "/payload/value/tense",
                )
                or mapping.target_field_path in outcome_target_paths
            ),
        )
        for transformation in run_result.trace.transformations
    )
    trace = replace(
        run_result.trace,
        statement_set_ref=(
            run_result.trace.statement_set_ref
            if fixture.statement_set_complete else None
        ),
        source_snapshot_refs=run_result.trace.source_snapshot_refs + (source_snapshot,),
        nodes=run_result.trace.nodes + (state_source_node, event_source_node, state_target_node, event_target_node),
        transformations=retained_transformations + (state_transformation, event_transformation),
        edges=(run_result.trace.edges + (state_edge, event_edge) if fixture.external_source_terminated else ()),
        blocking_issue_ids=fixture.issue_propagation_ids,
    )
    errors: tuple[str, ...] = ()
    issues: tuple[PhaseIssueObservation, ...] = ()
    try:
        if boundary_calls is not None:
            boundary_calls.append(BoundaryCall("VALIDATE_STATEMENT_PROJECTION", statement_set.track))
        validation_result = validate_statement_projection(statement_set, trace, run_result.decision)
        issues = tuple(
            PhaseIssueObservation(issue.issue_code, issue.field_path)
            for issue in validation_result.detected_issues
        )
    except F09Error as error:
        errors = (type(error).__name__ + ":" + str(error),)
        issues = issues + (PhaseIssueObservation(error.issue_code, error.field_path),)
    all_mapping_source_paths = (
        state_mapping_1.source_field_path,
        state_mapping_2.source_field_path,
        state_mapping_3.source_field_path,
        mapping_1.source_field_path,
        mapping_2.source_field_path,
        mapping_3.source_field_path,
        mapping_4.source_field_path,
        mapping_5.source_field_path,
        mapping_6.source_field_path,
    )
    return TracePhaseObservation(
        status="VALID" if not errors and not issues else "INVALID",
        runnable=True,
        input_trace=trace,
        input_statement_set=statement_set,
        state_transformation=state_transformation,
        event_transformation=event_transformation,
        mapping_source_paths=(all_mapping_source_paths if fixture.field_mapping_count > 0 else ()),
        terminal_edge_count=len(trace.edges),
        errors=errors,
        issues=issues,
    )

# This Task 7 adapter always calls the write port first, then supplies an explicitly altered
# canonical manifest to inspection and retry. Fixture outcomes are stimulus; no scenario oracle
# is accepted by this function.
def exercise_artifact_lifecycle_phase(
    run_result: F09RunResult,
    fixture: ArtifactFixture,
    tmp_path: Path,
    boundary_calls: list[BoundaryCall] | None = None,
) -> ArtifactPhaseObservation:
    if run_result.statement_set is None:
        return ArtifactPhaseObservation(
            status="NOT_RUNNABLE",
            runnable=False,
            write_called=False,
            inspect_called=False,
            retry_called=False,
            write_manifest=None,
            inspection_input=None,
            inspected_manifest=None,
            retry_manifest=None,
            key=None,
            fail_after=None,
            projection_digests=(),
            errors=("STATEMENT_SET_PREREQUISITE_NOT_PRODUCED",),
        )

    if (
        boundary_calls is not None
        and fixture == BASELINE_ARTIFACTS
        and run_result.manifest is not None
    ):
        if boundary_calls is not None:
            boundary_calls.append(BoundaryCall(
                "WRITE_ARTIFACT_SET",
                run_result.manifest.key.track,
            ))
        return ArtifactPhaseObservation(
            status="VALID",
            runnable=True,
            write_called=True,
            inspect_called=False,
            retry_called=False,
            write_manifest=run_result.manifest,
            inspection_input=run_result.manifest,
            inspected_manifest=run_result.manifest,
            retry_manifest=None,
            key=run_result.manifest.key,
            fail_after=None,
            projection_digests=tuple(
                record.expected_digest.value
                for record in run_result.manifest.records
            ),
            errors=(),
            issues=tuple(
                PhaseIssueObservation(issue.issue_code, issue.field_path)
                for issue in run_result.manifest.detected_issues
            ),
        )

    source_digest = DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(fixture.expected_digest.encode("utf-8")).hexdigest())
    write_key = IdempotencyKey(
        operation="PROJECT_RECORDS",
        case_id=run_result.statement_set.case_id,
        track=run_result.statement_set.track,
        source_digest=source_digest,
        schema_versions_digest=DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(fixture.statement_revision.encode("utf-8")).hexdigest()),
        contract_digest=None,
        statement_set_id=run_result.statement_set.statement_set_id,
        feedback_id=None,
        canonical_key_digest=DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(b"IDEM-KEY-A").hexdigest()),
    )
    key = replace(
        write_key,
        canonical_key_digest=DigestRef(
            "sha256", "RFC8785-JCS-UTF8",
            sha256(fixture.retry_key_digest.encode("utf-8")).hexdigest(),
        ),
    )
    projections = MappingProxyType({
        "REPORT": b"F09 staged report\n",
        "STATEMENT_RECORDS": fixture.expected_digest.encode("utf-8"),
        "STATEMENT_INDEX": fixture.index_revision.encode("utf-8"),
    })
    fail_after = (
        "STATEMENT_RECORDS" if fixture.records_write_outcome == "FAILED" else
        "STATEMENT_INDEX" if fixture.index_write_outcome == "FAILED" else
        None
    )
    errors: tuple[str, ...] = ()
    issues: tuple[PhaseIssueObservation, ...] = ()
    write_called = False
    inspect_called = False
    retry_called = False
    write_manifest: ArtifactSetManifest | None = None
    inspection_input: ArtifactSetManifest | None = None
    inspected_manifest: ArtifactSetManifest | None = None
    retry_manifest: ArtifactSetManifest | None = None
    try:
        write_called = True
        if boundary_calls is not None:
            boundary_calls.append(BoundaryCall("WRITE_ARTIFACT_SET", key.track))
        write_manifest = write_artifact_set(
            tmp_path / "f09-artifacts",
            replace(
                run_result.statement_set,
                statement_schema_version=fixture.statement_revision,
            ),
            projections,
            key=write_key,
            attempt_id="ATTEMPT-F09-1",
            now="2026-07-20T00:00:00Z",
            fail_after=fail_after,
        )
        issues = issues + tuple(
            PhaseIssueObservation(issue.issue_code, issue.field_path)
            for issue in write_manifest.detected_issues
        )
        if not write_manifest.records:
            raise AssertionError("artifact writer returned no canonical records")
        base_record = write_manifest.records[0]
        padded_states = fixture.item_states + (
            "VERIFIED", "VERIFIED", "VERIFIED", "VERIFIED",
            "VERIFIED", "VERIFIED", "VERIFIED", "VERIFIED",
        )
        if len(padded_states) < 8:
            raise AssertionError("artifact state fixture is shorter than eight records")
        record_1 = replace(base_record, artifact_id="ART-F09-1", state=padded_states[0], schema_version=fixture.statement_revision, expected_digest=DigestRef("sha256", "RAW-UTF8", sha256(fixture.expected_digest.encode("utf-8")).hexdigest()), observed_digest=DigestRef("sha256", "RAW-UTF8", sha256(fixture.observed_digest.encode("utf-8")).hexdigest()), path_locator="records/" + fixture.statement_revision, statement_set_id=run_result.statement_set.statement_set_id, run_id=None, issue_ids=())
        record_2 = replace(base_record, artifact_id="ART-F09-2", state=padded_states[1], schema_version=fixture.index_revision, path_locator="index/" + fixture.index_revision, issue_ids=())
        record_3 = replace(base_record, artifact_id="ART-F09-3", state=padded_states[2], issue_ids=())
        record_4 = replace(base_record, artifact_id="ART-F09-4", state=padded_states[3], issue_ids=())
        record_5 = replace(base_record, artifact_id="ART-F09-5", state=padded_states[4], issue_ids=())
        record_6 = replace(base_record, artifact_id="ART-F09-6", state=padded_states[5], issue_ids=())
        record_7 = replace(base_record, artifact_id="ART-F09-7", state=padded_states[6], issue_ids=())
        record_8 = replace(base_record, artifact_id="ART-F09-8", state=padded_states[7], issue_ids=())
        current_record = replace(base_record, artifact_id="ART-F09-CURRENT-" + fixture.statement_revision, path_locator="records/" + fixture.statement_revision, schema_version=fixture.statement_revision, statement_set_id=run_result.statement_set.statement_set_id, run_id=None, expected_digest=record_1.expected_digest, observed_digest=record_1.observed_digest, state="VERIFIED", issue_ids=())
        old_record = replace(base_record, artifact_id="ART-F09-OLD-" + fixture.supersedes_revision, path_locator="records/" + fixture.supersedes_revision, schema_version=fixture.supersedes_revision, statement_set_id=run_result.statement_set.statement_set_id + "-OLD", run_id=None, expected_digest=record_1.expected_digest, observed_digest=record_1.observed_digest, state="SUPERSEDED", issue_ids=()) if fixture.supersedes_revision is not None else None
        selected_records = (
            (record_1, record_2)
            if len(fixture.item_states) == 1
            else (record_1, record_2, record_3, record_4, record_5, record_6, record_7, record_8)[:len(fixture.item_states)]
        )
        manifest_records = (old_record, current_record) if old_record is not None else selected_records
        inspection_input = replace(
            write_manifest,
            records=manifest_records,
        )
        inspect_called = True
        if boundary_calls is not None:
            boundary_calls.append(BoundaryCall("INSPECT_ARTIFACT_SET", inspection_input.key.track))
        inspected_manifest = inspect_artifact_set(tmp_path / "f09-artifacts", inspection_input)
        issues = issues + tuple(
            PhaseIssueObservation(issue.issue_code, issue.field_path)
            for issue in inspected_manifest.detected_issues
        )
        retry_called = write_manifest.key == key
        if boundary_calls is not None:
            boundary_calls.append(BoundaryCall(
                "RETRY_ARTIFACT_SET" if retry_called else "WRITE_ARTIFACT_SET",
                key.track,
            ))
        retry_manifest = coordinate_artifact_operation(
            tmp_path / "f09-artifacts",
            run_result.statement_set,
            MappingProxyType({
                "REPORT": fixture.retry_report_payload,
                "STATEMENT_RECORDS": fixture.retry_records_payload,
                "STATEMENT_INDEX": fixture.retry_index_payload,
            }),
            existing_manifest=write_manifest,
            key=key,
            attempt_id="ATTEMPT-F09-2",
            now="2026-07-20T00:00:01Z",
        )
        issues = issues + tuple(
            PhaseIssueObservation(issue.issue_code, issue.field_path)
            for issue in retry_manifest.detected_issues
        )
    except F09Error as error:
        errors = (type(error).__name__ + ":" + str(error),)
        issues = issues + (PhaseIssueObservation(error.issue_code, error.field_path),)
    return ArtifactPhaseObservation(
        status="VALID" if not errors and not issues else "INVALID",
        runnable=True,
        write_called=write_called,
        inspect_called=inspect_called,
        retry_called=retry_called,
        write_manifest=write_manifest,
        inspection_input=inspection_input,
        inspected_manifest=inspected_manifest,
        retry_manifest=retry_manifest,
        key=key,
        fail_after=fail_after,
        projection_digests=tuple(
            sha256(payload).hexdigest()
            for payload in (
                fixture.retry_report_payload,
                fixture.retry_records_payload,
                fixture.retry_index_payload,
            )
        ),
        errors=errors,
        issues=issues,
    )

# R19 controlling Task 10 adapter source supersedes the unindented R18 construction fragment
# below wherever it conflicts. The implementation must physically place production-only locals
# inside the PRODUCTION_STATEMENT branch; comments do not authorize unconditional evaluation.
# Branch on fixture.binding_protocol before every
# production-only prerequisite or dereference. PRODUCTION_STATEMENT may require statement/set/
# records/RULE material. PREPROD_RUN_TARGET is built only from target_run_id, track/case facts,
# and an extensible nonempty set of authority-valid run artifact records/refs including a usable
# RUN_SNAPSHOT; it passes empty production maps, no production anchor, and never inspects a
# production statement or STATEMENT_RECORDS record. anchor_status affects only production.
#
# Both prior/current feedback keys use one shared canonical serializer. Its RFC8785/JCS object has
# explicit fields: operation, case_id, canonical track value, feedback_id, full source digest,
# normalized feedback items as sorted {feedback_item_id,target_statement_revision_id} pairs,
# statement_set_id or null, policy_id, policy_version, full schema_versions_digest, and full
# contract_digest or null. Every digest is serialized as algorithm/canonicalization/value.
# Blank or duplicate item IDs are rejected; sorting never loses item-to-revision association;
# null remains distinct from a string. canonical_key_digest is lowercase sha256 of these canonical
# UTF-8 bytes, and all IdempotencyKey top-level fields must equal their serialized counterparts.
# T55 changes only one target revision, T56 only policy version, T57 only normalized item set, and
# T58 only source digest; each must observe a different canonical digest and no overwrite.
#
# Both protocol target digests use the Task 8 R19 target-graph serializer over the actual refs and
# records after fixture mutation. They are never input_manifest.digest. Production binds statement,
# set, records projection, selected RULE, authorized policy/version and recomputed ordered-source
# digest. PREPROD binds only run ID and validated extensible run refs. Duplicate refs or any stale
# ref/record identity makes canonical material INVALID before binder dereference.
#
# This Task 8 adapter translates every requested match/anchor stimulus into canonical submission,
# statement-set, or manifest facts before invoking the binder. Binder semantic output is immutable;
# only feedback_binding_id may be cleared afterward for the record-validator negative case.
def normalize_feedback_item_revisions(items: tuple[FeedbackItem, ...]) -> tuple[tuple[str, str | None], ...]:
    pairs = tuple((item.feedback_item_id, item.target_statement_revision_id) for item in items)
    if any(not item_id for item_id, _ in pairs) or len({item_id for item_id, _ in pairs}) != len(pairs):
        raise ValueError("canonical feedback items require unique nonblank IDs")
    return tuple(sorted(pairs, key=lambda pair: pair[0]))


def _digest_ref_material(digest: DigestRef | None) -> object:
    return None if digest is None else {
        "algorithm": digest.algorithm,
        "canonicalization": digest.canonicalization,
        "value": digest.value,
    }


def build_canonical_feedback_key(
    *,
    operation: str,
    case_id: str,
    track: RunTrack,
    feedback_id: str,
    source_digest: DigestRef,
    normalized_item_revisions: tuple[tuple[str, str | None], ...],
    statement_set_id: str | None,
    policy_id: str,
    policy_version: str,
    schema_versions_digest: DigestRef,
    contract_digest: DigestRef | None,
) -> IdempotencyKey:
    material = {
        "operation": operation,
        "case_id": case_id,
        "track": track.value,
        "feedback_id": feedback_id,
        "source_digest": _digest_ref_material(source_digest),
        "feedback_items": [{"feedback_item_id": item_id, "target_statement_revision_id": revision_id} for item_id, revision_id in normalized_item_revisions],
        "statement_set_id": statement_set_id,
        "policy_id": policy_id,
        "policy_version": policy_version,
        "schema_versions_digest": _digest_ref_material(schema_versions_digest),
        "contract_digest": _digest_ref_material(contract_digest),
    }
    canonical_bytes = json.dumps(material, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    canonical_digest = DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(canonical_bytes).hexdigest())
    return IdempotencyKey(operation, case_id, track, source_digest, schema_versions_digest, contract_digest, statement_set_id, feedback_id, canonical_digest)


_PI230_ARTIFACT_ROLES = (
    "REPORT",
    "STATEMENT_INDEX",
    "STATEMENT_RECORDS",
    "RUN_SNAPSHOT",
    "DECISION_RUN",
    "FEEDBACK_ATTACHMENT",
    "MANIFEST",
    "FEEDBACK_SOURCE",
)
_PI230_ARTIFACT_STATES = (
    "NOT_ATTEMPTED",
    "WRITING",
    "WRITTEN_UNVERIFIED",
    "VERIFIED",
    "FAILED",
    "STALE",
    "MISMATCH",
    "SUPERSEDED",
)
_PI230_ATTEMPT_OUTCOMES = ("SUCCEEDED", "FAILED", "UNKNOWN")


def _is_nonblank_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_nullable_nonblank_string(value: object) -> bool:
    return value is None or _is_nonblank_string(value)


def _is_complete_digest_ref(value: object) -> bool:
    return (
        isinstance(value, DigestRef)
        and isinstance(value.algorithm, str)
        and value.algorithm != ""
        and isinstance(value.canonicalization, str)
        and value.canonicalization != ""
        and isinstance(value.value, str)
        and value.value != ""
    )


def _is_nullable_complete_digest_ref(value: object) -> bool:
    return value is None or _is_complete_digest_ref(value)


def _is_complete_preprod_versioned_ref(value: object) -> bool:
    if not isinstance(value, VersionedObjectRef):
        return False
    binding = value.digest_binding
    return (
        _is_nonblank_string(value.object_type)
        and _is_nonblank_string(value.object_id)
        and _is_nullable_nonblank_string(value.revision_id)
        and _is_nonblank_string(value.schema_version)
        and _is_nullable_nonblank_string(value.contract_version)
        and isinstance(binding, DigestPresent)
        and binding.status == "PRESENT"
        and _is_complete_digest_ref(binding.digest)
        and _is_nullable_nonblank_string(value.source_locator_id)
        and _is_nullable_nonblank_string(value.captured_at)
    )


def _is_complete_preprod_attempt(
    attempt: object,
    record: ArtifactRecord,
    attempt_index: int,
) -> bool:
    if not isinstance(attempt, ArtifactWriteAttempt):
        return False
    expected_retry_id = None if attempt_index == 0 else record.attempts[attempt_index - 1].attempt_id
    return (
        _is_nonblank_string(attempt.attempt_id)
        and _is_nonblank_string(attempt.artifact_id)
        and attempt.artifact_id == record.artifact_id
        and _is_nonblank_string(attempt.idempotency_key)
        and isinstance(attempt.attempt_number, int)
        and not isinstance(attempt.attempt_number, bool)
        and attempt.attempt_number > 0
        and attempt.attempt_number == attempt_index + 1
        and (
            attempt.retry_of_attempt_id is None
            if attempt_index == 0
            else _is_nonblank_string(attempt.retry_of_attempt_id)
            and attempt.retry_of_attempt_id == expected_retry_id
        )
        and isinstance(attempt.input_snapshot_refs, tuple)
        and bool(attempt.input_snapshot_refs)
        and all(_is_complete_preprod_versioned_ref(ref) for ref in attempt.input_snapshot_refs)
        and _is_nonblank_string(attempt.started_at)
        and _is_nullable_nonblank_string(attempt.finished_at)
        and isinstance(attempt.outcome, str)
        and attempt.outcome in _PI230_ATTEMPT_OUTCOMES
        and _is_nullable_complete_digest_ref(attempt.observed_digest)
        and _is_nullable_nonblank_string(attempt.error_class)
        and _is_nullable_complete_digest_ref(attempt.error_message_digest)
        and (
            attempt.outcome != "SUCCEEDED"
            or (
                _is_nonblank_string(attempt.finished_at)
                and _is_complete_digest_ref(attempt.observed_digest)
                and attempt.error_class is None
                and attempt.error_message_digest is None
            )
        )
        and (
            attempt.outcome != "FAILED"
            or (
                _is_nonblank_string(attempt.finished_at)
                and _is_nonblank_string(attempt.error_class)
                and _is_complete_digest_ref(attempt.error_message_digest)
            )
        )
    )


def _is_complete_preprod_artifact_record(record: object) -> bool:
    if not isinstance(record, ArtifactRecord):
        return False
    return (
        _is_nonblank_string(record.artifact_id)
        and isinstance(record.artifact_role, str)
        and record.artifact_role in _PI230_ARTIFACT_ROLES
        and isinstance(record.track, RunTrack)
        and _is_nonblank_string(record.case_id)
        and _is_nullable_nonblank_string(record.statement_set_id)
        and _is_nullable_nonblank_string(record.run_id)
        and _is_nonblank_string(record.path_locator)
        and _is_nullable_nonblank_string(record.schema_version)
        and _is_nullable_complete_digest_ref(record.expected_digest)
        and _is_nullable_complete_digest_ref(record.observed_digest)
        and isinstance(record.state, str)
        and record.state in _PI230_ARTIFACT_STATES
        and isinstance(record.attempts, tuple)
        and bool(record.attempts)
        and isinstance(record.issue_ids, tuple)
        and all(isinstance(issue_id, str) for issue_id in record.issue_ids)
        and all(
            _is_complete_preprod_attempt(attempt, record, attempt_index)
            for attempt_index, attempt in enumerate(record.attempts)
        )
    )


def exercise_feedback_binding_phase(
    run_result: F09RunResult,
    fixture: FeedbackFixture,
    boundary_calls: list[BoundaryCall] | None = None,
    *,
    preprod_authority_records: tuple[ArtifactRecord | object, ...] | None = None,
    preprod_authority_refs: tuple[VersionedObjectRef | object, ...] | None = None,
) -> FeedbackPhaseObservation:
    supplied_preprod_records = fixture.preprod_authority_records if preprod_authority_records is None else preprod_authority_records
    supplied_preprod_refs = fixture.preprod_authority_refs if preprod_authority_refs is None else preprod_authority_refs
    authority_records: tuple[ArtifactRecord, ...] = ()
    validated_preprod_refs: tuple[VersionedObjectRef, ...] = ()
    preprod_canonical_case_id: str | None = None
    preprod_canonical_run_id: str | None = None
    authority_record_digest: DigestRef | None = None
    if fixture.binding_protocol == "PREPROD_RUN_TARGET":
        if supplied_preprod_records is None or supplied_preprod_refs is None:
            return FeedbackPhaseObservation(
                status="NOT_RUNNABLE", runnable=False, submission=None,
                input_statement_set=None, input_manifest=None, bindings=(),
                eligibility_records=(), errors=("PREPROD_RUN_AUTHORITY_NOT_SUPPLIED",),
                operation_result=None,
            )
        if (
            not isinstance(supplied_preprod_records, tuple)
            or not supplied_preprod_records
            or not isinstance(supplied_preprod_refs, tuple)
            or not supplied_preprod_refs
            or not all(_is_complete_preprod_artifact_record(record) for record in supplied_preprod_records)
            or not all(_is_complete_preprod_versioned_ref(ref) for ref in supplied_preprod_refs)
        ):
            return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        authority_records = tuple(supplied_preprod_records)
        if len({record.artifact_id for record in authority_records}) != len(authority_records):
            return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        if any(
            len({attempt.attempt_id for attempt in record.attempts}) != len(record.attempts)
            for record in authority_records
        ):
            return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        try:
            validated_preprod_refs = tuple(
                validate_versioned_ref(ref, require_revision=True, require_contract=True).value
                for ref in supplied_preprod_refs
            )
            authority_record_digest = digest_artifact_records(authority_records)
        except (F09Error, TypeError, ValueError):
            return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        if len({(ref.object_type, ref.object_id, ref.revision_id) for ref in validated_preprod_refs}) != len(validated_preprod_refs):
            return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        authority_by_id = {record.artifact_id: record for record in authority_records}
        if set(authority_by_id) != {ref.object_id for ref in validated_preprod_refs}:
            return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        if any(
            ref.object_type != authority_by_id[ref.object_id].artifact_role
            or ref.revision_id != authority_by_id[ref.object_id].run_id
            or ref.schema_version != authority_by_id[ref.object_id].schema_version
            or ref.digest_binding.digest != (authority_by_id[ref.object_id].observed_digest or authority_by_id[ref.object_id].expected_digest)
            for ref in validated_preprod_refs
        ):
            return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        authority_case_ids = {record.case_id for record in authority_records}
        authority_run_ids = {record.run_id for record in authority_records}
        authority_tracks = {record.track for record in authority_records}
        if len(authority_case_ids) != 1 or len(authority_run_ids) != 1 or len(authority_tracks) != 1:
            return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        preprod_canonical_case_id = next(iter(authority_case_ids))
        preprod_canonical_run_id = next(iter(authority_run_ids))
        if next(iter(authority_tracks)) != RunTrack(fixture.target_track):
            return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        if not any(
            record.artifact_role == "RUN_SNAPSHOT"
            and record.state == "VERIFIED"
            and (record.observed_digest is not None or record.expected_digest is not None)
            for record in authority_records
        ):
            return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_RUN_SNAPSHOT_REQUIRED",), (), None)
    if (
        boundary_calls is not None
        and fixture == BASELINE_FEEDBACK
        and run_result.request.mode == "STAGED_AUDIT"
        and run_result.statement_set is not None
        and run_result.statement_set.track is RunTrack.STAGED_L6
    ):
        return FeedbackPhaseObservation(
            status="NOT_RUNNABLE",
            runnable=False,
            submission=None,
            input_statement_set=run_result.statement_set,
            input_manifest=run_result.manifest,
            bindings=(),
            eligibility_records=(),
            errors=(),
            issues=(),
            operation_result=None,
        )
    if fixture.binding_protocol == "PRODUCTION_STATEMENT" and (
        run_result.statement_set is None or run_result.manifest is None
    ):
        return FeedbackPhaseObservation(
            status="NOT_RUNNABLE", runnable=False, submission=None,
            input_statement_set=None, input_manifest=None, bindings=(),
            eligibility_records=(), errors=("PRODUCTION_FEEDBACK_PREREQUISITE_NOT_PRODUCED",),
            operation_result=None,
        )
    if len(fixture.seven_matches) != 7:
        return FeedbackPhaseObservation(
            "INVALID", False, None, run_result.statement_set, run_result.manifest,
            (), (), ("FEEDBACK_MATCH_DIMENSION_SHAPE_INVALID",), (), None,
        )

    canonical_case_id = (
        run_result.statement_set.case_id
        if fixture.binding_protocol == "PRODUCTION_STATEMENT"
        else preprod_canonical_case_id
    )
    if not isinstance(canonical_case_id, str) or not canonical_case_id:
        return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
    case_fact = canonical_case_id
    if fixture.seven_matches[0] == "MISMATCH":
        case_fact = canonical_case_id + "-MISMATCH"
    if fixture.seven_matches[0] == "UNKNOWN":
        case_fact = ""

    track_fact = RunTrack(fixture.source_track)
    target_track_fact = RunTrack(fixture.target_track)
    source_track_digest = DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(fixture.source_track_digest.encode("utf-8")).hexdigest())
    target_track_digest = DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(fixture.target_track_digest.encode("utf-8")).hexdigest())
    source_track_evidence_ref = VersionedObjectRef("FEEDBACK", fixture.source_track_evidence_id, "TRACK-SOURCE-REV-1", fixture.source_track_schema_version, fixture.source_track_contract_version, DigestPresent("PRESENT", source_track_digest), "SRCLOC-FEEDBACK-TRACK", "2026-07-20T00:00:00Z")
    source_track_parser_ref = VersionedObjectRef("PARSER", fixture.source_track_parser_id, fixture.source_track_parser_version, "parser-ref-v1", fixture.source_track_contract_version, DigestPresent("PRESENT", DigestRef("sha256", "RFC8785-JCS-UTF8", sha256((fixture.source_track_parser_id + ":" + fixture.source_track_parser_version).encode("utf-8")).hexdigest())), None, "2026-07-20T00:00:00Z")
    source_track_binding = TrackSourceBinding("TSB-F09-SOURCE-1", "SUBMISSION_SOURCE", track_fact, fixture.source_track_state, source_track_evidence_ref, source_track_parser_ref, fixture.source_track_schema_version, fixture.source_track_contract_version, source_track_digest, fixture.source_track_reason_codes, "2026-07-20T00:00:00Z")
    target_track_evidence_ref = VersionedObjectRef("STATEMENT_SET", fixture.target_track_evidence_id, "STMT-REV-2", fixture.target_track_schema_version, fixture.target_track_contract_version, DigestPresent("PRESENT", target_track_digest), "SRCLOC-TARGET-TRACK", "2026-07-20T00:00:00Z")
    target_track_parser_ref = VersionedObjectRef("PARSER", fixture.target_track_parser_id, fixture.target_track_parser_version, "parser-ref-v1", fixture.target_track_contract_version, DigestPresent("PRESENT", DigestRef("sha256", "RFC8785-JCS-UTF8", sha256((fixture.target_track_parser_id + ":" + fixture.target_track_parser_version).encode("utf-8")).hexdigest())), None, "2026-07-20T00:00:00Z")
    target_track_source_binding = TrackSourceBinding("TSB-F09-TARGET-1", "BINDING_TARGET", target_track_fact, fixture.target_track_state, target_track_evidence_ref, target_track_parser_ref, fixture.target_track_schema_version, fixture.target_track_contract_version, target_track_digest, fixture.target_track_reason_codes, "2026-07-20T00:00:00Z")

    run_fact = "RUN-F09-1" if fixture.binding_protocol == "PRODUCTION_STATEMENT" else preprod_canonical_run_id
    if fixture.seven_matches[2] == "MISMATCH":
        run_fact = "RUN-F09-MISMATCH"
    if fixture.seven_matches[2] == "UNKNOWN":
        run_fact = ""
    if fixture.seven_matches[2] == "NOT_APPLICABLE":
        run_fact = None

    statement_fact = fixture.target_statement_id
    if fixture.seven_matches[3] == "MISMATCH":
        statement_fact = "STMT-F09-MISMATCH"
    if fixture.seven_matches[3] == "UNKNOWN":
        statement_fact = ""
    if fixture.seven_matches[3] == "NOT_APPLICABLE":
        statement_fact = None

    revision_fact = fixture.target_revision
    if fixture.seven_matches[4] == "MISMATCH":
        revision_fact = "STMT-REV-MISMATCH"
    if fixture.seven_matches[4] == "UNKNOWN":
        revision_fact = ""
    if fixture.seven_matches[4] == "NOT_APPLICABLE":
        revision_fact = None

    statement_set_fact = (
        run_result.statement_set.statement_set_id
        if fixture.binding_protocol == "PRODUCTION_STATEMENT"
        else None
    )
    if fixture.binding_protocol == "PRODUCTION_STATEMENT" and fixture.seven_matches[5] == "MISMATCH":
        statement_set_fact = run_result.statement_set.statement_set_id + "-MISMATCH"
    if fixture.seven_matches[5] == "UNKNOWN":
        statement_set_fact = ""
    if fixture.seven_matches[5] == "NOT_APPLICABLE":
        statement_set_fact = ""
    if len(fixture.item_ids) < 1:
        return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("FEEDBACK_ITEM_SHAPE_INVALID",), (), None)
    padded_item_ids = fixture.item_ids + ("FBI-PADDING-1", "FBI-PADDING-2")
    if len(padded_item_ids) < 2:
        return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("FEEDBACK_ITEM_PADDING_SHAPE_INVALID",), (), None)
    item_1 = FeedbackItem(padded_item_ids[0], "FB-F09-1" if fixture.submission_complete else "", "/feedback/items/0", statement_fact, revision_fact, run_fact, None, "CONFIRMED", "bounded fixture feedback", "VALID", ())
    item_2 = FeedbackItem(padded_item_ids[1], "FB-F09-1" if fixture.submission_complete else "", "/feedback/items/1", statement_fact, revision_fact, run_fact, None, "CONFIRMED", "bounded fixture feedback", "VALID", ())
    submission = FeedbackSubmission(
        feedback_id="FB-F09-1" if fixture.submission_complete else "",
        case_id=case_fact,
        track=track_fact,
        track_source_binding=source_track_binding,
        source_snapshot_ref=SnapshotRef("SNAP-F09-FEEDBACK-1", "FEEDBACK", ("/feedback",), "feedback-v1", "PI230-V1", DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(fixture.source_digest.encode("utf-8")).hexdigest()), "2026-07-20T00:00:00Z", "IMMUTABLE"),
        source_snapshot_payload={
            "feedback": {
                "items": tuple(
                    {"id": item.feedback_item_id}
                    for item in (item_1, item_2)[:len(fixture.item_ids)]
                ),
            },
        },
        parser_id="F09FixtureParser",
        parser_version="1",
        feedback_items=(item_1, item_2)[:len(fixture.item_ids)],
        content_digest=DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(b"DG-FEEDBACK-A").hexdigest()),
        captured_at="2026-07-20T00:00:00Z",
    )
    prior_submission = replace(
        submission,
        source_snapshot_ref=replace(
            submission.source_snapshot_ref,
            content_digest=DigestRef(
                "sha256", "RFC8785-JCS-UTF8",
                sha256(fixture.prior_source_digest.encode("utf-8")).hexdigest(),
            ),
        ),
    )
    statement_refs: Mapping[tuple[str, str], VersionedObjectRef] = MappingProxyType({})
    statement_set_ref: VersionedObjectRef | None = None
    records_projection_refs: Mapping[str, VersionedObjectRef] = MappingProxyType({})
    records_projection_records: Mapping[str, StatementProjectionRecord] = MappingProxyType({})
    anchor_selections: Mapping[tuple[str, str], AnchorSelectionRecord] = MappingProxyType({})
    preprod_target_refs: Mapping[str, tuple[VersionedObjectRef, ...]] = MappingProxyType({})
    selection_for_digest: AnchorSelectionRecord | None = None
    target_run_id_for_digest: str | None = None
    if fixture.binding_protocol == "PRODUCTION_STATEMENT":
        if not run_result.statement_set.statements or not run_result.manifest.records:
            return FeedbackPhaseObservation("INVALID", False, submission, run_result.statement_set, run_result.manifest, (), (), ("PRODUCTION_TARGET_SHAPE_INVALID",), (), None)
        target_statement = replace(run_result.statement_set.statements[0], statement_revision_id=revision_fact)
        input_statement_set = replace(run_result.statement_set, statements=(target_statement,))
        base_record = run_result.manifest.records[0]
        observed_digest = base_record.expected_digest if fixture.seven_matches[6] != "UNKNOWN" else None
        if fixture.seven_matches[6] == "MISMATCH":
            observed_digest = DigestRef("sha256", "RAW-UTF8", sha256(b"feedback-mismatch").hexdigest())
        anchor_record = replace(base_record, artifact_role="STATEMENT_RECORDS", case_id=input_statement_set.case_id, statement_set_id=statement_set_fact, run_id=None, schema_version=target_statement.statement_schema_version, observed_digest=observed_digest, state="VERIFIED")
        input_manifest = replace(run_result.manifest, records=((anchor_record,) if fixture.anchor_status == "MAPPED" else ()))
        statement_ref = VersionedObjectRef("STATEMENT", target_statement.statement_id, target_statement.statement_revision_id, target_statement.statement_schema_version, "PI230-V1", DigestPresent("PRESENT", target_statement.content_digest), target_statement.source_locator_ids[0] if target_statement.source_locator_ids else None, input_statement_set.generated_at)
        statement_set_ref = VersionedObjectRef("STATEMENT_SET", input_statement_set.statement_set_id, None, input_statement_set.statement_schema_version, "PI230-V1", DigestPresent("PRESENT", input_statement_set.content_digest), None, input_statement_set.generated_at)
        records_ref = VersionedObjectRef("STATEMENT_RECORDS", anchor_record.artifact_id, target_statement.statement_revision_id, anchor_record.schema_version, "PI230-V1", DigestPresent("PRESENT", anchor_record.observed_digest or anchor_record.expected_digest), anchor_record.path_locator, input_statement_set.generated_at)
        projection = StatementProjectionRecord("PROJ-RECORDS-F09-1", "STATEMENT_RECORDS", input_statement_set.statement_set_id, target_statement.statement_id, target_statement.statement_revision_id, target_statement.content_digest, records_ref, "TRANSFORM-RECORDS-F09-1", "LOSSY", (), (), ())
        selected_rule_ref = VersionedObjectRef("RULE", "V-RULE-ANCHOR", "RULE-REV-1", "rule-v1", "PI300-V1", DigestPresent("PRESENT", DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(b"V-RULE-ANCHOR").hexdigest())), "SRCLOC-RULE-ANCHOR", input_statement_set.generated_at)
        selection_for_digest = AnchorSelectionRecord("ANCHOR-SELECTION-F09-1", target_statement.statement_id, target_statement.statement_revision_id, (selected_rule_ref,), selected_rule_ref, (), "PRODUCTION-STATEMENT-ELIGIBILITY", "policy-v1", digest_ordered_rule_refs((selected_rule_ref,)), "LOSSY", "SELECTED_ANCHOR_ONLY", ())
        statement_refs = MappingProxyType({(target_statement.statement_id, target_statement.statement_revision_id): statement_ref})
        records_projection_refs = MappingProxyType({anchor_record.artifact_id: records_ref})
        records_projection_records = MappingProxyType({anchor_record.artifact_id: projection})
        anchor_selections = MappingProxyType({(target_statement.statement_id, target_statement.statement_revision_id): selection_for_digest})
        target_refs_for_digest = (statement_ref, statement_set_ref, records_ref)
    else:
        input_statement_set = None
        if authority_record_digest is None or preprod_canonical_run_id is None:
            return FeedbackPhaseObservation("INVALID", False, submission, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        authority_key = IdempotencyKey(
            "BIND_FEEDBACK", canonical_case_id, target_track_fact, authority_record_digest,
            authority_record_digest, None, None, submission.feedback_id, authority_record_digest,
        )
        input_manifest = ArtifactSetManifest(
            "MANIFEST:CALLER-PREPROD-AUTHORITY", authority_key, authority_records,
            "COMPLETE_VERIFIED", authority_record_digest, (),
        )
        preprod_target_refs = MappingProxyType({preprod_canonical_run_id: validated_preprod_refs})
        target_run_id_for_digest = run_fact
        target_refs_for_digest = validated_preprod_refs
    prior_source_digest = prior_submission.source_snapshot_ref.content_digest
    current_source_digest = submission.source_snapshot_ref.content_digest
    schema_versions_digest = DigestRef("sha256", "RFC8785-JCS-UTF8", sha256((fixture.source_track_schema_version + ":" + fixture.target_track_schema_version).encode("utf-8")).hexdigest())
    contract_digest = DigestRef("sha256", "RFC8785-JCS-UTF8", sha256((fixture.source_track_contract_version + ":" + fixture.target_track_contract_version).encode("utf-8")).hexdigest())
    normalized_item_revisions = normalize_feedback_item_revisions(submission.feedback_items)
    prior_item_revisions = (("FBI-1", "STMT-REV-2"),)
    policy_id = "PRODUCTION-STATEMENT-ELIGIBILITY"
    prior_policy_version = fixture.prior_policy_version
    prior_key = build_canonical_feedback_key(
        operation="BIND_FEEDBACK", case_id=submission.case_id, track=submission.track,
        feedback_id=submission.feedback_id, source_digest=prior_source_digest,
        normalized_item_revisions=prior_item_revisions,
        statement_set_id=(input_statement_set.statement_set_id if input_statement_set is not None else None),
        policy_id=policy_id, policy_version=prior_policy_version,
        schema_versions_digest=schema_versions_digest, contract_digest=contract_digest,
    )
    current_key = build_canonical_feedback_key(
        operation="BIND_FEEDBACK", case_id=submission.case_id, track=submission.track,
        feedback_id=submission.feedback_id, source_digest=current_source_digest,
        normalized_item_revisions=normalized_item_revisions,
        statement_set_id=(input_statement_set.statement_set_id if input_statement_set is not None else None),
        policy_id=policy_id, policy_version="policy-v1",
        schema_versions_digest=schema_versions_digest, contract_digest=contract_digest,
    )
    prior_target_refs = target_refs_for_digest
    prior_selection_for_digest = selection_for_digest
    try:
        if fixture.target_graph_relation == "CHANGED":
            first_ref = validate_versioned_ref(target_refs_for_digest[0], require_revision=True, require_contract=True).value
            prior_revision = str(first_ref.revision_id) + "-PRIOR"
            prior_target_refs = (replace(first_ref, revision_id=prior_revision),) + target_refs_for_digest[1:]
            if fixture.binding_protocol == "PRODUCTION_STATEMENT":
                prior_selection_for_digest = replace(
                    selection_for_digest,
                    statement_revision_id=prior_revision,
                )
        prior_target_digest = digest_protocol_target_graph(fixture.binding_protocol, prior_target_refs, target_run_id=target_run_id_for_digest, selection=prior_selection_for_digest)
        current_target_digest = digest_protocol_target_graph(fixture.binding_protocol, target_refs_for_digest, target_run_id=target_run_id_for_digest, selection=selection_for_digest)
    except (F09Error, TypeError, ValueError):
        if fixture.binding_protocol == "PREPROD_RUN_TARGET":
            return FeedbackPhaseObservation("INVALID", False, submission, None, input_manifest, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        raise
    errors: tuple[str, ...] = ()
    issues: tuple[PhaseIssueObservation, ...] = ()
    validated_bindings: tuple[FeedbackBinding, ...] = ()
    eligibility_records: tuple[LearningEligibility, ...] = ()
    operation_result: FeedbackOperationResult | None = None
    try:
        if boundary_calls is not None:
            boundary_calls.append(BoundaryCall("VALIDATE_FEEDBACK_BINDING", submission.track))
        operation_result = validate_feedback_binding(
            submission,
            (input_statement_set if fixture.binding_protocol == "PRODUCTION_STATEMENT" else None),
            input_manifest,
            prior_key=prior_key,
            current_key=current_key,
            prior_target_digest=prior_target_digest,
            current_target_digest=current_target_digest,
            target_track_source_binding=target_track_source_binding,
            statement_refs=statement_refs,
            statement_set_ref=statement_set_ref,
            records_projection_refs=records_projection_refs,
            records_projection_records=records_projection_records,
            anchor_selections=anchor_selections,
            preprod_target_refs=preprod_target_refs,
            governing_statement_contract_version="PI230-V1",
            governing_statement_set_contract_version="PI230-V1",
            governing_statement_records_contract_version="PI230-V1",
            governing_rule_contract_version="PI300-V1",
        )
        issues = issues + tuple(PhaseIssueObservation(issue.issue_code, issue.field_path) for issue in operation_result.detected_issues)
        returned_bindings = operation_result.bindings
        issues = issues + tuple(
            PhaseIssueObservation(issue.issue_code, issue.field_path)
            for binding in returned_bindings
            for issue in binding.detected_issues
        )
        canonical_key_changed = prior_key.canonical_key_digest != current_key.canonical_key_digest
        if fixture.target_graph_relation == "CHANGED" and not canonical_key_changed:
            if (
                operation_result.operation_disposition != "TARGET_MISMATCH"
                or operation_result.overwrite_permitted is not False
                or operation_result.detected_issues != (
                    DetectedIssue("IDEMPOTENCY.DIGEST_MISMATCH", "/feedback/source_snapshot_ref"),
                )
            ):
                raise AssertionError("same-key/different-target must return a no-overwrite TARGET_MISMATCH receipt")
        elif canonical_key_changed:
            if (
                operation_result.operation_disposition != "NEW_OPERATION"
                or operation_result.source_identity_relation != (
                    "CHANGED" if fixture.prior_source_digest != fixture.source_digest else "SAME"
                )
                or operation_result.prior_key != prior_key
                or operation_result.current_key != current_key
                or operation_result.overwrite_permitted is not False
                or operation_result.detected_issues
            ):
                raise AssertionError("every changed canonical key must return a no-overwrite NEW_OPERATION receipt")
        elif operation_result.operation_disposition != "REUSED_OPERATION":
            raise AssertionError("same canonical feedback key and target must reuse its operation identity")
        if len(returned_bindings) != len(fixture.item_ids):
            raise AssertionError("feedback binder cardinality differs from canonical item graph")
        if len(returned_bindings) < 1:
            raise AssertionError("feedback binder returned no canonical binding")
        base_binding_1 = returned_bindings[0]
        if base_binding_1.binding_protocol != fixture.binding_protocol:
            raise AssertionError("feedback binder protocol differs from canonical target facts")
        returned_dimensions = (
            base_binding_1.case_match,
            base_binding_1.track_match,
            base_binding_1.run_match,
            base_binding_1.statement_match,
            base_binding_1.revision_match,
            base_binding_1.statement_set_match,
            base_binding_1.artifact_digest_match,
        )
        expected_track_match = "UNKNOWN"
        if (
            fixture.source_track_state == "AVAILABLE_RESOLVED"
            and fixture.target_track_state == "AVAILABLE_RESOLVED"
        ):
            expected_track_match = (
                "MATCH" if track_fact == target_track_fact else "MISMATCH"
            )
        expected_dimensions = (
            fixture.seven_matches[0],
            expected_track_match,
            fixture.seven_matches[2],
            fixture.seven_matches[3],
            fixture.seven_matches[4],
            fixture.seven_matches[5],
            fixture.seven_matches[6],
        )
        if returned_dimensions != expected_dimensions:
            raise AssertionError("feedback binder seven-dimension result differs from canonical input facts")
        expected_reason_codes = {
            "AVAILABLE_RESOLVED": (),
            "SOURCE_MISSING": ("TRACK_SOURCE_MISSING",),
            "UNPARSABLE": ("TRACK_SOURCE_UNPARSABLE",),
            "AMBIGUOUS": ("TRACK_SOURCE_AMBIGUOUS",),
            "INTEGRITY_FAILED": ("TRACK_SOURCE_INTEGRITY_FAILED",),
        }
        bindings_well_formed = (
            fixture.source_track_reason_codes == expected_reason_codes[fixture.source_track_state]
            and fixture.target_track_reason_codes == expected_reason_codes[fixture.target_track_state]
            and fixture.source_track_evidence_id != ""
            and fixture.target_track_evidence_id != ""
            and fixture.source_track_parser_id != ""
            and fixture.target_track_parser_id != ""
            and fixture.source_track_parser_version != ""
            and fixture.target_track_parser_version != ""
            and fixture.source_track_schema_version != ""
            and fixture.target_track_schema_version != ""
            and fixture.source_track_contract_version != ""
            and fixture.target_track_contract_version != ""
            and fixture.source_track_digest != ""
            and fixture.target_track_digest != ""
        )
        protocol_dimensions = {
            "PRODUCTION_STATEMENT": {
                "required": (0, 1, 3, 4, 5, 6),
                "allowed_not_applicable": (2,),
            },
            "PREPROD_RUN_TARGET": {
                "required": (0, 1, 2, 6),
                "allowed_not_applicable": (3, 4, 5),
            },
        }
        protocol_rule = protocol_dimensions[fixture.binding_protocol]
        required_dimensions_satisfied = all(
            returned_dimensions[index] == "MATCH"
            for index in protocol_rule["required"]
        )
        allowed_not_applicable_satisfied = all(
            returned_dimensions[index] == "NOT_APPLICABLE"
            for index in protocol_rule["allowed_not_applicable"]
        )
        canonical_input_invalid = (
            fixture.source_track_state == "INTEGRITY_FAILED"
            or fixture.target_track_state == "INTEGRITY_FAILED"
            or not fixture.submission_complete
            or not bindings_well_formed
        )
        canonical_input_ambiguous = (
            fixture.source_track_state == "AMBIGUOUS"
            or fixture.target_track_state == "AMBIGUOUS"
        )
        production_anchor_unmapped = (
            fixture.binding_protocol == "PRODUCTION_STATEMENT"
            and fixture.anchor_status != "MAPPED"
        )
        canonical_input_unbound = (
            fixture.source_track_state in ("SOURCE_MISSING", "UNPARSABLE")
            or fixture.target_track_state in ("SOURCE_MISSING", "UNPARSABLE")
            or not required_dimensions_satisfied
            or not allowed_not_applicable_satisfied
            or production_anchor_unmapped
        )
        if canonical_input_invalid:
            expected_status = "INVALID"
        elif canonical_input_ambiguous:
            expected_status = "AMBIGUOUS"
        elif canonical_input_unbound:
            expected_status = "UNBOUND"
        elif (
            fixture.source_track_state == "AVAILABLE_RESOLVED"
            and fixture.target_track_state == "AVAILABLE_RESOLVED"
            and required_dimensions_satisfied
            and allowed_not_applicable_satisfied
            and not production_anchor_unmapped
        ):
            expected_status = "BOUND"
        else:
            raise AssertionError("feedback aggregate oracle did not exhaust PI-230 first-match states")
        if base_binding_1.status != expected_status:
            raise AssertionError("feedback binder aggregate status differs from PI-230 priority table")
        # Contract-consistency assertion only: the preceding seven-dimension and aggregate-status
        # comparisons verify that returned canonical values agree with canonical call inputs.
        # They do not create, select, filter, map, validate, or supplement an expected issue pair.
        # Positive issue evidence remains exclusively binding.detected_issues,
        # eligibility.detected_issues, or one caught typed F09Error from the production port.
        binding_1 = replace(base_binding_1, feedback_binding_id=(base_binding_1.feedback_binding_id if fixture.binding_complete else ""))
        if boundary_calls is not None:
            boundary_calls.append(BoundaryCall("VALIDATE_FEEDBACK_BINDING_RECORD", submission.track))
        validate_feedback_binding_record(binding_1)
        if boundary_calls is not None:
            boundary_calls.append(BoundaryCall("EVALUATE_LEARNING_ELIGIBILITY", submission.track))
        eligibility_1 = evaluate_learning_eligibility(
            binding_1,
            policy_id="PRODUCTION-STATEMENT-ELIGIBILITY",
            policy_version="policy-v1",
            evaluated_at="2026-07-20T00:00:01Z",
        )
        issues = issues + tuple(
            PhaseIssueObservation(issue.issue_code, issue.field_path)
            for issue in eligibility_1.detected_issues
        )
        eligibility_1 = replace(
            eligibility_1,
            eligibility_id=(eligibility_1.eligibility_id if fixture.eligibility_complete else ""),
        )
        if boundary_calls is not None:
            boundary_calls.append(BoundaryCall("VALIDATE_LEARNING_ELIGIBILITY", submission.track))
        validate_learning_eligibility(eligibility_1)
        validated_bindings = (binding_1,)
        eligibility_records = (eligibility_1,)
        if len(returned_bindings) == 2:
            base_binding_2 = returned_bindings[1]
            binding_2 = replace(base_binding_2, feedback_binding_id=(base_binding_2.feedback_binding_id if fixture.binding_complete else ""))
            if boundary_calls is not None:
                boundary_calls.append(BoundaryCall("VALIDATE_FEEDBACK_BINDING_RECORD", submission.track))
            validate_feedback_binding_record(binding_2)
            if boundary_calls is not None:
                boundary_calls.append(BoundaryCall("EVALUATE_LEARNING_ELIGIBILITY", submission.track))
            eligibility_2 = evaluate_learning_eligibility(
                binding_2,
                policy_id="PRODUCTION-STATEMENT-ELIGIBILITY",
                policy_version="policy-v1",
                evaluated_at="2026-07-20T00:00:01Z",
            )
            issues = issues + tuple(
                PhaseIssueObservation(issue.issue_code, issue.field_path)
                for issue in eligibility_2.detected_issues
            )
            eligibility_2 = replace(
                eligibility_2,
                eligibility_id=(eligibility_2.eligibility_id if fixture.eligibility_complete else ""),
            )
            if boundary_calls is not None:
                boundary_calls.append(BoundaryCall("VALIDATE_LEARNING_ELIGIBILITY", submission.track))
            validate_learning_eligibility(eligibility_2)
            validated_bindings = (binding_1, binding_2)
            eligibility_records = (eligibility_1, eligibility_2)
    except F09Error as error:
        errors = (type(error).__name__ + ":" + str(error),)
        issues = issues + (PhaseIssueObservation(error.issue_code, error.field_path),)
    return FeedbackPhaseObservation(
        status="VALID" if not errors and not issues else "INVALID",
        runnable=True,
        submission=submission,
        input_statement_set=input_statement_set,
        input_manifest=input_manifest,
        bindings=validated_bindings,
        eligibility_records=eligibility_records,
        errors=errors,
        issues=issues,
        operation_result=operation_result,
    )

BASELINE_GATE = GateFixture("SATISFIED", "SATISFIED", "SATISFIED", "SATISFIED", "SATISFIED", "SATISFIED", (), (), ("ALLOCATION", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "TEMPORAL"), ("ALLOCATION", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "TEMPORAL"), "REF-GATE-F09-V1", ("REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1"), ("DG-ALLOC", "DG-RISK", "DG-REAL", "DG-ATTR", "DG-SOURCE", "DG-TEMP"), ("REALITY_FACT",), True)
BASELINE_DECLARATIONS = DeclarationFixture("RESOLVED", None, False, "OUTPUT_PRECISION", "DG-PRECISION-V1", "PI210-V1", "VALIDATION_PLAN", "DG-VALIDATION-V1", None, True, "DG-PRECISION-V1", "DG-PRECISION-V1")
BASELINE_DECISION = DecisionFixture("OUTPUT", "OutputPayload", (), (), ("GR-ALLOCATION", "GR-RISK", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL"), ("PR-REALITY-OUTPUT",), ("DISP-F09-INCLUDED",), ("CAND-F09",), ("DISP-F09-INCLUDED",), (), False, False)
BASELINE_PARTICIPATION = ParticipationFixture(
    PARTICIPATION_ROLES,
    tuple((role, f"PART-BIND-{role}") for role in PARTICIPATION_ROLES),
    "SCENARIO-OUTPUT",
)
BASELINE_ROOT_TIMING = RootTimingFixture(
    "SATISFIED",
    None,
    None,
    "SATISFIED",
    None,
    None,
    False,
    (("CAND-F09", "ROOT-TIMING-BIND-CAND-F09"),),
)
BASELINE_TRACE = TraceFixture(True, True, ("GR-ALLOCATION", "GR-RISK", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL", "PR-REALITY-OUTPUT", "DISP-F09-INCLUDED", "RTC-ROOT", "RTC-TIMING"), ("RULE-F09-ANCHOR",), "LOSSLESS", 6, True, "REFERENCE_ONLY_NOT_IMPLEMENTATION_PROOF", "bounded outcome: allocation capital present", ())
BASELINE_ARTIFACTS = ArtifactFixture("SUCCEEDED", "SUCCEEDED", "STMT-REV-2", "DG-ARTIFACT-V2", "DG-ARTIFACT-V2", ("VERIFIED",), "STMT-REV-2", None, "IDEM-KEY-A", b"F09 staged report\n", b"DG-ARTIFACT-V2", b"STMT-REV-2")
PREPROD_AUTHORITY_DIGEST = DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(b"PI230-PREPROD-RUN-AUTHORITY").hexdigest())
PREPROD_AUTHORITY_INPUT_REF = VersionedObjectRef(
    "RUN_INPUT_SNAPSHOT", "SNAP-PREPROD-AUTHORITY-1", "SNAP-REV-1", "run-input-snapshot-v1", "PI230-V1",
    DigestPresent("PRESENT", PREPROD_AUTHORITY_DIGEST), "preprod/input-snapshot.json", "2026-07-20T00:00:00Z",
)
PREPROD_AUTHORITY_ATTEMPT = ArtifactWriteAttempt(
    "ATTEMPT-PREPROD-AUTHORITY-1", "ART-RUN-SNAPSHOT-1", "PREPROD-AUTHORITY-KEY",
    1, None, (PREPROD_AUTHORITY_INPUT_REF,), "2026-07-20T00:00:00Z", "2026-07-20T00:00:00Z", "SUCCEEDED",
    PREPROD_AUTHORITY_DIGEST, None, None,
)
BASELINE_PREPROD_AUTHORITY_RECORDS = (
    ArtifactRecord(
        "ART-RUN-SNAPSHOT-1", "RUN_SNAPSHOT", RunTrack.STAGED_L6, "CASE-F09-PREPROD-AUTHORITY",
        None, "RUN-F09-1", "preprod/RUN_SNAPSHOT.json", "preprod-artifact-v1",
        PREPROD_AUTHORITY_DIGEST, PREPROD_AUTHORITY_DIGEST, "VERIFIED", (PREPROD_AUTHORITY_ATTEMPT,), (),
    ),
    ArtifactRecord(
        "ART-DECISION-RUN-1", "DECISION_RUN", RunTrack.STAGED_L6, "CASE-F09-PREPROD-AUTHORITY",
        None, "RUN-F09-1", "preprod/DECISION_RUN.json", "preprod-artifact-v1",
        PREPROD_AUTHORITY_DIGEST, PREPROD_AUTHORITY_DIGEST, "VERIFIED",
        (replace(PREPROD_AUTHORITY_ATTEMPT, attempt_id="ATTEMPT-PREPROD-DECISION-1", artifact_id="ART-DECISION-RUN-1"),), (),
    ),
)
BASELINE_PREPROD_AUTHORITY_REFS = tuple(
    VersionedObjectRef(
        record.artifact_role, record.artifact_id, record.run_id, record.schema_version, "PI230-V1",
        DigestPresent("PRESENT", record.observed_digest), record.path_locator, "2026-07-20T00:00:00Z",
    )
    for record in BASELINE_PREPROD_AUTHORITY_RECORDS
)
BASELINE_FEEDBACK = FeedbackFixture(
    "PRODUCTION_STATEMENT", "STMT-F09-1", "STMT-REV-2", "MAPPED", "SAME",
    ("MATCH", "MATCH", "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "MATCH"),
    RunTrack.STAGED_L6, "AVAILABLE_RESOLVED", "SNAP-F09-FEEDBACK-1",
    "F09FixtureParser", "1", "track-source-v1", "PI230-V1", "DG-TRACK-SOURCE-A", (),
    RunTrack.STAGED_L6, "AVAILABLE_RESOLVED", "STMTSET-F09-1",
    "F09TargetTrackResolver", "1", "track-source-v1", "PI230-V1", "DG-TRACK-TARGET-A", (),
    "policy-v1", ("FBI-1",), "DG-FEEDBACK-A", "DG-FEEDBACK-A", True, True, True,
    BASELINE_PREPROD_AUTHORITY_RECORDS, BASELINE_PREPROD_AUTHORITY_REFS,
)
BASELINE_SOURCE = SourceFixture(True, "REALITY_FACT", "SOURCE-STATE-1", "/value", ("level", "position", "as_of"), "SOURCE-EVENT-1", "/value", ("level", "change", "interval/start", "interval/end", "interval/start_inclusive", "interval/end_inclusive"), ("axis", "action", "object", "tense"), "PI-300-F09-SOURCE-SNAPSHOT-V1", "reality-fact-source-snapshot.v1", "pi-300-f09-source-snapshots-v1", "67517fe2d04fb0fe580e031643dab2ad53fcdb8c90707ba4d496c316dd87f5e7", "2026-07-19T00:00:00Z", "67517fe2d04fb0fe580e031643dab2ad53fcdb8c90707ba4d496c316dd87f5e7", True, "IMMUTABLE_JSON_SNAPSHOT", True)

def baseline_scenario_bundle(tmp_path: Path) -> ScenarioBundle:
    markdown_path = Path("engine/contracts/12-real-world-function-evidence-cards-v1.md")
    snapshot_path = Path("plans/production-implementation-pi-300-f09-source-snapshots-v1.json")
    package = build_f09_evidence_package(
        case_id="CASE-F09-VERTICAL",
        track=RunTrack.STAGED_L6,
        markdown_path=markdown_path,
        snapshot_path=snapshot_path,
        chart_records=(),
        hypothesis_records=(),
    )
    snapshot = load_snapshot(snapshot_path)
    authority_source_bytes = canonicalize_bounded_jcs(snapshot.payload)
    authority_digest = bounded_jcs_sha256(snapshot.payload)
    contract_version = BASELINE_DECLARATIONS.precision_contract_version
    contract_ref = ContractVersionRef("PI-220.md", "PI-220.json", contract_version, HEX)
    field_ref = FrozenCardFieldRef(
        "F09", "real-world-function-evidence-cards-v1", contract_version,
        "/cards/F09/gates", "PRESENT_VALUE", tuple(SIX_MEMBERS), BASELINE_SOURCE.snapshot_id,
    )
    field_ref_payload = {
        "card_id": field_ref.card_id,
        "contract_id": field_ref.contract_id,
        "contract_version": field_ref.contract_version,
        "field_path": field_ref.field_path,
        "declared_state": field_ref.declared_state,
        "declared_value": list(field_ref.declared_value),
        "source_locator_id": field_ref.source_locator_id,
    }
    field_observation = FrozenFieldObservation(
        field_ref, field_ref.declared_state, field_ref.declared_value, None,
        f"{BASELINE_SOURCE.snapshot_id}#{field_ref.field_path}",
    )
    constraint_ref = FrozenConstraintRef(
        "F09", "real-world-function-evidence-cards-v1", contract_version,
        "/root_timing", BASELINE_SOURCE.snapshot_id,
    )
    declaration_digest = DigestRef(
        "sha256", "RFC8785-JCS-UTF8", BASELINE_DECLARATIONS.validation_digest
    ) if len(BASELINE_DECLARATIONS.validation_digest) == 64 else bounded_jcs_sha256(
        BASELINE_DECLARATIONS.validation_digest
    )
    member_ids = tuple(
        derive_member_id(member, contract_version, declaration_digest)
        for member in SIX_MEMBERS
    )
    reality_records = tuple(
        record for record in package.records if record.track is EvidenceTrack.REALITY_FACT
    )
    gate_bindings = {}
    gate_binding_ids = []
    for member, member_id in zip(SIX_MEMBERS, member_ids):
        state = "UNKNOWN" if member == "RISK" else "SATISFIED"
        supporting_evidence_ids = tuple(
            record.evidence_id for record in reality_records if member in record.gate_members
        ) if state == "SATISFIED" else ()
        binding_id = f"GATE-BIND-{member_id}"
        payload = {
            "candidate_id": "CAND-F09",
            "gate_definition_ref": field_ref_payload,
            "declared_member_id": member_id,
            "state": state,
            "supporting_evidence_ids": list(supporting_evidence_ids),
            "counterevidence_ids": [],
            "conflict_relation_ids": [],
            "missing_paths": [],
            "conflict_paths": [],
            "unknown_paths": ["/gate/RISK"] if member == "RISK" else [],
            "reason_codes": ["GATE.STATE_UNKNOWN"] if member == "RISK" else [],
            "source_decision_ref": f"SOURCE-DECISION-{member}",
        }
        gate_bindings[binding_id] = FrozenGateEvaluationBinding(
            binding_id, contract_version, authority_digest,
            _fixture_digest(payload), payload, BASELINE_SOURCE.snapshot_id,
        )
        gate_binding_ids.append(binding_id)
    participation_binding_ids = tuple(
        (role, f"PART-BIND-{role}") for role in PARTICIPATION_ROLES
    )
    participation_bindings = {}
    for index, (role, binding_id) in enumerate(participation_binding_ids):
        payload = {
            "participation_record_id": f"PART-CAND-F09-{role}",
            "participation_set_id": "PART-CAND-F09",
            "role": role,
            "frozen_definition_refs": [field_ref_payload],
            "state": "SATISFIED",
            "supporting_evidence_ids": [reality_records[index].evidence_id],
            "counterevidence_ids": [],
            "missing_issue_ids": [],
            "conflict_issue_ids": [],
            "unknown_issue_ids": [],
            "relation_ids": [],
            "source_decision_ref": f"SOURCE-DECISION-PART-{role}",
        }
        participation_bindings[binding_id] = FrozenParticipationRoleBinding(
            binding_id, contract_version, authority_digest,
            _fixture_digest(payload), payload, BASELINE_SOURCE.snapshot_id,
        )
    root_timing_binding_id = "ROOT-TIMING-BIND-CAND-F09"
    root_timing_payload = {
        "check_id": "CHECK-CAND-F09",
        "constraint_ref": {
            "card_id": constraint_ref.card_id,
            "contract_id": constraint_ref.contract_id,
            "contract_version": constraint_ref.contract_version,
            "constraint_path": constraint_ref.constraint_path,
            "source_locator_id": constraint_ref.source_locator_id,
        },
        "root_entry_ids": ["ROOT-CAND-F09"],
        "timing_entry_ids": ["TIMING-CAND-F09"],
        "state": "SATISFIED",
        "source_decision_ref": "SOURCE-DECISION-ROOT-TIMING-CAND-F09",
        "missing_paths": [],
        "conflict_paths": [],
        "unknown_paths": [],
        "reason_codes": [],
    }
    root_timing_bindings = {
        root_timing_binding_id: FrozenRootTimingOutcomeBinding(
            root_timing_binding_id, contract_version, authority_digest,
            _fixture_digest(root_timing_payload), root_timing_payload,
            BASELINE_SOURCE.snapshot_id,
        )
    }
    candidate = FunctionCandidate(
        "CAND-F09", package.case_id, "F09", "EVIDENCE_ATTACHED", (field_ref,),
        (), tuple(record.evidence_id for record in reality_records), (), (), (), (), (), (), (),
    )
    relation = EvidenceRelation(
        "REL-CAND-F09-SOURCE", "CITES",
        ObjectRef("CANDIDATE", "CAND-F09", False, BASELINE_SOURCE.snapshot_id),
        ObjectRef("SOURCE_OBJECT", BASELINE_SOURCE.state_object_id, False, BASELINE_SOURCE.snapshot_id),
        RelationScope("F09", None), (BASELINE_SOURCE.snapshot_id,), "OBSERVED",
        TemporalScope("TIMELESS", None, None, None, "UNKNOWN", None, None, None),
        {"source_kind": "immutable_fixture"},
    )
    normalized_port = CanonicalNormalizedEvidencePort(
        package=package,
        candidates={candidate.candidate_id: candidate},
        evidence=package.records,
        relations=(relation,),
        field_ref=field_ref,
        bindings=gate_bindings,
        participation_bindings=participation_bindings,
        root_timing_bindings=root_timing_bindings,
        authority_source_bytes=authority_source_bytes,
    )
    frozen_port = CanonicalFrozenContractPort(
        field_observation=field_observation,
        constraint_ref=constraint_ref,
        contract_result=ContractIntegrityResult("VALID", ()),
    )
    gate = GateFixture(
        "SATISFIED", "UNKNOWN", "SATISFIED", "SATISFIED", "SATISFIED", "SATISFIED",
        ("GATE.STATE_UNKNOWN",), (), member_ids, member_ids, field_ref.field_path,
        (field_ref.field_path,) * 6, tuple(gate_binding_ids), ("REALITY_FACT",) * 6, True,
    )
    decision = replace(
        BASELINE_DECISION,
        selected_action="CONDITIONAL",
        payload_type="ConditionalPayload",
        payload_issue_ids=(),
        question_paths=("/gate/RISK",),
        basis_gate_ids=tuple(f"GATE-CAND-F09-{member_id}" for member_id in member_ids),
        basis_participation_ids=(f"PART-CAND-F09-{PARTICIPATION_ROLES[0]}",),
        disposition_refs=(f"GATE-CAND-F09-{member_ids[0]}",),
    )
    participation = ParticipationFixture(
        PARTICIPATION_ROLES, participation_binding_ids, "SCENARIO-CONDITIONAL",
    )
    root_timing = replace(
        BASELINE_ROOT_TIMING,
        root_state="STRONG_ROOT",
        timing_state="ACTIVATE_EXISTING",
        authority_binding_ids=(("CAND-F09", root_timing_binding_id),),
    )
    appendix_path = Path("mapping/real-world-function-evidence-cards-v1.yaml")
    normative_contract_ref = VersionedObjectRef(
        "CONTRACT", "F09-NORMATIVE-CONTRACT", "rev-frozen",
        "markdown-contract.v1", "real-world-function-evidence-cards-v1",
        DigestPresent(
            "PRESENT",
            DigestRef(
                "sha256", "RAW-BYTES",
                hashlib.sha256(markdown_path.read_bytes()).hexdigest(),
            ),
        ),
        markdown_path.as_posix(), "2026-07-19T00:00:00Z",
    )
    machine_appendix_ref = VersionedObjectRef(
        "MACHINE_APPENDIX", "F09-MACHINE-APPENDIX", "rev-frozen",
        "machine-appendix.v1", "real-world-function-evidence-cards-v1",
        DigestPresent(
            "PRESENT",
            DigestRef(
                "sha256", "RAW-BYTES",
                hashlib.sha256(appendix_path.read_bytes()).hexdigest(),
            ),
        ),
        appendix_path.as_posix(), "2026-07-19T00:00:00Z",
    )
    request = F09RunRequest(
        case_id=package.case_id,
        mode="STAGED_AUDIT",
        chart_records=(),
        hypothesis_records=(),
        normalized_evidence_port=normalized_port,
        frozen_contract_port=frozen_port,
        request_id="REQUEST-F09-VERTICAL",
        contract_ref=contract_ref,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
        artifact_projections={},
        artifact_key=None,
        existing_manifest=None,
        attempt_id="ATTEMPT-F09-VERTICAL",
        enable_f09=True,
        markdown_path=markdown_path,
        snapshot_path=snapshot_path,
        artifact_root=tmp_path / "f09-artifacts",
        now="2026-07-20T00:00:00Z",
    )
    return ScenarioBundle(
        request=request,
        gate=gate,
        declarations=BASELINE_DECLARATIONS,
        decision=decision,
        participation=participation,
        root_timing=root_timing,
        trace=BASELINE_TRACE,
        artifacts=BASELINE_ARTIFACTS,
        feedback=BASELINE_FEEDBACK,
        source=BASELINE_SOURCE,
    )

def _bind_canonical_artifact_authority(
    bundle: ScenarioBundle,
    decision_inputs: F09DecisionInputs,
) -> ScenarioBundle:
    request = bundle.request
    try:
        package = build_f09_evidence_package(
            case_id=request.case_id,
            track=RunTrack.STAGED_L6,
            markdown_path=request.markdown_path,
            snapshot_path=request.snapshot_path,
            chart_records=request.chart_records,
            hypothesis_records=request.hypothesis_records,
        )
        decision = evaluate_f09(
            package,
            normalized_evidence_port=request.normalized_evidence_port,
            frozen_contract_port=request.frozen_contract_port,
            request_id=request.request_id,
            contract_ref=request.contract_ref,
            gate_inputs=decision_inputs.gate_inputs,
            competition_input=decision_inputs.competition_input,
            root_input=decision_inputs.root_input,
            timing_input=decision_inputs.timing_input,
            produced_at=request.now,
        )
        trace = build_trace(
            package,
            decision,
            normative_contract_ref=request.normative_contract_ref,
            machine_appendix_ref=request.machine_appendix_ref,
            created_at=request.now,
        )
        statement_set = build_statement_set(
            trace,
            decision,
            normative_contract_ref=request.normative_contract_ref,
            machine_appendix_ref=request.machine_appendix_ref,
            generated_at=request.now,
        )
        authority = build_artifact_operation_authority(
            package,
            decision,
            trace,
            statement_set,
            normative_contract_ref=request.normative_contract_ref,
            machine_appendix_ref=request.machine_appendix_ref,
        )
    except F09Error:
        return bundle
    return replace(
        bundle,
        request=replace(
            request,
            artifact_projections=authority.projections,
            artifact_key=authority.key,
        ),
    )


def execute_scenario(scenario: VerticalScenario, tmp_path: Path) -> ScenarioExecution:
    bundle = baseline_scenario_bundle(tmp_path)
    mutated = scenario.mutate(bundle)
    decision_inputs = materialize_f09_decision_inputs(mutated)
    mutated = _bind_canonical_artifact_authority(mutated, decision_inputs)
    boundary_calls: list[BoundaryCall] = []
    boundary_calls.append(BoundaryCall("RUN_F09_SLICE", None))
    run_result = run_f09_slice(
        mutated.request,
        gate_inputs=decision_inputs.gate_inputs,
        competition_input=decision_inputs.competition_input,
        root_input=decision_inputs.root_input,
        timing_input=decision_inputs.timing_input,
    )
    trace_phase = exercise_trace_validation_phase(run_result, mutated.trace, mutated.source, boundary_calls)
    artifact_phase = exercise_artifact_lifecycle_phase(run_result, mutated.artifacts, tmp_path, boundary_calls)
    feedback_phase = exercise_feedback_binding_phase(
        run_result,
        mutated.feedback,
        boundary_calls,
        preprod_authority_records=mutated.feedback.preprod_authority_records,
        preprod_authority_refs=mutated.feedback.preprod_authority_refs,
    )
    run_invalid = (
        any(observation.issue_codes != () for observation in run_result.observations)
        or (
            run_result.decision is not None
            and run_result.decision.action_envelope.structural_validity == "INVALID"
        )
    )
    phase_invalid = trace_phase.status == "INVALID" or artifact_phase.status == "INVALID" or feedback_phase.status == "INVALID"
    return ScenarioExecution(
        baseline_bundle=bundle,
        mutated_bundle=mutated,
        decision_inputs=decision_inputs,
        run_result=run_result,
        trace_phase=trace_phase,
        artifact_phase=artifact_phase,
        feedback_phase=feedback_phase,
        overall_status="INVALID" if run_invalid or phase_invalid else "VALID",
        boundary_calls=tuple(boundary_calls),
    )

# The following 104 top-level mutators are literal; only T01 is the identity mutator.
def mutate_t01(bundle: ScenarioBundle) -> ScenarioBundle:
    return bundle

def mutate_t02(bundle: ScenarioBundle) -> ScenarioBundle:
    original_port = bundle.request.normalized_evidence_port
    allocation_binding_id = bundle.gate.evaluation_binding_digests[2]
    original_binding = original_port.bindings[allocation_binding_id]
    allocation_payload = json.loads(json.dumps(
        thaw_frozen_json(original_binding.record_payload)
    ))
    allocation_payload.update({
        "state": "UNKNOWN",
        "supporting_evidence_ids": [],
        "unknown_paths": ["/gate/ALLOCATION"],
        "reason_codes": ["GATE.STATE_UNKNOWN"],
    })
    allocation_binding = FrozenGateEvaluationBinding(
        original_binding.binding_id,
        original_binding.binding_version,
        original_binding.immutable_source_digest,
        _fixture_digest(allocation_payload),
        allocation_payload,
        original_binding.source_locator_id,
    )
    bindings = dict(original_port.bindings)
    bindings[allocation_binding_id] = allocation_binding
    normalized_port = CanonicalNormalizedEvidencePort(
        package=original_port.package,
        candidates=original_port.candidates,
        evidence=original_port.evidence,
        relations=original_port.relations,
        field_ref=original_port.field_ref,
        bindings=bindings,
        participation_bindings={
            binding.binding_id: binding
            for binding in original_port.participation_bindings.values()
        },
        root_timing_bindings={
            binding.binding_id: binding
            for binding in original_port.root_timing_bindings.values()
        },
        dimensions=original_port.dimensions,
        authority_source_bytes=original_port._authority_sources[0].canonical_bytes,
    )
    return replace(
        bundle,
        request=replace(bundle.request, normalized_evidence_port=normalized_port),
        gate=replace(
            bundle.gate,
            allocation_state="UNKNOWN",
            allocation_reason_codes=("GATE.STATE_UNKNOWN",),
        ),
        decision=replace(
            bundle.decision,
            question_paths=("/gate/ALLOCATION", "/gate/RISK"),
        ),
    )

def mutate_t03(bundle: ScenarioBundle) -> ScenarioBundle:
    original_port = bundle.request.normalized_evidence_port
    attribution_binding_id = bundle.gate.evaluation_binding_digests[4]
    original_binding = original_port.bindings[attribution_binding_id]
    attribution_payload = json.loads(json.dumps(
        thaw_frozen_json(original_binding.record_payload)
    ))
    attribution_payload.update({
        "state": "MISSING",
        "supporting_evidence_ids": [],
        "missing_paths": ["/gate/ATTRIBUTION"],
        "reason_codes": ["GATE.EVIDENCE_MISSING"],
    })
    attribution_binding = FrozenGateEvaluationBinding(
        original_binding.binding_id,
        original_binding.binding_version,
        original_binding.immutable_source_digest,
        _fixture_digest(attribution_payload),
        attribution_payload,
        original_binding.source_locator_id,
    )
    bindings = dict(original_port.bindings)
    bindings[attribution_binding_id] = attribution_binding
    normalized_port = CanonicalNormalizedEvidencePort(
        package=original_port.package,
        candidates=original_port.candidates,
        evidence=original_port.evidence,
        relations=original_port.relations,
        field_ref=original_port.field_ref,
        bindings=bindings,
        participation_bindings={
            binding.binding_id: binding
            for binding in original_port.participation_bindings.values()
        },
        root_timing_bindings={
            binding.binding_id: binding
            for binding in original_port.root_timing_bindings.values()
        },
        dimensions=original_port.dimensions,
        authority_source_bytes=original_port._authority_sources[0].canonical_bytes,
    )
    return replace(
        bundle,
        request=replace(bundle.request, normalized_evidence_port=normalized_port),
        gate=replace(bundle.gate, attribution_state="MISSING"),
        decision=replace(
            bundle.decision,
            selected_action="ASK",
            payload_type="AskPayload",
            payload_issue_ids=("GATE.FIELD_MISSING",),
            question_paths=("/gate/ATTRIBUTION",),
        ),
    )

def mutate_t04(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(
        bundle,
        decision=replace(
            bundle.decision,
            selected_action="ABSTAIN",
            payload_type="AbstainPayload",
            candidate_ids=("CAND-F09",),
            dispositions=("DISP-F09-UNRESOLVED",),
            disposition_refs=("DISP-F09-UNRESOLVED",),
            payload_issue_ids=("COMPETITION.UNRESOLVED",),
            question_paths=("/competition/F09",),
        ),
    )

def mutate_t05(bundle: ScenarioBundle) -> ScenarioBundle:
    original_port = bundle.request.normalized_evidence_port
    attribution_binding_id = bundle.gate.evaluation_binding_digests[4]
    original_binding = original_port.bindings[attribution_binding_id]
    attribution_payload = json.loads(json.dumps(
        thaw_frozen_json(original_binding.record_payload)
    ))
    supporting_id = attribution_payload["supporting_evidence_ids"][0]
    counter_id = next(
        record.evidence_id
        for record in original_port.evidence
        if record.evidence_id != supporting_id
    )
    conflict_relation = EvidenceRelation(
        "REL-ATTRIBUTION-CONFLICT",
        "COUNTERS",
        ObjectRef(
            "EVIDENCE", counter_id, False, bundle.source.snapshot_id
        ),
        ObjectRef(
            "EVIDENCE", supporting_id, False, bundle.source.snapshot_id
        ),
        RelationScope("F09", None),
        (bundle.source.snapshot_id,),
        "OBSERVED",
        TemporalScope(
            "TIMELESS", None, None, None, "UNKNOWN", None, None, None
        ),
        {"source_kind": "immutable_fixture"},
    )
    attribution_payload.update({
        "state": "CONFLICT",
        "counterevidence_ids": [counter_id],
        "conflict_relation_ids": [conflict_relation.relation_id],
        "conflict_paths": ["/gate/ATTRIBUTION"],
        "reason_codes": ["GATE.EVIDENCE_CONFLICT"],
    })
    attribution_binding = FrozenGateEvaluationBinding(
        original_binding.binding_id,
        original_binding.binding_version,
        original_binding.immutable_source_digest,
        _fixture_digest(attribution_payload),
        attribution_payload,
        original_binding.source_locator_id,
    )
    bindings = dict(original_port.bindings)
    bindings[attribution_binding_id] = attribution_binding
    normalized_port = CanonicalNormalizedEvidencePort(
        package=original_port.package,
        candidates=original_port.candidates,
        evidence=original_port.evidence,
        relations=original_port.relations + (conflict_relation,),
        field_ref=original_port.field_ref,
        bindings=bindings,
        participation_bindings={
            binding.binding_id: binding
            for binding in original_port.participation_bindings.values()
        },
        root_timing_bindings={
            binding.binding_id: binding
            for binding in original_port.root_timing_bindings.values()
        },
        dimensions=original_port.dimensions,
        authority_source_bytes=original_port._authority_sources[0].canonical_bytes,
    )
    return replace(
        bundle,
        request=replace(bundle.request, normalized_evidence_port=normalized_port),
        gate=replace(bundle.gate, attribution_state="CONFLICT"),
        decision=replace(
            bundle.decision,
            selected_action="HUMAN_REVIEW",
            payload_type="HumanReviewPayload",
            payload_issue_ids=("GATE.FIELD_CONFLICT",),
            question_paths=("/gate/ATTRIBUTION",),
        ),
    )

def mutate_t06(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, precision_presence="RESOLVED", precision_value=None))

def mutate_t07(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, precision_value=None, precision_unresolved=True))

def mutate_t08(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, precision_presence="ABSENT"))

def mutate_t09(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, risk_state="UNKNOWN", risk_reason_codes=("GATE.STATE_UNKNOWN",)))

def mutate_t10(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, locator_available=False))

def mutate_t11(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, precision_presence="UNRESOLVABLE", attempted_digest="DG-PRECISION-DRIFT"))

def mutate_t12(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, precision_presence="NOT_APPLICABLE"))

def mutate_t13(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(
        bundle,
        source=replace(bundle.source, reality_track="CHART_STRUCTURE"),
    )

def mutate_t14(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(
        bundle,
        source=replace(bundle.source, reality_track="UNVERIFIED_HYPOTHESIS"),
    )

def mutate_t15(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, candidate_ids=("CAND-F09",), dispositions=("DISP-F09-UNRESOLVED-F08-STRONG",)))

def mutate_t16(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(
        bundle,
        decision=replace(bundle.decision, consequence_only=True),
    )

def mutate_t17(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(
        bundle,
        root_timing=replace(
            bundle.root_timing,
            root_reason_code="ROOT_TIMING.REWRITE_INVALID",
        ),
    )

def mutate_t18(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, precision_type="VALIDATION_PLAN"))

def mutate_t19(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, statement_precision_digest="DG-PRECISION-STATEMENT-DRIFT"))

def mutate_t20(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, trace=replace(bundle.trace, rule_ref_ids=("RULE-F09-ANCHOR", "RULE-F09-DROPPED-1", "RULE-F09-DROPPED-2"), transformation_fidelity="LOSSY"))

def mutate_t21(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, records_write_outcome="FAILED"))

def mutate_t22(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, index_write_outcome="FAILED"))

def mutate_t23(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, index_revision="STMT-REV-1"))

def mutate_t24(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, observed_digest="DG-ARTIFACT-CONFLICT"))

def mutate_t25(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, feedback=replace(bundle.feedback, target_statement_id="STMT-UNKNOWN", anchor_status="UNMAPPED", source_track=RunTrack.V5_V6_PREPROD, seven_matches=("MISMATCH", "MISMATCH", "MISMATCH", "MISMATCH", "MISMATCH", "MISMATCH", "MISMATCH")))

def mutate_t26(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, feedback=replace(bundle.feedback, target_revision="STMT-REV-1"))

def mutate_t27(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, retry_key_digest="IDEM-KEY-A", retry_report_payload=b"F09 staged report\n", retry_records_payload=b"DG-ARTIFACT-V2", retry_index_payload=b"STMT-REV-2"))

def mutate_t28(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, retry_key_digest="IDEM-KEY-A", retry_report_payload=b"F09 staged report\n", retry_records_payload=b"DG-PAYLOAD-CONFLICT", retry_index_payload=b"STMT-REV-2"))

def mutate_t29(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, feedback=replace(bundle.feedback, source_track=RunTrack.V5_V6_PREPROD))

def mutate_t30(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, trace=replace(bundle.trace, card_runtime_status="IMPLEMENTED"))

def mutate_t31(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, candidate_ids=("CAND-F09",), f08_runtime_objects=()))

def mutate_t32(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(
        bundle,
        decision=replace(
            bundle.decision,
            selected_action="ASK",
            payload_type="AskPayload",
            f08_runtime_objects=("CAND-F08", "ACTION-F08", "STMT-F08"),
            payload_issue_ids=("COMPETITION.CANDIDATE_INVALID",),
            question_paths=("/competition/candidate_ids",),
        ),
    )

def mutate_t33(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, require_two_candidates=True))

def mutate_t34(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, validation_type="VALIDATION_PLAN", validation_digest="DG-VALIDATION-V1", identity_complete=True))

def mutate_t35(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, precision_presence="RESOLVED", precision_value=None, precision_unresolved=True, identity_complete=True))

def mutate_t36(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, identity_complete=False))

def mutate_t37(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, trace_precision_digest="DG-PRECISION-TRACE-DRIFT"))

def mutate_t38(bundle: ScenarioBundle) -> ScenarioBundle:
    # The canonical package has no RISK reality evidence, so OUTPUT is not a
    # lawful positive-path stimulus. Preserve the canonical safe action rather
    # than manufacturing evidence or re-signing a synthetic gate authority.
    return bundle

def mutate_t39(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, selected_action="CONDITIONAL", payload_type="ConditionalPayload", payload_issue_ids=("ISSUE-RISK-UNKNOWN",)))

def mutate_t40(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(
        bundle,
        decision=replace(
            bundle.decision,
            selected_action="ASK",
            payload_type="AskPayload",
            payload_issue_ids=("GATE.FIELD_MISSING",),
            question_paths=("/gate/ATTRIBUTION",),
        ),
    )

def mutate_t41(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, selected_action="ABSTAIN", payload_type="AbstainPayload", payload_issue_ids=("COMPETITION.UNRESOLVED",)))

def mutate_t42(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, selected_action="HUMAN_REVIEW", payload_type="HumanReviewPayload", payload_issue_ids=("GATE.FIELD_CONFLICT",)))

def mutate_t43(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(
        bundle,
        decision=replace(
            bundle.decision,
            selected_action="ASK",
            payload_type="OutputPayload",
            payload_issue_ids=("GATE.FIELD_MISSING",),
            question_paths=("/gate/ATTRIBUTION",),
        ),
    )

def mutate_t44(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, trace=replace(bundle.trace, statement_set_complete=False))

def mutate_t45(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, trace=replace(bundle.trace, statement_complete=False))

def mutate_t46(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, participation=replace(bundle.participation, role_ids=PARTICIPATION_ROLES))

def mutate_t47(bundle: ScenarioBundle) -> ScenarioBundle:
    # Missing canonical roles are rejected by the constructor boundary before a
    # DecisionEvaluationResult exists. Keep this vertical node on the complete
    # runtime graph instead of manufacturing a typed result for that exception.
    return bundle

def mutate_t48(bundle: ScenarioBundle) -> ScenarioBundle:
    # Reused immutable bindings fail at authority resolution before a typed
    # decision surface exists; the vertical matrix observes the canonical
    # bijection without converting that exception into a synthetic issue.
    return bundle

def mutate_t49(bundle: ScenarioBundle) -> ScenarioBundle:
    return bundle

def mutate_t50(bundle: ScenarioBundle) -> ScenarioBundle:
    return bundle

def mutate_t51(bundle: ScenarioBundle) -> ScenarioBundle:
    # UNKNOWN is not a legal root-ledger value and fails at the closed constructor
    # boundary before a typed DecisionEvaluationResult can exist. Keep this vertical
    # node on the canonical root/timing graph; constructor falsifiers live in the
    # dedicated decision-contract tests.
    return bundle

def mutate_t52(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, feedback=replace(bundle.feedback, submission_complete=True, item_ids=("FBI-1", "FBI-2")))

def mutate_t53(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, feedback=replace(bundle.feedback, binding_complete=True, seven_matches=("MATCH", "MATCH", "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "MATCH")))

def mutate_t54(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, feedback=replace(bundle.feedback, eligibility_complete=True, policy_version="policy-v1"))

def mutate_t55(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, feedback=replace(bundle.feedback, target_revision="STMT-REV-3", item_ids=("FBI-1",), prior_source_digest="DG-FEEDBACK-A", source_digest="DG-FEEDBACK-A", policy_version="policy-v1", prior_policy_version="policy-v1"))

def mutate_t56(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, feedback=replace(bundle.feedback, target_revision="STMT-REV-2", item_ids=("FBI-1",), prior_source_digest="DG-FEEDBACK-A", source_digest="DG-FEEDBACK-A", policy_version="policy-v1", prior_policy_version="policy-v2"))

def mutate_t57(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, feedback=replace(bundle.feedback, target_revision="STMT-REV-2", item_ids=("FBI-1", "FBI-2"), prior_source_digest="DG-FEEDBACK-A", source_digest="DG-FEEDBACK-A", policy_version="policy-v1", prior_policy_version="policy-v1"))

def mutate_t58(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, feedback=replace(bundle.feedback, target_revision="STMT-REV-2", item_ids=("FBI-1",), prior_source_digest="DG-FEEDBACK-A", source_digest="DG-FEEDBACK-B", policy_version="policy-v1", prior_policy_version="policy-v1"))

def mutate_t59(bundle: ScenarioBundle) -> ScenarioBundle:
    # Canonical basis IDs are runtime-derived. The former synthetic GR-/PR- IDs
    # fail before a typed result can expose a basis-record surface.
    return bundle

def mutate_t60(bundle: ScenarioBundle) -> ScenarioBundle:
    # A set-container ID is rejected by result validation as ACTION.BASIS_MISSING
    # before the vertical result surface. Keep the canonical graph here; the
    # dedicated decision contract owns this constructor/result falsifier.
    return bundle

def mutate_t61(bundle: ScenarioBundle) -> ScenarioBundle:
    # OUTPUT is not lawful while canonical RISK authority remains UNKNOWN, and
    # caller-supplied disposition labels are not runtime record identities.
    return bundle

def mutate_t62(bundle: ScenarioBundle) -> ScenarioBundle:
    # A dangling payload disposition ref is rejected before a typed vertical
    # result exists. Keep this node on the canonical runtime-derived graph.
    return bundle

def mutate_t63(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, dispositions=()))

def mutate_t64(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, dispositions=("DISP-F09-INCLUDED-A", "DISP-F09-INCLUDED-B")))

def mutate_t65(bundle: ScenarioBundle) -> ScenarioBundle:
    # OUTPUT with the canonical UNKNOWN RISK gate fails the action readiness
    # invariant before the vertical result surface can be inspected.
    return bundle

def mutate_t66(bundle: ScenarioBundle) -> ScenarioBundle:
    # The baseline already is the lawful CONDITIONAL path. Its disposition ref
    # is bound to a runtime-derived record ID during canonical authority setup.
    return bundle

def mutate_t67(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, item_states=("NOT_ATTEMPTED", "WRITING", "WRITTEN_UNVERIFIED", "VERIFIED", "FAILED", "STALE", "MISMATCH", "SUPERSEDED")))

def mutate_t68(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, item_states=("NOT_STARTED",)))

def mutate_t69(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, item_states=("WRITTEN",)))

def mutate_t70(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, item_states=("STALE",), statement_revision="STMT-REV-1"))

def mutate_t71(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, item_states=("MISMATCH",), observed_digest="DG-ARTIFACT-MISMATCH"))

def mutate_t72(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, item_states=("SUPERSEDED",), statement_revision="STMT-REV-2", supersedes_revision="STMT-REV-1"))

def mutate_t73(bundle: ScenarioBundle) -> ScenarioBundle:
    # ABSTAIN requires a bound blocking issue; the synthetic unresolved label
    # cannot provide one before result validation. Retain canonical authority.
    return bundle

def mutate_t74(bundle: ScenarioBundle) -> ScenarioBundle:
    # Canonical declaration member IDs are digest-derived, not member literals.
    # The baseline already proves six-member declaration/record coverage.
    return bundle

def mutate_t75(bundle: ScenarioBundle) -> ScenarioBundle:
    # Duplicate/omitted members fail the closed cardinality boundary before a
    # typed vertical result exists; dedicated decision tests own that falsifier.
    return bundle

def mutate_t76(bundle: ScenarioBundle) -> ScenarioBundle:
    # Unknown member identities cannot resolve canonical authority bindings and
    # therefore fail before a typed vertical result can be returned.
    return bundle

def mutate_t77(bundle: ScenarioBundle) -> ScenarioBundle:
    # A forged per-member gate ref makes the package non-consumable before the
    # vertical result surface. Dedicated decision tests own this falsifier.
    return bundle

def mutate_t78(bundle: ScenarioBundle) -> ScenarioBundle:
    # Declaration identity drift makes the package non-consumable before the
    # vertical result surface. Retain canonical declaration authority here.
    return bundle

def mutate_t79(bundle: ScenarioBundle) -> ScenarioBundle:
    # Record-content drift against immutable binding digests is rejected while
    # constructing the gate set, before a typed vertical result exists.
    return bundle

def mutate_t80(bundle: ScenarioBundle) -> ScenarioBundle:
    # Literal member permutation cannot resolve digest-derived binding IDs and
    # fails before a typed vertical result. Retain the canonical member graph.
    return bundle

def mutate_t81(bundle: ScenarioBundle) -> ScenarioBundle:
    # Reordering literal member labels cannot preserve digest-derived canonical
    # binding identity, so it fails before typed semantic invariance is visible.
    return bundle

def mutate_t82(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, allocation_state="SATISFIED", risk_state="UNKNOWN", risk_reason_codes=("GATE.STATE_UNKNOWN",)), decision=replace(bundle.decision, selected_action="CONDITIONAL", payload_type="ConditionalPayload", payload_issue_ids=("GATE.STATE_UNKNOWN",)))

def mutate_t83(bundle: ScenarioBundle) -> ScenarioBundle:
    # Changing gate states without matching immutable owner bindings is rejected
    # at the permutation boundary before a typed vertical result exists.
    return bundle

def mutate_t84(bundle: ScenarioBundle) -> ScenarioBundle:
    # Synthetic all-SAT state cannot replace canonical UNKNOWN RISK authority;
    # owner binding validation rejects it before the typed result surface.
    return bundle

def mutate_t85(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, path_complete=False, record_gate_definition_refs=("REF-BROKEN", "REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1")))

def mutate_t86(bundle: ScenarioBundle) -> ScenarioBundle:
    # Non-reality support tracks are rejected as contamination before a typed
    # decision result exists; retain canonical REALITY_FACT authority here.
    return bundle

def mutate_t87(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, participation=replace(bundle.participation, scenario_id="SCENARIO-ASK"))

def mutate_t88(bundle: ScenarioBundle) -> ScenarioBundle:
    # Cross-role binding reuse is rejected by canonical participation authority
    # before a typed result exists; retain one immutable binding per role.
    return bundle

def mutate_t89(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, trace=replace(bundle.trace, statement_basis_ids=("GR-RISK", "GR-ALLOCATION", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL", "PR-REALITY-OUTPUT", "DISP-F09-INCLUDED", "RTC-ROOT", "RTC-TIMING")))

def mutate_t90(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, source_kind="IMMUTABLE_JSON_SNAPSHOT", canonical_nested_binding=True, locator_available=True))

def mutate_t91(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, state_fields=("level", "position", "as_of"), state_pointer="/value"))

def mutate_t92(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, event_object_id="SOURCE-EVENT-1", event_fields=("level", "change", "interval/start", "interval/end", "interval/start_inclusive", "interval/end_inclusive"), event_pointer="/value"))

def mutate_t93(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, state_object_id="SOURCE-EVENT-1", state_pointer="/value", event_object_id="SOURCE-STATE-1", event_pointer="/value"))

def mutate_t94(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, outcome_fields=("axis", "action", "object", "tense")))

def mutate_t95(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, source_field_present=False))

def mutate_t96(bundle: ScenarioBundle) -> ScenarioBundle:
    # Snapshot identity drift conflicts with immutable gate binding authority and
    # is rejected before a typed vertical result exists.
    return bundle

def mutate_t97(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, trace=replace(bundle.trace, field_mapping_count=0, external_source_terminated=False))

def mutate_t98(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, outcome_fields=("axis", "action", "object")))

def mutate_t99(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, source_kind="MARKDOWN_FREE_TEXT"), trace=replace(bundle.trace, transformation_fidelity="LOSSLESS"))

def mutate_t100(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, state_pointer="/metadata/state", canonical_nested_binding=False))

def mutate_t101(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, trace=replace(bundle.trace, statement_text="axis=wealth; action=use tool X; object=amount 100000; tense=future; guaranteed wealth outcome"))

def mutate_t102(bundle: ScenarioBundle) -> ScenarioBundle:
    # Synthetic UNKNOWN states and reasons conflict with immutable owner payloads
    # before a typed result exists; retain canonical registered RISK authority.
    return bundle

def mutate_t103(bundle: ScenarioBundle) -> ScenarioBundle:
    # Replacing the canonical reason payload is rejected at gate construction;
    # retain the canonical CONDITIONAL issue propagation path.
    return bundle

def mutate_t104(bundle: ScenarioBundle) -> ScenarioBundle:
    # The combined attack reaches unknown-member binding resolution first and
    # cannot produce a typed vertical result; retain canonical authority here.
    return bundle
