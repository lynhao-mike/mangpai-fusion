# T-196 · Agent-first 第一性原则方案 + 卡 schema + 候选生成器规范

- 状态：🔵 Ready
- 依据：人类同意 Agent-first + 人在关键点选择；A+ kill；R-tool pass
- 前置：main `af22f270`

## 0. 一句话

写三份**规格**：第一性原则实现方案、五元组卡 v2（含候选层/选择来源/引擎校验）、
Agent 候选生成器（A/B/C 三档）。**不写代码、不做方向、不跑盲测、不改保护区文件。**

## 1. 文档

1. `docs/goals/first-principle-agent-first-v1.md`
   - 角色：引擎事实/校验；Agent 候选；人只做 1–2 个关键选择；
   - A 档自动 / B 档人选择 / C 档 needs_anchor；
   - P0 3–5、P1 10–20、P2 20–40 前瞻；
   - P0 gate：A 档自动占比 ≥50%、人 ≤15 分钟/卡、第三方重推 ≥90%、无无源断言；
   - P1/P2 gate 与 kill；不自动承诺冲/合/穿/刑方向；不复活 A+；不改保护区。
2. `docs/specs/analysis-card-v2.md`
   - 字段：宫位/十神、边ID、`direction_candidates[]`（2–3，每条带 basis/source_ref/quote/decisive/conflict_with）、
     `selected_option`、`selection_source`（agent_auto/human_fork/needs_anchor）、
     `state_candidates[]`、`rescue_candidates[]`、`engine_validation`（address/edge/ten_god/quote）；
   - A/B/C 的判定；无源即 C；伪造边/地址直接作废。
3. `docs/specs/agent-candidate-generator-v1.md`
   - 固定克/生/化/墓直接 A；
   - 冲/合/穿/刑只生成候选，不自动承诺；候选必须带原文/势/宾主依据；
   - 只有一个 decisive 候选且无冲突才 A；2–3 个冲突进 B；无源/穿制冲突进 C；
   - 不得发明边/地址/十神；引擎校验失败即丢弃。

## 2. 产物

- 三份文档 + `tasks/T-196/BRIEF.md` + `STATUS.md`
- 不写代码、不跑盲测、不改 engine/答案/保护区；不做 git 写。

## 3. 禁止

- 不自动承诺冲/合/穿/刑方向；不复活党势；不用旧 3 卡；不扩岁运/P2 以外。
- 不碰 `AGENTS.md` §4、`report-v7-human.md`。
