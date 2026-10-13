from __future__ import annotations

import inspect

import pytest


def test_duan_semantic_adapter_abstains_on_tied_scores() -> None:
    from tools.p_series_career_blind_harness import decide_duan_career_path

    result = decide_duan_career_path(
        employment_score=5,
        entrepreneurship_score=5,
        branch_conflict_intensity=0.5,
    )

    assert result["prediction"] == "abstain"
    assert result["reason"] == "duan_runner_mixed_not_allowed"


def test_score_excludes_mixed_truth_from_strict_binary_metrics() -> None:
    from tools.p_series_career_blind_harness import score_predictions

    result = score_predictions(
        predictions=[
            {"case_id": "P-1", "prediction": "employment"},
            {"case_id": "P-2", "prediction": "entrepreneurship"},
            {"case_id": "P-3", "prediction": "employment"},
        ],
        labels={"P-1": "employment", "P-2": "entrepreneurship", "P-3": "mixed"},
    )

    assert result["strict_binary_count"] == 2
    assert result["mixed_holdout_count"] == 1
    assert result["confusion_matrix"] == {
        "employment": {"employment": 1, "entrepreneurship": 0, "abstain": 0},
        "entrepreneurship": {"employment": 0, "entrepreneurship": 1, "abstain": 0},
    }
    assert result["accuracy"] == 1.0
    assert result["balanced_accuracy"] == 1.0


def test_score_counts_abstain_as_uncovered_and_not_correct() -> None:
    from tools.p_series_career_blind_harness import score_predictions

    result = score_predictions(
        predictions=[
            {"case_id": "P-1", "prediction": "abstain"},
            {"case_id": "P-2", "prediction": "entrepreneurship"},
        ],
        labels={"P-1": "employment", "P-2": "entrepreneurship"},
    )

    assert result["abstain_count"] == 1
    assert result["coverage"] == 0.5
    assert result["accuracy"] == 0.5
    assert result["recall"] == {"employment": 0.0, "entrepreneurship": 1.0}


def test_prediction_function_has_no_label_or_feedback_dependency() -> None:
    from tools.p_series_career_blind_harness import predict_from_manifest

    source = inspect.getsource(predict_from_manifest).lower()
    assert "_read_jsonl" not in source
    assert "feedback" not in source


@pytest.mark.parametrize("prediction", ["mixed", "unknown", ""])
def test_score_rejects_non_contract_prediction(prediction: str) -> None:
    from tools.p_series_career_blind_harness import score_predictions

    with pytest.raises(ValueError, match="prediction"):
        score_predictions(
            predictions=[{"case_id": "P-1", "prediction": prediction}],
            labels={"P-1": "employment"},
        )
