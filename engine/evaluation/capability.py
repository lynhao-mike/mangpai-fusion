from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Collection, Iterable, Mapping
from statistics import pstdev

from engine.evaluation.models import CapabilityPosterior, ScoreRecord

Identity = tuple[str, str, str, str, str, str]
ScoreKey = tuple[str, str, str]


def beta_posterior(hit_weight: float, miss_weight: float) -> tuple[float, tuple[float, float]]:
    """Return the Beta(1+hit, 1+miss) mean and clipped normal interval."""
    if hit_weight < 0.0 or miss_weight < 0.0:
        raise ValueError("hit and miss weights must be non-negative")
    alpha = 1.0 + hit_weight
    beta = 1.0 + miss_weight
    mean = alpha / (alpha + beta)
    variance = alpha * beta / ((alpha + beta) ** 2 * (alpha + beta + 1.0))
    half_width = 1.96 * math.sqrt(variance)
    return mean, (max(0.0, mean - half_width), min(1.0, mean + half_width))


def _identity(score: ScoreRecord) -> Identity:
    return (
        score.school_id,
        score.task_id,
        score.chart_prototype_id,
        score.claim_type,
        score.time_horizon,
        score.evidence_completeness_band,
    )


def _score_key(score: ScoreRecord) -> ScoreKey:
    return score.case_id, score.task_id, score.school_id


def _calibration_error(claims: list[tuple[ScoreRecord, float]]) -> float | None:
    scored = [(score, probability) for score, probability in claims if score.probability_score is not None and score.observed_positive is not None]
    if len(scored) < 5:
        return None
    bins: dict[int, list[tuple[float, bool]]] = defaultdict(list)
    for score, probability in scored:
        bins[min(int(probability * 10), 9)].append((probability, score.observed_positive))
    return sum(
        len(items) * abs(sum(probability for probability, _ in items) / len(items) - sum(observed for _, observed in items) / len(items))
        for items in bins.values()
    ) / len(scored)


def build_capability_posteriors(
    scores: Iterable[ScoreRecord],
    evidence_grade: str,
    evaluated_at: str,
    *,
    claim_probabilities: Mapping[ScoreKey, float],
    eligible_case_ids: Mapping[Identity, Collection[str]],
    score_weights: Mapping[ScoreKey, float] | None = None,
    incremental_gains: Mapping[Identity, float] | None = None,
) -> list[CapabilityPosterior]:
    grouped: dict[Identity, list[ScoreRecord]] = defaultdict(list)
    seen_score_keys: set[ScoreKey] = set()
    for score in scores:
        key = _score_key(score)
        if key in seen_score_keys:
            raise ValueError("duplicate score identity")
        seen_score_keys.add(key)
        grouped[_identity(score)].append(score)

    posteriors: list[CapabilityPosterior] = []
    for identity in sorted(grouped):
        records = grouped[identity]
        eligible = eligible_case_ids.get(identity)
        if not eligible:
            raise ValueError(f"missing or empty eligible case set for identity {identity}")
        eligible_set = set(eligible)

        claims_with_probabilities: list[tuple[ScoreRecord, float]] = []
        weighted_scores: list[tuple[float, float]] = []
        for record in records:
            key = _score_key(record)
            if score_weights is not None and key in score_weights and score_weights[key] not in (0.0, 0.5, 1.0):
                raise ValueError("score weight must be one of 0, 0.5, or 1")
            if record.state != "claim":
                continue
            if key not in claim_probabilities:
                raise ValueError(f"missing claim probability for {key}")
            probability = claim_probabilities[key]
            if not 0.0 <= probability <= 1.0:
                raise ValueError("claim probability must be between 0 and 1")
            claims_with_probabilities.append((record, probability))
            if record.probability_score is not None:
                weight = 1.0 if score_weights is None else score_weights.get(key, 1.0)
                weighted_scores.append((record.probability_score, weight))

        hits = sum(score * weight for score, weight in weighted_scores)
        n_eff = sum(weight for _, weight in weighted_scores)
        posterior_mean, interval = beta_posterior(hits, n_eff - hits)
        raw_probabilities = [probability for _, probability in claims_with_probabilities]
        school_id, task_id, prototype, claim_type, horizon, completeness = identity
        posteriors.append(
            CapabilityPosterior(
                school_id=school_id,
                task_id=task_id,
                chart_prototype_id=prototype,
                claim_type=claim_type,
                time_horizon=horizon,
                evidence_completeness_band=completeness,
                coverage_rate=len({record.case_id for record in records if record.state != "unsupported"} & eligible_set) / len(eligible_set),
                discrimination_score=pstdev(raw_probabilities) if len(raw_probabilities) >= 2 else 0.0,
                accuracy_score=hits / n_eff if n_eff else 0.0,
                calibration_error=_calibration_error(claims_with_probabilities),
                posterior_mean=posterior_mean,
                credible_interval=interval,
                n_eff=n_eff,
                evidence_grade=evidence_grade,
                last_evaluated_at=evaluated_at,
                incremental_gain=(incremental_gains or {}).get(identity, 0.0),
            )
        )
    return posteriors
