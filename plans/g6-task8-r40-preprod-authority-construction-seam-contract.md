# G6 / Task 8 R40 preprod authority public construction seam 合同

- **Unit：** feedback-owner public `PreprodRunAuthority` construction seam（仅合同）
- **Gate：** `CONTRACT — PASS / implementation authorization may be requested separately`
- **现行依赖：** R39 feedback adapter 已冻结；P-2 `BLOCKED`；Task 9-P `BLOCKED`；Task 9 amendment `STILL_OPEN`。
- **实现授权：** 否。本文及任何 review 结论均不授权 production、tests、Python、pytest、Git、远端或 GitHub operation。
- **作者写集：** 仅本文件。

## 1. Admission、目标与所有权

当前 [`PreprodRunAuthority`](../engine/f09/feedback.py:192) 的 `content_digest` 由 feedback owner 私有 [`_preprod_authority_self_excluded_material()`](../engine/f09/feedback.py:1361) 在 feedback binding 内校验；Task 9 无法合法构造具有正确 digest 的非空 authority。R39 已冻结 restricted consumer adapter，但没有 public construction callable。此合同为唯一缺口建立 feedback-owner public seam，且只解决 authority construction，不触及 binding、learning 或 Task 9 implementation。

目标是让已获独立授权的上游 producer 仅通过 P-1 returned [`RunArtifactSetResultV1`](g6-task8-r41-run-target-ref-capture-provisioning-seam-contract.md:77)，取得 immutable [`PreprodRunAuthority`](../engine/f09/feedback.py:192)；digest canonicalization 仍完全由 feedback owner 保有。此 callable 不接收 caller-built authority、caller-built digest、裸 manifest、裸 target-ref tuple、manifest path、root、record、key material、role label 或 private context。

