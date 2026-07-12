from __future__ import annotations

import pytest

from engine.evaluation.capability import beta_posterior, build_capability_posteriors
from engine.evaluation.models import ScoreRecord


def _score(
    case_id: str,
    *,
    state: str = "claim",
    probability_score: float | None = None,
    observed_positive: bool | None = None,
) -> ScoreRecord:
    return ScoreRecord(
        case_id=case_id,
        school_id="ziping",
        task_id="education.credentials",
        claim_type="binary_event",
        state=state,
        abstained=state == "abstain",
        knowledge_coverage=state != "unsupported",
        chart_prototype_id="strong_day_master",
        time_horizon="lifetime",
        evidence_completeness_band="complete",
        probability_score=probability_score,
        observed_positive=observed_positive,
    )


def test_beta_posterior_uses_uniform_prior_and_widens_for_small_samples() -> None:
    small_mean, small_interval = beta_posterior(2.0, 0.0)
    large_mean, large_interval = beta_posterior(20.0, 0.0)
    assert small_mean == 0.75
    assert large_mean > small_mean
    assert small_interval[1] - small_interval[0] > large_interval[1] - large_interval[0]


@pytest.mark.parametrize("weights", [(-1.0, 0.0), (0.0, -1.0)])
def test_beta_posterior_rejects_negative_weights(weights: tuple[float, float]) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        beta_posterior(*weights)


def test_capability_aggregation_is_conditional_deterministic_and_uses_scored_claims() -> None:
    scores = [
        _score("C-005", probability_score=0.96, observed_positive=True),
        _score("C-001", probability_score=0.36, observed_positive=False),
        _score("C-004", probability_score=0.75, observed_positive=True),
        _score("C-003", state="abstain"),
        _score("C-002", state="unsupported"),
    ]

    first = build_capability_posteriors(scores, "A", "2026-07-12T00:00:00Z")
    second = build_capability_posteriors(reversed(scores), "A", "2026-07-12T00:00:00Z")

    assert first == second
    assert len(first) == 1
    posterior = first[0]
    assert posterior.coverage_rate == pytest.approx(4 / 5)
    assert posterior.accuracy_score == pytest.approx((0.96 + 0.36 + 0.75) / 3)
    assert posterior.n_eff == pytest.approx(3.0)
    assert posterior.posterior_mean == pytest.approx((1.0 + 0.96 + 0.36 + 0.75) / 5.0)
    assert posterior.calibration_error is None
    assert posterior.discrimination_score > 0.0


def test_calibration_error_requires_at_least_five_scored_claims() -> None:
    fewer = [_score(f"C-{index}", probability_score=0.96, observed_positive=True) for index in range(4)]
    enough = fewer + [_score("C-4", probability_score=0.36, observed_positive=False)]

    assert build_capability_posteriors(fewer, "B", "now")[0].calibration_error is None
    assert build_capability_posteriors(enough, "B", "now")[0].calibration_error is not None
