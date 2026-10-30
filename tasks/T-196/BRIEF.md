# T-196 BRIEF

- 任务：`tasks/T-196/PROMPT.md`
- 执行者：子代理 AX
- 日期：2026-10-30
- 范围：只写规格；不写代码、不跑盲测、不做方向裁决、不改保护区、不做 git 写。

## 1. 改动文件

新增：

- `docs/goals/first-principle-agent-first-v1.md`
- `docs/specs/analysis-card-v2.md`
- `docs/specs/agent-candidate-generator-v1.md`
- `tasks/T-196/BRIEF.md`

更新：

- `tasks/T-196/STATUS.md`

未改：

- `AGENTS.md`（含 §4）、`CLAUDE.md`、`templates/report-v7-human.md`、`docs/analysis_human_touch.md`
- `engine/**`、规则、答案、`tests/**`、`pyproject.toml`、`requirements*.txt`
- `theory/_ir/**`、`sources/**`、`META/project-state.json`、`tasks/*/PROMPT.md`
- 未做 `git add/commit/push`，未跑盲测/评分器。

工作区并行物（**不是 T-196 产生，未触碰**）：`META/p0-cards-v1.json`、`META/p0-case-packets-v1.md`、`tasks/T-197/_engine/`、`tasks/T-197/_exclusion.json`、`tasks/T-197/build_p0_cards.py`、`tasks/T-197/render_packets.py`、`tasks/T-197/verify.py`；以及 T-196 之前已修改的 `META/p1-holdout-baseline-v1.json` / `.md`。中枢验收时不要把这些算进 T-196 diff。

## 2. 原始输出

### 2.1 `git status --short`（写完后）

```text
 M META/p1-holdout-baseline-v1.json
 M META/p1-holdout-baseline-v1.md
?? META/p0-cards-v1.json
?? META/p0-case-packets-v1.md
?? _tmp_t190b/
?? docs/goals/first-principle-agent-first-v1.md
?? docs/specs/agent-candidate-generator-v1.md
?? docs/specs/analysis-card-v2.md
?? mangpai-fusion-offline-04677d2c.zip
?? tasks/T-197/_engine/
?? tasks/T-197/_exclusion.json
?? tasks/T-197/build_p0_cards.py
?? tasks/T-197/render_packets.py
?? tasks/T-197/verify.py
```

说明：`docs/...` 三份是本任务新增；`META/p0-*` 与 `tasks/T-197/*` 是并行产物；`META/p1-holdout-baseline-v1.*` 在 T-196 开始前已显示 M，且 `git diff` 对它们无文本差异（可能只是行尾/stat），非 T-196 所为。`tasks/T-196/BRIEF.md` 新增、`STATUS.md` 由已跟踪文件变为 M。并行产物在写完本文件后仍有增加（例如 `tasks/T-197/STATUS.md`、`tasks/T-197/BRIEF.md`），T-196 未触碰；验收以 `git diff -- docs/goals docs/specs tasks/T-196` 为准。

### 2.2 文件哈希（SHA-256，写完时）

```text
docs/goals/first-principle-agent-first-v1.md
D099A1247B18DCCE55747BEF874A2AC2F513D40A6EF47B34B326A43AD28D81E7

docs/specs/analysis-card-v2.md
C8B1AC71D3A8FD89A3ED040BBFE49542A24FCA004ABA5A501D221508F51C197A

docs/specs/agent-candidate-generator-v1.md
4EE575E176C7CF24E6904DE8C0FCA3E8E0E192D750CCF31476C1C1B465CDC87B
```

### 2.3 自检命令与结果

用 `.venv\Scripts\python.exe` 跑了只读检查（不写仓库文件，输出到 `%TEMP%`）：

- JSON 代码块解析：`analysis-card-v2.md` 13 块、`agent-candidate-generator-v1.md` 8 块，全部 `json.loads` 通过；`first-principle-agent-first-v1.md` 无 JSON 块。
- Markdown 表格：三份文档所有表格列数一致，无报错。
- 相对链接：三份文档所有 `](...)` 相对链接均存在（`all links exist`）。
- 字段计数：`tier` / `decision_by` / `anchor_q` / `anchor_a` / `expert_decision` / `provenance` / `engine_validation` / `seeded_error` / `statement_claims` 在三份文档中均出现（数量不等，按职责分布）。
- 未跑 `pytest`：本任务无代码改动；按卡不跑测试/盲测。若要跑，按 `AGENTS.md` §5 的命令，不应因 T-196 新增文档而改变结果。

