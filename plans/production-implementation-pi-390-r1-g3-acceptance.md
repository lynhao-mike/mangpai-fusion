# PI-390-R1 · PI-300 独立 G3 验收记录

> 任务编号：PI-390-R1  
> 验收对象：[`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1)  
> 验收性质：与 PI-300 作者分离的独立 G3 设计验收；只审阅和裁决  
> 验收日期：2026-07-19  
> 唯一最终裁决：**BLOCKED**

---

## 1. 范围与独立性声明

本记录只裁决 PI-300 是否在不修改冻结 F09 语义、不执行声明性 YAML、不扩展第二张执行卡、不借用其他运行轨能力的前提下，对 G2 契约形成完整、无歧义、可验收的一卡垂直切片设计。

本验收实例与 PI-300 作者分离。PI-300 的“设计自检”仅作为待验对象内容，不作为验收证据；裁决完全来自下列冻结契约、G2 契约、G1 现状审计与 PI-300 正文的独立交叉核验。

本次未修改 PI-300、任何代码、测试、冻结契约、mapping、总控或 handoff；未执行实现测试；未扩展到第二张卡。唯一写入为本验收记录。

---

## 2. 检查方法

1. 逐行读取十份最小相关事实源。
2. 以正式 Markdown 冻结契约判定 F09 业务语义，以 YAML 仅核对声明值、字段状态、竞争关系和来源位置。
3. 以 PI-210、PI-220、PI-230 的规范对象和不变量为 G2 接口基线。
4. 以 PI-110、PI-120、PI-130 核对当前能力边界，防止把 analogue、staged 或 preprod 能力冒充新协议实现。
5. 对 PI-300 的正文、对象骨架、测试矩阵、失败注入、幂等和回滚分别核验；不采用其自检勾选作为通过依据。
6. 应用二值纪律：任一 High、Medium、critical ambiguity 或证据缺失均裁决 `BLOCKED`；只有所有问题数为零且矩阵全通过才允许 `PASS`。

---

## 3. 事实源

1. [`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:1)
2. [`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:1)
3. [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:1)
4. [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:1)
5. [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:1)
6. [`production-implementation-pi-290-r3-g2-reacceptance.md`](production-implementation-pi-290-r3-g2-reacceptance.md:1)
7. [`production-implementation-pi-110-input-pipeline-audit.md`](production-implementation-pi-110-input-pipeline-audit.md:1)
8. [`production-implementation-pi-120-findings-decision-conflict-audit.md`](production-implementation-pi-120-findings-decision-conflict-audit.md:1)
9. [`production-implementation-pi-130-report-statement-feedback-audit.md`](production-implementation-pi-130-report-statement-feedback-audit.md:1)
10. [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1)

PI-290-R3 只证明 G2 契约已通过独立复验，不替代本次对 PI-300 的 G3 核验；其边界明确仍不构成实现、生产接线或 runtime 证明，见 [`production-implementation-pi-290-r3-g2-reacceptance.md`](production-implementation-pi-290-r3-g2-reacceptance.md:160)。

---

## 4. 逐项验收矩阵

| # | 验收项 | 独立结果 | 直接证据与裁决理由 |
|---:|---|---|---|
| 1 | 严格只有 F09 一卡；F08 仅为竞争引用 | **PARTIAL / BLOCKED** | PI-300 明确 F08 不执行、不生成 action 或 statement，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:69) 与 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:259)。但其 `CompetitionSet` 只含一个 F09 candidate 和一个 F08 identity string，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:473)；PI-220 规范要求 `candidate_ids`、逐候选 evidence/counterevidence map、`candidate_dispositions`，见 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:348)。设计未说明“不执行 F08”时如何合法实例化该规范竞争集合，形成关键接口歧义。 |
| 2 | F09 冻结语义保持不变；YAML 不作 executable predicate | **PASS** | F09 冻结定义要求资本／信用资源、明确对象、非机械配置裁量和／或可归属风险暴露独立核验，见 [`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:265)。YAML 明确禁止 executable logic，见 [`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:6)。PI-300 禁止新增谓词、阈值、评分和加载 YAML 生成函数，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:86) 与 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:181)。 |
| 3 | 端到端链路完整 | **PARTIAL / BLOCKED** | PI-300 的顺序覆盖事实硬门、参与集、source gate、竞争／反证、root/timing、五动作、statement、artifact、feedback、eligibility，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:137)。但竞争对象、statement、feedback 和 eligibility 的说明性骨架未保持 G2 规范对象形状，导致“提到全部环节”不能证明接口可无损连接。具体见 H-01、H-03、M-01。 |
| 4 | validation plan 与 output precision 独立、无损 | **BLOCKED** | 语义文字正确：F09 validation plan 为 `PRESENT_VALUE + RESOLVED`，output precision 为 `BOTH_NULL_AND_UNRESOLVED + RESOLVED`，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:623)。但正常骨架中的两个 `FrozenDeclarationRef` 都缺少规范必需的 `declaration_id`、`contract_version`、`declaration_schema_version`，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:421)。G2 明确六项稳定身份字段全部必需，见 [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:377)，因此不能以该骨架机械证明跨层同一性。 |
| 5 | `FrozenDeclarationBinding` 五 presence 分支完整且失败安全 | **PASS** | PI-300 列出 `RESOLVED/ABSENT/NOT_APPLICABLE/UNAVAILABLE/UNRESOLVABLE` 的合法结构与处置，并禁止失败分支冒充 explicit null，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:632)。这与 PI-210 封闭联合一致，见 [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:387)。本项通过不消除第 4 项正常引用骨架缺字段问题。 |
| 6 | 五动作、payload、basis、issue、source refs 充分 | **PARTIAL / BLOCKED** | 五动作及非空 basis 均被要求，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:298)。但统一 envelope 骨架只把 payload 写成字符串占位“exactly one payload”，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:507)，未逐值实例化 PI-220 五种 payload 的规范字段，后者见 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:617)。表格给出部分语义条件，但不足以机械验证全部 payload 形状、issue 引用和 source decision refs 的闭合。 |
| 7 | 参与集、source gate、竞争、反证、root/timing 不可补偿且不可重写 | **PARTIAL / BLOCKED** | 六角色逐项列出且 source gate 独立，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:231)。root/timing 分账和禁止改写明确，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:276)。然而参与集骨架把每个角色压成 `role + refs`，缺 PI-220 要求的独立 state、支持／反证、missing/conflict/unknown issues、relation 和 source decision ref，见 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:309)；competition 骨架也未满足规范形状。故不可补偿只能从文字理解，不能从设计对象机械验证。 |
| 8 | production-default、parallel、staged/preprod、manual import 隔离；analogue 不冒充实现 | **PASS** | PI-300 将 production-default 设为目标轨，将 staged/preprod 限定为 `AUDIT_ONLY`，并明确现有组件只是 seam，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:75)、[`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:99) 与 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:816)。这与 G1 所证实的多轨碎片边界一致，见 [`production-implementation-pi-120-findings-decision-conflict-audit.md`](production-implementation-pi-120-findings-decision-conflict-audit.md:51)。manual import 未被用来补 production 结论或学习。 |
| 9 | artifact 非原子性、完整性、幂等、失败注入、feedback fail-closed、eligibility、rollback | **BLOCKED** | 非原子情景、失败注入和不做跨文件假回滚覆盖充分，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:740) 与 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:763)。但对象骨架重定义了 PI-230 的 `FeedbackSubmission`、`FeedbackBinding` 和 `LearningEligibility`：缺 parser/source snapshot、逐维 match、policy/version、learning target/excluded refs 等必需字段，并引入不同 status 词汇，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:582)；规范对象见 [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:614)。此外 feedback 幂等键未明确包含 statement revision 与 eligibility policy version，PI-230 明确要求二者，见 [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:601)。 |
| 10 | 测试矩阵覆盖边界和攻击面 | **PARTIAL / BLOCKED** | T01–T30 覆盖五动作、null/unresolved、跨轨、后果反填、root/timing 攻击、artifact 部分写和重复冲突，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:694)。但没有针对 H-01 的“F08 reference-only 如何满足规范 `candidate_ids/dispositions`”正反契约测试，也没有机械检查 H-03 中 PI-230 feedback/eligibility 全字段同构；所以测试矩阵不能发现当前核心 schema 漂移。 |
| 11 | 无实现完成、production-ready 或全卡 runtime 越界宣称 | **PASS** | PI-300 明确当前无 F09 runtime consumer、统一 dispatcher 或 statement/feedback 接线，均为 future implementation targets，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:30)；并固定 `REFERENCE_ONLY_NOT_IMPLEMENTATION_PROOF`，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:133)。未发现“实现完成”“production-ready”或“F01–F12 runtime=true”宣称。 |

