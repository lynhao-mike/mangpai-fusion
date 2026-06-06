# reports/ · 正式报告归档

每个案例分析完成后，默认生成 `C-YYYY-NNN-{乾/坤}-{四柱}-analyst-report.md` 命理师报告文件。

报告格式以 [`../templates/report-v1.3.md`](../templates/report-v1.3.md) 为当前渲染入口基线，但默认产物定位为命理师内部报告。命主/客户/用户可读报告不再默认生成；只有收到“生成用户报告 / 客户报告 / 命主可读报告 / 对外报告”等明确命令时，才允许额外生成。

**强制约束**：
- 每个 `cases/C-YYYY-NNN-{乾/坤}-{四柱}/` 必须对应 `reports/C-YYYY-NNN-{乾/坤}-{四柱}-analyst-report.md`
- 二者必须在**同一次 commit** 中提交（不允许只提交案例不提交报告）
- 报告标题必须标注性别命式（乾/坤），格式如：`# 八字命理师分析报告 · C-YYYY-NNN-乾-四柱 · 乾`
- 命理师报告必须包含证据链、派别归属、置信度、反馈锚点与归档信息
- 不得默认生成命主可读版、客户版、用户版或对外报告
- `statement_index.json` 必须使用 C-2026-025 的 `statements` 列表结构
- 案例绑定的临时问答 / 专项分析 / 处理结果归档到 `reports/C-YYYY-NNN-{乾/坤}-{四柱}-events.md`
- 正式报告的“归档信息”必须挂载对应 `*-events.md` 与 `cases/*/events.md` 的可点击链接
- 报告侧 `*-events.md` 必须挂载对应 `cases/*/analysis.md` 的可点击链接；对应 `analysis.md` 的“归档信息”必须反向挂载 `reports/*-events.md`
- `cases/C-YYYY-NNN-{乾/坤}-{四柱}/events.md` 保留为“命理分析过程记录”，不存放临时问答原文
