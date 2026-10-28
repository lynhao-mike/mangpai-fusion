# T-152 规则契约干跑报告（v1）

- 语料：`META/timing-eval-set-v1.json`，`usable_for_timing=true`，共 382 例
- 建盘成功：382 例；建盘失败：0 例
- 语义：本卡只新增 `triggered` / `outcome`；`matched` 仍是旧语义（conditions 全中且 exclusions 未中），未改产品输出。
- `n_suppressed_if_flipped`：若下一卡把 `matched` 改为 `triggered and outcome != 'fail'`，会被压掉的条数（预演，不是当前产品行为）。
- `matched == triggered`：True

## 1. 汇总表

| rule_id | eval | triggered | counter 命中 | 若反条件生效会压掉 | outcome=success |
|---|---:|---:|---:|---:|---:|
| `DUAN-EVENT-CAREER-ROLE-CHANGE-V1` | 382 | 176 | 307 | 113 | 63 |
| `DUAN-EVENT-CAREER-PATH-EMPLOYMENT-V1` | 77 | 77 | 0 | 0 | 77 |
| `DUAN-EVENT-CAREER-PATH-ENTREPRENEURSHIP-V1` | 78 | 78 | 72 | 72 | 6 |
| `DUAN-EVENT-CAREER-PATH-MIXED-V1` | 47 | 47 | 5 | 5 | 42 |
| `DUAN-EVENT-WEALTH-DEBT-V1` | 382 | 2 | 318 | 0 | 2 |
| `DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1` | 382 | 153 | 350 | 121 | 32 |
| `GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1` | 382 | 94 | 369 | 84 | 10 |
| `GAO-HEALTH-SYSTEM-RISK-MODERATE-V1` | 90 | 90 | 90 | 90 | 0 |
| `GAO-HEALTH-SYSTEM-RISK-HIGH-V1` | 17 | 17 | 17 | 17 | 0 |
| `YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1` | 382 | 231 | 290 | 139 | 92 |
| **合计** | 2219 | 965 | 1818 | 641 | 324 |

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
- 反条件：branch_conflict_intensity <= 0.4
- 数字：n_evaluated=47，n_matched=47，n_triggered=47，n_counter=5，n_suppressed_if_flipped=5，n_outcome_success=42
- 未触发：exclusion 否决 0 例；正条件未满足 0 例
- 反条件命中统计：`branch_conflict_intensity <= 0.4` × 5
- 若反条件生效会被压掉的 case_id（5 例，最多列 20 个，全量见 JSON）：`RF-2026-000119`, `RF-2026-000176`, `RF-2026-000269`, `RF-2026-000422`, `RF-2026-000471`

### `DUAN-EVENT-WEALTH-DEBT-V1`

- 流派 / 任务：duan / wealth.debt
- 正条件：has_wealth 为真；wealth_count >= 2；peer_pressure >= 3；support_drain_imbalance >= 3；branch_conflict_intensity >= 0.55；active_path_count >= 1
- 排除条件：evidence_completeness != full
- 反条件：support_drain_imbalance <= 3
- 数字：n_evaluated=382，n_matched=2，n_triggered=2，n_counter=318，n_suppressed_if_flipped=0，n_outcome_success=2
- 未触发：exclusion 否决 0 例；正条件未满足 380 例
- 反条件命中统计：`support_drain_imbalance <= 3` × 318
- 若反条件生效会被压掉的 case_id：无

### `DUAN-EVENT-MARRIAGE-DIVORCE-REMARRIAGE-V1`

- 流派 / 任务：duan / marriage.divorce_or_remarriage
- 正条件：independent_signal_count >= 2；active_path_count >= 1
- 排除条件：evidence_completeness != full
- 反条件：independent_signal_count <= 2
- 数字：n_evaluated=382，n_matched=153，n_triggered=153，n_counter=350，n_suppressed_if_flipped=121，n_outcome_success=32
- 未触发：exclusion 否决 0 例；正条件未满足 229 例
- 反条件命中统计：`independent_signal_count <= 2` × 350
- 若反条件生效会被压掉的 case_id（121 例，最多列 20 个，全量见 JSON）：`RF-2026-000034`, `RF-2026-000063`, `RF-2026-000065`, `RF-2026-000072`, `RF-2026-000086`, `RF-2026-000101`, `RF-2026-000103`, `RF-2026-000108`, `RF-2026-000111`, `RF-2026-000125`, `RF-2026-000128`, `RF-2026-000149`, `RF-2026-000169`, `RF-2026-000170`, `RF-2026-000171`, `RF-2026-000178`, `RF-2026-000188`, `RF-2026-000191`, `RF-2026-000196`, `RF-2026-000209`

### `GAO-WEALTH-DEBT-STRUCTURAL-CORROBORATION-V1`

