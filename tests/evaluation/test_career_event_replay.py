from __future__ import annotations

import inspect
from dataclasses import replace

import pytest

from engine.asof.career_event_prediction import (
    CareerPredictionWindow,
    predict_career_role_change,
)
from engine.decision.models import ChartFactLedger
from engine.evaluation.career_event_replay import (
    CAREER_EVENT_LABEL_SCHEMA,
    LEGACY_REN_CAREER_MODEL_ID,
    CareerEventReplayPrediction,
    HistoricalCareerEventLabel,
    freeze_career_event_predictions,
    freeze_career_event_replay_predictions,
    project_career_event_prediction,
    project_legacy_ren_career_event_prediction,
    reveal_career_event_labels,
    score_career_event_replay,
    verify_frozen_career_event_replay,
)


def _qualified_chart(*, year: int = 2024) -> ChartFactLedger:
    return ChartFactLedger(
        sex_marker="乾",
        four_pillars={
            "year": "癸未",
            "month": "甲寅",
            "day": "壬戌",
            "hour": "丙午",
        },
        dayun_steps=[{"ganzhi": "丙辰", "start_year": 2018, "end_year": 2027}],
        liunian_steps=[{"year": year, "ganzhi": "甲辰", "dayun": "丙辰"}],
    )


def _unqualified_chart(*, year: int = 2024) -> ChartFactLedger:
    return ChartFactLedger(
        sex_marker="乾",
        four_pillars={
            "year": "庚申",
            "month": "戊寅",
            "day": "壬子",
            "hour": "辛丑",
        },
        dayun_steps=[{"ganzhi": "丙辰", "start_year": 2018, "end_year": 2027}],
        liunian_steps=[{"year": year, "ganzhi": "甲辰", "dayun": "丙辰"}],
    )


def _run(case_id: str, *, qualified: bool = True, year: int = 2024):
    return predict_career_role_change(
        case_id=case_id,
        chart=_qualified_chart(year=year) if qualified else _unqualified_chart(year=year),
        window=CareerPredictionWindow(year, year, "historical"),
    )


def _label(
    *,
    label_id: str,
    case_id: str,
    year: int = 2024,
    event_type: str = "career.promotion",
    direction: str = "neutral",
    magnitude: float = 0.61,
) -> dict[str, object]:
    return {
        "label_id": label_id,
        "case_id": case_id,
        "start_year": year,
        "end_year": year,
        "domain": "事业",
        "event_type": event_type,
        "direction": direction,
        "magnitude": magnitude,
        "source_ref": f"cases/{case_id}/input.md#known-facts",
        "confidence_grade": "A",
        "dataset_classification": "development_replay_only",
    }


def _no_event(case_id: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "source_ref": f"cases/{case_id}/input.md#known-facts",
        "confidence_grade": "A",
        "dataset_classification": "development_replay_only",
    }


def _labels_document(
    freeze_hash: str,
    labels: list[dict[str, object]],
    *,
    no_event_cases: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": CAREER_EVENT_LABEL_SCHEMA,
        "freeze_hash": freeze_hash,
        "labels": labels,
        "no_event_cases": no_event_cases or [],
    }


def test_projection_keeps_only_blind_scoring_fields() -> None:
    run = _run("C-REPLAY-PROJECTION")

    projection = project_career_event_prediction(run)

    assert projection.status == "predicted"
    assert projection.predicted_start_year == 2024
    assert projection.predicted_end_year == 2024
    assert projection.event_type == "career.role_change"
    assert set(projection.to_dict()) == {
        "case_id",
        "model_id",
        "status",
        "observation_start_year",
        "observation_end_year",
        "predicted_start_year",
        "predicted_end_year",
        "domain",
        "event_type",
        "direction",
        "magnitude",
    }
    serialized = str(projection.to_dict()).lower()
    for forbidden in (
        "known_facts",
        "feedback",
        "verification",
        "label",
        "truth",
        "calibration",
    ):
        assert forbidden not in serialized


