from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


_CASE_ID_PATTERN = re.compile(
    r"P-GO-\d{4}-\d{3}-[乾坤]-[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]{8}"
)
_ARTIFACT_KIND_PATTERN = re.compile(r"[a-z][a-z0-9-]*")
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_REVISION_FIELDS = frozenset(
    {"supersedes", "supersedes_sha256", "reason", "approved_by"}
)


@dataclass(frozen=True)
class ArtifactRef:
    artifact_path: str
    artifact_sha256: str


def canonical_artifact_sha256(payload: Mapping[str, Any]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "artifact_sha256"}
    encoded = json.dumps(
        unsigned,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def single_case_artifact_path(
    root: Path,
    case_id: str,
    artifact_kind: str,
    version: int,
) -> Path:
    if _CASE_ID_PATTERN.fullmatch(case_id) is None:
        raise ValueError("invalid prospective case_id")
    if (
        isinstance(version, bool)
        or not isinstance(version, int)
        or version < 1
        or _ARTIFACT_KIND_PATTERN.fullmatch(artifact_kind) is None
    ):
        raise ValueError("invalid artifact identity")
    return Path(root) / case_id / f"{case_id}--{artifact_kind}--v{version:03d}.json"


def _document_bytes(document: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")


def publish_new_json(
    path: Path,
    payload: Mapping[str, Any],
    *,
    dry_run: bool,
) -> ArtifactRef:
    path = Path(path)
    digest = canonical_artifact_sha256(payload)
    reference = ArtifactRef(path.as_posix(), digest)
    if dry_run:
        return reference
    if path.exists() or path.is_symlink():
        raise ValueError(f"output already exists: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        document = {**payload, "artifact_sha256": digest}
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(_document_bytes(document))
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary_path, path)
        except FileExistsError as exc:
            raise ValueError(f"output already exists: {path}") from exc
    finally:
        temporary_path.unlink(missing_ok=True)
    return reference


def validate_parent_ref(ref: ArtifactRef) -> dict[str, Any]:
    path = Path(ref.artifact_path)
    if path.is_symlink():
        raise ValueError(f"parent artifact must not be a symlink: {path}")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"parent artifact is unreadable: {path}") from exc
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"parent artifact is not valid UTF-8 JSON: {path}") from exc
    if not isinstance(document, dict):
        raise ValueError("parent artifact must be a JSON object")
    if raw != _document_bytes(document):
        raise ValueError("parent artifact byte drift detected")

    stored_digest = document.get("artifact_sha256")
    if stored_digest != ref.artifact_sha256:
        raise ValueError("parent stored digest does not match reference")
    recomputed_digest = canonical_artifact_sha256(document)
    if recomputed_digest != stored_digest:
        raise ValueError("parent canonical digest mismatch")
    return document


def validate_revision_metadata(payload: Mapping[str, Any], version: int) -> None:
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise ValueError("invalid artifact version")

    present = _REVISION_FIELDS.intersection(payload)
    if version == 1:
        if present:
            raise ValueError("v001 must not contain revision metadata")
        return

    missing = _REVISION_FIELDS.difference(payload)
    if missing:
        raise ValueError(
            "revision metadata missing required field(s): " + ", ".join(sorted(missing))
        )
    for field in ("supersedes", "reason", "approved_by"):
        value = payload[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"revision metadata {field} must be a non-empty string")
    digest = payload["supersedes_sha256"]
    if not isinstance(digest, str) or _SHA256_PATTERN.fullmatch(digest) is None:
        raise ValueError("revision metadata supersedes_sha256 must be a lowercase SHA-256")
