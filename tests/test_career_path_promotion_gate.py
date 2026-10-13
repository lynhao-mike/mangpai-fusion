from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.career_path_promotion_gate import (
    PROMOTION_REQUIREMENTS,
    check_promotion_eligibility,
)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _fixture(tmp_path: Path, predictions: list[dict], labels: list[dict], *, one_shot: bool = True) -> tuple[Path, Path, Path]:
    predictions_path = tmp_path / "predictions.jsonl"
    labels_path = tmp_path / "labels.jsonl"
    freeze_path = tmp_path / "freeze.json"
    _write_jsonl(predictions_path, predictions)
    _write_jsonl(labels_path, labels)
    freeze_path.write_text(
        json.dumps(
            {
                "one_shot_freeze": one_shot,
                "case_count": len(predictions),
                "predictions_path": predictions_path.as_posix(),
                "predictions_sha256": hashlib.sha256(predictions_path.read_bytes()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    return predictions_path, labels_path, freeze_path


def test_promotion_requirements_are_frozen() -> None:
    assert PROMOTION_REQUIREMENTS == {
        "min_holdout_cases": 30,
        "min_balanced_accuracy": 0.60,
        "min_employment_recall": 0.55,
        "min_entrepreneurship_recall": 0.55,
        "min_coverage": 0.70,
        "beats_majority_baseline": True,
        "beats_frozen_baseline_balanced_acc": 0.425,
        "one_shot_freeze_required": True,
    }


def test_eligible_balanced_predictions_pass(tmp_path: Path) -> None:
    labels = [
        {"case_id": f"E-{i}", "label": "employment"} for i in range(15)
    ] + [{"case_id": f"B-{i}", "label": "entrepreneurship"} for i in range(15)]
    predictions = [
        {"case_id": row["case_id"], "prediction": row["label"]} for row in labels
    ]
    paths = _fixture(tmp_path, predictions, labels)

    result = check_promotion_eligibility(*paths)

    assert result["eligible"] is True
    assert result["failures"] == []
    assert all(result["checks"].values())


def test_current_frozen_classifier_fails_promotion() -> None:
    result = check_promotion_eligibility(
        Path("predictions/p-series-career-path-classifier-v1.jsonl"),
        Path("cases/p-series-career-path-labels.jsonl"),
        Path("META/as-of-evaluation/p-series-career-path-classifier-freeze-v1.json"),
    )

    assert result["eligible"] is False
    assert result["metrics"]["balanced_accuracy"] == 0.3625
    assert result["checks"]["beats_frozen_baseline_balanced_acc"] is False


def test_prediction_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    labels = [{"case_id": f"E-{i}", "label": "employment"} for i in range(30)]
    predictions = [{"case_id": row["case_id"], "prediction": "employment"} for row in labels]
    predictions_path, labels_path, freeze_path = _fixture(tmp_path, predictions, labels)
    predictions_path.write_text(predictions_path.read_text(encoding="utf-8") + "{}\n", encoding="utf-8")

    result = check_promotion_eligibility(predictions_path, labels_path, freeze_path)

    assert result["eligible"] is False
    assert result["checks"]["predictions_hash_matches_freeze"] is False


def test_missing_one_shot_freeze_fails_closed(tmp_path: Path) -> None:
    labels = [{"case_id": f"E-{i}", "label": "employment"} for i in range(30)]
    predictions = [{"case_id": row["case_id"], "prediction": "employment"} for row in labels]
    paths = _fixture(tmp_path, predictions, labels, one_shot=False)

    result = check_promotion_eligibility(*paths)

    assert result["eligible"] is False
    assert result["checks"]["one_shot_freeze_required"] is False


def test_explicit_temporal_schema_preserves_mixed_and_transitioning_denominators(tmp_path: Path) -> None:
    labels = [
        {"case_id": f"E-{i}", "reality_status_at_feedback": "employed"}
        for i in range(15)
    ] + [
        {"case_id": f"B-{i}", "reality_status_at_feedback": "entrepreneurial"}
        for i in range(15)
    ] + [
        {"case_id": "M-1", "reality_status_at_feedback": "mixed"},
        {"case_id": "T-1", "reality_status_at_feedback": "transitioning"},
    ]
    predictions = [
        {
            "case_id": row["case_id"],
            "prediction": {
                "employed": "employment",
                "entrepreneurial": "entrepreneurship",
                "mixed": "mixed",
                "transitioning": "transitioning",
            }[row["reality_status_at_feedback"]],
        }
        for row in labels
    ]
    paths = _fixture(tmp_path, predictions, labels)

    result = check_promotion_eligibility(*paths, label_schema="career_path_temporal_v1")

    assert result["eligible"] is True
    assert result["metrics"]["mixed_recognition"] == {"value": 1.0, "denominator": 1}
    assert result["metrics"]["transitioning_recognition"] == {"value": 1.0, "denominator": 1}


def test_unknown_label_schema_is_rejected_without_field_guessing(tmp_path: Path) -> None:
    labels = [{"case_id": f"E-{i}", "some_label": "employment"} for i in range(30)]
    predictions = [{"case_id": row["case_id"], "prediction": "employment"} for row in labels]
    paths = _fixture(tmp_path, predictions, labels)

    result = check_promotion_eligibility(*paths, label_schema="guessed-v9")

    assert result["eligible"] is False
    assert result["failures"][0].startswith("invalid_gate_input:unknown label schema")


def test_threshold_values_are_inclusive_but_baseline_comparison_is_strict(tmp_path: Path) -> None:
    labels = [
        {"case_id": f"E-{i}", "label": "employment"} for i in range(15)
    ] + [{"case_id": f"B-{i}", "label": "entrepreneurship"} for i in range(15)]
    predictions = []
    for index, row in enumerate(labels):
        truth = row["label"]
        prediction = truth if index % 5 != 0 else (
            "entrepreneurship" if truth == "employment" else "employment"
        )
        predictions.append({"case_id": row["case_id"], "prediction": prediction})
    paths = _fixture(tmp_path, predictions, labels)

    result = check_promotion_eligibility(*paths)

    assert result["metrics"]["balanced_accuracy"] == 0.8
    assert result["checks"]["min_balanced_accuracy"] is True
    assert result["checks"]["beats_majority_baseline"] is True
