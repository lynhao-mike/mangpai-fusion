# G6 / Task 8 R41：P-1 public run target-ref capture/provisioning seam admission 合同

- **Unit：** P-1-owned run target-ref capture/provisioning seam（仅 admission/contract）
- **Gate：** `CONTRACT — PASS / crypto-provider, registry and private signer provisioning frozen`
- **现行依赖：** P-1 verified-run-manifest fixture seam 已冻结；R39 feedback adapter 已冻结；R40 `REVISE`；P-2 与 Task 9-P `BLOCKED`；Task 9 amendment `STILL_OPEN`。
- **实现授权：** 否。本文与任何 review 均不授权 runtime、tests、Python、pytest、Git、远端或 GitHub operation。
- **作者写集：** 仅本文件。

## 1. Admission、唯一问题与边界

R40 的 [`construct_preprod_run_authority_v1()`](g6-task8-r40-preprod-authority-construction-seam-contract.md:22) 必须消费与 P-1 actual returned manifest 同源的四项 [`VersionedObjectRef`](../engine/f09/contracts.py:216)：`RUN_SNAPSHOT`、`DECISION_RUN`、`FEEDBACK_ATTACHMENT`、`MANIFEST`。R39 consumer 已冻结这项固定 closure（[`_validated_preprod_restricted_manifest_context()`](../engine/f09/feedback.py:970)），并要求前三项匹配 records、最后一项以 verifier-returned records digest 作 outer-ref binding（[`plans/g6-task8-r39-feedback-adapter-contract.md`](g6-task8-r39-feedback-adapter-contract.md:175)）。

当前 P-1 public manifest carrier [`ArtifactSetManifest`](../engine/f09/artifacts.py:545) 的 records 不包含完整 ref material：它缺少每个 target ref 所需的 `contract_version`、`source_locator_id`、`captured_at` 与 `revision_id` authority（[`ArtifactRecord`](../engine/f09/artifacts.py:520)）。[`RunArtifactSetRequestV1`](../engine/f09/artifacts.py:102) 虽带有 input snapshot refs，但未以现有事实证明它能唯一产生三项 output target refs，且 returned manifest 不保留该 request。不得由 Task 9、R40 或 feedback owner 猜测、补写、从 projection bytes/路径/时钟重建这些字段。

本 unit 只裁决 P-1 是否拥有一个**独立的 public、纯内存、returned-manifest-bound** target-ref carrier/provisioning seam；不实现该 seam，不修改 R40/R39，不改变 P-1 lifecycle/verifier，不修改 Task 9/P-2，也不创建 authority 或 digest。

## 2. 观察事实、推论与未知项

### 2.1 Observed facts

1. [`provision_verified_run_manifest_fixture_v1()`](../engine/f09/artifacts.py:1541) 只返回 manifest；其 locally-held input refs 与 records attempt data 不构成 public returned target-ref carrier。
2. [`coordinate_run_artifact_set_v1()`](../engine/f09/artifacts.py:1745) 的 public return type 是 [`ArtifactSetManifest`](../engine/f09/artifacts.py:545)，没有可见 target-ref return channel。
3. R39 对 restricted authority 的 `target_refs` 需要 exact [`VersionedObjectRef`](../engine/f09/contracts.py:216) material，并在 consumer 中作为 authority canonical material 的一部分；因此 ref 字段不能作为无语义的 placeholder。
4. R40 保留 feedback-owned authority digest construction，但已禁止 Task 9 自造 `target_refs`，并因缺少 owner-owned source 维持 `REVISE`（[`plans/g6-task8-r40-preprod-authority-construction-seam-contract.md`](g6-task8-r40-preprod-authority-construction-seam-contract.md:94)）。

### 2.2 Inference

完整 target-ref capture/provisioning 是 P-1 run graph 的 provenance/identity 问题，不是 feedback digest construction 问题。任何 future seam 必须由 P-1 owner 定义、验证并返回；feedback owner 只能消费该 returned value，再自行生成 authority digest。

### 2.3 已解决的 retained decision 与剩余限制

用户已明确保留并选择：P-1 lifecycle 通过一个绑定 actual returned manifest 的 public DTO 返回四项完整 `target_refs`；R40 只能消费该 DTO 的 returned refs。capture input 是 frozen `RunArtifactTargetRefsRequestV1`，含三项完整 projection [`VersionedObjectRef`](../engine/f09/trace.py:53)，并必须与 [`RunArtifactSetRequestV1`](../engine/f09/artifacts.py:102) key 的 case/track/run 精确一致。MANIFEST outer-ref 的余下五项 canonical material 则由 frozen `ManifestOuterRefRequestV1` 显式输入；新 callable exact type-guard 后仅使用其值，不得从 `now`、path、request 或 ambient state 推导。此决定使 P-1 成为 complete ref material 与其 manifest binding 的唯一 owner，禁止 Task 9/R40/feedback 构造、补写或重标这些 refs。

用户另已保留并选择 runtime crypto/provisioning model：新增根目录 [`requirements.txt`](../requirements.txt) 作为唯一正式 runtime dependency authority，只含 `cryptography>=42.0,<46.0`；不创建 lockfile，发布环境由受控构建流程在该范围内解析。P-1 只可使用该 provider 的 Ed25519 API；不得手写密码学、改用 HMAC 或依赖偶然安装。生产部署进程组合负责从部署秘密管理层取得私钥，并仅通过 [`engine/f09/artifacts.py`](../engine/f09/artifacts.py) 内 module-private installer 安装 private signer port；P-1 不读取 filesystem、environment、network 或 clock 来取得私钥。registry getter 与 public verifier 也不得读取这些来源。测试只可 monkeypatch 此 module-private signer port，不得新增 public signer setter、private-key DTO、环境变量或文件 fixture。

该决定不改变现有 [`coordinate_run_artifact_set_v1()`](../engine/f09/artifacts.py:1745) 的 return ABI；future implementation 必须另开 versioned lifecycle callable。对非 `V5_V6_PREPROD` request，该新 callable 必须在 coordinator 前抛 [`F09ContractError`](../engine/f09/errors.py)，且 coordinator/verifier/DTO 调用数均为零。它不授权 runtime/tests，三项 projection ref material 仅能由 exact capture DTO 提供，不能用 path、projection bytes、clock 或 ambient state 推导。

## 3. 冻结的 P-1 returned-carrier surface

future implementation 只能在 [`engine/f09/artifacts.py`](../engine/f09/artifacts.py) 新增下列 versioned public DTO 与 callable；现有 [`coordinate_run_artifact_set_v1()`](../engine/f09/artifacts.py:1745) 的签名、return type 与行为不得改变：

```python
@dataclass(frozen=True)
class RunArtifactTargetRefsRequestV1:
    run_snapshot_ref: VersionedObjectRef
    decision_run_ref: VersionedObjectRef
    feedback_attachment_ref: VersionedObjectRef


@dataclass(frozen=True)
class ManifestOuterRefRequestV1:
    revision_id: str | None
    schema_version: str
    contract_version: str | None
    source_locator_id: str | None
    captured_at: str | None


@dataclass(frozen=True)
class RunArtifactSetPublicKeyV1:
    key_id: str
    public_key_b64url: str
    status: Literal["ACTIVE", "REVOKED"]


@dataclass(frozen=True)
class RunArtifactSetPublicKeyRegistryV1:
    registry_version: str
    keys_by_id: Mapping[str, RunArtifactSetPublicKeyV1]


@dataclass(frozen=True)
class IssuedRunArtifactSetProofV1:
    algorithm: Literal["Ed25519"]
    key_id: str
    signature_b64url: str


@dataclass(frozen=True)
class RunArtifactSetResultV1:
    manifest: ArtifactSetManifest
    target_refs: tuple[VersionedObjectRef, ...]
    issuance_proof: IssuedRunArtifactSetProofV1


def coordinate_run_artifact_set_with_target_refs_v1(
    root: Path,
    request: RunArtifactSetRequestV1,
    *,
    target_refs_request: RunArtifactTargetRefsRequestV1,
    manifest_outer_ref_request: ManifestOuterRefRequestV1,
    existing_manifest: ArtifactSetManifest | None,
    attempt_id: str,
    now: str,
) -> RunArtifactSetResultV1: ...


def get_run_artifact_set_public_key_registry_v1() -> RunArtifactSetPublicKeyRegistryV1: ...


def canonicalize_run_artifact_set_issuance_payload_v1(
    manifest: ArtifactSetManifest,
    target_refs: tuple[VersionedObjectRef, ...],
) -> bytes: ...


def validate_run_artifact_set_result_issuance_v1(
    result: RunArtifactSetResultV1,
) -> None: ...
```

