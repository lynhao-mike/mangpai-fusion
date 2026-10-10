"""无反馈 BLIND_BASELINE 的领域契约、盲态投影与纯运行器。"""
from __future__ import annotations

import dataclasses as _dataclasses
import datetime as _datetime
import hashlib as _hashlib
import json as _json
import re as _re
from enum import Enum as _Enum
from typing import Any as _Any

from engine.asof.consultation_freeze import (
    CareerBlindDraft,
    CareerFreezePackage,
    compute_freeze_package_sha256,
    freeze_career_draft,
    freeze_package_to_canonical_bytes,
)
from engine.asof.future_projection import (
    UnsupportedDomainProjection,
    UnsupportedDomainStatus,
)
from engine.asof.session_contract import (
    BlindChartInput,
    ConsultationState,
    SessionEnvelope,
    SessionIdentity,
    create_initial_envelope,
    transition_session,
)
from engine.asof.state_ledger import DecisionAction


BLIND_BASELINE_PAYLOAD_SCHEMA_VERSION = "asof-blind-baseline-payload/v1"
QUESTION_SNAPSHOT_SCHEMA_VERSION = "asof-baseline-question-snapshot/v1"
RUNTIME_SNAPSHOT_SCHEMA_VERSION = "asof-baseline-runtime-snapshot/v1"
INPUT_ACCESS_SCHEMA_VERSION = "asof-baseline-input-access/v1"
CURRENT_STATE_SCHEMA_VERSION = "asof-blind-current-state/v1"
FUTURE_PROJECTION_SCHEMA_VERSION = "asof-blind-future-projection/v1"

_SHA256 = _re.compile(r"[0-9a-f]{64}\Z")
_UTC_TIMESTAMP = _re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z\Z"
)
_PROBE_MARKERS = frozenset(
    {
        "STRUCTURAL_PROBE_ONLY",
        "NO_CAREER_INFERENCE",
        "PROOF_SEAM_IS_NOT_A_CAREER_PREDICTION",
        "ANY_REAL_CAREER_CLAIM",
        "ACCURACY_INFERENCE",
        "prospective-asof-structural-probe/v1",
    }
)


class BlindBaselineError(ValueError):
    CODES = frozenset(
        {
            "INVALID_TYPE",
            "INVALID_VALUE",
            "IDENTITY_MISMATCH",
            "REFERENCE_MISMATCH",
            "DUPLICATE_ID",
            "INVALID_PROJECTION",
            "PROBE_NOT_PREDICTION",
            "HASH_MISMATCH",
        }
    )

    def __init__(self, code: str, message: str) -> None:
        if code not in self.CODES:
            raise ValueError("unknown blind baseline error code")
        self.code = code
        super().__init__(f"{code}: {message}")


def _error(code: str, message: str) -> BlindBaselineError:
    return BlindBaselineError(code, message)


def _text(value: object, field: str) -> str:
    if type(value) is not str:
        raise _error("INVALID_TYPE", f"{field} must be str")
    if not value.strip():
        raise _error("INVALID_VALUE", f"{field} must not be empty")
    return value


