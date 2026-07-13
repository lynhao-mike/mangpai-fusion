# 八字智能推理平台推进与验证路线

> 日期：2026-07-11  
> 文档类型：阶段推进、实验验证与迁移路线  
> 状态：设计已批准，尚未开始实施  
> 服从文档：[`docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md`](../docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md)

## 1. 路线定位

本文记录从当前手工专家系统向目标智能推理平台演进时的待验证假设、实验方案、阶段门禁、失败处理和迁移顺序。

本文允许随证据更新，不是长期架构宪法。凡涉及目标模型、对象边界、能力认定原则和禁止事项，均以核心设计宪法为准。

本路线采用 **Staged Clean Path**：保留旧引擎作为金标准对照，逐个证明新知识表示、流派能力评估、条件化路由和学习闭环具有增益；达到门禁后再切换正式入口。不得以重构规模或兼容成本降低目标设计标准，也不得在核心假设未获验证前全面替换当前生产链路。

## 2. 已确认事实

以下结论来自本轮仓库审查，可作为路线起点：

1. 当前系统能够生成专业、完整的统一报告，且已具备命盘计算、案例归档、statement 索引、反馈摄入和校准基础设施；
2. 输出质量主要由 [`engine/energy/`](../engine/energy/)、[`engine/picture/`](../engine/picture/)、[`engine/yingqi/`](../engine/yingqi/) 和 [`engine/pangzheng/`](../engine/pangzheng/) 的手写领域逻辑承担；
3. [`theory/ziping/index.yaml`](../theory/ziping/index.yaml) 与 [`theory/tiaohou_ditiansui/index.yaml`](../theory/tiaohou_ditiansui/index.yaml) 等生产知识中存在大量原文转录、泛化条件和低判别触发，不能仅凭规则数量证明推理能力；
4. [`engine/contracts/10-ziping-fusion-v5.md`](../engine/contracts/10-ziping-fusion-v5.md) 已定义五派独立命题、结构图、三段仲裁、预测账本和学习信号等正确方向；
5. 当前五派实现落地不均衡，子平与滴天髓具有专门 runner，三盲派仍大量复用旧领域引擎；
6. [`engine/domain-weights.yaml`](../engine/domain-weights.yaml) 是 legacy 专家共识矩阵，不是实验测得能力；
7. [`engine/expert-weights.yaml`](../engine/expert-weights.yaml) 是当前运行时静态先验，但没有证明“某流派在某类命盘的某项任务上具有专长”；
8. 当前学习闭环能够记录和微调，但样本、归因颗粒度和条件化能力模型不足以支撑“什么八字该用什么法”；
9. 部分报告包含既有反馈校准内容，例如 [`reports/C-2026-018-坤-乙丑戊寅乙酉乙酉-content-report.md`](../reports/C-2026-018-坤-乙丑戊寅乙酉乙酉-content-report.md)，此类报告适合复盘，不得直接用作流派预测能力评估。

## 3. 待验证假设

### H1：知识可执行化假设

将手写领域知识抽取为可执行规则后，可以在保持可解释性的同时达到不低于旧引擎的领域判断质量。

**证伪条件**：在代表性案例上，新规则层持续低于旧引擎，且差距无法通过规则覆盖补齐或条件边界修正消除。

### H2：条件化路由增益假设

“流派 × 任务 × 命盘原型 × 时间尺度 × 证据完整度”的能力后验，能够优于固定“流派 × 领域”权重。

**证伪条件**：经过独立盲测后，条件化路由相对固定权重无稳定增益，或其增益小于复杂度和方差成本。

### H3：克制增益假设

允许 runner 输出 `abstain` 和 `unsupported`，能够提高精确率、校准度和高风险领域安全性。

**证伪条件**：克制机制长期造成有价值判断的大量缺失，且总体决策效用低于强制输出基线。

### H4：角色化仲裁假设

结构合法性、事件落地、应期概率三段仲裁，以及“主力流派 + 反证流派”角色分工，优于平权投票和单一融合分数。

