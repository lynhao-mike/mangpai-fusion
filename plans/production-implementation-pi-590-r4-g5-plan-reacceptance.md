# PI-590-R4 · PI-500-R1 F09 实施计划独立只读复验

## 1. 审查身份、独立性、范围与禁令

- 复验任务：`PI-590-R4`；父任务：`PI-500 / G5`。
- 被审对象：[`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:1)。
- 本审查实例与 PI-570-R3 整改实例分离；整改者在被审计划中的自述、计数和关闭结论只用于定位，不作为验收证据。
- 本轮采用全新、静态、只读、fail-closed 复验；证据来自本实例直接读取、搜索、连续 ID 核对与逐字段对照。
- 本轮未修复被审计划，未修改总控、handoff、历史审查、生产代码或测试代码。
- 唯一写入为本审查工件：[`production-implementation-pi-590-r4-g5-plan-reacceptance.md`](production-implementation-pi-590-r4-g5-plan-reacceptance.md:1)。
- 未运行 pytest，未导入或执行计划中的 Python 代码，未执行 YAML 或 mapping。
- 本裁决不等于 G5 完成；父任务仍负责最终接收以及总控、handoff 同步。

## 2. 独立读取基线

本实例直接读取并比较：

1. [`README.md`](../README.md)、[`AGENTS.md`](../AGENTS.md) 与 [`project-state.json`](../META/project-state.json:1)。
2. 被审计划 [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:1)。
3. PI-210 canonical evidence/source/transformation 契约：[`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:112)。
4. PI-220 decision interface：[`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:90)。
5. PI-230 trace/artifact/feedback binding：[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:169)。
6. PI-300 F09 冻结垂直切片设计：[`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:754)。
7. PI-400-R4 技术复验：[`production-implementation-pi-400-r4-g4-technical-rereview.md`](production-implementation-pi-400-r4-g4-technical-rereview.md:1)。
8. 历史 PI-590-R1/R2/R3 审查：[`production-implementation-pi-590-r1-g5-plan-acceptance.md`](production-implementation-pi-590-r1-g5-plan-acceptance.md:1)、[`production-implementation-pi-590-r2-g5-plan-reacceptance.md`](production-implementation-pi-590-r2-g5-plan-reacceptance.md:1)、[`production-implementation-pi-590-r3-g5-plan-reacceptance.md`](production-implementation-pi-590-r3-g5-plan-reacceptance.md:1)。
9. 治理总控：[`production-implementation-control.md`](production-implementation-control.md:60)。

历史审查只作为 finding 身份基线；本轮 closure 结论不采信历史作者或整改者的自报计数。

## 3. PI-590-R3 两项 Finding 关闭矩阵

| R3 finding | R4 独立裁决 | 证据与边界 |
|---|---|---|
| `PI590R3-H-01` | **CLOSED** | Task 1 唯一定义 [`ObjectRef`](production-implementation-pi-500-r1-f09-implementation-plan.md:184)、[`FieldMapping`](production-implementation-pi-500-r1-f09-implementation-plan.md:190)、[`TransformationRecord`](production-implementation-pi-500-r1-f09-implementation-plan.md:196)。Task 6 只给出一个精确 import：[`from engine.f09.contracts import FieldMapping, ObjectRef, TransformationRecord`](production-implementation-pi-500-r1-f09-implementation-plan.md:698)。[`TraceEnvelope.transformations`](production-implementation-pi-500-r1-f09-implementation-plan.md:765) 使用该 imported canonical type；RED test 明确验证三项 runtime identity：[`Task 6 RED`](production-implementation-pi-500-r1-f09-implementation-plan.md:841)。全文未发现 Task 6 的本地重复 class、canonical-name alias、wrapper 或 import fallback；最终 review gate 也逐字固定唯一 ownership：[`Final checklist`](production-implementation-pi-500-r1-f09-implementation-plan.md:1824)。 |
| `PI590R3-H-02` | **PARTIAL / OPEN** | 原 finding 的 concrete-mutator 缺失子项已关闭：[`mutate_t01()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1339) 至 [`mutate_t104()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1648) 连续存在，constructor 与 tuple 也完整。但 finding 的 fixture→Task 5–8 concrete reachability、禁止 dead switch、禁止实现者发明 adapter logic 的验收条件未关闭：计划调用三个 post-run adapters，却没有定义这三个函数及其三个 observation dataclasses；见第 6 节。 |

