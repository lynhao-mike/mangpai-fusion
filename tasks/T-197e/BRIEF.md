# T-197e BRIEF · P0 r3 内容修复

- 任务卡：`tasks/T-197e/PROMPT.md`
- 执行者：子代理（T-197e P0 卡内容修复 Agent）
- 基线：`META/p0-cards-v1.json` r2（T-197d；工作树 `e0038714`）
- 范围：**只修 P0 卡的 root 副本与内容层**；不改候选取舍/答案、不改 engine/保护区、不跑 P1、不做 git 写、不降门槛。
- 产物：`META/p0-cards-v1.json`、`META/p0-report-v1.md`、`META/p0-case-packets-v1.md`、本文件、`STATUS.md`、幂等补丁脚本 `tasks/T-197e/patch_p0_cards_r3.py`。

## 1. 改动文件

| 文件 | 改动性质 | 说明 |
|---|---|---|
| `META/p0-cards-v1.json` | 字段/内容级修正 r2→r3 | root `anchor_questions` 同步；P0-02 事业结局引文；P0-03 他造归属；P0-04 H.b/state/metrics；新增 `missing_evidence` |
| `META/p0-report-v1.md` | r3 更新 | 标题/范围、§2 窗口、§4 D02/D04/D09、§4.1 12 项差异、§5 风险、§6 结论 |
| `META/p0-case-packets-v1.md` | 重新渲染 | 由 `tasks/T-197/render_packets.py` 从 r3 卡生成；修掉旧头部 12 条/`anchor_a=[]` 等过时表述 |
| `tasks/T-197e/patch_p0_cards_r3.py` | 新增 | stdlib-only 幂等补丁；记录 r3 每一条修正；`build → T-197d patch → T-197e patch` 可复现 |
| `tasks/T-197/render_packets.py` | 小修（渲染层） | 头部统计/修订号/anchor_a/缺证据/co_claims/state_scope_note/引文归属从 JSON 派生，不再硬编码 r1 数字 |
| `tasks/T-197e/BRIEF.md`、`STATUS.md` | 新增/更新 | 本文件与状态 |

**未改动**：`engine/**`、`sources/**`、`tests/**`、`tasks/T-197/PROMPT.md`、`tasks/T-197c/**`、`META/p0-thirdparty-v2.json`。无 git 写。

## 2. 四个优先项（改前 / 改后 / 证据）

### 2.1 D-R2-02 · P0-03 root AQ2 改 eliminate st1

- **改前**：root `anchor_questions[P0-03/AQ2].if_yes = {keep:[st2], eliminate:[], downgrade:[st1]}`；`elimination[yes] = {eliminates:[], keeps:[st2]}`。
- **改后**：root `if_yes = {keep:[st2], eliminate:[st1], downgrade:[]}`；`elimination[yes] = {eliminates:[st1], keeps:[st2]}`；与卡内 `cards[P0-03].anchor_q[AQ2]` 完全一致。
- **证据**：卡内 r2 已是 `eliminate=[st1]`（report §4 D09）；r3 把 root 镜像同步。独立比对 `root_sync_mismatches=[]`；`verify.py` 退出 0；`state_selected` 仍为 null（AQ2 unknown），selected 不变。

### 2.2 D-R2-01 · P0-01 root AQ2.discriminates 补齐 dc2

- **改前**：root `discriminates = [dc1, dc3]`，与 `elimination` 中 unknown 消去 `[dc1,dc2,dc3]` 不一致。
- **改后**：root `discriminates = [dc1, dc2, dc3]`；`discriminator_basis` 同步为卡内的 dc1/dc2/dc3 三读法说明。
- **证据**：卡内 r2 已含 dc2；r3 同步 root。独立比对 `root_sync_mismatches=[]`；`verify.py` 0；AQ2 unknown 的幸存集仍为空，selected 不变。

### 2.3 D04 · P0-02 outcome_quote 改事业结局引文