1. 字段、顺序、类型、keyword-only boundary、return type 与 public verifier signature 精确如上。六个 DTO 均为 frozen；`keys_by_id` 必须为 immutable mapping，mapping key 与其 `RunArtifactSetPublicKeyV1.key_id` exact equal，且不得有重复或空 `key_id`。`registry_version` 必须为 nonblank exact `str`；`public_key_b64url` 必须为 nonblank unpadded base64url exact `str`，解码后恰为 32 bytes Ed25519 public key；`status` 必须 exact 为 `ACTIVE` 或 `REVOKED`。

   `artifacts.py` 内仅允许一个 module-private registry installer：`_install_run_artifact_set_public_key_registry_v1(*, registry: RunArtifactSetPublicKeyRegistryV1) -> None`。生产部署进程组合只能在启动阶段调用它一次；`registry` 必须由部署秘密管理层/受控配置层在 P-1 外部已解析，并在 installer 内被 exact-guard、重新构造成 module-owned immutable snapshot。installer 不得读取 filesystem、network、environment 或 clock，不得返回 registry write capability；registry 未安装时 [`get_run_artifact_set_public_key_registry_v1()`](../engine/f09/artifacts.py:1) 抛 `F09ContractError("RUN_ARTIFACT_SET_REGISTRY_UNAVAILABLE", "issuance_proof")`。重复安装、可变 mapping、任一 key/material/status/encoding violation 均抛 `F09ContractError("RUN_ARTIFACT_SET_REGISTRY_INVALID", "issuance_proof")`，且不得替换已安装 snapshot。首次成功安装后，同一 process lifetime 内其 `registry_version` 和 keys material 永久不可变。测试仅可 monkeypatch module-private registry 与 signer ports，不得调用任一 installer。

   `get_run_artifact_set_public_key_registry_v1()` 不接收输入、只返回上述 P-1 module-owned in-memory immutable registry snapshot；不得读取 filesystem、network、environment 或 clock。`manifest` 必须是 carrier callable 内恰一次调用 [`coordinate_run_artifact_set_v1()`](../engine/f09/artifacts.py:1745) 的 actual returned object，不得由 caller、filesystem discovery、cache、fixture 或 feedback 重建/替换。
2. `IssuedRunArtifactSetProofV1` 是公开、value-verifiable issuance proof，不是 opaque capability：`algorithm` 必须 exact literal `Ed25519`（RFC 8032），`key_id` 必须 nonblank exact `str`，`signature_b64url` 必须 nonblank unpadded base64url exact `str`，解码后恰为 64 bytes。P-1 在 successful coordinator/verifier/join path 末尾，以仅由 P-1 private signer port 注入的专属 Ed25519 private key 对第 8 项 frozen payload 的 exact JCS UTF-8 bytes 签名，创建 proof 并返回同一 result；私钥、signer port、installer、注入配置与 registry write capability 绝不进入 result、任何 public callable、feedback 或 R40。

   `artifacts.py` 内仅允许一个 module-private installer：`_install_run_artifact_set_signer_port_v1(*, key_id: str, private_key: object) -> None`。生产部署进程组合只可在启动阶段调用它一次；`private_key` 必须是部署秘密管理层在 P-1 外部已解析的 `cryptography` `Ed25519PrivateKey` instance。installer 必须 lazy-import provider、exact-validate nonblank `key_id`、从该 key 导出 32-byte raw public key，并以 unpadded base64url 与 immutable registry 中同 `key_id` 的唯一 `ACTIVE` public key exact compare；不合格、unknown/revoked/mismatch、provider import failure 或重复安装均抛 `F09ContractError("RUN_ARTIFACT_SET_SIGNING_KEY_INVALID", "issuance_proof")`，且不得改变已安装 port。安装成功后，module-private port 仅持有 `key_id` 与可调用的 sign operation；installer 不得返回私钥或 port，也不得自行读取 filesystem、environment、network 或 clock。测试仅可 monkeypatch module-private port，不得调用 installer、设置环境变量、使用私钥文件 fixture 或新增 public signer setter/DTO。

   port 只能产生与 public registry 中 `ACTIVE` key 相同 `key_id` 的签名；缺 port 抛 `F09ContractError("RUN_ARTIFACT_SET_SIGNER_UNAVAILABLE", "issuance_proof")`，provider/import 或 signer execution failure 抛 `F09ContractError("RUN_ARTIFACT_SET_SIGNING_FAILED", "issuance_proof")`；均在 proof/DTO 返回前 fail closed，零 feedback/learning。
3. `canonicalize_run_artifact_set_issuance_payload_v1()` 是唯一 public、同步、纯内存 payload serializer：它 exact-guard `manifest`、`target_refs` 并只接受第 8 项的 verified four-role closure，返回 UTF-8 RFC 8785 JCS bytes。`validate_run_artifact_set_result_issuance_v1()` 必须 exact-guard result/proof classes 和 proof shape，恰一次调用该 serializer 与 `get_run_artifact_set_public_key_registry_v1()`，按 `key_id` 取得唯一 `ACTIVE` key，再验证 Ed25519 signature。unknown/revoked/non-unique key、registry/serializer/type/encoding failure、algorithm mismatch、payload mismatch 或验签失败均抛 `F09ContractError`，不调用 coordinator、manifest verifier、feedback 或 learning。registry 轮换只能发布新增 `key_id` 的新 immutable `registry_version`；旧 key 在新 snapshot 中未标记 `REVOKED` 时继续验证既有 proofs。R40 只可调用此 verifier，不得读取私钥、构造 proof、取得 registry 或自行验签。
4. 先 exact type guards 与 semantic guards：`request` 必须 exact [`RunArtifactSetRequestV1`](../engine/f09/artifacts.py:102)，`target_refs_request` 必须 exact `RunArtifactTargetRefsRequestV1`，其中三个成员均为 exact [`VersionedObjectRef`](../engine/f09/trace.py:53)；`manifest_outer_ref_request` 必须 exact `ManifestOuterRefRequestV1`。随后，在 coordinator 前按 R39 restricted material rules 验证三个 capture ref：`object_type`、`object_id`、`schema_version` 为 nonblank exact `str`，`revision_id`、`contract_version`、`source_locator_id`、`captured_at` 为 `None` 或 nonblank exact `str`，`digest_binding` 为 exact `DigestPresent` 且其 `DigestRef` 为 exact `sha256`、canonicalization 为 `RFC8785-JCS-UTF8` 或 `RAW-UTF8`、value 为 64 位小写十六进制 exact `str`。按相同 nullable/nonblank string rules 验证 `manifest_outer_ref_request` 五项，其中 `schema_version` 必须 nonblank。`request.key` 必须 exact [`RunArtifactSetKeyV1`](../engine/f09/artifacts.py:88) 且 `key.track is RunTrack.V5_V6_PREPROD`；任一 class 或 semantic guard 不合格均抛 [`F09ContractError`](../engine/f09/errors.py)，coordinator/verifier/DTO 调用数均为零。
5. 再对 `root`、`request`、`existing_manifest`、`attempt_id`、`now` 完全复用既有 P-1 lifecycle 的 validation、failure precedence 与 local-I/O boundary；不得改变 legacy API，亦不得创建第二个 lifecycle/write path。恰一次 coordinator 返回后，恰一次调用 public [`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1683)。
6. 三项 capture refs 的 object types/order 必须分别为 `RUN_SNAPSHOT`、`DECISION_RUN`、`FEEDBACK_ATTACHMENT`。coordinator/verifier 成功后，每一项必须按同名 `artifact_role` 精确 join actual returned manifest 的唯一 record，且逐项满足：`ref.object_id == record.artifact_id`、`ref.schema_version == record.schema_version`、`ref.digest_binding.digest == record.observed_digest`；三个 record roles 必须与 `request.key.projection_roles` 精确同序，因此这些 joins 将 capture refs 的 case/track/run identity 精确闭合至 actual manifest 的 `RunArtifactSetKeyV1`。不得把该 relation 解释为 `VersionedObjectRef` 不存在的直接 case/track/run fields equality。capture DTO 是其完整八字段 material 的唯一 source；不得接受 tuple、path/projection bytes、clock 或 ambient state 补足。
7. `MANIFEST` 是 P-1 owner 在 verifier 成功后构造的 outer-ref，不是 record/payload：`object_type` 精确为 `MANIFEST`，`object_id == manifest.manifest_id`，且 exact `DigestPresent` binding digest 等于该唯一 verifier call 的 returned records digest；不得用 `manifest.digest`，不得制造 `MANIFEST` record，且不得伪造 manifest schema/contract equality target。其 `revision_id`、`schema_version`、`contract_version`、`source_locator_id`、`captured_at` 必须按字段逐一、原样来自 exact `manifest_outer_ref_request`；不得从 `now`、path、`request`、manifest、clock 或 ambient state 推导、替换或补写。
8. DTO return 前，`target_refs` 必须为按上述顺序由三个 capture refs 与 P-1-built MANIFEST outer-ref 组成的 exact tuple；records closure 仅含三个 run roles 且各一项，所有 record 已 verified。`canonicalize_run_artifact_set_issuance_payload_v1()` 的唯一 JCS value tree 精确为 `{ "domain": "f09.run-artifact-set.issuance.v1", "manifest": ..., "target_refs": ... }`，**不含** proof、registry、key_id 或 signature：`manifest` object field order 为 `manifest_id`、`key`、`records_canonical_b64url`、`records_digest`、`state`、`detected_issues`；`records_canonical_b64url` 是 public [`canonicalize_artifact_records()`](../engine/f09/artifacts.py:709) 返回 bytes 的未填充 base64url，`records_digest` 是 public [`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1683) 返回 digest，`state` 是 enum value string，`detected_issues` 必须为 empty array。`key` object field order 为 `operation`、`case_id`、`track`、`run_id`、`source_digest`、`schema_versions_digest`、`contract_digest`、`input_snapshot_refs_graph_digest`、`projection_roles`、`projection_digest_by_role`、`canonical_key_digest`；每个 digest object field order 为 `algorithm`、`canonicalization`、`value`；enum 使用 `.value` string，`projection_roles` 与 `target_refs` 均是 ordered arrays，`projection_digest_by_role` 依 `projection_roles` 逐项形成 object。每个 `target_refs` element field order 为 `object_type`、`object_id`、`revision_id`、`schema_version`、`contract_version`、`digest_binding`、`source_locator_id`、`captured_at`；`None` 编码 JSON `null`；`digest_binding` object field order 为 `status`、`digest`，其中 `status` 是 `PRESENT` 且 `digest` 使用上述 digest object。payload 仅接受第 6--7 项的 exact verified material，serializer 不得调用 feedback private helper、复制 alternate serializer 或改用 digest algorithm。任何 missing/extra/reordered role、任一第 6 项 join mismatch（包括 cross-run swap）、legacy key、`STAGED_L6`、production、verifier failure、field-material ambiguity 或 signing/key failure 都 typed fail closed，零 DTO / authority / proof。
9. callable 不导入 artifacts underscore symbols、不复制 serializer/digest algorithm，也不调用 feedback/R40/binder/eligibility/learning。该 callable 的返回不构成 `PreprodRunAuthority`，不计算 feedback-owned `content_digest`，且不自动使 Task 9/P-2 可用。

