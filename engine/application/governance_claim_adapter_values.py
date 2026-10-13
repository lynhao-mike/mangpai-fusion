from __future__ import annotations

from dataclasses import dataclass

from engine.decision.models import SchoolClaim
from engine.governance import (
    ClaimIssue,
    ClaimIssueCode,
    ClaimKind,
    ClaimReference,
    ClaimReferenceCategory,
    ClaimStance,
    GovernanceClaim,
    GovernanceClaimContractError,
    TemporalLayer,
    TemporalScope,
)


@dataclass(frozen=True, slots=True)
class AdaptationResult:
    claim: GovernanceClaim | None
    issues: tuple[ClaimIssue, ...]


def loss(code: ClaimIssueCode, detail: str) -> AdaptationResult:
    return AdaptationResult(None, (ClaimIssue(code, detail),))


def catalog_loss(error: GovernanceClaimContractError) -> AdaptationResult:
    return loss(
        (
            ClaimIssueCode.LEGACY_REFERENCE_REJECTED
            if error.issue_code.startswith("CLAIM.REFERENCE_")
            else ClaimIssueCode.LEGACY_CLAIM_REJECTED
        ),
        f"{error.issue_code}: {error.diagnostic}",
    )


SCHOOL_METADATA_KEYS = frozenset(
    {"task_id", "stance", "temporal_scope", "reference_version"}
)
SCHOOL_ROLE_VALUES = frozenset({"lead", "co_lead", "evidence_only", "abstain"})
_SCHOOL_IDS = {
    "ziping": "ziping",
    "gao": "gao_dechen",
    "gao_dechen": "gao_dechen",
    "duan": "duan_jianye",
    "duan_jianye": "duan_jianye",
    "yang": "yang_qingjuan",
    "yang_qingjuan": "yang_qingjuan",
    "ren": "ren_fuhong",
    "ren_fuhong": "ren_fuhong",
}
_SCHOOL_KINDS = {
    "structure_claim": ClaimKind.STRUCTURE,
    "event_claim": ClaimKind.EVENT,
    "timing_claim": ClaimKind.TIMING,
    "support_claim": ClaimKind.SUPPORT,
}
DOMAIN_KINDS = {
    "structure_claim": ClaimKind.STRUCTURE,
    "event_claim": ClaimKind.EVENT,
    "timing_claim": ClaimKind.TIMING,
    "portrait_claim": ClaimKind.SUPPORT,
}
_SCHOOL_STANCES = {"support": ClaimStance.SUPPORT, "oppose": ClaimStance.OPPOSE}


def school_id(legacy_id: str) -> str | None:
    return _SCHOOL_IDS.get(legacy_id)


def metadata_text(claim: SchoolClaim, key: str) -> str | None:
    value = claim.metadata.get(key)
    return value if type(value) is str and value.strip() else None


def school_scope(claim: SchoolClaim) -> TemporalScope | None:
    scope = metadata_text(claim, "temporal_scope")
    return TemporalScope(layer=TemporalLayer.NATAL) if scope == "natal" else None


def school_stance(claim: SchoolClaim) -> ClaimStance | None:
    return _SCHOOL_STANCES.get(metadata_text(claim, "stance"))


def school_kind(claim: SchoolClaim) -> ClaimKind | None:
    return _SCHOOL_KINDS.get(claim.claim_type)


def school_references(
    claim: SchoolClaim, version: str
) -> tuple[ClaimReference, ...] | None:
    if any(
        type(reference) is not str or not reference.strip()
        for reference in claim.evidence_refs
    ):
        return None
    return tuple(
        ClaimReference(
            ClaimReferenceCategory.SOURCE_RULE
            if reference.startswith("rule:")
            else ClaimReferenceCategory.SCHOOL_REASON,
            reference,
            version,
        )
        for reference in claim.evidence_refs
    )
