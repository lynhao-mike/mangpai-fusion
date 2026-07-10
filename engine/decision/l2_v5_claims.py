"""V5 runner claim 到 L2 SchoolClaim 的无损边界。"""

from __future__ import annotations

from copy import deepcopy

from engine.decision.models import SchoolClaim, SchoolRole
from engine.v5.domain import V5Claim


def to_school_claim(claim: V5Claim, role: SchoolRole) -> SchoolClaim:
    """只复制来源字段与 L1 授权；不得在此产生命理判断。"""

    metadata = deepcopy(claim.metadata)
    metadata["v5_payload"] = deepcopy(
        {
            "stance": claim.stance,
            "polarity": claim.polarity,
            "counter_evidence": [item.to_dict() for item in claim.counter_evidence],
            "timing_hints": claim.timing_hints,
            "probabilistic": claim.probabilistic,
        }
    )
    return SchoolClaim(
        claim_id=claim.claim_id,
        school=claim.school,
        role_granted_by_l1=role,
        domain=claim.domain,
        claim_type=claim.claim_type,
        statement=claim.claim,
        evidence_refs=[item.evidence_id for item in claim.evidence],
        confidence=claim.confidence.score,
        falsifier=claim.falsifiable,
        dependencies=[f"v5:{claim.claim_id}"],
        metadata=metadata,
    )
