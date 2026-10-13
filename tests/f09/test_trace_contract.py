import hashlib
from dataclasses import fields, replace
from pathlib import Path

import pytest

import engine.f09.contracts as contracts
import engine.f09.trace as trace_module
from engine.f09.contracts import (
    DecisionAction,
    DigestRef,
    FieldMapping,
    ObjectRef,
    RunTrack,
    TransformationRecord,
)
from engine.f09.decision import evaluate_f09
from engine.f09.errors import F09ContractError, F09IntegrityError, F09SourceError
from engine.f09.evidence import build_f09_evidence_package
from engine.f09.trace import (
    DecisionTraceRef,
    DigestMissing,
    DigestPresent,
    ProjectionValidationResult,
    SnapshotRef,
    StandardStatement,
    StatementSet,
    TraceEdge,
    TraceEnvelope,
    TraceNode,
    VersionedObjectRef,
    build_statement_set as _build_statement_set,
    build_trace as _build_trace,
    validate_statement_projection as _validate_statement_projection,
)


PI300_DIGEST = DigestRef(
    "sha256",
    "RFC8785-JCS-UTF8",
    "67517fe2d04fb0fe580e031643dab2ad53fcdb8c90707ba4d496c316dd87f5e7",
)


def _evaluated(decision_case):
    return evaluate_f09(**decision_case, request_id="REQUEST-TRACE-1")


