# 分层命理决策学习系统架构设计

> 本文用于指导后续系统架构设计与代码实现。
>
> 核心目标：打造一个真正高准确率、可持续迭代的八字分析系统；系统应越来越懂“什么八字该用什么法”。
>
> 核心结论：系统不应继续走“多派融合成一个大杂烩”的路线，而应建立“分层决策模型”：输入事实、流派适用性、独立命题、结构审查、事件落地、应期概率、冲突仲裁、报告表达、反馈归因、校准治理逐层分权。
>
> 吸收原则：传统“数据先于判断、基础决定上层、理论分层、多证据验证、动态岁运、结果可解释”具有参考性；但必须从“多流派综合评分”改造为“流派适用性路由 + 分层裁判 + 分层反馈校准”。
>
> 本文以仓库现有代码为事实源：[`engine/decision/models.py`](../engine/decision/models.py:301)、[`engine/decision/orchestrator.py`](../engine/decision/orchestrator.py:34)、[`engine/decision/v5_adapter.py`](../engine/decision/v5_adapter.py:70)、[`engine/decision/l1_school_router.py`](../engine/decision/l1_school_router.py:52)、[`engine/v5/domain.py`](../engine/v5/domain.py:365)。编写顺序固定为：**geju 定靶心 → ponytail 压范围 → writing-plans 阶段化 → verification-before-completion 事实校验 → requesting-code-review + ponytail-review 最终审查**。

---

## 0. 格局判断（geju）

### 0.1 Thesis

**L0-L9 分层决策模型不需要“重新设计”，它已经在 [`engine/decision/`](../engine/decision/) 完整落地并带链路自校验。真正要做的重构只有一件事：把生产主链路上“先让流派发言、再反推谁适用”的倒置依赖，改成“先路由、后授权发言”。**

一句话：**方向已对，管道装反了。**

### 0.2 Confidence

**高置信度（针对问题定位）；中置信度（针对学习闭环成熟度）。**

高置信度的代码事实：

1. [`DecisionRun.validate_trace()`](../engine/decision/models.py:320) 已实现 L2→L1、L3→L2、L4→L3（且必须绑定 pass/weaken 的 verdict）、L5→L4、L6→L4、L7→L6、L8→L7、L9→L8 的全链路强校验，`abstain` 流派发言会被判非法。
2. [`route_schools()`](../engine/decision/l1_school_router.py:52) 已实现真正的规则式适用性路由：按四柱完整性、大运有无、分析焦点交集产出 `lead / co_lead / evidence_only / abstain`。
3. [`run_decision_mvp()`](../engine/decision/orchestrator.py:34) 已能从一段问真文本跑通 L0→L9 内存 DecisionRun。

中置信度的原因：

1. L1 路由是静态规则启发式，尚未由反馈驱动学习（falsifier 文案已写，学习回路未接）。
2. 生产报告默认入口仍是 legacy [`tools/render_report.py`](../tools/render_report.py:1)，run-centric 链路是 preprod。

### 0.3 The Trap（核心陷阱：倒置的路由依赖）

生产 v5→decision 适配路径 [`_school_applicability()`](../engine/decision/v5_adapter.py:70) 的实现是：

```text
schools = {claim.school for claim in output.claims}   # 先看谁已经发言
→ 再给这些已发言流派补一个 co_lead / abstain 适用性快照
```

这正是本文要杀死的“多流派大杂烩”换皮：**流派先无条件发言、系统事后追认适用性**。它与真正的路由器 [`route_schools()`](../engine/decision/l1_school_router.py:52)（先判资格、后决定谁能发言）方向相反，而后者当前只接在独立 MVP，未进生产。

| 继承形态 | 表象 | 是否真实约束 | 判断 |
|---|---|---|---|
| v5 五派固定角色（[`V5_SCHOOL_ROLES`](../engine/v5/domain.py:43)） | 每派天生一个角色 | 不真实 | 固定角色违反“没有万能流派”；角色必须由 L1 按盘、按域动态给。 |
| `_school_applicability` 反推适用性 | 迁移期快照，看着无害 | 不真实 | 它让 L1 沦为橡皮图章，是倒置依赖的根源，应删除。 |
| v5 与 decision 两套 run 模型并存 | 似乎要长期双轨 | 部分真实 | 二者不平权：[`V5RunSnapshot`](../engine/v5/domain.py:365) 是“各派说了什么”的事实快照，[`DecisionRun`](../engine/decision/models.py:301) 是“如何裁决”的账本。快照是源，账本是派生。 |
| L0-L9 看似未落地 | 文档写成未来工作 | 不真实 | 已落地；继续把它当规划会导致重复造轮子。 |

### 0.4 一主两辅

| 线路 | 角色 | 保留原则 |
|---|---|---|
| DecisionRun 裁判主线 | 正式目标主线 | 围绕 [`DecisionRun`](../engine/decision/models.py:301) 收口；L1 路由必须前置于 L2。 |
| V5RunSnapshot 事实快照 | 事实源辅线 | 保留“各派命题事实”，作为 DecisionRun 的输入，不作第二事实源。 |
| legacy render_report | 兼容辅线 | 保稳定，不承载新领域能力。 |

### 0.5 Kill / Merge / Split（ponytail 边界）

Kill：

1. 杀掉 [`_school_applicability()`](../engine/decision/v5_adapter.py:70) 的“从命题反推适用性”，改为调用真正路由。
2. 杀掉“五派固定角色即适用性”的观念。
3. 杀掉“L0-L9 待建设”的叙事。

Merge：把 v5 输出通过 L1 路由后再进 L2，L2 只接受被授权流派的命题。

Split：`V5RunSnapshot`（事实）与 `DecisionRun`（裁判）职责分离，不做平权双事实源。

明确不做：

