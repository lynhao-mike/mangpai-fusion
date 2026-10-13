# G10 无人化执行提示词（供 ChatGPT 5.6 Terra 执行）

> 用途：把本提示词整段粘贴给 terra 模型作为其唯一系统/任务指令，驱动其在**一次对话内**无人化跑完 G10 全部子 Gate。低 token、命令优先、证据优先，不写议论文。
>
> 工作目录固定：`f:/多流派新思路`。所有命令从仓库根执行。Windows `cmd.exe`；禁用 `tail`/`grep`/`sed`/`cat`，用 pytest `-q` 末行 summary 作为唯一计数依据。
>
> 事实源（按顺序读取，不得跳读）：
> 1. [`plans/production-implementation-control.md`](production-implementation-control.md) §3 阶段门表、§8 全部小节（含 §8.7、§8.8）
> 2. [`plans/g6-task9p-total-gate-upgrade-review.md`](g6-task9p-total-gate-upgrade-review.md)（Task 9-P 唯一现行裁决：`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`）
> 3. [`plans/g10-next-governance-milestone-plan.md`](g10-next-governance-milestone-plan.md)（本次要执行的冻结计划，唯一 thesis 与 Gate 定义均在此，不得重新发明）

---

## 0. 身份与硬性协议（全程生效，任何后续内容不可豁免）

- 只在本对话内推进；除非命中下方 STOP 条件，不为常规读取、写入、验证请求用户逐步批准。
- 严禁执行任何 Git 命令（包括只读 `git status`/`git log`）。
- 严禁任何 GitHub 读写操作（push、PR、Issue、Release、workflow、API）。
- 严禁修改 [`engine/f09/`](../engine/f09/)、[`tests/f09/`](../tests/f09/) 以及九份 Task 9-P 专项冻结文件，除非某个子 Gate 明确列出精确写集且已获该 Gate 独立授权。
- 严禁把 G10 任一子 Gate 的 PASS 外推为另一子 Gate、F10、或全仓正确性的 PASS。
- 每个子 Gate 只认真实命令输出（命令 + cwd + collected/passed/failed/errors/skipped + exit code），不得用散文代替运行证据。
- collection error = 零行为证据，立即停并归类，不反复微调、不扩大 selector。
- 修复后旧的 STATIC_REVIEW/VERIFY 立即失效，必须 fresh review + exact rerun。

---

## 1. 子任务分解与推进规则

把 G10 拆成 11 个小目标（对应 [`g10-next-governance-milestone-plan.md`](g10-next-governance-milestone-plan.md) §4 的 G10.0–G10.10）。每个小目标必须满足下方“完成判据”才能进入下一个；不得跳步、不得把中间结论当最终裁决。除非命中 STOP 条件，做完一个立即自动进入下一个，不要停下来问“是否继续”。

```
G10.0 RECOVER → G10.1 readiness INVENTORY → G10.2 sanity triage
  → G10.3 admission selection → G10.4 frozen contract → G10.5 authorized implement
  → G10.6 fresh STATIC_REVIEW → G10.7 exact VERIFY → G10.8 fresh EVIDENCE_REVIEW
  → G10.9 freeze/closeout → G10.10 F10 Go/Hold/Reject
```

### G10.0 RECOVER / baseline lock

- 读取本文件“事实源”三份文件的最后有效章节。
- 确认 Task 9-P 现行裁决、G6–G9 §8.1–§8.8 边界、两个非 F09 sanity 失败的既有登记（[`test_witness_trust_boundary_is_explicitly_documented()`](../tests/evaluation/test_dataset.py:256)、[`test_handoff_names_first_legal_case_action_and_all_independent_holds()`](../tests/evaluation/test_prospective_gate_workflow.py:343)）未被后续文件改写。
- 用非 Git 方式核对九份 Task 9-P 专项文件与总控是否在本次会话前被改动（仅用文件时间戳/长度对比，不使用 Git）。
- **完成判据**：写出一句话基线声明 + 唯一下一动作 = 进入 G10.1。

### G10.1 Production-readiness INVENTORY（只读，不选方案）

- 按 [`g10-next-governance-milestone-plan.md`](g10-next-governance-milestone-plan.md) §5.1 十二项证据域逐项打状态标签：`PROVEN`/`NOT_REQUIRED`/`REQUIRES_LOCAL_GATE`/`REQUIRES_EXTERNAL_DECISION`/`BLOCKED_BY_PROHIBITION`/`UNKNOWN`。
- 每项标签必须附证据来源（文件+行号或已执行命令），禁止凭空猜测。
- **完成判据**：十二项全部有标签和证据来源，且未选择实现方案。

### G10.2 Sanity failure triage（只读根因，不修复）

- 分别精确执行：
  ```
  python -m pytest tests/evaluation/test_dataset.py::test_witness_trust_boundary_is_explicitly_documented -q
  python -m pytest tests/evaluation/test_prospective_gate_workflow.py::test_handoff_names_first_legal_case_action_and_all_independent_holds -q
  ```
- 记录每条命令的 exit code、失败断言原文、涉及的期望文案。
- 判定两者是否与 F09 有因果关系（预期：无）；若发现因果关系，STOP 并归类为 `MATERIAL READINESS GAP`。
- **完成判据**：两条命令各自有完整账本 + 明确“不归因 F09”结论，或 STOP 记录。

### G10.3 Admission selection

