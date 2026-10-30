# T-197d · P0 卡修正（T-197c fail 后）

- 状态：🔵 Ready
- 依据：`META/p0-thirdparty-v1.json`（选择层 3/4=75%，P0-04 0/1）
- 前置：main `4b29b381`

## 0. 一句话

只修 P0 卡与 report 的**可复现性/字段一致性**，不重跑 A+、不改 engine、不跑 P1。
目标：同一第三方按卡重推 ≥90%；修不到就不宣称 P0。

## 1. P0-04

- 3 个 A 候选 dc1/dc2/dc3 **全存活**，不得用一个 `selected_option` 冒充唯一：
  - 拆成 3 个 claim（各自 `selected`/`claim_id`），或给 tie-break 规则并记录；
  - 卡级 `selected_option` 在非唯一时必须 `null`；
- `anchor_a` 填 AQ1=yes；`state_selected` 若 st2/st3 不能唯一→`null`，`state_tier=C`；
- `state_scope`/`pending`/`tier_reason`/`not_auto_selected`/`selection_source` 不得互相矛盾；
- `st1/st2.anchored_by` 改 AQ1；`anchor_a_note` 与 `state_note` 不得一边禁代答、一边据 L398 代答；
- `A 3/12=25%` 按 **claim** 计数，不按卡计数；A 率与 A 精度分开。

## 2. P0-03

- `dc3`（戌坏丑）与 `rs1`（戌坏丑救应）**同源重复**：二者只保留一个层级（方向或救应），不得双计；
- AQ1 的 `discriminates` 必须覆盖 dc3，或把 dc3 移出方向候选；
- unknown 下唯一幸存 dc3 时，`selected_option` 要么填 dc3，要么明确 `needs_anchor`，不能空着；
- AQ2 yes 要 `eliminate` 而非只 downgrade；st1/st2 不唯一时 `state_selected=null`。

## 3. P0-01/02

- e015 理由把月支 M.b 写成“夫妻宫”→ 改为日支/配偶宫；
- AQ2 的 `eliminates` 触及未列入 `discriminates` 的 dc2→ 补进 `discriminates` 或删除；
- st1/st2 的 `anchored_by` 必须是实际区分状态的题，不得写 AQ1。

## 4. report 与计数

- `META/p0-report-v1.md` 的 5 unknown/1 yes 写进卡 `anchor_a`；
- report 的 C/B1 与卡 `direction_tier` 统一；
- seeded 16/16 与 20/20 统一（写明是“植入错误”还是“self_test”）；
- A 3/12 的分子/分母口径写清。

## 5. verify 加三条

1. `selected_option` 非唯一时非空 → fail；
2. `anchor_a` 与 report 不一致 → fail；
3. A/B1/C 计数与 report 不一致 → fail。

## 6. 产物

- 修正后的 `META/p0-cards-v1.json`、`META/p0-report-v1.md`
- `tasks/T-197d/BRIEF.md` + `STATUS.md`
- 不跑 P1；不做 git 写；不改 engine/保护区/A+。

## 7. 边界

- 不为了过 90% 删候选/改答案/放宽断言；
- 不把 A 的 3 个 claim 压成 1 个假唯一；
- 修完由 T-197c 重跑，不改第三方结论。
