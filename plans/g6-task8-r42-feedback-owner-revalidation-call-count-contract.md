# G6 / Task 8 R42 feedback-owner restricted-context revalidation / call-count amendment 合同

- **Unit：** R39 feedback-owner private-helper revalidation 与 manifest-verifier call-count amendment（仅文档）
- **Gate：** `R42 — PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`
- **现行依赖：** R39 的 frozen adapter/runtime、R40 `REVISE`、R41 issuance-proof contract `PASS`；P-2 `BLOCKED`；Task 9-P `BLOCKED`；Task 9 amendment `STILL_OPEN`。
- **实现授权：** R42 的历史 implementation write set 已关闭；本文件的 §8–§10 仅记录 review、evidence 与 freeze，未授权其他 runtime、tests、Python、pytest、Git、远端或 GitHub operation。
- **作者写集：** 本合同及 R42 history 内的条件实现 write set，均已结束。

## 1. Admission 与阻断事实

R40 的 fresh read-only review 已证明：单次 [`_preprod_authority_self_excluded_material()`](../engine/f09/feedback.py:1361) 调用会触发**四次** [`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1683)：

1. [`_validated_preprod_restricted_manifest_context()`](../engine/f09/feedback.py:970) 在创建 context 时首次调用 verifier；
2. owner helper 直接调用 [`_manifest_records_shape()`](../engine/f09/feedback.py:1082)，其 restricted branch 经 [`_revalidate_preprod_restricted_manifest_context()`](../engine/f09/feedback.py:1026) 第二次调用 verifier；
3. [`_manifest_identity()`](../engine/f09/feedback.py:1200) 内嵌调用 `_manifest_records_shape()`，该 branch 经同一 revalidator 第三次调用 verifier；
4. `_manifest_identity()` 随后直接调用 `_revalidate_preprod_restricted_manifest_context()`，第四次调用 verifier。

R40 所需 owner-owned path 要求恰一次。R42 因而必须覆盖以上完整四点 call graph，而不得将其误记为三次。

R39 的 [`plans/g6-task8-r39-feedback-adapter-contract.md`](g6-task8-r39-feedback-adapter-contract.md:120) 原冻结语义要求每个 restricted helper 重验 verifier-returned digest。该要求正确地拒绝把 private context 视作 capability，但没有区分：

1. **本次 authority-material operation 的一次 P-1 manifest integrity verification**；与
2. **同一不可变 authority / manifest object 上、每个 restricted helper 必须做的 exact identity 与 structural revalidation**。

本 amendment 仅解决该 call-count 矛盾；不改变 R39 的 restricted domain、public API、legacy branch、digest owner、four-role closure、P-1 artifact owner、R41 issuance proof 或 Task 9/P-2 Gate。

## 2. 精确 supersession 与不变量

本文件仅在 R39 restricted `RunArtifactSetKeyV1` branch 内取代 R39 第 4.2 节第 127 行“每个 helper 必须再次调用 P-1 public verifier 并比较 digest”的含义。R39 对 exact type、object identity、case/run/track/key/roles、record joins、MANIFEST outer-ref、typed fail-closed、zero side effect 和 legacy preservation 的其余要求完整保留。

对一次 `_preprod_authority_self_excluded_material()` 的 restricted successful evaluation，唯一允许的 P-1 manifest verifier 调用数精确为 **1**：

```text
exact PreprodRunAuthority / V5_V6_PREPROD / RunArtifactSetKeyV1 guards
→ validate_run_artifact_manifest_v1(manifest) exactly once
→ create operation-local restricted context containing returned digest
→ structural revalidation in all downstream private helpers, with zero further verifier calls
→ canonical material
```

下列条件同时冻结：

1. verifier 必须在任一 run-specific record material、MANIFEST outer-ref acceptance 或 canonical material 产生前执行；
2. verifier typed failure 原样 fail closed；其后 restricted helper、material、authority digest、binding、eligibility 与 learning 调用数均为零；
3. verifier success 后的 downstream revalidation 不得重新调用 verifier，且不能将 context 名称、frozen dataclass 或先前 success 当作 capability；
4. downstream revalidation 仍必须 exact-check context type、`context.authority is current_authority`、`context.manifest is current_manifest`、current key exact type、track、operation、case/run/key/roles material、前三项 record joins 和 MANIFEST outer-ref 对 `context.verifier_returned_records_digest` 的 binding；
5. 任一 identity、shape、material、record 或 outer-ref mismatch 必须 typed fail closed，零 final material / authority；
6. 不得缓存、全局保存、跨 invocation 复用、公开、序列化、返回或由 caller 提供 restricted context；其生命周期严格限于当前 owner invocation 的私有 call chain；
7. R39 legacy `IdempotencyKey` branch 继续保持既有 `digest_artifact_records()` 路径、调用行为和 canonical bytes；不得改变。

## 3. 冻结 private helper surface 与职责

若后续获得独立 implementation authorization，future implementation 只能在 [`engine/f09/feedback.py`](../engine/f09/feedback.py) 使用以下模块私有结构；不得改变或新增 public callable、dataclass field、protocol、union 或 binder signature：

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


class _ManifestVerifierFailure(Exception):
    def __init__(self, error: F09ContractError | F09IntegrityError) -> None: ...


def _validated_preprod_restricted_manifest_context(
    authority: PreprodRunAuthority,
    *,
    propagate_manifest_verifier_failure: bool = False,
) -> _PreprodRestrictedManifestContext | None: ...


def _revalidate_preprod_restricted_manifest_context(
    context: _PreprodRestrictedManifestContext | None,
    authority: PreprodRunAuthority | None,
    manifest: ArtifactSetManifest | None,
) -> _PreprodRestrictedManifestContext: ...
```

职责精确冻结如下：

- [`_validated_preprod_restricted_manifest_context()`](../engine/f09/feedback.py:975) 是唯一 verifier-owning builder：它先完成 exact restricted admission guards，后恰一次调用 [`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1683)，并仅用 returned digest 创建 operation-local context。默认 `propagate_manifest_verifier_failure=False` 保持其现有 typed-failure surface；仅公开 operation owner 可传入 `True`。此时 builder 只在该**唯一 public verifier call**抛出 [`F09ContractError`](../engine/f09/errors.py:24) 或 [`F09IntegrityError`](../engine/f09/errors.py:29) 时，以 module-private [`_ManifestVerifierFailure`](../engine/f09/feedback.py:213) 保存同一 exception object。它不得标记、包装或改变任何 builder guard、post-verifier structural revalidation、authority digest、schema/contract digest 或 downstream failure。
- [`_revalidate_preprod_restricted_manifest_context()`](../engine/f09/feedback.py:1026) 是 verifier-free structural revalidator：它不得调用 P-1 verifier、digest serializer、filesystem、network、clock、environment、binding 或 learning；但必须完成第 2 节第 4 项列出的 exact identity/material/ref closure rechecks，并返回同一 context 或 typed fail closed。
- [`_preprod_authority_self_excluded_material()`](../engine/f09/feedback.py:1373) 仅可把该 keyword propagation intent 透传给 builder；不得自行分类、调用或重试 verifier。
- [`_compute_operation()`](../engine/f09/feedback.py:2040) 仅可捕获 `_ManifestVerifierFailure` 并 `raise failure.error`，从而由 [`bind_feedback_operation()`](../engine/f09/feedback.py:2138) 原样传播 sentinel object。其余 preprod authority/material 的 [`F09ContractError`](../engine/f09/errors.py:24) / [`F09IntegrityError`](../engine/f09/errors.py:29) 必须留在既有 invalid-operation fallback；不得按异常 class 广泛重抛。
- [`_manifest_records_shape()`](../engine/f09/feedback.py:1089) 与 [`_manifest_identity()`](../engine/f09/feedback.py:1207) 在 restricted branch 可以各调用 revalidator；这种重复 structural revalidation 被允许，且不得额外调用 manifest verifier。
- context 返回的 digest 是唯一允许供 restricted MANIFEST outer-ref、run-manifest identity material 与 supplied `manifest.digest` equality 使用的 records digest；feedback 不得自行重算、替换或升级该 digest。

## 4. 失败处置与负向 ledger

| ID | 原子负向条件 | 必须结果 |
|---|---|---|
| R42-F01 | 非 exact authority、非 V5/V6、非 exact run key、context 缺失/非 exact/subclass/proxy | typed fail closed；零 P-1 verifier（若 restricted admission 未达）/零 material/零 authority。 |
| R42-F02 | builder 前 guard 已通过但 P-1 verifier failure | 原样 typed failure；恰一次 verifier；零 downstream revalidator/material/authority/binding/learning。 |
| R42-F03 | verifier success 后 authority/manifest object identity、case/run/track/key/roles、record join 或 MANIFEST outer-ref mismatch | typed fail closed；不再调用 verifier；零 final material/authority。 |
| R42-F04 | restricted successful evaluation 内出现第二次或更多次 P-1 manifest verifier 调用（包括 direct records-shape、identity 内嵌 records-shape 与 identity direct revalidator 三个既有重复点） | 合同违反；STOP。 |
| R42-F05 | 使用 cached/global/caller-provided/cross-invocation context 或把 context 当 capability | 合同违反；STOP。 |
| R42-F06 | legacy manifest 进入 restricted path，或 run manifest fallback 到 legacy digest path | typed fail closed；不得改变 legacy canonical bytes。 |
| R42-F07 | 新增 artifacts private import、P-1 serializer/digest copy、I/O、binding、eligibility 或 learning | 合同违反；STOP。 |
| R42-F08 | 公开 [`bind_feedback_operation()`](../engine/f09/feedback.py:2122) 的 exact restricted-preprod 完整路径中，P-1 manifest verifier 抛出 sentinel typed failure | verifier 恰一次；公开入口原样抛出**同一异常对象**；在任何 invalid material、key、binding、receipt、eligibility 或 learning construction/call/return/persistence 前终止；上述六类调用与产物均为零；不得产生 partial/failure receipt、replacement key、binding candidate、eligibility/learning input/result，进入 legacy fallback 或第二次 verifier 均为合同违反并 STOP。 |

### 4.1 公开 operation verifier-failure 终止边界

本节仅补足 R42-F02 在公开 [`bind_feedback_operation()`](../engine/f09/feedback.py:2122) 完整 restricted-preprod operation 边界的可机械验证性；不改变既有 successful evaluation、private helper、public API、legacy branch 或其他 unit 的合同。

当 exact restricted-preprod operation 已通过必要 admission guards，进入 [`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1683) 且 verifier 抛出 typed failure 时：

1. verifier 必须精确调用一次；
2. [`bind_feedback_operation()`](../engine/f09/feedback.py:2122) 必须原样抛出 verifier 的**同一异常对象**，不得包装、重建、吞掉、降级为 operation result/receipt、转为 success 或进入 legacy fallback；
3. 失败必须先于 invalid material、key、binding、receipt、eligibility、learning 的任何 construction、call、return 或 persistence；六类调用数与产物数均为零；
4. 不得产生 partial/failure receipt、replacement key、binding candidate、eligibility input/result 或 learning input/result；
5. ordinary legacy branch 的调用顺序、异常边界、receipt status/issues/digest/bytes 与 canonical bytes 必须保持不变。

“原样”必须以异常对象 identity 验证，不得只比较异常类型或 message；“零产物”必须按六类分别观测，不得仅由公开入口没有返回值间接推断。

### 4.2 R42-F08 的封闭观察 ledger

R42-F08 的唯一未来测试必须先在 monkeypatch 前构造 exact restricted-preprod 的 `RawFeedbackAuthority`、其 raw submission、`prior=None` 与 clock；随后安装同一 sentinel typed failure 的 verifier stub。stub 只记录其接收的 `authority.manifest` 后 `raise sentinel`。测试仅经 [`bind_feedback_operation()`](../engine/f09/feedback.py:2122) 发起，并必须以 `caught.value is sentinel` 证明 exception identity。不得用替代 public entrypoint、private helper 直接调用、异常 type/message equality 或“入口无返回”代替该 oracle。

在 verifier stub 安装后，测试必须把下表每个闭合 seam 替换为“记录一次后立即 `pytest.fail`”的 probe；除 verifier 以外任何 probe 被调用即为 R42-F08 失败。每类的 calls 为对应 probe 的记录总数，outputs 为该类任何 constructor/helper 正常返回、append、yield、persist 或交给下一类的对象数。此路径没有 persistence API；因此 persistence 的唯一可观测代理是下表任何 receipt/binding/key/helper 正常返回或 collection append，均必须为零。

| 类别 | 封闭 observation seams（均须安装 fail-on-call probe） | 必须断言 |
|---|---|---|
| invalid material | [`_invalid_authority_material()`](../engine/f09/feedback.py:1528)、[`_invalid_schema_versions_digest_material()`](../engine/f09/feedback.py:1522)、[`_invalid_contract_digest_material()`](../engine/f09/feedback.py:1531)、[`_invalid_canonical_operation_identity_material()`](../engine/f09/feedback.py:1537) | calls = 0；outputs = 0。 |
| key | module-local [`IdempotencyKey`](../engine/f09/contracts.py:277) constructor 与 [`_canonical_operation_identity_material()`](../engine/f09/feedback.py:1512) | calls = 0；outputs = 0；不得产生 replacement/provisional key。 |
| binding | module-local [`FeedbackBinding`](../engine/f09/feedback.py:133) constructor 与 [`validate_feedback_binding_record()`](../engine/f09/feedback.py:2173) | calls = 0；outputs = 0；不得 append 或交付 binding candidate。 |
| receipt | [`_make_target_receipt()`](../engine/f09/feedback.py:2008) 与 module-local [`FeedbackOperationReceipt`](../engine/f09/feedback.py:262) constructor | calls = 0；outputs = 0；不得产生、append、返回或持久化 partial/failure receipt。 |
| eligibility | [`evaluate_learning_eligibility()`](../engine/f09/feedback.py:2296) 与 [`validate_learning_eligibility()`](../engine/f09/feedback.py:2356) | calls = 0；inputs/outputs = 0。 |
| learning | module-local [`LearningEligibility`](../engine/f09/feedback.py:310) constructor | calls = 0；outputs = 0；不得形成或交付 learning input/result。 |

测试还必须独立记录 verifier calls，并精确断言 `calls == [authority.manifest]`；不得把 verifier call log 与六类 probe log 合并。若未来生产实现新增任一在 verifier failure 后可构造、调用、返回、append、yield 或持久化上述六类对象的 seam，则该实现先违反本封闭 ledger，必须先修订本合同并取得新的 CONTRACT PASS，不能在测试中静默放行。

## 5. 条件 write set、静态 accounting 与未来验证

本 amendment drafting 的唯一 write 是：

```text
plans/g6-task8-r42-feedback-owner-revalidation-call-count-contract.md
```

仅当 R42 fresh CONTRACT review `PASS` 且 controller 另行显式激活 implementation Gate 后，条件 implementation write set 恰为：

```text
engine/f09/feedback.py
tests/f09/test_feedback_eligibility.py
```

不得修改 [`engine/f09/artifacts.py`](../engine/f09/artifacts.py)、R40、R41、Task 9、P-2、public API、依赖或任何其他文件。Task 3 已冻结的合同、[`engine/f09/json_source.py`](../engine/f09/json_source.py)、[`engine/f09/markdown_source.py`](../engine/f09/markdown_source.py)、[`tests/f09/test_json_source.py`](../tests/f09/test_json_source.py) 与 [`tests/f09/test_markdown_source.py`](../tests/f09/test_markdown_source.py) 明确排除：不得修改、重新审查、重算、复验、作为本 unit 的授权来源，或以 R42 结果外推其状态。

### 5.1 R39 accounting 的唯一窄幅兼容方式

本节是对 [`plans/g6-task8-r39-feedback-adapter-contract.md`](g6-task8-r39-feedback-adapter-contract.md:286) 第 8 节“新增四个 structural tests”及“不得新增第五个 structural node”的唯一窄幅 supersession：仅允许为 R42-F08 添加下述一个 named node，且只改变 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py) 的 aggregate accounting。R39 的四个 named nodes、P01–P94、runtime、legacy coverage、其他 contract 条款与其历史 `16 + 94 = 110` 冻结记录均不被改写。

