# G6 Task 8 R32 CONTRACT — Feedback Binding and Learning Eligibility Without Learning

## 0. 文档状态与治理边界

- 角色：Analyst。本文件是对 [`plans/g6-task8-r31-contract.md`](g6-task8-r31-contract.md) fresh review 中五个 BLOCKER 与两个 MAJOR 的最小、自包含修订，不是 review verdict。
- [`plans/g6-task8-r30-contract.md`](g6-task8-r30-contract.md) 与 [`plans/g6-task8-r31-contract.md`](g6-task8-r31-contract.md) 均保留为失败历史；实现者不得依赖它们补全本合同。
- fresh review 接受前禁止实现、创建测试或运行测试。
- 唯一未来实现白名单：[`engine/f09/feedback.py`](../engine/f09/feedback.py) 与 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py)。
- Task 1–7 owner 冻结，不得修改 [`engine/f09/contracts.py`](../engine/f09/contracts.py)、[`engine/f09/trace.py`](../engine/f09/trace.py)、[`engine/f09/artifacts.py`](../engine/f09/artifacts.py)、[`engine/f09/canonical_json.py`](../engine/f09/canonical_json.py)、[`engine/f09/errors.py`](../engine/f09/errors.py)。
- Task 8 只计算 binding 与 eligibility：零文件 I/O、零 repository/writer/learning/iteration side effect、零系统时钟隐式读取。
- 本合同不授权 shell、Git 或 GitHub 操作。

## 1. 权威、owner identity 与冲突解释

解释顺序：

1. [`PI-230 feedback/eligibility`](production-implementation-pi-230-traceability-binding.md:617) 与 [`PI-230 idempotency`](production-implementation-pi-230-traceability-binding.md:584)。
2. [`PI-300 feedback objects`](production-implementation-pi-300-one-card-vertical-slice-design.md:909) 与 [`PI-300 IdempotencyKey`](production-implementation-pi-300-one-card-vertical-slice-design.md:1174)。
3. [`PI-500 Task 8`](production-implementation-pi-500-r1-f09-implementation-plan.md:2291)。
4. 当前 owner exact runtime identities：[`RunTrack`](../engine/f09/contracts.py:21)、[`DigestRef`](../engine/f09/contracts.py:78)、[`DetectedIssue`](../engine/f09/contracts.py:582)、[`DigestPresent`](../engine/f09/trace.py:37)、[`DigestMissing`](../engine/f09/trace.py:43)、[`VersionedObjectRef`](../engine/f09/trace.py:53)、[`SnapshotRef`](../engine/f09/trace.py:65)、[`StandardStatement`](../engine/f09/trace.py:146)、[`StatementSet`](../engine/f09/trace.py:174)、[`IdempotencyKey`](../engine/f09/artifacts.py:48)、[`ArtifactWriteAttempt`](../engine/f09/artifacts.py:71)、[`ArtifactRecord`](../engine/f09/artifacts.py:87)、[`ArtifactSetManifest`](../engine/f09/artifacts.py:113) 与 [`F09ContractError`](../engine/f09/errors.py:29)。
5. 对 Task 8 新 public surface、raw boundary、policy trust anchors、digest materials、target receipts、role graph与测试 ledger，以本 R32 为唯一实现规格。

owner 实际字段不得被旧计划示例改写；PI-230 的语义不变量不得被历史伪代码改写。

## 2. 通用 exact 规则

### 2.1 bounded JCS

所有 Task 8 canonical digest 只调用 [`bounded_jcs_sha256()`](../engine/f09/canonical_json.py:251)：

- token 精确为 `sha256` 与 `RFC8785-JCS-UTF8`，值为 lowercase 64-hex；
- 值域仅为 exact null、bool、Unicode scalar string、tuple array 与字符串键 exact dict；
- 拒绝 number、list、自定义对象、非字符串键、surrogate、duplicate JSON key、BOM、cycle、mutation 与深度超过 64；
- raw bytes 只由 [`parse_bounded_jcs()`](../engine/f09/canonical_json.py:215) 解析；
- dict keys 由 owner canonicalizer 按 UTF-16BE code-unit order 排序；合同列出的字段顺序只定义成员全集，不替代 JCS key sorting。

### 2.2 禁止隐式投影

每个进入摘要的领域对象必须调用第 6 节唯一有名 material。禁止 reflection、`dataclasses.asdict`、`repr`、`str(object)`、`__dict__`、隐式 dataclass field walking，亦禁止复用 [`trace._canonical_value()`](../engine/f09/trace.py:240) 对 Task 8 对象做反射投影。未被第 6 节穷尽定义的对象不得进入 Task 8 digest。

### 2.3 blank-string 规则

仅下列显式类别要求 exact nonblank `str`：

1. 所有以 `_id`、`_version`、`_at`、`_locator`、`_locator_id`、`_type`、`_code`、`_path`、`family_id`、`school`、`canon`、`rule_type`、`verdict` 命名且其类型不是 nullable 的字段；
2. `DigestRef.algorithm`、`DigestRef.canonicalization`、`DigestRef.value`；
3. `ArtifactRecord.path_locator`、policy 的 schema/contract identity；
4. 本合同明确写出 nonblank 的 tuple string member。

nullable identity 字段为 null 或 nonblank exact string；`annotation`、`error_class`、诊断文本及一般 payload string 不套用 blanket blank rejection。尤其 `FeedbackSubmission.source_snapshot_payload` 只受 [`JcsValue`](../engine/f09/canonical_json.py:11) exact graph 与 digest coherence 约束；值 `""` 是合法 root payload，只要其摘要匹配。

### 2.4 顶层与 nested failure 边界

顶层 envelope 在任何 nested dataclass 构造前依次验证：

