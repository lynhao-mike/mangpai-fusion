# G6 Task 8 R31 CONTRACT — Feedback Binding and Learning Eligibility Without Learning

## 0. 文档状态与治理边界

- 角色：Analyst。本文件是基于 R30 fresh review 五个 BLOCKER 的最小完整修订，不是 review verdict。
- R30 保留为失败历史；R31 自包含，不要求实现者从 R30 恢复规范。
- fresh review 接受前禁止实现、创建测试或运行测试。
- 唯一未来实现白名单：[`engine/f09/feedback.py`](../engine/f09/feedback.py) 与 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py)。
- Task 1–7 owner 冻结，不得修改 [`engine/f09/contracts.py`](../engine/f09/contracts.py)、[`engine/f09/trace.py`](../engine/f09/trace.py)、[`engine/f09/artifacts.py`](../engine/f09/artifacts.py)、[`engine/f09/canonical_json.py`](../engine/f09/canonical_json.py)、[`engine/f09/errors.py`](../engine/f09/errors.py)。
- Task 8 只计算 binding 与 eligibility；零文件 I/O、零 repository/writer/learning side effect、零系统时钟隐式读取。
- 本合同不授权 Git 或 GitHub 操作。

## 1. 权威与冲突解释

解释顺序：

1. [`PI-230 feedback/eligibility`](production-implementation-pi-230-traceability-binding.md:617) 与 [`PI-230 idempotency`](production-implementation-pi-230-traceability-binding.md:584)。
2. [`PI-300 feedback objects`](production-implementation-pi-300-one-card-vertical-slice-design.md:909) 与 [`PI-300 IdempotencyKey`](production-implementation-pi-300-one-card-vertical-slice-design.md:1174)。
3. [`PI-500 Task 8`](production-implementation-pi-500-r1-f09-implementation-plan.md:2291)。
4. 当前 owner exact shapes：[`RunTrack`](../engine/f09/contracts.py:21)、[`DigestRef`](../engine/f09/contracts.py:78)、[`DetectedIssue`](../engine/f09/contracts.py:582)、[`VersionedObjectRef`](../engine/f09/trace.py:53)、[`SnapshotRef`](../engine/f09/trace.py:65)、[`StandardStatement`](../engine/f09/trace.py:146)、[`StatementSet`](../engine/f09/trace.py:174)、[`IdempotencyKey`](../engine/f09/artifacts.py:48)、[`ArtifactRecord`](../engine/f09/artifacts.py:87)、[`ArtifactSetManifest`](../engine/f09/artifacts.py:113)、[`F09Error`](../engine/f09/errors.py:4)。
5. 对 Task 8 新 public surface、trust anchor、source payload、digest material、role graph 与测试 ledger，以本 R31 为唯一实现规格。

owner 的实际字段不得被旧计划示例改写；PI-230 的语义不变量不得被历史伪代码改写。

## 2. 冻结 owner 事实与通用规则

### 2.1 bounded JCS

所有 Task 8 canonical digest 只调用 [`bounded_jcs_sha256()`](../engine/f09/canonical_json.py:251)：

- token 精确为 `sha256` 与 `RFC8785-JCS-UTF8`，值为 lowercase 64-hex；
- 值域仅为 null、exact bool、Unicode scalar string、tuple array、字符串键 exact dict；
- 拒绝 number、list、自定义对象、非字符串键、surrogate、duplicate JSON key、BOM、cycle、mutation 与深度超过 64；
- raw bytes 只由 [`parse_bounded_jcs()`](../engine/f09/canonical_json.py:215) 解析；领域对象必须逐字段显式投影，禁止 reflection、`asdict`、`str` 或 repr。

### 2.2 exact owner materials

以下有名材料是全文唯一复用定义，dict key 的 JCS 排序由 owner canonicalizer 完成；下列字段列表定义完整成员而非 Python insertion-order 权威：

- `digest_ref_material(d)`：`algorithm, canonicalization, value`。
- `digest_binding_material(b)`：`status, digest`；`DigestMissing` 还必须含 `issue_id`，`DigestPresent` 不得含该键。
- `versioned_ref_material(r)`：`object_type, object_id, revision_id, schema_version, contract_version, digest_binding, source_locator_id, captured_at`。
- `snapshot_ref_material(r)`：`source_snapshot_id, source_type, source_locator_ids, schema_version, contract_version, content_digest, captured_at, immutability`；locator tuple 保持 owner 顺序。
- `artifact_attempt_material(a)`：`attempt_id, artifact_id, idempotency_key, attempt_number_as_decimal_string, retry_of_attempt_id, input_snapshot_refs, started_at, finished_at, outcome, observed_digest, error_class, error_message_digest`。
- `artifact_record_material(r)`：`artifact_id, artifact_role, track_as_enum_value, case_id, statement_set_id, run_id, path_locator, schema_version, expected_digest, observed_digest, state_as_enum_value, attempts, issue_ids`；attempt 与 issue tuple 保持原序。
- `standard_statement_material` 与 `statement_set_material`：按 owner dataclass 声明顺序逐字段投影；所有 nested owner objects 递归使用本节有名材料；不得包含实现私有字段。

所有声明为 set projection 的 tuple 在排序前按本合同 identity 检查 duplicate；ordered tuple 保持原序。

### 2.3 顶层与 nested failure 边界

- 顶层参数类型错误、raw JCS parse 失败、raw 顶层 exact-key 失败、required 顶层值 blank、digest token 非规范、clock port 非法、prior receipt 与 prior raw authority 不自洽：抛 typed [`F09ContractError`](../engine/f09/errors.py:29) 或 [`F09IntegrityError`](../engine/f09/errors.py:21)，无 result。
- 顶层合法后，nested ref/object 缺失、malformed/inconsistent、合法多候选、source pointer semantic missing 或 protocol target 不足：不抛；逐 item 返回 `INVALID`、`AMBIGUOUS` 或 `UNBOUND`。
- 每次 nested attribute access 前先 exact type/tag guard。禁止捕获 `AttributeError`、`KeyError`、`IndexError` 来模拟业务状态。
- source pointer 的 grammar malformed 是 nested structural `INVALID`；grammar 合法但路径不存在是 nested semantic `UNBOUND`。两者不得合并。

