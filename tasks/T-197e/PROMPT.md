# T-197e · P0 r2 内容修复（T-197c r2 的 4 个优先项 + 附带）

- 状态：🔵 Ready
- 依据：`META/p0-thirdparty-v2.json`（12 差异/6 缺证据，selected 4/4）
- 前置：main `010de52e`

## 0. 一句话

只修 P0 卡的 root 副本与内容层，不跑 P1、不改 engine、不降门槛。修完 verify 0，再由 T-197c r3 复核。

## 1. 四个优先项

1. **D-R2-02**：P0-03 `root anchor_questions.AQ2` 仍是 `downgrade`；卡内已 `eliminate st1`。root 必须同步为 eliminate。
2. **D-R2-01**：P0-01 `root anchor_questions.AQ2.discriminates` 仍是 `[dc1,dc3]`；卡内已 `[dc1,dc2,dc3]`。root 同步。
3. **D04**：P0-02 `outcome_quote` 仍是 L25 婚姻句；事业结局在 `outcome_note`。改成事业结局引文，或明确 `outcome_quote=null` + note。
4. **P0-04 H.b**：dc1 只取月丑 M.b，漏时丑 H.b；L392“月时丑都入辰墓”、engine 墓用 `[D.b,H.b]`、e011。补 H.b 并记录两丑入墓。

## 2. 附带项

- **D-R2-05**：P0-04 st2 `decision_by=expert_single_choice` 与 `anchored_by=[AQ1]`/`state_decision=anchor_fact`/`expert_decision=null` 残留；统一为 `anchor_fact` 或 `expert_decision`。
- **D-R2-06**：metrics `state_candidates_selectable` 9→8（P0-01 st3 也是 C/定义口径）。
- **D-R2-07**：P0-03 st2 的 L131 是乾造 乙戊丙己/卯寅午丑，不是本造；删/改归属。
- **D-R2-10**：P0-04 AQ1 `source_outcome` 在 2003（L398 癸未），`fact_window=2010-2025`；窗口改为覆盖 2003，或把问题改成窗口内事实。
- **D-R2-09**：P0-04 st3 的 C 标签是扩展借用；改 `definition/non_outcome`（或加 `label_note`），保留 `selectable=false`。
- **D-R2-11/12**：P0-03 st1/st2 同 result「病」，只分病位；P0-04 st1/st2 是“富→破”时间序列。加 `state_scope` 说明，避免把“病位”当“病/不病”、把“轨迹”当“同一时点互斥”。
- **6 项缺证据**：M-01..06 逐条写入 `missing_evidence`，能补的补，补不了的标明“缺”。

## 3. 产物

- 修正后的 `META/p0-cards-v1.json`、`META/p0-report-v1.md`、`META/p0-case-packets-v1.md`
- `tasks/T-197e/BRIEF.md` + `STATUS.md`
- 不跑 P1；不做 git 写；不改 engine/保护区/A+。

## 4. 验收

- `tasks/T-197/verify.py` 退出 0；
- root `anchor_questions` 与卡内一致；
- 4 个优先项逐条在 BRIEF 列“改前/改后/证据”；
- T-197c r3 只核这 4 项 + selected，≥90% 且 4 项清零才进 P1。
