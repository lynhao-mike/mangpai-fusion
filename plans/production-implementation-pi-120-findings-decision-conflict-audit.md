# PI-120 · findings／decision／conflict 现状审计

> 任务编号：PI-120  
> 文档性质：G1 补证任务的静态现状审计  
> 审计日期：2026-07-19  
> 审计边界：仅记录当前仓库事实，不裁决 G1，不设计 G5，不提出生产实现方案

---

## 1. 审计目的与治理定位

本审计落实 [`production-implementation-control.md`](production-implementation-control.md:79) 中 PI-120“盘点 findings、决策状态与冲突机制”的要求，并以“可复用与缺口分账”为验收口径。它只提供 G1 架构盘点证据，不构成阶段门裁决。

治理依据如下：

1. [`production-implementation-control.md`](production-implementation-control.md:7) 是 F01–F12 生产实现设计阶段的总控状态表，但不是冻结业务语义事实源。
2. [`production-implementation-control.md`](production-implementation-control.md:65) 将 G1 标记为阻断状态；本审计无权改变该状态。
3. [`production-implementation-control.md`](production-implementation-control.md:215) 要求 G1 回答 findings、来源、置信度、冲突、五动作、竞争／仲裁及 linter 等问题。
4. [`production-implementation-g1-calibration-blocker.md`](production-implementation-g1-calibration-blocker.md:13) 记录 PI-195 裁决为 BLOCKED；该裁决不因本审计自动变化。
5. [`production-implementation-g1-calibration-blocker.md`](production-implementation-g1-calibration-blocker.md:54) 已预告 findings、冲突、并行域裁判及 run-centric 决策分布于不同轨道，本审计对该判断补充源码证据。
6. [`production-implementation-pi-110-input-pipeline-audit.md`](production-implementation-pi-110-input-pipeline-audit.md:27) 已建立 production-default、parallel/staged、v5/v6 preprod 的分账口径；本审计沿用该口径。

### 1.1 审计方法

- 静态阅读当前仓库源码、YAML 与既有治理文档。
- 追踪领域模型、生产者、消费者、持久化点与 lint 分派点。
- 对“未发现”类结论采用受限表述：只表示本次全仓 Python 静态搜索未定位到引用、加载器或调用点，不证明仓库外部不存在消费者。
- 不运行生产任务，不生成案例、报告或校准数据，不修改被禁止目录。

---

## 2. 结论摘要

### 2.1 总结论

当前仓库不存在一个横跨 production-default、parallel/staged 与 v5/v6 preprod 的统一 findings／decision／conflict 运行时协议。三个轨道各自具有可运行或可持久化的模型，但模型名称、状态值、冲突对象、仲裁结果、持久化位置和消费者均不相同。

### 2.2 关键事实

1. **production-default findings 已形成稳定主对象与落盘能力。** [`AnalysisOutput`](../engine/domain/analysis.py:182) 聚合 D1–D4、最终断语、冲突字段及可选旁路输出；[`_save_findings()`](../engine/infrastructure/findings_repository.py:11) 将 D1–D4 与完整输出写入案例 findings 目录。
2. **production-default 的结构化冲突字段存在，但 integration 当前不产生冲突记录。** [`integrate()`](../engine/application/integration.py:171) 返回 [`AnalysisOutput`](../engine/domain/analysis.py:182) 时将 conflicts 设为空列表，并注明结构化冲突由人工／报告层登记、自动语义仲裁另走独立模型，证据见 [`integration.py`](../engine/application/integration.py:333)。
3. **parallel-domain 旁路具有实际冲突扫描与裁判消费者。** [`run_parallel_domain_analysis()`](../engine/application/parallel_domain_runner.py:86) 调用 [`detect_cross_expert_conflicts()`](../engine/application/conflict_detection.py:18)、冲突 penalty、[`adjudicate_domain()`](../engine/application/adjudication.py:95) 和 consensus 构建；但其对象是 [`CrossExpertConflict`](../engine/domain/parallel.py:407)，不是 production-default 的 [`CrossSchoolConflict`](../engine/domain/analysis.py:94)。
4. **staged L6 具有另一套三段仲裁与冲突规则。** [`arbitrate_staged()`](../engine/decision/l6_staged_arbitration.py:535) 消费 [`ConflictRuleSet`](../engine/decision/l6_staged_arbitration.py:280)；[`run_parallel_with_arbitration()`](../engine/application/staged_parallel_runner.py:185) 显式加载 [`conflict-rules.yaml`](../engine/decision/conflict-rules.yaml:1)。该 runner 明确不落盘，见 [`run_parallel()`](../engine/application/staged_parallel_runner.py:124)。
5. **run-centric 决策账本位于 v5/v6 preprod 轨道。** [`DecisionRun`](../engine/decision/models.py:311) 持有 L0–L9 数据，包含 [`ArbitrationDecision`](../engine/decision/models.py:213)；[`decision_run_from_v5()`](../engine/decision/v5_adapter.py:270) 提供 v5 适配，[`render_v6_preprod_case()`](../engine/v5/preprod.py:215) 负责预生产 artifacts 持久化。
6. **output linter 是多分支消费者，而不是统一决策执行器。** [`lint()`](../tools/output_linter.py:498) 按输入类型分派；DecisionRun 由 [`_lint_decision_run()`](../tools/output_linter.py:802) 校验，production-default／parallel trace 和 v5 arbitration 走其他分支。
7. **五动作目前没有统一枚举、统一 envelope 或统一消费者。** OUTPUT、CONDITIONAL、ABSTAIN、HUMAN_REVIEW 仅存在语义近似物；本次静态审计未定位到作为决策动作的 ASK 模型、生产者和消费者。
8. **F01–F12 YAML 未发现 Python 运行时消费者。** 对完整文件名及路径的全仓 Python 静态搜索为零命中；该 YAML 当前只能确认是声明性事实源，不能据此认定其已接入运行链。

