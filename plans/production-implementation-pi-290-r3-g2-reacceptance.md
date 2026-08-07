# PI-290-R3：G2 独立复验与跨门裁决

- task_id：PI-290-R3
- parent_task_id：PI-200
- 验收实例：独立 acceptance／re-review
- 验收对象：整改后的 PI-210、PI-220、PI-230 运行时契约设计
- 验收日期：2026-07-19
- 最终裁决：**PASS**

## 1. 验收范围与边界

本实例与整改实例及 PI-290-R2 分离，直接读取整改后的三份 G2 设计与冻结事实源，不以整改者自述或上一轮裁决代替机械核验。

本次只完成以下工作：

1. 复验 H-03-R 是否解除；
2. 检查 R1 已关闭的 H-01、H-02、M-01～M-05 是否无回归；
3. 重跑完整十二项 G2 验收矩阵；
4. 对 G2 作 PASS 或 BLOCKED 二值裁决。

本次不修改设计，不实现代码，不设计 G3／G5，不选择一卡，不改变 production-default 行为，也不声称 runtime consumer、renderer、feedback fanout 或生产接线已经存在。

## 2. 直接事实源

本实例直接核对以下事实源：

1. [`production-implementation-control.md`](production-implementation-control.md:1)：阶段依赖、独立验收和 fail-closed 治理边界；
2. [`production-implementation-pi-290-r1-g2-acceptance.md`](production-implementation-pi-290-r1-g2-acceptance.md:50)：十二项矩阵及 H-01～H-03、M-01～M-05 原始解除条件；
3. [`production-implementation-pi-290-r2-g2-reacceptance.md`](production-implementation-pi-290-r2-g2-reacceptance.md:128)：仅作为 H-03-R 历史问题边界和无回归检查清单，不作为本轮结论来源；
4. [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:387)：规范化证据、冻结声明身份与声明引用存在性契约；
5. [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:599)：decision action envelope 与声明 binding 消费约束；
6. [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:335)：decision → trace → statement 追溯、artifact、feedback 与 learning 约束；
7. [`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:24)：冻结业务语义、缺失字段不得反推及 F01–F12 正式契约；
8. [`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:7)：声明性机器镜像、禁止推断与禁止可执行逻辑。

未以历史 handoff、旧计划或 runtime 实现现状替代上述设计事实源。

## 3. 验收方法与判定纪律

采用以下机械方法：

1. **类型闭合检查：** 对 PI-210 定义、PI-220 消费、PI-230 追溯逐字段核对类型、基数、判别分支和禁止状态；
2. **冻结样本检查：** 用 YAML 中 null、F09／F10 validation timepoints、F11 映射和 F12 嵌套 output precision 检查无损表达与分账；
3. **同一性检查：** 对 decision → trace → statement 的 presence、引用身份、类型、卡 ID、契约版本、声明 schema 版本和摘要逐项核对；
4. **失败分支检查：** 分别检查 ABSENT、NOT_APPLICABLE、UNAVAILABLE、UNRESOLVABLE，禁止把任一分支解释为声明值 null；
5. **回归检查：** 按 R1 每项阻断的解除条件检查当前三文档，不沿用 R2 的通过结论；
6. **矩阵重跑：** 十二项均单独裁决；任何 High、Medium 或关键歧义均令总体 BLOCKED，不采用附条件 PASS。

## 4. H-03-R 专项机械复验

### 4.1 唯一声明身份与存在性契约

PI-210 定义的稳定声明引用包含声明 ID、声明类型、卡 ID、契约版本、声明 schema 版本与内容摘要，见 [`FrozenDeclarationRef`](production-implementation-pi-210-normalized-evidence-model.md:369)。三文档唯一的声明引用存在性契约是 [`FrozenDeclarationBinding`](production-implementation-pi-210-normalized-evidence-model.md:387)，它是封闭判别联合，并明确禁止裸 null、空对象、缺字段或默认枚举代替分支，见 [`FrozenDeclarationBinding`](production-implementation-pi-210-normalized-evidence-model.md:429)。

