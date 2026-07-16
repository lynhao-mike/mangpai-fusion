# 学派能力历史隔离增量基线（2026-07-16）

## 判定摘要
- **artifact validity**：GO；阶段 A 冻结哈希、阶段 B 标签绑定、评分摘要与制品摘要均已校验。本处 GO 只表示本轮历史隔离基线链有效。
- **capability evidence**：形成 36 个非空后验切片；宽区间、低样本或单类标签仍须按 HOLD 理解。
- **routing readiness**：**HOLD**；本任务不运行 learned/static 门禁，也不切换默认路由。
- **prospective evidence**：本批仍为 historical_blind_candidate，重冻不会升级为 prospective 或 E3。
- coverage_complete
- calibration_acceptable
- incremental_non_negative
- high_risk_safe

## 增量范围
- 父冻结案例：64。
- 当前去重案例：75。
- 新增案例：11，ID：P-2026-066-坤-丙寅辛卯壬子丁未, P-2026-067-乾-壬戌癸丑癸卯己未, P-2026-068-乾-己酉丁卯庚戌丁丑, P-2026-069-乾-己未丁丑戊子壬戌, P-2026-070-乾-戊寅丁巳甲寅戊辰, P-2026-071-坤-丁卯甲辰辛丑辛卯, P-2026-072-坤-己巳甲戌戊申壬子, P-2026-073-乾-戊申己未乙未庚辰, P-2026-074-坤-乙卯戊子戊戌癸亥, P-2026-075-乾-戊辰辛酉乙丑丙戌, P-2026-076-乾-丁巳辛亥戊戌己未。

## 数据来源与历史隔离属性
- 命盘输入来自既有历史汇总并保持原去重结果；预测阶段只消费 case identity、性别、四柱、出生时间、大运、任务目录和规则快照。
- 标签只来自 2026-07-16 已公开历史反馈的保守低歧义标签，未新增标签、负例或 prospective 身份。
- **历史反馈早于当前六来源 runner 预测**；本次只是用新 runner 重冻历史输入，不是真实前瞻盲测。
- freeze hash：`3abc2223f90116f5778eb5b2b360580c0a83125fb6747052a0ceedf64ba98ab7`
- artifact digest：`sha256:242ee77d271da0b005e0d86dce51c77843a31aa8d6735e5a46f55cae55d17cf4`

