# 分析卡 v2 · 规格（候选层 + 锚点消歧 + 引擎校验）

> 任务：`tasks/T-196/PROMPT.md`；状态：🔵 Ready（规格，不写代码、不跑盲测、不改保护区）
> 关系：扩展现有卡 v1（`docs/specs/single-chart-analysis-v1.md`），**不改 v1 文件**；字段名以本文件为准，生成器与目标文档必须引用同一套字段。
> 依据：A+ v1.3 方向产品 kill（`docs/reviews/t191-a-plus-verdict-v1.md`）；R-tool 事实/检索层（`docs/specs/fact-evidence-pack-v1.md`）；actor 规则表（`docs/specs/actor-rules-v1.md`）；中枢 2026-10-30 两次追加修正（A 只固定类；B 拆 B1/B2；P0 只验管道）。
> 关联文档：[`docs/goals/first-principle-agent-first-v1.md`](../goals/first-principle-agent-first-v1.md)（目标/gate）、[`docs/specs/agent-candidate-generator-v1.md`](agent-candidate-generator-v1.md)（生成器）。

## 0. 一句话

卡 v2 仍是五元组卡，但方向/成败/救应三层改成**候选集**：方向 `direction_candidates[]`、成败 `state_candidates[]`、救应 `rescue_candidates[]`；每层 0–3 条候选（有多个有源备选时 2–3；单条/零条须写明理由），每条带 `basis` / `source_ref` / 逐字 `quote` / `decisive` / `conflict_with`；选择由 `tier ∈ {A, B1, B2, C}` 与 `decision_by ∈ {engine_fixed, anchor_fact, expert_judgment, needs_anchor}` 决定。**A 只给固定克/生/化/墓；冲/合/穿/刑一律 B1/B2/C。**

## 1. 与 v1 的关系

### 1.1 保留

- 五元组 `t1_local_image` / `t2_role_and_force` / `t3_outcome` / `t4_scene_and_activation` / `t5_dual_anchor`；
- `snapshot{chart_id, dayun_index, liunian_year}` 一卡一快照；
- `statement` / `boundary` / `confidence` / `unknowns`；
- v1 的 `L01`–`L21` 中与「事实可回查、地址、引文、禁止预测」相关的条款（映射见 §9）；
- `rescue_judged=未判`（G5：盲派域无救应事实；除非同时有救应原语 + 外部审计编号）。

### 1.2 新增

| 新增字段 | 作用 |
|---|---|
| `tier` | A / B1 / B2 / C |
| `decision_by` | engine_fixed / anchor_fact / expert_judgment / needs_anchor |
| `provenance` | 决策来源、生成器版本、CLI、`source_refs`；`kind` 必须等于 `decision_by` |
| `direction_candidates[]` | 1–3 条方向候选（A 固定类可为 1；B1 为 2–3；B2 为 1–3；C 为 0–3） |
| `selected_option` / `selection_source` | 方向选择与来源；`selection_source ∈ {agent_auto, human_fork, needs_anchor}` |
| `state_candidates[]` / `selected_state` / `state_selection_source` | 成败候选与选择 |
| `rescue_candidates[]` / `selected_rescue` / `rescue_selection_source` | 救应候选；v2 仍不自动判「已判」 |
| `anchor_q[]` / `anchor_a[]` | B1 的 1–2 个「命主已发生事实」是非题与答案 |
| `expert_decision` | B2 专家单选或 `needs_anchor`，带 `source_ref` + `quote` |
| `anchor_request` | C 的缺口与解锁条件 |
| `engine_validation` | address / edge / ten_god / quote / seeded_error 五检 |
| `statement_claims[]` | 逐句 claim + source_ref + quote；无源断言 = 0 |
| `card_status` | `valid` / `void`；伪造边/地址/十神/引文直接 void |

### 1.3 变化（不是放宽）

- v1 要求每卡都有 `direction`/`state`；v2 允许 `state_scope="not_claimed"` / `rescue_scope="not_claimed"`，但前提是 **statement 不得声称该层**，且 `unknowns` 记录缺口。这不是「少写一层」，而是「不判就不说」。
- v1 的 `direction_known=false` 仍适用于 `mutual` 或无选择；v2 把「谁作用于谁」放进候选层，`t2` 的 `direction`/`actor`/`target` 只是**已选项的投影**，不是新事实。
- v1 的 `rescue_judged=已判` 仍被禁止；v2 的 `rescue_candidates` 只是候选，不是化解结论。

## 2. 卡 schema

### 2.1 JSON 骨架

