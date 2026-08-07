# 原局—大运—流年—截止状态推理系统 · G7 更大规模样本外验证 · terra 单次对话无人化执行提示词

> 用途：直接复制本文件"提示词正文"（第 1 节起）作为新对话的第一条消息发给 ChatGPT 5.6 Terra。
>
> 背景：G6 样本外回放验证已完成，结论见 [`../reports/as-of-life-state-g6-out-of-sample-validation-report.md`](../reports/as-of-life-state-g6-out-of-sample-validation-report.md)——`C-2026-024` 一案通过、`C-2026-022` 因缺少显式十神字段被跳过，全仓零 diff、既有 2 个 pre-existing 失败未增加。该报告明确写明："G6 完成不代表 G7 已获批准，需另行明确授权。"
>
> **本文件即为该独立授权。** 用户已明确选择方向 A：以更大规模的新样本对已冻结的 `engine/asof/` 实现继续做样本外回放验证，**不做统计学习、不做命中率汇总、不做生产接入**，方法与 STOP 纪律与 G6 完全一致，只是把案例数从 2 提高到 3，覆盖不同性别、不同十神完整度、不同事件密度的组合。
>
> 前提文档（terra 必须先读，不在本提示词中重复展开）：
> - [`as-of-life-state-reasoning-design-2026-07-18.md`](as-of-life-state-reasoning-design-2026-07-18.md) —— 业务语义唯一事实源，冻结条款不可重开
> - [`../reports/as-of-life-state-career-wealth-slice-g0-g5-verification.md`](../reports/as-of-life-state-career-wealth-slice-g0-g5-verification.md) —— G0-G5 证据台账，只读参考
> - [`as-of-life-state-g6-out-of-sample-case-spec.md`](as-of-life-state-g6-out-of-sample-case-spec.md) —— G6 已冻结的两案例裁定，只读参考，本轮不得修改
> - [`../reports/as-of-life-state-g6-out-of-sample-validation-report.md`](../reports/as-of-life-state-g6-out-of-sample-validation-report.md) —— G6 收口报告，只读参考，本轮不得修改
> - `engine/asof/*.py`、`tests/asof/*.py` 现有全部文件（含 G6 新增的 `test_case_2024_out_of_sample.py`、`test_case_2022_out_of_sample.py`）—— 已冻结实现与既有测试范本，本轮默认只读

---

## 提示词正文（从这里开始复制）

你是 terra，本次会话的任务是在**一个对话内**、以**无人值守自主推进**的方式完成"原局—大运—流年—截止状态推理系统"的 **G7 更大规模样本外验证**：用三个全新案例（`C-2026-016-坤-甲子丙子丙戌戊子`、`C-2026-026-坤-癸未甲寅壬戌丙午`、`C-2026-027-乾-丁卯壬寅甲午乙丑`）分别驱动已冻结的 `engine/asof/` 实现完成历史截止点回放，检验该实现在更多命盘结构和事件密度组合下是否仍然成立。你可以把整个任务拆成子任务顺序执行，但**除下方 STOP 条件表列出的情况外，不得在任何一步停下来等待用户确认**。完成后必须给出一次性最终汇总。

### 0. 强制先读（严格按顺序，不得跳过或只读摘要）

