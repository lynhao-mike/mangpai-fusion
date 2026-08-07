from dataclasses import replace
from hashlib import sha256

from engine.f09.contracts import RunTrack
from engine.f09.trace import DigestPresent
from tests.f09.conftest import (
    BASELINE_ARTIFACTS,
    BASELINE_FEEDBACK,
    BASELINE_SOURCE,
    BASELINE_TRACE,
    execute_scenario,
    exercise_artifact_lifecycle_phase,
    exercise_feedback_binding_phase,
    exercise_trace_validation_phase,
)
from tests.f09.data.f09_vertical_scenarios import T01

def assert_production_feedback_material_boundary(observation):
    assert observation.operation_result is None
    assert observation.bindings == ()
    assert observation.eligibility_records == ()
    assert observation.errors == (
        "F09ContractError:digest must be bounded JCS SHA-256",
    )
    assert tuple((issue.code, issue.path) for issue in observation.issues) == (
        ("FEEDBACK.MATERIAL_INVALID", "/digest"),
    )


# trace: 10 literal definitions
def test_trace_statement_set_complete_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_TRACE
    changed = replace(base, statement_set_complete=False)
    assert base.statement_set_complete is True
    assert changed.statement_set_complete is False
    assert replace(changed, statement_set_complete=base.statement_set_complete) == base
    before = exercise_trace_validation_phase(run, base, BASELINE_SOURCE)
    after = exercise_trace_validation_phase(run, changed, BASELINE_SOURCE)
    assert before.input_statement_set is not None
    assert after.input_statement_set is not None
    assert before.input_statement_set.source_package_ref is not None
    assert after.input_statement_set.source_package_ref is None
    short_state = replace(BASELINE_SOURCE, state_fields=("level", "position"))
    short_event = replace(BASELINE_SOURCE, event_fields=("level", "change"))
    assert run.trace is not None
    assert run.statement_set is not None
    empty_nodes_run = replace(run, trace=replace(run.trace, nodes=()))
    empty_statements_run = replace(run, statement_set=replace(run.statement_set, statements=()))
    assert len(run.statement_set.statements) >= 1
    statement = run.statement_set.statements[0]
    empty_card_refs_run = replace(run, statement_set=replace(run.statement_set, statements=(replace(statement, card_identity_refs=()),)))
    empty_evidence_refs_run = replace(run, statement_set=replace(run.statement_set, statements=(replace(statement, evidence_refs=()),)))
    short_state_observation = exercise_trace_validation_phase(run, base, short_state)
    short_event_observation = exercise_trace_validation_phase(run, base, short_event)
    empty_nodes_observation = exercise_trace_validation_phase(empty_nodes_run, base, BASELINE_SOURCE)
    empty_statements_observation = exercise_trace_validation_phase(empty_statements_run, base, BASELINE_SOURCE)
    empty_card_refs_observation = exercise_trace_validation_phase(empty_card_refs_run, base, BASELINE_SOURCE)
    empty_evidence_refs_observation = exercise_trace_validation_phase(empty_evidence_refs_run, base, BASELINE_SOURCE)
    assert short_state_observation.errors == ("SOURCE_STATE_FIELD_SHAPE_INVALID",)
    assert short_event_observation.errors == ("SOURCE_EVENT_FIELD_SHAPE_INVALID",)
    assert empty_nodes_observation.errors == ("TRACE_NODE_SHAPE_INVALID",)
    assert empty_statements_observation.errors == ("STATEMENT_SHAPE_INVALID",)
    assert empty_card_refs_observation.errors == ("CARD_REF_SHAPE_INVALID",)
    assert empty_evidence_refs_observation.errors == ("EVIDENCE_REF_SHAPE_INVALID",)

def test_trace_statement_complete_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_TRACE
    changed = replace(base, statement_complete=False)
    assert base.statement_complete is True
    assert changed.statement_complete is False
    assert replace(changed, statement_complete=base.statement_complete) == base
    before = exercise_trace_validation_phase(run, base, BASELINE_SOURCE)
    after = exercise_trace_validation_phase(run, changed, BASELINE_SOURCE)
    assert before.input_statement_set is not None
    assert after.input_statement_set is not None
    assert len(before.input_statement_set.statements) >= 1
    assert len(after.input_statement_set.statements) >= 1
    assert before.input_statement_set.statements[0].statement_id != ""
    assert after.input_statement_set.statements[0].statement_id == ""

