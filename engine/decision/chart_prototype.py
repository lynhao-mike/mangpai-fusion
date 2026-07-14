"""由 cfv-v1 特征向量确定性分类命盘原型。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

from engine.features.types import ChartFeatureVector

_DEFAULT_REGISTRY = Path(__file__).resolve().parents[2] / "mapping" / "chart-prototype-registry-v1.yaml"


@dataclass(frozen=True)
class PrototypeDefinition:
    prototype_id: str
    label: str
    required_features: Mapping[str, Mapping[str, Any]]
    excluded_features: Mapping[str, Mapping[str, Any]]
    priority: int
    notes: str = ""


@dataclass(frozen=True)
class PrototypeAssignment:
    prototype_id: str
    confidence: float
    matched_conditions: tuple[str, ...]
    alternative_ids: tuple[str, ...] = ()


def load_prototype_registry(path: str | Path = _DEFAULT_REGISTRY) -> tuple[PrototypeDefinition, ...]:
    source = Path(path)
    raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema_version") != "chart-prototype-registry/v1":
        raise ValueError("invalid chart prototype registry schema_version")
    rows = raw.get("prototypes")
    if not isinstance(rows, list) or not 10 <= len(rows) <= 20:
        raise ValueError("chart prototype registry must contain 10-20 prototypes")
    definitions: list[PrototypeDefinition] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("prototype definition must be an object")
        try:
            definition = PrototypeDefinition(
                prototype_id=str(row["prototype_id"]),
                label=str(row["label"]),
                required_features=dict(row["required_features"]),
                excluded_features=dict(row.get("excluded_features", {})),
                priority=int(row["priority"]),
                notes=str(row.get("notes", "")),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid prototype definition: {exc}") from exc
        if not definition.prototype_id.startswith("prototype-") or not definition.required_features:
            raise ValueError("prototype_id and required_features are required")
        if definition.prototype_id in seen:
            raise ValueError(f"duplicate prototype_id: {definition.prototype_id}")
        seen.add(definition.prototype_id)
        definitions.append(definition)
    return tuple(sorted(definitions, key=lambda item: (item.priority, item.prototype_id)))


def _matches_operator(value: Any, operator: str, expected: Any) -> bool:
    if operator == "eq":
        return value == expected
    if operator == "gte":
        return float(value) >= float(expected)
    if operator == "lte":
        return float(value) <= float(expected)
    if operator == "length_gte":
        return len(value) >= int(expected)
    if operator == "outside":
        low, high = expected
        return float(value) < float(low) or float(value) > float(high)
    raise ValueError(f"unsupported prototype condition operator: {operator}")


def _condition_matches(vector: ChartFeatureVector, feature: str, condition: Mapping[str, Any]) -> bool:
    if not hasattr(vector, feature):
        raise ValueError(f"unknown ChartFeatureVector field in prototype registry: {feature}")
    if len(condition) != 1:
        raise ValueError(f"prototype condition for {feature} must have exactly one operator")
    operator, expected = next(iter(condition.items()))
    return _matches_operator(getattr(vector, feature), operator, expected)


def _definition_matches(vector: ChartFeatureVector, definition: PrototypeDefinition) -> tuple[bool, tuple[str, ...]]:
    matched: list[str] = []
    for feature, condition in definition.required_features.items():
        if not _condition_matches(vector, feature, condition):
            return False, ()
        operator, expected = next(iter(condition.items()))
        matched.append(f"{feature}:{operator}:{expected}")
    for feature, condition in definition.excluded_features.items():
        if _condition_matches(vector, feature, condition):
            return False, ()
    return True, tuple(matched)


def classify_prototype(
    feature_vector: ChartFeatureVector,
    *,
    registry_path: str | Path = _DEFAULT_REGISTRY,
) -> PrototypeAssignment:
    """返回主原型、边界备选和可审计的命中条件。"""
    if not isinstance(feature_vector, ChartFeatureVector):
        raise TypeError("feature_vector must be ChartFeatureVector")
    matches: list[tuple[PrototypeDefinition, tuple[str, ...]]] = []
    for definition in load_prototype_registry(registry_path):
        matched, conditions = _definition_matches(feature_vector, definition)
        if matched:
            matches.append((definition, conditions))
    if not matches:
        return PrototypeAssignment("prototype-unclassified", 0.0, (), ())
    winner, conditions = matches[0]
    alternatives = tuple(definition.prototype_id for definition, _ in matches[1:])
    confidence = 1.0 if not alternatives else round(1.0 / (1.0 + 0.35 * len(alternatives)), 3)
    return PrototypeAssignment(winner.prototype_id, confidence, conditions, alternatives)
