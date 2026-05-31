# reports/ · 正式报告归档

每个案例分析完成后，生成 `C-YYYY-NNN-{乾/坤}-{四柱}-report.md` 报告文件。

报告格式以 [`../templates/report-v1.3.md`](../templates/report-v1.3.md) 为唯一标准；该标准由 [`C-2026-025-坤-辛未乙未甲辰乙亥-report.md`](C-2026-025-坤-辛未乙未甲辰乙亥-report.md) 固化，报告类型为命主可读版，产品版本 v1.3.0，pipeline/schema v1.4.0。

**强制约束**：
- 每个 `cases/C-YYYY-NNN-{乾/坤}-{四柱}/` 必须对应 `reports/C-YYYY-NNN-{乾/坤}-{四柱}-report.md`
- 二者必须在**同一次 commit** 中提交（不允许只提交案例不提交报告）
- 报告标题必须标注性别命式（乾/坤），格式如：`# 八字分析报告 · C-YYYY-NNN-乾-四柱 · 乾`
- 报告必须包含 C-2026-025 标准章节与归档信息
- `statement_index.json` 必须使用 C-2026-025 的 `statements` 列表结构
