# tools/ · 自动化工具

> 本文件是工具入口的人工索引。若与具体工具 docstring 冲突，以工具文件头 + [`engine/contracts/00-OVERVIEW.md`](../engine/contracts/00-OVERVIEW.md:1) 为准。
>
> **状态约定**：
> - **active**：当前推荐入口，可用于新案 / 新流程。
> - **internal**：内部支持工具，通常由 active 工具或测试调用；不作为命理师日常手动入口。
> - **deprecated**：历史入口，默认不应运行；仅保留追溯能力。
> - **historical**：历史/迁移辅助工具，不作为日常主入口。
> - **missing**：文档曾提及但当前仓库未实现；不得作为可用工具引用。

---

## active · 当前推荐工具

| 工具 | 用途 | 推荐入口 / 说明 |
|---|---|---|
| [`preflight.py`](preflight.py:1) | input.md schema 校验与解析 | 新案入口护栏 |
| [`batch_intake.py`](batch_intake.py:1) | 批量入库：inbox → cases/pipeline | v1.3 D6 |
| [`batch_review.py`](batch_review.py:1) | 批量复盘：已填 feedback.md → ingest | v1.3 D6 |
| [`render_report.py`](render_report.py:1) | legacy standard report 渲染入口 | 当前正式兼容入口；固定使用 `templates/report-v1.3.md`，由 output_linter 兜底；不承载新增 run-centric 字段 |
| [`render_report_v6.py`](render_report_v6.py:1) | run-centric preprod 五派报告渲染 | 旁路生成 report / `*.v5.json` / `*.run.json` / `*.decision-run.json` / `*.feedback-attachment.json`；新增报告字段必须先进入 run / decision 结构，再渲染 |
| [`domain_analysis_cli.py`](domain_analysis_cli.py:1) | 六源三领域分析引擎 CLI | 交互与非交互双模式；写 `*.run.json` + `*-content-report.md`；`audit` 子命令只读校验 hash 与十八槽位覆盖完整性；不替代 `render_report.py`，不写 case 目录 |
| [`domain_prospective_cohort.py`](domain_prospective_cohort.py:1) | 事业、财富、婚姻三领域 prospective 盲测基线 CLI | `intake / freeze / reveal / score / status`；盲态严格白名单、递归泄漏拒绝、create-only hash 链、domain/task/claim 分账及 historical/prospective 隔离；少于 30 个真实 prospective 案例固定 `not_ready`，production false；不写生产规则、权重或路由 |
| [`domain_capability_status.py`](domain_capability_status.py:1) | 六源三领域十八槽位能力覆盖与弃权诊断 | 只读消费一个或多个 `*.run.json` 或目录；registration/runtime 严格分账，按 school/domain/task 输出同源 JSON/Markdown，支持 `--check` 校验 output hash、十八槽位身份、重复 run 与损坏输入；任务 4 正式门禁未落地时明确 `unavailable`；不写规则、权重或路由 |
| [`domain_feedback.py`](domain_feedback.py:1) | 六源三领域命题级结构化反馈与只读校准候选 | `prepare / ingest / status / candidates`；反馈绑定 run ID、snapshot output hash、claim ID 与稳定 claim hash，create-only 且拒绝 symlink、篡改、孤儿 claim、重复 reviewer/反馈；unknown、partial、应期偏差独立分账，高风险候选强制人工 review；不自动 promotion，不写理论、权重、路由、规则或历史 snapshot |
| [`output_linter.py`](output_linter.py:1) | 报告出口 lint / 禁越界输出 | 兜底护栏 #2 |
| [`three_layer_check.py`](three_layer_check.py:1) | 应期三层门检查 | v1.2 W3 护栏 |
| [`feedback_ingest.py`](feedback_ingest.py:1) | 结构化反馈摄入：`[y]` / `[n]` / `[?]` / `[skip]`，并把真实 `statement_index.json` 中的并行域 statement fanout 到 expert / adjudication 反馈日志 | v1.3 推荐反馈入口；无并行域 statement 时保持零行兼容行为 |
| [`parallel_domain_weight_status_scan.py`](parallel_domain_weight_status_scan.py:1) | 跨案例聚合 expert × domain 历史反馈并对账 canonical `feedback_overlay` | active 只读状态扫描；支持 `--format markdown|json` 与 `--check`，pending 时仅返回非零退出码供人工 review，不做 promotion、不写权重、不切换路由 |
| [`promote_expert_weight_feedback.py`](promote_expert_weight_feedback.py:1) | 将 expert × domain 反馈统计提升到 canonical runtime `feedback_overlay` | 默认 dry-run；正式写入必须同时使用 `--apply --reviewed-by <人类姓名>`，version 严格递增；只写 `engine/expert-weights.yaml`，不修改 legacy `engine/domain-weights.yaml` |
| [`v5_prediction_feedback.py`](v5_prediction_feedback.py:1) | v5 prediction-first 预测反馈 | 可读 `.v5.json` / `.run.json`；只写 `.v5.json`，拒绝写 run snapshot |
| [`feedback_review_gate.py`](feedback_review_gate.py:1) | 反馈复核包摄入前置闸门 | 只读检查 `META/feedback-closure-review-pack-*.json` 是否已完成人工裁决 |
| [`feedback_impact_report.py`](feedback_impact_report.py:1) | 反馈影响路径与置信度调整可视化 | dry-run 计算断语→规则→置信度变化，输出 Markdown + Mermaid |
| [`domain_role_audit.py`](domain_role_audit.py:1) | 规则 domain/role 分账审计矩阵 | 只读输出 `rule_id × domain × role` 命中率，验证错域样本是否进入 `misapplied` |
| [`late_feedback.py`](late_feedback.py:1) | 应期延迟反馈：±1 年窗口 | v1.3 D7 |
| [`boundary_miner.py`](boundary_miner.py:1) | ≥5 miss 后自动挖候选边界 | v1.3 D3 |
| [`veto_miner.py`](veto_miner.py:1) | 候选否决兜底：低后验 + 无边界 → review | v1.3 D4 |
| [`iteration_report.py`](iteration_report.py:1) | 每 10 完成反馈案产出迭代报告 | v1.3 D8 |
| [`cross_school_scan.py`](cross_school_scan.py:1) | 每 10 案跨派一致性扫描 | v1.3 自迭代 |
| [`extract_predictions.py`](extract_predictions.py:1) | 抽取 ★4+ 应期到 predictions/ | 预测封存现行入口 |
| [`timing_report.py`](timing_report.py:1) | 聚合 pipeline、batch、feedback、iteration timing.json | v1.2.1+ metrics；同时扫描 `cases/*/findings/timing.json` 与 `META/timings/*.json` |
| [`production_api.py`](production_api.py:1) | 生产 MVP HTTP JSON API | stdlib 同步 API；封装分析提交、状态查询、SQLite 元数据与缓存；高并发场景后续演进为 job queue |
| [`tool_registry.py`](tool_registry.py:1) | 扫描 tools/*.py 并生成可执行工具注册表 | 防止 README 与真实工具漂移 |
| [`school_capability_baseline.py`](school_capability_baseline.py:1) | 学派能力盲评基线的 audit / freeze / score / report CLI | 只读能力评估入口；`audit` 只生成 `school-capability-case-audit/v1`，不可直接评分，必须经人工审核并提升为含 `expected_schools` 的 reviewed `school-capability-case-manifest/v1`；仅写独立 artifact，不是生产校准、规则更新或权重写入入口 |
| [`school_capability_dataset.py`](school_capability_dataset.py:1) | 学派能力评估 inventory、prospective intake、盲评 bundle 与结构化标签准备 | 数据治理辅助；`prospective-intake` 拒绝 feedback / labels / report / known facts 字段或文件，并将唯一匹配的短槽位任务键解析为完整 case ID；`prepare-blind` 仅写安全 canonical intake、tasks、rule snapshot、chart 与 manifest，记录逐文件及 bundle SHA-256，并拒绝 symlink 与已存在目标目录；所有写命令支持 `--dry-run`；不会更新生产规则或权重 |
| [`school_capability_prospective.py`](school_capability_prospective.py:1) | prospective 盲包 staged 冻结、受控父链迁移与 freeze witness 链 | `stage-frozen-run` 从已校验盲包生成确定性六来源三态冻结制品；`migrate-single-case-parent-chain-v002` 仅用于获批的首案整条父链 v002 修订，先 sibling staging 复验、默认 dry-run、正式模式固定顺序 create-only；`witness-freeze-chain` 校验正式 intake、盲包与 staged run 后，一次安全生成或追加每案 `registered → prepared → freeze` 三事件段 |
| [`school_capability_review.py`](school_capability_review.py:1) | prospective 高风险任务独立双审、冲突仲裁与 A 级标签治理 | `prepare / submit / adjudicate / finalize / audit`；只消费冻结后 observation，拒绝预测/runner/report 泄漏、重复 reviewer、角色重叠及覆盖既有目标；所有写命令支持 `--dry-run`；不替代 `feedback_ingest.py`，不写生产规则或权重 |
| [`school_capability_cohort.py`](school_capability_cohort.py:1) | 单案 prospective 的十案父引用 cohort、双门禁与三门禁报告 CLI | `build / verify / score / gate / future-gate / report`；仅离线评估，只展开不可变父引用，两个离线 GO 均不代表平台 GO 或生产 GO，`production_switch=false`；不写生产入口、规则或权重 |
| [`school_capability_batch.py`](school_capability_batch.py:1) | 历史输入/反馈分文档的批量隔离、去重、冻结、保守标签、评分与基线报告 | 只消费先冻结输入、后揭示反馈；产物固定标为 historical blind candidate，不冒充 prospective，不写生产权重或规则 |
| [`school_capability_incremental.py`](school_capability_incremental.py:1) | 基于不可变父 baseline 构建独立历史隔离增量批次 | `prepare / stage-a / stage-b / bind-formal / finalize`；按命主 identity 求增量、先冻结后揭示，仅绑定低风险目录内标签，高风险无 A 级双审保持不可评分；不覆盖父制品或修改生产路由/权重 |
| [`school_capability_task8.py`](school_capability_task8.py:1) | 六个月计划 Task 8 的六来源历史隔离基线编排 | 严格拆分 stage-a 冻结与 stage-b 标签揭示，复用现有 runner/evaluation 契约并只读核验旧 prospective bundle；不写生产路由、权重或规则 |
| [`theory_slice_status.py`](theory_slice_status.py:1) | 分账扫描理论目录条目与可执行切片清单 | 只读输出 `catalog_count` / `executable_slice_count`；不更新规则生命周期、生产 registry 或权重 |
| [`rule_status_scan.py`](rule_status_scan.py:1) | 扫描 theory/*/index.yaml 的规则状态分布、N_eff、review 清单 | 易漂移规则状态的机器真相源 |
| [`career_path_competition_harness.py`](career_path_competition_harness.py:1) | 预注册职业路径三模型竞争实验 | 严格 prepare/predict/freeze/reveal/score；绑定 cohort、预注册、代码/规则和预测哈希；一个预注册 ID 只允许评分一次；当前无新 holdout 时只返回 not_ready，不切生产入口 |
| [`career_path_product_routing.py`](career_path_product_routing.py:1) | 冻结竞争 score receipt 的只读产品分流控制 | `status / report`；验证预注册、cohort、prediction、labels、freeze、model disposition、score receipt 与一次评分唯一性，失败关闭输出 blocked/shadow/structural-assistant/rejected；旧 invalidated v1 永不晋级，缺少预注册结构阈值时 not_evaluable，所有状态 production false；不评分、不创建 receipt、不切生产 |
| [`career_relation_expert_annotation.py`](career_relation_expert_annotation.py:1) | 职业关系模型中间结构盲标、双审裁决与一致率门禁 | `status / prepare-blind / submit`；仅允许安全命盘事实与冻结理论引用，默认 dry-run、显式 `--write` 才 create-only 落盘，拒绝泄漏、symlink、覆盖、agent 冒充专家与重复 reviewer；无真实双审时返回 `not_ready`，只服务结构机制审计和新 model_id 设计，不评分、不解禁 invalidated model-v1、不切生产 |
| [`career_path_prospective_cohort.py`](career_path_prospective_cohort.py:1) | 真正未见职业路径 cohort 的 prospective intake、隔离、双审裁决、时序标签与受控准入 | `status / intake / build-manifest / submit-review` 及 Python finalize/registry API；盲态白名单、源内容 SHA-256、case_id + 性别四柱身份去重、旧开发集排他，默认 dry-run/create-only/拒绝 symlink；mixed/unknown 保留但不计严格二分类分母；当前无真实样本固定 `not_ready`、0 案、production false，不预测、不评分 |
| [`career_path_holdout_gate.py`](career_path_holdout_gate.py:1) | 职业路径真正未见 holdout 数据准入门禁 | 只读核验预注册、旧开发集排他、至少 30 个严格二分类及每类至少 10、真实 `human-*` 双审/第三方裁决、labels SHA-256；mixed/unknown 保留但不计严格二分类分母；当前返回 `not_ready`，不预测、不评分、不切生产 |
| [`career_path_promotion_gate.py`](career_path_promotion_gate.py:1) | 冻结职业路径分类器的持续 promotion 门禁 | 只读重算 holdout 指标并校验预测哈希与一次冻结；显式接受旧标签或正式时序标签 schema，未知 schema 失败关闭；任一阈值失败即返回非零退出码，不写生产规则、权重或路由 |
| [`l1_routing_holdout_audit.py`](l1_routing_holdout_audit.py:1) | L1 learned/static 无泄漏留出集竞争覆盖与效用审计 | 只读冻结历史 batch/score；按命主分组切分、重算 cfv-v1 原型，只有同案同任务至少两派可评分才允许对照；learned 必须改变至少一个选择且效用不退化才可 GO |
| [`rebuild_l1_routing_evidence.py`](rebuild_l1_routing_evidence.py:1) | 重建 L1 路由盲测证据 | 从隔离命盘汇总重新冻结当前 runner 输出，揭示既有人工标签并评分；写 batch/scores/manifest，不写生产权重 |
| [`conditional_learning.py`](conditional_learning.py:1) | L9 条件化学习离线治理 CLI | `decide` / `apply` / `rollback`；六维能力身份按 N_eff 分级，高风险与成熟更新须显式审批，所有写流程支持 `--dry-run`；只写独立内容寻址能力快照，不写静态权重、生产规则或历史 run snapshot |
| [`event_archive.py`](event_archive.py:1) | 交互事件增量归档：把一次询问、分析、结果追加到报告侧 events 或 META 专项记录 | 处理后归档入口；case 可定位时写 `reports/*-events.md`，否则写 `META/session-events.md` |
| [`archive_verified_artifact.py`](archive_verified_artifact.py:1) | 单用途 verified artifact 归档 CLI | 通用归档入口；接受 `SOURCE --archive-root ARCHIVE_ROOT`，委托 `engine.archive.archive_verified_artifact()`，不专属 as-of |

