# G6 Task 8 R30 CONTRACT — Feedback Binding and Learning Eligibility Without Learning

## 0. 文档状态与治理边界

- 角色：Analyst；本文件是待 fresh review 的实现合同，不是 review verdict。
- Gate：CONTRACT drafting。fresh review 通过前，禁止实现、禁止创建测试、禁止运行测试。
- 唯一后续实现白名单：[`engine/f09/feedback.py`](../engine/f09/feedback.py) 与 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py)。
- Task 1–7 owner 冻结，尤其不得修改 [`engine/f09/contracts.py`](../engine/f09/contracts.py)、[`engine/f09/trace.py`](../engine/f09/trace.py)、[`engine/f09/artifacts.py`](../engine/f09/artifacts.py)、[`engine/f09/canonical_json.py`](../engine/f09/canonical_json.py)、[`engine/f09/errors.py`](../engine/f09/errors.py)。
- 本任务只计算绑定与学习准入，不摄入学习、不更新权重、不写规则、不触发迭代、不写文件。
- 永久禁止 GitHub 服务端 mutation；本合同不授权 Git 操作。

## 1. 权威基础与解释顺序

本合同重新核对并以如下顺序解释权威材料，不从 R29 摘要恢复正文：

1. 仓库入口与状态：[`README.md`](../README.md)、[`AGENTS.md`](../AGENTS.md)、[`META/project-state.json`](../META/project-state.json)。
2. 规范语义：[`PI-230 feedback binding`](production-implementation-pi-230-traceability-binding.md:617)、[`PI-230 idempotency`](production-implementation-pi-230-traceability-binding.md:584)、[`PI-230 anchor selection`](production-implementation-pi-230-traceability-binding.md:455)、[`PI-230 track split`](production-implementation-pi-230-traceability-binding.md:777)。
3. 垂直切片：[`PI-300 Feedback binding`](production-implementation-pi-300-one-card-vertical-slice-design.md:337)、[`PI-300 Learning eligibility`](production-implementation-pi-300-one-card-vertical-slice-design.md:353)、[`PI-300 IdempotencyKey`](production-implementation-pi-300-one-card-vertical-slice-design.md:1174)。
4. Task 范围与回归：[`PI-500 Task 8`](production-implementation-pi-500-r1-f09-implementation-plan.md:2291)。历史 remediation 只用于发现风险，不覆盖本 R30 的闭合定义。
5. 运行时 shape 以当前 owner 为准：[`RunTrack`](../engine/f09/contracts.py:21)、[`DigestRef`](../engine/f09/contracts.py:78)、[`DetectedIssue`](../engine/f09/contracts.py:582)、[`VersionedObjectRef`](../engine/f09/trace.py:53)、[`SnapshotRef`](../engine/f09/trace.py:65)、[`StandardStatement`](../engine/f09/trace.py:146)、[`StatementSet`](../engine/f09/trace.py:174)、[`IdempotencyKey`](../engine/f09/artifacts.py:48)、[`ArtifactRecord`](../engine/f09/artifacts.py:87)、[`ArtifactSetManifest`](../engine/f09/artifacts.py:113) 与 [`F09Error`](../engine/f09/errors.py:4)。

冲突解释规则：owner 的实际字段 shape 不得由计划中的旧示例改写；PI-230 的语义不变量不得由 PI-500 历史示例中的硬编码 policy 或不完整 canonicalization 改写；R30 对 Task 8 新 public surface 的定义是本任务唯一实现规格。

## 2. 固定 owner 事实

### 2.1 摘要与 canonicalization

所有 Task 8 canonical digest 必须由 [`bounded_jcs_sha256()`](../engine/f09/canonical_json.py:251) 产生：

- `algorithm` 精确为小写 `sha256`；
- `canonicalization` 精确为 `RFC8785-JCS-UTF8`；
- `value` 为小写 64-hex；
- 只允许 `null`、exact boolean、Unicode scalar string、tuple array、字符串键 dict；
- 拒绝数字、list、自定义对象、非字符串键、孤立 surrogate、重复 JSON key、BOM、cycle、mutation 与超过 64 层；
- raw bytes 先经 [`parse_bounded_jcs()`](../engine/f09/canonical_json.py:215)，领域对象到摘要材料必须显式投影为 bounded JCS，不允许通用反射或 `str()`。

### 2.2 实际 artifact 字段

每次 artifact 核对必须使用 [`ArtifactRecord`](../engine/f09/artifacts.py:87) 的真实字段：`artifact_id`、`artifact_role`、`track`、`case_id`、`statement_set_id`、`run_id`、`path_locator`、`schema_version`、`expected_digest`、`observed_digest`、`state`、`attempts`、`issue_ids`。不得以 manifest digest、文件存在、role 名或 caller 声明替代这些字段的逐项核对。

### 2.3 顶层错误边界

唯一边界如下：

- 顶层参数不是合同规定的类型、raw JCS 无法解析、tuple/mapping/union tag 非法、required 顶层值为空、摘要 token 非规范、authority/receipt 顶层 shape 非法：抛出 [`F09ContractError`](../engine/f09/errors.py:29) 或 [`F09IntegrityError`](../engine/f09/errors.py:21)，不返回 operation result。
- 顶层 shape 合法后，嵌套对象缺失、identity/version/digest 不一致、合法多候选、来源缺失、协议 required target 缺失：不得抛出；必须返回 typed invalid/non-bound operation result，其中每个 item 形成 `INVALID`、`AMBIGUOUS` 或 `UNBOUND` binding。
- 所有嵌套属性访问前必须先完成 tag/type guard；禁止通过捕获 `AttributeError`、`KeyError`、`IndexError` 将未 guard dereference 转成业务状态。

