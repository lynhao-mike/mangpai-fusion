# G6 Task 8 R38 CONTRACT — Feedback Binding and Learning Eligibility Without Learning

## 0. 文档状态与治理边界

- 角色：Contract Analyst。本文件是 Task 8 唯一且完整的规范 revision R38。任何历史 revision、PI、M2/M3、旧 obligation、旧实现或旧 review 均无规范效力，且不得用于补充、覆盖、排序或解释本文；本文未明确规定的行为一律不得由历史材料推断。
- R38 关闭的合同缺口是：outer identity envelope 与 raw submission identity 已通过后，nested target authority malformed 时，[`bind_feedback_operation()`](../engine/f09/feedback.py:1231) 必须返回 [`ValidFeedbackOperationResult`](../engine/f09/feedback.py:262)，全部 item 为 `INVALID / INVALID_MATERIAL / empty graph`，不得抛 typed error、不得返回 [`InvalidFeedbackOperationResult`](../engine/f09/feedback.py:274)、不得留下 digest/key 选择空间。
- R38 同时修订 P40 metadata coherence 与 P57 PREPROD ref/record acceptance；不新增 public shape、状态、disposition、结构测试节点或 P-ID。
- fresh CONTRACT review 接受前禁止实现、创建测试或运行测试。本次 drafting 不运行命令、pytest、compile、import、CLI、script、Git 或 GitHub mutation。
- 唯一未来实现白名单：[`engine/f09/feedback.py`](../engine/f09/feedback.py:1) 与 [`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py:1)。Task 1–7 owner 冻结：[`engine/f09/contracts.py`](../engine/f09/contracts.py:1)、[`engine/f09/trace.py`](../engine/f09/trace.py:1)、[`engine/f09/artifacts.py`](../engine/f09/artifacts.py:1)、[`engine/f09/canonical_json.py`](../engine/f09/canonical_json.py:1)、[`engine/f09/errors.py`](../engine/f09/errors.py:1) 均不得修改。
- Task 8 只计算 binding 与 eligibility：零文件 I/O、零 repository/writer/learning/iteration side effect、零系统时钟隐式读取。

## 1. 权威与完整 owner/public surface

本文件的规范文字与其明确链接的当前 owner exact runtime identities共同构成完整权威；链接仅确认被点名 owner 类型的现有字段与closed member，不引入任何其他文件的业务语义。发生冲突时不得自行选择或借历史材料解释，必须STOP并返回CONTRACT revision。owner identity包括 [`RunTrack`](../engine/f09/contracts.py:21)、[`DigestRef`](../engine/f09/contracts.py:78)、[`DetectedIssue`](../engine/f09/contracts.py:582)、[`VersionedObjectRef`](../engine/f09/trace.py:53)、[`SnapshotRef`](../engine/f09/trace.py:65)、[`StandardStatement`](../engine/f09/trace.py:146)、[`StatementSet`](../engine/f09/trace.py:174)、[`IdempotencyKey`](../engine/f09/artifacts.py:48)、[`ArtifactRecord`](../engine/f09/artifacts.py:87)、[`ArtifactSetManifest`](../engine/f09/artifacts.py:113)、[`F09ContractError`](../engine/f09/errors.py:29)与[`F09IntegrityError`](../engine/f09/errors.py:21)。本文全部“typed contract error”均且仅指 exact [`F09ContractError`](../engine/f09/errors.py:29)，全部“typed integrity error”均且仅指 exact [`F09IntegrityError`](../engine/f09/errors.py:21)；不得替换为其共同基类、其他异常或新增错误类型。R38不复制或修改owner类型。

[`engine/f09/feedback.py`](../engine/f09/feedback.py:1) 的 public dataclass exact field order 为：

- [`TrackSourceBinding`](../engine/f09/feedback.py:47)：`track_source_binding_id, side, track, state, source_evidence_ref, parser_ref, schema_version, contract_version, content_digest, state_reason_codes, captured_at`。
- [`FeedbackItem`](../engine/f09/feedback.py:62)：`feedback_item_id, feedback_id, source_span_locator, target_statement_id, target_statement_revision_id, target_run_id, target_prediction_id, verdict, annotation, integrity, issue_ids`。
- [`FeedbackSubmission`](../engine/f09/feedback.py:77)：`feedback_id, case_id, track, track_source_binding, source_snapshot_ref, source_snapshot_payload, parser_id, parser_version, feedback_items, content_digest, captured_at`。
- [`StatementProjectionRecord`](../engine/f09/feedback.py:92)：`projection_id, projection_type, statement_set_id, statement_id, statement_revision_id, source_statement_digest, projected_object_ref, transformation_id, fidelity, dropped_refs, synthesized_fields, issue_ids`。
- [`AnchorSelectionRecord`](../engine/f09/feedback.py:108)：`anchor_selection_id, statement_id, statement_revision_id, all_rule_refs, selected_anchor_rule_ref, non_anchor_rule_refs, selection_policy_id, selection_policy_version, source_order_digest, fidelity, fanout_scope, issue_ids`。
- [`FeedbackBinding`](../engine/f09/feedback.py:124)：`feedback_binding_id, feedback_item_ref, binding_protocol, source_track_binding_ref, target_track_source_binding, case_match, track_match, run_match, statement_match, revision_match, statement_set_match, artifact_digest_match, target_object_refs, record_anchor_ref, status, issue_ids, detected_issues, content_digest`。
- [`GoverningVersions`](../engine/f09/feedback.py:146)：`statement_contract_version, statement_set_contract_version, statement_records_contract_version, rule_contract_version`。
- [`RuleMetadataReceipt`](../engine/f09/feedback.py:154)：`rule_ref, family_id, school, canon, rule_type, metadata_schema_version, metadata_contract_version, source_ref, content_digest, captured_at`。
- [`ProductionStatementAuthority`](../engine/f09/feedback.py:168)：`statement_set, manifest, statement_refs, statement_set_ref, records_projection_refs, records_projection_records, anchor_selections, rule_metadata_receipts, governing_versions, content_digest`。
- [`PreprodRunAuthority`](../engine/f09/feedback.py:182)：`case_id, track, run_id, manifest, target_refs, content_digest`。
- [`AnchorPolicy`](../engine/f09/feedback.py:192)：`policy_id, policy_version, required_rule_object_type, required_fidelity, required_fanout_scope, schema_version, contract_version, content_digest`。
- [`EligibilityPolicy`](../engine/f09/feedback.py:204)：`policy_id, policy_version, allowed_track, required_feedback_policy, human_review_on_ambiguous, human_review_on_invalid, human_review_on_unknown_track, schema_version, contract_version, content_digest`。
- [`RawFeedbackAuthority`](../engine/f09/feedback.py:218)：`raw_submission, target_authority, target_track_source_binding, captured_at`。
- [`ItemTargetReceipt`](../engine/f09/feedback.py:226)：`feedback_item_id, protocol, target_statement_id, target_statement_revision_id, target_run_id, target_prediction_id, resolution_status, non_bound_category, graph, graph_digest, content_digest`。
- [`FeedbackOperationReceipt`](../engine/f09/feedback.py:241)：`operation_id, key, source_digest, authority_digest, item_target_receipts, aggregate_target_digest, bindings, anchor_policy_ref, eligibility_policy_ref, created_at, content_digest`。
- [`PriorFeedbackOperation`](../engine/f09/feedback.py:256)：`raw_authority, receipt`。
- [`ValidFeedbackOperationResult`](../engine/f09/feedback.py:262)：`valid, operation_disposition, source_identity_relation, prior_receipt, current_receipt, bindings, overwrite_permitted, detected_issues`。
- [`InvalidFeedbackOperationResult`](../engine/f09/feedback.py:274)：`valid, operation_disposition, source_identity_relation, prior_receipt, current_key, prior_aggregate_target_digest, current_aggregate_target_digest, item_target_receipts, bindings, overwrite_permitted, detected_issues`。
- [`LearningEligibility`](../engine/f09/feedback.py:289)：`eligibility_id, feedback_binding_id, feedback_binding_digest, policy_id, policy_version, status, learning_target_refs, excluded_supporting_rule_refs, blocking_reason_codes, detected_issues, evaluated_at, content_digest`。

Closed aliases/domains不得扩张：binding protocol只有 `PRODUCTION_STATEMENT | PREPROD_RUN_TARGET`；binding status只有 `BOUND | UNBOUND | AMBIGUOUS | INVALID`；required match只有 `MATCH | MISMATCH | UNKNOWN`；optional match另允许 `NOT_APPLICABLE`；eligibility只有 `ELIGIBLE | INELIGIBLE | HUMAN_REVIEW`；non-bound category只有 `INVALID_MATERIAL | AMBIGUOUS_CANDIDATES | TARGET_NOT_FOUND | SOURCE_SPAN_NOT_FOUND | TRACK_UNRESOLVED | REQUIRED_MATCH_FAILED | PROTOCOL_GRAPH_INCOMPLETE`；PREPROD role只有 `RUN_SNAPSHOT | DECISION_RUN | FEEDBACK_ATTACHMENT | MANIFEST`。[`FeedbackOperationResult`](../engine/f09/feedback.py:304) 精确为 valid/invalid result 的 closed union；[`FeedbackClockPort`](../engine/f09/feedback.py:308) 只有 `now() -> str`。

四个 public signatures固定为：

```python
def bind_feedback_operation(current: RawFeedbackAuthority, *, prior: PriorFeedbackOperation | None, clock: FeedbackClockPort) -> FeedbackOperationResult
def validate_feedback_binding_record(binding: FeedbackBinding) -> None
def evaluate_learning_eligibility(binding: FeedbackBinding, *, production_authority: ProductionStatementAuthority | None, clock: FeedbackClockPort) -> LearningEligibility
def validate_learning_eligibility(eligibility: LearningEligibility) -> None
```

不得新增 malformed-authority result/member/field、caller policy/provider或 public helper。

## 2. 通用 exact 规则与 failure classification

### 2.1 bounded JCS

所有 Task 8 canonical digest 只调用 [`bounded_jcs_sha256()`](../engine/f09/canonical_json.py:251)：token 精确为 `sha256` 与 `RFC8785-JCS-UTF8`，value 为 lowercase 64-hex。材料值域仅 exact null、bool、Unicode scalar string、tuple array 与字符串键 exact dict；拒绝 number、list、自定义对象、非字符串键、surrogate、duplicate key、BOM、cycle、mutation与深度超过64。raw bytes 只由 [`parse_bounded_jcs()`](../engine/f09/canonical_json.py:215) 解析，绝不直接进入 JCS material。dict key canonical order由 bounded JCS按 UTF-16BE决定；tuple保留调用者给定顺序。

每个领域对象必须使用第5节列出的有名 material；runtime实现、public validator与canonical material构造均禁止 reflection、`dataclasses.asdict`、`repr`、`str(object)`、`vars()`、`__dict__`、`dataclasses.fields()`、`__dataclass_fields__`、隐式 dataclass field walking及 owner private canonicalizer。Enum只嵌入 `.value`。唯一不属于 reflection 的runtime字段存在性机制是：在 exact class guard 成功后，仅可对本文相应 public dataclass 明确列出的 literal field name 逐字段调用 `getattr(value, "literal_field_name", private_missing_sentinel)`；返回该私有 sentinel 只表示 constructor-bypass 实例缺少该具名字段，必须在任何正常 dereference、coherence 或 material 构造前按第2.2节分类。禁止动态字段名、循环或批量探测、字段枚举、元数据读取、以该机制推导 schema/material，亦禁止把 sentinel 本身、字段存在性或探测结果写入任何 canonical material。所有 material 仍须由第5节逐字段手写的 closed-schema dict/tuple 构造。S01测试唯一例外是只为静态核对第1节public dataclass declaration exact field order而读取类级dataclass field metadata；该静态读取不得被runtime代码调用，不得生成fixture、parameter case、schema或material，也不得替代S05的显式constructor-bypass fixtures。

exact nonblank `str` 适用于非 nullable identity/version/time/locator/type/code/path、digest token/value、policy identity及本文明确标记的 constant/member；nullable identity只能是 null 或 nonblank exact string。一般 payload string与 `annotation` 可 blank；`source_snapshot_payload=""` 合法。

### 2.2 outer、nested 与 prior failure 三分法

1. Outer identity envelope：`current` 必须 exact [`RawFeedbackAuthority`](../engine/f09/feedback.py:218)，且其四个声明字段 `raw_submission, target_authority, target_track_source_binding, captured_at` 必须先分别通过第2.1节唯一允许的 literal-name presence guard；任一字段缺失均属于 outer failure。四字段齐全后，`raw_submission` exact bytes；`target_authority` exact Production 或 PREPROD authority；`target_track_source_binding` exact [`TrackSourceBinding`](../engine/f09/feedback.py:47)；clock实现 port；`captured_at` exact nonblank。任一失败抛 typed [`F09ContractError`](../engine/f09/errors.py:29)，无 result。exact class 的 `RawFeedbackAuthority.__new__()` constructor-bypass 实例不因 class identity 获得字段完整性推定，也不得泄漏原生 `AttributeError`。
2. Raw submission identity：raw bytes经 bounded JCS解析；顶层/nested exact keys/tags、必需 identity/time/version、`feedback_items` exact tuple、每项 exact dict、item ID exact nonblank且无 duplicate；构造 [`FeedbackSubmission`](../engine/f09/feedback.py:77)。submission self digest、source snapshot payload digest及 submission-side track binding self digest独立重算。任一 shape/contract失败抛 typed contract error，任一 digest/self-integrity失败抛 typed integrity error，均无 result。
3. Target binding prerequisite：前两类成功后、验证任何target authority nested字段之前，`target_track_source_binding`必须通过exact [`TrackSourceBinding`](../engine/f09/feedback.py:47)字段、`side=BINDING_TARGET`、exact owner RunTrack、两个VersionedObjectRef完整shape、schema/contract/captured-at nonblank、第2.3节五状态—reason exact tuple以及self digest重算。shape/tag/domain/nonblank/state-reason失败抛typed contract error；self digest或nested digest完整性失败抛typed integrity error；均无result。`state=INTEGRITY_FAILED`配exact `(TRACK_SOURCE_INTEGRITY_FAILED,)`是结构与self-integrity均合法的业务状态，不触发typed error，后续按每项precedence返回INVALID。若target binding prerequisite与target authority同时失败，必须先执行本项并抛本项typed error；不得进入invalid-authority family、不得构造receipt，也不得由authority失败遮蔽。
4. Nested target authority：前三类成功后，protocol已由 outer `target_authority` 的 exact class唯一确定。该 exact Production/PREPROD authority 的每个声明字段及其 nested exact-class object 的每个声明字段，均不因 class identity 获得字段完整性推定；必须按第2.1节使用相应 literal-name presence guard。分类只能按下列closed、互斥phase matrix执行；同一predicate只允许出现于一行，禁止以“coherence”“malformed”或历史实现为由跨行重分类：

   | phase | 充要predicate闭集 | 明确排除 | failure结果 |
   |---|---|---|---|
   | A0 authority envelope | exact Production/PREPROD authority自身第1节全部声明字段的literal presence | 任一nested值的shape、digest或关系 | invalid-authority family，all items `INVALID / INVALID_MATERIAL / empty graph` |
   | A1 normal-material structural closure | 第5节normal authority material递归实际嵌入的nested exact-class对象全部声明字段presence；exact class；scalar exact type/tag/nullability/nonblank/closed-domain；tuple exact type、member exact class、member-local字段shape；authority `VersionedObjectRef.digest_binding`在此只接受并完整验证exact `DigestPresent | DigestMissing` owner closed-union shape，合法`DigestMissing`的协议acceptance不在A1 | authority collection的duplicate、uniqueness或role cardinality（这些只在A3）；已通过owner union shape的digest binding是否满足协议要求Present（只在I）；statement/ref/projection/anchor/metadata或snapshot与某个item raw target的相等、候选数、required/optional match、graph completeness | 同上 |
   | A2 object-local integrity closure | 仅在A3已接受authority collection duplicate/role cardinality后，使用已通过A1全部shape检查的对象自身self-excluded named material重算digest；`StatementSet`/`StandardStatement` owner digest；supplied `ArtifactSetManifest.digest`与public `digest_artifact_records(manifest.records)`重算结果完整相等；authority tuple依第5节排序后重算authority自身self digest | 任何exact class、presence、scalar/tuple/member shape（这些只在A1）；任何authority collection duplicate、uniqueness或role cardinality（这些只在A3）；任何以某个item raw target选择出的statement/ref/record/anchor/metadata为一端的比较；snapshot-to-record比较 | 同上 |
   | A3 authority-local identity closure | 不读取任一item raw target即可判定的固定协议事实，且仅含：Production authority的statement set `case_id/track`与authority协议要求；Production五类authority collection按第5节逐类冻结的exact duplicate prohibition；PREPROD authority `case_id/run_id` nonblank、`track is V5_V6_PREPROD`、target role闭集及每role cardinality至多一（required RUN_SNAPSHOT缺失除外） | manifest records及其nested member的presence/exact class/字段shape/domain（只在A1）；supplied manifest `digest`与public records digest重算结果的比较（只在A2）；Production同协议候选identity但完整member material不等所形成的multiple/mismatch、required RUN_SNAPSHOT是否存在、record是否成为某请求ref候选及全部第6、7节关系（只在I） | 同上 |
   | I item-resolution | 仅在A0、A1、A3、A2依该顺序全部成功后，由一个validated `FeedbackItem`的四个raw target identity或PREPROD required RUN_SNAPSHOT存在性发起的第6、7节closed predicates：target identity protocol shape、候选选择/数量、target existence、七维match、statement/ref/set relation、projection、artifact relation、anchor relation、P40 metadata relation、snapshot-to-record relation、graph completeness | A0–A3任一predicate | 仅该item按第6.2节及对应P-ID得到`INVALID / UNBOUND / AMBIGUOUS / BOUND`；绝不进入invalid-authority family |

   A0→A1→A3→A2→I为唯一执行顺序；phase名称不是数字执行顺序。A1完成全部member/material shape validation；A3随后完成authority collection duplicate detection、uniqueness与role cardinality acceptance；只有A3成功后，A2才按第5节定义的唯一sort key排序已接受tuple并重算object/authority digest。进入I即表示整个authority已依该顺序通过A0、A1、A3、A2，I中不得再次把owner字段缺失、owner self digest或authority-local duplicate判为item-local。manifest records的member-local presence/exact class/shape/domain只在A1判定，supplied manifest `digest`与public records digest重算结果的完整比较只在A2判定；A3不检查任何manifest record member-local事实；record与请求ref/case/track/run/set/state/schema/digest的candidate-filter关系只在I判定。反之，A0–A3不得比较任何item的`target_statement_id/target_statement_revision_id/target_run_id/target_prediction_id`，不得预先执行projection/anchor/P40/snapshot candidate relation。`ProductionStatementAuthority.__new__()`、`PreprodRunAuthority.__new__()`及A1 closed class set内nested exact class的constructor-bypass实例分别在A0或A1失败。不得构造partial normal authority material；不得让原生`AttributeError`或其他异常越过public bind boundary。由于target binding prerequisite已通过，第8.1节可原样嵌入该合法对象并由同一validator接受。
5. Prior receipt：prior与current分别从各自 raw authority独立计算。prior outer/raw/target-binding prerequisite失败依第1至3项抛 typed error；prior receipt、key、target receipt、binding、aggregate、operation digest或其声明与重算不一致，抛 typed integrity error，无 result。不得把 malformed prior receipt降级为业务状态，也不得用current修补prior。
6. 对每个validated submission item，唯一item执行序列为：先按第6、7节对应protocol的字段列举顺序校验四个raw target identity closed shape；任一shape失败立即且唯一返回该item `INVALID / INVALID_MATERIAL / empty graph`，不得先读取target binding业务状态。仅shape全部成功后，通过prerequisite的target binding才按状态分流：`INTEGRITY_FAILED → INVALID / INVALID_MATERIAL / empty graph`；`AMBIGUOUS → AMBIGUOUS / AMBIGUOUS_CANDIDATES / empty graph`；`SOURCE_MISSING | UNPARSABLE → UNBOUND / TRACK_UNRESOLVED / empty graph`；只有`AVAILABLE_RESOLVED`继续第6、7节其余target resolution predicates。因而raw target shape失败机械优先于任一合法target-binding业务状态，target-binding业务状态又优先于candidate selection、relation或graph判断；第6.2节的item-local precedence只描述本唯一序列，不得反向解释。每次正常 dereference前必须依次完成 exact class guard与第2.1节 literal-name presence guard；presence guard 返回私有 sentinel 时不得继续读取该字段。禁止捕获 `AttributeError`、`KeyError`、`IndexError`模拟字段缺失或业务状态。

### 2.3 raw submission wire schema（完整且封闭）

raw submission是bounded JCS object；解析后每个JSON array均为exact tuple。以下每层object都必须含且仅含列出的keys，禁止additional field、缺字段、别名、未知tag、list、自定义对象或隐式默认值：

- 顶层exact keys：`feedback_id, case_id, track, track_source_binding, source_snapshot_ref, source_snapshot_payload, parser_id, parser_version, feedback_items, content_digest, captured_at`。`feedback_id, case_id, parser_id, parser_version, captured_at`为exact nonblank string；`track`为exact owner [`RunTrack`](../engine/f09/contracts.py:21) value；`track_source_binding`、`source_snapshot_ref`、`content_digest`分别使用下述唯一schema；`source_snapshot_payload`为任意bounded JCS value；`feedback_items`为exact tuple，允许空tuple；其member仅为下述feedback item。
- track binding exact keys：`track_source_binding_id, side, track, state, source_evidence_ref, parser_ref, schema_version, contract_version, content_digest, state_reason_codes, captured_at`。`track_source_binding_id, schema_version, contract_version, captured_at`为exact nonblank string；submission内`side`必须exact `SUBMISSION_SOURCE`；`track`为exact owner RunTrack value且必须等于顶层track；`state`闭集含且仅含`AVAILABLE_RESOLVED | SOURCE_MISSING | UNPARSABLE | AMBIGUOUS | INTEGRITY_FAILED`；reason闭集含且仅含`TRACK_SOURCE_MISSING | TRACK_SOURCE_UNPARSABLE | TRACK_SOURCE_AMBIGUOUS | TRACK_SOURCE_INTEGRITY_FAILED`。状态—reason cardinality表唯一为：`AVAILABLE_RESOLVED → ()`；`SOURCE_MISSING → (TRACK_SOURCE_MISSING,)`；`UNPARSABLE → (TRACK_SOURCE_UNPARSABLE,)`；`AMBIGUOUS → (TRACK_SOURCE_AMBIGUOUS,)`；`INTEGRITY_FAILED → (TRACK_SOURCE_INTEGRITY_FAILED,)`。`state_reason_codes`必须逐值等于对应exact tuple，不允许额外、缺失、重复、重排或跨状态reason；`source_evidence_ref`与`parser_ref`均用versioned ref schema；`content_digest`用digest ref schema。`parser_ref.object_id == parser_id`且`parser_ref.revision_id == parser_version`。P43的missing只对应`SOURCE_MISSING/(TRACK_SOURCE_MISSING,)`；P44的unparsable只对应`UNPARSABLE/(TRACK_SOURCE_UNPARSABLE,)`，不得合并为第三状态。
- snapshot ref exact keys：`source_snapshot_id, source_type, source_locator_ids, schema_version, contract_version, content_digest, captured_at, immutability`。`source_snapshot_id, captured_at`为exact nonblank string；`source_type`必须exact `FEEDBACK`；`source_locator_ids`为无duplicate的exact nonblank string tuple；`schema_version, contract_version`各为null或exact nonblank string；`content_digest`用digest ref schema；`immutability`只能为`IMMUTABLE | MUTABLE_SOURCE_CAPTURE`。
- feedback item exact keys：`feedback_item_id, feedback_id, source_span_locator, target_statement_id, target_statement_revision_id, target_run_id, target_prediction_id, verdict, annotation, integrity, issue_ids`。`feedback_item_id, feedback_id, source_span_locator, verdict`为exact nonblank string；item `feedback_id`必须等于顶层feedback ID；四个target identity各为null或exact nonblank string；`annotation`为exact string且可blank；`integrity`只能为`VALID | INVALID | UNRESOLVED`；`issue_ids`为exact tuple，允许空tuple，但每个member必须是exact nonblank string且全tuple不得duplicate；同一submission的`feedback_item_id`不得duplicate。
- versioned ref exact keys：`object_type, object_id, revision_id, schema_version, contract_version, digest_binding, source_locator_id, captured_at`。`object_type, object_id, schema_version`为exact nonblank string；`revision_id, contract_version, source_locator_id, captured_at`各为null或exact nonblank string；`digest_binding`只允许下述两个tagged schema。
- present digest binding含且仅含`status, digest`，`status=PRESENT`，`digest`用digest ref schema。missing digest binding含且仅含`status, digest, issue_id`，`status=MISSING`、`digest=null`、`issue_id`为exact nonblank string。其他key组合、tag或null位置均非法。
- digest ref含且仅含`algorithm, canonicalization, value`；三者均为exact nonblank string，且必须分别为`sha256`、`RFC8785-JCS-UTF8`、lowercase 64-hex。

raw contract validation采用唯一 deterministic depth-first per-object 顺序，而非 whole-tree global phases：bounded JCS parse成功后，从顶层object开始，先校验当前object的exact keys；仅当exact keys成功后才读取并校验当前层tag；仅当tag成功后才按本节为该object列出的字段顺序逐字段校验exact scalar/tuple/member/nullability。遇到nested object或tuple member时立即递归，并以同一规则完整校验该child后才返回parent继续下一个字段；当前object全部child成功后才校验该object的cross-field identity/coherence。因而两个分支同时失败时，schema列举顺序中先被深度优先访问的分支决定首错；在同一object内exact-keys错误先于tag错误，tag错误先于该object的字段错误，但较早分支的字段错误先于较晚兄弟分支的exact-keys或tag错误。顶层及全部nested shape/contract/coherence成功后，digest阶段固定为snapshot payload digest → submission-side track binding self digest → submission self digest。shape/contract失败抛typed contract error，digest/self-integrity失败抛typed integrity error；任何失败均无result。字段访问顺序只能来自本节对应wire object的逐字段列举顺序；wire schema不得从public dataclass字段顺序、constructor默认、历史文档或当前实现反向补全。

## 3. raw resolver 与 pinned policies

raw locator唯一 grammar为 `source-snapshot-id#RFC6901-json-pointer`：恰一 `#`；snapshot ID逐值相同；fragment blank表示root，否则以 `/` 开始；只接受 `~0/~1`并要求decode后canonical re-encode相同；dict exact key；tuple index仅 `0` 或 `[1-9][0-9]*`；拒绝 `-`、正号、leading zero、wildcard、recursive descent、normalization、case fold与多候选搜索。malformed为INVALID；canonical路径不存在或scalar traversal为UNBOUND；成功恰一node。

R38治理revision与R33 runtime policy identities严格分层。Anchor policy固定为：ID `G6-TASK8-ANCHOR-SELECTION`、version `r33-anchor-v1`、schema `anchor-policy.r33.v1`、contract `g6-task8-r33-anchor`、object ID `POLICY:G6:TASK8:R33:ANCHOR`、revision `rev-r33-anchor-v1`、locator `engine.f09.feedback#PINNED_ANCHOR_POLICY_R33`、captured-at `2026-07-22T00:00:00Z`、type `RULE`、fidelity `LOSSY`、fanout `SELECTED_ANCHOR_ONLY`。

Eligibility policy固定为：ID `G6-TASK8-LEARNING-ELIGIBILITY`、version `r33-eligibility-v1`、schema `eligibility-policy.r33.v1`、contract `g6-task8-r33-eligibility`、object ID `POLICY:G6:TASK8:R33:ELIGIBILITY`、revision `rev-r33-eligibility-v1`、locator `engine.f09.feedback#PINNED_ELIGIBILITY_POLICY_R33`、captured-at `2026-07-22T00:00:00Z`、allowed track `PRODUCTION_DEFAULT`、required policy `FEEDBACK_ALLOWED`、booleans依次为 `True, False, True`。两policy每次从module-private immutable literals独立构造，不读caller/environment/filesystem/registry/provider。

`R38`、本文文件名、invalid-authority治理说明及任何contract-review identity均不得进入runtime policy digest/ref、schema/contract digest、operation key、receipt、binding或其他runtime material。

## 4. 唯一 invalid-authority material family

### 4.1 分类与 authority preimage

进入本family的充要条件是待计算的current或prior各自通过第2.2节第1、2、3项全部prerequisite，且该次计算的exact-class target authority在第2.2节第4项明确定义的authority-wide structural/material phase任一predicate失败；第6、7节item-resolution phase产生的`INVALID / UNBOUND / AMBIGUOUS`不是本family触发条件。current与prior逐次独立适用同一充要条件，任一方不得借另一方的成功补足prerequisite。若任一方第1、2或3项失败，必须依对应项抛其exact typed error且无result，不得进入本family；target binding prerequisite与target authority同时失败时仍由第3项优先。protocol只由outer exact class机械决定：Production class → `PRODUCTION_STATEMENT`；PREPROD class → `PREPROD_RUN_TARGET`。

`invalid_authority_material(protocol)` 是含且仅含四字段的exact dict：

```text
{
  material_domain: G6_TASK8_TARGET_AUTHORITY,
  material_version: invalid-authority.v1,
  authority_status: INVALID_MATERIAL,
  protocol: PRODUCTION_STATEMENT | PREPROD_RUN_TARGET
}
```

四个key/value均为exact nonblank Unicode scalar string；无null、number、list、nested object或运行时排序输入。材料不含malformed authority任一字段、caller-supplied digest、异常文本、失败路径、失败数量、partial normal material、sentinel key或deferred key。同一protocol下全部malformed nested authorities属于一个equivalence class。`authority_digest = bounded_jcs_sha256(invalid_authority_material(protocol))`。

### 4.2 malformed schema/contract preimages

`invalid_authority_schema_identity_material(protocol)` exact dict：

```text
{
  status: INVALID_MATERIAL,
  protocol: protocol,
  schema_version: null,
  rule_metadata_schema_version: null
}
```

`schema_versions_digest_material` exact dict：

```text
{
  submission: validated submission source_snapshot_ref.schema_version,
  track_source_binding: validated submission track_source_binding.schema_version,
  target_authority: invalid_authority_schema_identity_material(protocol),
  rule_metadata: null,
  anchor_policy: pinned anchor policy schema_version,
  eligibility_policy: pinned eligibility policy schema_version
}
```

`invalid_authority_contract_identity_material(protocol)` exact dict：

```text
{
  status: INVALID_MATERIAL,
  protocol: protocol,
  contract_version: null,
  governing_versions: [null, null, null, null]
}
```

方括号表示exact tuple，位置依次是statement、statement-set、statement-records、rule governing contract version，不排序、不补值。`contract_digest_material` exact dict：

```text
{
  submission: validated submission source_snapshot_ref.contract_version,
  track_source_binding: validated submission track_source_binding.contract_version,
  target_authority: invalid_authority_contract_identity_material(protocol),
  governing_versions: [null, null, null, null],
  anchor_policy: pinned anchor policy contract_version,
  eligibility_policy: pinned eligibility policy contract_version
}
```

`schema_versions_digest`与`contract_digest`分别为上述exact material的[`bounded_jcs_sha256()`](../engine/f09/canonical_json.py:251)；不得互填，current不得从prior填值，不得从malformed nested governing versions取值。

### 4.3 malformed canonical operation identity 与 stable key

先构造key-without-canonical-digest，exact [`IdempotencyKey`](../engine/f09/artifacts.py:48)字段和值为：`operation=BIND_FEEDBACK`；`case_id, track, feedback_id, source_digest`来自validated submission；`schema_versions_digest, contract_digest`来自第4.2节；`statement_set_id=null`；排除`canonical_key_digest`。其named material exact keys为 `operation, case_id, track, source_digest, schema_versions_digest, contract_digest, statement_set_id, feedback_id`。

`invalid_authority_operation_identity_material(protocol)` exact dict：

```text
{
  status: INVALID_MATERIAL,
  protocol: protocol,
  authority_schema_version: null,
  authority_contract_version: null,
  governing_versions: [null, null, null, null],
  statement_set_id: null
}
```

malformed-case `canonical_operation_identity_material` 是下列唯一exact dict schema；顶层不得增减字段：

```text
{
  key: key-without-canonical-digest named material,
  item_raw_identities: (
    {
      feedback_item_id: exact nonblank string from validated FeedbackItem.feedback_item_id,
      target_statement_id: exact null or nonblank string from validated FeedbackItem.target_statement_id,
      target_statement_revision_id: exact null or nonblank string from validated FeedbackItem.target_statement_revision_id,
      target_run_id: exact null or nonblank string from validated FeedbackItem.target_run_id,
      target_prediction_id: exact null or nonblank string from validated FeedbackItem.target_prediction_id
    },
    ...
  ),
  anchor_policy: (pinned anchor policy_id, pinned anchor policy_version),
  eligibility_policy: (pinned eligibility policy_id, pinned eligibility policy_version),
  submission_schema: validated submission source_snapshot_ref.schema_version,
  submission_contract: validated submission source_snapshot_ref.contract_version,
  authority_identity: invalid_authority_operation_identity_material(protocol),
  source_snapshot_digest: exact digest-ref material from validated submission source_snapshot_ref.content_digest,
  feedback_id: validated submission feedback_id,
  case_id: validated submission case_id,
  track: validated submission track enum value
}
```

`item_raw_identities`必须是exact tuple；每个member必须是含且仅含上述五个key的exact dict。tuple按`feedback_item_id`的UTF-16BE字节序升序；dict key ordering只由bounded JCS决定；tuple member内部无语义顺序。`submission_schema_version`与`submission_contract_version`是非法替代拼写，出现任一即合同失败；唯一合法拼写是`submission_schema`与`submission_contract`。禁止附加字段、normal authority material、supplied authority/manifest/statement/set/artifact/metadata digest、aggregate/graph/receipt digest、失败诊断、sentinel或deferred key。

`canonical_key_digest = bounded_jcs_sha256(canonical_operation_identity_material)`，然后填回唯一stable key。

## 5. 全部 named materials、normal digest 与 self-exclusion

下列材料是Task 8唯一材料。所有dict含且仅含列出的字段；嵌套owner对象使用本节对应material；self-excluded对象先用不含自身digest的材料重算并验证，再在父材料明确要求时连同verified digest嵌入。

- `digest_ref = {algorithm, canonicalization, value}`；`digest_binding_present = {status, digest}`；`digest_binding_missing = {status, digest:null, issue_id}`。
- `versioned_ref = {object_type, object_id, revision_id, schema_version, contract_version, digest_binding, source_locator_id, captured_at}`。
- `snapshot_ref = {source_snapshot_id, source_type, source_locator_ids, schema_version, contract_version, content_digest, captured_at, immutability}`。
- `detected_issue = {issue_code, field_path}`。
- `track_binding_self_excluded = {track_source_binding_id, side, track, state, source_evidence_ref, parser_ref, schema_version, contract_version, state_reason_codes, captured_at}`。
- `feedback_item = {feedback_item_id, feedback_id, source_span_locator, target_statement_id, target_statement_revision_id, target_run_id, target_prediction_id, verdict, annotation, integrity, issue_ids}`。
- `submission_self_excluded = {feedback_id, case_id, track, track_source_binding, source_snapshot_ref, source_snapshot_payload, parser_id, parser_version, feedback_items, captured_at}`。
- `projection = {projection_id, projection_type, statement_set_id, statement_id, statement_revision_id, source_statement_digest, projected_object_ref, transformation_id, fidelity, dropped_refs, synthesized_fields, issue_ids}`。
- `anchor = {anchor_selection_id, statement_id, statement_revision_id, all_rule_refs, selected_anchor_rule_ref, non_anchor_rule_refs, selection_policy_id, selection_policy_version, source_order_digest, fidelity, fanout_scope, issue_ids}`。
- `governing_versions = {statement_contract_version, statement_set_contract_version, statement_records_contract_version, rule_contract_version}`。
- `metadata_self_excluded = {rule_ref, family_id, school, canon, rule_type, metadata_schema_version, metadata_contract_version, source_ref, captured_at}`。
- `anchor_policy_self_excluded = {policy_id, policy_version, required_rule_object_type, required_fidelity, required_fanout_scope, schema_version, contract_version}`。
- `eligibility_policy_self_excluded = {policy_id, policy_version, allowed_track, required_feedback_policy, human_review_on_ambiguous, human_review_on_invalid, human_review_on_unknown_track, schema_version, contract_version}`。
- `policy_digest_identity = {policy_id, policy_version, schema_version, contract_version, content_digest}`。
- manifest identity仅为`{records_digest}`；`records_digest`是该normal material的conceptual key，不是[`ArtifactSetManifest`](../engine/f09/artifacts.py:113)的owner字段名。其值必须是public [`digest_artifact_records()`](../engine/f09/artifacts.py:241)对supplied current `manifest.records` exact tuple的重算结果，且A2必须先验证supplied owner字段`manifest.digest`与该重算结果的`algorithm, canonicalization, value`全部逐值相等；只有验证后的重算结果可写入`records_digest`。manifest ID/key/state/issues及caller-supplied `manifest.digest`本身不进入records digest或manifest identity。
- Production authority self-excluded material为`{statement_set:{statement_set_id, content_digest}, manifest, statement_refs, statement_set_ref, records_projection_refs, records_projection_records, anchor_selections, rule_metadata_receipts, governing_versions}`；每个metadata member为`{material:metadata_self_excluded, content_digest}`。
- PREPROD authority self-excluded material为`{case_id, track, run_id, manifest, target_refs}`。
- binding self-excluded material为`{feedback_binding_id, feedback_item_ref, binding_protocol, source_track_binding_ref, target_track_source_binding, case_match, track_match, run_match, statement_match, revision_match, statement_set_match, artifact_digest_match, target_object_refs, record_anchor_ref, status, issue_ids, detected_issues}`；target track binding在该位置嵌入self-excluded material和verified `content_digest`。
- item target graph material为`{protocol, raw_target_identity:{target_statement_id, target_statement_revision_id, target_run_id, target_prediction_id}, resolution_status, non_bound_category, graph}`。
- item receipt self-excluded material为`{feedback_item_id, protocol, target_statement_id, target_statement_revision_id, target_run_id, target_prediction_id, resolution_status, non_bound_category, graph, graph_digest}`。
- aggregate target material是按item ID UTF-16BE排序的exact tuple；每项exact dict为`{feedback_item_id, protocol, resolution_status, graph_digest, item_target_receipt_content_digest}`。
- operation receipt self-excluded material为`{operation_id, key, source_digest, authority_digest, item_target_receipts, aggregate_target_digest, bindings, anchor_policy_ref, eligibility_policy_ref, created_at}`；每个item receipt与binding嵌入self-excluded material及verified `content_digest`。
- eligibility self-excluded material为`{eligibility_id, feedback_binding_id, feedback_binding_digest, policy_id, policy_version, status, learning_target_refs, excluded_supporting_rule_refs, blocking_reason_codes, detected_issues, evaluated_at}`。

下列nested owner named materials也是本节唯一材料，字段均含且仅含列举项；所有标注“string tuple”的值均为exact tuple，每个member为exact nonblank string，保留原顺序，不是dataclass、没有constructor-bypass class，也不属于S05 exact-class set：

- `frozen_declaration_ref = {declaration_id, declaration_type, card_id, contract_version, declaration_schema_version, content_digest}`；`content_digest`嵌入`digest_ref`。
- declaration binding是closed tagged union：Resolved为`{presence, ref}`；Absent/NotApplicable为`{presence, reason_code}`；Unavailable为`{presence, reason_code, issue_ids}`；Unresolvable为`{presence, attempted_ref, reason_code, issue_ids}`。`ref/attempted_ref`嵌入`frozen_declaration_ref`；presence、reason及nonempty issue tuple必须符合owner closed domain。
- `card_identity_ref = {card_identity_ref_id, card_id, normative_contract_ref, machine_appendix_ref, field_path, source_field_state, evaluator_state, declaration_status, runtime_capability_status, source_locator_ids, issue_ids}`；两个ref嵌入`versioned_ref`，两个tuple为string tuple，其余tag使用owner closed domain。
- `decision_trace_ref = {result_ref, action_id, selected_action, basis_record_ids, blocking_issue_ids, nonblocking_issue_ids, source_decision_refs, output_precision_binding, validation_plan_binding, structural_validity}`；仅`result_ref`嵌入`versioned_ref`；`basis_record_ids, blocking_issue_ids, nonblocking_issue_ids, source_decision_refs`四者全部为string tuple，member均为exact nonblank string，不递归引入`VersionedObjectRef`；两个binding嵌入上述closed union material，enum只嵌入`.value`。
- `idempotency_key = {operation, case_id, track, source_digest, schema_versions_digest, contract_digest, statement_set_id, feedback_id, canonical_key_digest}`；manifest owner shape检查使用全部字段，nullable位置遵循owner shape；该material不替代第4.3节及normal canonical operation identity中明确排除`canonical_key_digest`的key-without-canonical-digest材料。
- `artifact_write_attempt = {attempt_id, artifact_id, idempotency_key, attempt_number, retry_of_attempt_id, input_snapshot_refs, started_at, finished_at, outcome, observed_digest, error_class, error_message_digest}`；`attempt_number`仅在public [`digest_artifact_records()`](../engine/f09/artifacts.py:241)内部的既有records canonicalization出现，Task 8不得把number直接送入自身bounded JCS；nullable字段与ref/digest按owner shape。
- `artifact_record = {artifact_id, artifact_role, track, case_id, statement_set_id, run_id, path_locator, schema_version, expected_digest, observed_digest, state, attempts, issue_ids}`；attempts嵌入`artifact_write_attempt`，issue_ids为string tuple。`artifact_manifest_owner = {manifest_id, key, records, state, digest, detected_issues}`；key、records、digest、issues分别嵌入上述named material、`artifact_record`、`digest_ref`、`detected_issue`。这些owner materials仅冻结A1 presence/shape递归闭包；normal authority的manifest identity仍且仅为本节前述`{records_digest}`，其中`records_digest`只是material key且只能取A2已验证与supplied owner `manifest.digest`完整相等的public重算结果。records digest仍必须只调用public [`digest_artifact_records()`](../engine/f09/artifacts.py:241)，不得用这些展开材料另造records digest。

[`StandardStatement`](../engine/f09/trace.py:146) full owner material依次含全部24字段：`statement_id, statement_revision_id, statement_schema_version, case_id, statement_set_id, track, semantic_scope, domain, statement_text, display_section, decision_result_id, action_id, basis_record_ids, evidence_refs, relation_ids, source_locator_ids, card_identity_refs, confidence_snapshot_ref, output_precision_binding, validation_plan_binding, feedback_policy, content_digest, integrity, issue_ids`；`basis_record_ids, relation_ids, source_locator_ids, issue_ids`均为上述string tuple；`evidence_refs`嵌入`versioned_ref` tuple；`card_identity_refs`嵌入`card_identity_ref` tuple；nullable confidence ref嵌入null或`versioned_ref`；两个declaration binding嵌入上述closed tagged material。其owner content digest只排除`statement_revision_id`与`content_digest`。[`StatementSet`](../engine/f09/trace.py:174) owner content material字段为`statement_set_id, statement_schema_version, case_id, track, source_package_ref, decision_trace_ref, statements, generated_at, publication_state, issue_ids`，即只排除set的`content_digest`，分别嵌入`versioned_ref`、`decision_trace_ref`、statement full owner material tuple与string issue tuple。必须先在A1检查owner及全部nested exact shape，再在A2重算；不调用owner private helper。

Authority tuple处理严格服从A1→A3→A2：A1先完成exact member/material validation；A3再完成duplicate detection、uniqueness与role cardinality acceptance；A3成功后A2才排序并用排序结果构造authority self-excluded material。Production duplicate identity逐类含且仅含：`statement_refs`按完整`versioned_ref` named material逐值相等；`records_projection_refs`按完整`versioned_ref` named material逐值相等；`records_projection_records`按完整`projection` named material逐值相等；`anchor_selections`按完整`anchor` named material逐值相等；`rule_metadata_receipts`按`{material: metadata_self_excluded, content_digest}`完整member material逐值相等。这里“完整”包含相应第5节material列出的全部scalar、null、tuple、nested material及caller-supplied digest字段；A3只比较A1已验证shape的值，不在此验证或重算digest。任一tuple存在两个上述完整material逐值相等的members即A3 duplicate failure；该判定不使用sort key、object ID、statement/revision、rule ref或其他协议候选identity的局部相等。同协议候选identity相同但完整member material任一其余字段不同，不是A3 duplicate，必须保留到I按第6节产生multiple/mismatch，不得在A3吞并或择优。

A2 total order只使用A1已验证且A3已接受的值。`canonical_bytes(material)`唯一指[`canonicalize_bounded_jcs()`](../engine/f09/canonical_json.py:241)对第5节对应完整named material所得bytes；bytes按unsigned byte逐位lexicographic升序，较短且为另一bytes完整前缀者在前。exact nonblank string主键均先编码为UTF-16BE bytes并按同一unsigned lexicographic规则比较。逐类exact sort-key tuple为：`statement_refs → (canonical_bytes(versioned_ref),)`；`records_projection_refs → (object_id UTF-16BE bytes, canonical_bytes(versioned_ref))`；`records_projection_records → (projection_id UTF-16BE bytes, canonical_bytes(projection))`；`anchor_selections → (statement_id UTF-16BE bytes, statement_revision_id UTF-16BE bytes, canonical_bytes(anchor))`；`rule_metadata_receipts → (canonical_bytes(rule_ref versioned_ref), canonical_bytes({material:metadata_self_excluded, content_digest}))`。tuple positions依次lexicographic比较；最终完整canonical bytes保证任意两个非duplicate members有total order。null、`DigestPresent`与`DigestMissing`不另造rank：它们在完整named material中的exact JCS `null`或closed `status` string及对应字段自然进入canonical bytes；不得dereference Missing中的不存在digest。上述sort keys不定义或替代duplicate identity。

PREPROD `target_refs`只在A3确认每个role至多一个且无forbidden role后，sort-key exact为`(role_rank, canonical_bytes(versioned_ref))`，其中`RUN_SNAPSHOT=0, DECISION_RUN=1, FEEDBACK_ATTACHMENT=2, MANIFEST=3`；先按整数rank升序，再按canonical bytes unsigned lexicographic升序。role rank仅用于排序且不得进入bounded-JCS material；由于A3已关闭duplicate/forbidden role，A2不需要也不得定义fallback sort key。合法[`DigestMissing`](../engine/f09/trace.py:43)以其完整named material参与canonical bytes排序，不dereference不存在的digest。

Normal `schema_versions_digest_material` exact为`{submission, track_source_binding, target_authority, rule_metadata, anchor_policy, eligibility_policy}`；target authority值由exact class分别为`production-statement-authority.v1`或`preprod-run-authority.v1`；Production rule metadata值为governing rule contract version，PREPROD为null。Normal `contract_digest_material` exact为`{submission, track_source_binding, target_authority, rule_metadata, anchor_policy, eligibility_policy, statement_contract_version, statement_set_contract_version, statement_records_contract_version, rule_contract_version}`；PREPROD四个governing slot及rule metadata均null。

Normal canonical operation identity exact为`{key, item_raw_identities, anchor_policy, eligibility_policy, submission_schema, submission_contract, governing_versions, source_snapshot_digest, feedback_id, case_id, track, statement_set_id}`。其中key排除canonical digest；normal `item_raw_identities`是按item ID UTF-16BE排序的完整`feedback_item`材料tuple；policy各为`(policy_id, policy_version)`；Production governing versions为完整named material且set ID exact nonblank，PREPROD governing versions为四null exact tuple且set ID null。canonical key digest只排除自身；target authority/manifest/graph/aggregate/receipt digest不进入stable key。

四个关键preimage分别为authority material、schema versions material、contract material、canonical operation identity；四者不可互换。valid normal authority的上述字段、排序、null、digest和self-exclusion是byte-for-byte冻结对象；第4节invalid status/null/material不得进入valid normal bytes。本治理revision不证明任何历史实现常量正确，只冻结本节明确给出的normal runtime材料。

## 6. Production resolver、P40 与七维

Production只接受submission与authority track均为`PRODUCTION_DEFAULT`，authority statement set的case/track必须匹配。Production item target protocol shape含且仅含：`target_statement_id`必须exact nonblank；`target_statement_revision_id`为null或exact nonblank；`target_run_id`必须null；`target_prediction_id`必须null。按本顺序首个违反项唯一为I阶段`INVALID / INVALID_MATERIAL / empty graph`；禁止忽略、补值或把forbidden nonnull字段送入候选解析。shape通过后，每个item按raw statement ID选择恰一statement；revision为nullable optional维。statement与set owner digest必须依第5节独立重算。statement ref与statement set ref必须完整identity、schema、contract、present digest一致；governing四version均exact nonblank并分别约束statement、set、records projection与rule contract。

STATEMENT_RECORDS projection/ref必须形成完整一一对应identity：projection type、set ID、statement ID、revision ID、source statement digest、projected ref完整identity均匹配；不得只比较object ID或supplied digest。对应artifact record必须来自supplied current manifest records，处于statement-set scope：`statement_set_id` exact nonblank且匹配，`run_id` exact null；role、case、track、schema、expected/observed digest、VERIFIED与non-superseded条件全部独立满足。Production `run_match=NOT_APPLICABLE`，不得读取或推导expected run。

anchor selection必须对statement/revision唯一，policy ID/version等于第3节pin，all rule refs无duplicate，selected ref恰在all refs一次、不得在non-anchor refs，source order digest重算有效，fidelity/fanout符合pin。BOUND graph固定顺序为`STATEMENT, STATEMENT_SET, STATEMENT_RECORDS, RULE`，前三者进入`target_object_refs`，selected RULE进入`record_anchor_ref`。

### 6.1 P40 metadata coherence acceptance

Selected metadata receipt必须唯一、完整、nonblank、非UNMAPPED且self digest有效。当前冻结public shapes不存在第二个独立governing source object type：[`GoverningVersions`](../engine/f09/feedback.py:146)只有四个contract version；[`RuleMetadataReceipt`](../engine/f09/feedback.py:154)只有receipt自身的`source_ref.object_type`；selected rule authority也不声明其source object type。因此source object type不是Task 8 metadata-coherence acceptance dimension，不能从历史literal常量制造，不能由receipt self-attestation通过，也不能把“缺少第二值”判为INVALID。未来若要验证source object type，必须另开contract revision，引入owner authority/public shape及migration；Task 8不得隐式加入。

P40只验证以下可独立取得的维度；每个值先exact guard/nonblank，再按给定方向比较：

| 验收维度 | 独立源A | 独立源B | 比较方向 |
|---|---|---|---|
| rule完整identity | metadata receipt的`rule_ref` | anchor选择出的selected RULE ref | receipt → selected authority，全部8个ref字段逐值相等 |
| rule digest ownership | receipt `rule_ref.digest_binding` | selected RULE ref已验证的digest binding | receipt → selected authority，必须均为Present且完整digest逐值相等 |
| metadata contract | receipt `metadata_contract_version` | `governing_versions.rule_contract_version` | receipt → governing version，exact相等 |
| metadata schema | receipt `metadata_schema_version` | receipt `source_ref.schema_version` | metadata declaration → source ref schema，exact相等；两值独立guard，不允许复制补值 |
| receipt content | receipt supplied `content_digest` | bounded JCS重算`metadata_self_excluded` | supplied → recomputed，完整digest相等 |
| metadata identity payload | `family_id, school, canon, rule_type, captured_at`各receipt字段 | 本合同的exact nonblank/domain约束 | field → contract predicate，逐字段通过；`rule_type`不得为`UNMAPPED` |

`source_ref`本身仍必须exact [`VersionedObjectRef`](../engine/f09/trace.py:53)，其object type、ID、schema等shape字段均nonblank/nullable合法；其`digest_binding`必须是exact [`DigestPresent`](../engine/f09/trace.py:35)，且内含digest必须满足完整`algorithm, canonicalization, value` shape。exact [`DigestMissing`](../engine/f09/trace.py:43)即使wire shape合法、metadata receipt与Production authority均按该值重签且self digest有效，也必须使该target item进入`INVALID / INVALID_MATERIAL / empty graph`，不得`BOUND`。此要求仅限P40的`source_ref`，不改变`family_id == UNMAPPED`导致`UNBOUND`、rule digest ownership、invalid-authority family或source object type边界；`source_ref.object_type`仍没有第二独立值可做coherence equality。P40不得硬编码`RULE_SOURCE`、`rule-metadata.v1`或任何新常量；必须覆盖表中每类single mismatch、blank、missing/invalid digest，特别是上述合法shape且全量重签的`DigestMissing`反例，以及所有表内coherent但使用非历史literal的正例。

这只改变P40 acceptance judgment，不改变第5节valid normal metadata/authority digest字段或bytes，也不宣称旧实现中的任何source-object-type常量正确。

### 6.2 七维与 precedence

七维固定顺序为`case_match, track_match, run_match, statement_match, revision_match, statement_set_match, artifact_digest_match`。Production required维是case、track、statement、statement-set、artifact digest；run为N/A，revision在raw revision为null时可UNKNOWN，否则必须MATCH才可BOUND。PREPROD required维是case、track、run、artifact digest；statement、revision、statement-set恒N/A。

precedence固定且只适用于A0–A3已成功后的item-resolution：item-local malformed/inconsistent/integrity/protocol为INVALID；多个合法候选或source ambiguous为AMBIGUOUS；合法缺失、pointer/source unresolved、required mismatch或graph不完整为UNBOUND；只有唯一完整graph且全部required维MATCH才BOUND。PREPROD某请求ref的candidate数为0时唯一为`UNBOUND / TARGET_NOT_FOUND`，大于1时唯一为`AMBIGUOUS / AMBIGUOUS_CANDIDATES`；二者均empty graph，不得改判INVALID。不得default BOUND、倒推维度或用一个维度替代另一个。

## 7. PREPROD resolver 与 P57 mechanical predicate

PREPROD authority `track`必须exact [`RunTrack.V5_V6_PREPROD`](../engine/f09/contracts.py:21)，submission及target track binding也必须解析到该track；`case_id`与`run_id`exact nonblank。PREPROD item target protocol shape含且仅含：`target_statement_id`必须null；`target_statement_revision_id`必须null；`target_run_id`必须exact nonblank；`target_prediction_id`必须null。按本顺序首个违反项唯一为I阶段`INVALID / INVALID_MATERIAL / empty graph`。shape通过后，`target_run_id == authority.run_id`时`run_match=MATCH`并继续；不等时唯一为`UNBOUND / REQUIRED_MATCH_FAILED / empty graph`且`run_match=MISMATCH`。不得忽略、补值或把prediction映射到任一authority/ref字段。target refs角色与tuple语义为：恰一required `RUN_SNAPSHOT`；optional `DECISION_RUN`、`FEEDBACK_ATTACHMENT`、`MANIFEST`各零或一；其他role forbidden；规范graph/ref顺序固定为上述四角色序。每个ref独立应用下列predicate，不得跨ref复用candidate。

对authority `target_refs`中的请求ref `r`，其完整[`VersionedObjectRef`](../engine/f09/trace.py:53) owner shape、8字段exact class/nullability/nonblank及closed `DigestPresent | DigestMissing` binding shape已且只在A1验证。I不重复验证8字段shape；I仅执行协议acceptance：digest binding必须exact `DigestPresent`，其digest已通过A1 shape。shape合法的exact `DigestMissing`唯一使对应item为`INVALID / INVALID_MATERIAL / empty graph`且不进入candidate count。然后candidate严格且仅从supplied current `manifest.records`导出，唯一record-to-ref identity projection含且仅含：

```text
record.artifact_role == r.object_type
record.artifact_id == r.object_id
record.schema_version exact nonblank且 == r.schema_version
record.expected_digest非null且 == record.observed_digest == r.digest_binding.digest
```

四项比较均为owner value逐值exact equality；digest比较含`algorithm, canonicalization, value`全部三字段。candidate还必须同时满足`state != SUPERSEDED`、`case_id == authority.case_id`、`track is V5_V6_PREPROD`、`run_id == authority.run_id`、`statement_set_id is null`、`state == VERIFIED`；由此expected/observed都必为non-null。候选数必须恰为1才能继续：0唯一返回`UNBOUND / TARGET_NOT_FOUND / empty graph`；大于1唯一返回`AMBIGUOUS / AMBIGUOUS_CANDIDATES / empty graph`。二者均不得返回INVALID。禁止按tuple position、时间、revision、first/last或其他优先级选取，也禁止从其他manifest、历史record或filesystem补candidate。

[`ArtifactRecord`](../engine/f09/artifacts.py:87)不拥有`revision_id, contract_version, source_locator_id, captured_at`，所以这四个requested-ref字段只接受前述ref自身shape validation；它们不参与record candidate equality，不得由record推导、补值或宣称被record证明。`path_locator, attempts, issue_ids`也不进入record-to-ref identity projection或candidate equality。不得用tuple位置、时间、revision或locator制造第二套projection。

每个ref先依上述predicate独立确定唯一candidate；仅在RUN_SNAPSHOT ref的唯一candidate确定后，再执行且只执行下列snapshot-to-record投影：`validated submission.source_snapshot_ref.source_snapshot_id == candidate.artifact_id`；snapshot `schema_version`与candidate `schema_version`都必须exact nonblank且逐值相等；`snapshot.content_digest == candidate.expected_digest == candidate.observed_digest == RUN_SNAPSHOT ref.digest_binding.digest`，digest equality含`algorithm, canonicalization, value`三字段。snapshot `source_type`仍必须`FEEDBACK`，但不映射artifact role；snapshot的`contract_version, source_locator_ids, captured_at, immutability`只受raw wire schema自身验证，不参与candidate选择或snapshot-to-record equality。任一投影失败均为INVALID；不得改选第二candidate、从ref或record补nullable值、按位置/时间/revision择优。该检查不会增加candidate，故“恰一双方一致关系”精确指已确定的唯一RUN_SNAPSHOT candidate与唯一validated submission snapshot之间上述三组等值关系。PREPROD不得读取Production statement/set/projection/anchor/metadata/governing owners；三个statement维恒N/A；eligibility恒INELIGIBLE。

P57在同一P-ID内覆盖并使用下列closed唯一映射；任一反例只按最先命中的行分类：

| 判定点/predicate | 唯一status/category/graph | 作用域 |
|---|---|---|
| A3：forbidden target-ref role、同一role超过一个ref，或其他A0–A3 predicate失败 | 全部items `INVALID / INVALID_MATERIAL / ()` | invalid-authority family |
| A1：authority target ref自身8字段shape、closed digest-binding union或其nested digest shape非法 | 全部items `INVALID / INVALID_MATERIAL / ()` | invalid-authority family；不得进入I |
| I-ref acceptance：已通过A1 owner shape的请求ref使用exact `DigestMissing`而非exact `DigestPresent` | 该item `INVALID / INVALID_MATERIAL / ()` | item-local；不进入candidate count；I不重复shape validation |
| I-candidate filter：record role/object-ID不等、SUPERSEDED、case/track/run/set scope不等、非VERIFIED、record schema null或不等、expected/observed任一null、expected/observed/ref digest不等 | 该record不是candidate；不直接产生状态 | 对全部supplied current records完成同一filter后才计数 |
| filter后candidate count = 0（包括role/object-ID/schema/digest mismatch或missing导致无candidate） | 该item `UNBOUND / TARGET_NOT_FOUND / ()` | item-local |
| filter后candidate count > 1 | 该item `AMBIGUOUS / AMBIGUOUS_CANDIDATES / ()` | item-local |
| 恰一candidate后RUN_SNAPSHOT snapshot-to-record三组投影任一失败 | 该item `INVALID / INVALID_MATERIAL / ()` | item-local |
| required RUN_SNAPSHOT role在A3合法target refs中缺失 | 该item `UNBOUND / PROTOCOL_GRAPH_INCOMPLETE / ()` | item-local，先于逐ref filter |
| 所有required关系成功且optional refs各自成功 | `BOUND / null / canonical graph` | item-local |

ref自身合法的`revision_id, contract_version, source_locator_id, captured_at`不参与candidate filter，改变它们不得改变candidate数；四个合法角色逐ref独立应用同一表。Production/PREPROD item target protocol shape均先于本表的候选处理并按第6、7节唯一分类。禁止按位置/时间/revision择优，禁止把filter rejection直接改判INVALID，禁止新增P-ID。

## 8. malformed operation、idempotency 与 receipts

对每个validated submission item，按原tuple顺序生成[`ItemTargetReceipt`](../engine/f09/feedback.py:226)：protocol由outer class决定；四个raw target字段逐值复制；`resolution_status=INVALID`；`non_bound_category=INVALID_MATERIAL`；`graph=()`。graph digest、item receipt digest、aggregate digest严格使用第5节材料，不创建第二套算法。

### 8.1 malformed FeedbackBinding exact constructor

对validated submission中原tuple索引`i`的item `x`，必须构造且只可构造一个binding；所有字段唯一如下：

- `feedback_binding_id = "FEEDBACK-BINDING:" + x.feedback_item_id`。
- `feedback_item_ref`为exact [`VersionedObjectRef`](../engine/f09/trace.py:53)：`object_type=FEEDBACK`、`object_id=x.feedback_item_id`、`revision_id=rev-1`、`schema_version=feedback-item.v1`、`contract_version=g6-task8-feedback-v1`、`digest_binding=DigestPresent(PRESENT, bounded_jcs_sha256(feedback_item(x)))`、`source_locator_id=null`、`captured_at=current RawFeedbackAuthority.captured_at`。
- `source_track_binding_ref`为exact VersionedObjectRef：`object_type=TRACK_SOURCE_BINDING`、`object_id=validated submission.track_source_binding.track_source_binding_id`、`revision_id=rev-1`、`schema_version=validated submission.track_source_binding.schema_version`、`contract_version=validated submission.track_source_binding.contract_version`、`digest_binding=DigestPresent(PRESENT, validated且重算一致的submission track binding content_digest)`、`source_locator_id=null`、`captured_at=validated submission.track_source_binding.captured_at`。
- `binding_protocol`只由outer authority exact class决定；`target_track_source_binding`逐对象使用current outer wrapper提供且已通过第2.2节target binding prerequisite全部structural/state-reason/self-digest检查的对象，不从malformed target authority取值、不复制、不替换。
- Production七维exact tuple为`(UNKNOWN, UNKNOWN, NOT_APPLICABLE, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN)`；PREPROD七维exact tuple为`(UNKNOWN, UNKNOWN, UNKNOWN, NOT_APPLICABLE, NOT_APPLICABLE, NOT_APPLICABLE, UNKNOWN)`；位置固定对应`case_match, track_match, run_match, statement_match, revision_match, statement_set_match, artifact_digest_match`，不得读取malformed authority来细化任一UNKNOWN。
- `target_object_refs=()`、`record_anchor_ref=null`、`status=INVALID`、`issue_ids=x.issue_ids`、`detected_issues=()`。malformed authority failure不新增、不复用、不合成track/revision/unbound issue；因此issue tuple cardinality必须exact 0，且不存在可选code/path。
- `content_digest = bounded_jcs_sha256(binding self-excluded material)`；先以同shape和零digest占位构造unsigned binding，仅self-excluded material进入重算。不得使用authority异常文本、失败path、失败数量或partial graph影响binding ID、refs、dimensions、issues或digest。

上述constructor适用于authority-wide failure的每个item，不允许只标记触发dereference的首个item。bindings tuple与validated items同序、等长且无额外member；每个member须通过[`validate_feedback_binding_record()`](../engine/f09/feedback.py:1256)对binding-owned closed-domain、ref、dimension、`status`与`target_object_refs/record_anchor_ref`关系、issue与self-digest的检查。该validator不接收也不得推断[`ItemTargetReceipt`](../engine/f09/feedback.py:226)的`non_bound_category`或`graph`。

### 8.2 malformed operation receipt/result exact constructor

malformed authority current receipt逐字段唯一为：

| 字段 | 唯一值/来源 |
|---|---|
| `operation_id` | `"FEEDBACK-OP:" + key.canonical_key_digest.value` |
| `key` | 第4.3节完整stable key |
| `source_digest` | validated current submission `content_digest` |
| `authority_digest` | 第4.1节status-tagged invalid authority digest |
| `item_target_receipts` | 第8节按validated item原tuple顺序构造的exact tuple |
| `aggregate_target_digest` | 第5节aggregate target material的bounded JCS digest |
| `bindings` | 第8.1节按validated item原tuple顺序构造的exact tuple |
| `anchor_policy_ref` | exact VersionedObjectRef：`object_type=POLICY, object_id=POLICY:G6:TASK8:R33:ANCHOR, revision_id=rev-r33-anchor-v1, schema_version=anchor-policy.r33.v1, contract_version=g6-task8-r33-anchor, digest_binding=DigestPresent(PRESENT, independently reconstructed pinned anchor policy content_digest), source_locator_id=engine.f09.feedback#PINNED_ANCHOR_POLICY_R33, captured_at=2026-07-22T00:00:00Z` |
| `eligibility_policy_ref` | exact VersionedObjectRef：`object_type=POLICY, object_id=POLICY:G6:TASK8:R33:ELIGIBILITY, revision_id=rev-r33-eligibility-v1, schema_version=eligibility-policy.r33.v1, contract_version=g6-task8-r33-eligibility, digest_binding=DigestPresent(PRESENT, independently reconstructed pinned eligibility policy content_digest), source_locator_id=engine.f09.feedback#PINNED_ELIGIBILITY_POLICY_R33, captured_at=2026-07-22T00:00:00Z` |
| `created_at` | current调用恰一次`clock.now()`所得exact nonblank string；不得读系统时钟。重算prior时不得调用clock，必须逐值使用supplied prior receipt `created_at` |
| `content_digest` | 上述字段组成的第5节operation receipt self-excluded material之bounded JCS digest |

构造顺序固定为：validated submission/target-binding prerequisite → invalid authority/key → item receipts → aggregate → bindings →两policy refs → `created_at` → receipt self digest。operation producer必须在生成每个item receipt时机械检查`resolution_status / non_bound_category / graph`关系；prior receipt独立重算时必须从prior raw authority重新生成并逐字段比较该三者及其digest，不得把这项职责转移给只接收单个FeedbackBinding的validator。禁止用异常文本、failure path/count、prior值或malformed nested authority值填任一字段。

public result逐字段规则唯一为：

- 无prior：[`ValidFeedbackOperationResult`](../engine/f09/feedback.py:262) exact为`valid=True, operation_disposition=NEW_OPERATION, source_identity_relation=INITIAL, prior_receipt=null, current_receipt=current receipt, bindings=current receipt.bindings, overwrite_permitted=False, detected_issues=()`。
- 有prior时，先按第2.2节独立重算并完整验证prior。`source_identity_relation = SAME`当且仅当`current_receipt.source_digest == prior_receipt.source_digest`完整三字段逐值相等，否则`CHANGED`。
- key不同：valid result exact为`True, NEW_OPERATION, computed SAME|CHANGED, prior receipt, current receipt, current receipt.bindings, False, ()`，字段位置遵循第1节shape。
- key相同且aggregate相同：两次source digest因key包含source digest而必为相等，result exact为`True, REUSED_OPERATION, SAME, prior receipt, prior receipt, prior receipt.bindings, False, ()`；current receipt、bindings tuple及members必须以`is`复用prior。
- key相同且aggregate不同：[`InvalidFeedbackOperationResult`](../engine/f09/feedback.py:274) exact为`valid=False, operation_disposition=TARGET_MISMATCH, source_identity_relation=SAME, prior_receipt=prior receipt, current_key=current receipt.key, prior_aggregate_target_digest=prior receipt.aggregate_target_digest, current_aggregate_target_digest=current receipt.aggregate_target_digest, item_target_receipts=current receipt.item_target_receipts, bindings=(), overwrite_permitted=False, detected_issues=(DetectedIssue(IDEMPOTENCY.DIGEST_MISMATCH, /feedback/aggregate_target_digest),)`。该差异只能来自stable key明确排除而aggregate纳入的合法target-sensitive事实。

prior/current分别从各自raw bytes、validated submission identity、outer authority class、authority phase、validated target binding和module policies独立重算；current不得从prior补任一receipt字段。overwrite恒false。

invalid-authority equivalence class内任意nested字段变化不改变authority/key/aggregate；同protocol、同validated submission identity的malformed authority重复调用必须REUSED。operation-level mismatch issue唯一为`IDEMPOTENCY.DIGEST_MISMATCH @ /feedback/aggregate_target_digest`。

## 9. validators、eligibility 与 issue paths

[`validate_feedback_binding_record()`](../engine/f09/feedback.py:1256)必须重算binding content digest并仅检查其输入可观察的binding-owned信息：exact class、按第2.1节对第1节列明literal字段逐字段presence guard、closed domain、owner refs、track binding、locator、七维、`target_object_refs`的protocol graph形态与顺序、`record_anchor_ref`、`status`与这两个字段的关系、issue IDs、detected issue code/path和每个nested digest。field declaration order仅由S01静态验证，runtime validator不得反射检查field order。BOUND必须在`target_object_refs`与`record_anchor_ref`中具有合同要求的完整protocol graph；non-BOUND必须`target_object_refs=()`且`record_anchor_ref=null`。该validator不得检查或推断其输入中不存在的`non_bound_category`或[`ItemTargetReceipt`](../engine/f09/feedback.py:226) `graph`；receipt-owned `resolution_status / non_bound_category / graph`关系由第8.2节operation producer与prior receipt独立重算机械检查。不得新增public helper、参数或字段来转移该职责。

[`evaluate_learning_eligibility()`](../engine/f09/feedback.py:1336)不得信任binding自报：先调用binding validator，再使用同一个Production authority graph重新执行case/track/statement/revision/set/artifact/projection/anchor/P40 metadata/governing version验证，且selected RULE恰一。只有validated Production BOUND、allowed track、statement `FEEDBACK_ALLOWED`、完整anchor/artifact/metadata/version全部通过才ELIGIBLE；learning targets只含selected RULE，supporting rules按authority原语义进入exclusions。PREPROD、UNBOUND、INVALID为INELIGIBLE；AMBIGUOUS及policy规定的unknown-track为HUMAN_REVIEW。noneligible的targets/exclusions必须empty且blocking reasons nonempty。

[`validate_learning_eligibility()`](../engine/f09/feedback.py:1395)检查exact shape、closed status、binding digest、pinned policy ID/version、target/exclusion ref identity及互斥、blocking reasons、issues、time与self digest；ELIGIBLE必须targets非空且reasons空，其他状态必须targets/exclusions空且reasons非空。

producer bindings与validated item tuple同序。实际索引`i`的item-local issue path必须使用`/feedback_bindings/{i}` family；多item、非零索引及P03/P05/P42不得硬编码零。不得新增issue code/path family。

## 10. acceptance ledger 与 exact accounting

唯一测试文件为[`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py:1)。collection必须恰为12个non-param structural nodes与一个P01–P70参数节点；参数节点收集70 cases，总计`12 + 70 = 82`。不得新增node、P-ID、duplicate、hidden generation、漏收或额外收集。

12个structural obligations为：

- S01：全部public dataclass exact field order；只允许按第2.1节静态读取类级dataclass field metadata，不得把该读取引入runtime、validator、fixture或material。
- S02：closed aliases、closed union、clock protocol与四个public signatures。
- S03：owner类型按identity复用，不复制owner dataclass/enum/error。
- S04：malformed outer/top-level按第2.2节抛typed error且无result；exact `RawFeedbackAuthority` constructor-bypass 缺字段反例必须分别覆盖 `raw_submission, target_authority, target_track_source_binding, captured_at` 四个outer字段，并至少包含仅缺`captured_at`而其余三字段齐全的对象；每个反例均须证明由public bind抛exact typed contract error、无result且不泄漏原生`AttributeError`。
- S05：每次nested dereference有guard；在独立、完整、合法的outer raw bytes与target binding prerequisite下，分别以exact Production与PREPROD authority constructor-bypass缺字段反例调用public bind，证明不抛错、不泄漏原生`AttributeError`并返回valid/all INVALID material；断言使用public result的`bindings`字段。fixture不得在进入public bind前从malformed authority派生任何合法prerequisite。同一structural node内还须以源码中静态显式书写、非parameter/非hidden generation的fixture，覆盖A1 normal-material/owner-shape递归可达且runtime会dereference声明字段的closed exhaustive nested exact-class set；该集合含且仅含：`StatementSet, StandardStatement, ArtifactSetManifest, IdempotencyKey, ArtifactRecord, ArtifactWriteAttempt, VersionedObjectRef, DigestPresent, DigestMissing, DigestRef, DetectedIssue, DecisionTraceRef, CardIdentityRef, ResolvedDeclarationBinding, AbsentDeclarationBinding, NotApplicableDeclarationBinding, UnavailableDeclarationBinding, UnresolvableDeclarationBinding, FrozenDeclarationRef, StatementProjectionRecord, AnchorSelectionRecord, RuleMetadataReceipt, GoverningVersions`。其可达路径闭合为：Production `statement_set`递归到statement/set refs、decision trace、card refs与五种declaration-binding union；两协议`manifest` owner-shape递归到key、records、attempts、refs、issues与digests，尽管normal authority manifest identity只嵌入records digest；Production五个authority collections递归到projection/anchor/metadata/refs/digests/governing；PREPROD `target_refs`递归到refs/digest binding/digest。`BasisRecordIds`及其他ID/issue集合是`tuple[str, ...]` alias，按第5节string tuple验证，不是exact class，故不属于本集合；`SnapshotRef`只来自已验证submission prerequisite而非target authority normal material，故不属于本集合；policy、receipt、binding、eligibility类型在authority判定后构造，也不属于本集合。每个listed class各用一个仅缺其声明字段的constructor-bypass实例经public bind证明valid/all INVALID/INVALID_MATERIAL/empty graph且无原生`AttributeError`；A2只以独立digest mismatch fixtures覆盖，不存在“A2 shape fixture”。不得增删类、写“至少包括”或开放式等价项，不得用动态字段名、字段枚举或reflection生成fixture或case。
- S06：只有bounded JCS parser/digester；值域、深度、Unicode、duplicate、mutation限制全部受测。
- S07：第4、5节四类digest/key preimage的exact key、field、null、tuple、self-exclusion、sensitivity；malformed分支不信supplied digest且不用reflection/bytes/list/number/deferred/partial material，不把第2.1节仅用于presence guard的私有sentinel或探测结果写入material；valid authority所有runtime bytes不变且无R38治理identity。
- S08：valid/malformed prior/current独立重算；current不从prior补值；同protocol malformed equivalence为same key/same aggregate；合法target-sensitive变化可same key/changed aggregate。
- S09：REUSED返回prior receipt、bindings tuple及members的object identity。
- S10：两policy独立且不由caller/provider签名或替换，R33 pins完整。
- S11：模块import与runtime零side effect，只依赖标准库和五个owner模块。
- S12：机械静态计数恰为12 structural、1 parameterized node、P01–P70连续且总数82。

P01–P70的固定语义名称依次为：`production_complete_bound, preprod_snapshot_only_bound, unknown_statement_unbound, missing_revision_unknown, old_revision_mismatch_issue, duplicate_candidates_ambiguous, malformed_statement_ref_invalid, statement_owner_digest_exclusions, statement_contract_mismatch, set_case_mismatch, set_track_mismatch, set_owner_digest_nested_full, set_contract_mismatch, records_artifact_missing, records_artifact_duplicate, records_artifact_nonverified, records_expected_missing, records_observed_missing, records_digest_unequal, records_dimensions_independent, ref_artifact_id_mismatch, projection_type_invalid, projection_identity_mismatch, projection_digest_mismatch, anchor_missing, anchor_multiple, anchor_unsupported_none, anchor_empty_rules, anchor_duplicate_rules, anchor_selected_absent, anchor_selected_twice, anchor_nonanchor_order, anchor_source_order_digest, anchor_selected_not_rule, rule_contract_mismatch, metadata_missing_ineligible, metadata_multiple_human_review, metadata_blank_identity, metadata_unmapped, metadata_coherence, resolved_track_match, track_mismatch_issue, source_missing_unknown, target_unparsable_unknown, source_ambiguous, source_integrity_failed, resolved_with_reason_invalid, wrong_reason_invalid, source_side_track_parser, target_side_invalid, payload_digest_or_locator_invalid, pointer_missing_scalar_blank_root, preprod_missing_run, preprod_snapshot_cardinality, preprod_duplicate_refs_roles, preprod_mixed_dimensions, preprod_ref_record_or_forbidden, preprod_optional_decision_order, preprod_ineligible, policies_positive_eligible, feedback_policy_forbidden, caller_policy_injection, policy_swap_or_provider, production_ambiguous_review, invalid_unknown_track_eligibility, initial_new, changed_source_new, raw_revision_changes_key, same_key_same_aggregate_reused_identity, same_key_changed_target_mismatch`。P51是一个parameter case内顺序执行且必须全部通过的两个独立子场景，不得任选、合并或互相替代：P51a `payload_digest_mismatch`必须在第2.2节raw submission identity阶段抛exact [`F09IntegrityError`](../engine/f09/errors.py:21)，且无result、receipt、binding或target material；P51b `locator_invalid`必须使用digest与self-integrity均合法的raw submission，仅令locator grammar malformed，并返回本文规定的item-level `INVALID / INVALID_MATERIAL / empty graph` non-BOUND result及其status-tagged target material。P51仍只收集一个parameter instance，不新增node或P-ID。

同一ID内的加强义务：P07/P08/P12通过public bind重放A1 malformed statement ref或A2 owner digest mismatch，断言valid result、全部items为INVALID/INVALID_MATERIAL/empty graph且四类preimage可重算；这些case不得改造成I阶段relation mismatch。P40执行第6.1节全部机械比较，并断言`source_ref.digest_binding`为完整exact `DigestPresent`的正例可通过，而owner-shape合法且receipt与authority全量重签的exact `DigestMissing`反例是I阶段且只使对应item为INVALID/INVALID_MATERIAL/empty graph、不得使其他item进入invalid-authority family、不得BOUND；P57执行第7节完整唯一映射表，分别断言authority-wide malformed ref shape、forbidden/duplicate role，item-local shape合法`DigestMissing` acceptance failure、candidate-filter rejection后zero、multiple、post-selection projection invalid与required-role missing，禁止使用`INVALID或UNBOUND`二选一断言。P56还必须覆盖Production与PREPROD各自四个raw target字段的closed protocol-shape表及首错顺序，不得忽略forbidden nonnull identity；并对每个protocol至少将一个malformed raw target shape分别与合法target binding状态`INTEGRITY_FAILED, AMBIGUOUS, SOURCE_MISSING, UNPARSABLE, AVAILABLE_RESOLVED`交叉，逐例断言均由raw target shape优先得到`INVALID / INVALID_MATERIAL / empty graph`。另以shape合法item分别覆盖前四个非resolved状态，断言依次为`INVALID / INVALID_MATERIAL`、`AMBIGUOUS / AMBIGUOUS_CANDIDATES`、两例`UNBOUND / TRACK_UNRESOLVED`且均empty graph；只有shape合法且`AVAILABLE_RESOLVED`可进入candidate/relation判断。P01–P07、P51仅其locator-invalid子场景、P52–P57对non-BOUND断言status-tagged target material；P51的payload-digest-mismatch子场景必须且只能断言exact typed integrity error及无result/receipt/binding/target material，不适用任何non-BOUND material义务；P03/P05/P42覆盖多item同序、非零索引与动态paths；P20断言Production run null/N/A；P60/P63断言双policy；P68–P70断言stable key与target aggregate分账。其余P-ID必须按本节列出的固定语义完整执行，并覆盖相应正反例、owner exclusion/sensitivity、protocol、eligibility与idempotency断言。

## 11. VERIFY selectors 与 STOP

fresh CONTRACT接受后的focused VERIFY命令只能是：

```text
python -m pytest tests/f09/test_feedback_eligibility.py -q
```

期望为exact collection/accounting 82、输出`82 passed`、exit 0。不得把focused selector扩大为full suite。

Regression VERIFY必须以一个pytest invocation精确运行以下三个nodeid，且不得加减selector：

```text
python -m pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_h3_standard_list_schema_without_rule_ids_is_blocked_from_learning tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_ingest_includes_v5_feedback_attachment_summary_without_unblocking_learning tests/test_phase_a_minimal_learning_loop.py::test_statement_record_enforcement_marks_missing_as_unmapped -q
```

期望为exact collection 3、输出`3 passed`、exit 0。任一extra/missing/duplicate collection、collection error、nonzero exit、partial run或timeout均STOP。

实现或验证期间任一情形STOP：需改白名单外文件；需新增public shape/state/disposition/P-ID/node；owner shape/helper/API漂移；需private owner helper、I/O或caller policy；target binding prerequisite失败后仍构造result，或与authority交叉失败时未优先typed-error；无法guard-before-deref；valid normal authority bytes变化；R33 pin变化；Production run不是null/N/A；PREPROD track不是唯一`V5_V6_PREPROD`；metadata允许blank；Production projection不是完整identity；manifest未用public records digest；P57超出唯一record-to-ref projection或按位置/时间/revision选择；多item paths非动态；eligibility未用same graph复核；validator不能重算；出现side effect；union扩张；collection不是82；focused不是exact selector；regression不是exact三nodeids或期望不符。

## 12. closure、prohibitions 与未验证边界

机械否证包括：outer identity错误被降级，或exact outer constructor-bypass 缺 `raw_submission, target_authority, target_track_source_binding, captured_at` 任一字段时被降级、产生result或泄漏原生`AttributeError`；A0–A3 nested authority错误越界抛错或返回invalid result；A0–A3失败时任一item非INVALID/INVALID_MATERIAL/empty，或I阶段单item relation失败被扩张为all-items invalid-authority family；读取supplied authority digest；invalid preimage字段不精确；malformed canonical schema拼写错误、item tuple/dict shape错误或有附加字段；使用malformed内部值、bytes、number/list、reflection、deferred/partial material，或把presence sentinel/探测结果写入material；使用动态字段名、字段遍历、`vars()`、`__dict__`、`dataclasses.fields()`或`__dataclass_fields__`；S05 closed class set缺项、增项或由hidden generation补足；current从prior补值；Production/PREPROD token混同；valid path byte变化；R38治理identity进入runtime；P40要求不存在的source-object-type authority、接受receipt self-attestation或硬编码常量，或接受`source_ref.digest_binding`为`DigestMissing`并使item BOUND；P57接受SUPERSEDED、把zero判为非`UNBOUND/TARGET_NOT_FOUND`、把multiple判为非`AMBIGUOUS/AMBIGUOUS_CANDIDATES`、接受schema不等或执行优先选择；REUSED重建；public union扩张；计数非82。任一命中即否证R38。

R33 runtime policy tokens、normal authority全部digest/preimage/self-exclusion/key、owner材料、public shapes、stable key/target分账、item receipt、双policy、DigestMissing sort、blank payload、prior/current独立、REUSED identity、Production/PREPROD protocol、七维、metadata/selected RULE/exclusions、三态eligibility、zero side effects与`12 + 70 = 82`均由本文完整条款保护。未来实现只能修改[`engine/f09/feedback.py`](../engine/f09/feedback.py:1)与[`tests/f09/test_feedback_eligibility.py`](../tests/f09/test_feedback_eligibility.py:1)；禁止Git、GitHub mutation及owner修改。

未验证边界：本文未运行任何命令、import、compile、collection、pytest、focused selector或regression；未证明未来实现符合本合同，未证明82 cases或3 regressions通过，也未取得fresh reviewer接受。owner/source只读且未变。下一gate唯一为针对[`plans/g6-task8-r38-contract.md`](g6-task8-r38-contract.md:1)的独立fresh CONTRACT rereview；本文不自授CONTRACT PASS，不作任何review verdict。