---

## 调用边界

- [`tools/`](README.md:1) 作为 CLI / adapter 层：负责文件入口、人工日志、批处理与审计落盘。
- 当前 D1-D4 核心编排优先查看 [`engine/application/pipeline_runner.py`](../engine/application/pipeline_runner.py:1)，生产同步封装查看 [`engine/application/production_service.py`](../engine/application/production_service.py:1)。
- [`render_report.py`](render_report.py:1) 是 legacy standard report 兼容入口；[`render_report_v6.py`](render_report_v6.py:1) 是 run-centric preprod 证明入口。两者并存期间，不从 Markdown 反推结构化状态。
- [`conditional_learning.py`](conditional_learning.py:1) 是 staged 离线治理入口，不替代 [`feedback_ingest.py`](feedback_ingest.py:1)，也不切换生产路由；业务门禁与快照语义位于 [`engine/learning/`](../engine/learning/)，CLI 只做文件 adapter。
- 新报告字段必须先进入 [`V5RunSnapshot`](../engine/v5/domain.py:366) / [`DecisionRun`](../engine/decision/models.py:302) 等结构化对象，再由报告视图渲染；不得把新领域能力直接塞进 [`tools/`](README.md:1)。
- 新代码不应把 [`engine/application`](../engine/application:1) 继续扩大为依赖 [`tools/`](README.md:1) 的工具集合；涉及长期 API / queue / storage 时应下沉到 application / infrastructure 层。

