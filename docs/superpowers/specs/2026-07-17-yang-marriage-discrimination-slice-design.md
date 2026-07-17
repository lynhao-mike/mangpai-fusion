# 杨派 × 婚姻判别力切片设计规格

> 状态：已批准方向的设计规格；只定义目标契约，不包含代码或实施计划。
> 日期：2026-07-17
> 第一阶段边界：仅证明杨派婚姻原局判别器能稳定区分 `pressure / event / abstain`，且只有 `event` 获准进入 L3-L6。第一阶段不改 L7、报告模板、默认生产入口、概率、公共 `Claim` schema 或 production claim YAML。

## 1. 背景与当前误判链证据

仓库已经把 `marriage.divorce_or_remarriage` 定义为高风险二元事件任务，并明确“只评价是否发生，不把关系压力自动等同离婚”，见 [`META/prospective-go-task-catalog-v1.json`](../../../META/prospective-go-task-catalog-v1.json:29)。现有杨派 runner 也声明“一般关系压力不升格为事件”，见 [`generate_claims()`](../../../engine/v5/yang_runner.py:46)。但当前实现仍存在一条可机械复现的误判链：

1. [`_palace_disruption()`](../../../engine/v5/yang_runner.py:38) 将夫妻宫冲与刑害汇总为宫位受扰，并仅在 pair 层做局部去重。
2. [`generate_claims()`](../../../engine/v5/yang_runner.py:82) 把 `spouse_palace_disrupted`、`spouse_star_weak`、`peer_competition`、`output_spouse_conflict`、`female_mixed_official`、`compound_distinct_palace_pairs` 六个布尔量直接相加为 `independent_signal_count`。
3. 这些布尔量并非六个独立结构家族。例如“夫妻宫受扰”和“宫位存在两个不同冲刑害 pair”都来自夫妻宫事件锚；“配偶星弱”与“食伤制配偶星”都依赖配偶星家族。直接计数会把同源结构重复算成独立证据。
4. production candidate 规则只要求 `independent_signal_count >= 2`，见 [`YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1`](../../../theory/production/claim-rules-v1.yaml:234)。因此两个同源宫位信号，或两个没有夫妻宫事件锚的非宫位信号，理论上都可把关系压力升级为离婚或再婚事件。
5. 一旦 runner 返回 `Claim`，公共编排器即把非空结果转换成 `claim`，只有空列表才转为 `abstain`，见 [`generate_blind_outputs()`](../../../engine/claims/orchestrator.py:70)。公共输出没有 `pressure` 状态；其状态只有 `claim / abstain / unsupported`，见 [`BlindSchoolOutput`](../../../engine/evaluation/models.py:110)。
6. 进入 decision 链后，通用 L3 对 `event_claim` 默认给出 `weaken` 而非拒绝，见 [`build_structural_verdicts()`](../../../engine/decision/l3_structure.py:37)；L4 会把 `pass / weaken` 的事件命题转为现实事件，见 [`build_event_hypotheses()`](../../../engine/decision/l4_events.py:49)。于是“同源信号被计为两证”可沿 L2 → L3 weaken → L4 婚变 → L5 → L6 继续传播。
7. 现有单信号测试只证明宫冲、配偶星弱、单独比劫压力会返回空列表，见 [`test_yang_abstains_for_single_signal_relationship_pressure_or_missing_gender()`](../../../tests/claims/test_school_strength_runners.py:277)；它没有覆盖“双信号但同一家族”“夫妻宫锚缺失但两类非宫位信号成立”“pressure 必须可观测但不得进入 L3-L6”三条关键边界。
8. 理论源本身要求联合条件：男命规则把比劫、财星和妻宫共同受损绑定，且该规则已有失验记录，见 [`M2-Y-068`](../../../theory/yang/index.yaml:560)；女命规则也把夫妻宫受损与配偶星结构并看，见 [`M2-Y-088`](../../../theory/yang/index.yaml:868)。因此切片应修正“独立性判别”，而不是扩大铁断。

结论：当前问题不是缺少更多婚姻规则，而是缺少位于公共 `Claim` 之前的局部判别边界。第一阶段必须先把关系压力与事件资格分开，证明判别力后再讨论生产规则与报告。

## 2. 目标、非目标与阶段不变量

### 2.1 目标

