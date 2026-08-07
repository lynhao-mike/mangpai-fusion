# PI-390-R4 · PI-300 G3 独立复验记录

> 任务编号：PI-390-R4  
> 父任务：PI-300 / G3  
> 复验对象：PI-360-R3 整改后的 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1)  
> 文档性质：独立验收、只读审查；不整改、不实现、不执行测试、不改变生产默认  
> 裁决纪律：任一 High、Medium、critical ambiguity、关键证据缺失或回归均导致 `BLOCKED`

---

## 1. 独立性声明与审查边界

本记录是与 PI-300、PI-360-R1／R2／R3、PI-390-R1／R2／R3 分离的新验收实例。审查只读取冻结 F09、已通过的 G2 契约、G2 验收结论、PI-300 当前设计对象及既往 G3 验收记录；未把 PI-360-R3 的自述清单当作验收结论。

本实例没有：

- 修改 PI-300、PI-210／220／230、冻结契约、mapping、总控、handoff、代码或测试；
- 执行 YAML、测试或任何业务 evaluator；
- 执行 F08、扩展到第二张卡或引入新 schema／枚举／动作优先级；
- 把设计 fixture、T01–T77 或本文裁决表述为 runtime、测试执行、生产接线或投产证据。

本记录是本次任务唯一新增文件。

---

## 2. 事实源