## 3. public surface exact shapes

本节全部新类型定义于未来 [`engine/f09/feedback.py`](../engine/f09/feedback.py)，均为 frozen dataclass、无 defaults；tuple 顺序规范；union 均为封闭 tagged union。

### 3.1 closed aliases

| 名称 | exact 值域 |
|---|---|
| `MatchRequired` | `Literal[MATCH, MISMATCH, UNKNOWN]` |
| `MatchOptional` | `Literal[MATCH, MISMATCH, NOT_APPLICABLE, UNKNOWN]` |
| `TrackSourceState` | `Literal[AVAILABLE_RESOLVED, SOURCE_MISSING, UNPARSABLE, AMBIGUOUS, INTEGRITY_FAILED]` |
| `TrackSourceReasonCode` | `Literal[TRACK_SOURCE_MISSING, TRACK_SOURCE_UNPARSABLE, TRACK_SOURCE_AMBIGUOUS, TRACK_SOURCE_INTEGRITY_FAILED]` |
| `BindingProtocol` | `Literal[PRODUCTION_STATEMENT, PREPROD_RUN_TARGET]` |
| `BindingStatus` | `Literal[BOUND, UNBOUND, AMBIGUOUS, INVALID]` |
| `EligibilityStatus` | `Literal[ELIGIBLE, INELIGIBLE, HUMAN_REVIEW]` |
| `PreprodArtifactRole` | `Literal[RUN_SNAPSHOT, DECISION_RUN, FEEDBACK_ATTACHMENT, MANIFEST]` |
| `JcsSnapshotPayload` | owner [`JcsValue`](../engine/f09/canonical_json.py:11) 的运行时值；public annotation 必须直接复用该 owner alias |

### 3.2 submission 与 binding records

| public frozen dataclass | 字段，严格按声明顺序 |
|---|---|
| `TrackSourceBinding` | `track_source_binding_id: str`; `side: Literal[SUBMISSION_SOURCE, BINDING_TARGET]`; `track: RunTrack`; `state: TrackSourceState`; `source_evidence_ref: VersionedObjectRef`; `parser_ref: VersionedObjectRef`; `schema_version: str`; `contract_version: str`; `content_digest: DigestRef`; `state_reason_codes: tuple[TrackSourceReasonCode, ...]`; `captured_at: str` |
| `FeedbackItem` | `feedback_item_id: str`; `feedback_id: str`; `source_span_locator: str`; `target_statement_id: str | None`; `target_statement_revision_id: str | None`; `target_run_id: str | None`; `target_prediction_id: str | None`; `verdict: str`; `annotation: str`; `integrity: Literal[VALID, INVALID, UNRESOLVED]`; `issue_ids: tuple[str, ...]` |
| `FeedbackSubmission` | `feedback_id: str`; `case_id: str`; `track: RunTrack`; `track_source_binding: TrackSourceBinding`; `source_snapshot_ref: SnapshotRef`; `source_snapshot_payload: JcsValue`; `parser_id: str`; `parser_version: str`; `feedback_items: tuple[FeedbackItem, ...]`; `content_digest: DigestRef`; `captured_at: str` |
| `StatementProjectionRecord` | `projection_id: str`; `projection_type: Literal[STATEMENT_INDEX, STATEMENT_RECORDS]`; `statement_set_id: str`; `statement_id: str`; `statement_revision_id: str`; `source_statement_digest: DigestRef`; `projected_object_ref: VersionedObjectRef`; `transformation_id: str`; `fidelity: Literal[LOSSLESS, PARTIAL, LOSSY, UNSUPPORTED]`; `dropped_refs: tuple[VersionedObjectRef, ...]`; `synthesized_fields: tuple[str, ...]`; `issue_ids: tuple[str, ...]` |
| `AnchorSelectionRecord` | `anchor_selection_id: str`; `statement_id: str`; `statement_revision_id: str`; `all_rule_refs: tuple[VersionedObjectRef, ...]`; `selected_anchor_rule_ref: VersionedObjectRef | None`; `non_anchor_rule_refs: tuple[VersionedObjectRef, ...]`; `selection_policy_id: str`; `selection_policy_version: str`; `source_order_digest: DigestRef`; `fidelity: Literal[LOSSY, UNSUPPORTED]`; `fanout_scope: Literal[SELECTED_ANCHOR_ONLY, NONE]`; `issue_ids: tuple[str, ...]` |
| `FeedbackBinding` | `feedback_binding_id: str`; `feedback_item_ref: VersionedObjectRef`; `binding_protocol: BindingProtocol`; `source_track_binding_ref: VersionedObjectRef`; `target_track_source_binding: TrackSourceBinding`; `case_match: MatchRequired`; `track_match: MatchRequired`; `run_match: MatchOptional`; `statement_match: MatchOptional`; `revision_match: MatchOptional`; `statement_set_match: MatchOptional`; `artifact_digest_match: MatchRequired`; `target_object_refs: tuple[VersionedObjectRef, ...]`; `record_anchor_ref: VersionedObjectRef | None`; `status: BindingStatus`; `issue_ids: tuple[str, ...]`; `detected_issues: tuple[DetectedIssue, ...]`; `content_digest: DigestRef` |

### 3.3 authority、policy 与 receipt

