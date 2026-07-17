from __future__ import annotations

import ast
import hashlib
import inspect
import os
import subprocess
from dataclasses import fields
from pathlib import Path

from engine.claims.domain import Claim
from engine.decision.models import SchoolClaim
from engine.evaluation.models import BlindSchoolOutput
import engine.decision.yang_marriage as discriminator
import engine.decision.yang_marriage_slice as slice_module


APPROVED_BASELINE = "15ac7f3cdba01167b10f7ecc1139ef1e11782c8a"
APPROVED_BLOB_SHA256 = "79fb99e4a38c7c86fe20cea3bca27a857403a0b0c16d50949064555b04eac8ba"
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


def _assert_approved_worktree_bytes(
    approved_blob: bytes, worktree_bytes: bytes, *, expected_eol: str
) -> None:
    assert b"\r" not in approved_blob, "approved repository blob must use LF only"
    assert expected_eol in {"lf", "crlf"}
    expected = (
        approved_blob
        if expected_eol == "lf"
        else approved_blob.replace(b"\n", b"\r\n")
    )
    assert hashlib.sha256(worktree_bytes).digest() == hashlib.sha256(expected).digest()
    assert worktree_bytes == expected


def _audit_checkout_attributes(attributes: dict[str, str]) -> None:
    assert set(attributes) == {"filter", "working-tree-encoding", "eol", "text"}
    assert attributes["filter"] in {"unspecified", "unset"}
    assert attributes["working-tree-encoding"] in {"unspecified", "unset"}
    assert attributes["eol"] in {"unspecified", "unset", "lf", "crlf"}
    assert attributes["text"] in {"unspecified", "unset", "set", "auto"}


def _expected_checkout_eol(
    attributes: dict[str, str], *, autocrlf: str, core_eol: str
) -> str:
    if attributes["eol"] in {"lf", "crlf"}:
        return attributes["eol"]
    if attributes["text"] == "unset" or autocrlf in {"false", "input"}:
        return "lf"
    if autocrlf == "true":
        return "crlf"
    if core_eol in {"lf", "crlf"}:
        return core_eol
    return "crlf" if os.linesep == "\r\n" else "lf"


def _target_checkout_attributes(path: str) -> dict[str, str]:
    names = ("filter", "working-tree-encoding", "eol", "text")
    output = subprocess.check_output(
        ["git", "check-attr", *names, "--", path], text=True
    )
    attributes: dict[str, str] = {}
    for line in output.splitlines():
        _, name, value = line.rsplit(": ", 2)
        attributes[name] = value
    return attributes


def _git_config(name: str, *, default: str) -> str:
    result = subprocess.run(
        ["git", "config", "--get", name],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode in {0, 1}
    return result.stdout.strip().lower() if result.returncode == 0 else default


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


def test_approved_worktree_bytes_accept_only_exact_lf_or_pure_crlf() -> None:
    approved = b"first: value\nsecond: value\n"

    _assert_approved_worktree_bytes(approved, approved, expected_eol="lf")
    _assert_approved_worktree_bytes(
        approved, b"first: value\r\nsecond: value\r\n", expected_eol="crlf"
    )


def test_approved_worktree_bytes_reject_filter_content_and_newline_mutations() -> None:
    approved = b"first: value\nsecond: value\n"
    mutations = (
        b"first: value\nsecond: value\nfiltered: true\n",
        b"first: value\r\nsecond: changed\r\n",
        b"first: value\r\nsecond: value\n",
    )

    for mutation in mutations:
        try:
            _assert_approved_worktree_bytes(approved, mutation, expected_eol="crlf")
        except AssertionError:
            pass
        else:
            raise AssertionError(f"mutation unexpectedly accepted: {mutation!r}")


def test_checkout_attribute_audit_rejects_dangerous_filter_and_encoding() -> None:
    safe = {
        "filter": "unspecified",
        "working-tree-encoding": "unspecified",
        "eol": "unspecified",
        "text": "unspecified",
    }
    _audit_checkout_attributes(safe)
    _audit_checkout_attributes({**safe, "filter": "unset"})
    _audit_checkout_attributes({**safe, "working-tree-encoding": "unset"})

    for dangerous in (
        {**safe, "filter": "rewrite-yaml"},
        {**safe, "filter": "set"},
        {**safe, "working-tree-encoding": "UTF-16LE"},
        {**safe, "working-tree-encoding": "set"},
    ):
        try:
            _audit_checkout_attributes(dangerous)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"dangerous attributes unexpectedly accepted: {dangerous!r}")


def test_public_contract_fields_and_production_rule_bytes_are_unchanged() -> None:
    for model, expected in PUBLIC_FIELDS.items():
        assert tuple(item.name for item in fields(model)) == expected

    subprocess.run(
        ["git", "cat-file", "-e", f"{APPROVED_BASELINE}^{{commit}}"], check=True
    )
    path = PRODUCTION_RULE_PATH.as_posix()
    baseline_blob = subprocess.check_output(["git", "show", f"{APPROVED_BASELINE}:{path}"])
    head_blob = subprocess.check_output(["git", "show", f"HEAD:{path}"])
    assert hashlib.sha256(baseline_blob).hexdigest() == APPROVED_BLOB_SHA256
    assert hashlib.sha256(head_blob).hexdigest() == APPROVED_BLOB_SHA256
    assert head_blob == baseline_blob

    attributes = _target_checkout_attributes(path)
    _audit_checkout_attributes(attributes)
    expected_eol = _expected_checkout_eol(
        attributes,
        autocrlf=_git_config("core.autocrlf", default="false"),
        core_eol=_git_config("core.eol", default="native"),
    )
    _assert_approved_worktree_bytes(
        baseline_blob, PRODUCTION_RULE_PATH.read_bytes(), expected_eol=expected_eol
    )


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
