from __future__ import annotations

import collections.abc as _collections_abc
import dataclasses as _dataclasses
import datetime as _datetime
import enum as _enum
import hashlib as _hashlib
import hmac as _hmac
import json as _json
import re as _re


BLIND_INPUT_SCHEMA_VERSION = "asof-blind-input/v1"
SESSION_SCHEMA_VERSION = "asof-session/v1"
HEAVENLY_STEMS = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")
EARTHLY_BRANCHES = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")
TWELVE_GROWTH_PHASES = ("长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养")


class ConsultationState(str, _enum.Enum):
    STRICT_BLIND_INPUT = "STRICT_BLIND_INPUT"
    BLIND_DRAFTED = "BLIND_DRAFTED"
    FROZEN = "FROZEN"
    VERIFICATION_OPEN = "VERIFICATION_OPEN"
    ADJUDICATED = "ADJUDICATED"
    STATE_BUILT = "STATE_BUILT"
    PROJECTED = "PROJECTED"
    ARCHIVED = "ARCHIVED"


class ChartSource(str, _enum.Enum):
    WENZHEN_STRUCTURED_V1 = "wenzhen_structured_v1"


class ChartGender(str, _enum.Enum):
    QIAN = "乾"
    KUN = "坤"


class PillarName(str, _enum.Enum):
    YEAR = "year"
    MONTH = "month"
    DAY = "day"
    HOUR = "hour"


class SessionContractError(ValueError):
    __slots__ = ("_code",)

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self._code = code

    @property
    def code(self) -> str:
        return self._code


def _error(code: str, message: str) -> SessionContractError:
    return SessionContractError(code, message)


def _require_exact(value: object, expected: type, field: str) -> None:
    if type(value) is not expected:
        raise _error("INVALID_TYPE", f"{field} must have exact type {expected.__name__}")


def _require_member(value: str, allowed: tuple[str, ...], field: str) -> None:
    if value not in allowed:
        raise _error("INVALID_VALUE", f"{field} is outside its closed value domain")


@_dataclasses.dataclass(frozen=True, slots=True)
class PillarInput:
    stem: str
    branch: str
    hidden_stems: tuple[str, ...]
    changsheng: str

    def __post_init__(self) -> None:
        _require_exact(self.stem, str, "stem")
        _require_member(self.stem, HEAVENLY_STEMS, "stem")
        _require_exact(self.branch, str, "branch")
        _require_member(self.branch, EARTHLY_BRANCHES, "branch")
        _require_exact(self.hidden_stems, tuple, "hidden_stems")
        if not 1 <= len(self.hidden_stems) <= 3:
            raise _error("INVALID_VALUE", "hidden_stems must contain one to three items")
        for hidden_stem in self.hidden_stems:
            _require_exact(hidden_stem, str, "hidden_stems item")
            _require_member(hidden_stem, HEAVENLY_STEMS, "hidden_stems item")
        if len(set(self.hidden_stems)) != len(self.hidden_stems):
            raise _error("INVALID_VALUE", "hidden_stems must not contain duplicates")
        _require_exact(self.changsheng, str, "changsheng")
        _require_member(self.changsheng, TWELVE_GROWTH_PHASES, "changsheng")


@_dataclasses.dataclass(frozen=True, slots=True)
class FourPillarsInput:
    year: PillarInput
    month: PillarInput
    day: PillarInput
    hour: PillarInput

    def __post_init__(self) -> None:
        _require_exact(self.year, PillarInput, "year")
        _require_exact(self.month, PillarInput, "month")
        _require_exact(self.day, PillarInput, "day")
        _require_exact(self.hour, PillarInput, "hour")


@_dataclasses.dataclass(frozen=True, slots=True)
class DaiyunInput:
    sequence: int
    stem: str
    branch: str
    start_date: _datetime.date
    end_date: _datetime.date

    def __post_init__(self) -> None:
        _require_exact(self.sequence, int, "sequence")
        if self.sequence < 1:
            raise _error("INVALID_VALUE", "sequence must be positive")
        _require_exact(self.stem, str, "stem")
        _require_member(self.stem, HEAVENLY_STEMS, "stem")
        _require_exact(self.branch, str, "branch")
        _require_member(self.branch, EARTHLY_BRANCHES, "branch")
        _require_exact(self.start_date, _datetime.date, "start_date")
        _require_exact(self.end_date, _datetime.date, "end_date")
        if self.start_date >= self.end_date:
            raise _error("INVALID_VALUE", "daiyun start_date must precede end_date")


