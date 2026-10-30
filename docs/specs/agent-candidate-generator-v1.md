# Agent 候选生成器 v1 · 规格（固定类 A / 动态类 B1/B2/C）

> 任务：`tasks/T-196/PROMPT.md`；状态：🔵 Ready（规格，不写代码、不跑盲测、不改保护区）
> 关联文档：[`docs/goals/first-principle-agent-first-v1.md`](../goals/first-principle-agent-first-v1.md)（目标/gate/角色）、[`docs/specs/analysis-card-v2.md`](analysis-card-v2.md)（卡字段，字段名以此为准）。
> 依据：A+ v1.3 方向产品 kill（`docs/reviews/t191-a-plus-verdict-v1.md`）；R-tool 事实/检索层（`docs/specs/fact-evidence-pack-v1.md`、`META/r-tool-run-v1.json`、`META/r-tool-run-routing-v1.json`）；actor 规则表（`docs/specs/actor-rules-v1.md`）；fixed-20 经验（`META/p1-fixed-20.md`）；中枢 2026-10-30 两次追加修正（A 只固定类；B 拆 B1/B2；P0 只验管道）。

## 0. 一句话

给一个快照 + 一个问题，生成器只做三件事：从 `engine.cli` 取事实与边；从 `query_theory` / `sources/` 取逐字原文；产出 1–3 条带 `basis/source_ref/quote/decisive/conflict_with` 的候选，并做 `address/edge/ten_god/quote/seeded_error` 校验。**固定克/生/化/墓可直接 A；冲/合/穿/刑/破一律只出候选，永不 A**：能由命主已发生事实区分 → B1；不能 → B2；无源/穿制冲突/校验失败/锚点不收敛 → C。

## 1. 范围与非目标

### 1.1 范围

- 输入：`engine.cli` 的 chart/relations/structures/duan_zuogong；`query_theory` 命中；`sources/` 原文行；问题/域/快照。
- 输出：`agent-candidate-set/v1`（§7），可直接装配成卡 v2 的 `direction_candidates` / `state_candidates` / `rescue_candidates` / `tier` / `decision_by` / `provenance` / `anchor_q` / `anchor_a` / `expert_decision` / `anchor_request` / `engine_validation`。
- 约束：确定性、可回查、同输入同输出；不读答案/restricted/旧 3 卡/盲集 locator。

### 1.2 非目标

- 不写方向引擎；不自动承诺冲/合/穿/刑；不做党势；不复活 A+。
- 不生成「吉凶/应期/事件/概率」；不补救应原语；不把 `met` 说成成格。
- 不修改 `engine/**`、答案/测试、`AGENTS.md` §4、`templates/report-v7-human.md`；不做 git 写；不跑盲测。
- 不替锚点答题者答题，不替专家裁决，不替评分者评分。

## 2. 输入与白名单

### 2.1 允许读取

| 输入 | 用途 |
|---|---|
| `python -m engine.cli all --pillars ... --gender ... --json` | 四柱、十神、藏干、旬空、关系边、墓库、结构项、做功候选 |
| `python -m engine.cli relations/structures ... --json` | 需要 `pair_index` / 完整关系图时 |
| `python -m tools.query_theory --query ... --json` | `entry_id` / `source_ref` / 原文命中 |
| `sources/**` 对应 `source_ref` 行 | 逐字 quote 核对 |
| 问题文本 + `domain` + 预注册 `question_id` | 选边/选题域；不用于补事实 |
| 快照 `dayun_index` / `liunian_year` | 只在 P2 岁运卡；P0/P1 原局 |

### 2.2 禁止读取

- `META/p1-fixed-20-answers-v1.json`、`p1-fixed-20-answers-B-v1.json`、`p1-fixed-20-B-v1.md`；`META/routing-prereg-v1.json`；anchor/fresh/holdout/golden answers；`p1-system-run*`；`archive/adjudication_v1/restricted/**`。
- 旧 3 卡（`archive/demo/`）作为样例/测试/证明。
- 盲集 locator/case_id/答案；`expected_evidence` 等受限字段。
- 任何「上一次跑的结果」用作本次候选来源；候选必须从本次 CLI + 原文重推。

## 3. 生成流水线

