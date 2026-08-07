# G10-R2-A · F09 Operator Diagnosability Readiness Contract

- 记录日期：2026-07-27（Asia/Shanghai）
- Gate：G10-R2-A CONTRACT
- 裁决：**`AUTHORIZATION_REQUIRED — 需要新的独立 CONTRACT 授权才能修改 engine/f09`**
- 本地状态：**`LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION`**
- 后续 Gate：**未授权；按 STOP 条件停止于 G10-R2-A**

## 1. 目标

建立 F09 operator diagnosability 的最低可机械验证合同：给定一次失败或拒绝的 F09 run，operator 应能仅凭已持久化的 phase observation、artifact attempt ledger 与 typed error 投影，不读取源码，判断失败 phase、错误类别、失败输入/摘要身份及重试链。

本合同只盘点现有冻结实现并裁决其是否具备进入 G10-R2-B 的前提；不修改 F09 production 行为。

## 2. 非目标与 non-inference boundaries

本合同不做且不得用于推导：

- 不启动或隐含启动 F10，不解除 `HOLD F10`；
- 不修改 `engine/f09/` 下任何生产逻辑、字段、签名或默认行为；
- 不修改 `tests/f09/` 下任何既有测试；
- 不修改九份 Task 9-P 专项冻结文件、`handoff.md`、`tools/README.md` 或 F01–F12 契约；
- 不证明 F09 production ready、部署、发布、性能、安全、跨平台、Git provenance、GitHub 同步或全仓正确性；
- application 返回的内存对象不等于已持久化记录；
- artifact attempt ledger 的持久化不等于 phase observation 已持久化；
- `issue_code` 不等于 Python error class，`error_class` 也不等于 retryability policy；
- 本合同的 `AUTHORIZATION_REQUIRED` 不授权任何后续生产修改。

## 3. 冻结写集白名单

本轮实际启用写集仅为：

1. `plans/g10-r2-f09-operator-diagnosability-contract.md`（新建，本文件）。

以下初始候选路径因 STOP 触发而未启用：

1. `tests/f09/test_operator_diagnosability_readiness.py`；
2. `docs/f09-operator-diagnosability-runbook.md`；
3. `plans/g10-r2-f09-operator-diagnosability-report.md`；
4. `plans/g10-r1-readiness-and-sanity-closeout.md`。

禁止任何 Git 命令及任何 GitHub 读写或服务端操作。

## 4. 权威源码字段盘点

### 4.1 Typed error surface

`engine/f09/errors.py` 定义冻结基类 `F09Error` 及具体类别 `F09IntegrityError`、`F09SourceError`、`F09ContractError`、`F09WriteError`。

可诊断字段：

- `issue_code: str`：非空；
- `field_path: str`：非空；
- `diagnostic: str`：允许为空；
- Python 具体异常类：可区分 integrity/source/contract/write 类别。

限制：application 捕获 `F09Error` 时只把 `error.issue_code` 投影到 phase observation；`field_path`、`diagnostic` 与具体异常类不进入该 observation。

### 4.2 Phase observation 与 run result surface

`engine/f09/application.py` 的公开 `F09Observation` 字段：

- `event`，固定语义 `F09_SLICE_PHASE`；
- `case_id`；
- `mode`；
- `phase`：`SOURCE_PREFLIGHT` / `EVIDENCE` / `DECISION` / `TRACE` / `ARTIFACT`；
- `status`：`SUCCEEDED` / `FAILED` / `REJECTED`；
- `issue_codes`；
- `artifact_set_state`。

`F09RunResult` 另含：

- `request`；
- `evidence`；
- `decision`；
- `trace`；
- `statement_set`；
- `manifest`；
- `observations`；
- `stopped_at`。

直接观察：`run_f09_slice()` 为每个已到达 phase 追加 observation，失败或拒绝时设置 `stopped_at` 并返回 `F09RunResult`。

