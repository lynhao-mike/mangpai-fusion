from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from engine.evaluation.freeze import freeze_outputs
from engine.evaluation.models import BlindPrediction, BlindSchoolOutput
from engine.evaluation.prospective_artifacts import (
    ArtifactRef,
    canonical_artifact_sha256,
    publish_new_json,
)
from engine.evaluation.prospective_gates import (
    GateEvidence,
    _future_label_rows_from_manifests,
    _label_rows_from_manifests,
    build_cohort_manifest,
    build_future_gate_evidence_from_cohorts,
    build_gate_evidence_from_cohorts,
    build_three_gate_report,
    evaluate_future_empirical,
    evaluate_prediction_capability_candidate,
)


EVALUATED_AT = "2026-12-01T00:00:00Z"
PARENT_AT = "2026-11-30T00:00:00Z"
EVIDENCE_CLASS = "prediction_first_immediate_retrospective"


def _ref(path: Path) -> dict[str, str]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return {"artifact_path": path.as_posix(), "artifact_sha256": document["artifact_sha256"]}


def _publish(path: Path, payload: dict) -> Path:
    publish_new_json(path, {**payload, "artifact_path": path.as_posix()}, dry_run=False)
    return path


def _historical_refs(root: Path) -> list[ArtifactRef]:
    result = []
    for name, content in (
        ("six-month-platform-gate-2026-07-15.md", b"baseline\n"),
        ("six-month-platform-gate-2026-07-15.json", b'{"status":"HOLD"}\n'),
    ):
        path = root / "META" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        result.append(ArtifactRef(path.as_posix(), hashlib.sha256(content).hexdigest()))
    return result


def _case(
    root: Path, index: int, *, task: str = "career.role_change", mutation: str | None = None,
) -> tuple[Path, dict]:
    case_id = f"P-GO-2026-{index:03d}-乾-甲子乙丑丙寅丁卯"
    subject = hashlib.sha256(f"subject-{index}".encode()).hexdigest()
    label_identity = hashlib.sha256(f"label-{index}-{task}".encode()).hexdigest()
    label_path = root / case_id / f"{case_id}--immediate-retrospective-bound--v001.json"
    scorable = mutation != "labels_14" or index <= 14
    if mutation == "positive_zero":
        observed_positive = False
    elif mutation == "negative_zero":
        observed_positive = True
    else:
        observed_positive = index % 2 == 1
    frozen_probability = 0.9 if observed_positive else 0.1
    if mutation == "nan" and index == 1:
        frozen_probability = math.nan
    elif mutation == "inf" and index == 1:
        frozen_probability = math.inf
    elif mutation == "calibration_equal_0_2":
        frozen_probability = 0.8 if observed_positive else 0.2
        if index == 1:
            frozen_probability = math.nextafter(frozen_probability, 1.0)
    label = {
        "schema_version": "prospective-immediate-retrospective-bound/v1",
        "case_id": case_id,
        "subject_id_hash": subject,
        "created_at": "2026-11-28T00:00:00Z",
        "parents": [],
        "evidence_class": EVIDENCE_CLASS,
        "facts": [{
            "task_id": task,
            "classification": "immediate_fact",
            "scorable": scorable,
            "label": "occurred" if observed_positive else "not_observed",
            "label_identity": label_identity,
            **({"high_risk": True} if mutation == "high_risk_unreviewed" and index == 1 else {}),
        }],
    }
    _publish(label_path, label)
    frozen_path = root / case_id / f"{case_id}--frozen-run--v001.json"
    run = freeze_outputs([
        BlindSchoolOutput(
            case_id=case_id, school_id="static", task_id=task, state="claim",
            rationale="sealed fixture prediction",
            predictions=[BlindPrediction(
                prediction_id=f"prediction-{index}", event_label="occurred",
                probability=frozen_probability,
                time_window={}, evidence_refs=["fixture://input"], falsifier="not observed",
            )],
        ),
    ], "fixture-task-catalog/v1", "fixture-rule-snapshot/v1", frozen_at="2026-11-27T00:00:00Z")
    _publish(frozen_path, {
        "schema_version": "school-capability-single-case-staged-run/v1",
        "case_id": case_id,
        "subject_id_hash": subject,
        "created_at": run.frozen_at,
        "parents": [],
        "frozen_run": run.to_dict(),
    })
    completion_path = root / case_id / f"{case_id}--case-completion--v001.json"
    _publish(completion_path, {
        "schema_version": "prospective-case-completion/v1",
        "case_id": case_id,
        "subject_id_hash": subject,
        "created_at": "2026-11-29T00:00:00Z",
        "parents": [_ref(label_path), _ref(frozen_path)],
        "retrospective_completion_status": "CASE_COMPLETE_FOR_RETROSPECTIVE",
    })
    return completion_path, {
        "case_id": case_id,
        "subject_id_hash": subject,
        "task_id": task,
        "label_identity": label_identity,
        "observed_positive": observed_positive if scorable else None,
        "scorable": scorable,
    }


