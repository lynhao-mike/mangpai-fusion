# P4-4A Mapping Recovery Audit

生成时间：2026-06-12

审计性质：只读审计；除本报告外未修改 `theory/*`、`engine/*`、`tests/*`、`META/project-state.json`。

## 0. Executive Finding

554 条 feedback rows 中，534 条在 preprocess 阶段被写成 `rule_id=UNMAPPED`，另有 20 条为旧式 `M*` rule_id；但 554 条全部未能恢复到 Phase-300 strategy 的正式 `DTS-*` / `ZIPING-*` rule_id，导致动态置信度初始化侧全部进入 mapping repair / non-learning。

真正断链位置是：`feedback verdict → statement_id → statement_index → rule_id`。其中 414 条断在 preprocess fallback 生成的 `UNMAPPED-<case>-<line>` 临时 statement_id；另有旧版 `S-*` statement_id 可部分命中 statement_index，但 statement_index 缺规则桥，且旧式 `M*` rule_id 不在 Phase-300 strategy 表。

根因归类：`ROOT_CAUSE_E`（多原因混合）。主因是 `ROOT_CAUSE_C` + `ROOT_CAUSE_A/B` 叠加；`ROOT_CAUSE_D` 解释少量旧版 statement / 旧式规则号样本。

## A. Feedback Map Cardinality

输入：`META/phase-1000-feedback-preprocess/rule_statement_verdict_map.csv`

- Total feedback rows: 554
- Valid verdict rows (`y/n/pending`): 511
- Non-pending rows (`y/n`): 217
- Current `learnable=true`: 12
- Rows with `needs_mapping_repair=true`: 534
- Rows with `case_fallback=true`: 554
- Unique `rule_id`: 21
- Unique `statement_id`: 524

### rule_id frequency leaderboard

| Rank | rule_id | Frequency | Share |
|---:|---|---:|---:|
| 1 | `UNMAPPED` | 534 | 96.39% |
| 2 | `M1-D-028` | 1 | 0.18% |
| 3 | `M2-Y-028` | 1 | 0.18% |
| 4 | `M2-Y-029` | 1 | 0.18% |
| 5 | `M3-R-028` | 1 | 0.18% |
| 6 | `M1-D-029` | 1 | 0.18% |
| 7 | `M2-Y-030` | 1 | 0.18% |
| 8 | `M1-D-030` | 1 | 0.18% |
| 9 | `M3-R-029` | 1 | 0.18% |
| 10 | `M2-Y-031` | 1 | 0.18% |
| 11 | `G-SHENSHA-028` | 1 | 0.18% |
| 12 | `M1-D-031` | 1 | 0.18% |
| 13 | `G-SHENSHA-029` | 1 | 0.18% |
| 14 | `M3-R-030` | 1 | 0.18% |
| 15 | `M1-D-032` | 1 | 0.18% |
| 16 | `M3-R-031` | 1 | 0.18% |
| 17 | `M2-Y-032` | 1 | 0.18% |
| 18 | `M3-R-032` | 1 | 0.18% |
| 19 | `M1-D-033` | 1 | 0.18% |
| 20 | `M3-R-033` | 1 | 0.18% |
| 21 | `M2-Y-033` | 1 | 0.18% |

### statement_id frequency leaderboard

| Rank | statement_id | Frequency | Share |
|---:|---|---:|---:|
| 1 | `S-025-d1a001` | 2 | 0.36% |
| 2 | `S-025-d2b001` | 2 | 0.36% |
| 3 | `S-025-hl001` | 2 | 0.36% |
| 4 | `S-025-cns001` | 2 | 0.36% |
| 5 | `S-025-hl002` | 2 | 0.36% |
| 6 | `S-025-yq2018` | 2 | 0.36% |
| 7 | `S-025-yq2024` | 2 | 0.36% |
| 8 | `S-025-yq2025` | 2 | 0.36% |
| 9 | `S-025-yq2027` | 2 | 0.36% |
| 10 | `S-025-yq2029` | 2 | 0.36% |
| 11 | `S-026-d1a001` | 2 | 0.36% |
| 12 | `S-026-d2b001` | 2 | 0.36% |
| 13 | `S-026-hl001` | 2 | 0.36% |
| 14 | `S-026-cns001` | 2 | 0.36% |
| 15 | `S-026-hl002` | 2 | 0.36% |
| 16 | `S-026-yq2018` | 2 | 0.36% |
| 17 | `S-026-yq2021` | 2 | 0.36% |
| 18 | `S-026-yq2024` | 2 | 0.36% |
| 19 | `S-026-yq2026` | 2 | 0.36% |
| 20 | `S-026-yq2027` | 2 | 0.36% |
| 21 | `S-028-d1a001` | 2 | 0.36% |
| 22 | `S-028-d2b001` | 2 | 0.36% |
| 23 | `S-028-cns001` | 2 | 0.36% |
| 24 | `S-028-cns002` | 2 | 0.36% |
| 25 | `S-028-hl001` | 2 | 0.36% |
| 26 | `S-028-hl002` | 2 | 0.36% |
| 27 | `S-028-yq2024` | 2 | 0.36% |
| 28 | `S-028-yq2025` | 2 | 0.36% |
| 29 | `S-028-yq2026` | 2 | 0.36% |
| 30 | `S-028-yq2028` | 2 | 0.36% |
| ... | other 494 values | 494 | 89.17% |

