"""v5 静态门禁（ADR-006 冻结 + ADR-007 D9）。

把「v5 已冻结、白名单只减不增」从文档约定升级为**门禁内可执行的 AST 级检查**：

1. 扫描全仓 `*.py` 的 `import engine.v5[.*]` 与 `from engine import v5`；
2. 命中集合必须 ⊆ `tests/governance/v5_frozen_importers.py` 的冻结白名单；
3. 白名单条目数不得增加（上限断言）；
4. 出现新的「无法解析」文件也报红，避免拿解析失败当免检通道。

范本：`tests/governance/static_isolation_scanner.py`、`tests/f09/test_production_isolation.py`。
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Final

from tests.governance.v5_frozen_importers import (
    FROZEN_IMPORTER_COUNT_MAX,
    FROZEN_UNPARSEABLE,
    FROZEN_V5_IMPORTERS,
)

ROOT: Final[Path] = Path(__file__).resolve().parents[2]

#: 不作为扫描对象的目录名（构建产物 / 隔离副本 / 归档）。
EXCLUDED_DIR_NAMES: Final[frozenset[str]] = frozenset(
    {
        ".git",
        ".venv",
        ".worktrees",
        "_archive",
        "__pycache__",
        "node_modules",
    }
)


def _is_excluded_dir(name: str) -> bool:
    # 点开头的是工具产物目录（.venv / .omo / .taskswarm / .agent-teams …）；
    # pytest-of-* 是 pytest tmp_path 在 rootdir 下生成的临时目录，随时会新增内容。
    return (
        name in EXCLUDED_DIR_NAMES
        or name.startswith(".")
        or name.startswith("pytest-of-")
    )


def _imports_v5(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "engine.v5" or alias.name.startswith("engine.v5."):
                    return True
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "engine.v5" or module.startswith("engine.v5."):
                return True
            if module == "engine" and any(alias.name == "v5" for alias in node.names):
                return True
    return False


def scan_v5_importers(root: Path = ROOT) -> tuple[set[str], set[str]]:
    """返回 (命中文件集合, 无法解析文件集合)，路径均为相对 root 的 posix 字符串。"""

    hits: set[str] = set()
    unparseable: set[str] = set()
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if not _is_excluded_dir(name)]
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            path = Path(dirpath) / filename
            relative = path.relative_to(root).as_posix()
            try:
                # utf-8-sig：仓库里有带 BOM 的文件，BOM 会让 ast.parse 直接抛错
                tree = ast.parse(
                    path.read_text(encoding="utf-8-sig"), filename=str(path)
                )
            except SyntaxError:
                unparseable.add(relative)
                continue
            if _imports_v5(tree):
                hits.add(relative)
    return hits, unparseable


def test_v5_importers_are_within_frozen_whitelist() -> None:
    hits, _ = scan_v5_importers()
    offenders = sorted(hits - FROZEN_V5_IMPORTERS)
    assert not offenders, (
        "检测到白名单外的 engine.v5 引用 —— ADR-006 已冻结 v5，禁止新增依赖：\n"
        + "\n".join(f"  {path}" for path in offenders)
        + "\n修法：删掉该 import，或改走 engine.v5 之外的现行架构入口；"
        "不得把新文件加进 tests/governance/v5_frozen_importers.py。"
    )


def test_v5_whitelist_does_not_grow() -> None:
    assert len(FROZEN_V5_IMPORTERS) <= FROZEN_IMPORTER_COUNT_MAX, (
        f"v5 冻结白名单只能减不能增：当前 {len(FROZEN_V5_IMPORTERS)} 条，"
        f"上限 {FROZEN_IMPORTER_COUNT_MAX} 条。"
    )


def test_whitelist_entries_still_exist_on_disk() -> None:
    missing = sorted(
        path for path in FROZEN_V5_IMPORTERS if not (ROOT / path).exists()
    )
    assert not missing, (
        "白名单里的文件已不存在（删文件是允许的，但请同步从白名单移除并下调上限）：\n"
        + "\n".join(f"  {path}" for path in missing)
    )


def test_no_new_unparseable_files_are_used_as_loophole() -> None:
    _, unparseable = scan_v5_importers()
    new_ones = sorted(unparseable - FROZEN_UNPARSEABLE)
    assert not new_ones, (
        "扫描遇到无法解析的 .py —— 它会成为 v5 门禁的免检盲区：\n"
        + "\n".join(f"  {path}" for path in new_ones)
    )


def test_scanner_actually_detects_v5_import(tmp_path: Path) -> None:
    """自检：扫描器本身必须能认出新引用，否则门禁只有形式意义。"""

    (tmp_path / "plain_import.py").write_text("import engine.v5\n", encoding="utf-8")
    (tmp_path / "from_import.py").write_text(
        "from engine.v5 import runner\n", encoding="utf-8"
    )
    (tmp_path / "package_import.py").write_text(
        "from engine import v5\n", encoding="utf-8"
    )
    (tmp_path / "aliased.py").write_text(
        "import engine.v5 as legacy\n", encoding="utf-8"
    )
    (tmp_path / "unrelated.py").write_text(
        "import engine.facts\nfrom engine import facts\nV5 = 'engine.v5'\n",
        encoding="utf-8",
    )
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "ignored.py").write_text(
        "import engine.v5\n", encoding="utf-8"
    )

    hits, unparseable = scan_v5_importers(tmp_path)

    assert hits == {
        "plain_import.py",
        "from_import.py",
        "package_import.py",
        "aliased.py",
    }
    assert unparseable == set()
