from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from typing import Final

import yaml
from yaml import Node, SequenceNode

from engine.governance.fact_values import DigestRef
from engine.governance.structure_catalog_loader_values import (
    legacy_mapping_name,
    node_fields,
    node_optional_string,
    node_string,
    node_strings,
    parse_conditions,
    parse_family,
    parse_implementation_status,
    parse_legacy_mapping,
    parse_roles,
    parse_source_status,
    reject_structure_catalog,
)
from engine.governance.structure_catalog_types import (
    CanonicalStructureKey as CanonicalStructureKey,
    ImplementationStatus as ImplementationStatus,
    SourceStatus as SourceStatus,
    StructureCatalog as StructureCatalog,
    StructureCatalogContractError as StructureCatalogContractError,
    StructureCatalogEntry as StructureCatalogEntry,
    StructureConditionType as StructureConditionType,
    StructureFamily as StructureFamily,
    StructureId as StructureId,
    StructureRole as StructureRole,
)
from engine.predicates.ten_god_structure_types import TenGodStructureKind


DEFAULT_STRUCTURE_CATALOG_PATH: Final = Path("theory/ziping/structure-catalog-v1.yaml")
_SCHEMA: Final = "ziping.structure-catalog/v1"
_TOP_FIELDS: Final = frozenset({"schema_version", "structures"})
_ENTRY_FIELDS: Final = frozenset(
    {
        "structure_id",
        "canonical_key",
        "display_name_zh",
        "family",
        "required_roles",
        "candidate_types",
        "clear_types",
        "block_types",
        "damage_types",
        "source_status",
        "implementation_status",
        "legacy_mapping",
        "source_refs",
    }
)
_CURRENT_IDS: Final = frozenset(
    {
        "food_god_controls_killing",
        "hurting_officer_controls_killing",
        "killing_generates_seal",
    }
)


def _legacy_keys(
    entries: tuple[StructureCatalogEntry, ...],
) -> tuple[TenGodStructureKind, ...]:
    return tuple(
        entry.legacy_mapping for entry in entries if entry.legacy_mapping is not None
    )


def _entry_identity_for_scan(
    node: Node,
    index: int,
) -> tuple[str, str, TenGodStructureKind | None]:
    fields = node_fields(node, f"structures[{index}]", _ENTRY_FIELDS)
    return (
        node_string(fields["structure_id"], "structure_id"),
        node_string(fields["canonical_key"], "canonical_key"),
        parse_legacy_mapping(
            node_optional_string(fields["legacy_mapping"], "legacy_mapping")
        ),
    )


def _entry(node: Node, index: int) -> StructureCatalogEntry:
    fields = node_fields(node, f"structures[{index}]", _ENTRY_FIELDS)
    structure_id = StructureId(node_string(fields["structure_id"], "structure_id"))
    canonical_key = CanonicalStructureKey(
        node_string(fields["canonical_key"], "canonical_key")
    )
    display_name_zh = node_string(fields["display_name_zh"], "display_name_zh")
    family = parse_family(node_string(fields["family"], "family"))
    required_roles = parse_roles(fields["required_roles"])
    candidate_types = parse_conditions(fields["candidate_types"], "candidate_types")
    clear_types = parse_conditions(fields["clear_types"], "clear_types")
    block_types = parse_conditions(fields["block_types"], "block_types")
    damage_types = parse_conditions(fields["damage_types"], "damage_types")
    source_status = parse_source_status(
        node_string(fields["source_status"], "source_status")
    )
    implementation_status = parse_implementation_status(
        node_string(fields["implementation_status"], "implementation_status")
    )
    legacy_mapping = parse_legacy_mapping(
        node_optional_string(fields["legacy_mapping"], "legacy_mapping")
    )
    source_refs = node_strings(fields["source_refs"], "source_refs")
    material = (
        str(structure_id),
        str(canonical_key),
        display_name_zh,
        family.value,
        *(role.value for role in required_roles),
        *(condition.value for condition in candidate_types),
        *(condition.value for condition in clear_types),
        *(condition.value for condition in block_types),
        *(condition.value for condition in damage_types),
        source_status.value,
        implementation_status.value,
        legacy_mapping_name(legacy_mapping),
        *source_refs,
    )
    digest = DigestRef.from_material(
        (
            "ziping.structure-entry.v1",
            material,
        )
    )
    return StructureCatalogEntry(
        structure_id,
        canonical_key,
        display_name_zh,
        family,
        required_roles,
        candidate_types,
        clear_types,
        block_types,
        damage_types,
        source_status,
        implementation_status,
        legacy_mapping,
        source_refs,
        digest,
    )