1. `AGENTS.md`
2. `plans/as-of-life-state-reasoning-design-2026-07-18.md` 全文 —— 唯一业务语义事实源；本轮不得重新解释或修改任何冻结条款。
3. `plans/as-of-life-state-prototype-spec.md` 全文 —— G0 冻结的字段清单、命名裁定与白名单，本轮只读，不得修改，也不得为新案例新增字段或放宽白名单。
4. `reports/as-of-life-state-career-wealth-slice-g0-g5-verification.md` 全文 —— G0-G5 证据台账，只读。
5. `plans/as-of-life-state-g6-out-of-sample-case-spec.md` 全文 —— G6 已冻结的两案例裁定格式范本，只读，不得修改。
6. `reports/as-of-life-state-g6-out-of-sample-validation-report.md` 全文 —— G6 收口报告，只读，不得修改。
7. `engine/asof/` 下全部现有文件（`natal_capacity.py`、`daiyun_context.py`、`event_candidate.py`、`structural_track.py`、`reality_track.py`、`state_ledger.py`、`wealth_propagation.py`、`reality_translation.py`）——理解现有公共接口签名与不变量，本轮默认只读。
8. `tests/asof/` 下全部现有测试文件，包括 G6 新增的 `test_case_2024_out_of_sample.py`、`test_case_2022_out_of_sample.py` —— 作为本轮新测试的写法范本，本轮默认只读，不得修改其内容。
9. `cases/C-2026-016-坤-甲子丙子丙戌戊子/input.md`、`feedback.md`、`statement_index.json`。
10. `cases/C-2026-026-坤-癸未甲寅壬戌丙午/input.md`、`feedback.md`、`statement_index.json`。
11. `cases/C-2026-027-乾-丁卯壬寅甲午乙丑/input.md`、`feedback.md`、`statement_index.json`。

### 1. 三个候选案例的已知情况（仅供预判，最终准入裁决必须以你亲自读到的原文为准）

| 案例 | 已知优势 | 已知风险点 |
|---|---|---|
| `C-2026-016-坤-甲子丙子丙戌戊子` | 反馈时间线极密集且明确：2009 结婚入职会计、2011 产子、2012 换行业、2018 考编未过、2019 录取劳务派遣、2020 上岸编制 | 藏干在 YAML 块中只有 `主气/中气/余气+力量`，未单独标注十神子字段；四柱十神只出现在人读表格的"主星"列，不在结构化 YAML 块内。需要你自行核实这是否满足"十神"充分性，若判定不足，按 G6 先例跳过，不得自行推算补齐 |
| `C-2026-026-坤-癸未甲寅壬戌丙午` | 四柱、藏干十神、大运十神字段均完整（格式与 `C-2026-024` 一致）；反馈含 2020 年入职乡镇中学在编教师、2025-2026 两笔小额财物损失（可用于财富弃权路径断言，不构成传播事件） | 事业事件本身较单一（一次入编），历史截止点区分度不如 016 或 024 |
| `C-2026-027-乾-丁卯壬寅甲午乙丑` | 四柱、藏干十神、大运十神字段均完整；反馈含"最近 7 年左右开始从事机箱厂设计"（职业方向变化）、"2021 年左右卖掉婚房"（资产处置，可能触发财富路径） | 职业变化窗口是相对时间"最近 7 年左右"，没有绝对年份，需要你自行判断能否合理换算为窗口，或该断语因证据不够精确而不适合构造事件候选（若不适合，只用其余可回放的事实，或整案跳过） |

### 2. 写集边界（贯穿全程，无例外）

只允许新增文件：
- `tests/asof/test_case_2016_out_of_sample.py`
- `tests/asof/test_case_2026_out_of_sample.py`
- `tests/asof/test_case_2027_out_of_sample.py`
- `plans/as-of-life-state-g7-larger-sample-case-spec.md`（记录三个新案例的字段裁定与截止点冻结，格式参照 `as-of-life-state-g6-out-of-sample-case-spec.md` 但是全新独立文件）
- `reports/as-of-life-state-g7-larger-sample-validation-report.md`（G7 收口报告，全新独立文件）

**禁止修改的文件（无例外）：**
- `engine/asof/` 下任何现有文件——本轮是验证已冻结实现的泛化能力，不是扩展实现。若新案例暴露了必须修改 `engine/asof/` 才能通过的问题，视为触发 STOP（见下表），不得自行修改公共接口、裁决语义或白名单。
- `tests/asof/` 下 G0-G6 已有的全部测试文件（包括 G6 新增的两个）——保持只读，防止破坏已冻结证据。
- `plans/as-of-life-state-prototype-spec.md`、`plans/as-of-life-state-g6-out-of-sample-case-spec.md`、`reports/as-of-life-state-career-wealth-slice-g0-g5-verification.md`、`reports/as-of-life-state-g6-out-of-sample-validation-report.md`——已冻结台账，只追加新文件，不改旧文件。
- 任何现有生产文件，包括但不限于 `engine/application/`、`engine/decision/`、`engine/domain/`、`engine/yingqi/`、`engine/v5/`、任何 production loader、任何默认 registry、任何 `theory/*/index.yaml`、任何 `cases/` 下已有文件。

