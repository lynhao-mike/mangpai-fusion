# G10 下一治理里程碑计划

- 计划日期：2026-07-27（Asia/Shanghai）
- 计划性质：阶段 B 纯治理计划；不含实现，不构成实现或测试授权
- 进入依据：[`g6-task9p-total-gate-upgrade-review.md`](g6-task9p-total-gate-upgrade-review.md) 已裁决 Task 9-P 为 `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`
- 当前状态：**`PLANNED / NOT STARTED`**
- 本地状态：**`LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION`**

## 1. 里程碑 thesis

G10 不应立即扩张到 F10，也不应把 F09 的有界通过包装成“全量生产就绪”。下一治理里程碑应先建立一条**从 F09 evidence-bounded slice 到可裁决 production-readiness admission 的证据路径**，并把已知的两个非 F09 全仓 sanity 失败作为独立治理工作流分账，而不是混入 F09 修复或用来推翻已冻结的 Task 9-P/G6–G9 结论。

因此 G10 的唯一目标是：

> **形成 F09 全量生产就绪准入包，并对两个非 F09 sanity 失败给出独立、证据有界的处置裁决；随后才对 F10 是否启动作 Go / Hold / Reject 决策。**

G10 不是实现里程碑。任何代码、测试、文档修复或 F10 开发都必须由 G10 后续子 Gate 的独立授权启动。

## 2. 目标与非目标

### 2.1 目标

1. 恢复并冻结 G10 的权威事实源、保护边界和当前证据基线；
2. 建立 F09 production-readiness 缺口清单，区分已证明、未证明、无需证明和外部能力；
3. 对全仓 sanity 中两个已知非 F09 失败分别做只读归因与处置准入，不把它们归因于 F09；
4. 定义 production readiness 的 Gate、owner、证据类型、STOP 条件和 non-inference boundaries；
5. 形成 F10 启动决策包，但不在 G10 中实现 F10；
6. 输出唯一里程碑裁决和可恢复 handoff。

### 2.2 非目标

G10 本身不做：

- 不修改 [`../engine/f09/`](../engine/f09/) 或 [`../tests/f09/`](../tests/f09/)；
- 不修复 [`../tools/README.md`](../tools/README.md) 或 [`../handoff.md`](../handoff.md)；
- 不执行全仓测试、F09 测试或任何其他测试，除非后续 G10 VERIFY 合同明确授权精确命令；
- 不改变 production-default；
- 不重开 F01–F12 冻结业务语义；
- 不启动 F10 实现、schema 变更、API 变更或十二卡全量扩张；
- 不宣称部署、发布、生产可用性、性能、安全、跨平台或远端同步；
- 不执行任何 Git 命令；
- 不执行任何 GitHub 读写、网络发布、PR、Issue、Release、workflow 或服务端操作。

## 3. 候选方向与裁决

| 候选 | 内容 | 优点 | 主要风险 | G10 裁决 |
|---|---|---|---|---|
| A | 直接启动 F10 | 业务推进快 | 绕过 F09 production-readiness 缺口与两个 sanity 失败；把下一卡授权建立在不完整治理基线上 | `REJECT FOR G10` |
| B | 只修两个非 F09 sanity 失败 | 可快速恢复全仓表面绿 | 不能回答 F09 production-readiness；容易把“全仓绿”误作生产就绪 | `INSUFFICIENT ALONE` |
| C | F09 production-readiness admission + 两个 sanity 失败独立分账 + F10 Go/Hold 决策 | 证据链完整，避免跨域归因与过早扩张 | 需要严格 Gate 和 owner 分离 | **`SELECTED`** |
| D | 立即宣称 F09 production ready | 无额外成本 | 违反既有 non-inference boundaries；无部署/运行环境/全仓证据 | `FORBIDDEN` |

## 4. G10 分阶段 Gate

