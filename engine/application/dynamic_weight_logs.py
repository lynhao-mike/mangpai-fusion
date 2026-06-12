"""Minimal auditable JSONL logs for dynamic feedback weighting.

This module centralizes append/read/rotation behavior for production-visible
feedback-weight logs while staying stdlib-only and backward compatible with the
existing JSONL files under engine/logs/.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "dynamic-weight-log/v0.1"
DEFAULT_MAX_BYTES = 5 * 1024 * 1024
DEFAULT_BACKUP_COUNT = 3

LOG_SCHEMAS: dict[str, dict[str, Any]] = {
    "weight_change": {
        "required": [
            "schema_version",
            "ts",
            "event_type",
            "domain",
            "expert_system",
            "old_weight",
            "new_weight",
            "source",
        ],
        "event_type": "weight_change",
    },
    "expert_domain_feedback": {
        "required": [
            "schema_version",
            "ts",
            "event_type",
            "case_id",
            "statement_id",
            "domain",
            "expert_system",
            "verdict",
        ],
        "event_type": "expert_domain_feedback",
    },
    "adjudication_accuracy": {
        "required": [
            "schema_version",
            "ts",
            "event_type",
            "case_id",
            "statement_id",
            "adjudication_id",
            "domain",
            "verdict",
        ],
        "event_type": "adjudication_accuracy",
    },
}


def append_jsonl(
    path: str | Path,
    rows: Iterable[dict[str, Any]],
    *,
    event_type: str | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> int:
    """Append JSONL rows with schema/event metadata and size-based rotation."""

    normalized_rows = [normalize_event(row, event_type=event_type) for row in rows]
    if not normalized_rows:
        return 0
    target = Path(path)
    rotate_if_needed(target, max_bytes=max_bytes, backup_count=backup_count)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        for row in normalized_rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return len(normalized_rows)


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load valid JSON object lines; malformed/blank lines are ignored."""

    target = Path(path)
    if not target.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def normalize_event(row: dict[str, Any], *, event_type: str | None = None) -> dict[str, Any]:
    """Return a backward-compatible event carrying schema_version/event_type."""

    normalized = dict(row)
    if event_type and not normalized.get("event_type"):
        normalized["event_type"] = event_type
    normalized.setdefault("schema_version", SCHEMA_VERSION)
    return normalized


def rotate_if_needed(
    path: str | Path,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
) -> None:
    """Rotate path to .1/.2/... when it reaches max_bytes.

    Rotation is intentionally simple and local: no daemon, no compression, and
    no dependency on OS logrotate. Empty or missing files are not rotated.
    """

    target = Path(path)
    if max_bytes <= 0 or backup_count <= 0:
        return
    if not target.exists() or target.stat().st_size < max_bytes:
        return
    for idx in range(backup_count - 1, 0, -1):
        src = target.with_name(f"{target.name}.{idx}")
        dst = target.with_name(f"{target.name}.{idx + 1}")
        if src.exists():
            if dst.exists():
                dst.unlink()
            shutil.move(str(src), str(dst))
    first = target.with_name(f"{target.name}.1")
    if first.exists():
        first.unlink()
    shutil.move(str(target), str(first))


def ensure_log_files(paths: Iterable[str | Path]) -> None:
    """Create parent directories and empty JSONL files if absent."""

    for raw_path in paths:
        path = Path(raw_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
