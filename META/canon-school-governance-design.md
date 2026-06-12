# Canon → School 双层治理设计

## 1. 只读设计范围

本文件为 Phase-300 只读治理设计与可执行规范，承接 [`META/school-definition-audit.md`](school-definition-audit.md) 的结论：当前系统应以 School-Based Expert System 为生产边界，并以 Canon 作为来源归属与校准子层。

本设计不修改 [`theory/ziping/index.yaml`](../theory/ziping/index.yaml)、[`theory/tiaohou_ditiansui/index.yaml`](../theory/tiaohou_ditiansui/index.yaml)、`engine/*`、[`META/project-state.json`](project-state.json)，不自动修复规则、Schema 或权重。

## 2. 唯一推荐方案

唯一推荐：**Canon → School 双层投票与权重治理模型**。

```text
Rule Hit
  → Shared Evidence Key 去重
  → Family Cap 压缩
  → Rule Type 策略分流
  → Canon Layer 等权聚合
  → Canon 内 School Vote 归一化
  → School Lane 防压制融合
  → Phase-300 Calibration Record
```

核心原则：Rule 是最小命中单位，Canon 是第一层来源权重单位，School 是第二层运行与融合边界；最终学习不得直接使用 raw rule count 或 raw hit count。

## 3. Phase-300 投票层级

| 层级 | 输入 | 输出 | 护栏 |
|---|---|---|---|
| Rule Hit | 单条规则触发 | `rule_vote_raw` | 只做诊断，不直接进入最终权重 |
| Shared Evidence | 同一证据键多规则复用 | `evidence_feature` | 同 key 先合并，禁止重复放大 |
| Family Cap | 同 case × family 多规则命中 | `family_vote` | CRITICAL=1、HIGH=2、MEDIUM=3 |
| Rule Type | family vote | `typed_vote` | STRUCTURE / EVENT / GENERAL_PRINCIPLE / TIMING / ANTI_PATTERN 分策略 |
| Canon Layer | Canon 内 typed votes | `canon_vote` | 当前 5 个 Canon 初始等权 |
| School Layer | Canon 内 School votes | `school_vote_in_canon` | 当前单 School=1.00；未来多 School 按 capped vote 归一化 |
| Fusion Layer | Canon vote + School lane | `final_governance_vote` | School lane 归一化，防止 DTS / ZIPING 相互压制 |

## 4. 初始权重分布

### 4.1 Canon 初始权重

当前有效 Canon 为 5 个，初始均等：每个 Canon = **0.20**。

| Canon | Rule Count | Initial Canon Weight | Canon 内 School Composition |
|---|---:|---:|---|
| `DITIANSUI` | 41 | 0.20 | `tiaohou_ditiansui`: 41 |
| `DITIANSUI_CHANWEI` | 214 | 0.20 | `tiaohou_ditiansui`: 214 |
| `QIONGTONG_BAOJIAN` | 27 | 0.20 | `ziping`: 27 |
| `SANMING_TONGHUI` | 12 | 0.20 | `ziping`: 12 |
| `ZIPING_ZHENQUAN` | 18 | 0.20 | `ziping`: 18 |

### 4.2 School Lane 初始先验

School lane 初始先验不按规则数量分配，采用等权防压制：`ziping=0.50`，`tiaohou_ditiansui=0.50`。

| School | Rule Count | Initial School Lane Prior |
|---|---:|---:|
| `tiaohou_ditiansui` | 255 | 0.50 |
| `ziping` | 57 | 0.50 |

### 4.3 Canon 内 School 归一化

```text
school_vote_in_canon(c, s)
  = capped_vote(c, s) / sum(capped_vote(c, all_schools_in_canon))
```

当前每个 Canon 只对应一个 School，因此治理表中的初始 School Weight 均为 1.00。未来若同一 Canon 被多个 School 共同引用，则按同 case 内 family-capped vote 归一化；无命中时回退为该 Canon 内 School 均等先验。

## 5. Rule Type 投票策略

