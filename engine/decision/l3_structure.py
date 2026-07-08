"""L3 结构合法性层最小实现。"""

from __future__ import annotations

import hashlib

from engine.decision.models import SchoolClaim, StructuralVerdict


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]}"


def build_structural_verdicts(case_id: str, claims: list[SchoolClaim]) -> list[StructuralVerdict]:
    """L3 只审查结构基础，不定事件、不定年份。"""

    verdicts: list[StructuralVerdict] = []
    for claim in claims:
        verdict = "pass" if claim.claim_type == "structure" and claim.confidence >= 0.5 else "weaken"
        if claim.confidence <= 0.1:
            verdict = "reject"
        elif claim.claim_type in {"event", "timing"}:
            verdict = "unknown"
        verdicts.append(
            StructuralVerdict(
                verdict_id=_stable_id("dsv", case_id, claim.claim_id),
                claim_id=claim.claim_id,
                verdict=verdict,  # type: ignore[arg-type]
                structural_reason="L3 只审查结构基础；事件与应期命题不得在本层直接定案。",
                blocking_factors=[] if verdict == "pass" else ["需要结构命题继续支撑"],
                required_support=["ziping", "ditiansui"] if verdict != "pass" else [],
                confidence=0.6 if verdict == "pass" else 0.35,
            )
        )
    return verdicts
