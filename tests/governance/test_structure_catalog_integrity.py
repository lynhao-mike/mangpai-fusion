from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

import pytest

from engine.predicates.ten_god_structure_types import TenGodStructureKind


CATALOG_PATH = Path("theory/ziping/structure-catalog-v1.yaml")


def test_entry_constructor_rejects_forged_digest_and_raw_fields() -> None:
    from engine.governance import DigestRef
    from engine.governance.structure_catalog import (
        StructureCatalogContractError,
        load_structure_catalog,
    )
    from engine.governance.structure_catalog_types import StructureCatalogEntry

    # Given: a trusted entry parsed through the real YAML boundary.
    entry = load_structure_catalog(CATALOG_PATH).entries[0]

    # When / Then: forged content digests are rejected.
    with pytest.raises(StructureCatalogContractError) as forged:
        StructureCatalogEntry(
            entry.structure_id,
            entry.canonical_key,
            entry.display_name_zh,
            entry.family,
            entry.required_roles,
            entry.candidate_types,
            entry.clear_types,
            entry.block_types,
            entry.damage_types,
            entry.source_status,
            entry.implementation_status,
            entry.legacy_mapping,
            entry.source_refs,
            DigestRef.from_material(("forged",)),
        )
    assert forged.value.issue_code == "STRUCTURE.ENTRY_DIGEST"

    # When / Then: raw enum-like strings and mutable collections cannot enter.
    with pytest.raises(StructureCatalogContractError) as raw_family:
        StructureCatalogEntry(
            entry.structure_id,
            entry.canonical_key,
            entry.display_name_zh,
            "flow_protection",
            entry.required_roles,
            entry.candidate_types,
            entry.clear_types,
            entry.block_types,
            entry.damage_types,
            entry.source_status,
            entry.implementation_status,
            entry.legacy_mapping,
            entry.source_refs,
            entry.content_digest,
        )
    assert raw_family.value.issue_code == "STRUCTURE.ENTRY_TYPE"

    with pytest.raises(StructureCatalogContractError) as mutable_roles:
        StructureCatalogEntry(
            entry.structure_id,
            entry.canonical_key,
            entry.display_name_zh,
            entry.family,
            list(entry.required_roles),
            entry.candidate_types,
            entry.clear_types,
            entry.block_types,
            entry.damage_types,
            entry.source_status,
            entry.implementation_status,
            entry.legacy_mapping,
            entry.source_refs,
            entry.content_digest,
        )
    assert mutable_roles.value.issue_code == "STRUCTURE.ENTRY_TYPE"


def test_catalog_constructor_rejects_forged_digest_projection_and_entries() -> None:
    from engine.governance import DigestRef
    from engine.governance.structure_catalog import (
        StructureCatalogContractError,
        load_structure_catalog,
    )
    from engine.governance.structure_catalog_types import StructureCatalog

    # Given: a trusted catalog parsed through the real YAML boundary.
    catalog = load_structure_catalog(CATALOG_PATH)

    # When / Then: forged catalog digest cannot bind to real entries.
    with pytest.raises(StructureCatalogContractError) as forged:
        StructureCatalog(
            catalog.schema_version,
            catalog.entries,
            catalog.legacy_projection,
            DigestRef.from_material(("forged",)),
        )
    assert forged.value.issue_code == "STRUCTURE.CATALOG_DIGEST"

    # When / Then: mutable projections and wrong known enum targets fail closed.
    with pytest.raises(StructureCatalogContractError) as mutable_projection:
        StructureCatalog(
            catalog.schema_version,
            catalog.entries,
            dict(catalog.legacy_projection),
            catalog.content_digest,
        )
    assert mutable_projection.value.issue_code == "STRUCTURE.CATALOG_TYPE"

    wrong_projection = MappingProxyType(
        {
            TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING: "killing_generates_seal",
            TenGodStructureKind.HURTING_OFFICER_CONTROLS_KILLING: (
                "hurting_officer_controls_killing"
            ),
            TenGodStructureKind.KILLING_GENERATES_SEAL: "food_god_controls_killing",
        }
    )
    with pytest.raises(StructureCatalogContractError) as wrong_target:
        StructureCatalog(
            catalog.schema_version,
            catalog.entries,
            wrong_projection,
            catalog.content_digest,
        )
    assert wrong_target.value.issue_code == "STRUCTURE.LEGACY_TARGET"

    with pytest.raises(StructureCatalogContractError) as nested_entry:
        StructureCatalog(
            catalog.schema_version,
            ("not-entry",),
            catalog.legacy_projection,
            catalog.content_digest,
        )
    assert nested_entry.value.issue_code == "STRUCTURE.CATALOG_TYPE"
