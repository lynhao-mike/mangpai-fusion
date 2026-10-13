from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Never, NewType, TypeAlias, assert_never

from engine.f09.canonical_json import JcsValue, bounded_jcs_sha256
from engine.f09.errors import F09ContractError


CanonicalScalar: TypeAlias = None | bool | int | float | str
CanonicalValue: TypeAlias = (
    CanonicalScalar
    | list["CanonicalValue"]
    | tuple["CanonicalValue", ...]
    | Mapping[str, "CanonicalValue"]
)
CanonicalDigest = NewType("CanonicalDigest", str)
StableObjectId = NewType("StableObjectId", str)

_DIGEST_SCHEMA: Final = "governance.canonical-digest.v1"
_ID_SCHEMA: Final = "governance.stable-object-id.v1"
_NAMESPACE_PATTERN: Final = re.compile(
    r"[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*",
)


@dataclass(frozen=True, slots=True)
class CanonicalizationError(Exception):
    issue_code: str
    diagnostic: str

    def __str__(self) -> str:
        return self.diagnostic


def _reject(issue_code: str, diagnostic: str) -> Never:
    raise CanonicalizationError(
        issue_code=issue_code,
        diagnostic=diagnostic,
    )


def _tag_material(value: CanonicalValue, active: set[int]) -> JcsValue:
    match value:
        case None:
            return ("null",)
        case bool() as boolean:
            return ("boolean", "true" if boolean else "false")
        case int() as integer if type(integer) is int:
            return ("integer", str(integer))
        case float() as number if type(number) is float:
            if not math.isfinite(number):
                _reject(
                    "CANONICAL.NON_FINITE_NUMBER",
                    "canonical material contains a non-finite number",
                )
            return ("float", number.hex())
        case str() as text:
            return ("string", text)
        case list() as members:
            identity = id(members)
            if identity in active:
                _reject(
                    "CANONICAL.CYCLE_DETECTED",
                    "canonical material contains a cycle",
                )
            active.add(identity)
            try:
                return (
                    "list",
                    tuple(_tag_material(member, active) for member in members),
                )
            finally:
                active.remove(identity)
        case tuple() as members:
            identity = id(members)
            if identity in active:
                _reject(
                    "CANONICAL.CYCLE_DETECTED",
                    "canonical material contains a cycle",
                )
            active.add(identity)
            try:
                return (
                    "tuple",
                    tuple(_tag_material(member, active) for member in members),
                )
            finally:
                active.remove(identity)
        case Mapping() as mapping:
            identity = id(mapping)
            if identity in active:
                _reject(
                    "CANONICAL.CYCLE_DETECTED",
                    "canonical material contains a cycle",
                )
            active.add(identity)
            try:
                tagged: dict[str, JcsValue] = {}
                for key, item in mapping.items():
                    match key:
                        case str() as text_key:
                            tagged[text_key] = _tag_material(item, active)
                        case unsupported_key:
                            _reject(
                                "CANONICAL.KEY_TYPE_UNSUPPORTED",
                                "canonical mapping keys must be strings",
                            )
                            assert_never(unsupported_key)
                return ("mapping", tagged)
            finally:
                active.remove(identity)
        case unsupported:
            _reject(
                "CANONICAL.TYPE_UNSUPPORTED",
                f"unsupported canonical material type: {type(unsupported).__name__}",
            )
            assert_never(unsupported)


def _digest_tagged(value: JcsValue) -> CanonicalDigest:
    try:
        digest = bounded_jcs_sha256(value)
    except F09ContractError as error:
        raise CanonicalizationError(
            issue_code=error.issue_code,
            diagnostic=error.diagnostic or "bounded JCS rejected canonical material",
        ) from error
    return CanonicalDigest(digest.value)


def canonical_digest(value: CanonicalValue) -> CanonicalDigest:
    """Return a lowercase 64-character SHA-256 digest for canonical material."""
    try:
        tagged = _tag_material(value, set())
    except RecursionError:
        _reject(
            "CANONICAL.DEPTH_EXCEEDED",
            "canonical material exceeds the supported nesting depth",
        )
    return _digest_tagged((_DIGEST_SCHEMA, tagged))


def stable_object_id(
    namespace: str,
    identity: CanonicalValue,
) -> StableObjectId:
    """Return ``<namespace>:<64 lowercase hex>`` for identity material."""
    if _NAMESPACE_PATTERN.fullmatch(namespace) is None:
        _reject(
            "CANONICAL.NAMESPACE_INVALID",
            "namespace must be a lowercase dotted, dashed, or underscored name",
        )
    try:
        tagged = _tag_material(identity, set())
    except RecursionError:
        _reject(
            "CANONICAL.DEPTH_EXCEEDED",
            "canonical identity exceeds the supported nesting depth",
        )
    digest = _digest_tagged((_ID_SCHEMA, namespace, tagged))
    return StableObjectId(f"{namespace}:{digest}")
