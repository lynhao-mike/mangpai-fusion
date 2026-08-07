from __future__ import annotations

from dataclasses import dataclass
from typing import assert_never

from engine.application.governance_claim_adapters import adapt_decision_school_claim
from engine.application.governance_shadow_types import (
    SchoolViewFailure,
    SchoolViewOutcome,
    ShadowIssue,
    UnavailableSchool,
)
from engine.governance.governance_claim import GovernanceClaim
from engine.governance.governance_claim_values import (
    ClaimIssue,
    GovernanceReferenceCatalog,
)


@dataclass(frozen=True, slots=True)
class AdaptedSchoolViews:
    claims: tuple[GovernanceClaim, ...]
    unavailable: tuple[UnavailableSchool, ...]
    excluded_claim_refs: tuple[str, ...]
    issues: tuple[ShadowIssue, ...]


def _claim_issue(issue: ClaimIssue) -> ShadowIssue:
    return ShadowIssue(issue.code.value, "school_views.legacy_claims", issue.detail)


def adapt_school_views(
    views: tuple[SchoolViewOutcome | SchoolViewFailure, ...],
    catalog: GovernanceReferenceCatalog,
) -> AdaptedSchoolViews:
    claims: list[GovernanceClaim] = []
    unavailable: list[UnavailableSchool] = []
    excluded: list[str] = []
    issues: list[ShadowIssue] = []
    for view in views:
        match view:
            case SchoolViewFailure(
                school_id=school_id, issue_code=code, diagnostic=text
            ):
                unavailable.append(UnavailableSchool(school_id, code, text))
            case SchoolViewOutcome(school_id=school_id, legacy_claims=legacy_claims):
                if school_id == "ditiansui":
                    excluded.extend(claim.claim_id for claim in legacy_claims)
                    continue
                for legacy in legacy_claims:
                    adapted = adapt_decision_school_claim(legacy, catalog)
                    if adapted.claim is None:
                        issues.extend(_claim_issue(issue) for issue in adapted.issues)
                        continue
                    claims.append(adapted.claim)
            case unreachable:
                assert_never(unreachable)
    return AdaptedSchoolViews(
        tuple(sorted(claims, key=lambda claim: claim.claim_id)),
        tuple(unavailable),
        tuple(excluded),
        tuple(issues),
    )
