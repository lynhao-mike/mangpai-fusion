# G6 Task 9 Authority Adjudication Implementation Plan

> **For agentic workers:** 本文是上游 authority bounded adjudication，不是实现授权。任何后续执行必须先完成本文指定的独立前置 authority amendment，并经独立复核；不得从本文直接修改 production owner。

**Goal:** 为 G6 Task 9 冻结唯一、无循环知识、可证伪的上游 authority 裁决，并判定当前 Task 9 合同是否具备修订资格。

**Architecture:** Task 9 application 只编排已经存在的 public owners，不得复制 Task 4–8 语义。Same-instance evidence 改为 caller 提供已注册 package identity 后由 application 经同一 canonical port 读取；artifact projections/key 必须在 statement set 形成后由 Task 7 public owner 构造；feedback 是最终 phase，但必须由 Task 8 public owner绑定当前 non-production run authority，且不进入 learning。

**Tech Stack:** Python immutable dataclasses、runtime-checkable ports、bounded RFC 8785 JCS、lowercase SHA-256、typed F09 errors、Markdown authority contracts。

## Global Constraints

- 本裁决只创建 [`plans/g6-task9-authority-adjudication.md`](g6-task9-authority-adjudication.md)；未修改合同原文、PI-500、production code、tests、JSON、YAML、META 或 handoff。
- 本裁决未运行 Python、pytest、行为测试、Git 或 GitHub mutation。
- [`NormalizedEvidenceReadPort`](../engine/f09/contracts.py:741) 仍是唯一 canonical evidence port；禁止 application wrapper、第三 port、dict reconstruction 或隐式 registry。
- Task 10 仍是 tests-only；[`Task 10 closed write set`](production-implementation-pi-500-r1-f09-implementation-plan.md:3086) 不得产生或修改 production authority。
- Task 9 只接受显式 opt-in request mode `STAGED_AUDIT` 与 `PREPROD_SHADOW`；`PRODUCTION_DEFAULT` request 继续在任何 I/O 前 fail closed。
- canonical track 映射保持唯一：`STAGED_AUDIT -> RunTrack.STAGED_L6`、`PREPROD_SHADOW -> RunTrack.V5_V6_PREPROD`。
- feedback 只允许 binding without learning；禁止调用 [`evaluate_learning_eligibility()`](../engine/f09/feedback.py:2031)、[`validate_learning_eligibility()`](../engine/f09/feedback.py:2091) 或任何 learning execution/ingest/writer。

---

## 1. 裁决范围与证据层级

本裁决直接核验：

1. [`PI-500 Task 6–10`](production-implementation-pi-500-r1-f09-implementation-plan.md:3056) 与 [`PI-500-A1`](production-implementation-pi-500-r1-f09-implementation-plan.md:7804)；
2. 当前 [`Task 9 application orchestrator contract`](g6-task9-application-orchestrator-contract.md)；
3. runtime owners：[`contracts.py`](../engine/f09/contracts.py)、[`evidence.py`](../engine/f09/evidence.py)、[`decision.py`](../engine/f09/decision.py)、[`trace.py`](../engine/f09/trace.py)、[`artifacts.py`](../engine/f09/artifacts.py)、[`feedback.py`](../engine/f09/feedback.py)、[`canonical_json.py`](../engine/f09/canonical_json.py)。

裁决时以实际 public runtime surface 为可执行事实；PI-500 负责上游目标与 ownership 边界；当前 Task 9 合同中与两者冲突的 closure claim 不产生 authority。

## 2. 总裁决

**Gate：`BLOCKED`。**

理由不是 Task 9 编排顺序无法描述，而是 frozen Task 7/8 public owners 尚不能提供两个 Task 9 必需的 authority：

1. statement-set-dependent 三角色 projection bytes 与 artifact [`IdempotencyKey`](../engine/f09/artifacts.py:48) 的 public construction owner；
2. 对当前 opt-in tracks 可执行的 run-target feedback authority，尤其 [`RunTrack.STAGED_L6`](../engine/f09/contracts.py:21)，以及从 current run outputs 构造合法 target authority 的 public owner。