机械核对结果：PI-220 的 [`DecisionActionEnvelope`](production-implementation-pi-220-decision-interface.md:599) 和 PI-230 的 [`DecisionTraceRef`](production-implementation-pi-230-traceability-binding.md:347)、[`StandardStatement`](production-implementation-pi-230-traceability-binding.md:400) 均将 output precision 与 validation plan 定义为必填 binding；未继续使用 R2 所阻断的 nullable 引用外形。

### 4.2 五分支真值表

| presence 分支 | 必需内容 | 禁止内容／解释 | 下游效果 | 机械判定 |
|---|---|---|---|---|
| RESOLVED | 非 null 的完整稳定 ref | 不得缺 ref；不得把所引用声明的值 null 改写为引用缺失 | 可按身份、类型、卡、版本、schema、摘要精确解析 | PASS |
| ABSENT | 固定的 declaration-not-present 原因 | 不得携带 ref；不得解释为声明值 null | 保留“上游确无声明”事实 | PASS |
| NOT_APPLICABLE | 固定的 declaration-not-applicable 原因 | 不得携带 ref；不得解释为声明值 null | 保留“明确不适用”事实 | PASS |
| UNAVAILABLE | 未读取／来源不可用原因和非空 issue | 不得伪装成 absent、resolved null 或成功消费 | envelope／trace／statement fail closed | PASS |
| UNRESOLVABLE | attempted ref、解析失败原因和非空 issue | 不得丢失尝试身份；不得伪装成值 null | envelope／trace／statement fail closed | PASS |

证据：五分支及字段约束见 [`FrozenDeclarationBinding`](production-implementation-pi-210-normalized-evidence-model.md:387)；失败分支及禁止混淆规则见 [`FrozenDeclarationBinding`](production-implementation-pi-210-normalized-evidence-model.md:429)、[`DecisionActionEnvelope`](production-implementation-pi-220-decision-interface.md:611) 和 [`StandardStatement`](production-implementation-pi-230-traceability-binding.md:415)。

### 4.3 explicit-null output precision 保真

冻结 YAML 中 F01～F10 存在多个 `output_precision: null` 样本，见 [`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:215) 与 [`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:464)。当前设计建立唯一传播路径：

**冻结 output precision 声明对象存在且声明值为 null → RESOLVED + 非 null stable ref → decision 同一 binding → trace 同一 binding → statement 同一 binding → 引用解析到 declared precision null。**

该路径在 PI-210 的声明值／引用存在性分账规则中为强制条件，见 [`FrozenDeclarationBinding`](production-implementation-pi-210-normalized-evidence-model.md:431)；两个只读 getter 绝不返回裸 null，见 [`get_output_precision_binding()`](production-implementation-pi-210-normalized-evidence-model.md:1004)；PI-220 禁止将 explicit null 改成其他 presence，见 [`DecisionActionEnvelope`](production-implementation-pi-220-decision-interface.md:611)；PI-230 只允许 statement 以 RESOLVED binding 表达 explicit null，见 [`StandardStatement`](production-implementation-pi-230-traceability-binding.md:415)。

**判定：PASS。** explicit-null 声明值不会再导致稳定引用、版本、schema 或摘要消失。

### 4.4 output precision 与 validation plan 独立存在性语义

两类声明复用同一存在性判别联合，但使用不同 declaration type、不同声明 ID 和不同冻结来源字段，且不得互相派生或互为默认值，见 [`DecisionActionEnvelope`](production-implementation-pi-220-decision-interface.md:607)。

- output precision 声明对象存在但值为 null：必须 RESOLVED；
- validation plan 上游确无声明：可以 ABSENT；
- validation plan 明确不适用：可以 NOT_APPLICABLE；
- 任一声明未读取／来源不可用：UNAVAILABLE；
- 任一稳定引用身份、版本、schema、摘要或链路失败：UNRESOLVABLE。

F09／F10 的 validation timepoints 与各自 null output precision 在 YAML 中同时存在，见 [`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:463) 和 [`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:491)，当前契约不会将前者推导为后者。

**判定：PASS。** 两类声明共享引用存在性语法但不共享声明事实，R2 对照歧义已消除。

### 4.5 decision → trace → statement 逐值同一

