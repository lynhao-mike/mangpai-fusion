from __future__ import annotations

import hashlib
from pathlib import Path

from engine.decision.capability_registry import CapabilityRegistry
from engine.learning.models import ConditionalIdentity, ConditionalLearningSignal, LearningThresholds
from engine.learning.repository import ConditionalLearningRepository
from engine.learning.service import process_learning_signals


def _identity(task_id: str = "career.role_change") -> ConditionalIdentity:
    return ConditionalIdentity(
        school_id="ziping",
        task_id=task_id,
        chart_prototype_id="prototype-balanced",
        claim_type="binary_event",
        time_horizon="annual",
        evidence_completeness_band="complete",
    )


def _signal(
    signal_id: str,
    *,
    verdict: str = "hit",
    attributable: bool = True,
    task_id: str = "career.role_change",
) -> ConditionalLearningSignal:
    return ConditionalLearningSignal(
        signal_id=signal_id,
        feedback_observation_id=f"obs-{signal_id}",
        claim_id=f"claim-{signal_id}",
        rule_id="rule-career-001",
        identity=_identity(task_id),
        verdict=verdict,
        feedback_quality=1.0,
        attributable=attributable,
    )


def _row(*, n_eff: float, mean: float = 0.6, task_id: str = "career.role_change") -> dict[str, object]:
    return {
        **_identity(task_id).to_dict(),
        "coverage_rate": 1.0,
        "discrimination_score": 0.3,
        "accuracy_score": mean,
        "calibration_error": 0.1,
        "posterior_mean": mean,
        "credible_interval": [0.4, 0.8],
        "n_eff": n_eff,
        "evidence_grade": "E3",
        "last_evaluated_at": "2026-07-14T00:00:00Z",
        "incremental_gain": 0.0,
    }


def _thresholds() -> LearningThresholds:
    return LearningThresholds(5, 20, 0.5, 0.08, 0.05)


def _catalog(tmp_path: Path, *, high_risk: bool = False, task_id: str = "career.role_change") -> Path:
    path = tmp_path / "catalog.yaml"
    path.write_text(
        "schema_version: school-capability-tasks/v1\n"
        "tasks:\n"
        f"  - task_id: {task_id}\n"
        f"    high_risk: {'true' if high_risk else 'false'}\n",
        encoding="utf-8",
    )
    return path


def _seed(repository: ConditionalLearningRepository, row: dict[str, object]) -> str:
    ref = repository.freeze_snapshot([row], None, [], "2026-07-14T00:00:00Z")
    repository.apply_snapshot(ref)
    return ref


def _run(
    repository: ConditionalLearningRepository,
    catalog: Path,
    signals: list[ConditionalLearningSignal],
    approvals: set[str] | None = None,
):
    return process_learning_signals(
        signals,
        repository=repository,
        thresholds=_thresholds(),
        task_catalog_path=catalog,
        approval_decision_ids=approvals or set(),
        created_at="2026-07-15T00:00:00Z",
    )


def test_medium_sample_updates_l1_exact_six_dimension_registry_cell(tmp_path: Path) -> None:
    repository = ConditionalLearningRepository(tmp_path / "learning")
    parent = _seed(repository, _row(n_eff=4))

    decisions = _run(repository, _catalog(tmp_path), [_signal("sig-medium")])

    assert decisions[0].update_tier == "adjust_applicability"
    assert decisions[0].applied is True
    assert decisions[0].snapshot_ref != parent
    active_path = repository.snapshot_path(decisions[0].snapshot_ref or "")
    query = CapabilityRegistry.from_snapshot(active_path).query(**_identity().to_dict())
    assert query.shrink_level == "exact"
    assert query.n_eff == 5
    assert query.posterior_mean == decisions[0].proposed_posterior_mean


def test_low_sample_records_signal_but_keeps_active_snapshot_unchanged(tmp_path: Path) -> None:
    repository = ConditionalLearningRepository(tmp_path / "learning")
    parent = _seed(repository, _row(n_eff=2))

    decisions = _run(repository, _catalog(tmp_path), [_signal("sig-low")])

    assert decisions[0].update_tier == "record_only"
    assert decisions[0].applied is False
    assert repository.active_snapshot_ref() == parent
    assert repository.signals_path.is_file()


