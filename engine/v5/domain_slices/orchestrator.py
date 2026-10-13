"""六源三领域分析编排器。"""

from __future__ import annotations

import hashlib
from typing import Any

from engine.v5.domain import (
    V5Claim,
    V5Confidence,
    V5Evidence,
    V5Output,
    V5PredictionLedger,
    V5RunSnapshot,
    V5_SCHOOLS,
)
from engine.v5.domain_metadata_integrity import build_domain_evaluation_metadata, seal_capability_metadata
from engine.v5.adjudication import build_v5_adjudication_units
from engine.v5.domain_slices import build_domain_registry
from engine.v5.domain_slices.context import build_analysis_context
from engine.v5.domain_slices.contract import DomainAnalysisContext, DomainAnalysisRequest, SliceAudit, SliceResult
from engine.v5.domain_slices.registry import DomainSliceRegistry, SliceRegistration
from engine.v5.high_risk_gate import apply_high_risk_gate
from engine.v5.runner import (
    arbitrate_claims,
    build_learning_signals,
    build_structure_graph,
    prepare_claims_for_adjudication,
)

DOMAIN_NAMES = {"career": "事业", "wealth": "财富", "marriage": "婚姻"}


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def _chart(context: DomainAnalysisContext) -> dict[str, Any]:
    year, month, day, hour = context.pillars
    return {
        "case_id": context.case_id,
        "gender_marker": context.request.gender,
        "birth_datetime": context.request.birth_datetime.isoformat(sep=" ", timespec="seconds"),
        "as_of_date": context.request.as_of_date.isoformat(),
        "pillars": {"year": year, "month": month, "day": day, "hour": hour},
        "year_stem": year[0],
        "year_branch": year[1],
        "month_stem": month[0],
        "month_branch": month[1],
        "day_stem": day[0],
        "day_branch": day[1],
        "hour_stem": hour[0],
        "hour_branch": hour[1],
        "current_dayun": str(context.current_dayun["ganzhi"]),
        "dayun": [dict(item) for item in context.dayun],
        "future_years": [{"year": year_value, "ganzhi": ganzhi} for year_value, ganzhi in context.future_years],
        "calculator": context.calculator,
        "domain_analysis_request": context.request.to_dict(),
    }


def _abstain_claim(context: DomainAnalysisContext, registration: SliceRegistration, result: SliceResult) -> V5Claim:
    domain_name = DOMAIN_NAMES[registration.domain]
    status = result.status
    evidence = V5Evidence(
        evidence_id=_stable_id("v5ev", context.case_id, registration.school, registration.domain, status),
        source="domain_slice_registry",
        text=f"{registration.school} 在{domain_name}领域状态为 {status}。",
        node_refs=["chart:root"],
        metadata={"slice_status": status, "reason": result.audit.reason},
    )
    return V5Claim(
        claim_id=_stable_id("v5cl", context.case_id, registration.school, registration.domain, status),
        school=registration.school,
        domain=domain_name,
        claim="证据不足，本派在该领域克制判断。" if status == "abstain" else "本派在该领域暂不支持。",
        claim_type="timing_claim" if registration.school == "ren_fuhong" else "evidence_claim",
        stance="abstain",
        confidence=V5Confidence(tier="★", score=0.1, note="显式弃权，不进入正反证计分"),
        evidence=[evidence],
        falsifiable="切片接入完整规则与证据后，本占位命题应消失。",
        metadata={"runner_state": "domain_slice", "slice_status": status},
    )


def _run_slice(context: DomainAnalysisContext, registration: SliceRegistration) -> SliceResult:
    if registration.status != "implemented":
        reason = "P1 explicit abstain placeholder" if registration.status == "abstain" else "slice unsupported"
        return SliceResult(
            school=registration.school,
            domain=registration.domain,
            status=registration.status,
            audit=SliceAudit(reason=reason),
        )
    try:
        result = registration.generator(context)  # type: ignore[misc]
    except Exception as exc:
        return SliceResult(
            school=registration.school,
            domain=registration.domain,
            status="abstain",
            audit=SliceAudit(reason="slice execution failed", error_type=type(exc).__name__),
        )
    if result.school != registration.school or result.domain != registration.domain:
        raise ValueError("slice result identity does not match registration")
    return result


def run_domain_analysis(
    request: DomainAnalysisRequest,
    *,
    registry: DomainSliceRegistry | None = None,
) -> V5RunSnapshot:
    """运行请求中的领域，并保留完整十八槽位覆盖审计。"""

    resolved_registry = registry or build_domain_registry()
    context = build_analysis_context(request)
    coverage: list[dict[str, Any]] = []
    claims: list[V5Claim] = []
    requested = set(request.domains)

    for key in resolved_registry.keys():
        registration = resolved_registry.resolve(*key)
        if registration.domain in requested:
            result = _run_slice(context, registration)
            claims.extend(result.claims)
            if not result.claims:
                claims.append(_abstain_claim(context, registration, result))
            coverage.append(result.to_dict() | {"claims": []})
        else:
            coverage.append(
                {
                    "school": registration.school,
                    "domain": registration.domain,
                    "status": registration.status,
                    "claims": [],
                    "audit": {"reason": "not requested", "error_type": ""},
                }
            )

    claims.sort(key=lambda claim: (request.domains.index(next(key for key, value in DOMAIN_NAMES.items() if value == claim.domain)), V5_SCHOOLS.index(claim.school), claim.claim_id))
    claims, high_risk_gate_audit = apply_high_risk_gate(claims)
    chart = _chart(context)
    graph = build_structure_graph(context.case_id, chart, claims)
    arbitrations = arbitrate_claims(claims)
    adjudication_units = build_v5_adjudication_units(
        prepare_claims_for_adjudication(claims)
    )
    ledger = V5PredictionLedger(case_id=context.case_id, predictions=[])
    output = V5Output(
        case_id=context.case_id,
        chart=chart,
        claims=claims,
        structure_graph=graph,
        arbitration_results=arbitrations,
        prediction_ledger=ledger,
        learning_signals=build_learning_signals(context.case_id, claims, ledger),
        adjudication_units=list(adjudication_units),
    )
    domain_conclusions = {
        domain: "证据不足"
        for domain in request.domains
        if not any(claim.domain == DOMAIN_NAMES[domain] and claim.stance != "abstain" for claim in claims)
    }
    metadata = seal_capability_metadata(
        {
            "requested_domains": list(request.domains),
            "slice_coverage": coverage,
            "domain_conclusions": domain_conclusions,
            "high_risk_gate": high_risk_gate_audit,
            "production_ready": False,
            **build_domain_evaluation_metadata(claims),
        }
    )
    return V5RunSnapshot.from_output(
        output,
        engine_version="domain-analysis-p3-three-domains",
        metadata=metadata,
    )
