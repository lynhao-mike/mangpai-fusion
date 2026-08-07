# PI-290-R2 · G2 运行时契约设计独立复验裁决

> 复验实例：PI-290-R2  
> 父任务：PI-200  
> 模式：acceptance  
> 复验日期：2026-07-19  
> 与整改实例：PI-260-R1 分离  
> 最终裁决：**BLOCKED**

## 1. 裁决摘要

本实例对 [`production-implementation-pi-290-r1-g2-acceptance.md`](production-implementation-pi-290-r1-g2-acceptance.md:1) 登记的 H-01～H-03、M-01～M-05 进行了独立复验，并重新执行原十二项 G2 验收矩阵。

复验结果：

- H-01、H-02 已解除；
- M-01～M-05 已解除；
- H-03 **未完全解除**：三文档已经统一声明身份、版本、摘要与非空引用解析规则，但没有唯一规定引用本身为 null 的语义，仍可能把“冻结声明存在且其声明值为显式 null”与“声明引用不存在”折叠；
- 新发现 1 项关键歧义，归入 H-03 的残余问题，不另行重复计数；
- 十二项矩阵结果为 8 项 PASS、4 项 BLOCKED。

按照 [`production-implementation-control.md`](production-implementation-control.md:1) 的阶段门口径及本任务“任何 High、Medium 或关键歧义均须阻断”的规则，G2 最终裁决为 **BLOCKED**，不得进入 G3。

本复验只登记证据与裁决，没有修改或补写三份设计，没有给出修复方案，没有设计 G3 或 G5。

## 2. 复验范围、事实源与方法

### 2.1 直接复验对象

1. [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:1)
2. [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:1)
3. [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:1)

### 2.2 治理、冻结语义与现状证据

- 阶段治理：[`production-implementation-control.md`](production-implementation-control.md:1)
- R1 验收基线：[`production-implementation-pi-290-r1-g2-acceptance.md`](production-implementation-pi-290-r1-g2-acceptance.md:1)
- 正式冻结契约：[`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:1)
- 声明性机器附录：[`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:1)
- G1 决策／冲突审计：[`production-implementation-pi-120-findings-decision-conflict-audit.md`](production-implementation-pi-120-findings-decision-conflict-audit.md:1)
- G1 报告／statement／feedback 审计：[`production-implementation-pi-130-report-statement-feedback-audit.md`](production-implementation-pi-130-report-statement-feedback-audit.md:1)
- G1 独立验收：[`production-implementation-pi-190-r2-g1-acceptance.md`](production-implementation-pi-190-r2-g1-acceptance.md:1)
- G1 状态校准：[`production-implementation-pi-195-r2-g1-calibration.md`](production-implementation-pi-195-r2-g1-calibration.md:1)

### 2.3 复验方法

- 以正式 Markdown 契约优先、声明性 YAML 次之、G2 设计不得扩张冻结语义为事实源顺序。
- 对 R1 八项阻断逐项检查整改后类型、基数、枚举、引用、nullability 与 fail-closed 语义。
- 对 PI-210 → PI-220 → PI-230 做交叉接口抽查，并搜索旧竞争类型、裸字符串引用、普通 basis 列表和状态折叠残余。
- 对通过项只确认设计文本足以形成接口契约，不声称代码、测试或生产接线已经存在。
- 对残余问题只登记严重度、影响和复验解除条件，不自行修复。

## 3. R1 阻断项逐项复验

