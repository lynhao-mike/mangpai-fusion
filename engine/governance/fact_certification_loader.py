from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Final, Never

import yaml
from yaml import MappingNode, Node, ScalarNode, SequenceNode

from engine.governance.fact_certification import (
    CertificationContractError,
    CertificationIdentity,
    FactCertification,
    FactCertificationRegistry,
    PublicationStatus,
)
from engine.governance.fact_values import DigestRef, FactLevel


DEFAULT_FACT_CERTIFICATION_PATH: Final = Path("theory/multi-school-governance-v1.yaml")
_REGISTRY_SCHEMA: Final = "multi-school-governance/v1"
_TOP_LEVEL_FIELDS: Final = frozenset(
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
_ENTRY_FIELDS: Final = frozenset(
    {
        "registration_id",
        "certification_level",
        "fact_kind",
        "calculator_id",
        "calculator_version",
        "schema_version",
        "publication_status",
        "specification_digest",
        "cross_school_review_refs",
    }
)


def _reject(issue_code: str, field_path: str, diagnostic: str) -> Never:
    raise CertificationContractError(issue_code, field_path, diagnostic)


def _fields(
    node: Node,
    field_path: str,
    expected: frozenset[str],
    optional: frozenset[str] = frozenset(),
) -> Mapping[str, Node]:
    if not isinstance(node, MappingNode):
        _reject(
            "CERTIFICATION.YAML_MAPPING", field_path, f"{field_path} must be a mapping"
        )
    result: dict[str, Node] = {}
    for key_node, value_node in node.value:
        key = _string(key_node, f"{field_path}.key")
        if key in result:
            _reject(
                "CERTIFICATION.YAML_DUPLICATE_FIELD",
                field_path,
                f"duplicate field: {key}",
            )
        result[key] = value_node
    actual = frozenset(result)
    if not expected <= actual <= expected | optional:
        _reject(
            "CERTIFICATION.YAML_FIELDS",
            field_path,
            f"unexpected fields in {field_path}",
        )
    return MappingProxyType(result)


def _string(node: Node, field_path: str) -> str:
    if (
        not isinstance(node, ScalarNode)
        or node.tag != "tag:yaml.org,2002:str"
        or not node.value.strip()
    ):
        _reject(
            "CERTIFICATION.YAML_STRING",
            field_path,
            f"{field_path} must be a nonempty YAML string",
        )
    return node.value


def _strings(node: Node, field_path: str) -> tuple[str, ...]:
    if not isinstance(node, SequenceNode):
        _reject(
            "CERTIFICATION.YAML_SEQUENCE",
            field_path,
            f"{field_path} must be a YAML sequence",
        )
    return tuple(_string(item, field_path) for item in node.value)


def _level(value: str) -> FactLevel:
    if value == "certified_technical":
        return FactLevel.CERTIFIED_TECHNICAL
    if value == "certified_cross_school":
        return FactLevel.CERTIFIED_CROSS_SCHOOL
    _reject(
        "CERTIFICATION.LEVEL",
        "certification_level",
        "unsupported certification level",
    )


def _status(value: str) -> PublicationStatus:
    for status in PublicationStatus:
        if value == status.value:
            return status
    _reject(
        "CERTIFICATION.STATUS",
        "publication_status",
        "unsupported publication status",
    )


def _entry(node: Node, index: int) -> FactCertification:
    fields = _fields(node, f"certifications[{index}]", _ENTRY_FIELDS)
    identity = CertificationIdentity(
        _level(_string(fields["certification_level"], "certification_level")),
        _string(fields["fact_kind"], "fact_kind"),
        _string(fields["calculator_id"], "calculator_id"),
        _string(fields["calculator_version"], "calculator_version"),
        _string(fields["schema_version"], "schema_version"),
    )
    return FactCertification(
        _string(fields["registration_id"], "registration_id"),
        identity,
        _status(_string(fields["publication_status"], "publication_status")),
        DigestRef(_string(fields["specification_digest"], "specification_digest")),
        _strings(fields["cross_school_review_refs"], "cross_school_review_refs"),
    )


def resolve_registry_path(path: str | Path, workspace_root: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        _reject(
            "CERTIFICATION.PATH", "path", "registry path must be relative and contained"
        )
    root = Path(workspace_root).resolve(strict=False)
    current = root
    for component in candidate.parts:
        current = current / component
        if current.is_symlink():
            _reject(
                "CERTIFICATION.SYMLINK",
                "path",
                "registry path must not traverse symlinks",
            )
    resolved = (root / candidate).resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError:
        _reject("CERTIFICATION.PATH", "path", "registry path escapes workspace root")
    if not resolved.is_file():
        _reject(
            "CERTIFICATION.PATH",
            "path",
            "registry path must name an existing regular file",
        )
    return resolved


def load_fact_certification_registry(
    path: str | Path = DEFAULT_FACT_CERTIFICATION_PATH,
    *,
    workspace_root: str | Path = ".",
) -> FactCertificationRegistry:
    registry_path = resolve_registry_path(path, workspace_root)
    try:
        node = yaml.compose(
            registry_path.read_text(encoding="utf-8"), Loader=yaml.SafeLoader
        )
    except yaml.YAMLError as error:
        raise CertificationContractError(
            "CERTIFICATION.YAML_PARSE", "path", "invalid registry YAML"
        ) from error
    if node is None:
        _reject("CERTIFICATION.YAML_EMPTY", "path", "registry YAML must not be empty")
    top_level = _fields(
        node,
        "registry",
        _TOP_LEVEL_FIELDS - {"composition_templates", "triggers"},
        frozenset({"composition_templates", "triggers"}),
    )
    if _string(top_level["schema_version"], "schema_version") != _REGISTRY_SCHEMA:
        _reject(
            "CERTIFICATION.SCHEMA",
            "schema_version",
            "unsupported registry schema version",
        )
    certifications = top_level["certifications"]
    if not isinstance(certifications, SequenceNode):
        _reject(
            "CERTIFICATION.YAML_SEQUENCE",
            "certifications",
            "certifications must be a YAML sequence",
        )
    return FactCertificationRegistry(
        tuple(_entry(item, index) for index, item in enumerate(certifications.value))
    )