1. 不新增第三套 run / decision 模型。
2. 不现在切生产默认报告入口。
3. 不现在大搬目录。
4. 不把静态路由一步做成完整学习系统；先接反馈信号回路，再谈自动升降级。

### 0.6 Options

| Option | 描述 | Verdict |
|---|---|---|
| Conservative | 保留 `_school_applicability` 反推，只补文档 | Reject：倒置依赖不除，等于没改。 |
| Clean target | 生产直接切 route_schools 前置 + 默认入口切换 | Not now：迁移面大，先证纵切片。 |
| Staged clean | 先让 route_schools 前置于 v5 命题生成、在 preprod 证明链路不断，再逐步降级旧路径 | **Recommend** |

---

## 1. 总体裁决

系统的长期目标不是建立一个“把所有流派结论加权平均”的融合器，而是建立一个分层命理决策学习系统。

核心判断：

```text
没有万能流派，只有适用场景。
```

因此，系统第一步不是让所有流派都发言，而是判断：

```text
这个八字
→ 在这个领域
→ 对这个问题
→ 哪些流派有资格主审
→ 哪些流派只能辅证
→ 哪些流派必须弃权
```

系统追求的不是理论统一，而是：

1. 判断过程可追溯。
2. 流派适用性可学习。
3. 反馈可归因到层。
4. 规则与裁判策略可淘汰。
5. 准确率可按层、按域、按事件类型持续提升。

---

## 2. 从传统设计思想中吸收什么

外部材料中的以下思想具有参考性，应有机吸收。

### 2.1 数据先于判断

所有判断必须建立在完整、可追溯的事实账本上。

吸收方式：落实到 L0 输入事实层。

L0 只解析问真文本、登记缺失、保留未知区块和自由事实，不做命理判断。

### 2.2 基础决定上层

高级判断必须引用下层结果，不能跳层。

吸收方式：落实为分层依赖规则。

```text
结构未成立 → 事件不能硬落地
事件未成立 → 应期不能硬预测
冲突未裁决 → 报告不能写成确定结论
```

### 2.3 理论分层

格局、旺衰、调候、病药、象法、组合、神煞、岁运解决的问题不同。

吸收方式：这些理论不作为平级投票者，而是成为不同层级的证据来源。

| 理论 / 工具 | 新系统定位 |
|---|---|
| 格局理论 | 结构合法性审查素材 |
| 旺衰理论 | 结构与力量判断素材 |
| 调候理论 | 气候偏枯、病药判断素材 |
| 病药理论 | 核心矛盾与修复路径素材 |
| 组合关系 | 结构变化与事件触发素材 |
| 象法理论 | 事件落地素材 |
| 神煞 | 旁证 / 反证素材，不能孤证主审 |
| 岁运 | 应期概率素材 |

### 2.4 多证据验证

一个判断不能靠孤证。

吸收方式：改为分层证据门槛，而不是机械“三证据原则”。

高置信结论至少需要：

```text
主命题证据
+ 结构层通过或削弱说明
+ 事件落地路径
+ 应期或证伪口径
```

弱证据即使有三条，也不能自动升为高置信。

### 2.5 动态分析

八字判断必须考虑大运、流年变化。

吸收方式：岁运不再作为“报告段落”，而作为 L5 应期概率层的核心输入。

### 2.6 结果必须可解释

任何结果都必须说明依据、支持、反证和裁决理由。

吸收方式：每个报告条目必须能追溯到完整链路。

```text
ReportViewItem
→ ArbitrationDecision
→ TimingProbability
→ EventHypothesis
→ StructuralVerdict
→ SchoolClaim
→ SchoolApplicability
→ ChartFactLedger
→ RawWenzhenPayload
```

---

## 3. 必须拒绝什么

以下思想不能进入系统主架构。

### 3.1 拒绝“多流派共同参与最终决策”的默认模式

不是每个八字都需要所有流派参与。

低适用流派如果继续参与结论，会增加噪声，降低准确率。

### 3.2 拒绝全局综合评分

外部材料中的“格局稳定性、日主力量、调候完成度、病药匹配程度、五行流通程度、刑冲影响程度、岁运引动程度、象法一致程度统一加权评分”有风险。

系统不采用全局综合分。

正确做法：

```text
先路由
再分层裁判
只在同一层、同一任务内做评分
不跨层平均
```

### 3.3 拒绝固定权重

固定权重无法体现“不同八字适用不同流派”。

权重必须来自：

```text
当前命盘适用性
× 当前领域适用性
× 当前事件类型历史命中率
× 当前层级历史命中率
× 证据强度
```

### 3.4 拒绝把理论分析步骤当系统架构

传统八层：基础数据、五行能量、格局、调候、病药、组合、象法、岁运，是分析素材分类，不是系统主架构。

系统主架构必须是决策链，而不是理论堆叠顺序。

---

## 4. 目标系统定义

系统名称建议：

```text
Layered Bazi Decision Learning System
分层命理决策学习系统
```

系统本质：

```text
命理判断的司法系统
```

类比：

| 系统部分 | 类比 |
|---|---|
| 问真排盘事实 | 案件事实 |
| 各流派 | 证人 / 专家证言 |
| 流派适用性路由 | 专家资格审查 |
| 结构合法性层 | 证据合法性审查 |
| 事件落地层 | 案由归类 |
| 应期概率层 | 时间与概率评估 |
| 冲突仲裁层 | 法官裁决 |
| 报告表达层 | 判决书 |
| 反馈归因层 | 上诉与复盘 |
| 校准治理层 | 判例法与制度修正 |

---

## 5. 分层决策模型总览

最终层级为 L0 到 L9。

