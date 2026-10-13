# PI-590-R6 — G5 F09 实施计划独立复验

## Verdict: BLOCKED

- task_id：PI-590-R6
- parent_task_id：PI-500
- 审阅对象：[`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md)
- 审阅方式：全新分离实例、纯静态、fail-closed
- 审阅时间：2026-07-20
- 运行证据：无；未运行 Python、pytest、collection、YAML、mapping、计划代码或 Git
- 技术结论：计划仍存在 High 与 Medium 缺陷，不满足 G5 技术验收条件。
- 授权结论：本工件不授权实现、不授权测试执行、不授权 YAML/mapping 使用、不授权生产默认变更，也不更新控制面状态。

## 1. Severity summary

| Severity | Count | 结论 |
|---|---:|---|
| High | 3 | 任一项均足以阻断 |
| Medium | 2 | fail-closed 条件下同样阻断 |
| Low | 0 | — |
| Critical ambiguity | 2 | 已分别并入 H-01、H-03 |
| Key evidence gap | 2 | 31-leaf 可复制性与 T72 有效性证据不足 |
| Relevant regression | 0 个已证实 | 但不能抵消阻断项 |

### H-01 — Track UNKNOWN 不能由 binder 输入事实表达；七维闭包未成立

[`exercise_feedback_binding_phase()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1708) 在请求 track UNKNOWN 时仍构造一个合法、非空的 [`FeedbackSubmission.track`](production-implementation-pi-500-r1-f09-implementation-plan.md:1778)，仅把 [`track_fact_available`](production-implementation-pi-500-r1-f09-implementation-plan.md:1731) 置为 false，并通过 [`anchor_available`](production-implementation-pi-500-r1-f09-implementation-plan.md:1817) 删除 manifest anchor。该输入最多能表达“anchor 不可用”，不能要求 binder 计算 [`track_match`](production-implementation-pi-500-r1-f09-implementation-plan.md:946) 为 UNKNOWN；submission 与 statement set 仍各自携带有效 track。

这与 PI-230 对 track_match 的独立必填三态语义冲突：[`track_match`](production-implementation-pi-230-traceability-binding.md:654) 必须独立表达 MATCH、MISMATCH 或 UNKNOWN。计划自己的类型也把 [`FeedbackSubmission.track`](production-implementation-pi-500-r1-f09-implementation-plan.md:933) 声明为非 nullable。当前适配器把“track 身份未知”与“record anchor 缺失”合并，七维 stimulus 不是逐维可表达的 canonical facts。

此外，31 个 component tests 仅验证 source_track 的 MATCH/MISMATCH 路径；[`test_feedback_source_track_port()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2494) 没有覆盖 UNKNOWN，且 [`test_feedback_seven_matches_port()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2488) 只比较输入字段变化，不断言 binder 返回的七个维度。因此 H-01 未闭合。

### H-02 — 31 个 component tests 明确违反“拒绝分号歧义”的验收规则

计划声称 31 个定义可直接复制，并要求拒绝 semicolon-based ambiguity，但实际每个定义都在一行放置多个语句。例如 [`test_trace_statement_set_complete_port()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2348) 的初始化与断言分别使用分号连接；artifact 组从 [`test_artifact_records_write_outcome_port()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2409) 起采用相同模式；feedback 组从 [`test_feedback_target_statement_id_port()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2470) 起也采用相同模式。

用户给定的机械验收规则明确要求拒绝分号歧义。这里不是风格问题，而是复制性门禁的直接失败；因此 R5 M-01 不能按计划自述视为关闭。

### H-03 — T72 产生额外重复 current 记录，artifact cardinality/identity 有效性未闭合

[`exercise_artifact_lifecycle_phase()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1592) 在 supersedes_revision 非空时构造 old/current 两条 lifecycle records，随后又无条件构造 selected records，并通过 [`records=lifecycle_records + selected_records`](production-implementation-pi-500-r1-f09-implementation-plan.md:1676) 合并。

对 [`mutate_t72()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2125) 而言，item_states 长度为 1，所以 selected records 仍包含 record_1 与 record_2；最终顺序为 old、current、record_1、record_2。current 与 record_1 同时使用当前 statement revision、同一 statement set、同一 records path 和相同 digest，只以 artifact_id 区分。计划没有给出 PI-230 artifact role/path 唯一性下这组四记录可通过 [`inspect_artifact_set()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1678) 的静态理由，也没有说明为何 T72 应保留额外 current-like record。

