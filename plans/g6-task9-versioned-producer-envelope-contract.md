# G6 / Task 9 versioned producer / execution-envelope 合同

- **Unit：** Task 9 versioned producer / execution envelope（仅合同）
- **Gate：** `CONTRACT — REVISE / ready for fresh independent read-only review`
- **现行总状态：** P-1 authority-contract `PASS`（仅该合同 Gate）；P-2 `BLOCKED`；Task 9-P `BLOCKED`；Task 9 amendment `STILL_OPEN`。
- **实现授权：** 否。本文、其作者自检或任何 review `PASS` 都不构成 production、tests、Python、pytest、Git 或 GitHub 操作授权。
- **唯一作者写集：** 本文件。

## 1. 目标、权威输入与非目标

本合同冻结一个与 legacy Task 9 ABI 隔离的、版本化的 producer envelope。它只能消费 P-1 owner 实际返回的 run-artifact lifecycle result，并在满足所有串行 Gate 时暴露已验证的 `PreprodRunAuthority`；它不创建 current-run identity，不成为 feedback binder 或 learning caller。

权威输入按冲突优先级为：

1. [`plans/g6-task9p-prerequisite-authority-contract.md`](g6-task9p-prerequisite-authority-contract.md) 的 P-1/P-2/Task 9-P 现行 Gate；
2. [`plans/g6-task9p-p2-current-run-identity-authority-adjudication.md`](g6-task9p-p2-current-run-identity-authority-adjudication.md) 附录 B 的 producer-owned current-run provenance 与 P-2 禁止边界；
3. [`plans/g6-task9p-p2-upstream-contract-reconcile-adjudication.md`](g6-task9p-p2-upstream-contract-reconcile-adjudication.md) 第 10.4、13–18 节的现行 versioned key、feedback adapter 与 envelope 约束；
4. [`plans/g6-task8-r39-feedback-adapter-contract.md`](g6-task8-r39-feedback-adapter-contract.md) 的 feedback consumer adapter Gate；
5. [`plans/g6-task9-application-orchestrator-contract.md`](g6-task9-application-orchestrator-contract.md) 的 legacy ABI；
6. 运行时 public surface：[`engine/f09/application.py`](../engine/f09/application.py)、[`engine/f09/artifacts.py`](../engine/f09/artifacts.py)。

非目标：P-1 lifecycle/verifier 实现、R39 feedback adapter 实现、P-2 admission、feedback binding、learning eligibility、artifact private serializer/digest、legacy API 修改、任何测试或运行时执行。

## 2. 冻结的 public ABI 与 legacy 隔离

future implementation 仅可在 [`engine/f09/application.py`](../engine/f09/application.py) 定义并由 [`engine/f09/__init__.py`](../engine/f09/__init__.py) export 下列 surface：

```python
@dataclass(frozen=True)
class F09RunExecutionResultV1:
    run_result: F09RunResult
    preprod_authority: PreprodRunAuthority | None
    unsupported_reason: Literal["STAGED_L6_UNSUPPORTED"] | None


def run_f09_slice_with_execution_authority_v1(
    request: F09RunRequest,
    *,
    run_artifact_request: RunArtifactSetRequestV1,
    existing_run_manifest: ArtifactSetManifest | None,
    gate_inputs: tuple[GateEvaluationInput, ...],
    competition_input: CompetitionInput,
    root_input: RootInput,
    timing_input: TimingInput,
) -> F09RunExecutionResultV1: ...
```

1. [`F09RunExecutionResultV1`](../engine/f09/application.py) 必须是 frozen dataclass，字段、顺序、类型、构造顺序与 export 均精确如上。
2. [`F09RunRequest`](../engine/f09/application.py)、[`F09RunResult`](../engine/f09/application.py) 与 [`run_f09_slice()`](../engine/f09/application.py) 均保持字节级 ABI / constructor / signature / 行为兼容；不得添加 field、keyword input、authority side channel 或 observation cache。
3. `run_artifact_request` 与 `existing_run_manifest` 仅为 versioned callable 的 keyword-only 输入，不进入 legacy request，也不由 caller label、feedback item、legacy statement manifest 或 P-2 构造。
4. `run_artifact_request` 必须为 P-1 已验证的 [`RunArtifactSetRequestV1`](../engine/f09/artifacts.py)，且其 `key` 必须为 versioned [`RunArtifactSetKeyV1`](../engine/f09/artifacts.py)。不得扩展、别名、转换或复用 legacy [`IdempotencyKey`](../engine/f09/artifacts.py)。

## 3. 版本化 producer 处理顺序与所有权

