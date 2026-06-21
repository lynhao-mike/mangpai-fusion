# templates/ · 模板

| 文件 | 用途 | 阶段 |
|---|---|---|
| [input-from-wenzhen.md](input-from-wenzhen.md) | 问真八字 APP 信息提取规范 | M6 产出 |
| [report-v6.md](report-v6.md) | 《命理师内容报告（统一版）》当前稳定模板；归档置顶可跳转、全中文展示 schema、受限概率 baseline / prior boost、待反馈关键流年独立模块 | 当前稳定标准 |
| [report-v5.md](report-v5.md) | v5 文件名兼容入口；内容暂与 v6 展示规范保持一致，旧调用会由渲染器 alias 到 v6 | v5 兼容别名 |
| [report-v1.3.md](report-v1.3.md) | 历史《命理师内容报告（统一版）》渲染入口基线；不再作为新案默认模板 | 历史参考 |
| [feedback.md](feedback.md) | 命主反馈采集模板 | M7 产出 |
| [analysis-template-options.md](analysis-template-options.md) | 历史 analysis 输出规范候选方案；V2 后仅作架构回溯，不作为新案入口 | 历史参考 |
| [theory-extraction-template.md](theory-extraction-template.md) | 子平格局派、滴天髓调候派等原始教案到候选规则的理论提取模板 | 多专家体系预留入口 |
| [cases/_TEMPLATE/analysis.md](../cases/_TEMPLATE/analysis.md) | 历史 case 技术归档模板；V2 新案不得作为第二份可读报告默认生成 | 历史/内部参考 |
| [cases/_TEMPLATE/statement_index.json](../cases/_TEMPLATE/statement_index.json) | case 目录内的断语索引模板；结构与 C-2026-025 一致：`statements` 列表 | 当前唯一对象映射标准 |

模板都遵循“宁详勿略、可追溯、可回测”原则，避免遗漏关键命主信息。自 V2 起取消“双侧报告模式”，正式输出只生成一份《命理师内容报告（统一版）》；报告展示层禁止暴露共识 ID、互补 ID、独门 ID、冲突 ID、statement_id、报告章节编号、statement_index、关联裁判、内部推理索引与 Agent 工作记录。统一报告的性格与行为模式必须单列；学业 / 事业 / 财富 / 婚姻 / 健康等主要事项必须引用 [`../engine/contracts/11-outcome-taxonomy-v1.md`](../engine/contracts/11-outcome-taxonomy-v1.md) 与 [`../mapping/outcome-taxonomy-v1.yaml`](../mapping/outcome-taxonomy-v1.yaml)，缺少领域等级、二级指标等级、证据链、置信度、应期或反馈字段时，不得视为完整报告。

历史报告模板 `report.md`、`report-v1.2.md`、`report-v1.4.md` 不再作为新案入口或可选版本；`report-v5.md` 仅作为旧系统兼容别名保留，新案默认由 `tools/render_report.py` 收敛到 `report-v6.md`。
