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


def apply_ziping_career_slice(
    output: V5Output,
    applicability: list[SchoolApplicability],
) -> tuple[list[SchoolClaim], list[StructuralVerdict], list[EventHypothesis]]:
    """原生替换子平总体/事业 L2，并让完整 L2 集合直接进入 L3/L4。"""

    role_by_school = {item.school: item.role for item in applicability}
    target_v5 = [
        claim
        for claim in output.claims
        if claim.school == "ziping" and claim.domain in _TARGET_DOMAINS
    ]
    legacy_output = replace(
        output,
        claims=[claim for claim in output.claims if claim not in target_v5],
    )
    legacy_l2 = v5_adapter._claims(legacy_output, applicability)
    ziping_role = role_by_school.get("ziping", "abstain")
    native_l2 = (
        []
        if ziping_role == "abstain"
        else [to_school_claim(claim, ziping_role) for claim in target_v5]
    )

    claims = legacy_l2 + native_l2
    case_id = output.case_id or "V5-UNKNOWN"
    verdicts = build_structural_verdicts(case_id, claims)
    events = build_event_hypotheses(case_id, verdicts, claims)
    return claims, verdicts, events
