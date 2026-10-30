# T-197c r2 · 第三方重推简报

- 结论：**4/4 卡 selected 可复现（100% ≥ 90%）→ 建议 P0 gate 通过（按 selected 复现口径）**。
- 隔离：只读 4 卡 r2、`META/p0-report-v1.md`、4 段 `sources/duan/` 原文、`engine.cli`；未读 answers/golden/scoring，未用 r1 产物做结论，未跑评分器，未改卡/engine/保护区，未做 git 写。
- 方法：CLI 跑 4 盘 `all --json`；按每卡 `anchor_a` + `anchor_q.elimination` + `selection_rules` 独立重算；每条引文用 `path:Ln` 做逐字子串校验；地址/边/十神对照 CLI `chart/relations/duan_zuogong`。

## 1. 改动文件

| 文件 | 动作 |
|---|---|
| `META/p0-thirdparty-v2.json` | 新增（逐卡重推/差异/证据，40 KB） |
| `tasks/T-197c/BRIEF-r2.md` | 新增（本文件） |
| `tasks/T-197c/STATUS.md` | 追加 r2 执行记录与状态 |
| `META/p0-cards-v1.json`、`META/p0-report-v1.md`、`sources/`、`engine/` | 未改 |

## 2. 原始输出

### 2.1 4 卡重推

| 卡 | 域 | selected_option | state_selected | selected_claims | 重推 |
|---|---|---|---|---|---|
| P0-01 | 婚 | null | null | [] | ✅ 一致 |
| P0-02 | 事业 | null | null | [] | ✅ 一致 |
| P0-03 | 健康 | null | null | [] | ✅ 一致 |
| P0-04 | 财 | null | **败** | **[dc1,dc2,dc3]** | ✅ 一致 |

- 8/8 层选择（direction/state × 4 卡）复现；4/4 `selected_option`、4/4 `state_selected`、4/4 `selected_claims`、4/4 `direction_survivors`/`state_survivors` 与卡一致。
- 事实层：chart_id 4/4；四柱/性别 4/4；十神 claims **34/34**；material edges **9/9**；direction edge refs **11/11**（9 条 edge + 2 条 duan candidate）；引文 **83/83** 逐字命中（P0-02 `rs1` 无引文，`quote=null`，非校验失败）。
- CLI 4 条命令全部退出码 0。

关键重算：
- P0-01：AQ1/AQ2 均 unknown → direction 0 幸存；无 state 锚点 → state 2 幸存 → 两层 null。
- P0-02：AQ1 unknown 消 dc1/dc2；dc3 为 C 不参与 → direction 0 幸存；无 state 锚点 → state 2 幸存 → 两层 null。
- P0-03：dc3 已 dedup 并入 rs1；AQ1 unknown 消 dc1/dc2 → direction 0 幸存；AQ2 unknown 消 st1/st2 → state 0 幸存 → 两层 null。
- P0-04：direction 无锚点，三条 A claim 全存活 → `selected_option=null`/`selected_claims=[dc1,dc2,dc3]`；state 可参与={st1,st2}（st3 为 C/selectable=false），AQ1=yes 消 st1 → 仅 st2 → **败**。

### 2.2 P0-04 st3 语义判断（重点）

**判定：成立。** 卡把 st3 定为 `state=null / tier=C / selectable=false`，AQ1=yes 消 st1 后 st2 唯一=败，这个语义可以成立；**state 不应退回 null/C**。

理由：
1. st3 自身 `state=null`、`result=needs_anchor`，不主张成/败，不能成为 state 层的唯一 selected 值。
2. 其内容「财弱官旺、官当财看」是 L392 的**定义句**；同句结尾「所以是个富命」才是 st1 的成局主张。定义句回答「财指什么」，不回答「守不守得住」。
3. 包内已有明文规则：`selection_rules.excluded_tiers=[C]`、`c_tier_never_selected`；`field_semantics.layer_tier.C`「C 档在本包等于不参与选择」；`schema_compat.extensions`「state_candidates[].selectable / tier_note：C 档定义口径候选不参与成败选择」。st3 的 `tier_note`/`selectable=false` 与这三条一致。
4. 机械重算：state eligible={st1,st2}；AQ1=yes 只消 st1；survivors={st2}；st2.result=败 → `state_selected=败`，满足 `selected_must_equal_survivor`。
5. 因此这不是「为凑唯一而删候选」：st3 本来就不携带成/败值；把它计入会制造一个没有 outcome 的伪竞争者，反而违反 `unique_rule` 的语义。

