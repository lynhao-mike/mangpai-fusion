import json
from dataclasses import fields
from pathlib import Path

import pytest

from engine.f09.canonical_json import parse_bounded_jcs
from engine.f09.contracts import DigestRef, ImmutableJsonSourceBinding, SourceLocator
from engine.f09.errors import F09SourceError
from engine.f09.json_source import (
    ImmutableSnapshotEnvelope,
    load_snapshot,
    resolve_json_pointer,
    resolve_snapshot_field,
)
from engine.f09.markdown_source import resolve_markdown_frozen_field
import engine.f09.json_source as json_source


FIXTURE = Path("plans/production-implementation-pi-300-f09-source-snapshots-v1.json")
DIGEST = DigestRef(
    "sha256",
    "RFC8785-JCS-UTF8",
    "67517fe2d04fb0fe580e031643dab2ad53fcdb8c90707ba4d496c316dd87f5e7",
)


def _binding(**changes: object) -> ImmutableJsonSourceBinding:
    values = {
        "binding_kind": "IMMUTABLE_JSON_SNAPSHOT",
        "binding_schema_version": "source-binding.immutable-json.v1",
        "source_snapshot_id": "PI-300-F09-SOURCE-SNAPSHOT-V1",
        "source_schema_version": "reality-fact-source-snapshot.v1",
        "contract_version": "pi-300-f09-source-snapshots-v1",
        "content_digest": DIGEST,
        "captured_at": "2026-07-19T00:00:00Z",
    }
    values.update(changes)
    return ImmutableJsonSourceBinding(**values)


SOURCE_IDS = {
    ("SOURCE-STATE-1", "/value/level"): "SRCLOC-STATE-LEVEL",
    ("SOURCE-STATE-1", "/value/position"): "SRCLOC-STATE-POSITION",
    ("SOURCE-STATE-1", "/value/as_of"): "SRCLOC-STATE-AS-OF",
    ("SOURCE-EVENT-1", "/value/level"): "SRCLOC-EVENT-LEVEL",
    ("SOURCE-EVENT-1", "/value/change"): "SRCLOC-EVENT-CHANGE",
    ("SOURCE-EVENT-1", "/value/interval/start"): "SRCLOC-EVENT-START",
    ("SOURCE-EVENT-1", "/value/interval/end"): "SRCLOC-EVENT-END",
    ("SOURCE-EVENT-1", "/value/interval/start_inclusive"): "SRCLOC-EVENT-START-INCLUSIVE",
    ("SOURCE-EVENT-1", "/value/interval/end_inclusive"): "SRCLOC-EVENT-END-INCLUSIVE",
    ("SOURCE-OUTCOME-1", "/value/axis"): "SRCLOC-OUTCOME-AXIS",
    ("SOURCE-OUTCOME-1", "/value/action"): "SRCLOC-OUTCOME-ACTION",
    ("SOURCE-OUTCOME-1", "/value/object"): "SRCLOC-OUTCOME-OBJECT",
    ("SOURCE-OUTCOME-1", "/value/tense"): "SRCLOC-OUTCOME-TENSE",
}


def _locator(
    object_id: str,
    pointer: str,
    *,
    path: object = FIXTURE,
    source_id: object | None = None,
    source_type: object = "INPUT_FIELD",
    **binding_changes: object,
) -> SourceLocator:
    return SourceLocator(
        source_id=source_id or SOURCE_IDS.get((object_id, pointer), "INVALID"),  # type: ignore[arg-type]
        source_type=source_type,  # type: ignore[arg-type]
        path=str(path),
        object_id=object_id,
        field_path=pointer,
        binding=_binding(**binding_changes),
    )


def _assert_source_error(call, issue_code: str) -> None:
    with pytest.raises(F09SourceError) as caught:
        call()
    assert caught.value.issue_code == issue_code


