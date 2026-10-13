from __future__ import annotations

import ast
import importlib
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import date
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

import pytest

from engine.asof.career_state_builder import CareerStateBuildResult
from engine.asof.event_candidate import (
    AnnualInteractionTrace,
    CompletionMode,
    ExtensionBoundary,
    LifeEventCandidate,
    RootLevel,
    VerificationStatus,
)
from engine.asof.natal_capacity import EvidenceRef, SourceCitation
from engine.asof.reality_track import PathState, RealityStateEntry, RealityTrack
from engine.asof.session_contract import (
    SESSION_SCHEMA_VERSION,
    ConsultationState,
    SessionEnvelope,
    SessionIdentity,
)
from engine.asof.state_ledger import (
    DecisionAction,
    EventImpactAssessment,
    EventLedgerEntry,
    HypothesisState,
    ImpactLevel,
    ImpactScope,
    Persistence,
    VerifiedState,
)
from engine.asof.wealth_propagation import (
    WealthPropagationEdge,
    propagate_career_event_to_wealth as _propagate_career_event_to_wealth,
)


MODULE_NAME = "engine.asof.future_projection"
TARGET = Path("tests/asof/test_future_projection.py")
CASE_ID = "C-2026-001-乾-庚申戊寅壬子辛丑"
AS_OF = date(2020, 1, 1)
ERROR_CODES = {
    "INVALID_TYPE",
    "INVALID_VALUE",
    "UNKNOWN_FIELD",
    "INVALID_STATE",
    "DUPLICATE_ID",
    "IDENTITY_MISMATCH",
    "LEDGER_MISMATCH",
    "STATE_MISMATCH",
    "HYPOTHESIS_MISMATCH",
    "AMBIGUOUS_PATH_STATE",
    "UNKNOWN_STATE_REFERENCE",
    "UNKNOWN_PATH_REFERENCE",
    "WEALTH_BINDING_MISMATCH",
}
EXPECTED_FIELDS = {
    "CareerFutureCandidate": (
        "case_id",
        "as_of_date",
        "candidate_id",
        "conclusion",
        "required_active_state_ids",
        "required_open_path_ids",
    ),
    "WealthEventBinding": ("event_id", "observed_conditions", "active_falsifiers", "edges"),
    "WealthEventDecision": ("event_id", "decision"),
    "UnsupportedDomainProjection": ("domain", "status", "decision_action"),
    "FutureProjectionFromState": (
        "envelope",
        "career_mainline",
        "conditional_branches",
        "wealth_decisions",
        "wealth_states",
        "unsupported_domains",
    ),
}
MATRIX = (1, 1, 6, 5, 13, 8, 7, 6, 7, 1, 4, 1)


class _CareerStateBuildResultSubclass(CareerStateBuildResult):
    pass


def _api() -> ModuleType:
    """执行期才加载 wished-for Unit-4 API，保证 RED 可完整收集。"""

    return importlib.import_module(MODULE_NAME)


def _unchecked_replace(value: Any, **changes: Any) -> Any:
    clone = object.__new__(type(value))
    for field in fields(value):
        object.__setattr__(clone, field.name, changes.get(field.name, getattr(value, field.name)))
    return clone


def _identity(**changes: Any) -> SessionIdentity:
    values = {
        "schema_version": SESSION_SCHEMA_VERSION,
        "case_id": CASE_ID,
        "as_of_date": AS_OF,
        "session_id": "S-20260727T120000Z-0123abcd",
    }
    values.update(changes)
    return SessionIdentity(**values)


def _envelope(state: ConsultationState = ConsultationState.STATE_BUILT, **changes: Any) -> SessionEnvelope:
    values = {"identity": _identity(), "blind_input_sha256": "1" * 64, "state": state}
    values.update(changes)
    return SessionEnvelope(**values)


def _evidence() -> EvidenceRef:
    return EvidenceRef("cases/C-2026-001/input.md", "四柱.年柱", "庚申")


