# G10-R2-A2 · F09 Phase Observation Persistence Contract

- 记录日期：2026-07-27（Asia/Shanghai）
- Gate：G10-R2-A2 CONTRACT
- 上游历史：`plans/g10-r2-f09-operator-diagnosability-contract.md` 的 `AUTHORIZATION_REQUIRED` 与 STOP 事实保持不变
- 本轮授权来源：用户后续独立授权，允许最小修改 `engine/f09/`，并允许必要时最小调整 `tests/f09/test_application_opt_in.py` 与 `tests/f09/test_current_run_authority.py` 的临时路径 fixture
- 本地边界：**`LOCAL ONLY / NOT PUSHED`**
- 远端边界：禁止任何 Git/GitHub 操作；本合同不授予 GitHub 写权限
- F10 边界：**`HOLD F10` 保持；F10 未授权且不得启动**

## 1. Common Gate Record

- Gate：G10-R2-A2 CONTRACT
- Owner role：Controller / Contract Author
- Fresh reviewer role：Logical Fresh Contract Reviewer（不得以实现结果倒推合同）
- Authorization envelope：仅限本合同第 4 节列出的本地文件与命令；禁止 Git/GitHub；禁止修改公开 F09 ABI
- Activation condition：原 G10-R2-A 已按当时授权合法 STOP，且用户随后明确授予新的独立 production/test 最小修改权限
- Remaining inactive grants：IMPLEMENT、STATIC_REVIEW、VERIFY、EVIDENCE_REVIEW、FREEZE、HANDOFF；仅在前一 Gate PASS 后按最小范围激活
- Required inputs：原 G10-R2-A 合同、`engine/f09/application.py`、`engine/f09/errors.py`、`engine/f09/canonical_json.py`、`engine/f09/artifacts.py`、两个已授权既有测试文件及 `tests/f09/conftest.py` 的真实 fixture
- Observed facts：所有受控 `run_f09_slice()` 返回均经私有 `_result()`；公开 DTO/签名/导出存在精确冻结断言；vertical fixture 已使用 `tmp_path`；`test_current_run_authority.py` 通过 monkeypatch 隔离 legacy owner；`artifact_root=None` 时不存在合法持久化目标
- Inferences：可通过私有模块和 `_result()` 单点副作用闭合 D1，而无需改变公开 DTO、函数签名、导出或 artifact role
- Unknowns：实现前尚无 RED/GREEN 动态证据；全套回归状态尚未验证
- Required outputs：冻结 schema、locator、原子写入、failure routing、精确写集、TDD selectors 与 non-inference boundaries
- Falsifiers：需要新增公开字段/参数/导出/role；需要 cwd fallback；无法保证 terminal observation 唯一；无法在合法 root 下原子持久化；需触碰保护文件或 Git/GitHub
- STOP conditions：见第 10 节
- Verdict：**`PASS`（合同设计可进入 TDD RED；不代表实现或行为 PASS）**
- Direct evidence boundary：只证明设计与当前源码切入点相容
- Forbidden inference boundary：不得推导持久化已实现、测试已通过、D1 已满足、F09 production ready 或 F10 可启动
- Minimum next authorization：已由用户预授权的专用测试 RED；RED 必须先于 production implementation

## 2. 目标与验收口径

在不改变 F09 公开 ABI 的前提下，为每次提供合法 `artifact_root` 且通过 `_result()` 形成受控结果的 F09 run 持久化完整 phase observation log，使 operator 可仅凭落盘材料识别：

1. run identity：`case_id`、`request_id`、`attempt_id`、`mode`；
2. 已到达 phase 的有序 observation；
3. terminal phase、terminal status 与 issue identity；
4. run 是成功完成还是停在某 phase；
5. 与现有 artifact attempt ledger 联合时，可继续判断 artifact 写失败类别、输入摘要身份和 retry chain。

本合同采用原 G10-R2-A 的 D1–D5，不弱化 D2–D5。D1 的精确适用域为：

> 对所有 `artifact_root` 为合法 `Path` 且 `run_f09_slice()` 经 `_result()` 返回的受控 run，必须存在一份可解析、canonical、readback 已验证的 phase observation log。若 `stopped_at is not None`，其中必须且仅能有一个 terminal observation，且与 `stopped_at`、`case_id`、`mode` 一致。

## 3. 非目标与兼容边界

本轮明确不做：

- 不给 `F09RunRequest`、`F09Observation`、`F09RunResult`、`F09RunExecutionResultV1` 增删字段；
- 不改变 `run_f09_slice()` 或 `run_f09_slice_with_execution_authority_v1()` 的公开签名、类型提示或返回 DTO；
- 不改变 `engine.f09.__all__`；
- 不新增或改变 `ArtifactRecord.artifact_role`；
- 不把 observation log 伪装成业务 artifact manifest 的新 record；
- 不持久化 typed error 的 `diagnostic` 原文，避免扩大敏感错误文本暴露面；
- 不建立数据库、全局 registry、后台线程、遥测服务或外部依赖；
- 不修改九份 Task 9-P 冻结文件、F01–F12 契约、`handoff.md`、`tools/README.md`；
- 不执行 Git 命令、GitHub 读写、部署、发布或远端同步；
- 不解除 `HOLD F10`。