POINTERS = (
    ("SRCLOC-STATE-LEVEL", "SOURCE-STATE-1", "/value/level", "S2"),
    ("SRCLOC-STATE-POSITION", "SOURCE-STATE-1", "/value/position", "持续承担资本配置职责"),
    ("SRCLOC-STATE-AS-OF", "SOURCE-STATE-1", "/value/as_of", "2026-06-30"),
    ("SRCLOC-EVENT-LEVEL", "SOURCE-EVENT-1", "/value/level", "E2"),
    ("SRCLOC-EVENT-CHANGE", "SOURCE-EVENT-1", "/value/change", "配置责任范围扩大"),
    ("SRCLOC-EVENT-START", "SOURCE-EVENT-1", "/value/interval/start", "2026-04-01"),
    ("SRCLOC-EVENT-END", "SOURCE-EVENT-1", "/value/interval/end", "2026-06-30"),
    ("SRCLOC-EVENT-START-INCLUSIVE", "SOURCE-EVENT-1", "/value/interval/start_inclusive", True),
    ("SRCLOC-EVENT-END-INCLUSIVE", "SOURCE-EVENT-1", "/value/interval/end_inclusive", True),
    ("SRCLOC-OUTCOME-AXIS", "SOURCE-OUTCOME-1", "/value/axis", "allocation"),
    ("SRCLOC-OUTCOME-ACTION", "SOURCE-OUTCOME-1", "/value/action", "重配资本额度"),
    ("SRCLOC-OUTCOME-OBJECT", "SOURCE-OUTCOME-1", "/value/object", "经营单元A"),
    ("SRCLOC-OUTCOME-TENSE", "SOURCE-OUTCOME-1", "/value/tense", "current"),
)


@pytest.mark.parametrize(("source_id", "object_id", "pointer", "expected"), POINTERS)
def test_all_thirteen_frozen_pointers_resolve_losslessly(
    source_id: str, object_id: str, pointer: str, expected: object
) -> None:
    snapshot = load_snapshot(FIXTURE)
    locator = _locator(object_id, pointer, source_id=source_id)

    observation = resolve_snapshot_field(snapshot, locator=locator)

    assert observation.ref == f"{object_id}#{pointer}"
    assert observation.copied_value == expected
    assert type(observation.copied_value) is type(expected)
    assert observation.locator == locator
    assert observation.transformation == "LOSSLESS_COPY"


def test_rfc6901_escaping_and_empty_pointer_are_exact() -> None:
    root = parse_bounded_jcs(b'{"a/b":{"m~n":null},"":true}')

    assert resolve_json_pointer(root, "") is root
    assert resolve_json_pointer(root, "/a~1b/m~0n") is None
    assert resolve_json_pointer(root, "/") is True


def test_loaded_envelope_has_the_contract_owned_identity_payload_and_path_shape() -> None:
    snapshot = load_snapshot(FIXTURE)

    assert tuple(field.name for field in fields(snapshot)) == (
        "source_snapshot_id",
        "snapshot_schema_version",
        "contract_version",
        "content_digest",
        "captured_at",
        "payload",
        "source_path",
    )
    assert snapshot.source_snapshot_id == "PI-300-F09-SOURCE-SNAPSHOT-V1"
    assert snapshot.snapshot_schema_version == "reality-fact-source-snapshot.v1"
    assert snapshot.contract_version == "pi-300-f09-source-snapshots-v1"
    assert snapshot.content_digest == DIGEST
    assert snapshot.captured_at == "2026-07-19T00:00:00Z"
    assert type(snapshot.payload) is dict
    assert snapshot.source_path == str(FIXTURE)


@pytest.mark.parametrize("pointer", ["a", "/a~", "/a~2b", "/missing", "/0"])
def test_invalid_or_missing_json_pointers_fail_closed(pointer: str) -> None:
    root = parse_bounded_jcs(b'{"a":null}')
    _assert_source_error(
        lambda: resolve_json_pointer(root, pointer),
        "JSON.POINTER_NONCANONICAL"
        if pointer in ("a", "/a~", "/a~2b")
        else "JSON.POINTER_UNRESOLVED",
    )


