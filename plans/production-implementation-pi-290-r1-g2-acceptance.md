# PI-290-R1 · G2 运行时契约设计独立验收裁决

> 验收实例：PI-290-R1  
> 父任务：PI-200  
> 模式：acceptance  
> 验收日期：2026-07-19  
> 裁决：**BLOCKED**

## 1. 裁决摘要

[`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md)、[`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md) 与 [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md) 已覆盖中立证据、三轨分账、五动作、竞争／反证／根源／时序、全链追溯、运行轨道分账、非原子 artifact、幂等与反馈 fail-closed 等主要设计域；但三文档共同组成的运行时契约仍存在 **3 项 High、5 项 Medium** 阻断。

依据 [`production-implementation-control.md`](production-implementation-control.md) 的阶段门及本任务“任何 High、Medium 或关键歧义均须阻断”的裁决规则，G2 **不得进入 G3**。

本裁决只验收设计，不修改或补写设计，不选择修复方案，不设计 G3 最小切片或 G5 实现计划。

## 2. 验收范围、事实源与方法

### 2.1 直接验收对象

1. [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md)
2. [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md)
3. [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md)

### 2.2 规范与现状证据

- 阶段治理：[`production-implementation-control.md`](production-implementation-control.md)
- 冻结业务语义：[`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md)
- 声明性机器附录：[`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml)
- G1 决策／冲突现状：[`production-implementation-pi-120-findings-decision-conflict-audit.md`](production-implementation-pi-120-findings-decision-conflict-audit.md)
- G1 报告／statement／feedback 现状：[`production-implementation-pi-130-report-statement-feedback-audit.md`](production-implementation-pi-130-report-statement-feedback-audit.md)
- G1 独立验收：[`production-implementation-pi-190-r2-g1-acceptance.md`](production-implementation-pi-190-r2-g1-acceptance.md)
- G1 状态校准：[`production-implementation-pi-195-r2-g1-calibration.md`](production-implementation-pi-195-r2-g1-calibration.md)

### 2.3 验收方法

- 按冻结契约优先、声明性附录次之、G2 设计不得扩张语义的顺序核验。
- 对 PI-210 → PI-220 → PI-230 的类型、枚举、稳定 ID、引用解析、nullability、非空集合与失败状态做交叉抽查。
- 对通过项只确认设计文本已表达相应边界，不声称代码、测试或生产接线已经存在。
- 对缺陷仅登记严重度、影响和解除验收条件，不给出修复设计。

## 3. 严重度口径

| 严重度 | 本次口径 |
|---|---|
| High | 冻结语义不能无损表达、正式最低充分门可能被绕过，或关键跨文档引用无法机械闭合，直接影响合法动作与可追溯性 |
| Medium | 类型未定义、字段约束自相矛盾、同一职责存在竞争类型，或上下游非空／状态约束不一致，导致实现者必须自行猜测 |
| Low | 不影响可执行语义和跨文档互操作的表述问题；本次未以 Low 单独阻断 |

## 4. 十二项验收矩阵