权威约束：[`plans/g6-task8-r39-feedback-adapter-contract.md`](g6-task8-r39-feedback-adapter-contract.md)、[`plans/g6-task9-versioned-producer-envelope-contract.md`](g6-task9-versioned-producer-envelope-contract.md)、[`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1683) 与 [`_preprod_authority_self_excluded_material()`](../engine/f09/feedback.py:1361)。冲突时，owner boundary、public verifier 和 fail-closed 规则优先。

## 2. 精确 public surface

future implementation 只能在 [`engine/f09/feedback.py`](../engine/f09/feedback.py) 定义以下 public callable；它不必由 [`engine/f09/__init__.py`](../engine/f09/__init__.py) re-export，Task 9 future implementation 只能 module-qualified import：

```python
def construct_preprod_run_authority_v1(
    *,
    run_artifact_set_result: RunArtifactSetResultV1,
) -> PreprodRunAuthority: ...
```

1. callable 名称、keyword-only boundary、参数顺序、字段类型与返回类型精确如上；不得接收 `content_digest`、`ArtifactSetManifest`、裸 `target_refs`、`case_id`/`track`/`run_id`、`RunArtifactSetKeyV1`、filesystem root、request、receipt、private context 或 caller capability。
2. callable 必须为同步、纯内存 construction/validation seam：不执行 filesystem、network、clock、environment、subprocess、registry、feedback binding、eligibility 或 learning side effect。
3. `PreprodRunAuthority` dataclass、R39 private helpers、legacy feedback public API、[`RawFeedbackAuthority`](../engine/f09/feedback.py:240) 与 binder signatures 一律不变。
4. 该 seam 只允许 P-1 returned result 内 manifest key 的 `RunTrack.V5_V6_PREPROD`。`STAGED_L6`、production、未知/子类 enum 均 typed fail closed，绝不返回 authority。

## 3. construction、validation 和 digest ownership

1. 首先 exact-type guard：`run_artifact_set_result` 必须 exact [`RunArtifactSetResultV1`](g6-task8-r41-run-target-ref-capture-provisioning-seam-contract.md:77)。失败为 [`F09ContractError`](../engine/f09/errors.py)，零后续调用。随后只从该 result 取得 `manifest` 与 `target_refs`；不得接受或派生替代 carrier material。
2. 随后恰一次调用 P-1 public [`validate_run_artifact_set_result_issuance_v1()`](../engine/f09/artifacts.py)。issuance verifier 的任何 typed failure 原样传播，且 manifest verifier、authority construction、feedback digest、binder 与 learning 调用数均为零。R40 不得读取 registry、public key、私钥、signer port 或 payload bytes，也不得自行验签、重建 proof 或替换 serializer。
3. 仅在第 2 项成功后，**不得由 R40 seam 直接调用** [`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1683)。为保持 R39 private helper 不变且使成功路径的 manifest verification 恰为一次，唯一 owner-owned manifest-verification path 是第 6 项对 [`_preprod_authority_self_excluded_material()`](../engine/f09/feedback.py:1361) 的一次调用；该 helper 经其既有 [`_validated_preprod_restricted_manifest_context()`](../engine/f09/feedback.py:970) 恰一次调用 public manifest verifier。R40 seam 不导入 artifacts underscore symbol，不复制 run key serializer、records digest、manifest digest algorithm 或 issuance payload serializer。
4. manifest verifier 在第 6 项成功返回的 restricted context 内成功后，要求 `manifest.key` exact [`RunArtifactSetKeyV1`](../engine/f09/artifacts.py:88)，且 key 的 `case_id`、`run_id` 为 nonblank exact `str`、`track is RunTrack.V5_V6_PREPROD`；每个 manifest record 的 case/track/run id 必须与该 key 相同。任一 mismatch 为 [`F09IntegrityError`](../engine/f09/errors.py)，不构造 authority。
5. result 的 `target_refs` 必须 exact tuple，且 ordered role closure 必须且只能为 `RUN_SNAPSHOT`、`DECISION_RUN`、`FEEDBACK_ATTACHMENT`、`MANIFEST`；不得重复、缺失、额外或重排。前三项必须按 R41 frozen exact join 逐条匹配 returned manifest 的 verified record identity、schema 与 observed digest。`MANIFEST` 是 outer-ref，不是 record 或 payload：其 `object_id == manifest.manifest_id`，且 exact `DigestPresent` binding digest 等于第 6 项 returned restricted context 的 `verifier_returned_records_digest`；不得使用 `manifest.digest`，不得伪造 manifest schema/contract equality target。
6. 仅在 1–2 通过后，feedback owner 以内存 provisional authority（`content_digest` 使用 exact placeholder `DigestRef("sha256", "RFC8785-JCS-UTF8", "0" * 64)`）调用本模块 [`_preprod_authority_self_excluded_material()`](../engine/f09/feedback.py:1361) **恰一次且仅一次**，并传入 `include_restricted_context=True`。它是本 seam 唯一允许的 manifest-verification owner path：helper 的既有 restricted-context 校验恰一次调用 public manifest verifier；任何 typed failure 原样传播，零 final authority。helper 必须返回 `(material, restricted_context)`；R40 仅从该 returned context 读取 verifier-returned records digest，用于第 4–5 项复核，且不得再次验证 manifest。随后以 [`bounded_jcs_sha256()`](../engine/f09/canonical_json.py:251) 对该唯一 material 计算唯一 `content_digest`，再构造并返回最终 frozen authority。placeholder 不得返回、缓存、记录或暴露给 caller；final authority material 必须与 provisional 的 self-excluded material 相同。
7. callable 不调用 [`bind_feedback_operation()`](../engine/f09/feedback.py:2118)、[`evaluate_learning_eligibility()`](../engine/f09/feedback.py:2292) 或 [`validate_learning_eligibility()`](../engine/f09/feedback.py:2352)。它不是 P-2 admission、feedback readiness 或 learning eligibility 的证明。

## 4. Producer / consumer 边界

- Task 9 可在其**另行获得 implementation authorization**后调用本 seam，但只能传递 future P-1 [`coordinate_run_artifact_set_with_target_refs_v1()`](g6-task8-r41-run-target-ref-capture-provisioning-seam-contract.md:84) actual returned `RunArtifactSetResultV1`；不能构造 digest、authority、manifest、run id、target refs、proof 或 result 的替代物。R40 不接收裸 `target_refs`，不得把 result carrier 误解为允许 Task 9 自行拼装其 fields。
- R40 不实现 [`engine/f09/application.py`](../engine/f09/application.py)、[`engine/f09/artifacts.py`](../engine/f09/artifacts.py)、P-2 路径或任何 Task 9 tests；P-1 仍拥有 lifecycle/verifier，R39 仍拥有 consumer adapter。
- P-2 只能消费 future Task 9 public envelope 的 returned authority；不得调用该 seam，也不得变为 producer / issuer / signer。
- 非空 authority 的可构造性不等于可 binding、可 learning、可运行 Task 9 或 P-2 admission PASS；所有后续 Gate 保持独立。

