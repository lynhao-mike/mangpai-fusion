from __future__ import annotations

"""事业盲断联合冻结包与现场核验协议。

本模块只负责冻结与核验记录，不裁决事件影响，不生成账本或状态快照。
"""

import collections.abc as _collections_abc
import dataclasses as _dataclasses
import datetime as _datetime
import enum as _enum
import hashlib as _hashlib
import hmac as _hmac
import json as _json
import re as _re
from typing import Callable as _Callable, TypeVar as _TypeVar

from engine.asof.event_candidate import (
    AnnualInteractionTrace,
    CompletionMode,
    ExtensionBoundary,
    LifeEventCandidate,
    RootLevel,
    VerificationStatus,
)
from engine.asof.natal_capacity import EvidenceRef, SourceCitation
from engine.asof.reality_translation import (
    FrozenLandingSet,
    LandingPoint,
    LandingVerdict,
    RealityConstraint,
    verify_landing,
)
from engine.asof.session_contract import (
    SESSION_SCHEMA_VERSION,
    ConsultationState,
    SessionEnvelope,
    SessionIdentity,
)


FREEZE_PACKAGE_SCHEMA_VERSION = "asof-career-freeze-package/v1"
VERIFICATION_SCHEMA_VERSION = "asof-career-verification/v1"


class ConsultationFreezeError(ValueError):
    __slots__ = ("_code",)

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self._code = code

    @property
    def code(self) -> str:
        return self._code


class VerificationVerdict(str, _enum.Enum):
    CONFIRMED = "CONFIRMED"
    PARTIAL_HIT = "PARTIAL_HIT"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"
    WITHHELD = "WITHHELD"


def _error(code: str, message: str) -> ConsultationFreezeError:
    return ConsultationFreezeError(code, message)


def _exact(value: object, expected: type, field: str) -> None:
    if type(value) is not expected:
        raise _error("INVALID_TYPE", f"{field} must have exact type {expected.__name__}")


def _text(value: object, field: str) -> str:
    _exact(value, str, field)
    if not value.strip():
        raise _error("INVALID_VALUE", f"{field} must be non-empty")
    return value


def _date(value: object, field: str) -> _datetime.date:
    _exact(value, _datetime.date, field)
    return value


def _tuple_of(value: object, item_type: type, field: str, *, non_empty: bool = False) -> tuple:
    _exact(value, tuple, field)
    if non_empty and not value:
        raise _error("INVALID_VALUE", f"{field} must be non-empty")
    for item in value:
        if type(item) is not item_type:
            raise _error("INVALID_TYPE", f"{field} item must have exact type {item_type.__name__}")
    return value


_Result = _TypeVar("_Result")


def _closed_validation(operation: _Callable[[], _Result]) -> _Result:
    try:
        return operation()
    except ConsultationFreezeError:
        raise
    except (AttributeError, TypeError, ValueError) as exc:
        raise _error("INVALID_VALUE", "domain object is incomplete or internally invalid") from exc


def _digest(value: object, field: str) -> str:
    _exact(value, str, field)
    if _re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise _error("INVALID_VALUE", f"{field} must be a lowercase SHA-256 digest")
    return value


@_dataclasses.dataclass(frozen=True, slots=True)
class FrozenCareerFundamental:
    fundamental_id: str
    window_start: _datetime.date
    window_end: _datetime.date
    window_center: _datetime.date
    center: str
    reasonable_range: tuple[str, ...]
    strongest_alternative: str
    falsifiers: tuple[str, ...]

    def __post_init__(self) -> None:
        _closed_validation(lambda: _validate_fundamental(self, "fundamental"))


@_dataclasses.dataclass(frozen=True, slots=True)
class FrozenCareerEvent:
    candidate: LifeEventCandidate
    landing_set: FrozenLandingSet

    def __post_init__(self) -> None:
        _closed_validation(lambda: _validate_event(self, "event"))


@_dataclasses.dataclass(frozen=True, slots=True)
class CareerBlindDraft:
    fundamentals: tuple[FrozenCareerFundamental, ...]
    events: tuple[FrozenCareerEvent, ...]

    def __post_init__(self) -> None:
        _closed_validation(lambda: _validate_draft(self))