| 层级 | 名称 | 目标 | 准确率责任 |
|---|---|---|---|
| L0 | 输入事实层 | 解析问真专业文本、登记缺失、保留自由事实与未知区块 | 输入事实准确 |
| L1 | 流派适用性路由层 | 判断每个流派在当前命盘中的角色 | 选对流派 |
| L2 | 派别独立命题层 | 被授权流派独立产生命题 | 单派命题准确 |
| L3 | 结构合法性层 | 判断命题是否有命局结构基础 | 防止无根断语 |
| L4 | 事件落地层 | 把结构命题转成现实事件 | 事件类型准确 |
| L5 | 应期概率层 | 给事件时间窗、触发条件、概率区间 | 时间预测准确 |
| L6 | 冲突仲裁层 | 多派冲突时裁决优先级 | 综合裁判准确 |
| L7 | 报告表达层 | 只展示裁判结果和反馈点 | 表达不失真 |
| L8 | 反馈归因层 | 判断反馈命中或失验属于哪一层 | 学习信号准确 |
| L9 | 校准治理层 | 升级、降级、冻结、淘汰规则与策略 | 长期迭代准确 |

---

## 6. L0 输入事实层

### 6.1 已确认边界

L0 只针对问真专业文本格式。

已确认规则：

1. 问真文本区块未来可能扩展。
2. `_` 全部视为缺失但合法。
3. `$FOUR` 字段顺序固定。
4. `$DY_LOOP` 中 `#` 表示运节点，`>` 表示流年节点。
5. L0 可接收排盘事实和已知人生事实。
6. 已知人生事实用自由文本。
7. 已知人生事实不进入排盘事实，只作为后续校验材料。
8. 排盘事实与已知人生事实冲突时，只记录冲突，不裁决。
9. 未知区块原样保留。
10. L0 只校验格式完整性。

### 6.2 L0 允许做什么

```text
parse
normalize
record_missing
preserve_unknown
validate_format
```

### 6.3 L0 禁止做什么

```text
judge
predict
arbitrate
explain
infer_character
infer_wealth
infer_marriage
infer_timing
```

### 6.4 L0 输出对象

```text
RawWenzhenPayload
- raw_text
- raw_hash
- captured_at
- parser_version
```

```text
ChartFactLedger
- sex_marker
- solar_datetime
- four_pillars
- pillar_details
- siling
- void_by_pillar
- start_luck
- dayun_steps
- liunian_steps
- missing_fields
- unknown_blocks
- raw_source_hash
```

```text
ContextFactLedger
- known_fact_text
- analysis_focus_text
- conflict_notes
- preserved_text_blocks
```

L0 输出分为“排盘事实账本”和“校验材料”。排盘事实给 L1-L5 使用；自由文本事实只作为后续校验与上下文材料，不污染排盘事实。

---

## 7. L1 流派适用性路由层

### 7.1 核心原则

不同八字适用不同流派，一个流派不可能正确分析所有八字。

系统必须先生成流派适用性矩阵，再决定哪些流派能发言。

### 7.2 SchoolApplicability

```text
SchoolApplicability
- school
- role: lead | co_lead | evidence_only | abstain
- applicable_domains
- applicability_score
- reasons
- blockers
- confidence
- falsifier
```

### 7.3 role 权限

| role | 含义 | 权限 |
|---|---|---|
| lead | 当前命盘或领域主审 | 可产出主命题，可影响最终裁决 |
| co_lead | 当前命盘或领域副主审 | 可产出主命题，可参与裁决 |
| evidence_only | 只做旁证 | 只能提供证据，不得单独形成结论 |
| abstain | 弃权 | 只记录弃权原因，不进入裁判 |

### 7.4 流派适用范围初始画像

| 流派 / 系统 | 更适合主审的场景 | 更适合作辅证的场景 | 应弃权或降权的场景 |
|---|---|---|---|
| 子平类 | 格局、旺衰、用忌、结构层级清楚的命盘 | 事业、财富、学历、层级判断 | 纯象法细节、具体人物画像不足时 |
| 滴天髓类 | 气势、寒暖燥湿、调候、全局气机明显的命盘 | 格局成败、病药、气势偏枯 | 事件细节和具体应事不足时 |
| 段建业 | 做功路径、体用、宾主、财富事业落地明显的命盘 | 财运、事业、资源转化 | 做功路径不明显时 |
| 杨清娟 | 婚姻、人物画像、暗合、取象明显的命盘 | 配偶、关系、家庭、人物细节 | 结构层级判断不宜单独主审 |
| 任付红 | 岁运触发、应期、是非判断明显的命盘 | 时间窗、触发点、应期验证 | 原局结构未成立时不能单独定事件 |
| 高德臣 | 神煞、健康灾厄、旁证、学业子女等信号明显的命盘 | 健康、灾厄、学业、旁证补强 | 神煞孤证不能主审大结论 |

### 7.5 L1 学习目标

系统应持续学习：

```text
什么类型的命盘
→ 哪个流派更准
→ 哪个领域更准
→ 哪类事件更准
→ 哪类应期更准
```

反馈必须回打到流派适用性画像，而不只是规则命中率。

---

## 8. L2 派别独立命题层

L2 只允许被 L1 授权的流派产生命题。

```text
SchoolClaim
- claim_id
- school
- role_granted_by_l1
- domain
- claim_type
- statement
- evidence_refs
- confidence
- falsifier
- dependencies
```

限制：

1. L2 不输出最终结论。
2. L2 不提前融合多个流派。
3. L2 不抹平冲突。
4. L2 必须保留每条命题的流派来源。

---

## 9. L3 结构合法性层

L3 审查 L2 命题是否有命局结构基础。

```text
StructuralVerdict
- verdict_id
- claim_id
- verdict: pass | weaken | reject | unknown
- structural_reason
- blocking_factors
- required_support
- confidence
```

结构层必须有否决权。

没有结构否决权，系统会被孤证规则、神煞孤断、模板化判断淹没。

---

## 10. L4 事件落地层

L4 把通过结构审查的命题转成现实事件。

