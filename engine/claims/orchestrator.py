"""L2 命题编排：命盘事实 → 候选结构命题，并兼容既有盲测适配。"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from engine.claims.blind_adapter import claim_to_blind_output
from engine.claims.domain import Claim, TaskUnsupported
from engine.claims.runner_registry import DEFAULT_RUNNER_REGISTRY, RunnerRegistry
from engine.decision.models import ChartFactLedger
from engine.decision.l6_staged_arbitration import (
    ConflictRuleSet,
    StagedArbitrationResult,
    arbitrate_staged,
)
from engine.decision.adjudication_protocol import AdjudicationUnit
from engine.evaluation.freeze import freeze_outputs
from engine.evaluation.models import BlindSchoolOutput, BlindTask, FrozenBlindRun
from engine.features import build_chart_feature_vector


@dataclass(frozen=True)
class ClaimCandidateSet:
    """保留单个学派、任务的全部候选；候选顺序不代表裁决或优先级。"""

    case_id: str
    school_id: str
    task_id: str
    state: str
    claims: tuple[Claim, ...]
    rationale: str

    def __post_init__(self) -> None:
        for name in ("case_id", "school_id", "task_id", "rationale"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        if self.state not in {"candidates", "abstain", "unsupported"}:
            raise ValueError("state must be candidates, abstain, or unsupported")
        object.__setattr__(self, "claims", tuple(self.claims))
        if (self.state == "candidates") != bool(self.claims):
            raise ValueError("only candidates state must contain claims")
        seen_ids: set[str] = set()
        for claim in self.claims:
            if claim.school_id != self.school_id or claim.task_id != self.task_id:
                raise ValueError(
                    f"claim {claim.claim_id} school_id/task_id must match requested "
                    f"{self.school_id}/{self.task_id}; got {claim.school_id}/{claim.task_id}"
                )
            if claim.claim_id in seen_ids:
                raise ValueError(f"duplicate claim_id: {claim.claim_id}")
            seen_ids.add(claim.claim_id)


ChartAdjudicationState = Literal[
    "primary", "partial", "unresolved", "abstain", "unsupported",
]

_DEFAULT_CHART_CONFLICT_RULES = (
    Path(__file__).resolve().parents[2] / "engine" / "decision" / "conflict-rules.yaml"
)


@dataclass(frozen=True)
class ChartAdjudication:
    """只对原局结构命题做候选裁决，不生成现实结果标签。"""

    case_id: str
    task_id: str
    chart: ChartFactLedger
    candidate_sets: tuple[ClaimCandidateSet, ...]
    state: ChartAdjudicationState
    primary_claim: Claim | None
    rationale: str
    primary_claims: tuple[Claim, ...] = ()
    arbitration: StagedArbitrationResult | None = None
    units: tuple[AdjudicationUnit, ...] = ()

    def __post_init__(self) -> None:
        for name in ("case_id", "task_id", "rationale"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        object.__setattr__(self, "candidate_sets", tuple(self.candidate_sets))
        if self.state not in {"primary", "partial", "unresolved", "abstain", "unsupported"}:
            raise ValueError(f"invalid chart adjudication state: {self.state}")
        object.__setattr__(self, "primary_claims", tuple(self.primary_claims))
        object.__setattr__(self, "units", tuple(self.units))
        if self.primary_claim is not None and not self.primary_claims:
            object.__setattr__(self, "primary_claims", (self.primary_claim,))
        if self.primary_claim is not None and self.primary_claims != (self.primary_claim,):
            raise ValueError("primary_claim must be the only item in primary_claims")
        if self.state in {"primary", "partial"} and not self.primary_claims:
            raise ValueError(f"{self.state} state requires primary_claims")
        if self.state in {"unresolved", "abstain", "unsupported"} and self.primary_claims:
            raise ValueError(f"{self.state} state cannot contain primary_claims")
        claims = tuple(
            claim
            for candidate_set in self.candidate_sets
            for claim in candidate_set.claims
        )
        if any(candidate_set.task_id != self.task_id for candidate_set in self.candidate_sets):
            raise ValueError("all candidate sets must match task_id")
        claim_ids = {claim.claim_id for claim in claims}
        if any(claim.claim_id not in claim_ids for claim in self.primary_claims):
            raise ValueError("primary_claims must be retained in candidate_sets")
        if self.state == "unresolved" and len(claims) < 2:
            raise ValueError("unresolved state requires competing claims")

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "task_id": self.task_id,
            "chart": self.chart.to_dict(),
            "candidate_sets": [
                {
                    "case_id": item.case_id,
                    "school_id": item.school_id,
                    "task_id": item.task_id,
                    "state": item.state,
                    "claims": [claim.to_dict() for claim in item.claims],
                    "rationale": item.rationale,
                }
                for item in self.candidate_sets
            ],
            "state": self.state,
            "primary_claim": self.primary_claim.to_dict() if self.primary_claim else None,
            "primary_claims": [claim.to_dict() for claim in self.primary_claims],
            "arbitration": self.arbitration.to_dict() if self.arbitration else None,
            "units": [item.to_dict() for item in self.units],
            "rationale": self.rationale,
        }


def chart_ledger_from_mapping(chart: dict[str, Any]) -> ChartFactLedger:
    """把 v5 chart DTO 确定性规范为 L0 事实账本。"""
    pillars_raw = chart.get("pillars") or chart.get("four_pillars") or {}
    if isinstance(pillars_raw, (list, tuple)):
        pillars = {key: str(value) for key, value in zip(("year", "month", "day", "hour"), pillars_raw)}
    elif isinstance(pillars_raw, dict):
        pillars = {str(key): str(value) for key, value in pillars_raw.items()}
    else:
        pillars = {}
    dayun_raw = chart.get("dayun_steps") or []
    liunian_raw = chart.get("liunian_steps") or []
    return ChartFactLedger(
        sex_marker=str(chart.get("gender_marker") or chart.get("sex_marker") or chart.get("sex") or ""),
        solar_datetime=str(chart.get("solar_datetime") or ""),
        four_pillars=pillars,
        start_luck=str(chart.get("start_luck") or ""),
        dayun_steps=[dict(item) for item in dayun_raw if isinstance(item, dict)] if isinstance(dayun_raw, (list, tuple)) else [],
        liunian_steps=[dict(item) for item in liunian_raw if isinstance(item, dict)] if isinstance(liunian_raw, (list, tuple)) else [],
        missing_fields=[str(item) for item in chart.get("missing_fields", [])] if isinstance(chart.get("missing_fields", []), (list, tuple)) else [],
    )


def _missing_required_fields(chart: ChartFactLedger, task: BlindTask) -> tuple[str, ...]:
    missing: list[str] = []
    for field in task.required_input_fields:
        if field == "four_pillars":
            values = tuple(chart.four_pillars.values())
            present = bool(values) and all(str(value).strip() not in {"", "_"} for value in values)
        else:
            value = getattr(chart, field, None)
            present = bool(str(value).strip()) if isinstance(value, str) else value is not None
        if not present:
            missing.append(field)
    return tuple(missing)


def _state_output(
    *,
    case_id: str,
    school: str,
    task: BlindTask,
    state: str,
    rationale: str,
) -> BlindSchoolOutput:
    return BlindSchoolOutput(
        case_id=case_id,
        school_id=school,
        task_id=task.task_id,
        state=state,  # type: ignore[arg-type]
        rationale=rationale,
    )


def generate_claim_candidates(
    chart: ChartFactLedger | dict[str, Any],
    tasks: Sequence[BlindTask],
    *,
    case_id: str,
    schools: Sequence[str] = ("ziping", "ren"),
    registry: RunnerRegistry = DEFAULT_RUNNER_REGISTRY,
) -> list[ClaimCandidateSet]:
    """运行现有 L2 生成器并保留全部候选；稳定 ID 排序仅用于展示。"""
    ordered_tasks = sorted(tasks, key=lambda item: item.task_id)
    seen_task_ids: set[str] = set()
    for task in ordered_tasks:
        if task.task_id in seen_task_ids:
            raise ValueError(f"duplicate task_id: {task.task_id}")
        seen_task_ids.add(task.task_id)

    ledger = chart if isinstance(chart, ChartFactLedger) else chart_ledger_from_mapping(chart)
    try:
        features = build_chart_feature_vector(ledger)
    except (TypeError, ValueError) as exc:
        features = None
        feature_error = str(exc)
    else:
        feature_error = ""

    rows: list[ClaimCandidateSet] = []
    seen_claim_ids: set[str] = set()
    for school in sorted(set(schools)):
        for task in ordered_tasks:
            generator = registry.resolve(school, task.task_id)
            if generator is None:
                rows.append(ClaimCandidateSet(
                    case_id=case_id, school_id=school, task_id=task.task_id,
                    state="unsupported", claims=(),
                    rationale="no independent L2 claim generator is registered for this school",
                ))
                continue
            missing_required = _missing_required_fields(ledger, task)
            if missing_required:
                rows.append(ClaimCandidateSet(
                    case_id=case_id, school_id=school, task_id=task.task_id,
                    state="abstain", claims=(),
                    rationale=f"missing required chart facts: {', '.join(missing_required)}",
                ))
                continue
            if features is None:
                rows.append(ClaimCandidateSet(
                    case_id=case_id, school_id=school, task_id=task.task_id,
                    state="abstain", claims=(),
                    rationale=f"chart facts are insufficient to build cfv-v1: {feature_error}",
                ))
                continue
            try:
                claims = generator(ledger, features, task)
            except TaskUnsupported as exc:
                rows.append(ClaimCandidateSet(
                    case_id=case_id, school_id=school, task_id=task.task_id,
                    state="unsupported", claims=(), rationale=str(exc),
                ))
                continue
            if not claims:
                rows.append(ClaimCandidateSet(
                    case_id=case_id, school_id=school, task_id=task.task_id,
                    state="abstain", claims=(),
                    rationale="runner covers this task but chart facts do not satisfy a production trigger",
                ))
                continue
            ordered_claims = tuple(sorted(claims, key=lambda claim: claim.claim_id))
            candidate_set = ClaimCandidateSet(
                case_id=case_id, school_id=school, task_id=task.task_id,
                state="candidates", claims=ordered_claims,
                rationale=(
                    f"unresolved competition among candidates for the same task {task.task_id}; "
                    f"candidate IDs: {', '.join(claim.claim_id for claim in ordered_claims)}"
                    if len(ordered_claims) > 1 else ordered_claims[0].confidence_basis
                ),
            )
            for claim in candidate_set.claims:
                if claim.claim_id in seen_claim_ids:
                    raise ValueError(f"duplicate claim_id: {claim.claim_id}")
                seen_claim_ids.add(claim.claim_id)
            rows.append(candidate_set)
    return rows


def generate_chart_adjudication(
    chart: ChartFactLedger | dict[str, Any],
    task: BlindTask,
    *,
    case_id: str,
    schools: Sequence[str] = ("ziping", "ditiansui"),
    registry: RunnerRegistry = DEFAULT_RUNNER_REGISTRY,
    conflict_rules: ConflictRuleSet | None = None,
) -> ChartAdjudication:
    """从 L0 命盘事实生成结构候选，并按目标单位完成显式裁决。

    该入口只处理 ``structure.overview``。它保留每个已注册学派的完整
    Claim 集合，不使用置信度、规则数量、学派数量或 claim_id 选择 winner。
    不同目标的结构命题可以并存；同一目标竞争未解时返回 ``unresolved``
    或 ``partial``。这里的主断只属于结构层，不是现实 outcome，也不表示
    理论已经通过现实验证。
    """
    if task.task_id != "structure.overview":
        raise ValueError("chart adjudication only accepts structure.overview")
    if task.claim_type not in {"structure", "structure_claim"}:
        raise ValueError("chart adjudication requires a structure task")
    if not schools:
        raise ValueError("chart adjudication requires at least one school")

    ledger = chart if isinstance(chart, ChartFactLedger) else chart_ledger_from_mapping(chart)
    candidate_sets = tuple(
        generate_claim_candidates(
            ledger,
            [task],
            case_id=case_id,
            schools=schools,
            registry=registry,
        )
    )
    claims = tuple(
        claim
        for candidate_set in candidate_sets
        for claim in candidate_set.claims
    )
    if claims:
        rules = conflict_rules or ConflictRuleSet.from_yaml(_DEFAULT_CHART_CONFLICT_RULES)
        arbitration = arbitrate_staged(
            case_id,
            claims,
            None,
            conflict_rules=rules,
        )
        structure = arbitration.stage("structure")
        leaves = structure.domain_decisions or (structure,)
        units = tuple(
            AdjudicationUnit.from_stage_decision(leaf, claims)
            for leaf in leaves
            if leaf.task_id or leaf.target_id
        )
        primary_ids = tuple(
            claim_id
            for leaf in leaves
            if leaf.result in {"winner", "coexist", "conflict_resolved"}
            for claim_id in leaf.winner_claim_ids
        )
        claim_by_id = {claim.claim_id: claim for claim in claims}
        primary_claims = tuple(
            claim_by_id[claim_id]
            for claim_id in dict.fromkeys(primary_ids)
        )
        has_unresolved = any(leaf.result == "unresolved" for leaf in leaves)
        unresolved_ids = tuple(
            claim_id
            for leaf in leaves
            if leaf.result == "unresolved"
            for claim_id in leaf.minority_claim_ids
        )
        if has_unresolved and primary_claims:
            state = "partial"
            primary_claim = None
            rationale = (
                "部分结构目标已形成主断，但仍有同目标竞争未解决；分别保留。"
                f"未决命题：{', '.join(unresolved_ids)}"
            )
        elif has_unresolved:
            state = "unresolved"
            primary_claim = None
            rationale = (
                structure.rationale or "同目标结构竞争未解决；不选择人工 winner。"
            ) + (f"未决命题：{', '.join(unresolved_ids)}" if unresolved_ids else "")
        elif primary_claims:
            state = "primary"
            primary_claim = primary_claims[0] if len(primary_claims) == 1 else None
            rationale = "各结构目标均完成显式裁决；不同目标命题允许并存。"
        else:
            state = "abstain"
            primary_claim = None
            rationale = "结构命题经过裁决后没有可输出的主断。"
    elif candidate_sets and all(item.state == "unsupported" for item in candidate_sets):
        state = "unsupported"
        primary_claim = None
        primary_claims = ()
        arbitration = None
        units = ()
        rationale = "no requested school has an independent structure.overview generator"
    else:
        state = "abstain"
        primary_claim = None
        primary_claims = ()
        arbitration = None
        units = ()
        rationale = "no structure claim satisfied the current chart facts and runner conditions"

    return ChartAdjudication(
        case_id=case_id,
        task_id=task.task_id,
        chart=ledger,
        candidate_sets=candidate_sets,
        state=state,
        primary_claim=primary_claim,
        rationale=rationale,
        primary_claims=primary_claims,
        arbitration=arbitration,
        units=units,
    )


def generate_blind_outputs(
    chart: ChartFactLedger | dict[str, Any],
    tasks: Sequence[BlindTask],
    *,
    case_id: str,
    schools: Sequence[str] = ("ziping", "ren"),
    registry: RunnerRegistry = DEFAULT_RUNNER_REGISTRY,
) -> list[BlindSchoolOutput]:
    """兼容盲测入口：只有单候选进入 adapter，同任务未决竞争一律弃断。"""
    candidate_sets = generate_claim_candidates(
        chart, tasks, case_id=case_id, schools=schools, registry=registry,
    )
    tasks_by_id = {task.task_id: task for task in tasks}
    rows: list[BlindSchoolOutput] = []
    for candidate_set in candidate_sets:
        task = tasks_by_id[candidate_set.task_id]
        if candidate_set.state == "candidates" and len(candidate_set.claims) == 1:
            rows.append(claim_to_blind_output(candidate_set.claims[0], case_id=case_id, task=task))
        else:
            rows.append(_state_output(
                case_id=candidate_set.case_id, school=candidate_set.school_id, task=task,
                state="abstain" if candidate_set.state == "candidates" else candidate_set.state,
                rationale=candidate_set.rationale,
            ))
    return rows


def generate_frozen_claim_run(
    chart: ChartFactLedger | dict[str, Any],
    tasks: Sequence[BlindTask],
    *,
    case_id: str,
    task_catalog_version: str,
    rule_snapshot_id: str,
    schools: Sequence[str] = ("ziping", "ren"),
    registry: RunnerRegistry = DEFAULT_RUNNER_REGISTRY,
    frozen_at: str | None = None,
) -> FrozenBlindRun:
    """从命盘事实直接生成并冻结盲测输出，形成 03 可消费的标准制品。"""
    outputs = generate_blind_outputs(
        chart,
        tasks,
        case_id=case_id,
        schools=schools,
        registry=registry,
    )
    return freeze_outputs(
        outputs,
        task_catalog_version,
        rule_snapshot_id,
        frozen_at=frozen_at,
    )
