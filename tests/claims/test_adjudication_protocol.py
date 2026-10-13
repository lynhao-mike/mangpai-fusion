"""统一目标级裁决单位协议测试。"""

from dataclasses import replace

from engine.claims.domain import Claim, Evidence
from engine.decision.adjudication_protocol import AdjudicationUnit
from engine.decision.l6_staged_arbitration import ConflictRuleSet, arbitrate_staged


def _claim(claim_id: str, *, polarity: str = "positive") -> Claim:
    return Claim(
        claim_id=claim_id,
        school_id="synthetic",
        task_id="structure.overview",
        claim_type="structure_claim",
        stance="support",
        statement=f"claim {claim_id}",
        evidence=(Evidence(
            evidence_id=f"e-{claim_id}",
            fact_refs=("chart.four_pillars.day",),
            feature_refs=(),
            rule_id="rule.synthetic",
            text="synthetic fact",
        ),),
        falsifier=f"falsifier {claim_id}",
        time_window=None,
        confidence_basis="synthetic",
        applicability_snapshot={"condition": True},
        domain="总体",
        polarity=polarity,  # type: ignore[arg-type]
        target_id="structure.test",
    )


def test_primary_unit_keeps_trace_and_winner() -> None:
    claim = _claim("winner")
    result = arbitrate_staged("case", [claim], None, conflict_rules=ConflictRuleSet.empty())
    leaf = result.stage("structure").domain_decisions[0]

    unit = AdjudicationUnit.from_stage_decision(leaf, [claim])

    assert unit.status == "PRIMARY"
    assert unit.winner_claim_ids == ("winner",)
    assert unit.supporting_fact_refs == ("chart.four_pillars.day",)
    assert unit.rule_ids == ("rule.synthetic",)
    assert unit.falsifiers == ("falsifier winner",)


def test_unresolved_unit_has_candidates_but_no_manual_winner() -> None:
    first = _claim("a")
    second = replace(_claim("b", polarity="negative"), confidence=0.99)
    result = arbitrate_staged("case", [first, second], None, conflict_rules=ConflictRuleSet.empty())
    leaf = result.stage("structure").domain_decisions[0]

    unit = AdjudicationUnit.from_stage_decision(leaf, [first, second])

    assert unit.status == "UNRESOLVED"
    assert set(unit.candidate_claim_ids) == {"a", "b"}
    assert unit.winner_claim_ids == ()

