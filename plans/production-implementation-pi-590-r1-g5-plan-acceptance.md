# PI-590-R1 · PI-500-R1 F09 实现计划独立验收

## 1. 独立性与范围

- 验收任务：`PI-590-R1`；父任务：`PI-500 / G5`。
- 被验收对象：[`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md)。
- 本验收实例与计划编写实例分离；未采用计划自身在 [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:480) 声明的 `PASS` 作为证据。
- 本轮只做静态、只读、fail-closed 验收；未整改计划，未实现生产代码，未修改生产或测试文件，未执行声明性 YAML，未运行 pytest。
- 唯一写入为本验收记录。
- recursion：`allowed=false`，`remaining_depth=0`；未委派子任务或 reviewer。

## 2. 事实源

直接核对了以下规范与仓库事实：

1. [`README.md`](../README.md) 与 [`AGENTS.md`](../AGENTS.md)。
2. [`project-state.json`](../META/project-state.json)。
3. 总控状态 [`production-implementation-control.md`](production-implementation-control.md:69)。
4. G2 规范化证据契约 [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:262)。
5. G2 判定接口 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:90)。
6. G2 追溯绑定契约 [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:169)。
7. G3 F09 设计与 T01–T104 矩阵 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:909)。
8. G4 技术复验 [`production-implementation-pi-400-r4-g4-technical-rereview.md`](production-implementation-pi-400-r4-g4-technical-rereview.md:51)。
9. 实际冻结 JSON fixture [`production-implementation-pi-300-f09-source-snapshots-v1.json`](production-implementation-pi-300-f09-source-snapshots-v1.json)。
10. 实际冻结 Markdown 契约 [`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:265)。
11. 声明性 mapping 仅按文本读取：[`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:437)；未执行。
12. 当前测试树、引擎树、[`pyproject.toml`](../pyproject.toml:8) 及计划引用的现有测试符号。

## 3. 机械检查证据

### 3.1 路径与父目录

- 计划引用的冻结 Markdown、冻结 JSON、mapping、production entrypoint、adapter、renderer、feedback 工具及全部既有 regression test 文件均存在。
- 计划拟新增的 [`engine/f09/`](../engine/f09/) 与 [`tests/f09/`](../tests/f09/) 当前不存在，符合“实现计划尚未实施”的事实；其父目录 [`engine/`](../engine/) 与 [`tests/`](../tests/) 存在。
- 计划列为“不修改”的 [`requirements-dev.txt`](../requirements-dev.txt) 当前不存在；这不直接造成写入动作，但说明路径陈述不是完全基于当前仓库事实。

### 3.2 现有符号、签名与 pytest 节点

静态搜索确认下列现有符号存在：

- [`run_pipeline()`](../engine/application/pipeline_runner.py:33)
- [`run_pipeline_e2e()`](../engine/application/pipeline_runner.py:174)
- [`PipelineAdapters`](../engine/application/ports.py:51)
- [`SubmitAnalysisRequest`](../engine/application/production_service.py:41)

计划列出的 16 个具名既有 pytest 函数均在对应文件中存在，包括 [`test_run_pipeline_signature_and_defaults_are_unchanged()`](../tests/test_production_entrypoints_unchanged.py:35)、[`test_run_pipeline_e2e_accepts_explicit_adapters()`](../tests/test_performance_and_ports.py:92)、[`test_canonical_digest_is_order_independent()`](../tests/evaluation/test_task8_baseline.py:133)、[`test_old_and_staged_l6_can_run_side_by_side()`](../tests/decision/test_staged_arbitration.py:304) 及其余计划所列节点。未运行节点。

### 3.3 Windows 命令静态检查

- pytest 命令均以仓库根相对路径表达，未发现 `rm`、`cp`、`mv`、`grep` 或 `sed`。
- `&&` 是 Windows `cmd.exe` 可用的条件串联语法；参数化节点中的方括号在 `cmd.exe` 下不触发 shell glob。
- 计划的生成节点命令只生成字符串，不证明对应参数 case 已定义或可收集；该证据缺口见 `PI590-H-07`。

### 3.4 占位符与红旗词

对计划文本静态搜索 `TODO/TBD/FIXME/PLACEHOLDER/NotImplementedError/待定/待补/后续补/酌情/视情况/如有必要`，未发现实际未完成占位符。`PASS`、`missing`、`unknown` 等命中均处于测试预期或规范状态语境，不作为占位符计数。

### 3.5 T01–T104

- G3 事实源确有连续 104 行设计场景，从 [`T01`](production-implementation-pi-300-one-card-vertical-slice-design.md:1031) 到 [`T104`](production-implementation-pi-300-one-card-vertical-slice-design.md:1134)。
- 被验收计划只用范围行映射场景，见 [`Exact T01–T104 Mapping`](production-implementation-pi-500-r1-f09-implementation-plan.md:364)。静态抽取仅得到 46 个不同的字面 T ID；58 个 ID 没有逐项字面出现。
- 拟建的 [`test_f09_vertical_matrix.py`](../tests/f09/test_f09_vertical_matrix.py) 尚不存在，因此当前不存在 104 个可收集、可独立寻址的 executable pytest parameter nodes。
- [`nodes=[...]`](production-implementation-pi-500-r1-f09-implementation-plan.md:401) 只构造预期节点名称；它既不导入测试模块，也不执行 pytest collection，不能证明节点存在、恰一次或可运行。

### 3.6 冻结源字节与摘要

只读字节检查得到 [`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md) 含 `437` 个 CRLF、`0` 个 bare CR、无 BOM；与 G4 记录 [`437 CRLF`](production-implementation-pi-400-r4-g4-technical-rereview.md:51) 一致。G4 记录的 Markdown 规范摘要为 [`30ea0f...`](production-implementation-pi-400-r4-g4-technical-rereview.md:57)，JSON payload-only JCS 摘要为 [`67517f...`](production-implementation-pi-400-r4-g4-technical-rereview.md:94)。

