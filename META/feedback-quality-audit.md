# P4-1 Feedback Quality Audit（只读审计）

生成时间：2026-06-12T19:43:00+08:00

## 0. 审计边界

- 输入：`META/phase-300-calibration.md`、`META/phase-300-calibration-summary.md`、`META/phase-300-calibration-analysis.md`、`cases/*/feedback.md`。
- 本次只读审计未修改 `theory/*`、`engine/*`、`tests/*`、`META/project-state.json`。
- 由于 Phase-300 产物未提供 rule_id 到单条 feedback verdict 的直接映射，规则 Top20 采用“案例级触发归因”：某案例有 unknown/partial 信号时，将该案例触发的规则按信号数累加；该排行用于定位排查优先级，不等同于规则因果失准排行。

## 1. 总体反馈质量

| 指标 | 值 | 比例 |
|---|---|---|
| 案例数 | 100 | 100.0% |
| 有任一反馈信号案例 | 27 | 27.0% |
| 零反馈案例 | 73 | 73.0% |
| hit | 340 | 54.5% |
| miss | 109 | 17.5% |
| partial | 94 | 15.1% |
| unknown | 81 | 13.0% |

## 2. unknown 来源

| 分类 | 数量 | 占 unknown 比例 |
|---|---|---|
| A. 用户未反馈 | 37 | 45.7% |
| B. 反馈过于模糊 | 0 | 0.0% |
| C. 无法映射到断语 | 0 | 0.0% |
| D. 规则触发但无反馈字段 | 30 | 37.0% |
| E. 反馈格式错误 | 0 | 0.0% |
| F. 其他 | 14 | 17.3% |

## 3. partial 来源

| 分类 | 数量 | 占 partial 比例 |
|---|---|---|
| A. 部分命中 | 0 | 0.0% |
| B. 时间错误 | 91 | 96.8% |
| C. 强度错误 | 3 | 3.2% |
| D. 领域正确但细节错误 | 0 | 0.0% |
| E. 多断语混合 | 0 | 0.0% |

## 4. 最容易产生 unknown 的前 20 条规则（案例级触发归因）

| rule_id | family_id | school | canon | rule_type | unknown_count |
|---|---|---|---|---|---|
| DTS-PROD-20260605-001 | FAM-UNMAPPED-DTS-PROD-20260605-001 | tiaohou_ditiansui | DITIANSUI | EVENT | 81 |
| DTS-PROD-20260605-002 | FAM-UNMAPPED-DTS-PROD-20260605-002 | tiaohou_ditiansui | DITIANSUI | EVENT | 81 |
| DTS-PROD-20260605-003 | FAM-UNMAPPED-DTS-PROD-20260605-003 | tiaohou_ditiansui | DITIANSUI | EVENT | 81 |
| DTS-PROD-20260605-004 | FAM-UNMAPPED-DTS-PROD-20260605-004 | tiaohou_ditiansui | DITIANSUI | EVENT | 81 |
| DTS-PROD-20260605-006 | FAM-UNMAPPED-DTS-PROD-20260605-006 | tiaohou_ditiansui | DITIANSUI | EVENT | 81 |
| DTS-PROD-20260605-008 | FAM-UNMAPPED-DTS-PROD-20260605-008 | tiaohou_ditiansui | DITIANSUI | TIMING | 81 |
| DTS-PROD-20260605-010 | FAM-UNMAPPED-DTS-PROD-20260605-010 | tiaohou_ditiansui | DITIANSUI | EVENT | 81 |
| DTS-PROD-20260605-011 | FAM-UNMAPPED-DTS-PROD-20260605-011 | tiaohou_ditiansui | DITIANSUI | EVENT | 81 |
| DTS-PROD-20260605-012 | FAM-UNMAPPED-DTS-PROD-20260605-012 | tiaohou_ditiansui | DITIANSUI | EVENT | 81 |
| DTS-PROD-20260605-013 | FAM-UNMAPPED-DTS-PROD-20260605-013 | tiaohou_ditiansui | DITIANSUI | EVENT | 81 |
| DTS-PROD-20260605-015 | FAM-UNMAPPED-DTS-PROD-20260605-015 | tiaohou_ditiansui | DITIANSUI | EVENT | 81 |
| DTS-PROD-20260605-017 | FAM-UNMAPPED-DTS-PROD-20260605-017 | tiaohou_ditiansui | DITIANSUI | TIMING | 81 |
| DTS-PROD-20260605-018 | FAM-UNMAPPED-DTS-PROD-20260605-018 | tiaohou_ditiansui | DITIANSUI | GENERAL_PRINCIPLE | 81 |
| DTS-PROD-20260605-019 | FAM-UNMAPPED-DTS-PROD-20260605-019 | tiaohou_ditiansui | DITIANSUI | EVENT | 81 |
| DTS-PROD-20260606-004 | FAM-UNMAPPED-DTS-PROD-20260606-004 | tiaohou_ditiansui | DITIANSUI | EVENT | 81 |
| DTS-PROD-20260606-005 | FAM-UNMAPPED-DTS-PROD-20260606-005 | tiaohou_ditiansui | DITIANSUI | EVENT | 81 |
| DTS-PROD-20260606-006 | FAM-UNMAPPED-DTS-PROD-20260606-006 | tiaohou_ditiansui | DITIANSUI | EVENT | 81 |
| DTS-PROD-20260606-007 | FAM-UNMAPPED-DTS-PROD-20260606-007 | tiaohou_ditiansui | DITIANSUI | EVENT | 81 |
| DTS-PROD-20260606-008 | FAM-UNMAPPED-DTS-PROD-20260606-008 | tiaohou_ditiansui | DITIANSUI | EVENT | 81 |
| DTS-PROD-20260606-010 | FAM-UNMAPPED-DTS-PROD-20260606-010 | tiaohou_ditiansui | DITIANSUI | TIMING | 81 |

