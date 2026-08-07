from __future__ import annotations

from dataclasses import replace
from itertools import permutations
from pathlib import Path

import pytest

from engine.governance import (
    ClaimKind,
    ClaimStance,
    DigestRef,
    TemporalLayer,
    TemporalScope,
)
from tests.governance.composition_fixtures import claim as _claim


def test_synthetic_template_executes_only_with_explicit_shadow_authority() -> None:
    from engine.governance.composition import (
        CompositionExecutionMode,
        execute_composition,
        load_composition_registry,
    )

    # Given: the one registered synthetic-only template and independent components.
    registry = load_composition_registry(Path("theory/multi-school-governance-v1.yaml"))
    claims = (_claim("ziping"), _claim("gao_dechen"))

    # When: equivalent component orderings execute under explicit shadow authority.
    outputs = tuple(
        execute_composition(
            registry,
            template_id="synthetic.structure-consensus",
            version="1.0.0",
            components=ordered,
            mode=CompositionExecutionMode.SHADOW,
        )
        for ordered in permutations(claims)
    )

    # Then: replay is canonical and preserves components without creating a claim.
    assert len({output.content_digest for output in outputs}) == 1
    assert outputs[0].component_claim_ids == tuple(
        sorted(claim.claim_id for claim in claims)
    )
    assert outputs[0].output_kind is ClaimKind.STRUCTURE


def test_synthetic_template_rejects_production_execution() -> None:
    from engine.governance.composition import (
        CompositionExecutionMode,
        CompositionResult,
        execute_composition,
        load_composition_registry,
    )

    # Given: a synthetic-only template and a complete component set.
    registry = load_composition_registry(Path("theory/multi-school-governance-v1.yaml"))

    # When: production authority is explicitly requested.
    result = execute_composition(
        registry,
        template_id="synthetic.structure-consensus",
        version="1.0.0",
        components=(_claim("ziping"), _claim("gao_dechen")),
        mode=CompositionExecutionMode.PRODUCTION,
    )

    # Then: it produces a typed non-claim refusal.
    assert isinstance(result, CompositionResult)
    assert result.issue_code == "COMPOSITION.PRODUCTION_FORBIDDEN"


def test_unknown_version_and_missing_component_return_typed_non_claim_outcomes() -> (
    None
):
    from engine.governance.composition import (
        CompositionExecutionMode,
        CompositionOutcome,
        execute_composition,
        load_composition_registry,
    )

    # Given: the formal registry and one otherwise compatible component.
    registry = load_composition_registry(Path("theory/multi-school-governance-v1.yaml"))

    # When: exact version lookup misses and the known template lacks its second slot.
    unknown = execute_composition(
        registry,
        template_id="synthetic.structure-consensus",
        version="1.0.1",
        components=(_claim("ziping"),),
        mode=CompositionExecutionMode.SHADOW,
    )
    incomplete = execute_composition(
        registry,
        template_id="synthetic.structure-consensus",
        version="1.0.0",
        components=(_claim("ziping"),),
        mode=CompositionExecutionMode.SHADOW,
    )

    # Then: neither path manufactures a new central claim.
    assert (unknown.outcome, unknown.issue_code) == (
        CompositionOutcome.UNSUPPORTED,
        "COMPOSITION.UNSUPPORTED_TEMPLATE",
    )
    assert (incomplete.outcome, incomplete.issue_code) == (
        CompositionOutcome.CONDITIONAL,
        "COMPOSITION.COMPONENTS_REQUIRED",
    )