## 4. 十维验收矩阵

| # | 维度 | 结果 | 证据/裁决 |
|---:|---|---|---|
| 1 | 用户批准与范围 | BLOCKED | 总控仍记录 G5/PI-500 为 BLOCKED 且等待用户批准；见 `PI590-H-01`。本轮授权只足以执行独立验收，不等同于补发实施授权。 |
| 2 | 事实源保真 | BLOCKED | PI-210/220/230 的 canonical union、字段和状态被本地简化或改名；见 `PI590-H-02`、`PI590-H-03`、`PI590-H-04`、`PI590-H-05`、`PI590-H-06`。 |
| 3 | 可执行性 | BLOCKED | 实际 frozen Markdown 会被计划要求拒绝；104 个节点也未被计划逐项定义；见 `PI590-H-02`、`PI590-H-07`。 |
| 4 | 技术正确性 | BLOCKED | 关键状态机和跨层对象不符合已批准契约；见 `PI590-H-03` 至 `PI590-H-06`。 |
| 5 | RFC 8785 正确性 | PASS | 受限域明确覆盖 fixture，拒绝数字/重复键/孤立 surrogate，自定义 UTF-16 key ordering 与 payload-only digest 路径明确；未发现独立 High/Medium 缺陷。此 PASS 不抵消其他维度阻断。 |
| 6 | T01–T104 测试追溯 | BLOCKED | 范围摘要与字符串生成器不能证明 104 个 executable cases exactly once；见 `PI590-H-07`。 |
| 7 | Task DAG | BLOCKED | Task 10 允许在 matrix 测试任务中夹带 validator correction，破坏任务边界、原子评审与清晰依赖；见 `PI590-M-08`。 |
| 8 | rollout/rollback | PASS | R0–R3、stop conditions、代码回滚与 immutable artifact supersede 边界均有明确陈述；未发现独立 High/Medium 缺陷。 |
| 9 | writing-plans 质量 | BLOCKED | canonical 接口不能由零上下文工程师按计划无歧义实现，且 T 矩阵缺逐项 executable case 定义；见 `PI590-H-03` 至 `PI590-H-07`。 |
| 10 | 仓库边界 | PASS | 拟改动限定于新 [`engine/f09/`](../engine/f09/) 与 [`tests/f09/`](../tests/f09/)，默认入口明确不改，未发现生产默认接线；当前 production-default unchanged。 |

汇总：`PASS=3`，`BLOCKED=7`。