@_dataclasses.dataclass(frozen=True, slots=True)
class CareerFreezePackage:
    schema_version: str
    identity: SessionIdentity
    blind_input_sha256: str
    fundamentals: tuple[FrozenCareerFundamental, ...]
    events: tuple[FrozenCareerEvent, ...]

    def __post_init__(self) -> None:
        _closed_validation(lambda: _validate_package(self))


@_dataclasses.dataclass(frozen=True, slots=True)
class VerificationInput:
    schema_version: str
    freeze_package_sha256: str
    item_id: str
    verdict: VerificationVerdict
    actual_landing: LandingPoint | None
    reality_constraint: RealityConstraint | None
    taxonomy_evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        _closed_validation(lambda: _validate_verification_input(self))


@_dataclasses.dataclass(frozen=True, slots=True)
class CareerVerificationRecord:
    envelope: SessionEnvelope
    freeze_package_sha256: str
    item_id: str
    verdict: VerificationVerdict
    actual_landing: LandingPoint | None
    reality_constraint: RealityConstraint | None
    taxonomy_evidence: tuple[str, ...]
    landing_verdict: LandingVerdict | None
    frozen_landing_name: str | None
    reason_code: str

    def __post_init__(self) -> None:
        _closed_validation(lambda: _validate_record(self))


def _validate_fundamental(value: object, field: str) -> None:
    _exact(value, FrozenCareerFundamental, field)
    _text(value.fundamental_id, f"{field}.fundamental_id")
    _date(value.window_start, f"{field}.window_start")
    _date(value.window_end, f"{field}.window_end")
    _date(value.window_center, f"{field}.window_center")
    if value.window_start > value.window_end:
        raise _error("INVALID_VALUE", "fundamental window is reversed")
    if not value.window_start <= value.window_center <= value.window_end:
        raise _error("INVALID_VALUE", "window_center must lie inside the window")
    _text(value.center, f"{field}.center")
    _strings(value.reasonable_range, f"{field}.reasonable_range", non_empty=True)
    _text(value.strongest_alternative, f"{field}.strongest_alternative")
    if value.strongest_alternative == value.center:
        raise _error("INVALID_VALUE", "strongest alternative must differ from center")
    _strings(value.falsifiers, f"{field}.falsifiers", non_empty=True)


def _strings(value: object, field: str, *, non_empty: bool = False) -> tuple[str, ...]:
    items = _tuple_of(value, str, field, non_empty=non_empty)
    for item in items:
        _text(item, f"{field} item")
    return items


def _validate_evidence(value: object, field: str) -> None:
    _exact(value, EvidenceRef, field)
    _text(value.source, f"{field}.source")
    _text(value.locator, f"{field}.locator")
    _text(value.excerpt, f"{field}.excerpt")


def _validate_citation(value: object, field: str) -> None:
    _exact(value, SourceCitation, field)
    _text(value.source_path, f"{field}.source_path")
    _exact(value.line, int, f"{field}.line")
    if value.line < 1:
        raise _error("INVALID_VALUE", f"{field}.line must be positive")
    _text(value.excerpt, f"{field}.excerpt")


def _evidence_tuple(value: object, field: str, *, non_empty: bool = False) -> tuple[EvidenceRef, ...]:
    items = _tuple_of(value, EvidenceRef, field, non_empty=non_empty)
    for item in items:
        _validate_evidence(item, f"{field} item")
    return items


def _validate_trace(value: object, field: str) -> None:
    _exact(value, AnnualInteractionTrace, field)
    _exact(value.year, int, f"{field}.year")
    if value.year < 1:
        raise _error("INVALID_VALUE", f"{field}.year must be positive")
    _text(value.liunian, f"{field}.liunian")
    _text(value.dayun_ganzhi, f"{field}.dayun_ganzhi")
    _evidence_tuple(value.relations, f"{field}.relations")
    _strings(value.activated_node_ids, f"{field}.activated_node_ids")
    _strings(value.domains, f"{field}.domains")
    _evidence_tuple(value.supporting_evidence, f"{field}.supporting_evidence")
    _evidence_tuple(value.counter_evidence, f"{field}.counter_evidence")
    _text(value.trigger_strength, f"{field}.trigger_strength")
    if value.trigger_strength not in {"low", "medium", "high"}:
        raise _error("INVALID_VALUE", f"{field}.trigger_strength is invalid")
    _exact(value.crossed_candidate_gate, bool, f"{field}.crossed_candidate_gate")
    if value.crossed_candidate_gate and not (value.relations and value.activated_node_ids):
        raise _error("INVALID_VALUE", f"{field} crossed gate lacks its作用 chain")