def _optional_text(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _text(value, field)


def _date(value: object, field: str) -> _datetime.date:
    if type(value) is not _datetime.date:
        raise _error("INVALID_TYPE", f"{field} must be date")
    return value


def _strings(
    value: object,
    field: str,
    *,
    non_empty: bool = False,
) -> tuple[str, ...]:
    if type(value) is not tuple or any(
        type(item) is not str or not item.strip() for item in value
    ):
        raise _error("INVALID_TYPE", f"{field} must be tuple[str, ...]")
    if non_empty and not value:
        raise _error("INVALID_VALUE", f"{field} must not be empty")
    if len(value) != len(set(value)):
        raise _error("DUPLICATE_ID", f"{field} contains duplicates")
    return value


def _digest(value: object, field: str) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise _error("INVALID_VALUE", f"{field} must be lowercase SHA-256")
    return value


def _timestamp(value: object, field: str) -> _datetime.datetime:
    if type(value) is not str or _UTC_TIMESTAMP.fullmatch(value) is None:
        raise _error("INVALID_VALUE", f"{field} must be an ISO 8601 UTC timestamp")
    try:
        parsed = _datetime.datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise _error("INVALID_VALUE", f"{field} is invalid") from exc
    if parsed.tzinfo != _datetime.timezone.utc:
        raise _error("INVALID_VALUE", f"{field} must be UTC")
    return parsed


def _percent(value: object, field: str) -> int:
    if type(value) is not int:
        raise _error("INVALID_TYPE", f"{field} must be int")
    if not 0 <= value <= 100:
        raise _error("INVALID_VALUE", f"{field} must be between 0 and 100")
    return value


def _duplicates(values: tuple[str, ...]) -> bool:
    return len(values) != len(set(values))


class ArtifactKind(str, _Enum):
    BLIND_BASELINE = "BLIND_BASELINE"
    VERIFIED_STATE_REVISION = "VERIFIED_STATE_REVISION"
    CALIBRATED_REVISION = "CALIBRATED_REVISION"


class BlindHypothesisRole(str, _Enum):
    PRIMARY = "PRIMARY"
    CONDITIONAL = "CONDITIONAL"


@_dataclasses.dataclass(frozen=True, slots=True)
class ArtifactReference:
    artifact_path: str
    artifact_sha256: str

    def __post_init__(self) -> None:
        _text(self.artifact_path, "artifact_path")
        _digest(self.artifact_sha256, "artifact_sha256")


@_dataclasses.dataclass(frozen=True, slots=True)
class BaselineQuestionSnapshot:
    schema_version: str
    question_id: str
    task_id: str
    question_text_redacted: str
    outcome_type: str
    positive_definition: str
    negative_definition: str
    observation_window_start: str
    observation_window_end: str
    source: ArtifactReference

    def __post_init__(self) -> None:
        if self.schema_version != QUESTION_SNAPSHOT_SCHEMA_VERSION:
            raise _error("INVALID_VALUE", "question snapshot schema version mismatch")
        _text(self.question_id, "question_id")
        _text(self.task_id, "task_id")
        _text(self.question_text_redacted, "question_text_redacted")
        if self.outcome_type != "binary":
            raise _error("INVALID_VALUE", "Phase 1 question outcome_type must be binary")
        _text(self.positive_definition, "positive_definition")
        _text(self.negative_definition, "negative_definition")
        start = _timestamp(self.observation_window_start, "observation_window_start")
        end = _timestamp(self.observation_window_end, "observation_window_end")
        if end <= start:
            raise _error("INVALID_VALUE", "question observation window is reversed")
        if type(self.source) is not ArtifactReference:
            raise _error("INVALID_TYPE", "question source must be ArtifactReference")


@_dataclasses.dataclass(frozen=True, slots=True)
class BaselineRuntimeSnapshot:
    schema_version: str
    rule_snapshot_id: str
    rule_snapshot_sha256: str
    code_version: str
    model_id: str

    def __post_init__(self) -> None:
        if self.schema_version != RUNTIME_SNAPSHOT_SCHEMA_VERSION:
            raise _error("INVALID_VALUE", "runtime snapshot schema version mismatch")
        _text(self.rule_snapshot_id, "rule_snapshot_id")
        _digest(self.rule_snapshot_sha256, "rule_snapshot_sha256")
        _text(self.code_version, "code_version")
        _text(self.model_id, "model_id")


@_dataclasses.dataclass(frozen=True, slots=True)
class BlindInputAccessDeclaration:
    schema_version: str
    accessed_inputs: tuple[str, ...]
    feedback_accessed: bool
    verification_accessed: bool
    known_facts_accessed: bool

    def __post_init__(self) -> None:
        if self.schema_version != INPUT_ACCESS_SCHEMA_VERSION:
            raise _error("INVALID_VALUE", "input access schema version mismatch")
        expected = (
            "blind_chart_input",
            "career_blind_draft",
            "question_snapshot",
            "blind_current_state_snapshot",
            "blind_projection_input",
            "rule_snapshot",
        )
        if self.accessed_inputs != expected:
            raise _error("INVALID_VALUE", "blind input access whitelist differs")
        if any(
            type(value) is not bool
            for value in (
                self.feedback_accessed,
                self.verification_accessed,
                self.known_facts_accessed,
            )
        ):
            raise _error("INVALID_TYPE", "input access flags must be exact bool")
        if self.feedback_accessed or self.verification_accessed or self.known_facts_accessed:
            raise _error("INVALID_VALUE", "BLIND_BASELINE cannot access revealed facts")


@_dataclasses.dataclass(frozen=True, slots=True)
class BlindStateHypothesis:
    case_id: str
    as_of_date: _datetime.date
    hypothesis_id: str
    domain: str
    role: BlindHypothesisRole
    center: str
    reasonable_range: tuple[str, ...]
    strongest_alternative: str
    source_fundamental_ids: tuple[str, ...]
    source_event_ids: tuple[str, ...]
    evidence_chain: tuple[str, ...]
    assumed_open_path_ids: tuple[str, ...]
    conditions: tuple[str, ...]
    falsifiers: tuple[str, ...]
    confidence_percent: int
    decision_action: DecisionAction

    def __post_init__(self) -> None:
        _text(self.case_id, "case_id")
        _date(self.as_of_date, "as_of_date")
        _text(self.hypothesis_id, "hypothesis_id")
        _text(self.domain, "domain")
        if type(self.role) is not BlindHypothesisRole:
            raise _error("INVALID_TYPE", "role must be BlindHypothesisRole")
        _text(self.center, "center")
        _strings(self.reasonable_range, "reasonable_range", non_empty=True)
        _text(self.strongest_alternative, "strongest_alternative")
        fundamentals = _strings(
            self.source_fundamental_ids,
            "source_fundamental_ids",
        )
        events = _strings(self.source_event_ids, "source_event_ids")
        if not fundamentals and not events:
            raise _error(
                "INVALID_VALUE",
                "blind state hypothesis requires a frozen source reference",
            )
        _strings(self.evidence_chain, "evidence_chain", non_empty=True)
        _strings(self.assumed_open_path_ids, "assumed_open_path_ids")
        _strings(self.conditions, "conditions")
        _strings(self.falsifiers, "falsifiers", non_empty=True)
        _percent(self.confidence_percent, "confidence_percent")
        if type(self.decision_action) is not DecisionAction:
            raise _error("INVALID_TYPE", "decision_action must be DecisionAction")
        if self.role is BlindHypothesisRole.PRIMARY:
            if self.decision_action is not DecisionAction.OUTPUT:
                raise _error("INVALID_VALUE", "primary blind state must be OUTPUT")
        elif self.decision_action not in {
            DecisionAction.CONDITIONAL,
            DecisionAction.ASK,
        }:
            raise _error(
                "INVALID_VALUE",
                "conditional blind state must remain CONDITIONAL or ASK",
            )


@_dataclasses.dataclass(frozen=True, slots=True)
class BlindCurrentStateSnapshot:
    schema_version: str
    case_id: str
    as_of_date: _datetime.date
    primary_hypothesis_id: str
    hypotheses: tuple[BlindStateHypothesis, ...]

    def __post_init__(self) -> None:
        if self.schema_version != CURRENT_STATE_SCHEMA_VERSION:
            raise _error("INVALID_VALUE", "blind current-state schema version mismatch")
        _text(self.case_id, "case_id")
        _date(self.as_of_date, "as_of_date")
        _text(self.primary_hypothesis_id, "primary_hypothesis_id")
        if type(self.hypotheses) is not tuple or not self.hypotheses or any(
            type(item) is not BlindStateHypothesis for item in self.hypotheses
        ):
            raise _error(
                "INVALID_TYPE",
                "hypotheses must be a non-empty tuple[BlindStateHypothesis, ...]",
            )
        identifiers = tuple(item.hypothesis_id for item in self.hypotheses)
        if _duplicates(identifiers):
            raise _error("DUPLICATE_ID", "duplicate blind state hypothesis id")
        primary = tuple(
            item
            for item in self.hypotheses
            if item.role is BlindHypothesisRole.PRIMARY
        )
        conditional = tuple(
            item
            for item in self.hypotheses
            if item.role is BlindHypothesisRole.CONDITIONAL
        )
        if len(primary) != 1 or primary[0].hypothesis_id != self.primary_hypothesis_id:
            raise _error("INVALID_VALUE", "blind current state requires one exact primary")
        if len(conditional) > 2:
            raise _error("INVALID_VALUE", "at most two blind conditional states are allowed")
        if any(
            item.case_id != self.case_id or item.as_of_date != self.as_of_date
            for item in self.hypotheses
        ):
            raise _error("IDENTITY_MISMATCH", "blind state hypothesis identity differs")


@_dataclasses.dataclass(frozen=True, slots=True)
class BlindFutureCandidate:
    case_id: str
    as_of_date: _datetime.date
    candidate_id: str
    domain: str
    basis_hypothesis_id: str
    conclusion: str
    window_start: _datetime.date
    window_end: _datetime.date
    center: str
    alternatives: tuple[str, ...]
    evidence_chain: tuple[str, ...]
    conditions: tuple[str, ...]
    falsifiers: tuple[str, ...]
    confidence_percent: int
    decision_action: DecisionAction

    def __post_init__(self) -> None:
        _text(self.case_id, "case_id")
        _date(self.as_of_date, "as_of_date")
        _text(self.candidate_id, "candidate_id")
        if self.domain not in {"career", "wealth"}:
            raise _error("INVALID_VALUE", "Phase 1 supports only career and wealth")
        _text(self.basis_hypothesis_id, "basis_hypothesis_id")
        _text(self.conclusion, "conclusion")
        start = _date(self.window_start, "window_start")
        end = _date(self.window_end, "window_end")
        if start < self.as_of_date or end < start:
            raise _error("INVALID_VALUE", "future candidate window is invalid")
        _text(self.center, "center")
        _strings(self.alternatives, "alternatives")
        _strings(self.evidence_chain, "evidence_chain", non_empty=True)
        _strings(self.conditions, "conditions")
        _strings(self.falsifiers, "falsifiers", non_empty=True)
        _percent(self.confidence_percent, "confidence_percent")
        if type(self.decision_action) is not DecisionAction:
            raise _error("INVALID_TYPE", "decision_action must be DecisionAction")
        if self.decision_action not in {
            DecisionAction.OUTPUT,
            DecisionAction.CONDITIONAL,
            DecisionAction.ASK,
        }:
            raise _error("INVALID_VALUE", "future candidate action is unsupported")


@_dataclasses.dataclass(frozen=True, slots=True)
class BlindWealthBinding:
    edge_id: str
    source_career_candidate_id: str
    target_wealth_candidate_id: str
    required_conditions: tuple[str, ...]
    falsifiers: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.edge_id, "edge_id")
        _text(self.source_career_candidate_id, "source_career_candidate_id")
        _text(self.target_wealth_candidate_id, "target_wealth_candidate_id")
        _strings(self.required_conditions, "required_conditions")
        _strings(self.falsifiers, "falsifiers")


