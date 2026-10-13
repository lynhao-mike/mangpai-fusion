from __future__ import annotations

from engine.governance import ClaimEvidenceGrade, ClaimReference, ClaimReferenceCategory
from engine.governance.composition import (
    CompositionExecutionMode,
    CompositionOutcome,
    execute_composition,
    load_composition_registry,
)
from tests.governance.composition_fixtures import claim


def test_duplicate_component_cannot_satisfy_independent_support() -> None:
    # Given: the same valid GovernanceClaim repeats for both required slots.
    registry = load_composition_registry()
    component = claim("ziping")

    # When: the closed template evaluates the repeated component tuple.
    result = execute_composition(
        registry,
        template_id="synthetic.structure-consensus",
        version="1.0.0",
        components=(component, component),
        mode=CompositionExecutionMode.SHADOW,
    )

    # Then: one component cannot create independent support.
    assert (result.outcome, result.issue_code) == (
        CompositionOutcome.CONDITIONAL,
        "COMPOSITION.INDEPENDENT_COMPONENTS_REQUIRED",
    )


def test_evidence_cap_and_component_evidence_are_preserved() -> None:
    # Given: direct components and a template capped at corroborated evidence.
    registry = load_composition_registry()

    # When: the compatible components execute under explicit shadow authority.
    result = execute_composition(
        registry,
        template_id="synthetic.structure-consensus",
        version="1.0.0",
        components=(claim("ziping"), claim("gao_dechen")),
        mode=CompositionExecutionMode.SHADOW,
    )

    # Then: the output cannot exceed the registered evidence cap.
    assert result.evidence_grade is ClaimEvidenceGrade.CORROBORATED


def test_counterevidence_and_falsifier_survive_component_retention() -> None:
    # Given: one component carries registered contrary evidence and a falsifier.
    registry = load_composition_registry()
    counter = ClaimReference(ClaimReferenceCategory.FACT, "counter", "v1")
    component = claim(
        "ziping",
        counterevidence=(counter,),
        falsifier="a registered contrary result invalidates this composition",
    )

    # When: it composes with a distinct peer component.
    result = execute_composition(
        registry,
        template_id="synthetic.structure-consensus",
        version="1.0.0",
        components=(component, claim("gao_dechen")),
        mode=CompositionExecutionMode.SHADOW,
    )

    # Then: the complete original component envelope remains observable.
    retained = next(item for item in result.components if item.school_id == "ziping")
    assert retained.counterevidence == (counter,)
    assert (
        retained.falsifier
        == "a registered contrary result invalidates this composition"
    )
