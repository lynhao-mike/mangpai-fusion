# 下一长任务 Terra 无人值守执行提示词 · Unit9 合同缺口修复与闭环

> 本文件只交付一份可直接粘贴给 ChatGPT 5.6 Terra 的执行提示词；不在本文件内实施该长任务。

## 使用说明

- 直接把“提示词正文”整段粘贴给 Terra 作为单次会话的完整任务说明。
- 提示词内已包含所有必要事实源路径、已知缺口、修复边界和验证命令；Terra 不需要额外提问即可开始 RECOVER。
- 允许 Terra 在提示词内部自行拆出子任务（诊断 → 合同修订 → 测试修订 → RED → GREEN → 验证 → 报告），但必须在同一对话内完成，不得请求切换会话。

---

## 提示词正文

```text
你正在 mangpai-fusion 仓库承接长任务：修复 Unit9 合同缺口并完成闭环（Unit9.A REVISE → Unit9.B RED → Unit9.C VERIFY → Unit9.D REPORT/FREEZE）。本任务已经过独立事实核查确定为当前最高优先级，因为 as-of 求测闭环是仓库锁定的最高优先级方向（AGENTS.md 第 6 节禁止事项；plans/as-of-life-state-reasoning-design-2026-07-18.md 第 7 行）。

## 背景（已核实，无需重新调查）

Unit9 已创建三个文件：
- plans/as-of-life-state-unit9-real-case-future-projection-contract.md（合同，含旧 fresh review PASS，已失效）
- tests/asof/test_unit9_real_case_future_projection.py（测试，首次 RED 为 2 failed, 2 passed，形态不符合合同预期）
- reports/as-of-life-state-unit9-real-case-future-projection-report.md（尚未创建或为空）

已定位两个具体缺口，请在 RECOVER 阶段独立复核这两点是否仍然成立，而不是照抄本段结论：

1. **合同缺口**：合同第 6 节要求成功输入序列化后不含字符串 "2026"，但候选必须携带真实 case_id "C-2026-024-坤-己巳壬申辛亥壬辰"，导致该检查对完整候选对象必然失败。零污染检查的正确范围应限定在语义内容（conclusion 文本、required_active_state_ids、required_open_path_ids、wealth binding 的 event_id/observed_conditions/active_falsifiers/edges），不应检查整个候选对象的 repr。

2. **测试缺口**：test_unit9_real_case_future_projection.py 中第二次 run_career_session() 调用试图用 `record.verification for record in result.adjudication_bundle.records` 重建 verifications 参数，但 CareerVerificationRecord 没有 .verification 属性。正确做法是保留第一次调用使用的原始输入（verifications、suggestions、impact_adjudications、fundamental_adjudication、draft），直接复用这组原始对象做第二次调用，不要从结果对象反推。

## 唯一目标

三个真实事业候选/财富断言仍然有效，只是被上述两个缺口挡住：
1. 至少一个 CareerFutureCandidate 用真实 active_state_ids 和真实 open path 让最终状态到达 PROJECTED；
2. 两个确认事件的 WealthEventBinding 均 edges=()，财富传播均 NO_EXPLICIT_EDGE / changed=False / 不产生财富状态；
3. 2026–2027 待追踪内容不得污染候选语义、财富绑定语义或 required IDs（但候选 identity 本身允许包含真实 case_id）。

## 硬边界（不可协商）

- 只允许写三个文件：
  1. plans/as-of-life-state-unit9-real-case-future-projection-contract.md
  2. tests/asof/test_unit9_real_case_future_projection.py
  3. reports/as-of-life-state-unit9-real-case-future-projection-report.md
- 禁止修改 engine/asof/**、任何既有测试、cases/**/input.md、cases/**/feedback.md。
- 禁止任何 Git 或 GitHub 操作（本地与远端均不可）。
- 修复只能调整第 1、2 个文件中的断言范围与测试实现，不得放宽正确性要求本身（即不能删掉零污染检查,只能收窄其检查范围；不能删掉重投影调用,只能修正其参数构造方式）。
- 任何失败必须先分类：product defect / test defect / contract gap / selector-collection error / environment-tool failure。

## 执行流程

### Unit9.A REVISE
1. 只读重读 plans/as-of-life-state-unit9-real-case-future-projection-contract.md 全文和 tests/asof/test_unit9_real_case_future_projection.py 全文。
2. 独立确认上述两个缺口的根因（不要假设背景描述完全正确，必须用实际报错复现）。
3. 修订合同第 6 节，明确零污染检查的检查对象为语义字段而非完整对象 repr；在合同末尾追加新的 fresh review 段落，标注旧 PASS 已失效、新审查角色重置、新结论。
4. 复核只能给出 PASS 或 REVISE；REVISE 则继续修订直至 PASS。

### Unit9.B TDD RED（受控）
1. 修订测试文件：修正第二次 runner 调用的参数构造（复用第一次调用的原始输入对象），修正零污染断言的检查范围。
2. 运行 `python -m pytest tests/asof/test_unit9_real_case_future_projection.py -q`，记录真实 pytest 末行与 exit code。
3. 如果仍有失败但失败形态是"新缺口"（不在本提示词已知的两个缺口范围内），停止并把失败原始信息、分类和你的判断写入报告草稿，不要自行扩大修复范围。
4. 如果失败形态吻合已知缺口且属于测试自身输入/断言问题，修复后重新运行,直至该文件全绿或遇到不明确的新失败。

### Unit9.C VERIFY
运行以下命令并记录真实末行、exit code：
1. `python -m pytest tests/asof/test_unit9_real_case_future_projection.py -q`
2. `python -m pytest tests/asof -q`
3. `python -m pytest tests/asof/test_production_isolation.py -q`

完整套件相对已知前置基线（452 passed, 1 skipped）只允许新增 Unit9 测试实例通过，不得新增失败或 skipped。

对 engine/asof/ 目录下 15 个产品文件做 SHA-256/长度/UTC mtime 三元组核验,确认与本任务开始前完全一致（changed=0）。

### Unit9.D REPORT + FREEZE
1. 创建 reports/as-of-life-state-unit9-real-case-future-projection-report.md，结构参考 reports/as-of-life-state-unit8-real-case-blind-verification-report.md 的章节划分（结论状态、目标范围、授权写集、冻结矩阵、验证证据、失败与无效证据账本、非推断边界）。
2. 报告创建后必须重新执行 Unit9.C 的三条命令和产品三元组核验,只用报告创建后的新鲜结果作最终证据,不得复用创建报告前的结果。
3. 最终裁决只能是以下之一：PASS/COMPLETE — EVIDENCE-BOUNDED FREEZE，或 BLOCKED — 附具体原因。
4. 状态边界固定标注：LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION。

## STOP 条件（命中任一立即停止并汇报,不得继续推进）

- 需要修改 engine/asof/ 才能通过测试；
- 出现与已知两个缺口无关的新失败,且原因不明确；
- 完整 tests/asof 套件出现除 Unit9 新增实例外的额外失败或新增 skipped；
- 连续两轮 fresh review 均为 REVISE；
- 任何操作可能产生 GitHub 服务端副作用；
- 需要把 2026–2027 待追踪内容当作已核验事实才能让候选选中。

## 完成后的汇报格式

最终回复必须包含：真实运行得到的 active_state_ids/path_states/confirmed_ids、合同修订前后对比摘要、RED 到 GREEN 的失败分类账本、三条验证命令的真实末行与 exit code、产品三元组核验结果、最终裁决（PASS/BLOCKED 及原因）。不得省略任何一项,也不得用推测替代真实命令输出。
```

---

## 交付边界

本文件本身不实施 Unit9 长任务，只交付上述提示词与使用说明。
