import ast
from dataclasses import asdict, fields, replace
import hashlib
import inspect
import json
from types import MappingProxyType

import pytest

import engine.f09.decision as decision_module
from engine.f09.canonical_json import canonicalize_bounded_jcs
from engine.f09.contracts import (
    ContractIntegrityResult,
    ContractVersionRef,
    DecisionAction,
    DigestRef,
    EvidenceRelation,
    EvidenceTrack,
    FunctionCandidate,
    FrozenConstraintRef,
    FrozenFieldObservation,
    FrozenGateEvaluationBinding,
    FrozenParticipationRoleBinding,
    FrozenRootTimingOutcomeBinding,
    NormalizedEvidenceReadPort,
    ObjectRef,
    RelationScope,
    FrozenContractReadPort,
    thaw_frozen_json,
)
from engine.f09.decision import (
    AbstainPayload,
    AskPayload,
    ConditionalPayload,
    HumanReviewPayload,
    OutputPayload,
    PARTICIPATION_ROLES,
    evaluate_f09,
    validate_decision_result,
)


HEX = "1" * 64
DIGEST = DigestRef("sha256", "RFC8785-JCS-UTF8", HEX)
FIXED_RESOURCE_CANONICAL_BYTES = (
    b'{"candidate_id":"CANDIDATE-1","conflict_paths":[],"conflict_relation_ids":[],'
    b'"counterevidence_ids":[],"declared_member_id":"F09-MEMBER-dd69534a2c5c876333236ae8",'
    b'"gate_definition_ref":{"card_id":"F09","contract_id":"real-world-function-evidence-cards-v1",'
    b'"contract_version":"v1","declared_state":"PRESENT_VALUE","declared_value":'
    b'["RESOURCE","OBJECT","ALLOCATION","RISK","ATTRIBUTION","TENSE"],'
    b'"field_path":"/cards/F09/gates","source_locator_id":"SNAP-1"},"missing_paths":[],'
    b'"reason_codes":[],"source_decision_ref":"SOURCE-DECISION-RESOURCE","state":"SATISFIED",'
    b'"supporting_evidence_ids":["REALITY-RESOURCE"],"unknown_paths":[]}'
)


def _evaluate(case):
    return evaluate_f09(
        case["package"],
        normalized_evidence_port=case["normalized_evidence_port"],
        frozen_contract_port=case["frozen_contract_port"],
        request_id="REQUEST-1",
        contract_ref=case["contract_ref"],
        gate_inputs=case["gate_inputs"],
        competition_input=case["competition_input"],
        root_input=case["root_input"],
        timing_input=case["timing_input"],
        produced_at=case["produced_at"],
    )


def _first_binding(case):
    binding_id = case["gate_inputs"][0].gate.evaluation_binding_digests[0]
    return binding_id, case["normalized_evidence_port"].bindings[binding_id]


def _mutable_json(value):
    if type(value) is tuple:
        return [_mutable_json(item) for item in value]
    if type(value) is MappingProxyType:
        return {key: _mutable_json(item) for key, item in value.items()}
    return value


def _independent_digest(payload):
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return DigestRef("sha256", "RFC8785-JCS-UTF8", hashlib.sha256(canonical).hexdigest())


def _replace_binding(binding, **changes):
    payload = _mutable_json(changes.pop("record_payload", binding.record_payload))
    values = {
        "binding_id": binding.binding_id,
        "binding_version": binding.binding_version,
        "immutable_source_digest": binding.immutable_source_digest,
        "canonical_record_digest": binding.canonical_record_digest,
        "record_payload": payload,
        "source_locator_id": binding.source_locator_id,
    }
    values.update(changes)
    return type(binding)(**values)


def _replace_relation(relation, **changes):
    return replace(relation, metadata=_mutable_json(relation.metadata), **changes)


def _authorize_gate_binding(port, binding):
    authorized = dict(port._authorized_gate_record_digests)
    authorized[binding.binding_id] = binding.canonical_record_digest
    port._authorized_gate_record_digests = MappingProxyType(authorized)


