# as-of 后 2026-07-18 方向对齐审计

> 审计日期：2026-07-29（Asia/Shanghai）
> 审计性质：只读审计，不修改 `plans/`、`reports/`、`cases/`、`engine/`、`tools/` 下任何现有文件；本文件是本次审计唯一允许创建的新文件。
> 审计对象：2026-07-18 之后全部 as-of 相关 `plans/*.md`、`reports/*.md`、`engine/asof/*.py`、`cases/*/asof-*.json`
> 唯一方向基准：[`plans/as-of-life-state-reasoning-design-2026-07-18.md`](../plans/as-of-life-state-reasoning-design-2026-07-18.md)
> 时间口径（已与用户确认）：2026-07-19 至 07-26 期间的工作，若服务静态生成器而未建设 as-of 闭环，标为"方向偏离"；但因当时尚无 07-27 的显式优先级锁定禁令，不追溯认定其"违规"。2026-07-27 起才适用第 7 行显式禁令。

---

## 1. 核心文档检查清单（比对基准）

从 [`plans/as-of-life-state-reasoning-design-2026-07-18.md`](../plans/as-of-life-state-reasoning-design-2026-07-18.md) 提炼：

### 1.1 六条推理宪法（§3）

| 编号 | 原则 | 出处 |
|---|---|---|
| 3.1 | 原局是承载结构，不直接等于截止日现实结果 | [§3.1](../plans/as-of-life-state-reasoning-design-2026-07-18.md:47) |
| 3.2 | 大运是阶段上下文，定义路径开放/受阻/放大/抑制/修复/改道 | [§3.2](../plans/as-of-life-state-reasoning-design-2026-07-18.md:51) |
| 3.3 | 流年是动态触发器；命理结构轨×现实状态轨双轨约束，非数值乘法 | [§3.3](../plans/as-of-life-state-reasoning-design-2026-07-18.md:55) |
| 3.4 | 关键流年事件是状态转移入口，核验后依类型/影响度/持续时间/领域/根源性改变状态 | [§3.4](../plans/as-of-life-state-reasoning-design-2026-07-18.md:74) |
| 3.5 | 受约束的路径依赖：强/弱/无根源三级区分，原局根源性不得推翻已核验现实事实 | [§3.5](../plans/as-of-life-state-reasoning-design-2026-07-18.md:78) |
| 3.6 | 截止状态是历史轨迹归并结果：原局+大运+流年+已核验事件后果=截止日状态 | [§3.6](../plans/as-of-life-state-reasoning-design-2026-07-18.md:90) |

### 1.2 七个关键数据对象及必需字段（§5）

| 对象 | 必需信息/约束 | 出处 |
|---|---|---|
| `NatalCapacityGraph` | 领域能力与容量；主要结构与脆弱点；可行路径与限制；命理事实；原始语料；竞争解释与反证 | [§5.1](../plans/as-of-life-state-reasoning-design-2026-07-18.md:135) |
| `DaiyunContext` | 时间范围；路径开放/关闭/放大/抑制/修复/改道；与原局节点的有效关系；领域阶段倾向；适用条件与反证 | [§5.2](../plans/as-of-life-state-reasoning-design-2026-07-18.md:148) |
| `AnnualInteractionTrace` | 流年×大运×原局关系；被发动节点；领域；支持与反证；命理触发强度；是否越过事件候选证据门；触发强度不得直映现实影响度 | [§5.3](../plans/as-of-life-state-reasoning-design-2026-07-18.md:160) |
| `LifeEventCandidate` | 领域、类型、时间窗；原局/大运/流年链；根源及证据；支持/反证/替代假设；冻结版本；核验状态；系统建议影响；人工裁决；状态与路径变化；状态至少含 CANDIDATE/FROZEN/PARTIAL_HIT/CONFIRMED/REJECTED/UNKNOWN/WITHHELD | [§5.4](../plans/as-of-life-state-reasoning-design-2026-07-18.md:175) |
| `EventImpactAssessment` | 系统建议与人工最终裁决各自保留 impact/persistence/scope，另含 adjustment_reason；人工不得覆盖冻结建议 | [§5.5](../plans/as-of-life-state-reasoning-design-2026-07-18.md:203) |
| `VerifiedState` | 仅接受排盘确定信息、已核验事件、有证据裁决、截止日仍有效的持续状态和路径改变 | [§5.6](../plans/as-of-life-state-reasoning-design-2026-07-18.md:221) |
| `HypothesisState` | 不混入事实快照；每分支必须有成立条件、与事实主线差异、会改变的基本面/后运、最小消歧问题、反证条件 | [§5.7](../plans/as-of-life-state-reasoning-design-2026-07-18.md:232) |

### 1.3 四级现实影响度与双证据门

四级影响度：轻微/显著/重大/转折性（[§6.1](../plans/as-of-life-state-reasoning-design-2026-07-18.md:246)）；功能根源双证据门：命盘结构证据 + 原始语料证据同时满足（[§6.4](../plans/as-of-life-state-reasoning-design-2026-07-18.md:285)）。

### 1.4 优先级锁定五项禁止任务（第7行，2026-07-27 生效）

[`plans/as-of-life-state-reasoning-design-2026-07-18.md:7`](../plans/as-of-life-state-reasoning-design-2026-07-18.md:7) 明确列出五项必须排在 as-of 求测闭环之后的任务：

1. F10 启动决策包收尾
2. 多专家功能域主裁判路由 promotion
3. v1.4 V7 报告模板默认切换
4. 子平/滴天髓生产规则扩充
5. 八字指纹相似案检索