def test_trace_statement_basis_ids_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_TRACE
    changed = replace(base, statement_basis_ids=("GR-RISK",))
    assert base.statement_basis_ids != ("GR-RISK",)
    assert changed.statement_basis_ids == ("GR-RISK",)
    assert replace(changed, statement_basis_ids=base.statement_basis_ids) == base
    before = exercise_trace_validation_phase(run, base, BASELINE_SOURCE)
    after = exercise_trace_validation_phase(run, changed, BASELINE_SOURCE)
    assert before.input_statement_set is not None
    assert after.input_statement_set is not None
    assert len(before.input_statement_set.statements) >= 1
    assert len(after.input_statement_set.statements) >= 1
    assert before.input_statement_set.statements[0].basis_record_ids != after.input_statement_set.statements[0].basis_record_ids
    assert after.input_statement_set.statements[0].basis_record_ids == ("GR-RISK",)

def test_trace_rule_ref_ids_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_TRACE
    changed = replace(base, rule_ref_ids=("RULE-F09-DRIFT",))
    assert base.rule_ref_ids == ("RULE-F09-ANCHOR",)
    assert changed.rule_ref_ids == ("RULE-F09-DRIFT",)
    assert replace(changed, rule_ref_ids=base.rule_ref_ids) == base
    before = exercise_trace_validation_phase(run, base, BASELINE_SOURCE)
    after = exercise_trace_validation_phase(run, changed, BASELINE_SOURCE)
    assert before.input_statement_set is not None
    assert after.input_statement_set is not None
    assert len(before.input_statement_set.statements) >= 1
    assert len(after.input_statement_set.statements) >= 1
    before_statement = before.input_statement_set.statements[0]
    after_statement = after.input_statement_set.statements[0]
    assert len(after_statement.evidence_refs) >= 1
    assert before_statement.evidence_refs != after_statement.evidence_refs
    assert after_statement.evidence_refs[0].object_id == "RULE-F09-DRIFT"

def test_trace_transformation_fidelity_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_TRACE
    changed = replace(base, transformation_fidelity="LOSSY")
    assert base.transformation_fidelity == "LOSSLESS"
    assert changed.transformation_fidelity == "LOSSY"
    assert replace(changed, transformation_fidelity=base.transformation_fidelity) == base
    before = exercise_trace_validation_phase(run, base, BASELINE_SOURCE)
    after = exercise_trace_validation_phase(run, changed, BASELINE_SOURCE)
    assert before.state_transformation is not None
    assert before.event_transformation is not None
    assert after.state_transformation is not None
    assert after.event_transformation is not None
    assert before.state_transformation.fidelity == "LOSSLESS"
    assert before.event_transformation.fidelity == "LOSSLESS"
    assert after.state_transformation.fidelity == "LOSSY"
    assert after.event_transformation.fidelity == "LOSSY"

def test_trace_field_mapping_count_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_TRACE
    changed = replace(base, field_mapping_count=0)
    assert base.field_mapping_count == 6
    assert changed.field_mapping_count == 0
    assert replace(changed, field_mapping_count=base.field_mapping_count) == base
    before = exercise_trace_validation_phase(run, base, BASELINE_SOURCE)
    after = exercise_trace_validation_phase(run, changed, BASELINE_SOURCE)
    assert after.state_transformation is not None
    assert after.event_transformation is not None
    assert len(before.mapping_source_paths) == 9
    assert after.mapping_source_paths == ()
    assert after.state_transformation.field_mappings == ()
    assert after.event_transformation.field_mappings == ()