| # | 验收项 | 独立抽查结果 | 判定 | 关联阻断 |
|---:|---|---|---|---|
| 1 | 无冻结业务语义扩张 | 三份设计总体坚持只转录冻结字段、不得由证据数量生成业务结论、不得把现实事实回填理论根源；未发现新增卡特定业务结论。但 PI-210 对冻结输出精度的类型收窄造成语义损失，不属于安全的无损转录 | **BLOCKED** | H-01 |
| 2 | YAML 保持声明性，未内嵌算法 | [`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:9) 明确禁止可执行逻辑；PI-210/220/230 将读取、判定与追溯职责分开，未把 YAML 直接翻译成评分、权重或排序算法 | PASS | — |
| 3 | null／unresolved／absent／unknown 保真 | PI-210 明确区分 `PRESENT_VALUE`、`EXPLICIT_NULL`、`UNRESOLVED`、`ABSENT` 及 null+unresolved 并存状态，PI-220 又区分门的缺失、冲突与 evaluator unknown；但 PI-210 与 PI-220 对 unresolved 状态词表没有规范映射，跨接口仍有歧义 | **BLOCKED** | M-05 |
| 4 | validation timepoints 与 output precision 分账 | PI-210 明确两者不可互转，且保留 F09/F10 验证标签；但其输出精度引用只能承载单一 T0/T1/T2/null，无法承载 F11/F12 的结构化冻结声明 | **BLOCKED** | H-01 |
| 5 | 三轨分账 | PI-210 明确定义 chart structure、reality fact、unverified hypothesis 三轨；PI-220 规定现实门满足证据只能来自 reality fact，并禁止理论／假设冒充现实门 | PASS | — |
| 6 | 五动作失败安全且 ASK 存在 | PI-220 明确定义 OUTPUT、CONDITIONAL、ASK、ABSTAIN、HUMAN_REVIEW，并给出结构有效性和失败动作边界；PI-230 允许非输出动作无 statement set，不把 ASK 伪装成 OUTPUT | PASS | — |
| 7 | 门、竞争、反证、根源、时序接口闭合且不卡特定规则 | PI-220 提供现实门、竞争、反证、根源与时序记录，但正式契约要求的理论原局门、单家原局完整链、source gate 和破坏条件没有形成独立且不可绕过的 OUTPUT 采纳闭合条件 | **BLOCKED** | H-02 |
| 8 | 字段、来源、转换、decision、statement、feedback 全链可追溯 | PI-230 覆盖 source snapshot → normalized package → decision → statement → projections → feedback → learning eligibility；但 output precision／validation plan 引用不可解析，转换记录类型冲突，摘要缺失状态不可由声明类型表达 | **BLOCKED** | H-03、M-02、M-03 |
| 9 | production-default 与 staged／preprod 分账 | PI-230 显式区分 production-default、parallel-domain、staged L6、v5/v6 preprod、manual import，并限制跨轨边为 audit-only；与 G1 现状分账一致 | PASS | — |
| 10 | 非原子 artifact、幂等重试、反馈未知映射 fail closed | PI-230 明确 artifact set 非原子、尝试／重试与幂等键、摘要冲突、未知反馈映射不可学习及 human review；没有把文件存在等同于闭环成功 | PASS | — |
| 11 | 三文档类型和引用一致，不存在不可执行歧义 | 存在无稳定 ID 的对象被下游缩成字符串引用、未定义运行轨道类型、转换记录双类型、摘要必填与缺失状态冲突、basis 非空约束不一致及 unresolved 词表未映射 | **BLOCKED** | H-03、M-01 至 M-05 |
| 12 | 足以支撑一卡最小切片设计而不预实现十二卡 | 文档采用通用卡 ID 和声明性字段引用，没有逐卡预实现；但任一卡涉及正式最低充分门时仍可能绕门，选择 F11/F12 时又无法无损承载输出精度，因此尚不足以作为可执行的一卡切片设计输入 | **BLOCKED** | H-01、H-02、H-03 |

**矩阵结论：** 5 项 PASS，7 项 BLOCKED。通过项不能抵消任一 High 或 Medium 阻断。

## 5. 交叉接口抽查

### 5.1 PI-210 → PI-220

| 接口面 | 上游声明 | 下游消费 | 结果 |
|---|---|---|---|
| 中立 package | [`NormalizedEvidencePackage`](production-implementation-pi-210-normalized-evidence-model.md:198) | PI-220 只读端口按 package、candidate、track 和 relation 读取 | 基本闭合 |
| 三轨 | [`EvidenceTrack`](production-implementation-pi-210-normalized-evidence-model.md:222) | 现实门满足只允许 reality fact | 闭合 |
| 冻结字段状态 | [`FrozenCardFieldRef`](production-implementation-pi-210-normalized-evidence-model.md:326) | PI-220 读取字段引用和 unresolved 状态 | 部分闭合；状态词表缺规范映射 |
| 输出精度 | [`OutputPrecisionRef`](production-implementation-pi-210-normalized-evidence-model.md:364) | PI-220 在动作 envelope 中内嵌同类型 | 类型复用一致，但上游类型自身不能表达正式 YAML 的结构化值 |
| 验证计划 | [`ValidationPlanRef`](production-implementation-pi-210-normalized-evidence-model.md:358) | PI-220 在动作 envelope 中内嵌同类型或 null | 类型复用一致 |
| 正式最低充分门 | PI-210 能承载字段、关系、反证、根源与时序证据 | PI-220 主要闭合现实必要门 | 不闭合；缺少不可绕过的完整参与集合约束 |

### 5.2 PI-220 → PI-230

| 接口面 | PI-220 | PI-230 | 结果 |
|---|---|---|---|
| 动作枚举 | 五动作 | 同一五动作集合 | 闭合 |
| basis records | [`DecisionActionEnvelope.basis_record_ids`](production-implementation-pi-220-decision-interface.md:525) 为普通列表 | [`DecisionTraceRef.basis_record_ids`](production-implementation-pi-230-traceability-binding.md:305) 为非空列表 | 不一致；存在合法上游值无法进入下游的歧义 |
| 输出精度引用 | [`DecisionActionEnvelope.output_precision_ref`](production-implementation-pi-220-decision-interface.md:531) 为内嵌对象或 null | [`DecisionTraceRef.output_precision_ref`](production-implementation-pi-230-traceability-binding.md:309) 为字符串或 null | 断裂；上游对象无自身稳定 ID，字符串指向未定义 |
| 验证计划引用 | [`DecisionActionEnvelope.validation_plan_ref`](production-implementation-pi-220-decision-interface.md:532) 为内嵌对象或 null | [`DecisionTraceRef.validation_plan_ref`](production-implementation-pi-230-traceability-binding.md:310) 为字符串或 null | 断裂；同上 |
| 非输出动作 | ASK／ABSTAIN／HUMAN_REVIEW 可作为失败安全动作 | statement set 可为 null，并要求保留原因和状态 | 语义基本闭合 |
| 结构有效性 | 动作 envelope 记录结构有效性 | invalid 结果不可产生可发布 statement | 闭合 |

### 5.3 PI-210／PI-220 → PI-230 全链

| 接口面 | 抽查结果 | 判定 |
|---|---|---|
| 稳定对象引用 | package、decision result、statement 与 feedback 主对象可使用版本引用；输出精度和验证计划对象没有可解析稳定 ID | BLOCKED |
| 内容摘要 | [`VersionedObjectRef.content_digest`](production-implementation-pi-230-traceability-binding.md:245) 必填，但相邻规则又允许摘要缺失时保留对象 | BLOCKED |
| 运行轨道 | 顶层 envelope 直接给出枚举，多个子类型改用未定义的 [`RunTrack`](production-implementation-pi-230-traceability-binding.md:180) | BLOCKED |
| 转换账本 | 顶层使用 [`TransformationRecord`](production-implementation-pi-230-traceability-binding.md:160)，下文又定义字段不同的 [`TraceTransformationRecord`](production-implementation-pi-230-traceability-binding.md:447)，且未说明规范替换／适配关系 | BLOCKED |
| statement 追溯 | statement revision、basis、evidence、source locator、双投影和 feedback binding 均有明确链路 | 条件通过；依赖上述引用阻断解除 |
| 学习准入 | 未绑定、歧义、摘要未知和非原子 artifact 状态均不能静默进入学习 | PASS |

## 6. 阻断项

### H-01 · 冻结输出精度无法无损表达

- **严重度：High**
- **证据：** [`OutputPrecisionRef.declared_precision`](production-implementation-pi-210-normalized-evidence-model.md:366) 仅允许 T0、T1、T2 或 null；[`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:517) 的 F11 输出精度是含 T0/T1/T2/default_max 的映射，[`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:642) 的 F12 还是嵌套限制、允许项、必需项和 fallback 的结构化对象。
- **影响：** 正式冻结值无法经 PI-210 无损进入 PI-220/PI-230；实现者只能丢字段、另行推断或绕开声明类型，违反冻结语义保真与声明性读取边界。
- **解除验收条件：** 三文档必须共同证明 F01–F12 的冻结输出精度值可无损表示、可版本追溯，并继续与 validation timepoints 分账。此处只规定验收结果，不指定设计方案。

### H-02 · 正式最低充分参与集合未成为不可绕过的决策闭合条件

- **严重度：High**
- **证据：** [`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:50) 要求单家原局完整链、大运阶段、具体事件流年触发、现实功能硬门，以及本家破坏条件或跨材料有效反证。PI-220 的 [`GateEvaluationSet`](production-implementation-pi-220-decision-interface.md:239) 明确闭合现实门，并规定满足证据只能来自 reality fact；但未看到理论原局门、source gate、单家链完整性和破坏条件作为独立、必需且参与 OUTPUT 采纳性的统一记录约束。
- **影响：** 结构上有效的 OUTPUT 可能只证明现实门和局部账本存在，却未证明正式契约要求的全套参与角色闭合；这会把“接口有字段”误当成“业务门已通过”。
- **解除验收条件：** 必须能够机械证明正式最低充分参与集合中的每一角色均有独立状态、证据／缺证／冲突引用和失败安全动作约束，且不内嵌任一卡具体判断算法。