- 汇总 G10.1、G10.2 结果，选择**唯一**可在本对话内合法推进的最小单元（预期是：两个 sanity 失败的最小文案修复，因为它们是 `REQUIRES_LOCAL_GATE` 且写集明确）。
- 若 G10.1 发现任何 `REQUIRES_EXTERNAL_DECISION` 或 `BLOCKED_BY_PROHIBITION` 项，登记但不阻塞本轮 selection。
- **完成判据**：写出被选单元名称、精确写集候选、依赖和排除项。

### G10.4 Frozen governance contract

- 为被选单元（默认：两个 sanity 失败的最小文案修复）冻结合同：
  - 目标：让两条 selector 分别转为 passed，且不触及 F09、production-default、Git/GitHub。
  - 精确写集候选：[`tools/README.md`](../tools/README.md)（witness trust-boundary 文案）、[`handoff.md`](../handoff.md)（prospective 首案与 HOLD 文案）。
  - 非目标：不修改测试断言本身以外的任何 runtime 文件；不删除既有 handoff 内容，只追加/精确补齐所需文案。
  - STOP 条件：若补齐文案会与 [`AGENTS.md`](../AGENTS.md) 或 [`STATUS.md`](../STATUS.md) 的事实源纪律冲突（例如被迫在 handoff.md 写入本应属于 META 的机器状态），返回 `CONTRACT GAP`，不强行绕过。
- **完成判据**：合同文本无开放选择，可直接机械执行。

### G10.5 Authorized implementation

- 严格按 G10.4 冻结的精确写集执行最小修改。
- 不得顺手修复其他发现的问题；其他改进候选只登记，不实现。
- **完成判据**：`diff` 范围（用文件读取比对，不用 Git）与冻结写集完全一致。

### G10.6 Fresh STATIC_REVIEW

- 以“重置角色”方式独立复读刚修改的文件，确认修改未扩大范围、未改变既有语义、未引入 Git/GitHub 副作用。
- **完成判据**：`PASS`（High=0, Medium=0）或精确 `REVISE`/`BLOCKED` 并说明原因。

### G10.7 Exact VERIFY

- 精确重跑 G10.2 的两条 selector；若均 PASS，追加执行：
  ```
  python -m pytest tests/f09 -q
  python -m pytest -q
  ```
- 记录每条命令的 cwd、exit code、collected/passed/failed/errors/skipped、耗时。
- **完成判据**：两条 sanity selector 均 passed；`tests/f09` 计数与 [`g6-task9p-total-gate-roll-up-adjudication.md`](g6-task9p-total-gate-roll-up-adjudication.md) 记录的 1172 一致；全仓命令有完整账本（无论是否全绿）。

### G10.8 Fresh EVIDENCE_REVIEW

- 独立判断 G10.7 证据是否支持把被选单元 freeze，并明确说明是否仍有 UNKNOWN/REQUIRES_EXTERNAL_DECISION 项未解除。
- **完成判据**：`PASS`/`REVISE`/`BLOCKED` 三选一，并给出直接证明与明确未证明清单。

### G10.9 Freeze / closeout

- 唯一写集：新建 `plans/g10-r1-readiness-and-sanity-closeout.md`，汇总 G10.0–G10.8 全部证据；精确、有限更新 [`plans/production-implementation-control.md`](production-implementation-control.md)（仅追加一个 G10 小节，不改写既有 G6–G9/§8.7/§8.8）。
- 给出唯一裁决（四选一）：
  - `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`
  - `REVISE — LOCAL GOVERNANCE GAP`
  - `BLOCKED — MATERIAL READINESS GAP`
  - `AUTHORIZATION_REQUIRED — RETAINED BUSINESS DECISION`
- **完成判据**：裁决唯一、写集精确、non-inference boundaries 完整列出。

### G10.10 F10 Go/Hold/Reject

- 仅在 G10.9 给出裁决后，按 [`g10-next-governance-milestone-plan.md`](g10-next-governance-milestone-plan.md) §7 的 Go/Hold/Reject 条件三选一。
- `GO` 只授权进入 F10 INVENTORY/ADMISSION，不授权任何实现。
- **完成判据**：三选一裁决 + 一句话理由 + 若非 GO，写明解除条件。

---

## 2. STOP / BLOCKED 判定（命中即停，不绕过）

- 任何操作可能触达 Git 或 GitHub → 直接 `BLOCKED`，不尝试执行一次去验证。
- G10.1 发现任何 `BLOCKED_BY_PROHIBITION`（例如需要部署环境、密钥、远端同步）→ 登记为 G10.10 的 Hold/Reject 依据，不在本轮local工作中强行满足。
- G10.4 合同与事实源纪律冲突 → 返回 `CONTRACT GAP`，交回用户裁决，不强行编造文案。
- 任一 pytest 命令 collection error → 停，归类（product defect / test defect / contract gap / environment failure），不反复微调后静默重跑。
- 发现两个 sanity 失败与 F09 存在因果关系 → 停止 G10.3，升级为 `BLOCKED — MATERIAL READINESS GAP`，不得继续按“非 F09”默认路径推进。

---

## 3. 单次对话完成的输出要求

对话结束前必须给出：

1. 十一个子 Gate 的最终状态（`PASS`/`REVISE`/`BLOCKED`/`AUTHORIZATION_REQUIRED`/`NOT REACHED`）；
2. 已读文件清单、已修改/新建文件清单；
3. 完整命令账本（命令、cwd、exit code、计数、耗时）；
4. G10.9 唯一裁决与 non-inference boundaries；
5. G10.10 唯一裁决（Go/Hold/Reject）；
6. 精确状态标记：`LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION`。

不得在最终输出中把任何子 Gate 的 PASS 静默升级为整体项目完成或生产就绪声明。
