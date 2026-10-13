from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from engine.governance import ClaimEvidenceGrade, ClaimKind


def test_peer_registry_contains_exactly_five_canonical_schools_in_stable_order() -> (
    None
):
    from engine.governance.registries import load_school_registry

    # Given: the formal Wave 1 governance registry.
    registry = load_school_registry(workspace_root=Path.cwd())

    # When: its peer schools are read through the readonly boundary.
    school_ids = registry.peer_school_ids

    # Then: only the approved canonical peer IDs appear in deterministic order.
    assert school_ids == (
        "ziping",
        "gao_dechen",
        "duan_jianye",
        "yang_qingjuan",
        "ren_fuhong",
    )
    with pytest.raises(FrozenInstanceError):
        registry.__setattr__("peer_school_ids", ())


def test_ditiansui_is_legacy_compatibility_not_a_peer_role() -> None:
    from engine.governance.registries import (
        LegacyCompatibilitySource,
        load_school_registry,
    )

    # Given: the formal five-peer registry.
    registry = load_school_registry(workspace_root=Path.cwd())

    # When: the legacy Ditiansui source is queried by its exact canonical spelling.
    source = registry.lookup_school("ditiansui")

    # Then: it remains a compatibility source and exposes no peer-arbitration role.
    assert isinstance(source, LegacyCompatibilitySource)
    assert source.source_id == "ditiansui"
    assert not hasattr(source, "role")


@pytest.mark.parametrize(
    ("raw", "canonical"),
    (
        ("gao", "gao_dechen"),
        ("duan", "duan_jianye"),
        ("yang", "yang_qingjuan"),
        ("ren", "ren_fuhong"),
    ),
)
def test_boundary_aliases_normalize_only_exact_explicit_input(
    raw: str, canonical: str
) -> None:
    from engine.governance.registries import (
        SchoolRegistryContractError,
        load_school_registry,
        normalize_school_input,
    )

    # Given: an explicit boundary-only alias and a canonical registry.
    registry = load_school_registry(workspace_root=Path.cwd())

    # When: the alias is normalized before entering the canonical query boundary.
    normalized = normalize_school_input(raw)

    # Then: it maps exactly once, while case variants and substrings fail closed.
    assert normalized == canonical
    assert registry.lookup_school(raw).issue_code == "SCHOOL.UNKNOWN"
    for rejected in (raw.upper(), f"{raw}_extra", f" {raw}"):
        with pytest.raises(SchoolRegistryContractError):
            normalize_school_input(rejected)


def test_capability_query_requires_exact_complete_identity_and_abstains_without_fallback() -> (
    None
):
    from engine.governance.registries import (
        CapabilityAbstention,
        SchoolRegistryContractError,
        load_school_registry,
    )

    # Given: the formal registry has no conservatively publishable capabilities yet.
    registry = load_school_registry(workspace_root=Path.cwd())

    # When: an exact, complete identity is queried.
    from engine.governance.registries import CapabilityIdentity

    result = registry.lookup_capability(
        CapabilityIdentity(
            school_id="ziping",
            task_id="structure.assessment",
            claim_kind=ClaimKind.STRUCTURE,
            evidence_grade=ClaimEvidenceGrade.CORROBORATED,
            version="governance/v1",
        )
    )

    # Then: lack of an exact registration is typed abstention with reason and source.
    assert isinstance(result, CapabilityAbstention)
    assert result.reason_issue.code == "CAPABILITY.UNREGISTERED"
    assert result.source == "school_registry"
    for kwargs in (
        {"school_id": "gao"},
        {"task_id": ""},
        {"version": ""},
    ):
        with pytest.raises(SchoolRegistryContractError):
            from engine.governance.registries import CapabilityIdentity

            CapabilityIdentity(
                school_id=kwargs.get("school_id", "ziping"),
                task_id=kwargs.get("task_id", "structure.assessment"),
                claim_kind=ClaimKind.STRUCTURE,
                evidence_grade=ClaimEvidenceGrade.CORROBORATED,
                version=kwargs.get("version", "governance/v1"),
            )


def test_evidence_only_capability_is_never_winner_eligible(tmp_path: Path) -> None:
    from engine.governance.registries import (
        CapabilityQualification,
        load_school_registry,
    )

    # Given: a published exact capability whose role is restricted to evidence.
    path = tmp_path / "theory" / "registry.yaml"
    path.parent.mkdir()
    path.write_text(
        "\n".join(
            (
                "schema_version: multi-school-governance/v1",
                "certifications: []",
                "schools:",
                "  - ziping",
                "  - gao_dechen",
                "  - duan_jianye",
                "  - yang_qingjuan",
                "  - ren_fuhong",
                "legacy_compatibility_sources:",
                "  - ditiansui",
                "capabilities:",
                "  - school_id: ziping",
                "    task_id: structure.assessment",
                "    claim_kind: structure",
                "    evidence_grade: corroborated",
                "    version: governance/v1",
                "    role: evidence_only",
                "    publication_status: published",
                "composition_templates: []",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    # When: the exact identity is queried through the loaded registry.
    from engine.governance.registries import CapabilityIdentity

    result = load_school_registry(
        Path("theory/registry.yaml"), workspace_root=tmp_path
    ).lookup_capability(
        CapabilityIdentity(
            school_id="ziping",
            task_id="structure.assessment",
            claim_kind=ClaimKind.STRUCTURE,
            evidence_grade=ClaimEvidenceGrade.CORROBORATED,
            version="governance/v1",
        )
    )

    # Then: it may contribute evidence but cannot be selected as an independent winner.
    assert isinstance(result, CapabilityQualification)
    assert result.role.value == "evidence_only"
    assert result.winner_eligible is False


@pytest.mark.parametrize(
    "payload",
    (
        "schools: [ziping, ziping]",
        "schools: [ziping, gao_dechen, duan_jianye, yang_qingjuan, ren_fuhong, ditiansui]",
        "schools: false",
        "schools: [ziping]\nschools: [ziping]",
    ),
)
def test_loader_rejects_tampered_or_duplicate_school_registry_data(
    tmp_path: Path, payload: str
) -> None:
    from engine.governance.registries import (
        SchoolRegistryContractError,
        load_school_registry,
    )

    # Given: a syntactically plausible registry with an invalid school declaration.
    path = tmp_path / "theory" / "registry.yaml"
    path.parent.mkdir()
    path.write_text(
        "schema_version: multi-school-governance/v1\n"
        "certifications: []\n"
        f"{payload}\n"
        "legacy_compatibility_sources: [ditiansui]\n"
        "capabilities: []\n"
        "composition_templates: []\n",
        encoding="utf-8",
    )

    # When / Then: formal loading rejects it rather than normalizing or guessing.
    with pytest.raises(SchoolRegistryContractError):
        load_school_registry(Path("theory/registry.yaml"), workspace_root=tmp_path)
