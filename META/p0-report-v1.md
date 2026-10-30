# P0 报告 · Agent-first 锚点消歧（2026-10-30 · r2 / T-197d 修正）

> 4 卡、6 个事实题、**5 unknown / 1 yes**；6 个答案已全部落进各卡 `anchor_a`（`unknown` 带 `answer_source=not_in_source`，`yes` 带 `source_ref`+逐字 `quote`）。
> P0 只验管道与完整性，不做统计结论。
> 结论：**P0 管道通过（`tasks/T-197/verify.py` 退出 0）；C 率 3/4 是数据问题，P1 必须换「有已知事实」的真实案例。**
> r2 修正范围：P0-04 三条 A claim 不再折叠为单一方向、P0-03 `dc3`/`rs1` 单层登记、P0-01/02 的字段与锚点指向、本报告与卡逐项对齐。**未改任何候选取舍结论、未改 engine、未跑 P1。**

## 1. 4 卡结果

方向档 / 状态档是**证据档位**（A/B1/B2/C/`not_claimed`）；`selected_option` / `state_selected` 是按 `anchor_a` 复算后的结果，`null` 表示该层没有唯一幸存者（`needs_anchor`）。

| 卡 | 四柱/性别 | 域 | 方向档 | 状态档 | selected_option | state_selected | 依据 |
|---|---|---|---|---|---|---|---|
| P0-01 | 辛巳 庚寅 甲申 庚午 · 乾 | 婚 | B1 | not_claimed | null | null | AQ1/AQ2 原文未载（L21–33 只写五次婚姻、老婆带子女全跑了、孤家寡人）；无 state 层锚点题 |
| P0-02 | 戊戌 癸亥 乙巳 己卯 · 乾 | 事业 | B1 | not_claimed | null | null | AQ1 原文未载（L17–27 只写军官晋升履历，未写收入来源）；`dc3` 为 C 档不参与选择 |
| P0-03 | 壬寅 庚戌 己丑 庚午 · 坤 | 健康 | B1 | B1 | null | null | AQ1/AQ2 原文未载（L135–141 只写子宫癌、手术、中医治好、戌坏丑）；`dc3`/`rs1` 同源已并为救应一层 |
| P0-04 | 乙巳 己丑 壬辰 辛丑 · 乾 | 财 | A | B1 | null | 败 | 方向 3 条 A claim 互补（库收/克坏/财源），卡级不折叠；状态 AQ1=yes（L398 非法集资没收财产）→ st2 破局 |

> `selected_option=null` 不等于「没有方向结论」：P0-04 的三条 A claim 各自成立，记在 `selected_claims=[dc1,dc2,dc3]` 与逐 claim 的 `claim_id/claim_selected` 上，A 档按 **claim** 计数。

## 2. 6 个事实题（= 各卡 `anchor_a`）

| # | 卡 | 题 | 答案 | 依据 |
|---|---|---|---|---|
| 1 | P0-01 | AQ1 | unknown | 原文未载（父母/原生家庭是否介入施压） |
| 2 | P0-01 | AQ2 | unknown | 原文未载（与分开配偶是否仍有联系/经济往来） |
| 3 | P0-02 | AQ1 | unknown | 原文未载；窗口 2015–2025 原文未覆盖收入结构 |
| 4 | P0-03 | AQ1 | unknown | 原文未载（妇科病确诊前是否有婚姻/家庭重大变故） |
| 5 | P0-03 | AQ2 | unknown | 原文未载（发病期间是否有心脏/血压/心慌症状） |
| 6 | P0-04 | AQ1 | yes | 原文 L398「癸未年刚入乙运坐牢，因非法集资而没收产财。判刑十年。现已出狱。」（`source_mentions_answer=true`） |

> 答案口径：`answer_source=source_outcome` 才允许填 yes/no 并必须带 `source_ref`+`quote`；原文未载一律 `unknown` / `not_in_source`，交命主回答，Agent 不代答。因此 `anchor_a_note` 与 `state_note` 不再一边禁代答、一边据 L398 代答。

## 3. P0 gate

| 项 | 结果 |
|---|---|
| 字段完整 | 4/4 |
| 事实/引文 0 错 | 0 错；卡级 `seeded_error` 4 卡 × 4 项 = **16/16**（`card_scan`）；包级 fixture **self_test 20/20**（`mode=self_test`，**非第三方植入错误**） |
| ≤2 题/卡 | 4 卡：2/1/2/1，均 ≤2（合计 6） |
| 人 ≤5 分钟/卡 | 未实测；6 题均为是非题，阅读原文后作答 |
| 方向 claim 档位 | A=3 / B1=7 / B2=0 / C=1（合计 11；去重前 12） |
| A 自动占比（按 claim） | **3/11 = 27.3%**（去重前 3/12 = 25.0%），只报告、不调 gate |
| A 精度（A 档三条件自检） | 3/3 = 100%（固定克/生/化/墓 + engine 与原文同向 + 三条互补不竞争） |
| 类外自动发射 | 0 |
| 伪造/泄漏 | 0 |
| 第三方重推 ≥90% | **T-197c 重跑待判**（r2 已按 T-197c 的 D01–D20 逐项修，见 §4） |

**A 率与 A 精度分开**：A 率 = A claim / 全部方向 claim（3/11）；A 精度 = A claim 中满足 A 档定义的比例（3/3）。两者都不含「按卡计数」（3/4 = 75% 是错误口径，已废弃）。

## 4. 对 T-197c 20 项差异的处理