def _candidate(
    identifier: str,
    status: VerificationStatus,
    *,
    event_type: str = "responsibility_level_change",
) -> LifeEventCandidate:
    evidence = _evidence()
    return LifeEventCandidate(
        candidate_id=identifier,
        domain="career",
        event_type=event_type,
        window_start=date(2019, 1, 1),
        window_end=date(2019, 12, 31),
        natal_evidence=(evidence,),
        daiyun_evidence=(evidence,),
        annual_trace=AnnualInteractionTrace(
            year=2019,
            liunian="己亥",
            dayun_ganzhi="庚辰",
            relations=(evidence,),
            activated_node_ids=("career-authority",),
            domains=("career",),
            supporting_evidence=(evidence,),
            counter_evidence=(),
            trigger_strength="high",
            crossed_candidate_gate=True,
        ),
        root_level=RootLevel.STRONG_ROOT,
        root_evidence=(evidence,),
        source_citations=(SourceCitation("sources/gao/example.md", 1, "原局有根，岁运引动"),),
        completion_mode=CompletionMode.ACTIVATE_EXISTING,
        supporting_evidence=(evidence,),
        counter_evidence=(),
        alternative_hypotheses=("scope changed without title",),
        frozen_version="asof-prototype-v1",
        verification_status=status,
        extension_boundary=ExtensionBoundary.CROSS_DAIYUN_ELIGIBLE,
        is_primary_event=True,
    )


def _entry(
    identifier: str,
    status: VerificationStatus,
    *,
    event_date: date = date(2019, 7, 1),
    event_type: str = "responsibility_level_change",
) -> EventLedgerEntry:
    return EventLedgerEntry(
        _candidate(identifier, status, event_type=event_type),
        EventImpactAssessment(
            event_id=identifier,
            event_date=event_date,
            event_type=event_type,
            root_level=RootLevel.STRONG_ROOT,
            completion_mode=CompletionMode.ACTIVATE_EXISTING,
            system_suggested_impact=ImpactLevel.MAJOR,
            system_suggested_persistence=Persistence.CROSS_DAIYUN,
            system_suggested_scope=ImpactScope.PRIMARY_DOMAIN,
            state_value="career responsibility expanded",
        ),
    )


def _hypothesis(identifier: str) -> HypothesisState:
    return HypothesisState(
        case_id=CASE_ID,
        as_of_date=AS_OF,
        candidate_id=identifier,
        condition=f"若 {identifier} 成立",
        difference_from_verified=f"{identifier} 改变已核验基点",
        changed_fundamentals=("career-baseline",),
        changed_future_conclusions=(f"future:{identifier}",),
        minimum_question=f"{identifier} 是否发生？",
        falsifier=f"{identifier} 未发生",
        decision_action=DecisionAction.CONDITIONAL,
    )


def _result(
    *,
    confirmed_id: str = "event-confirmed",
    confirmed_date: date = date(2019, 7, 1),
    confirmed_type: str = "responsibility_level_change",
    **changes: Any,
) -> CareerStateBuildResult:
    confirmed = _entry(
        confirmed_id,
        VerificationStatus.CONFIRMED,
        event_date=confirmed_date,
        event_type=confirmed_type,
    )
    hypotheses = tuple(
        _entry(f"event-hypothesis-{index}", status)
        for index, status in enumerate(
            (
                VerificationStatus.PARTIAL_HIT,
                VerificationStatus.UNKNOWN,
                VerificationStatus.WITHHELD,
            ),
            start=1,
        )
    )
    state = RealityStateEntry(
        state_id=f"state:{confirmed_id}",
        domain="career",
        value="career responsibility expanded",
        source_event_id=confirmed_id,
        effective_from=confirmed_date,
        effective_until=None,
        verified=True,
    )
    track = RealityTrack(
        case_id=CASE_ID,
        as_of_date=AS_OF,
        active_states=(state,),
        path_states=(PathState("management", "open", confirmed_id), PathState("legacy", "closed", confirmed_id)),
        verified_event_ids=(confirmed_id,),
    )
    verified = VerifiedState(
        case_id=CASE_ID,
        as_of_date=AS_OF,
        reality_track=track,
        current_center="mid-level professional",
        reasonable_range=("specialist", "team lead"),
        verified_event_ids=(confirmed_id,),
        active_state_ids=(f"state:{confirmed_id}",),
        decision_action=DecisionAction.OUTPUT,
    )
    values = {
        "envelope": _envelope(),
        "ledger_entries": (confirmed, *hypotheses),
        "verified_state": verified,
        "hypothesis_states": tuple(_hypothesis(f"event-hypothesis-{index}") for index in range(1, 4)),
    }
    values.update(changes)
    return CareerStateBuildResult(**values)