- **改前**：`source.outcome_quote.text = "此人婚姻非常好，一生2个孩子，一儿一女。"`（L25 婚姻/子女句，与 career 域错配）。
- **改后**：`source.outcome_quote.text = "07年转戊辰运08年提副军长，预测2012年还会提升正军级干部。"`（同一 L25 的事业结局句）；新增 `outcome_quote.domain="career"` 与 `outcome_quote_domain_note`，说明 L25 前半为军官履历/晋升结局、后半才是婚姻子女；`outcome_note` 同步为晋升履历。
- **证据**：`sources/duan/MinerU_markdown_如何看军官_2056043755153842176.md:L25` 逐字子串命中；独立 quote 校验 `quote_verbatim_failures=[]`；M-01 标 `已补`。`source_quote_validation` 仍引 L25，引文计数不变。

### 2.4 P0-04 · dc1 补时支丑 H.b（两丑入辰墓）

- **改前**：dc1 `claim.members=[D.b,M.b]`、`addrs=[D.b,M.b]`；`palaces` 只有 M.b/D.b/Y.b；`material_edges=[e008,e004,e010]`；未记录 engine 第二条墓用 `[D.b,H.b]` 与 e011。
- **改后**：
  - dc1 `claim.members=[D.b,M.b,H.b]`，`addrs`/`ten_god_claims` 补 H.b（正官）；`claim.targets=[M.b,H.b]`、`atomic_members=[[D.b,M.b],[D.b,H.b]]`。
  - `palaces` 补 H.b「时支丑：官星（正官）—月时丑同入辰墓」，引 L392。
  - `material_edges` 补 `e011`（po(D.b,H.b) 辰丑破），`material_edge_reasons.e011` 写明时丑与辰库相破。
  - dc1 `co_claims` 记录 engine `duan_zuogong.candidates` 的 `墓用[D.b,H.b]`（actor=D.b）；`basis_text` 明写「L392『月时丑官都入辰墓』含月丑 M.b 与时丑 H.b 两丑」；`schema_compat.extensions` 加注「两条墓用合并为一个互补 claim，engine 原候选保留在 co_claims/atomic_members」。
- **证据**：`sources/duan/MinerU_markdown_段建业2011杭州财官班教材_2056046552687501312.md:L392` 逐字；engine `facts.duan_candidates` 同时给 `墓用[D.b,M.b]` 与 `墓用[D.b,H.b]`；`facts.edges` 有 `e011 po(D.b,H.b)`；M-03 标 `已补`。`verify.py` 0；P0-04 方向层仍 3 条 A claim 全存活，selected 不变。

## 3. 附带项与 6 项缺证据

| 项 | 改前 | 改后 / 证据 |
|---|---|---|
| D-R2-05 | P0-04 st2 `decision_by=expert_single_choice`，与 `state_decision=anchor_fact`、`anchored_by=[AQ1]`、`expert_decision=null` 矛盾 | 改 `decision_by=anchor_fact` + `decision_by_note`；全包 `expert_single_choice` 计数 0；st2 仍 `anchored_by=[AQ1]`（AQ1 确 discrimination st1/st2） |
| D-R2-06 | `metrics.state_candidates_selectable=9` | 改 8：10 个 state 候选 − 2 个 C 档（P0-01 st3、P0-04 st3）；加 `state_candidates_selectable_note` |
| D-R2-07 | P0-03 st2 `basis_text` 把 L131 他造判词写成「本造」 | `basis_text`/AQ2 `discriminator_basis` 改为「另一造（乾 乙戊丙己/卯寅午丑，L127-L133）判词，可迁移不可当本造」；L131 引文加 `attribution_note`；M-04 标「缺」 |
| D-R2-10 | P0-04 AQ1 `fact_window=2010-01..2025-12`，答案事件 2003 在窗口外 | 卡与 root 均改 `2000-01..2025-12`，`fact_window_note` 写明覆盖 2003 癸未；M-05 标「部分」（仍非命主自述） |
| D-R2-09 | P0-04 st3 `tier=C` 是扩展借用（有源定义口径） | 保留 `tier=C`/`selectable=false`；新增 `candidate_kind=definition/non_outcome` + `label_note`；`tier_note` 说明严格 schema 读法 |
| D-R2-11 | P0-03 st1/st2 result 都是「病」，只分病位 | 卡级 `state_scope_note` + st1/st2 `result_note`：只分病位，不分病/不病 |
| D-R2-12 | P0-04 st1/st2 是「富→破」时间序列 | 卡级 `state_scope_note` + st1/st2 `time_scope/result_note`：不是同一时点互斥；按卡声明「最终成败」仍取 st2 |
| D-R2-04 / M-02 | dc2 说「原文只说财制印未点名哪一个财」，与 dc1 引文冲突 | 删去错误表述，改为「原文点名戊、己缺原文/事实依据（M-02）」；dc2 保持 `decisive=false`，不删候选、不升格 |

