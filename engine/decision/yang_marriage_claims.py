"""杨派婚姻三态结果到既有 L2 SchoolClaim 的局部边界。"""

from __future__ import annotations

from engine.claims import stable_claim_id
from engine.decision.models import SchoolClaim, SchoolRole
from engine.decision.yang_marriage import YangMarriageDiscrimination

_TASK_ID = "marriage.divorce_or_remarriage"
_EVENT_FAMILY_KEYS = frozenset(
    {
        "spouse_palace_event_anchor",
        "spouse_star_peer_interaction",
        "spouse_star_output_interaction",
        "spouse_star_configuration",
    }
)
_CONFIDENCE = 0.60


def build_yang_marriage_school_claims(
    result: YangMarriageDiscrimination,
    role: SchoolRole,
) -> tuple[SchoolClaim, ...]:
    """仅把证据完整的 event 映射为一个支持票；其他三态结果不发言。"""
    if result.state != "event" or role == "abstain":
        return ()

    families = tuple(
        family for family in result.families if family.family_key in _EVENT_FAMILY_KEYS
    )
    if (
        len(families) < 2
        or not result.source_rule_refs
        or any(not family.fact_refs and not family.feature_refs for family in families)
    ):
        return ()

    family_refs = {f"family:{family.family_key}" for family in families}
    rule_refs = {f"rule:{ref}" for ref in result.source_rule_refs if ref.strip()}
    fact_refs = {
        f"fact:{ref}"
        for family in families
        for ref in family.fact_refs
        if ref.strip()
    }
    feature_refs = {
        f"feature:{ref}"
        for family in families
        for ref in family.feature_refs
        if ref.strip()
    }
    if not rule_refs or not fact_refs or not feature_refs:
        return ()

    source_rules = "|".join(sorted(result.source_rule_refs))
    claim = SchoolClaim(
        claim_id=stable_claim_id("yang", _TASK_ID, result.case_id, source_rules),
        school="yang",
        role_granted_by_l1=role,
        domain="婚姻",
        claim_type="event_claim",
        statement=(
            "杨派原局夫妻宫事件锚与独立配偶结构交互同向，"
            "支持存在离婚或再婚事件风险，但不作必然判断。"
        ),
        evidence_refs=sorted(family_refs)
        + sorted(rule_refs)
        + sorted(fact_refs)
        + sorted(feature_refs),
        confidence=_CONFIDENCE,
        falsifier=result.falsifier,
        dependencies=[result.schema_version],
        metadata={
            "task_id": _TASK_ID,
            "stance": "support",
            "source_scope": "yang_marriage_discrimination",
            "family_keys": sorted(family.family_key for family in families),
        },
    )
    return (claim,)
