"""段派 L2 事件 runner：从原局事实、cfv-v1 与纯做功适配结果生成命题。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from engine.claims import Claim, Evidence, TaskUnsupported, TimeWindow, stable_claim_id, validate_claim_evidence
from engine.claims.domain import render_statement
from engine.claims.rule_loader import ExecutableClaimRule, RuleEvaluationResult, evaluate_rule, load_claim_rule_registry
from engine.decision.models import ChartFactLedger
from engine.energy.tiyong import evaluate_tiyong
from engine.energy.zuogong import evaluate_zuogong
from engine.evaluation.models import BlindTask
from engine.features import ChartFeatureVector
from engine.predicates.types import Bazi, GanZhi, _default_canggan_for

_EVENT_TASKS = {
    "career.role_change",
    "career.path_type",
    "wealth.debt",
    "marriage.divorce_or_remarriage",
}
_TIMING_TASKS = {
    "career.change_window",
    "marriage.event_window",
    "health.event_window",
    "wealth.major_loss_window",
}
_SUPPORTED_TASKS = _EVENT_TASKS | _TIMING_TASKS
_LIFETIME = TimeWindow(start_year=1900, end_year=2100, label="lifetime")
_CLAIM_RULES = load_claim_rule_registry()


@dataclass(frozen=True)
class _DuanStructure:
    body_count: int
    purpose_count: int
    active_path_count: int
    strongest_path_score: float
    path_types: tuple[str, ...]


def chart_ledger_to_bazi(chart: ChartFactLedger) -> Bazi:
    """把事实账本四柱纯转换为旧段派确定性引擎的 ``Bazi`` 输入。"""
    aliases = (("year", "年柱"), ("month", "月柱"), ("day", "日柱"), ("hour", "时柱"))
    pillars: list[GanZhi] = []
    for english, chinese in aliases:
        raw = str(chart.four_pillars.get(english, chart.four_pillars.get(chinese, ""))).strip()
        if len(raw) != 2:
            raise ValueError("duan event runner requires four complete pillars")
        pillars.append(GanZhi.parse(raw))
    bazi = Bazi(年柱=pillars[0], 月柱=pillars[1], 日柱=pillars[2], 时柱=pillars[3])
    bazi.藏干 = _default_canggan_for(bazi)
    return bazi


def _duan_structure(chart: ChartFactLedger) -> _DuanStructure:
    bazi = chart_ledger_to_bazi(chart)
    tiyong = evaluate_tiyong(bazi)
    paths = evaluate_zuogong(bazi, tiyong)
    active = tuple(path for path in paths if path.layer_count >= 1)
    return _DuanStructure(
        body_count=len(tiyong.body),
        purpose_count=len(tiyong.purpose),
        active_path_count=len(active),
        strongest_path_score=max((path.strength.score for path in active), default=0.0),
        path_types=tuple(sorted({path.type for path in active})),
    )


def _count(features: ChartFeatureVector, *names: str) -> int:
    return sum(int(features.ten_god_counts.get(name, 0)) for name in names)


def _evidence(
    features: ChartFeatureVector,
    *,
    task_id: str,
    rule_id: str,
    feature_refs: tuple[str, ...],
    text: str,
) -> Evidence:
    raw = f"duan|{task_id}|{features.chart_id}|{rule_id}|{'|'.join(feature_refs)}|{text}"
    return Evidence(
        evidence_id="evidence-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20],
        fact_refs=("four_pillars.day",),
        feature_refs=feature_refs,
        rule_id=rule_id,
        text=text,
    )


def _claim(
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    task: BlindTask,
    structure: _DuanStructure,
    *,
    rule: ExecutableClaimRule,
    result: RuleEvaluationResult,
    context: dict[str, object],
    feature_refs: tuple[str, ...],
    evidence_text: str,
    snapshot: dict[str, object],
) -> list[Claim]:
    evidence = _evidence(
        features,
        task_id=task.task_id,
        rule_id=rule.rule_id,
        feature_refs=feature_refs,
        text=evidence_text,
    )
    applicability = {
        **snapshot,
        "duan_body_count": structure.body_count,
        "duan_purpose_count": structure.purpose_count,
        "duan_active_path_count": structure.active_path_count,
        "duan_strongest_path_score": structure.strongest_path_score,
        "duan_path_types": structure.path_types,
        "evidence_completeness": features.evidence_completeness,
    }
    claim = Claim(
        claim_id=stable_claim_id("duan", task.task_id, features.chart_id, rule.rule_id),
        school_id="duan",
        task_id=task.task_id,
        claim_type=rule.claim_type,
        stance="support",
        statement=render_statement(rule, result, context),
        evidence=(evidence,),
        falsifier=rule.falsifier,
        time_window=_LIFETIME,
        confidence_basis=rule.confidence_basis,
        applicability_snapshot=applicability,
        domain=task.domain,
        polarity=rule.polarity,
        magnitude=min(1.0, 0.45 + 0.08 * structure.active_path_count),
        confidence=(
            min(rule.base_confidence, rule.high_risk_confidence_cap)
            if task.high_risk and rule.high_risk_confidence_cap is not None
            else rule.base_confidence
        ),
        high_risk=task.high_risk,
    )
    validate_claim_evidence(claim, chart, features)
    return [claim]


def _career_role_change(
    chart: ChartFactLedger, features: ChartFeatureVector, task: BlindTask, structure: _DuanStructure,
) -> list[Claim]:
    output_count = _count(features, "食神", "伤官")
    official_count = _count(features, "正官", "七杀")
    movement_structure = features.mixed_official_kill or features.branch_conflict_intensity >= 0.35
    context = {
        "evidence_completeness": features.evidence_completeness,
        "has_official": features.has_official,
        "has_output": features.has_output,
        "output_count": output_count,
        "official_count": official_count,
        "movement_structure": movement_structure,
        "active_path_count": structure.active_path_count,
        "branch_conflict_intensity": features.branch_conflict_intensity,
    }
    rule = _CLAIM_RULES.get("DUAN-EVENT-CAREER-ROLE-CHANGE-V1")
    result = evaluate_rule(rule, context)
    if not result.matched:
        return []
    return _claim(
        chart, features, task, structure,
        rule=rule,
        result=result,
        context=context,
        feature_refs=("ten_god_counts.食神", "ten_god_counts.伤官", "ten_god_counts.正官", "ten_god_counts.七杀", "mixed_official_kill", "branch_conflict_intensity"),
        evidence_text=f"食伤={output_count}，官杀={official_count}，有效做功路径={structure.active_path_count}，冲突强度={features.branch_conflict_intensity:.2f}。",
        snapshot=context,
    )


def _career_path_type(
    chart: ChartFactLedger, features: ChartFeatureVector, task: BlindTask, structure: _DuanStructure,
) -> list[Claim]:
    employment_score = _count(features, "正官", "七杀", "正印", "偏印")
    entrepreneurship_score = _count(features, "食神", "伤官", "正财", "偏财")
    if employment_score >= 4 and entrepreneurship_score >= 4 and features.branch_conflict_intensity >= 0.35:
        predicted_label = "mixed"
    elif employment_score >= 4 and employment_score - entrepreneurship_score >= 3:
        predicted_label = "employment"
    elif entrepreneurship_score >= 4 and entrepreneurship_score - employment_score >= 3:
        predicted_label = "entrepreneurship"
    else:
        return []
    context = {
        "evidence_completeness": features.evidence_completeness,
        "predicted_label": predicted_label,
        "employment_score": employment_score,
        "entrepreneurship_score": entrepreneurship_score,
        "employment_advantage": employment_score - entrepreneurship_score,
        "entrepreneurship_advantage": entrepreneurship_score - employment_score,
        "branch_conflict_intensity": features.branch_conflict_intensity,
        "active_path_count": structure.active_path_count,
    }
    rule = _CLAIM_RULES.get(f"DUAN-EVENT-CAREER-PATH-{predicted_label.upper()}-V1")
    result = evaluate_rule(rule, context)
    if not result.matched:
        return []
    return _claim(
        chart, features, task, structure,
        rule=rule,
        result=result,
        context=context,
        feature_refs=("ten_god_counts.正官", "ten_god_counts.七杀", "ten_god_counts.正印", "ten_god_counts.偏印", "ten_god_counts.食神", "ten_god_counts.伤官", "ten_god_counts.正财", "ten_god_counts.偏财", "branch_conflict_intensity"),
        evidence_text=f"任职信号={employment_score}，经营信号={entrepreneurship_score}，有效做功路径={structure.active_path_count}。",
        snapshot=context,
    )


def _wealth_debt(
    chart: ChartFactLedger, features: ChartFeatureVector, task: BlindTask, structure: _DuanStructure,
) -> list[Claim]:
    wealth_count = _count(features, "正财", "偏财")
    peer_pressure = _count(features, "比肩", "劫财")
    imbalance = features.draining_count - features.supporting_count
    context = {
        "evidence_completeness": features.evidence_completeness,
        "has_wealth": features.has_wealth,
        "wealth_count": wealth_count,
        "peer_pressure": peer_pressure,
        "support_drain_imbalance": imbalance,
        "branch_conflict_intensity": features.branch_conflict_intensity,
        "active_path_count": structure.active_path_count,
    }
    rule = _CLAIM_RULES.get("DUAN-EVENT-WEALTH-DEBT-V1")
    result = evaluate_rule(rule, context)
    if not result.matched:
        return []
    return _claim(
        chart, features, task, structure,
        rule=rule,
        result=result,
        context=context,
        feature_refs=("ten_god_counts.正财", "ten_god_counts.偏财", "ten_god_counts.比肩", "ten_god_counts.劫财", "supporting_count", "draining_count", "branch_conflict_intensity"),
        evidence_text=f"财星={wealth_count}，比劫={peer_pressure}，克泄耗减生扶={imbalance}，冲突强度={features.branch_conflict_intensity:.2f}。",
        snapshot=context,
    )


def _marriage_divorce_or_remarriage(
    chart: ChartFactLedger, features: ChartFeatureVector, task: BlindTask, structure: _DuanStructure,
) -> list[Claim]:
    day_pillar = str(chart.four_pillars.get("day", chart.four_pillars.get("日柱", "")))
    day_branch = day_pillar[1] if len(day_pillar) == 2 else ""
    day_branch_disrupted = any(day_branch in pair for pair in (*features.chong_pairs, *features.xing_hai_pairs))
    independent_signals = (
        int(day_branch_disrupted)
        + int(features.mixed_official_kill)
        + int(bool(features.chong_pairs) and bool(features.xing_hai_pairs))
    )
    context = {
        "evidence_completeness": features.evidence_completeness,
        "independent_signal_count": independent_signals,
        "active_path_count": structure.active_path_count,
    }
    rule = _CLAIM_RULES.get("DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1")
    result = evaluate_rule(rule, context)
    if not result.matched:
        return []
    return _claim(
        chart, features, task, structure,
        rule=rule,
        result=result,
        context=context,
        feature_refs=("chong_pairs", "xing_hai_pairs", "mixed_official_kill", "branch_conflict_intensity"),
        evidence_text=f"日支受扰={day_branch_disrupted}，官杀混杂={features.mixed_official_kill}，冲刑害复合={bool(features.chong_pairs) and bool(features.xing_hai_pairs)}。",
        snapshot={**context, "day_branch": day_branch, "day_branch_disrupted": day_branch_disrupted, "mixed_official_kill": features.mixed_official_kill},
    )


def generate_claims(
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    task: BlindTask,
) -> list[Claim]:
    """生成段派白名单事件或 timing Claim；每任务每盘最多一条。"""
    if task.task_id not in _SUPPORTED_TASKS:
        raise TaskUnsupported(f"duan does not support task: {task.task_id}")
    if task.task_id in _TIMING_TASKS:
        from engine.v5.duan_timing import generate_timing_claims

        return generate_timing_claims(chart, features, task)
    if features.evidence_completeness != "full":
        return []
    try:
        structure = _duan_structure(chart)
    except (KeyError, TypeError, ValueError):
        return []
    handlers = {
        "career.role_change": _career_role_change,
        "career.path_type": _career_path_type,
        "wealth.debt": _wealth_debt,
        "marriage.divorce_or_remarriage": _marriage_divorce_or_remarriage,
    }
    return handlers[task.task_id](chart, features, task, structure)