def _validate_candidate(value: object, field: str) -> None:
    _exact(value, LifeEventCandidate, field)
    _text(value.candidate_id, f"{field}.candidate_id")
    _text(value.domain, f"{field}.domain")
    if value.domain != "career":
        raise _error("INVALID_VALUE", "candidate must belong to career")
    _text(value.event_type, f"{field}.event_type")
    _date(value.window_start, f"{field}.window_start")
    _date(value.window_end, f"{field}.window_end")
    if value.window_start > value.window_end:
        raise _error("INVALID_VALUE", "candidate window is reversed")
    _evidence_tuple(value.natal_evidence, f"{field}.natal_evidence", non_empty=True)
    _evidence_tuple(value.daiyun_evidence, f"{field}.daiyun_evidence")
    _validate_trace(value.annual_trace, f"{field}.annual_trace")
    _exact(value.root_level, RootLevel, f"{field}.root_level")
    _evidence_tuple(value.root_evidence, f"{field}.root_evidence", non_empty=True)
    citations = _tuple_of(value.source_citations, SourceCitation, f"{field}.source_citations", non_empty=True)
    for item in citations:
        _validate_citation(item, f"{field}.source_citations item")
    _exact(value.completion_mode, CompletionMode, f"{field}.completion_mode")
    _evidence_tuple(value.supporting_evidence, f"{field}.supporting_evidence")
    _evidence_tuple(value.counter_evidence, f"{field}.counter_evidence")
    _strings(value.alternative_hypotheses, f"{field}.alternative_hypotheses")
    _text(value.frozen_version, f"{field}.frozen_version")
    _exact(value.verification_status, VerificationStatus, f"{field}.verification_status")
    if value.verification_status is not VerificationStatus.FROZEN:
        raise _error("INVALID_VALUE", "candidate must already be frozen")
    _exact(value.extension_boundary, ExtensionBoundary, f"{field}.extension_boundary")
    _exact(value.is_primary_event, bool, f"{field}.is_primary_event")
    if not value.is_primary_event:
        raise _error("INVALID_VALUE", "only primary candidates may enter the package")
    if value.completion_mode is CompletionMode.INVALID_COMPLETION:
        raise _error("INVALID_VALUE", "invalid completion cannot produce a primary event")


def _validate_point(value: object, field: str) -> None:
    _exact(value, LandingPoint, field)
    _text(value.name, f"{field}.name")
    _text(value.domain, f"{field}.domain")
    _text(value.direction, f"{field}.direction")


def _validate_landing_set(value: object, field: str) -> None:
    _exact(value, FrozenLandingSet, field)
    _text(value.function_candidate, f"{field}.function_candidate")
    _validate_point(value.center, f"{field}.center")
    alternatives = _tuple_of(value.alternatives, LandingPoint, f"{field}.alternatives")
    if len(alternatives) > 2:
        raise _error("INVALID_VALUE", "at most two alternative landing points may be frozen")
    for item in alternatives:
        _validate_point(item, f"{field}.alternatives item")
        if item.domain != value.center.domain or item.direction != value.center.direction:
            raise _error("INVALID_VALUE", "alternatives must preserve center domain and direction")
    names = (value.center.name,) + tuple(item.name for item in alternatives)
    if len(set(names)) != len(names):
        raise _error("INVALID_VALUE", "frozen landing names must be unique")
    _text(value.weak_hit_boundary, f"{field}.weak_hit_boundary")
    _strings(value.falsifiers, f"{field}.falsifiers", non_empty=True)
    _strings(value.exclusions, f"{field}.exclusions", non_empty=True)
    _text(value.frozen_version, f"{field}.frozen_version")