1. versioned callable 必须首先以原参数、恰一次调用 [`run_f09_slice()`](../engine/f09/application.py)，并把该 returned object 原样放入 `run_result`；不得复制、重建或 mutation。
2. 仅当 `run_result.stopped_at is None`，才可用 `request.artifact_root`、`run_artifact_request`、`existing_run_manifest`、`request.attempt_id` 与 `request.now` 调用 P-1 public [`coordinate_run_artifact_set_v1()`](../engine/f09/artifacts.py) 恰一次。
3. 返回的 run manifest 必须是该 coordinator 的实际 returned object；不得从 legacy statement manifest、filesystem discovery、caller input、P-2、feedback 或缓存重建、重签、替换或借用。
4. Task 9 不拥有 run id、run key、run root、manifest id、record、attempt、payload digest、private serializer 或 verifier；只可消费 P-1 public lifecycle result，并可调用 public [`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py) 验证该 returned manifest。
5. `existing_run_manifest` 只能为相同 versioned key / run 的 P-1 H1 previous result 或 `None`。任何 legacy-key/run-key cross-use、case / track / run-id / refs / role / digest 不一致都 fail closed；不得写入、修复、relabel、borrow 或 fallback。

## 4. 分支语义与 authority mapping

1. disabled 或任一 legacy stop（`SOURCE_PREFLIGHT`、`EVIDENCE`、`DECISION`、`TRACE`、`ARTIFACT`）必须返回 `preprod_authority=None`、`unsupported_reason=None`；P-1 coordinator 和 verifier 调用数均为零。
2. P-1 coordinator 未返回 complete verified run graph，或 verifier 失败，必须 fail closed：`preprod_authority=None`、`unsupported_reason=None`，且 binder / eligibility / learning 调用数为零。
3. `STAGED_L6` 的 complete graph 分支必须返回 `preprod_authority=None` 与 `unsupported_reason="STAGED_L6_UNSUPPORTED"`；不得伪装为 `V5_V6_PREPROD`，不得调用 feedback、binder、eligibility 或 learning。
4. 现有 R39 adapter Gate 的 `PASS` 只允许 feedback owner 验证既有 authority；它不授予 Task 9 计算 `PreprodRunAuthority.content_digest` 的 public construction capability。由于反馈 owner 的 [`_preprod_authority_self_excluded_material()`](../engine/f09/feedback.py:1361) 是 private material path，而 Task 9 不得导入、调用或复制该 path，当前合同下所有 `V5_V6_PREPROD` 分支均必须返回 `preprod_authority=None`、`unsupported_reason=None`。
5. 仅在一个独立、fresh `PASS` 的 **feedback-owner public authority-construction seam 合同**冻结 exact public callable、输入 identity、返回 type、digest ownership、closed write set、tests 与 zero-side-effect boundary 后，future revision 才可定义 non-null branch；该 seam 不是 R39 的既有 private adapter，也不由本文、P-1、Task 9 或 P-2 实现。该前置 Gate 缺失、REVISE、BLOCKED 或任何输入不闭合时，必须保留 `None/None`；不得将 candidate 经 public field、observation、cache、exception details 或任何 side channel 暴露给 P-2 或 feedback。
6. future feedback-owner seam 若获独立冻结，其唯一允许的 authority mapping 必须为：
   - `case_id` 来自 returned manifest key；
   - `track` 来自 returned manifest key，且必须为 `V5_V6_PREPROD`；
   - `run_id` 来自 `run_artifact_request` 并与每条 returned record 一致；
   - `manifest` 为 P-1 returned manifest；
   - `target_refs` 顺序仅为 `RUN_SNAPSHOT`、`DECISION_RUN`、可选 `FEEDBACK_ATTACHMENT`、`MANIFEST` outer-ref；
   - `MANIFEST` 仅为 outer-ref：其 `object_id` 必须等于 returned manifest 的 `manifest_id`，其 exact `DigestPresent` binding digest 必须等于 P-1 public [`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1683) 返回的 records digest；它不是 writable record 或 payload，也不得使用 `manifest.digest` 替代该 verifier-returned digest；
   - `content_digest` 只能由该 future feedback-owner public seam 使用 owner-owned canonical material 生成；Task 9 不得计算、复制或伪造它。

## 5. failure precedence、零副作用与 negative ledger

| ID | 原子负向条件 | 必须结果 |
|---|---|---|
| T9V-F01 | legacy request/result/callable 被扩展，或 versioned 输入进入 legacy ABI | 合同失败；停止 implementation。 |
| T9V-F02 | disabled 或任一 legacy stop 调用 lifecycle/verifier，或产生 authority | `None/None`；零 P-1 lifecycle/verifier、feedback、learning 调用。 |
| T9V-F03 | caller/P-2/feedback 供应、重建、重签、relabel 或借用 run id/key/manifest/authority | fail closed；零 filesystem / feedback / learning side effect。 |
| T9V-F04 | legacy `IdempotencyKey` 与 `RunArtifactSetKeyV1` alias、转换或 cross-use | fail closed；不得创建 root、attempt 或 envelope。 |
| T9V-F05 | coordinator returned manifest 非 complete、identity/refs/roles/digests 不闭合，或 verifier 失败 | `preprod_authority=None`、`unsupported_reason=None`；零 binder/eligibility/learning。 |
| T9V-F06 | `STAGED_L6` 返回 authority、进入 binder 或 learning | `None/"STAGED_L6_UNSUPPORTED"`；零 feedback / learning side effect。 |
| T9V-F07 | 缺失独立 feedback-owner public authority-construction seam 时暴露 non-null authority，或 Task 9 调用/复制 feedback private material | `None/None`；停止于 producer envelope。 |
| T9V-F08 | `MANIFEST` outer-ref 使用 `manifest.digest`、被当作 writable record/payload，或未使用 verifier-returned records digest | fail closed；零 binder/eligibility/learning。 |
| T9V-F09 | Task 9 调用 `bind_feedback_operation()`、`evaluate_learning_eligibility()` 或 `validate_learning_eligibility()` | 合同违反；各调用数必须永远为零。 |

