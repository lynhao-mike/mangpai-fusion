# PI-390-R2 · PI-300 G3 独立复验记录

> 复验实例：PI-390-R2  
> 复验日期：2026-07-19  
> 复验对象：经 PI-360-R1 有界整改后的 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md)  
> 唯一最终裁决：**BLOCKED**

---

## 1. 范围、独立性与边界

本实例只审阅、核验和裁决整改后的 PI-300，不修改 PI-300，不实施代码，不执行测试，不扩展第二张卡，不修改总控或 handoff。唯一写入产物是本复验记录。

复验保持以下边界：

1. 唯一业务卡为 F09「资本配置与风险承担」。
2. F08 只能作为 F09 侧 strongest competing explanation 的证据、关系、问题和来源身份，不执行 F08，不产生 F08 candidate、disposition、action 或 statement。
3. 冻结 Markdown 契约是业务语义事实源；YAML 是声明性附录，不是可执行谓词。
4. 本裁决只评价设计契约是否可机械、无损实例化，不证明 runtime、renderer、feedback fanout、生产接线或 production readiness。
5. PI-300 自检、整改摘要和作者声明只用于定位，不作为通过证据。
6. 按 fail-closed 二值纪律，任一 High、Medium、critical ambiguity、关键证据缺失或新回归均导致 BLOCKED。

---

## 2. 方法与直接事实源

采用逐字段机械交叉核验，而非按意图或章节覆盖度判断：