def _independent_gate_record_digest(record):
    return _independent_digest(
        {
            "candidate_id": record.candidate_id,
            "gate_definition_ref": asdict(record.gate_definition_ref),
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
    )


@pytest.fixture
def evaluated(decision_case):
    return _evaluate(decision_case)


def test_exact_frozen_input_graph_and_direct_wrapper_construction(canonical_decision_input_types):
    expected_fields = {
        "GateInputState": ("allocation_state", "risk_state", "reality_state", "attribution_state", "source_state", "temporal_state", "risk_reason_codes", "allocation_reason_codes", "member_ids", "declared_member_ids", "gate_definition_ref", "record_gate_definition_refs", "evaluation_binding_digests", "supporting_evidence_tracks", "path_complete"),
        "DeclarationInputState": ("precision_presence", "precision_value", "precision_unresolved", "precision_type", "precision_digest", "precision_contract_version", "validation_type", "validation_digest", "attempted_digest", "identity_complete", "statement_precision_digest", "trace_precision_digest"),
        "DecisionInputState": ("selected_action", "payload_type", "payload_issue_ids", "question_paths", "basis_gate_ids", "basis_participation_ids", "disposition_refs", "candidate_ids", "dispositions", "f08_runtime_objects", "require_two_candidates", "consequence_only"),
        "ParticipationInputState": ("role_ids", "role_authority_binding_ids", "scenario_id"),
        "RootTimingInputState": ("root_state", "root_reason_code", "root_issue_path", "timing_state", "timing_reason_code", "timing_issue_path", "timing_rewrites_root", "authority_binding_ids"),
        "SourceInputState": ("locator_available", "reality_track", "state_object_id", "state_pointer", "state_fields", "event_object_id", "event_pointer", "event_fields", "outcome_fields", "snapshot_id", "snapshot_schema_version", "contract_version", "content_digest", "captured_at", "payload_digest", "source_field_present", "source_kind", "canonical_nested_binding"),
        "GateEvaluationInput": ("gate", "declarations", "participation", "source"),
        "CompetitionInput": ("decision", "source"),
        "RootInput": ("root_timing", "source"),
        "TimingInput": ("root_timing", "source"),
    }
    assert set(canonical_decision_input_types) == set(expected_fields)
    for name, runtime_type in canonical_decision_input_types.items():
        assert tuple(field.name for field in fields(runtime_type)) == expected_fields[name]
        assert runtime_type.__dataclass_params__.frozen
        assert not hasattr(runtime_type, "from_frozen_fixture")


def test_ports_and_binding_are_canonical_contract_types(decision_case):
    assert isinstance(decision_case["normalized_evidence_port"], NormalizedEvidenceReadPort)
    assert isinstance(decision_case["frozen_contract_port"], FrozenContractReadPort)
    assert tuple(field.name for field in fields(FrozenGateEvaluationBinding)) == (
        "binding_id", "binding_version", "immutable_source_digest",
        "canonical_record_digest", "record_payload", "source_locator_id",
    )
    for binding_type in (FrozenParticipationRoleBinding, FrozenRootTimingOutcomeBinding):
        assert tuple(field.name for field in fields(binding_type)) == (
            "binding_id", "binding_version", "immutable_source_digest",
            "canonical_record_digest", "record_payload", "source_locator_id",
        )
        assert binding_type.__dataclass_params__.frozen
    assert FrozenParticipationRoleBinding is not FrozenRootTimingOutcomeBinding
    assert not issubclass(FrozenParticipationRoleBinding, FrozenGateEvaluationBinding)
    assert not issubclass(FrozenRootTimingOutcomeBinding, FrozenGateEvaluationBinding)
    assert tuple(inspect.signature(NormalizedEvidenceReadPort.get_participation_role_binding).parameters) == ("self", "binding_id")
    assert tuple(inspect.signature(NormalizedEvidenceReadPort.get_root_timing_outcome_binding).parameters) == ("self", "binding_id")
    assert tuple(field.name for field in fields(FrozenFieldObservation)) == (
        "ref", "source_state", "value", "unresolved_state_ref", "source_location",
    )
    assert type(decision_case["normalized_evidence_port"].get_package("PKG-1")).__name__ == "NormalizedEvidencePackage"
    candidate = decision_case["normalized_evidence_port"].get_candidate("CANDIDATE-1")
    relation = decision_case["normalized_evidence_port"].list_relations("CANDIDATE-1")[0]
    assert type(candidate) is FunctionCandidate
    assert tuple(field.name for field in fields(FunctionCandidate)) == (
        "candidate_id", "case_id", "function_id", "status", "card_refs",
        "structure_evidence_ids", "reality_evidence_ids", "hypothesis_evidence_ids",
        "counterevidence_ids", "root_evidence_ids", "timing_evidence_ids",
        "competing_candidate_ids", "competition_dimensions", "unresolved_fields",
    )
    assert candidate.status == "EVIDENCE_ATTACHED" and candidate.card_refs
    assert type(relation) is EvidenceRelation
    assert tuple(field.name for field in fields(EvidenceRelation)) == (
        "relation_id", "relation_type", "from_ref", "to_ref", "scope",
        "source_refs", "status", "temporal_scope", "metadata",
    )
    assert relation.scope.function_id == "F09" and relation.source_refs and relation.status == "OBSERVED"
    assert type(decision_case["contract_ref"]) is ContractVersionRef
    signature = inspect.signature(evaluate_f09)
    assert signature.parameters["normalized_evidence_port"].kind is inspect.Parameter.KEYWORD_ONLY
    assert signature.parameters["frozen_contract_port"].kind is inspect.Parameter.KEYWORD_ONLY


@pytest.mark.parametrize(
    "resolver_name",
    ["get_participation_role_binding", "get_root_timing_outcome_binding"],
)
def test_new_resolver_empty_and_zero_match_failures(decision_case, resolver_name):
    resolver = getattr(decision_case["normalized_evidence_port"], resolver_name)
    with pytest.raises(ValueError, match="nonempty"):
        resolver("")
    with pytest.raises(KeyError):
        resolver("MISSING-BINDING")


def _replace_fixture_declared_authority(port, locator_id, **changes):
    authorities = dict(port._declared_source_authorities)
    authorities[locator_id] = replace(authorities[locator_id], **changes)
    port._declared_source_authorities = MappingProxyType(authorities)


def _copy_fixture_declared_authority(port, old_locator_id, new_locator_id, **changes):
    authorities = dict(port._declared_source_authorities)
    authority = authorities[old_locator_id]
    authorities[new_locator_id] = replace(authority, locator_id=new_locator_id, **changes)
    port._declared_source_authorities = MappingProxyType(authorities)


def _mutate_fixture_resolver_authority(port, store, binding_id, mutation):
    binding = store[binding_id]
    source_index = next(
        index for index, source in enumerate(port._authority_sources)
        if source.binding_id == binding_id
    )
    source = port._authority_sources[source_index]
    drifted_bytes = b'{"fixture":"drifted"}'
    drifted_digest = DigestRef(
        "sha256", "RFC8785-JCS-UTF8", hashlib.sha256(drifted_bytes).hexdigest(),
    )
    if mutation == "source_missing":
        del port._authority_sources[source_index]
    elif mutation == "not_immutable":
        port._authority_sources[source_index] = replace(source, immutable_provable=False)
    elif mutation == "duplicate_source":
        port._authority_sources.append(source)
    elif mutation == "actual_bytes_digest_mismatch":
        port._authority_sources[source_index] = replace(source, canonical_bytes=drifted_bytes)
    elif mutation == "declared_digest_mismatch":
        _replace_fixture_declared_authority(port, source.locator_id, declared_digest=drifted_digest)
    elif mutation == "binding_digest_mismatch":
        store[binding_id] = _replace_binding(binding, immutable_source_digest=drifted_digest)
    elif mutation == "synchronized_source_and_binding_forgery":
        port._authority_sources[source_index] = replace(source, canonical_bytes=drifted_bytes)
        store[binding_id] = _replace_binding(binding, immutable_source_digest=drifted_digest)
    elif mutation == "locator_mismatch":
        port._authority_sources[source_index] = replace(source, locator_id="OTHER")
    elif mutation == "version_mismatch":
        port._authority_sources[source_index] = replace(source, binding_version="v2")
    else:
        store.append(binding)


def _replace_fixture_authority_source(port, binding_id, **changes):
    source_index = next(
        index for index, source in enumerate(port._authority_sources)
        if source.binding_id == binding_id
    )
    port._authority_sources[source_index] = replace(port._authority_sources[source_index], **changes)


def _synchronize_fixture_authority_version(port, locator_id, binding_version):
    for store in (port.participation_bindings, port.root_timing_bindings):
        for binding in store.values():
            if binding.source_locator_id == locator_id:
                store[binding.binding_id] = _replace_binding(binding, binding_version=binding_version)
    port._authority_sources = [
        replace(source, binding_version=binding_version)
        if source.locator_id == locator_id else source
        for source in port._authority_sources
    ]
    _replace_fixture_declared_authority(port, locator_id, binding_version=binding_version)


RESOLVER_SOURCE_FALSIFIERS = (
    ("source_missing", "immutable authority source missing"),
    ("not_immutable", "authority source immutability is not provable"),
    ("duplicate_source", "multiple immutable authority source matches"),
    ("actual_bytes_digest_mismatch", "actual authority source digest does not match declared digest"),
    ("declared_digest_mismatch", "actual authority source digest does not match declared digest"),
    ("binding_digest_mismatch", "authority binding digest does not match declared digest"),
    ("synchronized_source_and_binding_forgery", "actual authority source digest does not match declared digest"),
    ("locator_mismatch", "authority source locator mismatch"),
    ("version_mismatch", "authority source binding version mismatch"),
    ("duplicate_binding_match", "multiple authority binding matches"),
)


@pytest.mark.parametrize(("mutation", "message"), RESOLVER_SOURCE_FALSIFIERS)
def test_participation_fixture_resolver_proves_immutable_authority_source(
    decision_case, mutation, message,
):
    # Resolver layer: source record, independent declared locator authority and
    # binding envelope are mutated separately; consumer validation is not invoked.
    binding_id, _ = _role_binding(decision_case)
    port = decision_case["normalized_evidence_port"]
    _mutate_fixture_resolver_authority(port, port.participation_bindings, binding_id, mutation)
    with pytest.raises(ValueError, match=message):
        port.get_participation_role_binding(binding_id)


@pytest.mark.parametrize(("mutation", "message"), RESOLVER_SOURCE_FALSIFIERS)
def test_root_timing_fixture_resolver_proves_immutable_authority_source(
    decision_case, mutation, message,
):
    # Independent root/timing resolver-layer matrix with the same three-party
    # proof axes; no evaluator or consumer identity validation is invoked.
    binding_id, _ = _check_binding(decision_case)
    port = decision_case["normalized_evidence_port"]
    _mutate_fixture_resolver_authority(port, port.root_timing_bindings, binding_id, mutation)
    with pytest.raises(ValueError, match=message):
        port.get_root_timing_outcome_binding(binding_id)


def test_participation_fixture_resolver_rejects_wrong_runtime_class(decision_case):
    binding_id, _ = _role_binding(decision_case)
    port = decision_case["normalized_evidence_port"]
    port.participation_bindings[binding_id] = next(iter(port.bindings.values()))
    with pytest.raises(TypeError, match="authority binding has wrong runtime class"):
        port.get_participation_role_binding(binding_id)


def test_root_timing_fixture_resolver_rejects_wrong_runtime_class(decision_case):
    binding_id, _ = _check_binding(decision_case)
    port = decision_case["normalized_evidence_port"]
    port.root_timing_bindings[binding_id] = next(iter(port.participation_bindings.values()))
    with pytest.raises(TypeError, match="authority binding has wrong runtime class"):
        port.get_root_timing_outcome_binding(binding_id)


def test_no_test_side_canonical_redeclaration_fake_authority_or_private_digest_escape():
    test_module = inspect.getmodule(test_no_test_side_canonical_redeclaration_fake_authority_or_private_digest_escape)
    assert test_module is not None
    tree = ast.parse(inspect.getsource(test_module))
    class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    function_names = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    argument_names = {
        argument.arg
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for argument in node.args.args + node.args.kwonlyargs
    }
    canonical_names = {
        "FrozenCardFieldRef", "FrozenConstraintRef", "FrozenParticipationRoleBinding",
        "FrozenRootTimingOutcomeBinding", "NormalizedEvidenceReadPort",
    }
    assert class_names.isdisjoint(canonical_names)
    assert not any(name.startswith("Fake") or name.endswith(("Port", "Adapter")) for name in class_names)
    assert not any("factory" in name or name.startswith(("make_authority", "build_authority")) for name in function_names)
    assert "monkeypatch" not in argument_names
    forbidden_private_calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "decision_module"
        and node.func.attr in {"_digest", "_record_payload", "_expanded_field_ref", "_expanded_constraint_ref"}
    }
    assert forbidden_private_calls == set()

    production_source = inspect.getsource(decision_module)
    assert "from engine.f09.evidence import validate_for_pi220" not in production_source
    assert "normalized_evidence_port.validate_for_pi220(" in production_source
    assert "from_frozen_fixture" not in production_source


