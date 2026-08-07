from __future__ import annotations

import ast
import inspect
from dataclasses import MISSING, FrozenInstanceError, fields, replace
from pathlib import Path
from typing import get_args, get_type_hints

import pytest

from engine.f09 import feedback
from engine.f09.artifacts import (
    ArtifactRecord,
    ArtifactSetManifest,
    ArtifactWriteAttempt,
    IdempotencyKey,
    IssuedRunArtifactSetProofV1,
    RunArtifactSetKeyV1,
    RunArtifactSetResultV1,
    digest_artifact_records,
    provision_verified_run_manifest_fixture_v1,
    validate_run_artifact_manifest_v1,
)
from engine.f09 import canonical_json
from engine.f09.canonical_json import (
    JcsValue,
    bounded_jcs_sha256,
    canonicalize_bounded_jcs,
    parse_bounded_jcs,
)
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


PUBLIC_SHAPES = {
    feedback.TrackSourceBinding: ("track_source_binding_id", "side", "track", "state", "source_evidence_ref", "parser_ref", "schema_version", "contract_version", "content_digest", "state_reason_codes", "captured_at"),
    feedback.FeedbackItem: ("feedback_item_id", "feedback_id", "source_span_locator", "target_statement_id", "target_statement_revision_id", "target_run_id", "target_prediction_id", "verdict", "annotation", "integrity", "issue_ids"),
    feedback.FeedbackSubmission: ("feedback_id", "case_id", "track", "track_source_binding", "source_snapshot_ref", "source_snapshot_payload", "parser_id", "parser_version", "feedback_items", "content_digest", "captured_at"),
    feedback.StatementProjectionRecord: ("projection_id", "projection_type", "statement_set_id", "statement_id", "statement_revision_id", "source_statement_digest", "projected_object_ref", "transformation_id", "fidelity", "dropped_refs", "synthesized_fields", "issue_ids"),
    feedback.AnchorSelectionRecord: ("anchor_selection_id", "statement_id", "statement_revision_id", "all_rule_refs", "selected_anchor_rule_ref", "non_anchor_rule_refs", "selection_policy_id", "selection_policy_version", "source_order_digest", "fidelity", "fanout_scope", "issue_ids"),
    feedback.FeedbackBinding: ("feedback_binding_id", "feedback_item_ref", "binding_protocol", "source_track_binding_ref", "target_track_source_binding", "case_match", "track_match", "run_match", "statement_match", "revision_match", "statement_set_match", "artifact_digest_match", "target_object_refs", "record_anchor_ref", "status", "issue_ids", "detected_issues", "content_digest"),
    feedback.GoverningVersions: ("statement_contract_version", "statement_set_contract_version", "statement_records_contract_version", "rule_contract_version"),
    feedback.RuleMetadataReceipt: ("rule_ref", "family_id", "school", "canon", "rule_type", "metadata_schema_version", "metadata_contract_version", "source_ref", "content_digest", "captured_at"),
    feedback.ProductionStatementAuthority: ("statement_set", "manifest", "statement_refs", "statement_set_ref", "records_projection_refs", "records_projection_records", "anchor_selections", "rule_metadata_receipts", "governing_versions", "content_digest"),
    feedback.PreprodRunAuthority: ("case_id", "track", "run_id", "manifest", "target_refs", "content_digest"),
    feedback.AnchorPolicy: ("policy_id", "policy_version", "required_rule_object_type", "required_fidelity", "required_fanout_scope", "schema_version", "contract_version", "content_digest"),
    feedback.EligibilityPolicy: ("policy_id", "policy_version", "allowed_track", "required_feedback_policy", "human_review_on_ambiguous", "human_review_on_invalid", "human_review_on_unknown_track", "schema_version", "contract_version", "content_digest"),
    feedback.RawFeedbackAuthority: ("raw_submission", "target_authority", "target_track_source_binding", "captured_at"),
    feedback.ItemTargetReceipt: ("feedback_item_id", "protocol", "target_statement_id", "target_statement_revision_id", "target_run_id", "target_prediction_id", "resolution_status", "non_bound_category", "graph", "graph_digest", "content_digest"),
    feedback.FeedbackOperationReceipt: ("operation_id", "key", "source_digest", "authority_digest", "item_target_receipts", "aggregate_target_digest", "bindings", "anchor_policy_ref", "eligibility_policy_ref", "created_at", "content_digest"),
    feedback.PriorFeedbackOperation: ("raw_authority", "receipt"),
    feedback.ValidFeedbackOperationResult: ("valid", "operation_disposition", "source_identity_relation", "prior_receipt", "current_receipt", "bindings", "overwrite_permitted", "detected_issues"),
    feedback.InvalidFeedbackOperationResult: ("valid", "operation_disposition", "source_identity_relation", "prior_receipt", "current_key", "prior_aggregate_target_digest", "current_aggregate_target_digest", "item_target_receipts", "bindings", "overwrite_permitted", "detected_issues"),
    feedback.LearningEligibility: ("eligibility_id", "feedback_binding_id", "feedback_binding_digest", "policy_id", "policy_version", "status", "learning_target_refs", "excluded_supporting_rule_refs", "blocking_reason_codes", "detected_issues", "evaluated_at", "content_digest"),
}


_ZERO = DigestRef("sha256", "RFC8785-JCS-UTF8", "0" * 64)
_NOW = "2026-07-22T01:02:03Z"


class _Clock:
    def __init__(self, value=_NOW):
        self.value = value
        self.calls = 0

    def now(self):
        self.calls += 1
        return self.value


def _digest(value):
    return bounded_jcs_sha256(value)


def _oracle_digest_ref(digest):
    return {
        "algorithm": digest.algorithm,
        "canonicalization": digest.canonicalization,
        "value": digest.value,
    }


def _oracle_digest_binding(binding):
    if type(binding) is DigestPresent:
        return {"status": binding.status, "digest": _oracle_digest_ref(binding.digest)}
    return {"status": binding.status, "digest": None, "issue_id": binding.issue_id}


def _oracle_ref(ref):
    return {
        "object_type": ref.object_type,
        "object_id": ref.object_id,
        "revision_id": ref.revision_id,
        "schema_version": ref.schema_version,
        "contract_version": ref.contract_version,
        "digest_binding": _oracle_digest_binding(ref.digest_binding),
        "source_locator_id": ref.source_locator_id,
        "captured_at": ref.captured_at,
    }


def _oracle_projection(record):
    return {
        "projection_id": record.projection_id,
        "projection_type": record.projection_type,
        "statement_set_id": record.statement_set_id,
        "statement_id": record.statement_id,
        "statement_revision_id": record.statement_revision_id,
        "source_statement_digest": _oracle_digest_ref(record.source_statement_digest),
        "projected_object_ref": _oracle_ref(record.projected_object_ref),
        "transformation_id": record.transformation_id,
        "fidelity": record.fidelity,
        "dropped_refs": tuple(_oracle_ref(ref) for ref in record.dropped_refs),
        "synthesized_fields": record.synthesized_fields,
        "issue_ids": record.issue_ids,
    }


def _oracle_anchor(record):
    return {
        "anchor_selection_id": record.anchor_selection_id,
        "statement_id": record.statement_id,
        "statement_revision_id": record.statement_revision_id,
        "all_rule_refs": tuple(_oracle_ref(ref) for ref in record.all_rule_refs),
        "selected_anchor_rule_ref": None if record.selected_anchor_rule_ref is None else _oracle_ref(record.selected_anchor_rule_ref),
        "non_anchor_rule_refs": tuple(_oracle_ref(ref) for ref in record.non_anchor_rule_refs),
        "selection_policy_id": record.selection_policy_id,
        "selection_policy_version": record.selection_policy_version,
        "source_order_digest": _oracle_digest_ref(record.source_order_digest),
        "fidelity": record.fidelity,
        "fanout_scope": record.fanout_scope,
        "issue_ids": record.issue_ids,
    }


def _oracle_metadata(receipt):
    return {
        "rule_ref": _oracle_ref(receipt.rule_ref),
        "family_id": receipt.family_id,
        "school": receipt.school,
        "canon": receipt.canon,
        "rule_type": receipt.rule_type,
        "metadata_schema_version": receipt.metadata_schema_version,
        "metadata_contract_version": receipt.metadata_contract_version,
        "source_ref": _oracle_ref(receipt.source_ref),
        "captured_at": receipt.captured_at,
    }


def _ref(object_type, object_id, *, revision="rev-1", schema="schema.v1", contract="contract.v1", digest=None):
    return VersionedObjectRef(
        object_type,
        object_id,
        revision,
        schema,
        contract,
        DigestPresent("PRESENT", digest or _digest(object_id)),
        None,
        _NOW,
    )


def _track_binding(*, side, track=RunTrack.PRODUCTION_DEFAULT, state="AVAILABLE_RESOLVED", reasons=(), parser_id="PARSER", parser_version="v1"):
    unsigned = feedback.TrackSourceBinding(
        f"TSB:{side}:{track.value}",
        side,
        track,
        state,
        _ref("FEEDBACK_SOURCE", "SOURCE"),
        _ref("PARSER", parser_id, revision=parser_version),
        "track-source.v1",
        "track-source-contract.v1",
        _ZERO,
        reasons,
        _NOW,
    )
    return replace(unsigned, content_digest=_digest(feedback._track_source_binding_self_excluded_material(unsigned)))


def _statement(*, statement_id="STMT-1", revision="rev-stmt-1", case_id="CASE-1", set_id="SET-1", track=RunTrack.PRODUCTION_DEFAULT, feedback_policy="FEEDBACK_ALLOWED"):
    declaration = NotApplicableDeclarationBinding("NOT_APPLICABLE", "DECLARATION_NOT_APPLICABLE")
    unsigned = StandardStatement(
        statement_id,
        revision,
        "statement.v1",
        case_id,
        set_id,
        track,
        "scope",
        "career",
        "statement text",
        None,
        "DECISION-1",
        "ACTION-1",
        ("BASIS-1",),
        (),
        (),
        ("SOURCE-LOCATOR-1",),
        (),
        None,
        declaration,
        declaration,
        feedback_policy,
        _ZERO,
        "VALID",
        (),
    )
    return replace(unsigned, content_digest=_digest(feedback._standard_statement_owner_content_material(unsigned)))


def _statement_set(statements, *, case_id="CASE-1", set_id="SET-1", track=RunTrack.PRODUCTION_DEFAULT):
    declaration = NotApplicableDeclarationBinding("NOT_APPLICABLE", "DECLARATION_NOT_APPLICABLE")
    decision = DecisionTraceRef(
        _ref("DECISION_RESULT", "DECISION-1"),
        "ACTION-1",
        DecisionAction.OUTPUT,
        ("BASIS-1",),
        (),
        (),
        (),
        declaration,
        declaration,
        "VALID",
    )
    unsigned = StatementSet(
        set_id,
        "statement.v1",
        case_id,
        track,
        _ref("NORMALIZED_PACKAGE", "PACKAGE-1"),
        decision,
        tuple(statements),
        _ZERO,
        _NOW,
        "PUBLISHABLE",
        (),
    )
    return replace(unsigned, content_digest=_digest(feedback._statement_set_owner_content_material(unsigned)))


def _manifest(records):
    records = tuple(records)
    key = IdempotencyKey(
        "PROJECT_RECORDS",
        "CASE-1",
        RunTrack.PRODUCTION_DEFAULT,
        _digest("source"),
        _digest("schemas"),
        _digest("contracts"),
        "SET-1",
        None,
        _digest("key"),
    )
    return ArtifactSetManifest("MANIFEST-1", key, records, ArtifactSetState.COMPLETE_VERIFIED, digest_artifact_records(records), ())


def _metadata(rule_ref, *, family_id="FAMILY-1", contract="rule.v1", source_ref=None):
    unsigned = feedback.RuleMetadataReceipt(
        rule_ref,
        family_id,
        "school",
        "canon",
        "rule-type",
        "rule-metadata.v1",
        contract,
        source_ref or _ref(
            "RULE_SOURCE", "RULE-SOURCE-1", schema="rule-metadata.v1"
        ),
        _ZERO,
        _NOW,
    )
    return replace(unsigned, content_digest=_digest(feedback._rule_metadata_receipt_self_excluded_material(unsigned)))


def _production_authority(*, statements=None, records=None, statement_refs=None, projection_refs=None, projections=None, anchors=None, metadata=None, set_case="CASE-1", set_track=RunTrack.PRODUCTION_DEFAULT):
    statements = tuple(statements or (_statement(case_id=set_case, track=set_track),))
    statement_set = _statement_set(statements, case_id=set_case, track=set_track)
    statement = statements[0]
    record_digest = _digest("statement-records")
    records = tuple(records or (ArtifactRecord(
        "ART-RECORDS",
        "STATEMENT_RECORDS",
        set_track,
        set_case,
        statement_set.statement_set_id,
        None,
        "statement_records.bin",
        "records.v1",
        record_digest,
        record_digest,
        ArtifactItemState.VERIFIED,
        (),
        (),
    ),))
    artifact_ref = _ref("STATEMENT_RECORDS", "ART-RECORDS", schema="records.v1", contract="records.v1", digest=record_digest)
    statement_ref = _ref("STATEMENT", statement.statement_id, revision=statement.statement_revision_id, schema=statement.statement_schema_version, contract="statement.v1", digest=statement.content_digest)
    set_ref = _ref("STATEMENT_SET", statement_set.statement_set_id, revision="rev-set-1", schema=statement_set.statement_schema_version, contract="statement-set.v1", digest=statement_set.content_digest)
    projection = feedback.StatementProjectionRecord(
        "PROJECTION-1",
        "STATEMENT_RECORDS",
        statement_set.statement_set_id,
        statement.statement_id,
        statement.statement_revision_id,
        statement.content_digest,
        artifact_ref,
        "PROJECT-RECORDS-v1",
        "LOSSLESS",
        (),
        (),
        (),
    )
    selected = _ref("RULE", "RULE-1", contract="rule.v1")
    supporting = _ref("RULE", "RULE-2", contract="rule.v1")
    policy = feedback._pinned_anchor_policy()
    rules = (supporting, selected)
    anchor = feedback.AnchorSelectionRecord(
        "ANCHOR-1",
        statement.statement_id,
        statement.statement_revision_id,
        rules,
        selected,
        (supporting,),
        policy.policy_id,
        policy.policy_version,
        _digest(tuple(feedback._versioned_object_ref_material(ref) for ref in rules)),
        policy.required_fidelity,
        policy.required_fanout_scope,
        (),
    )
    authority = feedback.ProductionStatementAuthority(
        statement_set,
        _manifest(records),
        tuple(statement_refs) if statement_refs is not None else (statement_ref,),
        set_ref,
        tuple(projection_refs) if projection_refs is not None else (artifact_ref,),
        tuple(projections) if projections is not None else (projection,),
        tuple(anchors) if anchors is not None else (anchor,),
        tuple(metadata) if metadata is not None else (_metadata(selected),),
        feedback.GoverningVersions("statement.v1", "statement-set.v1", "records.v1", "rule.v1"),
        _ZERO,
    )
    return replace(authority, content_digest=_digest(feedback._production_authority_self_excluded_material(authority)))


def _preprod_authority(*, refs=None, records=None, run_id="RUN-1"):
    digest = _digest({"items": ({"id": "ITEM-1"},)})
    snapshot_ref = _ref("RUN_SNAPSHOT", "SNAP", schema="feedback.v1", contract=None, digest=digest)
    records = tuple(records or (ArtifactRecord(
        "SNAP", "RUN_SNAPSHOT", RunTrack.V5_V6_PREPROD, "CASE-1", None, run_id,
        "run.bin", "feedback.v1", digest, digest, ArtifactItemState.VERIFIED, (), (),
    ),))
    authority = feedback.PreprodRunAuthority(
        "CASE-1", RunTrack.V5_V6_PREPROD, run_id, _manifest(records),
        tuple(refs) if refs is not None else (snapshot_ref,), _ZERO,
    )
    return replace(authority, content_digest=_digest(feedback._preprod_authority_self_excluded_material(authority)))


def _verified_preprod_authority():
    manifest = provision_verified_run_manifest_fixture_v1()
    refs = tuple(
        _ref(record.artifact_role, record.artifact_id, schema=record.schema_version, contract="run-fixture.v1", digest=record.observed_digest)
        for record in manifest.records
    ) + (_ref("MANIFEST", manifest.manifest_id, schema="run-fixture.v1", contract="run-fixture.v1", digest=manifest.digest),)
    unsigned = feedback.PreprodRunAuthority(
        manifest.key.case_id, manifest.key.track, manifest.key.run_id, manifest, refs, _ZERO,
    )
    return replace(unsigned, content_digest=_digest(feedback._preprod_authority_self_excluded_material(unsigned)))


def _item(*, item_id="ITEM-1", statement_id="STMT-1", revision="rev-stmt-1", run_id=None, locator="SNAP#/items/0", integrity="VALID"):
    return feedback.FeedbackItem(item_id, "FEEDBACK-1", locator, statement_id, revision, run_id, None, "CONFIRM", "", integrity, ())


def _raw(authority, *, items=None, source_binding=None, target_binding=None, payload=None, submission_track=None, captured_at=_NOW):
    items = tuple(items or (_item(run_id="RUN-1", statement_id=None, revision=None) if type(authority) is feedback.PreprodRunAuthority else _item(),))
    track = submission_track or (RunTrack.V5_V6_PREPROD if type(authority) is feedback.PreprodRunAuthority else RunTrack.PRODUCTION_DEFAULT)
    source_binding = source_binding or _track_binding(side="SUBMISSION_SOURCE", track=track)
    target_binding = target_binding or _track_binding(side="BINDING_TARGET", track=authority.track if type(authority) is feedback.PreprodRunAuthority else authority.statement_set.track)
    payload = {"items": tuple({"id": item.feedback_item_id} for item in items)} if payload is None else payload
    snapshot = SnapshotRef("SNAP", "FEEDBACK", ("SNAP",), "feedback.v1", "feedback-contract.v1", _digest(payload), _NOW, "IMMUTABLE")
    submission = feedback.FeedbackSubmission(
        "FEEDBACK-1", "CASE-1", track, source_binding, snapshot, payload,
        "PARSER", "v1", items, _ZERO, _NOW,
    )
    submission = replace(submission, content_digest=_digest(feedback._feedback_submission_self_excluded_material(submission)))
    material = feedback._feedback_submission_self_excluded_material(submission)
    material["track_source_binding"] = material["track_source_binding"] | {
        "content_digest": feedback._digest_ref_material(source_binding.content_digest),
    }
    material["content_digest"] = feedback._digest_ref_material(submission.content_digest)
    return feedback.RawFeedbackAuthority(canonicalize_bounded_jcs(material), authority, target_binding, captured_at)


def _bind(authority=None, **raw_changes):
    authority = authority or _production_authority()
    raw = _raw(authority, **raw_changes)
    return feedback.bind_feedback_operation(raw, prior=None, clock=_Clock())


def _binding(result, index=0):
    assert result.valid is True
    assert result.bindings is result.current_receipt.bindings
    return result.bindings[index]


def _assert_nonbound_receipt(result, index, status, category=None):
    binding = _binding(result, index)
    receipt = result.current_receipt.item_target_receipts[index]
    assert binding.status == status
    assert receipt.resolution_status == status
    assert receipt.graph == ()
    if category is not None:
        assert receipt.non_bound_category == category
    item = feedback.FeedbackItem(
        receipt.feedback_item_id, "FEEDBACK-1", "SNAP#", receipt.target_statement_id,
        receipt.target_statement_revision_id, receipt.target_run_id,
        receipt.target_prediction_id, "CONFIRM", "", "VALID", (),
    )
    assert receipt.graph_digest == _digest(
        feedback._item_target_graph_material(
            receipt.protocol,
            item,
            status,
            receipt.non_bound_category,
            (),
        )
    )
    assert receipt.content_digest == _digest(feedback._item_target_receipt_self_excluded_material(receipt))
    return binding, receipt


def _assert_invalid_authority_preimages(raw, result):
    submission = feedback._parse_submission(raw.raw_submission)
    operation = result.current_receipt
    protocol = "PRODUCTION_STATEMENT"
    anchor_policy = feedback._pinned_anchor_policy()
    eligibility_policy = feedback._pinned_eligibility_policy()

    def digest_material(value):
        return {"algorithm": value.algorithm, "canonicalization": value.canonicalization, "value": value.value}

    def key_material(value):
        return {
            "operation": value.operation,
            "case_id": value.case_id,
            "track": value.track.value,
            "source_digest": digest_material(value.source_digest),
            "schema_versions_digest": digest_material(value.schema_versions_digest),
            "contract_digest": digest_material(value.contract_digest),
            "statement_set_id": value.statement_set_id,
            "feedback_id": value.feedback_id,
        }

    invalid_authority = {
        "material_domain": "G6_TASK8_TARGET_AUTHORITY",
        "material_version": "invalid-authority.v1",
        "authority_status": "INVALID_MATERIAL",
        "protocol": protocol,
    }
    invalid_schema = {
        "submission": submission.source_snapshot_ref.schema_version,
        "track_source_binding": submission.track_source_binding.schema_version,
        "target_authority": {"status": "INVALID_MATERIAL", "protocol": protocol, "schema_version": None, "rule_metadata_schema_version": None},
        "rule_metadata": None,
        "anchor_policy": anchor_policy.schema_version,
        "eligibility_policy": eligibility_policy.schema_version,
    }
    invalid_contract = {
        "submission": submission.source_snapshot_ref.contract_version,
        "track_source_binding": submission.track_source_binding.contract_version,
        "target_authority": {"status": "INVALID_MATERIAL", "protocol": protocol, "contract_version": None, "governing_versions": (None, None, None, None)},
        "governing_versions": (None, None, None, None),
        "anchor_policy": anchor_policy.contract_version,
        "eligibility_policy": eligibility_policy.contract_version,
    }
    identities = tuple({
        "feedback_item_id": item.feedback_item_id,
        "target_statement_id": item.target_statement_id,
        "target_statement_revision_id": item.target_statement_revision_id,
        "target_run_id": item.target_run_id,
        "target_prediction_id": item.target_prediction_id,
    } for item in sorted(submission.feedback_items, key=lambda item: item.feedback_item_id.encode("utf-16-be")))
    canonical_identity = {
        "key": key_material(operation.key),
        "item_raw_identities": identities,
        "anchor_policy": (anchor_policy.policy_id, anchor_policy.policy_version),
        "eligibility_policy": (eligibility_policy.policy_id, eligibility_policy.policy_version),
        "submission_schema": submission.source_snapshot_ref.schema_version,
        "submission_contract": submission.source_snapshot_ref.contract_version,
        "authority_identity": {"status": "INVALID_MATERIAL", "protocol": protocol, "authority_schema_version": None, "authority_contract_version": None, "governing_versions": (None, None, None, None), "statement_set_id": None},
        "source_snapshot_digest": digest_material(submission.source_snapshot_ref.content_digest),
        "feedback_id": submission.feedback_id,
        "case_id": submission.case_id,
        "track": submission.track.value,
    }
    assert operation.authority_digest == _digest(invalid_authority)
    assert operation.key.schema_versions_digest == _digest(invalid_schema)
    assert operation.key.contract_digest == _digest(invalid_contract)
    assert operation.key.canonical_key_digest == _digest(canonical_identity)


