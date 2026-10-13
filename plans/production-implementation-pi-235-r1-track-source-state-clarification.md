# PI-235-R1：Track 来源状态契约澄清

> `task_id`: PI-235-R1  
> `parent_task_id`: PI-200  
> 状态：READY_FOR_REVIEW  
> 授权：用户明确选择 Option A；仅对 PI-230 做最小契约 amendment  
> 边界：设计澄清，不授权实现、测试、迁移执行或 production-default 变更

## 1. 结论

PI-230 现以最小、通用且非 F09 专属的 typed binding 澄清 track 来源状态。PI-210 唯一、非 nullable 的 `RunTrack` 保持不变，也不增加 `UNKNOWN` 枚举值；来源是否存在、能否唯一解析以及完整性是否通过，由独立的 `TrackSourceBinding.state` 表达。

binder 必须同时消费 submission source-side 与 binding target-side 两个 canonical typed binding。只有双方均为 `AVAILABLE_RESOLVED` 时才比较非空 track 值并唯一产生 `MATCH` 或 `MISMATCH`；任一侧缺失、不可解析、歧义、完整性失败或 binding 无法精确验证时固定产生 `UNKNOWN` 并 fail closed。R2 进一步固定 aggregate status 的唯一优先级为 `INVALID > AMBIGUOUS > UNBOUND > BOUND`，从而使相同 canonical typed inputs 同时唯一确定 `track_match` 与 `FeedbackBinding.status`。

## 2. 授权与修改范围

本 amendment 仅修改：

1. [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md)：canonical 契约增量；
2. [`production-implementation-pi-235-r1-track-source-state-clarification.md`](production-implementation-pi-235-r1-track-source-state-clarification.md)：本次 amendment 的授权、边界与审查工件。

未修改总控、handoff、PI-210、PI-220、PI-500、PI-590-R6、META、代码、测试、YAML 或 mapping。

## 3. 问题

原 PI-230 同时要求：

```text
FeedbackSubmission.track: RunTrack required
FeedbackBinding.track_match: MATCH | MISMATCH | UNKNOWN required
```

但未提供与非空 track 值正交的来源可用性／解析状态。下游因此无法仅凭 canonical typed inputs 区分以下事实：

- 来源成功且唯一解析为某个合法 track；
- 来源字段缺失；
- 来源存在但不可解析；
- 来源解析结果歧义；
- 来源、parser 或 binding 完整性失败。

自由文本 issue、`FeedbackItem.integrity` 或 `record_anchor_ref` 缺失均不足以承担该职责。特别是，删除 records anchor 不能合法表示 track 来源不可比较。

## 4. 精确 schema 增量

PI-230 新增以下封闭类型：

```text
TrackSourceState =
  AVAILABLE_RESOLVED | SOURCE_MISSING | UNPARSABLE |
  AMBIGUOUS | INTEGRITY_FAILED

TrackSourceBinding {
  track_source_binding_id: string required
  side: SUBMISSION_SOURCE | BINDING_TARGET required
  track: RunTrack required
  state: TrackSourceState required
  source_evidence_ref: VersionedObjectRef required
  parser_ref: VersionedObjectRef required
  schema_version: string required
  contract_version: string required
  content_digest: DigestRef required
  state_reason_codes: list<TrackSourceReasonCode> required
  captured_at: datetime required
}
```

### 4.1 必填性与基数

- 每个 `FeedbackSubmission` 必须恰有一个 `track_source_binding`；其 `side=SUBMISSION_SOURCE` 且 binding track 与 submission track 相同。
- 每个 `FeedbackBinding` 必须恰有一个 `source_track_binding_ref`，按 identity、version 和 digest 精确引用所属 submission binding。
- 每个 `FeedbackBinding` 必须恰有一个 `target_track_source_binding`；其 `side=BINDING_TARGET`。
- 两侧 binding 都是 binder 的 canonical typed input，任一侧不得从 anchor、item integrity、issue 文本或其他隐式状态反推。

### 4.2 审计证据

- `source_evidence_ref` 使用 `VersionedObjectRef` 指向承载或本应承载 track 的不可变来源捕获；来源字段缺失时仍需引用证明该缺失的捕获对象。
- `parser_ref` 使用 `VersionedObjectRef` 指向实际 parser／resolver revision，必须携带稳定 identity、schema／contract version 和 `DigestBinding`。
- binding 自身使用稳定 ID、schema／contract version 和 `DigestRef` 定版，不允许不可追溯裸布尔值。
- `AVAILABLE_RESOLVED` 要求来源存在、唯一解析、来源完整性通过、parser 完整性通过；失败状态中的非空 track 只是合法声明值，不得参加比较。

## 5. 确定性 truth table