| 编号 | R1 问题 | 整改后机械证据 | 复验结论 |
|---|---|---|---|
| H-01 | 冻结输出精度无法无损表达 | [`OutputPrecisionRef`](production-implementation-pi-210-normalized-evidence-model.md:394) 的声明值改为 opaque JSON 或 null；[`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:402) 明确逐值保留 F01–F10 的 null、F11 映射及 F12 嵌套对象；[`ValidationPlanRef`](production-implementation-pi-210-normalized-evidence-model.md:387) 独立保存验证时点；[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:789) 再次禁止抽取、展平或互映 | **已解除** |
| H-02 | 最低充分参与集合未成为不可绕过的决策闭合条件 | [`ParticipationRole`](production-implementation-pi-220-decision-interface.md:298) 覆盖正式共同五角色并增加每卡统一 source gate；[`MinimumSufficientParticipationSet`](production-implementation-pi-220-decision-interface.md:309) 与 [`ParticipationRoleRecord`](production-implementation-pi-220-decision-interface.md:319) 要求逐角色独立记录；[`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:337) 禁止删减、聚合或互补；[`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:342) 规定角色缺失或为 missing、conflict、unknown 时 OUTPUT envelope 必须 invalid | **已解除** |
| H-03 | 输出精度／验证计划跨文档引用不可解析 | [`FrozenDeclarationRef`](production-implementation-pi-210-normalized-evidence-model.md:378) 已统一身份、类型、卡 ID、契约版本、声明 schema 版本和摘要；[`DecisionActionEnvelope`](production-implementation-pi-220-decision-interface.md:581)、[`DecisionTraceRef`](production-implementation-pi-230-traceability-binding.md:339) 与 [`StandardStatement`](production-implementation-pi-230-traceability-binding.md:378) 均复用该类型；非 null 引用可机械解析。但三个下游字段均仍允许引用本身为 null，而 PI-210 对 output precision 始终返回含稳定引用的 [`OutputPrecisionRef`](production-implementation-pi-210-normalized-evidence-model.md:972)，即使冻结声明值为显式 null。下游未规范规定何时允许把 output precision 引用本身置 null，也未禁止用引用 null 代替显式 null 声明 | **未解除** |
| M-01 | 运行轨道类型未定义 | [`RunTrack`](production-implementation-pi-210-normalized-evidence-model.md:99) 定义唯一五值枚举；[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:88) 明确直接复用且不扩展；所有 track 字段使用同一类型 | **已解除** |
| M-02 | 转换记录存在竞争类型 | [`TransformationRecord`](production-implementation-pi-210-normalized-evidence-model.md:519) 被声明为三文档唯一规范转换契约；[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:480) 明确不存在 TraceTransformationRecord 或其他竞争元素类型，顶层、边、投影及查询端口均指向同一 transformation ID | **已解除** |
| M-03 | 摘要必填与摘要缺失可保留冲突 | [`DigestBinding`](production-implementation-pi-230-traceability-binding.md:277) 用 present／missing 判别联合表达两种状态；missing 分支要求摘要为 null 且有 issue ID；[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:295) 明确缺失时只可保留人工审计，不得发布 statement、建立 bound feedback 或进入学习 | **已解除** |
| M-04 | basis record 非空约束上下游不一致 | [`BasisRecordIds`](production-implementation-pi-220-decision-interface.md:116) 是非空字符串列表；五动作 envelope 统一使用该类型并在 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:659) 逐动作要求非空；PI-230 直接复用同一类型，见 [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:107) | **已解除** |
| M-05 | 来源 unresolved 与 evaluator unknown 等状态缺规范映射 | [`SourceFieldState`](production-implementation-pi-210-normalized-evidence-model.md:333) 与 [`FieldEvaluatorState`](production-implementation-pi-220-decision-interface.md:113) 已分为不同类型；[`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:528) 给出允许组合和禁止折叠矩阵；矩阵外组合 blocking fail closed；PI-230 逐值复用并禁止反向创造来源状态，见 [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:789) | **已解除** |

### 3.1 阻断关闭统计

- High：2 项解除，1 项未解除。
- Medium：5 项全部解除。
- R1 八项合计：7 项解除，1 项未解除。

## 4. H-03 残余关键歧义

### H-03-R · 声明值 null 与声明引用 null 未形成唯一跨文档语义

