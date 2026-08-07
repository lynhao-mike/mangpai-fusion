from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique

from engine.governance.fact_certification import FactCertificationRegistry
from engine.governance.fact_values import DigestRef, TemporalScope
from engine.governance.contracts import GovernanceFact
from engine.governance.governance_claim import GovernanceClaim
from engine.governance.governance_claim_values import (
    ClaimReference,
    GovernanceReferenceCatalog,
)
from engine.governance.school_registry import SchoolRegistry
from engine.governance.arbitration_values import (
    ArbitrationContractError,
    validate_variant,
)


@unique
class GateName(StrEnum):
    ELIGIBILITY = "eligibility"
    TEMPORAL = "temporal"
    EVIDENCE = "evidence"
    INDEPENDENCE = "independence"
    COUNTEREVIDENCE = "counterevidence"
    APPLICABILITY = "applicability"
    DECISION = "decision"


@unique
class ArbitrationDecision(StrEnum):
    CONSENSUS = "consensus"
    COMPLEMENTARY = "complementary"
    CONFLICT = "conflict"
    CONDITIONAL = "conditional"
    ABSTAIN = "abstain"
    HUMAN_REVIEW = "human_review"


@unique
class ArbitrationIssueCode(StrEnum):
    ELIGIBILITY_UNKNOWN_SCHOOL = "ARBITRATION.ELIGIBILITY_UNKNOWN_SCHOOL"
    EVIDENCE_BLOCKED = "ARBITRATION.EVIDENCE_BLOCKED"
    CAPABILITY_ABSTAIN = "ARBITRATION.CAPABILITY_ABSTAIN"
    FACT_CONFLICT = "ARBITRATION.FACT_CONFLICT"


@dataclass(frozen=True, slots=True)
class ArbitrationIntegrityError(Exception):
    code: ArbitrationIssueCode
    fact_id: str

    def __str__(self) -> str:
        return f"{self.code.value}: {self.fact_id} has incompatible contents"


@dataclass(frozen=True, slots=True)
class FactConflictContext:
    fact_id: str
    first_digest: str
    conflicting_digest: str

    def __post_init__(self) -> None:
        if not self.fact_id:
            raise ArbitrationIntegrityError(
                ArbitrationIssueCode.FACT_CONFLICT, self.fact_id
            )
        DigestRef(self.first_digest)
        DigestRef(self.conflicting_digest)
        if self.first_digest == self.conflicting_digest:
            raise ArbitrationIntegrityError(
                ArbitrationIssueCode.FACT_CONFLICT, self.fact_id
            )


@dataclass(frozen=True, slots=True)
class ClaimVariantRef:
    claim_id: str
    content_digest: DigestRef

    def __post_init__(self) -> None:
        validate_variant(self.claim_id, self.content_digest)

    @classmethod
    def from_claim(cls, claim: GovernanceClaim) -> ClaimVariantRef:
        return cls(claim.claim_id, claim.content_digest)


def variant_key(variant: ClaimVariantRef) -> tuple[str, str]:
    return (variant.claim_id, variant.content_digest.value)


@dataclass(frozen=True, slots=True)
class ClaimAudit:
    owner: ClaimVariantRef
    gate: GateName
    issue_code: ArbitrationIssueCode

    def __post_init__(self) -> None:
        from engine.governance.arbitration_nested_validation import audit

        audit(self)

    @property
    def claim_id(self) -> str:
        return self.owner.claim_id


@dataclass(frozen=True, slots=True)
class TemporalGroup:
    scope: TemporalScope
    variants: tuple[ClaimVariantRef, ...]

    def __post_init__(self) -> None:
        from engine.governance.arbitration_nested_validation import temporal

        temporal(self)

    @property
    def claim_ids(self) -> tuple[str, ...]:
        return tuple(variant.claim_id for variant in self.variants)


