# handoff · 短期下一步

> 本文件只服务当前/下一次 session 的短期交接，不作为版本、规则数量、N_eff、flagged/deprecated 清单的长期事实源。长期入口见 [`AGENTS.md`](AGENTS.md)，稳定状态见 [`STATUS.md`](STATUS.md)，机器状态见 [`META/project-state.json`](META/project-state.json)。

---

## 0. 最新交接 · 多流派并行功能域与裁判模型

> 更新时间：2026-06-08。此节优先级高于下方旧的问真转案短期交接；下方内容保留为历史上下文，除非用户明确要求继续问真转案，否则下一位 agent 应先接续本节。

### 0.1 本轮已完成

本轮根据“多流派并行功能域分析与裁判模型”方案，采用最小补丁方式对现有 v1.5 旁路实现做了加固，没有从零重建模型，也没有覆盖既有契约。

已完成改动：

- 加固 [`run_parallel_domain_analysis()`](engine/application/parallel_domain_runner.py)：每个 analyzer 调用都会拿到独立 [`DomainAnalysisContext`](engine/application/domain_analyzers.py) 副本，避免共享 `base_context` 污染。
- 加固异常隔离：单个 analyzer 抛异常时，runner 会转成显式 abstain reading，不影响同域其他专家或后续领域。
- 扩展 [`DomainAnalyzer`](engine/application/domain_analyzers.py)：新增 `is_wired()` 协议，并在 [`DomainAnalyzerRegistry`](engine/application/domain_analyzers.py) 上提供 wiring 状态查询。
- 新增模块级 [`get_wiring_status()`](engine/application/domain_analyzers.py)，返回默认 6 域 × 3 专家体系的 `wired` / `abstain_only` 状态。
- 扩展 [`tools/feedback_ingest.py`](tools/feedback_ingest.py)：新增 parallel-domain statement 反馈 fanout，到 reading / adjudication 级 JSONL 日志。
- 新增日志目标：[`engine/logs/expert_domain_feedback.jsonl`](engine/logs/expert_domain_feedback.jsonl) 与 [`engine/logs/adjudication_accuracy.jsonl`](engine/logs/adjudication_accuracy.jsonl)。这两个文件按需追加生成；当前不要求已存在。
- 新增 [`get_expert_domain_stats()`](tools/feedback_ingest.py) 聚合 expert × domain 命中 / 失验、`n_eff`、Beta mean、Wilson lower bound。
- 新增 [`compute_weight_update_proposal()`](tools/feedback_ingest.py) 生成动态权重调整提案；只返回 proposal，不自动修改任何 YAML 权重源。
- 扩展测试：[`tests/test_parallel_domain_runner.py`](tests/test_parallel_domain_runner.py) 与 [`tests/v1_3_acceptance/test_h3_feedback_parsing.py`](tests/v1_3_acceptance/test_h3_feedback_parsing.py)。

验证已通过：

```bash
python -m pytest tests/test_parallel_domain_runner.py tests/v1_3_acceptance/test_h3_feedback_parsing.py -q
```

结果：`13 passed in 0.27s`。

### 0.2 本轮触碰文件

- [`engine/application/parallel_domain_runner.py`](engine/application/parallel_domain_runner.py)
- [`engine/application/domain_analyzers.py`](engine/application/domain_analyzers.py)
- [`tools/feedback_ingest.py`](tools/feedback_ingest.py)
- [`tests/test_parallel_domain_runner.py`](tests/test_parallel_domain_runner.py)
- [`tests/v1_3_acceptance/test_h3_feedback_parsing.py`](tests/v1_3_acceptance/test_h3_feedback_parsing.py)
- [`handoff.md`](handoff.md)

未触碰：

- [`engine/application/pipeline_runner.py`](engine/application/pipeline_runner.py)
- [`engine/energy/`](engine/energy/)
- [`engine/picture/`](engine/picture/)
- [`engine/yingqi/`](engine/yingqi/)
- [`engine/pangzheng/`](engine/pangzheng/)

### 0.3 下一位 agent 应继续做什么

用户会把完整计划和执行方案一起发给下一位 agent。下一位 agent 不要按“从零创建阶段 1-A / 1-B”执行，因为当前仓库已经存在并行域模型、runner、orchestrator、adjudication、statement index 与测试骨架。