- 前次 G3 发现基线：[`production-implementation-pi-390-r1-g3-acceptance.md`](production-implementation-pi-390-r1-g3-acceptance.md:69)。
- 规范证据模型：[`FrozenDeclarationRef`](production-implementation-pi-210-normalized-evidence-model.md:568)、[`FrozenDeclarationBinding`](production-implementation-pi-210-normalized-evidence-model.md:591) 及字段来源对象所在的 [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md)。
- 规范判定接口：[`BasisRecordIds`](production-implementation-pi-220-decision-interface.md:116)、[`ParticipationRoleRecord`](production-implementation-pi-220-decision-interface.md:319)、[`CompetitionSet`](production-implementation-pi-220-decision-interface.md:349)、[`CandidateDisposition`](production-implementation-pi-220-decision-interface.md:399)、[`DecisionActionEnvelope`](production-implementation-pi-220-decision-interface.md:581) 与五种 payload 所在的 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:617)。
- 规范追踪、statement、artifact、feedback 与幂等：[`StandardStatement`](production-implementation-pi-230-traceability-binding.md:378)、[`ArtifactRecord`](production-implementation-pi-230-traceability-binding.md:512)、[`IdempotencyKey`](production-implementation-pi-230-traceability-binding.md:586)、[`FeedbackSubmission`](production-implementation-pi-230-traceability-binding.md:619)、[`FeedbackBinding`](production-implementation-pi-230-traceability-binding.md:649)、[`LearningEligibility`](production-implementation-pi-230-traceability-binding.md:680)。
- G2 复验边界：[`production-implementation-pi-290-r3-g2-reacceptance.md`](production-implementation-pi-290-r3-g2-reacceptance.md)。
- 冻结 F09 契约：[`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:265)。
- F09 声明附录：[`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:451)。
- G1 runtime 事实：[`production-implementation-pi-110-input-pipeline-audit.md`](production-implementation-pi-110-input-pipeline-audit.md)、[`production-implementation-pi-120-findings-decision-conflict-audit.md`](production-implementation-pi-120-findings-decision-conflict-audit.md)、[`production-implementation-pi-130-report-statement-feedback-audit.md`](production-implementation-pi-130-report-statement-feedback-audit.md)。
- 被验收设计全文：[`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1)。

核验顺序为：冻结语义与单卡边界 → PI-210 声明同一性 → PI-220 participation/competition/root/timing/五动作 → PI-230 statement/artifact/feedback/learning/幂等 → 轨道隔离、失败注入、回滚 → T01–T58 对上述约束的检测能力。

---

## 3. PI-390-R1 七项发现关闭矩阵

| R1 ID | R2 状态 | 独立复验证据与裁决 |
|---|---|---|
| H-01 | **CLOSED** | [`CompetitionSet.candidate_ids`](production-implementation-pi-220-decision-interface.md:351) 仅要求 list，没有至少两个候选的基数约束。PI-300 只列 F09 singleton，并通过 evidence、relation、dimension、issue、source locator 表示 F08，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:477)。同时明确禁止 F08 candidate/disposition/action/statement，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:523)。无需执行第二卡，信息仍保留在 strongest-competing-explanation 维度和反证引用中。 |
| H-02 | **CLOSED** | 两个正常 [`FrozenDeclarationRef`](production-implementation-pi-210-normalized-evidence-model.md:568) 均列出六个身份字段，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:395)；路径保留在被引用声明对象的 source field ref，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:412)。F09 precision 保持 explicit null 与 unresolved，并仍为 RESOLVED，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:426)。decision → trace → statement 逐字段同一约束明确，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:445)。 |
| H-03 | **CLOSED** | PI-300 的 [`FeedbackSubmission`](production-implementation-pi-300-one-card-vertical-slice-design.md:665)、[`FeedbackBinding`](production-implementation-pi-300-one-card-vertical-slice-design.md:676) 与 [`LearningEligibility`](production-implementation-pi-300-one-card-vertical-slice-design.md:692) 逐字段采用 PI-230 required 字段和规范枚举；未再使用 R1 指出的本地状态。 |
| M-01 | **CLOSED** | [`StatementSet`](production-implementation-pi-300-one-card-vertical-slice-design.md:609) 与 [`StandardStatement`](production-implementation-pi-300-one-card-vertical-slice-design.md:628) 已包含 PI-230 required 字段、完整版本引用、两类 binding、publication/integrity 和 issue 字段。 |
| M-02 | **CLOSED** | 六个 required role 各有完整 [`ParticipationRoleRecord`](production-implementation-pi-300-one-card-vertical-slice-design.md:464)，状态、证据、issue、relation 与 source decision 未被压缩；root ledger、timing ledger 和 root/timing check 逐对象实例化，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:525)。 |
| M-03 | **NOT CLOSED** | 五种 payload 的字段表面齐全，但 envelope 的 basis 和 disposition refs 未形成可解析的规范记录引用。详见本记录 M-R2-01。该问题直接违反用户要求的精确 [`BasisRecordIds`](production-implementation-pi-220-decision-interface.md:116) 与 payload 机械闭合复验。 |
| M-04 | **CLOSED** | feedback canonical identity 明确包含 source digest、规范化 item IDs、目标 statement revision 和 eligibility policy identity/version，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:901)，符合 [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:609)。 |

**七项结果：6 项关闭，1 项未关闭。**

---

## 4. 阻断发现

### M-R2-01 · M-03 未关闭：basis 与 disposition refs 不是可机械解析的规范记录引用

- **级别：Medium**
- **性质：R1 遗留未关闭 + 关键证据缺失**

PI-220 明确规定五动作的 basis 可以引用当前 result 内的 gate、participation role、competition、disposition、root/timing check 或 issue 记录，且不能用自由文本充数，见 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:675)。participation role 的稳定记录身份字段是 [`participation_record_id`](production-implementation-pi-220-decision-interface.md:320)。

PI-300 的 COMMON 和下游 trace/statement 却使用 participation set 身份 `PARTICIPATION-F09` 作为 basis，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:565)、[`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:619) 与 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:641)。该值是 [`MinimumSufficientParticipationSet.participation_set_id`](production-implementation-pi-300-one-card-vertical-slice-design.md:453)，不是任一 PR-* participation role record ID，因此不能证明 basis 严格落在 PI-220 允许的记录类型上。

此外，OUTPUT 与 CONDITIONAL payload 分别引用 `DISP-F09-INCLUDED` 和 `DISP-F09-CONDITIONAL`，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:570) 与 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:576)，但 PI-300 展示的唯一 [`CandidateDisposition`](production-implementation-pi-300-one-card-vertical-slice-design.md:509) 是 F09 的 UNRESOLVED 处置，且没有上述两个可解析对象。PI-220 的 [`CandidateDisposition`](production-implementation-pi-220-decision-interface.md:399) 本身也未提供独立 disposition record ID；PI-300 没有说明 refs 的规范解析键或映射规则。因而两个发布型 payload 的 disposition refs 是未闭合裸引用，不能证明每个 included candidate 有可追溯处置。

这不是缺少解释文字，而是动作 envelope → trace → statement 所复用的 basis 和 payload 引用缺少机械解析证据。T38/T39 只宣称完整，未注入错误记录类型或 dangling disposition ref，不能发现该问题。

### M-R2-02 · artifact item 状态枚举漂移为局部竞争 schema

- **级别：Medium**
- **性质：新回归 + 关键证据缺失**

