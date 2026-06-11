from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConclusionDiff:
    case_id: str
    before_count: int
    after_count: int
    added: list[dict[str, Any]]
    removed: list[dict[str, Any]]
    changed: list[dict[str, Any]]
    unchanged: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "before_count": self.before_count,
            "after_count": self.after_count,
            "added": self.added,
            "removed": self.removed,
            "changed": self.changed,
            "unchanged": self.unchanged,
        }


def build_conclusion_diff(
    *,
    case_id: str,
    before_output: dict[str, Any] | None,
    after_output: dict[str, Any],
) -> ConclusionDiff:
    before_items = _conclusion_map(before_output or {})
    after_items = _conclusion_map(after_output)

    added: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    changed: list[dict[str, Any]] = []
    unchanged: list[dict[str, Any]] = []

    for key, after in sorted(after_items.items()):
        before = before_items.get(key)
        if before is None:
            added.append(after)
            continue
        if _comparable_conclusion(before) == _comparable_conclusion(after):
            unchanged.append(after)
        else:
            changed.append({"key": key, "before": before, "after": after})

    for key, before in sorted(before_items.items()):
        if key not in after_items:
            removed.append(before)

    return ConclusionDiff(
        case_id=case_id,
        before_count=len(before_items),
        after_count=len(after_items),
        added=added,
        removed=removed,
        changed=changed,
        unchanged=unchanged,
    )


def _conclusion_map(output: dict[str, Any]) -> dict[str, dict[str, Any]]:
    conclusions = output.get("final_conclusions") or []
    mapped: dict[str, dict[str, Any]] = {}
    if not isinstance(conclusions, list):
        return mapped
    for index, item in enumerate(conclusions):
        if not isinstance(item, dict):
            continue
        key = _conclusion_key(item, index)
        mapped[key] = dict(item)
    return mapped


def _conclusion_key(item: dict[str, Any], index: int) -> str:
    trace_ids = item.get("trace_ids")
    if isinstance(trace_ids, list) and trace_ids:
        return "trace:" + ",".join(str(v) for v in trace_ids)
    statement = str(item.get("statement") or item.get("text") or "").strip()
    if statement:
        return "statement:" + statement
    return f"index:{index}"


def _comparable_conclusion(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "statement": item.get("statement") or item.get("text"),
        "confidence": item.get("confidence"),
        "school": item.get("school") or item.get("schools"),
        "trace_ids": item.get("trace_ids") or [],
    }