def test_freeze_is_order_independent_and_tamper_evident() -> None:
    left = _run("C-REPLAY-B")
    right = _run("C-REPLAY-A", qualified=False)

    first = freeze_career_event_predictions(
        [left, right],
        dataset_id="career-development-replay-v1",
        dataset_classification="development_replay_only",
    )
    second = freeze_career_event_predictions(
        [right, left],
        dataset_id="career-development-replay-v1",
        dataset_classification="development_replay_only",
    )

    assert first.to_dict() == second.to_dict()
    assert [item.case_id for item in first.predictions] == ["C-REPLAY-A", "C-REPLAY-B"]
    verify_frozen_career_event_replay(first)
    with pytest.raises(ValueError, match="freeze hash mismatch"):
        verify_frozen_career_event_replay(replace(first, dataset_id="tampered-dataset"))


def test_labels_cannot_be_revealed_before_matching_freeze() -> None:
    frozen = freeze_career_event_predictions(
        [_run("C-REPLAY-HASH")],
        dataset_id="career-development-replay-v1",
        dataset_classification="development_replay_only",
    )
    document = _labels_document(
        "0" * 64,
        [_label(label_id="L-HASH", case_id="C-REPLAY-HASH")],
    )

    with pytest.raises(ValueError, match="freeze_hash mismatch"):
        reveal_career_event_labels(frozen, document)


def test_reveal_rejects_unfrozen_cases_and_dataset_classification_drift() -> None:
    frozen = freeze_career_event_predictions(
        [_run("C-REPLAY-ADMITTED")],
        dataset_id="career-development-replay-v1",
        dataset_classification="development_replay_only",
    )

    with pytest.raises(ValueError, match="absent from frozen predictions"):
        reveal_career_event_labels(
            frozen,
            _labels_document(
                frozen.freeze_hash,
                [_label(label_id="L-UNKNOWN", case_id="C-REPLAY-UNKNOWN")],
            ),
        )

    drifted = _label(label_id="L-DRIFT", case_id="C-REPLAY-ADMITTED")
    drifted["dataset_classification"] = "unseen_holdout"
    with pytest.raises(ValueError, match="classification mismatch"):
        reveal_career_event_labels(
            frozen,
            _labels_document(frozen.freeze_hash, [drifted]),
        )


def test_multidimensional_score_reports_hits_abstention_and_error_rates() -> None:
    hit_run = _run("C-REPLAY-HIT")
    false_negative_run = _run("C-REPLAY-FN", qualified=False)
    false_positive_run = _run("C-REPLAY-FP")
    frozen = freeze_career_event_predictions(
        [hit_run, false_negative_run, false_positive_run],
        dataset_id="career-development-replay-v1",
        dataset_classification="development_replay_only",
    )
    hit_magnitude = project_career_event_prediction(hit_run).magnitude
    revealed = reveal_career_event_labels(
        frozen,
        _labels_document(
            frozen.freeze_hash,
            [
                _label(
                    label_id="L-HIT",
                    case_id="C-REPLAY-HIT",
                    event_type="career.promotion",
                    magnitude=hit_magnitude,
                ),
                _label(
                    label_id="L-FN",
                    case_id="C-REPLAY-FN",
                    event_type="career.transfer",
                    magnitude=0.6,
                ),
            ],
            no_event_cases=[_no_event("C-REPLAY-FP")],
        ),
    )

    score = score_career_event_replay(frozen, revealed)
    by_case = {item.case_id: item for item in score.case_scores}

    assert by_case["C-REPLAY-HIT"].timing_hit is True
    assert by_case["C-REPLAY-HIT"].event_type_hit is True
    assert by_case["C-REPLAY-HIT"].domain_hit is True
    assert by_case["C-REPLAY-HIT"].direction_hit is True
    assert by_case["C-REPLAY-HIT"].magnitude_hit is True
    assert by_case["C-REPLAY-FN"].false_negative is True
    assert by_case["C-REPLAY-FP"].false_positive is True
    assert score.metrics == {
        "case_count": 3,
        "observed_case_count": 2,
        "predicted_case_count": 2,
        "abstain_count": 1,
        "coverage": 0.666667,
        "timing_hit_rate": 0.5,
        "event_type_hit_rate": 0.5,
        "domain_hit_rate": 0.5,
        "direction_hit_rate": 0.5,
        "magnitude_hit_rate": 0.5,
        "false_positive_count": 1,
        "false_positive_rate": 1.0,
        "false_negative_count": 1,
        "false_negative_rate": 0.5,
        "promotion_eligible": "false",
    }


