# G6 Task 8 R36 CONTRACT — Feedback Binding and Learning Eligibility Without Learning

## 0. 文档状态与治理边界

- 角色：Analyst。本文件是 Task 8 合同文档 revision R36，supersede [`plans/g6-task8-r35-contract.md`](g6-task8-r35-contract.md)，只关闭多 item producer issue path 的合同缺口，不给 review verdict。
- R35 fresh CONTRACT review 曾为 PASS；后续 STATIC_REVIEW 发现：上游权威允许一个 submission 含多个 item 且每项生成一个 canonical binding，但 R35 将三类 item-local issue path 固定为索引 `0`。该矛盾使 R35 CONTRACT PASS失效，并要求回到 CONTRACT Gate。
- [`plans/g6-task8-r35-contract.md`](g6-task8-r35-contract.md)、[`plans/g6-task8-r34-contract.md`](g6-task8-r34-contract.md)、[`plans/g6-task8-r33-contract.md`](g6-task8-r33-contract.md) 及更早合同均保留为历史；实现者只以本 R36 为 Task 8 唯一合同，不得依赖历史合同补全、覆盖或改写语义。
- fresh review 接受前禁止实现、创建测试或运行测试。本次 drafting 不运行命令、pytest、Git 或 GitHub mutation。
- 唯一未来实现白名单：[`engine/f09/feedback.py`](../engine/f09/feedback.py) 与 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py)。
- Task 1–7 owner 冻结，不得修改 [`engine/f09/contracts.py`](../engine/f09/contracts.py)、[`engine/f09/trace.py`](../engine/f09/trace.py)、[`engine/f09/artifacts.py`](../engine/f09/artifacts.py)、[`engine/f09/canonical_json.py`](../engine/f09/canonical_json.py)、[`engine/f09/errors.py`](../engine/f09/errors.py)。
- Task 8 只计算 binding 与 eligibility：零文件 I/O、零 repository/writer/learning/iteration side effect、零系统时钟隐式读取。

## 1. 权威与 owner identity

解释顺序：

1. [`PI-230 feedback/eligibility`](production-implementation-pi-230-traceability-binding.md:617) 与 [`PI-230 idempotency`](production-implementation-pi-230-traceability-binding.md:584)。
2. [`PI-300 feedback objects`](production-implementation-pi-300-one-card-vertical-slice-design.md:909) 与 [`PI-300 IdempotencyKey`](production-implementation-pi-300-one-card-vertical-slice-design.md:1174)。
3. [`PI-500 Task 8`](production-implementation-pi-500-r1-f09-implementation-plan.md:2291)。
4. 当前 owner exact runtime identities：[`RunTrack`](../engine/f09/contracts.py:21)、[`DigestRef`](../engine/f09/contracts.py:78)、[`DetectedIssue`](../engine/f09/contracts.py:582)、[`DigestPresent`](../engine/f09/trace.py:37)、[`DigestMissing`](../engine/f09/trace.py:43)、[`VersionedObjectRef`](../engine/f09/trace.py:53)、[`SnapshotRef`](../engine/f09/trace.py:65)、[`StandardStatement`](../engine/f09/trace.py:146)、[`StatementSet`](../engine/f09/trace.py:174)、[`IdempotencyKey`](../engine/f09/artifacts.py:48)、[`ArtifactWriteAttempt`](../engine/f09/artifacts.py:71)、[`ArtifactRecord`](../engine/f09/artifacts.py:87)、[`ArtifactSetManifest`](../engine/f09/artifacts.py:113) 与 [`F09ContractError`](../engine/f09/errors.py:29)。
5. 对 Task 8 新 public surface、raw boundary、policy trust anchors、digest materials、target receipts、role graph 与测试 ledger，以本 R36 为唯一实现规格。

owner 实际字段不得被 PI 示例或旧合同改写。R36 对 owner digest 只允许两类使用：调用 owner public digest API；或在不存在可独立调用的 public validator 时，逐字段复制当前 owner material并用静态 oracle 防漂移。禁止调用 owner private helper。

## 2. 通用 exact 规则

### 2.1 bounded JCS

所有 Task 8 canonical digest 只调用 [`bounded_jcs_sha256()`](../engine/f09/canonical_json.py:251)：token 精确为 `sha256` 与 `RFC8785-JCS-UTF8`，值为 lowercase 64-hex；值域仅 exact null、bool、Unicode scalar string、tuple array 与字符串键 exact dict；拒绝 number、list、自定义对象、非字符串键、surrogate、duplicate JSON key、BOM、cycle、mutation 与深度超过 64。raw bytes 只由 [`parse_bounded_jcs()`](../engine/f09/canonical_json.py:215) 解析。dict keys 由 owner canonicalizer 按 UTF-16BE code-unit order排序。

### 2.2 禁止隐式投影

每个进入 Task 8 摘要的领域对象必须调用第 6 节唯一有名 material。禁止 reflection、`dataclasses.asdict`、`repr`、`str(object)`、`__dict__`、隐式 dataclass field walking，亦禁止复用 [`trace._canonical_value()`](../engine/f09/trace.py:240) 做反射投影。第 6.1 节对 owner statement/set 的逐字段复制是冻结的 named material，不授权反射。

### 2.3 blank string

exact nonblank `str` 仅适用于：非 nullable 的 `_id`、`_version`、`_at`、`_locator`、`_locator_id`、`_type`、`_code`、`_path`、`family_id`、`school`、`canon`、`rule_type`、`verdict` 字段；digest token/value；artifact path；policy schema/contract identity；以及本合同明确声明 nonblank 的 tuple member。nullable identity 为 null 或 nonblank exact string。`annotation`、`error_class`、诊断文本及一般 payload string 不受 blanket blank rejection；`source_snapshot_payload=""` 合法，只要摘要相符。

### 2.4 identity envelope 与 guard-before-dereference

