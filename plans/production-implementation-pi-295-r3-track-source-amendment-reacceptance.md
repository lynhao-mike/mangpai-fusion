# PI-295-R3：Track source amendment 独立静态复验

## 1. 范围、身份与角色分离声明

- 任务：`PI-295-R3`。
- 父任务：`PI-200`。
- 验收对象：[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md) 中用于关闭 PI-295-R2 `M-01 / CA-01` 的最小 track source state aggregate-status amendment。
- 独立性：本验收实例是未参与 PI-235-R1/R2 编写的分离实例；不采信 amendment 作者在 [`production-implementation-pi-235-r1-track-source-state-clarification.md`](production-implementation-pi-235-r1-track-source-state-clarification.md:5) 中记录的 `READY_FOR_REVIEW` 作为接受证据，也不以其 closure mapping 代替独立裁决。
- 方法：仅对授权事实源作静态、逐行、交叉核对；以 canonical PI-210、PI-220、PI-230 文本为裁决基础，以 PI-295-R2 的 finding 和 falsifier 为回归基线。
- 写入边界：本文件是本次唯一写入；未修改 PI-210、PI-220、PI-230、PI-235、PI-500、PI-590、总控、handoff、生产代码、测试代码、YAML 或 mapping。
- 裁决门槛：任一 High、Medium、critical ambiguity、关键证据缺口、canonical type conflict、冻结语义回归、production-default 回归或其他相关回归均导致 `BLOCKED`。
- 裁决能力边界：本验收只能接受或拒绝静态契约 amendment；不能证明实现正确、测试通过、运行时接线完成、PI-500 可实施、G5 完成或可投产。

## 2. 必读事实源与精确静态证据

