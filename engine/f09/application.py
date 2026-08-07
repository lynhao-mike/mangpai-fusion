from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping

from engine.f09.artifacts import (
    ArtifactSetManifest,
    IdempotencyKey,
    ManifestOuterRefRequestV1,
    RunArtifactSetKeyV1,
    RunArtifactSetRequestV1,
    RunArtifactTargetRefsRequestV1,
    coordinate_artifact_operation,
    coordinate_run_artifact_set_with_target_refs_v1,
)
from engine.f09.contracts import (
    ArtifactSetState,
    ContractVersionRef,
    NormalizedEvidenceReadPort,
    FrozenContractReadPort,
    RunTrack,
)
from engine.f09.decision import (
    CompetitionInput,
    DecisionEvaluationResult,
    GateEvaluationInput,
    RootInput,
    TimingInput,
    evaluate_f09,
)
from engine.f09.errors import F09ContractError, F09Error
from engine.f09.evidence import EvidenceRecord, NormalizedEvidencePackage, build_f09_evidence_package
from engine.f09.feedback import PreprodRunAuthority, construct_preprod_run_authority_v1
from engine.f09.operator_diagnostics import persist_phase_observation_log
from engine.f09.trace import (
    ProjectionValidationResult,
    StatementSet,
    TraceEnvelope,
    VersionedObjectRef,
    build_statement_set,
    build_trace,
    validate_statement_projection,
)


@dataclass(frozen=True)
class F09RunRequest:
    case_id: str
    mode: Literal[
        "STAGED_AUDIT",
        "PREPROD_SHADOW",
        "PRODUCTION_DEFAULT",
    ]
    chart_records: tuple[EvidenceRecord, ...]
    hypothesis_records: tuple[EvidenceRecord, ...]
    normalized_evidence_port: NormalizedEvidenceReadPort
    frozen_contract_port: FrozenContractReadPort
    request_id: str
    contract_ref: ContractVersionRef
    normative_contract_ref: VersionedObjectRef
    machine_appendix_ref: VersionedObjectRef
    artifact_projections: Mapping[str, bytes]
    artifact_key: IdempotencyKey
    existing_manifest: ArtifactSetManifest | None
    attempt_id: str
    enable_f09: bool = False
    markdown_path: Path = Path(
        "engine/contracts/12-real-world-function-evidence-cards-v1.md"
    )
    snapshot_path: Path = Path(
        "plans/production-implementation-pi-300-f09-source-snapshots-v1.json"
    )
    artifact_root: Path | None = None
    now: str = ""


@dataclass(frozen=True)
class F09Observation:
    event: Literal["F09_SLICE_PHASE"]
    case_id: str
    mode: str
    phase: Literal[
        "SOURCE_PREFLIGHT",
        "EVIDENCE",
        "DECISION",
        "TRACE",
        "ARTIFACT",
    ]
    status: Literal["SUCCEEDED", "FAILED", "REJECTED"]
    issue_codes: tuple[str, ...]
    artifact_set_state: str | None


@dataclass(frozen=True)
class F09RunResult:
    request: F09RunRequest
    evidence: NormalizedEvidencePackage | None
    decision: DecisionEvaluationResult | None
    trace: TraceEnvelope | None
    statement_set: StatementSet | None
    manifest: ArtifactSetManifest | None
    observations: tuple[F09Observation, ...]
    stopped_at: Literal[
        "SOURCE_PREFLIGHT",
        "EVIDENCE",
        "DECISION",
        "TRACE",
        "ARTIFACT",
    ] | None


@dataclass(frozen=True)
class F09RunExecutionResultV1:
    run_result: F09RunResult
    preprod_authority: PreprodRunAuthority | None
    unsupported_reason: Literal["STAGED_L6_UNSUPPORTED"] | None


_TRACK_BY_MODE = {
    "STAGED_AUDIT": RunTrack.STAGED_L6,
    "PREPROD_SHADOW": RunTrack.V5_V6_PREPROD,
}


def _observation(
    request: F09RunRequest,
    phase: Literal["SOURCE_PREFLIGHT", "EVIDENCE", "DECISION", "TRACE", "ARTIFACT"],
    status: Literal["SUCCEEDED", "FAILED", "REJECTED"],
    issue_codes: tuple[str, ...] = (),
    artifact_set_state: str | None = None,
) -> F09Observation:
    return F09Observation(
        "F09_SLICE_PHASE", request.case_id, request.mode, phase, status,
        issue_codes, artifact_set_state,
    )