## 5. Findings 与精确计数

### PI590-H-01 — High — G5 前置用户批准没有可核验证据

**证据：**

- 总控规定 G5 退出条件包含用户批准，且状态为 BLOCKED：[`production-implementation-control.md`](production-implementation-control.md:69)。
- PI-500 行仍为 `BLOCKED`、`未批准`：[`production-implementation-control.md`](production-implementation-control.md:92)。
- 总控明确当前 blocker 为 `AWAITING_USER_APPROVAL`，并要求“不启动 PI-500 / 不生成 G5 实现计划”：[`production-implementation-control.md`](production-implementation-control.md:230)。
- 计划自己也声明它不是实现授权：[`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:13)。

**影响：** 无法证明计划是在满足 G5 前置治理条件后形成；当前验收授权不能被扩大解释为生产实现授权。

**最小有界整改边界：** 仅由用户/治理流程提供并登记明确的 G5 计划授权状态；不得借本验收记录修改总控或推定授权。

### PI590-H-02 — High — CRLF 策略与 frozen source 及 PI-210 正面冲突

**证据：**

- 计划要求拒绝 CRLF：[`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:21)。
- 同一计划又要求实际 frozen Markdown 正向解析并得到规范摘要，同时把 CRLF 列为失败测试：[`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:166)。
- PI-210 规定预规范化把 CRLF 转 LF，只拒绝 bare CR：[`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:363)。
- G4 和本轮字节检查均确认实际文件含 437 个 CRLF：[`production-implementation-pi-400-r4-g4-technical-rereview.md`](production-implementation-pi-400-r4-g4-technical-rereview.md:51)。

**影响：** 按计划实现时，真实正例必被拒绝；Task 3 的 GREEN 条件不可同时满足，导致 source resolution、T90 及整个 vertical slice 不可执行。

**最小有界整改边界：** 仅统一计划中的行尾规范与 PI-210 已冻结的 CRLF→LF 预规范化语义，并相应界定 bare CR/BOM 负例；不得修改 frozen source 来迁就计划。

### PI590-H-03 — High — PI-210 SourceBinding 与 FrozenDeclarationBinding 被非规范扁平化

**证据：**

- 计划把 locator/binding 压成通用字段和 `source_identity` 键值 tuple，并把五个声明分支压成单一 dataclass：[`SourceLocator`](production-implementation-pi-500-r1-f09-implementation-plan.md:107)、[`SourceBinding`](production-implementation-pi-500-r1-f09-implementation-plan.md:108)、[`FrozenDeclarationBinding`](production-implementation-pi-500-r1-f09-implementation-plan.md:109)。
- PI-210 的 [`SourceLocator`](production-implementation-pi-210-normalized-evidence-model.md:263) 要求 `source_id/source_type/path/object_id/field_path/binding`，且 [`SourceBinding`](production-implementation-pi-210-normalized-evidence-model.md:275) 是分支专属必填字段的封闭判别联合。
- PI-210 明确两 frozen 分支六个非判别身份字段全部必填且互斥：[`SourceBinding` 约束](production-implementation-pi-210-normalized-evidence-model.md:318)。
- PI-210 的 [`FrozenDeclarationBinding`](production-implementation-pi-210-normalized-evidence-model.md:506) 是五个结构不同的分支；`RESOLVED` 只能带 `ref`，`UNRESOLVABLE` 必须带 `attempted_ref` 和非空 issue：[`FrozenDeclarationBinding` 约束](production-implementation-pi-210-normalized-evidence-model.md:549)。

**影响：** 本地模型允许缺失、重复、未知或分支不合法字段，无法逐字段证明 canonical identity，也不能保持五分支 fail-closed 语义；下游 PI-220/230 精确复制不可能成立。

**最小有界整改边界：** 仅把计划中的 PI-210 公共类型改为已批准 canonical 字段和封闭分支，并逐任务更新消费签名；不得发明 local synonym 或兼容扁平 wire shape。

### PI590-H-04 — High — PI-220 evaluator/gate 状态与 DecisionEvaluationResult 不符合 canonical contract

**证据：**