1. 在杨派婚姻切片内部定义且只定义 `pressure / event / abstain` 三态。
2. 对原始信号按结构家族去重，禁止同源布尔量冒充独立证据。
3. 将 `event` 的必要门固定为“夫妻宫事件锚 + 至少一个独立配偶结构交互”。两部分缺一不可。
4. 只有 `event` 能转换为现有 L2 `SchoolClaim` 并进入 L3-L6；`pressure` 和 `abstain` 在切片边界终止。
5. 采用局部不可变 DTO 保存判别状态、家族证据、阻断原因与证伪口径，不修改公共 `Claim`。
6. 按 [`apply_ziping_career_slice()`](../../../engine/decision/r10_ziping_career.py:52) 的“目标命题先剥离、切片原生处理、非目标走旧桥、合并后去重、直接调用下层”的方式接入，但仅覆盖杨派婚姻目标。
7. 用全新合成夹具建立可机械执行的正例、稳定反例、pressure、单信号、缺输入和去重门禁。
8. 明确第一阶段结论只能是“切片行为符合规格”或“切片被证伪”，不得声明准确率提升、GO 或生产替换资格。

### 2.2 非目标

第一阶段明确不做：

- 不修改 L7、[`ReportViewItem`](../../../engine/decision/models.py:240)、任何报告渲染器或模板。
- 不修改默认生产入口 [`run_pipeline()`](../../../engine/application/pipeline_runner.py:33)。
- 不修改默认 [`DEFAULT_RUNNER_REGISTRY`](../../../engine/claims/runner_registry.py:51) 或其注册摘要护栏。
- 不修改概率值、置信度公式、`base_confidence`、高风险封顶或概率展示。
- 不修改公共 [`Claim`](../../../engine/claims/domain.py:68)、[`SchoolClaim`](../../../engine/decision/models.py:114)、[`BlindSchoolOutput`](../../../engine/evaluation/models.py:110) schema。
- 不修改 [`theory/production/claim-rules-v1.yaml`](../../../theory/production/claim-rules-v1.yaml:234) 中现有杨派 production candidate 规则，不新增、替换或 staged 标记生产规则。
- 不新增公共 `marriage.relationship_pressure` task 或改变现有任务目录。
- 不做应期推导，不读取大运流年作为第一阶段事件资格条件。
- 不改段派婚姻 runner；其当前独立信号计算见 [`_marriage_divorce_or_remarriage()`](../../../engine/v5/duan_runner.py:236)，只作跨实现风险参照。
- 不把历史案例或历史冻结制品用于阈值调参。

### 2.3 第一阶段不变量

- `pressure` 不等于事件，不得以 `event_claim`、L3 verdict、L4 event、L5 timing 或 L6 decision 的形式出现。
- `abstain` 表示无法形成可负责的杨派婚姻判断，不等于稳定婚姻或事件未发生。
- `event` 仅表示满足原局事件资格，仍是不必然的高风险命题；不得使用“必离”“多婚命”等铁断。
- 同一结构家族对资格门最多贡献一次。
- production claim YAML 在切片证明前保持字节和语义不变；切片通过也只触发后续独立决策，不自动替换生产规则。
- [`test_default_runner_registry_registrations_are_unchanged()`](../../../tests/test_production_entrypoints_unchanged.py:39) 与 [`test_run_pipeline_signature_and_defaults_are_unchanged()`](../../../tests/test_production_entrypoints_unchanged.py:35) 所表达的生产稳定边界继续成立。

## 3. 术语与三态语义

### 3.1 术语

| 术语 | 定义 | 非定义 |
|---|---|---|
| 原始信号 | 从性别、四柱及 CFV 直接读取的最小事实或派生布尔量 | 不是独立证据数 |
| 结构家族 | 共享同一命理因果来源的一组原始信号 | 不是每个字段各算一家 |
| 夫妻宫事件锚 | 日支夫妻宫存在可定位、去重后的直接结构受扰，并达到事件锚口径 | 不是全局支冲强度，也不是任何非日支冲刑害 |
| 独立配偶结构交互 | 与夫妻宫事件锚不同家族，且显式涉及性别对应配偶星与另一结构发生关系 | 不是单纯“配偶星少”或无配偶星上下文的全局比劫、食伤计数 |
| 稳定反例 | 输入完整，但夫妻宫事件锚缺失，或仅有稳定/保护性结构，必须禁止事件升级的合成样本 | 不是对现实婚姻稳定的预测 |
| 切片证明 | 合成测试矩阵与层级隔离机械通过 | 不是准确率证明、GO 或生产授权 |

### 3.2 三态

