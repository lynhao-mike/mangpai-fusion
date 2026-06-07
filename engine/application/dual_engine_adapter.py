"""双引擎 findings 适配服务。

该服务复用现有 D1-D4 findings、子平/滴天髓生产规则与多专家功能域裁判，
生成 TheoryFindings、BlindFindings、FusionFindings 三层聚合输出。
"""
from __future__ import annotations

from typing import Optional

from engine.application.parallel_domain_orchestrator import analyze_parallel_domains
from engine.application.production_rule_loader import (
    ProductionRule,
    ProductionRuleLibrary,
    load_default_production_library,
)
from engine.domain.dual_engine import BlindFindings, FusionFindings, TheoryFindings
from engine.domain.parallel import ParallelAnalysisOutput
from engine.energy.types import EnergyFindings, Evidence
from engine.pangzheng.types import SupportFindings
from engine.picture.types import PictureFindings
from engine.predicates.strength import calc_gan_strength, calc_wuxing_strength
from engine.predicates.types import ParsedInput
from engine.yingqi.types import GateResult


def build_theory_findings(
    *,
    parsed: ParsedInput,
    energy: EnergyFindings,
    picture: PictureFindings,
    production_library: Optional[ProductionRuleLibrary] = None,
) -> TheoryFindings:
    """生成理论派聚合输出。"""

    if production_library is None:
        production_library = load_default_production_library()
    triggered_rules = production_library.triggered_rules(
        parsed=parsed,
        energy=energy,
        picture=picture,
    )
    strength_profile = calc_wuxing_strength(parsed.bazi)
    day_master_strength = calc_gan_strength(parsed.bazi.day_master, parsed.bazi)
    main_yongshen = [item.char for item in energy.tiyong.purpose]
    assistant_yongshen = [item.char for item in energy.tiyong.body]

    return TheoryFindings(
        case_id=energy.case_id or parsed.case_id,
        triggered_rules=[_rule_summary(rule) for rule in triggered_rules],
        rule_count_by_system=_count_rules_by_system(triggered_rules),
        strength_profile={k: round(v, 4) for k, v in strength_profile.items()},
        day_master_strength=round(day_master_strength, 4),
        main_yongshen=main_yongshen,
        assistant_yongshen=assistant_yongshen,
        evidence_rule_ids=[rule.id for rule in triggered_rules],
        confidence_summary=_confidence_summary([rule.confidence for rule in triggered_rules]),
    )


def build_blind_findings(
    *,
    energy: EnergyFindings,
    picture: PictureFindings,
    gate_results: list[GateResult],
    support: SupportFindings,
) -> BlindFindings:
    """生成盲派 D1-D4 聚合输出。"""

    return BlindFindings(
        case_id=energy.case_id or picture.case_id or support.case_id,
        energy_summary={
            "school": energy.school,
            "energy_level": energy.energy_level.to_dict(),
            "layer_count": energy.layer_count,
            "wealth_ceiling": energy.wealth_ceiling,
            "zuogong_path_count": len(energy.zuogong_paths),
            "has_guoheqiaoqiao": energy.has_guoheqiaoqiao,
            "muxing_qufa": energy.muxing_qufa,
        },
        picture_summary={
            "school": picture.school,
            "wubu_step_count": len(picture.wubu_steps),
            "wuhe_count": len(picture.wuhe_relations),
            "anyin_count": len(picture.anyin_results),
            "has_caifu": picture.caifu is not None,
            "has_guanming": picture.guanming is not None,
            "industry_path": dict(picture.industry_path),
            "wealth_level": dict(picture.wealth_level),
        },
        timing_summary={
            "school": "任",
            "gate_count": len(gate_results),
            "passed_gate_count": sum(1 for gate in gate_results if gate.passed_layers >= 1),
            "domains": sorted({gate.domain for gate in gate_results}),
            "years": [gate.year for gate in gate_results],
        },
        support_summary={
            "school": support.school,
            "support_domains": sorted(support.shensha_supports.keys()),
            "shensha_count": len(support.all_shensha_names()),
            "health_count": len(support.health_findings),
            "has_ciguan_xuetang": support.ciguan_xuetang is not None,
        },
        evidence_rule_ids=_evidence_rule_ids(
            energy.evidence
            + picture.evidence
            + [e for gate in gate_results for e in gate.evidence]
            + support.evidence
        ),
        upstream_hashes={
            "energy": energy.hash(),
            "picture": picture.hash(),
            "support": support.hash(),
        },
    )


