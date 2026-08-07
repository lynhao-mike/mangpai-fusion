# PI-390-R3 · PI-300 G3 独立复验记录

> 复验实例：PI-390-R3  
> 复验日期：2026-07-19  
> 复验对象：经 PI-360-R2 有界整改后的 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1)  
> 唯一最终裁决：**BLOCKED**

---

## 1. 独立性、范围与裁决纪律

本实例与 PI-300、PI-360-R1、PI-360-R2 分离，只进行只读设计验收。复验未修改被验收设计、PI-210／220／230、冻结契约、mapping、总控、handoff、代码或测试；唯一写入是本验收记录。未创建子任务，未递归委派，未执行 F08，未把 YAML 解释为逻辑，也未执行设计中的测试。

本记录采用 fail-closed 二值纪律：任一 High、Medium、critical ambiguity、关键证据缺失或回归均导致 BLOCKED。PI-300 的整改勾选、作者摘要及 T01–T73 的预期结果只用于定位，不能替代当前设计对象的机械证据。

裁决边界：即使 G3 通过，也只证明设计可进入 G4；不证明实现、测试执行、runtime、renderer、dispatcher、artifact coordinator、feedback fanout、production wiring 或投产能力。本次实际裁决为 BLOCKED。

---

## 2. 直接事实源

1. 前次基线：[`production-implementation-pi-390-r1-g3-acceptance.md`](production-implementation-pi-390-r1-g3-acceptance.md:1) 与 [`production-implementation-pi-390-r2-g3-reacceptance.md`](production-implementation-pi-390-r2-g3-reacceptance.md:1)。
2. 规范证据与声明绑定：[`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:1)。
3. 规范判定接口：[`GateEvaluationRecord`](production-implementation-pi-220-decision-interface.md:253)、[`ParticipationRoleRecord`](production-implementation-pi-220-decision-interface.md:319)、[`CompetitionSet`](production-implementation-pi-220-decision-interface.md:349)、[`CandidateDisposition`](production-implementation-pi-220-decision-interface.md:399)、[`DecisionEvaluationResult`](production-implementation-pi-220-decision-interface.md:558)、[`DecisionActionEnvelope`](production-implementation-pi-220-decision-interface.md:581) 与 basis 允许类型规则 [`BasisRecordIds`](production-implementation-pi-220-decision-interface.md:675)。
4. 规范追踪与 artifact：[`ArtifactRecord`](production-implementation-pi-230-traceability-binding.md:512)、[`ArtifactSetStatus`](production-implementation-pi-230-traceability-binding.md:550) 及 [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:1)。
5. G2 已接受边界：[`production-implementation-pi-290-r3-g2-reacceptance.md`](production-implementation-pi-290-r3-g2-reacceptance.md:1)。
6. F09 冻结语义：[`12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md:265)。
7. F09 声明性附录：[`real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml:451)；仅核对声明值，不执行其内容。
8. 当前验收对象全文：[`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1)。

---

## 3. PI-390-R2 两项 Medium 关闭矩阵

| R2 ID | R3 裁决 | 机械证据 |
|---|---|---|
| M-R2-01：basis／disposition refs | **NOT CLOSED** | disposition 子项已闭合，但 basis 子项仍缺一个当前 result 内的规范记录实例。详见第 4 节。 |
| M-R2-02：artifact item 状态枚举 | **CLOSED** | PI-300 逐值采用 PI-230 八值 item 枚举，明确禁止旧本地值，并将 item 与 set 聚合状态分账，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:955)；T67–T72 提供全枚举、非法旧值及 stale／mismatch／superseded 检测设计，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:874)。 |

**两项结果：1 CLOSED / 1 NOT CLOSED。**

---

## 4. 阻断发现

### M-R3-01 · basis 中 GATE-F09 无法在当前 result 解析为允许的 gate record

- **级别：Medium**
- **性质：R2 遗留未关闭 + 关键证据缺失**
- **对应对象／字段**：[`DecisionActionEnvelope.basis_record_ids`](production-implementation-pi-220-decision-interface.md:593)、[`DecisionTraceRef.basis_record_ids`](production-implementation-pi-230-traceability-binding.md:339)、[`StandardStatement.basis_record_ids`](production-implementation-pi-230-traceability-binding.md:393)

PI-220 允许 basis 引用当前 [`DecisionEvaluationResult`](production-implementation-pi-220-decision-interface.md:558) 内的 gate、participation role、competition、disposition、root／timing check 或 issue 记录，见 [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:675)。gate 记录的规范身份只能由当前 result 的 [`GateEvaluationSet.records`](production-implementation-pi-220-decision-interface.md:248) 中某个 [`GateEvaluationRecord.gate_record_id`](production-implementation-pi-220-decision-interface.md:254) 提供。