```json
{
  "schema": "analysis-card/v2",
  "card_id": "CARD-001",
  "case_id": "CASE-001",
  "snapshot": {"chart_id": "cf-...", "dayun_index": null, "liunian_year": null},
  "card_status": "valid",
  "tier": "B1",
  "decision_by": "anchor_fact",
  "pending": "none",
  "tier_reason": ["direction:anchor_conflict", "state:selected", "rescue:not_claimed"],
  "provenance": {
    "kind": "anchor_fact",
    "generator": "agent-candidate-generator/v1",
    "engine_cmd": "python -m engine.cli all --pillars \"...\" --gender 乾 --json",
    "theory_cmd": "python -m tools.query_theory --query \"...\" --json",
    "generated_at": "2026-10-30T00:00:00+08:00",
    "source_refs": ["sources/duan/....md:L000"],
    "anchor_q_ids": ["Q1"],
    "expert_id": null
  },
  "t1_local_image": {
    "palace": "day",
    "addrs": ["D.b", "H.b"],
    "ten_gods": ["正印", "偏印"],
    "relations": [
      {"kind": "chong", "edge_id": "e015", "members": ["D.b", "H.b"], "group": null, "completeness": null}
    ]
  },
  "t2_role_and_force": {
    "tiyong": {"actor_role": "体", "target_role": "体"},
    "binzhu_layer": 3,
    "direction_candidates": [
      {
        "option_id": "D1",
        "claim": {
          "relation": "chong",
          "direction": "actor_to_target",
          "members": ["D.b", "H.b"],
          "actor": "D.b",
          "target": "H.b"
        },
        "basis": [
          {"kind": "engine_edge", "ref": "e015", "note": "chong[D.b,H.b]"},
          {"kind": "source_directive", "ref": "sources/duan/....md:L000", "note": "施动句"}
        ],
        "source_ref": "sources/duan/....md:L000",
        "quote": "<逐字原文占位>",
        "decisive": true,
        "conflict_with": ["D2"],
        "conflict_class": null,
        "engine_note": null
      },
      {
        "option_id": "D2",
        "claim": {
          "relation": "chong",
          "direction": "mutual",
          "members": ["D.b", "H.b"],
          "actor": null,
          "target": null
        },
        "basis": [
          {"kind": "engine_edge", "ref": "e015", "note": "chong[D.b,H.b]"},
          {"kind": "source_directive", "ref": "sources/duan/....md:L000", "note": "互冲句"}
        ],
        "source_ref": "sources/duan/....md:L000",
        "quote": "<逐字原文占位>",
        "decisive": true,
        "conflict_with": ["D1"],
        "conflict_class": null,
        "engine_note": null
      }
    ],
    "selected_option": "D2",
    "selection_source": "human_fork",
    "direction": "冲",
    "direction_known": false,
    "actor": null,
    "target": null
  },
  "t3_outcome": {
    "state_scope": "selected",
    "state_candidates": [
      {
        "option_id": "S1",
        "state": "破局",
        "basis": [
          {"kind": "edge", "ref": "e015", "note": "目标受冲"},
          {"kind": "source_rule", "ref": "sources/duan/....md:L048", "note": "结构判据"}
        ],
        "source_ref": "sources/duan/....md:L048",
        "quote": "<逐字原文占位>",
        "decisive": true,
        "conflict_with": [],
        "engine_note": null
      }
    ],
    "selected_state": "S1",
    "state_selection_source": "agent_auto",
    "state": "破局",
    "rescue_scope": "not_claimed",
    "rescue_candidates": [],
    "selected_rescue": null,
    "rescue_selection_source": null,
    "rescue_judged": "未判"
  },
  "t4_scene_and_activation": {
    "scene": "<1–2 句落事，不含预测>",
    "scene_refs": ["CARD-000"],
    "activation": {
      "kind": "none_observed",
      "against_addr": "D.b",
      "suiyun_addr": null,
      "edge_id": null,
      "condition": "<条件描述>",
      "path": "relations.edges[scope=dayun|liunian, members∋D.b]"
    }
  },
  "t5_dual_anchor": {
    "address_anchor": {"edge_ids": ["e015"], "addrs": ["D.b", "H.b"]},
    "text_anchor": {"entry_id": "M1-D-298", "path": "sources/duan/....md", "line": 48},
    "candidate_anchors": [
      {"option_id": "D1", "source_ref": "sources/duan/....md:L000", "quote": "<逐字原文占位>"},
      {"option_id": "D2", "source_ref": "sources/duan/....md:L000", "quote": "<逐字原文占位>"}
    ]
  },
  "engine_validation": {
    "snapshot": {"chart_id": "cf-...", "dayun_index": null, "liunian_year": null},
    "address": {"status": "pass", "checked": ["D.b", "H.b"], "failures": []},
    "edge": {
      "status": "pass",
      "checked": [{"edge_id": "e015", "kind": "chong", "members": ["D.b", "H.b"]}],
      "failures": [],
      "reason": null
    },
    "ten_god": {
      "status": "pass",
      "checked": [{"addr": "D.b", "ten_god": "正印"}, {"addr": "H.b", "ten_god": "偏印"}],
      "failures": []
    },
    "quote": {
      "status": "pass",
      "checked": [{"source_ref": "sources/duan/....md:L000", "verbatim": true}],
      "failures": []
    },
    "seeded_error": {"status": "pass", "mode": "card_scan", "checked": [], "failures": []},
    "overall": "pass"
  },
  "anchor_q": [
    {
      "qid": "Q1",
      "text": "<纯事实是非题，不含候选/方向词>",
      "fact_window": "2021-01..2021-12",
      "fact_domain": "career",
      "answer_type": "yes_no",
      "discriminates": ["D1", "D2"],
      "elimination": [
        {"answer": "yes", "eliminates": ["D1"], "keeps": ["D2"]},
        {"answer": "no", "eliminates": ["D2"], "keeps": ["D1"]},
        {"answer": "unknown", "eliminates": [], "keeps": ["D1", "D2"]}
      ]
    }
  ],
  "anchor_a": [
    {"qid": "Q1", "answer": "yes", "answered_by": "anchor-1", "answered_at": "2026-10-30T00:00:00+08:00", "note": ""}
  ],
  "expert_decision": null,
  "anchor_request": null,
  "statement": "<由 statement_claims 组成，含地址>",
  "statement_claims": [
    {
      "claim_id": "SC1",
      "text": "<本句只写已选候选/事实>",
      "claim_ref": "D2",
      "source_ref": "sources/duan/....md:L000",
      "quote": "<逐字原文占位>"
    }
  ],
  "boundary": {"holds_when": "<条件>", "fails_when": "<反条件>"},
  "confidence": "中",
  "unknowns": ["G2"],
  "non_claims": ["不判吉凶", "不判应期", "不判主次/体用胜负"]
}
```

### 2.2 顶层字段

| 字段 | 类型 | 必填 | 约束 |
|---|---|---|---|
| `schema` | string | 是 | 固定 `"analysis-card/v2"` |
| `card_id` | string | 是 | 同报告内唯一；建议 `<set>-<seq>` |
| `case_id` | string | 是 | 预注册案例 ID；不得复用 anchor-60 / fixed-20 / dev-20 / holdout-20 / fresh-40 的 case_id |
| `snapshot` | object | 是 | `{chart_id, dayun_index, liunian_year}`；无岁运也必须写 `null`；一卡一快照 |
| `card_status` | enum | 是 | `valid` / `void`；`void` 见 §7.4 |
| `tier` | enum | valid 必填 | `A` / `B1` / `B2` / `C`；`void` 时为 `null` |
| `decision_by` | enum | 是 | `engine_fixed` / `anchor_fact` / `expert_judgment` / `needs_anchor` |
| `pending` | enum | 否（默认 `none`） | `none` / `anchor_q` / `expert_decision`；交付卡必须 `none`；非 `none` 只是草稿 |
| `tier_reason` | string[] | 是 | 见 §5.5；至少 1 条 |
| `provenance` | object | 是 | 见 §2.3；`kind` 必须等于 `decision_by` |
| `t1_local_image` | object | 是 | v1 字段；`addrs` ≥1；无关系时写 `no_relation:true` 并说明 |
| `t2_role_and_force` | object | 是 | 见 §2.4 |
| `t3_outcome` | object | 是 | 见 §2.5 |
| `t4_scene_and_activation` | object | 是 | v1 字段；P0/P1 原局快照；不得预测 |
| `t5_dual_anchor` | object | 是 | 见 §2.6；`candidate_anchors` 覆盖全部候选 |
| `engine_validation` | object | 是 | 见 §7；`overall=pass` 才可交付 |
| `anchor_q` / `anchor_a` | array | 是 | A/B2/C 为 `[]`；B1 为 1–2 条且一一对应 |
| `expert_decision` | object/null | 是 | B2 必填；A/B1/C 为 `null` |
| `anchor_request` | object/null | 是 | C 必填；A/B1/B2 为 `null` |
| `statement` | string | 是 | 含 `t1_local_image.addrs` 至少 1 个；只能由 `statement_claims` 组成 |
| `statement_claims` | array | 是 | 每条 `claim_id/text/claim_ref/source_ref/quote`；无源断言 = 0 |
| `boundary` | object | 是 | `holds_when` / `fails_when` 非空 |
| `confidence` | enum | 是 | `高` / `中` / `低` / `未知`；`未知` 不得进 A/B1/B2 |
| `unknowns` | string[] | 是 | 只接受预注册缺口 ID；`not_claimed` 层必须有对应缺口 |
| `non_claims` | string[] | 是 | 非空；列出本卡没有断言的事项 |