- 计划定义 [`EvaluatorState`](production-implementation-pi-500-r1-f09-implementation-plan.md:102) 为 `SATISFIED/UNSATISFIED/UNKNOWN/MISSING/CONFLICT`。
- PI-220 的 gate 状态是 `SATISFIED/MISSING/CONFLICT/UNKNOWN`，field evaluator 状态是 `EVALUATED/MISSING/CONFLICT/UNKNOWN/NOT_EVALUATED`：[`GateEvidenceState`](production-implementation-pi-220-decision-interface.md:97)、[`FieldEvaluatorState`](production-implementation-pi-220-decision-interface.md:113)。canonical contract 没有该位置的 `UNSATISFIED`。
- 计划的 [`GateEvaluationRecord`](production-implementation-pi-500-r1-f09-implementation-plan.md:211) 合并 supporting/counter/conflict/missing/unknown paths，并省略 canonical binding object。
- PI-220 要求这些引用分账并由 [`GateEvaluationBindingRef`](production-implementation-pi-220-decision-interface.md:269) 精确绑定。
- 计划的 [`DecisionEvaluationResult`](production-implementation-pi-500-r1-f09-implementation-plan.md:212) 省略 request/package/contract、consumption check、root-timing checks 和 produced time；canonical 顶层结构见 [`DecisionEvaluationResult`](production-implementation-pi-220-decision-interface.md:613)。

**影响：** 状态语义、record digest 输入和结果消费边界均漂移；T31–T104 的 gate/basis/permutation 检查无法证明是在执行已批准 PI-220 协议。

**最小有界整改边界：** 仅按 PI-220 canonical gate、field evaluator、record binding 和顶层 result schema 重写计划接口及消费矩阵；不得新增 `UNSATISFIED` 本地状态。

### PI590-H-05 — High — PI-230 trace/statement/artifact 公共对象缺少必需字段

**证据：**

- 计划的 [`TraceEnvelope`](production-implementation-pi-500-r1-f09-implementation-plan.md:238) 仅保留 IDs、basis、bindings、issues、digest。
- PI-230 canonical [`TraceEnvelope`](production-implementation-pi-230-traceability-binding.md:174) 还要求 schema、source snapshots、versioned refs、nodes、edges、transformations、artifacts、feedback bindings、integrity、blocking issues 和 created time。
- 计划的 [`StandardStatement`](production-implementation-pi-500-r1-f09-implementation-plan.md:239) 与 [`StatementSet`](production-implementation-pi-500-r1-f09-implementation-plan.md:240) 缺少 case/set/track/action/evidence/relation/source locator、feedback policy、issue 等必需字段；canonical 定义见 [`StatementSet`](production-implementation-pi-230-traceability-binding.md:360) 与 [`StandardStatement`](production-implementation-pi-230-traceability-binding.md:378)。
- 计划的 [`ArtifactRecord`](production-implementation-pi-500-r1-f09-implementation-plan.md:264) 用单次 attempt/error 字段替代 canonical attempts ledger，并省略 role/track/case/run/schema/issues；canonical 定义见 [`ArtifactRecord`](production-implementation-pi-230-traceability-binding.md:512)。

**影响：** action→trace→statement→artifact 的版本、摘要、来源和反馈桥无法完整闭合；T19、T34–T45、T52–T60、T82–T103 无法按 G3/PI-230 规范验收。

**最小有界整改边界：** 仅把计划的 PI-230 公共对象与 projection/lifecycle 函数改为 canonical 必填字段和引用类型，并补齐定义到消费的逐字段追溯；不得用 digest 单字段替代引用图。

### PI590-H-06 — High — FeedbackBinding 与 LearningEligibility 引入 G3 明令禁止的本地状态

**证据：**