### H-03 · 输出精度／验证计划跨文档引用不可解析

- **严重度：High**
- **证据：** PI-220 将 [`DecisionActionEnvelope.output_precision_ref`](production-implementation-pi-220-decision-interface.md:531) 与 [`DecisionActionEnvelope.validation_plan_ref`](production-implementation-pi-220-decision-interface.md:532) 定义为内嵌对象；PI-230 将对应字段定义为字符串引用，见 [`DecisionTraceRef.output_precision_ref`](production-implementation-pi-230-traceability-binding.md:309) 与 [`DecisionTraceRef.validation_plan_ref`](production-implementation-pi-230-traceability-binding.md:310)。PI-210 的 [`OutputPrecisionRef`](production-implementation-pi-210-normalized-evidence-model.md:364) 和 [`ValidationPlanRef`](production-implementation-pi-210-normalized-evidence-model.md:358) 均无自身稳定 ID。
- **影响：** PI-230 无法仅按契约机械解析字符串指向哪个对象、版本或字段快照；全链追溯在 decision → statement 处断开。
- **解除验收条件：** 上下游必须对对象身份、引用形式、版本／摘要及 null 语义形成单一、可机械校验的契约。

### M-01 · 运行轨道类型未定义

- **严重度：Medium**
- **证据：** PI-230 顶层 [`TraceEnvelope.track`](production-implementation-pi-230-traceability-binding.md:150) 直接列出枚举，子类型使用 [`RunTrack`](production-implementation-pi-230-traceability-binding.md:180)，文档未给出该类型的规范定义或与顶层枚举的等价声明。
- **影响：** 不同实现可能采用不同枚举、大小写或轨道集合，破坏跨 artifact 校验。
- **解除验收条件：** 所有轨道字段必须引用同一明确类型并具备一致枚举边界。

