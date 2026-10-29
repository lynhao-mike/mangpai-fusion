"""tools/kill_list_dependency_audit.py · T-171 Kill List 依赖审计（只读）。

从 6 个硬入口（engine/facts、engine/api、engine/cli、tools/engine_audit、
tools/relations_audit、tools/query_theory）递归建 import 图，再对
`docs/reviews/external-audit-adjudication-v2.md` §3 的 Kill List 逐条目裁决四类：

- 安全归档：Kill List 外无任何 import / 字符串引用；
- 有引用（需先改）：仍有 Kill List 外代码 import（含硬入口闭包）；
- 尺子在用：pyproject testpaths / ADR-004 基线命令（尺子）import 或按路径断言；
- 不可判：只有动态 import / 字符串引用 / 只列不删的文档目录。

本工具只读：不移动、不删除、不改任何源码；唯一写入是 `--json-out` / `--md-out`
指定的 META 产物（默认 META/kill-list-dependency-audit-v1.{json,md}）。

用法：
    python -m tools.kill_list_dependency_audit             # 写 META 产物（含运行期探针）
    python -m tools.kill_list_dependency_audit --no-probes # 只做静态图（快）
    python -m tools.kill_list_dependency_audit --check     # 不写文件，只看计数
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import tomllib
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Iterable, Sequence

ROOT: Final[Path] = Path(__file__).resolve().parents[1]
SCHEMA: Final[str] = "kill-list-dependency-audit/v1"
TASK: Final[str] = "T-171"
DEFAULT_JSON: Final[Path] = ROOT / "META" / "kill-list-dependency-audit-v1.json"
DEFAULT_MD: Final[Path] = ROOT / "META" / "kill-list-dependency-audit-v1.md"

CLASS_SAFE: Final[str] = "安全归档"
CLASS_REFERENCED: Final[str] = "有引用（需先改）"
CLASS_RULER: Final[str] = "尺子在用"
CLASS_UNKNOWN: Final[str] = "不可判"
CLASSES: Final[tuple[str, ...]] = (CLASS_SAFE, CLASS_REFERENCED, CLASS_RULER, CLASS_UNKNOWN)

#: 硬入口 id -> (相对路径, 说明)。路径必须是仓库内真实存在的文件。
ENTRYPOINTS: Final[tuple[tuple[str, str, str], ...]] = (
    ("facts", "engine/facts/__init__.py", "engine.facts 包根"),
    ("api", "engine/api/__init__.py", "engine.api 包根"),
    ("cli", "engine/cli.py", "python -m engine.cli"),
    ("engine_audit", "tools/engine_audit.py", "python -m tools.engine_audit"),
    ("relations_audit", "tools/relations_audit.py", "python -m tools.relations_audit"),
    ("query_theory", "tools/query_theory.py", "python -m tools.query_theory"),
)

#: 运行期探针：三条真正跑 481/0 基线的路径（与 tools/verify_baseline.py 同一判据来源）。
#: query_theory 不做运行期探针——它会写 theory/_light_index.json（缓存），
#: 违反本卡「只读」约束；它的静态闭包只有 tools.theory_content 一个内部依赖。
PROBES: Final[tuple[dict[str, Any], ...]] = (
    {
        "id": "cli",
        "module": "engine.cli",
        "argv": ["all", "--pillars", "庚申 戊寅 壬子 辛丑", "--gender", "乾", "--json"],
        "covers_481": True,
        "parse": None,
    },
    {
        "id": "engine_audit",
        "module": "tools.engine_audit",
        "argv": [],
        "covers_481": True,
        "parse": "engine_audit",
    },
    {
        "id": "relations_audit",
        "module": "tools.relations_audit",
        "argv": [],
        "covers_481": True,
        "parse": "relations_audit",
    },
)

ENGINE_AUDIT_SUMMARY_RE: Final[re.Pattern[str]] = re.compile(
    r"案例\s*(\d+)；有问题\s*(\d+)；问题种类\s*(\d+)；口径说明\s*(\d+)"
)
RELATIONS_AUDIT_SUMMARY_RE: Final[re.Pattern[str]] = re.compile(r"结论:\s*(全部通过|存在问题)")

#: Kill List（任务卡 §1 逐条对应）。pattern 支持目录、单文件与 fnmatch 通配。
KILL_LIST: Final[tuple[dict[str, Any], ...]] = (
    {
        "id": "claims-aggregation",
        "label": "聚合规则/假断语层",
        "patterns": (
            "theory/production/claim-rules-v1.yaml",
            "engine/claims/rule_loader.py",
            "theory/claims/conditions-v2/pilot-20.yaml",
            "engine/claims/condition_ir",
        ),
    },
    {
        "id": "legacy-architecture",
        "label": "旧架构层",
        "patterns": (
            "engine/v5",
            "engine/v2",
            "engine/f09",
            "engine/governance",
            "engine/learning",
            "engine/asof",
            "engine/decision",
            "engine/energy",
            "engine/picture",
            "engine/yingqi",
        ),
    },
    {
        "id": "dead-tools",
        "label": "已判死工具",
        "patterns": (
            "tools/timing_model_v1.py",
            "tools/domain_labels_wealth_health*.py",
            "tools/career_label_feasibility.py",
            "tools/career_path_*.py",
            "tools/m2y395_*.py",
        ),
    },
    {
        "id": "scaffold-tests",
        "label": "脚手架测试",
        "patterns": (
            "tests/f09",
            "tests/governance",
            "tests/v5",
            "tests/asof",
            "tests/evaluation",
        ),
    },
    {
        "id": "process-docs",
        "label": "过程文档（只列，不删）",
        "patterns": ("plans",),
    },
)

#: 与 tests/governance/test_v5_import_freeze.py 对齐的扫描排除规则。
EXCLUDED_DIR_NAMES: Final[frozenset[str]] = frozenset(
    {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".worktrees",
        "node_modules",
    }
)

MODULE_REF_RE: Final[re.Pattern[str]] = re.compile(r"^(engine|tools)(\.[A-Za-z_]\w*)+$")
PATH_REF_RE: Final[re.Pattern[str]] = re.compile(r"(?<![\w./-])(engine|tools|tests|theory)/[A-Za-z0-9_./-]+")
#: 审计脚本自身不能算「引用者」，否则 KILL_LIST 里的路径字面量会把自己变成消费者。
SELF_PATH: Final[str] = "tools/kill_list_dependency_audit.py"
DYNAMIC_CALL_NAMES: Final[frozenset[str]] = frozenset(
    {"import_module", "importorskip", "__import__", "load_module", "patch", "patch_module"}
)
FALLBACK_IMPORT_RE: Final[re.Pattern[str]] = re.compile(
    r"^\s*(?:from\s+(?P<src>\.*[A-Za-z_][\w.]*)\s+import\s+(?P<names>[^#]+)|import\s+(?P<plain>[^#]+))"
)

PROBE_SNIPPET: Final[str] = r"""
import io, json, runpy, sys
from contextlib import redirect_stdout

module = sys.argv[1]
args = json.loads(sys.argv[2])
sys.argv = [module] + args
buf = io.StringIO()
code = 0
try:
    with redirect_stdout(buf):
        try:
            runpy.run_module(module, run_name="__main__")
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
except BaseException as exc:  # noqa: BLE001 - 探针必须报告任何崩溃，而不是静默
    code = 99
    sys.stderr.write("__PROBE_ERROR__" + type(exc).__name__ + ": " + str(exc)[:300] + "\n")