## 3. Task 8 public surface：exact shape

以下类型全部定义在未来 [`engine/f09/feedback.py`](../engine/f09/feedback.py)，均为 frozen dataclass；tuple 顺序是规范顺序；所有 union 为封闭 tagged union；不得增加默认值、可选字段、隐式 coercion 或竞争类型。

### 3.1 closed aliases

| 名称 | 精确值域 |
|---|---|
| `MatchRequired` | `Literal[MATCH, MISMATCH, UNKNOWN]` |
| `MatchOptional` | `Literal[MATCH, MISMATCH, NOT_APPLICABLE, UNKNOWN]` |
| `TrackSourceState` | `Literal[AVAILABLE_RESOLVED, SOURCE_MISSING, UNPARSABLE, AMBIGUOUS, INTEGRITY_FAILED]` |
| `TrackSourceReasonCode` | `Literal[TRACK_SOURCE_MISSING, TRACK_SOURCE_UNPARSABLE, TRACK_SOURCE_AMBIGUOUS, TRACK_SOURCE_INTEGRITY_FAILED]` |
| `BindingProtocol` | `Literal[PRODUCTION_STATEMENT, PREPROD_RUN_TARGET]` |
| `BindingStatus` | `Literal[BOUND, UNBOUND, AMBIGUOUS, INVALID]` |
| `EligibilityStatus` | `Literal[ELIGIBLE, INELIGIBLE, HUMAN_REVIEW]` |

### 3.2 submission 与 binding records

| public dataclass | 字段，严格按声明顺序 |
|---|---|
| `TrackSourceBinding` | `track_source_binding_id: str`; `side: Literal[SUBMISSION_SOURCE, BINDING_TARGET]`; `track: RunTrack`; `state: TrackSourceState`; `source_evidence_ref: VersionedObjectRef`; `parser_ref: VersionedObjectRef`; `schema_version: str`; `contract_version: str`; `content_digest: DigestRef`; `state_reason_codes: tuple[TrackSourceReasonCode, ...]`; `captured_at: str` |
| `FeedbackItem` | `feedback_item_id: str`; `feedback_id: str`; `source_span_locator: str`; `target_statement_id: str | None`; `target_statement_revision_id: str | None`; `target_run_id: str | None`; `target_prediction_id: str | None`; `verdict: str`; `annotation: str`; `integrity: Literal[VALID, INVALID, UNRESOLVED]`; `issue_ids: tuple[str, ...]` |
| `FeedbackSubmission` | `feedback_id: str`; `case_id: str`; `track: RunTrack`; `track_source_binding: TrackSourceBinding`; `source_snapshot_ref: SnapshotRef`; `parser_id: str`; `parser_version: str`; `feedback_items: tuple[FeedbackItem, ...]`; `content_digest: DigestRef`; `captured_at: str` |
| `StatementProjectionRecord` | `projection_id: str`; `projection_type: Literal[STATEMENT_INDEX, STATEMENT_RECORDS]`; `statement_set_id: str`; `statement_id: str`; `statement_revision_id: str`; `source_statement_digest: DigestRef`; `projected_object_ref: VersionedObjectRef`; `transformation_id: str`; `fidelity: Literal[LOSSLESS, PARTIAL, LOSSY, UNSUPPORTED]`; `dropped_refs: tuple[VersionedObjectRef, ...]`; `synthesized_fields: tuple[str, ...]`; `issue_ids: tuple[str, ...]` |
| `AnchorSelectionRecord` | `anchor_selection_id: str`; `statement_id: str`; `statement_revision_id: str`; `all_rule_refs: tuple[VersionedObjectRef, ...]`; `selected_anchor_rule_ref: VersionedObjectRef | None`; `non_anchor_rule_refs: tuple[VersionedObjectRef, ...]`; `selection_policy_id: str`; `selection_policy_version: str`; `source_order_digest: DigestRef`; `fidelity: Literal[LOSSY, UNSUPPORTED]`; `fanout_scope: Literal[SELECTED_ANCHOR_ONLY, NONE]`; `issue_ids: tuple[str, ...]` |
| `FeedbackBinding` | `feedback_binding_id: str`; `feedback_item_ref: VersionedObjectRef`; `binding_protocol: BindingProtocol`; `source_track_binding_ref: VersionedObjectRef`; `target_track_source_binding: TrackSourceBinding`; `case_match: MatchRequired`; `track_match: MatchRequired`; `run_match: MatchOptional`; `statement_match: MatchOptional`; `revision_match: MatchOptional`; `statement_set_match: MatchOptional`; `artifact_digest_match: MatchRequired`; `target_object_refs: tuple[VersionedObjectRef, ...]`; `record_anchor_ref: VersionedObjectRef | None`; `status: BindingStatus`; `issue_ids: tuple[str, ...]`; `detected_issues: tuple[DetectedIssue, ...]` |

### 3.3 authority、receipt 与 policy types

