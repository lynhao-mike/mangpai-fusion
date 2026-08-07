from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools.career_path_competition_harness import (
    MODEL_IDS,
    assert_formal_model_eligibility,
    current_status,
    freeze_predictions,
    predict_competition,
    score_competition,
)


def _json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_current_repository_is_not_ready_and_does_not_score() -> None:
    result = current_status()

    assert result["status"] == "not_ready"
    assert result["failures"] == ["unseen_holdout_not_registered"]
    assert result["production_switch_permitted"] is False


def test_invalidated_relation_model_is_not_formally_scoreable() -> None:
    with pytest.raises(ValueError, match="invalidated.*new model_id and preregistration"):
        assert_formal_model_eligibility()


def test_unknown_disposition_is_not_treated_as_validated_theory(tmp_path: Path) -> None:
    disposition = tmp_path / "disposition.json"
    _json(
        disposition,
        {
            "model_id": MODEL_IDS[2],
            "formal_scoring_status": "unknown",
            "theory_fidelity": "unsupported",
        },
    )

    with pytest.raises(ValueError, match="not explicitly eligible"):
        assert_formal_model_eligibility(disposition)


def test_audit_matrix_marks_terminal_chains_unsupported_and_unresolved_as_unvalidated() -> None:
    matrix = json.loads(
        Path("META/as-of-evaluation/career-relation-model-v1-fidelity-matrix.json").read_text(
            encoding="utf-8"
        )
    )
    by_id = {row["rule_id"]: row for row in matrix["rules"]}

    assert by_id["CR-NATAL-EMPLOYMENT-CHAIN"]["status"] == "unsupported"
    assert by_id["CR-NATAL-ENTREPRENEURSHIP-CHAIN"]["status"] == "unsupported"
    assert by_id["CR-LOCATOR-STEP-2"]["status"] == "unresolved"
    assert by_id["CR-LOCATOR-STEP-5"]["status"] == "unresolved"
    assert all(
        row["validated_theory"] is False
        for row in by_id.values()
        if row["status"] in {"unsupported", "unresolved"}
    )


def test_predict_rejects_label_or_feedback_fields_before_model_execution(tmp_path: Path) -> None:
    prereg = tmp_path / "prereg.json"
    prepare = tmp_path / "prepare.json"
    blind = tmp_path / "blind.jsonl"
    _json(prereg, {"preregistration_id": "PRE-1"})
    _json(
        prepare,
        {
            "stage": "prepare",
            "contract": "case_ids_only_no_labels",
            "preregistration_path": prereg.as_posix(),
            "preregistration_sha256": _sha(prereg),
            "case_ids": ["H-1"],
        },
    )
    _jsonl(
        blind,
        [{"case_id": "H-1", "four_pillars": ["甲子", "乙丑", "丙寅", "丁卯"], "feedback": "leak"}],
    )

    with pytest.raises(ValueError, match="forbidden blind field"):
        predict_competition(prepare, blind, tmp_path / "predictions.jsonl")


def test_freeze_rejects_preregistration_id_mismatch(tmp_path: Path) -> None:
    prereg = tmp_path / "prereg.json"
    prepare = tmp_path / "prepare.json"
    predictions = tmp_path / "predictions.jsonl"
    _json(prereg, {"preregistration_id": "PRE-2"})
    _json(
        prepare,
        {
            "preregistration_id": "PRE-1",
            "preregistration_sha256": _sha(prereg),
            "cohort_sha256": "c" * 64,
            "case_ids": ["H-1"],
            "case_count": 1,
        },
    )
    _jsonl(
        predictions,
        [
            {"case_id": "H-1", "model_id": model, "prediction": "abstain", "trace": {"ok": True}}
            for model in MODEL_IDS
        ],
    )

    with pytest.raises(ValueError, match="preregistration_id mismatch"):
        freeze_predictions(prepare, predictions, tmp_path / "freeze.json", preregistration_path=prereg)


def test_freeze_rejects_tampered_preregistration_hash(tmp_path: Path) -> None:
    prereg = tmp_path / "prereg.json"
    prepare = tmp_path / "prepare.json"
    predictions = tmp_path / "predictions.jsonl"
    _json(prereg, {"preregistration_id": "PRE-1"})
    _json(
        prepare,
        {
            "preregistration_id": "PRE-1",
            "preregistration_sha256": "0" * 64,
            "cohort_sha256": "c" * 64,
            "case_ids": ["H-1"],
            "case_count": 1,
        },
    )
    _jsonl(predictions, [])

    with pytest.raises(ValueError, match="preregistration hash mismatch"):
        freeze_predictions(prepare, predictions, tmp_path / "freeze.json", preregistration_path=prereg)


def test_score_rejects_invalidated_model_before_formal_metrics(tmp_path: Path) -> None:
    predictions = tmp_path / "predictions.jsonl"
    labels = tmp_path / "labels.jsonl"
    freeze = tmp_path / "freeze.json"
    reveal = tmp_path / "reveal.json"
    _jsonl(
        predictions,
        [
            {"case_id": "H-1", "model_id": model, "prediction": "employment", "trace": {"ok": True}}
            for model in MODEL_IDS
        ],
    )
    _jsonl(labels, [{"case_id": "H-1", "label": "employment"}])
    _json(
        freeze,
        {
            "preregistration_id": "PRE-1",
            "predictions_path": predictions.as_posix(),
            "predictions_sha256": _sha(predictions),
            "case_ids": ["H-1"],
        },
    )
    _json(
        reveal,
        {
            "freeze_path": freeze.as_posix(),
            "freeze_sha256": _sha(freeze),
            "labels_path": labels.as_posix(),
            "labels_sha256": _sha(labels),
            "label_schema": "legacy_label_v1",
        },
    )

    with pytest.raises(ValueError, match="invalidated.*new model_id and preregistration"):
        score_competition(reveal, tmp_path / "score.json", tmp_path / "receipt.json")
    assert not (tmp_path / "score.json").exists()
    assert not (tmp_path / "receipt.json").exists()


def test_score_rejects_tampered_predictions_and_duplicate_score(tmp_path: Path) -> None:
    predictions = tmp_path / "predictions.jsonl"
    labels = tmp_path / "labels.jsonl"
    freeze = tmp_path / "freeze.json"
    reveal = tmp_path / "reveal.json"
    receipt = tmp_path / "receipt.json"
    _jsonl(
        predictions,
        [
            {"case_id": "H-1", "model_id": model, "prediction": "employment", "trace": {"ok": True}}
            for model in MODEL_IDS
        ],
    )
    _jsonl(labels, [{"case_id": "H-1", "label": "employment"}])
    _json(
        freeze,
        {
            "preregistration_id": "PRE-1",
            "predictions_path": predictions.as_posix(),
            "predictions_sha256": _sha(predictions),
            "case_ids": ["H-1"],
        },
    )
    _json(
        reveal,
        {
            "freeze_path": freeze.as_posix(),
            "freeze_sha256": _sha(freeze),
            "labels_path": labels.as_posix(),
            "labels_sha256": _sha(labels),
            "label_schema": "legacy_label_v1",
        },
    )
    _json(receipt, {"preregistration_id": "PRE-1"})

    with pytest.raises(ValueError, match="already been scored"):
        score_competition(reveal, tmp_path / "score.json", receipt)

    receipt.unlink()
    predictions.write_text(predictions.read_text(encoding="utf-8") + "{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="prediction hash mismatch"):
        score_competition(reveal, tmp_path / "score.json", receipt)