def _validate_event(value: object, field: str) -> None:
    _exact(value, FrozenCareerEvent, field)
    _validate_candidate(value.candidate, f"{field}.candidate")
    _validate_landing_set(value.landing_set, f"{field}.landing_set")
    if value.landing_set.function_candidate != value.candidate.event_type:
        raise _error("INVALID_VALUE", "landing function must match candidate event type")
    points = (value.landing_set.center,) + value.landing_set.alternatives
    if any(point.domain != "career" for point in points):
        raise _error("INVALID_VALUE", "all frozen landing points must belong to career")


def _validate_identity(value: object, field: str) -> None:
    _exact(value, SessionIdentity, field)
    _exact(value.schema_version, str, f"{field}.schema_version")
    if value.schema_version != SESSION_SCHEMA_VERSION:
        raise _error("SCHEMA_MISMATCH", "session schema version mismatch")
    _text(value.case_id, f"{field}.case_id")
    stem = "[甲乙丙丁戊己庚辛壬癸]"
    branch = "[子丑寅卯辰巳午未申酉戌亥]"
    case_pattern = rf"C-[0-9]{{4}}-(?:[0-9]{{3}}|RF[0-9]{{6}})-(?:乾|坤)-(?:{stem}{branch}){{4}}"
    if _re.fullmatch(case_pattern, value.case_id) is None:
        raise _error("INVALID_VALUE", "case_id has invalid format")
    _date(value.as_of_date, f"{field}.as_of_date")
    _text(value.session_id, f"{field}.session_id")
    if _re.fullmatch(r"S-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}", value.session_id) is None:
        raise _error("INVALID_VALUE", "session_id has invalid format")


def _validate_envelope(value: object, field: str) -> None:
    _exact(value, SessionEnvelope, field)
    _validate_identity(value.identity, f"{field}.identity")
    _digest(value.blind_input_sha256, f"{field}.blind_input_sha256")
    _exact(value.state, ConsultationState, f"{field}.state")


def _validate_draft(value: object) -> None:
    _exact(value, CareerBlindDraft, "draft")
    fundamentals = _tuple_of(value.fundamentals, FrozenCareerFundamental, "fundamentals", non_empty=True)
    for item in fundamentals:
        _validate_fundamental(item, "fundamentals item")
    events = _tuple_of(value.events, FrozenCareerEvent, "events")
    for item in events:
        _validate_event(item, "events item")
    fundamental_ids = tuple(item.fundamental_id for item in fundamentals)
    if len(set(fundamental_ids)) != len(fundamental_ids):
        raise _error("DUPLICATE_ID", "fundamental ids must be unique")
    event_ids = tuple(item.candidate.candidate_id for item in events)
    if len(set(event_ids)) != len(event_ids):
        raise _error("DUPLICATE_ID", "candidate ids must be unique")


def _validate_package(value: object) -> None:
    _exact(value, CareerFreezePackage, "package")
    _exact(value.schema_version, str, "schema_version")
    if value.schema_version != FREEZE_PACKAGE_SCHEMA_VERSION:
        raise _error("SCHEMA_MISMATCH", "freeze package schema version mismatch")
    _validate_identity(value.identity, "identity")
    _digest(value.blind_input_sha256, "blind_input_sha256")
    draft = object.__new__(CareerBlindDraft)
    object.__setattr__(draft, "fundamentals", value.fundamentals)
    object.__setattr__(draft, "events", value.events)
    _validate_draft(draft)
    if any(item.window_end > value.identity.as_of_date for item in value.fundamentals):
        raise _error("INVALID_VALUE", "fundamental window exceeds as_of_date")
    if any(item.candidate.window_end > value.identity.as_of_date for item in value.events):
        raise _error("INVALID_VALUE", "event window exceeds as_of_date")


def _validate_constraint(value: object, field: str) -> None:
    _exact(value, RealityConstraint, field)
    _text(value.state_id, f"{field}.state_id")
    _text(value.description, f"{field}.description")
    _strings(value.closed_landing_names, f"{field}.closed_landing_names")
    _strings(value.reachable_landing_names, f"{field}.reachable_landing_names")
    _exact(value.verified, bool, f"{field}.verified")