- **严重度：High／关键歧义。** 该问题直接影响冻结声明保真和 decision → statement 追溯，因此不能降为措辞问题。
- **上游事实：** [`get_output_precision_ref()`](production-implementation-pi-210-normalized-evidence-model.md:972) 返回非 nullable 的 [`OutputPrecisionRef`](production-implementation-pi-210-normalized-evidence-model.md:394)。其内部 [`FrozenDeclarationRef`](production-implementation-pi-210-normalized-evidence-model.md:378) 必填，而声明值可为 null，并由 [`SourceFieldState`](production-implementation-pi-210-normalized-evidence-model.md:333) 区分 explicit null 与 null+unresolved。
- **下游事实：** [`DecisionActionEnvelope.output_precision_ref`](production-implementation-pi-220-decision-interface.md:599)、[`DecisionTraceRef.output_precision_ref`](production-implementation-pi-230-traceability-binding.md:347) 和 [`StandardStatement.output_precision_ref`](production-implementation-pi-230-traceability-binding.md:400) 均允许引用本身为 null。
- **缺失规则：** [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:607) 只规定非 null 引用如何解析；[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:415) 只要求引用为 null 时按上游状态保留，但没有定义 null 引用代表声明不存在、动作不适用、未读取、引用断裂还是声明值为 null。
- **可观察歧义：** 对 F01–F10，合规生产者既可能保留非 null 的 OUTPUT_PRECISION 声明引用并解析到 explicit null，也可能把动作 envelope 的引用字段直接写 null；两者在当前下游 schema 中都可构造，但 provenance、摘要验证及 null/unresolved 保真能力不同。
- **validation plan 对照：** [`get_validation_plan_ref()`](production-implementation-pi-210-normalized-evidence-model.md:971) 本身允许不存在时返回 null；这与 output precision 的非 nullable 返回签名不相同。PI-220/PI-230 却对两类引用使用相同 nullable 外形，未保存这项上游语义差异。
- **影响：** 实现者必须自行猜测何时引用可为 null；显式 null 冻结声明可能失去 declaration ID、版本和摘要，H-01 的值保真因此无法保证沿 PI-220／PI-230 全链成立。
- **解除验收条件：** 三文档须对两类声明分别给出唯一且一致的引用 null 规则，并能机械区分“声明存在而声明值为 null”与“声明对象不存在／不适用／不可解析”。本条件只描述验收结果，不指定修复方案。

## 5. 机械专项核对

### 5.1 opaque output precision 与 validation timepoints

| 核对点 | 证据 | 判定 |
|---|---|---|
| F01–F10 null 保真 | [`OutputPrecisionRef`](production-implementation-pi-210-normalized-evidence-model.md:394) 接受 null，并以独立来源状态保存 | PASS |
| F11 映射保真 | [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:404) 明确保留 T0、T1、T2、default max 全映射 | PASS |
| F12 嵌套对象保真 | 同一规范明确保留 allowed、requires、fallback 等嵌套结构，不抽取或展平 | PASS |
| 与验证时点分账 | [`ValidationPlanRef`](production-implementation-pi-210-normalized-evidence-model.md:387) 和 [`OutputPrecisionRef`](production-implementation-pi-210-normalized-evidence-model.md:394) 使用不同声明类型、ID 与字段；[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:799) 禁止 F09/F10 验证时点成为输出精度 | PASS |
| 跨链 null 引用保真 | 声明对象中的 null 可保真，但下游引用本身 nullable 的语义未闭合 | **BLOCKED** |

### 5.2 最低充分参与集合与 F12 source gate

正式共同最低集合的五类角色均由 [`ParticipationRole`](production-implementation-pi-220-decision-interface.md:298) 独立表达，每卡统一 source gate 作为第六个记录角色加入。角色集合不能用数量聚合或其他角色证据补齐，OUTPUT 必须逐项检查。