前置 validation / integrity failure 必须优先于任何 filesystem write、registry mutation、feedback、eligibility 或 learning 调用。任何未在本文冻结的 type、field、owner、path 或行为需求均为 STOP，另开合同修订。

## 6. 条件 implementation 范围与 future verification

若且仅若后续独立总控明确授权 implementation，本 unit 的条件 write set 恰为：

```text
engine/f09/application.py
engine/f09/__init__.py
tests/f09/test_application_opt_in.py
tests/f09/test_production_isolation.py
```

该未来授权不得继承给 [`engine/f09/artifacts.py`](../engine/f09/artifacts.py)、[`engine/f09/feedback.py`](../engine/f09/feedback.py)、P-2 paths、legacy Task 9 contract 或其他 tests。需要任何额外路径时必须 STOP 并开启新合同。

未来测试（尚未授权、尚未执行）必须至少静态/动态证明：exact public ABI/export；legacy ABI unchanged；legacy-first single call；stops 的 zero coordinator；returned-manifest-only provenance；key isolation；same-run-only retry input；complete verifier gate；`STAGED_L6` unsupported；缺失独立 construction seam 时的 absent authority；future seam 已独立批准时才允许的 full authority mapping / verifier-digest `MANIFEST` outer-ref；以及 Task 9 的 zero feedback / learning calls。

## 7. Gate、证据边界与唯一下一合法动作

本文是 document-only CONTRACT draft，而非 implementation completion、static review、verification、evidence review 或 freeze。作者仅可声明：已将当前权威输入收敛为 versioned Task 9 producer/envelope 合同；未修改运行时代码或 tests，未执行 Python、pytest、Git、远端或 GitHub-mutating operation。

作者 verdict：**`REVISE — ready for fresh independent read-only contract review`**。

即使下一轮 review 为 `PASS`，它也只关闭本 Task 9 versioned contract review Gate；不改变 P-2 `BLOCKED`、Task 9-P `BLOCKED`、Task 9 amendment `STILL_OPEN`，不授权任何 implementation，并且不取代 P-1 / R39 / future feedback-owner construction seam / P-2 的独立 Gate。

**唯一下一合法动作：** 对本文件执行逻辑新鲜、只读的独立合同审查，核验 ABI 隔离、producer-owned returned-manifest provenance、`STAGED_L6`/R39 分支、closed write set、negative ledger 与禁止授权推导。

---

## 8. fresh independent read-only contract review 记录

- **Reviewer role：** logical fresh Static Reviewer；不采纳作者自检。
- **审查输入：** 本合同、[`F09RunExecutionResultV1`](../engine/f09/application.py)、[`RunArtifactSetKeyV1`](../engine/f09/artifacts.py)、[`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1683)、[`PreprodRunAuthority`](../engine/f09/feedback.py:192)、[`_preprod_authority_self_excluded_material()`](../engine/f09/feedback.py:1361) 与 R39 合同。
- **副作用边界：** 仅本地文档读取与本 review record 写回；未执行 Python、pytest、Git、远端或 GitHub-mutating operation。

### 8.1 Observed facts

1. 合同保持 legacy [`run_f09_slice()`](../engine/f09/application.py) / [`F09RunResult`](../engine/f09/application.py) 不变，并将新增输入限制在 versioned callable；不存在把 current-run identity 写回 legacy ABI 的授权。
2. [`RunArtifactSetKeyV1`](../engine/f09/artifacts.py) 与 legacy [`IdempotencyKey`](../engine/f09/artifacts.py) 是不同 exact carriers；合同禁止 alias/cross-use，并要求只消费 P-1 returned manifest。
3. [`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1683) 只在 manifest 为 `COMPLETE_VERIFIED`、records 闭合且 manifest digest 通过时返回重新计算的 records digest；合同的 `MANIFEST` outer-ref 已使用该返回值，而非 `manifest.digest`，并禁止 self-referential record。
4. R39 已冻结 [`PreprodRunAuthority`](../engine/f09/feedback.py:192) 的 validation/consumer adapter，却未提供 Task 9 可调用的 public constructor 或 public content-digest construction seam；[`_preprod_authority_self_excluded_material()`](../engine/f09/feedback.py:1361) 是 feedback owner private path。Task 9 若自行计算、导入或复制该 digest material，将违反 owner boundary。
5. 合同据此把现阶段所有 `V5_V6_PREPROD` authority 输出 fail-close 为 `None/None`，保持 `STAGED_L6` 的 `None/"STAGED_L6_UNSUPPORTED"`，并冻结 binder/eligibility/learning 的零调用。