任何 nested dataclass 构造前依次验证：`RawFeedbackAuthority`、raw bytes、target authority、clock、prior wrapper 的 exact 顶层类型；raw 顶层 keys；`feedback_items` exact tuple；每项 exact dict与keys；每个 `feedback_item_id` exact nonblank string；无 duplicate；必需 identity/time/version。任一失败抛 typed [`F09ContractError`](../engine/f09/errors.py:29) 或按完整性性质抛 [`F09IntegrityError`](../engine/f09/errors.py:21)，无 result，不得降级为 item `INVALID`。

identity envelope 成立后，其他 malformed nested field/ref/object 才为 item `INVALID`；合法多候选为 `AMBIGUOUS`；合法缺失或不可解析为 `UNBOUND`。每次 attribute/key/index dereference 前必须 exact class/type/tag/tuple cardinality guard；禁止捕获 `AttributeError`、`KeyError`、`IndexError` 模拟业务状态。

## 3. public surface exact shapes

本节新类型全部定义于未来 [`engine/f09/feedback.py`](../engine/f09/feedback.py)，均 frozen dataclass、无 defaults、字段顺序精确。

### 3.1 closed aliases

- `MatchRequired = Literal[MATCH, MISMATCH, UNKNOWN]`。
- `MatchOptional = Literal[MATCH, MISMATCH, NOT_APPLICABLE, UNKNOWN]`。
- `TrackSourceState = Literal[AVAILABLE_RESOLVED, SOURCE_MISSING, UNPARSABLE, AMBIGUOUS, INTEGRITY_FAILED]`。
- `TrackSourceReasonCode = Literal[TRACK_SOURCE_MISSING, TRACK_SOURCE_UNPARSABLE, TRACK_SOURCE_AMBIGUOUS, TRACK_SOURCE_INTEGRITY_FAILED]`。
- `BindingProtocol = Literal[PRODUCTION_STATEMENT, PREPROD_RUN_TARGET]`。
- `BindingStatus = Literal[BOUND, UNBOUND, AMBIGUOUS, INVALID]`。
- `EligibilityStatus = Literal[ELIGIBLE, INELIGIBLE, HUMAN_REVIEW]`。
- `TargetResolutionCategory = Literal[INVALID_MATERIAL, AMBIGUOUS_CANDIDATES, TARGET_NOT_FOUND, SOURCE_SPAN_NOT_FOUND, TRACK_UNRESOLVED, REQUIRED_MATCH_FAILED, PROTOCOL_GRAPH_INCOMPLETE]`。
- `PreprodArtifactRole = Literal[RUN_SNAPSHOT, DECISION_RUN, FEEDBACK_ATTACHMENT, MANIFEST]`。
- `JcsSnapshotPayload` 直接复用 owner [`JcsValue`](../engine/f09/canonical_json.py:11)。

### 3.2 submission、projection 与 binding

- `TrackSourceBinding(track_source_binding_id: str, side: Literal[SUBMISSION_SOURCE, BINDING_TARGET], track: RunTrack, state: TrackSourceState, source_evidence_ref: VersionedObjectRef, parser_ref: VersionedObjectRef, schema_version: str, contract_version: str, content_digest: DigestRef, state_reason_codes: tuple[TrackSourceReasonCode, ...], captured_at: str)`。
- `FeedbackItem(feedback_item_id: str, feedback_id: str, source_span_locator: str, target_statement_id: str | None, target_statement_revision_id: str | None, target_run_id: str | None, target_prediction_id: str | None, verdict: str, annotation: str, integrity: Literal[VALID, INVALID, UNRESOLVED], issue_ids: tuple[str, ...])`。
- `FeedbackSubmission(feedback_id: str, case_id: str, track: RunTrack, track_source_binding: TrackSourceBinding, source_snapshot_ref: SnapshotRef, source_snapshot_payload: JcsValue, parser_id: str, parser_version: str, feedback_items: tuple[FeedbackItem, ...], content_digest: DigestRef, captured_at: str)`。
- `StatementProjectionRecord(projection_id: str, projection_type: Literal[STATEMENT_INDEX, STATEMENT_RECORDS], statement_set_id: str, statement_id: str, statement_revision_id: str, source_statement_digest: DigestRef, projected_object_ref: VersionedObjectRef, transformation_id: str, fidelity: Literal[LOSSLESS, PARTIAL, LOSSY, UNSUPPORTED], dropped_refs: tuple[VersionedObjectRef, ...], synthesized_fields: tuple[str, ...], issue_ids: tuple[str, ...])`。
- `AnchorSelectionRecord(anchor_selection_id: str, statement_id: str, statement_revision_id: str, all_rule_refs: tuple[VersionedObjectRef, ...], selected_anchor_rule_ref: VersionedObjectRef | None, non_anchor_rule_refs: tuple[VersionedObjectRef, ...], selection_policy_id: str, selection_policy_version: str, source_order_digest: DigestRef, fidelity: Literal[LOSSY, UNSUPPORTED], fanout_scope: Literal[SELECTED_ANCHOR_ONLY, NONE], issue_ids: tuple[str, ...])`。
- `FeedbackBinding(feedback_binding_id: str, feedback_item_ref: VersionedObjectRef, binding_protocol: BindingProtocol, source_track_binding_ref: VersionedObjectRef, target_track_source_binding: TrackSourceBinding, case_match: MatchRequired, track_match: MatchRequired, run_match: MatchOptional, statement_match: MatchOptional, revision_match: MatchOptional, statement_set_match: MatchOptional, artifact_digest_match: MatchRequired, target_object_refs: tuple[VersionedObjectRef, ...], record_anchor_ref: VersionedObjectRef | None, status: BindingStatus, issue_ids: tuple[str, ...], detected_issues: tuple[DetectedIssue, ...], content_digest: DigestRef)`。

### 3.3 authorities、policies 与 receipts

