"""把现有 v5 输出映射成分层 DecisionRun。

ponytail: 这是迁移桥，不改 v5、不切生产入口；只证明真实 v5 产物能进入
L0-L7 账本。
"""

from __future__ import annotations

import hashlib
from typing import Any

from engine.decision.l1_school_router import route_schools
from engine.decision.l3_structure import build_structural_verdicts, extract_geju_profile
from engine.decision.l4_events import classify_event_type
from engine.decision.l8_feedback_attribution import build_feedback_attributions, build_feedback_signals
from engine.decision.l9_calibration import build_calibration_actions, build_router_calibration_actions
from engine.decision.models import (
    ArbitrationDecision,
    ChartFactLedger,
    ContextFactLedger,
    DecisionRun,
    EventHypothesis,
    RawWenzhenPayload,
    ReportViewItem,
    SchoolApplicability,
    SchoolClaim,
    StructuralVerdict,
    TimingProbability,
)
from engine.v5.domain import V5Output, V5RunSnapshot


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]}"


def _clamp_confidence(value: float) -> float:
    return min(1.0, max(0.0, value))


def _raw_text_from_output(output: V5Output) -> str:
    """生成迁移期 L0 raw_text；脏测试对象无法完整序列化时降级为最小结构。"""

    try:
        return output.to_json(indent=None)
    except (KeyError, TypeError, ValueError):
        return f"{output.schema_version}|{output.case_id}|{sorted(output.chart)}"


def _chart_to_ledger(output: V5Output, raw_hash: str) -> ChartFactLedger:
    chart = output.chart
    pillars = chart.get("pillars") or chart.get("四柱") or {}
    if isinstance(pillars, list):
        four = {key: value for key, value in zip(("year", "month", "day", "hour"), [str(item) for item in pillars]) if value.strip() and value.strip() != "_"}
    elif isinstance(pillars, dict):
        four = {str(k): str(v) for k, v in pillars.items() if str(v).strip() and str(v).strip() != "_"}
    else:
        four = {}
    missing = [f"$FOUR.{key}" for key in ("year", "month", "day", "hour") if key not in four or not four[key].strip() or four[key].strip() == "_"]
    return ChartFactLedger(
        sex_marker=str(chart.get("gender_marker") or chart.get("命式") or chart.get("sex") or ""),
        solar_datetime=str(chart.get("solar_datetime") or chart.get("公历") or ""),
        four_pillars=four,
        start_luck=str(chart.get("start_luck") or chart.get("起运时间") or ""),
        dayun_steps=list(chart.get("dayun_steps") or []),
        liunian_steps=list(chart.get("liunian_steps") or []),
        missing_fields=missing,
        raw_source_hash=raw_hash,
    )


def _claims(output: V5Output, applicability: list[SchoolApplicability]) -> list[SchoolClaim]:
    role_by_school = {item.school: item.role for item in applicability}
    return [
        SchoolClaim(
            claim_id=claim.claim_id,
            school=claim.school,
            role_granted_by_l1=role_by_school.get(claim.school, "co_lead"),  # type: ignore[arg-type]
            domain=claim.domain,
            claim_type=claim.claim_type,
            statement=claim.claim,
            evidence_refs=[evidence.evidence_id for evidence in claim.evidence],
            confidence=_clamp_confidence(claim.confidence.score),
            falsifier=claim.falsifiable,
            dependencies=[f"v5:{claim.claim_id}"],
            metadata=dict(claim.metadata),
        )
        for claim in output.claims
        if (
            claim.claim_id
            and claim.school
            and claim.domain
            and claim.stance != "abstain"
            and role_by_school.get(claim.school) != "abstain"
        )
    ]


_extract_geju_profile = extract_geju_profile


def _verdicts(case_id: str, claims: list[SchoolClaim]) -> list[StructuralVerdict]:
    return build_structural_verdicts(case_id, claims)