def test_fixed_resource_canonical_bytes_vector(decision_case):
    _, binding = _first_binding(decision_case)
    assert canonicalize_bounded_jcs(thaw_frozen_json(binding.record_payload)) == FIXED_RESOURCE_CANONICAL_BYTES
    assert binding.canonical_record_digest.value == "9924206df648b5b2c606e6009ddca58bdb02d6ee5464b034a565ce6371a5e1bc"


def test_six_member_identity_and_per_gate_evidence(evaluated):
    records = evaluated.gate_sets[0].records
    assert len(records) == 6
    assert len({record.declared_member_id for record in records}) == 6
    evidence_ids = tuple(record.supporting_evidence_ids for record in records)
    assert len(set(evidence_ids)) == 6
    assert all(len(ids) == 1 for ids in evidence_ids)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("missing", "GATE.MEMBER_BINDING_MISMATCH"),
        ("immutable", "GATE.PERMUTATION_BINDING_INVALID"),
        ("version", "GATE.MEMBER_BINDING_MISMATCH"),
        ("canonical", "GATE.PERMUTATION_BINDING_INVALID"),
    ],
)
def test_binding_identity_and_digest_drift_fail_closed(decision_case, mutation, message):
    binding_id, binding = _first_binding(decision_case)
    port = decision_case["normalized_evidence_port"]
    if mutation == "missing":
        del port.bindings[binding_id]
    elif mutation == "immutable":
        port.bindings[binding_id] = _replace_binding(binding, immutable_source_digest=replace(DIGEST, value="2" * 64))
    elif mutation == "version":
        port.bindings[binding_id] = _replace_binding(binding, binding_version="v2")
    else:
        port.bindings[binding_id] = _replace_binding(binding, canonical_record_digest=replace(DIGEST, value="2" * 64))
    with pytest.raises((KeyError, ValueError), match=message if mutation != "missing" else None):
        _evaluate(decision_case)


