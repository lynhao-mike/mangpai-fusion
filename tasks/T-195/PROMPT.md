# T-195 · R-tool 一次运行（fixed-20 + routing；不测方向）

- 状态：🔵 Ready
- 依据：`docs/specs/fact-evidence-pack-v1.md`；T-194 fixed-20/routing；T-194b A/B
- 前置：main `116cfb91`

## 0. 一句话

未污染 runner 只读 **fixed-20 盲卷 + routing 问题集** + `engine.cli` + `query_theory` + R 规格；
输出 fixed-20 的固定类事实与 routing 证据包。**不测方向、不输出断语**；中枢一次性评分。

## 1. fixed-20

- 20 条 fixed：每条给 `target_relation` 的端点；输出目标类（克/生/化/墓）事实、actor→target、edge/source_ref；
- 门禁：20/20 目标类覆盖；**out_of_class_emissions = 0**；不得发射冲/合/穿/刑/破/党势/岁运方向；
- 不要求 actor 对错计门（A/B 18/20；F20-011/014 已知 B 反向，fixed gate 只数类外与覆盖）。

## 2. routing

- 15 题；每题输出证据包：宫位、关系边 ID、source_ref 区间；
- 只测证据项覆盖率（macro_recall）：≥0.80 PASS、<0.60 KILL、0.60–0.79 GRAY；
- 不输出方向/断语/主次裁决。

## 3. 输入/隔离

- 只读：`META/p1-fixed-20-blind-v1.json`、`META/routing-questions-v1.json`（restricted 视图）、R 规格、`engine.cli`、`query_theory`、`sources/`；
- **禁止**：fixed-20 answers/B、routing-prereg 的期望证据、任何 anchor/fresh/holdout/golden answers、`p1-system-run*`；
- 不跑评分器；不做 git 写；不自评。

## 4. 产物

- `META/r-tool-run-v1.json`（fixed-20 事实 + routing 证据包；无方向/断语）
- `tasks/T-195/BRIEF.md` + `STATUS.md`
- 中枢用 R 规格的检查表评分；runner 不宣称通过。

## 5. 禁止

- 不做方向/断语；不改 engine/答案/阈值；不读 answers；不扩岁运/P2；不把旧卡当证据。