**6 项缺证据**（`META/p0-cards-v1.json.missing_evidence`）：

| ID | 卡 | 项 | 状态 | 处理/证据 |
|---|---|---|---|---|
| M-01 | P0-02 | 事业结局引文 | 已补 | L25 事业结局句；见 §2.3 |
| M-02 | P0-02 | dc2 己制癸原文/事实依据 | 缺 | 原文只点名戊；dc2 仅机械备选，不升格 |
| M-03 | P0-04 | 时支丑入墓/破库证据 | 已补 | L392 + 墓用[D.b,H.b] + e011；见 §2.4 |
| M-04 | P0-03 | 本造专属心脏/血压判据 | 缺 | L123 通例、L131 他造判词；本造只写子宫癌 |
| M-05 | P0-04 | 窗口内命主事实 | 部分 | 窗口已覆盖 2003；仍为 `source_outcome`，非命主自述 |
| M-06 | all | 逐卡独立 seeded 注入项 | 缺 | 4 卡复用同一 fixture；16/16 仍是 smoke check |

## 4. root 副本同步

`pack["anchor_questions"]` 已从 4 卡 `anchor_q` + `anchor_a` 逐题镜像：`layer/text/answer_type/discriminator_basis/rule_ref/source_mentions_answer/proxy_strength/if_yes/if_no/if_unknown/qid/discriminates/elimination/fact_window/fact_domain/fact_window_note/anchor_a`，以及 `answer/answer_source/answer_source_ref/answer_quote`。

独立比对输出：`root_sync_mismatches= []`（6 题全部一致）。

## 5. 原始输出

### 5.1 `tasks/T-197/verify.py`（最终）

```text
[ok]  schema=p0-cards/v1 task=T-197
[ok]  例数 4 ∈ [3,5]
[ok]  覆盖 婚/事业/健康/财
[ok]  逐卡结构/档位/引文校验完成（锚点题 6）
[ok]  anchor_a 完整且 source-backed（非 unknown 必带逐字原文）
[ok]  4 盘与 133 个排除集四柱零重叠
[ok]  anchor_a 与 report §2 一致：6 题（unknown 5 / yes 1）
[ok]  计数一致：A=3 B1=7 B2=0 C=1（方向 claim 合计 11）
      P0-01: dir_survivors=∅ state_survivors=['st1', 'st2'] selected_option=None state_selected=None
      P0-02: dir_survivors=∅ state_survivors=['st1', 'st2'] selected_option=None state_selected=None
      P0-03: dir_survivors=∅ state_survivors=∅ selected_option=None state_selected=None
      P0-04: dir_survivors=['dc1', 'dc2', 'dc3'] state_survivors=['st2'] selected_option=None state_selected='败'

PASS: p0 卡片包满足 T-197 + T-197d 验收项（selected 可复现 / A 仅固定类且按 claim 计数 / anchor_a 与 report 一致 / 引文逐字 / 零排除集重叠）
[exit code: 0]
```

### 5.2 独立检查（不改仓库）