def _gate_sources(tmp_path: Path, mutation: str | None = None) -> tuple[list[Path], Path, Path, Path]:
    cases = [_case(tmp_path / "cases", index, mutation=mutation) for index in range(1, 21)]
    historical = _historical_refs(tmp_path)
    manifests = []
    for cohort_index, start in enumerate((0, 10), 1):
        manifest = build_cohort_manifest(
            [item[0] for item in cases[start:start + 10]], historical, created_at=PARENT_AT,
        )
        path = tmp_path / f"cohort-{cohort_index}.json"
        publish_new_json(path, manifest, dry_run=False)
        manifests.append(path)

    rows = []
    for index, (completion, identity) in enumerate(cases, 1):
        completion_document = json.loads(completion.read_text(encoding="utf-8"))
        frozen_ref = next(parent for parent in completion_document["parents"] if "frozen-run" in parent["artifact_path"])
        rows.append({
            **identity,
            "scorable": identity["scorable"],
            "frozen_prediction": {
                **frozen_ref, "school_id": "static", "prediction_id": f"prediction-{index}",
            },
        })
    if mutation == "bool_count":
        rows[0]["scorable"] = 1
    elif mutation == "inconsistent_total":
        rows[0]["observed_positive"] = not rows[0]["observed_positive"]
    elif mutation == "forged_probability":
        rows[0]["probability"] = 0.01
        rows[0]["calibration_error"] = 0.0

    score_path = tmp_path / "scores.json"
    _publish(score_path, {
        "schema_version": "prospective-immediate-score-rows/v1",
        "created_at": PARENT_AT,
        "evidence_class": EVIDENCE_CLASS,
        "parents": [_ref(path) for path in manifests],
        "rows": rows,
    })
    competitive_count = 4 if mutation == "competitive_4" else 5
    holdout_path = tmp_path / "holdout.json"
    holdout_rows = []
    for index, row in enumerate(rows[:competitive_count]):
        holdout_rows.append({
            "case_id": row["case_id"], "subject_id_hash": row["subject_id_hash"],
            "task_id": row["task_id"], "eligible": True, "competitive": True,
            "training_subject_ids": [item["subject_id_hash"] for item in rows[10:]],
            "static_selection": "static", "learned_selection": "learned" if index == 0 else "static",
            "static_utility": 0.6, "learned_utility": 0.7,
        })
    if mutation == "selection_change_0":
        for row in holdout_rows:
            row["learned_selection"] = row["static_selection"]
    elif mutation == "learned_utility_lower":
        for row in holdout_rows:
            row["learned_utility"] = 0.5
    _publish(holdout_path, {
        "schema_version": "prospective-competition-holdout/v1",
        "created_at": PARENT_AT,
        "evidence_class": EVIDENCE_CLASS,
        "parents": [_ref(score_path)],
        "rows": holdout_rows,
    })
    statuses = {
        "high_risk_review_status": "FAIL" if mutation == "high_risk_unreviewed" else "NOT_APPLICABLE",
        "hash_audit_status": "FAIL" if mutation == "hash_fail" else "PASS",
        "witness_audit_status": "FAIL" if mutation == "witness_fail" else "PASS",
        "leakage_audit_status": "FAIL" if mutation == "leakage_fail" else "PASS",
    }
    audit_component_refs = []
    for name, status in statuses.items():
        path = tmp_path / f"{name}.json"
        _publish(path, {
            "schema_version": f"prospective-{name.replace('_status', '').replace('_', '-')}/v1",
            "created_at": PARENT_AT, "status": status, "parents": [_ref(holdout_path)],
        })
        audit_component_refs.append(_ref(path))
    audit_path = tmp_path / "audits.json"
    _publish(audit_path, {
        "schema_version": "prospective-candidate-audits/v1",
        "created_at": PARENT_AT,
        "evidence_class": EVIDENCE_CLASS,
        "parents": audit_component_refs,
        **statuses,
    })
    return manifests, score_path, holdout_path, audit_path


def _evidence(tmp_path: Path, mutation: str | None = None) -> GateEvidence:
    sources = _gate_sources(tmp_path, mutation)
    return build_gate_evidence_from_cohorts(
        sources[0], scoring_artifact=sources[1], holdout_artifact=sources[2], audit_artifact=sources[3],
    )


