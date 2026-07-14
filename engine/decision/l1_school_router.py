"""L1 流派适用性路由最小实现。

先决定哪些流派有资格发言；不产生命题、不裁判。
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal, Mapping, Sequence, overload

from engine.decision.capability_registry import CapabilityRegistry, CapabilityQuery
from engine.decision.chart_prototype import PrototypeAssignment, classify_prototype
from engine.decision.models import ChartFactLedger, ContextFactLedger, SchoolApplicability
from engine.evaluation.models import BlindTask
from engine.features.types import ChartFeatureVector

_ROLE_LADDER = ("lead", "co_lead", "evidence_only", "abstain")
_PRIOR_MIN_SAMPLE = 5
_PRIOR_LOW_HIT_RATE = 0.35
_PRIOR_SCORE_PENALTY = 0.2
_DEFAULT_SCHOOLS = ("ziping", "ditiansui", "duan_jianye", "yang_qingjuan", "ren_fuhong", "gao_dechen")
_PRODUCTION_EVIDENCE_GRADES = frozenset({"E2", "E3", "E4"})


@dataclass(frozen=True)
class RoutingRiskConfig:
    schools: tuple[str, ...] = _DEFAULT_SCHOOLS
    risk_factor: float = 0.45
    minimum_route_score: float = 0.35
    minimum_n_eff: float = 5.0
    minimum_evidence_grades: frozenset[str] = _PRODUCTION_EVIDENCE_GRADES
    high_risk_minimum_grade: str = "E3"
    max_primary_schools: int = 2

    def __post_init__(self) -> None:
        object.__setattr__(self, "schools", tuple(self.schools))
        object.__setattr__(self, "minimum_evidence_grades", frozenset(self.minimum_evidence_grades))
        if not self.schools:
            raise ValueError("RoutingRiskConfig.schools cannot be empty")
        if self.risk_factor < 0 or not 1 <= self.max_primary_schools <= 2:
            raise ValueError("invalid routing risk configuration")


@dataclass(frozen=True)
class TaskRoute:
    task_id: str
    primary_schools: tuple[str, ...]
    counter_school: str | None
    abstain_candidates: tuple[str, ...]
    unsupported_schools: tuple[str, ...]
    evidence_status: Literal["sufficient", "insufficient"]
    rationale: str
    school_scores: Mapping[str, float] = field(default_factory=dict)
    capability_queries: Mapping[str, CapabilityQuery] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "school_scores", MappingProxyType(dict(self.school_scores)))
        object.__setattr__(self, "capability_queries", MappingProxyType(dict(self.capability_queries)))


@dataclass(frozen=True)
class RoutePlan:
    primary_schools: tuple[str, ...]
    counter_school: str | None
    abstain_candidates: tuple[str, ...]
    unsupported_schools: tuple[str, ...]
    route_rationale: str
    capability_snapshot_id: str
    prototype_assignment: PrototypeAssignment
    per_task_routes: Mapping[str, TaskRoute]

    def __post_init__(self) -> None:
        object.__setattr__(self, "per_task_routes", MappingProxyType(dict(self.per_task_routes)))


def _downgrade_role(role: str) -> str:
    try:
        idx = _ROLE_LADDER.index(role)
    except ValueError:
        return role
    return _ROLE_LADDER[min(idx + 1, len(_ROLE_LADDER) - 1)]


def _apply_learned_prior(
    school: str,
    role: str,
    score: float,
    learned_prior: dict[str, tuple[float, int]] | None,
) -> tuple[str, float, list[str]]:
    if not learned_prior or school not in learned_prior:
        return role, score, []
    hit_rate, sample_n = learned_prior[school]
    if sample_n < _PRIOR_MIN_SAMPLE or hit_rate >= _PRIOR_LOW_HIT_RATE:
        return role, score, []
    return (
        _downgrade_role(role),
        max(0.0, round(score - _PRIOR_SCORE_PENALTY, 3)),
        [f"学习先验：该派历史命中率 {hit_rate}（样本 {sample_n}）偏低，下调路由角色。"],
    )


def _chart_signals(chart: ChartFactLedger) -> dict[str, object]:
    """只从 four_pillars 派生结构信号。"""

    from engine.predicates.ganzhi import gan_to_wuxing, is_gan, is_zhi, zhi_to_wuxing
    from engine.predicates.relations import zhi_chong

    gans: list[str] = []
    zhis: list[str] = []
    for value in chart.four_pillars.values():
        text = (value or "").strip()
        if len(text) >= 2 and is_gan(text[0]) and is_zhi(text[1]):
            gans.append(text[0])
            zhis.append(text[1])

    elements = [gan_to_wuxing(g) for g in gans] + [zhi_to_wuxing(z) for z in zhis]
    distribution = Counter(elements)
    missing_count = len({"木", "火", "土", "金", "水"} - set(distribution))
    total = len(elements)
    dominant = max(distribution.values()) if distribution else 0

    return {
        "complete": len(gans) == 4,
        "skewed": bool(total and (dominant / total >= 0.5 or missing_count >= 2)),
        "missing_count": missing_count,
        "has_chong": any(zhi_chong(zhis[i], zhis[j]) for i in range(len(zhis)) for j in range(i + 1, len(zhis))),
    }


SCHOOL_PROFILES: dict[str, dict[str, object]] = {
    "ziping": {
        "domains": ["事业", "财富", "学业", "总体"],
        "reason": "子平类适合格局、旺衰、用忌与结构层级审查。",
    },
    "ditiansui": {
        "domains": ["总体", "事业", "健康"],
        "reason": "滴天髓类适合气势、寒暖燥湿、调候与全局气机。",
    },
    "duan_jianye": {
        "domains": ["事业", "财富"],
        "reason": "段建业适合做功路径、体用宾主与财富事业落地。",
    },
    "yang_qingjuan": {
        "domains": ["婚姻", "家庭", "性格"],
        "reason": "杨清娟适合婚姻、人物画像、暗合与取象细节。",
    },
    "ren_fuhong": {
        "domains": ["应期", "事业", "婚姻", "健康"],
        "reason": "任付红适合岁运触发、时间窗与应期验证。",
    },
    "gao_dechen": {
        "domains": ["健康", "灾厄", "学业", "总体"],
        "reason": "高德臣适合神煞、健康灾厄、学业子女与旁证补强。",
    },
}


def _focus_domains(context: ContextFactLedger) -> set[str]:
    text = f"{context.analysis_focus_text}\n{context.known_fact_text}"
    domains = {domain for domain in ("学业", "事业", "财富", "婚姻", "健康", "性格") if domain in text}
    if any(token in text for token in ("工作", "职业", "升迁", "岗位")):
        domains.add("事业")
    if any(token in text for token in ("钱", "收入", "资产", "破财")):
        domains.add("财富")
    if any(token in text for token in ("结婚", "离婚", "配偶", "感情")):
        domains.add("婚姻")
    if any(token in text for token in ("身体", "疾病", "生病", "病灾")):
        domains.add("健康")
    return domains


def _static_route_schools(
    chart: ChartFactLedger,
    context: ContextFactLedger,
    *,
    learned_prior: dict[str, tuple[float, int]] | None = None,
) -> list[SchoolApplicability]:
    """生成兼容的静态 L1 SchoolApplicabilityMatrix。"""

    focus = _focus_domains(context)
    has_four = len([v for v in chart.four_pillars.values() if v and v != "_"]) == 4
    has_dayun = bool(chart.dayun_steps)
    signals = _chart_signals(chart)
    result: list[SchoolApplicability] = []

    for school, profile in SCHOOL_PROFILES.items():
        domains = [str(item) for item in profile["domains"]]  # type: ignore[index]
        overlap = focus.intersection(domains)
        reasons = [str(profile["reason"])]
        blockers: list[str] = []
        score = 0.55 + 0.1 * min(2, len(overlap))
        role = "co_lead"

        if school in {"ziping", "ditiansui"}:
            role = "lead" if has_four else "evidence_only"
        if school == "ren_fuhong" and not has_dayun:
            role = "evidence_only"
            blockers.append("缺少大运 / 流年节点，不能单独主审应期。")
            score -= 0.2
        if school == "gao_dechen":
            role = "evidence_only"
            reasons.append("神煞与旁证不能孤证主审大结论。")
        if signals["skewed"] and school == "ditiansui":
            score += 0.1
            reasons.append("五行偏枯或缺行明显，调候气势派更适用。")
        if signals["has_chong"] and signals["complete"] and school in {"duan_jianye", "ren_fuhong"}:
            score += 0.05
            if role == "co_lead":
                role = "lead"
            reasons.append("地支见冲，做功 / 应期派可主审事件触发。")
        if focus and not overlap and school not in {"ziping", "ditiansui"}:
            role = "abstain"
            blockers.append("当前分析焦点与该派初始适用域无交集。")
            score = 0.2

        if not has_four:
            if role != "abstain":
                role = "evidence_only"
            blockers.append("四柱事实不完整，所有上层判断只能降级。")
            score = min(score, 0.35)

        role, score, prior_reasons = _apply_learned_prior(school, role, score, learned_prior)
        reasons += prior_reasons

        result.append(
            SchoolApplicability(
                school=school,
                role=role,  # type: ignore[arg-type]
                applicable_domains=domains,
                applicability_score=round(max(0.0, min(1.0, score)), 3),
                reasons=reasons,
                blockers=blockers,
                confidence=0.55 if not blockers else 0.4,
                falsifier="若该派在相同命盘结构、领域、事件类型中连续失验，则下调路由角色。",
            )
        )
    return result


def _task_horizon(task: BlindTask) -> str:
    horizons = tuple(task.allowed_time_horizons)
    return str(horizons[0]) if horizons else "unspecified"


def _grade_rank(grade: str) -> int:
    normalized = grade.upper()
    if normalized.startswith("E") and normalized[1:].isdigit():
        return int(normalized[1:])
    # 历史盲测 artifact 使用 A/B 等级；B 对齐 E2，仅作为历史盲测证据。
    return {"A": 3, "B": 2, "C": 1}.get(normalized, 0)


def _is_supported(query: CapabilityQuery, task: BlindTask, risk: RoutingRiskConfig) -> bool:
    if query.shrink_level == "global_prior" or query.n_eff < risk.minimum_n_eff:
        return False
    grade_ok = query.evidence_grade in risk.minimum_evidence_grades or _grade_rank(query.evidence_grade) >= 2
    if task.high_risk:
        grade_ok = _grade_rank(query.evidence_grade) >= _grade_rank(risk.high_risk_minimum_grade)
    return grade_ok and query.coverage_rate > 0.0


def _route_score(query: CapabilityQuery, risk: RoutingRiskConfig) -> float:
    uncertainty = query.credible_interval[1] - query.credible_interval[0]
    # 增量价值用于判断反证/互补角色；主力排序保持“能力效用 - 不确定性惩罚”，
    # 避免高 complementarity 的反证派反客为主。
    return round(query.posterior_mean - risk.risk_factor * uncertainty, 6)


def _build_task_route(
    task: BlindTask,
    assignment: PrototypeAssignment,
    completeness: str,
    registry: CapabilityRegistry,
    risk: RoutingRiskConfig,
) -> TaskRoute:
    queries: dict[str, CapabilityQuery] = {}
    scores: dict[str, float] = {}
    unsupported: list[str] = []
    abstain: list[str] = []
    for school in risk.schools:
        query = registry.query(
            school_id=school,
            task_id=task.task_id,
            chart_prototype_id=assignment.prototype_id,
            claim_type=task.claim_type,
            time_horizon=_task_horizon(task),
            evidence_completeness_band=completeness,
        )
        queries[school] = query
        scores[school] = _route_score(query, risk)
        if query.shrink_level == "global_prior":
            unsupported.append(school)
        elif not _is_supported(query, task, risk) or scores[school] < risk.minimum_route_score:
            abstain.append(school)

    eligible = [school for school in risk.schools if school not in unsupported and school not in abstain]
    eligible.sort(key=lambda school: (-scores[school], school))
    if not eligible:
        return TaskRoute(
            task_id=task.task_id,
            primary_schools=(),
            counter_school=None,
            abstain_candidates=tuple(abstain),
            unsupported_schools=tuple(unsupported),
            evidence_status="insufficient",
            rationale="证据不足：没有流派达到该任务的最小能力证据与不确定性门槛。",
            school_scores=scores,
            capability_queries=queries,
        )

    primary_count = min(risk.max_primary_schools, len(eligible))
    primary: list[str] = [eligible[0]]
    if primary_count > 1 and len(eligible) > 1 and scores[eligible[1]] >= scores[eligible[0]] - 0.08:
        primary.append(eligible[1])
    counter_candidates = [school for school in eligible if school not in primary and queries[school].incremental_gain > 0.0]
    counter = max(counter_candidates, key=lambda school: (queries[school].incremental_gain, scores[school], school), default=None)
    rationale = (
        f"原型 {assignment.prototype_id}；按 expected_utility - risk×uncertainty + complementarity_gain 排序，"
        f"主力为 {', '.join(primary)}" + (f"，反证为 {counter}。" if counter else "。")
    )
    return TaskRoute(
        task_id=task.task_id,
        primary_schools=tuple(primary),
        counter_school=counter,
        abstain_candidates=tuple(abstain),
        unsupported_schools=tuple(unsupported),
        evidence_status="sufficient",
        rationale=rationale,
        school_scores=scores,
        capability_queries=queries,
    )


def build_route_plan(
    *,
    feature_vector: ChartFeatureVector,
    tasks: Sequence[BlindTask],
    evidence_completeness_band: str,
    registry: CapabilityRegistry,
    risk_config: RoutingRiskConfig,
) -> RoutePlan:
    """以条件化能力后验生成每任务独立、可追溯的 L1 路由计划。"""
    if not tasks:
        raise ValueError("tasks cannot be empty")
    assignment = classify_prototype(feature_vector)
    routes = {
        task.task_id: _build_task_route(task, assignment, evidence_completeness_band, registry, risk_config)
        for task in tasks
    }
    primary = tuple(dict.fromkeys(school for route in routes.values() for school in route.primary_schools))[:2]
    counter = next((route.counter_school for route in routes.values() if route.counter_school), None)
    abstain = tuple(dict.fromkeys(school for route in routes.values() for school in route.abstain_candidates))
    unsupported = tuple(dict.fromkeys(school for route in routes.values() for school in route.unsupported_schools))
    status_count = sum(route.evidence_status == "sufficient" for route in routes.values())
    rationale = (
        f"命盘映射为 {assignment.prototype_id}（置信 {assignment.confidence:.3f}）；"
        f"能力快照 {registry.snapshot_id}；{status_count}/{len(routes)} 个任务达到证据门槛。"
    )
    return RoutePlan(primary, counter, abstain, unsupported, rationale, registry.snapshot_id, assignment, routes)


@overload
def route_schools(
    chart: ChartFactLedger,
    context: ContextFactLedger,
    *,
    learned_prior: dict[str, tuple[float, int]] | None = None,
    routing_mode: Literal["static"] = "static",
    tasks: Sequence[BlindTask] | None = None,
    registry: CapabilityRegistry | None = None,
    risk_config: RoutingRiskConfig | None = None,
) -> list[SchoolApplicability]: ...


@overload
def route_schools(
    chart: ChartFactLedger,
    context: ContextFactLedger,
    *,
    learned_prior: dict[str, tuple[float, int]] | None = None,
    routing_mode: Literal["learned"],
    tasks: Sequence[BlindTask],
    registry: CapabilityRegistry,
    risk_config: RoutingRiskConfig | None = None,
) -> RoutePlan: ...


def route_schools(
    chart: ChartFactLedger,
    context: ContextFactLedger,
    *,
    learned_prior: dict[str, tuple[float, int]] | None = None,
    routing_mode: Literal["static", "learned"] = "static",
    tasks: Sequence[BlindTask] | None = None,
    registry: CapabilityRegistry | None = None,
    risk_config: RoutingRiskConfig | None = None,
) -> list[SchoolApplicability] | RoutePlan:
    """并行路由入口；默认静态，learned 必须显式注入冻结能力快照。"""
    if routing_mode == "static":
        return _static_route_schools(chart, context, learned_prior=learned_prior)
    if routing_mode != "learned":
        raise ValueError("routing_mode must be static or learned")
    if registry is None or not tasks:
        raise ValueError("learned routing requires registry and tasks")
    # 延迟导入切断 engine.features → engine.decision.models → decision.__init__ 的初始化环。
    from engine.features.chart_feature_vector import build_chart_feature_vector

    features = build_chart_feature_vector(chart)
    completeness = "complete" if features.evidence_completeness == "full" else features.evidence_completeness
    return build_route_plan(
        feature_vector=features,
        tasks=tasks,
        evidence_completeness_band=completeness,
        registry=registry,
        risk_config=risk_config or RoutingRiskConfig(),
    )
