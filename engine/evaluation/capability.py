from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Iterable
from statistics import pstdev

from engine.evaluation.models import CapabilityPosterior, ScoreRecord

Identity = tuple[str, str, str, str, str, str]


def beta_posterior(hit_weight: float, miss_weight: float) -> tuple[float, tuple[float, float]]:
    """Return the exact Beta(1+hit, 1+miss) mean and an approximate interval.

    The interval is a clipped 95% normal approximation, not an exact Beta
    posterior quantile. It is intentionally dependency-free.
    """
    if hit_weight < 0.0 or miss_weight < 0.0:
        raise ValueError("hit and miss weights must be non-negative")
    alpha = 1.0 + hit_weight
    beta = 1.0 + miss_weight
    mean = alpha / (alpha + beta)
    variance = alpha * beta / ((alpha + beta) ** 2 * (alpha + beta + 1.0))
    half_width = 1.96 * math.sqrt(variance)
    credible_interval_approx = (max(0.0, mean - half_width), min(1.0, mean + half_width))
    return mean, credible_interval_approx


def _identity(score: ScoreRecord) -> Identity:
    return (
        score.school_id,
        score.task_id,
        score.chart_prototype_id,
        score.claim_type,
        score.time_horizon,
        score.evidence_completeness_band,
    )


def _calibration_error(claims: list[ScoreRecord]) -> float | None:
    scored = [score for score in claims if score.probability_score is not None and score.observed_positive is not None]
    if len(scored) < 5:
        return None
    bins: dict[int, list[tuple[float, bool]]] = defaultdict(list)
    for score in scored:
        probability = 1.0 - math.sqrt(1.0 - score.probability_score) if score.observed_positive else math.sqrt(1.0 - score.probability_score)
        bins[min(int(probability * 10), 9)].append((probability, score.observed_positive))
    return sum(
        len(items) * abs(sum(probability for probability, _ in items) / len(items) - sum(observed for _, observed in items) / len(items))
        for items in bins.values()
    ) / len(scored)


def build_capability_posteriors(
    scores: Iterable[ScoreRecord],
    evidence_grade: str,
    evaluated_at: str,
) -> list[CapabilityPosterior]:
    grouped: dict[Identity, list[ScoreRecord]] = defaultdict(list)
    for score in scores:
        grouped[_identity(score)].append(score)

    posteriors: list[CapabilityPosterior] = []
    for identity in sorted(grouped):
        records = grouped[identity]
        claims = [record for record in records if record.state == "claim"]
        probability_scores = [record.probability_score for record in claims if record.probability_score is not None]
        hits = sum(score for score in probability_scores)
        misses = len(probability_scores) - hits
        posterior_mean, interval = beta_posterior(hits, misses)
        school_id, task_id, prototype, claim_type, horizon, completeness = identity
        posteriors.append(
            CapabilityPosterior(
                school_id=school_id,
                task_id=task_id,
                chart_prototype_id=prototype,
                claim_type=claim_type,
                time_horizon=horizon,
                evidence_completeness_band=completeness,
                coverage_rate=sum(record.knowledge_coverage for record in records) / len(records),
                discrimination_score=pstdev(probability_scores) if len(probability_scores) >= 2 else 0.0,
                accuracy_score=sum(probability_scores) / len(probability_scores) if probability_scores else 0.0,
                calibration_error=_calibration_error(claims),
                posterior_mean=posterior_mean,
                credible_interval=interval,
                n_eff=hits + misses,
                evidence_grade=evidence_grade,
                last_evaluated_at=evaluated_at,
            )
        )
    return posteriors