- `GoverningVersions(statement_contract_version: str, statement_set_contract_version: str, statement_records_contract_version: str, rule_contract_version: str)`。
- `RuleMetadataReceipt(rule_ref: VersionedObjectRef, family_id: str, school: str, canon: str, rule_type: str, metadata_schema_version: str, metadata_contract_version: str, source_ref: VersionedObjectRef, content_digest: DigestRef, captured_at: str)`。
- `ProductionStatementAuthority(statement_set: StatementSet, manifest: ArtifactSetManifest, statement_refs: tuple[VersionedObjectRef, ...], statement_set_ref: VersionedObjectRef, records_projection_refs: tuple[VersionedObjectRef, ...], records_projection_records: tuple[StatementProjectionRecord, ...], anchor_selections: tuple[AnchorSelectionRecord, ...], rule_metadata_receipts: tuple[RuleMetadataReceipt, ...], governing_versions: GoverningVersions, content_digest: DigestRef)`。
- `PreprodRunAuthority(case_id: str, track: RunTrack, run_id: str, manifest: ArtifactSetManifest, target_refs: tuple[VersionedObjectRef, ...], content_digest: DigestRef)`。
- `AnchorPolicy(policy_id: str, policy_version: str, required_rule_object_type: Literal[RULE], required_fidelity: Literal[LOSSY], required_fanout_scope: Literal[SELECTED_ANCHOR_ONLY], schema_version: str, contract_version: str, content_digest: DigestRef)`。
- `EligibilityPolicy(policy_id: str, policy_version: str, allowed_track: RunTrack, required_feedback_policy: Literal[FEEDBACK_ALLOWED], human_review_on_ambiguous: bool, human_review_on_invalid: bool, human_review_on_unknown_track: bool, schema_version: str, contract_version: str, content_digest: DigestRef)`。
- `RawFeedbackAuthority(raw_submission: bytes, target_authority: ProductionStatementAuthority | PreprodRunAuthority, target_track_source_binding: TrackSourceBinding, captured_at: str)`。
- `ItemTargetReceipt(feedback_item_id: str, protocol: BindingProtocol, target_statement_id: str | None, target_statement_revision_id: str | None, target_run_id: str | None, target_prediction_id: str | None, resolution_status: BindingStatus, non_bound_category: TargetResolutionCategory | None, graph: tuple[VersionedObjectRef, ...], graph_digest: DigestRef, content_digest: DigestRef)`。
- `FeedbackOperationReceipt(operation_id: str, key: IdempotencyKey, source_digest: DigestRef, authority_digest: DigestRef, item_target_receipts: tuple[ItemTargetReceipt, ...], aggregate_target_digest: DigestRef, bindings: tuple[FeedbackBinding, ...], anchor_policy_ref: VersionedObjectRef, eligibility_policy_ref: VersionedObjectRef, created_at: str, content_digest: DigestRef)`。
- `PriorFeedbackOperation(raw_authority: RawFeedbackAuthority, receipt: FeedbackOperationReceipt)`。

`ItemTargetReceipt` 总存在且可摘要：BOUND 时 category null且 graph 完整；非 BOUND 时 category 与最高优先状态一致且 graph empty；`graph_digest` 总为 status-tagged graph material摘要；`content_digest` 总摘要完整 receipt material。

### 3.4 results、ports 与签名

- `ValidFeedbackOperationResult(valid: Literal[True], operation_disposition: Literal[NEW_OPERATION, REUSED_OPERATION], source_identity_relation: Literal[INITIAL, SAME, CHANGED], prior_receipt: FeedbackOperationReceipt | None, current_receipt: FeedbackOperationReceipt, bindings: tuple[FeedbackBinding, ...], overwrite_permitted: Literal[False], detected_issues: tuple[DetectedIssue, ...])`。
- `InvalidFeedbackOperationResult(valid: Literal[False], operation_disposition: Literal[TARGET_MISMATCH], source_identity_relation: Literal[SAME], prior_receipt: FeedbackOperationReceipt, current_key: IdempotencyKey, prior_aggregate_target_digest: DigestRef, current_aggregate_target_digest: DigestRef, item_target_receipts: tuple[ItemTargetReceipt, ...], bindings: tuple[()], overwrite_permitted: Literal[False], detected_issues: tuple[DetectedIssue, ...])`。
- `LearningEligibility(eligibility_id: str, feedback_binding_id: str, feedback_binding_digest: DigestRef, policy_id: str, policy_version: str, status: EligibilityStatus, learning_target_refs: tuple[VersionedObjectRef, ...], excluded_supporting_rule_refs: tuple[VersionedObjectRef, ...], blocking_reason_codes: tuple[str, ...], detected_issues: tuple[DetectedIssue, ...], evaluated_at: str, content_digest: DigestRef)`。
- `FeedbackOperationResult` 是上述 valid/invalid 封闭 union。
- `FeedbackClockPort` 为 runtime-checkable Protocol，`now() -> str`。
- `bind_feedback_operation(current: RawFeedbackAuthority, *, prior: PriorFeedbackOperation | None, clock: FeedbackClockPort) -> FeedbackOperationResult`。
- `validate_feedback_binding_record(binding: FeedbackBinding) -> None`。
- `evaluate_learning_eligibility(binding: FeedbackBinding, *, production_authority: ProductionStatementAuthority | None, clock: FeedbackClockPort) -> LearningEligibility`。
- `validate_learning_eligibility(eligibility: LearningEligibility) -> None`。
- 不存在 policy/trust-root 参数或 caller-controlled authority port。

## 4. raw schema 与 resolver

`raw_submission` 必须是 bounded-JCS object，keys 精确对应 `FeedbackSubmission` 及 nested shapes。固定顺序为 raw bytes → bounded JCS → identity envelope → nested exact keys/tags →对象构造 → coherence validation。payload 直接来自 raw，不得合成。

`source_snapshot_payload` 可为任一合法 bounded-JCS root，包括 `""`；重算摘要等于 `source_snapshot_ref.content_digest`。snapshot 必须 `source_type=FEEDBACK`，identity/version/time nonblank，immutability 合法，locator tuple无duplicate且member nonblank。digest mismatch令全部已有 identity items为 `INVALID`，不得解析 pointer。

