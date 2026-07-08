# 分层决策系统重构启动判断

## Thesis

系统重构的目标不是继续强化现有五派融合器，而是把它降级为旧兼容 / 对照 runner，同时新增 `engine/decision/` 分层决策栈。第一刀只做内存中的 `DecisionRun` 证明物：链路不断，再谈迁移。

## Confidence

中高。原因：`plans/layered-decision-system.md` 已明确 L0-L9 与第一证明物；现有 `engine/v5/runner.py` 已有命题、仲裁、预测账本雏形，但缺 L1 路由与显式 L0-L7 链路对象。

## The Trap

陷阱是把重构做成“再包一层 v5”或“立刻替换生产入口”。这不是现实约束，只是历史路径惯性；真实约束是不能破坏当前报告、反馈摄入与测试。

## High-格局 Direction

建立司法式分层决策栈：L0 事实账本、L1 流派资格审查、L2 独立命题、L3 结构否决、L4 事件落地、L5 应期概率、L6 冲突裁判、L7 只读报告。旧 `application/pipeline_runner.py` 保持兼容，不新增能力。

## Frame-Opening Move

Zero-Legacy Thought Experiment：如果没有历史入口，系统不会先让所有派别共同写报告，而是先问“这张命盘、这个领域，谁有资格主审”。这说明 L1 路由必须先于 L2 命题池。

## Bold Takes

- 删除方向：停止把 D1-D4 串行叙事当全局主流程。
- 合并方向：现有 `v5` 命题、结构图、仲裁、预测账本以后逐步映射到 L2-L6，不在第一刀迁移。
- 拆分方向：把 L0 / L1 从旧 preflight 与 v5 runner 中独立出来。
- 不保留：内部兼容 shim、全局综合评分、固定权重、报告层补推理。

## Options

| 路线 | 做法 | Verdict |
|---|---|---|
| Conservative path | 在 `engine/v5/runner.py` 继续加字段模拟 L0-L9 | 不选：会继续把路由、命题、仲裁混在一个文件 |
| Clean target | 直接重写生产入口为 L0-L9 | 暂不选：证明物不足，风险超过收益 |
| Staged clean path | 新增 `engine/decision/`，先做内存 `DecisionRun`，不切入口 | 选定：最小可验证、不会破坏现有流程 |

## What Not To Do

- 不切 `tools/render_report.py` 默认出口。
- 不删除 `engine/application/pipeline_runner.py`。
- 不把 `v5` 全量搬家。
- 不新增数据库、配置中心或复杂插件机制。

## First Proof Point

`run_decision_mvp()` 能从一段问真专业文本生成 L0-L7 对象，且 `DecisionRun.validate_trace()` 为空。

## Falsifier

如果第一证明物无法稳定表达 `ReportViewItem → ArbitrationDecision → TimingProbability → EventHypothesis → StructuralVerdict → SchoolClaim → SchoolApplicability → ChartFactLedger → RawWenzhenPayload`，或必须依赖生产入口大改才能成立，则本方向需要回炉。
