# 原局—大运—流年—截止状态推理系统 · G6 样本外回放验证 · terra 单次对话无人化执行提示词

> 用途：直接复制本文件"提示词正文"（第 1 节起）作为新对话的第一条消息发给 ChatGPT 5.6 Terra。
>
> 背景：G0-G5 事业+财富首个原型（案例 `C-2026-028-乾-壬戌癸卯壬子乙巳`）已完成 evidence-bounded freeze，结论 `staged_verified_production_unchanged`，证据见 [`../reports/as-of-life-state-career-wealth-slice-g0-g5-verification.md`](../reports/as-of-life-state-career-wealth-slice-g0-g5-verification.md)。该报告明确写明："G6 未进入。G5 完成不代表 G6 获准；需独立冻结样本后验和用户另行明确审批。"
>
> **本文件即为该独立授权。** 用户在此正式授权启动 G6：用两个此前只做过准入预审、从未实际跑过管线的备选案例，对已冻结的 G0-G5 实现做**样本外回放验证**——检验同一套零业务扩展的代码能否在不同命盘上产出合理结果，而不是继续扩展新领域或新裁决规则。
>
> 前提文档（terra 必须先读，不在本提示词中重复展开）：
> - [`as-of-life-state-reasoning-design-2026-07-18.md`](as-of-life-state-reasoning-design-2026-07-18.md) —— 业务语义唯一事实源，冻结条款不可重开
> - [`../reports/as-of-life-state-reasoning-audit-2026-07-26.md`](../reports/as-of-life-state-reasoning-audit-2026-07-26.md) §2.6 —— 两个备选案例的预审结论
> - [`as-of-life-state-prototype-spec.md`](as-of-life-state-prototype-spec.md) —— G0 冻结规格，只读参考，不得修改
> - [`../reports/as-of-life-state-career-wealth-slice-g0-g5-verification.md`](../reports/as-of-life-state-career-wealth-slice-g0-g5-verification.md) —— G0-G5 证据台账，只读参考，不得修改
> - `engine/asof/*.py`、`tests/asof/*.py` 现有全部文件 —— 已冻结实现，本轮验证对象，默认只读

---

## 提示词正文（从这里开始复制）

你是 terra，本次会话的任务是在**一个对话内**、以**无人值守自主推进**的方式完成"原局—大运—流年—截止状态推理系统"的 **G6 样本外回放验证**：用两个此前只经过准入预审、从未真正跑过管线的备选案例（`C-2026-024-坤-己巳壬申辛亥壬辰`、`C-2026-022-坤-癸亥庚申戊寅己未`），分别驱动已冻结的 `engine/asof/` 实现完成历史截止点回放，验证该实现在案例 `C-2026-028` 之外是否仍然成立。你可以把整个任务拆成子任务顺序执行，但**除下方 STOP 条件表列出的情况外，不得在任何一步停下来等待用户确认**。完成后必须给出一次性最终汇总。

### 0. 强制先读（严格按顺序，不得跳过或只读摘要）

1. `AGENTS.md`
2. `plans/as-of-life-state-reasoning-design-2026-07-18.md` 全文 —— 唯一业务语义事实源；本轮不得重新解释或修改任何冻结条款。
3. `reports/as-of-life-state-reasoning-audit-2026-07-26.md` §2.5（2 个 pre-existing 全仓失败）、§2.6（两个备选案例的预审结论表）。
4. `plans/as-of-life-state-prototype-spec.md` 全文 —— G0 冻结的字段清单、命名裁定与白名单，本轮只读，不得修改，也不得为新案例新增字段或放宽白名单。
5. `reports/as-of-life-state-career-wealth-slice-g0-g5-verification.md` 全文 —— 已冻结的 G0-G5 证据台账，只读，不得修改或追加。
6. `engine/asof/` 下全部现有文件（`natal_capacity.py`、`daiyun_context.py`、`event_candidate.py`、`structural_track.py`、`reality_track.py`、`state_ledger.py`、`wealth_propagation.py`、`reality_translation.py`）——理解现有公共接口签名与不变量，本轮默认只读。
7. `tests/asof/` 下全部现有测试文件——作为本轮新测试的写法范本，本轮默认只读，不得修改其内容。
8. `cases/C-2026-024-坤-己巳壬申辛亥壬辰/input.md`、`feedback.md`、`statement_index.json`。
9. `cases/C-2026-022-坤-癸亥庚申戊寅己未/input.md`、`feedback.md`、`statement_index.json`。

### 1. 写集边界（贯穿全程，无例外）

只允许新增文件：
- `tests/asof/test_case_2024_out_of_sample.py`
- `tests/asof/test_case_2022_out_of_sample.py`
- `plans/as-of-life-state-g6-out-of-sample-case-spec.md`（记录两个新案例的字段裁定与截止点冻结，格式参照 `as-of-life-state-prototype-spec.md` 但是全新独立文件）
- `reports/as-of-life-state-g6-out-of-sample-validation-report.md`（G6 收口报告，全新独立文件）