| public dataclass | 字段，严格按声明顺序 |
|---|---|
| `GoverningVersions` | `statement_contract_version: str`; `statement_set_contract_version: str`; `statement_records_contract_version: str`; `rule_contract_version: str` |
| `RuleMetadataReceipt` | `rule_ref: VersionedObjectRef`; `family_id: str`; `school: str`; `canon: str`; `rule_type: str`; `metadata_schema_version: str`; `metadata_contract_version: str`; `source_ref: VersionedObjectRef`; `content_digest: DigestRef`; `captured_at: str` |
| `ProductionStatementAuthority` | `statement_set: StatementSet`; `manifest: ArtifactSetManifest`; `statement_refs: tuple[VersionedObjectRef, ...]`; `statement_set_ref: VersionedObjectRef`; `records_projection_refs: tuple[VersionedObjectRef, ...]`; `records_projection_records: tuple[StatementProjectionRecord, ...]`; `anchor_selections: tuple[AnchorSelectionRecord, ...]`; `rule_metadata_receipts: tuple[RuleMetadataReceipt, ...]`; `governing_versions: GoverningVersions`; `content_digest: DigestRef` |
| `PreprodRunAuthority` | `case_id: str`; `track: RunTrack`; `run_id: str`; `manifest: ArtifactSetManifest`; `target_refs: tuple[VersionedObjectRef, ...]`; `content_digest: DigestRef` |
| `EligibilityPolicy` | `policy_id: str`; `policy_version: str`; `allowed_track: RunTrack`; `required_feedback_policy: Literal[FEEDBACK_ALLOWED]`; `human_review_on_ambiguous: bool`; `human_review_on_invalid: bool`; `human_review_on_unknown_track: bool`; `content_digest: DigestRef` |
| `PolicyTrustRoot` | `trust_root_id: str`; `trust_root_version: str`; `approved_policy_refs: tuple[VersionedObjectRef, ...]`; `content_digest: DigestRef` |
| `ApprovedPolicyAuthority` | `policy: EligibilityPolicy`; `policy_ref: VersionedObjectRef`; `trust_root: PolicyTrustRoot`; `trust_root_ref: VersionedObjectRef`; `content_digest: DigestRef` |
| `RawFeedbackAuthority` | `raw_submission: bytes`; `target_authority: ProductionStatementAuthority | PreprodRunAuthority`; `target_track_source_binding: TrackSourceBinding`; `policy_authority: ApprovedPolicyAuthority`; `captured_at: str` |
| `FeedbackOperationReceipt` | `operation_id: str`; `key: IdempotencyKey`; `source_digest: DigestRef`; `target_digest: DigestRef`; `aggregate_target_digest: DigestRef`; `bindings: tuple[FeedbackBinding, ...]`; `policy_ref: VersionedObjectRef`; `authority_digest: DigestRef`; `created_at: str`; `content_digest: DigestRef` |
| `PriorFeedbackOperation` | `raw_authority: RawFeedbackAuthority`; `receipt: FeedbackOperationReceipt` |

`ProductionStatementAuthority | PreprodRunAuthority` 是唯一 target authority union。tag 由具体 dataclass 类型决定，不读取 item 字段猜测 authority 类型。一个 call 只能提供一种协议 authority；submission 内所有 items 必须与该协议一致，否则各冲突 item 为 `INVALID`。

### 3.4 operation 与 eligibility result union

| public dataclass | 字段，严格按声明顺序 |
|---|---|
| `ValidFeedbackOperationResult` | `valid: Literal[True]`; `operation_disposition: Literal[NEW_OPERATION, REUSED_OPERATION]`; `source_identity_relation: Literal[INITIAL, SAME, CHANGED]`; `prior_receipt: FeedbackOperationReceipt | None`; `current_receipt: FeedbackOperationReceipt`; `bindings: tuple[FeedbackBinding, ...]`; `overwrite_permitted: Literal[False]`; `detected_issues: tuple[DetectedIssue, ...]` |
| `InvalidFeedbackOperationResult` | `valid: Literal[False]`; `operation_disposition: Literal[TARGET_MISMATCH]`; `source_identity_relation: Literal[SAME]`; `prior_receipt: FeedbackOperationReceipt`; `current_key: IdempotencyKey`; `prior_target_digest: DigestRef`; `current_target_digest: DigestRef`; `aggregate_target_digest: DigestRef`; `bindings: tuple[()]`; `overwrite_permitted: Literal[False]`; `detected_issues: tuple[DetectedIssue, ...]` |
| `LearningEligibility` | `eligibility_id: str`; `feedback_binding_id: str`; `policy_id: str`; `policy_version: str`; `status: EligibilityStatus`; `learning_target_refs: tuple[VersionedObjectRef, ...]`; `excluded_supporting_rule_refs: tuple[VersionedObjectRef, ...]`; `blocking_reason_codes: tuple[str, ...]`; `detected_issues: tuple[DetectedIssue, ...]`; `evaluated_at: str` |

`FeedbackOperationResult` 是 `ValidFeedbackOperationResult | InvalidFeedbackOperationResult` 的封闭 union。不得保留旧的单一 result shape，不得添加第四 disposition。

### 3.5 read-only ports 与函数签名

| public surface | exact signature/职责 |
|---|---|
| `FeedbackClockPort` | runtime-checkable Protocol；`now() -> str`；只读时间源，不得隐式调用系统时钟 |
| `bind_feedback_operation` | `bind_feedback_operation(current: RawFeedbackAuthority, *, prior: PriorFeedbackOperation | None, clock: FeedbackClockPort) -> FeedbackOperationResult` |
| `validate_feedback_binding_record` | `validate_feedback_binding_record(binding: FeedbackBinding) -> None`；仅 shape/coherence validator |
| `evaluate_learning_eligibility` | `evaluate_learning_eligibility(binding: FeedbackBinding, *, production_authority: ProductionStatementAuthority | None, policy_authority: ApprovedPolicyAuthority, clock: FeedbackClockPort) -> LearningEligibility` |
| `validate_learning_eligibility` | `validate_learning_eligibility(eligibility: LearningEligibility) -> None` |

禁止 filesystem/repository/writer/learning port；Task 8 没有 mutation port。

## 4. raw submission 与 canonical preimages

### 4.1 raw submission schema