因此当前唯一可执行结论是：先完成独立前置 owner amendment；在其独立通过前，不得修订 Task 9 合同为 `PASS`，不得实现 [`run_f09_slice()`](production-implementation-pi-500-r1-f09-implementation-plan.md:3072)，也不得让 caller 预计算未来 statement-set identity 来绕过缺口。

## 3. 五项唯一 reconciliation

| Finding | 唯一状态 | 裁决 |
|---|---|---|
| `T9-C-02` | `CLOSED_BY_AMENDMENT` | 选择 caller 提供已注册 `package_id` 的方案。application 取消 [`build_f09_evidence_package()`](../engine/f09/evidence.py:355) 调用，经 request 中同一 [`NormalizedEvidenceReadPort.get_package()`](../engine/f09/contracts.py:742) 读取 authoritative package，并把同一对象与同一 port instance 交给 [`evaluate_f09()`](../engine/f09/decision.py:870)。 |
| `T9-C-05` | `REQUIRES_PREREQUISITE` | caller 不再提供 `artifact_projections`。现有 Task 6/7 无 public semantic projection builder；[`canonicalize_bounded_jcs()`](../engine/f09/canonical_json.py:241) 只是通用编码 owner，不能发明 `REPORT`、`STATEMENT_RECORDS`、`STATEMENT_INDEX` material。必须先新增 Task 7 public construction owner。 |
| `T9-C-06` | `REQUIRES_PREREQUISITE` | caller 不再提供 `artifact_key`。key 依赖已生成 statement set、current projections、schema/contracts；现有 [`coordinate_artifact_operation()`](../engine/f09/artifacts.py:1005) 只消费、不构造或证明 key material。必须由与 projections 相同的 Task 7 owner 在 statement set 后原子地产生。 |
| `T9-C-07` | `CLOSED_BY_AMENDMENT` | caller 只拥有 artifact root、optional prior manifest、attempt ID 与 execution time；application 拥有 phase order及 current authority 汇合；Task 7 owner拥有 operation-root resolution、fresh/retry、inspection和写入。若 supplied prior manifest key 不等于 current key，application 必须 fail closed，不得借 [`coordinate_artifact_operation()`](../engine/f09/artifacts.py:1005) 的 changed-key fresh-write 分支静默忽略 caller 声称的 prior state。 |
| `T9-C-10` | `REQUIRES_PREREQUISITE` | Task 9 最终 phase 必须是 `FEEDBACK`，不是 `ARTIFACT`；实际调用 owner必须是 [`bind_feedback_operation()`](../engine/f09/feedback.py:1857)，且 without learning。现有 [`PreprodRunAuthority`](../engine/f09/feedback.py:189) 只接受 `V5_V6_PREPROD`，无 `STAGED_L6` target protocol；当前 artifact output也不足以自行构造合法 run-target authority。必须先扩充 Task 8 public authority。 |

状态计数固定为：`CLOSED_BY_AMENDMENT=2`、`REQUIRES_PREREQUISITE=3`、`BLOCKED=0`。Finding 表中的 `BLOCKED=0` 不改变总 Gate 为 `BLOCKED`；总 Gate 表示存在未完成的 frozen-owner prerequisite。

## 4. Authority clauses

### A-1 Same-instance evidence closure

未来 Task 9 request 必须包含：

```python
package_id: str
normalized_evidence_port: NormalizedEvidenceReadPort
```

application 的唯一合法 evidence path：

```python
package = request.normalized_evidence_port.get_package(request.package_id)
result = evaluate_f09(
    package,
    normalized_evidence_port=request.normalized_evidence_port,
    # remaining frozen evaluator inputs
)
```

约束：

