"""事业域六源切片：复用既有可审计 runner，并在边界统一为 V5Claim。"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence

from engine.claims import Claim
from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindTask
from engine.features import ChartFeatureVector, build_chart_feature_vector
from engine.v5 import ditiansui_runner, duan_runner, gao_runner, ren_runner, ziping_runner
from engine.v5.domain import V5Claim, V5Confidence, V5Evidence, V5_SCHOOLS, V5School
from engine.v5.domain_slices.contract import DOMAIN_IDS, DomainAnalysisContext, SliceAudit, SliceResult
from engine.v5.domain_slices.registry import DomainSliceRegistry, SliceRegistration
from engine.v5.high_risk_gate import HIGH_RISK_TASKS

LegacyGenerator = Callable[[ChartFactLedger, ChartFeatureVector, BlindTask], list[Claim]]

_TASK_TYPES = {
    "structure.overview": "structure_claim",
    "career.role_change": "event_claim",
    "career.path_type": "event_claim",
    "career.change_window": "timing_claim",
    "wealth.debt": "event_claim",
    "wealth.major_loss_window": "timing_claim",
    "marriage.late_marriage": "event_claim",
    "marriage.divorce_or_remarriage": "event_claim",
    "marriage.event_window": "timing_claim",
}


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def _dayun_steps(context: DomainAnalysisContext) -> list[dict[str, object]]:
    ordered = sorted((dict(item) for item in context.dayun), key=lambda item: int(item["start_year"]))
    output: list[dict[str, object]] = []
    for index, item in enumerate(ordered):
        start = int(item["start_year"])
        next_start = int(ordered[index + 1]["start_year"]) if index + 1 < len(ordered) else start + 10
        output.append(
            {
                "ganzhi": str(item["ganzhi"]),
                "start_year": start,
                "end_year": int(item.get("end_year", next_start - 1)),
            }
        )
    return output


def _dayun_for_year(steps: Sequence[dict[str, object]], year: int) -> str:
    for step in steps:
        if int(step["start_year"]) <= year <= int(step["end_year"]):
            return str(step["ganzhi"])
    return ""


def context_to_chart_ledger(context: DomainAnalysisContext) -> ChartFactLedger:
    """把领域上下文无损转换成旧 L2 runner 的只读命盘事实账本。"""

    year, month, day, hour = context.pillars
    dayun_steps = _dayun_steps(context)
    liunian_steps = [
        {
            "year": future_year,
            "ganzhi": ganzhi,
            "dayun": _dayun_for_year(dayun_steps, future_year),
        }
        for future_year, ganzhi in context.future_years
    ]
    return ChartFactLedger(
        sex_marker=context.request.gender,
        solar_datetime=context.request.birth_datetime.isoformat(sep=" ", timespec="seconds"),
        four_pillars={"year": year, "month": month, "day": day, "hour": hour},
        dayun_steps=dayun_steps,
        liunian_steps=liunian_steps,
    )


def _confidence_tier(score: float) -> str:
    if score >= 0.75:
        return "★★★★★"
    if score >= 0.65:
        return "★★★★"
    if score >= 0.5:
        return "★★★"
    if score >= 0.3:
        return "★★"
    return "★"


def adapt_legacy_claim(
    legacy: Claim,
    *,
    public_school: V5School,
    public_domain: str = "事业",
) -> V5Claim:
    """适配旧 Claim；重新生成公开 ID，避免内部短 school ID 泄露到 snapshot。"""

    evidence = [
        V5Evidence(
            evidence_id=_stable_id(
                "v5ev",
                public_school,
                legacy.task_id,
                item.rule_id,
                *item.fact_refs,
                *item.feature_refs,
            ),
            source=public_school,
            text=item.text,
            node_refs=[*item.fact_refs, *(f"feature:{ref}" for ref in item.feature_refs)],
            rule_ids=[item.rule_id],
            metadata={"adapter": "legacy_claim_v1"},
        )
        for item in legacy.evidence
    ]
    rule_signature = ",".join(rule_id for item in evidence for rule_id in item.rule_ids)
    timing_hints = [legacy.time_window.to_dict()] if legacy.time_window else []
    return V5Claim(
        claim_id=_stable_id("v5cl", public_school, legacy.task_id, legacy.statement, rule_signature),
        school=public_school,
        domain=public_domain,
        claim=legacy.statement,
        claim_type=legacy.claim_type,
        stance=legacy.stance,
        polarity=legacy.polarity,
        confidence=V5Confidence(
            tier=_confidence_tier(legacy.confidence),
            score=legacy.confidence,
            note=legacy.confidence_basis,
        ),
        evidence=evidence,
        timing_hints=timing_hints,
        probabilistic=False,
        falsifiable=legacy.falsifier,
        metadata={
            "adapter": "legacy_claim_v1",
            "task_id": legacy.task_id,
            "high_risk": legacy.high_risk,
            "applicability_snapshot": dict(legacy.applicability_snapshot),
        },
    )


def _task(task_id: str, *, domain_name: str) -> BlindTask:
    claim_type = _TASK_TYPES[task_id]
    high_risk = task_id in HIGH_RISK_TASKS
    return BlindTask(
        task_id=task_id,
        domain=domain_name,
        claim_type=claim_type,
        scoring_method="domain-analysis-auditable-claim",
        quantifiable=False,
        high_risk=high_risk,
        allowed_time_horizons=["natal", "current_dayun", "next_three_years"],
        required_input_fields=["four_pillars"],
        label_schema={},
        evaluation_note="领域分析切片固定任务；不读取反馈标签。",
    )


def run_legacy_domain_slice(
    context: DomainAnalysisContext,
    *,
    public_school: V5School,
    tasks: Sequence[str],
    generator: LegacyGenerator,
    domain_id: str = "career",
    domain_name: str = "事业",
) -> SliceResult:
    """执行一个领域切片；规则不命中以显式 abstain 返回。"""

    chart = context_to_chart_ledger(context)
    features = build_chart_feature_vector(chart)
    claims = tuple(
        adapt_legacy_claim(
            claim,
            public_school=public_school,
            public_domain=domain_name,
        )
        for task_id in tasks
        for claim in generator(
            chart,
            features,
            _task(task_id, domain_name=domain_name),
        )
    )
    if not claims:
        return SliceResult(
            school=public_school,
            domain=domain_id,
            status="abstain",
            audit=SliceAudit(reason=f"{domain_id} rules did not match"),
        )
    return SliceResult(
        school=public_school,
        domain=domain_id,
        status="implemented",
        claims=claims,
        audit=SliceAudit(reason=f"{domain_id} rules matched"),
    )


def ziping_career_slice(context: DomainAnalysisContext) -> SliceResult:
    return run_legacy_domain_slice(
        context,
        public_school="ziping",
        tasks=("structure.overview", "career.role_change"),
        generator=ziping_runner.generate_claims,
    )


def ditiansui_career_slice(context: DomainAnalysisContext) -> SliceResult:
    return run_legacy_domain_slice(
        context,
        public_school="ditiansui",
        tasks=("structure.overview",),
        generator=ditiansui_runner.generate_claims,
    )


def gao_dechen_career_slice(context: DomainAnalysisContext) -> SliceResult:
    return run_legacy_domain_slice(
        context,
        public_school="gao_dechen",
        tasks=("career.change_window",),
        generator=gao_runner.generate_claims,
    )


def duan_jianye_career_slice(context: DomainAnalysisContext) -> SliceResult:
    return run_legacy_domain_slice(
        context,
        public_school="duan_jianye",
        tasks=("career.role_change", "career.path_type", "career.change_window"),
        generator=duan_runner.generate_claims,
    )


def ren_fuhong_career_slice(context: DomainAnalysisContext) -> SliceResult:
    """任付红只提供可证伪应期，不输出结构或事件合法性命题。"""

    return run_legacy_domain_slice(
        context,
        public_school="ren_fuhong",
        tasks=("career.change_window",),
        generator=ren_runner.generate_claims,
    )


CAREER_GENERATORS = {
    "ziping": ziping_career_slice,
    "ditiansui": ditiansui_career_slice,
    "gao_dechen": gao_dechen_career_slice,
    "duan_jianye": duan_jianye_career_slice,
    "ren_fuhong": ren_fuhong_career_slice,
}


def build_career_registry() -> DomainSliceRegistry:
    """P2 注册表：五个有现成规则的事业切片，杨派事业保持 unsupported。"""

    registrations: list[SliceRegistration] = []
    for school in V5_SCHOOLS:
        for domain in DOMAIN_IDS:
            if domain != "career":
                registrations.append(SliceRegistration(school=school, domain=domain, status="abstain"))
            elif school == "yang_qingjuan":
                registrations.append(SliceRegistration(school=school, domain=domain, status="unsupported"))
            else:
                registrations.append(
                    SliceRegistration(
                        school=school,
                        domain=domain,
                        status="implemented",
                        generator=CAREER_GENERATORS[school],
                    )
                )
    return DomainSliceRegistry(registrations)


# 兼容 P2 期间公开的旧名称；新切片统一使用领域无关名称。
run_legacy_career_slice = run_legacy_domain_slice


__all__ = [
    "CAREER_GENERATORS",
    "adapt_legacy_claim",
    "build_career_registry",
    "context_to_chart_ledger",
    "ditiansui_career_slice",
    "duan_jianye_career_slice",
    "gao_dechen_career_slice",
    "ren_fuhong_career_slice",
    "run_legacy_career_slice",
    "run_legacy_domain_slice",
    "ziping_career_slice",
]