| source-side | target-side | 比较条件 | `track_match` | binding 处理 |
|---|---|---|---|---|
| `AVAILABLE_RESOLVED` | `AVAILABLE_RESOLVED` | 两侧完整且 track 相等 | `MATCH` | 可继续核对其余维度 |
| `AVAILABLE_RESOLVED` | `AVAILABLE_RESOLVED` | 两侧完整且 track 不等 | `MISMATCH` | fail closed |
| 任一失败状态 | 任意状态 | 不可比较 | `UNKNOWN` | fail closed |
| 任意状态 | 任一失败状态 | 不可比较 | `UNKNOWN` | fail closed |
| binding 缺失，或 identity／schema／contract／digest 无效、不一致、无法解析（不含结构有效的多候选歧义） | 任意状态 | canonical input 无效 | `UNKNOWN` | `status=INVALID`，fail closed |
| 任意状态 | binding 缺失，或 identity／schema／contract／digest 无效、不一致、无法解析（不含结构有效的多候选歧义） | canonical input 无效 | `UNKNOWN` | `status=INVALID`，fail closed |

“失败状态”仅指 `SOURCE_MISSING | UNPARSABLE | AMBIGUOUS | INTEGRITY_FAILED`。除前两行外，任何组合都不得使用占位 track 值产生 `MATCH` 或 `MISMATCH`。

### 5.1 Aggregate status 的固定优先级与互斥表

七维 match 独立计算完成后，`FeedbackBinding.status` 必须按 `INVALID > AMBIGUOUS > UNBOUND > BOUND` 从高到低求值；命中首行即停止，低优先级事实不得覆盖已命中的高优先级状态。canonical input 包括 feedback item 引用、两侧 track source bindings、各 protocol 要求的 target／artifact／anchor 及其 identity、schema／contract version 与 digest。required dimension 仍仅由 PI-230 既有 `binding_protocol` 决定；本 amendment 不新增 required 维度，也不改变各维值域或独立计算。

| 优先级 | 互斥条件（均隐含未命中更高行） | 唯一 aggregate status |
|---:|---|---|
| 1 | 任一 required canonical input 缺失，或 identity／schema／contract／digest 无效、不一致、无法解析（不含下一行结构有效的多候选歧义）；任一侧 `INTEGRITY_FAILED`；legacy 缺 required binding | `INVALID` |
| 2 | 结构与完整性有效，但任一 canonical identity resolution 存在 genuinely ambiguous 的多个合法候选而不能唯一选择；或任一侧 source state 为 `AMBIGUOUS` | `AMBIGUOUS` |
| 3 | 结构有效且无歧义，但任一侧为 `SOURCE_MISSING`／`UNPARSABLE`；或双方 `AVAILABLE_RESOLVED` 且 track `MISMATCH`；或其他任一 protocol-required dimension 为 `MISMATCH`／`UNKNOWN`；或 required target／artifact／anchor 缺失、既有最低绑定条件不足 | `UNBOUND` |
| 4 | 双方 `AVAILABLE_RESOLVED` 且 track `MATCH`；其他所有 protocol-required dimensions 均 `MATCH`；只有该 protocol 明示允许的维度为 `NOT_APPLICABLE`；required target／artifact／anchor 与既有最低条件全部满足；且未命中前三行 | `BOUND` |

该表穷尽合法输入：双方 track `MATCH` 但其他六维出现 required `UNKNOWN`／`MISMATCH` 时固定 `UNBOUND`；protocol 明示允许的 `NOT_APPLICABLE` 可保留，非明示允许的 `NOT_APPLICABLE` 不能绕过 required match，按最低条件不足固定 `UNBOUND`。`track_match=UNKNOWN` 永远不能落入 `BOUND` 或自动 `ELIGIBLE`。source state `AMBIGUOUS` 在没有更高 `INVALID` 时必须提升 aggregate status 为 `AMBIGUOUS`；`SOURCE_MISSING`／`UNPARSABLE` 在结构有效且无歧义时固定为 `UNBOUND`；`INTEGRITY_FAILED` 固定为 `INVALID`。

## 6. 不变量

1. `RunTrack` 的所有权和值域仍属于 PI-210；本 amendment 不扩展、不 nullable 化该类型。
2. track 值与 track 来源状态正交；来源失败不改变合法非空 track 值。
3. `UNKNOWN` 是 match 结果，不是 track 值。
4. `record_anchor_ref` 与 track 来源状态独立；anchor 缺失不能制造 `UNKNOWN`，anchor 存在不能提升来源状态。
5. `FeedbackItem.integrity`、自由文本 `issue_ids` 和隐式约定不得替代 typed binding。
6. 七维 match 中只有 `track_match` 的 canonical 输入得到澄清；其他六维的字段、值域与独立推导不变，只按 PI-230 既有 protocol-required 条件参与通用 aggregate。
7. aggregate status 只按 `INVALID > AMBIGUOUS > UNBOUND > BOUND` 聚合；高优先级命中后不可被覆盖，且只有所有 protocol-required 条件和既有最低条件满足才可 `BOUND`。
8. `track_match=UNKNOWN` 不满足 `BOUND` 最低条件，不能成为 `BOUND` 或自动产生 `LearningEligibility.status=ELIGIBLE`。
9. legacy 缺 binding 仍固定为 `INVALID`；source state `AMBIGUOUS` 在无更高 `INVALID` 时固定聚合为 `AMBIGUOUS`。
10. production statement 和 preprod 仍分账；production-default 不变。
11. F01–F12（包括 F09）的门、评分、竞争、反证、根源、时序、动作与冻结业务语义均不变。