| 状态 | 精确语义 | L2-L6 权限 | 对外映射 |
|---|---|---|---|
| `event` | 夫妻宫事件锚成立，且至少一个独立配偶结构交互成立；输入完整且无硬阻断 | 唯一可转换为 L2 `SchoolClaim` 并进入 L3-L6 的状态 | 第一阶段只在切片测试制品可见；若经既有兼容边界转换，仍使用现有非必然事件文案 |
| `pressure` | 存在一项或多项可解释的关系压力结构，但不满足 event 必要门；证据足以说明“为何不升级” | 禁止进入 L2-L6；切片内部保留用于审计和后续报告降噪研究 | 第一阶段不得映射到公共 `Claim` 或新增公共 task |
| `abstain` | 性别、四柱、日支、证据完整度或必要派生事实缺失/非法，或没有足以形成杨派婚姻判断的信号 | 禁止进入 L2-L6 | 在需要兼容盲测网格时仍由现有边界表现为 `abstain`，但原因必须来自切片结果而非统一的“未触发 production rule”文案 |

状态优先级固定为：硬阻断先判 `abstain`；无硬阻断时先检查 `event` 必要门；必要门未全过但存在压力家族则为 `pressure`；既无事件资格又无压力证据则为 `abstain`。不得把 `pressure` 降格为“无信号”，也不得把 `abstain` 解读为负例。

## 4. 架构与数据流

### 4.1 第一阶段目标流

```text
ChartFactLedger + ChartFeatureVector
  → YangMarriageSignalExtractor
  → 原始信号集合
  → YangMarriageFamilyReducer
  → 去重后的结构家族集合
  → YangMarriageDiscriminator
      ├─ event
      │   → 局部 event adapter
      │   → SchoolClaim
      │   → L3
      │   → L4
      │   → L5
      │   → L6
      ├─ pressure
      │   → 切片审计终点
      └─ abstain
          → 切片审计终点

非杨派婚姻目标
  → 既有兼容路径保持不变
```

第一阶段不触碰 L7 与报告。现有目标主流程要求事件经结构、事件、概率应期与仲裁后才进入报告，见 [`engine/contracts/00-OVERVIEW.md`](../../../engine/contracts/00-OVERVIEW.md:53)；本切片只修正 L2 之前的资格判别及 L2-L6 入口，不越权改变表达层。

### 4.2 组件职责

1. **SignalExtractor**：只读取 [`ChartFactLedger`](../../../engine/decision/models.py:43) 与 [`ChartFeatureVector`](../../../engine/features/types.py:20)，产出规范化原始信号；不计分、不定状态。
2. **FamilyReducer**：按 §5 的家族键归并；同一家族可保留多个 evidence ref，但资格贡献固定为 0 或 1。
3. **Discriminator**：按 §6 的必要门产出一个局部不可变结果；不构造公共 `Claim`。
4. **Event adapter**：只接受 `state=event`；转换为现有 [`SchoolClaim`](../../../engine/decision/models.py:114) 或现有兼容 `Claim` 所需字段。收到其他状态必须 fail-closed。
5. **Slice assembler**：参照 R10 的目标剥离与直接下层调用模式。它不得把目标杨派婚姻命题再次送入 [`v5_adapter._claims()`](../../../engine/decision/v5_adapter.py:73)，避免双路径和重复 ID。
6. **Audit projection**：第一阶段只供测试读取三态、家族与阻断原因，不成为公共持久化 schema，不进入报告。

## 5. 结构家族去重

### 5.1 家族定义

第一阶段固定四个 event 资格家族与两个 pressure-only 家族：

| 家族键 | 可包含的原始信号 | 对 event 的角色 |
|---|---|---|
| `spouse_palace_event_anchor` | 日支参与的冲；日支参与的刑/害；多个不同日支 pair | 唯一夫妻宫事件锚家族；无论命中多少 pair，只贡献一个锚 |
| `spouse_star_peer_interaction` | 男命财星与比劫竞争；必须同时有性别对应配偶星上下文和比劫结构 | 可作为独立配偶结构交互 |
| `spouse_star_output_interaction` | 女命官杀与食伤冲突；必须同时有官杀上下文和食伤结构 | 可作为独立配偶结构交互 |
| `spouse_star_configuration` | 女命正官/七杀混杂 | 可作为独立配偶结构交互；同源别名只保留一次 |
| `spouse_star_context_pressure` | 性别对应配偶星弱、少或缺失，但没有与另一结构形成交互 | 只能支持 `pressure`，永不通过门 B |
| `ambient_relationship_pressure` | 缺少配偶星交互上下文的全局比劫偏重或食伤偏重 | 只能支持 `pressure`，永不通过门 B |

`spouse_star_weak` 归入 `spouse_star_context_pressure`，第一阶段不把它作为独立 event 交互家族。原因是“弱/缺失”本身没有表达与另一结构的交互，且现有实现会把“配偶星不存在”也算一个正向风险信号，见 [`generate_claims()`](../../../engine/v5/yang_runner.py:66)。pressure-only 家族只用于解释为何保留压力态，不能与门 A 组合后充当门 B。