# Independent old-digest mutations cover every closed field. Every instance keeps
# the original immutable RESOURCE digest and must fail before semantic validation.
STALE_OLD_DIGEST_VECTORS = (
    ("candidate_id", "CANDIDATE-STALE"),
    ("gate_definition_ref", {"card_id": "F09", "contract_id": "real-world-function-evidence-cards-v1", "contract_version": "v1", "field_path": "/stale", "declared_state": "PRESENT_VALUE", "declared_value": ["RESOURCE", "OBJECT", "ALLOCATION", "RISK", "ATTRIBUTION", "TENSE"], "source_locator_id": "SNAP-1"}),
    ("declared_member_id", "F09-MEMBER-STALE"),
    ("state", "UNKNOWN"),
    ("supporting_evidence_ids", ["REALITY-OBJECT"]),
    ("counterevidence_ids", ["REALITY-OBJECT"]),
    ("conflict_relation_ids", ["REL-CANDIDATE-SOURCE"]),
    ("missing_paths", ["/stale"]),
    ("conflict_paths", ["/stale"]),
    ("unknown_paths", ["/stale"]),
    ("reason_codes", ["GATE.STATE_UNKNOWN"]),
    ("source_decision_ref", "SOURCE-DECISION-STALE"),
)


@pytest.mark.parametrize(("field", "value"), STALE_OLD_DIGEST_VECTORS)
def test_stale_payload_fields_with_old_digest_fail_at_digest_comparison(decision_case, field, value):
    binding_id, binding = _first_binding(decision_case)
    payload = _mutable_json(binding.record_payload)
    payload[field] = value
    decision_case["normalized_evidence_port"].bindings[binding_id] = FrozenGateEvaluationBinding(
        binding.binding_id, binding.binding_version, binding.immutable_source_digest,
        binding.canonical_record_digest, payload, binding.source_locator_id,
    )
    with pytest.raises(ValueError, match="GATE.PERMUTATION_BINDING_INVALID"):
        _evaluate(decision_case)


# Contract-fixed re-sign vectors for all 12 closed payload fields. These digests
# were captured as immutable contract vectors; the tests do not compute an oracle.
STALE_RESIGN_VECTORS = (
    ("candidate_id", "CANDIDATE-STALE", "318b7e6171d92eacdeaa96dbc645f1c99276c01ed3dc2716bb843e08e43ce02b"),
    ("gate_definition_ref", {"card_id": "F09", "contract_id": "real-world-function-evidence-cards-v1", "contract_version": "v1", "field_path": "/stale", "declared_state": "PRESENT_VALUE", "declared_value": ["RESOURCE", "OBJECT", "ALLOCATION", "RISK", "ATTRIBUTION", "TENSE"], "source_locator_id": "SNAP-1"}, "6a3e8c258cfcc9d8529adf06d56d256557668ace51bbc0b7a74b292010a5f597"),
    ("declared_member_id", "F09-MEMBER-STALE", "98d8b9ac4a004a3119b58d96eefb1bab7d8b80f0f2b890fb69c713979911906d"),
    ("state", "UNKNOWN", "1b31fa3fbf6c4e23ee09062839a6ceb9bcd250ae74160e3c93a63f6987f059d9"),
    ("supporting_evidence_ids", ["REALITY-OBJECT"], "d63e250ff59c79c25b10ca927d62bd1b8586974f1aa990553fac86d043979938"),
    ("counterevidence_ids", ["REALITY-OBJECT"], "0729de7a274fcd4235b6b85dad011dea1d6da239a0c0d92eb2ead98b770fe313"),
    ("conflict_relation_ids", ["REL-CANDIDATE-SOURCE"], "d07910cb055415adac126cb0c8489ea1f08ae308a26486249d096a8127ec88cb"),
    ("missing_paths", ["/stale"], "0f411354b05828bbc80f64ceed7c59256752a703520ea6fb8072d57d87e80e35"),
    ("conflict_paths", ["/stale"], "17eb07507a23ba0f2e373dfc368f8cd69ad4bf1a94c9b0ca54dcfee75c7ee7e7"),
    ("unknown_paths", ["/stale"], "2b3d0c880ed4d1fa5c7f34d4e7046a580aa174cce9e07f0444d37772582c0d27"),
    ("reason_codes", ["GATE.STATE_UNKNOWN"], "fbffb346f25442ea490ff7e0577ff30a478542c3791d9b1cae4d29d3ce999c58"),
    ("source_decision_ref", "SOURCE-DECISION-STALE", "0ede2f75b71a4c3e9af13d3235fb9d1d4c2f366a4b33cc1cc4e4283d45f323e0"),
)


@pytest.mark.parametrize(("field", "value", "resigned_digest"), STALE_RESIGN_VECTORS)
def test_resigned_semantically_stale_payload_fields_fail_closed(decision_case, field, value, resigned_digest):
    binding_id, binding = _first_binding(decision_case)
    payload = _mutable_json(binding.record_payload)
    payload[field] = value
    assert _independent_digest(payload).value == resigned_digest
    decision_case["normalized_evidence_port"].bindings[binding_id] = FrozenGateEvaluationBinding(
        binding.binding_id, binding.binding_version, binding.immutable_source_digest,
        DigestRef("sha256", "RFC8785-JCS-UTF8", resigned_digest), payload, binding.source_locator_id,
    )
    with pytest.raises(ValueError, match="GATE.PERMUTATION_BINDING_INVALID"):
        _evaluate(decision_case)


def test_package_argument_must_equal_authoritative_package(decision_case):
    decision_case["package"] = replace(decision_case["package"], case_id="CASE-STALE")
    with pytest.raises(ValueError, match="INTEGRITY.PACKAGE_NOT_CONSUMABLE"):
        _evaluate(decision_case)


@pytest.mark.parametrize("bad_value", [(), {"not": "a string array"}, 1, 1.0])
def test_binding_freezer_rejects_non_closed_json_graph(decision_case, bad_value):
    _, binding = _first_binding(decision_case)
    payload = _mutable_json(binding.record_payload)
    payload["supporting_evidence_ids"] = bad_value
    with pytest.raises((TypeError, ValueError)):
        FrozenGateEvaluationBinding(
            binding.binding_id, binding.binding_version, binding.immutable_source_digest,
            binding.canonical_record_digest, payload, binding.source_locator_id,
        )


