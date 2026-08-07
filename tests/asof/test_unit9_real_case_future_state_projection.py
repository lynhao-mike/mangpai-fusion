from __future__ import annotations

import ast
from copy import deepcopy
from datetime import date
from pathlib import Path

import pytest

from engine.asof.event_candidate import VerificationStatus
from engine.asof.future_projection import (
    CareerFutureCandidate,
    FutureProjectionError,
    WealthEventBinding,
    project_future_from_state,
)
from engine.asof.session_contract import ConsultationState, SESSION_SCHEMA_VERSION
from engine.asof.session_runner import run_career_session
from tests.asof import test_unit8_real_case_blind_verification as unit8


AS_OF_DATE = date(2025, 12, 31)
SESSION_ID = "S-20251231T000000Z-00000009"
REAL_ACTIVE_STATE_IDS = (
    "state:career-2014-2015-teacher-entry",
    "state:career-2024-2025-school-principal",
)
REAL_OPEN_PATH_ID = "education-management-realized"
POSITIVE_CANDIDATE_ID = "career-future-education-management-continuity"
NEGATIVE_CANDIDATE_ID = "career-future-unverified-2026-2027"
UNKNOWN_PATH_ID = "path:unverified-2026-2027"
CONFIRMED_IDS = (unit8.TEACHER_ID, unit8.PRINCIPAL_ID)


def _state_built_result():
    draft = unit8._build_blind_draft(AS_OF_DATE)
    package = unit8._expected_package(AS_OF_DATE, SESSION_ID, draft)
    verifications, suggestions, adjudications, fundamental = (
        unit8._build_verification_from_feedback(package, AS_OF_DATE)
    )
    result = run_career_session(
        session_schema_version=SESSION_SCHEMA_VERSION,
        case_id=unit8.CASE_ID,
        as_of_date=AS_OF_DATE,
        session_id=SESSION_ID,
        blind_input=unit8._blind_input(),
        draft=draft,
        verifications=verifications,
        suggestions=suggestions,
        impact_adjudications=adjudications,
        fundamental_adjudication=fundamental,
        daiyun_end=AS_OF_DATE,
        career_candidates=None,
        wealth_bindings=None,
    )
    assert result.final_envelope.state is ConsultationState.STATE_BUILT
    assert result.state_result.verified_state.active_state_ids == REAL_ACTIVE_STATE_IDS
    assert tuple(
        (item.path_id, item.status, item.source_event_id)
        for item in result.state_result.verified_state.reality_track.path_states
    ) == ((REAL_OPEN_PATH_ID, "open", unit8.PRINCIPAL_ID),)
    assert tuple(
        item.candidate.candidate_id
        for item in result.state_result.ledger_entries
        if item.candidate.verification_status is VerificationStatus.CONFIRMED
    ) == CONFIRMED_IDS
    return result, draft, verifications, suggestions, adjudications, fundamental


def _career_candidates(
    path_id: str = REAL_OPEN_PATH_ID,
) -> tuple[CareerFutureCandidate, ...]:
    return (
        CareerFutureCandidate(
            case_id=unit8.CASE_ID,
            as_of_date=AS_OF_DATE,
            candidate_id=POSITIVE_CANDIDATE_ID,
            conclusion="已核验教育管理现实状态与开放路径支持后续事业主线延续",
            required_active_state_ids=(REAL_ACTIVE_STATE_IDS[1],),
            required_open_path_ids=(path_id,),
        ),
    )


def _wealth_bindings() -> tuple[WealthEventBinding, ...]:
    return tuple(
        WealthEventBinding(
            event_id=event_id,
            observed_conditions=(),
            active_falsifiers=(),
            edges=(),
        )
        for event_id in CONFIRMED_IDS
    )


