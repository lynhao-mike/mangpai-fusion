"""编排一次完整的 as-of 事业求测会话。"""

from __future__ import annotations

import dataclasses as _dataclasses
import datetime as _datetime

from engine.asof.career_state_builder import (
    CareerAdjudicationBundle,
    CareerFundamentalAdjudication,
    CareerImpactAdjudication,
    CareerImpactSuggestion,
    CareerStateBuildResult,
    adjudicate_career_verifications,
    build_career_states,
)
from engine.asof.consultation_freeze import (
    CareerBlindDraft,
    CareerFreezePackage,
    VerificationInput,
    compute_freeze_package_sha256,
    freeze_career_draft,
    open_verification,
    record_career_verification,
)
from engine.asof.future_projection import (
    CareerFutureCandidate,
    FutureProjectionFromState,
    WealthEventBinding,
    project_future_from_state,
)
from engine.asof.session_contract import (
    BlindChartInput,
    ConsultationState,
    SessionEnvelope,
    SessionIdentity,
    create_initial_envelope,
    transition_session,
)

__all__ = ("SessionRunResult", "run_career_session")


@_dataclasses.dataclass(frozen=True, slots=True)
class SessionRunResult:
    final_envelope: SessionEnvelope
    freeze_package: CareerFreezePackage
    adjudication_bundle: CareerAdjudicationBundle
    state_result: CareerStateBuildResult
    projection: FutureProjectionFromState | None


def run_career_session(
    *,
    session_schema_version: str,
    case_id: str,
    as_of_date: _datetime.date,
    session_id: str,
    blind_input: BlindChartInput,
    draft: CareerBlindDraft,
    verifications: tuple[VerificationInput, ...],
    suggestions: tuple[CareerImpactSuggestion, ...],
    impact_adjudications: tuple[CareerImpactAdjudication, ...],
    fundamental_adjudication: CareerFundamentalAdjudication,
    daiyun_end: _datetime.date,
    career_candidates: tuple[CareerFutureCandidate, ...] | None = None,
    wealth_bindings: tuple[WealthEventBinding, ...] | None = None,
) -> SessionRunResult:
    """依次委托冻结 API，返回本次会话的最终状态与中间产物。"""

    identity = SessionIdentity(session_schema_version, case_id, as_of_date, session_id)
    envelope = create_initial_envelope(identity, blind_input)
    envelope = transition_session(envelope, ConsultationState.BLIND_DRAFTED)
    envelope, freeze_package = freeze_career_draft(envelope, draft)
    freeze_package_sha256 = compute_freeze_package_sha256(freeze_package)
    envelope = open_verification(envelope, freeze_package, freeze_package_sha256)
    records = tuple(
        record_career_verification(envelope, freeze_package, verification)
        for verification in verifications
    )
    adjudication_bundle = adjudicate_career_verifications(
        envelope,
        freeze_package,
        records,
        suggestions,
        impact_adjudications,
        fundamental_adjudication,
    )
    state_result = build_career_states(adjudication_bundle, daiyun_end)

    projection = None
    final_envelope = state_result.envelope
    if career_candidates is not None or wealth_bindings is not None:
        projection = project_future_from_state(
            result=state_result,
            career_candidates=() if career_candidates is None else career_candidates,
            wealth_bindings=() if wealth_bindings is None else wealth_bindings,
        )
        final_envelope = projection.envelope

    return SessionRunResult(
        final_envelope,
        freeze_package,
        adjudication_bundle,
        state_result,
        projection,
    )
