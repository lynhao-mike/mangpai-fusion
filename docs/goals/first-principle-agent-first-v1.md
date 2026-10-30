# Goal Document: 第一性原则 · Agent-first v1

> 任务：`tasks/T-196/PROMPT.md`；状态：🔵 Ready（规格，不写代码、不跑盲测、不改保护区）
> 依据：A+ v1.3 方向产品 kill（`docs/reviews/t191-a-plus-verdict-v1.md`）；R-tool 事实/检索层（`docs/specs/fact-evidence-pack-v1.md`、`META/fact-audit-v1.md`、`META/p1-fixed-20.md`、`META/r-tool-run-v1.json`、`META/r-tool-run-routing-v1.json`）；人类同意 Agent-first + 人在关键点选择；中枢 2026-10-30 两次追加修正（A 只许固定类；B 拆 B1/B2；P0 只验管道与完整性）。
> 关联规格：`docs/specs/analysis-card-v2.md`（卡 v2，字段名以此为准）、`docs/specs/agent-candidate-generator-v1.md`（候选生成器）。
> 保护区：不改 `AGENTS.md` §4、`templates/report-v7-human.md`、`engine/**`、答案/测试/`pyproject.toml`/`requirements*.txt`；不做 git 写；不跑盲测。

## Go / No-Go

- **Judgment**: **Go（仅规格；P0/P1/P2 尚未执行）**
- **Reason**: A+ v1.3 已按预注册死线 kill 自动方向产品；R-tool 事实层已证明「排盘/关系/固定类事实」可用，但冲/合/穿/刑没有可自动承诺的方向。唯一诚实的下一步不是换阈值复活方向，而是把卡拆成「事实 + 候选 + 锚点消歧」：A 只给固定克/生/化/墓；B1 用命主已发生事实淘汰候选；B2 在无事实可辨时由专家单选；C 明确挂起。T-196 只冻结这套规格，不执行统计 gate。

## Target Outcome

在本规格通过中枢验收后，系统对一张真实八字 + 一个真实问题能产出一张**可回查的卡 v2**，并满足：

1. **卡 v2 完整**：五元组不丢；`direction_candidates[]` / `state_candidates[]` / `rescue_candidates[]` 各 0–3 条（有多个有源备选时 2–3；不适用时显式 `not_claimed`）；每条候选带 `basis` / `source_ref` / 逐字 `quote` / `decisive` / `conflict_with`。
2. **选择可追溯**：`tier ∈ {A, B1, B2, C}` 与 `decision_by ∈ {engine_fixed, anchor_fact, expert_judgment, needs_anchor}` 一一对应；A 只用于固定克/生/化/墓；冲/合/穿/刑一律 B1/B2/C，永不 A。
3. **人只做关键点**：A 无人；B1 人只答 1–2 个「命主已发生事实」的是非题，**不选候选**；B2 专家单选或 `needs_anchor`，必须带 `source_ref` + `quote`；C 由人补锚点，不猜。
4. **校验可机检**：`engine_validation` 覆盖 `address / edge / ten_god / quote / seeded_error`；伪造边/地址/十神/引文直接 `card_status="void"`；seeded 错误检测 100%。
5. **Gate 冻结**：P0 只验管道与完整性（编造/泄漏 hard kill），P1 验候选召回/A/B1/B2/C，P2 验外部可查事件的概率预测；阈值先冻结，跑后不移。
6. **不复活**：不恢复 A+、不写党势方向、不把旧 3 卡当证明、不把固定事实写成结论。

## Goal Definition

- **Type**: product / technical spec
- **Boundary**:
  - 含：三份规格（本文件、卡 v2、候选生成器 v1）；A/B1/B2/C 定义；P0/P1/P2 gate 与 kill；校验字段；角色隔离；与 R-tool / fixed-20 / anchor-60 的边界。
  - 不含：代码实现、engine/规则/答案/测试修改、盲测执行、真实盘的最终方向裁决、岁运以外的 P2 扩张、报告模板改造。
- **Non-goals**:
  - 不复活自动方向产品；不恢复 A+ v1.3 阈值；不写 `party-direction-v2`；不做党势方向。
  - 不用 3 张旧卡（`archive/demo/`）做演示/测试/能力证明。
  - 不碰 `AGENTS.md` §4、`templates/report-v7-human.md`、`docs/analysis_human_touch.md`。
  - 不跑盲测、不评分、不做 git 写；P0/P1/P2 只冻结规格。
- **Deferred work**:
  - P0/P1/P2 的实际执行与报告；
  - 救应原语（G5）与 `rescue_judged=已判` 的外部审计编号；
  - 岁运多快照卡（P2 范围，P0/P1 不扩）；
  - 理论检索召回率（routing v1 未评分，见 Current State）。
