# T-197 BRIEF · P0 4 例 Agent 卡 + 候选（B1 锚点消歧版 / agent-candidate-set v1）

- 状态：🟡 待中枢验收（`pending=anchor_q`，方向未选定）
- 执行者：子代理（T-197 P0 Agent）
- 任务卡：`tasks/T-197/PROMPT.md`；口径追加：中枢 2026-10-30 三条消息（B→B1/B2、A 只固定类、锚点事实题）
- 规格：`docs/specs/fact-evidence-pack-v1.md`、`docs/specs/actor-rules-v1.md`；**T-196 三份规格在本卡执行途中落盘**，字段按 `docs/specs/agent-candidate-generator-v1.md §7`（`agent-candidate-set/v1`）对齐
- 产物：`META/p0-cards-v1.json`、`META/p0-case-packets-v1.md`、本 BRIEF、`STATUS.md`

## 0. 一句话

选 4 例段派真实命例（婚/事业/健康/财各 1，与 dev-20/fresh-40/anchor-60/holdout-20/旧 3 卡零重叠），
每例 3 个方向候选 + 1–2 个**已发生事实的是非题**，全部候选过 engine 地址/边/十神/引文校验（20 个植入错误 fixture 全拦）；
**没有做「人选候选」版**，首版即 B1 版；6 个待答单元全部留空，B2 未触发。

## 1. 改动文件

| 文件 | 类型 | 说明 |
|---|---|---|
| `META/p0-cards-v1.json` | 新增 | 4 卡 / 12 方向候选 / 10 状态 / 4 救应 / 6 锚点题 / 校验 / `schema_compat` |
| `META/p0-case-packets-v1.md` | 新增 | 每例一页人读包 + 关键选择清单 + 答案回收表 + v2 对齐说明 |
| `tasks/T-197/BRIEF.md` | 新增 | 本文件 |
| `tasks/T-197/STATUS.md` | 修改 | 状态 + Blockers + Execution Log |
| `tasks/T-197/build_p0_cards.py` | 新增工具 | engine 快照 + `sources/` → JSON，含 address/edge/ten_god/quote/seeded_error 校验与 candidate-set 转换 |
| `tasks/T-197/render_packets.py` | 新增工具 | JSON → md，避免手抄地址/边号失真 |
| `tasks/T-197/verify.py` | 新增门禁 | 仅标准库；独立重读 `sources/` 复核引文；退出码表达验收 |
| `tasks/T-197/_engine/*.json`、`summary.txt` | 新增快照 | 8 次 `engine.cli`（all/relations × 4 盘）原始输出 |
| `tasks/T-197/_exclusion.json` | 新增工作件 | 5 个排除集的 `case_id/four_pillars/gender`（133 个四柱集合），仅查重 |

未改：`engine/**`、`tests/**`、`sources/**`、`META/project-state.json`、任何 `PROMPT.md`、阈值、答案。
未做：git 写、评分器、方向自动承诺。

## 2. 原始输出

### 2.1 构建（`build_p0_cards.py`，退出码 0）

```json
{
 "case_count": 4,
 "domains": ["career", "health", "marriage", "wealth"],
 "direction_candidates": 12,
 "candidate_tiers": {"A": 3, "B1": 8, "B2": 0, "C": 1},
 "candidate_tier_share": {"A": 0.25, "B1": 0.6667, "B2": 0.0, "C": 0.0833},
 "anchor_questions": 6,
 "b2_expert_decisions": 0,
 "engine_validation_failures": 0,
 "seeded_error_pass": true
}
```

```
wrote E:\Git hub\mangpai-fusion\META\p0-cards-v1.json
failures: 0
```

### 2.2 验收门禁（`tasks/T-197/verify.py`，退出码 0）

```
[ok]  schema=p0-cards/v1 task=T-197
[ok]  例数 4 ∈ [3,5]
[ok]  覆盖 婚/事业/健康/财
[ok]  逐卡结构/档位/引文校验完成（锚点题 6）
[ok]  4 盘与 133 个排除集四柱零重叠
[ok]  metrics: A=3 B1=8 B2=0 C=1 anchor_q=6 b2_decision=0

PASS: p0 卡片包满足 T-197 验收项（不自动选定 / A 仅固定类 / 引文逐字 / 零排除集重叠）
```

### 2.3 校验计数

| 项 | 结果 |
|---|---|
| address | 26/26 pass |
| edge / 做功候选 | 12/12 pass（边 kind+members 一致；`墓用/生泄用` 按 `duan_zuogong.candidates` 的 mode+members+actor 命中） |
| ten_god | 26/26 pass（含藏干十神） |
| 候选层引文逐字 | 26/26 pass |
| 原文/宫位引文逐字 | 24/24 pass（合计 50 条） |
| 逐卡 seeded_error（card_scan） | 16/16 拦截（假地址/假边/错十神/篡改引文各 1，每卡） |
| self_test（20 fixture） | 20/20 拦截（5 地址 / 5 边 / 5 十神 / 5 引文） |
| 校验失败候选 | 0 |

### 2.4 4 例与档位