def _events(case_id: str, output: V5Output, verdicts: list[StructuralVerdict], claims: list[SchoolClaim]) -> list[EventHypothesis]:
    claim_domain_by_id = {item.claim_id: item.domain for item in claims}
    source_ids_by_domain: dict[str, list[str]] = {}
    for verdict in verdicts:
        if verdict.verdict not in {"pass", "weaken"}:
            continue
        domain = claim_domain_by_id.get(verdict.claim_id, "")
        if domain:
            source_ids_by_domain.setdefault(domain, []).append(verdict.verdict_id)
    if not source_ids_by_domain:
        return []
    events: list[EventHypothesis] = []
    for prediction in output.prediction_ledger.predictions:
        if not prediction.prediction_id or not prediction.domain:
            continue
        if prediction.probability_range[0] > prediction.probability_range[1] or prediction.probability_range[0] < 0.0 or prediction.probability_range[1] > 1.0:
            continue
        source_ids = source_ids_by_domain.get(prediction.domain, [])
        if not source_ids:
            continue
        events.append(
            EventHypothesis(
                event_id=_stable_id("dev", case_id, prediction.prediction_id),
                source_verdict_ids=source_ids[:3],
                domain=prediction.domain,
                event_type=classify_event_type(prediction.event_label, prediction.domain),
                subject=prediction.domain,
                concrete_event=prediction.event_label,
                landing_path="由 v5 prediction ledger 迁移为 L4 事件假设。",
                confidence=_clamp_confidence(prediction.confidence.score),
            )
        )
    return events


def _timings(case_id: str, output: V5Output, event_by_prediction: dict[str, str]) -> list[TimingProbability]:
    return [
        TimingProbability(
            prediction_id=prediction.prediction_id,
            event_id=event_by_prediction[prediction.prediction_id],
            time_window=dict(prediction.time_window),
            trigger_conditions=list(prediction.trigger_conditions),
            probability_range=prediction.probability_range,
            confidence=_clamp_confidence(prediction.confidence.score),
            falsifier=prediction.falsifier,
        )
        for prediction in output.prediction_ledger.predictions
        if prediction.prediction_id in event_by_prediction and prediction.probability_range[0] <= prediction.probability_range[1] and 0.0 <= prediction.probability_range[0] and prediction.probability_range[1] <= 1.0
    ]


def _decisions(case_id: str, output: V5Output, events: list[EventHypothesis], applicability: list[SchoolApplicability]) -> list[ArbitrationDecision]:
    events_by_domain: dict[str, list[str]] = {}
    for event in events:
        events_by_domain.setdefault(event.domain, []).append(event.event_id)
    decisions: list[ArbitrationDecision] = []
    for idx, result in enumerate(output.arbitration_results, start=1):
        if result.stage != "event_realization" or not result.domain:
            continue
        competing = events_by_domain.get(result.domain, [])
        if not competing:
            continue
        if result.winning_schools:
            decision_result = "winner"
            winner_ids = competing
            rejected_ids: list[str] = []
            unresolved_ids: list[str] = []
        elif result.opposition_score > result.support_score:
            decision_result = "reject_all"
            winner_ids = []
            rejected_ids = competing
            unresolved_ids = []
        else:
            decision_result = "unresolved"
            winner_ids = []
            rejected_ids = []
            unresolved_ids = competing
        decisions.append(
            ArbitrationDecision(
                decision_id=_stable_id("dad", case_id, result.domain, result.stage, idx),
                domain=result.domain,
                competing_event_ids=competing,
                result=decision_result,  # type: ignore[arg-type]
                winner_ids=winner_ids,
                rejected_ids=rejected_ids,
                unresolved_ids=unresolved_ids,
                arbitration_rule="由 v5 event_realization 仲裁结果迁移。",
                school_applicability_snapshot=applicability,
                reason=result.rationale or result.conclusion,
            )
        )
    return decisions


_SCHOOL_ZH = {
    "ziping": "子平类",
    "ditiansui": "滴天髓类",
    "gao_dechen": "高德臣",
    "duan_jianye": "段建业",
    "yang_qingjuan": "杨清娟",
    "ren_fuhong": "任付红",
}


def _domain_evidence(
    domain: str,
    claims: list[SchoolClaim],
) -> tuple[list[str], list[str], int, dict[str, list[str]]]:
    evidence_domains = {"总体", "事业"} if domain == "事业" else {domain}
    domain_claims = [
        claim
        for claim in claims
        if claim.domain in evidence_domains and claim.statement
    ]
    school_evidence: dict[str, list[str]] = {}
    for claim in domain_claims:
        school_evidence.setdefault(claim.school, []).append(claim.statement)

    schools = [_SCHOOL_ZH.get(school, school) for school in school_evidence]
    evidences = [
        f"{_SCHOOL_ZH.get(school, school)}：{'；'.join(statements)}"
        for school, statements in school_evidence.items()
    ]
    return schools, evidences, len(domain_claims), school_evidence


