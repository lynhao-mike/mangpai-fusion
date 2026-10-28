# T-158 STATUS

- 状态：🔴 **v2 完成，门槛未过 → 标签不适合作裁决；T-160 不启动**（2026-10-29）
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
| 00:36 | 子代理 K 交付 v2：新增 `tools/domain_labels_wealth_health_v2.py`、`META/domain-labels-wealth-health-v2.{json,md}`、`tests/tools/test_domain_labels_wealth_health_v2.py`；v1 四件未动（v1 JSON SHA256 仍 `E9DA1DF4…`）。`python -m tools.domain_labels_wealth_health_v2` 退出码 0；`debt` 1/0/null=22/307/615（6.71%，n=328）、`serious_health`=22/365/557（5.70%，n=386）；v1→v2 流失 27/109（词表 18/76、家属 5/26、主体不明 1/5、房贷 1/0、否定 2/2）；**门槛：假阳性 debt 18.18%（4/22）、health 36.36%（8/22），含漏判 27.27% / 40.91% → 标签不适合作裁决（停，不再调词）**；v2 测试 30 passed；两次运行 JSON SHA256 一致；`git status --porcelain cases/` 为空。详见 BRIEF §5 |
| 00:50 | 中枢验收 v2：两次运行 JSON 哈希 `BB40808B…` 一致；v1 仍 `E9DA1DF4…`；v2 测试 30 passed；全量 **1246 passed / 1 skipped / 0 failed**；门槛结论接受——`labels_not_suitable`，**T-160 财富/健康不启动**；提交 |

## Blockers

1. **`null` 口径已裁决**：无可用证据（无该域事件 / 全提问 / 空文本）→ `null`，不折 0/1；v1 数字保留。
2. **v1 不进 T-160**：已知误判 `debt` 16/49（33%）、`serious_health` 71/131（54%）。v2 按卡 §9.2 做主体/否定/严重度/房贷过滤；**误判率仍 >20% 则停**，判「标签不适合作裁决」。
3. v2 产物写新文件 `META/domain-labels-wealth-health-v2.{json,md}`，v1 不动。
4. **v2 结论（已完成，门槛未过）**：按卡 §9.2.6 **停，不再调词，T-160 不启动**。
   - 假阳性：`debt` 4/22 = 18.18%（家庭债务 1、房贷跨句 1、公司破产 1、应收款 1）；
     `serious_health` 8/22 = 36.36%（祖辈 4、姻亲 1、繁体兄長 1、恋人 1、跨句主语继承 1）。
   - 假阴性：`debt` 2（否定窗口误伤「未/没」）、`serious_health` 1（「差点挂了 重病」）。
   - 含漏判错误率：`debt` 27.27%、`serious_health` 40.91% → 两标签均超 20%。
   - 敏感性：零主语若判「主体不明」则阳性归零（标签不可用）；主体词表加祖辈/姻亲后 `serious_health` 22→17（仍剩 3 例误判）。
   - 若中枢要 v3：须重新预注册（扩展亲属词表 / 跨句主语 / 否定窗口避开干支与「差点挂了」），不在 v2 上就地改词。