def test_trace_external_source_terminated_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_TRACE
    changed = replace(base, external_source_terminated=False)
    assert base.external_source_terminated is True
    assert changed.external_source_terminated is False
    assert replace(changed, external_source_terminated=base.external_source_terminated) == base
    before = exercise_trace_validation_phase(run, base, BASELINE_SOURCE)
    after = exercise_trace_validation_phase(run, changed, BASELINE_SOURCE)
    assert before.terminal_edge_count > 0
    assert after.terminal_edge_count == 0

def test_trace_card_runtime_status_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_TRACE
    changed = replace(base, card_runtime_status="IMPLEMENTED")
    assert base.card_runtime_status == "REFERENCE_ONLY_NOT_IMPLEMENTATION_PROOF"
    assert changed.card_runtime_status == "IMPLEMENTED"
    assert replace(changed, card_runtime_status=base.card_runtime_status) == base
    before = exercise_trace_validation_phase(run, base, BASELINE_SOURCE)
    after = exercise_trace_validation_phase(run, changed, BASELINE_SOURCE)
    assert before.input_statement_set is not None
    assert after.input_statement_set is not None
    assert len(before.input_statement_set.statements) >= 1
    assert len(after.input_statement_set.statements) >= 1
    before_statement = before.input_statement_set.statements[0]
    after_statement = after.input_statement_set.statements[0]
    assert len(before_statement.card_identity_refs) >= 1
    assert len(after_statement.card_identity_refs) >= 1
    assert before_statement.card_identity_refs[0].runtime_capability_status != after_statement.card_identity_refs[0].runtime_capability_status

def test_trace_statement_text_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_TRACE
    changed = replace(base, statement_text="drifted statement")
    assert base.statement_text != "drifted statement"
    assert changed.statement_text == "drifted statement"
    assert replace(changed, statement_text=base.statement_text) == base
    before = exercise_trace_validation_phase(run, base, BASELINE_SOURCE)
    after = exercise_trace_validation_phase(run, changed, BASELINE_SOURCE)
    assert before.input_statement_set is not None
    assert after.input_statement_set is not None
    assert len(before.input_statement_set.statements) >= 1
    assert len(after.input_statement_set.statements) >= 1
    assert before.input_statement_set.statements[0].statement_text != after.input_statement_set.statements[0].statement_text
    assert after.input_statement_set.statements[0].statement_text == "drifted statement"

def test_trace_issue_propagation_ids_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_TRACE
    changed = replace(base, issue_propagation_ids=("ISSUE-F09-DRIFT",))
    assert base.issue_propagation_ids == ()
    assert changed.issue_propagation_ids == ("ISSUE-F09-DRIFT",)
    assert replace(changed, issue_propagation_ids=base.issue_propagation_ids) == base
    before = exercise_trace_validation_phase(run, base, BASELINE_SOURCE)
    after = exercise_trace_validation_phase(run, changed, BASELINE_SOURCE)
    assert before.input_trace is not None
    assert after.input_trace is not None
    assert before.input_statement_set is not None
    assert after.input_statement_set is not None
    assert before.input_trace.blocking_issue_ids == ()
    assert after.input_trace.blocking_issue_ids == ("ISSUE-F09-DRIFT",)
    assert after.input_statement_set.issue_ids == ("ISSUE-F09-DRIFT",)

# artifact: 10 literal definitions
def test_artifact_records_write_outcome_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_ARTIFACTS
    changed = replace(base, records_write_outcome="FAILED")
    assert base.records_write_outcome == "SUCCEEDED"
    assert changed.records_write_outcome == "FAILED"
    assert replace(changed, records_write_outcome=base.records_write_outcome) == base
    before = exercise_artifact_lifecycle_phase(run, base, tmp_path / "before")
    after = exercise_artifact_lifecycle_phase(run, changed, tmp_path / "after")
    assert before.fail_after is None
    assert after.fail_after == "STATEMENT_RECORDS"

def test_artifact_index_write_outcome_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_ARTIFACTS
    changed = replace(base, index_write_outcome="FAILED")
    assert base.index_write_outcome == "SUCCEEDED"
    assert changed.index_write_outcome == "FAILED"
    assert replace(changed, index_write_outcome=base.index_write_outcome) == base
    before = exercise_artifact_lifecycle_phase(run, base, tmp_path / "before")
    after = exercise_artifact_lifecycle_phase(run, changed, tmp_path / "after")
    assert before.fail_after is None
    assert after.fail_after == "STATEMENT_INDEX"