| public frozen dataclass | 字段，严格按声明顺序 |
|---|---|
| `GoverningVersions` | `statement_contract_version: str`; `statement_set_contract_version: str`; `statement_records_contract_version: str`; `rule_contract_version: str` |
| `RuleMetadataReceipt` | `rule_ref: VersionedObjectRef`; `family_id: str`; `school: str`; `canon: str`; `rule_type: str`; `metadata_schema_version: str`; `metadata_contract_version: str`; `source_ref: VersionedObjectRef`; `content_digest: DigestRef`; `captured_at: str` |
| `ProductionStatementAuthority` | `statement_set: StatementSet`; `manifest: ArtifactSetManifest`; `statement_refs: tuple[VersionedObjectRef, ...]`; `statement_set_ref: VersionedObjectRef`; `records_projection_refs: tuple[VersionedObjectRef, ...]`; `records_projection_records: tuple[StatementProjectionRecord, ...]`; `anchor_selections: tuple[AnchorSelectionRecord, ...]`; `rule_metadata_receipts: tuple[RuleMetadataReceipt, ...]`; `governing_versions: GoverningVersions`; `content_digest: DigestRef` |
| `PreprodRunAuthority` | `case_id: str`; `track: RunTrack`; `run_id: str`; `manifest: ArtifactSetManifest`; `target_refs: tuple[VersionedObjectRef, ...]`; `content_digest: DigestRef` |
| `EligibilityPolicy` | `policy_id: str`; `policy_version: str`; `allowed_track: RunTrack`; `required_feedback_policy: Literal[FEEDBACK_ALLOWED]`; `human_review_on_ambiguous: bool`; `human_review_on_invalid: bool`; `human_review_on_unknown_track: bool`; `schema_version: str`; `contract_version: str`; `content_digest: DigestRef` |
| `RawFeedbackAuthority` | `raw_submission: bytes`; `target_authority: ProductionStatementAuthority | PreprodRunAuthority`; `target_track_source_binding: TrackSourceBinding`; `captured_at: str` |
| `FeedbackOperationReceipt` | `operation_id: str`; `key: IdempotencyKey`; `source_digest: DigestRef`; `target_digest: DigestRef`; `aggregate_target_digest: DigestRef`; `bindings: tuple[FeedbackBinding, ...]`; `policy_ref: VersionedObjectRef`; `authority_digest: DigestRef`; `created_at: str`; `content_digest: DigestRef` |
| `PriorFeedbackOperation` | `raw_authority: RawFeedbackAuthority`; `receipt: FeedbackOperationReceipt` |

R31 删除 R30 的 public `PolicyTrustRoot` 与 `ApprovedPolicyAuthority`。policy authority 不再是 caller 输入；唯一 policy 由第 5 节模块内 pinned trust anchor 产生。

`ProductionStatementAuthority | PreprodRunAuthority` 是唯一 target authority union，以 exact dataclass 类型判别。单 call 只允许一种 protocol；冲突 item 为 nested `INVALID`。

### 3.4 operation 与 eligibility results

| public frozen dataclass | 字段，严格按声明顺序 |
|---|---|
| `ValidFeedbackOperationResult` | `valid: Literal[True]`; `operation_disposition: Literal[NEW_OPERATION, REUSED_OPERATION]`; `source_identity_relation: Literal[INITIAL, SAME, CHANGED]`; `prior_receipt: FeedbackOperationReceipt | None`; `current_receipt: FeedbackOperationReceipt`; `bindings: tuple[FeedbackBinding, ...]`; `overwrite_permitted: Literal[False]`; `detected_issues: tuple[DetectedIssue, ...]` |
| `InvalidFeedbackOperationResult` | `valid: Literal[False]`; `operation_disposition: Literal[TARGET_MISMATCH]`; `source_identity_relation: Literal[SAME]`; `prior_receipt: FeedbackOperationReceipt`; `current_key: IdempotencyKey`; `prior_target_digest: DigestRef`; `current_target_digest: DigestRef`; `aggregate_target_digest: DigestRef`; `bindings: tuple[()]`; `overwrite_permitted: Literal[False]`; `detected_issues: tuple[DetectedIssue, ...]` |
| `LearningEligibility` | `eligibility_id: str`; `feedback_binding_id: str`; `feedback_binding_digest: DigestRef`; `policy_id: str`; `policy_version: str`; `status: EligibilityStatus`; `learning_target_refs: tuple[VersionedObjectRef, ...]`; `excluded_supporting_rule_refs: tuple[VersionedObjectRef, ...]`; `blocking_reason_codes: tuple[str, ...]`; `detected_issues: tuple[DetectedIssue, ...]`; `evaluated_at: str`; `content_digest: DigestRef` |

`FeedbackOperationResult` 是上述 valid/invalid 两类的封闭 union。

### 3.5 ports 与 exact signatures

- `FeedbackClockPort`：runtime-checkable Protocol；`now() -> str`。
- `bind_feedback_operation(current: RawFeedbackAuthority, *, prior: PriorFeedbackOperation | None, clock: FeedbackClockPort) -> FeedbackOperationResult`。
- `validate_feedback_binding_record(binding: FeedbackBinding) -> None`。
- `evaluate_learning_eligibility(binding: FeedbackBinding, *, production_authority: ProductionStatementAuthority | None, clock: FeedbackClockPort) -> LearningEligibility`。
- `validate_learning_eligibility(eligibility: LearningEligibility) -> None`。

不存在 policy/trust-root 参数或可信外部 port；caller 无法提交 policy authority。

## 4. raw schema、source payload 与 RFC 6901 resolver

### 4.1 raw exact schema

`RawFeedbackAuthority.raw_submission` 必须是 bounded-JCS object，键集合精确对应第 3.2 节 `FeedbackSubmission`，包含 `source_snapshot_payload`。nested objects 精确对应各新/owner dataclass 字段。JSON array 经 [`parse_bounded_jcs()`](../engine/f09/canonical_json.py:215) 规范化为 tuple；除此之外不 coercion。缺键、额外键、非法 enum/tag 或错误 exact type 按第 2.3 节处理。

解析固定为：raw bytes → bounded JCS → top-level exact keys → nested exact keys/tags → owner/new dataclass 构造 → coherence validation。payload 必须直接来自 raw；不得从 ref、locator、annotation 或 target authority 合成。

### 4.2 snapshot payload identity

- `source_snapshot_payload` 必须是合法 [`JcsValue`](../engine/f09/canonical_json.py:11)，可为任一 bounded-JCS root 类型；不得要求 object root。
- 重算 `bounded_jcs_sha256(source_snapshot_payload)`，必须逐值等于 `source_snapshot_ref.content_digest`。
- snapshot ref 必须满足：`source_type=FEEDBACK`；schema/contract/captured_at nonblank；immutability 为 `IMMUTABLE` 或 `MUTABLE_SOURCE_CAPTURE`；source locator IDs 为无 duplicate 的 nonblank tuple。
- digest mismatch 是 nested structural integrity failure：所有 items 为 `INVALID`，不得解析 pointer。

### 4.3 locator grammar 与 normalization

