# T-196 STATUS

- 状态：🟢 交付待中枢验收（2026-10-30，子代理 AX）
- 执行者：子代理 AX
- 任务卡：`tasks/T-196/PROMPT.md`
- 验收：中枢亲自看；只写规格
- 交付：三份规格 + `tasks/T-196/BRIEF.md` + 本文件

## Execution Log

| 时间 | 动作 |
|---|---|
| 08:15 | 人类同意 Agent-first；建卡派发（中枢） |
| 08:20 | 读卡与证据：T-191 裁决、`fact-evidence-pack-v1`、`fact-audit-v1`、fixed-20、r-tool run v1/routing、`archive/adjudication_v1/README` |
| 08:25 | 冻结 A/B1/B2/C、字段、P0/P1/P2 gate/kill；写三份规格 |
| 08:30 | 自检 JSON 块（13+8 全部可解析）、表格列数、相对链接、字段名；全部通过 |
| 08:35 | 写 `BRIEF.md`；更新 `STATUS.md` |
| 08:40 | 按中枢 T-197 反馈修正：P0 删除 A≥50%，改为 ≤2 题/≤5 分钟/字段完整性；A 可引擎确定性落定（`pending=none`）；`same_page` 不升 A；补第三轮修正对照 |

## Deliverables

1. `docs/goals/first-principle-agent-first-v1.md`（目标/角色/A-B1-B2-C/P0-P1-P2 gate 与 kill）
2. `docs/specs/analysis-card-v2.md`（卡字段/候选/锚点/专家/校验/示例）
3. `docs/specs/agent-candidate-generator-v1.md`（固定类 A、动态 B1/B2/C、锚点问题、校验丢弃）
4. `tasks/T-196/BRIEF.md`（改动/原始输出/风险/下游/修正对照/口径决策）
5. `tasks/T-196/STATUS.md`（本文件）

## Blockers

- 无阻塞规格交付的硬 blocker；以下为待中枢确认项：
  1. **`A≥90%` 口径**：本规格按 `a_rate_fixed`（A/固定类）与 `a_precision`（A 卡复核成立/A）双指标；若只要一项，P1 前确认。
  2. **P0 口径**：P0 只验管道/完整性/字段/≤2 题/≤5 分钟；A 自动占比只报告（T-197 3/12=25% 是真实结构，不判失败）；A≥90% 是 P1 门槛，不是 P0。
  3. **候选 2–3 的例外**：A 固定类/单候选 B2 允许 1 条，C/`not_claimed` 允许 0 条；若必须硬性 2–3，与「不得编造候选」冲突，需裁决。
  4. **B2 单候选确认**：动态单候选不能 A、不能 B1，落 B2 专家确认或 C；可能推高 B2 占比。
  5. **`direction_known` 语义**：仅 A 固定为 true；B1/B2 选中动态不投影到 `t2.actor/target`；下游若要直接读，需另加字段。
  6. **`same_page` 不升 A**：P0-01/P0-03 的 `same_page` 依据只作 B1 候选；A 必须至少有 `engine_candidate` / `engine_fixed_rule`。
  7. **T-197 P0 状态（据中枢转述）**：12 卡中 A=3/12=25%，6 个 B1 事实题已交人类，B2=0；符合「冲/合/穿/刑禁 A」结构，P0 不据此 kill。
- 非 T-196 的工作区并行物：`META/p0-cards-v1.json`、`META/p0-case-packets-v1.md`、`tasks/T-197/*`（并行产出）；`META/p1-holdout-baseline-v1.*` 在 T-196 前已显示 M、`git diff` 无文本差异。T-196 未触碰，不应计入本卡 diff。
- 任务卡前置 `af22f270` 与工作区 HEAD `1a773249` 不一致；仅记录，不影响规格内容。
- 未写代码、未跑盲测/评分器、未做 git 写、未改保护区；`seeded_error` 校验器与 P0/P1/P2 均未实现/执行，本卡只是规格。