def test_binding_freezer_rejects_cycle(decision_case):
    _, binding = _first_binding(decision_case)
    payload = _mutable_json(binding.record_payload)
    payload["supporting_evidence_ids"] = payload
    with pytest.raises(ValueError, match="cycle"):
        FrozenGateEvaluationBinding(
            binding.binding_id, binding.binding_version, binding.immutable_source_digest,
            binding.canonical_record_digest, payload, binding.source_locator_id,
        )


def test_empty_relation_authority_is_not_validated(decision_case):
    decision_case["normalized_evidence_port"].relations = ()
    with pytest.raises(ValueError, match="INTEGRITY.REFERENCE_BROKEN"):
        _evaluate(decision_case)


def test_contract_port_mismatch_fails_closed(decision_case):
    decision_case["frozen_contract_port"].contract_result = ContractIntegrityResult(
        "INVALID", ("INTEGRITY.CONTRACT_VERSION_MISMATCH",)
    )
    with pytest.raises(ValueError, match="INTEGRITY.CONTRACT_VERSION_MISMATCH"):
        _evaluate(decision_case)


def test_field_and_constraint_authority_come_from_contract_port(decision_case, evaluated):
    assert evaluated.gate_sets[0].gate_definition_refs == (
        decision_case["frozen_contract_port"].field_observation.ref,
    )
    check = evaluated.root_timing_checks[0].checks[0]
    assert isinstance(check.constraint_ref, FrozenConstraintRef)
    assert check.constraint_ref == decision_case["frozen_contract_port"].constraint_ref


def test_result_local_basis_rejects_external_source_decision_string(evaluated):
    external = evaluated.gate_sets[0].records[0].source_decision_ref
    bad = replace(evaluated.action_envelope, basis_record_ids=(external,))
    with pytest.raises(ValueError, match="ACTION.BASIS_MISSING"):
        validate_decision_result(replace(evaluated, action_envelope=bad))


@pytest.mark.parametrize(
    ("action", "payload_type"),
    [
        ("OUTPUT", "OutputPayload"),
        ("CONDITIONAL", "ConditionalPayload"),
        ("ASK", "AskPayload"),
        ("ABSTAIN", "AbstainPayload"),
        ("HUMAN_REVIEW", "HumanReviewPayload"),
    ],
)
def test_five_actions_are_selected_from_input(decision_case, action, payload_type):
    decision = decision_case["competition_input"].decision
    issue_ids = decision.payload_issue_ids
    paths = decision.question_paths
    if action == "OUTPUT":
        issue_ids, paths = (), ()
    elif action == "HUMAN_REVIEW":
        issue_ids, paths = ("ISSUE-CONFLICT",), ("/decision/conflict",)
    updated = replace(decision, selected_action=action, payload_type=payload_type, payload_issue_ids=issue_ids, question_paths=paths)
    decision_case["competition_input"] = replace(decision_case["competition_input"], decision=updated)
    result = _evaluate(decision_case)
    assert result.action_envelope.selected_action.value == action
    assert type(result.action_envelope.payload).__name__ == payload_type


def test_payload_mismatch_basis_empty_and_ask_conflict_fail(evaluated):
    mismatch = replace(evaluated.action_envelope, selected_action=DecisionAction.OUTPUT)
    with pytest.raises(ValueError, match="ACTION.PAYLOAD_TYPE_MISMATCH"):
        validate_decision_result(replace(evaluated, action_envelope=mismatch))
    with pytest.raises(ValueError, match="ACTION.BASIS_MISSING"):
        validate_decision_result(replace(evaluated, action_envelope=replace(evaluated.action_envelope, basis_record_ids=())))
    conflict = replace(
        evaluated.issues[0], issue_class="CONFLICT",
        evaluator_state=decision_module.FieldEvaluatorState.CONFLICT,
        evidence_ids=("REALITY-RESOURCE", "REALITY-OBJECT"),
    )
    with pytest.raises(ValueError, match="ACTION.QUESTION_NOT_BOUND_TO_ISSUE"):
        validate_decision_result(replace(evaluated, issues=(conflict,)))


def test_root_and_timing_port_constraint_fail_closed(decision_case, evaluated):
    root = evaluated.root_ledgers[0]
    forged = replace(root.root_entries[0], source_track="REALITY_FACT")
    with pytest.raises(ValueError, match="ROOT.SOURCE_TRACK_INVALID"):
        validate_decision_result(replace(evaluated, root_ledgers=(replace(root, root_entries=(forged,)),)))

    decision_case["frozen_contract_port"].constraint_ref = replace(
        decision_case["frozen_contract_port"].constraint_ref, constraint_path="/wrong"
    )
    with pytest.raises((KeyError, ValueError)):
        _evaluate(decision_case)


def test_validator_does_not_trust_cached_ready_state(evaluated):
    gate_set = evaluated.gate_sets[0]
    stale = replace(gate_set, records=gate_set.records[:-1], set_state="READY")
    with pytest.raises(ValueError, match="GATE.MEMBER_CARDINALITY_INVALID"):
        validate_decision_result(replace(evaluated, gate_sets=(stale,)))


def _role_binding(case, role=PARTICIPATION_ROLES[0]):
    binding_id = dict(case["gate_inputs"][0].participation.role_authority_binding_ids)[role]
    return binding_id, case["normalized_evidence_port"].participation_bindings[binding_id]


def _check_binding(case):
    binding_id = case["root_input"].root_timing.authority_binding_ids[0][1]
    return binding_id, case["normalized_evidence_port"].root_timing_bindings[binding_id]


PARTICIPATION_WRONG_TYPE_VECTORS = (
    ("participation_record_id", 1),
    ("participation_set_id", 1),
    ("role", 1),
    ("frozen_definition_refs", "not-a-tuple"),
    ("state", 1),
    ("supporting_evidence_ids", "not-a-tuple"),
    ("counterevidence_ids", "not-a-tuple"),
    ("missing_issue_ids", "not-a-tuple"),
    ("conflict_issue_ids", "not-a-tuple"),
    ("unknown_issue_ids", "not-a-tuple"),
    ("relation_ids", "not-a-tuple"),
    ("source_decision_ref", 1),
)

ROOT_TIMING_WRONG_TYPE_VECTORS = (
    ("check_id", 1),
    ("constraint_ref", "not-a-frozen-constraint-ref-payload"),
    ("root_entry_ids", "not-a-tuple"),
    ("timing_entry_ids", "not-a-tuple"),
    ("state", 1),
    ("source_decision_ref", 1),
    ("missing_paths", "not-a-tuple"),
    ("conflict_paths", "not-a-tuple"),
    ("unknown_paths", "not-a-tuple"),
    ("reason_codes", "not-a-tuple"),
)