def _validate_verification_input(value: object) -> None:
    _exact(value, VerificationInput, "verification")
    _exact(value.schema_version, str, "schema_version")
    if value.schema_version != VERIFICATION_SCHEMA_VERSION:
        raise _error("SCHEMA_MISMATCH", "verification schema version mismatch")
    _digest(value.freeze_package_sha256, "freeze_package_sha256")
    _text(value.item_id, "item_id")
    _exact(value.verdict, VerificationVerdict, "verdict")
    if value.actual_landing is not None:
        _validate_point(value.actual_landing, "actual_landing")
    if value.reality_constraint is not None:
        _validate_constraint(value.reality_constraint, "reality_constraint")
    _strings(value.taxonomy_evidence, "taxonomy_evidence")
def _validate_record(value: object) -> None:
    _exact(value, CareerVerificationRecord, "record")
    _validate_envelope(value.envelope, "envelope")
    if value.envelope.state is not ConsultationState.VERIFICATION_OPEN:
        raise _error("INVALID_STATE", "verification record must remain verification-open")
    _digest(value.freeze_package_sha256, "freeze_package_sha256")
    _text(value.item_id, "item_id")
    _exact(value.verdict, VerificationVerdict, "verdict")
    if value.actual_landing is not None:
        _validate_point(value.actual_landing, "actual_landing")
    if value.reality_constraint is not None:
        _validate_constraint(value.reality_constraint, "reality_constraint")
    _strings(value.taxonomy_evidence, "taxonomy_evidence")
    if value.landing_verdict is not None:
        _exact(value.landing_verdict, LandingVerdict, "landing_verdict")
    if value.frozen_landing_name is not None:
        _text(value.frozen_landing_name, "frozen_landing_name")
    _text(value.reason_code, "reason_code")
    if value.verdict is VerificationVerdict.WITHHELD:
        if value.actual_landing is not None or value.landing_verdict is not None:
            raise _error("INVALID_VALUE", "WITHHELD record cannot contain an actual or landing verdict")
        return
    if value.actual_landing is None:
        raise _error("INVALID_VALUE", "non-WITHHELD record requires an actual landing")
    expected = {
        VerificationVerdict.CONFIRMED: LandingVerdict.CENTER_HIT,
        VerificationVerdict.PARTIAL_HIT: LandingVerdict.ALTERNATIVE_HIT,
        VerificationVerdict.REJECTED: LandingVerdict.MISS,
        VerificationVerdict.UNKNOWN: LandingVerdict.TAXONOMY_GAP,
    }[value.verdict]
    if value.landing_verdict is not expected:
        raise _error("INVALID_VALUE", "record verdict matrix mismatch")


def _identity_projection(identity: SessionIdentity) -> dict[str, object]:
    return {
        "schema_version": identity.schema_version,
        "case_id": identity.case_id,
        "as_of_date": identity.as_of_date.isoformat(),
        "session_id": identity.session_id,
    }


def _evidence_projection(value: EvidenceRef) -> dict[str, object]:
    return {"source": value.source, "locator": value.locator, "excerpt": value.excerpt}


def _citation_projection(value: SourceCitation) -> dict[str, object]:
    return {"source_path": value.source_path, "line": value.line, "excerpt": value.excerpt}


def _point_projection(value: LandingPoint) -> dict[str, object]:
    return {"name": value.name, "domain": value.domain, "direction": value.direction}


def _landing_set_projection(value: FrozenLandingSet) -> dict[str, object]:
    return {
        "function_candidate": value.function_candidate,
        "center": _point_projection(value.center),
        "alternatives": [_point_projection(item) for item in value.alternatives],
        "weak_hit_boundary": value.weak_hit_boundary,
        "falsifiers": list(value.falsifiers),
        "exclusions": list(value.exclusions),
        "frozen_version": value.frozen_version,
    }


