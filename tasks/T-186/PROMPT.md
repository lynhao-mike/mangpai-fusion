# T-186 · P1′ 系统级断言评分器（一等指标）

- 状态：🔵 Ready
- 优先级：**P0（系统级盲测的尺子）**
- 依据：WB/Opus 裁决；`docs/specs/party-direction-v1.md`；goal v5
- 前置：T-184 已验收；T-183/T-185 并行

## 0. 一句话

写一个**独立的系统级断言评分器**：读 fresh-40 答案 + routing 例 + 系统输出，
一等字段输出 precision / coverage / needs_judgment 率 / confident-error / Wilson CI；
**不跑真实数据、不改 engine、不调阈值。**

## 1. 输入

- `META/p1-fresh-40-answers-v1.json`：40 条明确方向断言（a/b/kind/actor/quote/source_ref）
- `META/p1-fresh-40-routing-v1.json`（T-185 将补）：5 条 `expected_direction=needs_judgment`
- 系统输出 JSON（后续 runner 产生）：每条断言 `case_id, a, b, kind, direction∈{actor→target, mutual, needs_judgment}, edge_id, source_ref`
- 无真实输出时只跑合成 fixture；**不伪造真实结果**。

## 2. 指标（全部一等字段）

1. `total` = 40 + routing；
2. `correct` / `wrong` / `abstain_expected` / `abstain_unexpected` / `missing`；
3. `precision` = correct / (correct + wrong)（不含 needs_judgment）；
4. `coverage` = (correct + wrong) / total；
5. `needs_judgment_rate` = 实际 needs_judgment / total；
6. `confident_error` = wrong / (correct + wrong)；
7. Wilson 95% CI：precision、coverage 各一；
8. 分类型（克/生/化/墓/冲/合/穿/刑）小表；routing 例单列，不混入 precision 分母。

## 3. 判定（预注册，不调）

- pass：32/40（80%）且 Wilson 下界 >50% 且 coverage ≥75% 且 confident_error ≤10%
  且 dev-20 否决/不变量全过；
- kill：<24/40；24–31 灰区只发事实层；
- needs_judgment_rate >50% 只准宣称“分流引擎”，不准宣称“方向引擎”。

## 4. 产物

- `tools/p1_assertion_eval.py`（CLI：`--answers --routing --system-output [--json]`）
- `tests/tools/test_p1_assertion_eval.py`（合成 fixture：全对/全错/abstain/missing/neutral）
- `tasks/T-186/BRIEF.md` + `STATUS.md`
- 分支 `p1/assertion-eval`（worktree `..\mangpai-fusion-assertion`，从 main `f003d216` 起）

## 5. 禁止

- 不跑真实 fresh-40；不改 engine/hold-out/answers；不改阈值/分母；
- 不把 routing 例混入 precision；不把 abstain 记 ok/wrong；
- 不 push main。
