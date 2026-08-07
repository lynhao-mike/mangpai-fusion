from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from engine.predicates.ten_god_structure_types import TenGodStructureKind


CATALOG_PATH = Path("theory/ziping/structure-catalog-v1.yaml")


def test_structure_catalog_freezes_exactly_thirty_stable_entries() -> None:
    from engine.governance.structure_catalog import (
        ImplementationStatus,
        StructureFamily,
        load_structure_catalog,
    )

    # Given: the frozen Ziping structure catalog.
    catalog = load_structure_catalog(CATALOG_PATH)

    # When: entries are grouped by their stable family.
    family_counts = {
        family: sum(1 for entry in catalog.entries if entry.family is family)
        for family in StructureFamily
    }

    # Then: the catalog is the exact 13/5/3/9 closure and only three are current.
    assert len(catalog.entries) == 30
    assert len({entry.structure_id for entry in catalog.entries}) == 30
    assert len({entry.canonical_key for entry in catalog.entries}) == 30
    assert family_counts == {
        StructureFamily.FLOW_PROTECTION: 13,
        StructureFamily.CONTROL_TRANSFORMATION: 5,
        StructureFamily.CLEARING: 3,
        StructureFamily.DAMAGE_IMBALANCE: 9,
    }
    assert {
        entry.structure_id
        for entry in catalog.entries
        if entry.implementation_status is ImplementationStatus.CURRENT_IMPLEMENTED
    } == {
        "food_god_controls_killing",
        "hurting_officer_controls_killing",
        "killing_generates_seal",
    }


def test_structure_catalog_fields_are_complete_and_closed() -> None:
    from engine.governance.structure_catalog import load_structure_catalog

    # Given: every catalog item crosses the YAML trust boundary.
    catalog = load_structure_catalog(CATALOG_PATH)

    # When / Then: parsed entries expose complete typed fields, not raw YAML data.
    for entry in catalog.entries:
        assert entry.display_name_zh
        assert entry.required_roles
        assert entry.candidate_types
        assert entry.source_refs
        assert entry.content_digest.value
        assert entry.source_status.value
        assert entry.implementation_status.value
        assert tuple(entry.block_types)
        assert tuple(entry.damage_types)


def test_legacy_projection_maps_only_current_three_structure_kinds() -> None:
    from engine.governance.structure_catalog import load_structure_catalog

    # Given: the old enum remains a three-value compatibility surface.
    catalog = load_structure_catalog(CATALOG_PATH)

    # When: legacy mappings are projected.
    projection = catalog.legacy_projection

    # Then: every old enum has one target and no catalog-only item is backfilled.
    assert set(projection) == set(TenGodStructureKind)
    assert projection[TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING] == (
        "food_god_controls_killing"
    )
    assert projection[TenGodStructureKind.HURTING_OFFICER_CONTROLS_KILLING] == (
        "hurting_officer_controls_killing"
    )
    assert projection[TenGodStructureKind.KILLING_GENERATES_SEAL] == (
        "killing_generates_seal"
    )


def test_catalog_digest_ignores_order_but_tracks_display_changes(
    tmp_path: Path,
) -> None:
    from engine.governance.structure_catalog import load_structure_catalog

    # Given: the same catalog entries can be represented in another YAML order.
    baseline_text = CATALOG_PATH.read_text(encoding="utf-8")
    baseline = load_structure_catalog(CATALOG_PATH)
    reversed_path = tmp_path / "reversed.yaml"
    blocks = baseline_text.split("  - structure_id: ")
    header = blocks[0]
    entries = [f"  - structure_id: {block}" for block in blocks[1:]]
    reversed_path.write_text(header + "".join(reversed(entries)), encoding="utf-8")

    # When: order changes without changing item content.
    reordered = load_structure_catalog(reversed_path, workspace_root=tmp_path)

    # Then: the digest and stable IDs remain frozen.
    assert reordered.content_digest == baseline.content_digest
    assert {entry.structure_id for entry in reordered.entries} == {
        entry.structure_id for entry in baseline.entries
    }

    # When: display text changes while stable ID is preserved.
    renamed_path = tmp_path / "renamed.yaml"
    renamed_path.write_text(
        baseline_text.replace(
            "display_name_zh: 官印相生",
            "display_name_zh: 官印相生X",
            1,
        ),
        encoding="utf-8",
    )
    renamed = load_structure_catalog(renamed_path, workspace_root=tmp_path)

    # Then: ID compatibility is unchanged but the content digest changes.
    assert renamed.entries[0].structure_id == baseline.entries[0].structure_id
    assert renamed.content_digest != baseline.content_digest


@pytest.mark.parametrize(
    ("mutation", "issue_code"),
    (
        (
            lambda text: text.replace(
                "structure_id: killing_generates_seal",
                "structure_id: officer_generates_seal",
                1,
            ),
            "STRUCTURE.DUPLICATE_ID",
        ),
        (
            lambda text: text.replace(
                "canonical_key: killing_generates_seal",
                "canonical_key: officer_generates_seal",
                1,
            ),
            "STRUCTURE.DUPLICATE_KEY",
        ),
        (
            lambda text: text.replace(
                "legacy_mapping: null",
                "legacy_mapping: not_a_legacy_kind",
                1,
            ),
            "STRUCTURE.LEGACY_MAPPING",
        ),
        (
            lambda text: text.replace(
                "legacy_mapping: null",
                "legacy_mapping: KILLING_GENERATES_SEAL",
                1,
            ),
            "STRUCTURE.LEGACY_DUPLICATE",
        ),
        (
            lambda text: text.replace(
                "legacy_mapping: KILLING_GENERATES_SEAL",
                "legacy_mapping: null",
                1,
            ).replace(
                "legacy_mapping: null",
                "legacy_mapping: KILLING_GENERATES_SEAL",
                1,
            ),
            "STRUCTURE.LEGACY_TARGET",
        ),
        (
            lambda text: text.replace("    source_status: normalized\n", "", 1),
            "STRUCTURE.YAML_FIELDS",
        ),
        (
            lambda text: text.replace(
                "source_status: normalized",
                "source_status: invented",
                1,
            ),
            "STRUCTURE.SOURCE_STATUS",
        ),
    ),
)
def test_catalog_loader_fails_closed_for_invalid_yaml_matrix(
    tmp_path: Path,
    mutation: Callable[[str], str],
    issue_code: str,
) -> None:
    from engine.governance.structure_catalog import (
        StructureCatalogContractError,
        load_structure_catalog,
    )

    # Given: one exact invalid catalog mutation.
    invalid_path = tmp_path / "invalid.yaml"
    invalid_path.write_text(
        mutation(CATALOG_PATH.read_text(encoding="utf-8")),
        encoding="utf-8",
    )

    # When / Then: the loader rejects the catalog with the named typed issue.
    with pytest.raises(StructureCatalogContractError) as raised:
        load_structure_catalog(invalid_path, workspace_root=tmp_path)
    assert raised.value.issue_code == issue_code


def test_loading_structure_catalog_has_no_production_side_effects() -> None:
    from engine.governance.structure_catalog import load_structure_catalog

    # Given: the production loaders are not part of this catalog boundary.
    before = set(sys.modules)

    # When: the catalog is loaded through its public API.
    catalog = load_structure_catalog(CATALOG_PATH)
    imported = set(sys.modules) - before

    # Then: it returns a read-only catalog and does not import production entrypoints.
    assert len(catalog.entries) == 30
    assert "engine.application.production_rule_loader" not in imported
    assert "engine.application.production_rule_triggers" not in imported
