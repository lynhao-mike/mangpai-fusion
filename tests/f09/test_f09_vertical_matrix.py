from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import pytest

from engine.f09.contracts import ArtifactSetState, DecisionAction, DigestRef, RunTrack
from tests.f09.conftest import ScenarioExecution, VerticalScenario, execute_scenario
from tests.f09.data.f09_vertical_scenarios import SCENARIOS


def assert_action_and_state(
    execution: ScenarioExecution,
    expected_action: DecisionAction | None,
    expected_gate_or_state: str,
) -> None:
    run = execution.run_result
    decision = run.decision
    trace = execution.trace_phase
    artifact = execution.artifact_phase
    feedback = execution.feedback_phase
    if expected_action is not None:
        assert decision is not None
        assert decision.action_envelope.selected_action is expected_action
    match expected_gate_or_state:
        case "OUTPUT":
            assert decision is not None and decision.action_envelope.selected_action is DecisionAction.OUTPUT
        case "CONDITIONAL":
            assert decision is not None and decision.action_envelope.selected_action is DecisionAction.CONDITIONAL
        case "ASK":
            assert decision is not None and decision.action_envelope.selected_action is DecisionAction.ASK
        case "ABSTAIN":
            assert decision is not None and decision.action_envelope.selected_action is DecisionAction.ABSTAIN
        case "HUMAN_REVIEW":
            assert decision is not None and decision.action_envelope.selected_action is DecisionAction.HUMAN_REVIEW
        case "RESOLVED":
            assert execution.decision_inputs.gate_inputs[0].declarations.precision_presence == "RESOLVED"
        case "BOTH_NULL_AND_UNRESOLVED":
            declarations = execution.decision_inputs.gate_inputs[0].declarations
            assert (declarations.precision_presence, declarations.precision_value, declarations.precision_unresolved) == ("RESOLVED", None, True)
        case "ABSENT_INVALID":
            assert execution.decision_inputs.gate_inputs[0].declarations.precision_presence == "ABSENT"
            assert execution.overall_status == "INVALID"
        case "ABSENT_INPUT_LOCAL":
            assert execution.decision_inputs.gate_inputs[0].declarations.precision_presence == "ABSENT"
            assert decision is not None
            assert decision.action_envelope.structural_validity == "VALID"
        case "UNRESOLVABLE":
            declarations = execution.decision_inputs.gate_inputs[0].declarations
            assert declarations.attempted_digest is not None and declarations.attempted_digest != declarations.precision_digest
        case "NOT_APPLICABLE_INPUT_LOCAL":
            declarations = execution.decision_inputs.gate_inputs[0].declarations
            assert declarations.precision_presence == "NOT_APPLICABLE"
            assert decision is not None
            assert decision.action_envelope.structural_validity == "VALID"
        case "SOURCE_TRACK_INPUT_LOCAL":
            source = execution.decision_inputs.gate_inputs[0].source
            assert source.reality_track in (
                "CHART_STRUCTURE",
                "UNVERIFIED_HYPOTHESIS",
            )
            assert decision is not None
            assert decision.action_envelope.structural_validity == "VALID"
            assert trace.status == "INVALID"
        case "COMPETITION_READY_INPUT_LOCAL":
            assert decision is not None
            assert len(decision.competition_sets) == 1
            assert decision.competition_sets[0].structural_state == "READY"
        case "VALID":
            assert decision is not None and decision.action_envelope.structural_validity == "VALID"
        case "INVALID":
            assert execution.overall_status == "INVALID"
        case "READY":
            assert decision is not None and len(decision.participation_sets) == 1
            assert decision.participation_sets[0].structural_state == "READY"
        case "CONSUMABLE":
            assert decision is not None and decision.consumption_check.consumable is True
        case "BLOCKED_CONTRACT_MISMATCH":
            assert decision is not None and decision.consumption_check.consumable is False
            assert "CONTRACT.CARDINALITY_MISMATCH" in decision.consumption_check.blocking_issue_ids
        case "CONFLICT_UNRESOLVED":
            assert decision is not None and len(decision.competition_sets) == 1
            assert decision.competition_sets[0].structural_state == "DISPUTED"
        case "GATE_MISSING":
            assert decision is not None and len(decision.gate_sets) == 1
            assert any(record.state == "MISSING" for record in decision.gate_sets[0].records)
        case "CONSEQUENCE_INPUT_LOCAL":
            assert execution.decision_inputs.competition_input.decision.consequence_only is True
            assert decision is not None
            assert decision.action_envelope.structural_validity == "VALID"
        case "ROOT_TIMING_INPUT_LOCAL":
            root_timing = execution.decision_inputs.root_input.root_timing
            assert root_timing.root_reason_code == "ROOT_TIMING.REWRITE_INVALID"
            assert root_timing.timing_rewrites_root is False
            assert decision is not None
            assert decision.action_envelope.structural_validity == "VALID"
        case "INVALID_GATE":
            assert decision is not None and len(decision.gate_sets) == 1
            assert decision.gate_sets[0].issue_ids != ()
        case "LIMITED_ALLOCATION":
            gate = execution.decision_inputs.gate_inputs[0].gate
            assert (gate.allocation_state, gate.risk_state) == ("SATISFIED", "UNKNOWN")
        case "LIMITED_RISK":
            gate = execution.decision_inputs.gate_inputs[0].gate
            assert (gate.allocation_state, gate.risk_state) == ("UNKNOWN", "SATISFIED")
        case "DUAL_AXIS_AVAILABLE":
            gate = execution.decision_inputs.gate_inputs[0].gate
            assert (gate.allocation_state, gate.risk_state) == ("SATISFIED", "SATISFIED")
        case "VALID_ONLY_REGISTERED":
            gate = execution.decision_inputs.gate_inputs[0].gate
            assert (gate.risk_state, gate.risk_reason_codes) == (
                "UNKNOWN",
                ("ISSUE-RISK-UNKNOWN",),
            )
            assert (gate.allocation_state, gate.allocation_reason_codes) == (
                "UNKNOWN",
                ("UNREGISTERED-UNKNOWN-REASON",),
            )
            assert decision is not None
            assert "ISSUE-RISK-UNKNOWN" in decision.action_envelope.reason_codes
            assert "UNREGISTERED-UNKNOWN-REASON" in decision.action_envelope.validation_errors
        case "SAFE_ACTION":
            assert decision is not None and decision.action_envelope.selected_action is not DecisionAction.OUTPUT
        case "BLOCKING":
            assert execution.overall_status == "INVALID"
        case "STATEMENT_INVALID":
            assert trace.status == "INVALID"
            assert trace.errors != ()
        case "TRACE_STATEMENT_INVALID":
            assert trace.status == "INVALID"
            assert trace.errors != ()
        case "TRACE_ISSUE_INVALID":
            assert trace.status == "INVALID"
            assert trace.errors == ()
            assert trace.issues != ()
        case "VALID_PROJECTION":
            assert trace.status == "VALID" and trace.state_transformation is not None and trace.event_transformation is not None
        case "INVALID_PROJECTION":
            assert trace.status == "INVALID" and trace.errors != ()
        case "INVALID_LOSSLESS_SOURCE":
            assert trace.status == "INVALID"
            assert trace.mapping_source_paths == ()
        case "INVALID_LOSSLESS_EDGE":
            assert trace.status == "INVALID"
            assert trace.terminal_edge_count == 0
        case "INVALID_TRANSFORMATION":
            assert trace.state_transformation is not None and trace.state_transformation.fidelity == "UNSUPPORTED"
        case "INVALID_DESIGN":
            assert execution.decision_inputs.gate_inputs[0].source.canonical_nested_binding is False
        case "INCOMPLETE":
            assert len(execution.decision_inputs.gate_inputs[0].source.outcome_fields) != 4
        case "PROHIBITED_OUTPUT":
            assert trace.input_statement_set is not None and len(trace.input_statement_set.statements) == 1
            assert trace.input_statement_set.statements[0].statement_text == execution.mutated_bundle.trace.statement_text
            assert trace.errors != ()
        case "VALID_IFF_PRESERVED":
            assert decision is not None and trace.input_statement_set is not None and len(trace.input_statement_set.statements) == 1
            assert decision.action_envelope.nonblocking_issue_ids == trace.input_statement_set.statements[0].issue_ids
        case "LOSSY":
            assert trace.event_transformation is not None and trace.event_transformation.fidelity == "LOSSY"
        case "PARTIAL_RECORDS_WRITE_FAILED":
            assert artifact.write_called is True
            assert artifact.fail_after == "STATEMENT_RECORDS"
            assert artifact.status == "INVALID"
        case "PARTIAL_INDEX_WRITE_FAILED":
            assert artifact.write_called is True
            assert artifact.fail_after == "STATEMENT_INDEX"
            assert artifact.status == "INVALID"
        case "STALE_MIXED_REVISION":
            assert artifact.inspected_manifest is not None
            assert artifact.inspected_manifest.state is ArtifactSetState.STALE_MIXED_REVISION
        case "DIGEST_MISMATCH":
            assert artifact.inspected_manifest is not None
            assert artifact.inspected_manifest.state is ArtifactSetState.DIGEST_MISMATCH
        case "ARTIFACT_PHASE_INVALID":
            assert artifact.status == "INVALID"
            assert artifact.inspected_manifest is None
            assert artifact.issues != ()
        case "FEEDBACK_PHASE_INVALID":
            assert feedback.status == "INVALID"
            assert feedback.bindings == ()
            assert feedback.issues != ()
        case "FEEDBACK_NOT_RUNNABLE":
            assert feedback.status == "NOT_RUNNABLE"
            assert feedback.runnable is False
            assert feedback.bindings == ()
            assert feedback.eligibility_records == ()
            assert feedback.operation_result is None
        case "NO_OP_SUCCESS":
            assert artifact.write_manifest is not None and artifact.retry_manifest is not None
            assert artifact.write_manifest.digest == artifact.retry_manifest.digest
        case "CONFLICT":
            assert artifact.retry_manifest is None and artifact.errors != ()
        case "STALE_SET_NOT_READY":
            assert artifact.inspected_manifest is not None and any(record.state == "STALE" for record in artifact.inspected_manifest.records)
            assert artifact.inspected_manifest.state != "COMPLETE_VERIFIED"
        case "MISMATCH_SET_NOT_READY":
            assert artifact.inspected_manifest is not None and any(record.state == "MISMATCH" for record in artifact.inspected_manifest.records)
            assert artifact.inspected_manifest.state != "COMPLETE_VERIFIED"
        case "SUPERSEDED":
            assert artifact.inspection_input is not None and len(artifact.inspection_input.records) == 2
            assert artifact.inspection_input.records[0].state == "SUPERSEDED"
        case "UNBOUND_INELIGIBLE":
            assert len(feedback.bindings) == 1 and feedback.bindings[0].status == "UNBOUND"
            assert len(feedback.eligibility_records) == 1 and feedback.eligibility_records[0].status == "INELIGIBLE"
        case "INVALID_INELIGIBLE":
            assert len(feedback.bindings) == 1 and feedback.bindings[0].status == "INVALID"
            assert len(feedback.eligibility_records) == 1 and feedback.eligibility_records[0].status == "INELIGIBLE"
        case "INVALID_AUDIT_ONLY":
            assert len(feedback.bindings) == 1
            assert feedback.bindings[0].track_match == "MISMATCH"
            assert len(feedback.eligibility_records) == 1
            assert feedback.eligibility_records[0].status != "ELIGIBLE"
        case "BOUND":
            assert len(feedback.bindings) == 1
            assert feedback.bindings[0].status == "BOUND"
        case "ELIGIBLE":
            assert len(feedback.eligibility_records) == 1
            assert feedback.eligibility_records[0].status == "ELIGIBLE"
        case "REVISION_KEY_CHANGED":
            assert feedback.submission is not None
            assert len(feedback.submission.feedback_items) == 1
            assert feedback.submission.feedback_items[0].target_statement_revision_id == "STMT-REV-3"
        case "POLICY_KEY_CHANGED":
            assert len(feedback.eligibility_records) == 1
            assert feedback.eligibility_records[0].policy_id == "PRODUCTION-STATEMENT-ELIGIBILITY"
            assert feedback.eligibility_records[0].policy_version == "policy-v1"
            assert feedback.operation_result is not None
            assert feedback.operation_result.operation_disposition == "NEW_OPERATION"
        case "ITEM_SET_KEY_CHANGED":
            assert feedback.submission is not None
            assert len(feedback.submission.feedback_items) == 2
            assert tuple(item.feedback_item_id for item in feedback.submission.feedback_items) == ("FBI-1", "FBI-2")
        case "NEW_OPERATION_CHANGED_SOURCE":
            assert feedback.submission is not None
            baseline_digest = DigestRef(
                "sha256",
                "RFC8785-JCS-UTF8",
                sha256(
                    execution.baseline_bundle.feedback.source_digest.encode("utf-8")
                ).hexdigest(),
            )
            assert (
                feedback.submission.source_snapshot_ref.content_digest
                != baseline_digest
            )
            # The feedback adapter already asserts the producer-owned operation receipt;
            # source-snapshot and whole-submission digests are distinct identities and
            # are deliberately not compared here.
        case "SEMANTICS_UNCHANGED":
            assert decision is not None
            assert execution.mutated_bundle.gate != execution.baseline_bundle.gate
            assert tuple(record.declared_member_id for record in decision.gate_sets[0].records) == execution.baseline_bundle.gate.declared_member_ids
        case _:
            raise AssertionError("unknown expected_gate_or_state token: " + expected_gate_or_state)


