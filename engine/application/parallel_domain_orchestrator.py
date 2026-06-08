"""多流派功能域调度器与第一版裁判模型。

目标：在既有 D1-D4 串行 pipeline 旁，生成“盲派专家组 / 子平 / 滴天髓”
对各功能域的统一 ExpertReading，并做最小可运行裁判。

本模块只消费公开 findings 与正式生产规则，不让任一专家体系读取其他体系内部中间态。
"""

from __future__ import annotations

import hashlib
from typing import Iterable, Optional

from engine.application.adjudication import adjudicate_domain, build_domain_consensus
from engine.application.production_rule_loader import (
    ProductionRule,
    ProductionRuleLibrary,
    load_default_production_library,
)
from engine.domain.parallel import (
    DomainAnalysis,
    DomainName,
    EvidenceItem,
    ExpertReading,
    ExpertSystem,
    ParallelAnalysisOutput,
    ParallelConfidence,
)
from engine.energy.types import Confidence, EnergyFindings, Evidence
from engine.pangzheng.types import SupportFindings
from engine.picture.types import PictureFindings
from engine.predicates.types import ParsedInput
from engine.yingqi.types import GateResult

DEFAULT_DOMAINS: tuple[DomainName, ...] = ("学业", "事业", "财运", "婚姻", "健康", "性格")
EXPERTS: tuple[ExpertSystem, ...] = ("blind", "ziping", "tiaohou_ditiansui")
EXPERT_LABELS: dict[ExpertSystem, str] = {
    "blind": "盲派专家组",
    "ziping": "子平格局派",
    "tiaohou_ditiansui": "滴天髓调候派",
}
def analyze_parallel_domains(
    *,
    parsed: Optional[ParsedInput],
    energy: EnergyFindings,
    picture: PictureFindings,
    gate_results: list[GateResult],
    support: SupportFindings,
    production_library: Optional[ProductionRuleLibrary] = None,
    domains: Iterable[DomainName] = DEFAULT_DOMAINS,
) -> ParallelAnalysisOutput:
    """生成多专家功能域分析结果。"""

    case_id = energy.case_id or (getattr(parsed, "case_id", "") if parsed else "")
    if production_library is None:
        production_library = load_default_production_library()
    triggered_rules = production_library.triggered_rules(
        parsed=parsed,
        energy=energy,
        picture=picture,
    )
    analyses = [
        analyze_domain(
            domain=domain,
            case_id=case_id,
            energy=energy,
            picture=picture,
            gate_results=gate_results,
            support=support,
            production_rules=triggered_rules,
        )
        for domain in domains
    ]
    return ParallelAnalysisOutput(case_id=case_id, domain_analyses=analyses)


def analyze_domain(
    *,
    domain: DomainName,
    case_id: str,
    energy: EnergyFindings,
    picture: PictureFindings,
    gate_results: list[GateResult],
    support: SupportFindings,
    production_rules: list[ProductionRule],
) -> DomainAnalysis:
    """单功能域多专家分析。"""

    readings: list[ExpertReading] = []
    readings.extend(_blind_readings(domain, case_id, energy, picture, gate_results, support))
    readings.extend(_production_rule_readings(domain, case_id, production_rules))

    existing = {reading.expert_system for reading in readings}
    for expert in EXPERTS:
        if expert not in existing:
            readings.append(_abstain_reading(domain, case_id, expert))

    adjudication = adjudicate_domain(case_id=case_id, domain=domain, readings=readings)
    consensus = build_domain_consensus(
        case_id=case_id,
        domain=domain,
        readings=readings,
        adjudication=adjudication,
    )
    return DomainAnalysis(
        domain=domain,
        readings=readings,
        adjudication_result=adjudication,
        consensus=consensus,
        conflicts=[],
    )