[`test_artifact_supersedes_revision_port()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2451) 只检查前两条记录的 ID/state，不检查总 cardinality、后两条污染、path/role 唯一性、inspection status 或 retry status。因此 old/current 使用既有 [`ArtifactRecord`](production-implementation-pi-500-r1-f09-implementation-plan.md:874) 字段这一收窄目标虽部分完成，但“baseline/non-T72 不污染、T72 cardinality/order 与 lifecycle validity 兼容”未被证明，H-04 仍阻断。

### M-01 — component assertions 对错误路径存在不安全解引用

多个 component tests 在 adapter 可能返回 INVALID 且 nullable observation 字段可能保持 None 后，直接解引用或索引：

- [`test_artifact_index_revision_port()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2421) 直接读取 inspection_input.records[1]；
- [`test_artifact_expected_digest_port()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2427) 与 [`test_artifact_observed_digest_port()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2433) 直接读取 inspection_input.records[0]；
- [`test_feedback_policy_version_port()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2500) 直接索引 eligibility_records[0]；
- [`test_feedback_binding_complete_port()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2524) 在先索引 baseline bindings 后才检查 changed 结果；
- [`test_feedback_eligibility_complete_port()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2530) 同样依赖 baseline eligibility 非空。

计划的 observation 类型明确允许 [`inspection_input`](production-implementation-pi-500-r1-f09-implementation-plan.md:1362) 为 None，并允许 [`bindings`](production-implementation-pi-500-r1-f09-implementation-plan.md:1377) 与 eligibility_records 为空。测试应先证明 runnable、status、非 None 和 cardinality，再索引。当前定义不满足“baseline 必须产生 observation、不得在失败后不安全索引空 tuple”的门禁。

### M-02 — trace adapter 在边界输入上存在未守卫空序列索引

[`exercise_trace_validation_phase()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1383) 只检查 trace、statement_set、decision 是否为 None，随后直接索引：

- source.state_fields[0..2]：[`state_mapping_1`](production-implementation-pi-500-r1-f09-implementation-plan.md:1401) 至 [`state_mapping_3`](production-implementation-pi-500-r1-f09-implementation-plan.md:1413)；
- source.event_fields[0..5]：[`mapping_1`](production-implementation-pi-500-r1-f09-implementation-plan.md:1419) 至 [`mapping_6`](production-implementation-pi-500-r1-f09-implementation-plan.md:1449)；
- run_result.trace.nodes[0]：[`base_node`](production-implementation-pi-500-r1-f09-implementation-plan.md:1507)；
- statement_set.statements[0]、card_identity_refs[0]、evidence_refs[0]：[`base_statement`](production-implementation-pi-500-r1-f09-implementation-plan.md:1518) 至 [`base_evidence_ref`](production-implementation-pi-500-r1-f09-implementation-plan.md:1523)。

这些异常发生在 try/except 之前，且不会被仅捕获 F09Error 的区段转换为 typed INVALID observation。对于零上下文实施计划，这是明确的可达 IndexError 风险。

## 2. R5 findings closure matrix

