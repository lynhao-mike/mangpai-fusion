from __future__ import annotations

"""事业核验后的人工裁决，以及事实/假设双状态构建。"""

import dataclasses as _dataclasses
import datetime as _datetime
import hmac as _hmac
from typing import Callable as _Callable, TypeVar as _TypeVar

from engine.asof.consultation_freeze import (
    VERIFICATION_SCHEMA_VERSION,
    CareerFreezePackage,
    CareerVerificationRecord,
    FrozenCareerFundamental,
    VerificationInput,
    VerificationVerdict,
    compute_freeze_package_sha256,
    record_career_verification,
)
from engine.asof.event_candidate import LifeEventCandidate, VerificationStatus
from engine.asof.session_contract import ConsultationState, SessionEnvelope
from engine.asof.state_ledger import (
    AsOfRequest,
    EventImpactAssessment,
    EventLedgerEntry,
    HypothesisState,
    ImpactLevel,
    ImpactScope,
    Persistence,
    VerifiedState,
    admit_hypothesis_branch,
    build_verified_state,
)


CAREER_IMPACT_SUGGESTION_SCHEMA_VERSION = "asof-career-impact-suggestion/v1"


class CareerStateBuilderError(ValueError):
    __slots__ = ("_code",)
    CODES = frozenset(
        {
            "INVALID_TYPE",
            "INVALID_VALUE",
            "SCHEMA_MISMATCH",
            "DUPLICATE_ID",
            "INVALID_STATE",
            "HASH_MISMATCH",
            "UNKNOWN_FIELD",
            "ITEM_NOT_FOUND",
        }
    )

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self._code = code

    @property
    def code(self) -> str:
        return self._code


def _error(code: str, message: str) -> CareerStateBuilderError:
    return CareerStateBuilderError(code, message)


def _exact(value: object, expected: type, field: str) -> None:
    if type(value) is not expected:
        raise _error("INVALID_TYPE", f"{field} must have exact type {expected.__name__}")


def _text(value: object, field: str, *, allow_empty: bool = False) -> str:
    _exact(value, str, field)
    if not allow_empty and not value.strip():
        raise _error("INVALID_VALUE", f"{field} must be non-empty")
    return value


def _date(value: object, field: str) -> _datetime.date:
    _exact(value, _datetime.date, field)
    return value


def _optional_date(value: object, field: str) -> _datetime.date | None:
    if value is not None:
        _date(value, field)
    return value


def _strings(value: object, field: str, *, allow_empty_items: bool = False) -> tuple[str, ...]:
    _exact(value, tuple, field)
    for item in value:
        _text(item, f"{field} item", allow_empty=allow_empty_items)
    return value


_Result = _TypeVar("_Result")


def _closed(operation: _Callable[[], _Result]) -> _Result:
    try:
        return operation()
    except CareerStateBuilderError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise _error("INVALID_VALUE", "domain object is incomplete or internally invalid") from exc


@_dataclasses.dataclass(frozen=True, slots=True, init=False)
class CareerImpactSuggestion:
    schema_version: str
    freeze_package_sha256: str
    item_id: str
    event_date: _datetime.date
    suggested_impact: ImpactLevel
    suggested_persistence: Persistence
    suggested_scope: ImpactScope
    suggested_short_term_until: _datetime.date | None
    state_value: str
    opened_path_ids: tuple[str, ...]
    closed_path_ids: tuple[str, ...]

    def __init__(self, **values: object) -> None:
        allowed = tuple(field.name for field in _dataclasses.fields(type(self)))
        unknown = tuple(key for key in values if key not in allowed)
        if unknown:
            raise _error("UNKNOWN_FIELD", "career impact suggestion contains an unknown field")
        missing = tuple(key for key in allowed if key not in values)
        if missing:
            raise _error("INVALID_VALUE", "career impact suggestion is missing a required field")
        for key in allowed:
            object.__setattr__(self, key, values[key])


@_dataclasses.dataclass(frozen=True, slots=True)
class CareerImpactAdjudication:
    freeze_package_sha256: str
    item_id: str
    final_impact: ImpactLevel
    final_persistence: Persistence
    final_scope: ImpactScope
    final_short_term_until: _datetime.date | None
    adjustment_reason: str
    condition: str
    difference_from_verified: str
    changed_fundamental_ids: tuple[str, ...]
    changed_future_conclusions: tuple[str, ...]
    minimum_question: str
    falsifier: str