## 4. 条件 write set、negative ledger 与 future verification

若且仅若后续总控独立授权 implementation，条件 write set 恰为：

```text
requirements.txt
engine/f09/artifacts.py
tests/f09/test_artifact_lifecycle.py
```

[`requirements.txt`](../requirements.txt) 是唯一正式 runtime dependency authority，完整内容只能为 `cryptography>=42.0,<46.0` 加末尾换行；不创建或更新任何 lockfile，不修改 [`requirements-dev.txt`](../requirements-dev.txt) 或 [`pyproject.toml`](../pyproject.toml)。

未来 tests（未授权、未执行）至少覆盖：legacy coordinator ABI 不变；六个 new DTO、四个 public callable 与 private signer-port boundary 的 exact signature/frozen shape；in-memory registry 的 immutable snapshot、key-id/key-material equality、32-byte key、`ACTIVE`/`REVOKED`、unknown/non-unique key 与仅新增 key-id 的 rotation；Ed25519 issuance proof/public verifier 的 actual-result、substitute、clone、deserialize、direct-construction、altered/stale、invalid base64url、algorithm mismatch 与验签失败 cases；非 exact/malformed capture DTO、malformed manifest-outer DTO 与非 preprod request 在 coordinator 前 fail closed；legacy-first coordinator exactly once；returned manifest object identity；manifest verifier exactly once；four-role closure/order；每个 run record 的 ref identity/digest closure；MANIFEST outer-ref verifier digest 与五字段 exact pass-through（拒绝从 `now`/path/request/ambient state 派生）；proof payload 所有 field tree、base64url records bytes、JCS byte equality 与不含 proof/registry/key-id/signature；cross-run/legacy/STAGED/prod/ambiguous material fail closed；zero I/O/feedback/learning；无 artifacts private import/serializer copy；既有 lifecycle regressions。任何其他路径需求必须 STOP 并另开合同。

## 5. Negative ledger 与 STOP conditions

| ID | 原子反例 | 必须结果 |
|---|---|---|
| R41-F01 | 用 manifest record、path、projection bytes、clock 或 caller label 猜测缺失 ref 字段 | `REVISE`；不得起草 implementation signature。 |
| R41-F02 | Task 9/R40/feedback 生成、重标、缓存或替代 P-1 target refs | fail closed；零 authority。 |
| R41-F03 | `FEEDBACK_ATTACHMENT` 缺失/可选，或 `MANIFEST` 成为 record/payload / 使用 `manifest.digest` | 与 R39 不兼容；`REVISE`。 |
| R41-F04 | carrier 与 coordinator actual returned manifest 无 exact binding，或可 cross-run swap | `REVISE`；不得进入 implementation。 |
| R41-F07 | 将 public frozen dataclass 声称为 caller 不可构造的 opaque capability，或以未冻结 private registry/identity witness 证明 issuer | `REVISE`；该已否决模型不得复活。 |
| R41-F08 | 未冻结 public-key registry 的版本、不可变性、唯一 key 解析或 revoked disposition；或由 R40/feedback 自行选择验签 payload/serializer | `REVISE`；不得进入 implementation。 |
| R41-F05 | 为填补未知项而修改 P-1/R39/R40/Task 9/P-2 runtime、tests，或运行命令 | STOP；该行为不在本文授权内。 |
| R41-F09 | 以环境变量、文件、网络、clock、公开 setter/DTO 或 public callable provision、替换、导出私钥、signer 或 registry | `REVISE`；不得进入 implementation。 |
| R41-F10 | 不通过 [`requirements.txt`](../requirements.txt) 声明 `cryptography>=42.0,<46.0`，手写密码学、使用 HMAC/替代算法、偶然环境依赖，或创建 lockfile | `REVISE`；不得进入 implementation。 |
| R41-F06 | 任一操作可能改变 GitHub service-side state | `BLOCKED`；永久禁止执行。 |

## 6. Gate、证据边界与唯一下一合法动作（issuer-proof revision 历史）

**现行 verdict：`PASS — contract review gate closed`。** 本合同已按用户决定冻结 P-1 in-memory immutable public-key registry、private signer-port boundary 与 versioned public JCS payload serializer，并已完成第 17 节逻辑新鲜、只读独立合同审查；仍没有 runtime、test 或 behavior evidence，未执行 Python、pytest、Git、远端或 GitHub-mutating operation。

不得推导：R41 implementation authorization、R40 `PASS`、non-null [`PreprodRunAuthority`](../engine/f09/feedback.py:192) 可构造、Task 9 contract `PASS`、P-2/Task 9-P 解锁、全仓正确性或 GitHub 同步。

**唯一下一合法动作：** 仅文档修订 [`plans/g6-task8-r40-preprod-authority-construction-seam-contract.md`](g6-task8-r40-preprod-authority-construction-seam-contract.md)：在 manifest verifier 前 exact 调用 P-1 issuance verifier，并为其失败冻结零 manifest-verifier / 零 authority disposition；不得启动 implementation、tests 或命令。