## 5. 最容易产生 partial 的前 20 条规则（案例级触发归因）

| rule_id | family_id | school | canon | rule_type | partial_count |
|---|---|---|---|---|---|
| DTS-PROD-20260605-001 | FAM-UNMAPPED-DTS-PROD-20260605-001 | tiaohou_ditiansui | DITIANSUI | EVENT | 94 |
| DTS-PROD-20260605-002 | FAM-UNMAPPED-DTS-PROD-20260605-002 | tiaohou_ditiansui | DITIANSUI | EVENT | 94 |
| DTS-PROD-20260605-003 | FAM-UNMAPPED-DTS-PROD-20260605-003 | tiaohou_ditiansui | DITIANSUI | EVENT | 94 |
| DTS-PROD-20260605-004 | FAM-UNMAPPED-DTS-PROD-20260605-004 | tiaohou_ditiansui | DITIANSUI | EVENT | 94 |
| DTS-PROD-20260605-006 | FAM-UNMAPPED-DTS-PROD-20260605-006 | tiaohou_ditiansui | DITIANSUI | EVENT | 94 |
| DTS-PROD-20260605-008 | FAM-UNMAPPED-DTS-PROD-20260605-008 | tiaohou_ditiansui | DITIANSUI | TIMING | 94 |
| DTS-PROD-20260605-010 | FAM-UNMAPPED-DTS-PROD-20260605-010 | tiaohou_ditiansui | DITIANSUI | EVENT | 94 |
| DTS-PROD-20260605-011 | FAM-UNMAPPED-DTS-PROD-20260605-011 | tiaohou_ditiansui | DITIANSUI | EVENT | 94 |
| DTS-PROD-20260605-012 | FAM-UNMAPPED-DTS-PROD-20260605-012 | tiaohou_ditiansui | DITIANSUI | EVENT | 94 |
| DTS-PROD-20260605-013 | FAM-UNMAPPED-DTS-PROD-20260605-013 | tiaohou_ditiansui | DITIANSUI | EVENT | 94 |
| DTS-PROD-20260605-015 | FAM-UNMAPPED-DTS-PROD-20260605-015 | tiaohou_ditiansui | DITIANSUI | EVENT | 94 |
| DTS-PROD-20260605-017 | FAM-UNMAPPED-DTS-PROD-20260605-017 | tiaohou_ditiansui | DITIANSUI | TIMING | 94 |
| DTS-PROD-20260605-018 | FAM-UNMAPPED-DTS-PROD-20260605-018 | tiaohou_ditiansui | DITIANSUI | GENERAL_PRINCIPLE | 94 |
| DTS-PROD-20260605-019 | FAM-UNMAPPED-DTS-PROD-20260605-019 | tiaohou_ditiansui | DITIANSUI | EVENT | 94 |
| DTS-PROD-20260606-004 | FAM-UNMAPPED-DTS-PROD-20260606-004 | tiaohou_ditiansui | DITIANSUI | EVENT | 94 |
| DTS-PROD-20260606-005 | FAM-UNMAPPED-DTS-PROD-20260606-005 | tiaohou_ditiansui | DITIANSUI | EVENT | 94 |
| DTS-PROD-20260606-006 | FAM-UNMAPPED-DTS-PROD-20260606-006 | tiaohou_ditiansui | DITIANSUI | EVENT | 94 |
| DTS-PROD-20260606-007 | FAM-UNMAPPED-DTS-PROD-20260606-007 | tiaohou_ditiansui | DITIANSUI | EVENT | 94 |
| DTS-PROD-20260606-008 | FAM-UNMAPPED-DTS-PROD-20260606-008 | tiaohou_ditiansui | DITIANSUI | EVENT | 94 |
| DTS-PROD-20260606-010 | FAM-UNMAPPED-DTS-PROD-20260606-010 | tiaohou_ditiansui | DITIANSUI | TIMING | 94 |

