# School Definition Audit

## 1. 审计范围与只读约束

本审计用于判定当前生产规则体系究竟更接近：

- A. Canon-Based System（经典驱动系统）
- B. School-Based Expert System（流派专家系统）

审计遵守以下约束：

- 只读审计，不修改 `theory/*`。
- 只读审计，不修改 `engine/*`。
- 只读审计，不修改 `META/project-state.json`。
- 本文件仅新增审计结论与治理建议。

## 2. 证据基线

本轮审计依据以下文件：

- [`META/canon-source-mapping-audit.md`](canon-source-mapping-audit.md)
- [`theory/ziping/index.yaml`](../theory/ziping/index.yaml)
- [`theory/tiaohou_ditiansui/index.yaml`](../theory/tiaohou_ditiansui/index.yaml)
- [`theory/SCHEMA.md`](../theory/SCHEMA.md)
- [`META/project-state.json`](project-state.json)

核心事实：

1. [`META/canon-source-mapping-audit.md`](canon-source-mapping-audit.md) 已完成生产规则 Canon 归属统计，合计审计生产规则 312 条。
2. [`theory/ziping/index.yaml`](../theory/ziping/index.yaml) 使用 `expert_system: ziping` 作为生产规则边界，内部规则来源覆盖《子平真诠》《三命通会》《穷通宝鉴》。
3. [`theory/tiaohou_ditiansui/index.yaml`](../theory/tiaohou_ditiansui/index.yaml) 使用 `expert_system: tiaohou_ditiansui` 作为生产规则边界，内部规则来源覆盖《滴天髓》《滴天髓阐微》。
4. [`theory/SCHEMA.md`](../theory/SCHEMA.md) 体现仓库早期以 school / theory 目录组织规则的治理传统。
5. [`META/project-state.json`](project-state.json) 显示 `V9_ziping_ditiansui_production_rules` 已 landed，说明该批生产规则已进入当前项目状态。

## 3. School × Canon 统计

| School | Canon List | Rule Count |
|---|---|---:|
| `ziping` | `ZIPING_ZHENQUAN`（《子平真诠》）: 18；`SANMING_TONGHUI`（《三命通会》）: 12；`QIONGTONG_BAOJIAN`（《穷通宝鉴》）: 27 | 57 |
| `tiaohou_ditiansui` | `DITIANSUI`（《滴天髓》）: 41；`DITIANSUI_CHANWEI`（《滴天髓阐微》）: 214 | 255 |

全量统计：

| Canon | Canon Name | School | Rule Count |
|---|---|---|---:|
| `ZIPING_ZHENQUAN` | 《子平真诠》 | `ziping` | 18 |
| `SANMING_TONGHUI` | 《三命通会》 | `ziping` | 12 |
| `QIONGTONG_BAOJIAN` | 《穷通宝鉴》 | `ziping` | 27 |
| `DITIANSUI` | 《滴天髓》 | `tiaohou_ditiansui` | 41 |
| `DITIANSUI_CHANWEI` | 《滴天髓阐微》 | `tiaohou_ditiansui` | 214 |

补充观察：

- `MIXED_SOURCE`: 0 条。
- `UNKNOWN`: 0 条。
- 单规则多经典引用：0 条。

这说明当前规则的 Canon 归属并不混乱；问题不在于单条规则不可归属，而在于生产系统的可执行边界已经不是单一 Canon，而是 School / Expert System。

## 4. 系统分类判断

结论：当前系统应判定为 **B. School-Based Expert System（流派专家系统）**，而不是狭义的 **A. Canon-Based System（经典驱动系统）**。

理由：

1. 当前生产规则文件的顶层边界是 `expert_system`，例如 `ziping` 与 `tiaohou_ditiansui`。
2. 每个 `expert_system` 内部可以容纳多个 Canon，且这些 Canon 已经实际进入同一生产规则集合。
3. Canon 在当前系统中的主要作用是来源追踪、证据归属、未来校准分层，而不是唯一的运行时组织边界。
4. 若将系统定义为 Canon-Based，会误判当前结构：因为 `ziping` 不等于《子平真诠》，`tiaohou_ditiansui` 也不等于单本《滴天髓》。

因此，当前系统的真实形态是：

> 以 School / Expert System 为生产规则边界，以 Canon 为内部来源归属与治理子层的双层结构雏形。

## 5. `ziping` 是否已演变为混合专家系统

判断：**YES**。

`ziping` 已经演变为由以下 Canon 共同构成的混合专家系统：

- 《子平真诠》：18 条规则。
- 《三命通会》：12 条规则。
- 《穷通宝鉴》：27 条规则。

合计：57 条规则。

这意味着 `ziping` 不应再被理解为单一《子平真诠》规则集，而应理解为“子平类专家系统”。其中：

- 《子平真诠》偏格局、用神、成败结构。
- 《三命通会》补充五行生克、支干源流、事件与结构判断。
- 《穷通宝鉴》提供调候、中和、五行偏枯与月令寒暖燥湿等原则。