## 7. 已消费的前一轮 admission review（历史）

- **Gate：** `ADMISSION / fresh STATIC_REVIEW`
- **审查角色：** logical fresh Static Reviewer；只使用 R41、现有 P-1 public surface、R39/R40 边界与 [`VersionedObjectRef`](../engine/f09/trace.py:53) shape，不采纳作者自评。
- **授权边界：** 本地只读；未执行命令、Python、pytest、Git、远端或 GitHub operation。
- **直接证据：** [`ArtifactRecord`](../engine/f09/artifacts.py:520) 仅拥有 `artifact_id`、role、case/track/run、path、schema 与 digest/state 等字段，未携带 ref 的 `revision_id`、`contract_version`、`source_locator_id`、`captured_at`。现有 public fixture [`provision_verified_run_manifest_fixture_v1()`](../engine/f09/artifacts.py:1541) 仅返回 [`ArtifactSetManifest`](../engine/f09/artifacts.py:545)；运行时 [`engine/f09/artifacts.py`](../engine/f09/artifacts.py) 中的唯一 [`VersionedObjectRef`](../engine/f09/trace.py:53) construction 是其函数内局部 input-snapshot fixture（[`engine/f09/artifacts.py`](../engine/f09/artifacts.py:1543)），不是 public output target-ref carrier。[`engine/f09/application.py`](../engine/f09/application.py) 未包含 run target-ref surface。
- **审查结论：** “现有 public P-1 surface 缺少完整 output target-ref material source”得到支持；R41 没有虚构 callable/DTO、write set 或 schema literal，且将这些保留为未知，因此不存在可由本地合同消解的实现细节。
- **Falsifier：** 若有已冻结 public P-1 callable 返回与 actual manifest identity 绑定的完整四项 target refs，或 manifest/record 已有上述全部八字段的权威 source，则本审查必须 `REVISE`；所审范围未发现该 surface。
- **Verdict：** **`AUTHORIZATION_REQUIRED`**。下一步要求一个产品/API 级 retained decision：三项 projection target refs 中 `revision_id`、`contract_version`、`source_locator_id`、`captured_at` 的 canonical owner/source 是什么，以及该 source 是否应作为 P-1 public returned carrier。standing local autonomy 不能替用户在多种材料不同的 public provenance model 间选择。
- **禁止推导：** 本 verdict 不等于 R41/R40/Task 9 `PASS`，不授权 implementation/tests，也不解除 P-2/Task 9-P `BLOCKED` 或 Task 9 amendment `STILL_OPEN`。受控会话未执行 GitHub-mutating operation。

## 8. 用户决定后的逻辑新鲜、只读独立合同审查

- **Gate：** `CONTRACT / fresh STATIC_REVIEW`
- **审查角色：** logical fresh Static Reviewer；未采纳作者自评或前一 admission verdict。
- **授权边界：** 只读复核 R41、P-1 runtime surface、R39/R40 contracts 与 [`VersionedObjectRef`](../engine/f09/trace.py:53) shape；未执行命令、Python、pytest、Git、远端或 GitHub operation。
- **直接证据：** [`RunArtifactSetRequestV1`](../engine/f09/artifacts.py:102) 只有 key、`run_id`、`input_snapshot_refs`、`schema_version`、projections；它没有 per-projection `VersionedObjectRef` material。R41 第 3 节第 3 项同时把三项 output refs 的八字段唯一 source 指向该 request 的“owner-owned versioned capture inputs”，却将每 role 的 exact capture mapping 延后到尚未定义的 future implementation contract。
- **审查发现 R41-R01（阻断）：** 用户决定已解决“哪个 owner / carrier”问题，但未提供三项 projection output refs 的具体 canonical source model。当前 frozen request shape 不能携带所需的 per-role fields；R41 既禁止从路径/bytes/clock 推导，又没有新增独立 capture DTO/input。因此该 callable 不能在不臆造 material 的情况下实现，违反 CONTRACT Gate 的唯一、完整、可实现条件。
- **审查发现 R41-R02（阻断）：** R41 第 3 节第 5 项要求 track “仅 `V5_V6_PREPROD`”，但其 callable 未有单独 track input，唯一可用 discriminator 是 `request.key.track`。合同没有冻结应当拒绝 `STAGED_L6`/production 的精确 validation precedence 与 error boundary，也未说明 non-preprod 是否仍可合法产生 P-1 manifest 却只不产生 carrier。把此决策留给 implementation 会改变 versioned lifecycle capability，而非纯 carrier packaging。
- **Falsifier：** 任一修订若仍未定义 per-role complete capture carrier/input，或允许实施者从 bytes/path/time 推导它；或仍未决定 non-preprod request 对新 callable 的 disposition，则必须继续 `REVISE`。
- **Verdict：** **`REVISE`**。R41 不可进入 implementation authorization；R40 继续 `REVISE`，P-2 与 Task 9-P 继续 `BLOCKED`，Task 9 amendment 继续 `STILL_OPEN`。
- **最小修订要求：** 开立/冻结 P-1 versioned per-role target-ref capture input DTO（含三项 complete refs 或每项八字段的 owner-owned source）及其与 `RunArtifactSetRequestV1`/key 的 exact binding，并确定新 carrier callable 对非 `V5_V6_PREPROD` request 的 closed disposition。在此之前不得将 R41 的 conditional write set、tests 或 API 视为可实施授权。

## 9. complete API revision 后的逻辑新鲜、只读独立合同审查

- **Gate：** `CONTRACT / fresh STATIC_REVIEW`
- **审查角色：** logical fresh Static Reviewer；重新只读审查第 3--6 节及必要 runtime consumer shapes，不采纳作者 self-assessment 或第 8 节 verdict。
- **授权与副作用边界：** 仅本地只读。未执行命令、Python、pytest、Git、远端或 GitHub operation；没有修改 runtime/tests。
- **直接证据：** 新 capture DTO 已使三项 projection refs 的八字段拥有 explicit、exact caller/P-1 capture source；非 preprod guard 也已在 coordinator 前冻结为 `F09ContractError` 与零 coordinator/verifier/DTO 调用。R39 runtime 对前三项实际只验证 `object_type` 到 record role、`object_id == artifact_id`、`schema_version == record.schema_version`、`digest_binding.digest == record.observed_digest`，并以 manifest/key 的 `case_id`、`run_id`、`track` 约束该 records set（[`_validated_preprod_restricted_manifest_context()`](../engine/f09/feedback.py:970)）。`VersionedObjectRef` 本身没有 `case_id`、`track` 或 `run_id` fields（[`VersionedObjectRef`](../engine/f09/trace.py:53)），故第 3 节第 4、6 项的 key identity 必须理解为该 ref 经 exact record join 对 actual manifest/key 的关系，而非不存在的 ref field equality。
- **审查发现 R41-R03（阻断）：** 第 3 节第 5 项只冻结了 MANIFEST outer-ref 的 `object_type`、`object_id` 与 verifier-returned digest，却明确把其余五个 canonical fields 留给“future implementation contract”。但 R39 会把所有八个 fields 纳入 restricted authority canonical material（[`_restricted_preprod_target_ref_material()`](../engine/f09/feedback.py:436)）。现有 manifest/key 没有 manifest-ref `revision_id`、`schema_version`、`contract_version`、`source_locator_id` 或 `captured_at` 的既有 public canonical source；由实施者选择 literal、复用 `request.schema_version`、复用 `now` 或创建 locator 都会产生不同 authority content material。此为 public API/provenance choice，不能由 implementation 填补。
- **Falsifier：** 若既有 public P-1 contract 已精确规定 MANIFEST outer-ref 的上述五字段，或用户明确冻结其每个 source/value，则 R41-R03 消失；所审 facts 未提供任一项。若后续修订允许这些 fields 从 ambient clock、path 或猜测补齐，或把 key identity 误写为 `VersionedObjectRef` 不存在的 field equality，则审查仍必须 `REVISE`。
- **Verdict：** **`REVISE`**。capture DTO 与 non-preprod disposition 的两个前轮 blockers 已被解决；但 R41 尚不唯一、完整且可实施。R40 继续 `REVISE`，P-2 与 Task 9-P 继续 `BLOCKED`，Task 9 amendment 继续 `STILL_OPEN`。
- **唯一最小后续：** 用户须保留并决定 MANIFEST outer-ref 余下五字段的 canonical material/source；这不是 local-only implementation choice。决定到位后，才可仅修订 R41 并进行另一轮 logical fresh read-only review。

