# G6 / Task 8 P-1：公开 verified run-manifest fixture/provisioning seam 合同

**状态：PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE。P-1 public fixture/provisioning seam 已在本合同的精确本地证据范围内冻结；R39 继续 `BLOCKED`，未获得 implementation、verification 或 freeze 授权。未执行 Git、远端或 GitHub-mutating operation；不据此推断工作区清洁、全仓库通过或 GitHub 状态。**

## 1. Gate 身份与唯一目标

本 Gate 是 [`G6 / Task 8 R39 feedback adapter 合同`](g6-task8-r39-feedback-adapter-contract.md:23) 第 1.1.1 节要求的 P-1 独立前置 Gate。唯一目标是在 P-1 artifact owner 内提供一个可由跨 owner 测试导入的、确定性的、无副作用的 public fixture/provisioning callable；它返回一个已经通过 P-1 public verifier 的 exact [`ArtifactSetManifest`](../engine/f09/artifacts.py:546)，使 feedback 测试不必构造或理解 [`RunArtifactSetKeyV1.canonical_key_digest`](../engine/f09/artifacts.py:88)。

本 Gate 的通过不等于 R39 已解除阻断，也不等于 R39 或任何 Task 9/P-2 Gate 获得 implementation 授权。

## 2. Admission 裁决

### 2.1 观察事实