```text
Step 0  快照与地址闭包
Step 1  边/结构/墓库事实摄取
Step 2  固定类通过（克/生/化/墓）→ A 候选
Step 3  动态类通过（冲/合/穿/刑/破）→ B1/B2/C 候选
Step 4  成败候选通过（state）
Step 5  救应候选通过（rescue；只候选，不判已判）
Step 6  引擎校验（address/edge/ten_god/quote/seeded_error）
Step 7  候选集装配（option_id/conflict_with/排序）
Step 8  分层 tier + 卡级 tier
Step 9  B1 锚点问题 / B2 专家包 / C 锚点请求
Step 10 输出 candidate-set（final 或 pending）
```

### Step 0：快照与地址闭包

- `snapshot{chart_id, dayun_index, liunian_year}` 固定；P0/P1 只允许 `dayun_index=null`、`liunian_year=null`。
- 合法地址：`Y.s/M.s/D.s/H.s`、`Y.b/M.b/D.b/H.b`；仅当快照有岁运时追加 `DY{n}.s/b`、`LN{year}.s/b`。
- 藏干无独立地址（G4）：不得把藏干当地址；需要藏干时用其所属地支地址 + 藏干字段表达，且不得作为方向端点。
- 同字多位：若某字在四柱地支出现多次，候选端点必须用宫位/边消歧；消歧不了 → 该候选 `decisive=false`，层 C。
- `edge_id` 只在同一快照有效；跨快照引用 → `void`（卡 v2 §7.4）。

### Step 1：事实摄取

- 取 `relations.edges[]`（`edge_id/kind/members/group/completeness/distance`）、`relations.muku[]`（`openers/binders/candidates/requires_judgment`）、`structures[].items[]`（`kind/status/evidence`）、`duan_zuogong.tiyong`、`duan_zuogong.candidates[]`（`mode/relation_kind/members/actor/edge_id`）。
- 只使用本次 CLI 输出；不心算、不补边、不补十神。
- 记录 `gaps`：G2（动态无 actor）、G3（支-支无克边）、G4、G5、`muku_open_close`、`suiyun_ten_god` 等。

### Step 2：固定类通过（克/生/化/墓）

#### 2.1 类映射

| 类 | 引擎来源 | `actor` | `target` | 备注 |
|---|---|---|---|---|
| **克** | `ke` 边（members 有序 from→to）或 `duan_zuogong.candidates` 制用且边 kind=`ke`；无 edge 时按 engine 五行表 | 克者 | 被克者 | G3：支-支无克边时 `edge.not_applicable`，`basis.kind=engine_fixed_rule` |
| **生** | `sheng` 边或 `duan_zuogong.candidates` 生泄用 | 生者 | 受生者 | 生/泄分开写；不把泄写成生 |
| **化** | `duan_zuogong.candidates` `mode=化用`（`sheng(main_qi)`） | **化者**（受生端） | **被化者**（生端） | 与生相反；不得把 `sheng` 生者当化者（actor-rules §4.8） |
| **墓** | `duan_zuogong.candidates` `mode=墓用` / `muku` | **库** | **入库方** | engine 原始候选可能是 `(入库方,库)`；按 actor-rules §4.9 写 `actor=库`，`engine_note=muku_actor_corrected`；位移句 `X入Y墓` → `actor=null`，不成固定向 |

#### 2.2 候选构造

对每个固定事实：

1. 生成 `option_id=D1..D3`；
2. `claim.relation` ∈ {`ke`,`sheng`,`hua`,`muku`}；`claim.direction="actor_to_target"`；`members=[actor,target]`；
3. `basis` 至少 1 条：`engine_candidate` / `engine_edge` / `engine_fixed_rule`，`ref` 精确到 `duan_zuogong.candidates[i]` 或 `e0xx` 或 `engine/predicates/types.py` 规则；
4. `source_ref` + `quote`：类规则锚点或施动句；`quote` 必须逐字；例如墓可用 `未墓寅` 类定向句（禁止用位移句 `寅入未墓` 当 actor 依据）；
5. `decisive=true` 当且仅当：端点唯一、actor/target 规则无歧义、校验 pass、无互斥固定候选；
6. `conflict_with` 按卡 v2 §3.4 计算；固定类冲突（如克 vs 墓对同一端点）必须显式列出。