### 2.3 `provenance`

```json
{
  "kind": "engine_fixed|anchor_fact|expert_judgment|needs_anchor",
  "generator": "agent-candidate-generator/v1",
  "engine_cmd": "<实际命令>",
  "theory_cmd": "<实际命令或 null>",
  "generated_at": "<RFC3339>",
  "source_refs": ["sources/...:Lx-Ly"],
  "anchor_q_ids": ["Q1"],
  "expert_id": "expert-1"
}
```

- `kind` 必须等于 `decision_by`；不匹配 → V19。A 卡的 `provenance.kind` 即口头所说的 `provenance=engine_fixed`；用对象形式是为了同时保存 CLI/来源。
- A/B1/B2 的 `source_refs` 非空；C 可列出已检索但不足的来源，并写 `anchor_request`。
- B1 的 `anchor_q_ids` 必须与 `anchor_q[].qid` 一致；B2 的 `expert_id` 必须与 `expert_decision.expert_id` 一致。
- `generated_at` 不参与事实判断；同一输入重跑必须得到同候选集（生成器 §8.1）。

### 2.4 `t2_role_and_force`

| 字段 | 类型 | 约束 |
|---|---|---|
| `tiyong` | object | `{actor_role,target_role}` ∈ {体,用,双属}，取自 `duan_zuogong.tiyong` |
| `binzhu_layer` | int | 1–4，取自 `d01-deep-read.md:85-92` 四层表 |
| `direction_candidates` | array | 1–3 条；A 固定类可为 1；B1 必须 2–3；B2 1–3；C 0–3；见 §3.1 |
| `selected_option` | string/null | 必须是候选 `option_id`；null ⇔ `selection_source=needs_anchor` |
| `selection_source` | enum | `agent_auto` / `human_fork` / `needs_anchor`；与 `tier` 映射见 §4.2 |
| `direction` | string/null | 已选项的投影：`克/生/泄/化/墓/制/合/冲/刑/穿/害/破`；无选择为 `null` |
| `direction_known` | bool | 仅当 `tier=A`（engine_fixed）且已选项 `claim.direction="actor_to_target"` 时为 `true`；B1/B2/C 一律 `false`（engine 对动态 `actor=null`，选中不等于 engine 已知） |
| `actor` / `target` | string/null | 仅 `direction_known=true` 时非空且等于已选项 `claim.actor/target`；B1/B2/C 为 `null`；已选动态候选的 `actor/target` 只在 `direction_candidates[selected_option].claim` 里，不投影到 `t2` |

> v2 语义：`direction_known` 仍表示「engine 固定规则已知方向」，不是「本卡选了一个候选」。B1/B2 选中动态候选后，`selected_option` 记录选择，`direction_candidates[selected_option].claim` 记录 actor/target，但 `t2.actor/target` 保持 `null`，`non_claims` 必须写「engine 不确认动态 actor」。

- `direction_candidates[]` 的每条都按 §3.1 校验；A 只允许固定类候选被选中。
- `direction` 是**投影**，不是新事实；`statement` 不得超出已选项。
- 动态关系（冲/合/穿/刑/破）即使有候选，也**不得**让 `selection_source=agent_auto`（动态永不 A）。

### 2.5 `t3_outcome`

| 字段 | 类型 | 约束 |
|---|---|---|
| `state_scope` | enum | `selected` / `not_claimed` |
| `state_candidates` | array | `selected` 时 1–3 条；`not_claimed` 时 0–3 条（仅记录未决备选） |
| `selected_state` | string/null | `state_scope=selected` 时必须是候选 `option_id`；否则 `null` |
| `state_selection_source` | enum/null | `agent_auto` / `human_fork` / `needs_anchor`；`not_claimed` 时 `null` |
| `state` | enum/null | `成局` / `破局` / `逢救应化解`；`not_claimed` 时 `null` |
| `rescue_scope` | enum | `not_claimed` / `candidate_only` |
| `rescue_candidates` | array | 0–3 条；见 §3.3 |
| `selected_rescue` | null | v2 一律 `null`；救应原语 + 外部审计编号齐备前不得选 |
| `rescue_selection_source` | null | v2 一律 `null`；`candidate_only` 且救应材料影响结论时，卡降为 C |
| `rescue_judged` | enum | 固定 `未判`（G5） |

- `state_scope=selected`：`state_candidates` 中恰有 1 条 `decisive=true` 且无冲突，或由 B1 选出；`state` 等于该条 `state`。2–3 条互斥且无法用该卡 `anchor_q` 消歧 → C（`state_conflict`；B2 不用于 state 消歧）。
- 若方向层已是 B1，且同一 `anchor_q` 明确 `discriminates` 了 `S1/S2`，则 state 可随之选，`state_selection_source=human_fork`；否则 state 冲突 → C（B2 不用于 state 消歧）。
- `state_scope=not_claimed`：`selected_state=null`、`state=null`、`state_selection_source=null`；statement 不得出现「成局/破局/化解」等断言；`unknowns` 记录 `G_state_unjudged` 或 `G5`。
- `rescue_scope=not_claimed`：不得写「有救/化解/无救」；`rescue_judged=未判`。
- `rescue_scope=candidate_only`：列出候选与依据；若候选 `decisive=true` 且影响方向/成败，卡只能是 C（缺救应原语），不得 A/B1/B2 的结论。

### 2.6 `t5_dual_anchor`

| 字段 | 类型 | 约束 |
|---|---|---|
| `address_anchor.edge_ids` | string[] | 覆盖 `t2` 已选/候选引用的全部边；同快照 |
| `address_anchor.addrs` | string[] | 覆盖 `t1` 与候选端点 |
| `text_anchor` | object | `{entry_id, path, line}`；`path:line` 可解析；引文逐字 |
| `candidate_anchors` | array | 每条候选的 `option_id` + `source_ref` + `quote`；不得漏候选 |

- `candidate_anchors` 必须覆盖 `direction_candidates` / `state_candidates` / `rescue_candidates` 中所有 `decisive=true` 的候选；缺一 → V09。
- 原文锚点支持的是**结构/方向句**，不是吉凶断言；引用原文的吉凶半句来支撑结构结论 → V18。

## 3. 候选 schema

候选槽容量为 2–3 条；仅当只有一个有源候选时允许 1 条（A 固定类，或 B2 的单候选确认）或 0 条（C / `not_claimed`）。**不得为凑 2–3 条编造候选**；候选不足时降 B2/C 或 `not_claimed`。

### 3.1 方向候选 `direction_candidates[]`

```json
{
  "option_id": "D1",
  "claim": {
    "relation": "ke|sheng|hua|muku|chong|he|chuan|xing|po|zhi",
    "direction": "actor_to_target|mutual",
    "members": ["D.b", "H.b"],
    "actor": "D.b",
    "target": "H.b"
  },
  "basis": [
    {"kind": "engine_edge|engine_candidate|engine_fixed_rule|source_directive|source_rule|structure_item|gap",
     "ref": "e015|duan_zuogong.candidates[30]|sources/...:L48|structures[0].items[1]",
     "note": "<可选>"}
  ],
  "source_ref": "sources/...:Lx-Ly",
  "quote": "<逐字原文>",
  "decisive": true,
  "conflict_with": ["D2"],
  "conflict_class": null,
  "engine_note": null
}
```