# PhaseIssueObservation is owned by the sole conftest block and is populated only by
# the three adapters' actual validator/coordinator detection branches. The matrix
# module deliberately defines no phase scanner and performs no fixture re-judgment.


def assert_issue(
    execution: ScenarioExecution,
    expected_issue_code: str | None,
    expected_issue_path: str | None,
) -> None:
    run = execution.run_result
    decision_issue_pairs = tuple(
        (code, issue.field_path)
        for issue in (() if run.decision is None else run.decision.issues)
        for code in (issue.issue_id,) + issue.reason_codes
    )
    phase_issue_pairs = tuple(
        (issue.code, issue.path)
        for issue in (
            execution.trace_phase.issues
            + execution.artifact_phase.issues
            + execution.feedback_phase.issues
        )
    )
    action_issue_codes = () if run.decision is None else (
        run.decision.action_envelope.blocking_issue_ids
        + run.decision.action_envelope.nonblocking_issue_ids
        + run.decision.action_envelope.reason_codes
        + run.decision.action_envelope.validation_errors
    )
    trace_issue_codes = () if run.trace is None else run.trace.blocking_issue_ids
    statement_issue_codes = () if run.statement_set is None else (
        run.statement_set.issue_ids
        + tuple(code for statement in run.statement_set.statements for code in statement.issue_ids)
    )
    artifact_issue_codes = () if run.manifest is None else tuple(
        code for record in run.manifest.records for code in record.issue_ids
    )
    feedback_issue_codes = tuple(
        code for binding in execution.feedback_phase.bindings for code in binding.issue_ids
    ) + tuple(
        code
        for record in execution.feedback_phase.eligibility_records
        for code in record.blocking_reason_codes
    )
    phase_errors = execution.trace_phase.errors + execution.artifact_phase.errors + execution.feedback_phase.errors
    if expected_issue_code is None:
        assert expected_issue_path is None
        assert all(observation.issue_codes == () for observation in run.observations)
        if run.decision is not None:
            assert run.decision.issues == ()
            assert run.decision.action_envelope.blocking_issue_ids == ()
            assert run.decision.action_envelope.nonblocking_issue_ids == ()
            assert run.decision.action_envelope.reason_codes == ()
            assert run.decision.action_envelope.validation_errors == ()
        if run.trace is not None:
            assert run.trace.blocking_issue_ids == ()
        if run.statement_set is not None:
            assert run.statement_set.issue_ids == ()
            assert all(statement.issue_ids == () for statement in run.statement_set.statements)
        if run.manifest is not None:
            assert all(record.issue_ids == () for record in run.manifest.records)
        assert all(binding.issue_ids == () for binding in execution.feedback_phase.bindings)
        assert all(record.blocking_reason_codes == () for record in execution.feedback_phase.eligibility_records)
        assert phase_issue_pairs == ()
        assert phase_errors == ()
    else:
        assert expected_issue_path is not None
        # A positive pair must be emitted by one typed surface: either one
        # canonical DecisionIssue or one adapter-owned PhaseIssueObservation.
        # Code-only surfaces, exception text, fixture stimulus and baseline diffs
        # never supply a path and cannot be cross-joined with another surface.
        assert (expected_issue_code, expected_issue_path) in (
            decision_issue_pairs + phase_issue_pairs
        )
        if expected_issue_path == "/gate/*/reason_codes":
            # T102 retains an additional stimulus check, but this check cannot
            # replace the same-surface typed-pair assertion above.
            gate = execution.mutated_bundle.gate
            assert expected_issue_code == "GATE.STATE_UNKNOWN"
            assert gate.risk_reason_codes == ("ISSUE-RISK-UNKNOWN",)
            assert gate.allocation_reason_codes == ("UNREGISTERED-UNKNOWN-REASON",)
            assert execution.overall_status == "INVALID"