“默认行为不变”的冻结解释：公开调用形式、返回对象结构、成功/受控业务 phase 结果及 owner 调用顺序不变；新增的唯一行为是对合法 `artifact_root` 写入诊断旁路文件。若诊断持久化本身失败，采用第 8 节 fail-closed 路由，不允许静默返回一个无法诊断的受控结果。

## 4. 精确本地写集

### 4.1 CONTRACT / implementation / tests

1. `plans/g10-r2-a2-f09-phase-observation-persistence-contract.md`（本文件）；
2. `engine/f09/operator_diagnostics.py`（新增私有实现模块）；
3. `engine/f09/application.py`（仅导入私有 helper，并在 `_result()` 单点调用）；
4. `tests/f09/test_operator_diagnosability_readiness.py`（新增专用 TDD 测试）；
5. `tests/f09/test_application_opt_in.py`（仅把真正执行新 I/O 的 request root 改为 `tmp_path`，并保持 `artifact_root=None` 用例）；
6. `tests/f09/test_current_run_authority.py`（已授权但仅在真实执行新 I/O 时修改；若 monkeypatch 隔离使其不需要改，保持原样）；
7. `docs/f09-operator-diagnosability-runbook.md`（仅在实现与测试证明确有必要时新增）；
8. `plans/g10-r2-f09-operator-diagnosability-report.md`（最终证据报告）；
9. `plans/g10-r1-readiness-and-sanity-closeout.md`（仅允许更新十二域第 7 行及其直接证据引用，不得改写其他行或历史裁决）。

### 4.2 明确排除

- `tests/f09/conftest.py` 已确认 `baseline_scenario_bundle(tmp_path)` 使用 `tmp_path / "f09-artifacts"`，不在写集；
- 原 `plans/g10-r2-f09-operator-diagnosability-contract.md` 保持历史原文，不倒写；
- 任何未列路径默认禁止修改。

## 5. 持久化 schema

载体使用 `canonicalize_bounded_jcs()` 支持的 `dict / tuple / str / bool / None`，禁止 JSON number。schema 精确为：

```text
{
  "schema_version": "f09.operator-phase-observation-log.v1",
  "case_id": <str>,
  "request_id": <str>,
  "attempt_id": <str>,
  "mode": <str>,
  "completed": <bool>,
  "stopped_at": <str | null>,
  "observations": (
    {
      "event": "F09_SLICE_PHASE",
      "case_id": <str>,
      "mode": <str>,
      "phase": <str>,
      "status": <str>,
      "issue_codes": (<str>, ...),
      "artifact_set_state": <str | null>
    }, ...
  )
}
```

冻结约束：

- `completed is (stopped_at is None)`；
- observations 保持 application 产生顺序，不排序、不去重；
- stopped run 的最后一项必须是唯一 terminal observation；
- terminal status 只能为 `FAILED` 或 `REJECTED`；
- terminal `issue_codes` 必须非空且成员均为非空字符串；
- completed run 不得包含 `FAILED` / `REJECTED` observation；
- observation 的 `case_id` 与 `mode` 必须逐项匹配顶层 identity；
- 不写入 exception diagnostic 原文；artifact attempt 的错误消息继续只以 digest 表达。

## 6. 安全 locator 与可发现性

不得把未经路径安全验证的 `case_id`、`request_id`、`attempt_id` 直接拼成目录名。locator identity material 为：

```text
{
  "schema_version": "f09.operator-phase-observation-locator.v1",
  "case_id": request.case_id,
  "request_id": request.request_id,
  "attempt_id": request.attempt_id,
  "mode": request.mode
}
```

对该 bounded JCS material 计算 SHA-256 hex，目标固定为：

```text
<artifact_root>/operator-diagnostics/<identity_sha256>.json
```

可发现性规则：

- operator 可扫描固定的 `operator-diagnostics/` 目录并读取每个文件中的明文 identity；
- runbook 可给出同一 identity material 的确定性 locator 算法；
- locator 只用于文件名安全与稳定寻址，不替代文件内 identity；
- 同一 identity 的再次写入采用原子替换，形成该 attempt identity 的当前完整 observation log；不同 `attempt_id` 形成不同文件。

## 7. 写入与 readback 语义

私有实现模块必须：

1. 验证 `artifact_root` 是 `Path`；
2. 创建 `<artifact_root>/operator-diagnostics/`；
3. canonicalize schema material；
4. 在目标同目录创建唯一临时文件；
5. write、flush、`os.fsync()`；
6. `os.replace()` 原子提交；
7. readback 目标 bytes；
8. 要求 readback bytes 与预期 canonical bytes 完全相等；
9. 失败时尽力清理未提交临时文件；
10. 不删除或修改任何业务 artifact 文件。

