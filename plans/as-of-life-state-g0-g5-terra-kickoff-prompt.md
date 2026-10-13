# 原局—大运—流年—截止状态推理系统 · G0-G5 · terra 单次对话无人化执行提示词

> 用途：直接复制本文件"提示词正文"（第 1 节起）作为新对话的第一条消息发给 ChatGPT 5.6 Terra。
> 前提文档（terra 必须先读，不在本提示词中重复展开）：
> - [`as-of-life-state-reasoning-design-2026-07-18.md`](as-of-life-state-reasoning-design-2026-07-18.md) —— 业务语义唯一事实源
> - [`../reports/as-of-life-state-reasoning-audit-2026-07-26.md`](../reports/as-of-life-state-reasoning-audit-2026-07-26.md) —— 现状审计
> - [`as-of-life-state-g0-g5-execution-plan-for-terra.md`](as-of-life-state-g0-g5-execution-plan-for-terra.md) —— Gate 定义、风险登记、验证命令（本提示词的执行细节全部委托给这份文件，不重复展开）

---

## 提示词正文（从这里开始复制）

你是 terra，本次会话的任务是在**一个对话内**、以**无人值守自主推进**的方式，完整跑通"原局—大运—流年—截止状态推理系统"的 G0 到 G5 六个 Gate，产出一个通过隔离验证的事业+财富首个原型切片。你可以把整个任务拆成子任务顺序执行，但**除下方列出的四种情况外，不得在任何一步停下来等待用户确认**。完成 G5 后必须给出一次性最终汇总，不需要再等待用户逐条追问。

### 0. 强制先读（严格按顺序，不得跳过或只读摘要）

1. `AGENTS.md`
2. `plans/as-of-life-state-reasoning-design-2026-07-18.md` 全文 —— 这是唯一业务语义事实源，其中的冻结条款（§3 推理宪法、§6 事件影响模型、§7 双快照归并、§15 架构不变量）不得重新解释、简化或用"我认为更合理"的方案替换。
3. `reports/as-of-life-state-reasoning-audit-2026-07-26.md` 全文 —— 特别是 §2.2（既有模块字段缺口）、§2.5（G9 已知的 2 个 pre-existing 全仓失败测试）、§2.6（案例池预审结论）。
4. `plans/as-of-life-state-g0-g5-execution-plan-for-terra.md` 全文 —— 这是你的**唯一执行手册**：六个 Gate 的目标、产物、完成条件、验证命令、STOP 条件、风险登记表（§6）全部在这份文件里，本提示词不重复列出，你必须逐字执行其中每一条，不得自行简化字段清单或跳过任一 Gate 的完成条件。

只读参考（**全程禁止修改**）：
- `engine/yingqi/retrospective.py`
- `tests/ziping_career/`、`tests/ren_timing/`
- `engine/f09/`（架构模式参考，字段与命名不可复用）

### 1. 写集边界（贯穿全程，无例外）

只允许新增文件到：
- `engine/asof/`
- `tests/asof/`
- `plans/as-of-life-state-prototype-spec.md`（G0 产出）
- `reports/as-of-life-state-career-wealth-slice-g0-g5-verification.md`（持续追加，G5 收口）

**不允许修改任何现有文件**，包括但不限于 `engine/application/`、`engine/decision/`、`engine/domain/`、`engine/yingqi/`、任何 production loader、任何默认 registry、任何 `theory/*/index.yaml`。每个 Gate 收口时必须运行：

```
git status --short
git diff --name-only -- engine/application engine/decision engine/domain engine/yingqi engine/v5
```

第二条命令预期无输出。如有输出，立即停止（见下方 STOP 条件表），不得自行判断"影响可接受"或就地缩小 diff。

### 2. 自主推进协议

- 你可以在本对话内把 G0-G5 拆成任意数量的子任务，每个子任务开始前用一句话写清楚：任务目标 / 允许读取范围 / 允许写入文件清单 / 完成条件。
- Gate 之间**不需要**逐个请求用户批准；只有下表四种情况必须停止并等待用户输入，其余情况请持续自主推进直到 G5 完成：

| STOP 条件 | 判定标准 | 停止后应做什么 |
|---|---|---|
| 需修改设计文档冻结条款才能推进 | 设计条款与你打算实现的方式存在不可调和矛盾 | 写清楚冲突点、你考虑过的选项，等待用户裁决 |
| 需修改任何现有生产文件才能推进 | `git diff --name-only` 命中生产目录 | 立即停止，不要尝试"最小化"这次修改 |
| 全仓 `pytest -q` 出现第 3 个及以上失败 | 已知 2 个 pre-existing failures（`tests/evaluation/test_dataset.py::test_witness_trust_boundary_is_explicitly_documented` 与 `tests/evaluation/test_prospective_gate_workflow.py::test_handoff_names_first_legal_case_action_and_all_independent_holds`）不计入；第 3 个才算新增失败 | 定位失败是否由本次新增代码引入，报告给用户，不擅自修复非本计划范围的代码 |
| G5 完成，是否进入 G6 | G6 需要全新的、不可从本次继承的独立授权 | 在最终汇总中明确写"G5 已完成，是否启动 G6 需要您另行明确授权"，然后停止，不要自行开始 G6 |

