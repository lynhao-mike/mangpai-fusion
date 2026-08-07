# G6 / Task 8 R39：受限 preprod run-manifest feedback adapter 合同

**状态：PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE — P-1 public verified-run-manifest fixture/provisioning seam 已获独立 evidence-bounded freeze；R39 已完成独立 admission、白名单内 implementation、修订后的 fresh STATIC_REVIEW、授权后的精确 verification 与 fresh EVIDENCE_REVIEW。冻结仅覆盖本文件约束的 feedback adapter 及其两个精确 selectors；不得推定 P-1 范围外正确性、Task 9/P-2 admission/implementation/verification/freeze、全仓正确性或 GitHub 同步。受控会话未执行 GitHub-mutating operation。**

## 1. Gate 身份、范围与裁决

本文件是 `G6 / Task 8` 的独立 **feedback adapter contract revision R39**。它只约束将既冻结的 V5/V6 preprod run-artifact manifest 身份接入 feedback owner 的受限适配层。

### 1.1 直接前置事实

下列 P-1 surface 已被上游独立 implementation、verification 与 evidence-bounded freeze 证明，可作为本合同唯一允许的跨 owner 运行时依赖：

```python
validate_run_artifact_manifest_v1(
    manifest: ArtifactSetManifest,
) -> DigestRef
```

该 verifier 的定义在 [`engine/f09/artifacts.py`](../engine/f09/artifacts.py:1582)。它是 run-manifest 完整性、角色闭包、run key 与 digest 语义的唯一权威验证入口。

`RunArtifactSetKeyV1` 的定义在 [`engine/f09/artifacts.py`](../engine/f09/artifacts.py:87)，是 run graph 的唯一 key carrier；`IdempotencyKey` 仍仅服务 legacy artifact graph，定义在 [`engine/f09/artifacts.py`](../engine/f09/artifacts.py:63)。

### 1.1.1 R39 fixture/provisioning 前置条件（修订）

R39 的 feedback 测试不得导入 P-1 underscore/private builder，也不得复制 run key serializer、canonicalizer 或 digest preimage。要为 P79–P85 构造 exact verified run manifest，P-1 owner 必须先提供一个**公开、无副作用、只读或纯构造的 fixture/provisioning seam**：该 seam 只返回已由 P-1 public verifier 接受的 `ArtifactSetManifest`，并使 feedback 测试无需了解或重建 `RunArtifactSetKeyV1.canonical_key_digest` 的私有计算。

该 seam 不属于 R39 whitelist，不得由 feedback owner 实现、模拟、monkeypatch 成为 acceptance 证据，亦不得用历史 lifecycle test 的 private fixture 替代。在该 seam 存在、由 P-1 owner 独立验证且获得后续 R39 implementation Gate 明确重新激活前，本 Gate 为 `BLOCKED`。

### 1.2 与 R38 的关系

[`plans/g6-task8-r38-contract.md`](g6-task8-r38-contract.md) 保持不改，且继续规定其 legacy/prod feedback contract。

R39 不重写 R38，也不追溯改变 R38 已有证据。对本文件第 2 节限定的 **restricted V5/V6 preprod run-manifest adapter**，若 R38 的下列历史性表述与本文件冲突，则仅在该限定范围内以 R39 为准：

1. R38 的“唯一且完整 revision”表述；
2. R38 对 `12 structural + P01–P70 = 82` 的静态 accounting 断言；
3. R38 对 future feedback tests 不得新增 node 或 P-ID 的限制；
4. R38 中将所有 `ArtifactSetManifest` 一律按 legacy record digest 与 legacy `IdempotencyKey` 处理的隐含前提。

该有限 supersession **不**授权改动 R38、改变 production/default 行为、扩展 legacy key 的 domain，或将 R39 规则传播到 Task 9/P-2。

### 1.3 本 Gate 的结论边界

本文件完成后只可进入 fresh independent CONTRACT review。即便该 review PASS，也只代表可以单独请求/激活 feedback adapter 的 implementation Gate；不代表 [`engine/f09/feedback.py`](../engine/f09/feedback.py) 已正确实现，不代表任何 pytest 已运行，不代表 Task 9 合同可启动，也不代表 GitHub 有任何同步或变更。

## 2. 冻结目标与非目标

### 2.1 唯一目标

