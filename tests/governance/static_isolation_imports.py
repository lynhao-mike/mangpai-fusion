from __future__ import annotations

import ast
from pathlib import Path


class ImportCollector(ast.NodeVisitor):
    def __init__(self, path: Path, root: Path) -> None:
        self.path = path
        self.root = root
        self.modules: set[str] = set()
        self.importlib_bindings: set[str] = {"importlib"}
        self.import_module_bindings: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.modules.add(alias.name)
            if alias.name == "importlib":
                self.importlib_bindings.add(alias.asname or alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        parent = _resolved_import_parent(self.path, self.root, node)
        if parent:
            self.modules.add(parent)
        for alias in node.names:
            if alias.name == "*":
                continue
            self.modules.add(f"{parent}.{alias.name}" if parent else alias.name)
            if parent == "importlib" and alias.name == "import_module":
                self.import_module_bindings.add(alias.asname or alias.name)


def imported_modules_for_path(path: Path, root: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    collector = ImportCollector(path, root)
    collector.visit(tree)
    modules = set(collector.modules)
    for node in ast.walk(tree):
        if _is_literal_import_call(node, collector):
            modules.add(node.args[0].value)
    return tuple(sorted(modules))


def _is_literal_import_call(node: ast.AST, collector: ImportCollector) -> bool:
    if not (
        isinstance(node, ast.Call)
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
    ):
        return False
    if isinstance(node.func, ast.Name):
        return node.func.id in collector.import_module_bindings | {"__import__"}
    return (
        isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in collector.importlib_bindings
        and node.func.attr == "import_module"
    )


def _resolved_import_parent(path: Path, root: Path, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""
    package_parts = _package_parts(path, root)
    keep_count = max(len(package_parts) - node.level + 1, 0)
    base = package_parts[:keep_count]
    if node.module:
        return ".".join((*base, node.module))
    return ".".join(base)


def _package_parts(path: Path, root: Path) -> tuple[str, ...]:
    module_parts = _module_parts(path, root)
    if path.name == "__init__.py":
        return module_parts
    return module_parts[:-1]


def _module_parts(path: Path, root: Path) -> tuple[str, ...]:
    try:
        relative = path.resolve().relative_to(root)
        parts = relative.with_suffix("").parts
    except ValueError:
        parts = path.with_suffix("").parts
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    for anchor in ("engine", "tools", "tests"):
        if anchor in parts:
            return tuple(parts[parts.index(anchor) :])
    return (path.stem,)