---

## 2. 时间线：07-18 之后全部 as-of 相关文档

标注含义：**对齐**＝直接建设或验证“原局—大运—流年—截止状态”；**偏离**＝资源投向其他局部优化，或在锁定生效后触碰五项禁止任务；**中性执行载体**＝合同、提示词、裁决、验收记录，本身不决定方向，按其服务目标判定。

### 2.1 `plans/`：as-of 主线

| 时间 | 文档（同一任务的合同、规格、提示词合并列示） | 性质 | 判定 | 审计理由 |
|---|---|---|---|---|
| 07-18 | [`as-of-life-state-reasoning-design-2026-07-18.md`](../plans/as-of-life-state-reasoning-design-2026-07-18.md) | 核心设计 | 基准 | 唯一方向基准。 |
| 07-26 | [`as-of-life-state-g0-g5-execution-plan-for-terra.md`](../plans/as-of-life-state-g0-g5-execution-plan-for-terra.md)、[`as-of-life-state-g0-g5-terra-kickoff-prompt.md`](../plans/as-of-life-state-g0-g5-terra-kickoff-prompt.md)、[`as-of-life-state-prototype-spec.md`](../plans/as-of-life-state-prototype-spec.md) | 计划、提示词、规格 | **对齐** | 建立七对象的首个事业/财富切片，落实双轨、根源、状态归并与弃权。 |
| 07-26～27 | [`as-of-life-state-g6-out-of-sample-case-spec.md`](../plans/as-of-life-state-g6-out-of-sample-case-spec.md)、[`as-of-life-state-g6-out-of-sample-validation-kickoff-prompt.md`](../plans/as-of-life-state-g6-out-of-sample-validation-kickoff-prompt.md) | 规格、提示词 | **对齐** | 明确只做样本外回放，不扩展新域或新规则；提示词直接指定核心文档为唯一业务事实源（第10、25行）。 |
| 07-26～27 | [`as-of-life-state-g7-larger-sample-case-spec.md`](../plans/as-of-life-state-g7-larger-sample-case-spec.md)、[`as-of-life-state-g7-larger-sample-validation-kickoff-prompt.md`](../plans/as-of-life-state-g7-larger-sample-validation-kickoff-prompt.md) | 规格、提示词 | **对齐** | 扩至更多真实案例，保持冻结接口。 |
| 07-26～27 | [`as-of-life-state-g8-production-integration-spec.md`](../plans/as-of-life-state-g8-production-integration-spec.md) | 集成规格 | **对齐** | 薄接线，不改变 as-of 语义。 |
| 07-27 | [`as-of-life-state-g9-production-promotion-scope-adjudication.md`](../plans/as-of-life-state-g9-production-promotion-scope-adjudication.md)、[`as-of-life-state-g9-p1-production-cli-alias-contract.md`](../plans/as-of-life-state-g9-p1-production-cli-alias-contract.md)、[`as-of-life-state-g9-p1-terra-kickoff-prompt.md`](../plans/as-of-life-state-g9-p1-terra-kickoff-prompt.md) | 裁决、合同、提示词 | **对齐** | 只授权保守 CLI 别名，没有把 staged 验证夸大为生产默认。 |
| 07-28 | [`as-of-life-state-unit8-real-case-blind-verification-contract.md`](../plans/as-of-life-state-unit8-real-case-blind-verification-contract.md)、[`as-of-life-state-unit8-real-case-blind-verification-terra-kickoff-prompt.md`](../plans/as-of-life-state-unit8-real-case-blind-verification-terra-kickoff-prompt.md) | 合同、提示词 | **对齐** | 验证真实案例 session 流程。 |
| 07-28 | [`as-of-life-state-unit9-real-case-future-projection-contract.md`](../plans/as-of-life-state-unit9-real-case-future-projection-contract.md) | 合同 | **对齐但不完整** | 推进未来投影，但仍未补齐逐年确定性应期链。 |
| 07-28 | [`as-of-life-state-unit10-real-case-explicit-wealth-propagation-contract.md`](../plans/as-of-life-state-unit10-real-case-explicit-wealth-propagation-contract.md) | 合同 | **对齐** | 验证财富影响传播。 |
| 07-28 | [`as-of-life-state-unit11-real-case-session-productization-contract.md`](../plans/as-of-life-state-unit11-real-case-session-productization-contract.md) | 合同 | **对齐** | 会话制品化，仍为手动旁路。 |
| 07-28 | [`as-of-life-state-blind-judgment-first-proof-point-contract.md`](../plans/as-of-life-state-blind-judgment-first-proof-point-contract.md)、[`as-of-life-state-blind-judgment-first-proof-point-kickoff-prompt.md`](../plans/as-of-life-state-blind-judgment-first-proof-point-kickoff-prompt.md) | 合同、提示词 | **对齐** | 第一次真正执行“先冻结、后开反馈”。 |
| 07-28 | [`as-of-life-state-blind-judgment-batch-verification-kickoff-prompt.md`](../plans/as-of-life-state-blind-judgment-batch-verification-kickoff-prompt.md) | 提示词 | **对齐** | 明确 First Proof Point 为 0/1，并把 N=3～5 扩样作为最小必要后续（第7～12、26～29行）。 |
| 07-28～29 | [`as-of-life-state-next-task-geju-adjudication-2026-07-28.md`](../plans/as-of-life-state-next-task-geju-adjudication-2026-07-28.md)、[`as-of-life-state-next-task-geju-adjudication-2026-07-29.md`](../plans/as-of-life-state-next-task-geju-adjudication-2026-07-29.md) | 方向裁决 | **对齐** | 拒绝低杠杆扩域/无目标 F10，优先补真实盲断证据。 |
| 07-29 | [`as-of-life-state-blind-judgment-n5-extension-contract.md`](../plans/as-of-life-state-blind-judgment-n5-extension-contract.md) | 合同 | **对齐** | 扩样至 N=5。 |
| 07-29 | [`as-of-life-state-blind-judgment-n50-extension-contract-2026-07-29.md`](../plans/as-of-life-state-blind-judgment-n50-extension-contract-2026-07-29.md)、[`as-of-life-state-blind-judgment-n50-extension-and-geju-kickoff-prompt.md`](../plans/as-of-life-state-blind-judgment-n50-extension-and-geju-kickoff-prompt.md) | 合同、提示词 | **对齐但目标过大** | 方向正确；单会话 N=50 与真实逐案判读产能不匹配。 |
| 07-29 | [`as-of-life-state-blind-judgment-probe-table-annotation-detection-contract.md`](../plans/as-of-life-state-blind-judgment-probe-table-annotation-detection-contract.md) | 工具合同 | 中性（目标对齐） | 防止阶段一读取表格内嵌真实事实。 |
| 07-29 | [`as-of-life-state-blind-judgment-multi-round-continuous-expansion-kickoff-prompt.md`](../plans/as-of-life-state-blind-judgment-multi-round-continuous-expansion-kickoff-prompt.md) | 提示词 | **对齐** | 多轮持续扩样载体。 |

