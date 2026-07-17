from __future__ import annotations

import ast
import hashlib
import inspect
import json
from pathlib import Path

from engine.application.pipeline_runner import run_pipeline
from engine.claims.runner_registry import DEFAULT_RUNNER_REGISTRY
from engine.decision.models import SchoolClaim, StructuralVerdict

PIPELINE_SIGNATURE = (
    "(parsed: 'ParsedInput', *, cases_dir: 'Optional[Union[str, Path]]' = None, "
    "write_findings: 'bool' = True, timing: 'Optional[PipelineTiming]' = None, "
    "threshold_seconds: 'float' = 60.0) -> 'AnalysisOutput'"
)
DEFAULT_REGISTRY_SHA256 = "88779529d0d470d80558b2005a79089950adfc4deaf3d96e7b7d20bd78c0b16d"
PRODUCTION_CLAIM_RULES_SHA256 = "6396883d8db0b8d24c6c15435c130c6f9ae045c8c6d1fe8d2a84748c5b0bebef"


def _sha256(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_default_registry_pipeline_and_production_claim_rules_are_unchanged() -> None:
    registrations = sorted(
        (school, task, generator.__module__ + "." + generator.__name__)
        for (school, task), generator in DEFAULT_RUNNER_REGISTRY._runners.items()
    )
    digest = hashlib.sha256(json.dumps(registrations, separators=(",", ":")).encode()).hexdigest()
    assert digest == DEFAULT_REGISTRY_SHA256
    assert str(inspect.signature(run_pipeline)) == PIPELINE_SIGNATURE
    assert _sha256("theory/production/claim-rules-v1.yaml") == PRODUCTION_CLAIM_RULES_SHA256


def test_public_schema_has_not_been_extended_for_slice() -> None:
    assert tuple(SchoolClaim.__dataclass_fields__) == (
        "claim_id", "school", "role_granted_by_l1", "domain", "claim_type",
        "statement", "evidence_refs", "confidence", "falsifier", "dependencies", "metadata",
    )
    assert tuple(StructuralVerdict.__dataclass_fields__) == (
        "verdict_id", "claim_id", "verdict", "structural_reason",
        "blocking_factors", "required_support", "confidence",
    )


def test_staged_modules_do_not_import_default_registry_pipeline_reports_or_timing() -> None:
    forbidden = ("runner_registry", "pipeline_runner", "render_report", "l5_timing", "ren_career_timing")
    for relative in (
        "engine/decision/ziping_career_rules.py",
        "engine/decision/ziping_career_structure.py",
        "engine/decision/ziping_career_structure_slice.py",
    ):
        tree = ast.parse(Path(relative).read_text(encoding="utf-8"))
        imported = [
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        ]
        assert not any(token in module for token in forbidden for module in imported), relative