def test_temporal_incompatibility_and_strong_contradiction_are_deterministic() -> None:
    from engine.governance.composition import (
        CompositionExecutionMode,
        CompositionOutcome,
        execute_composition,
        load_composition_registry,
    )

    # Given: components that differ by temporal scope and by explicit stance.
    registry = load_composition_registry(Path("theory/multi-school-governance-v1.yaml"))

    # When: each pair enters the same closed synthetic template.
    temporal = execute_composition(
        registry,
        template_id="synthetic.structure-consensus",
        version="1.0.0",
        components=(
            _claim("ziping"),
            _claim(
                "gao_dechen",
                temporal_scope=TemporalScope(TemporalLayer.LIUNIAN, target_year=2026),
            ),
        ),
        mode=CompositionExecutionMode.SHADOW,
    )
    contradiction = execute_composition(
        registry,
        template_id="synthetic.structure-consensus",
        version="1.0.0",
        components=(_claim("ziping"), _claim("gao_dechen", stance=ClaimStance.OPPOSE)),
        mode=CompositionExecutionMode.SHADOW,
    )

    # Then: scope never broadens and direct contradiction routes to review.
    assert (temporal.outcome, temporal.issue_code) == (
        CompositionOutcome.CONFLICT,
        "COMPOSITION.TEMPORAL_INCOMPATIBLE",
    )
    assert (contradiction.outcome, contradiction.issue_code) == (
        CompositionOutcome.HUMAN_REVIEW,
        "COMPOSITION.STRONG_CONTRADICTION",
    )


def test_result_digest_and_execution_mode_boundaries_fail_closed() -> None:
    from engine.governance.composition import (
        CompositionContractError,
        CompositionExecutionMode,
        CompositionTemplate,
        execute_composition,
        load_composition_registry,
    )

    # Given: a valid composed result and its exact public construction material.
    registry = load_composition_registry(Path("theory/multi-school-governance-v1.yaml"))
    baseline = execute_composition(
        registry,
        template_id="synthetic.structure-consensus",
        version="1.0.0",
        components=(_claim("ziping"), _claim("gao_dechen")),
        mode=CompositionExecutionMode.SHADOW,
    )

    # When / Then: forged output digest is rejected at the public boundary.
    with pytest.raises(CompositionContractError, match="RESULT_DIGEST"):
        baseline.__class__(
            baseline.outcome,
            baseline.template_id,
            baseline.template_version,
            DigestRef.from_material(("forged",)),
            baseline.components,
            baseline.output_kind,
            baseline.output_scope,
            baseline.evidence_grade,
            baseline.issue_code,
        )
    template = registry.lookup("synthetic.structure-consensus", "1.0.0")
    assert isinstance(template, CompositionTemplate)
    with pytest.raises(CompositionContractError, match="DIGEST"):
        replace(template, specification_digest=DigestRef.from_material(("forged",)))


def test_template_constructor_rejects_raw_enum_like_values_with_typed_error() -> None:
    from engine.governance.composition import (
        CompositionContractError,
        CompositionTemplate,
        load_composition_registry,
    )

    # Given: a trusted parsed template that supplies all otherwise valid fields.
    template = load_composition_registry().lookup(
        "synthetic.structure-consensus", "1.0.0"
    )
    assert isinstance(template, CompositionTemplate)

    # When / Then: raw enum-like boundary values cannot escape as AttributeError.
    with pytest.raises(CompositionContractError):
        replace(template, output_kind="structure")
    with pytest.raises(CompositionContractError):
        replace(template, evidence_cap="corroborated")


@pytest.mark.parametrize(
    "unknown_field",
    ("callback", "expression", "predicate", "module_path"),
)
def test_loader_rejects_non_closed_template_fields(
    tmp_path: Path, unknown_field: str
) -> None:
    from engine.governance.composition import (
        CompositionContractError,
        load_composition_registry,
    )

    # Given: an exact valid baseline is copied before one forbidden field is injected.
    path = tmp_path / "theory" / "registry.yaml"
    path.parent.mkdir()
    baseline = Path("theory/multi-school-governance-v1.yaml").read_text(
        encoding="utf-8"
    )
    path.write_text(baseline, encoding="utf-8")
    assert load_composition_registry(
        Path("theory/registry.yaml"), workspace_root=tmp_path
    )

    # When: one dynamic execution escape hatch is appended to the valid template.
    injected = baseline.replace(
        "    version: 1.0.0\n",
        f"    version: 1.0.0\n    {unknown_field}: unsafe\n",
        1,
    )
    path.write_text(injected, encoding="utf-8")

    # Then: that exact extra field causes the fail-closed schema rejection.
    with pytest.raises(CompositionContractError) as raised:
        load_composition_registry(Path("theory/registry.yaml"), workspace_root=tmp_path)
    assert raised.value.issue_code == "COMPOSITION.YAML_FIELDS"
    assert raised.value.field_path == "composition_templates[0]"
