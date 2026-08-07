# PI-590-R3 · PI-500-R1 F09 实现计划独立只读复验

## 1. 审查身份、独立性与授权边界

- 复验任务：`PI-590-R3`；父任务：`PI-500 / G5`。
- 被审对象：[`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:1)。
- 本审查实例与 PI-570-R2 整改实例分离；整改作者在 [`PI-570-R2 remediation matrix`](production-implementation-pi-500-r1-f09-implementation-plan.md:1328) 中的关闭自述只用于定位，不作为验收证据。
- 本轮采用静态、只读、fail-closed 复验：未修复被审计划，未修改总控或 handoff，未创建生产代码或测试代码，未运行 pytest，未执行 YAML 或 mapping。
- 唯一写入为本审查工件：[`production-implementation-pi-590-r3-g5-plan-reacceptance.md`](production-implementation-pi-590-r3-g5-plan-reacceptance.md:1)。
- 审查结论不等于 G5 完成；总控仍记录 [`PI-500=BLOCKED`](production-implementation-control.md:92) 与 [`G5=IN_PROGRESS`](production-implementation-control.md:70)。

## 2. 读取基线

本实例直接读取并比较了以下事实源：

1. 仓库入口与 AI 规则：[`README.md`](../README.md)、[`AGENTS.md`](../AGENTS.md)。
2. 当前项目状态：[`project-state.json`](../META/project-state.json:1)。
3. 被审计划：[`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:1)。
4. PI-210 canonical 证据、来源与唯一转换账本：[`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:112)、[`TransformationRecord`](production-implementation-pi-210-normalized-evidence-model.md:665)。
5. PI-220 canonical 判定接口：[`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:90)。
6. PI-230 canonical trace、statement、artifact、feedback 契约：[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:169)。
7. PI-300 F09 垂直测试矩阵：[`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1027)。
8. PI-400-R4 独立技术复验：[`production-implementation-pi-400-r4-g4-technical-rereview.md`](production-implementation-pi-400-r4-g4-technical-rereview.md:51)。
9. PI-590-R1 审查基线：[`production-implementation-pi-590-r1-g5-plan-acceptance.md`](production-implementation-pi-590-r1-g5-plan-acceptance.md:86)。
10. PI-590-R2 直接 finding 基线：[`production-implementation-pi-590-r2-g5-plan-reacceptance.md`](production-implementation-pi-590-r2-g5-plan-reacceptance.md:96)。
11. 治理总控：[`production-implementation-control.md`](production-implementation-control.md:60)。

PI-400-R4 的 PASS 仅证明冻结设计的技术清关，不是本计划的 implementation/runtime test 证明；本轮未据此推定 Task 5、Task 6、Task 8 或 Task 10 已可执行。

## 3. 范围与禁令核验

| 边界 | 静态结果 | 证据 |
|---|---|---|
| F09-only | PASS | 计划明确限定 F09：[`Global Constraints`](production-implementation-pi-500-r1-f09-implementation-plan.md:13)。 |
| F08 identity-only | PASS | F08 只允许作为 identity/reference-only competitor：[`Task 5 review gate`](production-implementation-pi-500-r1-f09-implementation-plan.md:595)。 |
| 冻结源语义 | PASS | CRLF→LF、拒绝 BOM/bare CR、payload-only digest 边界未发现新漂移；对应 checklist 见 [`Final Independent Acceptance Checklist`](production-implementation-pi-500-r1-f09-implementation-plan.md:1291)。 |
| production-default unchanged | PASS | F09 仅显式 opt-in，默认与 `PRODUCTION_DEFAULT` 在 I/O 前停止：[`run_f09_slice()`](production-implementation-pi-500-r1-f09-implementation-plan.md:937)、[`Task 9 Step 1`](production-implementation-pi-500-r1-f09-implementation-plan.md:940)。 |
| implementation | `false` | 计划自身仍声明未实施：[`PI-570-R2 static self-review`](production-implementation-pi-500-r1-f09-implementation-plan.md:1344)。本审查未创建实现。 |
| tests executed | `0` | 本审查未运行 pytest；没有 runtime/collection 结果被作为证据。 |
| YAML executed | `false` | 本审查未执行 YAML。 |
| mapping executed | `false` | 本审查未执行 mapping。 |
| remediation performed | `false` | 本审查未修改被审计划。 |

## 4. PI-590-R2 Finding 关闭矩阵

| R2 finding | R3 裁决 | 逐项证据 |
|---|---|---|
| `PI590R2-H-01` | **CLOSED** | Task 5 已逐字段内联 PI-220 的 contract/package、六成员 declaration/evaluation、六个独立 participation records、competition/counterevidence/disposition、root/timing、field-path issues、顶层 result 与五动作对象；见 [`Task 5 Interfaces`](production-implementation-pi-500-r1-f09-implementation-plan.md:302)。动作 envelope 只有一个判别式 [`DecisionActionEnvelope.payload`](production-implementation-pi-500-r1-f09-implementation-plan.md:558)，五个 payload signatures 位于 [`OutputPayload`](production-implementation-pi-500-r1-f09-implementation-plan.md:518) 至 [`HumanReviewPayload`](production-implementation-pi-500-r1-f09-implementation-plan.md:546)。 |
| `PI590R2-H-02` | **OPEN / AMBIGUOUS** | Task 6 的 PI-230 refs/trace/card identity 字段图大体恢复，但计划在声称 import/reuse 后仍写出三个 Python class declarations：[`ObjectRef`](production-implementation-pi-500-r1-f09-implementation-plan.md:677)、[`FieldMapping`](production-implementation-pi-500-r1-f09-implementation-plan.md:683)、[`TransformationRecord`](production-implementation-pi-500-r1-f09-implementation-plan.md:689)。这与 Task 6 创建 [`engine/f09/trace.py`](production-implementation-pi-500-r1-f09-implementation-plan.md:607) 的落地上下文及“严禁另造”的后置文字冲突，无法证明实现者会 import 唯一 canonical 类型而非把代码块复制进 trace 模块。见 `PI590R3-H-01`。 |
| `PI590R2-H-03` | **CLOSED** | Task 8 已恢复 canonical [`FeedbackItem`](production-implementation-pi-500-r1-f09-implementation-plan.md:857)、[`FeedbackSubmission`](production-implementation-pi-500-r1-f09-implementation-plan.md:870)、[`FeedbackBinding`](production-implementation-pi-500-r1-f09-implementation-plan.md:881) 与 [`LearningEligibility`](production-implementation-pi-500-r1-f09-implementation-plan.md:897)。case/track/run/statement/revision/statement-set/artifact-digest 七维 match 均逐字段存在于 [`FeedbackBinding`](production-implementation-pi-500-r1-f09-implementation-plan.md:885)，且 eligibility 明确只评估、不调用学习：[`Task 8 invariants`](production-implementation-pi-500-r1-f09-implementation-plan.md:910)。 |
| `PI590R2-H-04` | **OPEN** | 计划确有 104 个 literal constructors、104 个不同 mutator references、104 个 literal pytest nodes 与 104-element tuple；但全文 [`mutate_tNN()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1127) 函数定义数为 `0`。constructor 的自然语言 `mutation` 值不能唯一确定 frozen object graph 的具体 changed field path/value，工程师仍需发明 104 个函数体。见 `PI590R3-H-02`。 |
| `PI590R2-M-05` | **CLOSED** | `<base>` 数量为 `0`；跨任务 regression shorthand 数量为 `0`。Task 10 提供唯一完整 regression 命令：[`Task 10 Step 7`](production-implementation-pi-500-r1-f09-implementation-plan.md:1005)；五 payload 已内联；Windows merge-base 与 diff 命令已展开：[`Final Independent Acceptance Checklist`](production-implementation-pi-500-r1-f09-implementation-plan.md:1287)。 |

