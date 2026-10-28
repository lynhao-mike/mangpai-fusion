from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

from engine.application.pipeline_runner import run_pipeline
from engine.claims.runner_registry import DEFAULT_RUNNER_REGISTRY
from engine.infrastructure.weight_repository import _DEFAULT_SCHOOL_WEIGHTS


HISTORICAL_SHA256 = {
    "META/six-month-platform-gate-2026-07-15.md": "d9ad97537b3ea360071b3b9a190d7e54a17bcaffe3e3ca107027ea2fba6fcd5d",
    "META/six-month-platform-gate-2026-07-15.json": "7a519b7c1197411ad23f91532fe4d9e79da57eea3f2bdd1a6d929325adf013c8",
}
PIPELINE_SIGNATURE = (
    "(parsed: 'ParsedInput', *, cases_dir: 'Optional[Union[str, Path]]' = None, "
    "write_findings: 'bool' = True, timing: 'Optional[PipelineTiming]' = None, "
    "threshold_seconds: 'float' = 60.0) -> 'AnalysisOutput'"
)
DEFAULT_REGISTRY_SHA256 = "88779529d0d470d80558b2005a79089950adfc4deaf3d96e7b7d20bd78c0b16d"
PRODUCTION_WEIGHT_FILE_SHA256 = "d8c8a90df1fe625a952ecc67ee6925812e28dbfe7200f4dbfc9f091d2e0fabae"
DEFAULT_WEIGHT_SUMMARY = {"blind": 0.26, "tiaohou_ditiansui": 0.32, "ziping": 0.42}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_historical_gate_baseline_bytes_are_immutable() -> None:
    assert {path: _sha256(Path(path)) for path in HISTORICAL_SHA256} == HISTORICAL_SHA256


def test_run_pipeline_signature_and_defaults_are_unchanged() -> None:
    assert str(inspect.signature(run_pipeline)) == PIPELINE_SIGNATURE


def test_default_runner_registry_registrations_are_unchanged() -> None:
    registrations = sorted(
        (school, task, generator.__module__ + "." + generator.__name__)
        for (school, task), generator in DEFAULT_RUNNER_REGISTRY._runners.items()
    )
    digest = hashlib.sha256(
        json.dumps(registrations, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert digest == DEFAULT_REGISTRY_SHA256


def test_production_weight_defaults_and_file_are_unchanged() -> None:
    assert _DEFAULT_SCHOOL_WEIGHTS == DEFAULT_WEIGHT_SUMMARY
    assert _sha256(Path("engine/expert-weights.yaml")) == PRODUCTION_WEIGHT_FILE_SHA256


def test_ren_staged_slice_does_not_modify_production_claim_rules() -> None:
    # T-156（2026-10-28）：A 类 counter_conditions 删除；审计见 META/counter-condition-audit-v1.md
    assert _sha256(Path("theory/production/claim-rules-v1.yaml")) == (
        "14d34deaaf37decaef4be2df76318c9d39202dc645f91f927cefab398f3e6467"
    )
