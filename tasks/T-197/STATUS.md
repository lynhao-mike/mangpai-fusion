# T-197 STATUS

- 状态：🟡 待中枢验收（`pending=anchor_q`；方向未选定）
- 执行者：子代理（T-197 P0 Agent）
- 任务卡：`tasks/T-197/PROMPT.md`
- 验收：中枢跑 `tasks/T-197/verify.py`（退出码 0）+ 抽查引文；人类只答事实题；第三方重推另测

## 产物

| 文件 | 说明 |
|---|---|
| `META/p0-cards-v1.json` | 4 卡 / 12 方向候选（A 3 · B1 8 · C 1）/ 10 状态 + 4 救应 / 6 锚点事实题 / 全量 engine 校验 + `schema_compat` + 20-fixture self_test |
| `META/p0-case-packets-v1.md` | 每例一页人读包 + 关键选择清单 + 答案回收表（留空）+ v2 对齐说明 |
| `tasks/T-197/BRIEF.md` | 改动文件 / 原始输出 / 未完成与风险 / 下游须知 |
| `tasks/T-197/build_p0_cards.py`、`render_packets.py`、`verify.py` | 构建、渲染、验收门禁（verify 仅标准库） |
| `tasks/T-197/_engine/*.json`、`_exclusion.json` | engine 快照（8 次调用）/ 排除集四柱（仅查重） |

## 结果摘要

- 4 例，覆盖 婚/事业/健康/财；四柱与 dev-20（F20）/fresh-40（PF）/anchor-60（A60）/holdout-20（P1-H）/旧 3 卡 **零重叠**（133 个排除四柱）。
- 校验：address 26/26、edge 12/12、ten_god 26/26、候选引文 26/26、原文/宫位引文 24/24；逐卡植入错误 16/16、self_test 20/20；失败候选 0。
- 档位：方向候选 A 3/12 = 25%（未达 T-196 P0 gate ≥50%）、B1 8、C 1；B2 触发 0；卡级 tier 全 B1（P0-04 方向层 A + 成败层冲突）。
- 未选定：`selected_option=null`、`anchor_a=[]`、`selection_source=needs_anchor`、`pending=anchor_q`。

## Blockers（需中枢/人类）

1. **A 档 gate 未达**：冲/合/穿/刑不得 A 的口径下，4 例的 material edge 多为对称关系。需中枢决定调 gate、改分母（只看固定类候选）或补固定类案例。
2. **6 个锚点事实题待答**：P0-01 AQ1/AQ2、P0-02 AQ1、P0-03 AQ1/AQ2、P0-04 AQ1（state）。人只答事实；答完由 T-197b 机械淘汰。
3. **T-196 规格落盘后的两处口径冲突**：v2 的 A 要求 `selected_option` 已填、C 也用 `selected_option=null`；T-197 禁止代选 → 本包用 `direction_tier` + `pending` 区分「待自动确认的 A」与「无源 C」。是否允许 T-197b 直接落 `agent_auto`，需中枢裁。
4. **P0-01/P0-03 单侧施力依据为结果句/计数句**（`same_page` 缺口），是否够格由中枢/第三人裁。

## Execution Log

| 时间 | 动作 |
|---|---|
| 08:15 | 建卡派发；P0 3–5 例 Agent 卡 |
| 08:19 | 读卡 + 规格 + T-196 卡（当时三份规格未落盘）+ 两份 R-tool META；从 `sources/duan/` 选定 4 例（婚姻专辑/如何看军官/疾病/财官班教材），四柱查重零重叠 |
| 08:20 | 8 次 `engine.cli`（all/relations × 4 盘）取事实；39 条引文先行逐字预检 |
| 08:21 | 按中枢追加口径改为 B1/B2 版：`build_p0_cards.py` 生成 `META/p0-cards-v1.json`（校验失败 0） |
| 08:22 | `render_packets.py` 生成 `META/p0-case-packets-v1.md`；`verify.py` 退出 0 |
| 08:24 | T-196 三份规格落盘；按 `analysis-card-v2` / `agent-candidate-generator-v1` §7 改名补字段（option_id/claim/basis/direction_tier/pending/elimination），加 `schema_compat` 与 20-fixture self_test |
| 08:26 | 修正 P0-04：原局富/岁运破属成败层，不适用方向层 B2 → 改 state 锚点题，`expert_decision=null`，B2=0；重建 → 重渲染 → `verify.py` 退出 0 |
| 08:27 | 写 `BRIEF.md`、更新 `STATUS.md`；向中枢回报 |
