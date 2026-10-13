# P 系列任职/经营盲断 Harness 审计报告

> 分类：历史案例的标签隔离回放基线，不是前瞻盲测；不得据此宣称已获得真实新案例盲断能力。

## 隔离与冻结

- 预测 cohort：40 个 case_id；预测阶段只读取 cohort manifest 与 `cases/shuru-input.md` 的性别、四柱和大运受限字段。
- 人工标签在独立 score 阶段才由 `cases/p-series-career-path-labels.jsonl` 揭示；预测代码不读取 `cases/fankui-feedback.md`。
- 冻结预测 SHA256：`e26ca4f76927005cb3e837bef6749618de26ddf7f4b1d035a0c9f383c678a755`。
- 输入 SHA256：`623335912b03d67997d377d0bf9d2233b20ce0bfb84b585ce9c3f1848fc55f53`；受限字段泄漏扫描命中：0。
- 模型：`engine/v5/duan_runner.py::_career_path_type` 的语义适配器；原逻辑的 mixed 分支在本契约中一律转为 abstain，未改写或调参生产规则。

## 严格二分类指标

- 严格可评分样本：37；mixed holdout：3。
- 准确率：29.73%；balanced accuracy：42.50%。
- recall：employment 25.00%；entrepreneurship 60.00%。
- abstain：17；覆盖率：54.05%。
- 多数类基线：32/37 = 86.49%。只预测 employment 即使准确率较高也没有实际区分能力。

| 真值 \ 预测 | employment | entrepreneurship | abstain |
|---|---:|---:|---:|
| employment | 8 | 9 | 15 |
| entrepreneurship | 0 | 3 | 2 |

## 预测类别分布

| 预测 | 数量 |
|---|---:|
| abstain | 20 |
| employment | 8 |
| entrepreneurship | 12 |

## 逐案审计表

