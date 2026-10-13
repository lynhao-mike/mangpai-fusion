from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.career_path_product_routing import evaluate_product_route, repository_product_status


OLD_MODEL_ID = "career-path-relation-model-v1"
NEW_MODEL_ID = "career-path-relation-model-v2"
TERMINAL_CHECKS = {
    "min_balanced_accuracy": True,
    "min_employment_recall": True,
    "min_entrepreneurship_recall": True,
    "min_coverage": True,
    "beats_majority_baseline": True,
    "beats_frozen_counting_baseline": True,
}


def _json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _artifacts(
    tmp_path: Path,
    *,
    terminal_passes: bool,
    structural: str = "passes",
    model_id: str = NEW_MODEL_ID,
) -> dict[str, Path]:
    prereg = tmp_path / "prereg.json"
    disposition = tmp_path / "disposition.json"
    predictions = tmp_path / "predictions.jsonl"
    labels = tmp_path / "labels.jsonl"
    freeze = tmp_path / "freeze.json"
    reveal = tmp_path / "reveal.json"
    score = tmp_path / "score.json"
    receipt = tmp_path / "receipt.json"

    structural_gate = {
        "metrics": {
            "career_pillar_location_consistency": {"minimum": 0.70, "minimum_denominator": 10},
            "trace_completeness": {"minimum": 0.95, "minimum_denominator": 30},
        },
        "required_evidence": ["expert_double_review"],
    }
    prereg_value = {
        "schema_version": "career-path-holdout-preregistration/v2",
        "preregistration_id": "PRE-V2",
        "status": "holdout_frozen_awaiting_predictions",
        "holdout_ready": True,
        "labels_revealed": False,
        "models": [{"model_id": model_id, "role": "candidate"}],
        "promotion_thresholds": {"frozen": True},
        "freeze_policy": {"one_shot_freeze": True, "one_score_only": True, "post_label_tuning_permitted": False},
    }
    if structural != "missing":
        prereg_value["structural_assistant_gate"] = structural_gate
    _json(prereg, prereg_value)
    _json(
        disposition,
        {
            "model_id": model_id,
            "decision": "eligible_for_new_model_formal_scoring",
            "formal_scoring_status": "eligible",
            "holdout_scoring_permitted": True,
            "promotion_eligible": True,
            "production_switch_permitted": False,
        },
    )
    predictions.write_text('{"case_id":"H-1"}\n', encoding="utf-8")
    labels.write_text('{"case_id":"H-1","label":"employment"}\n', encoding="utf-8")
    cohort_sha = "c" * 64
    _json(
        freeze,
        {
            "stage": "freeze",
            "one_shot_freeze": True,
            "one_score_only": True,
            "preregistration_id": "PRE-V2",
            "preregistration_sha256": _sha(prereg),
            "cohort_sha256": cohort_sha,
            "predictions_path": predictions.as_posix(),
            "predictions_sha256": _sha(predictions),
            "models": [model_id],
            "case_ids": ["H-1"],
        },
    )
    _json(
        reveal,
        {
            "stage": "reveal",
            "freeze_path": freeze.as_posix(),
            "freeze_sha256": _sha(freeze),
            "labels_path": labels.as_posix(),
            "labels_sha256": _sha(labels),
        },
    )
    checks = dict(TERMINAL_CHECKS)
    if not terminal_passes:
        checks["min_balanced_accuracy"] = False
    structural_value = 0.80 if structural == "passes" else 0.60
    score_value = {
        "schema_version": "career-path-competition-score/v2",
        "stage": "score",
        "preregistration_id": "PRE-V2",
        "preregistration_sha256": _sha(prereg),
        "cohort_sha256": cohort_sha,
        "predictions_sha256": _sha(predictions),
        "labels_sha256": _sha(labels),
        "freeze_sha256": _sha(freeze),
        "model_id": model_id,
        "disposition_sha256": _sha(disposition),
        "one_score_only": True,
        "admission_checks": {"cohort_ready": True, "labels_valid": True, "no_leakage": True},
        "promotion_checks": checks,
        "metrics": {
            model_id: {
                "career_pillar_location_consistency": {"value": structural_value, "denominator": 12},
                "trace_completeness": {"value": 1.0, "denominator": 30},
            }
        },
        "structural_evidence": ["expert_double_review"],
    }
    _json(score, score_value)
    _json(
        receipt,
        {
            "schema_version": "career-path-score-receipt/v2",
            "preregistration_id": "PRE-V2",
            "preregistration_sha256": _sha(prereg),
            "cohort_sha256": cohort_sha,
            "predictions_sha256": _sha(predictions),
            "labels_sha256": _sha(labels),
            "freeze_sha256": _sha(freeze),
            "model_id": model_id,
            "disposition_sha256": _sha(disposition),
            "score_sha256": _canonical_sha(score_value),
            "one_score_only": True,
        },
    )
    return {
        "preregistration_path": prereg,
        "disposition_path": disposition,
        "freeze_path": freeze,
        "reveal_path": reveal,
        "score_path": score,
        "receipt_path": receipt,
    }