| 检查维度 | decision → trace | trace → statement | 判定 |
|---|---|---|---|
| presence 分支 | 必须逐值复制 | 必须相同 | PASS |
| declaration ID／type／card ID | RESOLVED ref 精确解析 | 完整 ref 逐字段相同 | PASS |
| contract version | 必须一致 | 必须一致 | PASS |
| declaration schema version | 必须一致 | 必须一致 | PASS |
| content digest | 必须一致 | 必须一致 | PASS |
| reason code | 非 RESOLVED 分支保留 | 必须逐值相同 | PASS |
| issue IDs | 失败分支保留 | 必须逐值相同 | PASS |
| attempted ref | UNRESOLVABLE 保留 | 必须逐值相同 | PASS |

PI-230 明确要求 trace 逐值复制 PI-220 envelope，见 [`DecisionTraceRef`](production-implementation-pi-230-traceability-binding.md:353)；statement 不得自行降级、升级、补默认或重解释，见 [`StandardStatement`](production-implementation-pi-230-traceability-binding.md:415)。

### 4.6 H-03-R 裁决

**H-03-R：已解除。**

解除理由：三文档现在共同形成单一、非 nullable、可判别且可机械校验的声明 binding 契约；explicit-null 值保持 RESOLVED 与非 null stable ref；五种 presence 不混淆；output precision 与 validation plan 独立；decision → trace → statement 的分支、版本、schema、摘要和引用内容逐值同一。未发现残余 High、Medium 或关键歧义。

## 5. R1 七项已关闭问题无回归检查

| 编号 | 原问题 | 当前直接证据 | R3 判定 |
|---|---|---|---|
| H-01 | 冻结 output precision 无法无损表达 | [`OutputPrecisionRef.declared_precision`](production-implementation-pi-210-normalized-evidence-model.md:423) 为 opaque JSON 或 null；可承载 F11 映射与 F12 嵌套对象，且不把 F09／F10 timepoints 转成 precision | 无回归，PASS |
| H-02 | 最低充分参与集合可被绕过 | PI-220 要求每个 required role 恰有一条独立记录，并规定 MISSING／CONFLICT／UNKNOWN 使 OUTPUT invalid，见 [`ParticipationRoleRecord`](production-implementation-pi-220-decision-interface.md:293) | 无回归，PASS |
| M-01 | RunTrack 不唯一 | PI-210 定义唯一 [`RunTrack`](production-implementation-pi-210-normalized-evidence-model.md:99)；PI-230 所有 track 字段复用它且不扩展，见 [`RunTrack`](production-implementation-pi-230-traceability-binding.md:95) | 无回归，PASS |
| M-02 | 转换记录存在竞争类型 | PI-210 的 [`TransformationRecord`](production-implementation-pi-210-normalized-evidence-model.md:549) 是唯一规范转换契约；PI-230 明确不存在竞争 trace 转换类型，见 [`TransformationRecord`](production-implementation-pi-230-traceability-binding.md:484) | 无回归，PASS |
| M-03 | 摘要必填与摘要缺失冲突 | PI-230 以 [`DigestBinding`](production-implementation-pi-230-traceability-binding.md:277) 分账 PRESENT／MISSING；MISSING 带 issue 且 fail closed，见 [`DigestBinding`](production-implementation-pi-230-traceability-binding.md:295) | 无回归，PASS |
| M-04 | basis 非空基数上下游不一致 | PI-220 定义唯一非空 [`BasisRecordIds`](production-implementation-pi-220-decision-interface.md:116)，五动作统一使用；PI-230 decision trace 与 statement 复用同一类型，见 [`BasisRecordIds`](production-implementation-pi-230-traceability-binding.md:107) | 无回归，PASS |
| M-05 | 来源状态与 evaluator 状态混淆 | PI-210 [`SourceFieldState`](production-implementation-pi-210-normalized-evidence-model.md:333) 只记来源事实；PI-220 [`FieldEvaluatorState`](production-implementation-pi-220-decision-interface.md:113) 独立，并规定非矩阵组合 fail closed，见 [`FieldPathIssue`](production-implementation-pi-220-decision-interface.md:530) | 无回归，PASS |

**回归结论：** H-01、H-02、M-01～M-05 全部保持关闭，未发现回归。