## B. Phase-300 Strategy Rule Set Difference

输入：`META/phase-300-voting-strategy.md`

- Phase-300 strategy table total rule_id rows: 255
- Phase-300 strategy table unique rule_id: 255
- feedback unique rule_id: 21
- feedback 中存在、strategy 不存在: 21
- strategy 存在、feedback 不存在: 255

### feedback 中存在、strategy 不存在的 rule_id

- `G-SHENSHA-028`
- `G-SHENSHA-029`
- `M1-D-028`
- `M1-D-029`
- `M1-D-030`
- `M1-D-031`
- `M1-D-032`
- `M1-D-033`
- `M2-Y-028`
- `M2-Y-029`
- `M2-Y-030`
- `M2-Y-031`
- `M2-Y-032`
- `M2-Y-033`
- `M3-R-028`
- `M3-R-029`
- `M3-R-030`
- `M3-R-031`
- `M3-R-032`
- `M3-R-033`
- `UNMAPPED`

### strategy 存在、feedback 不存在的 rule_id

- `DTS-PROD-20260605-001`
- `DTS-PROD-20260605-002`
- `DTS-PROD-20260605-003`
- `DTS-PROD-20260605-004`
- `DTS-PROD-20260605-005`
- `DTS-PROD-20260605-006`
- `DTS-PROD-20260605-007`
- `DTS-PROD-20260605-008`
- `DTS-PROD-20260605-009`
- `DTS-PROD-20260605-010`
- `DTS-PROD-20260605-011`
- `DTS-PROD-20260605-012`
- `DTS-PROD-20260605-013`
- `DTS-PROD-20260605-014`
- `DTS-PROD-20260605-015`
- `DTS-PROD-20260605-016`
- `DTS-PROD-20260605-017`
- `DTS-PROD-20260605-018`
- `DTS-PROD-20260605-019`
- `DTS-PROD-20260606-001`
- `DTS-PROD-20260606-002`
- `DTS-PROD-20260606-003`
- `DTS-PROD-20260606-004`
- `DTS-PROD-20260606-005`
- `DTS-PROD-20260606-006`
- `DTS-PROD-20260606-007`
- `DTS-PROD-20260606-008`
- `DTS-PROD-20260606-009`
- `DTS-PROD-20260606-010`
- `DTS-PROD-20260606-011`
- `DTS-PROD-20260606-012`
- `DTS-PROD-20260606-013`
- `DTS-PROD-20260606-014`
- `DTS-PROD-20260606-015`
- `DTS-PROD-20260606-016`
- `DTS-PROD-20260606-017`
- `DTS-PROD-20260606-018`
- `DTS-PROD-20260606-019`
- `DTS-PROD-20260606-020`
- `DTS-PROD-20260606-021`
- `DTS-PROD-20260606-022`
- `DTS-PROD-20260606-023`
- `DTS-PROD-20260606-024`
- `DTS-PROD-20260606-025`
- `DTS-PROD-20260606-026`
- `DTS-PROD-20260606-027`
- `DTS-PROD-20260606-028`
- `DTS-PROD-20260606-029`
- `DTS-PROD-20260606-030`
- `DTS-PROD-20260606-031`
- `DTS-PROD-20260606-032`
- `DTS-PROD-20260606-033`
- `DTS-PROD-20260606-034`
- `DTS-PROD-20260606-035`
- `DTS-PROD-20260606-036`
- `DTS-PROD-20260606-037`
- `DTS-PROD-20260606-038`
- `DTS-PROD-20260606-039`
- `DTS-PROD-20260606-040`
- `DTS-PROD-20260606-041`
- `DTS-PROD-20260606-042`
- `DTS-PROD-20260606-043`
- `DTS-PROD-20260606-044`
- `DTS-PROD-20260606-045`
- `DTS-PROD-20260606-046`
- `DTS-PROD-20260606-047`
- `DTS-PROD-20260606-048`
- `DTS-PROD-20260606-049`
- `DTS-PROD-20260606-050`
- `DTS-PROD-20260606-051`
- `DTS-PROD-20260606-052`
- `DTS-PROD-20260606-053`
- `DTS-PROD-20260606-054`
- `DTS-PROD-20260606-055`
- `DTS-PROD-20260606-056`
- `DTS-PROD-20260606-057`
- `DTS-PROD-20260606-058`
- `DTS-PROD-20260606-059`
- `DTS-PROD-20260606-060`
- `DTS-PROD-20260606-061`
- `DTS-PROD-20260606-062`
- `DTS-PROD-20260606-063`
- `DTS-PROD-20260606-064`
- `DTS-PROD-20260606-065`
- `DTS-PROD-20260606-066`
- `DTS-PROD-20260606-067`
- `DTS-PROD-20260606-068`
- `DTS-PROD-20260606-069`
- `DTS-PROD-20260606-070`
- `DTS-PROD-20260606-071`
- `DTS-PROD-20260606-072`
- `DTS-PROD-20260606-073`
- `DTS-PROD-20260606-074`
- `DTS-PROD-20260606-075`
- `DTS-PROD-20260606-076`
- `DTS-PROD-20260606-077`
- `DTS-PROD-20260606-078`
- `DTS-PROD-20260606-079`
- `DTS-PROD-20260606-080`
- `DTS-PROD-20260606-081`
- `DTS-PROD-20260606-082`
- `DTS-PROD-20260606-083`
- `DTS-PROD-20260606-084`
- `DTS-PROD-20260606-085`
- `DTS-PROD-20260606-086`
- `DTS-PROD-20260606-087`
- `DTS-PROD-20260606-088`
- `DTS-PROD-20260606-089`
- `DTS-PROD-20260606-090`
- `DTS-PROD-20260606-091`
- `DTS-PROD-20260606-092`
- `DTS-PROD-20260606-093`
- `DTS-PROD-20260606-094`
- `DTS-PROD-20260606-095`
- `DTS-PROD-20260606-096`
- `DTS-PROD-20260606-097`
- `DTS-PROD-20260606-098`
- `DTS-PROD-20260606-099`
- `DTS-PROD-20260606-100`
- `DTS-PROD-20260606-101`
- `DTS-PROD-20260606-102`
- `DTS-PROD-20260606-103`
- `DTS-PROD-20260606-104`
- `DTS-PROD-20260606-105`
- `DTS-PROD-20260606-106`
- `DTS-PROD-20260606-107`
- `DTS-PROD-20260606-108`
- `DTS-PROD-20260606-109`
- `DTS-PROD-20260606-110`
- `DTS-PROD-20260606-111`
- `DTS-PROD-20260606-112`
- `DTS-PROD-20260606-113`
- `DTS-PROD-20260606-114`
- `DTS-PROD-20260606-115`
- `DTS-PROD-20260606-116`
- `DTS-PROD-20260606-117`
- `DTS-PROD-20260606-118`
- `DTS-PROD-20260606-119`
- `DTS-PROD-20260606-120`
- `DTS-PROD-20260606-121`
- ... omitted 115 additional rule_id values

