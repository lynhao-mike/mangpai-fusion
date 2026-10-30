# T-197d BRIEF · P0 卡修正（r2）

- 任务卡：`tasks/T-197d/PROMPT.md`
- 执行者：子代理（T-197d P0 卡修正 Agent）
- 范围：**只修 P0 卡/report 的可复现性与字段一致性**；不改 engine、不改候选的实质取舍（除 §2 明令的 dc3/rs1 同源去重）、不跑 P1、不做 git 写、不降门槛、不改 `tasks/T-197/PROMPT.md` 与保护区。
- 基线：`META/p0-cards-v1.json`（T-197 r1，20 项第三方差异见 `META/p0-thirdparty-v1.json`）

## 1. 改动文件

| 文件 | 改动性质 | 说明 |
|---|---|---|
| `META/p0-cards-v1.json` | 字段级修正（r1→r2） | P0-04 拆 3 条 A claim、卡级 `selected_option=null`、`anchor_a` 落 AQ1=yes；P0-03 `dc3`/`rs1` 单层化；P0-01/02 `anchored_by` 与 `discriminates` 修正；新增 `field_semantics`/`selection_rules`/`selection`/`dedup`；metrics 计数 12→11 |
| `META/p0-report-v1.md` | 重写 | 与卡同名字段对齐；§2 答案表成为可机检口径（verify 逐条比对）；§3 计数与 seeded 双口径；新增 §4「T-197c 20 项处理」、§5 未修/风险 |
| `tasks/T-197/verify.py` | 加 3 类断言（+字段不变量） | §5 的三条（非唯一却填 selected / anchor_a 与 report 不一致 / A-B1-C 计数不一致）+ `anchored_by`⊆`discriminates`、`elimination`⊆`discriminates`、`selection` 复算块一致性 |
| `META/p0-case-packets-v1.md` | 重新渲染（未改脚本） | 由 `tasks/T-197/render_packets.py` 从 r2 卡重新生成，避免人读包与卡矛盾 |
| `tasks/T-197d/patch_p0_cards.py` | 新增 | 幂等补丁脚本（stdlib-only），记录 r2 的每一条修正；`build → patch` 可复现 |
| `tasks/T-197d/BRIEF.md`、`STATUS.md` | 新增 | 本文件与状态 |

**未改动**：`engine/**`、`sources/**`、`tests/**`、`META/p0-thirdparty-v1.json`（T-197c 的产物，未回写）、`tasks/T-197/PROMPT.md`、`tasks/T-197/build_p0_cards.py`、`tasks/T-197c/**`。无 git 写。

## 2. 逐条修正内容

### 2.1 P0-04（唯一方向层 A 卡，T-197c 的 D10–D15 全部是 blocker）

| 字段 | r1 | r2 |
|---|---|---|
| `selected_option` | `"dc3"` | `null`（3 条 A claim 全存活，非唯一不得填） |
| 新增 `selected_claims` / `selected_options` / `claim_id` / `claim_selected` | — | `[dc1,dc2,dc3]`，逐 claim 记账（互补：库收 / 克坏功神 / 财源生官） |
| `anchor_a` | `[]` | `[{AQ1: "yes", answer_source:"source_outcome", source_ref:...L398, quote:逐字}]` |
| `anchor_a_note` | 「Agent 不代答、不据原文后续事实填写」 | 「有源才填、无源记 unknown」，与 `state_note` 同源不再互斥 |
| `state_selected` | `"败"`（不可复现） | `"败"`（**可复现**：AQ1=yes 消 st1，st3 为 C 档定义口径不参与选择 → st2 唯一） |
| `state_scope` | `not_claimed`（与 state_selected 矛盾） | `claimed` |
| `pending` | `null`，但 `tier_reason` 含 `pending:state_anchor` | `null`，tier_reason 已去掉该 token |
| `selection_source` | `agent_auto` | `engine_fixed_multi`（卡级无单一选择） |
| `not_auto_selected` | `true`（与已填选择矛盾） | `true`，并在 `field_semantics` 定义为「未自动折叠为单一 selected_option」 |
| `decision_by` | `engine_fixed`（名不副实） | `anchor_fact` + `decision_by_layer{direction:engine_fixed_multi,state:anchor_fact,rescue:needs_anchor}` |
| st1/st2 `anchored_by` | `["ED1"]`（悬空） | `["AQ1"]`（AQ1 是 state 题，`discriminates=[st1,st2]`） |
| `state_anchor_note` | `converted_from=expert_decision(ED1)` | `converted_from=null` / `resolved_by=AQ1`，说明 ED1 已废止 |
| st3 | 与 st1/st2 平权的 state 候选 | 保留（不删）+ `selectable=false` + `tier_note`（D19 推荐的第二种处理） |
| `non_claims` | 「不把富命/主凶择一写成结论（交 ED1）」 | 与原 ED1 解耦，并说明 st1 已被 AQ1 消去 |