实现可复用现有模式，但不得调用 `engine/f09/artifacts.py` 的私有 `_atomic_write_verified()`，避免跨模块依赖另一模块私有符号；最小重复原子写入骨架优于扩大公共 ABI。

## 8. Failure routing

### 8.1 合法 root 下写入失败

任何目录创建、canonicalization、写入、flush、fsync、replace 或 readback mismatch 必须 fail-closed，抛出：

```text
F09WriteError(
  "APPLICATION.OBSERVATION_PERSISTENCE_FAILED",
  "/artifact_root/operator-diagnostics",
  <bounded diagnostic>
)
```

其中 diagnostic 仅用于内存异常，不得另写原始异常文本到日志。该 typed error 证明诊断材料未可靠提交；调用方不得收到一个被误认为已有持久化证据的正常 `F09RunResult`。

### 8.2 `artifact_root=None` 唯一例外

`APPLICATION.ARTIFACT_ROOT_REQUIRED` preflight rejection 发生时没有合法持久化 owner。本合同禁止：

- fallback 到 cwd；
- fallback 到 repository root；
- fallback 到用户目录或全局临时目录；
- 为满足测试伪造持久化成功。

因此该单一 rejection 仍仅存在于内存返回值，明确标记为 D1 适用域之外。它直接证明的是“缺少持久化目标”，不是“持久化机制失效”。所有其他 preflight rejection 只要 request 提供合法 root，均必须持久化。

### 8.3 非受控异常

当前 owner 抛出的非 `F09Error` 继续原样传播；因为未形成 `_result()`，本合同不宣称为其持久化 phase log。不得借本轮扩大 `run_f09_slice()` 的异常捕获面。

## 9. TDD 与验证 selectors

执行顺序冻结为：

1. 新增 `tests/f09/test_operator_diagnosability_readiness.py`，在 production 未实现状态运行并记录真实 RED；
2. RED 至少独立覆盖：
   - 合法 root 下 SOURCE_PREFLIGHT rejection 持久化；
   - EVIDENCE / DECISION / TRACE / ARTIFACT terminal observation 持久化；
   - success 的五 phase 完整持久化；
   - canonical bytes 与确定性 locator；
   - 原子 write/readback failure 的 typed fail-closed；
   - `artifact_root=None` 不产生 fallback 文件；
   - D2 terminal issue identity；
   - D3 FAILED attempt closure；
   - D4 input/idempotency identity；
   - D5 retry predecessor chain；
3. 最小 production implementation；
4. 专用测试 GREEN；
5. `pytest tests/f09 -q`；
6. `pytest -q`；
7. 最终报告写入后，新鲜重跑上述三层验证。

任何 collection error 等于零行为证据。任何 repair 都使此前 STATIC_REVIEW 与 VERIFY 失效，必须重新审查与重跑。

## 10. STOP 条件

出现任一项即停止当前 Gate 并分类：

- 需要修改公开 DTO 字段、公开函数签名、`__all__` 或 artifact role；
- 需要在 `artifact_root=None` 时写入任意 fallback；
- 需要修改本合同写集之外的文件；
- 需要修改九份 Task 9-P 冻结文件或启动 F10；
- 需要 Git/GitHub、部署、远端服务或不可逆外部副作用；
- 专用测试无法在不弱化 D1–D5 的情况下表达；
- persistence failure 被静默吞掉；
- terminal observation 不唯一或 issue identity 可为空；
- collection error、环境错误或测试结果无法完整核对；
- 结论需要超出本地、当前代码与当前测试证据。

## 11. 逻辑新鲜合同自审

复核时重置“新增持久化必然需要公开 ABI”与“所有 fixture 都需修改”两项旧假设，只接受本轮源码证据：

1. `_result()` 是全部受控返回的单一切入点；
2. 私有 helper 不要求公开字段、参数、导出或 role；
3. `tests/f09/conftest.py` 已使用临时 root；
4. `test_current_run_authority.py` 的 legacy owner 被 monkeypatch，授权不等于必须修改；
5. `test_application_opt_in.py` 的真实 `run_f09_slice()` 调用使用字面 `Path("artifacts")`，需要最小临时路径隔离；
6. `artifact_root=None` 在逻辑与物理上没有合法 persistence owner，必须作为显式例外而非隐藏 fallback；
7. fail-closed 是 D1 保证成立的必要条件；best-effort 吞错无法证明落盘材料存在。

新鲜自审 verdict：**`PASS`**。本 PASS 只允许进入专用 TDD RED，不证明 implementation、STATIC_REVIEW、VERIFY、D1 readiness 或最终 FREEZE。

## 12. Gate 裁决与唯一下一合法动作

G10-R2-A2 CONTRACT verdict：**`PASS`**。

唯一下一合法动作：新增专用 readiness 测试并在未实现 production persistence 的状态运行精确 selector，记录真实首次 RED；不得先写 production 实现。

**`LOCAL ONLY / NOT PUSHED`**。本受控会话不得执行任何 GitHub-mutating operation；`HOLD F10` 未解除。