locator grammar唯一为 `source-snapshot-id#RFC6901-json-pointer`：恰一 `#`；snapshot ID逐值匹配；fragment空表示root，否则以 `/` 开始；只接受 `~0`/`~1`，解码一次后 canonical re-encode必须逐值相同。dict仅exact key；tuple index仅 `0` 或 `[1-9][0-9]*`；拒绝 `-`、正号、leading zero、wildcard、recursive descent、normalization、case fold与多候选搜索。malformed为 `INVALID`；canonical路径不存在或scalar traversal为 `UNBOUND`；成功恰一node。

## 5. 两个 caller-external policy trust boundary

R36 document revision 与 R33 runtime policy identity 是两个独立层次：R36 仅标识本合同文档代际；下述 AnchorPolicy 与 EligibilityPolicy 已进入 policy digest/ref、schema/contract digest 与 canonical operation key，其 runtime identity 继续稳定为 R33。本文不存在 policy 语义变化，所有 R33 runtime literals 必须逐值保留，禁止因文档 revision 机械升版为 R36；治理 revision 也不得进入任何 runtime digest、ref 或 key material。

### 5.1 AnchorPolicy

module-private literals：ID `G6-TASK8-ANCHOR-SELECTION`；version `r33-anchor-v1`；schema `anchor-policy.r33.v1`；contract `g6-task8-r33-anchor`；object ID `POLICY:G6:TASK8:R33:ANCHOR`；revision `rev-r33-anchor-v1`；locator `engine.f09.feedback#PINNED_ANCHOR_POLICY_R33`；captured at `2026-07-22T00:00:00Z`；type `RULE`；fidelity `LOSSY`；fanout `SELECTED_ANCHOR_ONLY`。

`anchor_policy_material` 恰含 policy 的七个非digest字段并排除 self digest；模块重算唯一 policy digest/ref。anchor record只匹配此 anchor policy identity。

### 5.2 EligibilityPolicy

module-private literals：ID `G6-TASK8-LEARNING-ELIGIBILITY`；version `r33-eligibility-v1`；schema `eligibility-policy.r33.v1`；contract `g6-task8-r33-eligibility`；object ID `POLICY:G6:TASK8:R33:ELIGIBILITY`；revision `rev-r33-eligibility-v1`；locator `engine.f09.feedback#PINNED_ELIGIBILITY_POLICY_R33`；captured at `2026-07-22T00:00:00Z`；allowed track `PRODUCTION_DEFAULT`；required policy `FEEDBACK_ALLOWED`；ambiguous/invalid/unknown booleans `True/False/True`。

`eligibility_policy_material` 恰含 policy 的九个非digest字段并排除 self digest；模块重算唯一 policy digest/ref。eligibility positive validation只匹配此 policy identity。

两policy identity/material/digest/ref独立且互异；禁止互含digest、交换、共用或caller签署。每次调用只从module-private immutable literals构造，不读取raw extra、environment、filesystem、registry或provider。

## 6. 穷尽 named recursive JCS materials

### 6.1 owner leaf、StandardStatement 与 StatementSet

通用 owner leaf：

- `digest_ref_material(d)`：`algorithm, canonicalization, value`。
- `digest_binding_material(b)`：exact-class/guard-before-deref；`DigestPresent` 为 `status, digest`；`DigestMissing` 为 `status, digest=null, issue_id`。
- `versioned_object_ref_material(r)`：`object_type, object_id, revision_id, schema_version, contract_version, digest_binding, source_locator_id, captured_at`。
- `snapshot_ref_material(r)`：`source_snapshot_id, source_type, source_locator_ids, schema_version, contract_version, content_digest, captured_at, immutability`。
- `detected_issue_material(i)`：`issue_code, field_path`。
- Enum 一律嵌入 `.value`；tuple保持原序；不得对 nested dataclass反射。

owner statement/set validator边界冻结如下：

- 当前唯一 public validator 是 [`validate_statement_projection()`](../engine/f09/trace.py:874)，其 actual authority 组合输入为 `statement_set, trace, result, package=None, *, normative_contract_ref=None, machine_appendix_ref=None`；它不是 StandardStatement 或 StatementSet 的独立 validator，且 Task 8 的 `ProductionStatementAuthority` 不拥有所需 `TraceEnvelope`、`DecisionEvaluationResult`、`NormalizedEvidencePackage` 与两份 card source refs。Task 8 因此不得调用它、不得调用 private [`_statement_content_digest()`](../engine/f09/trace.py:298) 或 [`_statement_set_content_digest()`](../engine/f09/trace.py:374)，也不得声称仅凭 Task 8 authority 已执行 owner projection validation。
- 因不存在可由 Task 8 actual authority 完整调用的 public standalone validator，R36 采用唯一允许的 fallback：逐字段复制当前 owner digest material，并以 S07 static field/material oracle 防止 owner 漂移；owner字段或helper exclusion集合变化时实施必须STOP回合同 review。

以下 nested materials 精确复制 owner [`_canonical_value()`](../engine/f09/trace.py:240) 对当前依赖 dataclass 的 material，不调用该 private函数：

- `frozen_declaration_ref_material`：`declaration_id, declaration_type, card_id, contract_version, declaration_schema_version, content_digest`。
- `frozen_declaration_binding_material`：先exact class/tag guard；`ResolvedDeclarationBinding` 为 `presence, ref`；`AbsentDeclarationBinding` 与 `NotApplicableDeclarationBinding` 为 `presence, reason_code`；`UnavailableDeclarationBinding` 为 `presence, reason_code, issue_ids`；`UnresolvableDeclarationBinding` 为 `presence, attempted_ref, reason_code, issue_ids`。
- `card_identity_ref_material`：`card_identity_ref_id, card_id, normative_contract_ref, machine_appendix_ref, field_path, source_field_state, evaluator_state, declaration_status, runtime_capability_status, source_locator_ids, issue_ids`；两个refs使用完整 named ref material。
- `decision_trace_ref_material`：`result_ref, action_id, selected_action, basis_record_ids, blocking_issue_ids, nonblocking_issue_ids, source_decision_refs, output_precision_binding, validation_plan_binding, structural_validity`。