### 2.2 P0-03（D07/D08/D09）

- **同源去重**：`dc3`（戌坏丑当疾病方向）与 `rs1`（戌坏丑→救应）同引 L141、同一条 e010 → 只保留**救应层** `rs1`，方向层移除 `dc3`；被移除项**完整原记录**保存在 `cards[P0-03].dedup[0].original_record`（没丢证据、不是静默删除）。
- `AQ1.discriminates=[dc1,dc2]` 现在覆盖全部方向候选；unknown → 两者全消 → 幸存集为空，`selected_option=null` **可由表复现**（D08 解决）。
- `AQ2`（心脏/血压）yes 由 `downgrade` 改为 **`eliminate=[st1]`**（D09），`if_yes`/`elimination` 同步。
- `rs1` 由 `B1/human_anchor` 改为 `C/needs_anchor`（本卡没有救应锚点题，B1 无从落地），`rescue_tier` 由 `not_claimed` 改 `C`；`anchored_by` 由错误的 `["AQ1"]` 改为 `[]`；`basis_text` 不再把 dc3 当活候选。
- `state_scope=not_claimed` → `candidate_only`（有候选、未收敛），`tier_reason` 同步。

### 2.3 P0-01 / P0-02（D01/D02/D03/D05/D20）

- `material_edge_reasons.e015`：「夫妻宫(M.b寅↔D.b申)相冲」→「月支寅(M.b)↔日支申(D.b)相冲；**M.b 是月支（父母兄弟宫），夫妻宫是 D.b**」。
- P0-01 `AQ2.discriminates` `[dc1,dc3]` → `[dc1,dc2,dc3]`（与 elimination 的消去项一致），并改写 `discriminator_basis`。
- P0-01/P0-02 `st1/st2.anchored_by` `["AQ1"]` → `[]` + `anchored_by_note`：这两卡**没有 state 层锚点题**，AQ1 是 direction 层，不得借写。
- P0-01 `outcome_note` 子女转述改为 L33 原文「一个孩子也没落着」。

### 2.4 包级（口径可机检）

- 新增 `field_semantics`（tier/scope/`not_auto_selected`/`anchor_a`/C 档语义）、`selection_rules`（可参与选择的档位、unknown 缺省、唯一规则、`selected` 必须等于唯一幸存者、state 必须等于其 `result`、多 claim 不折叠）。
- `metrics`：`direction_candidates 12→11`、`candidate_tiers {A:3,B1:7,B2:0,C:1}`、`candidate_tier_share` 重算、`a_claim_share{A:3/11=27.3%}`、`a_precision{3/3}`、`anchor_a_answers{unknown:5,yes:1}`、`state_candidates_selectable=9`、`direction_candidates_before_dedup=12`。
- `seeded_error` 计数**统一为两口径**：卡级 `card_scan` 4 卡×4 = **16/16**；包级 fixture `self_test` = **20/20**（`mode=self_test`，**非第三方植入**）。r1 report 写 16/16、卡写 20/20 的冲突按此消除（不是改数字）。

## 3. 原始输出（本机实跑）

### 3.1 verify（T-197 + T-197d）

