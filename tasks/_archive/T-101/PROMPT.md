# T-101 · 修 `tests/test_preflight_prospective.py` 的编码缺陷

## Review Level: 2

> 定级理由：改动落在 `tests/` 保护区内，且触碰的是一条**正在使用的断言路径**。
> 虽然只加了一个环境变量，但它决定了该用例从此在 GBK/UTF-8 两种环境下是否都成立，
> 属于「常规改动」，需中枢逐条核对断言未被松动后放行。不升至 3 是因为：
> File Scope 单文件、不触碰验收标准本身、不改变任何产品行为。

## Context（中枢只读勘察已确证，Worker 无需重复勘察）

默认门禁 `python -m pytest -q` 收 229 用例全绿，但该门禁的 `testpaths` 是白名单，
`tests/test_preflight_prospective.py` 不在其中。T-103 扩覆盖时该文件会进入门禁，
目前它是唯一红灯。

**已确证的事实（2026-10-19）：**

| 观测 | 命令 | 结果 |
|---|---|---|
| 控制台编码 | `python -c "import sys;print(sys.stdout.encoding)"` | `gbk` |
| 目标文件单跑 | `python -m pytest tests/test_preflight_prospective.py -q` | `rc=1`，1 failed |
| 失败形态 | — | `TypeError: argument of type 'NoneType' is not a container`，伴随 `PytestUnhandledThreadExceptionWarning` 中的 `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc0` |
| 子进程直跑 | `python -m tools.preflight "cases/P-GO-2026-001-坤-壬戌己酉乙卯丁亥/input.md"` | `rc=0`，但 stdout 为 `[OK] preflight passed: P-GO-2026-001-��-���缺����î����`（GBK 乱码） |
| 加环境变量后 | `PYTHONIOENCODING=utf-8 python -m pytest tests/test_preflight_prospective.py -q` | **`rc=0`，1 passed** |

**因果链**：`tools/preflight.py` 正常返回 0 且确实输出了正确文本，但输出经 Windows
GBK 控制台编码；测试 L16 以 `text=True, encoding="utf-8"` 强制解码 → 抛
`UnicodeDecodeError` → 读线程崩溃 → `result.stdout` 变成 `None` → L20 的 `in` 抛出
`TypeError`。**这是测试的编码契约与环境不匹配，不是被测代码的错误。**

## Objective

在**只改测试文件**的前提下消除该失败，使该用例在 GBK 与 UTF-8 环境都能通过。

## 指定方案（必须采用方案 a，不接受方案 b）

在 `subprocess.run(...)` 调用中补上子进程编码环境：

```python
env={**os.environ, "PYTHONIOENCODING": "utf-8"}
```

（需相应 `import os`。）

## 为何不改 `tools/preflight.py`（必须写进本次提交说明 / BRIEF.md）

1. **影响面**：`tools/preflight.py` 是公共 CLI，被测试、脚本、人工调用共用。为其
   强制 UTF-8 标准输出会改变所有调用方的可见行为（管道、重定向、`case_id` 校验
   输出等），属于验收范围之外的业务改动。
2. **定位错误**：preflight 在 GBK 控制台下 `rc=0` 且输出语义正确，代码无缺陷；
   缺陷在调用方假设了"子进程必以 UTF-8 输出"却没设置该环境。修复应落在提出假设
   的地方。
3. **最小改动原则**：方案 (b) 是一处业务代码改动影响 N 个调用方；方案 (a) 是一处
   测试改动影响 0 个调用方。
4. **保护性**：`tests/` 内修复不触碰产品行为，回归风险为零。

## File Scope

**必须且只能是：**

```
tests/test_preflight_prospective.py
```

以下文件**只读**（可用于理解，禁止修改）：`tools/preflight.py`。

## Do NOT

- **禁止修改测试或验收脚本使其通过**（含：放宽断言、删除断言、`pytest.skip`、
  `xfail`、`try/except` 吞掉异常）。本任务改的是**环境设置**，断言 `rc==0` 与
  `"P-GO-2026-001-坤-壬戌己酉乙卯丁亥" in result.stdout` 必须**原样保留**。
- **禁止读取 File Scope 之外的文件**（除上面标注的两个只读文件）。
- 禁止修改 `tools/preflight.py`、`pyproject.toml`、`conftest.py`。
- 禁止执行 `git commit` / `checkout` / `stash` / `reset` / `clean`。
- 禁止扩大范围去修其他测试的编码问题（另立任务卡）。

## Completion Criteria（可执行 + 期望退出码，全部需粘贴原始输出）

| # | 命令 | 期望 |
|---|---|---|
| 1 | `python -m pytest tests/test_preflight_prospective.py -q -o addopts="-ra --tb=short"` | **exit 0**，`1 passed` |
| 2 | `PYTHONIOENCODING=utf-8 python -m pytest tests/test_preflight_prospective.py -q` | **exit 0**，`1 passed`（UTF-8 环境不回归） |
| 3 | `python -m pytest -q` | **exit 0**，`229 passed`（默认门禁不回归） |
| 4 | `git diff --stat -- tests/test_preflight_prospective.py` | 仅 1 文件改动 |
| 5 | `git status --porcelain` | 除该文件（及 `tasks/T-101/`）外无其他改动 |
| 6 | 断言完整性人工核对 | `rc==0` 断言与 `in result.stdout` 断言**逐字未变** |

## Deliverables

- 改后的 `tests/test_preflight_prospective.py`
- `tasks/T-101/BRIEF.md`：包含失败复现、4 条"为何不改 preflight.py"、6 项验收原始输出
- 更新 `tasks/T-101/STATUS.md`（状态 + Execution Log 追加一行）