@pytest.mark.parametrize(("field", "wrong_value"), PARTICIPATION_WRONG_TYPE_VECTORS)
def test_participation_closed_payload_rejects_each_wrong_field_type_at_constructor_boundary(
    decision_case, field, wrong_value,
):
    _, binding = _role_binding(decision_case)
    payload = _mutable_json(binding.record_payload)
    payload[field] = wrong_value
    with pytest.raises((TypeError, ValueError)):
        FrozenParticipationRoleBinding(
            binding.binding_id, binding.binding_version, binding.immutable_source_digest,
            binding.canonical_record_digest, payload, binding.source_locator_id,
        )


@pytest.mark.parametrize(("field", "wrong_value"), ROOT_TIMING_WRONG_TYPE_VECTORS)
def test_root_timing_closed_payload_rejects_each_wrong_field_type_at_constructor_boundary(
    decision_case, field, wrong_value,
):
    _, binding = _check_binding(decision_case)
    payload = _mutable_json(binding.record_payload)
    payload[field] = wrong_value
    with pytest.raises((TypeError, ValueError)):
        FrozenRootTimingOutcomeBinding(
            binding.binding_id, binding.binding_version, binding.immutable_source_digest,
            binding.canonical_record_digest, payload, binding.source_locator_id,
        )


@pytest.mark.parametrize("binding_kind", ["participation", "root_timing"])
@pytest.mark.parametrize("schema_mutation", ["missing_key", "extra_key"])
def test_new_binding_closed_payload_rejects_missing_and_extra_keys(decision_case, binding_kind, schema_mutation):
    _, binding = _role_binding(decision_case) if binding_kind == "participation" else _check_binding(decision_case)
    payload = _mutable_json(binding.record_payload)
    if schema_mutation == "missing_key":
        payload.pop(next(iter(payload)))
    else:
        payload["extra"] = "forbidden"
    with pytest.raises(ValueError, match="closed"):
        type(binding)(
            binding.binding_id, binding.binding_version, binding.immutable_source_digest,
            binding.canonical_record_digest, payload, binding.source_locator_id,
        )


@pytest.mark.parametrize("binding_kind", ["participation", "root_timing"])
@pytest.mark.parametrize("mutation", ["value", "tuple_order"])
def test_new_binding_stale_digest_fails_closed(decision_case, binding_kind, mutation):
    binding_id, binding = _role_binding(decision_case) if binding_kind == "participation" else _check_binding(decision_case)
    payload = _mutable_json(binding.record_payload)
    tuple_field = "supporting_evidence_ids" if binding_kind == "participation" else "root_entry_ids"
    if mutation == "value":
        stale_digest = binding.canonical_record_digest
        payload[tuple_field] = payload[tuple_field] + ["STALE"]
    else:
        baseline = dict(payload)
        baseline[tuple_field] = payload[tuple_field] + ["SECOND"]
        stale_digest = _independent_digest(baseline)
        payload[tuple_field] = list(reversed(baseline[tuple_field]))
    replacement = type(binding)(
        binding.binding_id, binding.binding_version, binding.immutable_source_digest,
        stale_digest, payload, binding.source_locator_id,
    )
    store = (
        decision_case["normalized_evidence_port"].participation_bindings
        if binding_kind == "participation"
        else decision_case["normalized_evidence_port"].root_timing_bindings
    )
    store[binding_id] = replacement
    with pytest.raises(ValueError):
        _evaluate(decision_case)


@pytest.mark.parametrize("mutation", ["missing", "wrong_class", "shared", "role_swap", "shared_evidence", "version", "locator", "source_digest"])
def test_participation_authority_identity_and_isolation_fail_closed(decision_case, mutation):
    participation = decision_case["gate_inputs"][0].participation
    pairs = list(participation.role_authority_binding_ids)
    port = decision_case["normalized_evidence_port"]
    first_id, first = _role_binding(decision_case, PARTICIPATION_ROLES[0])
    second_id, second = _role_binding(decision_case, PARTICIPATION_ROLES[1])
    if mutation == "missing":
        del port.participation_bindings[first_id]
    elif mutation == "wrong_class":
        port.participation_bindings[first_id] = next(iter(port.bindings.values()))
    elif mutation == "shared":
        pairs[1] = (pairs[1][0], first_id)
        replacement_input = replace(participation, role_authority_binding_ids=tuple(pairs))
        decision_case["gate_inputs"] = (replace(decision_case["gate_inputs"][0], participation=replacement_input),)
    elif mutation == "role_swap":
        port.participation_bindings[first_id] = _replace_binding(first, record_payload=second.record_payload, canonical_record_digest=second.canonical_record_digest)
    elif mutation == "shared_evidence":
        payload = _mutable_json(second.record_payload)
        payload["supporting_evidence_ids"] = list(first.record_payload["supporting_evidence_ids"])
        port.participation_bindings[second_id] = FrozenParticipationRoleBinding(
            second.binding_id, second.binding_version, second.immutable_source_digest,
            _independent_digest(payload), payload, second.source_locator_id,
        )
    elif mutation == "version":
        _synchronize_fixture_authority_version(port, first.source_locator_id, "v2")
    elif mutation == "locator":
        port.participation_bindings[first_id] = _replace_binding(first, source_locator_id="OTHER")
        _replace_fixture_authority_source(port, first_id, locator_id="OTHER")
        _copy_fixture_declared_authority(port, first.source_locator_id, "OTHER")
    else:
        gate_input = decision_case["gate_inputs"][0]
        source = replace(gate_input.source, payload_digest="2" * 64)
        decision_case["gate_inputs"] = (replace(gate_input, source=source),)
    with pytest.raises(ValueError):
        _evaluate(decision_case)