### 2.2 `reports/`：as-of 主线

| 时间 | 报告 | 判定 | 关键结论 |
|---|---|---|---|
| 07-26 | [`as-of-life-state-reasoning-audit-2026-07-26.md`](as-of-life-state-reasoning-audit-2026-07-26.md) | **对齐** | 诚实报告 as-of 对象尚未形成完整生产链，并区分 F09 与 as-of。 |
| 07-26 | [`as-of-life-state-career-wealth-slice-g0-g5-verification.md`](as-of-life-state-career-wealth-slice-g0-g5-verification.md) | **对齐** | 首个单案原型证据冻结；证明结构和治理，不证明准确率。 |
| 07-26～27 | [`as-of-life-state-g6-out-of-sample-validation-report.md`](as-of-life-state-g6-out-of-sample-validation-report.md)、[`as-of-life-state-g7-larger-sample-validation-report.md`](as-of-life-state-g7-larger-sample-validation-report.md) | **对齐但证据弱** | 是已知反馈下的回放验证，不是真盲断准确率证据。 |
| 07-26～27 | [`as-of-life-state-g8-production-integration-report.md`](as-of-life-state-g8-production-integration-report.md)、[`as-of-life-state-g9-p1-production-cli-alias-report.md`](as-of-life-state-g9-p1-production-cli-alias-report.md) | **对齐** | 接入与 CLI 证据，不证明命理判断质量。 |
| 07-28 | [`as-of-life-state-unit8-real-case-blind-verification-report.md`](as-of-life-state-unit8-real-case-blind-verification-report.md)、[`as-of-life-state-unit9-real-case-future-projection-report.md`](as-of-life-state-unit9-real-case-future-projection-report.md)、[`as-of-life-state-unit10-real-case-explicit-wealth-propagation-report.md`](as-of-life-state-unit10-real-case-explicit-wealth-propagation-report.md)、[`as-of-life-state-unit11-second-case-session-productization-report.md`](as-of-life-state-unit11-second-case-session-productization-report.md) | **对齐但不完整** | 加强 session、投影、财富传播和制品化；没有消除职业宽泛化、窗口宽泛化和应期未接入问题。 |
| 07-28 | [`as-of-life-state-blind-judgment-first-proof-point-report.md`](as-of-life-state-blind-judgment-first-proof-point-report.md) | **对齐** | N=1，0 命中、1 失验；第14～27行列出此前 8 个回放/验证案例，但这些不属于同口径真盲断。 |
| 07-28 | [`as-of-life-state-blind-judgment-batch-report.md`](as-of-life-state-blind-judgment-batch-report.md) | **对齐** | N=3 批次，2/3；暴露污染检测和候选准入问题。 |
| 07-29 | [`as-of-life-state-blind-judgment-n5-extension-report.md`](as-of-life-state-blind-judgment-n5-extension-report.md) | **对齐** | 报告第7行写明上游 N=3、2/3；扩至累计 N=5。 |
| 07-29 | [`as-of-life-state-blind-judgment-n50-extension-report.md`](as-of-life-state-blind-judgment-n50-extension-report.md) | **对齐，BLOCKED** | R1 因 Windows 批量命令载体失败，未把技术失败伪装成业务结论。 |
| 07-29 | [`as-of-life-state-blind-judgment-n50-extension-report-r2.md`](as-of-life-state-blind-judgment-n50-extension-report-r2.md) | **对齐但暴露瓶颈** | 新触碰 6 案、有效 3 案，累计 N=8、5/8；第15～19行明确真正瓶颈是逐案判读产能。 |
| 07-29 | [`as-of-life-state-blind-judgment-continuous-extension-r1-report.md`](as-of-life-state-blind-judgment-continuous-extension-r1-report.md) | **对齐** | RF000190 无效；RF000243 `MISS`；累计 5/9（第117～125、161～163行）。 |
| 07-29 | [`as-of-life-state-blind-judgment-continuous-extension-r2-report.md`](as-of-life-state-blind-judgment-continuous-extension-r2-report.md) | **对齐** | RF000244 `MISS`；累计 5/10（第125～133、169～171行）。 |
| 07-29 | [`as-of-life-state-blind-judgment-continuous-extension-r3-report.md`](as-of-life-state-blind-judgment-continuous-extension-r3-report.md) | **对齐** | RF000249 `CENTER_HIT`；累计 6/11（第157～167、228～230行）。 |
| 07-29 | [`as-of-life-state-blind-judgment-continuous-extension-r4-report.md`](as-of-life-state-blind-judgment-continuous-extension-r4-report.md) | **对齐且关键纠偏** | RF000281 表面中心命中，但 fresh review 发现 2018 壬申运事实不能核验 2025 辛未运候选，裁为跨阶段 `BLOCKED`（第88～98行）。 |
| 07-29 | [`as-of-life-state-blind-judgment-continuous-extension-r5-report.md`](as-of-life-state-blind-judgment-continuous-extension-r5-report.md) | **对齐且开始修复窗口** | RF000284 把窗口收窄为 2025 单年，反馈仅有 2021 事实，诚实记无效（第69～72、192～208行）。 |
| 07-29 | [`as-of-life-state-blind-judgment-continuous-extension-r6-report.md`](as-of-life-state-blind-judgment-continuous-extension-r6-report.md) | **对齐** | RF000286 固定 2021 单年；反馈粒度不足，不跨年追认，记无效（第73～76、229～247行）。 |
| 07-29 | [`as-of-life-state-blind-judgment-continuous-extension-r7-report.md`](as-of-life-state-blind-judgment-continuous-extension-r7-report.md) | **对齐但落点仍偏宽** | RF000287 固定 2025 单年；“岗位/平台/团队/职责/权限”多选闭集仍宽；反馈无当年事实，记无效（第75～98、207～233行）。 |
| 07-29 | [`as-of-life-state-blind-judgment-continuous-extension-r8-report.md`](as-of-life-state-blind-judgment-continuous-extension-r8-report.md) | **对齐** | RF000301 固定 2024 单年；反馈无窗口事实，记无效；累计保持 6/11（第42～46、218～234行）。 |
| 07-29 | [`as-of-life-state-blind-judgment-root-cause-report.md`](as-of-life-state-blind-judgment-root-cause-report.md) | **对齐且重要修复，但尚未接入** | 复核 8 案为 2 CENTER/3 ALTERNATIVE/3 MISS；发现强度系统性偏乐观、双证据门未执行、理论库零接入；新增工具仍未进入真实流程（第24～48、125～140、166～170行）。 |
| 07-29 | [`as-of-fresh-cohort-validation-2026-07-29.md`](as-of-fresh-cohort-validation-2026-07-29.md) | **对齐且揭示重大缺口** | RF000894/900/868 新鲜冻结验证，暴露现实完成度过断、职业中心过宽、应期证据薄弱。 |