**证伪条件**：三段仲裁不能稳定提升冲突解释力、预测质量或反馈归因质量。

### H5：局部专长假设

流派专长主要存在于“任务 × 命盘原型”组合，而不是整个领域。

**证伪条件**：样本增长后，细分能力持续向领域均值收缩，无法形成稳定、可复现的局部优势。

### H6：可学习闭环假设

反馈能够准确归因到规则、流派、任务、原型和预测，并使能力后验与事件概率在独立数据上持续改善。

**证伪条件**：归因噪声、反馈质量或样本稀疏导致更新不稳定，独立集表现未改善或持续退化。

## 4. 总体阶段门禁

所有阶段采用三态决策：

- **GO**：达到该阶段的覆盖、准确、校准、增量价值、可追溯性和安全门槛；
- **HOLD**：方向未被证伪，但样本不足、可信区间过宽、标签质量不足或工程证据不完整；
- **STOP / REFRAME**：核心假设被证伪，或新流程在独立评估中持续低于旧流程。

不得仅凭以下信号判定 GO：

- 报告看起来更专业；
- 规则数量增加；
- 单个案例表现突出；
- 已知反馈案例拟合更好；
- 人工专家主观认为“符合理论”。

每个 GO 至少要求：

1. 预测冻结且无标签泄漏；
2. 推理轨迹可追溯；
3. 概率可追溯到评分样本与能力快照；
4. 与旧流程或固定权重基线同案盲测；
5. 误差、校准和高风险假阳性均被评估；
6. 失败案例已分类，不以删除异常样本掩盖问题。

## 5. Phase 0：最小证明与数据盘点

### 5.1 目标

不重构全系统，先证明一条最小闭环可成立，并确认仓库现有案例是否足以构建无标签泄漏的评估集。

### 5.2 工作内容

1. 盘点 [`cases/`](../cases/) 中案例的出生信息、反馈完整度、标签可信度和是否曾参与规则开发；
2. 将案例划分为：规则开发污染、可做历史盲测、可做前瞻跟踪、不可量化；
3. 选择至少一个反馈可靠案例，建立独立于报告文本的标准任务标签；
4. 定义最小 Chart、Fact、Task、Claim、Prediction 和 FeedbackObservation 数据链；
5. 输出一个“六大领域 × 十五层展示”之外的内部结构化证明物，重点证明可追溯、冻结和反馈隔离；
6. 从结构化结果渲染统一报告，验证展示质量不依赖报告模板临时创造结论。

### 5.3 GO 门槛

- 能产生完整运行快照；
- 预测冻结前无法访问反馈；
- 至少一个任务能从 Fact 追溯到 Rule、Claim、ArbitrationResult 和 Prediction；
- 报告不泄露内部 ID；
- 新旧结果可并排审查。

### 5.4 HOLD 条件

- 现有案例无法确认开发污染程度；
- 反馈无法形成稳定任务标签；
- 输入或大运信息缺失导致无法比较。

### 5.5 STOP / REFRAME 条件

- 当前数据根本无法分离预测与反馈；
- 统一报告质量完全依赖无法结构化的人工补写；
- 最小对象链无法承载当前关键判断。

## 6. Phase 1：单领域知识重铸

### 6.1 推荐领域

首选财富领域，原因是 [`engine/picture/wealth_15tier.py`](../engine/picture/wealth_15tier.py) 已有明确等级映射和可比较结果，便于识别知识与代码耦合。

若数据盘点显示婚姻反馈更可靠，可改以婚姻事件任务为第一领域。选择依据必须是反馈质量与可验证性，而非代码修改难度。

### 6.2 工作内容

1. 识别旧领域引擎中的确定性计算、命理知识、事件映射和展示文案；
2. 保留确定性计算为谓词；
3. 把命理判断抽成 ExecutableRule；
4. 为每条规则建立正例、反例、边界例和 `abstain` 条件；
5. 新旧引擎同案并跑；
6. 建立规则覆盖、判别力、结果一致性和退化报告。