- **Verification rule**:
  - T-196：三份文档存在、互相引用、字段名一致；`BRIEF.md` / `STATUS.md` 记录完整；不改保护区。
  - 产品：P0 过 hard gate 后进 P1；P1 过 gate 且不触 kill 后进 P2；P2 过 gate 且不触 kill 才算预测能力成立。
- **Evidence source**:
  - 引擎事实：`python -m engine.cli all|chart|relations|structures --json`；
  - 理论：`python -m tools.query_theory ... --json` 与 `sources/**` 逐字原文；
  - 评测：P0/P1/P2 预注册报告、seeded-error 报告、第三方重推记录、P2 Brier/对照。
- **Pass criteria**:
  - 规格层：三份文档 + BRIEF + STATUS；字段名一致；A 只固定类；动态永不 A；B1 只答事实；B2 有上限；C 有 `anchor_request`；P0/P1/P2 gate 与 kill 写死。
  - 执行层：P0 hard gate 全绿；P1 gate 全绿且不触 kill；P2 gate 全绿且不触 kill。
- **Confidence note**:
  - R-tool 的 fixed-20 是 20/20 覆盖 + 0 类外，但 3 条靠 `engine_element_rule` / `engine_pair_fallback`（`class_source_breakdown` 17/2/1），且 fixed-20 仍待 B 复核；不能把 20/20 当成方向能力。
  - 事实审计离散 1500/0，但 `precise_start_*` 严格 0 差异未达成（`META/fact-audit-v1.md`：50 项全为时刻类，最大 829s，按 120×节气秒差传播）；本规格不把精确交运时刻用作卡端点，也不宣称秒级独立 100%。
  - routing v1 因 `expected_evidence` 受限字段进入上下文而 `blind_valid=false`；routing v2 用脱敏 runner 视图重跑，`blind_valid=true`、15 题、116 个证据项、0 类外，但**召回尚未评分**。
- **Judgment owner**: 中枢（规格验收）+ 人类（产品口径/保护区授权）；P1/P2 最终由独立评分者与人类盲审，不由候选生成者自评。

## First Principle（第一性原则）

### 1. 事实 / 候选 / 选择三层

1. **事实层**（`engine.cli` + `query_theory` + `sources/`）：只回答「盘上有什么」——四柱、十神、藏干、旬空、关系边、墓库、结构项、原文锚点。事实层不产生方向，不产生吉凶，不产生应期。
2. **候选层**（Agent 候选生成器）：把事实 + 原文转成 1–3 条**可回查的候选**。每条候选必须能指回 `edge_id` / 地址 / `source_ref` / 逐字 `quote`；候选不是结论，`decisive` 只是「这条候选在证据上是否足以单独成立」。
3. **选择层**（A/B1/B2/C）：A 由固定规则自动；B1 由命主已发生事实淘汰候选；B2 由专家在无事实可辨时单选；C 挂起等锚点。**人永远不凭感觉挑候选**；人只提供事实或专家裁决。

> 一句话：过去失败在「让模型直接给方向」；本规格把方向拆成「候选生成」与「事实淘汰」两件事，自动只保留给固定类。

### 2. 角色与禁止兼任

| 角色 | 做什么 | 不做什么 |
|---|---|---|
| 引擎（`engine.cli`） | 排盘、关系边、十神、藏干、旬空、墓库、结构项；固定克/生/化/墓事实 | 不给冲/合/穿/刑方向；不下结论 |
| 理论检索（`query_theory`） | 返回 `entry_id` / `source_ref` / 原文行 | 不自动裁决；命中≠成立 |
| 候选生成器（Agent） | 生成候选、`basis`、`source_ref`、逐字 `quote`、`engine_validation`、B1 锚点问题、B2 候选包 | 不回答锚点问题；不评分；不自选 B1/B2；不自动承诺动态方向 |
| 锚点答题者（命主/知情者） | 只回答 1–2 个「已发生事实」的是非题 | 不选候选；不看候选方向；不预测未来 |
| 专家（B2） | 在无事实可辨时单选一个候选或 `needs_anchor`，必须带 `source_ref` + `quote` | 不生成候选；不评分；不回答锚点事实 |
| 评分/审计者 | 预注册标签、第三方重推、P1/P2 评分、seeded-error 审计 | 不生成候选；不回答锚点；不做 B2 专家 |
| 中枢/人类 | 验收规格、批准保护区变更、决定产品口径 | 不静默移阈值；不把失败重跑成通过 |