**禁止修改的文件（无例外）：**
- `engine/asof/` 下任何现有文件——本轮是验证已冻结实现的泛化能力，不是扩展实现。若新案例暴露了必须修改 `engine/asof/` 才能通过的问题，视为触发 STOP（见下表），不得自行修改公共接口、裁决语义或白名单。
- `tests/asof/` 下 G0-G5 已有的全部测试文件——保持只读，防止破坏已冻结证据。
- `plans/as-of-life-state-prototype-spec.md`、`reports/as-of-life-state-career-wealth-slice-g0-g5-verification.md`——已冻结台账，只追加新文件，不改旧文件。
- 任何现有生产文件，包括但不限于 `engine/application/`、`engine/decision/`、`engine/domain/`、`engine/yingqi/`、`engine/v5/`、任何 production loader、任何默认 registry、任何 `theory/*/index.yaml`、任何 `cases/` 下已有文件。

每个 Gate 收口时必须运行：

```
git status --short
git diff --name-only -- engine/application engine/decision engine/domain engine/yingqi engine/v5 engine/asof
```

第二条命令预期无输出（注意本轮把 `engine/asof` 也纳入了零 diff 检查，因为本轮对它是只读）。如有输出，立即停止，不得自行判断"影响可接受"或就地缩小 diff。

### 2. 自主推进协议

你可以在本对话内把 G6 拆成任意数量的子任务，每个子任务开始前用一句话写清楚：任务目标 / 允许读取范围 / 允许写入文件清单 / 完成条件。Gate 之间**不需要**逐个请求用户批准；只有下表情况必须停止并等待用户输入：

| STOP 条件 | 判定标准 | 停止后应做什么 |
|---|---|---|
| 新案例暴露必须修改 `engine/asof/` 才能通过的问题 | 现有公共接口签名、裁决语义或白名单组合无法覆盖新案例的合法业务场景 | 写清楚具体缺口（哪个函数/哪个裁决点/为什么现有白名单不够），列出可能的修复方案，等待用户裁决；不得自行扩大白名单或修改裁决语义 |
| 需修改任何现有生产文件或 `engine/asof/`/`tests/asof/` 已有文件 | `git diff --name-only` 命中禁止清单，或发现必须编辑既有文件才能推进 | 立即停止，不要尝试"最小化"这次修改 |
| 两个新案例的 `input.md` 排盘信息不足以构造原局承载图 | 缺少四柱、藏干、十神或起运信息中的任一项 | 报告缺口，不得用假设数据填补；如仅一个案例不足，可继续用另一个案例完成 G6，并在最终汇总中明确标注该案例"跳过，证据不足" |
| 全仓 `pytest -q` 出现第 3 个及以上失败 | 已知 2 个 pre-existing failures（`tests/evaluation/test_dataset.py::test_witness_trust_boundary_is_explicitly_documented` 与 `tests/evaluation/test_prospective_gate_workflow.py::test_handoff_names_first_legal_case_action_and_all_independent_holds`）不计入；第 3 个才算新增失败 | 定位失败是否由本次新增测试引入，报告给用户，不擅自修复非本计划范围的代码 |
| G6 完成，是否进入 G7（新增第三个案例、样本外统计汇总、或申请生产 promotion） | 需要全新的、不可从本次继承的独立授权 | 在最终汇总中明确写"G6 已完成，是否启动 G7 需要您另行明确授权"，然后停止 |

### 3. 证据纪律（不可谈判）

- 禁止在没有真实运行验证命令的情况下声称任何 Gate "通过"。每次声称完成，必须附带该次运行的真实输出（passed 数、failed 数、exit code）。
- 禁止用代码审查、静态阅读或"逻辑上应该没问题"替代实际 pytest 运行。
- 两个案例的历史截止点、已核验事业事件年份必须来自你实际读取的该案例 `feedback.md`，不得凭审计报告 §2.6 的摘要字样直接编造具体日期；审计表只是预审线索，实际截止点冻结必须以你亲自读到的原文为准。
- 若某案例没有财富反馈（大概率两个案例都没有），复用 G4 已冻结的两条合成传播边（升迁→稳定收入能力提高、创业→收入结构变化与资产风险暴露）进行"无匹配显式边不传播"或"事件类型不匹配不传播"的弃权路径断言，不得为这两个新案例发明新的传播边。

### 4. Gate 执行顺序

#### G6-A · 案例 C-2026-024 样本外回放

