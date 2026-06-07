"""子平 / 滴天髓生产规则到 V2 Evidence 的适配。"""

from __future__ import annotations

from collections.abc import Iterable

from engine.application.production_rule_loader import ProductionRule
from engine.v2.domain.evidence import SchoolEvidence
from engine.v2.evidence.base import clamp_confidence, normalize_domain, stable_evidence_id


def production_rules_to_evidence(*, case_id: str, rules: Iterable[ProductionRule]) -> list[SchoolEvidence]:
    """把生产规则转换为 V2 SchoolEvidence。

    注意：这里不调用旧链路的生产规则结论转换逻辑，只保留规则作为证据源。
    """

    evidences: list[SchoolEvidence] = []
    for rule in rules:
        domains = list(rule.domains or ["general"])
        for raw_domain in domains:
            domain = normalize_domain(raw_domain)
            evidence_id = stable_evidence_id(case_id, rule.expert_system, rule.id, domain)
            evidences.append(
                SchoolEvidence(
                    evidence_id=evidence_id,
                    case_id=case_id,
                    source_school=rule.expert_system,
                    domain=domain,
                    claim=rule.claim,
                    evidence=f"{rule.title}：{rule.output.statement or rule.claim}",
                    confidence=clamp_confidence(rule.confidence.posterior),
                    source_rule_id=rule.id,
                    trace_ids=[rule.id],
                    polarity="neutral",
                    metadata={
                        "title": rule.title,
                        "topic": rule.topic,
                        "axis_refs": list(rule.axis_refs),
                        "layer": rule.layer,
                        "source_path": rule.source.path,
                        "source_excerpt": rule.source.excerpt,
                        "falsifiable": rule.output.falsifiable,
                    },
                )
            )
    return evidences
