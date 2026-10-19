# T-102 · 在 `pyproject.toml` 建立 `slow` marker 机制

## Review Level: 2

> 定级理由：改动落在 `pyproject.toml` 保护区内，且与验收标准同文件。虽本卡
> 明确禁止触碰 `testpaths` / `addopts` / `--ignore`，但「同一个文件、同一个 section」
> 意味着手滑一次就可能改到门禁范围，因此需要中枢逐条核对 diff 后放行。
> 采用 `--strict-markers` 现有的注册方式，不改变任何用例的执行结果。

## Context（中枢只读勘察已确证，Worker 无需重复勘察）

**当前状态：** `pyproject.toml` 已有 `--strict-markers`（L29），已定义 8 个 marker
（L37-46），**但没有任何 `slow` marker**；全仓 `grep "mark\.slow"` 零命中。
因此本卡只需**注册机制**，不标注任何用例——`-m "not slow"` 立即等价于「全跑」，
这是零行为变更的安全前提。

**实测耗时分布（2026-10-19，本机）：**

| 目标 | 用例数 | 耗时 |
|---|---|---|
| 默认门禁 `python -m pytest -q` | 229 | **11.73s** |
| `tests/regression` | 34 | 402.31s |
| └ `test_g_iteration.py::test_g001_dry_run_idempotent` | 1 | **207.61s** |
| └ `test_g_iteration.py::test_g001_marriage_rule_misses_incremented` | 1 | 101.72s |
| └ `test_g_iteration.py::test_g001_marriage_rule_miss` | 1 | 92.52s |
| `tests/track_g_smoke` | 4 | 369.50s |
| └ `test_g_replay.py::test_dry_run_does_not_write` | 1 | **235.44s** |
| └ `test_g_replay.py::test_g001_diff_includes_marriage_rules` | 1 | 119.15s |
| `tests/v5` | 128 | 268.22s |
| `tests/ziping_career` | 35 | 79.36s |
| `tests/ren_timing` | 50 | 17.27s |
| `tests/v2` | 36 | 27.72s |

**关键观察：耗时不均匀地集中。** `tests/regression` 402s 里 **401.85s 来自 3 个用例**；
`tests/track_g_smoke` 369s 里 **369.3s 来自 3 个用例**。即 **6 个用例贡献了约 770s
（≈77%）的慢目录耗时**。按目录打 marker 会浪费颗粒度，按用例打才有意义。

## Objective

在 `pyproject.toml` 注册 `slow` marker，并确立标注准则，使后续可以：
`python -m pytest -q -m "not slow"` 跑快速子集、`python -m pytest -q` 跑全量。

**本卡不改 `testpaths`，不改任何测试文件，不给任何用例打 marker。**

## 指定改动

### 1. `markers` 段追加一项

```toml
"slow: 单用例耗时 > 10s 的集成/回放类测试；快速门禁用 -m \"not slow\" 排除",
```

（措辞可微调，但必须保持 `--strict-markers` 可识别。）

### 2. 新增标注准则（写进 `pyproject.toml` 注释）

```toml
# slow marker 阈值：单个测试函数耗时 > 10s。
# 按【用例】标注，不按【目录】标注——耗时高度集中在少数回放类用例上
# （2026-10-19 实测：6 个用例占慢目录 77% 耗时），按目录标注会误伤同目录的快用例。
# 标注由后续任务卡（v5 解禁卡）执行，本卡只注册机制。
```

## 标注方案（本卡只提出，不执行）

供下一张 v5 解禁卡与后续卡使用：

| 优先级 | 目标 | 预估节省 | 依据 |
|---|---|---|---|
| P0 | `tests/track_g_smoke/test_g_replay.py::*test_dry_run_does_not_write`（235s）、`*test_g001_diff_includes_marriage_rules`（119s） | ~354s | `--durations` |
| P0 | `tests/regression/test_g_iteration.py::*test_g001_dry_run_idempotent`（207s）、`*test_g001_marriage_rule_misses_incremented`（101s）、`*test_g001_marriage_rule_miss`（92s） | ~401s | `--durations` |
| P1 | `tests/v5` 中 >10s 的 5 个 `test_render_report_v6.py` / `test_report_reads_l7.py` 用例 | ~85s | `--durations` |
| 不标 | `tests/ziping_career`（单例最大 5s）、`tests/ren_timing`、`tests/v2` | 0 | 均低于阈值 |

## File Scope

**必须且只能是：**

```
pyproject.toml
```

（只允许改 `[tool.pytest.ini_options]` 下的 `markers` 列表与注释，**禁止**动
`testpaths`、`addopts`、`--ignore` 行。）

## Do NOT

- **禁止修改测试或验收脚本使其通过。**
- **禁止读取 File Scope 之外的文件**（`--durations` 输出由命令产生，不算读文件）。
- **禁止改动 `testpaths` / `addopts` / `--ignore`**——那是 T-103 的范围。
- **禁止给任何测试文件添加 `@pytest.mark.slow`**——本卡只注册机制。加了 marker 就等于
  改变门禁内容，会让 after 基线不可比。
- 禁止新增 `slow` 以外的 marker。
- 禁止执行 `git commit` / `checkout` / `stash` / `reset` / `clean`。

## Completion Criteria（可执行 + 期望退出码，全部需粘贴原始输出）

| # | 命令 | 期望 |
|---|---|---|
| 1 | `python -c "import tomllib,pathlib; d=tomllib.loads(pathlib.Path('pyproject.toml').read_text(encoding='utf-8')); print([m for m in d['tool']['pytest']['ini_options']['markers'] if m.startswith('slow')])"` | **exit 0**，输出非空且含 `slow:` |
| 2 | `python -m pytest --markers 2>&1 \| grep -c slow` | **exit 0**，计数 ≥ 1 |
| 3 | `python -m pytest -q -m "not slow"` | **exit 0**，`229 passed`，且耗时与 after 基线相当 |
| 4 | `python -m pytest -q` | **exit 0**，`229 passed`（零行为变更） |
| 5 | `git diff --stat` | 仅 `pyproject.toml`（及 `tasks/T-102/`） |
| 6 | `git diff pyproject.toml \| grep -E "^[-+].*(testpaths\|ignore=)"` | **空输出 + exit 1**（证明确实没动 testpaths/ignore） |

### before / after 耗时对照（必须写入 BRIEF.md）

在同一台机器、同一 `python -m pytest -q -p no:cacheprovider` 命令下测量：

| 指标 | before | after | 说明 |
|---|---|---|---|
| 默认门禁 `pytest -q` 耗时 | `____ s` | `____ s` | 必须**基本一致**（±10% 内属噪声）；显著变化即为回归 |
| 默认门禁用例数 | 229 | 229 | 必须不变 |
| `pytest -q -m "not slow"` 耗时 | — | `____ s` | 与默认门禁**相等**（因无用例被标注） |
| `python -V` / 机器 | `____` | `____` | 记录以便日后复现 |

> **判定标准**：本卡的正确结果是「耗时前后相同」。若 after 明显变慢，说明误加了
> marker 或改了 filter 配置，**视为失败**。

## Deliverables

- 改后的 `pyproject.toml`（仅 markers + 注释）
- `tasks/T-102/BRIEF.md`：含 before/after 计时对照表、`--durations` 原始输出、
  标注方案（P0/P1 清单）
- 更新 `tasks/T-102/STATUS.md`
