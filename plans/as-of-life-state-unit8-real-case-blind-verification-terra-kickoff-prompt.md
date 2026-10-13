# Unit 8 · session_runner 真实历史案例盲断验证 · Terra 无人值守执行提示词

> 用途：复制本文件全文作为新会话的第一条用户消息，指导 ChatGPT 5.6 Terra（或等价 agent）在**一次对话内**无人值守跑完 Unit8-A 至 Unit8-D。低 token、命令优先、证据优先，允许把任务拆成小步骤逐个完成小目标，做完一个立即自动进入下一个，不要中途停下来问"是否继续"，除非命中下方 STOP 条件。
>
> 工作目录固定：`f:/多流派新思路`。所有命令从仓库根执行。Windows `cmd.exe`；禁用 `tail`/`grep`/`sed`/`cat`，用 pytest `-q` 末行 summary 作为唯一计数依据。
>
> 前置事实：[`engine/asof/session_runner.py`](../engine/asof/session_runner.py:1)（Unit 1-7 唯一编排入口 `run_career_session`）已完成 evidence-bounded freeze，但目前只被合成 fixture 测试过（[`tests/asof/test_session_runner.py`](../tests/asof/test_session_runner.py:1)），从未用真实历史案例的"先盲断、后核验"完整流程跑过。`tests/asof/test_case_20xx_out_of_sample.py` 系列走的是**旧路径** [`build_verified_state()`](../engine/asof/state_ledger.py)，不经过 [`session_contract.py`](../engine/asof/session_contract.py:1) 的会话状态机。Unit 8 的目的就是补上这个缺口：证明新状态机能用真实案例的排盘与反馈，走完 `create_initial_envelope → freeze_career_draft → open_verification → record_career_verification → adjudicate_career_verifications → build_career_states →（可选）project_future_from_state` 全流程，并且盲断阶段确实不读取反馈。

---

## 0. 身份与硬性协议（全程生效，任何后续内容不可豁免）

- 只在本对话内推进；除非命中下方 STOP 条件，不为常规读取、写入、验证请求用户逐步批准。
- 严禁执行任何 Git 命令（包括只读 `git status`/`git log`）。
- 严禁任何 GitHub 读写操作。
- 严禁修改 [`engine/asof/`](../engine/asof/) 下任何文件、既有 `tests/asof/` 下任何既有测试文件、任何案例原文（`cases/**/input.md`、`cases/**/feedback.md`）。
- 严禁把本任务的 PASS 外推为 Unit 1-7 生产就绪、G6/G7/G8/G9/G10 结论变更，或任何生产默认行为变更。
- 每个子 Gate 只认真实命令输出（命令 + cwd + collected/passed/failed/errors/skipped + exit code），不得用散文代替运行证据。
- collection error = 零行为证据，立即停并归类，不反复微调、不扩大 selector。
- 修复后旧的 STATIC_REVIEW/VERIFY 立即失效，必须 fresh review + exact rerun。

## 1. 唯一写入白名单

1. `plans/as-of-life-state-unit8-real-case-blind-verification-contract.md`（新建，Unit8-A 产物）
2. `tests/asof/test_unit8_real_case_blind_verification.py`（新建）
3. `reports/as-of-life-state-unit8-real-case-blind-verification-report.md`（新建，Unit8-D 产物）

超出以上三个路径的任何修改均为越权，必须立即 STOP。**不新增、不修改任何 `engine/asof/*.py` 文件**——Unit 8 只验证既有冻结 API，不实现新产品代码。

## 2. 强制先读顺序