#### 2.3 A 的判定

固定类候选只有在以下全部成立时 `direction_tier=A`：

- 恰 1 条 `decisive=true`，且无其他冲突候选；
- `engine_validation` 对该候选全 pass（edge 可 `not_applicable`，需写 `G3` / `muku_no_edge`）；
- `source_ref` + `quote` 逐字；`basis` 至少 1 条 `engine_candidate` / `engine_fixed_rule`；仅 `same_page`/source-only 依据不得升 A（可保留为 B1 候选）；
- 元数据：`decision_by=engine_fixed`、`provenance.kind=engine_fixed`、`selection_source=agent_auto`、`pending=none`（A 由引擎确定性落定，不等人工；**「不代选」只约束 B/C**）。

以下任一 → 不得 A：

- 多条固定候选互斥（克 vs 生/墓对同一端点）；
- 端点同字多位、无法消歧；
- 只有位移句/条件未满足句/纯吉凶句；
- 只有 `same_page`/source-only 依据，没有 `engine_candidate` / `engine_fixed_rule`；
- engine 候选缺失且五行表兜底有歧义；
- 穿制/救应依赖；
- 校验失败（伪造 → void；非伪造 → C）。

#### 2.4 固定类冲突

- 候选数 ≥2 且至少一对冲突 → `direction_tier` 不能 A。
- 若能构造 B1 事实题 → B1；否则 B2；无源/校验失败 → C。
- 不得为了保 A 而删掉冲突候选；冲突必须保留并显式记录。

### Step 3：动态类通过（冲/合/穿/刑/破）

#### 3.1 铁律

- **动态永不 A**，即使只有 1 条 decisive 候选、原文无冲突。
- 不得由 engine 边直接给 `actor/target`；engine 对 `chong/he/chuan/xing/po` 的 `actor=null` 是事实，不是缺口可补。
- 候选必须同时有 `engine_edge` + `source_directive`；只有 engine 边 → 不是方向候选，只是关系事实。
- 没有施动句 → 无候选 → C（`no_source` / `no_candidate`）；不得用五行/常识补 actor。

#### 3.2 原文筛选

对每条边（`edge_id/kind/members`）：

1. 用两端字 + `kind` + 问题域调 `query_theory`；必要时回 `sources/` 读上下文；
2. 只保留**施动句/互动词**：
   - 主动：`A冲B` / `A合B` / `A穿B` / `A刑B` / `A破B`；`A把B…`；
   - 被动：`B被A穿` / `B被A冲` / `B被A所刑`；
   - 互文：`A与B相冲` / `互冲` / `两伤` / `互相穿`；
3. 丢弃：并列列举（`酉戌穿,丑午穿`）、位移句（`X入Y墓`）、条件未满足句、纯吉凶句、只描述关系种类不给施受的句子；
4. 逐字记录 `source_ref` + `quote`；不得拼接/改写/省略到改变语义。

#### 3.3 地址映射

- 句中的字必须能在本盘定位；字只出现一次 → 唯一地址；出现多次 → 需要句中的宫位/位置词（年/月/日/时/坐下/主位/宾位）或 edge members 消歧；仍不能 → 该候选 `decisive=false`，层 C。
- 不得把天干/藏干当支端点；不得把岁运字当原局端点（P0/P1）。
- `合`：若原文只写「合」不写谁合谁，最多生成 `mutual` 候选；若只写「合化/合绊」而不给施受，不生成方向候选（可生成 state 候选）。

#### 3.4 候选与冲突

- 1–3 条候选（1 条 → B2 确认；2–3 条 → B1/B2 消歧）；每条 `claim` + `basis`（`engine_edge` + `source_directive`）+ `source_ref` + `quote` + `decisive` + `conflict_with`。
- `decisive=true` 条件同卡 v2 §3.5；动态候选不得因「engine 边存在」而 decisive。
- `conflict_with` 按卡 v2 §3.4；必须对称。
- `conflict_class`：
  - `chuan_zhi`：穿制冲突（§3.5）；
  - `source_contradiction`：两条原文语义相反；
  - `null`：普通方向冲突。

#### 3.5 穿制冲突（固定 C）

以下任一 → `conflict_class="chuan_zhi"`、`decisive=false`、该层 C：