def _result(
    request: F09RunRequest,
    evidence: NormalizedEvidencePackage | None,
    decision: DecisionEvaluationResult | None,
    trace: TraceEnvelope | None,
    statement_set: StatementSet | None,
    manifest: ArtifactSetManifest | None,
    observations: list[F09Observation],
    stopped_at: Literal["SOURCE_PREFLIGHT", "EVIDENCE", "DECISION", "TRACE", "ARTIFACT"] | None,
) -> F09RunResult:
    result = F09RunResult(
        request, evidence, decision, trace, statement_set, manifest,
        tuple(observations), stopped_at,
    )
    if isinstance(request.artifact_root, Path):
        persist_phase_observation_log(request, result.observations, stopped_at)
    return result


def run_f09_slice(
    request: F09RunRequest,
    *,
    gate_inputs: tuple[GateEvaluationInput, ...],
    competition_input: CompetitionInput,
    root_input: RootInput,
    timing_input: TimingInput,
) -> F09RunResult:
    observations: list[F09Observation] = []
    rejection: F09ContractError | None = None
    if request.enable_f09 is not True:
        rejection = F09ContractError("APPLICATION.OPT_IN_REQUIRED", "/enable_f09")
    elif request.mode == "PRODUCTION_DEFAULT":
        rejection = F09ContractError("APPLICATION.PRODUCTION_DEFAULT_FORBIDDEN", "/mode")
    elif request.mode not in _TRACK_BY_MODE:
        rejection = F09ContractError("APPLICATION.MODE_UNSUPPORTED", "/mode")
    elif request.artifact_root is None:
        rejection = F09ContractError("APPLICATION.ARTIFACT_ROOT_REQUIRED", "/artifact_root")
    if rejection is not None:
        observations.append(_observation(request, "SOURCE_PREFLIGHT", "REJECTED", (rejection.issue_code,)))
        return _result(request, None, None, None, None, None, observations, "SOURCE_PREFLIGHT")

    mapped_track = _TRACK_BY_MODE[request.mode]
    observations.append(_observation(request, "SOURCE_PREFLIGHT", "SUCCEEDED"))
    try:
        evidence = build_f09_evidence_package(
            case_id=request.case_id, track=mapped_track,
            markdown_path=request.markdown_path, snapshot_path=request.snapshot_path,
            chart_records=request.chart_records, hypothesis_records=request.hypothesis_records,
        )
    except F09Error as error:
        observations.append(_observation(request, "EVIDENCE", "FAILED", (error.issue_code,)))
        return _result(request, None, None, None, None, None, observations, "EVIDENCE")
    observations.append(_observation(request, "EVIDENCE", "SUCCEEDED"))

    try:
        decision = evaluate_f09(
            evidence, normalized_evidence_port=request.normalized_evidence_port,
            frozen_contract_port=request.frozen_contract_port, request_id=request.request_id,
            contract_ref=request.contract_ref, gate_inputs=gate_inputs,
            competition_input=competition_input, root_input=root_input,
            timing_input=timing_input, produced_at=request.now,
        )
    except F09Error as error:
        observations.append(_observation(request, "DECISION", "FAILED", (error.issue_code,)))
        return _result(request, evidence, None, None, None, None, observations, "DECISION")
    observations.append(_observation(request, "DECISION", "SUCCEEDED"))

    try:
        trace = build_trace(
            evidence, decision, normative_contract_ref=request.normative_contract_ref,
            machine_appendix_ref=request.machine_appendix_ref, created_at=request.now,
        )
    except F09Error as error:
        observations.append(_observation(request, "TRACE", "FAILED", (error.issue_code,)))
        return _result(request, evidence, decision, None, None, None, observations, "TRACE")
    try:
        statement_set = build_statement_set(
            trace, decision, normative_contract_ref=request.normative_contract_ref,
            machine_appendix_ref=request.machine_appendix_ref, generated_at=request.now,
        )
    except F09Error as error:
        observations.append(_observation(request, "TRACE", "FAILED", (error.issue_code,)))
        return _result(request, evidence, decision, trace, None, None, observations, "TRACE")
    try:
        projection_validation: ProjectionValidationResult = validate_statement_projection(
            statement_set, trace, decision, evidence,
            normative_contract_ref=request.normative_contract_ref,
            machine_appendix_ref=request.machine_appendix_ref,
        )
    except F09Error as error:
        observations.append(_observation(request, "TRACE", "FAILED", (error.issue_code,)))
        return _result(request, evidence, decision, trace, statement_set, None, observations, "TRACE")
    projection_issues = tuple(issue.issue_code for issue in projection_validation.detected_issues)
    if projection_validation.valid is not True or projection_issues:
        observations.append(_observation(request, "TRACE", "FAILED", projection_issues))
        return _result(request, evidence, decision, trace, statement_set, None, observations, "TRACE")
    observations.append(_observation(request, "TRACE", "SUCCEEDED"))

    try:
        manifest = coordinate_artifact_operation(
            request.artifact_root, statement_set, request.artifact_projections,
            existing_manifest=request.existing_manifest, key=request.artifact_key,
            attempt_id=request.attempt_id, now=request.now,
        )
    except F09Error as error:
        observations.append(_observation(request, "ARTIFACT", "FAILED", (error.issue_code,)))
        return _result(request, evidence, decision, trace, statement_set, None, observations, "ARTIFACT")
    manifest_issues = tuple(issue.issue_code for issue in manifest.detected_issues)
    state = manifest.state.value
    if manifest.state is ArtifactSetState.COMPLETE_VERIFIED and not manifest_issues:
        observations.append(_observation(request, "ARTIFACT", "SUCCEEDED", manifest_issues, state))
        return _result(request, evidence, decision, trace, statement_set, manifest, observations, None)
    observations.append(_observation(request, "ARTIFACT", "FAILED", manifest_issues, state))
    return _result(request, evidence, decision, trace, statement_set, manifest, observations, "ARTIFACT")