def test_artifact_index_revision_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_ARTIFACTS
    changed = replace(base, index_revision="STMT-REV-1")
    assert base.index_revision == "STMT-REV-2"
    assert changed.index_revision == "STMT-REV-1"
    assert replace(changed, index_revision=base.index_revision) == base
    before = exercise_artifact_lifecycle_phase(run, base, tmp_path / "before")
    after = exercise_artifact_lifecycle_phase(run, changed, tmp_path / "after")
    assert before.inspection_input is not None
    assert after.inspection_input is not None
    assert len(before.inspection_input.records) >= 2
    assert len(after.inspection_input.records) >= 2
    assert before.inspection_input.records[1].schema_version != after.inspection_input.records[1].schema_version
    assert after.inspection_input.records[1].schema_version == "STMT-REV-1"

def test_artifact_expected_digest_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_ARTIFACTS
    changed = replace(base, expected_digest="DG-EXPECTED-DRIFT")
    assert base.expected_digest == "DG-ARTIFACT-V2"
    assert changed.expected_digest == "DG-EXPECTED-DRIFT"
    assert replace(changed, expected_digest=base.expected_digest) == base
    before = exercise_artifact_lifecycle_phase(run, base, tmp_path / "before")
    after = exercise_artifact_lifecycle_phase(run, changed, tmp_path / "after")
    assert before.inspection_input is not None
    assert after.inspection_input is not None
    assert len(before.inspection_input.records) >= 1
    assert len(after.inspection_input.records) >= 1
    assert len(after.projection_digests) >= 1
    assert before.inspection_input.records[0].expected_digest != after.inspection_input.records[0].expected_digest
    assert after.projection_digests[0] == sha256(
        changed.retry_report_payload
    ).hexdigest()

def test_artifact_observed_digest_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_ARTIFACTS
    changed = replace(base, observed_digest="DG-OBSERVED-DRIFT")
    assert base.observed_digest == "DG-ARTIFACT-V2"
    assert changed.observed_digest == "DG-OBSERVED-DRIFT"
    assert replace(changed, observed_digest=base.observed_digest) == base
    before = exercise_artifact_lifecycle_phase(run, base, tmp_path / "before")
    after = exercise_artifact_lifecycle_phase(run, changed, tmp_path / "after")
    assert before.inspection_input is not None
    assert after.inspection_input is not None
    assert len(before.inspection_input.records) >= 1
    assert len(after.inspection_input.records) >= 1
    assert before.inspection_input.records[0].observed_digest != after.inspection_input.records[0].observed_digest

def test_artifact_item_states_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_ARTIFACTS
    changed = replace(base, item_states=("MISMATCH",))
    assert base.item_states == ("VERIFIED",)
    assert changed.item_states == ("MISMATCH",)
    assert replace(changed, item_states=base.item_states) == base
    before = exercise_artifact_lifecycle_phase(run, base, tmp_path / "before")
    after = exercise_artifact_lifecycle_phase(run, changed, tmp_path / "after")
    assert before.inspection_input is not None
    assert after.inspection_input is not None
    assert len(before.inspection_input.records) >= 1
    assert len(after.inspection_input.records) >= 1
    assert before.inspection_input.records[0].state == "VERIFIED"
    assert after.inspection_input.records[0].state == "MISMATCH"

def test_artifact_statement_revision_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_ARTIFACTS
    changed = replace(base, statement_revision="STMT-REV-1")
    assert base.statement_revision == "STMT-REV-2"
    assert changed.statement_revision == "STMT-REV-1"
    assert replace(changed, statement_revision=base.statement_revision) == base
    before = exercise_artifact_lifecycle_phase(run, base, tmp_path / "before")
    after = exercise_artifact_lifecycle_phase(run, changed, tmp_path / "after")
    assert before.key is not None
    assert after.key is not None
    assert after.inspection_input is not None
    assert len(after.inspection_input.records) >= 1
    assert before.key.schema_versions_digest != after.key.schema_versions_digest
    assert after.inspection_input.records[0].schema_version == "STMT-REV-1"