## 6. 五类规则反馈率

说明：EVENT/TIMING 使用案例表显式计数；STRUCTURE/GENERAL_PRINCIPLE/ANTI_PATTERN 使用 Phase-300 summary 的 raw type distribution 对剩余 raw votes 做比例分摊。

| rule_type | hit率 | miss率 | partial率 | unknown率 |
|---|---|---|---|---|
| EVENT | 54.6% (79.5) | 17.5% (25.4) | 15.0% (21.8) | 13.0% (18.9) |
| TIMING | 54.4% (20.9) | 17.5% (6.7) | 15.2% (5.8) | 13.0% (5.0) |
| STRUCTURE | 54.5% (157.4) | 17.5% (50.5) | 15.1% (43.6) | 13.0% (37.5) |
| GENERAL_PRINCIPLE | 54.5% (64.8) | 17.5% (20.8) | 15.1% (18.0) | 13.0% (15.5) |
| ANTI_PATTERN | 54.5% (17.4) | 17.5% (5.6) | 15.1% (4.8) | 13.0% (4.1) |

## 7. 动态置信度系统是否真正具备学习条件

**NO**

原因：

1. 样本触发不真实：100% fallback 触发，不能代表主引擎运行时规则命中分布。
2. 反馈覆盖不足：仅 27% 案例有任一反馈信号，73% 案例无有效反馈。
3. 非确定信号过高：partial + unknown = 175/624 = 28.0%，且子类语义未被摄入模型区分。
4. 规则级因果链断裂：现有产物没有稳定暴露 rule_id → statement_id → feedback verdict 映射，不能安全更新单条规则后验。
5. 格式不统一：旧 feedback、v1.3 feedback、pending、空字段与 known_facts 混杂，机器学习入口会把“未反馈/不可判定”误当成规则证据。

## 8. Phase-1000 的真正阻塞项 TOP10

1. 100/100 案例均为 fallback_yaml_trigger，且 fallback 原因为 ModuleNotFoundError('No module named tools')，当前不是主 pipeline 的真实触发分布。
2. 有效反馈案例仅 27/100，73/100 为 0/0/0/0，低于进入动态学习所需的最低覆盖门槛。
3. 反馈总量 624 中 unknown=81、partial=94，非确定信号合计 175，占 28.0%，会污染 Beta/后验更新。
4. 反馈格式混用：v1.3 [y/n/?/skip]、旧表格、emoji、pending、空 [ ] 并存，机器摄入一致性不足。
5. rule_id / statement_id / feedback verdict 未形成稳定一一映射，规则级 Top20 只能做案例触发归因，不能做真实因果降权。
6. partial 未拆入时间、强度、领域细节、多断语混合等子类，现有系统容易把可修正规则当成半错规则。
7. unknown 主要来自未反馈、空字段与无法映射，而非规则本身失效；直接降权会误伤高触发基础规则。
8. 调候滴天髓 raw vote 占 80.9%，子平仅 19.1%，若不先做 school-lane 与 family-cap 校正，学习会被规则密度支配。
9. 高重复家族 FAM-011/FAM-018/FAM-010/FAM-004 尚需治理，否则 Phase-1000 会放大重复证据。
10. 报告归档、反馈入口、statement_index 缺失或滞后案例仍存在，闭环追踪链条未完全稳定。

## 9. 机器可读摘要

```json
{
  "case_count": 100,
  "feedback_cases": 27,
  "zero_feedback_cases": 73,
  "totals": {
    "hit": 340,
    "miss": 109,
    "partial": 94,
    "unknown": 81
  },
  "unknown_sources": {
    "D. 规则触发但无反馈字段": 30,
    "A. 用户未反馈": 37,
    "F. 其他": 14
  },
  "partial_sources": {
    "B. 时间错误": 91,
    "C. 强度错误": 3
  },
  "learning_ready": "NO",
  "methodology_note": "rule Top20 uses case-level trigger attribution because rule_id→statement_id→feedback verdict mapping is absent in Phase-300 artifacts"
}
```