### 2.3 非 as-of 轨道与五项禁令污染

| 轨道 | 时间关系 | 判定 | 证据 |
|---|---|---|---|
| `production-implementation-pi-*`、`g6-task*`、F09 | 07-19～27 | **方向偏离但多数不追溯判违规** | [`production-implementation-control.md`](../plans/production-implementation-control.md:1) 第3～7行显示该 F01～F12 生产实现轨道建立于 07-19；目标是冻结证据卡接入（第24～47行），不是 as-of 四层状态链。它消耗大量治理产能，但 07-19～26 尚无 07-27 显式禁令。 |
| G10 治理 | 07-27 | **中性，未实质启动 F10** | [`g10-next-governance-milestone-plan.md`](../plans/g10-next-governance-milestone-plan.md:9) 第11～17行要求先做 F09 readiness、再决定 F10；第48行将“直接启动 F10”裁为 `REJECT FOR G10`。[`production-implementation-control.md`](../plans/production-implementation-control.md:326) 第328～330行最终为 `HOLD F10`。 |
| 多专家反馈权重 promotion Phase 1～3 | 截止 07-27 已执行 | **偏离；高严重度；明确命中禁止项 #2** | [`parallel-domain-feedback-loop-phase1-terra-kickoff-prompt.md`](../plans/parallel-domain-feedback-loop-phase1-terra-kickoff-prompt.md:34) 第36～46行要求接通反馈→调权提案→人工 promotion→写回专家权重；[`parallel-domain-feedback-loop-phase3-registry-closure-report.md`](parallel-domain-feedback-loop-phase3-registry-closure-report.md:1) 第3行记录执行日期 07-27。该目标与核心文档第7行“多专家功能域主裁判路由 promotion”同义。 |
| V7 报告模板默认切换 | 07-18 后未发现实施 | **未污染** | [`META/project-state.json`](../META/project-state.json:23) 第30行仍为 `partial_template_exists_default_not_switched`。 |
| 子平/滴天髓生产规则扩充 | 早于核心文档 | **不属本审计期违规** | [`META/progress-report-2026-06-09.md`](../META/progress-report-2026-06-09.md:19) 第20、28行已记为 landed，说明不是 07-18 后新增。 |
| 八字指纹相似案检索 | 07-18 后未发现新 as-of 相关推进证据 | **未污染** | 仓库存在既有 [`similarity.py`](../engine/v2/similarity.py)，但未发现审计期内用它替代真盲断或作为 as-of 优先任务的计划/报告。 |