| 事实 | 静态证据 | 独立核对结果 |
|---|---|---|
| `RunTrack` 的 canonical owner 与封闭值域 | [`production-implementation-pi-210-normalized-evidence-model.md`](production-implementation-pi-210-normalized-evidence-model.md:99) | 仍为五个非空合法值；没有 `UNKNOWN`。 |
| PI-220 五动作保持封闭 | [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:90) | 仍为 `OUTPUT / CONDITIONAL / ASK / ABSTAIN / HUMAN_REVIEW`；本 amendment 未增加动作。 |
| PI-220 六类最低充分参与角色 | [`production-implementation-pi-220-decision-interface.md`](production-implementation-pi-220-decision-interface.md:348) | 六角色及其职责未被 track amendment 改写。 |
| `FeedbackSubmission.track` 与 typed source binding | [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:618) | `track` 仍为 required `RunTrack`；来源状态由正交 typed binding 表达。 |
| `TrackSourceState` 与 `TrackSourceBinding` 完整形状 | [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:620) | 五状态封闭；side、track、来源证据、parser、schema/contract version、digest、reason codes 和时间均为 required。 |
| source-side binding 的基数、side 与证据约束 | [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:671) | 每个 submission 恰一 source binding；缺失来源也必须有不可变证明捕获，parser revision 可审计。 |
| 失败状态、reason code 与占位 track 禁止提升 | [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:673) | 仅 `AVAILABLE_RESOLVED` 的 reason codes 为空；失败状态不能被非空 track、item integrity、issue 或 anchor 覆盖。 |
| 七维 match 与 aggregate status 的 canonical 字段 | [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:675) | 七维字段和值域保持原形；aggregate status 仍为 required 封闭四值。 |
| source/target typed binding 的恰一基数与精确关联 | [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:698) | source ref 必须按 identity、schema/contract version、digest 精确引用；target binding 必须独立且 side 正确。 |
| `track_match` truth table | [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:700) | 双 resolved 唯一得到 `MATCH/MISMATCH`；任一失败得到 `UNKNOWN`；canonical input 无效得到 `UNKNOWN + INVALID`。 |
| anchor/source-state 分账与其他六维独立 | [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:711) | anchor 不能制造或提升来源状态；`track_match=UNKNOWN` 不改变其他六维。 |
| aggregate status 固定优先级与首命中规则 | [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:713) | 明确按 `INVALID > AMBIGUOUS > UNBOUND > BOUND` 求值，命中首行即停止。 |
| 四行互斥 aggregate status 表 | [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:715) | 每行隐含“未命中更高行”，分别唯一输出四种 status。 |
| 穷尽、N/A 与 required 六维闭包 | [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:722) | 禁止 default `BOUND`；required `UNKNOWN/MISMATCH` 与未获允许的 N/A 均固定 `UNBOUND`。 |
| production statement 的 `BOUND` 最低条件 | [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:724) | track 之外仍要求 case、statement、revision、set、records、anchor metadata、source span 和 parser 等闭合。 |
| `track_match=UNKNOWN` 的学习准入边界 | [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:750) | 不得自动 `ELIGIBLE`；只能保持不可学习或按显式策略人审。 |
| legacy 缺 binding 的固定结果 | [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:752) | 固定 `track_match=UNKNOWN + status=INVALID + fail closed`，禁止复制已有非空 track 静默补齐。 |
| production-default 与 preprod 分账 | [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:774) | 两账本和 audit-only 跨轨边保持不变。 |
| F01–F12 非实现证明与冻结状态保真 | [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:805) | card identity 仍是 reference-only；null/unresolved/absent 与 evaluator 状态不折叠。 |
| canonical 不变量汇总 | [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:939) | 第 19–25 项明确重申类型正交、首命中、legacy、UNKNOWN、学习和默认行为边界。 |
| PI-295-R2 唯一阻断 finding 与 falsifier | [`production-implementation-pi-295-r2-track-source-amendment-acceptance.md`](production-implementation-pi-295-r2-track-source-amendment-acceptance.md:34) | 原缺陷是合法失败 binding 无法唯一推出 aggregate status；最小 falsifier 要求互斥、全覆盖、单值 status 表。 |
| amendment 作者不得自验 | [`production-implementation-pi-235-r1-track-source-state-clarification.md`](production-implementation-pi-235-r1-track-source-state-clarification.md:163) | closure mapping 仅用于定位整改，不构成独立 PASS。 |
| 总控授权边界 | [`production-implementation-control.md`](production-implementation-control.md:119) | 验收任务不得自行修复；未授权文件不得修改；阶段门须独立验收。 |
| 当前 G5/PI-500 边界 | [`production-implementation-control.md`](production-implementation-control.md:226) | 总控仍禁止实施代码、执行测试/YAML 和改变 production-default；本验收不得擅自更新总控状态。 |

## 3. PI-295-R2 `M-01 / CA-01` falsifier 独立复验

### 3.1 机械唯一性

aggregate 表先定义单一有序序列，再要求首命中停止。对任一输入组合，令 `P1..P4` 分别表示四行原始条件；实际命中条件机械等价于：

```text
R1 = P1
R2 = not P1 and P2
R3 = not P1 and not P2 and P3
R4 = not P1 and not P2 and not P3 and P4
```