```text
EventHypothesis
- event_id
- source_verdict_ids
- domain
- event_type
- subject
- concrete_event
- landing_path
- confidence
```

事件层必须具体，避免泛断。

不推荐进入高置信统计的泛断：

```text
事业有变化
感情有波动
财运有机会
健康需注意
```

推荐事件类型：

```text
升迁
换岗
创业
组织关系变化
收入结构变化
项目责任变化
结婚
离婚
疾病检查异常
手术
搬迁
破财
```

---

## 11. L5 应期概率层

L5 只回答事件何时触发、概率多高。

```text
TimingProbability
- prediction_id
- event_id
- time_window
- trigger_conditions
- probability_range
- confidence
- falsifier
```

禁止事项：

1. 不改写事件内容。
2. 不把事业事件改成婚姻事件。
3. 不绕过 L4 直接生成事件。

---

## 12. L6 冲突仲裁层

L6 是裁判层，不是融合层。

```text
ArbitrationDecision
- decision_id
- domain
- competing_event_ids
- result: winner | coexist | unresolved | reject_all
- winner_ids
- rejected_ids
- unresolved_ids
- arbitration_rule
- school_applicability_snapshot
- reason
```

动态仲裁权重应考虑：

```text
当前命盘适用性
× 当前领域适用性
× 当前事件类型历史命中率
× 当前层级历史命中率
× 证据强度
```

禁止固定写死某派永远优先。

---

## 13. L7 报告表达层

报告层只消费裁判结果，不新增推理。

```text
ReportViewItem
- report_item_id
- decision_id
- prediction_id optional
- display_text
- confidence_display
- evidence_summary
- feedback_prompt
```

禁止事项：

1. 报告层不能补命理判断。
2. 报告层不能把冲突改写成中庸话术。
3. 报告层不能生成无法追溯的断语。

---

## 14. L8 反馈归因层

反馈不应只记录命中或失验，而要定位是哪一层的问题。

```text
FeedbackSignal
- feedback_id
- report_item_id
- verdict: hit | miss | partial | unknown | skipped
- observed_fact
- observed_time
- notes
```

```text
FeedbackAttribution
- attribution_id
- feedback_id
- affected_layer: L0 | L1 | L2 | L3 | L4 | L5 | L6 | L7
- affected_object_id
- attribution_reason
- confidence
- requires_human_review
```

归因示例：

| 反馈情况 | 归因 |
|---|---|
| 事件发生了，但年份偏差两年 | L5 应期层错，L4 事件层可能正确 |
| 年份对了，但事件类型错了 | L4 事件落地错，L5 只是碰巧对 |
| 事件和年份都错，原命题也弱 | L2 或 L3 问题 |
| 报告写得太绝对，实际只是倾向 | L7 表达层问题 |
| 命主补充事实与输入相矛盾 | L0 或 ContextFact 问题 |
| 两派冲突，系统选错一方 | L6 仲裁策略问题 |
| 某派主审连续失验 | L1 流派路由问题 |

---

## 15. L9 校准治理层

L9 负责长期迭代。

校准对象不只是规则，还包括：

1. 流派适用范围。
2. 结构审查策略。
3. 事件落地映射。
4. 应期模型。
5. 冲突仲裁策略。
6. 报告表达策略。

```text
CalibrationAction
- action_id
- target_type: rule | school_profile | router | structure_policy | event_mapping | timing_policy | arbitration_policy | report_policy
- target_id
- action: upgrade | downgrade | freeze | deprecate | split | merge | review
- reason
- evidence_feedback_ids
- effective_from
```

生命周期建议：

```text
candidate
→ probation
→ confirmed
→ flagged
→ frozen
→ deprecated
```

这里不仅规则能降级，裁判策略和流派适用性也能降级。

---

## 16. 准确率指标体系

不要使用一个总准确率掩盖问题。

建议按层、按域、按事件类型统计。

| 指标 | 含义 |
|---|---|
| L1 routing accuracy | 流派适用性路由是否选对主审 |
| L2 claim hit rate | 单派命题被后续验证的命中率 |
| L3 structural precision | 结构层放行的命题后续命中率 |
| L3 rejection correctness | 被结构层驳回的命题是否确实不成立 |
| L4 event-type accuracy | 事件类型是否落对 |
| L5 timing hit rate | 时间窗是否命中 |
| L5 timing distance | 实际发生时间与预测窗口偏差 |
| L6 arbitration win rate | 仲裁胜出的路径是否最终更准 |
| L7 expression error rate | 报告表达是否歪曲裁判 |
| L8 attribution agreement | 反馈归因是否被人工认可 |
| L9 calibration gain | 校准后下一批样本准确率是否提升 |

真正高准确率系统必须能回答：哪一层准确，哪一层拖后腿。

---

## 17. 代码结构现状与定位

分层结构已在 [`engine/decision/`](../engine/decision/) 落地，不是待建设项：

```text
engine/decision/
  models.py                  已落地 · L0-L9 数据契约 + DecisionRun.validate_trace 全链路校验
  l0_wenzhen.py              已落地 · 问真文本解析
  l0_context.py              已落地 · 自由文本事实账本
  l1_school_router.py        已落地 · route_schools 规则式适用性路由（R1 起已前置生产）
  l2_claims.py               已落地 · 授权流派命题
  l3_structure.py            已落地 · 结构合法性
  l4_events.py               已落地 · 事件落地
  l5_timing.py               已落地 · 应期概率
  l6_arbitration.py          已落地 · 冲突仲裁
  l7_report_view.py          已落地 · 报告视图
  l8_feedback_attribution.py 已落地 · 反馈归因
  l9_calibration.py          已落地 · 校准动作
  orchestrator.py            已落地 · run_decision_mvp 内存 L0-L9 证明物
  v5_adapter.py              待删除 · R1 已删 _school_applicability 反推；现为 V5Output→DecisionRun 事后转录层，是倒置的最后寄生处（R10 终局删除，判断归位 L3/L4）
```