建议下一步按以下顺序继续：

1. 先读取 [`META/project-state.json`](META/project-state.json)、[`engine/domain/parallel.py`](engine/domain/parallel.py)、[`engine/application/adjudication.py`](engine/application/adjudication.py)、[`engine/application/domain_analyzers.py`](engine/application/domain_analyzers.py)、[`engine/application/parallel_domain_runner.py`](engine/application/parallel_domain_runner.py)、[`tools/feedback_ingest.py`](tools/feedback_ingest.py)。
2. 运行一次最小验证：`python -m pytest tests/test_parallel_domain_runner.py tests/v1_3_acceptance/test_h3_feedback_parsing.py -q`。
3. 继续补动态权重闭环的“读取/应用 proposal”层：可以新增人工确认后的 `apply_weight_update_proposal()`，但必须保持默认不自动写权重。
4. 若要接入裁判实时权重，优先在 [`engine/application/adjudication.py`](engine/application/adjudication.py) 支持可注入 feedback overlay / `WeightProfile`，不要替换现有 review draft prior profile。
5. 扩展测试覆盖：proposal 应用前后权重归一化、`n_eff < 5` 只警告不调整、`n_eff >= 10` 才允许较大调整、连续 miss 触发降权 proposal。
6. 如需面向 CLI 暴露统计，可以考虑给 [`tools/feedback_ingest.py`](tools/feedback_ingest.py) 增加只读参数，例如 `--expert-domain-stats` / `--weight-proposal`；不要默认在 ingest 后自动改权重。
7. 最后再考虑是否更新 [`META/project-state.json`](META/project-state.json) 中 `v1_5_status.dynamic_feedback_weighting`；只有当 proposal + 人工应用 + 测试闭环都完成后，才可从 `pending` 改为更准确状态。

### 0.4 下一位 agent 必须遵守的约束

- 不要覆盖 [`engine/domain/parallel.py`](engine/domain/parallel.py)；只能做兼容性增补。
- 内部专家枚举继续使用 `blind` / `ziping` / `tiaohou_ditiansui`，中文只在报告层展示。
- 功能域继续使用现有 `财运` / `事业` / `婚姻` / `健康` / `性格` / `学业`。
- 不要修改 [`engine/application/pipeline_runner.py`](engine/application/pipeline_runner.py)。
- 不要修改 D1-D4 核心目录：[`engine/energy/`](engine/energy/)、[`engine/picture/`](engine/picture/)、[`engine/yingqi/`](engine/yingqi/)、[`engine/pangzheng/`](engine/pangzheng/)。
- 不要让任一专家 analyzer 读取其他专家中间态；跨专家信息只能通过 [`ExpertReading`](engine/domain/parallel.py) 进入裁判。
- 动态权重默认只产出 proposal 和日志；未经人工确认，不得自动改 prior profile 或 YAML 权重文件。

### 0.5 可直接发给下一位 agent 的开场指令

```text
请先读取 handoff.md 的“0. 最新交接 · 多流派并行功能域与裁判模型”。我会把完整计划和执行方案一并发给你，但不要按从零创建文件执行；当前仓库已存在 v1.5 并行域模型、runner、orchestrator、adjudication、statement index 与测试骨架。请在现有实现基础上继续最小补丁：先复跑 python -m pytest tests/test_parallel_domain_runner.py tests/v1_3_acceptance/test_h3_feedback_parsing.py -q，然后继续补动态反馈权重闭环的 proposal 应用与测试。不要修改 engine/application/pipeline_runner.py，不要修改 D1-D4 核心目录，不要自动改权重 YAML。
```

---

## 1. 当前工作状态

本轮围绕问真 APP 补录排盘样本，已经完成从“已补完整排盘识别”到“首批正式转案 dry-run 方案”的非破坏性流水线。当前没有创建新的正式 [`cases/`](cases/) 下 `C-...` 案例目录；所有产物仍停留在 [`cases/raw_feedback/parsed/`](cases/raw_feedback/parsed/) 与 [`tools/`](tools/) 的审阅、候选、预检、计划层。

核心结论：