## 10. R41-R03 retained decision

- **用户决定：** 新增 frozen `ManifestOuterRefRequestV1`，完整承载 MANIFEST outer-ref 的 `revision_id`、`schema_version`、`contract_version`、`source_locator_id`、`captured_at`；新 carrier callable 仅在 exact type guard 成功后原样使用这些值，禁止从 `now`、path、request 或 ambient state 推导。
- **合同影响：** 本决定仅补足 P-1 public returned-carrier 的输入 provenance，未改变 legacy coordinator ABI、R39/R40 owner boundary、conditional write set 或任何 implementation/test authorization。
- **后续 Gate：** 该文档修订使第 9 节 review 失效；必须进行新的逻辑新鲜、只读独立合同审查。

## 11. MANIFEST complete-input revision 后的逻辑新鲜、只读独立合同审查

- **Gate：** `CONTRACT / fresh STATIC_REVIEW`
- **审查角色：** logical fresh Static Reviewer；只使用当前 R41 frozen surface、[`VersionedObjectRef`](../engine/f09/trace.py:53) 与 R39 restricted consumer requirements；不采纳第 10 节作者说明或此前 review verdict。
- **授权与副作用边界：** 只读审查；未执行命令、Python、pytest、Git、远端或 GitHub operation，亦未修改 runtime/tests。
- **直接证据：** `ManifestOuterRefRequestV1` 已为 MANIFEST ref 的五个此前缺失 fields 提供唯一 explicit source，且第 3 节第 5 项冻结了 verifier-returned digest、actual manifest ID 与原样 pass-through，因此 R41-R03 已被解决。R39 对每个 restricted ref 则还要求 exact `DigestPresent`（[`_restricted_preprod_target_ref_material()`](../engine/f09/feedback.py:436)），并要求其字符串 fields 符合 nonblank/nullable-nonblank material；仅 `VersionedObjectRef` exact class 不保证这些 nested material conditions。
- **审查发现 R41-R04（阻断）：** 第 3 节第 2 项仅对三个 capture refs 作 exact-class guard，没有冻结它们或 `ManifestOuterRefRequestV1` 输入 material 的 R39-compatible semantic validation（尤其是 capture ref 的 `DigestPresent`、digest shape、nonblank/nullable-nonblank fields）。第 3 节第 5 项已要求新建 MANIFEST binding 为 exact `DigestPresent`，但没有冻结其五项 pass-through input 的同等 material validity。实施者因而可选择在 coordinator 前、coordinator 后或仅让 R40 consumer 拒绝这些值；这些 choices 改变 failure precedence、I/O 边界与 carrier 的 usable public contract，不能留作 implementation discretion。
- **Falsifier：** 若 R41 明确要求在 coordinator 前按照 R39 restricted material rules 验证所有 capture refs，以及 `ManifestOuterRefRequestV1` 的五项值，并对任一不合格值统一 `F09ContractError`、零 coordinator/verifier/DTO，则 R41-R04 消失。若只验证 DTO/class、允许 `DigestMissing` 或把 semantic validation 延后给 R40，则必须维持 `REVISE`。
- **Verdict：** **`REVISE`**。R41-R03 已关闭，但 R41-R04 仍使 validation/failure precedence 不唯一。R40 继续 `REVISE`，P-2 与 Task 9-P 继续 `BLOCKED`，Task 9 amendment 继续 `STILL_OPEN`；本 verdict 不授权 implementation/tests。
- **唯一最小后续：** 仅修订 R41：冻结上述两类输入的 exact R39-compatible semantic guards、pre-coordinator precedence 与零调用 disposition，随后重新进行逻辑新鲜、只读合同审查。

## 12. R41-R04 最小合同修订

- **修订：** 第 3 节第 2 项已冻结所有 capture refs 与 `ManifestOuterRefRequestV1` 的 R39-compatible semantic guards；任一 class 或 material 不合格均在 coordinator 前以 `F09ContractError` fail closed，且 coordinator/verifier/DTO 调用数为零。
- **边界：** 该修订不改变 DTO/API shape、legacy coordinator ABI、P-1/R39/R40 ownership、conditional write set 或 implementation/test authorization。
- **后续 Gate：** 本修订使第 11 节 review 失效；唯一下一合法动作是新的 logical fresh、read-only CONTRACT review。

## 13. join-complete revision 后的逻辑新鲜、只读独立合同审查（历史）

- **Gate：** `CONTRACT / fresh STATIC_REVIEW`
- **审查角色：** logical fresh Static Reviewer；仅使用当前 frozen R41 surface、P-1 public coordinator/verifier shapes、R39 restricted consumer checks 与 [`VersionedObjectRef`](../engine/f09/trace.py:53) shape；不采纳本文作者评估及第 7--13 节旧审查结论。
- **授权与副作用边界：** 仅本地只读审查。未执行命令、Python、pytest、Git、远端或 GitHub operation；未修改 runtime/tests。
- **直接证据与判定：**
  1. 新 callable 保留既有 [`coordinate_run_artifact_set_v1()`](../engine/f09/artifacts.py:1745) ABI，并把其恰一次 actual returned manifest object 放入 result，故没有第二 lifecycle/write path 或 caller/fixture substitution。
  2. `RunArtifactTargetRefsRequestV1` 与 `ManifestOuterRefRequestV1` 分别为三项 projection ref 及 MANIFEST ref 的完整八字段提供 explicit source；所有 R39-required material 在 coordinator 前具备 exact class 与 semantic fail-closed guard，未留给 path、bytes、clock、`now`、request 或 ambient state。
  3. 三 capture refs 与 returned manifest records 的 exact role/object-ID/schema/digest join，连同 manifest key 的 case/track/run，提供了可实施的 identity closure；这与 R39 实际 consumer checks（[`_validated_preprod_restricted_manifest_context()`](../engine/f09/feedback.py:970)）一致，且没有臆造 `VersionedObjectRef` 不存在的 identity fields。
  4. MANIFEST outer-ref 严格绑定 actual manifest ID 与唯一 public verifier-returned records digest，固定四角色顺序与 R39 closure 相容；未使用 `manifest.digest` 或生成 MANIFEST record。
  5. 非 preprod、任一 type/material/join failure 均在规定边界 typed fail closed；P-1 ownership、zero feedback/learning、closed conditional write set、legacy ABI 与 GitHub prohibition 均明确。
- **Falsifier：** 以下任一事实将推翻本 verdict：实现合同改变 legacy coordinator signature/return/behavior；任一 ref material 可由 non-DTO source 补足；coordinator 前 guard 后仍有 coordinator/verifier/DTO side effect；capture ref 未按第 3 节第 4 项 join；MANIFEST binding 使用 `manifest.digest`；或 callable 进入 feedback/R40/binder/eligibility/learning。当前 frozen contract 对这些反例均有明确禁止或 fail-closed disposition。
- **Verdict：** **`PASS`**。R41 contract 现为唯一、完整、可证伪且具备独立 implementation authorization request 所需的 CONTRACT evidence；此 PASS **不构成** implementation/test/Python/pytest/Git/远端/GitHub authorization，也不证明任何 runtime behavior。
- **直接证据边界：** 仅证明 R41 文档合同在所审 P-1/R39 facts 下通过 fresh static review；不证明未来实现、测试、R40 authority construction、Task 9 producer、P-2、Task 9-P 或全仓正确性。
- **唯一下一合法动作：** 仅文档修订 R40：让 feedback-owner seam 消费 future `RunArtifactSetResultV1` 的 actual returned `manifest` 与 returned `target_refs`，移除可由 Task 9/caller 自造的裸 refs supply；随后对 R40 执行新的逻辑新鲜、只读合同审查。R40 在该修订与审查完成前继续 `REVISE`；P-2 与 Task 9-P 继续 `BLOCKED`，Task 9 amendment 继续 `STILL_OPEN`。

## 14. issuer-capability revision 后的逻辑新鲜、只读独立合同审查（历史）

