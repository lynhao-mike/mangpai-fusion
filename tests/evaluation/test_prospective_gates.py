from __future__ import annotations

import ast
import hashlib
import inspect
import json
from collections import defaultdict
import math
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from engine.evaluation.freeze import freeze_outputs
from engine.evaluation.models import BlindPrediction, BlindSchoolOutput
import engine.evaluation.prospective_artifacts as prospective_artifacts
from engine.evaluation.prospective_artifacts import (
    ArtifactRef,
    canonical_artifact_sha256,
    publish_new_json,
)
from engine.governance.governance_claim_values import ClaimEvidenceGrade, ClaimKind
from engine.evaluation.prospective_capability_identity import (
    build_capability_identity_artifact,
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
from tests.evaluation.test_governance_shadow_adapter import (
    _claim as governance_claim_fixture,
    _projection as governance_projection_fixture,
    _shadow as governance_shadow_fixture,
)


EVALUATED_AT = "2026-12-01T00:00:00Z"
PARENT_AT = "2026-11-30T00:00:00Z"
EVIDENCE_CLASS = "prediction_first_immediate_retrospective"


def _install_authority_files(root: Path) -> None:
    state = root / "META" / "project-state.json"
    contract = (
        root
        / ".omo"
        / "drafts"
        / ("w2-c4-governance-promotion-remediation-r3-admission-contract-2026-08-08.md")
    )
    state.parent.mkdir(parents=True, exist_ok=True)
    contract.parent.mkdir(parents=True, exist_ok=True)
    state.write_bytes(Path("META/project-state.json").read_bytes())
    contract.write_bytes(
        Path(
            ".omo/drafts/w2-c4-governance-promotion-remediation-r3-admission-contract-2026-08-08.md"
        ).read_bytes()
    )
    for name in (
        "six-month-platform-gate-2026-07-15.json",
        "six-month-platform-gate-2026-07-15.md",
    ):
        (root / "META" / name).write_bytes((Path("META") / name).read_bytes())


@pytest.fixture(autouse=True)
def _repository_authority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_authority_files(tmp_path)
    monkeypatch.setattr(
        prospective_artifacts, "_trusted_repository_root", lambda: tmp_path.absolute()
    )


def _identity(tmp_path: Path, name: str = "identity"):
    claim = governance_claim_fixture()
    shadow = governance_shadow_fixture(claim)
    projection = governance_projection_fixture(shadow, claim)
    identity, reference = build_capability_identity_artifact(
        claim,
        governance_result=shadow,
        governance_projection=projection,
        created_at="2026-11-26T00:00:00Z",
        source_output_path=tmp_path / f"{name}-source.json",
        output_path=tmp_path / f"{name}.json",
        dry_run=False,
    )
    return claim, identity, reference


def _ref(path: Path) -> dict[str, str]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return {
        "artifact_path": path.as_posix(),
        "artifact_sha256": document["artifact_sha256"],
    }


def _publish(path: Path, payload: dict) -> Path:
    publish_new_json(path, {**payload, "artifact_path": path.as_posix()}, dry_run=False)
    return path


def _run_school_cli(argv: list[str], capsys: pytest.CaptureFixture[str]):
    from tools.school_capability_cohort import main

    return_code = main(argv)
    captured = capsys.readouterr()
    return return_code, captured.out, captured.err


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
    root: Path,
    index: int,
    *,
    task: str = "career.role_change",
    mutation: str | None = None,
    capability_identity_ref: ArtifactRef | None = None,
) -> tuple[Path, dict]:
    case_id = f"P-GO-2026-{index:03d}-乾-甲子乙丑丙寅丁卯"
    subject = hashlib.sha256(f"subject-{index}".encode()).hexdigest()
    label_identity = hashlib.sha256(f"label-{index}-{task}".encode()).hexdigest()
    label_path = root / case_id / f"{case_id}--immediate-retrospective-bound--v001.json"
    output_state = (
        "abstain"
        if mutation == "output_states" and index == 1
        else "unsupported"
        if mutation == "output_states" and index == 2
        else "claim"
    )
    scorable = output_state == "claim" and (mutation != "labels_14" or index <= 14)
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
        "facts": [
            {
                "task_id": task,
                "classification": "immediate_fact" if scorable else "no_data",
                "scorable": scorable,
                "label": (
                    "occurred"
                    if scorable and observed_positive
                    else "not_observed"
                    if scorable
                    else "no_data"
                ),
                "label_identity": label_identity,
                **(
                    {"high_risk": True}
                    if mutation == "high_risk_unreviewed" and index == 1
                    else {}
                ),
            }
        ],
    }
    _publish(label_path, label)
    frozen_path = root / case_id / f"{case_id}--frozen-run--v001.json"
    run = freeze_outputs(
        [
            BlindSchoolOutput(
                case_id=case_id,
                school_id="static",
                task_id=task,
                state=output_state,
                rationale="sealed fixture prediction",
                predictions=(
                    [
                        BlindPrediction(
                            prediction_id=f"prediction-{index}",
                            event_label="occurred",
                            probability=frozen_probability,
                            time_window={},
                            evidence_refs=["fixture://input"],
                            falsifier="not observed",
                        )
                    ]
                    if output_state == "claim"
                    else []
                ),
            ),
        ],
        "fixture-task-catalog/v1",
        "fixture-rule-snapshot/v1",
        frozen_at="2026-11-27T00:00:00Z",
    )
    identity_value = (
        None
        if capability_identity_ref is None
        else {
            "artifact_path": capability_identity_ref.artifact_path,
            "artifact_sha256": capability_identity_ref.artifact_sha256,
        }
    )
    _publish(
        frozen_path,
        {
            "schema_version": "school-capability-single-case-staged-run/v1",
            "case_id": case_id,
            "subject_id_hash": subject,
            "created_at": run.frozen_at,
            "parents": [] if identity_value is None else [identity_value],
            **(
                {}
                if identity_value is None
                else {"capability_identity_ref": identity_value}
            ),
            "frozen_run": run.to_dict(),
        },
    )
    completion_path = root / case_id / f"{case_id}--case-completion--v001.json"
    _publish(
        completion_path,
        {
            "schema_version": "prospective-case-completion/v1",
            "case_id": case_id,
            "subject_id_hash": subject,
            "created_at": "2026-11-29T00:00:00Z",
            "parents": [_ref(label_path), _ref(frozen_path)],
            **(
                {}
                if identity_value is None
                else {"capability_identity_ref": identity_value}
            ),
            "retrospective_completion_status": "CASE_COMPLETE_FOR_RETROSPECTIVE",
        },
    )
    return completion_path, {
        "case_id": case_id,
        "subject_id_hash": subject,
        "task_id": task,
        "label_identity": label_identity,
        "observed_positive": observed_positive if scorable else None,
        "scorable": scorable,
    }