任派职业角色变化应期切片当前仅为 staged 专用入口：它消费已成立的职业变化事件，使用真实岁运触发生成可证伪 L5 窗口；未注册到默认 runner registry，也不替换正式 pipeline 或报告入口。

---

## internal · 内部支持工具

| 工具 | 用途 | 调用边界 |
|---|---|---|
| [`feedback_loop.py`](feedback_loop.py:1) | 反馈回流到底层规律生命周期 | 通常由 [`feedback_ingest.py`](feedback_ingest.py:1) / [`batch_review.py`](batch_review.py:1) 调用 |
| [`pipeline_adapters.py`](pipeline_adapters.py:1) | application ports 的 tools 层默认适配器 | 由 [`engine/application/pipeline_runner.py`](../engine/application/pipeline_runner.py:1) 兼容旧 e2e 调用时延迟加载；新代码优先显式注入 ports |
| [`rule_lifecycle.py`](rule_lifecycle.py:1) | 规律状态机、Beta 缓存、v1.4 V1/V2 字段 | 生命周期底层实现，不建议绕过反馈入口直接改状态 |
| [`drift_detect.py`](drift_detect.py:1) | 滑动窗漂移检测 | 由反馈闭环调用 |
| [`check_archive_links.py`](check_archive_links.py:1) | 检查 case/report 归档互链是否可追踪 | 归档质量检查；通常在报告批量归档后运行 |
| [`fix_archive_links.py`](fix_archive_links.py:1) | 规范化 case/report Markdown 互链 | 维护辅助；会改写归档链接，运行前建议先检查 diff |
| [`_audit_p6a1.py`](_audit_p6a1.py:1) | P6-A1 新案反馈可追踪性审计 | 保留审计脚本；非日常入口 |
| [`_build_rule_graph.py`](_build_rule_graph.py:1) | 构建规则图谱 IR | 内部生成物维护 |
| [`_generate_unified_rule_ir.py`](_generate_unified_rule_ir.py:1) | 汇总多派规则为统一 IR | 内部生成物维护 |
| [`_verify_production_rules.py`](_verify_production_rules.py:1) | 生产规则校验 | 内部审计 |
| [`feedback_statement_trace_audit.py`](feedback_statement_trace_audit.py:1) | 反馈断语追踪审计 | 内部审计 |
| [`feedback_v2_preprocess.py`](feedback_v2_preprocess.py:1) | v2 反馈预处理 | 历史反馈治理辅助 |
| [`chart_validation_calibrate.py`](chart_validation_calibrate.py:1) | 使用现有案例强制重算排盘并校准验证模块 | 内部只读审计；关闭问真可信来源旁路，输出 JSON/Markdown 校准记录 |
| [`v6_preprod_coverage_audit.py`](v6_preprod_coverage_audit.py:1) | v6 preprod 报告覆盖审计 | 只读审计报告与配套 artifact，用于切默认入口前的证据积累 |
| [`_generate_p_series_career_summary.py`](_generate_p_series_career_summary.py:1) | 生成 P 系列职业标签阶段摘要 | 内部一次性汇总脚本；不作为生产入口 |
| [`_verify_p_series_career_labels.py`](_verify_p_series_career_labels.py:1) | 校验 P 系列职业标签制品 | 内部历史实验审计；不作为生产入口 |
| [`as_of_admission_age_gate.py`](as_of_admission_age_gate.py:1) | as-of admission 年龄与截止日预筛 | as-of 内部证据门禁；不切换生产入口 |
| [`as_of_prospective.py`](as_of_prospective.py:1) | as-of 前瞻冻结、反馈释放与核验制品 CLI | 内部前瞻证据链入口；仅创建新制品，不切换生产入口 |
| [`as_of_blind_judgment_probe.py`](as_of_blind_judgment_probe.py:1) | as-of 盲态结构判断探针 | 历史/手动 side path，只用于方法验证 |
| [`as_of_candidate_prioritizer.py`](as_of_candidate_prioritizer.py:1) | as-of 候选优先级排序 | 内部候选治理工具 |
| [`as_of_contract_gate.py`](as_of_contract_gate.py:1) | as-of 输入契约预检查 | 内部失败关闭门禁 |
| [`as_of_current_state_scanner.py`](as_of_current_state_scanner.py:1) | as-of 当前状态候选扫描 | 内部只读扫描 |
| [`as_of_freeze_preflight.py`](as_of_freeze_preflight.py:1) | as-of 冻结前完整性检查 | 内部冻结证据门禁 |
| [`as_of_freeze_scaffold.py`](as_of_freeze_scaffold.py:1) | as-of 冻结制品脚手架 | 内部制品生成辅助 |
| [`as_of_methodology_diff.py`](as_of_methodology_diff.py:1) | as-of 方法论差异审计 | 内部只读审计 |
| [`as_of_raw_feedback_paipan.py`](as_of_raw_feedback_paipan.py:1) | 原始反馈排盘转 as-of 候选 | 历史数据准备辅助 |
| [`as_of_root_level_gate.py`](as_of_root_level_gate.py:1) | as-of 根层双证据正式校验 | 内部失败关闭门禁 |
| [`as_of_running_stats.py`](as_of_running_stats.py:1) | as-of 运行统计聚合 | 内部只读统计 |
| [`as_of_theory_lookup.py`](as_of_theory_lookup.py:1) | as-of 理论结构化检索 | 内部理论证据检索 |
| [`as_of_verdict_stats.py`](as_of_verdict_stats.py:1) | as-of 盲态裁决统计 | 内部只读统计 |
| [`audit_lunar_python_c2026.py`](audit_lunar_python_c2026.py:1) | C-2026 lunar-python 排盘审计 | 专项历史审计 |
| [`batch_occupation_accuracy.py`](batch_occupation_accuracy.py:1) | 职业四分类批量准确率评估 | 历史实验工具；结果不作为生产资格证据 |
| [`p_series_career_blind_harness.py`](p_series_career_blind_harness.py:1) | P 系列任职/经营标签隔离回放 | 历史开发回放，不得冒充 unseen holdout |
| [`p_series_career_classifier_v2_harness.py`](p_series_career_classifier_v2_harness.py:1) | 职业路径 v2 标签隔离 harness | 已否决历史实验；不切生产 |
| [`p_series_career_classifier_v3_harness.py`](p_series_career_classifier_v3_harness.py:1) | 职业路径 v3 标签隔离 harness | 已否决历史实验；不切生产 |

