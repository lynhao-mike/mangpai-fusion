# mangpai-fusion 项目进度仪表盘

> 状态快照：2026-10-07；机器状态源：`progress/PROJECT_PROGRESS.json`。
> 本仪表盘展示工程任务完成度，不把工程完成度等同于现实验证或生产准入。

## 当前总览

| 项目 | 当前值 |
|---|---|
| 产品版本 | `1.3.1` |
| 当前工作阶段 | `six-source-three-domain-verification-and-governance` |
| 加权任务进度 | **80.0%** |
| 下一阶段 | `P05` |
| 真实 prospective cohort | `not_ready` |
| 单案例未来观察 | `not_completed` |
| production_ready | **false** |
| production_switch_permitted | **false** |

### 结论

当前系统的工程能力已覆盖多个阶段，但现实 cohort 尚未就绪，生产准入仍关闭。

## 阶段进度

| 阶段 | 名称 | 状态 | 就绪条件 | 进度 | 已完成任务 |
|---|---|---|---|---:|---:|
| `P01` | 基础架构、理论资料与规则入库 | `COMPLETE` | `COMPLETE` | 100.0% | 4/4 |
| `P02` | 引擎、报告、反馈闭环与版本契约 | `COMPLETE` | `LOCKED` | 100.0% | 6/6 |
| `P03` | 六源三领域分析与治理能力 | `COMPLETE` | `ENGINEERING_COMPLETE / REAL_COHORT_NOT_READY` | 100.0% | 5/5 |
| `P04` | 命局候选保留与目标级裁决 | `COMPLETE` | `CHART_ONLY_EXIT_LANDED / PRODUCTION_MAPPING_PENDING` | 100.0% | 5/5 |
| `P05` | L2 → 现实测量层 | `IN_PROGRESS` | `GOVERNANCE_APPROVED / SPEC_PENDING` | 70.0% | 3/5 |
| `P06` | As-of / prospective 验证 | `VALIDATING` | `ENGINEERING_COMPLETE / COHORT_NOT_READY` | 36.4% | 2/5 |
| `P07` | 生产切换与最终验收 | `BLOCKED` | `NOT_READY` | 40.0% | 1/3 |

## P01 · 基础架构、理论资料与规则入库

状态：`COMPLETE`；就绪状态：`COMPLETE`；阶段权重：10。
阶段进度：**100.0%**（任务权重 4.0/4.0）。

进入条件：

- 仓库具备统一 schema、理论资料入口与规则数据结构。

退出条件：

- M1-M4 完成，四派资料入库并具备跨派映射基础。

任务：

| 任务 | 状态 | 完成度 | 权重 | 证据 / 说明 |
|---|---|---:|---:|---|
| `P01-T01` 仓库骨架、schema 与语料迁入 | `COMPLETE` | 100.0% | 1 | STATUS.md |
| `P01-T02` 高派与段派规律入库 | `COMPLETE` | 100.0% | 1 | STATUS.md |
| `P01-T03` 杨派与任派规律入库 | `COMPLETE` | 100.0% | 1 | STATUS.md |
| `P01-T04` 跨派映射矩阵建立 | `COMPLETE` | 100.0% | 1 | STATUS.md |

阻塞项：

- 无

下一步：

- 无

## P02 · 引擎、报告、反馈闭环与版本契约

状态：`COMPLETE`；就绪状态：`LOCKED`；阶段权重：15。
阶段进度：**100.0%**（任务权重 6.0/6.0）。

进入条件：

- 理论与规则资料已具备可执行入口。

退出条件：

- M5-M10 完成，分析、报告、反馈和版本契约均有稳定入口。

任务：

| 任务 | 状态 | 完成度 | 权重 | 证据 / 说明 |
|---|---|---:|---:|---|
| `P02-T01` 双轨置信度引擎与仲裁引擎 | `COMPLETE` | 100.0% | 1 | STATUS.md |
| `P02-T02` 主分析器与输入输出模板 | `COMPLETE` | 100.0% | 1 | STATUS.md |
| `P02-T03` META 自迭代、校准工具与案例归档 | `COMPLETE` | 100.0% | 1 | STATUS.md |
| `P02-T04` v1.2 双层引擎契约与发布门槛 | `COMPLETE` | 100.0% | 1 | STATUS.md |
| `P02-T05` v1.2 维度引擎与三层护栏 | `COMPLETE` | 100.0% | 1 | STATUS.md |
| `P02-T06` v1.3 自迭代闭环 D1-D8 | `COMPLETE` | 100.0% | 1 | STATUS.md |