1. 当前验收对象：[`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1)。
2. 规范化证据与冻结声明绑定：[`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:1)。
3. 判定接口，特别是 [`GateEvaluationSet`](production-implementation-pi-220-decision-interface.md:244)、[`GateEvaluationRecord`](production-implementation-pi-220-decision-interface.md:253)、[`DecisionEvaluationResult`](production-implementation-pi-220-decision-interface.md:558)、五动作 envelope 与 current-result basis 规则：[`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:553)。
4. trace、statement、artifact、feedback 与 learning 绑定：[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:1)，其中 artifact item 与 set 规范分别见 [`ArtifactRecord`](production-implementation-pi-230-traceability-binding.md:512) 和 [`ArtifactSetStatus`](production-implementation-pi-230-traceability-binding.md:550)。
5. 已通过的 G2 边界：[`production-implementation-pi-290-r3-g2-reacceptance.md`](production-implementation-pi-290-r3-g2-reacceptance.md:1)。
6. 既往 G3 发现基线：[`production-implementation-pi-390-r1-g3-acceptance.md`](production-implementation-pi-390-r1-g3-acceptance.md:1)、[`production-implementation-pi-390-r2-g3-reacceptance.md`](production-implementation-pi-390-r2-g3-reacceptance.md:1)、[`production-implementation-pi-390-r3-g3-reacceptance.md`](production-implementation-pi-390-r3-g3-reacceptance.md:1)。
7. F09 规范语义：[`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:265)。
8. 声明型机器附录：[`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:451)；它只提供冻结声明，不是可执行判定逻辑。

---

## 3. PI-390-R3 唯一发现关闭矩阵

| R3 发现 | R3 状态 | R4 机械证据 | R4 结论 |
|---|---|---|---|
| M-R3-01：basis 中 `GATE-F09` 无法在各场景当前 result 解析为允许的 gate record | OPEN / Medium | PI-300 现为五个互斥场景分别给出当前 [`DecisionEvaluationResult.gate_sets`](production-implementation-pi-300-one-card-vertical-slice-design.md:449)；每个 set 含一个完整 [`GateEvaluationRecord`](production-implementation-pi-300-one-card-vertical-slice-design.md:458)，其 `gate_record_id` 为 `GATE-F09`；唯一性、current-result 解析域和禁止回退在 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:449) 与 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:583) 明示；T74–T77 提供零匹配、多匹配、错误类型和跨 result 的反例设计，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1017)。 | **CLOSED** |

R3 所缺的不是声明性期望，而是当前 result 内可供 basis 解析的对象证据。PI-360-R3 后的第 7.2 节已经补入该对象证据，且没有通过删除 `GATE-F09` basis、借用别的记录类型或跨场景共享对象来规避问题。

---

## 4. 五场景 gate 机械核验

### 4.1 逐场景矩阵

| 当前 result 场景 | set 位置 | record 状态 | PI-220 全字段 | 状态—引用一致性 | `GATE-F09` 当前 result 恰一解析 | 安全动作关系 | 结论 |
|---|---|---|---|---|---|---|---|
| OUTPUT | [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:452) | `SATISFIED` | candidate、function、definition refs、record identity、support/counter/conflict、三类 path、reason、source decision、set state、issues 均存在 | 支持证据非空且被限定为 `REALITY_FACT`；source decision 非空；无 missing/conflict/unknown path | 是；本 set 一个，其他 set 禁止复用 | 无 blocking issue，可支持 OUTPUT 结构分支 | PASS |
| CONDITIONAL | [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:478) | `SATISFIED` | 全字段存在 | 配置轴支持存在；冻结 F09 允许配置轴和／或风险轴，未用缺失风险轴反填；source decision 非空；边界 issue 保留为 nonblocking 条件范围 | 是 | 条件和 unresolved issue 在 payload 中保留，不越界成双轴肯定结论 | PASS |
| ASK | [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:504) | `MISSING` | 全字段存在 | missing path 和缺证 reason 非空，source decision 为 null；同一 issue 进入 set、问题请求和 blocking refs | 是 | 问题、issue、字段路径及 resume token 闭合 | PASS |
| ABSTAIN | [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:530) | `SATISFIED` | 全字段存在 | gate 满足不消除 F08/F09 competition 阻断；现实支持和 source decision 完整 | 是 | 当前竞争 disposition 为 `UNRESOLVED`，仅支持 ABSTAIN，不产生 OUTPUT／CONDITIONAL | PASS |
| HUMAN_REVIEW | [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:556) | `CONFLICT` | 全字段存在 | 支持、反证、冲突 relation、conflict path、reason 和 source decision 全部保留；set 为 `DISPUTED` | 是 | 冲突两侧及 review scope 保留，不覆盖冲突 | PASS |

### 4.2 Gate 总体裁决

五个场景均逐值满足 PI-220 的 [`GateEvaluationRecord`](production-implementation-pi-220-decision-interface.md:253) 必需字段，并符合 [`SATISFIED/MISSING/CONFLICT/UNKNOWN`](production-implementation-pi-220-decision-interface.md:272) 的引用约束。`set_state=READY` 仅被解释为结构完整，不被解释为所有业务门均满足，符合 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:283)。

设计还明确要求每个 evidence、issue、relation 与 source decision 在场景当前 result 或其 PI-210 package 内解析，并将记录缺失、重复、错误类型、断链和跨 result 查找全部判为 invalid，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:583)。因此没有 fixture 完整性替代现实门满足的语义漂移：`SATISFIED` 仍要求获授权判定结果、非空现实事实支持与 source decision；设计文档没有定义或执行从 fixture 自动推导门满足的算法。

---

## 5. Basis、trace、statement 与 disposition 回归

### 5.1 Basis 逐值解析

五个 envelope 使用同一非空、有序 basis：

1. `GATE-F09`：在各自当前 result 中恰一解析为 [`GateEvaluationRecord.gate_record_id`](production-implementation-pi-220-decision-interface.md:254)。
2. `PR-NATAL`、`PR-DAYUN`、`PR-LIUNIAN`、`PR-REALITY`、`PR-FALSIFIER`、`PR-SOURCE`：分别解析为六个独立 [`ParticipationRoleRecord.participation_record_id`](production-implementation-pi-220-decision-interface.md:319)，实例见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:600)；容器 `PARTICIPATION-F09` 被明确禁止冒充 basis。
3. `COMPETITION-F09`：解析为当前 result 的规范 CompetitionSet，实例见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:616)。
4. `RTC-F09-1`：解析为 root/timing check，实例见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:700)。

这些类型均属于 PI-220 允许的 current-result basis 类型，见 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:675)。未发现自由文本充数、容器冒充 role record、evidence 冒充 gate record或跨 result 补齐。

### 5.2 Action → trace → statement 等值

- envelope 的 basis 固定值见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:725)；
- trace 的 basis 见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:775)；
- statement 的 basis 见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:788)。

三层均为相同九值、相同顺序；双声明 binding、action identity 和 selected action 同样保持逐值传播。PI-300 没有允许消费者删除 gate basis 或跨 result 重解析。

### 5.3 Disposition 恰一解析与动作兼容

| 场景 | 当前 competition disposition | 解析规则 | 动作兼容 | 结论 |
|---|---|---|---|---|
| OUTPUT | F09 `INCLUDED`，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:662) | 只在当前 result、basis 所引唯一 competition set 内按 candidate identity 恰一匹配 | OUTPUT 仅接受 `INCLUDED` | PASS |
| CONDITIONAL | F09 `CONDITIONAL`，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:671) | 同上 | CONDITIONAL 仅接受 `CONDITIONAL`，条件／issue refs 保留 | PASS |
| ABSTAIN | F09 `UNRESOLVED`，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:644) | 同上 | 只支持 ABSTAIN，不可冒充可发布处置 | PASS |
| ASK／HUMAN_REVIEW | 不携带 OutputPayload／ConditionalPayload 的 disposition refs | 对应动作使用自身规范 payload；不伪造可发布处置 | 与判别联合一致 | PASS |

零匹配、多匹配、dangling、跨 result 和动作不兼容均被明确判 invalid，规则见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:681)，测试设计见 T61–T66 与 T73：[`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1004)。

---

