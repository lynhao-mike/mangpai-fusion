# T-156 规则契约干跑报告（v2 · A 类反条件修复后）

- 语料：`META/timing-eval-set-v1.json`，`usable_for_timing=true`，共 382 例
- 建盘成功：382 例；建盘失败：0 例
- 语义：本卡只新增 `triggered` / `outcome`；`matched` 仍是旧语义（conditions 全中且 exclusions 未中），未改产品输出。
- `n_suppressed_if_flipped`：若下一卡把 `matched` 改为 `triggered and outcome != 'fail'`，会被压掉的条数（预演，不是当前产品行为）。
- `matched == triggered`：True

- 出处：本文件是 `python -m tools.rule_contract_report` 在 **T-156 修复后的 YAML** 上重跑的原样输出（工具第 52–53 行硬编码写 v1 路径，故输出整体搬为 `v2`；`v1` 原字节已按 SHA256 还原，v1 JSON SHA256 `E3ED1318CF12E3FF41D3F4C3646414D6DBBB8637544988D34BD2B84A4C5AD10A`、v1 MD SHA256 `A68311AB55DB4BFD4474258CBB2B4C95541808122D6422765463C4FC4CC1EF7C`）。
- 与 v1 的差异**只有反条件侧**：7 条 A 类规则 `counter_conditions` 置空 → `counter 命中` /`若反条件生效会压掉` / `outcome=success` 三项变化；`n_evaluated` / `n_matched` / `n_triggered` 逐条不变（逐条对照见 `META/counter-condition-audit-v1.md` §4）。
- 本卡未改 `matched`：仍是 T-152 的旧语义（conditions 全中且 exclusions 未中）。
- 除本标题与上面三条出处说明外，正文数字与句子均为工具原样输出。

## 1. 汇总表

| rule_id | eval | triggered | counter 命中 | 若反条件生效会压掉 | outcome=success |
|---|---:|---:|---:|---:|---:|
| `DUAN-EVENT-CAREER-ROLE-CHANGE-V1` | 382 | 176 | 307 | 113 | 63 |
| `DUAN-EVENT-CAREER-PATH-EMPLOYMENT-V1` | 77 | 77 | 0 | 0 | 77 |
| `DUAN-EVENT-CAREER-PATH-ENTREPRENEURSHIP-V1` | 78 | 78 | 72 | 72 | 6 |
| `DUAN-EVENT-CAREER-PATH-MIXED-V1` | 47 | 47 | 0 | 0 | 47 |
| `DUAN-EVENT-WEALTH-DEBT-V1` | 382 | 2 | 0 | 0 | 2 |
| `DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1` | 382 | 153 | 0 | 0 | 153 |
| `GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1` | 382 | 94 | 0 | 0 | 94 |
| `GAO-HEALTH-SYSTEM-RISK-MODERATE-V1` | 90 | 90 | 0 | 0 | 90 |
| `GAO-HEALTH-SYSTEM-RISK-HIGH-V1` | 17 | 17 | 0 | 0 | 17 |
| `YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1` | 382 | 231 | 0 | 0 | 231 |
| **合计** | 2219 | 965 | 379 | 185 | 780 |

## 2. 建盘 / 段派结构失败

无。

## 3. 逐条规则

### `DUAN-EVENT-CAREER-ROLE-CHANGE-V1`

- 流派 / 任务：duan / career.role_change
- 正条件：has_official 为真；has_output 为真；output_count >= 2；official_count >= 1；movement_structure 为真；active_path_count >= 1
- 排除条件：evidence_completeness != full
- 反条件：branch_conflict_intensity <= 0.34
- 数字：n_evaluated=382，n_matched=176，n_triggered=176，n_counter=307，n_suppressed_if_flipped=113，n_outcome_success=63
- 未触发：exclusion 否决 0 例；正条件未满足 206 例
- 反条件命中统计：`branch_conflict_intensity <= 0.34` × 307
- 若反条件生效会被压掉的 case_id（113 例，最多列 20 个，全量见 JSON）：`RF-2026-000010`, `RF-2026-000026`, `RF-2026-000034`, `RF-2026-000072`, `RF-2026-000092`, `RF-2026-000093`, `RF-2026-000096`, `RF-2026-000122`, `RF-2026-000132`, `RF-2026-000136`, `RF-2026-000139`, `RF-2026-000163`, `RF-2026-000169`, `RF-2026-000171`, `RF-2026-000180`, `RF-2026-000188`, `RF-2026-000192`, `RF-2026-000193`, `RF-2026-000197`, `RF-2026-000211`

### `DUAN-EVENT-CAREER-PATH-EMPLOYMENT-V1`

- 流派 / 任务：duan / career.path_type
- 正条件：predicted_label == employment；employment_score >= 4；employment_advantage >= 3
- 排除条件：evidence_completeness != full
- 反条件：active_path_count <= 0
- 数字：n_evaluated=77，n_matched=77，n_triggered=77，n_counter=0，n_suppressed_if_flipped=0，n_outcome_success=77
- 未触发：exclusion 否决 0 例；正条件未满足 0 例
- 若反条件生效会被压掉的 case_id：无

### `DUAN-EVENT-CAREER-PATH-ENTREPRENEURSHIP-V1`