@_dataclasses.dataclass(frozen=True, slots=True)
class CareerFundamentalAdjudication:
    freeze_package_sha256: str
    selected_fundamental_id: str
    reason: str


@_dataclasses.dataclass(frozen=True, slots=True)
class _AdjudicatedCareerImpact:
    freeze_package_sha256: str
    item_id: str
    suggestion: CareerImpactSuggestion
    final_impact: ImpactLevel
    final_persistence: Persistence
    final_scope: ImpactScope
    final_short_term_until: _datetime.date | None
    adjustment_reason: str
    condition: str
    difference_from_verified: str
    changed_fundamental_ids: tuple[str, ...]
    changed_future_conclusions: tuple[str, ...]
    minimum_question: str
    falsifier: str


@_dataclasses.dataclass(frozen=True, slots=True)
class CareerAdjudicationBundle:
    envelope: SessionEnvelope
    freeze_package_sha256: str
    package: CareerFreezePackage
    records: tuple[CareerVerificationRecord, ...]
    impact_adjudications: tuple[_AdjudicatedCareerImpact, ...]
    fundamental: FrozenCareerFundamental


@_dataclasses.dataclass(frozen=True, slots=True)
class CareerStateBuildResult:
    envelope: SessionEnvelope
    ledger_entries: tuple[EventLedgerEntry, ...]
    verified_state: VerifiedState
    hypothesis_states: tuple[HypothesisState, ...]


def _validate_expiry(
    persistence: Persistence,
    until: object,
    field: str,
    *,
    event_date: _datetime.date | None = None,
) -> None:
    _optional_date(until, field)
    if persistence is Persistence.SHORT_TERM:
        if until is None:
            raise _error("INVALID_VALUE", f"{field} is required for short-term persistence")
        if event_date is not None and until <= event_date:
            raise _error("INVALID_VALUE", f"{field} must be later than event_date")
    elif until is not None:
        raise _error("INVALID_VALUE", f"{field} is only valid for short-term persistence")


def _validate_suggestion(value: object) -> None:
    _exact(value, CareerImpactSuggestion, "suggestion")
    _text(value.schema_version, "suggestion.schema_version")
    if value.schema_version != CAREER_IMPACT_SUGGESTION_SCHEMA_VERSION:
        raise _error("SCHEMA_MISMATCH", "career impact suggestion schema mismatch")
    _text(value.freeze_package_sha256, "suggestion.freeze_package_sha256")
    _text(value.item_id, "suggestion.item_id")
    _date(value.event_date, "suggestion.event_date")
    _exact(value.suggested_impact, ImpactLevel, "suggestion.suggested_impact")
    _exact(value.suggested_persistence, Persistence, "suggestion.suggested_persistence")
    _exact(value.suggested_scope, ImpactScope, "suggestion.suggested_scope")
    _validate_expiry(
        value.suggested_persistence,
        value.suggested_short_term_until,
        "suggestion.suggested_short_term_until",
        event_date=value.event_date,
    )
    _text(value.state_value, "suggestion.state_value")
    _strings(value.opened_path_ids, "suggestion.opened_path_ids")
    _strings(value.closed_path_ids, "suggestion.closed_path_ids")
    if len(set(value.opened_path_ids)) != len(value.opened_path_ids):
        raise _error("DUPLICATE_ID", "opened path ids must be unique")
    if len(set(value.closed_path_ids)) != len(value.closed_path_ids):
        raise _error("DUPLICATE_ID", "closed path ids must be unique")
    if set(value.opened_path_ids) & set(value.closed_path_ids):
        raise _error("INVALID_VALUE", "a path cannot be both opened and closed")
    if value.suggested_impact is ImpactLevel.TURNING_POINT and not (
        value.opened_path_ids or value.closed_path_ids
    ):
        raise _error("INVALID_VALUE", "turning-point suggestion requires a path change")


def _require_complete_slots(value: object, model: type, field: str) -> None:
    _exact(value, model, field)
    if any(not hasattr(value, item.name) for item in _dataclasses.fields(model)):
        raise _error("INVALID_TYPE", f"{field} is structurally incomplete")