**硬隔离**：同一张卡上，候选生成者 ≠ 锚点答题者 ≠ 评分者；B2 专家也不得由候选生成者或评分者兼任。**锚点事实只能用于淘汰候选，不得进入评分标签**（见 §Metrics 的 `anchor_fact_leakage`）。

### 3. 为什么冲/合/穿/刑不能 A

- A+ v1.3 已证明：动态方向 3 次一致率 47.5%、margin +3、引文违规 18/20；再调阈值只会把失败藏起来（`docs/reviews/t191-a-plus-verdict-v1.md` §2–§4）。
- 「原文没有冲突」是**语料级判断**，不是单卡事实；同一对干支在不同书/不同句里可能给出相反施力方（如穿制：`21:L2425`「穿制不了对方是一种坏，冲合克都可以制，唯有穿制不了。」 vs `22:L2252`「戌酉穿， 羊刃穿了官杀库」……「为羊刃穿制了官库」）。
- 因此：**冲/合/穿/刑一律 B1/B2/C**；A 只保留给引擎固定规则能唯一确定的克/生/化/墓。动态候选可以很准，但必须经过事实淘汰或专家裁决，不能自动承诺。

## Current State

- **A+ 已 kill**：`docs/reviews/t191-a-plus-verdict-v1.md`、`archive/adjudication_v1/README.md`（`DISPOSITION: KILLED`）；fixed 10/10 通过，dynamic 3-run 一致 19/40 = 47.5%，margin +3，chart macro 72.5%，ambiguous 1/10，引文违规 18/20；不调阈值、不重跑同卷、不复活党势。
- **事实层**：离散事实 1500/0（四柱/日主/藏干/十神/旬空/粗略起运/大运干支与起止年）；`precise_start_*` 50 项差异全为时刻类，最大 829s，按 120×节气秒差传播，残差 <1s，未解释 0；严格 0 差异未达成，按卡判不通过，中枢判 **scoped pass**（`META/fact-audit-v1.md` §7）。
- **fixed-20**：20 条 / 20 盘，覆盖 20/20，`out_of_class_emissions=0`；来源分布 `engine_candidate 17 / engine_element_rule 2 / engine_pair_fallback 1`，3 条 mismatch（F20-009/013/014）；仍待 B 复核（`META/p1-fixed-20.md` §1–§7）。
- **R-tool 运行**：`META/r-tool-run-v1.json` fixed-20 20/20、0 类外；routing 15 题因 `expected_evidence` 受限字段进入上下文而 `blind_valid=false`。`META/r-tool-run-routing-v1.json` 用脱敏 runner 视图重跑，`blind_valid=true`、15 题、116 个证据项（宫位 37 / 边 49 / source_ref 30）、0 类外；**召回未评分**。
- **卡 v1**：`docs/specs/single-chart-analysis-v1.md` 已有五元组、L01–L21、快照隔离、三态；本规格在其上加候选层与 A/B1/B2/C，不改 v1 文件。
- **旧 3 卡**：`archive/demo/single-chart-cards-v1.md` / `.json` 已封存为 `ARCHIVED_RESEARCH_ARTIFACT`，不得作为演示、测试样例、能力证明或评测输入。
- **T-197 P0 反馈（据中枢 2026-10-30 转述）**：12 卡中 A=3/12=25%，B1 事实题 6 个已交人类，B2=0；A 25% 是「冲/合/穿/刑禁 A」后的真实结构，**不是失败**，P0 不据此 kill；P0-01/P0-03 的 `same_page` 依据只作 B1 候选，不升 A。
- **已知缺口**：G2（动态边无 actor）、G3（支-支不建克边）、G4（藏干无独立地址）、G5（救应未判）、`no_spouse_star`、`muku_open_close`、`suiyun_ten_god`、`boundary_zi_shi`；穿制原文自相矛盾；fixed-20 未双人复核；routing 召回未测。
- **工作区**：分支 `main`，HEAD `1a773249`；任务卡写前置 `af22f270`，以工作区实际 HEAD 为准，记录在 `tasks/T-196/BRIEF.md`；本任务未做 git 写。

## Tier Model（A / B1 / B2 / C）

