# Task 6 报告：关闭子平事业纵切片 P1/P2

## 范围

- 起始 HEAD：`91c0417 feat: assemble native ziping career L2-L4 slice`。
- 本任务仅修改 `engine/decision/r10_ziping_career.py`、`tests/r10/test_r10_ziping_career_acceptance.py` 与本报告。
- `.superpowers/sdd/task-1-report.md`、`.superpowers/sdd/task-2-report.md` 是进入 Task 6 前已有的用户修改，本任务未暂存。
- 未实施 Task 7。

## RED

先扩展 acceptance test，再运行：

```cmd
python -m pytest tests/r10/test_r10_ziping_career_acceptance.py -q
```

结果：exit 1，`7 failed, 6 passed`。失败均为预期缺口：

1. duplicate ziping applicability 两种顺序均未抛出 `ValueError`；
2. 目标与非目标同 ID 未拒绝；
3. 目标内部完全等值重复未拒绝；
4. 目标内部同 ID 不同内容未拒绝；
5. 相等但不同对象的重复目标未拒绝；
6. 目标与非目标同 ID 不同内容未拒绝。

这证明新增测试实际捕获了审查指出的 P1/P2，而不是在既有实现上直接变绿。

## GREEN

在 `r10_ziping_career.py` 做最小修复：

1. 先收集 ziping applicability；数量大于 1 时明确抛出 `ValueError("duplicate ziping applicability")`，不受输入顺序影响；
2. 缺少 ziping applicability 或角色为 `abstain` 时，只抑制 ziping 总体/事业目标，非目标仍交给 adapter；
3. 提取单一目标谓词，legacy claims 直接以该谓词的否定按原位置过滤；不再使用 `claim not in target_v5`，因此保序、保 multiplicity，且不受 dataclass 值相等影响；
4. adapter 仍接收由原 `V5Output` 仅替换 claims 得到的对象，applicability 保持原对象；其他 V5Output 字段等值不变；
5. adapter 返回的 legacy L2 按对象与顺序原样置于 native L2 前；
6. 合并 L2 后线性扫描 claim ID，任一重复立即抛出包含重复 ID 的 `ValueError`；不使用集合压平；
7. 仅在唯一性通过后进入 L3/L4。

首轮实现后 acceptance test 出现 1 个测试文件拼接错误；修正测试块位置后：`13 passed, 1 warning`。

## 契约覆盖

新增/加强的 acceptance 覆盖：

- duplicate ziping applicability 任意顺序；
- ziping 授权缺项与 abstain；
- 目标 + 非目标同 ID；
- 目标内部完全等值重复；
- 目标内部同 ID 不同内容；
- 其他派、ziping 财富、目标总体/事业的合成 output；
- 相等但不同对象的目标；
- adapter `args[0].claims` 精确等于原 output 按位置过滤后的非目标列表；
- adapter `args[1] is applicability`；
- 其他 V5Output 字段等值；
- adapter 返回对象逐对象、逐顺序保留；
- claims/verdicts 数量一对一；
- claim IDs 与 verdict IDs 各自唯一；
- 每个位置 `verdict.claim_id == claim.claim_id`；
- events 继续精确等于 L4 直接构建结果。

## 回归

分组验证：

```cmd
python -m pytest tests/r10 -q
python -m pytest tests/test_l4_event_type.py tests/test_l3_geju_review.py -q
python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q
```

结果：

- R10：`54 passed, 1 warning`；
- R8/R9：`11 passed, 1 warning`；
- MVP/adapter：`88 passed, 1 warning`。

提交前合并验证：

```cmd
python -m pytest tests/r10/test_r10_ziping_career_acceptance.py tests/r10/test_r10_ziping_career_l2.py tests/r10/test_r10_ziping_career_layers.py tests/test_l4_event_type.py tests/test_l3_geju_review.py tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q
git diff --check
```

结果：`153 passed, 1 warning`，`git diff --check` exit 0。warning 仅为仓库既有 `dual_engine_adapter` DeprecationWarning。

额外广集运行曾包含 `tests/test_l9_router_calibration.py`，结果为 `170 passed, 1 failed`；单独复现同样失败，失败点是样例默认 run 没有 feedback signal。`git diff` 证明本任务未修改 L9、MVP 或该测试，且 Task 5 报告已记录事件红线使默认空链合法；该历史测试与当前契约不一致，超出 Task 6 允许范围，因此未越界修改。

## 最终红线

1. 不靠集合压平重复 claim；完全重复也明确拒绝。
2. legacy 划分只用目标谓词否定，保序、保 multiplicity。
3. 缺项/abstain 只影响目标切片。
4. L3/L4 只接收唯一且逐位置可追踪的完整 L2。
5. events 不恢复 fallback，不做 Task 7。
