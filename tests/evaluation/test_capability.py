from __future__ import annotations

import pytest

from engine.evaluation.capability import beta_posterior, build_capability_posteriors
from engine.evaluation.models import ScoreRecord

IDENTITY = ("ziping", "education.credentials", "strong_day_master", "binary_event", "lifetime", "complete")


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


def _build(scores: list[ScoreRecord], **overrides: object):
    claims = {
        (score.case_id, score.task_id, score.school_id): 0.8
        for score in scores
        if score.state == "claim"
    }
    kwargs = {
        "claim_probabilities": claims,
        "eligible_case_ids": {IDENTITY: {score.case_id for score in scores}},
    }
    kwargs.update(overrides)
    return build_capability_posteriors(scores, "A", "2026-07-12T00:00:00Z", **kwargs)


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


def test_capability_uses_explicit_claim_probability_eligible_cases_weights_and_gain() -> None:
    scores = [
        _score("C-005", probability_score=0.96, observed_positive=True),
        _score("C-001", probability_score=0.36, observed_positive=False),
        _score("C-004", probability_score=0.75, observed_positive=True),
        _score("C-003", state="abstain"),
        _score("C-002", state="unsupported"),
    ]
    probabilities = {
        ("C-005", "education.credentials", "ziping"): 0.9,
        ("C-001", "education.credentials", "ziping"): 0.4,
        ("C-004", "education.credentials", "ziping"): 0.7,
    }
    weights = {
        ("C-005", "education.credentials", "ziping"): 1.0,
        ("C-001", "education.credentials", "ziping"): 0.5,
        ("C-004", "education.credentials", "ziping"): 0.0,
        ("C-003", "education.credentials", "ziping"): 1.0,
    }
    kwargs = {
        "claim_probabilities": probabilities,
        "eligible_case_ids": {IDENTITY: {"C-001", "C-002", "C-003", "C-004", "C-005", "C-006"}},
        "score_weights": weights,
        "incremental_gains": {IDENTITY: 0.125},
    }

    first = build_capability_posteriors(scores, "A", "now", **kwargs)
    second = build_capability_posteriors(reversed(scores), "A", "now", **kwargs)

    assert first == second
    posterior = first[0]
    assert posterior.coverage_rate == pytest.approx(4 / 6)
    assert posterior.discrimination_score == pytest.approx(0.2054804668)
    assert posterior.accuracy_score == pytest.approx((0.96 + 0.5 * 0.36) / 1.5)
    assert posterior.n_eff == pytest.approx(1.5)
    assert posterior.posterior_mean == pytest.approx((1 + 0.96 + 0.5 * 0.36) / 3.5)
    assert posterior.incremental_gain == pytest.approx(0.125)


def test_calibration_uses_explicit_probabilities_and_requires_five_scored_claims() -> None:
    fewer = [_score(f"C-{index}", probability_score=0.2, observed_positive=index % 2 == 0) for index in range(4)]
    enough = fewer + [_score("C-4", probability_score=0.2, observed_positive=True)]
    probabilities = {
        (score.case_id, score.task_id, score.school_id): probability
        for score, probability in zip(enough, [0.9, 0.1, 0.8, 0.2, 0.7], strict=True)
    }

    assert _build(fewer, claim_probabilities={key: value for key, value in probabilities.items() if key[0] != "C-4"})[0].calibration_error is None
    assert _build(enough, claim_probabilities=probabilities)[0].calibration_error == pytest.approx(0.18)


@pytest.mark.parametrize("probability", [-0.1, 1.1])
def test_claim_probability_must_exist_and_be_in_range(probability: float) -> None:
    score = _score("C-1", probability_score=0.8, observed_positive=True)
    with pytest.raises(ValueError, match="claim probability"):
        _build([score], claim_probabilities={(score.case_id, score.task_id, score.school_id): probability})
    with pytest.raises(ValueError, match="claim probability"):
        _build([score], claim_probabilities={})


@pytest.mark.parametrize("eligible", [{}, {IDENTITY: set()}])
def test_eligible_identity_must_exist_and_be_nonempty(eligible: dict) -> None:
    with pytest.raises(ValueError, match="eligible"):
        _build([_score("C-1", probability_score=0.8, observed_positive=True)], eligible_case_ids=eligible)


@pytest.mark.parametrize("weight", [-1.0, 0.25, 0.75, 2.0])
def test_score_weight_is_restricted(weight: float) -> None:
    score = _score("C-1", probability_score=0.8, observed_positive=True)
    with pytest.raises(ValueError, match="weight"):
        _build([score], score_weights={(score.case_id, score.task_id, score.school_id): weight})
