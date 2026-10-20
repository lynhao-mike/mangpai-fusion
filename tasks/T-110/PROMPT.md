# T-110 · 修 `as_of_contract_gate` 的 locator 校验缺口

## Review Level: 3

> 定级理由：改动的是**冻结门禁**本身，属于验收标准。改松会放行悬空证据，
> 改严会阻断已有冻结 case。必须独立评审，不得自测自过。

## Context（中枢已核实）

**核心缺陷：**
`tools/as_of_contract_gate.py:259` 的 `check_theory_evidence` 只检查：
- `theory_evidence` 非空
- 文本不是占位符（`TODO` / `待补充` / `暂无`，见 `_PLACEHOLDER_THEORY_EVIDENCE` :47）

**它从不验证 locator 指向的文件是否存在、行号是否越界。**

**真实后果（已发生）：**
`theory/ziping/index-new.yaml` 被 5 个冻结 case 的 `asof-blind-freeze.json` 引用。
如果该文件被删，`pytest` 依然全绿，但审计溯源静默断掉。

**locator 真实结构（实测）：**
```json
{
  "school": "ziping",
  "rule_id": "ZP-PROD-20260606-004",
  "status": "active",
  "locator": "theory/ziping/index-new.yaml:794-831",
  "summary": "...",
  "application": "..."
}
```
`theory_evidence` 是 `list[dict]`，locator 是字符串，格式 `path:start-end` 或 `path:line`。

## Objective

1. 给 `check_theory_evidence` 增加 locator 可达性校验（文件存在 + 行号在范围内）
2. **先体检存量**：扫描所有 `cases/**/asof-blind-freeze.json`，统计有多少 locator 失效
3. 按存量结果决定：报警模式 还是 阻断模式

## Steps

### Step 0: 读现有实现

- [ ] `check_theory_evidence` 全文（:259-293）
- [ ] `_evidence_texts`（:246-258）
- [ ] `TheoryEvidenceFinding` 数据类（:110-119）
- [ ] `run_contract_gate`（:294+）看它怎么被调用、`blocks_freeze` 怎么用

### Step 1: 存量体检（先做，不改代码）

写一个只读体检脚本，扫描所有 `cases/**/asof-blind-freeze.json`：
- 提取所有 locator
- 检查文件是否存在、行号是否越界
- 统计：总 locator 数 / 文件缺失数 / 行号越界数 / 健康数
- **列出失效的具体条目**（case id + rule_id + locator）

### Step 2: 按存量结果定实现策略

**如果存量 0 失败**：直接实现阻断式校验。

**如果存量有失败**：实现为**报警优先**——新增字段
`locator_findings` 或类似，默认 `blocks_freeze` 不因 locator 翻转，
只在报告里列出。**不要修那些失败条目**，交中枢决策。

### Step 3: 实施

- [ ] 新增校验逻辑，保持 `TheoryEvidenceFinding` 现有字段不删只加
- [ ] 保证 `_evidence_texts` 行为不变
- [ ] 新增一个测试文件 `tests/tools/test_locator_reachability.py`

## File Scope

**可改**：
- `tools/as_of_contract_gate.py`
- `tasks/T-110/BRIEF.md`
- `tasks/T-110/STATUS.md`

**可新建**：
- `tests/tools/test_locator_reachability.py`

**只读参考**：
- `cases/**/asof-blind-freeze.json`（体检对象，**禁止修改**）
- `theory/`（**禁止修改**）

## Completion Criteria（全部实跑并粘贴原始输出）

| # | 命令 | 期望 |
|---|---|---|
| 1 | 体检脚本 | 输出总 locator 数 / 失效数，**数字写进 BRIEF.md** |
| 2 | `python -m pytest -q` | **exit 0**，229 passed |
| 3 | `python -m pytest tests/tools -q -o addopts=""` | exit 0 |
| 4 | `python -m pytest tests/tools/test_locator_reachability.py -q -o addopts=""` | exit 0 |
| 5 | `git status --porcelain` | 只含上述 3 个路径的改动，`cases/` 与 `theory/` 零改动 |

## Do NOT

- **禁止修改任何 `cases/` 下文件**（那会篡改冻结证据）
- **禁止修改 `theory/` 下任何文件**
- **禁止让 locator 校验默认阻断冻结**（除非 Step 1 实测存量 0 失败）
- **禁止删除或重命名 `TheoryEvidenceFinding` 现有字段**
- **禁止执行 `git commit` / `checkout` / `stash` / `reset` / `clean`**
- **禁止用 `git checkout` 恢复任何东西**
- 禁止读取 File Scope 之外的文件

## Deliverables

- 改后的 `tools/as_of_contract_gate.py`
- 新增 `tests/tools/test_locator_reachability.py`
- `tasks/T-110/BRIEF.md`：四字段 + **存量体检数字**（这是本任务最重要的产出）
- 更新 `tasks/T-110/STATUS.md`
