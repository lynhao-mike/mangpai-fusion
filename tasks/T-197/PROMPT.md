# T-197 · P0 3–5 例 Agent 卡 + 候选选项（不自动选定）

- 状态：🔵 Ready
- 依据：T-196 三份规格（可先读 plan；卡 schema 以 T-196 为准）
- 前置：main `af22f270`

## 0. 一句话

选 3–5 例真实盘（非 dev-20/fresh-40/anchor-60），Agent 写全卡 + 2–3 个候选选项；
引擎校验地址/边/十神/引文；**不自动选定**；把“人的 1–2 个关键选择”整理成选择题，交中枢/人类。

## 1. 选例

- 3–5 例；覆盖婚/事业/健康/财；有明确问题；有 `sources/duan/` 原文；
- 排除 dev-20/holdout-20/fresh-40/anchor-60；不用旧 3 卡；
- 四柱/性别/出生信息/问题；已知真实后续事件可选（P0 不做预测，仅备查）。

## 2. 每例输出

- `chart_id`、四柱、问题、engine 事实（`engine.cli`）；
- `direction_candidates[]` 2–3：每条的 actor→target/mutual/needs_anchor、basis、source_ref、逐字 quote、decisive、conflict_with；
- `state_candidates[]` / `rescue_candidates[]`：成/败/救/应/needs_anchor，带 source；
- `engine_validation`：address/edge/ten_god/quote 是否通过；失败候选作废；
- **不做最终选择**；列成“关键选择 A/B”给人类。

## 3. 隔离/边界

- 不读 anchor/fresh/holdout/golden/`p1-system-run*` 的答案；不读 A+ 答案；
- 不跑评分器；不做方向自动承诺；不做 git 写；不改 engine/保护区；
- 不把 `needs_anchor` 写成断语；不发明边/地址。

## 4. 产物

- `META/p0-cards-v1.json`（3–5 卡 + 候选 + 校验）
- `META/p0-case-packets-v1.md`（每例一页：事实/候选/关键选择/锚点）
- `tasks/T-197/BRIEF.md` + `STATUS.md`
- 人选择后由中枢另卡记录（T-197b）；第三方重推另卡。