@_dataclasses.dataclass(frozen=True, slots=True)
class BlindProjectionInput:
    candidates: tuple[BlindFutureCandidate, ...]
    wealth_bindings: tuple[BlindWealthBinding, ...]

    def __post_init__(self) -> None:
        if type(self.candidates) is not tuple or any(
            type(item) is not BlindFutureCandidate for item in self.candidates
        ):
            raise _error(
                "INVALID_TYPE",
                "candidates must be tuple[BlindFutureCandidate, ...]",
            )
        if type(self.wealth_bindings) is not tuple or any(
            type(item) is not BlindWealthBinding for item in self.wealth_bindings
        ):
            raise _error(
                "INVALID_TYPE",
                "wealth_bindings must be tuple[BlindWealthBinding, ...]",
            )


@_dataclasses.dataclass(frozen=True, slots=True)
class BlindConditionalProjection:
    state_hypothesis: BlindStateHypothesis
    career_predictions: tuple[BlindFutureCandidate, ...]
    wealth_predictions: tuple[BlindFutureCandidate, ...]


@_dataclasses.dataclass(frozen=True, slots=True)
class BlindFutureProjection:
    schema_version: str
    case_id: str
    as_of_date: _datetime.date
    primary_hypothesis_id: str
    career_mainline: tuple[BlindFutureCandidate, ...]
    wealth_mainline: tuple[BlindFutureCandidate, ...]
    conditional_branches: tuple[BlindConditionalProjection, ...]
    wealth_bindings: tuple[BlindWealthBinding, ...]
    unsupported_domains: tuple[UnsupportedDomainProjection, ...]


