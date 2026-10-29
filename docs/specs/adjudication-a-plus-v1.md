# A+ 裁决规格 v1（Gemini 4 修正，草案，未冻结）

> 依据：`docs/reviews/t187-gemini4-verdict-v1.md`；Opus D + WB A + 中枢 A+ 合成。
> 状态：草案；需人类/Opus/WB/Gemini 确认后再 hash 冻结。不得在 dev-20/fresh-40 上调。

## 1. 输入契约

- `case_id/chart_id/four_pillars/gender`
- `target_relation: {addr_a, addr_b, char_a, char_b, mechanism}`
  - 地址用 `Y.s/Y.b/M.s/M.b/D.s/D.b/H.s/H.b` 钉死两端；
  - `mechanism ∈ {冲,合,穿,刑,克,生,化,墓}`；
  - **禁止** `source.path` / `source.locator` / 任何答案行号。
- 盲卷先过 `engine.cli` 合法性；PF-040 类非法时柱不得入卷。

## 2. 三层分栏

| 层 | 条数 | 计分 |
|---|---:|---|
| fixed gate | 10 | 克/生/化/墓；≥9/10；**不进动态主分母** |
| decidable dynamic | 40 | 冲/合/穿/刑；必须 actor→target 或 mutual；nj 记 miss；主分母 |
| ambiguous | 10 | 真歧义/边界；允许 nj + 正反冲突双引文；单列，不进 40 |

- 40 动态：≥30 盘、≤2 条/盘；与 golden-20、p1-holdout-20、fresh-40 三重零重叠。
- 标注人 ≠ 运行人 ≠ 裁判；双人复核；答案先 SHA-256。
- 不掺固定五行进 40；否则通过率被送分题稀释。

## 3. 引擎 / Agent 边界

- 引擎：事实（干支/藏干/十神/宫位/关系边）+ 固定克/生/化/墓方向；**不发射党势方向**；
  刑只保留未戌刑/三刑齐的 `mutual` **候选**；自刑边（酉酉/亥亥/午午）不得当做功候选。
- Agent：读 `engine.cli` + `query_theory` + 原文；给 actor→target / mutual；带 `edge_id`、`source_ref`、逐字 quote、党势/主宾依据。
- `needs_judgment`：仅 ambiguous 可用，且必须给 `conflict_quotes[2]`（正反两条冲突原文或无功条件原文）；decidable 上 nj = miss。

## 4. 指标与阈值（草案）

- 主指标：decidable 40 的 delivered-verdict 正确率；nj 记 miss。
- pass：≥32/40；Wilson LB≈65.2%；chart 聚类 ≥78%；比两条笨基线高 **8** 条。
- 灰区：24–31 不宣称；<24 硬 kill；28–31 与 24–27 的“产品级 kill”定义需统一（Gemini §5.2 与 §7 有 8/6 条、28/24 条的不一致）。
- 逃票：decidable nj ≤4/40（10%）；>6/40（15%）kill。
- 引文：伪造/行内不可检出/与机制无关 >2/40（5%）kill。
- 一致性：同一输入 3 次方向一致率 ≥90%。
- 基线：B1 T-184 delta 符号；B2 五行本气克向+主位；系统至少 +8（pass），<+6 kill（+6–7 灰）。

## 5. 3 张真实盘卡

- `direction_known=true 3/3`；`rescue_judged=已判 3/3`；t4 岁运快照。
- 跨盘移植拒绝：随机异盘 ≥95%；同构异盘（同样夫妻宫冲/刑）≥80%。
- 单字反事实翻转：替换一个非目标端点关键字，direction/state 必须可验证翻转。
- 旧 3 张卡只演示，不进盲测。

## 6. 步骤

1. 勘误 D-05（PF-003/PF-023），不改历史 hash；新盲集双人复核。
2. 冻结本规格 + scorer v2（地址/字、三层、nj=miss、聚类 CI、conflict_quotes、基线）。
3. 双人隔离策展 anchor-40（40 动态 +10 ambiguous +10 fixed）；engine.cli 预检；无 locator；先 hash。
4. 未污染 Agent 跑 3 次；中枢一次性评分；3 张卡移植测试。

## 7. 禁止

- 不复活引擎党势；不为 PF-008/PF-018/R8 调规则；不把 fixed 混进 40；
- 不在 dev-20/fresh-40 上重跑宣称；不留 locator；不先做岁运/P2；不让 Agent 用 nj 逃票。