@pytest.mark.parametrize("mutation", [
    "labels_14", "positive_zero", "negative_zero", "calibration_equal_0_2",
    "high_risk_unreviewed", "competitive_4", "selection_change_0",
    "learned_utility_lower", "hash_fail", "witness_fail", "leakage_fail",
])
def test_prediction_candidate_holds_on_each_missing_condition(tmp_path: Path, mutation: str) -> None:
    result = evaluate_prediction_capability_candidate(_evidence(tmp_path, mutation), evaluated_at=EVALUATED_AT)
    assert result["gate_id"] == "prediction_capability_candidate_gate_v1"
    assert result["status"] == "HOLD"
    assert result["unmet_conditions"]
    assert result["proposal_allowed"] is False
    assert result["production_switch"] is False


def test_prediction_candidate_go_only_creates_proposal_and_global_artifact(tmp_path: Path) -> None:
    evidence = _evidence(tmp_path)
    result = evaluate_prediction_capability_candidate(evidence, evaluated_at=EVALUATED_AT)
    assert result["schema_version"] == "prediction-capability-candidate-gate/v1"
    assert result["status"] == "GO"
    assert result["proposal_allowed"] is True
    assert result["production_switch"] is False
    assert result["unmet_conditions"] == []
    assert set(result["checks"]) == {
        "evidence_class_is_immediate", "completed_subjects_at_least_20",
        "one_task_has_15_positive_and_negative", "same_eligible_task_calibration_below_0_2",
        "high_risk_reviews_pass", "one_competitive_task_at_least_5", "selection_changed",
        "utility_not_degraded", "hash_audit_pass", "witness_audit_pass", "leakage_audit_pass",
    }
    assert result["parents"] == list(evidence.parents)
    assert result["evaluated_at"] >= max(evidence.parent_created_at)
    assert result["artifact_sha256"]


def test_gate_evidence_requires_two_verified_cohorts_and_recursive_real_labels(tmp_path: Path) -> None:
    manifests, scoring, holdout, audit = _gate_sources(tmp_path)
    with pytest.raises(ValueError, match="20|subject|cohort"):
        build_gate_evidence_from_cohorts(
            manifests[:1], scoring_artifact=scoring, holdout_artifact=holdout, audit_artifact=audit,
        )
    Path(manifests[0]).write_bytes(Path(manifests[0]).read_bytes() + b" ")
    with pytest.raises(ValueError, match="hash|drift|manifest|verified"):
        build_gate_evidence_from_cohorts(
            manifests, scoring_artifact=scoring, holdout_artifact=holdout, audit_artifact=audit,
        )


@pytest.mark.parametrize("mutation", ["nan", "inf", "bool_count", "inconsistent_total"])
def test_malformed_or_inconsistent_source_rows_fail_closed(tmp_path: Path, mutation: str) -> None:
    with pytest.raises(ValueError, match="finite|bool|scorable|label|inconsistent|lineage|prediction|probability"):
        _evidence(tmp_path, mutation)


@pytest.mark.parametrize("mutation", [
    lambda evidence: replace(evidence, unique_completed_subjects=-1),
    lambda evidence: replace(evidence, selection_change_count=True),
    lambda evidence: replace(evidence, learned_utility=math.inf),
    lambda evidence: replace(evidence, task_label_counts={"career.role_change": 19}),
])
def test_caller_cannot_forge_derived_counts_or_metrics(
    tmp_path: Path, mutation,
) -> None:
    forged = mutation(_evidence(tmp_path))
    with pytest.raises(ValueError, match="reconstruction|count|finite|inconsistent"):
        evaluate_prediction_capability_candidate(forged, evaluated_at=EVALUATED_AT)

def test_duplicate_case_subject_or_label_identity_across_cohorts_is_rejected(tmp_path: Path) -> None:
    manifests, scoring, holdout, audit = _gate_sources(tmp_path)
    second = json.loads(manifests[1].read_text(encoding="utf-8"))
    first = json.loads(manifests[0].read_text(encoding="utf-8"))
    second["members"][0] = first["members"][0]
    second.pop("artifact_sha256")
    manifests[1].unlink()
    publish_new_json(manifests[1], second, dry_run=False)
    with pytest.raises(ValueError, match="duplicate|verified|reconstruction"):
        build_gate_evidence_from_cohorts(
            manifests, scoring_artifact=scoring, holdout_artifact=holdout, audit_artifact=audit,
        )


def test_score_rows_cannot_self_attest_prediction_or_calibration(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="score|field|prediction|calibration|schema"):
        _evidence(tmp_path, "forged_probability")