持久化核对：全仓 Python production 搜索中，`F09Observation` / `F09_SLICE_PHASE` 仅见于 `engine/f09/application.py` 的构造与包导出；未发现进入 artifact canonical material、文件写入或其他持久化 consumer。测试读取 `result.observations` 只能证明内存公开产出，不证明持久化。

### 4.3 Artifact attempt ledger surface

`engine/f09/artifacts.py` 的 `ArtifactWriteAttempt` 字段：

- `attempt_id`；
- `artifact_id`；
- `idempotency_key`；
- `attempt_number`；
- `retry_of_attempt_id`；
- `input_snapshot_refs`；
- `started_at`；
- `finished_at`；
- `outcome`：`SUCCEEDED` / `FAILED` / `UNKNOWN`；
- `observed_digest`；
- `error_class`；
- `error_message_digest`。

所属 `ArtifactRecord` 还提供：

- `artifact_id`、`artifact_role`、`track`、`case_id`、`statement_set_id`、`run_id`；
- `path_locator`、`schema_version`、`expected_digest`、`observed_digest`；
- `state`、`attempts`、`issue_ids`。

`ArtifactSetManifest` 还提供：

- `manifest_id`、`key`、`records`、`state`、`digest`、`detected_issues`。

持久化核对：`canonicalize_artifact_records()` 明确把 attempt 的上述字段（含 `input_snapshot_refs`、`outcome`、`error_class`、`error_message_digest`）纳入 canonical material；`_attempt_outcome_closed()` 明确要求 `FAILED` attempt 有 `finished_at`、非空 `error_class`、非空 `error_message_digest`，且无 `observed_digest`。

限制：artifact attempt 可诊断写入失败与输入/重试身份，但不能覆盖在 EVIDENCE、DECISION 或 TRACE phase 中、尚未进入 artifact 写阶段的失败；它也不携带 application phase 字段。

## 5. 拟冻结的最低诊断标准与 pytest selector 设计

以下五条均可转化为独立 pytest 断言，但 D1 因生产持久化缺口当前不可满足，故整个列表不能进入 G10-R2-B：

### D1 · 失败 phase 必须可由持久化记录唯一定位

对任意 `stopped_at is not None` 的 F09 run，持久化诊断材料必须包含且仅包含一个 terminal observation，其 `phase == stopped_at`，其 `status` 为 `FAILED` 或 `REJECTED`，并携带同一 `case_id` 与 `mode`。

拟议测试：执行现有公开失败路径，读取其实际持久化产物而非仅检查 `F09RunResult.observations`，断言上述关联成立。

当前判定：**不可满足**。现行源码只返回内存 `F09Observation`，未发现 observation 持久化路径。

### D2 · terminal phase observation 必须携带错误 identity

每个 `FAILED` / `REJECTED` terminal observation 的 `issue_codes` 必须为非空 tuple，且每个成员为非空字符串；operator 可据此识别失败 issue identity。

拟议测试：覆盖现有 preflight rejection、caught typed F09 error、projection validation failure 与 manifest issue failure，逐一断言 terminal observation 的 `issue_codes`。

当前判定：内存公开结果可测；持久化前提受 D1 阻断。

### D3 · 每个 FAILED artifact attempt 必须闭合错误摘要

每个 `outcome == "FAILED"` 的 `ArtifactWriteAttempt` 必须有非空 `finished_at`、非空 `error_class`、完整 `error_message_digest`，同时 `observed_digest is None`。

拟议测试：直接使用现有 artifact coordinator 的真实写失败产出，并经现有 manifest validation / canonicalization 公开路径断言字段闭合。

当前判定：源码存在直接强约束，可机械验证。

### D4 · 每次 artifact attempt 必须可关联输入与幂等身份

每个 attempt 必须有非空 `attempt_id`、`artifact_id`、`idempotency_key`，非空 `input_snapshot_refs`；attempt 的 `artifact_id` 必须匹配所属 `ArtifactRecord.artifact_id`，记录的 `case_id`、`track`、`run_id` 提供 run 级定位。