| Case | 预测 | 人工真值 | 严格评分 | 命中 | 证据/模型信号 |
|---|---|---|---|---|---|
| P-2026-001 | entrepreneurship | entrepreneurship | 是 | 是 | active_path_count=5; branch_conflict_intensity=0.4166666666666667; employment_score=3; entrepreneurship_score=7; reason=duan_runner_entrepreneurship_trigger |
| P-2026-004 | abstain | employment | 是 | 否 | active_path_count=10; branch_conflict_intensity=0.11666666666666665; employment_score=6; entrepreneurship_score=8; reason=duan_runner_insufficient_advantage |
| P-2026-007 | entrepreneurship | employment | 是 | 否 | active_path_count=5; branch_conflict_intensity=0.11666666666666665; employment_score=3; entrepreneurship_score=6; reason=duan_runner_entrepreneurship_trigger |
| P-2026-008 | abstain | employment | 是 | 否 | active_path_count=3; branch_conflict_intensity=0.0; employment_score=5; entrepreneurship_score=6; reason=duan_runner_insufficient_advantage |
| P-2026-009 | abstain | employment | 是 | 否 | active_path_count=5; branch_conflict_intensity=0.45; employment_score=6; entrepreneurship_score=5; reason=duan_runner_mixed_not_allowed |
| P-2026-011 | abstain | employment | 是 | 否 | active_path_count=3; branch_conflict_intensity=0.3333333333333333; employment_score=3; entrepreneurship_score=5; reason=duan_runner_insufficient_advantage |
| P-2026-013 | entrepreneurship | employment | 是 | 否 | active_path_count=5; branch_conflict_intensity=0.0; employment_score=4; entrepreneurship_score=8; reason=duan_runner_entrepreneurship_trigger |
| P-2026-017 | abstain | employment | 是 | 否 | active_path_count=7; branch_conflict_intensity=0.26666666666666666; employment_score=6; entrepreneurship_score=4; reason=duan_runner_insufficient_advantage |
| P-2026-018 | abstain | employment | 是 | 否 | active_path_count=7; branch_conflict_intensity=0.43333333333333335; employment_score=3; entrepreneurship_score=4; reason=duan_runner_insufficient_advantage |
| P-2026-019 | abstain | employment | 是 | 否 | active_path_count=5; branch_conflict_intensity=0.2333333333333333; employment_score=4; entrepreneurship_score=4; reason=duan_runner_insufficient_advantage |
| P-2026-021 | entrepreneurship | employment | 是 | 否 | active_path_count=6; branch_conflict_intensity=0.11666666666666665; employment_score=0; entrepreneurship_score=7; reason=duan_runner_entrepreneurship_trigger |
| P-2026-023 | abstain | employment | 是 | 否 | active_path_count=4; branch_conflict_intensity=0.43333333333333335; employment_score=7; entrepreneurship_score=5; reason=duan_runner_mixed_not_allowed |
| P-2026-025 | abstain | employment | 是 | 否 | active_path_count=6; branch_conflict_intensity=0.4333333333333333; employment_score=4; entrepreneurship_score=5; reason=duan_runner_mixed_not_allowed |
| P-2026-027 | abstain | employment | 是 | 否 | active_path_count=7; branch_conflict_intensity=0.2833333333333333; employment_score=4; entrepreneurship_score=4; reason=duan_runner_insufficient_advantage |
| P-2026-030 | abstain | employment | 是 | 否 | active_path_count=6; branch_conflict_intensity=0.0; employment_score=5; entrepreneurship_score=7; reason=duan_runner_insufficient_advantage |
| P-2026-031 | entrepreneurship | employment | 是 | 否 | active_path_count=4; branch_conflict_intensity=0.0; employment_score=3; entrepreneurship_score=6; reason=duan_runner_entrepreneurship_trigger |
| P-2026-034 | employment | employment | 是 | 是 | active_path_count=5; branch_conflict_intensity=0.0; employment_score=7; entrepreneurship_score=3; reason=duan_runner_employment_trigger |
| P-2026-035 | entrepreneurship | entrepreneurship | 是 | 是 | active_path_count=5; branch_conflict_intensity=0.2333333333333333; employment_score=3; entrepreneurship_score=7; reason=duan_runner_entrepreneurship_trigger |
| P-2026-037 | entrepreneurship | entrepreneurship | 是 | 是 | active_path_count=4; branch_conflict_intensity=0.0; employment_score=3; entrepreneurship_score=8; reason=duan_runner_entrepreneurship_trigger |
| P-2026-038 | employment | employment | 是 | 是 | active_path_count=1; branch_conflict_intensity=0.11666666666666665; employment_score=7; entrepreneurship_score=3; reason=duan_runner_employment_trigger |
| P-2026-039 | employment | employment | 是 | 是 | active_path_count=5; branch_conflict_intensity=0.11666666666666665; employment_score=6; entrepreneurship_score=1; reason=duan_runner_employment_trigger |
| P-2026-041 | entrepreneurship | employment | 是 | 否 | active_path_count=8; branch_conflict_intensity=0.0; employment_score=3; entrepreneurship_score=7; reason=duan_runner_entrepreneurship_trigger |
| P-2026-045 | abstain | employment | 是 | 否 | active_path_count=8; branch_conflict_intensity=0.26666666666666666; employment_score=7; entrepreneurship_score=5; reason=duan_runner_insufficient_advantage |
| P-2026-046 | employment | employment | 是 | 是 | active_path_count=3; branch_conflict_intensity=0.0; employment_score=8; entrepreneurship_score=4; reason=duan_runner_employment_trigger |
| P-2026-047 | abstain | mixed | 否（mixed holdout） | — | active_path_count=7; branch_conflict_intensity=0.11666666666666665; employment_score=5; entrepreneurship_score=6; reason=duan_runner_insufficient_advantage |
| P-2026-048 | abstain | entrepreneurship | 是 | 否 | active_path_count=3; branch_conflict_intensity=0.11666666666666665; employment_score=5; entrepreneurship_score=3; reason=duan_runner_insufficient_advantage |
| P-2026-049 | employment | employment | 是 | 是 | active_path_count=4; branch_conflict_intensity=0.0; employment_score=6; entrepreneurship_score=3; reason=duan_runner_employment_trigger |
| P-2026-051 | abstain | mixed | 否（mixed holdout） | — | active_path_count=2; branch_conflict_intensity=0.4166666666666667; employment_score=4; entrepreneurship_score=6; reason=duan_runner_mixed_not_allowed |
| P-2026-055 | abstain | employment | 是 | 否 | active_path_count=2; branch_conflict_intensity=0.11666666666666665; employment_score=4; entrepreneurship_score=3; reason=duan_runner_insufficient_advantage |
| P-2026-056 | employment | employment | 是 | 是 | active_path_count=5; branch_conflict_intensity=0.4166666666666667; employment_score=6; entrepreneurship_score=3; reason=duan_runner_employment_trigger |
| P-2026-058 | entrepreneurship | employment | 是 | 否 | active_path_count=6; branch_conflict_intensity=0.39999999999999997; employment_score=2; entrepreneurship_score=9; reason=duan_runner_entrepreneurship_trigger |
| P-2026-060 | abstain | employment | 是 | 否 | active_path_count=4; branch_conflict_intensity=0.0; employment_score=6; entrepreneurship_score=8; reason=duan_runner_insufficient_advantage |
| P-2026-062 | employment | employment | 是 | 是 | active_path_count=2; branch_conflict_intensity=0.11666666666666665; employment_score=5; entrepreneurship_score=1; reason=duan_runner_employment_trigger |
| P-2026-063 | employment | employment | 是 | 是 | active_path_count=4; branch_conflict_intensity=0.3333333333333333; employment_score=7; entrepreneurship_score=4; reason=duan_runner_employment_trigger |
| P-2026-067 | abstain | mixed | 否（mixed holdout） | — | active_path_count=6; branch_conflict_intensity=0.5166666666666666; employment_score=6; entrepreneurship_score=4; reason=duan_runner_mixed_not_allowed |
| P-2026-071 | entrepreneurship | employment | 是 | 否 | active_path_count=5; branch_conflict_intensity=0.3; employment_score=3; entrepreneurship_score=6; reason=duan_runner_entrepreneurship_trigger |
| P-2026-072 | entrepreneurship | employment | 是 | 否 | active_path_count=9; branch_conflict_intensity=0.11666666666666665; employment_score=3; entrepreneurship_score=6; reason=duan_runner_entrepreneurship_trigger |
| P-2026-073 | entrepreneurship | employment | 是 | 否 | active_path_count=6; branch_conflict_intensity=0.0; employment_score=4; entrepreneurship_score=8; reason=duan_runner_entrepreneurship_trigger |
| P-2026-074 | abstain | employment | 是 | 否 | active_path_count=8; branch_conflict_intensity=0.11666666666666665; employment_score=4; entrepreneurship_score=4; reason=duan_runner_insufficient_advantage |
| P-2026-075 | abstain | entrepreneurship | 是 | 否 | active_path_count=14; branch_conflict_intensity=0.4333333333333333; employment_score=6; entrepreneurship_score=6; reason=duan_runner_mixed_not_allowed |
