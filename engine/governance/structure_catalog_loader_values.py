from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Never

from yaml import MappingNode, Node, ScalarNode, SequenceNode

from engine.governance.structure_catalog_types import (
    ImplementationStatus,
    SourceStatus,
    StructureCatalogContractError,
    StructureConditionType,
    StructureFamily,
    StructureRole,
)
from engine.predicates.ten_god_structure_types import TenGodStructureKind


def reject_structure_catalog(
    issue_code: str,
    field_path: str,
    diagnostic: str,
) -> Never:
    raise StructureCatalogContractError(issue_code, field_path, diagnostic)


def node_string(node: Node, field_path: str) -> str:
    if (
        not isinstance(node, ScalarNode)
        or node.tag != "tag:yaml.org,2002:str"
        or not node.value.strip()
    ):
        reject_structure_catalog(
            "STRUCTURE.YAML_STRING", field_path, "must be a nonempty string"
        )
    return node.value


def node_optional_string(node: Node, field_path: str) -> str | None:
    if isinstance(node, ScalarNode) and node.tag == "tag:yaml.org,2002:null":
        return None
    return node_string(node, field_path)


def node_fields(
    node: Node, field_path: str, expected: frozenset[str]
) -> Mapping[str, Node]:
    if not isinstance(node, MappingNode):
        reject_structure_catalog(
            "STRUCTURE.YAML_MAPPING", field_path, "must be a mapping"
        )
    fields: dict[str, Node] = {}
    for key_node, value_node in node.value:
        key = node_string(key_node, f"{field_path}.key")
        if key in fields:
            reject_structure_catalog(
                "STRUCTURE.YAML_DUPLICATE_FIELD", field_path, "duplicate field"
            )
        fields[key] = value_node
    if frozenset(fields) != expected:
        reject_structure_catalog(
            "STRUCTURE.YAML_FIELDS", field_path, "unexpected fields"
        )
    return MappingProxyType(fields)


def node_strings(node: Node, field_path: str) -> tuple[str, ...]:
    if not isinstance(node, SequenceNode):
        reject_structure_catalog(
            "STRUCTURE.YAML_SEQUENCE", field_path, "must be a sequence"
        )
    values = tuple(node_string(item, field_path) for item in node.value)
    if not values or len(values) != len(set(values)):
        reject_structure_catalog(
            "STRUCTURE.YAML_SEQUENCE", field_path, "must be nonempty and unique"
        )
    return values


def parse_family(value: str) -> StructureFamily:
    for family in StructureFamily:
        if value == family.value:
            return family
    reject_structure_catalog("STRUCTURE.FAMILY", "family", "unsupported family")


def _parse_role(value: str) -> StructureRole:
    for role in StructureRole:
        if value == role.value:
            return role
    reject_structure_catalog("STRUCTURE.ROLE", "required_roles", "unsupported role")


def _parse_condition(value: str) -> StructureConditionType:
    for condition in StructureConditionType:
        if value == condition.value:
            return condition
    reject_structure_catalog(
        "STRUCTURE.CONDITION_TYPE", "condition_types", "unsupported condition"
    )


def parse_source_status(value: str) -> SourceStatus:
    for status in SourceStatus:
        if value == status.value:
            return status
    reject_structure_catalog(
        "STRUCTURE.SOURCE_STATUS", "source_status", "unsupported source status"
    )


def parse_implementation_status(value: str) -> ImplementationStatus:
    for status in ImplementationStatus:
        if value == status.value:
            return status
    reject_structure_catalog(
        "STRUCTURE.IMPLEMENTATION_STATUS",
        "implementation_status",
        "unsupported implementation status",
    )


def parse_legacy_mapping(value: str | None) -> TenGodStructureKind | None:
    if value is None:
        return None
    for kind in TenGodStructureKind:
        if value == kind.name:
            return kind
    reject_structure_catalog(
        "STRUCTURE.LEGACY_MAPPING", "legacy_mapping", "unknown legacy mapping"
    )


def parse_roles(node: Node) -> tuple[StructureRole, ...]:
    return tuple(_parse_role(value) for value in node_strings(node, "required_roles"))


def parse_conditions(
    node: Node,
    field_path: str,
) -> tuple[StructureConditionType, ...]:
    return tuple(_parse_condition(value) for value in node_strings(node, field_path))


def legacy_mapping_name(legacy_mapping: TenGodStructureKind | None) -> str:
    if legacy_mapping is None:
        return ""
    return legacy_mapping.name