拟议测试：对 coordinator 真实 manifest 的所有 records/attempts 逐项断言，并确认 canonical material 包含这些字段。

当前判定：源码与现有 validator 提供直接约束，可机械验证。

### D5 · 重试历史必须形成无歧义前驱链

同一 artifact record 的第一个 attempt 必须 `attempt_number == 1` 且 `retry_of_attempt_id is None`；后续 attempt 的 `attempt_number` 必须顺序递增，`retry_of_attempt_id` 必须精确等于前一 attempt 的 `attempt_id`。

拟议测试：使用现有失败后 retry 的真实 coordinator 产出，断言完整链和 manifest validation 成功。

当前判定：源码存在直接强约束，可机械验证。

## 6. STOP 条件与实际触发

冻结 STOP 条件：

- 诊断标准失败根因是生产代码缺少字段或持久化行为，而非文档缺口；
- 需要修改 `engine/f09/` 的任何签名、字段或默认行为；
- 测试出现新增失败或 collection error；
- 标准无法从实际源码字段推导；
- 动作可能修改 Git/GitHub 或越出写集；
- 权威源码与合同出现无法消解的冲突。

实际触发：**第一项与第二项**。D1 要求 operator 仅凭已持久化记录定位失败 phase；现行 `F09Observation.phase/status/issue_codes` 只存在于内存 `F09RunResult` 返回面，未进入 artifact canonical material 或其他持久化路径。runbook 只能解释已有字段，不能把不存在的持久化行为补出来。闭合该缺口至少需要修改 `engine/f09/` 的生产持久化行为、载体或签名，而这些均在本任务中明确禁止。

失败分类：**product diagnosability / persistence visibility gap**，不是文档缺口、测试缺陷或 collection error。

## 7. 逻辑新鲜独立自审

复核方法：重置“提示词示例字段可能已存在”的假设，只接受本轮实际读取与全仓精确搜索结果；分别重新核对 typed error、application observation、artifact attempt canonical material 三条证据链。

复核结果：

1. `phase`、`status`、`issue_codes` 确实来自 `F09Observation` 实际字段；
2. `stopped_at` 确实来自 `F09RunResult` 实际字段；
3. `error_class`、`error_message_digest`、`input_snapshot_refs`、`idempotency_key` 与 retry 字段确实来自 `ArtifactWriteAttempt`；
4. `canonicalize_artifact_records()` 确实持久化 attempt ledger material；
5. production 搜索未发现 `F09Observation` / `F09_SLICE_PHASE` 的持久化 consumer；仅有 application 构造、包导出和 tests 内存断言；
6. attempt ledger 不能推导尚未进入 ARTIFACT phase 的 EVIDENCE / DECISION / TRACE failure；
7. 新增 runbook 无法弥补缺失的 production persistence behavior。

独立自审 verdict：**`PASS`（对本合同事实盘点与 STOP 裁决）**。该 PASS 不表示 operator diagnosability readiness PASS，也不允许进入 G10-R2-B。

## 8. Gate 裁决、已完成范围与唯一下一合法动作

G10-R2-A 最终裁决：

> **`AUTHORIZATION_REQUIRED — 需要新的独立 CONTRACT 授权才能修改 engine/f09`**

已完成：权威材料读取、字段盘点、五条最低标准设计、持久化核对、逻辑新鲜独立自审、STOP 证据落盘。

未开始：G10-R2-B TDD RED、G10-R2-C 实现/验证、G10-R2-D 报告/十二域更新。未创建专用测试、runbook 或最终报告；未运行任何 pytest；十二域表第 7 行保持 `REQUIRES_LOCAL_GATE`。

唯一下一合法动作：由用户另行发起并授权一个新的独立 CONTRACT，明确允许为 phase observation 设计最小持久化载体/路径及相应 production write set、兼容边界和验证 selectors。在该授权出现前，不得修改 `engine/f09/`，不得以文档或弱化测试替代生产持久化缺口。

**`LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION`**

`HOLD F10` 未被解除；F10 未获授权且未启动。