- `package_id` 是 caller 已注册 identity；application 不构造、不注册、不替换 package。
- application 必须在调用 [`evaluate_f09()`](../engine/f09/decision.py:870) 前验证返回对象的 `package_id`、`case_id` 与 mapped canonical track 对齐；失败使用既有 typed F09 error并停止。
- evidence read 与 evaluator 参数必须是对象同一性相同的 port instance，不仅是同类型实例。
- request 删除 `markdown_path`、`snapshot_path`、`chart_records`、`hypothesis_records` 等 application-build authority；source package publication 属 Task 9 上游，不在本编排器内。
- 本方案不修改 [`NormalizedEvidenceReadPort`](../engine/f09/contracts.py:741)，不新增 publication method，满足 [`PI-500-A1 same-port rule`](production-implementation-pi-500-r1-f09-implementation-plan.md:7853)。

### A-2 Artifact future-identity prohibition

以下字段必须从 Task 9 caller surface 删除：

```python
artifact_projections: Mapping[str, bytes]
artifact_key: IdempotencyKey
```

projections 与 key 只能在以下条件全部成立后构造：

1. [`build_statement_set()`](../engine/f09/trace.py:824) 已返回 current statement set；
2. [`validate_statement_projection()`](../engine/f09/trace.py:874) 已成功且 producer-owned `detected_issues` 为空；
3. current package、decision、trace、statement set、contract refs 与 schema refs 均仍是同一 run 的 canonical objects；
4. Task 7 public construction owner一次返回 projections 与 key，不允许两个 caller独立计算后拼接。

禁止 caller 预声明 `statement_set_id`、投影 digest、canonical key digest 或由未来 statement set 派生的 bytes。

### A-3 Artifact prior/execution authority split

caller-owned exact inputs：

```python
artifact_root: Path
existing_manifest: ArtifactSetManifest | None
attempt_id: str
artifact_now: str
```

application-owned检查：

```python
if existing_manifest is not None and existing_manifest.key != current.key:
    raise F09ContractError(
        "IDEMPOTENCY.DIGEST_MISMATCH",
        "/existing_manifest/key",
        "supplied prior manifest is not authority for the current operation",
    )
```

随后仅可调用：

```python
manifest = coordinate_artifact_operation(
    request.artifact_root,
    statement_set,
    current.projections,
    existing_manifest=request.existing_manifest,
    key=current.key,
    attempt_id=request.attempt_id,
    now=request.artifact_now,
)
```

application 不发现目录、不扫描 manifests、不生成 attempt ID、不读取 wall clock、不解释 artifact state为 issue。Task 7 owner继续拥有 contained operation root、record/attempt ledger、fresh/retry、digest验证及 filesystem mutation。

### A-4 Feedback is terminal and without learning

未来唯一 phase order：

```text
REQUEST_PREFLIGHT
→ EVIDENCE_READ
→ DECISION
→ TRACE
→ STATEMENT_SET
→ PROJECTION_VALIDATION
→ ARTIFACT_AUTHORITY_BUILD
→ ARTIFACT
→ FEEDBACK
```

`ARTIFACT` 不是成功终点。只有 manifest 为 `COMPLETE_VERIFIED` 才进入 `FEEDBACK`；其他 artifact states 保留 manifest并停止，feedback owner零调用。

`FEEDBACK` 有两个显式结果：

- caller 无 feedback submission：application 产生 typed `NOT_REQUESTED` phase observation，feedback owner零调用；
- caller 提供 feedback submission：application 使用前置 Task 8 owner构造 current [`RawFeedbackAuthority`](../engine/f09/feedback.py:225)，随后恰调用一次 [`bind_feedback_operation()`](../engine/f09/feedback.py:1857)。

无论 binding 结果为何，Task 9 都不得调用 [`evaluate_learning_eligibility()`](../engine/f09/feedback.py:2031)，不得执行 learning、ingest、weights、rule writes 或 iteration trigger。

## 5. 必须先完成的 frozen-owner prerequisite

### P-1 Task 7 artifact material authority

**Closed implementation write set：**

- Modify: [`engine/f09/artifacts.py`](../engine/f09/artifacts.py)
- Modify: [`tests/f09/test_artifact_lifecycle.py`](../tests/f09/test_artifact_lifecycle.py)

