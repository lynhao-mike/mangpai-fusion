# mangpai-fusion v1.3.1 系统架构评审报告

> 评审类型：只读架构评审与渐进式重构设计  
> 基线版本：`1.3.1`（事实源：[`VERSION`](VERSION:1)；Python 包版本见 [`engine/__init__.py`](engine/__init__.py:1)）  
> 状态：评审稿，等待人工确认；本报告不代表重构已获批准或已实施。  
> 证据口径：下列“现状事实”来自本次实际读取的源码、契约、测试与限定案例样本；设计文档中的建议不等于已实现能力。

## 1. 执行摘要

仓库当前不是一条已经完成迁移的单一分析架构，而是**兼容生产运行线与 run-centric/v5 目标线并存**：生产服务通过 `ProductionAnalysisService` 调用兼容 `run_pipeline_e2e()`，其内部由 `run_pipeline()` 编排 D1–D4 主分析并按边界挂接可选双引擎、预测、回溯、报告与反馈步骤；v5 已有独立命题、结构图、仲裁、预测账本及快照对象，但这些契约与 runner 不能据此被认定已替代生产入口（[`engine/application/production_service.py`](engine/application/production_service.py:141)、[`engine/application/pipeline_runner.py`](engine/application/pipeline_runner.py:33)、[`engine/v5/domain.py`](engine/v5/domain.py:140)、[`engine/README.md`](engine/README.md:1)）。

评审结论：**保留兼容入口及现有行为作为迁移锚点；以可验证的边界和档案契约逐步收敛，而不是先做目录级大搬迁或直接切换生产主链。** 现阶段项目状态明确写有真实 cohort 未就绪、`production_ready=false`、`production_switch_permitted=false`（[`META/project-state.json`](META/project-state.json:77)）。故“具备部分结构化能力”不能等价为“生产切换已通过”。

架构上最重要的治理要求是保护已验证行为及数据可追溯性：`tests/test_production_entrypoints_unchanged.py` 对 `run_pipeline` 签名、默认 runner registry、生产权重摘要/文件及规则文件哈希设有基线断言（[`tests/test_production_entrypoints_unchanged.py`](tests/test_production_entrypoints_unchanged.py:13)）；strict/tolerant 失败策略也有隔离测试（[`tests/test_error_policy.py`](tests/test_error_policy.py:1)）。这些门禁应作为渐进迁移护栏，而非通过修改基线来“让重构通过”。

## 2. 范围、方法与限制

### 2.1 范围

- 评估应用入口、生产服务、兼容流水线、v5/DecisionRun 数据边界、案例/报告档案、盲测治理契约与现有测试保护。
- 输出目标架构与 Phase 0–4 的候选迁移路线，实施细节另见 [`REFACTOR_PLAN.md`](REFACTOR_PLAN.md)。
- 不在本次评审中修改业务代码、规则、配置、测试、案例、报告或历史档案；不运行重构或生产切换。

### 2.2 证据限制与本轮实测

