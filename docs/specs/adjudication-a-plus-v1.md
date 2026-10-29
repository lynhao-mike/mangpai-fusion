# A+ 裁决规格 v1.1（Gemini + WB 收敛，草案待冻结）

> 依据：`docs/reviews/t187-gemini4-verdict-v1.md`、`docs/reviews/t187-wb-v4-verdict-v1.md`。
> 状态：阈值已统一；待 Opus/owner 最终确认后 hash 冻结。不得在 dev-20/fresh-40 上调。

## 1. 输入契约

- `case_id/chart_id/four_pillars/gender`
- `target_relation: {addr_a, addr_b, char_a, char_b, mechanism}`；地址用 `Y.s/Y.b/M.s/M.b/D.s/D.b/H.s/H.b` 钉死两端；
  `mechanism ∈ {冲,合,穿,刑,克,生,化,墓}`；**禁止 source.path / source.locator**。
- 盲卷先过 `engine.cli` 合法性；非法时柱不得入卷。

## 2. 三层分栏

| 层 | 条数 | 计分 |
|---|---:|---|
| fixed gate | 10 | 克/生/化/墓；≥9/10；**新策展，非 dev-20**；不进动态主分母 |
| decidable dynamic | 40 | 冲/合/穿/刑；必须 actor→target 或 mutual；nj=miss；主分母 |
| ambiguous | 10 | 真歧义/边界；允许 nj，但必须带正反冲突双引文 `conflict_quotes[2]`；单列 |

- anchor-60：≥30 盘、≤2/盘；与 golden-20、p1-holdout-20、fresh-40 三重零重叠；标注/运行/裁判分离；双人复核；答案先 hash。
- ambiguous 标签审计：>20% 在语料里其实可判 = 标注放水，需重标。

## 3. 引擎 / Agent 边界

- 引擎：事实 + 固定克/生/化/墓；**不发射任何党势方向**（R1/R2/R3/R5b 全死）；党数回执仅披露，不作方向依据。
- 刑：只保留 mutual **候选**（未戌刑/三刑齐），双向可表达；PF-025 单向、PF-027 mutual 都可能。
- 自刑边（酉酉/亥亥/午午）：保留事实边，**逐条 logged 剔除出做功候选**，不静默丢弃。
- Agent：读 `engine.cli` + `query_theory` + 原文；给 actor→target / mutual；带 edge_id、source_ref、逐字 quote、党势/主宾依据。
- `needs_judgment`：仅 ambiguous 可用，且必须 `conflict_quotes[2]`；decidable 上 nj=miss。

## 4. 阈值（冻结）

| 项 | 规则 |
|---|---|
| 主指标 | decidable 40 delivered-verdict correct；nj=miss；ambiguous 单列 |
| fixed 10 | ≥9/10；不过=事实层回归 |
| pass | ≥32/40 且 Wilson LB>50%（≈65.2%）且 chart 聚类 ≥78% 且 margin ≥+8 |
| 琥珀 28–31 | 可演示、不可宣称；只允许换新盲集复测一次 |
| 红 24–27 | 不宣称、不发布方向特性；事实+分流层可发；新预注册 |
| 硬 kill | <24/40 或 margin <+6 |
| margin +6–+7 | 灰：绝对分 ≥32 也压琥珀 |
| nj 逃票 | ≤4/40 正常；5–6/40 灰封顶琥珀；>6/40 kill |
| 引文 | 伪造/行内不可检出/与机制无关 >2/40 kill |
| 一致性 | 3 次方向一致 <90% kill |
| E2 | 本轮只披露（基线 12/40）；下轮 top-3 ≥50%；两轮 chance → 产品级 kill |
| 3 卡 | direction_known 3/3、rescue 3/3 且挂源、移植拒绝 ≥95%/同构 ≥80%、单字反事实翻转（预注册翻哪个字）、第三人可重推 |

## 5. 最小证明点

E1：给足 relation identity 的 decidable 40，未污染 Agent 必须表态；一次评分按 §4。E2 只披露；不混测。
scorer v2 必须先用 T-187 fixture 复算出 **12/40、2/20、28/40**，证明量具修好，才上新卷。

## 6. 步骤

1. 冻结本规格 + scorer v2 + T-187 回归 fixture。
2. 双人隔离策展 anchor-60（10 fixed +40 dynamic +10 ambiguous）；engine.cli 预检；无 locator；先 hash。
3. 未污染 Agent 跑 3 次；中枢一次性评分 + 3 卡门禁。
4. 按表判 pass/琥珀/红/kill；不调阈值。

## 7. 禁止

- 不复活引擎党势；不为 PF-008/PF-018/R8 调规则；不把 fixed 混进 40；
- 不在 dev-20/fresh-40 上重跑宣称；不留 locator；decidable 不给 nj；
- 看过答案的人不当裁判；不事后移阈值；不扩岁运/P2；不把旧卡当证明。
