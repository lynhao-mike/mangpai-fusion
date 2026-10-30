# T-197c BRIEF · r3（第三方复核）

- 状态：🟢 r3 完成；**4 项优先项 4/4 清零**；**selected 4/4 一致（100%）**；建议 **P0 gate 通过**（按 T-197c 口径，待中枢确认）。
- 范围：只核 T-197c r3 的 4 个优先项 + selected；不评分、不改卡、不做 git 写、不碰 engine/保护区。
- 输入：`META/p0-cards-v1.json`（rev r3）、`META/p0-report-v1.md`、`META/p0-thirdparty-v2.json`（按任务要求读取，仅作残余差异对照）、`sources/duan/` 4 段原文、`engine.cli`。除 v2 基线外，未读 answers / golden / scoring / 其他模型结论。
- 产物：`META/p0-thirdparty-v3.json`、本文件、`tasks/T-197c/STATUS.md`（另见 `.tmp-review-r3/` 临时只读校验）。

## 0. 一句话

4 个优先项全部由 r3 卡/root/原文/CLI 复现，selected 4 卡全部与卡内一致；剩下的是已登记的非阻塞 caveat 与缺证据（M-02 / M-04 / M-06，M-05 部分），不改变任何 `selected`。

## 1. 改动文件

| 文件 | 动作 |
|---|---|
| `META/p0-thirdparty-v3.json` | 新建：r3 逐项结果、selected 重算、残余差异/缺证据、gate 建议 |
| `tasks/T-197c/BRIEF-r3.md` | 新建：本简报 |
| `tasks/T-197c/STATUS.md` | 更新：r3 状态 + Execution Log |
| `.tmp-review-r3/` | 临时只读校验（4 盘 CLI 输出、逐字/选择重算脚本与结果）；未落仓，保留供本轮审计 |

未修改 `META/p0-cards-v1.json`、`engine/`、`tests/`、`sources/`；无 git 写。

## 2. 原始输出

### 2.1 4 个优先项（4/4 清零）

| # | 优先项 | 结果 | 关键证据 |
|---|---|---|---|
| P1 | P0-03 root AQ2 是否 eliminate st1、与卡内一致 | ✅ 清零 | root 与卡内 `if_yes={keep:[st2],eliminate:[st1],downgrade:[]}`、`elimination[yes].eliminates=[st1]` 完全一致；6 个 anchor_q 语义字段 root/card 6/6 相等（仅 root 有 `card_id`、卡内为 `null`） |
| P2 | P0-01 root AQ2.discriminates 是否 `[dc1,dc2,dc3]` | ✅ 清零 | root 与卡内均为 `[dc1,dc2,dc3]`；`elimination` yes 消 dc1/dc2、no 消 dc3、unknown 消三项，discriminates 覆盖全部被消项 |
| P3 | P0-02 outcome_quote 是否事业结局句、逐字命中 | ✅ 清零 | `source.outcome_quote` = L25 `07年转戊辰运08年提副军长，预测2012年还会提升正军级干部。`，逐字命中；不含婚姻句；L25 后半「此人婚姻非常好…」只出现在 `outcome_quote_domain_note` 的说明里 |
| P4 | P0-04 dc1 是否补 H.b、e011、L392 两丑入墓 | ✅ 清零 | dc1 `addrs/claim.members=[D.b,M.b,H.b]`、`targets=[M.b,H.b]`、H.b 十神=正官；`card.material_edges` 含 `e011`；CLI `e011=po(D.b,H.b)`；duan_zuogong 有 `墓用[D.b,M.b]` 与 `墓用[D.b,H.b]`；L392 引文逐字命中「月时丑官都入辰墓」 |

P4 的字段归属说明：dc1 本身没有独立 `material_edges` 字段；`e011` 记在 `card.material_edges` + `dc1.basis_text` / `co_claims`，H.b 已进入 dc1 的 `addrs` / `claim.members` / `ten_god_claims` / `palaces`。就本卡现有字段而言已补。

### 2.2 selected 4/4（机械重算）

重算规则：C 档 / `selectable=false` 不参与；`unknown` 走 elimination 的 unknown 行；仅 1 个幸存才填 selected；`state_selected` 必须等于唯一幸存候选的 `result`；无锚点层全部 eligible 候选幸存。

| 卡 | 方向层 | 状态层 | 卡内 selected | 重算 selected | 一致 |
|---|---|---|---|---|---|
| P0-01 | AQ1 unknown 消 dc1/dc2；AQ2 unknown 消 dc1/dc2/dc3 → 0 幸存 | 无 state 题；st1/st2 幸存（st3 C 排除） | `null` / `null` | `null` / `null` | ✅ |
| P0-02 | AQ1 unknown 消 dc1/dc2；dc3 为 C 排除 → 0 幸存 | 无 state 题；st1/st2 幸存 | `null` / `null` | `null` / `null` | ✅ |
| P0-03 | AQ1 unknown 消 dc1/dc2 → 0 幸存 | AQ2 unknown 消 st1/st2 → 0 幸存 | `null` / `null` | `null` / `null` | ✅ |
| P0-04 | 无锚点题；dc1/dc2/dc3 三条 A claim 全存活、互补不折叠 | st1/st2 参与（st3 C + selectable=false 排除）；AQ1=yes 消 st1 → st2 唯一，result=败 | `selected_option=null`；`selected_claims=[dc1,dc2,dc3]`；`state_selected=败` | `null`；`[dc1,dc2,dc3]`；`败` | ✅ |

