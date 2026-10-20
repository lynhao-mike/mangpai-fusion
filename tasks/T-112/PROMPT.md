# T-112 · 建立仓库健康基线：把「测试全绿但实际已坏」的盲区显性化

## Review Level: 2

> 只读诊断 + 新增一个可复用的检查脚本。不改产品代码、不改测试、不改门禁。

## Context

今天一天内发现了 **3 个「测试全绿但实际已坏」**的案例：

| 问题 | 为什么测试没抓到 |
|---|---|
| `cases/*/manifest.json` 被测试污染 | 12 个 tracked manifest 里有 2 个带着 pytest 临时路径，而 `.gitignore` 规则名字对不上实际文件 |
| `tests/r10` 5 个失败长期不可见 | `pyproject.toml` 的 `--ignore=tests/r10`，默认门禁不跑 |
| `as_of_contract_gate` 的 locator 可悬空 | 只检查「非空+非占位」，不检查文件和行号存在 |

**共同模式**：默认门禁 `python -m pytest -q` 是 229 passed 全绿，但它覆盖不到的地方已经坏了多处。

## Objective

写一个**一键体检脚本** `tools/repo_health_check.py`，把今天人工发现的所有盲区
变成自动检查项，并给出一份可读的体检报告。

## 必须包含的检查项（全部来自今天的真实发现）

### 检查 1：被 ignore 的测试目录到底还有多少失败？

- 读 `pyproject.toml` 的 `addopts` 找出所有 `--ignore=tests/xxx`
- 对每个被 ignore 的目录，跑 `pytest <dir> -q -o addopts=""`，记录失败数
- 输出：目录名 / 用例数 / 失败数 / 错误数

### 检查 2：testpaths 白名单外的测试文件

- 找出 `tests/**/test_*.py` 中不在 testpaths、也不被 ignore 的（那些"静默掉落"的）
- 跑一遍，记录结果
- 中枢已知数字：总 301 个测试文件，默认只收集 229 个用例，
  根级 62 个文件默认不跑但 61 个可跑且全绿

### 检查 3：git 跟踪的产物文件是否被污染

- 检查所有 tracked 的 `cases/**/manifest.json`，看是否含 `pytest-of-` 或绝对临时路径
- 检查所有 tracked 文件是否含本地绝对路径（`C:/Users/`）
- （中枢已知：035/036 已清洗，此检查应返回 0，作为回归保护）

### 检查 4：`.gitignore` 规则是否真的生效

- 对 `.gitignore` 里每条规则，检查它实际忽略了哪些 tracked 文件
- **重点**：`cases/**/findings/` 等规则写了几十年，但 tracked 文件名对不上
- 输出：写了但没生效的规则清单

### 检查 5：index-new.yaml 这类「游离文件」

- 扫描 `theory/*/index*.yaml`，比对它们与构建链产物 `index.yaml` 的重叠
- 若发现零重叠的独立文件，报警（中枢已知 `theory/ziping/index-new.yaml` 41 条零重叠）

### 检查 6：context window 里的 engine/ 死代码（不实现，只预留接口）

- 先不做具体分析，只在报告里输出 `engine/` 各子目录的 import 数与被 import 数
- 详细分析由 T-111 负责，这里只做数量统计

## 设计约束

1. **纯只读 + 只在 stdout 输出**，不写任何文件、不改任何状态
2. **不跑 pytest 全量**（太慢），只跑被 ignore 的小目录
3. 每个检查项独立，某项失败不影响其他项
4. 输出人类可读的 Markdown 报告到 stdout
5. 退出码：0 = 全绿，1 = 有警示项（供 CI 或人工判断）

## File Scope

**可新建**：`tools/repo_health_check.py`

**只读**：`pyproject.toml`、`.gitignore`、`theory/*/index*.yaml`、
`cases/**/manifest.json`、`tests/`（只统计文件名）

**可写**：`tasks/T-112/BRIEF.md`、`tasks/T-112/STATUS.md`

## Completion Criteria

| # | 命令 | 期望 |
|---|---|---|
| 1 | `python tools/repo_health_check.py` | exit 0 或 1，输出 6 项检查报告 |
| 2 | `python tools/repo_health_check.py 2>&1 \| head -60` | 报告可读，每项有明确数字 |
| 3 | `git status --porcelain` | 只含 `tools/repo_health_check.py` + `tasks/T-112/` |
| 4 | `python -m pytest -q` | **229 passed**（确认没破坏门禁） |

## Do NOT

- **禁止修改任何现有文件**（只允许新增 `repo_health_check.py`）
- **禁止修改 `pyproject.toml` / `.gitignore` / 任何测试**
- **禁止跑 pytest 全量**（只用 `-o addopts=""` 跑特定小目录）
- **禁止执行任何 git 写操作**
- 禁止读取 File Scope 之外的文件

## Deliverables

- `tools/repo_health_check.py`
- `tasks/T-112/BRIEF.md`：四字段 + **首次运行的完整体检报告**（这是关键产出）
- 更新 `tasks/T-112/STATUS.md`