def test_holdout_competition_cannot_repeat_one_untraceable_row_five_times(tmp_path: Path) -> None:
    manifests, scoring, holdout, audit = _gate_sources(tmp_path)
    document = json.loads(holdout.read_text(encoding="utf-8"))
    document["rows"] = [document["rows"][0]] * 5
    document.pop("artifact_sha256")
    holdout.unlink()
    publish_new_json(holdout, document, dry_run=False)

    with pytest.raises(ValueError, match="holdout|duplicate|case|lineage|trace"):
        build_gate_evidence_from_cohorts(
            manifests, scoring_artifact=scoring, holdout_artifact=holdout, audit_artifact=audit,
        )


def test_bare_aggregate_audit_statuses_are_not_auditable_evidence(tmp_path: Path) -> None:
    manifests, scoring, holdout, audit = _gate_sources(tmp_path)
    document = json.loads(audit.read_text(encoding="utf-8"))
    document["parents"] = [_ref(holdout)]
    document.pop("artifact_sha256")
    audit.unlink()
    publish_new_json(audit, document, dry_run=False)

    with pytest.raises(ValueError, match="audit|parent|component|lineage"):
        build_gate_evidence_from_cohorts(
            manifests, scoring_artifact=scoring, holdout_artifact=holdout, audit_artifact=audit,
        )


def test_no_high_risk_labels_use_not_applicable_instead_of_forged_pass(tmp_path: Path) -> None:
    evidence = _evidence(tmp_path)

    assert evidence.high_risk_review_status == "NOT_APPLICABLE"
    result = evaluate_prediction_capability_candidate(evidence, evaluated_at=EVALUATED_AT)
    assert result["checks"]["high_risk_reviews_pass"] is True


def test_gate_cli_is_create_only(tmp_path: Path) -> None:
    manifests, scoring, holdout, audit = _gate_sources(tmp_path)
    output = tmp_path / "prediction-capability-candidate-gate-v1.json"
    command = [sys.executable, "-m", "tools.school_capability_cohort", "gate"]
    for manifest in manifests:
        command.extend(("--manifest", str(manifest)))
    command.extend((
        "--scores", str(scoring), "--holdout", str(holdout), "--audit", str(audit),
        "--evaluated-at", EVALUATED_AT, "--out", str(output),
    ))
    dry = subprocess.run([*command, "--dry-run"], check=False, capture_output=True, text=True, encoding="utf-8")
    assert dry.returncode == 0, dry.stderr
    assert not output.exists()
    assert json.loads(dry.stdout)["result"]["status"] == "GO"
    first = subprocess.run(command, check=False, capture_output=True, text=True, encoding="utf-8")
    assert first.returncode == 0, first.stderr
    original = output.read_bytes()
    second = subprocess.run(command, check=False, capture_output=True, text=True, encoding="utf-8")
    assert second.returncode != 0
    assert "already exists" in second.stderr
    assert output.read_bytes() == original


def test_gate_cli_rejects_noncanonical_result_filename(tmp_path: Path) -> None:
    manifests, scoring, holdout, audit = _gate_sources(tmp_path)
    output = tmp_path / "arbitrary-go.json"
    command = [sys.executable, "-m", "tools.school_capability_cohort", "gate"]
    for manifest in manifests:
        command.extend(("--manifest", str(manifest)))
    command.extend((
        "--scores", str(scoring), "--holdout", str(holdout), "--audit", str(audit),
        "--evaluated-at", EVALUATED_AT, "--out", str(output),
    ))

    result = subprocess.run(command, check=False, capture_output=True, text=True, encoding="utf-8")

    assert result.returncode != 0
    assert "canonical" in result.stderr.lower() or "filename" in result.stderr.lower()
    assert not output.exists()


FUTURE_EVIDENCE_CLASS = "future_observation"
FUTURE_EVALUATED_AT = "2027-01-16T00:00:00Z"