def _blind_readings(
    domain: DomainName,
    case_id: str,
    energy: EnergyFindings,
    picture: PictureFindings,
    gate_results: list[GateResult],
    support: SupportFindings,
) -> list[ExpertReading]:
    readings: list[ExpertReading] = []
    evidence = _evidence_items(energy.evidence[:4])
    if domain in {"财运", "事业", "性格"}:
        readings.append(ExpertReading(
            reading_id=_reading_id(case_id, domain, "blind", "duan"),
            case_id=case_id,
            domain=domain,
            expert_system="blind",
            expert_name="盲派专家组·段派能量",
            sub_school="段",
            stance="support",
            claim=f"做功 {energy.layer_count} 层，富贵层级 {energy.wealth_ceiling}，可作为{domain}底盘。",
            polarity="positive" if energy.layer_count >= 2 else "mixed",
            confidence=_parallel_confidence(energy.confidence, reason="段派能量主判"),
            evidence_items=evidence,
            axis_refs=["blind.energy", "zuogong", "tiyong"],
            source_engine="engine.energy",
            falsifiable=f"若命主实际{domain}表现长期低于该底盘，则段派能量读数需降权。",
        ))

    if domain in {"事业", "财运", "婚姻", "健康", "学业"}:
        claim = _picture_claim(domain, picture)
        if claim:
            readings.append(ExpertReading(
                reading_id=_reading_id(case_id, domain, "blind", "yang"),
                case_id=case_id,
                domain=domain,
                expert_system="blind",
                expert_name="盲派专家组·杨派画面",
                sub_school="杨",
                stance="support",
                claim=claim,
                polarity="positive",
                confidence=_parallel_confidence(picture.confidence or energy.confidence, reason="杨派画面旁证"),
                evidence_items=_evidence_items(picture.evidence[:4]),
                axis_refs=["blind.picture", "yang.wubu"],
                source_engine="engine.picture",
                falsifiable=f"若命主实际{domain}路径与画面指针长期不符，则杨派读数需降权。",
            ))

    domain_gates = [g for g in gate_results if str(g.domain) == domain and g.confidence is not None]
    if domain_gates:
        best_gate = sorted(
            domain_gates,
            key=lambda g: (g.passed_layers, g.confidence.star if g.confidence is not None else 0),
            reverse=True,
        )[0]
        readings.append(ExpertReading(
            reading_id=_reading_id(case_id, domain, "blind", "ren"),
            case_id=case_id,
            domain=domain,
            expert_system="blind",
            expert_name="盲派专家组·任派应期",
            sub_school="任",
            stance="timing_only",
            claim=f"{best_gate.year} 年前后有 {best_gate.candidate_event} 应期线索，三层门通过 {best_gate.passed_layers} 层。",
            polarity="neutral",
            confidence=_parallel_confidence(best_gate.confidence, reason="任派三层应期门"),
            evidence_items=_evidence_items(best_gate.evidence),
            axis_refs=["blind.yingqi", "three_layer_gate"],
            source_engine="engine.yingqi",
            falsifiable=f"若 {best_gate.year} 年前后无对应事件，则任派应期读数失验。",
        ))

    support_boost = support.total_boost_for(domain) if hasattr(support, "total_boost_for") else 0.0
    if support_boost >= 0.03:
        readings.append(ExpertReading(
            reading_id=_reading_id(case_id, domain, "blind", "gao"),
            case_id=case_id,
            domain=domain,
            expert_system="blind",
            expert_name="盲派专家组·高派旁证",
            sub_school="高",
            stance="support",
            claim=f"高派旁证在{domain}域给出 +{support_boost:.2f} 补强。",
            polarity="positive",
            confidence=_parallel_confidence(support.confidence or energy.confidence, reason="高派神煞旁证"),
            evidence_items=_evidence_items(support.evidence[:4]),
            axis_refs=["blind.pangzheng", "shensha_support"],
            source_engine="engine.pangzheng",
            falsifiable=f"若{domain}相关旁证在反馈中持续无效，则高派 boost 需降权。",
        ))
    return readings


def _production_rule_readings(
    domain: DomainName,
    case_id: str,
    rules: list[ProductionRule],
) -> list[ExpertReading]:
    readings: list[ExpertReading] = []
    for rule in rules:
        if domain not in rule.domains:
            continue
        expert_system = rule.expert_system
        readings.append(ExpertReading(
            reading_id=_reading_id(case_id, domain, expert_system, rule.id),
            case_id=case_id,
            domain=domain,
            expert_system=expert_system,
            expert_name=EXPERT_LABELS[expert_system],
            stance="support",
            claim=_production_rule_claim(rule, domain),
            polarity="positive",
            confidence=_parallel_confidence(rule.confidence, reason=f"{rule.display_school}生产规则触发"),
            evidence_items=[EvidenceItem(
                evidence_type="runtime_finding",
                ref=rule.id,
                summary=f"{rule.title}：{rule.claim}",
                strength="high" if rule.confidence.star >= 4 else "medium",
            )],
            axis_refs=list(rule.axis_refs),
            scope_limit=_production_rule_scope(rule),
            falsifiable=rule.output.falsifiable,
            source_engine="engine.application.production_rule_loader",
            notes=_production_rule_notes(rule),
        ))
    return readings


