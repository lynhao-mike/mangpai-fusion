# Task 6 实现报告

## 完成内容

- 新增条件化能力聚合：按 `(school_id, task_id, chart_prototype_id, claim_type, time_horizon, evidence_completeness_band)` 分组，输出 coverage、discrimination、accuracy、calibration error、Beta posterior、N_eff 与证据元数据。
- Beta 使用 `Beta(1 + hit_weight, 1 + miss_weight)`；均值精确，区间明确记录为裁剪到 `[0, 1]` 的 95% normal approximation，不声称是精确 Beta quantile。
- calibration error 少于 5 条有效概率 claim 时固定为 `None`。
- 新增四组实验：`school_only`、`all_schools`、`leave_one_school_out`、`baseline_plus_school`，ID 集完整且学校与输入顺序不影响结果。
- equal-weight fusion 仅标记为 `equal_weight_evaluation_baseline`，不是生产仲裁器；unsupported 与 abstain 不贡献概率，无 claim 时返回 no-output。
- baseline prevalence 是必需 keyword-only 显式输入，文档要求来自指定 development split；实现不从被评估 labels 推导 prevalence。
- `ExperimentResult` 与 `ExperimentRow` 仅在实验模块内定义为最小 frozen dataclass，未扩张持久化契约。

## TDD 证据

1. RED：`python -m pytest tests/evaluation/test_capability.py tests/evaluation/test_experiments.py -v`
   - 结果：收集阶段 2 errors，分别为缺失 `engine.evaluation.capability` 与 `engine.evaluation.experiments`，符合预期。
2. 首次 GREEN 验证：同一命令实现后执行。
   - 结果：`1 failed, 9 passed`；唯一失败是测试对 Beta posterior mean 的手算预期错误（实际按加权 accuracy 得到 0.614），修正测试期望为公式值，未修改实现语义。
3. 专项 GREEN：同一命令再次执行。
   - 结果：`10 passed in 0.31s`。
4. 全 evaluation 回归：`python -m pytest tests/evaluation -q`
   - 结果：`83 passed in 0.30s`。
5. 格式验证：`git diff --check`
   - 结果：退出码 0。

## 提交与范围

- 功能提交：`c9de801 feat: estimate conditional school capability`。
- 提交仅包含：
  - `engine/evaluation/capability.py`
  - `engine/evaluation/experiments.py`
  - `tests/evaluation/test_capability.py`
  - `tests/evaluation/test_experiments.py`
- 本报告按要求写入 `.superpowers/sdd/task-6-report.md`，未纳入功能提交。
- 工作树中既有 `.superpowers/sdd/task-1-report.md` 与 `.superpowers/sdd/task-4-report.md` 修改未触碰、未提交。

---

## Task 6 定向修复追加记录（2026-07-12）

### 修复内容

- `build_capability_posteriors` 新增 keyword-only 的 `claim_probabilities`、`eligible_case_ids`、`score_weights`、`incremental_gains`；原始 claim probability 不再从 accuracy score 反解。
- coverage 改为显式 eligible case 集分母；缺 identity、空分母、缺 claim probability、越界 probability、非法权重均快速失败。
- 仅有效量化 claim 参与 weighted hit/miss/N_eff；默认权重 1，显式权重仅允许 0、0.5、1；calibration 使用显式 probability 与 observed label，至少 5 条。
- 实验协议改用显式 `eligible_case_tasks` 生成完整网格；增加 group mean utility、按 school 的 leave-one-out incremental gain，以及明确命名的 `(school_id, task_id)` 能力增益映射函数。
- 拒绝 task、label、output 重复 identity，拒绝未知 task，并复用 scoring 的 binary schema/label 约束语义。
- 未扩展持久化 models；功能改动仅涉及两个实现文件和两个对应测试文件。

### TDD 与验证证据

1. RED：`python -m pytest tests/evaluation/test_capability.py tests/evaluation/test_experiments.py -q`
   - 结果：`20 failed, 6 passed`；失败来自缺少新增显式参数和实验聚合接口，符合预期。
2. 实现后专项验证：同一命令。
   - 结果：`26 passed in 0.12s`。
3. 全 evaluation 回归：`python -m pytest tests/evaluation -q`
   - 结果：`99 passed in 0.37s`。
4. 格式验证：`git diff --check`
   - 结果：退出码 0。

---

## Task 6 最后定向修复追加记录（2026-07-12）

### 修复内容

- `run_four_group_experiment` 先物化 eligible grid，并对重复 `(case_id, task_id)` 抛出 `ValueError`；不再通过 `set` 静默去重。
- `build_capability_posteriors` 在聚合前拒绝重复 `(case_id, task_id, school_id)` score identity，防止同一 score 重复累计 N_eff。
- 在 `scoring.py` 提取公开纯函数 `binary_observed_value(task, label) -> bool`，集中执行 binary schema 校验与 observed label 映射。
- `score_output` 与 `run_four_group_experiment` 共同调用该函数，删除实验模块中的重复映射实现；错误语义与外部评分语义不变。
- 对上述三个行为补充 scoring、capability、experiments 回归测试。

### 严格 TDD 证据

1. RED（共享函数）：`python -m pytest tests/evaluation/test_scoring.py tests/evaluation/test_capability.py tests/evaluation/test_experiments.py -q`
   - 结果：收集阶段因 `binary_observed_value` 尚不存在而失败，符合预期。
2. RED（两个重复 identity）：分别运行两个新增测试。
   - 结果：`2 failed`，均为预期的 `DID NOT RAISE ValueError`。
3. 专项 GREEN：`python -m pytest tests/evaluation/test_scoring.py tests/evaluation/test_capability.py tests/evaluation/test_experiments.py -q`
   - 结果：`69 passed in 0.28s`。
4. 全 evaluation GREEN：`python -m pytest tests/evaluation -q`
   - 结果：`101 passed in 0.38s`。
5. 格式验证：`git diff --check`
   - 结果：退出码 0。

### 提交与范围

- 定向修复提交：`19e3e65 fix: reject duplicate evaluation identities`。
- 提交仅包含三个 evaluation 实现文件及其三个专项测试文件。
- 既有 `.superpowers/sdd/task-1-report.md` 与 `.superpowers/sdd/task-4-report.md` 工作树修改保持未触碰、未纳入提交。
- 本追加报告在功能提交后按要求更新，单独纳入报告提交。
