from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


def _module():
    try:
        return importlib.import_module("engine.decision.capability_registry")
    except ModuleNotFoundError as exc:
        pytest.fail(f"capability registry module is missing: {exc}")


def _posterior(
    school: str,
    task: str,
    prototype: str,
    *,
    mean: float,
    interval: tuple[float, float],
    n_eff: float,
    claim_type: str = "binary_event",
    horizon: str = "lifetime",
    completeness: str = "complete",
    gain: float = 0.0,
    grade: str = "E3",
) -> dict[str, object]:
    return {
        "school_id": school,
        "task_id": task,
        "chart_prototype_id": prototype,
        "claim_type": claim_type,
        "time_horizon": horizon,
        "evidence_completeness_band": completeness,
        "coverage_rate": 1.0,
        "discrimination_score": 0.3,
        "accuracy_score": mean,
        "calibration_error": 0.1,
        "posterior_mean": mean,
        "credible_interval": list(interval),
        "n_eff": n_eff,
        "evidence_grade": grade,
        "last_evaluated_at": "2026-07-14T00:00:00Z",
        "incremental_gain": gain,
    }


def _snapshot(tmp_path: Path, rows: list[dict[str, object]]) -> Path:
    path = tmp_path / "capability.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "school-capability-scores/v1",
                "freeze_hash": "freeze-123",
                "evaluated_at": "2026-07-14T00:00:00Z",
                "posteriors": rows,
            }
        ),
        encoding="utf-8",
    )
    return path


def _query(registry, **changes: str):
    identity = {
        "school_id": "ziping",
        "task_id": "career.role_change",
        "chart_prototype_id": "prototype-balanced",
        "claim_type": "binary_event",
        "time_horizon": "lifetime",
        "evidence_completeness_band": "complete",
    }
    identity.update(changes)
    return registry.query(**identity)


def test_exact_query_returns_traceable_snapshot_identity(tmp_path: Path) -> None:
    module = _module()
    row = _posterior("ziping", "career.role_change", "prototype-balanced", mean=0.82, interval=(0.7, 0.9), n_eff=12, gain=0.08)

    registry = module.CapabilityRegistry.from_snapshot(_snapshot(tmp_path, [row]))
    result = _query(registry)

    assert registry.snapshot_id.startswith("cap-")
    assert result.posterior_mean == 0.82
    assert result.incremental_gain == 0.08
    assert result.shrink_level == "exact"
    assert result.resolved_identity["chart_prototype_id"] == "prototype-balanced"


def test_low_sample_exact_cell_shrinks_to_prototype_backoff_with_wider_interval(tmp_path: Path) -> None:
    module = _module()
    rows = [
        _posterior("ziping", "career.role_change", "prototype-balanced", mean=0.95, interval=(0.8, 1.0), n_eff=2),
        _posterior("ziping", "career.role_change", "prototype-balanced", mean=0.72, interval=(0.58, 0.84), n_eff=8, horizon="ten_year"),
    ]

    result = _query(module.CapabilityRegistry.from_snapshot(_snapshot(tmp_path, rows)))

    assert result.shrink_level == "prototype_backoff"
    assert result.n_eff == 8
    assert result.credible_interval[0] < 0.58
    assert result.credible_interval[1] > 0.84


def test_missing_prototype_backs_off_to_task_then_domain_prior(tmp_path: Path) -> None:
    module = _module()
    task_rows = [
        _posterior("ziping", "career.role_change", "prototype-a", mean=0.8, interval=(0.65, 0.9), n_eff=6),
        _posterior("ziping", "career.role_change", "prototype-b", mean=0.6, interval=(0.45, 0.75), n_eff=6),
    ]
    task_result = _query(
        module.CapabilityRegistry.from_snapshot(_snapshot(tmp_path, task_rows)),
        chart_prototype_id="prototype-never-seen",
    )
    assert task_result.shrink_level == "task_backoff"

    domain_rows = [
        _posterior("ziping", "career.path_type", "prototype-a", mean=0.74, interval=(0.6, 0.85), n_eff=7, claim_type="categorical_state"),
        _posterior("ziping", "career.change_window", "prototype-b", mean=0.68, interval=(0.5, 0.82), n_eff=7, claim_type="event_timing"),
    ]
    domain_result = _query(
        module.CapabilityRegistry.from_snapshot(_snapshot(tmp_path, domain_rows)),
        task_id="career.unknown_task",
        chart_prototype_id="prototype-never-seen",
    )
    assert domain_result.shrink_level == "domain_prior"
    assert domain_result.resolved_identity["domain"] == "career"


def test_no_school_evidence_returns_global_prior_not_a_fabricated_winner(tmp_path: Path) -> None:
    module = _module()
    registry = module.CapabilityRegistry.from_snapshot(
        _snapshot(tmp_path, [_posterior("ziping", "career.role_change", "prototype-a", mean=0.8, interval=(0.6, 0.9), n_eff=10)])
    )

    result = _query(registry, school_id="unknown-school")

    assert result.shrink_level == "global_prior"
    assert result.posterior_mean == 0.5
    assert result.credible_interval == (0.0, 1.0)
    assert result.n_eff == 0.0


def test_snapshot_missing_required_fields_fails_loudly(tmp_path: Path) -> None:
    module = _module()
    invalid = _posterior("ziping", "career.role_change", "prototype-balanced", mean=0.8, interval=(0.6, 0.9), n_eff=10)
    del invalid["credible_interval"]

    with pytest.raises(ValueError, match="credible_interval"):
        module.CapabilityRegistry.from_snapshot(_snapshot(tmp_path, [invalid]))


def test_registry_loads_real_evaluation_score_artifact_shape() -> None:
    module = _module()

    registry = module.CapabilityRegistry.from_snapshot(Path("META/school-capability-historical-scores-2026-07-14.json"))

    assert registry.snapshot_id.startswith("cap-")
    assert registry.posterior_count > 0