### 5.2 去重规则

1. 同一个无序 pair 在冲与刑害集合中重复出现，只保留一个 canonical pair。
2. 同一日支与多个其他支形成多个 pair，可增强家族内部说明，但 `spouse_palace_event_anchor` 资格贡献仍为 1。
3. `palace_disrupted` 与 `compound_distinct_palace_pairs` 禁止分别计数；二者必须归并至同一夫妻宫家族。
4. 配偶星存在、配偶星计数、配偶星弱是同一配偶星上下文，不得彼此相加。
5. `peer_competition` 只有与男命财星上下文形成显式交互时才进入 `spouse_star_peer_interaction`；全局比劫多但无财星上下文只能形成 pressure。
6. `output_heavy` 只有与女命官杀上下文形成显式交互时才进入 `spouse_star_output_interaction`；全局食伤多但无官杀上下文只能形成 pressure。
7. `female_mixed_official` 与由相同正官/七杀计数推导的其他“官杀并见”别名必须归并为一个 `spouse_star_configuration` 家族。
8. 家族集合使用稳定排序与不可变 tuple；相同输入的家族顺序、state、reason code 和 ID 必须确定性一致。
9. 禁止用 `branch_conflict_intensity` 作为第五个独立家族；它是全局强度摘要，只可作家族内部说明。

## 6. `event` 必要门

### 6.1 门 A：夫妻宫事件锚

门 A 通过必须同时满足：

- 四柱完整且日柱恰为两个干支字符；
- 能确定日支；
- 至少一个 canonical pair 明确包含日支；
- 该 pair 属于当前切片允许的宫位受扰关系，即冲或刑/害；
- pair 已按 §5 去重。

全局存在冲、刑、害但不涉及日支，门 A 不通过。`he_pairs` 第一阶段不作为负面事件锚；合、暗合、合绊未来可作为 pressure 或保护/复杂化结构研究，但不得在本阶段直接升级离婚或再婚事件。

### 6.2 门 B：独立配偶结构交互

门 B 通过必须满足至少一个与门 A 不同家族的交互：

- 男命：性别对应配偶星为财，且财星上下文与比劫竞争形成显式交互；或
- 女命：性别对应配偶星为官杀，且官杀与食伤形成显式交互；或
- 女命：正官与七杀复合配置成立，归入 `spouse_star_configuration`；或
- 后续经独立规格批准的其他杨派配偶结构交互。

门 B 不接受：单纯配偶星缺失、单纯配偶星数量少、单纯全局比劫多、单纯全局食伤多、单纯全局支冲强度。

### 6.3 状态判定表

| 输入条件 | 输出 |
|---|---|
| 有硬阻断 | `abstain` |
| 门 A 通过且门 B 通过 | `event` |
| 门 A 通过、门 B 不通过，但存在宫位压力 | `pressure` |
| 门 A 不通过、存在一个或多个非宫位压力/配偶交互家族 | `pressure` |
| 门 A 与门 B 都不通过，且无可解释压力家族 | `abstain` |

禁止以“去重后家族总数 >= 2”替代 A+B。必要门是具名合取，不是计数阈值。

## 7. 局部不可变 DTO 建议

以下是语义建议，不是公共 schema 变更。实现可使用 `frozen dataclass` 与 tuple，风格与现有不可变 [`Claim`](../../../engine/claims/domain.py:67) 和 [`ChartFeatureVector`](../../../engine/features/types.py:19) 一致。

### 7.1 `YangMarriageFamilyEvidence`

| 字段 | 约束 |
|---|---|
| `family_key` | 仅允许 §5.1 固定的 event 资格家族键或 pressure-only 家族键 |
| `matched` | 严格布尔值 |
| `fact_refs` | 去重、稳定排序、不可变 tuple；只引用真实 chart facts |
| `feature_refs` | 去重、稳定排序、不可变 tuple；只引用 CFV 已有字段 |
| `canonical_pairs` | canonical 无序 pair 的稳定 tuple；非 pair 家族为空 |
| `reason_codes` | 稳定、机器可断言的非空 tuple |
| `detail` | 审计文本；不得含概率、应期或报告话术 |

### 7.2 `YangMarriageDiscrimination`