def test_unit9_real_candidate_projects_and_wealth_abstains_without_edges() -> None:
    candidates = _career_candidates()
    bindings = _wealth_bindings()
    result, draft, verifications, suggestions, adjudications, fundamental = (
        _state_built_result()
    )
    projected = run_career_session(
        session_schema_version=SESSION_SCHEMA_VERSION,
        case_id=unit8.CASE_ID,
        as_of_date=AS_OF_DATE,
        session_id=SESSION_ID,
        blind_input=unit8._blind_input(),
        draft=draft,
        verifications=verifications,
        suggestions=suggestions,
        impact_adjudications=adjudications,
        fundamental_adjudication=fundamental,
        daiyun_end=AS_OF_DATE,
        career_candidates=candidates,
        wealth_bindings=bindings,
    )

    assert projected.final_envelope.state is ConsultationState.PROJECTED
    assert projected.projection is not None
    assert projected.projection.career_mainline == candidates
    assert projected.projection.career_mainline
    assert NEGATIVE_CANDIDATE_ID not in tuple(
        item.candidate_id for item in projected.projection.career_mainline
    )
    assert tuple(item.event_id for item in projected.projection.wealth_decisions) == CONFIRMED_IDS
    assert all(
        item.decision.reason_code == "NO_EXPLICIT_EDGE"
        and item.decision.changed is False
        and item.decision.state is None
        and item.decision.edge_id is None
        for item in projected.projection.wealth_decisions
    )
    assert projected.projection.wealth_states == ()


def test_unit9_unknown_path_counterexample_is_rejected_without_mutation() -> None:
    result = _state_built_result()[0].state_result
    before = deepcopy(result)
    counterexample = CareerFutureCandidate(
        case_id=unit8.CASE_ID,
        as_of_date=AS_OF_DATE,
        candidate_id=NEGATIVE_CANDIDATE_ID,
        conclusion="仅用于验证未知路径引用会被拒绝",
        required_active_state_ids=(REAL_ACTIVE_STATE_IDS[1],),
        required_open_path_ids=(UNKNOWN_PATH_ID,),
    )

    with pytest.raises(FutureProjectionError) as caught:
        project_future_from_state(
            result=result,
            career_candidates=(counterexample,),
            wealth_bindings=_wealth_bindings(),
        )

    assert caught.value.code == "UNKNOWN_PATH_REFERENCE"
    assert result == before
    assert result.envelope.state is ConsultationState.STATE_BUILT


def test_unit9_unverified_2026_2027_items_do_not_pollute_success_inputs() -> None:
    candidates = _career_candidates(REAL_OPEN_PATH_ID)
    bindings = _wealth_bindings()
    semantic_payload = repr(
        (
            tuple(
                (
                    candidate.conclusion,
                    candidate.required_active_state_ids,
                    candidate.required_open_path_ids,
                )
                for candidate in candidates
            ),
            tuple(
                (
                    binding.event_id,
                    binding.observed_conditions,
                    binding.active_falsifiers,
                    binding.edges,
                )
                for binding in bindings
            ),
        )
    )
    forbidden = (
        "2026",
        "2027",
        "待追踪",
        "事业身份、关系名分、职位规则强化",
        "现实责任、家庭资产、长期规划压力增加",
        UNKNOWN_PATH_ID,
    )

    assert not any(token in semantic_payload for token in forbidden)
    assert {
        identifier
        for candidate in candidates
        for identifier in candidate.required_active_state_ids
    } <= set(REAL_ACTIVE_STATE_IDS)
    assert {
        identifier
        for candidate in candidates
        for identifier in candidate.required_open_path_ids
    } == {REAL_OPEN_PATH_ID}
    assert tuple(binding.event_id for binding in bindings) == CONFIRMED_IDS
    assert all(binding.edges == () for binding in bindings)


def test_unit9_fresh_ast_import_boundary() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    imported = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    forbidden_prefixes = (
        "engine.pipeline",
        "engine.v5.runner",
        "engine.v5.preprod",
        "tools.render_report",
        "tools.feedback",
        "engine.asof.natal_capacity",
        "engine.asof.structural_track",
        "engine.asof.daiyun_context",
    )

    assert not any(name.startswith(forbidden_prefixes) for name in imported)