1. P-1 已有 public verifier [`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1582)。该 verifier 只接受 exact manifest/key，并在内部重验 run key、role closure、attempt graph、record graph、state 与 records digest。
2. 已有 P-1 public coordinator [`coordinate_run_artifact_set_v1()`](../engine/f09/artifacts.py:1644) 需要已经合法的 [`RunArtifactSetRequestV1`](../engine/f09/artifacts.py:103)；其 request 又要求预先具有正确的 run key digest，不能解除 fixture 构造的闭环。
3. 有效 run key 目前只能由 P-1 owner 的私有 helpers [`_digest_run_input_snapshot_refs_v1()`](../engine/f09/artifacts.py:622) 与 [`_digest_run_artifact_set_key_v1()`](../engine/f09/artifacts.py:646) 构造；现有 lifecycle 正例也正使用这些 owner-private helpers，见 [`test_coordinate_run_artifact_set_writes_and_public_verifier_rebuilds_graph()`](../tests/f09/test_artifact_lifecycle.py:2784)。
4. R39 明确禁止 feedback owner 直接导入上述私有 helpers、复制 serializer/canonicalizer/digest preimage，或以 monkeypatch、fake verifier、lifecycle private fixture 取代真实 evidence，见 [`R39 fixture/provisioning 前置条件`](g6-task8-r39-feedback-adapter-contract.md:23)。
5. 当前 P-1 public function allowlist 不含 provisioning callable，见 [`test_artifact_authority_projection_roles_roots_payloads_and_public_surface_are_exact()`](../tests/f09/test_artifact_lifecycle.py:1389)。

### 2.2 结论

**Admission verdict：PASS（仅允许进入本 seam 的独立 CONTRACT review）。**

缺口真实、consumer 明确、owner 唯一，且最小解法是 P-1 提供固定的 pure fixture/provisioning callable。它不写入 artifact root、不读取既有 artifact、不接受 caller key/request/manifest，故不会扩大 lifecycle、filesystem、retry 或 run identity authority。

## 3. 冻结 public surface

未来仅允许新增下列一个 module-level public callable：

```python
def provision_verified_run_manifest_fixture_v1() -> ArtifactSetManifest: ...
```

该 callable 必须定义于 [`engine/f09/artifacts.py`](../engine/f09/artifacts.py)，并由 [`tests/f09/test_artifact_lifecycle.py`](../tests/f09/test_artifact_lifecycle.py) 作为唯一 owner test 文件验证。

### 3.1 精确语义

1. 不接受位置参数、keyword-only 参数、`*args`、`**kwargs`、request、root、clock、attempt ID、manifest、key、payload 或 callback。
2. 每次调用返回一个 fresh exact [`ArtifactSetManifest`](../engine/f09/artifacts.py:546)；返回对象及其 key、records、attempts、refs 均不得复用上一次调用的对象 identity。
3. 返回 manifest 必须能够由 [`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1582) 无异常接受，且 verifier 返回值必须与 `manifest.digest` 相等。
4. 返回 carrier 必须使用 exact [`RunArtifactSetKeyV1`](../engine/f09/artifacts.py:88)，并固定 `operation == "PROJECT_RUN_ARTIFACT_SET"`。
5. fixture 的 track 固定为 `RunTrack.V5_V6_PREPROD`；case ID、run ID、schema strings、source/contract/schema digests、input refs 与 projection payloads 均为 P-1-owned deterministic constants。它们不得来自环境、当前目录、文件、网络、时钟、随机源或 caller input。
6. **fixture 返回的 graph** 的 key roles 必须恰为 `("RUN_SNAPSHOT", "DECISION_RUN", "FEEDBACK_ATTACHMENT")`，records 顺序必须与 key roles 相同；无 `MANIFEST` record、statement role、legacy key 或 optional two-role closure。此约束不得被扩大为变更既有 [`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1683) 的 V1 lifecycle compatibility：该 public verifier 仍可按既有 P-1 contract 接受其合法的 two-role graph。seam 的证据要求是固定 fixture 本身和其在保持完整 key digest 的情况下删除、重排或替换任一 fixture role 时被 verifier fail-closed，而不是以此 seam 改写 generic verifier 的既有可接受 role domain。
7. 每个 record 必须是 exact [`ArtifactRecord`](../engine/f09/artifacts.py:520)，同一 case/track/run identity，`statement_set_id is None`，state 为 `VERIFIED`，expected/observed digest 相等，且包含一个 exact succeeded [`ArtifactWriteAttempt`](../engine/f09/artifacts.py:504)。attempt refs 与 key refs graph digest 必须一致。
8. fixture 只构造 in-memory graph；不得调用 [`coordinate_run_artifact_set_v1()`](../engine/f09/artifacts.py:1644)、[`inspect_run_artifact_set_v1()`](../engine/f09/artifacts.py:1629)、[`reconcile_run_artifact_set_v1()`](../engine/f09/artifacts.py:1883)、writer 或任何 filesystem API。

### 3.2 owner-local implementation boundary 与 consumer boundary

为构造本 callable 返回的 verifier-accepted graph，**只允许** [`engine/f09/artifacts.py`](../engine/f09/artifacts.py) 内该 callable 本体及其 P-1-owner-local module-private helper 调用既有 [`_digest_run_input_snapshot_refs_v1()`](../engine/f09/artifacts.py:622)、[`_digest_run_artifact_set_key_v1()`](../engine/f09/artifacts.py:646) 与 [`_digest_run_artifact_set_key_v1_from_key()`](../engine/f09/artifacts.py:692)。该 allowlist 只允许 owner-local canonical construction/verification；这些 symbols 不得新增 export、wrapper、alias、return field、callback、parameter 或其他跨 owner 可调用入口。

R39 feedback tests 只可从该 public callable 获取正例 manifest，并只可通过 public [`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1582) 验证它。它们可以以 immutable dataclass replacement 制造单项反例，但不得导入、调用、复制、间接暴露或要求 P-1 private helper，不得构造新的 accepted run key、复制 P-1 canonical preimage，或 monkeypatch verifier 当作 acceptance evidence。

本 seam 不签发 [`PreprodRunAuthority`](../engine/f09/feedback.py:192)，不构造 target refs，不代表 current execution，不改变 feedback canonical material，也不授权 feedback binding、learning 或 Task 9/P-2。

## 4. 非目标与保护边界

以下均禁止：