| 字段 | 约束 |
|---|---|
| `schema_version` | 局部版本，例如 `yang-marriage-discrimination/v1`；不注册为公共 Claim schema |
| `case_id` | 非空 |
| `state` | `pressure / event / abstain` 三选一 |
| `sex_basis` | `male_wealth / female_official / unknown` |
| `spouse_palace_branch` | 合法日支或空；为空时 state 必须为 `abstain` |
| `families` | 全部家族证据的稳定 tuple |
| `event_anchor_passed` | 严格布尔值 |
| `independent_spouse_interaction_passed` | 严格布尔值 |
| `blocking_reason_codes` | `event` 时必须为空；其他状态至少一项 |
| `falsifier` | `event` 必须绑定“婚姻史无离婚或再婚则证伪”；`pressure` 绑定“存在压力不等于事件”；`abstain` 绑定“补齐输入后重算”或“无足够杨派信号” |
| `source_rule_refs` | 只引用理论来源；第一阶段不得假称已替换 production rule |

DTO 构造时应强制以下一致性：

- `event` 当且仅当两个必要门都为真且无 blocker。
- `pressure` 至少有一个 matched family，但两个必要门不同时为真。
- `abstain` 不得携带可进入 L2 的 event payload。
- `families` 中每个 `family_key` 最多出现一次。
- DTO 不包含概率、星级、time window、L7 display text 或公共 claim 状态。

## 8. R10 式切片接入

接入形态遵循 [`apply_ziping_career_slice()`](../../../engine/decision/r10_ziping_career.py:52) 已证明的纵切片模式，但目标缩小为“杨派 + 婚姻 + divorce/remarriage 资格”：

1. 目标选择器只匹配 school 为杨派、domain 为婚姻、task 为 `marriage.divorce_or_remarriage` 的候选。
2. 在调用 legacy adapter 前，从旧输出中剥离全部目标候选；非目标命题原样交给旧路径。
3. 由局部 extractor、reducer、discriminator 基于 chart 与 CFV 生成唯一三态结果。
4. 仅当状态为 `event` 时构造一个目标 `SchoolClaim`；其文案继续采用非必然风险语义，且 evidence refs 必须来自两个必要门的家族证据。
5. `pressure` 与 `abstain` 均不构造目标 `SchoolClaim`。
6. 合并 legacy L2 与原生目标 L2 后，按 claim ID 全局拒绝重复，行为对齐 [`_reject_duplicate_claim_ids()`](../../../engine/decision/r10_ziping_career.py:44)。
7. 合并后的完整 L2 集合直接进入 [`build_structural_verdicts()`](../../../engine/decision/l3_structure.py:37)、[`build_event_hypotheses()`](../../../engine/decision/l4_events.py:49)、[`build_timing_probabilities()`](../../../engine/decision/l5_timing.py:24) 与 [`build_arbitration_decisions()`](../../../engine/decision/l6_arbitration.py:15)。
8. 对目标三态做反向护栏：若 `pressure` 或 `abstain` 对应的 ID/marker 出现在 L2、L3、L4、L5 或 L6，切片验收失败。
9. 第一阶段不将该 assembler 接到默认生产入口或默认 registry；只能由专用切片测试入口显式调用。

## 9. 错误与保守策略

| 情况 | 策略 |
|---|---|
| 缺 sex marker 或未知性别 | `abstain`，reason code 为 `missing_or_unknown_sex` |
| 四柱缺失、日柱非法、日支不可解析 | `abstain`，不得猜测 |
| CFV 构造失败或 evidence completeness 非 full | `abstain`；与现有 runner 的完整度保守边界一致，见 [`generate_claims()`](../../../engine/v5/yang_runner.py:54) |
| pair 非二元、含非法地支、结构自相矛盾 | fail-closed 为 `abstain`；测试入口可抛契约错误，但不得降级成 event |
| 同一 pair 跨集合重复 | canonical 去重，不报多证 |
| 只有夫妻宫锚 | `pressure` |
| 只有配偶结构交互，无夫妻宫锚 | `pressure` |
| 只有配偶星弱/缺失 | `pressure`，归入 `spouse_star_context_pressure`，绝不为 event |
| 既有 production rule 与切片结果冲突 | 第一阶段以切片结果作为专用切片测试事实；production YAML 保持不变并记录冲突，不回写、不自动 staged |
| event adapter 收到非 event | fail-closed，拒绝构造 `SchoolClaim` |
| 非目标旧路径异常 | 保持既有错误策略；切片不得吞掉或改写 |
| 无法证明两个家族独立 | 按不独立处理，降为 `pressure` |

保守原则是“宁可保留 pressure 或 abstain，也不把关系压力升级为高风险事件”。这与高风险冲突需保守处理的系统方向一致，且不改变现有概率或仲裁策略。

## 10. 合成测试矩阵

第一阶段唯一机械门禁使用全新合成夹具。每个夹具显式构造 chart、CFV 信号、预期家族、预期三态、预期 L2-L6 数量；不得从历史 case 复制反馈标签或根据历史结果调阈值。