def test_artifact_supersedes_revision_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_ARTIFACTS
    changed = replace(base, supersedes_revision="STMT-REV-1")
    assert base.supersedes_revision is None
    assert changed.supersedes_revision == "STMT-REV-1"
    assert replace(changed, supersedes_revision=base.supersedes_revision) == base
    before = exercise_artifact_lifecycle_phase(run, base, tmp_path / "before")
    after = exercise_artifact_lifecycle_phase(run, changed, tmp_path / "after")
    assert before.inspection_input is not None
    assert after.inspection_input is not None
    assert len(before.inspection_input.records) == 2
    assert len(after.inspection_input.records) == 2
    before_record_1 = before.inspection_input.records[0]
    before_record_2 = before.inspection_input.records[1]
    old_record = after.inspection_input.records[0]
    current_record = after.inspection_input.records[1]
    assert before_record_1.state == "VERIFIED"
    assert before_record_2.state == "VERIFIED"
    assert before_record_1.artifact_id not in (old_record.artifact_id, current_record.artifact_id)
    assert before_record_2.artifact_id not in (old_record.artifact_id, current_record.artifact_id)
    assert after.inspection_input.records == (old_record, current_record)
    assert old_record.artifact_id == "ART-F09-OLD-STMT-REV-1"
    assert old_record.state == "SUPERSEDED"
    assert current_record.artifact_id == "ART-F09-CURRENT-STMT-REV-2"
    assert current_record.state == "VERIFIED"
    assert old_record.path_locator != current_record.path_locator
    assert old_record.schema_version != current_record.schema_version
    assert old_record.statement_set_id != current_record.statement_set_id
    assert old_record.state != "VERIFIED"
    assert current_record.state != "SUPERSEDED"
    assert after.inspected_manifest is not None
    assert after.retry_manifest is None
    assert len(after.inspected_manifest.records) == 2
    assert tuple((issue.code, issue.path) for issue in after.issues) == (
        ("ARTIFACT.STATE_INVALID", "/artifacts/0/attempts/0/input_snapshot_refs"),
    )
    inspected_old = after.inspected_manifest.records[0]
    inspected_current = after.inspected_manifest.records[1]
    assert inspected_old.artifact_id == old_record.artifact_id
    assert inspected_old.path_locator == old_record.path_locator
    assert inspected_old.state == "SUPERSEDED"
    assert inspected_current.artifact_id == current_record.artifact_id
    assert inspected_current.path_locator == current_record.path_locator
    assert inspected_current.state == "VERIFIED"

def test_artifact_retry_key_digest_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_ARTIFACTS
    changed = replace(base, retry_key_digest="IDEM-KEY-DRIFT")
    assert base.retry_key_digest == "IDEM-KEY-A"
    assert changed.retry_key_digest == "IDEM-KEY-DRIFT"
    assert replace(changed, retry_key_digest=base.retry_key_digest) == base
    before = exercise_artifact_lifecycle_phase(run, base, tmp_path / "before")
    after = exercise_artifact_lifecycle_phase(run, changed, tmp_path / "after")
    assert before.key is not None
    assert after.key is not None
    assert before.key.canonical_key_digest != after.key.canonical_key_digest
    assert before.retry_manifest is None
    assert after.retry_manifest is None
    assert tuple((issue.code, issue.path) for issue in before.issues) == (
        ("ARTIFACT.STATE_INVALID", "/artifacts/REPORT"),
    )
    assert tuple((issue.code, issue.path) for issue in after.issues) == (
        ("ARTIFACT.STATE_INVALID", "/artifacts/REPORT"),
    )
    assert before.retry_called is False
    assert after.retry_called is False