**时间线总判定**：as-of 命名主线总体对齐；真正的资源偏离主要来自 F09 大型治理轨道（方向不直接对齐，但多数发生在显式锁定之前）以及 07-27 仍完成的多专家 feedback promotion（明确触碰禁止项）。

---
## 3. 具体偏离证据

### 3.1 偏离 A：职业中心落点宽泛化（高严重度）

三份最新冻结案确实存在用户指出的问题。以 RF000894 为例，冻结内容写成：

> “数据/信息处理、分析判断、技术方法、研究策划、流程质量或复杂问题解决之一”

证据见 [`RF000894/asof-blind-freeze.json`](../cases/C-2026-RF000894-乾-壬戌己酉庚子戊子/asof-blind-freeze.json:47)。这不是一个可证伪的“职业中心”，而是同时覆盖数据、分析、技术、研究、策划、流程、质量、复杂问题解决，近乎囊括全部非体力知识工作；RF000868 也采用“技术、信息处理、数据分析、系统流程、方案设计、工程实施、研究判断或复杂问题解决之一”（[`RF000868/asof-blind-freeze.json`](../cases/C-2026-RF000868-乾-壬申戊申庚辰丁亥/asof-blind-freeze.json:47)）。

RF000900 与 RF000868 也使用同构的多选宽口径。它导致两个后果：

1. **命中分母被人为放大**：只要反馈是常见知识工作，就可能落入其中一个“或”分支。
2. **根源性裁决失去区分度**：`STRONG_ROOT`/`WEAK_ROOT` 原本要约束“何种现实功能可完成”，宽口径把根源裁决退化为标签兼容。

历史来源判断：

- G0～G7 的主要目标是验证对象、门禁和状态归并，并未建立严格职业中心评分合同；因此宽泛化风险从原型期就**未被消除**。
- 真盲断早期并非一开始都如此宽。N5 报告中的 RF000121 冻结中心为“体制内执行/纪律型岗位（如军警、监管、一线执法）的正式任职与深化”，反馈为“武职”，属于较窄、可证伪落点（[`as-of-life-state-blind-judgment-n5-extension-report.md`](as-of-life-state-blind-judgment-n5-extension-report.md:25)，第33～44行）。
- 到 N50-R2，报告已承认每案“落点集合设计”是人工判读步骤（[`as-of-life-state-blind-judgment-n50-extension-report-r2.md`](as-of-life-state-blind-judgment-n50-extension-report-r2.md:15)，第17～19行），但没有引入“中心落点最大语义宽度”或“互斥类别数”约束。
- 最新 fresh cohort 才把宽泛化推到明确可见的极端。因此，**可确认的问题起点不是某一轮代码回归，而是 G0 起一直缺少精度合同；明显恶化至少在 N50/最新 fresh cohort 的人工模板化落点集合阶段出现**。现有证据不足以把首次出现精确定位到某个更早文件日期，不能虚构“从 G6 开始”等未经证实结论。

与核心文档的冲突：表面上仍经过原局/大运/事件对象，但实质削弱 §3.5 的“受约束路径依赖”和 §6.4 双证据门，因为过宽落点不再受根源约束，也难被反证。

### 3.2 偏离 B：事件窗口 2～3 年 + 多选事件类型（高严重度）

RF000894 的冻结事件候选把一个窗口同时定义为：

> “换单位、换岗位、职责重组、项目/业务显著变化或职业稳定性重置”

证据见 [`RF000894/asof-blind-freeze.json`](../cases/C-2026-RF000894-乾-壬戌己酉庚子戊子/asof-blind-freeze.json:110)。这同时给了较长年份窗口和五类高基率职业事件，天然提高命中概率。

历史 G0～G9 的判断：

- 核心对象层支持 `year_window`，但 G0～G9 主要验证“候选能否过门”和“状态能否归并”，不是由算法生成的逐年应期识别。
- N5/N50 与连续扩展早期窗口并不统一：R2 的 RF000244 甚至使用 2021-01-01～2026-06-11 的五年多窗口（[`...continuous-extension-r2-report.md`](as-of-life-state-blind-judgment-continuous-extension-r2-report.md:51)，第55～61行）；R3 的 RF000249 使用 2016～2026 十年观察窗（[`...r3-report.md`](as-of-life-state-blind-judgment-continuous-extension-r3-report.md:52)，第55～63行）。
- R4 已实际发现宽观察窗掩盖跨大运阶段错配：2018 壬申运事实不能核验冻结的 2025 辛未运机制（[`...r4-report.md`](as-of-life-state-blind-judgment-continuous-extension-r4-report.md:86)，第88～98行）。
- R5～R8 随后把窗口收窄为单年，并拒绝用窗口外事实追认。这说明历史工作**已经触及并部分修复时间窗口问题**；但年度选择仍是人工冻结，不是 `scan_retrospective()` 生成，且 R7 仍以“岗位/平台/团队/职责/权限”多选闭集扩大事件语义（[`...r7-report.md`](as-of-life-state-blind-judgment-continuous-extension-r7-report.md:75)，第77～98行）。
- 因而准确结论是：**早期存在 3～10 年宽窗口；R4 识别问题、R5 起收窄单年；最新 fresh cohort 又回退到 2～3 年加多选事件类型。修复发生过，但未制度化为确定性应期链。**

与核心文档的冲突：核心 §3.3、§3.4 要求逐年动态触发与关键流年事件进入状态转移；“2～3年 × 多类型”只能证明一个阶段内可能有变化，不能证明“已过关键流年的具体触发”。这是对 §3.6 等式第三项的实质性欠实现。

