from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Final, Never

import yaml
from yaml import MappingNode, Node, ScalarNode, SequenceNode

from engine.governance.composition_contracts import CompositionContractError
from engine.governance.composition_templates import (
    CompositionRegistry,
    CompositionTemplate,
    CompositionTemplateStatus,
    RequiredComponentSlot,
)
from engine.governance.fact_certification_loader import resolve_registry_path
from engine.governance.fact_values import DigestRef
from engine.governance.governance_claim_values import ClaimEvidenceGrade, ClaimKind
from engine.governance.school_registry_loader import load_school_registry


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
_TEMPLATE_FIELDS: Final = frozenset(
    {
        "template_id",
        "version",
        "accepted_claim_kinds",
        "accepted_stances",
        "accepted_task_ids",
        "accepted_temporal_layers",
        "required_component_slots",
        "output_kind",
        "event_scope_rule",
        "temporal_rule",
        "evidence_cap",
        "preserve_counterevidence",
        "preserve_falsifier",
        "human_review_conditions",
        "status",
        "specification_digest",
    }
)
_SLOT_FIELDS: Final = frozenset({"slot_id", "count"})


def _reject(code: str, path: str, diagnostic: str) -> Never:
    raise CompositionContractError(code, path, diagnostic)


def _fields(
    node: Node,
    path: str,
    expected: frozenset[str],
    optional: frozenset[str] = frozenset(),
) -> Mapping[str, Node]:
    if not isinstance(node, MappingNode):
        _reject("COMPOSITION.YAML_MAPPING", path, "must be a mapping")
    values: dict[str, Node] = {}
    for key_node, value_node in node.value:
        key = _string(key_node, f"{path}.key")
        if key in values:
            _reject("COMPOSITION.YAML_DUPLICATE_FIELD", path, f"duplicate field: {key}")
        values[key] = value_node
    actual = frozenset(values)
    if not expected <= actual <= expected | optional:
        _reject("COMPOSITION.YAML_FIELDS", path, "unexpected fields")
    return MappingProxyType(values)


def _string(node: Node, path: str) -> str:
    if (
        not isinstance(node, ScalarNode)
        or node.tag != "tag:yaml.org,2002:str"
        or not node.value.strip()
    ):
        _reject("COMPOSITION.YAML_STRING", path, "must be a nonempty string")
    return node.value


def _bool(node: Node, path: str) -> bool:
    if not isinstance(node, ScalarNode) or node.tag != "tag:yaml.org,2002:bool":
        _reject("COMPOSITION.YAML_BOOL", path, "must be a boolean")
    if node.value == "true":
        return True
    if node.value == "false":
        return False
    _reject("COMPOSITION.YAML_BOOL", path, "must be a boolean")


def _strings(node: Node, path: str) -> tuple[str, ...]:
    if not isinstance(node, SequenceNode):
        _reject("COMPOSITION.YAML_SEQUENCE", path, "must be a sequence")
    values = tuple(_string(item, path) for item in node.value)
    if not values or len(values) != len(set(values)):
        _reject("COMPOSITION.YAML_SEQUENCE", path, "must be nonempty and unique")
    return tuple(sorted(values))


def _kind(value: str, path: str) -> ClaimKind:
    for kind in ClaimKind:
        if value == kind.value:
            return kind
    _reject("COMPOSITION.CLAIM_KIND", path, "unsupported claim kind")


def _grade(value: str) -> ClaimEvidenceGrade:
    for grade in ClaimEvidenceGrade:
        if value == grade.value:
            return grade
    _reject("COMPOSITION.EVIDENCE_CAP", "evidence_cap", "unsupported evidence grade")


def _status(value: str) -> CompositionTemplateStatus:
    for status in CompositionTemplateStatus:
        if value == status.value:
            return status
    _reject("COMPOSITION.STATUS", "status", "unsupported status")


def _slot(node: Node, index: int) -> RequiredComponentSlot:
    fields = _fields(node, f"required_component_slots[{index}]", _SLOT_FIELDS)
    count_node = fields["count"]
    if (
        not isinstance(count_node, ScalarNode)
        or count_node.tag != "tag:yaml.org,2002:int"
    ):
        _reject("COMPOSITION.SLOT_COUNT", "count", "must be an integer")
    return RequiredComponentSlot(
        _string(fields["slot_id"], "slot_id"), int(count_node.value)
    )


def _template(node: Node, index: int) -> CompositionTemplate:
    fields = _fields(node, f"composition_templates[{index}]", _TEMPLATE_FIELDS)
    slots_node = fields["required_component_slots"]
    if not isinstance(slots_node, SequenceNode):
        _reject("COMPOSITION.SLOTS", "required_component_slots", "must be a sequence")
    kinds = tuple(
        _kind(value, "accepted_claim_kinds")
        for value in _strings(fields["accepted_claim_kinds"], "accepted_claim_kinds")
    )
    return CompositionTemplate(
        _string(fields["template_id"], "template_id"),
        _string(fields["version"], "version"),
        kinds,
        _strings(fields["accepted_stances"], "accepted_stances"),
        _strings(fields["accepted_task_ids"], "accepted_task_ids"),
        _strings(fields["accepted_temporal_layers"], "accepted_temporal_layers"),
        tuple(_slot(item, position) for position, item in enumerate(slots_node.value)),
        _kind(_string(fields["output_kind"], "output_kind"), "output_kind"),
        _string(fields["event_scope_rule"], "event_scope_rule"),
        _string(fields["temporal_rule"], "temporal_rule"),
        _grade(_string(fields["evidence_cap"], "evidence_cap")),
        _bool(fields["preserve_counterevidence"], "preserve_counterevidence"),
        _bool(fields["preserve_falsifier"], "preserve_falsifier"),
        _strings(fields["human_review_conditions"], "human_review_conditions"),
        _status(_string(fields["status"], "status")),
        DigestRef(_string(fields["specification_digest"], "specification_digest")),
    )


def load_composition_registry(
    path: str | Path = Path("theory/multi-school-governance-v1.yaml"),
    *,
    workspace_root: str | Path = ".",
) -> CompositionRegistry:
    load_school_registry(path, workspace_root=workspace_root)
    registry_path = resolve_registry_path(path, workspace_root)
    try:
        node = yaml.compose(
            registry_path.read_text(encoding="utf-8"), Loader=yaml.SafeLoader
        )
    except yaml.YAMLError as error:
        raise CompositionContractError(
            "COMPOSITION.YAML_PARSE", "path", "invalid registry YAML"
        ) from error
    if node is None:
        _reject("COMPOSITION.YAML_EMPTY", "path", "registry YAML must not be empty")
    fields = _fields(
        node,
        "registry",
        _TOP_FIELDS - {"triggers"},
        frozenset({"triggers"}),
    )
    templates = fields["composition_templates"]
    if not isinstance(templates, SequenceNode):
        _reject(
            "COMPOSITION.YAML_SEQUENCE", "composition_templates", "must be a sequence"
        )
    return CompositionRegistry(
        tuple(_template(item, index) for index, item in enumerate(templates.value))
    )
