# T-158 STATUS

- 状态：🟡 v1 交付、口径已裁决；**v2 修订中**（2026-10-29）
- 执行者：子代理 K
- 任务卡：`tasks/T-158/PROMPT.md`
- 简报：`tasks/T-158/BRIEF.md`（Worker 写）
- 验收：中枢亲自跑；标签只来自事件，不含盘面字段

## Execution Log

| 时间 | 动作 |
|---|---|
| 00:30 | 中枢建卡并派发；与 T-159（事业可行性审计）并行，File Scope 无重叠 |
| 00:19 | 子代理 K 交付：4 文件（工具 / JSON / MD / 测试）。`python -m tools.domain_labels_wealth_health` 退出码 0；漏斗 992/959/950/952/947、基础集 944、chart_ready 940；`debt` 1/0/null=49/287/608（阳性率 14.63%，n=335）、`serious_health` 131/287/526（31.41%，n=417）；两次运行 JSON SHA256 一致（`E9DA1DF4…`）；`pytest tests/tools/test_domain_labels_wealth_health.py` 38 passed；`pytest -q` 1216 passed / 1 skipped（含并行 T-159 的测试）；`git status --porcelain cases/` 为空。详见 `tasks/T-158/BRIEF.md` |
| 00:40 | 中枢裁决：`null` = 无可用证据（无事件/全提问/空文本），不折 0/1；v1 只作审计留档，T-160 不得用 v1 评分；派 v2（主体/否定/严重度/房贷过滤），误判率 >20% 则停。写入卡 §9 |

## Blockers

1. **`null` 口径已裁决**：无可用证据（无该域事件 / 全提问 / 空文本）→ `null`，不折 0/1；v1 数字保留。
2. **v1 不进 T-160**：已知误判 `debt` 16/49（33%）、`serious_health` 71/131（54%）。v2 按卡 §9.2 做主体/否定/严重度/房贷过滤；**误判率仍 >20% 则停**，判「标签不适合作裁决」。
3. v2 产物写新文件 `META/domain-labels-wealth-health-v2.{json,md}`，v1 不动。