1. `RawFeedbackAuthority`、`raw_submission`、target authority、clock 与 prior wrapper 的 exact top-level type；
2. raw bytes 可被 bounded JCS 解析为 exact dict，且 top-level keys 精确匹配 `FeedbackSubmission` raw schema；
3. `feedback_items` 是 exact tuple；每个 member 是 exact dict；每个 member 含且仅含 raw `FeedbackItem` keys；每个 `feedback_item_id` 是 exact nonblank `str`；
4. 已抽取 item IDs 无 duplicate，并按 raw tuple 建立稳定 identity；duplicate detection、后续排序、ledger 与 pointer path 全部只使用该 identity；
5. required top-level identity/time/version 字段满足第 2.3 节。

上述任一失败抛 typed [`F09ContractError`](../engine/f09/errors.py:29)，无 result。raw parse、digest token、prior receipt coherence 可按错误性质抛 [`F09ContractError`](../engine/f09/errors.py:29) 或 [`F09IntegrityError`](../engine/f09/errors.py:21)，无 result。不得把缺失、blank、错误类型或 duplicate `feedback_item_id` 降级成 item `INVALID`。

只有 identity envelope 成立后，其他 malformed nested field/ref/object 才成为该 item `INVALID`；合法多候选为 `AMBIGUOUS`；合法缺失或不可解析语义为 `UNBOUND`。每次 attribute/key/index dereference 前必须 exact type/tag/基数 guard，禁止捕获 `AttributeError`、`KeyError`、`IndexError` 模拟业务状态。

## 3. public surface exact shapes

本节全部新类型定义于未来 [`engine/f09/feedback.py`](../engine/f09/feedback.py)，均为 frozen dataclass、无 defaults；字段严格按表中顺序；tuple 顺序规范；union 为封闭 tagged union。

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
| `TargetResolutionCategory` | `Literal[INVALID_MATERIAL, AMBIGUOUS_CANDIDATES, TARGET_NOT_FOUND, SOURCE_SPAN_NOT_FOUND, TRACK_UNRESOLVED, REQUIRED_MATCH_FAILED, PROTOCOL_GRAPH_INCOMPLETE]` |
| `PreprodArtifactRole` | `Literal[RUN_SNAPSHOT, DECISION_RUN, FEEDBACK_ATTACHMENT, MANIFEST]` |
| `JcsSnapshotPayload` | owner [`JcsValue`](../engine/f09/canonical_json.py:11) 的 runtime identity；annotation 直接复用 owner alias |

### 3.2 submission、projection 与 binding

| public frozen dataclass | 字段，严格按声明顺序 |
|---|---|
| `TrackSourceBinding` | `track_source_binding_id: str`; `side: Literal[SUBMISSION_SOURCE, BINDING_TARGET]`; `track: RunTrack`; `state: TrackSourceState`; `source_evidence_ref: VersionedObjectRef`; `parser_ref: VersionedObjectRef`; `schema_version: str`; `contract_version: str`; `content_digest: DigestRef`; `state_reason_codes: tuple[TrackSourceReasonCode, ...]`; `captured_at: str` |
| `FeedbackItem` | `feedback_item_id: str`; `feedback_id: str`; `source_span_locator: str`; `target_statement_id: str | None`; `target_statement_revision_id: str | None`; `target_run_id: str | None`; `target_prediction_id: str | None`; `verdict: str`; `annotation: str`; `integrity: Literal[VALID, INVALID, UNRESOLVED]`; `issue_ids: tuple[str, ...]` |
| `FeedbackSubmission` | `feedback_id: str`; `case_id: str`; `track: RunTrack`; `track_source_binding: TrackSourceBinding`; `source_snapshot_ref: SnapshotRef`; `source_snapshot_payload: JcsValue`; `parser_id: str`; `parser_version: str`; `feedback_items: tuple[FeedbackItem, ...]`; `content_digest: DigestRef`; `captured_at: str` |
| `StatementProjectionRecord` | `projection_id: str`; `projection_type: Literal[STATEMENT_INDEX, STATEMENT_RECORDS]`; `statement_set_id: str`; `statement_id: str`; `statement_revision_id: str`; `source_statement_digest: DigestRef`; `projected_object_ref: VersionedObjectRef`; `transformation_id: str`; `fidelity: Literal[LOSSLESS, PARTIAL, LOSSY, UNSUPPORTED]`; `dropped_refs: tuple[VersionedObjectRef, ...]`; `synthesized_fields: tuple[str, ...]`; `issue_ids: tuple[str, ...]` |
| `AnchorSelectionRecord` | `anchor_selection_id: str`; `statement_id: str`; `statement_revision_id: str`; `all_rule_refs: tuple[VersionedObjectRef, ...]`; `selected_anchor_rule_ref: VersionedObjectRef | None`; `non_anchor_rule_refs: tuple[VersionedObjectRef, ...]`; `selection_policy_id: str`; `selection_policy_version: str`; `source_order_digest: DigestRef`; `fidelity: Literal[LOSSY, UNSUPPORTED]`; `fanout_scope: Literal[SELECTED_ANCHOR_ONLY, NONE]`; `issue_ids: tuple[str, ...]` |
| `FeedbackBinding` | `feedback_binding_id: str`; `feedback_item_ref: VersionedObjectRef`; `binding_protocol: BindingProtocol`; `source_track_binding_ref: VersionedObjectRef`; `target_track_source_binding: TrackSourceBinding`; `case_match: MatchRequired`; `track_match: MatchRequired`; `run_match: MatchOptional`; `statement_match: MatchOptional`; `revision_match: MatchOptional`; `statement_set_match: MatchOptional`; `artifact_digest_match: MatchRequired`; `target_object_refs: tuple[VersionedObjectRef, ...]`; `record_anchor_ref: VersionedObjectRef | None`; `status: BindingStatus`; `issue_ids: tuple[str, ...]`; `detected_issues: tuple[DetectedIssue, ...]`; `content_digest: DigestRef` |

### 3.3 authorities、独立 policies 与 target receipt