| tier | 允许的类 | `decision_by` | `selection_source` | 人的动作 | 成立条件 | 禁止 |
|---|---|---|---|---|---|---|
| **A** | 仅固定 **克/生/化/墓** | `engine_fixed` | `agent_auto` | 无 | 单一 `decisive` 固定候选；`engine_validation` 全 pass；state 选中或 `not_claimed`；rescue `not_claimed`；`provenance.kind=engine_fixed`；`pending=none` | 冲/合/穿/刑 A；冲突候选 A；无源 A |
| **B1** | 固定冲突或动态 | `anchor_fact` | `human_fork` | 只答 1–2 个「已发生事实」是非题，**不选候选** | 2–3 条有源冲突候选；`anchor_q` 能区分候选；答案淘汰后恰剩 1 条；`anchor_a` 完整 | 让人看候选后凭感觉挑；问题问未来/价值判断；答案用于评分 |
| **B2** | 固定冲突或动态 | `expert_judgment` | `human_fork` | 专家单选或 `needs_anchor` | 1–3 条有源候选（单条=确认；2–3 条=冲突且无可观测事实可辨）；`expert_decision` 带 `source_ref`+`quote`；P1 占比 ≤30% | 无源专家裁决；候选生成者兼任专家；B2 超上限 |
| **C** | 任意 | `needs_anchor` | `needs_anchor` | 补锚点/条件/救应原语 | 无源、穿制冲突、校验失败、锚点答不出/不够/矛盾、救应需原语、无候选、state 冲突无法消歧 | 把 C 写成结论；用猜测补锚点；静默改 tier |

**映射规则**：

- `tier=A` ⇒ `decision_by=engine_fixed` ⇒ `provenance.kind=engine_fixed` ⇒ `selection_source=agent_auto`。
- `tier=B1` ⇒ `decision_by=anchor_fact` ⇒ `provenance.kind=anchor_fact` ⇒ `selection_source=human_fork`。
- `tier=B2` ⇒ `decision_by=expert_judgment` ⇒ `provenance.kind=expert_judgment` ⇒ `selection_source=human_fork`。
- `tier=C` ⇒ `decision_by=needs_anchor` ⇒ `provenance.kind=needs_anchor` ⇒ `selection_source=needs_anchor`。
- 卡的 `tier` 取各层（direction/state/rescue）最高风险：`A < B1 < B2 < C`；`not_claimed` 层不参与取最高，但必须写 `*_scope="not_claimed"` 且 statement 不得声称该层。
- **动态永不 A**：即使动态只有一条 decisive 候选且原文无冲突，也只能 B2/C（单候选不构成 B1 消歧）；「原文无冲突」不能作为自动依据。

## Priority Rationale

1. **先卡后跑**：没有字段冻结，跑出来的结果无法复核；先冻结卡 v2 与生成器 v1，再谈 P0。
2. **P0 只验管道**：3–5 张卡先证明「字段齐、可回查、无编造、无泄漏、seeded 全抓」，不用小样本做统计 kill；小样本统计只会制造假阳性/假阴性。
3. **P1 再验候选与 A**：10–20 张卡上测候选召回、A 档自动率/精确率、B1 lift、B2/C 占比；这些指标直接对应「Agent-first 是否成立」。
4. **P2 最后验预测**：只有 P1 过 gate 才做 10–15 盘 / 20–40 外部可查事件的流月预测；P2 是产品承诺，不是规格自证。
5. **安全阀**：任何阶段出现伪造/泄漏/类外自动/引文漏，立即 hard kill，不进入下一阶段。

## Assumptions and Open Decisions

| Item | Status | Impact | Owner / Next step |
|---|---|---|---|
| 固定类（克/生/化/墓）足以支撑 P1 的 A≥90%（按固定类可 A 率） | assumed | 若固定类供给不足，P1 无法达标；需扩固定类案例或调整 P1 集合 | 中枢 + 策展；P1 前核 |
| T-197 的 A=3/12=25% 是真实结构而非失败 | confirmed | P0 不设 A 门槛；P1 才要求 A≥90% | 本规格；P0 报告只报告 |
| A 可由引擎确定性落定（engine_fixed/agent_auto/pending=none），「不代选」只约束 B/C | confirmed | A 不等待人工；B/C 才需要锚点/专家 | 生成器 §2.3/§3.9；卡 v2 §5.1 |
| B1 锚点问题能在不看候选的情况下由命主回答 | assumed | 若问题不可回答/会泄漏候选，B1 退化，B2/C 上升 | 候选生成器 + 锚点答题者隔离演练 |
| B2 占比在 P1 ≤30% | assumed | 若动态源普遍无事实可辨，B2 超限，P1 kill | P1 预注册时核 |
| C 占比在 P1 ≤50% | assumed | 若穿制/无源太多，C 超限，P1 kill | P1 预注册时核 |
| P2 能凑到 20–40 个外部可查事件、10–15 盘 | assumed | 凑不到则 P2 不启动，不硬跑 | 产品/人类；P2 前策展 |
| P2 Brier 能优于历史基率/交换盘/去引擎对照 | assumed | 若不能，P2 kill；不调窗口、不放宽 | 评分者 + 人类 |
| fixed-20 的 3 条 fallback（F20-009/013/014）不影响固定类 A 规则 | assumed | 若 B 复核推翻，固定类 A 需收紧为「engine_candidate 才 A」 | 中枢；B 复核后 |
| 事实审计的 `precise_start_*` 不进卡端点 | confirmed | 卡不依赖精确交运时刻；不宣称秒级 100% | 本规格 |
| routing 召回未评分 | confirmed | P0/P1 不引用 routing 召回作为能力证明 | 本规格 |
| 任务卡前置 `af22f270` 与工作区 HEAD `1a773249` 不一致 | confirmed | 仅记录，不影响规格内容；验收以工作区 diff 为准 | 中枢；BRIEF 记录 |