def test_score_distinguishes_timing_direction_and_magnitude_misses() -> None:
    run = _run("C-REPLAY-DIMENSIONS")
    frozen = freeze_career_event_predictions(
        [run],
        dataset_id="career-development-replay-v1",
        dataset_classification="development_replay_only",
    )
    revealed = reveal_career_event_labels(
        frozen,
        _labels_document(
            frozen.freeze_hash,
            [
                _label(
                    label_id="L-DIMENSIONS",
                    case_id="C-REPLAY-DIMENSIONS",
                    year=2026,
                    event_type="career.promotion",
                    direction="positive",
                    magnitude=0.0,
                )
            ],
        ),
    )

    item = score_career_event_replay(frozen, revealed, magnitude_tolerance=0.1).case_scores[0]

    assert item.timing_hit is False
    assert item.event_type_hit is True
    assert item.domain_hit is True
    assert item.direction_hit is False
    assert item.magnitude_hit is False


def test_reveal_requires_explicit_negative_labels_for_cases_without_events() -> None:
    frozen = freeze_career_event_predictions(
        [_run("C-REPLAY-UNLABELED")],
        dataset_id="career-development-replay-v1",
        dataset_classification="development_replay_only",
    )

    with pytest.raises(ValueError, match="explicit event or no-event label"):
        reveal_career_event_labels(
            frozen,
            _labels_document(frozen.freeze_hash, []),
        )


def test_freeze_api_cannot_accept_reality_or_label_inputs() -> None:
    parameters = set(inspect.signature(freeze_career_event_predictions).parameters)
    assert parameters == {"runs", "dataset_id", "dataset_classification"}
    assert parameters.isdisjoint(
        {
            "known_facts",
            "feedback",
            "verification",
            "labels",
            "revealed_labels",
            "truth",
            "calibration",
        }
    )


def test_legacy_ren_adapter_projects_timing_event_without_reality_inputs() -> None:
    chart = _qualified_chart(year=2024)

    prediction = project_legacy_ren_career_event_prediction(
        case_id="C-LEGACY-REPLAY@2024",
        chart=chart,
        window=CareerPredictionWindow(2024, 2024, "historical"),
    )

    assert prediction.model_id == LEGACY_REN_CAREER_MODEL_ID
    assert prediction.status == "predicted"
    assert prediction.predicted_start_year == 2024
    assert prediction.predicted_end_year == 2024
    assert prediction.event_type == "career.role_change"
    assert prediction.direction == "negative"
    parameters = set(inspect.signature(project_legacy_ren_career_event_prediction).parameters)
    assert parameters == {"case_id", "chart", "window"}


def test_generic_freeze_supports_one_legacy_model_and_rejects_mixed_models() -> None:
    shared = project_career_event_prediction(_run("C-SHARED-MODEL"))
    legacy = project_legacy_ren_career_event_prediction(
        case_id="C-LEGACY-MODEL",
        chart=_qualified_chart(),
        window=CareerPredictionWindow(2024, 2024, "historical"),
    )

    frozen = freeze_career_event_replay_predictions(
        [legacy],
        dataset_id="career-development-replay-legacy-v1",
        dataset_classification="development_replay_only",
    )

    assert frozen.model_id == LEGACY_REN_CAREER_MODEL_ID
    verify_frozen_career_event_replay(frozen)
    with pytest.raises(ValueError, match="mix model_id"):
        freeze_career_event_replay_predictions(
            [shared, legacy],
            dataset_id="career-development-replay-invalid-v1",
            dataset_classification="development_replay_only",
        )


def test_replay_contracts_fail_closed_on_incomplete_prediction_and_bad_label() -> None:
    with pytest.raises(ValueError, match="complete event fields"):
        CareerEventReplayPrediction(
            case_id="C-INCOMPLETE",
            model_id="career-role-change-shared-predictor-v1",
            status="predicted",
            observation_start_year=2024,
            observation_end_year=2024,
            predicted_start_year=2024,
            predicted_end_year=2024,
            domain="事业",
            event_type="career.role_change",
            direction=None,
            magnitude=0.6,
        )

    with pytest.raises(ValueError, match="unsupported historical career event_type"):
        HistoricalCareerEventLabel(
            label_id="L-BAD-TYPE",
            case_id="C-BAD-TYPE",
            start_year=2024,
            end_year=2024,
            domain="事业",
            event_type="career.unknown",
            direction="neutral",
            magnitude=0.6,
            source_ref="cases/C-BAD-TYPE/input.md",
            confidence_grade="A",
            dataset_classification="development_replay_only",
        )