结论：H-01 已真实关闭；H-02 只关闭了“104 bodies 不存在”这一子问题，不能整体标记 CLOSED。

## 4. H-01 唯一类型所有权专项核验

| 核验项 | 结果 | 独立证据 |
|---|---|---|
| Task 1 唯一规划 canonical owner | PASS | 三个 frozen class 连续定义于 [`engine/f09/contracts.py` 规划块](production-implementation-pi-500-r1-f09-implementation-plan.md:183)。 |
| Task 6 精确 import | PASS | 唯一精确语句位于 [`Task 6 interface block`](production-implementation-pi-500-r1-f09-implementation-plan.md:698)。 |
| Task 6 本地重复声明 | PASS，数量 `0` | Task 6 从 import 后直接定义 trace 类型；未出现第二组 `class ObjectRef`、`class FieldMapping` 或 `class TransformationRecord`。 |
| alias / wrapper / fallback | PASS，数量 `0` | 未发现 canonical-name alias、structurally competing wrapper、`try/except ImportError` fallback 或替代 element type。 |
| runtime identity | PASS | [`TraceEnvelope.transformations`](production-implementation-pi-500-r1-f09-implementation-plan.md:775) 为 `tuple[TransformationRecord, ...]`，并有三项 `is` identity assertions：[`Task 6 RED`](production-implementation-pi-500-r1-f09-implementation-plan.md:841)。 |
| TDD、职责、review gate | PASS | RED/GREEN、最小 implementation、回归、commit、independent review 与 rollback 均在 Task 6 明确；最终唯一类型 gate 位于 [`Final checklist`](production-implementation-pi-500-r1-f09-implementation-plan.md:1824)。 |

## 5. T01–T104 机械静态核验

### 5.1 计数与连续性

本轮只对被审计划中的 literal Python blocks 做静态文本核对，不导入或执行代码。定义块从 [`mutate_t01()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1339) 连续到 [`mutate_t104()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1648)；constructor block 从 [`T01`](production-implementation-pi-500-r1-f09-implementation-plan.md:1659) 连续到 [`T104`](production-implementation-pi-500-r1-f09-implementation-plan.md:1762)；literal tuple 位于 [`SCENARIOS`](production-implementation-pi-500-r1-f09-implementation-plan.md:1764)。

| 检查 | 独立静态结果 |
|---|---:|
| top-level `def mutate_tNN` definitions | `104` |
| unique definition IDs | `104` |
| missing IDs in T01–T104 | `0` |
| duplicate definition IDs | `0` |
| literal `VerticalScenario` constructors | `104` |
| distinct `mutate=mutate_tNN` references | `104` |
| complete literal pytest nodes | `104` |
| unique pytest nodes | `104` |
| literal `SCENARIOS` tuple elements | `104` |
| tuple missing IDs | `0` |
| tuple duplicate IDs | `0` |

计数方法：按连续 literal 行逐 ID 核对 T01–T104，并分别比对 function suffix、constructor LHS、`test_id`、mutator reference、pytest node suffix 与 tuple element；未把搜索工具返回的上下文分组数误当作 match 数。由于禁止执行计划代码，本轮不声称 AST parser 或 pytest collection 已运行。

### 5.2 函数体规则

- [`mutate_t01()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1339) 的唯一行为是 `return bundle`。
- T02–T104 均写成显式 top-level function，并使用 `replace(bundle, ...)` 与至少一个 nested `replace(bundle.<domain>, literal-field=literal-value)`；定义块未发现 omitted body。
- 定义块未发现 `pass`、函数体 ellipsis、TODO/TBD/FIXME、range、generator、loop/comprehension、dynamic ID、`getattr`、registry、factory、table parser 或 shared catch-all mutator。
- constructor、node 与 tuple 均为 literal data；没有 range/generator/dynamic builder 替代 exactly-once mapping。

### 5.3 Compound 深检

| 场景 | 结果 | 核验摘要 |
|---|---|---|
| [`mutate_t43()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1465) | PASS | 在 `decision` 上同时写入 `selected_action=ASK`、`payload_type=OutputPayload`、literal question path，形成固定 discriminator mismatch。 |
| [`mutate_t75()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1561) | PASS | `member_ids` 固定重复 SOURCE 并遗漏 TEMPORAL，`declared_member_ids` 保持 canonical 六成员。 |
| [`mutate_t96()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1624) | PASS | 同时漂移 snapshot ID、schema version、contract version、content digest、capture time 与 payload digest。 |
| [`mutate_t102()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1642) | PASS | 同时设置 risk/allocation UNKNOWN，并并列 registered 与 unregistered reason code。 |
| [`mutate_t104()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1648) | PASS | 固定组合 unknown member、forged gate ref、forged binding digest、unregistered reason、declaration digest drift 与 source payload digest drift。 |