@pytest.mark.parametrize("mutation", ["missing", "wrong_class", "candidate_swap", "constraint_swap", "root_swap", "timing_swap", "version", "locator", "source_digest"])
def test_root_timing_authority_identity_swaps_fail_closed(decision_case, mutation):
    binding_id, binding = _check_binding(decision_case)
    port = decision_case["normalized_evidence_port"]
    if mutation == "missing":
        del port.root_timing_bindings[binding_id]
    elif mutation == "wrong_class":
        port.root_timing_bindings[binding_id] = next(iter(port.participation_bindings.values()))
    elif mutation == "candidate_swap":
        root_timing = replace(decision_case["root_input"].root_timing, authority_binding_ids=(("OTHER", binding_id),))
        decision_case["root_input"] = replace(decision_case["root_input"], root_timing=root_timing)
        decision_case["timing_input"] = replace(decision_case["timing_input"], root_timing=root_timing)
    elif mutation in ("constraint_swap", "root_swap", "timing_swap"):
        payload = _mutable_json(binding.record_payload)
        field = {"constraint_swap": "constraint_ref", "root_swap": "root_entry_ids", "timing_swap": "timing_entry_ids"}[mutation]
        payload[field] = {"card_id": "F09", "contract_id": "wrong", "contract_version": "v1", "constraint_path": "/root_timing", "source_locator_id": "SNAP-1"} if field == "constraint_ref" else ["SWAPPED"]
        port.root_timing_bindings[binding_id] = FrozenRootTimingOutcomeBinding(
            binding.binding_id, binding.binding_version, binding.immutable_source_digest,
            _independent_digest(payload), payload, binding.source_locator_id,
        )
    elif mutation == "version":
        _synchronize_fixture_authority_version(port, binding.source_locator_id, "v2")
    elif mutation == "locator":
        port.root_timing_bindings[binding_id] = _replace_binding(binding, source_locator_id="OTHER")
        _replace_fixture_authority_source(port, binding_id, locator_id="OTHER")
        _copy_fixture_declared_authority(port, binding.source_locator_id, "OTHER")
    else:
        root_source = replace(decision_case["root_input"].source, payload_digest="2" * 64)
        timing_source = replace(decision_case["timing_input"].source, payload_digest="2" * 64)
        decision_case["root_input"] = replace(decision_case["root_input"], source=root_source)
        decision_case["timing_input"] = replace(decision_case["timing_input"], source=timing_source)
    with pytest.raises(ValueError):
        _evaluate(decision_case)


@pytest.mark.parametrize("input_kind", ["participation", "root_timing"])
def test_evaluator_input_rejects_empty_authority_binding_id_before_target_resolver(decision_case, input_kind):
    port = decision_case["normalized_evidence_port"]
    if input_kind == "participation":
        gate_input = decision_case["gate_inputs"][0]
        pairs = list(gate_input.participation.role_authority_binding_ids)
        pairs[0] = (pairs[0][0], "")
        participation = replace(gate_input.participation, role_authority_binding_ids=tuple(pairs))
        decision_case["gate_inputs"] = (replace(gate_input, participation=participation),)
    else:
        root_timing = decision_case["root_input"].root_timing
        pairs = list(root_timing.authority_binding_ids)
        pairs[0] = (pairs[0][0], "")
        changed = replace(root_timing, authority_binding_ids=tuple(pairs))
        decision_case["root_input"] = replace(decision_case["root_input"], root_timing=changed)
        decision_case["timing_input"] = replace(decision_case["timing_input"], root_timing=changed)
    with pytest.raises(ValueError):
        _evaluate(decision_case)
    assert not any(kind == input_kind for kind, _ in port.authority_calls)


PARTICIPATION_NON_SATISFIED_VECTORS = (
    ("MISSING", (), (), ("ISSUE-MISSING",), (), (), ()),
    ("CONFLICT", ("REALITY-RESOURCE",), ("REALITY-RESOURCE",), (), ("ISSUE-CONFLICT",), (), ("REL-CANDIDATE-SOURCE",)),
    ("UNKNOWN", (), (), (), (), ("ISSUE-UNKNOWN",), ()),
    ("NOT_APPLICABLE", (), (), (), (), (), ()),
)


@pytest.mark.parametrize(
    ("state", "supporting", "counter", "missing", "conflict", "unknown", "relations"),
    PARTICIPATION_NON_SATISFIED_VECTORS,
)
def test_evaluator_preserves_each_legal_non_satisfied_participation_authority_surface(
    decision_case, state, supporting, counter, missing, conflict, unknown, relations,
):
    binding_id, binding = _role_binding(decision_case)
    payload = _mutable_json(binding.record_payload)
    payload.update(
        state=state,
        supporting_evidence_ids=list(supporting),
        counterevidence_ids=list(counter),
        missing_issue_ids=list(missing),
        conflict_issue_ids=list(conflict),
        unknown_issue_ids=list(unknown),
        relation_ids=list(relations),
    )
    source_decision_ref = f"SOURCE-DECISION-PART-{state}"
    payload["source_decision_ref"] = source_decision_ref
    decision_case["normalized_evidence_port"].participation_bindings[binding_id] = FrozenParticipationRoleBinding(
        binding.binding_id, binding.binding_version, binding.immutable_source_digest,
        _independent_digest(payload), payload, binding.source_locator_id,
    )

    record = _evaluate(decision_case).participation_sets[0].role_records[0]
    assert record.authority_binding_id == binding_id
    assert record.state == state
    assert record.supporting_evidence_ids == supporting
    assert record.counterevidence_ids == counter
    assert record.missing_issue_ids == missing
    assert record.conflict_issue_ids == conflict
    assert record.unknown_issue_ids == unknown
    assert record.relation_ids == relations
    assert record.source_decision_ref == source_decision_ref


def test_evaluator_preserves_non_satisfied_root_timing_authority(decision_case):
    binding_id, binding = _check_binding(decision_case)
    payload = _mutable_json(binding.record_payload)
    payload.update(
        state="VIOLATED",
        conflict_paths=["/root_timing/conflict"],
        reason_codes=["TIMING.CONSTRAINT_UNKNOWN"],
    )
    decision_case["normalized_evidence_port"].root_timing_bindings[binding_id] = FrozenRootTimingOutcomeBinding(
        binding.binding_id, binding.binding_version, binding.immutable_source_digest,
        _independent_digest(payload), payload, binding.source_locator_id,
    )
    check = _evaluate(decision_case).root_timing_checks[0].checks[0]
    assert check.state == "VIOLATED"
    assert check.conflict_paths == ("/root_timing/conflict",)
    assert check.reason_codes == ("TIMING.CONSTRAINT_UNKNOWN",)
    assert check.source_decision_ref == payload["source_decision_ref"]


