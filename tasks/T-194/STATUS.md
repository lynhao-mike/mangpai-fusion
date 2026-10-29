# T-194 STATUS

- 状态：🟢 交付待验收（2026-10-29，子代理 AT）；B 复核未做
- 执行者：子代理 AT
- 验收：中枢抽查 + 双人复核（B 另派）

## Execution Log

| 时间 | 动作 |
|---|---|
| 20:20 | 建卡派发；fixed-20 + 分流预注册 |
| 20:18–21:30 | 读卡/`META/p1-anchor-60-v1.md`/`sources/duan/`；建 chart 索引（1129+ 唯一四柱）；提取克/生/化/墓候选；按「四柱零重叠 + 端点字唯一 + 引文逐字」筛选 |
| 21:05 | 锁定 20 条（克 5 / 生 5 / 化 5 / 墓 5）、20 张不同盘；`engine.cli all` 逐盘预检 20/20 退出码 0 |
| 21:10 | 写 `META/p1-fixed-20-blind-v1.json` + `-answers-v1.json` + `.md`，记录 sha256（答案先 hash） |
| 21:20 | 写 `META/routing-questions-v1.json`（15 题，97 证据项）+ `routing-prereg-v1.json` + `.md`，冻结 hash |
| 21:32 | 自检（blind 无答案/定位字段、a-b 对齐、引文逐字、区间零重叠、routing 边 ID 复现）→ errors: 0；写 BRIEF/STATUS |
| 21:40 | 加 `tasks/T-194/verify.py`（stdlib）并跑通：`PASS`，退出码 0 |

## 交付物

| 文件 | 状态 |
|---|---|
| `META/p1-fixed-20-blind-v1.json` | ✅ 20 条，sha256 `f7bdf96f…` |
| `META/p1-fixed-20-answers-v1.json` | ✅ 20 条，sha256 `09e6e497…` |
| `META/p1-fixed-20.md` | ✅ 策展说明 + B 复核清单 |
| `META/routing-questions-v1.json` | ✅ 15 题 / 97 证据项，sha256 `580dc36a…`（restricted） |
| `META/routing-prereg-v1.json` | ✅ 阈值 ≥0.80 / <0.60 / 0.60–0.79，sha256 `23eba8b3…` |
| `META/routing-questions-v1.md` | ✅ 口径与风险 |
| `tasks/T-194/verify.py` | ✅ 标准库自检，`PASS`（退出码 0） |
| `tasks/T-194/BRIEF.md` | ✅ |

## 关键数字（现场跑出）

- fixed-20：20/20 `engine.cli all` 退出码 0 + chart_id；四柱对 dev-20/holdout-20/fresh-40/anchor-60 **0 重叠**；行区间 **0 重叠**（最近 6 行）；端点字唯一 20/20。
- routing：15 题（婚 4 / 事 4 / 健 3 / 财 4）；宫位 35 + 边 32 + source_ref 30 = 97 项。

## Blockers

1. **B 复核未做**：本卡只完成 annotator A；需中枢另派复核（清单见 `META/p1-fixed-20.md` §8）。
2. **T-192 规格缺位**：`docs/specs/fact-evidence-pack-v1.md` 尚未产出，routing 证据项口径由本卡自定并冻结在 `routing-prereg-v1.json`；若 T-192 规格随后改变字段名，需要 v2 对齐。
3. **routing 与 fixed-20 同盘批**：卡允许「同一批或新盘」；若验收要求两卷不同盘，需换盘重发 v2。

## 未做（按卡禁止）

- 未跑评分器；未测方向/断语；未测冲合穿刑；未调 A+ 阈值；未做 git 写；未改 engine/规则/测试/保护区。