def _gate_sources(
    tmp_path: Path,
    mutation: str | None = None,
    *,
    capability_identity_ref: ArtifactRef | None = None,
    task: str = "career.role_change",
) -> tuple[list[Path], Path, Path, Path]:
    cases = [
        _case(
            tmp_path / "cases",
            index,
            mutation=mutation,
            task=task,
            capability_identity_ref=capability_identity_ref,
        )
        for index in range(1, 21)
    ]
    historical = _historical_refs(tmp_path)
    manifests = []
    for cohort_index, start in enumerate((0, 10), 1):
        manifest = build_cohort_manifest(
            [item[0] for item in cases[start : start + 10]],
            historical,
            created_at=PARENT_AT,
        )
        path = tmp_path / f"cohort-{cohort_index}.json"
        publish_new_json(path, manifest, dry_run=False)
        manifests.append(path)

    identity_value = (
        None
        if capability_identity_ref is None
        else {
            "artifact_path": capability_identity_ref.artifact_path,
            "artifact_sha256": capability_identity_ref.artifact_sha256,
        }
    )
    source_value = None
    if capability_identity_ref is not None:
        identity_document = json.loads(
            Path(capability_identity_ref.artifact_path).read_text(encoding="utf-8")
        )
        source_value = identity_document["parents"][0]

    rows = []
    for index, (completion, identity) in enumerate(cases, 1):
        completion_document = json.loads(completion.read_text(encoding="utf-8"))
        frozen_ref = next(
            parent
            for parent in completion_document["parents"]
            if "frozen-run" in parent["artifact_path"]
        )
        rows.append(
            {
                **identity,
                "scorable": identity["scorable"],
                **(
                    {}
                    if identity_value is None
                    else {
                        "capability_identity_ref": identity_value,
                        "governance_source_ref": source_value,
                    }
                ),
                "frozen_prediction": {
                    **frozen_ref,
                    "school_id": "static",
                    "prediction_id": f"prediction-{index}",
                },
            }
        )
    if mutation == "bool_count":
        rows[0]["scorable"] = 1
    elif mutation == "inconsistent_total":
        rows[0]["observed_positive"] = not rows[0]["observed_positive"]
    elif mutation == "forged_probability":
        rows[0]["probability"] = 0.01
        rows[0]["calibration_error"] = 0.0

    score_path = tmp_path / "scores.json"
    _publish(
        score_path,
        {
            "schema_version": "prospective-immediate-score-rows/v1",
            "created_at": PARENT_AT,
            "evidence_class": EVIDENCE_CLASS,
            "parents": [_ref(path) for path in manifests],
            **(
                {}
                if identity_value is None
                else {
                    "capability_identity_ref": identity_value,
                    "governance_source_ref": source_value,
                }
            ),
            "rows": rows,
        },
    )
    competitive_count = 4 if mutation == "competitive_4" else 5
    holdout_path = tmp_path / "holdout.json"
    holdout_rows = []
    for index, row in enumerate(rows[:competitive_count]):
        holdout_rows.append(
            {
                "case_id": row["case_id"],
                "subject_id_hash": row["subject_id_hash"],
                "task_id": row["task_id"],
                "eligible": True,
                "competitive": True,
                "training_subject_ids": [item["subject_id_hash"] for item in rows[10:]],
                "static_selection": "static",
                "learned_selection": "learned" if index == 0 else "static",
                "static_utility": 0.6,
                "learned_utility": 0.7,
            }
        )
    if mutation == "selection_change_0":
        for row in holdout_rows:
            row["learned_selection"] = row["static_selection"]
    elif mutation == "learned_utility_lower":
        for row in holdout_rows:
            row["learned_utility"] = 0.5
    _publish(
        holdout_path,
        {
            "schema_version": "prospective-competition-holdout/v1",
            "created_at": PARENT_AT,
            "evidence_class": EVIDENCE_CLASS,
            "parents": [_ref(score_path)],
            **(
                {}
                if identity_value is None
                else {
                    "capability_identity_ref": identity_value,
                    "governance_source_ref": source_value,
                }
            ),
            "rows": holdout_rows,
        },
    )
    statuses = {
        "high_risk_review_status": "FAIL"
        if mutation == "high_risk_unreviewed"
        else "NOT_APPLICABLE",
        "hash_audit_status": "FAIL" if mutation == "hash_fail" else "PASS",
        "witness_audit_status": "FAIL" if mutation == "witness_fail" else "PASS",
        "leakage_audit_status": "FAIL" if mutation == "leakage_fail" else "PASS",
    }
    audit_component_refs = []
    for name, status in statuses.items():
        path = tmp_path / f"{name}.json"
        _publish(
            path,
            {
                "schema_version": f"prospective-{name.replace('_status', '').replace('_', '-')}/v1",
                "created_at": PARENT_AT,
                "status": status,
                "parents": [_ref(holdout_path)],
                **(
                    {}
                    if identity_value is None
                    else {
                        "capability_identity_ref": identity_value,
                        "governance_source_ref": source_value,
                    }
                ),
            },
        )
        audit_component_refs.append(_ref(path))
    audit_path = tmp_path / "audits.json"
    _publish(
        audit_path,
        {
            "schema_version": "prospective-candidate-audits/v1",
            "created_at": PARENT_AT,
            "evidence_class": EVIDENCE_CLASS,
            "parents": audit_component_refs,
            **(
                {}
                if identity_value is None
                else {
                    "capability_identity_ref": identity_value,
                    "governance_source_ref": source_value,
                }
            ),
            **statuses,
        },
    )
    return manifests, score_path, holdout_path, audit_path


def test_gate_evidence_recursively_authenticates_one_exact_capability_identity(
    tmp_path: Path,
) -> None:
    claim, identity, identity_ref = _identity(tmp_path, "capability-identity")
    sources = _gate_sources(
        tmp_path,
        capability_identity_ref=identity_ref,
        task=claim.task_id,
    )

    evidence = build_gate_evidence_from_cohorts(
        sources[0],
        scoring_artifact=sources[1],
        holdout_artifact=sources[2],
        audit_artifact=sources[3],
    )

    assert evidence.capability_identity_ref == {
        "artifact_path": identity_ref.artifact_path,
        "artifact_sha256": identity_ref.artifact_sha256,
    }
    assert evidence.school_id == claim.school_id
    assert evidence.task_id == claim.task_id
    assert evidence.claim_kind is claim.claim_kind
    assert evidence.evidence_grade is claim.evidence_grade
    assert evidence.capability_version == claim.adapter_provenance.adapter_version
    assert evidence.governance_source_ref == identity.governance_source_ref


