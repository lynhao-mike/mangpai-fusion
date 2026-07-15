from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from engine.learning.models import ConditionalIdentity, ConditionalLearningSignal
from engine.learning.repository import ConditionalLearningRepository


def _signal(signal_id: str = "sig-001") -> ConditionalLearningSignal:
    return ConditionalLearningSignal(
        signal_id=signal_id,
        feedback_observation_id="obs-001",
        claim_id="claim-001",
        rule_id="rule-001",
        identity=ConditionalIdentity(
            school_id="ziping",
            task_id="career.role_change",
            chart_prototype_id="prototype-balanced",
            claim_type="binary_event",
            time_horizon="annual",
            evidence_completeness_band="complete",
        ),
        verdict="hit",
        feedback_quality=1.0,
        attributable=True,
    )


def _posterior(mean: float, n_eff: float) -> dict[str, object]:
    return {
        "school_id": "ziping",
        "task_id": "career.role_change",
        "chart_prototype_id": "prototype-balanced",
        "claim_type": "binary_event",
        "time_horizon": "annual",
        "evidence_completeness_band": "complete",
        "coverage_rate": 1.0,
        "discrimination_score": 0.3,
        "accuracy_score": mean,
        "calibration_error": 0.1,
        "posterior_mean": mean,
        "credible_interval": [0.4, 0.8],
        "n_eff": n_eff,
        "evidence_grade": "E3",
        "last_evaluated_at": "2026-07-15T00:00:00Z",
        "incremental_gain": 0.0,
    }


def test_same_canonical_payload_produces_same_content_hash(tmp_path: Path) -> None:
    repository = ConditionalLearningRepository(tmp_path / "learning")
    first = repository.freeze_snapshot(
        posteriors=[_posterior(0.6, 5)],
        parent_snapshot_ref=None,
        decision_ids=["d-2", "d-1"],
        created_at="2026-07-15T00:00:00Z",
    )
    second = repository.freeze_snapshot(
        posteriors=[dict(reversed(list(_posterior(0.6, 5).items())))],
        parent_snapshot_ref=None,
        decision_ids=["d-2", "d-1"],
        created_at="2026-07-15T00:00:00Z",
    )
    assert first == second
    assert (repository.snapshots_dir / f"{first.removeprefix('sha256:')}.json").is_file()


def test_existing_snapshot_is_never_overwritten(tmp_path: Path) -> None:
    repository = ConditionalLearningRepository(tmp_path / "learning")
    ref = repository.freeze_snapshot([_posterior(0.6, 5)], None, ["d-1"], "2026-07-15T00:00:00Z")
    path = repository.snapshot_path(ref)
    original = path.read_bytes()

    assert repository.freeze_snapshot([_posterior(0.6, 5)], None, ["d-1"], "2026-07-15T00:00:00Z") == ref
    assert path.read_bytes() == original


def test_active_pointer_uses_replace_without_leaving_temporary_file(tmp_path: Path) -> None:
    repository = ConditionalLearningRepository(tmp_path / "learning")
    ref = repository.freeze_snapshot([_posterior(0.6, 5)], None, ["d-1"], "2026-07-15T00:00:00Z")
    repository.apply_snapshot(ref)

    assert json.loads(repository.active_path.read_text(encoding="utf-8"))["snapshot_ref"] == ref
    assert not list(repository.root.glob("active.json.*.tmp"))


def test_rollback_restores_parent_content_without_deleting_child(tmp_path: Path) -> None:
    repository = ConditionalLearningRepository(tmp_path / "learning")
    parent = repository.freeze_snapshot([_posterior(0.6, 5)], None, ["d-1"], "2026-07-15T00:00:00Z")
    child = repository.freeze_snapshot([_posterior(0.7, 6)], parent, ["d-2"], "2026-07-15T01:00:00Z")
    repository.apply_snapshot(child)

    restored = repository.rollback(child)

    assert restored == parent
    assert repository.load_active_snapshot()["content_hash"] == parent
    assert repository.snapshot_path(child).exists()


def test_rollback_root_snapshot_has_no_parent(tmp_path: Path) -> None:
    repository = ConditionalLearningRepository(tmp_path / "learning")
    root_ref = repository.freeze_snapshot([_posterior(0.6, 5)], None, [], "2026-07-15T00:00:00Z")
    with pytest.raises(ValueError, match="parent"):
        repository.rollback(root_ref)


def test_missing_snapshot_fails_loudly(tmp_path: Path) -> None:
    repository = ConditionalLearningRepository(tmp_path / "learning")
    with pytest.raises(FileNotFoundError, match="snapshot"):
        repository.apply_snapshot("sha256:" + "0" * 64)


def test_signal_audit_is_append_only_jsonl(tmp_path: Path) -> None:
    repository = ConditionalLearningRepository(tmp_path / "learning")
    repository.record_signal(_signal("sig-001"))
    repository.record_signal(_signal("sig-002"))
    rows = [json.loads(line) for line in repository.signals_path.read_text(encoding="utf-8").splitlines()]
    assert [row["signal_id"] for row in rows] == ["sig-001", "sig-002"]


def test_repository_never_mutates_external_historical_run_snapshot(tmp_path: Path) -> None:
    historical = tmp_path / "history" / "case.run.json"
    historical.parent.mkdir()
    historical.write_bytes(b'{"sealed":true,"result":"original"}\n')
    before = hashlib.sha256(historical.read_bytes()).hexdigest()

    repository = ConditionalLearningRepository(tmp_path / "learning")
    repository.record_signal(_signal())
    ref = repository.freeze_snapshot([_posterior(0.6, 5)], None, [], "2026-07-15T00:00:00Z")
    repository.apply_snapshot(ref)

    assert hashlib.sha256(historical.read_bytes()).hexdigest() == before
    assert {path.name for path in repository.root.iterdir()} <= {
        "signals.jsonl", "decisions.jsonl", "reviews.jsonl", "snapshots", "active.json"
    }