1. 候选把「穿」当「制」的施力机制（`chuan` + 制用）；
2. 同一对端点出现相反原文：
   - `21:L2425`「穿制不了对方是一种坏，冲合克都可以制，唯有穿制不了。」
   - `22:L2252`「戌酉穿， 羊刃穿了官杀库」（同段又有「为羊刃穿制了官库」）
3. 候选依赖「一方必须有很强大的力量制另一方」，但本卡没有整数化力量证据。

处理：`anchor_request.blocked_reason="chuan_zhi"`；`what_would_unblock` 写「个案条件/力量整数化/新的裁决规格」；不得用一句消去另一句；引用 `docs/specs/party-direction-v1.md` §3.4 仅作为冲突记录，不复活党势方向。

#### 3.6 动态 tier

| 情况 | tier |
|---|---|
| 0 条有源候选 | C（`no_source`/`no_candidate`） |
| 1 条 decisive 候选，无冲突 | **B2**（专家确认/`needs_anchor`）；不得 A；单候选不构成 B1 消歧 |
| 2–3 条冲突候选，全部有源/校验 pass，无穿制 | 能构造事实题 → B1；否则 B2 |
| 2–3 条冲突，但任一无源/穿制/校验失败 | C |
| >3 条冲突 | 按 §3.7 取 3 条，记录 overflow；B1/B2（不得 A） |

#### 3.7 候选排序与截断

- 排序键（确定性）：`decisive=true` 优先；`basis` 中 `source_directive` + `engine_edge` 优先；quote 长度更短/更直接优先；柱序 `Y→M→D→H`；`option_id`。
- 超过 3 条：保留前 3 条，其余写入 `gaps` / `candidate_overflow`；不得静默丢弃。

### Step 4：成败候选（state）

- 来源：`structures[].items[]`（`status` ∈ met/unmet/not_evaluable/needs_judgment）、`relations.muku.openers/binders`、原文判据。
- 生成 1–3 条 `state_candidates`：
  - `成局`：结构项 met + 无 breaker met + 原文判据；
  - `破局`：breaker met 或边对目标构成冲/刑/穿/破 + 原文判据；
  - `逢救应化解`：rescuer met + 救应原语 + 外部审计编号；v2 缺原语 → 只候选，不选。
- `decisive=true` 仅当 `basis` 有 met/unmet 的结构项或明确原文判据；`needs_judgment`/`not_evaluable` → false。
- `state_scope`：
  - `selected`：恰 1 条 decisive 无冲突 → `state_selection_source=agent_auto`；2–3 条冲突时，只有方向层已是 B1 且同一 `anchor_q` 能消歧才随之选，否则 → C（`state_conflict`）；无源 → C 或 `not_claimed`（若 statement 不声称成败）。
  - `not_claimed`：0 条或只列备选；`state=null`；statement 不写成败。
- 不得「有冲边就破局」；不得把救应当「没发生」；不得写「库已开/已闭」。

### Step 5：救应候选（rescue）

- 来源：`structures[].items[kind=rescuer]`、`relations.muku.openers/binders`、原文。
- 生成 0–3 条 `rescue_candidates`：`rescuer` / `rescued` / `status`（candidate_met/candidate_unmet/not_evaluable）/ `rescue_primitive=null` / `external_audit_id=null` / `basis` / `source_ref` / `quote` / `decisive=false` / `conflict_with`。
- `rescue_scope`：
  - `not_claimed`：无候选；`selected_rescue=null`；`rescue_judged=未判`；
  - `candidate_only`：有候选但不得选；若救应材料影响方向/成败 → 卡 C（`rescue_primitive_missing`）。
- 不得把 `met` 说成化解/成格；不得写「有救/无救」结论。

### Step 6：引擎校验（候选级 + 卡级）

对每条候选逐项：

| 项 | 检查 | 失败 |
|---|---|---|
| address | 地址存在、同快照、非藏干、同字消歧 | 未知地址 → void；歧义 → C/候选 discard |
| edge | `edge_id` 存在、kind/members 一致、同快照；固定类无 edge → `not_applicable` + reason | 伪造/错配 → void |
| ten_god | 引用十神与 engine 一致；藏干十神用藏干字段；岁运十神不可得写缺口 | 不符 → void；不可得 → C |
| quote | `source_ref` 可解析；quote 逐字命中；含 OCR 空格；不拼接 | 不逐字/找不到 → void |
| seeded_error | 卡内无 seeded token；self_test 100% | 命中 → void；self_test <100% → P0 hard kill |