---

## 3. 轨道分账

| 轨道 | 主入口／生产者 | 主模型 | 冲突／仲裁 | 持久化 | 当前边界 |
|---|---|---|---|---|---|
| production-default | [`run_pipeline()`](../engine/application/pipeline_runner.py:33) → [`integrate()`](../engine/application/integration.py:171) | [`AnalysisOutput`](../engine/domain/analysis.py:182)、[`FinalConclusion`](../engine/domain/analysis.py:20) | [`CrossSchoolConflict`](../engine/domain/analysis.py:94) 字段存在，但 integration 返回空列表 | [`_save_findings()`](../engine/infrastructure/findings_repository.py:11) 写五类 JSON | 默认生产 findings 主链；不等于 staged 或 preprod 决策账本 |
| parallel-domain 旁路 | [`run_parallel_domain_analysis()`](../engine/application/parallel_domain_runner.py:86) | [`ExpertReading`](../engine/domain/parallel.py:163)、[`AdjudicationResult`](../engine/domain/parallel.py:343)、[`DomainAnalysis`](../engine/domain/parallel.py:509) | [`CrossExpertConflict`](../engine/domain/parallel.py:407)、penalty、少数派保留、consensus | 可作为 [`AnalysisOutput`](../engine/domain/analysis.py:182) 的附挂字段随完整输出序列化；不是独立统一决策账本 | 可运行旁路；不能冒充 production integration 的结构化冲突填充器 |
| staged L6 | [`run_parallel_with_arbitration()`](../engine/application/staged_parallel_runner.py:185) | [`StageDecision`](../engine/decision/l6_staged_arbitration.py:38)、[`StagedArbitrationResult`](../engine/decision/l6_staged_arbitration.py:114) | 三段冲突检测、规则匹配及 winner／coexist／unresolved／reject_all／conflict_resolved | runner 明确不落盘；结果模型自身支持 JSON save/load | 显式 staged 对照链，不是 production-default |
| v5/v6 preprod | [`decision_run_from_v5()`](../engine/decision/v5_adapter.py:270)、[`render_v6_preprod_case()`](../engine/v5/preprod.py:215) | [`DecisionRun`](../engine/decision/models.py:311)、[`ArbitrationDecision`](../engine/decision/models.py:213)、[`ReportViewItem`](../engine/decision/models.py:241) | v5 arbitration 适配到 run-centric L6 | 预生产报告及 v5、snapshot、DecisionRun、feedback attachment artifacts | opt-in 预生产链；不属于默认 findings repository |

### 3.1 默认链与旁路的连接边界

[`run_pipeline()`](../engine/application/pipeline_runner.py:33) 先执行 D1–D4 与 [`integrate()`](../engine/application/integration.py:171)，随后在独立异常边界内调用 dual-engine adapter，并将 theory、blind、fusion 与 parallel analysis 附挂到输出，见 [`pipeline_runner.py`](../engine/application/pipeline_runner.py:100)。适配失败会降级为空且不阻断 D1–D4，见 [`pipeline_runner.py`](../engine/application/pipeline_runner.py:113)。

因此：

- parallel analysis 可以成为完整 [`AnalysisOutput`](../engine/domain/analysis.py:182) 的附加数据；
- 附挂不代表 [`integrate()`](../engine/application/integration.py:171) 使用 parallel 冲突去填充 production-default conflicts；
- 附挂也不使 parallel-domain、staged L6 或 DecisionRun 自动成为同一协议。

---

## 4. production-default findings、integration 与持久化

### 4.1 领域对象

[`AnalysisOutput`](../engine/domain/analysis.py:182) 是 production-default 的完整分析输出，当前包含：

- D1 energy findings；
- D2 picture findings；
- D3 gate results；
- D4 support findings；
- [`FinalConclusion`](../engine/domain/analysis.py:20) 列表；
- [`CrossSchoolConflict`](../engine/domain/analysis.py:94) 列表；
- 应期、行业与财富框架等整合结果；
- retrospective、parallel analysis、theory／blind／fusion findings、prediction 等可选附挂数据。