| 类别 | 合成条件 | 预期 state | 家族断言 | L2-L6 断言 |
|---|---|---|---|---|
| 正例 M1 | 乾造；日支受冲；财星存在；比劫与财形成交互 | `event` | A=`spouse_palace_event_anchor`，B=`spouse_star_peer_interaction`；各一次 | 目标 L2=1，L3=1，L4=1，L5=1，L6 婚姻 decision 可追溯 |
| 正例 F1 | 坤造；日支受刑/害；官杀存在；食伤与官杀交互 | `event` | A + `spouse_star_output_interaction` | 同上 |
| 正例 F2 | 坤造；日支受冲；正官七杀混杂 | `event` | A + `spouse_star_configuration` | 同上 |
| 稳定反例 S1 | 输入完整；夫妻宫无冲刑害；配偶星上下文正常；无交互压力 | `abstain` | 无 matched event 家族 | 目标 L2-L6 全 0 |
| 稳定反例 S2 | 输入完整；仅非日支支冲强，夫妻宫不参与 | `pressure` 或无其他压力时 `abstain`；固定夹具应选择无其他压力并断言 `abstain` | A=false | 目标 L2-L6 全 0 |
| pressure P1 | 夫妻宫受冲，但无独立配偶结构交互 | `pressure` | 仅 A | 目标 L2-L6 全 0 |
| pressure P2 | 财星与比劫交互成立，但夫妻宫无事件锚 | `pressure` | 仅 B | 目标 L2-L6 全 0 |
| pressure P3 | 女命官杀混杂，但夫妻宫无事件锚 | `pressure` | 仅 `spouse_star_configuration` | 目标 L2-L6 全 0 |
| 单信号 G1 | 仅配偶星弱/缺失 | `pressure` | 仅 `spouse_star_context_pressure`；不得形成 event B 家族 | 目标 L2-L6 全 0 |
| 单信号 G2 | 仅全局比劫多，无财星交互 | `pressure` | 仅 `ambient_relationship_pressure`；不得形成 `spouse_star_peer_interaction` | 目标 L2-L6 全 0 |
| 单信号 G3 | 仅全局食伤多，无官杀交互 | `pressure` | 仅 `ambient_relationship_pressure`；不得形成 `spouse_star_output_interaction` | 目标 L2-L6 全 0 |
| 缺输入 I1 | 缺 sex marker | `abstain` | blocker 精确匹配 | 目标 L2-L6 全 0 |
| 缺输入 I2 | 缺日柱或日柱非法 | `abstain` | 无猜测日支 | 目标 L2-L6 全 0 |
| 缺输入 I3 | evidence completeness 为 partial/no_hour | `abstain` | blocker 精确匹配 | 目标 L2-L6 全 0 |
| 去重 D1 | 同一日支 pair 同时出现在 chong 与 xing_hai | `pressure`，若无 B | A 只出现一次，canonical pair 只出现一次 | 目标 L2-L6 全 0 |
| 去重 D2 | 日支存在两个不同受扰 pair，但无 B | `pressure` | A 仍只贡献一次 | 目标 L2-L6 全 0 |
| 去重 D3 | 女命正官/七杀计数与 mixed flag 同源重复 | 取决于 A；无 A 时 `pressure` | `spouse_star_configuration` 只出现一次 | 无 A 时目标 L2-L6 全 0 |
| 去重 D4 | A + 同一 B 的多个别名/字段同时命中 | `event` | 仅 A+B 两家族，不按字段膨胀 | 每层目标对象最多一个 |
| 决定性 R1 | 同一输入重复运行及 pair 输入顺序交换 | 状态相同 | DTO、家族顺序、稳定 ID 相同 | L2-L6 序列化相同 |
| 非目标 N1 | 同一 run 含非杨派或非婚姻命题 | 不适用 | 目标剥离不影响非目标 | 非目标对象与旧路径逐字段相等 |

“稳定反例”只证明切片不会把无锚结构升级为事件，不声明现实婚姻必然稳定。

## 11. 历史夹具隔离

1. 第一阶段机械门禁只使用全新合成夹具；测试 fixture 名称、case ID 和数据不得复用正式 case ID。
2. 历史 case、feedback、report、已冻结 run、既有 R6/R10 基线全部只读，不得作为阈值选择、家族划分或 expected state 的来源。
3. [`tests/r10/fixtures/r6_ziping_career_baseline.json`](../../../tests/r10/fixtures/r6_ziping_career_baseline.json:1) 继续服务子平事业切片，不得扩写杨派婚姻字段。
4. 历史门禁与生产入口 hash 护栏继续原样执行，见 [`tests/test_production_entrypoints_unchanged.py`](../../../tests/test_production_entrypoints_unchanged.py:13)。
5. 可选历史只读对照只允许回答“新切片与旧输出有何差异”，结果必须标记 non-gating、non-tuning、non-calibration；差异不得反向修改合成预期。
6. 禁止把历史 `feedback.md`、报告文本或人工标签导入切片 runner；现有 runner 无反馈/报告 import 的静态护栏见 [`test_loader_and_migrated_runners_do_not_use_dynamic_execution_or_revealed_inputs()`](../../../tests/claims/test_executable_claim_rules.py:371)。
7. 禁止改写任何不可变 prospective frozen run；切片验证必须生成临时内存对象或测试目录制品。