R1 已删除 [`v5_adapter.py`](../engine/decision/v5_adapter.py:1) 的“从命题反推适用性”，L1 路由已前置生产。当前 adapter 仍是 `V5Output→DecisionRun` 的事后转录层，并寄生了本该属于 L3/L4 的判断（`_extract_geju_profile` / `classify_event_type`）。核心待办不再是修 adapter，而是 §R10 的终局：让 v5 runner 下沉为 L2 命题供应器、判断归位分层链、删除 adapter 转录定位。

现有模块重新定位：

| 现有模块 | 长期定位 |
|---|---|
| tools/preflight.py | 旧 YAML 输入 adapter |
| engine/v5/runner.py | 临时聚合，逐步拆入 decision stack |
| engine/v5/ziping_runner.py | L2 子平 claim runner |
| engine/v5/ditiansui_runner.py | L2 滴天髓 claim runner |
| engine/energy/ | 段派 / 结构素材供应 |
| engine/picture/ | 杨派取象 / 事件素材供应 |
| engine/yingqi/ | L5 应期工具 |
| engine/pangzheng/ | L3 / L6 旁证反证工具 |
| engine/v5/report_view.py | L7 报告视图 |
| tools/feedback_ingest.py | L8 反馈入口，后续扩展归因 |
| engine/application/pipeline_runner.py | 旧兼容 / 回归 runner，禁止新增能力 |
| engine/pipeline.py | 历史 facade，只保留兼容导出 |

---

## 18. 分阶段落地路线（基于现状）

前提：L0-L9 数据契约、各层实现、`run_decision_mvp` 与 `validate_trace` 已落地。以下阶段不是从零建设，而是把倒置的生产路径扳正、再逐步接学习回路。已完成项不重复建设。

### 已完成（现状核对）

1. L0-L9 数据模型：[`engine/decision/models.py`](../engine/decision/models.py:31)。
2. 全链路校验：[`DecisionRun.validate_trace()`](../engine/decision/models.py:320)。
3. 规则式 L1 路由：[`route_schools()`](../engine/decision/l1_school_router.py:52)。
4. 内存 L0-L9 证明物：[`run_decision_mvp()`](../engine/decision/orchestrator.py:34)。
5. preprod 已消费 decision 派生：[`engine/v5/preprod.py`](../engine/v5/preprod.py:18)。

### Phase R1：扳正生产路由依赖（核心）

> 状态：已完成（route_schools 已前置于生产 v5→decision，_school_applicability 已删除，回归测试见 tests/test_decision_v5_adapter.py）。

目标：删除“先发言后追认适用性”，让 L1 前置。

动作：

1. 在生产 v5→decision 链路中，先用真实适用性路由决定授权流派，再让 L2 只接受被授权流派命题。
2. 删除或降级 [`_school_applicability()`](../engine/decision/v5_adapter.py:70) 的“从命题池反推”逻辑。
3. `abstain` 流派命题被 `validate_trace()` 判非法，作为回归护栏。

验收：生产链路产出的 DecisionRun，其 L1 适用性来自路由而非命题池；`validate_trace()` 返回空。

不做：不切默认报告入口，不改 legacy render_report 行为。

### Phase R2：路由输入从盘面事实取信号

> 状态：已完成（route_schools 已接入 _chart_signals：五行偏枯提升 ditiansui 分数、地支冲提升 duan_jianye / ren_fuhong 角色；区分力护栏见 tests/test_l1_structural_signals.py）。R2 仅从 four_pillars 派生信号，未读取未填充字段。

目标：让 L1 路由不只看四柱完整性，还能按盘面结构特征区分“该用哪派”。

动作：把结构、气势、做功、取象、应期等可判定的盘面信号接入 [`route_schools()`](../engine/decision/l1_school_router.py:52) 的打分。

验收：不同结构类型的命盘产出不同的 lead / evidence_only 分布，且每个 role 有 reasons 与 blockers。

### Phase R3：反馈归因回打到路由与层

> 状态：部分完成（单 run 内 miss 反馈已能回打到责任流派、产出 router 校准动作，见 [`tests/test_l9_router_calibration.py`](../tests/test_l9_router_calibration.py)）。跨 case 连续失验的聚合与真正改变未来路由属 R4，尚未实现。

目标：把 L8 归因结果接回 L1 适用性画像与 L9 校准动作。

动作：

1. 反馈按层归因（已有 [`FeedbackAttribution`](../engine/decision/models.py:266)）。
2. 某派在特定结构 / 域 / 事件类型连续失验，触发 L9 对 `school_profile` / `router` 的 downgrade / review。

验收：`CalibrationAction` 能以 feedback 证据下调流派路由角色，且 evidence_feedback_ids 绑定到已归因反馈。

### Phase R4：分层准确率看板

> 状态：聚合与渲染已完成（build_accuracy_report + render_accuracy_markdown，按 verdict / 层 / 域 / 事件类型统计，见 tests/test_accuracy_report.py）。真实反馈样本接入与 L5 timing distance 等需真实发生时间的指标尚未实现，依赖数据而非代码重构。

目标：用 §16 指标按层、按域、按事件类型统计，而非单一总准确率。

验收：能回答“哪一层准确、哪一层拖后腿”，为 L9 提供校准依据。

### Phase R5：流派适用性学习先验注入（注入端）

> 状态：注入端已完成（route_schools 支持可选 learned_prior，缺省零回归，低命中先验可下调对应流派角色与分数，见 tests/test_l1_learned_prior.py）。真实反馈聚合出 learned_prior 并持久化回灌（R5-B）尚未实现，依赖真实反馈样本与 tools 层落盘，属数据工程而非纯路由重构。方向依据见 docs/superpowers/plans/2026-07-09-r5-cross-run-routing-learning-direction.md。