- 候选级失败：丢弃该候选，记录 `validation_fail`；若所有候选被丢弃 → 层 C。
- 卡级失败：伪造/错配 → `card_status="void"`（不是 C）；不得交付。
- 校验通过后才允许进入 A/B1/B2；B1/B2 只能在通过校验的候选之间消歧。

### Step 7：候选集装配

- `option_id` 按层独立编号：`D1..D3` / `S1..S3` / `R1..R3`。
- `conflict_with` 对称；冲突图不允许自环。
- `basis` 排序固定：`engine_edge` / `engine_candidate` / `engine_fixed_rule` / `source_directive` / `source_rule` / `structure_item` / `gap`。
- 记录 `gaps`：无源、同字多位、G3/G4/G5、穿制、`suiyun_ten_god`、`muku_open_close`。
- 记录 `non_claims`：不判吉凶/应期/事件/概率/化解/党势。

### Step 8：分层 tier + 卡级 tier

| 层 | 允许 tier |
|---|---|
| direction | A（仅固定类）/ B1 / B2 / C |
| state | A（已选或 not_claimed）/ B1 / B2 / C / not_claimed |
| rescue | not_claimed / C（candidate_only 且影响结论时） |

- 卡级 `tier = max(A<B1<B2<C)`；`not_claimed` 不参与取最高。
- 动态方向层永远不是 A；若 state A + direction B1 → 卡 B1。
- `decision_by` / `selection_source` / `provenance.kind` 按卡 v2 §4.2 映射。

### Step 9：B1 / B2 / C 产物

- B1：1–2 个 `anchor_q` + `anchor_a`（见 §4）。
- B2：`expert_decision` 包（见 §5）。
- C：`anchor_request`（见 §6）。
- `pending` 语义：A 生成即 `none`；B1 等 `anchor_q`；B2 等 `expert_decision`；C 为 `none`（已挂起，等锚点）。A 不需要人，「不代选」只约束 B/C。
- 最终卡必须 `pending="none"`；B1/B2 未完成时输出 `pending="anchor_q"` / `"expert_decision"`，不得当作可交付卡。

## 4. B1 锚点问题生成（核心）

### 4.1 目标

用**命主已发生、可外部/记忆核验的事实**区分候选；人只答事实，不选候选。

### 4.2 问题生成步骤

1. 列出候选差异：`relation` / `actor` / `target` / `mutual` / `decisive` / 冲突对；
2. 为每个差异找「如果该候选成立，命主过去应发生过什么可观测事实」；事实必须是过去、具体窗口、二元可答；
3. 生成 1–2 个问题，使 yes/no 答案能淘汰至少一个候选；
4. 检查：每个候选至少有一条答案路径保留它；每个问题 yes/no 淘汰不同候选；答 unknown 不淘汰；
5. 检查问题文本不含候选 ID、方向词、吉凶词；不含「你选哪个/你觉得」；
6. 若无法在不泄漏候选的情况下生成问题 → 不进入 B1，转 B2。

### 4.3 问题字段

```json
{
  "qid": "Q1",
  "text": "<纯事实是非题>",
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
```

- 1–2 条；`qid` 唯一；`fact_window` 具体；`fact_domain` 枚举。
- `discriminates` ≥2；`elimination` 覆盖 yes/no/unknown；每条 `eliminates` 至少 1 个（unknown 可为空）。
- 问题文本禁止词：`冲/合/穿/刑/克/生/化/墓/用神/忌神/喜用/身强/身弱`、`D1/D2`、`A/B/C`、`→`。
- 问题必须是「是否发生过」；不得问「会不会」「是不是性格」「你倾向哪个」。

### 4.4 答题与收敛

