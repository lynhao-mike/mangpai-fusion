from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_ALLOWED_RELATIONS = frozenset({"冲", "刑", "穿", "合", "伏吟"})
_DEFAULT = Path("theory/production/ren-career-timing-rules-v1.yaml")
_SCHEMA_VERSION = "ren-career-timing-rules/v1"
_TOP_LEVEL_FIELDS = frozenset({"schema_version", "rules"})
_RULE_FIELDS = frozenset(
    {"rule_id", "relation", "priority", "source_path", "source_anchor", "confidence"}
)
_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class RenTimingRule:
    rule_id: str
    relation: str
    priority: int
    source_path: str
    source_anchor: str
    confidence: float


def _require_nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"invalid {field}")
    return value


def _resolve_source_path(source_path: str) -> Path:
    candidate = Path(source_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"invalid source path: {source_path}")
    resolved = (_REPOSITORY_ROOT / candidate).resolve()
    try:
        resolved.relative_to(_REPOSITORY_ROOT)
    except ValueError as exc:
        raise ValueError(f"invalid source path: {source_path}") from exc
    if not resolved.is_file():
        raise ValueError(f"missing source path: {source_path}")
    return resolved


def _load_source_anchors(source: Path) -> set[str]:
    raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("rules"), list):
        raise ValueError(f"source path has no parseable rules: {source}")
    anchors: set[str] = set()
    for item in raw["rules"]:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            anchors.add(item["id"])
    return anchors


def load_ren_timing_rules(path: Path | None = None) -> tuple[RenTimingRule, ...]:
    registry_path = path or _DEFAULT
    if not registry_path.is_absolute():
        registry_path = _REPOSITORY_ROOT / registry_path
    raw = yaml.safe_load(registry_path.read_text(encoding="utf-8"))

    if not isinstance(raw, dict) or set(raw) != _TOP_LEVEL_FIELDS:
        raise ValueError("invalid ren timing registry top-level fields")
    if raw["schema_version"] != _SCHEMA_VERSION:
        raise ValueError("invalid ren timing registry schema_version")
    if not isinstance(raw["rules"], list):
        raise ValueError("ren timing registry rules must be a list")

    seen_ids: set[str] = set()
    seen_relations: set[str] = set()
    source_anchors: dict[Path, set[str]] = {}
    rules: list[RenTimingRule] = []

    for item in raw["rules"]:
        if not isinstance(item, dict) or set(item) != _RULE_FIELDS:
            raise ValueError("invalid ren timing rule fields")

        rule_id = _require_nonempty_string(item["rule_id"], "rule_id")
        relation = _require_nonempty_string(item["relation"], "relation")
        source_path = _require_nonempty_string(item["source_path"], "source_path")
        source_anchor = _require_nonempty_string(item["source_anchor"], "source_anchor")

        if relation not in _ALLOWED_RELATIONS:
            raise ValueError(f"unsupported relation: {relation}")
        if rule_id in seen_ids:
            raise ValueError(f"duplicate rule_id: {rule_id}")
        if relation in seen_relations:
            raise ValueError(f"duplicate relation: {relation}")

        priority = item["priority"]
        if type(priority) is not int or priority <= 0:
            raise ValueError(f"invalid priority: {priority!r}")
        confidence = item["confidence"]
        if type(confidence) not in (int, float):
            raise ValueError(f"invalid confidence: {confidence!r}")
        confidence = float(confidence)
        if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            raise ValueError(f"invalid confidence: {confidence!r}")

        resolved_source = _resolve_source_path(source_path)
        anchors = source_anchors.setdefault(resolved_source, _load_source_anchors(resolved_source))
        if source_anchor not in anchors:
            raise ValueError(f"unresolvable source anchor: {source_anchor}")

        seen_ids.add(rule_id)
        seen_relations.add(relation)
        rules.append(
            RenTimingRule(
                rule_id=rule_id,
                relation=relation,
                priority=priority,
                source_path=source_path,
                source_anchor=source_anchor,
                confidence=confidence,
            )
        )

    return tuple(sorted(rules, key=lambda rule: (rule.priority, rule.rule_id)))
