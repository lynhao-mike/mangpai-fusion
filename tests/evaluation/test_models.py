from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from engine.evaluation.models import (
    BlindPrediction,
    BlindSchoolOutput,
    BlindTask,
    CapabilityPosterior,
    CaseAuditRecord,
    FrozenBlindRun,
    RevealedLabel,
    ScoreRecord,
)


def _prediction() -> BlindPrediction:
    return BlindPrediction(
        prediction_id="P-001",
        event_label="divorce",
        probability=0.7,
        time_window={"start_year": 2015, "end_year": 2020},
        evidence_refs=["F-001"],
        falsifier="no separation through 2020",
    )


def test_three_state_output_rejects_claim_without_prediction() -> None:
    with pytest.raises(ValueError, match="claim requires at least one prediction"):
        BlindSchoolOutput(
            case_id="C-TEST-001",
            school_id="ziping",
            task_id="marriage.divorce",
            state="claim",
            rationale="structure supports event",
            predictions=[],
        )


def test_abstain_and_unsupported_reject_predictions() -> None:
    for state in ("abstain", "unsupported"):
        with pytest.raises(ValueError, match=rf"{state} cannot contain predictions"):
            BlindSchoolOutput(
                case_id="C-TEST-001",
                school_id="yang_qingjuan",
                task_id="marriage.divorce",
                state=state,
                rationale="insufficient evidence",
                predictions=[_prediction()],
            )


def test_prediction_validation() -> None:
    with pytest.raises(ValueError, match="probability must be between 0 and 1"):
        BlindPrediction("P", "event", 1.1, {}, [], "falsifier")
    with pytest.raises(ValueError, match="event_label is required"):
        BlindPrediction("P", " ", 0.5, {}, [], "falsifier")
    with pytest.raises(ValueError, match="falsifier is required"):
        BlindPrediction("P", "event", 0.5, {}, [], " ")


def test_identity_and_protocol_validation() -> None:
    with pytest.raises(ValueError, match="task_id is required"):
        BlindTask("", "career", "binary", "brier", True, False, [], [], {"type": "boolean"}, "note")
    with pytest.raises(ValueError, match="domain is required"):
        BlindTask("task", " ", "binary", "brier", True, False, [], [], {"type": "boolean"}, "note")
    with pytest.raises(ValueError, match="scoring_method is required"):
        BlindTask("task", "career", "binary", " ", True, False, [], [], {"type": "boolean"}, "note")
    with pytest.raises(ValueError, match="quantifiable task requires non-empty label_schema"):
        BlindTask("task", "career", "binary", "brier", True, False, [], [], {}, "note")
    with pytest.raises(ValueError, match="case_id is required"):
        CaseAuditRecord("", True, True, True, False, True, [], "eligible", [])
    with pytest.raises(ValueError, match="school_id is required"):
        BlindSchoolOutput("case", "", "task", "abstain", "reason")


def test_probability_rate_interval_and_n_eff_validation() -> None:
    base = dict(
        school_id="ziping",
        task_id="career.change",
        chart_prototype_id="prototype.structure-clear",
        claim_type="binary_event",
        time_horizon="ten_year",
        evidence_completeness_band="complete",
        coverage_rate=0.8,
        discrimination_score=0.2,
        accuracy_score=0.71,
        calibration_error=0.08,
        posterior_mean=0.7,
        credible_interval=(0.51, 0.84),
        n_eff=18.0,
        evidence_grade="E2",
        last_evaluated_at="2026-07-11T00:00:00Z",
    )
    for field_name in ("coverage_rate", "discrimination_score", "accuracy_score", "calibration_error", "posterior_mean"):
        values = dict(base)
        values[field_name] = 1.1
        with pytest.raises(ValueError, match=field_name):
            CapabilityPosterior(**values)
    for interval in ((-0.1, 0.5), (0.8, 0.2), (0.2, 1.1)):
        with pytest.raises(ValueError, match="credible_interval"):
            CapabilityPosterior(**{**base, "credible_interval": interval})
    with pytest.raises(ValueError, match="n_eff must be non-negative"):
        CapabilityPosterior(**{**base, "n_eff": -1.0})


def test_all_persisted_contracts_round_trip_without_aliasing() -> None:
    task = BlindTask(
        "career.change", "career", "binary_event", "brier", True, False,
        ["ten_year"], ["pillars"], {"values": [True, False]}, "blind evaluation",
    )
    audit = CaseAuditRecord("C-TEST-001", True, True, True, False, True, ["report"], "eligible", ["complete"])
    output = BlindSchoolOutput("C-TEST-001", "ziping", "career.change", "claim", "supported", [_prediction()], ["counter"])
    run = FrozenBlindRun("catalog-v1", "snapshot-1", "2026-07-11T00:00:00Z", [output], "abc")
    label = RevealedLabel("C-TEST-001", "career.change", {"changed": True}, "2020", "feedback", "E2", True, "none")
    score = ScoreRecord(
        case_id="C-TEST-001", school_id="ziping", task_id="career.change", claim_type="binary_event",
        state="claim", probability_score=0.8, utility=-0.1, observed_positive=True,
        abstained=False, knowledge_coverage=True,
    )
    posterior = CapabilityPosterior(
        school_id="ziping", task_id="career.change", chart_prototype_id="prototype.structure-clear",
        claim_type="binary_event", time_horizon="ten_year", evidence_completeness_band="complete",
        coverage_rate=0.8, discrimination_score=0.2, accuracy_score=0.71, calibration_error=0.08,
        posterior_mean=0.7, credible_interval=(0.51, 0.84), n_eff=18.0,
        evidence_grade="E2", last_evaluated_at="2026-07-11T00:00:00Z",
    )
    for value in (task, audit, output, run, label, score, posterior):
        restored = type(value).from_dict(value.to_dict())
        assert restored == value
        with pytest.raises(FrozenInstanceError):
            restored.task_id = "changed"

    run_data = run.to_dict()
    assert run_data["schema_version"] == "school-capability-frozen-run/v1"
    assert isinstance(run_data["outputs"][0], dict)
    restored_run = FrozenBlindRun.from_dict(run_data)
    assert isinstance(restored_run.outputs[0], BlindSchoolOutput)
    assert isinstance(restored_run.outputs[0].predictions[0], BlindPrediction)

    posterior_data = posterior.to_dict()
    assert posterior_data["credible_interval"] == [0.51, 0.84]
    assert CapabilityPosterior.from_dict(posterior_data).credible_interval == (0.51, 0.84)

    task_data = task.to_dict()
    task_data["label_schema"]["values"].append("mutated")
    assert task.label_schema == {"values": [True, False]}
    label_data = label.to_dict()
    label_data["label"]["changed"] = False
    assert label.label == {"changed": True}


def test_score_defaults_and_negative_fields_are_supported() -> None:
    score = ScoreRecord(
        case_id="C", school_id="S", task_id="T", claim_type="binary", state="abstain",
        utility=-1.0, abstained=True, knowledge_coverage=False,
    )
    assert score.chart_prototype_id == "unclassified"
    assert score.time_horizon == "unspecified"
    assert score.evidence_completeness_band == "unknown"
    assert score.probability_score is None
    assert score.timing_score is None
    assert score.ordinal_score is None
    assert score.portrait_agreement is None

    posterior = CapabilityPosterior(
        "S", "T", "P", "binary", "year", "complete", 0.5, 0.5, 0.5,
        None, 0.5, (0.2, 0.8), 0.0, "E3", "now", incremental_gain=-0.2,
    )
    assert posterior.incremental_gain == -0.2
