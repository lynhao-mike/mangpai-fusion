# Task 4 报告：格局一致性审查归位 L3

## 范围

- 起始 HEAD：`d2d13688269ddbae3d372989d2ea6f20eb63eafb`
- 仅修改 `engine/decision/l3_structure.py`、`engine/decision/v5_adapter.py`、`tests/r10/test_r10_ziping_career_layers.py`。
- 未执行 Task 5，未修改 L4、runner、理论规则或其他流派领域。
- `.superpowers/sdd/task-1-report.md` 与 `task-2-report.md` 是进入 Task 4 前已有的用户修改，本任务未触碰、未暂存。

## RED

先创建 L3 用忌消费测试，执行：

```cmd
python -m pytest tests/r10/test_r10_ziping_career_layers.py::test_l3_consumes_geju_direction_from_l2_without_recomputing_it -q
```

结果：exit 1，`1 failed`。实际 verdict 已是 weaken，但 reason 不含 `正印`/`正格`，证明现有 L3 未消费 L2 metadata 格局方向，失败原因与目标缺失一致。

## GREEN 与迁移

- 将 adapter 的 profile 提取、十神文本识别、格局一致性裁决机械迁入 L3。
- L3 的 `extract_geju_profile()` 只读取 `SchoolClaim.metadata` 中的 `geju_type`、`favor_shishen`、`avoid_shishen`。
- `claim_type` 兼容 `structure` / `structure_claim` / `event` / `event_claim`；保留原生 L3 与 adapter 两条既有阈值和输出口径。
- adapter 仅保留 `_extract_geju_profile` alias 与 `_verdicts` 薄委托。
- 首条 GREEN：`1 passed`。

## 不发明测试

新增 metadata 缺失测试：仅 statement 出现“正印”而无 profile 时，仍按既有结构命题通过，reason 不出现“忌神”或“用神”。定向结果：`1 passed`。

静态红线扫描确认 L3 不含 `ziping_runner`、`run_ziping`、`engine.v5` 或 `theory` 调用。

## R9 回归与行为等价修复

首次完整 R9 回归暴露三处原生 L3 行为差异：极低置信 `structure` 未 reject、reject confidence 被抬高、evidence reason 丢失“旁证”。根因是最初机械迁移把 adapter 口径覆盖到了原生 L3。修复为按 claim_type 来源保留旧口径：

- 原生 `structure` 继续使用 0.5 pass 阈值、`<= 0.1` reject 与低 confidence 原值；
- 原生 event/timing/evidence 继续 unknown，并保留原 L3 旁证说明；
- `structure_claim` / `event_claim` 继续保持 adapter 的 0.4 阈值、weaken/reject 克制规则和 confidence 映射；
- 格局忌神冲突仍仅在 profile 存在时介入。

第二次完整回归又发现 adapter 的低置信 `event_claim` 被新原生 reject 门槛拦截，导致既有 reject_all 事件链消失。修复为 `<= 0.1` 通用 reject 仅适用于原生 L3 claim，adapter `*_claim` 保持 R9 旧行为；定向复验 `12 passed`。

## 最终验证

```cmd
python -m pytest tests/r10/test_r10_ziping_career_layers.py tests/test_l3_geju_review.py tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q
python -m pytest tests/r10 -q
git diff --check
```

结果：

- L3 + 完整 R9：`97 passed, 1 warning`；
- R10：`17 passed, 1 warning`；
- `git diff --check`：exit 0；
- 唯一 warning 为仓库既有 `dual_engine_adapter` DeprecationWarning。

## 红线

1. L3 只消费 L2 metadata，不调用 runner/理论，不自行判旺衰、用神、格局或做功。
2. metadata 无 profile 不发明用忌。
3. 保持原生 L3 和 R9 adapter 既有阈值、低置信 reject 克制口径与 event 链行为；明确新增仅为 claim_type 兼容。
4. adapter 无格局判断实现，只保留兼容 alias/委托。
5. 未碰 L4 或其他流派领域。

## Important 审查关闭：mutation / 契约测试加固

本轮只修改 `tests/r10/test_r10_ziping_career_layers.py` 与本报告；生产实现已满足契约，因此没有修改 `v5_adapter.py`、`l3_structure.py`，也没有进入 Task 5/L4。

新增门禁：

- 锁定 `_extract_geju_profile is l3_structure.extract_geju_profile`。
- monkeypatch adapter 绑定的 `build_structural_verdicts`，锁定 `_verdicts` 只传入原参数并原样返回委托结果，禁止 adapter 残留判断。
- 参数化 `structure` / `structure_claim` / `event` / `event_claim` 在 `0.1` / `0.4` / `0.5` 的既有兼容行为，覆盖原生低置信 reject 与 adapter reject 克制边界。
- 固定 `C-FIXED` / `fixed-claim` 的 verdict_id 常量 `dsv-f627b1616169`，并锁定直接 L3 与 adapter 输出相等。
- AST import 门禁禁止 `l3_structure.py` 导入 `engine.v5`、`runner`、`theory`。
- profile 只认 `geju_type` / `favor_shishen` / `avoid_shishen`；`geju`、`geju_type_hint`、`structure_type`、`favor`、`avoid`、`useful_gods`、`taboo_gods` 等伪字段不得触发 profile，且 canonical 字段不受伪字段污染。

### Mutation RED 证据

因正确实现已满足新增契约，按要求使用临时 mutation 并在同一命令中恢复文件：

1. 将 adapter `_verdicts` 临时变异为 `return []`，运行纯委托与等价测试：exit 1，`2 failed`；两条测试均杀死 adapter 残留行为变异。随后恢复原文件，layers 为 `23 passed`。
2. 将 `structure_claim` 的 `confidence >= 0.4` 临时变异为 `confidence > 0.4`，参数化边界测试在 `structure_claim-0.4-pass` 精确失败：exit 1，`1 failed, 11 passed`。随后恢复原文件，layers 为 `23 passed`。

首次新增测试运行还因手工录入的 verdict_id 期望常量错误得到 `1 failed, 22 passed`；根据同算法计算值纠正为 `dsv-f627b1616169`。这不是生产缺口，未据此改生产代码。

### 加固后验证

```cmd
python -m pytest tests/r10/test_r10_ziping_career_layers.py -q
python -m pytest tests/r10/test_r10_ziping_career_layers.py tests/test_l3_geju_review.py tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q
python -m pytest tests/r10 -q
```

结果：

- layers：`23 passed, 1 warning`；
- layers + 完整 R9：`118 passed, 1 warning`；
- R10：`38 passed, 1 warning`；
- warning 仍仅为仓库既有 `dual_engine_adapter` DeprecationWarning。