def _validate_adjudication(value: object, frozen_ids: frozenset[str]) -> None:
    _require_complete_slots(value, CareerImpactAdjudication, "adjudication")
    _text(value.freeze_package_sha256, "adjudication.freeze_package_sha256")
    _text(value.item_id, "adjudication.item_id")
    _exact(value.final_impact, ImpactLevel, "adjudication.final_impact")
    _exact(value.final_persistence, Persistence, "adjudication.final_persistence")
    _exact(value.final_scope, ImpactScope, "adjudication.final_scope")
    _validate_expiry(value.final_persistence, value.final_short_term_until, "adjudication.final_short_term_until")
    _text(value.adjustment_reason, "adjudication.adjustment_reason")
    _text(value.condition, "adjudication.condition", allow_empty=True)
    _text(value.difference_from_verified, "adjudication.difference_from_verified", allow_empty=True)
    _strings(value.changed_fundamental_ids, "adjudication.changed_fundamental_ids")
    _strings(value.changed_future_conclusions, "adjudication.changed_future_conclusions")
    _text(value.minimum_question, "adjudication.minimum_question", allow_empty=True)
    _text(value.falsifier, "adjudication.falsifier", allow_empty=True)
    populated = (
        bool(value.condition.strip()),
        bool(value.difference_from_verified.strip()),
        bool(value.changed_fundamental_ids),
        bool(value.changed_future_conclusions),
        bool(value.minimum_question.strip()),
        bool(value.falsifier.strip()),
    )
    if any(populated) and not all(populated):
        raise _error("INVALID_VALUE", "hypothesis fields must be wholly empty or wholly meaningful")
    if not set(value.changed_fundamental_ids) <= frozen_ids:
        raise _error("ITEM_NOT_FOUND", "changed fundamental is outside the frozen package")
    if len(set(value.changed_fundamental_ids)) != len(value.changed_fundamental_ids):
        raise _error("DUPLICATE_ID", "changed fundamental ids must be unique")


def _validate_impact_combination(
    suggestion: CareerImpactSuggestion,
    *,
    final_impact: ImpactLevel,
    final_persistence: Persistence,
    final_short_term_until: _datetime.date | None,
    condition: str,
    difference_from_verified: str,
    changed_fundamental_ids: tuple[str, ...],
    changed_future_conclusions: tuple[str, ...],
    minimum_question: str,
    falsifier: str,
    candidate: LifeEventCandidate,
    verdict: VerificationVerdict,
    as_of_date: _datetime.date,
    frozen_fundamental_ids: frozenset[str],
) -> None:
    if not candidate.window_start <= suggestion.event_date <= candidate.window_end:
        raise _error("INVALID_VALUE", "event_date must lie inside the frozen candidate window")
    if suggestion.event_date > as_of_date:
        raise _error("INVALID_VALUE", "event_date cannot exceed as_of_date")
    _validate_expiry(
        final_persistence,
        final_short_term_until,
        "adjudication.final_short_term_until",
        event_date=suggestion.event_date,
    )
    if (
        suggestion.suggested_persistence is Persistence.SHORT_TERM
        and final_persistence is Persistence.SHORT_TERM
        and final_short_term_until < suggestion.suggested_short_term_until
    ):
        raise _error("INVALID_VALUE", "final short-term expiry cannot precede suggested expiry")
    if final_impact is ImpactLevel.TURNING_POINT and not (
        suggestion.opened_path_ids or suggestion.closed_path_ids
    ):
        raise _error("INVALID_VALUE", "turning-point adjudication requires a path change")
    populated = (
        bool(condition.strip()),
        bool(difference_from_verified.strip()),
        bool(changed_fundamental_ids),
        bool(changed_future_conclusions),
        bool(minimum_question.strip()),
        bool(falsifier.strip()),
    )
    if any(populated) and not all(populated):
        raise _error("INVALID_VALUE", "hypothesis fields must be wholly empty or wholly meaningful")
    if not set(changed_fundamental_ids) <= frozen_fundamental_ids:
        raise _error("ITEM_NOT_FOUND", "changed fundamental is outside the frozen package")
    if len(set(changed_fundamental_ids)) != len(changed_fundamental_ids):
        raise _error("DUPLICATE_ID", "changed fundamental ids must be unique")
    if verdict is VerificationVerdict.CONFIRMED and any(populated):
        raise _error("INVALID_VALUE", "confirmed records cannot carry a hypothesis branch")


def _validate_authoritative_record(
    record: CareerVerificationRecord,
    package: CareerFreezePackage,
) -> None:
    authoritative = record_career_verification(
        record.envelope,
        package,
        VerificationInput(
            VERIFICATION_SCHEMA_VERSION,
            record.freeze_package_sha256,
            record.item_id,
            record.verdict,
            record.actual_landing,
            record.reality_constraint,
            record.taxonomy_evidence,
        ),
    )
    if record != authoritative:
        raise _error("INVALID_VALUE", "record differs from authoritative verification result")