关闭计数：`3 CLOSED + 2 OPEN`。因此 PI-570-R2 没有真正关闭全部 `H-01` 至 `H-04` 与 `M-05`。

## 5. 逐规范核验

### 5.1 Task 5 对 PI-220

**结果：PASS（本维度未发现新 High/Medium）。**

- 类型与枚举：[`FunctionId`](production-implementation-pi-500-r1-f09-implementation-plan.md:304)、[`StructuralReadinessState`](production-implementation-pi-500-r1-f09-implementation-plan.md:305)、[`ConstraintCheckState`](production-implementation-pi-500-r1-f09-implementation-plan.md:306)、[`ParticipationState`](production-implementation-pi-500-r1-f09-implementation-plan.md:308) 与 canonical 值域一致。
- 六维对象图：declaration、record、binding、set 的字段和非空/双射约束位于 [`GateMemberDeclarationSet`](production-implementation-pi-500-r1-f09-implementation-plan.md:345) 至 [`GateEvaluationSet`](production-implementation-pi-500-r1-f09-implementation-plan.md:371)。
- 六个 participation roles 使用独立 [`ParticipationRoleRecord`](production-implementation-pi-500-r1-f09-implementation-plan.md:381)，未以容器代替记录。
- competition/counterevidence/disposition 位于 [`CompetitionDimensionEvaluation`](production-implementation-pi-500-r1-f09-implementation-plan.md:408) 至 [`CompetitionSet`](production-implementation-pi-500-r1-f09-implementation-plan.md:439)。
- root 与 timing 分账，且 check 只引用 ledger entry IDs：[`RootLedgerEntry`](production-implementation-pi-500-r1-f09-implementation-plan.md:450)、[`TimingLedgerEntry`](production-implementation-pi-500-r1-f09-implementation-plan.md:466)、[`RootTimingConstraintCheck`](production-implementation-pi-500-r1-f09-implementation-plan.md:480)。
- 五动作使用单一 discriminated payload；不存在五个 nullable payload 竞争字段：[`DecisionPayload`](production-implementation-pi-500-r1-f09-implementation-plan.md:551)、[`DecisionActionEnvelope`](production-implementation-pi-500-r1-f09-implementation-plan.md:554)。