| Gate | 名称 | 目标 | 进入条件 | 完成条件 | 初始状态 |
|---|---|---|---|---|---|
| G10.0 | RECOVER / baseline lock | 恢复 Task 9-P、G6–G9、全仓 sanity 与禁止边界 | G10 计划获准启动 | 权威源、证据时点、写集、命令范围、保护对象和唯一下一动作被记录 | `NOT STARTED` |
| G10.1 | Production-readiness INVENTORY | 列出 F09 从有界切片到 production-readiness 的全部候选缺口 | G10.0 PASS | 每个缺口有 owner、证据、风险、是否材料性和所需 Gate；不选择实现方案 | `NOT STARTED` |
| G10.2 | Sanity failure triage | 对两个非 F09 失败分别做只读根因与归属判定 | G10.0 PASS；独立于 G10.1 | 两个失败各有复现状态、owner、最小修复候选、回归范围和“不得归因 F09”边界 | `NOT STARTED` |
| G10.3 | Admission selection | 从 G10.1/G10.2 选择唯一可实施单元或明确 HOLD | G10.1、G10.2 均完成 | 依赖、兼容、最小写集、STOP 条件和 retained decision 闭合 | `NOT STARTED` |
| G10.4 | Frozen governance contract | 为被选单元冻结合同 | G10.3 PASS | 目标/非目标、精确写集、精确验证 selectors、静态审查项、failure routing、non-inference 全部无歧义 | `NOT STARTED` |
| G10.5 | Authorized implementation | 仅执行 G10.4 冻结的最小本地修复或证据工作 | G10.4 fresh PASS 且获得该单元独立授权 | 修改范围与合同一致；不声明行为 PASS | `NOT STARTED` |
| G10.6 | Fresh STATIC_REVIEW | 独立检查范围、结构、语义和远端副作用 | G10.5 完成 | High/Medium=0，或返回精确 REVISE/BLOCKED | `NOT STARTED` |
| G10.7 | Exact VERIFY | 运行合同规定的必要最小命令 | G10.6 PASS | 完整记录命令、cwd、exit、计数、耗时、失败历史和参数化 reconciliation | `NOT STARTED` |
| G10.8 | Fresh EVIDENCE_REVIEW | 判断是否允许有界冻结 | G10.7 有效证据 | 独立给出 PASS/REVISE/BLOCKED 和直接证明/未证明 | `NOT STARTED` |
| G10.9 | Freeze / closeout | 汇总 F09 readiness admission 与 sanity workstream | 所有被选单元 frozen 或精确 blocked | 唯一 G10 裁决、剩余缺口和恢复 handoff 持久化 | `NOT STARTED` |
| G10.10 | F10 Go/Hold/Reject | 决定下一张卡是否允许进入设计/准入 | G10.9 完成 | 形成 `GO TO F10 ADMISSION`、`HOLD` 或 `REJECT` 三选一；不自动实现 | `NOT STARTED` |

## 5. 工作流 A：F09 production-readiness admission

### 5.1 必须盘点的证据域

G10.1 至少逐项回答：

1. **行为范围**：F09 已执行 selectors 覆盖什么，哪些未执行；
2. **全仓兼容**：两个非 F09 失败是否与 F09 无因果关系，是否还有未发现的集成风险；
3. **skipped 场景**：6 个 skipped 的原因、owner、是否属于材料性 readiness 缺口；
4. **配置与默认值**：opt-in、production-default、staged/preprod 分账是否满足预期运行边界；
5. **持久化与恢复**：artifact/feedback/current-run authority 的失败恢复、重试和幂等边界是否有足够证据；
6. **运行环境**：依赖、密钥/registry provisioning、环境配置、文件权限和外部服务是否属于仓库内可验证范围；
7. **观测性**：日志、审计轨迹、错误表面与 operator diagnosis 是否达到准入要求；
8. **性能与资源**：是否存在明确 SLO、基准和限额；无合同则记录 UNKNOWN，不自行创造指标；
9. **安全与信任边界**：只引用既有契约；缺失时建立候选，不在盘点阶段补写规则；
10. **回滚与故障隔离**：production-default 不变、opt-in 撤回路径和数据兼容边界；
11. **版本与 provenance**：本地证据与版本状态如何绑定；本任务禁止 Git，故 provenance 如需 Git 证据必须标记为本控制流程外的未满足项，不能伪造；
12. **部署/发布**：属于外部能力，不得由本地测试替代。