不得修改 application、Task 8 owner、Task 10 matrix或其他文件。

最小新增 public API：

```python
@dataclass(frozen=True)
class ArtifactOperationAuthority:
    projections: Mapping[str, bytes]
    key: IdempotencyKey


def build_artifact_operation_authority(
    package: NormalizedEvidencePackage,
    decision: DecisionEvaluationResult,
    trace: TraceEnvelope,
    statement_set: StatementSet,
    projection_validation: ProjectionValidationResult,
    *,
    normative_contract_ref: VersionedObjectRef,
    machine_appendix_ref: VersionedObjectRef,
) -> ArtifactOperationAuthority: ...
```

该前置 amendment 必须在 Task 7 内冻结并测试：

- 三个且仅三个 roles：`REPORT`、`STATEMENT_RECORDS`、`STATEMENT_INDEX`；
- 每个 role 的完整 bounded-JCS semantic material与schema version；
- `source_digest`、`schema_versions_digest`、`contract_digest`、`statement_set_id` 与 `canonical_key_digest` 的完整 material；
- operation literal及三角色共同 operation identity；
- object/track/case/statement-set一致性；
- 返回 mapping 的不可变/不被调用者修改保证；
- 任一 projection bytes变化必然改变相应 digest及 canonical key；
- 无 number、BOM、重复 key、非 canonical Unicode 或私有 helper跨模块调用。

在上述 material 被明确冻结前，不得把 [`canonicalize_bounded_jcs()`](../engine/f09/canonical_json.py:241) 当作 semantic owner。

### P-2 Task 8 non-production run feedback authority

**Closed implementation write set：**

- Modify: [`engine/f09/feedback.py`](../engine/f09/feedback.py)
- Modify: [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py)

不得修改 application、Task 7 owner、Task 10 matrix或其他文件。

最小新增 public API：

```python
@dataclass(frozen=True)
class NonProductionRunFeedbackInput:
    raw_submission: bytes
    target_track_source_binding: TrackSourceBinding
    target_records: tuple[ArtifactRecord, ...]
    target_refs: tuple[VersionedObjectRef, ...]
    captured_at: str


def build_nonproduction_feedback_authority(
    current: NonProductionRunFeedbackInput,
    *,
    case_id: str,
    track: RunTrack,
    run_id: str,
    manifest: ArtifactSetManifest,
) -> RawFeedbackAuthority: ...
```

该 owner 必须：

- 仅接受 `RunTrack.STAGED_L6` 或 `RunTrack.V5_V6_PREPROD`，并保持两轨分账；
- 由 caller-owned run records/refs 验证 common case/track/run identity，禁止 application fabrication；
- 要求 current verified manifest 与 target graph建立明确 digest/ref binding；
- 要求 protocol-authorized usable run snapshot，同时允许 authority允许的额外 run refs；
- guard every nested ref/digest before dereference；
- 返回可直接交给 [`bind_feedback_operation()`](../engine/f09/feedback.py:1857) 的 [`RawFeedbackAuthority`](../engine/f09/feedback.py:225)；
- 不调用 learning eligibility，不返回 learning target，不执行 side effect；
- 使 `STAGED_L6` 获得明确的 non-production run-target binding protocol，不能伪装成 production statement feedback。

若 Task 8 authority review判定 PI-230 不允许 `STAGED_L6` feedback target，P-2 必须 fail closed并上送 PI-230 prerequisite；不得在 Task 9 application中添加 local enum、adapter或兼容分支。

## 6. 前置完成后的 Task 9 exact request surface

前置 P-1/P-2 独立通过后，Task 9 amendment应冻结以下最小输入；这里仅定义目标 surface，不授权实现：