F12 的 source gate 在声明性附录中为 null 且列入 unresolved；依据 [`SourceFieldState`](production-implementation-pi-210-normalized-evidence-model.md:333) 应保留为 null+unresolved 并进入独立 source gate 角色记录。依据 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:339)，它不能静默成为 satisfied；处于 unknown、missing 或 conflict 时，依据 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:342) 必须使 OUTPUT invalid。未发现可绕过路径。

### 5.3 唯一类型、摘要、basis 与状态分账

| 专项 | 结果 | 机械结论 |
|---|---|---|
| 唯一 [`RunTrack`](production-implementation-pi-210-normalized-evidence-model.md:99) | 五值枚举由 PI-210 规范定义，PI-230 只复用 | PASS |
| 唯一 [`TransformationRecord`](production-implementation-pi-210-normalized-evidence-model.md:519) | PI-230 明确不存在竞争类型；“扩展”只通过版本化 trace node 补快照信息，不另建转换 schema | PASS |
| [`DigestBinding`](production-implementation-pi-230-traceability-binding.md:277) 缺失 fail closed | missing 可构造且禁止 statement 发布、bound feedback 与学习 | PASS |
| 五动作 [`BasisRecordIds`](production-implementation-pi-220-decision-interface.md:116) 基数 | 五动作、decision trace、standard statement 均为同一非空类型 | PASS |
| [`SourceFieldState`](production-implementation-pi-210-normalized-evidence-model.md:333) 与 [`FieldEvaluatorState`](production-implementation-pi-220-decision-interface.md:113) | 分字段记录，有允许组合和禁止折叠矩阵，矩阵外 blocking fail closed | PASS |

## 6. PI-210 → PI-220 → PI-230 交叉接口复验

| 接口面 | PI-210 | PI-220 | PI-230 | 复验结果 |
|---|---|---|---|---|
| 三轨证据 | 记录恰属一个 evidence track | 现实门满足只接受 reality fact | 仅追溯，不改轨 | PASS |
| 冻结字段状态 | 五态来源事实 | 独立 evaluator 五态与禁止折叠矩阵 | 同时保存两种状态 | PASS |
| 输出精度值 | opaque JSON 或 null，无损声明对象 | 只保存稳定声明引用 | decision／statement 逐值复用引用 | 值类型 PASS；引用 null 语义 BLOCKED |
| 验证计划 | 独立 validation plan 声明 | 独立稳定声明引用 | 与 output precision 永久分账 | PASS；但与 output precision 共享 nullable 外形造成 H-03-R 对照歧义 |
| 最低充分参与集合 | 提供分轨证据、字段、反证、根源和时序 | 六角色逐项记录并约束 OUTPUT | 追溯 action basis 和角色记录 ID | PASS |
| 运行轨道 | 唯一 [`RunTrack`](production-implementation-pi-210-normalized-evidence-model.md:99) | 适配边界按同一轨道集合说明 | 所有 track 字段直接复用 | PASS |
| 转换账本 | 唯一 [`TransformationRecord`](production-implementation-pi-210-normalized-evidence-model.md:519) | 适配 envelope 使用同一列表元素 | 顶层、边、投影、查询均指向同一 ID | PASS |
| basis | PI-210 不选择动作 | 五动作统一非空 basis | decision trace 与 statement 复用同一非空类型 | PASS |
| 摘要状态 | 冻结声明引用摘要必填 | 非 null 声明引用须摘要一致 | 通用对象用 [`DigestBinding`](production-implementation-pi-230-traceability-binding.md:277) 表达 present／missing | PASS |
| statement／feedback | 提供来源和转换链 | 产生 action／basis／issue | statement revision、双投影、feedback binding 与 learning eligibility 闭合 | 条件 PASS；依赖 H-03-R 解除 |

## 7. 完整十二项 G2 验收矩阵