保留意见：
- **C 标签属扩展借用**：基准 C=无源/冲突，而 st3 有源（L392）、无冻结规则冲突。建议未来 schema 改 `kind=definition/non_outcome` + `selectable=false`，不改当前 selected。
- **若中枢不承认该扩展**、把 st3 当真实 state 读法：AQ1=yes 不消 st3 → survivors={st2,st3} → `state_selected=null`、`state_scope=candidate_only`。此时不是退回 C 档结论，而是「无唯一幸存」；不建议把 `state_tier` 记成 C（AQ1 仍是 B1 锚点，且 C 的基准定义是无源/冲突）。
- **st1/st2 时间序列**：原文是「富命 → 发财五年/4 亿 → 主凶 → 坐牢/没收」的先富后破，不是同一时点互斥二值。按卡声明的「最终成败」口径，AQ1=yes 消 st1 → 败成立；若按「一生轨迹」口径，富与破可并存，state 应为多 claim 或 null。属口径风险，不改当前 selected。

### 2.3 差异清单（12 项，均不改变 selected）

| ID | 卡 | 严重度 | 差异 | 影响 |
|---|---|---|---|---|
| D-R2-01 | P0-01 | low | root `anchor_questions` AQ2 `discriminates=[dc1,dc3]`，卡内已 `[dc1,dc2,dc3]`（D02 只修了卡内副本） | 当前 unknown 下 selected 不变；按 root 校验会报 D02 未修 |
| D-R2-02 | P0-03 | medium | root AQ2 `elimination[yes].eliminates=[]`（旧 downgrade 口径），卡内已 `[st1]`（D09 只修了卡内副本） | 当前 unknown 下 null 不变；**未来 AQ2=yes 会复现分叉** |
| D-R2-03 | P0-02 | medium | `source.outcome_quote` 用 L25 婚姻句（D04 已知未修），事业结局无逐字引文 | selected 不变；证据层缺陷 |
| D-R2-04 | P0-02 | medium | dc2 称「原文未点名哪一个财」，但同卡 dc1 引 L27「戊就是做工的重要的字」——原文实际点名戊 | selected 不变；dc2 竞争地位/B1 设计必要性存疑 |
| D-R2-05 | P0-04 | low | st2 `decision_by=expert_single_choice`，但 `anchored_by=[AQ1]`、`state_decision=anchor_fact`、`expert_decision=null`（ED1 残留） | selected=败 不变；字段语义矛盾 |
| D-R2-06 | P0-04 | low | `metrics.state_candidates_selectable=9`，但 C 档 state 候选有 2 个（P0-01 st3、P0-04 st3），按 `excluded_tiers=[C]` 应为 8 | selected 不变；指标口径误导 |
| D-R2-07 | P0-03 | low | st2 `basis_text` 把 L131「午得寅生，旺，所以不得心脏病」写成「本造」，L131 实为另一造（乾 乙戊丙己 / 卯寅午丑） | selected 不变；证据归属错误 |
| D-R2-08 | P0-04 | medium | dc1 只取月支丑 M.b；原文「月时丑官都入辰墓」含时支丑 H.b，engine 也有 墓用[D.b,H.b]，H.b 未入 palaces/material_edges(e011)/dc1 | selected 不变；方向 claim 覆盖不完整，A 3/11 可能少计 |
| D-R2-09 | P0-04 | medium | st3 标 C，但 C 的基准定义是「无源/冲突」，st3 有源；属 `schema_compat` 扩展借用 | 不影响「不可选」判断；建议改 definition/non_outcome |
| D-R2-10 | P0-04 | low | AQ1 唯一非 unknown 答案是 source_outcome（L398 癸未年/2003），`fact_window=2010-01..2025-12`；卡有 `fact_window_note` 但非窗口内命主事实 | selected 不变；P1 需补命主事实 |
| D-R2-11 | P0-03 | low | st1/st2 的 `result` 都是「病」；AQ2 只区分病位（妇科/心脏），不区分病/不病 | 当前 null 不变；state 层实为病位归属层 |
| D-R2-12 | P0-04 | medium | st1 成局/富命 vs st2 破局/败，原文是先富后破的时间序列，不是同一时点互斥二值 | 按卡「最终成败」口径 败 成立；按「一生轨迹」口径应 null/多 claim |

