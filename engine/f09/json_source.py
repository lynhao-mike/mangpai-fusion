from dataclasses import dataclass
from pathlib import Path

from engine.f09.canonical_json import JcsValue, bounded_jcs_sha256, parse_bounded_jcs
from engine.f09.contracts import DigestRef, ImmutableJsonSourceBinding, SourceLocator
from engine.f09.errors import F09ContractError, F09SourceError
from engine.f09.markdown_source import FrozenFieldObservation


_FROZEN_LOCATOR_IDS = {
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


@dataclass(frozen=True)
class ImmutableSnapshotEnvelope:
    source_snapshot_id: str
    snapshot_schema_version: str
    contract_version: str
    content_digest: DigestRef
    captured_at: str
    payload: dict[str, JcsValue]
    source_path: str


def _reject(issue_code: str, field_path: str) -> None:
    raise F09SourceError(
        issue_code=issue_code,
        field_path=field_path,
        diagnostic="immutable JSON source resolution rejected",
    )


def _required_string(root: dict[str, JcsValue], field: str) -> str:
    value = root.get(field)
    if type(value) is not str or not value:
        _reject("JSON.SNAPSHOT_IDENTITY_INVALID", f"/{field}")
    return value


def _digest_ref(value: JcsValue) -> DigestRef:
    if type(value) is not dict or set(value) != {
        "algorithm",
        "canonicalization",
        "value",
    }:
        _reject("JSON.SNAPSHOT_IDENTITY_INVALID", "/content_digest")
    algorithm = value.get("algorithm")
    canonicalization = value.get("canonicalization")
    digest = value.get("value")
    if (
        algorithm != "sha256"
        or canonicalization != "RFC8785-JCS-UTF8"
        or type(digest) is not str
    ):
        _reject("JSON.SNAPSHOT_IDENTITY_INVALID", "/content_digest")
    try:
        return DigestRef(algorithm, canonicalization, digest)
    except (TypeError, ValueError):
        _reject("JSON.SNAPSHOT_IDENTITY_INVALID", "/content_digest")


def load_snapshot(path: Path) -> ImmutableSnapshotEnvelope:
    if not isinstance(path, Path):
        _reject("JSON.SOURCE_UNAVAILABLE", "/path")
    try:
        source_path = str(path)
        raw = path.read_bytes()
    except (OSError, ValueError, UnicodeError):
        _reject("JSON.SOURCE_UNAVAILABLE", "/path")
    try:
        parsed = parse_bounded_jcs(raw)
    except F09ContractError as error:
        raise F09SourceError(
            issue_code=error.issue_code,
            field_path=error.field_path,
            diagnostic="immutable JSON snapshot parse rejected",
        ) from error
    if type(parsed) is not dict or set(parsed) != {
        "source_snapshot_id",
        "snapshot_schema_version",
        "contract_version",
        "content_digest",
        "captured_at",
        "payload",
    }:
        _reject("JSON.SNAPSHOT_IDENTITY_INVALID", "/")
    payload = parsed.get("payload")
    if type(payload) is not dict:
        _reject("JSON.SNAPSHOT_IDENTITY_INVALID", "/payload")
    digest = _digest_ref(parsed.get("content_digest"))
    if bounded_jcs_sha256(payload) != digest:
        _reject("JSON.PAYLOAD_DIGEST_MISMATCH", "/payload")
    return ImmutableSnapshotEnvelope(
        source_snapshot_id=_required_string(parsed, "source_snapshot_id"),
        snapshot_schema_version=_required_string(parsed, "snapshot_schema_version"),
        contract_version=_required_string(parsed, "contract_version"),
        content_digest=digest,
        captured_at=_required_string(parsed, "captured_at"),
        payload=payload,
        source_path=source_path,
    )


def _decode_token(token: str) -> str:
    output: list[str] = []
    index = 0
    while index < len(token):
        char = token[index]
        if char != "~":
            output.append(char)
            index += 1
            continue
        if index + 1 >= len(token) or token[index + 1] not in "01":
            _reject("JSON.POINTER_NONCANONICAL", "/pointer")
        output.append("~" if token[index + 1] == "0" else "/")
        index += 2
    return "".join(output)


def resolve_json_pointer(root: JcsValue, pointer: str) -> JcsValue:
    if type(pointer) is not str or (pointer and not pointer.startswith("/")):
        _reject("JSON.POINTER_NONCANONICAL", "/pointer")
    if pointer == "":
        return root
    current = root
    for encoded in pointer[1:].split("/"):
        token = _decode_token(encoded)
        if type(current) is dict:
            if token not in current:
                _reject("JSON.POINTER_UNRESOLVED", pointer)
            current = current[token]
        elif type(current) is tuple:
            if (
                not token
                or (len(token) > 1 and token.startswith("0"))
                or not token.isascii()
                or not token.isdigit()
            ):
                _reject("JSON.POINTER_UNRESOLVED", pointer)
            index = int(token)
            if index >= len(current):
                _reject("JSON.POINTER_UNRESOLVED", pointer)
            current = current[index]
        else:
            _reject("JSON.POINTER_UNRESOLVED", pointer)
    return current


def _identity(snapshot: ImmutableSnapshotEnvelope) -> tuple[object, ...]:
    return (
        snapshot.source_snapshot_id,
        snapshot.snapshot_schema_version,
        snapshot.contract_version,
        snapshot.content_digest,
        snapshot.captured_at,
    )


def _binding_identity(binding: ImmutableJsonSourceBinding) -> tuple[object, ...]:
    return (
        binding.source_snapshot_id,
        binding.source_schema_version,
        binding.contract_version,
        binding.content_digest,
        binding.captured_at,
    )


def resolve_snapshot_field(
    snapshot: ImmutableSnapshotEnvelope,
    *,
    locator: SourceLocator,
) -> FrozenFieldObservation:
    if not isinstance(snapshot, ImmutableSnapshotEnvelope):
        _reject("JSON.SNAPSHOT_INVALID", "/snapshot")
    if not isinstance(locator, SourceLocator) or not isinstance(
        locator.binding, ImmutableJsonSourceBinding
    ):
        _reject("JSON.LOCATOR_INVALID", "/locator")
    if type(locator.path) is not str or not locator.path:
        _reject("JSON.LOCATOR_INVALID", "/locator/path")
    if locator.path != snapshot.source_path:
        _reject("JSON.SNAPSHOT_PATH_MISMATCH", "/locator/path")
    if _identity(snapshot) != _binding_identity(locator.binding):
        _reject("JSON.SNAPSHOT_IDENTITY_MISMATCH", "/locator/binding")
    if locator.source_type != "INPUT_FIELD":
        _reject("JSON.LOCATOR_INVALID", "/locator/source_type")
    if type(locator.object_id) is not str or not locator.object_id:
        _reject("JSON.LOCATOR_INVALID", "/locator/object_id")
    if type(locator.field_path) is not str:
        _reject("JSON.LOCATOR_INVALID", "/locator/field_path")
    expected_source_id = _FROZEN_LOCATOR_IDS.get(
        (locator.object_id, locator.field_path)
    )
    if type(locator.source_id) is not str or locator.source_id != expected_source_id:
        _reject("JSON.LOCATOR_INVALID", "/locator/source_id")

    objects = snapshot.payload.get("objects")
    if type(objects) is not dict:
        _reject("JSON.SNAPSHOT_INVALID", "/payload/objects")
    matched = objects.get(locator.object_id)
    if type(matched) is not dict or set(matched) != {"value"}:
        _reject("JSON.OBJECT_UNRESOLVED", f"/payload/objects/{locator.object_id}")
    copied = resolve_json_pointer(matched, locator.field_path)
    return FrozenFieldObservation(
        ref=f"{locator.object_id}#{locator.field_path}",
        copied_value=copied,
        locator=locator,
        transformation="LOSSLESS_COPY",
    )