- 流派 / 任务：gao / wealth.debt
- 正条件：wealth_exposed 为真；pressure_signal_count >= 2
- 排除条件：evidence_completeness != full
- 反条件：pressure_signal_count <= 2
- 数字：n_evaluated=382，n_matched=94，n_triggered=94，n_counter=369，n_suppressed_if_flipped=84，n_outcome_success=10
- 未触发：exclusion 否决 0 例；正条件未满足 288 例
- 反条件命中统计：`pressure_signal_count <= 2` × 369
- 若反条件生效会被压掉的 case_id（84 例，最多列 20 个，全量见 JSON）：`RF-2026-000011`, `RF-2026-000045`, `RF-2026-000063`, `RF-2026-000108`, `RF-2026-000119`, `RF-2026-000132`, `RF-2026-000151`, `RF-2026-000153`, `RF-2026-000178`, `RF-2026-000189`, `RF-2026-000192`, `RF-2026-000196`, `RF-2026-000197`, `RF-2026-000215`, `RF-2026-000216`, `RF-2026-000240`, `RF-2026-000244`, `RF-2026-000251`, `RF-2026-000258`, `RF-2026-000281`

### `GAO-HEALTH-SYSTEM-RISK-MODERATE-V1`

- 流派 / 任务：gao / health.system_risk
- 正条件：predicted_label == moderate；risk_signal_count >= 2；risk_signal_count <= 2
- 排除条件：evidence_completeness != full
- 反条件：risk_signal_count >= 2
- 数字：n_evaluated=90，n_matched=90，n_triggered=90，n_counter=90，n_suppressed_if_flipped=90，n_outcome_success=0
- 未触发：exclusion 否决 0 例；正条件未满足 0 例
- 反条件命中统计：`risk_signal_count >= 2` × 90
- 若反条件生效会被压掉的 case_id（90 例，最多列 20 个，全量见 JSON）：`RF-2026-000011`, `RF-2026-000045`, `RF-2026-000081`, `RF-2026-000101`, `RF-2026-000109`, `RF-2026-000111`, `RF-2026-000178`, `RF-2026-000189`, `RF-2026-000191`, `RF-2026-000196`, `RF-2026-000197`, `RF-2026-000213`, `RF-2026-000215`, `RF-2026-000216`, `RF-2026-000243`, `RF-2026-000251`, `RF-2026-000258`, `RF-2026-000259`, `RF-2026-000268`, `RF-2026-000279`

### `GAO-HEALTH-SYSTEM-RISK-HIGH-V1`

- 流派 / 任务：gao / health.system_risk
- 正条件：predicted_label == high；risk_signal_count >= 3
- 排除条件：evidence_completeness != full
- 反条件：risk_signal_count <= 3
- 数字：n_evaluated=17，n_matched=17，n_triggered=17，n_counter=17，n_suppressed_if_flipped=17，n_outcome_success=0
- 未触发：exclusion 否决 0 例；正条件未满足 0 例
- 反条件命中统计：`risk_signal_count <= 3` × 17
- 若反条件生效会被压掉的 case_id（17 例，最多列 20 个，全量见 JSON）：`RF-2026-000065`, `RF-2026-000132`, `RF-2026-000139`, `RF-2026-000192`, `RF-2026-000218`, `RF-2026-000298`, `RF-2026-000352`, `RF-2026-000367`, `RF-2026-000481`, `RF-2026-000536`, `RF-2026-000671`, `RF-2026-000765`, `RF-2026-000804`, `RF-2026-000917`, `RF-2026-000920`, `RF-2026-000940`, `RF-2026-000971`

### `YANG-MARRIAGE-DIVORCE-REMARRIAGE-RISK-V1`

- 流派 / 任务：yang / marriage.divorce_or_remarriage
- 正条件：sex 为真；spouse_star_basis ∈ [wealth, official]；independent_signal_count >= 2
- 排除条件：evidence_completeness != full；sex 为假
- 反条件：independent_signal_count <= 2
- 数字：n_evaluated=382，n_matched=231，n_triggered=231，n_counter=290，n_suppressed_if_flipped=139，n_outcome_success=92
- 未触发：exclusion 否决 0 例；正条件未满足 151 例
- 反条件命中统计：`independent_signal_count <= 2` × 290
- 若反条件生效会被压掉的 case_id（139 例，最多列 20 个，全量见 JSON）：`RF-2026-000011`, `RF-2026-000034`, `RF-2026-000045`, `RF-2026-000057`, `RF-2026-000063`, `RF-2026-000065`, `RF-2026-000070`, `RF-2026-000085`, `RF-2026-000087`, `RF-2026-000090`, `RF-2026-000094`, `RF-2026-000096`, `RF-2026-000100`, `RF-2026-000101`, `RF-2026-000108`, `RF-2026-000113`, `RF-2026-000118`, `RF-2026-000131`, `RF-2026-000142`, `RF-2026-000143`

