# templates/ · 模板

| 文件 | 用途 | 阶段 |
|---|---|---|
| [input-from-wenzhen.md](input-from-wenzhen.md) | 问真八字 APP 信息提取规范 | M6 产出 |
| [report-v1.3.md](report-v1.3.md) | 当前报告渲染入口基线；分析八字默认生成命理师报告并归档，用户报告需明确命令；主要事项必须逐项输出 15 层判断 | 当前唯一标准 |
| [feedback.md](feedback.md) | 命主反馈采集模板 | M7 产出 |
| [analysis-template-options.md](analysis-template-options.md) | analysis 输出规范候选方案与长期规则说明 | v1.4 定稿参考 |
| [theory-extraction-template.md](theory-extraction-template.md) | 子平格局派、滴天髓调候派等原始教案到候选规则的理论提取模板 | 多专家体系预留入口 |
| [cases/_TEMPLATE/analysis.md](../cases/_TEMPLATE/analysis.md) | case 目录内的固定 analysis 技术归档模板；以 C-2026-023 最新 analysis 为基准 | v1.4 固定模板 |
| [cases/_TEMPLATE/statement_index.json](../cases/_TEMPLATE/statement_index.json) | case 目录内的断语索引模板；结构与 C-2026-025 一致：`statements` 列表 | 当前唯一对象映射标准 |

模板都遵循“宁详勿略、可追溯、可回测”原则，避免遗漏关键命主信息。analysis 模板和正式命理师报告均禁止裸写 L+数字层级，必须写成“层级｜现实释义｜起止界限｜证伪条件”；学业 / 事业 / 财富 / 婚姻 / 健康 / 性格等主要事项缺少任一 15 层判断时，不得视为完整报告。

历史报告模板 `report.md`、`report-v1.2.md`、`report-v1.4.md` 已从当前仓库删除，不再作为新案入口或可选版本。
