from __future__ import annotations

from pathlib import Path

import pytest

from tests.governance.static_isolation_scanner import imported_modules

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine"


def _iter_python_files(package_dir: Path) -> list[Path]:
    if not package_dir.exists():
        return []
    return sorted(package_dir.rglob("*.py"))


def _imported_modules(py_file: Path) -> set[str]:
    return set(imported_modules(py_file))


def _display_violation_path(py_file: Path) -> str:
    try:
        return py_file.relative_to(ROOT).as_posix()
    except ValueError:
        return py_file.name


def _violations(package_dir: Path, forbidden_prefixes: tuple[str, ...]) -> list[str]:
    violations: list[str] = []
    for py_file in _iter_python_files(package_dir):
        modules = _imported_modules(py_file)
        for module in modules:
            if any(module.startswith(f"{other}.") for other in modules):
                continue
            for prefix in forbidden_prefixes:
                if module == prefix or module.startswith(prefix + "."):
                    rel = _display_violation_path(py_file)
                    violations.append(
                        f"{rel}: imports `{module}` (forbidden `{prefix}`)"
                    )
    return violations


def test_application_layer_does_not_import_tools() -> None:
    violations = _violations(ENGINE / "application", ("tools",))
    assert not violations, "application imports tools:\n" + "\n".join(violations)


def test_domain_layer_has_no_outward_imports() -> None:
    violations = _violations(
        ENGINE / "domain",
        ("tools", "engine.application", "engine.infrastructure"),
    )
    assert not violations, "domain has outward imports:\n" + "\n".join(violations)


def test_governance_layer_has_no_outward_imports() -> None:
    violations = _violations(
        ENGINE / "governance",
        ("tools", "engine.application", "engine.infrastructure"),
    )
    assert not violations, "governance has outward imports:\n" + "\n".join(violations)


def test_fixture_detects_relative_governance_outward_imports(tmp_path: Path) -> None:
    package = tmp_path / "engine" / "governance"
    package.mkdir(parents=True)
    source = package / "bad_relative.py"
    source.write_text(
        "from ..application import governance_shadow_runner\n",
        encoding="utf-8",
    )

    violations = _violations(
        package,
        ("tools", "engine.application", "engine.infrastructure"),
    )

    assert violations == [
        "bad_relative.py: imports `engine.application` "
        "(forbidden `engine.application`)"
    ]


def test_default_pipeline_adapters_live_in_infrastructure() -> None:
    from engine.infrastructure.adapters import (
        default_pipeline_adapters as infra_default,
    )
    from tools.pipeline_adapters import default_pipeline_adapters as tools_default

    assert tools_default is infra_default


def test_pipeline_runner_loads_adapters_from_infrastructure() -> None:
    runner_source = (ENGINE / "application" / "pipeline_runner.py").read_text(
        encoding="utf-8"
    )
    assert "from engine.infrastructure.adapters import" in runner_source
    assert "from tools.pipeline_adapters import" not in runner_source


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