上述字段均存在于相应 frozen input dataclass，且 baseline graph 给出 literal 初值。其余 mutators 也只修改已声明 domain field；未发现对不存在字段的 literal replacement。

## 6. Fixture → materializer / consumer 可达性

### 6.1 Task 5 decision inputs

**结果：PASS。**

[`materialize_f09_decision_inputs()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1317) 使用四个 direct canonical wrapper constructors，生成 `gate_inputs`、`competition_input`、`root_input`、`timing_input`；[`execute_scenario()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1046) 以四个显式 keyword 传入 [`run_f09_slice()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1050)。没有 `mutated.decision_inputs`、`**` expansion、fixture dict parser 或动态 factory。

### 6.2 Task 6–8 post-run consumers

**结果：BLOCKED。**

Harness 只有三个调用点：

- [`exercise_trace_validation_phase()` call](production-implementation-pi-500-r1-f09-implementation-plan.md:1057)
- [`exercise_artifact_lifecycle_phase()` call](production-implementation-pi-500-r1-f09-implementation-plan.md:1058)
- [`exercise_feedback_binding_phase()` call](production-implementation-pi-500-r1-f09-implementation-plan.md:1059)

[`ScenarioExecution`](production-implementation-pi-500-r1-f09-implementation-plan.md:1039) 也只引用 `TracePhaseObservation`、`ArtifactPhaseObservation`、`FeedbackPhaseObservation` 类型名。本实例全文搜索没有找到以下六个 literal definitions：

- `class TracePhaseObservation`
- `class ArtifactPhaseObservation`
- `class FeedbackPhaseObservation`
- `def exercise_trace_validation_phase(...)`
- `def exercise_artifact_lifecycle_phase(...)`
- `def exercise_feedback_binding_phase(...)`

计划仅以 prose 描述三者应构造哪些 canonical Task 6–8 objects：[`consumer prose`](production-implementation-pi-500-r1-f09-implementation-plan.md:1211) 与 [`leaf-to-port table`](production-implementation-pi-500-r1-f09-implementation-plan.md:1215)。但计划自己又明确要求三 adapter 与 typed observations 必须 literal 定义，并禁止用 prose 或 undefined helper 代替：[`no-omission rule`](production-implementation-pi-500-r1-f09-implementation-plan.md:1230)。这是内部直接矛盾。

因此以下关键逻辑仍需实现者发明：

1. 把 trace fixture leaves 构造成 canonical `TraceEnvelope`、`StatementSet`、`StandardStatement`、`TransformationRecord` 与 terminal edges 的精确 constructor/replace 图。
2. 把 artifact fixture leaves 构造成 projections、failure boundary、prior `ArtifactSetManifest`、`ArtifactRecord`、`IdempotencyKey` 与 retry payload 的精确输入。
3. 把 feedback fixture leaves 构造成完整 `FeedbackSubmission`、`FeedbackItem`、returned `FeedbackBinding` mutation 与 `LearningEligibility` validation input。
4. 三个 typed phase observation 的字段、not-runnable 表示及 error/result 汇总方式。

尤其 `statement_set_complete`、`statement_complete`、`submission_complete`、`binding_complete`、`eligibility_complete` 等 boolean leaves，没有 literal consumer body 证明它们改变 canonical call input，而不是 expectation-only switch。按计划自身 dead-switch gate 与本轮零上下文硬门，H-02 不能整体关闭。

## 7. PI-210 / PI-220 / PI-230 / PI-300 回归核验

| 规范维度 | 结果 | 独立核验 |
|---|---|---|
| PI-210 三轨证据、source binding、declaration binding | PASS | Task 1/3/4 保持 CHART_STRUCTURE、REALITY_FACT、UNVERIFIED_HYPOTHESIS 隔离、canonical source locator/binding 与五态 declaration；未发现本地替代状态。 |
| PI-210 conversion ledger identity | PASS | H-01 已关闭；唯一 class owner、精确 import 与 runtime identity assertions 齐备。 |
| PI-220 六成员 declaration/evaluation 双射 | PASS | Task 5 明确 member identity、shared definition ref、evaluation binding 与 bijection；T74–T81 覆盖 cardinality、unknown member、binding、permutation 与 reorder。 |
| PI-220 participation | PASS | 六个 independent participation roles 与 scenario-local reality record 约束存在；T46–T48、T87–T88 覆盖。 |
| PI-220 competition/disposition | PASS | counterevidence、candidate disposition、exact match 与 action compatibility 存在；F08 仅 identity/reference。 |
| PI-220 root/timing | PASS | 两套 ledger 分离，timing 禁止重写 root；T17、T49–T51 覆盖。 |
| PI-220 五动作 union | PASS | OUTPUT、CONDITIONAL、ASK、ABSTAIN、HUMAN_REVIEW 使用单一 discriminated payload；T38–T43 覆盖。 |
| PI-230 trace/statement | **BLOCKED by missing adapter** | 契约字段本身大体一致，但 Task 10 没有 literal trace adapter 证明 mutated fixture 进入 [`validate_statement_projection()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1217)。 |
| PI-230 artifact lifecycle | **BLOCKED by missing adapter** | 八态、append-only attempts、retry/idempotency 规划存在，但 Task 10 没有 literal artifact adapter。 |
| PI-230 feedback/eligibility | **BLOCKED by missing adapter** | canonical submission/item、四态 binding、七维 match、三态 eligibility 与零学习副作用存在，但 Task 10 没有 literal feedback adapter。 |
| PI-300 state projection | PASS | fixture 的 `level/position/as_of` 与 PI-300 locators 一致：[`state locators`](production-implementation-pi-300-one-card-vertical-slice-design.md:778)。 |
| PI-300 bounded outcome | PASS | fixture 的 `axis/action/object/tense` 与冻结四字段一致：[`outcome locators`](production-implementation-pi-300-one-card-vertical-slice-design.md:791)。 |
| PI-300 event projection | **BLOCKED / semantic mismatch** | 见第 8 节。 |
| F08 identity-only | PASS | T31 正例与 T32 forged executable F08 负例保持边界。 |
| frozen Markdown/JCS | PASS at plan level | CRLF→LF、BOM/bare CR rejection、payload-only bounded JCS 与冻结 digest 均有明确计划；本轮未执行验证。 |