### 5.2 Task 6 对 PI-210 / PI-230

**结果：BLOCKED。**

- [`DigestBinding`](production-implementation-pi-500-r1-f09-implementation-plan.md:621)、[`VersionedObjectRef`](production-implementation-pi-500-r1-f09-implementation-plan.md:624)、[`SnapshotRef`](production-implementation-pi-500-r1-f09-implementation-plan.md:635)、[`DecisionTraceRef`](production-implementation-pi-500-r1-f09-implementation-plan.md:646)、[`TraceNode`](production-implementation-pi-500-r1-f09-implementation-plan.md:659)、[`TraceEdge`](production-implementation-pi-500-r1-f09-implementation-plan.md:666)、[`TraceEnvelope`](production-implementation-pi-500-r1-f09-implementation-plan.md:705) 与 [`CardIdentityRef`](production-implementation-pi-500-r1-f09-implementation-plan.md:724) 的字段和值域与 PI-230 canonical 图一致。
- 但是 canonical 类型所有权仍不唯一可执行：PI-210 明确 [`TransformationRecord`](production-implementation-pi-210-normalized-evidence-model.md:710) 是 PI-210/220/230 唯一规范转换记录，PI-230 也要求只复用它并禁止竞争类型：[`PI-230 conversion ledger`](production-implementation-pi-230-traceability-binding.md:482)。被审计划同时给出“Import/reuse”注释和本地 class declarations，形成关键实现歧义。

### 5.3 Task 8 对 PI-230 feedback / eligibility

**结果：PASS（本维度未发现新 High/Medium）。**

- submission、item、source snapshot、parser identity、source span、nullable targets、annotation、integrity、issues、digest、capture time 均已内联。
- binding 四态、eligibility 三态与七维 match 全部逐字段存在。
- 多 item 一对一 binding、target protocol 不互补、operation identity、policy identity 和零学习副作用均明确：[`Task 8 invariants`](production-implementation-pi-500-r1-f09-implementation-plan.md:910)。

### 5.4 Task 10 对 PI-300 与零上下文可实施性

**结果：BLOCKED。**

- 静态 constructors 覆盖 T01–T104，每个恰一次；每项含 literal action/state/issue/path/basis/binding/side-effect/node。
- 静态 mutator symbol references 覆盖 `mutate_t01`–`mutate_t104`，每个恰一次。
- 静态 pytest nodes 覆盖 T01–T104，每个恰一次。
- [`SCENARIOS`](production-implementation-pi-500-r1-f09-implementation-plan.md:1235) 是 literal 104-element tuple，无 range、generator、dynamic ID 或 table parser。
- 但 `104 references != 104 concrete mutators`。计划仅规定 future functions “应用 named mutation”并验证 exact delta：[`mutator obligation`](production-implementation-pi-500-r1-f09-implementation-plan.md:1127)、[`exact-delta prose`](production-implementation-pi-500-r1-f09-implementation-plan.md:1238)。没有一个函数体，也没有逐函数 frozen object replacement expression、目标字段 path 与 literal replacement value。按本次硬门，“工程师仍需自行发明每个变异的字段和值”即必须 BLOCKED。

