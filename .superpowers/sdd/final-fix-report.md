# School Capability Blind Evaluation Final Fix Report

## 范围与隔离

- 工作区：隔离 worktree `f:/综合盲派/mangpai-fusion/.worktrees/school-capability-blind-evaluation`
- 起始 HEAD：`cdec332`
- 功能提交：`3b2e504 fix: enforce blind evaluation evidence gates`
- 未修改、未暂存、未提交既有工作区改动：`.superpowers/sdd/task-1-report.md`、`.superpowers/sdd/task-4-report.md`
- 未修改 `cases/`、`theory/`、`META/`、生产权重、runner 或生产入口；未运行 `tests/v5/`。

## TDD 证据

### 基线

命令：

```text
python -m pytest tests/evaluation -q
```

结果：`117 passed in 5.33s`。

### RED

先新增 `tests/evaluation/test_final_findings.py`，再运行：

```text
python -m pytest tests/evaluation -q
```

结果：`8 failed, 117 passed in 4.07s`。八个失败分别证明：score CLI 缺 `--manifest`；labels schema 不严格；eligible grid 缺 school output 未拒绝；实验不支持五类正式 scorer；utility 不是 proper utility；Beta 错用 proper score；报告仍可能 GO 且重复 posterior；持久记录仅浅冻结。

报告显式 gate 后续单独 RED：

```text
python -m pytest tests/evaluation/test_final_findings.py::test_report_only_allows_ready_or_stop_with_complete_explicit_gate_evidence -q
```

结果：`1 failed`，原因为 `render_capability_report()` 不接受 `gate_evidence`。

### GREEN

最终命令：

```text
python -m pytest tests/evaluation -q
```

结果：`126 passed in 3.91s`。

相关无副作用回归：

```text
python -m pytest tests/test_project_metadata.py tests/test_decision_mvp.py tests/test_l1_learned_prior.py tests/test_l9_router_calibration.py tests/test_accuracy_report.py -q
```

结果：`86 passed, 1 warning in 9.40s`。warning 为既有 `engine.application.dual_engine_adapter` deprecation warning。

边界验证：

```text
git diff --check
git status --short cases theory META engine/expert-weights.yaml engine/domain-weights.yaml
```

结果：均退出码 0；禁区 status 无输出。

## 10 Findings 映射

1. **score 必需 manifest、严格 schema、eligible gate、digest provenance**
   - 代码：`tools/school_capability_baseline.py` 增加必需 `--manifest`，严格顶层/record/expected_schools 校验，只允许 manifest 中 `blind_candidate` / `historical_blind_candidate` 进入 grid，并输出 manifest SHA256、task catalog identity、rule snapshot identity、freeze hash。
   - 测试：`tests/evaluation/test_final_findings.py`、`tests/evaluation/test_cli.py`。

2. **正式任务只执行 eligible grid，支持五类 scorer**
   - 代码：`engine/evaluation/experiments.py` 对显式 eligible grid 执行 binary、multiclass、ordinal、time_window、portrait；CLI 删除 binary-only 阻断，非 binary 仍产 individual score 和四组 proper utility。
   - 测试：`tests/evaluation/test_final_findings.py::test_experiment_supports_all_formal_scoring_methods`。

3. **expected_schools 显式、唯一非空、完整输出矩阵**
   - 代码：manifest v1 增加 `expected_schools`；CLI 和实验均要求每个 eligible case-task × school 恰好一个 output。
   - 测试：`tests/evaluation/test_final_findings.py::test_experiment_requires_exactly_one_output_per_eligible_case_task_and_school`、更新后的 `tests/evaluation/test_experiments.py`。

4. **labels v1 严格 schema、list、重复拒绝**
   - 代码：`engine/evaluation/freeze.py::reveal_labels()` 严格校验三个顶层键、schema version、labels list、record 精确字段和 `(case_id, task_id)` 唯一性。
   - 测试：`tests/evaluation/test_final_findings.py::test_reveal_labels_v1_rejects_unknown_top_level_record_keys_non_list_and_duplicates`。

