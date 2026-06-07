"""多流派功能域调度器与第一版裁判模型。

目标：在既有 D1-D4 串行 pipeline 旁，生成“盲派专家组 / 子平 / 滴天髓”
对各功能域的统一 ExpertReading，并做最小可运行裁判。

本模块只消费公开 findings 与正式生产规则，不让任一专家体系读取其他体系内部中间态。
"""

from __future__ import annotations

import hashlib
from typing import Iterable, Optional

from engine.application.production_rule_loader import (
    ProductionRule,
    ProductionRuleLibrary,
    load_default_production_library,
)
from engine.domain.parallel import (
    AdjudicationResult,
    ArbitrationReason,
    DomainAnalysis,
    DomainName,
    EvidenceItem,
    ExpertJudgement,
    ExpertReading,
    ExpertSystem,
    ParallelAnalysisOutput,
    ParallelConfidence,
    WeightProfile,
    DomainConsensus,
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
DOMAIN_WEIGHTS: dict[DomainName, dict[ExpertSystem, float]] = {
    "学业": {"blind": 0.42, "ziping": 0.34, "tiaohou_ditiansui": 0.24},
    "事业": {"blind": 0.42, "ziping": 0.36, "tiaohou_ditiansui": 0.22},
    "财运": {"blind": 0.44, "ziping": 0.34, "tiaohou_ditiansui": 0.22},
    "婚姻": {"blind": 0.50, "ziping": 0.28, "tiaohou_ditiansui": 0.22},
    "健康": {"blind": 0.34, "ziping": 0.22, "tiaohou_ditiansui": 0.44},
    "性格": {"blind": 0.42, "ziping": 0.30, "tiaohou_ditiansui": 0.28},
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

    adjudication = _adjudicate(domain, readings)
    consensus = _to_consensus(domain, adjudication, readings)
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

    domain_gates = [g for g in gate_results if str(g.domain) == domain and g.confidence]
    if domain_gates:
        best_gate = sorted(domain_gates, key=lambda g: (g.passed_layers, g.confidence.star), reverse=True)[0]
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


def _adjudicate(domain: DomainName, readings: list[ExpertReading]) -> AdjudicationResult:
    weights = DOMAIN_WEIGHTS[domain]
    profile = WeightProfile(
        profile_id=f"parallel-domain-{domain}",
        profile_version="2026-06-06-minimal-v1",
        source="engine.application.parallel_domain_orchestrator.DOMAIN_WEIGHTS",
        domain_weights=weights,
    )
    judgements: list[ExpertJudgement] = []
    support_score = 0.0
    oppose_score = 0.0
    for idx, reading in enumerate(readings, start=1):
        ballot = _ballot_from_stance(reading.stance)
        prior = weights.get(reading.expert_system, 0.0)
        confidence_weight = max(0.0, min(1.0, reading.confidence.raw))
        evidence_quality = _evidence_quality(reading)
        feedback_weight = 1.0
        conflict_penalty = 0.0
        raw_score = prior * confidence_weight
        adjusted = raw_score * evidence_quality * feedback_weight - conflict_penalty
        if ballot == "yes":
            support_score += adjusted
        elif ballot == "no":
            oppose_score += adjusted
        elif ballot == "mixed":
            support_score += adjusted * 0.5
            oppose_score += adjusted * 0.5
        judgements.append(ExpertJudgement(
            judgement_id=f"J-{domain}-{idx:02d}",
            reading_id=reading.reading_id,
            expert_system=reading.expert_system,
            domain=domain,
            claim=reading.claim,
            ballot=ballot,
            raw_score=round(raw_score, 4),
            prior_domain_weight=round(prior, 4),
            confidence_weight=round(confidence_weight, 4),
            feedback_weight=feedback_weight,
            evidence_quality_weight=round(evidence_quality, 4),
            conflict_penalty=conflict_penalty,
            adjusted_score=round(adjusted, 4),
            rationale=f"{EXPERT_LABELS[reading.expert_system]}：领域权重×置信度×证据质量。",
        ))

    active_support = [r.expert_system for r in readings if r.stance in {"support", "timing_only"}]
    active_oppose = [r.expert_system for r in readings if r.stance == "oppose"]
    abstained = [r.expert_system for r in readings if r.stance == "abstain"]
    if support_score == 0 and oppose_score == 0:
        decision = "no_output"
    elif support_score >= oppose_score:
        decision = "yes" if oppose_score == 0 else "mixed"
    else:
        decision = "no"
    merged = max(support_score, oppose_score)
    confidence = ParallelConfidence(
        raw=round(merged, 4),
        merged=round(merged, 4),
        star=_star_from_score(merged),
        percent=round(min(0.95, merged) * 100),
        reason="按领域权重、单派置信度与证据质量合并。",
    )
    return AdjudicationResult(
        adjudication_id=f"ADJ-{domain}-{_short_hash([r.reading_id for r in readings])}",
        domain=domain,
        claim=_primary_claim(readings),
        decision=decision,
        judgements=judgements,
        support_score=round(support_score, 4),
        oppose_score=round(oppose_score, 4),
        confidence=confidence,
        weight_profile=profile,
        winning_experts=sorted(set(active_support)) if decision in {"yes", "mixed"} else sorted(set(active_oppose)),
        dissenting_experts=sorted(set(active_oppose if decision in {"yes", "mixed"} else active_support)),
        abstained_experts=sorted(set(abstained)),
        arbitration_reason=ArbitrationReason(
            winner_reason="第一版裁判按领域先验权重、置信度与证据质量加权。",
            loser_reason="未胜出读数保留在 readings，用于后续反馈校准。",
            conflict_type="none" if not active_oppose else "evidence",
            output_strategy="primary_with_minority" if active_oppose else "primary_only",
        ),
    )


def _to_consensus(domain: DomainName, adjudication: AdjudicationResult, readings: list[ExpertReading]) -> DomainConsensus:
    selected = [r for r in readings if r.expert_system in adjudication.winning_experts and r.stance != "abstain"]
    evidence_items: list[EvidenceItem] = []
    for reading in selected:
        evidence_items.extend(reading.evidence_items)
    contributing = sorted(set(r.expert_system for r in selected))
    if adjudication.decision == "no_output":
        layer = "不输出"
        statement = f"{domain}域暂无足够多专家证据输出。"
    elif len(contributing) >= 3:
        layer = "多专家共识"
        statement = f"{domain}域多专家读数同向：{adjudication.claim}"
    elif len(contributing) == 2:
        layer = "双专家共识"
        statement = f"{domain}域双专家读数同向：{adjudication.claim}"
    elif contributing:
        layer = "主专家胜出"
        statement = f"{domain}域以{EXPERT_LABELS[contributing[0]]}为主：{adjudication.claim}"
    else:
        layer = "冲突保留"
        statement = f"{domain}域存在冲突或低置信读数，暂作保留。"
    return DomainConsensus(
        conclusion_id=f"PDC-{domain}-{_short_hash([adjudication.adjudication_id])}",
        domain=domain,
        headline=f"{domain}域裁判：{layer}",
        final_statement=statement,
        layer=layer,
        contributing_experts=contributing,
        dissenting_experts=list(adjudication.dissenting_experts),
        confidence=adjudication.confidence,
        evidence_items=evidence_items[:8],
        falsifiable=f"若命主反馈显示{domain}域主结论长期不符，则本域裁判失验并回写权重。",
        weight_profile=adjudication.weight_profile,
        arbitration_reason=adjudication.arbitration_reason,
        output_strategy=adjudication.arbitration_reason.output_strategy if adjudication.arbitration_reason else "primary_only",
    )


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


def _ballot_from_stance(stance: str) -> str:
    if stance in {"support", "timing_only"}:
        return "yes"
    if stance == "oppose":
        return "no"
    if stance == "mixed":
        return "mixed"
    return "abstain"


def _evidence_quality(reading: ExpertReading) -> float:
    if reading.stance == "abstain":
        return 0.0
    if not reading.evidence_items:
        return 0.6
    high = sum(1 for item in reading.evidence_items if item.strength == "high")
    medium = sum(1 for item in reading.evidence_items if item.strength == "medium")
    return min(1.0, 0.65 + high * 0.15 + medium * 0.08)


def _primary_claim(readings: list[ExpertReading]) -> str:
    active = [r for r in readings if r.stance != "abstain"]
    if not active:
        return "暂无足够读数"
    active.sort(key=lambda r: (r.confidence.raw, len(r.evidence_items)), reverse=True)
    return active[0].claim


def _star_from_score(score: float) -> int:
    if score >= 0.80:
        return 5
    if score >= 0.60:
        return 4
    if score >= 0.40:
        return 3
    if score >= 0.20:
        return 2
    return 1


def _reading_id(case_id: str, domain: str, expert: str, suffix: str) -> str:
    return f"RD-{domain}-{_short_hash([case_id, domain, expert, suffix])}"


def _short_hash(parts: Iterable[str]) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]
