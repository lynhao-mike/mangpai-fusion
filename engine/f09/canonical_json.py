import hashlib
import json
from dataclasses import dataclass
from typing import TypeAlias, Union

from engine.f09.contracts import DigestRef
from engine.f09.errors import F09ContractError

MAX_DEPTH = 64

JcsValue: TypeAlias = Union[
    None,
    bool,
    str,
    tuple["JcsValue", ...],
    dict[str, "JcsValue"],
]


@dataclass(frozen=True)
class _PNull:
    pass


@dataclass(frozen=True)
class _PBool:
    value: bool


@dataclass(frozen=True)
class _PString:
    value: str


@dataclass(frozen=True)
class _PArray:
    items: tuple["_Prepared", ...]


@dataclass(frozen=True)
class _PObject:
    items: tuple[tuple[str, "_Prepared"], ...]


_Prepared: TypeAlias = Union[_PNull, _PBool, _PString, _PArray, _PObject]


@dataclass(frozen=True)
class _MemoEntry:
    source: dict[object, object]
    prepared: _Prepared
    relative_depth: int


def _reject(issue_code: str, field_path: str) -> None:
    raise F09ContractError(
        issue_code=issue_code,
        field_path=field_path,
        diagnostic="bounded JCS contract rejection",
    )


def _validate_string(value: str) -> None:
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        _reject("JCS.INVALID_UNICODE", "/value")


def _snapshot_dict(value: dict[object, object]) -> tuple[tuple[object, object], ...]:
    return tuple(value.items())


def _prepare(
    value: object,
    active: set[int],
    memo: dict[int, _MemoEntry],
    depth: int,
) -> tuple[_Prepared, int]:
    if depth > MAX_DEPTH:
        _reject("JCS.DEPTH_EXCEEDED", "/value")
    if value is None:
        return (_PNull(), 0)
    if type(value) is bool:
        return (_PBool(value), 0)
    if type(value) is str:
        _validate_string(value)
        return (_PString(value), 0)
    if type(value) is tuple:
        identity = id(value)
        if identity in active:
            _reject("JCS.CYCLE_DETECTED", "/value")
        active.add(identity)
        try:
            children = tuple(
                _prepare(item, active, memo, depth + 1)
                for item in value
            )
            relative_depth = (
                0 if not children
                else 1 + max(child_depth for _, child_depth in children)
            )
            return (
                _PArray(tuple(child for child, _ in children)),
                relative_depth,
            )
        finally:
            active.remove(identity)
    if type(value) is dict:
        identity = id(value)
        if identity in active:
            _reject("JCS.CYCLE_DETECTED", "/value")
        if identity in memo:
            entry = memo[identity]
            if entry.source is not value:
                _reject("JCS.TYPE_UNSUPPORTED", "/value")
            if depth + entry.relative_depth > MAX_DEPTH:
                _reject("JCS.DEPTH_EXCEEDED", "/value")
            return (entry.prepared, entry.relative_depth)
        active.add(identity)
        try:
            try:
                items = _snapshot_dict(value)
            except RuntimeError:
                _reject("JCS.MUTATION_DETECTED", "/value")
            children = []
            for key, item in items:
                if type(key) is not str:
                    _reject("JCS.TYPE_UNSUPPORTED", "/value")
                _validate_string(key)
                child, child_depth = _prepare(
                    item,
                    active,
                    memo,
                    depth + 1,
                )
                children.append((key, child, child_depth))
            relative_depth = (
                0 if not children
                else 1 + max(child_depth for _, _, child_depth in children)
            )
            prepared = _PObject(tuple(
                (key, child) for key, child, _ in children
            ))
            memo[identity] = _MemoEntry(
                source=value,
                prepared=prepared,
                relative_depth=relative_depth,
            )
            return (prepared, relative_depth)
        finally:
            active.remove(identity)
    _reject("JCS.TYPE_UNSUPPORTED", "/value")


def _encode_string(value: str) -> bytes:
    _validate_string(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _encode(prepared: _Prepared) -> bytes:
    if isinstance(prepared, _PNull):
        return b"null"
    if isinstance(prepared, _PBool):
        return b"true" if prepared.value else b"false"
    if isinstance(prepared, _PString):
        return _encode_string(prepared.value)
    if isinstance(prepared, _PArray):
        return b"[" + b",".join(
            _encode(item) for item in prepared.items
        ) + b"]"
    if isinstance(prepared, _PObject):
        ordered = sorted(
            prepared.items,
            key=lambda item: item[0].encode("utf-16-be"),
        )
        return b"{" + b",".join(
            _encode_string(key) + b":" + _encode(item)
            for key, item in ordered
        ) + b"}"
    _reject("JCS.TYPE_UNSUPPORTED", "/value")


def _duplicate_checked_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _reject("JCS.DUPLICATE_KEY", "/raw")
        result[key] = value
    return result


def _reject_number(_value: str) -> None:
    _reject("JCS.NUMBER_UNSUPPORTED", "/raw")


def _normalize_parsed(value: object, depth: int) -> object:
    if depth > MAX_DEPTH:
        _reject("JCS.DEPTH_EXCEEDED", "/raw")
    if type(value) is list:
        return tuple(
            _normalize_parsed(item, depth + 1)
            for item in value
        )
    if type(value) is dict:
        return {
            key: _normalize_parsed(item, depth + 1)
            for key, item in value.items()
        }
    return value


def parse_bounded_jcs(raw: bytes) -> JcsValue:
    if type(raw) is not bytes or raw.startswith(b"\xef\xbb\xbf"):
        _reject("JCS.PARSE_INVALID", "/raw")
    try:
        text = raw.decode("utf-8", errors="strict")
        parsed = json.loads(
            text,
            object_pairs_hook=_duplicate_checked_object,
            parse_int=_reject_number,
            parse_float=_reject_number,
            parse_constant=_reject_number,
        )
        normalized = _normalize_parsed(parsed, 0)
    except F09ContractError:
        raise
    except RecursionError:
        _reject("JCS.DEPTH_EXCEEDED", "/raw")
    except (UnicodeDecodeError, json.JSONDecodeError):
        _reject("JCS.PARSE_INVALID", "/raw")
    try:
        _prepare(normalized, set(), {}, 0)
    except RecursionError:
        _reject("JCS.DEPTH_EXCEEDED", "/raw")
    return normalized


def canonicalize_bounded_jcs(value: JcsValue) -> bytes:
    try:
        prepared, _ = _prepare(value, set(), {}, 0)
        return _encode(prepared)
    except F09ContractError:
        raise
    except RecursionError:
        _reject("JCS.DEPTH_EXCEEDED", "/value")


def bounded_jcs_sha256(value: JcsValue) -> DigestRef:
    canonical_bytes = canonicalize_bounded_jcs(value)
    return DigestRef(
        algorithm="sha256",
        canonicalization="RFC8785-JCS-UTF8",
        value=hashlib.sha256(canonical_bytes).hexdigest(),
    )
