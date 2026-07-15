"""高派 L2 结构旁证 runner；仅使用 Chart/CFV 可计算代理，不伪造神煞或应期。"""

from __future__ import annotations

import hashlib

from engine.claims import Claim, Evidence, TaskUnsupported, TimeWindow, stable_claim_id, validate_claim_evidence
from engine.claims.rule_loader import ExecutableClaimRule, evaluate_rule, load_claim_rule_registry
from engine.decision.models import ChartFactLedger
from engine.evaluation.models import BlindTask
from engine.features import ChartFeatureVector

_SUPPORTED_TASKS = {"wealth.debt", "health.system_risk"}
_LIFETIME = TimeWindow(start_year=1900, end_year=2100, label="lifetime")
_CLAIM_RULES = load_claim_rule_registry()


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
    rule: ExecutableClaimRule,
    refs: tuple[str, ...],
    evidence_text: str,
    snapshot: dict[str, object],
) -> list[Claim]:
    claim = Claim(
        claim_id=stable_claim_id("gao", task.task_id, features.chart_id, rule.rule_id),
        school_id="gao",
        task_id=task.task_id,
        claim_type=rule.claim_type,
        stance="support",
        statement=rule.conclusion_template,
        evidence=(_evidence(features, task, rule_id=rule.rule_id, refs=refs, text=evidence_text),),
        falsifier=rule.falsifier,
        time_window=_LIFETIME,
        confidence_basis=rule.confidence_basis,
        applicability_snapshot={**snapshot, "evidence_completeness": features.evidence_completeness},
        domain=task.domain,
        polarity=rule.polarity,
        magnitude=min(1.0, 0.45 + 0.06 * len(snapshot)),
        confidence=(
            min(rule.base_confidence, rule.high_risk_confidence_cap)
            if task.high_risk and rule.high_risk_confidence_cap is not None
            else rule.base_confidence
        ),
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
    pressure_count = sum(int(value) for key, value in signals.items() if key != "wealth_exposed")
    context = {
        "evidence_completeness": features.evidence_completeness,
        "wealth_exposed": signals["wealth_exposed"],
        "pressure_signal_count": pressure_count,
    }
    rule = _CLAIM_RULES.get("GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1")
    if not evaluate_rule(rule, context).matched:
        return []
    refs = (
        "ten_god_counts.正财", "ten_god_counts.偏财", "ten_god_counts.比肩", "ten_god_counts.劫财",
        "supporting_count", "draining_count", "branch_conflict_intensity", "element_concentration",
        "missing_elements", "evidence_completeness",
    )
    return _claim(
        chart, features, task,
        rule=rule,
        refs=refs,
        evidence_text=f"财星={wealth_count}，比劫={peer_count}，克泄耗减生扶={imbalance}，压力信号={pressure_count}。",
        snapshot={**context, **signals, "wealth_count": wealth_count, "peer_count": peer_count},
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
    elif signal_count >= 2:
        predicted_label = "moderate"
    else:
        return []
    context = {
        "evidence_completeness": features.evidence_completeness,
        "predicted_label": predicted_label,
        "risk_signal_count": signal_count,
    }
    rule = _CLAIM_RULES.get(f"GAO-HEALTH-SYSTEM-RISK-{predicted_label.upper()}-V1")
    if not evaluate_rule(rule, context).matched:
        return []
    refs = (
        "supporting_count", "draining_count", "cold_warm_axis", "dry_wet_axis", "climate_extreme",
        "element_concentration", "missing_elements", "branch_conflict_intensity", "evidence_completeness",
    )
    return _claim(
        chart, features, task,
        rule=rule,
        refs=refs,
        evidence_text=f"克泄耗减生扶={imbalance}，复合强风险代理={signal_count}，分层={predicted_label}。",
        snapshot={**context, **strong_signals, "support_drain_imbalance": imbalance},
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