[`FinalConclusion`](../engine/domain/analysis.py:20) 同时承载 statement、domain、layer、school、confidence、evidence、应期与 falsifiable 等字段；layer 类型定义见 [`analysis.py`](../engine/domain/analysis.py:16)。这是一套“最终断语”模型，不是五动作模型。

[`CrossSchoolConflict`](../engine/domain/analysis.py:94) 承载 conflict ID、domain、description、派别 stances、arbitration rule、winner 与 output strategy。其 output strategy 只允许“显示主胜方／并列显示／降级输出”，见 [`analysis.py`](../engine/domain/analysis.py:93)。

### 4.2 integration 行为

[`integrate()`](../engine/application/integration.py:171) 的实际职责是：

1. 验证 D1–D4 hash 链，见 [`verify_hash_chain()`](../engine/application/integration.py:16)；
2. 把 gate 及生产规则转换为 [`FinalConclusion`](../engine/domain/analysis.py:20)，见 [`_gate_to_conclusion()`](../engine/application/integration.py:133)；
3. 构建层级摘要、整体置信度、应期表及领域框架；
4. 返回 [`AnalysisOutput`](../engine/domain/analysis.py:182)。

冲突字段的当前事实是：[`integration.py`](../engine/application/integration.py:333) 直接写入空列表，并在注释中把结构化冲突登记与自动语义仲裁放到其他层／模型。因此 production-default 的冲突 schema 是“可表达”，当前 integration 是“未自动产出”。

### 4.3 findings 持久化

[`_save_findings()`](../engine/infrastructure/findings_repository.py:11) 声明将 D1–D4 与 [`AnalysisOutput`](../engine/domain/analysis.py:182) 落盘，目标目录由 [`findings_repository.py`](../engine/infrastructure/findings_repository.py:35) 确定为案例 findings 子目录，写入动作位于 [`findings_repository.py`](../engine/infrastructure/findings_repository.py:54)。文件集合为：

- energy JSON；
- picture JSON；
- gate results JSON；
- support JSON；
- analysis output JSON。

[`run_pipeline()`](../engine/application/pipeline_runner.py:33) 在 write-findings 开启时调用仓储；写入失败只产生 warning 而不阻断业务，见 [`pipeline_runner.py`](../engine/application/pipeline_runner.py:159)。因此持久化是 production-default 的可用能力，但不是业务成功的硬事务门。

---

## 5. parallel-domain 冲突与裁判链

### 5.1 统一外部 reading 协议的局部范围

[`ExpertReading`](../engine/domain/parallel.py:163) 自称“三大专家体系进入裁判模型的唯一统一外部协议”，其字段包括 domain、expert system、stance、claim、polarity、confidence、evidence、scope limit 与 falsifiable。这里的“唯一统一”范围是 parallel-domain 裁判模型的专家输入，不覆盖 production-default、staged L6 或 DecisionRun。

### 5.2 实际运行消费者

[`run_parallel_domain_analysis()`](../engine/application/parallel_domain_runner.py:86) 对每个功能域执行以下步骤：

1. 运行注册的 analyzers，并在异常／超时条件下生成 fallback abstain；fallback 入口见 [`_fallback_abstain()`](../engine/application/parallel_domain_runner.py:370)。
2. 调用 [`detect_cross_expert_conflicts()`](../engine/application/conflict_detection.py:18) 检测高置信 support／oppose 强对立。
3. 调用 [`conflict_penalties_from_conflicts()`](../engine/application/conflict_detection.py:76) 将冲突严重度转为 expert penalty。
4. 调用 [`adjudicate_domain()`](../engine/application/adjudication.py:95) 计算 support／oppose score、decision、minority views 与 arbitration reason。
5. 再次扫描裁后少数派冲突，并调用 [`build_domain_consensus()`](../engine/application/adjudication.py:163) 形成报告层结论。
6. 汇总为 [`DomainAnalysis`](../engine/domain/parallel.py:509) 与 [`ParallelAnalysisOutput`](../engine/domain/parallel.py:539)。

### 5.3 决策值与输出策略

[`AdjudicationResult`](../engine/domain/parallel.py:343) 记录 decision、judgements、support／oppose score、winning／dissenting／abstained experts、minority views 与 arbitration reason。实际裁决函数 [`_decide()`](../engine/application/adjudication.py:320) 返回 no-output、yes、no 或 mixed。

[`_build_arbitration_reason()`](../engine/application/adjudication.py:403) 对应的 output strategy 包括 downgraded、parallel、primary-only 与 primary-with-minority；[`_consensus_layer()`](../engine/application/adjudication.py:444) 再映射为“不输出”“冲突保留”、共识、独门或主专家胜出等展示层语义。

这些状态具备实际生产者和下游 consensus 消费者，但它们是 parallel-domain 的局部协议，并不等于 OUTPUT／CONDITIONAL／ASK／ABSTAIN／HUMAN_REVIEW 五动作协议。

---

## 6. staged L6 冲突与仲裁链

### 6.1 独立模型

[`StageDecision`](../engine/decision/l6_staged_arbitration.py:38) 与 [`StagedArbitrationResult`](../engine/decision/l6_staged_arbitration.py:114) 将裁决分为 structure、event、timing 三段。文件头部声明其 decision result、conflict type 与 resolution strategy 范围，见 [`l6_staged_arbitration.py`](../engine/decision/l6_staged_arbitration.py:15)。

[`detect_opposition()`](../engine/decision/l6_staged_arbitration.py:343) 识别：

- occurrence opposition；
- polarity opposition；
- magnitude opposition。

[`_decide_group()`](../engine/decision/l6_staged_arbitration.py:454) 的结果包括 reject-all、unresolved、winner 与 coexist；规则成功消解的冲突由 [`_resolved()`](../engine/decision/l6_staged_arbitration.py:394) 表达为 conflict-resolved。

### 6.2 规则消费者

[`ConflictRuleSet.from_yaml()`](../engine/decision/l6_staged_arbitration.py:294) 是 staged L6 规则加载器。[`run_parallel_with_arbitration()`](../engine/application/staged_parallel_runner.py:185) 默认加载 [`conflict-rules.yaml`](../engine/decision/conflict-rules.yaml:1)，再调用 [`arbitrate_staged()`](../engine/decision/l6_staged_arbitration.py:535)。

这证明 staged conflict YAML 存在实际运行时消费者。该证据不能外推到 F01–F12 YAML，因为两者文件、schema、加载器和调用链均不同。

### 6.3 持久化边界

[`run_parallel()`](../engine/application/staged_parallel_runner.py:124) 的文档明确说明两条路径独立异常边界且不落盘。虽然 [`StagedArbitrationResult`](../engine/decision/l6_staged_arbitration.py:114) 自身提供 JSON save/load 方法，但本次定位到的 staged runner 未将该能力接入默认持久化流程。

---

## 7. v5/v6 preprod 的 DecisionRun 与 ArbitrationDecision

### 7.1 run-centric 账本

[`DecisionRun`](../engine/decision/models.py:311) 是 schema-version 为 decision-run-v1 的 L0–L9 聚合对象，包含：

- raw payload 与 chart／context ledger；
- school applicability 与 claims；
- structural verdicts；
- event hypotheses 与 timing probabilities；
- [`ArbitrationDecision`](../engine/decision/models.py:213)；
- [`ReportViewItem`](../engine/decision/models.py:241)；
- feedback signals／attributions；
- calibration actions。

[`DecisionRun.validate_trace()`](../engine/decision/models.py:329) 验证这些层之间的引用和最小链路完整性。

[`ArbitrationDecision`](../engine/decision/models.py:213) 记录 competing event IDs、result、winner／rejected／unresolved IDs、arbitration rule、school applicability snapshot 与 reason。它与 production-default 的 [`CrossSchoolConflict`](../engine/domain/analysis.py:94)、parallel-domain 的 [`AdjudicationResult`](../engine/domain/parallel.py:343) 及 staged 的 [`StageDecision`](../engine/decision/l6_staged_arbitration.py:38) 均不是同一类型。

### 7.2 v5 适配

[`decision_run_from_v5()`](../engine/decision/v5_adapter.py:270) 将 v5 输出包装为 [`DecisionRun`](../engine/decision/models.py:311)，且函数说明明确“不改变 v5 行为”。其中 [`_decisions()`](../engine/decision/v5_adapter.py:152) 将 v5 event-realization 仲裁映射为 winner、reject-all 或 unresolved；[`_report_items()`](../engine/decision/v5_adapter.py:227) 生成报告视图项。

这是兼容适配／证明链，不是 production-default D1–D4 integration 的原生决策协议。

### 7.3 v6 preprod artifacts

[`render_v6_preprod_case()`](../engine/v5/preprod.py:215) 构造 v5 输出、run snapshot 与 DecisionRun，执行 trace validation，并持久化预生产报告、v5 JSON、run JSON、DecisionRun JSON、feedback attachment 与 manifest，关键写入流程见 [`preprod.py`](../engine/v5/preprod.py:243)。

production service 以显式布尔开关控制该渲染，字段见 [`production_service.py`](../engine/application/production_service.py:48)，调用判断见 [`production_service.py`](../engine/application/production_service.py:159)。因此 v6 preprod 是 opt-in artifact 链，不是 production-default findings 仓储的必经环节。

---

## 8. output linter 消费现状

[`lint()`](../tools/output_linter.py:498) 是多输入分派入口：

1. Markdown 输入执行报告文本、内部 ID、跨域耦合、社会时钟、关系误用、parallel-domain Markdown 与 v6 结构等检查，见 [`output_linter.py`](../tools/output_linter.py:509)。
2. schema-version 为 decision-run-v1 时调用 [`_lint_decision_run()`](../tools/output_linter.py:802) 并直接返回，见 [`output_linter.py`](../tools/output_linter.py:540)。
3. 非 v5 的结构化输出读取 final conclusions 与 gate results，并调用 production-default 全局检查及 parallel traceability 检查，见 [`output_linter.py`](../tools/output_linter.py:547)。
4. v5 arbitration 由 [`_lint_v5_arbitration_results()`](../tools/output_linter.py:875) 处理，分派点见 [`output_linter.py`](../tools/output_linter.py:564)。

[`_lint_parallel_domain_traceability()`](../tools/output_linter.py:745) 要求 parallel-domain statement 绑定 reading IDs、adjudication ID、专家、domain、consensus layer、feedback state 及 conflict explanations。

[`_lint_decision_run()`](../tools/output_linter.py:802) 要求关键 L1–L8 列表非空，并检查 L0 raw/chart hash 及 L2→L1、L3→L2、L4→L3、L5→L4、L6→L4、L7→L6/L5 的引用绑定。

结论：output linter 是结构与追踪链门禁，且确有各轨道消费者分支；当前源码未显示其执行统一五动作协议，也未显示其消费 ASK 动作。

---

## 9. 五动作运行时核查

### 9.1 总体判断

当前未发现统一的五动作枚举、统一 action envelope、统一 producer contract 或统一 consumer dispatch。以下矩阵只记录语义近似物，不把近似物认定为五动作实现。

| 目标动作 | 当前语义近似物 | 实际消费者／后续用途 | 统一协议状态 |
|---|---|---|---|
| OUTPUT | [`FinalConclusion`](../engine/domain/analysis.py:20)；parallel yes／no；winner；[`ReportViewItem`](../engine/decision/models.py:241) | production 报告／lint；parallel consensus；preprod renderer | 有输出对象和消费者，但无统一 OUTPUT action |
| CONDITIONAL | mixed、parallel、primary-with-minority、downgraded、scope limit、falsifiable、timing probability | parallel consensus／报告；各自模型序列化 | 有条件化／降级语义碎片，但无统一 CONDITIONAL action |
| ASK | 普通输入 questions、future-question、CLI question 参数 | 各自输入或预测登记用途 | 未定位到决策动作 ASK 的模型、生产者或消费者；普通 question 数据不能等同 ASK |
| ABSTAIN | [`ExpertReading`](../engine/domain/parallel.py:163) 的 abstain stance；fallback abstain；adjudication abstained experts；no-output | parallel ballot、裁判与 consensus | 有可运行局部语义，但无跨轨道统一 ABSTAIN action |
| HUMAN_REVIEW | [`FeedbackAttribution`](../engine/decision/models.py:275) 的 requires-human-review；反馈／promotion 流程中的局部 review 标记 | 对应反馈归因或治理工具 | 有局部人审标记与流程，但无统一 HUMAN_REVIEW action dispatcher |

### 9.2 OUTPUT

production-default 用 [`FinalConclusion`](../engine/domain/analysis.py:20) 表达最终断语；parallel-domain 用 yes／no、winner 与 consensus 表达可展示结论；v5/v6 preprod 用 [`ReportViewItem`](../engine/decision/models.py:241) 提供报告视图。这些对象均有实际下游，但结构和状态值不同。

### 9.3 CONDITIONAL

parallel-domain 的 mixed、parallel、primary-with-minority、downgraded 和 minority view 表达保留冲突或降级输出；各 findings／report item 又可携带应期、scope limit 或 falsifiable。当前未发现名为 CONDITIONAL 的统一动作类型，也未发现一个消费者按该动作执行统一分派。

### 9.4 ASK

本次静态搜索发现的 question／questions／future-question 主要属于：

- 输入上下文问题字段；
- 未来问题登记；
- 命令行参数或评估问题。

这些对象没有被上述 findings、parallel adjudication、staged arbitration、DecisionRun 或 output linter 作为“请求补充信息后再决策”的统一动作消费。本次审计因此只能确认：**未定位到运行时决策动作 ASK 的统一模型、生产者和实际消费者。**

### 9.5 ABSTAIN

[`_fallback_abstain()`](../engine/application/parallel_domain_runner.py:370) 会在 analyzer 异常／超时时生成 abstain reading；[`_ballot_from_stance()`](../engine/application/adjudication.py:292) 将非 support／oppose／mixed stance 映射为 abstain；[`AdjudicationResult`](../engine/domain/parallel.py:343) 保存 abstained experts；[`_decide()`](../engine/application/adjudication.py:320) 可返回 no-output。该链具备实际 producer 和 consumer，但仅属于 parallel-domain 局部协议。

### 9.6 HUMAN_REVIEW

[`FeedbackAttribution`](../engine/decision/models.py:275) 包含 requires-human-review 布尔字段；仓库反馈摄入、权重 proposal 与 staging promotion 中也存在人审状态。当前没有证据显示这些局部标记被统一为跨 findings／decision／conflict 的 HUMAN_REVIEW 动作。