[`RawFeedbackAuthority`](../engine/f09/feedback.py:1) 的 `raw_submission` 必须是 bounded JCS object，且键集合精确对应 `FeedbackSubmission`，nested object 精确对应 `TrackSourceBinding`、`FeedbackItem`、`SnapshotRef`、`VersionedObjectRef`、`DigestPresent`/`DigestMissing` 与 `DigestRef` 的 owner 字段。拒绝缺键、额外键、数字、错误 enum、list 替代 tuple 语义、隐式默认与字符串 coercion。

解析顺序固定：raw bytes → bounded JCS → 顶层 exact-key guard → nested exact-key/tag guard → owner/new dataclass 构造 → dataclass coherence validation。任何 nested dereference 只能发生在对应 validated tagged value 产生之后。

### 4.2 reusable canonical materials

- `digest_ref_material`：`algorithm, canonicalization, value`。
- `digest_binding_material`：`status, digest`；`MISSING` 还包括 `issue_id`。
- `versioned_ref_material`：按 owner 顺序完整包含 `object_type, object_id, revision_id, schema_version, contract_version, digest_binding, source_locator_id, captured_at`。
- `artifact_record_material`：完整包含第 2.2 节列出的全部字段；attempt 也按 [`ArtifactWriteAttempt`](../engine/f09/artifacts.py:71) 完整投影。
- 所有 map 先转换成按 authority key 规定排序的 tuple；所有 authority-defined ordered tuple 保持原序；duplicate identity 在排序前拒绝。

### 4.3 submission digest

`FeedbackSubmission.content_digest` 的 preimage 是完整 submission，排除自身 `content_digest`；字段按第 3.2 节顺序，items 保持 raw 原序。`source_snapshot_ref.content_digest` 是 feedback source digest，二者不可互换。

### 4.4 authority digest

- Production authority preimage 包含完整 statement set、manifest、全部 refs、projection records、anchor selections、metadata receipts、四 governing versions；按各 tuple 的 authority identity 排序：statement refs 按 `object_id, revision_id`，records refs/records 按 `artifact_id`，selections 按 `statement_id, statement_revision_id`，metadata receipts 按 rule ref full identity。任何 duplicate 先判 invalid。
- PREPROD authority preimage 包含 `case_id, track, run_id, manifest` 与 target refs；target refs 按 full identity 排序。
- authority 的 `content_digest` 必须由上述 preimage 重算，不可信任 caller 给值。

### 4.5 target graph digest

Production target graph preimage：

1. `protocol=PRODUCTION_STATEMENT`；
2. canonical statement ref；
3. canonical statement-set ref；
4. canonical statement-records ref；
5. selected `RULE` ref；
6. selection policy ID/version；
7. recomputed ordered `all_rule_refs` source-order digest；
8. selected rule metadata receipt 的完整 identity/digest；
9. 四 governing versions。

PREPROD target graph preimage：

1. `protocol=PREPROD_RUN_TARGET`；
2. validated `case_id, track, run_id`；
3. nonempty extensible validated run-artifact refs，按 full identity 排序；
4. 每个 ref 对应完整 artifact record identity、expected/observed digest 与 state。

每 item 独立产生 target graph digest。operation `aggregate_target_digest` 的 preimage 是按 `feedback_item_id` 排序的 tuple：`feedback_item_id, protocol, item_target_graph_digest`。duplicate item ID 为 nested semantic `INVALID`，不得被排序掩盖。

### 4.6 canonical idempotency key

当前 key 必须由实现构造，不接受 caller-supplied key。其字段：

- `operation=BIND_FEEDBACK`；
- `case_id, track` 来自重算后的 submission；
- `source_digest=source_snapshot_ref.content_digest`；
- `schema_versions_digest` preimage 是 submission、track binding、target authority、metadata、policy、trust-root schema versions 的有名 tuple；
- `contract_digest` preimage 是 submission、target authority、policy、trust-root contract versions 及四 governing versions 的有名 tuple；
- Production `statement_set_id` 为 authority set ID；PREPROD 为 null；
- `feedback_id` 为 submission ID；
- `canonical_key_digest` preimage 完整包含上述字段，加规范化 item identities、每 item 原始 target IDs/revisions/run/prediction IDs、policy ID/version、authority digest 与 aggregate target digest，但排除 `canonical_key_digest` 自身。

任一 source、item set、item target revision、policy version、authority、governing version 或 target graph 变化都必须改变 key 或 target digest，不能沿用旧 operation identity。

### 4.7 receipt digest

Receipt `content_digest` preimage 是 receipt 全部字段但排除自身；bindings 按 submission item 原序。Receipt validation 必须重算 key、source digest、authority digest、每个 binding 与 target aggregate；不得只比较 receipt 自带摘要。

## 5. authority 与信任根规则

### 5.1 policy

Policy 必须来自独立 [`PolicyTrustRoot`](../engine/f09/feedback.py:1)：

- trust-root ref 必须精确引用 trust-root object/digest；
- policy ref 必须存在于 `approved_policy_refs` 且 full identity 唯一匹配；
- policy ref digest 必须等于重算 policy digest；
- approved authority digest 必须重算；
- caller 不能把任意 policy 与包含该 policy 的临时 trust root 一并自签：trust-root ref 的 digest binding 必须由独立 frozen `ApprovedPolicyAuthority` 输入核对，并且 policy ref 与 trust-root ref 不得共享 object identity、source locator 或 content digest。

本合同不硬编码 `PRODUCTION-STATEMENT-ELIGIBILITY/policy-v1`。实际值由 approved authority 提供；anchor selection 的 policy ID/version 必须逐值等于 approved policy。

### 5.2 metadata

Production `family_id`、`school`、`canon`、`rule_type` 只来自 [`RuleMetadataReceipt`](../engine/f09/feedback.py:1)，禁止从 feedback、自由文本、rule ID 命名、index 或 anchor selection 推断。正例必须满足：

