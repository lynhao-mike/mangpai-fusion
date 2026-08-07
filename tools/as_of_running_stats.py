"""递归聚合案例库中的 as-of 反馈裁决统计。

本工具只读取 ``asof-feedback-verdict.json``。旧 schema 优先使用
``separate_score_units`` 的既有汇总；缺少该字段的新 schema 则从职业基本面、
阶段方向和日期事件裁决重算。工具不会修改任何案例文件。
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping

__all__ = ("RunningStats", "append_stats_snapshot", "compute_running_stats")

_CENTER_HIT = "CENTER_HIT"
_MISS_VERDICTS = frozenset({"MISS", "TAXONOMY_GAP"})
_EVALUABLE_VERDICTS = frozenset({_CENTER_HIT, "ALTERNATIVE_HIT", *_MISS_VERDICTS})


@dataclass(frozen=True, slots=True)
class RunningStats:
    career_evaluable: int
    career_center_hits: int
    career_misses: int
    career_abstains: int
    phase_evaluable: int
    phase_center_hits: int
    phase_misses: int
    phase_abstains: int
    event_evaluable: int
    event_center_hits: int
    event_misses: int
    event_abstains: int
    case_count: int
    case_ids: tuple[str, ...]
    as_of: str


def append_stats_snapshot(stats: RunningStats, history_path: Path) -> None:
    """把当前统计快照追加到 JSONL 时间线文件（如不存在则创建）。"""

    snapshot = asdict(stats)
    snapshot.pop("case_ids")
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")) + "\n")


def _count_adjudications(items: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    verdicts = [str(item.get("verdict", "")) for item in items]
    return {
        "evaluable": sum(verdict in _EVALUABLE_VERDICTS for verdict in verdicts),
        "center_hits": verdicts.count(_CENTER_HIT),
        "misses": sum(verdict in _MISS_VERDICTS for verdict in verdicts),
        "abstains": verdicts.count("ABSTAIN"),
    }


def _mapping_items(value: Any) -> tuple[Mapping[str, Any], ...]:
    if isinstance(value, list):
        return tuple(item for item in value if isinstance(item, Mapping))
    if isinstance(value, Mapping):
        return (value,)
    return ()


def _recompute_units(payload: Mapping[str, Any]) -> dict[str, dict[str, int]]:
    career_items = _mapping_items(payload.get("career_baseline_adjudication"))
    if not career_items:
        career_items = _mapping_items(payload.get("primary_landing_adjudication"))

    return {
        "career_basic_state": _count_adjudications(career_items),
        "broad_phase_direction": _count_adjudications(
            _mapping_items(payload.get("phase_adjudications"))
        ),
        "dated_event_precision": _count_adjudications(
            _mapping_items(payload.get("event_adjudications"))
        ),
    }


def _score_units(payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    stored = payload.get("separate_score_units")
    if isinstance(stored, Mapping):
        required = (
            "career_basic_state",
            "broad_phase_direction",
            "dated_event_precision",
        )
        if all(isinstance(stored.get(name), Mapping) for name in required):
            return {name: stored[name] for name in required}
    return _recompute_units(payload)


def _integer(unit: Mapping[str, Any], field: str, source: Path) -> int:
    value = unit.get(field, 0)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{source}: {field} must be a non-negative integer")
    return value


def compute_running_stats(cases_root: Path) -> RunningStats:
    """扫描 cases_root 下所有 asof-feedback-verdict.json，聚合三类评分单位计数。"""

    totals = {
        domain: {field: 0 for field in ("evaluable", "center_hits", "misses", "abstains")}
        for domain in (
            "career_basic_state",
            "broad_phase_direction",
            "dated_event_precision",
        )
    }
    case_ids: list[str] = []

    for verdict_path in sorted(cases_root.rglob("asof-feedback-verdict.json")):
        with verdict_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, Mapping):
            raise ValueError(f"{verdict_path}: top-level JSON value must be an object")

        case_id = payload.get("case_id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"{verdict_path}: case_id must be a non-empty string")
        case_ids.append(case_id.strip())

        units = _score_units(payload)
        for domain, total in totals.items():
            unit = units[domain]
            for field in total:
                total[field] += _integer(unit, field, verdict_path)

    if len(case_ids) != len(set(case_ids)):
        raise ValueError("duplicate case_id found in asof-feedback-verdict.json files")

    career = totals["career_basic_state"]
    phase = totals["broad_phase_direction"]
    event = totals["dated_event_precision"]
    return RunningStats(
        career_evaluable=career["evaluable"],
        career_center_hits=career["center_hits"],
        career_misses=career["misses"],
        career_abstains=career["abstains"],
        phase_evaluable=phase["evaluable"],
        phase_center_hits=phase["center_hits"],
        phase_misses=phase["misses"],
        phase_abstains=phase["abstains"],
        event_evaluable=event["evaluable"],
        event_center_hits=event["center_hits"],
        event_misses=event["misses"],
        event_abstains=event["abstains"],
        case_count=len(case_ids),
        case_ids=tuple(sorted(case_ids)),
        as_of=date.today().isoformat(),
    )