## 5. 负向 ledger、write set 与 future verification

| ID | 原子负向条件 | 必须结果 |
|---|---|---|
| R40-F01 | 非 exact result carrier、非法/空 key material，或 caller 提供 `content_digest`/裸 manifest/裸 refs/private context | `F09ContractError`；零 issuance verifier / manifest verifier / authority / side effect。 |
| R40-F02 | P-1 issuance verifier 失败（包括 unknown/revoked key、signature/payload failure） | typed fail closed；零 manifest verifier / authority。 |
| R40-F07 | owner-owned manifest-verification path 中的 P-1 manifest verifier 失败、legacy manifest/key、或 key/record/case/track/run mismatch | typed fail closed；零 final authority；成功路径的 manifest verifier 调用数恰为一。 |
| R40-F03 | refs 缺 role、重复、错序、extra role、record mismatch，或 `MANIFEST` 用 `manifest.digest` / 被视为 record | typed integrity failure；零 authority。 |
| R40-F04 | `STAGED_L6`、production 或 cross-run swap/relabel | typed fail closed；零 authority / binder / learning。 |
| R40-F05 | 复制 artifacts serializer/digest、调用 artifacts private symbol、或由 Task 9/P-2 计算 feedback digest | 合同违反；STOP。 |
| R40-F06 | seam 直接触发 I/O、直接读取 registry 或 key material、binding、eligibility 或 learning | 合同违反；调用数均为零。P-1 issuance verifier 的内部 pure-memory registry read 不属于 R40 direct registry access。 |

若后续总控单独授权 implementation，条件 write set 恰为：

```text
engine/f09/feedback.py
tests/f09/test_feedback_eligibility.py
```

未来测试（未授权、未执行）至少覆盖 exact signature；exact result-carrier guard；issuance verifier 在 owner-owned manifest-verification path 前恰一次调用；issuance failure（unknown/revoked key、signature/payload failure）时零 manifest verifier/authority；V5/V6 success；仅由 `_preprod_authority_self_excluded_material(..., include_restricted_context=True)` 触发的 manifest verifier exactly once；digest round trip；all carrier/key/record/ref/outer-ref falsifiers；`STAGED_L6`/production rejection；zero direct I/O/registry/binding/learning；无 artifacts private import / serializer copy；以及 R39 legacy regression。需要变更这两个路径外任何文件时必须 STOP 并另开合同。

## 6. Gate 与唯一下一合法动作

作者 verdict：**`REVISE — ready for fresh independent read-only contract review after owner-owned manifest-verification-path repair`**。本文只形成 R40 document-only admission/contract；不构成 R40 implementation、R39 再冻结、Task 9/P-2 implementation 或任何 test authorization。

即使独立 review 结论为 `PASS`，也只关闭 R40 contract review Gate；Task 9 versioned contract 仍须独立复审，P-2 与 Task 9-P 保持 `BLOCKED`，Task 9 amendment 保持 `STILL_OPEN`，直至所有独立 Gate 和精确实施授权完成。

**唯一下一合法动作：** 对本次 owner-owned manifest-verification-path 修订执行逻辑新鲜、只读独立合同审查；不得开始 implementation、tests 或其他 unit。

## 7. 逻辑新鲜、只读独立合同审查