## 8. Findings

### PI590R4-H-01 — High — 三个 mandatory post-run adapters 与三个 typed observations 只有引用和 prose，没有 literal definitions

**精确证据：**

- Harness 调用三个函数：[`execute_scenario()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1046)。
- Harness 引用三个 observation 类型：[`ScenarioExecution`](production-implementation-pi-500-r1-f09-implementation-plan.md:1039)。
- 计划要求每个 fixture leaf 进入 concrete Task 6–8 call input：[`leaf-to-port table`](production-implementation-pi-500-r1-f09-implementation-plan.md:1215)。
- 计划明确禁止省略 literal adapter definitions：[`no-omission rule`](production-implementation-pi-500-r1-f09-implementation-plan.md:1230)。
- 本实例全文搜索六个定义，结果均为 `0`；只有 type references、call sites 与 prose。

**影响：** Task 10 无法在零上下文下实现；31 个 trace/artifact/feedback leaves 的 production-port reachability 没有 concrete code evidence，多个 boolean leaves 可能成为 dead expectation switches。工程师必须发明 canonical constructors、nested replacements、phase observations 和 not-runnable 行为。

**裁决：** `PI590R3-H-02` 仅部分关闭；fixture→consumer 关键证据缺口按 High 阻断。

### PI590R4-H-02 — High — T92 event fixture 字段与 PI-300 冻结 JSON event shape 不一致，且缺少 literal adapter 消除歧义

**精确证据：**

- PI-300 冻结 event 六字段及 object-root locators 为 `level`、`change`、`interval/start`、`interval/end`、`interval/start_inclusive`、`interval/end_inclusive`：[`PI-300 event locators`](production-implementation-pi-300-one-card-vertical-slice-design.md:783)。
- PI-300 的六个 LOSSLESS mappings 使用上述精确 paths：[`TR-F09-EVENT-1`](production-implementation-pi-300-one-card-vertical-slice-design.md:829)。
- 被审计划 baseline/T92 却把 event fields 写成 `event_type`、`occurred_at`、`actor`、`object`、`direction`、`magnitude`：[`mutate_t92()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1612)。
- T92 constructor 同时宣称“six event fields and pointers”“six lossless mappings”“same event identity”：[`T92`](production-implementation-pi-500-r1-f09-implementation-plan.md:1750)。
- 缺失的 trace adapter 没有 literal mapping 说明这六个非冻结名称如何变成 PI-300 的六个真实 source paths。

