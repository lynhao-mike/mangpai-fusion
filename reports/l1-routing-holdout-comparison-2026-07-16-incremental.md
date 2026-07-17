# L1 可学习路由留出集对照

**门禁结论：HOLD**

## 来源与证据等级
- 正式能力基线：[`META/six-month-capability-baseline-2026-07-16-incremental.json`](../META/six-month-capability-baseline-2026-07-16-incremental.json)
- 正式 L1 审计：[`META/l1-routing-holdout-audit-2026-07-16-incremental.json`](../META/l1-routing-holdout-audit-2026-07-16-incremental.json)
- 最小来源身份与摘要：[`META/historical-incremental-evidence-manifest-2026-07-16.json`](../META/historical-incremental-evidence-manifest-2026-07-16.json)
- freeze hash：`b5d09f6e5ec49e061c865d8f4a4ec3d934293cb0f6d5adfb98107c78aa478f68`
- Task 8 scores artifact digest：`sha256:41f8971d09dbe2952237abe46d6a095f734d1ebe0c9cb70d44e19f61341ba9a8`
- 数据证据等级：historical blind candidate；不是 prospective/E3。
- 本审计摘要：`sha256:13df1152f570749068183ec1894d3634cd1e4362e2f90ce252dd300cccc2718b`

## 无泄漏 subject 切分
- subject identity：`sex_marker + four_pillars`
- 训练案例：3
- 留出案例：1
- holdout fraction：0.25
- 固定切分盐：`historical-incremental-l1-routing-2026-07-16-v1`
- 训练能力快照：`cap-train-b295f0f5f1e78dbd668a`，仅由训练 case IDs 构造并绑定 Task 8 freeze hash。

## static baseline 来源与映射
来源：`mapping/school-capability-runner-coverage-v1.yaml`。映射不是 learned 训练结果反写。

| 任务 | static school |
|---|---|
| career.change_window | ren |
| career.path_type | duan |
| career.role_change | ziping |
| marriage.event_window | ren |

## 按任务竞争覆盖
- 留出可评分 case/task：2
- 多派竞争 case/task：1（最低门槛 5）
- claim 与有标签、按协议产生 utility 的 abstain 可参与；unsupported / utility=None 不参与。

| 任务 | 多派竞争数 |
|---|---:|
| marriage.event_window | 1 |

## learned/static 选择与留出效用
- 可比较记录：2
- 选择变化：0
- static 平均效用：-0.1000
- learned 平均效用：-0.1000

| case | task | static | learned | static utility | learned utility |
|---|---|---|---|---:|---:|
| P-2026-067-乾-壬戌癸丑癸卯己未 | career.path_type | duan | duan | -0.1000 | -0.1000 |
| P-2026-067-乾-壬戌癸丑癸卯己未 | marriage.event_window | ren | ren | -0.1000 | -0.1000 |

## 标签分布
| 任务 | 正例 | 负例 | 其他类别 |
|---|---:|---:|---:|
| career.path_type | 0 | 0 | 1 |
| marriage.event_window | 0 | 0 | 3 |

## 校准与高风险检查
- calibration status：`insufficient`；样本数 0；static/learned Brier：None / None。
- 高风险 status：`insufficient`；可评估记录 0；static/learned 假阳性 0 / 0。
- task × prototype 稳定增量切片：0。

## 门禁依据
- 同案同任务多流派可评分竞争样本不足：1 < 5。
- learned 与 static 选择完全相同。
- 留出标签缺少正负例或为单一类别：career.path_type, marriage.event_window。
- 校准样本不足，calibration_status=insufficient。
- 高风险任务不可评估。
- 没有 task × prototype 稳定增量证据。
- 可比较留出案例不足：1 < 5。

## 治理结论
结论为 **HOLD**。本审计不修改 `routing_mode`、默认路由、生产权重、runner、规则或评分算法。