1. Graft 对本轮治理/调用关系查询返回 `no matching nodes`；未构建索引，也不声称获得全仓调用图闭包。以下调用关系来自定向源码检查和静态隔离测试。
2. 样本访问限定为授权的 RF000149、RF000417 与 `META/prospective-go/single-cases/P-GO-2026-001-*`。未扫描 `cases/` 全树。此前一次按模式列文件的命令曾显示 `cases/P-GO-2026-001-*` 下一个文件名及大小元数据；未读取其内容，发现超出范围后未再访问该位置。本报告将此记录为范围偏差，不把该目录作为证据。
3. RF000149 冻结 JSON 的实际原始字节 SHA-256 为 `8a5139fa7681f0a48894dfb97eb7445ec5449a4bbb302b5f8b8be4afcbdae733`，旁置摘要文件记录 `82d3c6cba344532b8bef077eda1cdeae0c8736ad048ed786a7a40ff62c63f8e7`；两者不一致，尚待人工裁决。未改动样本或摘要。
4. RF000417 冻结 JSON 的实际原始字节 SHA-256 为 `eef2637e6288bc1b245e8c5c95e10fb73c356773a75dd3c1ce85651de129fde0`，与普通、feedback 前及 feedback 后摘要记录一致。
5. P-GO v004 在获准的 `META/prospective-go/single-cases/` 子树内完成核验。文件的原始字节摘要与 JSON 中 `artifact_sha256` 字段不应直接比较：实现以去除该字段后的 canonical JSON（UTF-8、`ensure_ascii=False`、键排序、紧凑分隔符）计算摘要（[`engine/evaluation/prospective_artifacts.py`](engine/evaluation/prospective_artifacts.py:99)）。对 manifest、frozen-run、intake 与 future-question registration 重算的 canonical 摘要均匹配；manifest 所列 5 个 bundle 文件摘要、bundle file-map 摘要及 run 的父记录摘要也均匹配。该结论限于所授权的 v004 文件。
6. 保护测试实测 `45 passed, 1 warning`；治理、应用隔离与盲测 adapter 定向测试实测 `339 passed`。`tools/README.md` 所列 tool registry 与 rule status markdown/check 命令均成功，check 输出分别为 `tool registry check passed`、`rule status scan passed`。warning 为 dual engine adapter deprecation warning。动态规则计数不固化在本报告。
7. Graft/IWE 返回未提供可用图谱结果；本报告不将精确源码读取、字符串搜索或静态测试夸大为完整动态调用图/运行时隔离证明。

## 3. 仓库理解与系统边界

仓库产品入口定义为面向命理师实战调用的融合分析系统，核心工作流从外部排盘输入，经预检、分析、报告、反馈回流至理论规则材料（[`README.md`](README.md:1)、[`AGENTS.md`](AGENTS.md:18)）。因此边界并非只有 `engine/`：输入校验、报告归档、case 事实、反馈审计与规则治理都会影响可追溯性。

机器状态把产品版本、项目阶段、能力状态及动态扫描策略分开管理；版本以 `VERSION` 为准，运行状态不得从阶段名推断（[`META/project-state.json`](META/project-state.json:1)、[`AGENTS.md`](AGENTS.md:25)）。动态规则计数等不宜硬编码进新评审文件，应使用仓库状态扫描入口按运行时结果读取（[`META/project-state.json`](META/project-state.json:113)）。

### 3.1 已落地兼容运行线（代码事实）

- `run_pipeline(parsed, ...)` 先校验解析后的命盘，再依次调用 energy、picture、yingqi、pangzheng、integrate；其后双引擎、预测及回溯通过各自隔离边界附加，findings 保存失败默认记录 warning（[`engine/application/pipeline_runner.py`](engine/application/pipeline_runner.py:33)、[`engine/application/pipeline_runner.py`](engine/application/pipeline_runner.py:68)、[`engine/application/pipeline_runner.py`](engine/application/pipeline_runner.py:100)、[`engine/application/pipeline_runner.py`](engine/application/pipeline_runner.py:159)）。
- `run_pipeline_e2e()` 提供端到端预检、分析、渲染及反馈步骤，并接收 strict/tolerant policy（[`engine/application/pipeline_runner.py`](engine/application/pipeline_runner.py:174)）。
- `ProductionAnalysisService` 有同步提交、排队/执行、job 生命周期、缓存与 artifact 收集；执行现存 job 时调用兼容 runner 的 strict 模式，并将失败登记在 job 状态（[`engine/application/production_service.py`](engine/application/production_service.py:77)、[`engine/application/production_service.py`](engine/application/production_service.py:108)、[`engine/application/production_service.py`](engine/application/production_service.py:141)、[`engine/application/production_service.py`](engine/application/production_service.py:334)）。
- `engine/pipeline.py` 仍承担历史兼容导出外观，不应在迁移中不经调用方核验就删除（[`engine/pipeline.py`](engine/pipeline.py:1)）。

### 3.2 v5 与 DecisionRun 结构化链（代码事实，不等于生产替换）