- **Gate：** `CONTRACT / fresh STATIC_REVIEW`
- **审查角色：** logical fresh Static Reviewer；只审查当时 R41 public shapes、Python dataclass public-construction semantics 与 R40 所需 pure-memory issuer proof；不采纳作者说明或第 13 节旧 PASS。
- **授权与副作用边界：** 仅本地只读审查；未执行命令、Python、pytest、Git、远端或 GitHub operation，未修改 runtime/tests。
- **直接证据：** 第 3 节将 `RunArtifactSetIssuanceCapabilityV1` 明确声明为 public frozen dataclass（第 58 行），但 Python public dataclass 自动公开可调用的 constructor；其空字段 shape 允许任意 caller 构造等价实例。与此同时，第 87 行要求 public verifier 依赖“P-1 private identity-held issuance witness”来区别 actual result，然而该 witness 的存储期限、并发/进程边界、replay disposition、lifetime cleanup 与 failure model均未冻结，且它是 R40 无法从 result value 验证的 ambient/private state。
- **审查发现 R41-R05（阻断）：** 当前修订同时要求“public frozen DTO 无 public constructor”和“public verifier 以未定义 private identity-held state 验证”，前者与 DTO shape 矛盾，后者把 issuer validity 定义为未冻结的 stateful capability registry。该设计既不是 value-verifiable public proof，也不是可由 R40 独立、纯内存且跨 owner 可靠消费的明确 API。实施者将不得不自行选择 token secrecy、registry lifecycle、serialization/process behavior 与 equality/identity semantics，违反 CONTRACT Gate 的唯一性和可实施性。
- **Falsifier：** 若 capability 改为非 public-constructible 的实际 Python surface并明确其持有/验证边界，或用户改选由公开 canonical material 可验证的 deterministic proof model，并分别冻结 verifier inputs、state/lifetime/replay/process behavior，则 R41-R05 消失。仅写 docstring、exact class guard 或私有 registry 的概念性描述不足以消除它。
- **Verdict：** **`REVISE`**。第 14 节的 PASS 已被本次 document revision 失效。R41 不授权 implementation/tests；R40 继续 `REVISE`，P-2 与 Task 9-P 继续 `BLOCKED`，Task 9 amendment 继续 `STILL_OPEN`。
- **唯一最小后续：** 用户须保留可验证 issuer provenance 的实际 API/security model：选择并冻结非 public-constructible capability 的真实 Python interface与状态边界，或替换为公开可验证的 proof model。不得由 implementation 自行决定。

## 附录 A. capture-ref / record join 最小合同修订（历史归档）

- **修订：** 第 3 节第 4、6 项已将三项 capture refs 与 actual returned manifest records 的 object ID、schema version、observed digest、role/order 关系冻结为 exact join，并明确 key 的 case/track/run closure 经 manifest/key 成立，而不是虚构 `VersionedObjectRef` fields。
- **边界：** 该修订只消除已有 consumer/runtime facts 支持的 relation ambiguity；不新增 public shape、不改变 owner、legacy ABI、write set 或 implementation/test authorization。
- **后续 Gate：** 本修订使第 11 节 review 失效；唯一下一合法动作是新的 logical fresh、read-only CONTRACT review。

## 15. Ed25519 issuance-proof revision 后的逻辑新鲜、只读独立合同审查（历史）

- **Gate：** `CONTRACT / fresh STATIC_REVIEW`。
- **审查角色：** logical fresh Static Reviewer；只审查当前第 3--6 节、R40 consumer contract、现有 P-1 public surface 与既有 canonicalization surface；不采纳作者说明或任何历史 `PASS` / `REVISE` verdict。
- **授权与副作用边界：** 仅本地只读；未执行命令、Python、pytest、Git、远端或 GitHub operation，未修改 runtime/tests。
- **直接证据：** 现有 [`engine/f09/artifacts.py`](../engine/f09/artifacts.py) 未定义 Ed25519 signer/verifier、public-key registry、`key_id`、revocation state 或 versioned immutable registry surface；全文搜索也未发现该 P-1 依赖。现有 public [`canonicalize_artifact_records()`](../engine/f09/artifacts.py:709) 只能 canonicalize records，`validate_run_artifact_manifest_v1()` 只返回 records digest（[`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1683)）。第 3 节第 8 项却要求一个覆盖 manifest、complete key、records bytes、verifier digest 与四 refs 的“P-1 public frozen serializer contract”，但没有定义其 callable、输入/输出 shape、field tree、version label 或已有权威 source；R39 的 [`_restricted_preprod_target_ref_material()`](../engine/f09/feedback.py:436) 是 feedback-private underscore helper，不能同时作为 P-1 public serializer。
- **审查发现 R41-R06（阻断）：** proof 的 `key_id` 只能指向概念性的 “versioned immutable public-key registry”。合同没有冻结 registry 的 public read interface、registry-version identity、key encoding、active/revoked representation、同一 `key_id` 的唯一性载体，或私钥与 signer 的 P-1-owned provision boundary。故实现者必须自选新文件/依赖、registry persistence/packaging 与 signing-key access model；这既超出第 4 节 closed write set，也使第 3 节第 3 项的 pure-memory verifier 无法从已定义 API 唯一实现。
- **审查发现 R41-R07（阻断）：** 第 3 节第 8 项只列出 payload 必含内容，未冻结 exact JCS value tree。特别是 `ArtifactSetManifest` / `RunArtifactSetKeyV1` 的 dataclass-to-JCS mapping、records canonical bytes 的 JSON representation（bytes 不属于 JCS value）、verifier digest 的 representation，以及四项 refs 的 ordered material container 都可有多个不同且合法的编码。禁止复制 serializer 又不存在对应 public serializer，故 producer 与 verifier 无法仅由当前合同导出唯一相同的 signed bytes。
- **关联 consumer 缺口：** 当前 R40 仍规定先调用 manifest verifier（[`construct_preprod_run_authority_v1()`](g6-task8-r40-preprod-authority-construction-seam-contract.md:22) 第 3 节第 2 项），没有要求先调用新的 issuance verifier；即使 R41 可实施，也尚未冻结 R40 的 required call order / zero-authority disposition。这不授权修改 R40，只证明 R40 继续 `REVISE`。
- **Falsifier：** 若 R41 已定义或引用一个现存、public、versioned immutable registry 的 exact read API 及 P-1 private signing-key boundary，并定义唯一、public、versioned manifest-plus-four-refs JCS payload serializer（含完整 field tree 与 bytes representation），且 conditional write set 覆盖这些实现归属，则 R41-R06/R41-R07 消失。仅有算法名、`key_id` 文本规则、概念性 registry 或“至少包含”字段清单均不足。
- **Verdict：** **`REVISE`**。Ed25519 public-proof 选择已排除 public dataclass opaque-capability 矛盾，但 registry 和 payload serializer 的实际 API/state boundaries仍未唯一、完整、可实施。R41 implementation authorization 不存在；R40 保持 `REVISE`，P-2 与 Task 9-P 保持 `BLOCKED`，Task 9 amendment 保持 `STILL_OPEN`。
- **唯一下一合法动作：** 请求用户保留一项最小 security/API decision：P-1 immutable public-key registry 的精确 public read surface、version/revocation/key-encoding model与 private signer provisioning boundary；以及 manifest-plus-four-refs payload 的唯一 public versioned JCS serializer/API（包括 bytes representation）。该用户决定已在当前第 3 节第 1--3、8 项落实；本历史 verdict 不再描述现行设计。

## 16. R41-R06 / R41-R07 retained decision

- **用户决定：** P-1 新增 frozen `RunArtifactSetPublicKeyV1` 与 `RunArtifactSetPublicKeyRegistryV1`，公开无参 [`get_run_artifact_set_public_key_registry_v1()`](../engine/f09/artifacts.py) 返回 module-owned in-memory immutable snapshot；registry 持有 `registry_version` 与按 `key_id` 唯一映射的 Ed25519 public key / `ACTIVE`、`REVOKED` 状态。私钥只由 P-1 private signer port 注入。P-1 新增公开 [`canonicalize_run_artifact_set_issuance_payload_v1()`](../engine/f09/artifacts.py)，输出 versioned JCS UTF-8 payload；records canonical bytes 编码为 unpadded base64url。
- **合同影响：** 第 3 节已明确 registry/value shape、process-lifetime immutability、rotation/revocation disposition、private signer boundary、serializer signature、exact JCS value tree、digest/enum/null/bytes representation 与 conditional write set；不改变 legacy coordinator ABI、R39/R40 owner boundary 或任何 implementation/test authorization。
- **后续 Gate：** 本决定使第 15 节历史 review 失效；唯一下一合法动作是新的 logical fresh、read-only CONTRACT review。

## 17. in-memory registry / public payload-serializer revision 后的逻辑新鲜、只读独立合同审查

- **Gate：** `CONTRACT / fresh STATIC_REVIEW`。
- **审查角色：** logical fresh Static Reviewer；只审查现行第 3--6 节、[`RunArtifactSetKeyV1`](../engine/f09/artifacts.py:88)、[`ArtifactSetManifest`](../engine/f09/artifacts.py:545)、[`canonicalize_artifact_records()`](../engine/f09/artifacts.py:709)、[`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1683)、[`VersionedObjectRef`](../engine/f09/trace.py:53) 与 R40 consumer boundary；不采纳作者说明或第 15 节历史 verdict。
- **授权与副作用边界：** 仅本地只读；未执行命令、Python、pytest、Git、远端或 GitHub operation，未修改 runtime/tests。
- **直接证据与判定：** 第 3 节现已定义 public registry DTO、无参 snapshot getter、key encoding/status/immutability/rotation rule，以及 private signer-port 的唯一所有权和 failure boundary。它还定义唯一 public payload serializer，精确冻结 top-level domain、manifest/key/ref/digest tree、enum/null rules、records bytes 的 base64url representation，并排除 proof/registry/key-id/signature；producer 和 public verifier 均被约束使用同一 serializer。现有 records canonicalization、manifest verifier与 ref shape提供了所引用 material 的实际 P-1/R39 facts；没有要求 R40 导入 private state 或自行选择 serializer。
- **Falsifier：** 若 registry getter 可返回可变 mapping、同一 snapshot 允许重复/不匹配 `key_id`、rotation 可重写既有 key material；若 private signer 可用 revoked/unknown key；若 payload 存在未定义 dataclass、digest、enum、null 或 bytes encoding；若 producer/verifier 可以不用同一 public serializer；或条件 implementation 需写入第 4 节以外文件，则本 review 必须 `REVISE`。现行合同对前四类反例均有明确 fail-closed/禁止条件，conditional write set 也覆盖 registry、serializer、signer integration 与其测试归属。
- **Verdict：** **`PASS`**。R41 的 issuer-proof contract 现已具有唯一、完整、可证伪的 public registry、private signing boundary 与 signed-payload API。此 PASS 只关闭 R41 文档合同审查 Gate；**不构成** implementation、tests、Python、pytest、Git、远端或 GitHub authorization，不证明 crypto/runtime behavior，也不构成 R40/Task 9/P-2 `PASS`。
- **唯一下一合法动作：** 仅文档修订 R40：在其 manifest verifier 前 exact 调用 [`validate_run_artifact_set_result_issuance_v1()`](../engine/f09/artifacts.py)，并冻结 issuance-verifier failure 的零 manifest-verifier/零 authority disposition；随后对 R40 执行新的逻辑新鲜、只读合同审查。R40 保持 `REVISE`；P-2 与 Task 9-P 保持 `BLOCKED`，Task 9 amendment 保持 `STILL_OPEN`。