def test_gate_public_builders_do_not_accept_caller_controlled_root() -> None:
    forbidden = {"admitted_root", "repository_root", "workspace_root"}
    for entrypoint in (
        build_cohort_manifest,
        build_gate_evidence_from_cohorts,
        build_future_gate_evidence_from_cohorts,
        evaluate_prediction_capability_candidate,
        evaluate_future_empirical,
        build_three_gate_report,
    ):
        assert forbidden.isdisjoint(inspect.signature(entrypoint).parameters)


def test_gate_evidence_is_recursively_immutable_and_rejects_mutable_input() -> None:
    evidence = GateEvidence(
        evidence_class=EVIDENCE_CLASS,
        unique_completed_subjects=20,
        task_label_counts={"task": 20},
        positive_counts={"task": 10},
        negative_counts={"task": 10},
        no_data_counts={"task": 0},
        calibration_error_by_task={"task": 0.1},
        competitive_count_by_task={"task": 5},
        selection_change_count=1,
        learned_utility=0.7,
        static_utility=0.6,
        high_risk_review_status="NOT_APPLICABLE",
        hash_audit_status="PASS",
        witness_audit_status="PASS",
        leakage_audit_status="PASS",
        parents=({"artifact_path": "x.json", "artifact_sha256": "0" * 64},),
        parent_created_at=(PARENT_AT,),
        capability_identity_ref={
            "artifact_path": "identity.json",
            "artifact_sha256": "1" * 64,
        },
        governance_source_ref=ArtifactRef("source.json", "2" * 64),
        school_id="ziping",
        task_id="task",
        claim_kind=ClaimKind.EVENT,
        evidence_grade=ClaimEvidenceGrade.DIRECT,
        capability_version="v1",
        provenance_verified=True,
    )

    with pytest.raises((TypeError, FrozenInstanceError)):
        evidence.task_label_counts["task"] = 21  # type: ignore[index]
    with pytest.raises((TypeError, FrozenInstanceError)):
        evidence.parents[0]["artifact_path"] = "forged.json"  # type: ignore[index]
    with pytest.raises((TypeError, FrozenInstanceError)):
        evidence.capability_identity_ref["artifact_path"] = "forged.json"  # type: ignore[index]
    with pytest.raises(TypeError, match="immutable|mapping|dict|exact"):
        GateEvidence(
            **{
                **evidence.__dict__,
                "task_label_counts": defaultdict(int, {"task": 20}),
            }
        )


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("task_label_counts", {"task": True}),
        ("positive_counts", {"task": 1.0}),
        ("negative_counts", {"task": []}),
        ("no_data_counts", {"task": {"mutable": 1}}),
        ("competitive_count_by_task", {"task": -1}),
        ("calibration_error_by_task", {"task": float("nan")}),
        ("calibration_error_by_task", {"task": float("inf")}),
        ("calibration_error_by_task", {"task": True}),
        ("calibration_error_by_task", {"task": [{"mutable": 1}]}),
        ("capability_identity_ref", {"artifact_path": [], "artifact_sha256": "1" * 64}),
        ("parents", ({"artifact_path": "x.json", "artifact_sha256": {}},)),
    ],
)
def test_gate_evidence_public_constructor_rejects_non_scalar_mapping_values(
    field: str, invalid: object
) -> None:
    valid = {
        "evidence_class": EVIDENCE_CLASS,
        "unique_completed_subjects": 20,
        "task_label_counts": {"task": 20},
        "positive_counts": {"task": 10},
        "negative_counts": {"task": 10},
        "no_data_counts": {"task": 0},
        "calibration_error_by_task": {"task": 0.1},
        "competitive_count_by_task": {"task": 5},
        "selection_change_count": 1,
        "learned_utility": 0.7,
        "static_utility": 0.6,
        "high_risk_review_status": "NOT_APPLICABLE",
        "hash_audit_status": "PASS",
        "witness_audit_status": "PASS",
        "leakage_audit_status": "PASS",
        "parents": ({"artifact_path": "x.json", "artifact_sha256": "0" * 64},),
        "parent_created_at": (PARENT_AT,),
        "capability_identity_ref": {
            "artifact_path": "identity.json",
            "artifact_sha256": "1" * 64,
        },
        "governance_source_ref": ArtifactRef("source.json", "2" * 64),
        "school_id": "ziping",
        "task_id": "task",
        "claim_kind": ClaimKind.EVENT,
        "evidence_grade": ClaimEvidenceGrade.DIRECT,
        "capability_version": "v1",
        "provenance_verified": True,
    }
    valid[field] = invalid

    with pytest.raises(
        (TypeError, ValueError), match="scalar|integer|finite|string|bound"
    ):
        GateEvidence(**valid)  # type: ignore[arg-type]


def _gate_evidence_constructor_kwargs() -> dict[str, object]:
    return {
        "evidence_class": EVIDENCE_CLASS,
        "unique_completed_subjects": 20,
        "task_label_counts": {"task": 20},
        "positive_counts": {"task": 10},
        "negative_counts": {"task": 10},
        "no_data_counts": {"task": 0},
        "calibration_error_by_task": {"task": 0.1},
        "competitive_count_by_task": {"task": 5},
        "selection_change_count": 1,
        "learned_utility": 2.5,
        "static_utility": -0.5,
        "high_risk_review_status": "NOT_APPLICABLE",
        "hash_audit_status": "PASS",
        "witness_audit_status": "PASS",
        "leakage_audit_status": "PASS",
        "parents": ({"artifact_path": "x.json", "artifact_sha256": "0" * 64},),
        "parent_created_at": (PARENT_AT,),
    }


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("unique_completed_subjects", True),
        ("unique_completed_subjects", -1),
        ("unique_completed_subjects", 1.0),
        ("selection_change_count", True),
        ("claim_rows", -1),
        ("abstain_rows", 1.0),
        ("unsupported_rows", True),
        ("learned_utility", math.nan),
        ("learned_utility", math.inf),
        ("static_utility", -math.inf),
        ("static_utility", True),
        ("static_utility", []),
        ("parent_created_at", [PARENT_AT]),
        ("parent_created_at", ("not-utc",)),
        ("parent_created_at", (PARENT_AT, PARENT_AT)),
        ("evidence_class", "unknown"),
        ("high_risk_review_status", "PASS_FUTURE"),
        ("hash_audit_status", "UNKNOWN"),
        ("witness_audit_status", True),
        ("leakage_audit_status", []),
        ("governance_source_ref", {"artifact_path": "x", "artifact_sha256": "0" * 64}),
        ("school_id", ""),
        ("task_id", 1),
        ("capability_version", ""),
        ("claim_kind", "event"),
        ("evidence_grade", "direct"),
        ("provenance_verified", 1),
    ],
)
def test_gate_evidence_constructor_closes_top_level_scalar_schema(
    field: str, invalid: object
) -> None:
    values = _gate_evidence_constructor_kwargs()
    values[field] = invalid
    with pytest.raises((TypeError, ValueError)):
        GateEvidence(**values)  # type: ignore[arg-type]