1. [`AGENTS.md`](../AGENTS.md) —— 仓库 AI 调用规则。
2. [`plans/as-of-life-state-reasoning-design-2026-07-18.md`](as-of-life-state-reasoning-design-2026-07-18.md:1) §3.5、§3.7、§9、§15 —— 事实/假设分离、盲断先于核验、架构不变量。
3. [`plans/as-of-life-state-g6-out-of-sample-case-spec.md`](as-of-life-state-g6-out-of-sample-case-spec.md:1) 第 2 节 —— 案例 `C-2026-024` 的冻结事实（原局节点、大运阶段、事件窗口、三个截止点、财富弃权），**本任务直接复用这些冻结事实，不得重新解释或改写它们**。
4. [`engine/asof/session_contract.py`](../engine/asof/session_contract.py:1) 全文 —— `SessionIdentity`/`BlindChartInput`/`ConsultationState`/`create_initial_envelope`/`transition_session`。
5. [`engine/asof/consultation_freeze.py`](../engine/asof/consultation_freeze.py:1) 全文 —— `FrozenCareerFundamental`/`FrozenCareerEvent`/`CareerBlindDraft`/`VerificationInput`/`VerificationVerdict`。
6. [`engine/asof/career_state_builder.py`](../engine/asof/career_state_builder.py:1) 全文 —— `CareerImpactSuggestion`/`CareerImpactAdjudication`/`CareerFundamentalAdjudication`。
7. [`engine/asof/session_runner.py`](../engine/asof/session_runner.py:1) 全文与 [`tests/asof/test_session_runner.py`](../tests/asof/test_session_runner.py:1) 全文 —— 唯一编排入口的精确签名与调用顺序，本任务不得重新发明这套顺序。
8. [`engine/asof/event_candidate.py`](../engine/asof/event_candidate.py:1)、[`engine/asof/natal_capacity.py`](../engine/asof/natal_capacity.py:1)、[`engine/asof/daiyun_context.py`](../engine/asof/daiyun_context.py:1)、[`engine/asof/reality_translation.py`](../engine/asof/reality_translation.py:1) —— 构造 `LifeEventCandidate`/`NatalCapacityGraph`/`DaiyunStage`/`FrozenLandingSet` 所需的既有类型。
9. `cases/C-2026-024-坤-己巳壬申辛亥壬辰/input.md` 与 `feedback.md` 全文 —— 唯一使用的真实案例；**在完成盲断草案构造之前不得让 feedback.md 的任何内容进入草案对象的证据字段**。

不要从历史 handoff、旧摘要或其他案例文件推断本任务范围；一切以本文件与上述 9 项权威源为准。

## 3. 子任务分解与推进规则（Unit8.A–Unit8.D，全部在本对话内完成）

```
Unit8.0 RECOVER → Unit8.A CONTRACT → Unit8.B TDD RED
  → Unit8.C IMPLEMENT + VERIFY → Unit8.D REPORT + FREEZE
```

### Unit8.0 RECOVER

- 按第 2 节顺序读完权威源。
- 确认 `C-2026-024` 的冻结事实（四柱、藏干、大运两段、两个事业事件窗口、三个截止点 `2013-12-31`/`2015-12-31`/`2025-12-31`、财富弃权规则）与 [`tests/asof/test_case_2024_out_of_sample.py`](../tests/asof/test_case_2024_out_of_sample.py:1)（若存在同案例旧测试，只读参考，不修改、不复制其 `build_verified_state` 调用路径）。
- **完成判据**：一句话基线声明 + 确认三个截止点与两个事件窗口取值，写入 Unit8-A 合同草稿。

### Unit8.A CONTRACT（写入 `plans/as-of-life-state-unit8-real-case-blind-verification-contract.md`）

冻结以下内容，不得留开放选择：

1. **案例与截止点**：`C-2026-024-坤-己巳壬申辛亥壬辰`，三个独立会话，`as_of_date` 分别为 `2013-12-31`、`2015-12-31`、`2025-12-31`，每个会话使用独立 `SessionIdentity.session_id`（格式 `S-YYYYMMDDTHHMMSSZ-xxxxxxxx`，可用固定占位时间戳，只要格式合法）。
2. **盲断草案构造规则**（硬性纪律，STATIC_REVIEW 必查）：
   - 测试模块内必须有一个独立函数（如 `_build_blind_draft(as_of_date)`），只使用 `input.md` 的四柱、藏干、十神、大运字段构造 `NatalCapacityGraph`、`DaiyunStage`、`AnnualInteractionTrace`、`LifeEventCandidate`（经 `evaluate_event_candidate`）、`FrozenLandingSet`、`FrozenCareerFundamental`、`FrozenCareerEvent`；
   - 该函数的源码中**不得出现** `feedback.md` 的路径字符串、反馈原文摘录或反馈日期；
   - 三个截止点对应的冻结事件集合：`2013-12-31` → 零事件（草案不含任何 `FrozenCareerEvent`，`CareerBlindDraft.events == ()`）；`2015-12-31` → 仅含教师入职事件；`2025-12-31` → 教师入职 + 升职校长两个事件。事件窗口、根源等级、完成方式沿用 [`g6-out-of-sample-case-spec.md`](as-of-life-state-g6-out-of-sample-case-spec.md:76) 第 2.5 节冻结值（均为 `STRONG_ROOT` + `ACTIVATE_EXISTING`）。
   - 每个 `FrozenLandingSet` 的 `center`/`alternatives`/`falsifiers` 必须只依据原局节点与年度轨迹推断合理落点（例如"教育系统内的岗位承接"），不得直接写出反馈已知的确切结果作为唯一落点而不设替代假设。