| 字段 | 约束 |
|---|---|
| `option_id` | 同层唯一；`D1..D3` |
| `claim.relation` | 只能取上述枚举；固定类用 `ke/sheng/hua/muku`；动态用 `chong/he/chuan/xing/po`；`zhi` 只作复合/制用，不单独成向 |
| `claim.direction` | `actor_to_target` 或 `mutual`；`mutual` 时 `actor/target=null`，`members` 必须两端 |
| `claim.members` | 必须与 engine 边的 `members` 一致（同快照）；固定类无 edge 时用两端地址 |
| `claim.actor/target` | `actor_to_target` 时非空；必须是 engine 物理地址；不得用藏干/岁运字（无快照时） |
| `basis` | ≥1 条；动态候选必须至少 1 条 `source_directive`；A 固定候选至少 1 条 `engine_candidate` 或 `engine_fixed_rule` |
| `source_ref` | `sources/...:Lx` 或 `:Lx-Ly`；必须可解析 |
| `quote` | 该行/行区间的**逐字子串**；含 OCR 空格；不拼接/不改写/不省略到改变语义 |
| `decisive` | 仅当 quote 是施动句/规则句，明确给出 actor/target（或 mutual），无条件未满足、无相反来源；穿制候选恒 `false` |
| `conflict_with` | 与哪些 `option_id` 冲突；必须对称；冲突定义见 §3.4 |
| `conflict_class` | `null` / `chuan_zhi` / `source_contradiction` |
| `engine_note` | 可选：`muku_actor_corrected`、`G3_no_edge`、`engine_pair_fallback` 等；不得用来掩盖校验失败 |

**数量**：A 固定类 1 条（若列备选，备选必须 `decisive=false` 且 `conflict_with=[]`）；B1 必须 2–3 条且至少一对冲突；B2 为 1–3 条（单条时是确认而非消歧；2–3 条时至少一对冲突）；C 0–3 条。

### 3.2 成败候选 `state_candidates[]`

```json
{
  "option_id": "S1",
  "state": "成局|破局|逢救应化解",
  "basis": [
    {"kind": "edge|structure_item|source_rule|gap", "ref": "e015|structures[0].items[1]|sources/...:L48", "note": "<可选>"}
  ],
  "source_ref": "sources/...:Lx-Ly",
  "quote": "<逐字原文>",
  "decisive": true,
  "conflict_with": [],
  "engine_note": null
}
```

- `state` 三态，不许布尔；`decisive=true` 仅当 `basis` 中有 `status=met/unmet` 的结构项或明确原文判据，且 quote 支持该状态；`needs_judgment`/`not_evaluable` → `decisive=false`。
- `成局`：结构成立且无破项；`破局`：breaker met 或边对目标构成冲/刑/穿/破 + 原文判据；`逢救应化解`：必须有 rescuer met + 救应原语 + 外部审计编号；v2 缺原语 → 只能 `candidate_only`，不得 `selected`。
- 不允许「有冲边就等于破局」；必须有 `basis` + 原文判据（v1 §2.3）。
- `state_scope=not_claimed` 时，`state_candidates` 只作备选记录，不得被 statement 使用。

### 3.3 救应候选 `rescue_candidates[]`

```json
{
  "option_id": "R1",
  "rescuer": "D.b",
  "rescued": "H.b",
  "status": "candidate_met|candidate_unmet|not_evaluable",
  "rescue_primitive": null,
  "external_audit_id": null,
  "basis": [
    {"kind": "structure_item|edge|source_rule|gap", "ref": "structures[0].items[2]|e015|sources/...:L48", "note": "<可选>"}
  ],
  "source_ref": "sources/...:Lx-Ly",
  "quote": "<逐字原文>",
  "decisive": false,
  "conflict_with": []
}
```

- `rescue_primitive` 与 `external_audit_id` 在本版均为 `null`；因此 `decisive` 恒 `false`，`selected_rescue` 恒 `null`（G5）。
- `status=candidate_met` 不得写成「已化解」；不得把结构项 `met` 说成成格/化解。
- 不得写「库已开/已闭」；`relations.muku.openers/binders` 只作事实。

### 3.4 冲突与 `conflict_with`

两条方向候选冲突，当且仅当至少一条成立：

1. 同一对端点，`actor` 相反或 `target` 相反（A→B vs B→A）；
2. 同一对端点，一条 `actor_to_target`、一条 `mutual`；
3. 同一对端点，`relation` 不同且不能共存（如 `chong` vs `he`，`ke` vs `muku` 对同一端点的做功解释互斥）；
4. 两条都声称同一层结论，但一条的 `quote` 与另一条语义相反（`source_contradiction`）。

`conflict_with` 必须对称：若 D1 列 D2，D2 必须列 D1；否则 V08。

### 3.5 候选的 `decisive` 判据

`decisive=true` 必须同时满足：

1. `quote` 逐字命中，且是**施动句/规则句**：句法主语（或被动式「被 X 所 Y」的 X）能落到 `actor`，宾语/受事能落到 `target`；不能是并列列举、位移句、条件未满足句、纯吉凶句；
2. `actor/target` 都能由 engine 地址定位；同字多位的歧义必须用宫位/边消解，不能消解 → `decisive=false`；
3. 无 `conflict_class="chuan_zhi"`；无 `source_contradiction`；
4. `engine_validation` 对该候选的 address/edge/ten_god/quote/seeded_error 全 pass（或 edge 合法 `not_applicable`）；
5. 不属于「无源」：`source_ref` 与 `quote` 都存在且逐字。

`decisive=false` 的候选可以留在候选集里作备选，但不得被 A 选中；B1/B2 只能在 `decisive=true` 的候选之间选（除非专家明确写 `needs_anchor`）。

## 4. 选择来源与 `decision_by`

### 4.1 `selection_source` 枚举（保持 v1 原三值）

| 值 | 含义 | 对应 tier |
|---|---|---|
| `agent_auto` | Agent 依固定规则自动选中，无人参与 | A |
| `human_fork` | 人提供事实（B1）或专家裁决（B2）后选中；**人没有直接挑候选**（B1） | B1 / B2 |
| `needs_anchor` | 无选择；卡挂起 | C |

- B1 的「人」只回答事实；选中是 Agent 按 `elimination` 机械执行的结果，但 `selection_source` 仍记 `human_fork`，因为决定输入来自人。
- B2 的「人」是专家；`selection_source=human_fork` + `decision_by=expert_judgment`。
- 动态卡任何情况下不得 `agent_auto`。

### 4.2 `decision_by` 与 tier 映射