| public frozen dataclass | 字段，严格按声明顺序 |
|---|---|
| `GoverningVersions` | `statement_contract_version: str`; `statement_set_contract_version: str`; `statement_records_contract_version: str`; `rule_contract_version: str` |
| `RuleMetadataReceipt` | `rule_ref: VersionedObjectRef`; `family_id: str`; `school: str`; `canon: str`; `rule_type: str`; `metadata_schema_version: str`; `metadata_contract_version: str`; `source_ref: VersionedObjectRef`; `content_digest: DigestRef`; `captured_at: str` |
| `ProductionStatementAuthority` | `statement_set: StatementSet`; `manifest: ArtifactSetManifest`; `statement_refs: tuple[VersionedObjectRef, ...]`; `statement_set_ref: VersionedObjectRef`; `records_projection_refs: tuple[VersionedObjectRef, ...]`; `records_projection_records: tuple[StatementProjectionRecord, ...]`; `anchor_selections: tuple[AnchorSelectionRecord, ...]`; `rule_metadata_receipts: tuple[RuleMetadataReceipt, ...]`; `governing_versions: GoverningVersions`; `content_digest: DigestRef` |
| `PreprodRunAuthority` | `case_id: str`; `track: RunTrack`; `run_id: str`; `manifest: ArtifactSetManifest`; `target_refs: tuple[VersionedObjectRef, ...]`; `content_digest: DigestRef` |
| `AnchorPolicy` | `policy_id: str`; `policy_version: str`; `required_rule_object_type: Literal[RULE]`; `required_fidelity: Literal[LOSSY]`; `required_fanout_scope: Literal[SELECTED_ANCHOR_ONLY]`; `schema_version: str`; `contract_version: str`; `content_digest: DigestRef` |
| `EligibilityPolicy` | `policy_id: str`; `policy_version: str`; `allowed_track: RunTrack`; `required_feedback_policy: Literal[FEEDBACK_ALLOWED]`; `human_review_on_ambiguous: bool`; `human_review_on_invalid: bool`; `human_review_on_unknown_track: bool`; `schema_version: str`; `contract_version: str`; `content_digest: DigestRef` |
| `RawFeedbackAuthority` | `raw_submission: bytes`; `target_authority: ProductionStatementAuthority | PreprodRunAuthority`; `target_track_source_binding: TrackSourceBinding`; `captured_at: str` |
| `ItemTargetReceipt` | `feedback_item_id: str`; `protocol: BindingProtocol`; `target_statement_id: str | None`; `target_statement_revision_id: str | None`; `target_run_id: str | None`; `target_prediction_id: str | None`; `resolution_status: BindingStatus`; `non_bound_category: TargetResolutionCategory | None`; `graph: tuple[VersionedObjectRef, ...]`; `graph_digest: DigestRef`; `content_digest: DigestRef` |
| `FeedbackOperationReceipt` | `operation_id: str`; `key: IdempotencyKey`; `source_digest: DigestRef`; `authority_digest: DigestRef`; `item_target_receipts: tuple[ItemTargetReceipt, ...]`; `aggregate_target_digest: DigestRef`; `bindings: tuple[FeedbackBinding, ...]`; `anchor_policy_ref: VersionedObjectRef`; `eligibility_policy_ref: VersionedObjectRef`; `created_at: str`; `content_digest: DigestRef` |
| `PriorFeedbackOperation` | `raw_authority: RawFeedbackAuthority`; `receipt: FeedbackOperationReceipt` |

`ItemTargetReceipt` 总是存在且总是 digestible：

- `BOUND`：`non_bound_category=None`，`graph` 是第 8/9 节完整规范 graph；
- 非 `BOUND`：`non_bound_category` 必须是与最高优先状态一致的闭集值，`graph=()`；
- `graph_digest` 总是 `bounded_jcs_sha256(item_target_graph_material)`；禁止“无 digest graph”；
- `content_digest` 总是摘要完整 status-tagged receipt material。

### 3.4 operation 与 eligibility results

| public frozen dataclass | 字段，严格按声明顺序 |
|---|---|
| `ValidFeedbackOperationResult` | `valid: Literal[True]`; `operation_disposition: Literal[NEW_OPERATION, REUSED_OPERATION]`; `source_identity_relation: Literal[INITIAL, SAME, CHANGED]`; `prior_receipt: FeedbackOperationReceipt | None`; `current_receipt: FeedbackOperationReceipt`; `bindings: tuple[FeedbackBinding, ...]`; `overwrite_permitted: Literal[False]`; `detected_issues: tuple[DetectedIssue, ...]` |
| `InvalidFeedbackOperationResult` | `valid: Literal[False]`; `operation_disposition: Literal[TARGET_MISMATCH]`; `source_identity_relation: Literal[SAME]`; `prior_receipt: FeedbackOperationReceipt`; `current_key: IdempotencyKey`; `prior_aggregate_target_digest: DigestRef`; `current_aggregate_target_digest: DigestRef`; `item_target_receipts: tuple[ItemTargetReceipt, ...]`; `bindings: tuple[()]`; `overwrite_permitted: Literal[False]`; `detected_issues: tuple[DetectedIssue, ...]` |
| `LearningEligibility` | `eligibility_id: str`; `feedback_binding_id: str`; `feedback_binding_digest: DigestRef`; `policy_id: str`; `policy_version: str`; `status: EligibilityStatus`; `learning_target_refs: tuple[VersionedObjectRef, ...]`; `excluded_supporting_rule_refs: tuple[VersionedObjectRef, ...]`; `blocking_reason_codes: tuple[str, ...]`; `detected_issues: tuple[DetectedIssue, ...]`; `evaluated_at: str`; `content_digest: DigestRef` |

`FeedbackOperationResult` 是 valid/invalid 两类封闭 union。

### 3.5 ports 与 exact signatures

- `FeedbackClockPort`：runtime-checkable Protocol；`now() -> str`。
- `bind_feedback_operation(current: RawFeedbackAuthority, *, prior: PriorFeedbackOperation | None, clock: FeedbackClockPort) -> FeedbackOperationResult`。
- `validate_feedback_binding_record(binding: FeedbackBinding) -> None`。
- `evaluate_learning_eligibility(binding: FeedbackBinding, *, production_authority: ProductionStatementAuthority | None, clock: FeedbackClockPort) -> LearningEligibility`。
- `validate_learning_eligibility(eligibility: LearningEligibility) -> None`。