```python
@dataclass(frozen=True)
class F09RunRequest:
    case_id: str
    mode: Literal["STAGED_AUDIT", "PREPROD_SHADOW", "PRODUCTION_DEFAULT"]
    enable_f09: bool
    package_id: str
    normalized_evidence_port: NormalizedEvidenceReadPort
    frozen_contract_port: FrozenContractReadPort
    request_id: str
    contract_ref: ContractVersionRef
    normative_contract_ref: VersionedObjectRef
    machine_appendix_ref: VersionedObjectRef
    artifact_root: Path | None
    existing_manifest: ArtifactSetManifest | None
    attempt_id: str
    decision_now: str
    trace_now: str
    statement_now: str
    artifact_now: str
    feedback_input: NonProductionRunFeedbackInput | None
    prior_feedback_operation: PriorFeedbackOperation | None
    feedback_clock: FeedbackClockPort | None
```

调用边界：

- `feedback_input is None` 时，`prior_feedback_operation` 与 `feedback_clock` 必须也为 `None`；
- `feedback_input is not None` 时，`feedback_clock` 必须存在，application先调用 [`build_nonproduction_feedback_authority()`](g6-task9-authority-adjudication.md) 再调用 [`bind_feedback_operation()`](../engine/f09/feedback.py:1857)；
- `prior_feedback_operation` 只能交给 binder，不得由 application解析或合成；
- 所有 time/clock authority显式输入，不得读取 ambient clock；
- gate、competition、root、timing inputs继续使用 Task 5 canonical dataclasses与同一 evidence port resolver graph。

## 7. Phase ownership与停止语义

| Phase | Owner | 成功输出 | Fail-closed stop |
|---|---|---|---|
| `REQUEST_PREFLIGHT` | Task 9 application | mapped canonical track | opt-in false、未知/production mode、root/package/authority shape invalid时零I/O停止 |
| `EVIDENCE_READ` | [`NormalizedEvidenceReadPort.get_package()`](../engine/f09/contracts.py:742) | authoritative package | package/case/track mismatch停止 |
| `DECISION` | [`evaluate_f09()`](../engine/f09/decision.py:870) | decision result | typed error或producer issues停止 |
| `TRACE` | [`build_trace()`](../engine/f09/trace.py:593) | trace | typed error或invalid trace停止 |
| `STATEMENT_SET` | [`build_statement_set()`](../engine/f09/trace.py:824) | statement set | typed error停止 |
| `PROJECTION_VALIDATION` | [`validate_statement_projection()`](../engine/f09/trace.py:874) | validation result | detected issues非空或invalid停止 |
| `ARTIFACT_AUTHORITY_BUILD` | prerequisite [`build_artifact_operation_authority()`](g6-task9-authority-adjudication.md) | projections + key | material/identity mismatch停止且零filesystem write |
| `ARTIFACT` | [`coordinate_artifact_operation()`](../engine/f09/artifacts.py:1005) | manifest | 非`COMPLETE_VERIFIED`保留manifest并停止 |
| `FEEDBACK` | prerequisite authority builder + [`bind_feedback_operation()`](../engine/f09/feedback.py:1857) | binding operation result或`NOT_REQUESTED` | typed binding failure停止；永不进入learning |

observations只能机械投影 phase、status、producer-owned issue code/path与artifact state；不得包含source prose、internal statement IDs，不得从state/reason推导issue。

## 8. Write-set effect

### 本裁决的实际写集

- Create: [`plans/g6-task9-authority-adjudication.md`](g6-task9-authority-adjudication.md)

### 本裁决明确不授权

- 不授权修改 [`g6-task9-application-orchestrator-contract.md`](g6-task9-application-orchestrator-contract.md)。
- 不授权修改 [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md)。
- 不授权修改任何 [`engine/f09/`](../engine/f09/) 或 [`tests/f09/`](../tests/f09/) 文件。
- 不授权运行 tests、collection、Git 或 GitHub operations。

### 前置任务通过后的分段写集

1. P-1 仅 [`engine/f09/artifacts.py`](../engine/f09/artifacts.py) 与 [`tests/f09/test_artifact_lifecycle.py`](../tests/f09/test_artifact_lifecycle.py)。
2. P-2 仅 [`engine/f09/feedback.py`](../engine/f09/feedback.py) 与 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py)。
3. P-1/P-2 独立通过后，另开 Task 9 contract-only amendment，仅修改 [`g6-task9-application-orchestrator-contract.md`](g6-task9-application-orchestrator-contract.md)。
4. contract amendment 独立通过后才可另行授权 Task 9 implementation；Task 10 保持 tests-only且不能与 owner implementation混写。

