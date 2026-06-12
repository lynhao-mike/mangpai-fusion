# Feedback V2 Pre-Process Summary

> 生成时间：2026-06-12T16:30:35Z  
> 来源：recent 10 cases from `META/iteration-state.json::completed_case_ids`  
> 工具：`tools/feedback_v2_preprocess.py`  
> 约束：未修改 `theory/`、`engine/`、`tests/`、`META/project-state.json`、`cases/*/feedback.md` 原文。

## 1. 总体统计

| metric | value |
|---|---:|
| `cases_total` | 10 |
| `statement_records_total` | 225 |
| `feedback_signals_total` | 27 |
| `feedback_coverage` (signals / records) | 12.0% |
| `learnable_samples_total` | 8 |
| `pending_samples_total` | 198 |
| `invalid_statement_id_total` | 0 |

## 2. verdict 分布（仅 {y, n, skip, pending}）

| verdict | rows |
|---|---:|
| `y` | 8 |
| `n` | 0 |
| `skip` | 19 |
| `pending` | 198 |

## 3. 案例级明细

| case_id | records | signals | y | n | skip | pending | learnable | invalid_sid |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `C-2026-015-乾-甲寅乙亥丙辰辛卯` | 111 | 0 | 0 | 0 | 0 | 111 | 0 | 0 |
| `C-2026-018-坤-乙丑戊寅乙酉乙酉` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| `C-2026-025-坤-辛未乙未甲辰乙亥` | 10 | 5 | 3 | 0 | 2 | 5 | 3 | 0 |
| `C-2026-026-坤-癸未甲寅壬戌丙午` | 10 | 6 | 5 | 0 | 1 | 4 | 5 | 0 |
| `C-2026-RF000345-乾-癸酉乙丑乙卯乙酉` | 19 | 3 | 0 | 0 | 3 | 16 | 0 | 0 |
| `C-2026-RF000441-乾-癸亥己未己未庚午` | 18 | 2 | 0 | 0 | 2 | 16 | 0 | 0 |
| `C-2026-RF000864-乾-己巳丙子乙卯甲申` | 18 | 3 | 0 | 0 | 3 | 15 | 0 | 0 |
| `C-2026-RF000243-坤-己卯己巳戊午丁巳` | 16 | 4 | 0 | 0 | 4 | 12 | 0 | 0 |
| `C-2026-RF000524-坤-己巳丙寅戊戌丁巳` | 16 | 4 | 0 | 0 | 4 | 12 | 0 | 0 |
| `C-2026-032-乾-癸酉乙卯戊戌甲寅` | 7 | 0 | 0 | 0 | 0 | 7 | 0 | 0 |

## 4. 产物路径

