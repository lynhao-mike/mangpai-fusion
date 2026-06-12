# Phase-300 校准投票策略

## 1. 只读设计范围

本文件是 Phase-300 初始投票策略设计，基于 [`META/canon-school-governance-design.md`](canon-school-governance-design.md) 的 Canon → School 双层治理模型生成。

限制：本次只生成设计与可执行表格，不修改 [`theory/ziping/index.yaml`](../theory/ziping/index.yaml)、[`theory/tiaohou_ditiansui/index.yaml`](../theory/tiaohou_ditiansui/index.yaml)、`engine/*` 或 [`META/project-state.json`](project-state.json)，不创建新规则，不修改既有权重。

## 2. Phase-300 投票总链路

```text
Raw Rule Votes（原始触发，仅诊断）
  → Shared Evidence 降重（STRUCTURE / GENERAL_PRINCIPLE / ANTI_PATTERN 重复票降为证据票）
  → Family Vote（family-level 去重后的主票）
  → Canon Vote（5 个 Canon 初始 0.20/Canon）
  → School Vote（School lane 内归一化，ziping=0.50、tiaohou_ditiansui=0.50）
  → Phase-300 Calibration Outcome
```

## 3. 投票层级定义

| 投票层级 | 是否进入最终权重 | 定义 | Phase-300 用途 |
|---|---|---|---|
| Raw Rule Votes | 否 | 每条 triggered rule 原始计数 | 仅作诊断、活跃度与重复票监控 |
| Shared Evidence Votes | 辅助 | 重复 evidence key 合并后的证据票 | STRUCTURE / GENERAL_PRINCIPLE / ANTI_PATTERN 高重复票降重 |
| Family Vote | 是 | 同 case × family 内按 cap 压缩后的主票 | 主校准口径，先于 Canon Vote |
| Canon Vote | 是 | Canon 层按初始 0.20 权重聚合 family votes | 第一层权重校准 |
| School Vote | 是 | School lane 内归一化，初始 `ziping=0.50`、`tiaohou_ditiansui=0.50` | 第二层防压制融合 |

## 4. Canon → School 归一化公式

Family-level normalization 必须发生在 Canon Vote 前：

```text
family_vote(case, family) = min(raw_hits(case, family), family_cap[family])
canon_vote(case, canon) = canon_weight[canon] × sum(typed_family_vote(case, canon))
school_vote_in_canon(case, canon, school)
  = capped_vote(case, canon, school) / sum(capped_vote(case, canon, all_schools_in_canon))
school_lane_vote(case, school)
  = school_lane_prior[school] × normalize(sum(canon_vote(case, canon, school)))
```

当前每个 Canon 只映射到一个 School，因此 `school_vote_in_canon=1.00`；但仍保留公式，以兼容未来同 Canon 多 School 的情况。

## 5. 初始权重

| Canon | Rule Count | Phase-300 Canon Weight | School Composition |
|---|---:|---:|---|
| `DITIANSUI` | 41 | 0.20 | `tiaohou_ditiansui`: 41 |
| `DITIANSUI_CHANWEI` | 214 | 0.20 | `tiaohou_ditiansui`: 214 |
| `QIONGTONG_BAOJIAN` | 27 | 0.20 | `ziping`: 27 |
| `SANMING_TONGHUI` | 12 | 0.20 | `ziping`: 12 |
| `ZIPING_ZHENQUAN` | 18 | 0.20 | `ziping`: 18 |

| School | Rule Count | Phase-300 School Weight | 防压制说明 |
|---|---:|---:|---|
| `tiaohou_ditiansui` | 255 | 0.50 | 不按规则数量分配；lane 内归一化后参与融合 |
| `ziping` | 57 | 0.50 | 不按规则数量分配；lane 内归一化后参与融合 |

## 6. Family Cap