`standard_statement_owner_content_material(s)` 必须先 exact class/field-order oracle，再含且仅含以下当前字段，按 named nested material递归：

`statement_id, statement_schema_version, case_id, statement_set_id, track, semantic_scope, domain, statement_text, display_section, decision_result_id, action_id, basis_record_ids, evidence_refs, relation_ids, source_locator_ids, card_identity_refs, confidence_snapshot_ref, output_precision_binding, validation_plan_binding, feedback_policy, integrity, issue_ids`。

它明确排除 `statement_revision_id` 与 `content_digest`，与当前 owner [`_statement_content_digest()`](../engine/f09/trace.py:298) 一致；不存在 `statement_digest, statement_type, text, source_object_refs, rule_refs, decision_trace_refs` 等字段。`statement_revision_id`变化不得改变该owner content digest；任一included字段变化必须改变。

`standard_statement_full_owner_material(s)` 含 [`StandardStatement`](../engine/f09/trace.py:146) 当前全部24字段，顺序/成员为：`statement_id, statement_revision_id, statement_schema_version, case_id, statement_set_id, track, semantic_scope, domain, statement_text, display_section, decision_result_id, action_id, basis_record_ids, evidence_refs, relation_ids, source_locator_ids, card_identity_refs, confidence_snapshot_ref, output_precision_binding, validation_plan_binding, feedback_policy, content_digest, integrity, issue_ids`；用于 statement set 的 nested statements，禁止以statement digest identity替代。

`statement_set_owner_content_material(s)` 必须先 exact class/field-order oracle，再含且仅含：`statement_set_id, statement_schema_version, case_id, track, source_package_ref, decision_trace_ref, statements, generated_at, publication_state, issue_ids`，其中 `statements` 按原序嵌入 `standard_statement_full_owner_material`；只排除 `content_digest`，与当前 owner [`_statement_set_content_digest()`](../engine/f09/trace.py:374) 一致。不存在 `run_id, source_snapshot_refs, statement_set_digest`。任一included字段及任一nested statement字段变化必须改变；仅set `content_digest`变化不得改变。

Task 8 对 Production authority 中 statement/set 的处理顺序固定：

1. 在任何dereference前 exact class guard；检查 statement set field tuple与每个nested statement exact class。
2. 用上述 named owner materials与 [`bounded_jcs_sha256()`](../engine/f09/canonical_json.py:251) 分别重算每个 statement `content_digest` 和 set `content_digest`；逐值不等即 `INVALID`。
3. authority material只嵌入经上述验证的 external identities：`standard_statement_validated_identity_material = statement_id, statement_revision_id, content_digest`；`statement_set_validated_identity_material = statement_set_id, content_digest`。此处没有重定义另一套 owner算法。
4. S07 静态断言 owner dataclass exact field order、owner private helper exclusion集合、每个named nested material与上述复制一致；漂移立即失败并要求合同修订，禁止静默兼容。

### 6.2 ArtifactSetManifest owner digest

- Artifact record及attempt的具体递归 canonical material完全由 public [`digest_artifact_records()`](../engine/f09/artifacts.py:241) 权威拥有；Task 8 不复制、不重命名、不替代该算法。
- 任何 manifest owner验证必须先 exact class/tuple/member guard，然后严格调用 `digest_artifact_records(manifest.records)` 并逐值比较 `manifest.digest`。不允许将 `manifest_id`、`key`、`state` 或 `detected_issues` 纳入 `manifest.digest`，也不允许摘要整个manifest来验证owner digest。
- Task 8 不需要完整manifest envelope digest，因此不定义 `artifact_manifest_envelope_digest`。authority material嵌入 `artifact_manifest_validated_records_identity_material`，其唯一成员为已由 public API重算并验证的 `records_digest=manifest.digest`；manifest其他字段仅参与shape/coherence/协议状态校验，不伪装成owner digest identity。
- owner records digest sensitivity oracle：任一 [`canonicalize_artifact_records()`](../engine/f09/artifacts.py:189) 所含record/attempt字段变化必须改变 `manifest.digest`；仅改变 `manifest_id/key/state/detected_issues` 必须不改变 `manifest.digest`。若未来确需envelope digest，必须另立合同、另命名、另material与另sensitivity oracle；禁止替代owner records digest。

### 6.3 其余 owner 与 Task 8 materials

- `idempotency_key_material(k, include_canonical_key_digest)`：`operation, case_id, track, source_digest, schema_versions_digest, contract_digest, statement_set_id, feedback_id`，flag true才含 `canonical_key_digest`。
- `track_source_binding_self_excluded_material`：第3.2节全部字段，排除 `content_digest`。
- `feedback_item_material`：全部字段。
- `feedback_submission_self_excluded_material`：全部字段，排除 `content_digest`；payload原值；items raw order。
- `statement_projection_record_material`、`anchor_selection_record_material`、`governing_versions_material`：各自全部字段。
- `rule_metadata_receipt_self_excluded_material`：全部字段排除 `content_digest`；authority嵌入完整self-excluded material与validated digest。
- 两policy self-excluded materials按第5节；receipt/key嵌入各自 `policy_digest_identity_material(policy_id, policy_version, schema_version, contract_version, content_digest)`。
- `production_authority_self_excluded_material`：statement set用validated identity；manifest用validated records identity；其余字段按named material完整嵌入；排除 `content_digest`。
- `preprod_authority_self_excluded_material`：manifest用validated records identity；其余字段完整嵌入；排除 `content_digest`。
- `feedback_binding_self_excluded_material`：全部字段排除 `content_digest`。
- `item_target_graph_material`：`protocol, raw_target_identity, resolution_status, non_bound_category, graph`；raw identity含四个raw target字段；BOUND graph完整，非BOUND empty。
- `item_target_receipt_self_excluded_material`：全部字段排除 `content_digest`；先重算graph digest。
- `aggregate_target_material`：按 `feedback_item_id` UTF-16 order，每项 `feedback_item_id, protocol, resolution_status, graph_digest, item_target_receipt_content_digest`。
- `feedback_operation_receipt_self_excluded_material`：全部字段排除 `content_digest`；所有nested digest先重算验证。
- `learning_eligibility_self_excluded_material`：全部字段排除 `content_digest`；binding digest须重算。