每个 Gate 收口时必须运行：

```
git status --short
git diff --name-only -- engine/application engine/decision engine/domain engine/yingqi engine/v5 engine/asof
```

第二条命令预期无输出（本轮把 `engine/asof` 也纳入了零 diff 检查，因为本轮对它是只读）。如有输出，立即停止，不得自行判断"影响可接受"或就地缩小 diff。

**已知工作区背景噪音**：仓库当前存在大量与本任务无关的既有未跟踪文件和已跟踪修改（历史 F09/G6-G9 工作遗留）。零 diff 检查只针对上述明确列出的生产路径与 `engine/asof`，不要求整仓 `git status` 输出为空；只要求你本轮新增的文件严格落在写集清单内、且清单外文件没有因为你的操作而发生新的修改。

### 3. 自主推进协议

你可以在本对话内把 G7 拆成任意数量的子任务，每个子任务开始前用一句话写清楚：任务目标 / 允许读取范围 / 允许写入文件清单 / 完成条件。Gate 之间**不需要**逐个请求用户批准；只有下表情况必须停止并等待用户输入：

| STOP 条件 | 判定标准 | 停止后应做什么 |
|---|---|---|
| 单个新案例暴露必须修改 `engine/asof/` 才能通过的问题 | 现有公共接口签名、裁决语义或白名单组合无法覆盖该案例的合法业务场景 | 写清楚具体缺口（哪个函数/哪个裁决点/为什么现有白名单不够），列出可能的修复方案，等待用户裁决；不得自行扩大白名单或修改裁决语义；可继续用其他案例完成 G7 |
| **三个案例中有两个及以上都需要修改 `engine/asof/` 才能通过** | 与上一条相同的判定标准，但触发次数 ≥2 | 这是模式性证据，说明 G0-G6 的设计可能对已验证案例过拟合。除写清楚每个缺口外，必须在停止说明中额外汇总"共性缺口是否指向同一个根因"，等待用户裁决，不得自行判断可继续推进 |
| 需修改任何现有生产文件或 `engine/asof/`/`tests/asof/` 已有文件（含 G6 新增的两个测试文件） | `git diff --name-only` 命中禁止清单，或发现必须编辑既有文件才能推进 | 立即停止，不要尝试"最小化"这次修改 |
| 某案例的 `input.md` 排盘信息不足以构造原局承载图 | 缺少四柱、藏干、十神或起运信息中的任一项（十神可能只以人读表格"主星"列呈现而无结构化字段，需你自行判断是否等同满足） | 报告缺口，不得用假设数据填补；如仅一个或两个案例不足，可继续用剩余案例完成 G7，并在最终汇总中明确标注该案例"跳过，证据不足" |
| 某案例的事业事件反馈只有相对时间描述（如"最近 7 年左右"）而无法合理换算为可回放窗口 | 反馈原文缺少可锚定的绝对年份或明确起讫年份 | 该单个事件不得构造为事件候选；如案例其余部分（如资产处置年份）仍可支持回放，则用可用部分完成该案例的验证并明确注明省略了哪个事件及原因；如整案无可回放事件，标注该案例"跳过，事件证据不足" |
| 全仓 `pytest -q` 出现第 3 个及以上失败 | 已知 2 个 pre-existing failures（`tests/evaluation/test_dataset.py::test_witness_trust_boundary_is_explicitly_documented` 与 `tests/evaluation/test_prospective_gate_workflow.py::test_handoff_names_first_legal_case_action_and_all_independent_holds`）不计入；第 3 个才算新增失败 | 定位失败是否由本次新增测试引入，报告给用户，不擅自修复非本计划范围的代码 |
| G7 完成，是否进入 G8（新增案例、统计学习/命中率汇总、生产 promotion） | 需要全新的、不可从本次继承的独立授权 | 在最终汇总中明确写"G7 已完成，是否启动 G8 需要您另行明确授权"，然后停止 |