## 6. 两项特别裁决

### 6.1 `TransformationRecord` 是否仍构成本地重复定义

**裁决：是，至少构成 High 级关键实现歧义；本轮按 fail-closed 视为未关闭。**

理由：

1. Task 6 的文件写集要求创建 [`engine/f09/trace.py`](production-implementation-pi-500-r1-f09-implementation-plan.md:607)。
2. 紧随“Import/reuse”注释后的内容不是 import statement 或类型别名，而是可复制的 [`class ObjectRef`](production-implementation-pi-500-r1-f09-implementation-plan.md:678)、[`class FieldMapping`](production-implementation-pi-500-r1-f09-implementation-plan.md:684)、[`class TransformationRecord`](production-implementation-pi-500-r1-f09-implementation-plan.md:690) declarations。
3. 同一 Task 又要求不得在 trace、contracts 或 fixture 另造 conversion 类型：[`Task 6 invariant`](production-implementation-pi-500-r1-f09-implementation-plan.md:779)。
4. 零上下文工程师无法同时逐字遵守“以下是完整接口代码块”和“不得另造”；注释不能改变 Python declaration 的语义。

因此字段逐值一致也不能消除类型身份分裂风险。计划必须明确只在 Task 1 的 canonical module 定义一次，并在 Task 6 给出唯一具体 import；本审查不代为修复。

### 6.2 104 个 `mutate_tNN` symbols 是否等于 concrete mutators

**裁决：否；构成 High 级关键证据缺口，必须 BLOCKED。**

理由：

1. 104 个 constructor references 和 104 个唯一 symbol 名只证明名称覆盖，不证明行为被定义。
2. 全文 concrete [`def mutate_tNN()`](production-implementation-pi-500-r1-f09-implementation-plan.md:1127) bodies 数量为 `0`。
3. 如 “delete required set field”“construct each canonical item state”“break binding/evidence/path/relation/decision”等 mutation prose 仍包含多个可选字段、值和对象层级；实现者必须自行选择具体 frozen replacement。
4. harness 只调用 [`scenario.mutate()`](production-implementation-pi-500-r1-f09-implementation-plan.md:980)，没有任何机制把 prose 自动、唯一地转成 mutation；计划又正确禁止 table parser、registry、factory 和 dynamic generation。

所以 Task 10 尚未达到 literal executable scenario data / concrete mutator 的零上下文要求。

## 7. 机械计数与搜索证据

使用只读文本解析对 constructor listing 和全文做静态计数；未导入计划代码、未执行 YAML/mapping、未运行 pytest。

| 检查 | 结果 |
|---|---:|
| literal [`VerticalScenario`](production-implementation-pi-500-r1-f09-implementation-plan.md:963) constructor assignments | `104`；unique `104`；missing `0`；duplicate `0` |
| literal `mutate=mutate_tNN` references | `104`；unique `104`；missing `0`；duplicate `0` |
| complete literal pytest nodes | `104`；unique `104`；missing `0`；duplicate `0` |
| literal [`SCENARIOS`](production-implementation-pi-500-r1-f09-implementation-plan.md:1235) tuple IDs | `104`；unique `104`；missing `0`；duplicate `0` |
| concrete `def mutate_tNN(...)` definitions | `0`；missing `104` |
| `<base>` | `0` |
| `Use the related repository command already listed by Tasks 1–9` | `0` |
| local-looking `class ObjectRef` declarations | `1` |
| local-looking `class FieldMapping` declarations | `1` |
| local-looking `class TransformationRecord` declarations | `1` |

关于禁止动态替代：命中 “range/generator/table parser/generated node” 的位置是明确禁令：[`mutator constraints`](production-implementation-pi-500-r1-f09-implementation-plan.md:1127)，不是动态实现。未发现实际 range、generator、dynamic ID 或 inferred expectation 数据定义。