### 8.2 Falsifier disposition

- 若合同允许 versioned input 进入 legacy ABI、允许 caller/P-2 重建 manifest/authority、允许 `STAGED_L6` authority，或让 `MANIFEST` 使用 `manifest.digest`，本 review 应为 `REVISE`；这些 falsifier 未成立。
- 若当前权威 surface 已存在一个 feedback-owner public authority-construction callable，则第 4.1.4–4.1.5 的 absent-authority 结论应为 `REVISE`；所审 runtime 与 R39 合同均未给出该 surface。
- 因该 public seam 本身的 API、owner write set 与 verification 仍未由独立合同裁决，本 Task 9 合同不得把它当作既有可用依赖，也不得自行指定/实现它。

### 8.3 Verdict、证据边界与唯一下一合法动作

**Verdict：`REVISE`。** 本审查直接证明：本文已保留 ABI/key/manifest/track 的 fail-closed 边界，并正确拒绝使用 feedback private digest material。它不能证明 non-null `PreprodRunAuthority` 目前可由 Task 9 合法构造；缺失的 feedback-owner public authority-construction seam 是一个独立 contract/admission 决策。

不得推导：Task 9 contract `PASS`、P-2 admission `PASS`、Task 9-P 解锁、任何 implementation / tests / Python / pytest / Git 授权、全仓正确性或 GitHub 同步。受控会话未执行 GitHub-mutating operation。

**唯一下一合法动作：** 由 feedback owner 开立独立、document-only 的 public authority-construction seam admission/contract；其必须先冻结 exact callable、authority content-digest ownership、P-1 verifier-digest `MANIFEST` outer-ref、closed write set、zero binding/learning side effects与 fresh review。该 Gate 未独立 `PASS` 前，本合同保持 `REVISE`，P-2 与 Task 9-P 保持 `BLOCKED`，Task 9 amendment 保持 `STILL_OPEN`。

---

## 9. R40/R41 冻结后的现行最小合同修订

> **现行效力与历史保留：** 第 1–8 节的 draft、`REVISE` verdict、falsifier disposition 与 STOP 记录全部保留为历史。本节仅覆盖与已完成的 R41 returned-carrier / issuance-proof seam、R40 feedback-owner public constructor、versioned callable ingress、track branch order、failure disposition 和 future verification 相冲突的旧条款。本轮唯一 write 是本文件；未修改 production、tests、其他计划或状态文件，未执行 Python、pytest、Git、远端或 GitHub-mutating operation。

### 9.1 ADMISSION observed facts、inference 与 unknowns

**Observed facts：**

1. R41 已在 [`engine/f09/artifacts.py`](../engine/f09/artifacts.py) 交付 exact [`RunArtifactTargetRefsRequestV1`](../engine/f09/artifacts.py:113)、[`ManifestOuterRefRequestV1`](../engine/f09/artifacts.py:120)、[`RunArtifactSetResultV1`](../engine/f09/artifacts.py:149) 与 public [`coordinate_run_artifact_set_with_target_refs_v1()`](../engine/f09/artifacts.py:2041)。该 coordinator 先验证两个 capture inputs，再调用 legacy run-artifact coordinator、验证实际 returned manifest、构造 `MANIFEST` outer-ref、签署完整 result，并返回带 issuance proof 的 carrier。
2. R41 coordinator 明确只接受 exact `RunArtifactSetRequestV1` / `RunArtifactSetKeyV1` 且 track 为 `V5_V6_PREPROD`；`STAGED_L6` 在进入 legacy run-artifact coordinator 前即被拒绝。
3. R40 已在 [`engine/f09/feedback.py`](../engine/f09/feedback.py) 交付 feedback-owner public [`construct_preprod_run_authority_v1()`](../engine/f09/feedback.py:1430)。其唯一输入是 actual `RunArtifactSetResultV1`；它先验证 issuance proof，再使用 feedback-owner canonical material 生成 `content_digest`，返回 `PreprodRunAuthority`。
4. 第 2 节 ABI 只接收 `run_artifact_request` 与 `existing_run_manifest`，不能向 R41 coordinator 提供两个 exact capture inputs；第 3.2 仍调用旧 `coordinate_run_artifact_set_v1()`，不能产生 R40 唯一允许消费的 signed returned carrier。
5. 第 4.4–4.5、第 5 节 T9V-F07 与第 6 节 absent-authority verification oracle 所依赖的“public constructor 不存在”事实已经失效。