### 6.4 canonical operation key

`schema_versions_digest_material` 为 `submission, track_source_binding, target_authority, rule_metadata, anchor_policy, eligibility_policy`。`contract_digest_material` 同名并含四 governing versions；PREPROD四位置null。

`canonical_operation_identity_material` 恰含：key-without-canonical-digest；按item ID排序的 item raw identity tuple；两个policy ID/version；submission/authority schema/contract及四governing versions；source snapshot digest、feedback/case/track、Production set ID或PREPROD null。

禁止进入key：aggregate/current/prior graph、任一graph digest、authority content digest、manifest/statement/set/artifact/metadata digest及任何target-content-sensitive digest。每个self digest排除自身。R36 治理 revision 同样禁止进入 policy digest/ref、schema/contract digest、canonical operation key 或任何 runtime material。S07做included-field单变、excluded-self、key禁止项、blank payload、owner statement/set static-oracle、owner records digest sensitivity。

## 7. authority tuple validation 与 sorting

所有set-projection tuple先member exact guard/material validation，再duplicate，再排序。`statement_refs`按full ref identity。`records_projection_refs`合法后按 `object_id, nullable(revision_id), schema_version, nullable(contract_version), digest_binding_key, nullable(source_locator_id), nullable(captured_at)`；`nullable(null)=(0,"")`、string=`(1,str)`；Present=`(0,"PRESENT",algorithm,canonicalization,value,"")`；Missing=`(1,"MISSING","","","",issue_id)`。禁止读取 `DigestMissing.digest.value` 或不存在的 `artifact_id`。projection records按projection ID；anchor按statement/revision；metadata按full rule ref；duplicate按既定INVALID/AMBIGUOUS语义。

## 8. Production protocol

目标statement/revision必须唯一验证：statement及set owner digest；STATEMENT_RECORDS projection与ref；retained non-superseded artifact。artifact role、case/track/set/run/schema/version、VERIFIED、expected/observed、projection source/projected digest及四governing versions均独立匹配。

Anchor唯一；all rules非空无duplicate；selected恰一次且type RULE；non-anchor为原序删除selected；source-order digest重算；record只匹配AnchorPolicy；fidelity/fanout匹配。selected metadata receipt唯一、完整、nonblank、非UNMAPPED且digest/version/source coherent。supporting rules仅ordered exclusions。

Production BOUND graph顺序恰 `STATEMENT, STATEMENT_SET, STATEMENT_RECORDS, RULE`；binding targets恰前三，anchor恰第四。非BOUND graph empty但仍有status-tagged receipt/digest。

## 9. PREPROD closed role graph

required exactly-one `RUN_SNAPSHOT`；optional zero-or-one `DECISION_RUN, FEEDBACK_ATTACHMENT, MANIFEST`；顺序固定。REPORT、STATEMENT_INDEX、STATEMENT_RECORDS、FEEDBACK_SOURCE forbidden。duplicate、超基数、forbidden、malformed均INVALID。

每ref唯一映射retained non-superseded artifact；type/ID/schema/digest/case/track/run一致，set ID null，VERIFIED且expected=observed。snapshot两侧恰一且同artifact。PREPROD不读取Production statement/set/projection/anchor/metadata；三statement维N/A，anchor null。BOUND graph为全部合法refs；非BOUND empty仍摘要。PREPROD eligibility始终INELIGIBLE。

## 10. binding、七维与 precedence

TrackSourceBinding resolved时reasons empty；failure state各有唯一reason。source side/track/parser与submission一致；target side正确。两侧resolved才比较track，否则UNKNOWN。

七维独立：Production为case/track/statement/revision/set/artifact required MATCH，run N/A；PREPROD为case/track/run/artifact required MATCH，statement/revision/set N/A。缺事实UNKNOWN，确定不等MISMATCH。precedence固定：INVALID malformed/inconsistent/integrity/protocol；AMBIGUOUS多合法候选或source ambiguous；UNBOUND合法缺失、pointer/source unresolved、required失败、graph不足；BOUND仅完整唯一且required全MATCH。不得default BOUND或倒推七维。

## 11. eligibility

只接受validated binding、可选Production authority与clock，policy仅来自module pin。ELIGIBLE仅Production BOUND、allowed track、statement `FEEDBACK_ALLOWED`、anchor policy正验、artifact/metadata/versions复核、恰一selected RULE。target恰selected；exclusions恰ordered supporting rules。PREPROD、UNBOUND、policy禁止、metadata合法缺失为INELIGIBLE；AMBIGUOUS为HUMAN_REVIEW；INVALID为INELIGIBLE；unknown-track且非invalid为HUMAN_REVIEW。非eligible targets/exclusions empty且reasons nonempty；fresh issues empty；time来自clock；两digest独立。

## 12. idempotency、prior/current 与 REUSED

producer构造 `BIND_FEEDBACK` key。prior/current分别从各自raw bytes、payload、authority、target binding与module policies独立重算；禁止用current重算prior或信任receipt自报。prior不自洽抛integrity error无result。

分支：无prior→NEW/INITIAL；key不同→NEW且source SAME/CHANGED；key相同后才比aggregate，相同→REUSED/SAME且current receipt、bindings tuple及members均以 `is` 复用prior；不同→TARGET_MISMATCH/SAME、empty bindings、current item receipts、exact issue `IDEMPOTENCY.DIGEST_MISMATCH @ /feedback/aggregate_target_digest`、无current receipt。same-key changed-target仅改变同raw identity authority graph content/digest。overwrite始终false。

## 13. validators、issues 与副作用

binding validator检查exact shapes/domains/tuple/refs/track/locator/七维/protocol graph/anchor/status/issues/digest。eligibility validator检查policy/status/time/binding digest、eligible RULE/exclusions/no reasons、noneligible empty targets/exclusions/nonempty reasons、fresh issues/content digest。