| # | 验收项 | R2 独立复验结果 | 判定 | 关联阻断 |
|---:|---|---|---|---|
| 1 | 无冻结业务语义扩张 | opaque 输出精度逐值保留；三文档继续禁止从 YAML 文本、证据数量或旧轨道结果生成新业务结论；未新增卡特定判词 | PASS | — |
| 2 | YAML 保持声明性，未内嵌算法 | 声明读取、判定结果承载和追溯职责分开；没有评分、权重、排序、优先级或自然语言条件编译协议 | PASS | — |
| 3 | null／unresolved／absent／unknown 保真 | 来源五态与 evaluator 五态已有明确允许组合和禁止折叠矩阵；但 output precision 的声明值 null 仍可能被下游引用 null 折叠 | **BLOCKED** | H-03-R |
| 4 | validation timepoints 与 output precision 分账 | 两类值使用不同声明类型、稳定 ID、来源字段和只读端口；F09/F10 验证标签不得转换为输出精度；F11/F12 输出精度完整对象可保留 | PASS | — |
| 5 | 三轨分账 | chart structure、reality fact、unverified hypothesis 各自独立；现实门满足只接受 reality fact | PASS | — |
| 6 | 五动作失败安全且 ASK 存在 | OUTPUT、CONDITIONAL、ASK、ABSTAIN、HUMAN_REVIEW 使用一一对应 payload、非空 basis 和结构禁入条件；unknown 不是第六动作 | PASS | — |
| 7 | 门、竞争、反证、根源、时序接口闭合且不卡特定规则 | 最低充分五角色加每卡 source gate 均独立记录；OUTPUT 不可绕过；竞争、反证、根源和时序保持引用式、非算法化 | PASS | — |
| 8 | 字段、来源、转换、decision、statement、feedback 全链可追溯 | 主链、唯一转换记录、版本摘要、statement revision、双投影和反馈准入均已定义；但显式 null 声明可能在 decision envelope 处失去稳定声明引用 | **BLOCKED** | H-03-R |
| 9 | production-default 与 staged／preprod 分账 | 唯一运行轨道枚举覆盖 production default、parallel domain、staged L6、v5/v6 preprod、manual import；跨轨只允许 audit-only | PASS | — |
| 10 | 非原子 artifact、幂等重试、反馈未知映射 fail closed | artifact 集合状态、重试 identity、摘要冲突、重复摄入、unknown／unmapped feedback 和学习准入均 fail closed | PASS | — |
| 11 | 三文档类型和引用一致，不存在不可执行歧义 | RunTrack、TransformationRecord、DigestBinding、BasisRecordIds 和双状态类型已经一致；FrozenDeclarationRef 的引用 null 语义仍不唯一 | **BLOCKED** | H-03-R |
| 12 | 足以支撑一卡最小切片设计而不预实现十二卡 | 通用卡身份、角色、证据、动作和追溯接口已具备，且未预实现十二卡；但实现任一卡时仍需自行决定 output precision 引用本身何时可为 null，尚不足以无歧义进入 G3 | **BLOCKED** | H-03-R |

**矩阵统计：** 8 项 PASS、4 项 BLOCKED。任何通过项均不能抵消 H-03-R。

## 8. 非阻断通过项

以下整改已达到本轮设计验收要求，但不改变总体 BLOCKED：

1. 冻结 output precision 可以无损保存 null、标量、映射和嵌套对象。
2. validation timepoints 与 output precision 的声明类型、字段和只读接口永久分账。
3. 最低充分共同五角色和每卡 source gate 均有独立状态、证据／缺证／冲突引用及 OUTPUT 禁入规则。
4. F12 的 unresolved source gate 不能静默满足或绕过 OUTPUT。
5. RunTrack 只有一个规范枚举。
6. TransformationRecord 只有一个规范元素契约。
7. DigestBinding 可表达摘要存在／缺失，且 missing 状态 fail closed。
8. 五动作统一使用非空 BasisRecordIds。
9. 来源状态与 evaluator 状态禁止静默折叠。
10. 三轨、五动作、运行轨道、非原子 artifact、幂等、反馈和学习准入的既有通过项未被整改破坏。