def _catalog(entries: tuple[StructureCatalogEntry, ...]) -> StructureCatalog:
    if len(entries) != 30:
        reject_structure_catalog(
            "STRUCTURE.COUNT", "structures", "catalog must contain exactly 30"
        )
    ids = tuple(str(entry.structure_id) for entry in entries)
    if len(ids) != len(set(ids)):
        reject_structure_catalog(
            "STRUCTURE.DUPLICATE_ID", "structures", "duplicate structure ID"
        )
    keys = tuple(str(entry.canonical_key) for entry in entries)
    if len(keys) != len(set(keys)):
        reject_structure_catalog(
            "STRUCTURE.DUPLICATE_KEY", "structures", "duplicate canonical key"
        )
    current_ids = frozenset(
        str(entry.structure_id)
        for entry in entries
        if entry.implementation_status is ImplementationStatus.CURRENT_IMPLEMENTED
    )
    if current_ids != _CURRENT_IDS:
        reject_structure_catalog(
            "STRUCTURE.IMPLEMENTED_SET", "structures", "implemented set changed"
        )
    legacy_keys = _legacy_keys(entries)
    if len(legacy_keys) != len(set(legacy_keys)):
        reject_structure_catalog(
            "STRUCTURE.LEGACY_DUPLICATE",
            "legacy_mapping",
            "duplicate legacy mapping",
        )
    projection = {
        entry.legacy_mapping: str(entry.structure_id)
        for entry in entries
        if entry.legacy_mapping is not None
    }
    if set(projection) != set(TenGodStructureKind):
        reject_structure_catalog(
            "STRUCTURE.LEGACY_SET", "legacy_mapping", "legacy mapping incomplete"
        )
    material = tuple(
        sorted(
            (str(entry.structure_id), entry.content_digest.value) for entry in entries
        )
    )
    return StructureCatalog(
        _SCHEMA,
        entries,
        MappingProxyType(projection),
        DigestRef.from_material(("ziping.structure-catalog.v1", material)),
    )


def load_structure_catalog(
    path: str | Path = DEFAULT_STRUCTURE_CATALOG_PATH,
    *,
    workspace_root: str | Path = ".",
) -> StructureCatalog:
    catalog_path = Path(path)
    if not catalog_path.is_absolute():
        catalog_path = Path(workspace_root) / catalog_path
    try:
        node = yaml.compose(
            catalog_path.read_text(encoding="utf-8"), Loader=yaml.SafeLoader
        )
    except yaml.YAMLError as error:
        raise StructureCatalogContractError(
            "STRUCTURE.YAML_PARSE", "path", "invalid catalog YAML"
        ) from error
    if node is None:
        reject_structure_catalog(
            "STRUCTURE.YAML_EMPTY", "path", "catalog YAML must not be empty"
        )
    fields = node_fields(node, "catalog", _TOP_FIELDS)
    if node_string(fields["schema_version"], "schema_version") != _SCHEMA:
        reject_structure_catalog(
            "STRUCTURE.SCHEMA", "schema_version", "unsupported schema"
        )
    structures = fields["structures"]
    if not isinstance(structures, SequenceNode):
        reject_structure_catalog(
            "STRUCTURE.YAML_SEQUENCE", "structures", "must be a sequence"
        )
    scanned_entries = tuple(
        _entry_identity_for_scan(item, index)
        for index, item in enumerate(structures.value)
    )
    ids = tuple(structure_id for structure_id, _, _ in scanned_entries)
    if len(ids) != len(set(ids)):
        reject_structure_catalog(
            "STRUCTURE.DUPLICATE_ID", "structures", "duplicate structure ID"
        )
    keys = tuple(canonical_key for _, canonical_key, _ in scanned_entries)
    if len(keys) != len(set(keys)):
        reject_structure_catalog(
            "STRUCTURE.DUPLICATE_KEY", "structures", "duplicate canonical key"
        )
    legacy_keys = tuple(
        legacy_mapping
        for _, _, legacy_mapping in scanned_entries
        if legacy_mapping is not None
    )
    if len(legacy_keys) != len(set(legacy_keys)):
        reject_structure_catalog(
            "STRUCTURE.LEGACY_DUPLICATE",
            "legacy_mapping",
            "duplicate legacy mapping",
        )
    return _catalog(
        tuple(_entry(item, index) for index, item in enumerate(structures.value))
    )