- `V5Claim` 是标准命题数据对象，带学校、领域、命题类型、立场、置信度、证据等字段；`V5Confidence` 的等级/分值不等同于事件概率（[`engine/v5/domain.py`](engine/v5/domain.py:85)、[`engine/v5/domain.py`](engine/v5/domain.py:140)）。
- v5 domain 还定义结构图、仲裁、预测、学习信号、run snapshot、case manifest、feedback attachment 与 `V5Output` 等对象（[`engine/v5/domain.py`](engine/v5/domain.py:202)、[`engine/v5/domain.py`](engine/v5/domain.py:226)、[`engine/v5/domain.py`](engine/v5/domain.py:381)、[`engine/v5/domain.py`](engine/v5/domain.py:502)、[`engine/v5/domain.py`](engine/v5/domain.py:583)、[`engine/v5/domain.py`](engine/v5/domain.py:667)）。
- `run_v5()` 与 `run_v5_snapshot()` 提供运行/快照入口（[`engine/v5/runner.py`](engine/v5/runner.py:1257)）。Decision adapter 测试要求 V5 输出转换后保留 claim、预测、反馈信号、归因及可验证 trace，并要求 snapshot 路径与 output adapter 一致（[`tests/test_decision_v5_adapter.py`](tests/test_decision_v5_adapter.py:10)、[`tests/test_decision_v5_adapter.py`](tests/test_decision_v5_adapter.py:38)）。
- 这些事实表明目标链结构已经存在部分实现与测试；它们没有单独证明生产级质量、生产切换授权、真实 cohort 统计有效性或完整盲态隔离。

### 3.3 盲测与治理边界

- 双核契约要求多轮记录保留，最终交付以封存前最后一轮为准；首次揭示核验资料时封存全部轮次，封存后不可修改（[`engine/contracts/22-dual-core-blind-validation-v1.md`](engine/contracts/22-dual-core-blind-validation-v1.md:36)）。
- 统计单元为 `(case_id, matter_category, rule_id)`；分母为零的率值为空；错杀/纠偏仅进入人工待审，不自动生效（[`engine/contracts/22-dual-core-blind-validation-v1.md`](engine/contracts/22-dual-core-blind-validation-v1.md:43)）。
- 未知 trigger 必须失败关闭；契约规定未知证据为 `insufficient_evidence` 且不激活（[`engine/contracts/22-dual-core-blind-validation-v1.md`](engine/contracts/22-dual-core-blind-validation-v1.md:62)）。
- 个案反馈不得自动修改通用规则；历史记录不可覆盖；未解释的双运行线差异由人工裁决并作为阻塞项。上述均为实施硬约束，不得通过重构改成自动规则更新或自动合并差异（[`META/statement-record-contract-v1.md`](META/statement-record-contract-v1.md:13)、[`engine/contracts/22-dual-core-blind-validation-v1.md`](engine/contracts/22-dual-core-blind-validation-v1.md:36)）。

### 3.4 Wave 1 / Wave 2 治理层调用关系与隔离证据

