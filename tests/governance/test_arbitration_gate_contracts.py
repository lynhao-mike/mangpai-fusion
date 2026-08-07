from __future__ import annotations

from itertools import permutations

import pytest

from engine.governance import DigestRef
from engine.governance.arbitration import (
    ArbitrationContractError,
    ArbitrationResult,
    GateName,
    arbitrate,
)
from engine.governance.arbitration_contracts import GateRecord
from engine.governance.arbitration_trace import result_digest
from tests.governance.test_arbitration_gates import _arena, _claim


def _digest_with_gates(
    result: ArbitrationResult, gates: tuple[GateRecord, ...]
) -> DigestRef:
    provisional = object.__new__(ArbitrationResult)
    for name, value in (
        ("decision", result.decision),
        ("retained_variants", result.retained_variants),
        ("applicable_variants", result.applicable_variants),
        ("minority_variants", result.minority_variants),
        ("preserved_variants", result.preserved_variants),
        ("temporal_groups", result.temporal_groups),
        ("evidence_groups", result.evidence_groups),
        ("counterevidence_traces", result.counterevidence_traces),
        ("audits", result.audits),
        ("gates", gates),
    ):
        object.__setattr__(provisional, name, value)
    return result_digest(provisional)


def test_result_build_rejects_empty_missing_duplicate_and_reordered_gate_history() -> (
    None
):
    # Given: a complete result with a canonical seven-gate history.
    result = arbitrate(_arena(_claim()))
    gate_cases = (
        (),
        result.gates[:-1],
        (result.gates[0], *result.gates),
        tuple(reversed(result.gates)),
    )

    # When / Then: every incomplete or reordered history fails before digesting.
    for gates in gate_cases:
        with pytest.raises(ArbitrationContractError):
            ArbitrationResult.build(
                result.decision,
                result.retained_variants,
                result.applicable_variants,
                result.minority_variants,
                result.preserved_variants,
                result.temporal_groups,
                result.evidence_groups,
                result.counterevidence_traces,
                result.audits,
                gates,
            )


def test_result_direct_constructor_rejects_matching_digest_with_invalid_gate_history() -> (
    None
):
    # Given: a digest forged from an otherwise valid result with no gate records.
    result = arbitrate(_arena(_claim()))
    gates: tuple[GateRecord, ...] = ()
    digest = _digest_with_gates(result, gates)

    # When / Then: direct construction still validates gate history before digest binding.
    with pytest.raises(ArbitrationContractError):
        ArbitrationResult(
            result.decision,
            digest,
            result.retained_variants,
            result.applicable_variants,
            result.minority_variants,
            result.preserved_variants,
            result.temporal_groups,
            result.evidence_groups,
            result.counterevidence_traces,
            result.audits,
            gates,
        )


def test_result_rejects_gate_history_with_overlapping_or_lost_variants() -> None:
    # Given: a canonical result and a gate that contradicts its predecessor state.
    result = arbitrate(_arena(_claim()))
    evidence = result.gates[2]
    overlapping = GateRecord(
        GateName.EVIDENCE,
        evidence.retained_variants,
        evidence.retained_variants,
    )
    gates = (*result.gates[:2], overlapping, *result.gates[3:])

    # When / Then: a variant cannot be both retained and rejected in one gate.
    with pytest.raises(ArbitrationContractError):
        ArbitrationResult.build(
            result.decision,
            result.retained_variants,
            result.applicable_variants,
            result.minority_variants,
            result.preserved_variants,
            result.temporal_groups,
            result.evidence_groups,
            result.counterevidence_traces,
            result.audits,
            gates,
        )


def test_derivation_identity_distinguishes_and_folds_complete_source_families() -> None:
    # Given: equal references with different derivations, plus a same-derivation variant.
    first = _claim(confidence=0.7)
    same_derivation = _claim(confidence=0.8)
    changed_derivation = _claim(
        derivation_chain_digest=DigestRef.from_material(("task7", "alternate"))
    )

    # When: every complete source identity is grouped through independence.
    folded = arbitrate(_arena(first, same_derivation))
    separated = arbitrate(_arena(first, changed_derivation))

    # Then: only the complete identity, including derivation, can fold.
    assert folded.independent_group_count == 1
    assert separated.independent_group_count == 2


def test_derivation_identity_is_permutation_invariant_without_transitive_merging() -> (
    None
):
    # Given: two matching derivations and a distinct derivation with the same references.
    first = _claim(confidence=0.7)
    same_derivation = _claim(confidence=0.8)
    distinct_derivation = _claim(
        derivation_chain_digest=DigestRef.from_material(("task7", "alternate"))
    )

    # When: all input permutations enter the immutable arbitrator.
    results = tuple(
        arbitrate(_arena(*ordered))
        for ordered in permutations((first, same_derivation, distinct_derivation))
    )

    # Then: the matching pair folds once while the distinct derivation remains separate.
    assert {result.content_digest for result in results} == {results[0].content_digest}
    assert {result.independent_group_count for result in results} == {2}
