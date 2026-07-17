from dataclasses import replace

import pytest

from engine.claims import stable_claim_id
from engine.decision.yang_marriage import (
    YangMarriageDiscrimination,
    YangMarriageFamilyEvidence,
)
from engine.decision.yang_marriage_claims import build_yang_marriage_school_claims
from tests.yang_marriage.test_domain_model import discrimination, family


_TASK_ID = "marriage.divorce_or_remarriage"


def _event() -> YangMarriageDiscrimination:
    return discrimination(
        state="event",
        families=(
            family("spouse_star_peer_interaction"),
            family("spouse_palace_event_anchor"),
        ),
        event_anchor_passed=True,
        independent_spouse_interaction_passed=True,
        blocking_reason_codes=(),
    )


@pytest.mark.parametrize(
    "result",
    (
        discrimination(
            state="pressure",
            families=(family("spouse_palace_event_anchor"),),
            event_anchor_passed=True,
            independent_spouse_interaction_passed=False,
            blocking_reason_codes=("missing_independent_spouse_interaction",),
        ),
        discrimination(
            state="abstain",
            families=(),
            event_anchor_passed=False,
            independent_spouse_interaction_passed=False,
            blocking_reason_codes=("insufficient_yang_marriage_signal",),
            sex_basis="unknown",
            spouse_palace_branch="",
        ),
    ),
)
def test_pressure_and_abstain_emit_no_claim(result: YangMarriageDiscrimination) -> None:
    assert build_yang_marriage_school_claims(result, "lead") == ()


def test_event_emits_one_conservative_support_claim() -> None:
    claims = build_yang_marriage_school_claims(_event(), "lead")

    assert len(claims) == 1
    claim = claims[0]
    assert claim.school == "yang"
    assert claim.domain == "婚姻"
    assert claim.claim_type == "event_claim"
    assert claim.role_granted_by_l1 == "lead"
    assert claim.confidence == 0.60
    assert claim.metadata["stance"] == "support"
    assert claim.metadata["task_id"] == _TASK_ID
    assert not any(text in claim.statement for text in ("必离", "100%", "多婚命"))


def test_claim_id_and_family_evidence_chain_are_stable_and_deduplicated() -> None:
    anchor = YangMarriageFamilyEvidence(
        family_key="spouse_palace_event_anchor",
        matched=True,
        fact_refs=("four_pillars.day", "four_pillars.day"),
        feature_refs=("xing_hai_pairs", "chong_pairs", "chong_pairs"),
        canonical_pairs=(("午", "子"), ("午", "子")),
        reason_codes=("day_branch_disrupted", "day_branch_disrupted"),
        detail="日支受扰。",
    )
    interaction = YangMarriageFamilyEvidence(
        family_key="spouse_star_peer_interaction",
        matched=True,
        fact_refs=("sex_marker", "sex_marker"),
        feature_refs=("ten_god_counts.劫财", "has_wealth", "has_wealth"),
        canonical_pairs=(),
        reason_codes=("male_wealth_peer_interaction",),
        detail="财星与比劫交互。",
    )
    result = replace(
        _event(),
        families=(interaction, anchor),
        source_rule_refs=(
            "theory/yang/index.yaml#M2-Y-088",
            "theory/yang/index.yaml#M2-Y-068",
            "theory/yang/index.yaml#M2-Y-068",
        ),
    )

    first = build_yang_marriage_school_claims(result, "co_lead")[0]
    second = build_yang_marriage_school_claims(result, "co_lead")[0]

    assert first.to_dict() == second.to_dict()
    assert first.claim_id == stable_claim_id(
        "yang",
        _TASK_ID,
        result.case_id,
        "theory/yang/index.yaml#M2-Y-068|theory/yang/index.yaml#M2-Y-088",
    )
    assert first.evidence_refs == [
        "family:spouse_palace_event_anchor",
        "family:spouse_star_peer_interaction",
        "rule:theory/yang/index.yaml#M2-Y-068",
        "rule:theory/yang/index.yaml#M2-Y-088",
        "fact:four_pillars.day",
        "fact:sex_marker",
        "feature:chong_pairs",
        "feature:has_wealth",
        "feature:ten_god_counts.劫财",
        "feature:xing_hai_pairs",
    ]


@pytest.mark.parametrize(
    "result",
    (
        replace(_event(), source_rule_refs=()),
        replace(
            _event(),
            families=(
                replace(family("spouse_palace_event_anchor"), fact_refs=(), feature_refs=()),
                family("spouse_star_peer_interaction"),
            ),
        ),
    ),
)
def test_event_with_missing_rule_or_family_evidence_fails_closed(
    result: YangMarriageDiscrimination,
) -> None:
    assert build_yang_marriage_school_claims(result, "lead") == ()