### 2.4 读取的证据文件

`tasks/T-196/PROMPT.md`、`docs/reviews/t191-a-plus-verdict-v1.md`、`docs/specs/fact-evidence-pack-v1.md`、`META/fact-audit-v1.md`、`META/p1-fixed-20.md`、`META/r-tool-run-v1.json`、`META/r-tool-run-routing-v1.json`、`archive/adjudication_v1/README.md`；并参考 `docs/specs/single-chart-analysis-v1.md`、`docs/specs/actor-rules-v1.md`、`docs/agent_tools.md`、`docs/specs/adjudication-a-plus-v1.md`。

## 3. 未完成与风险

1. **只有规格，没有实现/执行**：P0/P1/P2 均未跑；`seeded_error` 校验器、卡生成器、评分器都还没有代码；本文件不能当作能力证明。
2. **P0 已删除 A≥50% 门槛**：按中枢 2026-10-30 T-197 反馈，P0 只验管道/完整性/字段/≤2 题/≤5 分钟；A 自动占比只报告。T-197 实测 A=3/12=25% 是「冲/合/穿/刑禁 A」后的真实结构，不是失败；P0 不据此 kill。A≥90% 是 P1 门槛（且按 `a_rate_fixed` + `a_precision` 双指标）。P0 hard kill 仍保留编造/泄漏/seed<100%/类外自动/无源/角色隔离。
3. **A≥90% 的口径**：本规格把它拆成 `a_rate_fixed`（A 卡/固定类卡）与 `a_precision`（A 卡经复核仍成立/A 卡）双指标；若中枢只想要其中一个，需在 P1 前确认。
4. **候选数量 2–3 的例外**：卡要求 2–3，但 A 固定类/单候选 B2 允许 1 条，C/`not_claimed` 允许 0 条；理由是不为凑数编造候选。若必须硬性 2–3，会与「不得发明边/地址/十神」冲突，需中枢裁决。
5. **B2 单候选确认**：动态只有 1 条 decisive 候选时不能 A，也不能 B1（B1 要 2–3 条消歧），本规格落到 B2 专家确认或 C；这会把 B2 占比推高，P1 的 B2≤30% 可能吃紧。
6. **state 冲突默认 C**：B2 不用于 state 消歧；只有方向层 B1 且同一 `anchor_q` 能区分 S 候选时，state 才可随之选。若产品要求 state 也走 B2，需要扩展 `expert_decision`。
7. **`direction_known` 语义**：本规格限定 `direction_known=true` 仅 A 固定；B1/B2 选中的动态候选不投影到 `t2.actor/target`，只在 `direction_candidates[selected_option].claim` 里。若下游希望直接用 `t2.actor/target` 读动态选择，需要另加 `selected_actor/selected_target` 字段。
8. **fixed-20 的 3 条 fallback**：F20-009/013/014 依赖 `engine_element_rule`/`engine_pair_fallback`；固定 A 允许 `engine_fixed_rule` 兜底，但必须在 `provenance` 如实写，不能伪装成 `engine_candidate`。fixed-20 仍待 B 复核。
9. **routing 召回未评分**：`META/r-tool-run-routing-v1.json` 只证明 15 题、116 个证据项、0 类外、`blind_valid=true`，不证明召回；P0/P1 不得引用它当能力。
10. **事实审计严格口径未过**：`precise_start_*` 50 项差异是时刻类，严格 0 差异未达成；卡不使用该字段，P2 若用流月必须走 `engine.cli` 岁运快照。
11. **HEAD 不一致**：`tasks/T-196/PROMPT.md` 写前置 `af22f270`，工作区 HEAD 是 `1a773249`（`docs: Agent-first P0 启动...`）；本任务未做 git 写，验收以工作区 diff 为准。
12. **无第三方复核**：三份规格只有本 Agent 自查（JSON/表格/链接/字段），没有第二人逐条复核；中枢需亲自看。
13. **并行 T-197 产物**：工作区出现 `META/p0-*` 与 `tasks/T-197/*`，不是 T-196 产生；若中枢要提交 T-196，只应暂存 `docs/goals/...`、`docs/specs/...`、`tasks/T-196/BRIEF.md`、`tasks/T-196/STATUS.md`。

## 4. 下游须知