| 卡 | 域 | 四柱（性别） | chart_id | direction_tier | 卡 tier / pending | 候选（档） | 待答 |
|---|---|---|---|---|---|---|---|
| P0-01 | 婚 | 辛巳 庚寅 甲申 庚午（乾） | `cf-daef938eab28eb49e1b8` | B1 | B1 / anchor_q | dc1 B1 / dc2 B1 / dc3 B1 | AQ1、AQ2 |
| P0-02 | 事业 | 戊戌 癸亥 乙巳 己卯（乾） | `cf-1627557db9bf35baf387` | B1 | B1 / anchor_q | dc1 B1 / dc2 B1 / dc3 C | AQ1 |
| P0-03 | 健康 | 壬寅 庚戌 己丑 庚午（坤） | `cf-0075a9941ae6f079f4b9` | B1 | B1 / anchor_q | dc1 B1 / dc2 B1 / dc3 B1 | AQ1、AQ2 |
| P0-04 | 财 | 乙巳 己丑 壬辰 辛丑（乾） | `cf-4d8fe4fe1b354d973a7b` | A | B1 / anchor_q | dc1 A / dc2 A / dc3 A | AQ1（state） |

A 档 3 条均为固定类：P0-04 的 `墓用`(辰→丑)、`ke`(辛→乙)、`生泄用`(巳→丑)。
冲/合/穿/刑/破一条也没有进 A（P0-01 dc1–dc3、P0-03 dc1–dc3 全 B1；P0-02 dc3 冲为 C）。

## 3. 未完成与风险

1. **A 档占比 25%（3/12）未达 T-196 P0 gate ≥50%**。4 例的 material edge 多是对称关系；冲/合/穿不得 A（中枢追加），固定类只剩 P0-04 的墓/克/生。
   P0-04 的方向层虽是 A，但成败层有冲突（原局富 vs 岁运破），按 v2 §5.6 卡级取 B1。是否调 gate、改分母（只看固定类候选）或补固定类案例，由中枢定，本卡不调阈值。
2. **B2 触发 0（B2 / 全部 B 单元 = 0.00%）**。先前把 P0-04 的「原局富 vs 岁运破」当作 B2 是**误用**：v2 §5.3 的 B2 只用于方向候选间无可观测事实可分；该冲突属成败层，已改为 state 锚点题（`source_mentions_answer=true`，因原文已写坐牢没收）。
3. **本包是 `agent-candidate-set/v1` 的 pending 形态，不是可交付的 `analysis-card/v2`**：v2 的 `t1–t5`、`statement_claims`、`selected_*` 都要求先有选择，而 T-197 明令不选定、`pending=anchor_q` 前不得填。
   两处口径冲突已写入 `schema_compat.known_conflicts`：①v2 的 A 要求已选，T-197 禁止代选；②v2 的 C 也用 `selected_option=null`，与「待自动确认的 A」同形。
4. **P0-01 / P0-03 的「单侧施力」依赖结果句或计数句**（`evidence_gap=same_page`）：`夫宫被冲克`＋`寅多作用一次`、`伤了时上禄`＋`丑午穿`；两句都未在同句给出施动主语。是否够格作方向依据，留中枢/第三人裁，未升 A。
5. **锚点题与原文后续事实的可推测性**：原文写了结局（五婚、子宫癌、坐牢）。本卡题目刻意避开原文已写事实（原生家庭是否介入、分开后是否仍有往来、收入结构、发病前家庭变故、心脏症状），`source_mentions_answer` 仅 P0-04 为 true。
6. **P0 gate 的「第三方重推 ≥90%」「人 ≤15 分钟/卡」尚未测**：需要 T-197b 在干净会话按 `verify.py` + 原文重推；本卡只保证可回查性。
7. 四柱输入无出生时刻：`engine.input_limitations` 明确不起运、不给大运公历年份；全部 `dayun_index=null`、`liunian_year=null`，岁运句只引用不作判。
8. 案例来自段派出版物中的真实命例，**后续事实只备查**；全部候选 `is_conclusion=false`，不据此反推断语。

## 4. 下游须知

1. **T-197b 填答流程**：填 `anchor_a`（每卡数组，`{qid,answer,answered_by,answered_at,note}`），按每题 `elimination` 机械淘汰：
   恰剩 1 条 → `selected_option` = 幸存、`selection_source=human_fork`、`pending=none`；剩 0 条 → C（`anchor_inconsistent`）；2 问后仍 >1 → C（`anchor_insufficient`）；`unknown` 无法收敛 → C（`anchor_unknown`）。
   **不要**让人直接选方向。
2. **C 档不要补源**：P0-02 dc3（亥巳冲）与各卡 C 项（P0-01 st3/rs1、P0-02 rs1、P0-04 st3/rs1）在拿到原文定向句前保持 `needs_anchor`，不得用五行或十神反推。
3. **A 档（P0-04 方向层）**：三条固定类事实可进事实层；但不得写成「富/穷」「守得住/守不住」。若 T-197b 确认方向层 A，卡级 tier 仍由成败层决定。
4. **`agent_top1` 未冻结**：生成器 §8.2 的 B1 lift 基线需要另卡在看答案前冻结；本包刻意未给，避免锚定。
5. **重跑**：`build_p0_cards.py` → `render_packets.py` → `verify.py`（应退出 0）。`_engine/*.json` 是 2026-10-30 快照；engine 变更后需重跑快照再重建，否则 `chart_id`/edge_id 可能漂移。
6. **查重口径**：`_exclusion.json` 只含 `case_id/four_pillars/gender`（F20 20、PF 40、A60 60、P1-H 20、旧 3 卡 3）；未读任何答案、`target_relation`、`expected_evidence` 或 `p1-system-run*`。