| tier | `decision_by` | `provenance.kind` | `selection_source` | 谁做决定 |
|---|---|---|---|---|
| A | `engine_fixed` | `engine_fixed` | `agent_auto` | 引擎固定规则 |
| B1 | `anchor_fact` | `anchor_fact` | `human_fork` | 命主/知情者答事实，Agent 淘汰 |
| B2 | `expert_judgment` | `expert_judgment` | `human_fork` | 专家单选/`needs_anchor` |
| C | `needs_anchor` | `needs_anchor` | `needs_anchor` | 无人能定；补锚点 |

不匹配 → V03/V19。

## 5. Tier 判定

> B 档按中枢 2026-10-30 修正拆为 **B1（锚点事实消歧）** 与 **B2（专家裁决）**；外层仍是 A / B / C 三档，B 内部分两支。A 只固定类；动态永不 A。

### 5.1 A（仅固定克/生/化/墓）

必须同时满足：

1. `t2` 已选方向候选的 `claim.relation ∈ {ke, sheng, hua, muku}`；
2. 该层恰有 1 条 `decisive=true`，`conflict_with=[]`；其余备选（如有）`decisive=false` 且 `conflict_with=[]`；`direction_known=true`；
3. `engine_validation.overall=pass`（edge 可为 `not_applicable`，但必须写明 `G3` 或 `muku no edge`）；且 `basis` 至少 1 条 `engine_candidate` / `engine_fixed_rule`；仅 `same_page`/source-only 依据不得升 A（可作 B1 候选）；
4. `state_scope=selected` 且恰有 1 条 decisive state 无冲突、`state_selection_source=agent_auto`，或 `state_scope=not_claimed` 且 statement 不声称成败；
5. `rescue_scope=not_claimed`；若有 `candidate_only` 的 decisive 救应，降 C；
6. `anchor_q=[]`、`anchor_a=[]`、`expert_decision=null`、`anchor_request=null`；
7. `provenance.kind=engine_fixed`；`statement_claims` 全部有源；
8. 卡内没有动态关系被选中（t1 可以列动态边，但不得成为已选方向）；
9. `pending=none`（A 由引擎确定性落定，不等人工；**「不代选」只约束 B/C，不约束 A**）。

**A 的硬禁止**：任何 `chong/he/chuan/xing/po` 候选被选中 → 不是 A，直接 V02。

**A 的自动性**：A 不需要人；`engine_fixed` + `agent_auto` + `pending=none` 是 A 的正常状态。T-197 的「不代选」只针对 B/C（B1 要人等事实、B2 要等专家），不意味着 A 也要等人工。

**`same_page` 不升 A**：`same_page`/source-only 是 actor-rules-v1 §4.10 的证据分级；它只能支撑 B1 候选，不能单独支撑 A。A 必须有 `engine_candidate` / `engine_fixed_rule` 依据。

### 5.2 B1（锚点事实消歧）

必须同时满足：

1. `direction_candidates` 为 2–3 条（或固定类冲突的 2–3 条），至少一对 `conflict_with`；
2. 所有参与消歧的候选 `decisive=true`、有源、校验 pass；无 C 条件；
3. `anchor_q` 为 1–2 条：只问「命主已发生事实」，`answer_type=yes_no`，`fact_window` 具体，`discriminates` ≥2 个候选；问题文本**不得**出现候选 `option_id`、方向词（冲/合/穿/刑/克/生/化/墓）、或「你选哪个」；
4. `anchor_a` 与 `anchor_q` 一一对应；答案 ∈ {yes,no,unknown}；
5. 按 `elimination` 淘汰后**恰剩 1 条**；剩 0 条 → C（`anchor_inconsistent`）；剩 >1 条 → 加第 2 问，仍 >1 → C（`anchor_insufficient`）；任何 `unknown` 导致无法收敛 → C（`anchor_unknown`）；
6. `selected_option` = 唯一幸存候选；`decision_by=anchor_fact`；`selection_source=human_fork`；`expert_decision=null`；
7. `provenance.kind=anchor_fact`，`anchor_q_ids` 与 `anchor_q` 一致；
8. 锚点答题者未看候选/方向（流程声明见生成器 §4.5）；锚点事实不进入评分。

### 5.3 B2（专家裁决）

必须同时满足：

1. `direction_candidates` 为 1–3 条（单条时是确认而非消歧；2–3 条时至少一对冲突）；所有候选有源、校验 pass；无 C 条件；
2. 生成器判定**没有任何可观测的已发生事实**能区分候选（`anchor_q=[]`；`provenance`/B2 包记录 `b2_reason="no_observable_discriminator"`）；
3. `expert_decision` 非空：`option_id` ∈ 候选；`source_ref` + `quote` 逐字，支持该候选；`expert_id` 与 `provenance.expert_id` 一致；
4. 专家可选一个候选，或写 `needs_anchor`（后者 → C）；
5. `selected_option` = 专家选项；`decision_by=expert_judgment`；`selection_source=human_fork`；
6. `anchor_q=[]`、`anchor_a=[]`；`anchor_request=null`；
7. 专家 ≠ 候选生成者 ≠ 评分者 ≠ 锚点答题者；B2 占比 P1 ≤30%。

### 5.4 C（needs_anchor）

任一成立即 C：

1. 某层无任何有源候选（`source_ref`/`quote` 缺失，或 quote 不支持该方向）；
2. 候选涉及**穿制冲突**（`conflict_class="chuan_zhi"`，见 §6.3）；
3. `engine_validation` 非伪造类失败（如 edge 无法确认、ten_god 不可得、G3/G4 缺口导致方向不能落地）；
4. B1 锚点答不出/不够/矛盾（`anchor_unknown` / `anchor_insufficient` / `anchor_inconsistent`）；
5. 救应材料影响结论但缺救应原语/外部审计编号（G5）；
6. 无候选（0 条）或所有候选 `decisive=false`；
7. 只有固定类但存在多个互斥固定候选且无法用事实/专家消歧（可转 B1/B2；若都不成立 → C）；
8. `state_candidates` 2–3 条互斥，且无法用同一 `anchor_q` 消歧（`state_conflict`；B2 不用于 state 消歧）。

C 必须：

- `selected_option=null`；`selection_source=needs_anchor`；`decision_by=needs_anchor`；`provenance.kind=needs_anchor`；
- 若 C 由 state 冲突触发，`state_scope=not_claimed`、`selected_state=null`、`state=null`，不得在 C 卡里硬选 state；
- `anchor_request` 非空：`target_layer`、`need`、`blocked_reason`、`what_would_unblock`；
- `tier=C`；`card_status=valid`（除非同时有伪造 → void）；
- statement 只写已确认事实与缺口，**不得**写未决方向/成败。

`blocked_reason` 枚举：`no_source` / `chuan_zhi` / `validation_fail` / `anchor_unknown` / `anchor_insufficient` / `anchor_inconsistent` / `rescue_primitive_missing` / `no_candidate` / `state_conflict`。

### 5.5 `tier_reason` 代码

