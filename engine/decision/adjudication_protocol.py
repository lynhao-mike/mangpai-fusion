"""统一的目标级裁决单位协议。

这个模块只负责把既有 Claim 与 L6 StageDecision 投影成可追溯的
目标级裁决单位。它不新增命理规则、权重或现实结果 taxonomy。
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Literal, Mapping, Sequence

from engine.claims.domain import Claim
from engine.decision.l6_staged_arbitration import StageDecision

AdjudicationStatus = Literal[
    "PRIMARY",
    "COEXIST",
    "UNRESOLVED",
    "NO_MAPPING",
    "ABSTAIN",
    "UNSUPPORTED",
]
MappingStatus = Literal["NOT_APPLICABLE", "UNASSESSED", "NO_MAPPING", "MAPPED"]


def _status_for(result: str) -> AdjudicationStatus:
    if result in {"winner", "conflict_resolved"}:
        return "PRIMARY"
    if result == "coexist":
        return "COEXIST"
    if result == "unresolved":
        return "UNRESOLVED"
    if result == "reject_all":
        return "ABSTAIN"
    raise ValueError(f"unsupported stage decision result: {result}")


@dataclass(frozen=True)
class AdjudicationUnit:
    """一个现实问题或结构目标的最小裁决制品。

    ``PRIMARY`` 只表示当前命理命题层已经完成目标级裁决；它不表示
    已经完成 L2→现实 outcome 映射。若映射不存在，调用方必须使用
    ``NO_MAPPING``，不能把结构主断冒充现实结论。
    """

    domain: str
    task_id: str
    target_id: str
    claim_type: str
    candidate_claim_ids: tuple[str, ...]
    supporting_fact_refs: tuple[str, ...]
    rule_ids: tuple[str, ...]
    applicability: Mapping[str, Any]
    counterevidence: tuple[str, ...]
    falsifiers: tuple[str, ...]
    status: AdjudicationStatus
    winner_claim_ids: tuple[str, ...] = ()
    rationale: str = ""
    mapping_status: MappingStatus = "UNASSESSED"
    mapping_type: str | None = None
    outcome_indicators: tuple[str, ...] = ()
    mapping_reason: str = ""

    def __post_init__(self) -> None:
        for name in ("domain", "task_id", "target_id", "claim_type"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} is required")
        if self.status not in {
            "PRIMARY", "COEXIST", "UNRESOLVED", "NO_MAPPING", "ABSTAIN", "UNSUPPORTED",
        }:
            raise ValueError(f"invalid adjudication status: {self.status}")
        if self.mapping_status not in {"NOT_APPLICABLE", "UNASSESSED", "NO_MAPPING", "MAPPED"}:
            raise ValueError(f"invalid mapping status: {self.mapping_status}")
        for name in (
            "candidate_claim_ids", "supporting_fact_refs", "rule_ids",
            "counterevidence", "falsifiers", "winner_claim_ids", "outcome_indicators",
        ):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        object.__setattr__(self, "applicability", MappingProxyType(dict(self.applicability)))
        candidate_ids = set(self.candidate_claim_ids)
        if not set(self.winner_claim_ids).issubset(candidate_ids):
            raise ValueError("winner_claim_ids must be retained in candidate_claim_ids")
        if self.status in {"PRIMARY", "COEXIST"} and not self.winner_claim_ids:
            raise ValueError(f"{self.status} requires winner_claim_ids")
        if self.status in {"UNRESOLVED", "NO_MAPPING", "ABSTAIN", "UNSUPPORTED"} and self.winner_claim_ids:
            raise ValueError(f"{self.status} cannot contain winner_claim_ids")
        if self.mapping_status == "MAPPED" and not self.outcome_indicators:
            raise ValueError("MAPPED requires outcome_indicators")

    @classmethod
    def from_stage_decision(
        cls,
        decision: StageDecision,
        claims: Sequence[Claim],
    ) -> "AdjudicationUnit":
        """从一个 L6 叶节点生成单位；不使用 claim 顺序或置信度选胜者。"""

        claim_by_id = {claim.claim_id: claim for claim in claims}
        candidate_ids = tuple(dict.fromkeys(
            decision.winner_claim_ids
            + decision.minority_claim_ids
            + decision.rejected_claim_ids
        ))
        candidate_claims = [claim_by_id[item] for item in candidate_ids if item in claim_by_id]
        winning_ids = tuple(item for item in decision.winner_claim_ids if item in claim_by_id)
        status = _status_for(decision.result)
        if status in {"PRIMARY", "COEXIST"}:
            winner_claim_ids = winning_ids
        else:
            winner_claim_ids = ()
        supporting_fact_refs = tuple(dict.fromkeys(
            ref
            for claim in candidate_claims
            for evidence in claim.evidence
            for ref in evidence.fact_refs
        ))
        rule_ids = tuple(dict.fromkeys(
            evidence.rule_id
            for claim in candidate_claims
            for evidence in claim.evidence
        ))
        counterevidence = tuple(dict.fromkeys(
            evidence.evidence_id
            for claim in candidate_claims
            if claim.claim_id not in winning_ids
            for evidence in claim.evidence
        ))
        falsifiers = tuple(dict.fromkeys(claim.falsifier for claim in candidate_claims))
        applicability = {
            "by_claim": {
                claim.claim_id: dict(claim.applicability_snapshot)
                for claim in candidate_claims
            }
        }
        claim_type = candidate_claims[0].claim_type if candidate_claims else decision.stage
        return cls(
            domain=decision.domain,
            task_id=decision.task_id,
            target_id=decision.target_id or decision.task_id,
            claim_type=claim_type,
            candidate_claim_ids=candidate_ids,
            supporting_fact_refs=supporting_fact_refs,
            rule_ids=rule_ids,
            applicability=applicability,
            counterevidence=counterevidence,
            falsifiers=falsifiers,
            status=status,
            winner_claim_ids=winner_claim_ids,
            rationale=decision.rationale,
            mapping_status="NOT_APPLICABLE",
            mapping_reason="结构命题尚未进入现实 outcome 映射层。",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "task_id": self.task_id,
            "target_id": self.target_id,
            "claim_type": self.claim_type,
            "candidate_claim_ids": list(self.candidate_claim_ids),
            "supporting_fact_refs": list(self.supporting_fact_refs),
            "rule_ids": list(self.rule_ids),
            "applicability": dict(self.applicability),
            "counterevidence": list(self.counterevidence),
            "falsifiers": list(self.falsifiers),
            "status": self.status,
            "winner_claim_ids": list(self.winner_claim_ids),
            "rationale": self.rationale,
            "mapping_status": self.mapping_status,
            "mapping_type": self.mapping_type,
            "outcome_indicators": list(self.outcome_indicators),
            "mapping_reason": self.mapping_reason,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AdjudicationUnit":
        return cls(
            domain=str(data["domain"]),
            task_id=str(data["task_id"]),
            target_id=str(data["target_id"]),
            claim_type=str(data["claim_type"]),
            candidate_claim_ids=tuple(str(item) for item in data.get("candidate_claim_ids", [])),
            supporting_fact_refs=tuple(str(item) for item in data.get("supporting_fact_refs", [])),
            rule_ids=tuple(str(item) for item in data.get("rule_ids", [])),
            applicability=dict(data.get("applicability", {})),
            counterevidence=tuple(str(item) for item in data.get("counterevidence", [])),
            falsifiers=tuple(str(item) for item in data.get("falsifiers", [])),
            status=str(data["status"]),  # type: ignore[arg-type]
            winner_claim_ids=tuple(str(item) for item in data.get("winner_claim_ids", [])),
            rationale=str(data.get("rationale", "")),
            mapping_status=str(data.get("mapping_status", "UNASSESSED")),  # type: ignore[arg-type]
            mapping_type=str(data["mapping_type"]) if data.get("mapping_type") else None,
            outcome_indicators=tuple(str(item) for item in data.get("outcome_indicators", [])),
            mapping_reason=str(data.get("mapping_reason", "")),
        )