| 风险等级 | Cap | 说明 |
|---|---:|---|
| CRITICAL | 1 | 高重复、高放大风险 family，同 case 只允许 1 张 family 主票 |
| HIGH | 2 | 高频结构 family，最多保留 2 张主/辅混合票 |
| MEDIUM | 3 | 事件或解释细分 family，最多保留 3 张票 |

| Family ID | Risk | Family Cap | Shared Evidence Keys |
|---|---|---:|---|
| `FAM-001` | `HIGH` | 2 | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏 |
| `FAM-002` | `HIGH` | 2 | 月令, 旺衰, 旺相休囚 |
| `FAM-003` | `HIGH` | 2 | 旺衰 |
| `FAM-004` | `CRITICAL` | 1 | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节, 寒暖状态, 土燥土湿, 十干调候用神 |
| `FAM-005` | `HIGH` | 2 | 通关条件 |
| `FAM-006` | `HIGH` | 2 | - |
| `FAM-007` | `HIGH` | 2 | 有情无情 |
| `FAM-008` | `HIGH` | 2 | - |
| `FAM-009` | `MEDIUM` | 3 | - |
| `FAM-010` | `MEDIUM` | 3 | - |
| `FAM-011` | `CRITICAL` | 1 | 从格条件 |
| `FAM-012` | `HIGH` | 2 | - |
| `FAM-013` | `HIGH` | 2 | 月令, 旺衰, 旺相休囚 |
| `FAM-014` | `MEDIUM` | 3 | - |
| `FAM-015` | `MEDIUM` | 3 | - |
| `FAM-016` | `MEDIUM` | 3 | - |
| `FAM-017` | `MEDIUM` | 3 | 调候 |
| `FAM-018` | `HIGH` | 2 | 月令, 坎离升降 |
| `FAM-019` | `MEDIUM` | 3 | - |
| `FAM-020` | `MEDIUM` | 3 | 月令 |

## 7. Rule Type 投票策略

| Rule Type | Count | 主票 | 辅助票 | 解释票 | Phase-300 使用规则 |
|---|---:|---|---|---|---|
| `ANTI_PATTERN` | 18 | 否 | 是 | 是 | 降为 Shared Evidence / veto / 降权票；不作正向主票。 |
| `EVENT` | 73 | 是 | 是 | 是 | 事件落点主票；同 family 内仍先 cap，再进入 Canon Vote。 |
| `GENERAL_PRINCIPLE` | 55 | 否 | 是 | 是 | 降为 Shared Evidence / 辅助票；不直接形成主票。 |
| `STRUCTURE` | 147 | 有条件主票 | 是 | 是 | 先做 Shared Evidence 去重与 Family Cap；通过 cap 后进入 Canon Vote。 |
| `TIMING` | 19 | 有条件主票 | 是 | 是 | 应期票单独统计准确率；不与结构票混加。 |

Shared Evidence 规则：`STRUCTURE`、`GENERAL_PRINCIPLE`、`ANTI_PATTERN` 中使用同一 shared evidence key 的重复票，不得重复进入主票；应先降为 evidence feature，再由 family vote 消化。

## 8. DTS vs ZIPING 防压制机制

1. Canon Vote 前先执行 family-level normalization。
2. School Vote 在各自 School lane 内归一化。
3. `ziping` 与 `tiaohou_ditiansui` 初始 School Weight 均为 0.50，不按 57:255 的规则数量分配。
4. Raw Rule Votes 只用于诊断，不允许直接拉高 `tiaohou_ditiansui` 或压低 `ziping`。
5. 若 raw vote、family vote、canon vote、school vote 结论冲突，进入人工仲裁，不自动调权。

## 9. 312 条规则 Phase-300 投票策略表