| 编号 | 问题 | 处理 |
|---|---|---|
| D01 | e015 理由把月支 M.b 写成夫妻宫 | 已修：改为「月支寅(M.b)↔日支申(D.b)」，并注明 M.b 不是夫妻宫 |
| D02 | AQ2 `discriminates` 未含被消去的 dc2 | 已修：`discriminates=[dc1,dc2,dc3]`，与 elimination 消去项一致 |
| D03 | P0-01 st1/st2 `anchored_by=AQ1`（AQ1 不区分它们） | 已修：留空，并加 `anchored_by_note` 说明本卡无 state 锚点题 |
| D04 | P0-02 `outcome_quote` 是婚姻句，与事业域错配 | **未修（见 §5）** |
| D05 | P0-02 st1/st2 `anchored_by=AQ1` | 已修：留空 + 说明 |
| D06 | P0-02 `dc3`(C) 未被 AQ1 覆盖，方向层永不唯一 | 已修：`selection_rules` 明确 C 档不参与选择 → 幸存集为空 = `needs_anchor` |
| D07 | P0-03 `dc3` 与 `rs1` 同源重复 | 已修：只保留救应层 `rs1`，方向层移除 `dc3`，原记录完整存于 `dedup[0].original_record` |
| D08 | P0-03 unknown 下唯一幸存 dc3 但 `selected=null` | 已修：`dc3` 不再在方向层，AQ1 unknown 后 survived=[]，null 可由表复现 |
| D09 | P0-03 AQ2 yes 只 downgrade st1 | 已修：`eliminate=[st1]`、`downgrade=[]`，elimination 表同步 |
| D10 | P0-04 三个 A 候选并存却单填 `selected_option=dc3` | 已修：`selected_option=null` + `selected_claims=[dc1,dc2,dc3]` + 逐 claim `claim_id/claim_selected` |
| D11 | P0-04 `state_selected=败` 不能由 `anchor_a=[]` 复现 | 已修：`anchor_a` AQ1=yes（源 L398）；st3 为 C 档定义口径不参与成败选择 → st2 唯一 |
| D12 | `anchor_a_note` 禁代答，`state_note` 却据 L398 代答 | 已修：统一为「有源才填、无源记 unknown」，`state_note` 与 `anchor_a` 同源 |
| D13 | `anchor_a`/`state_scope`/`pending`/`not_auto_selected`/`selection_source` 互相矛盾 | 已修：`state_scope=claimed`、`pending=null`、`selection_source=engine_fixed_multi`、`decision_by=anchor_fact`，`tier_reason` 去掉 `pending:state_anchor` |
| D14 | P0-04 st1/st2 `anchored_by=ED1` 悬空 | 已修：改 `anchored_by=[AQ1]`（AQ1 即 state 题），`state_anchor_note` 改写并说明 ED1 已废止 |
| D15 | 卡级 `decision_by=engine_fixed` 名不副实 | 已修：`decision_by=anchor_fact` + `decision_by_layer` 分方向/状态/救应 |
| D16 | report 记方向 C，卡 `direction_tier=B1` | 已修：本报告分「方向档/状态档/selected」三列，与卡字段同名字段对齐 |
| D17 | seeded 16/16 与 20/20 打架 | 已修：两个口径分列（卡级 card_scan 16/16；包级 self_test 20/20），并标注「非第三方植入」 |
| D18 | report 的 5 unknown / 1 yes 未落进卡 `anchor_a` | 已修：§2 六条与 4 卡 `anchor_a` 逐条一致（verify 互检） |
| D19 | P0-04 st3 是定义口径却当 state 候选、不被 AQ1 消去 | 已修：保留候选（不删）+ `selectable=false` + `tier_note`，C 档不参与选择 |
| D20 | P0-01 `outcome_note` 子女转述弱于 L33 | 已修：改为 L33 原文「一个孩子也没落着」 |

## 5. 仍未修 / 风险（不掩盖）

1. **D04 未修**：P0-02 的 `outcome_quote` 仍是 L25 的婚姻句。改它会牵动 `source_quote_validation` 与 `engine_validation.aggregate` 的引文计数，属内容层而非选择层，本轮不动；已记入 `tasks/T-197d/BRIEF.md` 交 T-197c/中枢定夺。
2. **A 率 3/11 = 27.3% 未达 ≥50% gate**：这是案例数据问题（4 例的 material edge 多为冲/合/穿/刑），不是管道问题；**没有为此删候选或放宽断言**。
3. **6 题中 5 题仍 unknown**：需命主/人类回答；`anchor_a` 已留位，格式与 `answer_source` 枚举见卡内 `field_semantics`。
4. **`tasks/T-197/build_p0_cards.py` 未同步**：r2 修正由 `tasks/T-197d/patch_p0_cards.py` 施加，重跑 T-197 builder 会覆盖 r2；下游请按 build → patch 顺序复现。

## 6. 结论

- **P0 管道通过**：A 按 claim 自动、B1 锚点、C 留白、引文/地址校验、seeded 拦截都能跑通；`verify.py` 退出 0。
- **`selected` 现在可由表复现**：4 卡的方向层在 `anchor_a` 下幸存集均为空（P0-04 为三条互补 A claim），状态层 P0-01/02 无锚点、P0-03 全消、P0-04 唯一 → `selected` 取值与 `selection_rules` 一一对应。
- **C 率 3/4 是数据问题，不是管道问题**：教材案例只给盘与结论，没给「命主已发生事实」，锚点题只能 unknown。
- **P1 必须用带已知事实的真实案例**；否则 C 必然 >50%，P1 的 C≤50% 会直接 kill，且 kill 的是「数据没有事实」，不是产品能力。
- 下一步：T-197c 按 r2 重推；T-198 真实案例录入 + P1；P2 只做预注册。