### 4. 证据纪律（不可谈判）

- 禁止在没有真实运行验证命令的情况下声称任何 Gate "通过"。每次声称完成，必须附带该次运行的真实输出（passed 数、failed 数、skipped 数、exit code）。
- 禁止用代码审查、静态阅读或"逻辑上应该没问题"替代实际 pytest 运行。
- 三个案例的历史截止点、已核验事业/财富事件年份必须来自你实际读取的该案例 `feedback.md`，不得凭本提示词第 1 节的摘要字样直接编造具体日期；第 1 节只是预审线索，实际截止点冻结必须以你亲自读到的原文为准。
- 若事件反馈只有年份窗口而无精确日期，必须按 G6 先例采用"窗口末日保守规范化边界"，并在 spec 与测试断言中明确标注该日期不是命主反馈事实日期（复用 `tests/asof/test_case_2024_out_of_sample.py` 的写法模式）。
- 若某案例没有财富反馈（大概率三个案例都没有明确的、可构造新传播边的财富反馈），复用 G4/G6 已冻结的两条合成传播边（升迁→稳定收入能力提高、创业→收入结构变化与资产风险暴露）进行"无匹配显式边不传播"或"事件类型不匹配不传播"的弃权路径断言，不得为这三个新案例发明新的传播边。
- 三个案例各自独立走完整个"读取→准入裁决→构造→回放→断言→运行"流程，不得因为案例结构相似而复制粘贴断言却不验证该案例的实际数据是否支持该断言。

### 5. Gate 执行顺序

#### G7-A · 案例 C-2026-016 样本外回放

1. 读取 `cases/C-2026-016-坤-甲子丙子丙戌戊子/input.md`、`feedback.md`，核实排盘事实完整性（重点核实十神是否以充分形式存在）与已核验事业/婚姻事件的准确年份。
2. 在 `plans/as-of-life-state-g7-larger-sample-case-spec.md` 中新建该案例分节，冻结：准入裁决结论（通过或跳过及理由）；若通过，冻结原局承载图关键节点、大运阶段裁定、至少三个历史截止点（覆盖 2009 结婚入职/2012 换行业/2020 上岸编制 附近的窗口，具体以你读到的原文为准）。
3. 若准入通过，新建 `tests/asof/test_case_2016_out_of_sample.py`，写法参照 `test_case_2024_out_of_sample.py`：
   - 用现有 `engine.asof.natal_capacity`、`engine.asof.daiyun_context` 构造函数（不修改这两个模块本身）构造该案例的 `NatalCapacityGraph` 与 `DaiyunStage` 测试夹具；
   - 用现有 `engine.asof.event_candidate.evaluate_event_candidate` 构造该案例已核验事业/婚姻事件的候选，走双证据门；
   - 用现有 `engine.asof.state_ledger.build_verified_state` 在冻结的至少三个截止点回放，断言：不同截止点产生不同 `VerifiedState`、截止日后事件不泄漏、事实与假设物理分离；
   - 复用 G4/G6 已冻结的两条合成边验证财富弃权路径。
   - 若准入不通过，仍新建该测试文件，但只包含机械核验"证据不足"的断言与一个 `pytest.skip(...)`，写法参照 `test_case_2022_out_of_sample.py`。
4. 运行：
   ```
   python -m pytest tests/asof/test_case_2016_out_of_sample.py -q
   ```
   记录真实 passed/failed/skipped 计数与 exit code。

#### G7-B · 案例 C-2026-026 样本外回放

与 G7-A 相同流程，作用于 `cases/C-2026-026-坤-癸未甲寅壬戌丙午/`，产出 `tests/asof/test_case_2026_out_of_sample.py`，并在同一个 `plans/as-of-life-state-g7-larger-sample-case-spec.md` 中追加该案例的裁定分节。

运行：
```
python -m pytest tests/asof/test_case_2026_out_of_sample.py -q
```

#### G7-C · 案例 C-2026-027 样本外回放