**Inference：** active target 唯一且 prerequisites 已满足，故 ADMISSION 为 `PASS`；但现行合同不能直接 `PASS`，必须以本节修复 ABI ingress、调用链和 stale absent-authority oracle 后再接受逻辑新鲜 CONTRACT review。

**Unknowns / forbidden inference：** 尚未实施 Task 9 versioned callable，尚无 Task 9 动态测试证据；R40/R41 unit freeze 不证明 Task 9、P-2、Task 9-P 或 G6 完成，也不授权修改 P-2、artifacts、feedback 或 legacy ABI。

### 9.2 覆盖后的 exact public ABI

第 2 节 callable signature 由下列现行 ABI 完整替代；envelope dataclass 保持不变：

```python
def run_f09_slice_with_execution_authority_v1(
    request: F09RunRequest,
    *,
    run_artifact_request: RunArtifactSetRequestV1,
    target_refs_request: RunArtifactTargetRefsRequestV1,
    manifest_outer_ref_request: ManifestOuterRefRequestV1,
    existing_run_manifest: ArtifactSetManifest | None,
    gate_inputs: tuple[GateEvaluationInput, ...],
    competition_input: CompetitionInput,
    root_input: RootInput,
    timing_input: TimingInput,
) -> F09RunExecutionResultV1: ...
```

1. `target_refs_request` 与 `manifest_outer_ref_request` 是仅属于 versioned callable 的 exact keyword-only inputs；它们不得进入 `F09RunRequest`、`F09RunResult`、legacy `run_f09_slice()`、observation、cache、P-2 或 feedback caller surface。
2. Task 9 只可把这两个对象原样转交 R41 coordinator，不得复制、重建、补字段、生成 ref、计算 digest、签名或构造 `RunArtifactSetResultV1` substitute。
3. legacy ABI、`F09RunExecutionResultV1` 三字段及其 field/constructor order、其余 keyword-only inputs 与第 6 节 closed implementation write set均保持不变。

### 9.3 覆盖后的 exact processing order 与 branch semantics

1. 对所有输入分支，versioned callable 首先以原参数恰一次调用 legacy [`run_f09_slice()`](../engine/f09/application.py)，并保留 returned object identity。
2. disabled 或任一 legacy stop 返回该 exact `run_result`、`preprod_authority=None`、`unsupported_reason=None`；R41 coordinator、R40 constructor、binder、eligibility 与 learning 调用数均为零。
3. legacy success 后先读取 legacy request 的 canonical mapped execution track，并核对 `run_artifact_request.key.case_id == request.case_id`、`run_artifact_request.key.run_id == run_artifact_request.run_id` 与 exact mapped track identity。不存在受支持 canonical non-production mapping，或任一 identity 不一致时 typed fail closed；不得调用 R41/R40，不得创建 envelope substitute。
4. exact `STAGED_L6` success 分支立即返回 exact `run_result`、`preprod_authority=None`、`unsupported_reason="STAGED_L6_UNSUPPORTED"`；R41/R40 与 feedback/learning calls 均为零。该顺序覆盖第 4.3 中“complete graph 后 unsupported”的历史表述，因为 R41 issuance coordinator 不接受 `STAGED_L6`。
5. exact `V5_V6_PREPROD` success 分支必须用 `request.artifact_root`、actual `run_artifact_request`、actual `target_refs_request`、actual `manifest_outer_ref_request`、`existing_run_manifest`、`request.attempt_id` 与 `request.now` 调用 [`coordinate_run_artifact_set_with_target_refs_v1()`](../engine/f09/artifacts.py:2041) 恰一次，并保留 actual returned `RunArtifactSetResultV1` object identity。
6. R41 成功后，Task 9 必须把该 actual returned carrier 原样作为唯一 keyword argument调用 [`construct_preprod_run_authority_v1()`](../engine/f09/feedback.py:1430) 恰一次；不得另行调用 manifest verifier、issuance verifier、feedback private helper，亦不得自行映射 authority fields/content digest。
7. R40 成功后返回 `F09RunExecutionResultV1(run_result, actual_returned_authority, None)`。该 envelope availability 不调用也不暗示 binder、eligibility、learning 或 P-2 admission readiness。
8. R41 抛出的 exact typed failure 原样传播，R40 call count 为零且不返回 envelope；R40 抛出的 exact typed failure原样传播且不返回 envelope。两类失败均不得降级为 `None/None`、不得吞错、重试、重签、修复、borrow、relabel 或调用后续 feedback/learning。

### 9.4 现行 negative ledger disposition