## 6. 跨文档接口抽查

| 接口面 | PI-210 | PI-220 | PI-230 | 裁决 |
|---|---|---|---|---|
| 三轨证据 | 定义结构、现实、假设三轨 | 现实门满足只接受现实事实 | 保留 evidence 与 source refs | 闭合，PASS |
| 声明值与存在性 | opaque value／null 与 binding 分账 | 两类 binding 必填且独立 | decision、trace、statement 逐值同一 | 闭合，PASS |
| 最低充分参与角色 | 提供证据、字段、根源、时序与反证来源 | 逐角色记录且 OUTPUT 不可绕过 | action basis 与角色记录可追溯 | 闭合，PASS |
| 五动作 | 不提前选择动作 | OUTPUT、CONDITIONAL、ASK、ABSTAIN、HUMAN_REVIEW | 非输出动作不得伪装成 OUTPUT statement | 闭合，PASS |
| 运行轨道 | 唯一 RunTrack | 适配边界保持分账 | production／preprod 跨轨只 audit-only | 闭合，PASS |
| 转换 | 唯一 TransformationRecord | 适配记录沿用唯一类型 | 顶层、边、投影、查询均指向同一记录 ID | 闭合，PASS |
| 摘要 | 冻结引用带摘要 | resolved 声明校验摘要 | DigestBinding 表达通用对象摘要缺失并阻断 | 闭合，PASS |
| statement／feedback | 提供来源与转换链 | 提供 action／basis／issue | revision、artifact、feedback binding、learning eligibility fail closed | 闭合，PASS |

## 7. 完整十二项 G2 验收矩阵

| # | 验收项 | R3 独立复验结果 | 判定 | 关联阻断 |
|---:|---|---|---|---|
| 1 | 无冻结业务语义扩张 | output precision 以 opaque JSON／null 逐值保存；设计只读取声明，不从证据数量、旧轨结果或自然语言生成卡片结论 | PASS | — |
| 2 | YAML 保持声明性，未内嵌算法 | YAML 明确禁止推断缺失字段和可执行逻辑；三文档未定义评分、权重、排序或自然语言编译协议 | PASS | — |
| 3 | null／unresolved／absent／unknown 保真 | 来源状态、evaluator 状态、声明值状态和声明引用存在性四层分账；explicit-null 只能由 RESOLVED stable ref 定位，五种 presence 不混淆 | PASS | — |
| 4 | validation timepoints 与 output precision 分账 | 使用不同声明类型、ID、来源字段和独立 binding；F09／F10 timepoints 不推导 precision，F11／F12 结构化 precision 可无损保存 | PASS | — |
| 5 | 三轨分账 | chart structure、reality fact、unverified hypothesis 独立；现实门满足仅接受 reality fact | PASS | — |
| 6 | 五动作失败安全且 ASK 存在 | 五动作各有匹配 payload、非空 basis 和结构禁入；unknown 不是第六动作；失败 binding 禁止 OUTPUT／CONDITIONAL | PASS | — |
| 7 | 门、竞争、反证、根源、时序接口闭合且不卡特定规则 | 最低充分角色逐项记录并约束 OUTPUT；竞争、反证、根源、时序均为引用式契约，没有执行卡片算法 | PASS | — |
| 8 | 字段、来源、转换、decision、statement、feedback 全链可追溯 | 稳定身份、唯一转换、版本、schema、摘要、statement revision、artifact、feedback 与 learning 链闭合；声明 binding 全链逐值同一 | PASS | — |
| 9 | production-default 与 staged／preprod 分账 | 唯一 RunTrack 覆盖各轨；跨轨仅 audit-only；preprod attachment 不替代 production statement bridge | PASS | — |
| 10 | 非原子 artifact、幂等重试、反馈未知映射 fail closed | artifact 独立状态、冻结重试边界、digest conflict、重复摄入、unknown／unmapped feedback 均 fail closed | PASS | — |
| 11 | 三文档类型和引用一致，不存在不可执行歧义 | RunTrack、TransformationRecord、DigestBinding、BasisRecordIds、双状态类型及 FrozenDeclarationBinding 均形成唯一跨文档契约 | PASS | — |
| 12 | 足以支撑一卡最小切片设计而不预实现十二卡 | 通用卡身份、角色、证据、动作、声明 binding 与追溯接口已无歧义；未选择一卡、未嵌入十二卡算法、未声称实现 | PASS | — |