矩阵统计：**PASS 4，PARTIAL/BLOCKED 4，BLOCKED 3**。由于验收纪律不接受 partial，非 PASS 项均阻断 G3。

---

## 5. High / Medium / critical ambiguity 清单

### H-01 · F08 reference-only 与 PI-220 competition schema 未闭合

- **级别：High + critical ambiguity**
- PI-300 要求唯一 executable candidate 为 F09、F08 只作 identity ref，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:259)。
- 其骨架使用 `primary_candidate_id + competing_identity`，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:473)。
- PI-220 唯一规范却要求 `candidate_ids`、按 candidate ID 分账的 evidence/counterevidence 与每个候选的 disposition，见 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:348)。
- PI-300 未定义合法、无损、非第二卡执行的适配方式。实现者可能被迫二选一：执行 F08 以生成 candidate，或偏离 G2 schema 新建 identity-only competition 类型。两者都触及硬边界，因此构成 critical ambiguity。

### H-02 · 正常 `FrozenDeclarationRef` 骨架缺稳定身份字段

- **级别：High**
- PI-300 两个正常 `RESOLVED.ref` 仅展示 `declaration_type/card_id/field_path/content_digest`，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:421)。
- G2 唯一稳定声明引用要求 `declaration_id/declaration_type/card_id/contract_version/declaration_schema_version/content_digest`，见 [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:377)。`field_path` 不能替代缺失的三项稳定身份字段。
- 该骨架正是 PI-300 所指定的第一证明点所需对象；字段不全使 declaration identity/digest 跨层同一无法机械验证，属于核心 falsifier 证据缺失。