在 feedback owner 内增加一个 **模块私有、fail-closed 的 restricted identity adapter**，使 exact `PreprodRunAuthority`、exact `RunTrack.V5_V6_PREPROD`、exact `RunArtifactSetKeyV1` 和 exact P-1 run manifest 可被 feedback authority validation 使用，同时保持所有 legacy manifest 和所有 production authority 的既有行为及 canonical bytes 不变。

### 2.2 非目标

以下均不在本合同或其后实现授权内：

- 不创建、写入、读取或 reconcile run artifacts；
- 不修改 P-1 artifact lifecycle、run serializer、run digest 或 P-1 tests；
- 不扩展、重定义或向 `IdempotencyKey.operation` 增加 `PROJECT_RUN_ARTIFACT_SET`；
- 不公开 private context、public boolean、environment switch、global toggle 或 caller-supplied “restricted” capability；
- 不通过 artifact role 字符串、manifest 角色集合或 manifest 字段值推断 privilege；
- 不改变 ordinary legacy manifest 的 records/digest/canonicalization；
- 不调用 `bind_feedback_operation()`、`evaluate_learning_eligibility()` 或 `validate_learning_eligibility()` 作为 adapter validation 的副作用；
- 不使 `STAGED_L6` 可构造、可消费或可进入 feedback/learning；
- 不修改 Task 9/P-2 文件、版本化 callable/envelope 或 public API；
- 除本文件第 8 节列明、且仅在本状态行的 verification 授权内执行的两个 R39 selectors 外，不运行 Python、pytest、Git、远端或 GitHub 操作；尤其不得借此执行 Task 9 或 P-2 selector。

## 3. 未来 implementation 的精确本地 write whitelist

仅在 R39 fresh CONTRACT PASS 后、且 controller 激活独立 implementation Gate 时，允许为本合同目的修改：

```text
engine/f09/feedback.py
tests/f09/test_feedback_eligibility.py
```

本合同起草阶段的唯一写入是：

```text
plans/g6-task8-r39-feedback-adapter-contract.md
```

任何新增文件、重命名、删除、格式化扫改、依赖安装、P-1 owner 修改、Task 9 修改、local Git 或 GitHub operation 都在 whitelist 外，必须 STOP。尤其第 1.1.1 节要求的 public fixture/provisioning seam 必须通过 P-1 owner 的独立 contract、write whitelist、implementation、verification 与 freeze；R39 不得越权实现它。

## 4. 受限身份模型

### 4.1 exact discriminants

restricted branch 仅当以下全部成立时才可被创建及消费：