当前该测试文件已有 18 个 structural nodes（R39 四个加 R42 两个 successful-path nodes 已实际存在）。R42-F08 之后的唯一有效 aggregate accounting 为：

```text
18 existing structural nodes
+ 1 new named R42-F08 structural node:
  test_bind_feedback_operation_manifest_verifier_typed_failure_stops_before_all_downstream_effects
+ 94 existing P01–P94 parameterized falsifier instances
= 113 collected instances
```

未来 implementation/test 必须只把该 named R42-F08 test 添加为 `test_contract_falsifier_ledger` 之外的第 19 个 structural node，并将静态 accounting assertion 精确改为 `12 + 4 + 3 = 19 structural`、`70 + 24 = 94 falsifiers`、`19 + 94 = 113 collected`。P01–P94 的 ID 序列、内容、参数化方式和既有 18 个 structural nodes 必须逐字保留；不得新增第五个 R39 structural category、不得改变 R39 对既有 16-node baseline 的历史冻结，也不得将 F08 偷换进 P01–P94。该窄幅 supersession 只规定 R42 implementation 后该测试模块的 aggregate accounting，不改变 R39 runtime、contract、falsifier 或任何其他文件。

测试未授权、未执行；若后续获得单独 verification authorization，至少必须证明：

1. restricted successful self-excluded-material evaluation 触发 public manifest verifier exactly once；并以 call-count oracle 覆盖 builder、direct records-shape、identity 内嵌 records-shape 与 identity direct revalidator 四个既有 call site；
2. proof/manifest verifier failures分别保持 R40 所要求的零后继处置；
3. 公开 operation 的 R42-F08 只通过 [`bind_feedback_operation()`](../engine/f09/feedback.py:2122) 发起；其唯一回归测试必须命名为 `test_bind_feedback_operation_manifest_verifier_typed_failure_stops_before_all_downstream_effects`，并按第 4.2 节的封闭 observation ledger 分别断言 verifier exactly once、sentinel exception identity 原样抛出，以及 invalid material、key、binding、receipt、eligibility、learning 六类 calls/outputs 各自为零；
4. builder 后每个 restricted helper 仍执行 structural identity/material/outer-ref revalidation；
5. post-verifier mismatch 不触发第二次 verifier；
6. legacy behavior、R39 accounting 与 zero-side-effect boundary 不回归。