| Rule Type | Rule Count | Phase-300 策略 |
|---|---:|---|
| `ANTI_PATTERN` | 18 | 不作正向主票；作为 veto、降权或风险提示。 |
| `EVENT` | 73 | 主票核心；同 family 内仍需 cap。 |
| `GENERAL_PRINCIPLE` | 55 | 不直接进主票；作为辅助票、解释框架与有限学习。 |
| `STRUCTURE` | 147 | 有条件主票；必须先做 Shared Evidence 去重与 Family Cap。 |
| `TIMING` | 19 | 应期票单独学习；不与结构主票混加。 |

## 6. Family Cap 与 Shared Evidence Keys

| Family ID | Family Cap | Shared Evidence Keys |
|---|---:|---|
| `FAM-001` | 2 | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏 |
| `FAM-002` | 2 | 月令, 旺衰, 旺相休囚 |
| `FAM-003` | 2 | 旺衰 |
| `FAM-004` | 1 | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节, 寒暖状态, 土燥土湿, 十干调候用神 |
| `FAM-005` | 2 | 通关条件 |
| `FAM-006` | 2 | - |
| `FAM-007` | 2 | 有情无情 |
| `FAM-008` | 2 | - |
| `FAM-009` | 3 | - |
| `FAM-010` | 3 | - |
| `FAM-011` | 1 | 从格条件 |
| `FAM-012` | 2 | - |
| `FAM-013` | 2 | 月令, 旺衰, 旺相休囚 |
| `FAM-014` | 3 | - |
| `FAM-015` | 3 | - |
| `FAM-016` | 3 | - |
| `FAM-017` | 3 | 调候 |
| `FAM-018` | 2 | 月令, 坎离升降 |
| `FAM-019` | 3 | - |
| `FAM-020` | 3 | 月令 |

执行规则：同 case × same family 先压缩为 family vote；多 family 规则取最严格 cap；无 family 的规则作为 singleton vote，单 case 内最大贡献为 1；Shared Evidence Key 先生成 evidence feature，再被 family vote 消化。

## 7. DTS / ZIPING 防相互压制

1. raw rule count 与 raw hit count 只做诊断，不进入最终权重。
2. Canon 初始等权，5 个 Canon 各 0.20。
3. School lane 初始等权，`ziping=0.50`、`tiaohou_ditiansui=0.50`。
4. 每个 School 先在自身 lane 内完成 Shared Evidence 去重、Family Cap 与 Rule Type 策略，再进入融合层。
5. `DITIANSUI_CHANWEI` 规则数 214 不得天然压制 `ZIPING_ZHENQUAN` 18、`SANMING_TONGHUI` 12 或 `QIONGTONG_BAOJIAN` 27。

```text
final_vote(case)
  = normalize_by_school_lane(
      sum_over_canons(
        canon_weight[c]
        × school_vote_in_canon[c,s]
        × family_capped_rule_type_vote[c,s]
```

## 8. Rule × Canon × School 治理表

