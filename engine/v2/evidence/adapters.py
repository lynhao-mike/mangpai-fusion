"""V2 Evidence 适配总入口。"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from engine.application.production_rule_loader import ProductionRule
from engine.v2.domain.evidence import SchoolEvidence
from engine.v2.evidence.production_rules import production_rules_to_evidence
from engine.v2.evidence.runtime_findings import (
    energy_to_evidence,
    gate_results_to_evidence,
    picture_to_evidence,
    support_to_evidence,
)


def build_school_evidences(
    *,
    case_id: str,
    energy: Any,
    picture: Any,
    gate_results: list[Any],
    support: Any,
    production_rules: Iterable[ProductionRule] | None = None,
) -> list[SchoolEvidence]:
    """构建 V2 所需的全流派证据列表。

    本函数只做只读适配，不修改任何 V1 findings，也不生成最终结论。
    """

    evidences: list[SchoolEvidence] = []
    evidences.extend(energy_to_evidence(energy))
    evidences.extend(picture_to_evidence(picture))
    evidences.extend(gate_results_to_evidence(gate_results, case_id=case_id))
    evidences.extend(support_to_evidence(support))
    if production_rules is not None:
        evidences.extend(production_rules_to_evidence(case_id=case_id, rules=production_rules))
    return _with_case_id(evidences, case_id)


def _with_case_id(evidences: list[SchoolEvidence], case_id: str) -> list[SchoolEvidence]:
    """补齐旧 findings 可能缺失的 case_id。"""

    output: list[SchoolEvidence] = []
    for item in evidences:
        if item.case_id:
            output.append(item)
            continue
        output.append(
            SchoolEvidence(
                evidence_id=item.evidence_id,
                case_id=case_id,
                source_school=item.source_school,
                domain=item.domain,
                claim=item.claim,
                evidence=item.evidence,
                confidence=item.confidence,
                source_rule_id=item.source_rule_id,
                trace_ids=list(item.trace_ids),
                time_scope=dict(item.time_scope) if item.time_scope is not None else None,
                polarity=item.polarity,
                metadata=dict(item.metadata),
            )
        )
    return output