1. `type(authority) is PreprodRunAuthority`；
2. `authority.track is RunTrack.V5_V6_PREPROD`；
3. `type(authority.manifest) is ArtifactSetManifest`；
4. `type(authority.manifest.key) is RunArtifactSetKeyV1`；
5. `authority.manifest.key.operation == "PROJECT_RUN_ARTIFACT_SET"`；
6. P-1 public verifier [`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1582) 成功，并返回该 manifest 的 recomputed records digest：即当前 P-1 实现对 `manifest.records` 调用 [`digest_artifact_records()`](../engine/f09/artifacts.py:761) 的返回值；feedback 仅消费该返回值，不重算、不复制 serializer，也不另造 run-graph digest 或 preimage；
7. authority 的 `case_id`、`run_id`、track、ref roles 与 key/manifest 中重算的同名 material 精确一致；
8. refs 的有序角色闭包恰为 `RUN_SNAPSHOT`、`DECISION_RUN`、`FEEDBACK_ATTACHMENT`、`MANIFEST`，且每一 ref 的 exact identity 与 validated manifest/authority material 一致。

任何一步不满足、任意 subtype、任意 mixed key、任意 verifier 异常或 digest/identity mismatch 都必须在触及 restricted downstream material 前 typed fail closed。不得 fallback 到 legacy branch。

### 4.2 私有 carrier

未来实现必须在 [`engine/f09/feedback.py`](../engine/f09/feedback.py) 中定义冻结、模块私有的 carrier，推荐且冻结的形态如下：

```python
@dataclass(frozen=True)
class _PreprodRestrictedManifestContext:
    authority: PreprodRunAuthority
    manifest: ArtifactSetManifest
    case_id: str
    run_id: str
    track: RunTrack
    key: RunArtifactSetKeyV1
    roles: tuple[str, ...]
    verifier_returned_records_digest: DigestRef
```

该 type 不得被导出、加入 `__all__`、写入 public dataclass、接受为 public function parameter，或可由 caller 直接构造为授权凭证。

private 名称、frozen dataclass 与传入 object 都不是 security capability。每个使用该 carrier 的 restricted helper 必须独立重验：

- `type(context) is _PreprodRestrictedManifestContext`；
- `context.authority is current_authority`；
- `context.manifest is current_manifest`（需要 manifest 参数的 helper）；
- authority/manifest/key 的 exact types 与 track；
- 重算后的 case/run/track/key/roles material；
- P-1 public verifier 返回的 recomputed records digest 与 `context.verifier_returned_records_digest` 的 equality；feedback 不重算、不另造 run-graph digest 或 preimage。

在任一 helper 中仅检查 `isinstance`、仅比较 value equality、仅信任此前 helper 已验证、或根据 private 字段名推断授权，均为合同违例。

### 4.3 创建点与 validation order

restricted context 只能在 `PreprodRunAuthority` 的 authority self-excluded validation 路径中、完成所有 exact type/track/key/identity guards 后创建。推荐实现采用一个 module-private builder，例如：

```python
def _validated_preprod_restricted_manifest_context(
    authority: PreprodRunAuthority,
) -> _PreprodRestrictedManifestContext | None: ...
```

该 helper 必须：

1. 对非 exact `PreprodRunAuthority`、非 `V5_V6_PREPROD` 或非 run key 返回 `None`，不将其解释为 restricted；
2. 对看似 restricted 但任何 material/verifier 不一致的输入抛出 typed contract/integrity failure；
3. 在调用任何 run-specific payload builder 前调用 P-1 public verifier；
4. 不调用 artifacts 私有 symbol、不复制 P-1 serializer/digest material；
5. 不做 I/O、不写 state、不调用 feedback binding 或 learning API。

`STAGED_L6` 必须在 authority construction/validation 的 closed track guard 中被拒绝；它既不得得到 context，也不得走 legacy fallback 以成为可消费 feedback authority。

## 5. Legacy 与 run manifest digest 分流

### 5.1 唯一 digest selector

反馈 owner 必须有单一、私有、可审计的 manifest digest selection seam。其语义冻结如下：

| manifest 分类 | key | digest authority | 允许行为 |
|---|---|---|---|
| ordinary legacy | exact `IdempotencyKey` | existing [`digest_artifact_records()`](../engine/f09/artifacts.py:761) | 维持既有 records shape、digest 与 canonical bytes |
| restricted preprod run | exact `RunArtifactSetKeyV1` + validated context | [`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1582) 返回的 recomputed records digest（当前实现为 [`digest_artifact_records(manifest.records)`](../engine/f09/artifacts.py:761)） | 仅使用 verifier 返回值；禁止 legacy serializer、feedback 重算或另造 run-graph digest/preimage |
| 其它或混合 | 任何 | 无 | typed fail closed |

