# Phase-1000 Learnable Sample Audit

生成时间：`2026-06-12T15:52:19Z`

## 1. build_learning_samples() 统计

| 指标 | 数量 |
|---|---:|
| feedback rows | 592 |
| learnable | 0 |
| pending | 353 |
| skip | 52 |
| unmapped | 592 |

## 2. Ready Check

| 指标 | 值 |
|---|---|
| recoverable rows | 0 |
| recoverable percent | 0.0% |
| final status | `BLOCKED` |
| reason | recoverable rows = 0；feedback -> statement_record -> rule_id 链仍无可恢复样本 |

## 3. 边界声明

本审计只重建历史映射与学习样本计数；未进入权重学习，未更新 Dynamic Confidence，未修改任何生产规则。