def test_gate_evidence_constructor_requires_all_or_no_capability_identity() -> None:
    values = _gate_evidence_constructor_kwargs()
    values["capability_identity_ref"] = {
        "artifact_path": "identity.json",
        "artifact_sha256": "1" * 64,
    }
    with pytest.raises(ValueError, match="identity"):
        GateEvidence(**values)  # type: ignore[arg-type]

    values.update(
        governance_source_ref=ArtifactRef("source.json", "2" * 64),
        school_id="ziping",
        task_id="task",
        claim_kind=ClaimKind.EVENT,
        evidence_grade=ClaimEvidenceGrade.DIRECT,
        capability_version="v1",
        provenance_verified=True,
    )
    evidence = GateEvidence(**values)  # type: ignore[arg-type]
    assert replace(evidence, learned_utility=3.0).learned_utility == 3.0


def test_gate_evidence_exposes_authenticated_frozen_output_state_counts(
    tmp_path: Path,
) -> None:
    sources = _gate_sources(tmp_path, mutation="output_states")

    evidence = build_gate_evidence_from_cohorts(
        sources[0],
        scoring_artifact=sources[1],
        holdout_artifact=sources[2],
        audit_artifact=sources[3],
    )

    assert evidence.claim_rows == 18
    assert evidence.abstain_rows == 1
    assert evidence.unsupported_rows == 1


def test_mixed_identity_or_source_in_score_holdout_or_independent_audit_fails_closed(
    tmp_path: Path,
) -> None:
    claim, _, identity_ref = _identity(tmp_path)
    sources = _gate_sources(
        tmp_path,
        capability_identity_ref=identity_ref,
        task=claim.task_id,
    )
    score = json.loads(sources[1].read_text(encoding="utf-8"))
    score["rows"][0]["governance_source_ref"]["artifact_sha256"] = "0" * 64
    score.pop("artifact_sha256")
    sources[1].unlink()
    publish_new_json(sources[1], score, dry_run=False)

    with pytest.raises(ValueError, match="source|identity|lineage|score"):
        build_gate_evidence_from_cohorts(
            sources[0],
            scoring_artifact=sources[1],
            holdout_artifact=sources[2],
            audit_artifact=sources[3],
        )


def _evidence(tmp_path: Path, mutation: str | None = None) -> GateEvidence:
    sources = _gate_sources(tmp_path, mutation)
    return build_gate_evidence_from_cohorts(
        sources[0],
        scoring_artifact=sources[1],
        holdout_artifact=sources[2],
        audit_artifact=sources[3],
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "labels_14",
        "positive_zero",
        "negative_zero",
        "calibration_equal_0_2",
        "high_risk_unreviewed",
        "competitive_4",
        "selection_change_0",
        "learned_utility_lower",
        "hash_fail",
        "witness_fail",
        "leakage_fail",
    ],
)
def test_prediction_candidate_holds_on_each_missing_condition(
    tmp_path: Path, mutation: str
) -> None:
    result = evaluate_prediction_capability_candidate(
        _evidence(tmp_path, mutation),
        evaluated_at=EVALUATED_AT,
    )
    assert result["gate_id"] == "prediction_capability_candidate_gate_v1"
    assert result["status"] == "HOLD"
    assert result["unmet_conditions"]
    assert result["proposal_allowed"] is False
    assert result["production_switch"] is False


def test_prediction_candidate_go_only_creates_proposal_and_global_artifact(
    tmp_path: Path,
) -> None:
    evidence = _evidence(tmp_path)
    result = evaluate_prediction_capability_candidate(
        evidence,
        evaluated_at=EVALUATED_AT,
    )
    assert result["schema_version"] == "prediction-capability-candidate-gate/v1"
    assert result["status"] == "GO"
    assert result["proposal_allowed"] is True
    assert result["production_switch"] is False
    assert result["unmet_conditions"] == []
    assert set(result["checks"]) == {
        "evidence_class_is_immediate",
        "completed_subjects_at_least_20",
        "one_task_has_15_positive_and_negative",
        "same_eligible_task_calibration_below_0_2",
        "high_risk_reviews_pass",
        "one_competitive_task_at_least_5",
        "selection_changed",
        "utility_not_degraded",
        "hash_audit_pass",
        "witness_audit_pass",
        "leakage_audit_pass",
    }
    assert result["parents"] == list(evidence.parents)
    assert result["evaluated_at"] >= max(evidence.parent_created_at)
    assert result["artifact_sha256"]


def test_gate_evidence_requires_two_verified_cohorts_and_recursive_real_labels(
    tmp_path: Path,
) -> None:
    manifests, scoring, holdout, audit = _gate_sources(tmp_path)
    with pytest.raises(ValueError, match="20|subject|cohort"):
        build_gate_evidence_from_cohorts(
            manifests[:1],
            scoring_artifact=scoring,
            holdout_artifact=holdout,
            audit_artifact=audit,
        )
    Path(manifests[0]).write_bytes(Path(manifests[0]).read_bytes() + b" ")
    with pytest.raises(ValueError, match="hash|drift|manifest|verified"):
        build_gate_evidence_from_cohorts(
            manifests,
            scoring_artifact=scoring,
            holdout_artifact=holdout,
            audit_artifact=audit,
        )


@pytest.mark.parametrize("mutation", ["nan", "inf", "bool_count", "inconsistent_total"])
def test_malformed_or_inconsistent_source_rows_fail_closed(
    tmp_path: Path, mutation: str
) -> None:
    with pytest.raises(
        ValueError,
        match="finite|bool|scorable|label|inconsistent|lineage|prediction|probability",
    ):
        _evidence(tmp_path, mutation)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda evidence: replace(evidence, unique_completed_subjects=-1),
        lambda evidence: replace(evidence, selection_change_count=True),
        lambda evidence: replace(evidence, learned_utility=math.inf),
    ],
)
def test_caller_cannot_construct_invalid_top_level_derived_counts_or_metrics(
    tmp_path: Path,
    mutation,
) -> None:
    with pytest.raises((TypeError, ValueError), match="integer|non-negative|finite"):
        mutation(_evidence(tmp_path))


def test_caller_cannot_forge_derived_mapping_counts(tmp_path: Path) -> None:
    forged = replace(_evidence(tmp_path), task_label_counts={"career.role_change": 19})
    with pytest.raises(ValueError, match="reconstruction|count|inconsistent"):
        evaluate_prediction_capability_candidate(
            forged,
            evaluated_at=EVALUATED_AT,
        )


