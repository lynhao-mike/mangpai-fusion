"""多专家功能域 analyzer 协议与注册表。

该模块是并行功能域分析的唯一专家接线机制。各派内部可以有完全不同的
实现，但暴露给 runner / 裁判层的结果必须是 ExpertReading。
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional, Protocol

from engine.application.production_rule_loader import ProductionRule
from engine.domain.parallel_constants import CANONICAL_DOMAINS, CANONICAL_EXPERT_ORDER, EXPERT_LABELS
from engine.domain.parallel import (
    DomainName,
    EvidenceItem,
    ExpertReading,
    ExpertSystem,
    ParallelConfidence,
)
from engine.energy.types import Confidence, Evidence


@dataclass(frozen=True)
class DomainAnalysisContext:
    """功能域分析器的最小上下文。"""

    case_id: str
    base_context: dict[str, Any] = field(default_factory=dict)


class DomainAnalyzer(Protocol):
    """专家体系 × 功能域分析器协议。"""

    expert_system: ExpertSystem
    expert_name: str

    def analyze(self, parsed: Any, domain: DomainName, context: DomainAnalysisContext) -> ExpertReading:
        """返回该专家体系对指定功能域的独立 ExpertReading。"""
        ...

    def is_wired(self) -> bool:
        """是否已接入真实规则或执行器。"""
        ...


class AbstainDomainAnalyzer:
    """未接线专家体系的显式弃权 analyzer。"""

    def __init__(
        self,
        *,
        expert_system: ExpertSystem,
        expert_name: str,
        reason: str = "理论库或执行器尚未接入，按旁路原则显式弃权。",
        source_engine: str = "abstain_adapter",
    ) -> None:
        self.expert_system: ExpertSystem = expert_system
        self.expert_name = expert_name
        self.reason = reason
        self.source_engine = source_engine

    def analyze(self, parsed: Any, domain: DomainName, context: DomainAnalysisContext) -> ExpertReading:
        return ExpertReading(
            reading_id=f"RD-{context.case_id}-{domain}-{self.expert_system}-ABSTAIN",
            case_id=context.case_id,
            domain=domain,
            expert_system=self.expert_system,
            expert_name=self.expert_name,
            stance="abstain",
            claim=self.reason,
            polarity="neutral",
            confidence=ParallelConfidence(
                raw=0.0,
                merged=None,
                feedback_adjusted=None,
                star=1,
                percent=0,
                reason="显式弃权不参与加权胜出。",
            ),
            evidence_items=[],
            axis_refs=[],
            scope_limit="未接入执行器，不能输出正式结论。",
            falsifiable="后续接线并回测后再建立可证伪断语。",
            source_engine=self.source_engine,
            isolation_boundary="external_protocol_only",
            notes=self.reason,
        )

    def is_wired(self) -> bool:
        return False


class StaticReadingAnalyzer:
    """测试与旁路演练用的静态 reading analyzer。"""

    def __init__(self, reading: ExpertReading) -> None:
        self.reading = reading
        self.expert_system = reading.expert_system
        self.expert_name = reading.expert_name

    def analyze(self, parsed: Any, domain: DomainName, context: DomainAnalysisContext) -> ExpertReading:
        if self.reading.domain != domain:
            raise ValueError(f"静态 reading domain 不匹配：{self.reading.domain} != {domain}")
        if self.reading.case_id != context.case_id:
            data = self.reading.to_dict()
            data["case_id"] = context.case_id
            data["reading_id"] = f"RD-{context.case_id}-{domain}-{self.reading.expert_system}"
            return ExpertReading.from_dict(data)
        return self.reading

    def is_wired(self) -> bool:
        return True


class PipelineBlindAnalyzer:
    """把 pipeline 已有盲派 findings 包装为 registry analyzer。"""

    expert_system: ExpertSystem = "blind"
    expert_name = "盲派综合组"

    def analyze(self, parsed: Any, domain: DomainName, context: DomainAnalysisContext) -> ExpertReading:
        energy = context.base_context.get("energy")
        picture = context.base_context.get("picture")
        gate_results = list(context.base_context.get("gate_results") or [])
        support = context.base_context.get("support")
        claims: list[str] = []
        evidence_items: list[EvidenceItem] = []
        axis_refs: list[str] = []
        confidences: list[Confidence] = []
        source_engines: list[str] = []

        if energy is not None and domain in {"财运", "事业", "性格"}:
            claims.append(f"段派能量：做功 {energy.layer_count} 层，富贵层级 {energy.wealth_ceiling}，可作为{domain}底盘。")
            evidence_items.extend(_evidence_items(getattr(energy, "evidence", [])[:4]))
            axis_refs.extend(["blind.energy", "zuogong", "tiyong"])
            if getattr(energy, "confidence", None) is not None:
                confidences.append(energy.confidence)
            source_engines.append("engine.energy")

        if picture is not None and domain in {"事业", "财运", "婚姻", "健康", "学业"}:
            claim = _picture_claim(domain, picture)
            if claim:
                claims.append(f"杨派画面：{claim}")
                evidence_items.extend(_evidence_items(getattr(picture, "evidence", [])[:4]))
                axis_refs.extend(["blind.picture", "yang.wubu"])
                confidence = getattr(picture, "confidence", None) or getattr(energy, "confidence", None)
                if confidence is not None:
                    confidences.append(confidence)
                source_engines.append("engine.picture")

        domain_gates = [g for g in gate_results if str(getattr(g, "domain", "")) == domain and getattr(g, "confidence", None) is not None]
        if domain_gates:
            best_gate = sorted(
                domain_gates,
                key=lambda g: (g.passed_layers, g.confidence.star if g.confidence is not None else 0),
                reverse=True,
            )[0]
            claims.append(f"任派应期：{best_gate.year} 年前后有 {best_gate.candidate_event} 应期线索，三层门通过 {best_gate.passed_layers} 层。")
            evidence_items.extend(_evidence_items(getattr(best_gate, "evidence", [])))
            axis_refs.extend(["blind.yingqi", "three_layer_gate"])
            confidences.append(best_gate.confidence)
            source_engines.append("engine.yingqi")

        if support is not None:
            support_boost = support.total_boost_for(domain) if hasattr(support, "total_boost_for") else 0.0
            if support_boost >= 0.03:
                claims.append(f"高派旁证：在{domain}域给出 +{support_boost:.2f} 补强。")
                evidence_items.extend(_evidence_items(getattr(support, "evidence", [])[:4]))
                axis_refs.extend(["blind.pangzheng", "shensha_support"])
                confidence = getattr(support, "confidence", None) or getattr(energy, "confidence", None)
                if confidence is not None:
                    confidences.append(confidence)
                source_engines.append("engine.pangzheng")

        if not claims:
            return AbstainDomainAnalyzer(
                expert_system=self.expert_system,
                expert_name=self.expert_name,
                reason=f"{self.expert_name}在{domain}域暂无已触发 pipeline 读数。",
            ).analyze(parsed, domain, context)

        return ExpertReading(
            reading_id=_reading_id(context.case_id, domain, self.expert_system, "pipeline_blind"),
            case_id=context.case_id,
            domain=domain,
            expert_system=self.expert_system,
            expert_name=self.expert_name,
            stance="support",
            claim="；".join(claims),
            polarity="positive",
            confidence=_best_parallel_confidence(confidences, reason="盲派 pipeline findings 聚合"),
            evidence_items=evidence_items,
            axis_refs=_dedupe(axis_refs),
            scope_limit="由 pipeline 公开 findings 聚合，不读取其他专家内部中间态。",
            falsifiable=f"若命主实际{domain}表现长期低于该底盘，则盲派聚合读数需降权。",
            source_engine="+".join(_dedupe(source_engines)) or "pipeline_findings",
        )

    def is_wired(self) -> bool:
        return True


class PipelineProductionRuleAnalyzer:
    """把子平 / 滴天髓生产规则触发结果包装为 registry analyzer。"""

    def __init__(self, expert_system: ExpertSystem) -> None:
        self.expert_system: ExpertSystem = expert_system
        self.expert_name = EXPERT_LABELS[expert_system]

    def analyze(self, parsed: Any, domain: DomainName, context: DomainAnalysisContext) -> ExpertReading:
        rules = [
            rule
            for rule in list(context.base_context.get("production_rules") or [])
            if rule.expert_system == self.expert_system and domain in rule.domains
        ]
        if not rules:
            return AbstainDomainAnalyzer(
                expert_system=self.expert_system,
                expert_name=self.expert_name,
                reason=f"{self.expert_name}在{domain}域暂无触发生产规则。",
            ).analyze(parsed, domain, context)

        claims = [_production_rule_claim(rule, domain) for rule in rules]
        evidence_items = [
            EvidenceItem(
                evidence_type="runtime_finding",
                ref=rule.id,
                summary=f"{rule.title}：{rule.claim}",
                strength="high" if rule.confidence.star >= 4 else "medium",
            )
            for rule in rules
        ]
        axis_refs: list[str] = []
        for rule in rules:
            axis_refs.extend(rule.axis_refs)

        return ExpertReading(
            reading_id=_reading_id(context.case_id, domain, self.expert_system, "production_rules"),
            case_id=context.case_id,
            domain=domain,
            expert_system=self.expert_system,
            expert_name=self.expert_name,
            stance="support",
            claim="；".join(claims),
            polarity="positive",
            confidence=_best_parallel_confidence([rule.confidence for rule in rules], reason=f"{self.expert_name}生产规则聚合触发"),
            evidence_items=evidence_items,
            axis_refs=_dedupe(axis_refs),
            scope_limit="；".join(_production_rule_scope(rule) for rule in rules),
            falsifiable="；".join(rule.output.falsifiable for rule in rules if rule.output.falsifiable),
            source_engine="engine.application.production_rule_loader",
            notes="；".join(_production_rule_notes(rule) for rule in rules),
        )

    def is_wired(self) -> bool:
        return True


class DomainAnalyzerRegistry:
    """专家体系 × 功能域注册表，避免 runner 使用大量 if/else。"""

    def __init__(self) -> None:
        self._items: dict[tuple[DomainName, ExpertSystem], DomainAnalyzer] = {}

    def register(self, domain: DomainName, expert_system: ExpertSystem, analyzer: DomainAnalyzer) -> None:
        self._items[(domain, expert_system)] = analyzer

    def get(self, domain: DomainName, expert_system: ExpertSystem) -> DomainAnalyzer:
        analyzer = self._items.get((domain, expert_system))
        if analyzer is not None:
            return analyzer
        return AbstainDomainAnalyzer(
            expert_system=expert_system,
            expert_name=EXPERT_LABELS[expert_system],
        )

    def registered_experts(self, domain: DomainName) -> list[ExpertSystem]:
        return [expert for (registered_domain, expert), _ in self._items.items() if registered_domain == domain]

    def get_wiring_status(
        self,
        *,
        domains: tuple[DomainName, ...] | None = None,
        experts: tuple[ExpertSystem, ...] | None = None,
    ) -> dict[str, dict[str, str]]:
        """返回各功能域 × 专家体系的接线状态。"""

        selected_domains = domains or DEFAULT_DOMAINS
        selected_experts = experts or DEFAULT_EXPERT_ORDER
        status: dict[str, dict[str, str]] = {}
        for domain in selected_domains:
            status[domain] = {}
            for expert in selected_experts:
                analyzer = self.get(domain, expert)
                is_wired = getattr(analyzer, "is_wired", lambda: True)()
                status[domain][expert] = "wired" if is_wired else "abstain_only"
        return status


DEFAULT_EXPERT_ORDER: tuple[ExpertSystem, ...] = CANONICAL_EXPERT_ORDER
DEFAULT_DOMAINS: tuple[DomainName, ...] = CANONICAL_DOMAINS


def build_empty_parallel_registry() -> DomainAnalyzerRegistry:
    """构造全部专家默认弃权的旁路注册表。"""

    return DomainAnalyzerRegistry()


def build_pipeline_findings_registry(domains: Iterable[DomainName] | None = None) -> DomainAnalyzerRegistry:
    """为 pipeline 公开 findings 构造标准 registry analyzer 接线。"""

    registry = DomainAnalyzerRegistry()
    for domain in domains or DEFAULT_DOMAINS:
        registry.register(domain, "blind", PipelineBlindAnalyzer())
        registry.register(domain, "ziping", PipelineProductionRuleAnalyzer("ziping"))
        registry.register(domain, "tiaohou_ditiansui", PipelineProductionRuleAnalyzer("tiaohou_ditiansui"))
    return registry


def get_wiring_status(registry: DomainAnalyzerRegistry | None = None) -> dict[str, dict[str, str]]:
    """返回默认功能域 × 专家体系的接线状态。"""

    return (registry or build_empty_parallel_registry()).get_wiring_status()


def _picture_claim(domain: DomainName, picture: Any) -> str:
    if domain == "婚姻" and getattr(picture, "marriage_picture", None):
        window = picture.marriage_picture.get("初婚最佳窗口")
        stability = picture.marriage_picture.get("婚姻稳定度", "待校准")
        return f"婚姻窗口 {window}，稳定度 {stability}。"
    if domain == "事业" and getattr(picture, "industry_pointers", None):
        return f"行业方向偏 {'、'.join(str(x) for x in picture.industry_pointers[:3])}。"
    if domain == "财运" and getattr(picture, "caifu", None):
        return f"财富取象 {picture.caifu.type}，等级第 {picture.caifu.rank} 等。"
    if domain == "学业" and getattr(picture, "guanming", None):
        return f"官命/考试取法 {picture.guanming.type}，第 {picture.guanming.rank} 取。"
    if domain == "健康" and getattr(picture, "tiaohou_advice", None):
        return "调候建议已生成，可作为健康生活方式旁证。"
    return ""


def _production_rule_claim(rule: ProductionRule, domain: DomainName) -> str:
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


def _evidence_items(evidence: Iterable[Evidence]) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    for ev in evidence:
        items.append(
            EvidenceItem(
                evidence_type="runtime_finding",
                ref=ev.rule_id,
                summary=ev.description,
                strength="high" if ev.weight >= 0.7 else "medium" if ev.weight >= 0.4 else "low",
            )
        )
    return items


def _best_parallel_confidence(confidences: Iterable[Optional[Confidence]], *, reason: str) -> ParallelConfidence:
    available = [confidence for confidence in confidences if confidence is not None]
    if not available:
        return ParallelConfidence(raw=0.5, star=2, percent=50, reason=reason)
    best = sorted(available, key=lambda c: (c.star, c.posterior), reverse=True)[0]
    percent = int(round(best.percent * 100)) if best.percent <= 1 else int(round(best.percent))
    return ParallelConfidence(
        raw=round(float(best.posterior), 4),
        star=int(best.star),
        percent=percent,
        reason=reason,
    )


def _reading_id(case_id: str, domain: str, expert: str, suffix: str) -> str:
    return f"RD-{domain}-{_short_hash([case_id, domain, expert, suffix])}"


def _short_hash(parts: Iterable[str]) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]


def _dedupe(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(str(value) for value in values if value))