## 18. Runtime implementation 前的 fresh admission / dependency review（历史）

- **Gate：** `ADMISSION / fresh STATIC_REVIEW`。
- **审查角色与输入：** logical fresh Analyst/Static Reviewer；只审查现行 R41 contract、[`engine/f09/artifacts.py`](../engine/f09/artifacts.py)、[`tests/f09/test_artifact_lifecycle.py`](../tests/f09/test_artifact_lifecycle.py) 与仓库声明的依赖 surface；不采纳第 17 节合同 PASS 作为 runtime 可实施性证据。
- **授权与副作用边界：** 仅本地只读；未编辑 runtime/tests，未运行 Python、pytest、Git、远端或 GitHub operation。本节只记录 admission 结论，不授权 implementation。
- **观察事实：**
  1. [`engine/f09/artifacts.py`](../engine/f09/artifacts.py:1) 现有 imports 和 repository-declared dependency surface 中没有 Ed25519 provider、`cryptography`、PyNaCl 或同类 runtime package；Python 标准库没有可替代的 Ed25519 sign/verify API。
  2. 当前 P-1 runtime 只提供 manifest lifecycle 与 [`validate_run_artifact_manifest_v1()`](../engine/f09/artifacts.py:1683)，尚无第 3 节要求的 signer port、key provisioning、Ed25519 verification primitive 或 immutable registry implementation。
  3. 第 4 节冻结的条件 write set 仅限 [`engine/f09/artifacts.py`](../engine/f09/artifacts.py) 与 [`tests/f09/test_artifact_lifecycle.py`](../tests/f09/test_artifact_lifecycle.py)，且未包含依赖声明/lockfile 或既有 crypto adapter；因此不能以未声明的环境安装、临时自实现密码学或新增依赖来满足第 3 节。
- **推论：** 第 17 节的 document-only `PASS` 仍证明 public proof/serializer contract 可审查；但它不证明现有本地依赖图可在闭合 write set 内安全实现 Ed25519。当前 implementation target 缺少唯一、已声明且可测试的 crypto provider 与 signer-port provisioning mechanism。
- **Falsifiers：** 若一个已声明、版本固定且本地可用的 Ed25519 provider 已存在，并能在不改动第 4 节 write set 外文件的条件下支持 private signer-port 与 public verification，则该 blocker 消失。仅声称系统环境可能安装某包、手写 Ed25519、以 HMAC/非对称替代算法代替，或在 tests 中 mock 掉签名均不能证伪。
- **Verdict：** **`REVISE`**。R41 不可进入 implementation authorization；R40 的 document-only CONTRACT PASS 不会产生可执行 implementation authorization。P-2 与 Task 9-P 保持 `BLOCKED`，Task 9 amendment 保持 `STILL_OPEN`。
- **最小修订要求：** 先对 P-1 Ed25519 provider 与 private signer-port 的实际实现来源做独立、document-only retained decision：要么冻结一个已声明/锁定的依赖及其允许的依赖文件 write set，要么冻结一个已有、已验证的本地 crypto port。不得手写密码学，不得以环境偶然依赖作为合同事实。
- **唯一下一合法动作：** 仅开立上述 P-1 crypto-provider / signer-port boundary 的 document-only admission；不得修改 runtime/tests、运行命令、执行 Git、远端或 GitHub operation。

## 19. R41 crypto-provider / signer-port retained decision

- **直接观察：** repository dependency inventory 在排除 [`.git`](../.git) 后仅发现 [`pyproject.toml`](../pyproject.toml) 与 [`requirements-dev.txt`](../requirements-dev.txt)；前者只有 pytest configuration，后者明确是 development/test entrypoint，均不是 runtime authority。当前不存在 [`requirements.txt`](../requirements.txt)、lockfile、packaging manifest 或已声明 Ed25519 provider。
- **用户 retained decision：** 新建 [`requirements.txt`](../requirements.txt) 作为唯一 runtime authority，唯一条目为 `cryptography>=42.0,<46.0`，不创建 lockfile；受控发布构建在该范围内解析。P-1 使用 `cryptography` Ed25519 implementation。生产部署进程组合从部署秘密管理层取得私钥，并从部署秘密管理层/受控配置层取得完整 public-key registry，分别调用 P-1 module-private signer/registry installers；P-1 runtime、registry getter 和 verifier 均不读取文件、环境、网络或 clock。installers 不公开、不得返回私钥或 registry write capability；测试仅 monkeypatch private registry/signer ports。
- **合同影响：** 第 2、3、4、5 节已据此冻结 dependency authority、version/lock policy、private provisioning/test boundary、registry provisioning、typed failure precedence 与条件 write set。该决定不创建 [`requirements.txt`](../requirements.txt)，不安装依赖，不改动 runtime/tests，也不构成 implementation authorization。
- **后续 Gate：** 本修订使所有旧 R41 CONTRACT verdict 失效。唯一下一合法动作是 logical fresh、read-only independent CONTRACT review；不得实施、测试、安装依赖或执行 Git/远端/GitHub operation。

## 20. crypto-provider / registry / signer revision 后的逻辑新鲜、只读独立合同审查