### 5.2 Readiness 状态模型

每个候选缺口只能取：

- `PROVEN`：有当前、范围匹配的直接证据；
- `NOT_REQUIRED`：由冻结合同明确排除；
- `REQUIRES_LOCAL_GATE`：可由后续本地合同/实现/验证闭合；
- `REQUIRES_EXTERNAL_DECISION`：需要用户业务决策、凭据或环境；
- `BLOCKED_BY_PROHIBITION`：需要 GitHub mutation 或其他永久禁止操作；
- `UNKNOWN`：权威事实不足，禁止猜测。

`PROVEN + NOT_REQUIRED` 的简单计数不得自动推出 production ready；必须由 G10.8 独立 EVIDENCE_REVIEW 按材料性裁决。

## 6. 工作流 B：两个非 F09 sanity 失败

### 6.1 已知失败登记

来自 [`production-implementation-control.md`](production-implementation-control.md) §8.5 的既有账本：

1. [`test_witness_trust_boundary_is_explicitly_documented()`](../tests/evaluation/test_dataset.py:256)：要求 [`../tools/README.md`](../tools/README.md) 存在 witness trust-boundary 文案；
2. [`test_handoff_names_first_legal_case_action_and_all_independent_holds()`](../tests/evaluation/test_prospective_gate_workflow.py:343)：要求 [`../handoff.md`](../handoff.md) 存在 prospective 首案与 HOLD 文案。

该记录是历史 observed failure，不是 G10 fresh reproduction。G10.2 若获精确命令授权，应先分别运行两个 selector，不直接运行全仓；collection error 为零行为证据。

### 6.2 分账规则

- 两个失败必须分别建 ledger，不允许一个修复同时被默认为另一个 PASS；
- 不得修改 F09 runtime/tests 处理这两个失败；
- 不得为了测试绿而在事实源中写入虚假状态；
- [`../handoff.md`](../handoff.md) 不是长期事实源，若其测试要求与当前事实源纪律冲突，必须返回 CONTRACT/NEEDS_DECISION，不得强行补文案；
- [`../tools/README.md`](../tools/README.md) 是工具索引，其 witness 文案必须有对应权威语义来源，不能凭测试字符串臆造；
- 修复后必须先 fresh STATIC_REVIEW，再精确重跑各自 selector；是否再跑全仓由独立合同决定；
- 即使两项均 PASS，也只能证明对应 sanity selectors，不自动证明 F09 production readiness 或全仓正确性。

## 7. 工作流 C：F10 启动决策包

### 7.1 Go 条件

只有同时满足以下条件，G10.10 才可裁决 `GO TO F10 ADMISSION`：

1. G10.9 已形成完整 closeout；
2. F09 readiness 的材料性本地缺口已冻结或精确 blocked；
3. 两个 sanity 失败已分别 frozen、明确 non-material，或有用户接受的 HOLD；
4. 没有把 Git/GitHub、部署或外部环境证据伪装成本地 PASS；
5. F10 的业务目标、owner 和依赖可由现有冻结事实唯一确定；
6. Go 只授权进入 F10 INVENTORY/ADMISSION，不授权实现。

### 7.2 Hold 条件

出现以下任一情况应裁决 `HOLD`：

- readiness 缺口需要真正业务优先级决策；
- 需要不可用凭据、部署环境或外部 capability；
- 两个 sanity 失败暴露事实源/测试契约冲突；
- F10 目标存在多个材料性不同选项且无法从权威源唯一选择；
- 当前证据时效或完整性不足，但问题可通过后续合法动作解除。

### 7.3 Reject 条件

出现以下任一情况应裁决 `REJECT`：

- F10 与冻结 F01–F12 语义冲突且无正式变更流程；
- 需要 GitHub mutation 才能继续本控制流程；
- 目标要求绕过 evidence Gate、删除失败历史或把局部 PASS 外推为项目完成；
- 目标本身已被现有能力覆盖，新增实现违反 YAGNI。

## 8. 初始授权矩阵与保护对象

