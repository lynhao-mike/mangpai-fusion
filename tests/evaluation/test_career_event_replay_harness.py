from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

import tools.career_event_replay_harness as harness
from tools.career_event_replay_harness import (
    compare_scored_replay,
    main,
    predict_and_freeze_blind_cohort,
    reveal_and_score_frozen_replay,
)


BLIND_COHORT = Path(
    "META/as-of-evaluation/career-event-development-replay-blind-cohort-v1.json"
)
LABELS = Path("META/as-of-evaluation/career-event-development-replay-labels-v1.json")


def _document(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _pipeline() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    frozen = predict_and_freeze_blind_cohort(_document(BLIND_COHORT))
    scored = reveal_and_score_frozen_replay(frozen, _document(LABELS))
    compared = compare_scored_replay(scored)
    return frozen, scored, compared


def test_real_development_replay_compares_same_explicit_cohort() -> None:
    frozen, scored, payload = _pipeline()

    assert frozen["schema_version"] == (
        "career-event-development-replay-freeze-bundle/v1"
    )
    assert scored["schema_version"] == (
        "career-event-development-replay-score-bundle/v1"
    )
    assert payload["schema_version"] == (
        "career-event-development-replay-comparison/v1"
    )
    assert payload["dataset_classification"] == "development_replay_only"
    assert payload["promotion_eligible"] is False
    assert payload["unseen_holdout_evidence"] == "none"
    assert payload["replay_unit_count"] == 10
    assert len(payload["blind_cohort_digest"]) == 64
    assert len(payload["labels_digest"]) == 64
    assert len(payload["freeze_bundle_hash"]) == 64
    assert len(payload["score_bundle_hash"]) == 64
    assert len(payload["comparison_hash"]) == 64

    legacy = payload["legacy"]
    shared = payload["shared"]
    assert legacy["freeze"]["predictions"]
    assert shared["freeze"]["predictions"]
    assert {item["case_id"] for item in legacy["freeze"]["predictions"]} == {
        item["case_id"] for item in shared["freeze"]["predictions"]
    }
    assert legacy["freeze"]["model_id"] != shared["freeze"]["model_id"]
    assert legacy["score"]["metrics"]["case_count"] == 10
    assert shared["score"]["metrics"]["case_count"] == 10
    assert legacy["score"]["metrics"]["promotion_eligible"] == "false"
    assert shared["score"]["metrics"]["promotion_eligible"] == "false"


def test_structure_gate_reduces_coverage_and_false_positives_on_development_replay() -> None:
    _, _, payload = _pipeline()
    legacy = payload["legacy"]["score"]["metrics"]
    shared = payload["shared"]["score"]["metrics"]

    assert shared["predicted_case_count"] < legacy["predicted_case_count"]
    assert shared["coverage"] < legacy["coverage"]
    assert shared["false_positive_count"] < legacy["false_positive_count"]
    assert shared["false_negative_count"] > legacy["false_negative_count"]
    assert payload["metric_delta_shared_minus_legacy"]["coverage"] < 0
    assert payload["metric_delta_shared_minus_legacy"]["false_positive_count"] < 0


def test_blind_artifact_contains_no_label_or_reality_fields() -> None:
    document = _document(BLIND_COHORT)
    encoded = json.dumps(document, ensure_ascii=False).lower()

    assert set(document) == {
        "schema_version",
        "dataset_id",
        "dataset_classification",
        "promotion_eligible",
        "unseen_holdout_evidence",
        "normalization_policy",
        "charts",
        "replay_units",
    }
    for forbidden in (
        '"labels"',
        '"no_event_cases"',
        '"source_ref"',
        '"confidence_grade"',
        '"known_facts"',
        '"feedback"',
        '"verification"',
        '"observed"',
        '"calibration"',
    ):
        assert forbidden not in encoded


def test_predict_freeze_cli_never_reads_labels_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "freeze.json"
    original = harness._read_json
    opened: list[Path] = []

    def guarded(path: Path) -> dict[str, object]:
        resolved = Path(path)
        opened.append(resolved)
        if resolved == LABELS:
            raise AssertionError("predict-freeze must not open labels artifact")
        return original(resolved)

    monkeypatch.setattr(harness, "_read_json", guarded)

    assert main(
        [
            "predict-freeze",
            "--blind-cohort",
            str(BLIND_COHORT),
            "--out-freeze",
            str(output),
        ]
    ) == 0
    assert opened == [BLIND_COHORT]
    assert output.exists()


def test_reveal_score_validates_freeze_before_opening_labels(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invalid_freeze = tmp_path / "invalid-freeze.json"
    invalid_freeze.write_text(
        json.dumps(
            {
                "schema_version": "career-event-development-replay-freeze-bundle/v1",
                "freeze_bundle_hash": "0" * 64,
            }
        ),
        encoding="utf-8",
    )
    opened: list[Path] = []
    original = harness._read_json

    def guarded(path: Path) -> dict[str, object]:
        resolved = Path(path)
        opened.append(resolved)
        if resolved == LABELS:
            raise AssertionError("labels must not open before freeze validation")
        return original(resolved)

    monkeypatch.setattr(harness, "_read_json", guarded)

    with pytest.raises(ValueError, match="freeze bundle schema"):
        main(
            [
                "reveal-score",
                "--freeze",
                str(invalid_freeze),
                "--labels",
                str(LABELS),
                "--out-score",
                str(tmp_path / "score.json"),
            ]
        )
    assert opened == [invalid_freeze]


def test_predict_freeze_rejects_embedded_revealed_fields() -> None:
    document = _document(BLIND_COHORT)
    document["labels"] = []

    with pytest.raises(ValueError, match="blind cohort schema"):
        predict_and_freeze_blind_cohort(document)


def test_phase_apis_enforce_separate_inputs() -> None:
    predict_parameters = set(
        inspect.signature(predict_and_freeze_blind_cohort).parameters
    )
    reveal_parameters = set(
        inspect.signature(reveal_and_score_frozen_replay).parameters
    )
    compare_parameters = set(inspect.signature(compare_scored_replay).parameters)

    assert predict_parameters == {"blind_document"}
    assert reveal_parameters == {"freeze_bundle", "labels_document"}
    assert compare_parameters == {"score_bundle"}
    assert predict_parameters.isdisjoint(
        {
            "labels_document",
            "known_facts",
            "feedback",
            "verification",
            "calibration",
        }
    )