def test_pointer_is_rooted_at_matched_object_not_inner_value_or_envelope() -> None:
    snapshot = load_snapshot(FIXTURE)
    observation = resolve_snapshot_field(
        snapshot, locator=_locator("SOURCE-STATE-1", "/value/level")
    )
    assert observation.copied_value == "S2"

    matched = parse_bounded_jcs(
        b'{"value":{"level":"S2"}}'
    )
    assert resolve_json_pointer(matched, "") is matched
    assert resolve_json_pointer(matched, "/value/level") == "S2"


@pytest.mark.parametrize(
    ("object_id", "foreign_pointer"),
    [
        ("SOURCE-STATE-1", "/value/change"),
        ("SOURCE-EVENT-1", "/value/axis"),
        ("SOURCE-OUTCOME-1", "/value/position"),
    ],
)
def test_state_event_and_outcome_identities_cannot_interchange(
    object_id: str, foreign_pointer: str
) -> None:
    snapshot = load_snapshot(FIXTURE)
    _assert_source_error(
        lambda: resolve_snapshot_field(
            snapshot, locator=_locator(object_id, foreign_pointer)
        ),
        "JSON.LOCATOR_INVALID",
    )


def test_explicit_null_is_a_resolved_value_not_absent_unavailable_or_unresolved() -> None:
    root = parse_bounded_jcs(b'{"present":null}')
    assert resolve_json_pointer(root, "/present") is None
    _assert_source_error(
        lambda: resolve_json_pointer(root, "/absent"),
        "JSON.POINTER_UNRESOLVED",
    )


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("source_snapshot_id", "drift"),
        ("source_schema_version", "drift"),
        ("contract_version", "drift"),
        (
            "content_digest",
            DigestRef("sha256", "RFC8785-JCS-UTF8", "0" * 64),
        ),
        ("captured_at", "2026-07-20T00:00:00Z"),
    ],
)
def test_any_five_field_locator_identity_drift_fails_closed(
    field: str, replacement: object
) -> None:
    snapshot = load_snapshot(FIXTURE)
    _assert_source_error(
        lambda: resolve_snapshot_field(
            snapshot,
            locator=_locator("SOURCE-STATE-1", "/value/level", **{field: replacement}),
        ),
        "JSON.SNAPSHOT_IDENTITY_MISMATCH",
    )


def _write_mutated_snapshot(tmp_path: Path, mutate) -> Path:
    envelope = json.loads(FIXTURE.read_text(encoding="utf-8"))
    mutate(envelope)
    path = tmp_path / "snapshot.json"
    path.write_text(
        json.dumps(envelope, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def test_payload_digest_drift_fails_even_when_identity_digest_is_unchanged(
    tmp_path: Path,
) -> None:
    path = _write_mutated_snapshot(
        tmp_path,
        lambda envelope: envelope["payload"]["objects"]["SOURCE-STATE-1"][
            "value"
        ].__setitem__("level", "S3"),
    )

    _assert_source_error(
        lambda: load_snapshot(path), "JSON.PAYLOAD_DIGEST_MISMATCH"
    )


def test_missing_object_identity_fails_without_guessing_or_fallback() -> None:
    snapshot = load_snapshot(FIXTURE)
    _assert_source_error(
        lambda: resolve_snapshot_field(
            snapshot, locator=_locator("SOURCE-UNKNOWN-1", "/value/level")
        ),
        "JSON.LOCATOR_INVALID",
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("object_id", None),
        ("object_id", 1),
        ("object_id", ""),
        ("field_path", None),
        ("field_path", 1),
    ],
)
def test_malformed_locator_object_id_and_field_path_fail_as_source_errors(
    field: str, value: object
) -> None:
    snapshot = load_snapshot(FIXTURE)
    locator = _locator("SOURCE-STATE-1", "/value/level")
    object.__setattr__(locator, field, value)

    _assert_source_error(
        lambda: resolve_snapshot_field(snapshot, locator=locator),
        "JSON.LOCATOR_INVALID",
    )


@pytest.mark.parametrize("path", [None, "not-a-path", 1, object()])
def test_malformed_snapshot_path_argument_fails_as_source_error(path: object) -> None:
    _assert_source_error(
        lambda: load_snapshot(path),  # type: ignore[arg-type]
        "JSON.SOURCE_UNAVAILABLE",
    )


def test_exact_path_with_nul_fails_as_source_error() -> None:
    _assert_source_error(
        lambda: load_snapshot(Path("invalid\0snapshot.json")),
        "JSON.SOURCE_UNAVAILABLE",
    )


def test_locator_path_must_equal_the_loaded_snapshot_artifact() -> None:
    snapshot = load_snapshot(FIXTURE)
    _assert_source_error(
        lambda: resolve_snapshot_field(
            snapshot,
            locator=_locator(
                "SOURCE-STATE-1", "/value/level", path="plans/other-snapshot.json"
            ),
        ),
        "JSON.SNAPSHOT_PATH_MISMATCH",
    )


def test_malformed_locator_path_fails_as_source_error() -> None:
    snapshot = load_snapshot(FIXTURE)
    locator = _locator("SOURCE-STATE-1", "/value/level")
    object.__setattr__(locator, "path", None)
    _assert_source_error(
        lambda: resolve_snapshot_field(snapshot, locator=locator),
        "JSON.LOCATOR_INVALID",
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_type", "FINDING_OBJECT"),
        ("source_id", "SRCLOC-STATE-POSITION"),
        ("source_id", None),
    ],
)
def test_source_type_and_per_field_source_id_drift_fail_closed(
    field: str, value: object
) -> None:
    snapshot = load_snapshot(FIXTURE)
    locator = _locator("SOURCE-STATE-1", "/value/level")
    object.__setattr__(locator, field, value)
    _assert_source_error(
        lambda: resolve_snapshot_field(snapshot, locator=locator),
        "JSON.LOCATOR_INVALID",
    )