### 6.3 GO 门槛

- 新知识层不依赖字符串标签回读上游结论；
- 关键规则具备正反例判别测试；
- 在独立评估集上不低于旧引擎；
- 失败差异可定位到规则覆盖或条件边界；
- 新知识可通过数据修改扩展，无需改通用执行器。

### 6.4 STOP / REFRAME 条件

如果大量关键判断无法形式化，或可执行知识持续显著低于手写引擎，则收缩目标：保留手写领域引擎为主力，只把适用性路由、反馈隔离和能力评估接入旧引擎。

## 7. Phase 2：流派能力基线实验

### 7.1 初始规模

初始目标为 30—50 个反馈可靠、尽量未参与当前规则开发的案例，以及约 20 个可验证任务。该数字是实验起点，不是永久契约；若数据盘点不满足，应进入 HOLD，不得以泄漏案例凑数。

### 7.2 任务集

任务必须从领域拆为可验证问题，例如：

- 婚姻：晚婚、离婚/再婚、关系压力、配偶职业类别、婚恋事件时间窗；
- 财富：收入等级、财富波动、负债、资产积累、收入来源、重大损失时间窗；
- 事业：职业类型、岗位变化、权责变化、创业/体制路径、失业或转岗时间窗；
- 学业：学历等级、考试阶段变化、专业路径、证书与继续教育；
- 健康：器官系统风险、已发生疾病类别、风险时间窗；
- 性格与画像：只做双盲标签一致度，不伪装成事件概率。

### 7.3 独立盲评协议

每个流派只读取：

- 标准出生事实；
- 统一确定性派生事实；
- 当前任务定义；
- 输入完整度。

每个流派不得读取：

- 真实经历；
- 反馈文件；
- 已有报告中的反馈校准段；
- 其他流派中间结论；
- 旧报告最终结论。

所有输出冻结后才揭示标签并评分。

### 7.4 四组实验

```text
A. 只使用该流派
B. 使用全部流派
C. 使用全部流派但移除该流派
D. 基础事实模型加该流派
```

### 7.5 评分体系

- 二元事件：Brier Score 与 Log Loss；
- 多分类事件：macro-F1 与多分类概率评分；
- 时间窗：窗口命中、中心偏差和越界惩罚；
- 等级预测：有序分类误差；
- 画像判断：人工双盲一致率；
- `abstain`：正确克制奖励与机会损失惩罚；
- 模糊命题：vagueness penalty；
- 自相矛盾：contradiction penalty；
- 高风险事件：提高 false positive cost。

建议单命题效用框架：

```text
utility
= probability_score
+ timing_score
+ specificity_bonus
- false_positive_cost
- vagueness_penalty
- contradiction_penalty
```

具体系数必须由基线实验与风险偏好确定，不在本路线中先验写死。

### 7.6 能力发布条件

只发布同时记录以下字段的“暂定专长”：

```text
posterior_mean
credible_interval
N_eff
calibration_error
incremental_gain
evidence_grade
```

不允许只发布命中率排行榜。

## 8. Phase 3：方法适用性路由

### 8.1 初始命盘原型

第一版控制在 10—20 个稳定原型，候选维度包括：

- 身强、身弱、从格候选；
- 气势集中、多方混战；
- 做功链清晰、不清晰；
- 宫位冲合明显、弱；
- 官杀混杂及财官印食关键组合；
- 寒暖燥湿极端、中和；
- 原局信号强、依赖大运流年；
- 神煞与结构同向、冲突。

原型必须由 Fact 定义。不得一开始创建数百个专家文本标签。

### 8.2 层级能力模型

```text
全局流派能力
→ 流派 × 领域
→ 流派 × 任务
→ 流派 × 任务 × 命盘原型
```

样本不足时自动向上收缩，禁止小样本格子独立掌权。

### 8.3 路由决策

候选形式：

```text
route_score
= expected_utility
- risk_factor × posterior_uncertainty
+ complementarity_gain
```

