from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Final, Never

import yaml
from yaml import MappingNode, Node, ScalarNode, SequenceNode

from engine.governance.composition_loader import load_composition_registry
from engine.governance.fact_certification_loader import resolve_registry_path
from engine.governance.trigger_registry import (
    TriggerRegistrationSpec,
    TriggerRegistry,
    TriggerRegistryContractError,
    build_trigger_registry,
)


DEFAULT_TRIGGER_REGISTRY_PATH: Final = Path("theory/multi-school-governance-v1.yaml")
_SCHEMA: Final = "multi-school-governance/v1"
_TOP_FIELDS: Final = frozenset(
    {
        "schema_version",
        "certifications",
        "schools",
        "legacy_compatibility_sources",
        "capabilities",
        "composition_templates",
        "triggers",
    }
)
_TRIGGER_FIELDS: Final = frozenset(
    {
        "trigger_id",
        "evaluator_id",
        "evaluator_version",
        "required_fact_kinds",
        "allowed_temporal_layers",
        "missing_input_behavior",
        "publication_status",
    }
)


def _reject(issue_code: str, field_path: str, diagnostic: str) -> Never:
    raise TriggerRegistryContractError(issue_code, field_path, diagnostic)


def _string(node: Node, field_path: str) -> str:
    if (
        not isinstance(node, ScalarNode)
        or node.tag != "tag:yaml.org,2002:str"
        or not node.value.strip()
    ):
        _reject("TRIGGER.YAML_STRING", field_path, "must be a nonempty string")
    return node.value


def _fields(
    node: Node,
    field_path: str,
    expected: frozenset[str],
) -> Mapping[str, Node]:
    if not isinstance(node, MappingNode):
        _reject("TRIGGER.YAML_MAPPING", field_path, "must be a mapping")
    fields: dict[str, Node] = {}
    for key_node, value_node in node.value:
        key = _string(key_node, f"{field_path}.key")
        if key in fields:
            _reject(
                "TRIGGER.YAML_DUPLICATE_FIELD",
                field_path,
                f"duplicate field: {key}",
            )
        fields[key] = value_node
    if frozenset(fields) != expected:
        _reject("TRIGGER.YAML_FIELDS", field_path, "unexpected fields")
    return MappingProxyType(fields)


def _strings(node: Node, field_path: str) -> tuple[str, ...]:
    if not isinstance(node, SequenceNode):
        _reject("TRIGGER.YAML_SEQUENCE", field_path, "must be a sequence")
    values = tuple(_string(item, field_path) for item in node.value)
    if not values or len(values) != len(set(values)):
        _reject("TRIGGER.YAML_SEQUENCE", field_path, "must be nonempty and unique")
    return tuple(sorted(values))


def _trigger(node: Node, index: int) -> TriggerRegistrationSpec:
    fields = _fields(node, f"triggers[{index}]", _TRIGGER_FIELDS)
    return TriggerRegistrationSpec(
        trigger_id=_string(fields["trigger_id"], "trigger_id"),
        evaluator_id=_string(fields["evaluator_id"], "evaluator_id"),
        evaluator_version=_string(fields["evaluator_version"], "evaluator_version"),
        required_fact_kinds=_strings(
            fields["required_fact_kinds"], "required_fact_kinds"
        ),
        allowed_temporal_layers=_strings(
            fields["allowed_temporal_layers"], "allowed_temporal_layers"
        ),
        missing_input_behavior=_string(
            fields["missing_input_behavior"], "missing_input_behavior"
        ),
        publication_status=_string(fields["publication_status"], "publication_status"),
    )


def load_trigger_registry(
    path: str | Path = DEFAULT_TRIGGER_REGISTRY_PATH,
    *,
    workspace_root: str | Path = ".",
) -> TriggerRegistry:
    load_composition_registry(path, workspace_root=workspace_root)
    registry_path = resolve_registry_path(path, workspace_root)
    try:
        node = yaml.compose(
            registry_path.read_text(encoding="utf-8"), Loader=yaml.SafeLoader
        )
    except yaml.YAMLError as error:
        raise TriggerRegistryContractError(
            "TRIGGER.YAML_PARSE", "path", "invalid registry YAML"
        ) from error
    if node is None:
        _reject("TRIGGER.YAML_EMPTY", "path", "registry YAML must not be empty")
    fields = _fields(node, "registry", _TOP_FIELDS)
    if _string(fields["schema_version"], "schema_version") != _SCHEMA:
        _reject("TRIGGER.SCHEMA", "schema_version", "unsupported schema")
    triggers = fields["triggers"]
    if not isinstance(triggers, SequenceNode):
        _reject("TRIGGER.YAML_SEQUENCE", "triggers", "must be a sequence")
    return build_trigger_registry(
        tuple(_trigger(item, index) for index, item in enumerate(triggers.value))
    )