`FeedbackItem.source_span_locator` 的唯一 grammar 是：

```text
source-span-locator = source-snapshot-id "#" json-pointer
json-pointer         = "" / *( "/" reference-token )
reference-token      = *( unescaped / escaped )
unescaped            = %x00-2E / %x30-7D / %x7F-D7FF / %xE000-10FFFF
escaped              = "~0" / "~1"
```

附加 exact constraints：

1. locator 必须是 exact nonblank `str` 且不含 Unicode surrogate。
2. `source-snapshot-id` 必须 nonblank，禁止 `#`，并逐值等于 `source_snapshot_ref.source_snapshot_id`。
3. 以第一个且唯一一个 `#` 分隔；多于一个 `#` 为 malformed。fragment 不做 percent-decoding；`%` 只是普通字符。
4. 空 fragment 表示 root pointer。非空 fragment 必须以 `/` 开始。
5. token 从左到右只做一次 `~1 → /`、`~0 → ~`；任何 `~` 后非 `0/1` 或 terminal `~` 为 malformed。
6. canonical re-encoding 对解码 token 逐字符执行 `~ → ~0`、`/ → ~1`，token 以 `/` 连接；`snapshot_id + # + canonical_pointer` 必须逐值等于原 locator。否则 malformed，禁止接受替代拼写。
7. dict navigation 只按 exact string key；tuple navigation token 必须为 `0` 或首字符 `1..9` 后接十进制数字，禁止 `-`、`+`、leading zero、空 token 作 tuple index。由于 bounded JCS 禁止 number，索引长度由 decimal string 与 tuple length 的字符串/安全整数比较实现，不接受超大值 coercion 异常。
8. 每一步只选择一个 dict member 或 tuple member；bounded-JCS object 不存在 duplicate key，因此合法 navigation 天生唯一。resolver 禁止 wildcard、递归 descent、key normalization、case folding、Unicode normalization或多候选搜索。

malformed grammar/index token → item `INVALID`、empty graph。grammar canonical 且某 dict key/tuple index不存在或中途命中 scalar → item `UNBOUND`、source-span missing reason、empty graph。成功必须恰好得到一个 node；node 可为 null/bool/string/tuple/dict，不要求 truthy。

## 5. caller-external pinned policy trust anchor

### 5.1 module-private frozen literals

未来 [`engine/f09/feedback.py`](../engine/f09/feedback.py) 必须定义以下 module-private exact constants；它们不是函数参数、public dataclass 字段或 caller 可覆盖 registry：

| constant | exact value |
|---|---|
| `_PINNED_POLICY_ID` | `G6-TASK8-PRODUCTION-STATEMENT-ELIGIBILITY` |
| `_PINNED_POLICY_VERSION` | `r31-v1` |
| `_PINNED_POLICY_SCHEMA_VERSION` | `eligibility-policy.r31.v1` |
| `_PINNED_POLICY_CONTRACT_VERSION` | `g6-task8-r31` |
| `_PINNED_POLICY_OBJECT_ID` | `POLICY:G6-TASK8:R31:PRODUCTION` |
| `_PINNED_POLICY_REVISION_ID` | `rev-r31-v1` |
| `_PINNED_POLICY_SOURCE_LOCATOR_ID` | `engine.f09.feedback#PINNED_POLICY_R31` |
| `_PINNED_POLICY_CAPTURED_AT` | `2026-07-22T00:00:00Z` |
| `_PINNED_ALLOWED_TRACK` | `RunTrack.PRODUCTION_DEFAULT` |
| `_PINNED_REQUIRED_FEEDBACK_POLICY` | `FEEDBACK_ALLOWED` |
| `_PINNED_HUMAN_REVIEW_ON_AMBIGUOUS` | `True` |
| `_PINNED_HUMAN_REVIEW_ON_INVALID` | `False` |
| `_PINNED_HUMAN_REVIEW_ON_UNKNOWN_TRACK` | `True` |
| `_PINNED_ROOT_ID` | `G6-TASK8-R31-TRUST-ROOT` |
| `_PINNED_ROOT_VERSION` | `r31-v1` |
| `_PINNED_ROOT_SCHEMA_VERSION` | `policy-trust-root.r31.v1` |
| `_PINNED_ROOT_CONTRACT_VERSION` | `g6-task8-r31` |
| `_PINNED_ROOT_OBJECT_ID` | `TRUST-ROOT:G6-TASK8:R31` |
| `_PINNED_ROOT_REVISION_ID` | `rev-r31-v1` |
| `_PINNED_ROOT_SOURCE_LOCATOR_ID` | `engine.f09.feedback#PINNED_POLICY_TRUST_ROOT_R31` |
| `_PINNED_ROOT_CAPTURED_AT` | `2026-07-22T00:00:00Z` |

### 5.2 exact policy, ref 与 root materials

Pinned policy material 是 exact dict：

- `policy_id, policy_version, allowed_track, required_feedback_policy, human_review_on_ambiguous, human_review_on_invalid, human_review_on_unknown_track, schema_version, contract_version`；
- 值逐一来自第 5.1 节；不含 `content_digest`。

`_PINNED_POLICY_DIGEST = bounded_jcs_sha256(policy_material)`。模块构造唯一 `EligibilityPolicy`，其 `content_digest` 等于该值。

Pinned policy ref 是 exact [`VersionedObjectRef`](../engine/f09/trace.py:53)：object type `ELIGIBILITY_POLICY`；其余 identity 使用第 5.1 节 policy constants；digest binding 恰为 `DigestPresent(PRESENT, _PINNED_POLICY_DIGEST)`。

Pinned root material 是 exact dict：

- `trust_root_id, trust_root_version, trust_root_schema_version, trust_root_contract_version`；
- `approved_policy_refs` 为只含 `versioned_ref_material(_PINNED_POLICY_REF)` 的 tuple；
- `root_object_id, root_revision_id, root_source_locator_id, root_captured_at`；
- 不含 root digest 自身。

`_PINNED_ROOT_DIGEST = bounded_jcs_sha256(root_material)`。实现不得接受 caller root，root digest 仅由 frozen literals 与 pinned policy ref 在模块内重算。

### 5.3 anti-self-signing oracle