唯一producer issue pair 模式：validated submission 的 `feedback_items` tuple 保持原顺序逐项生成 canonical bindings tuple，不得按 item ID 或其他字段重排；对其中实际零基索引为 `i` 的 item，逐项 issue path 必须分别为 `FEEDBACK.TARGET_UNBOUND @ /feedback_bindings/{i}`、`FEEDBACK.REVISION_MISMATCH @ /feedback_bindings/{i}/revision_match`、`FEEDBACK.TRACK_MISMATCH @ /feedback_bindings/{i}/track_match`。因此 `i` 同时是该 item 在 validated submission tuple 与最终 bindings tuple 中的索引，不得对所有 item 固定为 `0`。operation-level pair 仍唯一固定为 `IDEMPOTENCY.DIGEST_MISMATCH @ /feedback/aggregate_target_digest`。不得新增 issue code 或其他 path family。

未来 [`engine/f09/feedback.py`](../engine/f09/feedback.py) 只导入标准库与五个冻结owner模块；禁止filesystem/network/process/database/queue/tools feedback/learning repository/writer/iteration；不得调用系统时钟。

## 14. static accounting：12 + 70 = 82

唯一测试文件 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py)。collection恰12个non-param structural nodes加一个70-ID参数测试，共82；禁止额外node、duplicate ID或hidden generation。

### 14.1 structural nodes

- S01 `test_public_dataclass_shapes_are_exact`：全部public shapes/field order/annotation/frozen。
- S02 `test_public_unions_aliases_and_protocol_are_closed`：aliases、union、port、四签名、无policy参数。
- S03 `test_owner_types_are_reused_by_identity`：owner classes与JcsValue直接复用。
- S04 `test_malformed_top_level_raises_typed_error_without_result`：顶层/ID/duplicate typed error。
- S05 `test_every_nested_dereference_is_guarded`：adversarial getter在guard前不可触达。
- S06 `test_canonicalization_is_bounded_jcs_only`：bounded token/rejections；blank payload合法。
- S07 `test_all_digest_preimages_are_complete_and_sensitive`：全部named material；statement/set exact owner fields、nested refs、exclusion与private-helper static oracle；manifest严格public records digest且owner digest对records敏感、对manifest ID/key/state/issues不敏感；无envelope替代；key分账；每item digest。
- S08 `test_prior_and_current_recompute_from_independent_raw_authorities`：两侧独立；same stable key可changed aggregate。
- S09 `test_reused_returns_prior_bindings_by_identity`：receipt/tuple/members机械复用。
- S10 `test_policy_trust_boundaries_are_independent_and_not_caller_signed`：双policy独立。
- S11 `test_no_side_effect_import_or_runtime_surface`：禁止import/filesystem/learning触达。
- S12 `test_static_accounting_is_exactly_12_plus_70`：12、P01..P70、82。

### 14.2 P01–P70

- P01 Production完整→BOUND，六required MATCH/run N/A，三refs+RULE，receipt。
- P02 PREPROD snapshot-only→BOUND，case/track/run/digest MATCH，三N/A。
- P03 两item同序：index 0为issue-free控制项，index 1 unknown statement→UNBOUND；bindings数量与validated items相等且逐索引feedback item identity一致，index 1 exact issue `FEEDBACK.TARGET_UNBOUND @ /feedback_bindings/1`。P04 missing revision→UNBOUND/UNKNOWN。P05 两item同序：index 0为issue-free控制项，index 1 old revision→UNBOUND/MISMATCH；数量及逐索引identity同P03，index 1 exact issue `FEEDBACK.REVISION_MISMATCH @ /feedback_bindings/1/revision_match`。
- P06 duplicate candidates→AMBIGUOUS；P07 malformed statement ref→INVALID/guarded；P08 statement owner digest mismatch→INVALID，并证明revision ID与content digest排除语义；P09 statement contract mismatch→INVALID。
- P10 set case mismatch→UNBOUND；P11 set track mismatch→UNBOUND；P12 set owner digest mismatch→INVALID，并证明set仅排除content digest且nested statement full material敏感；P13 set contract mismatch→INVALID。
- P14 records artifact missing→UNBOUND；P15 duplicate→AMBIGUOUS；P16 nonverified→UNBOUND；P17 expected missing→UNBOUND；P18 observed missing→UNBOUND；P19 digest unequal→UNBOUND；P20 record dimensions mismatch→独立/UNBOUND；P21 ref/artifact ID mismatch→INVALID；P22 projection type invalid→INVALID；P23 projection identities mismatch→INVALID；P24 projection digests mismatch→INVALID。
- P25 anchor missing→UNBOUND；P26 multiple→AMBIGUOUS；P27 unsupported/none→UNBOUND；P28 empty rules→INVALID；P29 duplicate rules→INVALID；P30 selected absent→INVALID；P31 selected twice→INVALID；P32 nonanchor order错误→INVALID；P33 source-order digest mismatch→INVALID；P34 selected非RULE→INVALID；P35 rule contract mismatch→INVALID。
- P36 metadata missing→UNBOUND/INELIGIBLE；P37 multiple→AMBIGUOUS/HUMAN_REVIEW；P38 blank identity→INVALID；P39 UNMAPPED→UNBOUND/INELIGIBLE；P40 source/digest/version mismatch→INVALID。
- P41 resolved track same→MATCH。P42 两item同序：index 0为issue-free控制项，index 1 resolved track different→MISMATCH；bindings数量与validated items相等且逐索引feedback item identity一致，index 1 exact issue `FEEDBACK.TRACK_MISMATCH @ /feedback_bindings/1/track_match`。P43 source missing→UNKNOWN/UNBOUND；P44 target unparsable→UNKNOWN/UNBOUND；P45 ambiguous source→AMBIGUOUS；P46 integrity failed→INVALID；P47 resolved with reason→INVALID；P48 wrong reason→INVALID；P49 source side/track/parser mismatch→INVALID；P50 target side错误→INVALID。
- P51 payload digest mismatch或malformed locator→INVALID/no resolver；P52 canonical pointer missing/scalar→UNBOUND且blank root正例。
- P53 PREPROD missing run→UNBOUND；P54 snapshot missing/multiple→UNBOUND/INVALID；P55 duplicate refs/roles→INVALID；P56 mixed dimensions→独立fail closed；P57 ref/record mismatch或forbidden→INVALID；P58 optional decision run→仍BOUND规范顺序；P59 PREPROD eligibility→INELIGIBLE。
- P60 双policy正例→各验自身且ELIGIBLE一RULE/ordered exclusions；P61 feedback policy禁止→INELIGIBLE；P62 caller policy注入→拒绝或忽略；P63交换policy/provider→失败或零调用；P64 Production ambiguous→HUMAN_REVIEW；P65 invalid/unknown track→INELIGIBLE/HUMAN_REVIEW。
- P66 initial→NEW/INITIAL；P67 changed source/key→NEW/CHANGED；P68 raw revision变化→key变化/NEW；P69 same key+same aggregate→REUSED/SAME/identity复用；P70 raw identity稳定仅合法target graph content变化→same key+different aggregate/TARGET_MISMATCH，唯一 exact operation-level issue `IDEMPOTENCY.DIGEST_MISMATCH @ /feedback/aggregate_target_digest`，不得使用任一 `/feedback_bindings/{i}` item-local path，且no overwrite。