| 代码 | 含义 |
|---|---|
| `direction:engine_fixed` | 固定类自动 |
| `direction:anchor_conflict` | 动态/固定冲突，用锚点事实消歧 |
| `direction:expert_conflict` | 无事实可辨，专家裁决 |
| `direction:no_source` | 无源 → C |
| `direction:chuan_zhi` | 穿制冲突 → C |
| `direction:validation_fail` | 校验失败 → C |
| `state:selected` | 成败已选 |
| `state:not_claimed` | 成败不判 |
| `state:conflict` | 成败冲突 |
| `rescue:not_claimed` | 救应不判 |
| `rescue:candidate_only` | 救应仅候选 |
| `rescue:needs_primitive` | 缺救应原语 → C |
| `card:void_fabricated_ref` | 伪造引用 → void |

### 5.6 卡级 tier 取最高

- 严重度：`A < B1 < B2 < C`；`not_claimed` 层不参与取最高，但必须写 `*_scope="not_claimed"`。
- 方向层 A + 成败层 B1 → 卡 B1；方向 B1 + 成败 C → 卡 C。
- 卡级 tier 必须等于各层最高；不一致 → V03。

## 6. B1 锚点、B2 专家、C 锚点请求

### 6.1 B1 `anchor_q[]`

| 字段 | 约束 |
|---|---|
| `qid` | `Q1..Q2`，同卡唯一 |
| `text` | 纯事实是非题；不含候选 ID、方向词、吉凶词；不问未来；不问价值判断 |
| `fact_window` | 具体年月区间（如 `2021-01..2021-12`）；不得写「这几年」 |
| `fact_domain` | `career/marriage/health/wealth/residence/other` |
| `answer_type` | 固定 `yes_no` |
| `discriminates` | ≥2 个 `option_id`；必须与 `elimination` 一致 |
| `elimination` | 覆盖 `yes` / `no` / `unknown`；每条给 `eliminates[]` / `keeps[]`；淘汰后必须能收敛到 1 条（或触发 C） |

**好问题**：「2021-01 至 2021-12 之间，命主是否发生过一次有第三方记录的岗位变动（升职/降职/调岗）？」
**坏问题**：「命主是被冲还是被合？」（让人选候选）、「2027 年会不会升职？」（未来）、「命主是不是性格强势？」（模糊/价值）。

问题文本不得出现：`冲/合/穿/刑/克/生/化/墓/用神/忌神/喜用`、候选 `option_id`、`A/B/C`、方向箭头。
**冻结**：`anchor_q` 与 `elimination` 必须在答题前冻结（记录 hash）；答题后不得改问题/淘汰表，否则该 B1 作废。

### 6.2 B1 `anchor_a[]`

```json
{"qid": "Q1", "answer": "yes|no|unknown", "answered_by": "anchor-1", "answered_at": "<RFC3339>", "note": ""}
```

- 必须与 `anchor_q` 一一对应；答案只能 yes/no/unknown。
- 答题者**只看问题**，不看候选/方向/卡；由流程保证并记录（生成器 §4.5）。
- 锚点事实只用于 `elimination`，不得进入 P1/P2 评分标签、训练或调参（目标文档 `anchor_fact_leakage=0`）。

### 6.3 穿制冲突（C 的固定条件）

以下任一成立 → 候选 `conflict_class="chuan_zhi"`、`decisive=false`，该层 C：

1. 候选把「穿」当作「制」的施力机制（`chuan` + 制用语义）；
2. 同一对端点的来源中出现相反说法：`21:L2425`「穿制不了对方是一种坏，冲合克都可以制，唯有穿制不了。」 vs `22:L2252`「戌酉穿， 羊刃穿了官杀库」（同段又有「为羊刃穿制了官库」）；
3. 候选需要「力量绝对优势」才能成立，但当前卡没有整数化力量证据。

处理：`anchor_request.blocked_reason="chuan_zhi"`；`what_would_unblock` 写明「需个案条件/力量整数化/新的裁决规格」；**不得**用其中一句消去另一句（`docs/specs/party-direction-v1.md` §3.4 已记录该冲突；本规格只引用其冲突事实，不复活党势方向）。

### 6.4 B2 `expert_decision`

```json
{
  "option_id": "D2",
  "expert_id": "expert-1",
  "source_ref": "sources/...:Lx-Ly",
  "quote": "<逐字原文>",
  "reason": "<为什么该候选优于其他候选；不得只写『经验』>",
  "decided_at": "<RFC3339>"
}
```

- `option_id` 必须在候选集内且 `decisive=true`；`source_ref` + `quote` 必须支持该候选（不是只支持类规则）。
- 专家可选 `needs_anchor`：写 `"option_id": null`，并在 `reason` 写缺口；此时卡降 C，`anchor_request.blocked_reason="no_candidate"` 或 `validation_fail`。
- 专家 ≠ 候选生成者 ≠ 评分者；不得由同一人兼任。
- B2 占比 P1 ≤30%；超限 → P1 kill（目标文档）。

### 6.5 C `anchor_request`

```json
{
  "target_layer": "direction|state|rescue",
  "need": "<缺什么：施动句/个案条件/力量证据/救应原语/地址消歧>",
  "blocked_reason": "no_source|chuan_zhi|validation_fail|anchor_unknown|anchor_insufficient|anchor_inconsistent|rescue_primitive_missing|no_candidate",
  "what_would_unblock": "<可检验的解锁条件>"
}
```

- C 卡不得写 `selected_option`；不得把 `anchor_request` 写成结论。
- 补锚点后必须重跑生成器与 `engine_validation`，不能手工改 `selected_option` 绕过校验。

## 7. `engine_validation`

### 7.1 结构

```json
{
  "snapshot": {"chart_id": "cf-...", "dayun_index": null, "liunian_year": null},
  "address": {"status": "pass|fail", "checked": [], "failures": []},
  "edge": {"status": "pass|fail|not_applicable", "checked": [], "failures": [], "reason": null},
  "ten_god": {"status": "pass|fail|not_applicable", "checked": [], "failures": []},
  "quote": {"status": "pass|fail", "checked": [], "failures": []},
  "seeded_error": {"status": "pass|fail", "mode": "card_scan|self_test", "checked": [], "failures": []},
  "overall": "pass|fail"
}
```

`overall=pass` 当且仅当五个子检全部 `pass` 或合法 `not_applicable`；任一 `fail` → `overall=fail`。

### 7.2 五个子检

| 子检 | 检查什么 | 失败处置 |
|---|---|---|
| `address` | 候选/已选/t1 的每个地址存在于同快照 engine 输出；藏干无独立地址（G4）；岁运地址只在快照有 `DY/LN` 时允许；同字多位必须用宫位/边消歧 | 未知地址 = 伪造 → `void`；歧义无法消解 → C |
| `edge` | 每个 `edge_id` 存在于同快照；`kind/members/group/completeness` 与 engine 完全一致；不得跨快照；固定类无 edge 时 `not_applicable` + `reason`（G3/muku） | 边不存在或 members 不符 = 伪造 → `void`；合法缺边 → `not_applicable`，不 void |
| `ten_god` | 每个被引用的干/支十神与 engine 一致；地支取本气十神；藏干十神必须用藏干引用，不得当地址；岁运字十神不可得时写 `suiyun_ten_god` 缺口 | 十神不符 = 伪造 → `void`；不可得 → C/缺口 |
| `quote` | `source_ref` 可解析；`quote` 是 `path:line`（或行区间）的**逐字子串**；含 OCR 空格；不拼接/不改写/不省略到改变语义；不得用吉凶半句支撑结构 | 不逐字/找不到 = 伪造 → `void` |
| `seeded_error` | 卡内不得含 seeded 假地址/假边/假引文/假十神 token；校验器须在 seeded fixture 上 100% 抓出（`mode=self_test` 报告） | 命中 → `void`；self_test <100% → P0 hard kill |

