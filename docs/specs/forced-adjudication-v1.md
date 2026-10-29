# 强制裁决双层 v1（D 草案，未冻结）

> 依据：Opus 5.5 的 T-187 复核；`docs/reviews/t187-instrument-verdict-v1.md`。
> 状态：**草案，未预注册、未跑**；等人类/Opus/Gemini 4 确认后再 hash 冻结。

## 1. 产品假设

一张盘 + 一条目标边 → 一条锚定作用断言：

`edge_id / direction(actor→target | mutual) / state(成|败|救应) / source_ref / verbatim_quote / party_receipt`

- 引擎（T-184 冻结）只出事实 + 克/生/化/墓方向；
- 引擎的冲/合/刑/穿/合绊 `needs_judgment` 与 `mutual` 只是候选；
- **Agent 必须给 actor→target 或 mutual；`needs_judgment` 不再是合法终态**（输出 nj 计错）。
- 不在引擎里补寅申巳亥、刑方向、穿制规则（这些是从 fresh-40 答案看出的污染启发，交给 Agent 用原文判）。

## 2. 两个证明点

### E1 · 给边定向

- 盲输入：四柱/性别 + 目标两端引擎地址 + 关系名（不给 source locator）。
- 输出：方向 + 成败 + source_ref/quote + 党势回执。
- 主指标：correct/60；nj 计错。
- pass ≥45/60（75%）；kill <36/60。
- 固定五行子层：≥18/20；否则先修引擎 bug，不是判断问题。
- 对照基线：先算“Δ 符号一方为 actor”“五行克方为 actor”两条笨规则；系统至少高 6 条。
- 一致性：同一 prompt 跑 3 次，方向一致率 ≥90%。

### E2 · 选边

- 同一批只给盘，看 top-3 是否命中专家边；T-187 的 12/40 是基线。
- 目标 ≥50%（top-3）；不过则只攻选边，再不过停。

## 3. fresh-60

- 全部新盘；与 dev-20、fresh-40 零重叠；换人策展。
- 只收原文明写 actor 或明写“两坏”的条目。
- 分层：固定五行 ≥20；冲/合/刑 ≥25；穿 ≤15。
- 盲输入不含 source locator；答案先 hash；标注人 ≠ 运行人。
- 评分器先过地址归一（a/b）合成测试，再跑真数据。

## 4. 3 张真实盘卡

- `direction_known=true` 3/3；`rescue_judged` 有明确判定；
- 断言移植到随机另一张盘，≥90% 被拒（边 ID 不存在/方向翻转）；
- 锚点可由第三方只凭 CLI + source_ref 重推；
- 已知答案的旧 3 张卡只演示，不进盲测。

## 5. 禁止

- 不在 dev-20/fresh-40 上改阈值/加规则/换分母；
- 不复活 5 例 spike；不扩岁运；不写专用 H02/H05 规则；
- 不把 `needs_judgment` 当合法退路；
- 不从答案往引擎补规则。

## 6. 待确认

- 人类/Opus/Gemini 4 是否接受 D/E1/E2/fresh-60 与上述阈值；
- 接受后：先 hash 本规格 + fresh-60 答案，再跑；
- 若 E1 不过：停自动方向主张；退检索另立项，不算续命。