- 答题者只看 `text` / `fact_window` / `answer_type`；**不看** `discriminates` / `elimination` / `direction_candidates`。
- `anchor_q` 与 `elimination` 必须在答题前冻结（记录 hash）；答题后不得改；否则该 B1 作废。
- 答案 ∈ {yes,no,unknown}；写入 `anchor_a`，带 `answered_by` / `answered_at`。
- Agent 按 `elimination` 机械淘汰：
  - 恰剩 1 条 → `selected_option` = 幸存；`decision_by=anchor_fact`；`selection_source=human_fork`；`tier=B1`；
  - 剩 0 条 → C（`anchor_inconsistent`）；
  - 剩 >1 条且还有第 2 问 → 继续；2 问后仍 >1 → C（`anchor_insufficient`）；
  - 任何 `unknown` 导致无法收敛 → C（`anchor_unknown`）。
- 锚点事实只用于淘汰；不得进入评分标签/训练/调参（目标文档 `anchor_fact_leakage=0`）。

### 4.5 角色隔离

- 候选生成者不得回答锚点问题；锚点答题者不得是评分者；评分者不得看锚点答案用于标签。
- 答题者盲态声明写入 P0/P1 报告（`anchor_answerer_blind=true`）。
- B1 的 `selection_source=human_fork` 只表示「人的事实输入决定了淘汰」，不表示「人挑了候选」。

## 5. B2 专家包

### 5.1 何时 B2

- 1–3 条有源候选，但**没有任何可观测的已发生事实**能区分（生成器无法生成 §4 的问题而不泄漏候选）；
- 1 条 decisive 候选、无冲突（无法构造 B1 消歧；专家确认或 `needs_anchor`）。

### 5.2 专家包内容

- 候选列表：`option_id` / `claim` / `basis` / `source_ref` / `quote` / `conflict_with`；
- 冲突摘要：哪些候选互斥、为什么；
- 缺口：`gaps` / `non_claims`；
- 不给 `agent_top1` 推荐，避免锚定。

### 5.3 专家裁决

```json
{
  "option_id": "D1",
  "expert_id": "expert-1",
  "source_ref": "sources/...:Lx-Ly",
  "quote": "<逐字原文>",
  "reason": "<为什么该候选优于其他；必须引原文，不得只写经验>",
  "decided_at": "<RFC3339>"
}
```

- 专家只能选候选集内 `decisive=true` 的候选，或写 `needs_anchor`（→ C）。
- `source_ref` + `quote` 必须支持该候选，不是只支持类规则。
- 专家 ≠ 候选生成者 ≠ 评分者 ≠ 锚点答题者；B2 占比 P1 ≤30%。

## 6. C 锚点请求

```json
{
  "target_layer": "direction|state|rescue",
  "need": "<缺什么>",
  "blocked_reason": "no_source|chuan_zhi|validation_fail|anchor_unknown|anchor_insufficient|anchor_inconsistent|rescue_primitive_missing|no_candidate|state_conflict",
  "what_would_unblock": "<可检验的解锁条件>"
}
```

- C 卡 `selected_option=null`、`selection_source=needs_anchor`、`decision_by=needs_anchor`。
- 补锚点后必须重跑生成器 + 校验；不得手工改 `selected_option`。
- C 卡不得写成结论；不得用猜测补源。

## 7. 候选集输出 schema

```json
{
  "schema": "agent-candidate-set/v1",
  "card_id": "CARD-001",
  "case_id": "CASE-001",
  "snapshot": {"chart_id": "cf-...", "dayun_index": null, "liunian_year": null},
  "card_status": "valid|void",
  "direction_candidates": [],
  "direction_tier": "A|B1|B2|C",
  "selected_option": "D1|null",
  "selection_source": "agent_auto|human_fork|needs_anchor",
  "state_scope": "selected|not_claimed",
  "state_candidates": [],
  "state_tier": "A|B1|B2|C|not_claimed",
  "selected_state": "S1|null",
  "state_selection_source": "agent_auto|human_fork|needs_anchor|null",
  "rescue_scope": "not_claimed|candidate_only",
  "rescue_candidates": [],
  "rescue_tier": "not_claimed|C",
  "selected_rescue": null,
  "rescue_selection_source": null,
  "tier": "A|B1|B2|C|null",
  "decision_by": "engine_fixed|anchor_fact|expert_judgment|needs_anchor",
  "provenance": {},
  "anchor_q": [],
  "anchor_a": [],
  "expert_decision": null,
  "anchor_request": null,
  "pending": "none|anchor_q|expert_decision",
  "engine_validation": {},
  "gaps": [],
  "non_claims": []
}
```

