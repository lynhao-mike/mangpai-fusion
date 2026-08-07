"""六源三领域高风险命题的独立安全门禁。

门禁只约束显式注册的高风险 task。在命题生成后按 task 汇总独立的
非 timing 支持来源；不足时失败关闭为 abstain，不制造 oppose，也不提高置信度。
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import replace
from typing import Any, Iterable

from engine.v5.domain import V5Claim

HIGH_RISK_TASKS = frozenset(
    {
        "wealth.debt",
        "wealth.major_loss_window",
        "marriage.divorce_or_remarriage",
    }
)
MIN_INDEPENDENT_NON_TIMING_SOURCES = 2


def _task_id(claim: V5Claim) -> str:
    return str(claim.metadata.get("task_id", "")).strip()


def _is_timing_only(claim: V5Claim) -> bool:
    return claim.school == "ren_fuhong" or claim.claim_type == "timing_claim"


def _evidence_complete(claim: V5Claim) -> bool:
    return bool(claim.evidence) and all(
        item.source.strip()
        and item.text.strip()
        and bool(item.node_refs or item.rule_ids)
        for item in claim.evidence
    )


def _eligible_independent_sources(claims: Iterable[V5Claim]) -> tuple[str, ...]:
    """返回同一 task 的独立结构/事件支持来源；timing 与旁证命题不计入。"""

    return tuple(
        sorted(
            {
                claim.school
                for claim in claims
                if claim.stance == "support"
                and claim.claim_type in {"structure_claim", "event_claim"}
                and not _is_timing_only(claim)
                and _evidence_complete(claim)
                and bool(claim.falsifiable.strip())
            }
        )
    )


def _failure_reason(claim: V5Claim, independent_source_count: int) -> str:
    if not _evidence_complete(claim):
        return "incomplete_evidence"
    if not claim.falsifiable.strip():
        return "missing_falsifier"
    if independent_source_count < MIN_INDEPENDENT_NON_TIMING_SOURCES:
        return "insufficient_independent_non_timing_sources"
    return ""


def apply_high_risk_gate(claims: list[V5Claim]) -> tuple[list[V5Claim], dict[str, Any]]:
    """门禁高风险命题并返回可写入 snapshot metadata 的确定性审计摘要。

    普通 task 保留原对象和原行为。高风险 task 按同一 task 汇总来源；失败命题
    仅转换为 abstain，置信度原样保留以证明门禁没有做任何增益。
    """

    grouped: dict[str, list[V5Claim]] = defaultdict(list)
    for claim in claims:
        task_id = _task_id(claim)
        if task_id in HIGH_RISK_TASKS:
            grouped[task_id].append(claim)

    source_ledger = {
        task_id: _eligible_independent_sources(task_claims)
        for task_id, task_claims in sorted(grouped.items())
    }
    status_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    gated: list[V5Claim] = []

    for claim in claims:
        task_id = _task_id(claim)
        if task_id not in HIGH_RISK_TASKS:
            gated.append(claim)
            continue

        sources = source_ledger[task_id]
        reason = _failure_reason(claim, len(sources))
        status = "failed" if reason else "passed"
        gate_metadata = {
            "status": status,
            "reason": reason,
            "task_id": task_id,
            "required_independent_source_count": MIN_INDEPENDENT_NON_TIMING_SOURCES,
            "independent_source_count": len(sources),
            "independent_sources": list(sources),
            "evidence_complete": _evidence_complete(claim),
            "falsifier_present": bool(claim.falsifiable.strip()),
            "timing_only_excluded": _is_timing_only(claim),
            "confidence_increased": False,
            "requires_human_review": True,
        }
        metadata = dict(claim.metadata)
        metadata.update({"high_risk": True, "high_risk_gate": gate_metadata})
        status_counts[status] += 1
        if reason:
            reason_counts[reason] += 1
            metadata["high_risk_gate_original_stance"] = claim.stance
            gated.append(
                replace(
                    claim,
                    claim="高风险命题证据未通过独立安全门禁，暂不形成肯定判断。",
                    stance="abstain",
                    probabilistic=False,
                    metadata=metadata,
                )
            )
        else:
            gated.append(replace(claim, metadata=metadata))

    audit = {
        "registry_version": "high-risk-domain-claims-v1",
        "registered_tasks": sorted(HIGH_RISK_TASKS),
        "evaluated_claim_count": sum(status_counts.values()),
        "status_counts": dict(sorted(status_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
        "task_results": [
            {
                "task_id": task_id,
                "independent_source_count": len(sources),
                "independent_sources": list(sources),
                "required_independent_source_count": MIN_INDEPENDENT_NON_TIMING_SOURCES,
            }
            for task_id, sources in source_ledger.items()
        ],
        "confidence_increased": False,
        "reality_accuracy_validated": False,
    }
    return gated, audit