## C. statement_index.json Field Coverage

扫描范围：`cases/**/statement_index.json`

- statement_index files: 1010
- parsed statement entries: 4797
- invalid JSON files: 0
- unique statement_id in indexes: 1644

| Field | Key Exists | Present Value | Total Statements | Coverage |
|---|---:|---:|---:|---:|
| `rule_id` | 0 | 0 | 4797 | 0.00% |
| `family_id` | 0 | 0 | 4797 | 0.00% |
| `school` | 0 | 0 | 4797 | 0.00% |
| `canon` | 0 | 0 | 4797 | 0.00% |
| `rule_type` | 0 | 0 | 4797 | 0.00% |

说明：`statement_index.json` 基本是报告 statement 索引，不是规则级证据桥。`rule_id/family_id/school/canon/rule_type` 覆盖率接近或等于 0，因此即使旧版 `S-*` statement_id 命中，也无法稳定恢复到 Phase-300 family / canon。

## D. Pipeline Recovery Funnel

完整链路：`feedback verdict → statement_id → statement_index → rule_id → family_id → school → canon`

| Step | Count | Success Rate vs Feedback | Drop From Previous |
|---|---:|---:|---:|
| feedback verdict | 554 | 100.00% | — |
| statement found | 101 | 18.23% | 453 |
| rule found | 20 | 3.61% | 81 |
| family found | 0 | 0.00% | 20 |
| school found | 0 | 0.00% | 0 |
| canon found | 0 | 0.00% | 0 |

漏斗结论：`statement found` 为 101 / 554，但 `family/school/canon found` 仍为 0。断链不是单点：第一断点在 `statement_id → statement_index`，第二断点在 `statement_index/rule_id → Phase-300 strategy`。

## E. Root Cause Classification

