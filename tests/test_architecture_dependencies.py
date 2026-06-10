"""Clean Architecture 依赖方向守护测试。

固化 plans/clean-architecture-refactor.md § 8 验收标准：
- #7 application 层不得再出现 ``from tools.`` 或 ``import tools.``
- #8 domain 层不得导入 application、infrastructure、tools

通过 AST 静态扫描各层源码的 import 语句，避免反向依赖回潮。
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine"


def _iter_python_files(package_dir: Path) -> list[Path]:
    if not package_dir.exists():
        return []
    return sorted(package_dir.rglob("*.py"))


def _imported_modules(py_file: Path) -> set[str]:
    """返回某文件 import 的顶层模块全名集合（含 from-import 的来源模块）。"""
    source = py_file.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(py_file))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            # 仅记录绝对导入；相对导入（level>0）天然在本层内部。
            if node.level == 0 and node.module:
                modules.add(node.module)
    return modules


def _violations(package_dir: Path, forbidden_prefixes: tuple[str, ...]) -> list[str]:
    violations: list[str] = []
    for py_file in _iter_python_files(package_dir):
        for module in _imported_modules(py_file):
            for prefix in forbidden_prefixes:
                if module == prefix or module.startswith(prefix + "."):
                    rel = py_file.relative_to(ROOT).as_posix()
                    violations.append(f"{rel}: imports `{module}` (forbidden `{prefix}`)")
    return violations


def test_application_layer_does_not_import_tools() -> None:
    """验收标准 #7：application 层不得依赖 tools.*。"""
    violations = _violations(ENGINE / "application", ("tools",))
    assert not violations, "application 层出现 tools 反向依赖:\n" + "\n".join(violations)


def test_domain_layer_has_no_outward_imports() -> None:
    """验收标准 #8：domain 层不得导入 application / infrastructure / tools。"""
    violations = _violations(
        ENGINE / "domain",
        ("tools", "engine.application", "engine.infrastructure"),
    )
    assert not violations, "domain 层出现外向依赖:\n" + "\n".join(violations)


def test_default_pipeline_adapters_live_in_infrastructure() -> None:
    """默认适配器装配应落在 infrastructure 层，tools 仅保留兼容 shim。"""
    from engine.infrastructure.adapters import default_pipeline_adapters as infra_default
    from tools.pipeline_adapters import default_pipeline_adapters as tools_default

    # tools shim 必须重导出 infrastructure 实现，二者为同一对象。
    assert tools_default is infra_default


def test_pipeline_runner_loads_adapters_from_infrastructure() -> None:
    """pipeline_runner 默认适配器来源应为 infrastructure，而非 tools。"""
    runner_source = (ENGINE / "application" / "pipeline_runner.py").read_text(encoding="utf-8")
    assert "from engine.infrastructure.adapters import" in runner_source
    assert "from tools.pipeline_adapters import" not in runner_source


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