def test_duplicate_case_subject_or_label_identity_across_cohorts_is_rejected(
    tmp_path: Path,
) -> None:
    manifests, scoring, holdout, audit = _gate_sources(tmp_path)
    second = json.loads(manifests[1].read_text(encoding="utf-8"))
    first = json.loads(manifests[0].read_text(encoding="utf-8"))
    second["members"][0] = first["members"][0]
    second.pop("artifact_sha256")
    manifests[1].unlink()
    publish_new_json(manifests[1], second, dry_run=False)
    with pytest.raises(ValueError, match="duplicate|verified|reconstruction"):
        build_gate_evidence_from_cohorts(
            manifests,
            scoring_artifact=scoring,
            holdout_artifact=holdout,
            audit_artifact=audit,
        )


def test_score_rows_cannot_self_attest_prediction_or_calibration(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="score|field|prediction|calibration|schema"):
        _evidence(tmp_path, "forged_probability")


def test_holdout_competition_cannot_repeat_one_untraceable_row_five_times(
    tmp_path: Path,
) -> None:
    manifests, scoring, holdout, audit = _gate_sources(tmp_path)
    document = json.loads(holdout.read_text(encoding="utf-8"))
    document["rows"] = [document["rows"][0]] * 5
    document.pop("artifact_sha256")
    holdout.unlink()
    publish_new_json(holdout, document, dry_run=False)

    with pytest.raises(ValueError, match="holdout|duplicate|case|lineage|trace"):
        build_gate_evidence_from_cohorts(
            manifests,
            scoring_artifact=scoring,
            holdout_artifact=holdout,
            audit_artifact=audit,
        )


def test_bare_aggregate_audit_statuses_are_not_auditable_evidence(
    tmp_path: Path,
) -> None:
    manifests, scoring, holdout, audit = _gate_sources(tmp_path)
    document = json.loads(audit.read_text(encoding="utf-8"))
    document["parents"] = [_ref(holdout)]
    document.pop("artifact_sha256")
    audit.unlink()
    publish_new_json(audit, document, dry_run=False)

    with pytest.raises(ValueError, match="audit|parent|component|lineage"):
        build_gate_evidence_from_cohorts(
            manifests,
            scoring_artifact=scoring,
            holdout_artifact=holdout,
            audit_artifact=audit,
        )


def test_no_high_risk_labels_use_not_applicable_instead_of_forged_pass(
    tmp_path: Path,
) -> None:
    evidence = _evidence(tmp_path)

    assert evidence.high_risk_review_status == "NOT_APPLICABLE"
    result = evaluate_prediction_capability_candidate(
        evidence,
        evaluated_at=EVALUATED_AT,
    )
    assert result["checks"]["high_risk_reviews_pass"] is True


def test_school_gate_publication_explicitly_uses_operation_authority_root() -> None:
    module = ast.parse(Path("tools/school_capability_cohort.py").read_text("utf-8"))
    functions = {
        node.name: node
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    for owner_name in ("_gate", "_future_gate"):
        owner = functions[owner_name]
        authority_assignments = [
            node
            for node in ast.walk(owner)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "authority"
                for target in node.targets
            )
        ]
        operation_calls = [
            node
            for node in ast.walk(owner)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id
            in {
                "_build_gate_evidence_with_authority",
                "_build_future_gate_evidence_with_authority",
                "_evaluate_prediction_capability_candidate_with_authority",
                "_evaluate_future_empirical_with_authority",
            }
        ]
        publications = [
            node
            for node in ast.walk(owner)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "publish_new_json"
        ]

        assert authority_assignments
        assert len(operation_calls) == 2
        for call in operation_calls:
            operation_authority = next(
                keyword.value for keyword in call.keywords if keyword.arg == "authority"
            )
            assert isinstance(operation_authority, ast.Name)
            assert operation_authority.id == "authority"
        assert len(publications) == 1
        admitted_root = next(
            keyword.value
            for keyword in publications[0].keywords
            if keyword.arg == "admitted_root"
        )
        assert isinstance(admitted_root, ast.Call)
        assert isinstance(admitted_root.func, ast.Name)
        assert admitted_root.func.id == "_authority_root"
        assert isinstance(admitted_root.args[0], ast.Name)
        assert admitted_root.args[0].id == "authority"


def test_school_cli_does_not_expose_caller_controlled_root() -> None:
    import argparse

    from tools.school_capability_cohort import build_parser

    parsers = [build_parser()]
    option_strings: set[str] = set()
    while parsers:
        parser = parsers.pop()
        for action in parser._actions:
            option_strings.update(action.option_strings)
            if isinstance(action, argparse._SubParsersAction):
                parsers.extend(action.choices.values())
    assert "--admitted-root" not in option_strings