```
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

### 3.2 反向验证（新断言确实会红；在 `%TEMP%` 的隔离副本上做，不动仓库）

| 注入的破坏 | verify 输出（节选） | 退出码 |
|---|---|---|
| P0-04 `selected_option="dc3"`（三 A 全存活时冒充唯一） | `P0-04 selected_option=dc3 非唯一：方向层幸存 ['dc1','dc2','dc3']（非唯一时不得填）` | 1 |
| report 第 6 题 yes→unknown | `report 答案表与卡 anchor_a 不一致：report 独有/不同={('P0-04','AQ1'):'unknown'}` | 1 |
| `metrics.candidate_tiers.B1` 7→8 | `metrics.candidate_tiers={'A':3,'B1':8,...} ≠ 逐卡清点 {'A':3,'B1':7,...}` | 1 |
| P0-01 `state_selected="败"`（state 层 2 个幸存） | `P0-01 state_selected=败 非唯一：状态层幸存 ['st1','st2']` | 1 |
| P0-03 `rs1.anchored_by=["AQ1"]` | `P0-03/rs1 anchored_by=AQ1，但 AQ1.discriminates 不含它` | 1 |
| P0-03 `AQ1` elimination 触及 dc3 | `P0-03/AQ1 elimination 触及未列入 discriminates 的 dc3` | 1 |

### 3.3 其它实跑

```
patch_p0_cards.py 连跑两次 sha256 相同: idempotent: True
独立清点: tiers {'B1':7,'C':1,'A':3} total 11; A share 0.2727;
          state candidates 10; rescue 4; anchor q 6; answers {unknown:5, yes:1}
diffstat(numstat + / -): cards +519/-246 · case-packets +45/-46 · report +71/-26 · verify +292/-18
sha256(前16): cards AC9C7BA455C5A4CB · report 19AB2596A7067EB2 · verify 72100F2713794B9F
```

## 4. 未完成与风险

1. **D04 未修（唯一未处理的第三方 finding）**：P0-02 的 `outcome_quote` 仍是 L25 的婚姻句。改它要动 `source_quote_validation` 与 `engine_validation.aggregate` 的引文计数，属内容层、不影响选择层；本轮不碰，交 T-197c/中枢定夺。
2. **A 率 3/11 = 27.3%（去重前 3/12 = 25.0%）仍未达 ≥50% 的 P0 报告线**：数据问题（4 例 material edge 多为冲/合/穿/刑），**没有为此删候选或放宽任何断言**；`a_share_vs_p0_gate.verdict` 仍为「未达」。
3. **`state_selected="败"` 保留而非置 null**：走的是「C 档不参与选择」的显式规则（D19 推荐的第二种处理），因此 st2 唯一、答案可复现。若中枢偏好最保守分支（state 置 null + `state_tier=C`），把 `selection_rules` 的 C 档规则改成「C 档参与并阻止唯一」即可，其余字段已按该语义双向兼容。
4. **`tasks/T-197/build_p0_cards.py` 未同步**：r2 由 `tasks/T-197d/patch_p0_cards.py` 施加。**重跑 T-197 builder 会覆盖 r2**，必须 build → patch。
5. **历史文档仍写 r1 数字**：`tasks/T-197/STATUS.md`、`tasks/T-197/BRIEF.md`、`docs/goals/first-principle-agent-first-v1.md`、`tasks/T-196/*` 里的「A 3/12=25%」是 r1 记录，未回写（r2 = 3/11=27.3%，两口径都 <50%，结论不变）。
6. **`META/p0-thirdparty-v1.json` 未回写**：它是 T-197c 的产物，其 `evidence` 行号在 r2 落盘后已整体偏移，需 T-197c 重跑重取。

## 5. 下游须知（T-197c / 中枢）

1. **`anchor_a` 非空是 r2 的预期状态**，不要再按 r1 的「anchor_a 必须为空」判 fail。口径看卡内 `field_semantics.anchor_a`：`source_outcome` 才可填 yes/no（必须带逐字 quote），`not_in_source` 一律 unknown。
2. **复算口径**：某层幸存集 = 该层 `anchor_q`（缺省 answer=unknown）`elimination` 消去后、**档位 ∈ {A,B1,B2}** 的候选；恰好 1 个才允许填 selected，`state_selected` 必须等于该候选 `result`。卡内 `selection.*` 是同一算法的声明结果，verify 会逐项对比。
3. **A 计数按 claim**（方向候选条数）不是按卡：r2 = 3/11；不要再报「3/4=75%」或仅报「3/12」。
4. **P0-03 方向候选只剩 2 条**（dc1/dc2），`dc3` 在 `dedup[0].original_record` 里；不要把它当方向候选重算。
5. **P0-04 方向层没有锚点题**（3 条 A claim 互补、全存活）；`state` 层唯一锚点是 AQ1，已由原文 L398 落 yes。
6. 若需改卡：改 `tasks/T-197d/patch_p0_cards.py` 再跑，不要手改 JSON（否则 report/verify 的机检会红，且与 builder 的关系更难追溯）。
