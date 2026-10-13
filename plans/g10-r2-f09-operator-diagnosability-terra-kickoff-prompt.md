# G10-R2 · F09 Operator Diagnosability Readiness · Terra 无人值守执行提示词

> 用途：复制本文件全文作为新会话的第一条用户消息，指导 ChatGPT 5.6 Terra（或等价 agent）无人值守完成 G10-R2-A 至 G10-R2-D。
> 前置：G10（[`g10-next-governance-milestone-plan.md`](g10-next-governance-milestone-plan.md)）已完成，唯一裁决为 `G10.9=PASS/COMPLETE—EVIDENCE-BOUNDED FREEZE`、`G10.10=HOLD F10`，记录见 [`g10-r1-readiness-and-sanity-closeout.md`](g10-r1-readiness-and-sanity-closeout.md)。本任务**不是** F10，也不解除 `HOLD F10`；它只把 G10.1 十二证据域中标记为 `REQUIRES_LOCAL_GATE` 的第 7 项「观测性」推进到可裁决状态。

---

你正在 mangpai-fusion 仓库执行长任务 **G10-R2：F09 Operator Diagnosability Readiness Gate**。全程无人值守，允许你把任务拆成小步骤逐个完成小目标，但必须在同一个会话内依次做完 G10-R2-A（CONTRACT）、G10-R2-B（TDD RED）、G10-R2-C（实现+验证）、G10-R2-D（报告+复核）四个 Gate，不等待中途确认，除非触及下方 STOP 条件。

## 0. 强制先读顺序

1. [`AGENTS.md`](../AGENTS.md) —— 仓库 AI 调用规则。
2. [`plans/g10-next-governance-milestone-plan.md`](g10-next-governance-milestone-plan.md) —— G10 计划全文，确认状态模型枚举、non-inference boundaries 与 STOP 条件。
3. [`plans/g10-r1-readiness-and-sanity-closeout.md`](g10-r1-readiness-and-sanity-closeout.md) 全文，尤其第 2 节十二域表——第 7 项「观测性」当前为 `REQUIRES_LOCAL_GATE`，依据是「已有 audit/error surface，operator readiness 未单独验收」。这是本任务唯一要推进的域，不得扩大到其他域。
4. [`engine/f09/errors.py`](../engine/f09/errors.py) 全文 —— 已冻结的 typed F09 error 层，只读参考。
5. [`engine/f09/contracts.py`](../engine/f09/contracts.py) 全文 —— phase observation / evidence contract 的字段定义，只读参考。
6. [`engine/f09/artifacts.py`](../engine/f09/artifacts.py) 中 `ArtifactWriteAttempt`、`ArtifactPhaseObservation`（用 grep 定位实际类名与字段）—— 已冻结的 attempt/audit 记录结构，只读参考。
7. [`plans/production-implementation-control.md`](production-implementation-control.md) §8（尤其 §8.9）—— 确认 F09 现行冻结边界与本次可修改范围不冲突。

不要从旧摘要、handoff.md 或本提示词的转述推断上述文件的精确字段名和类型；必须实际读取源码后再动手。

## 1. 任务目标与非目标

### 1.1 目标

对 F09 现有的 typed errors、phase observations、artifact attempt ledger 建立一份**operator diagnosability 契约**：定义一组具体、可机械验证的最低诊断标准（例如：给定任意一次失败的 F09 run，operator 能否仅凭已持久化的 observation/attempt/error 记录，不看源码就判断出「哪个 phase 失败」「错误类别」「是否可重试」「关联哪次输入/digest」）。随后用测试证明现有实现是否满足该标准；若发现材料性缺口，只能通过**新增只读文档**（operator runbook）补齐,不得修改 F09 生产代码的对外行为或签名。

### 1.2 非目标

- 不启动、不隐含启动 F10；不改变 `HOLD F10` 裁决。
- 不修改 [`engine/f09/`](../engine/f09/) 下任何生产逻辑、字段、签名或默认行为。若诊断标准验证发现真正的行为缺口（而非文档缺口），必须在 G10-R2-A CONTRACT 阶段就把该发现记录为 `AUTHORIZATION_REQUIRED`，停止并交回决策，不得自行扩大到实现修复。
- 不修改 [`tests/f09/`](../tests/f09/) 下任何既有测试文件。
- 不修改九份 Task 9-P 专项冻结文件、[`handoff.md`](../handoff.md)、[`tools/README.md`](../tools/README.md)、任何 F01–F12 契约。
- 不执行任何 Git 命令、任何 GitHub 读写。
- 不声明性能、安全、部署、跨平台或全仓正确性已证明。