- 字段名与卡 v2 一致；卡片装配时把 `direction_candidates` 放入 `t2_role_and_force`，`state_candidates` / `rescue_candidates` 放入 `t3_outcome`。
- `direction_tier` / `state_tier` / `rescue_tier` 是生成器审计字段；卡 v2 只保留卡级 `tier` + `tier_reason`，装配时把分层 tier 写入 `tier_reason`（如 `direction:anchor_conflict`）。
- `pending != "none"` 时不是可交付卡；B1/B2 完成后才置 `none`。
- `void` 时 `tier=null`、`card_status=void`、`decision_by=needs_anchor`、`void_reason` 非空。

## 8. 确定性与 `agent_top1`

### 8.1 确定性

- 同一输入（CLI JSON + 问题 + 快照 + 原文版本）必须产出同一候选集；排序稳定；不使用随机数；`generated_at` 只写元数据，不参与选择。
- 输入 hash：`engine_cli_sha256` / `source_refs_sha256` / `question_sha256`；写入 `provenance`（可选）。
- 重跑必须重新走 CLI，不得复用上次候选。

### 8.2 `agent_top1`（B1 lift 基线）

在锚点答案之前，从 `decisive=true` 候选中按以下确定性规则选 1 条，记为 `agent_top1`：

1. `basis` 同时含 `engine_edge` + `source_directive` 的候选优先；
2. 其次 `source_directive` 更直接（quote 更短、施动句无被动/条件）优先；
3. 再次柱序 `Y→M→D→H`（actor 在先）；
4. 最后 `option_id` 字典序。

- `agent_top1` 必须在看锚点答案前写入报告并冻结；B1 lift = B1 准确率 − `agent_top1` 准确率。
- `agent_top1` 只作基线，不作为卡选择；不得因锚点答案回头改。

## 9. 分层 tier 判定表（汇总）

| 条件 | direction_tier | state_tier | rescue_tier | 卡 tier | decision_by |
|---|---|---|---|---|---|
| 固定单条 decisive，校验 pass，无冲突 | A | A 或 not_claimed | not_claimed | A | engine_fixed |
| 固定冲突 / 动态 2–3 冲突，有事实题 | B1 | A/B1/not_claimed | not_claimed | B1 | anchor_fact |
| 固定冲突 / 动态，无事实可辨 | B2 | A/not_claimed | not_claimed | B2 | expert_judgment |
| 无源 / 穿制 / 校验失败 / 锚点不收敛 / 救应缺原语 | C | 任意 | C 或 not_claimed | C | needs_anchor |
| 伪造地址/边/十神/引文 | — | — | — | `void` | needs_anchor |

**优先级**：`void` > C > B2 > B1 > A。任何 C 层把卡拉到 C；任何伪造把卡作废。

## 10. 禁止

- 动态 A：`chong/he/chuan/xing/po` 被自动选中；`selection_source=agent_auto` 的动态卡。
- 由 engine 边直接给动态 actor/target；用五行/常识补 `actor`；把 `can_control` 当「制得住」。
- 伪造边/地址/十神/引文；跨快照；藏干当地址；编造 `edge_id`。
- 把 `mutual` 写成单向；把 `合` 写成有向；把 `墓` actor 写入库方；把 `化` actor 写被化者。
- 穿制冲突下硬选一边；用一句原文消去相反原文。
- B1 问题里出现候选/方向词，或让人看候选后挑；锚点事实进评分。
- B2 专家由生成者/评分者兼任；专家无 `source_ref`/`quote` 裁决。
- 把 C 写成结论；把 `void` 卡混入统计；把 `met` 写成成格/化解。
- 读答案/restricted/旧 3 卡/盲集 locator；复活 A+/党势；改保护区；做 git 写；跑盲测。

## 11. 示例（字段形状，不是评测样本）

> `quote` 用占位；真实卡逐字复制。示例不对应真实盘，不使用旧 3 卡/盲集。

### 11.1 固定墓 → A

```json
{
  "direction_tier": "A",
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
  "tier": "A",
  "decision_by": "engine_fixed",
  "pending": "none"
}
```