PI-230 的 [`ArtifactRecord.state`](production-implementation-pi-230-traceability-binding.md:525) 规范枚举为 NOT_ATTEMPTED、WRITING、WRITTEN_UNVERIFIED、VERIFIED、FAILED、STALE、MISMATCH、SUPERSEDED。

PI-300 在非原子 artifact 设计中改写为 NOT_STARTED、WRITING、WRITTEN、VERIFIED、FAILED，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:918)。其中 NOT_STARTED 与 WRITTEN 不是 PI-230 枚举，并删除了 WRITTEN_UNVERIFIED、STALE、MISMATCH、SUPERSEDED 的 item-level 表达能力。这与同文“直接采用 PI-230 同一规范对象、不创建本地枚举”的原则不一致，也会使 manifest failure、digest mismatch、stale mixed revision 和 supersession 无法逐 artifact 无损表示。

T21–T24 及失败注入覆盖了 set-level PARTIAL、STALE_MIXED_REVISION 和 mismatch 场景，但没有断言每个 artifact item 必须使用 PI-230 全枚举，因此测试矩阵无法捕获这一局部 schema 漂移。

---

## 5. 完整 G3 验收矩阵

| 验收维度 | 结果 | 行号证据与说明 |
|---|---|---|
| 单卡边界 | PASS | 唯一 F09，F08 不执行，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:69)。 |
| 冻结 F09 语义 | PASS | F09 范围、两轴、来源、root/timing、冲突弃权与冻结契约一致；冻结依据见 [`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:265)。 |
| YAML 声明性 | PASS | PI-300 禁止加载 YAML 生成函数，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:189)；附录本身禁止 executable logic，见 [`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:6)。 |
| 现实硬门到 learning eligibility 链 | BLOCKED | 环节均出现，但动作 basis/disposition 引用未闭合，artifact item schema 又发生漂移；见 M-R2-01、M-R2-02。 |
| 五类 declaration presence | PASS | RESOLVED、ABSENT、NOT_APPLICABLE、UNAVAILABLE、UNRESOLVABLE 分支和影响完整，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:718)。 |
| explicit null + unresolved 保真 | PASS | F09 precision 为 BOTH_NULL_AND_UNRESOLVED 且 binding 仍 RESOLVED，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:426)。 |
| 五动作判别联合 | BLOCKED | 五 payload 字段齐全且 action/payload 一一对应，但 OUTPUT/CONDITIONAL disposition refs 与全部 envelope 的 participation basis 不可机械解析，见 M-R2-01。 |
| 角色不可补偿 | PASS | 六角色逐记录，规范 fail-safe 规则明确，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:449)。 |
| source gate | PASS | source role 独立存在且缺失时阻断发布；见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:470)。 |
| competition/counterevidence | PASS | F09 singleton 与 F08 evidence-only 竞争表示满足单卡约束，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:477)。 |
| root/timing 分账 | PASS | 两账本和 constraint check 完整且禁止反写，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:525)。 |
| decision → trace → statement 同一 | BLOCKED | binding 身份同一已闭合，但 basis 中持续复制错误类型引用，不能证明完整 trace 同一有效。 |
| StatementSet/StandardStatement | PASS | required 字段完整，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:609)。 |
| production/preprod 隔离 | PASS | 明确 AUDIT_ONLY 且不改变 production-default，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:947)。 |
| artifact 非原子性 | BLOCKED | 场景、set 状态与不假回滚意图正确，但 item 状态枚举偏离 PI-230，见 M-R2-02。 |
| 幂等 | PASS | 使用 PI-230 对象，feedback canonical identity 四项敏感材料齐全，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:879)。 |
| 失败注入 | PARTIAL / BLOCKED | source、normalizer、resolver、decision、artifact、feedback、eligibility 故障覆盖充分，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:854)；未覆盖 basis 记录类型、dangling disposition ref 和 artifact enum 漂移。 |
| feedback fail-closed | PASS | exact binding、三态 eligibility 与未知/错 revision/mixed revision 阻断完整，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:662)。 |
| rollback | PASS | 不覆盖不可变事实、不做跨文件假回滚、不跨轨回退，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:936)。 |
| runtime/production-ready 边界 | PASS | 明确没有 F09 runtime consumer 或统一 dispatcher，全部为 future targets，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:30)。 |

---

## 6. Regression 与硬 falsifier 矩阵

