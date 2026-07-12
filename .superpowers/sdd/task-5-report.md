# Task 5 实现报告

## 完成内容

- 新增纯函数 Brier score、LogLoss、时间窗口与 ordinal 归一化评分，并对概率边界、epsilon、畸形窗口和 rank 范围进行显式校验。
- 新增任务感知 `score_output`：按任务评分方法分派 binary/multiclass probability、time window、ordinal 与 portrait agreement。
- 实现 claim / abstain / unsupported 三态语义：弃权不伪造 accuracy，仅在有效可量化标签存在时计机会成本；unsupported 不计 accuracy 且 knowledge coverage 为 false。
- 高风险 false positive 使用命名常量 `HIGH_RISK_FALSE_POSITIVE_MULTIPLIER = 2.0`；弃权机会成本同样使用命名常量。
- 非量化 portrait 仅输出 agreement，不进入 probability、timing、ordinal accuracy 或 utility。
- 未引入第三方依赖，功能提交仅包含评分模块及其测试。

## TDD 证据

1. RED：`python -m pytest tests/evaluation/test_scoring.py -v`
   - 结果：收集阶段失败，`ModuleNotFoundError: No module named 'engine.evaluation.scoring'`，符合缺失实现的预期失败。
2. GREEN：同一命令实现后执行。
   - 结果：`8 passed in 0.24s`。
3. 回归验证：`python -m pytest tests/evaluation -q`
   - 结果：`40 passed in 0.23s`。
4. 差异格式检查：`git diff --check`
   - 结果：退出码 0，无格式错误。

## 提交与范围

- 功能提交：`267f906 feat: score blind predictions by task type`。
- 提交只包含 `engine/evaluation/scoring.py` 与 `tests/evaluation/test_scoring.py`。
- 本 SDD 报告按要求写入，但未提交。
- 工作树中既有 `.superpowers/sdd/task-1-report.md` 与 `.superpowers/sdd/task-4-report.md` 修改未触碰、未提交。

## 定向修复（审查反馈）

- 二元标签改为依据任务 `label_schema.positive_label` / `negative_label` 显式映射，未知标签拒绝，消除字符串真值转换。
- 强制 label、output、task 的 case/task 身份绑定；不一致立即 `ValueError`。
- binary、time-window、ordinal、portrait 强制恰好一条 prediction；multiclass 强制至少两类、类别唯一、概率和容差为 `1e-9`、observed 类别存在。
- multiclass 采用所有类别 squared error 的均值作为完整 Brier，并以 `1 - mean_brier` 写入 probability score，保持 `[0, 1]`。
- 时间年份、ordinal rank/max-rank 均只接受非 bool 的原生整数；时间标签不再执行宽松 `int()` 转换。

### 修复 TDD 与回归证据

1. RED：`python -m pytest tests/evaluation/test_scoring.py -v`
   - 结果：`21 failed, 7 passed`；失败覆盖显式二元映射、身份绑定、prediction 基数、多分类协议和整数类型边界。
2. 中间 GREEN：首次实现后为 `2 failed, 26 passed`，保留旧 numeric portrait agreement 行为并统一错误消息后继续验证。
3. 专项 GREEN：`python -m pytest tests/evaluation/test_scoring.py -v`
   - 结果：`28 passed in 0.20s`。
4. 全 evaluation 回归：`python -m pytest tests/evaluation -q`
   - 结果：`60 passed in 0.57s`。
5. 格式验证：`git diff --check`
   - 结果：退出码 0。