def _career_candidate(api: ModuleType, identifier: str = "future-mainline", **changes: Any) -> Any:
    values = {
        "case_id": CASE_ID,
        "as_of_date": AS_OF,
        "candidate_id": identifier,
        "conclusion": "事业沿已打开的管理路径继续发展",
        "required_active_state_ids": ("state:event-confirmed",),
        "required_open_path_ids": ("management",),
    }
    values.update(changes)
    return api.CareerFutureCandidate(**values)


def _edge(**changes: Any) -> WealthPropagationEdge:
    values = {
        "edge_id": "career-to-wealth",
        "source_event_type": "responsibility_level_change",
        "target_state": "income capacity expanded",
        "required_conditions": ("compensation-adjusted",),
        "delay_days": 30,
        "persistence": Persistence.CROSS_DAIYUN,
        "falsifiers": ("compensation-unchanged",),
        "verified": True,
    }
    values.update(changes)
    return WealthPropagationEdge(**values)


def _binding(api: ModuleType, **changes: Any) -> Any:
    values = {
        "event_id": "event-confirmed",
        "observed_conditions": ("compensation-adjusted",),
        "active_falsifiers": (),
        "edges": (_edge(),),
    }
    values.update(changes)
    return api.WealthEventBinding(**values)


def _project(api: ModuleType, *, result: Any | None = None, candidates: Any | None = None, bindings: Any | None = None) -> Any:
    return api.project_future_from_state(
        result=_result() if result is None else result,
        career_candidates=(_career_candidate(api),) if candidates is None else candidates,
        wealth_bindings=(_binding(api),) if bindings is None else bindings,
    )


def _assert_error(api: ModuleType, code: str, operation: Callable[[], Any]) -> None:
    with pytest.raises(api.FutureProjectionError) as caught:
        operation()
    assert caught.value.code == code
    assert caught.value.code in ERROR_CODES


def test_public_api_models_fields_and_immutability() -> None:
    api = _api()
    assert api.FutureProjectionError.CODES == frozenset(ERROR_CODES)
    for name, expected in EXPECTED_FIELDS.items():
        model = getattr(api, name)
        assert is_dataclass(model)
        assert model.__dataclass_params__.frozen is True
        assert tuple(field.name for field in fields(model)) == expected
        assert "__dict__" not in model.__dict__
    assert issubclass(api.UnsupportedDomainStatus, Enum)
    assert tuple(item.value for item in api.UnsupportedDomainStatus) == ("NOT_IMPLEMENTED",)
    candidate = _career_candidate(api)
    with pytest.raises(FrozenInstanceError):
        candidate.conclusion = "mutated"


def test_valid_projection_is_deterministic_and_physically_separated() -> None:
    api = _api()
    result = _result()
    first = _project(api, result=result)
    second = _project(api, result=result)
    assert first == second
    assert first.envelope.state is ConsultationState.PROJECTED
    assert result.envelope.state is ConsultationState.STATE_BUILT
    assert first.career_mainline == (_career_candidate(api),)
    assert first.conditional_branches == result.hypothesis_states[:2]
    assert tuple(item.event_id for item in first.wealth_decisions) == ("event-confirmed",)
    assert tuple(state.domain for state in first.wealth_states) == ("wealth",)