| R5 finding | R6 static result | Evidence | Closure |
|---|---|---|---|
| H-01 feedback pre-call facts | post-call 七维/anchor overwrite 已移除；run baseline 使用 NOT_APPLICABLE；但 track UNKNOWN 仍不可独立表达，component test 也不核验 binder 七维输出 | [`exercise_feedback_binding_phase()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1708), [`track_fact_available`](production-implementation-pi-500-r1-f09-implementation-plan.md:1731) | NOT CLOSED |
| H-02 digest token | 所有在 PI-500 中显示的 DigestRef algorithm constructor literals 均为精确小写 sha256；未检出 uppercase/hyphenated constructor literal | [`source_digest`](production-implementation-pi-500-r1-f09-implementation-plan.md:1611), [`content_digest`](production-implementation-pi-500-r1-f09-implementation-plan.md:1783) | CLOSED |
| H-03 state/event graph | state/event transformation、source/target nodes、field mappings 与 terminal edges 均在 validator 调用前进入 trace；T93 交换 source object identity，固定 targets 与 temporal mapping paths 保持分离 | [`state_transformation`](production-implementation-pi-500-r1-f09-implementation-plan.md:1459), [`event_transformation`](production-implementation-pi-500-r1-f09-implementation-plan.md:1483), [`validate_statement_projection()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1563), [`mutate_t93()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2188) | CLOSED for R5 scope |
| narrowed H-04 T72 | old/current 已用既有 ArtifactRecord 字段独立表达，issue_ids 不承载 supersession identity；但额外 selected records 造成 cardinality/identity validity 缺口 | [`old_record`](production-implementation-pi-500-r1-f09-implementation-plan.md:1667), [`selected_records`](production-implementation-pi-500-r1-f09-implementation-plan.md:1669) | NOT CLOSED |
| M-01 31 tests | 数量与分组正确；定义是 literal top-level；但全部使用分号压缩，且若干测试存在 nullable/empty unsafe indexing | [`Thirty-one literal adapter component tests`](production-implementation-pi-500-r1-f09-implementation-plan.md:2342) | NOT CLOSED |

## 3. 31-leaf reachability/component-definition audit

### 3.1 Mechanical count

| Group | Required | Statically visible | Result |
|---|---:|---:|---|
| trace | 10 | 10 | count PASS |
| artifact | 10 | 10 | count PASS |
| feedback | 11 | 11 | count PASS |
| total | 31 | 31 | count PASS |

所有定义均为 literal top-level function definition；未见 loop、range、generator、registry、factory、table parser、dynamic ID 或 shared catch-all。每个定义名称对应一个 fixture leaf，并包含 baseline→replace mutation、目标恢复后整体相等检查、adapter call 与 observation assertion。

### 3.2 Reachability result

- trace 10 leaves 均可静态追到 statement/trace/transformation/edge 构造；见 [`TraceFixture`](production-implementation-pi-500-r1-f09-implementation-plan.md:1293) 与 [`exercise_trace_validation_phase()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1383)。
- artifact 10 leaves 均可静态追到 write、manifest alteration、inspect、retry 或 key/projection 输入；见 [`ArtifactFixture`](production-implementation-pi-500-r1-f09-implementation-plan.md:1299) 与 [`exercise_artifact_lifecycle_phase()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1592)。
- feedback 11 leaves均进入 submission、item、manifest、binder、eligibility 或 record validator；见 [`FeedbackFixture`](production-implementation-pi-500-r1-f09-implementation-plan.md:1305) 与 [`exercise_feedback_binding_phase()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1708)。

### 3.3 Definition-quality verdict

BLOCKED。数量和静态 reachability 不能替代可复制性、安全索引与语义输出证明。H-02 与 M-01 的问题使 31-leaf 门禁失败。

## 4. T72/T93 special review

### T72

- PASS：old/current 使用现有 PI-230 ArtifactRecord identity/path/schema/statement-set/run/digest/state 字段；没有 invented supersedes field；没有 issue-string parsing。
- PASS：old 位于 current 之前，符合审计阅读顺序。
- FAIL：old/current 后仍追加 record_1/record_2，形成四记录 manifest；current 与 record_1 的当前 revision/path/set/digest 重叠未解释。
- FAIL：component test 未断言 cardinality、唯一性、inspection/retry 成功或 non-T72 pollution absence。
- 结论：BLOCKED。

### T93

- state source object 与 event source object 由 [`mutate_t93()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2188) 双向交换。
- state/event source locator IDs、target object IDs、target field paths、state as_of 与 event interval paths保持独立。
- 两个 transformation、四个 nodes 与两个 terminal edges 都在 [`validate_statement_projection()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1563) 前进入 graph。
- 结论：R5 H-03 的 stimulus 缺口已静态关闭；未声称 validator 运行结果。

## 5. T01–T104 five-way static accounting

| Accounting axis | Static result | Citation |
|---|---:|---|
| concrete mutator definitions | 104，T01–T104 连续可见 | [`mutate_t31()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2002) 至 [`mutate_t104()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2221)，前段 T01–T30 位于同一 mutator block |
| literal constructors | 104，T01–T104 连续可见 | [`T01`](production-implementation-pi-500-r1-f09-implementation-plan.md:2232) 至 [`T104`](production-implementation-pi-500-r1-f09-implementation-plan.md:2335) |
| mutator references | 104 个 constructor 各自引用同号 mutate_tNN | 同上 |
| complete pytest nodes | 104 个完整 literal node，后缀与 TNN 对应 | 同上 |
| literal tuple | 104 个按序 entries | [`SCENARIOS`](production-implementation-pi-500-r1-f09-implementation-plan.md:2337) |

静态五路 accounting 通过。此结论不等同于 AST 执行、pytest collection 或 runtime success。

