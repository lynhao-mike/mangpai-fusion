# cases/ · 案例库

每个案例的标准归档结构：

```
cases/
├── cases-index.md                         案例索引（含八字指纹防重 + 统计）
├── _TEMPLATE/
│   ├── input.md                           输入模板
│   ├── analysis.md                        固定 analysis 技术归档模板
│   ├── feedback.md                        命主反馈模板
│   ├── statement_index.json               断语索引模板
│   └── lessons.md                         复盘教训模板
└── C-YYYY-NNN-{乾/坤}-{四柱}/
    ├── input.md                           输入（去隐私后的命盘 + 提问）
    ├── analysis.md                        四派融合分析过程（含 statement_id、派别仲裁、五维层级释义）
    ├── feedback.md                        命主反馈（应验/失验逐条记录）
    ├── statement_index.json               断语索引（用于 feedback 对齐与后续校准）
    ├── events.md                          命理分析过程记录（取用依据、判断路径、专项索引；不存放临时问答原文）
    └── lessons.md                         本案学到的教训（用于规律升降级；可在反馈后补齐）
```

生成报告时必须**同时**完成两侧归档：

- `reports/C-YYYY-NNN-{乾/坤}-{四柱}-analyst-report.md`：命理师内部正式报告。
- `cases/C-YYYY-NNN-{乾/坤}-{四柱}/`：同名 case 目录，至少包含 `input.md`、`analysis.md`、`feedback.md`、`statement_index.json`。

新案例首次分析若用户要求“分析八字 / 看这个八字 / 断这个八字 / 生成报告 / 形成报告 / 出报告 / 输出报告”，默认生成命理师报告，不得先只输出会话分析；必须在同一轮任务内生成 analyst report 并建立同名 case。若用户明确要求临时口头分析或不归档，必须标记“未归档、不可进入反馈闭环”；后续一旦要求报告，必须将首次会话分析与后续反馈校准补入同名 case，再生成 analyst report。只有当用户明确要求“生成用户报告 / 客户报告 / 命主可读报告 / 对外报告”时，才允许额外生成用户报告。正式报告与 `analysis.md` 必须覆盖学业 / 事业 / 财富 / 婚姻 / 健康 / 性格等主要事项；每个事项必须给出 15 层判断，格式至少包含“层级｜现实释义｜起止界限｜证伪条件”。

`analysis.md` 以 `cases/_TEMPLATE/analysis.md` 为固定模板；禁止裸写 `L+数字` 层级，必须写成“层级｜现实释义｜起止界限｜证伪条件”。

## 命理分析过程记录与交互归档

`cases/C-YYYY-NNN-{乾/坤}-{四柱}/events.md` 重新定位为“命理分析过程记录”，用于记录本案取用依据、判断路径、关键应期推导与专项分析索引；不再存放临时问答原文。对应 `analysis.md` 的“归档信息”需挂载报告侧 `reports/*-events.md` 与本案 `events.md`，确保分析归档与专项记录可点击互通。

每次处理临时询问、专项分析或非标准报告任务后，使用 `tools/event_archive.py` 追加归档本次“询问 / 分析 / 结果”：

- 能定位到案例时：写入 `reports/C-YYYY-NNN-{乾/坤}-{四柱}-events.md`，并由对应正式报告挂载可点击链接。
- 无法定位到具体案例时：写入 `META/session-events.md`。
- 报告侧 `*-events.md` 只记录交互审计，不替代 `analysis.md`、`feedback.md` 或 `statement_index.json`，也不参与反馈计分。