### 3.3 偏离 C：应期规则存在，确定性算法也存在，但 as-of 没接入（关键架构缺口）

#### 3.3.1 理论规则不是不存在

[`theory/duan/index.yaml`](../theory/duan/index.yaml) 与 [`theory/gao/index.yaml`](../theory/gao/index.yaml) 已包含应期方法论，例如应期四大类系统化、冲合互补和流年优先级。最新冻结案的 `theory_evidence` 却只引用格局/调候定性规则，没有引用这些应期规则；RF000894 的引用区见 [`RF000894/asof-blind-freeze.json`](../cases/C-2026-RF000894-乾-壬戌己酉庚子戊子/asof-blind-freeze.json:137)，RF000868 的引用区见 [`RF000868/asof-blind-freeze.json`](../cases/C-2026-RF000868-乾-壬申戊申庚辰丁亥/asof-blind-freeze.json:137)。

#### 3.3.2 `engine/yingqi/retrospective.py` 已有确定性逐年扫描基础

核心文档 §4 已点名现有基础：[`FlowYearEnergy`](../engine/yingqi/retrospective.py:42)、[`RetrospectiveReport`](../engine/yingqi/retrospective.py:110)、[`scan_retrospective()`](../engine/yingqi/retrospective.py:282)。当前实现状态：

- [`FlowYearEnergy`](../engine/yingqi/retrospective.py:42) 表达单个流年的干支、能量、触发与解释。
- [`RetrospectiveReport`](../engine/yingqi/retrospective.py:110) 汇总起讫年、逐年结果与命中统计。
- [`scan_retrospective()`](../engine/yingqi/retrospective.py:282) 能按年份遍历并生成确定性回溯报告。

因此答案不是“未实现任何应期算法”，而是：**已有一套独立的 retrospective 确定性扫描器，但它没有成为 as-of 的 `AnnualInteractionTrace` 生产者。**

#### 3.3.3 `engine/asof/` 没有真正接线

搜索调用链未发现 `engine/asof/`、G6～G9 或 Unit8～11 调用 [`scan_retrospective()`](../engine/yingqi/retrospective.py:282)，也未发现把 [`FlowYearEnergy`](../engine/yingqi/retrospective.py:42) 转换成 `AnnualInteractionTrace` 的 adapter。最新冻结案例依赖人工填写 `frozen_event_candidates` 和人工 `theory_evidence`，因此绕过了 retrospective。

这解释了“为什么最近三案没有调用”：

1. G0 原型规格把 `AnnualInteractionTrace` 作为概念对象/有限字段实现，但未授权 yingqi 集成。
2. G6～G9 的任务被刻意限定为“零业务扩展”的样本外验证、薄集成和 CLI；[`as-of-life-state-g6-out-of-sample-validation-kickoff-prompt.md`](../plans/as-of-life-state-g6-out-of-sample-validation-kickoff-prompt.md:5) 第7行明确禁止扩展新裁决规则。
3. Unit8～11 继续做 session、投影、财富传播与制品化，没有单独设立“yingqi → AnnualInteractionTrace adapter”阶段。
4. 真盲断层只能由人工构造候选，遂出现宽窗口、多选事件型和只引格局规则。

所以该工作**在核心文档设计范围内（§4 明确点名），但从 G0 到 Unit11 都没做完**。这是当前最关键的技术方向缺口，不是可忽略的代码细节。

### 3.4 偏离 D：最新冻结案把“结构可能性”写成“现实完成度”（高严重度）

fresh cohort 报告已为此建立 `REALITY_COMPLETION_OVERCLAIM` 分类，说明历史工作的结构/现实双轨虽然在对象层存在，但人工冻结层仍可能越界：从原局格局和当前大运直接推成“已形成稳定职业中心”，没有足够已核验事件后果。

这直接违反：

- §3.1：原局不是现实结果；
- §3.3：命理结构轨不能替代现实状态轨；
- §3.5：现实事实约束结构解释；
- §3.6：截止状态必须包含已核验事件留下的持续后果。

这也是为什么“代码门禁通过”不能等于“方向完整对齐”：门禁约束对象和值域，但未约束自然语言落点是否过宽、是否越过现实证据。

### 3.5 偏离 E：五项禁止任务污染（1 个明确命中，2 个前置/边界问题）

| 项目 | 结论 | 严重度 |
|---|---|---|
| 多专家主裁判路由 promotion | 07-27 仍完成 Phase3 收口；目标与禁止项 #2 同义。虽然 Phase3 的直接写入只是工具登记和冻结收口，但它服务的 Phase1/2 目标正是专家权重 promotion。 | **高** |
| F10 | G10 做了启动决策包，但最终 `HOLD F10`；属于禁令边缘动作，未实质启动 F10。 | **低/边界** |
| F09 `production-implementation-pi-*` / `g6-task*` | 大量工作不建设 as-of；07-19～26 属方向资源错配，但不追溯判违反 07-27 禁令。 | **中** |
| V7 默认切换 | 未发生。 | 无 |
| 子平/滴天髓扩充 | 06-09 前已 landed，不属审计期。 | 无 |
| 指纹相似检索 | 未见审计期推进。 | 无 |

---

## 4. 历史验证案例全集与命中率趋势

### 4.1 案例全集：必须分口径

不能把“回放/集成案例”和“真盲断评分案例”混为同一分母。

#### A. G0～G9、Unit8～11 的已知反馈回放/产品化案例

First Proof Point 报告第16～27行明确列出 8 个此前使用案例（[`as-of-life-state-blind-judgment-first-proof-point-report.md`](as-of-life-state-blind-judgment-first-proof-point-report.md:16)）：

