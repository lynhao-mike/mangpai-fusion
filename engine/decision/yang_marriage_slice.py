"""杨派婚姻 event-only 专用 L2-L6 纵切片。"""

from __future__ import annotations

from dataclasses import replace

from engine.decision import v5_adapter
from engine.decision.l3_structure import build_structural_verdicts
from engine.decision.l4_events import build_event_hypotheses
from engine.decision.l5_timing import build_timing_probabilities
from engine.decision.l6_arbitration import build_arbitration_decisions
from engine.decision.models import (
    ArbitrationDecision,
    ChartFactLedger,
    EventHypothesis,
    SchoolApplicability,
    SchoolClaim,
    SchoolRole,
    StructuralVerdict,
    TimingProbability,
)
from engine.decision.yang_marriage import (
    YangMarriageDiscrimination,
    discriminate_yang_marriage,
)
from engine.decision.yang_marriage_claims import build_yang_marriage_school_claims
from engine.features.types import ChartFeatureVector
from engine.v5.domain import V5Output

_TARGET_TASK = "marriage.divorce_or_remarriage"
_TARGET_SCHOOL = "yang_qingjuan"


def _is_yang_marriage_target(claim: object) -> bool:
    metadata = getattr(claim, "metadata", {}) or {}
    return (
        getattr(claim, "school", None) == _TARGET_SCHOOL
        and getattr(claim, "domain", None) == "婚姻"
        and metadata.get("task_id") == _TARGET_TASK
    )


def _reject_duplicate_claim_ids(claims: list[SchoolClaim]) -> None:
    seen: set[str] = set()
    for claim in claims:
        if claim.claim_id in seen:
            raise ValueError(f"duplicate L2 claim_id: {claim.claim_id}")
        seen.add(claim.claim_id)


def to_yang_marriage_school_claim(
    result: YangMarriageDiscrimination,
    role: SchoolRole,
) -> SchoolClaim:
    """仅接受 event，并复用既有局部 SchoolClaim 适配契约。"""
    if result.state != "event":
        raise ValueError("yang marriage adapter accepts event only")
    claims = build_yang_marriage_school_claims(result, role)
    if len(claims) != 1:
        raise ValueError("yang marriage event requires complete structural evidence")
    return claims[0]


def apply_yang_marriage_slice(
    output: V5Output,
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    applicability: list[SchoolApplicability],
) -> tuple[
    YangMarriageDiscrimination,
    list[SchoolClaim],
    list[StructuralVerdict],
    list[EventHypothesis],
    list[TimingProbability],
    list[ArbitrationDecision],
]:
    """剥离旧目标，仅让局部 event 进入现有 L2-L6 builders。"""
    case_id = output.case_id or features.chart_id
    result = discriminate_yang_marriage(case_id, chart, features)
    yang_roles = [item for item in applicability if item.school == _TARGET_SCHOOL]
    if len(yang_roles) > 1:
        raise ValueError("duplicate yang_qingjuan applicability")

    legacy_output = replace(
        output,
        claims=[claim for claim in output.claims if not _is_yang_marriage_target(claim)],
    )
    legacy_l2 = v5_adapter._claims(legacy_output, applicability)
    role: SchoolRole = yang_roles[0].role if yang_roles else "abstain"
    native_l2 = (
        []
        if result.state != "event" or role == "abstain"
        else [to_yang_marriage_school_claim(result, role)]
    )
    # 专用切片必须让唯一目标越过公共 L4 的前两项 cap；既有非目标相对顺序不变。
    claims = native_l2 + legacy_l2
    _reject_duplicate_claim_ids(claims)

    verdicts = build_structural_verdicts(case_id, claims)
    events = build_event_hypotheses(case_id, verdicts, claims)
    timings = build_timing_probabilities(case_id, events)
    decisions = build_arbitration_decisions(case_id, events, applicability)
    return result, claims, verdicts, events, timings, decisions