## 6. Gate 与唯一下一合法动作

作者 verdict：**`REVISE — R42-F08 已补充 accounting、封闭 observation ledger 与 Task 3 retained protection；等待逻辑新鲜、只读独立 CONTRACT review`**。本文只开立 R42 document-only admission/contract；它不修订 runtime、不改写 R39 evidence freeze、不关闭 R40-R04，亦不授权 Task 9/P-2 implementation 或 tests。

即使 R42 review 后续为 `PASS`，也只关闭 R42 合同 Gate。R40 必须在 R42 独立 contract/implementation/verification Gate 依序闭合且明确授权后重新审查；P-2 与 Task 9-P 持续 `BLOCKED`，Task 9 amendment 持续 `STILL_OPEN`。

**唯一下一合法动作：** 对本次 R42-F08 accounting/ledger/protection correction 执行逻辑新鲜、只读独立合同审查；不得开始 implementation、tests、命令、Git 或其他 unit。

## 7. R42-F08 correction 后的逻辑新鲜、只读独立合同审查

- **Gate：** `CONTRACT / fresh STATIC_REVIEW`。
- **审查角色与输入：** logical fresh Static Reviewer；仅重读本合同、[`plans/g6-task8-r39-feedback-adapter-contract.md`](g6-task8-r39-feedback-adapter-contract.md:286)、[`engine/f09/feedback.py`](../engine/f09/feedback.py:2024) 的 public-operation control flow 及 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py:1761) 的现行 accounting。未采纳作者自评或先前 verdict。
- **范围/副作用核验：** 本轮只读审查前唯一修改是本合同；未修改 runtime/tests，未执行 Python、pytest、Git、远端或 GitHub operation。条件 implementation write set 仍严格为 [`engine/f09/feedback.py`](../engine/f09/feedback.py) 与 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py)。Task 3 排除项在第 5 节明示保留。
- **Accounting 核验：** 现行模块静态 assertion 为 18 structural + 94 parameterized = 112；第 5.1 节明确以唯一 R42-F08 named node 将其变为 `(12 base + 4 R39 + 3 R42) = 19 structural`、94 falsifiers、113 collected，并保留 P01–P94 与既有 18 nodes。该 narrow supersession 直接且不再把 F08 误称为 R39 第五节点。
- **Failure-boundary 核验：** 当时的 [`_compute_operation()`](../engine/f09/feedback.py:2040) 会 catch typed verifier failure 后触及 invalid material/key/binding/receipt path，故这是 implementation 必须修复的真实 Critical gap，不得被 CONTRACT PASS 掩盖。第 4.1–4.2 节已将 future oracle 冻结为 public entrypoint、verifier identity/once，以及 invalid material、key、binding、receipt、eligibility、learning 六类各自封闭 seam 的 zero-call/zero-output ledger；未以“无返回”替代观察。
- **Falsifiers：** 任一实现若包装/吞掉 sentinel、第二次 verifier、进入 legacy fallback，或触及第 4.2 节任何 fail-on-call seam，即违反 R42-F08；任一 accounting 变更若删除/重命名既有 node、改变 P01–P94、加入额外 structural node，或触碰 Task 3 排除项，即本 review 失效并 `REVISE`。
- **Verdict：** **`PASS`**，仅关闭 R42 document-only CONTRACT Gate。它不证明当前 runtime 已修复、不证明测试存在或通过、不构成 STATIC_REVIEW/VERIFY/EVIDENCE_REVIEW/FREEZE PASS，亦不关闭 R40-R04、P-2、Task 9-P 或 Task 9。
- **唯一下一合法动作：** controller 可仅按第 5 节条件 write set 激活 R42 IMPLEMENT Gate，先以唯一 F08 named test 建立 RED；不得启动 R40、R41、Task 9、P-2、Task 3、Git、远端或 GitHub operation。