@_dataclasses.dataclass(frozen=True, slots=True)
class BlindChartInput:
    schema_version: str
    chart_source: ChartSource
    gender: ChartGender
    pillars: FourPillarsInput
    daiyun: tuple[DaiyunInput, ...]

    def __post_init__(self) -> None:
        _require_exact(self.schema_version, str, "schema_version")
        if self.schema_version != BLIND_INPUT_SCHEMA_VERSION:
            raise _error("SCHEMA_MISMATCH", "blind input schema version mismatch")
        _require_exact(self.chart_source, ChartSource, "chart_source")
        _require_exact(self.gender, ChartGender, "gender")
        _require_exact(self.pillars, FourPillarsInput, "pillars")
        _require_exact(self.daiyun, tuple, "daiyun")
        if not 1 <= len(self.daiyun) <= 20:
            raise _error("INVALID_VALUE", "daiyun must contain one to twenty items")
        previous = None
        for expected_sequence, item in enumerate(self.daiyun, 1):
            _require_exact(item, DaiyunInput, "daiyun item")
            if item.sequence != expected_sequence:
                raise _error("INVALID_VALUE", "daiyun sequence must start at one and be contiguous")
            if previous is not None and previous.end_date != item.start_date:
                raise _error("INVALID_VALUE", "adjacent daiyun dates must be contiguous")
            previous = item


@_dataclasses.dataclass(frozen=True, slots=True)
class SessionIdentity:
    schema_version: str
    case_id: str
    as_of_date: _datetime.date
    session_id: str

    def __post_init__(self) -> None:
        _require_exact(self.schema_version, str, "schema_version")
        if self.schema_version != SESSION_SCHEMA_VERSION:
            raise _error("SCHEMA_MISMATCH", "session schema version mismatch")
        _require_exact(self.case_id, str, "case_id")
        stem = "[甲乙丙丁戊己庚辛壬癸]"
        branch = "[子丑寅卯辰巳午未申酉戌亥]"
        case_pattern = rf"C-[0-9]{{4}}-(?:[0-9]{{3}}|RF[0-9]{{6}})-(?:乾|坤)-(?:{stem}{branch}){{4}}"
        if _re.fullmatch(case_pattern, self.case_id) is None:
            raise _error("INVALID_VALUE", "case_id has invalid format")
        _require_exact(self.as_of_date, _datetime.date, "as_of_date")
        _require_exact(self.session_id, str, "session_id")
        if _re.fullmatch(r"S-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}", self.session_id) is None:
            raise _error("INVALID_VALUE", "session_id has invalid format")


@_dataclasses.dataclass(frozen=True, slots=True)
class SessionEnvelope:
    identity: SessionIdentity
    blind_input_sha256: str
    state: ConsultationState

    def __post_init__(self) -> None:
        _require_exact(self.identity, SessionIdentity, "identity")
        _require_exact(self.blind_input_sha256, str, "blind_input_sha256")
        if _re.fullmatch(r"[0-9a-f]{64}", self.blind_input_sha256) is None:
            raise _error("INVALID_VALUE", "blind_input_sha256 has invalid format")
        _require_exact(self.state, ConsultationState, "state")


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


def _enum_value(enum_type: type[_enum.Enum], value: object, field: str) -> _enum.Enum:
    _require_exact(value, str, field)
    try:
        return enum_type(value)
    except ValueError:
        raise _error("INVALID_VALUE", f"{field} is outside its closed value domain") from None


def _date_value(value: object, field: str) -> _datetime.date:
    _require_exact(value, str, field)
    if _re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None:
        raise _error("INVALID_VALUE", f"{field} must use YYYY-MM-DD")
    try:
        return _datetime.date.fromisoformat(value)
    except ValueError:
        raise _error("INVALID_VALUE", f"{field} is not a valid date") from None


def _pillar_from_mapping(value: object, field: str) -> PillarInput:
    mapping = _closed_mapping(value, ("stem", "branch", "hidden_stems", "changsheng"), field)
    stem = mapping["stem"]
    _require_exact(stem, str, f"{field}.stem")
    _require_member(stem, HEAVENLY_STEMS, f"{field}.stem")
    branch = mapping["branch"]
    _require_exact(branch, str, f"{field}.branch")
    _require_member(branch, EARTHLY_BRANCHES, f"{field}.branch")
    hidden = mapping["hidden_stems"]
    if type(hidden) is not list:
        raise _error("INVALID_TYPE", f"{field}.hidden_stems must be a list")
    return PillarInput(stem, branch, tuple(hidden), mapping["changsheng"])


def _daiyun_from_mapping(value: object, field: str) -> DaiyunInput:
    item = _closed_mapping(value, ("sequence", "stem", "branch", "start_date", "end_date"), field)
    sequence = item["sequence"]
    _require_exact(sequence, int, f"{field}.sequence")
    if sequence < 1:
        raise _error("INVALID_VALUE", f"{field}.sequence must be positive")
    stem = item["stem"]
    _require_exact(stem, str, f"{field}.stem")
    _require_member(stem, HEAVENLY_STEMS, f"{field}.stem")
    branch = item["branch"]
    _require_exact(branch, str, f"{field}.branch")
    _require_member(branch, EARTHLY_BRANCHES, f"{field}.branch")
    start_date = _date_value(item["start_date"], f"{field}.start_date")
    end_date = _date_value(item["end_date"], f"{field}.end_date")
    return DaiyunInput(sequence, stem, branch, start_date, end_date)