- 流派 / 任务：duan / career.path_type
- 正条件：predicted_label == entrepreneurship；entrepreneurship_score >= 4；entrepreneurship_advantage >= 3；active_path_count >= 1
- 排除条件：evidence_completeness != full
- 反条件：employment_score >= 2
- 数字：n_evaluated=78，n_matched=78，n_triggered=78，n_counter=72，n_suppressed_if_flipped=72，n_outcome_success=6
- 未触发：exclusion 否决 0 例；正条件未满足 0 例
- 反条件命中统计：`employment_score >= 2` × 72
- 若反条件生效会被压掉的 case_id（72 例，最多列 20 个，全量见 JSON）：`RF-2026-000050`, `RF-2026-000066`, `RF-2026-000087`, `RF-2026-000092`, `RF-2026-000093`, `RF-2026-000101`, `RF-2026-000113`, `RF-2026-000140`, `RF-2026-000149`, `RF-2026-000151`, `RF-2026-000188`, `RF-2026-000192`, `RF-2026-000211`, `RF-2026-000212`, `RF-2026-000216`, `RF-2026-000219`, `RF-2026-000255`, `RF-2026-000258`, `RF-2026-000268`, `RF-2026-000292`

### `DUAN-EVENT-CAREER-PATH-MIXED-V1`

- 流派 / 任务：duan / career.path_type
- 正条件：predicted_label == mixed；employment_score >= 4；entrepreneurship_score >= 4；branch_conflict_intensity >= 0.35；active_path_count >= 1
- 排除条件：evidence_completeness != full
- 反条件：（无）
- 数字：n_evaluated=47，n_matched=47，n_triggered=47，n_counter=0，n_suppressed_if_flipped=0，n_outcome_success=47
- 未触发：exclusion 否决 0 例；正条件未满足 0 例
- 若反条件生效会被压掉的 case_id：无

### `DUAN-EVENT-WEALTH-DEBT-V1`

- 流派 / 任务：duan / wealth.debt
- 正条件：has_wealth 为真；wealth_count >= 2；peer_pressure >= 3；support_drain_imbalance >= 3；branch_conflict_intensity >= 0.55；active_path_count >= 1
- 排除条件：evidence_completeness != full
- 反条件：（无）
- 数字：n_evaluated=382，n_matched=2，n_triggered=2，n_counter=0，n_suppressed_if_flipped=0，n_outcome_success=2
- 未触发：exclusion 否决 0 例；正条件未满足 380 例
- 若反条件生效会被压掉的 case_id：无

### `DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1`

- 流派 / 任务：duan / marriage.divorce_or_remarriage
- 正条件：independent_signal_count >= 2；active_path_count >= 1
- 排除条件：evidence_completeness != full
- 反条件：（无）
- 数字：n_evaluated=382，n_matched=153，n_triggered=153，n_counter=0，n_suppressed_if_flipped=0，n_outcome_success=153
- 未触发：exclusion 否决 0 例；正条件未满足 229 例
- 若反条件生效会被压掉的 case_id：无

### `GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1`

- 流派 / 任务：gao / wealth.debt
- 正条件：wealth_exposed 为真；pressure_signal_count >= 2
- 排除条件：evidence_completeness != full
- 反条件：（无）
- 数字：n_evaluated=382，n_matched=94，n_triggered=94，n_counter=0，n_suppressed_if_flipped=0，n_outcome_success=94
- 未触发：exclusion 否决 0 例；正条件未满足 288 例
- 若反条件生效会被压掉的 case_id：无

### `GAO-HEALTH-SYSTEM-RISK-MODERATE-V1`

- 流派 / 任务：gao / health.system_risk
- 正条件：predicted_label == moderate；risk_signal_count >= 2；risk_signal_count <= 2
- 排除条件：evidence_completeness != full
- 反条件：（无）
- 数字：n_evaluated=90，n_matched=90，n_triggered=90，n_counter=0，n_suppressed_if_flipped=0，n_outcome_success=90
- 未触发：exclusion 否决 0 例；正条件未满足 0 例
- 若反条件生效会被压掉的 case_id：无

### `GAO-HEALTH-SYSTEM-RISK-HIGH-V1`

- 流派 / 任务：gao / health.system_risk
- 正条件：predicted_label == high；risk_signal_count >= 3
- 排除条件：evidence_completeness != full
- 反条件：（无）
- 数字：n_evaluated=17，n_matched=17，n_triggered=17，n_counter=0，n_suppressed_if_flipped=0，n_outcome_success=17
- 未触发：exclusion 否决 0 例；正条件未满足 0 例
- 若反条件生效会被压掉的 case_id：无

### `YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1`

- 流派 / 任务：yang / marriage.divorce_or_remarriage
- 正条件：sex 为真；spouse_star_basis ∈ [wealth, official]；independent_signal_count >= 2
- 排除条件：evidence_completeness != full；sex 为假
- 反条件：（无）
- 数字：n_evaluated=382，n_matched=231，n_triggered=231，n_counter=0，n_suppressed_if_flipped=0，n_outcome_success=231
- 未触发：exclusion 否决 0 例；正条件未满足 151 例
- 若反条件生效会被压掉的 case_id：无