def _file_digest(path: Path) -> DigestRef:
    return DigestRef(
        "sha256",
        "RAW-BYTES",
        hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def _card_source_refs():
    contract_path = Path("engine/contracts/12-real-world-function-evidence-cards-v1.md")
    appendix_path = Path("mapping/real-world-function-evidence-cards-v1.yaml")
    return (
        VersionedObjectRef(
            object_type="CONTRACT",
            object_id="F09-NORMATIVE-CONTRACT",
            revision_id="rev-frozen",
            schema_version="markdown-contract.v1",
            contract_version="real-world-function-evidence-cards-v1",
            digest_binding=DigestPresent("PRESENT", _file_digest(contract_path)),
            source_locator_id=contract_path.as_posix(),
            captured_at="2026-07-19T00:00:00Z",
        ),
        VersionedObjectRef(
            object_type="MACHINE_APPENDIX",
            object_id="F09-MACHINE-APPENDIX",
            revision_id="rev-frozen",
            schema_version="machine-appendix.v1",
            contract_version="real-world-function-evidence-cards-v1",
            digest_binding=DigestPresent("PRESENT", _file_digest(appendix_path)),
            source_locator_id=appendix_path.as_posix(),
            captured_at="2026-07-19T00:00:00Z",
        ),
    )


def build_trace(package, result, *, created_at):
    normative_contract_ref, machine_appendix_ref = _card_source_refs()
    return _build_trace(
        package,
        result,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
        created_at=created_at,
    )


def build_statement_set(trace, result, *, generated_at):
    normative_contract_ref, machine_appendix_ref = _card_source_refs()
    return _build_statement_set(
        trace,
        result,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
        generated_at=generated_at,
    )


def validate_statement_projection(statement_set, trace, result):
    normative_contract_ref, machine_appendix_ref = _card_source_refs()
    package = _canonical_package(trace.case_id) if isinstance(trace, TraceEnvelope) else None
    return _validate_statement_projection(
        statement_set,
        trace,
        result,
        package,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
    )


def _ref(object_type, object_id, source_locator_id=None):
    return VersionedObjectRef(
        object_type=object_type,
        object_id=object_id,
        revision_id="rev-1",
        schema_version="f09.test.v1",
        contract_version="pi-230-v1",
        digest_binding=DigestPresent("PRESENT", PI300_DIGEST),
        source_locator_id=source_locator_id,
        captured_at="2026-07-19T00:00:00Z",
    )


_SOURCE_LOCATORS = {
    "SOURCE-STATE-1": ("SRCLOC-STATE-LEVEL", "SRCLOC-STATE-POSITION", "SRCLOC-STATE-AS-OF"),
    "SOURCE-EVENT-1": ("SRCLOC-EVENT-LEVEL", "SRCLOC-EVENT-CHANGE", "SRCLOC-EVENT-START", "SRCLOC-EVENT-END", "SRCLOC-EVENT-START-INCLUSIVE", "SRCLOC-EVENT-END-INCLUSIVE"),
    "SOURCE-OUTCOME-1": ("SRCLOC-OUTCOME-AXIS", "SRCLOC-OUTCOME-ACTION", "SRCLOC-OUTCOME-OBJECT", "SRCLOC-OUTCOME-TENSE"),
}


def _transformation(transformation_id, source_id, mappings):
    return TransformationRecord(
        transformation_id=transformation_id,
        adapter_id="f09-test-adapter",
        adapter_version="v1",
        source_object_refs=(ObjectRef("SOURCE_OBJECT", source_id, False, _SOURCE_LOCATORS[source_id][0]),),
        target_object_refs=tuple(ObjectRef("EVIDENCE", locator_id, False, locator_id) for locator_id in _SOURCE_LOCATORS[source_id]),
        fidelity="LOSSLESS",
        field_mappings=tuple(FieldMapping(source, target, "COPY", "LOSSLESS") for source, target in mappings),
        dropped_fields=(),
        dropped_object_refs=(),
        synthesized_fields=(),
        issues=(),
        transformed_at="2026-07-19T00:00:00Z",
    )


def _valid_projection(decision_case):
    package = _canonical_package(decision_case["package"].case_id)
    result = replace(_evaluated(decision_case), package_id=package.package_id)
    trace = build_trace(package, result, created_at="2026-07-19T00:00:00Z")
    statement_set = build_statement_set(
        trace,
        result,
        generated_at="2026-07-19T00:00:00Z",
    )
    return trace, statement_set, result


def _projection_with_statement_text(decision_case, action, statement_text):
    package = _canonical_package(decision_case["package"].case_id)
    result = replace(
        _evaluated(decision_case),
        package_id=package.package_id,
        action_envelope=replace(
            _evaluated(decision_case).action_envelope,
            selected_action=action,
        ),
    )
    trace = build_trace(package, result, created_at="2026-07-19T00:00:00Z")
    statement_set = build_statement_set(
        trace,
        result,
        generated_at="2026-07-19T00:00:00Z",
    )
    statement = trace_module._sign_statement(
        replace(statement_set.statements[0], statement_text=statement_text)
    )
    statement_set_id, _ = trace_module._statement_set_identity(
        statement_set.case_id,
        statement_set.decision_trace_ref.result_ref,
        (statement.statement_revision_id,),
    )
    statement = trace_module._sign_statement(
        replace(statement, statement_set_id=statement_set_id)
    )
    statement_set = replace(
        statement_set,
        statement_set_id=statement_set_id,
        statements=(statement,),
    )
    statement_set = replace(
        statement_set,
        content_digest=trace_module._statement_set_content_digest(statement_set),
    )
    statement_set_ref = trace_module._versioned_ref(
        "STATEMENT_SET",
        statement_set.statement_set_id,
        captured_at=trace.created_at,
        digest=statement_set.content_digest,
        revision_id=f"rev-{statement_set.content_digest.value[:16]}",
        schema_version=statement_set.statement_schema_version,
    )
    statement_ref = trace_module._versioned_ref(
        "STATEMENT",
        statement.statement_id,
        captured_at=trace.created_at,
        digest=statement.content_digest,
        revision_id=statement.statement_revision_id,
        schema_version=statement.statement_schema_version,
    )
    old_set_ref = trace.statement_set_ref
    old_statement_ref = next(
        node.object_ref
        for node in trace.nodes
        if node.object_ref.object_type == "STATEMENT"
    )
    replacements = {
        old_set_ref: statement_set_ref,
        old_statement_ref: statement_ref,
    }
    trace = replace(
        trace,
        statement_set_ref=statement_set_ref,
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
    return trace, statement_set, result


def test_trace_module_reuses_canonical_runtime_identities():
    import engine.f09.trace as trace

    assert trace.TransformationRecord is contracts.TransformationRecord
    assert trace.ObjectRef is contracts.ObjectRef
    assert trace.FieldMapping is contracts.FieldMapping
    assert trace.DetectedIssue is contracts.DetectedIssue


def test_trace_envelope_retains_future_phase_fields_without_local_fallbacks():
    names = tuple(field.name for field in fields(TraceEnvelope))
    assert "artifacts" in names
    assert "feedback_bindings" in names
    import engine.f09.trace as trace

    assert not hasattr(trace, "ArtifactRecord")
    assert not hasattr(trace, "FeedbackBinding")


def _canonical_package(case_id):
    return build_f09_evidence_package(
        case_id=case_id,
        track=RunTrack.MANUAL_IMPORT,
        markdown_path=Path("engine/contracts/12-real-world-function-evidence-cards-v1.md"),
        snapshot_path=Path("plans/production-implementation-pi-300-f09-source-snapshots-v1.json"),
        chart_records=(),
        hypothesis_records=(),
    )


def test_statement_identity_ignores_result_request_and_produced_at(decision_case):
    package = _canonical_package(decision_case["package"].case_id)
    first_result = replace(_evaluated(decision_case), package_id=package.package_id)
    second_result = replace(
        evaluate_f09(
            **{
                **decision_case,
                "produced_at": "2026-07-22T00:00:00Z",
            },
            request_id="REQUEST-TRACE-2",
        ),
        package_id=package.package_id,
    )
    first_trace = build_trace(
        package,
        first_result,
        created_at="2026-07-19T00:00:00Z",
    )
    second_trace = build_trace(
        package,
        second_result,
        created_at="2026-07-19T00:00:00Z",
    )
    first_set = build_statement_set(
        first_trace,
        first_result,
        generated_at="2026-07-19T00:00:00Z",
    )
    second_set = build_statement_set(
        second_trace,
        second_result,
        generated_at="2026-07-19T00:00:00Z",
    )

    assert first_result.result_id != second_result.result_id
    assert (
        first_set.statements[0].statement_id
        == second_set.statements[0].statement_id
    )


def test_validator_rejects_statement_id_not_derived_from_basis(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    invalid_statement = replace(
        statement_set.statements[0],
        statement_id="STATEMENT-COORDINATED-FAKE",
    )

    assert validate_statement_projection(
        replace(statement_set, statements=(invalid_statement,)),
        trace,
        result,
    ) == ProjectionValidationResult(
        False,
        (contracts.DetectedIssue("TRACE.BINDING_MISMATCH", "/trace/identity"),),
    )


def test_builders_preserve_identity_and_produce_validator_accepted_graph(decision_case):
    evaluated = _evaluated(decision_case)
    package = _canonical_package(decision_case["package"].case_id)
    result = replace(evaluated, package_id=package.package_id)
    trace = build_trace(package, result, created_at="2026-07-19T00:00:00Z")
    statement_set = build_statement_set(trace, result, generated_at="2026-07-19T00:00:00Z")

    assert trace.case_id == package.case_id
    assert trace.decision_result_ref.object_id == result.result_id
    assert statement_set.decision_trace_ref.action_id == result.action_envelope.action_id
    assert statement_set.decision_trace_ref.basis_record_ids == result.action_envelope.basis_record_ids
    assert statement_set.statements[0].basis_record_ids == result.action_envelope.basis_record_ids
    assert statement_set.decision_trace_ref.output_precision_binding == result.action_envelope.output_precision_binding
    assert statement_set.decision_trace_ref.validation_plan_binding == result.action_envelope.validation_plan_binding
    assert statement_set.statements[0].output_precision_binding == result.action_envelope.output_precision_binding
    assert statement_set.statements[0].validation_plan_binding == result.action_envelope.validation_plan_binding
    assert trace.statement_set_ref.object_id == statement_set.statement_set_id
    assert len(statement_set.statements[0].evidence_refs) == 13
    assert len(statement_set.statements[0].source_locator_ids) == 13
    assert trace.source_snapshot_refs[0].source_locator_ids == tuple(record.locator.source_id for record in package.records)
    assert {edge.edge_type for edge in trace.edges if edge.transformation_id is None} == {
        "DERIVED_FROM",
        "EVALUATED_BY",
        "RENDERED_AS",
    }
    assert len(tuple(edge for edge in trace.edges if edge.edge_type == "DERIVED_FROM")) == 13
    assert len(tuple(edge for edge in trace.edges if edge.edge_type == "EVALUATED_BY")) == 1
    assert len(tuple(edge for edge in trace.edges if edge.edge_type == "RENDERED_AS")) == 2
    assert validate_statement_projection(statement_set, trace, result) == ProjectionValidationResult(True, ())


@pytest.mark.parametrize(
    "mutation",
    [
        "source_id",
        "object_id",
        "field_path",
        "track",
        "transformation",
        "source_snapshot_id",
        "source_schema_version",
        "contract_version",
        "captured_at",
        "content_digest",
        "value",
    ],
)
def test_builder_rejects_each_canonical_source_identity_drift(decision_case, mutation):
    package = _canonical_package(decision_case["package"].case_id)
    record = package.records[0]
    if mutation == "source_id":
        drifted = replace(record, locator=replace(record.locator, source_id="SRCLOC-DRIFT"))
    elif mutation == "object_id":
        drifted = replace(record, locator=replace(record.locator, object_id="SOURCE-DRIFT"))
    elif mutation == "field_path":
        drifted = replace(record, locator=replace(record.locator, field_path="/value/drift"))
    elif mutation == "track":
        drifted = replace(record, track=contracts.EvidenceTrack.CHART_STRUCTURE)
    elif mutation == "transformation":
        drifted = replace(record, transformation="MDFF_V1_COPY")
    elif mutation == "value":
        drifted = replace(record, value="DRIFT")
    else:
        binding_changes = {
            "source_snapshot_id": {"source_snapshot_id": "SNAPSHOT-DRIFT"},
            "source_schema_version": {"source_schema_version": "schema.drift.v1"},
            "contract_version": {"contract_version": "contract-drift-v1"},
            "captured_at": {"captured_at": "2026-07-20T00:00:00Z"},
            "content_digest": {
                "content_digest": DigestRef(
                    "sha256",
                    "RFC8785-JCS-UTF8",
                    "0" * 64,
                )
            },
        }
        binding = replace(record.locator.binding, **binding_changes[mutation])
        drifted = replace(record, locator=replace(record.locator, binding=binding))
    invalid_package = replace(package, records=(drifted,) + package.records[1:])
    result = replace(_evaluated(decision_case), package_id=package.package_id)
    with pytest.raises(F09SourceError):
        build_trace(invalid_package, result, created_at="2026-07-19T00:00:00Z")


def test_valid_projection_returns_explicit_empty_issue_tuple(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    assert validate_statement_projection(statement_set, trace, result) == ProjectionValidationResult(True, ())


def test_card_sources_bind_two_distinct_frozen_file_digests():
    normative_contract_ref, machine_appendix_ref = _card_source_refs()

    assert normative_contract_ref.object_type == "CONTRACT"
    assert machine_appendix_ref.object_type == "MACHINE_APPENDIX"
    assert normative_contract_ref.digest_binding.digest != machine_appendix_ref.digest_binding.digest


@pytest.mark.parametrize(
    ("field", "value", "issue_code", "field_path"),
    [
        ("statement_set_id", "", "STATEMENT.SET_INVALID", "/statement_set"),
        ("statement_schema_version", "", "STATEMENT.SET_INVALID", "/statement_set"),
        ("case_id", "", "STATEMENT.SET_INVALID", "/statement_set"),
        ("track", "MANUAL_IMPORT", "STATEMENT.SET_INVALID", "/statement_set"),
        ("source_package_ref", None, "STATEMENT.SET_INVALID", "/statement_set"),
        ("content_digest", None, "STATEMENT.SET_INVALID", "/statement_set"),
        ("generated_at", "", "STATEMENT.SET_INVALID", "/statement_set"),
        ("publication_state", "UNKNOWN", "STATEMENT.SET_INVALID", "/statement_set"),
        ("issue_ids", [], "STATEMENT.SET_INVALID", "/statement_set"),
        ("statements", (), "STATEMENT.RECORD_INVALID", "/statements/0"),
    ],
)
def test_required_statement_set_fields_fail_with_typed_issue(decision_case, field, value, issue_code, field_path):
    trace, statement_set, result = _valid_projection(decision_case)
    invalid = replace(statement_set, **{field: value})
    validation = validate_statement_projection(invalid, trace, result)
    assert validation == ProjectionValidationResult(False, (contracts.DetectedIssue(issue_code, field_path),))


@pytest.mark.parametrize(
    "field",
    ["statement_id", "statement_revision_id", "statement_schema_version", "case_id", "statement_set_id", "semantic_scope", "domain", "statement_text", "decision_result_id", "action_id"],
)
def test_required_statement_fields_fail_with_typed_issue(decision_case, field):
    trace, statement_set, result = _valid_projection(decision_case)
    invalid_statement = replace(statement_set.statements[0], **{field: ""})
    validation = validate_statement_projection(replace(statement_set, statements=(invalid_statement,)), trace, result)
    assert validation == ProjectionValidationResult(False, (contracts.DetectedIssue("STATEMENT.RECORD_INVALID", "/statements/0"),))


def test_every_statement_constructor_field_is_required(decision_case):
    _, statement_set, _ = _valid_projection(decision_case)
    statement = statement_set.statements[0]
    values = {field.name: getattr(statement, field.name) for field in fields(StandardStatement)}
    for field in fields(StandardStatement):
        incomplete = dict(values)
        incomplete.pop(field.name)
        with pytest.raises(TypeError):
            StandardStatement(**incomplete)


def test_every_statement_set_constructor_field_is_required(decision_case):
    _, statement_set, _ = _valid_projection(decision_case)
    values = {field.name: getattr(statement_set, field.name) for field in fields(StatementSet)}
    for field in fields(StatementSet):
        incomplete = dict(values)
        incomplete.pop(field.name)
        with pytest.raises(TypeError):
            StatementSet(**incomplete)


@pytest.mark.parametrize("binding_name", ["output_precision_binding", "validation_plan_binding"])
def test_statement_declaration_identity_drift_fails_closed(decision_case, binding_name):
    trace, statement_set, result = _valid_projection(decision_case)
    statement = statement_set.statements[0]
    other = statement.validation_plan_binding if binding_name == "output_precision_binding" else statement.output_precision_binding
    invalid_statement = replace(statement, **{binding_name: other})
    validation = validate_statement_projection(replace(statement_set, statements=(invalid_statement,)), trace, result)
    assert validation == ProjectionValidationResult(False, (contracts.DetectedIssue("TRACE.BINDING_MISMATCH", "/statements/0/output_precision_binding"),))


@pytest.mark.parametrize("binding_name", ["output_precision_binding", "validation_plan_binding"])
@pytest.mark.parametrize(
    ("ref_field", "value"),
    [
        ("declaration_id", "DECLARATION-DRIFT"),
        ("declaration_type", "OUTPUT_PRECISION"),
        ("card_id", "F08"),
        ("contract_version", "contract-drift"),
        ("declaration_schema_version", "schema-drift"),
        ("content_digest", DigestRef("sha256", "RFC8785-JCS-UTF8", "0" * 64)),
    ],
)
def test_each_six_field_declaration_identity_drift_fails_closed(decision_case, binding_name, ref_field, value):
    trace, statement_set, result = _valid_projection(decision_case)
    statement = statement_set.statements[0]
    binding = getattr(statement, binding_name)
    assert isinstance(binding, contracts.ResolvedDeclarationBinding)
    if ref_field == "declaration_type" and binding.ref.declaration_type == value:
        value = "VALIDATION_PLAN"
    drifted = replace(binding, ref=replace(binding.ref, **{ref_field: value}))
    invalid_statement = replace(statement, **{binding_name: drifted})
    invalid_set = replace(statement_set, statements=(invalid_statement,))
    validation = validate_statement_projection(invalid_set, trace, result)
    assert validation == ProjectionValidationResult(False, (contracts.DetectedIssue("TRACE.BINDING_MISMATCH", "/statements/0/output_precision_binding"),))


@pytest.mark.parametrize("binding_name", ["output_precision_binding", "validation_plan_binding"])
def test_decision_trace_declaration_identity_drift_fails_closed(decision_case, binding_name):
    trace, statement_set, result = _valid_projection(decision_case)
    decision_trace = statement_set.decision_trace_ref
    other = decision_trace.validation_plan_binding if binding_name == "output_precision_binding" else decision_trace.output_precision_binding
    invalid_set = replace(statement_set, decision_trace_ref=replace(decision_trace, **{binding_name: other}))
    validation = validate_statement_projection(invalid_set, trace, result)
    assert validation.detected_issues == (contracts.DetectedIssue("TRACE.BINDING_MISMATCH", "/statements/0/output_precision_binding"),)


@pytest.mark.parametrize("surface", ["statement", "decision_trace"])
@pytest.mark.parametrize("mutation", ["alter", "reorder", "drop", "add"])
def test_each_basis_identity_mutation_fails_closed(decision_case, surface, mutation):
    trace, statement_set, result = _valid_projection(decision_case)
    basis = statement_set.statements[0].basis_record_ids
    assert len(basis) > 1
    drifted = {
        "alter": ("ALTERED",) + basis[1:],
        "reorder": tuple(reversed(basis)),
        "drop": basis[:-1],
        "add": basis + ("EXTRA",),
    }[mutation]
    if surface == "statement":
        invalid_statement = replace(statement_set.statements[0], basis_record_ids=drifted)
        invalid_set = replace(statement_set, statements=(invalid_statement,))
        expected_issue = contracts.DetectedIssue(
            "TRACE.BINDING_MISMATCH",
            "/trace/identity",
        )
    else:
        invalid_set = replace(statement_set, decision_trace_ref=replace(statement_set.decision_trace_ref, basis_record_ids=drifted))
        expected_issue = contracts.DetectedIssue(
            "TRACE.BASIS_MISMATCH",
            "/statements/0/basis_record_ids",
        )
    validation = validate_statement_projection(invalid_set, trace, result)
    assert validation == ProjectionValidationResult(False, (expected_issue,))


def test_implemented_capability_claim_fails_closed(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    statement = statement_set.statements[0]
    card = replace(statement.card_identity_refs[0], runtime_capability_status="IMPLEMENTED")
    invalid_statement = replace(statement, card_identity_refs=(card,))
    validation = validate_statement_projection(replace(statement_set, statements=(invalid_statement,)), trace, result)
    assert validation == ProjectionValidationResult(False, (contracts.DetectedIssue("CARD.IDENTITY_INVALID", "/card_identity_refs/0/runtime_capability_status"),))


def test_output_prose_cannot_expand_beyond_copied_outcome_scope(decision_case):
    trace, invalid_set, output_result = _projection_with_statement_text(
        decision_case,
        DecisionAction.OUTPUT,
        "axis action object tense wealth outcome",
    )
    validation = validate_statement_projection(invalid_set, trace, output_result)
    assert validation == ProjectionValidationResult(False, (contracts.DetectedIssue("OUTPUT.SCOPE_EXCEEDED", "/statements/0/statement_text"),))


@pytest.mark.parametrize("action", [DecisionAction.CONDITIONAL, DecisionAction.ASK, DecisionAction.ABSTAIN, DecisionAction.HUMAN_REVIEW])
def test_non_output_action_cannot_use_formal_output_prose(decision_case, action):
    trace, invalid_set, invalid_result = _projection_with_statement_text(
        decision_case,
        action,
        "axis action object tense",
    )
    validation = validate_statement_projection(invalid_set, trace, invalid_result)
    assert validation == ProjectionValidationResult(False, (contracts.DetectedIssue("STATEMENT.RECORD_INVALID", "/statements/0"),))


@pytest.mark.parametrize(
    ("surface", "field"),
    [
        ("statement", "statement_set_id"),
        ("statement", "decision_result_id"),
        ("statement", "action_id"),
        ("statement", "case_id"),
        ("statement", "track"),
        ("set", "case_id"),
        ("set", "track"),
        ("set", "source_package_ref"),
        ("decision_trace", "result_ref"),
    ],
)
def test_each_nonempty_projection_identity_drift_fails_closed(decision_case, surface, field):
    trace, statement_set, result = _valid_projection(decision_case)
    if surface == "statement":
        value = RunTrack.STAGED_L6 if field == "track" else "DRIFT"
        invalid = replace(statement_set, statements=(replace(statement_set.statements[0], **{field: value}),))
    elif surface == "set":
        value = RunTrack.STAGED_L6 if field == "track" else (_ref("PACKAGE", "PACKAGE-DRIFT") if field == "source_package_ref" else "DRIFT")
        invalid = replace(statement_set, **{field: value})
    else:
        invalid = replace(statement_set, decision_trace_ref=replace(statement_set.decision_trace_ref, result_ref=_ref("DECISION", "RESULT-DRIFT")))
    assert validate_statement_projection(invalid, trace, result) == ProjectionValidationResult(False, (contracts.DetectedIssue("TRACE.BINDING_MISMATCH", "/trace/identity"),))


def test_statement_set_ref_cannot_alias_statement_identity(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    invalid = replace(trace, statement_set_ref=trace.nodes[-1].object_ref)
    validation = validate_statement_projection(statement_set, invalid, result)
    assert validation == ProjectionValidationResult(False, (contracts.DetectedIssue("TRACE.BINDING_MISMATCH", "/trace/identity"),))


def test_transformation_target_must_have_unique_reachable_node_and_terminal_edge(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    target = trace.edges[0].to_ref
    missing_node = replace(trace, nodes=tuple(node for node in trace.nodes if node.object_ref != target))
    assert validate_statement_projection(statement_set, missing_node, result) == ProjectionValidationResult(False, (contracts.DetectedIssue("SOURCE.POINTER_UNRESOLVED", "/transformations/LOSSLESS_COPY"),))
    missing_edge = replace(trace, edges=trace.edges[1:])
    assert validate_statement_projection(statement_set, missing_edge, result) == ProjectionValidationResult(False, (contracts.DetectedIssue("TRACE.EDGE_MISSING", "/transformations/mappings"),))


def test_statement_evidence_locator_and_digest_must_close_to_snapshot(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    statement = statement_set.statements[0]
    missing_locator = replace(statement.evidence_refs[0], source_locator_id=None)
    invalid_statement = replace(statement, evidence_refs=(missing_locator,) + statement.evidence_refs[1:])
    assert validate_statement_projection(replace(statement_set, statements=(invalid_statement,)), trace, result) == ProjectionValidationResult(False, (contracts.DetectedIssue("SOURCE.POINTER_UNRESOLVED", "/statements/0/evidence_refs"),))
    drifted_digest = replace(statement.evidence_refs[0], digest_binding=DigestPresent("PRESENT", DigestRef("sha256", "RFC8785-JCS-UTF8", "0" * 64)))
    invalid_statement = replace(statement, evidence_refs=(drifted_digest,) + statement.evidence_refs[1:])
    assert validate_statement_projection(replace(statement_set, statements=(invalid_statement,)), trace, result) == ProjectionValidationResult(False, (contracts.DetectedIssue("SOURCE.IDENTITY_MISMATCH", "/statements/0/evidence_refs"),))


@pytest.mark.parametrize(
    "object_type",
    ["PACKAGE", "DECISION", "STATEMENT_SET", "STATEMENT"],
)
def test_each_required_provenance_node_is_independently_required(decision_case, object_type):
    trace, statement_set, result = _valid_projection(decision_case)
    invalid = replace(
        trace,
        nodes=tuple(
            node
            for node in trace.nodes
            if node.object_ref.object_type != object_type
        ),
    )
    assert validate_statement_projection(statement_set, invalid, result) == ProjectionValidationResult(
        False,
        (contracts.DetectedIssue("SOURCE.POINTER_UNRESOLVED", "/trace/provenance"),),
    )


@pytest.mark.parametrize(
    "edge_selector",
    [
        ("DERIVED_FROM", "EVIDENCE", "PACKAGE"),
        ("EVALUATED_BY", "PACKAGE", "DECISION"),
        ("RENDERED_AS", "DECISION", "STATEMENT_SET"),
        ("RENDERED_AS", "STATEMENT_SET", "STATEMENT"),
    ],
)
def test_each_required_provenance_segment_is_independently_required(decision_case, edge_selector):
    trace, statement_set, result = _valid_projection(decision_case)
    matching_edges = tuple(
        edge
        for edge in trace.edges
        if (
            edge.edge_type,
            edge.from_ref.object_type,
            edge.to_ref.object_type,
        )
        == edge_selector
    )
    assert matching_edges
    invalid = replace(
        trace,
        edges=tuple(edge for edge in trace.edges if edge not in matching_edges),
    )
    assert validate_statement_projection(statement_set, invalid, result) == ProjectionValidationResult(
        False,
        (contracts.DetectedIssue("TRACE.EDGE_MISSING", "/trace/provenance"),),
    )


@pytest.mark.parametrize(
    ("surface", "field"),
    [
        ("trace", "trace_id"),
        ("trace", "trace_schema_version"),
        ("package_ref", "revision_id"),
        ("package_ref", "schema_version"),
        ("package_ref", "contract_version"),
        ("package_ref", "digest_binding"),
        ("package_ref", "captured_at"),
        ("result_ref", "revision_id"),
        ("result_ref", "schema_version"),
        ("result_ref", "contract_version"),
        ("result_ref", "digest_binding"),
        ("result_ref", "captured_at"),
        ("statement_set", "statement_schema_version"),
        ("statement_set", "content_digest"),
        ("statement", "statement_revision_id"),
        ("statement", "statement_schema_version"),
        ("statement", "content_digest"),
    ],
)
def test_each_versioned_projection_identity_axis_fails_closed(decision_case, surface, field):
    trace, statement_set, result = _valid_projection(decision_case)
    digest = DigestRef("sha256", "RFC8785-JCS-UTF8", "0" * 64)
    if surface == "trace":
        invalid_trace = replace(trace, **{field: "DRIFT"})
        invalid_set = statement_set
    elif surface in ("package_ref", "result_ref"):
        ref_name = "normalized_package_ref" if surface == "package_ref" else "decision_result_ref"
        ref = getattr(trace, ref_name)
        value = DigestPresent("PRESENT", digest) if field == "digest_binding" else "DRIFT"
        invalid_trace = replace(trace, **{ref_name: replace(ref, **{field: value})})
        invalid_set = statement_set
    elif surface == "statement_set":
        value = digest if field == "content_digest" else "DRIFT"
        invalid_trace = trace
        invalid_set = replace(statement_set, **{field: value})
    else:
        value = digest if field == "content_digest" else "DRIFT"
        invalid_trace = trace
        invalid_set = replace(
            statement_set,
            statements=(replace(statement_set.statements[0], **{field: value}),),
        )
    assert validate_statement_projection(invalid_set, invalid_trace, result) == ProjectionValidationResult(
        False,
        (contracts.DetectedIssue("TRACE.BINDING_MISMATCH", "/trace/identity"),),
    )


@pytest.mark.parametrize(
    ("surface", "field", "value", "issue_code", "field_path"),
    [
        (
            "statement",
            "display_section",
            "DRIFT",
            "TRACE.BINDING_MISMATCH",
            "/trace/identity",
        ),
        (
            "statement",
            "relation_ids",
            ("REL-DRIFT",),
            "TRACE.BINDING_MISMATCH",
            "/trace/identity",
        ),
        (
            "statement",
            "feedback_policy",
            "FEEDBACK_ALLOWED",
            "TRACE.BINDING_MISMATCH",
            "/trace/identity",
        ),
        (
            "statement",
            "issue_ids",
            ("ISSUE-DRIFT",),
            "TRACE.BINDING_MISMATCH",
            "/trace/identity",
        ),
        (
            "card",
            "field_path",
            "/cards/DRIFT",
            "TRACE.BINDING_MISMATCH",
            "/trace/identity",
        ),
        (
            "card",
            "source_locator_ids",
            ("SRCLOC-DRIFT",),
            "TRACE.BINDING_MISMATCH",
            "/trace/identity",
        ),
        (
            "card_contract",
            "revision_id",
            "DRIFT",
            "CARD.IDENTITY_INVALID",
            "/card_identity_refs/0",
        ),
        (
            "card_appendix",
            "captured_at",
            "DRIFT",
            "CARD.IDENTITY_INVALID",
            "/card_identity_refs/0",
        ),
    ],
)
def test_each_canonical_statement_payload_drift_requires_new_identity(
    decision_case,
    surface,
    field,
    value,
    issue_code,
    field_path,
):
    trace, statement_set, result = _valid_projection(decision_case)
    statement = statement_set.statements[0]
    if surface == "statement":
        invalid_statement = replace(statement, **{field: value})
    else:
        card = statement.card_identity_refs[0]
        if surface == "card":
            invalid_card = replace(card, **{field: value})
        else:
            ref_name = (
                "normative_contract_ref"
                if surface == "card_contract"
                else "machine_appendix_ref"
            )
            invalid_card = replace(
                card,
                **{
                    ref_name: replace(
                        getattr(card, ref_name),
                        **{field: value},
                    ),
                },
            )
        invalid_statement = replace(
            statement,
            card_identity_refs=(invalid_card,),
        )
    invalid_set = replace(statement_set, statements=(invalid_statement,))
    assert validate_statement_projection(invalid_set, trace, result) == ProjectionValidationResult(
        False,
        (contracts.DetectedIssue(issue_code, field_path),),
    )


@pytest.mark.parametrize(
    "field",
    ["revision_id", "schema_version", "contract_version", "captured_at"],
)
def test_each_statement_evidence_version_axis_fails_as_identity_drift(
    decision_case,
    field,
):
    trace, statement_set, result = _valid_projection(decision_case)
    statement = statement_set.statements[0]
    drifted_ref = replace(statement.evidence_refs[0], **{field: "DRIFT"})
    invalid_statement = replace(
        statement,
        evidence_refs=(drifted_ref,) + statement.evidence_refs[1:],
    )
    invalid_set = replace(statement_set, statements=(invalid_statement,))
    assert validate_statement_projection(invalid_set, trace, result) == ProjectionValidationResult(
        False,
        (contracts.DetectedIssue("TRACE.BINDING_MISMATCH", "/trace/identity"),),
    )


def test_build_trace_rejects_malformed_contract_ref_before_dereference(decision_case):
    package = _canonical_package(decision_case["package"].case_id)
    result = replace(
        _evaluated(decision_case),
        package_id=package.package_id,
        contract_ref=object(),
    )
    with pytest.raises(F09ContractError) as caught:
        build_trace(package, result, created_at="2026-07-19T00:00:00Z")
    assert caught.value.issue_code == "TRACE.RESULT_INVALID"
    assert caught.value.field_path == "/decision_result/contract_ref"


def test_validator_rejects_malformed_contract_ref_before_dereference(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    with pytest.raises(F09ContractError) as caught:
        validate_statement_projection(
            statement_set,
            trace,
            replace(result, contract_ref=object()),
        )
    assert caught.value.issue_code == "TRACE.BINDING_MISMATCH"
    assert caught.value.field_path == "/decision_result/contract_ref"


def test_build_trace_rejects_malformed_action_envelope_before_dereference(decision_case):
    package = _canonical_package(decision_case["package"].case_id)
    result = replace(
        _evaluated(decision_case),
        package_id=package.package_id,
        action_envelope=object(),
    )
    with pytest.raises(F09ContractError) as caught:
        build_trace(package, result, created_at="2026-07-19T00:00:00Z")
    assert caught.value.issue_code == "TRACE.RESULT_INVALID"
    assert caught.value.field_path == "/decision_result/action_envelope"


def test_build_statement_set_rejects_malformed_result_ref_before_dereference(decision_case):
    trace, _, result = _valid_projection(decision_case)
    malformed_trace = replace(trace, decision_result_ref=object())
    with pytest.raises(F09ContractError) as caught:
        build_statement_set(
            malformed_trace,
            result,
            generated_at="2026-07-19T00:00:00Z",
        )
    assert caught.value.issue_code == "STATEMENT.TRACE_INVALID"
    assert caught.value.field_path == "/trace/decision_result_ref"


def test_build_statement_set_rejects_malformed_action_envelope_before_dereference(decision_case):
    trace, _, result = _valid_projection(decision_case)
    with pytest.raises(F09ContractError) as caught:
        build_statement_set(
            trace,
            replace(result, action_envelope=object()),
            generated_at="2026-07-19T00:00:00Z",
        )
    assert caught.value.issue_code == "STATEMENT.RESULT_INVALID"
    assert caught.value.field_path == "/decision_result/action_envelope"


@pytest.mark.parametrize(
    ("source_index", "binding"),
    [
        (0, DigestMissing("MISSING", None, "CONTRACT-SOURCE-MISSING")),
        (1, DigestMissing("MISSING", None, "APPENDIX-SOURCE-MISSING")),
    ],
)
def test_builder_rejects_missing_card_source_digest(decision_case, source_index, binding):
    package = _canonical_package(decision_case["package"].case_id)
    result = replace(_evaluated(decision_case), package_id=package.package_id)
    refs = list(_card_source_refs())
    refs[source_index] = replace(refs[source_index], digest_binding=binding)

    with pytest.raises(F09ContractError) as caught:
        _build_trace(
            package,
            result,
            normative_contract_ref=refs[0],
            machine_appendix_ref=refs[1],
            created_at="2026-07-19T00:00:00Z",
        )
    assert caught.value.issue_code == "CARD.IDENTITY_INVALID"


@pytest.mark.parametrize(
    "mutation",
    [
        "coordinated-fake-digests",
        "copied-contract-digest",
        "wrong-algorithm",
        "wrong-canonicalization",
    ],
)
def test_builder_rejects_non_authoritative_card_source_refs(
    decision_case,
    mutation,
):
    package = _canonical_package(decision_case["package"].case_id)
    result = replace(_evaluated(decision_case), package_id=package.package_id)
    contract_ref, appendix_ref = _card_source_refs()
    if mutation == "coordinated-fake-digests":
        contract_ref = replace(
            contract_ref,
            digest_binding=DigestPresent(
                "PRESENT",
                DigestRef("sha256", "RAW-BYTES", "0" * 64),
            ),
        )
        appendix_ref = replace(
            appendix_ref,
            digest_binding=DigestPresent(
                "PRESENT",
                DigestRef("sha256", "RAW-BYTES", "1" * 64),
            ),
        )
    elif mutation == "copied-contract-digest":
        appendix_ref = replace(
            appendix_ref,
            digest_binding=contract_ref.digest_binding,
        )
    elif mutation == "wrong-algorithm":
        digest = contract_ref.digest_binding.digest
        contract_ref = replace(
            contract_ref,
            digest_binding=DigestPresent(
                "PRESENT",
                replace(digest, algorithm="sha512"),
            ),
        )
    else:
        digest = appendix_ref.digest_binding.digest
        appendix_ref = replace(
            appendix_ref,
            digest_binding=DigestPresent(
                "PRESENT",
                replace(digest, canonicalization="RFC8785-JCS-UTF8"),
            ),
        )

    with pytest.raises(F09ContractError) as caught:
        _build_trace(
            package,
            result,
            normative_contract_ref=contract_ref,
            machine_appendix_ref=appendix_ref,
            created_at="2026-07-19T00:00:00Z",
        )
    assert caught.value.issue_code == "CARD.IDENTITY_INVALID"


def test_validator_rejects_coordinated_fake_card_authority_graph(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    package = _canonical_package(trace.case_id)
    contract_ref, appendix_ref = _card_source_refs()
    fake_contract_ref = replace(
        contract_ref,
        digest_binding=DigestPresent(
            "PRESENT",
            DigestRef("sha256", "RAW-BYTES", "0" * 64),
        ),
    )
    fake_appendix_ref = replace(
        appendix_ref,
        digest_binding=DigestPresent(
            "PRESENT",
            DigestRef("sha256", "RAW-BYTES", "1" * 64),
        ),
    )
    statement = statement_set.statements[0]
    fake_card_ref = replace(
        statement.card_identity_refs[0],
        normative_contract_ref=fake_contract_ref,
        machine_appendix_ref=fake_appendix_ref,
    )
    fake_set = replace(
        statement_set,
        statements=(replace(statement, card_identity_refs=(fake_card_ref,)),),
    )

    assert _validate_statement_projection(
        fake_set,
        trace,
        result,
        package,
        normative_contract_ref=fake_contract_ref,
        machine_appendix_ref=fake_appendix_ref,
    ) == ProjectionValidationResult(
        False,
        (contracts.DetectedIssue("CARD.IDENTITY_INVALID", "/card_identity_refs/0"),),
    )


@pytest.mark.parametrize(
    "binding",
    [
        DigestPresent("DRIFT", PI300_DIGEST),
        DigestPresent(
            "PRESENT",
            DigestRef("", "RFC8785-JCS-UTF8", "0" * 64),
        ),
        DigestPresent(
            "PRESENT",
            DigestRef("sha256", "", "0" * 64),
        ),
        DigestMissing("DRIFT", None, "ISSUE-DIGEST-MISSING"),
        DigestMissing("MISSING", None, ""),
    ],
)
def test_digest_binding_discriminant_and_missing_issue_are_closed(decision_case, binding):
    trace, statement_set, result = _valid_projection(decision_case)
    malformed_ref = replace(trace.decision_result_ref, digest_binding=binding)
    malformed_trace = replace(trace, decision_result_ref=malformed_ref)
    with pytest.raises(F09SourceError) as caught:
        validate_statement_projection(statement_set, malformed_trace, result)
    assert caught.value.issue_code == "TRACE.EDGE_MISSING"


def test_statement_set_identity_binds_case_result_ref_and_statement_revision(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    mutations = (
        replace(statement_set, case_id="CASE-DRIFT"),
        replace(
            statement_set,
            decision_trace_ref=replace(
                statement_set.decision_trace_ref,
                result_ref=replace(
                    statement_set.decision_trace_ref.result_ref,
                    revision_id="rev-drift",
                ),
            ),
        ),
        replace(
            statement_set,
            statements=(
                replace(
                    statement_set.statements[0],
                    statement_revision_id="rev-drift",
                ),
            ),
        ),
    )
    for invalid_set in mutations:
        assert validate_statement_projection(invalid_set, trace, result) == ProjectionValidationResult(
            False,
            (contracts.DetectedIssue("TRACE.BINDING_MISMATCH", "/trace/identity"),),
        )


def test_generated_at_drift_invalidates_statement_set_digest(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    invalid_set = replace(statement_set, generated_at="2026-07-20T00:00:00Z")

    assert validate_statement_projection(invalid_set, trace, result) == ProjectionValidationResult(
        False,
        (contracts.DetectedIssue("TRACE.BINDING_MISMATCH", "/trace/identity"),),
    )


def test_card_evaluator_state_must_remain_not_evaluated(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    statement = statement_set.statements[0]
    invalid_card = replace(
        statement.card_identity_refs[0],
        evaluator_state=contracts.FieldEvaluatorState.EVALUATED,
    )
    invalid_set = replace(
        statement_set,
        statements=(replace(statement, card_identity_refs=(invalid_card,)),),
    )

    assert validate_statement_projection(invalid_set, trace, result) == ProjectionValidationResult(
        False,
        (contracts.DetectedIssue("CARD.IDENTITY_INVALID", "/card_identity_refs/0"),),
    )


def test_validator_rejects_swapped_card_source_authorities(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    package = _canonical_package(trace.case_id)
    normative_contract_ref, machine_appendix_ref = _card_source_refs()

    assert _validate_statement_projection(
        statement_set,
        trace,
        result,
        package,
        normative_contract_ref=machine_appendix_ref,
        machine_appendix_ref=normative_contract_ref,
    ) == ProjectionValidationResult(
        False,
        (contracts.DetectedIssue("CARD.IDENTITY_INVALID", "/card_identity_refs/0"),),
    )


def test_validator_requires_authoritative_package_snapshot(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    normative_contract_ref, machine_appendix_ref = _card_source_refs()

    assert _validate_statement_projection(
        statement_set,
        trace,
        result,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
    ) == ProjectionValidationResult(
        False,
        (contracts.DetectedIssue("TRACE.BINDING_MISMATCH", "/trace/package_digest"),),
    )


def test_self_consistent_non_authoritative_package_graph_fails_digest_check(decision_case):
    authoritative_package = _canonical_package(decision_case["package"].case_id)
    projected_package = replace(authoritative_package, track=RunTrack.STAGED_L6)
    result = replace(_evaluated(decision_case), package_id=projected_package.package_id)
    trace = build_trace(
        projected_package,
        result,
        created_at="2026-07-19T00:00:00Z",
    )
    statement_set = build_statement_set(
        trace,
        result,
        generated_at="2026-07-19T00:00:00Z",
    )
    normative_contract_ref, machine_appendix_ref = _card_source_refs()

    assert _validate_statement_projection(
        statement_set,
        trace,
        result,
        authoritative_package,
        normative_contract_ref=normative_contract_ref,
        machine_appendix_ref=machine_appendix_ref,
    ) == ProjectionValidationResult(
        False,
        (contracts.DetectedIssue("TRACE.BINDING_MISMATCH", "/trace/package_digest"),),
    )


def test_result_payload_drift_cannot_reuse_old_trace_digest(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    drifted_action = replace(
        result.action_envelope,
        reason_codes=result.action_envelope.reason_codes + ("DRIFT",),
    )
    assert validate_statement_projection(
        statement_set,
        trace,
        replace(result, action_envelope=drifted_action),
    ) == ProjectionValidationResult(
        False,
        (contracts.DetectedIssue("TRACE.BINDING_MISMATCH", "/trace/identity"),),
    )


def test_malformed_projection_raises_existing_typed_error(decision_case):
    trace, _, result = _valid_projection(decision_case)
    with pytest.raises(F09ContractError) as caught:
        validate_statement_projection(object(), trace, result)
    assert caught.value.issue_code == "STATEMENT.SET_INVALID"
    assert caught.value.field_path == "/statement_set"


@pytest.mark.parametrize(
    ("mutation", "error_type", "issue_code"),
    [
        (lambda trace: replace(trace, nodes=(replace(trace.nodes[0], object_ref=object()),)), F09SourceError, "TRACE.EDGE_MISSING"),
        (lambda trace: replace(trace, source_snapshot_refs=(replace(trace.source_snapshot_refs[0], content_digest=object()),)), F09SourceError, "SOURCE.IDENTITY_MISMATCH"),
        (lambda trace: replace(trace, transformations=(replace(trace.transformations[0], source_object_refs=(object(),)),) + trace.transformations[1:]), F09IntegrityError, "TRANSFORMATION.UNSUPPORTED"),
    ],
)
def test_nested_malformed_graph_raises_typed_error(decision_case, mutation, error_type, issue_code):
    trace, statement_set, result = _valid_projection(decision_case)
    with pytest.raises(error_type) as caught:
        validate_statement_projection(statement_set, mutation(trace), result)
    assert caught.value.issue_code == issue_code


def test_malformed_decision_trace_result_ref_raises_typed_error(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    invalid_set = replace(
        statement_set,
        decision_trace_ref=replace(
            statement_set.decision_trace_ref,
            result_ref=object(),
        ),
    )
    with pytest.raises(F09ContractError) as caught:
        validate_statement_projection(invalid_set, trace, result)
    assert caught.value.issue_code == "STATEMENT.SET_INVALID"


def test_malformed_card_nested_ref_raises_typed_error(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    statement = statement_set.statements[0]
    invalid_card = replace(
        statement.card_identity_refs[0],
        normative_contract_ref=object(),
    )
    invalid_set = replace(
        statement_set,
        statements=(
            replace(statement, card_identity_refs=(invalid_card,)),
        ),
    )
    with pytest.raises(F09ContractError) as caught:
        validate_statement_projection(invalid_set, trace, result)
    assert caught.value.issue_code == "STATEMENT.RECORD_INVALID"


@pytest.mark.parametrize(
    ("predicate", "mutation", "issue_code", "field_path"),
    [
        ("T93", lambda trace: replace(trace, transformations=(replace(trace.transformations[0], field_mappings=(replace(trace.transformations[0].field_mappings[0], source_field_path="/drift"),) + trace.transformations[0].field_mappings[1:]),) + trace.transformations[1:]), "SOURCE.LOCATOR_MISMATCH", "/source_locators"),
        ("T95", lambda trace: replace(trace, transformations=(replace(trace.transformations[0], field_mappings=(replace(trace.transformations[0].field_mappings[0], source_field_path="drift"),) + trace.transformations[0].field_mappings[1:]),) + trace.transformations[1:]), "SOURCE.POINTER_UNRESOLVED", "/transformations/LOSSLESS_COPY"),
        ("T96", lambda trace: replace(trace, source_snapshot_refs=(replace(trace.source_snapshot_refs[0], source_snapshot_id="SNAPSHOT-DRIFT"),)), "SOURCE.IDENTITY_MISMATCH", "/source_locators/binding"),
        ("T97", lambda trace: replace(trace, transformations=trace.transformations[:2] + (replace(trace.transformations[2], field_mappings=()),)), "TRACE.EDGE_MISSING", "/transformations/mappings"),
        ("T100", lambda trace: replace(trace, transformations=(replace(trace.transformations[0], source_object_refs=(replace(trace.transformations[0].source_object_refs[0], source_locator_id="SRCLOC-UNKNOWN"),)),) + trace.transformations[1:]), "SOURCE.BINDING_INVALID", "/source_locators/0"),
    ],
)
def test_each_r15_source_predicate_has_exact_issue_pair(decision_case, predicate, mutation, issue_code, field_path):
    trace, statement_set, result = _valid_projection(decision_case)
    assert validate_statement_projection(statement_set, mutation(trace), result) == ProjectionValidationResult(False, (contracts.DetectedIssue(issue_code, field_path),))


def test_t99_unsupported_source_kind_has_exact_issue_pair(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    source = trace.transformations[0].source_object_refs[0]
    changed_ref = replace(trace.nodes[0].object_ref, object_type="PACKAGE")
    transformation = replace(
        trace.transformations[0],
        source_object_refs=(replace(source, object_type="PACKAGE"),),
    )
    edges = tuple(
        replace(edge, from_ref=changed_ref)
        if edge.transformation_id == transformation.transformation_id
        else edge
        for edge in trace.edges
    )
    invalid = replace(
        trace,
        nodes=(replace(trace.nodes[0], object_ref=changed_ref),) + trace.nodes[1:],
        transformations=(transformation,) + trace.transformations[1:],
        edges=edges,
    )
    assert validate_statement_projection(statement_set, invalid, result) == ProjectionValidationResult(
        False,
        (contracts.DetectedIssue("TRANSFORMATION.UNSUPPORTED", "/transformations/0"),),
    )


def _with_t99(trace):
    source = trace.transformations[0].source_object_refs[0]
    changed_ref = replace(trace.nodes[0].object_ref, object_type="PACKAGE")
    transformation = replace(
        trace.transformations[0],
        source_object_refs=(replace(source, object_type="PACKAGE"),),
    )
    return replace(
        trace,
        nodes=(replace(trace.nodes[0], object_ref=changed_ref),) + trace.nodes[1:],
        transformations=(transformation,) + trace.transformations[1:],
        edges=tuple(
            replace(edge, from_ref=changed_ref)
            if edge.transformation_id == transformation.transformation_id
            else edge
            for edge in trace.edges
        ),
    )


def test_r15_detection_order_keeps_t95_before_t100(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    source = replace(trace.transformations[0].source_object_refs[0], source_locator_id="SRCLOC-UNKNOWN")
    mapping = replace(trace.transformations[0].field_mappings[0], source_field_path="drift")
    invalid_transformation = replace(trace.transformations[0], source_object_refs=(source,), field_mappings=(mapping,) + trace.transformations[0].field_mappings[1:])
    invalid = replace(trace, transformations=(invalid_transformation,) + trace.transformations[1:])
    assert validate_statement_projection(statement_set, invalid, result) == ProjectionValidationResult(False, (contracts.DetectedIssue("SOURCE.POINTER_UNRESOLVED", "/transformations/LOSSLESS_COPY"),))


def test_r15_detection_order_keeps_t100_before_t93(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    transformation = trace.transformations[0]
    invalid = replace(
        trace,
        transformations=(replace(
            transformation,
            source_object_refs=(replace(transformation.source_object_refs[0], source_locator_id="SRCLOC-UNKNOWN"),),
            field_mappings=(replace(transformation.field_mappings[0], source_field_path="/drift"),) + transformation.field_mappings[1:],
        ),) + trace.transformations[1:],
    )
    assert validate_statement_projection(statement_set, invalid, result) == ProjectionValidationResult(False, (contracts.DetectedIssue("SOURCE.BINDING_INVALID", "/source_locators/0"),))


def test_r15_detection_order_keeps_t93_before_t96(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    transformation = trace.transformations[0]
    invalid = replace(
        trace,
        transformations=(replace(transformation, field_mappings=(replace(transformation.field_mappings[0], source_field_path="/drift"),) + transformation.field_mappings[1:]),) + trace.transformations[1:],
        source_snapshot_refs=(replace(trace.source_snapshot_refs[0], source_snapshot_id="SNAPSHOT-DRIFT"),),
    )
    assert validate_statement_projection(statement_set, invalid, result) == ProjectionValidationResult(False, (contracts.DetectedIssue("SOURCE.LOCATOR_MISMATCH", "/source_locators"),))


def test_r15_detection_order_keeps_t96_before_t97(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    invalid = replace(
        trace,
        source_snapshot_refs=(replace(trace.source_snapshot_refs[0], source_snapshot_id="SNAPSHOT-DRIFT"),),
        transformations=trace.transformations[:2] + (replace(trace.transformations[2], field_mappings=()),),
    )
    assert validate_statement_projection(statement_set, invalid, result) == ProjectionValidationResult(False, (contracts.DetectedIssue("SOURCE.IDENTITY_MISMATCH", "/source_locators/binding"),))


def test_r15_detection_order_keeps_t97_before_t98(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    invalid = replace(trace, transformations=trace.transformations[:2] + (replace(trace.transformations[2], field_mappings=()),))
    assert validate_statement_projection(statement_set, invalid, result) == ProjectionValidationResult(False, (contracts.DetectedIssue("TRACE.EDGE_MISSING", "/transformations/mappings"),))


def test_r15_detection_order_keeps_t98_before_t99(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    invalid = _with_t99(trace)
    outcome = invalid.transformations[2]
    invalid = replace(invalid, transformations=invalid.transformations[:2] + (replace(outcome, field_mappings=outcome.field_mappings[:-1]),))
    assert validate_statement_projection(statement_set, invalid, result) == ProjectionValidationResult(False, (contracts.DetectedIssue("SOURCE.FIELD_MISSING", "/outcome"),))


def test_r15_detection_order_keeps_t99_before_t101(decision_case):
    trace, invalid_set, invalid_result = _projection_with_statement_text(
        decision_case,
        DecisionAction.OUTPUT,
        "axis action object tense wealth outcome",
    )
    assert validate_statement_projection(invalid_set, _with_t99(trace), invalid_result) == ProjectionValidationResult(False, (contracts.DetectedIssue("TRANSFORMATION.UNSUPPORTED", "/transformations/0"),))


def test_outcome_copy_fields_cannot_be_dropped(decision_case):
    trace, statement_set, result = _valid_projection(decision_case)
    outcome = trace.transformations[2]
    invalid = replace(trace, transformations=trace.transformations[:2] + (replace(outcome, field_mappings=outcome.field_mappings[:-1]),))
    validation = validate_statement_projection(statement_set, invalid, result)
    assert validation == ProjectionValidationResult(False, (contracts.DetectedIssue("SOURCE.FIELD_MISSING", "/outcome"),))
