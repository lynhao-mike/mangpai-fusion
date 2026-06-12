# Rule Source Audit

审计范围：

- theory/ziping/index.yaml
- theory/tiaohou_ditiansui/index.yaml

审计性质：只读来源审计。本文只统计每条规则的 source_book、school、canon 与潜在混杂风险，不修改规则文件、权重或 Schema，不做自动纠正。

来源识别口径：

- source_book：优先从 source.path、source.book、source.title、source.canon、source.excerpt 中识别经典名。
- school：按经典归属推断；子平真诠、三命通会、穷通宝鉴归入 ziping；滴天髓归入 tiaohou_ditiansui。
- canon：按经典性质归入子平格局经典、子平综合经典、调候取用经典、滴天髓气机经典。
- 若字段不完整或无法识别，标记 UNKNOWN 或 SOURCE_MISSING_OR_INCOMPLETE。

## 1. 所有规则来源统计表

| Rule ID | Source Book | School | Canon | Source Path |
|---|---|---|---|---|
| ZP-PROD-20260605-001 | 子平真诠 | ziping | 子平格局经典 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-002 | 子平真诠 | ziping | 子平格局经典 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-003 | 子平真诠 | ziping | 子平格局经典 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-004 | 子平真诠 | ziping | 子平格局经典 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-005 | 子平真诠 | ziping | 子平格局经典 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-006 | 子平真诠 | ziping | 子平格局经典 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-007 | 子平真诠 | ziping | 子平格局经典 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-008 | 子平真诠 | ziping | 子平格局经典 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-009 | 子平真诠+调候经典 | tiaohou_ditiansui+ziping | 子平格局经典+调候经典 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-010 | 子平真诠 | ziping | 子平格局经典 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-011 | 子平真诠 | ziping | 子平格局经典 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-012 | 子平真诠 | ziping | 子平格局经典 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-013 | 子平真诠 | ziping | 子平格局经典 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-014 | 子平真诠 | ziping | 子平格局经典 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-015 | 子平真诠 | ziping | 子平格局经典 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-016 | 子平真诠 | ziping | 子平格局经典 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-017 | 子平真诠 | ziping | 子平格局经典 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260605-018 | 子平真诠 | ziping | 子平格局经典 | sources/ziping/《子平真诠》.md |
| ZP-PROD-20260606-001 | 三命通会 | ziping | 子平综合经典 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-002 | 三命通会 | ziping | 子平综合经典 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-003 | 三命通会 | ziping | 子平综合经典 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-004 | 三命通会 | ziping | 子平综合经典 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-005 | 三命通会 | ziping | 子平综合经典 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-006 | 三命通会 | ziping | 子平综合经典 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-007 | 三命通会 | ziping | 子平综合经典 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-008 | 三命通会 | ziping | 子平综合经典 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-009 | 三命通会 | ziping | 子平综合经典 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-010 | 三命通会 | ziping | 子平综合经典 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-011 | 三命通会 | ziping | 子平综合经典 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-012 | 三命通会 | ziping | 子平综合经典 | sources/ziping/《三命通会》.md |
| ZP-PROD-20260606-013 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-014 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-015 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-016 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-017 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-018 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-019 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-020 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-021 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-022 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-023 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-024 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-025 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-026 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part1.md |
| ZP-PROD-20260606-027 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-028 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-029 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-030 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-031 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-032 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-033 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-034 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-035 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-036 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-037 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-038 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| ZP-PROD-20260606-039 | 穷通宝鉴 | ziping | 调候取用经典 | sources/ziping/穷通宝鉴-明-余春台_part2.md |
| DTS-PROD-20260605-001 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-002 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-003 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-004 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-005 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-006 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-007 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-008 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-009 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-010 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-011 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-012 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-013 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-014 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-015 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-016 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-017 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-018 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260605-019 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part1.md |
| DTS-PROD-20260606-001 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-002 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-003 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-004 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-005 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-006 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-007 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-008 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-009 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-010 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-011 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-012 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part2.md |
| DTS-PROD-20260606-013 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part3.md |
| DTS-PROD-20260606-014 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part3.md |
| DTS-PROD-20260606-015 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part3.md |
| DTS-PROD-20260606-016 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part3.md |
| DTS-PROD-20260606-017 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part3.md |
| DTS-PROD-20260606-018 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part3.md |
| DTS-PROD-20260606-019 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part3.md |
| DTS-PROD-20260606-020 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part3.md |
| DTS-PROD-20260606-021 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part3.md |
| DTS-PROD-20260606-022 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓_part3.md |
| DTS-PROD-20260606-023 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-024 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-025 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-026 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-027 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-028 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-029 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-030 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-031 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-032 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-033 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-034 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-035 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-036 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-037 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-038 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part1.md |
| DTS-PROD-20260606-039 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-040 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-041 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-042 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-043 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-044 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-045 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-046 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-047 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-048 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-049 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-050 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-051 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-052 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-053 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-054 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-055 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-056 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-057 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-058 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-059 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-060 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-061 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-062 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-063 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-064 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part2.md |
| DTS-PROD-20260606-065 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-066 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-067 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-068 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-069 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-070 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-071 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-072 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-073 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-074 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-075 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-076 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-077 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-078 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-079 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-080 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-081 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-082 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-083 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-084 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part3.md |
| DTS-PROD-20260606-085 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-086 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-087 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-088 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-089 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-090 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-091 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-092 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-093 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-094 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-095 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-096 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-097 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-098 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-099 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-100 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-101 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-102 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-103 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-104 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-105 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-106 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-107 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-108 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-109 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-110 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-111 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-112 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-113 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-114 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-115 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-116 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-117 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-118 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-119 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-120 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-121 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-122 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-123 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-124 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-125 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-126 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-127 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-128 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-129 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-130 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-131 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-132 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-133 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-134 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part4.md |
| DTS-PROD-20260606-135 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-136 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-137 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-138 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-139 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-140 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-141 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-142 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-143 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-144 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-145 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-146 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-147 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-148 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-149 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-150 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-151 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-152 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-153 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-154 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-155 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-156 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-157 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-158 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-159 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-160 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-161 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-162 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-163 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-164 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-165 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-166 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-167 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-168 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-169 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-170 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-171 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-172 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-173 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-174 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-175 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-176 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-177 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-178 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part5.md |
| DTS-PROD-20260606-179 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-180 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-181 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-182 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-183 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-184 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-185 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-186 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-187 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-188 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-189 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-190 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-191 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-192 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-193 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-194 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-195 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-196 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-197 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-198 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-199 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-200 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-201 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-202 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-203 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-204 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-205 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-206 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-207 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-208 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-209 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-210 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-211 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-212 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-213 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-214 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-215 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part6.md |
| DTS-PROD-20260606-216 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-217 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-218 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-219 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-220 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-221 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-222 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-223 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-224 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-225 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-226 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-227 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-228 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-229 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-230 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-231 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-232 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-233 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-234 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-235 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |
| DTS-PROD-20260606-236 | 滴天髓 | tiaohou_ditiansui | 滴天髓气机经典 | sources/tiaohou_ditiansui/滴天髓阐微-清-任铁樵_part8.md |

