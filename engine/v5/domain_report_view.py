"""六源三领域命理师报告的公开 ViewModel。

本模块只从结构化 run snapshot 白名单投影公开字段；Markdown 渲染器不得
直接读取内部身份、规则路径或推理索引。
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

from engine.v5.domain import V5ArbitrationResult, V5Claim, V5RunSnapshot, V5_SCHOOLS
from engine.v5.adjudication import build_v5_adjudication_units
from engine.v5.domain_slices.orchestrator import DOMAIN_NAMES

SCHOOL_NAMES = {
    "ziping": "子平",
    "ditiansui": "滴天髓",
    "gao_dechen": "高德臣",
    "duan_jianye": "段建业",
    "yang_qingjuan": "杨清娟",
    "ren_fuhong": "任付红",
}
STANCE_NAMES = {
    "support": "支持",
    "oppose": "反对",
    "mixed": "保留",
    "abstain": "弃权",
}
CONFLICT_NAMES = {
    "none": "无实质冲突",
    "direction_conflict": "方向冲突",
    "occurrence_opposition": "事件是否发生存在冲突",
    "timing_conflict": "应期存在冲突",
    "structure_event_conflict": "结构与事件判断存在冲突",
}


_INTERNAL_PUBLIC_TEXT_PATTERNS = (
    re.compile(r"\b(?:v5cl|claim|v5ev|evidence|run|statement)-[0-9a-z-]{6,}\b", re.IGNORECASE),
    re.compile(r"\b(?:claim_id|evidence_id|statement_id|statement_index|rule_id)\b", re.IGNORECASE),
    re.compile(r"\bINTERNAL-RULE-[0-9A-Z-]+\b", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])internal[\\/][^\s]+", re.IGNORECASE),
)


def _validate_public_text(text: str, deny_values: set[str]) -> str:
    if any(value and value in text for value in deny_values) or any(pattern.search(text) for pattern in _INTERNAL_PUBLIC_TEXT_PATTERNS):
        raise ValueError("public text contains an internal identifier or path")
    return text


@dataclass(frozen=True)
class ClaimCardView:
    school_name: str
    judgment: str
    evidence_texts: tuple[str, ...]
    stance_name: str
    confidence_text: str
    confidence_note: str
    timing_texts: tuple[str, ...]
    falsifier: str
    status_reason: str
    timing_only: bool
    high_risk: bool
    high_risk_gate_status: str
    high_risk_gate_reason: str


@dataclass(frozen=True)
class DomainView:
    name: str
    conclusion: str
    conclusion_confidence: str
    adjudication_status: str
    adjudication_summary: str
    mapping_status: str
    mapping_summary: str
    conflict_summary: str
    conflict_rationale: str
    cards: tuple[ClaimCardView, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DomainReportView:
    gender_marker: str
    birth_datetime: str
    pillars_text: str
    as_of_date: str
    current_dayun: str
    future_years_text: str
    domains: tuple[DomainView, ...] = field(default_factory=tuple)


def _confidence_text(tier: str, score: float) -> str:
    percent = max(0, min(100, round(score * 100)))
    return f"{tier}（{percent}%）"


def _timing_text(hint: dict[str, Any]) -> str:
    start = hint.get("start_year")
    end = hint.get("end_year")
    label = str(hint.get("label", "")).strip()
    if start is not None and end is not None:
        window = str(start) if start == end else f"{start}—{end}"
        return f"{window}（{label}）" if label else window
    if start is not None:
        return f"{start}（{label}）" if label else str(start)
    return label or "应期证据不足"


def _coverage_reasons(snapshot: V5RunSnapshot) -> dict[tuple[str, str], tuple[str, str]]:
    reasons: dict[tuple[str, str], tuple[str, str]] = {}
    for item in snapshot.metadata.get("slice_coverage", []):
        if not isinstance(item, dict):
            continue
        school = str(item.get("school", ""))
        domain = str(item.get("domain", ""))
        audit = item.get("audit", {})
        reason = str(audit.get("reason", "")) if isinstance(audit, dict) else ""
        reasons[(school, domain)] = (str(item.get("status", "")), reason)
    return reasons


def _public_status_reason(claim: V5Claim, status: str, audit_reason: str) -> str:
    if claim.stance != "abstain":
        return ""
    if status == "unsupported" or claim.metadata.get("slice_status") == "unsupported":
        return "该学派当前没有可执行的本领域切片，暂不支持此项判断。"
    if audit_reason == "slice execution failed":
        return "切片执行未形成可靠结果，已失败关闭为弃权。"
    gate = claim.metadata.get("high_risk_gate")
    if isinstance(gate, dict) and gate.get("status") == "failed":
        return "高风险命题未满足独立安全门禁，已失败关闭为弃权；不形成反对命题。"
    return "当前证据未达到成说门槛，本派克制弃权。"


def _gate_public_fields(claim: V5Claim) -> tuple[str, str]:
    if not bool(claim.metadata.get("high_risk", False)):
        return "", ""
    gate = claim.metadata.get("high_risk_gate")
    if not isinstance(gate, dict):
        return "门禁状态不可用", "需人工复核"
    status = str(gate.get("status", ""))
    reason = str(gate.get("reason", ""))
    status_text = "通过（仍需人工复核）" if status == "passed" else "未通过（已弃权）"
    reason_names = {
        "insufficient_independent_non_timing_sources": "同一任务不足两个独立非应期来源",
        "incomplete_evidence": "证据不完整",
        "missing_falsifier": "缺少明确反证条件",
    }
    return status_text, reason_names.get(reason, "需人工复核")


def _arbitration_for_domain(snapshot: V5RunSnapshot, domain_name: str) -> V5ArbitrationResult | None:
    candidates = [item for item in snapshot.arbitration_results if item.domain == domain_name]
    if not candidates:
        return None
    stage_order = {"structure_legality": 0, "event_realization": 1, "probability_timing": 2}
    return max(candidates, key=lambda item: stage_order.get(item.stage, -1))


def build_domain_report_view(snapshot: V5RunSnapshot) -> DomainReportView:
    """把快照投影为不含任何内部身份字段的命理师公开视图。"""

    deny_values = {snapshot.run_id}
    for claim in snapshot.claims:
        deny_values.add(claim.claim_id)
        for evidence in claim.evidence:
            deny_values.add(evidence.evidence_id)
            deny_values.update(evidence.rule_ids)
            if "/" in evidence.source or "\\" in evidence.source:
                deny_values.add(evidence.source)

    def public(text: object) -> str:
        return _validate_public_text(str(text), deny_values)

    chart = snapshot.canonical_input
    pillars = chart.get("pillars", {})
    requested = [str(item) for item in snapshot.metadata.get("requested_domains", [])]
    reasons = _coverage_reasons(snapshot)
    domain_views: list[DomainView] = []

    for domain in requested:
        domain_name = DOMAIN_NAMES[domain]
        arbitration = _arbitration_for_domain(snapshot, domain_name)
        fallback = str(snapshot.metadata.get("domain_conclusions", {}).get(domain, "证据不足"))
        legacy_conclusion = public(arbitration.conclusion if arbitration and arbitration.conclusion else fallback)
        domain_claims = [claim for claim in snapshot.claims if claim.domain == domain_name]
        claim_ids = {claim.claim_id for claim in domain_claims}
        units = [
            item for item in snapshot.adjudication_units
            if item.domain == domain_name
            and set(item.candidate_claim_ids).issubset(claim_ids)
        ]
        if not units and domain_claims:
            units = [item for item in build_v5_adjudication_units(domain_claims)]
        unresolved_count = sum(item.status == "UNRESOLVED" for item in units)
        coexist_count = sum(item.status == "COEXIST" for item in units)
        primary_count = sum(item.status == "PRIMARY" for item in units)
        mapped_count = sum(item.mapping_status == "MAPPED" for item in units)
        no_mapping_count = sum(item.mapping_status == "NO_MAPPING" for item in units)
        if mapped_count:
            mapping_status = "已映射"
            mapping_summary = "存在已批准的现实指标映射。"
        elif no_mapping_count:
            mapping_status = "NO_MAPPING"
            mapping_summary = "当前没有已批准的现实指标映射，不输出学历、职业、财富或婚姻现实标签。"
        else:
            mapping_status = "未评估"
            mapping_summary = "现实指标映射尚未评估。"
        if unresolved_count:
            adjudication_status = "未决"
            adjudication_summary = "同一目标存在支持与反对命题，当前不形成唯一主断。"
            conclusion = adjudication_summary
        elif primary_count or coexist_count:
            if coexist_count:
                adjudication_status = "同向并存"
                adjudication_summary = "已形成同向主断，但多个命题并存，不合并为单一命题。"
            else:
                adjudication_status = "已形成主断"
                adjudication_summary = "目标级裁决已形成主断。"
            conclusion = f"{adjudication_summary}{legacy_conclusion}"
        else:
            adjudication_status = "弃权"
            adjudication_summary = "当前领域没有形成可输出的目标级主断。"
            conclusion = adjudication_summary
        conclusion = public(conclusion)
        conclusion_confidence = (
            _confidence_text(arbitration.confidence.tier, arbitration.confidence.score)
            if arbitration
            else "★（10%）"
        )
        conflict_type = arbitration.conflict_type if arbitration else "none"
        cards: list[ClaimCardView] = []
        domain_claims.sort(key=lambda claim: (V5_SCHOOLS.index(claim.school), claim.claim))
        for claim in domain_claims:
            status, audit_reason = reasons.get((claim.school, domain), (str(claim.metadata.get("slice_status", "")), ""))
            gate_status, gate_reason = _gate_public_fields(claim)
            cards.append(
                ClaimCardView(
                    school_name=SCHOOL_NAMES[claim.school],
                    judgment=public(claim.claim),
                    evidence_texts=tuple(public(item.text) for item in claim.evidence) or ("未形成可公开证据文本。",),
                    stance_name=STANCE_NAMES[claim.stance],
                    confidence_text=_confidence_text(claim.confidence.tier, claim.confidence.score),
                    confidence_note=public(claim.confidence.note),
                    timing_texts=tuple(public(_timing_text(item)) for item in claim.timing_hints) or ("应期证据不足",),
                    falsifier=public(claim.falsifiable or "尚无明确反证条件，使用前需人工补充。"),
                    status_reason=_public_status_reason(claim, status, audit_reason),
                    timing_only=claim.school == "ren_fuhong" or claim.claim_type == "timing_claim",
                    high_risk=bool(claim.metadata.get("high_risk", False)),
                    high_risk_gate_status=gate_status,
                    high_risk_gate_reason=gate_reason,
                )
            )
        domain_views.append(
            DomainView(
                name=domain_name,
                conclusion=conclusion,
                conclusion_confidence=conclusion_confidence,
                adjudication_status=adjudication_status,
                adjudication_summary=public(adjudication_summary),
                mapping_status=mapping_status,
                mapping_summary=public(mapping_summary),
                conflict_summary=CONFLICT_NAMES.get(conflict_type, "存在需人工判读的命题冲突"),
                conflict_rationale=public(arbitration.rationale if arbitration else "当前无可执行冲突命题。"),
                cards=tuple(cards),
            )
        )

    future_years = chart.get("future_years", [])
    return DomainReportView(
        gender_marker=str(chart.get("gender_marker", "乾/坤")),
        birth_datetime=str(chart.get("birth_datetime", "待补充")),
        pillars_text="｜".join(str(pillars.get(key, "")) for key in ("year", "month", "day", "hour")),
        as_of_date=str(chart.get("as_of_date", "待补充")),
        current_dayun=str(chart.get("current_dayun", "待补充")),
        future_years_text="、".join(f"{item['year']} {item['ganzhi']}" for item in future_years),
        domains=tuple(domain_views),
    )