def _resign_authority(authority):
    return replace(authority, content_digest=_digest(feedback._production_authority_self_excluded_material(authority)))


def _replace_statement(authority, statement, *, resign_statement=True, resign_set=True):
    if resign_statement:
        statement = replace(statement, content_digest=_digest(feedback._standard_statement_owner_content_material(statement)))
    statement_set = replace(authority.statement_set, statements=(statement,))
    if resign_set:
        statement_set = replace(statement_set, content_digest=_digest(feedback._statement_set_owner_content_material(statement_set)))
    statement_refs = tuple(
        replace(
            ref,
            revision_id=statement.statement_revision_id,
            digest_binding=DigestPresent("PRESENT", statement.content_digest),
        )
        if ref.object_id == statement.statement_id
        else ref
        for ref in authority.statement_refs
    )
    statement_set_ref = replace(
        authority.statement_set_ref,
        digest_binding=DigestPresent("PRESENT", statement_set.content_digest),
    )
    return replace(
        authority,
        statement_set=statement_set,
        statement_refs=statement_refs,
        statement_set_ref=statement_set_ref,
    )


def _eligibility(binding, authority=None):
    return feedback.evaluate_learning_eligibility(binding, production_authority=authority, clock=_Clock())


def test_public_dataclass_shapes_are_exact():
    for cls, expected in PUBLIC_SHAPES.items():
        assert tuple(field.name for field in fields(cls)) == expected
        assert cls.__dataclass_params__.frozen
        assert all(
            field.default is MISSING and field.default_factory is MISSING
            for field in fields(cls)
        )
        with pytest.raises((TypeError, FrozenInstanceError)):
            cls.__new__(cls).__setattr__("x", 1)


def test_public_unions_aliases_and_protocol_are_closed():
    aliases = {
        feedback.MatchRequired: {"MATCH", "MISMATCH", "UNKNOWN"},
        feedback.MatchOptional: {"MATCH", "MISMATCH", "NOT_APPLICABLE", "UNKNOWN"},
        feedback.TrackSourceState: {"AVAILABLE_RESOLVED", "SOURCE_MISSING", "UNPARSABLE", "AMBIGUOUS", "INTEGRITY_FAILED"},
        feedback.TrackSourceReasonCode: {"TRACK_SOURCE_MISSING", "TRACK_SOURCE_UNPARSABLE", "TRACK_SOURCE_AMBIGUOUS", "TRACK_SOURCE_INTEGRITY_FAILED"},
        feedback.BindingProtocol: {"PRODUCTION_STATEMENT", "PREPROD_RUN_TARGET"},
        feedback.BindingStatus: {"BOUND", "UNBOUND", "AMBIGUOUS", "INVALID"},
        feedback.EligibilityStatus: {"ELIGIBLE", "INELIGIBLE", "HUMAN_REVIEW"},
        feedback.TargetResolutionCategory: {"INVALID_MATERIAL", "AMBIGUOUS_CANDIDATES", "TARGET_NOT_FOUND", "SOURCE_SPAN_NOT_FOUND", "TRACK_UNRESOLVED", "REQUIRED_MATCH_FAILED", "PROTOCOL_GRAPH_INCOMPLETE"},
        feedback.PreprodArtifactRole: {"RUN_SNAPSHOT", "DECISION_RUN", "FEEDBACK_ATTACHMENT", "MANIFEST"},
    }
    assert all(set(get_args(alias)) == expected for alias, expected in aliases.items())
    assert set(get_args(feedback.FeedbackOperationResult)) == {feedback.ValidFeedbackOperationResult, feedback.InvalidFeedbackOperationResult}
    assert getattr(feedback.FeedbackClockPort, "_is_runtime_protocol", False)
    assert all(set(get_type_hints(cls)) == set(PUBLIC_SHAPES[cls]) for cls in PUBLIC_SHAPES)
    signatures = {
        feedback.bind_feedback_operation: (("current", inspect.Parameter.POSITIONAL_OR_KEYWORD), ("prior", inspect.Parameter.KEYWORD_ONLY), ("clock", inspect.Parameter.KEYWORD_ONLY)),
        feedback.validate_feedback_binding_record: (("binding", inspect.Parameter.POSITIONAL_OR_KEYWORD),),
        feedback.evaluate_learning_eligibility: (("binding", inspect.Parameter.POSITIONAL_OR_KEYWORD), ("production_authority", inspect.Parameter.KEYWORD_ONLY), ("clock", inspect.Parameter.KEYWORD_ONLY)),
        feedback.validate_learning_eligibility: (("eligibility", inspect.Parameter.POSITIONAL_OR_KEYWORD),),
    }
    expected_hints = {
        feedback.bind_feedback_operation: {"current": feedback.RawFeedbackAuthority, "prior": feedback.PriorFeedbackOperation | None, "clock": feedback.FeedbackClockPort, "return": feedback.FeedbackOperationResult},
        feedback.validate_feedback_binding_record: {"binding": feedback.FeedbackBinding, "return": type(None)},
        feedback.evaluate_learning_eligibility: {"binding": feedback.FeedbackBinding, "production_authority": feedback.ProductionStatementAuthority | None, "clock": feedback.FeedbackClockPort, "return": feedback.LearningEligibility},
        feedback.validate_learning_eligibility: {"eligibility": feedback.LearningEligibility, "return": type(None)},
    }
    for function, expected in signatures.items():
        signature = inspect.signature(function)
        assert tuple((name, parameter.kind) for name, parameter in signature.parameters.items()) == expected
        assert all(parameter.default is inspect.Parameter.empty for parameter in signature.parameters.values())
        assert get_type_hints(function) == expected_hints[function]


def test_owner_types_are_reused_by_identity():
    hints = {cls: get_type_hints(cls) for cls in PUBLIC_SHAPES}
    assert hints[feedback.TrackSourceBinding]["track"] is RunTrack
    assert hints[feedback.FeedbackSubmission]["source_snapshot_ref"] is SnapshotRef
    assert hints[feedback.ProductionStatementAuthority]["statement_set"] is StatementSet
    assert hints[feedback.ProductionStatementAuthority]["manifest"] is ArtifactSetManifest
    assert hints[feedback.FeedbackOperationReceipt]["key"] is IdempotencyKey
    assert hints[feedback.FeedbackBinding]["detected_issues"] == tuple[DetectedIssue, ...]
    assert feedback.JcsSnapshotPayload is JcsValue


def test_malformed_top_level_raises_typed_error_without_result():
    class Clock:
        def now(self):
            return "2026-07-22T00:00:00Z"

    with pytest.raises(F09ContractError) as raised:
        feedback.bind_feedback_operation(object(), prior=None, clock=Clock())
    assert raised.value.field_path == "/current"

    authority = _production_authority()
    raw = _raw(authority)
    base = parse_bounded_jcs(raw.raw_submission)
    first_error_cases = (
        ({**base, "case_id": "", "track_source_binding": {"bad": None}}, "/case_id"),
        ({**base, "track_source_binding": {**base["track_source_binding"], "source_evidence_ref": {"bad": None}}, "source_snapshot_ref": {"bad": None}}, "/track_source_binding/source_evidence_ref"),
        ({**base, "track_source_binding": {**base["track_source_binding"], "side": "WRONG", "source_evidence_ref": {"bad": None}}}, "/track_source_binding/side"),
        ({**base, "source_snapshot_ref": {**base["source_snapshot_ref"], "source_type": "WRONG", "content_digest": {"bad": None}}, "feedback_items": ({"bad": None},)}, "/source_snapshot_ref/source_type"),
    )
    for malformed, expected_path in first_error_cases:
        with pytest.raises(F09ContractError) as failure:
            feedback.bind_feedback_operation(replace(raw, raw_submission=canonicalize_bounded_jcs(malformed)), prior=None, clock=Clock())
        assert failure.value.field_path == expected_path

    production_raw = raw
    bypassed_raw_submission = feedback.RawFeedbackAuthority.__new__(feedback.RawFeedbackAuthority)
    object.__setattr__(bypassed_raw_submission, "target_authority", production_raw.target_authority)
    object.__setattr__(bypassed_raw_submission, "target_track_source_binding", production_raw.target_track_source_binding)
    object.__setattr__(bypassed_raw_submission, "captured_at", production_raw.captured_at)
    with pytest.raises(F09ContractError):
        feedback.bind_feedback_operation(bypassed_raw_submission, prior=None, clock=_Clock())
    bypassed_raw_authority = feedback.RawFeedbackAuthority.__new__(feedback.RawFeedbackAuthority)
    object.__setattr__(bypassed_raw_authority, "raw_submission", production_raw.raw_submission)
    object.__setattr__(bypassed_raw_authority, "target_track_source_binding", production_raw.target_track_source_binding)
    object.__setattr__(bypassed_raw_authority, "captured_at", production_raw.captured_at)
    with pytest.raises(F09ContractError):
        feedback.bind_feedback_operation(bypassed_raw_authority, prior=None, clock=_Clock())
    bypassed_raw_binding = feedback.RawFeedbackAuthority.__new__(feedback.RawFeedbackAuthority)
    object.__setattr__(bypassed_raw_binding, "raw_submission", production_raw.raw_submission)
    object.__setattr__(bypassed_raw_binding, "target_authority", production_raw.target_authority)
    object.__setattr__(bypassed_raw_binding, "captured_at", production_raw.captured_at)
    with pytest.raises(F09ContractError):
        feedback.bind_feedback_operation(bypassed_raw_binding, prior=None, clock=_Clock())
    bypassed_raw_captured_at = feedback.RawFeedbackAuthority.__new__(feedback.RawFeedbackAuthority)
    object.__setattr__(bypassed_raw_captured_at, "raw_submission", production_raw.raw_submission)
    object.__setattr__(bypassed_raw_captured_at, "target_authority", production_raw.target_authority)
    object.__setattr__(bypassed_raw_captured_at, "target_track_source_binding", production_raw.target_track_source_binding)
    with pytest.raises(F09ContractError):
        feedback.bind_feedback_operation(bypassed_raw_captured_at, prior=None, clock=_Clock())


