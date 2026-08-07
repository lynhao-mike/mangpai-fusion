from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path


_PRODUCTION_ENTRYPOINTS = (
    Path("engine/application/pipeline_runner.py"),
    Path("engine/claims/runner_registry.py"),
    Path("engine/infrastructure/weight_repository.py"),
)


def _imports_f09(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == "engine.f09" or alias.name.startswith("engine.f09.") for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom):
            if node.module == "engine.f09" or (node.module or "").startswith("engine.f09."):
                return True
    return False


def test_default_production_entrypoints_do_not_import_f09():
    assert not any(_imports_f09(path) for path in _PRODUCTION_ENTRYPOINTS)


def test_clean_default_production_entrypoint_imports_do_not_load_f09():
    for module_name in (
        "engine.application.pipeline_runner",
        "engine.claims.runner_registry",
        "engine.infrastructure.weight_repository",
    ):
        program = (
            f"import {module_name}; import sys; "
            "assert not any(name == 'engine.f09' or name.startswith('engine.f09.') "
            "for name in sys.modules)"
        )
        completed = subprocess.run(
            [sys.executable, "-c", program],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr


def test_importing_f09_opt_in_surface_does_not_load_default_production_modules():
    before = set(sys.modules)
    import engine.f09.application  # noqa: F401

    loaded = set(sys.modules) - before
    assert not {
        "engine.application.pipeline_runner",
        "engine.claims.runner_registry",
        "engine.infrastructure.weight_repository",
    }.intersection(loaded)


def test_versioned_application_owner_boundary_has_no_forbidden_calls():
    path = Path("engine/f09/application.py")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    definition = next(
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "run_f09_slice_with_execution_authority_v1"
    )
    called_names = {
        node.func.id
        for node in ast.walk(definition)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert called_names.isdisjoint({
        "validate_run_artifact_manifest_v1",
        "validate_run_artifact_set_result_issuance_v1",
        "_preprod_authority_self_excluded_material",
        "bind_feedback_operation",
        "evaluate_learning_eligibility",
        "validate_learning_eligibility",
    })
    assert called_names & {
        "coordinate_run_artifact_set_with_target_refs_v1",
        "construct_preprod_run_authority_v1",
    } == {
        "coordinate_run_artifact_set_with_target_refs_v1",
        "construct_preprod_run_authority_v1",
    }
