# 分层命理决策学习系统架构设计

> 本文用于指导后续系统架构设计与代码实现。
>
> 核心目标：打造一个真正高准确率、可持续迭代的八字分析系统；系统应越来越懂“什么八字该用什么法”。
>
> 核心结论：系统不应继续走“多派融合成一个大杂烩”的路线，而应建立“分层决策模型”：输入事实、流派适用性、独立命题、结构审查、事件落地、应期概率、冲突仲裁、报告表达、反馈归因、校准治理逐层分权。
>
> 吸收原则：传统“数据先于判断、基础决定上层、理论分层、多证据验证、动态岁运、结果可解释”具有参考性；但必须从“多流派综合评分”改造为“流派适用性路由 + 分层裁判 + 分层反馈校准”。

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

## 17. 建议代码结构

长期建议新增：

```text
engine/decision/
  models.py
  l0_wenzhen.py
  l0_context.py
  l1_school_router.py
  l2_claims.py
  l3_structure.py
  l4_events.py
  l5_timing.py
  l6_arbitration.py
  l7_report_view.py
  l8_feedback_attribution.py
  l9_calibration.py
  orchestrator.py
```

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

## 18. 分阶段落地路线

### Phase 1：立契约，不改行为

目标：先定边界，防止继续混乱。

产物：

1. L0 到 L9 数据模型草案。
2. 每层输入 / 输出 / 禁止事项。
3. 流派适用性路由规则草案。
4. 分层反馈归因规则草案。

不做：

1. 不切生产入口。
2. 不改旧报告。
3. 不删除旧 pipeline。

### Phase 2：实现 L0 问真事实账本

目标：接收问真专业文本，输出 L0 事实账本。

验收：

1. 能解析 `$BASE`。
2. 能解析 `$FOUR`。
3. 能解析 `$DY_LOOP`。
4. `_` 登记为缺失但合法。
5. 未知区块原样保留。
6. 自由文本事实单独保存。
7. 不输出命理判断。

### Phase 3：实现 L1 流派适用性路由

目标：先决定哪些流派有资格发言。

验收：

1. 每个流派都有 role。
2. 至少支持 lead、co_lead、evidence_only、abstain。
3. abstain 流派不进入后续裁判。
4. evidence_only 流派只能提供旁证。
5. 每个 role 都有 reasons 和 blockers。

### Phase 4：L2 独立命题账本

目标：被授权流派独立输出 SchoolClaim。

验收：

1. 每条 claim 有 school、domain、statement、evidence、falsifier。
2. 不输出最终综合结论。
3. 不提前融合。

### Phase 5：L3 到 L6 裁判链最小闭环

目标：先实现可追踪，不追求完美。

最小要求：

1. L3 能 pass / weaken / reject。
2. L4 能生成事件假设。
3. L5 能生成时间窗和概率。
4. L6 能处理 winner / coexist / unresolved / reject_all。

### Phase 6：L7 报告只读裁判结果

目标：报告层不再补推理。

验收：

1. 每个报告条目有链路 ID。
2. 报告句子可反查到 L0 原始事实。
3. 报告不生成无来源断语。

### Phase 7：L8 / L9 学习闭环

目标：从命中 / 失验升级到分层归因和治理动作。

验收：

1. 反馈能归因到层。
2. 反馈能更新流派适用性。
3. 反馈能更新规则或裁判策略。
4. 长期失效对象可降级、冻结、淘汰。

---

## 19. 第一证明物

最小证明物不是完整系统，而是一个内存中的 DecisionRun。

输入：一段问真专业文本。

输出：

```text
DecisionRun
- L0: ChartFactLedger
- L1: SchoolApplicabilityMatrix
- L2: 至少 3 条 SchoolClaim
- L3: 至少 3 条 StructuralVerdict
- L4: 至少 2 条 EventHypothesis
- L5: 至少 1 条 TimingProbability
- L6: 至少 1 条 ArbitrationDecision
- L7: 至少 1 条 ReportViewItem
```

验收链路：

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

如果链路不断，架构方向正确。

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

1. 确认 L0 到 L9 分层命名和职责。
2. 定义核心数据对象。
3. 定义问真专业文本 L0 输入契约。
4. 定义 SchoolApplicabilityMatrix。
5. 定义 DecisionRun 链路追踪格式。
6. 做 L0 parser 的最小实现。
7. 做 L1 rule-based router 的最小实现。
8. 做一个样例 DecisionRun。
9. 再决定是否迁移现有 v5 runner。

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