## 12. 验收标准

以下条件必须全部机械通过；任一失败即第一阶段未验收：

1. **三态完备**：测试矩阵中每个夹具恰好得到一个 `pressure / event / abstain` 状态。
2. **必要门等价**：所有 `event` 均满足 `event_anchor_passed=true` 且 `independent_spouse_interaction_passed=true`；所有满足两门且无 blocker 的合成正例均为 `event`。
3. **层级隔离**：所有 `pressure` 与 `abstain` 夹具在目标 L2、L3、L4、L5、L6 的对象数均为 0。
4. **event 链完整**：每个 event 正例恰有一个目标 L2 claim、一个绑定该 claim 的 L3 verdict、一个绑定该 verdict 的 L4 event、一个绑定该 event 的 L5 timing，以及包含该 event 的婚姻 L6 decision；完整 `DecisionRun.validate_trace()` 返回空，校验契约见 [`DecisionRun.validate_trace()`](../../../engine/decision/models.py:329)。
5. **家族唯一**：每个 DTO 的 `family_key` 无重复；D1-D4 去重夹具的 canonical pair 与家族计数符合 §10。
6. **无计数替代**：测试源码或切片判别路径不得以 `independent_signal_count >= 2` 作为 event 充分条件；机械测试应构造“总信号数不少于 2 但 A 缺失”并断言非 event。
7. **确定性**：R1 重跑与 pair 顺序置换后，DTO 序列化、稳定 ID、L2-L6 目标对象序列化一致。
8. **非目标零回归**：N1 中非目标 L2-L6 对象与切片前旧路径逐字段相等。
9. **公共契约未变**：公共 [`Claim`](../../../engine/claims/domain.py:68)、[`SchoolClaim`](../../../engine/decision/models.py:114)、[`BlindSchoolOutput`](../../../engine/evaluation/models.py:110) 字段集合不变；默认 registry digest 与 pipeline signature 护栏通过。
10. **生产规则未变**：[`theory/production/claim-rules-v1.yaml`](../../../theory/production/claim-rules-v1.yaml:234) 中杨派规则的字节或规范化摘要与第一阶段基线一致。
11. **报告边界未变**：L7、模板、默认报告入口没有切片分支；测试应证明专用切片在不调用报告 renderer 时可独立验收。
12. **概率未变**：切片 DTO 不含概率；event adapter 沿用现有值，不新增重算、缩放或校准。
13. **历史隔离**：门禁测试只引用专用合成 fixtures；扫描不得发现 `cases/`、`reports/`、历史 feedback 或 frozen run 路径。
14. **文案保守**：event statement 不含“必离”“100%”“多婚命”；pressure 不含离婚或再婚已成立语义。
15. **规格质量**：本文无未决占位标记，无互相冲突的阶段边界，且所有验收项可由断言、摘要或静态扫描执行。

验收通过只允许表述为：“杨派婚姻判别切片在合成矩阵上满足三态、去重、必要门与层级隔离规格。”不得表述为准确率提升、可以 GO、可切生产或可替换规则。

## 13. 首个证伪点

首个证伪点固定为**无夫妻宫事件锚的双非宫位信号样本**：输入完整，构造两个或更多当前旧实现会计入 `independent_signal_count` 的非宫位信号，例如配偶星弱加比劫压力，或女命官杀混杂加食伤压力，但日支不参与任何冲刑害。

预期：新切片必须输出 `pressure`，且目标 L2-L6 全为空。

若该样本仍输出 `event` 或产生任何目标 L2-L6 对象，则证明以下至少一项失败：

- 实现仍在使用总信号计数替代具名必要门；
- 配偶结构家族没有与夫妻宫家族独立；
- pressure 隔离边界失效；
- R10 式目标剥离存在旁路，旧杨派 event claim 仍进入 adapter。

出现该证伪结果时必须停止第一阶段，不得通过提高阈值、改概率、改报告文案或修改 production YAML 掩盖失败。

## 14. 风险与回退

