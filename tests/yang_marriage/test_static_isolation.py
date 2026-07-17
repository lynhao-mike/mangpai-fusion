from __future__ import annotations

import ast
import hashlib
import inspect
import subprocess
from dataclasses import fields
from pathlib import Path

from engine.claims.domain import Claim
from engine.decision.models import SchoolClaim
from engine.evaluation.models import BlindSchoolOutput
import engine.decision.yang_marriage as discriminator
import engine.decision.yang_marriage_slice as slice_module


PUBLIC_FIELDS = {
    Claim: (
        "claim_id",
        "school_id",
        "task_id",
        "claim_type",
        "stance",
        "statement",
        "evidence",
        "falsifier",
        "time_window",
        "confidence_basis",
        "applicability_snapshot",
        "domain",
        "polarity",
        "magnitude",
        "confidence",
        "high_risk",
        "target_id",
    ),
    SchoolClaim: (
        "claim_id",
        "school",
        "role_granted_by_l1",
        "domain",
        "claim_type",
        "statement",
        "evidence_refs",
        "confidence",
        "falsifier",
        "dependencies",
        "metadata",
    ),
    BlindSchoolOutput: (
        "case_id",
        "school_id",
        "task_id",
        "state",
        "rationale",
        "predictions",
        "counter_evidence",
    ),
}


def _source_paths() -> tuple[Path, Path]:
    return Path(discriminator.__file__), Path(slice_module.__file__)


def test_public_contract_fields_and_production_rule_bytes_are_unchanged() -> None:
    for model, expected in PUBLIC_FIELDS.items():
        assert tuple(item.name for item in fields(model)) == expected

    path = "theory/production/claim-rules-v1.yaml"
    baseline_ref = subprocess.check_output(
        ["git", "merge-base", "HEAD", "main"], text=True
    ).strip()
    baseline = subprocess.check_output(["git", "show", f"{baseline_ref}:{path}"])
    current_blob = subprocess.check_output(
        ["git", "hash-object", "--path", path, path], text=True
    ).strip()
    current = subprocess.check_output(["git", "cat-file", "blob", current_blob])
    assert hashlib.sha256(current).digest() == hashlib.sha256(baseline).digest()
    assert current == baseline


def test_slice_has_no_history_report_learning_or_count_threshold_dependency() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in _source_paths())
    forbidden = (
        "cases/",
        "reports/",
        "feedback.md",
        "META/prospective-go",
        "r6_ziping_career_baseline",
        "render_report",
        "ReportViewItem",
        "independent_signal_count",
    )
    assert not {token for token in forbidden if token in text}
    assert ">= 2" not in inspect.getsource(discriminator.discriminate_yang_marriage)


def test_slice_imports_do_not_reach_l7_l9_or_production_runner() -> None:
    imported: set[str] = set()
    for path in _source_paths():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported |= {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        }
    forbidden_prefixes = (
        "engine.decision.l7",
        "engine.decision.l8",
        "engine.decision.l9",
        "engine.application",
        "engine.v5.yang_runner",
        "tools",
    )
    assert not {name for name in imported if name.startswith(forbidden_prefixes)}


def test_synthetic_gates_do_not_consume_historical_or_revealed_paths() -> None:
    test_root = Path("tests/yang_marriage")
    paths = (
        test_root / "fixtures.py",
        test_root / "test_synthetic_matrix.py",
        test_root / "test_slice_layers.py",
    )
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    forbidden = (
        "cases/",
        "reports/",
        "feedback.md",
        "META/prospective-go",
        "r6_ziping_career_baseline",
    )
    assert not {token for token in forbidden if token in text}


def test_default_pipeline_registry_l7_report_and_templates_do_not_import_slice() -> None:
    paths = (
        Path("engine/application/pipeline_runner.py"),
        Path("engine/claims/runner_registry.py"),
        Path("engine/decision/l7_report_view.py"),
        Path("tools/render_report.py"),
        *sorted(
            path
            for path in Path("templates").rglob("*")
            if path.is_file() and path.suffix.lower() in {".md", ".json", ".yaml", ".yml"}
        ),
    )
    offenders = [
        str(path)
        for path in paths
        if "yang_marriage_slice" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []
