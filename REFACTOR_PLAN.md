# mangpai-fusion v1.3.1 渐进式重构实施方案

> 状态：Phase 1、Phase 2、Phase 3 的架构边界均为 `Completed & Signed-off by Human Adjudicator`；该签字不代表算法行为正确，也不授权生产切换。
> 生产门禁：`production_switch_permitted=false`。Compatibility D1/D2 与 V5 算法内核缺陷留待专项迭代，不阻碍 Phase 1–3 结构边界验收。
> 前置评审：[`ARCH_REVIEW_REPORT.md`](ARCH_REVIEW_REPORT.md)。
> 范围边界：Phase 1–3 验收的是架构/数据隔离边界；不据此宣称命理算法正确或生产就绪。

## 1. 实施目标与非目标

### 目标

1. 在不改变命理判断规则、规则权重、路由决策或生产输出语义的前提下，逐步清晰化兼容生产入口、应用服务、v5/DecisionRun 与持久化产物之间的边界。
2. 以现有契约测试和运行制品为基线，给兼容线建立可重复的行为保护，再逐步提高新 run 的身份、快照、断语、反馈和 artifact 引用完整度。
3. 让兼容生产线与 v5 目标线在切换获批前可并行、可区分、可审计；生产切换必须经过独立证据门禁和人工批准。
4. 盲测轮次、封存、核验、预测、反馈和规则审核保持各自数据边界；统计信号不得自动修改生产规则、权重或路由。

### 非目标

- 不删除旧模块、历史案例、报告或运行产物；不批量改写历史档案。
- 不改变业务规则、命理解释、置信度口径、默认权重、runner 注册、路由、报告章节/内容语义或 pipeline 顺序。
- 不把架构重构当作扩充理论规则、调参或引入新仲裁算法的授权。
- 不以 v5 对象存在、单个样本跑通或测试通过推定生产就绪。
- 不扩展到未获确认的盲测生产入口、统计阈值或流派权重策略。

## 2. 当前事实与实施前置

- 生产服务执行路径通过 `run_pipeline_e2e(..., error_policy="strict")` 进入兼容 pipeline；`_run_existing_job()` 中 strict 异常使 job 进入 failed 状态（[`engine/application/production_service.py`](engine/application/production_service.py:141)）。`run_pipeline` 与 `run_pipeline_e2e` 在 Phase 4 独立生产门禁批准前保持唯一默认生产入口。
- `ProductionAnalysisService` 对外请求/响应字段、公开方法、job 状态机和 strict 错误策略在 Phase 1 不变。仅允许在行为测试保护下整理私有的 cache key、artifact 收集、summary 组装职责；不新增无消费者接口或 DI 容器（[`engine/application/production_service.py`](engine/application/production_service.py:237)、[`engine/application/production_service.py`](engine/application/production_service.py:334)、[`engine/application/production_service.py`](engine/application/production_service.py:393)）。
- 兼容 `run_pipeline()` 有签名/默认值保护，runner registry、默认权重及生产规则文件也有哈希/摘要保护（[`tests/test_production_entrypoints_unchanged.py`](tests/test_production_entrypoints_unchanged.py:17)、[`tests/test_production_entrypoints_unchanged.py`](tests/test_production_entrypoints_unchanged.py:35)、[`tests/test_production_entrypoints_unchanged.py`](tests/test_production_entrypoints_unchanged.py:39)、[`tests/test_production_entrypoints_unchanged.py`](tests/test_production_entrypoints_unchanged.py:50)）。strict/tolerant 失败策略及 V5 adapter 有独立测试。
- Wave 1 `engine/governance/` 由 Wave 2 application shadow 调用，后接显式 evaluation blind adapter；静态隔离测试保护 forbidden imports、legacy consumers、Snapshot 写入、YAML 污染与系统时间边界。V5 当前没有被证明是 shadow 的调用方或生产替代线；源码文本搜索无命中不等于动态闭包证明（详见 [`ARCH_REVIEW_REPORT.md`](ARCH_REVIEW_REPORT.md:58)）。
- 盲测与规则治理服从双核盲测契约及 Statement Record 契约：先封存后核验，历史记录只读，个案反馈不得自动修改通用规则；未解释的双运行线差异由人工裁决并阻塞推进（[`engine/contracts/22-dual-core-blind-validation-v1.md`](engine/contracts/22-dual-core-blind-validation-v1.md:36)、[`META/statement-record-contract-v1.md`](META/statement-record-contract-v1.md:13)）。
- 案例 artifact 容量治理另立项目；本计划不实施拆分、压缩、去重、删除或回填。
- 本轮门禁结果：保护测试 45 passed/1 deprecation warning；治理、application isolation、shadow adapter 定向测试 339 passed；tool registry markdown/check 与 rule status markdown/check 均成功。样本哈希核验：RF000149 摘要 mismatch（阻塞，待人工裁决）；RF000417 摘要一致；授权 META P-GO v004 的 canonical artifact、bundle files 与 parent chain 核验一致。详见 [`ARCH_REVIEW_REPORT.md`](ARCH_REVIEW_REPORT.md:24)。这些是当前工作树的 Phase 0 实测，不替代 Phase 1 开始前重跑。
- Graft 未返回可用代码图；跨目录改动前仍须在批准范围内检查精确调用方与影响面，不得声称已完成全依赖闭包。

## 3. 建议架构与边界

```text
API / CLI / internal entrypoints
    ↓
Application use case
  request validation · mode/policy · job lifecycle
    ├── Compatibility executor adapter → existing D1–D4 pipeline (production default)
    └── V5/Decision executor adapter → approved preproduction/run-centric path
    ↓
Run identity + immutable snapshot + decision trace
    ↓
Artifact manifest + StatementRecord + feedback attachment
    ├── renderer → user-facing report
    └── governance workflow → sealed validation / human review queue
```

约束：

- 先确认现有真实调用方和契约，再抽象接口；没有第二个真实实现需要解耦时不新建通用工厂或空端口。
- 兼容执行器在独立切换批准前保持默认；`engine/pipeline.py` 的兼容导出不能未经调用方核验移除。
- 一次运行的快照、报告投影、学习断语记录和反馈引用是相关但不同的模型。`statement_index` 不得被假定为学习链唯一事实源；反馈应以稳定 `statement_id` 连接记录与 rule metadata（[`META/statement-record-contract-v1.md`](META/statement-record-contract-v1.md:13)、[`META/statement-record-contract-v1.md`](META/statement-record-contract-v1.md:179)）。
- 历史记录按只读兼容 lane 保留；新增更正记录而不是覆盖原始封存内容（[`DESIGN_HANDOFF.md`](DESIGN_HANDOFF.md:12)）。
- “盲测”“普通咨询”“核验/复核”“未来预测”是需要隔离的数据访问/生命周期模式，不允许事后改标；具体入口接口与存储模型须由业务负责人确认。

## 4. Phase 0–4 实施顺序与文件范围

### Phase 0：建立行为与数据基线（本轮已执行并完成文档范围复核；不改生产行为）

**本轮实测范围与结果**

- 生产保护：`pytest tests/test_production_entrypoints_unchanged.py tests/test_error_policy.py tests/test_decision_v5_adapter.py -q` → 45 passed，1 deprecation warning。
- 治理/隔离：`pytest tests/governance tests/application/test_governance_shadow_runner.py tests/application/test_governance_fact_builder.py tests/application/test_governance_claim_adapters.py tests/application/test_application_import_isolation.py tests/evaluation/test_governance_shadow_adapter.py -q` → 339 passed。
- 工具状态：按 `tools/README.md` 执行 tool registry 与 rule status 的 markdown 和 `--check` 命令；两项 check 均通过。动态计数保持扫描输出，不作为静态设计事实。
- 授权样本仅包括 RF000149、RF000417 与 `META/prospective-go/single-cases/P-GO-2026-001-*`。RF000149 sidecar hash mismatch 未解决；RF000417 原始 hash 与 feedback 前后记录相符；P-GO v004 canonical artifact/bundle/parent hashes 相符。未访问 `cases/P-GO-2026-001-*` 内容，未扫描 `cases/` 全树。
- 一次目录模式清单命令超出范围列出了 `cases/P-GO-2026-001-*` 下一个文件名/大小元数据；未读文件内容，之后未再访问。此偏差已记录，不作为样本证据。
- 本轮只更新本计划与架构评审报告；业务代码、配置、测试、样本、规则及既有 artifact 均未修改。

**退出状态**

基线门禁已实测，RF000149 hash mismatch 作为独立阻塞事项保留。Phase 0 是历史基线阶段；Phase 1–3 架构边界现已由 Human Adjudicator 签字验收。任何新的代码行为变更仍须单独授权并按实际改动重跑关联门禁。

### Phase 1：应用用例与兼容执行器边界（架构边界：Completed & Signed-off by Human Adjudicator）

**实施前具体范围（不得超出）**

1. `engine/application/production_service.py`：在 `ProductionAnalysisService` 私有职责内审视 `compute_cache_key()`（当前约第 237 行）、`_collect_artifacts()` / `_append_artifact_if_exists()`（约第 334–391 行）及 `_build_summary()`（约第 393–410 行）。仅当测试确认可独立且存在实质耦合痛点时，才将这些私有实现拆成最小纯函数/私有协作单元；不改变公开签名、请求/响应字段、job 状态转换、cache 命中语义、artifact 顺序或 strict 异常传播。
2. `engine/application/pipeline_runner.py`：本阶段仅保留 `run_pipeline()`（33–172）与 `run_pipeline_e2e()`（174–291）为兼容默认入口并核验调用关系；除非经单独批准且测试先行，不搬迁/重写 pipeline orchestration。
3. `engine/pipeline.py`：继续保留历史兼容导出；本阶段不删除、不改路由。
4. 测试前置：至少先跑并保持通过 `tests/test_production_entrypoints_unchanged.py`、`tests/test_error_policy.py`、相关 `tests/application/` production service/job/cache/artifact 测试；本轮保护基线还包括 `tests/test_decision_v5_adapter.py`。Phase 1 开始时重新盘点测试名并重跑，不把 Phase 0 结果当永久证明。

**不做**

- 不移动领域计算，不改变 D1–D4 步骤顺序，不重写 engine 算法。
- 不合并 strict/tolerant，不吞掉生产异常，不改变附加链错误隔离策略。
- 不为了“分层完整”引入尚无消费者的 interface/DI 容器。

**验收门**

`run_pipeline` 签名和默认值、默认 registry/权重与规则基线不变；strict/tolerant 行为测试、service/job 生命周期测试和完整关联测试通过；差异限于结构且经人工 review。

### Phase 2：新 run 记录和 artifact 关系标准化（架构边界：Completed & Signed-off by Human Adjudicator）

**本阶段已实施范围与验证**

- `snapshot.run_id` 已作为 V5 preprod canonical run ID，贯通 DecisionRun adapter、manifest 绑定与 feedback attachment；相关身份一致性/拒绝不匹配测试覆盖。
- StatementRecord v1 保持旧 schema；独立 v2 builder 以显式学习身份逐规则拆分，缺失结构化身份失败关闭，不从断语或缺失字段推断。
- 新增 `engine/evaluation/dual_core_blind.py`：按双核盲测契约校验多轮记录、核验记录、事项/方向白名单及完整轮次网格；复用 prospective artifact 的 canonical hash、父引用校验和 create-only 发布。独立命中/未命中只作为统计 API 的显式输入，不写入封存记录。
- 封存路径按 case ID SHA-256 确定为 `admitted_root/.dual-core-blind-seals/<digest>.json`；拒绝传入其他路径，避免通过改路径为同一 case 重复封存。测试仅使用合成数据与 `tmp_path`。
- 定向验证：`python -m pytest tests/evaluation/test_dual_core_blind.py tests/test_statement_runtime.py -q` → 14 passed。生产/治理隔离门禁 → 35 passed、1 deprecation warning；`python -m tools.rule_status_scan --check` 与 `python -m tools.tool_registry --check` 均通过。路径限定 `git diff --check` 通过。
- 验收边界：未运行可能读取真实 `cases/` 的整库或整文件测试；意外修改的真实案例 manifest 保持未触碰，未 stage/commit。sealed artifact 由 API 固定路径并对该路径 create-only；此测试证明 API 写入语义，不等于多进程并发/抗恶意文件系统竞态证明。

**本阶段范围落实与兼容约束**

- `engine/v5/domain.py`、`engine/decision/v5_adapter.py` 与相关预生产/反馈适配路径仅调整 canonical run identity 所需边界；没有把 v5 改为默认生产入口。
- StatementRecord v1 旧结构保持兼容；v2 使用独立 builder 和显式结构化身份，不回填历史记录、不推断缺失 rule metadata。
- 新增双核 seal 作为独立评估 artifact；不写历史案例、不接入生产规则/权重/路由，也不扩展成 CLI 或生产盲测入口。
- 历史案例仍按只读 Legacy Lane 处理；artifact 拆分/压缩/去重、删除与历史回填不在本阶段范围内。

**验收门**

Phase 2 验收记录：新 run 的 manifest/DecisionRun/feedback 身份有定向测试保护；StatementRecord v1/v2 边界有定向测试；双核 seal 使用固定 canonical 路径、父链/hash 与 create-only 有合成测试保护。定向与保护测试、状态扫描及 tool registry 检查均通过。该阶段不涉及真实样本读写或历史回填。上述有限验证不构成多进程并发或生产接入证明；生产接入仍须后续单独批准。

### Phase 3：兼容线与 V5 受控互操作（架构边界：Completed & Signed-off by Human Adjudicator）

**互操作边界与运行记录**

- evaluation-only runner 位于 [`engine/evaluation/dual_line_interop.py`](engine/evaluation/dual_line_interop.py:264)，隔离兼容输入并调用 `run_pipeline(..., write_findings=False)`，再绑定 V5 snapshot 与 DecisionRun trace。DecisionRun 身份不匹配时失败关闭；该路径不是生产切换。
- 差异仅按双方共享且唯一的 rule identity 配对；未匹配或身份歧义不作相似度合并。兼容聚合 ID（如 `CC-D1-001`）与 V5 规则级 claim ID 属于不同命名空间及输出粒度，因此本次 0 项配对不等于 338 项逐条应合并，也不据此判定算法一致或不一致。
- 合成验证记录：`tests/evaluation/test_dual_line_interop.py` 为 18 passed；Phase 1/2 相关保护与互操作集为 111 passed、1 条既有弃用警告。此为合成对象与临时目录验证，不替代算法正确性或生产准入证据。
- **本次 RF000417 运行**：run ID `run-f9c7648ad11f`，差异 338 项：Compatibility-only 7、V5-only 331、双方非空配对 0。V5 共 331 claims；本次捕获中 polarity 全为 neutral，stance 为 support 330、abstain 1。`trace_issues: []` 只表示 DecisionRun validator 检查范围内未发现 trace 断点，不表示不存在下述旁路异常。
- **旧 RF000417 运行（单独保留，不与本次合并统计）**：run ID `run-87d73e02a9c7`，旧记录差异数为 1,794，曾标注为 `human_adjudication_blocker`；旧运行未可靠核实 Compatibility-only / V5-only / 配对的拆分数量。其输入摘要及运行身份属于旧次运行，不应用来替代本次 run 的统计。

**Human Adjudicator 正式裁决**

- 用户作为本项目唯一业务裁决人，正式签署 Phase 1、Phase 2、Phase 3 的**架构边界验收**。签字范围是结构、身份绑定、盲态隔离及互操作治理边界；不代表对当前命理算法输出背书。
- 对本次 338 项差异的裁决：Compatibility 聚合 ID（例如 `CC-D1-001`）与 V5 规则级 claim ID 命名空间和粒度不同；因此 0 项可配对不构成逐条合并指令。保持 identity-only 匹配，不做相似度合并。
- Compatibility 算法缺陷靶点进入专项迭代：D1 做功方向与反局误判、贼神/捕神逻辑错误；D2 化官生印判定失实。
- V5 算法缺陷靶点进入专项迭代：盲派 Top-15 机械截断、子平输出噪音、polarity 全 neutral / stance 几乎全 support、事业 event arbitration 的 opposition score 与 claim stance 不自洽。
- 上述命理/算法内核问题不阻碍 Phase 1–3 的结构边界签字，但必须在专项迭代中处理；本计划不据此修改业务算法、规则、权重或生产路由。

**三项旁路异常（只读诊断；原始 traceback 未随运行制品留存）**

现存 RF000417 capture 不含 theory、prediction、retrospective 对象，也未保存 traceback。因此下列是依异常原始消息与源码访问链定位的候选抛错点，不应表述为已由 traceback 核实的栈帧；精确最初调用方和输入对象来源尚不能从该运行制品确认。三项均为 Python `AttributeError`：

1. Error Message：`'dict' object has no attribute 'all_zhis'`。源码候选：[`engine/predicates/strength.py`](engine/predicates/strength.py:78) 的 `is_dishi()` 在第 83 行访问 `bazi.all_zhis()`；同类访问也存在于 [`engine/application/production_rule_triggers.py`](engine/application/production_rule_triggers.py:165) 的 `_is_wuxing_imbalanced()`（第 173 行）与 `_has_zhi_chong()`（第 184 行）。触发条件是这些逻辑收到普通 `dict`，但按 `Bazi` 对象调用其方法；本次原始 traceback 缺失，无法唯一确认是哪一个候选函数实际抛出，亦未确认 dict 的构造来源。
2. Error Message：`'NoneType' object has no attribute 'day_master_strength'`。源码候选：[`engine/application/prediction_signals.py`](engine/application/prediction_signals.py:22) 的 `extract_ziping_signal()` 第 27 行读取 `theory.day_master_strength`；调用位于 [`engine/application/pipeline_runner.py`](engine/application/pipeline_runner.py:120) 第 122 行。直接触发条件是 `theory` 为 `None`。pipeline 的 theory adapter 异常分支会令 `theory_findings=None`，而 prediction 分支仍尝试提取信号；这解释了可见代码中的旁路链，但缺少 traceback，无法证明该 RF000417 异常确由第 1 项先行异常造成。
3. Error Message：`'DayunStep' object has no attribute '起岁'`。源码候选：[`engine/yingqi/retrospective.py`](engine/yingqi/retrospective.py:282) 的 `scan_retrospective()` 第 337 行读取 `step.起岁`（并随后读取 `step.止岁`）；调用位于 [`engine/application/pipeline_runner.py`](engine/application/pipeline_runner.py:140) 第 143 行。触发条件是运行时传入的 `DayunStep` 实例没有回溯扫描所需的 `起岁` 属性，属于对象字段契约不匹配。当前证据不能确认该对象具体由哪条适配路径构造；已存在的 `adapt_dayun()` 会尝试适配完整区间端点，但不得据此反推此异常的真实对象来源。

**P-GO 契约边界**

- P-GO-2026-001 v004 状态仍为 `INCOMPLETE_DAYUN_CONTRACT`。仅按授权检查 bundle 指定材料；本任务未运行 P-GO、未推算或补造缺失的大运区间字段。该状态不因 Phase 1–3 架构签字而改变。

**验收与未决事项边界**

- Phase 1–3 架构边界现已由唯一 Human Adjudicator 签字验收；已记录的旁路异常和命理算法内核缺陷转入专项迭代，不倒推为结构边界未验收。
- `production_switch_permitted=false`；兼容线仍是默认生产入口。Phase 4 生产切换评估需另有真实 cohort、正式门禁证据与独立人工批准。
- 本任务没有重跑 RF 双线、没有运行 P-GO，也没有修改业务代码或规则。

### Phase 4：生产切换评估（本阶段不自动执行切换）

**前置**

- 项目真实 cohort 已按正式流程准备完成，并通过运行时状态扫描；当前状态不满足生产切换许可。
- 预先由业务负责人确定样本准入、统计分母、成功/失败阈值、风险界限、兼容报告要求与回滚条件。
- 流程审计证明无盲态泄露、封存被覆盖、规则自动写回或 artifact 丢失；生产报告与反馈链路通过端到端验收。

**实施形式**

Phase 4 仅产出独立 go/no-go 决议。若 GO，另开变更任务实现逐步灰度/回滚；本计划不预先把切换代码混入前序结构重构。

## 5. 验证策略与门禁

### 每个阶段的最低验证

1. 先盘点实际测试名，运行阶段相关窄范围 pytest；扩大到 `pytest tests/` 前确认耗时与当前环境。每阶段均在目标工作树重跑，不复用历史通过结果。
2. Phase 1 生产保护至少验证 `tests/test_production_entrypoints_unchanged.py`、`tests/test_error_policy.py` 与相关 application service/job/cache/artifact tests；Phase 2 adapter/snapshot 改动验证 `tests/test_decision_v5_adapter.py`、相关 `tests/v5/` 和所触及的 serialization/contract tests。
3. 历史记录中的治理隔离集与 adapter 集为 339 passed；任何后续代码行为变更均须按其实际改动面重跑相关测试，不能将历史通过结果当作新变更的验证。执行工具 registry、rule status 等仓库门禁时以 `tools/README.md` 当前有效入口为准；本轮两套 markdown/check 命令均通过。
4. 对有产物变化的阶段，比较输入、manifest、report、snapshot、feedback attachment 与 statement records 的路径/ID/版本/哈希；冻结文件和历史快照必须不变。
5. 记录失败测试；不得为了通过门禁删除旧断言、放宽 strict 行为、更新规则哈希基线或修改权重基准，除非业务所有者批准了独立的行为变更任务。

### 阻断条件

- 生产入口签名或输出语义非计划内变化。
- 任一规则/权重/路由/runner registry 在结构重构中变化。
- strict 生产错误被降级吞掉，或 tolerant 行为意外变成 strict。
- run/statement/artifact 追踪断裂、封存产物被覆盖、反馈无法稳定回链。
- 盲态样本读取边界无法证明，或 RF 冻结样本不符合要求仍试图继续对照。
- 真实 cohort/生产切换未获授权却切换默认入口。

## 6. 总体验收标准

只有同时满足以下要求，才可将这轮重构标记完成：

- 兼容入口和已保护的生产默认行为保持；任何刻意变化均有独立批准、迁移说明及回滚策略。
- 新增结构只解决已证实的边界问题，不留无消费者抽象；v5/DecisionRun 与 manifest/statement/feedback 关系可通过测试验证。
- 旧案例和报告可继续读取，历史/封存内容未被覆盖或删除。
- 数据治理符合双核盲测契约，规则修改只进入人工待审，不直接自动生效。
- 所有适用测试与扫描门禁在实施工作树实际通过，证据保留；不得引用本评审未执行的验证。
- 生产切换决议另行审批；在正式许可前，兼容线继续作为默认生产入口。

## 7. 禁止事项

- 禁止在本轮评审或未批准阶段修改任何现有业务代码、规则、配置、测试与案例数据；已批准阶段仅可改动其明示文件范围。
- 禁止把功能架构评审扩大为规则改写、置信度调参、学校权重、路由 promotion 或新裁决算法设计。
- 禁止以名称猜测能力、以设计文档代替实现证据、以历史状态数字代替运行时扫描。
- 禁止全量扫描/导出 `cases/` 来填补当前抽样证据；遵守案件范围与盲态数据边界。
- 禁止删除或覆盖旧模块、兼容入口、报告、run snapshot、freeze、feedback 或统计快照；任何清理/迁移须另立有恢复证明的批准方案。
- 禁止重置或篡改哈希/签名/权重门禁来适配重构结果。
- 禁止未获生产切换许可就让 v5/新执行器取代兼容生产默认入口。

## 8. 执行前需批准

开始任何代码实施前，请确认：

1. Phase 1–3 架构边界已获 Human Adjudicator 正式签字；签字不改变命理判断算法，也不构成生产切换许可。
2. `ProductionAnalysisService` 的内部职责整理仅允许在 Phase 0 找到明确耦合痛点且测试边界可保护后进行。
3. 新运行数据契约与旧历史数据共存；不做自动历史回填或推断。
4. 盲测流程继续遵守先封存后核验及样本访问边界；后续样本运行依其各自授权执行。
5. Phase 4 必须独立评估和批准；当前 `production_switch_permitted=false`。
