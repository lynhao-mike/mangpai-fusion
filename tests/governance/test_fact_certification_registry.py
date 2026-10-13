from __future__ import annotations

from pathlib import Path

import pytest

from engine.governance.canonical import canonical_digest, stable_object_id
from engine.governance.fact_values import DigestRef, FactLevel


_SCHEMA_VERSION = "multi-school-governance/v1"


def _entry(
    *,
    level: str = "certified_technical",
    status: str = "published",
    version: str = "1.0.0",
    reviews: tuple[str, ...] = (),
    fact_kind: str = "chart.ten_god_map",
) -> dict[str, str | list[str]]:
    ordered_reviews = tuple(sorted(reviews))
    identity = (level, fact_kind, "engine.ten_god", version, "facts/v1")
    registration_id = str(
        stable_object_id("fact_certification", (identity, status, ordered_reviews))
    )
    material = (
        "governance.fact-certification.v1",
        registration_id,
        *identity,
        status,
        ordered_reviews,
    )
    return {
        "registration_id": registration_id,
        "certification_level": level,
        "fact_kind": fact_kind,
        "calculator_id": "engine.ten_god",
        "calculator_version": version,
        "schema_version": "facts/v1",
        "publication_status": status,
        "specification_digest": str(DigestRef.from_material(material).value),
        "cross_school_review_refs": list(ordered_reviews),
    }


def _write_registry(tmp_path: Path, entries: list[dict[str, str | list[str]]]) -> Path:
    lines = [
        f"schema_version: {_SCHEMA_VERSION}",
        "certifications: []" if not entries else "certifications:",
    ]
    for entry in entries:
        for key, value in entry.items():
            match value:
                case str():
                    lines.append(
                        f"  - {key}: {value}"
                        if key == "registration_id"
                        else f"    {key}: {value}"
                    )
                case list():
                    lines.append(f"    {key}: []" if not value else f"    {key}:")
                    lines.extend(f"      - {item}" for item in value)
                case unreachable:
                    raise AssertionError(f"unsupported fixture value: {unreachable!r}")
    lines.extend(
        (
            "schools:",
            "  - ziping",
            "  - gao_dechen",
            "  - duan_jianye",
            "  - yang_qingjuan",
            "  - ren_fuhong",
            "legacy_compatibility_sources:",
            "  - ditiansui",
            "capabilities: []",
        )
    )
    path = tmp_path / "theory" / "registry.yaml"
    path.parent.mkdir()
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_loads_published_l2a_and_returns_unsupported_for_exact_missing_version(
    tmp_path: Path,
) -> None:
    from engine.governance.registries import (
        CertificationIdentity,
        FactCertification,
        UnsupportedFactCertification,
        load_fact_certification_registry,
    )

    # Given: explicit L2A and L2B registrations with their distinct required evidence.
    _write_registry(
        tmp_path,
        [
            _entry(),
            _entry(
                level="certified_cross_school",
                fact_kind="chart.pillar_relation",
                reviews=(
                    "review:ziping:2026-08-03",
                    "review:ren_fuhong:2026-08-03",
                ),
            ),
        ],
    )

    # When: the exact registered and an adjacent unregistered version are queried.
    registry = load_fact_certification_registry(
        Path("theory/registry.yaml"), workspace_root=tmp_path
    )
    registered = registry.lookup(
        CertificationIdentity(
            FactLevel.CERTIFIED_TECHNICAL,
            "chart.ten_god_map",
            "engine.ten_god",
            "1.0.0",
            "facts/v1",
        )
    )
    missing = registry.lookup(
        CertificationIdentity(
            FactLevel.CERTIFIED_TECHNICAL,
            "chart.ten_god_map",
            "engine.ten_god",
            "1.0.1",
            "facts/v1",
        )
    )
    cross_school = registry.lookup(
        CertificationIdentity(
            FactLevel.CERTIFIED_CROSS_SCHOOL,
            "chart.pillar_relation",
            "engine.ten_god",
            "1.0.0",
            "facts/v1",
        )
    )

    # Then: published certification is returned and no neighbor fallback occurs.
    assert isinstance(registered, FactCertification)
    assert isinstance(cross_school, FactCertification)
    assert isinstance(missing, UnsupportedFactCertification)
    assert missing.issue_code == "CERTIFICATION.UNSUPPORTED"


def test_keeps_l2a_and_l2b_semantics_strictly_separate(tmp_path: Path) -> None:
    from engine.governance.registries import (
        CertificationContractError,
        load_fact_certification_registry,
    )

    # Given: an L2A entry pretending to carry cross-school consensus references.
    registry_path = _write_registry(
        tmp_path,
        [_entry(reviews=("review:ziping:2026-08-03", "review:ren:2026-08-03"))],
    )

    # When: the registry is loaded.
    with pytest.raises(CertificationContractError, match="L2A"):
        load_fact_certification_registry(
            Path("theory/registry.yaml"), workspace_root=tmp_path
        )

    # Then: L2A cannot impersonate cross-school consensus.
    assert registry_path.exists()