### H-03 · PI-230 feedback 与 learning 对象被局部重定义

- **级别：High**
- PI-300 骨架以 `submission_id/items/idempotency_key`、单值 `binding_state` 及 `ELIGIBLE/INELIGIBLE/NEEDS_MAPPING_REPAIR/NOT_READY` 描述下游对象，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:582)。
- PI-230 规范要求 FeedbackSubmission 保存 source snapshot、parser identity/version、content digest 和 capture time；FeedbackBinding 逐维保存 case/track/run/statement/revision/set/digest match；LearningEligibility 保存 policy identity/version、target refs、excluded refs 和 blocking reasons，见 [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:614)。
- 当前设计骨架不足以证明 exact binding 和 fail-closed eligibility 可按 G2 唯一契约实例化，且存在实现者照骨架新建竞争 schema 的风险。

### M-01 · StatementSet / StandardStatement 骨架省略多项 required 字段

- **级别：Medium**
- PI-300 骨架缺少 statement schema version、case/track、source package ref、publication state/generated-at，以及 statement semantic scope/domain/text/relation refs/confidence snapshot 等规范字段，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:527)。
- PI-230 的 required 字段见 [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:355)。
- 虽然 PI-300 文字称“必须保留”若干信息，但说明性对象未声明其为裁剪视图，也未完整引用规范对象，存在实现时把不完整骨架当目标 schema 的歧义。

### M-02 · participation 与 root/timing 骨架压缩掉规范失败安全字段

- **级别：Medium**
- PI-300 participation 只展示 `role + refs`；root/timing 只展示单值 assessment/completion mode，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:445)。
- PI-220 要求每个 participation role 有独立 state、支持／反证、missing/conflict/unknown issues、relations 与 source decision ref；root/timing 还要求 entry IDs、source track、约束引用和问题路径，见 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:293) 与 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:417)。
- 省略这些字段后，角色不可补偿和 root/timing 不可重写不能仅靠对象结构验证。

### M-03 · 五动作 payload 未形成可机械验收对象

- **级别：Medium**
- PI-300 的 envelope 骨架将 payload 写为描述性字符串，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:507)。
- PI-220 已冻结五种不同 payload 的完整字段，见 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:617)。
- PI-300 的动作表覆盖大部分语义条件，但没有逐动作对象实例证明 payload 判别联合、issues 和 refs 可完整落地，无法满足“每项设计断言独立核验”的证据强度。