### 7.3 `seeded_error` 的两种模式

- `mode="card_scan"`：逐卡扫描，`checked` 列出扫描的地址/边/引文/十神，`failures` 列出命中项；正常卡 `pass`。
- `mode="self_test"`：校验器对 seeded fixture（假地址/假边/假引文/假十神各 ≥5 例）自测；`checked` 列出 fixture ID，`failures` 列出漏报；必须 `detected/total=100%`。
- P0 报告必须同时有 per-card `card_scan` 与一次 `self_test` 100%；任一缺失 → P0 fail。

### 7.4 `card_status="void"`

以下任一 → 整卡作废（不是 C，不得交付）：

1. 伪造地址（engine 无此地址）；
2. 伪造/错配边（edge_id 不存在、kind/members 不符、跨快照）；
3. 伪造十神（与 engine 不符）；
4. 伪造引文（`source_ref` 不存在或 quote 非逐字）；
5. `seeded_error` 命中；
6. 藏干被当地址使用（G4）且候选依赖它。

`void` 卡：`card_status="void"`、`tier=null`、`decision_by="needs_anchor"`、`selection_source="needs_anchor"`、`void_reason` 非空；不得进入 P0/P1/P2 统计；必须重生成。

## 8. `statement` 与 `statement_claims`

### 8.1 规则

- `statement` 只能由 `statement_claims[].text` 组成（可加连接词），不得引入 claim 之外的方向/成败/救应断言。
- 每条 claim 必须有 `claim_ref`（候选 `option_id` / `edge:e015` / `fact:...` / `state:S1` / `rescue:R1`）+ `source_ref` + `quote`。
- `statement` 必须含 `t1_local_image.addrs` 至少 1 个地址。
- 不得出现：年份/年龄/期限、概率/程度词（大概率/一定/必定/必然）、事件断言（结婚/离婚/疾病/破财/升职的具体发生）、吉凶/应期/化解/改运、只靠十神名称的形容词。
- `not_claimed` 层不得出现在 statement；只能出现在 `unknowns` / `anchor_request`。

### 8.2 无源断言判定

- `claim_ref` 无法解析 → 无源；
- `source_ref` 为空或不可解析 → 无源；
- `quote` 非逐字 → 无源（且 quote 失败 → void）；
- claim 含方向/成败/救应词但对应候选 `decisive=false` 或未选中 → 无源/越权；
- 任一 → `unsourced_claims>0`；P0/P1 hard kill。

## 9. 校验码

### 9.1 V01–V22

| 码 | 检查 | 失败 |
|---|---|---|
| V01 | 按 tier 的必填字段齐全（含 `provenance` / `engine_validation` / `statement_claims`） | fail |
| V02 | A 只允许固定 `ke/sheng/hua/muku`；动态 A = 禁止 | fail |
| V03 | `tier` / `decision_by` / `selection_source` / `provenance.kind` 映射一致；卡级 tier = 各层最高 | fail |
| V04 | A：恰 1 条 decisive、无冲突、校验 pass、state/rescue 合规 | fail |
| V05 | B1：1–2 问、纯事实、`discriminates`≥2、答案齐、淘汰后恰 1 条、答题者盲态 | fail |
| V06 | B2：`expert_decision` 有源/逐字、候选内、专家隔离、`anchor_q=[]` | fail |
| V07 | C：`selected_option=null`、`anchor_request` 四字段齐、statement 不写未决 | fail |
| V08 | 候选 1–3、`option_id` 唯一、`conflict_with` 对称、数量符合 tier | fail |
| V09 | 每条候选有 `source_ref` + `quote`；`candidate_anchors` 覆盖 decisive 候选 | fail |
| V10 | 动态候选至少 1 条 `source_directive`；不得只靠 engine 边定 actor | fail |
| V11 | `engine_validation.address/edge/ten_god` pass 或合法 not_applicable | fail/void |
| V12 | `engine_validation.quote` 逐字 100% | fail/void |
| V13 | `seeded_error.card_scan` pass；`self_test` 100% | fail/void |
| V14 | 无跨快照 `edge_id` / 地址 | void |
| V15 | 无藏干地址（G4） | void |
| V16 | 穿制冲突 → C，不得 A/B1/B2 | fail |
| V17 | `statement_claims` 覆盖 statement；无无源断言 | fail |
| V18 | 无预测/吉凶/应期/概率/事件/化解 | fail |
| V19 | `provenance.kind==decision_by`；A/B1/B2 的 `source_refs` 非空；B1 `anchor_q_ids`/B2 `expert_id` 对齐 | fail |
| V20 | `card_status`/`void` 规则；void 卡不得进统计 | fail |
| V21 | 角色隔离声明：生成者 ≠ 锚点答题者 ≠ 评分者；B2 专家不兼任 | fail |
| V22 | 锚点事实未进入评分标签/训练/调参 | fail |

### 9.2 与 v1 L 码的映射

| v1 | v2 | 说明 |
|---|---|---|
| L01 五元组齐全 | V01 | 保留 |
| L02 ① 地址/关系 | V01 / V11 | 保留 |
| L06 ② 方向未定即置空 | V03 / V04 | `direction_known=true` 仅 A 固定；`mutual` 时 `direction=关系种`、`direction_known=false`、`actor=target=null`；B1/B2 选中动态时 `direction_known=false`、`actor=target=null`（actor/target 只在候选 `claim`）；无选择（C）时 `direction=null`、`direction_known=false`、`actor=target=null` |
| L07 ③ 三态非布尔 | V03 / V07 | `not_claimed` 时 `state=null`，不写第四态 |
| L08/L09 救应 | V07 / §3.3 | `rescue_judged=未判`；`已判` 仍需原语+审计编号 |
| L10–L18 statement | V17 / V18 | 禁止预测/吉凶/计数句 |
| L19 快照字段 | V01 | `snapshot` 三字段必填 |

## 10. 示例（字段形状，不是评测样本）

> 以下示例只示字段；`quote` 用占位，真实卡必须从 `source_ref` 行逐字复制。示例不对应任何真实盘，也不使用旧 3 卡或盲集案例。

### 10.1 A（固定墓，`decision_by=engine_fixed`）