---

## deprecated · 历史入口，默认禁用

当前无保留的 deprecated 可执行入口；旧 `calibrate.py` 已删除，反馈入口统一使用 [`feedback_ingest.py`](feedback_ingest.py:1) + [`feedback_loop.py`](feedback_loop.py:1)。

---

## historical · 历史/迁移辅助

| 工具 | 用途 | 说明 |
|---|---|---|
| [`as_of_integration.py`](as_of_integration.py:1) | G8 as-of 统一报告薄编排 | 运营者手动调用的旁路证明入口；仅在显式截止日与受控事件账本下追加状态快照，未接入默认 runner、生产服务或 HTTP API |
| [`as_of_session_cli.py`](as_of_session_cli.py:1) | 历史/手动 as-of 事业会话旁路 | 手动 opt-in 的旁路证明入口；公开 `run_and_archive_session()` 与 CLI `main()`，不切换任何生产默认入口 |
| [`production_as_of_cli.py`](production_as_of_cli.py:1) | G9-P1 as-of 生产目录约定 CLI 别名 | 仅把默认目录对齐当前工作目录下的 `cases/` / `reports/` 并委托 G8 薄层；仍是手动旁路，不代表默认生产入口已切换 |
| [`case_feedback_intake.py`](case_feedback_intake.py:1) | 真实案例反馈语料抽取：原文归档、候选拆分、质量分级、JSONL 输出 | 真实反馈语料迁移 / 抽取辅助；支持 `--dry-run`，非日常反馈入口 |
| [`case_feedback_promote.py`](case_feedback_promote.py:1) | A/B 级真实反馈样本转 case draft | 只生成 `cases/raw_feedback/case_drafts/RF-.../` 待补排盘草稿；不写正式 `cases-index.md` |
| [`case_feedback_repan_index.py`](case_feedback_repan_index.py:1) | 问真排盘补录索引生成器 | 汇总 `case_drafts/RF-.../input.md` 的出生信息与排盘粘贴占位区；支持 `--dry-run` |
| [`cross_domain_consistency_check.py`](cross_domain_consistency_check.py:1) | 历史报告跨维度输出耦合 W9 回溯扫描 | 历史回溯审计辅助；非日常入口 |
| [`materials_intake.py`](materials_intake.py:1) | 教材入库前置闸门：扫 `sources/inbox/*.md` → 归档 `sources/{school}/` + 生成 `theory/raw/{school}/extracted/` 抽取骨架 | 理论材料迁移 / 入库辅助；支持 `--dry-run` |
| [`recompute_wenzhen_case.py`](recompute_wenzhen_case.py:1) | 问真补盘正式 case hard-gated 重算 | 问真补盘修复 / 重算辅助；非默认报告入口 |
| [`build_indexes.py`](build_indexes.py:1) | 构建 / 重建索引 | 迁移与维护场景使用 |
| [`build_multi_school_backtest_report.py`](build_multi_school_backtest_report.py:1) | 生成问真 READY 案例多流派回测报告 | 问真批处理阶段性辅助；非日常反馈入口 |
| [`build_wenzhen_first5_promotion_plan.py`](build_wenzhen_first5_promotion_plan.py:1) | 生成问真首批 5 案转正式 case 的 dry-run 计划 | 问真批处理阶段性辅助；新流程优先使用 READY 批处理链路 |
| [`build_wenzhen_top30_review_pack.py`](build_wenzhen_top30_review_pack.py:1) | 生成问真 Top30 人工 review 包 | 问真 Top30 批处理辅助；非日常主入口 |
| [`build_wenzhen_top30_review_gate.py`](build_wenzhen_top30_review_gate.py:1) | 生成问真 Top30 review gate / OCR 队列 / promotion checklist | 问真 Top30 批处理辅助；用于 OCR 与晋级闸门 |
| [`build_wenzhen_top30_staging_manifest.py`](build_wenzhen_top30_staging_manifest.py:1) | 生成问真 Top30 转正式 case 的 staging manifest | 问真 Top30 批处理辅助；供 promotion preflight / promote 工具读取 |
| [`extract_wenzhen_repan_completed.py`](extract_wenzhen_repan_completed.py:1) | 从排盘补录索引抽取已完成问真排盘 JSONL | 问真排盘补录迁移辅助；非日常反馈入口 |
| [`preflight_wenzhen_staging_promotion.py`](preflight_wenzhen_staging_promotion.py:1) | 转正式 case 前校验问真 staging 候选 | 问真 Top30 批处理辅助；检查冲突、必备字段与目标路径 |
| [`promote_wenzhen_first5_cases.py`](promote_wenzhen_first5_cases.py:1) | 将已批准首批 5 个问真 staging 候选转正式 case | 历史首批迁移辅助；后续批次优先使用 READY 批量工具 |
| [`promote_wenzhen_ready_batch.py`](promote_wenzhen_ready_batch.py:1) | 将问真 READY staging 候选批量转正式 case | 问真 Top30 批处理辅助；运行前需完成 review gate / preflight |
| [`promote_wenzhen_staging_cases.py`](promote_wenzhen_staging_cases.py:1) | 将问真 staging records 转正式 case | 问真批处理迁移辅助；非日常反馈入口 |
| [`sync_wenzhen_repan_index_status.py`](sync_wenzhen_repan_index_status.py:1) | 同步问真排盘拆分索引状态与统计 | 问真补录索引维护辅助 |
| [`promote_wenzhen_pending_analysis_samples.py`](promote_wenzhen_pending_analysis_samples.py:1) | 将问真待分析样本批量初始化为正式 case | 问真批处理迁移辅助；支持 dry-run 与无效干支人工 review 标记 |
| [`fix_wenzhen_invalid_ganzhi.py`](fix_wenzhen_invalid_ganzhi.py:1) | 修复问真样本 OCR 式无效干支字符 | 问真迁移修复辅助；支持 `--dry-run` |
| [`fix_wenzhen_dayun_direction.py`](fix_wenzhen_dayun_direction.py:1) | 修复历史问真转案的大运方向与序列错误 | 默认 dry-run；仅对校准快照严格匹配的历史固定“乾顺坤逆”错误记录执行，`--write` 才改文件 |
| [`normalize_wenzhen_fixed_cases.py`](normalize_wenzhen_fixed_cases.py:1) | 规范化已修复问真无效干支 case | 问真迁移修复辅助；同步结构化四柱/性别/大运字段 |
| [`generate_wenzhen_fixed_reports.py`](generate_wenzhen_fixed_reports.py:1) | 为已修复问真无效干支 case 生成统一报告 | 问真迁移修复辅助；不运行反馈摄入 |
| [`promote_candidate_rules_to_production.py`](promote_candidate_rules_to_production.py:1) | 候选规则迁移为生产规则 | 历史迁移辅助；非日常反馈入口 |
| [`batch_rl_backtest.py`](batch_rl_backtest.py:1) | 批量 RL 回溯训练 | 保留为候选训练/审计入口；不得直接写 production |
| [`export_prediction_model_snapshot.py`](export_prediction_model_snapshot.py:1) | 导出预测模型快照 | 预测模型迁移/审计辅助 |
| [`extract_ditiansui_production_rules.py`](extract_ditiansui_production_rules.py:1) | 抽取滴天髓生产规则 | 理论源迁移辅助 |
| [`extract_ziping_production_rules.py`](extract_ziping_production_rules.py:1) | 抽取子平生产规则 | 理论源迁移辅助 |
| [`historical_mapping_recovery.py`](historical_mapping_recovery.py:1) | 历史映射恢复 | 历史追溯辅助 |

