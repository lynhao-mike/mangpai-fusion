# PI-590-R2 · PI-500-R1 F09 整改后实现计划独立复验

## 1. 独立性、授权与范围

- 复验任务：`PI-590-R2`；父任务：`PI-500 / G5`。
- 被验收对象：[`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:1)。
- 本实例只做分离实例、只读、fail-closed 复验；未采信计划自身的 [`READY_FOR_INDEPENDENT_REACCEPTANCE`](production-implementation-pi-500-r1-f09-implementation-plan.md:870) 或整改自述作为验收证据。
- 技术范围仅为 F09；F08 仅可作为 identity-only competitor；mapping 未执行。
- 未修复计划，未实现生产代码，未创建或修改测试，未运行 pytest，未执行声明性 YAML，未改变 production-default。
- recursion：`allowed=false`，`remaining_depth=0`；未委派子任务。
- 唯一写入为本复验记录：[`production-implementation-pi-590-r2-g5-plan-reacceptance.md`](production-implementation-pi-590-r2-g5-plan-reacceptance.md:1)。

## 2. 治理事实与事实源

### 2.1 治理事实

- 总控当前明确记录 G4=`COMPLETED`、G5=`IN_PROGRESS`：[`production-implementation-control.md`](production-implementation-control.md:69)。
- 用户于 2026-07-20 的“以子任务完成G5”已被登记为 G4 用户批准硬门解除证据：[`production-implementation-control.md`](production-implementation-control.md:228)。
- R1 的 `PI590-H-01` 已由父实例认定为治理登记时序滞后并关闭：[`production-implementation-control.md`](production-implementation-control.md:230)。本复验不重开该 finding。
- PI-500 在新的独立复验通过前仍为 `BLOCKED`：[`production-implementation-control.md`](production-implementation-control.md:92)。

### 2.2 直接核对的事实源

1. 仓库入口与 AI 规则：[`README.md`](../README.md)、[`AGENTS.md`](../AGENTS.md)。
2. 项目状态：[`project-state.json`](../META/project-state.json:1)。
3. 治理总控：[`production-implementation-control.md`](production-implementation-control.md:60)。
4. PI-210 canonical 证据与来源契约：[`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:262)。
5. PI-220 canonical 判定接口：[`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:147)。
6. PI-230 canonical trace、statement、artifact、feedback 契约：[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:169)。
7. PI-300 F09 设计与场景矩阵：[`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1027)。
8. PI-400-R4 冻结源机械证据：[`production-implementation-pi-400-r4-g4-technical-rereview.md`](production-implementation-pi-400-r4-g4-technical-rereview.md:51)。
9. R1 finding 基线：[`production-implementation-pi-590-r1-g5-plan-acceptance.md`](production-implementation-pi-590-r1-g5-plan-acceptance.md:86)。
10. 整改后实现计划：[`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:1)。

## 3. 只读机械检查证据

### 3.1 T01–T104 marker 限界解析

只解析 [`PI-570-R1-SCENARIOS-BEGIN`](production-implementation-pi-500-r1-f09-implementation-plan.md:673) 与 [`PI-570-R1-SCENARIOS-END`](production-implementation-pi-500-r1-f09-implementation-plan.md:780) 之间的 Markdown 表体，并以首列严格匹配 `T\d{2,3}`：

- body rows：`104`；
- ID 集合及顺序：字面 `T01` 至 `T104`，每个恰一次；
- duplicate IDs：`0`；missing IDs：`0`；
- 每个 body row：`9` 列；空单元格：`0`；
- pytest node：`104` 个且字面唯一，均以本行 `[Txx]` 结尾；
- marker 外的 T ID 未纳入计数。

重点逐项与 PI-300 交叉核对：

| ID | 计划行 | PI-300 行 | 静态结论 |
|---|---:|---:|---|
| T01 | [`T01`](production-implementation-pi-500-r1-f09-implementation-plan.md:676) | [`T01`](production-implementation-pi-300-one-card-vertical-slice-design.md:1031) | purpose、完整基线、OUTPUT、非空 basis 与不扩张精度一致。 |
| T19 | [`T19`](production-implementation-pi-500-r1-f09-implementation-plan.md:694) | [`T19`](production-implementation-pi-300-one-card-vertical-slice-design.md:1049) | statement binding 漂移、invalid 与逐值绑定一致。 |
| T31 | [`T31`](production-implementation-pi-500-r1-f09-implementation-plan.md:706) | [`T31`](production-implementation-pi-300-one-card-vertical-slice-design.md:1061) | 仅 F09 candidate/disposition，F08 只留引用且不执行，一致。 |
| T52 | [`T52`](production-implementation-pi-500-r1-f09-implementation-plan.md:727) | [`T52`](production-implementation-pi-300-one-card-vertical-slice-design.md:1082) | 行级意图一致，但 Task 8 实际接口没有完整 canonical submission/item 字段；见 `PI590R2-H-03`。 |
| T74 | [`T74`](production-implementation-pi-500-r1-f09-implementation-plan.md:749) | [`T74`](production-implementation-pi-300-one-card-vertical-slice-design.md:1104) | 六成员、六 records、按 member ID 全双射且顺序无关，一致。 |
| T90 | [`T90`](production-implementation-pi-500-r1-f09-implementation-plan.md:765) | [`T90`](production-implementation-pi-300-one-card-vertical-slice-design.md:1120) | actual Markdown、actual JSON fixture、两类 binding 与禁止 YAML/prose 替代，一致。 |
| T96 | [`T96`](production-implementation-pi-500-r1-f09-implementation-plan.md:771) | [`T96`](production-implementation-pi-300-one-card-vertical-slice-design.md:1126) | snapshot identity、payload-only JCS 与 fail-closed 方向一致。 |
| T104 | [`T104`](production-implementation-pi-500-r1-f09-implementation-plan.md:779) | [`T104`](production-implementation-pi-300-one-card-vertical-slice-design.md:1134) | 综合 member/binding/digest/reason 攻击与禁止降级修复一致。 |

结论：**literal Markdown 场景表的 104 行完整性通过；可执行 scenario 数据设计仍不通过。** 计划只给出一个真实 [`VerticalScenario`](production-implementation-pi-500-r1-f09-implementation-plan.md:616) constructor（T01），其余 103 行只是未来应转换的数据表，并不是字面的 [`SCENARIOS`](production-implementation-pi-500-r1-f09-implementation-plan.md:643) constructors；见 `PI590R2-H-04`。

### 3.2 CRLF、BOM 与冻结源语义

- 计划明确接受 LF/CRLF，并在摘要和 COPY 前把 CRLF 规范化为 LF：[`Global Constraints`](production-implementation-pi-500-r1-f09-implementation-plan.md:21)。
- 计划明确拒绝 bare CR 与 UTF-8 BOM：[`Global Constraints`](production-implementation-pi-500-r1-f09-implementation-plan.md:21)。
- 该语义与 PI-210 的 canonical 预规范化完全一致：[`MDFF_V1_COPY`](production-implementation-pi-210-normalized-evidence-model.md:363)。
- 计划把实际冻结 Markdown 的 `437 CRLF / 0 bare CR / no BOM` 作为正例，而不是拒绝对象：[`Global Constraints`](production-implementation-pi-500-r1-f09-implementation-plan.md:21)。

R1 `PI590-H-02`：**CLOSED**。

### 3.3 路径、符号、命令和占位检查

- 既有 [`run_pipeline()`](../engine/application/pipeline_runner.py:33)、[`run_pipeline_e2e()`](../engine/application/pipeline_runner.py:174)、[`PipelineAdapters`](../engine/application/ports.py:51)、[`SubmitAnalysisRequest`](../engine/application/production_service.py:41) 均存在。
- 抽查的具名 regression 节点均存在，包括 [`test_parallel_and_comparison_modules_have_no_forbidden_imports()`](../tests/application/test_staged_parallel_runner.py:156)、[`test_staged_modules_do_not_import_default_registry_pipeline_reports_or_timing()`](../tests/ziping_career/test_production_isolation.py:48)、[`test_old_and_staged_l6_can_run_side_by_side()`](../tests/decision/test_staged_arbitration.py:304)、[`test_submit_hard_fails_when_required_artifact_is_missing()`](../tests/test_production_service.py:360)、[`test_recompute_writes_rendered_report_md()`](../tests/test_recompute_report_write.py:27)、[`test_render_report_v6_generates_report_and_v5_json()`](../tests/v5/test_render_report_v6.py:56) 与 [`test_ep004_production_service_strict_render_failure_marks_job_failed()`](../tests/test_error_policy.py:297)。未运行节点。
- [`requirements-dev.txt`](../requirements-dev.txt:1) 当前存在；计划只将其列入不修改范围，不构成 false path。
- 计划明确“不指定不存在的命名 skill”：[`Global Constraints`](production-implementation-pi-500-r1-f09-implementation-plan.md:39)。
- Windows 命令未使用 `rm/cp/mv/grep/sed`。
- 仍有未解析占位与跨任务模糊指令：[`<base>`](production-implementation-pi-500-r1-f09-implementation-plan.md:829)、[`Use the related repository command already listed by Tasks 1–9`](production-implementation-pi-500-r1-f09-implementation-plan.md:662)，以及以“must use the complete PI-220 branch declarations”替代实际 branch signatures：[`Task 5`](production-implementation-pi-500-r1-f09-implementation-plan.md:359)。见 `PI590R2-M-05`。

## 4. R1 Finding Closure Matrix

| R1 finding | 复验结果 | 证据与裁决 |
|---|---|---|
| `PI590-H-01` | GOVERNANCE-CLOSED | 用户批准与 G4/G5 状态已同步；只记录，不重复技术验收。见 [`control`](production-implementation-control.md:228)。 |
| `PI590-H-02` | CLOSED | CRLF→LF、bare CR/BOM fail closed、actual CRLF positive case 均与 PI-210 一致。 |
| `PI590-H-03` | CLOSED | [`SourceLocator`](production-implementation-pi-500-r1-f09-implementation-plan.md:136) 为 canonical 六字段；[`SourceBinding`](production-implementation-pi-500-r1-f09-implementation-plan.md:112) 为三分支联合；[`FrozenDeclarationBinding`](production-implementation-pi-500-r1-f09-implementation-plan.md:152) 为五分支联合；consumer 规定 binding 只位于 locator：[`EvidenceRecord`](production-implementation-pi-500-r1-f09-implementation-plan.md:284)。 |
| `PI590-H-04` | OPEN / REGRESSED | gate/field enums 与 gate record 分账已修复，但 PI-220 的 package、declaration、participation、competition、root/timing 与 action envelope 仍被改名、删字段或扁平化；见 `PI590R2-H-01`。 |
| `PI590-H-05` | OPEN | artifact attempt ledger 已补齐，但 PI-230 refs、trace node/edge、transformation、decision trace 与 card identity 仍非 canonical；见 `PI590R2-H-02`。 |
| `PI590-H-06` | OPEN | canonical 四态、三态及七维 match 已恢复，但 submission/item 仍缺 canonical 必填字段和类型；见 `PI590R2-H-03`。 |
| `PI590-H-07` | OPEN | 104 行 Markdown 表 exactly-once 已证明；但实际可执行设计仅给出 T01 constructor，未给出 T02–T104 literal [`SCENARIOS`](production-implementation-pi-500-r1-f09-implementation-plan.md:643) 数据；见 `PI590R2-H-04`。 |
| `PI590-M-08` | CLOSED | Task 10 closed write set 仅限 [`tests/f09/`](production-implementation-pi-500-r1-f09-implementation-plan.md:607)，实现缺陷必须返回 Tasks 1–9 或新的独立有界任务：[`Task 10 boundary`](production-implementation-pi-500-r1-f09-implementation-plan.md:612)。commit/review/rollback 同样 tests-only：[`Task 10 commit`](production-implementation-pi-500-r1-f09-implementation-plan.md:663)。 |

关闭计数：技术 findings `3/7 CLOSED`（H-02、H-03、M-08）；技术 findings `4/7 OPEN`（H-04、H-05、H-06、H-07）；H-01 另记 governance-closed。

## 5. 新 Findings

### PI590R2-H-01 — High — Task 5 仍未实现 PI-220 canonical 决策对象图

**精确证据：**

1. 计划的 [`ContractVersionRef`](production-implementation-pi-500-r1-f09-implementation-plan.md:304) 使用 `contract_id/contract_version/content_digest`，但 canonical 要求 `normative_contract_path/machine_appendix_path/contract_version/content_digest`：[`ContractVersionRef`](production-implementation-pi-220-decision-interface.md:147)。
2. 计划的 [`PackageConsumptionCheck`](production-implementation-pi-500-r1-f09-implementation-plan.md:308) 被改成 `package_ref/state/checked_record_ids/issue_ids`；canonical 要求 package ID、PI-210 integrity、contract integrity、三类 reference integrity、`consumable` 与 blocking issues：[`PackageConsumptionCheck`](production-implementation-pi-220-decision-interface.md:217)。
3. 计划的 [`GateMemberDeclarationSet`](production-implementation-pi-500-r1-f09-implementation-plan.md:311) 缺 `declaration_source_id/declaration_schema_version/declaration_version`，并把成员声明值替换成局部 `member` enum；canonical 要求不可变声明来源身份和非 null `declared_member_value`：[`GateMemberDeclarationSet`](production-implementation-pi-220-decision-interface.md:254)。
4. 计划的 [`ParticipationRoleRecord`](production-implementation-pi-500-r1-f09-implementation-plan.md:329) 误用 [`FieldEvaluatorState`](production-implementation-pi-500-r1-f09-implementation-plan.md:102)，缺 canonical 独立 `ParticipationState`、frozen definition refs、missing/conflict/unknown issue 分账及 relation IDs：[`ParticipationRoleRecord`](production-implementation-pi-220-decision-interface.md:361)。
5. 计划的 [`CompetitionSet`](production-implementation-pi-500-r1-f09-implementation-plan.md:332) 省略 relation IDs、dimension records、counterevidence records 与 structural state；canonical 结构见 [`CompetitionSet`](production-implementation-pi-220-decision-interface.md:404)。
6. 计划的 root/timing ledger 采用本地 label/state/source-decision 形状：[`RootLedgerEntry`](production-implementation-pi-500-r1-f09-implementation-plan.md:333)、[`TimingLedgerEntry`](production-implementation-pi-500-r1-f09-implementation-plan.md:335)；canonical 分别要求 source-track 固定、object/rationale refs、completion mode 与 target root evidence：[`RootLedgerEntry`](production-implementation-pi-220-decision-interface.md:483)、[`TimingLedgerEntry`](production-implementation-pi-220-decision-interface.md:505)。
7. 计划的 [`DecisionActionEnvelope`](production-implementation-pi-500-r1-f09-implementation-plan.md:339) 使用五个 nullable payload 字段，且缺 subject candidate、blocking/nonblocking issues、reason codes、source decisions、两声明 binding、structural validity 和 validation errors；canonical 是一个 discriminated `payload` 并要求上述字段：[`DecisionActionEnvelope`](production-implementation-pi-220-decision-interface.md:636)。

**影响：** 零上下文实现者按 Task 5 编码会得到与已批准 PI-220 不兼容的公共对象；六成员双射、participation、competition、root/timing、五动作结构有效性及下游 PI-230 精确复制均无法按 canonical 契约验收。R1 `PI590-H-04` 未关闭。

**最小有界整改：** 仅在 Task 1/5/9 中逐字段采用 PI-220 已批准对象、enum 和 discriminated unions，并同步函数签名与 consumer；不得保留本地简化 wire shape、nullable 五 payload 或同名异义类型。

### PI590R2-H-02 — High — Task 6 仍建立非 canonical PI-230 引用图和竞争 TransformationRecord

**精确证据：**

1. 计划的 [`VersionedObjectRef`](production-implementation-pi-500-r1-f09-implementation-plan.md:305) 仅四字段；canonical 还要求 revision、contract、判别式 digest binding、locator 与 capture time：[`VersionedObjectRef`](production-implementation-pi-230-traceability-binding.md:266)。
2. 计划的 [`SnapshotRef`](production-implementation-pi-500-r1-f09-implementation-plan.md:382) 缺 source locator IDs、contract version 与 immutability，且字段名不同；canonical 见 [`SnapshotRef`](production-implementation-pi-230-traceability-binding.md:300)。
3. 计划的 [`DecisionTraceRef`](production-implementation-pi-500-r1-f09-implementation-plan.md:383) 缺 selected action、blocking/nonblocking issues、source decisions、两声明 binding 与 structural validity；canonical 见 [`DecisionTraceRef`](production-implementation-pi-230-traceability-binding.md:339)。
4. 计划的 [`TraceNode`](production-implementation-pi-500-r1-f09-implementation-plan.md:384) 和 [`TraceEdge`](production-implementation-pi-500-r1-f09-implementation-plan.md:385) 使用 node IDs/source-target node IDs/local relation type，而 canonical 使用 `object_ref + object_role + track` 及 `from_ref/to_ref + edge_type + fidelity + track_crossing`：[`TraceNode`](production-implementation-pi-230-traceability-binding.md:202)、[`TraceEdge`](production-implementation-pi-230-traceability-binding.md:211)。
5. 计划新定义局部 [`TransformationRecord`](production-implementation-pi-500-r1-f09-implementation-plan.md:386)，字段和状态均与 PI-210 唯一规范转换记录不同；PI-210 canonical 见 [`TransformationRecord`](production-implementation-pi-210-normalized-evidence-model.md:668)，PI-230 明令只复用它且不得创建竞争类型：[`转换账本`](production-implementation-pi-230-traceability-binding.md:482)。
6. 计划的 [`CardIdentityRef`](production-implementation-pi-500-r1-f09-implementation-plan.md:406) 仅五字段；canonical 还要求 identity ref ID、normative/machine refs、field path、source/evaluator states、declaration status、locators 与 issues：[`CardIdentityRef`](production-implementation-pi-230-traceability-binding.md:750)。

**影响：** trace 无法证明版本、摘要、来源、track crossing、fidelity 与声明逐值一致；局部转换类型直接违反 PI-210/230 单一转换契约。T19、T37、T44–T45、T89、T97、T99 等无法按批准架构执行。R1 `PI590-H-05` 未关闭。

**最小有界整改：** 仅将 Task 1/6/9 的所有 refs、node、edge、decision trace、card identity 改为 PI-230 canonical 字段；删除局部转换类型并逐值复用 PI-210 [`TransformationRecord`](production-implementation-pi-210-normalized-evidence-model.md:668)。

### PI590R2-H-03 — High — Task 8 的 FeedbackSubmission/FeedbackItem 仍缺 PI-230 必填绑定材料

**精确证据：**

- 计划的 [`FeedbackSubmission`](production-implementation-pi-500-r1-f09-implementation-plan.md:533) 使用 `statement_set_id`、通用 [`VersionedObjectRef`](production-implementation-pi-500-r1-f09-implementation-plan.md:305)、`items/submitted_at/digest`，但 canonical 要求 [`SnapshotRef`](production-implementation-pi-230-traceability-binding.md:300)、`parser_id`、`parser_version`、`feedback_items`、`content_digest` 与 `captured_at`：[`FeedbackSubmission`](production-implementation-pi-230-traceability-binding.md:619)。
- 计划的 [`FeedbackItem`](production-implementation-pi-500-r1-f09-implementation-plan.md:532) 缺 `feedback_id`、source span、nullable statement/revision、run/prediction targets、annotation、integrity 与 issues；canonical 见 [`FeedbackItem`](production-implementation-pi-230-traceability-binding.md:631)。
- [`FeedbackBinding`](production-implementation-pi-500-r1-f09-implementation-plan.md:535) 的四态和七维、[`LearningEligibility`](production-implementation-pi-500-r1-f09-implementation-plan.md:551) 的三态已恢复，但完整上游 submission/item 身份材料缺失，无法支撑这些 match 维度和 fail-closed 状态。

**影响：** source span、parser identity、preprod run/prediction、item integrity 和 issue provenance 无法绑定；T52 所称“complete canonical submission/items”与实际接口矛盾，T52–T58 不能按 PI-230 验收。R1 `PI590-H-06` 未关闭。

**最小有界整改：** 仅把 Task 8 的 submission/item 改为 PI-230 全字段 canonical 类型，并同步 binder、idempotency 和 trace consumers；保留已修复的四态、三态与七维 match，不引入本地状态。

### PI590R2-H-04 — High — T02–T104 没有 literal executable SCENARIOS 数据定义

**精确证据：**

- 计划展示的真实 Python constructor 只有 [`T01 = VerticalScenario(...)`](production-implementation-pi-500-r1-f09-implementation-plan.md:639)。
- 随后只声明未来模块会把表的每行“express”成 constructor：[`scenario data prose`](production-implementation-pi-500-r1-f09-implementation-plan.md:637)，再直接导入尚未定义内容的 [`SCENARIOS`](production-implementation-pi-500-r1-f09-implementation-plan.md:643)。
- [`pytest.mark.parametrize()`](production-implementation-pi-500-r1-f09-implementation-plan.md:645) 是具体 harness，但没有 T02–T104 constructor、mutator symbol 或每行字段到 constructor 的 literal data shape。
- 标记表的 104 行虽然 exactly-once 且字段齐全，但 Markdown 表行不是 Python [`VerticalScenario`](production-implementation-pi-500-r1-f09-implementation-plan.md:616) 对象，也不会被所示 import/parametrize 自动读取。
- 计划诚实声明当前不主张节点可收集：[`future collection`](production-implementation-pi-500-r1-f09-implementation-plan.md:654)；该诚实性通过，但不能替代可执行设计完整性。

**影响：** 实现者仍需自行设计 103 个 mutators、`expected_action` 的 `None`/enum 映射、issue code/path 拆分和 assertion tuple 语义；无法仅按计划机械生成 104 个 scenario-specific future nodes。R1 `PI590-H-07` 仅关闭了表计数部分，未关闭 executable design 部分。

**最小有界整改：** 仅在 Task 10 中逐项提供 T01–T104 的 literal [`VerticalScenario`](production-implementation-pi-500-r1-f09-implementation-plan.md:616) constructor（可位于明确的 scenario-data listing），每项绑定具体 mutator symbol、分离 issue code/path、typed expected action/state、basis/binding/side-effect assertions 与唯一完整 pytest node；不得创建测试文件或运行 pytest。

### PI590R2-M-05 — Medium — writing-plans 仍含不可直接执行的占位和跨任务指令

**精确证据：**

- 最终 checklist 使用未定义的 [`<base>`](production-implementation-pi-500-r1-f09-implementation-plan.md:829)，没有给出建立 base ref 的步骤或命令。
- Task 10 Step 7 使用 [`Use the related repository command already listed by Tasks 1–9`](production-implementation-pi-500-r1-f09-implementation-plan.md:662)，未指定唯一命令；Tasks 1–9 实际存在多组不同 regression commands。
- Task 5 用“must use the complete PI-220 branch declarations”代替五个 payload 的精确字段/signatures：[`Task 5 payload instruction`](production-implementation-pi-500-r1-f09-implementation-plan.md:359)。这既是接口缺失，也是不可执行的外部跳转式指令。

**影响：** 实现者和 reviewer 无法无歧义执行 diff boundary、Task 10 related regression 或五 payload contract；commit/review evidence 可能因实例选择不同而不一致。

**最小有界整改：** 仅把 `<base>` 替换为明确建立并使用 base ref 的 Windows-compatible 步骤；为 Task 10 列出确定的 regression 命令；逐字段内联或精确引用 canonical payload 定义及消费签名。不得扩大实现范围。

## 6. 十维 Fail-Closed 复验矩阵

| # | 维度 | 结果 | 裁决 |
|---:|---|---|---|
| 1 | 用户批准与范围 | PASS | H-01 governance-closed；G4/G5 当前状态清楚；F09-only、F08 identity-only、mapping/YAML 不执行边界保留。 |
| 2 | PI-210/220/230 事实源保真 | BLOCKED | PI-210 source/declaration 已修复；PI-220、PI-230 trace/ref/feedback 仍存在 canonical 字段和类型漂移。见 H-01 至 H-03。 |
| 3 | CRLF/BOM/RFC 8785 技术正确性 | PASS | CRLF→LF、bare CR/BOM fail closed、payload-only restricted JCS 与实际冻结源正例均明确。未执行实现。 |
| 4 | 决策接口完整性 | BLOCKED | [`DecisionActionEnvelope`](production-implementation-pi-500-r1-f09-implementation-plan.md:339) 及 participation/competition/root/timing 非 canonical。见 H-01。 |
| 5 | Trace/statement/artifact 完整性 | BLOCKED | StandardStatement/StatementSet 与 artifact attempts 接近 canonical，但 refs/node/edge/transformation/card identity 仍不合格。见 H-02。 |
| 6 | Feedback/eligibility 安全 | BLOCKED | canonical statuses/matches 已修复；submission/item 身份和 provenance 不完整。见 H-03。 |
| 7 | T01–T104 追溯与 executable pytest 设计 | BLOCKED | 表体 104 行 exactly-once 通过；实际 literal [`SCENARIOS`](production-implementation-pi-500-r1-f09-implementation-plan.md:643) 仅示范 T01，103 项仍缺。见 H-04。 |
| 8 | Task DAG、Task 10 ownership、commit/rollback | PASS | Task 10 tests-only 边界已关闭，production defects 返回 owning task；R0–R3、stop/rollback 与独立 review 均明确。 |
| 9 | writing-plans 质量 | BLOCKED | canonical interfaces、payload signatures、base ref 与 Task 10 regression 命令仍不足以零歧义执行。见 H-01 至 H-05。 |
| 10 | 仓库与 production-default 边界 | PASS | 改动计划限新 [`engine/f09/`](../engine/f09/) 与 [`tests/f09/`](../tests/f09/)；默认入口不接线；production-default unchanged。 |

汇总：`PASS=4`，`BLOCKED=6`。

## 7. Finding 精确计数

- High：`4`
- Medium：`1`
- Low：`0`
- Critical ambiguity：`0`（相关歧义已计入 High/Medium，不重复计数）
- Key evidence gap：`1`（T02–T104 literal executable scenario data；已计入 `PI590R2-H-04`）
- Semantic/architectural boundary violations：`3`（`PI590R2-H-01` 至 `PI590R2-H-03`，交叉分类，不另加 finding 总数）
- Relevant regression failures：`0`（按约束未运行测试；静态抽查未发现所引用既有符号/节点缺失）
- Findings 总数：`5`

## 8. 最终裁决

# BLOCKED

Fail-closed 规则要求任一 High、Medium、关键证据缺口或语义/架构边界违规均阻断。本轮存在 `4 High + 1 Medium`；因此整改后计划仍不满足独立 G5 计划验收的零阻断条件。

本裁决不否定已经机械关闭的 CRLF、PI-210 source/declaration、104 行表计数和 Task 10 tests-only 边界；但这些局部关闭不能抵消仍开放的 PI-220、PI-230、feedback 和 executable scenario design 缺陷。

固定状态声明：

- `tests executed=0`
- `implementation=false`
- `production-default unchanged`
- `YAML executed=false`
- `mapping executed=false`
- `remediation performed=false`
- `F09 only=true`
- `F08 identity-only=true`
- `PI-500=BLOCKED`
- `G4=COMPLETED`
- `G5=IN_PROGRESS`

## 9. 唯一下一动作

由独立于本复验实例的计划整改实例，仅在 [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:1) 内有界修复 `PI590R2-H-01` 至 `PI590R2-M-05`，随后提交新的分离实例 G5 计划复验；不得进入生产实现、不得创建测试、不得运行 pytest、不得执行 YAML 或 mapping。