def test_artifact_retry_complete_payload_set_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_ARTIFACTS
    changed = replace(base, retry_records_payload=b"DG-PAYLOAD-DRIFT")
    assert (base.retry_report_payload, base.retry_records_payload, base.retry_index_payload) == (b"F09 staged report\n", b"DG-ARTIFACT-V2", b"STMT-REV-2")
    assert changed.retry_records_payload == b"DG-PAYLOAD-DRIFT"
    assert replace(changed, retry_records_payload=base.retry_records_payload) == base
    before = exercise_artifact_lifecycle_phase(run, base, tmp_path / "before")
    after = exercise_artifact_lifecycle_phase(run, changed, tmp_path / "after")
    assert len(before.projection_digests) == 3
    assert len(after.projection_digests) == 3
    assert before.projection_digests[1] != after.projection_digests[1]

# feedback: 11 literal definitions
def test_feedback_target_statement_id_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, target_statement_id="STMT-UNKNOWN")
    assert base.target_statement_id == "STMT-F09-1"
    assert changed.target_statement_id == "STMT-UNKNOWN"
    assert replace(changed, target_statement_id=base.target_statement_id) == base
    before = exercise_feedback_binding_phase(run, base)
    after = exercise_feedback_binding_phase(run, changed)
    assert before.submission is not None
    assert after.submission is not None
    assert len(before.submission.feedback_items) >= 1
    assert len(after.submission.feedback_items) >= 1
    assert before.submission.feedback_items[0].target_statement_id == "STMT-F09-1"
    assert after.submission.feedback_items[0].target_statement_id == "STMT-UNKNOWN"

def test_feedback_target_revision_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, target_revision="STMT-REV-1")
    assert base.target_revision == "STMT-REV-2"
    assert changed.target_revision == "STMT-REV-1"
    assert replace(changed, target_revision=base.target_revision) == base
    after = exercise_feedback_binding_phase(run, changed)
    assert after.submission is not None
    assert len(after.submission.feedback_items) >= 1
    assert after.submission.feedback_items[0].target_statement_revision_id == "STMT-REV-1"
    assert_production_feedback_material_boundary(after)

def test_feedback_anchor_status_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, anchor_status="UNMAPPED")
    assert base.anchor_status == "MAPPED"
    assert changed.anchor_status == "UNMAPPED"
    assert replace(changed, anchor_status=base.anchor_status) == base
    before = exercise_feedback_binding_phase(run, base)
    after = exercise_feedback_binding_phase(run, changed)
    assert before.submission is not None
    assert after.submission is not None
    assert before.input_manifest is not None
    assert after.input_manifest is not None
    assert len(before.input_manifest.records) >= 1
    assert before.input_manifest.records[0].artifact_role == "STATEMENT_RECORDS"
    assert after.input_manifest.records == ()
    assert before.submission.track_source_binding.state == "AVAILABLE_RESOLVED"
    assert after.submission.track_source_binding.state == "AVAILABLE_RESOLVED"

