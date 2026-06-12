# Canon Source Mapping Audit

## 1. 审计范围与限制

本报告仅审计 `theory/ziping/index.yaml` 与 `theory/tiaohou_ditiansui/index.yaml` 的生产规则 source/canon 映射；未修改 `theory/*`、`engine/*`、权重、Schema、Family 或 Rule Type。

Canon 枚举限定为：`ZIPING_ZHENQUAN`、`SANMING_TONGHUI`、`QIONGTONG_BAOJIAN`、`DITIANSUI`、`DITIANSUI_CHANWEI`、`MODERN_COURSE`、`MIXED_SOURCE`、`UNKNOWN`。

## 2. Canon 判定规则

| Canon | 判定信号 |
|---|---|
| ZIPING_ZHENQUAN | 《子平真诠》 |
| SANMING_TONGHUI | 《三命通会》 |
| QIONGTONG_BAOJIAN | 《穷通宝鉴》 |
| DITIANSUI | 《滴天髓》 |
| DITIANSUI_CHANWEI | 《滴天髓阐微》 |
| MODERN_COURSE | 现代课程/系统课程 |
| MIXED_SOURCE | 混合来源 |
| UNKNOWN | 未知来源 |

若同一规则的 source/path/excerpt/reference 信息同时出现多个经典信号，则归为 `MIXED_SOURCE`，并列入多经典引用风险。

## 3. 总体统计

| canon | source_book | 规则数 | family 数 | rule_type 分布 |
|---|---|---|---|---|
| ZIPING_ZHENQUAN | 《子平真诠》 | 18 | 16 | ANTI_PATTERN:3, EVENT:2, STRUCTURE:12, TIMING:1 |
| SANMING_TONGHUI | 《三命通会》 | 12 | 11 | ANTI_PATTERN:1, EVENT:5, STRUCTURE:5, TIMING:1 |
| QIONGTONG_BAOJIAN | 《穷通宝鉴》 | 27 | 12 | ANTI_PATTERN:1, EVENT:3, GENERAL_PRINCIPLE:19, STRUCTURE:4 |
| DITIANSUI | 《滴天髓》 | 41 | 9 | ANTI_PATTERN:3, EVENT:6, GENERAL_PRINCIPLE:7, STRUCTURE:22, TIMING:3 |
| DITIANSUI_CHANWEI | 《滴天髓阐微》 | 214 | 20 | ANTI_PATTERN:10, EVENT:57, GENERAL_PRINCIPLE:29, STRUCTURE:104, TIMING:14 |
| MODERN_COURSE | 现代课程/系统课程 | 0 | 0 | - |
| MIXED_SOURCE | 混合来源 | 0 | 0 | - |
| UNKNOWN | 未知来源 | 0 | 0 | - |

## 4. School × Canon 分布

| school | canon | 规则数 |
|---|---|---|
| tiaohou_ditiansui | DITIANSUI | 41 |
| tiaohou_ditiansui | DITIANSUI_CHANWEI | 214 |
| ziping | ZIPING_ZHENQUAN | 18 |
| ziping | SANMING_TONGHUI | 12 |
| ziping | QIONGTONG_BAOJIAN | 27 |

## 5. 全量规则映射