| Rule ID | Canon | School | Family ID | Rule Type | Shared Evidence Keys | 初始 Canon Weight | 初始 School Weight | Family Cap |
|---|---|---|---|---|---|---:|---:|---|
| `DTS-PROD-20260605-001` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-003` | `EVENT` | 旺衰 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260605-002` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-006` | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260605-003` | `DITIANSUI` | `tiaohou_ditiansui` | - | `ANTI_PATTERN` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260605-004` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-003` | `STRUCTURE` | 旺衰 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260605-005` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-005` | `STRUCTURE` | 通关条件 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260605-006` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-002`, `FAM-013` | `STRUCTURE` | 月令, 旺衰, 旺相休囚 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260605-007` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-001` | `ANTI_PATTERN` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260605-008` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-002` | `STRUCTURE` | 月令, 旺衰, 旺相休囚 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260605-009` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-005`, `FAM-020` | `STRUCTURE` | 通关条件, 月令 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260605-010` | `DITIANSUI` | `tiaohou_ditiansui` | - | `TIMING` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260605-011` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-002`, `FAM-006` | `GENERAL_PRINCIPLE` | 月令, 旺衰, 旺相休囚 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260605-012` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-002`, `FAM-006` | `GENERAL_PRINCIPLE` | 月令, 旺衰, 旺相休囚 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260605-013` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-003`, `FAM-007` | `STRUCTURE` | 旺衰, 有情无情 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260605-014` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-001` | `STRUCTURE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260605-015` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-002`, `FAM-013` | `STRUCTURE` | 月令, 旺衰, 旺相休囚 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260605-016` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-005` | `STRUCTURE` | 通关条件 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260605-017` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260605-018` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-006` | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260605-019` | `DITIANSUI` | `tiaohou_ditiansui` | `FAM-004` | `GENERAL_PRINCIPLE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-001` | `DITIANSUI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-002` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-003` | `DITIANSUI` | `tiaohou_ditiansui` | - | `ANTI_PATTERN` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-004` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-005` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-006` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-007` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-008` | `DITIANSUI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-009` | `DITIANSUI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-010` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-011` | `DITIANSUI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-012` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-013` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-014` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-015` | `DITIANSUI` | `tiaohou_ditiansui` | - | `TIMING` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-016` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-017` | `DITIANSUI` | `tiaohou_ditiansui` | - | `TIMING` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-018` | `DITIANSUI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-019` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-020` | `DITIANSUI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-021` | `DITIANSUI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-022` | `DITIANSUI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-023` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-024` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-025` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-026` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-027` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `ANTI_PATTERN` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-028` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-029` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-030` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-031` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-032` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-033` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-034` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-035` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-036` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-037` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-038` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-039` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-040` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `ANTI_PATTERN` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-041` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `TIMING` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-042` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-043` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-044` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-045` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-046` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-047` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-048` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-049` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-050` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `ANTI_PATTERN` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-051` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `ANTI_PATTERN` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-052` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-053` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-054` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-055` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-056` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-057` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-001`, `FAM-002`, `FAM-013`, `FAM-020` | `STRUCTURE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏, 旺衰, 旺相休囚 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-058` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-059` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-002`, `FAM-013`, `FAM-020` | `STRUCTURE` | 月令, 旺衰, 旺相休囚 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-060` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-061` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-002`, `FAM-011` | `GENERAL_PRINCIPLE` | 月令, 旺衰, 旺相休囚, 从格条件 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-062` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-001`, `FAM-002`, `FAM-003` | `STRUCTURE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏, 旺衰, 旺相休囚 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-063` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-005` | `STRUCTURE` | 通关条件 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-064` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-005`, `FAM-010` | `TIMING` | 通关条件 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-065` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-005`, `FAM-010` | `STRUCTURE` | 通关条件 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-066` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-067` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `ANTI_PATTERN` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-068` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-069` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-070` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-071` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-072` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-073` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-074` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-075` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-076` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-077` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-078` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-079` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-007`, `FAM-008` | `ANTI_PATTERN` | 有情无情 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-080` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-007`, `FAM-008`, `FAM-015` | `TIMING` | 有情无情 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-081` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-008` | `EVENT` | - | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-082` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-007`, `FAM-008` | `STRUCTURE` | 有情无情 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-083` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-084` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-019` | `TIMING` | - | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-085` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-019` | `STRUCTURE` | - | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-086` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-019` | `STRUCTURE` | - | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-087` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-010` | `EVENT` | - | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-088` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-010` | `STRUCTURE` | - | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-089` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-090` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-001`, `FAM-005` | `GENERAL_PRINCIPLE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏, 通关条件 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-091` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-005`, `FAM-015` | `GENERAL_PRINCIPLE` | 通关条件 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-092` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-093` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-004` | `STRUCTURE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-094` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-004`, `FAM-020` | `ANTI_PATTERN` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-095` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-096` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-004` | `EVENT` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-097` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-004` | `STRUCTURE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-098` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-099` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-100` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-101` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-102` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-004`, `FAM-018` | `STRUCTURE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-103` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-004`, `FAM-018` | `GENERAL_PRINCIPLE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-104` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-018` | `GENERAL_PRINCIPLE` | 月令, 坎离升降 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-105` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-018` | `GENERAL_PRINCIPLE` | 月令, 坎离升降 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-106` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-107` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-108` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-004`, `FAM-018` | `STRUCTURE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-109` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-018` | `GENERAL_PRINCIPLE` | 月令, 坎离升降 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-110` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-111` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-112` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-113` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-004`, `FAM-018` | `TIMING` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-114` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-115` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-116` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-117` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-118` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-119` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-120` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-121` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-122` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-123` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-124` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-125` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-126` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-127` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-128` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-129` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-130` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-131` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-132` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-133` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-134` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-135` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-136` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `ANTI_PATTERN` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-137` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-138` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `TIMING` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-139` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-140` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-141` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-142` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-143` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-144` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-145` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-146` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-147` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-148` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-149` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-150` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-151` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-152` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-153` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-154` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `TIMING` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-155` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-156` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-157` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-158` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-159` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-160` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-161` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-162` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-163` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-164` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-165` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-166` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `TIMING` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-167` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-168` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-006`, `FAM-012`, `FAM-015` | `STRUCTURE` | - | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-169` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-006`, `FAM-012` | `STRUCTURE` | - | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-170` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-006`, `FAM-012` | `EVENT` | - | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-171` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `STRUCTURE` | 从格条件 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-172` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `STRUCTURE` | 从格条件 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-173` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `STRUCTURE` | 从格条件 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-174` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `STRUCTURE` | 从格条件 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-175` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `STRUCTURE` | 从格条件 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-176` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `STRUCTURE` | 从格条件 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-177` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `STRUCTURE` | 从格条件 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-178` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `EVENT` | 从格条件 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-179` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `EVENT` | 从格条件 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-180` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `EVENT` | 从格条件 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-181` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-182` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-183` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-012`, `FAM-019` | `ANTI_PATTERN` | - | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-184` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-012` | `STRUCTURE` | - | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-185` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-012` | `STRUCTURE` | - | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-186` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-012` | `STRUCTURE` | - | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-187` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-012` | `EVENT` | - | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-188` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-012`, `FAM-019` | `STRUCTURE` | - | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-189` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-012` | `STRUCTURE` | - | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-190` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-191` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-192` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-193` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-194` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `TIMING` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-195` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `STRUCTURE` | 从格条件 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-196` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-011` | `STRUCTURE` | 从格条件 | 0.20 | 1.00 | 1 |
| `DTS-PROD-20260606-197` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-198` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-199` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `TIMING` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-200` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-014` | `STRUCTURE` | - | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-201` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-014` | `STRUCTURE` | - | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-202` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-014` | `STRUCTURE` | - | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-203` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-014` | `EVENT` | - | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-204` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-017` | `STRUCTURE` | 调候 | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-205` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-017` | `STRUCTURE` | 调候 | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-206` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-017` | `STRUCTURE` | 调候 | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-207` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-208` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-209` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-210` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-211` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-212` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-213` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-003`, `FAM-016` | `EVENT` | 旺衰 | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-214` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-016` | `STRUCTURE` | - | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-215` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-016` | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-216` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-008`, `FAM-015` | `EVENT` | - | 0.20 | 1.00 | 2 |
| `DTS-PROD-20260606-217` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `TIMING` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-218` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-015` | `EVENT` | - | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-219` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-009` | `EVENT` | - | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-220` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-009` | `TIMING` | - | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-221` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-009` | `EVENT` | - | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-222` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-009`, `FAM-010` | `EVENT` | - | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-223` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-009` | `STRUCTURE` | - | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-224` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | `FAM-010` | `STRUCTURE` | - | 0.20 | 1.00 | 3 |
| `DTS-PROD-20260606-225` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-226` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-227` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-228` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-229` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `TIMING` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-230` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-231` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-232` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-233` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `TIMING` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-234` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `ANTI_PATTERN` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-235` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `DTS-PROD-20260606-236` | `DITIANSUI_CHANWEI` | `tiaohou_ditiansui` | - | `EVENT` | - | 0.20 | 1.00 | 1（singleton） |
| `ZP-PROD-20260605-001` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-001`, `FAM-003` | `EVENT` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏, 旺衰 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260605-002` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-009` | `ANTI_PATTERN` | - | 0.20 | 1.00 | 3 |
| `ZP-PROD-20260605-003` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-001`, `FAM-013`, `FAM-020` | `STRUCTURE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏, 旺衰, 旺相休囚 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260605-004` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-002` | `STRUCTURE` | 月令, 旺衰, 旺相休囚 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260605-005` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-001`, `FAM-007`, `FAM-019` | `STRUCTURE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260605-006` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-001`, `FAM-006`, `FAM-019` | `ANTI_PATTERN` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260605-007` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-007`, `FAM-008` | `EVENT` | 有情无情 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260605-008` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-001`, `FAM-005`, `FAM-007` | `STRUCTURE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏, 通关条件 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260605-009` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-003`, `FAM-004` | `STRUCTURE` | 旺衰, 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求 等 12 项 | 0.20 | 1.00 | 1 |
| `ZP-PROD-20260605-010` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-001`, `FAM-007` | `STRUCTURE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260605-011` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-007`, `FAM-008`, `FAM-009`, `FAM-010` | `STRUCTURE` | 有情无情 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260605-012` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-007`, `FAM-010` | `STRUCTURE` | 有情无情 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260605-013` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-009` | `STRUCTURE` | - | 0.20 | 1.00 | 3 |
| `ZP-PROD-20260605-014` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-011`, `FAM-012` | `STRUCTURE` | 从格条件 | 0.20 | 1.00 | 1 |
| `ZP-PROD-20260605-015` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-007`, `FAM-008` | `STRUCTURE` | 有情无情 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260605-016` | `ZIPING_ZHENQUAN` | `ziping` | `FAM-015` | `TIMING` | - | 0.20 | 1.00 | 3 |
| `ZP-PROD-20260605-017` | `ZIPING_ZHENQUAN` | `ziping` | - | `ANTI_PATTERN` | - | 0.20 | 1.00 | 1（singleton） |
| `ZP-PROD-20260605-018` | `ZIPING_ZHENQUAN` | `ziping` | - | `STRUCTURE` | - | 0.20 | 1.00 | 1（singleton） |
| `ZP-PROD-20260606-001` | `SANMING_TONGHUI` | `ziping` | `FAM-005` | `STRUCTURE` | 通关条件 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260606-002` | `SANMING_TONGHUI` | `ziping` | `FAM-002`, `FAM-013`, `FAM-020` | `STRUCTURE` | 月令, 旺衰, 旺相休囚 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260606-003` | `SANMING_TONGHUI` | `ziping` | `FAM-005`, `FAM-006`, `FAM-012` | `STRUCTURE` | 通关条件 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260606-004` | `SANMING_TONGHUI` | `ziping` | `FAM-001`, `FAM-002`, `FAM-009`, `FAM-010` | `STRUCTURE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏, 旺衰, 旺相休囚 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260606-005` | `SANMING_TONGHUI` | `ziping` | `FAM-001`, `FAM-007`, `FAM-009` | `EVENT` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260606-006` | `SANMING_TONGHUI` | `ziping` | `FAM-005`, `FAM-020` | `EVENT` | 通关条件, 月令 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260606-007` | `SANMING_TONGHUI` | `ziping` | `FAM-001` | `STRUCTURE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260606-008` | `SANMING_TONGHUI` | `ziping` | `FAM-020` | `EVENT` | 月令 | 0.20 | 1.00 | 3 |
| `ZP-PROD-20260606-009` | `SANMING_TONGHUI` | `ziping` | `FAM-006`, `FAM-009` | `ANTI_PATTERN` | - | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260606-010` | `SANMING_TONGHUI` | `ziping` | `FAM-006`, `FAM-014` | `EVENT` | - | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260606-011` | `SANMING_TONGHUI` | `ziping` | `FAM-006`, `FAM-014` | `TIMING` | - | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260606-012` | `SANMING_TONGHUI` | `ziping` | `FAM-006`, `FAM-014` | `EVENT` | - | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260606-013` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-002`, `FAM-003`, `FAM-010`, `FAM-016` | `STRUCTURE` | 月令, 旺衰, 旺相休囚 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260606-014` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-005` | `EVENT` | 通关条件 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260606-015` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-005` | `GENERAL_PRINCIPLE` | 通关条件 | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260606-016` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-006`, `FAM-015` | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 2 |
| `ZP-PROD-20260606-017` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-004`, `FAM-013`, `FAM-018` | `EVENT` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 13 项 | 0.20 | 1.00 | 1 |
| `ZP-PROD-20260606-018` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-004`, `FAM-013` | `EVENT` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 13 项 | 0.20 | 1.00 | 1 |
| `ZP-PROD-20260606-019` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-004`, `FAM-013`, `FAM-018` | `STRUCTURE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 13 项 | 0.20 | 1.00 | 1 |
| `ZP-PROD-20260606-020` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-004` | `GENERAL_PRINCIPLE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 0.20 | 1.00 | 1 |
| `ZP-PROD-20260606-021` | `QIONGTONG_BAOJIAN` | `ziping` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `ZP-PROD-20260606-022` | `QIONGTONG_BAOJIAN` | `ziping` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `ZP-PROD-20260606-023` | `QIONGTONG_BAOJIAN` | `ziping` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `ZP-PROD-20260606-024` | `QIONGTONG_BAOJIAN` | `ziping` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `ZP-PROD-20260606-025` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-003`, `FAM-004`, `FAM-016`, `FAM-017` | `STRUCTURE` | 旺衰, 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求 等 12 项 | 0.20 | 1.00 | 1 |
| `ZP-PROD-20260606-026` | `QIONGTONG_BAOJIAN` | `ziping` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `ZP-PROD-20260606-027` | `QIONGTONG_BAOJIAN` | `ziping` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `ZP-PROD-20260606-028` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-004`, `FAM-018` | `GENERAL_PRINCIPLE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 0.20 | 1.00 | 1 |
| `ZP-PROD-20260606-029` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-004` | `GENERAL_PRINCIPLE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 0.20 | 1.00 | 1 |
| `ZP-PROD-20260606-030` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-004` | `GENERAL_PRINCIPLE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 0.20 | 1.00 | 1 |
| `ZP-PROD-20260606-031` | `QIONGTONG_BAOJIAN` | `ziping` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `ZP-PROD-20260606-032` | `QIONGTONG_BAOJIAN` | `ziping` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `ZP-PROD-20260606-033` | `QIONGTONG_BAOJIAN` | `ziping` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `ZP-PROD-20260606-034` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-001`, `FAM-004`, `FAM-013`, `FAM-018` | `STRUCTURE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏, 调候, 坎离升降 等 18 项 | 0.20 | 1.00 | 1 |
| `ZP-PROD-20260606-035` | `QIONGTONG_BAOJIAN` | `ziping` | - | `GENERAL_PRINCIPLE` | - | 0.20 | 1.00 | 1（singleton） |
| `ZP-PROD-20260606-036` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-004` | `GENERAL_PRINCIPLE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 11 项 | 0.20 | 1.00 | 1 |
| `ZP-PROD-20260606-037` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-004`, `FAM-005`, `FAM-017` | `GENERAL_PRINCIPLE` | 月令, 调候, 坎离升降, 震兑调济, 燥湿状态, 火暖需求, 水润需求, 月令季节 等 12 项 | 0.20 | 1.00 | 1 |
| `ZP-PROD-20260606-038` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-001`, `FAM-004`, `FAM-013`, `FAM-018` | `ANTI_PATTERN` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏, 调候, 坎离升降 等 18 项 | 0.20 | 1.00 | 1 |
| `ZP-PROD-20260606-039` | `QIONGTONG_BAOJIAN` | `ziping` | `FAM-001`, `FAM-004`, `FAM-013` | `GENERAL_PRINCIPLE` | 月令, 有情无情, 跨类别取用, 相神护卫, 喜忌取裁, yongshen来源_月令透藏, 调候, 坎离升降 等 18 项 | 0.20 | 1.00 | 1 |

## 9. Phase-300 校准记录字段

Phase-300 每条校准记录至少保留：`case_id`、`rule_id`、`canon`、`school`、`family_ids`、`rule_type`、`shared_evidence_keys`、`raw_hit`、`family_capped_vote`、`canon_weight_before`、`school_weight_in_canon_before`、`school_lane_prior_before`、`calibration_outcome`、`learning_scope`。

## 10. 最终结论

Phase-300 唯一推荐采用 **Canon → School 双层治理模型**：Canon 层 5 个有效 Canon 初始均等 0.20；Canon 内 School 当前均为 1.00；School lane 以 `ziping=0.50`、`tiaohou_ditiansui=0.50` 防止 DTS / ZIPING 相互压制；Family Cap、Shared Evidence Keys 与 Rule Type 策略全部保留。
