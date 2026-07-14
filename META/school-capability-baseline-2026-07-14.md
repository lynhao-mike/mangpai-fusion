# 学派能力历史隔离基线（2026-07-14）

## 判定
**GO — 非空概率后验已形成，Phase 0 数据地基验收通过。**

## 数据与冻结
- 冻结案例：64
- 可评分历史隔离案例：39
- 未抽取到保守标签案例：25
- 结构化标签：66
- 冻结输出：2432
- 冻结完整性：已验证（freeze_hash=75c02fef...）

## 三态能力覆盖
- 产生命题（claim）：121
- 克制不判（abstain）：199
- 当前不支持（unsupported）：2112

## 六维能力后验（非空切片）

| 流派 | 任务 | 证据带 | N_eff | 后验均值 | 95% CI |
|---|---|---|---|---|---|
| ziping | career.role_change | complete | 5.0 | 0.857 | [0.615, 1.000] |
| ziping | career.role_change | partial | 2.0 | 0.750 | [0.370, 1.000] |

## GO 达标证据
- ≥30 案例有完整结构化标注：39 案 ✓
- 污染案例标为 development_only：25 案 ✓
- 评估框架产出非空 posterior：2 切片，max N_eff=5.0 ✓
- 至少一个任务从 Fact 追溯到 Claim → Prediction → Score：ziping/career.role_change ✓
- 报告不泄露内部 ID ✓

## 能力陈述（保守）
子平流派对"显著职业角色变化"（career.role_change）任务，在四柱食伤制杀结构与官杀混局信号下，初步后验均值 0.857（CI 宽）。这仅代表初始 5 个有效样本的观察结果，不构成稳定专长证据，需更多独立样本收敛。

## 限制与风险
- 后验区间宽，不应用于生产调权
- 其他 17 项任务仍为 unsupported/abstain，覆盖极为有限
- 本批为历史隔离盲测，非真实前瞻新案
- binary claim 概率固定为 0.65，尚未接入学习调整
- 仅子平一派产出 binary claim，任派缺逐年流年数据

## 后续路径
1. 补充逐年流年信息使任派 time_window 任务可产出 timing claim
2. 扩展 marriage.late_marriage 标签覆盖（当前仅 1 条）
3. 积累至 N_eff ≥ 10 后再考虑回流 L1 路由
4. 收集真实前瞻新案进一步验证泛化能力
