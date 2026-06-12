# Phase-1000 Feedback Sample Pre-Processing Summary

> 范围：正式 `cases/C-2026-*` 目录中具备 `input.md` 的前 100 个 Phase-1000 候选；只生成标准化副本与映射表，不改写原始 `cases/*`、`theory/*`、`engine/*`、`tests/*`、`META/project-state.json`。

## 1. 输出产物

- 映射 CSV：`META/phase-1000-feedback-preprocess/rule_statement_verdict_map.csv`
- 映射 JSON：`META/phase-1000-feedback-preprocess/rule_statement_verdict_map.json`
- case 审计 JSON：`META/phase-1000-feedback-preprocess/case_feedback_preprocess_audit.json`
- 标准化 feedback 副本目录：`META/phase-1000-feedback-preprocess/normalized-feedback/`

## 2. 案例覆盖率

| metric | value |
|---|---:|
| `total_cases` | 100 |
| `paired_input_feedback` | 100 |
| `missing_feedback` | 0 |
| `missing_statement_index` | 0 |
| `cases_with_any_feedback_signal` | 100 |
| `zero_feedback_signal` | 0 |
| `cases_with_y_n` | 23 |
| `fallback_cases` | 100 |
| `feedback_signal_rows` | 554 |
| `learnable_rows` | 12 |
| `mapping_repair_rows` | 534 |

## 3. verdict 标准化状态

| verdict | rows |
|---|---:|
| `y` | 183 |
| `n` | 34 |
| `skip` | 43 |
| `pending` | 294 |

说明：旧 `[?]`、空 `[ ]`、`unknown`、`待反馈`、`⏳ pending` 统一映射为 `pending`；`partial` / `🟡` 不保留为顶层 verdict，按 P4-2 写入 `partial_reason` 并默认不进入可学习样本。

## 4. 缺失 / fallback 案例统计

| category | count | action |
|---|---:|---|
| feedback 缺失 | 0 | 待补 `feedback.md` |
| 零反馈信号 | 0 | 待按 v1.3 表补充 `statement_id/verdict` |
| statement_index 缺失 | 0 | 待回填 `statement_index.json` |
| fallback 标记 | 100 | 待修复：`ModuleNotFoundError('No module named tools')` |

## 5. 覆盖不足统计

### 5.1 School

| school | rows | note |
|---|---:|---|
| `UNMAPPED` | 554 | 当前 `statement_index.json` 多数未携带 school 字段，需后续回填 |

### 5.2 Family

| family | rows | note |
|---|---:|---|
| `UNMAPPED` | 554 | 当前 `statement_index.json` 多数未携带 family 字段，暂不可做 family posterior |

### 5.3 Rule Type

| rule_type | rows |
|---|---:|
| `UNMAPPED` | 414 |
| `TIMING` | 50 |
| `GENERAL_PRINCIPLE` | 45 |
| `EVENT` | 45 |

### 5.4 案例数

| bucket | case_count |
|---|---:|
| 有任一反馈信号 | 100 |
| 有明确 y/n | 23 |
| 待补或待修复 | 100 |

## 6. 结论

本轮完成了 Phase-1000 候选反馈字段的标准化预处理与 `rule_id -> statement_id -> verdict` 映射输出。当前最大阻塞仍是 fallback 环境标记与 rule 映射不足：大量断语缺少可学习 `rule_id`，因此本批输出只能作为动态置信度引擎读取前的清洗副本与修复队列，不能直接解冻规则 posterior 自动更新。
