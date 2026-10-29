# T-174 · P1 33 条第二人复核（只读）

- 状态：🔵 Ready
- 优先级：**P0（P1 尺子的独立复核）**
- 依据：`docs/reviews/p1-direction-recall-verdict-v1.md`
- 前置：独立 Agent 分支 `rethink/2026-10-29` @ `6a40bcb5`

## 0. 一句话

对独立 Agent 的 33 条原书主功标注做**第二人复核**：quote 是否逐字、地址是否对、actor 是否原文明确；
重算方向召回 7/17；出分歧清单。**只读，不改分支、不改代码。**

## 1. 输入

- `E:\Git hub\mangpai-fusion-rethink\META\golden-20-core-edges-v1.json`（33 条）
- `E:\Git hub\mangpai-fusion-rethink\META\golden-20-core-edge-recall-v1.json`（结果）
- `META/golden-20-answers-v1.json`（原书答案）
- `sources/` 原文（quote 必须逐字命中）
- `engine.cli`（地址/边/actor 复核）

## 2. 复核内容

逐条 33 条：

1. `quote` 是否逐字出现在 `source_refs.path:line`；
2. `a_addrs`/`b_addrs` 是否是原文所说宫位/十神的正确地址；
3. `actor_stated` 是否真的由原文明确（「A 克 B」），不是 reviewer 补的；
4. `kinds` 是否原文明确；原文没说的应为 null；
5. 与 `golden-20-core-edge-recall-v1.json` 的 `rows[]` 对照：地址/边/actor 是否一致；
6. 重算：23 可判、17 有施力方、正确几条、方向召回百分比；
7. 分歧清单：按「quote 不逐字 / 地址错 / actor 原文没说 / kind 错 / 其他」分类。

## 3. 产物

- `META/p1-second-review-v1.json`：33 条复核、分歧、重算
- `META/p1-second-review-v1.md`：计数、分歧、结论（41.2% 是否稳健）
- 可选 `tests/tools/test_p1_second_review.py`（schema/确定性）

**禁止**：改分支、改 33 条原文件、改 engine/规则/测试；不跑评分模型；git 写操作。

## 4. 验收（中枢亲自看）

- 33 条全部有复核状态；
- 重算的 7/17 与结果文件一致或给出差异原因；
- 分歧清单可回原文；
- 结论明确：41.2% 是否仍 <60%（±2 条内）。

## 5. 回报

1. 改动文件；2. 原始输出（重算数字、分歧计数）；3. 风险；4. 下游须知（P1 是否要改阈值/重跑）。