3. **核验草案构造规则**：另一个独立函数（如 `_build_verification_from_feedback(package, as_of_date)`），只在此函数内引用 `feedback.md` 的原文摘录，构造 `VerificationInput`（逐条对应草案中的每个 `FrozenCareerEvent`）、`CareerImpactSuggestion`、`CareerImpactAdjudication`、`CareerFundamentalAdjudication`。零事件截止点（`2013-12-31`）的 `verifications`/`suggestions`/`impact_adjudications` 均为空 tuple。
4. **daiyun_end 推导规则**：`daiyun_end` 必须等于覆盖 `as_of_date` 的大运阶段的结束日，由案例大运表推导（[`g6-out-of-sample-case-spec.md`](as-of-life-state-g6-out-of-sample-case-spec.md:47) 第 2.3 节两段大运），不得自行发明。
5. **调用顺序**：每个会话必须调用 [`run_career_session()`](../engine/asof/session_runner.py:53) 一次，`career_candidates`/`wealth_bindings` 全部留空（`None`），三个会话都应停在 `STATE_BUILT`（因为财富无显式传播边，事业本身也不构造后运候选——本任务只验证盲断→核验→建状态闭环，不验证 Unit 4 的未来推演）。
6. **断言最小集**：
   - `2013-12-31` 会话：`result.state_result.verified_state.verified_event_ids == ()`；
   - `2015-12-31` 会话：`verified_event_ids` 恰含教师入职事件 ID；
   - `2025-12-31` 会话：`verified_event_ids` 恰含教师入职与升职校长两个事件 ID；
   - 三个会话各自的 `result.final_envelope.state is ConsultationState.STATE_BUILT`；
   - `2013-12-31` 会话的 `freeze_package.events == ()`，直接证明"盲断阶段确实不知道未来事件"，而不是靠运行期过滤器隐藏未来事件。
7. **STATIC_REVIEW 静态检查项**：用 `ast` 解析测试文件，确认 `_build_blind_draft` 函数体的字符串常量与属性访问链中不包含 `"feedback"` 子串；确认三处 `run_career_session` 调用严格按 Unit 8 冻结顺序传参，不重新实现任何 Unit1-7 内部校验逻辑。
8. 本合同必须经一次逻辑新鲜独立复核（reset 角色重读第 1-7 条与权威源），verdict 写入合同末尾。

**完成判据**：合同无开放选择，可直接机械执行；fresh review verdict 为 `PASS`。若发现与权威源冲突（例如反馈窗口日期与 G6 冻结值不一致），返回 `CONTRACT GAP`，不强行编造。

### Unit8.B TDD RED

1. 创建 [`tests/asof/test_unit8_real_case_blind_verification.py`](../tests/asof/test_unit8_real_case_blind_verification.py:1)，按合同实现三个测试（每个截止点一个，或参数化为一个测试三个 case）。
2. 运行：

```text
python -m pytest tests/asof/test_unit8_real_case_blind_verification.py -q
```

3. 完成条件：**行为阶段真实失败**（例如断言不一致、字段缺失、类型错误），不是 collection error。记录精确 failed 数、exit code、失败原因摘要。若测试助手本身有拼写/导入缺陷，可在本 Gate 内修订后重新确认失败仍来自真实断言差异，不得因 helper 缺陷跳过 RED。
4. 若首次运行直接全部 PASS：STOP，不得声称完成——这意味着测试没有真实约束力，必须重新设计断言（例如加入 `freeze_package.events` 精确长度检查、`verified_event_ids` 精确内容检查）后重新取得有效 RED。

