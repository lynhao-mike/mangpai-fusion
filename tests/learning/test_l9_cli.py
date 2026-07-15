from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from engine.learning.models import ConditionalIdentity, ConditionalLearningSignal
from engine.learning.repository import ConditionalLearningRepository


ROOT = Path(__file__).resolve().parents[2]


def _identity(task_id: str = "career.role_change") -> ConditionalIdentity:
    return ConditionalIdentity(
        school_id="ziping",
        task_id=task_id,
        chart_prototype_id="prototype-balanced",
        claim_type="binary_event",
        time_horizon="annual",
        evidence_completeness_band="complete",
    )


def _signal(signal_id: str, task_id: str = "career.role_change") -> ConditionalLearningSignal:
    return ConditionalLearningSignal(
        signal_id=signal_id,
        feedback_observation_id=f"obs-{signal_id}",
        claim_id=f"claim-{signal_id}",
        rule_id="rule-career-001",
        identity=_identity(task_id),
        verdict="hit",
        feedback_quality=1.0,
        attributable=True,
    )


def _posterior(n_eff: float, task_id: str = "career.role_change") -> dict[str, object]:
    return {
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


def _inputs(tmp_path: Path, signal: ConditionalLearningSignal, *, high_risk: bool = False) -> tuple[Path, Path, Path]:
    signals = tmp_path / "signals.json"
    signals.write_text(json.dumps([signal.to_dict()]), encoding="utf-8")
    config = tmp_path / "learning.yaml"
    config.write_text(
        "thresholds:\n"
        "  medium_n_eff: 5\n"
        "  mature_n_eff: 20\n"
        "  partial_weight: 0.5\n"
        "  max_posterior_delta: 0.08\n"
        "  large_change_delta: 0.05\n",
        encoding="utf-8",
    )
    catalog = tmp_path / "catalog.yaml"
    catalog.write_text(
        "tasks:\n"
        f"  - task_id: {signal.identity.task_id}\n"
        f"    high_risk: {'true' if high_risk else 'false'}\n",
        encoding="utf-8",
    )
    return signals, config, catalog


def _run(*args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "tools.conditional_learning", *(str(arg) for arg in args)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _common(repository_root: Path, signals: Path, config: Path, catalog: Path) -> list[object]:
    return [
        "--repository-root",
        repository_root,
        "--signals-file",
        signals,
        "--config",
        config,
        "--task-catalog",
        catalog,
        "--created-at",
        "2026-07-15T00:00:00Z",
    ]


def _seed(repository_root: Path, *, n_eff: float, task_id: str = "career.role_change") -> tuple[ConditionalLearningRepository, str]:
    repository = ConditionalLearningRepository(repository_root)
    snapshot_ref = repository.freeze_snapshot(
        [_posterior(n_eff, task_id)], None, [], "2026-07-14T00:00:00Z"
    )
    repository.apply_snapshot(snapshot_ref)
    return repository, snapshot_ref


def test_decide_dry_run_outputs_decision_without_writing_repository(tmp_path: Path) -> None:
    repository_root = tmp_path / "learning"
    signals, config, catalog = _inputs(tmp_path, _signal("sig-dry"))

    result = _run("decide", *_common(repository_root, signals, config, catalog), "--dry-run")

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["decisions"][0]["update_tier"] == "record_only"
    assert not repository_root.exists()


def test_apply_rejects_mature_update_without_explicit_approval(tmp_path: Path) -> None:
    repository_root = tmp_path / "learning"
    repository, parent = _seed(repository_root, n_eff=19)
    signals, config, catalog = _inputs(tmp_path, _signal("sig-mature"))
    approvals = tmp_path / "approvals.json"
    approvals.write_text('{"approved_decision_ids": []}', encoding="utf-8")

    result = _run(
        "apply", *_common(repository_root, signals, config, catalog), "--approval-file", approvals
    )

    assert result.returncode != 0
    assert "approval" in result.stderr.lower()
    assert repository.active_snapshot_ref() == parent


def test_apply_rejects_high_risk_update_without_explicit_approval(tmp_path: Path) -> None:
    task_id = "health.system_risk"
    repository_root = tmp_path / "learning"
    repository, parent = _seed(repository_root, n_eff=5, task_id=task_id)
    signals, config, catalog = _inputs(tmp_path, _signal("sig-risk", task_id), high_risk=True)
    approvals = tmp_path / "approvals.json"
    approvals.write_text('{"approved_decision_ids": []}', encoding="utf-8")

    result = _run(
        "apply", *_common(repository_root, signals, config, catalog), "--approval-file", approvals
    )

    assert result.returncode != 0
    assert "approval" in result.stderr.lower()
    assert repository.active_snapshot_ref() == parent


def test_approved_mature_apply_creates_snapshot(tmp_path: Path) -> None:
    repository_root = tmp_path / "learning"
    repository, parent = _seed(repository_root, n_eff=19)
    signals, config, catalog = _inputs(tmp_path, _signal("sig-approved"))
    decided = _run("decide", *_common(repository_root, signals, config, catalog), "--dry-run")
    decision_id = json.loads(decided.stdout)["decisions"][0]["decision_id"]
    approvals = tmp_path / "approvals.json"
    approvals.write_text(json.dumps({"approved_decision_ids": [decision_id]}), encoding="utf-8")

    result = _run(
        "apply", *_common(repository_root, signals, config, catalog), "--approval-file", approvals
    )

    assert result.returncode == 0, result.stderr
    decision = json.loads(result.stdout)["decisions"][0]
    assert decision["applied"] is True
    assert decision["snapshot_ref"] != parent
    assert repository.active_snapshot_ref() == decision["snapshot_ref"]


def test_apply_dry_run_does_not_change_repository(tmp_path: Path) -> None:
    repository_root = tmp_path / "learning"
    repository, parent = _seed(repository_root, n_eff=4)
    signals, config, catalog = _inputs(tmp_path, _signal("sig-apply-dry"))
    approvals = tmp_path / "approvals.json"
    approvals.write_text('{"approved_decision_ids": []}', encoding="utf-8")
    before = {path.relative_to(repository_root): path.read_bytes() for path in repository_root.rglob("*") if path.is_file()}

    result = _run(
        "apply",
        *_common(repository_root, signals, config, catalog),
        "--approval-file",
        approvals,
        "--dry-run",
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["decisions"][0]["applied"] is True
    after = {path.relative_to(repository_root): path.read_bytes() for path in repository_root.rglob("*") if path.is_file()}
    assert after == before
    assert repository.active_snapshot_ref() == parent


def test_rollback_restores_parent_and_dry_run_leaves_pointer_unchanged(tmp_path: Path) -> None:
    repository_root = tmp_path / "learning"
    repository, parent = _seed(repository_root, n_eff=4)
    child = repository.freeze_snapshot(
        [_posterior(5)], parent, ["decision-child"], "2026-07-15T00:00:00Z"
    )
    repository.apply_snapshot(child)

    dry_run = _run(
        "rollback", "--repository-root", repository_root, "--snapshot-ref", child, "--dry-run"
    )
    assert dry_run.returncode == 0, dry_run.stderr
    assert json.loads(dry_run.stdout)["active_snapshot_ref"] == parent
    assert repository.active_snapshot_ref() == child

    result = _run("rollback", "--repository-root", repository_root, "--snapshot-ref", child)
    assert result.returncode == 0, result.stderr
    assert repository.active_snapshot_ref() == parent


def test_invalid_signal_file_returns_nonzero_with_readable_stderr(tmp_path: Path) -> None:
    repository_root = tmp_path / "learning"
    signals, config, catalog = _inputs(tmp_path, _signal("sig-invalid"))
    signals.write_text("not-json", encoding="utf-8")

    result = _run("decide", *_common(repository_root, signals, config, catalog), "--dry-run")

    assert result.returncode != 0
    assert result.stderr.strip()