1. **字段名唯一来源**：卡 v2（`docs/specs/analysis-card-v2.md`）。生成器输出与卡装配必须使用同一套：`tier` / `decision_by` / `selection_source` / `direction_candidates` / `selected_option` / `state_candidates` / `selected_state` / `rescue_candidates` / `selected_rescue` / `anchor_q` / `anchor_a` / `expert_decision` / `provenance` / `engine_validation` / `seeded_error` / `statement_claims` / `card_status`。
2. **A 只固定**：`ke/sheng/hua/muku` 且单条 decisive、无冲突、校验 pass；冲/合/穿/刑/破永远 B1/B2/C。
3. **B1 人只答事实**：`anchor_q` 1–2 条，答题者不看候选/方向；`anchor_q` + `elimination` 答题前冻结；答 unknown/不收敛 → C；锚点事实不进评分。
4. **B2 专家**：无可观测事实可辨；1–3 条候选（单条=确认）；`expert_decision` 带 `source_ref`+逐字 quote；专家 ≠ 生成者 ≠ 评分者 ≠ 锚点答题者；P1 ≤30%。
5. **C 不是结论**：`selected_option=null`、`anchor_request` 四字段齐；穿制冲突、无源、校验失败、state 冲突、救应缺原语都进 C；不得用猜测补。
6. **伪造即 void**：假地址/假边/假十神/假引文/跨快照/藏干当地址 → `card_status=void`，不进统计；`seeded_error` 卡扫描 + self_test 100%。
7. **P0 先做**：3–5 卡，建议 4 张（2 固定 A + 1 B1 + 1 C），先实现 seeded fixture 与字段完整性检查；不要先跑 P1/P2、不要先扩岁运。
8. **P1 再跑**：10–20 卡，≥5 固定、≥5 动态；标签独立预注册；`agent_top1` 先冻结；gate/kill 按目标文档，不调阈值、不重跑同卷。
9. **P2 最后**：10–15 盘 / 20–40 外部可查事件，流月 1–3 月，2–3 互斥分支 + 皆非，先验/预注册 hash/盲评/交换盘/去引擎/历史基率；窗口过期按 miss，不放宽。
10. **保护区不动**：`AGENTS.md` §4、`report-v7-human.md`、`engine/**`、答案/测试、`pyproject.toml`/`requirements*.txt` 仍只读；要改另开卡。
11. **不复活**：不写自动方向、不写 `party-direction-v2`、不用旧 3 卡、不恢复 A+ 阈值。

## 5. 中枢修正对照（单列）

### 5.1 第一轮修正（A 只固定；B 锚点消歧；字段/校验/P0/P1/P2/角色）

| # | 中枢修正 | 落点 |
|---|---|---|
| 1 | A 只许固定克/生/化/墓，`provenance=engine_fixed`；冲/合/穿/刑一律不得 A | 目标文档 Tier Model A 行；卡 v2 §5.1、§5.3 note；生成器 §2.3、§3.6、§9 |
| 2 | B 改锚点消歧：Agent 出 1–2 个「命主已发生事实」是非题；人不选候选，只答事实；答不出→needs_anchor | 卡 v2 §5.2、§6.1–6.2；生成器 §4；目标文档 Tier Model B1 |
| 3 | 卡字段补 `tier` / `decision_by` / `anchor_q[]` / `anchor_a[]` / `provenance` / `engine_validation`（address/edge/ten_god/quote/seeded_error） | 卡 v2 §2、§7；生成器 §7；目标文档 Metrics/Tier |
| 4 | 校验器 100% 抓 seeded 假地址/假边/假引文；P0 只验管道与完整性（编造/泄漏 hard kill），不做统计 kill | 卡 v2 §7.3、§9 V13；目标文档 P0 Hard Gate / Report 分离 |
| 5 | P1 指标：召回≥80%、A≥90%、B 锚点后比 Agent top-1 高≥15pp、C≤50%、类外自动 0、引文 100%；kill：召回<50%、A<80%、B 提升≤3pp、C>60%、任何类外自动/引文漏 | 目标文档 P1 Gate/Kill；Metrics 定义 |
| 6 | P2：10–15 盘/20–40 外部可查事件、流月 1–3 月、2–3 互斥分支+皆非、先验、可评分≥70%、Brier、交换盘/去引擎/历史基率、预注册 hash、盲评、窗口过期不放宽 | 目标文档 P2 Phase/Gate/Kill |
| 7 | 候选生成者不得兼任锚点答题者/评分者；锚点事实不得用于评分 | 目标文档角色表/`anchor_fact_leakage`；卡 v2 V21/V22；生成器 §4.5、§10 |
| 8 | 不自动承诺冲/合/穿/刑；不碰保护区；不复活党势/A+ | 三份文档的禁止/Non-goals 段 |