def test_feedback_seven_matches_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    mismatch = ("MISMATCH", "MISMATCH", "MISMATCH", "MISMATCH", "MISMATCH", "MISMATCH", "MISMATCH")
    changed = replace(base, source_track=RunTrack.V5_V6_PREPROD, seven_matches=mismatch)
    production_required_na = replace(base, seven_matches=("MATCH", "MATCH", "NOT_APPLICABLE", "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH"))
    preprod_allowed_na = replace(base, binding_protocol="PREPROD_RUN_TARGET", target_statement_id=None, target_revision=None, seven_matches=("MATCH", "MATCH", "MATCH", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "MATCH"))
    preprod_required_na = replace(preprod_allowed_na, seven_matches=("MATCH", "MATCH", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "MATCH"))
    assert base.binding_protocol == "PRODUCTION_STATEMENT"
    assert base.seven_matches == ("MATCH", "MATCH", "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "MATCH")
    assert changed.seven_matches == mismatch
    assert len(production_required_na.seven_matches) >= 4
    assert production_required_na.seven_matches[3] == "NOT_APPLICABLE"
    assert preprod_allowed_na.seven_matches[2:] == ("MATCH", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "MATCH")
    assert len(preprod_required_na.seven_matches) >= 3
    assert preprod_required_na.seven_matches[2] == "NOT_APPLICABLE"
    assert replace(changed, source_track=base.source_track, seven_matches=base.seven_matches) == base
    before = exercise_feedback_binding_phase(run, base)
    after = exercise_feedback_binding_phase(run, changed)
    production_required_na_observation = exercise_feedback_binding_phase(run, production_required_na)
    preprod_allowed_na_observation = exercise_feedback_binding_phase(run, preprod_allowed_na)
    preprod_required_na_observation = exercise_feedback_binding_phase(run, preprod_required_na)
    assert_production_feedback_material_boundary(before)
    assert_production_feedback_material_boundary(after)
    assert_production_feedback_material_boundary(production_required_na_observation)
    assert preprod_allowed_na_observation.operation_result is None
    assert preprod_allowed_na_observation.errors == (
        "F09ContractError:expected exact owner enum member",
    )
    assert tuple(
        (issue.code, issue.path) for issue in preprod_allowed_na_observation.issues
    ) == (("FEEDBACK.MATERIAL_INVALID", "/manifest/state"),)
    assert preprod_required_na_observation.operation_result is None
    assert preprod_required_na_observation.errors == (
        "PREPROD_TARGET_GRAPH_INVALID",
    )
    assert preprod_required_na_observation.issues == ()

def test_feedback_source_track_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, source_track=RunTrack.V5_V6_PREPROD)
    malformed_source_binding = replace(base, source_track_state="SOURCE_MISSING", source_track_reason_codes=())
    source_missing = replace(base, source_track_state="SOURCE_MISSING", source_track_reason_codes=("TRACK_SOURCE_MISSING",))
    source_unparsable = replace(base, source_track_state="UNPARSABLE", source_track_reason_codes=("TRACK_SOURCE_UNPARSABLE",))
    source_ambiguous = replace(base, source_track_state="AMBIGUOUS", source_track_reason_codes=("TRACK_SOURCE_AMBIGUOUS",))
    source_integrity_failed = replace(base, source_track_state="INTEGRITY_FAILED", source_track_reason_codes=("TRACK_SOURCE_INTEGRITY_FAILED",))
    target_missing = replace(base, target_track_state="SOURCE_MISSING", target_track_reason_codes=("TRACK_SOURCE_MISSING",))
    target_unparsable = replace(base, target_track_state="UNPARSABLE", target_track_reason_codes=("TRACK_SOURCE_UNPARSABLE",))
    target_ambiguous = replace(base, target_track_state="AMBIGUOUS", target_track_reason_codes=("TRACK_SOURCE_AMBIGUOUS",))
    target_integrity_failed = replace(base, target_track_state="INTEGRITY_FAILED", target_track_reason_codes=("TRACK_SOURCE_INTEGRITY_FAILED",))
    source_missing_unmapped = replace(source_missing, anchor_status="UNMAPPED")
    assert base.source_track == RunTrack.STAGED_L6
    assert changed.source_track == RunTrack.V5_V6_PREPROD
    assert replace(changed, source_track=base.source_track) == base
    before = exercise_feedback_binding_phase(run, base)
    after = exercise_feedback_binding_phase(run, changed)
    malformed_source_observation = exercise_feedback_binding_phase(run, malformed_source_binding)
    source_missing_observation = exercise_feedback_binding_phase(run, source_missing)
    source_unparsable_observation = exercise_feedback_binding_phase(run, source_unparsable)
    source_ambiguous_observation = exercise_feedback_binding_phase(run, source_ambiguous)
    source_integrity_observation = exercise_feedback_binding_phase(run, source_integrity_failed)
    target_missing_observation = exercise_feedback_binding_phase(run, target_missing)
    target_unparsable_observation = exercise_feedback_binding_phase(run, target_unparsable)
    target_ambiguous_observation = exercise_feedback_binding_phase(run, target_ambiguous)
    target_integrity_observation = exercise_feedback_binding_phase(run, target_integrity_failed)
    source_missing_unmapped_observation = exercise_feedback_binding_phase(run, source_missing_unmapped)
    for observation in (
        before,
        after,
        malformed_source_observation,
        source_missing_observation,
        source_unparsable_observation,
        source_ambiguous_observation,
        source_integrity_observation,
        target_missing_observation,
        target_unparsable_observation,
        target_ambiguous_observation,
        target_integrity_observation,
        source_missing_unmapped_observation,
    ):
        assert_production_feedback_material_boundary(observation)

