from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from engine.governance.fact_values import DigestRef
from engine.governance.structure_catalog_types import (
    CanonicalStructureKey,
    ImplementationStatus,
    SourceStatus,
    StructureCatalogContractError,
    StructureConditionType,
    StructureFamily,
    StructureId,
    StructureRole,
)
from engine.predicates.ten_god_structure_types import TenGodStructureKind


_SCHEMA: Final = "ziping.structure-catalog/v1"
_EXPECTED_LEGACY_TARGETS: Final = MappingProxyType(
    {
        TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING: "food_god_controls_killing",
        TenGodStructureKind.HURTING_OFFICER_CONTROLS_KILLING: (
            "hurting_officer_controls_killing"
        ),
        TenGodStructureKind.KILLING_GENERATES_SEAL: "killing_generates_seal",
    }
)
_CURRENT_IDS: Final = frozenset(_EXPECTED_LEGACY_TARGETS.values())


def _entry_material(entry: StructureCatalogEntry) -> tuple[str, ...]:
    legacy = entry.legacy_mapping.name if entry.legacy_mapping is not None else ""
    return (
        str(entry.structure_id),
        str(entry.canonical_key),
        entry.display_name_zh,
        entry.family.value,
        *(role.value for role in entry.required_roles),
        *(condition.value for condition in entry.candidate_types),
        *(condition.value for condition in entry.clear_types),
        *(condition.value for condition in entry.block_types),
        *(condition.value for condition in entry.damage_types),
        entry.source_status.value,
        entry.implementation_status.value,
        legacy,
        *entry.source_refs,
    )


def expected_entry_digest(entry: StructureCatalogEntry) -> DigestRef:
    return DigestRef.from_material(
        ("ziping.structure-entry.v1", _entry_material(entry))
    )


def expected_catalog_digest(entries: tuple[StructureCatalogEntry, ...]) -> DigestRef:
    material = tuple(
        sorted(
            (str(entry.structure_id), entry.content_digest.value) for entry in entries
        )
    )
    return DigestRef.from_material(("ziping.structure-catalog.v1", material))


@dataclass(frozen=True, slots=True)
class StructureCatalogEntry:
    structure_id: StructureId
    canonical_key: CanonicalStructureKey
    display_name_zh: str
    family: StructureFamily
    required_roles: tuple[StructureRole, ...]
    candidate_types: tuple[StructureConditionType, ...]
    clear_types: tuple[StructureConditionType, ...]
    block_types: tuple[StructureConditionType, ...]
    damage_types: tuple[StructureConditionType, ...]
    source_status: SourceStatus
    implementation_status: ImplementationStatus
    legacy_mapping: TenGodStructureKind | None
    source_refs: tuple[str, ...]
    content_digest: DigestRef

    def __post_init__(self) -> None:
        if type(self.structure_id) is not StructureId:
            raise StructureCatalogContractError(
                "STRUCTURE.ENTRY_TYPE", "structure_id", "invalid structure ID"
            )
        if type(self.canonical_key) is not CanonicalStructureKey:
            raise StructureCatalogContractError(
                "STRUCTURE.ENTRY_TYPE", "canonical_key", "invalid canonical key"
            )
        if type(self.display_name_zh) is not str or not self.display_name_zh.strip():
            raise StructureCatalogContractError(
                "STRUCTURE.ENTRY_TYPE", "display_name_zh", "invalid display name"
            )
        if type(self.family) is not StructureFamily:
            raise StructureCatalogContractError(
                "STRUCTURE.ENTRY_TYPE", "family", "invalid family"
            )
        _require_tuple("required_roles", self.required_roles, StructureRole)
        _require_tuple("candidate_types", self.candidate_types, StructureConditionType)
        _require_tuple("clear_types", self.clear_types, StructureConditionType)
        _require_tuple("block_types", self.block_types, StructureConditionType)
        _require_tuple("damage_types", self.damage_types, StructureConditionType)
        if type(self.source_status) is not SourceStatus:
            raise StructureCatalogContractError(
                "STRUCTURE.ENTRY_TYPE", "source_status", "invalid source status"
            )
        if type(self.implementation_status) is not ImplementationStatus:
            raise StructureCatalogContractError(
                "STRUCTURE.ENTRY_TYPE",
                "implementation_status",
                "invalid implementation status",
            )
        if self.legacy_mapping is not None and type(self.legacy_mapping) is not (
            TenGodStructureKind
        ):
            raise StructureCatalogContractError(
                "STRUCTURE.ENTRY_TYPE", "legacy_mapping", "invalid legacy mapping"
            )
        _require_text_tuple("source_refs", self.source_refs)
        if type(self.content_digest) is not DigestRef:
            raise StructureCatalogContractError(
                "STRUCTURE.ENTRY_TYPE", "content_digest", "invalid content digest"
            )
        _check_entry_legacy_target(self)
        if self.content_digest != expected_entry_digest(self):
            raise StructureCatalogContractError(
                "STRUCTURE.ENTRY_DIGEST", "content_digest", "entry digest mismatch"
            )