def test_rejects_short_school_aliases_in_l2b_review_refs(tmp_path: Path) -> None:
    from engine.governance.registries import (
        CertificationContractError,
        load_fact_certification_registry,
    )

    # Given: a published L2B entry using short aliases instead of canonical peer IDs.
    _write_registry(
        tmp_path,
        [
            _entry(
                level="certified_cross_school",
                reviews=("review:ziping:2026-08-03", "review:ren:2026-08-03"),
            )
        ],
    )

    # When / Then: loading fails closed.
    with pytest.raises(CertificationContractError, match="canonical peer"):
        load_fact_certification_registry(
            Path("theory/registry.yaml"), workspace_root=tmp_path
        )


@pytest.mark.parametrize("status", ["candidate", "proposed"])
def test_does_not_consume_candidate_or_proposed_certifications(
    tmp_path: Path, status: str
) -> None:
    from engine.governance.registries import (
        CertificationIdentity,
        UnsupportedFactCertification,
        load_fact_certification_registry,
    )

    # Given: a non-published technical registration.
    _write_registry(tmp_path, [_entry(status=status)])

    # When: it is queried as a certified fact.
    registry = load_fact_certification_registry(
        Path("theory/registry.yaml"), workspace_root=tmp_path
    )
    result = registry.lookup(
        CertificationIdentity(
            FactLevel.CERTIFIED_TECHNICAL,
            "chart.ten_god_map",
            "engine.ten_god",
            "1.0.0",
            "facts/v1",
        )
    )

    # Then: the result remains explicitly unsupported.
    assert isinstance(result, UnsupportedFactCertification)


@pytest.mark.parametrize(
    "mutation",
    ["duplicate", "identity_conflict", "unknown_status", "tamper", "bool_scalar"],
)
def test_rejects_invalid_or_tampered_registry_entries(
    tmp_path: Path, mutation: str
) -> None:
    from engine.governance.registries import (
        CertificationContractError,
        load_fact_certification_registry,
    )

    # Given: an invalid registry entry shape or binding.
    first = _entry()
    match mutation:
        case "duplicate":
            entries = [first, first]
        case "identity_conflict":
            second = _entry(status="candidate")
            entries = [first, second]
        case "unknown_status":
            first["publication_status"] = "mystery"
            entries = [first]
        case "tamper":
            first["specification_digest"] = str(canonical_digest(("tampered",)))
            entries = [first]
        case "bool_scalar":
            entries = [first]
        case unreachable:
            raise AssertionError(f"unsupported mutation: {unreachable}")
    registry_path = _write_registry(tmp_path, entries)
    if mutation == "bool_scalar":
        registry_path.write_text(
            "schema_version: multi-school-governance/v1\ncertifications: false\n",
            encoding="utf-8",
        )

    # When / Then: malformed registrations cannot load.
    with pytest.raises(CertificationContractError):
        load_fact_certification_registry(
            Path("theory/registry.yaml"), workspace_root=tmp_path
        )


def test_rejects_path_escape_absolute_paths_and_symlink_escape(tmp_path: Path) -> None:
    from engine.governance.registries import (
        CertificationContractError,
        load_fact_certification_registry,
    )

    # Given: paths that are not an explicit regular file below the workspace root.
    external = tmp_path.parent / "outside-registry.yaml"
    external.write_text(
        "schema_version: multi-school-governance/v1\ncertifications: []\n",
        encoding="utf-8",
    )
    link = tmp_path / "theory" / "linked.yaml"
    link.parent.mkdir()
    try:
        link.symlink_to(external)
    except OSError as error:
        pytest.skip(f"symlink creation unavailable: {error}")

    # When / Then: every escape form is rejected.
    for candidate in (
        Path("../outside-registry.yaml"),
        external,
        Path("theory/linked.yaml"),
    ):
        with pytest.raises(CertificationContractError):
            load_fact_certification_registry(candidate, workspace_root=tmp_path)


def test_exposes_no_mutating_registry_operations(tmp_path: Path) -> None:
    from engine.governance.registries import load_fact_certification_registry

    # Given: a loaded empty formal registry.
    _write_registry(tmp_path, [])

    # When: its public operations are inspected.
    registry = load_fact_certification_registry(
        Path("theory/registry.yaml"), workspace_root=tmp_path
    )

    # Then: only immutable data and lookup are available, never publish/promote mutation.
    assert registry.registrations == ()
    assert not any(
        name in dir(registry) for name in ("publish", "promote", "append", "add")
    )