## Metrics（P0/P1/P2 共用定义）

| 指标 | 定义 | 备注 |
|---|---|---|
| `a_rate_fixed` | A 卡数 / 固定类卡数（克/生/化/墓） | A 只允许固定类；这是「固定类 A 档自动率」 |
| `a_precision` | 经独立复核仍成立的 A 卡数 / A 卡数 | 防止「为了 A 而 A」 |
| `a_share` | A 卡数 / 全部卡数（含 C） | 仅报告（P0 不设门槛；P1 的 A≥90% 是 A 档自动率/精确率，不是单纯占比） |
| `candidate_recall` | 预注册正确选项 ∈ 候选 `option_id` 集合的卡数 / 有可判选项的卡数（A/B1/B2；C 不计入分母） | 预注册标签由独立策展者给出，不得用锚点事实或生成器输出做标签；C≤50% 约束防止用 C 逃票 |
| `b1_lift_pp` | (B1 卡准确率 − `agent_top1` 准确率) × 100 | `agent_top1` = 锚点前确定性 top-1（规则见生成器 §8.2），P1 前冻结 |
| `b2_share` | B2 卡数 / 全部卡数 | P1 gate ≤30%；>30% kill |
| `c_share` | C 卡数 / 全部卡数 | P1 gate ≤50%；>60% kill |
| `human_minutes_per_card` | 每卡人工时间：A=0；B1=答题时间；B2=专家裁决时间；C=补锚点时间；报告均值与最大值 | P0 gate ≤5 分钟/卡；P1 目标 ≤15 |
| `third_party_reproduce_rate` | 第三方仅凭卡 + `engine.cli` + 原文，复推出同 `tier` / 同 `selected_option` / 同候选集合 / 同 `engine_validation` 的卡数 / 卡数 | P0 报告（不作 gate）；P1/P2 作为复核证据 |
| `unsourced_claims` | `statement_claims[]` 中无 `source_ref`/`quote`、引文非逐字、或 claim 无法指回候选/事实的条数 | 必须 0 |
| `out_of_class_auto` | 冲/合/穿/刑/破被自动选为 `selected_option` 的条数（含 B1/B2 之外的任何自动） | 必须 0；任何 >0 kill |
| `quote_verbatim_rate` | 逐字命中 `source_ref` 行区间的 quote 数 / quote 总数 | 必须 100%；任何漏 kill |
| `seeded_error_detection` | seeded 假地址/假边/假引文/假十神被校验器抓出的比例 | 必须 100%；<100% P0 kill |
| `fabricated_refs` | 不存在的地址/边/十神/引文条数 | 必须 0；任何 >0 `card_status=void` + P0 kill |
| `leakage_events` | 读取/引用答案、restricted、旧 3 卡、盲集 locator/case_id 的次数 | 必须 0；任何 >0 hard kill |
| `tier_misclassification` | 审计认为应降级/升级但卡写错的卡数 | P0 必须 0；P1 目标 0 |
| `anchor_fact_leakage` | 锚点事实被用于评分标签/训练/调参的次数 | 必须 0；任何 >0 hard kill |

## Phases（P0 / P1 / P2）

> 以下 phase 是**未来执行计划**，T-196 不执行；阈值在跑前冻结，不得事后移动，不得换同卷重跑到过。

### Phase P0：管道与完整性（3–5 卡）