## 六来源 × 十任务三态覆盖
| 学派 | 任务 | claim | abstain | unsupported |
|---|---|---:|---:|---:|
| ziping | structure.overview | 4 | 0 | 0 |
| ziping | career.role_change | 0 | 4 | 0 |
| ziping | marriage.divorce_or_remarriage | 0 | 0 | 4 |
| ziping | wealth.debt | 0 | 0 | 4 |
| ziping | career.path_type | 0 | 0 | 4 |
| ziping | health.system_risk | 0 | 0 | 4 |
| ziping | career.change_window | 0 | 0 | 4 |
| ziping | marriage.event_window | 0 | 0 | 4 |
| ziping | health.event_window | 0 | 0 | 4 |
| ziping | wealth.major_loss_window | 0 | 0 | 4 |
| ditiansui | structure.overview | 3 | 1 | 0 |
| ditiansui | career.role_change | 0 | 0 | 4 |
| ditiansui | marriage.divorce_or_remarriage | 0 | 0 | 4 |
| ditiansui | wealth.debt | 0 | 0 | 4 |
| ditiansui | career.path_type | 0 | 0 | 4 |
| ditiansui | health.system_risk | 0 | 0 | 4 |
| ditiansui | career.change_window | 0 | 0 | 4 |
| ditiansui | marriage.event_window | 0 | 0 | 4 |
| ditiansui | health.event_window | 0 | 0 | 4 |
| ditiansui | wealth.major_loss_window | 0 | 0 | 4 |
| duan | structure.overview | 0 | 0 | 4 |
| duan | career.role_change | 0 | 4 | 0 |
| duan | marriage.divorce_or_remarriage | 3 | 1 | 0 |
| duan | wealth.debt | 0 | 4 | 0 |
| duan | career.path_type | 0 | 4 | 0 |
| duan | health.system_risk | 0 | 0 | 4 |
| duan | career.change_window | 0 | 4 | 0 |
| duan | marriage.event_window | 0 | 4 | 0 |
| duan | health.event_window | 0 | 4 | 0 |
| duan | wealth.major_loss_window | 0 | 4 | 0 |
| ren | structure.overview | 0 | 0 | 4 |
| ren | career.role_change | 0 | 4 | 0 |
| ren | marriage.divorce_or_remarriage | 0 | 0 | 4 |
| ren | wealth.debt | 0 | 0 | 4 |
| ren | career.path_type | 0 | 0 | 4 |
| ren | health.system_risk | 0 | 0 | 4 |
| ren | career.change_window | 0 | 4 | 0 |
| ren | marriage.event_window | 0 | 4 | 0 |
| ren | health.event_window | 0 | 4 | 0 |
| ren | wealth.major_loss_window | 0 | 4 | 0 |
| gao | structure.overview | 0 | 0 | 4 |
| gao | career.role_change | 0 | 0 | 4 |
| gao | marriage.divorce_or_remarriage | 0 | 0 | 4 |
| gao | wealth.debt | 2 | 2 | 0 |
| gao | career.path_type | 0 | 0 | 4 |
| gao | health.system_risk | 0 | 4 | 0 |
| gao | career.change_window | 0 | 4 | 0 |
| gao | marriage.event_window | 0 | 4 | 0 |
| gao | health.event_window | 0 | 4 | 0 |
| gao | wealth.major_loss_window | 0 | 4 | 0 |
| yang | structure.overview | 0 | 0 | 4 |
| yang | career.role_change | 0 | 0 | 4 |
| yang | marriage.divorce_or_remarriage | 2 | 2 | 0 |
| yang | wealth.debt | 0 | 0 | 4 |
| yang | career.path_type | 0 | 0 | 4 |
| yang | health.system_risk | 0 | 0 | 4 |
| yang | career.change_window | 0 | 0 | 4 |
| yang | marriage.event_window | 0 | 0 | 4 |
| yang | health.event_window | 0 | 0 | 4 |
| yang | wealth.major_loss_window | 0 | 0 | 4 |

覆盖增加、Claim 数量或规则数量不等于准确率提升。

## 非空后验及可信区间
| 学派 | 任务 | 证据完整度 | N_eff | 后验均值 | 95% CI |
|---|---|---|---:|---:|---|
| ditiansui | career.role_change | complete | 0.000 | 0.500 | [0.000, 1.000] |
| ditiansui | career.role_change | partial | 0.000 | 0.500 | [0.000, 1.000] |
| ditiansui | marriage.divorce_or_remarriage | complete | 0.000 | 0.500 | [0.000, 1.000] |
| ditiansui | marriage.divorce_or_remarriage | partial | 0.000 | 0.500 | [0.000, 1.000] |
| ditiansui | wealth.debt | complete | 0.000 | 0.500 | [0.000, 1.000] |
| ditiansui | wealth.debt | partial | 0.000 | 0.500 | [0.000, 1.000] |
| duan | career.role_change | complete | 0.000 | 0.500 | [0.000, 1.000] |
| duan | career.role_change | partial | 0.000 | 0.500 | [0.000, 1.000] |
| duan | marriage.divorce_or_remarriage | complete | 0.000 | 0.500 | [0.000, 1.000] |
| duan | marriage.divorce_or_remarriage | partial | 0.000 | 0.500 | [0.000, 1.000] |
| duan | wealth.debt | complete | 0.000 | 0.500 | [0.000, 1.000] |
| duan | wealth.debt | partial | 0.000 | 0.500 | [0.000, 1.000] |
| gao | career.role_change | complete | 0.000 | 0.500 | [0.000, 1.000] |
| gao | career.role_change | partial | 0.000 | 0.500 | [0.000, 1.000] |
| gao | marriage.divorce_or_remarriage | complete | 0.000 | 0.500 | [0.000, 1.000] |
| gao | marriage.divorce_or_remarriage | partial | 0.000 | 0.500 | [0.000, 1.000] |
| gao | wealth.debt | complete | 0.000 | 0.500 | [0.000, 1.000] |
| gao | wealth.debt | partial | 0.000 | 0.500 | [0.000, 1.000] |
| ren | career.role_change | complete | 0.000 | 0.500 | [0.000, 1.000] |
| ren | career.role_change | partial | 0.000 | 0.500 | [0.000, 1.000] |
| ren | marriage.divorce_or_remarriage | complete | 0.000 | 0.500 | [0.000, 1.000] |
| ren | marriage.divorce_or_remarriage | partial | 0.000 | 0.500 | [0.000, 1.000] |
| ren | wealth.debt | complete | 0.000 | 0.500 | [0.000, 1.000] |
| ren | wealth.debt | partial | 0.000 | 0.500 | [0.000, 1.000] |
| yang | career.role_change | complete | 0.000 | 0.500 | [0.000, 1.000] |
| yang | career.role_change | partial | 0.000 | 0.500 | [0.000, 1.000] |
| yang | marriage.divorce_or_remarriage | complete | 0.000 | 0.500 | [0.000, 1.000] |
| yang | marriage.divorce_or_remarriage | partial | 0.000 | 0.500 | [0.000, 1.000] |
| yang | wealth.debt | complete | 0.000 | 0.500 | [0.000, 1.000] |
| yang | wealth.debt | partial | 0.000 | 0.500 | [0.000, 1.000] |
| ziping | career.role_change | complete | 0.000 | 0.500 | [0.000, 1.000] |
| ziping | career.role_change | partial | 0.000 | 0.500 | [0.000, 1.000] |
| ziping | marriage.divorce_or_remarriage | complete | 0.000 | 0.500 | [0.000, 1.000] |
| ziping | marriage.divorce_or_remarriage | partial | 0.000 | 0.500 | [0.000, 1.000] |
| ziping | wealth.debt | complete | 0.000 | 0.500 | [0.000, 1.000] |
| ziping | wealth.debt | partial | 0.000 | 0.500 | [0.000, 1.000] |

