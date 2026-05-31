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
    ├── events.md                          临时问答 / 专项分析 / 处理结果增量记录（不参与反馈计分）
    └── lessons.md                         本案学到的教训（用于规律升降级；可在反馈后补齐）
```

生成报告时必须**同时**完成两侧归档：

- `reports/C-YYYY-NNN-{乾/坤}-{四柱}-report.md`：命主可读正式报告。
- `cases/C-YYYY-NNN-{乾/坤}-{四柱}/`：同名 case 目录，至少包含 `input.md`、`analysis.md`、`feedback.md`、`statement_index.json`。

`analysis.md` 以 `cases/_TEMPLATE/analysis.md` 为固定模板；禁止裸写 `L+数字` 层级，必须写成“层级｜现实释义｜起止界限｜证伪条件”。

## 交互事件增量归档

每次处理临时询问、专项分析或非标准报告任务后，使用 `tools/event_archive.py` 追加归档本次“询问 / 分析 / 结果”：

- 能定位到案例时：写入 `cases/C-YYYY-NNN-{乾/坤}-{四柱}/events.md`。
- 无法定位到具体案例时：写入 `META/session-events.md`。
- `events.md` 只记录交互审计，不替代 `analysis.md`、`feedback.md` 或 `statement_index.json`，也不参与反馈计分。
