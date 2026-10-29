# T-189b STATUS

- 状态：✅ **交付待验收**（2026-10-29）
- 执行者：子代理 AP（T-189b）
- 任务卡：`tasks/T-189b/PROMPT.md`
- 分支：`p1/assertion-v2b`（worktree `..\mangpai-fusion-av2b`）
- 代码提交：`9a0b90f9`
- 验证：`pytest tests/tools/test_p1_assertion_eval_v2.py -q` → **73 passed**；
  全仓 `pytest -q` → **1569 passed, 1 skipped**；T-187 三数 **12/40、2/20、28/40** 已钉在测试里。

## Execution Log

| 时间 | 动作 |
|---|---|
| 17:15 | 拆分建卡（中枢） |
| 17:32 | T-189a 已合并（1520/1）；派 T-189b 增量（中枢） |
| 17:34 | 读卡 + 规格 §3/§4 + T-189a BRIEF/工具/测试 + `META/p1-system-run-v1.json` + `p1-fresh-40-answers-v1.json`；建 worktree（从 `0512463c` 起，`e6e4add5` 仍是祖先） |
| 17:36 | 写 B1（`party_delta` 或 `four_pillars` 现算 + 平局柱序左）、B2（本气克/生 + 四库主位端）、margin、per-case 地址表 |
| 17:40 | 写 chart 聚类 bootstrap（2000/seed 20261029）、3 次方向一致、T-187 回归、ambiguous source loader |
| 17:45 | 追加 49 个用例（T-189a 24 保留，共 73）；targeted **73 passed** |
| 17:48 | 合成 CLI smoke：B1 12、B2 0、margin +20、cluster 16/20、3 次 36/40、T-187 12/40 + 2/20 + 28/40（非真实盘） |
| 17:50–17:52 | 全仓 `pytest -q`：**1569 passed, 1 skipped**（0 failed；skip = T-114 既有） |
| 17:52 | commit `9a0b90f9`（工具 + 测试）；写 BRIEF/STATUS，文档单独提交 |

## Blockers

1. **fixed 10 的天干端点**：T-189a 的 `char_a/char_b` 只收单个地支字；真实 anchor fixed 10
   若出现 `庚`/`乙` 等天干会退出 2。需中枢二选一：T-190 fixed 全选地支端点，或授权把字集扩到干支。
2. **T-190 答案字段**：当前格式缺 `chart_id` / `four_pillars`（或 `party_delta`）/ `source_refs`；
   缺它们会导致 margin 不可比、聚类退化为逐条、多行 ambiguous loader 取不到第二行。
   请在 T-190 冻结 hash 前补，或评分时只读合并盲卷字段。
3. **chart 聚类 ≥78% 口径未定义**：全对盘率与 macro 是两个数；本工具都报，不判 pass/kill，
   请中枢在 A+ 规格里钉死。

## 交付摘要

- B1：delta>0 火党端→金水党端；<0 反向；=0 柱序左端；未戌同类端合法弃权（B2 兜住）。
- B2：本气克→克方、本气生→生方、同五行四库→主位端（D/H 优先；同主/同宾柱序靠后）；
  有柱位时四库**不弃权**。
- margin：`dynamic.correct − max(B1,B2)`；缺数据才 `margin_comparable=false`。
- 聚类：按 `chart_id` 的 macro / 全对盘率 / bootstrap95。
- 3 次一致：定向比端点取向，缺 case 记不一致；dynamic 主口径。
- T-187：`t187_regression()` 复算 **edge 12/40、direction 2/20、edge mismatch 28/40**；
  只作量具回归，不宣称新结果。
- source loader：`--source-loader --source-root`，只读、只补行文本，引文口径不变。
- 未跑真实 anchor-60；未改 engine/答案/阈值/分母；未 push main。
