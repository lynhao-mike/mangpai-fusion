# School Capability Blind Evaluation — Final Fix 3 Report

## 范围

本轮仅修复两个 Important：派生 gate 不可信与低样本必须 HOLD。未扩展至密钥信任根，也未修改旧报告、案例或生产规则。

## 严格 TDD

### RED

先新增并修正测试，再修改实现。定向测试首次结果：`2 failed, 4 passed`。

失败项准确覆盖：

1. 单个 posterior 的 `n_eff=4.999` 且 gate 全真时错误进入 `READY_FOR_MANUAL_REVIEW`。
2. 篡改 `computed_gate_evidence` 并重算普通 `artifact_digest` 后，报告错误信任派生字段并进入 READY。

### GREEN

实现后同一定向命令结果：`6 passed`。

## 实现结果

1. `engine/evaluation/report.py` 新增纯函数 `compute_gate_evidence()`，只依据 posteriors、incremental gains、experiment summary、高风险审计摘要、coverage summary、gate thresholds 与 provenance 重算派生 gate。
2. score CLI 使用该纯函数生成 `computed_gate_evidence`，并在 artifact 中保留重算所需基础事实。
3. report CLI 校验 artifact checksum 后再次调用同一纯函数；若存储的派生 gate 存在且与重算值不一致则拒绝，渲染始终使用重算值。
4. 注释明确 `artifact_digest` 只是 consistency checksum，不是认证签名；本阶段不承诺防御攻击者整体改写所有基础实验事实。
5. `render_capability_report()` 使用 `all_below_threshold`：posteriors 为空或全部 `n_eff < 5` 时强制 HOLD；混合样本中至少一个 `n_eff >= 5` 且完整 gate 全真时才允许 READY；既有明确增量失败 STOP 规则保持不变。

## 验证

### Evaluation 全量

```text
python -m pytest tests/evaluation -q
147 passed in 5.60s
```

### 无写副作用相关回归

```text
python -m pytest tests/test_project_metadata.py tests/test_decision_mvp.py tests/test_l1_learned_prior.py tests/test_l9_router_calibration.py tests/test_accuracy_report.py -q
86 passed, 1 warning in 9.61s
```

warning 是仓库既有 deprecated adapter 提示，本轮未引入。

### 边界检查

`git diff --check` 退出码为 0。

## 提交

代码提交：`0197631`（`fix: recompute capability report gate`）。

代码提交只包含：

- `engine/evaluation/report.py`
- `tools/school_capability_baseline.py`
- `tests/evaluation/test_report.py`
- `tests/evaluation/test_cli.py`
- `tests/evaluation/test_final_findings.py`

本报告将单独提交，且不包含旧报告及 worktree 中既有的 case manifest 修改。