---

## missing · 旧文档曾提及但当前未实现

| 旧工具名 | 当前状态 | 现行替代 / 处理方式 |
|---|---|---|
| `seal_prediction.py` | 仓库当前不存在 | 使用 [`extract_predictions.py`](extract_predictions.py:1) |
| `verify_evidence.py` | 仓库当前不存在 | 使用 [`output_linter.py`](output_linter.py:1) + trace_id 验收测试 |
| `normalize_extracted.py` | 仓库当前不存在 | 理论库迁移已完成；后续如需恢复，应新建专门迁移工具 |
| `score_initial.py` | 仓库当前不存在 | 初始评分已并入规则生命周期 / 置信度契约 |
| `cross_map.py` | 仓库当前不存在 | 使用 [`cross_school_scan.py`](cross_school_scan.py:1)；跨派映射维护见 [`mapping`](../mapping/README.md:1) |

---

## executable registry / status scan

```bash
python tools/tool_registry.py --format markdown
python tools/tool_registry.py --check
python tools/rule_status_scan.py --format markdown
python tools/rule_status_scan.py --check
python tools/parallel_domain_weight_status_scan.py --format markdown
python tools/parallel_domain_weight_status_scan.py --check
python tools/domain_capability_status.py reports/domain-analysis --format markdown
python tools/domain_capability_status.py reports/domain-analysis --check
python -m tools.domain_feedback status --store META/domain-feedback --snapshot reports/domain-analysis/example.run.json
python -m tools.domain_feedback candidates --store META/domain-feedback --snapshot reports/domain-analysis/example.run.json
```

