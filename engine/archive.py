"""Verified artifact 的本地只文件归档边界。"""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import secrets
import stat
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, Any, Iterable


class ArchiveInputError(ValueError):
    """输入不属于冻结的 verified artifact 或路径边界。"""


class ArchiveConflictError(RuntimeError):
    """同一逻辑目标已经存在不同内容。"""


class ArchiveIOError(OSError):
    """归档发布或发布后读回失败。"""


PUBLIC_EXCEPTIONS = (ArchiveInputError, ArchiveConflictError, ArchiveIOError)


@dataclass(frozen=True)
class ArchiveResult:
    status: str
    target: Path
    artifact_id: str
    payload_digest: str
    report: str


_FIELDS = {
    "schema_version",
    "artifact_id",
    "source_digest",
    "payload_digest",
    "verified_at",
    "verifier",
    "verification_basis",
    "payload",
}
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_ARTIFACT_ID = re.compile(r"[A-Za-z0-9._+-]+\Z")
_TOKEN = re.compile(r"[A-Za-z0-9._:/+-]+\Z")


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _parse_time(value: object) -> datetime:
    if not isinstance(value, str) or not value:
        raise ArchiveInputError("verified_at must be an offset-aware RFC 3339 time")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ArchiveInputError("verified_at must be an offset-aware RFC 3339 time") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ArchiveInputError("verified_at must include an explicit UTC offset")
    return parsed