不存在 policy/trust-root 参数或 caller-controlled authority port。

## 4. raw schema、source payload 与 RFC 6901 resolver

`raw_submission` 必须是 bounded-JCS object，top-level keys 精确对应 `FeedbackSubmission`，nested keys 精确对应相应新/owner shape。解析固定为 raw bytes → bounded JCS → 第 2.4 节 identity envelope → nested exact keys/tags →对象构造 → coherence validation。payload 直接来自 raw，不得从 ref、locator、annotation 或 target authority 合成。

`source_snapshot_payload` 可为任一合法 bounded-JCS root，包括 `""`；重算摘要必须等于 `source_snapshot_ref.content_digest`。snapshot 必须为 `source_type=FEEDBACK`，identity/version/time nonblank，immutability 合法，locator tuple 无 duplicate 且 members nonblank。digest mismatch 令所有已建立 identity 的 items 为 `INVALID`，不得解析 pointer。

唯一 locator grammar：`source-snapshot-id + # + RFC6901-json-pointer`。必须 exact nonblank、无 surrogate、恰一 `#`；snapshot ID逐值匹配。fragment 为空表示 root，否则以 `/` 开始；仅接受 `~0` 与 `~1`，解码一次后再以 `~→~0`、`/→~1` canonical re-encode，结果必须逐值等于原 locator。dict 仅 exact key；tuple index 仅 `0` 或 `[1-9][0-9]*`，拒绝 `-`、正号、leading zero 与异常 coercion；禁止 wildcard、recursive descent、Unicode normalization、case fold 与多候选搜索。

malformed grammar/index token → `INVALID`；canonical pointer 路径不存在或中途命中 scalar → `UNBOUND`；成功恰得一个 node，node 可为 null/bool/string/tuple/dict。

## 5. 两个 caller-external policy trust boundary

### 5.1 AnchorPolicy pinned identity

模块私有 literals：

- ID `G6-TASK8-ANCHOR-SELECTION`；version `r32-anchor-v1`；schema `anchor-policy.r32.v1`；contract `g6-task8-r32-anchor`；
- object ID `POLICY:G6:TASK8:R32:ANCHOR`；revision `rev-r32-anchor-v1`；locator `engine.f09.feedback#PINNED_ANCHOR_POLICY_R32`；captured at `2026-07-22T00:00:00Z`；
- required object type `RULE`；fidelity `LOSSY`；fanout scope `SELECTED_ANCHOR_ONLY`。

`anchor_policy_material` 恰含 `policy_id, policy_version, required_rule_object_type, required_fidelity, required_fanout_scope, schema_version, contract_version`，排除 self digest。模块重算唯一 `AnchorPolicy.content_digest` 与 `VersionedObjectRef(object_type=ANCHOR_POLICY, DigestPresent(...))`。每个 `AnchorSelectionRecord.selection_policy_id/version` 只能与此 anchor policy 自身 identity 比较，禁止与 eligibility identity 比较。

### 5.2 EligibilityPolicy pinned identity

模块私有 literals：

- ID `G6-TASK8-LEARNING-ELIGIBILITY`；version `r32-eligibility-v1`；schema `eligibility-policy.r32.v1`；contract `g6-task8-r32-eligibility`；
- object ID `POLICY:G6:TASK8:R32:ELIGIBILITY`；revision `rev-r32-eligibility-v1`；locator `engine.f09.feedback#PINNED_ELIGIBILITY_POLICY_R32`；captured at `2026-07-22T00:00:00Z`；
- allowed track `RunTrack.PRODUCTION_DEFAULT`；required feedback policy `FEEDBACK_ALLOWED`；ambiguous/invalid/unknown-track booleans分别为 `True/False/True`。

`eligibility_policy_material` 恰含 `policy_id, policy_version, allowed_track, required_feedback_policy, human_review_on_ambiguous, human_review_on_invalid, human_review_on_unknown_track, schema_version, contract_version`，排除 self digest。模块重算唯一 `EligibilityPolicy.content_digest` 与 `VersionedObjectRef(object_type=ELIGIBILITY_POLICY, DigestPresent(...))`。eligibility positive validation 只能匹配此 policy 自身 ID/version。

### 5.3 independence 与 anti-self-signing

两个 policy 的 identity、material、digest、ref 分别重算，ID/version/object ID/digest 不得相等或互换；一个 policy 的 material 禁止包含另一个 policy digest。每次 bind/evaluate 从 module-private immutable literals构造，不读取 caller object、raw extra、target authority extra、environment、filesystem、mutable registry 或 monkeypatched provider。public schema/signature不接受 policy/root。caller 同 ID 自洽重签或把一个 policy 用于两种职责，必须被忽略或拒绝，永不改变结果。

## 6. 穷尽的 named recursive JCS materials

### 6.1 owner leaf 与 nested materials

以下名称、成员全集与 nested strategy 唯一：

