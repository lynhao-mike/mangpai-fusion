"""Evidence-first detail expansion policy for first-pass Bazi reports.

This module separates structural evidence sufficiency from feedback-derived
confidence so initial reports can stay detailed without inflating confidence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


DETAIL_DOMAINS: tuple[str, ...] = ("education", "career", "wealth", "marriage", "health")
DOMAIN_LABELS: dict[str, str] = {
    "education": "学业",
    "career": "事业",
    "wealth": "财富",
    "marriage": "婚姻",
    "health": "健康",
}


@dataclass(frozen=True)
class ScoreBreakdown:
    """A normalized score with transparent component values."""

    value: float
    components: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": round(self.value, 4),
            "components": {k: round(v, 4) for k, v in self.components.items()},
        }


@dataclass(frozen=True)
class DetailExpansion:
    """Report-facing expansion decision for one domain."""

    domain: str
    label: str
    level: int
    level_label: str
    evidence_score: ScoreBreakdown
    confidence_score: ScoreBreakdown
    allow_theory_detail: bool
    inference_type: str
    theory_sources: list[str]
    uncertainty: str
    detail_items: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "label": self.label,
            "level": self.level,
            "level_label": self.level_label,
            "evidence_score": self.evidence_score.to_dict(),
            "confidence_score": self.confidence_score.to_dict(),
            "allow_theory_detail": self.allow_theory_detail,
            "inference_type": self.inference_type,
            "theory_sources": list(self.theory_sources),
            "uncertainty": self.uncertainty,
            "detail_items": list(self.detail_items),
        }


def build_detail_expansions(
    *,
    energy: Any,
    picture: Any,
    gates: list[Any] | tuple[Any, ...] | None,
    support: Any = None,
    final_conclusions: list[Any] | tuple[Any, ...] | None = None,
    known_facts: Any = None,
) -> dict[str, DetailExpansion]:
    """Build evidence-first expansion decisions for report domains.

    EvidenceScore answers: is the chart/theory/time evidence sufficient to say
    more? ConfidenceScore answers: has the claim been validated by feedback?
    They intentionally remain separate.
    """

    gate_list = list(gates or [])
    conclusion_list = list(final_conclusions or [])
    return {
        domain: _build_domain_expansion(
            domain=domain,
            energy=energy,
            picture=picture,
            gates=gate_list,
            support=support,
            final_conclusions=conclusion_list,
            known_facts=known_facts,
        )
        for domain in DETAIL_DOMAINS
    }


def _build_domain_expansion(
    *,
    domain: str,
    energy: Any,
    picture: Any,
    gates: list[Any],
    support: Any,
    final_conclusions: list[Any],
    known_facts: Any,
) -> DetailExpansion:
    evidence = _evidence_score(domain, energy, picture, gates, support, final_conclusions)
    confidence = _confidence_score(domain, energy, picture, gates, support, final_conclusions, known_facts)
    level = _expansion_level(evidence.value)
    allow_theory_detail = evidence.value >= 0.75
    label = DOMAIN_LABELS[domain]
    return DetailExpansion(
        domain=domain,
        label=label,
        level=level,
        level_label=_level_label(level),
        evidence_score=evidence,
        confidence_score=confidence,
        allow_theory_detail=allow_theory_detail,
        inference_type="理论推断" if allow_theory_detail and confidence.value <= 0.55 else "验证推断",
        theory_sources=_theory_sources(domain, evidence.components),
        uncertainty=_uncertainty_text(domain, evidence.value, confidence.value, allow_theory_detail),
        detail_items=_detail_items(level, domain),
    )


def _evidence_score(
    domain: str,
    energy: Any,
    picture: Any,
    gates: list[Any],
    support: Any,
    final_conclusions: list[Any],
) -> ScoreBreakdown:
    chart = _chart_completeness(energy, picture)
    coverage = _rule_coverage(domain, energy, picture, support, final_conclusions)
    consensus = _school_consensus(domain, energy, picture, support, final_conclusions)
    timing = _timing_support(domain, gates)
    value = 0.25 * chart + 0.30 * coverage + 0.25 * consensus + 0.20 * timing
    return ScoreBreakdown(
        value=_clamp(value),
        components={
            "chart_completeness": chart,
            "rule_coverage": coverage,
            "school_consensus": consensus,
            "timing_support": timing,
        },
    )


def _confidence_score(
    domain: str,
    energy: Any,
    picture: Any,
    gates: list[Any],
    support: Any,
    final_conclusions: list[Any],
    known_facts: Any,
) -> ScoreBreakdown:
    confidences = [
        _confidence_value(getattr(energy, "confidence", None)),
        _confidence_value(getattr(picture, "confidence", None)),
        _confidence_value(getattr(support, "confidence", None)),
    ]
    confidences.extend(
        _confidence_value(getattr(gate, "confidence", None))
        for gate in gates
        if _same_domain(domain, getattr(gate, "domain", ""))
    )
    confidences.extend(
        _confidence_value(getattr(item, "confidence", None))
        for item in final_conclusions
        if _same_domain(domain, getattr(item, "domain", ""))
    )
    nonzero = [v for v in confidences if v > 0]
    stability = sum(nonzero) / len(nonzero) if nonzero else 0.45
    sample_n = _sample_n(energy) + _sample_n(picture) + _sample_n(support)
    sample_factor = min(sample_n / 10.0, 1.0)
    feedback_factor = min(_known_fact_count(known_facts) / 5.0, 1.0)
    user_consistency = feedback_factor if feedback_factor > 0 else 0.25
    historical_hit_rate = stability if sample_factor >= 0.3 else 0.45
    value = 0.30 * sample_factor + 0.30 * historical_hit_rate + 0.20 * user_consistency + 0.20 * stability
    return ScoreBreakdown(
        value=_clamp(value),
        components={
            "case_validation": sample_factor,
            "historical_hit_rate": historical_hit_rate,
            "user_feedback_consistency": user_consistency,
            "theory_stability": stability,
        },
    )


def _chart_completeness(energy: Any, picture: Any) -> float:
    score = 0.0
    if getattr(energy, "wealth_ceiling", None):
        score += 0.25
    if int(getattr(energy, "layer_count", 0) or 0) > 0:
        score += 0.25
    if getattr(picture, "caifu", None) is not None:
        score += 0.15
    if getattr(picture, "guanming", None) is not None:
        score += 0.15
    if getattr(picture, "marriage_picture", None):
        score += 0.10
    if getattr(picture, "industry_pointers", None):
        score += 0.10
    return _clamp(score)


def _rule_coverage(domain: str, energy: Any, picture: Any, support: Any, final_conclusions: list[Any]) -> float:
    count = 0
    count += len(_evidence_items(energy))
    count += len(_evidence_items(picture))
    count += len(_domain_support_items(domain, support))
    count += sum(1 for item in final_conclusions if _same_domain(domain, getattr(item, "domain", "")))
    if domain == "wealth" and getattr(picture, "caifu", None) is not None:
        count += 2
    if domain == "career" and getattr(picture, "guanming", None) is not None:
        count += 2
    if domain == "marriage" and getattr(picture, "marriage_picture", None):
        count += 2
    if domain == "health" and getattr(support, "health_findings", None):
        count += 2
    if domain == "education" and getattr(support, "ciguan_xuetang", None):
        count += 2
    return _clamp(count / 8.0)


def _school_consensus(domain: str, energy: Any, picture: Any, support: Any, final_conclusions: list[Any]) -> float:
    schools: set[str] = set()
    if _evidence_items(energy):
        schools.add("段")
    if _evidence_items(picture):
        schools.add("杨")
    if _domain_support_items(domain, support) or (domain == "health" and getattr(support, "health_findings", None)):
        schools.add("高")
    for item in final_conclusions:
        if not _same_domain(domain, getattr(item, "domain", "")):
            continue
        schools.update(str(s) for s in (getattr(item, "contributing_schools", None) or []))
    return _clamp(len(schools) / 4.0)


def _timing_support(domain: str, gates: list[Any]) -> float:
    domain_gates = [g for g in gates if _same_domain(domain, getattr(g, "domain", ""))]
    if not domain_gates:
        return 0.35
    best = max(int(getattr(g, "passed_layers", 0) or 0) for g in domain_gates)
    return _clamp(best / 3.0)


def _theory_sources(domain: str, components: Mapping[str, float]) -> list[str]:
    sources = ["段派做功/体用结构", "杨派五步法/取象画像"]
    if components.get("school_consensus", 0.0) >= 0.5:
        sources.append("多流派同向旁证")
    if components.get("timing_support", 0.0) >= 0.67:
        sources.append("任派三层应期支持")
    if domain in {"education", "health", "marriage"}:
        sources.append("高派神煞与专项旁证")
    return sources


def _uncertainty_text(domain: str, evidence: float, confidence: float, allow_theory_detail: bool) -> str:
    label = DOMAIN_LABELS[domain]
    if allow_theory_detail and confidence <= 0.55:
        return f"{label}域证据充分但反馈样本不足；以下细节只按理论链条展开，不等同于已被案例验证。"
    if evidence < 0.75:
        return f"{label}域证据尚不足，只保留粗粒度判断，待大运流年和现实反馈补证。"
    return f"{label}域证据与置信度均可支持展开，仍需后续反馈校准边界。"


def _detail_items(level: int, domain: str) -> list[str]:
    items = ["L0 粗粒度结论"]
    if level >= 1:
        items.append("L1 领域分项")
    if level >= 2:
        items.append("L2 层级预测")
    if level >= 3:
        items.append("L3 人物画像")
    if level >= 4:
        items.append("L4 关键时间节点预测")
    return items


def _expansion_level(evidence_score: float) -> int:
    if evidence_score >= 0.90:
        return 4
    if evidence_score >= 0.82:
        return 3
    if evidence_score >= 0.75:
        return 2
    if evidence_score >= 0.60:
        return 1
    return 0


def _level_label(level: int) -> str:
    return {
        0: "L0 粗粒度结论",
        1: "L1 领域分项",
        2: "L2 层级预测",
        3: "L3 人物画像",
        4: "L4 关键时间节点预测",
    }[level]


def _evidence_items(obj: Any) -> list[Any]:
    return list(getattr(obj, "evidence", None) or []) if obj is not None else []


def _domain_support_items(domain: str, support: Any) -> list[Any]:
    if support is None:
        return []
    shensha = getattr(support, "shensha_supports", None) or {}
    if isinstance(shensha, Mapping):
        return list(shensha.get(domain, []) or [])
    return []


def _confidence_value(confidence: Any) -> float:
    if confidence is None:
        return 0.0
    raw = getattr(confidence, "posterior", None)
    if raw is None:
        raw = getattr(confidence, "percent", None)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0.0
    if value > 1.0:
        value = value / 100.0
    return _clamp(value)


def _sample_n(obj: Any) -> int:
    conf = getattr(obj, "confidence", None) if obj is not None else None
    try:
        return int(getattr(conf, "sample_n", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _known_fact_count(known_facts: Any) -> int:
    if not known_facts:
        return 0
    try:
        return len(list(known_facts))
    except TypeError:
        return 1


def _same_domain(domain: str, raw: Any) -> bool:
    text = str(raw or "")
    return text == domain or DOMAIN_LABELS.get(domain, "") in text


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
