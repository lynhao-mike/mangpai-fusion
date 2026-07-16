# 学派能力暂定能力基线

## 1. 评估范围与证据等级
本报告区分弱先验、历史盲评证据与未来前瞻证据；当前结果仅是可复核基线。

## 2. 案例可用性与污染盘点
- historical_blind_candidate: 4

## 3. 任务覆盖与三态输出
输出状态为 claim / abstain / unsupported；缺失输出不得视为错误预测。

## 4. 六维条件切片下的五维能力基线
在 school / task / chart prototype / claim type / time horizon / evidence completeness 六维条件切片下，按覆盖、区分度、准确度、校准与增量收益五个能力指标观察，不合成为生产权重。
详细后验仅在下一节展示，避免重复发布。

## 5. 四组增量实验
- baseline_plus_school:ditiansui: 0.750
- baseline_plus_school:duan: 0.750
- baseline_plus_school:gao: 0.750
- baseline_plus_school:ren: 0.750
- baseline_plus_school:yang: 0.750
- baseline_plus_school:ziping: 0.750

## 6. 条件化能力后验
- ditiansui/career.role_change: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- ditiansui/career.role_change: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- ditiansui/marriage.divorce_or_remarriage: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- ditiansui/marriage.divorce_or_remarriage: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- ditiansui/wealth.debt: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- ditiansui/wealth.debt: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- duan/career.role_change: coverage=1.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- duan/career.role_change: coverage=1.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- duan/marriage.divorce_or_remarriage: coverage=1.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- duan/marriage.divorce_or_remarriage: coverage=1.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- duan/wealth.debt: coverage=1.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- duan/wealth.debt: coverage=1.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- gao/career.role_change: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- gao/career.role_change: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- gao/marriage.divorce_or_remarriage: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- gao/marriage.divorce_or_remarriage: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- gao/wealth.debt: coverage=1.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- gao/wealth.debt: coverage=1.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- ren/career.role_change: coverage=1.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- ren/career.role_change: coverage=1.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- ren/marriage.divorce_or_remarriage: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- ren/marriage.divorce_or_remarriage: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- ren/wealth.debt: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- ren/wealth.debt: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- yang/career.role_change: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- yang/career.role_change: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- yang/marriage.divorce_or_remarriage: coverage=1.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- yang/marriage.divorce_or_remarriage: coverage=1.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- yang/wealth.debt: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- yang/wealth.debt: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- ziping/career.role_change: coverage=1.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- ziping/career.role_change: coverage=1.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- ziping/marriage.divorce_or_remarriage: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- ziping/marriage.divorce_or_remarriage: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- ziping/wealth.debt: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B
- ziping/wealth.debt: coverage=0.000, discrimination=0.000, accuracy=0.000, calibration=None, incremental_gain=0.000, posterior=0.500, interval=[0.000, 1.000], N_eff=0, evidence=B

## 7. 校准与高风险误差
高风险误报需单独审查；低样本校准值不得外推。

## 8. 样本与证据限制
历史报告、已知反馈与规则开发材料可能造成标签泄漏；污染案例不得作为盲评证据。
初始样本不能证明稳定专长，结论必须由独立前瞻样本证伪或复现。

## 9. 评估门禁建议
**HOLD**
缺少完整、显式、可复核的 gate evidence 时一律 HOLD；正式出口仅允许人工复核、停止或保持。