## 2. 来源分布统计

### 2.1 按 source_book 统计

| Source Book | Count |
|---|---:|
| 滴天髓 | 255 |
| 穷通宝鉴 | 27 |
| 子平真诠 | 18 |
| 三命通会 | 12 |
| 调候经典 | 1 |

### 2.2 按 school 统计

| School | Count |
|---|---:|
| tiaohou_ditiansui | 255 |
| ziping | 56 |
| tiaohou_ditiansui+ziping | 1 |

### 2.3 按 canon 统计

| Canon | Count |
|---|---:|
| 滴天髓气机经典 | 255 |
| 调候取用经典 | 27 |
| 子平格局经典 | 17 |
| 子平综合经典 | 12 |
| 子平格局经典+调候经典 | 1 |

### 2.4 按规则文件统计

| Rule File School | Count |
|---|---:|
| ziping | 57 |
| tiaohou_ditiansui | 255 |

## 3. 潜在混杂风险提示

| Rule ID | Risk Type | Detail |
|---|---|---|
| ZP-PROD-20260605-009 | MULTI_CANON_REFERENCE | 同一规则来源文本命中多本经典 |
| ZP-PROD-20260605-009 | POSSIBLE_CROSS_SCHOOL_SOURCE | ziping 文件中识别为 tiaohou_ditiansui+ziping |

### 3.1 哪些规则同时引用多本经典

- ZP-PROD-20260605-009: 子平真诠+调候经典

### 3.2 哪些规则来源不明或缺失

- 未发现来源不明或 source.path 缺失的规则。

### 3.3 哪些规则可能被误引用为子平真诠/滴天髓

- ZP-PROD-20260605-009: 位于 ziping，但识别 school=tiaohou_ditiansui+ziping source_book=子平真诠+调候经典

## 4. 对未来案例校准可能产生的影响说明

1. 如果来源经典混杂但未显式标注，校准时会把不同理论传统的命中率合并，导致某一经典的真实有效性被误估。
2. 子平、三命通会、穷通宝鉴虽然都可归入广义子平体系，但其理论侧重点不同；若不区分 canon，格局、综合断法、调候取用会在校准中互相污染。
3. 滴天髓/调候规则若引用子平类经典而未标注，会扩大滴天髓规则族的表面覆盖率，影响 family-level 去重和 school-level 权重评估。
4. source.excerpt 缺失或来源不明会降低规则可审计性，未来反馈无法可靠追溯到具体经典依据。
5. 未来校准建议同时记录 rule_id、source_book、school、canon 四个维度，避免只按规则文件或 expert_system 统计。

## 5. 审计结论

- 本次共审计 312 条规则。
- source_book 分布以 滴天髓 为最大来源，数量为 255。
- 显性多经典同条引用数量：1。
- 来源不明或缺失数量：0。
- 潜在误归属数量：1。
- 本报告不进行任何自动纠正，仅提供来源治理审计依据。