因此，`ziping` 的治理单位应是 School，但其内部校准不能丢失 Canon 归属。

## 6. `tiaohou_ditiansui` 是否已演变为混合专家系统

判断：**YES**。

`tiaohou_ditiansui` 已经演变为由以下 Canon 共同构成的混合专家系统：

- 《滴天髓》：41 条规则。
- 《滴天髓阐微》：214 条规则。

合计：255 条规则。

这意味着 `tiaohou_ditiansui` 不应被理解为单本《滴天髓》的规则集，而应理解为“滴天髓—阐微调候专家系统”。其中：

- 《滴天髓》提供纲领性原则、结构判断、气势与中和框架。
- 《滴天髓阐微》提供大量阐释、细化、扩展与应用型规则。

因此，`tiaohou_ditiansui` 的生产边界是 School / Expert System，Canon 是其内部来源层。

## 7. 未来治理风险

### 7.1 Canon Drift

风险定义：同一 Canon 名下的规则在后续新增、反馈校准或人工修订中逐渐吸收其他 Canon 的逻辑，导致 Canon 标签失真。

当前风险等级：中。

原因：

- 当前无 `MIXED_SOURCE` 与 `UNKNOWN`，基础归属较干净。
- 但 `ziping` 和 `tiaohou_ditiansui` 都已是多 Canon 组合系统，后续新增规则若只按 School 追加，容易弱化 Canon 来源边界。

治理要求：

- 新增规则必须保留 `source.path`、`source.excerpt` 与 Canon 推断结果。
- Phase-300 校准结果不得只回写到 School 层，应可追踪到 Canon 层。

### 7.2 School Drift

风险定义：School / Expert System 边界持续扩大，逐渐变成“所有相近规则的收纳桶”，导致其方法论边界不清。

当前风险等级：中高。

原因：

- `ziping` 已包含三本经典，内部理论重心可能在格局、三命综合、调候原则之间移动。
- `tiaohou_ditiansui` 中《滴天髓阐微》规则数远高于《滴天髓》，长期可能使 School 语义偏向阐微解释体系，而非原始纲领体系。

治理要求：

- 每个 School 必须有明确的 Canon 组成清单。
- 当新增 Canon 超出既有 School 语义边界时，应触发 School Definition Review。
- School 级权重只适合表达专家系统整体表现，不适合替代 Canon 归因。

### 7.3 Rule Attribution Drift

风险定义：规则在抽取、合并、重写、校准、反馈闭环中逐渐失去可验证的来源归属，最终无法说明“此规则来自哪本经典、属于哪个 School、为何如此校准”。

当前风险等级：中。

原因：

- 当前规则归属较完整，但未来 Phase-300 若只按命中率调整权重，可能造成高绩效规则被跨层误归因。
- 若只保留 School 命中表现，会掩盖 Canon 内部差异。

治理要求：

- 保留 Rule → Canon → School 的链路。
- 校准记录必须同时记录 rule_id、canon、school。
- 反馈统计应允许按 Canon、School、Rule Family 三个维度切片。

## 8. Phase-300 校准模型评估

| 方案 | 判断 | 优点 | 缺点 |
|---|---|---|---|
| A. Canon Weight | 不建议单独采用 | 来源归属精细，能识别经典差异 | 忽略当前运行时以 `expert_system` / School 装载规则的事实；难以表达专家系统整体表现 |
| B. School Weight | 不建议单独采用 | 符合当前生产边界，便于工程加载与整体校准 | 会掩盖同一 School 内不同 Canon 的表现差异，放大 Canon Drift 与 Rule Attribution Drift |
| C. 双层结构（Canon → School） | 唯一推荐 | 同时保留来源精度与生产边界；可做 Canon 内校准、School 聚合、跨 School 对照 | 需要在校准数据结构中维护双层字段与聚合逻辑 |

## 9. 唯一推荐治理方案

唯一推荐：**C. 双层结构（Canon → School）**。

建议治理模型：

```text
Rule
  → Canon
    → School / Expert System
      → Runtime Evidence / Report / Feedback Calibration
```

落地原则：

1. Rule 是最小可校准单位。
2. Canon 是来源归属与细粒度权重层。
3. School 是专家系统边界、运行时加载边界与报告聚合边界。
4. Phase-300 应同时维护 Canon Weight 与 School Weight，但治理入口采用 Canon → School 双层结构。
5. 当 Canon 表现与 School 表现冲突时，应优先检查 Rule Family 与 Canon 分布，而不是直接整体升降 School 权重。

推荐权重聚合方向：

```text
rule_score
  → canon_weighted_score
  → school_aggregated_score
  → report_confidence / calibration_feedback
```

## 10. 最终 YES / NO

**YES**。

建议进入 **Canon→School 双层治理模型**。

最终判定：当前系统不是纯 Canon-Based System，而是 **School-Based Expert System**，并且已经具备明确的 Canon 子层。Phase-300 不应选择单层 Canon Weight 或单层 School Weight，而应采用 **Canon → School 双层结构** 作为唯一推荐治理方案。