```json
{
  "tier": "A",
  "decision_by": "engine_fixed",
  "provenance": {"kind": "engine_fixed", "generator": "agent-candidate-generator/v1", "source_refs": ["sources/duan/....md:L2288"]},
  "t2_role_and_force": {
    "direction_candidates": [{
      "option_id": "D1",
      "claim": {"relation": "muku", "direction": "actor_to_target", "members": ["Y.b", "D.b"], "actor": "Y.b", "target": "D.b"},
      "basis": [
        {"kind": "engine_candidate", "ref": "duan_zuogong.candidates[30]", "note": "墓用/muku"},
        {"kind": "source_rule", "ref": "sources/duan/....md:L2288", "note": "未墓寅"}
      ],
      "source_ref": "sources/duan/....md:L2288",
      "quote": "<逐字原文占位>",
      "decisive": true,
      "conflict_with": [],
      "conflict_class": null,
      "engine_note": "muku_actor_corrected"
    }],
    "selected_option": "D1",
    "selection_source": "agent_auto",
    "direction": "墓",
    "direction_known": true,
    "actor": "Y.b",
    "target": "D.b"
  },
  "anchor_q": [],
  "anchor_a": [],
  "expert_decision": null,
  "anchor_request": null
}
```

要点：墓的 actor 是**库**（`Y.b`），不是入库方；若 engine 原始候选方向相反，`engine_note="muku_actor_corrected"`，但 `engine_validation.edge` 记录候选对（pair）校验，不伪装成 engine actor。

### 10.2 B1（动态冲，锚点事实消歧）

```json
{
  "tier": "B1",
  "decision_by": "anchor_fact",
  "t2_role_and_force": {
    "direction_candidates": [
      {"option_id": "D1", "claim": {"relation": "chong", "direction": "actor_to_target", "members": ["D.b", "H.b"], "actor": "D.b", "target": "H.b"}, "decisive": true, "conflict_with": ["D2"]},
      {"option_id": "D2", "claim": {"relation": "chong", "direction": "mutual", "members": ["D.b", "H.b"], "actor": null, "target": null}, "decisive": true, "conflict_with": ["D1"]}
    ],
    "selected_option": "D2",
    "selection_source": "human_fork"
  },
  "anchor_q": [{
    "qid": "Q1",
    "text": "<纯事实是非题，不含方向词>",
    "fact_window": "2021-01..2021-12",
    "fact_domain": "career",
    "answer_type": "yes_no",
    "discriminates": ["D1", "D2"],
    "elimination": [
      {"answer": "yes", "eliminates": ["D1"], "keeps": ["D2"]},
      {"answer": "no", "eliminates": ["D2"], "keeps": ["D1"]},
      {"answer": "unknown", "eliminates": [], "keeps": ["D1", "D2"]}
    ]
  }],
  "anchor_a": [{"qid": "Q1", "answer": "yes", "answered_by": "anchor-1", "answered_at": "<RFC3339>", "note": ""}],
  "expert_decision": null
}
```

要点：人只答「是/否/不知道」；Agent 按 `elimination` 淘汰，不让人挑 D1/D2。若答 `unknown` 或淘汰后不唯一 → C。

### 10.3 B2（动态穿，专家裁决）

```json
{
  "tier": "B2",
  "decision_by": "expert_judgment",
  "t2_role_and_force": {
    "direction_candidates": [
      {"option_id": "D1", "claim": {"relation": "chuan", "direction": "actor_to_target", "members": ["Y.b", "H.b"], "actor": "Y.b", "target": "H.b"}, "decisive": true, "conflict_with": ["D2"]},
      {"option_id": "D2", "claim": {"relation": "chuan", "direction": "actor_to_target", "members": ["Y.b", "H.b"], "actor": "H.b", "target": "Y.b"}, "decisive": true, "conflict_with": ["D1"]}
    ],
    "selected_option": "D1",
    "selection_source": "human_fork"
  },
  "anchor_q": [],
  "anchor_a": [],
  "expert_decision": {
    "option_id": "D1",
    "expert_id": "expert-1",
    "source_ref": "sources/duan/....md:L000",
    "quote": "<逐字原文占位>",
    "reason": "<为什么 D1 优于 D2；必须引原文>",
    "decided_at": "<RFC3339>"
  }
}
```

要点：B2 只在「无可观测已发生事实可区分」时使用；专家必须带原文；B2 占比 P1 ≤30%。

### 10.4 C（穿制冲突）

```json
{
  "tier": "C",
  "decision_by": "needs_anchor",
  "selection_source": "needs_anchor",
  "t2_role_and_force": {
    "direction_candidates": [{
      "option_id": "D1",
      "claim": {"relation": "chuan", "direction": "actor_to_target", "members": ["Y.b", "H.b"], "actor": "Y.b", "target": "H.b"},
      "source_ref": "sources/duan/....md:L2252",
      "quote": "<逐字原文占位>",
      "decisive": false,
      "conflict_with": [],
      "conflict_class": "chuan_zhi"
    }],
    "selected_option": null,
    "selection_source": "needs_anchor"
  },
  "anchor_request": {
    "target_layer": "direction",
    "need": "<个案条件/力量整数化/新裁决规格>",
    "blocked_reason": "chuan_zhi",
    "what_would_unblock": "<可检验条件>"
  }
}
```

要点：穿制冲突下，`decisive=false`，不得 A/B1/B2；不拿 `21:L2425` 或 `22:L2252` 单句消去另一句。

## 11. 禁止

- 动态 A：`chong/he/chuan/xing/po` 被自动选中；任何 `selection_source=agent_auto` 的动态卡。
- 自动承诺：没有 `source_ref` + 逐字 `quote` 的候选被选中；仅凭 engine 边/五行表给动态 actor。
- 伪造：地址/边/十神/引文不存在或错配；跨快照引用；藏干当地址；编造 `edge_id`。
- 把 `mutual` 写成单向；把 `合` 写成有向 actor→target；把 `墓` 的 actor 写成入库方；把 `化` 的 actor 写成被化者。
- 穿制冲突下硬选一边；用一句原文消去相反原文。
- 把 B1 问题写成「你选哪个/你觉得是冲还是合」；让人看候选后挑；把锚点事实用于评分。
- 无源断言；`statement` 出现年份/概率/事件/吉凶/应期/化解。
- 复活 A+ / 党势 / `party-direction-v2`；用旧 3 卡做演示/测试/证明。
- 改 `AGENTS.md` §4、`templates/report-v7-human.md`、`engine/**`、答案/测试、`pyproject.toml`/`requirements*.txt`；做 git 写；跑盲测。

## 12. Cross-References

- 目标/gate：[`docs/goals/first-principle-agent-first-v1.md`](../goals/first-principle-agent-first-v1.md)
- 候选生成器：[`docs/specs/agent-candidate-generator-v1.md`](agent-candidate-generator-v1.md)
- 卡 v1：[`docs/specs/single-chart-analysis-v1.md`](single-chart-analysis-v1.md)
- actor 规则：[`docs/specs/actor-rules-v1.md`](actor-rules-v1.md)
- 事实证据包：[`docs/specs/fact-evidence-pack-v1.md`](fact-evidence-pack-v1.md)
- A+ 裁决：[`docs/reviews/t191-a-plus-verdict-v1.md`](../reviews/t191-a-plus-verdict-v1.md)
- 归档治理：[`archive/adjudication_v1/README.md`](../../archive/adjudication_v1/README.md)
- 工具入口：[`docs/agent_tools.md`](../agent_tools.md)