### 11.2 动态冲 → B1

```json
{
  "direction_tier": "B1",
  "direction_candidates": [
    {"option_id": "D1", "claim": {"relation": "chong", "direction": "actor_to_target", "members": ["D.b", "H.b"], "actor": "D.b", "target": "H.b"}, "decisive": true, "conflict_with": ["D2"]},
    {"option_id": "D2", "claim": {"relation": "chong", "direction": "mutual", "members": ["D.b", "H.b"], "actor": null, "target": null}, "decisive": true, "conflict_with": ["D1"]}
  ],
  "anchor_q": [{"qid": "Q1", "text": "<纯事实是非题>", "fact_window": "2021-01..2021-12", "fact_domain": "career", "answer_type": "yes_no", "discriminates": ["D1", "D2"], "elimination": [{"answer": "yes", "eliminates": ["D1"], "keeps": ["D2"]}, {"answer": "no", "eliminates": ["D2"], "keeps": ["D1"]}, {"answer": "unknown", "eliminates": [], "keeps": ["D1", "D2"]}]}],
  "anchor_a": [{"qid": "Q1", "answer": "yes", "answered_by": "anchor-1", "answered_at": "<RFC3339>", "note": ""}],
  "selected_option": "D2",
  "selection_source": "human_fork",
  "tier": "B1",
  "decision_by": "anchor_fact",
  "pending": "none"
}
```

### 11.3 动态穿 → B2

```json
{
  "direction_tier": "B2",
  "direction_candidates": [
    {"option_id": "D1", "claim": {"relation": "chuan", "direction": "actor_to_target", "members": ["Y.b", "H.b"], "actor": "Y.b", "target": "H.b"}, "decisive": true, "conflict_with": ["D2"]},
    {"option_id": "D2", "claim": {"relation": "chuan", "direction": "actor_to_target", "members": ["Y.b", "H.b"], "actor": "H.b", "target": "Y.b"}, "decisive": true, "conflict_with": ["D1"]}
  ],
  "anchor_q": [],
  "anchor_a": [],
  "expert_decision": {"option_id": "D1", "expert_id": "expert-1", "source_ref": "sources/duan/....md:L000", "quote": "<逐字原文占位>", "reason": "<引原文说明 D1 优于 D2>", "decided_at": "<RFC3339>"},
  "selected_option": "D1",
  "selection_source": "human_fork",
  "tier": "B2",
  "decision_by": "expert_judgment",
  "pending": "none"
}
```

### 11.4 穿制 → C

```json
{
  "direction_tier": "C",
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
  "selection_source": "needs_anchor",
  "anchor_request": {"target_layer": "direction", "need": "<个案条件/力量整数化/新裁决规格>", "blocked_reason": "chuan_zhi", "what_would_unblock": "<可检验条件>"},
  "tier": "C",
  "decision_by": "needs_anchor",
  "pending": "none"
}
```

## 12. Cross-References

- 目标/gate/角色：[`docs/goals/first-principle-agent-first-v1.md`](../goals/first-principle-agent-first-v1.md)
- 卡 v2（字段名以此为准）：[`docs/specs/analysis-card-v2.md`](analysis-card-v2.md)
- 卡 v1：[`docs/specs/single-chart-analysis-v1.md`](single-chart-analysis-v1.md)
- actor 规则：[`docs/specs/actor-rules-v1.md`](actor-rules-v1.md)
- 事实证据包：[`docs/specs/fact-evidence-pack-v1.md`](fact-evidence-pack-v1.md)
- A+ 裁决：[`docs/reviews/t191-a-plus-verdict-v1.md`](../reviews/t191-a-plus-verdict-v1.md)
- 归档治理：[`archive/adjudication_v1/README.md`](../../archive/adjudication_v1/README.md)
- 事实审计：[`META/fact-audit-v1.md`](../../META/fact-audit-v1.md)
- fixed-20：[`META/p1-fixed-20.md`](../../META/p1-fixed-20.md)
- R-tool 运行：[`META/r-tool-run-v1.json`](../../META/r-tool-run-v1.json) / [`META/r-tool-run-routing-v1.json`](../../META/r-tool-run-routing-v1.json)
- 工具入口：[`docs/agent_tools.md`](../agent_tools.md)