def _future_case(
    root: Path, index: int, *, mutation: str | None = None,
) -> tuple[Path, dict]:
    completion, identity = _case(
        root, index, mutation="calibration_equal_0_2" if mutation == "calibration_equal_0_2" else None,
    )
    completion_document = json.loads(completion.read_text(encoding="utf-8"))
    frozen_ref = next(parent for parent in completion_document["parents"] if "frozen-run" in parent["artifact_path"])
    frozen_path = Path(frozen_ref["artifact_path"])
    frozen_document = json.loads(frozen_path.read_text(encoding="utf-8"))
    question_path = completion.with_name(
        f"{identity['case_id']}--future-question-registration--v001.json"
    )
    question_ref = publish_new_json(question_path, {
        "schema_version": "prospective-future-question/v1",
        "case_id": identity["case_id"],
        "subject_id_hash": identity["subject_id_hash"],
        "created_at": "2026-11-27T00:00:00Z",
        "artifact_path": question_path.as_posix(),
        "future_task_id": identity["task_id"],
        "question_text_redacted": "未来窗口内是否发生显著岗位角色变化？",
        "outcome_type": "binary",
        "positive_definition": "发生并由登记来源确认",
        "negative_definition": "完整窗口结束且登记来源确认未发生",
        "verification_source_requirements": ["custody://structured-interview"],
        "observation_window": {
            "start_at": "2026-11-27T00:00:00Z",
            "end_at": "2027-01-15T00:00:00Z",
        },
        "parents": [],
    }, dry_run=False)
    frozen_document["parents"] = [question_ref.__dict__]
    frozen_document["future_question_registration_sha256"] = question_ref.artifact_sha256
    frozen_document.pop("artifact_sha256")
    frozen_path.unlink()
    publish_new_json(frozen_path, frozen_document, dry_run=False)
    completion_document["parents"] = [
        _ref(frozen_path) if parent["artifact_path"] == frozen_path.as_posix() else parent
        for parent in completion_document["parents"]
    ]
    future_path = completion.with_name(
        f"{identity['case_id']}--future-observation-bound--v001.json"
    )
    observed_positive = identity["observed_positive"]
    if mutation == "positive_zero":
        observed_positive = False
    elif mutation == "negative_zero":
        observed_positive = True
    label = "occurred" if observed_positive else "not_observed"
    scorable = True
    no_data_reason = None
    pending_from = 10 if mutation == "subjects_9" else 8
    if mutation in {"subjects_9", "labels_7", "window_unmatured", "no_data"} and index >= pending_from:
        label = "no_data"
        scorable = False
        no_data_reason = "window_unmatured" if mutation == "window_unmatured" else "no_data"
    high_risk = mutation == "high_risk_reused" and index == 1
    if mutation == "premature_not_observed" and index == 1:
        label = "not_observed"
        observed_positive = False
    observation = {
        "future_task_id": identity["task_id"],
        "label": label,
        "scorable": scorable and not high_risk,
        "high_risk": high_risk,
        "observed_at": "2027-01-14T00:00:00Z" if mutation == "premature_not_observed" and index == 1 else "2027-01-15T00:00:00Z",
        "collected_at": "2027-01-14T00:00:00Z" if mutation == "premature_not_observed" and index == 1 else "2027-01-15T00:00:00Z",
        "observation_window": {
            "start_at": "2026-11-27T00:00:00Z",
            "end_at": "2027-01-15T00:00:00Z",
        },
        **({"no_data_reason": no_data_reason} if no_data_reason else {}),
        **({"review_status": "pending_independent_dual_review"} if high_risk else {}),
    }
    label_identity = canonical_artifact_sha256({
        "case_id": identity["case_id"],
        "evidence_class": FUTURE_EVIDENCE_CLASS,
        "future_task_id": identity["task_id"],
        "observed_at": observation["observed_at"],
    })
    unbound_path = completion.with_name(
        f"{identity['case_id']}--future-observation-unbound--v001.json"
    )
    _publish(unbound_path, {
        "schema_version": "prospective-future-observation-unbound/v1",
        "case_id": identity["case_id"],
        "subject_id_hash": identity["subject_id_hash"],
        "created_at": "2027-01-15T00:00:00Z",
        "evidence_class": FUTURE_EVIDENCE_CLASS,
        "label_identity": label_identity,
        "parents": [question_ref.__dict__, _ref(frozen_path)],
        "observation": observation,
    })
    _publish(future_path, {
        "schema_version": "prospective-future-observation-bound/v1",
        "case_id": identity["case_id"],
        "subject_id_hash": identity["subject_id_hash"],
        "created_at": "2027-01-15T00:00:00Z",
        "evidence_class": FUTURE_EVIDENCE_CLASS,
        "label_identity": label_identity,
        "parents": [_ref(unbound_path)],
        "observation": observation,
    })
    completion_document["parents"].append(_ref(future_path))
    completion_document["future_completion_status"] = (
        "CASE_COMPLETE_FOR_FUTURE" if observation["scorable"] else "PENDING"
    )
    completion_document["created_at"] = "2027-01-15T01:00:00Z"
    completion_document.pop("artifact_sha256")
    completion.unlink()
    publish_new_json(completion, completion_document, dry_run=False)
    return completion, {
        **identity,
        "label_identity": json.loads(future_path.read_text(encoding="utf-8"))["label_identity"],
        "observed_positive": observed_positive if observation["scorable"] else None,
        "scorable": observation["scorable"],
    }