### M-04 · feedback 幂等身份未完整承接 PI-230

- **级别：Medium**
- PI-300 的 `BIND_FEEDBACK` 键为 case、statement set、feedback item 和 submission digest，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:765)。
- PI-230 明确要求 feedback ingest 幂等键包含 feedback source digest、feedback item IDs、statement revision 与 eligibility policy version，见 [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:601)。
- PI-300 未明确 statement revision 和 policy version 如何进入 binding/ingest canonical identity，存在旧 revision 重放或 policy 变化沿用旧键的歧义。

### 问题统计

- High：**3**
- Medium：**4**
- critical ambiguity：**1**（H-01，同时计入 High）
- 证据缺失项：**4 类**（竞争适配、完整声明身份骨架、完整下游 binding schema、完整五动作 payload 实例）

按照既定纪律，任一上述问题已足以裁决 `BLOCKED`。

---

## 6. Falsifier 结果

| Falsifier | 结果 | 证据判断 |
|---|---|---|
| 修改 F09 冻结字段、竞争边或 contradiction guard 才能选择动作 | **未发现直接修改；但竞争接口存在 critical ambiguity** | PI-300 明文禁止修改，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:855)；H-01 使忠实实现路径未闭合。 |
| 将 mapping YAML 解释为 executable predicate | **未触发** | 禁止加载 YAML 生成判断函数，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:181)。 |
| explicit-null binding 改成 absent/unavailable | **未在语义文字中触发；正常 ref 结构证据失败** | presence 语义正确，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:623)；但 H-02 阻断跨层身份验证。 |
| validation plan 与 output precision 无法独立传递 | **结构证明失败** | 两对象概念分开，但正常 refs 缺规范稳定身份字段，不能证明无损同一。 |
| 必须扩展第二张卡才能完成 F09 竞争记录 | **未证明可避免** | PI-300 宣称无需第二卡，但其 competition 骨架不满足 PI-220 candidate-based schema；H-01 未解决。 |
| 五动作或 basis/issue/source refs 缺失 | **部分触发** | 五动作和 basis 文字存在；完整 payload 对象证据缺失，见 M-03。 |
| production-default 被 staged/preprod 污染 | **未触发** | 轨道隔离明确，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:816)。 |
| 报告成功被等同 artifact-set 完整 | **未触发** | PI-300 明确二者不等价，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:326)。 |
| 反馈不可精确绑定或不合格反馈进入学习 | **设计 schema 证明失败** | fail-closed 文字正确，但下游对象未同构 PI-230，见 H-03 与 M-04。 |

**Falsifier 总结：** 没有发现对冻结业务语义的显式改写，也没有发现跨轨污染或 YAML 执行化；但“可忠实实例化”的关键结构证明被 H-01、H-02、H-03 否定，不能以正确意图替代完整设计证据。

---

## 7. 边界声明

1. 本裁决是设计验收，不是实现测试结果。
2. 本裁决不认定当前 runtime、renderer、feedback fanout 或 production wiring 已实现 F09。
3. 本裁决不修改或重新解释 F09、F08/F09 竞争边、contradiction guard、显式 null 或 unresolved 字段。
4. 本裁决不授权执行 F08 或扩展第二张卡。
5. 本裁决不授权把声明性 YAML 编译为判断逻辑。
6. 本裁决不修改 [`production-implementation-control.md`](production-implementation-control.md:1) 或 [`handoff.md`](../handoff.md:1)；状态同步由父实例执行。
7. 本记录中的问题定位是验收证据，不是代为整改或实现方案。

---

## 8. 唯一最终裁决

# BLOCKED

理由：发现 **3 个 High、4 个 Medium、1 个 critical ambiguity**，且存在关键接口证据缺失。根据“任一 High、Medium、critical ambiguity 或证据缺失即 BLOCKED”的二值纪律，PI-300 当前不满足 G3 PASS 条件。

---

## 9. 后续状态建议

父实例应保持 G3 为阻断状态，不启动一卡实现，不把 PI-300 标记为 accepted/completed，不改变 production-default。后续只能由 PI-300 设计责任方在原任务边界内消除上述契约漂移和 critical ambiguity，再创建新的、与作者分离的 G3 复验实例；复验仍必须保持 F09 单卡，不得通过执行 F08、修改冻结语义或执行 YAML 来消除问题。