### Phase R6：扶正主干——让分层链驱动报告（核心方向）

> 状态：全域已落地（学业/事业/财富/婚姻/健康五域报告裁决结论均改读 L7 ReportViewItem；L7 display_text 已加厚，聚合各派最高置信依据；缺省零回归，见 tests/v5/test_report_reads_l7.py）。北极星仍是 v5 runner 下沉为 L2、L3 接真实命局审查、L4 从结构推导事件类型。

**核心判断**：真实案例 C-2026-035 跑通后暴露一个根本倒置——当前 v5 在推理，L0-L9 在抄写。命主看的报告 Markdown 走 [`render_report_v6_from_output(output)`](../engine/v5/report_view.py:304) 从 V5Output 直渲染；[`DecisionRun`](../engine/decision/models.py:301) 是并列旁路派生物（[`engine/v5/preprod.py`](../engine/v5/preprod.py:242) 两条路互不消费）。所以分层裁判链从未真正决定过报告里的任何一句话。

这与 R1 的"先发言后追认适用性"是同一种倒置的不同部位。R1 扳正了 L1 路由；R6 要扳正的是"报告主干"。

**四个已验证缺口（同一病灶的四个部位）**：

| 缺口 | 根因 | 性质 |
|---|---|---|
| L1 无 abstain | v5 chart 只有 dayun_summary 字符串、无 dayun_steps 列表，[`v5_adapter.py`](../engine/decision/v5_adapter.py:64) 取到空列表 | 配管 |
| L3 无 reject（0/330） | [`l3_structure.py`](../engine/decision/l3_structure.py:20) 只按 confidence<=0.1 reject，无真实命局审查 | 架构 + 命理逻辑 |
| L4 event_type 全为 v5_prediction | [`v5_adapter.py`](../engine/decision/v5_adapter.py:139) 硬编码占位符，未从结构推导事件 | 架构 |
| 报告与 L7 分离 | 报告 Markdown 不消费 L7 ReportViewItem，走旧 V5Output 渲染 | 架构（最根本） |

**目标模型**：让 DecisionRun 成为主干，v5 五派 runner 降为 L2 命题供应器，报告只读 L7、L7 只读 L6，逐层向下到 L0，删除 v5_adapter 的"事后转录"定位。

**分步取舍**：

1. Option A 补丁四缺口 → Reject（四个治标叠加仍是"v5推理+抄写"）。
2. Option B 一次性扶正主干大重构 → 北极星，Not now（工程量大、风险高）。
3. Option C 单向扶正切片 → Recommend：先让报告的一个域（事业）改读 L7 ReportViewItem，证明"分层能驱动报告"，再逐域迁移。

**第一证明物**：C-2026-035 报告"事业"域改读 L7 ReportViewItem，其余五域暂保持旧渲染（双轨期），验证报告文本与 decision-run.json 事业裁决一致。

**证伪口径**：若 L7 ViewModel 太贫瘠（只有"事业 winner"无五派依据/15 层判断），或 L3/L4 拿不到 v5 中间结构（旺衰/用神/做功路径）无法产出有信息量的 verdict，则 Option B 代价被低估，需回到本节重判。

**与 R1-R5 的关系**：R1-R5 扳正并强化了 L1 路由与反馈学习（输入端与学习端）；R6 扳正报告主干（输出端）。三者合起来才让"事实→路由→命题→结构→事件→应期→裁判→报告→反馈→校准"成为一条真正由分层链驱动、而非 v5 事后抄写的闭环。L3 真实命局审查是其中唯一的纯命理逻辑难点，应独立建模，不与配管工作混做。

### Phase R8：L4 事件类型分类（文本启发式过渡）

> 状态：已落地（L4 event_type 从占位符 v5_prediction 改为从 event_label 关键词分类，匹配不到回退按域通用类型，见 tests/test_l4_event_type.py）。**这是文本分类过渡，不是从命局结构推导事件**——真正的结构推导依赖 L3 真实审查（仍是占位），属后续阶段。分类关键词表 _EVENT_TYPE_KEYWORDS 是可迭代启发式，不是命理终态。

### Phase R9：L3 结构审查消费格局用忌神（一致性审查）

> 状态：已落地（L3 消费 v5 已算出的格局 favor/avoid 十神方向，对依赖忌神且无 favor 支撑的命题降级，低置信再 reject；无格局裁决时零回归，见 tests/test_l3_geju_review.py）。**这是消费 v5 已算出的格局结论做一致性审查，不是 L3 自行判定旺衰/用神**。C-2026-035 重跑实测：L3 verdict 分布由 R9 前 pass 287 / weaken 41 变为 pass 277 / weaken 51 / unknown 2（10 条依赖忌神命题被降级），validate_trace 仍为空。当前覆盖度取决于 v5 产出的格局裁决数量（仅事业域有格局裁决）。扩大覆盖（多域格局裁决、旺衰独立校验）属后续命局知识建模工作。

### Phase R10：北极星终局——v5 runner 下沉为 L2、删除 v5_adapter 事后转录

> 状态：**第一证明物已完成**（2026-07-11，分支 `feature/r10-ziping-career-l2-slice`，21 commits，200 passed）。子平 × 事业纵切片已证明：目标 L2-L4 原生产出、唯一 `DecisionRun` 驱动报告、`validate_trace()` 返回空、报告事业域全部占位符（五派列 + 裁决 + 共识 + 冲突）仅从 L7 `ReportViewItem` 派生（含结构化 `school_evidence`）、信息量 ≥ R6 基线（270/5/270）。L3/L4 判断（`_extract_geju_profile` / `classify_event_type`）已从 adapter 归位到 `l3_structure.py` / `l4_events.py`；adapter 仅保留非目标流派/领域的迁移期桥。**后续迁移待做**：其他流派/领域逐域迁移、adapter 全删、生产默认入口切换。**已知架构债（PRE_EXISTING_DEBT，来自 R9）**：L3 格局 profile 全局 scope 污染非目标流派/域；L3 对 `event_claim` 无条件发 `weaken`——均需 K 系列或后续迁移时收窄 scope。