def _future_gate_sources(
    tmp_path: Path, mutation: str | None = None,
) -> tuple[list[Path], Path, Path, Path]:
    cases = [_future_case(tmp_path / "future-cases", index, mutation=mutation) for index in range(1, 11)]
    historical = _historical_refs(tmp_path)
    manifest = build_cohort_manifest(
        [item[0] for item in cases], historical, created_at="2027-01-15T02:00:00Z",
    )
    manifest_path = tmp_path / "future-cohort.json"
    publish_new_json(manifest_path, manifest, dry_run=False)

    rows = []
    for index, (completion, identity) in enumerate(cases, 1):
        completion_document = json.loads(completion.read_text(encoding="utf-8"))
        frozen_ref = next(parent for parent in completion_document["parents"] if "frozen-run" in parent["artifact_path"])
        rows.append({
            **identity,
            "frozen_prediction": {
                **frozen_ref, "school_id": "static", "prediction_id": f"prediction-{index}",
            },
        })
    score_path = tmp_path / "future-scores.json"
    _publish(score_path, {
        "schema_version": "prospective-future-score-rows/v1",
        "created_at": "2027-01-15T03:00:00Z",
        "evidence_class": FUTURE_EVIDENCE_CLASS,
        "parents": [_ref(manifest_path)],
        "rows": rows,
    })
    competitive_count = 4 if mutation in {"competitive_4", "competition_not_applicable"} else 5
    holdout_rows = []
    for index, row in enumerate(rows[:competitive_count]):
        holdout_rows.append({
            "case_id": row["case_id"], "subject_id_hash": row["subject_id_hash"],
            "task_id": row["task_id"], "eligible": mutation != "competition_not_applicable",
            "competitive": mutation != "competition_not_applicable",
            "training_subject_ids": [item[1]["subject_id_hash"] for item in cases[5:]],
            "static_selection": "static", "learned_selection": "learned" if index == 0 else "static",
            "static_utility": 0.6,
            "learned_utility": 0.5 if mutation == "learned_utility_lower" else 0.7,
        })
    if mutation == "selection_change_0":
        for row in holdout_rows:
            row["learned_selection"] = row["static_selection"]
    holdout_path = tmp_path / "future-holdout.json"
    _publish(holdout_path, {
        "schema_version": "prospective-future-competition-holdout/v1",
        "created_at": "2027-01-15T04:00:00Z",
        "evidence_class": FUTURE_EVIDENCE_CLASS,
        "parents": [_ref(score_path)],
        "rows": holdout_rows,
    })
    has_high_risk = mutation == "high_risk_reused"
    statuses = {
        "high_risk_review_status": "FAIL" if has_high_risk else "NOT_APPLICABLE",
        "hash_audit_status": "FAIL" if mutation == "parent_hash_fail" else "PASS",
        "witness_audit_status": "PASS",
        "leakage_audit_status": "PASS",
    }
    component_refs = []
    for name, status in statuses.items():
        path = tmp_path / f"future-{name}.json"
        _publish(path, {
            "schema_version": f"prospective-{name.replace('_status', '').replace('_', '-')}/v1",
            "created_at": "2027-01-15T05:00:00Z", "status": status,
            "evidence_class": FUTURE_EVIDENCE_CLASS, "parents": [_ref(holdout_path)],
            **({"review_evidence_class": EVIDENCE_CLASS} if has_high_risk and name == "high_risk_review_status" else {}),
        })
        component_refs.append(_ref(path))
    audit_path = tmp_path / "future-audits.json"
    _publish(audit_path, {
        "schema_version": "prospective-future-candidate-audits/v1",
        "created_at": "2027-01-15T06:00:00Z",
        "evidence_class": FUTURE_EVIDENCE_CLASS,
        "parents": component_refs,
        **statuses,
    })
    return [manifest_path], score_path, holdout_path, audit_path


def _future_evidence(tmp_path: Path, mutation: str | None = None) -> GateEvidence:
    sources = _future_gate_sources(tmp_path, mutation)
    return build_future_gate_evidence_from_cohorts(
        sources[0], scoring_artifact=sources[1], holdout_artifact=sources[2], audit_artifact=sources[3],
    )


@pytest.mark.parametrize("mutation", [
    "subjects_9", "labels_7", "positive_zero", "negative_zero", "window_unmatured",
    "calibration_equal_0_2", "high_risk_reused", "competitive_4",
    "competition_not_applicable", "selection_change_0", "learned_utility_lower",
    "parent_hash_fail",
])
def test_future_gate_holds_on_each_missing_condition(tmp_path: Path, mutation: str) -> None:
    evidence = _future_evidence(tmp_path, mutation)
    if mutation == "calibration_equal_0_2":
        assert evidence.calibration_error_by_task["career.role_change"] == pytest.approx(0.2)
    result = evaluate_future_empirical(evidence, evaluated_at=FUTURE_EVALUATED_AT)
    assert result["gate_id"] == "future_empirical_gate_v1"
    assert result["status"] == "HOLD"
    assert result["production_switch"] is False