def test_feedback_policy_version_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, prior_policy_version="policy-v2")
    assert base.prior_policy_version == "policy-v1"
    assert changed.prior_policy_version == "policy-v2"
    assert changed.policy_version == "policy-v1"
    assert replace(changed, prior_policy_version=base.prior_policy_version) == base
    after = exercise_feedback_binding_phase(run, changed)
    assert_production_feedback_material_boundary(after)

def test_feedback_item_ids_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, item_ids=("FBI-DRIFT",))
    assert base.item_ids == ("FBI-1",)
    assert changed.item_ids == ("FBI-DRIFT",)
    assert replace(changed, item_ids=base.item_ids) == base
    after = exercise_feedback_binding_phase(run, changed)
    assert after.submission is not None
    assert len(after.submission.feedback_items) >= 1
    assert after.submission.feedback_items[0].feedback_item_id == "FBI-DRIFT"
    assert_production_feedback_material_boundary(after)

def test_feedback_target_graph_relation_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, target_graph_relation="CHANGED")
    assert base.target_graph_relation == "SAME"
    assert changed.target_graph_relation == "CHANGED"
    assert replace(changed, target_graph_relation=base.target_graph_relation) == base
    observation = exercise_feedback_binding_phase(run, changed)
    assert_production_feedback_material_boundary(observation)


def test_feedback_source_digest_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, source_digest="DG-FEEDBACK-DRIFT")
    assert base.source_digest == "DG-FEEDBACK-A"
    assert changed.source_digest == "DG-FEEDBACK-DRIFT"
    assert replace(changed, source_digest=base.source_digest) == base
    before = exercise_feedback_binding_phase(run, base)
    after = exercise_feedback_binding_phase(run, changed)
    assert before.submission is not None
    assert after.submission is not None
    assert before.submission.content_digest == after.submission.content_digest
    assert before.submission.source_snapshot_ref.content_digest != after.submission.source_snapshot_ref.content_digest
    assert before.submission.track_source_binding.content_digest == after.submission.track_source_binding.content_digest
    assert before.submission.track_source_binding.content_digest.algorithm == "sha256"
    assert after.submission.track_source_binding.content_digest.algorithm == "sha256"

def test_feedback_submission_complete_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, submission_complete=False)
    assert base.submission_complete is True
    assert changed.submission_complete is False
    assert replace(changed, submission_complete=base.submission_complete) == base
    before = exercise_feedback_binding_phase(run, base)
    after = exercise_feedback_binding_phase(run, changed)
    assert before.submission is not None
    assert after.submission is not None
    assert len(after.submission.feedback_items) >= 1
    assert before.submission.feedback_id == "FB-F09-1"
    assert after.submission.feedback_id == ""
    assert after.submission.feedback_items[0].feedback_id == ""
    assert after.status == "INVALID"

def test_feedback_binding_complete_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, binding_complete=False)
    assert base.binding_complete is True
    assert changed.binding_complete is False
    assert replace(changed, binding_complete=base.binding_complete) == base
    before = exercise_feedback_binding_phase(run, base)
    after = exercise_feedback_binding_phase(run, changed)
    assert_production_feedback_material_boundary(before)
    assert_production_feedback_material_boundary(after)
    assert after.submission == before.submission
    assert after.input_statement_set == before.input_statement_set
    assert after.input_manifest == before.input_manifest

def test_feedback_eligibility_complete_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, eligibility_complete=False)
    assert base.eligibility_complete is True
    assert changed.eligibility_complete is False
    assert replace(changed, eligibility_complete=base.eligibility_complete) == base
    before = exercise_feedback_binding_phase(run, base)
    after = exercise_feedback_binding_phase(run, changed)
    assert_production_feedback_material_boundary(before)
    assert_production_feedback_material_boundary(after)
    assert after.submission == before.submission
    assert after.bindings == before.bindings