1. T9V-F01、F02、F06、F09 继续有效，但其中所有“coordinator”均按本节区分为 R41 versioned coordinator；stop 与 `STAGED_L6` 分支必须是零 R41/R40 calls。
2. T9V-F03 由两层 owner-bounded oracle 替代：(a) Task 9 在 R41 前可判定的 canonical case/run/track mismatch、unsupported mapping 或 legacy/versioned carrier cross-use 必须零 R41/R40 calls、零 versioned run-artifact write、零 execution envelope、零 feedback/learning；(b) 只有 R41 owner 能判定的 existing-manifest/key/target-ref/issuance/manifest identity failure 必须在恰一次 R41 call 内 fail closed，R40 call count 为零，exact exception identity 原样传播，且不得 second call、retry、write execution envelope 或调用 feedback/learning。两层均不得要求撤销、否认或把先行 legacy `run_f09_slice()` 已合法产生的 legacy statement-artifact side effect 计入该 versioned-only oracle；Task 9 不得为了把 (b) 前移而复制 R41 owner validation。
3. T9V-F04 由下列现行 oracle 替代：legacy `IdempotencyKey` 与 `RunArtifactSetKeyV1` 的 alias、转换或 cross-use 必须 fail closed；不得由 R41 创建 versioned run-artifact root/attempt，不得创建 execution envelope。先行 legacy callable 的既有 statement-artifact root/attempt 不属于该 versioned-only oracle，且不得被修改、回滚或重标。
4. T9V-F05 由下列现行 oracle 替代：R41 capture/manifest/issuance/identity 任一失败必须传播 exact failure、零 R40 calls、零 envelope；R40 issuance/manifest/authority material 任一失败必须传播 exact failure、零 envelope；两者均零 binder/eligibility/learning calls。
5. T9V-F07 由下列现行 oracle 替代：`V5_V6_PREPROD` success 必须恰一次消费 R41 actual returned carrier并恰一次调用 R40 public constructor；任何 absent authority、caller-built/substitute result、Task 9 field mapping、digest computation、feedback private helper调用或跳过 issuance-bound carrier 均为合同违反。
6. T9V-F08 由下列现行 oracle 替代：Task 9 不得构造、读取后重建、替换或逐字段解释 R41 returned carrier 中的 `MANIFEST` outer-ref，不得直接调用 manifest verifier、选择 digest 或制造 writable `MANIFEST` record/payload；它只能把 actual `RunArtifactSetResultV1` 对象原样交给 R40。outer-ref/digest 的 producer correctness 属于已冻结 R41 seam，Task 9 只证明 zero-construction 与 object-identity handoff，不重复证明或实现 R41 内部算法。
7. 新增 T9V-F10，按 owner 与分支拆分：
   - 对 disabled、任一 legacy stop 或 exact `STAGED_L6` 分支，两个 capture inputs 的 runtime material 均不被消费，也不声明其内部 role/order/digest/material 已获验证；R41/R40 调用数必须为零。静态 Gate 在这些分支只证明 versioned ABI presence / exact annotation、Task 9 零复制/零重建，以及 mandatory pre-R41 exit。
   - 仅在 legacy success、canonical mapped track 为 exact `V5_V6_PREPROD` 且 Task 9 pre-R41 case/run/track admission 已通过后，缺失、非 exact、role/order/digest/material 不闭合的 `target_refs_request` 或 `manifest_outer_ref_request` 必须在恰一次 R41 owner call 内 fail closed；R40/binder/eligibility/learning 调用数为零，且不得 retry、second call 或生成 envelope。
   - 所有进入 R41 的成功候选中，Task 9 只能原样传递两个 capture objects；任何复制、重建、补字段或逐字段解释均由静态 Gate 拒绝。
8. 新增 T9V-F11：R41/R40 exception 被吞并改写为 `None/None`、产生 partial envelope、触发 retry/second call 或通过 observation/cache/exception detail side channel 暴露 candidate authority，均为合同违反。

### 9.5 覆盖后的 future verification、write set 与 STOP

future verification 必须至少证明：

- exact amended ABI/export；legacy declarations 与 signature 不变，且既有未修改 legacy tests 通过；不把抽象 runtime behavior 描述为 byte-for-byte；
- legacy-first exactly-once 与 exact returned `run_result` identity；
- disabled/stops 的零 R41/R40 calls；
- `STAGED_L6` pre-R41 unsupported 与零 R41/R40/feedback/learning calls；
- V5/V6 exact ingress objects 被原样传入 R41，actual `RunArtifactSetResultV1` 被原样传入 R40；
- Task 9 pre-R41 admission 可判定的 canonical case/run/track mismatch、unsupported mapping 与 carrier cross-use 必须证明零 R41/R40 calls、零 versioned root/attempt/write 与零 envelope；只有 R41 owner 可判定的 existing-manifest/key/target-ref/issuance/manifest identity failure 必须证明 R41 恰一次、R40 零次、exact exception identity、零 second call/retry/envelope；两类静态/动态 oracle 均须把先行 legacy statement-artifact side effect 排除在 T9V-F03/F04 的 versioned-only accounting 外；
- Task 9 对 R41 returned `MANIFEST` outer-ref 的 zero-construction / zero-rebuild / object-identity handoff，且不重复测试或实现 R41 内部 digest algorithm；
- R41 exactly once、R40 exactly once、Task 9 零 direct manifest/issuance verifier及零 private feedback helper calls；
- R41 failure → zero R40/no envelope，R40 failure → no envelope，exception identity preserved；
- returned authority object identity、`unsupported_reason=None`，以及零 binder/eligibility/learning calls；
- T9V-F01–F09 与 F11 的静态/动态 falsifier closure；
- T9V-F10 的分支化 closure：disabled/legacy-stop/`STAGED_L6` 证明 capture material 未消费且零 R41/R40；legacy-success exact `V5_V6_PREPROD` 且 pre-R41 admission 通过后，malformed capture material 证明恰一次 R41 fail closed、零 R40/retry/second call/envelope；所有候选均以静态 oracle 证明 exact ABI、零 copy/rebuild 与 object-identity handoff。

