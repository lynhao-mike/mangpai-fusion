from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum, unique
from types import MappingProxyType
from typing import Final, Never, NewType, TypeAlias, assert_never

from engine.governance.canonical import (
    CanonicalValue,
    CanonicalizationError,
    canonical_digest,
)


FactId = NewType("FactId", str)
SnapshotId = NewType("SnapshotId", str)
FrozenJsonScalar: TypeAlias = None | bool | int | float | str
FrozenJson: TypeAlias = (
    FrozenJsonScalar | tuple["FrozenJson", ...] | Mapping[str, "FrozenJson"]
)

_DIGEST_PATTERN: Final = re.compile(r"[0-9a-f]{64}")
_DIGEST_ALGORITHM: Final = "sha256"
_CANONICALIZATION: Final = "governance-tagged-jcs-v1"
_MIN_YEAR: Final = 1
_MAX_YEAR: Final = 9999


@dataclass(frozen=True, slots=True)
class FactContractError(Exception):
    issue_code: str
    field_path: str
    diagnostic: str

    def __str__(self) -> str:
        return self.diagnostic


@dataclass(frozen=True, slots=True)
class FactIntegrityError(FactContractError):
    pass


@dataclass(frozen=True, slots=True)
class DuplicateFactIdError(FactIntegrityError):
    fact_id: FactId


@dataclass(frozen=True, slots=True)
class ConflictingFactIdError(FactIntegrityError):
    fact_id: FactId
    first_digest: DigestRef
    conflicting_digest: DigestRef


def _reject(issue_code: str, field_path: str, diagnostic: str) -> Never:
    raise FactContractError(issue_code, field_path, diagnostic)


@dataclass(frozen=True, slots=True)
class DigestRef:
    value: str
    algorithm: str = _DIGEST_ALGORITHM
    canonicalization: str = _CANONICALIZATION

    def __post_init__(self) -> None:
        if self.algorithm != _DIGEST_ALGORITHM:
            _reject("FACT.DIGEST_ALGORITHM", "algorithm", "digest must use sha256")
        if self.canonicalization != _CANONICALIZATION:
            _reject(
                "FACT.DIGEST_CANONICALIZATION",
                "canonicalization",
                "digest must use the governance canonicalization",
            )
        if type(self.value) is not str or _DIGEST_PATTERN.fullmatch(self.value) is None:
            _reject("FACT.DIGEST_VALUE", "value", "digest must be lowercase 64-hex")

    @classmethod
    def from_material(cls, material: CanonicalValue) -> DigestRef:
        try:
            value = canonical_digest(material)
        except CanonicalizationError as error:
            raise FactContractError(
                issue_code=error.issue_code,
                field_path="material",
                diagnostic=error.diagnostic,
            ) from error
        return cls(value=str(value))


@unique
class FactLevel(StrEnum):
    CANONICAL_OBSERVATION = "canonical_observation"
    CANDIDATE_DERIVED = "candidate_derived"
    CERTIFIED_TECHNICAL = "certified_technical"
    CERTIFIED_CROSS_SCHOOL = "certified_cross_school"


@unique
class TemporalLayer(StrEnum):
    NATAL = "natal"
    DAYUN = "dayun"
    LIUNIAN = "liunian"


def _valid_year(field_path: str, value: int) -> int:
    if type(value) is not int or not _MIN_YEAR <= value <= _MAX_YEAR:
        _reject(
            "FACT.YEAR_INVALID",
            field_path,
            f"year must be an integer from {_MIN_YEAR} through {_MAX_YEAR}",
        )
    return value


def _valid_range(start: int, end: int) -> None:
    _valid_year("dayun_start_year", start)
    _valid_year("dayun_end_year", end)
    if start > end:
        _reject(
            "FACT.DAYUN_RANGE_INVERTED",
            "dayun_end_year",
            "dayun start year must not exceed end year",
        )