- 修改 [`engine/f09/feedback.py`](../engine/f09/feedback.py) 或 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py)；R39 继续 `BLOCKED`。
- 修改 [`engine/f09/contracts.py`](../engine/f09/contracts.py)、[`engine/f09/application.py`](../engine/f09/application.py)、exports、Task 9/P-2 文件或任何其他 production/test 文件。
- 改变 existing public callable 的签名、legacy artifact bytes/digest、`IdempotencyKey` literal domain，或 run lifecycle/verifier semantics。
- 新增 generic key builder、generic manifest builder、caller-defined fixture inputs、mutable registry、environment switch 或 fixture-specific privilege flag。
- 使用 I/O、subprocess、network、clock、randomness、global mutable cache、writer、reconcile、feedback binder、eligibility evaluator 或 learning validator。
- 将 fixture 视为 production run、artifact persistence proof、current-execution authority 或 R39 acceptance evidence 的替代品。

## 5. Conditional implementation write whitelist

只有在本合同获得 fresh independent CONTRACT `PASS` 且 controller 明确激活独立 implementation Gate 后，允许修改的路径恰为：

```text
engine/f09/artifacts.py
tests/f09/test_artifact_lifecycle.py
```

合同阶段唯一允许写入的路径是本文件。任何第三路径、重命名、删除、依赖安装、Python/pytest、Git、远端或 GitHub operation 均为 STOP。

## 6. Static 与动态验证合同

未来 P-1 owner tests 必须至少证明：

1. callable 的 name、module、zero-argument signature、return annotation 与 public callable allowlist 精确；allowlist 仅在既有集合基础上新增该一个 name。
2. 两次调用均返回 fresh exact manifest/key/record/attempt/ref graph，不共享 mutable backing mapping，并且均由 public verifier 成功验证。
3. fixture 固定为 V5/V6 preprod、run operation、精确三角色顺序、单 succeeded attempt、正确 refs graph 与 complete-verified manifest；不得出现 legacy key、statement role 或 `MANIFEST` record。
4. 对每项单点 mutation（key operation、canonical key digest、case/track/run identity、**fixture 的** role closure/order、record digest/state、attempt refs graph、manifest digest/state）均由 public verifier typed fail closed。role-closure falsifier 必须保持原 key 的 canonical digest，以证明删除、重排或替换 fixture role 的不一致 graph 被拒绝；它不要求、也不得借此改变既有合法 two-role V1 lifecycle graph 的 public verifier compatibility。
5. AST/static gate 证明 fixture callable 与其 P-1 helper call graph 不出现 filesystem/ambient authority、writer/coordinator/inspection/reconcile、feedback/learning call、任何跨-owner private import，且 production source 中没有 generic/caller-provided builder escape hatch；同时精确允许且只允许第 3.2 节列出的三个 artifacts owner-local private canonical helpers，不得增加 wrapper、alias 或任何可被 consumer 调用的 private seam。
6. legacy artifact lifecycle 的 existing canonical bytes/digest regression 与现有 run lifecycle tests 保持通过；新增 seam 不改变其 observed behavior。
7. feedback test file 对 P-1 private symbol 的 import/use 仍为零；该项为 future R39 reopening 的前置 static evidence，不在本 seam Gate 通过前修改 R39 文件。

未来执行 selectors（当前禁止运行）为：

```text
python -m pytest tests/f09/test_artifact_lifecycle.py --collect-only -q
python -m pytest tests/f09/test_artifact_lifecycle.py -q
python -m py_compile engine/f09/artifacts.py tests/f09/test_artifact_lifecycle.py
```

`--collect-only` 输出是本 unit 的 static/dynamic reconciliation evidence：其 collection total 必须与随后完整 pytest selector 的 passed total 一致。它只审计本 owner test module 的收集面，不扩大为全仓库、R39 或系统级验证。

## 7. Falsifiers 与 STOP

以下任一项为 `REVISE` 或 `BLOCKED`，不得实现或 freeze：