@dataclass(frozen=True, slots=True)
class EvidenceGroup:
    source_keys: tuple[str, ...]
    variants: tuple[ClaimVariantRef, ...]

    def __post_init__(self) -> None:
        from engine.governance.arbitration_nested_validation import evidence

        evidence(self)

    @property
    def claim_ids(self) -> tuple[str, ...]:
        return tuple(variant.claim_id for variant in self.variants)


@dataclass(frozen=True, slots=True)
class GateRecord:
    gate: GateName
    retained_variants: tuple[ClaimVariantRef, ...]
    rejected_variants: tuple[ClaimVariantRef, ...]

    def __post_init__(self) -> None:
        from engine.governance.arbitration_nested_validation import record

        record(self)

    @property
    def retained_claim_ids(self) -> tuple[str, ...]:
        return tuple(variant.claim_id for variant in self.retained_variants)

    @property
    def rejected_claim_ids(self) -> tuple[str, ...]:
        return tuple(variant.claim_id for variant in self.rejected_variants)


@dataclass(frozen=True, slots=True)
class CounterevidenceTrace:
    owner: ClaimVariantRef
    references: tuple[ClaimReference, ...]

    def __post_init__(self) -> None:
        from engine.governance.arbitration_nested_validation import trace

        trace(self)


@dataclass(frozen=True, slots=True)
class ArbitrationContext:
    facts: tuple[GovernanceFact, ...]
    certifications: FactCertificationRegistry

    def __post_init__(self) -> None:
        if type(self.facts) is not tuple or any(
            type(fact) is not GovernanceFact for fact in self.facts
        ):
            raise ArbitrationContractError("facts", "must be immutable GovernanceFact")
        if type(self.certifications) is not FactCertificationRegistry:
            raise ArbitrationContractError(
                "certifications", "must be a FactCertificationRegistry"
            )


@dataclass(frozen=True, slots=True)
class ArbitrationArena:
    claims: tuple[GovernanceClaim, ...]
    context: ArbitrationContext
    reference_catalog: GovernanceReferenceCatalog
    school_registry: SchoolRegistry
    capability_version: str
    fact_conflicts: tuple[FactConflictContext, ...] = ()

    def __post_init__(self) -> None:
        if type(self.claims) is not tuple or any(
            type(claim) is not GovernanceClaim for claim in self.claims
        ):
            raise ArbitrationContractError(
                "claims", "must be immutable GovernanceClaim"
            )
        if type(self.context) is not ArbitrationContext:
            raise ArbitrationContractError("context", "must be an ArbitrationContext")
        if type(self.reference_catalog) is not GovernanceReferenceCatalog:
            raise ArbitrationContractError(
                "reference_catalog", "must be a GovernanceReferenceCatalog"
            )
        if type(self.school_registry) is not SchoolRegistry:
            raise ArbitrationContractError(
                "school_registry", "must be a SchoolRegistry"
            )
        if type(self.capability_version) is not str or not self.capability_version:
            raise ArbitrationContractError("capability_version", "must be nonempty")
        if type(self.fact_conflicts) is not tuple or any(
            type(item) is not FactConflictContext for item in self.fact_conflicts
        ):
            raise ArbitrationContractError(
                "fact_conflicts", "must be immutable FactConflictContext"
            )

    def with_fact_conflicts(
        self, conflicts: tuple[FactConflictContext, ...]
    ) -> ArbitrationArena:
        return ArbitrationArena(
            self.claims,
            self.context,
            self.reference_catalog,
            self.school_registry,
            self.capability_version,
            conflicts,
        )


@dataclass(frozen=True, slots=True)
class ArbitrationProgress:
    active_claims: tuple[GovernanceClaim, ...]
    audits: tuple[ClaimAudit, ...]
    gates: tuple[GateRecord, ...]
    preserved_variants: tuple[ClaimVariantRef, ...] = ()
    temporal_groups: tuple[TemporalGroup, ...] = ()
    evidence_groups: tuple[EvidenceGroup, ...] = ()
    counterevidence_traces: tuple[CounterevidenceTrace, ...] = ()
    applicable_claims: tuple[GovernanceClaim, ...] = ()