def test_mature_sample_is_not_applied_without_explicit_decision_approval(tmp_path: Path) -> None:
    repository = ConditionalLearningRepository(tmp_path / "learning")
    parent = _seed(repository, _row(n_eff=19))

    decisions = _run(repository, _catalog(tmp_path), [_signal("sig-mature")])

    assert decisions[0].update_tier == "adjust_rule_prior"
    assert decisions[0].requires_human_approval is True
    assert decisions[0].applied is False
    assert repository.active_snapshot_ref() == parent


def test_mature_sample_applies_after_explicit_decision_approval(tmp_path: Path) -> None:
    repository = ConditionalLearningRepository(tmp_path / "learning")
    _seed(repository, _row(n_eff=19))
    catalog = _catalog(tmp_path)
    proposed = _run(repository, catalog, [_signal("sig-mature")])[0]

    applied = _run(repository, catalog, [_signal("sig-mature")], {proposed.decision_id})[0]

    assert applied.applied is True
    assert applied.snapshot_ref is not None
    snapshot = repository.load_active_snapshot()
    assert snapshot is not None
    assert snapshot["posteriors"][0]["n_eff"] == 20
    assert snapshot["rule_prior_proposals"][0]["rule_id"] == "rule-career-001"


def test_high_risk_medium_sample_does_not_apply_without_approval(tmp_path: Path) -> None:
    repository = ConditionalLearningRepository(tmp_path / "learning")
    parent = _seed(repository, _row(n_eff=5, task_id="health.system_risk"))

    decisions = _run(
        repository,
        _catalog(tmp_path, high_risk=True, task_id="health.system_risk"),
        [_signal("sig-risk", task_id="health.system_risk")],
    )

    assert decisions[0].requires_human_approval is True
    assert decisions[0].applied is False
    assert repository.active_snapshot_ref() == parent
    assert "high_risk" in decisions[0].audit["review_reasons"]


def test_unattributable_signal_is_record_only_and_enters_review_without_distribution(tmp_path: Path) -> None:
    repository = ConditionalLearningRepository(tmp_path / "learning")
    parent = _seed(repository, _row(n_eff=10))

    decisions = _run(
        repository,
        _catalog(tmp_path),
        [_signal("sig-no-data", verdict="no_data", attributable=False)],
    )

    assert decisions[0].update_tier == "record_only"
    assert decisions[0].applied is False
    assert decisions[0].n_eff_before == decisions[0].n_eff_after == 10
    assert decisions[0].proposed_delta == 0
    assert repository.active_snapshot_ref() == parent
    assert "unattributable" in repository.reviews_path.read_text(encoding="utf-8")


def test_service_never_writes_theory_or_static_weight_files(tmp_path: Path) -> None:
    repository = ConditionalLearningRepository(tmp_path / "learning")
    _seed(repository, _row(n_eff=19))
    protected = [
        Path("engine/expert-weights.yaml"),
        Path("engine/domain-weights.yaml"),
        Path("theory/ziping/index.yaml"),
    ]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected}

    proposed = _run(repository, _catalog(tmp_path), [_signal("sig-protected")])[0]
    _run(repository, _catalog(tmp_path), [_signal("sig-protected")], {proposed.decision_id})

    assert {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in protected} == before


def test_signals_for_same_identity_are_recomputed_sequentially(tmp_path: Path) -> None:
    repository = ConditionalLearningRepository(tmp_path / "learning")
    _seed(repository, _row(n_eff=4))

    decisions = _run(
        repository,
        _catalog(tmp_path),
        [_signal("sig-first"), _signal("sig-second", verdict="miss")],
    )

    assert decisions[0].n_eff_before == 4
    assert decisions[0].n_eff_after == decisions[1].n_eff_before == 5
    assert decisions[1].n_eff_after == 6
    assert repository.load_active_snapshot()["posteriors"][0]["n_eff"] == 6  # type: ignore[index]