def test_future_gate_go_recomputes_ten_completed_future_labels_from_frozen_predictions(tmp_path: Path) -> None:
    evidence = _future_evidence(tmp_path)
    result = evaluate_future_empirical(evidence, evaluated_at=FUTURE_EVALUATED_AT)
    assert evidence.evidence_class == FUTURE_EVIDENCE_CLASS
    assert evidence.unique_completed_subjects == 10
    assert result["status"] == "GO"
    assert result["production_switch"] is False
    assert result["checks"]["fresh_high_risk_reviews_pass"] is True
    assert evidence.high_risk_review_status == "NOT_APPLICABLE"


def test_twenty_immediate_plus_ten_future_cannot_satisfy_historical_baseline(tmp_path: Path) -> None:
    immediate = evaluate_prediction_capability_candidate(_evidence(tmp_path / "immediate"), evaluated_at=FUTURE_EVALUATED_AT)
    future = evaluate_future_empirical(_future_evidence(tmp_path / "future"), evaluated_at=FUTURE_EVALUATED_AT)
    historical_path = Path("META/six-month-platform-gate-2026-07-15.json")
    historical_ref = ArtifactRef(historical_path.as_posix(), hashlib.sha256(historical_path.read_bytes()).hexdigest())
    report = build_three_gate_report(immediate, future, historical_ref)
    assert "预测能力候选 GO" in report
    assert "未来实证 GO" in report
    assert "historical baseline（只读引用） HOLD" in report
    assert "30" not in report
    assert "已自动切生产" not in report
    assert "production_switch: false" in report


def test_future_gate_cli_and_three_gate_report_are_canonical_create_only(tmp_path: Path) -> None:
    future_sources = _future_gate_sources(tmp_path / "future")
    future_out = tmp_path / "future-empirical-gate-v1.json"
    future_command = [sys.executable, "-m", "tools.school_capability_cohort", "future-gate"]
    for manifest in future_sources[0]:
        future_command.extend(("--manifest", str(manifest)))
    future_command.extend((
        "--scores", str(future_sources[1]), "--holdout", str(future_sources[2]),
        "--audit", str(future_sources[3]), "--evaluated-at", FUTURE_EVALUATED_AT,
        "--out", str(future_out),
    ))
    created = subprocess.run(future_command, check=False, capture_output=True, text=True, encoding="utf-8")
    assert created.returncode == 0, created.stderr
    assert json.loads(future_out.read_text(encoding="utf-8"))["status"] == "GO"
    original = future_out.read_bytes()
    duplicate = subprocess.run(future_command, check=False, capture_output=True, text=True, encoding="utf-8")
    assert duplicate.returncode != 0
    assert future_out.read_bytes() == original

    immediate_sources = _gate_sources(tmp_path / "immediate")
    immediate_out = tmp_path / "prediction-capability-candidate-gate-v1.json"
    immediate_command = [sys.executable, "-m", "tools.school_capability_cohort", "gate"]
    for manifest in immediate_sources[0]:
        immediate_command.extend(("--manifest", str(manifest)))
    immediate_command.extend((
        "--scores", str(immediate_sources[1]), "--holdout", str(immediate_sources[2]),
        "--audit", str(immediate_sources[3]), "--evaluated-at", FUTURE_EVALUATED_AT,
        "--out", str(immediate_out),
    ))
    assert subprocess.run(immediate_command, check=False, capture_output=True, text=True, encoding="utf-8").returncode == 0
    historical_json = Path("META/six-month-platform-gate-2026-07-15.json")
    report_out = tmp_path / "three-gate-report-v1.md"
    report_command = [
        sys.executable, "-m", "tools.school_capability_cohort", "report",
        "--immediate-gate", str(immediate_out), "--future-gate", str(future_out),
        "--historical-json", str(historical_json), "--out", str(report_out),
    ]
    report_result = subprocess.run(report_command, check=False, capture_output=True, text=True, encoding="utf-8")
    assert report_result.returncode == 0, report_result.stderr
    assert report_out.read_text(encoding="utf-8").count("## ") == 3
    report_original = report_out.read_bytes()
    assert subprocess.run(report_command, check=False, capture_output=True, text=True, encoding="utf-8").returncode != 0
    assert report_out.read_bytes() == report_original


def test_future_gate_rejects_claimed_completion_collected_before_actual_window_end(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="window|matur|collected"):
        _future_evidence(tmp_path, "premature_not_observed")