def _candidate_projection(value: LifeEventCandidate) -> dict[str, object]:
    trace = value.annual_trace
    return {
        "candidate_id": value.candidate_id,
        "domain": value.domain,
        "event_type": value.event_type,
        "window_start": value.window_start.isoformat(),
        "window_end": value.window_end.isoformat(),
        "natal_evidence": [_evidence_projection(item) for item in value.natal_evidence],
        "daiyun_evidence": [_evidence_projection(item) for item in value.daiyun_evidence],
        "annual_trace": {
            "year": trace.year,
            "liunian": trace.liunian,
            "dayun_ganzhi": trace.dayun_ganzhi,
            "relations": [_evidence_projection(item) for item in trace.relations],
            "activated_node_ids": list(trace.activated_node_ids),
            "domains": list(trace.domains),
            "supporting_evidence": [_evidence_projection(item) for item in trace.supporting_evidence],
            "counter_evidence": [_evidence_projection(item) for item in trace.counter_evidence],
            "trigger_strength": trace.trigger_strength,
            "crossed_candidate_gate": trace.crossed_candidate_gate,
        },
        "root_level": value.root_level.value,
        "root_evidence": [_evidence_projection(item) for item in value.root_evidence],
        "source_citations": [_citation_projection(item) for item in value.source_citations],
        "completion_mode": value.completion_mode.value,
        "supporting_evidence": [_evidence_projection(item) for item in value.supporting_evidence],
        "counter_evidence": [_evidence_projection(item) for item in value.counter_evidence],
        "alternative_hypotheses": list(value.alternative_hypotheses),
        "frozen_version": value.frozen_version,
        "verification_status": value.verification_status.value,
        "extension_boundary": value.extension_boundary.value,
        "is_primary_event": value.is_primary_event,
    }


def _package_projection(package: CareerFreezePackage) -> dict[str, object]:
    return {
        "schema_version": package.schema_version,
        "identity": _identity_projection(package.identity),
        "blind_input_sha256": package.blind_input_sha256,
        "fundamentals": [
            {
                "fundamental_id": item.fundamental_id,
                "window_start": item.window_start.isoformat(),
                "window_end": item.window_end.isoformat(),
                "window_center": item.window_center.isoformat(),
                "center": item.center,
                "reasonable_range": list(item.reasonable_range),
                "strongest_alternative": item.strongest_alternative,
                "falsifiers": list(item.falsifiers),
            }
            for item in package.fundamentals
        ],
        "events": [
            {"candidate": _candidate_projection(item.candidate), "landing_set": _landing_set_projection(item.landing_set)}
            for item in package.events
        ],
    }


