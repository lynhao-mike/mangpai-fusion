"""R10 第一证明物：子平·事业域 L2-L4 原生纵切片。"""

from __future__ import annotations

from dataclasses import replace

from engine.decision import v5_adapter
from engine.decision.l2_v5_claims import to_school_claim
from engine.decision.l3_structure import build_structural_verdicts
from engine.decision.l4_events import build_event_hypotheses
from engine.decision.models import (
    EventHypothesis,
    SchoolApplicability,
    SchoolClaim,
    StructuralVerdict,
)
from engine.v5.domain import V5Output

_TARGET_DOMAINS = {"总体", "事业"}


def _is_ziping_career_target(claim: object) -> bool:
    return (
        getattr(claim, "school", None) == "ziping"
        and getattr(claim, "domain", None) in _TARGET_DOMAINS
    )


def _reject_duplicate_claim_ids(claims: list[SchoolClaim]) -> None:
    seen: set[str] = set()
    for claim in claims:
        if claim.claim_id in seen:
            raise ValueError(f"duplicate L2 claim_id: {claim.claim_id}")
        seen.add(claim.claim_id)


def apply_ziping_career_slice(
    output: V5Output,
    applicability: list[SchoolApplicability],
) -> tuple[list[SchoolClaim], list[StructuralVerdict], list[EventHypothesis]]:
    """原生替换子平总体/事业 L2，并让完整 L2 集合直接进入 L3/L4。"""

    ziping_applicability = [item for item in applicability if item.school == "ziping"]
    if len(ziping_applicability) > 1:
        raise ValueError("duplicate ziping applicability")

    target_v5 = [claim for claim in output.claims if _is_ziping_career_target(claim)]
    legacy_output = replace(
        output,
        claims=[claim for claim in output.claims if not _is_ziping_career_target(claim)],
    )
    legacy_l2 = v5_adapter._claims(legacy_output, applicability)
    ziping_role = (
        ziping_applicability[0].role if ziping_applicability else "abstain"
    )
    native_l2 = (
        []
        if ziping_role == "abstain"
        else [to_school_claim(claim, ziping_role) for claim in target_v5]
    )

    claims = legacy_l2 + native_l2
    _reject_duplicate_claim_ids(claims)
    case_id = output.case_id or "V5-UNKNOWN"
    verdicts = build_structural_verdicts(case_id, claims)
    events = build_event_hypotheses(case_id, verdicts, claims)
    return claims, verdicts, events