def test_all_public_source_api_failures_use_exact_source_error_envelope() -> None:
    cases = (
        (
            lambda: resolve_markdown_frozen_field(  # type: ignore[arg-type]
                None,
                "mdff:v1/heading/F09/card/F09/item/Label",
                expected_digest=DIGEST,
            ),
            "MARKDOWN.LOCATOR_INVALID",
            "/locator",
        ),
        (
            lambda: load_snapshot("not-a-path"),  # type: ignore[arg-type]
            "JSON.SOURCE_UNAVAILABLE",
            "/path",
        ),
        (
            lambda: resolve_json_pointer({}, "pointer"),
            "JSON.POINTER_NONCANONICAL",
            "/pointer",
        ),
        (
            lambda: resolve_snapshot_field(  # type: ignore[arg-type]
                None,
                locator=_locator("SOURCE-STATE-1", "/value/level"),
            ),
            "JSON.SNAPSHOT_INVALID",
            "/snapshot",
        ),
    )

    for call, expected_issue_code, expected_field_path in cases:
        with pytest.raises(F09SourceError) as caught:
            call()

        error = caught.value
        assert type(error) is F09SourceError
        assert error.issue_code == expected_issue_code
        assert isinstance(error.issue_code, str)
        assert error.issue_code.strip()
        assert error.field_path == expected_field_path
        assert isinstance(error.diagnostic, str)


def test_resolve_snapshot_field_does_not_read_parse_or_redigest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = ImmutableSnapshotEnvelope(
        source_snapshot_id="PI-300-F09-SOURCE-SNAPSHOT-V1",
        snapshot_schema_version="reality-fact-source-snapshot.v1",
        contract_version="pi-300-f09-source-snapshots-v1",
        content_digest=DIGEST,
        captured_at="2026-07-19T00:00:00Z",
        payload={"objects": {"SOURCE-STATE-1": {"value": {"level": "S2"}}}},
        source_path=str(FIXTURE),
    )

    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("resolve_snapshot_field must only consume its loaded envelope")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(json_source, "parse_bounded_jcs", forbidden)
    monkeypatch.setattr(json_source, "bounded_jcs_sha256", forbidden)
    monkeypatch.setattr(json_source, "load_snapshot", forbidden)

    observation = resolve_snapshot_field(
        snapshot,
        locator=_locator("SOURCE-STATE-1", "/value/level"),
    )

    assert observation.copied_value == "S2"
    assert observation.transformation == "LOSSLESS_COPY"
