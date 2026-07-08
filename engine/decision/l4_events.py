"""L4 事件落地层最小实现。"""

from __future__ import annotations

import hashlib

from engine.decision.models import EventHypothesis, SchoolClaim, StructuralVerdict


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]}"


def build_event_hypotheses(case_id: str, verdicts: list[StructuralVerdict], claims: list[SchoolClaim]) -> list[EventHypothesis]:
    """把结构审查后的命题落成可反馈事件；不改写结构裁决。"""

    claim_by_id = {item.claim_id: item for item in claims}
    passed = [item.verdict_id for item in verdicts if item.verdict in {"pass", "weaken"}]
    event_claims = [item for item in claims if item.claim_type == "event" and item.role_granted_by_l1 != "evidence_only"]
    events: list[EventHypothesis] = []
    for claim in event_claims[:2]:
        events.append(
            EventHypothesis(
                event_id=_stable_id("dev", case_id, claim.claim_id),
                source_verdict_ids=passed[:2] or [_stable_id("dsv", case_id, claim.claim_id)],
                domain=claim.domain,
                event_type="可反馈现实事件",
                subject=claim.school,
                concrete_event=claim.statement,
                landing_path="L4 只把通过结构审查的命题落成现实事件，不改写结构裁决。",
                confidence=min(0.65, claim.confidence),
            )
        )
    if not events and verdicts:
        claim = claim_by_id[verdicts[0].claim_id]
        if claim.claim_type != "structure":
            return []
        events.append(
            EventHypothesis(
                event_id=_stable_id("dev", case_id, claim.claim_id, "fallback"),
                source_verdict_ids=[verdicts[0].verdict_id],
                domain=claim.domain,
                event_type="待具体化事件",
                subject=claim.school,
                concrete_event="结构命题已登记，但事件层仍需真实 runner 接入。",
                landing_path="兜底事件槽位，仅证明链路，不作为正式断语。",
                confidence=0.3,
            )
        )
    return events
