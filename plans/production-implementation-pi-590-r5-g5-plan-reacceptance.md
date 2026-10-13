# PI-590-R5 · G5 F09 实施计划独立复验

## 1. 验收结论

**Verdict: BLOCKED**

本次复验是对 [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) 的全新、分离、纯静态复验。按 fail-closed 规则，只要存在 High、关键证据缺口、语义矛盾或无法由当前文本直接证明的关键行为，即不得判定 PASS。

严重度汇总：

| 严重度 | 数量 |
|---|---:|
| High | 4 |
| Medium | 1 |
| Low | 0 |
| 关键证据缺口 | 2 |

PASS 条件未满足。PI-500 继续保持 BLOCKED；本工件不授权实现、测试执行、声明式配置执行、映射执行、Git 操作或生产默认行为变更。

## 2. 复验边界与方法

### 2.1 已静态审阅的事实源

- 治理状态与授权边界：[`production-implementation-control.md`](production-implementation-control.md)
- 被复验计划：[`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md)
- PI-210 规范：[`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md)
- PI-220 规范：[`production-implementation-pi-220-decision-gate-semantics.md`](production-implementation-pi-220-decision-gate-semantics.md)
- PI-230 规范：[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md)
- PI-300 F09 设计：[`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md)
- 冻结快照：[`production-implementation-pi-300-f09-source-snapshots-v1.json`](production-implementation-pi-300-f09-source-snapshots-v1.json)
- 当前项目状态：[`project-state.json`](../META/project-state.json)

### 2.2 静态动作

- 逐段读取治理、PI-210、PI-220、PI-230、PI-300、冻结快照和被复验计划。
- 静态比对 Task 6–8 接口、三组 phase observation、三组 adapter、31 个 fixture leaves、T91–T97、T01–T104 literal definitions、constructors、mutator references、pytest nodes 和 tuple。
- 静态搜索类型所有权、digest token、supersession 表达、component-test 要求及禁用机制。
- 未执行 Python、pytest、pytest collection、YAML、mapping 或 Git。
- 未读取或采用 PI-570-R4 自我声明作为独立闭环证据；其 remediation record 仅作为待核声明处理。

## 3. High findings

### PI590R5-H-01 — feedback fixture 的七维匹配与 anchor 状态没有进入 canonical binder 的调用输入

**结论：PI590R4-H-01 未关闭。**

规范表明确要求所有右侧 port 都必须在 validation 之前构造实际调用输入；调用后才比较或修改不算消费，见 [`leaf-to-port 前置消费规则`](production-implementation-pi-500-r1-f09-implementation-plan.md:1215)。同一表宣称 feedback 的 target、anchor、七维 match 与 source track 都供应给 canonical binder，见 [`feedback leaf-to-port 行`](production-implementation-pi-500-r1-f09-implementation-plan.md:1227)。

实际 adapter 仅把 submission、statement set、manifest 传入 [`validate_feedback_binding()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1696)。binder 返回后，adapter 才通过 [`replace()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1704) 覆盖七个 match dimensions，并在 [`record_anchor_ref`](production-implementation-pi-500-r1-f09-implementation-plan.md:1714) 上应用 anchor switch。第二个 binding 重复同一后置改写，见 [`binding_2 后置改写`](production-implementation-pi-500-r1-f09-implementation-plan.md:1732)。

因此：

- feedback.seven_matches 不是 named binder 的 pre-call stimulus；
- feedback.anchor_status 只影响 source span，并在 binder 返回后直接覆写 anchor ref，不能证明 binder 消费 record-anchor availability；
- T25 与 T53 可验证 fixture 合成后的 binding record，而不是 canonical binder 的绑定行为；
- 这与计划自身的前置消费规则直接矛盾。

在零上下文机械实现标准下，工程师无法同时逐字实现 adapter 与满足 normative table。该矛盾单独足以 BLOCKED。

### PI590R5-H-02 — adapter 使用非 canonical digest algorithm token

PI-210 要求 digest algorithm 是注册的 lowercase ASCII token。被复验计划的 Task 1 也要求 lowercase digest validation，但 artifact adapter 多次构造 uppercase token，首个实例见 [`DigestRef 构造`](production-implementation-pi-500-r1-f09-implementation-plan.md:1545)，其余实例见 [`IdempotencyKey digest 构造`](production-implementation-pi-500-r1-f09-implementation-plan.md:1551)、[`ArtifactRecord digest 构造`](production-implementation-pi-500-r1-f09-implementation-plan.md:1591)、[`feedback snapshot digest 构造`](production-implementation-pi-500-r1-f09-implementation-plan.md:1682) 与 [`feedback submission digest 构造`](production-implementation-pi-500-r1-f09-implementation-plan.md:1689)。

这些 literal definitions 与 canonical PI-210 contract 不兼容。若 constructor 严格校验，adapter 会在进入目标 lifecycle 或 binder 前失败；若 constructor 接受 uppercase，则 Task 1 的 canonical validation 又被违反。零上下文实现者必须自行选择非规范行为，因此属于 High semantic contradiction。

### PI590R5-H-03 — T93 不能由展示的 canonical call graph 静态证明为所声明的 state/event identity failure

T93 交换 source fixture 中的 state 与 event object IDs，见 [`mutate_t93()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2078)。trace adapter 只使用 event object ID 构造 conversion source object，见 [`TransformationRecord.source_object_refs`](production-implementation-pi-500-r1-f09-implementation-plan.md:1435)。展示的 adapter 没有把 state object ID、state fields 或 state pointer 构造成传给 [`validate_statement_projection()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1502) 的独立预期端或对照端。

因此可以静态证明 event source object 会改变，却不能直接证明 validator 同时获得 canonical state identity 并据此识别 state/event swap，更不能证明它必然产出 T93 声明的 SOURCE.LOCATOR_MISMATCH。T93 constructor 的 expected label 见 [`T93`](production-implementation-pi-500-r1-f09-implementation-plan.md:2214)，但 expectation 不是 stimulus evidence。

按 fail-closed 规则，PI590R4-H-02 对 T93 的有效失败声明未被独立关闭。

### PI590R5-H-04 — artifact supersession 被塞入 issue string，未形成 canonical 可审计 identity relation

Task 7 的 [`ArtifactRecord`](production-implementation-pi-500-r1-f09-implementation-plan.md:874) 没有 supersedes identity/ref 字段。artifact adapter 把 superseded revision 编码为 issue string，见 [`record_8`](production-implementation-pi-500-r1-f09-implementation-plan.md:1598)，然后仅把这一合成 record 交给 [`inspect_artifact_set()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1603)。

