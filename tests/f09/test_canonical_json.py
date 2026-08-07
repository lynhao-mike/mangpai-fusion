import hashlib
import json
from pathlib import Path

import pytest

import engine.f09.canonical_json as canonical_json
from engine.f09.canonical_json import (
    _PArray,
    _prepare,
    bounded_jcs_sha256,
    canonicalize_bounded_jcs,
    parse_bounded_jcs,
)
from engine.f09.errors import F09ContractError


FIXTURE = Path("plans/production-implementation-pi-300-f09-source-snapshots-v1.json")


def _assert_rejection(call, issue_code: str, field_path: str) -> None:
    with pytest.raises(F09ContractError) as caught:
        call()
    assert caught.value.issue_code == issue_code
    assert caught.value.field_path == field_path


@pytest.mark.parametrize("case", ["fixture"])
def test_frozen_fixture_payload_digest(case: str) -> None:
    assert case == "fixture"
    envelope = json.loads(FIXTURE.read_bytes())
    payload = envelope["payload"]
    raw_payload = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    parsed = parse_bounded_jcs(raw_payload)
    canonical = canonicalize_bounded_jcs(parsed)
    digest = bounded_jcs_sha256(parsed)
    assert digest.algorithm == "sha256"
    assert digest.canonicalization == "RFC8785-JCS-UTF8"
    assert digest.value == hashlib.sha256(canonical).hexdigest()
    assert digest.value == "67517fe2d04fb0fe580e031643dab2ad53fcdb8c90707ba4d496c316dd87f5e7"


@pytest.mark.parametrize(
    "value",
    [
        {"b": "second", "a": "first"},
        {"a": "first", "b": "second"},
    ],
)
def test_object_insertion_order_is_irrelevant(value: dict[str, str]) -> None:
    assert canonicalize_bounded_jcs(value) == b'{"a":"first","b":"second"}'


@pytest.mark.parametrize(
    ("supplementary", "bmp"),
    [
        ("\U00010000", "\uE000"),
        ("\U00010001", "\uE001"),
    ],
)
def test_utf16_key_order_places_supplementary_first(
    supplementary: str,
    bmp: str,
) -> None:
    value = {bmp: "bmp", supplementary: "supplementary"}
    expected = (
        "{"
        + json.dumps(supplementary, ensure_ascii=False)
        + ':"supplementary",'
        + json.dumps(bmp, ensure_ascii=False)
        + ':"bmp"}'
    ).encode("utf-8")
    assert canonicalize_bounded_jcs(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, b"null"),
        (True, b"true"),
        (False, b"false"),
        ("ASCII", b'"ASCII"'),
        ("盲派", '"盲派"'.encode("utf-8")),
    ],
)
def test_legal_scalars(value: object, expected: bytes) -> None:
    assert canonicalize_bounded_jcs(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ((), b"[]"),
        ((("x",),), b'[["x"]]'),
        ({}, b"{}"),
        ({"a": ("x", {"b": False})}, b'{"a":["x",{"b":false}]}'),
    ],
)
def test_legal_containers(value: object, expected: bytes) -> None:
    assert canonicalize_bounded_jcs(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ('"', b'"\\\""'),
        ("\\", b'"\\\\"'),
        ("\b\t\n\f\r", b'"\\b\\t\\n\\f\\r"'),
        ("\x00", b'"\\u0000"'),
        ("/", b'"/"'),
    ],
)
def test_exact_string_escaping(value: str, expected: bytes) -> None:
    assert canonicalize_bounded_jcs(value) == expected


@pytest.mark.parametrize(
    ("raw", "issue_code"),
    [
        (b"\xef\xbb\xbfnull", "JCS.PARSE_INVALID"),
        (b'"\xff"', "JCS.PARSE_INVALID"),
        (b'{"a":null,"a":true}', "JCS.DUPLICATE_KEY"),
        (b"1", "JCS.NUMBER_UNSUPPORTED"),
        (b"1.5", "JCS.NUMBER_UNSUPPORTED"),
        (b"1e2", "JCS.NUMBER_UNSUPPORTED"),
        (b"NaN", "JCS.NUMBER_UNSUPPORTED"),
        (b"Infinity", "JCS.NUMBER_UNSUPPORTED"),
        (b"-Infinity", "JCS.NUMBER_UNSUPPORTED"),
    ],
)
def test_raw_rejections(raw: bytes, issue_code: str) -> None:
    _assert_rejection(lambda: parse_bounded_jcs(raw), issue_code, "/raw")


