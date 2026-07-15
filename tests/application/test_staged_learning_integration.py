from __future__ import annotations

from pathlib import Path

import pytest

from engine.application.staged_parallel_runner import ParallelRun
from engine.claims import Claim, Evidence, TimeWindow
from engine.decision.l6_staged_arbitration import ConflictRuleSet
from engine.evaluation.freeze import freeze_outputs
from engine.evaluation.models import BlindPrediction, BlindSchoolOutput
from engine.learning.models import ConditionalIdentity, ConditionalLearningSignal, LearningThresholds
from engine.learning.repository import ConditionalLearningRepository


def _claim(
    claim_id: str,
    *,
    school_id: str,
    task_id: str,
    claim_type: str,
    stance: str = "support",
    high_risk: bool = False,
) -> Claim:
    return Claim(
        claim_id=claim_id,
        school_id=school_id,
        task_id=task_id,
        claim_type=claim_type,  # type: ignore[arg-type]
        stance=stance,  # type: ignore[arg-type]
        statement=claim_id,
        evidence=(Evidence(f"e-{claim_id}", ("four_pillars.day",), (), f"r-{claim_id}", "fixture"),),
        falsifier="fixture falsifier",
        time_window=TimeWindow(2026, 2026) if claim_type != "structure_claim" else None,
        confidence_basis="fixture",
        applicability_snapshot={"domain": "健康" if high_risk else "事业"},
        domain="健康" if high_risk else "事业",
        confidence=0.8,
        high_risk=high_risk,
        target_id=task_id,
    )


def _parallel(*claims: Claim):
    outputs = [
        BlindSchoolOutput(
            case_id="C-TASK11",
            school_id=claim.school_id,
            task_id=claim.task_id,
            state="claim",
            rationale="fixture",
            predictions=[
                BlindPrediction(
                    prediction_id=f"p-{claim.claim_id}",
                    event_label=claim.statement,
                    probability=claim.confidence,
                    time_window=claim.time_window.to_dict() if claim.time_window else {},
                    evidence_refs=[item.evidence_id for item in claim.evidence],
                    falsifier=claim.falsifier,
                )
            ],
        )
        for claim in claims
    ]
    frozen = freeze_outputs(outputs, "tasks/v1", "rules/v1")
    object.__setattr__(frozen, "staged_claims", tuple(claims))
    return ParallelRun("C-TASK11", None, frozen)


def _identity(task_id: str = "career.role_change") -> ConditionalIdentity:
    return ConditionalIdentity("ziping", task_id, "balanced", "binary_event", "annual", "complete")


def _signal(
    signal_id: str,
    *,
    task_id: str = "career.role_change",
    verdict: str = "hit",
    attributable: bool = True,
) -> ConditionalLearningSignal:
    return ConditionalLearningSignal(
        signal_id=signal_id,
        feedback_observation_id=f"obs-{signal_id}",
        claim_id=f"claim-{signal_id}",
        rule_id="rule-1",
        identity=_identity(task_id),
        verdict=verdict,
        feedback_quality=1.0,
        attributable=attributable,
    )


def _thresholds() -> LearningThresholds:
    return LearningThresholds(5, 20, 0.5, 0.08, 0.05)


def _catalog(tmp_path: Path, *, high_risk: bool = False, task_id: str = "career.role_change") -> Path:
    path = tmp_path / f"{task_id.replace('.', '-')}.yaml"
    path.write_text(
        "schema_version: school-capability-tasks/v1\n"
        "tasks:\n"
        f"  - task_id: {task_id}\n"
        f"    high_risk: {'true' if high_risk else 'false'}\n",
        encoding="utf-8",
    )
    return path


def _seed(repository: ConditionalLearningRepository, *, n_eff: float, task_id: str = "career.role_change") -> str:
    row = {
        **_identity(task_id).to_dict(),
        "coverage_rate": 1.0,
        "discrimination_score": 0.3,
        "accuracy_score": 0.6,
        "calibration_error": 0.1,
        "posterior_mean": 0.6,
        "credible_interval": [0.4, 0.8],
        "n_eff": n_eff,
        "evidence_grade": "E3",
        "last_evaluated_at": "2026-07-14T00:00:00Z",
        "incremental_gain": 0.0,
    }
    ref = repository.freeze_snapshot([row], None, [], "2026-07-14T00:00:00Z")
    repository.apply_snapshot(ref)
    return ref


