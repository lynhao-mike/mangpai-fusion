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
| [`render_report.py`](render_report.py:1) | 渲染 C-2026-025 唯一标准报告 | 固定使用 `templates/report-v1.3.md`，由 output_linter 兜底 |
| [`output_linter.py`](output_linter.py:1) | 报告出口 lint / 禁越界输出 | 兜底护栏 #2 |
| [`three_layer_check.py`](three_layer_check.py:1) | 应期三层门检查 | v1.2 W3 护栏 |
| [`feedback_ingest.py`](feedback_ingest.py:1) | 结构化反馈摄入：`[y]` / `[n]` / `[?]` / `[skip]` | v1.3 推荐反馈入口 |
| [`feedback_review_gate.py`](feedback_review_gate.py:1) | 反馈复核包摄入前置闸门 | 只读检查 `META/feedback-closure-review-pack-*.json` 是否已完成人工裁决 |
| [`feedback_impact_report.py`](feedback_impact_report.py:1) | 反馈影响路径与置信度调整可视化 | dry-run 计算断语→规则→置信度变化，输出 Markdown + Mermaid |
| [`late_feedback.py`](late_feedback.py:1) | 应期延迟反馈：±1 年窗口 | v1.3 D7 |
| [`boundary_miner.py`](boundary_miner.py:1) | ≥5 miss 后自动挖候选边界 | v1.3 D3 |
| [`veto_miner.py`](veto_miner.py:1) | 候选否决兜底：低后验 + 无边界 → review | v1.3 D4 |
| [`iteration_report.py`](iteration_report.py:1) | 每 10 完成反馈案产出迭代报告 | v1.3 D8 |
| [`cross_school_scan.py`](cross_school_scan.py:1) | 每 10 案跨派一致性扫描 | v1.3 自迭代 |
| [`cross_domain_consistency_check.py`](cross_domain_consistency_check.py:1) | 历史报告跨维度输出耦合 W9 回溯扫描 | v1.4 V8 / CFL-C015-002 |
| [`extract_predictions.py`](extract_predictions.py:1) | 抽取 ★4+ 应期到 predictions/ | 预测封存现行入口 |
| [`timing_report.py`](timing_report.py:1) | 聚合 pipeline、batch、feedback、iteration timing.json | v1.2.1+ metrics；同时扫描 `cases/*/findings/timing.json` 与 `META/timings/*.json` |
| [`production_api.py`](production_api.py:1) | 生产 MVP HTTP JSON API | stdlib 同步 API；封装分析提交、状态查询、SQLite 元数据与缓存；高并发场景后续演进为 job queue |
| [`tool_registry.py`](tool_registry.py:1) | 扫描 tools/*.py 并生成可执行工具注册表 | 防止 README 与真实工具漂移 |
| [`rule_status_scan.py`](rule_status_scan.py:1) | 扫描 theory/*/index.yaml 的规则状态分布、N_eff、review 清单 | 易漂移规则状态的机器真相源 |
| [`materials_intake.py`](materials_intake.py:1) | 教材入库前置闸门：扫 `sources/inbox/*.md` → 归档 `sources/{school}/` + 生成 `theory/raw/{school}/extracted/` 抽取骨架 | 多派别 Markdown 教材入口；支持 `--dry-run` |
| [`case_feedback_intake.py`](case_feedback_intake.py:1) | 真实案例反馈语料抽取：原文归档、候选拆分、质量分级、JSONL 输出 | 处理 `cases/实战案例反馈990个案例_part*.md`；支持 `--dry-run` |
| [`recompute_wenzhen_case.py`](recompute_wenzhen_case.py:1) | 问真补盘正式 case hard-gated 重算 | 运行严格 pipeline，校验 `statement_index.json`，产出 school verdict / conclusion diff / confidence delta / feedback binding 检查 |
| [`case_feedback_promote.py`](case_feedback_promote.py:1) | A/B 级真实反馈样本转 case draft | 只生成 `cases/raw_feedback/case_drafts/RF-.../` 待补排盘草稿；不写正式 `cases-index.md` |
| [`case_feedback_repan_index.py`](case_feedback_repan_index.py:1) | 问真排盘补录索引生成器 | 汇总 `case_drafts/RF-.../input.md` 的出生信息与排盘粘贴占位区；支持 `--dry-run` |
| [`event_archive.py`](event_archive.py:1) | 交互事件增量归档：把一次询问、分析、结果追加到报告侧 events 或 META 专项记录 | 处理后归档入口；case 可定位时写 `reports/*-events.md`，否则写 `META/session-events.md` |

---

## 调用边界

- [`tools/`](README.md:1) 作为 CLI / adapter 层：负责文件入口、人工日志、批处理与审计落盘。
- 当前 D1-D4 核心编排优先查看 [`engine/application/pipeline_runner.py`](../engine/application/pipeline_runner.py:1)，生产同步封装查看 [`engine/application/production_service.py`](../engine/application/production_service.py:1)。
- 新代码不应把 [`engine/application`](../engine/application:1) 继续扩大为依赖 [`tools/`](README.md:1) 的工具集合；涉及长期 API / queue / storage 时应下沉到 application / infrastructure 层。

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

---

## deprecated · 历史入口，默认禁用

| 工具 | 状态 | 替代方案 |
|---|---|---|
| [`calibrate.py`](calibrate.py:1) | **deprecated v1.3.0+**；v1.0 反馈入口，字段名 / 状态机与 v1.2+ 不兼容，默认 guard 退出 | 用 [`feedback_ingest.py`](feedback_ingest.py:1) + [`feedback_loop.py`](feedback_loop.py:1) |

---

## historical · 历史/迁移辅助

| 工具 | 用途 | 说明 |
|---|---|---|
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
| [`normalize_wenzhen_fixed_cases.py`](normalize_wenzhen_fixed_cases.py:1) | 规范化已修复问真无效干支 case | 问真迁移修复辅助；同步结构化四柱/性别/大运字段 |
| [`generate_wenzhen_fixed_reports.py`](generate_wenzhen_fixed_reports.py:1) | 为已修复问真无效干支 case 生成统一报告 | 问真迁移修复辅助；不运行反馈摄入 |
| [`promote_candidate_rules_to_production.py`](promote_candidate_rules_to_production.py:1) | 候选规则迁移为生产规则 | 历史迁移辅助；非日常反馈入口 |

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
```

- 工具索引漂移检查以 [`tool_registry.py`](tool_registry.py:1) 为准。
- 规则状态、N_eff、flagged/deprecated 清单以 [`rule_status_scan.py`](rule_status_scan.py:1) 为准；文档只引用扫描结果，不复制长期数字。

---

## dry-run 约定

并非所有历史工具都支持 dry-run。新工具若会修改 [`cases`](../cases/README.md:1)、[`META`](../META/INDEX.md:1)、[`theory`](../theory/README.md:1) 或 [`predictions`](../predictions/README.md:1)，应优先提供 `dry_run` / `--dry-run` 入口；若不支持，必须在工具 docstring 中明确说明。