- 已从男女优先索引抽取 98 个完整问真排盘样本。
- 已生成 Top30 人工审阅包。
- Top30 中 4 个因 OCR / 干支异常进入阻塞队列。
- 26 个非阻塞候选已进入 staging manifest。
- 26 个 staging 候选通过 promotion preflight，状态均为 READY。
- 已生成首批 5 个 READY 候选的正式转案 dry-run 计划。
- 下一步必须先人工确认首批 5 案转案方案，再创建正式 case 目录并逐案运行 preflight。

---

## 2. 本轮已完成产物

### 2.1 索引同步与完整样本抽取

已完成问真排盘 split index 的状态同步与完整样本抽取，相关工具与产物：

- [`tools/sync_wenzhen_repan_index_status.py`](tools/sync_wenzhen_repan_index_status.py)：同步导航页、男命优先索引、女命优先索引的状态与统计。
- [`tools/extract_wenzhen_repan_completed.py`](tools/extract_wenzhen_repan_completed.py)：从 split indexes 抽取完整排盘样本。
- [`cases/raw_feedback/parsed/wenzhen_repan_completed.jsonl`](cases/raw_feedback/parsed/wenzhen_repan_completed.jsonl)：98 条完整排盘结构化记录。
- [`cases/raw_feedback/parsed/wenzhen_repan_completed-summary.json`](cases/raw_feedback/parsed/wenzhen_repan_completed-summary.json)：抽取汇总。
- [`cases/raw_feedback/parsed/wenzhen_repan_top30.md`](cases/raw_feedback/parsed/wenzhen_repan_top30.md)：初版 Top30 候选列表。

关键结果：

- 完整样本数：98。
- 性别分布：男 59、女 39。
- 质量分布：A 1、B 97。
- 干支异常标记：10 条，主要来自 OCR 字符，如“王”疑似“壬”、“西”疑似“酉”。

### 2.2 Top30 人工审阅包

已生成 Top30 人工审阅包，用于命理师逐案核对排盘、事实与原始反馈摘录：

- [`tools/build_wenzhen_top30_review_pack.py`](tools/build_wenzhen_top30_review_pack.py)：生成 Top30 审阅包。
- [`cases/raw_feedback/parsed/wenzhen_repan_top30_review.md`](cases/raw_feedback/parsed/wenzhen_repan_top30_review.md)：Top30 人工审阅 Markdown 包。
- [`cases/raw_feedback/parsed/wenzhen_repan_top30_review-summary.json`](cases/raw_feedback/parsed/wenzhen_repan_top30_review-summary.json)：审阅包摘要。

验证结果：

- 审阅 section：30。
- 表格记录：30。
- 人工 checklist：30。
- 缺失 draft：0。
- 事件数不一致：0。
- review flags：`invalid_ganzhi_chars=3`、`ocr_wang_for_ren=3`、`ocr_xi_for_you=2`。

### 2.3 OCR 阻塞队列与 promotion checklist

已对 Top30 进行 review gate 分流：

- [`tools/build_wenzhen_top30_review_gate.py`](tools/build_wenzhen_top30_review_gate.py)：生成 OCR 阻塞队列与 promotion checklist。
- [`cases/raw_feedback/parsed/wenzhen_repan_top30_ocr_queue.md`](cases/raw_feedback/parsed/wenzhen_repan_top30_ocr_queue.md)：需要先人工校正的 OCR / 干支异常队列。
- [`cases/raw_feedback/parsed/wenzhen_repan_top30_promotion_checklist.md`](cases/raw_feedback/parsed/wenzhen_repan_top30_promotion_checklist.md)：26 个非阻塞候选的转案准备清单。
- [`cases/raw_feedback/parsed/wenzhen_repan_top30_review_gate-summary.json`](cases/raw_feedback/parsed/wenzhen_repan_top30_review_gate-summary.json)：分流摘要。

阻塞 raw_id：

- `RF-2026-000771`
- `RF-2026-000551`
- `RF-2026-000894`
- `RF-2026-000684`

验证结果：

- OCR queue：4。
- Promotion candidates：26。
- Top30 总数一致：30。
- OCR 队列与 promotion checklist 未重复、未遗漏。

### 2.4 Staging manifest