### M-02 · 转换记录存在竞争类型且顶层职责不明

- **严重度：Medium**
- **证据：** [`TraceEnvelope.transformations`](production-implementation-pi-230-traceability-binding.md:160) 使用 PI-210 名称的 TransformationRecord；PI-230 又声明复用同一语义后定义字段集合不同的 [`TraceTransformationRecord`](production-implementation-pi-230-traceability-binding.md:447)。
- **影响：** 实现者无法确定顶层列表的实际元素 schema，也无法判断 source/target versioned refs、dropped object refs 等字段是否必需。
- **解除验收条件：** 顶层转换账本必须只有一个规范元素契约，或存在无歧义、可验证的显式关系。

### M-03 · 摘要必填与摘要缺失可保留相互矛盾

- **严重度：Medium**
- **证据：** [`VersionedObjectRef.content_digest`](production-implementation-pi-230-traceability-binding.md:245) 为必填 DigestRef；[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:257) 又允许摘要缺失时保留对象用于人工审计。
- **影响：** 声明类型无法构造文档明确允许的状态；实现者只能违反字段必填或丢弃人工审计对象。
- **解除验收条件：** 类型必须能无歧义表达摘要存在与缺失两种状态，并保持缺失时不得安全跨文件绑定的 fail-closed 语义。

### M-04 · basis record 非空约束上下游不一致

- **严重度：Medium**
- **证据：** [`DecisionActionEnvelope.basis_record_ids`](production-implementation-pi-220-decision-interface.md:525) 是普通列表；[`DecisionTraceRef.basis_record_ids`](production-implementation-pi-230-traceability-binding.md:305) 和 [`StandardStatement.basis_record_ids`](production-implementation-pi-230-traceability-binding.md:355) 要求非空。
- **影响：** PI-220 允许的动作 envelope 可能无法进入 PI-230；尤其 ASK 或失败动作是否必须引用非空 basis 没有统一契约。
- **解除验收条件：** 每种动作的 basis 基数要求须在 PI-220 与 PI-230 一致，并能由结构校验器机械判定。

### M-05 · unresolved 状态词表缺少跨接口规范映射

- **严重度：Medium**
- **证据：** PI-210 冻结字段使用 `UNRESOLVED` 并另行表达 null+unresolved 并存；PI-220 门状态使用 `UNKNOWN`，字段问题与 unresolved 记录又使用不同状态语汇，但三文档未给出哪些状态是来源事实、哪些是 evaluator 状态及其禁止转换矩阵。
- **影响：** 适配器可能把来源未决、字段缺失和判定器未知相互折叠，削弱用户要求的 null／unresolved／absent／unknown 保真。
- **解除验收条件：** 跨接口必须具有显式、无损且 fail-closed 的状态对应规则，并禁止把来源事实状态静默改写成 evaluator 状态或默认值。