| Rule ID | Canon | School | Family ID | Rule Type | Shared Evidence Keys | Family Cap | Phase-300 Canon Weight | Phase-300 School Weight | 投票层级说明 |
|---|---|---|---|---|---|---:|---:|---:|---|
| `DTS-PROD-20260605-001` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-003` | `EVENT` | 旺衰 | 2 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260605-002` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-006` | `GENERAL_PRINCIPLE` | - | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260605-003` | `DITIANSUI` | `tiaohou_ditiansui` | - | `ANTI_PATTERN` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Veto/降权辅助票 → Canon 风险层 |
| `DTS-PROD-20260605-004` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-003` | `STRUCTURE` | 旺衰 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260605-005` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-005` | `STRUCTURE` | 通关条件 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260605-006` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-002`, `FAM-013` | `STRUCTURE` | 月令, 旺衰, 旺相休囚 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260605-007` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-001` | `ANTI_PATTERN` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Veto/降权辅助票 → Canon 风险层 |
| `DTS-PROD-20260605-008` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-002` | `STRUCTURE` | 月令, 旺衰, 旺相休囚 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260605-009` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-005`, `FAM-020` | `STRUCTURE` | 通关条件, 月令 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260605-010` | `DITIANSUI` | `tiaohou_ditiansui` | - | `TIMING` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Timing Family Vote → Canon Timing Vote → School Timing Lane |
| `DTS-PROD-20260605-011` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-002`, `FAM-006` | `GENERAL_PRINCIPLE` | 月令, 旺衰, 旺相休囚 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260605-012` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-002`, `FAM-006` | `GENERAL_PRINCIPLE` | 月令, 旺衰, 旺相休囚 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260605-013` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-003`, `FAM-007` | `STRUCTURE` | 旺衰, 有情无情 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260605-014` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-001` | `STRUCTURE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260605-015` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-002`, `FAM-013` | `STRUCTURE` | 月令, 旺衰, 旺相休囚 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260605-016` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-005` | `STRUCTURE` | 通关条件 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260605-017` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260605-018` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-006` | `GENERAL_PRINCIPLE` | - | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260605-019` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-004` | `GENERAL_PRINCIPLE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-001` | `DITIANSUI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-002` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-003` | `DITIANSUI` | `tiaohou_ditiansui` | - | `ANTI_PATTERN` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Veto/降权辅助票 → Canon 风险层 |
| `DTS-PROD-20260606-004` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-005` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-006` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-007` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-008` | `DITIANSUI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-009` | `DITIANSUI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-010` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-011` | `DITIANSUI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-012` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-013` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-014` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-015` | `DITIANSUI` | `tiaohou_ditiansui` | - | `TIMING` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Timing Family Vote → Canon Timing Vote → School Timing Lane |
| `DTS-PROD-20260606-016` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-017` | `DITIANSUI` | `tiaohou_ditiansui` | - | `TIMING` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Timing Family Vote → Canon Timing Vote → School Timing Lane |
| `DTS-PROD-20260606-018` | `DITIANSUI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-019` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-020` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-021` | `DITIANSUI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-022` | `DITIANSUI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-023` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-024` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-025` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-026` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-027` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `ANTI_PATTERN` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Veto/降权辅助票 → Canon 风险层 |
| `DTS-PROD-20260606-028` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-029` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-030` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-031` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-032` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-033` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-034` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-035` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-036` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-037` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-038` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-039` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-040` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `ANTI_PATTERN` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Veto/降权辅助票 → Canon 风险层 |
| `DTS-PROD-20260606-041` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `TIMING` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Timing Family Vote → Canon Timing Vote → School Timing Lane |
| `DTS-PROD-20260606-042` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-043` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-044` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-045` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-046` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-047` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-048` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-049` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-050` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `ANTI_PATTERN` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Veto/降权辅助票 → Canon 风险层 |
| `DTS-PROD-20260606-051` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `ANTI_PATTERN` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Veto/降权辅助票 → Canon 风险层 |
| `DTS-PROD-20260606-052` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-053` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-054` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-055` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-056` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-057` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-001`, `FAM-002`, `FAM-013`, `FAM-020` | `STRUCTURE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏, 旺衰, 旺相休囚 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-058` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-059` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-002`, `FAM-013`, `FAM-020` | `STRUCTURE` | 月令, 旺衰, 旺相休囚 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-060` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-061` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-002`, `FAM-011` | `GENERAL_PRINCIPLE` | 月令, 旺衰, 旺相休囚, 从格条件 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-062` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-001`, `FAM-002`, `FAM-003` | `STRUCTURE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏, 旺衰, 旺相休囚 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-063` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-005` | `STRUCTURE` | 通关条件 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-064` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-005`, `FAM-010` | `TIMING` | 通关条件 | 2 | 0.20 | 0.50 | Raw 诊断 → Timing Family Vote → Canon Timing Vote → School Timing Lane |
| `DTS-PROD-20260606-065` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-005`, `FAM-010` | `STRUCTURE` | 通关条件 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-066` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-067` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `ANTI_PATTERN` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Veto/降权辅助票 → Canon 风险层 |
| `DTS-PROD-20260606-068` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-069` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-070` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-071` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-072` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-073` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-074` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-075` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-076` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-077` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-078` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-079` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-007`, `FAM-008` | `ANTI_PATTERN` | 有情无情 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Veto/降权辅助票 → Canon 风险层 |
| `DTS-PROD-20260606-080` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-007`, `FAM-008`, `FAM-015` | `TIMING` | 有情无情 | 2 | 0.20 | 0.50 | Raw 诊断 → Timing Family Vote → Canon Timing Vote → School Timing Lane |
| `DTS-PROD-20260606-081` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-008` | `EVENT` | - | 2 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-082` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-007`, `FAM-008` | `STRUCTURE` | 有情无情 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-083` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-084` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-019` | `TIMING` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Timing Family Vote → Canon Timing Vote → School Timing Lane |
| `DTS-PROD-20260606-085` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-019` | `STRUCTURE` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-086` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-019` | `STRUCTURE` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-087` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-010` | `EVENT` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-088` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-010` | `STRUCTURE` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-089` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-090` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-001`, `FAM-005` | `GENERAL_PRINCIPLE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏, 通关条件 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-091` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-005`, `FAM-015` | `GENERAL_PRINCIPLE` | 通关条件 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-092` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-093` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-004` | `STRUCTURE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-094` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-004`, `FAM-020` | `ANTI_PATTERN` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Veto/降权辅助票 → Canon 风险层 |
| `DTS-PROD-20260606-095` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-096` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-004` | `EVENT` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-097` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-004` | `STRUCTURE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-098` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-099` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-100` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-101` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-102` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-004`, `FAM-018` | `STRUCTURE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-103` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-004`, `FAM-018` | `GENERAL_PRINCIPLE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-104` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-018` | `GENERAL_PRINCIPLE` | 月令, 坎离升降 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-105` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-018` | `GENERAL_PRINCIPLE` | 月令, 坎离升降 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-106` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-107` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-108` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-004`, `FAM-018` | `STRUCTURE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-109` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-018` | `GENERAL_PRINCIPLE` | 月令, 坎离升降 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-110` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-111` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-112` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-113` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-004`, `FAM-018` | `TIMING` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Timing Family Vote → Canon Timing Vote → School Timing Lane |
| `DTS-PROD-20260606-114` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-115` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-116` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-117` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-118` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-119` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-120` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-121` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-122` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-123` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-124` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-125` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-126` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-127` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-128` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-129` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-130` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-131` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-132` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-133` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-134` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-135` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-136` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `ANTI_PATTERN` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Veto/降权辅助票 → Canon 风险层 |
| `DTS-PROD-20260606-137` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-138` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `TIMING` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Timing Family Vote → Canon Timing Vote → School Timing Lane |
| `DTS-PROD-20260606-139` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-140` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-141` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-142` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-143` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-144` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-145` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-146` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-147` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-148` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-149` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-150` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-151` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-152` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-153` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-154` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `TIMING` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Timing Family Vote → Canon Timing Vote → School Timing Lane |
| `DTS-PROD-20260606-155` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-156` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-157` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-158` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-159` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-160` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-161` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-162` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-163` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-164` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-165` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-166` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `TIMING` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Timing Family Vote → Canon Timing Vote → School Timing Lane |
| `DTS-PROD-20260606-167` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-168` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-006`, `FAM-012`, `FAM-015` | `STRUCTURE` | - | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-169` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-006`, `FAM-012` | `STRUCTURE` | - | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-170` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-006`, `FAM-012` | `EVENT` | - | 2 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-171` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `STRUCTURE` | 从格条件 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-172` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `STRUCTURE` | 从格条件 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-173` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `STRUCTURE` | 从格条件 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-174` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `STRUCTURE` | 从格条件 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-175` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `STRUCTURE` | 从格条件 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-176` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `STRUCTURE` | 从格条件 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-177` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `STRUCTURE` | 从格条件 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-178` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `EVENT` | 从格条件 | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-179` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `EVENT` | 从格条件 | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-180` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `EVENT` | 从格条件 | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-181` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-182` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-183` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-012`, `FAM-019` | `ANTI_PATTERN` | - | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Veto/降权辅助票 → Canon 风险层 |
| `DTS-PROD-20260606-184` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-012` | `STRUCTURE` | - | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-185` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-012` | `STRUCTURE` | - | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-186` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-012` | `STRUCTURE` | - | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-187` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-012` | `EVENT` | - | 2 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-188` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-012`, `FAM-019` | `STRUCTURE` | - | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-189` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-012` | `STRUCTURE` | - | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-190` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-191` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-192` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-193` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-194` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `TIMING` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Timing Family Vote → Canon Timing Vote → School Timing Lane |
| `DTS-PROD-20260606-195` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `STRUCTURE` | 从格条件 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-196` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `STRUCTURE` | 从格条件 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-197` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-198` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-199` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `TIMING` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Timing Family Vote → Canon Timing Vote → School Timing Lane |
| `DTS-PROD-20260606-200` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-014` | `STRUCTURE` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-201` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-014` | `STRUCTURE` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-202` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-014` | `STRUCTURE` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-203` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-014` | `EVENT` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-204` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-017` | `STRUCTURE` | 调候 | 3 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-205` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-017` | `STRUCTURE` | 调候 | 3 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-206` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-017` | `STRUCTURE` | 调候 | 3 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-207` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-208` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-209` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-210` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-211` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-212` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-213` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-003`, `FAM-016` | `EVENT` | 旺衰 | 2 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-214` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-016` | `STRUCTURE` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-215` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-016` | `GENERAL_PRINCIPLE` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-216` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-008`, `FAM-015` | `EVENT` | - | 2 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-217` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `TIMING` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Timing Family Vote → Canon Timing Vote → School Timing Lane |
| `DTS-PROD-20260606-218` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-015` | `EVENT` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-219` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-009` | `EVENT` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-220` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-009` | `TIMING` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Timing Family Vote → Canon Timing Vote → School Timing Lane |
| `DTS-PROD-20260606-221` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-009` | `EVENT` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-222` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-009`, `FAM-010` | `EVENT` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-223` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-009` | `STRUCTURE` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-224` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-010` | `STRUCTURE` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-225` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-226` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-227` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-228` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-229` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `TIMING` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Timing Family Vote → Canon Timing Vote → School Timing Lane |
| `DTS-PROD-20260606-230` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-231` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-232` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `DTS-PROD-20260606-233` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `TIMING` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Timing Family Vote → Canon Timing Vote → School Timing Lane |
| `DTS-PROD-20260606-234` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `ANTI_PATTERN` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Veto/降权辅助票 → Canon 风险层 |
| `DTS-PROD-20260606-235` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `DTS-PROD-20260606-236` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260605-001` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-001`, `FAM-003` | `EVENT` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏, 旺衰 | 2 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260605-002` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-009` | `ANTI_PATTERN` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Veto/降权辅助票 → Canon 风险层 |
| `ZP-PROD-20260605-003` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-001`, `FAM-013`, `FAM-020` | `STRUCTURE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏, 旺衰, 旺相休囚 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260605-004` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-002` | `STRUCTURE` | 月令, 旺衰, 旺相休囚 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260605-005` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-001`, `FAM-007`, `FAM-019` | `STRUCTURE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260605-006` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-001`, `FAM-006`, `FAM-019` | `ANTI_PATTERN` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Veto/降权辅助票 → Canon 风险层 |
| `ZP-PROD-20260605-007` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-007`, `FAM-008` | `EVENT` | 有情无情 | 2 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260605-008` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-001`, `FAM-005`, `FAM-007` | `STRUCTURE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏, 通关条件 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260605-009` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-003`, `FAM-004` | `STRUCTURE` | 旺衰, 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求 等 12 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260605-010` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-001`, `FAM-007` | `STRUCTURE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260605-011` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-007`, `FAM-008`, `FAM-009`, `FAM-010` | `STRUCTURE` | 有情无情 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260605-012` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-007`, `FAM-010` | `STRUCTURE` | 有情无情 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260605-013` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-009` | `STRUCTURE` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260605-014` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-011`, `FAM-012` | `STRUCTURE` | 从格条件 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260605-015` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-007`, `FAM-008` | `STRUCTURE` | 有情无情 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260605-016` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-015` | `TIMING` | - | 3 | 0.20 | 0.50 | Raw 诊断 → Timing Family Vote → Canon Timing Vote → School Timing Lane |
| `ZP-PROD-20260605-017` | `ZIPING_ZHENQUAN` | `ziping` | - | `ANTI_PATTERN` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Veto/降权辅助票 → Canon 风险层 |
| `ZP-PROD-20260605-018` | `ZIPING_ZHENQUAN` | `ziping` | - | `STRUCTURE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260606-001` | `SANMING_TONGHUI` | `ziping` | `FAM-005` | `STRUCTURE` | 通关条件 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260606-002` | `SANMING_TONGHUI` | `ziping` | `FAM-002`, `FAM-013`, `FAM-020` | `STRUCTURE` | 月令, 旺衰, 旺相休囚 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260606-003` | `SANMING_TONGHUI` | `ziping` | `FAM-005`, `FAM-006`, `FAM-012` | `STRUCTURE` | 通关条件 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260606-004` | `SANMING_TONGHUI` | `ziping` | `FAM-001`, `FAM-002`, `FAM-009`, `FAM-010` | `STRUCTURE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏, 旺衰, 旺相休囚 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260606-005` | `SANMING_TONGHUI` | `ziping` | `FAM-001`, `FAM-007`, `FAM-009` | `EVENT` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏 | 2 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260606-006` | `SANMING_TONGHUI` | `ziping` | `FAM-005`, `FAM-020` | `EVENT` | 通关条件, 月令 | 2 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260606-007` | `SANMING_TONGHUI` | `ziping` | `FAM-001` | `STRUCTURE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260606-008` | `SANMING_TONGHUI` | `ziping` | `FAM-020` | `EVENT` | 月令 | 3 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260606-009` | `SANMING_TONGHUI` | `ziping` | `FAM-006`, `FAM-009` | `ANTI_PATTERN` | - | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Veto/降权辅助票 → Canon 风险层 |
| `ZP-PROD-20260606-010` | `SANMING_TONGHUI` | `ziping` | `FAM-006`, `FAM-014` | `EVENT` | - | 2 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260606-011` | `SANMING_TONGHUI` | `ziping` | `FAM-006`, `FAM-014` | `TIMING` | - | 2 | 0.20 | 0.50 | Raw 诊断 → Timing Family Vote → Canon Timing Vote → School Timing Lane |
| `ZP-PROD-20260606-012` | `SANMING_TONGHUI` | `ziping` | `FAM-006`, `FAM-014` | `EVENT` | - | 2 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260606-013` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-002`, `FAM-003`, `FAM-010`, `FAM-016` | `STRUCTURE` | 月令, 旺衰, 旺相休囚 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260606-014` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-005` | `EVENT` | 通关条件 | 2 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260606-015` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-005` | `GENERAL_PRINCIPLE` | 通关条件 | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `ZP-PROD-20260606-016` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-006`, `FAM-015` | `GENERAL_PRINCIPLE` | - | 2 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `ZP-PROD-20260606-017` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-004`, `FAM-013`, `FAM-018` | `EVENT` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 13 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260606-018` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-004`, `FAM-013` | `EVENT` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 13 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260606-019` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-004`, `FAM-013`, `FAM-018` | `STRUCTURE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 13 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260606-020` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-004` | `GENERAL_PRINCIPLE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `ZP-PROD-20260606-021` | `QIONGTONG_BAOJIAN` | `ziping` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `ZP-PROD-20260606-022` | `QIONGTONG_BAOJIAN` | `ziping` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `ZP-PROD-20260606-023` | `QIONGTONG_BAOJIAN` | `ziping` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `ZP-PROD-20260606-024` | `QIONGTONG_BAOJIAN` | `ziping` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `ZP-PROD-20260606-025` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-003`, `FAM-004`, `FAM-016`, `FAM-017` | `STRUCTURE` | 旺衰, 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求 等 12 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260606-026` | `QIONGTONG_BAOJIAN` | `ziping` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `ZP-PROD-20260606-027` | `QIONGTONG_BAOJIAN` | `ziping` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `ZP-PROD-20260606-028` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-004`, `FAM-018` | `GENERAL_PRINCIPLE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `ZP-PROD-20260606-029` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-004` | `GENERAL_PRINCIPLE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `ZP-PROD-20260606-030` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-004` | `GENERAL_PRINCIPLE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `ZP-PROD-20260606-031` | `QIONGTONG_BAOJIAN` | `ziping` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `ZP-PROD-20260606-032` | `QIONGTONG_BAOJIAN` | `ziping` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `ZP-PROD-20260606-033` | `QIONGTONG_BAOJIAN` | `ziping` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `ZP-PROD-20260606-034` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-001`, `FAM-004`, `FAM-013`, `FAM-018` | `STRUCTURE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏, 调候, 坎离升降 等 18 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Family Vote → Canon Vote → School Vote |
| `ZP-PROD-20260606-035` | `QIONGTONG_BAOJIAN` | `ziping` | - | `GENERAL_PRINCIPLE` | - | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `ZP-PROD-20260606-036` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-004` | `GENERAL_PRINCIPLE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `ZP-PROD-20260606-037` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-004`, `FAM-005`, `FAM-017` | `GENERAL_PRINCIPLE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 12 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |
| `ZP-PROD-20260606-038` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-001`, `FAM-004`, `FAM-013`, `FAM-018` | `ANTI_PATTERN` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏, 调候, 坎离升降 等 18 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → Veto/降权辅助票 → Canon 风险层 |
| `ZP-PROD-20260606-039` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-001`, `FAM-004`, `FAM-013` | `GENERAL_PRINCIPLE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏, 调候, 坎离升降 等 18 项 | 1 | 0.20 | 0.50 | Raw 诊断 → Shared Evidence → 辅助 Family Vote → Canon 辅助权重 |

## 10. 最终执行口径

Phase-300 初始投票策略固定为：Raw Rule Votes 只诊断；Family Vote 是主票入口；Canon Vote 采用 0.20/Canon 初始权重；School Vote 在 lane 内归一化并采用 `ziping=0.50`、`tiaohou_ditiansui=0.50` 初始先验；Family Cap、Shared Evidence 与 Rule Type 策略必须全部保留。