条件 implementation write set 仍恰为第 6 节四个路径。任何需要修改 [`engine/f09/artifacts.py`](../engine/f09/artifacts.py)、[`engine/f09/feedback.py`](../engine/f09/feedback.py)、legacy contract、P-2 path 或其他 tests 的实现方案立即 STOP 并返回新的独立 contract Gate。

### 9.6 第一次 fresh CONTRACT review failure disposition

第一次逻辑新鲜 review verdict 为 `REVISE`：它确认 amended ABI、legacy isolation、pre-R41 `STAGED_L6`、actual carrier handoff、failure propagation 与 closed write set基本闭合，同时发现 T9V-F03/F04 的“零 filesystem/root/attempt”绝对表述与 legacy-first 顺序冲突，以及 T9V-F08 仍把 R41-owned outer-ref algorithm 当作 Task 9 oracle。本次只以第 9.4–9.5 的 versioned-only accounting、legacy-side-effect exclusion 与 R41-owner handoff修订消费这些 findings；未改变 ABI、owner、track branch、write set 或 P-2 STOP。

### 9.7 第二次 fresh CONTRACT review failure disposition

第二次逻辑新鲜 review verdict 为 `REVISE`：它确认第一次 review 所发现的 legacy side-effect accounting 与 R41-owned outer-ref owner gap 已闭合，但发现 T9V-F03 仍把所有 versioned identity mismatch 都写成零 R41 call；`existing_run_manifest.key != request.key` 等 owner-owned mismatch 只能在 R41 调用内部被发现。本次仅以第 9.4–9.5 的两层 owner-bounded call-count oracle 消费该 finding：Task 9 pre-R41 admission failure 为零 R41/R40，而 R41-owned identity failure 为 R41 恰一次、R40 零次、exact failure propagation 与零 retry/second call/envelope。未改变 ABI、legacy-first order、owner、track branch、write set 或 P-2 STOP。

### 9.8 当前 Gate、证据边界与唯一下一合法动作

- **ADMISSION verdict：`PASS`。** 仅证明 Task 9 versioned producer/envelope 是当前依赖已满足的唯一 active candidate，且最小合同修订范围可闭合。
- **第三次 fresh CONTRACT review verdict：`REVISE`。** Review 确认 amended ABI、legacy isolation、R41/R40 identity handoff、owner-bounded failure accounting与四文件 write set基本闭合，但发现旧 T9V-F10 对 stop/`STAGED_L6` 也要求 malformed capture material 由 R41 fail closed，与 mandatory pre-R41 exit 冲突。
- **第三次 review 后修订：** T9V-F10 已拆为 pre-R41 不消费分支、V5/V6 R41-owner runtime validation 分支与全候选 static identity/zero-copy 分支，并同步收紧 verification oracle；该作者修订本身不作为 review evidence。
- **第四次 fresh independent CONTRACT review verdict：`PASS`。** 独立只读 reviewer 确认第 9 节当前文本在 amended ABI、legacy isolation、legacy-first/track ordering、R41 exact ingress、R41→R40 actual-carrier identity handoff、owner-bounded failure accounting、分支化 T9V-F10、T9V-F01–F11 可证伪性与四文件 closed write set 上唯一、完整、可实施、可证伪；第三次 review blocker 已关闭。

### 9.9 fresh STATIC_REVIEW、VERIFY、EVIDENCE_REVIEW 与证据有界冻结

Gate chain：

```text
CONTRACT PASS
→ fresh STATIC_REVIEW REVISE
→ bounded test-only repair
→ fresh STATIC_REVIEW PASS
→ fresh VERIFY PASS
→ fresh EVIDENCE_REVIEW PASS
→ PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE
```