| case_id | 标准化 feedback | 映射 CSV | 映射 JSON |
|---|---|---|---|
| `C-2026-015-乾-甲寅乙亥丙辰辛卯` | `cases/C-2026-015-乾-甲寅乙亥丙辰辛卯/normalized-feedback/C-2026-015-乾-甲寅乙亥丙辰辛卯-feedback.normalized.md` | `META/phase-1000-feedback-mapping/C-2026-015-乾-甲寅乙亥丙辰辛卯-mapping.csv` | `META/phase-1000-feedback-mapping/C-2026-015-乾-甲寅乙亥丙辰辛卯-mapping.json` |
| `C-2026-018-坤-乙丑戊寅乙酉乙酉` | `cases/C-2026-018-坤-乙丑戊寅乙酉乙酉/normalized-feedback/C-2026-018-坤-乙丑戊寅乙酉乙酉-feedback.normalized.md` | `META/phase-1000-feedback-mapping/C-2026-018-坤-乙丑戊寅乙酉乙酉-mapping.csv` | `META/phase-1000-feedback-mapping/C-2026-018-坤-乙丑戊寅乙酉乙酉-mapping.json` |
| `C-2026-025-坤-辛未乙未甲辰乙亥` | `cases/C-2026-025-坤-辛未乙未甲辰乙亥/normalized-feedback/C-2026-025-坤-辛未乙未甲辰乙亥-feedback.normalized.md` | `META/phase-1000-feedback-mapping/C-2026-025-坤-辛未乙未甲辰乙亥-mapping.csv` | `META/phase-1000-feedback-mapping/C-2026-025-坤-辛未乙未甲辰乙亥-mapping.json` |
| `C-2026-026-坤-癸未甲寅壬戌丙午` | `cases/C-2026-026-坤-癸未甲寅壬戌丙午/normalized-feedback/C-2026-026-坤-癸未甲寅壬戌丙午-feedback.normalized.md` | `META/phase-1000-feedback-mapping/C-2026-026-坤-癸未甲寅壬戌丙午-mapping.csv` | `META/phase-1000-feedback-mapping/C-2026-026-坤-癸未甲寅壬戌丙午-mapping.json` |
| `C-2026-RF000345-乾-癸酉乙丑乙卯乙酉` | `cases/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉/normalized-feedback/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉-feedback.normalized.md` | `META/phase-1000-feedback-mapping/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉-mapping.csv` | `META/phase-1000-feedback-mapping/C-2026-RF000345-乾-癸酉乙丑乙卯乙酉-mapping.json` |
| `C-2026-RF000441-乾-癸亥己未己未庚午` | `cases/C-2026-RF000441-乾-癸亥己未己未庚午/normalized-feedback/C-2026-RF000441-乾-癸亥己未己未庚午-feedback.normalized.md` | `META/phase-1000-feedback-mapping/C-2026-RF000441-乾-癸亥己未己未庚午-mapping.csv` | `META/phase-1000-feedback-mapping/C-2026-RF000441-乾-癸亥己未己未庚午-mapping.json` |
| `C-2026-RF000864-乾-己巳丙子乙卯甲申` | `cases/C-2026-RF000864-乾-己巳丙子乙卯甲申/normalized-feedback/C-2026-RF000864-乾-己巳丙子乙卯甲申-feedback.normalized.md` | `META/phase-1000-feedback-mapping/C-2026-RF000864-乾-己巳丙子乙卯甲申-mapping.csv` | `META/phase-1000-feedback-mapping/C-2026-RF000864-乾-己巳丙子乙卯甲申-mapping.json` |
| `C-2026-RF000243-坤-己卯己巳戊午丁巳` | `cases/C-2026-RF000243-坤-己卯己巳戊午丁巳/normalized-feedback/C-2026-RF000243-坤-己卯己巳戊午丁巳-feedback.normalized.md` | `META/phase-1000-feedback-mapping/C-2026-RF000243-坤-己卯己巳戊午丁巳-mapping.csv` | `META/phase-1000-feedback-mapping/C-2026-RF000243-坤-己卯己巳戊午丁巳-mapping.json` |
| `C-2026-RF000524-坤-己巳丙寅戊戌丁巳` | `cases/C-2026-RF000524-坤-己巳丙寅戊戌丁巳/normalized-feedback/C-2026-RF000524-坤-己巳丙寅戊戌丁巳-feedback.normalized.md` | `META/phase-1000-feedback-mapping/C-2026-RF000524-坤-己巳丙寅戊戌丁巳-mapping.csv` | `META/phase-1000-feedback-mapping/C-2026-RF000524-坤-己巳丙寅戊戌丁巳-mapping.json` |
| `C-2026-032-乾-癸酉乙卯戊戌甲寅` | `cases/C-2026-032-乾-癸酉乙卯戊戌甲寅/normalized-feedback/C-2026-032-乾-癸酉乙卯戊戌甲寅-feedback.normalized.md` | `META/phase-1000-feedback-mapping/C-2026-032-乾-癸酉乙卯戊戌甲寅-mapping.csv` | `META/phase-1000-feedback-mapping/C-2026-032-乾-癸酉乙卯戊戌甲寅-mapping.json` |

## 5. 结论

- verdict 字段已统一为 `{y, n, skip, pending}`，与 Phase-1000 学习通道对齐；learnable 样本仅在 verdict ∈ {y, n} 且 statement_id 命中 record 时才计入。
- 缺失反馈的 statement 一律记 `pending`，可在后续批次补齐后再生成映射。
- `INVALID_STATEMENT_ID` 数量为 0 表示 feedback.md 引用句柄全部能 join；出现 >0 时建议修复 feedback.md 中孤立的 `[S-...]`。
- 本工具不修改任何规则/权重/置信度；学习通道消费方应读取本工具产出的 CSV/JSON。