@pytest.mark.parametrize("case", ("result", "career_container", "binding_container", "candidate_item", "binding_item", "unknown_field"))
def test_exact_types_closed_slots_and_constructor_boundaries(case: str) -> None:
    api = _api()
    if case == "result":
        valid = _result()
        subclass = _CareerStateBuildResultSubclass(
            valid.envelope,
            valid.ledger_entries,
            valid.verified_state,
            valid.hypothesis_states,
        )
        operation = lambda: _project(api, result=subclass)
    elif case == "career_container":
        operation = lambda: _project(api, candidates=[])
    elif case == "binding_container":
        operation = lambda: _project(api, bindings=[])
    elif case == "candidate_item":
        class CandidateSubclass(api.CareerFutureCandidate):
            pass

        candidate = _career_candidate(api)
        subclass = CandidateSubclass(
            *(getattr(candidate, field.name) for field in fields(candidate))
        )
        operation = lambda: _project(api, candidates=(subclass,))
    elif case == "binding_item":
        class BindingSubclass(api.WealthEventBinding):
            pass

        binding = _binding(api)
        subclass = BindingSubclass(
            *(getattr(binding, field.name) for field in fields(binding))
        )
        operation = lambda: _project(api, bindings=(subclass,))
    else:
        operation = lambda: api.CareerFutureCandidate(
            case_id=CASE_ID,
            as_of_date=AS_OF,
            candidate_id="future-mainline",
            conclusion="x",
            required_active_state_ids=(),
            required_open_path_ids=(),
            priority=1,
        )
    _assert_error(api, "INVALID_TYPE" if case != "unknown_field" else "UNKNOWN_FIELD", operation)


@pytest.mark.parametrize(
    ("case", "code"),
    (
        ("wrong_state", "INVALID_STATE"),
        ("verified_case", "IDENTITY_MISMATCH"),
        ("track_case", "IDENTITY_MISMATCH"),
        ("verified_date", "IDENTITY_MISMATCH"),
        ("track_date", "IDENTITY_MISMATCH"),
    ),
)
def test_state_identity_and_validation_precedence(case: str, code: str) -> None:
    api = _api()
    result = _result()
    verified = result.verified_state
    if case == "wrong_state":
        result = replace(result, envelope=_envelope(ConsultationState.ADJUDICATED))
    elif case == "verified_case":
        result = replace(result, verified_state=replace(verified, case_id="other-case"))
    elif case == "track_case":
        result = replace(result, verified_state=replace(verified, reality_track=replace(verified.reality_track, case_id="other-case")))
    elif case == "verified_date":
        result = replace(result, verified_state=replace(verified, as_of_date=date(2020, 1, 2)))
    else:
        result = replace(result, verified_state=replace(verified, reality_track=replace(verified.reality_track, as_of_date=date(2020, 1, 2))))
    _assert_error(api, code, lambda: _project(api, result=result, candidates=(object(),), bindings=(object(),)))