def run_f09_slice_with_execution_authority_v1(
    request: F09RunRequest,
    *,
    run_artifact_request: RunArtifactSetRequestV1,
    target_refs_request: RunArtifactTargetRefsRequestV1,
    manifest_outer_ref_request: ManifestOuterRefRequestV1,
    existing_run_manifest: ArtifactSetManifest | None,
    gate_inputs: tuple[GateEvaluationInput, ...],
    competition_input: CompetitionInput,
    root_input: RootInput,
    timing_input: TimingInput,
) -> F09RunExecutionResultV1:
    run_result = run_f09_slice(
        request,
        gate_inputs=gate_inputs,
        competition_input=competition_input,
        root_input=root_input,
        timing_input=timing_input,
    )
    if run_result.stopped_at is not None:
        return F09RunExecutionResultV1(run_result, None, None)

    if type(run_artifact_request) is not RunArtifactSetRequestV1:
        raise F09ContractError(
            "APPLICATION.RUN_ARTIFACT_REQUEST_INVALID",
            "/run_artifact_request",
        )
    if type(run_artifact_request.key) is not RunArtifactSetKeyV1:
        raise F09ContractError(
            "APPLICATION.RUN_ARTIFACT_KEY_INVALID",
            "/run_artifact_request/key",
        )

    mapped_track = _TRACK_BY_MODE.get(request.mode)
    if mapped_track is None:
        raise F09ContractError("APPLICATION.VERSIONED_MODE_UNSUPPORTED", "/mode")
    if run_artifact_request.key.case_id != request.case_id:
        raise F09ContractError("APPLICATION.RUN_CASE_MISMATCH", "/run_artifact_request/key/case_id")
    if run_artifact_request.key.run_id != run_artifact_request.run_id:
        raise F09ContractError("APPLICATION.RUN_ID_MISMATCH", "/run_artifact_request/run_id")
    if run_artifact_request.key.track is not mapped_track:
        raise F09ContractError("APPLICATION.RUN_TRACK_MISMATCH", "/run_artifact_request/key/track")

    if mapped_track is RunTrack.STAGED_L6:
        return F09RunExecutionResultV1(run_result, None, "STAGED_L6_UNSUPPORTED")

    run_artifact_set_result = coordinate_run_artifact_set_with_target_refs_v1(
        request.artifact_root,
        run_artifact_request,
        target_refs_request=target_refs_request,
        manifest_outer_ref_request=manifest_outer_ref_request,
        existing_manifest=existing_run_manifest,
        attempt_id=request.attempt_id,
        now=request.now,
    )
    preprod_authority = construct_preprod_run_authority_v1(
        run_artifact_set_result=run_artifact_set_result,
    )
    return F09RunExecutionResultV1(run_result, preprod_authority, None)