参数由 Phase 2 实验估计。路由结果选择一至两个主力流派和至多一个反证流派，并允许所有流派均不具备足够证据。

### 8.4 对照组

必须与以下基线比较：

- [`engine/expert-weights.yaml`](../engine/expert-weights.yaml) 固定领域权重；
- 所有流派平权；
- 单一最佳流派；
- 不路由、全部参与。

### 8.5 GO 门槛

条件化路由在独立盲测中同时满足：

- 总体决策效用不低于最佳基线；
- 校准误差不恶化；
- 高风险假阳性不增加；
- 至少部分任务×原型显示稳定增量；
- 路由原因可解释且可复现。

若只提高训练集表现，必须 STOP 并检查过拟合。

## 9. Phase 4：推理内核与学习闭环

### 9.1 推理内核

1. 五派 runner 独立输出标准命题；
2. ClaimGraph 区分结构、事件、时间、程度和表达冲突；
3. 三段仲裁分别产出结构合法性、事件落地和应期概率；
4. PredictionLedger 只接收可反馈事件；
5. ReportView 只消费仲裁与预测结果。

### 9.2 学习归因

反馈应尽量映射到：

```text
claim_id
school_id
rule_id
task_id
chart_prototype_id
prediction_id
time_error
feedback_quality
```

无法映射时不得平均分摊给所有参与规则。

### 9.3 N_eff 分级治理

建议从以下分级开始验证：

- 低样本：仅记录信号和可信区间，不调整生产决策；
- 中样本：允许小幅调整适用性后验，不修改核心规则；
- 成熟样本：允许调整规则先验和生产路由，但需版本冻结与人工复核；
- 高风险领域：无论样本量，重大权重变化均需人工审批。

具体阈值由 Phase 2 数据分布确定，不在此提前固定。

### 9.4 前瞻冻结验证

在规则和路由版本冻结后，收集新案例作为 E3/E4 证据。只有前瞻表现支持的专长才能进入正式生产路由。

## 10. Phase 5：正式切换与旧引擎退场

### 10.1 正式切换条件

- 六大领域核心任务覆盖不低于旧流程；
- 独立集决策效用与校准整体不低于旧流程；
- 高风险断语安全指标不退化；
- 所有正式结论具备最小审计链；
- 路由、能力后验和预测快照可复现；
- 反馈可归因；
- 统一报告不依赖 runner 私有对象。

### 10.2 退场顺序

1. 新旧并跑；
2. 新流程作为默认，旧流程作为显式 fallback；
3. 观察前瞻生产表现；
4. 旧流程降为回归对照命令；
5. 只有确认无真实外部契约依赖后，删除旧主流程编排权；
6. 有价值的旧领域能力保留为规则、谓词或 runner 内部适配器，不因删除旧编排而丢失。

## 11. 数据、泄漏与证据治理

### 11.1 数据分割

案例至少区分：

- 开发集：可用于规则构建；
- 历史盲测集：构建时不可见标签；
- 前瞻验证集：规则冻结后收集；
- 生产监控集：真实上线预测。

同一命主、多版本报告、衍生案例不得跨集合造成信息泄漏。

### 11.2 标签质量

反馈必须记录：

```text
source
observed_at
confidence_grade
quantifiable
conflict_state
reviewer
```

自述、第三方记录、结构化档案和推测性描述不能拥有相同标签权重。

### 11.3 泄漏处理

一旦发现 runner 在冻结前接触标签、反馈校准报告或旧最终结论，相关批次整体作废；不得通过删除个别异常输出继续使用该批次分数。

### 11.4 漂移监控

监控命盘来源、地域年代、社会制度、收入标尺、婚育时钟和反馈渠道变化。社会语境变化可能使事件映射失效，但不必然推翻底层结构规则。

## 12. 失败与异常处理