## 9. 禁止项

- 禁止保留 caller-owned `artifact_projections` 或 `artifact_key`。
- 禁止 caller/application预计算尚未生成的 statement-set identity。
- 禁止 application调用 [`build_f09_evidence_package()`](../engine/f09/evidence.py:355) 后假设其已进入同一 read port。
- 禁止给 [`NormalizedEvidenceReadPort`](../engine/f09/contracts.py:741) 加 application-local wrapper/publication shim。
- 禁止调用 private helpers，例如 [`_statement_set_content_digest()`](../engine/f09/trace.py:374) 或 [`_idempotency_key_material()`](../engine/f09/feedback.py:682)，作为跨模块 public authority。
- 禁止把通用 JCS canonicalizer解释为 projection schema owner。
- 禁止 prior manifest key mismatch时静默走fresh write。
- 禁止 application扫描artifact root以猜测existing manifest。
- 禁止 application生成attempt ID或读取ambient clock。
- 禁止把 `STAGED_L6` feedback伪装为 [`ProductionStatementAuthority`](../engine/f09/feedback.py:175)。
- 禁止 Task 9 调用 learning eligibility或任何learning execution。
- 禁止 Task 10 tests/fixtures产生production authority或反向修改owner contract。

## 10. 风险与证伪路径

| 风险 | 第一证明点 | 证伪条件 |
|---|---|---|
| Same-instance 仅文字相同、对象不相同 | application identity assertion证明read与evaluator收到同一port object | 任一wrapper、复制port或第三resolver出现即证伪 |
| Projection schema仍由caller/Task 9私造 | P-1 public owner test从statement set后构造三角色bytes | request仍含projection bytes，或application出现role serializer即证伪 |
| Key material漏项导致不同outputs同key | P-1逐字段mutation test覆盖source/schema/contracts/statement set/projections | 任一权威字段变化而canonical key不变即证伪 |
| Prior manifest被静默忽略 | Task 9 pre-coordinator mismatch test要求typed stop且零write | key mismatch仍调用coordinator fresh branch即证伪 |
| STAGED feedback无runtime protocol | P-2以caller-owned staged run graph产生合法RawFeedbackAuthority | 依赖production statement authority、local enum或adapter fabrication即证伪 |
| PREPROD target由application伪造 | P-2空/坏/扩展caller graph均能到达owner guards | application固定构造RUN_SNAPSHOT/DECISION_RUN或重标artifact即证伪 |
| Feedback暗中进入learning | import/call graph及side-effect test监控eligibility/learning owners零调用 | 任一eligibility、ingest、rule/weight writer调用即证伪 |
| Task 10越权修复owner | changed-path gate区分owner prerequisite与tests-only task | Task 10修改`engine/f09/`或生成authority helper即证伪 |

## 11. Gate与唯一下一合法动作

**Gate：`BLOCKED`。**

- 不是 `PASS`：当前不存在可供 Task 9 调用的 public artifact projection/key construction authority，也不存在覆盖两个 opt-in tracks且绑定current run的 public feedback authority。
- 不是 `REVISE`：这些缺口不能只靠改写 Task 9 amendment 文档收敛；那会把 frozen Task 7/8 semantic ownership偷偷搬进application或caller。
- `T9-C-02` 与 `T9-C-07` 已形成唯一 amendment裁决，但不得单独解锁合同修订，因为phase chain仍在artifact authority与feedback authority处中断。

**唯一下一合法动作：** 新开一个独立、role-separated 的 **G6 Task 9-P prerequisite authority amendment**，仅裁决并冻结本文件 P-1/P-2 的 public APIs、semantic material、track protocol与两个closed implementation write sets；该前置 amendment独立通过前，不得修改当前 Task 9 合同、application、Task 10 tests或任何 production owner。