def _validate_fundamental_adjudication(value: object, package: CareerFreezePackage, digest: str) -> FrozenCareerFundamental:
    _require_complete_slots(value, CareerFundamentalAdjudication, "fundamental_adjudication")
    _text(value.freeze_package_sha256, "fundamental_adjudication.freeze_package_sha256")
    if not _hmac.compare_digest(value.freeze_package_sha256, digest):
        raise _error("HASH_MISMATCH", "fundamental adjudication package hash differs")
    if value.selected_fundamental_id is None:
        raise _error("INVALID_VALUE", "fundamental_adjudication.selected_fundamental_id is required")
    _text(value.selected_fundamental_id, "fundamental_adjudication.selected_fundamental_id")
    _text(value.reason, "fundamental_adjudication.reason")
    matches = tuple(item for item in package.fundamentals if item.fundamental_id == value.selected_fundamental_id)
    if len(matches) != 1:
        raise _error("ITEM_NOT_FOUND", "selected fundamental is outside the frozen package")
    return matches[0]


def adjudicate_career_verifications(
    envelope: SessionEnvelope,
    package: CareerFreezePackage,
    records: tuple[CareerVerificationRecord, ...],
    suggestions: tuple[CareerImpactSuggestion, ...],
    impact_adjudications: tuple[CareerImpactAdjudication, ...],
    fundamental_adjudication: CareerFundamentalAdjudication,
) -> CareerAdjudicationBundle:
    def operation() -> CareerAdjudicationBundle:
        _exact(envelope, SessionEnvelope, "envelope")
        if type(envelope.state) is not ConsultationState or envelope.state is not ConsultationState.VERIFICATION_OPEN:
            raise _error("INVALID_STATE", "adjudication requires VERIFICATION_OPEN")
        _require_complete_slots(package, CareerFreezePackage, "package")
        if envelope.identity != package.identity:
            raise _error("INVALID_VALUE", "envelope and package identities differ")
        if not _hmac.compare_digest(envelope.blind_input_sha256, package.blind_input_sha256):
            raise _error("HASH_MISMATCH", "blind input hashes differ")
        digest = compute_freeze_package_sha256(package)

        _exact(records, tuple, "records")
        for record in records:
            _require_complete_slots(record, CareerVerificationRecord, "record")
            if not _hmac.compare_digest(record.freeze_package_sha256, digest):
                raise _error("HASH_MISMATCH", "record package hash differs")
        event_ids = tuple(event.candidate.candidate_id for event in package.events)
        event_id_set = frozenset(event_ids)
        for record in records:
            if record.item_id not in event_id_set:
                raise _error("ITEM_NOT_FOUND", "record item is outside the frozen package")
            if record.envelope != envelope:
                raise _error("INVALID_VALUE", "record envelope differs from adjudication envelope")
            _validate_authoritative_record(record, package)
        record_ids = tuple(record.item_id for record in records)
        if len(set(record_ids)) != len(record_ids):
            raise _error("DUPLICATE_ID", "record ids must be unique")
        if set(record_ids) != event_id_set or len(record_ids) != len(event_ids):
            raise _error("ITEM_NOT_FOUND", "every frozen event requires exactly one record")

        _exact(suggestions, tuple, "suggestions")
        for suggestion in suggestions:
            _validate_suggestion(suggestion)
            if not _hmac.compare_digest(suggestion.freeze_package_sha256, digest):
                raise _error("HASH_MISMATCH", "suggestion package hash differs")
            if suggestion.item_id not in event_id_set:
                raise _error("ITEM_NOT_FOUND", "suggestion item is outside the frozen package")
        suggestion_ids = tuple(item.item_id for item in suggestions)
        if len(set(suggestion_ids)) != len(suggestion_ids):
            raise _error("DUPLICATE_ID", "suggestion ids must be unique")

        frozen_fundamental_ids = frozenset(item.fundamental_id for item in package.fundamentals)
        _exact(impact_adjudications, tuple, "impact_adjudications")
        for decision in impact_adjudications:
            _validate_adjudication(decision, frozen_fundamental_ids)
            if not _hmac.compare_digest(decision.freeze_package_sha256, digest):
                raise _error("HASH_MISMATCH", "impact adjudication package hash differs")
            if decision.item_id not in event_id_set:
                raise _error("ITEM_NOT_FOUND", "impact adjudication item is outside the frozen package")
        decision_ids = tuple(item.item_id for item in impact_adjudications)
        if len(set(decision_ids)) != len(decision_ids):
            raise _error("DUPLICATE_ID", "impact adjudication ids must be unique")

        record_by_id = {item.item_id: item for item in records}
        expected = tuple(item_id for item_id in event_ids if record_by_id[item_id].verdict is not VerificationVerdict.REJECTED)
        if set(suggestion_ids) != set(expected) or len(suggestion_ids) != len(expected):
            raise _error("ITEM_NOT_FOUND", "every non-rejected record requires exactly one suggestion")
        if set(decision_ids) != set(expected) or len(decision_ids) != len(expected):
            raise _error("ITEM_NOT_FOUND", "every non-rejected record requires exactly one adjudication")

        suggestion_by_id = {item.item_id: item for item in suggestions}
        decision_by_id = {item.item_id: item for item in impact_adjudications}
        combined: list[_AdjudicatedCareerImpact] = []
        event_by_id = {item.candidate.candidate_id: item for item in package.events}
        for item_id in expected:
            suggestion = suggestion_by_id[item_id]
            decision = decision_by_id[item_id]
            candidate = event_by_id[item_id].candidate
            _validate_impact_combination(
                suggestion,
                final_impact=decision.final_impact,
                final_persistence=decision.final_persistence,
                final_short_term_until=decision.final_short_term_until,
                condition=decision.condition,
                difference_from_verified=decision.difference_from_verified,
                changed_fundamental_ids=decision.changed_fundamental_ids,
                changed_future_conclusions=decision.changed_future_conclusions,
                minimum_question=decision.minimum_question,
                falsifier=decision.falsifier,
                candidate=candidate,
                verdict=record_by_id[item_id].verdict,
                as_of_date=package.identity.as_of_date,
                frozen_fundamental_ids=frozen_fundamental_ids,
            )
            combined.append(
                _AdjudicatedCareerImpact(
                    decision.freeze_package_sha256,
                    decision.item_id,
                    suggestion,
                    decision.final_impact,
                    decision.final_persistence,
                    decision.final_scope,
                    decision.final_short_term_until,
                    decision.adjustment_reason,
                    decision.condition,
                    decision.difference_from_verified,
                    decision.changed_fundamental_ids,
                    decision.changed_future_conclusions,
                    decision.minimum_question,
                    decision.falsifier,
                )
            )

        fundamental = _validate_fundamental_adjudication(fundamental_adjudication, package, digest)
        return CareerAdjudicationBundle(
            _dataclasses.replace(envelope, state=ConsultationState.ADJUDICATED),
            digest,
            package,
            tuple(record_by_id[item_id] for item_id in event_ids),
            tuple(combined),
            fundamental,
        )

    return _closed(operation)


