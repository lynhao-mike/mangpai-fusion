"""把现有 V5 命题投影为目标级裁决单位。

这里复用现有 claim 的 stance、证据与 falsifier，不新增派别权重或命理规则。
同一目标出现支持与反对时保留 ``UNRESOLVED``；多个同向命题以
``COEXIST`` 输出，避免把多条观点伪装成一个人工挑出的 winner。
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from engine.decision.adjudication_protocol import AdjudicationUnit
from engine.v5.domain import V5Claim


def _task_id(claim: V5Claim) -> str:
    return str(claim.metadata.get("task_id", "")).strip()


def _target_id(claim: V5Claim) -> tuple[str, str, bool]:
    task_id = _task_id(claim)
    explicit = str(claim.metadata.get("target_id", "")).strip()
    target_id = explicit or task_id
    if target_id:
        return task_id or target_id, target_id, True
    # 这是内部失败哨兵，不是可以展示或用于现实测量的 outcome label。
    missing = f"__missing_target__.{claim.domain}.{claim.claim_type}"
    return missing, missing, False


def _unit_status(claims: list[V5Claim], has_target: bool) -> tuple[str, tuple[str, ...]]:
    if not has_target:
        return "UNSUPPORTED", ()
    active = [claim for claim in claims if claim.stance != "abstain"]
    if not active:
        return "ABSTAIN", ()
    stances = {claim.stance for claim in active}
    if len(stances) > 1 or "mixed" in stances:
        return "UNRESOLVED", ()
    if len(active) == 1:
        return "PRIMARY", (active[0].claim_id,)
    return "COEXIST", tuple(claim.claim_id for claim in active)


def build_v5_adjudication_units(claims: list[V5Claim]) -> tuple[AdjudicationUnit, ...]:
    """按领域、任务、目标和命题阶段生成确定性的裁决单位。"""

    grouped: dict[tuple[str, str, str, str], list[V5Claim]] = defaultdict(list)
    for claim in claims:
        task_id, target_id, has_target = _target_id(claim)
        grouped[(claim.domain, task_id, target_id, claim.claim_type)].append(claim)

    units: list[AdjudicationUnit] = []
    for (domain, task_id, target_id, claim_type), group in sorted(grouped.items()):
        has_target = not target_id.startswith("__missing_target__.")
        status, winner_ids = _unit_status(group, has_target)
        candidate_ids = tuple(claim.claim_id for claim in group)
        winning = set(winner_ids)
        supporting_facts = tuple(dict.fromkeys(
            ref
            for claim in group
            for evidence in claim.evidence
            for ref in evidence.node_refs
        ))
        rule_ids = tuple(dict.fromkeys(
            rule_id
            for claim in group
            for evidence in claim.evidence
            for rule_id in evidence.rule_ids
        ))
        counterevidence = tuple(dict.fromkeys(
            evidence.evidence_id
            for claim in group
            if claim.claim_id not in winning
            for evidence in (*claim.evidence, *claim.counter_evidence)
        ))
        applicability: dict[str, Any] = {
            "by_claim": {
                claim.claim_id: {
                    "task_id": _task_id(claim),
                    "target_id": str(claim.metadata.get("target_id", "")).strip(),
                    "runner_state": str(claim.metadata.get("runner_state", "")),
                }
                for claim in group
            }
        }
        units.append(AdjudicationUnit(
            domain=domain,
            task_id=task_id,
            target_id=target_id,
            claim_type=claim_type,
            candidate_claim_ids=candidate_ids,
            supporting_fact_refs=supporting_facts,
            rule_ids=rule_ids,
            applicability=applicability,
            counterevidence=counterevidence,
            falsifiers=tuple(dict.fromkeys(claim.falsifiable for claim in group if claim.falsifiable)),
            status=status,  # type: ignore[arg-type]
            winner_claim_ids=winner_ids,
            rationale=(
                "同一目标存在支持与反对命题，保留未决。"
                if status == "UNRESOLVED"
                else "多条同向命题允许并存。"
                if status == "COEXIST"
                else "该目标仅有一条有效命题。"
                if status == "PRIMARY"
                else "该目标当前只有弃权命题。"
                if status == "ABSTAIN"
                else "命题缺少显式 task_id/target_id，不能进入目标级裁决。"
            ),
            mapping_status="NO_MAPPING",
            mapping_reason="当前没有已批准的 CHART_L2→现实 outcome mapping。",
        ))
    return tuple(units)


__all__ = ["build_v5_adjudication_units"]