计划同时要求 old/new refs auditable 和 old identity retained，见 [`T72`](production-implementation-pi-500-r1-f09-implementation-plan.md:2193)，而 canonical trace relation 已定义显式 SUPERSEDES edge 类型，见 [`TraceEdge.edge_type`](production-implementation-pi-500-r1-f09-implementation-plan.md:756)。当前 literal adapter 没有构造 old artifact object ref、new artifact object ref 或显式 supersession relation。issue string 不是 typed identity relation，也没有规范说明允许从 issue ID 解析身份。

零上下文工程师必须发明解析规则或额外数据结构才能满足 T72，因此属于 High architectural gap。

## 4. Medium finding

### PI590R5-M-01 — 31-leaf component tests 只有要求，没有 copyable test definitions

计划要求 component tests 对每个 leaf 做一次 mutation，并证明 target argument changed 以及 non-target arguments equal，见 [`component-test 要求`](production-implementation-pi-500-r1-f09-implementation-plan.md:1232) 和 [`最终验收检查`](production-implementation-pi-500-r1-f09-implementation-plan.md:2281)。但是文档只给出了要求，没有给出 31 个 literal test definitions、参数表或完整 assertion graph。

这不取代 H-01 的直接矛盾，但意味着即使修正 adapter，零上下文工程师仍需自行设计部分 oracle 结构。由于目标是 mechanically implementable plan，该缺口记为 Medium。

## 5. R4 High closure 判定