@_dataclasses.dataclass(frozen=True, slots=True)
class BlindBaselineRunResult:
    artifact_kind: ArtifactKind
    final_envelope: SessionEnvelope
    freeze_package: CareerFreezePackage
    freeze_package_sha256: str
    question_snapshot: BaselineQuestionSnapshot
    runtime_snapshot: BaselineRuntimeSnapshot
    input_access: BlindInputAccessDeclaration
    current_state: BlindCurrentStateSnapshot
    projection: BlindFutureProjection


def _contains_probe_marker(value: object) -> bool:
    if _dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _contains_probe_marker(
            {
                field.name: getattr(value, field.name)
                for field in _dataclasses.fields(value)
            }
        )
    if isinstance(value, dict):
        return any(
            _contains_probe_marker(key) or _contains_probe_marker(item)
            for key, item in value.items()
        )
    if isinstance(value, (tuple, list)):
        return any(_contains_probe_marker(item) for item in value)
    if isinstance(value, str):
        return any(marker in value for marker in _PROBE_MARKERS)
    return False


def _validate_state_sources(
    state: BlindCurrentStateSnapshot,
    package: CareerFreezePackage,
) -> None:
    fundamental_ids = {item.fundamental_id for item in package.fundamentals}
    event_ids = {item.candidate.candidate_id for item in package.events}
    for hypothesis in state.hypotheses:
        if not set(hypothesis.source_fundamental_ids).issubset(fundamental_ids):
            raise _error(
                "REFERENCE_MISMATCH",
                "blind state references unknown frozen fundamental",
            )
        if not set(hypothesis.source_event_ids).issubset(event_ids):
            raise _error(
                "REFERENCE_MISMATCH",
                "blind state references unknown frozen event",
            )