因此 `R1..R4` 两两互斥。同一输入即使同时携带低优先级事实，也只能由最先成立的一行产生唯一 status；低优先级事实不能覆盖结果。该机制由 [`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:713) 和表头中的“均隐含未命中任何更高行”共同固定。

### 3.2 穷尽性

合法输入的结果空间按以下顺序闭合：

1. canonical 输入结构、身份、版本、契约或摘要无效，以及 integrity failure，进入 `INVALID`；
2. 结构与完整性有效但不能唯一消歧，进入 `AMBIGUOUS`；
3. 结构有效、无歧义但任一 required 条件不能满足，进入 `UNBOUND`；
4. 只有所有 required 条件均满足，且 N/A 仅出现在 protocol 明示允许处，进入 `BOUND`。

[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:722) 又明确禁止尚未证明第 4 行全部条件的合法输入默认成为 `BOUND`。因此不存在第五类悬空结果，也不存在合法失败 binding 在 `INVALID / AMBIGUOUS / UNBOUND` 之间任意选择的空间。

### 3.3 逐组合 aggregate status 验证矩阵

矩阵中的“其余有效”表示未出现更高优先级事实；叠加案例则显式验证高优先级覆盖。

| # | 输入组合 | 首个命中 | 唯一结果 | 裁决依据 | 结果 |
|---:|---|---:|---|---|---|
| 1 | required canonical input 缺失 | 1 | `track_match=UNKNOWN`（涉及 track binding 时）且 `INVALID` | 表第 1 行；truth table 无效输入行 | PASS |
| 2 | identity/schema/contract/digest 任一无效、不一致或不可解析 | 1 | `INVALID` | 表第 1 行 | PASS |
| 3 | source-side `INTEGRITY_FAILED` | 1 | `track_match=UNKNOWN + INVALID` | truth table 失败状态行；表第 1 行 | PASS |
| 4 | target-side `INTEGRITY_FAILED` | 1 | `track_match=UNKNOWN + INVALID` | truth table 失败状态行；表第 1 行 | PASS |
| 5 | 结构与完整性有效的 genuinely ambiguous canonical identity resolution | 2 | `AMBIGUOUS` | 表第 2 行 | PASS |
| 6 | source-side `AMBIGUOUS`，其余有效 | 2 | `track_match=UNKNOWN + AMBIGUOUS` | truth table；表第 2 行 | PASS |
| 7 | target-side `AMBIGUOUS`，其余有效 | 2 | `track_match=UNKNOWN + AMBIGUOUS` | truth table；表第 2 行 | PASS |
| 8 | 任一侧 `SOURCE_MISSING`，结构有效且无歧义 | 3 | `track_match=UNKNOWN + UNBOUND` | truth table；表第 3 行 | PASS |
| 9 | 任一侧 `UNPARSABLE`，结构有效且无歧义 | 3 | `track_match=UNKNOWN + UNBOUND` | truth table；表第 3 行 | PASS |
| 10 | 双方 `AVAILABLE_RESOLVED`，resolved track 不等 | 3 | `track_match=MISMATCH + UNBOUND` | truth table mismatch 行；表第 3 行 | PASS |
| 11 | 双方 resolved track `MATCH`，其他六维中任一 protocol-required 维度为 `UNKNOWN` | 3 | `UNBOUND` | 表第 3 行及穷尽说明 | PASS |
| 12 | 双方 resolved track `MATCH`，其他六维中任一 protocol-required 维度为 `MISMATCH` | 3 | `UNBOUND` | 表第 3 行及穷尽说明 | PASS |
| 13 | 双方 resolved track `MATCH`；其他 required 维度均 `MATCH`；仅 protocol 明示允许的维度为 `NOT_APPLICABLE`；最低条件全满足 | 4 | `BOUND` | 表第 4 行 | PASS |
| 14 | 非 protocol 明示允许的 required 维度被填为 `NOT_APPLICABLE` | 3 | `UNBOUND` | 未满足 required 条件；穷尽说明明确固定 `UNBOUND` | PASS |
| 15 | 双方 resolved track `MATCH`；全部 required dimensions、target、artifact、anchor 和最低条件满足 | 4 | `BOUND` | 表第 4 行及 production minimum | PASS |
| 16 | legacy submission 缺 required track source binding | 1 | `track_match=UNKNOWN + INVALID + not ELIGIBLE` | 表第 1 行；legacy fail-closed 条款 | PASS |
| 17 | `INTEGRITY_FAILED` 与 source/target ambiguity 同时存在 | 1 | `INVALID` | 严格优先级使第 1 行覆盖第 2 行 | PASS |
| 18 | canonical digest 无效与 `SOURCE_MISSING` 同时存在 | 1 | `INVALID` | 第 1 行覆盖第 3 行 | PASS |
| 19 | genuine ambiguity 与 resolved-track/required-dimension mismatch 同时存在 | 2 | `AMBIGUOUS` | 未命中 invalid 时，第 2 行覆盖第 3 行 | PASS |
| 20 | resolved track `MATCH`，但 required target/artifact/anchor 不足 | 3 | `UNBOUND` | 第 3 行覆盖潜在第 4 行 | PASS |

**矩阵结论：20 PASS / 0 BLOCKED。** 指定基础组合和优先级叠加组合均获得单值输出。`track_match=UNKNOWN` 在所有适用组合中都不能命中 `BOUND`，也不会自动产生 `ELIGIBLE`。

### 3.4 Falsifier 裁决

PI-295-R2 的最小 falsifier 要求事实源存在一张覆盖完整 binding、每种 `TrackSourceState` 与其他六维组合，并唯一输出 aggregate status 的互斥决策表（[`production-implementation-pi-295-r2-track-source-amendment-acceptance.md`](production-implementation-pi-295-r2-track-source-amendment-acceptance.md:50)）。PI-230 当前第 713–722 行已直接满足该条件：

- 每种来源失败状态均有固定类别；
- canonical 输入无效与合法多候选歧义明确分开；
- 其他六维 required `UNKNOWN/MISMATCH` 和 N/A 边界明确；
- 优先级、首命中、互斥与禁止 default `BOUND` 明确；
- legacy、`UNKNOWN` 与 learning fail-closed 明确。

因此，原 `M-01 / CA-01` 已被 canonical 事实源中的新表**证伪并关闭**。

## 4. PI-295-R2 先前 17 个 PASS 项静态回归复验

下表独立复验 PI-295-R2 原矩阵中除原第 9 项外的 17 个 PASS；不继承旧结论。

| 原编号 | 回归项 | 当前独立证据 | 结果 |
|---:|---|---|---|
| 1 | binding 字段均引用已定义 canonical types | PI-210 定义 `RunTrack`/digest；PI-230 第 620–637 行定义新增封闭类型和字段 | PASS |
| 2 | source/target 基数与引用可机械关联 | PI-230 第 671、698 行分别固定 submission 恰一 source binding 与 binding 恰一 source ref/target binding | PASS |
| 3 | 失败状态仍保留合法来源证据与 parser 审计引用 | PI-230 第 630–636、671 行要求 immutable evidence、versioned parser、version/digest | PASS |
| 4 | binding digest 与 versioned reference 的精确关系未弱化 | PI-230 第 671、698、708–709 行继续要求 identity/version/digest 精确引用，无效即 invalid | PASS |
| 5 | reason-code 值域与状态基数闭合 | PI-230 第 639–641、673 行固定四个 reason codes 及 resolved/failed 基数规则 | PASS |
| 6 | `track_match` truth table 完备互斥 | PI-230 第 700–711 行仍以双 resolved、任一失败、输入无效三类闭合 | PASS |
| 7 | 双方 `AVAILABLE_RESOLVED` 只能得到 `MATCH/MISMATCH` | PI-230 第 704–705 行未变 | PASS |
| 8 | 任一失败或 binding identity/version/digest 无效时为 `UNKNOWN` | PI-230 第 706–709 行未变；aggregate 新表只补 status，不改 match | PASS |
| 10 | `RunTrack` 仍非空且未新增 `UNKNOWN` | PI-210 第 99–105 行；PI-230 第 618、646 行 | PASS |
| 11 | source state 不依赖 anchor、item integrity 或自由文本 | PI-230 第 673、711 行继续明确禁止替代或提升 | PASS |
| 12 | 其他六维值域与独立计算不变 | PI-230 第 684–690、711、713 行；新表仅在七维独立算出后聚合 | PASS |
| 13 | `track_match=UNKNOWN` 不可自动 `ELIGIBLE` | PI-230 第 722、750 行明确禁止 | PASS |
| 14 | legacy 缺 required binding 固定 fail closed | PI-230 第 717、754 行固定 unknown + invalid + 不学习 | PASS |
| 15 | amendment 仍最小、通用、非 F09 专属 | canonical 增量只位于通用 FeedbackBinding/track source 契约；PI-235 第 135–145 行排除业务卡修改 | PASS |
| 16 | PI-220 六 gates、六 roles、五 actions 不变 | PI-220 第 90、239、348 行仍持有原接口；PI-230 第 943 行只引用 PI-220 输出、不生成业务状态 | PASS |
| 17 | F09/F08、F01–F12 冻结语义、rollout/default 不变 | PI-230 第 805–862、956–966 行保持 reference-only、字段保真和默认行为不变 | PASS |
| 18 | literal typed inputs 仍足以表达 `track_match=UNKNOWN` | PI-230 第 625–637、698–711 行提供双侧 canonical typed bindings 和确定性 truth table；仅属契约能力 | PASS |

**回归结论：17 PASS / 0 BLOCKED。** 未发现 schema/type、其他六维、PI-220、冻结卡语义、production-default 或实现授权边界的静态回归。

## 5. Findings

### 5.1 阻断 findings

无。

### 5.2 非阻断能力边界

| ID | Severity | 证据 | 影响 | 最小 falsifier / 关闭方式 |
|---|---|---|---|---|
| N-01 | Informational | 本任务仅获授权静态读取；PI-230 自身声明 card refs 不构成实现证明（[`production-implementation-pi-230-traceability-binding.md`](production-implementation-pi-230-traceability-binding.md:836)） | 本 PASS 不能外推为序列化、adapter、binder、测试或运行时正确 | 后续独立实现验收提供实际代码、测试及运行证据；不属于本 amendment 接受条件 |
| N-02 | Informational | PI-295-R2 已记录 PI-500 仍使用旧消费形状（[`production-implementation-pi-295-r2-track-source-amendment-acceptance.md`](production-implementation-pi-295-r2-track-source-amendment-acceptance.md:83)） | canonical 表达能力存在，不代表 PI-500 已正确消费 | 仅可由后续有界 PI-500 计划整改和独立复验关闭；本任务不授权修改 |

Informational 能力边界不属于 High、Medium、critical ambiguity、关键证据缺口或回归，不阻断本次纯静态 amendment acceptance。

## 6. 统计

| 类别 | 数量 | 门禁结果 |
|---|---:|---|
| High | 0 | 不阻断 |
| Medium | 0 | 不阻断 |
| Low | 0 | 不阻断 |
| Critical ambiguity | 0 | 不阻断 |
| Key evidence gap | 0 | 不阻断 |
| Canonical type conflict | 0 | 不阻断 |
| Frozen-semantics regression | 0 | 不阻断 |
| Production-default regression | 0 | 不阻断 |
| Other relevant regression | 0 | 不阻断 |
| Informational capability boundary | 2 | 非阻断 |
| Aggregate-status combinations | 20 PASS / 0 BLOCKED | 通过 |
| Prior PASS regression items | 17 PASS / 0 BLOCKED | 通过 |
| PI-295-R2 blocking root causes | 1 closed / 0 open | `M-01 / CA-01` 已关闭 |

## 7. 最终唯一裁决

# PASS

本裁决**仅接受 PI-230 track source state aggregate-status amendment 的静态契约整改**。canonical 表已机械唯一、穷尽、互斥，并严格按 `INVALID > AMBIGUOUS > UNBOUND > BOUND` 首命中；PI-295-R2 的 `M-01 / CA-01` falsifier 已真正成立，原阻断根因关闭；先前 17 个 PASS 项无静态回归。

本 `PASS` 明确：

- 不授权 PI-500 实现或计划修改；
- 不授权修改生产代码、测试、YAML、mapping、总控或 handoff；
- 不证明实现、测试、运行时接线、迁移或 rollout 正确；
- 不改变 production-default；
- 不代表 G5 完成；
- 不自动恢复、完成或通过任何上层阶段门。

## 8. 未执行声明

本任务未运行 Python、pytest、test collection、任何计划代码片段、YAML、mapping、Git 或其他实现验证命令；未执行序列化、adapter、binder、迁移、测试或 production 行为验证。除创建本验收记录外，未修改任何文件。

## 9. 唯一下一动作

**父实例独立核验后才可恢复 PI-570-R6。**