每次 bind/evaluate 都重新由第 5.1–5.2 节 literals 构造 policy/ref/root material；不得读取 caller object、environment、filesystem、global mutable registry 或 monkeypatched authority provider。caller raw schema 不含 policy/root 字段，public signatures 不含 policy/root 参数。

机械 falsifier：测试向 raw submission、target authority或任意 extra attribute 注入另一 policy/root，或以同 ID 自洽重签不同 booleans/digest；结果必须与无注入调用逐值相同，且使用 pinned policy。若 public signature/raw keys 接受该 authority、结果 policy identity 改变、或恶意 policy 得到 `ELIGIBLE`，S10 失败。这样 caller 无法通过整体自洽重签绕过。

## 6. 每个 Task 8 digest 的 exact preimage

本节穷尽所有新对象的 `content_digest` owner；除本节外不得出现未定义 Task 8 content digest。

1. `TrackSourceBinding.content_digest`：按第 3.2 节字段顺序包含全部字段，排除 `content_digest`；refs 使用第 2.2 节材料；enum 写 value。
2. `FeedbackSubmission.content_digest`：按第 3.2 节字段顺序包含全部字段，排除 `content_digest`；payload 原值直接进入材料；items 保持 raw 原序。
3. `FeedbackBinding.content_digest`：按第 3.2 节字段顺序包含全部字段，排除 `content_digest`；`DetectedIssue` 投影为 `issue_code, field_path`；target refs 保持协议规范顺序。
4. `RuleMetadataReceipt.content_digest`：按第 3.3 节字段顺序包含全部字段，排除 `content_digest`。
5. `ProductionStatementAuthority.content_digest`：按第 3.3 节字段顺序包含全部字段，排除 `content_digest`；ordering 见第 7 节。
6. `PreprodRunAuthority.content_digest`：按第 3.3 节字段顺序包含全部字段，排除 `content_digest`；target refs 按 full identity 排序。
7. `EligibilityPolicy.content_digest`：第 5.2 节 policy material。
8. `FeedbackOperationReceipt.content_digest`：按第 3.3 节字段顺序包含全部字段，排除 `content_digest`；bindings 保持 submission item 原序，并各自包含重算后的 binding digest。
9. `LearningEligibility.content_digest`：按第 3.4 节字段顺序包含全部字段，排除 `content_digest`；`feedback_binding_digest` 必须等于重算 `FeedbackBinding.content_digest`。

`FeedbackBinding.content_digest` 是 receipt 与 eligibility 的唯一共同 binding digest owner：receipt 内 binding 自带该 digest；eligibility 的 `feedback_binding_digest` 逐值复制已重算值。不得以 binding ID、receipt digest、authority digest 或 target digest替代。

### 6.1 authority-independent digests

- `source_order_digest` material：ordered `all_rule_refs` 的 `versioned_ref_material` tuple。
- per-item Production target digest material：`protocol, statement_ref, statement_set_ref, records_ref, selected_rule_ref, selection_policy_id, selection_policy_version, recomputed_source_order_digest, selected_metadata_receipt, governing_versions`。
- per-item PREPROD target digest material：`protocol, case_id, track, run_id, role_entries`；role entries 按第 8 节 role 顺序，每项含 ref full material 与支持它的完整 artifact material。
- aggregate target digest material：按 `feedback_item_id` UTF-16 code-unit lexical order排序的 tuple，每项 `feedback_item_id, protocol, item_target_graph_digest`；duplicate item ID 在排序前为 nested `INVALID`。
- `schema_versions_digest` material：有名 tuple `submission, track_source_binding, target_authority, rule_metadata, eligibility_policy, policy_trust_root`，每项是第 3/5 节 exact schema version。
- `contract_digest` material：同名 tuple的 contract versions，另含四个 governing versions；PREPROD governing versions位置为四个 null。
- `canonical_key_digest` material：完整 [`IdempotencyKey`](../engine/f09/artifacts.py:48) 字段但排除自身，另含规范化 item identities、每 item 原始 target IDs/revisions/run/prediction IDs、pinned policy ID/version、authority digest、aggregate target digest。

每个 digest 均排除自身；S07 对上述每个 included field 做单变 sensitivity，并验证改变 excluded self placeholder 不改变结果。

## 7. Production authority：真实排序键与映射

### 7.1 tuple identities 与排序

- `statement_refs` set identity：`object_id, revision_id, schema_version, contract_version, digest_binding full material, source_locator_id, captured_at`；按该 tuple排序。
- `records_projection_refs` set identity：同一 full `versioned_ref_material`；按 `object_id, revision_id, schema_version, contract_version, digest digest-value, source_locator_id-or-empty, captured_at-or-empty` 排序。禁止引用不存在的 `artifact_id` 字段。
- `records_projection_records` set identity：`projection_id`；按 `projection_id` 排序，duplicate projection ID 为 `INVALID`。
- `anchor_selections` set identity：`statement_id, statement_revision_id`；按该 pair 排序。
- `rule_metadata_receipts` set identity：`rule_ref` full identity；按 full identity 排序。

nullable 排序统一用 tagged key：null 为 `0, empty-string`，string 为 `1, value`；digest binding 用 `status` 后接完整 digest/issue key。不得依赖 Python 对 null/string 的比较。

### 7.2 records ref/record/artifact 三方唯一映射

对目标 statement/revision：

1. 唯一 `StatementProjectionRecord` 满足 `projection_type=STATEMENT_RECORDS` 及 statement/set/revision identity。
2. 其 `projected_object_ref` 必须逐值等于唯一 `records_projection_ref`；该 ref 的 `object_type=STATEMENT_RECORDS`。
3. 该 ref 的 `object_id` 必须逐值等于唯一 retained non-superseded [`ArtifactRecord.artifact_id`](../engine/f09/artifacts.py:88)，且 record `artifact_role=STATEMENT_RECORDS`。
4. artifact 的 case/track/set/run/schema/state/expected/observed digest 按协议逐字段校验；state 恰为 `VERIFIED`，expected 与 observed 都存在且相等。
5. projection 的 `source_statement_digest` 等于 statement content digest；projected ref digest 等于 artifact observed digest；governing records contract 等于 projected ref contract。
6. 0 个合法候选为 `UNBOUND`；多个结构合法候选为 `AMBIGUOUS`；任一 supplied ref/record/artifact malformed、identity冲突或 digest冲突为 `INVALID`。