**selected 一致 4/4 = 100%（≥90% 阈值）。**

### 2.3 CLI / 引文 / root 对齐

| 检查 | 结果 |
|---|---|
| `engine.cli all` 4 盘 | 退出码 4/4 = 0 |
| chart_id | 4/4 一致（P0-01 `cf-daef938eab28eb49e1b8`；P0-02 `cf-1627557db9bf35baf387`；P0-03 `cf-0075a9941ae6f079f4b9`；P0-04 `cf-4d8fe4fe1b354d973a7b`） |
| 四柱/性别 | 4/4 一致 |
| 优先项相关引文逐字 | 3/3（L25 事业句、L392 两丑入墓、L398 没收财产） |
| root vs 卡内 anchor_q | 6/6 语义一致（仅 `card_id` 字段差异：root 有值、卡内 null） |

CLI 命令（只读）：

```text
E:\Git hub\mangpai-fusion\.venv\Scripts\python.exe -m engine.cli all --pillars "辛巳 庚寅 甲申 庚午" --gender 乾 --json
E:\Git hub\mangpai-fusion\.venv\Scripts\python.exe -m engine.cli all --pillars "戊戌 癸亥 乙巳 己卯" --gender 乾 --json
E:\Git hub\mangpai-fusion\.venv\Scripts\python.exe -m engine.cli all --pillars "壬寅 庚戌 己丑 庚午" --gender 坤 --json
E:\Git hub\mangpai-fusion\.venv\Scripts\python.exe -m engine.cli all --pillars "乙巳 己丑 壬辰 辛丑" --gender 乾 --json
```

## 3. 未完成与风险

1. **残余差异 0**：r2 的 12 项（D-R2-01..12）逐项核对，均已按 report §4.1 处理；无仍与卡/root/原文矛盾的差异。D-R2-04 的原文证据缺口保留为 M-02，D-R2-09 的 C 标签借用与 D-R2-11/12 的语义口径保留为 caveat。
2. **缺证据 3 项**：M-02（P0-02 dc2 己制癸无原文/命主事实）、M-04（P0-03 本造专属心脏/血压判据缺，L131 是他造可迁移判词）、M-06（4 卡 seeded 复用同一 fixture，非逐卡独立注入）。**均不影响 selected。**
3. **部分 1 项**：M-05（P0-04 AQ1 窗口已覆盖 2003，但答案仍是 `source_outcome`，非命主自述；P1 需补 testimony）。
4. **C 标签 caveat**：P0-04 st3 仍用 `tier=C` 扩展借用；已加 `candidate_kind=definition/non_outcome` + `label_note` + `selectable=false`。下游不得读成「无源 C」，也不得据此改 `selectable=false`。
5. **口径 caveat**：P0-04 st1/st2 是「先富后破」时间序列，卡按「最终成败」取败；P0-03 st1/st2 result 都是「病」，state 层只分病位。两卡均已加 `state_scope_note` / `result_note`。
6. **A 率另计**：report §3 的 A 自动占比 3/11=27.3% 仍未达 ≥50%；该指标不在本轮 4 项/selected 复核范围，报告 §5 已归因为案例数据问题。若中枢把 A 率也作为必须同时满足的硬 gate，则不能仅凭本轮判过。
7. 未跑评分器、未改卡、未做 git 写；没有为过 gate 删候选、改答案或放宽断言。

## 4. 下游须知

- **gate 建议**：按 T-197c 口径（selected 复现 ≥90% 且 4 项清零）→ **pass**；selected 4/4=100%，4 项 4/4 清零，无 gate 阻塞。
- **不要**把本轮 `residual_caveats` 读成 selected 变化：P0-01/02/03 仍 `null/null`，P0-04 仍 `selected_option=null`、`state_selected=败`、`selected_claims=[dc1,dc2,dc3]`。
- P0-04 st3 的 C 标签是扩展借用；严格 schema 请按 `candidate_kind=definition/non_outcome` + `selectable=false` 读取。
- P1 前优先补：P0-02 dc2 的原文/命主依据（M-02）、P0-03 本造心脏/血压判据（M-04）、逐卡独立 seeded（M-06）；P0-04 命主 testimony（M-05）。
- 复现 r3 卡链时按 `build → T-197d patch → T-197e patch_p0_cards_r3.py`；`tasks/T-197/build_p0_cards.py` 未同步 r3，直接重跑 builder 会覆盖。