| 风险 | 影响 | 规格内控制 | 回退 |
|---|---|---|---|
| 家族划分仍把同源变量拆开 | 假独立证据继续升级 event | 固定家族键、D1-D4 去重矩阵、具名 A+B 门 | 停用专用切片入口，恢复旧测试路径；production 未改，无生产数据迁移 |
| 门槛过严导致 event 覆盖下降 | 更多 pressure/abstain | 第一阶段不以覆盖率为成功标准，不调概率 | 保留结果为证伪材料，不替换 production 规则 |
| pressure 丢失可解释性 | 后续报告无法降噪而只剩弃权 | DTO 保留 matched families 与 blockers | 回退到内部审计，不进入公共输出 |
| 双路径产生重复 claim | 同一事件重复进入 L3-L6 | 目标先剥离、合并后拒绝重复 ID | 专用 assembler fail-closed，不调用下层 |
| 局部 DTO 演变为第二套公共 Claim | 契约分裂 | DTO 禁止概率、time window、L7 字段，仅作切片判别结果 | 保持 DTO 私有，不持久化为公共制品 |
| 历史样本泄漏进调参 | 合成门禁失真 | 路径静态扫描、历史只读对照标记 | 删除受污染测试结果，重建全新合成夹具 |
| 先改 production YAML 再证明 | 生产规则先行、回退复杂 | 摘要护栏与明确不变量 | 任何 YAML 变化均判第一阶段失败并恢复原字节 |
| 把 pressure 写成离婚风险 | 高风险表达扩大 | pressure 文案禁用事件成立语义 | 第二阶段报告工作继续 HOLD |

由于第一阶段不切默认入口、不改 schema、不改生产规则和历史制品，回退是删除或停止调用专用切片入口及其合成测试制品；不需要迁移生产数据，也不得覆盖历史冻结结果。

## 15. 第二阶段后置边界

以下工作只有在 §12 全部通过且首个证伪点未触发后，才能另立规格与批准；第一阶段不得预实现。

### 15.1 报告降噪

- 目标是让报告区分“事件资格”“关系压力”“证据不足”，避免把 pressure 渲染成离婚或再婚。
- 必须单独评审 L7 消费契约、模板占位、命理师可读措辞与反馈问题。
- 在此之前，[`ReportViewItem`](../../../engine/decision/models.py:240)、[`tools/render_report.py`](../../../tools/render_report.py:1) 和模板保持不变。
- 报告优化不能反向改变第一阶段判别 state，也不能通过话术把 pressure 升格为 event。

### 15.2 公共 pressure 契约

- 第二阶段可评估是否需要公共 `pressure`，但不得直接把它塞入现有 `ClaimStance`；当前 [`Claim`](../../../engine/claims/domain.py:68) 的 stance 仅为 support/oppose，盲测输出状态仅为 claim/abstain/unsupported。
- 可选方向必须另行比较：新增独立 pressure observation、扩展任务目录、或只在 L7 ViewModel 表达。
- 任何公共契约变化都必须版本化、提供兼容与迁移策略，并重新评审冻结制品 hash、评分分母和反馈语义。
- pressure 不得进入 `marriage.divorce_or_remarriage` 的正例概率评分；否则会重新制造“压力=事件”的标签污染。

### 15.3 应期

- 应期只能消费已经通过 event 必要门并完成 L3/L4 的事件；pressure 与 abstain 不得生成离婚/再婚 time window。
- 第二阶段应优先接真实 `liunian_steps` 与事件触发证据，不能沿用 [`build_timing_probabilities()`](../../../engine/decision/l5_timing.py:24) 的 MVP 默认时间窗作为杨派婚姻终态。
- 原局判别错误与年份错误必须分账：事件类型错回打 L4/切片，时间窗错回打 L5。
- 不得在第一阶段用应期命中反向证明原局 event 门正确。

### 15.4 production rule 决策

- 切片证明后，才允许比较三种独立决策：保持现状、替换 production candidate、或以新 rule ID staged 标记并并行对照。
- 该决策必须引用合成切片证明和独立的新样本验证；不得仅凭历史回放替换。
- 即使后续样本良好，也只形成显式变更提案；不得承诺准确率、GO 或自动切换默认生产入口。

## 16. 规格结论

第一阶段的唯一目标是建立一个局部、可证伪、可机械隔离的杨派婚姻判别器：先按结构家族去重，再执行“夫妻宫事件锚 + 独立配偶结构交互”的具名必要门，输出 `pressure / event / abstain`，且只有 `event` 进入 L3-L6。

这不是报告项目、概率项目、公共 schema 项目或生产规则替换项目。production claim YAML、默认入口、L7 与模板保持不变；合成切片通过后，报告降噪、公共 pressure 契约、应期和规则 staged/替换仍需分别批准。