- **Purpose**：证明卡 v2 + 生成器 v1 能产出完整、可回查、无编造、无泄漏的卡；并验 B1 ≤2 题、每卡 ≤5 分钟；A 占比只报告，不做统计能力判断。
- **Entry condition**：本文件、卡 v2、生成器 v1 经中枢验收；P0 卡集策展完成（非盲集、无答案、无 locator）；seeded fixture 就绪。
- **Phase rules**：
  - 卡集 3–5 张；建议 4 张：2 张固定 A（克/生/化/墓中至少 2 类）+ 1 张 B1 + 1 张 C；可选第 5 张 B2。**P0 不设 A 占比门槛**；A 只报告（T-197 实测 3/12=25% 是「冲/合/穿/刑禁 A」后的真实结构，不判失败）。
  - 每卡一个快照；P0 不扩岁运（`dayun_index=null`、`liunian_year=null`）。
  - 候选生成者、锚点答题者、评分者三角色分离；锚点事实不进入评分。
  - 不读答案/restricted/旧 3 卡/盲集 case_id；出包前跑 `tools.check_bundle_case_ids`（工具存在时）。
- **Todos**：
  - [ ] P0-1 策展 3–5 卡，登记 `case_id` / 四柱 / 问题 / 来源，确认与 anchor-60 / fixed-20 / dev-20 / holdout-20 / fresh-40 零重叠。
    - **Proof**: 卡集清单 + 零重叠核对记录。
  - [ ] P0-2 用生成器产出候选集与卡 v2；每卡填 `tier` / `decision_by` / `provenance` / `engine_validation` / `anchor_q/a` / `expert_decision`（按 tier）。A 必须 `pending=none`（engine_fixed / agent_auto，引擎确定性落定）；B/C 可 `pending` 到输入齐。
    - **Proof**: 卡 JSON 文件 + 字段完整性检查退出码 0。
  - [ ] P0-3 跑 seeded-error fixture：假地址/假边/假引文/假十神各 ≥5 例，校验器必须 100% 抓出。
    - **Proof**: seeded 报告 `detected/total=100%`；漏报 0。
  - [ ] P0-4 B1 锚点答题：答题者只看问题，不看候选；记录 1–2 个是非答案；生成器按淘汰表得出结论。
    - **Proof**: `anchor_q` / `anchor_a` / 淘汰记录；答题者盲态声明。
  - [ ] P0-5 第三方重推：第三方仅凭卡 + CLI + 原文复推 `tier` / `selected_option` / 候选集合 / `engine_validation`。
    - **Proof**: 逐卡重推记录；`third_party_reproduce_rate`。
  - [ ] P0-6 出 P0 报告：hard gate + 报告项 + 未完成/风险。
    - **Proof**: `tasks/<P0>/BRIEF.md` + 报告；中枢现场复核。
- **Hard Gate（kill）**：
  | 项 | 阈值 | 处置 |
  |---|---|---|
  | `fabricated_refs` | 0 | >0 → `card_status=void`，P0 kill |
  | `leakage_events` | 0 | >0 → P0 kill |
  | `seeded_error_detection` | 100% | <100% → P0 kill |
  | `out_of_class_auto` | 0 | >0 → P0 kill |
  | `unsourced_claims` | 0 | >0 → P0 kill |
  | 动态 A | 0 | >0 → P0 kill |
  | A 的 `pending` | `none` | A 仍 pending → P0 fail |
  | B1 `anchor_q` 数 | ≤2 / 卡 | >2 → P0 fail |
  | `human_minutes_per_card` | ≤5 分钟 / 卡 | >5 → P0 fail |
  | `tier_misclassification` | 0 | >0 → P0 fail |
  | 必填字段（按 tier） | 100% | 缺一 → P0 fail |
  | 角色隔离 / 锚点不评分 | 100% | 违反 → P0 kill |
- **说明**：`fail` 与 `kill` 都阻断进入 P1；`kill` 另要求记录原因、修规格/换新集，不重跑同卷。
- **Report（不作 kill）**：`a_share` 仅报告（T-197 3/12=25% 不判失败，P1 才要求 A≥90%）；`third_party_reproduce_rate` 目标 ≥90%（报告）；`candidate_recall` 仅报告。
- **Exit proof**: P0 报告 hard gate 全绿；seeded 100%；无 void/泄漏；字段完整性 100%；B1 锚点记录完整且 ≤2 题/≤5 分钟；A `pending=none`。
- **Stop condition**: 任一 hard gate 触发；或 B1 问题无法在不泄漏候选的情况下形成；或 P0 卡集无法满足零重叠。

### Phase P1：候选召回与 A/B1/B2/C（10–20 卡）

- **Purpose**：在独立预注册标签上测候选召回、A 档自动率/精确率、B1 事实淘汰的增益、B2/C 占比。
- **Entry condition**：P0 过 hard gate；P1 卡集与标签预注册并 hash；`agent_top1` 规则冻结；角色隔离演练完成。
- **Phase rules**：
  - 10–20 卡；固定类与动态类混合，至少 5 张固定类、5 张动态类，保证 A/B1/B2/C 指标可测；标签由独立策展者给出，候选生成者/锚点答题者/评分者不得兼任标签作者。
  - `candidate_recall` 的标签不得来自锚点事实；锚点事实只用于淘汰。
  - A 只允许固定类；动态卡一律 B1/B2/C。
  - 不调阈值、不换同卷重跑；失败后修规格/换新集。