**矩阵统计：12 项 PASS、0 项 BLOCKED。**

## 8. 风险与非证明事项

本轮未发现阻断 G2 的 High、Medium 或关键歧义。仍须保留以下边界风险，但它们不是本次设计契约阻断：

1. 这是设计验收，不是 schema、代码、测试或生产接线验收；
2. [`CardIdentityRef.runtime_capability_status`](production-implementation-pi-230-traceability-binding.md:759) 固定为 REFERENCE_ONLY_NOT_IMPLEMENTATION_PROOF；稳定引用只证明可定位冻结字段；
3. 当前 artifact hard gate、statement records 和 learning bridge 的实现错位仍须由后续获授权阶段处理；本文件不宣称已修复；
4. 非原子 artifact、幂等和 fail-closed 是契约要求，不证明事务、锁、队列或存储实现已存在；
5. 任何后续实现若把 explicit-null binding 降为裸 null、合并 presence 分支或改变 decision → statement 逐值同一，均构成契约违规并应重新阻断。

## 9. G2 最终跨门裁决

**裁决：PASS，允许 G2 设计跨门。**

裁决依据：H-03-R 已解除；H-01、H-02、M-01～M-05 无回归；完整十二项矩阵全部 PASS；三文档之间未发现剩余 High、Medium 或关键可执行歧义。

**该 PASS 仅表示 PI-210／PI-220／PI-230 的 G2 运行时契约设计通过独立验收，不表示任何 schema、runtime consumer、生产代码、测试、renderer、feedback fanout、learning bridge 或 F01–F12 实现已经完成。**

## 10. 允许与禁止的下一步

### 10.1 允许

1. 将本文作为 PI-290-R3 的唯一独立 G2 复验记录；
2. 父任务 PI-200 依据本文，在获授权治理流程中登记 G2 PASS，并将后续动作推进到 G3 的独立任务创建；
3. 后续 G3 仅可在新的任务边界内选择一卡并设计最小垂直切片，继续遵守冻结事实、声明性 YAML、fail-closed 与非实现证明边界。

### 10.2 禁止

1. 不得把本次 PASS 改写为“实现完成”或“生产可用”；
2. 不得由本验收实例修改总控、handoff、PI-210、PI-220、PI-230、冻结契约、YAML、生产代码、测试或数据；
3. 不得在本文选择一卡、设计 G3 细节或设计 G5 实现计划；
4. 不得把 FrozenDeclarationRef、FrozenDeclarationBinding 或 CardIdentityRef 的存在解释为 runtime consumer 已存在；
5. 不得绕过父任务治理直接开始实现。

### 10.3 父任务唯一下一动作

**PI-200 的唯一下一动作：在获授权治理记录中登记 PI-290-R3 的 G2 PASS，并据此创建一个独立 G3 一卡最小垂直切片设计任务。**

本验收实例不直接修改总控，也不执行该下一动作。

## 11. 自检

- [x] 当前实例为 PI-290-R3，与整改实例及 PI-290-R2 分离；
- [x] 未递归委派；
- [x] 已直接读取整改后 PI-210／PI-220／PI-230、冻结 Markdown 契约与声明性 YAML；
- [x] 已机械核对 output precision 与 validation plan 各自的引用存在性；
- [x] 已验证 explicit-null output precision 始终保留非 null stable ref；
- [x] 已验证裸 null、ABSENT、NOT_APPLICABLE、UNAVAILABLE、UNRESOLVABLE 不混淆；
- [x] 已验证 decision → trace → statement 的分支、版本、schema、摘要和引用逐值同一；
- [x] 已检查 H-01、H-02、M-01～M-05 无回归；
- [x] 已重新执行完整十二项 G2 验收矩阵；
- [x] 未发现 High、Medium 或关键歧义；
- [x] 未修改任何设计、总控、handoff、冻结事实源、代码、测试或数据；
- [x] 已明确 PASS 只代表 G2 设计跨门，不代表实现。
