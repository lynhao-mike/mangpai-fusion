from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from engine.decision.models import ChartFactLedger, RawWenzhenPayload, SchoolClaim
from engine.features.types import ChartFeatureVector
from engine.governance.arbitration_contracts import FactConflictContext
from engine.governance.arbitration_result import ArbitrationResult
from engine.governance.canonical import CanonicalValue
from engine.governance.composition_templates import CompositionRegistry
from engine.governance.contracts import FactSnapshot
from engine.governance.fact_certification import FactCertificationRegistry
from engine.governance.fact_values import DigestRef
from engine.governance.governance_claim import GovernanceClaim
from engine.governance.governance_claim_values import GovernanceReferenceCatalog
from engine.governance.school_registry import SchoolRegistry
from engine.governance.trigger_registry import TriggerEvaluationContext, TriggerRegistry


@dataclass(frozen=True, slots=True)
class SchoolViewOutcome:
    school_id: str
    legacy_claims: tuple[SchoolClaim, ...]


@dataclass(frozen=True, slots=True)
class SchoolViewFailure:
    school_id: str
    issue_code: str
    diagnostic: str


@dataclass(frozen=True, slots=True)
class TriggerRequest:
    trigger_id: str
    context: TriggerEvaluationContext


@dataclass(frozen=True, slots=True)
class CompositionRequest:
    template_id: str
    version: str
    component_claim_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GovernanceShadowRequest:
    case_id: str
    raw_payload: RawWenzhenPayload
    chart: ChartFactLedger
    calculator_version: str
    school_views: tuple[SchoolViewOutcome | SchoolViewFailure, ...]
    target_year: int | None = None
    feature_vector: ChartFeatureVector | None = None
    fact_conflicts: tuple[FactConflictContext, ...] = ()


@dataclass(frozen=True, slots=True)
class GovernanceShadowDependencies:
    reference_catalog: GovernanceReferenceCatalog
    school_registry: SchoolRegistry
    certification_registry: FactCertificationRegistry
    capability_version: str
    trigger_registry: TriggerRegistry | None = None
    trigger_requests: tuple[TriggerRequest, ...] = ()
    composition_registry: CompositionRegistry | None = None
    composition_requests: tuple[CompositionRequest, ...] = ()


@dataclass(frozen=True, slots=True)
class ShadowIssue:
    issue_code: str
    field_path: str
    diagnostic: str

    def to_canonical(self) -> CanonicalValue:
        return (self.issue_code, self.field_path, self.diagnostic)


@dataclass(frozen=True, slots=True)
class UnavailableSchool:
    school_id: str
    issue_code: str
    diagnostic: str

    def to_canonical(self) -> CanonicalValue:
        return (self.school_id, self.issue_code, self.diagnostic)


@dataclass(frozen=True, slots=True)
class ShadowClaimTrace:
    claim_id: str
    school_id: str
    source_claim_ref: str
    content_digest: str

    @classmethod
    def from_claim(cls, claim: GovernanceClaim) -> ShadowClaimTrace:
        return cls(
            claim.claim_id,
            claim.school_id,
            claim.adapter_provenance.source_claim_ref,
            claim.content_digest.value,
        )

    def to_canonical(self) -> CanonicalValue:
        return (
            self.claim_id,
            self.school_id,
            self.source_claim_ref,
            self.content_digest,
        )


@dataclass(frozen=True, slots=True)
class GateTrace:
    gate: str
    retained_claim_ids: tuple[str, ...]
    rejected_claim_ids: tuple[str, ...]

    def to_canonical(self) -> CanonicalValue:
        return (self.gate, self.retained_claim_ids, self.rejected_claim_ids)


@dataclass(frozen=True, slots=True)
class ShadowArbitrationTrace:
    decision: str
    content_digest: str
    retained_claim_ids: tuple[str, ...]
    gate_trace: tuple[GateTrace, ...]

    @classmethod
    def from_result(cls, result: ArbitrationResult) -> ShadowArbitrationTrace:
        return cls(
            result.decision.value,
            result.content_digest.value,
            result.retained_claim_ids,
            tuple(
                GateTrace(
                    record.gate.value,
                    record.retained_claim_ids,
                    record.rejected_claim_ids,
                )
                for record in result.gates
            ),
        )

    def to_canonical(self) -> CanonicalValue:
        return (
            self.decision,
            self.content_digest,
            self.retained_claim_ids,
            tuple(record.to_canonical() for record in self.gate_trace),
        )


@dataclass(frozen=True, slots=True)
class TriggerTrace:
    trigger_id: str
    active: bool
    issues: tuple[str, ...]

    def to_canonical(self) -> CanonicalValue:
        return (self.trigger_id, self.active, self.issues)


@dataclass(frozen=True, slots=True)
class CompositionTrace:
    template_id: str
    version: str
    outcome: str
    content_digest: str
    issue_code: str | None

    def to_canonical(self) -> CanonicalValue:
        return (
            self.template_id,
            self.version,
            self.outcome,
            self.content_digest,
            self.issue_code,
        )


@dataclass(frozen=True, slots=True)
class GovernanceShadowResult:
    schema_version: str
    runner_version: str
    status: Literal["ok", "fail_closed"]
    fact_snapshot_id: str
    fact_snapshot_digest: str
    input_digest: str
    fact_kinds: tuple[str, ...]
    claims: tuple[ShadowClaimTrace, ...]
    unavailable_schools: tuple[UnavailableSchool, ...]
    excluded_claim_refs: tuple[str, ...]
    trigger_results: tuple[TriggerTrace, ...]
    composition_results: tuple[CompositionTrace, ...]
    arbitration: ShadowArbitrationTrace | None
    issues: tuple[ShadowIssue, ...]
    result_digest: str

    def to_canonical(self) -> CanonicalValue:
        return (
            self.schema_version,
            self.runner_version,
            self.status,
            self.fact_snapshot_id,
            self.fact_snapshot_digest,
            self.input_digest,
            self.fact_kinds,
            tuple(claim.to_canonical() for claim in self.claims),
            tuple(item.to_canonical() for item in self.unavailable_schools),
            self.excluded_claim_refs,
            tuple(item.to_canonical() for item in self.trigger_results),
            tuple(item.to_canonical() for item in self.composition_results),
            self.arbitration.to_canonical() if self.arbitration is not None else None,
            tuple(issue.to_canonical() for issue in self.issues),
        )


def shadow_result_digest(result: GovernanceShadowResult) -> str:
    return DigestRef.from_material(result.to_canonical()).value


def snapshot_versions(snapshot: FactSnapshot) -> tuple[str, ...]:
    return tuple(sorted({fact.calculator_version for fact in snapshot.facts}))