@pytest.mark.parametrize(
    ("case", "code"),
    (
        ("duplicate_ledger", "DUPLICATE_ID"),
        ("entry_id_mismatch", "LEDGER_MISMATCH"),
        ("verified_ids", "LEDGER_MISMATCH"),
        ("track_verified_ids", "LEDGER_MISMATCH"),
        ("active_ids", "STATE_MISMATCH"),
        ("duplicate_state", "DUPLICATE_ID"),
        ("unknown_state_source", "STATE_MISMATCH"),
        ("unconfirmed_state_source", "LEDGER_MISMATCH"),
        ("ambiguous_path", "AMBIGUOUS_PATH_STATE"),
        ("unknown_path_source", "STATE_MISMATCH"),
        ("unconfirmed_path_source", "LEDGER_MISMATCH"),
        ("duplicate_path", "DUPLICATE_ID"),
        ("invalid_path_status", "INVALID_VALUE"),
    ),
)
def test_ledger_verified_state_and_active_state_consistency(case: str, code: str) -> None:
    api = _api()
    result = _result()
    verified = result.verified_state
    track = verified.reality_track
    if case == "duplicate_ledger":
        duplicate = _unchecked_replace(
            result.ledger_entries[0],
            assessment=replace(result.ledger_entries[0].assessment, state_value="different duplicate"),
        )
        result = replace(result, ledger_entries=(result.ledger_entries[0], duplicate, *result.ledger_entries[1:]))
    elif case == "entry_id_mismatch":
        bad = _unchecked_replace(result.ledger_entries[0], assessment=replace(result.ledger_entries[0].assessment, event_id="other"))
        result = replace(result, ledger_entries=(bad, *result.ledger_entries[1:]))
    elif case == "verified_ids":
        result = replace(result, verified_state=replace(verified, verified_event_ids=()))
    elif case == "track_verified_ids":
        result = replace(
            result,
            verified_state=replace(
                verified,
                reality_track=_unchecked_replace(track, verified_event_ids=()),
            ),
        )
    elif case == "active_ids":
        result = replace(result, verified_state=replace(verified, active_state_ids=()))
    elif case == "duplicate_state":
        duplicate = replace(track.active_states[0], value="different duplicate")
        result = replace(result, verified_state=replace(verified, reality_track=_unchecked_replace(track, active_states=(track.active_states[0], duplicate))))
    elif case == "unknown_state_source":
        state = _unchecked_replace(track.active_states[0], source_event_id="other")
        result = replace(result, verified_state=replace(verified, reality_track=_unchecked_replace(track, active_states=(state,))))
    elif case == "unconfirmed_state_source":
        state = _unchecked_replace(
            track.active_states[0],
            state_id="state:event-hypothesis-1",
            source_event_id="event-hypothesis-1",
        )
        forged_track = _unchecked_replace(
            track,
            active_states=(state,),
            verified_event_ids=(*track.verified_event_ids, "event-hypothesis-1"),
        )
        forged_verified = _unchecked_replace(
            verified,
            reality_track=forged_track,
            verified_event_ids=forged_track.verified_event_ids,
            active_state_ids=(state.state_id,),
        )
        result = replace(result, verified_state=forged_verified)
    elif case == "ambiguous_path":
        duplicate = PathState("management", "closed", "event-confirmed")
        result = replace(result, verified_state=replace(verified, reality_track=replace(track, path_states=(*track.path_states, duplicate))))
    elif case == "unknown_path_source":
        path = _unchecked_replace(track.path_states[0], source_event_id="other")
        result = replace(result, verified_state=replace(verified, reality_track=_unchecked_replace(track, path_states=(path,))))
    elif case == "unconfirmed_path_source":
        path = _unchecked_replace(track.path_states[0], source_event_id="event-hypothesis-1")
        forged_track = _unchecked_replace(
            track,
            path_states=(path,),
            verified_event_ids=(*track.verified_event_ids, "event-hypothesis-1"),
        )
        result = replace(result, verified_state=_unchecked_replace(verified, reality_track=forged_track))
    elif case == "duplicate_path":
        duplicate = replace(track.path_states[0], status="reduced")
        result = replace(result, verified_state=replace(verified, reality_track=_unchecked_replace(track, path_states=(track.path_states[0], duplicate))))
    else:
        path = _unchecked_replace(track.path_states[0], status="invented")
        result = replace(result, verified_state=replace(verified, reality_track=_unchecked_replace(track, path_states=(path,))))
    _assert_error(
        api,
        code,
        lambda: _project(
            api,
            result=result,
            candidates=(object(),),
            bindings=(object(),),
        ),
    )


@pytest.mark.parametrize(
    "case",
    (
        "cap",
        "partial_hit",
        "withheld",
        "duplicate",
        "confirmed_binding",
        "identity",
        "unknown_candidate",
        "wrong_date",
    ),
)
def test_hypothesis_binding_source_order_and_two_branch_cap(case: str) -> None:
    api = _api()
    result = _result()
    if case == "cap":
        confirmed, first, second, third = result.ledger_entries
        reordered_hypotheses = (
            result.hypothesis_states[2],
            result.hypothesis_states[0],
            result.hypothesis_states[1],
        )
        result = replace(
            result,
            ledger_entries=(confirmed, third, first, second),
            hypothesis_states=reordered_hypotheses,
        )
        projected = _project(api, result=result)
        assert projected.conditional_branches == reordered_hypotheses[:2]
        assert tuple(branch.candidate_id for branch in projected.conditional_branches) == (
            "event-hypothesis-3",
            "event-hypothesis-1",
        )
        return
    if case in {"partial_hit", "withheld"}:
        status = VerificationStatus.PARTIAL_HIT if case == "partial_hit" else VerificationStatus.WITHHELD
        identifier = f"event-{case}"
        entry = _entry(identifier, status)
        result = replace(
            result,
            ledger_entries=(result.ledger_entries[0], entry),
            hypothesis_states=(_hypothesis(identifier),),
        )
        assert _project(api, result=result).conditional_branches == result.hypothesis_states
        return
    if case == "duplicate":
        duplicate = replace(result.hypothesis_states[0], difference_from_verified="different duplicate")
        result = replace(result, hypothesis_states=(result.hypothesis_states[0], duplicate))
    elif case == "confirmed_binding":
        result = replace(result, hypothesis_states=(_hypothesis("event-confirmed"),))
    elif case == "identity":
        result = replace(result, hypothesis_states=(replace(result.hypothesis_states[0], case_id="other-case"),))
    elif case == "unknown_candidate":
        result = replace(result, hypothesis_states=(_hypothesis("event-not-in-ledger"),))
    else:
        result = replace(result, hypothesis_states=(replace(result.hypothesis_states[0], as_of_date=date(2020, 1, 2)),))
    _assert_error(
        api,
        "DUPLICATE_ID" if case == "duplicate" else "HYPOTHESIS_MISMATCH",
        lambda: _project(
            api,
            result=result,
            candidates=(object(),),
            bindings=(object(),),
        ),
    )