def _process(signal, repository, catalog):
    from engine.learning.service import process_feedback_signal

    return process_feedback_signal(
        signal,
        repository,
        thresholds=_thresholds(),
        task_catalog_path=catalog,
        created_at="2026-07-15T00:00:00Z",
    )


def test_parallel_claim_snapshot_produces_structure_event_and_timing_decisions() -> None:
    from engine.application.staged_parallel_runner import run_parallel_with_arbitration

    parallel = _parallel(
        _claim("structure", school_id="ziping", task_id="career.structure", claim_type="structure_claim"),
        _claim("event", school_id="duan", task_id="career.event", claim_type="event_claim"),
        _claim("timing", school_id="ren", task_id="career.timing", claim_type="timing_claim"),
    )

    decision_run = run_parallel_with_arbitration(parallel, route_plan={
        "career.structure": "ziping",
        "career.event": "duan",
        "career.timing": "ren",
    })

    assert [stage.stage for stage in decision_run.stages] == ["structure", "event", "timing"]
    assert [stage.winner_claim_ids for stage in decision_run.stages] == [
        ("structure",),
        ("event",),
        ("timing",),
    ]
    assert decision_run.weight_source == "l1_capability"


def test_high_risk_opposition_without_l1_route_remains_unresolved() -> None:
    from engine.application.staged_parallel_runner import run_parallel_with_arbitration

    parallel = _parallel(
        _claim("risk", school_id="gao", task_id="health.severe", claim_type="event_claim", high_risk=True),
        _claim("safe", school_id="ren", task_id="health.severe", claim_type="event_claim", stance="oppose", high_risk=True),
    )

    decision = run_parallel_with_arbitration(parallel).stage("event")

    assert decision.result == "unresolved"
    assert set(decision.minority_claim_ids) == {"risk", "safe"}


def test_missing_l1_route_uses_uniform_fallback_and_missing_snapshot_is_empty() -> None:
    from engine.application.staged_parallel_runner import run_parallel_with_arbitration

    with_claim = run_parallel_with_arbitration(
        _parallel(_claim("event", school_id="duan", task_id="career.event", claim_type="event_claim"))
    )
    empty = run_parallel_with_arbitration(ParallelRun("C-EMPTY", None, None))

    assert with_claim.weight_source == "uniform_fallback"
    assert empty.weight_source == "uniform_fallback"
    assert [item.result for item in empty.stages] == ["reject_all", "reject_all", "reject_all"]


def test_unattributable_no_data_feedback_is_record_only(tmp_path: Path) -> None:
    repository = ConditionalLearningRepository(tmp_path / "learning")
    parent = _seed(repository, n_eff=10)

    decision = _process(
        _signal("no-data", verdict="no_data", attributable=False),
        repository,
        _catalog(tmp_path),
    )

    assert decision.update_tier == "record_only"
    assert decision.applied is False
    assert repository.active_snapshot_ref() == parent


def test_low_sample_feedback_is_record_only(tmp_path: Path) -> None:
    repository = ConditionalLearningRepository(tmp_path / "learning")
    parent = _seed(repository, n_eff=2)

    decision = _process(_signal("low"), repository, _catalog(tmp_path))

    assert decision.update_tier == "record_only"
    assert decision.applied is False
    assert repository.active_snapshot_ref() == parent


def test_failed_apply_keeps_parent_snapshot_active(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repository = ConditionalLearningRepository(tmp_path / "learning")
    parent = _seed(repository, n_eff=4)

    def fail_apply(snapshot_ref: str) -> None:
        raise RuntimeError(f"cannot apply {snapshot_ref}")

    monkeypatch.setattr(repository, "apply_snapshot", fail_apply)

    with pytest.raises(RuntimeError, match="cannot apply"):
        _process(_signal("apply-fails"), repository, _catalog(tmp_path))

    assert repository.active_snapshot_ref() == parent


def test_arbitration_rerun_does_not_mutate_frozen_history_bytes() -> None:
    from engine.application.staged_parallel_runner import run_parallel_with_arbitration

    parallel = _parallel(_claim("event", school_id="duan", task_id="career.event", claim_type="event_claim"))
    assert parallel.claim_snapshot is not None
    before = parallel.claim_snapshot.freeze_hash

    first = run_parallel_with_arbitration(parallel, conflict_rules=ConflictRuleSet.empty())
    second = run_parallel_with_arbitration(parallel, conflict_rules=ConflictRuleSet.empty())

    assert first == second
    assert parallel.claim_snapshot.freeze_hash == before
