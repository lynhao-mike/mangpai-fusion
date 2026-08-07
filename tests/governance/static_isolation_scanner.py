from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

from tests.governance.static_isolation_imports import imported_modules_for_path
from tests.governance.static_isolation_metadata import active_entrypoint_paths


ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_OUTWARD_IMPORTS: Final = (
    "engine.application",
    "engine.infrastructure",
    "tools",
)
SHADOW_RUNNER_IMPORT: Final = "engine.application.governance_shadow_runner"
SHADOW_RUNNER_TOKEN: Final = "governance_shadow_runner"
FACT_SNAPSHOT_WRITERS: Final = (
    "FactSnapshot",
    "build_fact_snapshot",
    "build_governance_fact_snapshot",
)
SYSTEM_TIME_CALLS: Final = (
    "date.today",
    "datetime.now",
    "time.time",
)
FACT_SNAPSHOT_IMPORT_PARENTS: Final = (
    "engine.governance",
    "engine.governance.contracts",
)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def python_files(package_dir: Path) -> tuple[Path, ...]:
    if not package_dir.exists():
        return ()
    return tuple(sorted(package_dir.rglob("*.py")))


def imported_modules(path: Path) -> tuple[str, ...]:
    return imported_modules_for_path(path, ROOT)


def _matches_prefix(module: str, prefixes: tuple[str, ...]) -> bool:
    return any(
        module == prefix or module.startswith(f"{prefix}.") for prefix in prefixes
    )


def forbidden_import_issues(
    paths: tuple[Path, ...], forbidden_prefixes: tuple[str, ...]
) -> tuple[str, ...]:
    issues: list[str] = []
    for path in paths:
        modules = imported_modules(path)
        for module in modules:
            if any(
                module.startswith(f"{other}.") for other in modules if other != module
            ):
                continue
            if _matches_prefix(module, forbidden_prefixes):
                issues.append(f"{display_path(path)} imports {module}")
    return tuple(issues)


def legacy_shadow_consumer_paths() -> tuple[Path, ...]:
    fixed = (
        ROOT / "engine" / "pipeline.py",
        ROOT / "engine" / "application" / "pipeline_runner.py",
        ROOT / "engine" / "claims" / "runner_registry.py",
        ROOT / "engine" / "decision" / "orchestrator.py",
        ROOT / "tools" / "feedback_ingest.py",
        ROOT / "tools" / "feedback_loop.py",
        ROOT / "tools" / "render_report.py",
        *active_entrypoint_paths(ROOT),
    )
    templates = tuple(
        sorted(
            path
            for path in (ROOT / "templates").rglob("*")
            if path.is_file()
            and path.suffix.lower() in {".json", ".md", ".yaml", ".yml"}
        )
    )
    return tuple(dict.fromkeys(path for path in (*fixed, *templates) if path.exists()))


def shadow_runner_consumer_issues(paths: tuple[Path, ...]) -> tuple[str, ...]:
    issues: list[str] = []
    for path in paths:
        if path.suffix == ".py":
            import_issues = tuple(
                f"{display_path(path)} imports {module}"
                for module in imported_modules(path)
                if module == SHADOW_RUNNER_IMPORT
            )
            if import_issues:
                issues.extend(import_issues)
                continue
        if SHADOW_RUNNER_TOKEN in path.read_text(encoding="utf-8"):
            issues.append(f"{display_path(path)} contains {SHADOW_RUNNER_TOKEN}")
    return tuple(issues)


def call_leaf_names(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    aliases = _fact_snapshot_aliases(tree)
    return tuple(
        _canonical_call_leaf(ast.unparse(node.func), aliases)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    )


def _fact_snapshot_aliases(tree: ast.AST) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        parent = node.module or ""
        if parent not in FACT_SNAPSHOT_IMPORT_PARENTS:
            continue
        for imported in node.names:
            if imported.name in FACT_SNAPSHOT_WRITERS:
                aliases[imported.asname or imported.name] = imported.name
    return aliases


def _canonical_call_leaf(call: str, aliases: dict[str, str]) -> str:
    leaf = call.split(".")[-1]
    if call in aliases:
        return aliases[call]
    return aliases.get(leaf, leaf)


def fact_snapshot_write_issues(paths: tuple[Path, ...]) -> tuple[str, ...]:
    return tuple(
        f"{display_path(path)} calls {name}"
        for path in paths
        for name in call_leaf_names(path)
        if name in FACT_SNAPSHOT_WRITERS
    )


def school_view_adapter_paths(root: Path = ROOT) -> tuple[Path, ...]:
    application = root / "engine" / "application"
    candidates = {
        *application.glob("governance_*adapter*.py"),
        *application.glob("governance_*school*view*.py"),
    }
    return tuple(sorted(path for path in candidates if path.exists()))


def new_governance_python_paths() -> tuple[Path, ...]:
    application = ROOT / "engine" / "application"
    return (
        *python_files(ROOT / "engine" / "governance"),
        *tuple(sorted(application.glob("governance_*.py"))),
    )


def system_time_liunian_issues(paths: tuple[Path, ...]) -> tuple[str, ...]:
    issues: list[str] = []
    for path in paths:
        source = path.read_text(encoding="utf-8")
        if "liunian" not in f"{path.name}\n{source}".lower():
            continue
        tree = ast.parse(source)
        forbidden_calls = _system_time_call_names(tree)
        calls = tuple(
            ast.unparse(node.func)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
        )
        if any(_is_system_time_call(call, forbidden_calls) for call in calls):
            issues.append(
                f"{display_path(path)} reads system time while mentioning liunian"
            )
    return tuple(issues)


def _system_time_call_names(tree: ast.AST) -> frozenset[str]:
    names = set(SYSTEM_TIME_CALLS)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        parent = node.module or ""
        for imported in node.names:
            binding = imported.asname or imported.name
            if parent == "datetime" and imported.name == "datetime":
                names.add(f"{binding}.now")
            if parent == "datetime" and imported.name == "date":
                names.add(f"{binding}.today")
            if parent == "time" and imported.name == "time":
                names.add(binding)
    return frozenset(names)


def _is_system_time_call(call: str, forbidden_calls: frozenset[str]) -> bool:
    return any(call == name or call.endswith(f".{name}") for name in forbidden_calls)