@dataclass(frozen=True, slots=True)
class TemporalScope:
    layer: TemporalLayer
    dayun_start_year: int | None = None
    dayun_end_year: int | None = None
    target_year: int | None = None

    def __post_init__(self) -> None:
        if type(self.layer) is not TemporalLayer:
            _reject("FACT.TEMPORAL_LAYER", "layer", "layer must be a TemporalLayer")
        match self.layer:
            case TemporalLayer.NATAL:
                years = (self.dayun_start_year, self.dayun_end_year, self.target_year)
                if any(year is not None for year in years):
                    _reject(
                        "FACT.NATAL_FIELDS_FORBIDDEN",
                        "layer",
                        "natal scope cannot contain dayun or liunian years",
                    )
            case TemporalLayer.DAYUN:
                if self.dayun_start_year is None or self.dayun_end_year is None:
                    _reject(
                        "FACT.DAYUN_RANGE_REQUIRED",
                        "layer",
                        "dayun scope requires an explicit year range",
                    )
                _valid_range(self.dayun_start_year, self.dayun_end_year)
                if self.target_year is not None:
                    _reject(
                        "FACT.DAYUN_TARGET_FORBIDDEN",
                        "target_year",
                        "dayun scope cannot contain a liunian target year",
                    )
            case TemporalLayer.LIUNIAN:
                if self.target_year is None:
                    _reject(
                        "FACT.LIUNIAN_TARGET_REQUIRED",
                        "target_year",
                        "liunian scope requires an explicit target year",
                    )
                target = _valid_year("target_year", self.target_year)
                has_start = self.dayun_start_year is not None
                has_end = self.dayun_end_year is not None
                if has_start != has_end:
                    _reject(
                        "FACT.LIUNIAN_DAYUN_RANGE_PARTIAL",
                        "layer",
                        "liunian dayun context must provide both range bounds",
                    )
                start = self.dayun_start_year
                end = self.dayun_end_year
                if start is not None and end is not None:
                    _valid_range(start, end)
                    if not start <= target <= end:
                        _reject(
                            "FACT.LIUNIAN_OUTSIDE_DAYUN",
                            "target_year",
                            "liunian target year is outside its dayun range",
                        )
            case unreachable:
                assert_never(unreachable)


def _text(field_path: str, value: str) -> str:
    if type(value) is not str or not value.strip():
        _reject("FACT.TEXT_REQUIRED", field_path, f"{field_path} must be nonempty")
    return value


def _refs(field_path: str, values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple or not values:
        _reject("FACT.REFS_REQUIRED", field_path, f"{field_path} must be a tuple")
    normalized = tuple(sorted(_text(field_path, value) for value in values))
    if len(normalized) != len(set(normalized)):
        _reject("FACT.REF_DUPLICATE", field_path, f"{field_path} contains duplicates")
    return normalized


@dataclass(frozen=True, slots=True)
class FactSpec:
    fact_kind: str
    fact_level: FactLevel
    temporal_scope: TemporalScope
    source_positions: tuple[str, ...]
    input_refs: tuple[str, ...]
    calculator_id: str
    calculator_version: str

    def __post_init__(self) -> None:
        _text("fact_kind", self.fact_kind)
        _text("calculator_id", self.calculator_id)
        _text("calculator_version", self.calculator_version)
        if type(self.fact_level) is not FactLevel:
            _reject("FACT.LEVEL", "fact_level", "fact_level must be a FactLevel")
        if type(self.temporal_scope) is not TemporalScope:
            _reject("FACT.TEMPORAL_SCOPE", "temporal_scope", "invalid temporal scope")
        object.__setattr__(
            self, "source_positions", _refs("source_positions", self.source_positions)
        )
        object.__setattr__(self, "input_refs", _refs("input_refs", self.input_refs))


@dataclass(frozen=True, slots=True)
class SnapshotSpec:
    schema_version: str
    case_id: str
    input_digest: DigestRef

    def __post_init__(self) -> None:
        _text("schema_version", self.schema_version)
        _text("case_id", self.case_id)
        if type(self.input_digest) is not DigestRef:
            _reject(
                "FACT.INPUT_DIGEST", "input_digest", "input_digest must be DigestRef"
            )


def _freeze_validated(value: CanonicalValue) -> FrozenJson:
    match value:
        case None | bool() | int() | float() | str():
            return value
        case list() | tuple() as members:
            return tuple(_freeze_validated(member) for member in members)
        case Mapping() as mapping:
            return MappingProxyType(
                {key: _freeze_validated(item) for key, item in mapping.items()},
            )
        case unreachable:
            assert_never(unreachable)


def freeze_payload(payload: CanonicalValue) -> FrozenJson:
    DigestRef.from_material(payload)
    return _freeze_validated(payload)