class _CustomObject:
    pass


class _StringSubclass(str):
    pass


def _cycle() -> dict[str, object]:
    value: dict[str, object] = {}
    value["self"] = value
    return value


@pytest.mark.parametrize(
    ("value", "issue_code"),
    [
        ({1: None}, "JCS.TYPE_UNSUPPORTED"),
        (1, "JCS.TYPE_UNSUPPORTED"),
        (1.0, "JCS.TYPE_UNSUPPORTED"),
        ([], "JCS.TYPE_UNSUPPORTED"),
        (b"value", "JCS.TYPE_UNSUPPORTED"),
        (_CustomObject(), "JCS.TYPE_UNSUPPORTED"),
        ({"\ud800": None}, "JCS.INVALID_UNICODE"),
        ("\udfff", "JCS.INVALID_UNICODE"),
        ({"nested": (_StringSubclass("x"),)}, "JCS.TYPE_UNSUPPORTED"),
        (_cycle(), "JCS.CYCLE_DETECTED"),
    ],
)
def test_direct_and_nested_runtime_rejections(
    value: object,
    issue_code: str,
) -> None:
    _assert_rejection(
        lambda: canonicalize_bounded_jcs(value),
        issue_code,
        "/value",
    )


@pytest.mark.parametrize(
    ("value", "expected", "issue_code"),
    [
        (True, b"true", None),
        (False, b"false", None),
        (1, None, "JCS.TYPE_UNSUPPORTED"),
        (0, None, "JCS.TYPE_UNSUPPORTED"),
    ],
)
def test_bool_is_accepted_before_integer_rejection(
    value: object,
    expected: bytes | None,
    issue_code: str | None,
) -> None:
    if issue_code is None:
        assert canonicalize_bounded_jcs(value) == expected
    else:
        _assert_rejection(
            lambda: canonicalize_bounded_jcs(value),
            issue_code,
            "/value",
        )


def _bounded_case_raw_depth() -> None:
    raw = (b"[" * 65) + b"null" + (b"]" * 65)
    _assert_rejection(
        lambda: parse_bounded_jcs(raw),
        "JCS.DEPTH_EXCEEDED",
        "/raw",
    )


def _bounded_case_relative_depth_reuse() -> None:
    shared = {"child": None}
    deep: object = shared
    for _ in range(63):
        deep = (deep,)
    value = (shared, deep)
    _assert_rejection(
        lambda: canonicalize_bounded_jcs(value),
        "JCS.DEPTH_EXCEEDED",
        "/value",
    )


def _bounded_case_memo_reuse() -> None:
    shared = {"child": None}
    memo = {}
    prepared, relative_depth = _prepare((shared, shared), set(), memo, 0)
    assert isinstance(prepared, _PArray)
    assert prepared.items[0] is prepared.items[1]
    assert relative_depth == 2
    entry = memo[id(shared)]
    assert entry.source is shared
    assert entry.prepared is prepared.items[0]
    assert entry.relative_depth == 1


def _bounded_case_snapshot_runtime_error(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def fail_snapshot(_value: dict[object, object]) -> tuple[tuple[object, object], ...]:
        nonlocal calls
        calls += 1
        raise RuntimeError("deterministic snapshot failure")

    monkeypatch.setattr(canonical_json, "_snapshot_dict", fail_snapshot)
    _assert_rejection(
        lambda: canonicalize_bounded_jcs({"value": None}),
        "JCS.MUTATION_DETECTED",
        "/value",
    )
    assert calls == 1


@pytest.mark.parametrize(
    "case",
    [
        "raw_depth",
        "relative_depth_reuse",
        "memo_reuse",
        "snapshot_runtime_error",
    ],
)
def test_bounded_safety_cases(
    case: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if case == "raw_depth":
        _bounded_case_raw_depth()
    elif case == "relative_depth_reuse":
        _bounded_case_relative_depth_reuse()
    elif case == "memo_reuse":
        _bounded_case_memo_reuse()
    else:
        _bounded_case_snapshot_runtime_error(monkeypatch)