- `digest_ref_material(d)`：`algorithm, canonicalization, value`。
- `digest_binding_material(b)`：`DigestPresent` 为 `status, digest`；`DigestMissing` 为 `status, digest=null, issue_id`。先 exact tag/type guard。
- `versioned_object_ref_material(r)`：`object_type, object_id, revision_id, schema_version, contract_version, digest_binding, source_locator_id, captured_at`；完整 material，不以 object ID 替代。
- `snapshot_ref_material(r)`：`source_snapshot_id, source_type, source_locator_ids, schema_version, contract_version, content_digest, captured_at, immutability`。
- `detected_issue_material(i)`：`issue_code, field_path`。
- `idempotency_key_material(k, include_canonical_key_digest)`：owner 字段 `operation, case_id, track, source_digest, schema_versions_digest, contract_digest, statement_set_id, feedback_id`，仅当 flag true 时再含 `canonical_key_digest`。
- `artifact_write_attempt_material(a)`：`attempt_id, artifact_id, idempotency_key, attempt_number_as_decimal_string, retry_of_attempt_id, input_snapshot_refs, started_at, finished_at, outcome, observed_digest, error_class, error_message_digest`。
- `artifact_record_material(r)`：`artifact_id, artifact_role, track, case_id, statement_set_id, run_id, path_locator, schema_version, expected_digest, observed_digest, state, attempts, issue_ids`。
- `artifact_set_manifest_self_excluded_material(m)`：`manifest_id, key` 使用完整 key material、`records, state, detected_issues`；排除 `digest`。使用前重算该 material 并验证 `m.digest`；其他材料嵌套 manifest 时只使用 `artifact_set_manifest_digest_identity_material`，其内容为 `manifest_id, digest`。
- `standard_statement_self_excluded_material(s)`：按 owner 声明字段逐一列入：`statement_id, statement_revision_id, case_id, track, statement_set_id, statement_type, text, feedback_policy, source_object_refs, evidence_refs, rule_refs, decision_trace_refs, content_digest`，只排除 owner 自签字段 `statement_digest`；若 owner 当前 exact field names 与此列表不一致，实施 STOP 而非反射猜测。嵌套 authority 时使用经 owner validator验证后的 `standard_statement_digest_identity_material(statement_id, statement_revision_id, statement_digest)`。
- `statement_set_self_excluded_material(s)`：按 owner 声明字段逐一列入：`statement_set_id, case_id, track, run_id, statements, source_snapshot_refs, content_digest`，排除 owner 自签字段 `statement_set_digest`；若 owner exact fields不同则 STOP。嵌套 authority时使用验证后的 `statement_set_digest_identity_material(statement_set_id, statement_set_digest)`。

任何拥有 self digest 的 nested owner object，必须先用其上述 self-excluded material重算并逐值验证，再按明确指定的 digest identity嵌入；无 self digest对象使用完整 material。

### 6.2 Task 8 object materials

- `track_source_binding_self_excluded_material`：第 3.2 节全部字段，排除 `content_digest`；refs用完整 ref material。
- `feedback_item_material`：第 3.2 节全部字段；无 self digest，完整嵌入。
- `feedback_submission_self_excluded_material`：第 3.2 节全部字段，排除 `content_digest`；payload原值；items按 raw order用完整 item material。
- `statement_projection_record_material`：第 3.2 节全部字段；无 self digest；refs完整嵌入。
- `anchor_selection_record_material`：第 3.2 节全部字段；无 self digest；refs完整嵌入。
- `governing_versions_material`：四个声明字段；无 self digest。
- `rule_metadata_receipt_self_excluded_material`：第 3.3 节全部字段，排除 `content_digest`；使用前重算；authority 嵌套时使用完整 self-excluded material加经验证的 `content_digest`。
- `anchor_policy_self_excluded_material` 与 `eligibility_policy_self_excluded_material`：第 5 节各自 exact material；嵌套 receipt/key时使用各自 `policy_digest_identity_material(policy_id, policy_version, schema_version, contract_version, content_digest)`。
- `production_authority_self_excluded_material`：`statement_set`用验证后 digest identity、`manifest`用验证后 digest identity；其余第 3.3 节字段依本节 named material完整嵌入；排除 `content_digest`。
- `preprod_authority_self_excluded_material`：第 3.3 节全部字段，manifest用验证后 digest identity、refs完整嵌入，排除 `content_digest`。
- `feedback_binding_self_excluded_material`：第 3.2 节全部字段，排除 `content_digest`；issues用 named material。
- `item_target_graph_material`：`protocol, raw_target_identity, resolution_status, non_bound_category, graph`；raw identity含四个原始 target ID/revision/run/prediction字段；`BOUND` graph按协议为完整 refs，非 BOUND graph恰为 empty tuple。每 item 无例外摘要此 material得到 `graph_digest`。
- `item_target_receipt_self_excluded_material`：第 3.3 节全部字段，排除 `content_digest`；`graph_digest`必须等于上一项重算值。
- `aggregate_target_material`：按 `feedback_item_id` UTF-16 code-unit order的 tuple，每项恰含 `feedback_item_id, protocol, resolution_status, graph_digest, item_target_receipt_content_digest`。每个 item 总贡献一个 digest。
- `feedback_operation_receipt_self_excluded_material`：第 3.3 节全部字段，排除 `content_digest`；key用完整 key material；authority/content/policy/item/binding digests均须先重算验证。
- `learning_eligibility_self_excluded_material`：第 3.4 节全部字段，排除 `content_digest`；refs完整嵌入；`feedback_binding_digest`等于重算 binding digest。

### 6.3 canonical operation key material

`schema_versions_digest_material` 是有名 tuple：`submission, track_source_binding, target_authority, rule_metadata, anchor_policy, eligibility_policy`，值为各 stable schema identity。`contract_digest_material` 是同名 stable contract identities并含四个 governing contract versions；PREPROD四位置为 null。

`canonical_operation_identity_material` 恰含：

1. `idempotency_key_without_canonical_digest`；
2. normalized item identity tuple：按 `feedback_item_id` UTF-16 order，每项含 `feedback_item_id` 与四个 raw target identity字段；
3. `anchor_policy_id, anchor_policy_version, eligibility_policy_id, eligibility_policy_version`；
4. submission schema/contract identity、target authority schema/contract identity、四个 governing versions；
5. source snapshot digest、feedback ID、case ID、track、Production statement-set ID或PREPROD null。

明确禁止进入 canonical key preimage：aggregate/current/prior target graph、任一 item target graph digest、`ProductionStatementAuthority.content_digest`、`PreprodRunAuthority.content_digest`、manifest/statement/set/artifact/rule metadata content digest及任何随同 raw target IDs/revisions不变而因 target content变化的 authority digest。key只标识稳定 operation intent；mutable target aggregate在 key equality成立后独立比较。