## 2. Gate 顺序与完成条件

### G10-R2-A：CONTRACT（冻结合同）

1. 实际读取第 0 节列出的 F09 源码文件，列出当前已持久化、可用于诊断的具体字段清单（如 phase 名、error class、error message digest、attempt outcome、idempotency key、input snapshot refs 等——精确名称以实际源码为准）。
2. 基于该清单定义 3–6 条具体、可机械验证的最低诊断标准（例如：「每个 FAILED attempt 必须携带非空 error_class 与 error_message_digest」「每个 phase observation 必须可定位到唯一 phase 名」）。每条标准必须能转化为一个 pytest 断言。
3. 冻结写入 [`plans/g10-r2-f09-operator-diagnosability-contract.md`](g10-r2-f09-operator-diagnosability-contract.md)：目标/非目标、精确写集白名单（更新第 3 节）、诊断标准清单、对应验证 selector 设计、STOP 条件、non-inference boundaries。
4. 对该合同做一次逻辑新鲜的独立自审（重置假设，重新核对字段是否确实来自实际源码而非猜测），记录 verdict。只有 `PASS` 才能进入 G10-R2-B。

### G10-R2-B：TDD RED

1. 创建 [`tests/f09/test_operator_diagnosability_readiness.py`](../tests/f09/test_operator_diagnosability_readiness.py)，把 CONTRACT 中每条诊断标准转化为一个独立测试函数，直接对现有 F09 公开产出（不新建 mock 行为）做断言。
2. 运行：

```text
python -m pytest tests/f09/test_operator_diagnosability_readiness.py -q
```

3. 记录精确 collected/passed/failed 数与 exit code。允许两种结果：
   - 全部通过（说明现有实现已满足标准，直接进入 G10-R2-C 的验证收尾，不需要新增文档）；
   - 部分失败（说明存在文档或可见性缺口，进入 G10-R2-C 补齐 runbook）。
   collection error 视为零证据，必须先修好测试文件本身再重跑。

### G10-R2-C：补齐 + 验证

1. 若 G10-R2-B 全部通过：跳过文档新增，直接执行下方第 2 步验证账本。
2. 若存在失败：只能创建 [`docs/f09-operator-diagnosability-runbook.md`](../docs/f09-operator-diagnosability-runbook.md)，用现有真实字段说明 operator 应如何从 attempt/observation 记录诊断典型失败；不得为了让测试通过而弱化断言、删除失败用例或修改生产代码。若失败的根因确实是生产代码缺少某个诊断字段（而非文档缺失），必须停止并在报告中记录为 `AUTHORIZATION_REQUIRED — 需要新的独立 CONTRACT 授权才能修改 engine/f09`，不得自行实现。
3. 依次运行并记录 passed/failed/skipped、exit code：

```text
python -m pytest tests/f09/test_operator_diagnosability_readiness.py -q
python -m pytest tests/f09 -q
python -m pytest -q
```

4. 完成条件：
   - 专用测试全部 passed（或已诚实记录为 `AUTHORIZATION_REQUIRED` 并停止）；
   - `tests/f09 -q` 计数与 [`g10-r1-readiness-and-sanity-closeout.md`](g10-r1-readiness-and-sanity-closeout.md) 记录的 1172 passed 一致，零新增失败；
   - 全仓 `pytest -q` 相比 [`g10-r1-readiness-and-sanity-closeout.md`](g10-r1-readiness-and-sanity-closeout.md) 记录的 `3121 passed, 7 skipped, 1 warning` 基线零新增失败（允许新增 1 passed 对应本任务新测试）；
   - 全仓命令可能耗时约 20 分钟，必须真正等待其退出并取得完整 summary 行与 exit code，不得臆造或提前终止推断。

### G10-R2-D：报告与最终复核