1. 第一次 Task 9 fresh STATIC_REVIEW verdict 为 `REVISE`，仅发现三个测试闭环缺口：stop/`STAGED_L6` 未以 poison capture 证明 material 未消费；V5/V6 malformed capture 未证明恰一次交给 R41 owner 后 fail closed；legacy `run_f09_slice()` signature regression oracle 不完整。该 verdict 不是动态 RED，也不证明 runtime failure。
2. bounded repair 仅修改 [`tests/f09/test_application_opt_in.py`](../tests/f09/test_application_opt_in.py)：补充 legacy signature/type-hint oracle、poison capture stop/STAGED oracle，以及两个 malformed capture 的 R41-owner identity/failure 参数实例。未修改 runtime、R41、R40、P-2 或其他 tests。修改后旧 static verdict 失效。
3. 第二次逻辑新鲜、独立、只读 STATIC_REVIEW verdict 为 `PASS`：确认 amended ABI/export、legacy-first、branch order、owner-bounded failure accounting、zero-copy/object-identity handoff、T9V-F01–F11 与分支化 T9V-F10 的静态/动态 oracle 均闭合。该 PASS 只授权 VERIFY，不证明 behavior。
4. exact focused VERIFY：

```text
cwd: f:/多流派新思路
command: python -m pytest -q tests/f09/test_application_opt_in.py::test_public_dtos_and_entrypoint_are_exact tests/f09/test_application_opt_in.py::test_versioned_public_dto_signature_and_export_are_exact tests/f09/test_application_opt_in.py::test_versioned_legacy_stop_preserves_identity_and_calls_no_versioned_owner tests/f09/test_application_opt_in.py::test_versioned_staged_success_is_pre_r41_unsupported tests/f09/test_application_opt_in.py::test_versioned_preprod_hands_actual_ingress_to_r41_and_carrier_to_r40_once tests/f09/test_application_opt_in.py::test_versioned_pre_r41_identity_mismatch_calls_no_versioned_owner tests/f09/test_application_opt_in.py::test_versioned_legacy_key_cross_use_fails_typed_before_versioned_owner tests/f09/test_application_opt_in.py::test_versioned_malformed_capture_is_handed_once_to_r41_owner_and_fails_before_r40 tests/f09/test_application_opt_in.py::test_versioned_r41_failure_is_propagated_once_before_r40 tests/f09/test_application_opt_in.py::test_versioned_r40_failure_is_propagated_once_without_envelope tests/f09/test_production_isolation.py::test_versioned_application_owner_boundary_has_no_forbidden_calls
result: 18 collected / 18 passed / 0 failed / 0 errors / exit 0 / 0.43s
```

静态实例为 `1 + 1 + 5 + 1 + 1 + 3 + 1 + 2 + 1 + 1 + 1 = 18`，动态 collection 为 18，差为 0，reconciled = YES。

5. 两个 Task 9 模块完整 VERIFY：

```text
cwd: f:/多流派新思路
command: python -m pytest -q tests/f09/test_application_opt_in.py tests/f09/test_production_isolation.py
result: 30 collected / 30 passed / 0 failed / 0 errors / exit 0 / 1.75s
```

静态实例为 application 26 + production isolation 4 = 30，动态 collection 为 30，差为 0，reconciled = YES。

6. F09 regression：

```text
cwd: f:/多流派新思路
command: python -m pytest -q tests/f09
result: 1019 collected / 1019 passed / 0 failed / 0 errors / exit 0 / 58.97s
```

7. failure/stale evidence history：第一次 STATIC_REVIEW `REVISE` 被完整保留；修订后重新取得 fresh STATIC_REVIEW PASS 才执行 VERIFY。旧会话 Task 9 tests/freeze 与旧 `1017` 数量仅为 stale recovery clue，未用于本 verdict。本轮无 collection error、动态失败或 failure 后 rerun。
8. fresh independent EVIDENCE_REVIEW verdict 为 `PASS`，确认 exact commands、cwd、collection/result/exit、失败历史、stale evidence 隔离、18/18 与 30/30 reconciliation 及本地命令的 GitHub side-effect screening 均闭合；freeze eligible = YES。
9. **直接证明：** 当前 versioned ABI/export、legacy-first identity、stop/STAGED pre-R41 exits、V5/V6 ingress 与 R41→R40 actual-object handoff、pre-R41 mismatch/cross-use fail-close、R41/R40 exception propagation、owner direct-call prohibition，以及当前 F09 regression 1019 项，在所述环境与命令范围内通过。
10. **不得推导：** 本冻结不证明 P-2、Task 9-P、G6、repository-wide full suite、性能、安全、跨平台、部署、发布、远端同步或 GitHub 整体状态；本受控链未执行 Git/GitHub-mutating operation，但不得据此推断 GitHub 从未被其他主体改变。

**Freeze verdict：`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`。** 这是 Task 9 unit 的本地证据有界冻结，不是 Phase 或项目完成。

**唯一下一合法动作：** 在 R40 与 Task 9 均 durable evidence-bounded frozen 的前提下，对 P-2 执行 fresh independent ADMISSION review；在该 ADMISSION PASS 前不得实施、验证或宣称 P-2/Task 9-P/G6 完成。
