"""高派 L2 结构旁证 runner；仅使用 Chart/CFV 可计算代理，不伪造神煞或应期。"""

from __future__ import annotations

import hashlib

from engine.claims import Claim, Evidence, TaskUnsupported, TimeWindow, stable_claim_id, validate_claim_evidence
from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindTask
from engine.features import ChartFeatureVector

_SUPPORTED_TASKS = {"wealth.debt", "health.system_risk"}
_LIFETIME = TimeWindow(start_year=1900, end_year=2100, label="lifetime")
_HIGH_RISK_CONFIDENCE_CAP = 0.62


def _count(features: ChartFeatureVector, *names: str) -> int:
    return sum(int(features.ten_god_counts.get(name, 0)) for name in names)


def _evidence(
    features: ChartFeatureVector,
    task: BlindTask,
    *,
    rule_id: str,
    refs: tuple[str, ...],
    text: str,
) -> Evidence:
    raw = f"gao|{task.task_id}|{features.chart_id}|{rule_id}|{'|'.join(refs)}"
    return Evidence(
        evidence_id="evidence-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20],
        fact_refs=("four_pillars.day",),
        feature_refs=refs,
        rule_id=rule_id,
        text=text,
    )


def _claim(
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    task: BlindTask,
    *,
    rule_id: str,
    statement: str,
    falsifier: str,
    confidence_basis: str,
    refs: tuple[str, ...],
    evidence_text: str,
    snapshot: dict[str, object],
    confidence: float,
) -> list[Claim]:
    claim = Claim(
        claim_id=stable_claim_id("gao", task.task_id, features.chart_id, rule_id),
        school_id="gao",
        task_id=task.task_id,
        claim_type="event_claim",
        stance="support",
        statement=statement,
        evidence=(_evidence(features, task, rule_id=rule_id, refs=refs, text=evidence_text),),
        falsifier=falsifier,
        time_window=_LIFETIME,
        confidence_basis=confidence_basis,
        applicability_snapshot={**snapshot, "evidence_completeness": features.evidence_completeness},
        domain=task.domain,
        polarity="negative",
        magnitude=min(1.0, 0.45 + 0.06 * len(snapshot)),
        confidence=min(confidence, _HIGH_RISK_CONFIDENCE_CAP) if task.high_risk else confidence,
        high_risk=task.high_risk,
    )
    validate_claim_evidence(claim, chart, features)
    return [claim]


def _wealth_debt(
    chart: ChartFactLedger, features: ChartFeatureVector, task: BlindTask,
) -> list[Claim]:
    wealth_count = _count(features, "正财", "偏财")
    peer_count = _count(features, "比肩", "劫财")
    imbalance = features.draining_count - features.supporting_count
    signals = {
        "wealth_exposed": features.has_wealth and wealth_count >= 2,
        "peer_competition": peer_count >= 3,
        "support_drain_imbalance": imbalance >= 3,
        "branch_conflict": features.branch_conflict_intensity >= 0.55,
        "concentrated_or_withered": features.element_concentration >= 0.50 or len(features.missing_elements) >= 2,
    }
    # 财星是债务命题的必要语境，且还须至少两种独立压力代理同向。
    pressure_count = sum(int(value) for key, value in signals.items() if key != "wealth_exposed")
    if not signals["wealth_exposed"] or pressure_count < 2:
        return []
    rule_id = "GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1"
    refs = (
        "ten_god_counts.正财", "ten_god_counts.偏财", "ten_god_counts.比肩", "ten_god_counts.劫财",
        "supporting_count", "draining_count", "branch_conflict_intensity", "element_concentration",
        "missing_elements", "evidence_completeness",
    )
    return _claim(
        chart, features, task,
        rule_id=rule_id,
        statement="高派结构性旁证显示债务风险与财富承压信号复合出现，但不作必然判断。",
        falsifier="若没有可核验的显著债务、长期负债或债务危机记录，则命题证伪。",
        confidence_basis="财星达到最低门槛，并至少有两项比劫竞争、克泄耗失衡、支冲突或五行偏枯代理同向；未使用神煞或应期输入。",
        refs=refs,
        evidence_text=f"财星={wealth_count}，比劫={peer_count}，克泄耗减生扶={imbalance}，压力信号={pressure_count}。",
        snapshot={**signals, "wealth_count": wealth_count, "peer_count": peer_count, "pressure_signal_count": pressure_count},
        confidence=0.60,
    )


def _health_system_risk(
    chart: ChartFactLedger, features: ChartFeatureVector, task: BlindTask,
) -> list[Claim]:
    imbalance = features.draining_count - features.supporting_count
    strong_signals = {
        "severe_support_drain_imbalance": imbalance >= 4,
        "climate_extreme": features.climate_extreme and max(abs(features.cold_warm_axis), abs(features.dry_wet_axis)) >= 0.65,
        "element_concentration": features.element_concentration >= 0.50 or len(features.missing_elements) >= 2,
        "branch_conflict": features.branch_conflict_intensity >= 0.55,
    }
    signal_count = sum(int(value) for value in strong_signals.values())
    if signal_count >= 3:
        predicted_label = "high"
        confidence = 0.60
    elif signal_count >= 2:
        predicted_label = "moderate"
        confidence = 0.55
    else:
        return []
    rule_id = f"GAO-HEALTH-SYSTEM-RISK-{predicted_label.upper()}-V1"
    refs = (
        "supporting_count", "draining_count", "cold_warm_axis", "dry_wet_axis", "climate_extreme",
        "element_concentration", "missing_elements", "branch_conflict_intensity", "evidence_completeness",
    )
    return _claim(
        chart, features, task,
        rule_id=rule_id,
        statement=f"高派结构风险分层为 {predicted_label}：多项原局结构代理同向，仅表示系统性健康风险旁证，不替代专业评估。",
        falsifier="若独立结构复核和可核验健康记录均不支持相应风险等级，则命题证伪；该命题不是医学结论。",
        confidence_basis="只按生扶/克泄耗失衡、气候极端、五行集中偏枯与支冲突的复合程度分层；不使用疾病或神煞诊断。",
        refs=refs,
        evidence_text=f"克泄耗减生扶={imbalance}，复合强风险代理={signal_count}，分层={predicted_label}。",
        snapshot={**strong_signals, "support_drain_imbalance": imbalance, "risk_signal_count": signal_count, "predicted_label": predicted_label},
        confidence=confidence,
    )


def generate_claims(
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    task: BlindTask,
) -> list[Claim]:
    """生成高派债务旁证或健康结构风险分层；未覆盖任务显式 unsupported。"""
    if task.task_id not in _SUPPORTED_TASKS:
        raise TaskUnsupported(f"gao does not support task: {task.task_id}")
    if features.evidence_completeness != "full":
        return []
    if task.task_id == "wealth.debt":
        return _wealth_debt(chart, features, task)
    return _health_system_risk(chart, features, task)