- receipt `rule_ref` full identity 等于 selected anchor；
-四 metadata 字段均为 nonblank 且不等于 `UNMAPPED`；
- receipt source ref、schema、contract、digest、captured time 完整；
- receipt digest 重算一致；
- selected anchor 只有一个 matching receipt；0 个为 `UNBOUND`，多个合法候选为 `AMBIGUOUS`，malformed/inconsistent receipt 为 `INVALID`。

### 5.3 四 governing versions

四个版本逐一控制 statement、statement set、statement records、rule ref/metadata。它们都必须 nonblank，并分别与实际 ref 的 `contract_version` 相等；不得用一个 global version 替代，不得由 ref 反向选择 governing version。

## 6. protocol mechanics

### 6.1 common guards

每 item 独立执行：验证 submission/item identity、source span 可定位于 source snapshot、source track binding、target track binding、authority、policy authority、receipt（如有），再进入 protocol branch。guard 失败后不得继续读取失败对象的 nested field。

`TrackSourceBinding` 规则：

- `AVAILABLE_RESOLVED` 必须 reasons 为空；
- 四失败 state 必须恰有对应单一 reason；
- source side 必须为 `SUBMISSION_SOURCE` 且 track 等于 submission track；target side 必须为 `BINDING_TARGET`；
- parser ref 必须与 submission parser ID/version 对齐；
- source binding ref 引用 binding 自身 ID/schema/contract/digest，不引用 source evidence 代替；
- 两侧都 `AVAILABLE_RESOLVED` 才比较 track，否则 `track_match=UNKNOWN`。

### 6.2 Production protocol

仅 [`ProductionStatementAuthority`](../engine/f09/feedback.py:1) 可进入。必须唯一解析：

- statement：ID/revision/case/track/set membership/content digest/statement feedback policy；
- statement set：ID/case/track/schema/digest；
-唯一非 superseded `STATEMENT_RECORDS` artifact：`track, case_id, statement_set_id` 一致，`run_id` 按 authority 实值核对而非忽略，state 为 `VERIFIED`，expected/observed digest 均存在且相等；
- records ref 与 projection record：artifact ID、statement ID/revision/set、source statement digest、projected ref、governing contract 均一致；
- anchor selection：`fidelity=LOSSY`、`fanout_scope=SELECTED_ANCHOR_ONLY`、ordered `all_rule_refs` nonempty 且无 duplicate、selected 出现恰一次、`non_anchor_rule_refs` 精确等于删除 selected 后的原序列、source-order digest 重算一致；
- selected anchor 是唯一 `RULE` learning target，其他合法规则仅成为 exclusions；
- selected metadata receipt 完整；
- manifest 必须 `COMPLETE_VERIFIED`，但该状态不替代 records 的逐字段检查。

Production target refs 的规范顺序恰为 `STATEMENT, STATEMENT_SET, STATEMENT_RECORDS`；anchor 单列于 `record_anchor_ref`。不得用 index 替代 records。`run_match` 唯一合法正值为 `NOT_APPLICABLE`。

### 6.3 PREPROD protocol

仅 [`PreprodRunAuthority`](../engine/f09/feedback.py:1) 可进入。它是 run-only：

- item 必须有 `target_run_id`，不得有 statement ID/revision；prediction ID 可作为附加 audit target，但不能替代 run；
- authority records 必须形成同一 `case_id, track, run_id` 的非空 graph；
- 必须有唯一可用 `RUN_SNAPSHOT` ref/record；
-每个 target ref 都须由 retained non-superseded artifact record 支持，object type/ID 对应 role/artifact ID，case/track/run/schema/digest/state 一致；
- graph 可包含额外合法 run-related refs，不固定为三元组；duplicate、mixed case/track/run、缺 snapshot 或 digest disagreement 均 fail closed；
-不得读取 production statement/set/projection/anchor/metadata；`record_anchor_ref=None`；statement/revision/set 三维为 `NOT_APPLICABLE`；
- PREPROD binding 即使 `BOUND`，本 Task 8 production eligibility 仍为 `INELIGIBLE`，不得跨轨解锁。

## 7. 七维独立计算与 aggregate precedence

七维必须全部先独立计算，不能从 aggregate status 倒推：

| 维度 | Production | PREPROD |
|---|---|---|
| case | required `MATCH` | required `MATCH` |
| track | required `MATCH` | required `MATCH` |
| run | `NOT_APPLICABLE` | required `MATCH` |
| statement | required `MATCH` | `NOT_APPLICABLE` |
| revision | required `MATCH` | `NOT_APPLICABLE` |
| statement set | required `MATCH` | `NOT_APPLICABLE` |
| artifact digest | required `MATCH` | required `MATCH` |

每维缺少可比较的合法事实为 `UNKNOWN`，确定不等为 `MISMATCH`，只在协议明确允许时使用 `NOT_APPLICABLE`。required 维使用 `NOT_APPLICABLE` 固定导致 `UNBOUND`。

aggregate 首命中优先级固定：

1. `INVALID`：canonical material malformed/inconsistent、item identity 不一致、任一 track binding `INTEGRITY_FAILED`、协议 union 冲突、legacy required binding 缺失；target graph 清空、anchor 清空。
2. `AMBIGUOUS`：结构和完整性合法，但存在多个合法候选，或任一 track binding `AMBIGUOUS`；target graph 清空、anchor 清空。
3. `UNBOUND`：合法缺失、`SOURCE_MISSING`、`UNPARSABLE`、required `UNKNOWN/MISMATCH/NOT_APPLICABLE`、required target/anchor/metadata 不足；target graph 只在完整、唯一且协议一致时保留，否则清空。
4. `BOUND`：所有 required 维为 `MATCH`、仅 permitted 维为 `NOT_APPLICABLE`、完整 target graph/anchor 条件成立、无前三类事实。

