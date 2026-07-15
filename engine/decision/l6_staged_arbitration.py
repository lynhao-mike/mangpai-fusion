"""L6 分段仲裁：结构、事件、应期独立裁决并显式消解对立命题。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, Mapping, Protocol, Sequence

import yaml

from engine.claims.domain import Claim

Stage = Literal["structure", "event", "timing"]
DecisionResult = Literal["winner", "coexist", "unresolved", "reject_all", "conflict_resolved"]
ConflictType = Literal["none", "polarity_opposition", "magnitude_opposition", "occurrence_opposition"]
ResolutionStrategy = Literal[
    "capability_weighted",
    "evidence_completeness",
    "structure_precedence",
    "conservative_high_risk",
]
WeightSource = Literal["l1_capability", "uniform_fallback"]

_STAGES: tuple[Stage, ...] = ("structure", "event", "timing")
_CLAIM_STAGE: dict[str, Stage] = {
    "structure_claim": "structure",
    "event_claim": "event",
    "timing_claim": "timing",
}
_REJECT_THRESHOLD = 0.1
_MAGNITUDE_GAP = 0.5
_HIGH_RISK_OVERWHELMING_GAP = 0.6


@dataclass(frozen=True)
class StageDecision:
    stage: Stage
    domain: str
    result: DecisionResult
    task_id: str = ""
    target_id: str = ""
    winner_side: str | None = None
    winner_claim_ids: tuple[str, ...] = ()
    minority_claim_ids: tuple[str, ...] = ()
    rejected_claim_ids: tuple[str, ...] = ()
    conflict_type: ConflictType = "none"
    resolution_rule_id: str | None = None
    weighted_support: float = 0.0
    weighted_oppose: float = 0.0
    rationale: str = ""
    domain_decisions: tuple[StageDecision, ...] = ()

    def __post_init__(self) -> None:
        if self.stage not in _STAGES:
            raise ValueError("invalid stage")
        if self.result not in {"winner", "coexist", "unresolved", "reject_all", "conflict_resolved"}:
            raise ValueError("invalid result")
        if self.conflict_type not in {"none", "polarity_opposition", "magnitude_opposition", "occurrence_opposition"}:
            raise ValueError("invalid conflict_type")
        if self.result == "conflict_resolved" and not self.resolution_rule_id:
            raise ValueError("conflict_resolved requires resolution_rule_id")
        for name in ("winner_claim_ids", "minority_claim_ids", "rejected_claim_ids", "domain_decisions"):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        if any(item.stage != self.stage or item.domain_decisions for item in self.domain_decisions):
            raise ValueError("domain_decisions must be leaf decisions from the same stage")

    @classmethod
    def empty(cls, stage: Stage) -> StageDecision:
        return cls(stage=stage, domain="", result="reject_all", rationale="该段无可裁决命题。")

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "domain": self.domain,
            "result": self.result,
            "task_id": self.task_id,
            "target_id": self.target_id,
            "winner_side": self.winner_side,
            "winner_claim_ids": list(self.winner_claim_ids),
            "minority_claim_ids": list(self.minority_claim_ids),
            "rejected_claim_ids": list(self.rejected_claim_ids),
            "conflict_type": self.conflict_type,
            "resolution_rule_id": self.resolution_rule_id,
            "weighted_support": self.weighted_support,
            "weighted_oppose": self.weighted_oppose,
            "rationale": self.rationale,
            "domain_decisions": [item.to_dict() for item in self.domain_decisions],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> StageDecision:
        return cls(
            stage=str(data["stage"]),  # type: ignore[arg-type]
            domain=str(data.get("domain", "")),
            result=str(data["result"]),  # type: ignore[arg-type]
            task_id=str(data.get("task_id", "")),
            target_id=str(data.get("target_id", "")),
            winner_side=str(data["winner_side"]) if data.get("winner_side") else None,
            winner_claim_ids=tuple(str(item) for item in data.get("winner_claim_ids", [])),
            minority_claim_ids=tuple(str(item) for item in data.get("minority_claim_ids", [])),
            rejected_claim_ids=tuple(str(item) for item in data.get("rejected_claim_ids", [])),
            conflict_type=str(data.get("conflict_type", "none")),  # type: ignore[arg-type]
            resolution_rule_id=str(data["resolution_rule_id"]) if data.get("resolution_rule_id") else None,
            weighted_support=float(data.get("weighted_support", 0.0)),
            weighted_oppose=float(data.get("weighted_oppose", 0.0)),
            rationale=str(data.get("rationale", "")),
            domain_decisions=tuple(StageDecision.from_dict(item) for item in data.get("domain_decisions", [])),
        )


@dataclass(frozen=True)
class StagedArbitrationResult:
    case_id: str
    stages: tuple[StageDecision, ...]
    weight_source: WeightSource

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id is required")
        object.__setattr__(self, "stages", tuple(self.stages))
        if len(self.stages) != 3:
            raise ValueError("stages must contain exactly three decisions")
        if tuple(item.stage for item in self.stages) != _STAGES:
            raise ValueError("stages must be ordered structure, event, timing")
        if self.weight_source not in {"l1_capability", "uniform_fallback"}:
            raise ValueError("invalid weight_source")

    def stage(self, stage: Stage) -> StageDecision:
        return self.stages[_STAGES.index(stage)]

    def to_dict(self) -> dict[str, Any]:
        return {"case_id": self.case_id, "stages": [item.to_dict() for item in self.stages], "weight_source": self.weight_source}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> StagedArbitrationResult:
        return cls(
            case_id=str(data["case_id"]),
            stages=tuple(StageDecision.from_dict(item) for item in data.get("stages", [])),
            weight_source=str(data["weight_source"]),  # type: ignore[arg-type]
        )

    def save_json(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load_json(cls, path: str | Path) -> StagedArbitrationResult:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("staged arbitration JSON must be an object")
        return cls.from_dict(data)


class SchoolWeightPlan(Protocol):
    source: WeightSource

    def school_weight(self, school_id: str, task_id: str) -> float: ...


@dataclass(frozen=True)
class ApplicabilityPlan:
    """L1 每任务、每流派权重的只读持久化快照。"""

    task_school_weights: Mapping[str, Mapping[str, float]] = field(default_factory=dict)
    source: WeightSource = "l1_capability"

    def __post_init__(self) -> None:
        if self.source not in {"l1_capability", "uniform_fallback"}:
            raise ValueError("invalid applicability source")
        frozen: dict[str, Mapping[str, float]] = {}
        for task_id, weights in self.task_school_weights.items():
            normalized = {str(school): float(weight) for school, weight in weights.items()}
            if any(not 0.0 <= weight <= 1.0 for weight in normalized.values()):
                raise ValueError("school weights must be between 0 and 1")
            frozen[str(task_id)] = MappingProxyType(normalized)
        object.__setattr__(self, "task_school_weights", MappingProxyType(frozen))

    @classmethod
    def uniform(cls) -> ApplicabilityPlan:
        return cls(source="uniform_fallback")

    @classmethod
    def from_route_plan(cls, route_plan: Any) -> ApplicabilityPlan:
        routes = getattr(route_plan, "per_task_routes", None)
        if not isinstance(routes, Mapping):
            raise TypeError("applicability must be ApplicabilityPlan, RoutePlan, or None")
        return cls({str(task_id): dict(route.school_scores) for task_id, route in routes.items()})

    def school_weight(self, school_id: str, task_id: str) -> float:
        if self.source == "uniform_fallback":
            return 1.0
        return float(self.task_school_weights.get(task_id, {}).get(school_id, 0.0))


def _coerce_plan(applicability: Any | None, claims: Sequence[Claim]) -> ApplicabilityPlan:
    if applicability is None:
        return ApplicabilityPlan.uniform()
    plan = applicability if isinstance(applicability, ApplicabilityPlan) else ApplicabilityPlan.from_route_plan(applicability)
    if any(claim.school_id not in plan.task_school_weights.get(claim.task_id, {}) for claim in claims):
        return ApplicabilityPlan.uniform()
    return plan


@dataclass(frozen=True)
class ConflictRule:
    rule_id: str
    applies_to_stage: Stage
    conflict_type: ConflictType
    target_claim_type: str
    resolution_strategy: ResolutionStrategy
    min_weight_gap: float
    falsifier: str
    domains: tuple[str, ...] = ()
    high_risk_only: bool = False

    def __post_init__(self) -> None:
        if not self.rule_id.strip() or not self.target_claim_type.strip() or not self.falsifier.strip():
            raise ValueError("conflict rule identifiers and falsifier are required")
        if self.applies_to_stage not in _STAGES:
            raise ValueError("invalid conflict rule stage")
        if self.conflict_type == "none":
            raise ValueError("conflict rule cannot target none")
        if self.resolution_strategy not in {"capability_weighted", "evidence_completeness", "structure_precedence", "conservative_high_risk"}:
            raise ValueError("invalid resolution_strategy")
        if type(self.high_risk_only) is not bool:
            raise ValueError("high_risk_only must be boolean")
        if not 0.0 <= self.min_weight_gap <= 1.0:
            raise ValueError("min_weight_gap must be between 0 and 1")
        object.__setattr__(self, "domains", tuple(self.domains))

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ConflictRule:
        return cls(
            rule_id=str(data["rule_id"]),
            applies_to_stage=str(data["applies_to_stage"]),  # type: ignore[arg-type]
            conflict_type=str(data["conflict_type"]),  # type: ignore[arg-type]
            target_claim_type=str(data["target_claim_type"]),
            resolution_strategy=str(data["resolution_strategy"]),  # type: ignore[arg-type]
            min_weight_gap=float(data.get("min_weight_gap", 0.0)),
            falsifier=str(data["falsifier"]),
            domains=tuple(str(item) for item in data.get("domains", [])),
            high_risk_only=_strict_bool(data.get("high_risk_only", False), "high_risk_only"),
        )


def _strict_bool(value: Any, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be boolean")
    return value


@dataclass(frozen=True)
class ConflictRuleSet:
    rules: tuple[ConflictRule, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "rules", tuple(self.rules))
        ids = [item.rule_id for item in self.rules]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate conflict rule_id")

    @classmethod
    def empty(cls) -> ConflictRuleSet:
        return cls(())

    @classmethod
    def from_yaml(cls, path: str | Path) -> ConflictRuleSet:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, Mapping) or raw.get("schema_version") != "l6-conflict-rules/v1":
            raise ValueError("conflict rule schema_version must be l6-conflict-rules/v1")
        rules = raw.get("rules")
        if not isinstance(rules, list):
            raise ValueError("conflict rules must be a list")
        return cls(tuple(ConflictRule.from_dict(item) for item in rules))

    def match(self, stage: Stage, conflict_type: ConflictType, claims: Sequence[Claim], domain: str) -> ConflictRule | None:
        claim_types = {item.claim_type for item in claims}
        high_risk = any(item.high_risk for item in claims)
        matches = [
            rule for rule in self.rules
            if rule.applies_to_stage == stage
            and rule.conflict_type == conflict_type
            and rule.target_claim_type in claim_types
            and (not rule.domains or domain in rule.domains)
            and (not rule.high_risk_only or high_risk)
        ]
        if not matches:
            if high_risk and conflict_type != "none":
                claim_type = next(iter(claim_types))
                return ConflictRule(
                    rule_id=f"CR-HIGH-RISK-DEFAULT-{stage.upper()}-{conflict_type.upper()}",
                    applies_to_stage=stage,
                    conflict_type=conflict_type,
                    target_claim_type=claim_type,
                    resolution_strategy="conservative_high_risk",
                    min_weight_gap=0.8,
                    falsifier="若高风险治理策略变更，则重新审核默认保守规则。",
                    high_risk_only=True,
                )
            return None
        selected = max(matches, key=lambda rule: (rule.high_risk_only, bool(rule.domains), rule.resolution_strategy == "conservative_high_risk"))
        if high_risk and selected.resolution_strategy != "conservative_high_risk":
            return ConflictRule(
                rule_id=f"CR-HIGH-RISK-DEFAULT-{stage.upper()}-{conflict_type.upper()}",
                applies_to_stage=stage,
                conflict_type=conflict_type,
                target_claim_type=selected.target_claim_type,
                resolution_strategy="conservative_high_risk",
                min_weight_gap=0.8,
                falsifier="若高风险治理策略变更，则重新审核默认保守规则。",
                high_risk_only=True,
            )
        return selected


def detect_opposition(claims: Sequence[Claim]) -> ConflictType:
    if len(claims) < 2 or len({item.task_id for item in claims}) != 1:
        return "none"
    if {item.stance for item in claims} == {"support", "oppose"}:
        return "occurrence_opposition"
    polarities = {item.polarity for item in claims}
    if "positive" in polarities and "negative" in polarities:
        return "polarity_opposition"
    magnitudes = [item.magnitude for item in claims if item.magnitude is not None]
    if len(magnitudes) >= 2 and max(magnitudes) - min(magnitudes) >= _MAGNITUDE_GAP:
        return "magnitude_opposition"
    return "none"


def _side(claim: Claim, conflict_type: ConflictType) -> str:
    if conflict_type == "occurrence_opposition":
        return claim.stance
    if conflict_type == "polarity_opposition":
        return claim.polarity
    if conflict_type == "magnitude_opposition":
        return "high" if (claim.magnitude or 0.0) >= 0.5 else "low"
    return "support"


def _weighted_sides(claims: Sequence[Claim], plan: ApplicabilityPlan, conflict_type: ConflictType) -> dict[str, float]:
    totals: dict[str, float] = {}
    for claim in claims:
        side = _side(claim, conflict_type)
        totals[side] = totals.get(side, 0.0) + plan.school_weight(claim.school_id, claim.task_id)
    return totals


def _display_support_oppose(totals: Mapping[str, float], conflict_type: ConflictType) -> tuple[float, float]:
    if conflict_type == "occurrence_opposition":
        return totals.get("support", 0.0), totals.get("oppose", 0.0)
    if conflict_type == "polarity_opposition":
        return totals.get("positive", 0.0), totals.get("negative", 0.0)
    return totals.get("high", 0.0), totals.get("low", 0.0)


def _unresolved(stage: Stage, domain: str, claims: Sequence[Claim], conflict_type: ConflictType, rule: ConflictRule | None, rationale: str, plan: ApplicabilityPlan) -> StageDecision:
    support, oppose = _display_support_oppose(_weighted_sides(claims, plan, conflict_type), conflict_type)
    first = claims[0]
    return StageDecision(
        stage, domain, "unresolved", task_id=first.task_id, target_id=first.target_id,
        minority_claim_ids=tuple(item.claim_id for item in claims),
        conflict_type=conflict_type, resolution_rule_id=rule.rule_id if rule else None,
        weighted_support=round(support, 6), weighted_oppose=round(oppose, 6), rationale=rationale,
    )


def _resolved(stage: Stage, domain: str, claims: Sequence[Claim], winners: Sequence[Claim], conflict_type: ConflictType, rule: ConflictRule, plan: ApplicabilityPlan, rationale: str) -> StageDecision:
    support, oppose = _display_support_oppose(_weighted_sides(claims, plan, conflict_type), conflict_type)
    winner_ids = tuple(item.claim_id for item in winners)
    first = claims[0]
    winner_side = _side(winners[0], conflict_type) if winners else None
    return StageDecision(
        stage, domain, "conflict_resolved", task_id=first.task_id, target_id=first.target_id, winner_side=winner_side,
        winner_claim_ids=winner_ids,
        minority_claim_ids=tuple(item.claim_id for item in claims if item.claim_id not in winner_ids),
        conflict_type=conflict_type, resolution_rule_id=rule.rule_id,
        weighted_support=round(support, 6), weighted_oppose=round(oppose, 6), rationale=rationale,
    )


def _resolve_conflict(
    stage: Stage,
    domain: str,
    claims: Sequence[Claim],
    conflict_type: ConflictType,
    rule: ConflictRule,
    plan: ApplicabilityPlan,
    structure_decision: StageDecision | None,
) -> StageDecision:
    totals = _weighted_sides(claims, plan, conflict_type)
    ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0]))

    if rule.resolution_strategy == "evidence_completeness":
        scores = {item.claim_id: len(item.evidence) for item in claims}
        best = max(scores.values())
        winners = [item for item in claims if scores[item.claim_id] == best]
        if len(winners) != 1:
            return _unresolved(stage, domain, claims, conflict_type, rule, "对立双方证据完整度持平，保留争议。", plan)
        return _resolved(stage, domain, claims, winners, conflict_type, rule, plan, f"显式规则 {rule.rule_id} 以证据完整度消解对立。")

    if rule.resolution_strategy == "structure_precedence":
        if structure_decision is None or structure_decision.result in {"reject_all", "unresolved"}:
            return _unresolved(stage, domain, claims, conflict_type, rule, "对应领域结构结论不足，结构优先规则不能强行消解。", plan)
        structure_side = structure_decision.winner_side
        winner_claims = [item for item in claims if structure_side and _side(item, conflict_type) == structure_side]
        if not winner_claims:
            return _unresolved(stage, domain, claims, conflict_type, rule, "结构结论未提供可映射方向，保留争议。", plan)
        return _resolved(stage, domain, claims, winner_claims, conflict_type, rule, plan, f"显式规则 {rule.rule_id} 服从同领域结构结论。")

    if len(ranked) < 2:
        return _unresolved(stage, domain, claims, conflict_type, rule, "对立侧不足，无法按规则消解。", plan)
    winning_side, winning_score = ranked[0]
    gap = winning_score - ranked[1][1]
    threshold = rule.min_weight_gap
    if rule.resolution_strategy == "conservative_high_risk":
        threshold = max(threshold, _HIGH_RISK_OVERWHELMING_GAP)
        if plan.source == "uniform_fallback":
            return _unresolved(stage, domain, claims, conflict_type, rule, "高风险对立缺少 L1 能力证据，均匀回退不得按数量消解。", plan)
        if gap < threshold:
            return _unresolved(stage, domain, claims, conflict_type, rule, "高风险对立未达到压倒性证据门槛，保留双方并提示风险。", plan)
    elif gap < threshold:
        return _unresolved(stage, domain, claims, conflict_type, rule, "能力权重差未达到显式规则门槛，保留双方观点。", plan)
    winners = [item for item in claims if _side(item, conflict_type) == winning_side]
    return _resolved(stage, domain, claims, winners, conflict_type, rule, plan, f"显式规则 {rule.rule_id} 以 {rule.resolution_strategy} 消解；差值 {gap:.3f}。")


def _decide_group(
    stage: Stage,
    domain: str,
    claims: Sequence[Claim],
    plan: ApplicabilityPlan,
    rules: ConflictRuleSet,
    structure_decision: StageDecision | None = None,
) -> StageDecision:
    active = [item for item in claims if item.confidence > _REJECT_THRESHOLD]
    rejected = tuple(item.claim_id for item in claims if item.confidence <= _REJECT_THRESHOLD)
    first = claims[0]
    if not active:
        return StageDecision(stage, domain, "reject_all", task_id=first.task_id, target_id=first.target_id, rejected_claim_ids=rejected, rationale="该任务命题均未达到最低可信门槛。")
    conflict_type = detect_opposition(active)
    if conflict_type != "none":
        rule = rules.match(stage, conflict_type, active, domain)
        if rule is None:
            decision = _unresolved(stage, domain, active, conflict_type, None, "检测到直接对立但无显式消解规则，保留双方。", plan)
        else:
            decision = _resolve_conflict(stage, domain, active, conflict_type, rule, plan, structure_decision)
        return StageDecision(**{**decision.__dict__, "rejected_claim_ids": rejected})
    if len(active) == 1:
        claim = active[0]
        side = claim.polarity if claim.polarity != "neutral" else claim.stance
        rationale = f"结构方向={side}；该领域仅有一条有效命题。" if stage == "structure" else "该领域仅有一条有效命题。"
        return StageDecision(
            stage, domain, "winner", task_id=claim.task_id, target_id=claim.target_id, winner_side=side,
            winner_claim_ids=(claim.claim_id,), rejected_claim_ids=rejected,
            weighted_support=round(plan.school_weight(claim.school_id, claim.task_id), 6), rationale=rationale,
        )
    return StageDecision(
        stage, domain, "coexist", task_id=first.task_id, target_id=first.target_id,
        winner_claim_ids=tuple(item.claim_id for item in active), rejected_claim_ids=rejected,
        weighted_support=round(sum(plan.school_weight(item.school_id, item.task_id) for item in active), 6),
        rationale="多条命题未构成结构化对立，允许并存。",
    )


def _summary(stage: Stage, decisions: Sequence[StageDecision]) -> StageDecision:
    if not decisions:
        return StageDecision.empty(stage)
    if len(decisions) == 1:
        leaf = decisions[0]
        return StageDecision(**{**leaf.__dict__, "domain_decisions": (leaf,)})
    if all(item.result == "reject_all" for item in decisions):
        result: DecisionResult = "reject_all"
    elif any(item.result == "unresolved" for item in decisions):
        result = "unresolved"
    elif any(item.result == "conflict_resolved" for item in decisions):
        result = "conflict_resolved"
    else:
        result = "coexist"
    # 摘要节点不是一次显式规则命中；多任务/多领域下不能伪造规则 ID。
    if result == "conflict_resolved" and len(decisions) > 1:
        result = "coexist"
    return StageDecision(
        stage, "多领域", result,
        winner_claim_ids=tuple(value for item in decisions for value in item.winner_claim_ids),
        minority_claim_ids=tuple(value for item in decisions for value in item.minority_claim_ids),
        rejected_claim_ids=tuple(value for item in decisions for value in item.rejected_claim_ids),
        conflict_type=next((item.conflict_type for item in decisions if item.conflict_type != "none"), "none"),
        resolution_rule_id=None,
        weighted_support=round(sum(item.weighted_support for item in decisions), 6),
        weighted_oppose=round(sum(item.weighted_oppose for item in decisions), 6),
        rationale="该段按领域独立裁决；逐域规则与理由保留在 domain_decisions。",
        domain_decisions=tuple(decisions),
    )


def _reject_downstream_for_structure(structure: StageDecision, downstream: StageDecision) -> StageDecision:
    if structure.result != "reject_all" or not structure.rejected_claim_ids or downstream.result == "reject_all":
        return downstream
    return StageDecision(
        downstream.stage, downstream.domain, "reject_all", task_id=downstream.task_id, target_id=downstream.target_id,
        rejected_claim_ids=tuple(dict.fromkeys(downstream.winner_claim_ids + downstream.minority_claim_ids + downstream.rejected_claim_ids)),
        conflict_type=downstream.conflict_type, resolution_rule_id=downstream.resolution_rule_id,
        weighted_support=downstream.weighted_support, weighted_oppose=downstream.weighted_oppose,
        rationale="同领域结构段全部否决，下游命题受结构优先级约束。",
    )


def arbitrate_staged(
    case_id: str,
    claims: Sequence[Claim],
    applicability: Any | None,
    *,
    conflict_rules: ConflictRuleSet,
) -> StagedArbitrationResult:
    """按 claim_type 分三段、按 domain 独立裁决；旧 L6 入口保持不变。"""

    plan = _coerce_plan(applicability, claims)
    segmented: dict[Stage, list[Claim]] = {stage: [] for stage in _STAGES}
    for claim in claims:
        stage = _CLAIM_STAGE.get(claim.claim_type)
        if stage is not None:
            segmented[stage].append(claim)

    grouped: dict[Stage, dict[tuple[str, str], list[Claim]]] = {stage: {} for stage in _STAGES}
    for stage, stage_claims in segmented.items():
        for claim in stage_claims:
            grouped[stage].setdefault((claim.domain, claim.task_id, claim.target_id), []).append(claim)

    structure_leaves = [
        _decide_group("structure", domain, group, plan, conflict_rules)
        for (domain, _task_id, _target_id), group in sorted(grouped["structure"].items())
    ]
    structure_by_target = {(item.domain, item.target_id): item for item in structure_leaves}

    downstream: dict[Stage, list[StageDecision]] = {"event": [], "timing": []}
    for stage in ("event", "timing"):
        for (domain, _task_id, _target_id), group in sorted(grouped[stage].items()):
            structure_decision = structure_by_target.get((domain, group[0].target_id))
            decision = _decide_group(stage, domain, group, plan, conflict_rules, structure_decision)
            if structure_decision is not None:
                decision = _reject_downstream_for_structure(structure_decision, decision)
            downstream[stage].append(decision)

    return StagedArbitrationResult(
        case_id,
        (_summary("structure", structure_leaves), _summary("event", downstream["event"]), _summary("timing", downstream["timing"])),
        plan.source,
    )