## 6. Canonical regression checks

| Check | Result | Evidence |
|---|---|---|
| PI-210 unique conversion-type ownership | PASS static | Task 6 复用 canonical types；[`TransformationRecord`](production-implementation-pi-500-r1-f09-implementation-plan.md:1459) 进入 trace |
| PI-220 six gates | PASS static | baseline 六成员与 T74–T85 保持六门语义；[`mutate_t74()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2131) |
| PI-220 six participation roles | PASS static | [`BASELINE_PARTICIPATION`](production-implementation-pi-500-r1-f09-implementation-plan.md:1882) 含六角色；T46–T48 覆盖完整性/攻击 |
| PI-220 five actions | PASS static | T38–T42 分别覆盖 OUTPUT、CONDITIONAL、ASK、ABSTAIN、HUMAN_REVIEW；[`T38`](production-implementation-pi-500-r1-f09-implementation-plan.md:2269) 至 [`T42`](production-implementation-pi-500-r1-f09-implementation-plan.md:2273) |
| PI-230 feedback states | PASS type surface | [`FeedbackBinding.status`](production-implementation-pi-500-r1-f09-implementation-plan.md:954) 为四态 |
| PI-230 eligibility states | PASS type surface | [`LearningEligibility.status`](production-implementation-pi-500-r1-f09-implementation-plan.md:962) 为三态 |
| F09 only | PASS static plan boundary | rollout 仅 F09 staged/preprod opt-in；[`Phase R1`](production-implementation-pi-500-r1-f09-implementation-plan.md:2552) |
| F08 identity only | PASS static | [`mutate_t31()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2002) 与 T31/T32 明确区分 reference-only 和 forged runtime objects |
| production-default unchanged | PASS static declaration | [`Phase R3`](production-implementation-pi-500-r1-f09-implementation-plan.md:2568) 明确需未来独立授权 |
| disabling mechanisms | PASS static declaration | R0 默认不可达，R1/R2 显式 opt-in；[`Phase R0`](production-implementation-pi-500-r1-f09-implementation-plan.md:2543) |

上述 regression PASS 仅表示未发现新的静态语义回退；不能覆盖本工件的阻断发现。

## 7. Disabling mechanisms and authorization boundary

- F09 必须默认关闭并从默认 import/entrypoint 不可达。
- R1 仅允许 enable_f09=true、STAGED_AUDIT 与隔离 artifact root；见 [`Phase R1`](production-implementation-pi-500-r1-f09-implementation-plan.md:2552)。
- R2 仅允许 PREPROD_SHADOW、preprod-only root、AUDIT_ONLY 跨轨链接；见 [`Phase R2`](production-implementation-pi-500-r1-f09-implementation-plan.md:2560)。
- R3 未授权；不得修改 SubmitAnalysisRequest 或 pipeline 默认值；见 [`Phase R3`](production-implementation-pi-500-r1-f09-implementation-plan.md:2568)。
- 本次 BLOCKED 不授权修复、不授权实现、不授权测试、不授权 Git、不授权控制面状态变化。

## 8. Modified files

本复验仅创建一个文件：

1. [`production-implementation-pi-590-r6-g5-plan-reacceptance.md`](production-implementation-pi-590-r6-g5-plan-reacceptance.md)

未修改审阅对象、control、handoff、META、YAML、mapping、production code、test code 或其他文件。

## 9. Unique next legal action

唯一下一合法动作：由 PI-500 的计划所有者启动一个新的、范围受限的计划修复任务，只修改 [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md)，并至少完成以下四项：

1. 为 track UNKNOWN 提供与非 nullable Track 契约一致、且能让 binder 独立计算 track_match=UNKNOWN 的 canonical 输入语义；补充逐维 binder-output assertions。
2. 重写全部 31 个 component tests，移除分号多语句形式，并在任何 nullable/tuple 索引前证明 runnable、status、非 None 与 cardinality。
3. 修正 T72 manifest 组成，使 old/current identity、记录 cardinality、顺序、path/role 唯一性与 inspect/retry validity 明确且无额外 current-like record 污染；component test 必须断言完整记录集合。
4. 在 trace adapter 的所有序列索引前实施 fail-closed shape guard，保证 malformed prerequisites 返回 typed NOT_RUNNABLE/INVALID observation，而非产生未捕获 IndexError。

完成该受限修复后，必须再由新的分离实例执行下一轮纯静态 G5 reacceptance。