| 情况 | 处理 |
|---|---|
| 输入不完整 | 降低 evidence completeness，禁止补造事实 |
| 无适用流派 | 输出证据不足，不强制路由 |
| 流派冲突且证据接近 | 保留少数派和冲突，不强行唯一结论 |
| 后验样本不足 | 向上级均值收缩并显示宽可信区间 |
| 反馈互相矛盾 | 进入人工裁决，不自动学习 |
| 标签泄漏 | 整批实验作废 |
| 知识抽取后退化 | 保留旧引擎，不扩大迁移范围 |
| 某派无增量价值 | 降低决策权，保留研究输出 |
| 条件化路由无增益 | 回退固定先验，简化路由模型 |
| 报告覆盖退化 | 不切正式出口，定位 ViewModel 或上游缺失 |
| 前瞻表现与历史回测分离 | 冻结更新，检查过拟合与数据漂移 |

## 13. 测试体系

### 13.1 契约测试

覆盖对象序列化、三态输出、ID 稳定、路由快照、规则版本、预测冻结和历史复现。

### 13.2 规则判别测试

每条生产规则必须有：

- 正例触发；
- 反例不触发；
- 排除条件；
- 边界例 `abstain`；
- 反证条件；
- 跨案例稳定性。

### 13.3 盲测回测

验证预测冻结、评分协议、四组流派实验、旧流程对照和泄漏防护。

### 13.4 前瞻生产验证

验证 E3/E4 证据、实时校准、风险告警、反馈延迟和模型漂移。

## 14. 现有权重迁移定位

### 14.1 legacy 领域矩阵

[`engine/domain-weights.yaml`](../engine/domain-weights.yaml) 保留为 expert-authored hypothesis registry 的历史输入，不得直接升级为条件化能力事实源。

### 14.2 当前运行时权重

[`engine/expert-weights.yaml`](../engine/expert-weights.yaml) 在正式迁移前继续作为兼容运行时事实源。后续应补充：

```text
prior_source
evidence_grade
applicable_scope
last_reviewed_at
```

其数值作为弱先验进入能力模型，不作为专长证明。

### 14.3 新能力事实源

未来应建立独立的 school capability registry，存储条件化能力后验、可信区间、N_eff、校准误差、增量价值和证据等级。不得把这些易变统计塞回静态领域权重文件。

## 15. 第一推进单元

文档批准后的第一个实施计划只覆盖：

> 建立流派能力评估协议与最小盲测数据包。

该单元包括：

1. 案例可用性与污染盘点；
2. 首批统一任务集；
3. runner 独立出题与三态输出规范；
4. 预测冻结和标签揭示流程；
5. 评分函数与四组增量实验；
6. 能力后验最小输出格式；
7. 一份不宣称永久专长的基线评估报告。

该单元不包括：

- 全面重写五派 runner；
- 正式切换生产入口；
- 自动改写规则权重；
- 一次性抽取全部理论；
- 构建复杂在线学习服务。

完成第一推进单元并得到能力基线后，再决定 Phase 1 首选财富还是婚姻领域，以及是否值得实现条件化路由器。

## 16. 阶段状态维护规则

本文后续允许追加阶段状态，但不得硬编码产品版本、规则总数、当前 N_eff 或 Git HEAD。相关事实必须引用仓库唯一事实源或运行时工具。

每次阶段更新至少记录：

```text
phase
status: GO | HOLD | STOP | IN_PROGRESS
evidence_artifacts
accepted_hypotheses
rejected_hypotheses
known_risks
next_irreversible_decision
updated_at
```

当前状态：第一推进单元（流派能力评估协议与最小盲测框架）已实现并合并。下一不可逆决策是启动 Phase 0 真实标注数据地基，并打通"能力后验 → L1 路由"回流飞轮。

## 17. As-Built 审计与阶段状态（2026-07-12）

> 本节由 2026-07-12 系统级深度调研补入，记录第一推进单元合并后的真实实现状态与后续升级方向。属易变状态，以仓库唯一事实源为准，不覆盖第 1–15 节的目标原则。

### 17.1 第一推进单元交付事实

流派能力评估框架已实现并合并（merge commit `063e72a`），位于 [`engine/evaluation/`](../engine/evaluation/)，包含：