## 6. 完整 G3 回归矩阵

| G3 检查域 | 结果 | 机械证据与边界 |
|---|---|---|
| 单卡边界 | PASS | 仅执行 F09；范围和非目标见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:75)。 |
| F08 identity-only | PASS | F08 只作为 hypothesis/evidence/relation/source identity，不创建 candidate、disposition、action 或 statement，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:613)。 |
| 冻结 F09 语义 | PASS | 资源、对象、配置／风险轴、归属、时态、source 与 unresolved competition 仍按冻结语义 fail safe；没有以结果、职位、普通债务或理论候选补门。 |
| YAML 非执行边界 | PASS | mapping 仅作声明来源；设计明确不加载 YAML 生成判断函数，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:181)。 |
| 三轨证据 | PASS | 只有 `REALITY_FACT` 可满足现实门，理论和 hypothesis 不升级为事实，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:115)。 |
| 冻结声明与显式 null | PASS | validation 与 output precision 使用两个完整 ref；precision 的 null + unresolved 保持 `RESOLVED`，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:392)。 |
| Necessary gates | PASS | 五场景 current-result gate fixture 全字段、状态引用和唯一解析通过；未把结构完整当业务满足。 |
| 最低充分参与 | PASS | 六个 required role 各有独立完整 record；状态不能互补，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:585)。 |
| Competition／counterevidence | PASS | F09 单候选竞争集保留 F08 反证、关系、冲突维度、source 与 disposition；未只存胜方。 |
| Root／timing 分账 | PASS | 两账本及 check 独立，timing 不写回 root，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:685)。 |
| 五动作判别联合 | PASS | 五个互斥完整 envelope、非空 basis、匹配 payload 和 issue 路径均存在，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:723)。 |
| Statement／trace | PASS | 完整 StatementSet、DecisionTraceRef 与 StandardStatement；statement 只投影 decision，不重做判定，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:764)。 |
| Artifact item／set 分账 | PASS | item 逐值采用 PI-230 八态，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1095)；item stale/mismatch/superseded 与 set aggregate 分账，只有 `COMPLETE_VERIFIED` 才继续 feedback-ready 检查。 |
| 非原子 artifact／rollback | PASS | report、records、index、manifest 各自失败和 partial/mixed/mismatch 路径明确；不做跨文件假回滚或覆盖，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1033) 与 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1117)。 |
| Feedback binding | PASS | submission、item、七维 match、target refs、anchor、status 与 issues 采用 PI-230 形状；未知、错 revision、mixed revision 和 digest mismatch fail closed。 |
| Learning eligibility | PASS | eligibility 只计算准入，不执行学习；非完整 artifact、跨轨、unmapped 或不精确 binding 均不可学习，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:353)。 |
| 幂等 | PASS | 使用 PI-230 IdempotencyKey；source digest、item ID 集、statement revision、policy version 进入 canonical identity，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1056)。 |
| Track isolation | PASS | production-default 与 staged/preprod 分账；跨轨仅 `AUDIT_ONLY`，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1128)。 |
| Runtime／production-ready 否认 | PASS | 文档明确无 F09 runtime consumer、统一 dispatcher、原生 statement/artifact/feedback 接线，且固定 card capability 为 reference-only，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:30) 与 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1182)。 |

完整回归未发现 R1 已关闭六项、R2 已关闭的 disposition／artifact 两项或 R3 gate 修复发生倒退。

---

## 7. Regression 与 falsifier 矩阵

| Falsifier / regression | 结果 | 说明 |
|---|---|---|
| 修改冻结 F09 必要门、竞争边或 contradiction guard | 未触发 | 设计只引用冻结语义。 |
| 将 mapping YAML 变为 executable predicate | 未触发 | 明确禁止执行。 |
| fixture 完整即自动令 gate `SATISFIED` | 未触发 | `SATISFIED` 仍要求获授权结果、`REALITY_FACT` 支持和 source decision。 |
| explicit null 改为 absent／unavailable 或默认精度 | 未触发 | precision binding 保持 `RESOLVED`，null 与 unresolved 均保留。 |
| validation plan 与 output precision 串线 | 未触发 | 两个声明 identity、type、ref 和 field path 分离。 |
| 执行 F08 或扩成第二卡 | 未触发 | F08 identity-only；不存在 F08 candidate/action/statement。 |
| gate record 零匹配、多匹配、错误类型或跨 result 回退 | 未触发 | 正例对象已补齐；T74–T77 明确 fail closed。 |
| action／trace／statement basis 漂移 | 未触发 | 九值同序同值。 |
| basis 使用不允许的记录类型 | 未触发 | gate、六 role records、competition、root/timing check 均可机械解析。 |
| disposition dangling、多匹配或动作不兼容 | 未触发 | 当前 result 恰一解析与动作兼容规则完整。 |
| participation 角色互补 | 未触发 | 六角色恰一独立记录。 |
| timing 改写 root | 未触发 | ledger 分账并有攻击测试。 |
| artifact item enum 漂移或 item/set 混用 | 未触发 | 八值 item enum 与 set aggregate 分账。 |
| report success 等同 artifact complete | 未触发 | partial、written-unverified、mixed revision 与 mismatch 均阻断 readiness。 |
| unknown／mismatch feedback 进入学习 | 未触发 | binding 与 eligibility fail closed。 |
| preprod/staged 改变 production-default | 未触发 | track-preserving；跨轨仅 audit。 |
| 将设计或测试清单宣称为 runtime／production proof | 未触发 | 全文持续否认实现和投产证明。 |

