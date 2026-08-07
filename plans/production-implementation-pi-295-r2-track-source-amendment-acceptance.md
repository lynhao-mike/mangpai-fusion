# PI-295-R2：Track source amendment 独立静态验收

## 1. 验收身份与边界

- 任务：`PI-295-R2`
- 父任务：`PI-200`
- 验收对象：[`production-implementation-pi-235-r1-track-source-state-clarification.md`](production-implementation-pi-235-r1-track-source-state-clarification.md) 及其写入 [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md) 的实际 canonical 增量。
- 审查方式：逻辑 fresh review；本实例不采用 amendment 作者的自评作为验收证据，只依据授权原始文件重新作静态裁决。
- 执行边界：只读授权的八个文件；未运行 Python、pytest、test collection、计划代码片段、YAML、mapping、Git 或任何实现验证命令；未修改任何既有文件。
- 裁决口径：任一 High、Medium、critical ambiguity、关键证据缺口、canonical 类型冲突、冻结语义变化或 production-default 回归均须 `BLOCKED`。

## 2. Verdict

# BLOCKED

该 amendment 已经为 `track_match=UNKNOWN` 建立双侧 typed source-state 输入，且未发现 `RunTrack`、PI-220、F09/F08 或 production-default 回归；但是，合法且完整的失败状态 binding 只被规定为 fail closed，没有唯一确定 required `FeedbackBinding.status` 在 `UNBOUND | AMBIGUOUS | INVALID` 中的输出。该歧义位于 canonical 输出契约内，足以使两个合规实现对相同 typed inputs 产生不同结果，因此构成 1 个 Medium 和 1 个 critical ambiguity。按本任务 fail-closed 标准，不能接受 amendment。

本裁决仅是静态契约验收结论，不是实现正确性、测试通过、G5 解阻、rollout 或 production 使用授权。

## 3. Severity 与门禁统计

| 类别 | 数量 | 门禁结果 |
|---|---:|---|
| High | 0 | 无 High |
| Medium | 1 | 阻断 |
| Low | 0 | 无 Low |
| Critical ambiguity | 1 | 阻断；与 Medium M-01 为同一根因，不重复计为第二缺陷 |
| Key evidence gap | 0 | 授权静态证据足以定位根因 |
| Canonical type conflict | 0 | 未发现 |
| Frozen-semantics regression | 0 | 未发现 |
| Production-default regression | 0 | 未发现 |
| Relevant regression | 0 | 未发现 |

## 4. 阻断发现

### M-01 / CA-01：失败 source state 没有唯一闭合 `FeedbackBinding.status`

**观察事实**

1. [`TrackSourceState`](production-implementation-pi-230-traceability-binding.md:621) 封闭定义了 `SOURCE_MISSING`、`UNPARSABLE`、`AMBIGUOUS`、`INTEGRITY_FAILED` 四种失败状态。
2. [`FeedbackBinding.status`](production-implementation-pi-230-traceability-binding.md:693) 是 required 字段，封闭值域为 `BOUND | UNBOUND | AMBIGUOUS | INVALID`。
3. truth table 对任一合法失败状态唯一确定 `track_match=UNKNOWN`，但“binding 处理”只写 fail closed；只有 binding 缺失、引用不可解析、版本或 digest 不一致时才显式固定 `status=INVALID`（[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:700)，[`production-implementation-pi-235-r1-track-source-state-clarification.md`](production-implementation-pi-235-r1-track-source-state-clarification.md:81)）。
4. `BOUND` 最低条件和学习门禁排除了 `track_match=UNKNOWN` 成为 `BOUND` 或自动 `ELIGIBLE`，但没有在剩余的 `UNBOUND | AMBIGUOUS | INVALID` 中给出逐状态唯一选择（[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:713)，[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:739)）。
5. legacy 缺 binding 被单独固定为 `INVALID`，不能补足合法、完整但 source state 失败的情形（[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:741)）。

**为何阻断**

对于同一对结构完整、引用有效的 bindings，例如 source 为 `SOURCE_MISSING`、target 为 `AVAILABLE_RESOLVED`，现有文字可唯一推出 `track_match=UNKNOWN` 和不可学习，却不能机械唯一推出整体 status 是 `UNBOUND` 还是 `INVALID`。当 source state 为 `AMBIGUOUS` 时，也不能唯一确定 aggregate status 是否必须为 `AMBIGUOUS`。这些状态不是注释，而是 required canonical output；实现分歧会进入绑定审计、下游策略和测试预期。

