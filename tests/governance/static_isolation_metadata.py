from __future__ import annotations

import json
from pathlib import Path
from typing import Final

ACTIVE_ENTRYPOINT_KEYS: Final = (
    "active_feedback_entrypoints",
    "active_report_entrypoints",
)

type JsonNode = str | int | float | bool | None | list[JsonNode] | dict[str, JsonNode]


def active_entrypoint_paths(root: Path) -> tuple[Path, ...]:
    source = root / "META" / "project-state.json"
    state: JsonNode = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(state, dict):
        return ()
    return tuple(
        root / entrypoint
        for key in ACTIVE_ENTRYPOINT_KEYS
        for entrypoint in _string_sequence(state.get(key))
    )


def _string_sequence(value: JsonNode) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))