不得 default `BOUND`。`track_match=UNKNOWN` 永不 `BOUND`。

## 8. eligibility mechanics

Eligibility 只接受一个已验证 binding 与独立 approved policy authority：

- `ELIGIBLE` 仅限 Production `BOUND`，track 为 policy `allowed_track`，statement `feedback_policy=FEEDBACK_ALLOWED`，policy/anchor selection一致，artifact/metadata/四版本复核通过，且恰有一个 selected `RULE` target。
- `learning_target_refs` 对 `ELIGIBLE` 恰为 selected anchor；`excluded_supporting_rule_refs` 精确为 anchor selection 的 non-anchor refs，保持原序。
- PREPROD、Production `UNBOUND`、policy 禁止、feedback policy 非 allowed、合法 metadata 缺失固定 `INELIGIBLE`。
- Production `AMBIGUOUS`、`INVALID`、`track_match=UNKNOWN` 按 approved policy 的三个 boolean 分别选择 `HUMAN_REVIEW` 或 `INELIGIBLE`；三态不得折叠。
- 非 `ELIGIBLE` 的 targets 与 exclusions 均为空，并有 nonempty blocking reasons。
- fresh eligibility 的 `detected_issues=()`；不得把 binding status、dimension、reason、`issue_ids` 或已有 issue tuple 转换/复制成 producer issue pair。
- `evaluated_at=clock.now()`；identity preimage 包含 binding ID/digest、policy full identity、四 governing versions与 evaluated timestamp。

## 9. idempotency 四分支与机械 reuse

prior/current 均必须从各自 `RawFeedbackAuthority.raw_submission` 和各自 actual target/policy authority独立解析、重算；禁止拿 current authority 重算 prior，禁止信任 prior receipt 自报 key/digest。

| 分支 | 条件 | 唯一结果 |
|---|---|---|
| A initial | 无 prior | valid `NEW_OPERATION`, relation `INITIAL`, current fresh bindings/receipt |
| B changed | prior 自洽；current canonical key 不同 | valid `NEW_OPERATION`, relation 按 source digest 为 `CHANGED` 或 `SAME`, current fresh bindings/receipt；旧 receipt 仅审计 |
| C reused | prior 自洽；same key + same independently recomputed aggregate target digest | valid `REUSED_OPERATION`, relation `SAME`；`bindings` 必须逐对象机械返回 `prior.receipt.bindings`，不得重建、重排或以 current fresh bindings 替换；current receipt 即 prior receipt |
| D mismatch | prior 自洽；same key + different independently recomputed aggregate target digest | invalid `TARGET_MISMATCH`, relation `SAME`, empty bindings, exact `DetectedIssue(IDEMPOTENCY.DIGEST_MISMATCH, /feedback/target_digest)`, no overwrite |

prior receipt 与 prior raw authority 不一致属于 nested authority invalid：抛出 [`F09IntegrityError`](../engine/f09/errors.py:21) 且不返回 result，因为 operation comparison 的可信前提不存在。任何分支 `overwrite_permitted=False`。

## 10. record validators

[`validate_feedback_binding_record`](../engine/f09/feedback.py:1) 必须检查：exact dataclass；所有 closed domains；tuple shapes；canonical refs；source/target track-binding coherence；协议 permitted/required dimensions；Production target order/cardinality 与 `RULE` anchor；PREPROD nonempty extensible graph与 null anchor；`BOUND` exact dimension tuple；非 BOUND 不得伪装完整学习 graph；detected issue tuple shape。

[`validate_learning_eligibility`](../engine/f09/feedback.py:1) 必须检查：exact dataclass；closed status；nonblank identities/time；tuple shapes；`ELIGIBLE` 恰一 `RULE` target、允许有 ordered exclusions、无 blocking reasons；非 eligible 无 targets/exclusions且有 reasons；fresh detected issues 为空。

validator 只验证 record，不访问 filesystem、authority source 或 learning components。

## 11. producer-owned issue boundary

Task 8 仅生产以下 exact pairs：

- target graph 合法缺失：`FEEDBACK.TARGET_UNBOUND @ /feedback_bindings/0`；
- revision 确定 mismatch：`FEEDBACK.REVISION_MISMATCH @ /feedback_bindings/0/revision_match`；
- track 确定 mismatch：`FEEDBACK.TRACK_MISMATCH @ /feedback_bindings/0/track_match`；
- same-key target mismatch：`IDEMPOTENCY.DIGEST_MISMATCH @ /feedback/target_digest`。

状态、维度、metadata 缺失、human-review reason 不自动映射成新 issue pair。未在 owner registry 证明存在的 code 不得发明。

## 12. 零副作用与 import 边界

未来 [`engine/f09/feedback.py`](../engine/f09/feedback.py) 可以导入 Python 标准库，以及冻结 owner：[`engine/f09/contracts.py`](../engine/f09/contracts.py)、[`engine/f09/trace.py`](../engine/f09/trace.py)、[`engine/f09/artifacts.py`](../engine/f09/artifacts.py)、[`engine/f09/canonical_json.py`](../engine/f09/canonical_json.py)、[`engine/f09/errors.py`](../engine/f09/errors.py)。

禁止导入 `tools.feedback_ingest`、minimal learning loop、weight repository、rule writer、iteration trigger、filesystem/pathlib/tempfile/os、network/subprocess/database/queue。binder/evaluator 不打开文件、不写 manifest、不修改 artifact、不调用 learning、不更新计数。

## 13. 静态测试 accounting：12 structural + 70 parameter IDs = 82