def project_future_from_blind_state(
    *,
    state: BlindCurrentStateSnapshot,
    projection_input: BlindProjectionInput,
) -> BlindFutureProjection:
    if type(state) is not BlindCurrentStateSnapshot:
        raise _error("INVALID_TYPE", "state must be BlindCurrentStateSnapshot")
    if type(projection_input) is not BlindProjectionInput:
        raise _error("INVALID_TYPE", "projection_input must be BlindProjectionInput")

    hypotheses = {item.hypothesis_id: item for item in state.hypotheses}
    candidates = projection_input.candidates
    candidate_ids = tuple(item.candidate_id for item in candidates)
    if _duplicates(candidate_ids):
        raise _error("DUPLICATE_ID", "duplicate blind future candidate id")
    for candidate in candidates:
        if candidate.case_id != state.case_id or candidate.as_of_date != state.as_of_date:
            raise _error("IDENTITY_MISMATCH", "future candidate identity differs")
        if candidate.basis_hypothesis_id not in hypotheses:
            raise _error(
                "REFERENCE_MISMATCH",
                "future candidate references unknown blind state hypothesis",
            )
        hypothesis = hypotheses[candidate.basis_hypothesis_id]
        expected_actions = (
            {DecisionAction.OUTPUT}
            if hypothesis.role is BlindHypothesisRole.PRIMARY
            else {DecisionAction.CONDITIONAL, DecisionAction.ASK}
        )
        if candidate.decision_action not in expected_actions:
            raise _error(
                "INVALID_PROJECTION",
                "future candidate action differs from its blind-state role",
            )

    career_by_id = {
        item.candidate_id: item for item in candidates if item.domain == "career"
    }
    wealth_by_id = {
        item.candidate_id: item for item in candidates if item.domain == "wealth"
    }
    bindings = projection_input.wealth_bindings
    edge_ids = tuple(item.edge_id for item in bindings)
    target_ids = tuple(item.target_wealth_candidate_id for item in bindings)
    if _duplicates(edge_ids) or _duplicates(target_ids):
        raise _error("DUPLICATE_ID", "duplicate blind wealth binding identity")
    if set(target_ids) != set(wealth_by_id):
        raise _error(
            "INVALID_PROJECTION",
            "every blind wealth prediction requires exactly one explicit edge",
        )
    for binding in bindings:
        source = career_by_id.get(binding.source_career_candidate_id)
        target = wealth_by_id.get(binding.target_wealth_candidate_id)
        if source is None or target is None:
            raise _error(
                "REFERENCE_MISMATCH",
                "blind wealth binding references an unknown candidate",
            )
        if source.basis_hypothesis_id != target.basis_hypothesis_id:
            raise _error(
                "INVALID_PROJECTION",
                "blind wealth edge must remain inside one state hypothesis",
            )

    primary_id = state.primary_hypothesis_id
    career_mainline = tuple(
        item
        for item in candidates
        if item.domain == "career" and item.basis_hypothesis_id == primary_id
    )
    wealth_mainline = tuple(
        item
        for item in candidates
        if item.domain == "wealth" and item.basis_hypothesis_id == primary_id
    )
    if not career_mainline:
        raise _error(
            "INVALID_PROJECTION",
            "BLIND_BASELINE requires at least one primary career prediction",
        )
    primary_conclusions = {item.conclusion for item in career_mainline}

    branches = []
    for hypothesis in state.hypotheses:
        if hypothesis.role is BlindHypothesisRole.PRIMARY:
            continue
        career = tuple(
            item
            for item in candidates
            if item.domain == "career"
            and item.basis_hypothesis_id == hypothesis.hypothesis_id
        )
        wealth = tuple(
            item
            for item in candidates
            if item.domain == "wealth"
            and item.basis_hypothesis_id == hypothesis.hypothesis_id
        )
        if not career or not any(
            item.conclusion not in primary_conclusions for item in career
        ):
            raise _error(
                "INVALID_PROJECTION",
                "conditional state must materially change a career conclusion",
            )
        branches.append(BlindConditionalProjection(hypothesis, career, wealth))

    unsupported = tuple(
        UnsupportedDomainProjection(
            domain,
            UnsupportedDomainStatus.NOT_IMPLEMENTED,
            DecisionAction.ABSTAIN,
        )
        for domain in ("family", "education", "marriage", "health")
    )
    return BlindFutureProjection(
        FUTURE_PROJECTION_SCHEMA_VERSION,
        state.case_id,
        state.as_of_date,
        primary_id,
        career_mainline,
        wealth_mainline,
        tuple(branches),
        bindings,
        unsupported,
    )


