# T-197d STATUS

- 状态：🟡 待中枢复验 + T-197c 重推（r2 已落盘，`verify.py` 退出 0）
- 执行者：子代理（T-197d P0 卡修正 Agent）
- 任务卡：`tasks/T-197d/PROMPT.md`
- 验收：中枢跑 `tasks/T-197/verify.py`（退出码 0）+ 抽查引文；T-197c 按 r2 重推 ≥90%
- 边界：不改 engine / 不跑 P1 / 不做 git 写 / 不降门槛 / 不改 `tasks/T-197/PROMPT.md` 与保护区

## 产物

| 文件 | 说明 |
|---|---|
| `META/p0-cards-v1.json` | r2：4 卡 / **11 方向 claim（A 3 · B1 7 · B2 0 · C 1）** / 10 状态（9 可参与成败选择）+ 4 救应 / 6 锚点题（`anchor_a` 已落盘：unknown 5 · yes 1）；新增 `field_semantics`/`selection_rules`/`selection`/`dedup` |
| `META/p0-report-v1.md` | 重写：分「方向档 / 状态档 / selected」三列；§2 答案表可机检；§3 计数与 seeded 双口径；新增 §4 对 T-197c 20 项的逐项处理、§5 未修/风险 |
| `tasks/T-197/verify.py` | +3 类断言（非唯一却填 selected / anchor_a 与 report 不一致 / A-B1-C 计数不一致）+ `anchored_by`⊆`discriminates`、`elimination`⊆`discriminates`、`selection` 复算块一致性 |
| `META/p0-case-packets-v1.md` | 由 `render_packets.py` 从 r2 卡重新渲染（脚本未改） |
| `tasks/T-197d/patch_p0_cards.py` | 幂等补丁脚本，记录 r2 每条修正；`build → patch` 可复现 |
| `tasks/T-197d/BRIEF.md` | 改动文件 / 原始输出 / 未完成与风险 / 下游须知 |

## 结果摘要

- **verify：退出码 0**（`[ok]` 8 条 + 逐卡 survivors 行），反向注入 6 类破坏均退出码 1（见 BRIEF §3.2）。
- **A/B1/C 计数**：A=3 / B1=7 / B2=0 / C=1（方向 claim 合计 **11**；去重前 12）。A 率 **3/11 = 27.3%**（去重前 3/12 = 25.0%），A 精度 3/3。按 **claim** 计数，不按卡计数。
- **selected 可复现**：P0-01/02/03 方向层幸存集为空；P0-04 方向层 3 条互补 A claim 全存活 → 卡级 `selected_option=null` + `selected_claims=[dc1,dc2,dc3]`；P0-04 state 层 AQ1=yes 消 st1、st3(C) 不参与 → st2 唯一 → `state_selected="败"`。
- **anchor_a 与 report 一致**：6 题（unknown 5 / yes 1），唯一的 yes 带 `source_ref=L398` + 逐字 `quote`。
- **P0-03 同源去重**：`dc3`（方向）与 `rs1`（救应）只保留救应一层；被移除项完整记录在 `dedup[0].original_record`。
- **未降门槛**：`a_share_vs_p0_gate.verdict` 仍为「未达」；没有为提升 A 率或 reproducibility 删候选/改答案/放宽断言。

## Blockers（需中枢/T-197c）

1. **T-197c 需重跑**：r2 已按 D01–D20 逐项修（BRIEF §2、report §4），D04 明确未修（P0-02 `outcome_quote` 域错配，medium、不影响选择层）。三方文件的 `evidence` 行号已因 r2 落盘整体偏移，需重取。
2. **A 率 27.3% < 50%（仅报告线）**：数据问题（4 例 material edge 多为冲/合/穿/刑），不是管道问题；需中枢决定 gate/分母/补固定类案例，本轮不调。
3. **`tasks/T-197/build_p0_cards.py` 未同步**：重跑 builder 会覆盖 r2；下游须 `build → patch`（`tasks/T-197d/patch_p0_cards.py`）。
4. **6 题中 5 题仍 unknown**：需命主/人类回答；`anchor_a` 已留位，回答时按 `field_semantics.anchor_a` 填（非 source_outcome 必须有 `source_ref`+逐字 `quote`，否则 verify 红）。
5. **`state_selected="败"` 的取舍需中枢确认**：走「C 档不参与选择」的显式规则（D19 第二种处理）使 st2 唯一；若平台偏好最保守分支（state 置 null + `state_tier=C`），改 `selection_rules` 的 C 档语义即可，其余字段已兼容。

## Execution Log

| 时间 | 动作 |
|---|---|
| 09:20 | T-197c fail（选择层 3/4=75%，P0-04 not_reproducible）；中枢建 `tasks/T-197d/PROMPT.md`，不降门槛 |
| 09:21 | 读卡：`PROMPT.md`、`p0-cards-v1.json`、`p0-report-v1.md`、`p0-thirdparty-v1.json`、`tasks/T-197/verify.py`；逐条对齐 D01–D20 |
| 09:22 | 复核原文 L392/L394/L396/L398（财官班教材）、L139/L141（疾病）、L21–L33（婚姻）、L25（军官），确认 quote 逐字与 AQ1 的 source 依据 |
| 09:25 | 写 `tasks/T-197d/patch_p0_cards.py`，施加 r2：P0-04 三条 A claim + `anchor_a=AQ1 yes` + 状态唯一化；P0-03 `dc3`/`rs1` 单层化 + AQ2 yes→eliminate；P0-01/02 `anchored_by`/`discriminates`/e015 理由；包级 `field_semantics`/`selection_rules`/metrics（12→11） |
| 09:30 | 重写 `META/p0-report-v1.md`（可机检答案表 + 计数行 + 20 项处理表） |
| 09:32 | 改 `tasks/T-197/verify.py`：加 3 类断言 + 3 条字段不变量；原「anchor_a 必须为空」「selected 必须 engine_fixed」两条按 r2 口径替换为更强的来源/唯一性校验 |
| 09:35 | 隔离副本反向验证 6 类注入，全部退出码 1；正式包 `verify.py` 退出码 0 |
| 09:38 | `render_packets.py` 重新渲染人读包；补丁连跑两次 sha256 一致（幂等） |
| 09:40 | 写 `BRIEF.md`、更新 `STATUS.md`；向中枢回报 |