## 7. Legacy 兼容与迁移边界

legacy submission 缺少 required `track_source_binding` 时，不得静默假定 `AVAILABLE_RESOLVED`。在两侧 binding 被显式重建并验证前，规范结果固定为：

```text
FeedbackBinding.track_match = UNKNOWN
FeedbackBinding.status = INVALID
LearningEligibility.status != ELIGIBLE
```

允许的迁移仅是从可定位的原始 source snapshot 和有版本 parser／resolver 重建 typed binding。无法取得来源证据、无法唯一解析或无法验证完整性时必须保持 invalid／unknown；仅复制 legacy 非空 track 值不构成迁移完成。

本 amendment 不授权执行数据迁移，也不规定数据库、序列化、锁、事务或发布机制。

## 8. 非目标

本 amendment 不做以下事项：

- 不修改 PI-210 `RunTrack`；
- 不修改 PI-220 判定接口；
- 不修改 F09 或其他卡片业务语义；
- 不修改 PI-500 实现计划或 PI-590-R6 验收文档；
- 不设计代码、测试、YAML、mapping 或迁移脚本；
- 不改变门、评分、动作、学习策略或 production-default；
- 不宣称实现已完成或 G5 已解除阻断。

## 9. 静态证据与审查点

独立审查应至少核对：

1. PI-230 的 `FeedbackSubmission.track` 仍为 required `RunTrack`；
2. `RunTrack` 值域未增加 `UNKNOWN`；
3. 两侧 typed binding 的状态、基数、证据引用和版本／digest 约束完整；
4. truth table 对所有不可比较组合固定输出 `UNKNOWN`；
5. canonical input 无效、任一 `INTEGRITY_FAILED`、任一 `AMBIGUOUS`、任一 `SOURCE_MISSING`／`UNPARSABLE`、resolved track mismatch 及其他六维 allowed combinations 均由互斥表唯一聚合；
6. aggregate status 优先级严格为 `INVALID > AMBIGUOUS > UNBOUND > BOUND`，高优先级不可被覆盖；
7. legacy 缺 binding 固定为 invalid／unknown／fail closed；
8. anchor 与 track source state 明确独立；
9. `UNKNOWN` 不可成为 `BOUND` 或自动进入 `ELIGIBLE`；
10. 七维 match 的其他六维、PI-220、F09／其他冻结语义及 production-default 未改变；
11. PI-295-R2 的 M-01／CA-01 falsifier 已被 canonical 互斥表直接覆盖，且其余 17 个 PASS 项无静态回归。

## 10. R2 remediation record 与 finding closure mapping

- remediation task：`PI-235-R2`；目标仅为关闭 PI-295-R2 的单一根因 `M-01 / CA-01`。
- canonical 修改：PI-230 在原 `track_match` truth table 后新增 aggregate status 固定优先级、首命中停止规则、互斥穷尽表及对应不变量。
- finding closure mapping：PI-295-R2 M-01／CA-01 所述“同一合法完整失败 binding 可在 `UNBOUND | AMBIGUOUS | INVALID` 间产生多种输出”，现分别固定为：结构／完整性无效或 `INTEGRITY_FAILED` → `INVALID`；结构有效且 genuinely ambiguous 或 source state `AMBIGUOUS` → `AMBIGUOUS`；结构有效、无歧义但来源明确缺失／不可解析、确定 mismatch 或 required binding 条件不足 → `UNBOUND`；只有全部 protocol-required 条件及既有最低条件满足 → `BOUND`。
- falsifier closure：完整 binding + 每种 `TrackSourceState` + 其他六维既有允许组合现在按优先级首命中，单值输出；`track_match=UNKNOWN` 仍不能 `BOUND`／`ELIGIBLE`，legacy 缺 binding 仍 `INVALID`。
- 无回归边界：未改 schema、`RunTrack`、七维值域、六维独立推导、PI-220、F09／其他卡片、学习策略或 production-default；PI-295-R2 先前 17 个 PASS 项的依据未被本次增量撤销。
- 作者结论仅为 `READY_FOR_REVIEW`；本记录是整改映射，不是 finding 的独立验收关闭或 PASS 裁决。

## 11. 未执行声明

本任务仅进行了授权文档的静态编辑。未运行 Python、pytest、test collection、计划代码片段、YAML、mapping、Git 或任何实现验证命令。

## 12. 治理与下一动作

本 amendment 作者只完成契约澄清与范围自检，不具备独立验收授权，不得自验 PASS。当前结论仍为 `READY_FOR_REVIEW`。

唯一下一动作：由未参与本 R2 remediation 编写的独立实例，对第 9 节审查点、PI-295-R2 M-01／CA-01 falsifier、先前 17 个 PASS 项及 PI-230 实际 canonical 增量做静态复验，并单独裁决是否接受该整改。