**最小 falsifier**

若现有授权事实源中存在一张覆盖“完整 binding + 每种 `TrackSourceState` + 其他六维组合”的互斥 status 决策表，并能对每个输入唯一输出 `UNBOUND`、`AMBIGUOUS` 或 `INVALID`，则本发现可被证伪。授权范围内未见该闭包。

## 5. 逐项验收矩阵

| # | 验收项 | 结果 | 静态证据与裁决 |
|---:|---|---|---|
| 1 | `TrackSourceBinding` 字段引用已定义 canonical types | PASS | `RunTrack`、`DigestRef` 由 PI-210 定义（[`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:99)）；`VersionedObjectRef` 与 `DigestBinding` 由 PI-230 定义（[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:263)）；新增封闭类型见 [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:620)。未见未定义字段类型。
| 2 | source/target 基数与引用可机械关联 | PASS | submission 恰一内嵌 source binding、binding 恰一 source ref 和恰一 target binding；side 与 submission track 对齐规则明确（[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:671)，[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:698)）。
| 3 | 失败状态下 `source_evidence_ref`、`parser_ref` 可合法存在 | PASS | source missing 时仍引用可证明缺失的不可变捕获；parser ref 始终引用实际 parser/resolver revision（[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:671)）。`VersionedObjectRef.digest_binding=MISSING` 可保留对象作人工审计但不得安全绑定或学习（[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:277)，[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:295)）。
| 4 | `content_digest` 与 `VersionedObjectRef.digest_binding` 关系明确 | PASS | binding 以稳定 ID、schema/contract version、`content_digest` 定版；source ref 必须按 identity、schema/contract version 与 digest 精确引用（[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:671)，[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:698)）。`DigestBinding=MISSING` 不能完成精确跨文件绑定，继而落入 invalid/unknown 行（[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:295)，[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:708)）。
| 5 | reason code 值域与基数闭合 | PASS | 四个失败状态对应四个同名封闭 reason code；`AVAILABLE_RESOLVED` 必须为空，其余状态必须恰一对应值（[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:639)，[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:673)）。
| 6 | truth table 完备、互斥 | PASS（仅 `track_match`） | 双 resolved 按相等/不等互斥分成 MATCH/MISMATCH；任一失败为 UNKNOWN；输入缺失或 identity/version/digest 无效为 UNKNOWN + INVALID；兜底句禁止其他组合比较占位 track（[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:700)）。
| 7 | 双方均 `AVAILABLE_RESOLVED` 时只能 MATCH/MISMATCH | PASS | 两个互斥比较行明确（[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:704)）。
| 8 | 任一失败或 binding identity/version/digest 无效时 UNKNOWN | PASS | 失败状态与无效 canonical input 分行覆盖（[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:706)）。
| 9 | `INVALID`、`UNBOUND`、`AMBIGUOUS` 关系无冲突且唯一 | **BLOCKED** | 无直接值冲突，但合法失败状态没有 required aggregate status 的唯一映射；见 M-01/CA-01。
| 10 | 非空 `RunTrack` 不变且没有 UNKNOWN Track | PASS | PI-210 值域仍为五个非空 track，无 UNKNOWN（[`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:99)）；amendment 明确 UNKNOWN 仅为 match 结果（[`production-implementation-pi-235-r1-track-source-state-clarification.md`](production-implementation-pi-235-r1-track-source-state-clarification.md:94)）。
| 11 | source state 不依赖 anchor、item integrity 或自由文本 | PASS | 禁止反推和替代，并明确 anchor 正交（[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:673)，[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:711)）。
| 12 | 其他六维独立 | PASS | amendment 明确只澄清 `track_match` canonical 输入，其他六维输入、值域和独立计算不变（[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:711)，[`production-implementation-pi-235-r1-track-source-state-clarification.md`](production-implementation-pi-235-r1-track-source-state-clarification.md:101)）。
| 13 | UNKNOWN 不可 ELIGIBLE | PASS | UNKNOWN 不满足 BOUND 最低条件，只可 INELIGIBLE 或按显式策略 HUMAN_REVIEW，不得学习（[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:739)）。
| 14 | legacy 缺字段 fail closed | PASS | 固定 UNKNOWN + INVALID + 非 ELIGIBLE，且禁止复制非空 track 静默补齐（[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:743)）。
| 15 | amendment 最小、通用、非 F09 专属 | PASS | 增量位于通用 FeedbackBinding 契约，只增加 track source state/binding 与比较规则；非目标明确不改 F09 或其他卡片（[`production-implementation-pi-235-r1-track-source-state-clarification.md`](production-implementation-pi-235-r1-track-source-state-clarification.md:120)）。
| 16 | 不改 PI-220 六门、六角色、五动作 | PASS | amendment 明确不修改 PI-220（[`production-implementation-pi-235-r1-track-source-state-clarification.md`](production-implementation-pi-235-r1-track-source-state-clarification.md:124)）；PI-220 五动作值域与角色/门边界仍由原契约持有（[`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:90)，[`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:348)）。
| 17 | 不改冻结 F09、F08、rollout/default | PASS | amendment 明确冻结业务语义和 production-default 不变（[`production-implementation-pi-235-r1-track-source-state-clarification.md`](production-implementation-pi-235-r1-track-source-state-clarification.md:103)），且非目标排除门、评分、动作、学习策略和 default 变化（[`production-implementation-pi-235-r1-track-source-state-clarification.md`](production-implementation-pi-235-r1-track-source-state-clarification.md:122)）。未见实际 canonical 增量越界。
| 18 | 足以让后续 PI-500 用 literal typed inputs 表达 UNKNOWN | PASS（能力边界） | PI-230 已提供两侧 typed binding 和确定性 track truth table（[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:625)，[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:698)）。现有 PI-500 仍使用 `track_fact_available` 与 anchor 间接刺激，且旧 submission/binding shape 尚未消费这些字段；这证明后续计划需整改，不否定新 contract 的 literal-input 表达能力（[`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:1774)，[`production-implementation-pi-590-r6-g5-plan-reacceptance.md`](production-implementation-pi-590-r6-g5-plan-reacceptance.md:72)）。本验收未修复 PI-500。

## 6. 对既有 G2/G5 结论的边界

- 未发现 amendment 回归 PI-290-R3 已验收的唯一 `RunTrack`、版本对象引用和摘要绑定基线；该结论仅限静态差异审查（[`production-implementation-pi-290-r3-g2-reacceptance.md`](production-implementation-pi-290-r3-g2-reacceptance.md:141)）。
- PI-590-R6 的原 G5 `BLOCKED` 不能因本验收自动解除。amendment 已补上其 H-01 所缺的 canonical 表达能力，但 PI-500 尚未整改，且本轮又发现 canonical aggregate status 闭包缺口（[`production-implementation-pi-590-r6-g5-plan-reacceptance.md`](production-implementation-pi-590-r6-g5-plan-reacceptance.md:66)）。
- 本文不能关闭 PI-590-R6 的其他 H/M 发现，也不能证明实现或测试行为。

## 7. 遗留非阻断风险

在 M-01 修复之前，下列事项仅记录为非新增阻断风险，不得解释为已验证：

1. `VersionedObjectRef` 使用通用 `object_type: string`，具体 track binding object-type token 仍需后续实现契约固定；当前 identity + version + digest 规则足以表达精确引用，但尚无运行证据。
2. 本次执行被明确限制为静态审查；schema 可序列化性、adapter 行为、binder 分支覆盖和跨文件 digest 实际一致性均未验证。
3. PI-500 仍是旧消费形状；literal typed inputs 的可消费性是契约能力判断，不是已有实现事实。

## 8. 唯一下一动作

返回 amendment remediation：仅在 PI-230 的 track source 增量中补一张完整、互斥、确定性的 `FeedbackBinding.status` 决策表，覆盖两侧 bindings 均结构有效时四种失败 `TrackSourceState` 与其他六维结果的组合，并明确：

- 哪些组合唯一输出 `UNBOUND`；
- 哪些组合唯一输出 `AMBIGUOUS`；
- 哪些组合唯一输出 `INVALID`；
- `TrackSourceState.AMBIGUOUS` 是否以及何时提升 aggregate status；
- 输入缺失、identity/schema/contract version/digest 无效仍固定 `INVALID`；
- 所有 `track_match=UNKNOWN` 组合仍不可 `BOUND` 或 `ELIGIBLE`。

修订必须保持 `RunTrack` 非空、其他六维独立、PI-220、F08/F09 冻结语义和 production-default 不变。完成该最小 amendment 后，重新提交独立静态验收；不得直接进入 PI-570-R6、PI-500 实现、测试、rollout 或 production-default 变更。