- **Gate：** `CONTRACT / fresh STATIC_REVIEW`。
- **审查角色与独立性：** logical fresh Static Reviewer；重新仅审查现行第 2--5、19 节、[`engine/f09/artifacts.py`](../engine/f09/artifacts.py)、[`engine/f09/errors.py`](../engine/f09/errors.py) 及已盘点的 dependency surfaces；不采纳作者的修订评价或任何旧 `PASS` / `REVISE` verdict。
- **授权与副作用边界：** 本地只读 review；未修改 runtime/tests/dependency files，未安装依赖，未执行 Python、pytest、Git、远端或 GitHub operation。
- **直接证据与判定：** 已盘点的 repository dependency surfaces 仅有 pytest-only [`pyproject.toml`](../pyproject.toml) 与 development/test-only [`requirements-dev.txt`](../requirements-dev.txt)，不存在既有 runtime authority 或 Ed25519 provider。现行合同将新建 [`requirements.txt`](../requirements.txt) 明确为唯一 runtime authority，锁定唯一条目 `cryptography>=42.0,<46.0` 且禁止 lockfile/替代 dependency surface。它把 public-key registry 与 private signer 分别约束为一次性、module-private deployment installers：输入均在 P-1 外部由部署秘密管理层/受控配置层解析；P-1 不读 filesystem/environment/network/clock；安装成功后的 state 为 process-lifetime immutable；getter、verifier、result、R40 与 feedback 无 write capability 或私钥出口。registry 缺失、registry/input invalid、signer 缺失、signer key invalid、provider/sign execution failure 均有 exact [`F09ContractError`](../engine/f09/errors.py:29) code/path disposition，并在 proof/DTO 之前 fail closed。未来 implementation write set 精确列为 [`requirements.txt`](../requirements.txt)、[`engine/f09/artifacts.py`](../engine/f09/artifacts.py) 与 [`tests/f09/test_artifact_lifecycle.py`](../tests/f09/test_artifact_lifecycle.py)；没有要求 R40、feedback、Task 9、P-2、lockfile 或部署配置写入。
- **Falsifiers：** 若 implementation 需要 P-1 自行读取/解析秘密或 registry、可替换已安装 registry/signer、通过 public callable 导出或注入 private material、依赖未在 [`requirements.txt`](../requirements.txt) 声明、修改条件 write set 外路径，或 provider 不能提供 contract 所需 Ed25519 raw-public-key/sign/verify API，则本 verdict 必须 `REVISE`。现行合同对前四项有显式 fail-closed/STOP 条款；最后一项留给后续 authorized implementation static/dynamic verification，未被本 review 伪称已证明。
- **Verdict：** **`PASS`**。R41 现已具备唯一、完整且可实施的 crypto dependency、registry provisioning、private signer provisioning、typed failure 与测试替换边界；该 PASS 只关闭 document-level CONTRACT Gate，不证明 [`cryptography`](../requirements.txt) 已安装、任何 runtime behavior、Ed25519 interoperability、R40 implementation、Task 9/P-2 解锁或全仓正确性。
- **唯一下一合法动作：** 对 R41 开立独立的 `IMPLEMENT` admission：仅允许在冻结 write set 内创建 [`requirements.txt`](../requirements.txt)、实现 [`engine/f09/artifacts.py`](../engine/f09/artifacts.py) 及新增 [`tests/f09/test_artifact_lifecycle.py`](../tests/f09/test_artifact_lifecycle.py) 的 RED coverage；在该 admission 前不得修改、安装或运行 tests。

## 21. Runtime implementation 后的静态审查、验证与证据有界冻结

- **Gate：** `STATIC_REVIEW → VERIFY → EVIDENCE_REVIEW → FREEZE`。
- **审查边界：** 仅审查 R41 冻结 write set：[`requirements.txt`](../requirements.txt)、[`engine/f09/artifacts.py`](../engine/f09/artifacts.py) 与 [`tests/f09/test_artifact_lifecycle.py`](../tests/f09/test_artifact_lifecycle.py)。本轮表征补充只修改测试文件，没有修改 runtime、依赖声明、R40、feedback、Task 9 或 P-2，也没有执行 Git、远端或 GitHub operation。
- **逻辑新鲜静态审查：** `PASS`。runtime 保持单一 module-private registry/signer installer、module-owned immutable registry、public serializer/verifier、Ed25519 value proof 与 legacy coordinator reuse；新增 oracle 将“同进程重复 installer 必须失败且保留第一次 snapshot”与“部署发布新的 add-only immutable registry snapshot”区分为两个不同语义，没有把 rotation 实现成进程内二次安装，也没有引入 filesystem、network、environment、clock、feedback 或 learning 路径。
- **既有实现证明历史：** canonical base64url pad-bit 缺陷具有真实 `RED → GREEN` 记录；其余已实施 R41 producer/verifier/registry/signer 行为由此前 focused tests、静态边界测试和回归证据支持。不得把本节新增表征测试伪称为新的产品实现 `RED → GREEN`。
- **本轮 characterization evidence：** [`test_r41_duplicate_registry_install_preserves_installed_snapshot()`](../tests/f09/test_artifact_lifecycle.py:4963) 直接证明重复安装失败后原 snapshot object 与 key material 保留；[`test_r41_rotation_snapshot_only_adds_key_id_without_rewriting_old_key()`](../tests/f09/test_artifact_lifecycle.py:5012) 直接证明新 registry version 只新增 key ID 且旧 ACTIVE key material 不变；[`test_r41_old_active_key_proof_remains_valid_under_add_only_rotation()`](../tests/f09/test_artifact_lifecycle.py:5053) 直接证明旧 ACTIVE key 在新 snapshot 中继续验证既有 proof；参数化 [`test_r41_issuance_proof_is_value_verifiable_after_reconstruction()`](../tests/f09/test_artifact_lifecycle.py:5115) 的 clone、JCS serialize/parse reconstruction 与 direct construction 三个实例直接证明验签依赖公开值而非 Python object identity。
- **Focused verification：** `python -m pytest tests/f09/test_artifact_lifecycle.py -q -k "duplicate_registry_install_preserves_installed_snapshot or rotation_snapshot_only_adds_key_id_without_rewriting_old_key or old_active_key_proof_remains_valid_under_add_only_rotation or issuance_proof_is_value_verifiable_after_reconstruction"` 返回 `6 passed, 211 deselected`；随后 [`tests/f09/test_artifact_lifecycle.py`](../tests/f09/test_artifact_lifecycle.py) 编译检查通过。
- **完整模块验证：** `python -m pytest tests/f09/test_artifact_lifecycle.py -q` 返回 `217 passed`。
- **R40/R41 联合回归：** `python -m pytest tests/f09/test_feedback_eligibility.py tests/f09/test_artifact_lifecycle.py -q` 返回 `332 passed`。
- **静态/动态 reconciliation：** 新增四个 test declarations，其中一个参数化为三个实例，故动态净增六项；完整 artifact lifecycle 模块由 `211` 增至 `217`，联合模块由 `326` 增至 `332`，计数闭合。
- **直接证明：** 冻结合同中的 public DTO/callable、Ed25519 actual proof、canonical payload/base64url、registry/signer fail-closed、duplicate-install preservation、add-only rotation、旧 ACTIVE key continuity、value reconstruction、tamper/malformed cases、coordinator/verifier call counts、returned manifest identity、four-role closure及相关零下游副作用，在指定测试边界内有动态或静态 oracle。
- **不证明：** 本证据不外推到全仓测试、部署/秘密管理层、性能、并发初始化、跨进程配置发布、Task 9/P-2 可用性、G6 总完成或 GitHub 同步。
- **Evidence verdict：** **`PASS`**。未发现需要修改 [`engine/f09/artifacts.py`](../engine/f09/artifacts.py) 的生产缺陷；此前四类缺口已由 characterization evidence 补齐，证据与合同矩阵在当前授权边界内闭合。
- **Freeze verdict：** **`PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`**。R41 returned-carrier / provisioning seam 单元冻结；任何改变 DTO shape、signed payload、registry rotation/revocation、signer provisioning、call-order 或 side-effect boundary 的后续修改必须重新开立合同与验证 Gate。本冻结只允许总控重新评估下一独立单元，不自动解锁或证明 Task 9/P-2。