| R4 finding | 静态判定 | 证据 |
|---|---|---|
| PI590R4-H-01 | NOT CLOSED | 三个 observation dataclasses 与三个 adapters 均已给出 literal bodies，且都有 typed NOT_RUNNABLE 与 typed F09Error aggregation；但 feedback 七维 match 和 anchor availability 是 binder 返回后的 fixture alteration，违反前置消费规则。见 [`TracePhaseObservation`](production-implementation-pi-500-r1-f09-implementation-plan.md:1342)、[`ArtifactPhaseObservation`](production-implementation-pi-500-r1-f09-implementation-plan.md:1353)、[`FeedbackPhaseObservation`](production-implementation-pi-500-r1-f09-implementation-plan.md:1365) 及 [`feedback adapter`](production-implementation-pi-500-r1-f09-implementation-plan.md:1631)。 |
| PI590R4-H-02 | NOT CLOSED | T92 的 frozen event fields、object-root pointer 与六个 LOSSLESS mappings 已显示；T97 的 mapping count 和 terminal edge switch 在 validation 前生效；但 T93 缺少可静态证明的 canonical state/event 对照输入。见 [`BASELINE_SOURCE`](production-implementation-pi-500-r1-f09-implementation-plan.md:1777)、[`六个 mappings`](production-implementation-pi-500-r1-f09-implementation-plan.md:1393)、[`mutate_t97()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2090)。 |

## 6. 31 fixture leaves reachability 结论

### 6.1 Trace：10 leaves

- statement_set_complete、statement_complete、statement_basis_ids、rule_ref_ids、statement_text、issue_propagation_ids、transformation_fidelity、field_mapping_count、external_source_terminated、card_runtime_status 均在调用 [`validate_statement_projection()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1502) 前进入 displayed canonical statement、statement set、trace 或 transformation graph。
- T97 的两个 leaves 都是 pre-call stimulus：mapping slicing 位于 [`selected_event_mappings`](production-implementation-pi-500-r1-f09-implementation-plan.md:1430)，terminal edge selection 位于 [`TraceEnvelope.edges`](production-implementation-pi-500-r1-f09-implementation-plan.md:1494)。
- T93 的失败语义仍不成立，原因见 H-03。

### 6.2 Artifact：10 leaves

- records_write_outcome 与 index_write_outcome 进入 fail boundary；index revision、statement revision、expected digest、observed digest、item states、retry key digest、retry payload digest 均进入 displayed write、inspection 或 retry inputs。
- supersedes_revision 仅进入 issue string，不构成 canonical identity relation，见 H-04。
- 所有 displayed digest constructors 受 H-02 阻断。

### 6.3 Feedback：11 leaves

- target_statement_id、target_revision、source_track、policy_version、item_ids、source_digest、submission_complete、binding_complete、eligibility_complete 均进入某个 displayed canonical constructor、validator 或 evaluator input。
- anchor_status 仅部分进入 binder input的 source span，claimed record-anchor availability 仍在 binder 返回后应用。
- seven_matches 完全在 binder 返回后应用。
- 因而 31/31 的 normative pre-call binder-route 声明不能成立。

## 7. T91–T97 与 PI-300 投影复验

- T91 state source fields 在 literal constructor 中为 level、position、as_of，见 [`mutate_t91()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2072)。
- T92 event source fields 与 frozen snapshot 一致：level、change、interval/start、interval/end、interval/start_inclusive、interval/end_inclusive，见 [`mutate_t92()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2075) 与 [`frozen event payload`](production-implementation-pi-300-f09-source-snapshots-v1.json:20)。
- 六个 literal mappings 均声明 LOSSLESS，且 source paths 由 object-root /value 与六个 event paths 组成，见 [`mapping_1`](production-implementation-pi-500-r1-f09-implementation-plan.md:1393) 至 [`mapping_6`](production-implementation-pi-500-r1-f09-implementation-plan.md:1423)。
- T97 是有效 pre-call mutation，但 exact error classification 仍需未来实现验证；本次不声称 runtime outcome。
- T93 的有效 failure 无法由 displayed call graph 直接证明，见 H-03。

## 8. T01–T104 五路静态 accounting

在不执行 parser 或 collection 的边界内，文档展示了连续、literal 的五类文本结构：

| 类别 | 静态结果 | 证据 |
|---|---:|---|
| concrete mutator definitions | 104 visible, T01–T104 连续 | [`mutate_t01()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1802) 至 [`mutate_t104()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2111) |
| literal constructors | 104 visible, T01–T104 连续 | [`T01 constructor`](production-implementation-pi-500-r1-f09-implementation-plan.md:2122) 至 [`T104 constructor`](production-implementation-pi-500-r1-f09-implementation-plan.md:2225) |
| literal mutator references | 每个 constructor 一项，与同 ID 对齐 | 同上 constructor block |
| complete pytest nodes | 每个 constructor 一项完整 path，与同 ID 对齐 | 同上 constructor block |
| literal tuple entries | T01–T104 连续 | [`SCENARIOS`](production-implementation-pi-500-r1-f09-implementation-plan.md:2227) |