Production target refs 规范顺序恰为 `STATEMENT, STATEMENT_SET, STATEMENT_RECORDS`；selected `RULE` 单列 `record_anchor_ref`。不得以 index 替代 records。

## 8. PREPROD closed role graph

### 8.1 allowed/forbidden closed set

允许进入 PREPROD `target_refs` 的 artifact roles 闭集恰为：

1. `RUN_SNAPSHOT` — required，恰 1。
2. `DECISION_RUN` — optional，0 或 1。
3. `FEEDBACK_ATTACHMENT` — optional，0 或 1。
4. `MANIFEST` — optional，0 或 1。

owner 的 `REPORT`、`STATEMENT_INDEX`、`STATEMENT_RECORDS`、`FEEDBACK_SOURCE` 在 PREPROD target graph 中全部 forbidden。未知 role 在 owner shape 层已非法。拒绝任一 forbidden/unknown/重复或超基数 role 的唯一结果为该 item `INVALID`、七维在可独立计算处照算、`target_object_refs=()`、`record_anchor_ref=None`、无 target digest graph。

### 8.2 每角色 exact oracle

每个 supplied target ref 必须有恰一 retained non-superseded artifact record，且：

- ref `object_type` 逐值等于 artifact role；`object_id` 等于 `artifact_id`；ref schema 等于 record schema；ref digest 为 `DigestPresent` 且等于 record observed digest；
- record case/track/run 逐值等于 authority；statement_set_id 必须 null；state 恰为 `VERIFIED`；expected/observed digest 均存在且相等；
- authority manifest records 中同 role 的 retained record 基数不得超过该角色上限；superseded records只保留审计，不支持 target ref；
- target refs 规范顺序固定为 `RUN_SNAPSHOT, DECISION_RUN, FEEDBACK_ATTACHMENT, MANIFEST`，缺失 optional role 跳过；caller 顺序不同先规范化，重复 full identity 或重复 role 在排序前拒绝。

`RUN_SNAPSHOT` 唯一性同时约束 manifest retained records 和 target refs：两侧都恰一且映射同一 artifact。attachment 不能替代 snapshot。P58 的唯一 extra-role fixture 是在只有 snapshot 的合法 graph 中增加一个完整 `DECISION_RUN` ref/record，结果仍为 `BOUND`；增加第二个 `DECISION_RUN` 或任何其他 role 固定 `INVALID`。

PREPROD 不读取 production statement/set/projection/anchor/metadata；statement/revision/set 为 `NOT_APPLICABLE`，anchor 为 null。即使 `BOUND`，eligibility 仍为 `INELIGIBLE`。

## 9. common binding mechanics

`TrackSourceBinding`：resolved 时 reasons 为空；每个 failure state 恰有对应单一 reason。source side 必须 `SUBMISSION_SOURCE`、track 等于 submission；target side必须 `BINDING_TARGET`。parser ref 与 parser ID/version对齐。source ref 引用 binding 自身 ID/schema/contract/recomputed digest，而非 source evidence。只有两侧 resolved 才比较 track，否则 `UNKNOWN`。

七维先独立计算：

| 维度 | Production | PREPROD |
|---|---|---|
| case | required MATCH | required MATCH |
| track | required MATCH | required MATCH |
| run | NOT_APPLICABLE | required MATCH |
| statement | required MATCH | NOT_APPLICABLE |
| revision | required MATCH | NOT_APPLICABLE |
| statement set | required MATCH | NOT_APPLICABLE |
| artifact digest | required MATCH | required MATCH |

缺可比较事实为 `UNKNOWN`；确定不等为 `MISMATCH`；只在明确许可处使用 `NOT_APPLICABLE`。aggregate 首命中固定：

1. `INVALID`：malformed/inconsistent canonical material、item identity冲突、任一 track binding integrity failed、protocol union冲突、source locator malformed、PREPROD forbidden role；empty graph/anchor。
2. `AMBIGUOUS`：结构合法但多个合法候选或 track source ambiguous；empty graph/anchor。
3. `UNBOUND`：合法缺失、pointer missing、source missing/unparsable、required unknown/mismatch/N/A、target/anchor/metadata不足。
4. `BOUND`：所有 required MATCH、仅 permitted N/A、完整唯一 graph且无前三类事实。

不得 default BOUND；track unknown 永不 BOUND。

## 10. eligibility

Evaluator 只接受已验证 binding、可选 Production authority和 clock；policy始终由第 5 节 pinned anchor构造。

- `ELIGIBLE` 仅限 Production BOUND、track 为 pinned allowed track、statement feedback policy为 `FEEDBACK_ALLOWED`、anchor selection policy逐值等于 pinned policy、artifact/metadata/governing versions复核通过、恰一 selected RULE。
- eligible target恰为 selected anchor；exclusions 精确为 ordered non-anchor refs；recomputed binding digest 写入 `feedback_binding_digest`。
- PREPROD、Production UNBOUND、policy禁止、metadata合法缺失固定 INELIGIBLE。
- Production AMBIGUOUS固定 HUMAN_REVIEW；INVALID固定 INELIGIBLE；track unknown固定 HUMAN_REVIEW，若同时 invalid则 invalid boolean优先。这里由 pinned booleans机械决定，无 caller policy分支。
- 非 eligible target/exclusion为空，blocking reasons nonempty。
- fresh `detected_issues=()`；不复制 binding issues或转换状态为 producer issue。
- `evaluated_at=clock.now()`；eligibility digest按第 6 节重算。

## 11. idempotency 与 receipt

当前 key由 producer构造，不接受 caller key：operation固定 `BIND_FEEDBACK`；case/track/source来自重算 submission；schema/contract digest按第 6 节；Production set ID来自 authority，PREPROD为 null；feedback ID来自 submission；canonical key按第 6 节。

prior/current 必须分别从各自 raw bytes、payload、target authority以及同一 module-pinned policy独立解析与重算。禁止 current authority重算 prior，禁止信任 receipt 自报 digest。