def assert_basis(execution: ScenarioExecution, expected_assertions: tuple[str, ...]) -> None:
    decision_input = execution.mutated_bundle.decision
    decision = execution.run_result.decision
    action_basis_ids = () if decision is None else decision.action_envelope.basis_record_ids
    statement_basis_ids = (
        ()
        if execution.trace_phase.input_statement_set is None
        else execution.trace_phase.input_statement_set.statements[0].basis_record_ids
    )
    gate_input = execution.mutated_bundle.gate
    participation_input = execution.mutated_bundle.participation
    root_timing_input = execution.mutated_bundle.root_timing
    source_input = execution.mutated_bundle.source
    trace_input = execution.mutated_bundle.trace
    artifact_input = execution.mutated_bundle.artifacts
    feedback_input = execution.mutated_bundle.feedback
    for token in expected_assertions:
        match token:
            case "nonempty":
                assert action_basis_ids == ("GR-ALLOCATION", "GR-RISK", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL", "PR-REALITY-OUTPUT", "DISP-F09-INCLUDED")
            case "exact_local_records":
                assert action_basis_ids == ("GR-ALLOCATION", "GR-RISK", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL", "PR-REALITY-OUTPUT", "DISP-F09-INCLUDED")
            case "condition_refs":
                assert decision_input.payload_issue_ids == ("ISSUE-RISK-UNKNOWN",)
            case "six_gates":
                assert action_basis_ids == ("GR-ALLOCATION", "GR-RISK", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL", "PR-REALITY-OUTPUT", "DISP-F09-INCLUDED")
            case "question_issue_path_resume":
                assert decision_input.question_paths == ("/gate/ATTRIBUTION",)
            case "both_candidate_evidence":
                assert decision_input.dispositions == ("DISP-F09-UNRESOLVED",)
            case "both_sides":
                assert gate_input.attribution_state == "CONFLICT" and decision_input.payload_issue_ids == ("GATE.FIELD_CONFLICT",)
            case "review_scope":
                assert decision_input.selected_action == "HUMAN_REVIEW" and decision_input.payload_type == "HumanReviewPayload"
            case "declaration_ref_nonempty":
                assert execution.mutated_bundle.declarations.precision_digest == "DG-PRECISION-V1"
            case "value_presence_separate":
                assert (execution.mutated_bundle.declarations.precision_value, execution.mutated_bundle.declarations.precision_unresolved) == (None, True)
            case "no_borrowed_basis":
                assert decision_input.basis_gate_ids == execution.baseline_bundle.decision.basis_gate_ids
            case "unknown_path_retained":
                assert gate_input.risk_reason_codes == ("GATE.STATE_UNKNOWN",)
            case "no_satisfied_gate_basis":
                assert source_input.locator_available is False and decision_input.basis_gate_ids == execution.baseline_bundle.decision.basis_gate_ids
            case "attempted_ref_retained":
                assert execution.mutated_bundle.declarations.attempted_digest == "DG-PRECISION-DRIFT"
            case "no_action_basis":
                assert execution.mutated_bundle.declarations.precision_presence == "NOT_APPLICABLE" and decision_input.basis_gate_ids == execution.baseline_bundle.decision.basis_gate_ids
            case "chart_refs_context_only":
                assert source_input.reality_track == "CHART_STRUCTURE"
                assert gate_input.supporting_evidence_tracks == ("REALITY_FACT",) * 6
            case "hypothesis_refs_retained":
                assert source_input.reality_track == "UNVERIFIED_HYPOTHESIS"
                assert gate_input.supporting_evidence_tracks == ("REALITY_FACT",) * 6
            case "both_evidence_sets":
                assert decision_input.dispositions == ("DISP-F09-UNRESOLVED-F08-STRONG",)
            case "consequence_excluded":
                assert decision_input.consequence_only is True
                assert gate_input == execution.baseline_bundle.gate
            case "ledgers_separate":
                assert root_timing_input.root_reason_code == "ROOT_TIMING.REWRITE_INVALID"
                assert root_timing_input.timing_rewrites_root is False
            case "declaration_refs_separate":
                declarations = execution.mutated_bundle.declarations
                assert declarations.precision_type == "VALIDATION_PLAN" and declarations.validation_type == "VALIDATION_PLAN"
                assert declarations.precision_digest != declarations.validation_digest
            case "action_basis_unchanged":
                assert decision_input.basis_gate_ids == execution.baseline_bundle.decision.basis_gate_ids
            case "one_anchor_two_dropped":
                assert trace_input.rule_ref_ids == ("RULE-F09-ANCHOR", "RULE-F09-DROPPED-1", "RULE-F09-DROPPED-2") and trace_input.transformation_fidelity == "LOSSY"
            case "input_snapshots_logged":
                assert artifact_input.records_write_outcome == "FAILED" and execution.artifact_phase.fail_after == "STATEMENT_RECORDS"
            case "prior_records_retained":
                assert artifact_input.index_write_outcome == "FAILED" and execution.artifact_phase.fail_after == "STATEMENT_INDEX"
            case "current_old_refs_visible":
                assert artifact_input.index_revision == "STMT-REV-1" and execution.artifact_phase.inspection_input is not None
            case "original_inputs_retained":
                assert len(execution.artifact_phase.projection_digests) == 3
            case "zero_learning_targets":
                assert feedback_input.target_statement_id == "STMT-UNKNOWN" and feedback_input.anchor_status == "UNMAPPED"
            case "old_target_retained":
                assert feedback_input.target_revision == "STMT-REV-1"
            case "same_snapshots":
                assert (artifact_input.retry_key_digest, artifact_input.retry_report_payload, artifact_input.retry_records_payload, artifact_input.retry_index_payload) == ("IDEM-KEY-A", b"F09 staged report\n", b"DG-ARTIFACT-V2", b"STMT-REV-2")
            case "both_attempt_refs":
                assert (artifact_input.retry_key_digest, artifact_input.retry_records_payload) == ("IDEM-KEY-A", b"DG-PAYLOAD-CONFLICT")
            case "audit_refs_only":
                assert feedback_input.source_track is RunTrack.V5_V6_PREPROD and feedback_input.target_track is RunTrack.STAGED_L6
            case "card_ref_retained":
                assert trace_input.card_runtime_status == "IMPLEMENTED"
            case "f09_disposition_only":
                assert decision_input.candidate_ids == ("CAND-F09",) and decision_input.f08_runtime_objects == ()
            case "forged_object_retained":
                assert decision_input.f08_runtime_objects == ("CAND-F08", "ACTION-F08", "STMT-F08")
            case "singleton_basis_retained":
                assert decision_input.candidate_ids == ("CAND-F09",) and decision_input.require_two_candidates is True
            case "ref_nonempty":
                declarations = execution.mutated_bundle.declarations
                assert (declarations.validation_type, declarations.validation_digest, declarations.identity_complete) == ("VALIDATION_PLAN", "DG-VALIDATION-V1", True)
            case "attempted_ref_visible":
                assert execution.mutated_bundle.declarations.identity_complete is False
            case "decision_basis_stable":
                assert decision_input.basis_gate_ids == execution.baseline_bundle.decision.basis_gate_ids and execution.mutated_bundle.declarations.trace_precision_digest == "DG-PRECISION-TRACE-DRIFT"
            case "nonempty_exact_basis":
                assert decision_input.basis_gate_ids == execution.baseline_bundle.decision.basis_gate_ids and decision_input.basis_participation_ids == ("PR-REALITY-OUTPUT",)
            case "issue_refs_preserved":
                assert decision_input.payload_issue_ids == ("ISSUE-RISK-UNKNOWN",)
            case "original_refs_nonempty":
                assert decision_input.question_paths == ("/gate/ATTRIBUTION",)
            case "blocking_basis":
                assert decision_input.payload_issue_ids == ("COMPETITION.UNRESOLVED",)
            case "both_conflict_sides":
                assert decision_input.payload_issue_ids == ("GATE.FIELD_CONFLICT",)
            case "basis_retained_for_issue":
                assert decision_input.basis_gate_ids == execution.baseline_bundle.decision.basis_gate_ids and decision_input.payload_type == "OutputPayload"
            case "trace_ref_required":
                assert trace_input.statement_set_complete is False
            case "complete_basis_ids":
                assert trace_input.statement_complete is False and trace_input.statement_basis_ids == execution.baseline_bundle.trace.statement_basis_ids
            case "six_canonical_role_bindings":
                assert len(participation_input.role_ids) == 6
                assert len(participation_input.role_authority_binding_ids) == 6
                assert tuple(role for role, _ in participation_input.role_authority_binding_ids) == participation_input.role_ids
                assert len({binding_id for _, binding_id in participation_input.role_authority_binding_ids}) == 6
            case "missing_role_not_repaired":
                assert len(participation_input.role_ids) == 5
                assert len(participation_input.role_authority_binding_ids) == 6
                assert "SOURCE_GATE" not in participation_input.role_ids
            case "duplicate_binding_not_repaired":
                binding_ids = tuple(binding_id for _, binding_id in participation_input.role_authority_binding_ids)
                assert len(binding_ids) == 6 and len(set(binding_ids)) == 5
            case "chart_evidence_only":
                assert (root_timing_input.root_state, root_timing_input.root_reason_code, root_timing_input.root_issue_path) == ("STRONG_ROOT", None, None)
            case "timing_evidence_local":
                assert (root_timing_input.timing_state, root_timing_input.timing_reason_code, root_timing_input.timing_issue_path) == ("ACTIVATE_EXISTING", None, None)
            case "both_ledgers_referenced":
                assert (root_timing_input.root_state, root_timing_input.root_reason_code, root_timing_input.root_issue_path) == ("UNKNOWN", None, None)
            case "item_targets_explicit":
                assert feedback_input.item_ids == ("FBI-1", "FBI-2")
            case "target_refs_explicit":
                assert feedback_input.seven_matches == ("MATCH", "MATCH", "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "MATCH")
            case "learning_excluded_refs_explicit":
                assert feedback_input.policy_version == "policy-v1" and feedback_input.eligibility_complete is True
            case "revised_target_input":
                assert feedback_input.target_revision == "STMT-REV-3"
            case "same_target_refs":
                assert feedback_input.prior_policy_version == "policy-v2" and feedback_input.policy_version == "policy-v1" and feedback_input.target_revision == execution.baseline_bundle.feedback.target_revision
            case "full_item_set_included":
                assert feedback_input.item_ids == ("FBI-1", "FBI-2")
            case "source_ref_retained":
                assert feedback_input.source_digest == "DG-FEEDBACK-B"
            case "three_layers_same_ordered_ids":
                assert action_basis_ids == ("GR-ALLOCATION", "GR-RISK", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL", "PR-REALITY-OUTPUT", "DISP-F09-INCLUDED")
                assert statement_basis_ids == ("GR-ALLOCATION", "GR-RISK", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL", "PR-REALITY-OUTPUT", "DISP-F09-INCLUDED", "RTC-ROOT", "RTC-TIMING")
            case "bad_id_retained":
                assert decision_input.basis_participation_ids == ("PARTICIPATION-SET-CONTAINER",)
            case "exact_candidate_basis":
                assert decision_input.candidate_ids == ("CAND-F09",) and decision_input.disposition_refs == ("DISP-F09-INCLUDED",)
            case "bad_ref_explicit":
                assert decision_input.disposition_refs == ("CAND-NOT-IN-SET",)
            case "zero_match":
                assert decision_input.dispositions == ()
                assert len(decision_input.disposition_refs) == 1
                assert decision_input.disposition_refs[0] in action_basis_ids
            case "both_records_retained":
                assert decision_input.dispositions == ("DISP-F09-INCLUDED-A", "DISP-F09-INCLUDED-B")
            case "disposition_basis_retained":
                assert decision_input.dispositions == ("DISP-F09-CONDITIONAL",) and decision_input.selected_action == "OUTPUT"
            case "condition_issues_retained":
                assert decision_input.dispositions == ("DISP-F09-CONDITIONAL",) and decision_input.selected_action == "CONDITIONAL"
            case "attempts_state_appropriate":
                assert artifact_input.item_states == ("NOT_ATTEMPTED", "WRITING", "WRITTEN_UNVERIFIED", "VERIFIED", "FAILED", "STALE", "MISMATCH", "SUPERSEDED")
            case "not_started_ref_retained":
                assert artifact_input.item_states == ("NOT_STARTED",)
            case "written_ref_retained":
                assert artifact_input.item_states == ("WRITTEN",)
            case "old_input_refs":
                assert (artifact_input.item_states, artifact_input.statement_revision) == (("STALE",), "STMT-REV-1")
            case "attempt_retained":
                assert (artifact_input.item_states, artifact_input.observed_digest) == (("MISMATCH",), "DG-ARTIFACT-MISMATCH")
            case "old_new_refs_auditable":
                assert (artifact_input.supersedes_revision, artifact_input.statement_revision) == ("STMT-REV-1", "STMT-REV-2")
            case "blocking_competition_basis":
                assert decision_input.dispositions == ("DISP-F09-UNRESOLVED",) and decision_input.selected_action == "ABSTAIN"
            case "bijection_by_member_id":
                assert gate_input.member_ids == ("ALLOCATION", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "TEMPORAL")
                assert gate_input.declared_member_ids == gate_input.member_ids
            case "no_inferred_member":
                assert gate_input.member_ids == ("ALLOCATION", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "SOURCE")
            case "bad_record_retained":
                assert len(gate_input.member_ids) == 6
                assert gate_input.member_ids[-1] == "UNKNOWN_MEMBER"
            case "six_ids_retained":
                assert len(gate_input.record_gate_definition_refs) == 6
                assert gate_input.record_gate_definition_refs[-1] == "REF-GATE-F09-V1/SOURCE"
            case "member_id_insufficient":
                assert len(gate_input.declared_member_ids) == 6
                assert gate_input.declared_member_ids[0] == "ALLOCATION@V2:DG-DRIFT"
            case "mutated_fields_visible":
                assert len(gate_input.evaluation_binding_digests) == 6
                assert gate_input.allocation_state == "CONFLICT"
                assert gate_input.evaluation_binding_digests[0] == "DG-ALLOC"
            case "member_local_basis_checked":
                assert gate_input.member_ids[:2] == ("RISK", "ALLOCATION") and gate_input.evaluation_binding_digests[:2] == ("DG-ALLOC", "DG-RISK")
            case "basis_values_unchanged":
                assert gate_input.member_ids == ("TEMPORAL", "SOURCE", "ATTRIBUTION", "REALITY", "RISK", "ALLOCATION")
                assert gate_input.evaluation_binding_digests == tuple(reversed(execution.baseline_bundle.gate.evaluation_binding_digests))
            case "risk_unknown_six_record_chain":
                assert len(gate_input.member_ids) == 6
                assert (gate_input.allocation_state, gate_input.risk_state, gate_input.risk_reason_codes) == ("SATISFIED", "UNKNOWN", ("GATE.STATE_UNKNOWN",))
            case "allocation_risk_unknown_six_record_chain":
                assert len(gate_input.member_ids) == 6
                assert (
                    gate_input.allocation_state,
                    gate_input.allocation_reason_codes,
                    gate_input.risk_state,
                    gate_input.risk_reason_codes,
                ) == (
                    "UNKNOWN",
                    ("GATE.STATE_UNKNOWN",),
                    "UNKNOWN",
                    ("GATE.STATE_UNKNOWN",),
                )
            case "allocation_unknown_six_record_chain":
                assert len(gate_input.member_ids) == 6
                assert (gate_input.allocation_state, gate_input.allocation_reason_codes, gate_input.risk_state) == ("UNKNOWN", ("GATE.STATE_UNKNOWN",), "SATISFIED")
            case "six_satisfied_records":
                assert (gate_input.allocation_state, gate_input.risk_state, gate_input.reality_state, gate_input.attribution_state, gate_input.source_state, gate_input.temporal_state) == ("SATISFIED",) * 6
            case "each_member_independent":
                assert gate_input.path_complete is False and gate_input.record_gate_definition_refs[0] == "REF-BROKEN"
            case "invalid_support_retained":
                assert gate_input.supporting_evidence_tracks == ("CHART_STRUCTURE", "UNVERIFIED_HYPOTHESIS")
            case "scenario_marker_is_input_local":
                assert participation_input.scenario_id == "SCENARIO-ASK"
                assert participation_input.role_authority_binding_ids == execution.baseline_bundle.participation.role_authority_binding_ids
            case "cross_role_binding_reuse_retained":
                assert participation_input.scenario_id == "SCENARIO-ASK"
                binding_ids = tuple(binding_id for _, binding_id in participation_input.role_authority_binding_ids)
                assert len(binding_ids) == 6 and len(set(binding_ids)) == 5
            case "three_layers_ordered_equal":
                assert execution.run_result.decision is not None
                assert action_basis_ids == execution.run_result.decision.action_envelope.basis_record_ids
                assert statement_basis_ids == execution.mutated_bundle.trace.statement_basis_ids
                assert statement_basis_ids != execution.baseline_bundle.trace.statement_basis_ids
            case "both_source_chains_reachable":
                assert source_input.source_kind == "IMMUTABLE_JSON_SNAPSHOT" and source_input.canonical_nested_binding is True
            case "three_lossless_mappings":
                assert source_input.state_fields == ("level", "position", "as_of") and execution.trace_phase.state_transformation is not None and len(execution.trace_phase.state_transformation.field_mappings) == 3
            case "six_lossless_mappings":
                assert len(source_input.event_fields) == 6 and execution.trace_phase.event_transformation is not None and len(execution.trace_phase.event_transformation.field_mappings) == 6
            case "bad_chain_explicit":
                assert (source_input.state_object_id, source_input.event_object_id) == ("SOURCE-EVENT-1", "SOURCE-STATE-1")
            case "four_lossless_mappings":
                assert source_input.outcome_fields == ("axis", "action", "object", "tense")
            case "broken_input_ref_shown":
                assert source_input.source_field_present is False
            case "envelope_payload_refs_retained":
                assert (source_input.snapshot_id, source_input.snapshot_schema_version, source_input.contract_version, source_input.content_digest, source_input.payload_digest) == ("SNAP-F09-DRIFT", "snapshot-v2", "PI300-V2", "DG-SNAPSHOT-DRIFT", "DG-PAYLOAD-DRIFT")
            case "target_requires_source_chain":
                assert trace_input.field_mapping_count == 0 and trace_input.external_source_terminated is False
            case "remaining_refs_retained":
                assert source_input.outcome_fields == ("axis", "action", "object")
            case "prose_ref_segregated":
                assert source_input.source_kind == "MARKDOWN_FREE_TEXT" and trace_input.transformation_fidelity == "LOSSLESS"
            case "source_chain_absent":
                assert source_input.state_pointer == "/metadata/state" and source_input.canonical_nested_binding is False
            case "lawful_four_field_basis":
                assert source_input.outcome_fields == ("axis", "action", "object", "tense")
                assert execution.trace_phase.input_statement_set is not None
                assert (
                    execution.trace_phase.input_statement_set.statements[0].statement_text
                    == execution.mutated_bundle.trace.statement_text
                )
            case "issue_path_retained":
                assert (gate_input.risk_reason_codes, gate_input.allocation_reason_codes) == (("ISSUE-RISK-UNKNOWN",), ("UNREGISTERED-UNKNOWN-REASON",))
            case "same_issue_basis_all_layers":
                assert decision_input.payload_issue_ids == trace_input.issue_propagation_ids == ("ISSUE-RISK-UNKNOWN",)
            case "all_attack_evidence_retained":
                assert len(gate_input.member_ids) == 6
                assert len(gate_input.record_gate_definition_refs) == 6
                assert len(gate_input.evaluation_binding_digests) == 6
                assert gate_input.member_ids[-1] == "UNKNOWN_MEMBER"
                assert gate_input.record_gate_definition_refs[-1] == "REF-GATE-F09-FORGED"
                assert gate_input.evaluation_binding_digests[-1] == "DG-FORGED"
                assert execution.mutated_bundle.declarations.precision_digest == "DG-PRECISION-FORGED"
                assert source_input.payload_digest == "DG-PAYLOAD-FORGED"
            case _:
                raise AssertionError("unknown basis_assertion token: " + token)


def assert_bindings(execution: ScenarioExecution, expected_assertions: tuple[str, ...]) -> None:
    declarations = execution.decision_inputs.gate_inputs[0].declarations
    source = execution.decision_inputs.gate_inputs[0].source
    participation = execution.decision_inputs.gate_inputs[0].participation
    decision_input = execution.decision_inputs.competition_input.decision
    gate = execution.mutated_bundle.gate
    artifact = execution.artifact_phase
    feedback = execution.feedback_phase
    for token in expected_assertions:
        match token:
            case "declarations_exact":
                assert declarations == execution.mutated_bundle.declarations
                assert (declarations.precision_presence, declarations.precision_digest) == ("RESOLVED", "DG-PRECISION-V1")
            case "risk_unknown_exact":
                assert (gate.risk_state, gate.risk_reason_codes) == ("UNKNOWN", ("ISSUE-RISK-UNKNOWN",))
            case "missing_path_bound":
                assert (gate.attribution_state, decision_input.question_paths) == ("MISSING", ("/gate/ATTRIBUTION",))
            case "conflict_refs_exact":
                assert (gate.attribution_state, decision_input.payload_issue_ids) == ("CONFLICT", ("GATE.FIELD_CONFLICT",))
            case "resolved_ref_exact":
                assert (declarations.precision_presence, declarations.precision_value, declarations.precision_digest) == ("RESOLVED", None, "DG-PRECISION-V1")
            case "resolved_ref_retained":
                assert (declarations.precision_value, declarations.precision_unresolved, declarations.precision_digest) == (None, True, "DG-PRECISION-V1")
            case "absent_reason_exact":
                assert declarations.precision_presence == "ABSENT"
            case "unknown_digest_exact":
                assert (gate.risk_state, gate.risk_reason_codes, declarations.precision_digest) == ("UNKNOWN", ("GATE.STATE_UNKNOWN",), "DG-PRECISION-V1")
            case "unavailable_issues_nonempty":
                assert source.locator_available is False
                assert source.content_digest == execution.baseline_bundle.source.content_digest
            case "unresolvable_branch_exact":
                assert (declarations.precision_presence, declarations.attempted_digest) == ("UNRESOLVABLE", "DG-PRECISION-DRIFT")
            case "not_applicable_reason_visible":
                assert declarations.precision_presence == "NOT_APPLICABLE"
            case "both_declarations_exact":
                assert (declarations.precision_digest, declarations.statement_precision_digest) == ("DG-PRECISION-V1", "DG-PRECISION-STATEMENT-DRIFT")
            case "type_id_path_exact":
                assert (declarations.precision_type, declarations.validation_type) == ("VALIDATION_PLAN", "VALIDATION_PLAN")
            case "field_path_locator_only":
                assert (declarations.validation_type, declarations.validation_digest, declarations.identity_complete) == ("VALIDATION_PLAN", "DG-VALIDATION-V1", True)
            case "resolved_identity_exact":
                assert (declarations.precision_presence, declarations.precision_unresolved, declarations.identity_complete) == ("RESOLVED", True, True)
            case "no_guessed_match":
                assert declarations.identity_complete is False
            case "both_refs_field_equal":
                assert declarations.trace_precision_digest == "DG-PRECISION-TRACE-DRIFT"
                assert declarations.precision_digest == "DG-PRECISION-V1"
            case "source_version_refs_exact":
                assert (source.snapshot_schema_version, source.contract_version) == ("reality-fact-source-snapshot.v1", "pi-300-f09-source-snapshots-v1")
            case "declarations_revision_exact":
                assert (declarations.precision_contract_version, declarations.statement_precision_digest) == ("PI210-V1", "DG-PRECISION-V1")
            case "chart_track_exact":
                assert source.reality_track == "CHART_STRUCTURE"
            case "hypothesis_track_exact":
                assert source.reality_track == "UNVERIFIED_HYPOTHESIS"
            case "source_refs_retained":
                assert source == execution.baseline_bundle.source
                assert gate == execution.baseline_bundle.gate
            case "source_refs_reachable":
                assert (source.snapshot_id, source.content_digest) == ("PI-300-F09-SOURCE-SNAPSHOT-V1", "67517fe2d04fb0fe580e031643dab2ad53fcdb8c90707ba4d496c316dd87f5e7")
            case "evidence_track_bound":
                assert (gate.reality_state, gate.supporting_evidence_tracks) == ("SATISFIED", ("CHART_STRUCTURE", "UNVERIFIED_HYPOTHESIS"))
            case "two_source_binding_branches":
                assert (source.source_kind, source.canonical_nested_binding) == ("IMMUTABLE_JSON_SNAPSHOT", True)
            case "object_root_locators_exact":
                assert (source.state_object_id, source.state_pointer, source.state_fields) == ("SOURCE-STATE-1", "/value", ("level", "position", "as_of"))
            case "same_event_identity":
                assert (source.event_object_id, source.event_pointer) == ("SOURCE-EVENT-1", "/value")
                assert len(source.event_fields) == 6
            case "object_pointer_temporal_bound":
                assert (source.state_object_id, source.event_object_id) == ("SOURCE-EVENT-1", "SOURCE-STATE-1")
            case "value_schema_null_refs_exact":
                assert source.outcome_fields == ("axis", "action", "object", "tense")
            case "no_metadata_substitute":
                assert (source.source_field_present, source.state_pointer) == (False, "/value")
            case "five_fields_payload_digest_exact":
                assert (source.snapshot_id, source.snapshot_schema_version, source.contract_version, source.content_digest, source.payload_digest) == ("SNAP-F09-DRIFT", "snapshot-v2", "PI300-V2", "DG-SNAPSHOT-DRIFT", "DG-PAYLOAD-DRIFT")
            case "versioned_refs_reachable":
                assert (source.snapshot_id, source.contract_version, execution.mutated_bundle.trace.external_source_terminated) == ("PI-300-F09-SOURCE-SNAPSHOT-V1", "pi-300-f09-source-snapshots-v1", False)
            case "missing_locator_explicit":
                assert source.outcome_fields == ("axis", "action", "object")
            case "json_source_required":
                assert source.source_kind == "MARKDOWN_FREE_TEXT"
            case "canonical_nested_binding":
                assert (source.state_pointer, source.canonical_nested_binding) == ("/metadata/state", False)
            case "lossless_refs_unchanged":
                assert source.outcome_fields == ("axis", "action", "object", "tense")
                assert source.content_digest == execution.baseline_bundle.source.content_digest
            case "f08_reference_absent":
                assert decision_input.f08_runtime_objects == ()
            case "f08_forged_objects_exact":
                assert decision_input.f08_runtime_objects == ("CAND-F08", "ACTION-F08", "STMT-F08")
            case "f08_identity_only":
                assert decision_input.dispositions == ("DISP-F09-UNRESOLVED-F08-STRONG",)
                assert decision_input.candidate_ids == ("CAND-F09",)
            case "f08_ref_reachable":
                assert (decision_input.candidate_ids, decision_input.f08_runtime_objects) == (("CAND-F09",), ())
            case "contract_ref_exact":
                assert (decision_input.candidate_ids, decision_input.require_two_candidates) == (("CAND-F09",), True)
            case "output_discriminator":
                assert (decision_input.selected_action, decision_input.payload_type) == ("OUTPUT", "OutputPayload")
            case "conditional_discriminator":
                assert (decision_input.selected_action, decision_input.payload_type) == ("CONDITIONAL", "ConditionalPayload")
            case "ask_discriminator":
                assert (decision_input.selected_action, decision_input.payload_type) == ("ASK", "AskPayload")
            case "abstain_discriminator":
                assert (decision_input.selected_action, decision_input.payload_type) == ("ABSTAIN", "AbstainPayload")
            case "review_discriminator":
                assert (decision_input.selected_action, decision_input.payload_type) == ("HUMAN_REVIEW", "HumanReviewPayload")
            case "discriminator_mismatch":
                assert (decision_input.selected_action, decision_input.payload_type) == ("ASK", "OutputPayload")
            case "unique_disposition_ref":
                assert len(decision_input.dispositions) == 1
                assert len(decision_input.disposition_refs) == 1
                assert decision_input.dispositions == decision_input.disposition_refs
            case "current_result_scope":
                assert decision_input.disposition_refs == ("CAND-NOT-IN-SET",)
            case "current_result_only":
                assert decision_input.dispositions == ()
                assert len(decision_input.disposition_refs) == 1
                assert execution.run_result.decision is not None
                assert decision_input.disposition_refs[0] in execution.run_result.decision.action_envelope.basis_record_ids
            case "uniqueness_violated":
                assert decision_input.dispositions == ("DISP-F09-INCLUDED-A", "DISP-F09-INCLUDED-B")
            case "action_mapping_exact":
                assert (decision_input.selected_action, decision_input.dispositions) == ("OUTPUT", ("DISP-F09-CONDITIONAL",))
            case "disposition_exact":
                assert (decision_input.selected_action, decision_input.dispositions, decision_input.disposition_refs) == ("ABSTAIN", ("DISP-F09-UNRESOLVED",), ("DISP-F09-UNRESOLVED",))
            case "scenario_marker_bound":
                assert participation.scenario_id == "SCENARIO-ASK"
            case "record_identity_valid":
                assert decision_input.basis_gate_ids == execution.baseline_bundle.decision.basis_gate_ids
                assert execution.mutated_bundle.trace.statement_basis_ids != execution.baseline_bundle.trace.statement_basis_ids
            case "refs_field_equal":
                assert decision_input.payload_issue_ids == execution.mutated_bundle.trace.issue_propagation_ids == ("ISSUE-RISK-UNKNOWN",)
            case "records_resolve_current_result":
                assert execution.run_result.decision is not None
                assert execution.run_result.decision.action_envelope.basis_record_ids == ("GR-ALLOCATION", "GR-RISK", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL", "PR-REALITY-OUTPUT", "DISP-F09-INCLUDED")
                assert execution.trace_phase.input_statement_set is not None
                assert execution.trace_phase.input_statement_set.statements[0].basis_record_ids == ("GR-ALLOCATION", "GR-RISK", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL", "PR-REALITY-OUTPUT", "DISP-F09-INCLUDED", "RTC-ROOT", "RTC-TIMING")
            case "no_container_coercion":
                assert decision_input.basis_participation_ids == ("PARTICIPATION-SET-CONTAINER",)
            case "ledger_refs_exact":
                assert execution.decision_inputs.root_input.root_timing == execution.mutated_bundle.root_timing
                assert execution.mutated_bundle.root_timing.root_reason_code == "ROOT_TIMING.REWRITE_INVALID"
                assert execution.mutated_bundle.root_timing.timing_rewrites_root is False
            case "root_refs_exact":
                assert (execution.decision_inputs.root_input.root_timing.root_state, execution.decision_inputs.root_input.root_timing.root_reason_code) == ("STRONG_ROOT", None)
            case "timing_refs_exact":
                assert (execution.decision_inputs.timing_input.root_timing.timing_state, execution.decision_inputs.timing_input.root_timing.timing_reason_code) == ("ACTIVATE_EXISTING", None)
            case "source_decision_exact":
                assert execution.decision_inputs.root_input.root_timing == execution.decision_inputs.timing_input.root_timing == execution.mutated_bundle.root_timing
            case "role_binding_bijection_exact":
                assert len(participation.role_ids) == len(participation.role_authority_binding_ids) == 6
                assert tuple(role for role, _ in participation.role_authority_binding_ids) == participation.role_ids
                assert len({binding_id for _, binding_id in participation.role_authority_binding_ids}) == 6
            case "missing_role_explicit":
                assert len(participation.role_ids) == 5
                assert "SOURCE_GATE" not in participation.role_ids
            case "duplicate_binding_explicit":
                binding_ids = tuple(binding_id for _, binding_id in participation.role_authority_binding_ids)
                assert len(binding_ids) == 6 and len(set(binding_ids)) == 5
            case "records_attempt_ledger_complete":
                assert artifact.write_called is True
                assert artifact.fail_after == "STATEMENT_RECORDS"
            case "index_attempt_ledger_complete":
                assert artifact.write_called is True
                assert artifact.fail_after == "STATEMENT_INDEX"
            case "revisions_exact":
                assert artifact.inspection_input is not None
                assert execution.mutated_bundle.artifacts.index_revision == "STMT-REV-1"
            case "expected_observed_separate":
                assert (execution.mutated_bundle.artifacts.expected_digest, execution.mutated_bundle.artifacts.observed_digest) == ("DG-ARTIFACT-V2", "DG-ARTIFACT-CONFLICT")
            case "same_canonical_key":
                assert artifact.key is not None
                assert execution.mutated_bundle.artifacts.retry_key_digest == "IDEM-KEY-A"
                assert execution.mutated_bundle.artifacts.retry_records_payload == b"DG-ARTIFACT-V2"
            case "retry_digest_separate":
                assert execution.mutated_bundle.artifacts.retry_records_payload == b"DG-PAYLOAD-CONFLICT"
                assert execution.mutated_bundle.artifacts.observed_digest == "DG-ARTIFACT-V2"
            case "observed_digest_separate":
                assert execution.mutated_bundle.artifacts.retry_records_payload == b"DG-ARTIFACT-V2"
                assert execution.mutated_bundle.artifacts.observed_digest == "DG-ARTIFACT-MISMATCH"
            case "exact_eight_value_enum":
                assert execution.mutated_bundle.artifacts.item_states == ("NOT_ATTEMPTED", "WRITING", "WRITTEN_UNVERIFIED", "VERIFIED", "FAILED", "STALE", "MISMATCH", "SUPERSEDED")
            case "not_started_not_coerced":
                assert execution.mutated_bundle.artifacts.item_states == ("NOT_STARTED",)
                assert artifact.errors != ()
            case "written_not_coerced":
                assert execution.mutated_bundle.artifacts.item_states == ("WRITTEN",)
                assert artifact.errors != ()
            case "item_set_states_separate":
                assert (execution.mutated_bundle.artifacts.item_states, execution.mutated_bundle.artifacts.statement_revision) == (("STALE",), "STMT-REV-1")
            case "old_identity_retained":
                assert (execution.mutated_bundle.artifacts.statement_revision, execution.mutated_bundle.artifacts.supersedes_revision) == ("STMT-REV-2", "STMT-REV-1")
            case "seven_dimensions_explicit":
                assert execution.mutated_bundle.feedback.seven_matches == ("MISMATCH",) * 7
            case "revision_mismatch":
                assert execution.mutated_bundle.feedback.target_revision == "STMT-REV-1"
            case "track_mismatch":
                assert (execution.mutated_bundle.feedback.source_track, execution.mutated_bundle.feedback.target_track) == (RunTrack.V5_V6_PREPROD, RunTrack.STAGED_L6)
            case "snapshot_parser_span_targets_integrity_exact":
                assert execution.mutated_bundle.feedback.item_ids == ("FBI-1", "FBI-2")
                assert execution.mutated_bundle.feedback.submission_complete is True
            case "seven_dimensions_exact":
                assert execution.mutated_bundle.feedback.seven_matches == ("MATCH", "MATCH", "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "MATCH")
            case "feedback_binding_id_exact":
                assert execution.mutated_bundle.feedback.policy_version == "policy-v1"
                assert execution.mutated_bundle.feedback.eligibility_complete is True
            case "revision_in_identity":
                assert execution.mutated_bundle.feedback.target_revision == "STMT-REV-3"
            case "policy_in_identity":
                assert execution.mutated_bundle.feedback.prior_policy_version == "policy-v2"
                assert execution.mutated_bundle.feedback.policy_version == "policy-v1"
            case "item_ids_canonicalized":
                assert execution.mutated_bundle.feedback.item_ids == ("FBI-1", "FBI-2")
            case "digest_in_identity":
                assert execution.mutated_bundle.feedback.source_digest == "DG-FEEDBACK-B"
            case "reference_only_literal":
                assert execution.mutated_bundle.trace.card_runtime_status == "IMPLEMENTED"
                assert decision_input.f08_runtime_objects == ()
            case "shared_whole_ref":
                assert gate.gate_definition_ref == "REF-GATE-F09-V1"
                assert gate.record_gate_definition_refs == ("REF-GATE-F09-V1",) * 6
            case "bijection_fails":
                assert gate.member_ids == ("ALLOCATION", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "SOURCE")
                assert gate.declared_member_ids == ("ALLOCATION", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "TEMPORAL")
            case "declaration_mismatch":
                assert gate.member_ids == ("ALLOCATION", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "UNKNOWN_MEMBER")
            case "whole_ref_equal":
                assert gate.gate_definition_ref == "REF-GATE-F09-V1"
                assert len(gate.record_gate_definition_refs) == 6
                assert gate.record_gate_definition_refs[-1] == "REF-GATE-F09-V1/SOURCE"
            case "version_digest_boundary":
                assert len(gate.declared_member_ids) == 6
                assert gate.declared_member_ids[0] == "ALLOCATION@V2:DG-DRIFT"
            case "both_digests_checked":
                assert len(gate.evaluation_binding_digests) == 6
                assert (gate.allocation_state, gate.evaluation_binding_digests[0]) == ("CONFLICT", "DG-ALLOC")
            case "identity_content_bound":
                assert gate.member_ids[:2] == ("RISK", "ALLOCATION")
                assert gate.evaluation_binding_digests[:2] == ("DG-ALLOC", "DG-RISK")
            case "bindings_unchanged":
                assert gate.member_ids == ("TEMPORAL", "SOURCE", "ATTRIBUTION", "REALITY", "RISK", "ALLOCATION")
                assert gate.evaluation_binding_digests == ("DG-TEMP", "DG-SOURCE", "DG-ATTR", "DG-REAL", "DG-RISK", "DG-ALLOC")
            case "risk_unknown_member_bindings_exact":
                assert (gate.allocation_state, gate.risk_state, gate.evaluation_binding_digests) == ("SATISFIED", "UNKNOWN", execution.baseline_bundle.gate.evaluation_binding_digests)
            case "allocation_risk_unknown_member_bindings_exact":
                assert (gate.allocation_state, gate.risk_state) == ("UNKNOWN", "UNKNOWN")
                assert gate.evaluation_binding_digests == execution.baseline_bundle.gate.evaluation_binding_digests
            case "allocation_unknown_member_bindings_exact":
                assert (gate.allocation_state, gate.risk_state, gate.evaluation_binding_digests) == ("UNKNOWN", "SATISFIED", execution.baseline_bundle.gate.evaluation_binding_digests)
            case "bindings_exact":
                assert gate.evaluation_binding_digests == ("DG-ALLOC", "DG-RISK", "DG-REAL", "DG-ATTR", "DG-SOURCE", "DG-TEMP")
            case "broken_ref_identified":
                assert gate.path_complete is False
                assert len(gate.record_gate_definition_refs) == 6
                assert gate.record_gate_definition_refs[0] == "REF-BROKEN"
            case "registry_code_exact":
                assert (gate.risk_reason_codes, gate.allocation_reason_codes) == (("ISSUE-RISK-UNKNOWN",), ("UNREGISTERED-UNKNOWN-REASON",))
            case "locator_gate_bindings_checked":
                assert len(gate.member_ids) == 6
                assert len(gate.evaluation_binding_digests) == 6
                assert gate.member_ids[-1] == "UNKNOWN_MEMBER"
                assert gate.evaluation_binding_digests[-1] == "DG-FORGED"
                assert source.payload_digest == "DG-PAYLOAD-FORGED"
            case _:
                raise AssertionError("unknown binding_assertion token: " + token)


def assert_side_effect_boundary(execution: ScenarioExecution, expected_assertion: str) -> None:
    run = execution.run_result
    trace = execution.trace_phase
    artifact = execution.artifact_phase
    feedback = execution.feedback_phase
    called_ports = tuple(call.port for call in execution.boundary_calls)
    called_tracks = tuple(call.track for call in execution.boundary_calls if call.track is not None)
    assert run.request.mode in ("STAGED_AUDIT", "PREPROD_SHADOW")
    assert run.request.enable_f09 is True
    match expected_assertion:
        case "staged_writes_only":
            assert artifact.write_called is True
            assert run.manifest is not None
            assert run.manifest.key.track is RunTrack.STAGED_L6
        case "staged_only":
            assert artifact.write_called is True
            assert run.manifest is not None
            assert run.manifest.key.track is RunTrack.STAGED_L6
        case "no_production_or_learning":
            assert all(call.track is not RunTrack.PRODUCTION_DEFAULT for call in execution.boundary_calls if call.track is not None)
            assert all(record.status != "ELIGIBLE" for record in feedback.eligibility_records)
        case "no_conclusion_write":
            assert run.decision is not None
            assert run.decision.action_envelope.selected_action is DecisionAction.ASK
            assert run.statement_set is not None
            assert artifact.write_called is True
            assert run.manifest is not None
            assert run.manifest.key.track is RunTrack.STAGED_L6
        case "no_formal_outcome":
            assert run.decision is not None
            assert (
                run.decision.action_envelope.selected_action
                is DecisionAction.ABSTAIN
            )
            assert run.statement_set is not None
            assert artifact.write_called is True
            assert run.manifest is not None
            assert run.manifest.key.track is RunTrack.STAGED_L6
        case "no_auto_learning":
            assert all(record.status != "ELIGIBLE" for record in feedback.eligibility_records)
        case "no_inferred_precision":
            declarations = execution.mutated_bundle.declarations
            assert (declarations.precision_presence, declarations.precision_value) == ("RESOLVED", None)
        case "no_precision_fallback":
            assert execution.mutated_bundle.declarations.precision_unresolved is True
            assert execution.mutated_bundle.declarations.precision_value is None
        case "no_output_disposition_fallback":
            assert execution.mutated_bundle.decision.selected_action == "OUTPUT"
            assert execution.mutated_bundle.decision.dispositions == ("DISP-F09-INCLUDED",)
        case "no_conditional_disposition_fallback":
            assert execution.mutated_bundle.decision.selected_action == "CONDITIONAL"
            assert execution.mutated_bundle.decision.dispositions == ("DISP-F09-CONDITIONAL",)
        case "frozen_source_unchanged":
            assert execution.decision_inputs.gate_inputs[0].source == execution.mutated_bundle.source
        case "unknown_not_action":
            assert execution.mutated_bundle.gate.risk_state == "UNKNOWN"
            assert run.decision is not None
            assert run.decision.action_envelope.selected_action is not DecisionAction.OUTPUT
            assert run.decision.action_envelope.structural_validity == "VALID"
        case "no_artifacts":
            assert trace.status == "INVALID"
            assert any(
                issue.code == "TRACE.BINDING_MISMATCH"
                and issue.path == "/trace/identity"
                for issue in trace.issues
            )
            assert run.manifest is not None
            assert artifact.write_called is True
            assert run.manifest.key.track is RunTrack.STAGED_L6
        case "no_statement":
            assert run.statement_set is None
            assert artifact.write_called is False
        case "no_promotion":
            assert run.statement_set is None
        case "no_second_card":
            assert execution.mutated_bundle.decision.f08_runtime_objects == ()
            assert execution.mutated_bundle.decision.candidate_ids == ("CAND-F09",)
        case "no_backfill":
            assert execution.mutated_bundle.decision.consequence_only is True
            assert execution.mutated_bundle.gate.allocation_state == "MISSING"
        case "no_decision_write":
            assert artifact.write_called is False
            assert execution.overall_status == "INVALID"
        case "no_guessing":
            assert execution.overall_status == "INVALID"
        case "no_publish":
            assert run.statement_set is None
        case "no_learning_ready":
            assert all(record.status != "ELIGIBLE" for record in feedback.eligibility_records)
        case "no_feedback_readiness":
            assert feedback.status != "VALID"
        case "no_rollback_overwrite":
            assert artifact.write_manifest is not None
            assert artifact.fail_after == "STATEMENT_INDEX"
            assert artifact.retry_manifest is None
        case "no_overwrite":
            assert artifact.inspected_manifest is not None
            assert artifact.inspected_manifest.state is ArtifactSetState.DIGEST_MISMATCH
            assert artifact.retry_manifest is None
        case "artifact_invalid_no_retry":
            assert artifact.status == "INVALID"
            assert artifact.inspected_manifest is None
            assert artifact.retry_manifest is None
        case "learning_calls_zero":
            assert all(record.status != "ELIGIBLE" for record in feedback.eligibility_records)
        case "no_fuzzy_match":
            assert len(feedback.bindings) == 1
            assert feedback.bindings[0].status == "INVALID"
        case "no_artifact_duplicate":
            assert artifact.retry_called is True
            assert artifact.write_manifest is not None
            assert artifact.retry_manifest is not None
            assert artifact.write_manifest.digest == artifact.retry_manifest.digest
        case "no_feedback_duplicate":
            assert feedback.submission is not None
            assert len(feedback.submission.feedback_items) == 2
            assert tuple(item.feedback_item_id for item in feedback.submission.feedback_items) == ("FBI-1", "FBI-2")
            assert len(feedback.bindings) == 2
            assert tuple(binding.feedback_item_ref.object_id for binding in feedback.bindings) == ("FBI-1", "FBI-2")
        case "no_overwrite_or_learning":
            assert artifact.retry_called is True
            assert artifact.retry_manifest is None
            assert artifact.errors != ()
            assert all(record.status != "ELIGIBLE" for record in feedback.eligibility_records)
        case "no_production_learning":
            assert all(call.track is not RunTrack.PRODUCTION_DEFAULT for call in execution.boundary_calls if call.track is not None)
            assert all(record.status != "ELIGIBLE" for record in feedback.eligibility_records)
        case "no_f08_execution":
            assert execution.mutated_bundle.decision.f08_runtime_objects == ()
            assert execution.mutated_bundle.decision.candidate_ids == ("CAND-F09",)
        case "no_silent_deletion":
            assert execution.mutated_bundle.decision.f08_runtime_objects == ("CAND-F08", "ACTION-F08", "STMT-F08")
            assert execution.overall_status == "INVALID"
        case "no_f08_repair":
            assert execution.mutated_bundle.decision.require_two_candidates is True
            assert execution.mutated_bundle.decision.candidate_ids == ("CAND-F09",)
            assert execution.run_result.decision is not None
            assert execution.run_result.decision.consumption_check.consumable is True
        case "no_identity_inference":
            assert execution.mutated_bundle.declarations.identity_complete is True
            assert execution.mutated_bundle.declarations.validation_digest == "DG-VALIDATION-V1"
        case "no_outcome_field_inference":
            assert execution.mutated_bundle.source.outcome_fields == ("axis", "action", "object")
            assert execution.trace_phase.status == "INVALID"
        case "no_precision_expansion":
            assert execution.mutated_bundle.declarations.precision_value is None
            assert execution.mutated_bundle.declarations.precision_unresolved is True
        case "no_output":
            assert artifact.write_called is False
            assert run.statement_set is None
        case "no_hidden_resolution":
            assert execution.mutated_bundle.decision.payload_issue_ids == ("ISSUE-RISK-UNKNOWN",)
        case "no_outcome":
            assert execution.mutated_bundle.decision.question_paths == ("/gate/ATTRIBUTION",)
            assert artifact.write_called is False
        case "no_output_payload":
            assert execution.mutated_bundle.decision.payload_type == "AbstainPayload"
            assert artifact.write_called is False
        case "no_priority":
            assert execution.mutated_bundle.decision.payload_type == "HumanReviewPayload"
        case "no_write":
            assert artifact.write_called is False
            assert artifact.write_manifest is None
        case "ready_not_satisfied":
            assert execution.mutated_bundle.participation.role_ids == ("ROLE-ALLOCATION", "ROLE-RISK", "ROLE-REALITY", "ROLE-ATTRIBUTION", "ROLE-SOURCE", "ROLE-TEMPORAL")
        case "no_repair":
            assert execution.overall_status == "INVALID"
        case "no_decision":
            assert artifact.write_called is False
            assert execution.overall_status == "INVALID"
        case "timing_cannot_mutate":
            assert execution.decision_inputs.root_input.root_timing == execution.decision_inputs.timing_input.root_timing
            assert execution.mutated_bundle.root_timing.timing_rewrites_root is False
        case "root_unchanged":
            assert execution.mutated_bundle.root_timing.root_state == execution.baseline_bundle.root_timing.root_state
        case "no_rewrite":
            assert execution.mutated_bundle.root_timing.timing_rewrites_root is False
        case "no_learning":
            assert all(record.status != "ELIGIBLE" for record in feedback.eligibility_records)
        case "bound_status_exact":
            assert len(feedback.bindings) == 1
            assert feedback.bindings[0].status == "BOUND"
        case "evaluation_only":
            assert "EVALUATE_LEARNING_ELIGIBILITY" in called_ports
            assert len(feedback.eligibility_records) == 1
        case "no_old_key_reuse":
            assert feedback.submission is not None
            assert len(feedback.submission.feedback_items) == 1
            assert feedback.submission.feedback_items[0].target_statement_revision_id == "STMT-REV-3"
            assert all(record.status != "ELIGIBLE" for record in feedback.eligibility_records)
        case "reevaluate_only":
            assert len(feedback.eligibility_records) == 1
            assert feedback.eligibility_records[0].policy_version == "policy-v1"
            assert feedback.operation_result is not None
            assert feedback.operation_result.operation_disposition == "NEW_OPERATION"
        case "no_last_write_wins":
            assert feedback.submission is not None
            baseline_digest = DigestRef(
                "sha256",
                "RFC8785-JCS-UTF8",
                sha256(execution.baseline_bundle.feedback.source_digest.encode("utf-8")).hexdigest(),
            )
            assert feedback.submission.source_snapshot_ref.content_digest != baseline_digest
            assert feedback.submission.content_digest != feedback.submission.source_snapshot_ref.content_digest
            assert all(record.status != "ELIGIBLE" for record in feedback.eligibility_records)
        case "no_cross_result_lookup":
            assert execution.mutated_bundle.decision.disposition_refs == ("DISP-F09-INCLUDED",)
        case "fail_closed":
            assert execution.overall_status == "INVALID"
        case "no_first_wins":
            assert execution.mutated_bundle.decision.dispositions == ("DISP-F09-INCLUDED-A", "DISP-F09-INCLUDED-B")
            assert execution.overall_status == "INVALID"
        case "no_downgrade":
            assert execution.mutated_bundle.decision.dispositions == ("DISP-F09-CONDITIONAL",)
        case "no_readiness_inference":
            assert execution.mutated_bundle.artifacts.item_states == ("NOT_ATTEMPTED", "WRITING", "WRITTEN_UNVERIFIED", "VERIFIED", "FAILED", "STALE", "MISMATCH", "SUPERSEDED")
        case "no_verified_inference":
            assert execution.mutated_bundle.artifacts.item_states == ("WRITTEN",)
            assert artifact.status == "INVALID"
        case "no_feedback":
            assert artifact.inspected_manifest is not None
            assert artifact.inspected_manifest.state != "COMPLETE_VERIFIED"
            assert feedback.bindings == ()
            assert feedback.eligibility_records == ()
        case "not_verified":
            assert artifact.inspection_input is not None
            assert len(artifact.inspection_input.records) == 2
            assert artifact.inspection_input.records[0].state == "SUPERSEDED"
        case "no_outcome_statement":
            assert execution.mutated_bundle.decision.selected_action == "ABSTAIN"
            assert run.statement_set is None
        case "order_independent":
            assert execution.mutated_bundle.gate.member_ids == execution.mutated_bundle.gate.declared_member_ids
        case "no_coercion":
            assert len(execution.mutated_bundle.gate.record_gate_definition_refs) == 6
            assert execution.mutated_bundle.gate.record_gate_definition_refs[-1] == "REF-GATE-F09-V1/SOURCE"
        case "no_stale_reuse":
            assert len(execution.mutated_bundle.gate.declared_member_ids) == 6
            assert execution.mutated_bundle.gate.declared_member_ids[0] == "ALLOCATION@V2:DG-DRIFT"
        case "no_accept":
            assert execution.mutated_bundle.gate.allocation_state == "CONFLICT"
            assert execution.overall_status == "INVALID"
        case "no_positional_repair":
            assert execution.mutated_bundle.gate.member_ids[:2] == ("RISK", "ALLOCATION")
        case "no_semantic_drift":
            assert execution.mutated_bundle.gate.member_ids == ("TEMPORAL", "SOURCE", "ATTRIBUTION", "REALITY", "RISK", "ALLOCATION")
        case "no_risk_strengthening":
            assert (execution.mutated_bundle.gate.risk_state, execution.mutated_bundle.gate.risk_reason_codes) == ("UNKNOWN", ("GATE.STATE_UNKNOWN",))
        case "no_allocation_strengthening":
            assert (execution.mutated_bundle.gate.allocation_state, execution.mutated_bundle.gate.allocation_reason_codes) == ("UNKNOWN", ("GATE.STATE_UNKNOWN",))
        case "no_priority_invented":
            assert (execution.mutated_bundle.gate.allocation_state, execution.mutated_bundle.gate.risk_state) == ("SATISFIED", "SATISFIED")
        case "no_sat_promotion":
            assert execution.mutated_bundle.gate.supporting_evidence_tracks == ("CHART_STRUCTURE", "UNVERIFIED_HYPOTHESIS")
            assert execution.overall_status == "INVALID"
        case "no_cross_scenario_reuse":
            assert execution.mutated_bundle.participation.reality_record_id == "PR-REALITY-ASK"
        case "no_masking":
            assert execution.mutated_bundle.participation.reality_record_id == "PR-REALITY-OUTPUT"
            assert execution.overall_status == "INVALID"
        case "no_yaml_or_prose_substitute":
            assert execution.mutated_bundle.source.source_kind == "IMMUTABLE_JSON_SNAPSHOT"
        case "no_synthesis":
            assert execution.trace_phase.status == "VALID"
            assert execution.mutated_bundle.source.source_kind == "IMMUTABLE_JSON_SNAPSHOT"
        case "no_interchange":
            assert execution.mutated_bundle.source.state_object_id == "SOURCE-EVENT-1"
            assert execution.mutated_bundle.source.event_object_id == "SOURCE-STATE-1"
        case "no_business_synthesis":
            assert execution.mutated_bundle.source.outcome_fields == ("axis", "action", "object", "tense")
        case "no_local_bypass":
            assert execution.trace_phase.status == "INVALID"
            assert execution.mutated_bundle.source.payload_digest == "DG-PAYLOAD-DRIFT"
        case "no_claim":
            assert execution.trace_phase.status == "INVALID"
            assert run.statement_set is None
        case "no_auto_extraction":
            assert execution.mutated_bundle.source.source_kind == "MARKDOWN_FREE_TEXT"
            assert execution.trace_phase.status == "INVALID"
        case "no_dual_write":
            assert execution.mutated_bundle.source.canonical_nested_binding is False
            assert artifact.write_called is False
        case "no_expanded_publish":
            assert run.statement_set is None
        case "unknown_code_fails":
            assert execution.mutated_bundle.gate.allocation_reason_codes == ("UNREGISTERED-UNKNOWN-REASON",)
            assert execution.overall_status == "INVALID"
        case "no_dropped_issue":
            assert execution.mutated_bundle.decision.payload_issue_ids == execution.mutated_bundle.trace.issue_propagation_ids == ("ISSUE-RISK-UNKNOWN",)
        case "no_downgrade_repair":
            assert len(execution.mutated_bundle.gate.member_ids) == 6
            assert execution.mutated_bundle.gate.member_ids[-1] == "UNKNOWN_MEMBER"
            assert execution.overall_status == "INVALID"
        case _:
            raise AssertionError("unknown side_effect_assertion token: " + expected_assertion)
    assert set(called_ports) <= {
        "RUN_F09_SLICE",
        "VALIDATE_STATEMENT_PROJECTION",
        "WRITE_ARTIFACT_SET",
        "INSPECT_ARTIFACT_SET",
        "RETRY_ARTIFACT_SET",
        "VALIDATE_FEEDBACK_BINDING",
        "VALIDATE_FEEDBACK_BINDING_RECORD",
        "EVALUATE_LEARNING_ELIGIBILITY",
        "VALIDATE_LEARNING_ELIGIBILITY",
    }
    assert RunTrack.PRODUCTION_DEFAULT not in called_tracks
    if run.evidence is not None:
        assert run.evidence.track is not RunTrack.PRODUCTION_DEFAULT
    if run.trace is not None:
        assert run.trace.track is not RunTrack.PRODUCTION_DEFAULT
    if run.statement_set is not None:
        assert run.statement_set.track is not RunTrack.PRODUCTION_DEFAULT
    if run.manifest is not None:
        assert run.manifest.key.track is not RunTrack.PRODUCTION_DEFAULT
        assert all(record.track is not RunTrack.PRODUCTION_DEFAULT for record in run.manifest.records)
    if execution.feedback_phase.submission is not None:
        assert execution.feedback_phase.submission.track is not RunTrack.PRODUCTION_DEFAULT


@pytest.mark.parametrize(
    "scenario",
    SCENARIOS,
    ids=[scenario.test_id for scenario in SCENARIOS],
)
def test_f09_vertical_matrix(scenario: VerticalScenario, tmp_path: Path) -> None:
    execution = execute_scenario(scenario, tmp_path)
    assert_action_and_state(execution, scenario.expected_action, scenario.expected_gate_or_state)
    assert_issue(execution, scenario.expected_issue_code, scenario.expected_issue_path)
    assert_basis(execution, scenario.basis_assertions)
    assert_bindings(execution, scenario.binding_assertions)
    assert_side_effect_boundary(execution, scenario.side_effect_assertion)