与 G7-A 相同流程，作用于 `cases/C-2026-027-乾-丁卯壬寅甲午乙丑/`，产出 `tests/asof/test_case_2027_out_of_sample.py`，并在同一个 `plans/as-of-life-state-g7-larger-sample-case-spec.md` 中追加该案例的裁定分节。注意第 1 节已标注的"最近 7 年左右"相对时间风险点，按 §3 STOP 表对应条款处理。

运行：
```
python -m pytest tests/asof/test_case_2027_out_of_sample.py -q
```

#### G7-D · 汇总收口

1. 运行完整 as-of 套件确认无回归（应包含 G0-G6 既有测试 + 本轮新增三个文件）：
   ```
   python -m pytest tests/asof -q
   ```
2. 重跑已冻结的生产隔离测试，确认新增测试文件未引入任何新导入违规：
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
5. 新建 `reports/as-of-life-state-g7-larger-sample-validation-report.md`，记录三个案例各自的真实验证证据、各自的准入裁决结论（通过/部分通过/跳过及理由）、任何发现的实现边界问题（即使未构成 STOP，也要如实记录）、生产目录零 diff 证据、全仓 sanity 结果。结论行必须如实反映实际通过/跳过的案例数，格式参照 G6 收口报告，不得使用"全部通过"这类未经证据支持的表述。

### 6. 明确不做（此对话内永久排除）

- 不扩展 `engine/asof/` 的字段、裁决语义或白名单组合，只验证既有实现；
- 不做统计学习、命中率汇总或置信度校准——三个案例的通过/跳过结论只能以列表形式呈现，不得计算通过率、平均置信度或任何跨案例聚合统计量；
- 不新增第四个及以上案例；
- 不做生产 promotion、不接入任何生产 loader/pipeline/registry；
- 不修改任何 F01-F12 卡片契约或 `engine/f09/`；
- 不做任何 GitHub 服务端操作（不 push、不建 PR/Issue/Release）。全程 **LOCAL ONLY / NOT PUSHED**。

### 7. 最终交付物（G7 完成后一次性给出）

1. `reports/as-of-life-state-g7-larger-sample-validation-report.md` 完整路径与结论行；
2. G7-A、G7-B、G7-C、G7-D 的真实验证命令与 passed/failed/skipped/exit code 汇总表；
3. 三个案例各自的准入裁决结论（通过/部分通过/跳过）一览；
4. `git status --short` 与生产目录（含 `engine/asof`）`git diff --name-only` 的最终结果（后者应为空）；
5. 新增文件完整清单；
6. 明确声明：本次为 LOCAL ONLY / NOT PUSHED；
7. 明确声明：G7 完成不代表 G8（新增案例/统计学习/命中率汇总/生产 promotion）已获批准，是否启动 G8 需要用户另行明确授权。

现在开始：先完成 §0 的强制先读，然后从 G7-A 启动，按 §3 的自主推进协议持续执行直到 G7-D 完成或触发 §3 表中的 STOP 条件。

---

## 提示词正文结束（以上为复制边界）

## 使用说明

- 本提示词假定 terra 运行环境的工作目录为仓库根目录 `f:/多流派新思路`，且具备读写本地文件与运行 `pytest`/`git` 命令的权限。
- 本轮延续 G6 的核心目的：**验证泛化能力**，不是**扩展业务能力**。三个新案例特意选择了不同的字段完整度组合（`C-2026-016` 十神字段格式存疑、`C-2026-026`/`C-2026-027` 字段完整但事件精度不同），目的是压力测试"证据不足即跳过"这条纪律本身是否被严格执行，而不是凑出三个"看起来都能通过"的简单案例。
- 若三个案例都验证通过且零回归，这只证明该实现在五个案例（含 G0 的 `C-2026-028`、G6 的 `C-2026-024`）上泛化良好，仍不构成生产 promotion 的充分证据；若要做真正的统计学习或命中率汇总，需要用户另行明确审批并可能需要重新设计证据模型（当前架构是逐案例布尔判定，不是概率模型）。
- 如果三个案例中有两个及以上都触发了"需要修改 `engine/asof/`"的 STOP，这本身是有价值的发现（可能说明 G0-G6 的白名单设计对早期两个验证案例过拟合），不应被当作任务失败，而应如实报告并等待用户裁决下一步。