1. `C-2026-028-乾-壬戌癸卯壬子乙巳`（G0～G5）
2. `C-2026-024-坤-己巳壬申辛亥壬辰`（G6、Unit8、Unit9）
3. `C-2026-022-坤-癸亥庚申戊寅己未`（G6，跳过）
4. `C-2026-016-坤-甲子丙子丙戌戊子`（G7）
5. `C-2026-026-坤-癸未甲寅壬戌丙午`（G7）
6. `C-2026-027-乾-丁卯壬寅甲午乙丑`（G7）
7. `C-2026-RF000118-乾-己巳癸酉辛丑己丑`（Unit10、Unit11）
8. `C-2026-RF000475-坤-戊辰辛酉己巳乙丑`（Unit9）

这些案例用于回放、接口、状态归并或产品化，不构成可与后续盲断命中率合并的样本。

#### B. 真盲断闭环累计样本

- First Proof Point：`C-2026-002-坤-壬戌庚戌戊辰丙辰`，有效 N=1，失验。
- N=3 批次及 N5 扩样累计：报告列出的 RF000121、RF000123（无效）、RF000125，加上批次中的有效案例，共形成 N5 报告口径的有效 N=5。
- N50-R2 新触碰：RF000149、164、171、175、178、179；其中 149、164、179 为有效评分，171、175、178 无效（[`as-of-life-state-blind-judgment-n50-extension-report-r2.md`](as-of-life-state-blind-judgment-n50-extension-report-r2.md:25)，第28～35行）。
- 连续扩展 R1～R8 新触碰：RF000190、243、244、249、281、284、286、287、301；其中 RF000243/244 为 MISS、RF000249 为 CENTER_HIT，RF000281 为跨阶段 BLOCKED，其余为窗口事实不足无效。
- fresh cohort：RF000894、RF000900、RF000868，属于后续新鲜冻结审计/验证，应与连续扩展账本分列。

**可核实统计**：

- First Proof 报告确认此前 8 个回放/产品化案例；R8 库存报告确认截至其执行前已有 **22 个不同 RF 案例被历史盲断报告触碰**（[`...continuous-extension-r8-report.md`](as-of-life-state-blind-judgment-continuous-extension-r8-report.md:11)，第15～24行），R8 再新增 RF000301，故盲断轨道截至 R8 至少触碰 **23 个 RF 案例**。
- R8 后的 fresh cohort 再新增 RF000894、RF000900、RF000868 三案；此前 8 个回放/产品化案例中 RF000118、RF000475 已包含在 23 个 RF 历史触碰集内，另有 6 个非重叠普通 C 案；First Proof 的 C-2026-002 也不在 RF 集内。因此当前可核实去重保守下界为 **23 + 3 + 6 + 1 = 33 个案例**。这不是“有效评分 N”；它只统计曾被 as-of 回放、冻结、核验或产品化实际触碰的不同案例。
- 连续扩展的严格有效观察账本截至 R8 为 **N=11，命中或部分命中 6/11**；另有 9 个无效、1 个跨阶段 BLOCKED（[`...r8-report.md`](as-of-life-state-blind-judgment-continuous-extension-r8-report.md:218)，第222～234行）。
- 最新 fresh cohort 3 案使用更细的结构/现实/事件分项评分，不能直接强加进 6/11。

### 4.2 命中率历史趋势

| 轮次 | 有效 N | 命中/部分命中 | 失验 | 报告命中率 | 可比性与解读 |
|---|---:|---:|---:|---:|---|
| First Proof Point | 1 | 0 | 1 | 0% | 真盲断首次证明点；[`...first-proof-point-report.md`](as-of-life-state-blind-judgment-first-proof-point-report.md:8) 第10、14行给出 PASS 与案例，后续批次提示词第10行明确写 0/1。 |
| N=3 批次 | 3 | 2 | 1 | 66.7% | [`...n5-extension-report.md`](as-of-life-state-blind-judgment-n5-extension-report.md:3) 第7行回溯为 N=3、2/3。 |
| N5 累计 | 5 | 4 | 1 | 80% | N50-R2 报告第71行明确记录 N=5、4/5。 |
| N50-R2 本轮新增 | 3 | 1（部分命中） | 2 | 33.3% | [`...n50-extension-report-r2.md`](as-of-life-state-blind-judgment-n50-extension-report-r2.md:60) 第66、72行。 |
| N5 + N50-R2 合并 | 8 | 5 | 3 | 62.5% | 同报告第73、125行；报告第75、95～98行明确禁止当成真实准确率。 |
| 连续 R1 后累计 | 9 | 5 | 4 | 55.6% | R1 第117～125、161～163行。 |
| 连续 R2 后累计 | 10 | 5 | 5 | 50% | R2 第125～144、169～171行。 |
| 连续 R3～R8 累计 | 11 | 6 | 5 | 54.5%（6/11） | R3 新增中心命中；R4 BLOCKED、R5～R8 无效，累计不再变化。R8 第218～234行。 |
| 根因报告三态重算（8个已有核验案） | 8 | 2 CENTER + 3 ALTERNATIVE | 3 MISS | 不提供单一命中率 | [`...root-cause-report.md`](as-of-life-state-blind-judgment-root-cause-report.md:22) 第24～48行揭示 3 个替代命中全部同向偏乐观。 |
| fresh cohort | 3 | 不宜强并 | 不宜强并 | 未形成与旧轮完全同口径总命中率 | 主要输出结构断言/现实完成度/事件候选分评分，暴露 overclaim。 |

