# handoff · 短期下一步

> 本文件只服务当前/下一次 session 的短期交接，不作为版本、规则数量、N_eff、flagged/deprecated 清单的长期事实源。长期入口见 [`AGENTS.md`](AGENTS.md)，稳定状态见 [`STATUS.md`](STATUS.md)，机器状态见 [`META/project-state.json`](META/project-state.json)。

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