1. 创建 [`plans/g10-r2-f09-operator-diagnosability-report.md`](g10-r2-f09-operator-diagnosability-report.md)：CONTRACT 摘要、诊断标准清单、G10-R2-B 首次 RED（如有）原始结果、是否新增 runbook、G10-R2-C 全部验证命令的精确计数与 exit code、`LOCAL ONLY / NOT PUSHED` 声明。
2. 对 [`plans/g10-r1-readiness-and-sanity-closeout.md`](g10-r1-readiness-and-sanity-closeout.md) 第 2 节十二域表做一处有限追加：把第 7 项「观测性」的状态从 `REQUIRES_LOCAL_GATE` 更新为 `PROVEN`（有界）或维持 `REQUIRES_LOCAL_GATE`（若发现材料性缺口未获授权解决），并注明依据本任务证据；不得改写其余十一项或第 4–7 节既有裁决。
3. 报告创建后，重新执行 G10-R2-C 第 3 步全部命令一次，把新鲜结果回填报告，不得复制创建前的旧结果当作最终证据。
4. 最终收口检查：报告结尾声明 `LOCAL ONLY / NOT PUSHED`，且明确声明 `HOLD F10` 未被解除、F10 未获授权且未启动。

## 3. 写入白名单（初始，A 阶段冻结后为准）

1. `plans/g10-r2-f09-operator-diagnosability-contract.md`（新建）
2. `tests/f09/test_operator_diagnosability_readiness.py`（新建）
3. `docs/f09-operator-diagnosability-runbook.md`（新建，仅当 G10-R2-B 出现失败时才创建）
4. `plans/g10-r2-f09-operator-diagnosability-report.md`（新建）
5. `plans/g10-r1-readiness-and-sanity-closeout.md`（仅第 2 节十二域表第 7 行的有限更新）

超出以上路径的任何修改均为越权，必须立即 STOP。

## 4. 明确禁止修改

- [`engine/f09/`](../engine/f09/) 下任何生产文件；
- [`tests/f09/`](../tests/f09/) 下任何既有测试文件；
- 九份 Task 9-P 专项冻结文件（见 [`production-implementation-control.md`](production-implementation-control.md) §8.7）；
- [`handoff.md`](../handoff.md)、[`tools/README.md`](../tools/README.md)；
- [`plans/g10-next-governance-milestone-plan.md`](g10-next-governance-milestone-plan.md)、[`plans/g10-r1-readiness-and-sanity-closeout.md`](g10-r1-readiness-and-sanity-closeout.md) 第 1、3–8 节及第 2 节除第 7 行外的其他行；
- 任何 F01–F12 正式契约与机器附录；
- 任何 Git 或 GitHub 操作。

## 5. STOP 条件（出现任一即立即停止，不得自行绕过）

- 诊断标准验证失败的根因是生产代码缺少某字段，而非文档缺失；
- 需要修改 `engine/f09/` 任何签名、字段或默认行为；
- `tests/f09 -q` 或全仓 `pytest -q` 出现本次基线（1172 passed / 3121 passed, 7 skipped）之外的新增失败；
- CONTRACT 阶段的诊断标准清单无法从实际源码字段推导，只能凭空定义；
- 任何动作可能修改 GitHub 服务端状态；
- 本提示词与实际读到的源码/合同出现无法用第 0 节权威文件解决的冲突。

出现 STOP 条件时：保留已取得的全部证据（不删除、不覆盖），在会话内明确写出触发的具体条件、已完成的 Gate、以及唯一下一合法动作，然后停止，不要猜测性继续。

## 6. 最终交付要求

完成 G10-R2-D 后，在同一会话内给出总结，必须包含：

1. CONTRACT 文件路径与诊断标准清单摘要；
2. G10-R2-B 首次 RED 的精确 failed 数与 exit code（若全部直接 passed，明确说明未发生 RED）；
3. 是否新增 runbook 文档及其路径；
4. G10-R2-C 全部验证命令的精确 passed/failed/skipped 数与 exit code（专用测试、`tests/f09`、全仓）；
5. 十二域表第 7 行的最终状态更新；
6. 报告路径及其"报告后最终新鲜复核"章节的回填结果；
7. `LOCAL ONLY / NOT PUSHED` 声明；
8. 明确声明 `HOLD F10` 未被解除，F10 未获授权且未启动。

不得在任一项证据缺失或未新鲜验证时声称任务完成。