关于 Windows 命令：

- Task 10 regression 命令已完整展开且为仓库根相对路径：[`Task 10 Step 7`](production-implementation-pi-500-r1-f09-implementation-plan.md:1005)。
- merge-base capture 与 `for /f` diff 命令符合 Windows `cmd.exe` 语法，并区分交互式 `%B` 与 batch `%%B`：[`Final Independent Acceptance Checklist`](production-implementation-pi-500-r1-f09-implementation-plan.md:1287)。
- 未发现 `rm`、`cp`、`mv`、`grep`、`sed` 等 Unix-only 命令。

## 8. Findings

### PI590R3-H-01 — High — Task 6 仍把 PI-210 唯一转换类型写成可复制的本地 class declarations

**精确证据：**

- Task 6 声称 import/reuse：[`Import/reuse comment`](production-implementation-pi-500-r1-f09-implementation-plan.md:676)。
- 随后却声明 [`ObjectRef`](production-implementation-pi-500-r1-f09-implementation-plan.md:677)、[`FieldMapping`](production-implementation-pi-500-r1-f09-implementation-plan.md:683)、[`TransformationRecord`](production-implementation-pi-500-r1-f09-implementation-plan.md:689)。
- 同一 Task 又禁止另造：[`Task 6 invariant`](production-implementation-pi-500-r1-f09-implementation-plan.md:779)。
- PI-210 唯一所有权规则：[`PI-210 sole canonical conversion record`](production-implementation-pi-210-normalized-evidence-model.md:710)。

**影响：** 零上下文工程师可能在 [`engine/f09/trace.py`](production-implementation-pi-500-r1-f09-implementation-plan.md:607) 创建第二组同字段、不同 runtime identity 的类型，破坏 PI-210/230 单一 ledger、跨模块类型检查和 trace reachability。

**裁决：** `PI590R2-H-02` 未关闭；关键架构歧义按 High 阻断。

### PI590R3-H-02 — High — Task 10 只有 104 个 mutator 名称，没有 104 个 concrete mutator bodies

**精确证据：**

- 104 个 literal constructors 位于 [`T01`](production-implementation-pi-500-r1-f09-implementation-plan.md:1130) 至 [`T104`](production-implementation-pi-500-r1-f09-implementation-plan.md:1233)。
- 函数体仅由 prose 委托未来实现：[`mutator obligation`](production-implementation-pi-500-r1-f09-implementation-plan.md:1127)。
- exact changed path/value 仍由未来测试去断言，而非在计划中逐函数给出：[`exact-delta prose`](production-implementation-pi-500-r1-f09-implementation-plan.md:1238)。
- 静态计数：mutator references=`104`，concrete definitions=`0`。

**影响：** 工程师仍须为每个场景发明目标 frozen object、field path、literal replacement value、compound mutation 顺序以及 non-target equality 边界；无法从计划机械实现 T01–T104 的 executable scenarios。

**裁决：** `PI590R2-H-04` 未关闭；关键证据缺口按 High 阻断。

### Finding 计数

- High：`2`
- Medium：`0`
- Low：`0`
- Critical ambiguity：`1`（`PI590R3-H-01`，已计入 High，不重复计数）
- Key evidence gap：`1`（`PI590R3-H-02`，已计入 High，不重复计数）
- Relevant regression failures：`0`（按禁令未运行 pytest，不表示 runtime 通过）
- Findings 总数：`2`

## 9. 总裁决

# BLOCKED

Fail-closed 条件要求 High、Medium、critical ambiguity 和关键证据缺口全部为零。本轮存在 `2 High`，其中一个是唯一类型所有权的关键架构歧义，另一个是 104 个 concrete mutators 缺失的关键可执行证据缺口。因此 PI-570-R2 未真正关闭 PI-590-R2 的全部 findings，PI-500 计划不能进入实现。

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

## 10. 下一步

由与本审查实例分离的整改实例，仅在 [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:1) 内有界消除 `PI590R3-H-01` 与 `PI590R3-H-02`，随后由新的独立实例进行只读复验。整改前不得进入生产实现、不得创建测试、不得运行 pytest、不得执行 YAML 或 mapping；本工件不修改总控，也不宣称 G5 完成。
