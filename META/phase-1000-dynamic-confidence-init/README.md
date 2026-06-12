# Phase-1000 动态置信度初始化副本

本目录为只读分析生成物，不修改原始规则库、引擎或 META/project-state.json。

## 文件

- `rule_statement_family_alignment.csv`: feedback 行级 rule_id -> statement_id -> verdict 与 Family / School / Rule Type 对齐副本。
- `family_vote_summary.csv`: family-level 初始权重、cap 与 raw vote 统计。
- `family_lane_mapping.csv`: family 到 School lane / Canon 的初始分布。
- `unmapped_rules_repair_queue.csv`: 未映射或需修复映射的行级队列。
- `dynamic_confidence_init.json`: 便于后续 Phase-1000 / Phase-3000 使用的 JSON 汇总副本。

## 初始化权重

- family_weight: `1.0`
- ziping lane_weight: `0.50`
- tiaohou_ditiansui lane_weight: `0.50`
- 5 个 Canon initial_canon_weight: `0.20`
