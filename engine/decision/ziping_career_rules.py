from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from engine.evaluation.freeze import canonical_json

SCHEMA_VERSION = "ziping-career-structure-rules/v1"
TASK_RULE_ID = "ZIPING-CAREER-OFFICIAL-PATH-DISRUPTION-V1"
DEFAULT_RULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "theory"
    / "production"
    / "ziping-career-structure-rules-v1.yaml"
)
_CATALOG_PATH = Path(__file__).resolve().parents[2] / "theory" / "ziping" / "index.yaml"
_ALLOWED_OPERATORS = {"eq", "ne", "gte", "lte", "in", "not_in", "truthy", "falsy"}
_EXPECTED_SOURCE_IDS = ("ZP-PROD-20260622-011", "ZP-PROD-20260622-012")
_TOP_LEVEL_FIELDS = {
    "schema_version",
    "school_id",
    "task_id",
    "domain",
    "target_layer",
    "task_rule_id",
    "claim_type",
    "required_facts",
    "required_gates",
    "conditions",
    "exclusions",
    "counter_conditions",
    "conclusion_template",
    "confidence_basis",
    "falsifier",
    "source_anchors",
    "lifecycle_state",
    "base_confidence",
}
_FIXED_FIELDS = {
    "schema_version": SCHEMA_VERSION,
    "school_id": "ziping",
    "task_id": "career.role_change",
    "domain": "事业",
    "target_layer": "L3",
    "task_rule_id": TASK_RULE_ID,
    "claim_type": "structure_claim",
    "lifecycle_state": "staged",
}


class MappingSchemaError(ValueError):
    pass


@dataclass(frozen=True)
class RuleCondition:
    fact: str
    op: str
    value: object


@dataclass(frozen=True)
class SourceAnchor:
    production_rule_id: str
    path: str
    line: int
    excerpt: str
    supports: str


@dataclass(frozen=True)
class ZipingCareerRuleMapping:
    schema_version: str
    school_id: str
    task_id: str
    domain: str
    target_layer: str
    task_rule_id: str
    claim_type: str
    required_facts: tuple[str, ...]
    required_gates: tuple[str, ...]
    conditions: tuple[RuleCondition, ...]
    exclusions: tuple[RuleCondition, ...]
    counter_conditions: tuple[RuleCondition, ...]
    conclusion_template: str
    confidence_basis: str
    falsifier: str
    source_anchors: tuple[SourceAnchor, ...]
    lifecycle_state: str
    base_confidence: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "school_id": self.school_id,
            "task_id": self.task_id,
            "domain": self.domain,
            "target_layer": self.target_layer,
            "task_rule_id": self.task_rule_id,
            "claim_type": self.claim_type,
            "required_facts": list(self.required_facts),
            "required_gates": list(self.required_gates),
            "conditions": [item.__dict__ for item in self.conditions],
            "exclusions": [item.__dict__ for item in self.exclusions],
            "counter_conditions": [item.__dict__ for item in self.counter_conditions],
            "conclusion_template": self.conclusion_template,
            "confidence_basis": self.confidence_basis,
            "falsifier": self.falsifier,
            "source_anchors": [item.__dict__ for item in self.source_anchors],
            "lifecycle_state": self.lifecycle_state,
            "base_confidence": self.base_confidence,
        }


def mapping_digest(mapping: ZipingCareerRuleMapping) -> str:
    data = mapping.to_dict()
    data["source_anchors"] = sorted(
        data["source_anchors"], key=lambda item: item["production_rule_id"]
    )
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def _non_empty_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MappingSchemaError(f"{field} must be a non-empty string")
    return value


def _string_tuple(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise MappingSchemaError(f"{field} must be a non-empty list")
    result = tuple(_non_empty_string(item, field) for item in value)
    if len(set(result)) != len(result):
        raise MappingSchemaError(f"{field} contains duplicates")
    return result


def _conditions(value: object, field: str) -> tuple[RuleCondition, ...]:
    if not isinstance(value, list):
        raise MappingSchemaError(f"{field} must be a list")
    result = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"fact", "op", "value"}:
            raise MappingSchemaError(f"{field} condition has invalid fields")
        fact = _non_empty_string(item["fact"], f"{field}.fact")
        op = _non_empty_string(item["op"], f"{field}.operator")
        if op not in _ALLOWED_OPERATORS:
            raise MappingSchemaError(f"unknown operator: {op}")
        result.append(RuleCondition(fact=fact, op=op, value=item["value"]))
    return tuple(result)


