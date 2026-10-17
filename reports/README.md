# reports/ · 正式报告归档

每个案例分析完成后，默认生成 `C-YYYY-NNN-{乾/坤}-{四柱}-human-report.md` 人话主报告文件。

报告格式以 [`../templates/report-v7-human.md`](../templates/report-v7-human.md) 为当前渲染入口基线，产物定位为**命主可读的人话主报告**。

**强制约束**：
- 每个 `cases/C-YYYY-NNN-{乾/坤}-{四柱}/` 必须对应 `reports/C-YYYY-NNN-{乾/坤}-{四柱}-human-report.md`
- 报告标题必须标注性别命式（乾/坤），格式如：`# 八字命理分析报告 · C-YYYY-NNN-乾-四柱 · 乾`
- 新分析默认只产 **v7 单一人话主报告**；不得生成第三份重复结论的变体（如客户版、对外版）
- 历史存量 `*-analyst-report.md`（v6 内部稿）**保留兼容，不强制迁移、不删除**；新分析不再要求 v6/v7 两份同 commit 提交。若某案例另需机器可解析产物，按需单独生成并在《我不编的》声明
- 归档前必须通过 `python -m tools.human_touch_linter <file>` 零 ERROR
- `statement_index.json` 必须使用 C-2026-025 的 `statements` 列表结构
- 案例绑定的临时问答 / 专项分析 / 处理结果归档到 `reports/C-YYYY-NNN-{乾/坤}-{四柱}-events.md`
- 正式报告的「归档信息」必须挂载对应 `*-events.md` 与 `cases/*/events.md` 的可点击链接
- 报告侧 `*-events.md` 必须挂载对应 `cases/*/analysis.md` 的可点击链接；对应 `analysis.md` 的「归档信息」必须反向挂载 `reports/*-events.md`
- `cases/C-YYYY-NNN-{乾/坤}-{四柱}/events.md` 保留为「命理分析过程记录」，不存放临时问答原文
- v6 预生产渲染会在报告旁路生成 `*.v5.json`（兼容结构化输出）与 `*.run.json`（run snapshot，可校验 `output_hash`），二者均为报告派生结构化产物，不替代 `cases/*/input.md` / `feedback.md` / `statement_index.json`

---

## v7 人话报告标准（新分析默认唯一主产物）

新案例或新分析默认按 [`../templates/report-v7-human.md`](../templates/report-v7-human.md) 生成**一份** `*-human-report.md：前六节直接说人话，地址 / 边号 / 理论条目收拢到节末简注与文末《附：关键依据索引与可核验断语表》。**不再重复生成「内部表格稿 + 人话稿」双文件**——该模式是 Token 翻倍与结论不一致的根因，已作废。

历史已归档的 `*-analyst-report.md`（v6 内部稿）作为存量保留兼容，不强制迁移。

写作纪律见 [`../docs/analysis_human_touch.md`](../docs/analysis_human_touch.md)（三大病灶禁令、干支→人话翻译表、流年断法三要素、裁决义务）；推演 SOP 见 [`../docs/agent_tools.md`](../docs/agent_tools.md) Step 6。

**抗引擎变更**：人话规范与 Linter 的风格类检查不随 `engine/` 变更失效；若 Linter 报「契约失效」，按 [`../docs/analysis_human_touch.md`](../docs/analysis_human_touch.md) §3.5.2 同步清单处理。
