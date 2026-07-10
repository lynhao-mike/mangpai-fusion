"""L3 结构合法性层最小实现。"""

from __future__ import annotations

import hashlib

from engine.decision.models import SchoolClaim, StructuralVerdict


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]}"


def extract_geju_profile(claims: list[SchoolClaim]) -> dict[str, object] | None:
    """只从 L2 metadata 提取既有格局方向；缺失时不推导。"""

    for claim in claims:
        metadata = claim.metadata or {}
        if metadata.get("geju_type"):
            return {
                "geju_type": str(metadata.get("geju_type")),
                "favor": {str(item) for item in metadata.get("favor_shishen", [])},
                "avoid": {str(item) for item in metadata.get("avoid_shishen", [])},
            }
    return None


_SHISHEN_NAMES = ("正官", "七杀", "正财", "偏财", "食神", "伤官", "正印", "偏印", "比肩", "劫财")


def shishen_in_statement(statement: str) -> set[str]:
    text = statement or ""
    return {name for name in _SHISHEN_NAMES if name in text}


def build_structural_verdicts(case_id: str, claims: list[SchoolClaim]) -> list[StructuralVerdict]:
    """L3 只消费 L2 结构方向，不定事件、不定年份。"""

    profile = extract_geju_profile(claims)
    verdicts: list[StructuralVerdict] = []
    for claim in claims:
        adapter_claim = claim.claim_type.endswith("_claim")
        if claim.claim_type == "structure":
            verdict = "pass" if claim.confidence >= 0.5 else "weaken"
        elif claim.claim_type == "structure_claim":
            verdict = "pass" if claim.confidence >= 0.4 else "weaken"
        elif claim.claim_type == "event_claim":
            verdict = "weaken"
        else:
            verdict = "unknown"

        if adapter_claim:
            reason = "由 L2 claim_type 与 confidence 映射的结构审查。"
            blocking = [] if verdict == "pass" else ["需真实 L3 结构策略复核"]
            required_support = [] if verdict == "pass" else ["L3 structure policy"]
            verdict_confidence = min(0.7, max(0.2, claim.confidence))
        else:
            reason = "L3 只审查结构基础；事件、应期与旁证命题不得在本层直接定案。"
            blocking = [] if verdict == "pass" else ["需要结构命题继续支撑"]
            required_support = ["ziping", "ditiansui"] if verdict != "pass" else []
            verdict_confidence = 0.6 if verdict == "pass" else 0.35

        if not adapter_claim and claim.confidence <= 0.1:
            verdict = "reject"
            verdict_confidence = claim.confidence

        if profile and verdict in {"pass", "weaken"}:
            shishen = shishen_in_statement(claim.statement)
            hits_avoid = shishen & profile["avoid"]
            hits_favor = shishen & profile["favor"]
            if hits_avoid and not hits_favor:
                reason = f"命题依赖格局忌神 {sorted(hits_avoid)}（{profile['geju_type']}），与用神方向不一致，降级。"
                blocking = [f"忌神方向：{sorted(hits_avoid)}"]
                if verdict == "pass":
                    verdict = "weaken"
                elif verdict == "weaken" and claim.confidence < 0.3:
                    verdict = "reject"

        verdicts.append(
            StructuralVerdict(
                verdict_id=_stable_id("dsv", case_id, claim.claim_id),
                claim_id=claim.claim_id,
                verdict=verdict,  # type: ignore[arg-type]
                structural_reason=reason,
                blocking_factors=blocking,
                required_support=required_support,
                confidence=verdict_confidence,
            )
        )
    return verdicts