## 7. 非阻断通过项

以下能力在设计层已达到本轮验收要求，但不改变总体 BLOCKED：

1. YAML 保持声明性，未被定义为评分／排序算法载体。
2. 三轨证据账本及现实门只接受现实事实支持的边界清楚。
3. 五动作完整包含 ASK，并保留 CONDITIONAL、ABSTAIN、HUMAN_REVIEW 的失败安全出口。
4. production-default、parallel-domain、staged L6、v5/v6 preprod 与 manual import 分账清楚。
5. source、field、relation、decision、statement revision、双投影、feedback 与 learning eligibility 的目标链路完整。
6. 非原子 artifact 集合、幂等尝试、摘要冲突、重复摄入和未知反馈映射均采用 fail-closed 口径。
7. 设计使用通用卡身份和字段路径，没有预先实现十二卡的具体算法。

## 8. 一卡最小切片可设计性裁决

**当前结论：不具备进入 G3 的充分条件。**

三份设计已经提供一卡切片所需的大部分通用形状，但任意切片仍会遇到以下不可执行选择：

- 若选择 F11 或 F12，冻结输出精度不能由 PI-210 类型无损承载；
- 若选择其他卡，正式最低充分参与集合仍没有不可绕过的决策闭合证明；
- 任一卡的 decision 到 statement 追溯都会遇到输出精度／验证计划字符串引用无稳定目标的问题；
- 实现者还必须自行决定运行轨道类型、转换记录 schema、摘要缺失表示及 basis 非空规则。

因此，本裁决不选择卡片、不定义切片、不提出 G3 方案。

## 9. 允许与禁止的下一步

### 9.1 允许

1. 将本裁决作为 PI-290-R1 的独立 G2 验收记录。
2. 由获授权的 G2 设计流程处理第 6 节阻断项，并形成新的、可独立复验的设计版本。
3. 后续复验继续以冻结契约与声明性 YAML 为事实源，逐项验证 H-01 至 M-05 的解除条件。
4. 保留 G3、G4、G5 的既有依赖阻断，直至新的 G2 独立验收为 PASS。

### 9.2 禁止

1. 不得把本次 BLOCKED 改写为“基本通过”“附条件通过”或允许进入 G3。
2. 不得由本验收文件修改 PI-210、PI-220、PI-230、总控、handoff、冻结契约或 mapping。
3. 不得把本验收列出的解除条件当成已批准的修复设计。
4. 不得启动、设计或实现 G3 一卡切片。
5. 不得设计 G5 实现计划、修改生产默认行为或预先实现 F01–F12。
6. 不得以通过项抵消任何 High、Medium 或关键歧义。

## 10. 自检

- [x] 由 PI-290-R1 当前实例独立完成，未递归委派。
- [x] 已读取总控、PI-210、PI-220、PI-230、冻结契约、声明性 YAML 及必要 G1 审计。
- [x] 已覆盖用户指定的十二项验收矩阵。
- [x] 已抽查 PI-210 → PI-220 → PI-230 的类型、稳定 ID、引用、nullability 与非空集合约束。
- [x] 已区分冻结业务语义、声明性数据、运行时判定和追溯职责。
- [x] 已区分 production-default、parallel-domain、staged L6 与 v5/v6 preprod。
- [x] 已检查非原子 artifact、幂等重试和未知反馈映射 fail-closed。
- [x] 发现 High／Medium 后按规则裁决为 BLOCKED，未自行修复设计。
- [x] 未设计 G3 或 G5，未选择一卡切片。
- [x] 未运行代码或测试，未声称测试通过。
- [x] 未修改总控、handoff、三份设计、冻结契约、mapping 或其他文件。
- [x] 本次唯一写入目标为 [`production-implementation-pi-290-r1-g2-acceptance.md`](production-implementation-pi-290-r1-g2-acceptance.md)。

## 11. 最终裁决

**BLOCKED** — PI-210、PI-220、PI-230 尚未共同形成可进入 G3 的无歧义运行时契约设计。当前存在 3 项 High 与 5 项 Medium 阻断；在全部解除并通过新的独立 G2 验收前，G3 必须保持阻断。