## 8. R42 implementation 后的逻辑新鲜 STATIC_REVIEW

- **Gate：** `STATIC_REVIEW`。
- **审查角色与独立性：** logical fresh Static Reviewer；在审查前重置作者/实现者结论，仅以本合同第 2–5 节、[`engine/f09/feedback.py`](../engine/f09/feedback.py:213) 的最终实现、[`engine/f09/feedback.py`](../engine/f09/feedback.py:975) 的 verifier call site、[`engine/f09/feedback.py`](../engine/f09/feedback.py:2040) 的 exception boundary、[`engine/f09/feedback.py`](../engine/f09/feedback.py:2142) 的 public entrypoint 与 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py:1761) 的 F08 oracle 为输入。
- **范围审查：** R42 实际修改仅限 [`engine/f09/feedback.py`](../engine/f09/feedback.py) 与 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py)；本 freeze record 仅修改本合同。未修改 artifacts、Task 3 排除文件、R40、R41、Task 9、P-2、public API 或依赖；未执行 Git 或远端/GitHub operation。
- **结构核验：** `_ManifestVerifierFailure` 只由 builder 的唯一 public verifier call 创建，保存原始 typed exception object；仅 operation owner 传入 propagation intent，且仅 `_compute_operation()` 捕获 wrapper 后 `raise failure.error`。因此只有 verifier-originated `F09ContractError` / `F09IntegrityError` 逃逸，其他 preprod material typed failures继续由既有 fallback 生成 invalid operation。
- **F08 核验：** 测试仅经 public binder 调用；以 `caught.value is sentinel` 验证 object identity；verifier log 独立为 exactly once；六类封闭 seams 均为 fail-on-call probes，并分别断言 calls/outputs 为零，eligibility 另断言 inputs 为零。
- **Accounting 核验：** 静态 AST assertion 精确验证 19 个 structural nodes 与 94 个 P01–P94 parameterized falsifiers，合计 113；P01–P94 ID 序列未改变。
- **Falsifiers：** 若 wrapper 由 non-verifier path 创建、catch 按 typed class 广泛重抛、F08 触及任何下游 seam、出现第二次 verifier、P01–P94/既有 nodes 被改变、或 write set 越界，则 verdict 必为 `REVISE`。
- **Verdict：** **`PASS`**。这只证明最终静态结构、write scope、oracle 与 accounting 符合 R42 合同；不证明全仓、R40、R41、Task 3、Task 9、P-2、GitHub 或部署状态。
- **唯一下一合法动作：** 对最终 R42 scope 执行完整 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py) verification，并作 fresh evidence review。