## 9. G2 跨门裁决

**裁决：不允许跨门。**

理由：H-03 的稳定引用身份、版本和摘要部分虽已修复，但 nullability 仍没有形成跨 PI-210／PI-220／PI-230 的唯一语义。该歧义可以让显式 null 冻结声明在 action／statement 链路中丢失声明身份和摘要，直接破坏冻结值保真与 provenance。依据 fail-closed 口径，不能裁为“基本通过”或“附条件通过”。

在新的独立验收明确确认 H-03-R 解除之前：

- G2 保持 **BLOCKED**；
- G3、G4、G5 继续保持依赖阻断；
- F01–F12 implementation 继续保持 false；
- 本文不选择一卡，不定义最小切片。

## 10. 允许与禁止的下一步

### 10.1 允许

1. 将本文作为 PI-290-R2 独立复验记录。
2. 由获授权且与本验收实例分离的 G2 整改流程处理 H-03-R。
3. 整改后启动新的独立 G2 复验，至少机械核对两类声明各自的引用 null 语义、显式 null 值保真、版本／摘要解析和 decision → statement 同一性。
4. 保留本次已关闭 H-01、H-02、M-01～M-05 的证据，后续复验仍须检查其未回归。
5. 继续保持 G3、G4、G5 的既有阻断。

### 10.2 禁止

1. 不得把本次 BLOCKED 改写为基本通过、附条件通过或允许进入 G3。
2. 不得由本验收文件修改 [`production-implementation-control.md`](production-implementation-control.md:1)、handoff、PI-210、PI-220、PI-230、冻结契约、YAML、生产代码、测试或数据。
3. 不得由本实例修复 H-03-R，本文的解除验收条件不构成修复设计。
4. 不得启动、设计或实现 G3 一卡切片。
5. 不得设计 G5 实现计划或改变 production-default 行为。
6. 不得把 FrozenDeclarationRef 或 CardIdentityRef 的存在解释为 F01–F12 runtime consumer 已实现。
7. 不得以七项已关闭的 R1 阻断抵消一个残余 High／关键歧义。

## 11. 自检

- [x] 当前实例为 PI-290-R2，与 PI-260-R1 整改实例分离。
- [x] 未递归委派。
- [x] 已读取总控、R1 验收、整改后 PI-210／220／230、冻结契约、声明性 YAML 与必要 G1 审计。
- [x] 已逐项复验 H-01～H-03、M-01～M-05。
- [x] 已机械核对 opaque output precision、validation timepoints 分账、最低充分参与角色、OUTPUT 不可绕过和 F12 source gate。
- [x] 已核对 FrozenDeclarationRef 的身份、类型、版本、摘要与 nullability。
- [x] 已核对唯一 RunTrack、唯一 TransformationRecord、DigestBinding missing fail closed、五动作 BasisRecordIds 基数及来源／evaluator 禁止折叠矩阵。
- [x] 已重新执行完整十二项 G2 验收矩阵及交叉接口抽查。
- [x] 发现 H-03-R 后按规则裁决 BLOCKED，未自行修复。
- [x] 未运行代码或测试，未声称实现或测试通过。
- [x] 未设计 G3 或 G5，未选择一卡切片。
- [x] 未修改总控、handoff、三份设计、冻结契约、YAML、生产文件或其他文档。
- [x] 本次唯一创建文件为 [`production-implementation-pi-290-r2-g2-reacceptance.md`](production-implementation-pi-290-r2-g2-reacceptance.md:1)。

## 12. 最终裁决

**BLOCKED** — R1 的 H-01、H-02 与 M-01～M-05 已解除，但 H-03 尚有“冻结声明值 null 与声明引用 null 未唯一分账”的 High／关键歧义。完整十二项矩阵为 8 项 PASS、4 项 BLOCKED。G2 不得跨门，G3、G4、G5 必须继续保持阻断，直至整改后通过新的独立 G2 验收。
