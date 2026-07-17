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


APPROVED_BASELINE = "15ac7f3cdba01167b10f7ecc1139ef1e11782c8a"
PRODUCTION_RULE_PATH = Path("theory/production/claim-rules-v1.yaml")


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


def _imported_modules(source: str) -> set[str]:
    imported: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            parent = node.module or ""
            imported.add(parent)
            imported.update(
                f"{parent}.{alias.name}" if parent else alias.name
                for alias in node.names
                if alias.name != "*"
            )
        elif (
            isinstance(node, ast.Call)
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
            and (
                isinstance(node.func, ast.Name)
                and node.func.id == "__import__"
                or isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "importlib"
                and node.func.attr == "import_module"
            )
        ):
            imported.add(node.args[0].value)
    return imported


def test_import_scanner_recognizes_static_and_dynamic_import_forms() -> None:
    mutations = {
        "import engine.decision.l7_report_view": "engine.decision.l7_report_view",
        "import engine.decision.l7_report_view as report_view": "engine.decision.l7_report_view",
        "from engine.decision import l7_report_view": "engine.decision.l7_report_view",
        "from engine.decision import l7_report_view as report_view": "engine.decision.l7_report_view",
        'importlib.import_module("engine.decision.l7_report_view")': "engine.decision.l7_report_view",
        '__import__("engine.decision.l7_report_view")': "engine.decision.l7_report_view",
    }
    for source, expected in mutations.items():
        assert expected in _imported_modules(source), source


def test_public_contract_fields_and_production_rule_bytes_are_unchanged() -> None:
    for model, expected in PUBLIC_FIELDS.items():
        assert tuple(item.name for item in fields(model)) == expected

    subprocess.run(
        ["git", "cat-file", "-e", f"{APPROVED_BASELINE}^{{commit}}"], check=True
    )
    path = PRODUCTION_RULE_PATH.as_posix()
    baseline_blob = subprocess.check_output(["git", "show", f"{APPROVED_BASELINE}:{path}"])
    head_blob = subprocess.check_output(["git", "show", f"HEAD:{path}"])
    assert hashlib.sha256(head_blob).digest() == hashlib.sha256(baseline_blob).digest()
    assert head_blob == baseline_blob

    # `core.autocrlf` may make checkout bytes CRLF while the repository blob is LF.
    # Apply checkout filters to the approved blob, then compare the actual raw bytes;
    # never clean/hash the worktree bytes with `hash-object --path`.
    expected_worktree = subprocess.check_output(
        ["git", "cat-file", "--filters", f"--path={path}", f"{APPROVED_BASELINE}:{path}"]
    )
    current_worktree = PRODUCTION_RULE_PATH.read_bytes()
    assert hashlib.sha256(current_worktree).digest() == hashlib.sha256(expected_worktree).digest()
    assert current_worktree == expected_worktree


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
        imported |= _imported_modules(path.read_text(encoding="utf-8"))
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