def build_career_states(bundle: CareerAdjudicationBundle, daiyun_end: _datetime.date) -> CareerStateBuildResult:
    def operation() -> CareerStateBuildResult:
        _require_complete_slots(bundle, CareerAdjudicationBundle, "bundle")
        _require_complete_slots(bundle.envelope, SessionEnvelope, "bundle.envelope")
        if type(bundle.envelope.state) is not ConsultationState or bundle.envelope.state is not ConsultationState.ADJUDICATED:
            raise _error("INVALID_STATE", "state build requires ADJUDICATED")
        _require_complete_slots(bundle.package, CareerFreezePackage, "bundle.package")
        _date(daiyun_end, "daiyun_end")
        if daiyun_end < bundle.package.identity.as_of_date:
            raise _error("INVALID_VALUE", "daiyun_end cannot precede as_of_date")
        if bundle.envelope.identity != bundle.package.identity:
            raise _error("INVALID_VALUE", "bundle envelope and package identities differ")
        if not _hmac.compare_digest(bundle.envelope.blind_input_sha256, bundle.package.blind_input_sha256):
            raise _error("HASH_MISMATCH", "bundle blind input hashes differ")
        digest = compute_freeze_package_sha256(bundle.package)
        _text(bundle.freeze_package_sha256, "bundle.freeze_package_sha256")
        if not _hmac.compare_digest(bundle.freeze_package_sha256, digest):
            raise _error("HASH_MISMATCH", "bundle package hash differs")

        event_ids = tuple(item.candidate.candidate_id for item in bundle.package.events)
        event_id_set = frozenset(event_ids)
        if len(event_id_set) != len(event_ids):
            raise _error("DUPLICATE_ID", "frozen event ids must be unique")

        _exact(bundle.records, tuple, "bundle.records")
        for record in bundle.records:
            _require_complete_slots(record, CareerVerificationRecord, "bundle record")
            _require_complete_slots(record.envelope, SessionEnvelope, "bundle record.envelope")
            _exact(record.verdict, VerificationVerdict, "bundle record.verdict")
            if not _hmac.compare_digest(record.freeze_package_sha256, digest):
                raise _error("HASH_MISMATCH", "bundle record package hash differs")
            if record.item_id not in event_id_set:
                raise _error("ITEM_NOT_FOUND", "bundle record item is outside the frozen package")
            if record.envelope.identity != bundle.package.identity:
                raise _error("INVALID_VALUE", "bundle record identity differs from package")
            if not _hmac.compare_digest(record.envelope.blind_input_sha256, bundle.package.blind_input_sha256):
                raise _error("HASH_MISMATCH", "bundle record blind input hash differs")
            if type(record.envelope.state) is not ConsultationState or record.envelope.state is not ConsultationState.VERIFICATION_OPEN:
                raise _error("INVALID_STATE", "bundle record must originate from VERIFICATION_OPEN")
            _validate_authoritative_record(record, bundle.package)
        record_ids = tuple(item.item_id for item in bundle.records)
        if len(set(record_ids)) != len(record_ids):
            raise _error("DUPLICATE_ID", "bundle record ids must be unique")
        if set(record_ids) != event_id_set or len(record_ids) != len(event_ids):
            raise _error("ITEM_NOT_FOUND", "bundle requires exactly one record per frozen event")
        record_by_id = {item.item_id: item for item in bundle.records}

        expected_ids = tuple(
            item_id
            for item_id in event_ids
            if record_by_id[item_id].verdict is not VerificationVerdict.REJECTED
        )
        _exact(bundle.impact_adjudications, tuple, "bundle.impact_adjudications")
        frozen_fundamental_ids = frozenset(item.fundamental_id for item in bundle.package.fundamentals)
        for decision in bundle.impact_adjudications:
            _require_complete_slots(decision, _AdjudicatedCareerImpact, "bundle impact adjudication")
            _text(decision.freeze_package_sha256, "bundle impact adjudication.freeze_package_sha256")
            _text(decision.item_id, "bundle impact adjudication.item_id")
            if not _hmac.compare_digest(decision.freeze_package_sha256, digest):
                raise _error("HASH_MISMATCH", "bundle impact adjudication package hash differs")
            if decision.item_id not in event_id_set:
                raise _error("ITEM_NOT_FOUND", "bundle impact adjudication item is outside the frozen package")
            _validate_suggestion(decision.suggestion)
            if decision.suggestion.item_id != decision.item_id:
                raise _error("INVALID_VALUE", "bundle suggestion and adjudication item ids differ")
            if not _hmac.compare_digest(decision.suggestion.freeze_package_sha256, digest):
                raise _error("HASH_MISMATCH", "bundle suggestion package hash differs")
            _exact(decision.final_impact, ImpactLevel, "bundle impact adjudication.final_impact")
            _exact(decision.final_persistence, Persistence, "bundle impact adjudication.final_persistence")
            _exact(decision.final_scope, ImpactScope, "bundle impact adjudication.final_scope")
            _text(decision.adjustment_reason, "bundle impact adjudication.adjustment_reason")
            _text(decision.condition, "bundle impact adjudication.condition", allow_empty=True)
            _text(decision.difference_from_verified, "bundle impact adjudication.difference_from_verified", allow_empty=True)
            _strings(decision.changed_fundamental_ids, "bundle impact adjudication.changed_fundamental_ids")
            _strings(decision.changed_future_conclusions, "bundle impact adjudication.changed_future_conclusions")
            _text(decision.minimum_question, "bundle impact adjudication.minimum_question", allow_empty=True)
            _text(decision.falsifier, "bundle impact adjudication.falsifier", allow_empty=True)
            event = next(item for item in bundle.package.events if item.candidate.candidate_id == decision.item_id)
            _validate_impact_combination(
                decision.suggestion,
                final_impact=decision.final_impact,
                final_persistence=decision.final_persistence,
                final_short_term_until=decision.final_short_term_until,
                condition=decision.condition,
                difference_from_verified=decision.difference_from_verified,
                changed_fundamental_ids=decision.changed_fundamental_ids,
                changed_future_conclusions=decision.changed_future_conclusions,
                minimum_question=decision.minimum_question,
                falsifier=decision.falsifier,
                candidate=event.candidate,
                verdict=record_by_id[decision.item_id].verdict,
                as_of_date=bundle.package.identity.as_of_date,
                frozen_fundamental_ids=frozen_fundamental_ids,
            )
        decision_ids = tuple(item.item_id for item in bundle.impact_adjudications)
        if len(set(decision_ids)) != len(decision_ids):
            raise _error("DUPLICATE_ID", "bundle impact adjudication ids must be unique")
        if set(decision_ids) != set(expected_ids) or len(decision_ids) != len(expected_ids):
            raise _error("ITEM_NOT_FOUND", "bundle requires one impact adjudication per non-rejected record")
        decision_by_id = {item.item_id: item for item in bundle.impact_adjudications}

        _require_complete_slots(bundle.fundamental, FrozenCareerFundamental, "bundle.fundamental")
        fundamental_matches = tuple(item for item in bundle.package.fundamentals if item == bundle.fundamental)
        if len(fundamental_matches) != 1:
            raise _error("ITEM_NOT_FOUND", "bundle fundamental is not exactly one frozen choice")
        status_by_verdict = {
            VerificationVerdict.CONFIRMED: VerificationStatus.CONFIRMED,
            VerificationVerdict.PARTIAL_HIT: VerificationStatus.PARTIAL_HIT,
            VerificationVerdict.UNKNOWN: VerificationStatus.UNKNOWN,
            VerificationVerdict.WITHHELD: VerificationStatus.WITHHELD,
        }
        entries: list[EventLedgerEntry] = []
        hypotheses: list[HypothesisState] = []
        request = AsOfRequest(bundle.package.identity.case_id, bundle.package.identity.as_of_date)
        for frozen_event in bundle.package.events:
            candidate = frozen_event.candidate
            record = record_by_id[candidate.candidate_id]
            if record.verdict is VerificationVerdict.REJECTED:
                continue
            decision = decision_by_id[candidate.candidate_id]
            assessed_candidate = _dataclasses.replace(candidate, verification_status=status_by_verdict[record.verdict])
            suggestion = decision.suggestion
            assessment = EventImpactAssessment(
                event_id=candidate.candidate_id,
                event_date=suggestion.event_date,
                event_type=candidate.event_type,
                root_level=candidate.root_level,
                completion_mode=candidate.completion_mode,
                system_suggested_impact=suggestion.suggested_impact,
                system_suggested_persistence=suggestion.suggested_persistence,
                system_suggested_scope=suggestion.suggested_scope,
                practitioner_final_impact=decision.final_impact,
                practitioner_final_persistence=decision.final_persistence,
                practitioner_final_scope=decision.final_scope,
                adjustment_reason=decision.adjustment_reason,
                short_term_until=decision.final_short_term_until,
                state_value=suggestion.state_value,
                opened_path_ids=suggestion.opened_path_ids,
                closed_path_ids=suggestion.closed_path_ids,
            )
            entries.append(EventLedgerEntry(assessed_candidate, assessment))
            if record.verdict is not VerificationVerdict.CONFIRMED and decision.condition:
                branch = admit_hypothesis_branch(
                    request,
                    candidate=assessed_candidate,
                    assessment=assessment,
                    condition=decision.condition,
                    difference_from_verified=decision.difference_from_verified,
                    changed_fundamentals=decision.changed_fundamental_ids,
                    changed_future_conclusions=decision.changed_future_conclusions,
                    minimum_question=decision.minimum_question,
                    falsifier=decision.falsifier,
                )
                if branch is not None:
                    hypotheses.append(branch)

        ledger_entries = tuple(entries)
        verified = build_verified_state(
            request,
            entries=ledger_entries,
            daiyun_end=daiyun_end,
            current_center=bundle.fundamental.center,
            reasonable_range=bundle.fundamental.reasonable_range,
        )
        return CareerStateBuildResult(
            _dataclasses.replace(bundle.envelope, state=ConsultationState.STATE_BUILT),
            ledger_entries,
            verified,
            tuple(hypotheses),
        )

    return _closed(operation)