唯一测试文件：[`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py)。收集结果必须恰为 82：12 个非参数 structural node + 一个 70-ID 参数测试；不得用 hidden dynamic generation、重复 ID 或额外 node 改变总数。

### 13.1 12 structural tests

| ID / exact node suffix | 唯一 oracle |
|---|---|
| S01 `test_public_dataclass_shapes_are_exact` | 第 3 节所有 public dataclass 字段名、顺序、annotation、frozen 全等 |
| S02 `test_public_unions_aliases_and_protocol_are_closed` | aliases、union、port、四个 public function signatures 精确 |
| S03 `test_owner_types_are_reused_by_identity` | owner class identity 使用 `is`，无本地复制 |
| S04 `test_malformed_top_level_raises_typed_error_without_result` | 每类 malformed top-level 都为 typed F09 error/no result |
| S05 `test_every_nested_dereference_is_guarded` | adversarial objects 的 property getter 若在 guard 前读取即 fail；函数返回 typed negative record |
| S06 `test_canonicalization_is_bounded_jcs_only` | sha256/JCS token、numbers/list/BOM/duplicate/depth/surrogate 拒绝 |
| S07 `test_all_digest_preimages_are_complete_and_sensitive` | 第 4 节每个材料字段单变均改变相应 digest |
| S08 `test_prior_and_current_recompute_from_independent_raw_authorities` | 两侧 spy authority 均被独立消费；交叉替换被检出 |
| S09 `test_reused_returns_prior_bindings_by_identity` | C 分支 tuple 及每个 binding 对象均 `is` prior receipt member |
| S10 `test_policy_trust_root_cannot_be_caller_self_signed` | 独立 root/ref/digest/locator约束；自签 policy fail closed |
| S11 `test_no_side_effect_import_or_runtime_surface` | import graph 禁止项、filesystem snapshot、learning monkeypatch 均零触达 |
| S12 `test_static_accounting_is_exactly_12_plus_70` | structural=12、parameter IDs=P01..P70、总 collected=82 |

### 13.2 70 parameter IDs 与逐 ID oracle

所有 ID 由 `test_feedback_contract_matrix[Px]` 承载：

| ID | stimulus | exact oracle |
|---|---|---|
| P01 | 完整 Production authority | `BOUND`；六 required MATCH；run N/A；完整三 refs + RULE anchor |
| P02 | 完整 PREPROD authority | `BOUND`；case/track/run/digest MATCH；statement/revision/set N/A；无 anchor |
| P03 | unknown statement ID | Production `UNBOUND`; statement mismatch；不可学习 |
| P04 | missing target revision | Production `UNBOUND`; revision unknown |
| P05 | old target revision | Production `UNBOUND`; revision mismatch + exact revision issue |
| P06 | duplicate valid statement candidates | `AMBIGUOUS`; empty graph |
| P07 | malformed statement ref | `INVALID`; empty graph；无未 guard dereference |
| P08 | statement digest mismatch | `INVALID`; empty graph |
| P09 | statement contract mismatch | `INVALID`;四 governing versions 不被合并 |
| P10 | set case mismatch | case mismatch；`UNBOUND` |
| P11 | set track mismatch | track 独立 mismatch；`UNBOUND` |
| P12 | set digest mismatch | `INVALID`; empty graph |
| P13 | set contract mismatch | `INVALID` |
| P14 | records artifact 缺失 | `UNBOUND`; target-unbound issue |
| P15 | records artifact duplicate | `AMBIGUOUS` |
| P16 | records state 非 VERIFIED | `UNBOUND` |
| P17 | records expected digest 缺失 | artifact digest unknown；`UNBOUND` |
| P18 | records observed digest 缺失 | artifact digest unknown；`UNBOUND` |
| P19 | records expected/observed 不等 | artifact digest mismatch；`UNBOUND` |
| P20 | records case/track/set 不等 |对应维独立值；aggregate `UNBOUND` |
| P21 | records ref object identity 不等 | `INVALID`; empty graph |
| P22 | projection type 非 records | `INVALID` |
| P23 | projection statement/revision/set 不等 | `INVALID` |
| P24 | projection source digest 不等 | `INVALID` |
| P25 | anchor selection 缺失 | `UNBOUND`; no anchor |
| P26 | anchor selection 多候选 | `AMBIGUOUS` |
| P27 | `UNSUPPORTED/NONE` anchor | `UNBOUND`; no learning target |
| P28 | empty all-rule refs | `INVALID` |
| P29 | duplicate all-rule ref | `INVALID` |
| P30 | selected anchor 不在 all refs | `INVALID` |
| P31 | selected anchor 出现两次 | `INVALID` |
| P32 | non-anchor 不是原序删除 selected | `INVALID` |
| P33 | source-order digest 不等 | `INVALID` |
| P34 | selected object type 非 RULE | `INVALID` |
| P35 | rule governing contract mismatch | `INVALID` |
| P36 | metadata receipt 缺失 | `UNBOUND`; `INELIGIBLE` |
| P37 | metadata receipt 多候选 | `AMBIGUOUS`; `HUMAN_REVIEW` 或 policy 指定 ineligible |
| P38 | metadata 任一字段 blank | `INVALID` |
| P39 | metadata 任一字段 UNMAPPED | `UNBOUND`; `INELIGIBLE` |
| P40 | metadata source/digest/version mismatch | `INVALID` |
| P41 | source/target track 均 resolved 且同值 | track MATCH；不影响其他六维独立值 |
| P42 | source/target track 均 resolved 且异值 | track MISMATCH + exact track issue；`UNBOUND` |
| P43 | source state SOURCE_MISSING | track UNKNOWN；`UNBOUND` |
| P44 | target state UNPARSABLE | track UNKNOWN；`UNBOUND` |
| P45 |任一 state AMBIGUOUS | track UNKNOWN；aggregate `AMBIGUOUS` |
| P46 |任一 state INTEGRITY_FAILED | track UNKNOWN；aggregate `INVALID` |
| P47 | resolved state 带 reason | malformed nested binding → `INVALID` |
| P48 | failure state reason 不精确 | malformed nested binding → `INVALID` |
| P49 | source side/track/parser mismatch | `INVALID`; source binding ref 不可伪造 |
| P50 | target side 非 BINDING_TARGET | `INVALID` |
| P51 | Production required statement 为 N/A 攻击 | `UNBOUND`;不得 BOUND |
| P52 | PREPROD required run 为 N/A 攻击 | `UNBOUND`;不得 BOUND |
| P53 | PREPROD 缺 target run | `UNBOUND` |
| P54 | PREPROD 缺 RUN_SNAPSHOT | `UNBOUND`; attachment 不解锁 |
| P55 | PREPROD duplicate refs | `INVALID` |
| P56 | PREPROD mixed case/track/run |各维独立；aggregate fail closed |
| P57 | PREPROD ref/record mismatch | `INVALID` |
| P58 | PREPROD extra legitimate run ref |仍可 `BOUND`；graph 非封闭三元组 |
| P59 | PREPROD BOUND eligibility | `INELIGIBLE`; no target/exclusion |
| P60 | approved Production policy正例 | `ELIGIBLE`;恰一 RULE target；ordered exclusions完整 |
| P61 | statement feedback policy 非 allowed | `INELIGIBLE` |
| P62 | unapproved policy ref | typed invalid authority；不得 caller 自签 |
| P63 | policy/root identity或digest mismatch | typed invalid authority |
| P64 | Production ambiguous binding | policy boolean 保留 `HUMAN_REVIEW/INELIGIBLE` 三态选择 |
| P65 | Production invalid/unknown-track binding |对应 policy boolean；永不 ELIGIBLE |
| P66 | initial operation | valid NEW/INITIAL；fresh receipt；no overwrite |
| P67 | changed source且 changed key | valid NEW/CHANGED；prior/current evidence retained；无 mismatch issue |
| P68 | changed policy/target revision/authority | valid NEW；canonical identity sensitivity逐项成立 |
| P69 | same key + same independently recomputed target | valid REUSED/SAME；bindings 对象机械复用 prior |
| P70 | same key + different independently recomputed target | invalid TARGET_MISMATCH；empty bindings；exact digest issue；no overwrite |

## 14. focused selector 与 exact regressions

合同通过 fresh review 后，实施阶段唯一 focused selector：

`python -m pytest tests/f09/test_feedback_eligibility.py -q`

期望：`82 passed`，且 accounting 为 12 structural + 70 parameter IDs。

随后只运行以下 exact regression nodeids：

1. `tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_h3_standard_list_schema_without_rule_ids_is_blocked_from_learning`
2. `tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_ingest_includes_v5_feedback_attachment_summary_without_unblocking_learning`
3. `tests/test_phase_a_minimal_learning_loop.py::test_statement_record_enforcement_marks_missing_as_unmapped`

期望：`3 passed`。本 CONTRACT drafting Gate 不运行上述命令。

## 15. STOP 条件与 falsifiers

实施者必须 STOP 并返回 CONTRACT review，若出现任一情况：

- 需要修改 Task 1–7 owner 或白名单外文件；
- 无法以 owner actual shape 实现；
- 需要 filesystem、learning、writer 或 caller-signed trust root；
- 无法在 dereference 前 guard；
- 需要第五个 binding status、第四个 eligibility status 或新增 disposition；
- 需要从 R29 摘要补语义；
- static collection 不等于 82；
- exact regressions 与 focused contract 冲突。

可证伪条件：任一摘要字段变化不改变应变 digest；prior 未从 raw authority 重算；REUSED 返回新 binding 对象；PREPROD 读取 production anchor；七维任一由 aggregate 倒推；metadata 由 rule ID/index 推断；policy 可自签；非 ELIGIBLE 暴露 learning target；调用后 filesystem/learning state 变化；malformed top-level 返回 result；nested semantic failure 抛出未约定异常。任一命中即否证实现符合 R30。

## 16. proven / unproven boundary

本合同静态已证明的范围仅是：权威字段已恢复、owner shape 已核对、实现白名单与 public surface 已冻结、canonical preimages/协议/优先级/eligibility/idempotency/test oracles 已写成可证伪规格。

本合同未证明：[`engine/f09/feedback.py`](../engine/f09/feedback.py) 已存在或正确；[`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py) 已存在；82 个测试可收集或通过；三个 regression 通过；import graph 与零副作用在运行时成立；fresh reviewer 接受本合同。以上只能在后续获授权 Gate 以实际代码与测试证据证明。

## 17. remaining unknowns

- 独立 approved policy/trust-root 的真实部署对象 ID、版本和 immutable source locator 尚未由当前 owner 提供；本合同将其作为 caller 必须提供并机械验证的 authority，不硬编码示例值。
- Production rule metadata 的未来持久化来源尚未由 Task 1–7 owner 暴露 read port；R30 因而要求 immutable `RuleMetadataReceipt` 随 authority 输入，且禁止 Task 8 自行访问 legacy records。
- PREPROD 合法扩展 artifact role 的注册表当前只由 [`ArtifactRecord.artifact_role`](../engine/f09/artifacts.py:89) 封闭值域表达；R30 允许其中 run-related retained roles，但不新增 role。

这些 unknown 不授权实现者自行选择业务常量；若 fresh review 认为它们阻断机械实现，应回到 CONTRACT drafting，而不是在代码中猜测。

---

**当前状态：等待 fresh review。本文不作任何 CONTRACT verdict。**