**影响：** 零上下文实现者只能选择发明字段转换、错误地构造不存在的 source locators，或偏离 PI-300 frozen source semantics。任何一种都破坏 T92 的 LOSSLESS 与 same-event-identity 断言，并可能使 T92 成为 expectation-only 正例。

**裁决：** frozen-source semantic regression 与关键 adapter ambiguity 均为 High；按 fail-closed 阻断。

### Finding 计数

- High：`2`
- Medium：`0`
- Low：`0`
- Critical ambiguity：`1`，即 missing adapter definitions；已计入 High，不重复计数。
- Key evidence gap：`1`，即 fixture→Task 6–8 concrete reachability；已计入 High，不重复计数。
- Relevant runtime regression failures：`0`；本轮按禁令未运行 pytest，不表示 runtime 通过。
- Findings 总数：`2`

## 9. Placeholder、命令与治理边界

| 项目 | 结果 |
|---|---|
| mutator bodies 中 placeholder/shorthand | `0`；未发现 `pass`、omitted body、TODO/TBD/FIXME、dynamic generator。 |
| Task 10 regression command | PASS；完整 Windows 仓库根命令位于 [`Task 10 Step 7`](production-implementation-pi-500-r1-f09-implementation-plan.md:1089)。 |
| immutable comparison ref | PASS；[`cmd.exe` merge-base/for-f commands](production-implementation-pi-500-r1-f09-implementation-plan.md:1816) 区分交互 `%B` 与 batch `%%B`。 |
| Unix-only commands | 未发现 `rm`、`cp`、`mv`、`grep`、`sed` 被要求用于 Windows workflow。 |
| F09-only | `true` |
| F08 identity-only | `true` |
| frozen semantics | event projection finding 除外，其余静态边界保持；因此总体不通过。 |
| production-default unchanged | `true` |
| implementation | `false` |
| tests executed | `0` |
| YAML executed | `false` |
| mapping executed | `false` |
| remediation performed | `false` |

## 10. 总裁决

# BLOCKED

Fail-closed 通过条件要求 High=`0`、Medium=`0`、critical ambiguity=`0`、key evidence gap=`0`。本轮独立复验确认 `PI590R3-H-01` 已关闭，且 104 concrete mutator bodies、constructors、references、nodes 与 tuple 已完整落字；但仍存在 `2 High`：

1. 三个 mandatory Task 6–8 post-run adapters 与三个 typed observations 完全没有 literal definitions，导致 fixture→consumer reachability 不可证明。
2. T92 event fixture 字段与 PI-300 冻结 event source shape 实质不一致，且不存在 concrete adapter 解释或消除该漂移。

因此被审计划尚未达到零上下文可实施性，`PI590R3-H-02` 不能整体关闭，PI-500 不得进入实现。

固定状态：

- `tests executed=0`
- `implementation=false`
- `production-default unchanged`
- `YAML executed=false`
- `mapping executed=false`
- `remediation performed=false`
- `F09 only=true`
- `F08 identity-only=true`
- `PI-500=BLOCKED`
- `G5=IN_PROGRESS`

## 11. 下一步

由与本审查实例分离的整改实例，仅在 [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:1) 内有界处理 `PI590R4-H-01` 与 `PI590R4-H-02`；随后由新的独立实例执行只读复验。整改前不得创建生产实现或测试、不得运行 pytest、不得执行 YAML 或 mapping。本工件不修改总控或 handoff，也不宣称 G5 完成。