---

## 10. F01–F12 YAML 消费核查

审计对象为 [`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:1)。

### 10.1 静态搜索结果

对当前仓库 Python 文件执行以下静态检索：

- 完整文件名；
- mapping 相对路径；
- F01 与 F12 标识。

结果：完整文件名与路径未命中任何 Python 引用、loader、registry 接线或调用点；F01／F12 也未形成可识别的该 YAML 运行时加载链。

### 10.2 结论边界

- 可以确认：本次仓库内 Python 静态审计未发现 F01–F12 YAML 的运行时消费者。
- 不能据此断言：仓库外部、未纳入搜索的非 Python 工具或人工流程绝对不存在消费。
- 不能把 staged L6 对 [`conflict-rules.yaml`](../engine/decision/conflict-rules.yaml:1) 的实际加载，外推为 F01–F12 YAML 已接线。
- 不能把 YAML 中声明的动作词视为已有运行时动作协议。

---

## 11. 可复用组件清单

本节“可复用”仅表示组件已有明确职责、模型或实际调用证据，不表示已决定将其用于任何后续生产设计。

| 组件 | 已确认能力 | 所属轨道 | 证据 |
|---|---|---|---|
| [`AnalysisOutput`](../engine/domain/analysis.py:182) | 聚合 D1–D4、最终断语、冲突字段与可选旁路结果 | production-default | [`analysis.py`](../engine/domain/analysis.py:181) |
| [`FinalConclusion`](../engine/domain/analysis.py:20) | 带 domain、layer、school、confidence、evidence、应期与 falsifiable 的断语 | production-default | [`analysis.py`](../engine/domain/analysis.py:19) |
| [`_save_findings()`](../engine/infrastructure/findings_repository.py:11) | 将 D1–D4 与完整输出持久化 | production-default | [`findings_repository.py`](../engine/infrastructure/findings_repository.py:11) |
| [`verify_hash_chain()`](../engine/application/integration.py:16) | 校验 D1–D4 上游 hash | production-default | [`integration.py`](../engine/application/integration.py:16) |
| [`ExpertReading`](../engine/domain/parallel.py:163) | parallel-domain 专家输入协议 | parallel-domain | [`parallel.py`](../engine/domain/parallel.py:162) |
| [`detect_cross_expert_conflicts()`](../engine/application/conflict_detection.py:18) | 同域强对立与裁后少数派冲突扫描 | parallel-domain | [`conflict_detection.py`](../engine/application/conflict_detection.py:18) |
| [`adjudicate_domain()`](../engine/application/adjudication.py:95) | 加权裁判、少数派保留及输出策略 | parallel-domain | [`adjudication.py`](../engine/application/adjudication.py:95) |
| [`ConflictRuleSet`](../engine/decision/l6_staged_arbitration.py:280) | staged 冲突 YAML 加载与规则匹配 | staged L6 | [`l6_staged_arbitration.py`](../engine/decision/l6_staged_arbitration.py:279) |
| [`arbitrate_staged()`](../engine/decision/l6_staged_arbitration.py:535) | structure／event／timing 三段仲裁 | staged L6 | [`l6_staged_arbitration.py`](../engine/decision/l6_staged_arbitration.py:535) |
| [`DecisionRun`](../engine/decision/models.py:311) | L0–L9 run-centric 账本与 trace validation | v5/v6 preprod | [`models.py`](../engine/decision/models.py:310) |
| [`decision_run_from_v5()`](../engine/decision/v5_adapter.py:270) | v5 到 DecisionRun 的兼容映射 | v5/v6 preprod | [`v5_adapter.py`](../engine/decision/v5_adapter.py:270) |
| [`lint()`](../tools/output_linter.py:498) | 按输入 schema 分派结构、追踪链与报告检查 | 多轨道门禁 | [`output_linter.py`](../tools/output_linter.py:498) |

---

## 12. 模型碎片与缺口

本节只登记现状差异，不给出修复方案。

1. **冲突对象碎片化。** production-default 使用 [`CrossSchoolConflict`](../engine/domain/analysis.py:94)，parallel-domain 使用 [`CrossExpertConflict`](../engine/domain/parallel.py:407)，staged L6 使用 [`StageDecision`](../engine/decision/l6_staged_arbitration.py:38) 内嵌冲突字段，v5/v6 使用 [`ArbitrationDecision`](../engine/decision/models.py:213) 表达竞争事件裁决。
2. **production-default 冲突生产缺口。** [`AnalysisOutput`](../engine/domain/analysis.py:182) 有 conflicts 字段，但 [`integrate()`](../engine/application/integration.py:171) 当前固定返回空列表。
3. **结果值碎片化。** production conflicts 使用中文展示策略；parallel 使用 yes／no／mixed／no-output 及多种 output strategy；staged 使用 winner／coexist／unresolved／reject-all／conflict-resolved；DecisionRun arbitration 使用另一组 result 与 ID 集合。
4. **持久化分账。** production-default 写案例 findings；staged runner 不落盘；v6 preprod 写报告旁 artifacts；三者没有共同 ledger 证据。
5. **五动作协议缺口。** 未发现统一枚举、统一 envelope、统一 producer contract 与统一 consumer dispatch。
6. **ASK 缺口最明确。** 普通 question 数据存在，但未发现其作为决策动作进入 findings、仲裁、持久化及 linter 的闭环。
7. **HUMAN_REVIEW 仅为局部标记。** requires-human-review 与各治理 review 流程存在，但没有跨轨道动作协议。
8. **linter 分支化。** output linter 能检查多种结构，却按 schema 分支执行，未体现统一 action-level 验证。
9. **F01–F12 YAML 消费缺口。** 未发现 Python runtime loader 或消费者，声明性卡片与已运行链之间没有静态接线证据。
10. **旁路附挂不等于模型统一。** parallel analysis 可附挂到 [`AnalysisOutput`](../engine/domain/analysis.py:182)，但字段共存不改变其冲突、裁判及状态协议彼此独立的事实。

---

## 13. 不可触碰边界

依据本任务授权与治理文档，本审计固定以下边界：

1. 不修改 production、mapping、engine、tools、tests、templates、META、cases、reports 下任何文件。
2. 不改变 production-default 行为，不把 parallel/staged 或 v5/v6 preprod 描述为默认生产链。
3. 不将 [`AnalysisOutput.conflicts`](../engine/domain/analysis.py:200) 的空列表解释为“无冲突”；它只表示当前 integration 未自动登记结构化冲突。
4. 不将 parallel-domain 的局部“统一外部协议”扩大解释为全系统统一协议。
5. 不将 staged L6 的 [`conflict-rules.yaml`](../engine/decision/conflict-rules.yaml:1) 消费证据迁移到 F01–F12 YAML。
6. 不将普通 questions、future-question 或命令行 question 参数解释为运行时 ASK 动作。
7. 不因已有 DecisionRun artifacts 而认定 production-default 已迁移到 L0–L9 账本。
8. 不因 output linter 能校验多个 schema 而认定它是统一决策执行器。
9. 不提出或暗含生产实现、迁移顺序、目标 schema 或 G5 方案。
10. 不裁决 G1，不改变 PI-195 的 BLOCKED 记录。

---

## 14. 精确证据索引

### 14.1 治理与任务边界

- PI-120 定义与验收口径：[`production-implementation-control.md`](production-implementation-control.md:79)
- G1 必答项：[`production-implementation-control.md`](production-implementation-control.md:215)
- G1 与下游阻断：[`production-implementation-control.md`](production-implementation-control.md:226)
- PI-195 BLOCKED：[`production-implementation-g1-calibration-blocker.md`](production-implementation-g1-calibration-blocker.md:13)
- 已知五动作与 ASK 缺口：[`production-implementation-g1-calibration-blocker.md`](production-implementation-g1-calibration-blocker.md:54)
- 轨道必须分账：[`production-implementation-g1-calibration-blocker.md`](production-implementation-g1-calibration-blocker.md:72)

### 14.2 production-default

- [`FinalConclusion`](../engine/domain/analysis.py:20)
- [`CrossSchoolConflict`](../engine/domain/analysis.py:94)
- [`AnalysisOutput`](../engine/domain/analysis.py:182)
- [`AnalysisOutput.to_dict()`](../engine/domain/analysis.py:233)
- [`integrate()`](../engine/application/integration.py:171)
- production conflicts 空列表：[`integration.py`](../engine/application/integration.py:333)
- dual-engine／parallel 附挂：[`pipeline_runner.py`](../engine/application/pipeline_runner.py:100)
- findings 保存调用与非阻断失败：[`pipeline_runner.py`](../engine/application/pipeline_runner.py:159)
- findings 仓储：[`_save_findings()`](../engine/infrastructure/findings_repository.py:11)
- findings 目录：[`findings_repository.py`](../engine/infrastructure/findings_repository.py:35)
- 五类文件写入：[`findings_repository.py`](../engine/infrastructure/findings_repository.py:54)

### 14.3 parallel-domain

- [`ExpertReading`](../engine/domain/parallel.py:163)
- [`AdjudicationResult`](../engine/domain/parallel.py:343)
- [`CrossExpertConflict`](../engine/domain/parallel.py:407)
- [`DomainConsensus`](../engine/domain/parallel.py:446)
- [`DomainAnalysis`](../engine/domain/parallel.py:509)
- [`ParallelAnalysisOutput`](../engine/domain/parallel.py:539)
- canonical runner：[`run_parallel_domain_analysis()`](../engine/application/parallel_domain_runner.py:86)
- fallback abstain：[`_fallback_abstain()`](../engine/application/parallel_domain_runner.py:370)
- 冲突扫描：[`detect_cross_expert_conflicts()`](../engine/application/conflict_detection.py:18)
- conflict penalty：[`conflict_penalties_from_conflicts()`](../engine/application/conflict_detection.py:76)
- 裁判入口：[`adjudicate_domain()`](../engine/application/adjudication.py:95)
- ballot 映射：[`_ballot_from_stance()`](../engine/application/adjudication.py:292)
- decision 计算：[`_decide()`](../engine/application/adjudication.py:320)
- output strategy：[`_build_arbitration_reason()`](../engine/application/adjudication.py:403)
- consensus layer：[`_consensus_layer()`](../engine/application/adjudication.py:444)

### 14.4 staged L6

- [`StageDecision`](../engine/decision/l6_staged_arbitration.py:38)
- [`StagedArbitrationResult`](../engine/decision/l6_staged_arbitration.py:114)
- [`ConflictRule`](../engine/decision/l6_staged_arbitration.py:232)
- [`ConflictRuleSet.from_yaml()`](../engine/decision/l6_staged_arbitration.py:294)
- [`detect_opposition()`](../engine/decision/l6_staged_arbitration.py:343)
- [`_decide_group()`](../engine/decision/l6_staged_arbitration.py:454)
- [`arbitrate_staged()`](../engine/decision/l6_staged_arbitration.py:535)
- staged runner 不落盘：[`run_parallel()`](../engine/application/staged_parallel_runner.py:124)
- 规则加载与仲裁调用：[`run_parallel_with_arbitration()`](../engine/application/staged_parallel_runner.py:185)
- staged 冲突规则：[`conflict-rules.yaml`](../engine/decision/conflict-rules.yaml:1)

### 14.5 v5/v6 preprod 与 linter

- [`ArbitrationDecision`](../engine/decision/models.py:213)
- [`ReportViewItem`](../engine/decision/models.py:241)
- [`FeedbackAttribution`](../engine/decision/models.py:275)
- [`DecisionRun`](../engine/decision/models.py:311)
- [`DecisionRun.validate_trace()`](../engine/decision/models.py:329)
- v5 decisions 映射：[`_decisions()`](../engine/decision/v5_adapter.py:152)
- v5 report items：[`_report_items()`](../engine/decision/v5_adapter.py:227)
- v5 → DecisionRun：[`decision_run_from_v5()`](../engine/decision/v5_adapter.py:270)
- v6 preprod 渲染：[`render_v6_preprod_case()`](../engine/v5/preprod.py:215)
- v6 preprod artifacts：[`preprod.py`](../engine/v5/preprod.py:243)
- preprod opt-in 字段：[`production_service.py`](../engine/application/production_service.py:48)
- preprod 条件调用：[`production_service.py`](../engine/application/production_service.py:159)
- linter 主入口：[`lint()`](../tools/output_linter.py:498)
- DecisionRun 分派：[`output_linter.py`](../tools/output_linter.py:540)
- parallel traceability：[`_lint_parallel_domain_traceability()`](../tools/output_linter.py:745)
- DecisionRun lint：[`_lint_decision_run()`](../tools/output_linter.py:802)
- v5 arbitration lint：[`_lint_v5_arbitration_results()`](../tools/output_linter.py:875)

---

## 15. 自检记录

| 自检项 | 结果 |
|---|---|
| 是否明确区分 production-default、parallel/staged、v5/v6 preprod | 通过 |
| 是否追踪 findings 领域模型、integration 与持久化 | 通过 |
| 是否追踪冲突模型、scanner 与裁判消费者 | 通过 |
| 是否追踪 DecisionRun、ArbitrationDecision 与 preprod artifacts | 通过 |
| 是否追踪 output linter 的 schema 分派与检查范围 | 通过 |
| 是否逐项核查 OUTPUT／CONDITIONAL／ASK／ABSTAIN／HUMAN_REVIEW | 通过 |
| 是否将普通 question 与运行时 ASK 分开 | 通过 |
| 是否核查 F01–F12 YAML runtime consumer | 通过；静态搜索未发现 Python 消费者 |
| 是否列出可复用组件、模型碎片／缺口、不可触碰边界 | 通过 |
| 是否给出源码路径与精确行号 | 通过 |
| 是否提出或暗含生产实现 | 未提出 |
| 是否裁决 G1 或设计 G5 | 否 |
| 是否修改禁止目录 | 否；本任务仅创建本审计文件 |

---

## 16. 审计结语

PI-120 的静态证据表明，当前仓库已经分别具备 production-default findings 聚合与持久化、parallel-domain 冲突扫描和裁判、staged L6 规则仲裁、v5/v6 preprod DecisionRun 账本，以及多 schema output lint 能力；但这些能力仍属于不同运行轨道和模型体系。production-default 的结构化 conflicts 当前为空，五动作尚无统一运行时协议，ASK 未定位到决策动作消费者，F01–F12 YAML 未发现 Python 运行时消费链。

本结论仅完成 PI-120 现状补证，不改变任何阶段门状态或生产行为。