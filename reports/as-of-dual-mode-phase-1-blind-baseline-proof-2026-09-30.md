# as-of 双模式重构 Phase 1：无反馈 BLIND_BASELINE 证明物

> 日期：2026-09-30  
> 授权范围：只实施无反馈 `BLIND_BASELINE` 证明；不进入稀疏核验、解释校准、六领域扩展、UI 或生产切换。  
> 结论：**Phase 1 的领域闭环、prospective lineage 适配、create-only 归档与定向回归已完成。**

---

## 1. 证明目标

本阶段证明以下闭环可以在完全不读取命主反馈、核验记录或 known facts 的条件下成立：

```text
prospective single-case blind bundle
→ as-of blind bundle
→ real CareerBlindDraft
→ frozen retrospective package
→ blind current-state hypotheses
→ blind future projection
→ immutable BLIND_BASELINE artifact
→ readback and digest verification
```

本阶段不声称：

- 已实现 `VERIFIED_STATE_REVISION`；
- 已实现 `CALIBRATED_REVISION`；
- 已实现 `InterpretationDelta`；
- 已切换任何生产入口；
- existing structural probe 已成为真实预测。

---

## 2. 新增实现

### 2.1 无反馈领域契约与纯运行器

新增 [`engine/asof/blind_baseline.py`](../engine/asof/blind_baseline.py)，包含：

- `ArtifactKind`：封闭定义三种制品名称，但 Phase 1 只运行 `BLIND_BASELINE`；
- `BaselineQuestionSnapshot`：绑定已封存 prospective future question；
- `BaselineRuntimeSnapshot`：绑定规则快照、代码版本和模型标识；
- `BlindInputAccessDeclaration`：固定输入白名单并强制 feedback、verification、known facts 三项均为 `False`；
- `BlindStateHypothesis` 与 `BlindCurrentStateSnapshot`：表达一个 primary 和最多两个 conditional 当前状态假设；
- `BlindFutureCandidate`、`BlindWealthBinding` 与 `BlindFutureProjection`：表达无反馈未来事业主线、条件分支和财富显式传播；
- `run_blind_baseline()`：只执行输入封存、历史盲断冻结、盲态当前状态校验和盲态未来投影；
- `serialize_blind_baseline_payload()`：生成纯 JSON payload；
- `blind_baseline_payload_sha256()`：生成 canonical payload digest。

运行器最终 workflow envelope 保持：

```text
FROZEN
```

它不调用：

```text
open_verification
record_career_verification
adjudicate_career_verifications
build_career_states
project_future_from_state
```

### 2.2 关键失败关闭约束

领域层已证明以下约束：

1. structural probe marker 不能被归档为真实 `BLIND_BASELINE`；
2. 当前状态必须引用已冻结 fundamental 或 event；
3. primary 当前状态必须是 `OUTPUT`；
4. conditional 当前状态只能是 `CONDITIONAL` 或 `ASK`；
5. conditional 分支最多两个；
6. 每个 conditional 分支必须实质改变事业结论；
7. future candidate 必须绑定同一 case 和 `as_of_date`；
8. wealth prediction 必须有且只有一个显式传播边；
9. 财富边只能连接同一状态假设内的事业和财富候选；
10. family、education、marriage、health 保持 `NOT_IMPLEMENTED / ABSTAIN`；
11. question observation window 按解析后的 UTC instant 比较，不按字符串字典序比较；
12. freeze package digest 在序列化前再次验证。

### 2.3 Prospective lineage 与 immutable archive 适配器

新增 [`engine/asof/blind_baseline_archive.py`](../engine/asof/blind_baseline_archive.py)，复用：

- prospective single-case bundle verifier；
- as-of blind bundle verifier；
- future question sealed artifact；
- rule snapshot reference；
- parent artifact reference；
- `publish_new_json()` create-only 发布；
- `validate_parent_ref()` 递归父链和 canonical digest 验证。

适配器提供：

- `load_blind_baseline_lineage_context()`：从已验证的 prospective/as-of bundle 构造唯一 question、rule、identity 和 parent 上下文；
- `publish_blind_baseline()`：发布 immutable artifact，拒绝覆盖，并立即读回验证顶层 artifact digest 和嵌套 baseline payload digest。