PI-300 的 action、trace、statement 三层都使用同序 basis，其中首值是 GATE-F09，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:589)、[`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:643) 和 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:665)。但 PI-300 的“设计级规范对象实例”只实际展示了：

- 六个独立 [`ParticipationRoleRecord`](production-implementation-pi-220-decision-interface.md:319)，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:451)；
- [`CompetitionSet`](production-implementation-pi-220-decision-interface.md:349)，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:479)；
- [`RootTimingConstraintCheck`](production-implementation-pi-220-decision-interface.md:476)，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:564)。

全文没有实例化任何 `gate_record_id: "GATE-F09"` 的 [`GateEvaluationRecord`](production-implementation-pi-220-decision-interface.md:253)，也没有展示包含该记录的当前 result [`GateEvaluationSet`](production-implementation-pi-220-decision-interface.md:244)。现有出现位置仅把 GATE-F09 当作 participation supporting evidence、candidate disposition supporting record、字段路径片段或 basis 裸 ID，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:468)、[`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:530) 与 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:607)。这些位置都不能机械证明它是当前 result 中的 gate record，而不是 evidence ID 或未解析裸 ID。

T59 声称每个 ID 唯一解析为允许类型，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:866)，但它是待实现测试的预期，不是当前 result 的对象实例。第 16 节整改勾选同样明确标注“非验收”，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:1059)。因此本复验不能以作者声明填补缺失记录。

### 4.1 basis 逐值机械解析矩阵

| basis 值 | 目标允许类型 | 当前设计中的实际对象 | 裁决 |
|---|---|---|---|
| GATE-F09 | [`GateEvaluationRecord`](production-implementation-pi-220-decision-interface.md:253) | 无 `gate_record_id` 实例；只有裸引用／evidence 用法 | **FAIL** |
| PR-NATAL | [`ParticipationRoleRecord`](production-implementation-pi-220-decision-interface.md:319) | 独立 role record，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:465) | PASS |
| PR-DAYUN | [`ParticipationRoleRecord`](production-implementation-pi-220-decision-interface.md:319) | 独立 role record，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:466) | PASS |
| PR-LIUNIAN | [`ParticipationRoleRecord`](production-implementation-pi-220-decision-interface.md:319) | 独立 role record，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:467) | PASS |
| PR-REALITY | [`ParticipationRoleRecord`](production-implementation-pi-220-decision-interface.md:319) | 独立 role record，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:468) | PASS |
| PR-FALSIFIER | [`ParticipationRoleRecord`](production-implementation-pi-220-decision-interface.md:319) | 独立 role record，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:469) | PASS |
| PR-SOURCE | [`ParticipationRoleRecord`](production-implementation-pi-220-decision-interface.md:319) | 独立 role record，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:470) | PASS |
| COMPETITION-F09 | [`CompetitionSet`](production-implementation-pi-220-decision-interface.md:349) | 完整 competition 对象，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:480) | PASS |
| RTC-F09-1 | [`RootTimingConstraintCheck`](production-implementation-pi-220-decision-interface.md:476) | 完整 check 对象，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:567) | PASS |

### 4.2 action → trace → statement 同一性

三层列表的顺序和值逐项相同，故“复制同一性”本身 **PASS**；但共同复制的 GATE-F09 不可解析，所以“三层有效 basis”整体 **BLOCKED**。逐值相同不能把无类型闭合的 ID 转化为允许记录。

### 4.3 disposition refs 子项

该子项 **PASS**：

1. PI-300 没有新增 `disposition_id` 或局部 schema，而是把 candidate identity 作为 payload ref 的本切片解析键。
2. 解析范围被限定为当前 envelope 的当前 [`DecisionEvaluationResult`](production-implementation-pi-220-decision-interface.md:558)，且只能进入 basis 所引用的唯一 [`CompetitionSet`](production-implementation-pi-220-decision-interface.md:349)，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:545)。
3. 每个 ref 必须恰一匹配 [`CandidateDisposition.candidate_id`](production-implementation-pi-220-decision-interface.md:400)，并与 payload 的 included candidate 对应。
4. OUTPUT 只接受 INCLUDED；CONDITIONAL 只接受 CONDITIONAL；UNRESOLVED 只支持 ABSTAIN 场景。
5. OUTPUT 与 CONDITIONAL 各自场景给出了兼容 disposition，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:523)。
6. T61–T66 覆盖正例、dangling、零匹配、多匹配和动作不兼容；T73 覆盖 ABSTAIN unresolved，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:868)。

---

## 5. ArtifactRecord.state 与 item/set 分账

PI-230 的 item 枚举为 NOT_ATTEMPTED、WRITING、WRITTEN_UNVERIFIED、VERIFIED、FAILED、STALE、MISMATCH、SUPERSEDED，见 [`ArtifactRecord.state`](production-implementation-pi-230-traceability-binding.md:525)。PI-300 在 artifact coordinator 设计中逐值列出同一八值集合，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:963)。