feedback owner 不得将 run manifest 或其 records 直接送入 [`digest_artifact_records()`](../engine/f09/artifacts.py:761)；restricted branch 只能调用 public [`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1582) 并消费其返回值。该限制不禁止 verifier owner 在既冻结的 P-1 实现内部为计算其 recomputed records digest 而调用该函数。legacy manifest 绝不得用 public run verifier 作为 silent fallback；verifier-returned recomputed records digest 与 legacy digest 也绝不得 cross-swap 后继续生成 authority digest。

### 5.2 Key material 不扩展 legacy API

现有 legacy [`_idempotency_key_material()`](../engine/f09/feedback.py:682) 的输入 domain 仍为 exact `IdempotencyKey`，不得改为接受 union，也不得把 `PROJECT_RUN_ARTIFACT_SET` 加入其 operation closure。

未来实现必须以与 legacy helper 分离的 private run-key material path 表达 exact `RunArtifactSetKeyV1`；该 path 的 material 必须由 context 重验后的 current key 产生。它不得复刻 P-1 的 run key serializer，不得调用 [`engine/f09/artifacts.py`](../engine/f09/artifacts.py) 的 underscore symbol，也不得把 key `repr`、`__dict__`、反射结果或 caller payload 用作 canonical material。

### 5.3 Records shape 与 MANIFEST outer-ref

现有 [`_manifest_records_shape()`](../engine/f09/feedback.py:904) 和 [`_manifest_identity()`](../engine/f09/feedback.py:1001) 只可在 ordinary legacy branch 保持既有语义。

restricted run branch 的 `MANIFEST` 处理必须是 outer-ref 专用分支：

- `RUN_SNAPSHOT`、`DECISION_RUN`、`FEEDBACK_ATTACHMENT` 继续按已验证的 run records 匹配；
- `MANIFEST` 只匹配 authority 的 outer manifest ref 与 manifest identity/digest material；其 exact acceptance 为 `object_type == "MANIFEST"`、`object_id == authority.manifest.manifest_id`、exact `DigestPresent` binding 的 digest 等于 public verifier 返回的 recomputed records digest；feedback 不重算、不另造 run-graph digest 或 preimage；
- `ArtifactSetManifest` 当前 owner shape没有独立 schema/contract fields，故 R39 不得伪造“P-1 manifest schema/contract identity”、也不得对 MANIFEST ref 的 `schema_version` 或 `contract_version` 添加不存在的 equality target；这两个 ref 字段仅按 R38 既有 `VersionedObjectRef` shape 规则验证；
- outer ref 的 object-id 或 digest mismatch 为 `INVALID / INVALID_MATERIAL`；不存在可验证 outer manifest identity 才是 `UNBOUND / TARGET_NOT_FOUND`；不得把 outer mismatch 降级为普通 records mismatch；
- 不查询 records 寻找 `artifact_role="MANIFEST"`；
- 不要求、制造或容忍 self-referential `ArtifactRecord(artifact_role="MANIFEST")`；
- outer-ref identity、case/run/track/key/roles 和 verifier-returned recomputed records digest 任一不一致都 typed fail closed。

## 6. Future helper contract

未来实现可为本合同增加/调整**私有** helpers，但不得改变 public callable surface。若将 existing helpers 增加 restricted 参数，参数仅可 keyword-only 且不得由 public caller 传入；推荐冻结的语义接口为：

```python
def _manifest_records_shape(
    manifest: ArtifactSetManifest,
    *,
    restricted_context: _PreprodRestrictedManifestContext | None = None,
    current_authority: PreprodRunAuthority | None = None,
) -> tuple[ArtifactRecord, ...]: ...

def _manifest_identity(
    manifest: ArtifactSetManifest,
    *,
    restricted_context: _PreprodRestrictedManifestContext | None = None,
    current_authority: PreprodRunAuthority | None = None,
) -> dict[str, JcsValue]: ...
```

对 restricted manifest：`_manifest_records_shape()` 只返回 P-1 verifier 已认可的 non-MANIFEST run records，或由明确的 private run-only equivalent 直接提供同一受限用途；它不得触发 legacy key material 或 legacy digest。

对 ordinary manifest：没有 context 时必须保留当前 exact legacy behavior；若 manifest 看起来是 run key 但 context 缺失，必须 typed fail closed，而非退回 ordinary logic。

任何 helper 同时接收 `restricted_context` 与 `current_authority` 时，缺其中之一、类型不 exact、identity 不同、track/key 不匹配都必须 typed fail closed。

## 7. 结构、不变量与副作用约束

未来 implementation 必须同时满足：

1. feedback 只新增 public artifacts imports：`RunArtifactSetKeyV1` 与 `validate_run_artifact_manifest_v1`；不得导入任何 artifacts underscore symbol；
2. 不复制或近似复制 P-1 run serializer、canonicalizer、digest construction 或 lifecycle implementation；
3. 不新增 filesystem、network、clock、environment、subprocess、database、tools 或 runtime side-effect imports；现有 [`test_no_side_effect_import_or_runtime_surface()`](../tests/f09/test_feedback_eligibility.py:1659) 的边界继续有效；
4. 仅 exact `RunTrack.V5_V6_PREPROD` 可进入 run adapter；production/default authority 不得获得 run context；
5. legacy production/preprod samples 的 receipt status、issues、digest 和 bytes 不得变化；
6. verifier exception 必须保持 typed failure boundary，不得被吞掉、降级、转换为 success 或转入 legacy fallback；
7. 不得由 adapter 直接或间接调用 `bind_feedback_operation()`、`evaluate_learning_eligibility()`、`validate_learning_eligibility()`；
8. 不得新增 writer、mutation、learning、eligibility 或 feedback binding side effect；
9. 不得改变 R38 已冻结的 public dataclass shape、public unions、protocol 或 public function signatures；
10. 不得更改 P-1 artifacts owner 或 Task 9 owner 文件。

## 8. Future verification contract与 accounting

本 R39 contract drafting Gate 不运行命令。R39 implementation 停止且 fresh STATIC_REVIEW PASS 后，本状态行的独立 verification 授权仅允许下列 selector：

```text
python -m pytest tests/f09/test_feedback_eligibility.py -q
python -m py_compile engine/f09/feedback.py tests/f09/test_feedback_eligibility.py
```

working directory 必须为 repository root；命令执行前必须再次筛查 GitHub/remote side effect，且完整记录 collection、pass/fail/error、exit code、rerun 与失败历史。上述 selectors 只验证 feedback owner 范围，不证明 P-1、Task 9、P-2 或全系统正确性。仅当 fresh EVIDENCE_REVIEW PASS、静态/动态计数 reconciled 且明确记录直接证明与禁止推断边界时，才可冻结 R39；R39 freeze 不授予 Task 9 或 P-2 的任何后继 Gate。

### 8.1 取代 accounting 的精确规则

R39 implementation 必须把 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py:1667) 中的 R38-only guard 改名为 `test_static_accounting_is_exactly_16_plus_94`，并替换为下列唯一 R39 accounting model：

```text
12 base structural + 4 named restricted-context structural = 16 structural
70 base falsifiers + 24 restricted-context falsifiers = 94 parameterized falsifiers
16 structural tests + 94 parameterized falsifiers = 110 collected test instances
```

其中：

- `test_contract_falsifier_ledger` 不计入 structural tests；static accounting function 本身计入 16 structural tests，不得第二次相加；
- falsifier 参数化仅允许连续的 `P01` 至 `P94`，不允许重复、跳号或额外 P-ID；
- accounting guard 必须直接断言 literal `12, 4, 16, 70, 24, 94, 110`、完整 node name/ID sequence、AST structural count、ledger length 与 `94 + 16 = 110`；不得用 `>=`、占位值或从被测 collection 反推 expected 值；
- 旧的 82-count 不能与新的 110-count 同时作为有效断言；
- 该 replacement 只适用于 feedback eligibility test file；R38 文件和其历史事实不改。

### 8.2 新增 P71–P94 falsifier ledger

R39 要求新增以下 24 个 parameterized falsifiers；每项应只断言一个最小 fail-closed 或 preservation 性质：

| ID | 最小 falsifier |
|---|---|
| P71 | `restricted_context_exact_runtime_type_required`：context 不是 exact private runtime type 时 typed fail closed，restricted branch 不执行 |
| P72 | `restricted_context_subclass_or_proxy_rejected`：context 为 subclass 或 proxy 时 typed fail closed，restricted branch 不执行 |
| P73 | `restricted_context_authority_identity_rechecked`：context authority 与 current authority 非同一对象时 typed fail closed |
| P74 | `restricted_context_manifest_identity_rechecked`：context manifest 与 current manifest 非同一对象时 typed fail closed |
| P75 | `restricted_context_stale_case_material_rejected`：context 的重算 case material 不一致时 typed fail closed |
| P76 | `restricted_context_stale_run_track_key_roles_material_rejected`：run、track、key 或 roles material 任一不一致时 typed fail closed |
| P77 | `restricted_helper_direct_call_rejected`：direct restricted-shaped call 在 context/companion 缺失、非 exact、stale、swap 或 material mismatch 时 typed fail closed；不得要求 helper 识别不可观察的 caller provenance |
| P78 | `restricted_call_graph_unique_orchestrator_site`：AST fixture mutation 引入第二个 restricted-helper orchestrator call 后 static gate 必须失败 |
| P79 | `public_run_manifest_verifier_accepts_exact_verified_run_manifest`：仅在第 1.1.1 节 public fixture/provisioning seam 已可用时，exact verified run manifest 返回 recomputed records `DigestRef`，即当前 P-1 对 `manifest.records` 调用 [`digest_artifact_records()`](../engine/f09/artifacts.py:761) 的返回值 |
| P80 | `public_run_manifest_verifier_rejects_non_run_operation`：非 exact `PROJECT_RUN_ARTIFACT_SET` operation typed fail closed |
| P81 | `public_run_manifest_verifier_rejects_invalid_run_role_closure`：records roles 相对 exact `key.projection_roles` 缺失、重复、错序，或包含 statement/额外 role 时 typed fail closed；public verifier 保留 key 所声明的合法两角色或三角色 closure，restricted adapter 对四个 outer refs 的闭合要求是更窄的 adapter policy |
| P82 | `public_run_manifest_verifier_rejects_attempt_refs_graph_mismatch`：retained attempt refs graph mismatch typed fail closed |
| P83 | `public_run_manifest_verifier_rejects_case_track_run_or_state_mismatch`：case、track、run-id、record state 或 manifest state mismatch typed fail closed |
| P84 | `public_run_manifest_verifier_preserves_legacy_statement_bytes`：public verifier 加入后 legacy statement bytes/digest byte-for-byte unchanged |
| P85 | `public_run_manifest_verifier_rejects_run_legacy_digest_cross_swap`：verifier-returned recomputed records digest 与 legacy digest cross-swap typed fail closed |
| P86 | `manifest_outer_ref_valid_restricted_regression`：有效 restricted MANIFEST outer-ref 保持合同规定 acceptance |
| P87 | `manifest_outer_ref_identity_mismatch_regression`：MANIFEST outer-ref object-id 或 digest mismatch typed fail closed |
| P88 | `manifest_outer_ref_duplicate_or_self_record_regression`：duplicate outer ref 或 self-referential MANIFEST record typed fail closed |
| P89 | `ordinary_target_refs_record_matching_regression`：non-MANIFEST refs 维持既有 record matching |
| P90 | `feedback_adapter_has_no_artifacts_private_helper_import`：AST fixture mutation 加入 artifacts underscore import 后 static gate 必须失败 |
| P91 | `feedback_adapter_has_no_run_serializer_or_digest_copy`：AST fixture mutation 加入 run serializer/digest definition 或 copied canonical preimage 后 static gate 必须失败 |
| P92 | `feedback_adapter_stops_without_frozen_public_verifier`：P-1 public verifier prerequisite 未完成则 adapter implementation STOP |
| P93 | `feedback_adapter_calls_only_public_run_manifest_verifier`：restricted feedback validation 仅调用 public verifier，不调用 private seam |
| P94 | `serial_owner_gate_preserves_zero_binding_learning_calls`：P-1 或 adapter Gate 未完成、或 validation failure 时 binding/eligibility/learning 均为零 calls |

新增四个 structural tests 的 exact names 与职责必须是：

1. `test_restricted_context_contract_ast_is_exact`：restricted context 不进入 public callable/type/field/signature，不存在 caller/global/environment trigger；
2. `test_restricted_context_call_graph_has_one_orchestrator_site`：唯一 orchestrator 与 restricted helper call-chain；
3. `test_restricted_context_helpers_revalidate_bound_objects`：每个 restricted helper 重验 exact context type、authority/manifest object identity 与重算 material；
4. `test_feedback_adapter_uses_public_run_manifest_verifier_only`：仅导入/调用 public verifier，禁止 artifacts underscore import 与 run serializer/digest copy。

MANIFEST outer-ref 的 source/behavior、literal accounting 和 P01–P94 sequence 应在上述 named structural tests 与对应 parameterized falsifier 中一对一覆盖，不得新增第五个 structural node。尤其 P78、P90 与 P91 必须是 parameterized AST fixture/mutation oracles；不得把它们换成行为 case 或重复计入 structural count。现有 R38 structural tests 必须保留或仅作机械调整以反映 R39 accounting；不得通过删除 legacy coverage 来凑计数。

## 9. Fresh independent CONTRACT review 问题

reviewer 必须在 fresh context 中仅根据本合同、P-1 public surface 与当前 owner baseline 回答：

1. R39 是否明确且有限地覆盖 R38 的冲突条款，同时没有修改 R38 或扩大到 Task 9？
2. run graph 是否严格使用 exact `RunArtifactSetKeyV1` 与 public verifier，且没有扩展 legacy `IdempotencyKey`？
3. private context 是否在每个 helper 重验 exact type、object identity 与 material，而非把 private name 当 capability？
4. run/legacy selector、digest cross-swap 与 verifier error 是否均 fail closed？
5. `MANIFEST` 是否只走 outer-ref 专用分支，且不依赖 self-referential record，并且未对当前 `ArtifactSetManifest` owner shape不存在的 schema/contract identity 作出伪造要求？
6. 是否保持 zero I/O、zero feedback/learning side effect、`STAGED_L6` unsupported 与 public API stability？
7. whitelist、test selectors、110 accounting、P71–P94 ledger、direct-evidence boundary 与 STOP 是否机械可审计？
8. 本合同是否避免将 CONTRACT PASS 误表述为 implementation/verification/freeze PASS，且不存在 GitHub mutation？

review verdict 只能为 `PASS`、`REVISE`、`BLOCKED` 或 `AUTHORIZATION_REQUIRED`，并必须按问题逐项给出可定位证据。reviewer 不得修复合同或实现代码。

## 10. STOP conditions 与禁止推断

发生任一情形立即 STOP 并记录为 `REVISE` 或 `BLOCKED`，不得开始 implementation：

- P-1 public verifier/key surface 与本合同所列签名不一致；
- 第 1.1.1 节要求的 public verified-run-manifest fixture/provisioning seam 不存在、未由 P-1 owner 验证，或需要 feedback owner 使用 P-1 private builder/serializer copy 才能构造 P79–P85 fixture；
- 需要修改 whitelist 外文件；
- 需要 artifacts private import、serializer copy 或 legacy key domain 扩展；
- 需要公开 caller flag/context 或环境/global switch；
- 需要 I/O、writer、binding、learning 或 `STAGED_L6` 支持；
- R39 accounting 不能同时保留 legacy evidence并机械达到 110；
- fresh review 发现任何 scope、identity、MANIFEST 或 fail-closed gap；
- 任意拟议操作会触发 GitHub service-side mutation。

本合同直接证明的仅是：R39 的目标、边界、前置依赖、future whitelist、invariants、falsifiers、selectors 与 review question 已被书面冻结。它**不证明**未来实现存在、测试收集为 110、测试通过、反馈行为正确、P-1 外的依赖正确、Task 9 已获准，或任何远端/GitHub 状态。

## 11. 当前 Gate 记录

```text
Unit: G6 / Task 8 R39 — feedback adapter contract
Current stage: FREEZE
Current verdict: PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE
Frozen scope: engine/f09/feedback.py 与 tests/f09/test_feedback_eligibility.py 中的 R39 restricted preprod run-manifest adapter；不扩张到 P-1、Task 9、P-2、public API 或全仓
Fresh review chain: independent admission PASS；P-1 public fixture/provisioning seam evidence-bounded frozen；implementation whitelist complete；修订后的 fresh STATIC_REVIEW PASS；verification/freeze authorization fresh review PASS；fresh EVIDENCE_REVIEW PASS
Authorized verification evidence: repository root；`python -m pytest tests/f09/test_feedback_eligibility.py -q` → 110 passed in 27.14s, exit 0；`python -m py_compile engine/f09/feedback.py tests/f09/test_feedback_eligibility.py` → exit 0
Static/dynamic reconciliation: static accounting = 12 base structural + 4 restricted-context structural + 70 base falsifiers + 24 restricted-context falsifiers = 110；dynamic pytest passed = 110；difference = 0；reconciled = YES
Remote-side-effect screening: two commands are local Python test/bytecode-compilation selectors; command text contains no Git, remote, GitHub CLI/API, publish or deployment operation. 本受控会话未执行 GitHub-mutating operation。
Invalid/historical evidence: prior feedback selector 25 failures 与此前未经本 Gate 授权的 selector runs 均为历史证据；不得替代上述 fresh verification evidence。
Directly proven: selected feedback-owner test scope currently passes all 110 collected instances；P91 mutation oracle rejects named serializer/canonicalizer copies及包含 canonical-preimage domain sentinel 的顶层和嵌套改名复制；selected Python files compile.
Not proven: full suite/system-wide correctness；P-1 范围外正确性；Task 9/P-2 correctness、admission 或 authorization；所有安全性质；GitHub 全局未变；GitHub synchronization、PR、merge、deployment 或 publication。
Explicit exclusions: engine/f09/artifacts.py、P-1 tests、Task 9/P-2 files、public API、new files/dependencies、Git、remote and GitHub operations
Unique next legal action: 对现行 Task 9-P/P-2 upstream reconcile 文档执行 fresh independent、read-only review，以裁定其自身 `REVISE — ready for fresh independent review` 是否可 PASS；在该 Gate 及后续串行前置条件分别闭合前，Task 9 contract/implementation 与 P-2 仍不得启动。
```
