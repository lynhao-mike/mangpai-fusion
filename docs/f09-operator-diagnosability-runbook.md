# F09 Operator Diagnosability Runbook

- 适用范围：具有合法 `artifact_root` 且由 `run_f09_slice()` 形成受控结果的 F09 run
- schema：`f09.operator-phase-observation-log.v1`
- 本地边界：**LOCAL ONLY / NOT PUSHED**
- 治理边界：本 runbook 不证明部署、发布、性能、跨平台运行、Git/GitHub 同步或 F10 可启动；**HOLD F10 保持**

## 1. 固定目录与文件定位

每个受控 run 的 phase observation log 位于：

```text
<artifact_root>/operator-diagnostics/<identity_sha256>.json
```

`identity_sha256` 是以下 bounded JCS material 的 SHA-256 hex：

```text
{
  "schema_version": "f09.operator-phase-observation-locator.v1",
  "case_id": request.case_id,
  "request_id": request.request_id,
  "attempt_id": request.attempt_id,
  "mode": request.mode
}
```

操作员有两种发现方式：

1. 已知四项 identity 时，按上述算法计算 digest 并精确定位文件；
2. identity 不完整时，扫描 `<artifact_root>/operator-diagnostics/*.json`，解析文件内明文 identity 后匹配。

禁止直接把未经路径安全验证的 `case_id`、`request_id` 或 `attempt_id` 拼入路径。文件名 digest 只负责安全稳定寻址，文件内 identity 才是 run 身份材料。

## 2. 文件完整性与 schema

文件必须可由 bounded JCS parser 解析，并满足重新 canonicalize 后 bytes 与原文件完全一致。顶层结构为：

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

允许的 phase 顺序是已实际到达 phase 的前缀：

```text
SOURCE_PREFLIGHT → EVIDENCE → DECISION → TRACE → ARTIFACT
```

不得自行排序、去重或补造 observation。

## 3. 判断成功与 terminal failure

### 3.1 完成 run

完成 run 必须同时满足：

- `completed` 为 `true`；
- `stopped_at` 为 `null`；
- observations 恰按顺序覆盖五个 phase；
- 五项 status 均为 `SUCCEEDED`；
- 不存在 `FAILED` 或 `REJECTED` observation。

### 3.2 停止 run

停止 run 必须同时满足：

- `completed` 为 `false`；
- `stopped_at` 是五个 phase 之一；
- 恰有一个 status 为 `FAILED` 或 `REJECTED` 的 terminal observation；
- terminal observation 是 observations 最后一项；
- terminal `phase == stopped_at`；
- terminal `issue_codes` 非空，且每项都是非空字符串；
- 每项 observation 的 `case_id`、`mode` 与顶层 identity 一致。

若以上闭合条件不成立，不得把文件解释为可靠的受控 run 诊断结果，应按诊断材料完整性失败处理。

## 4. 常见 phase 解释

| terminal phase | operator 直接可见含义 | 后续读取 |
|---|---|---|
| `SOURCE_PREFLIGHT` | 请求在 owner 调用前被拒绝 | 读取 terminal `status` 与 `issue_codes` |
| `EVIDENCE` | evidence owner 形成 typed F09 failure | 读取 terminal `issue_codes` |
| `DECISION` | decision owner 形成 typed F09 failure | 读取 terminal `issue_codes` |
| `TRACE` | trace 或 projection 路径形成 typed F09 failure | 读取 terminal `issue_codes` |
| `ARTIFACT` | artifact phase 返回未闭合状态或 issue | 联查 artifact manifest 与 attempt ledger |

phase log 不持久化异常 diagnostic 原文；不要从缺失的原文推断异常细节。

## 5. 联查 artifact attempt ledger

当 terminal phase 是 `ARTIFACT` 时，phase log 用于确认 run identity、terminal phase、terminal status 与 issue identity；artifact manifest/attempt ledger 用于进一步判断写入失败及重试链。

对目标 artifact record 的 attempt 依次核对：

1. **失败闭合**
   - `outcome == "FAILED"`；
   - `finished_at` 非空；
   - `observed_digest is None`；
   - `error_class` 非空；
   - `error_message_digest` 非空。
2. **身份关联**
   - attempt 的 `artifact_id` 与所属 record 一致；
   - `input_snapshot_refs` 与本次 request 一致；
   - `idempotency_key` 与本次 artifact set key 的 canonical digest 一致。
3. **重试链**
   - 首次 attempt 的 `attempt_number == 1` 且 `retry_of_attempt_id is None`；
   - 后续 attempt number 连续递增；
   - 每次 retry 的 `retry_of_attempt_id` 精确指向直接前驱 attempt；
   - 重试后 manifest 必须通过公共 validator。

phase observation log 与 artifact attempt ledger 是互补材料：前者覆盖所有受控 phase，后者只提供 artifact 写入尝试的细节。不得用 attempt ledger 反推未到达 artifact phase 的 failure。

## 6. 持久化失败的调用方表现

诊断目录创建、canonicalization、write、flush、fsync、replace 或 readback mismatch 任一失败，都必须 fail-closed 抛出：

```text
F09WriteError(
  "APPLICATION.OBSERVATION_PERSISTENCE_FAILED",
  "/artifact_root/operator-diagnostics",
  <bounded diagnostic>
)
```

调用方收到该 typed error 时，不得把本次调用当作已具有可靠持久化诊断材料的正常 `F09RunResult`。replace 前失败应不留下已提交目标；replace 后 readback mismatch 可能已存在目标文件，但该文件不得视为已验证材料。

## 7. `artifact_root=None` 唯一例外

当 preflight issue 是 `APPLICATION.ARTIFACT_ROOT_REQUIRED` 时，没有合法持久化 owner。该 rejection 只存在于内存返回值，明确位于物理持久化适用域之外。

禁止 fallback 到：

- 当前工作目录；
- repository root；
- 用户目录；
- 系统或全局临时目录。

缺少文件在这一精确场景中表示“没有合法持久化目标”，不表示持久化机制对合法 root 失效。

## 8. 非受控异常边界

owner 抛出的非 `F09Error` 继续原样传播，未形成受控 `_result()`，本轮不宣称为其持久化 phase log。不得因未发现 phase log 就把非受控异常改判为某个受控 terminal phase。

## 9. 证据与禁止推导

本 runbook 直接支持的 operator 判断仅限：

- 合法 root 下受控 run 的 identity 与已到达 phase；
- completed 或 stopped 状态；
- 唯一 terminal phase/status/issue identity；
- artifact phase 与 attempt ledger 联查后的失败类别、输入/idempotency identity 和 retry predecessor chain。

不得据此推导：

- F09 完全生产就绪；
- 外部密钥、权限或服务已就绪；
- 性能、安全基准、跨平台兼容或部署发布已证明；
- Git provenance 或 GitHub 同步状态；
- F10 已获授权、可以启动或可以解除 HOLD。
