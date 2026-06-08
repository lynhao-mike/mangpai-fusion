"""多流派并行功能域旁路 runner。

该 runner 是 plans/parallel-domain-voting-architecture.md 的最小代码落点：
- 默认不接入生产 pipeline；
- 每个功能域收集盲派、子平、滴天髓 ExpertReading；
- 使用裁判模型生成 DomainAnalysis；
- 未接线专家必须显式 abstain。
"""

from __future__ import annotations

from typing import Any, Sequence

from engine.application.adjudication import adjudicate_domain, build_domain_consensus
from engine.application.domain_analyzers import (
    DEFAULT_DOMAINS,
    DEFAULT_EXPERT_ORDER,
    DomainAnalysisContext,
    DomainAnalyzerRegistry,
    build_empty_parallel_registry,
    EXPERT_LABELS,
    AbstainDomainAnalyzer,
)
from engine.domain.parallel import DomainAnalysis, DomainName, ExpertReading, ExpertSystem, ParallelAnalysisOutput


def run_parallel_domain_analysis(
    parsed: Any,
    *,
    case_id: str | None = None,
    domains: Sequence[DomainName] | None = None,
    expert_order: Sequence[ExpertSystem] = DEFAULT_EXPERT_ORDER,
    registry: DomainAnalyzerRegistry | None = None,
    base_context: dict[str, Any] | None = None,
) -> ParallelAnalysisOutput:
    """运行旁路多专家功能域分析。"""

    resolved_case_id = case_id or _case_id_from_parsed(parsed)
    selected_domains = list(domains or DEFAULT_DOMAINS)
    active_registry = registry or build_empty_parallel_registry()
    shared_base_context = dict(base_context or {})

    analyses: list[DomainAnalysis] = []
    for domain in selected_domains:
        readings = [
            _safe_analyze(
                parsed=parsed,
                domain=domain,
                case_id=resolved_case_id,
                expert_system=expert_system,
                registry=active_registry,
                base_context=shared_base_context,
            )
            for expert_system in expert_order
        ]
        adjudication = adjudicate_domain(
            case_id=resolved_case_id,
            domain=domain,
            readings=readings,
        )
        consensus = build_domain_consensus(
            case_id=resolved_case_id,
            domain=domain,
            readings=readings,
            adjudication=adjudication,
        )
        analyses.append(
            DomainAnalysis(
                domain=domain,
                readings=readings,
                adjudication_result=adjudication,
                consensus=consensus,
                conflicts=[],
            )
        )

    return ParallelAnalysisOutput(
        case_id=resolved_case_id,
        domain_analyses=analyses,
    )


def _safe_analyze(
    *,
    parsed: Any,
    domain: DomainName,
    case_id: str,
    expert_system: ExpertSystem,
    registry: DomainAnalyzerRegistry,
    base_context: dict[str, Any],
) -> ExpertReading:
    context = DomainAnalysisContext(
        case_id=case_id,
        base_context=dict(base_context),
    )
    try:
        return registry.get(domain, expert_system).analyze(parsed, domain, context)
    except Exception as exc:  # noqa: BLE001
        return AbstainDomainAnalyzer(
            expert_system=expert_system,
            expert_name=EXPERT_LABELS[expert_system],
            reason=f"分析器异常，按隔离原则弃权：{exc}",
        ).analyze(parsed, domain, context)


def _case_id_from_parsed(parsed: Any) -> str:
    case_id = getattr(parsed, "case_id", None)
    if case_id:
        return str(case_id)
    meta = getattr(parsed, "meta", None)
    if isinstance(meta, dict) and meta.get("case_id"):
        return str(meta["case_id"])
    return "C-UNKNOWN"