def build_fusion_findings(
    *,
    theory: TheoryFindings,
    blind: BlindFindings,
    parallel_analysis: ParallelAnalysisOutput,
) -> FusionFindings:
    """生成理论派与盲派融合输出。"""

    conclusions = [
        {
            "domain": analysis.domain,
            "conclusion_id": analysis.consensus.conclusion_id,
            "headline": analysis.consensus.headline,
            "final_statement": analysis.consensus.final_statement,
            "layer": analysis.consensus.layer,
            "contributing_experts": list(analysis.consensus.contributing_experts),
            "dissenting_experts": list(analysis.consensus.dissenting_experts),
            "confidence": analysis.consensus.confidence.to_dict(),
        }
        for analysis in parallel_analysis.domain_analyses
    ]
    return FusionFindings(
        case_id=parallel_analysis.case_id,
        conclusions=conclusions,
        theory_support=list(theory.evidence_rule_ids),
        blind_support=list(blind.evidence_rule_ids),
        confidence_summary=_fusion_confidence_summary(conclusions),
        parallel_analysis=parallel_analysis,
    )


def analyze_dual_engine(
    *,
    parsed: ParsedInput,
    energy: EnergyFindings,
    picture: PictureFindings,
    gate_results: list[GateResult],
    support: SupportFindings,
    production_library: Optional[ProductionRuleLibrary] = None,
    parallel_analysis: Optional[ParallelAnalysisOutput] = None,
) -> tuple[TheoryFindings, BlindFindings, FusionFindings]:
    """一次性生成双引擎三层 findings。"""

    if production_library is None:
        production_library = load_default_production_library()
    theory = build_theory_findings(
        parsed=parsed,
        energy=energy,
        picture=picture,
        production_library=production_library,
    )
    blind = build_blind_findings(
        energy=energy,
        picture=picture,
        gate_results=gate_results,
        support=support,
    )
    if parallel_analysis is None:
        parallel_analysis = analyze_parallel_domains(
            parsed=parsed,
            energy=energy,
            picture=picture,
            gate_results=gate_results,
            support=support,
            production_library=production_library,
        )
    fusion = build_fusion_findings(
        theory=theory,
        blind=blind,
        parallel_analysis=parallel_analysis,
    )
    return theory, blind, fusion


def _rule_summary(rule: ProductionRule) -> dict[str, object]:
    return {
        "id": rule.id,
        "expert_system": rule.expert_system,
        "display_school": rule.display_school,
        "title": rule.title,
        "topic": rule.topic,
        "domains": list(rule.domains),
        "axis_refs": list(rule.axis_refs),
        "claim": rule.claim,
        "trigger": rule.conditions.trigger,
        "confidence": rule.confidence.to_dict(),
        "layer": rule.layer,
    }


def _count_rules_by_system(rules: list[ProductionRule]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for rule in rules:
        counts[rule.expert_system] = counts.get(rule.expert_system, 0) + 1
    return counts


def _confidence_summary(confidences: list[object]) -> dict[str, object]:
    if not confidences:
        return {"count": 0, "avg_percent": 0.0, "max_star": 0}
    percents = [float(getattr(confidence, "percent", 0.0)) for confidence in confidences]
    stars = [int(getattr(confidence, "star", 0)) for confidence in confidences]
    return {
        "count": len(confidences),
        "avg_percent": round(sum(percents) / len(percents), 4),
        "max_star": max(stars),
    }


def _fusion_confidence_summary(conclusions: list[dict[str, object]]) -> dict[str, object]:
    if not conclusions:
        return {"domain_count": 0, "avg_percent": 0.0, "max_star": 0}
    confidences = [item.get("confidence", {}) for item in conclusions]
    percents = [float(conf.get("percent", 0)) / 100.0 for conf in confidences if isinstance(conf, dict)]
    stars = [int(conf.get("star", 0)) for conf in confidences if isinstance(conf, dict)]
    return {
        "domain_count": len(conclusions),
        "avg_percent": round(sum(percents) / len(percents), 4) if percents else 0.0,
        "max_star": max(stars) if stars else 0,
    }


def _evidence_rule_ids(evidence_items: list[Evidence]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for evidence in evidence_items:
        if evidence.rule_id and evidence.rule_id not in seen:
            seen.add(evidence.rule_id)
            ordered.append(evidence.rule_id)
    return ordered
