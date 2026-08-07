from __future__ import annotations

from typing import TYPE_CHECKING

from engine.governance.arbitration_contracts import ClaimVariantRef
from engine.governance.fact_values import DigestRef

if TYPE_CHECKING:
    from engine.governance.arbitration_result import ArbitrationResult


def _variant_material(variant: ClaimVariantRef) -> tuple[str, str]:
    return (variant.claim_id, variant.content_digest.value)


def result_digest(result: ArbitrationResult) -> DigestRef:
    material = (
        "governance.arbitration.v2",
        result.decision.value,
        tuple(_variant_material(item) for item in result.retained_variants),
        tuple(_variant_material(item) for item in result.applicable_variants),
        tuple(_variant_material(item) for item in result.minority_variants),
        tuple(_variant_material(item) for item in result.preserved_variants),
        tuple(
            (
                group.scope.layer.value,
                group.scope.dayun_start_year,
                group.scope.dayun_end_year,
                group.scope.target_year,
                tuple(_variant_material(item) for item in group.variants),
            )
            for group in result.temporal_groups
        ),
        tuple(
            (
                group.source_keys,
                tuple(_variant_material(item) for item in group.variants),
            )
            for group in result.evidence_groups
        ),
        tuple(
            (
                _variant_material(trace.owner),
                tuple(
                    (ref.category.value, ref.reference_id, ref.version)
                    for ref in trace.references
                ),
            )
            for trace in result.counterevidence_traces
        ),
        tuple(
            (_variant_material(item.owner), item.gate.value, item.issue_code.value)
            for item in result.audits
        ),
        tuple(
            (
                item.gate.value,
                tuple(_variant_material(ref) for ref in item.retained_variants),
                tuple(_variant_material(ref) for ref in item.rejected_variants),
            )
            for item in result.gates
        ),
    )
    return DigestRef.from_material(material)
