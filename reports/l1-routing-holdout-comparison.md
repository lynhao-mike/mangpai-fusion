# L1 可学习路由留出集对照

**门禁结论：HOLD**

## 来源与证据等级
- Task 8 制品：`META/six-month-capability-baseline-2026-07-15.json`
- freeze hash：`5f2cff073152a6a09146f6465db8ce825732481ab42c4ba878ebad7c8faa01c9`
- artifact digest：`sha256:e881231bde38e0c78728e1bbbb6dbf0ab6f7aa79bff4bdd232bda256c64cff61`
- 数据证据等级：historical blind candidate；不是 prospective/E3。
- 本审计摘要：`sha256:781edb8dbeedac7a565d829b300c529ce4d0dfa38f08368a07465abaccadb834`

## 无泄漏 subject 切分
- subject identity：`sex_marker + four_pillars`
- 训练案例：25
- 留出案例：8
- holdout fraction：0.25
- 固定切分盐：`six-month-l1-routing-v1`
- 训练能力快照：`cap-train-56aea7c0e71b3d5cf7d5`，仅由训练 case IDs 构造并绑定 Task 8 freeze hash。

## static baseline 来源与映射
来源：`mapping/school-capability-runner-coverage-v1.yaml`。映射不是 learned 训练结果反写。

| 任务 | static school |
|---|---|
| career.change_window | ren |
| career.path_type | duan |
| career.role_change | ziping |
| marriage.event_window | ren |

## 按任务竞争覆盖
- 留出可评分 case/task：15
- 多派竞争 case/task：9（最低门槛 5）
- claim 与有标签、按协议产生 utility 的 abstain 可参与；unsupported / utility=None 不参与。

| 任务 | 多派竞争数 |
|---|---:|
| career.change_window | 2 |
| career.role_change | 2 |
| marriage.event_window | 5 |

## learned/static 选择与留出效用
- 可比较记录：15
- 选择变化：0
- static 平均效用：-0.1000
- learned 平均效用：-0.1000

| case | task | static | learned | static utility | learned utility |
|---|---|---|---|---:|---:|
| P-2026-006-乾-壬戌辛亥戊戌庚申 | career.path_type | duan | duan | -0.1000 | -0.1000 |
| P-2026-006-乾-壬戌辛亥戊戌庚申 | marriage.event_window | ren | ren | -0.1000 | -0.1000 |
| P-2026-014-坤-乙卯辛巳甲子戊辰 | marriage.event_window | ren | ren | -0.1000 | -0.1000 |
| P-2026-025-乾-癸亥丁巳丙申丁酉 | career.path_type | duan | duan | -0.1000 | -0.1000 |
| P-2026-045-乾-戊午辛酉癸巳甲寅 | career.change_window | ren | ren | -0.1000 | -0.1000 |
| P-2026-045-乾-戊午辛酉癸巳甲寅 | career.path_type | duan | duan | -0.1000 | -0.1000 |
| P-2026-045-乾-戊午辛酉癸巳甲寅 | career.role_change | ziping | ziping | -0.1000 | -0.1000 |
| P-2026-045-乾-戊午辛酉癸巳甲寅 | marriage.event_window | ren | ren | -0.1000 | -0.1000 |
| P-2026-048-乾-庚戌戊子辛卯庚寅 | career.path_type | duan | duan | -0.1000 | -0.1000 |
| P-2026-051-乾-庚申丁亥辛丑己亥 | career.change_window | ren | ren | -0.1000 | -0.1000 |
| P-2026-051-乾-庚申丁亥辛丑己亥 | career.path_type | duan | duan | -0.1000 | -0.1000 |
| P-2026-051-乾-庚申丁亥辛丑己亥 | career.role_change | ziping | ziping | -0.1000 | -0.1000 |
| P-2026-051-乾-庚申丁亥辛丑己亥 | marriage.event_window | ren | ren | -0.1000 | -0.1000 |
| P-2026-063-乾-壬戌庚戌辛巳壬辰 | career.path_type | duan | duan | -0.1000 | -0.1000 |
| P-2026-065-乾-丁卯壬寅壬辰甲辰 | marriage.event_window | ren | ren | -0.1000 | -0.1000 |

## 标签分布
| 任务 | 正例 | 负例 | 其他类别 |
|---|---:|---:|---:|
| career.change_window | 0 | 0 | 4 |
| career.path_type | 0 | 0 | 6 |
| career.role_change | 0 | 0 | 6 |
| marriage.event_window | 0 | 0 | 10 |

## 校准与高风险检查
- calibration status：`insufficient`；样本数 0；static/learned Brier：None / None。
- 高风险 status：`insufficient`；可评估记录 0；static/learned 假阳性 0 / 0。
- task × prototype 稳定增量切片：0。

## 门禁依据
- learned 与 static 选择完全相同。
- 留出标签缺少正负例或为单一类别：career.change_window, career.path_type, career.role_change, marriage.event_window。
- 校准样本不足，calibration_status=insufficient。
- 高风险任务不可评估。
- 没有 task × prototype 稳定增量证据。
- learned 路由与静态基线选择完全相同，尚未证明条件化路由增量。

## 治理结论
结论为 **HOLD**。本审计不修改 `routing_mode`、默认路由、生产权重、runner、规则或评分算法。