---

## 8. T01–T77 测试设计充分性

| 测试组 | 设计充分性 | 说明 |
|---|---|---|
| T01–T19 | PASS | 覆盖五动作正常路径、null/unresolved/absent/unknown、来源与声明故障、三轨污染、竞争、后果反填、root/timing 和声明 binding 漂移。 |
| T20–T30 | PASS | 覆盖 projection loss、artifact 非原子失败、mixed revision、digest mismatch、feedback 映射与幂等、跨轨和 capability 误宣称。 |
| T31–T37 | PASS | 覆盖 F08 identity-only、伪造第二 candidate、singleton、完整声明 identity 和 decision→trace→statement binding 漂移。 |
| T38–T45 | PASS | 覆盖五 payload 判别联合、错配负例及完整 StatementSet／StandardStatement 必需字段。 |
| T46–T54 | PASS | 覆盖六 participation role、角色补偿攻击、状态 fail-safe、root/timing、FeedbackSubmission、FeedbackBinding 与 LearningEligibility 全字段。 |
| T55–T58 | PASS | 覆盖 feedback source、item IDs、statement revision 与 policy version 对 canonical identity 的影响。 |
| T59–T60 | PASS | T59 现以五个 current-result gate fixtures 为前置，逐个 basis 恰一解析；T60 阻止 participation 容器冒充 role record。 |
| T61–T66、T73 | PASS | 覆盖 disposition 正例、dangling、零／多匹配、动作不兼容及 ABSTAIN unresolved 分支。 |
| T67–T72 | PASS | 覆盖 PI-230 八个 artifact item 状态、非法旧值以及 stale/mismatch/superseded 与 set 分账。 |
| T74–T77 | PASS | 覆盖 R3 缺口的四个关键 falsifier：gate 缺失、重复、错误记录类型和跨 result 引用。 |

T01–T77 是充分的**设计级测试矩阵**，能够在未来实现中证伪本切片的关键结构不变量。它们不是已创建或已执行测试，也不替代第 7.2 节当前设计对象；本次 R4 对象验收依赖实际写入 PI-300 的五个 gate fixtures，而不是依赖 T59 的预期文字。

---

## 9. 精确统计

- High：**0**
- Medium：**0**
- critical ambiguity：**0**
- 关键证据缺失：**0 类**
- 新回归：**0**
- PI-390-R3 唯一 Medium：**1 CLOSED / 0 OPEN**
- PI-390-R1 七项历史发现：**7 CLOSED / 0 OPEN**
- 五个互斥 gate 场景：**5 PASS / 0 BLOCKED**
- G3 回归检查域：**18 PASS / 0 BLOCKED**
- T01–T77 设计用例：**77 个已定义 / 0 个在本验收中执行**

---

## 10. 唯一最终裁决

# PASS

PI-360-R3 已关闭 PI-390-R3 的唯一 Medium：`GATE-F09` 现在在五个互斥场景各自当前 `DecisionEvaluationResult` 中均恰一解析为完整、允许类型的 `GateEvaluationRecord`，且状态—引用关系符合 PI-220。完整 G3 回归未发现 High、Medium、critical ambiguity、关键证据缺失或回归。

该 PASS 只证明 PI-300 的 **F09 单卡 G3 设计**具备进入 G4 独立设计评审的条件；不证明任何代码已实现、T01–T77 已执行、runtime 已接线、production-default 已改变、反馈学习已启用或系统可投产。

---

## 11. 状态建议

1. 将 PI-300／G3 的阶段门结论记录为已通过独立设计验收，并允许进入 G4。
2. G4 仍须作为新的独立评审，不得把本记录替代 G4，也不得直接进入实现或 G5。
3. F01–F12 的 implementation 状态继续保持 `false`；production-default、staged/preprod、冻结契约和 mapping 均保持不变。
4. 后续任何实现若不能维持 current-result gate/basis/disposition 解析、双声明分账、F08 identity-only、artifact item/set 分账、feedback fail-closed 或 track isolation，应停止并重新阻断，不得以扩大卡片范围或改写冻结语义修复。