- 工具索引漂移检查以 [`tool_registry.py`](tool_registry.py:1) 为准。
- 规则状态、N_eff、flagged/deprecated 清单以 [`rule_status_scan.py`](rule_status_scan.py:1) 为准；文档只引用扫描结果，不复制长期数字。
- 多专家功能域反馈的跨案例 N_eff、overlay 对账与 pending promotion review 清单以 [`parallel_domain_weight_status_scan.py`](parallel_domain_weight_status_scan.py:1) 为准；这些易漂移结果不得复制到稳定文档。
- 六源三领域的十八槽位 registration/runtime、命题质量与弃权原因以 [`domain_capability_status.py`](domain_capability_status.py:1) 运行时输出为准；不得把扫描数字复制到稳定文档。
- 命题反馈先用 [`domain_feedback.py`](domain_feedback.py:1) 的 `prepare` 生成绑定草稿，再人工填写并用 `ingest` create-only 摄入；`candidates` 仅输出只读人工校准候选，不是 [`conditional_learning.py`](conditional_learning.py:1) 的 apply/promotion 授权。

---

## 学派能力 single-case prospective / blind 隔离

真实命令以 [`school_capability_dataset.py`](school_capability_dataset.py:1294)、[`school_capability_prospective.py`](school_capability_prospective.py:414) 与 [`school_capability_cohort.py`](school_capability_cohort.py:304) 的 parser 为准。所有写操作先 dry-run，人工确认后才正式执行；下列命令仅离线评估，`production_switch=false`。