@pytest.mark.parametrize(
    ("state", "path_field", "reason_codes"),
    [("VIOLATED", "conflict_paths", []), ("UNKNOWN", "unknown_paths", [])],
)
def test_root_timing_non_satisfied_surfaces_require_path_and_reason(decision_case, state, path_field, reason_codes):
    _, binding = _check_binding(decision_case)
    payload = _mutable_json(binding.record_payload)
    payload["state"] = state
    payload[path_field] = []
    payload["reason_codes"] = reason_codes
    with pytest.raises(ValueError, match="state surface"):
        FrozenRootTimingOutcomeBinding(
            binding.binding_id, binding.binding_version, binding.immutable_source_digest,
            binding.canonical_record_digest, payload, binding.source_locator_id,
        )


@pytest.mark.parametrize("pi210_state", ["INVALID", "BLOCKED"])
def test_pi210_non_ready_fails_before_authority_consumption(decision_case, pi210_state):
    port = decision_case["normalized_evidence_port"]
    port.package = replace(port.package, integrity_state=pi210_state)
    decision_case["package"] = port.package
    with pytest.raises(ValueError, match="INTEGRITY.PACKAGE_NOT_CONSUMABLE"):
        _evaluate(decision_case)
    assert port.authority_calls == []


def test_gate_conflict_relation_consumer_explicitly_rejects_empty_source_refs_static_oracle():
    # Canonical EvidenceRelation rejects an empty tuple at construction, so this is
    # deliberately a static consumer-predicate oracle, not a dynamic reachability claim.
    tree = ast.parse(inspect.getsource(decision_module._gate_conflict_relation_valid))
    returns = [node for node in ast.walk(tree) if isinstance(node, ast.Return)]
    assert len(returns) == 1
    predicate = returns[0].value
    assert isinstance(predicate, ast.BoolOp)
    assert isinstance(predicate.op, ast.And)
    source_ref_terms = [
        term
        for term in predicate.values
        if isinstance(term, ast.Call)
        and isinstance(term.func, ast.Name)
        and term.func.id == "bool"
        and len(term.args) == 1
        and not term.keywords
        and isinstance(term.args[0], ast.Attribute)
        and isinstance(term.args[0].value, ast.Name)
        and term.args[0].value.id == "relation"
        and term.args[0].attr == "source_refs"
    ]
    assert len(source_ref_terms) == 1


@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("relation_type", "CONTRADICTS"), ("status", "PROPOSED"),
        ("scope", RelationScope("F08", None)), ("direction", "reverse"),
        ("endpoint", ObjectRef("SOURCE_OBJECT", "STATE-X", False, "SNAP-1")),
        ("self_loop", True),
    ],
)
def test_gate_conflict_relation_dynamic_consumer_axes_fail_closed(decision_case, axis, value):
    binding_id, binding = _first_binding(decision_case)
    payload = _mutable_json(binding.record_payload)
    payload["state"] = "CONFLICT"
    payload["counterevidence_ids"] = ["REALITY-OBJECT"]
    payload["conflict_relation_ids"] = ["REL-CANDIDATE-SOURCE"]
    payload["conflict_paths"] = ["/conflict"]
    payload["reason_codes"] = ["GATE.EVIDENCE_CONFLICT"]
    authorized_binding = FrozenGateEvaluationBinding(
        binding.binding_id, binding.binding_version, binding.immutable_source_digest,
        _independent_digest(payload), payload, binding.source_locator_id,
    )
    port = decision_case["normalized_evidence_port"]
    port.bindings[binding_id] = authorized_binding
    _authorize_gate_binding(port, authorized_binding)
    gate_input = decision_case["gate_inputs"][0]
    decision_case["gate_inputs"] = (
        replace(gate_input, gate=replace(gate_input.gate, reality_state="CONFLICT")),
    )
    relation = decision_case["normalized_evidence_port"].relations[0]
    valid_from = ObjectRef("EVIDENCE", "REALITY-ATTRIBUTION", False, "SNAP-1")
    valid_to = ObjectRef("EVIDENCE", "REALITY-RESOURCE", False, "SNAP-1")
    relation = _replace_relation(relation, relation_type="COUNTERS", status="ASSERTED", scope=RelationScope("F09", None), from_ref=valid_from, to_ref=valid_to, source_refs=("SNAP-1",))
    if axis == "direction":
        # Only direction changes: both endpoints remain existing EVIDENCE objects,
        # distinct, F09-scoped and sourced; the current member endpoint moves off to_ref.
        relation = _replace_relation(relation, from_ref=valid_to, to_ref=valid_from)
    elif axis == "endpoint":
        relation = _replace_relation(relation, from_ref=value)
    elif axis == "self_loop":
        relation = _replace_relation(relation, from_ref=valid_to)
    else:
        relation = _replace_relation(relation, **{axis: value})
    decision_case["normalized_evidence_port"].relations = (relation,)
    with pytest.raises(ValueError):
        _evaluate(decision_case)


@pytest.mark.parametrize("surface", ["gate", "participation", "check"])
def test_output_rejects_ready_container_with_non_satisfied_current_content(decision_case, surface):
    decision = decision_case["competition_input"].decision
    decision_case["competition_input"] = replace(
        decision_case["competition_input"],
        decision=replace(decision, selected_action="OUTPUT", payload_type="OutputPayload", payload_issue_ids=(), question_paths=()),
    )
    result = _evaluate(decision_case)
    envelope = result.action_envelope
    if surface == "gate":
        item = result.gate_sets[0]
        record = replace(item.records[0], state=decision_module.GateEvidenceState.UNKNOWN, supporting_evidence_ids=(), unknown_paths=("/unknown",))
        record = replace(
            record,
            evaluation_binding_ref=replace(
                record.evaluation_binding_ref,
                canonical_record_digest=_independent_gate_record_digest(record),
            ),
        )
        changed = replace(result, gate_sets=(replace(item, records=(record,) + item.records[1:], set_state="READY"),))
    elif surface == "participation":
        item = result.participation_sets[0]
        records = (replace(item.role_records[0], state="NOT_APPLICABLE", supporting_evidence_ids=()),) + item.role_records[1:]
        changed = replace(result, participation_sets=(replace(item, role_records=records, structural_state="READY"),))
    else:
        item = result.root_timing_checks[0]
        changed = replace(result, root_timing_checks=(replace(item, checks=(replace(item.checks[0], state="NOT_APPLICABLE", reason_codes=("TIMING.CONSTRAINT_UNKNOWN",)),), structural_state="READY"),))
    with pytest.raises(ValueError, match="ACTION.BLOCKING_ISSUE_PRESENT"):
        validate_decision_result(replace(changed, action_envelope=envelope))
