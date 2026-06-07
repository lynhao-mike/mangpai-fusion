"""V2 实战推理旁路 runner。"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from engine.application.production_rule_loader import (
    ProductionRule,
    ProductionRuleLibrary,
    load_default_production_library,
)
from engine.predicates.types import ParsedInput
from engine.v2.agents import run_domain_agents
from engine.v2.domain.output import V2AnalysisOutput
from engine.v2.evidence.adapters import build_school_evidences
from engine.v2.evidence.builder import build_domain_evidences
from engine.v2.events import build_event_candidates
from engine.v2.similarity import find_similar_cases


def run_v2_reasoning(
    *,
    parsed: ParsedInput | None,
    energy: Any,
    picture: Any,
    gate_results: list[Any],
    support: Any,
    production_library: ProductionRuleLibrary | None = None,
    production_rules: Iterable[ProductionRule] | None = None,
) -> V2AnalysisOutput:
    """运行 V2 只读旁路。

    - 不调用旧结论合成逻辑；
    - 不修改 AnalysisOutput；
    - 不改变 D1-D4 findings；
    - 只输出 V2AnalysisOutput。
    """

    case_id = _case_id(parsed=parsed, energy=energy, picture=picture)
    rules = list(production_rules) if production_rules is not None else _triggered_rules(
        parsed=parsed,
        energy=energy,
        picture=picture,
        production_library=production_library,
    )
    school_evidences = build_school_evidences(
        case_id=case_id,
        energy=energy,
        picture=picture,
        gate_results=gate_results,
        support=support,
        production_rules=rules,
    )
    domain_evidences = build_domain_evidences(school_evidences)
    domain_results = run_domain_agents(domain_evidences)
    event_candidates = build_event_candidates(domain_results)
    similar_cases = find_similar_cases(
        case_id=case_id,
        domain_evidences=domain_evidences,
        event_candidates=event_candidates,
    )
    return V2AnalysisOutput(
        case_id=case_id,
        school_evidences=school_evidences,
        domain_evidences=domain_evidences,
        domain_results=domain_results,
        event_candidates=event_candidates,
        similar_cases=similar_cases,
        report_sections={
            "基础结构": {},
            "格局": {},
            "调候": {},
            "体用做功": {},
            "领域分析": {item.domain: item.confidence for item in domain_results},
            "事件预测": [item.to_dict() for item in event_candidates],
            "应期分析": [],
            "案例验证": [item.to_dict() for item in similar_cases],
            "最终结论": [],
        },
    )


def _triggered_rules(
    *,
    parsed: ParsedInput | None,
    energy: Any,
    picture: Any,
    production_library: ProductionRuleLibrary | None,
) -> list[ProductionRule]:
    library = production_library or load_default_production_library()
    return library.triggered_rules(parsed=parsed, energy=energy, picture=picture)


def _case_id(*, parsed: ParsedInput | None, energy: Any, picture: Any) -> str:
    for obj in (parsed, energy, picture):
        if obj is None:
            continue
        case_id = getattr(obj, "case_id", "")
        if case_id:
            return str(case_id)
    return ""