def test_every_nested_dereference_is_guarded():
    class Explosive:
        def __getattribute__(self, name):
            raise AssertionError(f"guard dereferenced {name}")

    source = Path("engine/f09/feedback.py").read_text(encoding="utf-8")
    assert "except AttributeError" not in source
    assert "except KeyError" not in source
    assert "except IndexError" not in source
    assert "vars(" not in source
    assert "__dict__" not in source
    assert "dataclasses.fields" not in source
    assert "__dataclass_fields__" not in source
    assert feedback._production_record_scope_valid(Explosive(), "SET-1") is False
    with pytest.raises(F09ContractError):
        feedback._versioned_object_ref_material(Explosive())
    with pytest.raises(F09ContractError):
        feedback.validate_feedback_binding_record(Explosive())
    with pytest.raises(F09ContractError):
        feedback.validate_learning_eligibility(Explosive())
    with pytest.raises(F09ContractError):
        feedback.bind_feedback_operation(_raw(_production_authority()), prior=Explosive(), clock=_Clock())

    production = _production_authority()
    preprod = _preprod_authority()
    production_raw = _raw(production)
    preprod_raw = _raw(preprod)
    statement = production.statement_set.statements[0]
    manifest = production.manifest
    record = manifest.records[0]
    statement_ref = production.statement_refs[0]
    projection = production.records_projection_records[0]
    anchor = production.anchor_selections[0]
    metadata = production.rule_metadata_receipts[0]
    valid_attempt = ArtifactWriteAttempt(
        "ATTEMPT-1", record.artifact_id, "KEY-1", 1, None, (), _NOW,
        _NOW, "SUCCEEDED", record.observed_digest, None, None,
    )
    valid_missing_digest = DigestMissing("MISSING", None, "ISSUE-1")
    valid_issue = DetectedIssue("ISSUE", "/field")
    valid_card = CardIdentityRef(
        "CARD-1", "F01", _ref("CONTRACT", "CARD-CONTRACT"),
        _ref("APPENDIX", "CARD-APPENDIX"), "/field", "PRESENT_VALUE",
        FieldEvaluatorState.EVALUATED, "FROZEN_DECLARATION",
        "REFERENCE_ONLY_NOT_IMPLEMENTATION_PROOF", ("LOC-1",), ("ISSUE-1",),
    )
    valid_frozen_ref = FrozenDeclarationRef(
        "DECL-1", "OUTPUT_PRECISION", "F01", "contract.v1",
        "declaration.v1", _digest("declaration"),
    )
    valid_resolved = ResolvedDeclarationBinding("RESOLVED", valid_frozen_ref)
    valid_absent = AbsentDeclarationBinding("ABSENT", "DECLARATION_NOT_PRESENT")
    valid_not_applicable = NotApplicableDeclarationBinding(
        "NOT_APPLICABLE", "DECLARATION_NOT_APPLICABLE",
    )
    valid_unavailable = UnavailableDeclarationBinding(
        "UNAVAILABLE", "DECLARATION_UNREAD", ("ISSUE-1",),
    )
    valid_unresolvable = UnresolvableDeclarationBinding(
        "UNRESOLVABLE", valid_frozen_ref, "BROKEN_REFERENCE", ("ISSUE-1",),
    )

    bypassed_digest = DigestRef.__new__(DigestRef)
    object.__setattr__(bypassed_digest, "algorithm", statement.content_digest.algorithm)
    object.__setattr__(bypassed_digest, "canonicalization", statement.content_digest.canonicalization)
    malformed_authority = replace(
        production,
        statement_refs=(replace(statement_ref, digest_binding=DigestPresent("PRESENT", bypassed_digest)),),
    )
    result = feedback.bind_feedback_operation(
        feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at),
        prior=None, clock=_Clock(),
    )
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_manifest = ArtifactSetManifest.__new__(ArtifactSetManifest)
    object.__setattr__(bypassed_manifest, "manifest_id", manifest.manifest_id)
    object.__setattr__(bypassed_manifest, "key", manifest.key)
    object.__setattr__(bypassed_manifest, "records", manifest.records)
    object.__setattr__(bypassed_manifest, "state", manifest.state)
    object.__setattr__(bypassed_manifest, "digest", manifest.digest)
    malformed_authority = replace(production, manifest=bypassed_manifest)
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_key = IdempotencyKey.__new__(IdempotencyKey)
    object.__setattr__(bypassed_key, "operation", manifest.key.operation)
    object.__setattr__(bypassed_key, "case_id", manifest.key.case_id)
    object.__setattr__(bypassed_key, "track", manifest.key.track)
    object.__setattr__(bypassed_key, "source_digest", manifest.key.source_digest)
    object.__setattr__(bypassed_key, "schema_versions_digest", manifest.key.schema_versions_digest)
    object.__setattr__(bypassed_key, "contract_digest", manifest.key.contract_digest)
    object.__setattr__(bypassed_key, "statement_set_id", manifest.key.statement_set_id)
    object.__setattr__(bypassed_key, "feedback_id", manifest.key.feedback_id)
    malformed_authority = replace(production, manifest=replace(manifest, key=bypassed_key))
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_record = ArtifactRecord.__new__(ArtifactRecord)
    object.__setattr__(bypassed_record, "artifact_id", record.artifact_id)
    object.__setattr__(bypassed_record, "artifact_role", record.artifact_role)
    object.__setattr__(bypassed_record, "track", record.track)
    object.__setattr__(bypassed_record, "case_id", record.case_id)
    object.__setattr__(bypassed_record, "statement_set_id", record.statement_set_id)
    object.__setattr__(bypassed_record, "run_id", record.run_id)
    object.__setattr__(bypassed_record, "path_locator", record.path_locator)
    object.__setattr__(bypassed_record, "schema_version", record.schema_version)
    object.__setattr__(bypassed_record, "expected_digest", record.expected_digest)
    object.__setattr__(bypassed_record, "observed_digest", record.observed_digest)
    object.__setattr__(bypassed_record, "state", record.state)
    object.__setattr__(bypassed_record, "attempts", record.attempts)
    malformed_authority = replace(production, manifest=replace(manifest, records=(bypassed_record,)))
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_attempt = ArtifactWriteAttempt.__new__(ArtifactWriteAttempt)
    object.__setattr__(bypassed_attempt, "attempt_id", valid_attempt.attempt_id)
    object.__setattr__(bypassed_attempt, "artifact_id", valid_attempt.artifact_id)
    object.__setattr__(bypassed_attempt, "idempotency_key", valid_attempt.idempotency_key)
    object.__setattr__(bypassed_attempt, "attempt_number", valid_attempt.attempt_number)
    object.__setattr__(bypassed_attempt, "retry_of_attempt_id", valid_attempt.retry_of_attempt_id)
    object.__setattr__(bypassed_attempt, "input_snapshot_refs", valid_attempt.input_snapshot_refs)
    object.__setattr__(bypassed_attempt, "started_at", valid_attempt.started_at)
    object.__setattr__(bypassed_attempt, "finished_at", valid_attempt.finished_at)
    object.__setattr__(bypassed_attempt, "outcome", valid_attempt.outcome)
    object.__setattr__(bypassed_attempt, "observed_digest", valid_attempt.observed_digest)
    object.__setattr__(bypassed_attempt, "error_class", valid_attempt.error_class)
    malformed_record = replace(record, attempts=(bypassed_attempt,))
    malformed_authority = replace(production, manifest=replace(manifest, records=(malformed_record,)))
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_present = DigestPresent.__new__(DigestPresent)
    object.__setattr__(bypassed_present, "status", statement_ref.digest_binding.status)
    malformed_authority = replace(production, statement_refs=(replace(statement_ref, digest_binding=bypassed_present),))
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_missing = DigestMissing.__new__(DigestMissing)
    object.__setattr__(bypassed_missing, "status", valid_missing_digest.status)
    object.__setattr__(bypassed_missing, "digest", valid_missing_digest.digest)
    malformed_authority = replace(production, statement_refs=(replace(statement_ref, digest_binding=bypassed_missing),))
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_issue = DetectedIssue.__new__(DetectedIssue)
    object.__setattr__(bypassed_issue, "issue_code", valid_issue.issue_code)
    malformed_authority = replace(production, manifest=replace(manifest, detected_issues=(bypassed_issue,)))
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_trace = DecisionTraceRef.__new__(DecisionTraceRef)
    object.__setattr__(bypassed_trace, "result_ref", production.statement_set.decision_trace_ref.result_ref)
    object.__setattr__(bypassed_trace, "action_id", production.statement_set.decision_trace_ref.action_id)
    object.__setattr__(bypassed_trace, "selected_action", production.statement_set.decision_trace_ref.selected_action)
    object.__setattr__(bypassed_trace, "basis_record_ids", production.statement_set.decision_trace_ref.basis_record_ids)
    object.__setattr__(bypassed_trace, "blocking_issue_ids", production.statement_set.decision_trace_ref.blocking_issue_ids)
    object.__setattr__(bypassed_trace, "nonblocking_issue_ids", production.statement_set.decision_trace_ref.nonblocking_issue_ids)
    object.__setattr__(bypassed_trace, "source_decision_refs", production.statement_set.decision_trace_ref.source_decision_refs)
    object.__setattr__(bypassed_trace, "output_precision_binding", production.statement_set.decision_trace_ref.output_precision_binding)
    object.__setattr__(bypassed_trace, "validation_plan_binding", production.statement_set.decision_trace_ref.validation_plan_binding)
    malformed_authority = replace(production, statement_set=replace(production.statement_set, decision_trace_ref=bypassed_trace))
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_card = CardIdentityRef.__new__(CardIdentityRef)
    object.__setattr__(bypassed_card, "card_identity_ref_id", valid_card.card_identity_ref_id)
    object.__setattr__(bypassed_card, "card_id", valid_card.card_id)
    object.__setattr__(bypassed_card, "normative_contract_ref", valid_card.normative_contract_ref)
    object.__setattr__(bypassed_card, "machine_appendix_ref", valid_card.machine_appendix_ref)
    object.__setattr__(bypassed_card, "field_path", valid_card.field_path)
    object.__setattr__(bypassed_card, "source_field_state", valid_card.source_field_state)
    object.__setattr__(bypassed_card, "evaluator_state", valid_card.evaluator_state)
    object.__setattr__(bypassed_card, "declaration_status", valid_card.declaration_status)
    object.__setattr__(bypassed_card, "runtime_capability_status", valid_card.runtime_capability_status)
    object.__setattr__(bypassed_card, "source_locator_ids", valid_card.source_locator_ids)
    malformed_statement = replace(statement, card_identity_refs=(bypassed_card,))
    malformed_authority = replace(production, statement_set=replace(production.statement_set, statements=(malformed_statement,)))
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_resolved = ResolvedDeclarationBinding.__new__(ResolvedDeclarationBinding)
    object.__setattr__(bypassed_resolved, "presence", valid_resolved.presence)
    malformed_statement = replace(statement, output_precision_binding=bypassed_resolved)
    malformed_authority = replace(production, statement_set=replace(production.statement_set, statements=(malformed_statement,)))
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_absent = AbsentDeclarationBinding.__new__(AbsentDeclarationBinding)
    object.__setattr__(bypassed_absent, "presence", valid_absent.presence)
    malformed_statement = replace(statement, output_precision_binding=bypassed_absent)
    malformed_authority = replace(production, statement_set=replace(production.statement_set, statements=(malformed_statement,)))
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_not_applicable = NotApplicableDeclarationBinding.__new__(NotApplicableDeclarationBinding)
    object.__setattr__(bypassed_not_applicable, "presence", valid_not_applicable.presence)
    malformed_statement = replace(statement, output_precision_binding=bypassed_not_applicable)
    malformed_authority = replace(production, statement_set=replace(production.statement_set, statements=(malformed_statement,)))
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_unavailable = UnavailableDeclarationBinding.__new__(UnavailableDeclarationBinding)
    object.__setattr__(bypassed_unavailable, "presence", valid_unavailable.presence)
    object.__setattr__(bypassed_unavailable, "reason_code", valid_unavailable.reason_code)
    malformed_statement = replace(statement, output_precision_binding=bypassed_unavailable)
    malformed_authority = replace(production, statement_set=replace(production.statement_set, statements=(malformed_statement,)))
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_unresolvable = UnresolvableDeclarationBinding.__new__(UnresolvableDeclarationBinding)
    object.__setattr__(bypassed_unresolvable, "presence", valid_unresolvable.presence)
    object.__setattr__(bypassed_unresolvable, "attempted_ref", valid_unresolvable.attempted_ref)
    object.__setattr__(bypassed_unresolvable, "reason_code", valid_unresolvable.reason_code)
    malformed_statement = replace(statement, output_precision_binding=bypassed_unresolvable)
    malformed_authority = replace(production, statement_set=replace(production.statement_set, statements=(malformed_statement,)))
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_frozen_ref = FrozenDeclarationRef.__new__(FrozenDeclarationRef)
    object.__setattr__(bypassed_frozen_ref, "declaration_id", valid_frozen_ref.declaration_id)
    object.__setattr__(bypassed_frozen_ref, "declaration_type", valid_frozen_ref.declaration_type)
    object.__setattr__(bypassed_frozen_ref, "card_id", valid_frozen_ref.card_id)
    object.__setattr__(bypassed_frozen_ref, "contract_version", valid_frozen_ref.contract_version)
    object.__setattr__(bypassed_frozen_ref, "declaration_schema_version", valid_frozen_ref.declaration_schema_version)
    malformed_statement = replace(statement, output_precision_binding=ResolvedDeclarationBinding("RESOLVED", bypassed_frozen_ref))
    malformed_authority = replace(production, statement_set=replace(production.statement_set, statements=(malformed_statement,)))
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_statement = StandardStatement.__new__(StandardStatement)
    object.__setattr__(bypassed_statement, "statement_id", statement.statement_id)
    object.__setattr__(bypassed_statement, "statement_revision_id", statement.statement_revision_id)
    object.__setattr__(bypassed_statement, "statement_schema_version", statement.statement_schema_version)
    object.__setattr__(bypassed_statement, "case_id", statement.case_id)
    object.__setattr__(bypassed_statement, "statement_set_id", statement.statement_set_id)
    object.__setattr__(bypassed_statement, "track", statement.track)
    object.__setattr__(bypassed_statement, "semantic_scope", statement.semantic_scope)
    object.__setattr__(bypassed_statement, "domain", statement.domain)
    object.__setattr__(bypassed_statement, "statement_text", statement.statement_text)
    object.__setattr__(bypassed_statement, "display_section", statement.display_section)
    object.__setattr__(bypassed_statement, "decision_result_id", statement.decision_result_id)
    object.__setattr__(bypassed_statement, "action_id", statement.action_id)
    object.__setattr__(bypassed_statement, "basis_record_ids", statement.basis_record_ids)
    object.__setattr__(bypassed_statement, "evidence_refs", statement.evidence_refs)
    object.__setattr__(bypassed_statement, "relation_ids", statement.relation_ids)
    object.__setattr__(bypassed_statement, "source_locator_ids", statement.source_locator_ids)
    object.__setattr__(bypassed_statement, "card_identity_refs", statement.card_identity_refs)
    object.__setattr__(bypassed_statement, "confidence_snapshot_ref", statement.confidence_snapshot_ref)
    object.__setattr__(bypassed_statement, "output_precision_binding", statement.output_precision_binding)
    object.__setattr__(bypassed_statement, "validation_plan_binding", statement.validation_plan_binding)
    object.__setattr__(bypassed_statement, "feedback_policy", statement.feedback_policy)
    object.__setattr__(bypassed_statement, "content_digest", statement.content_digest)
    object.__setattr__(bypassed_statement, "integrity", statement.integrity)
    malformed_authority = replace(production, statement_set=replace(production.statement_set, statements=(bypassed_statement,)))
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_set = StatementSet.__new__(StatementSet)
    object.__setattr__(bypassed_set, "statement_set_id", production.statement_set.statement_set_id)
    object.__setattr__(bypassed_set, "statement_schema_version", production.statement_set.statement_schema_version)
    object.__setattr__(bypassed_set, "case_id", production.statement_set.case_id)
    object.__setattr__(bypassed_set, "track", production.statement_set.track)
    object.__setattr__(bypassed_set, "source_package_ref", production.statement_set.source_package_ref)
    object.__setattr__(bypassed_set, "decision_trace_ref", production.statement_set.decision_trace_ref)
    object.__setattr__(bypassed_set, "statements", production.statement_set.statements)
    object.__setattr__(bypassed_set, "content_digest", production.statement_set.content_digest)
    object.__setattr__(bypassed_set, "generated_at", production.statement_set.generated_at)
    object.__setattr__(bypassed_set, "publication_state", production.statement_set.publication_state)
    malformed_authority = replace(production, statement_set=bypassed_set)
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_ref = VersionedObjectRef.__new__(VersionedObjectRef)
    object.__setattr__(bypassed_ref, "object_type", statement_ref.object_type)
    object.__setattr__(bypassed_ref, "object_id", statement_ref.object_id)
    object.__setattr__(bypassed_ref, "revision_id", statement_ref.revision_id)
    object.__setattr__(bypassed_ref, "schema_version", statement_ref.schema_version)
    object.__setattr__(bypassed_ref, "contract_version", statement_ref.contract_version)
    object.__setattr__(bypassed_ref, "digest_binding", statement_ref.digest_binding)
    object.__setattr__(bypassed_ref, "source_locator_id", statement_ref.source_locator_id)
    malformed_authority = replace(production, statement_refs=(bypassed_ref,))
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_versions = feedback.GoverningVersions.__new__(feedback.GoverningVersions)
    object.__setattr__(bypassed_versions, "statement_contract_version", production.governing_versions.statement_contract_version)
    object.__setattr__(bypassed_versions, "statement_set_contract_version", production.governing_versions.statement_set_contract_version)
    object.__setattr__(bypassed_versions, "statement_records_contract_version", production.governing_versions.statement_records_contract_version)
    malformed_authority = replace(production, governing_versions=bypassed_versions)
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_projection = feedback.StatementProjectionRecord.__new__(feedback.StatementProjectionRecord)
    object.__setattr__(bypassed_projection, "projection_id", projection.projection_id)
    object.__setattr__(bypassed_projection, "projection_type", projection.projection_type)
    object.__setattr__(bypassed_projection, "statement_set_id", projection.statement_set_id)
    object.__setattr__(bypassed_projection, "statement_id", projection.statement_id)
    object.__setattr__(bypassed_projection, "statement_revision_id", projection.statement_revision_id)
    object.__setattr__(bypassed_projection, "source_statement_digest", projection.source_statement_digest)
    object.__setattr__(bypassed_projection, "projected_object_ref", projection.projected_object_ref)
    object.__setattr__(bypassed_projection, "transformation_id", projection.transformation_id)
    object.__setattr__(bypassed_projection, "fidelity", projection.fidelity)
    object.__setattr__(bypassed_projection, "dropped_refs", projection.dropped_refs)
    object.__setattr__(bypassed_projection, "synthesized_fields", projection.synthesized_fields)
    malformed_authority = replace(production, records_projection_records=(bypassed_projection,))
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_anchor = feedback.AnchorSelectionRecord.__new__(feedback.AnchorSelectionRecord)
    object.__setattr__(bypassed_anchor, "anchor_selection_id", anchor.anchor_selection_id)
    object.__setattr__(bypassed_anchor, "statement_id", anchor.statement_id)
    object.__setattr__(bypassed_anchor, "statement_revision_id", anchor.statement_revision_id)
    object.__setattr__(bypassed_anchor, "all_rule_refs", anchor.all_rule_refs)
    object.__setattr__(bypassed_anchor, "selected_anchor_rule_ref", anchor.selected_anchor_rule_ref)
    object.__setattr__(bypassed_anchor, "non_anchor_rule_refs", anchor.non_anchor_rule_refs)
    object.__setattr__(bypassed_anchor, "selection_policy_id", anchor.selection_policy_id)
    object.__setattr__(bypassed_anchor, "selection_policy_version", anchor.selection_policy_version)
    object.__setattr__(bypassed_anchor, "source_order_digest", anchor.source_order_digest)
    object.__setattr__(bypassed_anchor, "fidelity", anchor.fidelity)
    object.__setattr__(bypassed_anchor, "fanout_scope", anchor.fanout_scope)
    malformed_authority = replace(production, anchor_selections=(bypassed_anchor,))
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_metadata = feedback.RuleMetadataReceipt.__new__(feedback.RuleMetadataReceipt)
    object.__setattr__(bypassed_metadata, "rule_ref", metadata.rule_ref)
    object.__setattr__(bypassed_metadata, "family_id", metadata.family_id)
    object.__setattr__(bypassed_metadata, "school", metadata.school)
    object.__setattr__(bypassed_metadata, "canon", metadata.canon)
    object.__setattr__(bypassed_metadata, "rule_type", metadata.rule_type)
    object.__setattr__(bypassed_metadata, "metadata_schema_version", metadata.metadata_schema_version)
    object.__setattr__(bypassed_metadata, "metadata_contract_version", metadata.metadata_contract_version)
    object.__setattr__(bypassed_metadata, "source_ref", metadata.source_ref)
    object.__setattr__(bypassed_metadata, "content_digest", metadata.content_digest)
    malformed_authority = replace(production, rule_metadata_receipts=(bypassed_metadata,))
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, malformed_authority, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_production = feedback.ProductionStatementAuthority.__new__(feedback.ProductionStatementAuthority)
    object.__setattr__(bypassed_production, "statement_set", production.statement_set)
    object.__setattr__(bypassed_production, "manifest", production.manifest)
    object.__setattr__(bypassed_production, "statement_refs", production.statement_refs)
    object.__setattr__(bypassed_production, "statement_set_ref", production.statement_set_ref)
    object.__setattr__(bypassed_production, "records_projection_refs", production.records_projection_refs)
    object.__setattr__(bypassed_production, "records_projection_records", production.records_projection_records)
    object.__setattr__(bypassed_production, "anchor_selections", production.anchor_selections)
    object.__setattr__(bypassed_production, "rule_metadata_receipts", production.rule_metadata_receipts)
    object.__setattr__(bypassed_production, "governing_versions", production.governing_versions)
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(production_raw.raw_submission, bypassed_production, production_raw.target_track_source_binding, production_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_preprod = feedback.PreprodRunAuthority.__new__(feedback.PreprodRunAuthority)
    object.__setattr__(bypassed_preprod, "case_id", preprod.case_id)
    object.__setattr__(bypassed_preprod, "track", preprod.track)
    object.__setattr__(bypassed_preprod, "run_id", preprod.run_id)
    object.__setattr__(bypassed_preprod, "manifest", preprod.manifest)
    object.__setattr__(bypassed_preprod, "target_refs", preprod.target_refs)
    result = feedback.bind_feedback_operation(feedback.RawFeedbackAuthority(preprod_raw.raw_submission, bypassed_preprod, preprod_raw.target_track_source_binding, preprod_raw.captured_at), prior=None, clock=_Clock())
    receipt = result.current_receipt.item_target_receipts[0]
    assert result.valid is True
    assert all(binding.status == "INVALID" for binding in result.bindings)
    assert all((item_receipt.resolution_status, item_receipt.non_bound_category) == ("INVALID", "INVALID_MATERIAL") for item_receipt in result.current_receipt.item_target_receipts)
    assert all(binding.target_object_refs == () for binding in result.bindings)
    assert all(item_receipt.graph == () for item_receipt in result.current_receipt.item_target_receipts)
    assert all(not any(type(ref) is SnapshotRef for ref in item_receipt.graph) for item_receipt in result.current_receipt.item_target_receipts)

    bypassed_binding = feedback.FeedbackBinding.__new__(feedback.FeedbackBinding)
    with pytest.raises(F09ContractError):
        feedback.validate_feedback_binding_record(bypassed_binding)
    bypassed_eligibility = feedback.LearningEligibility.__new__(feedback.LearningEligibility)
    with pytest.raises(F09ContractError):
        feedback.validate_learning_eligibility(bypassed_eligibility)

    snapshot = SnapshotRef("SNAP", "FEEDBACK", ("SNAP",), "feedback.v1", "feedback-contract.v1", _digest({"items": ({"id": "ITEM-1"},)}), _NOW, "IMMUTABLE")
    assert feedback._production_target(Explosive(), production, _NOW)[:3] == ("INVALID", "INVALID_MATERIAL", ())
    assert feedback._production_target(_item(), Explosive(), _NOW)[:3] == ("INVALID", "INVALID_MATERIAL", ())
    assert feedback._preprod_target(Explosive(), preprod, snapshot, _NOW)[:3] == ("INVALID", "INVALID_MATERIAL", ())
    assert feedback._preprod_target(_item(run_id="RUN-1"), Explosive(), snapshot, _NOW)[:3] == ("INVALID", "INVALID_MATERIAL", ())


def test_canonicalization_is_bounded_jcs_only():
    tree = ast.parse(Path("engine/f09/feedback.py").read_text(encoding="utf-8"))
    imported = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    assert not ({"json", "hashlib"} & imported)
    source = ast.unparse(tree)
    assert "bounded_jcs_sha256" in source and "parse_bounded_jcs" in source
    assert "RFC8785-JCS-UTF8" in source and "sha256" in source
    assert "source_snapshot_payload" in source
    class Custom: pass
    cycle = {}
    cycle["self"] = cycle
    too_deep = None
    for _ in range(canonical_json.MAX_DEPTH + 1):
        too_deep = (too_deep,)
    for value in (1, [], Custom(), "\ud800", cycle, too_deep):
        with pytest.raises(F09ContractError):
            canonicalize_bounded_jcs(value)
    for raw in (b'{"n":1}', b'{"x":null,"x":null}', b'\xef\xbb\xbf{}'):
        with pytest.raises(F09ContractError):
            parse_bounded_jcs(raw)
    original_snapshot = canonical_json._snapshot_dict
    try:
        canonical_json._snapshot_dict = lambda value: (_ for _ in ()).throw(RuntimeError("mutated"))
        with pytest.raises(F09ContractError) as raised:
            canonicalize_bounded_jcs({"x": None})
        assert type(raised.value) is F09ContractError
        assert raised.value.issue_code == "JCS.MUTATION_DETECTED"
    finally:
        canonical_json._snapshot_dict = original_snapshot


def test_all_digest_preimages_are_complete_and_sensitive():
    source = Path("engine/f09/feedback.py").read_text(encoding="utf-8")
    required = (
        "_digest_ref_material", "_digest_binding_material", "_versioned_object_ref_material",
        "_snapshot_ref_material", "_detected_issue_material", "_frozen_declaration_ref_material",
        "_frozen_declaration_binding_material", "_card_identity_ref_material", "_decision_trace_ref_material",
        "_standard_statement_owner_content_material", "_standard_statement_full_owner_material",
        "_statement_set_owner_content_material", "_idempotency_key_material",
        "_track_source_binding_self_excluded_material", "_feedback_item_material",
        "_feedback_submission_self_excluded_material", "_statement_projection_record_material",
        "_anchor_selection_record_material", "_governing_versions_material",
        "_rule_metadata_receipt_self_excluded_material", "_anchor_policy_material",
        "_eligibility_policy_material", "_production_authority_self_excluded_material",
        "_preprod_authority_self_excluded_material", "_feedback_binding_self_excluded_material",
        "_item_target_graph_material", "_item_target_receipt_self_excluded_material",
        "_aggregate_target_material", "_feedback_operation_receipt_self_excluded_material",
        "_learning_eligibility_self_excluded_material", "_canonical_operation_identity_material",
    )
    assert all(name in source for name in required)
    assert "digest_artifact_records(" in source
    assert "_statement_content_digest(" not in source and "_statement_set_content_digest(" not in source
    assert "asdict(" not in source and "repr(" not in source and "__dict__" not in source
    assert "vars(" not in source and "dataclasses.fields" not in source and "__dataclass_fields__" not in source
    assert "R35" not in source and "R37" not in source
    assert "r33-anchor-v1" in source and "r33-eligibility-v1" in source
    statement_fields = (
        "statement_id", "statement_revision_id", "statement_schema_version", "case_id",
        "statement_set_id", "track", "semantic_scope", "domain", "statement_text",
        "display_section", "decision_result_id", "action_id", "basis_record_ids",
        "evidence_refs", "relation_ids", "source_locator_ids", "card_identity_refs",
        "confidence_snapshot_ref", "output_precision_binding", "validation_plan_binding",
        "feedback_policy", "content_digest", "integrity", "issue_ids",
    )
    statement_set_fields = (
        "statement_set_id", "statement_schema_version", "case_id", "track",
        "source_package_ref", "decision_trace_ref", "statements", "content_digest",
        "generated_at", "publication_state", "issue_ids",
    )
    statement_content_excluded = ("statement_revision_id", "content_digest")
    statement_set_content_excluded = ("content_digest",)
    owner_tree = ast.parse(Path("engine/f09/trace.py").read_text(encoding="utf-8"))
    helpers = {node.name: node for node in owner_tree.body if isinstance(node, ast.FunctionDef)}
    statement_excluded = helpers["_statement_content_digest"].body[0].value.generators[0].ifs[0]
    set_excluded = helpers["_statement_set_content_digest"].body[0].value.generators[0].ifs[0]
    assert ast.literal_eval(statement_excluded.comparators[0]) == statement_content_excluded
    assert ast.literal_eval(set_excluded.comparators[0]) == "content_digest"

    statement = _statement()
    statement_material = feedback._standard_statement_owner_content_material(statement)
    alternate_declaration = AbsentDeclarationBinding("ABSENT", "DECLARATION_NOT_PRESENT")
    card = CardIdentityRef(
        "CARD-REF-1", "F01", _ref("CONTRACT", "CARD-CONTRACT"),
        _ref("APPENDIX", "CARD-APPENDIX"), "/card", "PRESENT_VALUE",
        FieldEvaluatorState.EVALUATED, "FROZEN_DECLARATION",
        "REFERENCE_ONLY_NOT_IMPLEMENTATION_PROOF", ("LOC-2",), ("ISSUE-2",),
    )
    statement_changes = {
        "statement_id": "STMT-CHANGED", "statement_revision_id": "REV-EXCLUDED",
        "statement_schema_version": "statement.v2", "case_id": "CASE-CHANGED",
        "statement_set_id": "SET-CHANGED", "track": RunTrack.MANUAL_IMPORT,
        "semantic_scope": "changed-scope", "domain": "wealth",
        "statement_text": "changed-text", "display_section": "changed-section",
        "decision_result_id": "DECISION-CHANGED", "action_id": "ACTION-CHANGED",
        "basis_record_ids": ("BASIS-CHANGED",),
        "evidence_refs": (_ref("EVIDENCE", "EVIDENCE-CHANGED"),),
        "relation_ids": ("RELATION-CHANGED",),
        "source_locator_ids": ("LOCATOR-CHANGED",),
        "card_identity_refs": (card,),
        "confidence_snapshot_ref": _ref("CONFIDENCE", "CONFIDENCE-CHANGED"),
        "output_precision_binding": alternate_declaration,
        "validation_plan_binding": alternate_declaration,
        "feedback_policy": "HUMAN_REVIEW_ONLY", "content_digest": _digest("SELF-EXCLUDED"),
        "integrity": "UNRESOLVED", "issue_ids": ("ISSUE-CHANGED",),
    }
    assert set(statement_changes) == set(statement_fields)
    for field_name, changed_value in statement_changes.items():
        changed_material = feedback._standard_statement_owner_content_material(
            replace(statement, **{field_name: changed_value})
        )
        if field_name in statement_content_excluded:
            assert changed_material == statement_material
        else:
            assert changed_material != statement_material

    statement_set = _statement_set((statement,))
    set_material = feedback._statement_set_owner_content_material(statement_set)
    set_changes = {
        "statement_set_id": "SET-CHANGED", "statement_schema_version": "statement.v2",
        "case_id": "CASE-CHANGED", "track": RunTrack.MANUAL_IMPORT,
        "source_package_ref": _ref("NORMALIZED_PACKAGE", "PACKAGE-CHANGED"),
        "decision_trace_ref": replace(statement_set.decision_trace_ref, action_id="ACTION-CHANGED"),
        "statements": (replace(statement, statement_revision_id="REV-FULL-MATERIAL"),),
        "content_digest": _digest("SET-SELF-EXCLUDED"),
        "generated_at": "2026-07-22T09:09:09Z", "publication_state": "BLOCKED",
        "issue_ids": ("SET-ISSUE",),
    }
    assert set(set_changes) == set(statement_set_fields)
    for field_name, changed_value in set_changes.items():
        changed_material = feedback._statement_set_owner_content_material(
            replace(statement_set, **{field_name: changed_value})
        )
        if field_name in statement_set_content_excluded:
            assert changed_material == set_material
        else:
            assert changed_material != set_material

    full_statement_material = feedback._standard_statement_full_owner_material(statement)
    assert set(full_statement_material) == set(statement_fields)
    assert feedback._standard_statement_full_owner_material(
        replace(statement, statement_revision_id="REV-FULL-MATERIAL")
    ) != full_statement_material

    authority = _production_authority()
    manifest = authority.manifest
    record = manifest.records[0]
    attempt = ArtifactWriteAttempt(
        "ATTEMPT-1", record.artifact_id, "KEY-1", 1, None,
        (_ref("INPUT", "INPUT-1"),), _NOW, None, "SUCCEEDED",
        record.observed_digest, None, None,
    )
    record = replace(record, attempts=(attempt,))
    records_digest = digest_artifact_records((record,))
    record_changes = {
        "artifact_id": "ART-CHANGED", "artifact_role": "REPORT",
        "track": RunTrack.MANUAL_IMPORT, "case_id": "CASE-CHANGED",
        "statement_set_id": "SET-CHANGED", "run_id": "RUN-CHANGED",
        "path_locator": "changed.bin", "schema_version": "records.v2",
        "expected_digest": _digest("EXPECTED-CHANGED"),
        "observed_digest": _digest("OBSERVED-CHANGED"),
        "state": ArtifactItemState.STALE, "attempts": (),
        "issue_ids": ("RECORD-ISSUE",),
    }
    assert set(record_changes) == {"artifact_id", "artifact_role", "track", "case_id", "statement_set_id", "run_id", "path_locator", "schema_version", "expected_digest", "observed_digest", "state", "attempts", "issue_ids"}
    assert all(digest_artifact_records((replace(record, **{name: value}),)) != records_digest for name, value in record_changes.items())
    attempt_changes = {
        "attempt_id": "ATTEMPT-2", "artifact_id": "ART-ATTEMPT-CHANGED",
        "idempotency_key": "KEY-2", "attempt_number": 2,
        "retry_of_attempt_id": "ATTEMPT-0", "input_snapshot_refs": (_ref("INPUT", "INPUT-2"),),
        "started_at": "2026-07-22T03:00:00Z", "finished_at": "2026-07-22T03:01:00Z",
        "outcome": "FAILED", "observed_digest": _digest("ATTEMPT-OBSERVED"),
        "error_class": "IOError", "error_message_digest": _digest("ATTEMPT-ERROR"),
    }
    assert set(attempt_changes) == {"attempt_id", "artifact_id", "idempotency_key", "attempt_number", "retry_of_attempt_id", "input_snapshot_refs", "started_at", "finished_at", "outcome", "observed_digest", "error_class", "error_message_digest"}
    assert all(digest_artifact_records((replace(record, attempts=(replace(attempt, **{name: value}),)),)) != records_digest for name, value in attempt_changes.items())
    assert digest_artifact_records(manifest.records) == manifest.digest
    assert replace(manifest, manifest_id="OTHER").digest == manifest.digest
    assert replace(manifest, key=replace(manifest.key, feedback_id="OTHER")).digest == manifest.digest
    assert replace(manifest, state=ArtifactSetState.PARTIAL).digest == manifest.digest
    assert replace(manifest, detected_issues=(DetectedIssue("X", "/x"),)).digest == manifest.digest

    submission = feedback._parse_submission(_raw(authority).raw_submission)
    anchor_policy = feedback._pinned_anchor_policy()
    eligibility_policy = feedback._pinned_eligibility_policy()
    anchor = authority.anchor_selections[0]
    changed_anchor = replace(
        anchor, selected_anchor_rule_ref=anchor.non_anchor_rule_refs[0],
        non_anchor_rule_refs=(anchor.selected_anchor_rule_ref,),
    )
    target_changed_authority = replace(
        authority, anchor_selections=(changed_anchor,),
        rule_metadata_receipts=(_metadata(changed_anchor.selected_anchor_rule_ref),),
    )
    key_material = feedback._canonical_operation_identity_material(
        manifest.key, submission, authority,
        anchor_policy, eligibility_policy,
    )
    independent_authority_material = {
        "statement_set": {
            "statement_set_id": authority.statement_set.statement_set_id,
            "content_digest": _oracle_digest_ref(authority.statement_set.content_digest),
        },
        "manifest": {"records_digest": _oracle_digest_ref(digest_artifact_records(authority.manifest.records))},
        "statement_refs": tuple(_oracle_ref(ref) for ref in authority.statement_refs),
        "statement_set_ref": _oracle_ref(authority.statement_set_ref),
        "records_projection_refs": tuple(_oracle_ref(ref) for ref in authority.records_projection_refs),
        "records_projection_records": tuple(_oracle_projection(record) for record in authority.records_projection_records),
        "anchor_selections": tuple(_oracle_anchor(record) for record in authority.anchor_selections),
        "rule_metadata_receipts": tuple({
            "material": _oracle_metadata(receipt),
            "content_digest": _oracle_digest_ref(receipt.content_digest),
        } for receipt in authority.rule_metadata_receipts),
        "governing_versions": {
            "statement_contract_version": authority.governing_versions.statement_contract_version,
            "statement_set_contract_version": authority.governing_versions.statement_set_contract_version,
            "statement_records_contract_version": authority.governing_versions.statement_records_contract_version,
            "rule_contract_version": authority.governing_versions.rule_contract_version,
        },
    }
    assert set(_oracle_digest_ref(authority.statement_set.content_digest)) == {
        "algorithm", "canonicalization", "value"
    }
    assert set(_oracle_ref(authority.statement_set_ref)) == {"object_type", "object_id", "revision_id", "schema_version", "contract_version", "digest_binding", "source_locator_id", "captured_at"}
    assert set(_oracle_projection(authority.records_projection_records[0])) == {"projection_id", "projection_type", "statement_set_id", "statement_id", "statement_revision_id", "source_statement_digest", "projected_object_ref", "transformation_id", "fidelity", "dropped_refs", "synthesized_fields", "issue_ids"}
    assert set(_oracle_anchor(authority.anchor_selections[0])) == {"anchor_selection_id", "statement_id", "statement_revision_id", "all_rule_refs", "selected_anchor_rule_ref", "non_anchor_rule_refs", "selection_policy_id", "selection_policy_version", "source_order_digest", "fidelity", "fanout_scope", "issue_ids"}
    assert set(_oracle_metadata(authority.rule_metadata_receipts[0])) == {"rule_ref", "family_id", "school", "canon", "rule_type", "metadata_schema_version", "metadata_contract_version", "source_ref", "captured_at"}
    assert _oracle_ref(replace(authority.statement_set_ref, revision_id=None))["revision_id"] is None
    assert type(independent_authority_material["statement_refs"]) is tuple
    assert type(independent_authority_material["records_projection_records"]) is tuple
    assert _oracle_projection(replace(
        authority.records_projection_records[0], transformation_id="ORACLE-CHANGED"
    )) != independent_authority_material["records_projection_records"][0]
    assert _oracle_anchor(replace(
        authority.anchor_selections[0], issue_ids=("ORACLE-CHANGED",)
    )) != independent_authority_material["anchor_selections"][0]
    assert _oracle_metadata(replace(
        authority.rule_metadata_receipts[0], canon="ORACLE-CHANGED"
    )) != independent_authority_material["rule_metadata_receipts"][0]["material"]
    assert _oracle_metadata(replace(
        authority.rule_metadata_receipts[0], content_digest=_digest("SELF-EXCLUDED")
    )) == independent_authority_material["rule_metadata_receipts"][0]["material"]
    independent_schema_material = {
        "submission": submission.source_snapshot_ref.schema_version,
        "track_source_binding": submission.track_source_binding.schema_version,
        "target_authority": "production-statement-authority.v1",
        "rule_metadata": authority.governing_versions.rule_contract_version,
        "anchor_policy": anchor_policy.schema_version,
        "eligibility_policy": eligibility_policy.schema_version,
    }
    independent_contract_material = {
        "submission": submission.source_snapshot_ref.contract_version,
        "track_source_binding": submission.track_source_binding.contract_version,
        "target_authority": "production-statement-authority.v1",
        "rule_metadata": authority.governing_versions.rule_contract_version,
        "anchor_policy": anchor_policy.contract_version,
        "eligibility_policy": eligibility_policy.contract_version,
        "statement_contract_version": authority.governing_versions.statement_contract_version,
        "statement_set_contract_version": authority.governing_versions.statement_set_contract_version,
        "statement_records_contract_version": authority.governing_versions.statement_records_contract_version,
        "rule_contract_version": authority.governing_versions.rule_contract_version,
    }
    independent_key_material = {
        "operation": manifest.key.operation,
        "case_id": manifest.key.case_id,
        "track": manifest.key.track.value,
        "source_digest": _oracle_digest_ref(manifest.key.source_digest),
        "schema_versions_digest": _oracle_digest_ref(manifest.key.schema_versions_digest),
        "contract_digest": _oracle_digest_ref(manifest.key.contract_digest),
        "statement_set_id": manifest.key.statement_set_id,
        "feedback_id": manifest.key.feedback_id,
    }
    independent_canonical_material = {
        "key": independent_key_material,
        "item_raw_identities": tuple({
            "feedback_item_id": current.feedback_item_id,
            "feedback_id": current.feedback_id,
            "source_span_locator": current.source_span_locator,
            "target_statement_id": current.target_statement_id,
            "target_statement_revision_id": current.target_statement_revision_id,
            "target_run_id": current.target_run_id,
            "target_prediction_id": current.target_prediction_id,
            "verdict": current.verdict,
            "annotation": current.annotation,
            "integrity": current.integrity,
            "issue_ids": current.issue_ids,
        } for current in sorted(submission.feedback_items, key=lambda current: current.feedback_item_id.encode("utf-16-be"))),
        "anchor_policy": (anchor_policy.policy_id, anchor_policy.policy_version),
        "eligibility_policy": (eligibility_policy.policy_id, eligibility_policy.policy_version),
        "submission_schema": submission.source_snapshot_ref.schema_version,
        "submission_contract": submission.source_snapshot_ref.contract_version,
        "governing_versions": independent_authority_material["governing_versions"],
        "source_snapshot_digest": _oracle_digest_ref(submission.source_snapshot_ref.content_digest),
        "feedback_id": submission.feedback_id,
        "case_id": submission.case_id,
        "track": submission.track.value,
        "statement_set_id": authority.statement_set.statement_set_id,
    }
    assert feedback._production_authority_self_excluded_material(authority) == independent_authority_material
    assert feedback._schema_versions_digest_material(submission, authority, anchor_policy, eligibility_policy) == independent_schema_material
    assert feedback._contract_digest_material(submission, authority, anchor_policy, eligibility_policy) == independent_contract_material
    assert key_material == independent_canonical_material
    target_changed_key_material = feedback._canonical_operation_identity_material(
        manifest.key, submission, target_changed_authority,
        anchor_policy, eligibility_policy,
    )
    assert target_changed_key_material == key_material
    forbidden = {"aggregate_target_digest", "graph_digest", "authority_digest", "manifest_digest", "content_digest"}
    def nested_keys(value):
        if type(value) is dict:
            return set(value) | set().union(*(nested_keys(item) for item in value.values()))
        if type(value) is tuple:
            return set().union(*(nested_keys(item) for item in value))
        return set()
    assert not (forbidden & nested_keys(key_material))

    malformed_digest_value = DigestRef.__new__(DigestRef)
    object.__setattr__(malformed_digest_value, "algorithm", "sha256")
    object.__setattr__(malformed_digest_value, "canonicalization", "RFC8785-JCS-UTF8")
    object.__setattr__(malformed_digest_value, "value", object())
    short_digest_value = DigestRef.__new__(DigestRef)
    object.__setattr__(short_digest_value, "algorithm", "sha256")
    object.__setattr__(short_digest_value, "canonicalization", "RFC8785-JCS-UTF8")
    object.__setattr__(short_digest_value, "value", "0" * 63)
    uppercase_digest_value = DigestRef.__new__(DigestRef)
    object.__setattr__(uppercase_digest_value, "algorithm", "sha256")
    object.__setattr__(uppercase_digest_value, "canonicalization", "RFC8785-JCS-UTF8")
    object.__setattr__(uppercase_digest_value, "value", "A" * 64)
    nonhex_digest_value = DigestRef.__new__(DigestRef)
    object.__setattr__(nonhex_digest_value, "algorithm", "sha256")
    object.__setattr__(nonhex_digest_value, "canonicalization", "RFC8785-JCS-UTF8")
    object.__setattr__(nonhex_digest_value, "value", "g" * 64)
    for malformed_digest in (
        malformed_digest_value,
        short_digest_value,
        uppercase_digest_value,
        nonhex_digest_value,
    ):
        with pytest.raises(F09ContractError) as failure:
            feedback._digest_ref_material(malformed_digest)
        assert type(failure.value) is F09ContractError

    leaf_material_oracles = (
        (feedback._digest_ref_material, statement.content_digest, replace(statement.content_digest, value="1" * 64), {"algorithm", "canonicalization", "value"}),
        (feedback._digest_binding_material, authority.statement_refs[0].digest_binding, DigestPresent("PRESENT", _digest("other-binding")), {"status", "digest"}),
        (feedback._versioned_object_ref_material, authority.statement_refs[0], replace(authority.statement_refs[0], source_locator_id="OTHER"), {"object_type", "object_id", "revision_id", "schema_version", "contract_version", "digest_binding", "source_locator_id", "captured_at"}),
        (feedback._snapshot_ref_material, submission.source_snapshot_ref, replace(submission.source_snapshot_ref, captured_at="2026-07-22T09:00:00Z"), {"source_snapshot_id", "source_type", "source_locator_ids", "schema_version", "contract_version", "content_digest", "captured_at", "immutability"}),
        (feedback._detected_issue_material, DetectedIssue("ISSUE", "/one"), DetectedIssue("ISSUE", "/two"), {"issue_code", "field_path"}),
        (feedback._frozen_declaration_binding_material, statement.output_precision_binding, alternate_declaration, {"presence", "reason_code"}),
        (feedback._card_identity_ref_material, card, replace(card, field_path="/other"), {"card_identity_ref_id", "card_id", "normative_contract_ref", "machine_appendix_ref", "field_path", "source_field_state", "evaluator_state", "declaration_status", "runtime_capability_status", "source_locator_ids", "issue_ids"}),
        (feedback._decision_trace_ref_material, statement_set.decision_trace_ref, replace(statement_set.decision_trace_ref, action_id="ACTION-OTHER"), {"result_ref", "action_id", "selected_action", "basis_record_ids", "blocking_issue_ids", "nonblocking_issue_ids", "source_decision_refs", "output_precision_binding", "validation_plan_binding", "structural_validity"}),
        (lambda key: feedback._idempotency_key_material(key, False), manifest.key, replace(manifest.key, feedback_id="FEEDBACK-OTHER"), {"operation", "case_id", "track", "source_digest", "schema_versions_digest", "contract_digest", "statement_set_id", "feedback_id"}),
    )
    for material, original, changed, expected_keys in leaf_material_oracles:
        original_material = material(original)
        assert set(original_material) == expected_keys
        assert material(changed) != original_material
        assert bounded_jcs_sha256(material(changed)) != bounded_jcs_sha256(original_material)
    assert set(feedback._idempotency_key_material(manifest.key, True)) == {"operation", "case_id", "track", "source_digest", "schema_versions_digest", "contract_digest", "statement_set_id", "feedback_id", "canonical_key_digest"}

    operation = _bind(authority).current_receipt
    binding = operation.bindings[0]
    resignable_binding_mutations = (
        replace(binding, feedback_binding_id="FEEDBACK-BINDING:OTHER"),
        replace(binding, feedback_item_ref=replace(binding.feedback_item_ref, object_type="OTHER")),
        replace(binding, feedback_item_ref=replace(binding.feedback_item_ref, object_id="OTHER")),
        replace(binding, feedback_item_ref=replace(binding.feedback_item_ref, revision_id="rev-2")),
        replace(binding, feedback_item_ref=replace(binding.feedback_item_ref, schema_version="feedback-item.v2")),
        replace(binding, feedback_item_ref=replace(binding.feedback_item_ref, contract_version="wrong")),
        replace(binding, feedback_item_ref=replace(binding.feedback_item_ref, digest_binding=DigestMissing("MISSING", None, "MISSING"))),
        replace(binding, feedback_item_ref=replace(binding.feedback_item_ref, source_locator_id="forbidden")),
        replace(binding, source_track_binding_ref=replace(binding.source_track_binding_ref, object_type="OTHER")),
        replace(binding, source_track_binding_ref=replace(binding.source_track_binding_ref, revision_id="rev-2")),
        replace(binding, source_track_binding_ref=replace(binding.source_track_binding_ref, digest_binding=DigestMissing("MISSING", None, "MISSING"))),
        replace(binding, source_track_binding_ref=replace(binding.source_track_binding_ref, source_locator_id="forbidden")),
        replace(
            binding,
            target_track_source_binding=replace(
                binding.target_track_source_binding,
                track=RunTrack.V5_V6_PREPROD,
                content_digest=_digest(feedback._track_source_binding_self_excluded_material(replace(
                    binding.target_track_source_binding,
                    track=RunTrack.V5_V6_PREPROD,
                ))),
            ),
        ),
    )
    binding_mutations = tuple(
        replace(malformed, content_digest=_digest(feedback._feedback_binding_self_excluded_material(malformed)))
        for malformed in resignable_binding_mutations
    ) + (
        replace(binding, feedback_item_ref=replace(binding.feedback_item_ref, captured_at="")),
        replace(binding, source_track_binding_ref=replace(binding.source_track_binding_ref, contract_version="")),
        replace(binding, source_track_binding_ref=replace(binding.source_track_binding_ref, captured_at="")),
    )
    for malformed_binding in binding_mutations:
        with pytest.raises(F09ContractError) as failure:
            feedback.validate_feedback_binding_record(malformed_binding)
        assert type(failure.value) is F09ContractError
    target_receipt = operation.item_target_receipts[0]
    eligibility = _eligibility(binding, authority)
    preprod = _preprod_authority()
    material_oracles = (
        (feedback._track_source_binding_self_excluded_material, submission.track_source_binding, replace(submission.track_source_binding, captured_at="2026-07-22T09:00:00Z"), "content_digest", {"track_source_binding_id", "side", "track", "state", "source_evidence_ref", "parser_ref", "schema_version", "contract_version", "state_reason_codes", "captured_at"}),
        (feedback._feedback_submission_self_excluded_material, submission, replace(submission, parser_version="v2"), "content_digest", {"feedback_id", "case_id", "track", "track_source_binding", "source_snapshot_ref", "source_snapshot_payload", "parser_id", "parser_version", "feedback_items", "captured_at"}),
        (feedback._statement_projection_record_material, authority.records_projection_records[0], replace(authority.records_projection_records[0], transformation_id="OTHER"), None, {"projection_id", "projection_type", "statement_set_id", "statement_id", "statement_revision_id", "source_statement_digest", "projected_object_ref", "transformation_id", "fidelity", "dropped_refs", "synthesized_fields", "issue_ids"}),
        (feedback._anchor_selection_record_material, authority.anchor_selections[0], replace(authority.anchor_selections[0], issue_ids=("OTHER",)), None, {"anchor_selection_id", "statement_id", "statement_revision_id", "all_rule_refs", "selected_anchor_rule_ref", "non_anchor_rule_refs", "selection_policy_id", "selection_policy_version", "source_order_digest", "fidelity", "fanout_scope", "issue_ids"}),
        (feedback._governing_versions_material, authority.governing_versions, replace(authority.governing_versions, rule_contract_version="rule.v2"), None, {"statement_contract_version", "statement_set_contract_version", "statement_records_contract_version", "rule_contract_version"}),
        (feedback._rule_metadata_receipt_self_excluded_material, authority.rule_metadata_receipts[0], replace(authority.rule_metadata_receipts[0], canon="other"), "content_digest", {"rule_ref", "family_id", "school", "canon", "rule_type", "metadata_schema_version", "metadata_contract_version", "source_ref", "captured_at"}),
        (feedback._anchor_policy_material, feedback._pinned_anchor_policy(), replace(feedback._pinned_anchor_policy(), schema_version="other"), "content_digest", {"policy_id", "policy_version", "required_rule_object_type", "required_fidelity", "required_fanout_scope", "schema_version", "contract_version"}),
        (feedback._eligibility_policy_material, feedback._pinned_eligibility_policy(), replace(feedback._pinned_eligibility_policy(), contract_version="other"), "content_digest", {"policy_id", "policy_version", "allowed_track", "required_feedback_policy", "human_review_on_ambiguous", "human_review_on_invalid", "human_review_on_unknown_track", "schema_version", "contract_version"}),
        (feedback._production_authority_self_excluded_material, authority, replace(authority, governing_versions=replace(authority.governing_versions, rule_contract_version="rule.v2")), "content_digest", {"statement_set", "manifest", "statement_refs", "statement_set_ref", "records_projection_refs", "records_projection_records", "anchor_selections", "rule_metadata_receipts", "governing_versions"}),
        (feedback._preprod_authority_self_excluded_material, preprod, replace(preprod, run_id="RUN-2"), "content_digest", {"case_id", "track", "run_id", "manifest", "target_refs"}),
        (feedback._feedback_binding_self_excluded_material, binding, replace(binding, issue_ids=("OTHER",)), "content_digest", {"feedback_binding_id", "feedback_item_ref", "binding_protocol", "source_track_binding_ref", "target_track_source_binding", "case_match", "track_match", "run_match", "statement_match", "revision_match", "statement_set_match", "artifact_digest_match", "target_object_refs", "record_anchor_ref", "status", "issue_ids", "detected_issues"}),
        (feedback._item_target_receipt_self_excluded_material, target_receipt, replace(target_receipt, feedback_item_id="ITEM-OTHER"), "content_digest", {"feedback_item_id", "protocol", "target_statement_id", "target_statement_revision_id", "target_run_id", "target_prediction_id", "resolution_status", "non_bound_category", "graph", "graph_digest"}),
        (feedback._feedback_operation_receipt_self_excluded_material, operation, replace(operation, created_at="2026-07-22T09:00:00Z"), "content_digest", {"operation_id", "key", "source_digest", "authority_digest", "item_target_receipts", "aggregate_target_digest", "bindings", "anchor_policy_ref", "eligibility_policy_ref", "created_at"}),
        (feedback._learning_eligibility_self_excluded_material, eligibility, replace(eligibility, evaluated_at="2026-07-22T09:00:00Z"), "content_digest", {"eligibility_id", "feedback_binding_id", "feedback_binding_digest", "policy_id", "policy_version", "status", "learning_target_refs", "excluded_supporting_rule_refs", "blocking_reason_codes", "detected_issues", "evaluated_at"}),
    )
    for material, original, changed, excluded_self, expected_keys in material_oracles:
        original_material = material(original)
        assert set(original_material) == expected_keys
        assert material(changed) != original_material
        assert bounded_jcs_sha256(material(changed)) != bounded_jcs_sha256(original_material)
        if excluded_self is not None:
            assert material(replace(original, **{excluded_self: _digest("changed-self")})) == original_material
    anchor_policy = feedback._pinned_anchor_policy()
    policy_identity = feedback._policy_digest_identity_material(anchor_policy)
    assert set(policy_identity) == {"policy_id", "policy_version", "schema_version", "contract_version", "content_digest"}
    assert feedback._policy_digest_identity_material(replace(anchor_policy, content_digest=_digest("other-policy"))) != policy_identity
    schema_material = feedback._schema_versions_digest_material(submission, authority, anchor_policy, feedback._pinned_eligibility_policy())
    contract_material = feedback._contract_digest_material(submission, authority, anchor_policy, feedback._pinned_eligibility_policy())
    assert set(schema_material) == {"submission", "track_source_binding", "target_authority", "rule_metadata", "anchor_policy", "eligibility_policy"}
    assert set(contract_material) == {"submission", "track_source_binding", "target_authority", "rule_metadata", "anchor_policy", "eligibility_policy", "statement_contract_version", "statement_set_contract_version", "statement_records_contract_version", "rule_contract_version"}
    item = submission.feedback_items[0]
    changed_submission = replace(submission, feedback_items=(replace(item, verdict="REJECT"),))
    assert feedback._canonical_operation_identity_material(manifest.key, changed_submission, authority, anchor_policy, feedback._pinned_eligibility_policy()) != key_material

    item_material = feedback._feedback_item_material(item)
    assert set(item_material) == {"feedback_item_id", "feedback_id", "source_span_locator", "target_statement_id", "target_statement_revision_id", "target_run_id", "target_prediction_id", "verdict", "annotation", "integrity", "issue_ids"}
    assert feedback._feedback_item_material(replace(item, verdict="REJECT")) != item_material
    graph_material = feedback._item_target_graph_material("PRODUCTION_STATEMENT", item, "BOUND", None, target_receipt.graph)
    assert set(graph_material) == {"protocol", "raw_target_identity", "resolution_status", "non_bound_category", "graph"}
    assert feedback._item_target_graph_material("PRODUCTION_STATEMENT", replace(item, target_prediction_id="PRED-2"), "BOUND", None, target_receipt.graph) != graph_material
    aggregate_material = feedback._aggregate_target_material(operation.item_target_receipts)
    changed_receipt = replace(target_receipt, feedback_item_id="ITEM-OTHER")
    changed_receipt = replace(changed_receipt, content_digest=_digest(feedback._item_target_receipt_self_excluded_material(changed_receipt)))
    assert feedback._aggregate_target_material((changed_receipt,)) != aggregate_material


def test_prior_and_current_recompute_from_independent_raw_authorities():
    authority = _production_authority()
    prior_raw = _raw(authority)
    receipt = feedback.bind_feedback_operation(prior_raw, prior=None, clock=_Clock()).current_receipt
    independently_changed_prior_raw = _raw(authority, items=(replace(_item(), annotation="different-prior-raw"),))
    prior = feedback.PriorFeedbackOperation(independently_changed_prior_raw, receipt)
    with pytest.raises(F09IntegrityError) as raised:
        feedback.bind_feedback_operation(_raw(authority), prior=prior, clock=_Clock())
    assert raised.value.field_path == "/prior/receipt"


def test_reused_returns_prior_bindings_by_identity():
    authority = _production_authority()
    raw = _raw(authority)
    receipt = feedback.bind_feedback_operation(raw, prior=None, clock=_Clock()).current_receipt
    prior = feedback.PriorFeedbackOperation(raw, receipt)
    reused = feedback.bind_feedback_operation(raw, prior=prior, clock=_Clock())
    assert reused.current_receipt is receipt
    assert reused.bindings is receipt.bindings
    assert all(current is previous for current, previous in zip(reused.bindings, receipt.bindings))


def test_policy_trust_boundaries_are_independent_and_not_caller_signed():
    anchor = feedback._pinned_anchor_policy()
    eligibility = feedback._pinned_eligibility_policy()
    assert anchor.policy_id != eligibility.policy_id
    assert anchor.content_digest != eligibility.content_digest
    assert "R33" in feedback._PINNED_ANCHOR_OBJECT_ID
    assert "R33" in feedback._PINNED_ELIGIBILITY_OBJECT_ID
    assert "policy" not in inspect.signature(feedback.bind_feedback_operation).parameters


def test_no_side_effect_import_or_runtime_surface():
    tree = ast.parse(Path("engine/f09/feedback.py").read_text(encoding="utf-8"))
    roots = {alias.name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    roots |= {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    assert not ({"os", "pathlib", "subprocess", "socket", "sqlite3", "requests", "tools", "time", "datetime"} & roots)
    assert not any(name in Path("engine/f09/feedback.py").read_text(encoding="utf-8") for name in ("open(", "write(", "unlink(", "mkdir(", "system("))


def test_restricted_context_contract_ast_is_exact():
    source = Path("engine/f09/feedback.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    context = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "_PreprodRestrictedManifestContext")
    assert tuple(field.target.id for field in context.body if isinstance(field, ast.AnnAssign) and isinstance(field.target, ast.Name)) == (
        "authority", "manifest", "case_id", "run_id", "track", "key", "roles", "verifier_returned_records_digest",
    )
    assert "restricted=" not in source and "environ" not in source and "globals(" not in source


def _restricted_context_builder_callers(tree):
    return tuple(
        definition.name
        for definition in tree.body
        if isinstance(definition, ast.FunctionDef)
        if any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_validated_preprod_restricted_manifest_context"
            for node in ast.walk(definition)
        )
    )


def test_restricted_context_call_graph_has_one_orchestrator_site():
    tree = ast.parse(Path("engine/f09/feedback.py").read_text(encoding="utf-8"))
    assert _restricted_context_builder_callers(tree) == (
        "_preprod_authority_self_excluded_material",
    )


def test_restricted_context_helpers_revalidate_bound_objects():
    source = Path("engine/f09/feedback.py").read_text(encoding="utf-8")
    assert "type(context) is not _PreprodRestrictedManifestContext" in source
    assert "context.authority is not authority" in source
    assert "context.manifest is not manifest" in source
    assert "verified_digest = context.verifier_returned_records_digest" in source


def test_feedback_adapter_uses_public_run_manifest_verifier_only():
    tree = ast.parse(Path("engine/f09/feedback.py").read_text(encoding="utf-8"))
    artifact_imports = [alias.name for node in tree.body if isinstance(node, ast.ImportFrom) and node.module == "engine.f09.artifacts" for alias in node.names]
    assert "validate_run_artifact_manifest_v1" in artifact_imports
    assert not any(name.startswith("_") for name in artifact_imports)
    assert "_digest_run_artifact_set_key_v1" not in Path("engine/f09/feedback.py").read_text(encoding="utf-8")


def test_restricted_authority_material_invokes_public_manifest_verifier_once(monkeypatch):
    authority = _verified_preprod_authority()
    calls = []
    original = feedback.validate_run_artifact_manifest_v1
    monkeypatch.setattr(
        feedback,
        "validate_run_artifact_manifest_v1",
        lambda manifest: calls.append(manifest) or original(manifest),
    )

    feedback._preprod_authority_self_excluded_material(authority)

    assert calls == [authority.manifest]


def test_r40_issuance_failure_stops_before_owner_manifest_verification(monkeypatch):
    manifest = provision_verified_run_manifest_fixture_v1()
    result = RunArtifactSetResultV1(
        manifest,
        (),
        IssuedRunArtifactSetProofV1("Ed25519", "key-1", "signature"),
    )
    issuance_failure = F09ContractError(
        "RUN_ARTIFACT_SET_SIGNING_FAILED", "issuance_proof", "invalid issuance",
    )
    manifest_verifier_calls = 0
    authority_construction_calls = 0

    def reject_issuance(value):
        assert value is result
        raise issuance_failure

    def count_manifest_verifier(_manifest):
        nonlocal manifest_verifier_calls
        manifest_verifier_calls += 1
        raise AssertionError("manifest verification must not run after issuance failure")

    def count_authority_construction(*_args, **_kwargs):
        nonlocal authority_construction_calls
        authority_construction_calls += 1
        raise AssertionError("authority construction must not run after issuance failure")

    monkeypatch.setattr(
        feedback,
        "validate_run_artifact_set_result_issuance_v1",
        reject_issuance,
        raising=False,
    )
    monkeypatch.setattr(feedback, "validate_run_artifact_manifest_v1", count_manifest_verifier)
    monkeypatch.setattr(feedback, "PreprodRunAuthority", count_authority_construction)

    with pytest.raises(F09ContractError) as caught:
        feedback.construct_preprod_run_authority_v1(run_artifact_set_result=result)

    assert caught.value is issuance_failure
    assert manifest_verifier_calls == 0
    assert authority_construction_calls == 0


def test_r40_constructs_authority_after_issuance_and_one_manifest_verification(monkeypatch):
    expected = _verified_preprod_authority()
    result = RunArtifactSetResultV1(
        expected.manifest,
        expected.target_refs,
        IssuedRunArtifactSetProofV1("Ed25519", "key-1", "signature"),
    )
    issuance_calls = 0
    manifest_verifier_calls = 0
    owner_helper_calls = 0
    real_manifest_verifier = feedback.validate_run_artifact_manifest_v1
    real_owner_helper = feedback._preprod_authority_self_excluded_material

    def count_issuance(value):
        nonlocal issuance_calls
        assert value is result
        issuance_calls += 1

    def count_manifest_verifier(manifest):
        nonlocal manifest_verifier_calls
        manifest_verifier_calls += 1
        return real_manifest_verifier(manifest)

    def count_owner_helper(authority, **kwargs):
        nonlocal owner_helper_calls
        owner_helper_calls += 1
        return real_owner_helper(authority, **kwargs)

    def forbidden_downstream(*_args, **_kwargs):
        raise AssertionError("R40 constructor must not enter binding or learning")

    monkeypatch.setattr(feedback, "validate_run_artifact_set_result_issuance_v1", count_issuance)
    monkeypatch.setattr(feedback, "validate_run_artifact_manifest_v1", count_manifest_verifier)
    monkeypatch.setattr(feedback, "_preprod_authority_self_excluded_material", count_owner_helper)
    for name in (
        "bind_feedback_operation",
        "evaluate_learning_eligibility",
        "validate_learning_eligibility",
    ):
        monkeypatch.setattr(feedback, name, forbidden_downstream)

    authority = feedback.construct_preprod_run_authority_v1(run_artifact_set_result=result)

    assert issuance_calls == 1
    assert manifest_verifier_calls == 1
    assert owner_helper_calls == 1
    assert authority.case_id == expected.case_id
    assert authority.track is expected.track
    assert authority.run_id == expected.run_id
    assert authority.manifest is result.manifest
    assert authority.target_refs is result.target_refs
    assert authority.content_digest == bounded_jcs_sha256(
        feedback._preprod_authority_self_excluded_material(authority)
    )


def test_r40_constructor_explicitly_rechecks_returned_restricted_context_digest():
    tree = ast.parse(Path("engine/f09/feedback.py").read_text(encoding="utf-8"))
    constructor = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "construct_preprod_run_authority_v1"
    )
    attributes = {
        (node.value.id, node.attr)
        for node in ast.walk(constructor)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
    }
    assert (
        "restricted_context",
        "verifier_returned_records_digest",
    ) in attributes


def test_r40_constructor_static_contract_boundary_is_exact():
    signature = inspect.signature(feedback.construct_preprod_run_authority_v1)
    assert tuple(signature.parameters) == ("run_artifact_set_result",)
    parameter = signature.parameters["run_artifact_set_result"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty
    assert get_type_hints(feedback.construct_preprod_run_authority_v1) == {
        "run_artifact_set_result": RunArtifactSetResultV1,
        "return": feedback.PreprodRunAuthority,
    }

    tree = ast.parse(Path("engine/f09/feedback.py").read_text(encoding="utf-8"))
    constructor = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "construct_preprod_run_authority_v1"
    )
    source = ast.unparse(constructor)
    assert "type(run_artifact_set_result) is not RunArtifactSetResultV1" in source
    calls = {
        node.func.id
        for node in ast.walk(constructor)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert calls.isdisjoint(
        {
            "validate_run_artifact_manifest_v1",
            "bind_feedback_operation",
            "evaluate_learning_eligibility",
            "validate_learning_eligibility",
        }
    )
    artifact_imports = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "engine.f09.artifacts"
        for alias in node.names
    }
    assert not any(name.startswith("_") for name in artifact_imports)


def test_restricted_full_operation_invokes_public_manifest_verifier_once(monkeypatch):
    authority = _verified_preprod_authority()
    raw = _raw(authority)
    calls = []
    original = feedback.validate_run_artifact_manifest_v1
    monkeypatch.setattr(
        feedback,
        "validate_run_artifact_manifest_v1",
        lambda manifest: calls.append(manifest) or original(manifest),
    )

    result = feedback.bind_feedback_operation(raw, prior=None, clock=_Clock())

    assert result.valid is True
    assert calls == [authority.manifest]


def test_bind_feedback_operation_manifest_verifier_typed_failure_stops_before_all_downstream_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _verified_preprod_authority()
    raw = _raw(authority)
    sentinel = F09IntegrityError("ARTIFACT.MANIFEST_INVALID", "/manifest", "sentinel")
    verifier_calls = []
    downstream = {
        "invalid_material": {"calls": 0, "outputs": 0},
        "key": {"calls": 0, "outputs": 0},
        "binding": {"calls": 0, "outputs": 0},
        "receipt": {"calls": 0, "outputs": 0},
        "eligibility": {"calls": 0, "inputs": 0, "outputs": 0},
        "learning": {"calls": 0, "outputs": 0},
    }

    def verifier(manifest):
        verifier_calls.append(manifest)
        raise sentinel

    def forbidden(category):
        def probe(*_args, **_kwargs):
            downstream[category]["calls"] += 1
            if category == "eligibility":
                downstream[category]["inputs"] += 1
            pytest.fail(f"R42-F08 must not construct or call {category}")
        return probe

    monkeypatch.setattr(feedback, "validate_run_artifact_manifest_v1", verifier)
    for name in (
        "_invalid_authority_material",
        "_invalid_schema_versions_digest_material",
        "_invalid_contract_digest_material",
        "_invalid_canonical_operation_identity_material",
    ):
        monkeypatch.setattr(feedback, name, forbidden("invalid_material"))
    for name in ("IdempotencyKey", "_canonical_operation_identity_material"):
        monkeypatch.setattr(feedback, name, forbidden("key"))
    for name in ("FeedbackBinding", "validate_feedback_binding_record"):
        monkeypatch.setattr(feedback, name, forbidden("binding"))
    for name in ("_make_target_receipt", "FeedbackOperationReceipt"):
        monkeypatch.setattr(feedback, name, forbidden("receipt"))
    for name in ("evaluate_learning_eligibility", "validate_learning_eligibility"):
        monkeypatch.setattr(feedback, name, forbidden("eligibility"))
    monkeypatch.setattr(feedback, "LearningEligibility", forbidden("learning"))

    with pytest.raises(F09IntegrityError) as caught:
        feedback.bind_feedback_operation(raw, prior=None, clock=_Clock())

    assert caught.value is sentinel
    assert verifier_calls == [authority.manifest]
    assert downstream == {
        "invalid_material": {"calls": 0, "outputs": 0},
        "key": {"calls": 0, "outputs": 0},
        "binding": {"calls": 0, "outputs": 0},
        "receipt": {"calls": 0, "outputs": 0},
        "eligibility": {"calls": 0, "inputs": 0, "outputs": 0},
        "learning": {"calls": 0, "outputs": 0},
    }


def test_static_accounting_is_exactly_23_plus_94():
    module = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    nodes = [node for node in module.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")]
    structural = [node for node in nodes if node.name != "test_contract_falsifier_ledger"]
    assert len(structural) == 23
    assert len(CONTRACT_FALSIFIERS) == 94
    assert len(structural) + len(CONTRACT_FALSIFIERS) == 117
    assert tuple(case_id for case_id, _ in CONTRACT_FALSIFIERS) == tuple(f"P{index:02d}" for index in range(1, 95))


CONTRACT_FALSIFIERS = (
    ("P01", "production_complete_bound"), ("P02", "preprod_snapshot_only_bound"),
    ("P03", "unknown_statement_unbound"), ("P04", "missing_revision_unknown"),
    ("P05", "old_revision_mismatch_issue"), ("P06", "duplicate_candidates_ambiguous"),
    ("P07", "malformed_statement_ref_invalid"), ("P08", "statement_owner_digest_exclusions"),
    ("P09", "statement_contract_mismatch"), ("P10", "set_case_mismatch"),
    ("P11", "set_track_mismatch"), ("P12", "set_owner_digest_nested_full"),
    ("P13", "set_contract_mismatch"), ("P14", "records_artifact_missing"),
    ("P15", "records_artifact_duplicate"), ("P16", "records_artifact_nonverified"),
    ("P17", "records_expected_missing"), ("P18", "records_observed_missing"),
    ("P19", "records_digest_unequal"), ("P20", "records_dimensions_independent"),
    ("P21", "ref_artifact_id_mismatch"), ("P22", "projection_type_invalid"),
    ("P23", "projection_identity_mismatch"), ("P24", "projection_digest_mismatch"),
    ("P25", "anchor_missing"), ("P26", "anchor_multiple"),
    ("P27", "anchor_unsupported_none"), ("P28", "anchor_empty_rules"),
    ("P29", "anchor_duplicate_rules"), ("P30", "anchor_selected_absent"),
    ("P31", "anchor_selected_twice"), ("P32", "anchor_nonanchor_order"),
    ("P33", "anchor_source_order_digest"), ("P34", "anchor_selected_not_rule"),
    ("P35", "rule_contract_mismatch"), ("P36", "metadata_missing_ineligible"),
    ("P37", "metadata_multiple_human_review"), ("P38", "metadata_blank_identity"),
    ("P39", "metadata_unmapped"), ("P40", "metadata_coherence"),
    ("P41", "resolved_track_match"), ("P42", "track_mismatch_issue"),
    ("P43", "source_missing_unknown"), ("P44", "target_unparsable_unknown"),
    ("P45", "source_ambiguous"), ("P46", "source_integrity_failed"),
    ("P47", "resolved_with_reason_invalid"), ("P48", "wrong_reason_invalid"),
    ("P49", "source_side_track_parser"), ("P50", "target_side_invalid"),
    ("P51", "payload_digest_or_locator_invalid"), ("P52", "pointer_missing_scalar_blank_root"),
    ("P53", "preprod_missing_run"), ("P54", "preprod_snapshot_cardinality"),
    ("P55", "preprod_duplicate_refs_roles"), ("P56", "preprod_mixed_dimensions"),
    ("P57", "preprod_ref_record_or_forbidden"), ("P58", "preprod_optional_decision_order"),
    ("P59", "preprod_ineligible"), ("P60", "policies_positive_eligible"),
    ("P61", "feedback_policy_forbidden"), ("P62", "caller_policy_injection"),
    ("P63", "policy_swap_or_provider"), ("P64", "production_ambiguous_review"),
    ("P65", "invalid_unknown_track_eligibility"), ("P66", "initial_new"),
    ("P67", "changed_source_new"), ("P68", "raw_revision_changes_key"),
    ("P69", "same_key_same_aggregate_reused_identity"), ("P70", "same_key_changed_target_mismatch"),
    ("P71", "restricted_context_exact_runtime_type_required"), ("P72", "restricted_context_subclass_or_proxy_rejected"),
    ("P73", "restricted_context_authority_identity_rechecked"), ("P74", "restricted_context_manifest_identity_rechecked"),
    ("P75", "restricted_context_stale_case_material_rejected"), ("P76", "restricted_context_stale_run_track_key_roles_material_rejected"),
    ("P77", "restricted_helper_direct_call_rejected"), ("P78", "restricted_call_graph_unique_orchestrator_site"),
    ("P79", "public_run_manifest_verifier_accepts_exact_verified_run_manifest"), ("P80", "public_run_manifest_verifier_rejects_non_run_operation"),
    ("P81", "public_run_manifest_verifier_rejects_invalid_run_role_closure"), ("P82", "public_run_manifest_verifier_rejects_attempt_refs_graph_mismatch"),
    ("P83", "public_run_manifest_verifier_rejects_case_track_run_or_state_mismatch"), ("P84", "public_run_manifest_verifier_preserves_legacy_statement_bytes"),
    ("P85", "public_run_manifest_verifier_rejects_run_legacy_digest_cross_swap"), ("P86", "manifest_outer_ref_valid_restricted_regression"),
    ("P87", "manifest_outer_ref_identity_mismatch_regression"), ("P88", "manifest_outer_ref_duplicate_or_self_record_regression"),
    ("P89", "ordinary_target_refs_record_matching_regression"), ("P90", "feedback_adapter_has_no_artifacts_private_helper_import"),
    ("P91", "feedback_adapter_has_no_run_serializer_or_digest_copy"), ("P92", "feedback_adapter_stops_without_frozen_public_verifier"),
    ("P93", "feedback_adapter_calls_only_public_run_manifest_verifier"), ("P94", "serial_owner_gate_preserves_zero_binding_learning_calls"),
)


@pytest.mark.parametrize("case_id,falsifier", CONTRACT_FALSIFIERS, ids=[f"P{index:02d}" for index in range(1, 95)])
def test_contract_falsifier_ledger(case_id, falsifier):
    """One collected node with ninety-four independently addressed executable oracles."""
    authority = _production_authority()
    item = _item()

    if case_id == "P01":
        result = _bind(authority)
        binding = _binding(result)
        receipt = result.current_receipt.item_target_receipts[0]
        assert binding.status == "BOUND"
        assert (binding.case_match, binding.track_match, binding.run_match) == ("MATCH", "MATCH", "NOT_APPLICABLE")
        assert (binding.statement_match, binding.revision_match, binding.statement_set_match, binding.artifact_digest_match) == ("MATCH", "MATCH", "MATCH", "MATCH")
        assert tuple(ref.object_type for ref in binding.target_object_refs) == ("STATEMENT", "STATEMENT_SET", "STATEMENT_RECORDS")
        assert binding.record_anchor_ref.object_type == "RULE"
        assert receipt.resolution_status == "BOUND" and receipt.non_bound_category is None
        assert tuple(ref.object_type for ref in receipt.graph) == ("STATEMENT", "STATEMENT_SET", "STATEMENT_RECORDS", "RULE")
        assert receipt.graph_digest == _digest(feedback._item_target_graph_material("PRODUCTION_STATEMENT", item, "BOUND", None, receipt.graph))
        return

    if case_id == "P02":
        result = _bind(_preprod_authority())
        binding = _binding(result)
        assert binding.status == "BOUND"
        assert (binding.case_match, binding.track_match, binding.run_match, binding.artifact_digest_match) == ("MATCH", "MATCH", "MATCH", "MATCH")
        assert (binding.statement_match, binding.revision_match, binding.statement_set_match) == ("NOT_APPLICABLE",) * 3
        assert tuple(ref.object_type for ref in binding.target_object_refs) == ("RUN_SNAPSHOT",)
        assert result.current_receipt.item_target_receipts[0].graph == binding.target_object_refs
        return

    if case_id in {"P03", "P05", "P42"}:
        control = _item(item_id="ITEM-0", locator="SNAP#/items/0")
        if case_id == "P03":
            changed = _item(item_id="ITEM-1", statement_id="UNKNOWN", locator="SNAP#/items/1")
            expected = DetectedIssue("FEEDBACK.TARGET_UNBOUND", "/feedback_bindings/1")
        elif case_id == "P05":
            changed = _item(item_id="ITEM-1", revision="rev-old", locator="SNAP#/items/1")
            expected = DetectedIssue("FEEDBACK.REVISION_MISMATCH", "/feedback_bindings/1/revision_match")
        else:
            second = _statement(statement_id="STMT-2", revision="rev-stmt-2", track=RunTrack.V5_V6_PREPROD)
            statement_set = _statement_set((authority.statement_set.statements[0], second))
            second_ref = _ref(
                "STATEMENT", "STMT-2", revision="rev-stmt-2",
                schema="statement.v1", contract="statement.v1",
                digest=second.content_digest,
            )
            second_record_digest = _digest("statement-records-preprod")
            second_record = ArtifactRecord(
                "ART-RECORDS-PREPROD", "STATEMENT_RECORDS", RunTrack.V5_V6_PREPROD,
                "CASE-1", "SET-1", None, "statement_records_preprod.bin",
                "records.v1", second_record_digest, second_record_digest,
                ArtifactItemState.VERIFIED, (), (),
            )
            second_artifact_ref = _ref(
                "STATEMENT_RECORDS", "ART-RECORDS-PREPROD",
                schema="records.v1", contract="records.v1", digest=second_record_digest,
            )
            second_projection = replace(
                authority.records_projection_records[0],
                projection_id="PROJECTION-2",
                statement_id="STMT-2",
                statement_revision_id="rev-stmt-2",
                source_statement_digest=second.content_digest,
                projected_object_ref=second_artifact_ref,
            )
            second_selected = _ref("RULE", "RULE-3", contract="rule.v1")
            second_supporting = _ref("RULE", "RULE-4", contract="rule.v1")
            second_rules = (second_supporting, second_selected)
            second_anchor = replace(
                authority.anchor_selections[0],
                anchor_selection_id="ANCHOR-2",
                statement_id="STMT-2",
                statement_revision_id="rev-stmt-2",
                all_rule_refs=second_rules,
                selected_anchor_rule_ref=second_selected,
                non_anchor_rule_refs=(second_supporting,),
                source_order_digest=_digest(tuple(
                    feedback._versioned_object_ref_material(ref)
                    for ref in second_rules
                )),
            )
            candidate = replace(
                authority,
                statement_set=statement_set,
                statement_set_ref=replace(
                    authority.statement_set_ref,
                    digest_binding=DigestPresent(
                        "PRESENT", statement_set.content_digest
                    ),
                ),
                statement_refs=authority.statement_refs + (second_ref,),
                manifest=_manifest(authority.manifest.records + (second_record,)),
                records_projection_refs=authority.records_projection_refs + (second_artifact_ref,),
                records_projection_records=authority.records_projection_records + (second_projection,),
                anchor_selections=authority.anchor_selections + (second_anchor,),
                rule_metadata_receipts=authority.rule_metadata_receipts + (_metadata(second_selected),),
            )
            candidate = _resign_authority(candidate)
            changed = _item(
                item_id="ITEM-1", statement_id="STMT-2",
                revision="rev-stmt-2", locator="SNAP#/items/1",
            )
            result = _bind(candidate, items=(control, changed))
            assert len(result.bindings) == len(result.current_receipt.item_target_receipts) == 2
            assert tuple(binding.feedback_item_ref.object_id for binding in result.bindings) == ("ITEM-0", "ITEM-1")
            assert result.bindings[0].status == "BOUND"
            assert result.bindings[0].track_match == "MATCH"
            assert result.bindings[0].detected_issues == ()
            assert result.bindings[1].status == "UNBOUND"
            assert result.bindings[1].track_match == "MISMATCH"
            assert result.bindings[1].detected_issues == (DetectedIssue("FEEDBACK.TRACK_MISMATCH", "/feedback_bindings/1/track_match"),)
            assert tuple(receipt.feedback_item_id for receipt in result.current_receipt.item_target_receipts) == ("ITEM-0", "ITEM-1")
            assert result.current_receipt.item_target_receipts[1].graph == ()
            return
        result = _bind(authority, items=(control, changed))
        assert len(result.bindings) == len(result.current_receipt.item_target_receipts) == 2
        assert tuple(binding.feedback_item_ref.object_id for binding in result.bindings) == ("ITEM-0", "ITEM-1")
        assert result.bindings[0].status == "BOUND" and result.bindings[0].detected_issues == ()
        assert result.bindings[1].status == "UNBOUND" and result.bindings[1].detected_issues == (expected,)
        assert result.current_receipt.item_target_receipts[1].graph == ()
        return

    if case_id == "P04":
        result = _bind(authority, items=(_item(revision=None),))
        binding = _binding(result)
        receipt = result.current_receipt.item_target_receipts[0]
        assert binding.status == "BOUND" and binding.revision_match == "UNKNOWN"
        assert receipt.resolution_status == "BOUND" and receipt.graph
        assert binding.detected_issues == ()
        return

    if case_id == "P06":
        duplicate = _statement()
        duplicate_set = _statement_set((duplicate, duplicate))
        candidate = replace(
            authority,
            statement_set=duplicate_set,
            statement_set_ref=replace(
                authority.statement_set_ref,
                digest_binding=DigestPresent(
                    "PRESENT", duplicate_set.content_digest
                ),
            ),
        )
        candidate = _resign_authority(candidate)
        status, category, graph, _, _ = feedback._production_target(item, candidate, _NOW)
        assert (status, category, graph) == ("AMBIGUOUS", "AMBIGUOUS_CANDIDATES", ())
        return

    if case_id == "P07":
        candidate = replace(authority, statement_refs=(object(),))
        raw = _raw(candidate)
        result = feedback.bind_feedback_operation(raw, prior=None, clock=_Clock())
        binding, receipt = _assert_nonbound_receipt(result, 0, "INVALID", "INVALID_MATERIAL")
        assert result.valid is True and binding.detected_issues == () and receipt.graph == ()
        _assert_invalid_authority_preimages(raw, result)
        return

    if case_id == "P08":
        original = authority.statement_set.statements[0]
        revised = replace(original, statement_revision_id="rev-other")
        assert _digest(feedback._standard_statement_owner_content_material(original)) == _digest(feedback._standard_statement_owner_content_material(revised))
        tampered = replace(original, content_digest=_digest("wrong"))
        candidate = _replace_statement(authority, tampered, resign_statement=False, resign_set=False)
        raw = _raw(candidate)
        result = feedback.bind_feedback_operation(raw, prior=None, clock=_Clock())
        binding, receipt = _assert_nonbound_receipt(result, 0, "INVALID", "INVALID_MATERIAL")
        assert result.valid is True and binding.detected_issues == () and receipt.graph == ()
        _assert_invalid_authority_preimages(raw, result)
        return

    if case_id == "P09":
        ref = replace(authority.statement_refs[0], contract_version="wrong-contract")
        status, category, graph, _, _ = feedback._production_target(item, replace(authority, statement_refs=(ref,)), _NOW)
        assert (status, category, graph) == ("INVALID", "INVALID_MATERIAL", ())
        return

    if case_id == "P10":
        result = _bind(_production_authority(set_case="CASE-OTHER"))
        binding, receipt = _assert_nonbound_receipt(
            result, 0, "UNBOUND", "REQUIRED_MATCH_FAILED"
        )
        assert binding.case_match == "MISMATCH" and receipt.graph == ()
        return

    if case_id == "P11":
        candidate = replace(
            authority,
            statement_set=replace(
                authority.statement_set, track=RunTrack.V5_V6_PREPROD
            ),
        )
        target_binding = _track_binding(
            side="BINDING_TARGET", track=RunTrack.PRODUCTION_DEFAULT
        )
        raw = _raw(
            candidate,
            target_binding=target_binding,
            submission_track=RunTrack.PRODUCTION_DEFAULT,
        )
        result = feedback.bind_feedback_operation(raw, prior=None, clock=_Clock())
        binding, receipt = _assert_nonbound_receipt(
            result, 0, "INVALID", "INVALID_MATERIAL"
        )
        assert result.valid is True and binding.detected_issues == ()
        assert receipt.graph == ()
        _assert_invalid_authority_preimages(raw, result)
        return

    if case_id == "P12":
        statement = authority.statement_set.statements[0]
        changed = replace(statement, statement_text="changed")
        assert _digest(feedback._statement_set_owner_content_material(replace(authority.statement_set, content_digest=_digest("ignored")))) == _digest(feedback._statement_set_owner_content_material(authority.statement_set))
        assert _digest(feedback._statement_set_owner_content_material(replace(authority.statement_set, statements=(changed,)))) != authority.statement_set.content_digest
        candidate = replace(authority, statement_set=replace(authority.statement_set, statements=(changed,)))
        raw = _raw(candidate)
        result = feedback.bind_feedback_operation(raw, prior=None, clock=_Clock())
        binding, receipt = _assert_nonbound_receipt(result, 0, "INVALID", "INVALID_MATERIAL")
        assert result.valid is True and binding.detected_issues == () and receipt.graph == ()
        _assert_invalid_authority_preimages(raw, result)
        return

    if case_id == "P13":
        candidate = replace(authority, statement_set_ref=replace(authority.statement_set_ref, contract_version="wrong"))
        status, category, graph, _, _ = feedback._production_target(item, candidate, _NOW)
        assert (status, category, graph) == ("INVALID", "INVALID_MATERIAL", ())
        return

    if case_id in {"P14", "P15", "P16", "P17", "P18", "P19"}:
        record = authority.manifest.records[0]
        if case_id == "P14": records = ()
        elif case_id == "P15":
            duplicate_candidate = replace(record, path_locator="duplicate-location.bin")
            duplicate_authority = replace(authority, manifest=_manifest((record, duplicate_candidate)))
            status, category, graph, _, _ = feedback._production_target(item, duplicate_authority, _NOW)
            assert (status, category, graph) == ("AMBIGUOUS", "AMBIGUOUS_CANDIDATES", ())
            decoy_digest = _digest("same-scope-unrelated-statement-records")
            decoys = (
                replace(
                    record,
                    artifact_id="UNRELATED-STATEMENT-RECORDS",
                    path_locator="unrelated.bin",
                    expected_digest=decoy_digest,
                    observed_digest=decoy_digest,
                ),
                replace(record, schema_version="statement-records.v2", path_locator="schema-decoy.bin"),
                replace(record, run_id="RUN-DECOY", path_locator="run-decoy.bin"),
            )
            for decoy in decoys:
                decoy_authority = replace(authority, manifest=_manifest((record, decoy)))
                status, category, graph, _, _ = feedback._production_target(item, decoy_authority, _NOW)
                assert status == "BOUND" and category is None and graph
            return
        elif case_id == "P16": records = (replace(record, state=ArtifactItemState.WRITTEN_UNVERIFIED),)
        elif case_id == "P17": records = (replace(record, expected_digest=None),)
        elif case_id == "P18": records = (replace(record, observed_digest=None),)
        else: records = (replace(record, observed_digest=_digest("unequal")),)
        candidate = replace(authority, manifest=_manifest(records))
        status, category, graph, _, dims = feedback._production_target(item, candidate, _NOW)
        expected_status = "AMBIGUOUS" if case_id == "P15" else "UNBOUND"
        assert status == expected_status and graph == () and dims[2] == "NOT_APPLICABLE"
        assert category == ("AMBIGUOUS_CANDIDATES" if case_id == "P15" else "PROTOCOL_GRAPH_INCOMPLETE")
        return

    if case_id == "P20":
        record = replace(authority.manifest.records[0], artifact_id="RUN-LIKE-TARGET-ARTIFACT-ID")
        target_ref = replace(authority.records_projection_refs[0], object_id=record.artifact_id)
        target_projection = replace(authority.records_projection_records[0], projected_object_ref=target_ref)
        decoy_digest = _digest("other-artifact-with-conflicting-run")
        decoy = ArtifactRecord(
            "OTHER-ARTIFACT", "REPORT", RunTrack.PRODUCTION_DEFAULT,
            "CASE-1", None, "RUN-DECOY-MUST-NOT-BE-AUTHORITY", "report.bin",
            "report.v1", decoy_digest, decoy_digest,
            ArtifactItemState.VERIFIED, (), (),
        )
        positive_authority = _resign_authority(replace(
            authority, manifest=_manifest((record, decoy)),
            records_projection_refs=(target_ref,),
            records_projection_records=(target_projection,),
        ))
        positive = _bind(
            positive_authority,
            items=(_item(run_id=None),),
        )
        bound = _binding(positive)
        assert record.statement_set_id == authority.statement_set.statement_set_id and record.run_id is None
        assert "RUN" in record.artifact_id and decoy.run_id == "RUN-DECOY-MUST-NOT-BE-AUTHORITY"
        assert decoy.artifact_id == "OTHER-ARTIFACT"
        assert bound.status == "BOUND" and bound.run_match == "NOT_APPLICABLE"
        nonnull_run = _bind(positive_authority, items=(_item(run_id="RAW-RUN-FORBIDDEN"),))
        nonnull_binding, nonnull_receipt = _assert_nonbound_receipt(nonnull_run, 0, "INVALID", "INVALID_MATERIAL")
        assert nonnull_binding.run_match == "NOT_APPLICABLE"
        assert nonnull_binding.target_object_refs == nonnull_receipt.graph == ()
        invalid_record = replace(
            authority.manifest.records[0], run_id="RUN-MUST-NOT-BE-INFERRED"
        )
        invalid_authority = replace(authority, manifest=_manifest((invalid_record,)))
        invalid = _bind(_resign_authority(invalid_authority))
        invalid_binding, invalid_receipt = _assert_nonbound_receipt(invalid, 0, "INVALID", "INVALID_MATERIAL")
        assert invalid_binding.run_match == "NOT_APPLICABLE"
        assert invalid_binding.target_object_refs == () and invalid_receipt.graph == ()
        assert invalid_receipt.graph_digest == _digest(feedback._item_target_graph_material("PRODUCTION_STATEMENT", item, "INVALID", "INVALID_MATERIAL", ()))
        independent_ref = replace(
            target_ref,
            schema_version="records-schema.independent",
            contract_version="records-contract.independent",
        )
        independent_record = replace(record, schema_version="records-schema.independent")
        independent_projection = replace(
            target_projection,
            projected_object_ref=independent_ref,
        )
        independent_versions = replace(
            authority.governing_versions,
            statement_records_contract_version="records-contract.independent",
        )
        independent_authority = replace(
            authority,
            manifest=_manifest((independent_record,)),
            records_projection_refs=(independent_ref,),
            records_projection_records=(independent_projection,),
            governing_versions=independent_versions,
        )
        status, category, graph, _, dimensions = feedback._production_target(
            item, independent_authority, _NOW,
        )
        assert status == "BOUND" and category is None and graph
        assert dimensions[2] == "NOT_APPLICABLE"

        schema_mismatch_record = replace(
            authority.manifest.records[0], schema_version="records.other"
        )
        status, category, graph, _, dimensions = feedback._production_target(
            item,
            replace(authority, manifest=_manifest((schema_mismatch_record,))),
            _NOW,
        )
        assert (status, category, graph) == ("INVALID", "INVALID_MATERIAL", ())
        assert dimensions[2] == "NOT_APPLICABLE"

        contract_mismatch_versions = replace(
            authority.governing_versions,
            statement_records_contract_version="records.other",
        )
        status, category, graph, _, dimensions = feedback._production_target(
            item,
            replace(authority, governing_versions=contract_mismatch_versions),
            _NOW,
        )
        assert (status, category, graph) == ("INVALID", "INVALID_MATERIAL", ())
        assert dimensions[2] == "NOT_APPLICABLE"

        wrong_type_ref = replace(
            authority.records_projection_refs[0], object_type="REPORT",
        )
        wrong_type_projection = replace(
            authority.records_projection_records[0],
            projected_object_ref=wrong_type_ref,
        )
        status, category, graph, _, dimensions = feedback._production_target(
            item,
            replace(
                authority,
                records_projection_refs=(wrong_type_ref,),
                records_projection_records=(wrong_type_projection,),
            ),
            _NOW,
        )
        assert (status, category, graph) == ("INVALID", "INVALID_MATERIAL", ())
        assert dimensions[2] == "NOT_APPLICABLE"

        schema_mismatch_ref = replace(
            authority.records_projection_refs[0], schema_version="records.other",
        )
        schema_mismatch_projection = replace(
            authority.records_projection_records[0],
            projected_object_ref=schema_mismatch_ref,
        )
        status, category, graph, _, dimensions = feedback._production_target(
            item,
            replace(
                authority,
                records_projection_refs=(schema_mismatch_ref,),
                records_projection_records=(schema_mismatch_projection,),
            ),
            _NOW,
        )
        assert (status, category, graph) == ("INVALID", "INVALID_MATERIAL", ())
        assert dimensions[2] == "NOT_APPLICABLE"
        return

    if case_id in {"P21", "P22", "P23", "P24"}:
        projection = authority.records_projection_records[0]
        if case_id == "P21": projection = replace(projection, projected_object_ref=replace(projection.projected_object_ref, object_id="OTHER"))
        elif case_id == "P22": projection = replace(projection, projection_type="STATEMENT_INDEX")
        elif case_id == "P23": projection = replace(projection, statement_id="OTHER")
        else: projection = replace(projection, source_statement_digest=_digest("wrong"))
        status, category, graph, _, _ = feedback._production_target(item, replace(authority, records_projection_records=(projection,)), _NOW)
        assert (status, category, graph) == ("INVALID", "INVALID_MATERIAL", ())
        return

    if case_id in {"P25", "P26", "P27", "P28", "P29", "P30", "P31", "P32", "P33", "P34", "P35"}:
        anchor = authority.anchor_selections[0]
        if case_id == "P25": anchors = ()
        elif case_id == "P26":
            duplicate = replace(anchor, anchor_selection_id="ANCHOR-2")
            anchors = (anchor, duplicate)
        elif case_id == "P27": anchors = (replace(anchor, selected_anchor_rule_ref=None, fidelity="UNSUPPORTED", fanout_scope="NONE"),)
        elif case_id == "P28": anchors = (replace(anchor, all_rule_refs=(), selected_anchor_rule_ref=None, non_anchor_rule_refs=()),)
        elif case_id == "P29":
            rules = (
                anchor.all_rule_refs[0],
                anchor.all_rule_refs[0],
                anchor.selected_anchor_rule_ref,
            )
            anchors = (replace(
                anchor,
                all_rule_refs=rules,
                non_anchor_rule_refs=rules[:2],
                source_order_digest=_digest(tuple(
                    feedback._versioned_object_ref_material(ref)
                    for ref in rules
                )),
            ),)
        elif case_id == "P30": anchors = (replace(anchor, selected_anchor_rule_ref=_ref("RULE", "ABSENT", contract="rule.v1")),)
        elif case_id == "P31":
            rules = (
                anchor.all_rule_refs[0],
                anchor.selected_anchor_rule_ref,
                anchor.selected_anchor_rule_ref,
            )
            anchors = (replace(
                anchor,
                all_rule_refs=rules,
                source_order_digest=_digest(tuple(
                    feedback._versioned_object_ref_material(ref)
                    for ref in rules
                )),
            ),)
        elif case_id == "P32": anchors = (replace(anchor, non_anchor_rule_refs=tuple(reversed(anchor.non_anchor_rule_refs + (anchor.selected_anchor_rule_ref,)))),)
        elif case_id == "P33": anchors = (replace(anchor, source_order_digest=_digest("wrong-order")),)
        elif case_id == "P34":
            not_rule = replace(anchor.selected_anchor_rule_ref, object_type="CLAIM")
            rules = (anchor.all_rule_refs[0], not_rule)
            anchors = (replace(
                anchor,
                all_rule_refs=rules,
                selected_anchor_rule_ref=not_rule,
                source_order_digest=_digest(tuple(
                    feedback._versioned_object_ref_material(ref)
                    for ref in rules
                )),
            ),)
        else:
            wrong = replace(anchor.selected_anchor_rule_ref, contract_version="wrong")
            rules = (anchor.all_rule_refs[0], wrong)
            anchors = (replace(
                anchor,
                all_rule_refs=rules,
                selected_anchor_rule_ref=wrong,
                source_order_digest=_digest(tuple(
                    feedback._versioned_object_ref_material(ref)
                    for ref in rules
                )),
            ),)
        status, category, graph, _, _ = feedback._production_target(item, replace(authority, anchor_selections=anchors), _NOW)
        if case_id == "P25": assert (status, category) == ("UNBOUND", "PROTOCOL_GRAPH_INCOMPLETE")
        elif case_id == "P26": assert (status, category) == ("AMBIGUOUS", "AMBIGUOUS_CANDIDATES")
        elif case_id == "P27": assert (status, category) == ("UNBOUND", "PROTOCOL_GRAPH_INCOMPLETE")
        else: assert (status, category) == ("INVALID", "INVALID_MATERIAL")
        assert graph == ()
        return

    if case_id in {"P36", "P37", "P38", "P39", "P40"}:
        md = authority.rule_metadata_receipts[0]
        if case_id == "P38":
            candidate = replace(
                authority,
                rule_metadata_receipts=(replace(md, family_id=""),),
            )
            target_binding = _track_binding(
                side="BINDING_TARGET", track=RunTrack.PRODUCTION_DEFAULT
            )
            raw = _raw(
                candidate,
                target_binding=target_binding,
                submission_track=RunTrack.PRODUCTION_DEFAULT,
            )
            result = feedback.bind_feedback_operation(
                raw, prior=None, clock=_Clock()
            )
            binding, receipt = _assert_nonbound_receipt(
                result, 0, "INVALID", "INVALID_MATERIAL"
            )
            assert result.valid is True and binding.detected_issues == ()
            assert binding.target_object_refs == receipt.graph == ()
            _assert_invalid_authority_preimages(raw, result)
            return
        if case_id == "P36": metadata = ()
        elif case_id == "P37":
            duplicate = replace(md, captured_at="2026-07-22T02:00:00Z")
            duplicate = replace(duplicate, content_digest=_digest(feedback._rule_metadata_receipt_self_excluded_material(duplicate)))
            metadata = (md, duplicate)
        elif case_id == "P39":
            changed = replace(md, family_id="UNMAPPED")
            metadata = (replace(changed, content_digest=_digest(feedback._rule_metadata_receipt_self_excluded_material(changed))),)
        else:
            coherent_source = replace(
                md.source_ref,
                object_type="NON_HISTORICAL_SOURCE",
                object_id="SOURCE-CUSTOM-2",
                revision_id="source-rev-9",
                schema_version="metadata.custom.v2",
                contract_version="source-contract.custom.v3",
                digest_binding=DigestPresent("PRESENT", _digest("custom-source-payload")),
                source_locator_id="custom://metadata/source-2",
                captured_at="2026-07-22T04:00:00Z",
            )
            assert type(coherent_source.digest_binding) is DigestPresent
            assert len(coherent_source.digest_binding.digest.value) == 64
            coherent = replace(md, metadata_schema_version="metadata.custom.v2", source_ref=coherent_source)
            coherent = replace(coherent, content_digest=_digest(feedback._rule_metadata_receipt_self_excluded_material(coherent)))
            coherent_authority = _resign_authority(replace(
                authority, rule_metadata_receipts=(coherent,)
            ))
            assert _binding(_bind(coherent_authority)).status == "BOUND"
            missing_source = replace(
                md,
                source_ref=replace(
                    md.source_ref,
                    digest_binding=DigestMissing("MISSING", None, "MISSING"),
                ),
            )
            missing_source = replace(
                missing_source,
                content_digest=_digest(feedback._rule_metadata_receipt_self_excluded_material(missing_source)),
            )
            second_statement = _statement(
                statement_id="STMT-2", revision="rev-stmt-2",
            )
            statement_set = _statement_set(
                (authority.statement_set.statements[0], second_statement),
            )
            second_statement_ref = _ref(
                "STATEMENT", second_statement.statement_id,
                revision=second_statement.statement_revision_id,
                schema=second_statement.statement_schema_version,
                contract="statement.v1", digest=second_statement.content_digest,
            )
            second_record_digest = _digest("statement-records-2")
            second_record = ArtifactRecord(
                "ART-RECORDS-2", "STATEMENT_RECORDS", RunTrack.PRODUCTION_DEFAULT,
                "CASE-1", "SET-1", None, "statement_records_2.bin", "records.v1",
                second_record_digest, second_record_digest, ArtifactItemState.VERIFIED,
                (), (),
            )
            second_artifact_ref = _ref(
                "STATEMENT_RECORDS", "ART-RECORDS-2", schema="records.v1",
                contract="records.v1", digest=second_record_digest,
            )
            second_projection = replace(
                authority.records_projection_records[0],
                projection_id="PROJECTION-2",
                statement_id=second_statement.statement_id,
                statement_revision_id=second_statement.statement_revision_id,
                source_statement_digest=second_statement.content_digest,
                projected_object_ref=second_artifact_ref,
            )
            second_selected = _ref("RULE", "RULE-3", contract="rule.v1")
            second_supporting = _ref("RULE", "RULE-4", contract="rule.v1")
            second_rules = (second_supporting, second_selected)
            second_anchor = replace(
                authority.anchor_selections[0],
                anchor_selection_id="ANCHOR-2",
                statement_id=second_statement.statement_id,
                statement_revision_id=second_statement.statement_revision_id,
                all_rule_refs=second_rules,
                selected_anchor_rule_ref=second_selected,
                non_anchor_rule_refs=(second_supporting,),
                source_order_digest=_digest(tuple(
                    feedback._versioned_object_ref_material(ref)
                    for ref in second_rules
                )),
            )
            missing_authority = replace(
                authority,
                statement_set=statement_set,
                statement_set_ref=replace(
                    authority.statement_set_ref,
                    digest_binding=DigestPresent("PRESENT", statement_set.content_digest),
                ),
                statement_refs=authority.statement_refs + (second_statement_ref,),
                manifest=_manifest(authority.manifest.records + (second_record,)),
                records_projection_refs=authority.records_projection_refs + (second_artifact_ref,),
                records_projection_records=authority.records_projection_records + (second_projection,),
                anchor_selections=authority.anchor_selections + (second_anchor,),
                rule_metadata_receipts=(missing_source, _metadata(second_selected)),
            )
            missing_authority = _resign_authority(missing_authority)
            missing_items = (
                _item(item_id="ITEM-1", locator="SNAP#/items/0"),
                _item(
                    item_id="ITEM-2", statement_id="STMT-2", revision="rev-stmt-2",
                    locator="SNAP#/items/1",
                ),
            )
            missing_result = _bind(missing_authority, items=missing_items)
            assert len(missing_result.bindings) == 2
            missing_binding, missing_receipt = _assert_nonbound_receipt(
                missing_result, 0, "INVALID", "INVALID_MATERIAL"
            )
            assert missing_binding.target_object_refs == missing_receipt.graph == ()
            assert missing_result.bindings[1].status == "BOUND"
            assert missing_result.current_receipt.item_target_receipts[1].resolution_status == "BOUND"
            assert missing_result.current_receipt.item_target_receipts[1].non_bound_category is None
            assert missing_result.current_receipt.item_target_receipts[1].graph
            ref_mutations = (
                replace(md.rule_ref, object_type="OTHER"),
                replace(md.rule_ref, object_id="OTHER"),
                replace(md.rule_ref, revision_id="OTHER"),
                replace(md.rule_ref, schema_version="OTHER"),
                replace(md.rule_ref, contract_version="OTHER"),
                replace(md.rule_ref, digest_binding=DigestPresent("PRESENT", _digest("OTHER-RULE"))),
                replace(md.rule_ref, source_locator_id="OTHER"),
                replace(md.rule_ref, captured_at="2026-07-22T02:00:00Z"),
            )
            resignable_metadata_mutations = tuple(replace(md, rule_ref=changed_ref) for changed_ref in ref_mutations) + (
                replace(md, metadata_contract_version="wrong"),
                replace(md, metadata_schema_version="wrong"),
                replace(md, source_ref=replace(md.source_ref, schema_version="wrong")),
                replace(md, rule_type="UNMAPPED"),
                replace(md, rule_ref=replace(md.rule_ref, digest_binding=DigestMissing("MISSING", None, "MISSING"))),
                replace(md, source_ref=replace(md.source_ref, digest_binding=DigestMissing("MISSING", None, "MISSING"))),
            )
            anchor = authority.anchor_selections[0]
            selected_missing = replace(anchor.selected_anchor_rule_ref, digest_binding=DigestMissing("MISSING", None, "MISSING"))
            selected_rules = (anchor.all_rule_refs[0], selected_missing)
            selected_missing_anchor = replace(
                anchor,
                all_rule_refs=selected_rules,
                selected_anchor_rule_ref=selected_missing,
                source_order_digest=_digest(tuple(feedback._versioned_object_ref_material(ref) for ref in selected_rules)),
            )
            selected_missing_authority = _resign_authority(replace(
                authority, anchor_selections=(selected_missing_anchor,)
            ))
            selected_missing_result = _bind(selected_missing_authority)
            _assert_nonbound_receipt(
                selected_missing_result, 0, "INVALID", "INVALID_MATERIAL"
            )

            target_binding = _track_binding(
                side="BINDING_TARGET", track=RunTrack.PRODUCTION_DEFAULT
            )
            blank_identity_mutations = (
                replace(md, family_id=""),
                replace(md, school=""),
                replace(md, canon=""),
                replace(md, rule_type=""),
                replace(md, captured_at=""),
            )
            for changed in blank_identity_mutations:
                malformed_authority = replace(
                    authority, rule_metadata_receipts=(changed,)
                )
                malformed_raw = _raw(
                    malformed_authority,
                    target_binding=target_binding,
                    submission_track=RunTrack.PRODUCTION_DEFAULT,
                )
                malformed_result = feedback.bind_feedback_operation(
                    malformed_raw, prior=None, clock=_Clock()
                )
                malformed_binding, malformed_receipt = _assert_nonbound_receipt(
                    malformed_result, 0, "INVALID", "INVALID_MATERIAL"
                )
                assert malformed_result.valid is True
                assert malformed_binding.detected_issues == ()
                assert malformed_binding.target_object_refs == malformed_receipt.graph == ()
                _assert_invalid_authority_preimages(
                    malformed_raw, malformed_result
                )

            bad_digest_authority = replace(
                authority,
                rule_metadata_receipts=(
                    replace(md, content_digest=_digest("wrong-metadata-receipt")),
                ),
            )
            bad_digest_raw = _raw(
                bad_digest_authority,
                target_binding=target_binding,
                submission_track=RunTrack.PRODUCTION_DEFAULT,
            )
            bad_digest_result = feedback.bind_feedback_operation(
                bad_digest_raw, prior=None, clock=_Clock()
            )
            bad_digest_binding, bad_digest_receipt = _assert_nonbound_receipt(
                bad_digest_result, 0, "INVALID", "INVALID_MATERIAL"
            )
            assert bad_digest_result.valid is True
            assert bad_digest_binding.detected_issues == ()
            assert bad_digest_binding.target_object_refs == bad_digest_receipt.graph == ()
            _assert_invalid_authority_preimages(
                bad_digest_raw, bad_digest_result
            )

            for changed in resignable_metadata_mutations:
                changed = replace(
                    changed,
                    content_digest=_digest(
                        feedback._rule_metadata_receipt_self_excluded_material(
                            changed
                        )
                    ),
                )
                changed_authority = _resign_authority(replace(
                    authority, rule_metadata_receipts=(changed,)
                ))
                changed_result = _bind(changed_authority)
                _assert_nonbound_receipt(
                    changed_result, 0, "INVALID", "INVALID_MATERIAL"
                )

            family_unmapped = replace(md, family_id="UNMAPPED")
            family_unmapped = replace(
                family_unmapped,
                content_digest=_digest(
                    feedback._rule_metadata_receipt_self_excluded_material(
                        family_unmapped
                    )
                ),
            )
            family_unmapped_authority = _resign_authority(replace(
                authority, rule_metadata_receipts=(family_unmapped,)
            ))
            _assert_nonbound_receipt(
                _bind(family_unmapped_authority),
                0,
                "UNBOUND",
                "PROTOCOL_GRAPH_INCOMPLETE",
            )
            return
        candidate = replace(authority, rule_metadata_receipts=metadata)
        status, category, graph, _, _ = feedback._production_target(item, candidate, _NOW)
        expected = {"P36": "UNBOUND", "P37": "AMBIGUOUS", "P39": "UNBOUND"}[case_id]
        assert status == expected and graph == ()
        binding_result = _bind(_resign_authority(candidate))
        eligibility = _eligibility(_binding(binding_result), _resign_authority(candidate))
        expected_eligibility = "HUMAN_REVIEW" if case_id == "P37" else "INELIGIBLE"
        assert eligibility.status == expected_eligibility and eligibility.learning_target_refs == ()
        return

    if case_id == "P41":
        binding = _binding(_bind(authority))
        assert binding.track_match == "MATCH" and binding.status == "BOUND"
        return

    if case_id in {"P43", "P44", "P45", "P46", "P47", "P48", "P49", "P50"}:
        if case_id == "P43": source = _track_binding(side="SUBMISSION_SOURCE", state="SOURCE_MISSING", reasons=("TRACK_SOURCE_MISSING",)); target = None
        elif case_id == "P44": source = None; target = _track_binding(side="BINDING_TARGET", state="UNPARSABLE", reasons=("TRACK_SOURCE_UNPARSABLE",))
        elif case_id == "P45": source = _track_binding(side="SUBMISSION_SOURCE", state="AMBIGUOUS", reasons=("TRACK_SOURCE_AMBIGUOUS",)); target = None
        elif case_id == "P46": source = _track_binding(side="SUBMISSION_SOURCE", state="INTEGRITY_FAILED", reasons=("TRACK_SOURCE_INTEGRITY_FAILED",)); target = None
        elif case_id in {"P47", "P48"}:
            valid_target = _track_binding(side="BINDING_TARGET")
            target = feedback.TrackSourceBinding.__new__(feedback.TrackSourceBinding)
            object.__setattr__(target, "track_source_binding_id", valid_target.track_source_binding_id)
            object.__setattr__(target, "side", valid_target.side)
            object.__setattr__(target, "track", valid_target.track)
            object.__setattr__(target, "state", valid_target.state)
            object.__setattr__(target, "source_evidence_ref", valid_target.source_evidence_ref)
            object.__setattr__(target, "parser_ref", valid_target.parser_ref)
            object.__setattr__(target, "schema_version", valid_target.schema_version)
            object.__setattr__(target, "contract_version", valid_target.contract_version)
            object.__setattr__(target, "content_digest", valid_target.content_digest)
            object.__setattr__(target, "state_reason_codes", valid_target.state_reason_codes)
            object.__setattr__(target, "captured_at", valid_target.captured_at)
            if case_id == "P47":
                object.__setattr__(target, "state_reason_codes", ("TRACK_SOURCE_MISSING",))
            else:
                object.__setattr__(target, "state", "SOURCE_MISSING")
                object.__setattr__(target, "state_reason_codes", ("TRACK_SOURCE_UNPARSABLE",))
            source = None
        elif case_id == "P49":
            source = _track_binding(side="SUBMISSION_SOURCE", parser_id="OTHER")
            target = None
        else: source = None; target = _track_binding(side="SUBMISSION_SOURCE")
        if case_id in {"P47", "P48", "P49", "P50"}:
            with pytest.raises(F09ContractError) as failure:
                _bind(authority, source_binding=source, target_binding=target)
            if case_id in {"P47", "P48"}:
                assert type(failure.value) is F09ContractError
                assert failure.value.issue_code == "FEEDBACK.MATERIAL_INVALID"
                assert failure.value.field_path == "/track_source_binding/state_reason_codes"
            return
        result = _bind(authority, source_binding=source, target_binding=target)
        binding = _binding(result)
        receipt = result.current_receipt.item_target_receipts[0]
        expected = {
            "P43": ("UNBOUND", "TRACK_UNRESOLVED"),
            "P44": ("UNBOUND", "TRACK_UNRESOLVED"),
            "P45": ("AMBIGUOUS", "AMBIGUOUS_CANDIDATES"),
            "P46": ("INVALID", "INVALID_MATERIAL"),
        }[case_id]
        assert (binding.status, receipt.non_bound_category) == expected
        assert binding.track_match == "UNKNOWN" and binding.target_object_refs == ()
        assert receipt.resolution_status == binding.status and receipt.graph == ()
        if case_id in {"P43", "P44"}:
            assert binding.detected_issues == (
                DetectedIssue("FEEDBACK.TARGET_UNBOUND", "/feedback_bindings/0"),
            )
        else:
            assert binding.detected_issues == ()
        return

    if case_id == "P51":
        raw = _raw(authority)
        parsed = parse_bounded_jcs(raw.raw_submission)
        snapshot = parsed["source_snapshot_ref"]
        snapshot["content_digest"] = feedback._digest_ref_material(_digest("wrong-payload"))
        submission_without_digest = dict(parsed)
        submission_without_digest.pop("content_digest")
        track_binding_without_digest = dict(submission_without_digest["track_source_binding"])
        track_binding_without_digest.pop("content_digest")
        submission_without_digest["track_source_binding"] = track_binding_without_digest
        parsed["content_digest"] = feedback._digest_ref_material(_digest(submission_without_digest))
        mismatched = replace(raw, raw_submission=canonicalize_bounded_jcs(parsed))
        with pytest.raises(F09IntegrityError) as failure:
            feedback.bind_feedback_operation(mismatched, prior=None, clock=_Clock())
        assert failure.value.field_path == "/source_snapshot_ref/content_digest"
        malformed = _bind(authority, items=(_item(locator="SNAP#not-a-pointer"),))
        binding, receipt = _assert_nonbound_receipt(malformed, 0, "INVALID", "INVALID_MATERIAL")
        assert binding.target_object_refs == () and receipt.graph == ()
        return

    if case_id == "P52":
        missing = _bind(authority, items=(_item(locator="SNAP#/items/9"),))
        _assert_nonbound_receipt(missing, 0, "UNBOUND", "SOURCE_SPAN_NOT_FOUND")
        blank_root = _bind(authority, items=(_item(locator="SNAP#"),), payload="")
        assert _binding(blank_root).status == "BOUND"
        scalar = _bind(authority, items=(_item(locator="SNAP#/x"),), payload="scalar")
        _assert_nonbound_receipt(scalar, 0, "UNBOUND", "SOURCE_SPAN_NOT_FOUND")
        return

    if case_id == "P53":
        result = _bind(_preprod_authority(), items=(_item(statement_id=None, revision=None, run_id=None),))
        binding, receipt = _assert_nonbound_receipt(result, 0, "INVALID", "INVALID_MATERIAL")
        assert binding.run_match == "UNKNOWN" and receipt.graph == ()
        return

    if case_id in {"P54", "P55", "P56", "P57", "P58"}:
        preprod = _preprod_authority()
        snapshot = preprod.target_refs[0]
        record = preprod.manifest.records[0]
        if case_id == "P54": candidate = replace(preprod, target_refs=())
        elif case_id == "P55":
            duplicate = replace(snapshot, object_id="ART-RUN-2")
            candidate = replace(preprod, target_refs=(snapshot, duplicate))
            result = _bind(candidate)
            binding, receipt = _assert_nonbound_receipt(
                result, 0, "INVALID", "INVALID_MATERIAL"
            )
            assert result.valid is True and binding.target_object_refs == ()
            assert receipt.graph == ()
            return
        elif case_id == "P56":
            target_states = (
                ("AVAILABLE_RESOLVED", ()),
                ("SOURCE_MISSING", ("TRACK_SOURCE_MISSING",)),
                ("UNPARSABLE", ("TRACK_SOURCE_UNPARSABLE",)),
                ("AMBIGUOUS", ("TRACK_SOURCE_AMBIGUOUS",)),
                ("INTEGRITY_FAILED", ("TRACK_SOURCE_INTEGRITY_FAILED",)),
            )
            malformed_by_protocol = (
                (authority, (
                    _item(statement_id=None, revision="rev-stmt-1", run_id=None),
                    _item(statement_id="STMT-1", revision="rev-stmt-1", run_id="RUN-FORBIDDEN"),
                    replace(_item(), target_prediction_id="PRED-FORBIDDEN"),
                    _item(statement_id=None, revision=None, run_id=None),
                )),
                (preprod, (
                    _item(statement_id="STMT-FORBIDDEN", revision=None, run_id="RUN-1"),
                    _item(statement_id=None, revision="REV-FORBIDDEN", run_id="RUN-1"),
                    _item(statement_id=None, revision=None, run_id=None),
                    replace(_item(statement_id=None, revision=None, run_id="RUN-1"), target_prediction_id="PRED-FORBIDDEN"),
                )),
            )
            for protocol_authority, malformed_items in malformed_by_protocol:
                target_track = RunTrack.PRODUCTION_DEFAULT if protocol_authority is authority else RunTrack.V5_V6_PREPROD
                for malformed_item in malformed_items:
                    for state, reasons in target_states:
                        target = _track_binding(side="BINDING_TARGET", track=target_track, state=state, reasons=reasons)
                        result = _bind(protocol_authority, items=(malformed_item,), target_binding=target)
                        binding, receipt = _assert_nonbound_receipt(result, 0, "INVALID", "INVALID_MATERIAL")
                        assert binding.target_object_refs == receipt.graph == ()
            legal_by_protocol = ((authority, _item()), (preprod, _item(statement_id=None, revision=None, run_id="RUN-1")))
            expected_states = {
                "SOURCE_MISSING": ("UNBOUND", "TRACK_UNRESOLVED"),
                "UNPARSABLE": ("UNBOUND", "TRACK_UNRESOLVED"),
                "AMBIGUOUS": ("AMBIGUOUS", "AMBIGUOUS_CANDIDATES"),
                "INTEGRITY_FAILED": ("INVALID", "INVALID_MATERIAL"),
            }
            for protocol_authority, legal_item in legal_by_protocol:
                target_track = RunTrack.PRODUCTION_DEFAULT if protocol_authority is authority else RunTrack.V5_V6_PREPROD
                for state, reasons in target_states[1:]:
                    target = _track_binding(side="BINDING_TARGET", track=target_track, state=state, reasons=reasons)
                    result = _bind(protocol_authority, items=(legal_item,), target_binding=target)
                    binding, receipt = _assert_nonbound_receipt(result, 0, *expected_states[state])
                    assert binding.target_object_refs == receipt.graph == ()
            return
        elif case_id == "P57":
            bad_ref = replace(snapshot, object_id="OTHER")
            candidate = replace(preprod, target_refs=(bad_ref,))
            forbidden_ref = replace(snapshot, object_type="REPORT")
            other_digest = _digest("other-snapshot")
            other_ref = replace(snapshot, object_id="OTHER", digest_binding=DigestPresent("PRESENT", other_digest))
            other_record = replace(record, artifact_id="OTHER", expected_digest=other_digest, observed_digest=other_digest)
            resolver_cases = (
                (replace(snapshot, object_id="OTHER"), (record,), "UNBOUND", "TARGET_NOT_FOUND"),
                (replace(snapshot, schema_version="other.v1"), (record,), "UNBOUND", "TARGET_NOT_FOUND"),
                (snapshot, (replace(record, artifact_role="DECISION_RUN"),), "UNBOUND", "TARGET_NOT_FOUND"),
                (snapshot, (replace(record, artifact_id="OTHER"),), "UNBOUND", "TARGET_NOT_FOUND"),
                (snapshot, (replace(record, schema_version="other.v1"),), "UNBOUND", "TARGET_NOT_FOUND"),
                (other_ref, (other_record,), "INVALID", "INVALID_MATERIAL"),
                (snapshot, (), "UNBOUND", "TARGET_NOT_FOUND"),
                (snapshot, (replace(record, state=ArtifactItemState.SUPERSEDED),), "UNBOUND", "TARGET_NOT_FOUND"),
                (snapshot, (record, replace(record, path_locator="duplicate.bin")), "AMBIGUOUS", "AMBIGUOUS_CANDIDATES"),
                (replace(snapshot, digest_binding=DigestMissing("MISSING", None, "MISSING")), (record,), "INVALID", "INVALID_MATERIAL"),
                (replace(snapshot, digest_binding=DigestPresent("PRESENT", _digest("wrong-ref"))), (record,), "UNBOUND", "TARGET_NOT_FOUND"),
                (snapshot, (replace(record, expected_digest=None),), "UNBOUND", "TARGET_NOT_FOUND"),
                (snapshot, (replace(record, observed_digest=None),), "UNBOUND", "TARGET_NOT_FOUND"),
                (snapshot, (replace(record, expected_digest=_digest("wrong")),), "UNBOUND", "TARGET_NOT_FOUND"),
                (snapshot, (replace(record, observed_digest=_digest("wrong")),), "UNBOUND", "TARGET_NOT_FOUND"),
                (snapshot, (replace(record, case_id="OTHER"),), "UNBOUND", "TARGET_NOT_FOUND"),
                (snapshot, (replace(record, track=RunTrack.PRODUCTION_DEFAULT),), "UNBOUND", "TARGET_NOT_FOUND"),
                (snapshot, (replace(record, run_id="OTHER"),), "UNBOUND", "TARGET_NOT_FOUND"),
                (snapshot, (replace(record, statement_set_id="SET-1"),), "UNBOUND", "TARGET_NOT_FOUND"),
                (snapshot, (replace(record, state=ArtifactItemState.WRITTEN_UNVERIFIED),), "UNBOUND", "TARGET_NOT_FOUND"),
            )
            for changed_ref, changed_records, expected_status, expected_category in resolver_cases:
                changed = replace(preprod, target_refs=(changed_ref,), manifest=_manifest(changed_records))
                changed = replace(changed, content_digest=_digest(feedback._preprod_authority_self_excluded_material(changed)))
                resolved = _bind(changed)
                _assert_nonbound_receipt(resolved, 0, expected_status, expected_category)
            forbidden = replace(preprod, target_refs=(forbidden_ref,))
            forbidden_result = _bind(forbidden)
            _assert_nonbound_receipt(forbidden_result, 0, "INVALID", "INVALID_MATERIAL")
            duplicate_role = replace(preprod, target_refs=(snapshot, replace(snapshot, object_id="ART-RUN-DUPLICATE")))
            _assert_nonbound_receipt(_bind(duplicate_role), 0, "INVALID", "INVALID_MATERIAL")
            required_role_missing = replace(preprod, target_refs=())
            required_role_missing = replace(required_role_missing, content_digest=_digest(feedback._preprod_authority_self_excluded_material(required_role_missing)))
            _assert_nonbound_receipt(_bind(required_role_missing), 0, "UNBOUND", "PROTOCOL_GRAPH_INCOMPLETE")
            assert _binding(_bind(preprod)).status == "BOUND"
            for malformed_ref in (
                replace(snapshot, revision_id=""),
                replace(snapshot, contract_version=""),
                replace(snapshot, source_locator_id=""),
                replace(snapshot, captured_at=""),
            ):
                malformed = replace(preprod, target_refs=(malformed_ref,))
                invalid = _bind(malformed)
                _assert_nonbound_receipt(invalid, 0, "INVALID", "INVALID_MATERIAL")
            for role in ("RUN_SNAPSHOT", "DECISION_RUN", "FEEDBACK_ATTACHMENT", "MANIFEST"):
                role_digest = snapshot.digest_binding.digest if role == "RUN_SNAPSHOT" else _digest(role)
                role_ref = snapshot if role == "RUN_SNAPSHOT" else _ref(role, "ART-" + role, schema=role.lower() + ".v1", contract=None, digest=role_digest)
                role_record = record if role == "RUN_SNAPSHOT" else ArtifactRecord("ART-" + role, role, RunTrack.V5_V6_PREPROD, "CASE-1", None, "RUN-1", "ignored.bin", role_ref.schema_version, role_digest, role_digest, ArtifactItemState.VERIFIED, (), ())
                refs = (snapshot,) if role == "RUN_SNAPSHOT" else (snapshot, role_ref)
                records = (record,) if role == "RUN_SNAPSHOT" else (record, role_record)
                positive = replace(preprod, target_refs=refs, manifest=_manifest(records))
                positive = replace(positive, content_digest=_digest(feedback._preprod_authority_self_excluded_material(positive)))
                assert _binding(_bind(positive)).status == "BOUND"
                changed_role_ref = replace(role_ref, revision_id="rev-other", contract_version="contract.other", source_locator_id="locator.other", captured_at="2026-07-22T03:00:00Z")
                changed_refs = (changed_role_ref,) if role == "RUN_SNAPSHOT" else (snapshot, changed_role_ref)
                ref_nonidentity = replace(preprod, target_refs=changed_refs, manifest=_manifest(records))
                ref_nonidentity = replace(ref_nonidentity, content_digest=_digest(feedback._preprod_authority_self_excluded_material(ref_nonidentity)))
                assert _binding(_bind(ref_nonidentity)).status == "BOUND"
                decoy_record = replace(role_record, path_locator="different.bin", attempts=(), issue_ids=("IGNORED",))
                nonidentity_records = (decoy_record,) if role == "RUN_SNAPSHOT" else (record, decoy_record)
                nonidentity = replace(preprod, target_refs=refs, manifest=_manifest(nonidentity_records))
                nonidentity = replace(nonidentity, content_digest=_digest(feedback._preprod_authority_self_excluded_material(nonidentity)))
                assert _binding(_bind(nonidentity)).status == "BOUND"
        else:
            digest = _digest("decision")
            decision_ref = _ref("DECISION_RUN", "ART-DECISION", schema="decision.v1", contract=None, digest=digest)
            decision_record = ArtifactRecord("ART-DECISION", "DECISION_RUN", RunTrack.V5_V6_PREPROD, "CASE-1", None, "RUN-1", "decision.bin", "decision.v1", digest, digest, ArtifactItemState.VERIFIED, (), ())
            candidate = replace(preprod, target_refs=(decision_ref, snapshot), manifest=_manifest((record, decision_record)))
        candidate = replace(candidate, content_digest=_digest(feedback._preprod_authority_self_excluded_material(candidate)))
        result = _bind(candidate)
        binding = _binding(result)
        receipt = result.current_receipt.item_target_receipts[0]
        if case_id == "P58":
            assert binding.status == "BOUND"
            assert tuple(ref.object_type for ref in binding.target_object_refs) == ("RUN_SNAPSHOT", "DECISION_RUN")
            assert receipt.graph == binding.target_object_refs
        else:
            expected = {
                "P54": ("UNBOUND", "PROTOCOL_GRAPH_INCOMPLETE"),
                "P56": ("INVALID", "INVALID_MATERIAL"),
                "P57": ("UNBOUND", "TARGET_NOT_FOUND"),
            }[case_id]
            assert (binding.status, receipt.non_bound_category) == expected
            assert binding.target_object_refs == () and receipt.graph == ()
        return

    if case_id == "P59":
        result = _bind(_preprod_authority())
        eligibility = _eligibility(_binding(result), None)
        assert eligibility.status == "INELIGIBLE" and eligibility.learning_target_refs == () and eligibility.blocking_reason_codes
        return

    if case_id == "P60":
        result = _bind(authority)
        binding = _binding(result)
        eligibility = _eligibility(binding, authority)
        anchor = authority.anchor_selections[0]
        assert eligibility.status == "ELIGIBLE"
        assert eligibility.learning_target_refs == (anchor.selected_anchor_rule_ref,)
        assert eligibility.excluded_supporting_rule_refs == anchor.non_anchor_rule_refs
        assert eligibility.blocking_reason_codes == () and eligibility.detected_issues == ()
        assert feedback._pinned_anchor_policy().content_digest != feedback._pinned_eligibility_policy().content_digest
        forged_digest = _digest("forged-different-records")
        forged_record = replace(
            authority.manifest.records[0], artifact_id="ART-FORGED",
            expected_digest=forged_digest, observed_digest=forged_digest,
        )
        forged_ref = replace(
            authority.records_projection_refs[0], object_id="ART-FORGED",
            digest_binding=DigestPresent("PRESENT", forged_digest),
        )
        forged_projection = replace(
            authority.records_projection_records[0],
            projected_object_ref=forged_ref,
        )
        forged = replace(
            authority,
            manifest=_manifest((forged_record,)),
            records_projection_refs=(forged_ref,),
            records_projection_records=(forged_projection,),
        )
        forged = _resign_authority(forged)
        assert forged.content_digest == _digest(feedback._production_authority_self_excluded_material(forged))
        rejected = _eligibility(binding, forged)
        assert rejected.status == "INELIGIBLE" and rejected.learning_target_refs == ()
        return

    if case_id == "P61":
        original = authority.statement_set.statements[0]
        statement = replace(
            original,
            feedback_policy="NOT_FEEDBACK_TARGET",
            content_digest=_digest(
                feedback._standard_statement_owner_content_material(
                    replace(original, feedback_policy="NOT_FEEDBACK_TARGET")
                )
            ),
        )
        statement_set = replace(authority.statement_set, statements=(statement,))
        statement_set = replace(
            statement_set,
            content_digest=_digest(
                feedback._statement_set_owner_content_material(statement_set)
            ),
        )
        candidate = replace(authority, statement_set=statement_set)
        candidate = _resign_authority(candidate)
        eligibility = _eligibility(_binding(_bind(authority)), candidate)
        assert eligibility.status == "INELIGIBLE" and eligibility.learning_target_refs == () and eligibility.blocking_reason_codes
        return

    if case_id == "P62":
        with pytest.raises(TypeError):
            feedback.bind_feedback_operation(_raw(authority), prior=None, clock=_Clock(), policy=object())
        return

    if case_id == "P63":
        class Provider:
            calls = 0
            def policy(self):
                self.calls += 1
                return feedback._pinned_anchor_policy()
        provider = Provider()
        with pytest.raises(TypeError):
            feedback.evaluate_learning_eligibility(_binding(_bind(authority)), production_authority=authority, clock=_Clock(), policy_provider=provider)
        assert provider.calls == 0
        assert feedback._pinned_anchor_policy().policy_id != feedback._pinned_eligibility_policy().policy_id
        return

    if case_id == "P64":
        anchor = authority.anchor_selections[0]
        candidate = replace(authority, anchor_selections=(anchor, replace(anchor, anchor_selection_id="ANCHOR-2")))
        result = _bind(_resign_authority(candidate))
        eligibility = _eligibility(_binding(result), _resign_authority(candidate))
        assert _binding(result).status == "AMBIGUOUS" and eligibility.status == "HUMAN_REVIEW"
        assert eligibility.learning_target_refs == ()
        return

    if case_id == "P65":
        invalid = _binding(_bind(authority, items=(_item(locator="bad"),)))
        assert _eligibility(invalid, authority).status == "INELIGIBLE"
        missing = _track_binding(side="SUBMISSION_SOURCE", state="SOURCE_MISSING", reasons=("TRACK_SOURCE_MISSING",))
        unknown = _binding(_bind(authority, source_binding=missing))
        assert unknown.track_match == "UNKNOWN" and _eligibility(unknown, authority).status == "HUMAN_REVIEW"
        return

    if case_id == "P66":
        result = feedback.bind_feedback_operation(_raw(authority), prior=None, clock=_Clock())
        assert result.valid and result.operation_disposition == "NEW_OPERATION" and result.source_identity_relation == "INITIAL"
        assert result.prior_receipt is None and result.overwrite_permitted is False
        return

    if case_id in {"P67", "P68", "P69", "P70"}:
        prior_raw = _raw(authority)
        prior_result = feedback.bind_feedback_operation(prior_raw, prior=None, clock=_Clock())
        prior = feedback.PriorFeedbackOperation(prior_raw, prior_result.current_receipt)
        if case_id == "P67":
            current_raw = _raw(authority, items=(replace(_item(), annotation="changed-source"),))
            current = feedback.bind_feedback_operation(current_raw, prior=prior, clock=_Clock())
            assert current.valid and current.operation_disposition == "NEW_OPERATION" and current.source_identity_relation == "CHANGED"
            assert current.current_receipt.key != prior.receipt.key and current.overwrite_permitted is False
        elif case_id == "P68":
            current_raw = _raw(authority, items=(_item(revision="rev-raw-changed"),))
            current = feedback.bind_feedback_operation(current_raw, prior=prior, clock=_Clock())
            assert current.valid and current.operation_disposition == "NEW_OPERATION"
            assert current.current_receipt.key.canonical_key_digest != prior.receipt.key.canonical_key_digest
        elif case_id == "P69":
            current = feedback.bind_feedback_operation(prior_raw, prior=prior, clock=_Clock())
            assert current.valid and current.operation_disposition == "REUSED_OPERATION" and current.source_identity_relation == "SAME"
            assert current.current_receipt is prior.receipt and current.bindings is prior.receipt.bindings
            assert all(now is before for now, before in zip(current.bindings, prior.receipt.bindings))
            assert current.overwrite_permitted is False
        else:
            anchor = authority.anchor_selections[0]
            selected, supporting = anchor.selected_anchor_rule_ref, anchor.non_anchor_rule_refs[0]
            changed_anchor = replace(anchor, selected_anchor_rule_ref=supporting, non_anchor_rule_refs=(selected,))
            changed_authority = replace(authority, anchor_selections=(changed_anchor,), rule_metadata_receipts=(_metadata(supporting),))
            changed_authority = _resign_authority(changed_authority)
            current = feedback.bind_feedback_operation(_raw(changed_authority), prior=prior, clock=_Clock())
            assert current.valid is False and current.operation_disposition == "TARGET_MISMATCH" and current.source_identity_relation == "SAME"
            assert current.current_key == prior.receipt.key
            assert current.prior_aggregate_target_digest != current.current_aggregate_target_digest
            assert current.bindings == () and len(current.item_target_receipts) == 1
            assert current.item_target_receipts[0].resolution_status == "BOUND"
            assert current.detected_issues == (DetectedIssue("IDEMPOTENCY.DIGEST_MISMATCH", "/feedback/aggregate_target_digest"),)
            assert all("/feedback_bindings/" not in issue.field_path for issue in current.detected_issues)
            assert current.overwrite_permitted is False
        return

    if case_id in {"P71", "P72", "P73", "P74", "P75", "P76", "P77"}:
        authority = _verified_preprod_authority()
        context = feedback._validated_preprod_restricted_manifest_context(authority)
        assert context is not None
        if case_id == "P71":
            candidate = object()
            companion_authority, companion_manifest = authority, authority.manifest
        elif case_id == "P72":
            class ContextSubclass(feedback._PreprodRestrictedManifestContext):
                pass
            candidate = ContextSubclass(*tuple(getattr(context, field.name) for field in fields(context)))
            companion_authority, companion_manifest = authority, authority.manifest
        elif case_id == "P73":
            candidate = context
            companion_authority = _verified_preprod_authority()
            companion_manifest = companion_authority.manifest
        elif case_id == "P74":
            candidate = context
            companion_authority = authority
            companion_manifest = _verified_preprod_authority().manifest
        elif case_id == "P75":
            candidate = replace(context, case_id="CASE:F09:STALE")
            companion_authority, companion_manifest = authority, authority.manifest
        elif case_id == "P76":
            for candidate in (
                replace(context, run_id="RUN:F09:STALE"),
                replace(context, track=RunTrack.PRODUCTION_DEFAULT),
                replace(context, key=replace(context.key, run_id="RUN:F09:STALE")),
                replace(context, roles=("RUN_SNAPSHOT",)),
            ):
                with pytest.raises(F09IntegrityError):
                    feedback._revalidate_preprod_restricted_manifest_context(candidate, authority, authority.manifest)
            return
        else:
            record = authority.manifest.records[0]
            snapshot = SnapshotRef(
                record.artifact_id, "FEEDBACK", (record.artifact_id,), record.schema_version,
                "feedback-contract.v1", record.observed_digest, _NOW, "IMMUTABLE",
            )
            item = _item(run_id=authority.run_id, statement_id=None, revision=None)
            with pytest.raises(F09IntegrityError):
                feedback._revalidate_preprod_restricted_manifest_context(None, authority, authority.manifest)
            with pytest.raises(F09IntegrityError):
                feedback._preprod_target(item, authority, snapshot, _NOW)
            with pytest.raises(F09ContractError):
                feedback._manifest_records_shape(authority.manifest)
            return
        with pytest.raises(F09IntegrityError):
            feedback._revalidate_preprod_restricted_manifest_context(candidate, companion_authority, companion_manifest)
        return

    if case_id == "P78":
        source = Path("engine/f09/feedback.py").read_text(encoding="utf-8")
        baseline = ast.parse(source)
        mutant = ast.parse(
            source
            + "\ndef _mutated_restricted_context_builder(authority):\n"
              "    return _validated_preprod_restricted_manifest_context(authority)\n"
        )
        assert _restricted_context_builder_callers(baseline) == (
            "_preprod_authority_self_excluded_material",
        )
        assert _restricted_context_builder_callers(mutant) != (
            "_preprod_authority_self_excluded_material",
        )
        return

    if case_id == "P79":
        authority = _verified_preprod_authority()
        assert validate_run_artifact_manifest_v1(authority.manifest) == authority.manifest.digest
        assert feedback._validated_preprod_restricted_manifest_context(authority) is not None
        return

    if case_id in {"P80", "P81", "P82", "P83", "P85"}:
        manifest = provision_verified_run_manifest_fixture_v1()
        if case_id == "P80":
            changed = replace(manifest, key=replace(manifest.key, operation="PROJECT_ARTIFACT_SET"))
        elif case_id == "P81":
            records = (manifest.records[1], manifest.records[0], manifest.records[2])
            changed = replace(manifest, records=records, digest=digest_artifact_records(records))
        elif case_id == "P82":
            record = replace(manifest.records[0], attempts=(replace(manifest.records[0].attempts[0], input_snapshot_refs=()),))
            records = (record,) + manifest.records[1:]
            changed = replace(manifest, records=records, digest=digest_artifact_records(records))
        elif case_id == "P83":
            record = replace(manifest.records[0], case_id="CASE:F09:OTHER")
            records = (record,) + manifest.records[1:]
            changed = replace(manifest, records=records, digest=digest_artifact_records(records))
        else:
            changed = replace(manifest, digest=digest_artifact_records(manifest.records[:-1]))
        with pytest.raises((F09ContractError, F09IntegrityError)):
            validate_run_artifact_manifest_v1(changed)
        return

    if case_id == "P84":
        legacy = _preprod_authority().manifest
        before = canonicalize_bounded_jcs(feedback._manifest_identity(legacy))
        assert digest_artifact_records(legacy.records) == legacy.digest
        assert canonicalize_bounded_jcs(feedback._manifest_identity(legacy)) == before
        with pytest.raises(F09ContractError):
            validate_run_artifact_manifest_v1(legacy)
        return

    if case_id in {"P86", "P87", "P88", "P89"}:
        authority = _verified_preprod_authority()
        if case_id == "P86":
            context = feedback._validated_preprod_restricted_manifest_context(authority)
            assert context is not None
            assert feedback._manifest_identity(authority.manifest, restricted_context=context, current_authority=authority) == {"records_digest": feedback._digest_ref_material(authority.manifest.digest)}
            return
        if case_id == "P87":
            for bad_ref in (
                replace(authority.target_refs[3], object_id="RUN-MANIFEST:OTHER"),
                replace(authority.target_refs[3], digest_binding=DigestPresent("PRESENT", _digest("wrong-manifest-digest"))),
            ):
                candidate = replace(authority, target_refs=authority.target_refs[:3] + (bad_ref,))
                with pytest.raises(F09IntegrityError):
                    feedback._validated_preprod_restricted_manifest_context(candidate)
            return
        if case_id == "P88":
            duplicate = replace(authority, target_refs=authority.target_refs + (authority.target_refs[3],))
            with pytest.raises(F09IntegrityError):
                feedback._validated_preprod_restricted_manifest_context(duplicate)
            record = replace(authority.manifest.records[0], artifact_role="MANIFEST")
            records = (record,) + authority.manifest.records[1:]
            with pytest.raises(F09IntegrityError):
                validate_run_artifact_manifest_v1(replace(authority.manifest, records=records, digest=digest_artifact_records(records)))
            return
        record = authority.manifest.records[0]
        snapshot = SnapshotRef(
            record.artifact_id, "FEEDBACK", (record.artifact_id,), record.schema_version,
            "feedback-contract.v1", record.observed_digest, _NOW, "IMMUTABLE",
        )
        item = _item(run_id=authority.run_id, statement_id=None, revision=None)
        context = feedback._validated_preprod_restricted_manifest_context(authority)
        assert context is not None
        assert feedback._preprod_target(
            item, authority, snapshot, _NOW, restricted_context=context,
        )[0] == "BOUND"
        changed_ref = replace(authority.target_refs[0], object_id="RUN-ARTIFACT:OTHER")
        changed = replace(authority, target_refs=(changed_ref,) + authority.target_refs[1:])
        with pytest.raises(F09IntegrityError):
            feedback._validated_preprod_restricted_manifest_context(changed)
        return

    if case_id in {"P90", "P91", "P92", "P93", "P94"}:
        source = Path("engine/f09/feedback.py").read_text(encoding="utf-8")
        if case_id == "P90":
            def has_no_artifacts_private_import(tree):
                return not any(
                    alias.name.startswith("_")
                    for node in tree.body
                    if isinstance(node, ast.ImportFrom) and node.module == "engine.f09.artifacts"
                    for alias in node.names
                )
            baseline = ast.parse(source)
            mutant = ast.parse("from engine.f09.artifacts import _private_run_builder\n" + source)
            assert has_no_artifacts_private_import(baseline)
            assert not has_no_artifacts_private_import(mutant)
            return
        if case_id == "P91":
            def has_no_run_digest_copy(tree):
                forbidden_definitions = {
                    node.name for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef)
                    and (node.name.startswith("_digest_run_") or node.name == "canonicalize_artifact_records")
                }
                forbidden_calls = {
                    node.func.id for node in ast.walk(tree)
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id in {"canonicalize_artifact_records", "_digest_run_artifact_set_key_v1"}
                }
                run_key_preimages = {
                    node.name for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef)
                    if any(
                        isinstance(value, ast.Constant)
                        and value.value == "f09.run-artifact-set.key.v1"
                        for value in ast.walk(node)
                    )
                }
                return not forbidden_definitions and not forbidden_calls and not run_key_preimages
            baseline = ast.parse(source)
            named_mutant = ast.parse(source + "\ndef _digest_run_artifact_set_key_v1():\n    return canonicalize_artifact_records(())\n")
            renamed_preimage_mutant = ast.parse(source + "\ndef _renamed_run_preimage():\n    return {'domain': 'f09.run-artifact-set.key.v1'}\n")
            nested_preimage_mutant = ast.parse(source + "\ndef _wrapper():\n    def _renamed_nested_run_preimage():\n        return {'domain': 'f09.run-artifact-set.key.v1'}\n    return _renamed_nested_run_preimage\n")
            assert has_no_run_digest_copy(baseline)
            assert not has_no_run_digest_copy(named_mutant)
            assert not has_no_run_digest_copy(renamed_preimage_mutant)
            assert not has_no_run_digest_copy(nested_preimage_mutant)
            return
        authority = _verified_preprod_authority()
        if case_id == "P92":
            def unavailable(manifest):
                raise F09IntegrityError("RUN_ARTIFACT.UNAVAILABLE", "/manifest", "public verifier unavailable")
            monkeypatch = pytest.MonkeyPatch()
            monkeypatch.setattr(feedback, "validate_run_artifact_manifest_v1", unavailable)
            try:
                with pytest.raises(F09IntegrityError):
                    feedback._validated_preprod_restricted_manifest_context(authority)
            finally:
                monkeypatch.undo()
            return
        if case_id == "P93":
            calls = []
            original = feedback.validate_run_artifact_manifest_v1
            monkeypatch = pytest.MonkeyPatch()
            monkeypatch.setattr(feedback, "validate_run_artifact_manifest_v1", lambda manifest: calls.append(manifest) or original(manifest))
            try:
                assert feedback._validated_preprod_restricted_manifest_context(authority) is not None
            finally:
                monkeypatch.undo()
            assert calls == [authority.manifest]
            return
        calls = []
        monkeypatch = pytest.MonkeyPatch()
        for name in ("bind_feedback_operation", "evaluate_learning_eligibility", "validate_learning_eligibility"):
            monkeypatch.setattr(feedback, name, lambda *args, _name=name, **kwargs: calls.append(_name))
        try:
            invalid = replace(authority, target_refs=authority.target_refs[:3])
            with pytest.raises(F09IntegrityError):
                feedback._validated_preprod_restricted_manifest_context(invalid)
        finally:
            monkeypatch.undo()
        assert calls == []
        return

    raise AssertionError(f"unhandled contract oracle {case_id}: {falsifier}")