### 5.2 第二轮修正（B1/B2；字段；P1/P2；角色）

| # | 中枢修正 | 落点 |
|---|---|---|
| 1 | B 拆 B1（锚点消歧）/ B2（专家裁决）；B2 必须带 source/quote，P1 ≤30% | 卡 v2 §5.2、§5.3、§6；生成器 §3.6、§4、§5；目标文档 Tier Model、P1 Gate/Kill |
| 2 | A 仍只许固定类；冲/合/穿/刑一律 B/C，不得 A | 卡 v2 §5.1、§5.3 note；生成器 §3.1、§3.6；目标文档 Tier Model |
| 3 | 卡字段加 `tier`（A/B1/B2/C）、`decision_by`、`anchor_q/a`、`expert_decision`、`provenance` | 卡 v2 §2、§5、§6；生成器 §7 |
| 4 | P1 门槛：召回≥80%、A≥90%、B1 lift≥15pp、B2≤30%、C≤50%、类外自动 0、引文 100%；kill：召回<50%、A<80%、B1 lift≤3pp、C>60%、B2>30%、任何类外自动/引文漏 | 目标文档 P1 Gate/Kill；Metrics |
| 5 | P2 同第一轮 6 | 目标文档 P2 |
| 6 | 候选生成者 ≠ 锚点答题者 ≠ 评分者；锚点事实不得用于评分 | 目标文档角色表；卡 v2 V21/V22；生成器 §4.5、§10 |
| 7 | 不自动承诺冲/合/穿/刑；不碰保护区；不复活党势/A+ | 三份文档的禁止/Non-goals 段 |

### 5.3 第三轮修正（T-197 反馈）

| # | 中枢修正 | 落点 |
|---|---|---|
| 1 | P0 删除「A≥50%」；P0 只验管道/完整性/字段/≤2 题/≤5 分钟；A 自动占比只报告，不作 P0 门槛；A≥90% 是 P1 门槛 | 目标文档 P0 Purpose/Phase rules/Hard Gate/Report/Metrics；Dry-Run #1 |
| 2 | T-197 的 A 仅 3/12=25% 是「冲/合/穿/刑禁 A」后的真实结构，不是失败；P0 不因此 kill | 目标文档 P0 说明、Current State、Dry-Run #1；本 BRIEF §3.2 |
| 3 | A 可由引擎确定性落定（`engine_fixed` / `agent_auto` / `pending=none`）；T-197「不代选」只约束 B/C，不约束 A | 卡 v2 §5.1 条件 9 + A 自动性段；生成器 §2.3、§3.9；目标文档 Tier Model A 行 |
| 4 | 6 个 B1 事实题已交人类；答不出→needs_anchor；B2=0 | 卡 v2 §5.2/§6.2；生成器 §4.4；P0 gate ≤2 题/≤5 分钟 |
| 5 | P0-01/P0-03 的 `same_page` 依据只作 B1 候选，不升 A；可保留 | 卡 v2 §5.1 条件 3；生成器 §2.3 A 条件与「不得 A」清单 |
| 6 | 其余按卡 | — |

## 6. 口径决策（需中枢确认的 5 项）

1. **`A≥90%`**：本规格按 `a_rate_fixed`（A 卡/固定类卡）与 `a_precision`（A 卡经复核成立/A 卡）双指标执行；若只要其一，P1 前确认。
2. **P0 口径**：P0 只验管道/完整性/字段/≤2 题/≤5 分钟；A 占比仅报告（T-197 3/12=25% 不判失败）；A≥90% 是 P1 门槛，不是 P0。
3. **候选 2–3 的例外**：A 固定类/单候选 B2 允许 1；C/`not_claimed` 允许 0；不编造候选。
4. **B2 单候选确认**：动态单候选不能 A、不能 B1，落 B2 专家确认或 C；可能推高 B2 占比。
5. **`direction_known`**：仅 A 固定为 true；B1/B2 选中动态不投影到 `t2.actor/target`，只存候选 `claim`。若下游要直接读，需另加 `selected_actor/selected_target`。
