# T-197c STATUS

- 状态：🟢 r2 复核完成；**重推一致 4/4（100%）**；建议 **P0 gate 通过**（按 selected 复现口径，**待中枢确认**）。12 项非选择性差异 + 6 项缺证据见 `BRIEF-r2.md`。
- 执行者：第三方复核子代理（r1 → r2）
- 任务卡：`tasks/T-197c/PROMPT.md`
- 产物：`META/p0-thirdparty-v2.json`、`tasks/T-197c/BRIEF-r2.md`（r1 的 `p0-thirdparty-v1.json` / `BRIEF.md` 保留）
- 验收：中枢比较重推一致率

## Execution Log

| 时间 | 动作 |
|---|---|
| 09:00 | P0 4 卡/6 答已收口；派第三方重推 |
| 09:12 | r1：完成 4 卡 CLI/地址/边/十神/引文核对（事实层 4/4 通过，0 错）；按 anchor_a+elimination 重推；P0-01/02 可复现、P0-03 有条件可复现、P0-04 不可复现；3/4=75% < 90%，gate fail；产物 `p0-thirdparty-v1.json` / `BRIEF.md` 已落盘 |
| 09:35 | r2：只读 r2 卡/报告/4 段原文/CLI，独立重推 4 卡；事实层 0 错（chart_id 4/4、十神 34/34、material edges 9/9、direction refs 11/11、引文 83/83）；selected/state/claims 8/8 层复现，**4/4 卡一致=100%**；P0-04 st3 语义判定成立（定义口径不参与成/败）；记录 12 项非选择性差异 + 6 项缺证据；产物 `p0-thirdparty-v2.json` / `BRIEF-r2.md` 已落盘 |

## r1 Blockers（历史，r2 逐项复核）

1. P0-04 `selected_option=dc3` 在三个 A 方向候选中不唯一 → r2 卡已改 `selected_option=null` + `selected_claims=[dc1,dc2,dc3]`；r2 重推一致。**已消解**。
2. P0-04 `state_selected=败` 不能由 `anchor_a=[]` 复现（unknown→st3；yes→st2+st3）→ r2 `anchor_a` AQ1=yes（L398）；st3 `selectable=false`；r2 重推 st2 唯一=败；st3 语义判定成立（见 `BRIEF-r2` §2.2）。**已消解（附 C 标签保留意见 D-R2-09）**。
3. `state_scope` / `pending` / `not_auto_selected` 与已填选择/状态冲突；`st1/st2.anchored_by=ED1` 悬空 → r2 `state_scope=claimed`、`pending=null`、`anchored_by=[AQ1]`；r2 核对通过；st2 `decision_by` 仍为 `expert_single_choice`（D-R2-05 残留）。**基本消解**。
4. P0-03 dc3 与 rs1 同源重复（戌坏丑），AQ1 不覆盖 dc3 → r2 只保留救应层 rs1，`dedup[0].original_record` 完整；r2 重推 direction 0 幸存、state 0 幸存 → null。**已消解**。
5. report 的 5 unknown / 1 yes 未落入卡 `anchor_a`；report 方向 C 与卡 B1、seeded 16/16 与 20/20 口径不一致 → r2 `anchor_a` 6 条落盘；卡/报告档位一致；seeded 两口径已分列。**已消解**（root `anchor_questions` 仍有 2 处未同步，见 D-R2-01/02）。

## r2 结论

- **4/4 卡 selected 可复现**：P0-01/02/03 两层 null；P0-04 `selected_option=null`、`state_selected=败`、`selected_claims=[dc1,dc2,dc3]`。
- **P0-04 st3 语义成立**：`state=null / result=needs_anchor` 的定义口径不参与成/败选择；C 标签属 `schema_compat` 扩展借用，建议改 definition/non_outcome；若 hub 收紧 C 定义，fallback 为 `state_selected=null` + `state_scope=candidate_only`，不是把 state 记成 C 档结论。
- **非阻塞残留**：D-R2-01..12（`BRIEF-r2` §2.3）；缺证据 M-01..06（§2.4）。其中建议 P1 前优先处理：root `anchor_questions` 同步（D-R2-02 最优先，未来 AQ2=yes 会分叉）、P0-02 D04、P0-04 H.b 覆盖、P0-03 L131 归属。

## Blockers

- 无 gate 阻塞。r2 发现均为非选择性差异/缺证据，不改变任何 `selected`；详见 `BRIEF-r2.md`。
