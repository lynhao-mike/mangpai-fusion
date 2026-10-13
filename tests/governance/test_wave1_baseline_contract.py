from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

from engine.claims.domain import Claim
from engine.decision.models import SchoolClaim
from engine.predicates.ten_god_structure_types import TenGodStructureKind


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_MODULE = "engine.governance"
LEGACY_ENTRYPOINTS = (
    Path("engine/decision/orchestrator.py"),
    Path("tools/render_report.py"),
    Path("tools/feedback_ingest.py"),
    Path("tools/feedback_loop.py"),
)
PRODUCTION_LOADER = Path("engine/application/production_rule_loader.py")


class _ImportCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.modules: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        self.modules.update(alias.name for alias in node.names)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        parent = node.module or ""
        self.modules.add(parent)
        self.modules.update(
            f"{parent}.{alias.name}" if parent else alias.name
            for alias in node.names
            if alias.name != "*"
        )


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    collector = _ImportCollector()
    collector.visit(tree)
    return collector.modules


def _governance_imports(path: Path) -> tuple[str, ...]:
    return tuple(
        sorted(
            module
            for module in _imported_modules(path)
            if module == GOVERNANCE_MODULE
            or module.startswith(f"{GOVERNANCE_MODULE}.")
        )
    )


def test_school_claim_fields_are_frozen_for_wave1_compatibility() -> None:
    assert tuple(item.name for item in fields(SchoolClaim)) == (
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
    )


def test_claim_fields_are_frozen_for_wave1_compatibility() -> None:
    assert tuple(item.name for item in fields(Claim)) == (
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
    )


def test_ten_god_structure_kind_remains_the_existing_three_values() -> None:
    assert tuple((member.name, member.value) for member in TenGodStructureKind) == (
        ("FOOD_GOD_CONTROLS_KILLING", "\u98df\u795e\u5236\u6740"),
        ("HURTING_OFFICER_CONTROLS_KILLING", "\u4f24\u5b98\u9a7e\u6740"),
        ("KILLING_GENERATES_SEAL", "\u6740\u5370\u76f8\u751f"),
    )


def test_default_production_library_remains_legacy_owned_and_exact() -> None:
    loader_path = ROOT / PRODUCTION_LOADER
    assert _governance_imports(loader_path) == ()

    from engine.application.production_rule_loader import (
        load_default_production_library,
    )

    library = load_default_production_library()
    assert set(library.rule_sets) == {"ziping", "tiaohou_ditiansui"}
    assert len(library.rule_sets["ziping"].rules) == 933
    assert len(library.rule_sets["tiaohou_ditiansui"].rules) == 1108
    assert len(library.rules) == 2041


def test_legacy_orchestrator_report_and_feedback_do_not_import_governance() -> None:
    offenders = {
        path.as_posix(): imports
        for path in LEGACY_ENTRYPOINTS
        if (imports := _governance_imports(ROOT / path))
    }
    assert offenders == {}