| 分支 | exact 条件与结果 |
|---|---|
| initial | 无 prior → valid NEW/INITIAL；fresh bindings/receipt |
| changed | prior自洽且 current key不同 → valid NEW；relation只按 source digest为 CHANGED或SAME；fresh current receipt |
| reused | prior自洽；same key + same独立重算 aggregate target digest → valid REUSED/SAME；current receipt必须是 prior receipt同一对象；bindings tuple及成员逐对象 `is` prior receipt members |
| mismatch | prior自洽；same key + different独立重算 aggregate target digest → invalid TARGET_MISMATCH/SAME；empty bindings；exact `DetectedIssue(IDEMPOTENCY.DIGEST_MISMATCH, /feedback/target_digest)` |

prior receipt与prior raw不自洽抛 [`F09IntegrityError`](../engine/f09/errors.py:21)，无 result。所有分支 overwrite false。Receipt validation重算 key、source、authority、aggregate、每个 binding content digest及 receipt digest。

## 12. record validators、issues 与副作用

`validate_feedback_binding_record` 检查 exact dataclass、closed domains、tuple、canonical refs、track coherence、source locator evidence、协议维度、Production三 refs+RULE、PREPROD closed role graph/null anchor、status coherence、detected issues以及 binding digest。

`validate_learning_eligibility` 检查 exact dataclass、closed status、nonblank identity/time、binding digest token、eligible恰一 RULE/可有ordered exclusions/no reasons、非eligible无 targets/exclusions且reasons nonempty、fresh issue tuple empty以及 eligibility digest。

Task 8唯一 producer issue pairs：

- `FEEDBACK.TARGET_UNBOUND @ /feedback_bindings/0`
- `FEEDBACK.REVISION_MISMATCH @ /feedback_bindings/0/revision_match`
- `FEEDBACK.TRACK_MISMATCH @ /feedback_bindings/0/track_match`
- `IDEMPOTENCY.DIGEST_MISMATCH @ /feedback/target_digest`

状态、pointer missing、metadata缺失、role拒绝、human-review reason不自动发明 issue code。

未来 [`engine/f09/feedback.py`](../engine/f09/feedback.py) 只能导入标准库和五个冻结 owner。禁止 pathlib/filesystem/os/tempfile、network/subprocess/database/queue、tools feedback、learning repository/writer/iteration。不得调用系统时钟。

## 13. 静态测试 accounting：12 + 70 = 82

唯一测试文件为 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py)。collection必须恰为12个非参数 structural nodes加一个70-ID参数测试，共82；禁止额外 node、重复 ID或hidden generation。

### 13.1 structural nodes

| ID / exact suffix | 唯一 oracle |
|---|---|
| S01 `test_public_dataclass_shapes_are_exact` | 第3节全部public dataclass字段、顺序、annotation、frozen全等；R30 policy authority types不存在 |
| S02 `test_public_unions_aliases_and_protocol_are_closed` | aliases、union、port、四签名精确；无policy参数 |
| S03 `test_owner_types_are_reused_by_identity` | owner class与JcsValue直接复用 |
| S04 `test_malformed_top_level_raises_typed_error_without_result` | 每类 malformed top-level typed error/no result |
| S05 `test_every_nested_dereference_is_guarded` | adversarial getter在guard前不可触达；nested negative返回record |
| S06 `test_canonicalization_is_bounded_jcs_only` | token及number/list/BOM/duplicate/depth/surrogate拒绝 |
| S07 `test_all_digest_preimages_are_complete_and_sensitive` | 第6节每个included字段单变改变digest；self排除 |
| S08 `test_prior_and_current_recompute_from_independent_raw_authorities` | 两侧raw/payload/authority独立消费，交叉替换检出 |
| S09 `test_reused_returns_prior_bindings_by_identity` | receipt、tuple与成员均机械复用 |
| S10 `test_policy_trust_root_cannot_be_caller_self_signed` | 第5节pinned literals/material重算；caller注入/自洽重签不能影响结果 |
| S11 `test_no_side_effect_import_or_runtime_surface` | 禁止import、filesystem snapshot、learning monkeypatch零触达 |
| S12 `test_static_accounting_is_exactly_12_plus_70` | structural=12、IDs=P01..P70、collected=82 |

### 13.2 参数矩阵 P01–P70

所有 ID 仅由 `test_feedback_contract_matrix[Px]` 承载：