每个 self digest排除自身。S07 对每个 included field做单变 sensitivity，并验证 excluded self、禁止字段与合法 payload blank语义。

## 7. authority tuple validation 与 M1 closed sorting

所有 set-projection tuple先逐 member exact guard与完整 material validation，再 duplicate check，再排序；ordered tuple保持原序。

- `statement_refs`：full ref identity；按其完整 status-tagged sort key排序。
- `records_projection_refs`：先验证每个 member 是 exact `VersionedObjectRef`，每个 nullable/string字段合法，`digest_binding`是 exact `DigestPresent`或`DigestMissing`且各自成员合法；任一 malformed ref使相关 item `INVALID`，禁止排序。合法后排序键恰为：
  `object_id, nullable(revision_id), schema_version, nullable(contract_version), digest_binding_key, nullable(source_locator_id), nullable(captured_at)`。
  其中 `nullable(null)=(0,"")`、`nullable(str)=(1,str)`；`DigestPresent` key=`(0,"PRESENT",algorithm,canonicalization,value,"")`；`DigestMissing` key=`(1,"MISSING","","","",issue_id)`。禁止读取 `DigestMissing.digest.value`，禁止按不存在的 `artifact_id` 排序。
- `records_projection_records`：按 `projection_id`；duplicate → `INVALID`。
- `anchor_selections`：按 `statement_id, statement_revision_id`；duplicate pair → `AMBIGUOUS`。
- `rule_metadata_receipts`：按 rule ref full status-tagged identity；duplicate identity → `AMBIGUOUS`。

## 8. Production protocol

对目标 statement/revision必须唯一验证：statement与statement set；`STATEMENT_RECORDS` projection record；逐值等于其 `projected_object_ref` 的 records ref；以及 retained non-superseded artifact，其中 ref `object_id == artifact.artifact_id`。artifact role恰为 `STATEMENT_RECORDS`，case/track/set/run/schema/version一致，state恰 `VERIFIED`，expected与observed存在且相等，projection source digest等于statement content digest，projected ref digest等于observed digest，四 governing versions独立匹配。

Anchor必须唯一；`all_rule_refs`非空无duplicate；selected恰出现一次且 type `RULE`；non-anchor恰为按原序删除 selected；source-order digest重算；record policy ID/version只匹配第 5.1 节 `AnchorPolicy`；fidelity/fanout匹配该 policy。selected metadata receipt唯一、完整、非blank、非 `UNMAPPED`且 digest/version/source coherence成立。supporting rules只作为 ordered exclusions，不成为学习 target。

Production `BOUND` graph顺序恰为 `STATEMENT, STATEMENT_SET, STATEMENT_RECORDS, RULE`；binding `target_object_refs`恰前三项，`record_anchor_ref`恰为第四项。任何非 BOUND graph恰为空，但仍产生第 3.3/6.2 节 status-tagged item target receipt与 digest。

## 9. PREPROD closed role graph

允许 role闭集与顺序恰为：required exactly-one `RUN_SNAPSHOT`；optional zero-or-one `DECISION_RUN`、`FEEDBACK_ATTACHMENT`、`MANIFEST`。`REPORT`、`STATEMENT_INDEX`、`STATEMENT_RECORDS`、`FEEDBACK_SOURCE` forbidden。任一duplicate、超基数、forbidden或malformed role为 `INVALID`。

每个 ref必须唯一映射 retained non-superseded artifact：object type=role、object ID=artifact ID、schema/digest一致；record case/track/run等于 authority，statement_set_id=null，state=`VERIFIED`，expected/observed存在相等。`RUN_SNAPSHOT` 在refs与manifest两侧均恰一且映射同一 artifact；attachment不能替代。

PREPROD不读取 Production statement/set/projection/anchor/metadata；statement/revision/set为 `NOT_APPLICABLE`，anchor null。`BOUND` graph为按闭集顺序的全部合法refs；非 BOUND graph为空但仍摘要。PREPROD eligibility始终 `INELIGIBLE`。

## 10. binding mechanics、七维与 precedence

`TrackSourceBinding` resolved时reasons为空；每个failure state恰有对应单一reason。source side=`SUBMISSION_SOURCE`且track等于submission；target side=`BINDING_TARGET`。parser ref与parser identity对齐。只有两侧resolved才比较track，否则 `UNKNOWN`。

七维独立计算，不得从aggregate status倒推：

| 维度 | Production | PREPROD |
|---|---|---|
| case | required MATCH | required MATCH |
| track | required MATCH | required MATCH |
| run | NOT_APPLICABLE | required MATCH |
| statement | required MATCH | NOT_APPLICABLE |
| revision | required MATCH | NOT_APPLICABLE |
| statement set | required MATCH | NOT_APPLICABLE |
| artifact digest | required MATCH | required MATCH |

缺事实为 `UNKNOWN`，确定不等为 `MISMATCH`，仅明确许可处为 `NOT_APPLICABLE`。aggregate precedence固定：

1. `INVALID`：malformed/inconsistent material、protocol冲突、integrity failure、malformed locator、forbidden role；
2. `AMBIGUOUS`：结构合法但多个合法候选或track source ambiguous；
3. `UNBOUND`：合法缺失、pointer missing、source missing/unparsable、required unknown/mismatch/N/A、target/anchor/metadata不足；
4. `BOUND`：required全 MATCH、仅 permitted N/A、唯一完整graph且无前三类事实。

不得 default BOUND；track unknown永不 BOUND。每项无论何状态都先完成可独立计算的七维，再建立 status-tagged receipt。

## 11. eligibility

Evaluator只接受已验证 binding、可选 Production authority与clock；eligibility policy只来自第 5.2 节。