- [`models.py`](../engine/evaluation/models.py)：八个冻结持久化对象与三态命题契约；
- [`task_catalog.py`](../engine/evaluation/task_catalog.py) + [`mapping/school-capability-task-catalog-v1.yaml`](../mapping/school-capability-task-catalog-v1.yaml)：18 项可验证任务目录；
- [`case_audit.py`](../engine/evaluation/case_audit.py)：案例污染审计与盲测资格分级；
- [`freeze.py`](../engine/evaluation/freeze.py)：预测冻结与标签揭示门禁；
- [`scoring.py`](../engine/evaluation/scoring.py)：任务型评分与克制效用；
- [`capability.py`](../engine/evaluation/capability.py)：六维条件化能力后验；
- [`experiments.py`](../engine/evaluation/experiments.py)：四组增量实验；
- [`report.py`](../engine/evaluation/report.py) + [`tools/school_capability_baseline.py`](../tools/school_capability_baseline.py)：基线报告与只读 CLI；
- 147 项测试覆盖；经 7 任务双阶段审查 + 3 轮整体验收。

阶段状态：

```text
phase: 第一推进单元（能力评估协议与盲测框架）
status: GO
evidence_artifacts: engine/evaluation/ · tests/evaluation/ (147 passed) · merge 063e72a
accepted_hypotheses: 盲测冻结/任务型评分/六维能力后验/四组实验 工程可实现
rejected_hypotheses: 无
known_risks: 尚无真实标注数据喂入；能力后验尚未回流 L1
next_irreversible_decision: 启动 Phase 0 真实标注数据地基
updated_at: 2026-07-12
```

### 17.1B Phase 0 真实标注数据地基状态（2026-07-13）

```text
phase: Phase 0 真实标注数据地基
status: HOLD
evidence_artifacts: META/school-capability-case-inventory.json · META/school-capability-data-foundation-summary-2026-07-12.md · tools/school_capability_dataset.py
accepted_hypotheses: 保守污染分级、结构化标签、reviewed manifest/config、冻结后揭示、前瞻登记与白名单隔离可工程化
rejected_hypotheses: 现有 990/Top30 feedback-first 案例可改名为 historical blind；宽泛领域命题可直接冒充精确评估任务
known_risks: 133 个现有案例 blind eligible=0；现有引擎缺显式 task-specific 事件绑定；无法由代码补造 30 个真实前瞻案例
next_irreversible_decision: 使用 prospective-intake + prepare-blind 对后续真实新案执行预测先冻结，累计至少 30 案后重跑 score/report 门禁
updated_at: 2026-07-13
```

HOLD 是 Phase 0 §5.4 规定的正确结果：样本不足时不得用污染案例凑数。代码侧采集与隔离基础设施已落地，但“≥30 个真实 prospective 案例”是外部事实采集门槛，不能通过并行 agent、复制同案或手写输出合法满足。

### 17.2 As-Built 真实实现审计发现

调研确认当前运行内核与目标架构的主要差距（证据来自源码通读）：

| 层 | 目标 | As-Built 现状 | 定级 |
|---|---|---|---|
| L0 事实 | 命局特征结构化 | [`engine/predicates/`](../engine/predicates/) 可算干支/十神/冲合；无统一"命局特征向量"对象 | 🟡 |
| L1 适用性 | 可学习"什么八字用什么法" | [`engine/decision/l1_school_router.py`](../engine/decision/l1_school_router.py) 的 `SCHOOL_PROFILES` 静态硬编码 + 全局命中率降权 | 🔴 |
| L2 命题 | 各派独立推导 + 证据链 | 子平 runner 仅月令旺衰+格局两层；三盲派靠 `theory/*/index.yaml` 原文触发；`school-claims.json` 存在人工手写命题 | 🔴 |
| L3 结构 | 结构一致性交叉校验 | 子平两层 + 滴天髓原文；无跨派结构对撞 | 🟡 |
| L4 事件 | 命题→事件类型 | v5 有 event_realization 阶段但多为模板文案 | 🟡 |
| L5 应期 | 概率+时间窗 | 有 whitelist 域与时间窗槽位；概率为固定档位非学习所得 | 🔴 |
| L6 仲裁 | 三段分离裁决 | [`engine/decision/l6_arbitration.py`](../engine/decision/l6_arbitration.py) 仅按置信差距选 winner/coexist/unresolved | 🔴 |
| L7 报告 | 结论表达 | [`tools/render_report.py`](../tools/render_report.py) + output_linter 成熟 | 🟢 |
| L8 归因 | 反馈归因到规则 | statement→rule→family 映射链存在 | 🟡 |
| L9 校准 | 权重优化/迭代 | `update_confidence` 仅 rule/family 两级线性 alpha/beta 加减 | 🔴 |

