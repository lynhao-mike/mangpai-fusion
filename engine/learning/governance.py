"""配置驱动、无副作用的 L9 学习治理。"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any, Mapping

import yaml

from engine.evaluation.models import CapabilityPosterior
from engine.learning.models import ConditionalLearningSignal, LearningDecision, LearningThresholds


def load_learning_thresholds(path: str | Path) -> LearningThresholds:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("thresholds"), dict):
        raise ValueError("conditional learning config requires thresholds mapping")
    values = raw["thresholds"]
    required = (
        "medium_n_eff",
        "mature_n_eff",
        "partial_weight",
        "max_posterior_delta",
        "large_change_delta",
    )
    for name in required:
        if name not in values:
            raise ValueError(f"missing threshold: {name}")
    return LearningThresholds(**{name: float(values[name]) for name in required})


def _beta_posterior(hit_weight: float, miss_weight: float) -> tuple[float, tuple[float, float]]:
    alpha = 1.0 + hit_weight
    beta = 1.0 + miss_weight
    mean = alpha / (alpha + beta)
    variance = alpha * beta / ((alpha + beta) ** 2 * (alpha + beta + 1.0))
    half_width = 1.96 * math.sqrt(variance)
    return mean, (max(0.0, mean - half_width), min(1.0, mean + half_width))


def _current_values(current: CapabilityPosterior | None) -> tuple[float, float, tuple[float, float]]:
    if current is None:
        mean, interval = _beta_posterior(0.0, 0.0)
        return mean, 0.0, interval
    return current.posterior_mean, current.n_eff, current.credible_interval


def _signal_weight(signal: ConditionalLearningSignal, thresholds: LearningThresholds) -> float:
    if signal.effective_weight == 0.0:
        return 0.0
    verdict_multiplier = thresholds.partial_weight if signal.verdict == "partial" else 1.0
    return signal.feedback_quality * verdict_multiplier


def _review_reasons(
    signal: ConditionalLearningSignal,
    *,
    is_high_risk: bool,
    proposed_delta: float,
    thresholds: LearningThresholds,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not signal.attributable:
        reasons.append("unattributable")
    if is_high_risk:
        reasons.append("high_risk")
    if abs(proposed_delta) >= thresholds.large_change_delta:
        reasons.append("large_change")
    metadata_reasons = signal.metadata.get("review_reasons", ())
    if isinstance(metadata_reasons, str):
        metadata_reasons = (metadata_reasons,)
    for reason in metadata_reasons:
        if reason in {"feedback_conflict", "sample_drift", "cross_domain", "suspected_leakage"}:
            reasons.append(str(reason))
    return tuple(dict.fromkeys(reasons))


def decide_learning_tier(
    signal: ConditionalLearningSignal,
    current_posterior: CapabilityPosterior | None,
    thresholds: LearningThresholds,
    is_high_risk: bool,
) -> LearningDecision:
    """计算单个归因信号的治理决策；不写任何持久状态。"""

    current_mean, n_eff_before, current_interval = _current_values(current_posterior)
    weight = _signal_weight(signal, thresholds)
    n_eff_after = n_eff_before + weight

    raw_mean = current_mean
    raw_interval = current_interval
    if weight:
        hits = current_mean * n_eff_before
        misses = (1.0 - current_mean) * n_eff_before
        if signal.verdict == "hit":
            hits += weight
        elif signal.verdict == "miss":
            misses += weight
        elif signal.verdict == "partial":
            hits += weight * 0.5
            misses += weight * 0.5
        raw_mean, raw_interval = _beta_posterior(hits, misses)

    raw_delta = raw_mean - current_mean
    clamped_delta = max(-thresholds.max_posterior_delta, min(thresholds.max_posterior_delta, raw_delta))
    proposed_mean = max(0.0, min(1.0, current_mean + clamped_delta))

    if not signal.attributable or signal.verdict == "no_data":
        tier = "manual_review"
        proposed_delta = 0.0
        proposed_mean = current_mean
        raw_interval = current_interval
    elif n_eff_after < thresholds.medium_n_eff:
        tier = "record_only"
        proposed_delta = 0.0
        proposed_mean = current_mean
        raw_interval = current_interval
    elif n_eff_after < thresholds.mature_n_eff:
        tier = "adjust_applicability"
        proposed_delta = clamped_delta
    else:
        tier = "adjust_rule_prior"
        proposed_delta = clamped_delta

    reasons = _review_reasons(
        signal,
        is_high_risk=is_high_risk,
        proposed_delta=proposed_delta,
        thresholds=thresholds,
    )
    requires_approval = is_high_risk or tier in {"adjust_rule_prior", "manual_review"}
    applied = tier == "adjust_applicability" and not requires_approval
    rationale = f"tier={tier}; n_eff={n_eff_before:g}->{n_eff_after:g}"
    digest_source = f"{signal.signal_id}|{signal.identity.key}|{n_eff_before:.12g}|{n_eff_after:.12g}|{tier}"
    decision_id = "decision-" + hashlib.sha256(digest_source.encode("utf-8")).hexdigest()[:20]

    audit: Mapping[str, Any] = {
        "verdict": signal.verdict,
        "effective_weight": weight,
        "unclamped_posterior_mean": raw_mean,
        "unclamped_delta": raw_delta,
        "review_reasons": reasons,
        "rule_id": signal.rule_id,
    }
    return LearningDecision(
        decision_id=decision_id,
        signal_id=signal.signal_id,
        target_identity=signal.identity,
        update_tier=tier,
        proposed_delta=proposed_delta,
        proposed_posterior_mean=proposed_mean,
        proposed_credible_interval=raw_interval,
        n_eff_before=n_eff_before,
        n_eff_after=n_eff_after,
        applied=applied,
        requires_human_approval=requires_approval,
        snapshot_ref=None,
        rationale=rationale,
        audit=audit,
    )