@pytest.mark.parametrize(
    ("case", "code"),
    (
        ("reduced_path", None),
        ("source_order", None),
        ("closed_path", None),
        ("unknown_state", "UNKNOWN_STATE_REFERENCE"),
        ("unknown_path", "UNKNOWN_PATH_REFERENCE"),
        ("duplicate_candidate", "DUPLICATE_ID"),
        ("identity", "IDENTITY_MISMATCH"),
    ),
)
def test_career_candidate_state_and_path_gates(case: str, code: str | None) -> None:
    api = _api()
    candidate = _career_candidate(api)
    if case == "reduced_path":
        result = _result()
        track = result.verified_state.reality_track
        reduced = replace(track.path_states[0], status="reduced")
        result = replace(
            result,
            verified_state=replace(
                result.verified_state,
                reality_track=replace(track, path_states=(reduced, *track.path_states[1:])),
            ),
        )
        assert _project(api, result=result, candidates=(candidate,)).career_mainline == ()
        return
    if case == "source_order":
        second = _career_candidate(api, "future-second")
        assert _project(api, candidates=(second, candidate)).career_mainline == (second, candidate)
        return
    if case == "closed_path":
        closed = _career_candidate(api, required_open_path_ids=("legacy",))
        assert _project(api, candidates=(closed,)).career_mainline == ()
        return
    if case == "unknown_state":
        candidates = (_career_candidate(api, required_active_state_ids=("state:missing",)),)
    elif case == "unknown_path":
        candidates = (_career_candidate(api, required_open_path_ids=("missing",)),)
    elif case == "duplicate_candidate":
        candidates = (candidate, _career_candidate(api, conclusion="different duplicate"))
    else:
        candidates = (_career_candidate(api, case_id="other-case"),)
    assert code is not None
    _assert_error(
        api,
        code,
        lambda: _project(api, candidates=candidates, bindings=(object(),)),
    )