### Unit8.C IMPLEMENT + VERIFY

1. 调整测试实现直至通过。**不得修改 `engine/asof/` 任何文件**——如果发现 `session_runner` 或其依赖存在真实缺陷，STOP 并在报告中记录缺陷描述，不得自行修复冻结产品代码。
2. 依次运行并记录 passed/failed/skipped、exit code、耗时：

```text
python -m pytest tests/asof/test_unit8_real_case_blind_verification.py -q
python -m pytest tests/asof -q
python -m pytest tests/asof/test_production_isolation.py -q
```

3. 完成条件：
   - 专用测试全部 passed；
   - `tests/asof -q` 相对当前基线（当前应为 449 passed, 1 skipped）只允许新增 passed，不允许任何既有测试新增失败；
   - 生产隔离测试 4 passed；
   - 用文件读取比对（不使用 Git）确认 `engine/asof/` 目录下每个文件内容与本任务开始前一致（可用文件长度或时间戳粗对比，逐一列出确认零变更）。
4. 若出现任何既有测试新增失败：立即 STOP，归类（product defect / test defect / contract gap / environment failure），不得自行"修复"冻结产品代码来让测试通过。

### Unit8.D REPORT + FREEZE

1. 创建 [`reports/as-of-life-state-unit8-real-case-blind-verification-report.md`](../reports/as-of-life-state-unit8-real-case-blind-verification-report.md:1)，结构建议：验证目标、写集清单、案例与截止点、盲断/核验分离证据（引用 `_build_blind_draft` 源码不含 feedback 字样的检查结果）、Unit8-A/B/C 逐项证据（含首次 RED 原始输出）、三个截止点的 `verified_event_ids` 实际输出、`engine/asof/` 零变更确认、`LOCAL ONLY / NOT PUSHED`。
2. 报告创建后，重新执行 Unit8.C 第 2 步全部命令一次，把新鲜结果回填报告，不得复制创建前的旧结果当作最终证据。
3. 给出唯一裁决（四选一）：
   - `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`
   - `REVISE — LOCAL GOVERNANCE GAP`
   - `BLOCKED — MATERIAL GAP`（例如发现 session_runner 或其依赖存在需要修复的真实缺陷）
   - `AUTHORIZATION_REQUIRED — RETAINED DECISION`
4. 明确列出 non-inference boundaries：本任务不证明 Unit 1-7 全量生产就绪；不证明其他案例、其他截止点、Unit 4 未来推演、财富传播、归档层（Unit 6）行为；不构成对 G6/G7/G8/G9/G10 结论的变更；未执行任何 Git/GitHub 操作。

## 4. STOP / BLOCKED 判定（命中即停，不绕过）

- 需要修改 `engine/asof/` 任一文件；
- 需要修改任何既有 `tests/asof/` 测试文件、案例原文；
- 首次新增测试直接全部 PASS（零真实约束力）；
- `tests/asof -q` 出现除本任务新增测试之外的任何新增失败；
- 发现 `session_runner` 或其依赖存在真实缺陷（例如 `freeze_career_draft` 未真正阻止反馈信息泄漏进草案）——记录为 `BLOCKED — MATERIAL GAP`，不得自行修复；
- 任何操作可能触达 Git 或 GitHub；
- 合同文本与本提示词出现无法用第 2 节权威文件解决的冲突。

出现 STOP 条件时：保留已取得的全部证据，在会话内明确写出触发条件、已完成的 Gate、唯一下一合法动作，然后停止，不要猜测性继续。

## 5. 单次对话完成的最终输出要求

对话结束前必须给出：

1. 三个白名单文件的最终路径；
2. Unit8-A CONTRACT fresh review verdict；
3. Unit8-B 首次 RED 的精确 failed 数、exit code 与失败原因摘要；
4. Unit8-C 全部验证命令的精确 passed/failed/skipped 数、exit code、耗时；
5. `engine/asof/` 零变更确认方式与结果；
6. Unit8-D 唯一裁决与 non-inference boundaries；
7. 精确状态标记：`LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION`。

不得在任一项证据缺失或未新鲜验证时声称任务完成。