def run_blind_baseline(
    *,
    session_schema_version: str,
    case_id: str,
    as_of_date: _datetime.date,
    session_id: str,
    blind_input: BlindChartInput,
    draft: CareerBlindDraft,
    question_snapshot: BaselineQuestionSnapshot,
    current_state: BlindCurrentStateSnapshot,
    projection_input: BlindProjectionInput,
    runtime_snapshot: BaselineRuntimeSnapshot,
) -> BlindBaselineRunResult:
    if type(blind_input) is not BlindChartInput:
        raise _error("INVALID_TYPE", "blind_input must be BlindChartInput")
    if type(draft) is not CareerBlindDraft:
        raise _error("INVALID_TYPE", "draft must be CareerBlindDraft")
    if type(question_snapshot) is not BaselineQuestionSnapshot:
        raise _error(
            "INVALID_TYPE",
            "question_snapshot must be BaselineQuestionSnapshot",
        )
    if type(current_state) is not BlindCurrentStateSnapshot:
        raise _error(
            "INVALID_TYPE",
            "current_state must be BlindCurrentStateSnapshot",
        )
    if type(projection_input) is not BlindProjectionInput:
        raise _error(
            "INVALID_TYPE",
            "projection_input must be BlindProjectionInput",
        )
    if type(runtime_snapshot) is not BaselineRuntimeSnapshot:
        raise _error(
            "INVALID_TYPE",
            "runtime_snapshot must be BaselineRuntimeSnapshot",
        )
    if (
        _contains_probe_marker(draft)
        or _contains_probe_marker(current_state)
        or _contains_probe_marker(projection_input)
    ):
        raise _error(
            "PROBE_NOT_PREDICTION",
            "STRUCTURAL_PROBE_ONLY cannot be archived as BLIND_BASELINE",
        )

    identity = SessionIdentity(
        session_schema_version,
        case_id,
        as_of_date,
        session_id,
    )
    envelope = create_initial_envelope(identity, blind_input)
    drafted = transition_session(envelope, ConsultationState.BLIND_DRAFTED)
    frozen_envelope, freeze_package = freeze_career_draft(drafted, draft)
    freeze_package_sha256 = compute_freeze_package_sha256(freeze_package)

    if current_state.case_id != case_id or current_state.as_of_date != as_of_date:
        raise _error("IDENTITY_MISMATCH", "blind current-state identity differs")
    _validate_state_sources(current_state, freeze_package)
    projection = project_future_from_blind_state(
        state=current_state,
        projection_input=projection_input,
    )
    access = BlindInputAccessDeclaration(
        INPUT_ACCESS_SCHEMA_VERSION,
        (
            "blind_chart_input",
            "career_blind_draft",
            "question_snapshot",
            "blind_current_state_snapshot",
            "blind_projection_input",
            "rule_snapshot",
        ),
        False,
        False,
        False,
    )
    return BlindBaselineRunResult(
        ArtifactKind.BLIND_BASELINE,
        frozen_envelope,
        freeze_package,
        freeze_package_sha256,
        question_snapshot,
        runtime_snapshot,
        access,
        current_state,
        projection,
    )