## 四组增量实验摘要
- `baseline_plus_school:ditiansui`：0.750000
- `baseline_plus_school:duan`：0.750000
- `baseline_plus_school:gao`：0.750000
- `baseline_plus_school:ren`：0.750000
- `baseline_plus_school:yang`：0.750000
- `baseline_plus_school:ziping`：0.750000

增量只表示同一历史标签集上的评估差异；runner 增加不会自动构成能力提升。

## 高风险假阳性与不可评估项
- 高风险假阳性分类数：0。
- 未达到 A 级与双审要求的高风险标签保持不可评分；没有把门槛降级。
- 无标签、只有正例、缺逐年流年或校准样本不足的切片保持 HOLD。

## 失败分类
- `calibration_insufficient`：36
- `high_risk_unassessable`：120
- `leakage` 一旦非零应整批 STOP；本轮最终制品要求其为零。

## 与 2026-07-14 基线的可比变化
- 旧基线只冻结 ziping/ren 与更广的 19 任务矩阵；本轮按唯一目录筛选十任务并扩展为六来源。
- 本轮新增 runner 的三态覆盖只说明可执行范围变化，不自动说明准确率、校准或生产效用提升。
- 标签仍主要覆盖既有职业与婚恋事件任务；Tasks 3—5 新增高风险任务缺少合格人工标签，不能进行能力升级声明。

## 标签与输入限制
- 不补造负例，因此部分任务只有正例，缺少判别力。
- 历史输入没有逐年流年序列；任/段 timing runner 的 abstain 属于正确克制，但使应期任务不可评估。
- 出生时间或大运缺失的案例保留在矩阵中并进入 input_completeness/partial 记录，没有删除异常样本改善分数。

## Prospective 状态
- NOT_APPLICABLE_HISTORICAL_INCREMENT；本批为历史增量，不是前瞻样本。
- 旧 bundle hash：`not-applicable`；旧规则身份：`not-applicable`，未静默改写。
- 下一批 intake 模板：`use META/prospective-intake-protocol-v1.md`
- 下一批 bundle 模板：`use the prospective blind bundle workflow`

## 下一不可逆决策
**不能由 Task 8 直接进入生产路由或宣称 Task 9 已 GO。** 当前 routing readiness 为 HOLD；只有后续获得真实竞争覆盖、负例判别力、可评估高风险任务和足够校准样本后，才可单独执行 Task 9 learned/static 留出竞争。