def _validate_artifact(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _FIELDS:
        raise ArchiveInputError("verified artifact must contain exactly the canonical fields")
    for field in ("schema_version", "artifact_id", "verifier"):
        if not isinstance(value[field], str) or not value[field]:
            raise ArchiveInputError(f"{field} must be a non-empty string")
    if not _ARTIFACT_ID.fullmatch(value["artifact_id"]):
        raise ArchiveInputError("artifact_id is not a safe logical target name")
    if not _TOKEN.fullmatch(value["schema_version"]):
        raise ArchiveInputError("schema_version must be a token")
    for field in ("source_digest", "payload_digest"):
        if not isinstance(value[field], str) or not _DIGEST.fullmatch(value[field]):
            raise ArchiveInputError(f"{field} must be a lowercase SHA-256 digest")
    _parse_time(value["verified_at"])
    basis = value["verification_basis"]
    if (
        not isinstance(basis, list)
        or not basis
        or any(not isinstance(item, str) or not item for item in basis)
        or len(set(basis)) != len(basis)
    ):
        raise ArchiveInputError("verification_basis must be a non-empty unique string array")
    if not isinstance(value["payload"], dict):
        raise ArchiveInputError("payload must be an object")
    try:
        payload_bytes = _canonical_json(value["payload"])
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ArchiveInputError("payload must be canonical UTF-8 JSON") from exc
    actual_payload_digest = hashlib.sha256(payload_bytes).hexdigest()
    if actual_payload_digest != value["payload_digest"]:
        raise ArchiveInputError("payload_digest does not match canonical payload bytes")
    return value


def _reject_reparse(path: Path) -> None:
    """拒绝既有路径及其既有祖先中的符号链接/reparse point。"""
    path = Path(path).absolute()
    for candidate in (path, *path.parents):
        if not candidate.exists() and not candidate.is_symlink():
            continue
        try:
            info = candidate.lstat()
        except OSError as exc:
            raise ArchiveIOError(f"cannot inspect path identity: {candidate}") from exc
        attributes = getattr(info, "st_file_attributes", 0)
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        if candidate.is_symlink() or attributes & reparse_flag:
            raise ArchiveInputError(f"reparse point is forbidden: {candidate}")


def _windows_identity_snapshot(path: Path) -> tuple[int, int, str]:
    from ctypes import wintypes

    class FileInformation(ctypes.Structure):
        _fields_ = [
            ("attributes", wintypes.DWORD),
            ("creation_time_low", wintypes.DWORD),
            ("creation_time_high", wintypes.DWORD),
            ("access_time_low", wintypes.DWORD),
            ("access_time_high", wintypes.DWORD),
            ("write_time_low", wintypes.DWORD),
            ("write_time_high", wintypes.DWORD),
            ("volume_serial", wintypes.DWORD),
            ("size_high", wintypes.DWORD),
            ("size_low", wintypes.DWORD),
            ("links", wintypes.DWORD),
            ("file_index_high", wintypes.DWORD),
            ("file_index_low", wintypes.DWORD),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE
    get_information = kernel32.GetFileInformationByHandle
    get_information.argtypes = [wintypes.HANDLE, ctypes.POINTER(FileInformation)]
    get_information.restype = wintypes.BOOL
    get_final_path = kernel32.GetFinalPathNameByHandleW
    get_final_path.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
    get_final_path.restype = wintypes.DWORD
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [wintypes.HANDLE]
    close_handle.restype = wintypes.BOOL
    handle = create_file(
        str(path), 0, 0x1 | 0x2 | 0x4, None, 3, 0x02000000, None
    )
    invalid = wintypes.HANDLE(-1).value
    if handle == invalid:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        information = FileInformation()
        if not get_information(handle, ctypes.byref(information)):
            raise ctypes.WinError(ctypes.get_last_error())
        size = get_final_path(handle, None, 0, 0)
        if not size:
            raise ctypes.WinError(ctypes.get_last_error())
        buffer = ctypes.create_unicode_buffer(size + 1)
        if not get_final_path(handle, buffer, len(buffer), 0):
            raise ctypes.WinError(ctypes.get_last_error())
        file_index = (information.file_index_high << 32) | information.file_index_low
        return information.volume_serial, file_index, buffer.value.casefold()
    finally:
        if not close_handle(handle):
            raise ctypes.WinError(ctypes.get_last_error())


def _identity_snapshot(path: Path) -> tuple[int, int, str]:
    """返回打开句柄所观察到的文件身份与最终解析路径。"""
    path = Path(path)
    try:
        if os.name == "nt":
            return _windows_identity_snapshot(path)
        descriptor = os.open(path, os.O_RDONLY)
        try:
            info = os.fstat(descriptor)
            final_path = str(Path(os.path.realpath(path)).absolute()).casefold()
            return info.st_dev, info.st_ino, final_path
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise ArchiveIOError(f"cannot capture handle identity: {path}") from exc


def _open_stage(parent: Path) -> tuple[IO[bytes], Path]:
    for _ in range(32):
        path = parent / f".{secrets.token_hex(16)}.staging"
        try:
            return path.open("xb"), path
        except FileExistsError:
            continue
        except OSError as exc:
            raise ArchiveIOError("cannot create same-parent staging file") from exc
    raise ArchiveIOError("cannot allocate an exclusive staging name")


def _rename_no_replace(source: Path, target: Path) -> None:
    if target.exists():
        raise FileExistsError(str(target))
    os.rename(source, target)


def _readback(target: Path) -> bytes:
    try:
        with target.open("rb") as handle:
            return handle.read()
    except OSError as exc:
        raise ArchiveIOError("cannot read back published artifact") from exc


def _text(value: object) -> str:
    text = str(value)
    if not 1 <= len(text) <= 512 or any(ord(char) < 32 for char in text) or "|" in text:
        raise ArchiveInputError("report TEXT is outside the frozen grammar")
    return text


def _token(value: object) -> str:
    text = str(value)
    if not _TOKEN.fullmatch(text):
        raise ArchiveInputError("report TOKEN is outside the frozen grammar")
    return text


def _render_report(
    artifact: dict[str, Any],
    status: str,
    target: Path,
    events: Iterable[dict[str, str]] = (),
) -> str:
    event_values = list(events)
    if len(event_values) > 19:
        raise ArchiveInputError("report accepts at most 19 events")
    normalized_events: list[tuple[datetime, str, str, str]] = []
    for event in event_values:
        if set(event) != {"time", "kind", "detail"}:
            raise ArchiveInputError("event must contain time, kind and detail")
        parsed = _parse_time(event["time"])
        normalized_events.append((parsed, event["time"], _token(event["kind"]), _text(event["detail"])))
    normalized_events.sort(key=lambda item: item[0])
    now = datetime.now(timezone.utc).isoformat()
    payload_size = len(_canonical_json(artifact["payload"]))
    archived_size = len(_canonical_json(artifact))
    basis = ",".join(artifact["verification_basis"])
    fixed = [
        "REPORT: VERIFIED ARTIFACT ARCHIVE",
        "report-schema: verified-artifact-archive/v1",
        f"artifact-id: {_text(artifact['artifact_id'])}",
        f"artifact-schema: {_token(artifact['schema_version'])}",
        f"source-digest: {artifact['source_digest']}",
        f"payload-digest: {artifact['payload_digest']}",
        f"verified-at: {artifact['verified_at']}",
        f"verifier: {_text(artifact['verifier'])}",
        f"verification-basis: {_text(basis)}",
        f"archive-result: {_token(status)}",
        f"archive-target: {_text(target)}",
        f"archive-observed-at: {now}",
        f"input-name: {_text(target.name)}",
        f"input-size-bytes: {archived_size}",
        f"payload-size-bytes: {payload_size}",
        "report-generator: engine.archive",
        f"report-generated-at: {now}",
        f"event-count: {len(normalized_events)}",
        "event-order: chronological",
        "digest-algorithm: sha256",
        "text-encoding: utf-8",
        "line-ending: lf",
        "fixed-line-count: 33",
        "event-line-count: 19",
        "total-line-count: 52",
        *[f"reserved-0{index}: -" for index in range(1, 8)],
        "EVENTS: BEGIN",
    ]
    event_lines = []
    for index in range(1, 20):
        if index <= len(normalized_events):
            _, time_text, kind, detail = normalized_events[index - 1]
            event_lines.append(f"event-{index:02d}: USED|{time_text}|{kind}|{detail}")
        else:
            event_lines.append(f"event-{index:02d}: EMPTY|-|-|-")
    return "\n".join([*fixed, *event_lines]) + "\n"


def _existing_result(
    target: Path, candidate: bytes, artifact: dict[str, Any]
) -> ArchiveResult:
    target_identity = _identity_snapshot(target)
    observed = _readback(target)
    if _identity_snapshot(target) != target_identity:
        raise ArchiveIOError("existing archive target identity changed during readback")
    if observed != candidate:
        raise ArchiveConflictError(f"archive target conflicts: {target}")
    return ArchiveResult(
        "UNCHANGED",
        target,
        artifact["artifact_id"],
        artifact["payload_digest"],
        _render_report(artifact, "UNCHANGED", target),
    )


def archive_verified_artifact(source: os.PathLike[str] | str, archive_root: os.PathLike[str] | str) -> ArchiveResult:
    """验证 JSON artifact 及其 ``.source`` sidecar，并安全归档。"""
    source = Path(source)
    source_sidecar = source.with_name(source.name + ".source")
    archive_root = Path(archive_root)
    _reject_reparse(source)
    _reject_reparse(source_sidecar)
    _reject_reparse(archive_root)
    try:
        raw = source.read_bytes()
        source_bytes = source_sidecar.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ArchiveInputError("source and its .source sidecar must be readable") from exc
    artifact = _validate_artifact(value)
    if hashlib.sha256(source_bytes).hexdigest() != artifact["source_digest"]:
        raise ArchiveInputError("source_digest does not match .source sidecar bytes")
    try:
        candidate = _canonical_json(artifact)
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ArchiveInputError("verified artifact must be canonical UTF-8 JSON") from exc
    target = archive_root / f"{artifact['artifact_id']}.json"
    created_report = _render_report(artifact, "CREATED", target)
    _render_report(artifact, "UNCHANGED", target)
    if target.exists():
        _reject_reparse(target)
        return _existing_result(target, candidate, artifact)
    try:
        archive_root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ArchiveIOError("cannot create archive root") from exc
    _reject_reparse(archive_root)
    root_identity = _identity_snapshot(archive_root)
    handle: IO[bytes] | None = None
    stage: Path | None = None
    try:
        handle, stage = _open_stage(archive_root)
        handle.write(candidate)
        handle.flush()
        os.fsync(handle.fileno())
        handle.close()
        handle = None
        _reject_reparse(stage)
        _reject_reparse(archive_root)
        _identity_snapshot(stage)
        if _identity_snapshot(archive_root) != root_identity:
            raise ArchiveIOError("archive parent identity changed before publication")
        try:
            _rename_no_replace(stage, target)
            stage = None
        except FileExistsError:
            return _existing_result(target, candidate, artifact)
        except OSError as exc:
            raise ArchiveIOError("rename-only publication failed") from exc
        _reject_reparse(target)
        target_identity = _identity_snapshot(target)
        observed = _readback(target)
        if _identity_snapshot(target) != target_identity:
            raise ArchiveIOError("published artifact identity changed during readback")
        if observed != candidate or hashlib.sha256(observed).digest() != hashlib.sha256(candidate).digest():
            raise ArchiveIOError("published artifact readback mismatch")
        return ArchiveResult(
            "CREATED",
            target,
            artifact["artifact_id"],
            artifact["payload_digest"],
            created_report,
        )
    except ArchiveIOError:
        raise
    except OSError as exc:
        raise ArchiveIOError("archive staging I/O failed") from exc
    finally:
        if handle is not None:
            try:
                handle.close()
            except OSError:
                pass
        if stage is not None:
            try:
                _reject_reparse(stage)
                if stage.exists() and stage.parent == archive_root:
                    stage.unlink()
            except (OSError, ArchiveInputError):
                pass


__all__ = [
    "ArchiveResult",
    "ArchiveInputError",
    "ArchiveConflictError",
    "ArchiveIOError",
    "archive_verified_artifact",
]