#### R10.0 Thesis

**把"v5 推理 + L0-L9 抄写"扳正为"分层链原生推理"的终局，不是再补一层适配，而是删除 `v5_adapter` 的"事后转录"定位本身。** v5 五派 runner 应直接作为 L2 命题供应器，向 DecisionRun 投喂 `SchoolClaim`；L3-L7 在链内原生推理，不再从成品 `V5Output` 反向拆解。一句话：**adapter 是过渡期的脚手架，终局是拆掉脚手架，不是加固它。**

#### R10.1 Confidence

**高置信度（针对倒置定位与删除方向）；中置信度（针对一次性可迁移的工程量）。** 高置信：adapter 承载了本该属于 L1/L3/L4 的判断（代码已核实）。中置信：v5 runner 内部结构（旺衰/用神/做功路径）能否被 L2/L3 直接消费而不丢信息，需先做纵切片证明。

#### R10.2 The Trap（继承约束辨析）

| 继承形态 | 表象 | 是否真实约束 | 判断 |
|---|---|---|---|
| `v5_adapter` 事后转录 | 迁移期必要桥 | 不真实 | R1-R9 已把桥两端都扳正，桥本身成了倒置的最后寄生处，应删除而非加固。 |
| v5 runner 产出成品 `V5Output` | runner 天生输出报告级结论 | 不真实 | runner 应产出 L2 级 `SchoolClaim`（原子命题 + 证据 + 置信 + 证伪），成品化是历史耦合。 |
| L3/L4 判断寄生在 adapter | `_extract_geju_profile` / `classify_event_type` 在 adapter 内 | 不真实 | 命理判断必须归位到 L3/L4 层内，adapter 不应承载任何判断。 |
| legacy `render_report` 默认入口 | 生产仍走旧渲染 | 部分真实 | 有稳定性契约，属真实约束；迁移默认入口是 R10 的收尾，不是前置。 |

#### R10.3 Kill / Merge / Split（ponytail 边界）

Kill：删除 `v5_adapter` 的"从 `V5Output` 反推 L1/L3/L4"逻辑；删除"runner 必须产出成品结论"的耦合。

Merge：`_extract_geju_profile`、`classify_event_type` 等判断从 adapter 归位到 L3/L4 层内原生实现。

Split：v5 五派 runner 拆为"L2 命题供应"与"legacy 报告渲染"两职责，前者进 DecisionRun，后者随默认入口迁移时一并退役。

明确不做：不新建第三套 run 模型；不在 runner 下沉未证明前切默认入口；不把 R10 与 K 系列命理建模混做（配管 vs 命理逻辑分离）。

#### R10.4 Options

| Option | 描述 | Verdict |
|---|---|---|
| Conservative | 保留 adapter，继续在其内补 L3/L4 判断 | Reject：倒置的最后寄生处不除，等于 R6 只做了一半。 |
| Clean target | 一次性让全部五派 runner 下沉 L2 + 删 adapter + 切默认入口 | Not now：工程量最大、风险最高，缺纵切片证据。 |
| Staged clean | 先让**一派一域**（如子平·事业）runner 原生产出 L2 SchoolClaim，DecisionRun 不经 adapter 转录该切片，证明"链内原生推理"信息不丢，再逐派逐域迁移，最后删 adapter、切默认入口 | **Recommend** |

#### R10.5 First Proof Point（最小、可证）

子平派·事业域：`ziping_runner` 直接产出 L2 `SchoolClaim`，该域 DecisionRun 不经 `v5_adapter` 的反推逻辑；断言 (1) 该域 L1 角色、L3 verdict、L4 event_type 均由链内层产出而非 adapter 派生；(2) 报告事业域文本与 decision-run.json 一致；(3) [`validate_trace()`](../engine/decision/models.py:320) 返回空；(4) 相对 R6 基线，该域五派依据与 15 层判断信息量不减。

#### R10.6 Falsifier

1. runner 下沉后，L2 `SchoolClaim` 丢失 v5 内部结构（旺衰/用神/做功路径），L3/L4 拿不到足够信息产出有区分力的 verdict —— 说明 v5 runner 与 L2 契约不匹配，Clean target 代价被低估，回本节重判。
2. 纵切片报告信息量低于 R6 基线（依据变薄、15 层判断塌陷）—— 说明下沉损失信息，需先加厚 L2/L7 契约再迁移。

---

## 18bis. 独立命局知识建模工程（K 系列）

> 定位：R 系列扳正的是**决策链管道**（谁先发言、谁驱动报告、判断归哪层）；K 系列建的是**命理知识本身**（如何原生判旺衰/用神/格局/交叉验证）。两者正交：K 系列为 R10 之后的 L3/L4 提供"链内原生推理"所需的命理引擎，不与配管工作混做。**铁律不变：K 系列产出可被 L3/L4 消费的独立判断，但不得让 adapter 或报告层凭空发明命理。** 每项独立立项，建议各自用 geju 单独开题。

| 工程 | 目标 | 现状缺口 | 依赖 |
|---|---|---|---|
| K1 多域格局裁决 | 格局用忌神裁决从"仅事业域"扩到学业/事业/财富/婚姻/健康全域 | R9 的 L3 一致性审查只覆盖 v5 有格局裁决的事业域 | 独立命理建模，非配管 |
| K2 旺衰独立校验 | L3 原生判旺衰/用神，不再只消费 v5 已算结论 | 当前 L3 是"消费 v5 格局方向"的一致性审查，非独立推导 | 命理知识工程 + R10 下沉后 L3 才有原生输入 |
| K3 五派结构交叉验证 | 多派对同一结构的判断做交叉一致性校验，冲突入 L6 而非事后追认 | 当前无跨派结构级交叉验证，冲突仲裁只在事件层 | K1/K2 提供可比较的结构级判断 |