为避免归档基础能力在 import 阶段被仓库中可选 prospective 模块缺失阻塞，两个 verifier 采用延迟加载；正式调用时仍必须执行原 verifier，未绕过事实源验证。

---

## 3. 测试证明

新增 [`tests/asof/test_blind_baseline.py`](../tests/asof/test_blind_baseline.py)，覆盖：

- 无 feedback / verification 输入也能完成 baseline；
- envelope 保持 `FROZEN`；
- input access 三项泄漏标志均为 `False`；
- payload JSON round-trip 与 digest 稳定；
- 等值但不同小数秒写法的 UTC timestamp 不会绕过窗口校验；
- structural probe 被拒绝；
- unknown frozen source ID 被拒绝；
- wealth 无显式 edge 被拒绝；
- conditional branch 数量上限；
- conditional branch 必须改变主线事业结论；
- runner AST 不导入、不调用 verification/adjudication/verified projection；
- lineage snapshot 不匹配时写入前失败；
- create-only publication、不可覆盖和原字节保持；
- 正式发布后的 readback、artifact digest 和 baseline payload digest 验证；
- lineage loader 使用 sealed question、rule snapshot 和 as-of identity。

### 3.1 定向测试结果

```text
uv run --python 3.11 --with pytest --with PyYAML pytest \
  tests/asof/test_blind_baseline.py \
  tests/asof/test_consultation_freeze.py \
  tests/asof/test_session_runner.py \
  tests/asof/test_future_projection.py \
  tests/asof/test_archive_integration.py -q

202 passed in 0.90s
```

### 3.2 扩大 as-of 回归结果

在排除需要本机 `sxtwl` 原生编译环境的生产集成测试、两个已漂移的 protected-byte 基线断言，以及一个与本阶段无关的既有 frozen-slots 异常类型断言后：

```text
579 passed, 1 skipped, 1 deselected
```

未排除时观察到的阻断均不由 Phase 1 新文件引入：

1. `sxtwl==2.0.7` 在当前 Windows 环境需要 Microsoft Visual C++ 14.0+ 才能构建；
2. [`engine/evaluation/prospective_capability_identity.py`](../engine/evaluation/prospective_capability_identity.py) 在当前工作树中缺失，但既有 prospective 模块仍导入它；
3. protected-byte 测试显示既有 [`engine/evaluation/prospective_gates.py`](../engine/evaluation/prospective_gates.py) 与 [`tools/preflight.py`](../tools/preflight.py) 已相对测试基线漂移；
4. [`tests/asof/test_career_state_builder.py`](../tests/asof/test_career_state_builder.py) 的一个既有测试预期 `AttributeError`，当前 Python 运行时实际抛出 `TypeError`。

这些问题未在本阶段修复，因为不属于已授权的无反馈 baseline 范围。

---

## 4. 隔离结论

本阶段没有修改：

- [`engine/asof/session_runner.py`](../engine/asof/session_runner.py) 的 verified path；
- [`engine/asof/future_projection.py`](../engine/asof/future_projection.py) 的 confirmed-state projection；
- [`engine/asof/career_state_builder.py`](../engine/asof/career_state_builder.py) 的核验与裁决语义；
- 生产 CLI、报告入口或默认 pipeline；
- 全局规则、权重、路由或反馈摄入机制。

因此，Phase 1 证明物是旁路、显式 opt-in、不可覆盖的 `BLIND_BASELINE` 能力，不构成生产切换。

---

## 5. Phase 1 验收结论

| 验收项 | 结果 |
|---|---|
| 无反馈可独立完成 | 通过 |
| 历史盲断冻结 | 通过 |
| 盲态当前状态 | 通过 |
| 盲态未来事业预测 | 通过 |
| 显式财富传播 | 通过 |
| 最多两个条件分支 | 通过 |
| structural probe 禁止冒充预测 | 通过 |
| feedback / verification / known facts 零访问声明 | 通过 |
| prospective question/rule/parent lineage 复用 | 通过 |
| create-only、不可覆盖 | 通过 |
| 发布后读回与双层 digest 验证 | 通过 |
| verified path 保持不变 | 通过 |
| 生产入口保持不变 | 通过 |

**Phase 1 无反馈 `BLIND_BASELINE` 证明完成。** 后续若无新的明确授权，不进入稀疏核验、`VERIFIED_STATE_REVISION`、`InterpretationDelta`、`CALIBRATED_REVISION` 或生产切换。