本计划本身不授予后续执行权限。G10 启动时必须重新冻结最小授权矩阵：

| Capability | G10 启动时要求 |
|---|---|
| read | 精确列出权威文件、两个失败对应测试文件及必要 owner 文件；排除历史 handoff 推断 |
| modify | 每个独立单元单独列出精确文件；默认无 |
| command/test | 完整命令、cwd、selector、超时、side-effect boundary、rerun 条件 |
| local Git | **禁止**；本任务用户明确禁止所有 Git 命令 |
| GitHub/remote | **禁止**；不读不写，不尝试一次验证 |
| handoff write | 仅写当轮获准的 G10 控制/裁决文件，不创建竞争事实源 |

持续保护：

- F09 已冻结源码、测试和九份 Task 9-P 专项文件；
- G6–G9 与 Task 9-P 的历史裁决和失败账本；
- 用户拥有的本地改动；
- 所有凭据、远端配置和外部服务状态。

## 9. STOP 条件与 failure routing

遇到以下情况立即停止当前单元并分类：

- 拟议动作可能触达 Git/GitHub、网络发布或远端状态：`BLOCKED`；
- owner 或事实源冲突：返回 `CONTRACT GAP`，不得自行选择；
- selector 不唯一：停止并做最小 disambiguation；
- collection error：记录为零行为证据，不修复后直接扩大重跑；
- 测试失败：区分 product defect、test defect、contract gap、environment/tool failure；
- 修改超出冻结 write set：停止并废止后续授权；
- 修复后旧 STATIC_REVIEW/VERIFY 自动失效，必须 fresh review 与 exact rerun；
- 发现 F09 之外的改进候选：登记但不顺手修复。

## 10. G10 验证账本最低字段

任何后续 VERIFY 必须逐命令记录：

- 完整命令；
- working directory；
- 执行时间；
- exit code；
- collected / passed / failed / errors / skipped / xfail / xpass；
- 耗时；
- selector 与静态实例 reconciliation；
- 首次失败、修复、stale evidence 与 rerun 历史；
- 直接证明；
- 明确未证明；
- GitHub side-effect screening。

没有完整账本不得冻结。工具报告“写入成功”只证明写工具成功，不证明内容正确。

## 11. G10 最终裁决枚举

G10.9 只能给出一个：

- `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`；
- `REVISE — LOCAL GOVERNANCE GAP`；
- `BLOCKED — MATERIAL READINESS GAP`；
- `AUTHORIZATION_REQUIRED — RETAINED BUSINESS DECISION`。

随后 G10.10 只能给出一个：

- `GO TO F10 ADMISSION`；
- `HOLD F10`；
- `REJECT F10`。

两个裁决必须分开：G10 PASS 不自动等于 F10 Go，F10 Go 也只允许进入准入，不允许实现。

## 12. Non-inference boundaries

本计划不得用于推导：

- G10 已启动、已实现、已验证或已完成；
- F09 production ready；
- 两个非 F09 sanity 失败已复现、已归因或已修复；
- 全仓测试当前计数仍与 2026-07-26 相同；
- 全仓绿、6 个 skipped 已通过或所有未执行场景正确；
- F10 已获准启动或实现；
- production-default 可以改变；
- F01–F12 冻结语义可以重开；
- Task 9-P PASS 自动继承为 G10/F10 的合同、实现或验证授权；
- 部署、发布、性能、安全、生产环境、Git provenance 或远端同步已证明；
- GitHub 整体未变化、已同步或存在任何 PR/Issue/Release 状态。

## 13. 唯一下一合法动作

本任务内 G10 保持 `PLANNED / NOT STARTED`，不得继续实现。

后续若用户另行启动 G10，唯一首动作是：

> **执行 G10.0 RECOVER / baseline lock：重新读取届时权威状态，确认 Task 9-P/G6–G9 冻结边界、两个 sanity failure 的当前性、精确写集、禁止操作与唯一下一 Gate；不得直接修复、跑全仓或启动 F10。**

精确状态标记：

> **`LOCAL ONLY / NOT PUSHED / NO GITHUB MUTATION`**