- **Gate：** `CONTRACT / fresh STATIC_REVIEW`
- **审查角色：** logical fresh Static Reviewer；未采纳作者自评。
- **授权边界：** 只读复核本文、R39 合同与现有 feedback runtime；未执行命令、Python、pytest、Git、远端或 GitHub operation。
- **直接证据：** R40 public surface 把 `target_refs` 作为 caller input（第 2 节）；R40 第 4 节又禁止 Task 9 构造 target-ref 替代物。现有 R39 runtime 的 [`_validated_preprod_restricted_manifest_context()`](../engine/f09/feedback.py:970) 要求严格、固定的四项 role closure：`RUN_SNAPSHOT`、`DECISION_RUN`、`FEEDBACK_ATTACHMENT`、`MANIFEST`（[`engine/f09/feedback.py`](../engine/f09/feedback.py:995)）。该 runtime 仅以 record identity/schema/observed digest 复核前三项，却仍消费 caller-supplied [`VersionedObjectRef`](../engine/f09/contracts.py) 的其他 material；P-1 manifest record 并未被此证据证明可独立派生完整 ref material。
- **审查发现 R40-R01（阻断）：** 第 3 节将 `FEEDBACK_ATTACHMENT` 规定为“可选”，与既冻结 R39 consumer 的固定四项 closure 不兼容。若 R40 返回三项 ref authority，R39 必然 fail closed，故该 public constructor 不能被视为可实现的 consumer-compatible seam。
- **审查发现 R40-R02（阻断）：** 第 2/3 节要求 caller 提供完整 `target_refs`，第 4 节却禁止唯一预期 caller Task 9 构造这些 refs 的替代物；同时合同没有指定一个已冻结、public、owner-owned 的 ref capture/provisioning source。将该空缺留给 implementation 会把 authority material/role provenance 悄然回流给 producer，或迫使实现猜测 manifest 未承诺的 ref fields，违反 R40 的 P-1 provenance 与 fail-closed 目标。
- **非阻断观察：** provisional zero digest 仅供 self-excluded material 计算，且 R39 的 material 路径不以其 digest value 形成 preimage；在“绝不返回、缓存或暴露 placeholder”的现有边界内，尚未发现该项自身的合同矛盾。它不构成已实施或已验证的行为证据。
- **Falsifier：** 任一修订若仍允许三项 refs、让 Task 9 任意构造/重标 ref、或声称仅由 manifest records 可派生完整 `VersionedObjectRef` 而无独立字段级事实源，则审查必须继续 `REVISE`。
- **Verdict：** **`REVISE`**。R40 不可进入 implementation authorization；所有 inactive successor assumptions 失效。P-2 与 Task 9-P 继续 `BLOCKED`，Task 9 amendment 继续 `STILL_OPEN`。
- **最小修订要求：** 将 role closure 与 R39 固定为四项，并将 `target_refs` 的来源收紧为一个明示、可验证且尚须独立 admission 的 public ref-capture/provisioning seam；若该 source 尚不存在，R40 必须明确 fail closed，而不得把构造责任赋予 Task 9。

### 7.1 Review 后的受控修订与残余 Gate