## 9. R42 fresh VERIFY 与 EVIDENCE_REVIEW

- **Gate：** `VERIFY → EVIDENCE_REVIEW`。
- **执行边界：** 仅本地命令 `python -m pytest tests/f09/test_feedback_eligibility.py -q`，working directory 为 `f:/多流派新思路`；该命令不含 Git、远端、GitHub CLI/API 或网络操作。
- **失败历史：** 初次 implementation 后全文件运行得到 `3 failed, 110 passed`：`test_every_nested_dereference_is_guarded`、P55、P57，直接证明初始 boundary repair 过宽并使非-verifier preprod material errors逃逸；该 run 不能作为 behavior PASS evidence。根因定位为 [`_compute_operation()`](../engine/f09/feedback.py:2031) 将全部 preprod material 构造移出原 fallback catch。随后以唯一 wrapper marker 分割 verifier-originated failure 与其余 typed material failure，旧 static review 失效并在 §8 重新审查。
- **最终动态证据：** 在 §8 fresh STATIC_REVIEW 后，上述 exact command exit code 为 0，输出完整、未截断，`113 passed in 15.15s`；无 failed、error、skipped 或 timeout。该动态 collected count 与 §8 的静态 `19 + 94 = 113` 精确一致。
- **Falsifier review：** F08 terminality、P55/P57 fallback、nested dereference guard、successful exactly-once path 与 P01–P94 均由完整模块运行覆盖；无 selector drift、collection error、partial run 或 static/dynamic count mismatch。初次 3-failure run已保留为历史失败而非 PASS 证据。
- **Evidence verdict：** **`PASS`**。当前有效证据为最终完整 run；历史 3-failure run为无效 PASS 证据但保留其边界回归诊断价值。静态/动态 reconciliation：`113 / 113 / difference 0 / YES`。
- **直接证明：** R42 公开 restricted-preprod verifier typed failure 在 F08 覆盖下原样停止且没有六类下游 effect；同一 test module 的既有 non-verifier invalid fallback、restricted successful path、19+94 accounting 与 P01–P94 在该 final source state 下通过。
- **不证明：** 全仓 suite、Task 3、R40、R41、Task 9、P-2、性能、安全、部署、远端同步、PR/merge/publication，或 GitHub 整体未变；仅可确认本受控 session 未执行 GitHub-mutating operation。
- **Freeze eligible：** `YES`。

## 10. R42 evidence-bounded freeze

**Verdict：`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`。**

本冻结仅覆盖 R42-F08 的 restricted-preprod public manifest verifier typed-failure terminality、其最小 exception-boundary partition、以及 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py) 的 113-instance verification evidence。它不重新冻结、修改、复验或外推 Task 3，亦不关闭 R40、R41、Task 9、P-2 或任一全局/远端 Gate。

**唯一下一合法动作：** 依据既有依赖关系对 R40 的残余 call-count/revalidation gap 执行新的只读 admission；不得把 R42 freeze 当作 Task 9 或 G6 总冻结授权。