- `ELIGIBLE` 仅限 Production BOUND、track为eligibility policy allowed track、statement feedback policy为 `FEEDBACK_ALLOWED`、anchor已由独立 anchor policy正验、artifact/metadata/governing versions复核通过、恰一 selected `RULE`；
- target恰为 selected anchor；exclusions恰为ordered non-anchor refs；
- PREPROD、Production UNBOUND、policy禁止、metadata合法缺失固定 `INELIGIBLE`；
- Production AMBIGUOUS固定 `HUMAN_REVIEW`；INVALID固定 `INELIGIBLE`；unknown-track且非INVALID固定 `HUMAN_REVIEW`；
- 非eligible target/exclusion为空，blocking reasons nonempty；fresh `detected_issues=()`；
- `evaluated_at=clock.now()`；binding与eligibility digest独立重算；eligibility positive validation只接受第 5.2 节自身ID/version，绝不接受anchor policy identity。

## 12. idempotency、独立 raw authority 与 REUSED identity

producer自行构造 key：operation=`BIND_FEEDBACK`；case/track/source/schema/contract/set/feedback字段来自重算事实；canonical key只用第 6.3 节稳定 material。

prior/current必须分别从各自 raw bytes、payload、target authority、target track binding及两个module-pinned policies独立解析和重算。禁止用current重算prior，禁止信任receipt自报key/source/authority/item/aggregate/binding/content digest。先验证prior raw与receipt完整自洽，否则抛 [`F09IntegrityError`](../engine/f09/errors.py:21)，无 result。

分支顺序：

1. 无prior：`NEW_OPERATION/INITIAL`，fresh receipt与bindings。
2. prior合法且current key不同：`NEW_OPERATION`；source digest同为 `SAME`，否则 `CHANGED`；fresh current receipt。
3. key逐值相同后，才比较各自独立重算的 `aggregate_target_digest`：相同为 `REUSED_OPERATION/SAME`；current receipt必须是prior receipt同一对象，bindings tuple与每个member均逐对象 `is` prior receipt members。
4. same key + aggregate不同：`TARGET_MISMATCH/SAME`；empty bindings；返回current item target receipts证明可构造差异；exact issue `IDEMPOTENCY.DIGEST_MISMATCH @ /feedback/aggregate_target_digest`；不创建current receipt。

同 key + changed target graph的构造方式固定：保持raw submission、item IDs、四个raw target identity、policy/schema/contract identities全部不变，仅改变同identity target authority中的合法 graph content/digest；因此key相同而aggregate不同，必达分支4。所有分支overwrite false。

## 13. validators、issues 与副作用

`validate_feedback_binding_record`检查exact dataclass、closed domains、tuple、refs、track、locator、七维、协议graph/anchor/status/issue与binding digest。`validate_learning_eligibility`检查exact shape、policy identity、status、time、binding digest、eligible唯一RULE/exclusions/no reasons、非eligible空targets/exclusions/nonempty reasons、fresh issues与content digest。

Task 8唯一 producer issue pairs：

- `FEEDBACK.TARGET_UNBOUND @ /feedback_bindings/0`
- `FEEDBACK.REVISION_MISMATCH @ /feedback_bindings/0/revision_match`
- `FEEDBACK.TRACK_MISMATCH @ /feedback_bindings/0/track_match`
- `IDEMPOTENCY.DIGEST_MISMATCH @ /feedback/aggregate_target_digest`

未来 [`engine/f09/feedback.py`](../engine/f09/feedback.py) 只导入标准库与五个冻结owner模块。禁止 pathlib/filesystem/os/tempfile、network/subprocess/database/queue、tools feedback、learning repository/writer/iteration；不得调用系统时钟。

## 14. 静态测试 accounting：12 + 70 = 82

唯一测试文件为 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py)。collection必须恰为12个非参数 structural nodes加一个70-ID参数测试，共82；禁止额外node、duplicate ID或hidden generation。

### 14.1 structural nodes

| ID / exact suffix | 唯一 oracle |
|---|---|
| S01 `test_public_dataclass_shapes_are_exact` | 第3节全部public shapes/field order/annotation/frozen精确；含两policy与item target receipt |
| S02 `test_public_unions_aliases_and_protocol_are_closed` | aliases、union、port、四签名精确；无policy参数 |
| S03 `test_owner_types_are_reused_by_identity` | owner classes与JcsValue直接复用 |
| S04 `test_malformed_top_level_raises_typed_error_without_result` | feedback_items tuple/dict/ID/duplicate边界及其他top-level typed error/no result |
| S05 `test_every_nested_dereference_is_guarded` | adversarial getter在guard前不可触达；nested negative返回record |
| S06 `test_canonicalization_is_bounded_jcs_only` | token及number/list/BOM/duplicate/depth/surrogate拒绝；blank payload合法 |
| S07 `test_all_digest_preimages_are_complete_and_sensitive` | 第6节每个named recursive material、included-field sensitivity、self排除；key对禁止target content不敏感；每item总有digest |
| S08 `test_prior_and_current_recompute_from_independent_raw_authorities` | 两侧raw/payload/authority独立消费；same stable key可构造changed aggregate |
| S09 `test_reused_returns_prior_bindings_by_identity` | receipt、tuple与members均机械复用 |
| S10 `test_policy_trust_boundaries_are_independent_and_not_caller_signed` | anchor/eligibility identity/material/digest互异；各验自身；caller不能影响 |
| S11 `test_no_side_effect_import_or_runtime_surface` | 禁止import、filesystem snapshot、learning monkeypatch零触达 |
| S12 `test_static_accounting_is_exactly_12_plus_70` | structural=12、IDs=P01..P70、collected=82 |

### 14.2 参数矩阵 P01–P70

所有ID仅由 `test_feedback_contract_matrix[Px]` 承载：