5. **coverage 按 metadata identity**
   - 代码：`engine/evaluation/capability.py` 继续以完整六维 identity 的显式 eligible case 集作分母；CLI 按每条 score 的完整 metadata identity 建立 eligible 集，不再按 task 全局混用后验。
   - 测试：`tests/evaluation/test_capability.py`、`tests/evaluation/test_final_findings.py`。

6. **task-aware proper utility，高风险 FP 2x**
   - 代码：`engine/evaluation/experiments.py` 复用 `score_output()` 的 proper score，二元高风险 false positive 对 loss 使用 `HIGH_RISK_FALSE_POSITIVE_MULTIPLIER = 2.0`。
   - 测试：`tests/evaluation/test_final_findings.py::test_experiment_uses_task_aware_proper_utility_and_doubles_high_risk_false_positive_cost`。

7. **Beta 离散命中，weight 仅观测权重，accuracy 保持 proper**
   - 代码：`engine/evaluation/capability.py` 将 `accuracy_score` 保持加权 proper score；Beta hit/miss 改为概率阈值分类与 observed 的离散命中；0/0.5/1 仅作为观测权重。
   - 测试：`tests/evaluation/test_final_findings.py::test_capability_coverage_uses_full_metadata_identity_and_beta_uses_discrete_hits`、更新后的 `tests/evaluation/test_capability.py`。

8. **报告安全状态机、默认 HOLD、绝不 GO、posterior 去重**
   - 代码：`engine/evaluation/report.py` 默认 HOLD；完整显式 gate evidence 仅可产生 `READY_FOR_MANUAL_REVIEW` 或 `STOP`；展示层移除 GO 字样；posterior 详情仅渲染一次。
   - 测试：`tests/evaluation/test_final_findings.py` 的默认 HOLD/去重测试和显式 gate 测试、`tests/evaluation/test_report.py`。

9. **全 provenance**
   - 代码：score 输出 `provenance` 包含 manifest digest、task catalog digest identity、rule snapshot digest identity、freeze hash；freeze hash 继续绑定 task/rule 完整 canonical 文件摘要。
   - 测试：`tests/evaluation/test_cli.py` 的 freeze digest 测试与 score JSON contract 测试。

10. **persisted records 深不可变**
    - 代码：`engine/evaluation/models.py` 构造时递归冻结 list/tuple 为 tuple、dict 为 `MappingProxyType`；`to_dict()` 递归恢复 JSON 可序列化副本；nested mutation 被拒绝。
    - 测试：`tests/evaluation/test_final_findings.py::test_persisted_contracts_are_deeply_immutable`、更新后的 round-trip/aliasing 测试。

## 改动文件

- `engine/evaluation/capability.py`
- `engine/evaluation/experiments.py`
- `engine/evaluation/freeze.py`
- `engine/evaluation/models.py`
- `engine/evaluation/report.py`
- `engine/evaluation/scoring.py`
- `tools/school_capability_baseline.py`
- `templates/school-capability-case-manifest.json`
- `tests/evaluation/test_capability.py`
- `tests/evaluation/test_cli.py`
- `tests/evaluation/test_experiments.py`
- `tests/evaluation/test_final_findings.py`
- `tests/evaluation/test_models.py`
- `tests/evaluation/test_report.py`

## 未解决项

- 无已知功能缺口。
- 非 binary 任务不进入 binary Beta accuracy posterior；它们仍进入任务感知 individual score 与四组 proper utility。这是避免为 ordinal/time-window/portrait 伪造二元命中的有意边界。
- 未运行 `tests/v5/`，遵守禁止写真实 cases 的用户约束。
- 唯一测试 warning 为仓库既有 deprecated adapter 提示，与本变更无关。