```bat
python -m tools.school_capability_dataset single-case-intake --input <input.md路径> --tasks META/prospective-go-task-catalog-v1.json --school ziping --school ditiansui --school duan --school ren --school gao --school yang --operator human-intake-01 --tasks-by-case META/prospective-go/prospective-go-b01-tasks-by-case.json --future-question <future-question草稿路径> --case-root META/prospective-go/single-cases --created-at <真实UTC时间> --dry-run
python -m tools.school_capability_dataset prepare-single-case-blind --intake <单案intake路径> --future-question <future-question-registration路径> --tasks META/prospective-go-task-catalog-v1.json --rule-snapshot META/prospective-go-rule-snapshot-v1.json --target-dir <单案blind-bundle路径> --dry-run
python -m tools.school_capability_prospective stage-single-case-frozen-run --bundle-root <单案blind-bundle路径> --out <单案frozen-run路径> --dry-run
python -m tools.school_capability_prospective migrate-single-case-parent-chain-v002 --input <input.md路径> --tasks META/prospective-go-task-catalog-v1.json --rule-snapshot META/prospective-go-rule-snapshot-v1.json --tasks-by-case META/prospective-go/prospective-go-b01-tasks-by-case.json --future-question <v002问题草稿路径> --case-root META/prospective-go/single-cases --operator <操作人> --approved-by <批准人> --reason <批准理由> --dry-run
```

正式最小链在 immutable frozen result 落盘并通过 hash / 父链校验后即可接收反馈或待核验结果：

```bat
python -m tools.school_capability_dataset issue-feedback-release --frozen-run <单案frozen-run路径> --created-at <真实UTC时间> --out <单案feedback-release路径> --dry-run
```

独立人类 witness / verification 仅为可选审计与历史兼容入口，不是反馈前置条件。若选择使用，以下占位符只能替换路径、时间和仓库外 registry root，绝不能放 key；agent 不读取、请求、记录或展示真实值：

```bat
set "SCHOOL_CAPABILITY_WITNESS_KEY="
rem 独立人类见证人现在亲自在此临时终端输入真实值；agent 离开屏幕且不接收该值。
python -m tools.school_capability_prospective witness-freeze-chain --intake <单案正式intake路径> --bundle-root <单案blind-bundle路径> --staged-run <单案frozen-run路径> --out <单案witness路径> --witness-key-env SCHOOL_CAPABILITY_WITNESS_KEY --dry-run
python -m tools.school_capability_prospective witness-freeze-chain --intake <单案正式intake路径> --bundle-root <单案blind-bundle路径> --staged-run <单案frozen-run路径> --out <单案witness路径> --witness-key-env SCHOOL_CAPABILITY_WITNESS_KEY
python -m tools.school_capability_dataset witness-verify-single-case --intake <单案正式intake路径> --bundle-root <单案blind-bundle路径> --frozen-run <单案frozen-run路径> --registry <单案witness路径> --external-root <见证方仓库外保存的root> --verifier human-witness-01 --verified-at <真实UTC时间> --out <单案verification路径> --witness-key-env SCHOOL_CAPABILITY_WITNESS_KEY --dry-run
python -m tools.school_capability_dataset witness-verify-single-case --intake <单案正式intake路径> --bundle-root <单案blind-bundle路径> --frozen-run <单案frozen-run路径> --registry <单案witness路径> --external-root <见证方仓库外保存的root> --verifier human-witness-01 --verified-at <真实UTC时间> --out <单案verification路径> --witness-key-env SCHOOL_CAPABILITY_WITNESS_KEY
set "SCHOOL_CAPABILITY_WITNESS_KEY="
python -c "import os; print('SET' if os.environ.get('SCHOOL_CAPABILITY_WITNESS_KEY') else 'NOT SET')"
```