- **Wave 1（`engine/governance/`）**提供纯治理领域契约与执行逻辑：canonical/digest、不可变 fact/snapshot、claim identity/integrity、fact certification、school/structure/composition/trigger registries 及 arbitration。治理包的静态门禁拒绝其向 `engine.application`、`engine.infrastructure`、`tools` 等外层反向导入（[`tests/governance/static_isolation_scanner.py`](tests/governance/static_isolation_scanner.py:58)、[`tests/governance/test_static_isolation.py`](tests/governance/test_static_isolation.py:69)）。
- **Wave 2（`engine/application/`）**通过 `build_governance_fact_snapshot()` 把已校验的 chart、dayun、liunian 与 feature facts 组装为治理 snapshot，并核验 chart raw-source hash（[`engine/application/governance_fact_builder.py`](engine/application/governance_fact_builder.py:237)）；`adapt_decision_school_claim()` / `adapt_domain_claim()` 将既有 claim 显式转换为带 provenance 的治理 claim（[`engine/application/governance_claim_adapters.py`](engine/application/governance_claim_adapters.py:90)、[`engine/application/governance_claim_adapters.py`](engine/application/governance_claim_adapters.py:169)）。`run_governance_shadow()` 调用 Wave 1 的 trigger、composition 与 arbitration，并产出 digest 绑定的 shadow 结果；composition 显式采用 `CompositionExecutionMode.SHADOW`（[`engine/application/governance_shadow_runner.py`](engine/application/governance_shadow_runner.py:152)、[`engine/application/governance_shadow_runner.py`](engine/application/governance_shadow_runner.py:214)）。
- **Evaluation adapter** 是显式盲测接缝：`adapt_governance_shadow_to_blind_outputs()` 验证 schema/version、digest、task、projection identity、claim provenance 和预测字段；不从聚合 trace 猜测语义（[`engine/evaluation/governance_shadow_adapter.py`](engine/evaluation/governance_shadow_adapter.py:129)、[`engine/evaluation/governance_shadow_adapter.py`](engine/evaluation/governance_shadow_adapter.py:228)）。静态测试另覆盖 shadow runner 不被 legacy report/feedback 入口消费、School View adapter 不写 `FactSnapshot`、治理 YAML 不携带历史案例/结果标签/绝对路径及 liunian 不读取系统时间（[`tests/governance/test_static_isolation.py`](tests/governance/test_static_isolation.py:101)、[`tests/governance/test_static_isolation.py`](tests/governance/test_static_isolation.py:199)、[`tests/governance/test_static_isolation.py`](tests/governance/test_static_isolation.py:265)、[`tests/governance/test_static_isolation.py`](tests/governance/test_static_isolation.py:318)）。
- **与 V5 的关系：** 对 `engine/v5/` 源码作治理/shadow 关键字文本检索未命中；这只是静态文本证据，不能证明所有动态间接调用均不存在。`engine/decision/v5_adapter.py` 是将 `V5Output` 包装成 `DecisionRun` 的迁移桥，明确不改变 V5 行为（[`engine/decision/v5_adapter.py`](engine/decision/v5_adapter.py:276)）。当前可见链路因此是 governance → application shadow → evaluation blind adapter，与 V5 runner 并行而非其内部调用；不得据此将 shadow 或 V5 升为默认生产入口。

## 4. 架构诊断

### 4.1 优势与可保留资产

1. **兼容入口有明确签名和行为基线。** 测试锁定 `run_pipeline` 签名、runner registry、默认权重与规则文件哈希；这为小步迁移提供了保护面（[`tests/test_production_entrypoints_unchanged.py`](tests/test_production_entrypoints_unchanged.py:17)、[`tests/test_production_entrypoints_unchanged.py`](tests/test_production_entrypoints_unchanged.py:35)、[`tests/test_production_entrypoints_unchanged.py`](tests/test_production_entrypoints_unchanged.py:39)、[`tests/test_production_entrypoints_unchanged.py`](tests/test_production_entrypoints_unchanged.py:50)）。
2. **应用层已有部分服务化边界。** 生产服务承担请求规范化、job/cache/artifact 责任，而领域计算仍由 pipeline 执行（[`engine/application/production_service.py`](engine/application/production_service.py:54)、[`engine/application/production_service.py`](engine/application/production_service.py:225)、[`engine/application/production_service.py`](engine/application/production_service.py:334)）。
3. **错误策略不是隐式单一行为。** tolerant 与 strict 的差异由测试覆盖；renderer、findings 保存、feedback ingest 失败在 tolerant 下警告返回、strict 下传播异常，生产服务 strict 行为亦有测试说明（[`tests/test_error_policy.py`](tests/test_error_policy.py:1)、[`tests/test_error_policy.py`](tests/test_error_policy.py:90)）。
4. **结构化迁移资产已存在。** v5 domain、snapshot、DecisionRun adapter、案例 manifest 和反馈附件可以作为未来契约基础，不必另造并行 DTO（[`engine/v5/domain.py`](engine/v5/domain.py:381)、[`engine/v5/domain.py`](engine/v5/domain.py:502)、[`cases/C-2026-001-乾-庚申戊寅壬子辛丑/manifest.json`](cases/C-2026-001-乾-庚申戊寅壬子辛丑/manifest.json:1)）。
5. **存储与学习治理已有明确不可越界原则。** Statement Record 契约要求反馈通过稳定 `statement_id` 正向连接规则元数据，冻结生成时置信度，并禁止从自然语言反馈猜测规则身份（[`META/statement-record-contract-v1.md`](META/statement-record-contract-v1.md:13)、[`META/statement-record-contract-v1.md`](META/statement-record-contract-v1.md:148)、[`META/statement-record-contract-v1.md`](META/statement-record-contract-v1.md:179)）。