@dataclass(frozen=True, slots=True)
class StructureCatalog:
    schema_version: str
    entries: tuple[StructureCatalogEntry, ...]
    legacy_projection: Mapping[TenGodStructureKind, str]
    content_digest: DigestRef

    def __post_init__(self) -> None:
        if self.schema_version != _SCHEMA:
            raise StructureCatalogContractError(
                "STRUCTURE.SCHEMA", "schema_version", "unsupported schema"
            )
        if type(self.entries) is not tuple or any(
            type(entry) is not StructureCatalogEntry for entry in self.entries
        ):
            raise StructureCatalogContractError(
                "STRUCTURE.CATALOG_TYPE", "entries", "entries must be catalog entries"
            )
        if len(self.entries) != 30:
            raise StructureCatalogContractError(
                "STRUCTURE.COUNT", "entries", "catalog must contain exactly 30"
            )
        _check_unique_entries(self.entries)
        if type(self.legacy_projection) is not MappingProxyType:
            raise StructureCatalogContractError(
                "STRUCTURE.CATALOG_TYPE",
                "legacy_projection",
                "legacy projection must be immutable",
            )
        _check_legacy_projection(self.legacy_projection)
        if type(self.content_digest) is not DigestRef:
            raise StructureCatalogContractError(
                "STRUCTURE.CATALOG_TYPE", "content_digest", "invalid catalog digest"
            )
        if self.content_digest != expected_catalog_digest(self.entries):
            raise StructureCatalogContractError(
                "STRUCTURE.CATALOG_DIGEST",
                "content_digest",
                "catalog digest mismatch",
            )


def _require_tuple[T](
    field_path: str, values: tuple[T, ...], expected: type[T]
) -> None:
    if type(values) is not tuple or not values:
        raise StructureCatalogContractError(
            "STRUCTURE.ENTRY_TYPE", field_path, "field must be a nonempty tuple"
        )
    if any(type(value) is not expected for value in values):
        raise StructureCatalogContractError(
            "STRUCTURE.ENTRY_TYPE", field_path, "field contains invalid item"
        )


def _require_text_tuple(field_path: str, values: tuple[str, ...]) -> None:
    if type(values) is not tuple or not values:
        raise StructureCatalogContractError(
            "STRUCTURE.ENTRY_TYPE", field_path, "field must be a nonempty tuple"
        )
    if any(type(value) is not str or not value.strip() for value in values):
        raise StructureCatalogContractError(
            "STRUCTURE.ENTRY_TYPE", field_path, "field contains invalid text"
        )


def _check_entry_legacy_target(entry: StructureCatalogEntry) -> None:
    structure_id = str(entry.structure_id)
    expected = (
        _EXPECTED_LEGACY_TARGETS.get(entry.legacy_mapping)
        if entry.legacy_mapping is not None
        else None
    )
    if expected is not None and expected != structure_id:
        raise StructureCatalogContractError(
            "STRUCTURE.LEGACY_TARGET",
            "legacy_mapping",
            "legacy mapping target changed",
        )
    if entry.legacy_mapping is not None and (
        entry.implementation_status is not ImplementationStatus.CURRENT_IMPLEMENTED
    ):
        raise StructureCatalogContractError(
            "STRUCTURE.LEGACY_TARGET",
            "legacy_mapping",
            "catalog-only entry cannot carry legacy mapping",
        )
    if structure_id in _CURRENT_IDS and entry.legacy_mapping is None:
        raise StructureCatalogContractError(
            "STRUCTURE.LEGACY_TARGET",
            "legacy_mapping",
            "current implemented entry requires exact legacy mapping",
        )


def _check_unique_entries(entries: tuple[StructureCatalogEntry, ...]) -> None:
    ids = tuple(str(entry.structure_id) for entry in entries)
    if len(ids) != len(set(ids)):
        raise StructureCatalogContractError(
            "STRUCTURE.DUPLICATE_ID", "entries", "duplicate structure ID"
        )
    keys = tuple(str(entry.canonical_key) for entry in entries)
    if len(keys) != len(set(keys)):
        raise StructureCatalogContractError(
            "STRUCTURE.DUPLICATE_KEY", "entries", "duplicate canonical key"
        )
    current_ids = frozenset(
        str(entry.structure_id)
        for entry in entries
        if entry.implementation_status is ImplementationStatus.CURRENT_IMPLEMENTED
    )
    if current_ids != _CURRENT_IDS:
        raise StructureCatalogContractError(
            "STRUCTURE.IMPLEMENTED_SET", "entries", "implemented set changed"
        )


def _check_legacy_projection(projection: Mapping[TenGodStructureKind, str]) -> None:
    if set(projection) != set(TenGodStructureKind):
        raise StructureCatalogContractError(
            "STRUCTURE.LEGACY_SET", "legacy_projection", "legacy mapping incomplete"
        )
    for legacy, expected in _EXPECTED_LEGACY_TARGETS.items():
        if projection[legacy] != expected:
            raise StructureCatalogContractError(
                "STRUCTURE.LEGACY_TARGET",
                "legacy_projection",
                "legacy mapping target changed",
            )