`issue-feedback-release` 当前推荐直接消费 immutable frozen result；随后可使用 `release-immediate-retrospective-template`、`collect-immediate-retrospective` 接收 / 登记结果。旧 verification 参数仍兼容，但只用于已有链和可选审计。到期未来账使用 `collect-future-observation`，完成链使用 `build-case-completion`。每 10 个回顾完成案使用以下真实 cohort 子命令，只引用父制品：

```bat
python -m tools.school_capability_cohort build --completion <完成制品路径> --historical-md META/six-month-platform-gate-2026-07-15.md --historical-json META/six-month-platform-gate-2026-07-15.json --out-dir META/prospective-go/cohorts --dry-run
python -m tools.school_capability_cohort gate --manifest <cohort-manifest路径> --scores <即时评分路径> --holdout <即时留出路径> --audit <即时审计路径> --out <prediction-capability-candidate-gate-v1.json路径> --dry-run
python -m tools.school_capability_cohort future-gate --manifest <cohort-manifest路径> --scores <未来评分路径> --holdout <未来留出路径> --audit <未来审计路径> --out <future-empirical-gate-v1.json路径> --dry-run
python -m tools.school_capability_cohort report --immediate-gate <即时门禁路径> --future-gate <未来门禁路径> --historical-json META/six-month-platform-gate-2026-07-15.json --out <three-gate-report-v1.md路径> --dry-run
```

- `prospective-intake` 的输入只能是名为 `input.md` 的普通文件；case ID 取父目录名，禁止重复 case、未知 task、symlink，以及路径、内容或 JSON 字段中的 feedback / labels / report / known facts 标记。现有 tasks-by-case 文件可以继续使用 `P-GO-2026-NNN` 短槽位；CLI 只在唯一匹配时将其解析为完整 `P-GO-2026-NNN-{乾/坤}-{四柱}` case ID，无需生成改写版任务文件，零匹配或多匹配都会拒绝。
- `prepare-blind` 使用显式白名单生成全新目录。安全白名单为 `intake.json`、`tasks.json`、`rule-snapshot.json`、`bundle-manifest.json` 与 `cases/<case_id>/chart.json`；同目录中的 `input.md`、feedback、labels、report、known facts 或其他文件不会进入 bundle。
- `stage-frozen-run` 只消费已校验盲包，保留六来源全部 `claim / abstain / unsupported`，并把任务目录及规则快照的内容 hash 绑定到冻结制品。
- `witness-freeze-chain` 一次为每案安全生成或向既有 registry 追加完整 `registered → prepared → freeze` 三事件段；追加时用 `--registry` 指向既有 registry，并把 `--out` 指向全新路径，不覆盖旧制品。该流程不创建 reveal 事件；HMAC key 只从 `--witness-key-env` 指定的环境变量读取，不得写入命令参数、文件或仓库。
- manifest 记录内容 SHA-256；bundle hash 只由白名单文件的相对路径和内容 hash 决定，因此不受时间、源目录或目标目录影响。
- 源文件及其路径链、目标路径链均拒绝 symlink；目标目录或输出文件必须不存在。所有写命令先执行 `--dry-run`；dry-run 只打印计划或制品 JSON，不创建输出。真实数据未到时状态仍为 HOLD，不创建空 intake、空盲包、空 frozen run 或空 witness registry。

### 受信独立见证边界（Witness HMAC 可选审计）

- witness HMAC 不参与最小反馈门槛；仅在选择增强审计时，由独立 key holder 保管密钥并签署事件。
- 本地完整性模型用于发现未持有 witness key 的本地篡改；**密钥泄漏**或**恶意见证**不在本地完整性模型覆盖范围内。
- witness registry 的 `registry root` 应由见证方做**外部备份**或锚定，以便发现本地 registry 被替换或回滚。
- 该机制提供可验证的职责分离与篡改证据，不是无限防恶意管理员；同时控制本地系统、witness key 与外部 registry root 的管理员超出此模型的安全假设。

---

## dry-run 约定

并非所有历史工具都支持 dry-run。新工具若会修改 [`cases`](../cases/README.md:1)、[`META`](../META/INDEX.md:1)、[`theory`](../theory/README.md:1) 或 [`predictions`](../predictions/README.md:1)，应优先提供 `dry_run` / `--dry-run` 入口；若不支持，必须在工具 docstring 中明确说明。
