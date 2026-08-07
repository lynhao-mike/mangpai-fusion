from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Final, Never

import yaml
from yaml import MappingNode, Node, ScalarNode, SequenceNode

from engine.governance.fact_certification import (
    CertificationContractError,
    PublicationStatus,
)
from engine.governance.fact_certification_loader import (
    DEFAULT_FACT_CERTIFICATION_PATH,
    load_fact_certification_registry,
    resolve_registry_path,
)
from engine.governance.governance_claim_values import ClaimEvidenceGrade, ClaimKind
from engine.governance.school_registry import (
    CapabilityIdentity,
    CapabilityRegistration,
    CapabilityRole,
    LegacyCompatibilitySource,
    PEER_SCHOOL_IDS,
    PeerSchool,
    SchoolRegistry,
    SchoolRegistryContractError,
)


DEFAULT_SCHOOL_REGISTRY_PATH: Final = DEFAULT_FACT_CERTIFICATION_PATH
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
_CAPABILITY_FIELDS: Final = frozenset(
    {
        "school_id",
        "task_id",
        "claim_kind",
        "evidence_grade",
        "version",
        "role",
        "publication_status",
    }
)


def _reject(issue_code: str, field_path: str, diagnostic: str) -> Never:
    raise SchoolRegistryContractError(issue_code, field_path, diagnostic)


def _string(node: Node, field_path: str) -> str:
    if (
        not isinstance(node, ScalarNode)
        or node.tag != "tag:yaml.org,2002:str"
        or not node.value.strip()
    ):
        _reject(
            "SCHOOL.YAML_STRING",
            field_path,
            f"{field_path} must be a nonempty YAML string",
        )
    return node.value


def _fields(
    node: Node,
    field_path: str,
    expected: frozenset[str],
    optional: frozenset[str] = frozenset(),
) -> Mapping[str, Node]:
    if not isinstance(node, MappingNode):
        _reject("SCHOOL.YAML_MAPPING", field_path, f"{field_path} must be a mapping")
    fields: dict[str, Node] = {}
    for key_node, value_node in node.value:
        key = _string(key_node, f"{field_path}.key")
        if key in fields:
            _reject(
                "SCHOOL.YAML_DUPLICATE_FIELD", field_path, f"duplicate field: {key}"
            )
        fields[key] = value_node
    actual = frozenset(fields)
    if not expected <= actual <= expected | optional:
        _reject("SCHOOL.YAML_FIELDS", field_path, f"unexpected fields in {field_path}")
    return MappingProxyType(fields)


def _strings(node: Node, field_path: str) -> tuple[str, ...]:
    if not isinstance(node, SequenceNode):
        _reject(
            "SCHOOL.YAML_SEQUENCE", field_path, f"{field_path} must be a YAML sequence"
        )
    return tuple(_string(item, field_path) for item in node.value)


def _claim_kind(value: str) -> ClaimKind:
    for claim_kind in ClaimKind:
        if value == claim_kind.value:
            return claim_kind
    _reject("CAPABILITY.CLAIM_KIND", "claim_kind", "unsupported claim kind")


def _evidence_grade(value: str) -> ClaimEvidenceGrade:
    for evidence_grade in ClaimEvidenceGrade:
        if value == evidence_grade.value:
            return evidence_grade
    _reject("CAPABILITY.EVIDENCE_GRADE", "evidence_grade", "unsupported grade")


def _role(value: str) -> CapabilityRole:
    for role in CapabilityRole:
        if value == role.value:
            return role
    _reject("CAPABILITY.ROLE", "role", "unsupported capability role")


def _publication_status(value: str) -> PublicationStatus:
    for status in PublicationStatus:
        if value == status.value:
            return status
    _reject(
        "CAPABILITY.PUBLICATION_STATUS",
        "publication_status",
        "unsupported publication status",
    )


def _capability(node: Node, index: int) -> CapabilityRegistration:
    fields = _fields(node, f"capabilities[{index}]", _CAPABILITY_FIELDS)
    return CapabilityRegistration(
        identity=CapabilityIdentity(
            school_id=_string(fields["school_id"], "school_id"),
            task_id=_string(fields["task_id"], "task_id"),
            claim_kind=_claim_kind(_string(fields["claim_kind"], "claim_kind")),
            evidence_grade=_evidence_grade(
                _string(fields["evidence_grade"], "evidence_grade")
            ),
            version=_string(fields["version"], "version"),
        ),
        role=_role(_string(fields["role"], "role")),
        publication_status=_publication_status(
            _string(fields["publication_status"], "publication_status")
        ),
    )


def load_school_registry(
    path: str | Path = DEFAULT_SCHOOL_REGISTRY_PATH, *, workspace_root: str | Path = "."
) -> SchoolRegistry:
    try:
        load_fact_certification_registry(path, workspace_root=workspace_root)
    except CertificationContractError as error:
        raise SchoolRegistryContractError(
            error.issue_code, error.field_path, error.diagnostic
        ) from error
    registry_path = resolve_registry_path(path, workspace_root)
    try:
        node = yaml.compose(
            registry_path.read_text(encoding="utf-8"), Loader=yaml.SafeLoader
        )
    except yaml.YAMLError as error:
        raise SchoolRegistryContractError(
            "SCHOOL.YAML_PARSE", "path", "invalid registry YAML"
        ) from error
    if node is None:
        _reject("SCHOOL.YAML_EMPTY", "path", "registry YAML must not be empty")
    fields = _fields(
        node,
        "registry",
        _TOP_FIELDS - {"composition_templates", "triggers"},
        frozenset({"composition_templates", "triggers"}),
    )
    if _string(fields["schema_version"], "schema_version") != _SCHEMA:
        _reject(
            "SCHOOL.SCHEMA", "schema_version", "unsupported registry schema version"
        )
    school_ids = _strings(fields["schools"], "schools")
    if school_ids != PEER_SCHOOL_IDS:
        _reject("SCHOOL.PEER_SET", "schools", "schools must be the exact peer registry")
    legacy_ids = _strings(
        fields["legacy_compatibility_sources"], "legacy_compatibility_sources"
    )
    if legacy_ids != ("ditiansui",):
        _reject(
            "SCHOOL.LEGACY_SET", "legacy_compatibility_sources", "legacy set is fixed"
        )
    capabilities = fields["capabilities"]
    if not isinstance(capabilities, SequenceNode):
        _reject(
            "CAPABILITY.YAML_SEQUENCE",
            "capabilities",
            "capabilities must be a YAML sequence",
        )
    return SchoolRegistry(
        peer_schools=tuple(PeerSchool(value) for value in school_ids),
        legacy_compatibility_sources=(LegacyCompatibilitySource("ditiansui"),),
        capabilities=tuple(
            _capability(item, index) for index, item in enumerate(capabilities.value)
        ),
    )