- **Gate（全绿才进 P2）**：
  | 指标 | Gate |
  |---|---|
  | `candidate_recall` | ≥80% |
  | `a_rate_fixed` | ≥90% |
  | `a_precision` | ≥90% |
  | `b1_lift_pp` | ≥15pp |
  | `b2_share` | ≤30% |
  | `c_share` | ≤50% |
  | `out_of_class_auto` | 0 |
  | `quote_verbatim_rate` | 100% |
  | 硬项 | 伪造/泄漏/seed<100%/动态 A/无源断言/角色混用 = 0 |
- **Kill**：
  | 指标 | Kill |
  |---|---|
  | `candidate_recall` | <50% |
  | `a_rate_fixed` 或 `a_precision` | <80% |
  | `b1_lift_pp` | ≤3pp |
  | `c_share` | >60% |
  | `b2_share` | >30% |
  | `out_of_class_auto` | 任何 >0 |
  | `quote_verbatim_rate` | 任何 <100% |
  | 硬项 | 任何伪造/泄漏/动态 A/无源断言/角色混用 |
- **Gray（不 kill、不进 P2）**：`candidate_recall` 50–79%；A 80–89%；B1 lift 3–15pp；C 50–60%。记录后修规格/换新集，不重跑同卷。
- **Exit proof**: P1 报告 + 指标计算脚本输出 + 独立复核签字；gate 全绿且未触 kill。
- **Stop condition**: 任一 kill；或 B2/C 超限导致 P1 结构不成立；或标签/锚点隔离被破坏。

### Phase P2：外部可查事件的概率预测（10–15 盘 / 20–40 事件）

- **Purpose**：在 P1 通过的卡能力上，验证「2–3 互斥分支 + 皆非」的流月预测是否优于基率与对照。
- **Entry condition**：P1 gate 全绿且未触 kill；P2 事件集、窗口、分支、先验、评分规则预注册并 hash；盲评协议签署。
- **Phase rules**：
  - 10–15 盘、20–40 个外部可查事件；每个事件给 1–3 个月流月窗口。
  - 每个事件 2–3 个互斥分支 + 「皆非」；必须写先验；分支必须可外部核验。
  - 评分：Brier；对照：交换盘、去引擎、历史基率；盲评；预注册 hash 校验。
  - 窗口过期未解决按 miss 计分，不从分母剔除；只有「不可外部核验」的事件才剔除，剔除率 ≤30%。
- **Gate**：
  | 指标 | Gate |
  |---|---|
  | `event_count` | 20–40 |
  | `chart_count` | 10–15 |
  | `window_months` | 每事件 1–3 个月流月窗口，100% |
  | `priors_recorded` | 每个事件先验已记录，100% |
  | `scorable_rate` | ≥70% |
  | `unverifiable_exclusion_rate` | ≤30% |
  | 分支覆盖 | 2–3 互斥分支 + 皆非，100% |
  | Brier vs 历史基率 | 改善 ≥0.03 |
  | Brier vs 交换盘 | 交换盘更差 ≥0.03 |
  | Brier vs 去引擎 | 去引擎更差 ≥0.03 |
  | 预注册/盲评/window | hash 一致、盲评成立、过期按 miss |
  | 类外自动/引文/伪造/泄漏 | 0 |
- **Kill**：
  | 指标 | Kill |
  |---|---|
  | `scorable_rate` | <50% |
  | `unverifiable_exclusion_rate` | >30% |
  | Brier vs 历史基率 | 改善 ≤0 |
  | 交换盘/去引擎对照 | 未变差（无法证明不是噪声） |
  | 分支覆盖 | <100% |
  | 预注册/window/先验/盲评 | 任一违反（含过期放宽、先验事后补） |
  | 类外自动/引文/伪造/泄漏 | 任何 >0 |
- **Gray（不 kill、不宣称通过）**：`scorable_rate` 50–69%；Brier 改善 0–0.03；记录后修事件集/换新集，不放宽窗口。
- **Exit proof**: P2 报告 + Brier/对照/盲评记录 + 预注册 hash 校验；gate 全绿且未触 kill。
- **Stop condition**: 任一 kill；或事件总数不足 20 个；或可评分率 <50%；或窗口过期无法按 miss 计入。

## Dry-Run Findings