P01–P07/P51–P57均断言非BOUND也有status-tagged target material；P03/P05/P42以既有三个ID机械关闭多item同序一一映射、非零索引与三类item-local issue paths；P08/P12与S07关闭statement/set owner digest；S07同时独立关闭manifest records digest；P60/P63关闭双policy；P68–P70关闭stable key/target分账，P70另关闭operation-level固定path与item-local path隔离。IDs连续且恰70。

## 15. focused selector、regressions、STOP 与 falsifiers

focused selector保持不变：`python -m pytest tests/f09/test_feedback_eligibility.py -q`，期望82 passed。三个regression nodeids保持不变：

1. `tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_h3_standard_list_schema_without_rule_ids_is_blocked_from_learning`
2. `tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_ingest_includes_v5_feedback_attachment_summary_without_unblocking_learning`
3. `tests/test_phase_a_minimal_learning_loop.py::test_statement_record_enforcement_marks_missing_as_unmapped`

期望3 passed；本drafting gate不运行。

实施STOP条件：需改白名单外文件；owner shape/helper exclusion/public digest API漂移；需调用private owner helper；需I/O/learning/writer/caller policy；无法guard-before-deref；需新增状态/disposition；collection非82；focused/regression冲突。

机械falsifiers：statement/set不存在字段；statement content digest包含revision/self；set digest包含self或未完整嵌入nested statements；调用owner private digest helper；manifest.digest包含manifest ID/key/state/issues；不用或替代public records digest；把可选envelope当owner digest；key包含target-sensitive digest；item缺digest；policy共用identity；raw ID降级；nested材料反射；DigestMissing被dereference；blank payload拒绝；prior未独立重算；REUSED重建；七维倒推；PREPROD读取Production；supporting rule成为target；noneligible暴露target；产生副作用；任一 AnchorPolicy 或 EligibilityPolicy 的 R33 runtime token被改为R36；R36治理 revision进入任何runtime policy digest/ref、schema-contract digest、canonical operation key或其他runtime material。任一命中即否证符合R36。

## 16. closure、non-regression 与 remaining unknown

### revision closure

- R33 关闭两个实质 blocker：B1 冻结当前 [`StandardStatement`](../engine/f09/trace.py:146) 与 [`StatementSet`](../engine/f09/trace.py:174) actual fields、owner helper exclusion及逐字段 fallback；B2 将 manifest owner验证严格限定为 public [`digest_artifact_records()`](../engine/f09/artifacts.py:241) 的 records digest。
- R34 只修正 `standard_statement_full_owner_material` 从错误“22字段”到正确“全部24字段”的计数，未改变字段序列或运行时语义；但它保留错误的 R33 文档 identity，故 R34 合同治理状态及针对它的先前 PASS 均因该矛盾失效。
- R35 完整继承 R33 已关闭的两个实质 blocker、R34 的24字段计数修正及全部既有运行时语义，并关闭文档代际与 runtime policy identity 分层问题；其后因多 item 的 item-local issue path 固定为索引 `0` 而失效。
- R36 仅冻结 validated submission item tuple 与 canonical bindings tuple 的同序一一映射，并将三类 item-local producer issue path 收敛为该实际零基索引 `i`；operation-level digest mismatch path、runtime R33 policy identity及其他业务合同均不变。

### non-regression

R33已关闭边界全部保持：stable key/target分账、ItemTargetReceipt、双policy、item identity envelope、DigestMissing sort、blank payload、prior/current独立、REUSED identity、Production/PREPROD协议、七维、metadata/selected RULE/exclusions、三态eligibility、zero side effects、exact public shapes。两套runtime policy的version/schema/contract/object/revision/locator、语义ID及captured_at全部保持R33原值；`standard_statement_full_owner_material` 保持全部24字段及原序；所有digest算法、preimage、self-exclusion与key材料保持不变。12 structural + P01–P70 = 82不变；focused selector及三个regression nodeids不变；未来实现白名单、STOP与零副作用边界不变。

### remaining unknown

仅剩当前实现草案整改与针对 R36 的独立执行证据：现有草案尚未通过 STATIC_REVIEW，82-case collection/通过、三个regression通过及R36 fresh reviewer接受均未由本文证明。Production metadata持久化来源仍无Task 1–7 port，本合同继续以完整重摘要的内存 `RuleMetadataReceipt` 为输入证据，不要求常量，不构成阻断unknown。当前无其他阻断unknown。

---

**当前状态：R35 的先前 CONTRACT PASS 已因多 item issue path 缺口失效；R36 等待独立 fresh review，本文不自授 PASS，也不作任何 CONTRACT verdict。**