- 本修订已将 `FEEDBACK_ATTACHMENT` 改为 required，并声明 `target_refs` 只能是 future P-1 public capture/provisioning seam 的 actual returned value；R40 seam 不可依据裸 tuple 判断其 producer provenance，故不将该文字修订误判为 R40 `PASS`。
- **残余缺口：** 当前 P-1 public surface 只证明 [`ArtifactSetManifest`](../engine/f09/artifacts.py:545) 与 [`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1683)；其中 manifest records 不承诺完整 [`VersionedObjectRef`](../engine/f09/contracts.py) 的 `contract_version`、`source_locator_id`、`captured_at` 等 material。R40 不能臆造这些字段，也不得从 projection bytes / filesystem / private serializer 推导。
- **当前 Gate：** **`REVISE`**。R40 implementation authorization 不存在；任何非空 authority 分支仍 fail closed。R39 冻结不变；P-2 与 Task 9-P 保持 `BLOCKED`，Task 9 amendment 保持 `STILL_OPEN`。
- **唯一下一合法动作：** 为 P-1 owner 开立独立、document-only 的 run target-ref capture/provisioning seam admission/contract（R41）；该 unit 必须先裁决完整 ref material 的唯一权威来源、public carrier、returned-manifest identity binding、write set 与零 I/O 边界，之后才可重新 fresh-review R40。

## 8. R41 returned-carrier integration 后的逻辑新鲜、只读独立合同审查

- **Gate：** `CONTRACT / fresh STATIC_REVIEW`
- **审查角色：** logical fresh Static Reviewer；仅以当前 R40 surface、R41 frozen public DTO/return contract、R39 consumer facts 与 feedback owner boundary 审查；不采纳本文作者自评或第 7 节历史结论。
- **授权与副作用边界：** 仅本地只读；未执行命令、Python、pytest、Git、远端或 GitHub operation，未修改 runtime/tests。
- **直接证据：** R41 已定义 frozen public [`RunArtifactSetResultV1`](g6-task8-r41-run-target-ref-capture-provisioning-seam-contract.md:57)，其正常路径携带 coordinator 的 actual returned manifest 和 P-1 built four-role refs；R40 因而不再接受裸 manifest/refs，R39 所需 role closure、record joins 与 MANIFEST verifier digest 均有 frozen upstream contract。R40 当前却只对 result 作 exact-class guard（第 3 节第 1 项）。公开 frozen dataclass 可以由任意 caller 以合法-looking `manifest` 和 `target_refs` 实例化；`type(result) is RunArtifactSetResultV1` 不能证明它来自 R41 callable 的 actual return，而 R40 也不得调用 P-1 private state、filesystem 或重新运行 lifecycle 以证明来源。
- **审查发现 R40-R03（阻断）：** “仅消费 actual returned `RunArtifactSetResultV1`”是本 unit 的 provenance invariant，但当前 public carrier 没有可验证的 issuance/provenance witness，R40 的 exact-class validation 不能区分 R41 actual returned result 与 Task 9/caller 自行拼装的 result。将这项判断留给 implementation 会要么违反 Task 9 non-construction boundary，要么需要未冻结的 P-1 proof/capability model；R40 因此尚未达到唯一、可实施的 CONTRACT Gate。
- **Falsifier：** 若 P-1 public contract 提供 R40 可纯内存、无私有导入地验证的 actual-return provenance witness，且 R40 在 verifier 前精确验证该 witness；或该 result 被设计为 caller 无法直接构造而仍保持 P-1 public consume path，则该发现消失。仅以 exact dataclass、manifest/ref semantic validity 或 caller discipline 不能证伪此缺口。
- **Verdict：** **`REVISE`**。R41 解决 complete ref material 与 manifest binding contract，但未让 R40 证明 carrier issuer provenance。R40 implementation authorization 不存在；P-2 与 Task 9-P 保持 `BLOCKED`，Task 9 amendment 保持 `STILL_OPEN`。
- **唯一最小后续：** 为 P-1/R41 保留一个 public provenance-proof/capability design decision：R40 如何在不访问 private state、filesystem 或重跑 lifecycle 的前提下，区分 actual returned `RunArtifactSetResultV1` 与 caller-built substitute。该决定属于 public API/security boundary，不能由 R40 implementation 自行选择；在此之前不得修改 runtime/tests。

## 9. Owner-owned manifest-verification path 修订后的逻辑新鲜、只读独立合同审查

- **Gate：** `CONTRACT / fresh STATIC_REVIEW`
- **审查角色：** logical fresh Static Reviewer；仅复核本次 R40 修订、R41 issuance verifier 合同，以及 R39 feedback-owner runtime 的既有 helper call graph；未采纳作者自评或既往 review 结论。
- **授权与副作用边界：** 仅本地只读；未编辑 runtime/tests，未执行命令、Python、pytest、Git、远端或 GitHub operation。本文 review 结论不授予任何 implementation authorization。
- **通过证据：** 第 3 节第 1–2 项将 exact `RunArtifactSetResultV1` guard 置于 issuance verifier 前，并冻结 issuance failure 时零 manifest verifier / 零 authority；R40 也未直接访问 registry、payload、public/private key 或 signer。四角色 closure、MANIFEST outer-ref 与 feedback-owner digest boundary 均仍被要求保持。
- **审查发现 R40-R04（阻断）：** 第 3 节第 6 项虽将 manifest-verification owner 收束为仅一次 `_preprod_authority_self_excluded_material(..., include_restricted_context=True)` 调用，但该 frozen helper 的现有成功 call graph 并非一次 verifier：它先在 `_validated_preprod_restricted_manifest_context()` 内调用 `validate_run_artifact_manifest_v1()`，随后 `_manifest_records_shape(..., restricted_context=...)` 经 `_revalidate_preprod_restricted_manifest_context()` 再次调用，最后 `_manifest_identity(..., restricted_context=...)` 触发的 `_manifest_records_shape()` 再次 revalidate。因此单次 helper 调用实际会触发三次 manifest verifier，不能满足本合同的 exactly-once invariant；而第 2 节第 3 项又冻结 R39 private helpers 不变，R40 无法在其 write set 内消除此矛盾。
- **Falsifier：** 若 R39 owner 先以独立、document-only amendment 冻结一个不破坏 digest ownership 与 fail-closed revalidation 的 single-manifest-verifier mechanism、精确 helper surface 和 write set，且 R40 随后只消费该已冻结 owner contract，则 R40-R04 消失。仅把计数要求写入 R40、仅减少 R40 helper 调用次数，或在 implementation 中临时改 private helper 均不足以证伪。
- **Verdict：** **`REVISE`**。R40 contract review Gate 未关闭；不得授权 R40 implementation、tests、Task 9/P-2 或 runtime 修改。P-2 与 Task 9-P 保持 `BLOCKED`，Task 9 amendment 保持 `STILL_OPEN`。
- **唯一下一合法动作：** 仅开立 R39 feedback-owner private-helper revalidation/call-count amendment 的 document-only admission/contract，先裁决 single manifest-verifier mechanism 与精确 write set；不得修改 runtime、tests、R40/R41 以外 unit，亦不得执行命令、测试或 Git。

## 10. R42 有界冻结后的逻辑新鲜、只读独立合同审查

- **Gate：** `CONTRACT / fresh STATIC_REVIEW`。
- **审查角色与输入：** logical fresh Static Reviewer；仅审查本合同第 2--6 节、R42 frozen runtime/helper facts、R41 issuance-proof contract 及 R39 consumer boundary；不采纳作者自评或第 7--9 节历史 verdict。
- **授权与副作用边界：** 仅本地只读。未编辑 runtime/tests，未执行命令、Python、pytest、Git、远端或 GitHub operation；本节仅记录该 review，未授予 implementation authorization。
- **直接证据与判定：**
  1. R42 已将 [`_validated_preprod_restricted_manifest_context()`](../engine/f09/feedback.py:975) 固定为唯一 public manifest-verifier owner；其一次 [`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1683) 成功后，仅创建 operation-local context。
  2. R42 的 [`_revalidate_preprod_restricted_manifest_context()`](../engine/f09/feedback.py:1038) 仅重验 exact authority/manifest identity、key、case/run/track、roles、record joins 与 MANIFEST outer-ref；该路径没有 verifier call。因此 R40-R04 所述单次 owner helper 的多次 verifier call graph 已消失，R40 第 3 节第 3、6 项的 exactly-once invariant 具有已冻结 owner-side contract/runtime evidence。
  3. R41 已冻结 [`RunArtifactSetResultV1`](g6-task8-r41-run-target-ref-capture-provisioning-seam-contract.md:77) 和 [`validate_run_artifact_set_result_issuance_v1()`](g6-task8-r41-run-target-ref-capture-provisioning-seam-contract.md:105) 的 public value-verifiable issuance-proof boundary。R40 第 3 节第 1--2 项先 exact-guard result、后调用该 verifier，并为其 typed failure 冻结零 manifest verifier / 零 authority；随后只从 verified carrier 消费 manifest 与四角色 refs，未重新引入 caller-built substitute。
  4. R40 仍将 feedback-owned authority digest 限定为一次 [`_preprod_authority_self_excluded_material()`](../engine/f09/feedback.py:1373) 返回 material 的 [`bounded_jcs_sha256()`](../engine/f09/canonical_json.py:251) 计算；R40 不读取 registry、key、payload bytes、filesystem 或 artifacts private symbol，且不进入 binder、eligibility 或 learning。R39 fixed four-role closure、MANIFEST outer-ref 与 legacy boundary保持不变。
