"""从已核验事业现实状态推演后运，并经显式边传播财富状态。"""
from __future__ import annotations

import dataclasses as _dataclasses
import datetime as _datetime
from enum import Enum
from typing import Callable, TypeVar

from engine.asof.career_state_builder import CareerStateBuildResult
from engine.asof.event_candidate import VerificationStatus
from engine.asof.reality_track import RealityStateEntry
from engine.asof.session_contract import ConsultationState, transition_session
from engine.asof.state_ledger import DecisionAction, HypothesisState
from engine.asof.wealth_propagation import (
    WealthPropagationDecision,
    WealthPropagationEdge,
    propagate_career_event_to_wealth,
)


class FutureProjectionError(ValueError):
    CODES = frozenset(
        {
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
    )

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _error(code: str, message: str) -> FutureProjectionError:
    return FutureProjectionError(code, message)


def _text(value: object, field: str) -> str:
    if type(value) is not str:
        raise _error("INVALID_TYPE", f"{field} must be str")
    if not value.strip():
        raise _error("INVALID_VALUE", f"{field} must not be empty")
    return value


def _date(value: object, field: str) -> _datetime.date:
    if type(value) is not _datetime.date:
        raise _error("INVALID_TYPE", f"{field} must be date")
    return value


def _strings(value: object, field: str) -> tuple[str, ...]:
    if type(value) is not tuple or any(type(item) is not str or not item.strip() for item in value):
        raise _error("INVALID_TYPE", f"{field} must be tuple[str, ...]")
    return value


_T = TypeVar("_T")


def _closed_model(model: type[_T], values: dict[str, object]) -> _T:
    allowed = tuple(field.name for field in _dataclasses.fields(model))
    unknown = set(values) - set(allowed)
    if unknown:
        raise _error("UNKNOWN_FIELD", f"unknown fields: {sorted(unknown)}")
    missing = set(allowed) - set(values)
    if missing:
        raise _error("INVALID_VALUE", f"missing fields: {sorted(missing)}")
    instance = object.__new__(model)
    for name in allowed:
        object.__setattr__(instance, name, values[name])
    return instance


@_dataclasses.dataclass(frozen=True, slots=True, init=False)
class CareerFutureCandidate:
    case_id: str
    as_of_date: _datetime.date
    candidate_id: str
    conclusion: str
    required_active_state_ids: tuple[str, ...]
    required_open_path_ids: tuple[str, ...]

    def __init__(self, *args: object, **values: object) -> None:
        names = tuple(field.name for field in _dataclasses.fields(type(self)))
        if len(args) > len(names) or any(name in values for name in names[: len(args)]):
            raise _error("INVALID_TYPE", "invalid constructor arguments")
        instance = _closed_model(type(self), {**dict(zip(names, args)), **values})
        _text(instance.case_id, "case_id")
        _date(instance.as_of_date, "as_of_date")
        _text(instance.candidate_id, "candidate_id")
        _text(instance.conclusion, "conclusion")
        _strings(instance.required_active_state_ids, "required_active_state_ids")
        _strings(instance.required_open_path_ids, "required_open_path_ids")
        for field in _dataclasses.fields(self):
            object.__setattr__(self, field.name, getattr(instance, field.name))


@_dataclasses.dataclass(frozen=True, slots=True, init=False)
class WealthEventBinding:
    event_id: str
    observed_conditions: tuple[str, ...]
    active_falsifiers: tuple[str, ...]
    edges: tuple[WealthPropagationEdge, ...]

    def __init__(self, *args: object, **values: object) -> None:
        names = tuple(field.name for field in _dataclasses.fields(type(self)))
        if len(args) > len(names) or any(name in values for name in names[: len(args)]):
            raise _error("INVALID_TYPE", "invalid constructor arguments")
        instance = _closed_model(type(self), {**dict(zip(names, args)), **values})
        _text(instance.event_id, "event_id")
        _strings(instance.observed_conditions, "observed_conditions")
        _strings(instance.active_falsifiers, "active_falsifiers")
        if type(instance.edges) is not tuple or any(type(edge) is not WealthPropagationEdge for edge in instance.edges):
            raise _error("INVALID_TYPE", "edges must be tuple[WealthPropagationEdge, ...]")
        for field in _dataclasses.fields(self):
            object.__setattr__(self, field.name, getattr(instance, field.name))


@_dataclasses.dataclass(frozen=True, slots=True)
class WealthEventDecision:
    event_id: str
    decision: WealthPropagationDecision


class UnsupportedDomainStatus(str, Enum):
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


@_dataclasses.dataclass(frozen=True, slots=True)
class UnsupportedDomainProjection:
    domain: str
    status: UnsupportedDomainStatus
    decision_action: DecisionAction


@_dataclasses.dataclass(frozen=True, slots=True)
class FutureProjectionFromState:
    envelope: object
    career_mainline: tuple[CareerFutureCandidate, ...]
    conditional_branches: tuple[HypothesisState, ...]
    wealth_decisions: tuple[WealthEventDecision, ...]
    wealth_states: tuple[RealityStateEntry, ...]
    unsupported_domains: tuple[UnsupportedDomainProjection, ...]


def _duplicates(values: tuple[str, ...]) -> bool:
    return len(values) != len(set(values))


def _validate_result(result: CareerStateBuildResult) -> None:
    envelope = result.envelope
    verified = result.verified_state
    track = verified.reality_track
    identity = envelope.identity
    if envelope.state is not ConsultationState.STATE_BUILT:
        raise _error("INVALID_STATE", "projection requires STATE_BUILT")
    if verified.case_id != identity.case_id or track.case_id != identity.case_id:
        raise _error("IDENTITY_MISMATCH", "case identity differs")
    if verified.as_of_date != identity.as_of_date or track.as_of_date != identity.as_of_date:
        raise _error("IDENTITY_MISMATCH", "as-of identity differs")

    ledger_ids = tuple(entry.candidate.candidate_id for entry in result.ledger_entries)
    if _duplicates(ledger_ids):
        raise _error("DUPLICATE_ID", "duplicate ledger event id")
    if any(entry.assessment.event_id != entry.candidate.candidate_id for entry in result.ledger_entries):
        raise _error("LEDGER_MISMATCH", "ledger event identity differs")
    status_by_id = {entry.candidate.candidate_id: entry.candidate.verification_status for entry in result.ledger_entries}
    confirmed_ids = tuple(identifier for identifier in ledger_ids if status_by_id[identifier] is VerificationStatus.CONFIRMED)
    if verified.verified_event_ids != confirmed_ids or track.verified_event_ids != confirmed_ids:
        raise _error("LEDGER_MISMATCH", "verified event ids differ from confirmed ledger")

    states = track.active_states
    state_ids = tuple(state.state_id for state in states)
    if _duplicates(state_ids):
        raise _error("DUPLICATE_ID", "duplicate active state id")
    if verified.active_state_ids != state_ids:
        raise _error("STATE_MISMATCH", "active state ids differ")
    for state in states:
        status = status_by_id.get(state.source_event_id)
        if status is not VerificationStatus.CONFIRMED:
            if state.source_event_id in status_by_id:
                raise _error("LEDGER_MISMATCH", "active state source is not confirmed")
            raise _error("STATE_MISMATCH", "active state source is unknown")

    path_ids = tuple(path.path_id for path in track.path_states)
    if _duplicates(path_ids):
        statuses_by_path: dict[str, set[str]] = {}
        for path in track.path_states:
            statuses_by_path.setdefault(path.path_id, set()).add(path.status)
        if any({"open", "closed"} <= statuses for statuses in statuses_by_path.values()):
            raise _error("AMBIGUOUS_PATH_STATE", "path is both open and closed")
        raise _error("DUPLICATE_ID", "duplicate path id")
    for path in track.path_states:
        if path.status not in {"open", "closed", "reduced"}:
            raise _error("INVALID_VALUE", "invalid path status")
        status = status_by_id.get(path.source_event_id)
        if status is not VerificationStatus.CONFIRMED:
            if path.source_event_id in status_by_id:
                raise _error("LEDGER_MISMATCH", "path source is not confirmed")
            raise _error("STATE_MISMATCH", "path source is unknown")

    hypothesis_ids = tuple(branch.candidate_id for branch in result.hypothesis_states)
    if _duplicates(hypothesis_ids):
        raise _error("DUPLICATE_ID", "duplicate hypothesis id")
    allowed_statuses = {
        VerificationStatus.PARTIAL_HIT,
        VerificationStatus.UNKNOWN,
        VerificationStatus.WITHHELD,
    }
    for branch in result.hypothesis_states:
        if branch.case_id != identity.case_id or branch.as_of_date != identity.as_of_date:
            raise _error("HYPOTHESIS_MISMATCH", "hypothesis identity differs")
        if status_by_id.get(branch.candidate_id) not in allowed_statuses:
            raise _error("HYPOTHESIS_MISMATCH", "hypothesis is not bound to an eligible ledger event")


def _validate_candidates(result: CareerStateBuildResult, candidates: tuple[CareerFutureCandidate, ...]) -> tuple[CareerFutureCandidate, ...]:
    identity = result.envelope.identity
    identifiers = tuple(candidate.candidate_id for candidate in candidates)
    if _duplicates(identifiers):
        raise _error("DUPLICATE_ID", "duplicate career candidate id")
    active_ids = set(result.verified_state.active_state_ids)
    paths = {path.path_id: path.status for path in result.verified_state.reality_track.path_states}
    selected = []
    for candidate in candidates:
        if candidate.case_id != identity.case_id or candidate.as_of_date != identity.as_of_date:
            raise _error("IDENTITY_MISMATCH", "career candidate identity differs")
        if any(identifier not in active_ids for identifier in candidate.required_active_state_ids):
            raise _error("UNKNOWN_STATE_REFERENCE", "career candidate references unknown active state")
        if any(identifier not in paths for identifier in candidate.required_open_path_ids):
            raise _error("UNKNOWN_PATH_REFERENCE", "career candidate references unknown path")
        if all(paths[identifier] == "open" for identifier in candidate.required_open_path_ids):
            selected.append(candidate)
    return tuple(selected)


def project_future_from_state(
    *,
    result: CareerStateBuildResult,
    career_candidates: tuple[CareerFutureCandidate, ...],
    wealth_bindings: tuple[WealthEventBinding, ...],
) -> FutureProjectionFromState:
    if type(result) is not CareerStateBuildResult:
        raise _error("INVALID_TYPE", "result must be exact CareerStateBuildResult")
    if type(career_candidates) is not tuple or type(wealth_bindings) is not tuple:
        raise _error("INVALID_TYPE", "projection inputs must be tuples")
    _validate_result(result)
    if any(type(candidate) is not CareerFutureCandidate for candidate in career_candidates):
        raise _error("INVALID_TYPE", "career candidate item type differs")
    career_mainline = _validate_candidates(result, career_candidates)
    if any(type(binding) is not WealthEventBinding for binding in wealth_bindings):
        raise _error("INVALID_TYPE", "wealth binding item type differs")

    binding_ids = tuple(binding.event_id for binding in wealth_bindings)
    if _duplicates(binding_ids):
        raise _error("DUPLICATE_ID", "duplicate wealth binding event id")
    confirmed_entries = tuple(
        entry for entry in result.ledger_entries
        if entry.candidate.verification_status is VerificationStatus.CONFIRMED
    )
    confirmed_ids = tuple(entry.candidate.candidate_id for entry in confirmed_entries)
    if binding_ids != confirmed_ids:
        raise _error("WEALTH_BINDING_MISMATCH", "wealth bindings must exactly cover confirmed events in source order")
    binding_by_id = {binding.event_id: binding for binding in wealth_bindings}
    decisions = []
    wealth_states = []
    for entry in confirmed_entries:
        binding = binding_by_id[entry.candidate.candidate_id]
        decision = propagate_career_event_to_wealth(
            event_id=entry.candidate.candidate_id,
            event_type=entry.assessment.event_type,
            event_date=entry.assessment.event_date,
            verified_event=True,
            observed_conditions=binding.observed_conditions,
            active_falsifiers=binding.active_falsifiers,
            edges=binding.edges,
        )
        decisions.append(WealthEventDecision(entry.candidate.candidate_id, decision))
        if decision.changed:
            assert decision.state is not None
            wealth_states.append(decision.state)
    unsupported = tuple(
        UnsupportedDomainProjection(domain, UnsupportedDomainStatus.NOT_IMPLEMENTED, DecisionAction.ABSTAIN)
        for domain in ("family", "education", "marriage", "health")
    )
    return FutureProjectionFromState(
        transition_session(result.envelope, ConsultationState.PROJECTED),
        career_mainline,
        result.hypothesis_states[:2],
        tuple(decisions),
        tuple(wealth_states),
        unsupported,
    )


__all__ = (
    "CareerFutureCandidate",
    "FutureProjectionError",
    "FutureProjectionFromState",
    "UnsupportedDomainProjection",
    "UnsupportedDomainStatus",
    "WealthEventBinding",
    "WealthEventDecision",
    "project_future_from_state",
)