| ID | stimulus | exact oracle |
|---|---|---|
| P01 | 完整 Production authority | BOUND；六required MATCH；run N/A；三refs+RULE |
| P02 | 完整 PREPROD snapshot-only authority | BOUND；case/track/run/digest MATCH；三维N/A；无anchor |
| P03 | unknown statement ID | Production UNBOUND；statement mismatch；不可学习 |
| P04 | missing target revision | UNBOUND；revision unknown |
| P05 | old target revision | UNBOUND；revision mismatch+exact issue |
| P06 | duplicate valid statement candidates | AMBIGUOUS；empty graph |
| P07 | malformed statement ref | INVALID；empty graph；无unguarded read |
| P08 | statement digest mismatch | INVALID；empty graph |
| P09 | statement contract mismatch | INVALID；四governing versions独立 |
| P10 | set case mismatch | case mismatch；UNBOUND |
| P11 | set track mismatch | track mismatch；UNBOUND |
| P12 | set digest mismatch | INVALID；empty graph |
| P13 | set contract mismatch | INVALID |
| P14 | records artifact缺失 | UNBOUND；target-unbound issue |
| P15 | records artifact duplicate | AMBIGUOUS |
| P16 | records state非VERIFIED | UNBOUND |
| P17 | records expected digest缺失 | digest unknown；UNBOUND |
| P18 | records observed digest缺失 | digest unknown；UNBOUND |
| P19 | records expected/observed不等 | digest mismatch；UNBOUND |
| P20 | records case/track/set不等 | 对应维独立；UNBOUND |
| P21 | records ref object_id不等artifact_id或projected ref | INVALID；empty graph |
| P22 | projection type非records | INVALID |
| P23 | projection statement/revision/set不等 | INVALID |
| P24 | projection source/projected digest不等 | INVALID |
| P25 | anchor缺失 | UNBOUND；no anchor |
| P26 | anchor多候选 | AMBIGUOUS |
| P27 | UNSUPPORTED/NONE anchor | UNBOUND |
| P28 | empty all-rule refs | INVALID |
| P29 | duplicate all-rule ref | INVALID |
| P30 | selected不在all refs | INVALID |
| P31 | selected出现两次 | INVALID |
| P32 | non-anchor非原序删除selected | INVALID |
| P33 | source-order digest不等 | INVALID |
| P34 | selected type非RULE | INVALID |
| P35 | rule governing contract mismatch | INVALID |
| P36 | metadata receipt缺失 | UNBOUND；INELIGIBLE |
| P37 | metadata receipt多候选 | AMBIGUOUS；pinned policy HUMAN_REVIEW |
| P38 | metadata字段blank | INVALID |
| P39 | metadata字段UNMAPPED | UNBOUND；INELIGIBLE |
| P40 | metadata source/digest/version mismatch | INVALID |
| P41 | 双track resolved同值 | track MATCH；其他维独立 |
| P42 | 双track resolved异值 | track MISMATCH+exact issue；UNBOUND |
| P43 | source state SOURCE_MISSING | track UNKNOWN；UNBOUND |
| P44 | target state UNPARSABLE | track UNKNOWN；UNBOUND |
| P45 | 任一state AMBIGUOUS | track UNKNOWN；AMBIGUOUS |
| P46 | 任一state INTEGRITY_FAILED | track UNKNOWN；INVALID |
| P47 | resolved带reason | INVALID |
| P48 | failure reason不精确 | INVALID |
| P49 | source side/track/parser mismatch | INVALID；source binding ref不可伪造 |
| P50 | target side非BINDING_TARGET | INVALID |
| P51 | source payload digest mismatch或locator malformed/noncanonical | INVALID；resolver不运行或empty graph |
| P52 | locator canonical但pointer missing/scalar traversal | UNBOUND；与malformed分账 |
| P53 | PREPROD缺target run | UNBOUND |
| P54 | PREPROD缺或多RUN_SNAPSHOT | 缺为UNBOUND；多为INVALID；attachment不解锁 |
| P55 | PREPROD duplicate refs/role | INVALID |
| P56 | PREPROD mixed case/track/run | 各维独立；fail closed |
| P57 | PREPROD ref/record mismatch或forbidden role | INVALID；empty graph |
| P58 | PREPROD增加唯一完整DECISION_RUN | 仍BOUND；规范顺序snapshot,decision-run |
| P59 | PREPROD BOUND eligibility | INELIGIBLE；no target/exclusion |
| P60 | pinned Production policy正例 | ELIGIBLE；binding digest同owner；恰一RULE+ordered exclusions |
| P61 | statement feedback policy非allowed | INELIGIBLE |
| P62 | caller在raw/authority extra中注入自签policy | 顶层extra key拒绝或extra attribute被忽略；永不改变pinned结果 |
| P63 | monkeypatch caller authority/root provider或同ID重签 | 无provider调用；pinned material/digest/identity不变 |
| P64 | Production ambiguous binding | pinned boolean固定HUMAN_REVIEW |
| P65 | Production invalid或unknown-track | invalid固定INELIGIBLE；unknown-track非invalid固定HUMAN_REVIEW；永不ELIGIBLE |
| P66 | initial operation | valid NEW/INITIAL；fresh receipt；no overwrite |
| P67 | changed source且changed key | valid NEW/CHANGED；无mismatch issue |
| P68 | changed pinned-sensitive target revision/authority | valid NEW；identity sensitivity成立；caller不能改变policy |
| P69 | same key+same独立重算target | valid REUSED/SAME；receipt/bindings机械复用；binding digest重验 |
| P70 | same key+different独立重算target | invalid TARGET_MISMATCH；empty；exact issue；no overwrite |

P51/P52 关闭 source locator blocker；P21/P24关闭真实records映射；P54/P55/P57/P58关闭PREPROD闭集；P60/P69验证唯一binding digest owner；P62/P63与S10关闭trust boundary。参数ID仍连续且恰70。

## 14. focused selector、STOP 与 falsifiers

fresh review后唯一focused selector：`python -m pytest tests/f09/test_feedback_eligibility.py -q`，期望 `82 passed`。随后只运行：

1. `tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_h3_standard_list_schema_without_rule_ids_is_blocked_from_learning`
2. `tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_ingest_includes_v5_feedback_attachment_summary_without_unblocking_learning`
3. `tests/test_phase_a_minimal_learning_loop.py::test_statement_record_enforcement_marks_missing_as_unmapped`

期望3 passed；本 drafting gate不运行。

实施者必须STOP并返回contract review：需要修改白名单外文件；无法使用owner actual shape；需要I/O/learning/writer/caller policy；无法guard-before-dereference；需要新增状态/disposition；collection不等82；focused与exact regressions冲突。

机械 falsifiers：任一included digest字段单变不敏感；snapshot payload未重摘要；malformed/missing pointer混同；caller可重签policy；records按不存在字段排序；projection ref不能唯一映射artifact ID；PREPROD接受闭集外role或RUN_SNAPSHOT非恰一；receipt/eligibility使用不同binding digest owner；prior未独立重算；REUSED重建对象；七维由aggregate倒推；非eligible暴露target；产生I/O/learning副作用。任一命中即否证实现符合R31。

## 15. proven、unproven 与 remaining unknowns

静态合同冻结了public shapes、五个blocker闭合、所有Task 8 digest preimages、协议、失败边界、idempotency与82-case ledger。它不证明未来代码存在、测试可收集/通过、regressions通过或fresh reviewer接受；这些只由后续获授权gate的实际证据证明。

Production metadata的持久化来源仍不由Task 1–7 owner提供port；R31继续以随Production authority输入且完整重摘要的 `RuleMetadataReceipt` 作为纯内存证据。该事实不要求实现者选择常量，不阻断实现。

无其他remaining unknown。尤其 policy identity/material/digest算法、source payload/locator、Production映射键、PREPROD roles/cardinality与binding digest owner均已确定，不留实现者猜测。

---

**当前状态：等待 fresh review。本文不作任何 CONTRACT verdict。**