def test_terminal_pass_routes_only_to_shadow_candidate(tmp_path: Path) -> None:
    result = evaluate_product_route(**_artifacts(tmp_path, terminal_passes=True))

    assert result["state"] == "shadow_candidate"
    assert result["production_switch_permitted"] is False


def test_terminal_failure_with_preregistered_structure_routes_to_assistant(tmp_path: Path) -> None:
    result = evaluate_product_route(**_artifacts(tmp_path, terminal_passes=False))

    assert result["state"] == "structural_evidence_assistant"
    assert result["structural_evidence_status"] == "passed"
    assert result["production_switch_permitted"] is False


def test_terminal_and_preregistered_structure_failure_is_rejected(tmp_path: Path) -> None:
    result = evaluate_product_route(
        **_artifacts(tmp_path, terminal_passes=False, structural="fails")
    )

    assert result["state"] == "rejected"
    assert result["production_switch_permitted"] is False


def test_missing_structural_thresholds_fail_closed_as_not_evaluable(tmp_path: Path) -> None:
    result = evaluate_product_route(
        **_artifacts(tmp_path, terminal_passes=False, structural="missing")
    )

    assert result["state"] == "blocked_not_ready"
    assert result["structural_evidence_status"] == "not_evaluable"
    assert "structural_assistant_gate_not_preregistered" in result["failures"]


def test_hash_tampering_is_rejected(tmp_path: Path) -> None:
    paths = _artifacts(tmp_path, terminal_passes=True)
    score = json.loads(paths["score_path"].read_text(encoding="utf-8"))
    score["predictions_sha256"] = "0" * 64
    _json(paths["score_path"], score)

    result = evaluate_product_route(**paths)

    assert result["state"] == "rejected"
    assert "predictions_hash_mismatch" in result["failures"]


def test_duplicate_or_non_unique_score_receipt_is_rejected(tmp_path: Path) -> None:
    paths = _artifacts(tmp_path, terminal_passes=True)
    receipt = json.loads(paths["receipt_path"].read_text(encoding="utf-8"))
    receipt["one_score_only"] = False
    _json(paths["receipt_path"], receipt)

    result = evaluate_product_route(**paths)

    assert result["state"] == "rejected"
    assert "score_uniqueness_not_proven" in result["failures"]


def test_invalidated_v1_can_never_be_promoted(tmp_path: Path) -> None:
    paths = _artifacts(tmp_path, terminal_passes=True, model_id=OLD_MODEL_ID)
    disposition = json.loads(paths["disposition_path"].read_text(encoding="utf-8"))
    disposition.update(
        {
            "decision": "invalidated_requires_new_model_id",
            "formal_scoring_status": "invalidated",
            "holdout_scoring_permitted": False,
            "promotion_eligible": False,
        }
    )
    _json(paths["disposition_path"], disposition)

    result = evaluate_product_route(**paths)

    assert result["state"] == "blocked_not_ready"
    assert "invalidated_model_id" in result["failures"]


def test_current_repository_is_blocked_with_holdout_and_model_evidence() -> None:
    result = repository_product_status()

    assert result["state"] == "blocked_not_ready"
    assert "unseen_holdout_not_registered" in result["failures"]
    assert "invalidated_model_id" in result["failures"]
    assert result["production_switch_permitted"] is False
