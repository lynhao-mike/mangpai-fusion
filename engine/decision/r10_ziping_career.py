"""R10 第一证明物：子平·事业域 L2-L4 原生纵切片。"""

from __future__ import annotations

import hashlib
from dataclasses import replace

from engine.decision import v5_adapter
from engine.decision.l1_school_router import route_schools
from engine.decision.l2_v5_claims import to_school_claim
from engine.decision.l3_structure import build_structural_verdicts
from engine.decision.l4_events import build_event_hypotheses
from engine.decision.l5_timing import build_timing_probabilities
from engine.decision.l6_arbitration import build_arbitration_decisions
from engine.decision.l8_feedback_attribution import (
    build_feedback_attributions,
    build_feedback_signals,
)
from engine.decision.l9_calibration import (
    build_calibration_actions,
    build_router_calibration_actions,
)
from engine.decision.models import (
    ContextFactLedger,
    DecisionRun,
    EventHypothesis,
    RawWenzhenPayload,
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


def build_ziping_career_decision_run(
    output: V5Output,
    raw_text: str = "",
    *,
    run_id: str | None = None,
) -> DecisionRun:
    """逐层装配子平·事业纵切片的唯一 DecisionRun。"""

    raw = raw_text or v5_adapter._raw_text_from_output(output)
    raw_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    payload = RawWenzhenPayload(
        raw_text=raw,
        raw_hash=raw_hash,
        parser_version="decision-r10-ziping-career",
    )
    # ponytail: 仅复用迁移桥的 chart DTO 映射，不参与 L1-L4 判断；R10 全迁移时删除。
    chart = v5_adapter._chart_to_ledger(output, raw_hash)
    context = ContextFactLedger(preserved_text_blocks=["r10_ziping_career"])
    applicability = route_schools(chart, context)
    claims, verdicts, events = apply_ziping_career_slice(output, applicability)
    case_id = output.case_id or "V5-UNKNOWN"
    timings = build_timing_probabilities(case_id, events)
    decisions = build_arbitration_decisions(case_id, events, applicability)
    # ponytail: 独立 L7 文本尚不足以维持 R6 信息量；兼容 builder 只表达既有 L2/L6，不新增判断。
    report_items = v5_adapter._report_items(case_id, decisions, timings, claims)
    feedback_signals = build_feedback_signals(case_id, report_items)
    feedback_attributions = build_feedback_attributions(feedback_signals)
    calibration_actions = build_calibration_actions(case_id, feedback_attributions)
    calibration_actions += build_router_calibration_actions(
        case_id, report_items, decisions, feedback_signals
    )
    return DecisionRun(
        run_id=run_id or v5_adapter._stable_id("drun", case_id, raw_hash),
        case_id=case_id,
        raw_payload=payload,
        chart_ledger=chart,
        context_ledger=context,
        school_applicability=applicability,
        school_claims=claims,
        structural_verdicts=verdicts,
        event_hypotheses=events,
        timing_probabilities=timings,
        arbitration_decisions=decisions,
        report_items=report_items,
        feedback_signals=feedback_signals,
        feedback_attributions=feedback_attributions,
        calibration_actions=calibration_actions,
    )
