# PI-220：必要门、竞争、反证、根源、时序与五动作判定接口

> `task_id`: PI-220  
> `parent_task_id`: PI-200  
> 状态：设计产物，待 PI-290 独立汇总与 G2 验收  
> 边界：仅定义纯接口协议；不修改生产代码、默认行为或冻结业务语义

## 1. 目的与结论

本文在 PI-210 规范化证据包之上定义一个只读、可追溯、失败安全的判定交换协议。协议负责表达：

- 必要门逐门证据状态；
- 竞争候选、比较维度和反证引用；
- 根源账本、时序账本及二者之间的约束检查；
- `OUTPUT`、`CONDITIONAL`、`ASK`、`ABSTAIN`、`HUMAN_REVIEW` 五动作 envelope；
- 缺证、冲突、未知和冻结字段状态的精确路径；
- 只描述结构事实的 reason codes；
- 现有运行轨道到本协议的单向、无推断适配边界。

本协议不定义判定算法。它不决定某张卡的门如何解释，不计算分数、权重、排序或优先级，不把声明性 YAML 编译为代码，也不规定候选胜负。任何实际判定组件只能在冻结契约授权范围内填充本协议；协议校验器只校验结构完整性和失败安全条件。

## 2. 规范性事实源与优先级

1. [`engine/contracts/12-real-world-function-evidence-cards-v1.md`](../engine/contracts/12-real-world-function-evidence-cards-v1.md)：F01–F12 正式冻结语义。
2. [`mapping/real-world-function-evidence-cards-v1.yaml`](../mapping/real-world-function-evidence-cards-v1.yaml)：声明性机器镜像，只允许精确读取字段、枚举和值；不得执行其中的自然语言条件。
3. [`plans/production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md)：本协议唯一规范化运行输入模型。
4. [`plans/production-implementation-pi-120-findings-decision-conflict-audit.md`](production-implementation-pi-120-findings-decision-conflict-audit.md)：现有运行轨道及五动作缺口审计。
5. [`plans/production-implementation-control.md`](production-implementation-control.md)：阶段、依赖和治理边界。

冲突时按以上顺序处理。机器附录不得覆盖正式契约；PI-210 中立对象不得被旧轨道的 winner、decision 或 confidence 反向改写。

## 3. 明确非目标

PI-220 不包含以下内容：

- 不设计或实现 G3 生产接线；
- 不设计 G5 测试实现、回归集或验收执行器；
- 不修改 F01–F12 定义、共同纪律或冻结字段；
- 不编写卡片特定 `if/else`；
- 不定义评分、权重、排序、优先级、投票或置信度重算；
- 不从职位、收入、行业、身份或结果字段推断必要门满足；
- 不把 `validation_timepoints` 映射为 `output_precision`；
- 不把 `null`、`unresolved`、`absent`、运行时缺证或 evaluator unknown 合并；
- 不把示例解释为任何具体卡片结论；
- 不自验 G2，也不改变 PI-200、PI-290 或总控状态。

## 4. 设计原则

### 4.1 只读与派生隔离

PI-220 只读取 PI-210 对象。判定结果写入独立的 `DecisionEvaluationResult`，不得回写：

- `NormalizedEvidencePackage`；
- `FunctionCandidate`；
- `EvidenceRecord`；
- `EvidenceRelation`；
- `FrozenCardFieldRef`；
- 原运行轨道的 finding、conflict 或 decision。

### 4.2 分账不可互补

以下账本必须独立保存，不得相互补门或折叠：

- 命理结构轨与现实事实轨；
- 未核验假设轨与现实事实轨；
- 现实必要门与理论链；
- 状态与事件；
- 根源与时序完成；
- 覆盖情况与证据充分性；
- 输出精度与置信度；
- 功能层与结果分类层。

### 4.3 引用优先于复制

判定对象优先持有 PI-210 ID、关系 ID、冻结字段引用和来源定位，不复制自由文本作为事实。展示摘要只能作为非规范性字段，不能参与动作可采纳性校验。

### 4.4 失败安全

- 空列表不等于通过、无冲突或无反证；
- 引用断裂不得被忽略；
- 未知不得被默认成否定或满足；
- 冲突不得以最后写入值覆盖；
- 包级完整性失败时不得产生 `OUTPUT` 或 `CONDITIONAL`；
- 动作 payload 不完整时整个 envelope 无效，不得降级成看似完整的输出。

## 5. 类型约定

以下为语言无关伪类型。`required` 表示字段必须出现，不表示字段值必须非空；允许为空时会明确写为 `null` 或空集合。所有 ID 在同一 `package_id` 范围内必须稳定。

```text
type DecisionAction =
  OUTPUT | CONDITIONAL | ASK | ABSTAIN | HUMAN_REVIEW

type EvidenceTrack =
  CHART_STRUCTURE | REALITY_FACT | UNVERIFIED_HYPOTHESIS

type GateEvidenceState =
  SATISFIED | MISSING | CONFLICT | UNKNOWN

type StructuralReadinessState =
  READY | INCOMPLETE | DISPUTED | BLOCKED

type ConstraintCheckState =
  SATISFIED | VIOLATED | UNKNOWN | NOT_APPLICABLE

type SourceFieldState =
  PRESENT_VALUE |
  EXPLICIT_NULL |
  LISTED_UNRESOLVED |
  BOTH_NULL_AND_UNRESOLVED |
  ABSENT

type FieldEvaluatorState =
  EVALUATED | MISSING | CONFLICT | UNKNOWN | NOT_EVALUATED

type BasisRecordIds = nonempty list<string>

type IssueClass = MISSING | CONFLICT | UNKNOWN

type Severity = INFO | BLOCKING
```

`UNKNOWN` 不是第六个动作。它只表示证据、字段或约束检查尚不可知；最终 envelope 仍必须从五动作中选择且满足对应结构约束。

## 6. 只读输入接口

### 6.1 顶层请求

```text
DecisionEvaluationRequest {
  request_id: string required
  package_id: string required
  case_id: string required
  candidate_ids: list<string> required
  evaluation_scope: EvaluationScope required
  pi210_snapshot_ref: string required
  frozen_contract_ref: ContractVersionRef required
  requested_at: datetime required
}

EvaluationScope {
  function_ids: list<F01..F12> required
  as_of: datetime | null required
  requested_output_context: string | null required
}

ContractVersionRef {
  normative_contract_path: string required
  machine_appendix_path: string required
  contract_version: string required
  content_digest: string required
}
```

`requested_output_context` 只标识调用上下文，不能替代 `output_precision`，也不能触发业务推断。

### 6.2 PI-210 只读端口

```text
interface NormalizedEvidenceReadPort {
  get_package(package_id) -> NormalizedEvidencePackage
  validate_for_pi220(package_id) -> IntegrityState

  get_candidate(candidate_id) -> FunctionCandidate
  list_candidates(case_id, function_ids?) -> list<FunctionCandidate>

  list_evidence(candidate_id, track, kinds?, as_of?)
    -> list<EvidenceRecord>
  list_counterevidence(candidate_id)
    -> list<EvidenceRecord>

  get_card_field_ref(function_id, field_path)
    -> FrozenCardFieldRef
  get_unresolved_states(function_id)
    -> list<UnresolvedFieldState>
  get_validation_plan_binding(function_id)
    -> FrozenDeclarationBinding
  get_output_precision_binding(function_id)
    -> FrozenDeclarationBinding

  list_relations(object_id, relation_types?)
    -> list<EvidenceRelation>
  get_competition_dimensions(candidate_id)
    -> list<CompetitionDimensionRecord>
}
```

端口必须返回不可变快照或等价只读视图。PI-220 不能直接读取原始 YAML 来绕过 `FrozenCardFieldRef`，不能从自由文本重建缺失字段。

### 6.3 冻结契约只读端口

```text
interface FrozenContractReadPort {
  get_field(ref: FrozenCardFieldRef) -> FrozenFieldObservation
  get_constraint_ref(function_id, constraint_path)
    -> FrozenConstraintRef
  verify_contract_version(ref: ContractVersionRef)
    -> ContractIntegrityResult
}

FrozenFieldObservation {
  ref: FrozenCardFieldRef required
  source_state: SourceFieldState required
  value: any | null required
  unresolved_state_ref: string | null required
  source_location: string required
}
```

该端口只能执行精确寻址、类型保持读取、版本核对和摘要校验。它不得解释 `priority_rule`、`conflict_priority`、`root_guards` 或自然语言门条件。

`source_state` 逐值复用 PI-210 `SourceFieldState`，只陈述来源字段事实；该端口不得生成 evaluator 状态。

## 7. 包级消费前置检查

```text
PackageConsumptionCheck {
  package_id: string required
  pi210_integrity: IntegrityState required
  contract_integrity: ContractIntegrityResult required
  candidate_reference_integrity: VALID | INVALID required
  evidence_reference_integrity: VALID | INVALID required
  relation_reference_integrity: VALID | INVALID required
  consumable: boolean required
  blocking_issue_ids: list<string> required
}
```

`consumable=true` 必须同时满足：

- PI-210 `pi220_consumable=true`；
- 引用完整；
- 卡绑定未失败；
- 三轨未污染；
- 冻结契约版本和摘要可核对。

这里的 `consumable` 仅表示可进入 PI-220 接口处理，不表示任何门满足、候选成立或允许正式输出。

## 8. 必要门协议

### 8.1 门组、声明成员与逐门记录

```text
GateEvaluationSet {
  candidate_id: string required
  function_id: F01..F12 required
  gate_definition_refs: nonempty list<FrozenCardFieldRef> required
  member_declaration_set: GateMemberDeclarationSet required
  records: nonempty list<GateEvaluationRecord> required
  set_state: StructuralReadinessState required
  issue_ids: list<string> required
}

GateMemberDeclarationSet {
  declaration_set_id: string required
  declaration_source_id: string required
  declaration_schema_version: string required
  declaration_version: string required
  content_digest: DigestRef required
  members: nonempty list<GateDeclaredMember> required
}

GateDeclaredMember {
  declared_member_id: string required
  declared_member_value: opaque-json non-null required
  gate_definition_ref: FrozenCardFieldRef required
}

GateEvaluationRecord {
  gate_record_id: string required
  candidate_id: string required
  gate_definition_ref: FrozenCardFieldRef required
  declared_member_id: string required
  evaluation_binding_ref: GateEvaluationBindingRef required
  state: GateEvidenceState required

  supporting_evidence_ids: list<string> required
  counterevidence_ids: list<string> required
  conflict_relation_ids: list<string> required

  missing_paths: list<FieldPathIssueRef> required
  conflict_paths: list<FieldPathIssueRef> required
  unknown_paths: list<FieldPathIssueRef> required

  reason_codes: list<ReasonCode> required
  source_decision_ref: string | null required
}

GateEvaluationBindingRef {
  binding_id: string required
  binding_schema_version: string required
  binding_version: string required
  canonical_record_digest: DigestRef required
  immutable_source_digest: DigestRef required
}
```

`GateMemberDeclarationSet` 是通用 G2 声明对象，不是卡片算法。其不可变来源必须能按 `declaration_source_id + declaration_schema_version + declaration_version + content_digest` 精确解析；规范序列化内容必须包含全部 `members`，且每个成员显式保存非 null `declared_member_value` 及其真实 `gate_definition_ref`。`declared_member_id` 只在该声明集版本内充当稳定身份，不得由 `gate_record_id` 字符串、数组位置、证据内容、issue path 或自然语言运行时解析派生。

`GateEvaluationBindingRef` 必须解析到获授权判定来源中的不可变绑定对象。该对象的规范 payload 必须逐值包含当前记录的 `candidate_id`、`gate_definition_ref`、`declared_member_id`、`state`、全部 evidence／relation／path 引用、`reason_codes` 与 `source_decision_ref`；`canonical_record_digest` 对上述 payload 作规范摘要，`immutable_source_digest` 证明所解析来源对象。摘要不是自认证字段：来源不存在、不可变性不可证、版本或任一摘要不匹配时必须 fail closed。这样交换两条记录的状态或证据而不同时交换其显式成员身份与获授权来源绑定，不能产生另一个结构有效对象。

### 8.2 状态结构语义

| 状态 | 结构含义 | 最低引用要求 | 禁止解释 |
|---|---|---|---|
| `SATISFIED` | 获授权判定组件已给出门满足结果 | 非空现实事实证据引用；门定义引用；`source_decision_ref` | 证据数量多即满足；理论结构替代现实事实 |
| `MISSING` | 满足该门所需的已声明输入没有可用证据 | 至少一个 `missing_paths` 或明确的缺证 issue | 缺证即反证；空列表即满足 |
| `CONFLICT` | 同一门存在不可静默合并的支持与反证/相斥事实 | 支持与反证引用，或冲突关系引用；至少一个 `conflict_paths` | 后写覆盖前写；按数量裁决 |
| `UNKNOWN` | 字段可读取但语义状态未决，或 evaluator 无法形成门状态 | 至少一个 `unknown_paths` 或未知 issue | unknown 等于 missing、false 或 unresolved |

协议校验器不负责从证据生成上述状态；它只检查状态与引用是否结构一致。`SATISFIED` 只能引用 `REALITY_FACT` 作为现实门支持证据。`CHART_STRUCTURE` 和 `UNVERIFIED_HYPOTHESIS` 可被保留为关联上下文，但不能出现在 `supporting_evidence_ids` 中冒充现实门满足证据。

### 8.3 门集合基数、身份与聚合限制

对每个 `GateEvaluationSet`，校验器必须同时执行以下机械不变量：

1. `gate_definition_refs` 按 `card_id + contract_id + contract_version + field_path + declared_state + declared_value + source_locator_id` 的规范值去重；重复项无效。该列表必须与 `member_declaration_set.members[*].gate_definition_ref` 的规范去重集合、以及 `records[*].gate_definition_ref` 的规范去重集合三者完全相等。多个成员和记录可以共享同一个真实、可解析的整体冻结字段引用；共享不产生虚构子路径。
2. `declaration_set_id` 在消费范围内恰一解析；声明来源、schema version、declaration version 与 `content_digest` 必须全部匹配。声明成员的 `declared_member_id` 与 `declared_member_value` 均非空，且 `declared_member_id` 在该声明集版本内唯一；同值重复成员也无效。
3. 每条记录的 `candidate_id` 必须等于所属 set；`gate_record_id` 在当前 `DecisionEvaluationResult` 内唯一；`declared_member_id` 必须在当前声明集中恰一命中，且记录的 `gate_definition_ref` 必须与命中成员逐值相同。
4. `records` 与 `members` 构成全双射：每个声明成员恰有一条记录，每条记录恰属一个成员，因此 `|records| = |members|`。重复成员记录、遗漏成员记录、未知成员、跨声明集回退或按数组位置补配均无效。
5. 每条 `evaluation_binding_ref` 必须唯一解析并通过版本、`canonical_record_digest` 与 `immutable_source_digest` 校验。绑定 payload 中的显式成员身份和记录 payload 必须与当前记录逐值一致；不得从 ID 字符串、位置、证据、issue path 或自然语言重建身份。
6. 同一 `declared_member_id` 在同一声明版本中只能绑定一个规范 `gate_definition_ref`；同一记录声明的 ref、成员声明的 ref 与去重定义 ref 不一致时，集合必须 `BLOCKED`。

`set_state` 只表达结构可用性，不是业务聚合判定：

- 任一声明／版本／摘要／绑定失败、重复、遗漏、未知成员、共享 ref 不一致或引用断裂：`BLOCKED`；
- 记录尚未齐全但没有伪造完整性的情况：`INCOMPLETE`；
- 存在未裁决冲突：`DISPUTED`；
- 所有声明成员均有身份、绑定和引用结构完整的逐成员记录：`READY`。

`READY` 不等于“所有门满足”。协议禁止通过门数量、满足比例或任意排序生成候选优先级。

### 8.4 置换 falsifier

设计级验收至少包含以下 fail-closed falsifier；它们检查通用身份绑定，不执行任何卡片业务语义：

| 变异 | 必须结果 | 禁止恢复方式 |
|---|---|---|
| 交换两条记录的 `state`、证据、关系、路径或 reason code，但保留各自 `declared_member_id` 与原 `evaluation_binding_ref` | `canonical_record_digest`／不可变来源 payload 不匹配，集合 `BLOCKED` | 不得按记录位置、证据内容或自然语言猜回 |
| 仅交换两条记录的 `declared_member_id` | 声明成员 ref 或 binding payload 不一致，集合 `BLOCKED` | 不得解析 `gate_record_id` 推断成员 |
| 将 `declared_member_id` 改为声明集中不存在的值 | 未知成员，集合 `BLOCKED` | 不得创建临时成员或回退其他声明版本 |
| 复制一个合法成员身份覆盖另一成员 | 重复且完整覆盖失败，集合 `BLOCKED` | 不得 last-write-wins 或按数组去重 |
| 改写成员声明值、成员 ref、声明版本或任一摘要 | 声明来源完整性失败，集合 `BLOCKED` | 不得接受本地重摘要作为原来源证明 |
| 多条记录共享真实整体 ref，仅对记录顺序作任意置换，同时保持每条记录身份与绑定整体不变 | 结构结果不变 | 不得让数组位置参与身份或结果 |

因此，可观察映射由 `record → declared_member_id → versioned declaration member → real FrozenCardFieldRef` 唯一确定；对 `n` 个共享 ref 成员不存在 `n!` 个不可辨识置换。伪造身份、只移动状态／证据或破坏声明绑定都会失败；完整移动一条记录及其真实身份和获授权绑定只改变序列位置，不改变语义映射。

### 8.5 最低充分参与角色集合

冻结契约的共同最低充分参与集合与每卡声明的 `source_gate` 通过以下通用角色协议闭合。它只要求角色逐项存在、状态可追溯并约束动作可采纳性，不解释任一卡如何从证据得到状态。

```text
type ParticipationRole =
  SINGLE_SCHOOL_COMPLETE_NATAL_CHAIN |
  DAIYUN_STAGE_EFFECT |
  LIUNIAN_SPECIFIC_EVENT_TRIGGER |
  REAL_WORLD_FUNCTION_GATE |
  BREAK_CONDITION_OR_VALID_FALSIFIER |
  SOURCE_GATE

type ParticipationState =
  SATISFIED | MISSING | CONFLICT | UNKNOWN | NOT_APPLICABLE

MinimumSufficientParticipationSet {
  participation_set_id: string required
  candidate_id: string required
  function_id: F01..F12 required
  required_roles: nonempty list<ParticipationRole> required
  role_records: nonempty list<ParticipationRoleRecord> required
  structural_state: StructuralReadinessState required
  issue_ids: list<string> required
}

ParticipationRoleRecord {
  participation_record_id: string required
  participation_set_id: string required
  role: ParticipationRole required
  frozen_definition_refs: nonempty list<FrozenCardFieldRef> required
  state: ParticipationState required
  supporting_evidence_ids: list<string> required
  counterevidence_ids: list<string> required
  missing_issue_ids: list<string> required
  conflict_issue_ids: list<string> required
  unknown_issue_ids: list<string> required
  relation_ids: list<string> required
  source_decision_ref: string | null required
}
```

规范约束：

1. `required_roles` 必须逐值来自冻结共同最低充分参与集合，并另含每卡统一字段 `source_gate`；不得由实现者删减、改名或加入新业务角色。具体事件不适用流年触发时，获授权组件可记录 `NOT_APPLICABLE`，但必须有冻结定义引用与可追溯判定引用，协议不自行判断何时不适用。
2. 每个 required role 恰有一个独立 `ParticipationRoleRecord`；禁止用单一聚合状态、门数量、材料数量或其他角色的证据补齐。
3. `SATISFIED` 必须有非空 `supporting_evidence_ids` 和可解析 `source_decision_ref`；`MISSING` 必须有非空 `missing_issue_ids`；`CONFLICT` 必须同时保留冲突两侧证据或关系及非空 `conflict_issue_ids`；`UNKNOWN` 必须有非空 `unknown_issue_ids`；`NOT_APPLICABLE` 必须有可解析 `source_decision_ref`。
4. 现实硬门的满足证据仍只能来自 `REALITY_FACT`；原局完整链、大运阶段、流年触发、破坏／反证与 source gate 按各自冻结引用和 PI-210 分轨证据保存，不得互相改轨或互补。
5. `structural_state=READY` 只表示所有 required role 均有结构完整记录，不表示它们业务上满足。协议校验器不得执行 `theory_origin_gate`、`source_gate`、`timing_completion`、`contradiction_guards` 或自然语言条件。
6. `OUTPUT` 可采纳性必须逐项检查本集合；缺少角色记录，或任一 required role 为 `MISSING`、`CONFLICT`、`UNKNOWN`，均使 envelope `INVALID`。`NOT_APPLICABLE` 仅在上述可追溯条件成立时不阻断。其他动作按第 13 节失败安全约束保留问题和依据，不规定动作选择优先级。

## 9. 竞争候选与反证协议

### 9.1 竞争集合

```text
CompetitionSet {
  competition_id: string required
  candidate_ids: list<string> required
  relation_ids: list<string> required
  dimension_records: list<CompetitionDimensionEvaluation> required
  counterevidence_records: list<CounterevidenceReference> required
  candidate_dispositions: list<CandidateDisposition> required
  structural_state: StructuralReadinessState required
  issue_ids: list<string> required
}

CompetitionDimensionEvaluation {
  dimension:
    primary_responsibility |
    primary_action |
    direct_object |
    primary_deliverable |
    primary_uncertainty |
    stable_input |
    strongest_competing_explanation
  candidate_evidence: map<candidate_id, list<evidence_id>> required
  candidate_counterevidence: map<candidate_id, list<evidence_id>> required
  comparison_relation_ids: list<string> required
  state: UNOBSERVED | PARTIAL | READY_FOR_DECISION | DISPUTED required
  missing_paths: list<FieldPathIssueRef> required
  conflict_paths: list<FieldPathIssueRef> required
  unknown_paths: list<FieldPathIssueRef> required
}
```

### 9.2 反证引用

```text
CounterevidenceReference {
  reference_id: string required
  candidate_id: string required
  evidence_id: string required
  relation_ids: list<string> required
  affected_gate_record_ids: list<string> required
  affected_dimension_records: list<string> required
  source_track: EvidenceTrack required
  source_locator: string required
}
```

反证必须是显式证据引用，不能只写自由文本摘要。一个反证可同时影响门和竞争维度，但必须分别列出受影响记录。反证存在本身不自动排除候选；其业务影响由冻结语义授权的判定组件提供，协议不推断。

### 9.3 候选处置

```text
CandidateDisposition {
  candidate_id: string required
  disposition: INCLUDED | CONDITIONAL | EXCLUDED | UNRESOLVED required
  source_decision_ref: string required
  supporting_record_ids: list<string> required
  limiting_record_ids: list<string> required
  reason_codes: list<ReasonCode> required
}
```

处置记录用于承载外部授权判定结果，不等于排名：

- 允许多个 `INCLUDED`，不强制唯一 winner；
- 不提供 score、rank、weight、vote 或 priority 字段；
- `EXCLUDED` 必须有可定位的限制记录，不能仅凭旧轨道 winner 反推；
- `UNRESOLVED` 必须保留缺证、冲突或未知路径；
- `source_decision_ref` 必须指向可追溯的判定记录，不能指向自由文本结论。

## 10. 根源与时序分账协议

### 10.1 根源账本

```text
RootConstraintLedger {
  candidate_id: string required
  root_entries: list<RootLedgerEntry> required
  issue_ids: list<string> required
}

RootLedgerEntry {
  root_evidence_id: string required
  vocabulary_scope: COMMON | CARD_SPECIFIC required
  label: STRONG_ROOT | WEAK_ROOT | NO_ROOT | string required
  card_id: F01..F12 | null required
  object_refs: list<string> required
  rationale_source_refs: list<string> required
  source_track: CHART_STRUCTURE required
}
```

根源账本只接受 PI-210 根源证据引用。现实反馈、候选数量、流派数量、职位或收入不得写入该账本以升级根源。

### 10.2 时序账本

```text
TimingConstraintLedger {
  candidate_id: string required
  timing_entries: list<TimingLedgerEntry> required
  issue_ids: list<string> required
}

TimingLedgerEntry {
  timing_evidence_id: string required
  completion_mode:
    ACTIVATE_EXISTING |
    COMPLETE_LATENT |
    REPAIR_DEFECT |
    TEMPORARY_SUBSTITUTE |
    INVALID_COMPLETION
  target_root_evidence_id: string | null required
  timing_object_refs: list<string> required
  source_track: CHART_STRUCTURE required
}
```

时序账本不得写入或改写根源标签。`validation_timepoints` 只能作为后续验证计划引用，不能填充 completion mode，也不能被转换为输出精度。

### 10.3 根源—时序约束检查

```text
RootTimingConstraintSet {
  candidate_id: string required
  checks: list<RootTimingConstraintCheck> required
  structural_state: StructuralReadinessState required
  issue_ids: list<string> required
}

RootTimingConstraintCheck {
  check_id: string required
  constraint_ref: FrozenConstraintRef required
  root_entry_ids: list<string> required
  timing_entry_ids: list<string> required
  state: ConstraintCheckState required
  source_decision_ref: string | null required
  missing_paths: list<FieldPathIssueRef> required
  conflict_paths: list<FieldPathIssueRef> required
  unknown_paths: list<FieldPathIssueRef> required
  reason_codes: list<ReasonCode> required
}
```

`constraint_ref` 必须定位到冻结契约中的约束。PI-220 不把约束文本编译为表达式，不定义卡片条件。获授权组件提供检查状态，接口校验器仅验证：

- 引用存在；
- 根源和时序条目未混账；
- `VIOLATED`、`UNKNOWN` 有对应问题路径或理由；
- 约束结果没有反向改写原证据。

## 11. 缺证、冲突与未知字段路径

### 11.1 统一问题对象

```text
FieldPathIssue {
  issue_id: string required
  issue_class: MISSING | CONFLICT | UNKNOWN required
  severity: INFO | BLOCKING required

  owner_type:
    PACKAGE | CANDIDATE | GATE | COMPETITION_DIMENSION |
    ROOT_ENTRY | TIMING_ENTRY | ROOT_TIMING_CHECK | ACTION
  owner_id: string required

  source_object_type: string required
  source_object_id: string required
  path_dialect: JSON_POINTER required
  field_path: string required
  source_state: SourceFieldState required
  evaluator_state: FieldEvaluatorState required

  evidence_ids: list<string> required
  relation_ids: list<string> required
  frozen_field_refs: list<FrozenCardFieldRef> required
  reason_codes: list<ReasonCode> required
}

type FieldPathIssueRef = string
```

### 11.2 来源字段状态与 evaluator 状态禁止折叠矩阵

`source_state` 原样承接 PI-210 `SourceFieldState`；`evaluator_state` 是判定组件对当前任务能否判定的独立状态。二者必须同时记录，禁止把来源状态直接改写成 evaluator 状态或反向覆盖来源。

| 来源 `source_state` | 允许的 `evaluator_state` | 必须保留 | 禁止折叠／默认转换 |
|---|---|---|---|
| `PRESENT_VALUE` | `EVALUATED`、`CONFLICT`、`UNKNOWN`、`NOT_EVALUATED` | 原值、来源与 evaluator 理由／冲突引用 | 有值即 `EVALUATED`；无法解释即 `ABSENT` 或 `MISSING` |
| `EXPLICIT_NULL` | `EVALUATED`、`MISSING`、`UNKNOWN`、`NOT_EVALUATED` | 显式 null 及独立 evaluator 理由 | `ABSENT`、空字符串、false、0、默认枚举 |
| `LISTED_UNRESOLVED` | `UNKNOWN`、`NOT_EVALUATED`；仅有独立额外证据时可 `EVALUATED` 或 `CONFLICT` | unresolved 声明与额外证据引用 | 自动 `MISSING`、`ABSENT`、否定值或默认值 |
| `BOTH_NULL_AND_UNRESOLVED` | `UNKNOWN`、`NOT_EVALUATED`；仅有独立额外证据时可 `EVALUATED` 或 `CONFLICT` | null 与 unresolved 两个来源事实及额外证据引用 | 压成单独 null、单独 unresolved、`MISSING` 或默认值 |
| `ABSENT` | `MISSING`、`NOT_EVALUATED`；仅有独立外部证据时可 `EVALUATED`、`CONFLICT` 或 `UNKNOWN` | 缺字段事实与外部证据来源 | `EXPLICIT_NULL`、默认枚举或伪造来源值 |

附加禁止矩阵：

| evaluator 情况 | 必须使用 | 禁止回写来源状态 |
|---|---|---|
| 无法解释已提供值 | `UNKNOWN` + unknown issue／理由 | 不得改为 `ABSENT`、`LISTED_UNRESOLVED` 或 `EXPLICIT_NULL` |
| 多来源值不可合并 | `CONFLICT` + 冲突两侧证据／关系 | 不得创造 `CONFLICTING_VALUES` 来源状态、任选一值或最后写入值 |
| 当前任务未执行判定 | `NOT_EVALUATED` | 不得冒充来源 unresolved 或 evaluator unknown |
| 必需输入不可获得 | `MISSING` + missing issue | 不得把来源 null／unresolved／absent 三者彼此改写 |

`issue_class`、`source_state` 与 `evaluator_state` 三者分开：例如 `ABSENT` 可支撑 evaluator `MISSING`，但二者不是同一概念；`LISTED_UNRESOLVED` 通常形成 evaluator `UNKNOWN`，不得自动当作缺字段。任何不在矩阵中的组合均 fail closed，产生 blocking issue，不得用于 `OUTPUT`。

所有问题必须定位到 JSON Pointer 路径。只写“证据不足”“有冲突”而没有 owner、source object 和 field path 的记录不合格。

## 12. 五动作 envelope

### 12.1 顶层结果

```text
DecisionEvaluationResult {
  result_id: string required
  request_id: string required
  package_id: string required
  contract_ref: ContractVersionRef required

  consumption_check: PackageConsumptionCheck required
  gate_sets: list<GateEvaluationSet> required
  participation_sets: list<MinimumSufficientParticipationSet> required
  competition_sets: list<CompetitionSet> required
  root_ledgers: list<RootConstraintLedger> required
  timing_ledgers: list<TimingConstraintLedger> required
  root_timing_checks: list<RootTimingConstraintSet> required
  issues: list<FieldPathIssue> required

  action_envelope: DecisionActionEnvelope required
  produced_at: datetime required
}
```

### 12.2 动作 envelope

```text
DecisionActionEnvelope {
  action_id: string required
  selected_action: DecisionAction required
  subject_candidate_ids: list<string> required

  payload:
    OutputPayload |
    ConditionalPayload |
    AskPayload |
    AbstainPayload |
    HumanReviewPayload

  basis_record_ids: BasisRecordIds required
  blocking_issue_ids: list<string> required
  nonblocking_issue_ids: list<string> required
  reason_codes: list<ReasonCode> required
  source_decision_refs: list<string> required

  output_precision_binding: FrozenDeclarationBinding required
  validation_plan_binding: FrozenDeclarationBinding required

  structural_validity: VALID | INVALID required
  validation_errors: list<string> required
}
```

`payload` 必须与 `selected_action` 一一对应。`output_precision_binding` 与 `validation_plan_binding` 逐值复用 PI-210 唯一 `FrozenDeclarationBinding`，并按 `FrozenDeclarationRef.declaration_type` 分账；二者不得内嵌可变声明副本、使用裸字符串或裸 `null`、互相派生或互为默认值。

机械约束如下：

1. `RESOLVED` 必须携带完整非 null `ref`，并解析到 `declaration_id`、`declaration_type`、`card_id`、`contract_version`、`declaration_schema_version` 与 `content_digest` 均一致的 PI-210 不可变声明。
2. output precision 冻结声明存在时必须为 `RESOLVED`；其声明值即使为 explicit null，也只能由该非 null 引用解析到 `OutputPrecisionRef.declared_precision=null`，不得将 binding 改为其他分支。
3. validation plan 只按自身上游存在性选择分支：确无声明为 `ABSENT`，明确不适用为 `NOT_APPLICABLE`；不得由 output precision 状态推导。
4. `UNAVAILABLE` 表达未读取／来源不可用，`UNRESOLVABLE` 表达引用身份、版本、schema、摘要或链路解析失败；二者必须保留 PI-210 issue，且令 envelope `structural_validity=INVALID`，禁止 `OUTPUT`／`CONDITIONAL` 发布、有效反馈绑定与学习。
5. `ABSENT`、`NOT_APPLICABLE`、`UNAVAILABLE`、`UNRESOLVABLE` 均不得被消费者解释为声明值 null；不符合判别联合字段约束的 envelope 必须拒绝。

### 12.3 动作 payload

```text
OutputPayload {
  included_candidate_ids: list<string> required
  disposition_refs: list<string> required
  scope_refs: list<string> required
}

ConditionalPayload {
  included_candidate_ids: list<string> required
  disposition_refs: list<string> required
  condition_refs: list<string> required
  unresolved_issue_ids: list<string> required
  scope_refs: list<string> required
}

AskPayload {
  question_requests: list<QuestionRequest> required
  unresolved_issue_ids: list<string> required
  resume_token: string required
}

QuestionRequest {
  question_id: string required
  target_issue_ids: list<string> required
  requested_field_paths: list<string> required
  expected_answer_shape: string required
}

AbstainPayload {
  abstained_candidate_ids: list<string> required
  blocking_issue_ids: list<string> required
  abstention_scope: string required
}

HumanReviewPayload {
  review_case_id: string required
  review_issue_ids: list<string> required
  review_record_ids: list<string> required
  requested_review_scope: string required
}
```

payload 只携带结构引用，不携带具体卡片结论文本。自然语言渲染属于后续消费者，不属于 PI-220。

## 13. 动作失败安全结构约束

本节定义动作的**可采纳性约束**，不定义动作选择算法、动作优先级或业务决策规则。生产者可以在冻结语义允许范围内选择动作，但违反下列约束的 envelope 必须标记为 `INVALID`，且不得进入正式输出消费者。

| 动作 | 必须具备 | 结构性禁止条件 |
|---|---|---|
| `OUTPUT` | 包可消费；非空 subject；每个 subject 有可追溯处置；必要门记录完整且被授权结果标记满足；最低充分参与集合逐角色闭合；竞争、反证和根源—时序约束无 blocking issue；非空 basis | 包不可消费；门或 required role 为 `MISSING/CONFLICT/UNKNOWN`；required role 记录缺失；存在 blocking issue；引用断裂；仅有旧轨道 winner/decision |
| `CONDITIONAL` | 非空 basis；包可消费；非空 subject；非空 `condition_refs`；每个条件可定位；未决项列入 `unresolved_issue_ids`；条件范围不超出已授权处置 | 用条件文本掩盖 blocking integrity failure；缺少条件引用；把 unknown 静默转成肯定输出 |
| `ASK` | 非空 basis；非空问题；每个问题绑定一个或多个 `MISSING/UNKNOWN` issue；请求字段路径明确；有 resume token | 问题不对应 issue；要求回答者提供系统内部推断；以 ASK 绕过包完整性错误却不保留错误 |
| `ABSTAIN` | 非空 basis；非空阻断问题；弃权对象和范围明确 | 空理由弃权；把局部轨道 abstain 状态直接复制成统一动作；同时携带正式输出 payload |
| `HUMAN_REVIEW` | 非空 basis；非空 review issue 与 record 引用；复核范围明确；保留冲突两侧或不可映射输入 | 只给摘要不保留原引用；以人审状态覆盖冲突；同时携带正式输出 payload |

五种动作的 `basis_record_ids` 均使用同一 `BasisRecordIds` 非空类型；basis 可引用本 result 内的 gate、participation role、competition、disposition、root／timing check 或 issue 记录，但不得使用自由文本充数。此基数约束不规定动作优先级或业务结论。

附加不变量：

1. 一个 envelope 恰有一个 `selected_action` 和一个匹配 payload。
2. `OUTPUT` 与 `CONDITIONAL` 不能在 `consumable=false` 时有效。
3. blocking 的引用完整性、卡绑定或跨轨污染问题不能被降为 nonblocking。
4. `ASK` 不是普通报告问题列表的别名；必须有 issue 到字段路径的闭环。
5. `ABSTAIN` 不是“无结果”的空对象；必须保存阻断依据。
6. `HUMAN_REVIEW` 不是任意不确定性的默认标签；必须保存待复核记录和范围。
7. 协议不规定 `ASK`、`ABSTAIN`、`HUMAN_REVIEW` 之间的优先级。
8. 协议不规定多个候选必须唯一胜出。

## 14. 结构性 reason codes

### 14.1 格式

```text
ReasonCode = <NAMESPACE>.<STRUCTURAL_FACT>
```

允许命名空间：

- `INTEGRITY`
- `FIELD`
- `GATE`
- `COMPETITION`
- `COUNTEREVIDENCE`
- `ROOT`
- `TIMING`
- `ACTION`
- `ADAPTER`

reason code 只能描述可机械核对的结构事实。它不能表达“某功能成立”“某候选更强”“某事件必发”等业务语义，也不能成为隐藏规则引擎。

### 14.2 最小目录

| Code | 结构含义 |
|---|---|
| `INTEGRITY.PACKAGE_NOT_CONSUMABLE` | PI-210 包不可供 PI-220 消费 |
| `INTEGRITY.REFERENCE_BROKEN` | 对象、证据或关系引用断裂 |
| `INTEGRITY.TRACK_CONTAMINATION` | 证据轨隔离完整性失败 |
| `INTEGRITY.CARD_BINDING_INVALID` | 卡绑定完整性失败 |
| `INTEGRITY.CONTRACT_VERSION_MISMATCH` | 冻结契约版本或摘要不匹配 |
| `FIELD.ABSENT` | 指定路径不存在 |
| `FIELD.EXPLICIT_NULL_PRESERVED` | 显式 null 已保真 |
| `FIELD.UNRESOLVED_PRESERVED` | unresolved 状态已保真 |
| `FIELD.NULL_AND_UNRESOLVED_PRESERVED` | null 与 unresolved 并存状态已保真 |
| `FIELD.EVALUATOR_UNKNOWN` | evaluator 无法解释已提供字段 |
| `FIELD.CONFLICTING_VALUES` | 多来源值不可无损合并 |
| `GATE.RECORD_MISSING` | 声明门缺少逐门记录 |
| `GATE.MEMBER_DECLARATION_INVALID` | 成员声明来源、版本、摘要或显式值无效 |
| `GATE.MEMBER_CARDINALITY_INVALID` | 成员与记录非全双射、重复、遗漏或出现未知成员 |
| `GATE.MEMBER_BINDING_MISMATCH` | 记录、成员、冻结 ref 或不可变 evaluation binding 不一致 |
| `GATE.PERMUTATION_BINDING_INVALID` | 状态／证据与显式成员身份的置换破坏绑定 |
| `GATE.EVIDENCE_MISSING` | 门记录定位到缺证路径 |
| `GATE.EVIDENCE_CONFLICT` | 门记录定位到冲突引用 |
| `GATE.STATE_UNKNOWN` | 门状态未知且有路径 |
| `GATE.REALITY_FACT_REFERENCE_REQUIRED` | 满足状态缺少现实事实轨引用 |
| `COMPETITION.DIMENSION_UNOBSERVED` | 竞争维度无观测引用 |
| `COMPETITION.DIMENSION_PARTIAL` | 竞争维度引用不完整 |
| `COMPETITION.DIMENSION_DISPUTED` | 竞争维度存在未裁决冲突 |
| `COMPETITION.DISPOSITION_UNRESOLVED` | 候选处置未决 |
| `COUNTEREVIDENCE.REFERENCE_PRESENT` | 反证引用存在 |
| `COUNTEREVIDENCE.RELATION_MISSING` | 反证缺少关系定位 |
| `ROOT.ENTRY_MISSING` | 需要引用的根源条目缺失 |
| `ROOT.SOURCE_TRACK_INVALID` | 根源条目来源轨不合规 |
| `TIMING.ENTRY_MISSING` | 需要引用的时序条目缺失 |
| `TIMING.ROOT_REFERENCE_BROKEN` | 时序到根源引用断裂 |
| `TIMING.CONSTRAINT_UNKNOWN` | 根源—时序约束检查未知 |
| `TIMING.CONSTRAINT_VIOLATED` | 获授权组件报告约束违反 |
| `ACTION.PAYLOAD_TYPE_MISMATCH` | 动作与 payload 类型不匹配 |
| `ACTION.BASIS_MISSING` | 动作缺少依据记录 |
| `ACTION.BLOCKING_ISSUE_PRESENT` | 正式输出动作仍有阻断问题 |
| `ACTION.QUESTION_NOT_BOUND_TO_ISSUE` | ASK 问题未绑定问题记录 |
| `ACTION.REVIEW_SCOPE_MISSING` | 人审范围缺失 |
| `ADAPTER.SOURCE_SEMANTICS_UNMAPPABLE` | 来源字段无法无损映射 |
| `ADAPTER.LEGACY_DECISION_NOT_REUSED` | 旧 decision 被保留但未当作 PI-220 结论 |
| `ADAPTER.CONFIDENCE_NOT_RECOMPUTED` | 适配器未重算统一置信度 |

扩展 reason code 必须满足：

- 能由字段、引用、枚举或完整性检查直接证明；
- 不引入新的卡片条件；
- 不隐含评分、排序或优先级；
- 不替代冻结契约引用；
- 在注册表中有唯一说明和稳定版本。

## 15. 现有运行轨道适配边界

### 15.1 通用适配器协议

```text
interface DecisionTrackAdapter {
  describe_source() -> SourceTrackDescriptor
  adapt_read_only(source_snapshot_ref)
    -> AdapterResult<NormalizedEvidencePackageReference>
}

AdapterResult<T> {
  value: T | null required
  transformations: list<TransformationRecord> required
  unmappable_fields: list<FieldPathIssue> required
  preserved_source_refs: list<string> required
  integrity: VALID | INVALID required
}
```

允许的适配操作：

- 字段复制；
- 精确枚举映射；
- 类型保持解析；
- 容器包装；
- 稳定 ID 和来源引用建立；
- 有损转换的显式记录。

禁止的适配操作：

- 业务推断；
- 评分、排序、投票或 winner 推导；
- 统一置信度重算；
- 以旧 decision 填充 PI-220 disposition；
- 以旧 abstain 填充 PI-220 `ABSTAIN`；
- 以普通 question 填充 PI-220 `ASK`；
- 以 human-review 标志直接填充 `HUMAN_REVIEW`；
- 执行 F01–F12 YAML 自然语言字段。

### 15.2 轨道矩阵

| 来源轨道 | 可读取资产 | 必须隔离或保留 | 不得声称 |
|---|---|---|---|
| `PRODUCTION_DEFAULT` | findings、`FinalConclusion`、`CrossSchoolConflict` 等来源快照 | 旧结论和冲突作为 legacy source ref；证据轨需经 PI-210 归一化 | 旧 conclusion 等于 PI-220 `OUTPUT`；旧 winner 等于唯一候选 |
| `PARALLEL_DOMAIN` | parallel findings、yes/no、局部 abstain、并存结果 | domain scope、局部 abstain 语义、来源 confidence | parallel abstain 等于统一 `ABSTAIN`；yes/no 等于门状态 |
| `STAGED_L6` | staged findings、`StageDecision`、arbitration 记录 | stage、规则版本、局部 decision 语义 | staged YAML 消费方式可迁移为 F01–F12 执行器 |
| `V5_V6_PREPROD` | opt-in findings、`DecisionRun`、`ArbitrationDecision`、`ReportViewItem` | preprod scope、run id、未提升状态 | preprod decision 改变 production-default；report item 等于正式动作 |
| `MANUAL_IMPORT` | 人工结构化证据与来源定位 | provenance、人工标注状态、未核验项 | 人工摘要等于现实事实；未核验假设可直接满足门 |

### 15.3 消费者边界

现有报告、pipeline 和 preprod 消费者在 G3 接线前均不被视为五动作消费者。PI-220 文档只定义未来消费者必须检查的 envelope，不改变任何当前默认行为。

尤其：

- `OUTPUT` 不能自动路由到当前报告渲染；
- `ASK` 没有现成统一 dispatcher；
- `ABSTAIN` 与 parallel-domain 局部 abstain 不是同一协议；
- `HUMAN_REVIEW` 需要独立 review scope 和记录闭环；
- `CONDITIONAL` 不能由 mixed、downgraded 或 scope-limit 字段直接替代。

## 16. 纯结构示例

以下示例使用占位 ID，仅展示 `consumption_check`、一个 gate set 与 `ASK` envelope 的局部结构，不是完整 `DecisionEvaluationResult`；因此省略 `contract_ref`、`participation_sets`、`competition_sets`、root／timing ledgers 与顶层 issues。示例不对应 F01–F12 中任何具体卡片，也不产生业务结论。

```yaml
result_id: DER-EXAMPLE
request_id: REQ-EXAMPLE
package_id: PKG-EXAMPLE
consumption_check:
  consumable: true
  blocking_issue_ids: []

gate_sets:
  - candidate_id: CANDIDATE-A
    function_id: FXX
    gate_definition_refs:
      - CARD-FIELD-1
    member_declaration_set:
      declaration_set_id: GATE-MEMBERS-EXAMPLE
      declaration_source_id: DECLARATION-SOURCE-EXAMPLE
      declaration_schema_version: GATE-MEMBER-DECLARATION-V1
      declaration_version: V1
      content_digest:
        algorithm: SHA-256
        canonicalization: GATE-MEMBER-DECLARATION-C14N-V1
        value: DIGEST-MEMBER-DECLARATION-EXAMPLE
      members:
        - declared_member_id: MEMBER-EXAMPLE
          declared_member_value: example-declared-member
          gate_definition_ref: CARD-FIELD-1
    records:
      - gate_record_id: GATE-1
        candidate_id: CANDIDATE-A
        gate_definition_ref: CARD-FIELD-1
        declared_member_id: MEMBER-EXAMPLE
        evaluation_binding_ref:
          binding_id: GATE-BINDING-EXAMPLE
          binding_schema_version: GATE-EVALUATION-BINDING-V1
          binding_version: V1
          canonical_record_digest:
            algorithm: SHA-256
            canonicalization: GATE-EVALUATION-RECORD-C14N-V1
            value: DIGEST-RECORD-EXAMPLE
          immutable_source_digest:
            algorithm: SHA-256
            canonicalization: IMMUTABLE-SOURCE-C14N-V1
            value: DIGEST-SOURCE-EXAMPLE
        state: UNKNOWN
        supporting_evidence_ids: []
        counterevidence_ids: []
        conflict_relation_ids: []
        missing_paths: []
        conflict_paths: []
        unknown_paths:
          - ISSUE-1
        reason_codes:
          - GATE.STATE_UNKNOWN
        source_decision_ref: null
    set_state: READY
    issue_ids:
      - ISSUE-1

action_envelope:
  action_id: ACTION-EXAMPLE
  selected_action: ASK
  subject_candidate_ids:
    - CANDIDATE-A
  payload:
    question_requests:
      - question_id: QUESTION-1
        target_issue_ids:
          - ISSUE-1
        requested_field_paths:
          - /example/path
        expected_answer_shape: declared-structured-value
    unresolved_issue_ids:
      - ISSUE-1
    resume_token: RESUME-EXAMPLE
  basis_record_ids:
    - GATE-1
  blocking_issue_ids: []
  nonblocking_issue_ids:
    - ISSUE-1
  reason_codes:
    - GATE.STATE_UNKNOWN
  source_decision_refs:
    - DECISION-EXAMPLE
  output_precision_binding:
    presence: RESOLVED
    ref:
      declaration_id: OUTPUT-PRECISION-FXX
      declaration_type: OUTPUT_PRECISION
      card_id: FXX
      contract_version: CONTRACT-VERSION-EXAMPLE
      declaration_schema_version: DECLARATION-SCHEMA-VERSION-EXAMPLE
      content_digest: DIGEST-EXAMPLE
  validation_plan_binding:
    presence: ABSENT
    reason_code: DECLARATION_NOT_PRESENT
  structural_validity: VALID
  validation_errors: []
```

示例中的 `FXX` 是非生产占位符。示例不表示 ASK 必然优先于其他失败安全动作，只证明 ASK payload 如何绑定 unknown issue 和字段路径。

## 17. 接口不变量汇总

1. PI-220 输入只读，输出独立。
2. 所有结论性状态均有来源判定引用；协议校验器不生产业务结论。
3. 每个声明成员单独记录，不用聚合分数代替；多个记录允许共享同一个真实整体冻结 ref，但必须经版本化、摘要绑定的显式成员声明形成全双射。
4. record→member→真实冻结 ref 由显式身份和不可变 evaluation binding 唯一确定；重复、遗漏、未知成员、共享 ref 不一致及成员／状态置换全部 fail closed，不依赖 ID 解析、数组位置、证据内容、issue path 或自然语言。
5. 最低充分参与集合的六类通用角色逐项独立记录，`OUTPUT` 不得绕过；协议不执行卡片算法。
6. `SATISFIED` 的现实门支持证据只来自 `REALITY_FACT`。
7. 缺证、冲突、未知分别建模并保留字段路径。
8. 来源字段状态与 evaluator 状态分别记录；声明值 `null`、unresolved、absent、unknown、conflict 不得静默折叠，声明引用存在性另由 `FrozenDeclarationBinding` 判别。
9. 竞争按冻结维度携带引用，但不强制唯一 winner。
10. 反证必须引用证据和关系，不以自由文本替代。
11. 根源与时序分账，约束检查引用冻结来源。
12. `validation_timepoints` 与 `output_precision` 使用独立 `FrozenDeclarationBinding`，并以不同 `FrozenDeclarationRef.declaration_type` 分账；声明存在且值为 null 时仍须保留 `RESOLVED.ref`。
13. 一个 envelope 恰有一个五动作及匹配 payload，五动作统一使用非空 `BasisRecordIds`。
14. 包不可消费、存在 blocking integrity issue，或任一必要声明 binding 为 `UNAVAILABLE`／`UNRESOLVABLE` 时，`OUTPUT`、`CONDITIONAL` 无效。
15. reason code 只解释结构事实，不承载卡片业务规则。
16. 适配器只能做无推断转换，并保留有损与不可映射状态。
17. 现有轨道的 winner、decision、abstain、question、human-review 标志均不能直接升级为 PI-220 动作。

## 18. PI-220 自检

| 检查项 | 结果 | 说明 |
|---|---|---|
| 唯一产物边界 | 符合 | 仅设计本计划文档 |
| PI-210 只读输入 | 符合 | 定义只读端口与独立结果对象 |
| 逐门满足/缺失/冲突 | 符合 | 另含 unknown，且不改变三种必需状态 |
| 共享真实 ref 与成员身份 | 符合 | 版本化声明集、显式成员值、全双射、不可变 evaluation binding 与 permutation falsifier；不扩张冻结路径 |
| 最低充分参与角色 | 符合 | 六类通用角色独立记录状态与证据／缺证／冲突引用；`OUTPUT` 不可绕过 |
| 竞争与反证引用 | 符合 | 显式维度、证据、关系和处置引用；无排名 |
| 根源与时序分账 | 符合 | 独立账本及引用式约束检查 |
| 五动作 envelope | 符合 | 五动作一一对应 payload 并统一使用非空 `BasisRecordIds`；unknown 非动作 |
| 失败安全结构约束 | 符合 | 定义可采纳性，不定义选择算法或优先级 |
| 来源／evaluator 状态边界 | 符合 | 两套状态分别记录并以禁止折叠矩阵约束；路径保留 JSON Pointer、owner 与 source object |
| reason codes | 符合 | 仅结构性命名空间和机械事实 |
| 现有轨道适配边界 | 符合 | 单向、只读、无推断；不改变默认行为 |
| YAML 非执行 | 符合 | 仅允许字段寻址、类型保持读取和版本核对 |
| 无卡片特定逻辑 | 符合 | 无 F01–F12 特定 `if/else` 或具体结论 |
| 无评分/权重/排序 | 符合 | schema 不提供相关字段，不规定唯一 winner |
| null/unresolved/absent/unknown 保真 | 符合 | 声明值状态、引用存在性与 evaluator 状态分账；裸 nullable 引用禁用 |
| 时间点与输出精度分账 | 符合 | 两类声明独立使用 `FrozenDeclarationBinding`，并以不同 `declaration_type` 的稳定 `FrozenDeclarationRef` 分账 |
| 不设计 G3/G5 | 符合 | 仅说明边界，不给实现或测试执行计划 |
| 整改实例自检边界 | 符合 | 本节仅记录 PI-220 文档结构与范围自检，不作独立 G2 验收，不宣称 G2 PASS |

## 19. 治理声明

本文件完成 PI-220 的接口设计产物，不代表：

- PI-200 已完成；
- G2 已通过；
- G3、G4 或 G5 已解锁；
- F01–F12 已进入生产；
- 任何现有运行轨道已支持统一五动作；
- 任何具体案例或卡片已产生结论。

后续是否接受本接口、如何汇总 G2，以及是否解除后续阶段阻断，均由 PI-290 和总控治理流程独立决定。

---

## 20. PI-220-A1 — Task 5 authority-binding amendment（2026-07-21）

### 20.1 优先级、裁决来源与非目标

本节是版本化 `PI-220-A1` 修订，来源为 2026-07-21 Task 5 保留合同裁决及其后续确认。凡本节与第 1–19 节关于 participation authority、root/timing authority、Gate conflict 可采纳性或 `OUTPUT` 条件的文字冲突，以本节为准；未明确覆盖的历史语义继续有效。特别是既有 `GateEvaluationBindingRef`、其解析对象及 `get_gate_evaluation_binding()` 的字段、payload、摘要和失败语义完全不变；禁止继承、扩义、复用或改名为通用 authority binding。

本修订只增加两个独立 immutable binding 和 canonical `NormalizedEvidenceReadPort` 上两个 resolver；不增加第三个 port，不增加 source-resolution resolver，不改变 PI-210 relation schema，不定义选择、评分、排名或业务推断算法。

### 20.2 两个独立 immutable binding

以下两个类均为独立 public runtime identity；不得以 type alias、继承、union、泛型参数、既有 gate binding 或结构相同的本地替身代替。

```python
@dataclass(frozen=True)
class FrozenParticipationRoleBinding:
    binding_id: str
    binding_version: str
    immutable_source_digest: DigestRef
    canonical_record_digest: DigestRef
    record_payload: Mapping[str, object]
    source_locator_id: str

@dataclass(frozen=True)
class FrozenRootTimingOutcomeBinding:
    binding_id: str
    binding_version: str
    immutable_source_digest: DigestRef
    canonical_record_digest: DigestRef
    record_payload: Mapping[str, object]
    source_locator_id: str
```

两个 envelope 均恰有以上六字段。全部 string 必须为非空；两个 digest 必须是有效 `DigestRef`；`record_payload` 在构造时递归冻结；额外 envelope 字段无效。class identity 分别固定 schema，`binding_version` 固定该 binding instance 所依据的 authority 版本；二者不得互换。

`FrozenParticipationRoleBinding.record_payload` 的 closed key set 恰为：

```text
participation_record_id
participation_set_id
role
frozen_definition_refs
state
supporting_evidence_ids
counterevidence_ids
missing_issue_ids
conflict_issue_ids
unknown_issue_ids
relation_ids
source_decision_ref
```

其中 `role` 是既有 `ParticipationRole` 的 role identity。`frozen_definition_refs` 为非空 tuple；其余复数字段均为 tuple。`state` 只能是既有 `ParticipationState`。`source_decision_ref` 对每个状态都必须是非空 string；authority 未提供 source decision 时 binding 无效，不得以 `None` 代替。每条 `ParticipationRoleRecord` 必须新增且只新增 `authority_binding_id: string`，并与一个独立 binding 一一对应；同一 binding 不得服务两个 role record。

逐状态 surface 不变量如下：

| `state` | 必须非空 | 必须为空 |
|---|---|---|
| `SATISFIED` | `supporting_evidence_ids`, `source_decision_ref` | `missing_issue_ids`, `conflict_issue_ids`, `unknown_issue_ids` |
| `MISSING` | `missing_issue_ids`, `source_decision_ref` | `supporting_evidence_ids`, `conflict_issue_ids`, `unknown_issue_ids` |
| `CONFLICT` | `supporting_evidence_ids`, `counterevidence_ids`, `conflict_issue_ids`, `relation_ids`, `source_decision_ref` | `missing_issue_ids`, `unknown_issue_ids` |
| `UNKNOWN` | `unknown_issue_ids`, `source_decision_ref` | `missing_issue_ids`, `conflict_issue_ids` |
| `NOT_APPLICABLE` | `source_decision_ref` | 全部 evidence、issue 与 relation tuples |

表中未要求为空的字段可由 authority 显式提供，但不得从其他 role 借用。每个 role 的 state、evidence、issues、relations 和 source decision 必须仅来自该 role binding；禁止一个 aggregate boolean、共享 aggregate evidence、共享 binding、角色间复制或缺失时借证。两个 role 即使内容相同，也必须拥有不同 `binding_id`，且 payload 中保留各自 role identity。

`FrozenRootTimingOutcomeBinding.record_payload` 的 closed key set 恰为：

```text
check_id
constraint_ref
root_entry_ids
timing_entry_ids
state
source_decision_ref
missing_paths
conflict_paths
unknown_paths
reason_codes
```

`constraint_ref` 必须是精确 `FrozenConstraintRef`；entry ID 字段均为 tuple，且 `root_entry_ids` 与 `timing_entry_ids` 都非空；path 与 reason 字段均为 tuple；`state` 只能是既有 `ConstraintCheckState`；`source_decision_ref` 对每个状态都必须是非空 string，缺失即 binding 无效。每条 `RootTimingConstraintCheck` 必须新增且只新增 `authority_binding_id: string`，并与一个 binding 一一对应。逐状态 surface 不变量如下：

| `state` | 必须非空 | 必须为空 |
|---|---|---|
| `SATISFIED` | `source_decision_ref` | `missing_paths`, `conflict_paths`, `unknown_paths`, `reason_codes` |
| `VIOLATED` | `source_decision_ref`, `conflict_paths`, `reason_codes` | `missing_paths`, `unknown_paths` |
| `UNKNOWN` | `source_decision_ref`, `unknown_paths`, `reason_codes` | `missing_paths`, `conflict_paths` |
| `NOT_APPLICABLE` | `source_decision_ref`, `reason_codes` | `missing_paths`, `conflict_paths`, `unknown_paths` |

`VIOLATED` 必须同时有 conflict path 和 reason；`UNKNOWN` 必须同时有 unknown path 和 reason。evaluator 不得制造 binding、source decision、entry ID、path/reason 或硬编码 `SATISFIED`。

两个类的 `canonical_record_digest` 都必须对对应 closed payload 的全部 key/value 以 key 名升序、tuple 顺序保真、`DigestRef`/冻结 ref 全字段展开的 RFC 8785 JCS UTF-8 bytes 计算 lowercase `sha256`。`immutable_source_digest` 对 `source_locator_id` 所定位的完整不可变 authority source bytes 按 locator 声明的 canonicalization 计算。摘要不是自认证字段；任何字段、顺序、版本、locator、来源、类型或摘要不一致均失败关闭。

### 20.3 canonical port resolvers 与失败语义

既有 canonical `NormalizedEvidenceReadPort` 追加且只追加以下两个方法：

```python
def get_participation_role_binding(
    self,
    binding_id: str,
) -> FrozenParticipationRoleBinding: ...

def get_root_timing_outcome_binding(
    self,
    binding_id: str,
) -> FrozenRootTimingOutcomeBinding: ...
```

resolver 输入必须是非空 string，否则抛 `ValueError`；零匹配抛 `KeyError(binding_id)`；多匹配、closed payload 违规、authority/source 不可变性不可证、版本/locator/digest/逐值不匹配均抛 `ValueError`；解析到错误 runtime class identity 抛 `TypeError`。不得返回 `None`、sentinel、fallback、相近版本或 gate binding。consumer 捕获这些失败后必须把所属结构置为 blocking/invalid，禁止降级推断。

Task 9 与 Task 10 必须 import/reuse `engine.f09.contracts` 中这两个 class identity 和同一个 `NormalizedEvidenceReadPort` identity；不得在 application、tests、fixture、adapter 中重声明、包装为第三个 port、从 dict 重建或绕过 resolver。

### 20.4 Gate conflict relation 可采纳矩阵

某 relation 只有同时满足以下全部条件，才可进入 gate record 的 `conflict_relation_ids`：

| 轴 | 唯一允许值/条件 |
|---|---|
| `relation_type` | `COUNTERS` 或 `COMPETES_WITH` |
| `status` | `ASSERTED` 或 `OBSERVED` |
| `scope.function_id` | 精确 `F09` |
| 当前 member endpoint | `to_ref.object_type == EVIDENCE` 且 `to_ref.object_id` 属于当前 gate member record 的 evidence ID 闭集 |
| 对端 | `from_ref.object_type == EVIDENCE`，且 `from_ref.object_id != to_ref.object_id` |
| 来源 | `source_refs` 非空 |
| 前置 | `validate_for_pi220(package_id) == READY` |

当前 member evidence ID 闭集是该 record 的 `supporting_evidence_ids ∪ counterevidence_ids`；不得借用其他 member 或其他 role 的 evidence。方向固定，反向 relation 无效。`CONTRADICTS`、`PROPOSED`、`DISPUTED`、非 F09/null scope、非 evidence endpoint、自环、外部或其他 member endpoint 均不可采纳并使引用它的 gate record fail closed。`ASSERTED | OBSERVED` 是从 PI-210 四状态中选择的最保守机械闭集：排除尚未采纳的 proposed 与正在争议的 disputed，但不虚构观察级别优先级。

`source_refs` 的存在性和解析完整性完全由成功的 PI-210 validation 负责。Task 5 只验证非空并依赖 `READY` 前置，不重新解析 source ref，不增加 source resolver。

### 20.5 `OUTPUT` 条件、falsifiers 与治理边界

`GateEvaluationSet.set_state == READY` 只证明声明/记录结构闭合，不证明业务满足。`OUTPUT` 必须同时满足：

1. 每个必要 gate 的每条 `GateEvaluationRecord.state == GateEvidenceState.SATISFIED`；
2. 六个 participation role 各自存在唯一 record/独立 authority binding，且每条 `state == SATISFIED`；`NOT_APPLICABLE` 不可用于 `OUTPUT`；
3. 每条 root/timing check 均由唯一 authority binding 解析，且 `state == SATISFIED`；
4. 上述所有 binding、relation 与 PI-210 integrity 验证成功。

任一条件失败必须阻断 `OUTPUT`，不得以 `READY`、集合非空、aggregate flag、默认值或其他角色/成员结果替代。

实现与测试的精确闭集仅为 `engine/f09/contracts.py`、`engine/f09/decision.py`、`tests/f09/conftest.py`、`tests/f09/test_decision_contract.py`。任何其他路径变化立即 STOP。最低 falsifier matrix 必须逐项独立覆盖：binding 不存在/重复/错误 class；两个新 binding 的额外/缺失 payload key；任一 payload 值或 tuple 顺序变化但摘要未变；role swap、共享 binding、共享 evidence、跨 role 借证；root/timing entry/constraint swap；evaluator 硬编码 satisfied；`VIOLATED` 或 `UNKNOWN` 缺 path/reason；relation type/status/scope/方向/endpoint/source refs 各轴单独非法；PI-210 integrity 非 READY；gate set READY 但一条 gate 非 satisfied；任一 role 非 satisfied；任一 check 非 satisfied。每项均须 fail closed。

本 amendment 不授权 Python、tests、pytest、import、Git 或 GitHub 操作。GitHub 服务端变更永久禁止。它只冻结下一实现 Gate 的合同；实现后仍需 fresh independent review，且不得由本 CONTRACT reviser 自证通过。