- 每个 Gate 完成后，必须**落盘**（不是只在对话里口头总结）：把该 Gate 的产物、真实运行的验证命令、真实 passed/failed 计数、exit code 追加到 `reports/as-of-life-state-career-wealth-slice-g0-g5-verification.md`。格式参照 `reports/ziping-career-structure-slice-g0-g5-verification.md`。

### 3. 证据纪律（不可谈判）

- 禁止在没有真实运行验证命令的情况下声称任何 Gate "通过"。每次声称完成，必须附带该次运行的真实输出（passed 数、failed 数、exit code）。
- 禁止用代码审查、静态阅读或"逻辑上应该没问题"替代实际 pytest 运行。
- 每个 Gate 的具体验证命令、完成条件判据均已在 `plans/as-of-life-state-g0-g5-execution-plan-for-terra.md` 对应章节给出，直接照抄执行，不要自己发明替代命令。
- G3、G2 分别涉及"禁止加权求和"和"禁止双轨合并为单对象"两条架构级禁令（对应执行计划 §6 风险 R2、R7），必须在对应测试里写出**结构性断言**（例如断言 `VerifiedState` 与 `HypothesisState` 是不同的 dataclass 类型、断言实现代码源文件不包含加权求和模式的 AST 检查），不能只靠人工承诺"我没有加权"。

### 4. Gate 执行顺序（细节全部见执行计划文件，此处只是路线图）

按顺序执行，不得跳跃或并行交叉写入同一产物：

1. **G0** 规格与案例冻结 —— 直接采用执行计划 §3 已预审的推荐案例 `C-2026-028-乾-壬戌癸卯壬子乙巳`（除非你复核后发现其 `input.md` 排盘信息不足，此时切换到备选案例，但不得降低三条件标准）。产出 `plans/as-of-life-state-prototype-spec.md`。
2. **G1** 纯判别层（原局承载图 + 大运上下文）—— 注意 `retrospective.py` 的字段是自由文本，不能直接映射，必须建适配层。
3. **G2** 事件候选与证据门（根源分级 + 五种完成方式，限定在设计 §6.6 六个白名单组合内）。
4. **G3** 双轨状态机（⚠️ 全计划最高复杂度 Gate，单案例数据可能不足以触发全部路径，允许构造并标注为"合成"的边界测试）。
5. **G4** 财富跨域传播边 + 现实落点转译（预告：推荐案例大概率没有财富事件反馈，以合成传播边为主，这是预期结果不是缺陷）。
6. **G5** 历史回放验证 + 生产隔离 + 终验报告收口。

每个 Gate 的目标、产物清单、完成条件表、验证命令、STOP 条件、风险应对，一律以 `plans/as-of-life-state-g0-g5-execution-plan-for-terra.md` 第 4 节对应小节为准。

### 5. 明确不做（此对话内永久排除）

- 不做样本外后验校准、不做置信度 Beta 切换、不做生产 promotion；
- 不扩展到六大基本面全量，只做事业主域 + 财富传播域；
- 不修改任何 F01-F12 卡片契约或 `engine/f09/`；
- 不建立跨卡复用的统一五动作 dispatcher；
- 不做任何 GitHub 服务端操作（不 push、不建 PR/Issue/Release）。全程 **LOCAL ONLY / NOT PUSHED**。

### 6. 最终交付物（G5 完成后一次性给出，不要逐 Gate 打断用户）

1. `reports/as-of-life-state-career-wealth-slice-g0-g5-verification.md` 完整文件路径与结论行（预期 `staged_verified_production_unchanged`）；
2. 六个 Gate 的真实验证命令与 passed/failed/exit code 汇总表；
3. `git status --short` 与生产目录 `git diff --name-only` 的最终结果（生产目录应为空）；
4. 新增文件完整清单；
5. 明确声明：本次为 LOCAL ONLY / NOT PUSHED；
6. 明确声明：G5 完成不代表 G6 已获批准，是否启动 G6 需要用户另行明确授权。

现在开始：先完成 §0 的强制先读，然后从 G0 启动，按 §2 的自主推进协议持续执行直到 G5 完成或触发 §2 表中的 STOP 条件。

---

## 提示词正文结束（以上为复制边界）

## 使用说明

- 本提示词假定 terra 运行环境的工作目录为仓库根目录 `f:/多流派新思路`，且具备读写本地文件与运行 `pytest`/`git` 命令的权限。
- 本提示词不重复展开 Gate 内部细节，是为了防止提示词与执行计划文件出现"两份不同步的真相源"；如后续需要调整某个 Gate 的完成条件，只需修改 `plans/as-of-life-state-g0-g5-execution-plan-for-terra.md`，本提示词无需同步编辑。
- 若 terra 在实际运行中发现执行计划文件与设计文档之间存在它未曾发现的新冲突，应按本提示词 §2 的 STOP 表处理，不应自行仲裁。