| ID | stimulus | exact oracle |
|---|---|---|
| P01 | 完整Production authority | BOUND；六required MATCH；run N/A；三refs+RULE；BOUND target receipt |
| P02 | 完整PREPROD snapshot-only | BOUND；case/track/run/digest MATCH；三维N/A；receipt有snapshot graph |
| P03 | unknown statement ID | UNBOUND；statement mismatch；empty graph但receipt digest存在 |
| P04 | missing target revision | UNBOUND；revision unknown；status-tagged digest存在 |
| P05 | old target revision | UNBOUND；revision mismatch+exact issue |
| P06 | duplicate valid statement candidates | AMBIGUOUS；empty graph；category精确 |
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
| P37 | metadata receipt多候选 | AMBIGUOUS；HUMAN_REVIEW |
| P38 | metadata显式identity字段blank | INVALID |
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
| P51 | payload digest mismatch或locator malformed/noncanonical | INVALID；resolver不运行；empty graph但digest存在 |
| P52 | locator canonical但pointer missing/scalar traversal | UNBOUND；与malformed分账；blank root payload正例可解析 |
| P53 | PREPROD缺target run | UNBOUND |
| P54 | PREPROD缺或多RUN_SNAPSHOT | 缺UNBOUND；多INVALID；每项仍有target digest |
| P55 | PREPROD duplicate refs/role | INVALID |
| P56 | PREPROD mixed case/track/run | 各维独立；fail closed |
| P57 | PREPROD ref/record mismatch或forbidden role | INVALID；empty graph |
| P58 | PREPROD增加唯一完整DECISION_RUN | 仍BOUND；规范顺序snapshot,decision-run |
| P59 | PREPROD BOUND eligibility | INELIGIBLE；no target/exclusion |
| P60 | 两policy各自正例 | anchor只验anchor identity；eligibility只验eligibility identity；ELIGIBLE恰一RULE+ordered exclusions |
| P61 | statement feedback policy非allowed | INELIGIBLE |
| P62 | caller raw/authority extra注入任一自签policy | top-level拒绝或extra attribute忽略；结果不变 |
| P63 | 交换两policy identity或monkeypatch provider | 各自positive validation失败或provider零调用；永不互换 |
| P64 | Production ambiguous binding | eligibility policy固定HUMAN_REVIEW |
| P65 | Production invalid或unknown-track | invalid INELIGIBLE；unknown非invalid HUMAN_REVIEW；永不ELIGIBLE |
| P66 | initial operation | valid NEW/INITIAL；fresh receipt；no overwrite |
| P67 | changed source且changed key | valid NEW/CHANGED；无mismatch issue |
| P68 | raw target revision改变 | stable operation identity按raw revision敏感，key改变；valid NEW；aggregate另算 |
| P69 | same key + same独立重算aggregate | valid REUSED/SAME；receipt/bindings机械复用；所有item receipt/digest重验 |
| P70 | raw IDs/revisions与key稳定字段不变，仅合法target graph content改变 | same key + different aggregate；TARGET_MISMATCH；empty bindings；exact issue；no overwrite |

P01–P07/P51–P57同时断言非BOUND也有status-tagged target material；P60/P63关闭policy分界；P68–P70机械证明canonical key与target aggregate分域。ID连续且恰70。

## 15. focused selector、regressions、STOP 与 falsifiers

fresh review后唯一focused selector：`python -m pytest tests/f09/test_feedback_eligibility.py -q`，期望 `82 passed`。随后只运行三个 exact node：

1. `tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_h3_standard_list_schema_without_rule_ids_is_blocked_from_learning`
2. `tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_ingest_includes_v5_feedback_attachment_summary_without_unblocking_learning`
3. `tests/test_phase_a_minimal_learning_loop.py::test_statement_record_enforcement_marks_missing_as_unmapped`

期望 `3 passed`；本 drafting gate不运行。

实施者必须STOP并返回contract review：需修改白名单外文件；owner exact shape与第6.1节列举不一致；需I/O/learning/writer/caller policy；无法guard-before-dereference；需新增状态/disposition；collection不等82；focused与exact regressions冲突。

机械 falsifiers：key包含target aggregate或target-sensitive authority digest；同key target graph变化不可构造；任一item缺digest；非BOUND material无status/category/raw identity；两个policy共用identity/material/digest；raw item ID失败被降级；任一nested digest材料靠反射；`DigestMissing`排序dereference digest；blank payload被拒；prior未独立重算；REUSED重建对象；七维倒推；PREPROD读取Production graph；supporting rule成为target；非eligible暴露target；产生副作用。任一命中即否证实现符合R32。

## 16. 七项 closure mapping 与 remaining unknowns

| finding | R32 closure |
|---|---|
| B1 canonical key/target mismatch | 第6.3与12节从key移除aggregate及target-sensitive authority digests；key相等后独立比较aggregate；S07/S08、P68–P70同步 |
| B2 every item digestible | 第3.3与6.2节冻结status-tagged `ItemTargetReceipt`；BOUND完整graph，非BOUND empty graph+闭集category；每项总有digest |
| B3 policy trust boundaries | 第5节冻结互异AnchorPolicy与EligibilityPolicy identity/material/digest/ref，各自positive validation，禁止复用 |
| B4 stable nested identity | 第2.4节先验证exact tuple/dict/nonblank item ID与duplicate，再允许nested降级；违规typed top-level error/no result |
| B5 exhaustive recursive materials | 第6节逐对象命名并声明full material或validated digest identity；禁止reflection/asdict/repr/implicit walking |
| M1 projection-ref sorting | 第7节先validate再以覆盖Present/Missing的完整tagged key排序 |
| M2 narrow blank rejection | 第2.3与4节仅枚举identity/time/version等；blank source payload合法且只验JcsValue/digest |

静态合同冻结public shapes、失败边界、两套policy、所有digest preimages、独立raw recomputation、REUSED identity、Production/PREPROD separation、七维、precedence、metadata/selected RULE/exclusions、三态eligibility、零副作用与82-case ledger。

remaining unknown仅为未来实现与执行证据：代码尚不存在，82-case collection/通过、三个regression通过及fresh reviewer接受均未被本文证明。Production metadata持久化来源仍无Task 1–7 port，本合同继续将完整重摘要的内存 `RuleMetadataReceipt` 作为输入证据；不要求常量，不构成已知 blocker。当前无其他预期 blocker。

---

**当前状态：等待 fresh review。本文不作任何 CONTRACT verdict。**
