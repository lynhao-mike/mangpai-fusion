# Historical Mapping Recovery Report

生成时间：`2026-06-12T15:52:19Z`

## 1. 恢复链路

```text
feedback row -> statement_id -> statement_record -> rule_id
```

## 2. 统计

| 指标 | 数量 |
|---|---:|
| feedback rows | 592 |
| recoverable rows | 0 |
| unrecoverable rows | 592 |
| recoverable percent | 0.0% |

## 3. 不可恢复原因分布

| 原因 | 数量 |
|---|---:|
| statement_record_missing | 474 |
| statement_record_needs_mapping_repair | 118 |

## 4. 明细产物

- 迁移日志：`META/historical-statement-record-migration-log.json`