mods = sorted(m for m in sys.modules if m.split(".")[0] in ("engine", "tools"))
payload = {"exit": code, "modules": mods, "tail": buf.getvalue()[-4000:]}
sys.stdout.write("__MODULES__" + json.dumps(payload, ensure_ascii=True))
"""


# ---------------------------------------------------------------- 路径与索引


def rel_posix(path: Path) -> str:
    """仓库内相对路径，统一 posix 分隔符。"""
    return path.resolve().relative_to(ROOT).as_posix()


def is_excluded_dir(name: str) -> bool:
    return name in EXCLUDED_DIR_NAMES or name.startswith(".") or name.startswith("pytest-of-")


def iter_py_files() -> list[str]:
    """确定性遍历仓库内 .py（排除 .venv / 点目录 / 缓存 / pytest-of-*）。"""
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(name for name in dirnames if not is_excluded_dir(name))
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                found.append(rel_posix(Path(dirpath) / filename))
    return sorted(found)


def module_of(rel: str) -> str:
    parts = rel[: -len(".py")].split("/")
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def is_package_init(rel: str) -> bool:
    return rel.endswith("/__init__.py")


def package_of(rel: str) -> str:
    module = module_of(rel)
    return module if is_package_init(rel) else module.rpartition(".")[0]


@dataclass(frozen=True)
class ImportStmt:
    raw_target: str
    lineno: int
    kind: str  # "import" | "from"


@dataclass
class Edge:
    source: str  # rel path
    target: str  # rel path
    lineno: int
    kind: str  # "import" | "from" | "package"


@dataclass
class Item:
    path: str
    module: str | None
    kind: str  # "module" | "data" | "docs"
    group: str
    category: str
    parse_mode: str = "ast"
    in_hard_entry_closure: bool = False
    reached_by_entries: list[str] = field(default_factory=list)
    imported_by: list[dict[str, Any]] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    kill_list_imported_by: list[dict[str, Any]] = field(default_factory=list)
    string_refs: list[dict[str, Any]] = field(default_factory=list)
    ruler_string_refs: list[dict[str, Any]] = field(default_factory=list)
    blockers: dict[str, int] = field(default_factory=dict)
    runtime_loaded: dict[str, bool] = field(default_factory=dict)
    breaks_481_0: bool = False
    klass: str = CLASS_UNKNOWN
    role: str = ""
    reason: str = ""
    recommendation: str = ""
    batch: int | None = None
    sub_batch: str | None = None
    batch_note: str = ""
    order_in_batch: int | None = None
    entry_chain: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- 静态 import 图


def collect_imports(rel: str, tree: ast.AST) -> list[ImportStmt]:
    """把一棵 AST 的 import 语句展开成候选模块名（含 from-import 的名字）。"""
    pkg = package_of(rel)
    stmts: list[ImportStmt] = []

    def push(raw: str, lineno: int, kind: str) -> None:
        stmts.append(ImportStmt(raw_target=raw, lineno=lineno, kind=kind))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                push(alias.name, node.lineno, "import")
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = pkg
                for _ in range(node.level - 1):
                    base = base.rpartition(".")[0]
                prefix = f"{base}.{node.module}" if node.module else base
            else:
                prefix = node.module or ""
            if prefix:
                push(prefix, node.lineno, "from")
                for alias in node.names:
                    if alias.name != "*":
                        push(f"{prefix}.{alias.name}", node.lineno, "from")
            else:  # from . import x
                for alias in node.names:
                    push(f"{pkg}.{alias.name}", node.lineno, "from")
    return stmts


def fallback_imports(rel: str, source: str) -> list[ImportStmt]:
    """PEP 695 等本解释器无法 ast.parse 的文件：用行级正则兜底（近似，已声明）。"""
    pkg = package_of(rel)
    stmts: list[ImportStmt] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        match = FALLBACK_IMPORT_RE.match(line)
        if match is None:
            continue
        if match.group("plain"):
            for piece in match.group("plain").split(","):
                name = piece.split(" as ")[0].strip().strip("()")
                if name:
                    stmts.append(ImportStmt(raw_target=name, lineno=lineno, kind="import"))
            continue
        src = match.group("src").strip().strip("()")
        dots = len(src) - len(src.lstrip("."))
        src = src.lstrip(".")
        names = match.group("names").strip().strip("()")
        if dots:
            base = pkg
            for _ in range(dots - 1):
                base = base.rpartition(".")[0]
            prefix = f"{base}.{src}" if src else base
        else:
            prefix = src
        if not prefix:
            continue
        stmts.append(ImportStmt(raw_target=prefix, lineno=lineno, kind="from"))
        for piece in names.split(","):
            name = piece.split(" as ")[0].strip().strip("()")
            if name and name != "*":
                stmts.append(ImportStmt(raw_target=f"{prefix}.{name}", lineno=lineno, kind="from"))
    return stmts


def resolve_edges(rel: str, stmts: Iterable[ImportStmt], index: dict[str, str]) -> list[Edge]:
    """把 import 目标落到仓库文件；父包 __init__ 目标记为 synthetic package 边。"""
    edges: list[Edge] = []
    seen: set[tuple[str, int, str]] = set()
    for stmt in stmts:
        target = index.get(stmt.raw_target)
        if target is not None:
            key = (target, stmt.lineno, stmt.kind)
            if key not in seen:
                seen.add(key)
                edges.append(Edge(source=rel, target=target, lineno=stmt.lineno, kind=stmt.kind))
        # 导入子模块会先执行父包 __init__：父包被归档同样会断。
        parts = stmt.raw_target.split(".")
        for cut in range(len(parts) - 1, 0, -1):
            parent = index.get(".".join(parts[:cut]))
            if parent is None:
                continue
            key = (parent, stmt.lineno, "package")
            if key not in seen:
                seen.add(key)
                edges.append(Edge(source=rel, target=parent, lineno=stmt.lineno, kind="package"))
    return edges


def collect_string_refs(rel: str, tree: ast.AST) -> list[dict[str, Any]]:
    """收集全部字符串常量（后续再匹配 Kill List 目标），并标注动态 import 调用。

    不在这里按形态过滤：数据文件常以 `ROOT / "theory" / "claims" / "pilot-20.yaml"`
    分段拼接，只有末尾的 basename 是独立常量，必须留到目标匹配阶段再筛。
    """
    dynamic_lines: set[tuple[int, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = ""
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            name = func.attr
        if name not in DYNAMIC_CALL_NAMES:
            continue
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                dynamic_lines.add((node.lineno, arg.value))

    refs: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        value = node.value.strip()
        if not value or len(value) > 200:
            continue
        via = "dynamic" if (node.lineno, node.value) in dynamic_lines else "string"
        refs.append({"from": rel, "line": node.lineno, "value": value, "via": via})
    return refs


# ---------------------------------------------------------------- 尺子定义


def load_pytest_ini() -> dict[str, Any]:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return data.get("tool", {}).get("pytest", {}).get("ini_options", {})


def pytest_ignored_roots() -> list[str]:
    """addopts 里的 --ignore=...：默认门禁不收集的目录。"""
    roots: list[str] = []
    for token in load_pytest_ini().get("addopts", []):
        token = str(token)
        if token.startswith("--ignore="):
            roots.append(token.split("=", 1)[1].replace("\\", "/").strip("/"))
    return sorted(dict.fromkeys(roots))


#: 「尺子」= 事实层判据：481/0 的测量装置。来自裁决 §3「tests/facts、tests/api 是尺子」。
#: 其它 testpaths 里的测试是「门禁测试」：必须保持绿，但 tests/ 已由 ADR-004 降级为可改
#: （不得删放宽判据让红变绿），因此它们不构成「永不可归档」，只要求同批改/归档。
RULER_TESTPATHS: Final[tuple[str, ...]] = ("tests/facts", "tests/api", "tests/predicates")


def gate_roots() -> list[str]:
    """默认门禁实际收集的范围：testpaths 去掉 addopts --ignore。"""
    ignored = pytest_ignored_roots()
    roots: list[str] = []
    for path in load_pytest_ini().get("testpaths", []):
        rel = str(path).replace("\\", "/").strip("/")
        if not (ROOT / rel).exists():
            continue
        if any(rel == ignore or rel.startswith(ignore + "/") for ignore in ignored):
            continue
        roots.append(rel)
    return sorted(dict.fromkeys(roots))


def ruler_roots() -> list[str]:
    """尺子 = facts/api/predicates 三套 + ADR-004 基线命令脚本。"""
    roots = [rel for rel in RULER_TESTPATHS if (ROOT / rel).exists()]
    if (ROOT / "tools/verify_baseline.py").is_file():
        roots.append("tools/verify_baseline.py")
    return sorted(dict.fromkeys(roots))


def under(rel: str, root: str) -> bool:
    return rel == root or rel.startswith(root + "/")


def is_ruler_file(rel: str, roots: Sequence[str]) -> bool:
    return any(under(rel, root) for root in roots)


def importer_tier(rel: str, rulers: Sequence[str], gate: Sequence[str]) -> str:
    """引用者分层：尺子 / 门禁测试 / 门禁外测试 / 活引擎 / 活工具 / 冒烟 / 其它。"""
    if is_ruler_file(rel, rulers):
        return "ruler"
    if is_ruler_file(rel, gate):
        return "gate-test"
    if rel.startswith("tests/"):
        return "test-outside-gate"
    if rel.startswith("engine/"):
        return "engine"
    if rel.startswith("tools/"):
        return "tools"
    if rel.startswith("smoke/"):
        return "smoke"
    return "other"


# ---------------------------------------------------------------- 运行期探针


def interpreter_label() -> str:
    exe = Path(sys.executable)
    try:
        return exe.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return exe.name


def run_probe(probe: dict[str, Any], timeout: int) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONHASHSEED"] = "0"
    cmd = [sys.executable, "-c", PROBE_SNIPPET, probe["module"], json.dumps(probe["argv"], ensure_ascii=False)]
    record: dict[str, Any] = {
        "id": probe["id"],
        "module": probe["module"],
        "argv": list(probe["argv"]),
        "covers_481": bool(probe["covers_481"]),
        "interpreter": interpreter_label(),
    }
    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        record.update({"exit_code": None, "status": "timeout", "modules": []})
        return record
    stdout = proc.stdout or ""
    marker = stdout.rfind("__MODULES__")
    modules: list[str] = []
    tail = ""
    exit_code: int | None = None
    if marker >= 0:
        try:
            payload = json.loads(stdout[marker + len("__MODULES__") :])
            modules = sorted(str(name) for name in payload.get("modules", []))
            tail = str(payload.get("tail", ""))
            exit_code = int(payload.get("exit", 0))
        except (ValueError, TypeError):
            modules = []
    metrics: dict[str, Any] = {}
    if probe.get("parse") == "engine_audit":
        match = ENGINE_AUDIT_SUMMARY_RE.search(tail)
        if match:
            metrics = {
                "cases": int(match.group(1)),
                "fails": int(match.group(2)),
                "fail_kinds": int(match.group(3)),
                "declared_notes": int(match.group(4)),
            }
    elif probe.get("parse") == "relations_audit":
        match = RELATIONS_AUDIT_SUMMARY_RE.search(tail)
        if match:
            metrics = {"verdict": match.group(1)}

    record.update(
        {
            "exit_code": exit_code if exit_code is not None else proc.returncode,
            "status": "ok" if marker >= 0 else "unparsed",
            "metrics": metrics,
            "modules": modules,
        }
    )
    return record


# ---------------------------------------------------------------- 分类


def recommend(klass: str, item: Item, hits: Sequence[dict[str, Any]]) -> str:
    live = sorted({row["from"] for row in hits if row["tier"] in ("engine", "tools", "smoke", "other")})
    gate = sorted({row["from"] for row in hits if row["tier"] == "gate-test"})
    outside = sorted({row["from"] for row in hits if row["tier"] == "test-outside-gate"})
    if klass == CLASS_SAFE:
        if item.role == "order-blocked":
            return "本身无外部引用，但 importer 还在：跟着 importer 一起搬（先移 importer）"
        return "可直接移入 archive/；同批内按清单顺序（先 importer，后被 import 的模块）"
    if klass == CLASS_RULER:
        if item.role == "ruler":
            return "本文件就是尺子判据；归档/改名须先改 pyproject testpaths 或 ADR-004 授权"
        if item.role == "ruler-path-string":
            return "尺子按路径断言它存在：先改尺子（需人类批准），不得靠删判据变绿"
        if item.role == "needed-by-ruler":
            return "尺子锁住的模块依赖它：与上游一起保留，或先拆尺子"
        return "尺子（tests/facts、tests/api、tests/predicates）import 它：不得归档"
    if klass == CLASS_UNKNOWN:
        if item.kind == "docs":
            return "任务卡要求只列不删；不进入任何归档批次"
        return "只有动态 import / 字符串引用：人工确认后再定，禁止按『看起来没人用』归档"
    if item.role == "hard-entry":
        return f"先改写硬入口（{', '.join(item.reached_by_entries)}）的依赖路径；改写前一动就破 481/0"
    if item.role == "order-blocked":
        return "本身无外部引用，但 importer 还在：跟着 importer 一起搬（先移 importer）"
    if item.role == "gate-test-file":
        return "本文件就在门禁内：归档等于改门禁，须显式改 pyproject/testpaths 或目录（需人类批准）"
    if item.role == "gate-test-dynamic":
        return "先改门禁测试里的 importlib 调用（或确认该路径可选），再归档"
    if live:
        refs = "、".join(f"`{path}`" for path in live[:3])
        return f"先改活代码引用方（{refs}），再归档"
    if gate:
        refs = "、".join(f"`{path}`" for path in gate[:3])
        return f"先改/同批归档门禁测试（{refs}）；tests/ 可按 ADR-004 改，但不得让红变绿"
    if outside:
        refs = "、".join(f"`{path}`" for path in outside[:3])
        return f"引用方是门禁外测试（{refs}）：连同该测试一起归档即可"
    if item.role == "string-ref-live-code":
        return "先改活代码里的路径字面量（读该文件的工具脚本），再归档"
    return "先改引用方，再归档"


# ---------------------------------------------------------------- 主流程


def build_report(*, probe_runtime: bool = True, timeout: int = 300) -> dict[str, Any]:
    py_files = iter_py_files()
    index: dict[str, str] = {}
    for rel in py_files:
        module = module_of(rel)
        if module:
            index[module] = rel

    parse_fallbacks: list[str] = []
    imports_by_file: dict[str, list[ImportStmt]] = {}
    parse_mode: dict[str, str] = {}
    edges: list[Edge] = []
    string_refs: list[dict[str, Any]] = []
    for rel in py_files:
        raw = (ROOT / rel).read_bytes()
        stmts: list[ImportStmt]
        try:
            tree = ast.parse(raw, filename=rel)
        except SyntaxError:
            parse_fallbacks.append(rel)
            parse_mode[rel] = "regex"
            stmts = fallback_imports(rel, raw.decode("utf-8-sig", errors="replace"))
        else:
            parse_mode[rel] = "ast"
            stmts = collect_imports(rel, tree)
            string_refs.extend(collect_string_refs(rel, tree))
        imports_by_file[rel] = stmts
        edges.extend(resolve_edges(rel, stmts, index))

    # Kill List 归属：路径 -> 组（按 KILL_LIST 顺序，先命中先得）。
    def kill_group(rel: str) -> str | None:
        candidate = rel.rstrip("/")
        for group in KILL_LIST:
            for pattern in group["patterns"]:
                pattern = pattern.rstrip("/")
                if candidate == pattern or candidate.startswith(pattern + "/"):
                    return group["id"]
                if any(ch in pattern for ch in "*?[") and fnmatch.fnmatchcase(candidate, pattern):
                    return group["id"]
        return None

    def is_kill_list_path(rel: str) -> bool:
        return kill_group(rel) is not None

    entries = list(ENTRYPOINTS)
    entry_closure: dict[str, set[str]] = {}
    entry_chain: dict[str, dict[str, list[str]]] = {}
    out_edges: dict[str, list[str]] = defaultdict(list)
    for edge in sorted(edges, key=lambda e: (e.source, e.target, e.lineno, e.kind)):
        out_edges[edge.source].append(edge.target)
    for adjacency in out_edges.values():
        adjacency[:] = sorted(dict.fromkeys(adjacency))

    for entry_id, path, _desc in entries:
        parents: dict[str, str | None] = {path: None}
        closure: set[str] = {path}
        queue: deque[str] = deque([path])
        while queue:
            current = queue.popleft()
            for nxt in out_edges.get(current, ()):  # 已排序 → BFS 确定性
                if nxt not in parents:
                    parents[nxt] = current
                    closure.add(nxt)
                    queue.append(nxt)
        entry_closure[entry_id] = closure

        def chain_to(target: str, _parents: dict[str, str | None] = parents) -> list[str]:
            chain: list[str] = []
            cursor: str | None = target
            while cursor is not None:
                chain.append(cursor)
                cursor = _parents.get(cursor)
            return list(reversed(chain))

        entry_chain[entry_id] = {target: chain_to(target) for target in closure}

    reached_by: dict[str, list[str]] = defaultdict(list)
    for entry_id, closure in entry_closure.items():
        for target in closure:
            reached_by[target].append(entry_id)
    for values in reached_by.values():
        values.sort()

    # 运行期探针
    probe_records: list[dict[str, Any]] = []
    runtime_paths: dict[str, set[str]] = {}
    if probe_runtime:
        for probe in PROBES:
            record = run_probe(probe, timeout=timeout)
            probe_records.append(record)
            runtime_paths[probe["id"]] = {index[name] for name in record["modules"] if name in index}

    rulers = ruler_roots()
    gate = gate_roots()

    # 反向边聚合
    inbound: dict[str, list[Edge]] = defaultdict(list)
    for edge in edges:
        inbound[edge.target].append(edge)
    for values in inbound.values():
        values.sort(key=lambda e: (e.source, e.lineno, e.kind))

    # Kill List 条目：.py 模块 + 数据文件 + 只列不删的文档目录
    item_paths: dict[str, str] = {}
    for rel in py_files:
        if is_kill_list_path(rel):
            item_paths[rel] = "module"
    data_paths: set[str] = set()
    for group in KILL_LIST:
        for pattern in group["patterns"]:
            if any(ch in pattern for ch in "*?["):
                continue
            candidate = ROOT / pattern
            if candidate.is_file() and not pattern.endswith(".py"):
                item_paths.setdefault(pattern, "data")
                data_paths.add(pattern)
            elif candidate.is_dir() and not any(True for _ in candidate.rglob("*.py")):
                item_paths.setdefault(pattern.rstrip("/") + "/", "docs")

    module_paths = {rel for rel, kind in item_paths.items() if kind == "module"}

    # 字符串引用 -> 目标条目（模块名 / 路径字面量 / 数据文件 basename）
    known_paths = sorted(set(py_files) | data_paths)
    data_basenames = {path.rsplit("/", 1)[-1]: path for path in data_paths}
    string_by_target: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ref in string_refs:
        if ref["from"] == SELF_PATH:
            continue
        value = ref["value"]
        targets: set[str] = set()
        if MODULE_REF_RE.match(value):
            for module_name, module_path in index.items():
                if value == module_name or value.startswith(module_name + "."):
                    targets.add(module_path)
        if PATH_REF_RE.search(value) or value.endswith(".yaml") or value.endswith(".json"):
            for rel in known_paths:
                if value == rel or value.endswith("/" + rel) or rel.endswith("/" + value):
                    targets.add(rel)
        basename = value.rsplit("/", 1)[-1]
        if basename in data_basenames:
            targets.add(data_basenames[basename])
        for target in targets:
            if target in item_paths and target != ref["from"]:
                string_by_target[target].append(ref)

    items: list[Item] = []
    for rel in sorted(item_paths):
        kind = item_paths[rel]
        group = kill_group(rel) or "unknown"
        item = Item(
            path=rel,
            module=module_of(rel) if kind == "module" else None,
            kind=kind,
            group=group,
            category=next((entry["label"] for entry in KILL_LIST if entry["id"] == group), group),
            parse_mode=parse_mode.get(rel, "n/a"),
        )
        if kind == "module":
            item.in_hard_entry_closure = rel in reached_by
            item.reached_by_entries = list(reached_by.get(rel, []))
            item.imports = sorted(
                {
                    index[stmt.raw_target]
                    for stmt in imports_by_file.get(rel, ())
                    if stmt.raw_target in index
                }
                - {rel}
            )
            rows: dict[tuple[str, int, str], dict[str, Any]] = {}
            seen_package_source: set[str] = set()
            for edge in inbound.get(rel, ()):
                if edge.kind == "package":
                    # 父包边按来源文件去重：一个文件 import 多个子模块只记最靠前的一处。
                    if edge.source in seen_package_source:
                        continue
                    seen_package_source.add(edge.source)
                    key = (edge.source, edge.lineno, "package")
                else:
                    key = (edge.source, edge.lineno, edge.kind)
                rows[key] = {
                    "from": edge.source,
                    "line": edge.lineno,
                    "kind": edge.kind,
                    "in_kill_list": edge.source in module_paths,
                    "is_ruler": is_ruler_file(edge.source, rulers),
                    "tier": importer_tier(edge.source, rulers, gate),
                }
            item.imported_by = [rows[key] for key in sorted(rows)]
            item.kill_list_imported_by = [row for row in item.imported_by if row["in_kill_list"]]
            item.runtime_loaded = {
                probe["id"]: rel in runtime_paths.get(probe["id"], set()) for probe in PROBES
            }
            item.breaks_481_0 = any(
                item.runtime_loaded.get(probe["id"]) and probe["covers_481"] for probe in PROBES
            ) and any(
                entry in item.reached_by_entries for entry in ("cli", "engine_audit", "relations_audit")
            )
        item.string_refs = sorted(
            string_by_target.get(rel, []), key=lambda r: (r["from"], r["line"], r["value"])
        )
        item.ruler_string_refs = [ref for ref in item.string_refs if is_ruler_file(ref["from"], rulers)]

        external_hits = [row for row in item.imported_by if not row["in_kill_list"]]
        ruler_hits = [row for row in external_hits if row["tier"] == "ruler"]
        gate_hits = [row for row in external_hits if row["tier"] == "gate-test"]
        live_hits = [row for row in external_hits if row["tier"] in ("engine", "tools", "smoke", "other")]
        outside_test_hits = [row for row in external_hits if row["tier"] == "test-outside-gate"]
        external_string = [
            ref for ref in item.string_refs if not is_kill_list_path(ref["from"]) and ref["from"] != rel
        ]
        ruler_strings = [ref for ref in item.string_refs if is_ruler_file(ref["from"], rulers)]
        gate_strings = [
            ref
            for ref in external_string
            if importer_tier(ref["from"], rulers, gate) == "gate-test" and ref["via"] == "string"
        ]
        gate_dynamic = [
            ref
            for ref in external_string
            if importer_tier(ref["from"], rulers, gate) == "gate-test" and ref["via"] == "dynamic"
        ]
        live_strings = [
            ref
            for ref in external_string
            if importer_tier(ref["from"], rulers, gate) in ("engine", "tools", "smoke", "other")
            and ref["via"] == "string"
        ]
        outside_test_strings = [
            ref for ref in external_string if importer_tier(ref["from"], rulers, gate) == "test-outside-gate"
        ]
        dynamic_strings = [ref for ref in external_string if ref["via"] == "dynamic"]
        item.blockers = {
            "ruler_importers": len({row["from"] for row in ruler_hits}),
            "gate_test_importers": len({row["from"] for row in gate_hits}),
            "live_code_importers": len({row["from"] for row in live_hits}),
            "outside_gate_test_importers": len({row["from"] for row in outside_test_hits}),
            "ruler_path_strings": len(ruler_strings),
            "gate_test_string_refs": len(gate_strings),
            "live_code_string_refs": len(live_strings),
            "outside_gate_test_string_refs": len(outside_test_strings),
            "dynamic_refs": len(dynamic_strings),
        }
        item.ruler_string_refs = sorted(
            ruler_strings, key=lambda r: (r["from"], r["line"], r["value"])
        )

        if kind == "docs":
            item.klass, item.role = CLASS_UNKNOWN, "docs-listed-only"
            item.reason = "任务卡 §1 明确『只列，不删』；不是代码模块"
        elif is_ruler_file(rel, rulers):
            item.klass, item.role = CLASS_RULER, "ruler"
            item.reason = "本文件就在尺子集合内（tests/facts、tests/api、tests/predicates、verify_baseline）"
        elif ruler_hits:
            item.klass, item.role = CLASS_RULER, "used-by-ruler"
            item.reason = "尺子（事实层判据）import 了它"
        elif ruler_strings:
            item.klass, item.role = CLASS_RULER, "ruler-path-string"
            item.reason = "尺子按路径断言它存在"
        elif is_ruler_file(rel, gate):
            item.klass, item.role = CLASS_REFERENCED, "gate-test-file"
            item.reason = "本文件就在默认 pytest 门禁内：归档=改门禁（需显式改 pyproject/目录）"
        elif item.in_hard_entry_closure:
            item.klass, item.role = CLASS_REFERENCED, "hard-entry"
            item.reason = "硬入口闭包依赖它"
        elif live_hits:
            item.klass, item.role = CLASS_REFERENCED, "live-code"
            item.reason = "Kill List 外活代码 import 了它"
        elif gate_hits:
            item.klass, item.role = CLASS_REFERENCED, "gate-test"
            item.reason = "门禁测试 import 了它（测试与模块需同批改/归档）"
        elif live_strings:
            item.klass, item.role = CLASS_REFERENCED, "string-ref-live-code"
            item.reason = "活代码用路径字面量读取/加载它"
        elif gate_strings or gate_dynamic:
            item.klass = CLASS_REFERENCED
            item.role = "gate-test-string" if gate_strings else "gate-test-dynamic"
            item.reason = (
                "门禁测试按路径断言它存在（改测试即可）"
                if gate_strings
                else "门禁测试用 importlib 动态 import 它（importlib.import_module）"
            )
        elif outside_test_hits or outside_test_strings:
            item.klass, item.role = CLASS_REFERENCED, "outside-gate-test"
            item.reason = "只被门禁外测试 import/断言（默认 pytest 不收集）"
        elif dynamic_strings:
            item.klass, item.role = CLASS_UNKNOWN, "dynamic-import-only"
            item.reason = "只有动态 import（importlib/mock.patch）引用，静态图无法判定是否必经"
        elif external_string:
            item.klass, item.role = CLASS_UNKNOWN, "string-only"
            item.reason = "只有字符串引用，静态 import 图看不见"
        else:
            item.klass, item.role = CLASS_SAFE, "leaf"
            item.reason = "Kill List 外无 import、无字符串引用"
        item.recommendation = recommend(item.klass, item, external_hits)
        if item.in_hard_entry_closure:
            entry_order = {entry_id: offset for offset, (entry_id, _p, _d) in enumerate(entries)}
            best = sorted(item.reached_by_entries, key=lambda name: entry_order[name])[0]
            item.entry_chain = entry_chain[best].get(rel, [])
        items.append(item)

    base_batch = {CLASS_SAFE: 1, CLASS_REFERENCED: 2, CLASS_UNKNOWN: 3, CLASS_RULER: None}
    for item in items:
        item.batch = base_batch[item.klass]

    # 批号顺延（松弛到不动点）：
    # ① 归档 X 会断它的 importer，所以 X 必须等 importer 先搬 → X 的批号 ≥ 所有 KL importer；
    # ② 尺子锁住（永不归档）的模块 import 的 X 也不能归档 → X 顺延到「保留」。
    kl_importers: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        if edge.source in module_paths and edge.target in module_paths and edge.source != edge.target:
            kl_importers[edge.target].add(edge.source)
    batch_by_path = {item.path: item.batch for item in items}
    changed = True
    while changed:
        changed = False
        for item in items:
            if item.batch is None:
                continue
            source_batches = [
                batch_by_path[src] for src in kl_importers.get(item.path, ()) if src in batch_by_path
            ]
            if any(source is None for source in source_batches):
                item.batch = None
                batch_by_path[item.path] = None
                item.batch_note = "顺延到保留：尺子锁住的 importer 依赖它"
                changed = True
                continue
            new_batch = max([item.batch] + source_batches) if source_batches else item.batch
            if new_batch != item.batch:
                item.batch = new_batch
                batch_by_path[item.path] = new_batch
                item.batch_note = f"顺延：importer 在批次 {new_batch}"
                changed = True
    for item in items:
        if item.batch is None and item.klass != CLASS_RULER:
            item.klass = CLASS_RULER
            item.role = "needed-by-ruler"
            item.reason = "尺子锁住的模块 import 了它：归档会间接断尺子"
            item.recommendation = recommend(item.klass, item, [])
        if item.batch == 2:
            if item.klass == CLASS_SAFE:
                item.sub_batch = "2c"
                item.role = "order-blocked"
                item.reason = "本身无外部引用，但 importer 在批次 2，必须跟着先搬"
                item.recommendation = recommend(item.klass, item, [])
            elif item.role == "outside-gate-test":
                item.sub_batch = "2a"
            else:
                item.sub_batch = "2b"

    def topo_order(members: Sequence[Item]) -> list[Item]:
        """批内顺序：importer 先于被 import 的模块（否则先移后者会断前者）。"""
        paths = {item.path for item in members}
        importers: dict[str, set[str]] = defaultdict(set)
        remaining: dict[str, set[str]] = {}
        for item in members:
            remaining[item.path] = set()
        for edge in edges:
            if edge.source in paths and edge.target in paths and edge.source != edge.target:
                remaining[edge.source].add(edge.target)
                importers[edge.target].add(edge.source)
        placed: list[str] = []
        while remaining:
            ready = sorted(
                path for path in remaining if not any(src in remaining for src in importers.get(path, ()))
            )
            if not ready:  # 批内存在环：按路径确定性破环
                ready = [sorted(remaining)[0]]
            for path in ready:
                placed.append(path)
                remaining.pop(path, None)
        by_path = {item.path: item for item in members}
        return [by_path[path] for path in placed]

    ordered: list[Item] = []
    batch_specs: list[tuple[int | None, str, str]] = [
        (1, "安全归档（现在就能搬）", CLASS_SAFE),
        (2, "有引用（需先改）", CLASS_REFERENCED),
        (3, "不可判", CLASS_UNKNOWN),
        (None, "尺子在用（保留）", CLASS_RULER),
    ]
    for batch_no, _label, _klass in batch_specs:
        if batch_no is None:
            group = sorted(
                (item for item in items if item.batch is None), key=lambda i: (i.role, i.path)
            )
        else:
            group = topo_order([item for item in items if item.batch == batch_no])
        for offset, item in enumerate(group, start=1):
            item.order_in_batch = offset if item.batch is not None else None
        ordered.extend(group)

    # 不变量（自检）：批号必须满足「先 importer 后 imported」，且「安全归档」不得有外部引用者。
    by_path = {item.path: item for item in items}
    violations: list[dict[str, Any]] = []
    for item in items:
        if item.batch is None:
            continue
        for source in sorted(kl_importers.get(item.path, ())):
            source_item = by_path.get(source)
            if source_item is None or source_item is item:
                continue
            if source_item.batch is None:
                violations.append({"kind": "importer-kept", "item": item.path, "importer": source})
            elif source_item.batch > item.batch:
                violations.append(
                    {
                        "kind": "importer-later-batch",
                        "item": item.path,
                        "batch": item.batch,
                        "importer": source,
                        "importer_batch": source_item.batch,
                    }
                )
        if item.klass == CLASS_SAFE:
            external = sorted({row["from"] for row in item.imported_by if not row["in_kill_list"]})
            if external:
                violations.append(
                    {"kind": "safe-but-external-importer", "item": item.path, "importers": external}
                )
    invariants = {
        "ok": not violations,
        "checked_items": sum(1 for item in items if item.batch is not None),
        "violation_count": len(violations),
        "violations": violations[:20],
    }

    by_class = Counter(item.klass for item in items)
    by_class_modules = Counter(item.klass for item in items if item.kind == "module")
    breaks = [item for item in items if item.breaks_481_0]
    grouped_edges: dict[tuple[str, str], dict[str, Any]] = {}
    for edge in edges:
        if not (edge.source in module_paths or edge.target in module_paths):
            continue
        row = grouped_edges.setdefault(
            (edge.source, edge.target), {"from": edge.source, "to": edge.target, "lines": [], "kinds": []}
        )
        if edge.lineno not in row["lines"]:
            row["lines"].append(edge.lineno)
        if edge.kind not in row["kinds"]:
            row["kinds"].append(edge.kind)
    edge_records = []
    for key in sorted(grouped_edges):
        row = grouped_edges[key]
        row["lines"].sort()
        row["kinds"].sort()
        edge_records.append(row)

    by_probe = {record["id"]: record for record in probe_records}
    engine_probe = by_probe.get("engine_audit", {})
    relations_probe = by_probe.get("relations_audit", {})
    baseline_481: dict[str, Any] = {
        "definition": (
            "481/0 = tools.engine_audit 全量 481 盘 0 错 + tools.relations_audit 全通过；"
            "tools.verify_baseline --compare 以这两条命令为判据"
        ),
        "engine_audit": {
            "exit_code": engine_probe.get("exit_code"),
            **engine_probe.get("metrics", {}),
        },
        "relations_audit": {
            "exit_code": relations_probe.get("exit_code"),
            **relations_probe.get("metrics", {}),
        },
    }
    baseline_481["ok"] = (
        baseline_481["engine_audit"].get("cases") == 481
        and baseline_481["engine_audit"].get("fails") == 0
        and baseline_481["engine_audit"].get("exit_code") == 0
        and baseline_481["relations_audit"].get("verdict") == "全部通过"
        and baseline_481["relations_audit"].get("exit_code") == 0
    )

    summary = {
        "items_total": len(items),
        "modules_total": sum(1 for item in items if item.kind == "module"),
        "data_files_total": sum(1 for item in items if item.kind == "data"),
        "docs_total": sum(1 for item in items if item.kind == "docs"),
        "by_class": {name: by_class.get(name, 0) for name in CLASSES},
        "by_class_modules": {name: by_class_modules.get(name, 0) for name in CLASSES},
        "breaks_481_0": [item.path for item in breaks],
        "batch_counts": {
            "1_safe_now": sum(1 for item in items if item.batch == 1),
            "2a_outside_gate_test_only": sum(1 for item in items if item.sub_batch == "2a"),
            "2b_live_code_or_gate": sum(1 for item in items if item.sub_batch == "2b"),
            "2c_order_deferred": sum(1 for item in items if item.sub_batch == "2c"),
            "3_unknown": sum(1 for item in items if item.batch == 3),
            "docs_listed_only": sum(1 for item in items if item.kind == "docs"),
            "keep_ruler": sum(1 for item in items if item.batch is None),
        },
        "static_class_vs_batch": {
            name: {
                "static": by_class.get(name, 0),
                "archivable_now_batch1": sum(
                    1 for item in items if item.klass == name and item.batch == 1
                ),
                "deferred": sum(
                    1
                    for item in items
                    if item.klass == name and item.batch is not None and item.batch != base_batch[name]
                ),
                "held_by_ruler": sum(
                    1 for item in items if item.klass == name and item.batch is None
                ),
            }
            for name in CLASSES
        },
        "hard_entry_closure_sizes": {entry_id: len(closure) for entry_id, closure in entry_closure.items()},
        "hard_entry_kill_list_hits": {
            entry_id: sum(1 for path in closure if path in module_paths)
            for entry_id, closure in entry_closure.items()
        },
        "kill_list_internal_edges": sum(
            1 for edge in edges if edge.source in module_paths and edge.target in module_paths
        ),
        "kill_list_cross_group_edges": sum(
            1
            for edge in edges
            if edge.source in module_paths
            and edge.target in module_paths
            and kill_group(edge.source) != kill_group(edge.target)
        ),
        "parse_fallbacks": sorted(parse_fallbacks),
        "py_files_scanned": len(py_files),
        "rulers": rulers,
        "pytest_ignored_roots": pytest_ignored_roots(),
        "probes_run": [record["id"] for record in probe_records],
        "baseline_481_ok": baseline_481["ok"],
        "invariants": invariants,
    }

    report: dict[str, Any] = {
        "schema": SCHEMA,
        "task": TASK,
        "generated_by": "tools/kill_list_dependency_audit.py",
        "read_only": True,
        "method": [
            "静态：ast 解析全仓 .py，从 6 个硬入口做确定性 BFS；父包 __init__ 记为 package 边",
            "兜底：PEP 695 等本解释器解析不了的文件用行级正则提取 import，并在 items[].parse_mode 标注",
            "反向：每个 Kill List 条目列出全部入边（文件 + 行号）与字符串/动态引用",
            "edges 按 (from, to) 聚合，lines 保留全部行号，kinds 标注 import / from / package",
            "运行期：subprocess 跑 engine.cli all 与全量 engine_audit / relations_audit，取 sys.modules 与 481/0 计数",
            "尺子：tests/facts、tests/api、tests/predicates + tools/verify_baseline.py；命中即『尺子在用』",
            "门禁测试：testpaths 内非尺子的测试，可按 ADR-004 改/同批归档，不构成永不可归档",
        ],
        "kill_list_groups": [
            {"id": group["id"], "label": group["label"], "patterns": list(group["patterns"])}
            for group in KILL_LIST
        ],
        "entries": [
            {
                "id": entry_id,
                "path": path,
                "description": desc,
                "closure_size": len(entry_closure[entry_id]),
                "modules": sorted(entry_closure[entry_id]),
            }
            for entry_id, path, desc in entries
        ],
        "runtime_probes": probe_records,
        "baseline_481": baseline_481,
        "summary": summary,
        "batches": [
            {
                "batch": batch_no,
                "label": label,
                "class": klass,
                "count": sum(1 for item in items if item.batch == batch_no),
                "sub_counts": {
                    key: sum(1 for item in items if item.batch == batch_no and item.sub_batch == key)
                    for key in ("2a", "2b", "2c")
                },
                "items": [item.path for item in ordered if item.batch == batch_no],
            }
            for batch_no, label, klass in batch_specs
        ],
        "items": [
            {
                "path": item.path,
                "module": item.module,
                "kind": item.kind,
                "group": item.group,
                "category": item.category,
                "class": item.klass,
                "role": item.role,
                "reason": item.reason,
                "batch": item.batch,
                "sub_batch": item.sub_batch,
                "batch_note": item.batch_note,
                "order_in_batch": item.order_in_batch,
                "parse_mode": item.parse_mode,
                "in_hard_entry_closure": item.in_hard_entry_closure,
                "reached_by_entries": item.reached_by_entries,
                "entry_chain": item.entry_chain,
                "imports": item.imports,
                "imported_by": item.imported_by,
                "kill_list_imported_by": item.kill_list_imported_by,
                "blockers": item.blockers,
                "string_refs": item.string_refs,
                "ruler_string_refs": item.ruler_string_refs,
                "runtime_loaded": item.runtime_loaded,
                "breaks_481_0": item.breaks_481_0,
                "recommendation": item.recommendation,
            }
            for item in ordered
        ],
        "edges": edge_records,
        "limitations": [
            "反射取包：getattr(engine, 'v5').x 之类写法不在 ast.Import 覆盖内",
            "字符串匹配：只识别 (engine|tools|tests|theory)/ 路径字面量与 a.b.c 模块名，拼接字符串看不出来",
            "运行期探针：engine_audit / relations_audit 跑全量 481 盘，engine.cli 只跑 1 盘冒烟；481/0 判据由 tools.verify_baseline 复核",
            "query_theory 探针：未跑，因为它会写 theory/_light_index.json 缓存，违反本卡只读约束",
            "白名单数据：路径字面量可能是清单/白名单（如 tests/governance/v5_frozen_importers.py 的 51 条 v5 路径），本审计按最保守口径计为引用",
            "批内顺序：Kill List 内部互相引用不构成阻塞，但同批归档必须先移 importer 再移被 import 的模块",
        ],
    }
    return report


# ---------------------------------------------------------------- Markdown


def _md_cell(text: str) -> str:
    """表格单元格转义：竖线会把 Markdown 表格切列。"""
    return text.replace("|", "\\|")


def _fmt_refs(rows: Sequence[dict[str, Any]], limit: int = 3) -> str:
    if not rows:
        return "—"
    parts: list[str] = []
    for row in rows[:limit]:
        tag = ""
        if row.get("tier") == "ruler":
            tag = "（尺子）"
        elif row.get("tier") == "gate-test":
            tag = "（门禁）"
        elif row.get("in_kill_list"):
            tag = "（KL）"
        note = " [包]" if row.get("kind") == "package" else ""
        parts.append(f"`{row['from']}`:{row['line']}{note}{tag}")
    if len(rows) > limit:
        parts.append(f"…+{len(rows) - limit}")
    return "<br>".join(parts)


def _evidence(item: dict[str, Any]) -> str:
    chunks: list[str] = []
    if item["in_hard_entry_closure"]:
        chunks.append("硬入口：" + ", ".join(item["reached_by_entries"]))
    external = [row for row in item["imported_by"] if not row["in_kill_list"]]
    if external:
        chunks.append("外部 import：" + _fmt_refs(external))
    if item["ruler_string_refs"]:
        chunks.append(
            "尺子路径断言："
            + ", ".join(f"`{ref['from']}`:{ref['line']}" for ref in item["ruler_string_refs"][:2])
        )
    strings = [ref for ref in item["string_refs"] if ref not in item["ruler_string_refs"]]
    if strings:
        rendered = []
        for ref in strings[:2]:
            tag = "（importlib 动态）" if ref["via"] == "dynamic" else ""
            rendered.append(f"`{ref['value']}`@{ref['from']}:{ref['line']}{tag}")
        chunks.append("字符串：" + ", ".join(rendered))
    if item["kill_list_imported_by"]:
        chunks.append("KL 内部：" + _fmt_refs(item["kill_list_imported_by"], limit=2))
    loaded = sorted(k for k, v in item["runtime_loaded"].items() if v)
    if loaded:
        chunks.append("运行期：" + "、".join(loaded))
    return "<br>".join(chunks) or "—"


def _strength(item: dict[str, Any]) -> str:
    blockers = item["blockers"]
    bits: list[str] = []
    if blockers["ruler_importers"] or blockers["ruler_path_strings"]:
        bits.append(f"尺子 {blockers['ruler_importers'] + blockers['ruler_path_strings']}")
    if blockers["gate_test_importers"]:
        bits.append(f"门禁测试 {blockers['gate_test_importers']}")
    if blockers["live_code_importers"]:
        bits.append(f"活代码 {blockers['live_code_importers']}")
    if blockers["outside_gate_test_importers"]:
        bits.append(f"门禁外测试 {blockers['outside_gate_test_importers']}")
    if blockers["gate_test_string_refs"]:
        bits.append(f"门禁字符串 {blockers['gate_test_string_refs']}")
    if blockers["live_code_string_refs"]:
        bits.append(f"活代码字符串 {blockers['live_code_string_refs']}")
    if blockers["dynamic_refs"]:
        bits.append(f"动态 import {blockers['dynamic_refs']}")
    return "、".join(bits) or "—"


def render_markdown(report: dict[str, Any], json_sha256: str, json_rel: str) -> str:
    summary = report["summary"]
    by_class = summary["by_class"]
    batch_counts = summary["batch_counts"]
    batches = {batch["batch"]: batch for batch in report["batches"]}
    lines: list[str] = []
    add = lines.append
    add(f"# Kill List 依赖审计 v1（{report['task']}，只读）")
    add("")
    add("> 生成：`python -m tools.kill_list_dependency_audit`（确定性；两次运行 JSON 字节一致）")
    add(f"> 机器可读：[`{json_rel}`]({json_rel}) · sha256 `{json_sha256}`")
    add("> 口径：静态 `ast` import 图（6 硬入口递归 BFS）+ 运行期 `sys.modules` 探针；**本审计不移动、不删除任何文件**。")
    add("")
    add("## 0. 一句话")
    add("")
    add(
        f"扫描 {summary['items_total']} 个 Kill List 条目（{summary['modules_total']} 个 .py 模块、"
        f"{summary['data_files_total']} 个数据文件、{summary['docs_total']} 个文档目录）："
        f"静态四类为 **安全归档 {by_class[CLASS_SAFE]}**、**有引用（需先改）{by_class[CLASS_REFERENCED]}**、"
        f"**尺子在用 {by_class[CLASS_RULER]}**、**不可判 {by_class[CLASS_UNKNOWN]}**；"
        f"按依赖顺延后**现在真正能搬的只有 {batch_counts['1_safe_now']} 个**（批次 1）；"
        f"「一动就破 481/0」的模块 **{len(summary['breaks_481_0'])}** 个"
        f"（基线 481 盘 / 0 错现场复跑：{'通过' if report['baseline_481']['ok'] else '未通过'}）。"
    )
    add("")
    add("## 1. 四类计数（静态判据）")
    add("")
    add("| 类 | 全部条目 | 仅 .py 模块 | 处置 |")
    add("|---|---:|---:|---|")
    disposition = {
        CLASS_SAFE: "批次 1；无外部引用者可立即移入 `archive/`",
        CLASS_REFERENCED: "批次 2，先改引用方再归档",
        CLASS_RULER: "不得归档；要动先改尺子（需人类批准）",
        CLASS_UNKNOWN: "批次 3，人工确认前不动",
    }
    for name in CLASSES:
        add(f"| {name} | {by_class[name]} | {summary['by_class_modules'][name]} | {disposition[name]} |")
    add("")
    add("> **类 ≠ 批次**：归档 X 会断掉 import X 的模块，因此被后续批 importer 依赖的条目必须顺延。")
    add(
        f"> 所以「安全归档 {by_class[CLASS_SAFE]} 个」里只有 {batch_counts['1_safe_now']} 个现在能搬，"
        f"其余 {batch_counts['2c_order_deferred']} 个要跟着 importer 一起搬（见 §4 的 2c）。"
    )
    add("")
    add("## 2. 硬入口递归闭包")
    add("")
    add("| 入口 | 路径 | 闭包模块数 | 闭包内 Kill List 模块 | 运行期探针 |")
    add("|---|---|---:|---:|---|")
    probes_by_id = {record["id"]: record for record in report["runtime_probes"]}
    for entry in report["entries"]:
        probe = probes_by_id.get(entry["id"])
        if probe is None:
            if entry["id"] == "query_theory":
                probe_note = "未跑（会写缓存，只读约束）"
            else:
                probe_note = "无独立探针（由 cli / engine_audit 同路径覆盖）"
        else:
            probe_note = f"exit={probe['exit_code']} · 加载 {len(probe['modules'])} 个 engine/tools 模块"
        add(
            f"| `{entry['id']}` | `{entry['path']}` | {entry['closure_size']} | "
            f"{summary['hard_entry_kill_list_hits'][entry['id']]} | {probe_note} |"
        )
    add("")
    add(
        f"Kill List 内部互相引用边 **{summary['kill_list_internal_edges']}** 条"
        f"（跨组 {summary['kill_list_cross_group_edges']} 条）：不构成阻塞，但同批归档必须先移 importer。"
    )
    add("")
    add("## 3. 「一动就破 481/0」的模块")
    add("")
    baseline = report["baseline_481"]
    engine_baseline = baseline["engine_audit"]
    relations_baseline = baseline["relations_audit"]
    add(
        "审计时现场跑基线：`tools.engine_audit` 案例 "
        f"**{engine_baseline.get('cases', '?')}**、有问题 **{engine_baseline.get('fails', '?')}**"
        f"（exit={engine_baseline.get('exit_code')}）；`tools.relations_audit` 结论 "
        f"**{relations_baseline.get('verdict', '未跑')}**（exit={relations_baseline.get('exit_code')}）。"
    )
    add("")
    if summary["breaks_481_0"]:
        add("判据：① 在 `cli` / `engine_audit` / `relations_audit` 闭包内；② 运行期 `sys.modules` 实际加载。两者缺一不列。")
        add("")
        add("| 模块 | 触及入口 | 运行期加载 | 最短 import 链（入口 → 模块） |")
        add("|---|---|---|---|")
        for item in report["items"]:
            if not item["breaks_481_0"]:
                continue
            chain = " ← ".join(f"`{p}`" for p in item["entry_chain"])
            loaded = "、".join(sorted(k for k, v in item["runtime_loaded"].items() if v))
            add(f"| `{item['path']}` | {', '.join(item['reached_by_entries'])} | {loaded} | {chain} |")
    else:
        add("**没有**：Kill List 内没有任何模块同时满足「硬入口闭包 + 运行期实际加载」。")
    add("")
    add("## 4. 分批归档顺序")
    add("")
    add("| 批 | 内容 | 条目数 | 前提 |")
    add("|---|---|---:|---|")
    add(f"| 1 | 安全归档（现在就能搬） | {batch_counts['1_safe_now']} | 无外部引用，且 importer 也都在批 1 |")
    add(f"| 2a | 只被门禁外测试引用 | {batch_counts['2a_outside_gate_test_only']} | 连同该测试一起归档 |")
    add(f"| 2b | 被活代码 / 门禁测试 / 字符串引用 | {batch_counts['2b_live_code_or_gate']} | 先改引用方（或同批归档测试） |")
    add(f"| 2c | 顺序顺延（本身无引用） | {batch_counts['2c_order_deferred']} | 跟着 importer 一起搬 |")
    add(f"| 3 | 不可判 | {batch_counts['3_unknown']} | 人工确认（含 {batch_counts['docs_listed_only']} 个只列不删文档） |")
    add(f"| — | 尺子在用（保留） | {batch_counts['keep_ruler']} | 不动 |")
    add("")
    for batch_no, title, hint in (
        (1, "批 1 · 安全归档", "批内顺序 = 先移 importer、再移被 import 的模块（拓扑序，环按路径破）。"),
        (2, "批 2 · 有引用（需先改）", "2a 先做（引用方本来就不在门禁里）；2b 要改活代码或门禁测试；2c 只是跟着搬。"),
        (3, "批 3 · 不可判", "人工确认前不动。"),
        (None, "保留 · 尺子在用", "永不归档；改判据须单独立项并说明理由。"),
    ):
        batch = batches[batch_no]
        add(f"### {title}（{batch['count']}）")
        add("")
        if batch["count"] == 0:
            add("（空）")
            add("")
            continue
        add(hint)
        add("")
        add("| # | 条目 | 类 | 子批 | 引用强度 | 关键证据 | 建议 |")
        add("|---:|---|---|---|---|---|---|")
        for item in report["items"]:
            if item["batch"] != batch_no:
                continue
            note = item["batch_note"]
            label = f"{item['class']}" + (f"（{note}）" if note else "")
            add(
                f"| {item['order_in_batch'] if item['order_in_batch'] is not None else '—'} | `{item['path']}` | "
                f"{label} | {item['sub_batch'] or '—'} | {_strength(item)} | {_evidence(item)} | "
                f"{item['recommendation']} |"
            )
        add("")
    add("## 5. 谁锁住了 Kill List")
    add("")
    add("| 引用来源 | 命中条目数 | 含义 |")
    add("|---|---:|---|")
    locks = [
        ("ruler_importers", "尺子 import（tests/facts、tests/api、tests/predicates）", "动它等于动 481/0 的测量装置"),
        ("ruler_path_strings", "尺子路径断言", "尺子按路径读/断言文件存在"),
        ("gate_test_importers", "门禁测试 import", "tests/ 可改（ADR-004），但要同批改/归档"),
        ("live_code_importers", "活代码 import（engine/ + tools/ + smoke/）", "必须先改生产代码"),
        ("outside_gate_test_importers", "门禁外测试 import", "默认 pytest 不收集，可连同归档"),
    ]
    for key, label, meaning in locks:
        count = sum(1 for item in report["items"] if item["blockers"].get(key))
        add(f"| {label} | {count} | {meaning} |")
    add("")
    add("## 6. 风险与不可判来源")
    add("")
    add("| 风险 | 说明 |")
    add("|---|---|")
    for limitation in report["limitations"]:
        head, sep, tail = limitation.partition("：")
        row = (head, tail) if sep else ("限制", limitation)
        add(f"| {_md_cell(row[0])} | {_md_cell(row[1])} |")
    add("")
    add("## 7. 复现")
    add("")
    add("```powershell")
    add(".venv\\Scripts\\python.exe -m tools.kill_list_dependency_audit")
    add(".venv\\Scripts\\python.exe -m pytest -q")
    add("```")
    add("")
    add("两次运行 JSON 应字节一致（本文件 sha256 见文首）；如不一致即为审计脚本引入不确定性，须先修脚本。")
    add("")
    return "\n".join(lines)


# ---------------------------------------------------------------- CLI


def write_outputs(report: dict[str, Any], json_out: Path, md_out: Path) -> tuple[str, str]:
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(payload, encoding="utf-8", newline="\n")
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    markdown = render_markdown(report, digest, json_out.name)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.write_text(markdown, encoding="utf-8", newline="\n")
    return digest, markdown


def main(argv: Sequence[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="T-171 Kill List 依赖审计（只读）")
    parser.add_argument("--json-out", default=str(DEFAULT_JSON))
    parser.add_argument("--md-out", default=str(DEFAULT_MD))
    parser.add_argument("--no-probes", action="store_true", help="跳过运行期探针（只做静态图，秒级）")
    parser.add_argument("--probe-timeout", type=int, default=300)
    parser.add_argument("--check", action="store_true", help="不写文件，只打印计数")
    args = parser.parse_args(argv)

    report = build_report(probe_runtime=not args.no_probes, timeout=args.probe_timeout)
    summary = report["summary"]
    print(f"Kill List 条目: {summary['items_total']}（模块 {summary['modules_total']}）")
    for name in CLASSES:
        print(f"  {name}: {summary['by_class'][name]}")
    print(f"一动就破 481/0: {len(summary['breaks_481_0'])}")
    invariants = summary["invariants"]
    print(
        f"批次不变量: {'通过' if invariants['ok'] else '失败'} "
        f"（检查 {invariants['checked_items']} 项，违规 {invariants['violation_count']}）"
    )
    baseline = report["baseline_481"]
    print(
        "481/0 基线: engine_audit cases={cases} fails={fails} exit={ea_exit}; "
        "relations_audit={verdict} exit={ra_exit}; ok={ok}".format(
            cases=baseline["engine_audit"].get("cases"),
            fails=baseline["engine_audit"].get("fails"),
            ea_exit=baseline["engine_audit"].get("exit_code"),
            verdict=baseline["relations_audit"].get("verdict"),
            ra_exit=baseline["relations_audit"].get("exit_code"),
            ok=baseline["ok"],
        )
    )
    for entry_id, size in summary["hard_entry_closure_sizes"].items():
        print(f"  入口 {entry_id}: 闭包 {size} 模块")

    if args.check:
        return 0
    digest, _markdown = write_outputs(report, Path(args.json_out), Path(args.md_out))
    print(f"written: {args.json_out}")
    print(f"written: {args.md_out}")
    print(f"json sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