- **Falsifiers：** 若 owner helper 再次从 revalidation 调用 manifest verifier；若 R40 在 issuance verifier 前接触 manifest verifier；若 issuance failure 可构造 authority；若 result 退回为 caller-built 裸 refs/manifest；若 R40 复制 P-1 serializer、读取 registry/key/private state，或扩大 conditional write set，则本 verdict 必为 `REVISE`。
- **Verdict：** **`PASS`**。R40 合同现为唯一、完整、可证伪，且可在单独、精确的 implementation authorization 下实施。R40-R04 已关闭。
- **直接证据边界：** 本 PASS 只关闭 R40 document-only CONTRACT Gate；不证明 R40/R41 runtime、tests、crypto behavior、Task 9、P-2、Task 9-P、全仓正确性、部署、远端同步或 GitHub 状态。
- **唯一下一合法动作：** controller 可为 R40 请求或激活一份独立的 IMPLEMENT authorization，且范围只能是第 5 节条件 write set [`engine/f09/feedback.py`](../engine/f09/feedback.py) 与 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py)；在该授权前不得修改 runtime/tests、运行命令、执行 Git、远端或 GitHub operation。

## 11. R40 fresh VERIFY、EVIDENCE_REVIEW 与证据有界冻结

- **Gate chain：** `CONTRACT PASS → authorized IMPLEMENT → fresh STATIC_REVIEW PASS → fresh VERIFY PASS → fresh EVIDENCE_REVIEW PASS → PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`。
- **授权与副作用边界：** 本轮只修改第 5 节冻结 write set 中的 [`engine/f09/feedback.py`](../engine/f09/feedback.py) 与 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py)，以及在 EVIDENCE_REVIEW PASS 后追加本 durable freeze ledger。所有验证均在仓库根目录执行本地 `pytest`；命令不含 Git、网络或 GitHub mutation。本 controlled session 未执行 GitHub-mutating operation，但不得据此推断 GitHub 服务端整体状态。
- **实现边界：** [`construct_preprod_run_authority_v1()`](../engine/f09/feedback.py:1430) 先 exact-guard returned carrier，再恰一次验证 issuance；仅在成功后构造 provisional frozen authority，恰一次调用 owner material helper并显式消费 returned restricted-context records digest，最后以唯一 self-excluded material 计算并返回 final digest。constructor 不直接进入 manifest verifier、binder、eligibility 或 learning。
- **失败历史：** 新增 restricted-context digest-consumption oracle 后，exact RED 为 `1 failed, 1 passed, exit 1`；runtime 最小修复后相同 selectors 为 `2 passed, exit 0`。随后测试 oracle 加固使该 GREEN 成为 stale evidence；旧 STATIC_REVIEW 同时失效。加固后先取得 fresh independent STATIC_REVIEW `PASS`，才运行以下 fresh VERIFY。旧会话中的 R40/Task 9 测试与 freeze 仅作恢复线索，未用于本冻结。
- **Fresh VERIFY ledger（working directory 均为仓库根目录）：**
  1. exact R40 focused selectors：`7 collected / 7 passed / 0 failed / 0 errors / exit 0 / 1.39s`；
  2. 完整 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py)：`117 collected / 117 passed / 0 failed / 0 errors / exit 0 / 16.30s`；
  3. 完整 [`tests/f09`](../tests/f09)：`1017 collected / 1017 passed / 0 failed / 0 errors / exit 0 / 49.33s`。
