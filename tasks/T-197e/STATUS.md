# T-197e STATUS

- 状态：🟡 待中枢复验 + T-197c r3（r3 已落盘，`tasks/T-197/verify.py` 退出 0）
- 执行者：子代理（T-197e P0 卡内容修复 Agent）
- 任务卡：`tasks/T-197e/PROMPT.md`
- 验收：中枢跑 `tasks/T-197/verify.py`（退出码 0）+ 抽查 4 项优先/root 副本；T-197c r3 只核 4 项 + selected，≥90% 且 4 项清零才进 P1
- 边界：不改 engine/保护区/答案/候选取舍；不跑 P1；不做 git 写；不降门槛

## 产物

| 文件 | 说明 |
|---|---|
| `META/p0-cards-v1.json` | r3：root `anchor_questions` 同步；P0-02 事业结局引文；P0-03 他造归属；P0-04 H.b/e011/state 口径；`missing_evidence` 6 项；metrics `state_candidates_selectable=8` |
| `META/p0-report-v1.md` | r3：标题/范围；§2 窗口；§4 D02/D04/D09；§4.1 12 项差异处理；§5 风险；§6 结论 |
| `META/p0-case-packets-v1.md` | 由 `tasks/T-197/render_packets.py` 从 r3 卡重渲染；头部统计/anchor_a/缺证据清单已更新 |
| `tasks/T-197e/patch_p0_cards_r3.py` | 幂等补丁脚本；`build → T-197d patch → T-197e patch` 可复现 |
| `tasks/T-197e/BRIEF.md` | 四个优先项改前/改后/证据、附带项、原始输出、风险、下游须知 |
| `tasks/T-197/render_packets.py` | 渲染层小修（统计/修订号/anchor_a/缺证据/co_claims/state_scope_note 从 JSON 派生） |

## 结果摘要

- **4 个优先项全部落盘**：
  - D-R2-02 P0-03 root AQ2 yes：`downgrade=[st1]` → `eliminate=[st1]`；
  - D-R2-01 P0-01 root AQ2：`[dc1,dc3]` → `[dc1,dc2,dc3]`；
  - D04 P0-02 `outcome_quote`：L25 婚姻句 → L25 事业结局句（副军长/预测正军级）；
  - P0-04 dc1：补时支丑 H.b、两丑入辰墓、engine 墓用 `[D.b,H.b]`、e011 辰丑破。
- **附带项**：D-R2-05/06/07/09/10/11/12 逐项处理；D-R2-04 部分处理（M-02 仍缺）。
- **root 副本**：`anchor_questions` 6 题与卡内逐字段一致（`root_sync_mismatches=[]`）。
- **verify**：退出码 0；A=3 / B1=7 / B2=0 / C=1；selected 4/4 不变（P0-01/02/03 null；P0-04 `selected_option=null`/`state_selected=败`）。
- **未降门槛**：A 率仍 27.3%「未达」；没有删候选、改答案、放宽断言。
- **缺证据**：6 项已入 `missing_evidence`；M-01/M-03 已补、M-05 部分、M-02/M-04/M-06 标缺。

## Blockers / 待中枢

1. **T-197c r3 未跑**：需按 r3 只核 4 项优先 + selected；≥90% 且 4 项清零才进 P1。
2. **M-02/M-04/M-06 缺证据**：不影响 selected，但 M-02 关系 B1 竞争设计必要性、M-04 关系 P0-03 st2 可锚性、M-06 关系 seeded 口径强度；需中枢决定是否 P1 前补。
3. **A 率 27.3% < 50%（仅报告线）**：数据问题，不是管道问题；本轮未调 gate。
4. **repro 链条未合并**：`build_p0_cards.py` 未同步 r2/r3；下游须按 `build → T-197d patch → T-197e patch`。
5. **6 题中 5 题仍 unknown**：需命主/人类回答；`anchor_a` 已留位。
6. **P0-04 st3 仍是 `tier=C` 扩展借用**：已加 `candidate_kind=definition/non_outcome` + `label_note`；严格 schema 下游按定义口径读。

## Execution Log

| 时间 | 动作 |
|---|---|
| 09:38 | 读 `tasks/T-197e/PROMPT.md`、`META/p0-cards-v1.json`、`META/p0-report-v1.md`、`META/p0-thirdparty-v2.json`、`tasks/T-197/verify.py`；基线 verify 0 |
| 09:40 | 核对第三方的 12 项差异与 6 项缺证据，定位到 root `anchor_questions`、P0-02 `source.outcome_quote`、P0-03 st2 `basis_text`、P0-04 dc1/palaces/material_edges/metrics/state |
| 09:43 | 写 `tasks/T-197e/patch_p0_cards_r3.py`，施加 r3；补丁连跑两次 sha256 一致（幂等） |
| 09:45 | 重渲染 `META/p0-case-packets-v1.md`；修 `render_packets.py` 的旧头部/`anchor_a=[]` 硬编码 |
| 09:46 | 更新 `META/p0-report-v1.md`：§2 窗口、§4 D02/D04/D09、§4.1 12 项、§5/§6 |
| 09:47 | 独立检查 root 同步、全部 quote 逐字、H.b/e011、`expert_single_choice` 计数、metrics、missing_evidence；全部通过 |
| 09:48 | `tasks/T-197/verify.py` 退出 0（最终输出见 BRIEF §5.1） |
| 09:49 | 写 `BRIEF.md`、更新 `STATUS.md`；向中枢回报 |