已把 26 个非阻塞候选转成机器可读 staging manifest：

- [`tools/build_wenzhen_top30_staging_manifest.py`](tools/build_wenzhen_top30_staging_manifest.py)：生成 staging manifest。
- [`cases/raw_feedback/parsed/wenzhen_repan_top30_staging_manifest.jsonl`](cases/raw_feedback/parsed/wenzhen_repan_top30_staging_manifest.jsonl)：26 行 staging JSONL。
- [`cases/raw_feedback/parsed/wenzhen_repan_top30_staging_manifest-summary.json`](cases/raw_feedback/parsed/wenzhen_repan_top30_staging_manifest-summary.json)：staging 摘要。
- [`cases/raw_feedback/parsed/wenzhen_repan_top30_staging_manifest.md`](cases/raw_feedback/parsed/wenzhen_repan_top30_staging_manifest.md)：人工可读 staging index。

验证结果：

- JSONL rows：26。
- Markdown table rows：26。
- required fields 缺失：0。
- blocking flags inside staging：0。
- 所有候选状态均为 `staged_pending_human_review`。

### 2.5 Promotion preflight

已对 26 个 staging 候选执行正式转案前预检：

- [`tools/preflight_wenzhen_staging_promotion.py`](tools/preflight_wenzhen_staging_promotion.py)：检查 suggested case id、draft 来源、字段完整性、事件数、四柱格式、目标目录冲突。
- [`cases/raw_feedback/parsed/wenzhen_repan_top30_promotion_preflight.md`](cases/raw_feedback/parsed/wenzhen_repan_top30_promotion_preflight.md)：preflight 报告。
- [`cases/raw_feedback/parsed/wenzhen_repan_top30_promotion_preflight-summary.json`](cases/raw_feedback/parsed/wenzhen_repan_top30_promotion_preflight-summary.json)：preflight 摘要。

验证结果：

- Candidate count：26。
- READY：26。
- BLOCKED：0。
- Errors：0。
- Warnings：0。
- 与 staging manifest 数量一致。

### 2.6 首批 5 案 dry-run 转案计划

已为前 5 个 READY 候选生成正式转案 dry-run 方案：

- [`tools/build_wenzhen_first5_promotion_plan.py`](tools/build_wenzhen_first5_promotion_plan.py)：生成首批 5 案 dry-run 转案方案。
- [`cases/raw_feedback/parsed/wenzhen_repan_first5_promotion_plan.json`](cases/raw_feedback/parsed/wenzhen_repan_first5_promotion_plan.json)：结构化转案计划。
- [`cases/raw_feedback/parsed/wenzhen_repan_first5_promotion_plan.md`](cases/raw_feedback/parsed/wenzhen_repan_first5_promotion_plan.md)：人工可读转案计划。

首批 raw_id：

- `RF-2026-000345`
- `RF-2026-000441`
- `RF-2026-000864`
- `RF-2026-000243`
- `RF-2026-000524`

验证结果：

- Plan count：5。
- Markdown case sections：5。
- Markdown table rows：5。
- 每案目标文件数：4。
- 目标正式目录尚未创建，检查结果为空列表。

---

## 3. 当前硬性约束

后续 agent 必须遵守：

1. 不得把 [`cases/raw_feedback/parsed/`](cases/raw_feedback/parsed/) 中的候选样本直接当作正式案例使用。
2. 不得在未获得人工确认前创建新的 [`cases/`](cases/) 下 `C-...` 正式目录。
3. 阻塞队列中的 4 个 raw_id 必须先人工校正 OCR / 干支，再重新走 gate、staging、preflight。
4. 正式转案时每个 case 目录至少需要生成：`input.md`、`analysis.md`、`feedback.md`、`statement_index.json`。
5. 每个正式 case 的 `input.md` 创建后，必须运行 `python -m tools.preflight cases/<case_id>/input.md`。
6. 每个正式 case 必须保留 raw_id、source index path、draft path、staging manifest path，方便后续反馈摄入追踪。
7. 本轮所有工具均为非破坏性工具，不应自动修改正式 case 目录。

---

## 4. 下一步推荐执行顺序

### 4.1 人工确认首批 5 案

先打开并核对：

