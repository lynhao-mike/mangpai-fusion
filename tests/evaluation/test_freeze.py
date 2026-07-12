import json
from pathlib import Path

import pytest

from engine.evaluation.freeze import freeze_outputs, reveal_labels, verify_frozen_run
from engine.evaluation.models import BlindPrediction, BlindSchoolOutput


def _output(
    *,
    case_id: str = "C-TEST-001",
    school_id: str = "ziping",
    task_id: str = "marriage.divorce_or_remarriage",
    prediction_ids: tuple[str, ...] = ("P-001",),
) -> BlindSchoolOutput:
    return BlindSchoolOutput(
        case_id=case_id,
        school_id=school_id,
        task_id=task_id,
        state="claim",
        rationale="spouse structure is unstable",
        predictions=[
            BlindPrediction(
                prediction_id=prediction_id,
                event_label="occurred",
                probability=0.7,
                time_window={"start_year": 2015, "end_year": 2020},
                evidence_refs=["F-001"],
                falsifier="no divorce or remarriage observed",
            )
            for prediction_id in prediction_ids
        ],
    )


def test_freeze_is_canonical_and_repeatable_for_same_input() -> None:
    outputs = [
        _output(case_id="C-TEST-002", prediction_ids=("P-002", "P-001")),
        _output(case_id="C-TEST-001"),
    ]

    first = freeze_outputs(outputs, "tasks-v1", "rules-v1")
    second = freeze_outputs(reversed(outputs), "tasks-v1", "rules-v1")

    assert first.freeze_hash == second.freeze_hash
    assert [output.case_id for output in first.outputs] == ["C-TEST-001", "C-TEST-002"]
    assert [item.prediction_id for item in first.outputs[1].predictions] == ["P-001", "P-002"]


@pytest.mark.parametrize(
    ("field", "changed"),
    [
        ("task_catalog_version", "tasks-v2"),
        ("rule_snapshot_id", "rules-v2"),
        ("frozen_at", "2099-01-01T00:00:00Z"),
        ("schema_version", "school-capability-frozen-run/v2"),
    ],
)
def test_verify_rejects_tampered_run_metadata(field: str, changed: str) -> None:
    run = freeze_outputs([_output()], "tasks-v1", "rules-v1")
    altered = run.to_dict()
    altered[field] = changed

    with pytest.raises(ValueError, match="freeze hash mismatch"):
        verify_frozen_run(type(run).from_dict(altered))


def test_verify_rejects_tampered_output() -> None:
    run = freeze_outputs([_output()], "tasks-v1", "rules-v1")
    altered = run.to_dict()
    altered["outputs"][0]["rationale"] = "changed after freeze"

    with pytest.raises(ValueError, match="freeze hash mismatch"):
        verify_frozen_run(type(run).from_dict(altered))


def test_reveal_rejects_wrong_freeze_hash_before_parsing_labels(tmp_path: Path) -> None:
    run = freeze_outputs([_output()], "tasks-v1", "rules-v1")
    path = tmp_path / "labels.json"
    path.write_text(
        json.dumps({
            "schema_version": "school-capability-labels/v1",
            "freeze_hash": "wrong",
            "labels": [{"not": "a valid label"}],
        }),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="freeze_hash"):
        reveal_labels(run, path)


def test_reveal_verifies_run_before_reading_labels(tmp_path: Path) -> None:
    run = freeze_outputs([_output()], "tasks-v1", "rules-v1")
    altered = run.to_dict()
    altered["outputs"][0]["rationale"] = "tampered"

    with pytest.raises(ValueError, match="freeze hash mismatch"):
        reveal_labels(type(run).from_dict(altered), tmp_path / "missing.json")


def test_reveal_returns_valid_labels_for_exact_freeze_hash(tmp_path: Path) -> None:
    run = freeze_outputs([_output()], "tasks-v1", "rules-v1")
    path = tmp_path / "labels.json"
    path.write_text(
        json.dumps({
            "schema_version": "school-capability-labels/v1",
            "freeze_hash": run.freeze_hash,
            "labels": [{
                "case_id": "C-TEST-001",
                "task_id": "marriage.divorce_or_remarriage",
                "label": "occurred",
                "observed_at": "2026-01-01",
                "source": "feedback.md",
                "confidence_grade": "A",
                "quantifiable": True,
                "conflict_state": "none",
            }],
        }),
        encoding="utf-8",
    )

    labels = reveal_labels(run, path)

    assert len(labels) == 1
    assert labels[0].label == "occurred"
