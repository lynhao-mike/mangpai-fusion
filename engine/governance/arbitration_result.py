from __future__ import annotations

from dataclasses import dataclass

from engine.governance.arbitration_contracts import (
    ArbitrationDecision,
    ClaimAudit,
    ClaimVariantRef,
    CounterevidenceTrace,
    EvidenceGroup,
    GateRecord,
    TemporalGroup,
)
from engine.governance.arbitration_values import ArbitrationContractError
from engine.governance.arbitration_nested_validation import nested, variants
from engine.governance.arbitration_result_validation import gate_history
from engine.governance.fact_values import DigestRef


def _validate(
    decision: ArbitrationDecision,
    content_digest: DigestRef,
    retained_variants: tuple[ClaimVariantRef, ...],
    applicable_variants: tuple[ClaimVariantRef, ...],
    minority_variants: tuple[ClaimVariantRef, ...],
    preserved_variants: tuple[ClaimVariantRef, ...],
    temporal_groups: tuple[TemporalGroup, ...],
    evidence_groups: tuple[EvidenceGroup, ...],
    traces: tuple[CounterevidenceTrace, ...],
    audits: tuple[ClaimAudit, ...],
    gates: tuple[GateRecord, ...],
) -> None:
    if (
        type(decision) is not ArbitrationDecision
        or type(content_digest) is not DigestRef
    ):
        raise ArbitrationContractError("result", "must use exact decision and digest")
    for field_path, values in (
        ("retained_variants", retained_variants),
        ("applicable_variants", applicable_variants),
        ("minority_variants", minority_variants),
        ("preserved_variants", preserved_variants),
    ):
        variants(field_path, values, False)
    nested(temporal_groups, evidence_groups, traces, audits, gates)
    gate_history(gates, preserved_variants, applicable_variants)


@dataclass(frozen=True, slots=True)
class ArbitrationResult:
    decision: ArbitrationDecision
    content_digest: DigestRef
    retained_variants: tuple[ClaimVariantRef, ...]
    applicable_variants: tuple[ClaimVariantRef, ...]
    minority_variants: tuple[ClaimVariantRef, ...]
    preserved_variants: tuple[ClaimVariantRef, ...]
    temporal_groups: tuple[TemporalGroup, ...]
    evidence_groups: tuple[EvidenceGroup, ...]
    counterevidence_traces: tuple[CounterevidenceTrace, ...]
    audits: tuple[ClaimAudit, ...]
    gates: tuple[GateRecord, ...]

    def __post_init__(self) -> None:
        from engine.governance.arbitration_trace import result_digest

        _validate(
            self.decision,
            self.content_digest,
            self.retained_variants,
            self.applicable_variants,
            self.minority_variants,
            self.preserved_variants,
            self.temporal_groups,
            self.evidence_groups,
            self.counterevidence_traces,
            self.audits,
            self.gates,
        )
        if self.content_digest != result_digest(self):
            raise ArbitrationContractError("content_digest", "does not bind result")

    @classmethod
    def build(
        cls,
        decision: ArbitrationDecision,
        retained_variants: tuple[ClaimVariantRef, ...],
        applicable_variants: tuple[ClaimVariantRef, ...],
        minority_variants: tuple[ClaimVariantRef, ...],
        preserved_variants: tuple[ClaimVariantRef, ...],
        temporal_groups: tuple[TemporalGroup, ...],
        evidence_groups: tuple[EvidenceGroup, ...],
        counterevidence_traces: tuple[CounterevidenceTrace, ...],
        audits: tuple[ClaimAudit, ...],
        gates: tuple[GateRecord, ...],
    ) -> ArbitrationResult:
        from engine.governance.arbitration_trace import result_digest

        marker = DigestRef.from_material(("arbitration-result-build",))
        _validate(
            decision,
            marker,
            retained_variants,
            applicable_variants,
            minority_variants,
            preserved_variants,
            temporal_groups,
            evidence_groups,
            counterevidence_traces,
            audits,
            gates,
        )
        provisional = object.__new__(cls)
        for name, value in (
            ("decision", decision),
            ("retained_variants", retained_variants),
            ("applicable_variants", applicable_variants),
            ("minority_variants", minority_variants),
            ("preserved_variants", preserved_variants),
            ("temporal_groups", temporal_groups),
            ("evidence_groups", evidence_groups),
            ("counterevidence_traces", counterevidence_traces),
            ("audits", audits),
            ("gates", gates),
        ):
            object.__setattr__(provisional, name, value)
        return cls(
            decision,
            result_digest(provisional),
            retained_variants,
            applicable_variants,
            minority_variants,
            preserved_variants,
            temporal_groups,
            evidence_groups,
            counterevidence_traces,
            audits,
            gates,
        )

    @property
    def independent_group_count(self) -> int:
        return len(self.evidence_groups)

    @property
    def retained_claim_ids(self) -> tuple[str, ...]:
        return tuple(variant.claim_id for variant in self.retained_variants)

    @property
    def applicable_claim_ids(self) -> tuple[str, ...]:
        return tuple(variant.claim_id for variant in self.applicable_variants)