- 需要 caller 构造 run key、传入 payload、root、clock、manifest 或 request；
- 返回结果未被 public verifier接纳，或靠 monkeypatch/fake verifier 接纳；
- fixture 写入、读取、reconcile 或依赖现有 filesystem state；
- fixture 在第 3.2 节 allowlist 外复用 P-1 private helper，或以 export、wrapper、alias、return field、callback、parameter、跨-owner import/call 或其他方式向 feedback consumer 暴露 P-1 private helper；
- 有效 fixture 不是固定的 three-role V5/V6 preprod graph，或以本 seam 为由改变既有合法 two-role V1 lifecycle graph 的 verifier compatibility；
- 修改 whitelist 外路径，或 public callable allowlist 出现额外 name；
- legacy bytes/digest、run lifecycle/verifier 或 R39 files 发生改动；
- 任何行为被表述为 current-run authority、feedback readiness、binding/learning entitlement，或 GitHub service-side mutation。

## 8. Freeze 与 R39 reopening 条件

P-1 seam 仅当以下证据全部完成时才可 `FREEZE`：独立 implementation Gate 授权、whitelist 内实现、全部 P-1 static/dynamic selectors 通过、fresh independent evidence review 为 `PASS`、并在本文件记录 evidence-bounded freeze。

只有在该 freeze 后，controller 才可将 R39 从 [`BLOCKED`](g6-task8-r39-feedback-adapter-contract.md:331) 重新送入独立 implementation authorization 判断。P-1 seam 的 CONTRACT `PASS`、实现完成或单次 verifier 成功均不自动重开 R39。

## 9. Evidence-bounded freeze 记录

```text
Unit: G6 / Task 8 P-1 public verified run-manifest fixture/provisioning seam
Current stage: FREEZE
Current verdict: PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE

Fresh gate evidence:
- CONTRACT: collection-reconciliation 最小修订获 fresh independent PASS。
- IMPLEMENT: 仅在合同 whitelist 内完成；未修改 R39 files。
- STATIC_REVIEW: fresh independent PASS；确认固定 three-role fixture、owner-local private-helper boundary、无 ambient/lifecycle/feedback escape hatch，并保持既有合法 two-role V1 lifecycle verifier compatibility。
- VERIFY: `python -m pytest tests/f09/test_artifact_lifecycle.py --collect-only -q` = 169 collected；`python -m pytest tests/f09/test_artifact_lifecycle.py -q` = 169 passed；`python -m py_compile engine/f09/artifacts.py tests/f09/test_artifact_lifecycle.py` exit 0。
- Reconciliation: 169 collected = 169 passed。
- EVIDENCE_REVIEW: fresh independent PASS，允许 evidence-bounded FREEZE。

Failure history retained:
- 此前同一 lifecycle selector 曾为 2 failed / 167 passed；该失败证据未用于本 freeze。其后以最小修复处理 typed fail-closed assertion 与 reachable private-helper allowlist，并完成 fresh static review 和上述完整重跑。

Directly proven:
- 本 seam 的 public fixture 在本合同所列 static/dynamic evidence 范围内满足固定 V5/V6 preprod three-role verifier-accepted in-memory graph 及 fail-closed 边界。
- 本控制会话未执行 Git、远端或 GitHub-mutating operation。

Not proven / do not infer:
- 不证明工作区清洁、全仓库或系统级正确性、持久 artifact、current-run authority、feedback binding/learning entitlement、R39 readiness，或任何 GitHub 状态与同步。

Protected unit: R39 feedback adapter remains BLOCKED；本 freeze 只满足 controller 后续独立 admission/implementation authorization 判断的前置条件，绝不自动重开或授权 R39。
Forbidden at freeze boundary: 修改 R39 files、执行 Git、远端或 GitHub operation。
Unique next legal action: 在独立 admission Gate 下，仅判断是否可重新送审 R39；在该判断完成前不得修改 R39 files。
```