def blind_chart_input_from_mapping(value: object) -> BlindChartInput:
    top = _closed_mapping(value, ("schema_version", "chart_source", "gender", "pillars", "daiyun"), "blind_input")
    _require_exact(top["schema_version"], str, "schema_version")
    if top["schema_version"] != BLIND_INPUT_SCHEMA_VERSION:
        raise _error("SCHEMA_MISMATCH", "blind input schema version mismatch")
    chart_source = _enum_value(ChartSource, top["chart_source"], "chart_source")
    gender = _enum_value(ChartGender, top["gender"], "gender")
    pillars_value = _closed_mapping(top["pillars"], ("year", "month", "day", "hour"), "pillars")
    pillars = FourPillarsInput(
        _pillar_from_mapping(pillars_value["year"], "pillars.year"),
        _pillar_from_mapping(pillars_value["month"], "pillars.month"),
        _pillar_from_mapping(pillars_value["day"], "pillars.day"),
        _pillar_from_mapping(pillars_value["hour"], "pillars.hour"),
    )
    daiyun_value = top["daiyun"]
    if type(daiyun_value) is not list:
        raise _error("INVALID_TYPE", "daiyun must be a list")
    daiyun_items = []
    for index, raw_item in enumerate(daiyun_value):
        daiyun_items.append(_daiyun_from_mapping(raw_item, f"daiyun[{index}]"))
    return BlindChartInput(
        top["schema_version"],
        chart_source,
        gender,
        pillars,
        tuple(daiyun_items),
    )


def _pillar_projection(pillar: PillarInput) -> dict[str, object]:
    return {"stem": pillar.stem, "branch": pillar.branch, "hidden_stems": list(pillar.hidden_stems), "changsheng": pillar.changsheng}


def blind_input_to_canonical_bytes(blind_input: BlindChartInput) -> bytes:
    _require_exact(blind_input, BlindChartInput, "blind_input")
    projection = {
        "schema_version": blind_input.schema_version,
        "chart_source": blind_input.chart_source.value,
        "gender": blind_input.gender.value,
        "pillars": {
            "year": _pillar_projection(blind_input.pillars.year),
            "month": _pillar_projection(blind_input.pillars.month),
            "day": _pillar_projection(blind_input.pillars.day),
            "hour": _pillar_projection(blind_input.pillars.hour),
        },
        "daiyun": [
            {"sequence": item.sequence, "stem": item.stem, "branch": item.branch, "start_date": item.start_date.isoformat(), "end_date": item.end_date.isoformat()}
            for item in blind_input.daiyun
        ],
    }
    return _json.dumps(projection, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def compute_blind_input_sha256(blind_input: BlindChartInput) -> str:
    return _hashlib.sha256(blind_input_to_canonical_bytes(blind_input)).hexdigest()


def create_initial_envelope(identity: SessionIdentity, blind_input: BlindChartInput) -> SessionEnvelope:
    _require_exact(identity, SessionIdentity, "identity")
    _require_exact(blind_input, BlindChartInput, "blind_input")
    expected_gender = identity.case_id.split("-")[3]
    if expected_gender != blind_input.gender.value:
        raise _error("INVALID_VALUE", "case_id gender does not match blind input gender")
    return SessionEnvelope(identity, compute_blind_input_sha256(blind_input), ConsultationState.STRICT_BLIND_INPUT)


def verify_envelope_hash(envelope: SessionEnvelope, blind_input: BlindChartInput) -> None:
    _require_exact(envelope, SessionEnvelope, "envelope")
    _require_exact(blind_input, BlindChartInput, "blind_input")
    actual = compute_blind_input_sha256(blind_input)
    if not _hmac.compare_digest(envelope.blind_input_sha256, actual):
        raise _error("HASH_MISMATCH", "blind input hash does not match envelope")


def transition_session(envelope: SessionEnvelope, target: ConsultationState) -> SessionEnvelope:
    _require_exact(envelope, SessionEnvelope, "envelope")
    _require_exact(target, ConsultationState, "target")
    states = tuple(ConsultationState)
    source_index = states.index(envelope.state)
    if source_index + 1 >= len(states) or states[source_index + 1] is not target:
        raise _error("INVALID_TRANSITION", "only the next forward consultation state is legal")
    return _dataclasses.replace(envelope, state=target)


__all__ = (
    "BLIND_INPUT_SCHEMA_VERSION",
    "SESSION_SCHEMA_VERSION",
    "HEAVENLY_STEMS",
    "EARTHLY_BRANCHES",
    "TWELVE_GROWTH_PHASES",
    "ConsultationState",
    "ChartSource",
    "ChartGender",
    "PillarName",
    "SessionContractError",
    "PillarInput",
    "FourPillarsInput",
    "DaiyunInput",
    "BlindChartInput",
    "SessionIdentity",
    "SessionEnvelope",
    "blind_chart_input_from_mapping",
    "blind_input_to_canonical_bytes",
    "compute_blind_input_sha256",
    "create_initial_envelope",
    "verify_envelope_hash",
    "transition_session",
)