| PI-230 item 值 | PI-300 采用 | 测试检测 |
|---|---|---|
| NOT_ATTEMPTED | 是 | T67；T68 禁止 NOT_STARTED |
| WRITING | 是 | T67 |
| WRITTEN_UNVERIFIED | 是 | T67；T69 禁止 WRITTEN |
| VERIFIED | 是 | T67 |
| FAILED | 是 | T67，且失败注入保留 artifact attempt failure |
| STALE | 是 | T67、T70 |
| MISMATCH | 是 | T67、T71 |
| SUPERSEDED | 是 | T67、T72 |

item 状态与 set 聚合状态被明确分开：旧 revision、摘要不符、已被取代分别落在 item 的 STALE／MISMATCH／SUPERSEDED；set 则计算 COMPLETE_VERIFIED、PARTIAL、STALE_MIXED_REVISION、DIGEST_MISMATCH 等聚合结果，且只有 COMPLETE_VERIFIED 可继续 feedback-ready，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:966)。PI-300 没有再用 NOT_STARTED／WRITTEN，也明确禁止静默映射。

本项结论：**PASS，M-R2-02 CLOSED**。本结论只评价设计枚举和检测能力，不证明 artifact 实现或测试执行。

---

## 6. 完整 G3 验收矩阵

| 验收维度 | 结果 | 证据与说明 |
|---|---|---|
| F09 单卡边界 | PASS | 唯一主卡 F09；F08 仅 identity/evidence/relation/issue/source locator，禁止 F08 candidate/disposition/action/statement，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:69) 与 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:477)。 |
| 冻结语义与 YAML 边界 | PASS | F09 双轴、source、root/timing、冲突弃权与冻结契约一致；mapping 仅声明性使用，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:40)。 |
| declaration binding | PASS | 两个完整 ref 独立，validation 与 precision 不串线，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:392)。 |
| explicit-null | PASS | precision 为 null + unresolved，但 binding 仍 RESOLVED 且 ref 非空，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:426)。 |
| 五动作判别联合 | **BLOCKED** | 五个 payload 形状及 disposition 解析已闭合，但所有场景共同 basis 中 GATE-F09 无当前 result gate record 实例。 |
| participation | PASS | 六个 required role 各有独立完整 role record，容器 ID 不再冒充 basis，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:451)。 |
| root/timing | PASS | 两账本与 check 分账，禁止 timing 反写 root，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:549)。 |
| statement | **BLOCKED** | [`StatementSet`](production-implementation-pi-300-one-card-vertical-slice-design.md:633) 与 [`StandardStatement`](production-implementation-pi-300-one-card-vertical-slice-design.md:652) 字段完整，binding 与 basis 列表逐值复制；但复制的 basis 含不可解析 GATE-F09。 |
| feedback/learning | PASS | submission、七维 binding、eligibility 使用 PI-230 对象与枚举；unknown/mismatch/mixed/unsupported fail closed，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:686)。 |
| 幂等 | PASS | 采用 PI-230 key；canonical identity 包含 source digest、item IDs、statement revision 与 policy version，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:918)。 |
| 跨轨隔离 | PASS | production-default 与 staged/preprod 分账，crossing 只允许 AUDIT_ONLY，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:988)。 |
| 非原子 artifact | PASS | 不假设跨文件事务，不删除已成功项；item 八值与 set 聚合分账，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:955)。 |
| 失败注入 | PASS | input、source、normalizer、resolver、decision、competition、root/timing、statement、artifact、feedback、eligibility 均有隔离边界，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:893)。 |
| production-ready 否认 | PASS | 明确 runtime consumer、dispatcher、statement/feedback wiring 均未实现，且 card capability 固定 reference-only，见 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:30) 与 [`production-implementation-pi-300-one-card-vertical-slice-design.md`](production-implementation-pi-300-one-card-vertical-slice-design.md:669)。 |

---

## 7. Regression／falsifier 回归