主干流水线 [`engine/application/pipeline_runner.py`](../engine/application/pipeline_runner.py) 实际为 `energy(段派)→picture(杨派)→yingqi(任派)→pangzheng(高派)→integrate` 串行工位链，非多派竞争。

理论库现状：[`theory/ziping`](../theory/ziping/index.yaml) / [`theory/tiaohou_ditiansui`](../theory/tiaohou_ditiansui/index.yaml) 为 production-active 但 `claim` 字段多为古籍原文整段；高派 261 条全为 candidate；段/杨/任派多为 promoted 但缺可判别 trigger。

### 17.3 四个致命差距（决定"越来越懂什么八字用什么法"）

1. **L1 适用性不可学习**：只有静态领域表 + 全局命中率，评估框架的六维能力后验没有回流通道。
2. **L2 命题非引擎生成**：有价值命题人工写入 JSON，导致盲测评估的其实是人的水平而非系统水平。
3. **L6 仲裁无命理逻辑**：只比置信数字，无结构/事件/应期分段裁决与矛盾对撞。
4. **L9 学习是拧螺丝不是学模型**：线性加减无法学到"某类结构下某派更可信"的条件化知识。

### 17.4 最高杠杆判断：回流飞轮

评估框架（已建成）产出"某派在某六维格子下的能力后验" → L9 转成"命局特征→流派权重"更新 → L1 下次分型更准。**这条 `评估 → L9 → L1` 回流通道目前完全断开，接通它是全局最高杠杆动作**，也是 Phase 2/3 的前置。评估框架当前唯一缺的是真实标注数据（Phase 0）与这条回流线。

### 17.5 后续升级方向与详细指导文档

按依赖排序拆分为独立可执行升级单元，每个单元有专属详细指导文档，见 [`plans/upgrade-guides/`](upgrade-guides/)：

| 序 | 升级单元 | 指导文档 | 前置 |
|---|---|---|---|
| 00 | 升级方向总览与依赖图 | [`00-overview-and-sequencing.md`](upgrade-guides/00-overview-and-sequencing.md) | — |
| 01 | 命局特征向量层（脊椎） | [`01-chart-feature-vector.md`](upgrade-guides/01-chart-feature-vector.md) | — |
| 02 | L2 命题引擎化 | [`02-claim-engine.md`](upgrade-guides/02-claim-engine.md) | 01 |
| 03 | 评估数据地基与真实标注 | [`03-evaluation-data-foundation.md`](upgrade-guides/03-evaluation-data-foundation.md) | 02 |
| 04 | L1 可学习路由与回流飞轮 | [`04-learnable-routing-flywheel.md`](upgrade-guides/04-learnable-routing-flywheel.md) | 01,03 |
| 05 | L6 分段仲裁与矛盾对撞 | [`05-segmented-arbitration.md`](upgrade-guides/05-segmented-arbitration.md) | 02 |
| 06 | L9 条件化学习与校准治理 | [`06-conditional-learning-governance.md`](upgrade-guides/06-conditional-learning-governance.md) | 03,04 |

胜负手是 **04**：它第一次让系统用独立盲测数据证明"学过之后 L1 分型命中率 > 静态表基线"。此假设成立，则平台目标成立。
