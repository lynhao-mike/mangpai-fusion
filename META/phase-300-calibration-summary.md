# Phase-300 Calibration Summary

生成时间：`2026-06-12T11:16:51+00:00`  
案例数：`100`

## 1. Raw→Family→Canon→School 压缩率

| 层级 | 总量 | 相对 Raw | 说明 |
|---|---|---|---|
| Raw Rule Votes | 24310 | 100.0% | 原始触发规则数 |
| Family groups | 20240 | 83.3% | case × school × canon × family 分组数 |
| Family Votes | 22451 | 92.4% | Shared Evidence + Family Cap 后票数 |
| Canon Main Votes | 17256 | 71.0% | 仅 EVENT/STRUCTURE 主票进入 Canon 主口径 |
| School lanes | 200 | 0.8% | ziping/tiaohou_ditiansui 双 lane 归一化槽位 |

## 2. 重复票压缩率

| 指标 | 值 |
|---|---|
| raw_total | 24310 |
| family_vote_total | 22451 |
| duplicate_or_cap_compressed | 1859 |
| duplicate_compression_rate | 7.6% |

## 3. EVENT / TIMING 覆盖率

| 指标 | 案例数/票数 | 覆盖率 |
|---|---|---|
| EVENT case coverage | 100 | 100.0% |
| TIMING case coverage | 100 | 100.0% |
| EVENT raw hits | 5473 | 22.5% |
| TIMING raw hits | 1605 | 6.6% |

## 4. 分布统计

| 维度 | 分布 |
|---|---|
| trigger_mode | fallback_yaml_trigger:100 |
| Rule Type | ANTI_PATTERN:1248, EVENT:5473, GENERAL_PRINCIPLE:4663, STRUCTURE:11321, TIMING:1605 |
| Canon | DITIANSUI:3444, DITIANSUI_CHANWEI:16218, QIONGTONG_BAOJIAN:2326, SANMING_TONGHUI:925, ZIPING_ZHENQUAN:1397 |
| School | tiaohou_ditiansui:19662, ziping:4648 |

## 5. 反馈闭环数据

| 反馈信号 | 计数 |
|---|---|
| hit | 340 |
| miss | 109 |
| partial | 94 |
| unknown | 81 |

## 6. 校准口径备注

- Raw Rule Votes 仅用于诊断，不直接进入最终权重。
- Family Votes 先合并 Shared Evidence Keys，再按 Family Cap 压缩。
- Canon Vote 使用 Phase-300 初始 `0.20/Canon`。
- School Vote 在 `ziping` 与 `tiaohou_ditiansui` 各自 lane 内归一化，初始 prior 均为 `0.50`。
- `GENERAL_PRINCIPLE` 与 `ANTI_PATTERN` 计为辅助/解释/veto 数据，不作正向主票。