阻塞项：

- 无

下一步：

- 无

## P03 · 六源三领域分析与治理能力

状态：`COMPLETE`；就绪状态：`ENGINEERING_COMPLETE / REAL_COHORT_NOT_READY`；阶段权重：15。
阶段进度：**100.0%**（任务权重 7.0/7.0）。

进入条件：

- 基础分析、报告和反馈闭环已稳定。

退出条件：

- 六源三领域工程能力完成；现实验证另由 P06 管理，不能由工程完成状态替代。

任务：

| 任务 | 状态 | 完成度 | 权重 | 证据 / 说明 |
|---|---|---:|---:|---|
| `P03-T01` 六源三领域分析引擎 | `COMPLETE` | 100.0% | 2 | META/project-state.json |
| `P03-T02` 命理师逐命题报告工作台 | `COMPLETE` | 100.0% | 2 | META/project-state.json |
| `P03-T03` 十八槽位 registration/runtime 诊断 | `COMPLETE` | 100.0% | 1 | META/project-state.json |
| `P03-T04` 高风险命题失败关闭门禁 | `COMPLETE` | 100.0% | 1 | META/project-state.json |
| `P03-T05` 命题级 create-only 反馈与只读校准候选 | `COMPLETE` | 100.0% | 1 | META/project-state.json |

阻塞项：

- 真人 prospective cohort 仍为 not_ready；该项不回写为工程完成。

下一步：

- 由 P06 继续处理真实 cohort 与未来观察。

## P04 · 命局候选保留与目标级裁决

状态：`COMPLETE`；就绪状态：`CHART_ONLY_EXIT_LANDED / PRODUCTION_MAPPING_PENDING`；阶段权重：20。
阶段进度：**100.0%**（任务权重 10.0/10.0）。

进入条件：

- 现有命题可以保留并按 domain/task/target 组织。

退出条件：

- 目标级裁决稳定输出；现实映射注册、Measurement Spec 和完整生产报告切换另需完成。

任务：

| 任务 | 状态 | 完成度 | 权重 | 证据 / 说明 |
|---|---|---:|---:|---|
| `P04-T01` 统一 AdjudicationUnit 与候选保留 | `COMPLETE` | 100.0% | 2 | plans/chart-adjudication-implementation-2026-10-07.md |
| `P04-T02` 按 target_id 的同向/冲突/不支持裁决 | `COMPLETE` | 100.0% | 2 | plans/chart-adjudication-implementation-2026-10-07.md |
| `P04-T03` V5 目标级报告视图不覆盖未决结论 | `COMPLETE` | 100.0% | 1 | plans/chart-adjudication-implementation-2026-10-07.md |
| `P04-T04` 现实映射注册表与单位级映射状态 | `COMPLETE` | 100.0% | 3 | mapping/chart-l2-measurement-registry-v1.json；tools/measurement_registry.py |
| `P04-T05` chart-only 结构裁决出口与边界验收 | `COMPLETE` | 100.0% | 2 | tools/chart_adjudication.py；tests/test_chart_adjudication_cli.py |

阻塞项：

- 候选映射已登记，但没有已批准的现实映射；未完成映射的裁决单位必须保持 NO_MAPPING。

下一步：

- 保持现实映射独立受 P05 管理，不把 chart-only 主断直接写成现实标签。

## P05 · L2 → 现实测量层

状态：`IN_PROGRESS`；就绪状态：`GOVERNANCE_APPROVED / SPEC_PENDING`；阶段权重：15。
阶段进度：**70.0%**（任务权重 7.0/10.0）。

进入条件：

- L2→现实测量层治理框架已获批准，且不自动批准任何具体映射。

退出条件：

- 具体 L2 完成语义保真审查、映射类型与 Measurement Spec 冻结，并由独立验证流程接收。

任务：