def test_three_gate_report_rejects_same_named_forged_historical_path(tmp_path: Path) -> None:
    forged = tmp_path / "attacker" / "six-month-platform-gate-2026-07-15.json"
    forged.parent.mkdir(parents=True)
    forged.write_text(
        '{"schema_version":"six-month-platform-gate/v1","status":"GO"}\n',
        encoding="utf-8",
    )
    ref = ArtifactRef(forged.as_posix(), hashlib.sha256(forged.read_bytes()).hexdigest())
    immediate = {"gate_id": "prediction_capability_candidate_gate_v1", "status": "GO"}
    future = {"gate_id": "future_empirical_gate_v1", "status": "GO"}

    with pytest.raises(ValueError, match="historical|canonical|baseline|path"):
        build_three_gate_report(immediate, future, ref)


def test_three_gate_report_binds_canonical_historical_md_hash_and_scopes_go_offline() -> None:
    historical_path = Path("META/six-month-platform-gate-2026-07-15.json")
    ref = ArtifactRef(historical_path.as_posix(), hashlib.sha256(historical_path.read_bytes()).hexdigest())
    immediate = {"gate_id": "prediction_capability_candidate_gate_v1", "status": "GO"}
    future = {"gate_id": "future_empirical_gate_v1", "status": "GO"}

    report = build_three_gate_report(immediate, future, ref)

    md_path = Path("META/six-month-platform-gate-2026-07-15.md")
    assert hashlib.sha256(md_path.read_bytes()).hexdigest() in report
    assert "离线候选门禁结果：GO（不代表平台 GO 或生产 GO）" in report
    assert "production_switch: false" in report


def test_immediate_aggregation_skips_future_only_member_in_mixed_manifest(tmp_path: Path) -> None:
    cases = [_future_case(tmp_path / "mixed-immediate", index) for index in range(1, 11)]
    future_only = cases[-1][0]
    completion = json.loads(future_only.read_text(encoding="utf-8"))
    completion["retrospective_completion_status"] = "PENDING"
    completion["parents"] = [
        parent for parent in completion["parents"]
        if "immediate-retrospective" not in parent["artifact_path"]
    ]
    completion.pop("artifact_sha256")
    future_only.unlink()
    publish_new_json(future_only, completion, dry_run=False)
    manifest = build_cohort_manifest(
        [item[0] for item in cases], _historical_refs(tmp_path),
        created_at="2027-01-15T02:00:00Z",
    )

    labels, cases_seen, subjects_seen, frozen = _label_rows_from_manifests([manifest])

    assert len(labels) == 9
    assert len(cases_seen) == 9
    assert len(subjects_seen) == 9
    assert set(frozen) == cases_seen
    assert completion["case_id"] not in cases_seen


def test_future_aggregation_skips_retrospective_only_and_pending_future_members(tmp_path: Path) -> None:
    retrospective_only = [_case(tmp_path / "mixed-future", index) for index in range(1, 11)]
    manifest = build_cohort_manifest(
        [item[0] for item in retrospective_only], _historical_refs(tmp_path),
        created_at=PARENT_AT,
    )

    labels, completed_cases, completed_subjects, frozen = _future_label_rows_from_manifests([manifest])

    assert labels == {}
    assert completed_cases == set()
    assert completed_subjects == set()
    assert frozen == {}


def test_future_aggregation_rejects_parentless_hand_forged_bound_artifact(tmp_path: Path) -> None:
    cases = [_future_case(tmp_path / "forged-future", index) for index in range(1, 11)]
    manifest = build_cohort_manifest(
        [item[0] for item in cases], _historical_refs(tmp_path),
        created_at="2027-01-15T02:00:00Z",
    )
    first = manifest["members"][0]
    future_path = Path(first["parents"]["future"]["artifact_path"])
    forged = json.loads(future_path.read_text(encoding="utf-8"))
    forged["parents"] = []
    forged.pop("artifact_sha256")
    future_path.unlink()
    publish_new_json(future_path, forged, dry_run=False)
    completion_path = Path(first["parents"]["completion"]["artifact_path"])
    completion = json.loads(completion_path.read_text(encoding="utf-8"))
    completion["parents"] = [
        _ref(future_path) if parent["artifact_path"] == future_path.as_posix() else parent
        for parent in completion["parents"]
    ]
    completion.pop("artifact_sha256")
    completion_path.unlink()
    publish_new_json(completion_path, completion, dry_run=False)
    manifest = build_cohort_manifest(
        [member["parents"]["completion"]["artifact_path"] for member in manifest["members"]],
        _historical_refs(tmp_path / "rebuilt"), created_at="2027-01-15T02:00:00Z",
    )

    with pytest.raises(ValueError, match="future|parent|lineage|unbound|registration|frozen"):
        _future_label_rows_from_manifests([manifest])