- **静态/动态 reconciliation：** [`test_static_accounting_is_exactly_23_plus_94()`](../tests/f09/test_feedback_eligibility.py:1985) 机械计数 `23` 个 structural tests 与连续 `P01`--`P94` 的 `94` 个 parameterized falsifiers，静态总数 `117`；完整 feedback module 动态 collection 为 `117`，差额 `0`，`Reconciled: YES`。
- **Fresh EVIDENCE_REVIEW：** 独立只读 reviewer verdict 为 **`PASS`**；审查保留完整 RED/stale/GREEN 历史，确认三层命令输出完整、exit code 已知、selector 与范围匹配，且 `23 + 94 = 117` 与动态 collection 精确闭合。`Freeze eligible: YES`。
- **直接证明：** 当前 R40 construction seam 在冻结合同范围内通过 exact focused behavior、完整 feedback module 与完整 F09 regression；issuance-first、owner manifest verifier exactly-once、returned restricted-context digest reconciliation、zero downstream binder/learning、public-only boundary 与 fail-closed falsifiers处于当前证据覆盖内。
- **不得推断：** 本冻结不证明 Task 9、Task 9-P、P-2 或 G6 完成；不证明 repository-wide full suite、部署、发布、生产就绪、Git/GitHub 状态或远端同步；不授权后续 unit 跳过其独立 Gate。
- **Freeze verdict：** **`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`**。R40 unit 在上述源码、合同和证据边界内 durable frozen。
- **唯一下一合法动作：** 重建 Task 9 的 fresh CONTRACT review；在该 Gate PASS 前不得把 R40 freeze 外推为 Task 9 implementation/verification evidence，也不得进入 P-2 ADMISSION。