def _project(value: object) -> _Any:
    if _dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _project(getattr(value, field.name))
            for field in _dataclasses.fields(value)
        }
    if isinstance(value, _Enum):
        return value.value
    if type(value) in {_datetime.date, _datetime.datetime}:
        return value.isoformat()
    if isinstance(value, tuple):
        return [_project(item) for item in value]
    if isinstance(value, list):
        return [_project(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _project(item) for key, item in value.items()}
    return value


def serialize_blind_baseline_payload(
    result: BlindBaselineRunResult,
) -> dict[str, object]:
    if type(result) is not BlindBaselineRunResult:
        raise _error("INVALID_TYPE", "result must be BlindBaselineRunResult")
    if result.artifact_kind is not ArtifactKind.BLIND_BASELINE:
        raise _error("INVALID_VALUE", "artifact kind must be BLIND_BASELINE")
    if result.final_envelope.state is not ConsultationState.FROZEN:
        raise _error("INVALID_VALUE", "blind baseline workflow envelope must remain FROZEN")
    if compute_freeze_package_sha256(result.freeze_package) != result.freeze_package_sha256:
        raise _error("HASH_MISMATCH", "freeze package digest differs")
    try:
        freeze_package = _json.loads(
            freeze_package_to_canonical_bytes(result.freeze_package).decode("utf-8")
        )
    except (UnicodeDecodeError, _json.JSONDecodeError) as exc:
        raise _error("INVALID_VALUE", "freeze package cannot be serialized") from exc
    return {
        "schema_version": BLIND_BASELINE_PAYLOAD_SCHEMA_VERSION,
        "artifact_kind": result.artifact_kind.value,
        "envelope": _project(result.final_envelope),
        "question_snapshot": _project(result.question_snapshot),
        "runtime_snapshot": _project(result.runtime_snapshot),
        "input_access": _project(result.input_access),
        "freeze_package_sha256": result.freeze_package_sha256,
        "freeze_package": freeze_package,
        "current_state": _project(result.current_state),
        "projection": _project(result.projection),
    }


def blind_baseline_payload_sha256(payload: dict[str, object]) -> str:
    if type(payload) is not dict:
        raise _error("INVALID_TYPE", "payload must be dict")
    try:
        encoded = _json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise _error("INVALID_VALUE", "payload must be canonical JSON") from exc
    return _hashlib.sha256(encoded).hexdigest()


__all__ = (
    "ArtifactKind",
    "ArtifactReference",
    "BLIND_BASELINE_PAYLOAD_SCHEMA_VERSION",
    "BaselineQuestionSnapshot",
    "BaselineRuntimeSnapshot",
    "BlindBaselineError",
    "BlindBaselineRunResult",
    "BlindConditionalProjection",
    "BlindCurrentStateSnapshot",
    "BlindFutureCandidate",
    "BlindFutureProjection",
    "BlindHypothesisRole",
    "BlindInputAccessDeclaration",
    "BlindProjectionInput",
    "BlindStateHypothesis",
    "BlindWealthBinding",
    "CURRENT_STATE_SCHEMA_VERSION",
    "FUTURE_PROJECTION_SCHEMA_VERSION",
    "INPUT_ACCESS_SCHEMA_VERSION",
    "QUESTION_SNAPSHOT_SCHEMA_VERSION",
    "RUNTIME_SNAPSHOT_SCHEMA_VERSION",
    "blind_baseline_payload_sha256",
    "project_future_from_blind_state",
    "run_blind_baseline",
    "serialize_blind_baseline_payload",
)