| Falsifier / regression | 结果 | 证据 |
|---|---|---|
| 修改冻结 F09 | 未触发 | PI-300 明确冻结边界，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:988)。 |
| 执行 YAML | 未触发 | 禁止生成判断函数，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:189)。 |
| explicit null 变 absent/unavailable | 未触发 | 正常分支保持 RESOLVED，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:441)。 |
| validation/precision 串线 | 未触发 | 两个声明对象、类型、路径与 binding 独立，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:392)。 |
| 必须执行 F08/第二卡 | 未触发 | singleton 合法，F08 仅 evidence identity，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:477)。 |
| 任一动作/payload/basis 缺失 | **触发：basis/payload refs 不闭合** | 字段名存在，但 participation basis 类型错误且两个 disposition refs 无对象，见 M-R2-01。 |
| 角色可补偿 | 未触发 | 每个 required role 独立记录，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:464)。 |
| 跨轨污染 | 未触发 | preprod 只作 audit，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:949)。 |
| 报告成功等同 artifact 完整 | 未触发 | T21–T23 保持 PARTIAL/mixed revision，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:803)。 |
| 不合格反馈可学习 | 未触发 | unknown、mismatch、mixed revision 与 unsupported anchor 均 fail closed，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:705)。 |
| 新 schema 回归 | **触发** | artifact item 状态出现 PI-230 之外的 NOT_STARTED/WRITTEN，见 M-R2-02。 |

---

## 7. T01–T58 充分性裁决

| 测试组 | 结果 | 说明 |
|---|---|---|
| T01–T19：动作、声明、三轨、竞争、root/timing、binding | PARTIAL | 主要业务和声明攻击面充分；T04 的“无正式 payload”结合 T41 解释为“无正式 OUTPUT payload”，未单独计 critical ambiguity。但该措辞应避免被实现为无 AbstainPayload。 |
| T20–T30：投影、artifact、幂等、feedback、跨轨、能力声明 | PARTIAL / BLOCKED | 覆盖 set-level partial/mixed/mismatch，却未校验 [`ArtifactRecord.state`](production-implementation-pi-230-traceability-binding.md:525) 全枚举同构。 |
| T31–T37：F08 identity-only 与声明身份 | PASS | 正反路径覆盖 singleton、伪造第二候选、六字段 ref、null/unresolved 与跨层漂移。 |
| T38–T43：五 payload | PARTIAL / BLOCKED | 字段完整和判别错配覆盖到位，但未检查 basis ID 所属记录类型，也未检查 disposition refs 可解析到实际规范处置。 |
| T44–T54：statement、participation、root/timing、feedback/eligibility | PASS | required 字段、状态—issue—decision 路径和规范枚举有正负例。 |
| T55–T58：feedback canonical identity | PASS | 四类 identity 变化均被单独覆盖。 |

**总体：T01–T58 不足以发现本次两个阻断问题，不能支撑 G3 PASS。**

---

## 8. 精确统计

- High：**0**
- Medium：**2**
- critical ambiguity：**0**
- 关键证据缺失：**2 类**
  1. 动作 basis/disposition 引用的规范记录类型与可解析对象证据；
  2. artifact item 状态与 PI-230 全枚举同构证据。
- 新回归：**1**（artifact item 状态局部竞争 schema）
- PI-390-R1 七项：**6 CLOSED / 1 NOT CLOSED**

说明：M-R2-01 同时包含 basis 类型错误和 dangling disposition refs，但二者共同否定同一项 M-03“完整五动作可机械实例化”，因此按一个 Medium 发现、一个关键证据类别统计；未重复计数。M-R2-02 是独立 artifact schema 回归。

---

## 9. 唯一最终裁决

# BLOCKED

理由：PI-390-R1 的 M-03 尚未关闭，且新增 artifact item 状态枚举漂移；合计 **0 High、2 Medium、0 critical ambiguity、2 类关键证据缺失、1 个新回归**。依据二值纪律，任一 Medium、关键证据缺失或新回归都禁止 PASS。

---

## 10. 状态建议

1. 父流程保持 G3 阻断，不将 PI-300 标记为 accepted/completed，不启动一卡实现，不改变 production-default。
2. 本实例不整改上述问题；整改责任仍属于 PI-300 设计责任方。
3. 后续复验必须继续保持 F09 单卡，不得以执行 F08、修改冻结语义、执行 YAML 或借用 preprod/staged 结果消除阻断。
4. 后续独立复验至少应机械验证：每个 basis ID 的规范记录类型、每个 disposition ref 的实际解析对象，以及每个 artifact item 状态逐值属于 PI-230 枚举。

本记录不证明 runtime、测试执行、生产接线、renderer、artifact coordinator、feedback fanout 或 learning 实现已经存在或可投产。