def freeze_package_to_canonical_bytes(package: CareerFreezePackage) -> bytes:
    _closed_validation(lambda: _validate_package(package))
    return _json.dumps(
        _package_projection(package),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def compute_freeze_package_sha256(package: CareerFreezePackage) -> str:
    return _hashlib.sha256(freeze_package_to_canonical_bytes(package)).hexdigest()


def verify_freeze_package_hash(package: CareerFreezePackage, expected_sha256: str) -> None:
    _exact(package, CareerFreezePackage, "package")
    expected = _digest(expected_sha256, "expected_sha256")
    actual = compute_freeze_package_sha256(package)
    if not _hmac.compare_digest(actual, expected):
        raise _error("HASH_MISMATCH", "freeze package hash mismatch")


def freeze_career_draft(envelope: SessionEnvelope, draft: CareerBlindDraft) -> tuple[SessionEnvelope, CareerFreezePackage]:
    def operation() -> tuple[SessionEnvelope, CareerFreezePackage]:
        _exact(envelope, SessionEnvelope, "envelope")
        if type(envelope.state) is not ConsultationState or envelope.state is not ConsultationState.BLIND_DRAFTED:
            raise _error("INVALID_STATE", "career draft may only freeze from BLIND_DRAFTED")
        _validate_identity(envelope.identity, "envelope.identity")
        _digest(envelope.blind_input_sha256, "envelope.blind_input_sha256")
        _exact(draft, CareerBlindDraft, "draft")
        _validate_draft(draft)
        for item in draft.fundamentals:
            if item.window_end > envelope.identity.as_of_date:
                raise _error("INVALID_VALUE", "fundamental window exceeds as_of_date")
        for item in draft.events:
            if item.candidate.window_end > envelope.identity.as_of_date:
                raise _error("INVALID_VALUE", "event window exceeds as_of_date")
        package = CareerFreezePackage(
            FREEZE_PACKAGE_SCHEMA_VERSION,
            envelope.identity,
            envelope.blind_input_sha256,
            draft.fundamentals,
            draft.events,
        )
        frozen = _dataclasses.replace(envelope, state=ConsultationState.FROZEN)
        return frozen, package

    return _closed_validation(operation)


def open_verification(
    envelope: SessionEnvelope,
    package: CareerFreezePackage,
    freeze_package_sha256: str,
) -> SessionEnvelope:
    def operation() -> SessionEnvelope:
        _exact(envelope, SessionEnvelope, "envelope")
        _exact(package, CareerFreezePackage, "package")
        if type(envelope.state) is not ConsultationState or envelope.state is not ConsultationState.FROZEN:
            raise _error("INVALID_STATE", "verification may only open from FROZEN")
        _validate_identity(envelope.identity, "envelope.identity")
        _digest(envelope.blind_input_sha256, "envelope.blind_input_sha256")
        _validate_package(package)
        if envelope.identity != package.identity:
            raise _error("INVALID_VALUE", "envelope and package identities differ")
        if not _hmac.compare_digest(envelope.blind_input_sha256, package.blind_input_sha256):
            raise _error("HASH_MISMATCH", "blind input hashes differ")
        verify_freeze_package_hash(package, freeze_package_sha256)
        return _dataclasses.replace(envelope, state=ConsultationState.VERIFICATION_OPEN)

    return _closed_validation(operation)


def _mapping(value: object, field: str) -> _collections_abc.Mapping:
    if not isinstance(value, _collections_abc.Mapping):
        raise _error("INVALID_TYPE", f"{field} must be a mapping")
    return value


def _closed_mapping(value: object, allowed: tuple[str, ...], field: str) -> _collections_abc.Mapping:
    mapping = _mapping(value, field)
    for key in mapping:
        if type(key) is not str or key not in allowed:
            raise _error("UNKNOWN_FIELD", f"{field} contains an unknown field")
    for key in allowed:
        if key not in mapping:
            raise _error("INVALID_VALUE", f"{field}.{key} is required")
    return mapping


def _point_from_mapping(value: object) -> LandingPoint | None:
    if value is None:
        return None
    mapping = _closed_mapping(value, ("name", "domain", "direction"), "actual_landing")
    return LandingPoint(
        _text(mapping["name"], "actual_landing.name"),
        _text(mapping["domain"], "actual_landing.domain"),
        _text(mapping["direction"], "actual_landing.direction"),
    )


def _constraint_from_mapping(value: object) -> RealityConstraint | None:
    if value is None:
        return None
    mapping = _closed_mapping(
        value,
        ("state_id", "description", "closed_landing_names", "reachable_landing_names", "verified"),
        "reality_constraint",
    )
    closed = mapping["closed_landing_names"]
    reachable = mapping["reachable_landing_names"]
    _exact(closed, list, "reality_constraint.closed_landing_names")
    _exact(reachable, list, "reality_constraint.reachable_landing_names")
    for item in closed:
        _text(item, "reality_constraint.closed_landing_names item")
    for item in reachable:
        _text(item, "reality_constraint.reachable_landing_names item")
    _exact(mapping["verified"], bool, "reality_constraint.verified")
    return RealityConstraint(
        _text(mapping["state_id"], "reality_constraint.state_id"),
        _text(mapping["description"], "reality_constraint.description"),
        tuple(closed),
        tuple(reachable),
        mapping["verified"],
    )


def verification_input_from_mapping(value: object) -> VerificationInput:
    allowed = (
        "schema_version",
        "freeze_package_sha256",
        "item_id",
        "verdict",
        "actual_landing",
        "reality_constraint",
        "taxonomy_evidence",
    )
    mapping = _closed_mapping(value, allowed, "verification")
    schema_version = mapping["schema_version"]
    _exact(schema_version, str, "verification.schema_version")
    if schema_version != VERIFICATION_SCHEMA_VERSION:
        raise _error("SCHEMA_MISMATCH", "verification schema version mismatch")
    digest = _digest(mapping["freeze_package_sha256"], "verification.freeze_package_sha256")
    item_id = _text(mapping["item_id"], "verification.item_id")
    raw_verdict = mapping["verdict"]
    _exact(raw_verdict, str, "verification.verdict")
    try:
        verdict = VerificationVerdict(raw_verdict)
    except ValueError as exc:
        raise _error("INVALID_VALUE", "verification.verdict is outside its closed value domain") from exc
    actual = _point_from_mapping(mapping["actual_landing"])
    constraint = _constraint_from_mapping(mapping["reality_constraint"])
    taxonomy = mapping["taxonomy_evidence"]
    _exact(taxonomy, list, "verification.taxonomy_evidence")
    for item in taxonomy:
        _text(item, "verification.taxonomy_evidence item")
    return VerificationInput(schema_version, digest, item_id, verdict, actual, constraint, tuple(taxonomy))


def record_career_verification(
    envelope: SessionEnvelope,
    package: CareerFreezePackage,
    verification: VerificationInput,
) -> CareerVerificationRecord:
    def operation() -> CareerVerificationRecord:
        _exact(envelope, SessionEnvelope, "envelope")
        _exact(package, CareerFreezePackage, "package")
        if type(envelope.state) is not ConsultationState or envelope.state is not ConsultationState.VERIFICATION_OPEN:
            raise _error("INVALID_STATE", "recording requires VERIFICATION_OPEN")
        _validate_identity(envelope.identity, "envelope.identity")
        _digest(envelope.blind_input_sha256, "envelope.blind_input_sha256")
        _validate_package(package)
        if envelope.identity != package.identity:
            raise _error("INVALID_VALUE", "envelope and package identities differ")
        if not _hmac.compare_digest(envelope.blind_input_sha256, package.blind_input_sha256):
            raise _error("HASH_MISMATCH", "blind input hashes differ")
        _exact(verification, VerificationInput, "verification")
        _validate_verification_input(verification)
        verify_freeze_package_hash(package, verification.freeze_package_sha256)
        event = next((item for item in package.events if item.candidate.candidate_id == verification.item_id), None)
        if event is None:
            raise _error("ITEM_NOT_FOUND", "verification item is not present in the frozen package")

        if verification.verdict is VerificationVerdict.WITHHELD:
            if verification.actual_landing is not None:
                raise _error("INVALID_VALUE", "WITHHELD forbids an actual landing")
            landing_verdict = None
            frozen_name = None
            reason_code = "VERIFICATION_WITHHELD"
        else:
            if verification.actual_landing is None:
                raise _error("INVALID_VALUE", "this verdict requires an actual landing")
            if verification.verdict is VerificationVerdict.UNKNOWN and verification.reality_constraint is None:
                raise _error("INVALID_VALUE", "UNKNOWN requires an explicit reality constraint")
            result = verify_landing(
                event.landing_set,
                actual=verification.actual_landing,
                explicit_constraint=verification.reality_constraint,
                taxonomy_evidence=verification.taxonomy_evidence,
            )
            expected = {
                VerificationVerdict.CONFIRMED: LandingVerdict.CENTER_HIT,
                VerificationVerdict.PARTIAL_HIT: LandingVerdict.ALTERNATIVE_HIT,
                VerificationVerdict.REJECTED: LandingVerdict.MISS,
                VerificationVerdict.UNKNOWN: LandingVerdict.TAXONOMY_GAP,
            }[verification.verdict]
            if result.verdict is not expected:
                raise _error("INVALID_VALUE", "verification verdict does not match landing verdict")
            landing_verdict = result.verdict
            frozen_name = result.frozen_landing_name
            reason_code = result.reason_code

        return CareerVerificationRecord(
            envelope,
            verification.freeze_package_sha256,
            verification.item_id,
            verification.verdict,
            verification.actual_landing,
            verification.reality_constraint,
            verification.taxonomy_evidence,
            landing_verdict,
            frozen_name,
            reason_code,
        )

    return _closed_validation(operation)
