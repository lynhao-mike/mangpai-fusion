from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import yaml

from engine.evaluation.models import BlindTask

_SUPPORTED_SCORING_METHODS = {
    "binary_probability",
    "multiclass_probability",
    "ordinal",
    "time_window",
    "portrait_agreement",
}
_SCHEMA_VERSION = "school-capability-tasks/v1"


def load_task_catalog(path: Path) -> list[BlindTask]:
    raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema_version") != _SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {_SCHEMA_VERSION}")
    items = raw.get("tasks")
    if not isinstance(items, list):
        raise ValueError("tasks must be a list")

    tasks: list[BlindTask] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("each task must be a mapping")
        domain = item.get("domain")
        if not isinstance(domain, str) or not domain.strip():
            raise ValueError("domain must be a non-empty string")
        scoring_method = item.get("scoring_method")
        if scoring_method not in _SUPPORTED_SCORING_METHODS:
            raise ValueError(f"unsupported scoring_method: {scoring_method}")
        if not isinstance(item.get("label_schema"), dict):
            raise ValueError("label_schema must be a mapping")
        task = BlindTask.from_dict(item)
        if task.task_id in seen:
            raise ValueError(f"duplicate task_id: {task.task_id}")
        if not task.domain.strip():
            raise ValueError(f"domain is required for {task.task_id}")
        if task.scoring_method not in _SUPPORTED_SCORING_METHODS:
            raise ValueError(f"unsupported scoring_method: {task.scoring_method}")
        if task.quantifiable and not task.label_schema:
            raise ValueError(f"label_schema is required for quantifiable task {task.task_id}")
        seen.add(task.task_id)
        tasks.append(task)
    return tasks


def task_by_id(tasks: Sequence[BlindTask]) -> dict[str, BlindTask]:
    indexed: dict[str, BlindTask] = {}
    for task in tasks:
        if task.task_id in indexed:
            raise ValueError(f"duplicate task_id: {task.task_id}")
        indexed[task.task_id] = task
    return indexed