| Rank | Root Cause | Rows Affected | Evidence | Classification |
|---:|---|---:|---|---|
| 1 | `ROOT_CAUSE_A` | 534 | 534 条 `rule_id=UNMAPPED`；statement_index 规则字段覆盖不足，无法承接规则反查 | Primary/Structural |
| 2 | `ROOT_CAUSE_C` | 414 | preprocess fallback 生成 `UNMAPPED-*` statement_id，无法命中真实 statement_index | Primary |
| 3 | `ROOT_CAUSE_B` | 20 | 20 条旧式 `M*` rule_id 不在 Phase-300 strategy 表；`UNMAPPED` 也不在策略表 | Primary |
| 4 | `ROOT_CAUSE_D` | 39 | 非 `UNMAPPED-*` 的旧版 statement_id 存在部分不命中，且旧版命中样本缺少正式 rule bridge | Secondary |
| 5 | `ROOT_CAUSE_E` | 554 | A/B/C/D 均存在，最终表现为全量 non-learning / mapping repair | Final category |

### alignment repair reason leaderboard

| Rank | repair_reason | Frequency | Share |
|---:|---|---:|---:|
| 1 | `rule_not_in_phase300_strategy` | 554 | 13.03% |
| 2 | `missing_family_id` | 554 | 13.03% |
| 3 | `missing_school_lane` | 554 | 13.03% |
| 4 | `missing_canon` | 554 | 13.03% |
| 5 | `input_fallback_reason_present` | 554 | 13.03% |
| 6 | `missing_rule_id` | 534 | 12.56% |
| 7 | `input_needs_mapping_repair` | 534 | 12.56% |
| 8 | `missing_or_invalid_rule_type` | 414 | 9.74% |

### fallback reason leaderboard

| Rank | fallback_reason | Frequency | Share |
|---:|---|---:|---:|
| 1 | `ModuleNotFoundError('No module named tools')` | 554 | 100.00% |

## F. Repair Priority

1. 修复 Phase-1000 preprocess 的执行入口 / import path，优先清除 `ModuleNotFoundError('No module named tools')` fallback。
2. 禁止把 `UNMAPPED-<case>-<line>` 作为可学习 statement_id；preprocess 必须优先读取 `cases/<case_id>/statement_index.json` 的真实 statement_id。
3. 建立 `statement_id → rule_id` bridge；如果报告 statement 不是规则 statement，则需要独立 mapping 文件承接 feedback 到规则证据。
4. 建立旧式 `M*` rule_id 到正式 `DTS-*` / `ZIPING-*` rule_id 的迁移表，或在 preprocessing 阶段直接重算正式 rule_id。
5. 用 Phase-300 strategy 表补齐 `rule_id → family_id/school/canon/rule_type`，并对 Family ID 为 `-` 的策略规则明确 learning lane。
6. 重新生成 `rule_statement_family_alignment.csv`，以 funnel 指标而不是行数成功作为解除阻塞标准。

## G. Expected Learnable Samples After Repair

| Scenario | Estimated Learnable Rows | Basis |
|---|---:|---|
| Current state | 0 | `canon found=0`，当前不可进入动态置信度学习 |
| 修复 import fallback + statement bridge，pending 排除 | up to 217 | `feedback_verdict in y/n` 的样本数 |
| 修复 import fallback + statement bridge，pending 进入 review lane | up to 511 | `y/n/pending` 全部可进入治理或复核队列 |
| 完整规则桥与 Phase-300 对齐后上限 | 554 | 仅当 pending 被定义为治理样本且全部补齐 rule/family/canon |

保守预计：首轮修复后可恢复最多 217 条 `y/n` 样本为可学习候选；`pending` 不应直接进入 Beta 学习，只进入 review / remediation lane。

## H. Phase-1000 Blocker Decision

结论：不解除 Phase-1000 阻塞。

解除条件：

- `fallback_reason=ModuleNotFoundError('No module named tools')` 清零。
- `statement found` 对非 pending 样本不低于 90%。
- `rule found`、`family found`、`school found`、`canon found` 对非 pending 样本不低于 80%。
- `feedback 中存在、strategy 不存在` 的 rule_id 只允许剩余人工确认的 deprecated / non-learning id。
- `learnable=true` 覆盖主要 `y/n` 样本，且 repair queue 不再全量堆积。

## I. Direct Evidence Snapshot

- `rule_statement_verdict_map.csv`: `UNMAPPED` 534/554；其余 20 条为旧式 `M*` id。
- `rule_statement_verdict_map.csv`: unique `statement_id` 为 524，多数为 `UNMAPPED-*` fallback id，少数为旧版 `S-*`。
- `rule_statement_family_alignment.csv`: repair reasons 集中在 missing rule / strategy / family / school / canon / rule_type。
- `statement_index.json`: 共有 4797 条 statement entry，但规则映射字段覆盖率不足，无法承担 rule recovery。
- `META/feedback-governance-remediation-plan.md`: 本审计定位的首修目标应落在 preprocess runner / module invocation 与 bridge mapping，而不是直接调 dynamic confidence 权重。