- 计划定义 [`FeedbackBinding.status`](production-implementation-pi-500-r1-f09-implementation-plan.md:292) 为 `BOUND/INVALID/MISMATCH/UNMAPPED/MIXED_REVISION`，定义 [`LearningEligibility.status`](production-implementation-pi-500-r1-f09-implementation-plan.md:293) 为 `ELIGIBLE/INELIGIBLE/NOT_READY`。
- PI-230 canonical 状态分别为 `BOUND/UNBOUND/AMBIGUOUS/INVALID` 与 `ELIGIBLE/INELIGIBLE/HUMAN_REVIEW`：[`FeedbackBinding`](production-implementation-pi-230-traceability-binding.md:649)、[`LearningEligibility`](production-implementation-pi-230-traceability-binding.md:680)。
- G3 明确要求 mismatch/mixed revision 等落入 canonical 分支，且“不得引入本地状态”：[`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:952)。
- 计划同时把 canonical 七维 match 字段压成 `matched_dimensions`，丢失逐维 `MATCH/MISMATCH/UNKNOWN/NOT_APPLICABLE` 结构。

**影响：** T52–T58 的预期状态空间被改变，feedback/learning 消费方无法按 PI-230 处理，且 fail-closed 情况可能被错误归类。

**最小有界整改边界：** 仅恢复 PI-230 的完整字段与两组 canonical 状态，使用 issues/match 维度表达 mismatch、unmapped 和 mixed revision；不得保留本地状态兼容层。

### PI590-H-07 — High — T01–T104 未被证明为 exactly-once executable pytest cases

**证据：**

- 计划要求参数 IDs 为字面 `T01` 到 `T104`：[`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:349)。
- 实际映射仅以 25 个范围/组行概括：[`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:368)。
- 静态抽取仅得到 46 个不同字面 ID；58 个 ID 未逐项出现。
- 拟建测试文件当前不存在；而字符串生成命令仅打印预期名字：[`nodes=[...]`](production-implementation-pi-500-r1-f09-implementation-plan.md:401)。
- G3 的每个场景具有独立输入、预期和边界，从 [`T01`](production-implementation-pi-300-one-card-vertical-slice-design.md:1031) 到 [`T104`](production-implementation-pi-300-one-card-vertical-slice-design.md:1134)，不能由范围标题证明逐项实现。

**影响：** 无法证明无遗漏、无重复、节点可收集，亦无法证明每个 branch 有场景专属 invariant，而非只生成 104 个名称后共享空泛断言。

**最小有界整改边界：** 仅在计划中逐项列出 104 个 scenario 的 literal ID、G3 row、mutation、expected action/state/issues/basis/binding/side-effect assertions 和唯一 node；验收应使用静态定义/pytest collection 证据，而非名称字符串生成器。不得在本验收中创建测试。

### PI590-M-08 — Medium — Task 10 允许测试矩阵提交夹带 validator 修正

**证据：**

- Task 10 Step 4 允许“minimal validator corrections”：[`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:354)。
- 同一 Task 的 commit 只列测试文件：[`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:358)。
- rollback 才要求若夹带 validator correction 则事后拆 commit：[`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:360)。

**影响：** 生产修正可能未被 commit、review gate 和 rollback 路径准确覆盖；Task 10 可绕过前序组件任务的 RED→GREEN→独立评审边界，DAG 和变更归属不确定。

**最小有界整改边界：** 仅禁止 Task 10 修改 validator；任何实现缺口必须回到所属前序 Task 或形成独立、先 RED 后实现、单独 commit/review/rollback 的有界任务。

### Finding 计数

- High：`7`
- Medium：`1`
- Low：`0`
- Critical ambiguity：`0`（已归入上述 High/Medium，不重复计数）
- Key evidence gap：`1`（T01–T104 executable exactly-once；已计入 `PI590-H-07`）
- Semantic/architectural boundary violations：`4`（`PI590-H-03` 至 `PI590-H-06`，为交叉分类，不另加 finding 总数）
- Relevant regression evidence：`0`（未运行测试；静态接口/路径检查未发现既有节点缺失）
- Findings 总数：`8`

## 6. 最终裁决

# BLOCKED

Fail-closed 规则要求任何 High、Medium、关键证据缺口或语义/架构边界违规均阻断。本轮存在 `7 High + 1 Medium`，不满足 PASS 的零阻断条件。计划自身的 PASS 声明不改变本裁决。

- `tests executed=0`
- `implementation=false`
- `production-default unchanged`
- `YAML executed=false`
- `remediation performed=false`

## 7. 唯一下一动作

由独立于本验收实例的计划整改实例，仅在 [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md) 内有界修复 `PI590-H-01` 至 `PI590-M-08`，随后提交新的独立 G5 计划复验；不得进入生产实现。