def _report_items(
    case_id: str,
    decisions: list[ArbitrationDecision],
    timings: list[TimingProbability],
    claims: list[SchoolClaim] | None = None,
) -> list[ReportViewItem]:
    timing_by_domain = {timing.event_id: timing for timing in timings}
    items: list[ReportViewItem] = []
    for decision in decisions:
        event_ids = decision.rejected_ids if decision.result == "reject_all" else decision.winner_ids or decision.competing_event_ids
        schools, evidences, claim_count, school_evidence = _domain_evidence(
            decision.domain, claims or []
        )
        display_text = f"{decision.domain}：{decision.reason}"
        if schools:
            display_text += "｜参与流派：" + "、".join(schools)
        if evidences:
            display_text += "｜依据：" + "；".join(evidences)
        for idx, event_id in enumerate(event_ids, start=1):
            timing = timing_by_domain.get(event_id)
            confidence_text = "迁移期，以 v5 置信度为准"
            timing_text = "未形成 L5 时间窗"
            if timing:
                confidence_text = f"{timing.confidence:.0%}"
                timing_text = str(timing.time_window or "未标定")
            item_display_text = (
                f"{display_text}｜置信度：{confidence_text}｜应期：{timing_text}"
            )
            items.append(
                ReportViewItem(
                    report_item_id=_stable_id("drv", case_id, decision.decision_id, idx),
                    decision_id=decision.decision_id,
                    prediction_id=timing.prediction_id if timing else "",
                    display_text=item_display_text,
                    confidence_display=confidence_text,
                    evidence_summary=f"本域共 {claim_count} 条流派命题参与结构裁决。" if claim_count else "L7 只读 v5→decision 适配后的 L6/L5 结果。",
                    school_evidence=school_evidence,
                    feedback_prompt="按预测账本反馈命中、失验、半命中或跳过。",
                )
            )
    return items


def decision_run_from_v5(output: V5Output, *, raw_text: str = "") -> DecisionRun:
    """把 V5Output 包成 DecisionRun，不改变 v5 行为。"""

    raw = raw_text or _raw_text_from_output(output)
    raw_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    payload = RawWenzhenPayload(raw_text=raw, raw_hash=raw_hash, parser_version="decision-v5-adapter")
    chart = _chart_to_ledger(output, raw_hash)
    context = ContextFactLedger(preserved_text_blocks=["v5_adapter"])
    applicability = route_schools(chart, context)
    claims = _claims(output, applicability)
    case_id = output.case_id or "V5-UNKNOWN"
    verdicts = _verdicts(case_id, claims)
    events = _events(case_id, output, verdicts, claims)
    valid_predictions = [
        prediction
        for prediction in output.prediction_ledger.predictions
        if prediction.prediction_id and prediction.domain and prediction.probability_range[0] <= prediction.probability_range[1] and 0.0 <= prediction.probability_range[0] and prediction.probability_range[1] <= 1.0
    ]
    event_ids = {event.event_id for event in events}
    event_by_prediction = {
        prediction.prediction_id: event_id
        for prediction in valid_predictions
        for event_id in [_stable_id("dev", case_id, prediction.prediction_id)]
        if event_id in event_ids
    }
    timings = _timings(case_id, output, event_by_prediction)
    decisions = _decisions(case_id, output, events, applicability)
    report_items = _report_items(case_id, decisions, timings, claims)
    feedback_signals = build_feedback_signals(case_id, report_items)
    feedback_attributions = build_feedback_attributions(feedback_signals)
    calibration_actions = build_calibration_actions(case_id, feedback_attributions)
    calibration_actions = calibration_actions + build_router_calibration_actions(
        case_id, report_items, decisions, feedback_signals
    )
    return DecisionRun(
        run_id=_stable_id("drun", case_id, raw_hash),
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


def decision_run_from_snapshot(snapshot: V5RunSnapshot) -> DecisionRun:
    """从 run snapshot 派生裁判账本，保持 snapshot 是事实源。"""

    output = snapshot.to_output()
    return decision_run_from_v5(output, raw_text=output.to_json(indent=None))
