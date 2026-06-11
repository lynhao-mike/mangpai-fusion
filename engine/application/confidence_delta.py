from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConfidenceDelta:
    case_id: str
    overall: dict[str, Any]
    conclusions: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "overall": self.overall,
            "conclusions": self.conclusions,
        }


def build_confidence_delta(
    *,
    case_id: str,
    before_output: dict[str, Any] | None,
    after_output: dict[str, Any],
) -> ConfidenceDelta:
    before_output = before_output or {}
    before_conclusions = _conclusion_map(before_output)
    after_conclusions = _conclusion_map(after_output)

    rows: list[dict[str, Any]] = []
    for key, after in sorted(after_conclusions.items()):
        before = before_conclusions.get(key, {})
        rows.append(
            {
                "key": key,
                "before": _confidence_value(before.get("confidence")),
                "after": _confidence_value(after.get("confidence")),
                "delta_percent": _delta_percent(before.get("confidence"), after.get("confidence")),
            }
        )

    return ConfidenceDelta(
        case_id=case_id,
        overall={
            "before": _confidence_value(before_output.get("overall_confidence")),
            "after": _confidence_value(after_output.get("overall_confidence")),
            "delta_percent": _delta_percent(
                before_output.get("overall_confidence"),
                after_output.get("overall_confidence"),
            ),
        },
        conclusions=rows,
    )


def _conclusion_map(output: dict[str, Any]) -> dict[str, dict[str, Any]]:
    conclusions = output.get("final_conclusions") or []
    mapped: dict[str, dict[str, Any]] = {}
    if not isinstance(conclusions, list):
        return mapped
    for index, item in enumerate(conclusions):
        if not isinstance(item, dict):
            continue
        trace_ids = item.get("trace_ids")
        if isinstance(trace_ids, list) and trace_ids:
            key = "trace:" + ",".join(str(v) for v in trace_ids)
        else:
            statement = str(item.get("statement") or item.get("text") or "").strip()
            key = "statement:" + statement if statement else f"index:{index}"
        mapped[key] = item
    return mapped


def _confidence_value(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return {
            "star": value.get("star"),
            "percent": value.get("percent"),
            "posterior": value.get("posterior"),
            "reason": value.get("reason"),
        }
    if hasattr(value, "to_dict"):
        return _confidence_value(value.to_dict())
    return {"raw": value}


def _delta_percent(before: Any, after: Any) -> int | float | None:
    before_value = _numeric_percent(before)
    after_value = _numeric_percent(after)
    if before_value is None or after_value is None:
        return None
    return after_value - before_value


def _numeric_percent(value: Any) -> int | float | None:
    if value is None:
        return None
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    if isinstance(value, dict):
        raw = value.get("percent")
        if isinstance(raw, (int, float)):
            return raw
    return None
