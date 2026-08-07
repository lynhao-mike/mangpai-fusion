from __future__ import annotations

from itertools import permutations

import pytest

from engine.governance import (
    ClaimIssue,
    ClaimIssueCode,
    ClaimReference,
    ClaimReferenceCategory,
)
from engine.governance.arbitration import (
    ArbitrationDecision,
    ArbitrationContractError,
    ArbitrationIntegrityError,
    ArbitrationResult,
    ClaimVariantRef,
    CounterevidenceTrace,
    FactConflictContext,
    arbitrate,
)
from tests.governance.test_arbitration_gates import _arena, _claim


def test_arbitration_is_permutation_invariant_and_idempotent() -> None:
    # Given: two independently qualified claims.
    first = _claim()
    second = _claim(school="gao_dechen")
    outputs = []

    # When: each input ordering is independently arbitrated twice.
    for ordered in permutations((first, second)):
        outputs.append((arbitrate(_arena(*ordered)), arbitrate(_arena(*ordered))))

    # Then: every replay exposes the same decision and immutable digest.
    assert all(left == right for left, right in outputs)
    assert len({output[0].content_digest for output in outputs}) == 1


def test_duplicate_same_source_claim_cannot_raise_independent_strength() -> None:
    # Given: a source claim and an exact duplicate from the same evidence family.
    claim = _claim()
    baseline = arbitrate(_arena(claim))

    # When: duplicate input is submitted to a new immutable arena.
    copied = arbitrate(_arena(claim, claim))

    # Then: independent grouping stays constant while the original claim stays retained.
    assert baseline.independent_group_count == copied.independent_group_count == 1
    assert copied.retained_variants == (ClaimVariantRef.from_claim(claim),)


def test_public_variant_and_counterevidence_boundaries_reject_malformed_inputs() -> (
    None
):
    # Given: a valid claim-derived variant and exact registered reference.
    claim = _claim()
    variant = ClaimVariantRef.from_claim(claim)
    reference = ClaimReference(ClaimReferenceCategory.FACT, "fact", "v1")

    # When / Then: raw, subclass, mutable, duplicate, and forged inputs fail closed.
    class TextSubclass(str):
        pass

    for claim_id, digest in (
        ("", claim.content_digest),
        (True, claim.content_digest),
        (TextSubclass(claim.claim_id), claim.content_digest),
        (claim.claim_id, "a" * 64),
        (claim.claim_id, TextSubclass("a" * 64)),
    ):
        with pytest.raises(ArbitrationContractError):
            ClaimVariantRef(claim_id, digest)
    for owner, references in (
        ("forged", (reference,)),
        (variant, []),
        (variant, {reference}),
        (variant, (item for item in (reference,))),
        (variant, (reference, reference)),
    ):
        with pytest.raises(ArbitrationContractError):
            CounterevidenceTrace(owner, references)


def test_result_public_boundary_rejects_mutable_and_forged_collections() -> None:
    # Given: a fully validated result and its legitimate digest.
    result = arbitrate(_arena(_claim()))

    # When / Then: direct and builder inputs cannot retain mutable or wrong values.
    with pytest.raises(ArbitrationContractError):
        ArbitrationResult(
            result.decision,
            result.content_digest,
            list(result.retained_variants),
            result.applicable_variants,
            result.minority_variants,
            result.preserved_variants,
            result.temporal_groups,
            result.evidence_groups,
            result.counterevidence_traces,
            result.audits,
            result.gates,
        )
    with pytest.raises(ArbitrationContractError):
        ArbitrationResult(
            result.decision,
            result.content_digest,
            result.retained_variants,
            result.applicable_variants,
            result.minority_variants,
            result.preserved_variants,
            result.temporal_groups,
            ("forged",),
            result.counterevidence_traces,
            result.audits,
            result.gates,
        )
    with pytest.raises(ArbitrationContractError):
        ArbitrationResult.build(
            result.decision,
            list(result.retained_variants),
            result.applicable_variants,
            result.minority_variants,
            result.preserved_variants,
            result.temporal_groups,
            result.evidence_groups,
            result.counterevidence_traces,
            result.audits,
            result.gates,
        )


def test_evidence_gate_distinguishes_clean_and_blocked_variants_with_same_claim_id() -> (
    None
):
    # Given: equivalent assertions whose content differs only by a typed blocker.
    clean = _claim()
    blocked = _claim(
        blockers=(ClaimIssue(ClaimIssueCode.INSUFFICIENT_EVIDENCE, "missing input"),)
    )

    # When: both variants traverse the immutable evidence gate.
    result = arbitrate(_arena(clean, blocked))
    evidence = next(
        record for record in result.gates if record.gate.value == "evidence"
    )

    # Then: the gate retains and rejects distinct first-class variant references.
    assert clean.claim_id == blocked.claim_id
    assert evidence.retained_variants == (ClaimVariantRef.from_claim(clean),)
    assert evidence.rejected_variants == (ClaimVariantRef.from_claim(blocked),)


def test_confidence_content_change_changes_arbitration_digest() -> None:
    # Given: two assertion variants with one identity but different content confidence.
    baseline = _claim(confidence=0.7)
    changed = _claim(confidence=0.8)

    # When: each complete arena is arbitrated independently.
    baseline_result = arbitrate(_arena(baseline))
    changed_result = arbitrate(_arena(changed))

    # Then: result digests bind the full variant content rather than only claim ID.
    assert baseline.claim_id == changed.claim_id
    assert baseline_result.content_digest != changed_result.content_digest