| Falsifier／regression | 结果 | 裁决依据 |
|---|---|---|
| 修改冻结 F09 才能闭合 | 未触发 | 设计保持冻结语义。 |
| 执行 YAML 为逻辑 | 未触发 | 明确禁止 executable predicate。 |
| 扩展或执行 F08 | 未触发 | singleton F09 与 F08 identity-only 保持。 |
| explicit null 改 absent/unavailable | 未触发 | 正常 binding 保持 RESOLVED。 |
| validation/precision 串线 | 未触发 | 两声明身份、路径和值分账。 |
| action／trace／statement basis 不同 | 未触发 | 三层同序同值。 |
| basis 记录类型不可机械解析 | **触发** | GATE-F09 缺少当前 result 中的 [`GateEvaluationRecord`](production-implementation-pi-220-decision-interface.md:253) 实例。 |
| disposition dangling／零匹配／多匹配／不兼容 | 未触发 | 解析规则与 T61–T66、T73 已覆盖。 |
| participation 容器冒充 role record | 未触发 | 已改为六个 PR-* 记录身份。 |
| timing 反写 root | 未触发 | 两账本与 check 分离。 |
| report success 等同 artifact complete | 未触发 | PARTIAL／mixed revision／digest mismatch 均阻断 readiness。 |
| item 状态局部 schema | 未触发 | 八值逐值同构，非法旧值有负例。 |
| 不合格反馈进入学习 | 未触发 | binding／eligibility fail closed。 |
| preprod 解锁 production | 未触发 | 仅 AUDIT_ONLY crossing。 |
| 设计冒充 production ready | 未触发 | runtime、接线和测试执行均被明确否认。 |

---

## 8. T01–T73 测试充分性裁决

测试矩阵是设计充分性证据，不是测试执行证据。本次未运行测试，也不把“预期 valid”当作对象存在证明。

| 测试组 | 结果 | 说明 |
|---|---|---|
| T01–T19 | PASS（设计覆盖） | 覆盖五动作主路径、declaration 五分支、explicit-null、三轨污染、F08/F09 竞争、后果反填、root/timing 攻击与 binding 漂移。 |
| T20–T30 | PASS（设计覆盖） | 覆盖 lossy projection、非原子 artifact、未知／错 revision 反馈、幂等冲突、跨轨与 capability 误宣称。 |
| T31–T37 | PASS（设计覆盖） | 覆盖 F08 identity-only、伪造第二候选、singleton contract mismatch、声明六字段与跨层漂移。 |
| T38–T45 | PASS（设计覆盖） | 覆盖五 payload 判别联合及 StatementSet／StandardStatement 必需字段。 |
| T46–T58 | PASS（设计覆盖） | 覆盖 participation、root/timing、feedback/eligibility 全字段与 canonical identity 变化。 |
| T59–T60 | **INSUFFICIENT / BLOCKED** | T60 能捕获容器冒充 role；T59 只声明 GATE-F09 可解析，却没有当前 result gate record fixture／实例作为正例前置。它不能自行证明该 ID 的记录类型。 |
| T61–T66、T73 | PASS（设计覆盖） | disposition 当前 result 限定、恰一匹配、dangling、零、多和动作兼容均有精确正负例。 |
| T67–T72 | PASS（设计覆盖） | 八值正例、两个非法旧值及 item stale／mismatch／superseded 与 set 分账均被检测。 |

**总体：T01–T73 的攻击面覆盖已显著增强，但 T59 的正例没有由当前 result 的 gate record 实例闭合；因此测试设计不能支撑 G3 PASS。**

---

## 9. 精确统计

- High：**0**
- Medium：**1**
- critical ambiguity：**0**
- 关键证据缺失：**1 类**
  1. GATE-F09 在各场景当前 [`DecisionEvaluationResult`](production-implementation-pi-220-decision-interface.md:558) 中唯一解析为 [`GateEvaluationRecord`](production-implementation-pi-220-decision-interface.md:253) 的对象证据。
- 新回归：**0**
- PI-390-R2 两项：**1 CLOSED / 1 NOT CLOSED**

计数说明：disposition 子项已关闭；六个 participation、competition、root/timing check 也已闭合。仅 GATE-F09 缺失导致 basis 整体失败，故按一个 Medium 和一类关键证据缺失计数，不重复计 action、trace、statement 三层。

---

## 10. 唯一最终裁决

# BLOCKED

理由：PI-390-R2 的 M-R2-01 未完全关闭。action、trace、statement 共同引用的 GATE-F09 无法从 PI-300 展示的各场景当前 result 机械解析到 PI-220 允许的 gate record 类型。合计 **0 High、1 Medium、0 critical ambiguity、1 类关键证据缺失、0 新回归**。按 fail-closed 纪律，不能以 T59 的设计声明或整改勾选替代缺失对象。

---

## 11. 状态建议

1. G3 保持阻断；PI-300 不标记 accepted/completed，不进入 G4，不启动一卡实现，不改变 production-default。
2. 本复验只指出缺口，不修复设计；整改责任仍属于 PI-300 设计责任方。
3. 后续复验必须继续保持 F09 单卡、F08 identity-only、YAML 非执行、冻结语义不变和 preprod/staged 隔离。
4. 后续可验收证据必须在每个互斥场景的当前 result 中提供可唯一解析的 GATE-F09 gate record，并再次核对 action → trace → statement basis 逐值同一；不能只增加作者声明或测试期望。

本记录不证明任何测试已执行，也不证明 runtime、renderer、dispatcher、artifact coordinator、feedback fanout、learning 或 production wiring 已实现或可投产。