**趋势判断**：没有持续改善证据。累计序列为 **0% → 66.7% → 80% → 62.5% → 55.6% → 50% → 54.5%**；R4～R8 因 1 个 BLOCKED、4 个无效，没有新增可评分改善证据。更重要的是，根因复核把表面“5/8 命中或部分命中”拆成 2 个中心命中、3 个同向偏乐观替代命中、3 个失验，证明合并分数掩盖了系统性强度过断。诚实结论是：**准确率没有随时间稳定改善；最新有效账本约在五成上下徘徊，且受非随机选样、无效样本和宽泛措辞影响。**

---

## 5. 偏离项分级与诚实结论

### 5.1 偏离项数量

本审计确认 **6 项材料性偏离/缺口**：

| # | 偏离/缺口 | 严重度 |
|---:|---|---|
| 1 | 职业中心多选宽泛化，缺乏语义宽度和互斥性约束 | **高** |
| 2 | 2～3 年窗口叠加多选事件类型，精确应期不可证伪 | **高** |
| 3 | `yingqi.retrospective` 确定性逐年扫描未接入 `AnnualInteractionTrace` | **关键/高** |
| 4 | 结构可能性被人工冻结层过断成现实完成度 | **高** |
| 5 | 07-27 多专家 feedback promotion 收口触碰优先级禁止项 #2 | **高** |
| 6 | 07-19～26 F09/PI/G6-task 大型治理轨道消耗资源但不推进 as-of | **中**（方向资源错配，不追溯判违规） |

另有 1 个低严重度边界项：G10 做到 F10 启动决策包，但最终 `HOLD F10`，没有实质启动，不计入 6 项材料偏离。

### 5.2 直接回答：“都白做了吗？还是走偏了？”

**不是都白做了，也不是整体走错方向；准确结论是：主线走对了，但完成度被治理成功感和样本命中表象高估，并存在 5 个高严重度的实质偏离/欠实现。**

走对且有保留价值的部分：

- 七对象和根源×完成方式已经变成可执行的 `engine/asof/` 原型；
- G0～G9 建成门禁、状态归并、样本外回放、薄集成和 CLI；
- Unit8～11 建成 session、未来投影、财富传播和制品化；
- First Proof/N5/N50 开始真正执行“先冻结、后开反馈”，并诚实记录 0/1、无效样本、BLOCKED 和累计回落；
- 这些都服务核心文档，不是白做。

但没有完成、且足以影响方向正确性的部分：

- 核心等式中的“已过关键流年的具体触发”仍主要靠人工宽窗口候选，没有把现有 retrospective 算法接入；
- “截止状态”在自然语言冻结层仍可能从结构直接跃迁到现实完成度；
- 职业中心和事件类型过宽，使“命中”可被低证伪性措辞抬高；
- 命中率没有形成改善趋势；截至 R8 的有效 N=11、观察 6/11 仍小、非随机，且三态复核显示强度轴系统性偏乐观；
- 明确优先级锁定生效当日，仍完成了多专家 promotion 轨道收口。

因此最诚实的总裁决是：

> **走对了但不完整，并在“应期接入、现实证据约束、预测可证伪性、优先级纪律”四个核心环节发生系统性偏移。历史工作不是废物，但不能再把接口/治理 PASS 当成推理质量 PASS，也不能继续扩域、调权、模板或规则规模来掩盖盲断证据不足。**

### 5.3 以后不可偏离的硬门

本审计不重新设计架构，但从核心文档可直接导出四条准入判据。任何后续工作在开始前必须回答：

1. 是否直接补齐“原局—大运—流年—截止状态”四层中的一个可验证缺口？
2. 是否提高盲断可证伪性，而不是扩大候选/窗口/措辞覆盖面？
3. 是否用已核验现实事实约束结构解释，而不是反向用结构覆盖现实？
4. 是否避开五项锁定任务；若触及，是否已有 as-of 闭环完成的证据而非治理性 PASS？

任一答案为“否”，默认停止，不以“顺手收尾”“已有代码”“测试全绿”或“报告更完整”为理由绕过。

---

## 6. 本审计明确不做的事

1. 不评价 `engine/asof/`、`engine/yingqi/` 或 F09 的一般代码质量、性能、安全性和风格。
2. 不重新设计 as-of 架构，不在本报告提出完整实现计划。
3. 不重跑测试；本任务是方向审计，既有测试 PASS 也不是命理准确率证据。
4. 不修改任何既有计划、报告、案例冻结件、代码、工具或状态文件。
5. 不重新评分全部历史案例；只按已有报告中可核实数字归并，并明确不可比口径。
6. 不评价五项禁止任务本身是否永远没有价值；只审计它们是否在 as-of 闭环之前被错误优先。
7. 不把文件数量、治理 Gate 数或 pytest 数量视为方向对齐证据。

---

## 7. 最终裁决

`PARTIALLY ALIGNED — MATERIAL CORRECTION REQUIRED`

- 主线方向：**对齐**。
- 完成度：**不完整，且关键应期链未闭合**。
- 验证证据：**有真实进展，但截至 R8 仅有效 N=11、观察 6/11，且高波动、非随机，不能证明准确率改善**。
- 材料偏离：**6 项（5 高、1 中），另 1 项低严重度边界事项**。
- 是否白做：**否**。
- 是否走偏：**局部且材料性走偏；若不立即以核心文档约束后续准入，将从“局部偏移”升级为“系统性偏离”。**