def _source_anchors(value: object) -> tuple[SourceAnchor, ...]:
    if not isinstance(value, list) or not value:
        raise MappingSchemaError("source_anchors must be a non-empty list")
    catalog = yaml.safe_load(_CATALOG_PATH.read_text(encoding="utf-8"))
    indexed = {item["id"]: item for item in catalog["rules"]}
    anchors = []
    for item in value:
        expected = {"production_rule_id", "path", "line", "excerpt", "supports"}
        if not isinstance(item, dict) or set(item) != expected:
            raise MappingSchemaError("source_anchors entry has invalid fields")
        rule_id = _non_empty_string(item["production_rule_id"], "production_rule_id")
        path = _non_empty_string(item["path"], "source path")
        excerpt = _non_empty_string(item["excerpt"], "source excerpt")
        supports = _non_empty_string(item["supports"], "source supports")
        line = item["line"]
        if not isinstance(line, int) or isinstance(line, bool) or line < 1:
            raise MappingSchemaError("source line must be a positive integer")
        source_file = Path(__file__).resolve().parents[2] / path
        if not source_file.is_file():
            raise MappingSchemaError(f"source file does not exist: {path}")
        production = indexed.get(rule_id)
        if production is None:
            raise MappingSchemaError(f"source production rule does not exist: {rule_id}")
        source = production.get("source", {})
        if source.get("path") != path or int(source.get("line", 0)) != line:
            raise MappingSchemaError(f"source anchor does not resolve: {rule_id}")
        if excerpt not in str(source.get("excerpt", "")):
            raise MappingSchemaError(f"source excerpt does not resolve: {rule_id}")
        anchors.append(SourceAnchor(rule_id, path, line, excerpt, supports))
    ids = tuple(anchor.production_rule_id for anchor in anchors)
    if len(set(ids)) != len(ids) or set(ids) != set(_EXPECTED_SOURCE_IDS):
        raise MappingSchemaError("source_anchors must contain the exact production rule IDs")
    return tuple(sorted(anchors, key=lambda anchor: anchor.production_rule_id))


def load_ziping_career_rule_mapping(
    path: Path = DEFAULT_RULE_PATH,
) -> ZipingCareerRuleMapping:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise MappingSchemaError("mapping must be an object")
    fields = set(document)
    if fields != _TOP_LEVEL_FIELDS:
        unknown = fields - _TOP_LEVEL_FIELDS
        missing = _TOP_LEVEL_FIELDS - fields
        if unknown:
            raise MappingSchemaError(f"unknown top-level fields: {sorted(unknown)}")
        raise MappingSchemaError(f"missing top-level fields: {sorted(missing)}")
    for field, expected in _FIXED_FIELDS.items():
        if document[field] != expected:
            raise MappingSchemaError(f"{field} must be {expected!r}")
    base_confidence = document["base_confidence"]
    if (
        not isinstance(base_confidence, (int, float))
        or isinstance(base_confidence, bool)
        or not 0 <= base_confidence <= 1
    ):
        raise MappingSchemaError("base_confidence must be between 0 and 1")
    return ZipingCareerRuleMapping(
        schema_version=document["schema_version"],
        school_id=document["school_id"],
        task_id=document["task_id"],
        domain=document["domain"],
        target_layer=document["target_layer"],
        task_rule_id=document["task_rule_id"],
        claim_type=document["claim_type"],
        required_facts=_string_tuple(document["required_facts"], "required_facts"),
        required_gates=_string_tuple(document["required_gates"], "required_gates"),
        conditions=_conditions(document["conditions"], "conditions"),
        exclusions=_conditions(document["exclusions"], "exclusions"),
        counter_conditions=_conditions(document["counter_conditions"], "counter_conditions"),
        conclusion_template=_non_empty_string(document["conclusion_template"], "conclusion_template"),
        confidence_basis=_non_empty_string(document["confidence_basis"], "confidence_basis"),
        falsifier=_non_empty_string(document["falsifier"], "falsifier"),
        source_anchors=_source_anchors(document["source_anchors"]),
        lifecycle_state=document["lifecycle_state"],
        base_confidence=float(base_confidence),
    )