@pytest.mark.parametrize(
    ("case", "code"),
    (
        ("multiple", None),
        ("missing", "WEALTH_BINDING_MISMATCH"),
        ("extra", "WEALTH_BINDING_MISMATCH"),
        ("duplicate", "DUPLICATE_ID"),
        ("wrong_id", "WEALTH_BINDING_MISMATCH"),
        ("unconfirmed_only", "WEALTH_BINDING_MISMATCH"),
    ),
)
def test_wealth_binding_requires_exact_confirmed_event_coverage(
    case: str,
    code: str | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _api()
    binding = _binding(api)
    if case == "multiple":
        result = _result()
        second_id = "event-confirmed-2"
        second_date = date(2019, 8, 1)
        second = _entry(
            second_id,
            VerificationStatus.CONFIRMED,
            event_date=second_date,
            event_type="career_path_change",
        )
        second_state = RealityStateEntry(
            state_id=f"state:{second_id}",
            domain="career",
            value="career responsibility expanded",
            source_event_id=second_id,
            effective_from=second_date,
            effective_until=None,
            verified=True,
        )
        track = result.verified_state.reality_track
        verified_ids = (*track.verified_event_ids, second_id)
        forged_track = replace(
            track,
            active_states=(*track.active_states, second_state),
            verified_event_ids=verified_ids,
        )
        forged_verified = replace(
            result.verified_state,
            reality_track=forged_track,
            verified_event_ids=verified_ids,
            active_state_ids=(*result.verified_state.active_state_ids, second_state.state_id),
        )
        result = replace(
            result,
            ledger_entries=(*result.ledger_entries, second),
            verified_state=forged_verified,
        )
        second_edge = _edge(
            edge_id="career-path-to-wealth",
            source_event_type="career_path_change",
            required_conditions=("second-condition",),
        )
        second_binding = _binding(
            api,
            event_id=second_id,
            observed_conditions=("second-condition",),
            active_falsifiers=(),
            edges=(second_edge,),
        )
        calls: list[dict[str, Any]] = []

        def spy(**values: Any) -> Any:
            calls.append(values)
            return _propagate_career_event_to_wealth(**values)

        monkeypatch.setattr(api, "propagate_career_event_to_wealth", spy)
        projected = _project(
            api,
            result=result,
            bindings=(binding, second_binding),
        )
        assert calls == [
            {
                "event_id": "event-confirmed",
                "event_type": "responsibility_level_change",
                "event_date": date(2019, 7, 1),
                "verified_event": True,
                "observed_conditions": binding.observed_conditions,
                "active_falsifiers": binding.active_falsifiers,
                "edges": binding.edges,
            },
            {
                "event_id": second_id,
                "event_type": "career_path_change",
                "event_date": second_date,
                "verified_event": True,
                "observed_conditions": second_binding.observed_conditions,
                "active_falsifiers": second_binding.active_falsifiers,
                "edges": second_binding.edges,
            },
        ]
        assert len(calls) == 2
        assert tuple(item.event_id for item in projected.wealth_decisions) == (
            "event-confirmed",
            second_id,
        )
        assert all(item.decision.changed for item in projected.wealth_decisions)
        assert tuple(state.source_event_id for state in projected.wealth_states) == (
            "event-confirmed",
            second_id,
        )
        return
    if case == "missing":
        bindings = ()
    elif case == "extra":
        bindings = (binding, _binding(api, event_id="event-extra"))
    elif case == "duplicate":
        bindings = (binding, _binding(api, observed_conditions=("different-duplicate",)))
    elif case == "wrong_id":
        bindings = (_binding(api, event_id="event-other"),)
    else:
        bindings = (_binding(api, event_id="event-hypothesis-1"),)
    assert code is not None
    _assert_error(api, code, lambda: _project(api, bindings=bindings))


@pytest.mark.parametrize(
    ("case", "reason", "changed"),
    (
        ("success", "WEALTH_STATE_PROPAGATED", True),
        ("alternate_ledger_event", "WEALTH_STATE_PROPAGATED", True),
        ("no_edge", "NO_EXPLICIT_EDGE", False),
        ("ambiguous", "AMBIGUOUS_EXPLICIT_EDGES", False),
        ("conditions", "PROPAGATION_CONDITIONS_NOT_MET", False),
        ("falsifier", "PROPAGATION_FALSIFIED", False),
        ("edge_unverified", "EDGE_UNVERIFIED", False),
    ),
)
def test_wealth_decisions_preserve_all_low_level_outcomes(case: str, reason: str, changed: bool) -> None:
    api = _api()
    result = _result()
    expected_id = "event-confirmed"
    expected_date = date(2019, 7, 31)
    expected_value = "income capacity expanded"
    if case == "alternate_ledger_event":
        expected_id = "event-alternate"
        expected_date = date(2018, 7, 17)
        expected_value = "wealth structure changed"
        result = _result(
            confirmed_id=expected_id,
            confirmed_date=date(2018, 6, 17),
            confirmed_type="career_path_change",
        )
        binding = _binding(
            api,
            event_id=expected_id,
            edges=(
                _edge(
                    source_event_type="career_path_change",
                    target_state=expected_value,
                ),
            ),
        )
    elif case == "no_edge":
        binding = _binding(api, edges=())
    elif case == "ambiguous":
        binding = _binding(api, edges=(_edge(), _edge(edge_id="second-edge")))
    elif case == "conditions":
        binding = _binding(api, observed_conditions=())
    elif case == "falsifier":
        binding = _binding(api, active_falsifiers=("compensation-unchanged",))
    elif case == "edge_unverified":
        binding = _binding(api, edges=(_edge(verified=False),))
    else:
        binding = _binding(api)
    candidates = (
        _career_candidate(
            api,
            required_active_state_ids=(f"state:{expected_id}",),
        ),
    )
    projected = _project(
        api,
        result=result,
        candidates=candidates,
        bindings=(binding,),
    )
    assert len(projected.wealth_decisions) == 1
    audit = projected.wealth_decisions[0]
    assert audit.event_id == expected_id
    assert audit.decision.reason_code == reason
    assert audit.decision.changed is changed
    assert len(projected.wealth_states) == (1 if changed else 0)
    if changed:
        state = projected.wealth_states[0]
        assert state.state_id == f"wealth:{audit.decision.edge_id}:{expected_id}"
        assert state.domain == "wealth"
        assert state.value == expected_value
        assert state.source_event_id == expected_id
        assert state.effective_from == expected_date
        assert state.verified is True


def test_unsupported_domains_are_fixed_not_implemented_abstentions() -> None:
    api = _api()
    projected = _project(api)
    assert tuple(item.domain for item in projected.unsupported_domains) == ("family", "education", "marriage", "health")
    assert all(item.status is api.UnsupportedDomainStatus.NOT_IMPLEMENTED for item in projected.unsupported_domains)
    assert all(item.decision_action is DecisionAction.ABSTAIN for item in projected.unsupported_domains)


@pytest.mark.parametrize("case", ("state", "identity", "ledger", "wealth"))
def test_failures_are_immutable_and_never_advance_session(case: str) -> None:
    api = _api()
    result = _result()
    before = deepcopy(result)
    if case == "state":
        operation = lambda: _project(api, result=replace(result, envelope=_envelope(ConsultationState.ADJUDICATED)))
    elif case == "identity":
        operation = lambda: _project(api, result=replace(result, verified_state=replace(result.verified_state, case_id="other-case")))
    elif case == "ledger":
        operation = lambda: _project(api, result=replace(result, verified_state=replace(result.verified_state, verified_event_ids=())))
    else:
        operation = lambda: _project(api, result=result, bindings=())
    with pytest.raises(api.FutureProjectionError):
        operation()
    assert result == before
    assert result.envelope.state is ConsultationState.STATE_BUILT


def test_unit4_import_boundary_paths_error_codes_and_test_matrix() -> None:
    tree = ast.parse(TARGET.read_text(encoding="utf-8"))
    top_level_tests = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    ]
    actual_matrix = []
    for test in top_level_tests:
        signature_names = {
            argument.arg
            for argument in (
                *test.args.posonlyargs,
                *test.args.args,
                *test.args.kwonlyargs,
            )
        }
        parameter_counts = []
        for decorator in test.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "parametrize"
                and len(decorator.args) >= 2
            ):
                names = ast.literal_eval(decorator.args[0])
                parameter_names = (
                    tuple(item.strip() for item in names.split(","))
                    if isinstance(names, str)
                    else tuple(names)
                )
                assert parameter_names
                assert all(isinstance(item, str) and item for item in parameter_names)
                assert len(set(parameter_names)) == len(parameter_names)
                assert set(parameter_names) <= signature_names
                rows = ast.literal_eval(decorator.args[1])
                if len(parameter_names) > 1:
                    assert all(
                        isinstance(row, (tuple, list))
                        and len(row) == len(parameter_names)
                        for row in rows
                    )
                parameter_counts.append(len(rows))
        assert len(parameter_counts) <= 1
        actual_matrix.append(parameter_counts[0] if parameter_counts else 1)
    assert len(top_level_tests) == 12
    assert tuple(actual_matrix) == MATRIX
    assert sum(actual_matrix) == 60
    assert MATRIX == (1, 1, 6, 5, 13, 8, 7, 6, 7, 1, 4, 1)

    top_level_imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            top_level_imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            top_level_imports.append(node.module)
    assert MODULE_NAME not in top_level_imports

    unit4_paths = {
        path.as_posix()
        for root in (Path("engine/asof"), Path("tests/asof"))
        for path in root.glob("*future_projection.py")
    }
    assert unit4_paths <= {"engine/asof/future_projection.py", "tests/asof/test_future_projection.py"}

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
    production = Path("engine/asof/future_projection.py")
    if production.exists():
        production_tree = ast.parse(production.read_text(encoding="utf-8"))
        imported = []
        for node in ast.walk(production_tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        assert not any(name.startswith(forbidden_prefixes) for name in imported)
