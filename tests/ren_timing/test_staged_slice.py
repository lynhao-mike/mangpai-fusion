from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

from engine.application.pipeline_runner import run_pipeline
from engine.claims.runner_registry import DEFAULT_RUNNER_REGISTRY


def _sha256(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_ren_staged_work_starts_from_unchanged_production_boundaries() -> None:
    registrations = sorted(
        (school, task, fn.__module__ + "." + fn.__name__)
        for (school, task), fn in DEFAULT_RUNNER_REGISTRY._runners.items()
    )
    assert hashlib.sha256(json.dumps(registrations, separators=(",", ":")).encode()).hexdigest() == (
        "88779529d0d470d80558b2005a79089950adfc4deaf3d96e7b7d20bd78c0b16d"
    )
    assert "ren_career_timing" not in str(inspect.signature(run_pipeline))
    assert _sha256("theory/production/claim-rules-v1.yaml") == (
        "6396883d8db0b8d24c6c15435c130c6f9ae045c8c6d1fe8d2a84748c5b0bebef"
    )