| 任务 | 状态 | 完成度 | 权重 | 证据 / 说明 |
|---|---|---:|---:|---|
| `P05-T01` 治理框架获批并冻结边界 | `COMPLETE` | 100.0% | 3 | plans/measurement/ |
| `P05-T02` “学业有成”候选测量对象审计 | `COMPLETE` | 100.0% | 2 | plans/measurement/ |
| `P05-T03` “学业有成”候选 Measurement Spec v0.1 结构化制品 | `COMPLETE` | 100.0% | 2 | plans/measurement/academic-achievement-v0.1-spec.json |
| `P05-T04` 映射、观察与证伪条件冻结 | `BLOCKED` | 0.0% | 2 | plans/measurement/ |
| `P05-T05` blind pilot 准入审查 | `BLOCKED` | 0.0% | 1 | META/project-state.json |

阻塞项：

- 当前尚未冻结任何具体 L2→L3 Measurement Spec；不得启动 blind pilot。

下一步：

- 先完成一个具体候选的 Measurement Spec，允许最终被拒绝为 NO_MAPPING。

## P06 · As-of / prospective 验证

状态：`VALIDATING`；就绪状态：`ENGINEERING_COMPLETE / COHORT_NOT_READY`；阶段权重：15。
阶段进度：**36.4%**（任务权重 4.0/11.0）。

进入条件：

- 盲态输入、冻结、揭示、评分协议已实现。

退出条件：

- 完成真实未知结果 cohort、未来观察与独立评分，并产生可审计验证证据。

任务：

| 任务 | 状态 | 完成度 | 权重 | 证据 / 说明 |
|---|---|---:|---:|---|
| `P06-T01` blind bundle / freeze / reveal / score 协议 | `COMPLETE` | 100.0% | 3 | META/project-state.json |
| `P06-T02` 单案例 prospective 链路实现 | `COMPLETE` | 100.0% | 1 | META/project-state.json；engine/evaluation/prospective_single_case.py；engine/evaluation/prospective_capability_identity.py |
| `P06-T03` 真实 prospective cohort 建立 | `READY` | 0.0% | 3 | META/project-state.json |
| `P06-T04` 未来观察完成并形成评分数据 | `READY` | 0.0% | 2 | META/project-state.json |
| `P06-T05` 经验验证门禁与生产准入结论 | `BLOCKED` | 0.0% | 2 | META/project-state.json |

阻塞项：

- domain prospective real_cohort=not_ready。
- 单案例 future_observation 尚未完成。

下一步：

- 在不泄漏现实结果的前提下建立真实 cohort，再执行冻结后的 reveal/score。

## P07 · 生产切换与最终验收

状态：`BLOCKED`；就绪状态：`NOT_READY`；阶段权重：10。
阶段进度：**40.0%**（任务权重 2.0/5.0）。

进入条件：

- P04、P05、P06 的退出条件均已满足。

退出条件：

- 现实映射、未知结果验证与生产准入门禁全部通过，production_ready=true。

任务：

| 任务 | 状态 | 完成度 | 权重 | 证据 / 说明 |
|---|---|---:|---:|---|
| `P07-T01` production readiness 门禁实现与失败关闭输出 | `COMPLETE` | 100.0% | 2 | engine/evaluation/domain_prospective.py；tools/domain_prospective_cohort.py |
| `P07-T02` production readiness 门禁通过 | `BLOCKED` | 0.0% | 2 | META/project-state.json |
| `P07-T03` 最终验收与发布判定 | `BLOCKED` | 0.0% | 1 | META/project-state.json |

阻塞项：

- 现实测量映射不足。
- 真实未知结果验证尚未完成。
- 当前 production_ready=false。

下一步：

- 先完成 P04-P06 的阻塞项，不提前切换生产入口。

## 全局阻塞项

- 当前生产状态仍为 production_ready=false，不能把工程落地等同于准确性验证。
- 现实结果不得污染盲态裁决与已冻结分析制品。

## 下一步

1. 审查并决定候选 Measurement Spec 是否可以进入正式冻结；不批准时保持 UNRESOLVED。
1. 在具体 Measurement Spec 获批前保持 blind pilot 暂停。
1. 保持 P06 的真实 cohort 状态为 not_ready，直到有独立未知结果数据。