### 4.2 主要架构风险/待验证点

| 风险 | 证据与判断 | 处理原则 |
|---|---|---|
| 双运行线职责可能漂移 | 兼容 runner 与 v5 runner 并存；生产 service 当前显式走兼容 strict 路径（[`engine/application/production_service.py`](engine/application/production_service.py:141)、[`engine/v5/runner.py`](engine/v5/runner.py:1257)）。两线是否共享相同输入语义、规则集及输出承诺，需后续用契约对照验证。 | 不以目录名称或“新系统”标记推断替换关系；明确兼容边界与切换门禁。 |
| 外层服务可能同时承担多类编排责任 | `ProductionAnalysisService` 涵盖提交/排队、缓存、artifact 与 summary 等职责（[`engine/application/production_service.py`](engine/application/production_service.py:77)、[`engine/application/production_service.py`](engine/application/production_service.py:237)、[`engine/application/production_service.py`](engine/application/production_service.py:334)、[`engine/application/production_service.py`](engine/application/production_service.py:393)）。这是职责集中信号，但仅凭此不足以判定必须拆类。 | Phase 0 先梳理边界与依赖；仅在测试可隔离、真实变更需要时拆分。 |
| 持久化/归档体积和重复制品可能放大维护成本 | 既有 `REPO_DIAGNOSIS.md` 报告抽查发现过较大的 analysis JSON，但其量级属于历史扫描，不在本次重新测量范围；限定案例中 C-2026-001 manifest 显示多个 run 制品（[`REPO_DIAGNOSIS.md`](REPO_DIAGNOSIS.md:63)、[`cases/C-2026-001-乾-庚申戊寅壬子辛丑/manifest.json`](cases/C-2026-001-乾-庚申戊寅壬子辛丑/manifest.json:5)）。 | 先定义 artifact inventory、权威产物与引用关系；禁止未经专项归档方案删历史文件。 |
| 可读报告、statement index、statement record 与运行快照边界需持续明确 | Statement Record 设计规定一条学习断语需绑定唯一 `rule_id/family_id`，`statement_index` 只是展示索引而非唯一学习索引（[`META/statement-record-contract-v1.md`](META/statement-record-contract-v1.md:13)、[`META/statement-record-contract-v1.md`](META/statement-record-contract-v1.md:20)）。 | 保持展示模型与学习模型分离；以稳定 ID 建链，不从文本反推。 |
| 盲测流程设计未等同完整产品化 | 合约描述封存和失败关闭，但 `DESIGN_HANDOFF.md` 列出入口、持久化、统计等已共识未实现事项（[`DESIGN_HANDOFF.md`](DESIGN_HANDOFF.md:175)）。 | 先按流程完整性和隔离证明验收，不预设准确率门槛或自动学习。 |
| 自动学习/路由切换存在高风险误读 | 项目状态禁止切生产的当前证据，以及设计中禁止单案自动改规则的边界明确（[`META/project-state.json`](META/project-state.json:77)、[`DESIGN_HANDOFF.md`](DESIGN_HANDOFF.md:10)）。 | 生产规则、权重、路由维持人工批准；不得在架构重构名义下改变决策算法。 |
| 静态隔离有定向门禁，但调用图闭包仍不完整 | Wave 1 forbidden-import、Wave 2 shadow legacy-consumer、School View Snapshot 写入及 liunian 系统时间等检查已由专用 scanner/test 覆盖；治理/应用/adapter 定向测试通过。Graft 没有匹配图节点，且 V5 关键词搜索只属文本级证据。 | 后续若改动跨目录依赖，先取得批准并补足精确调用方/影响面；当前不声称穷尽动态或间接依赖。 |

## 5. 建议目标架构（设计建议，不是当前事实）

采用**边界优先、双运行线可共存、产物可追溯、行为受契约保护**的目标形态：

```text
入口 / API / CLI
  └─ Application use case（校验请求、选择已批准的执行模式、错误策略）
       ├─ Compatibility engine adapter ── 现有 D1–D4 生产线（默认保持）
       └─ V5/Decision adapter ─────────── 受控预生产 / 已批准的 run-centric 流程
              ↓
        统一 Run Snapshot / DecisionRun / Statement Records
              ↓
        Artifact manifest（输入版本、引擎/规则版本、运行产物引用、哈希/状态）
              ↓
        Renderer（用户可读输出）与 feedback attachment（可追踪学习输入）分离
              ↓
        Feedback / blind-validation governance（只产生审核材料，不直接写生产规则）
```