def test_gate_cli_is_create_only(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    manifests, scoring, holdout, audit = _gate_sources(tmp_path)
    output = tmp_path / "prediction-capability-candidate-gate-v1.json"
    command = ["gate"]
    for manifest in manifests:
        command.extend(("--manifest", str(manifest)))
    command.extend(
        (
            "--scores",
            str(scoring),
            "--holdout",
            str(holdout),
            "--audit",
            str(audit),
            "--evaluated-at",
            EVALUATED_AT,
            "--out",
            str(output),
        )
    )
    dry_code, dry_stdout, dry_stderr = _run_school_cli([*command, "--dry-run"], capsys)
    assert dry_code == 0, dry_stderr
    assert not output.exists()
    assert json.loads(dry_stdout)["result"]["status"] == "GO"
    first_code, _, first_stderr = _run_school_cli(command, capsys)
    assert first_code == 0, first_stderr
    original = output.read_bytes()
    second_code, _, second_stderr = _run_school_cli(command, capsys)
    assert second_code != 0
    assert "already exists" in second_stderr
    assert output.read_bytes() == original


def test_gate_cli_rejects_noncanonical_result_filename(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    manifests, scoring, holdout, audit = _gate_sources(tmp_path)
    output = tmp_path / "arbitrary-go.json"
    command = ["gate"]
    for manifest in manifests:
        command.extend(("--manifest", str(manifest)))
    command.extend(
        (
            "--scores",
            str(scoring),
            "--holdout",
            str(holdout),
            "--audit",
            str(audit),
            "--evaluated-at",
            EVALUATED_AT,
            "--out",
            str(output),
        )
    )

    return_code, _, stderr = _run_school_cli(command, capsys)

    assert return_code != 0
    assert "canonical" in stderr.lower() or "filename" in stderr.lower()
    assert not output.exists()


FUTURE_EVIDENCE_CLASS = "future_observation"
FUTURE_EVALUATED_AT = "2027-01-16T00:00:00Z"


def _future_case(
    root: Path,
    index: int,
    *,
    mutation: str | None = None,
    capability_identity_ref: ArtifactRef | None = None,
    task: str = "career.role_change",
) -> tuple[Path, dict]:
    completion, identity = _case(
        root,
        index,
        mutation="calibration_equal_0_2"
        if mutation == "calibration_equal_0_2"
        else None,
        capability_identity_ref=capability_identity_ref,
        task=task,
    )
    completion_document = json.loads(completion.read_text(encoding="utf-8"))
    frozen_ref = next(
        parent
        for parent in completion_document["parents"]
        if "frozen-run" in parent["artifact_path"]
    )
    frozen_path = Path(frozen_ref["artifact_path"])
    frozen_document = json.loads(frozen_path.read_text(encoding="utf-8"))
    question_path = completion.with_name(
        f"{identity['case_id']}--future-question-registration--v001.json"
    )
    question_ref = publish_new_json(
        question_path,
        {
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
        },
        dry_run=False,
    )
    frozen_document["parents"] = [question_ref.__dict__]
    frozen_document["future_question_registration_sha256"] = (
        question_ref.artifact_sha256
    )
    frozen_document.pop("artifact_sha256")
    frozen_path.unlink()
    publish_new_json(frozen_path, frozen_document, dry_run=False)
    completion_document["parents"] = [
        _ref(frozen_path)
        if parent["artifact_path"] == frozen_path.as_posix()
        else parent
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
    if (
        mutation in {"subjects_9", "labels_7", "window_unmatured", "no_data"}
        and index >= pending_from
    ):
        label = "no_data"
        scorable = False
        no_data_reason = (
            "window_unmatured" if mutation == "window_unmatured" else "no_data"
        )
    high_risk = mutation == "high_risk_reused" and index == 1
    if mutation == "premature_not_observed" and index == 1:
        label = "not_observed"
        observed_positive = False
    observation = {
        "future_task_id": identity["task_id"],
        "label": label,
        "scorable": scorable and not high_risk,
        "high_risk": high_risk,
        "observed_at": "2027-01-14T00:00:00Z"
        if mutation == "premature_not_observed" and index == 1
        else "2027-01-15T00:00:00Z",
        "collected_at": "2027-01-14T00:00:00Z"
        if mutation == "premature_not_observed" and index == 1
        else "2027-01-15T00:00:00Z",
        "observation_window": {
            "start_at": "2026-11-27T00:00:00Z",
            "end_at": "2027-01-15T00:00:00Z",
        },
        **({"no_data_reason": no_data_reason} if no_data_reason else {}),
        **({"review_status": "pending_independent_dual_review"} if high_risk else {}),
    }
    label_identity = canonical_artifact_sha256(
        {
            "case_id": identity["case_id"],
            "evidence_class": FUTURE_EVIDENCE_CLASS,
            "future_task_id": identity["task_id"],
            "observed_at": observation["observed_at"],
        }
    )
    unbound_path = completion.with_name(
        f"{identity['case_id']}--future-observation-unbound--v001.json"
    )
    _publish(
        unbound_path,
        {
            "schema_version": "prospective-future-observation-unbound/v1",
            "case_id": identity["case_id"],
            "subject_id_hash": identity["subject_id_hash"],
            "created_at": "2027-01-15T00:00:00Z",
            "evidence_class": FUTURE_EVIDENCE_CLASS,
            "label_identity": label_identity,
            "parents": [question_ref.__dict__, _ref(frozen_path)],
            "observation": observation,
        },
    )
    _publish(
        future_path,
        {
            "schema_version": "prospective-future-observation-bound/v1",
            "case_id": identity["case_id"],
            "subject_id_hash": identity["subject_id_hash"],
            "created_at": "2027-01-15T00:00:00Z",
            "evidence_class": FUTURE_EVIDENCE_CLASS,
            "label_identity": label_identity,
            "parents": [_ref(unbound_path)],
            "observation": observation,
        },
    )
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
        "label_identity": json.loads(future_path.read_text(encoding="utf-8"))[
            "label_identity"
        ],
        "observed_positive": observed_positive if observation["scorable"] else None,
        "scorable": observation["scorable"],
    }


def _future_gate_sources(
    tmp_path: Path,
    mutation: str | None = None,
    *,
    capability_identity_ref: ArtifactRef | None = None,
    task: str = "career.role_change",
) -> tuple[list[Path], Path, Path, Path]:
    cases = [
        _future_case(
            tmp_path / "future-cases",
            index,
            mutation=mutation,
            capability_identity_ref=capability_identity_ref,
            task=task,
        )
        for index in range(1, 11)
    ]
    historical = _historical_refs(tmp_path)
    manifest = build_cohort_manifest(
        [item[0] for item in cases],
        historical,
        created_at="2027-01-15T02:00:00Z",
    )
    manifest_path = tmp_path / "future-cohort.json"
    publish_new_json(manifest_path, manifest, dry_run=False)

    identity_value = (
        None
        if capability_identity_ref is None
        else {
            "artifact_path": capability_identity_ref.artifact_path,
            "artifact_sha256": capability_identity_ref.artifact_sha256,
        }
    )
    source_value = None
    if capability_identity_ref is not None:
        identity_document = json.loads(
            Path(capability_identity_ref.artifact_path).read_text(encoding="utf-8")
        )
        source_value = identity_document["parents"][0]

    rows = []
    for index, (completion, identity) in enumerate(cases, 1):
        completion_document = json.loads(completion.read_text(encoding="utf-8"))
        frozen_ref = next(
            parent
            for parent in completion_document["parents"]
            if "frozen-run" in parent["artifact_path"]
        )
        rows.append(
            {
                **identity,
                **(
                    {}
                    if identity_value is None
                    else {
                        "capability_identity_ref": identity_value,
                        "governance_source_ref": source_value,
                    }
                ),
                "frozen_prediction": {
                    **frozen_ref,
                    "school_id": "static",
                    "prediction_id": f"prediction-{index}",
                },
            }
        )
    score_path = tmp_path / "future-scores.json"
    _publish(
        score_path,
        {
            "schema_version": "prospective-future-score-rows/v1",
            "created_at": "2027-01-15T03:00:00Z",
            "evidence_class": FUTURE_EVIDENCE_CLASS,
            "parents": [_ref(manifest_path)],
            **(
                {}
                if identity_value is None
                else {
                    "capability_identity_ref": identity_value,
                    "governance_source_ref": source_value,
                }
            ),
            "rows": rows,
        },
    )
    competitive_count = (
        4 if mutation in {"competitive_4", "competition_not_applicable"} else 5
    )
    holdout_rows = []
    for index, row in enumerate(rows[:competitive_count]):
        holdout_rows.append(
            {
                "case_id": row["case_id"],
                "subject_id_hash": row["subject_id_hash"],
                "task_id": row["task_id"],
                "eligible": mutation != "competition_not_applicable",
                "competitive": mutation != "competition_not_applicable",
                "training_subject_ids": [
                    item[1]["subject_id_hash"] for item in cases[5:]
                ],
                "static_selection": "static",
                "learned_selection": "learned" if index == 0 else "static",
                "static_utility": 0.6,
                "learned_utility": 0.5 if mutation == "learned_utility_lower" else 0.7,
            }
        )
    if mutation == "selection_change_0":
        for row in holdout_rows:
            row["learned_selection"] = row["static_selection"]
    holdout_path = tmp_path / "future-holdout.json"
    _publish(
        holdout_path,
        {
            "schema_version": "prospective-future-competition-holdout/v1",
            "created_at": "2027-01-15T04:00:00Z",
            "evidence_class": FUTURE_EVIDENCE_CLASS,
            "parents": [_ref(score_path)],
            **(
                {}
                if identity_value is None
                else {
                    "capability_identity_ref": identity_value,
                    "governance_source_ref": source_value,
                }
            ),
            "rows": holdout_rows,
        },
    )
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
        _publish(
            path,
            {
                "schema_version": f"prospective-{name.replace('_status', '').replace('_', '-')}/v1",
                "created_at": "2027-01-15T05:00:00Z",
                "status": status,
                "evidence_class": FUTURE_EVIDENCE_CLASS,
                "parents": [_ref(holdout_path)],
                **(
                    {}
                    if identity_value is None
                    else {
                        "capability_identity_ref": identity_value,
                        "governance_source_ref": source_value,
                    }
                ),
                **(
                    {"review_evidence_class": EVIDENCE_CLASS}
                    if has_high_risk and name == "high_risk_review_status"
                    else {}
                ),
            },
        )
        component_refs.append(_ref(path))
    audit_path = tmp_path / "future-audits.json"
    _publish(
        audit_path,
        {
            "schema_version": "prospective-future-candidate-audits/v1",
            "created_at": "2027-01-15T06:00:00Z",
            "evidence_class": FUTURE_EVIDENCE_CLASS,
            "parents": component_refs,
            **(
                {}
                if identity_value is None
                else {
                    "capability_identity_ref": identity_value,
                    "governance_source_ref": source_value,
                }
            ),
            **statuses,
        },
    )
    return [manifest_path], score_path, holdout_path, audit_path


def _future_evidence(tmp_path: Path, mutation: str | None = None) -> GateEvidence:
    sources = _future_gate_sources(tmp_path, mutation)
    return build_future_gate_evidence_from_cohorts(
        sources[0],
        scoring_artifact=sources[1],
        holdout_artifact=sources[2],
        audit_artifact=sources[3],
    )


def test_future_gate_reconstruction_exposes_same_exact_typed_identity(
    tmp_path: Path,
) -> None:
    claim, identity, identity_ref = _identity(tmp_path, "future-identity")
    sources = _future_gate_sources(
        tmp_path,
        capability_identity_ref=identity_ref,
        task=claim.task_id,
    )

    evidence = build_future_gate_evidence_from_cohorts(
        sources[0],
        scoring_artifact=sources[1],
        holdout_artifact=sources[2],
        audit_artifact=sources[3],
    )

    assert evidence.capability_identity_ref == identity_ref.__dict__
    assert evidence.governance_source_ref == identity.governance_source_ref
    assert evidence.school_id == claim.school_id
    assert evidence.task_id == claim.task_id
    assert evidence.claim_kind is claim.claim_kind
    assert evidence.evidence_grade is claim.evidence_grade
    assert evidence.capability_version == claim.adapter_provenance.adapter_version


@pytest.mark.parametrize(
    "mutation",
    [
        "subjects_9",
        "labels_7",
        "positive_zero",
        "negative_zero",
        "window_unmatured",
        "calibration_equal_0_2",
        "high_risk_reused",
        "competitive_4",
        "competition_not_applicable",
        "selection_change_0",
        "learned_utility_lower",
        "parent_hash_fail",
    ],
)
def test_future_gate_holds_on_each_missing_condition(
    tmp_path: Path, mutation: str
) -> None:
    evidence = _future_evidence(tmp_path, mutation)
    if mutation == "calibration_equal_0_2":
        assert evidence.calibration_error_by_task[
            "career.role_change"
        ] == pytest.approx(0.2)
    result = evaluate_future_empirical(
        evidence,
        evaluated_at=FUTURE_EVALUATED_AT,
    )
    assert result["gate_id"] == "future_empirical_gate_v1"
    assert result["status"] == "HOLD"
    assert result["production_switch"] is False


def test_future_gate_go_recomputes_ten_completed_future_labels_from_frozen_predictions(
    tmp_path: Path,
) -> None:
    evidence = _future_evidence(tmp_path)
    result = evaluate_future_empirical(
        evidence,
        evaluated_at=FUTURE_EVALUATED_AT,
    )
    assert evidence.evidence_class == FUTURE_EVIDENCE_CLASS
    assert evidence.unique_completed_subjects == 10
    assert result["status"] == "GO"
    assert result["production_switch"] is False
    assert result["checks"]["fresh_high_risk_reviews_pass"] is True
    assert evidence.high_risk_review_status == "NOT_APPLICABLE"


def test_twenty_immediate_plus_ten_future_cannot_satisfy_historical_baseline(
    tmp_path: Path,
) -> None:
    immediate_root = (tmp_path / "immediate").absolute()
    future_root = (tmp_path / "future").absolute()
    immediate = evaluate_prediction_capability_candidate(
        _evidence(immediate_root),
        evaluated_at=FUTURE_EVALUATED_AT,
    )
    future = evaluate_future_empirical(
        _future_evidence(future_root),
        evaluated_at=FUTURE_EVALUATED_AT,
    )
    historical_path = tmp_path / "META" / "six-month-platform-gate-2026-07-15.json"
    historical_ref = ArtifactRef(
        historical_path.as_posix(),
        hashlib.sha256(historical_path.read_bytes()).hexdigest(),
    )
    report = build_three_gate_report(
        immediate,
        future,
        historical_ref,
    )
    assert "预测能力候选 GO" in report
    assert "未来实证 GO" in report
    assert "historical baseline（只读引用） HOLD" in report
    assert "30" not in report
    assert "已自动切生产" not in report
    assert "production_switch: false" in report


def test_future_gate_cli_and_three_gate_report_are_canonical_create_only(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    future_sources = _future_gate_sources(tmp_path / "future")
    future_out = tmp_path / "future-empirical-gate-v1.json"
    future_command = ["future-gate"]
    for manifest in future_sources[0]:
        future_command.extend(("--manifest", str(manifest)))
    future_command.extend(
        (
            "--scores",
            str(future_sources[1]),
            "--holdout",
            str(future_sources[2]),
            "--audit",
            str(future_sources[3]),
            "--evaluated-at",
            FUTURE_EVALUATED_AT,
            "--out",
            str(future_out),
        )
    )
    created_code, _, created_stderr = _run_school_cli(future_command, capsys)
    assert created_code == 0, created_stderr
    assert json.loads(future_out.read_text(encoding="utf-8"))["status"] == "GO"
    original = future_out.read_bytes()
    duplicate_code, _, _ = _run_school_cli(future_command, capsys)
    assert duplicate_code != 0
    assert future_out.read_bytes() == original

    immediate_sources = _gate_sources(tmp_path / "immediate")
    immediate_out = tmp_path / "prediction-capability-candidate-gate-v1.json"
    immediate_command = ["gate"]
    for manifest in immediate_sources[0]:
        immediate_command.extend(("--manifest", str(manifest)))
    immediate_command.extend(
        (
            "--scores",
            str(immediate_sources[1]),
            "--holdout",
            str(immediate_sources[2]),
            "--audit",
            str(immediate_sources[3]),
            "--evaluated-at",
            FUTURE_EVALUATED_AT,
            "--out",
            str(immediate_out),
        )
    )
    immediate_code, _, immediate_stderr = _run_school_cli(immediate_command, capsys)
    assert immediate_code == 0, immediate_stderr
    historical_json = tmp_path / "META" / "six-month-platform-gate-2026-07-15.json"
    report_out = tmp_path / "three-gate-report-v1.md"
    report_command = [
        "report",
        "--immediate-gate",
        str(immediate_out),
        "--future-gate",
        str(future_out),
        "--historical-json",
        str(historical_json),
        "--out",
        str(report_out),
    ]
    report_code, _, report_stderr = _run_school_cli(report_command, capsys)
    assert report_code == 0, report_stderr
    assert report_out.read_text(encoding="utf-8").count("## ") == 3
    report_original = report_out.read_bytes()
    duplicate_report_code, _, _ = _run_school_cli(report_command, capsys)
    assert duplicate_report_code != 0
    assert report_out.read_bytes() == report_original


def test_future_gate_rejects_claimed_completion_collected_before_actual_window_end(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="window|matur|collected"):
        _future_evidence(tmp_path, "premature_not_observed")


def test_three_gate_report_rejects_same_named_forged_historical_path(
    tmp_path: Path,
) -> None:
    forged = tmp_path / "attacker" / "six-month-platform-gate-2026-07-15.json"
    forged.parent.mkdir(parents=True)
    forged.write_text(
        '{"schema_version":"six-month-platform-gate/v1","status":"GO"}\n',
        encoding="utf-8",
    )
    ref = ArtifactRef(
        forged.as_posix(), hashlib.sha256(forged.read_bytes()).hexdigest()
    )
    immediate = {"gate_id": "prediction_capability_candidate_gate_v1", "status": "GO"}
    future = {"gate_id": "future_empirical_gate_v1", "status": "GO"}

    with pytest.raises(ValueError, match="historical|canonical|baseline|path|root"):
        build_three_gate_report(
            immediate,
            future,
            ref,
        )


def test_three_gate_report_binds_canonical_historical_md_hash_and_scopes_go_offline(
    tmp_path: Path,
) -> None:
    historical_path = tmp_path / "META" / "six-month-platform-gate-2026-07-15.json"
    ref = ArtifactRef(
        historical_path.as_posix(),
        hashlib.sha256(historical_path.read_bytes()).hexdigest(),
    )
    immediate = {"gate_id": "prediction_capability_candidate_gate_v1", "status": "GO"}
    future = {"gate_id": "future_empirical_gate_v1", "status": "GO"}

    report = build_three_gate_report(
        immediate,
        future,
        ref,
    )

    md_path = tmp_path / "META" / "six-month-platform-gate-2026-07-15.md"
    assert hashlib.sha256(md_path.read_bytes()).hexdigest() in report
    assert "离线候选门禁结果：GO（不代表平台 GO 或生产 GO）" in report
    assert "production_switch: false" in report


def test_immediate_aggregation_skips_future_only_member_in_mixed_manifest(
    tmp_path: Path,
) -> None:
    cases = [
        _future_case(tmp_path / "mixed-immediate", index) for index in range(1, 11)
    ]
    future_only = cases[-1][0]
    completion = json.loads(future_only.read_text(encoding="utf-8"))
    completion["retrospective_completion_status"] = "PENDING"
    completion["parents"] = [
        parent
        for parent in completion["parents"]
        if "immediate-retrospective" not in parent["artifact_path"]
    ]
    completion.pop("artifact_sha256")
    future_only.unlink()
    publish_new_json(future_only, completion, dry_run=False)
    manifest = build_cohort_manifest(
        [item[0] for item in cases],
        _historical_refs(tmp_path),
        created_at="2027-01-15T02:00:00Z",
    )

    labels, cases_seen, subjects_seen, frozen = _label_rows_from_manifests(
        [manifest], admitted_root=tmp_path.absolute()
    )

    assert len(labels) == 9
    assert len(cases_seen) == 9
    assert len(subjects_seen) == 9
    assert set(frozen) == cases_seen
    assert completion["case_id"] not in cases_seen


def test_future_aggregation_skips_retrospective_only_and_pending_future_members(
    tmp_path: Path,
) -> None:
    retrospective_only = [
        _case(tmp_path / "mixed-future", index) for index in range(1, 11)
    ]
    manifest = build_cohort_manifest(
        [item[0] for item in retrospective_only],
        _historical_refs(tmp_path),
        created_at=PARENT_AT,
    )

    labels, completed_cases, completed_subjects, frozen = (
        _future_label_rows_from_manifests(
            [manifest], authority=prospective_artifacts._repository_authority()
        )
    )

    assert labels == {}
    assert completed_cases == set()
    assert completed_subjects == set()
    assert frozen == {}


def test_future_aggregation_rejects_parentless_hand_forged_bound_artifact(
    tmp_path: Path,
) -> None:
    cases = [_future_case(tmp_path / "forged-future", index) for index in range(1, 11)]
    manifest = build_cohort_manifest(
        [item[0] for item in cases],
        _historical_refs(tmp_path),
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
        _ref(future_path)
        if parent["artifact_path"] == future_path.as_posix()
        else parent
        for parent in completion["parents"]
    ]
    completion.pop("artifact_sha256")
    completion_path.unlink()
    publish_new_json(completion_path, completion, dry_run=False)
    manifest = build_cohort_manifest(
        [
            member["parents"]["completion"]["artifact_path"]
            for member in manifest["members"]
        ],
        _historical_refs(tmp_path / "rebuilt"),
        created_at="2027-01-15T02:00:00Z",
    )

    with pytest.raises(
        ValueError, match="future|parent|lineage|unbound|registration|frozen"
    ):
        _future_label_rows_from_manifests(
            [manifest], authority=prospective_artifacts._repository_authority()
        )