**K 系列证伪口径**：若任一 K 工程产出的"独立命理判断"在真实反馈上准确率不高于"消费 v5 结论"的基线，说明独立建模未带来增量，应回退到消费 v5 并重估 K 工程 ROI。

**排序建议**：K 系列依赖真实反馈样本校准（同 HANDOFF §4 的数据瓶颈），且 K2/K3 依赖 R10 下沉后 L3 有原生输入通道。因此近期不与 R10 并行启动；R10 纵切片证明"链内原生推理"可行后，再按 K1→K2→K3 逐项立项。

---

## 19. 第一证明物与证伪口径

内存 DecisionRun 证明物已由 [`run_decision_mvp()`](../engine/decision/orchestrator.py:34) 落地，链路校验由 [`DecisionRun.validate_trace()`](../engine/decision/models.py:320) 保证。因此本轮重构的第一证明物不是“再跑一次 MVP”，而是证明**生产路径的 L1 路由是前置的、不是反推的**。

### 19.1 First Proof Point（最小、可证）

用一个正式 case 跑生产 v5→decision 链路，断言：

1. DecisionRun 的 `school_applicability` 来自真实路由（含 `abstain` / `evidence_only` 分布），而非“命题池里出现过的流派全部 co_lead”。
2. 存在至少一个流派被路由为 `abstain`，且其没有任何 L2 claim。
3. [`validate_trace()`](../engine/decision/models.py:320) 返回空列表。

这是最小改动就能证明方向的切片：只要生产链路的 L1 不再由命题反推，方向即成立。

### 19.2 Falsifier（什么情况说明方向错了）

1. 真实路由接入后，几乎所有命盘所有流派仍恒为 `lead / co_lead`，说明路由无区分力，L1 只是换了个橡皮图章。
2. 路由前置后主要事件准确率不升反降，且 L8 归因显示错误集中在 L1，说明“先路由”假设本身有问题，需要回到 geju 重判。

链路能追溯（L7→L0）只是必要条件；L1 有真实区分力且能被反馈校准，才是充分条件。

---

## 20. 红线与反例

以下情况说明系统又偏回大杂烩：

1. 每个八字仍强制所有流派都写结论。
2. 低适用流派仍能影响最终结论。
3. L2 直接输出最终人生结论。
4. L3 开始定年份。
5. L5 改写事件内容。
6. L6 把冲突写成“综合来看”。
7. L7 报告层补命理判断。
8. 反馈只能命中 / 失验，不能归因到层。
9. 校准只升级规则，不能降级流派适用性或裁判策略。
10. 系统不能解释为什么某个八字不用某派主审。
11. 系统重新引入全局综合评分。
12. 系统把格局、神煞、象法、应期放进同一个评分表混算。

---

## 21. 近期最短行动清单

R1-R9 已在 [`engine/decision/`](../engine/decision/) 全部落地并通过验证（状态见 §18 各 Phase）。当前系统**不卡在代码，卡在两处**：真实反馈样本不足，以及北极星（R10）与命理建模（K 系列）尚未启动。不要顺着 R 序列惯性把已完成阶段再做一遍。

已完成：L0-L9 数据契约与链路校验、L1 规则路由前置生产、路由结构信号、单 run 反馈回打、分层准确率看板、学习先验注入端、报告改读 L7、L4 事件类型分类、L3 格局一致性审查。

当前真实起点（按优先级）：

1. **积累真实反馈样本（立即可做、不需新代码）**：让命主填 case 的 `feedback.md`，用 `python -m tools.feedback_ingest <case_id>` 摄入。R5-B 跨案学习、K 系列命理建模校准都卡在此，需按 `school×domain×role` 分桶、每桶 5-20 条起步。
2. **R10 纵切片（北极星第一步）**：按 §R10.5 让子平派·事业域 runner 原生产出 L2 `SchoolClaim`，该域不经 `v5_adapter` 反推，验证四条断言。这是删除 adapter 事后转录、把倒置彻底扳正的第一证明物。
3. **暂不启动的**：K 系列命理建模（依赖真实样本 + R10 下沉后 L3 原生输入通道），以及切换生产默认报告入口（R10 收尾项）。各自独立立项，用 geju 单独开题，不与 R10 配管混做。

---

## 22. 最终结论

真正高准确率、可持续迭代的八字系统，不应追求“更多流派融合”，而应追求：

```text
事实准确
→ 流派选对
→ 命题独立
→ 结构有审查
→ 事件可验证
→ 应期可证伪
→ 冲突可裁决
→ 报告不失真
→ 反馈可归因
→ 策略可淘汰
```

外部材料有参考性，但只能作为价值观和理论素材来源；它不能替代当前系统的分层决策主架构。

最终路线：

```text
保留“数据先于判断、基础决定上层、理论分层、多证据验证、动态岁运、结果可解释”；
删除“多流派默认融合、全局综合评分、固定权重、所有理论共同参与最终决策”。
```

系统的核心能力应从“生成报告”升级为“持续学习哪类八字该用哪套方法”。

补充（2026-07-10，真实案例 C-2026-035 验证后）：这一升级的前提是**报告本身必须由分层裁判链驱动**。当前系统仍是“v5 推理、L0-L9 抄写”的倒置状态（详见 §18 Phase R6 与 [`plans/l0-l9-refactor-geju-judgment-2026-07-10.md`](l0-l9-refactor-geju-judgment-2026-07-10.md)）。因此路线补一条压轴：**先让报告改读 L7、把 v5 各派 runner 降为 L2 命题供应器，让分层链真正当家，再谈跨案学习。** 否则学习学的只是 v5 的账，不是分层裁判的账。