建议的稳定边界：

- **输入/预检边界**：外部排盘文本解析与 chart validation 先完成，再交执行器；未验证命盘不得进入规则分析（当前 runner 已调用 `ensure_parsed_chart_validated`，[`engine/application/pipeline_runner.py`](engine/application/pipeline_runner.py:68)）。
- **Use case 边界**：由应用用例协调执行模式、错误策略与运行生命周期；底层计算只接收经过校验的输入，渲染与归档作为独立端口。此为建议，具体接口待实施前核对。
- **执行器边界**：兼容 pipeline 和 v5 作为显式执行器实现暂时并存；调用方不得依赖具体内部阶段。没有正式门禁前，兼容执行器仍是默认生产入口。
- **运行记录边界**：每次运行的身份、不可变快照、DecisionRun trace、StatementRecord 与 manifest 通过稳定 ID 关联；不把完整渲染文案当作机器学习唯一事实源（[`META/statement-record-contract-v1.md`](META/statement-record-contract-v1.md:179)）。
- **产物边界**：manifest 记录权威产物、版本及引用；renderer 可重建展示产物，但不得覆盖已封存预测/盲测轮次。案例样本已有多制品引用形态，可作为审查起点而不是强行统一旧档案（[`cases/C-2026-001-乾-庚申戊寅壬子辛丑/manifest.json`](cases/C-2026-001-乾-庚申戊寅壬子辛丑/manifest.json:14)）。
- **治理边界**：盲测、普通咨询、核验/复核、前瞻预测要区分模式与数据访问边界；核验后不倒改盲测数据；学习信号进入人工审核，不自动改变生产规则、权重或路由（[`engine/contracts/22-dual-core-blind-validation-v1.md`](engine/contracts/22-dual-core-blind-validation-v1.md:36)、[`DESIGN_HANDOFF.md`](DESIGN_HANDOFF.md:12)）。

## 6. 渐进式重构路线（Phase 0–4）

所有阶段均为**待批准候选**。每阶段必须可单独回滚；先加契约测试/行为快照，再改实现；不允许业务规则变化混入纯结构重构。

### Phase 0 — 证据基线与边界冻结（本轮已执行，文档更新与范围复核完成）

目标：把当前兼容生产行为、治理隔离边界、获准样本哈希与错误语义记录为可复核基线。

- `run_pipeline` / `run_pipeline_e2e` 仍是兼容生产入口；`ProductionAnalysisService` strict 行为与 V5 adapter 契约由保护测试验证，测试结果见本节第 3 项。
- 定向源码检查确认 Wave 1 / Wave 2 / blind adapter 的调用关系与静态隔离检查范围，详见 3.4；未将源码检索冒充完整调用图。
- 授权样本实测：RF000149 sidecar SHA-256 mismatch 是待裁决阻塞项；RF000417 原始字节 SHA-256 与 feedback 前后记录一致；P-GO v004 canonical artifact、bundle file 与 parent hashes 全部匹配。仅核验获准目录。
- 验证命令及结果：`pytest tests/test_production_entrypoints_unchanged.py tests/test_error_policy.py tests/test_decision_v5_adapter.py -q`（45 passed, 1 deprecation warning）；`pytest tests/governance tests/application/test_governance_shadow_runner.py tests/application/test_governance_fact_builder.py tests/application/test_governance_claim_adapters.py tests/application/test_application_import_isolation.py tests/evaluation/test_governance_shadow_adapter.py -q`（339 passed）。tool registry 与 rule status 的 markdown/check 命令均执行成功。
- 未改业务代码、配置、测试、案例或既有 artifact；本 Phase 0 仅允许更新本评审与 [`REFACTOR_PLAN.md`](REFACTOR_PLAN.md)。

退出条件：保护与治理门禁已有可复跑结果；RF000149 mismatch 作为未解决证据事项保留；Phase 1 仍需用户另行批准，不因 Phase 0 完成而自动启动。