def test_counterevidence_gate_exposes_immutable_variant_trace() -> None:
    # Given: a support claim that carries an exact registered contrary reference.
    counter = ClaimReference(ClaimReferenceCategory.FACT, "fact", "v1")
    claim = _claim(counterevidence=(counter,))

    # When: the claim crosses the counterevidence gate.
    result = arbitrate(_arena(claim))

    # Then: its owner variant and exact reference survive in the public trace.
    assert result.counterevidence_traces[0].owner == ClaimVariantRef.from_claim(claim)
    assert result.counterevidence_traces[0].references == (counter,)


def test_support_copies_cannot_remove_counterevidence_trace() -> None:
    # Given: one contrary reference and repeated same-source supporting assertions.
    counter = ClaimReference(ClaimReferenceCategory.FACT, "fact", "v1")
    contrary = _claim(counterevidence=(counter,))
    support = _claim()

    # When: duplicate supporting input joins the same source family.
    result = arbitrate(_arena(contrary, support, support))

    # Then: the contrary reference remains visible regardless of copy count.
    assert result.counterevidence_traces == (result.counterevidence_traces[0],)
    assert result.counterevidence_traces[0].owner == ClaimVariantRef.from_claim(
        contrary
    )


def test_counterevidence_content_changes_arbitration_digest() -> None:
    # Given: otherwise equivalent claims with and without contrary evidence.
    plain = _claim()
    counter = _claim(
        counterevidence=(ClaimReference(ClaimReferenceCategory.FACT, "fact", "v1"),)
    )

    # When: both variants are independently decided.
    plain_result = arbitrate(_arena(plain))
    counter_result = arbitrate(_arena(counter))

    # Then: the immutable digest binds the counterevidence trace.
    assert plain_result.content_digest != counter_result.content_digest


def test_shared_fact_with_different_source_rule_remains_two_evidence_groups() -> None:
    # Given: claims share a public fact but cite distinct complete theory sources.
    first = _claim(
        source_rule_refs=(
            ClaimReference(ClaimReferenceCategory.SOURCE_RULE, "rule", "v1"),
        )
    )
    second = _claim(
        source_rule_refs=(
            ClaimReference(ClaimReferenceCategory.SOURCE_RULE, "rule-alt", "v1"),
        )
    )

    # When: independence grouping is evaluated before capability qualification.
    result = arbitrate(_arena(first, second))

    # Then: a shared observation does not erase distinct source identities.
    assert result.independent_group_count == 2
    assert set(result.retained_claim_ids) == {first.claim_id, second.claim_id}


def test_transitive_overlap_cannot_merge_distinct_complete_source_identities() -> None:
    # Given: A and C cite r1 while bridge B cites r2, all sharing public fact f.
    first = _claim(
        source_rule_refs=(
            ClaimReference(ClaimReferenceCategory.SOURCE_RULE, "rule", "v1"),
        )
    )
    bridge = _claim(
        source_rule_refs=(
            ClaimReference(ClaimReferenceCategory.SOURCE_RULE, "rule-alt", "v1"),
        )
    )
    third = _claim(
        school="gao_dechen",
        source_rule_refs=(
            ClaimReference(ClaimReferenceCategory.SOURCE_RULE, "rule", "v1"),
        ),
    )

    # When: transitive overlapping references enter the immutable arena.
    result = arbitrate(_arena(first, bridge, third))

    # Then: only complete r1 identities fold, leaving r2 independent.
    assert result.independent_group_count == 2
    assert tuple(sorted(len(group.claim_ids) for group in result.evidence_groups)) == (
        1,
        2,
    )


def test_reference_permutation_produces_the_same_claim_and_arbitration_digest() -> None:
    # Given: equivalent reference sets arriving in opposite orders.
    first = _claim(
        source_rule_refs=(
            ClaimReference(ClaimReferenceCategory.SOURCE_RULE, "rule", "v1"),
            ClaimReference(ClaimReferenceCategory.SOURCE_RULE, "rule-alt", "v1"),
        )
    )
    second = _claim(source_rule_refs=tuple(reversed(first.source_rule_refs)))

    # When: each canonicalized claim is independently arbitrated.
    first_result = arbitrate(_arena(first))
    second_result = arbitrate(_arena(second))

    # Then: input reference order has no semantic or digest effect.
    assert first == second
    assert first_result.content_digest == second_result.content_digest


def test_empty_arena_abstains_without_implicit_default_authority() -> None:
    # Given: no claim is admitted into a complete typed arena.
    result = arbitrate(_arena())

    # When / Then: the central decision does not manufacture a winner.
    assert result.decision is ArbitrationDecision.ABSTAIN


def test_explicit_fact_conflict_context_fails_closed() -> None:
    # Given: an upstream integrity scanner reports incompatible contents for one fact ID.
    conflict = FactConflictContext("fact", "a" * 64, "b" * 64)

    # When / Then: arbitration rejects the arena before theory-level resolution.
    with pytest.raises(ArbitrationIntegrityError, match="ARBITRATION.FACT_CONFLICT"):
        arbitrate(_arena(_claim()).with_fact_conflicts((conflict,)))
