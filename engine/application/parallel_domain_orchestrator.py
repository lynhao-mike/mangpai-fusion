"""pipeline 兼容的并行功能域薄适配层。

本模块不再拼装 blind / production readings，也不得继续扩展业务规则。
职责仅限：
1. 消费 pipeline 现有公开 findings；
2. 触发生产规则库，形成 runner base_context；
3. 构造 DomainAnalyzerRegistry 接线；
4. 调用 canonical run_parallel_domain_analysis()。
"""

from __future__ import annotations

from typing import Iterable, Optional, cast

from engine.application.domain_analyzers import DEFAULT_DOMAINS, build_pipeline_findings_registry
from engine.application.parallel_domain_runner import run_parallel_domain_analysis
from engine.application.production_rule_loader import (
    ProductionRuleLibrary,
    load_default_production_library,
)
from engine.domain.parallel import DomainName, ParallelAnalysisOutput
from engine.energy.types import EnergyFindings
from engine.pangzheng.types import SupportFindings
from engine.picture.types import PictureFindings
from engine.predicates.types import ParsedInput
from engine.yingqi.types import GateResult


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
    """把 pipeline findings 适配到 canonical runner。"""

    selected_domains = list(domains)
    case_id = energy.case_id or (getattr(parsed, "case_id", "") if parsed else "")
    active_library = production_library or load_default_production_library()
    triggered_rules = active_library.triggered_rules(
        parsed=parsed,
        energy=energy,
        picture=picture,
    )
    registry = build_pipeline_findings_registry(selected_domains)
    output = run_parallel_domain_analysis(
        parsed,
        case_id=case_id,
        domains=selected_domains,
        registry=registry,
        base_context={
            "energy": energy,
            "picture": picture,
            "gate_results": gate_results,
            "support": support,
            "production_rules": triggered_rules,
        },
    )
    return cast(ParallelAnalysisOutput, output)