### Phase 1 — 应用层接口收敛（不换算法）

目标：明确请求、执行模式、输出与适配器边界，保留 `run_pipeline` 的兼容签名和行为。

- 先写 characterization/contract tests；将入口对领域实现细节的耦合逐项列出。
- 若实际调用关系证明有必要，逐步把 pipeline orchestration 与 service job/cache/artifact 责任隔离；避免为了层次而新建空接口或工厂。
- `engine/pipeline.py` 兼容导出和 `ProductionAnalysisService` 对外契约在迁移期保留。

退出条件：生产入口兼容测试、错误策略测试及相关应用服务测试维持通过；无规则/权重变化。

### Phase 2 — 运行记录与产物引用标准化

目标：让每次运行可定位、可重放审计、可关联反馈，不破坏历史档案。

- 以现存 `V5RunSnapshot`、`DecisionRun`、manifest、feedback attachment 与 Statement Record 合约为候选边界；先对字段、版本、缺失值与兼容转换做契约映射。
- 新运行优先保证 run ID、源引擎/规则版本、产物身份和稳定 statement ID 完整；历史产物采用只读 legacy lane，不批量迁移/重写。
- 大型 artifact 的拆分、压缩或去重另立容量与恢复方案，不作为本阶段默认动作。

退出条件：新样本引用闭合、反馈能按稳定 ID 回链、旧样本只读且可读取；封存数据不被覆盖。

### Phase 3 — 双运行线受控互操作

目标：在不切生产默认值的前提下，对兼容线和 v5/DecisionRun 做限定输入下的契约比对。

- 明确可比字段、不可直接比较字段、差异分级及人工 adjudication 流程；不将数值相似度视为算法等价。
- 通过独立测试和获准样本验证输入校验、trace 完整、置信度语义、预测范围、产物引用和失败行为。
- 盲测必须先封存后核验；无法对照事项按既定流程失败处理；不能通过切换样本或读取反馈绕过盲态边界。

退出条件：流程隔离、制品完整性和差异解释达到人工批准标准；仍不自动切生产。

### Phase 4 — 生产切换评估（独立审批门）

目标：只有真实 cohort 与预先批准的门槛足够时，提出生产切换决策。

- 根据实时项目状态及正式双核盲测/生产门禁证据重新评估 readiness；不得引用旧报告中的静态数字代替扫描。
- 由命理师/产品负责人确认数据范围、统计口径、风险阈值、回滚方案及用户报告兼容性。
- 通过批准后另立实施变更；未通过则兼容线继续作为生产默认。

当前状态 `production_ready=false` 且 `production_switch_permitted=false`，故 Phase 4 当前不能被视为已满足（[`META/project-state.json`](META/project-state.json:77)）。

## 7. 必须由人工确认的事项

1. 兼容生产 pipeline 是否在接下来一阶段继续作为唯一默认生产入口（建议：是，直至切换门禁获批）。
2. Phase 1 是否允许为了职责隔离调整 `ProductionAnalysisService` 内部结构；对外请求字段、响应语义与 job 状态是否必须完全不变。
3. 新 run snapshot、DecisionRun、StatementRecord 与现有 manifest 的权威关系、schema 版本策略、缺失字段策略及向后兼容期限。
4. 盲测 MVP 的业务负责人、规定事项范围、首次核验资料交付与全流程失败后的处置方式。
5. 案例 artifact 容量治理是否单独立项；在无恢复性证明前建议不删除、不覆盖历史制品。
6. 双运行线对照使用的批准样本、差异判定人和生产切换统计门槛。项目状态当前不允许默认切换。
7. RF000149 冻结文件与 sidecar 摘要不一致，需人工裁决并确定是否允许后续使用；不得自行重算后改写冻结记录。RF000417 与 P-GO v004 的限定哈希检查通过，但不替代其他样本准入审批。

## 8. 评审结论

推荐采用**兼容优先、契约先行、run-centric 逐步接入、盲测与学习治理独立、生产切换单独审批**的渐进路线。不要把 v5 已有对象、一次案例产物或历史诊断报告误读为生产迁移门禁已通过。当前只完成架构诊断与候选路线；所有实施都等待用户评审确认。