def _production_rule_claim(rule: ProductionRule, domain: DomainName) -> str:
    """把子平 / 滴天髓生产规则展开成接近盲派读数的“过程 + 结论”。"""

    required = "；".join(rule.conditions.required) or "基础触发条件已满足"
    optional = "；".join(rule.conditions.optional) or "无额外可选补强条件"
    exclusions = "；".join(rule.conditions.exclusions) or "无特殊排除项"
    return (
        f"【{rule.display_school}·{rule.title}】领域：{domain}。"
        f"取法过程：先验触发={rule.conditions.trigger}；必看条件={required}；"
        f"可选补强={optional}；排除/保留={exclusions}。"
        f"理论判断：{rule.claim}。落地断语：{rule.output.statement}"
    )


def _production_rule_scope(rule: ProductionRule) -> str:
    domains = "、".join(rule.domains) or "未标注"
    axes = "、".join(rule.axis_refs) or "未标注"
    return f"适用领域={domains}；分析轴={axes}；当前为生产规则触发读数，需与盲派底盘和反馈共同校准。"


def _production_rule_notes(rule: ProductionRule) -> str:
    source = rule.source
    parts = [f"来源：{source.path}；摘录：{source.excerpt}"]
    if rule.review_notes:
        parts.append(f"审校：{rule.review_notes}")
    return "；".join(parts)


def _picture_claim(domain: DomainName, picture: PictureFindings) -> str:
    if domain == "婚姻" and picture.marriage_picture:
        window = picture.marriage_picture.get("初婚最佳窗口")
        stability = picture.marriage_picture.get("婚姻稳定度", "待校准")
        return f"婚姻窗口 {window}，稳定度 {stability}。"
    if domain == "事业" and picture.industry_pointers:
        return f"行业方向偏 {'、'.join(str(x) for x in picture.industry_pointers[:3])}。"
    if domain == "财运" and picture.caifu:
        return f"财富取象 {picture.caifu.type}，等级第 {picture.caifu.rank} 等。"
    if domain == "学业" and picture.guanming:
        return f"官命/考试取法 {picture.guanming.type}，第 {picture.guanming.rank} 取。"
    if domain == "健康" and picture.tiaohou_advice:
        return "调候建议已生成，可作为健康生活方式旁证。"
    return ""


def _abstain_reading(domain: DomainName, case_id: str, expert: ExpertSystem) -> ExpertReading:
    return ExpertReading(
        reading_id=_reading_id(case_id, domain, expert, "abstain"),
        case_id=case_id,
        domain=domain,
        expert_system=expert,
        expert_name=EXPERT_LABELS[expert],
        stance="abstain",
        claim=f"{EXPERT_LABELS[expert]}在{domain}域暂无已接线生产读数。",
        polarity="neutral",
        confidence=ParallelConfidence(raw=0.0, star=0, percent=0, reason="abstain"),
        evidence_items=[],
        axis_refs=[],
        scope_limit="规则未接线或触发条件不足。",
        source_engine="parallel_domain_orchestrator",
    )


def _evidence_items(evidence: Iterable[Evidence]) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    for ev in evidence:
        items.append(EvidenceItem(
            evidence_type="runtime_finding",
            ref=ev.rule_id,
            summary=ev.description,
            strength="high" if ev.weight >= 0.7 else "medium" if ev.weight >= 0.4 else "low",
        ))
    return items


def _parallel_confidence(confidence: Optional[Confidence], *, reason: str) -> ParallelConfidence:
    if confidence is None:
        return ParallelConfidence(raw=0.5, star=2, percent=50, reason=reason)
    percent = int(round(confidence.percent * 100)) if confidence.percent <= 1 else int(round(confidence.percent))
    return ParallelConfidence(
        raw=round(float(confidence.posterior), 4),
        star=int(confidence.star),
        percent=percent,
        reason=reason,
    )


def _reading_id(case_id: str, domain: str, expert: str, suffix: str) -> str:
    return f"RD-{domain}-{_short_hash([case_id, domain, expert, suffix])}"


def _short_hash(parts: Iterable[str]) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]