```text
root_sync_mismatches= []
quote_verbatim_failures= []
source/palace quote failures: []
P0-04 H.b in claim.members= True
P0-04 H.b in palaces= True
P0-04 e011 in material_edges= True
P0-04 co_claims= [墓用 [D.b,H.b] actor=D.b]
P0-04 st2 decision_by= anchor_fact
expert_single_choice count= 0
metrics state selectable= 8
P0-04 window= 2000-01..2025-12
P0-04 st3= {tier:C, selectable:false, candidate_kind:definition/non_outcome}
P0-03 state_scope_note? True
P0-04 state_scope_note? True
missing ids= [M-01..M-06]; summary={total:6, resolved:2, partial:1, missing:3}
```

### 5.3 补丁幂等

```text
patch_p0_cards_r3.py 连跑两次: idempotent=True
cards_sha256=D5BD8C49E8615AED518ABEC8DFF7E75996C980DD528283D193911ECB197EE050
report_sha256(前16)=0CDDAE9342250914
packets_sha256(前16)=F7C960A2B0951ABF
```

## 6. 未完成与风险

1. **M-02 / M-04 / M-06 仍缺证据**：M-02（己制癸无原文/命主事实）、M-04（本造专属心脏/血压判据缺）、M-06（4 卡 seeded 复用同一 fixture，非逐卡独立注入）。已逐条写入 `missing_evidence`；**没有为此删候选、改答案或放宽断言**。
2. **M-05 只做到「部分」**：P0-04 AQ1 窗口已覆盖 2003，但答案仍是原文 `source_outcome`，不是命主自述；P1 需补 `testimony`。
3. **A 率 3/11 = 27.3% 仍未达 ≥50% gate**：数据问题（4 例 material edge 多为冲/合/穿/刑），不是管道问题；未调 gate、未删候选。
4. **5 题仍 unknown**：需命主/人类回答；`anchor_a` 已留位，回答时按 `field_semantics.anchor_a` 填。
5. **repro 链条未合并**：`tasks/T-197/build_p0_cards.py` 未同步 r2/r3；重跑 builder 会覆盖，必须按 `build → T-197d patch → T-197e patch` 顺序复现。
6. **P0-04 st3 仍是 `tier=C` 扩展借用**：已加 `candidate_kind=definition/non_outcome` + `label_note`；严格 schema 下游不要读成「无源 C」，也不要据此改 `selectable=false`。
7. **`META/p0-thirdparty-v2.json` 未回写**：它是 T-197c r2 的产物；r3 的复核应由 T-197c r3 重新生成（本轮不改第三方文件）。
8. **`tasks/T-197/verify.py` 未改**：r3 没有放宽任何断言；仍以原 `verify.py` 退出 0 为验收。

## 7. 下游须知（T-197c r3 / 中枢）

1. **T-197c r3 只核 4 项优先 + selected**：D-R2-01、D-R2-02、D04、P0-04 H.b；selected 4/4 不变（P0-01/02/03 null；P0-04 `selected_option=null` + `state_selected=败`）。
2. **root `anchor_questions` 现已与卡内一致**：不要再按 r2 的 root 旧值判 D-R2-01/02 未修；6 题 root/card 独立比对为零差异。
3. **P0-02 的 `outcome_quote` 是事业结局句**：L25 同段后半的婚姻句已移出 career outcome；不要把它再当 D04 未修。
4. **P0-04 方向层仍是 3 条互补 A claim**：不要因为 dc1 补了 H.b 就把它折成单一 selected_option；A 计数仍是 3/11。
5. **P0-04 state 层是「最终成败」口径**：st1 先富、st2 后破是时间序列；若按「一生轨迹」口径，state_selected 应为 null 或多 claim（本卡不采用）。
6. **P0-03 的 L131 是他造判词**：乾 乙戊丙己 / 卯寅午丑（L127-L133），本造只是同构寅午半合；不要把它读成本造「不得心脏病」的判词。
7. **不要直接手改 JSON**：改 `tasks/T-197e/patch_p0_cards_r3.py` 再跑；`render_packets.py` 重新生成人读包。`verify.py` 退出 0 才算落盘。
8. **不跑 P1、不做 git 写**：本轮边界保持；P1 需真实案例与命主事实，P2 只做预注册。