### 2.4 缺证据（6 项）

| ID | 卡 | 缺什么 |
|---|---|---|
| M-01 | P0-02 | 事业结局引文（L25 是婚姻句；正师/副军叙述无逐字 outcome_quote） |
| M-02 | P0-02 | dc2（己制癸）的原文/事实依据；L27 已点名戊为工神 |
| M-03 | P0-04 | 时支丑 H.b 的入墓/破库证据（L392 月时两丑、engine 墓用[D.b,H.b]、e011） |
| M-04 | P0-03 | 本造专属的心脏/血压判据（st2 引 L123 同章病性 + L131 他造判词） |
| M-05 | P0-04 | 窗口内命主事实（AQ1 唯一答案是 2003 原文结局，窗口 2010-2025） |
| M-06 | all | 逐卡独立的 seeded 注入项（4 卡复用同一组 fixture；HY:L15 只在 P0-01 源内） |

完整字段、逐条证据与 `fact_checks` 见 `META/p0-thirdparty-v2.json`。

## 3. 未完成与风险

- **未跑评分器**（按要求）；未实测人工 ≤5 分钟/卡。
- **D04 未修**：P0-02 `outcome_quote` 仍是 L25 婚姻句；本轮只读复核，不改卡，交 T-197d/hub 定夺。
- **root `anchor_questions` 未同步**（D-R2-01/02）：当前 selected 不受影响，但 P0-03 AQ2 未来答 yes 会「卡内选 st2 / root 保留 st1」分叉；P1 前应同步。
- **P0-02 dc2 论证矛盾**（D-R2-04）：原文 L27 点名戊，dc2 的「未点名」说法不成立；若中枢按原文收敛，方向层可能应选 dc1，而不是 null。
- **P0-04 H.b 覆盖缺口**（D-R2-08）：不影响 selected，但 A 3/11 与「官入辰墓」claim 的覆盖面需定夺。
- **st3 C 标签**（D-R2-09）：语义成立，但标签是扩展借用；若中枢收紧 C 定义，fallback 为 `state_selected=null` + `state_scope=candidate_only`，**不是**把 state 记成 C 档结论。
- **Gate 口径**：按 selected 复现 4/4=100%；若把「任一非选择性差异」也算该卡不一致，则 zero-difference cards=0/4（4 卡都有至少 1 项元数据/证据差异）。建议 gate 按 selected 复现计，差异列入 P1 前清理。

## 4. 下游须知

1. **P0 gate 建议 pass**（selection-level 4/4=100%）；差异不是「重推不一致」，但 12 项应记录，D-R2-02/03/04/08 建议 P1 前处理。
2. **不要用 root `anchor_questions` 复算 P0-01 AQ2 / P0-03 AQ2**：卡内 `anchor_q` 才是 r2 口径；root 两份副本仍是旧值（D02/D09 未真正同步）。
3. **不要把 st3 当 state 赢家**：它是「官当财看」的定义口径，`state=null`；当前 `state_selected=败` 来自 st2，不是 st3。
4. **P0-02 不要引用 L25 作为事业结局**：它是婚姻/子女句；事业结局只能引用 `outcome_note`（正师/副军）或补新的逐字引文。
5. **P0-04 方向层是 multi-claim**：三条 A claim 互补，不是三选一；A 计数 3/11 的 11 是否应含时支丑，需 hub 定夺。
6. 本轮未改卡、未改 engine、未做 git 写；所有结论可由 `META/p0-thirdparty-v2.json` 的 `recompute`/`fact_checks` 复现。