对 displayed block 的直接文本核验结果：missing=0，duplicate=0。T01 的 sole return 是 bundle，见 [`mutate_t01()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1802)；T02–T104 均显示 nested literal replace。compound rows可见于 [`mutate_t43()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1928)、[`mutate_t75()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2024)、[`mutate_t96()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2087)、[`mutate_t102()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2105) 与 [`mutate_t104()`](production-implementation-pi-500-r1-f09-implementation-plan.md:2111)。

限制：这是计划文本的 static literal accounting，不是 AST parse、import 或 pytest collection evidence；本工件不声称节点当前可收集或代码可执行。

## 9. Canonical regression checks

| 检查项 | 静态结论 |
|---|---|
| PI-210 type ownership | 计划指定 ObjectRef、FieldMapping、TransformationRecord 由 Task 1 唯一拥有；Task 6 使用一个 concrete import，见 [`Task 6 import`](production-implementation-pi-500-r1-f09-implementation-plan.md:697)。未发现 Task 6 的竞争性本地声明。 |
| PI-210 digest rules | FAIL：uppercase algorithm token，见 H-02。 |
| PI-220 six gates | 计划显示六个 member identities 与六个 evaluation inputs，且 baseline 为六项，见 [`BASELINE_GATE`](production-implementation-pi-500-r1-f09-implementation-plan.md:1769)。 |
| PI-220 six participation roles | baseline 显示六个独立角色，见 [`BASELINE_PARTICIPATION`](production-implementation-pi-500-r1-f09-implementation-plan.md:1772)。 |
| Competition 与 candidate disposition | literal decision fixtures、T59–T66 及 Task 5 contract 分离表达；未发现以 F08 runtime candidate 作为 baseline。 |
| Root/timing separation | harness 显式构造两个 wrapper 并分别传入 run call，见 [`materialize_f09_decision_inputs()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1334) 与 [`execute_scenario()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1048)。 |
| Five-action discriminated union | Task 5 和 T38–T43 显示 OUTPUT、CONDITIONAL、ASK、ABSTAIN、HUMAN_REVIEW 五分支与 mismatch negative row。 |
| PI-230 binding statuses | BOUND、UNBOUND、AMBIGUOUS、INVALID 四态完整，见 [`FeedbackBinding.status`](production-implementation-pi-500-r1-f09-implementation-plan.md:954)。 |
| PI-230 seven dimensions | 七个字段完整，见 [`FeedbackBinding match dimensions`](production-implementation-pi-500-r1-f09-implementation-plan.md:945)。 |
| PI-230 eligibility statuses | ELIGIBLE、INELIGIBLE、HUMAN_REVIEW 三态完整，见 [`LearningEligibility.status`](production-implementation-pi-500-r1-f09-implementation-plan.md:962)。 |
| F09-only execution | 计划闭合在 engine/f09 与 tests/f09，Task 10 写集 tests-only，见 [`Task 10 closed write set`](production-implementation-pi-500-r1-f09-implementation-plan.md:1013)。 |
| F08 identity/reference-only | baseline runtime candidate 仅 CAND-F09；T31/T32 明确正负边界，见 [`mutate_t31()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1892) 与 [`mutate_t32()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1895)。 |
| Windows cmd.exe compatibility | final commands 使用 Windows-compatible merge-base capture 与 for loop；pytest commands 从 repo root 表述，见 [`final checklist command`](production-implementation-pi-500-r1-f09-implementation-plan.md:2279)。本次未执行。 |
| Production-default authorization | R3 明确未授权且默认关闭，见 [`R3 authorization boundary`](production-implementation-pi-500-r1-f09-implementation-plan.md:2263)。本工件不扩大授权。 |

## 10. 关键证据缺口

1. 当前 static call graph 不能证明 T93 产生其声明的 canonical failure；详见 H-03。
2. 31-leaf component tests 没有 literal test bodies，且 feedback 两个关键 leaves 与 normative binder route 直接冲突；详见 H-01 与 M-01。

## 11. 禁用机制检查

对 normative adapter 与 literal mutator blocks 的静态阅读未见 standalone pass、TODO、NotImplemented、ellipsis body、dynamic attribute access、factory、registry、table parser、catch-all exception 或 dynamic keyword expansion。三个 adapters 仅捕获 typed F09Error，unexpected exceptions 没有被吞掉。宽泛 prose 搜索结果不作为代码违规证据。

该项通过不抵消 H-01 至 H-04。

## 12. 修改文件列表

本次仅创建：

- [`production-implementation-pi-590-r5-g5-plan-reacceptance.md`](production-implementation-pi-590-r5-g5-plan-reacceptance.md)

未修改被复验计划、production code、tests、YAML、mapping、META、cases、reports 或默认配置。

## 13. 唯一下一合法动作

由 PI-500 计划所有者在一个新的、明确授权且仅限计划文档的 remediation 中修订 [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md)，同时解决 H-01 至 H-04 与 M-01；完成后由另一个全新、分离的审阅实例执行下一轮纯静态 G5 reacceptance。此前不得进入实现或测试执行。