- [`cases/raw_feedback/parsed/wenzhen_repan_first5_promotion_plan.md`](cases/raw_feedback/parsed/wenzhen_repan_first5_promotion_plan.md)
- [`cases/raw_feedback/parsed/wenzhen_repan_first5_promotion_plan.json`](cases/raw_feedback/parsed/wenzhen_repan_first5_promotion_plan.json)

需要确认：

- suggested case id 是否接受。
- 四柱与问真原文是否一致。
- birth fields 是否足够生成正式 `input.md`。
- known facts 是否可迁移到正式 `feedback.md`。
- 是否允许创建对应正式目录。

### 4.2 创建首批 5 个正式 case

人工确认后，再创建 5 个正式目录。每案按 dry-run plan 生成：

- `input.md`：来自 staging 排盘、birth 字段与原 draft known_facts。
- `analysis.md`：记录来源、转案说明、待正式分析占位。
- `feedback.md`：迁移已知事实，并保留 raw_id 追踪。
- `statement_index.json`：初始化 statement 追踪骨架。

创建后逐案运行：

```bash
python -m tools.preflight cases/<case_id>/input.md
```

### 4.3 通过首批 5 案后再批量推进

若首批 5 案通过正式 preflight：

1. 复用相同模板与字段映射。
2. 继续处理剩余 21 个 READY staging 候选。
3. 每批建议 5-10 个，不建议一次性创建 26 个。
4. 每批完成后更新对应 review / staging / preflight 记录。

### 4.4 单独处理 OCR 阻塞队列

阻塞 raw_id 不应混入首批转案：

- `RF-2026-000771`
- `RF-2026-000551`
- `RF-2026-000894`
- `RF-2026-000684`

处理顺序：

1. 打开 [`cases/raw_feedback/parsed/wenzhen_repan_top30_ocr_queue.md`](cases/raw_feedback/parsed/wenzhen_repan_top30_ocr_queue.md)。
2. 人工核对问真截图 / 原文中“王”“西”等 OCR 可疑字。
3. 修正源 draft 或索引中的排盘文本。
4. 重新运行 review gate、staging manifest、promotion preflight。
5. 只有通过 preflight 后才进入正式转案。

---

## 5. 建议给下一 agent 的开场指令

可直接复制以下指令给新 agent：

```text
请读取 handoff.md，并继续问真排盘 Top30 转正式案例流程。当前已经完成 Top30 review、OCR gate、26 个 staging 候选、promotion preflight，以及首批 5 案 dry-run promotion plan。不要直接创建全部正式 cases；先读取 cases/raw_feedback/parsed/wenzhen_repan_first5_promotion_plan.md 与 .json，按计划创建首批 5 个正式 case 目录，每案生成 input.md、analysis.md、feedback.md、statement_index.json，并逐案运行 python -m tools.preflight cases/<case_id>/input.md。不要处理 OCR 阻塞队列，除非我明确要求修 OCR。
```

---

## 6. 快速核验命令

如需复核当前状态，可运行：

```bash
python tools/build_wenzhen_top30_review_pack.py --dry-run
python tools/build_wenzhen_top30_review_gate.py --dry-run
python tools/build_wenzhen_top30_staging_manifest.py --dry-run
python tools/preflight_wenzhen_staging_promotion.py --dry-run
python tools/build_wenzhen_first5_promotion_plan.py --dry-run
```

如需重建非破坏性产物，可去掉 `--dry-run`。重建这些产物不会创建正式 [`cases/`](cases/) 下的 `C-...` 目录。

---

## 7. 禁止误用提醒

- 不要从 [`handoff.md`](handoff.md) 推断长期版本状态；版本看 [`VERSION`](VERSION)，机器状态看 [`META/project-state.json`](META/project-state.json)。
- 不要把 `current_phase` 当产品版本。
- 不要使用 deprecated 的 [`tools/calibrate.py`](tools/calibrate.py) 作为新反馈入口。
- 不要只生成报告或分析而不归档 case；正式案例必须能被后续 [`tools/feedback_ingest.py`](tools/feedback_ingest.py) / [`tools/feedback_loop.py`](tools/feedback_loop.py) 追踪。
- 不要在报告标题或 case id 中遗漏乾/坤。
