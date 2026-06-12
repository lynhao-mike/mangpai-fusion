# Recoverability Classification

生成时间：`2026-06-12T16:03:27Z`

## 1. 可恢复性分类

| 分类 | 数量 | 比例 | 预估恢复样本数 |
|---|---:|---:|---:|
| HIGH_RECOVERABLE | 0 | 0.0% | 0 |
| MEDIUM_RECOVERABLE | 162 | 27.36% | 162 |
| LOW_RECOVERABLE | 430 | 72.64% | 0 |
| UNRECOVERABLE | 0 | 0.0% | 0 |

## 2. TOP10 Root Causes

### ROOT_CAUSE_1

- 原因：`feedback_has_only_indirect_or_report_level_reference`
- 影响样本数：430
- 占比：72.64%

### ROOT_CAUSE_2

- 原因：`report_and_index_exist_but_record_mapping_missing`
- 影响样本数：162
- 占比：27.36%

## 3. Phase-1000 阻塞主根因

唯一主根因：`feedback_has_only_indirect_or_report_level_reference`。

该根因说明 feedback 与当前 statement_records 之间缺少同源、同版本、可学习的 statement 级绑定；因此即使 statement_records 覆盖率为 127/127，也不能恢复为 Phase-1000 learnable samples。
