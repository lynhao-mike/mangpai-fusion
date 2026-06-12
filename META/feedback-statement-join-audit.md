# Feedback Statement Join Audit

生成时间：`2026-06-12T16:03:27Z`

## 1. Join 结果

| 指标 | 数量 | 占比 |
|---|---:|---:|
| 成功 join | 0 | 0.0% |
| 失败 join | 592 | 100.0% |

## 2. 失败原因分类

| Join Code | 含义 | 数量 | 占比 |
|---|---|---:|---:|
| JOIN_A | statement_id 不存在或仅有 needs_mapping_repair record | 162 | 27.36% |
| JOIN_B | statement_id 格式变化 | 0 | 0.0% |
| JOIN_C | feedback 未记录 statement_id | 430 | 72.64% |
| JOIN_D | statement_records 与反馈来自不同版本报告 | 0 | 0.0% |
| JOIN_E | 其他 | 0 | 0.0% |