1. 读取 `cases/C-2026-024-坤-己巳壬申辛亥壬辰/input.md`、`feedback.md`，核实排盘事实完整性与已核验事业事件的准确年份。
2. 在 `plans/as-of-life-state-g6-out-of-sample-case-spec.md` 中冻结：该案例的原局承载图关键节点、大运阶段裁定、至少三个历史截止点（覆盖事件前/事件间/事件后，具体年份以你读到的 `feedback.md` 原文为准）。
3. 新建 `tests/asof/test_case_2024_out_of_sample.py`：
   - 用现有 `engine.asof.natal_capacity`、`engine.asof.daiyun_context` 构造函数（不修改这两个模块本身）构造该案例的 `NatalCapacityGraph` 与 `DaiyunStage` 测试夹具；
   - 用现有 `engine.asof.event_candidate.evaluate_event_candidate` 构造该案例已核验事业事件的候选，走双证据门；
   - 用现有 `engine.asof.state_ledger.build_verified_state` 在冻结的三个截止点回放，断言：不同截止点产生不同 `VerifiedState`、截止日后事件不泄漏、事实与假设物理分离（复用 G3/G5 已验证的断言模式，不需要重新发明新的架构级断言）；
   - 若该案例出现假设性财富传播场景，复用 G4 已冻结的两条合成边验证弃权路径。
4. 运行：
   ```
   python -m pytest tests/asof/test_case_2024_out_of_sample.py -q
   ```
   记录真实 passed/failed 计数与 exit code。

#### G6-B · 案例 C-2026-022 样本外回放

与 G6-A 相同流程，作用于 `cases/C-2026-022-坤-癸亥庚申戊寅己未/`，产出 `tests/asof/test_case_2022_out_of_sample.py`，并在同一个 `plans/as-of-life-state-g6-out-of-sample-case-spec.md` 中追加该案例的裁定（同一文件内两个案例分节记录，不新建第二个 spec 文件）。

运行：
```
python -m pytest tests/asof/test_case_2022_out_of_sample.py -q
```

#### G6-C · 汇总收口

1. 运行完整 as-of 套件确认无回归：
   ```
   python -m pytest tests/asof -q
   ```
2. 重跑 G5 已冻结的生产隔离测试，确认新增测试文件未引入任何新导入违规：
   ```
   python -m pytest tests/asof/test_production_isolation.py -q
   ```
3. 生产目录零 diff 检查：
   ```
   git diff --name-only -- engine/application engine/decision engine/domain engine/yingqi engine/v5 engine/asof
   git status --short
   ```
4. 全仓 sanity：
   ```
   python -m pytest -q
   ```
   确认失败数仍为 2 个 pre-existing（无第 3 个）。
5. 新建 `reports/as-of-life-state-g6-out-of-sample-validation-report.md`，记录两个案例各自的真实验证证据、任何发现的实现边界问题（即使未构成 STOP，也要如实记录，例如某个断言只能弱化验证而非强验证的原因）、生产目录零 diff 证据、全仓 sanity 结果，结论行使用 `staged_out_of_sample_validated_production_unchanged`（若两个案例都验证通过）或如实标注部分案例跳过。

### 5. 明确不做（此对话内永久排除）

- 不扩展 `engine/asof/` 的字段、裁决语义或白名单组合，只验证既有实现；
- 不做统计学习、命中率汇总或置信度校准；
- 不新增第三个案例；
- 不做生产 promotion、不接入任何生产 loader/pipeline/registry；
- 不修改任何 F01-F12 卡片契约或 `engine/f09/`；
- 不做任何 GitHub 服务端操作（不 push、不建 PR/Issue/Release）。全程 **LOCAL ONLY / NOT PUSHED**。

### 6. 最终交付物（G6 完成后一次性给出）

1. `reports/as-of-life-state-g6-out-of-sample-validation-report.md` 完整路径与结论行；
2. G6-A、G6-B、G6-C 的真实验证命令与 passed/failed/exit code 汇总表；
3. `git status --short` 与生产目录（含 `engine/asof`）`git diff --name-only` 的最终结果（应为空）；
4. 新增文件完整清单；
5. 明确声明：本次为 LOCAL ONLY / NOT PUSHED；
6. 明确声明：G6 完成不代表 G7（新增案例/统计汇总/生产 promotion）已获批准，是否启动 G7 需要用户另行明确授权。

现在开始：先完成 §0 的强制先读，然后从 G6-A 启动，按 §2 的自主推进协议持续执行直到 G6-C 完成或触发 §2 表中的 STOP 条件。

---

## 提示词正文结束（以上为复制边界）

## 使用说明

- 本提示词假定 terra 运行环境的工作目录为仓库根目录 `f:/多流派新思路`，且具备读写本地文件与运行 `pytest`/`git` 命令的权限。
- 本轮的核心目的是**验证泛化能力**，不是**扩展业务能力**：如果 terra 发现两个新案例都需要修改 `engine/asof/` 才能通过，这本身就是一个有价值的发现（说明 G0-G5 的字段/裁决设计可能对案例 `C-2026-028` 过拟合），应该按 STOP 表停止并如实报告，而不是自行"顺手"扩大实现范围。
- 若两个案例都验证通过且零回归，这只证明该实现在三个案例上泛化良好，仍不构成生产 promotion 的充分证据；G7（更大样本、统计汇总或生产接入）需要用户另行明确审批。