| rule_id | school | source_book | canon | rule_type | families | source_path |
|---|---|---|---|---|---|---|
| DTS-PROD-20260605-001 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | EVENT | FAM-003 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-002 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | GENERAL_PRINCIPLE | FAM-006 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-003 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | ANTI_PATTERN | - | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-004 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | FAM-003 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-005 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | FAM-005 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-006 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | FAM-002, FAM-013 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-007 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | ANTI_PATTERN | FAM-001 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-008 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | FAM-002 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-009 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | FAM-005, FAM-020 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-010 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | TIMING | - | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-011 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | GENERAL_PRINCIPLE | FAM-002, FAM-006 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-012 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | GENERAL_PRINCIPLE | FAM-002, FAM-006 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-013 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | FAM-003, FAM-007 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-014 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | FAM-001 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-015 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | FAM-002, FAM-013 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-016 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | FAM-005 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-017 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-018 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | GENERAL_PRINCIPLE | FAM-006 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-019 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | GENERAL_PRINCIPLE | FAM-004 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260606-001 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | EVENT | - | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-002 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-003 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | ANTI_PATTERN | - | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-004 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-005 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-006 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-007 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-008 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | EVENT | - | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-009 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | EVENT | - | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-010 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-011 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | EVENT | - | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-012 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-013 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓_part3.md |
| DTS-PROD-20260606-014 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓_part3.md |
| DTS-PROD-20260606-015 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | TIMING | - | sources/tiaohou_ditiansui/滴天髓_part3.md |
| DTS-PROD-20260606-016 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓_part3.md |
| DTS-PROD-20260606-017 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | TIMING | - | sources/tiaohou_ditiansui/滴天髓_part3.md |
| DTS-PROD-20260606-018 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓_part3.md |
| DTS-PROD-20260606-019 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓_part3.md |
| DTS-PROD-20260606-020 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓_part3.md |
| DTS-PROD-20260606-021 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓_part3.md |
| DTS-PROD-20260606-022 | tiaohou_ditiansui | 《滴天髓》 | DITIANSUI | EVENT | - | sources/tiaohou_ditiansui/滴天髓_part3.md |
| DTS-PROD-20260606-023 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-024 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-025 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-026 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-027 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | ANTI_PATTERN | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-028 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-029 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-030 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-031 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-032 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-033 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-034 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-035 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-036 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-037 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-038 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-039 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-040 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | ANTI_PATTERN | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-041 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | TIMING | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-042 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-043 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-044 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-045 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-046 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-047 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-048 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-049 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-050 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | ANTI_PATTERN | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-051 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | ANTI_PATTERN | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-052 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-053 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-054 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-055 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-056 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-057 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-001, FAM-002, FAM-013, FAM-020 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-058 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-059 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-002, FAM-013, FAM-020 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-060 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-061 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | FAM-002, FAM-011 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-062 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-001, FAM-002, FAM-003 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-063 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-005 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-064 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | TIMING | FAM-005, FAM-010 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-065 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-005, FAM-010 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-066 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-067 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | ANTI_PATTERN | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-068 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-069 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-070 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-071 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-072 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-073 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-074 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-075 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-076 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-077 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-078 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-079 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | ANTI_PATTERN | FAM-007, FAM-008 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-080 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | TIMING | FAM-007, FAM-008, FAM-015 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-081 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | FAM-008 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-082 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-007, FAM-008 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-083 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-084 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | TIMING | FAM-019 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-085 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-019 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-086 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-019 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-087 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | FAM-010 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-088 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-010 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-089 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-090 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | FAM-001, FAM-005 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-091 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | FAM-005, FAM-015 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-092 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-093 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-004 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-094 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | ANTI_PATTERN | FAM-004, FAM-020 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-095 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-096 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | FAM-004 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-097 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-004 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-098 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-099 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-100 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-101 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-102 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-004, FAM-018 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-103 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | FAM-004, FAM-018 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-104 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | FAM-018 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-105 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | FAM-018 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-106 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-107 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-108 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-004, FAM-018 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-109 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | FAM-018 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-110 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-111 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-112 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-113 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | TIMING | FAM-004, FAM-018 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-114 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-115 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-116 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-117 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-118 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-119 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-120 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-121 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-122 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-123 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-124 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-125 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-126 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-127 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-128 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-129 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-130 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-131 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-132 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-133 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-134 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-135 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-136 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | ANTI_PATTERN | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-137 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-138 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | TIMING | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-139 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-140 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-141 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-142 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-143 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-144 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-145 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-146 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-147 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-148 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-149 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-150 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-151 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-152 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-153 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-154 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | TIMING | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-155 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-156 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-157 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-158 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-159 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-160 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-161 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-162 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-163 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-164 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-165 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-166 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | TIMING | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-167 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-168 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-006, FAM-012, FAM-015 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-169 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-006, FAM-012 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-170 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | FAM-006, FAM-012 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-171 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-011 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-172 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-011 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-173 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-011 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-174 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-011 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-175 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-011 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-176 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-011 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-177 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-011 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-178 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | FAM-011 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-179 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | FAM-011 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-180 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | FAM-011 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-181 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-182 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-183 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | ANTI_PATTERN | FAM-012, FAM-019 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-184 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-012 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-185 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-012 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-186 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-012 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-187 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | FAM-012 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-188 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-012, FAM-019 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-189 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-012 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-190 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-191 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-192 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-193 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-194 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | TIMING | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-195 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-011 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-196 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-011 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-197 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-198 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-199 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | TIMING | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-200 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-014 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-201 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-014 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-202 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-014 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-203 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | FAM-014 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-204 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-017 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-205 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-017 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-206 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-017 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-207 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-208 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-209 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-210 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-211 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-212 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-213 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | FAM-003, FAM-016 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-214 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-016 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-215 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | FAM-016 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-216 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | FAM-008, FAM-015 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-217 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | TIMING | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-218 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | FAM-015 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-219 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | FAM-009 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-220 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | TIMING | FAM-009 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-221 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | FAM-009 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-222 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | FAM-009, FAM-010 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-223 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-009 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-224 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | FAM-010 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-225 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-226 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-227 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-228 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-229 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | TIMING | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-230 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-231 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-232 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | STRUCTURE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-233 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | TIMING | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-234 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | ANTI_PATTERN | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-235 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | GENERAL_PRINCIPLE | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-236 | tiaohou_ditiansui | 《滴天髓阐微》 | DITIANSUI_CHANWEI | EVENT | - | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| ZP-PROD-20260605-001 | ziping | 《子平真诠》 | ZIPING_ZHENQUAN | EVENT | FAM-001, FAM-003 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-002 | ziping | 《子平真诠》 | ZIPING_ZHENQUAN | ANTI_PATTERN | FAM-009 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-003 | ziping | 《子平真诠》 | ZIPING_ZHENQUAN | STRUCTURE | FAM-001, FAM-013, FAM-020 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-004 | ziping | 《子平真诠》 | ZIPING_ZHENQUAN | STRUCTURE | FAM-002 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-005 | ziping | 《子平真诠》 | ZIPING_ZHENQUAN | STRUCTURE | FAM-001, FAM-007, FAM-019 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-006 | ziping | 《子平真诠》 | ZIPING_ZHENQUAN | ANTI_PATTERN | FAM-001, FAM-006, FAM-019 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-007 | ziping | 《子平真诠》 | ZIPING_ZHENQUAN | EVENT | FAM-007, FAM-008 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-008 | ziping | 《子平真诠》 | ZIPING_ZHENQUAN | STRUCTURE | FAM-001, FAM-005, FAM-007 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-009 | ziping | 《子平真诠》 | ZIPING_ZHENQUAN | STRUCTURE | FAM-003, FAM-004 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-010 | ziping | 《子平真诠》 | ZIPING_ZHENQUAN | STRUCTURE | FAM-001, FAM-007 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-011 | ziping | 《子平真诠》 | ZIPING_ZHENQUAN | STRUCTURE | FAM-007, FAM-008, FAM-009, FAM-010 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-012 | ziping | 《子平真诠》 | ZIPING_ZHENQUAN | STRUCTURE | FAM-007, FAM-010 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-013 | ziping | 《子平真诠》 | ZIPING_ZHENQUAN | STRUCTURE | FAM-009 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-014 | ziping | 《子平真诠》 | ZIPING_ZHENQUAN | STRUCTURE | FAM-011, FAM-012 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-015 | ziping | 《子平真诠》 | ZIPING_ZHENQUAN | STRUCTURE | FAM-007, FAM-008 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-016 | ziping | 《子平真诠》 | ZIPING_ZHENQUAN | TIMING | FAM-015 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-017 | ziping | 《子平真诠》 | ZIPING_ZHENQUAN | ANTI_PATTERN | - | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-018 | ziping | 《子平真诠》 | ZIPING_ZHENQUAN | STRUCTURE | - | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260606-001 | ziping | 《三命通会》 | SANMING_TONGHUI | STRUCTURE | FAM-005 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-002 | ziping | 《三命通会》 | SANMING_TONGHUI | STRUCTURE | FAM-002, FAM-013, FAM-020 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-003 | ziping | 《三命通会》 | SANMING_TONGHUI | STRUCTURE | FAM-005, FAM-006, FAM-012 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-004 | ziping | 《三命通会》 | SANMING_TONGHUI | STRUCTURE | FAM-001, FAM-002, FAM-009, FAM-010 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-005 | ziping | 《三命通会》 | SANMING_TONGHUI | EVENT | FAM-001, FAM-007, FAM-009 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-006 | ziping | 《三命通会》 | SANMING_TONGHUI | EVENT | FAM-005, FAM-020 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-007 | ziping | 《三命通会》 | SANMING_TONGHUI | STRUCTURE | FAM-001 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-008 | ziping | 《三命通会》 | SANMING_TONGHUI | EVENT | FAM-020 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-009 | ziping | 《三命通会》 | SANMING_TONGHUI | ANTI_PATTERN | FAM-006, FAM-009 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-010 | ziping | 《三命通会》 | SANMING_TONGHUI | EVENT | FAM-006, FAM-014 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-011 | ziping | 《三命通会》 | SANMING_TONGHUI | TIMING | FAM-006, FAM-014 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-012 | ziping | 《三命通会》 | SANMING_TONGHUI | EVENT | FAM-006, FAM-014 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-013 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | STRUCTURE | FAM-002, FAM-003, FAM-010, FAM-016 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-014 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | EVENT | FAM-005 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-015 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | GENERAL_PRINCIPLE | FAM-005 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-016 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | GENERAL_PRINCIPLE | FAM-006, FAM-015 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-017 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | EVENT | FAM-004, FAM-013, FAM-018 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-018 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | EVENT | FAM-004, FAM-013 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-019 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | STRUCTURE | FAM-004, FAM-013, FAM-018 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-020 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | GENERAL_PRINCIPLE | FAM-004 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-021 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | GENERAL_PRINCIPLE | - | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-022 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | GENERAL_PRINCIPLE | - | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-023 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | GENERAL_PRINCIPLE | - | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-024 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | GENERAL_PRINCIPLE | - | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-025 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | STRUCTURE | FAM-003, FAM-004, FAM-016, FAM-017 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-026 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | GENERAL_PRINCIPLE | - | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-027 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | GENERAL_PRINCIPLE | - | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-028 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | GENERAL_PRINCIPLE | FAM-004, FAM-018 | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-029 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | GENERAL_PRINCIPLE | FAM-004 | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-030 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | GENERAL_PRINCIPLE | FAM-004 | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-031 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | GENERAL_PRINCIPLE | - | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-032 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | GENERAL_PRINCIPLE | - | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-033 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | GENERAL_PRINCIPLE | - | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-034 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | STRUCTURE | FAM-001, FAM-004, FAM-013, FAM-018 | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-035 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | GENERAL_PRINCIPLE | - | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-036 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | GENERAL_PRINCIPLE | FAM-004 | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-037 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | GENERAL_PRINCIPLE | FAM-004, FAM-005, FAM-017 | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-038 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | ANTI_PATTERN | FAM-001, FAM-004, FAM-013, FAM-018 | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-039 | ziping | 《穷通宝鉴》 | QIONGTONG_BAOJIAN | GENERAL_PRINCIPLE | FAM-001, FAM-004, FAM-013 | sources/ziping/穷通宝鉴-明-余春台_part2.md |