1. **P0 不设 A 占比门槛**：T-197 实测 A=3/12=25%，是「冲/合/穿/刑禁 A」后的真实结构；P0 只验管道/字段/≤2 题/≤5 分钟，A 占比仅报告。P1 才要求 A≥90%（按固定类 A 率 + A 精确率）。若误把 P0 的 25% 当失败，会错误 kill 一个结构正确的管道。
2. **B1 问题容易泄漏候选**：问题若出现「冲/合/穿/刑」「被克/被合」等词，答题者会反推候选。生成器必须把问题写成纯事实（时间、事件、对象、外部记录），并在 P0 做盲态演练。
3. **B2 上限可能被动态单候选卡挤爆**：动态只有一条 decisive 候选时不能 A，只能 B2/C；若大量卡无事实可问，B2 会超 30%。P1 策展要保证足够多「可用事实区分」的动态卡，否则 P1 结构不成立。
4. **C≤50% 依赖源供给**：穿制冲突、无施动句、藏干无地址都会推高 C；若 C>60%，不是调阈值，而是补源/换卡集/承认覆盖不足。
5. **fixed-20 的 3 条 fallback**：F20-009/013/014 说明固定类 A 不能假设 engine 总有候选；生成器需允许 `engine_fixed_rule` 兜底并标 `edge=not_applicable`（G3），但必须在 `provenance` 中如实写 `engine_fixed_rule`，不得伪装成 `engine_candidate`。
6. **事实审计的时刻差异**：`precise_start_*` 不作为卡端点；P2 若用流月，必须用 `engine.cli` 的岁运快照，不得自行推算交运时刻。
7. **routing 召回未评分**：P0/P1 不得引用 routing 的 116 个证据项作为召回能力；它只证明证据包可生成、可回查。
8. **旧 3 卡不可用**：任何示例、测试、演示都不得复用 `archive/demo/` 的 3 卡；本规格示例只用字段占位。

## Final Validation

- **T-196 验收**：
  - 三份文档存在且互相引用：`docs/goals/first-principle-agent-first-v1.md`、`docs/specs/analysis-card-v2.md`、`docs/specs/agent-candidate-generator-v1.md`；
  - 字段名一致：`tier` / `decision_by` / `selection_source` / `anchor_q` / `anchor_a` / `expert_decision` / `provenance` / `engine_validation` / `seeded_error` / `statement_claims`；
  - A 只固定类；动态永不 A；B1 只答事实；B2 有上限；C 有 `anchor_request`；
  - P0/P1/P2 gate 与 kill 写死；P0 只验管道与完整性；
  - 未改 `AGENTS.md` §4、`templates/report-v7-human.md`、`engine/**`、答案/测试；未做 git 写；未跑盲测。
- **未来执行验收**：P0 hard gate 全绿 → P1 gate 全绿且不触 kill → P2 gate 全绿且不触 kill；任何阶段 hard kill 即停。

## First Execution Step

中枢验收这三份规格后，先做 **P0 卡集策展（3–5 卡，建议 2 固定 A + 1 B1 + 1 C）** 与 **seeded-error fixture**；不要先跑统计、不要先扩 P1/P2、不要读答案/旧卡。P0 的第一条命令应是 `python -m engine.cli all --pillars "..." --gender ... --json` 与 `python -m tools.query_theory ... --json`，不是评分器。

## Cross-References

- 卡 v2（字段名以此为准）：[`docs/specs/analysis-card-v2.md`](../specs/analysis-card-v2.md)
- 候选生成器 v1：[`docs/specs/agent-candidate-generator-v1.md`](../specs/agent-candidate-generator-v1.md)
- 卡 v1（五元组基线）：[`docs/specs/single-chart-analysis-v1.md`](../specs/single-chart-analysis-v1.md)
- actor 规则表：[`docs/specs/actor-rules-v1.md`](../specs/actor-rules-v1.md)
- 事实证据包：[`docs/specs/fact-evidence-pack-v1.md`](../specs/fact-evidence-pack-v1.md)
- A+ 裁决：[`docs/reviews/t191-a-plus-verdict-v1.md`](../reviews/t191-a-plus-verdict-v1.md)
- 归档治理：[`archive/adjudication_v1/README.md`](../../archive/adjudication_v1/README.md)
- 事实审计：[`META/fact-audit-v1.md`](../../META/fact-audit-v1.md)
- fixed-20：[`META/p1-fixed-20.md`](../../META/p1-fixed-20.md)
- R-tool 运行：[`META/r-tool-run-v1.json`](../../META/r-tool-run-v1.json) / [`META/r-tool-run-routing-v1.json`](../../META/r-tool-run-routing-v1.json)
- 工具入口：[`docs/agent_tools.md`](../agent_tools.md)