## 6. TOP 风险

### A. MIXED_SOURCE 规则

未发现 `MIXED_SOURCE` 规则。

### B. UNKNOWN 规则

未发现 `UNKNOWN` 规则。

### C. 一个规则引用多个经典的情况

未发现同一规则引用多个经典的情况。

## 7. 系统定位判断

结论：当前系统应判定为 **B. 子平派专家系统 + 滴天髓调候派专家系统**，而不是狭义的 **A.《子平真诠》+《滴天髓》**。

证据：

1. `ziping` 生产规则并非只来自《子平真诠》，还覆盖 ZIPING_ZHENQUAN, SANMING_TONGHUI, QIONGTONG_BAOJIAN，说明其是子平派综合规则库。
2. `tiaohou_ditiansui` 生产规则并非只来自《滴天髓》正文，还覆盖 DITIANSUI, DITIANSUI_CHANWEI，说明其包含滴天髓正文与任铁樵《滴天髓阐微》阐释系统。
3. 规则层存在 family 与 rule_type 的跨 canon 分布；生产结构以专家系统为组织边界，而非以单本典籍为唯一边界。

## 8. 审计结论

本轮共审计生产规则 312 条。`MIXED_SOURCE` 0 条，`UNKNOWN` 0 条，多经典引用 0 条。

当前生产规则的 canon 映射未发现混合来源或未知来源风险；后续可将本报告作为 Phase-300 前的来源口径基线。
