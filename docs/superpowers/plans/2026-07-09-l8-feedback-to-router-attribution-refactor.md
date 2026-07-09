# 反馈归因回打流派路由（Phase R3）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把单次 run 内的"失验（miss）"反馈，沿 `report_item → arbitration_decision → school_applicability_snapshot` 回打到**责任流派**，产出 `target_type="router"、target_id=流派名` 的 L9 校准动作——补齐当前"router 校准动作 target 指向报告条目、说不清该下调哪一派"的缺口。

**Architecture:** 现状 [`build_calibration_actions()`](../../../engine/decision/l9_calibration.py) 把 L8 归因转成校准动作，但 L1 归因的 `affected_object_id` 是 report_item_id，无法指明流派。R3 新增一个纯函数 `build_router_calibration_actions()`，只在**本 run 内**把 miss 反馈映射到"主审/副主审流派"，产出流派级 router 动作，追加到 `calibration_actions`。跨 case 连续失验的持久化与真正改变未来路由，**显式延后到 R4**。

**Tech Stack:** Python 3、dataclass、pytest。纯内存函数，无外部依赖、无持久化。

## Global Constraints

- 事实源以 [`AGENTS.md`](../../../AGENTS.md) 为准；架构判断以 [`plans/layered-decision-system.md`](../../../plans/layered-decision-system.md) 为准。
- **R3 只在单个 DecisionRun 内工作，不做跨 run 聚合、不写文件、不建数据库、不改旧 feedback_loop / Beta 生命周期。** 跨 run 学习是 R4。
- 复用既有 [`CalibrationAction`](../../../engine/decision/models.py:280) 数据结构，不新增模型。
- 产出的 router 动作必须满足 [`DecisionRun.validate_trace()`](../../../engine/decision/models.py:320)：`evidence_feedback_ids` 非空、且每个 feedback_id 必须存在于 `feedback_signals` 且已被 `feedback_attributions` 归因。
- 不改 [`build_calibration_actions()`](../../../engine/decision/l9_calibration.py) 现有行为；R3 动作是**追加**，不是替换。
- 默认 run 的反馈 verdict 全是 `unknown`，R3 在无 miss 时必须产出空列表，保证现有 `calibration_actions == []` 断言不破。
- 每个任务结束跑绿相关测试；Windows cmd.exe：命令用 `&&` 串联，不用 `sed`/`grep`/`cat`；提交信息用中文。

## 背景事实（执行前必读，已实测确认）

1. 每个 [`ArbitrationDecision`](../../../engine/decision/models.py:211) 带 `school_applicability_snapshot: list[SchoolApplicability]`，其中 `role in {"lead","co_lead"}` 的即"主审责任派"。已实测 `report_item → decision → snapshot` 一跳可达且存在 lead/co_lead 派。
2. [`ReportViewItem`](../../../engine/decision/models.py:239) 有 `decision_id`；[`FeedbackSignal`](../../../engine/decision/models.py:253) 有 `report_item_id` 与 `verdict`。
3. [`build_feedback_attributions()`](../../../engine/decision/l8_feedback_attribution.py) 会给每条 signal 产出归因，因此任何 miss signal 的 feedback_id 都已被归因，满足 trace 的 evidence 绑定要求。
4. [`validate_trace()`](../../../engine/decision/models.py:497) 对 L9 的校验：`action_id/target_id/reason` 非空、`target_type` 合法（`router` 合法）、`action` 合法（`downgrade`/`review` 合法）、`evidence_feedback_ids` 非空且绑定到已归因 feedback。**它不校验 target_id 必须是 report_item**，所以流派名作为 target_id 合法。
5. 已实测原型：真实 run 注入一个 `verdict="miss"` 反馈后，R3 逻辑产出 router 动作，且把动作追加进 DecisionRun 后 `validate_trace() == []`。
6. 接线点：[`orchestrator.run_decision_mvp()`](../../../engine/decision/orchestrator.py) 与 [`v5_adapter.decision_run_from_v5()`](../../../engine/decision/v5_adapter.py:251) 各有一处 `calibration_actions = build_calibration_actions(...)`。

---

### Task 1: 新增 build_router_calibration_actions（TDD）

**Files:**
- Modify: `engine/decision/l9_calibration.py`
- Test: `tests/test_l9_router_calibration.py`（新建）

**Interfaces:**
- Produces: `build_router_calibration_actions(case_id: str, report_items: list[ReportViewItem], decisions: list[ArbitrationDecision], feedback_signals: list[FeedbackSignal]) -> list[CalibrationAction]`。
  - 逻辑：对每条 `verdict=="miss"` 的 signal，找到其 report_item → decision → snapshot 中 `role in {"lead","co_lead"}` 的流派，按流派聚合 feedback_id；每个责任流派产出一条 `target_type="router"、target_id=流派名` 的动作，`action="downgrade" if 证据数>=3 else "review"`。
  - 无 miss 时返回 `[]`。

- [ ] **Step 1: 写失败测试**

新建 [`tests/test_l9_router_calibration.py`](../../../tests/test_l9_router_calibration.py)：

```python
from __future__ import annotations

import dataclasses

from engine.decision import run_decision_mvp
from engine.decision.l9_calibration import build_router_calibration_actions


WENZHEN = """
$BASE
命式: 乾
$FOUR
Y:甲寅
M:乙卯
D:丙子
H:戊午
$DY_LOOP
# 1998-2007 甲寅
$FOCUS
事业
""".strip()


def test_router_calibration_empty_when_no_miss() -> None:
    run = run_decision_mvp(WENZHEN)

    actions = build_router_calibration_actions(
        run.case_id, run.report_items, run.arbitration_decisions, run.feedback_signals
    )

    assert actions == []


def test_router_calibration_targets_lead_school_on_miss() -> None:
    run = run_decision_mvp(WENZHEN)
    signals = list(run.feedback_signals)
    assert signals, "样例 run 应至少有一条反馈信号"
    signals[0] = dataclasses.replace(signals[0], verdict="miss", notes="流派选错 主审失验")

    actions = build_router_calibration_actions(
        run.case_id, run.report_items, run.arbitration_decisions, signals
    )

    assert actions, "miss 反馈应产出至少一条 router 校准动作"
    assert all(a.target_type == "router" for a in actions)
    assert all(a.target_id for a in actions)
    assert all(a.evidence_feedback_ids for a in actions)
    assert all(a.action in {"review", "downgrade"} for a in actions)
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_l9_router_calibration.py -v`
Expected: FAIL，`ImportError: cannot import name 'build_router_calibration_actions'`。

- [ ] **Step 3: 实现函数**

在 [`engine/decision/l9_calibration.py`](../../../engine/decision/l9_calibration.py) 顶部 import 行改为（追加所需类型）：

```python
from engine.decision.models import (
    ArbitrationDecision,
    CalibrationAction,
    FeedbackAttribution,
    FeedbackSignal,
    ReportViewItem,
)
```

在文件末尾追加函数：

```python
def build_router_calibration_actions(
    case_id: str,
    report_items: list[ReportViewItem],
    decisions: list[ArbitrationDecision],
    feedback_signals: list[FeedbackSignal],
) -> list[CalibrationAction]:
    """把单 run 内 miss 反馈回打到责任流派，产出 router 校准动作。

    R3 约束：只在本 run 内工作，不做跨 run 聚合、不持久化。
    """

    decision_by_id = {d.decision_id: d for d in decisions}
    report_by_id = {r.report_item_id: r for r in report_items}

    per_school: dict[str, list[str]] = {}
    for signal in feedback_signals:
        if signal.verdict != "miss" or not signal.feedback_id:
            continue
        report_item = report_by_id.get(signal.report_item_id)
        if report_item is None:
            continue
        decision = decision_by_id.get(report_item.decision_id)
        if decision is None:
            continue
        for applicability in decision.school_applicability_snapshot:
            if applicability.role in {"lead", "co_lead"} and applicability.school:
                per_school.setdefault(applicability.school, []).append(signal.feedback_id)

    actions: list[CalibrationAction] = []
    for idx, (school, feedback_ids) in enumerate(sorted(per_school.items()), start=1):
        evidence = sorted(set(feedback_ids))
        actions.append(
            CalibrationAction(
                action_id=f"router-cal-{case_id}-{idx:03d}",
                target_type="router",
                target_id=school,
                action="downgrade" if len(evidence) >= 3 else "review",
                reason="该流派在本命盘被 L1 授权主审 / 副主审，但对应报告条目失验，回打路由角色。",
                evidence_feedback_ids=evidence,
            )
        )
    return actions
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_l9_router_calibration.py -v`
Expected: 2 PASS。

- [ ] **Step 5: 提交**

```bash
git add engine/decision/l9_calibration.py tests/test_l9_router_calibration.py && git commit -m "feat: 新增 build_router_calibration_actions 把 miss 反馈回打责任流派"
```

---

### Task 2: 导出新函数并接入 orchestrator

**Files:**
- Modify: `engine/decision/__init__.py`
- Modify: `engine/decision/orchestrator.py`
- Test: `tests/test_l9_router_calibration.py`（追加）

**Interfaces:**
- Consumes: `build_router_calibration_actions`（Task 1）。
- Produces: `run_decision_mvp` 的 `calibration_actions` 在有 miss 时包含 router 动作；无 miss 时行为不变（默认 run 仍为 `[]`）。

- [ ] **Step 1: 在 __init__.py 导出**

在 [`engine/decision/__init__.py`](../../../engine/decision/__init__.py:31) 的 `from engine.decision.l9_calibration import build_calibration_actions` 改为：

```python
from engine.decision.l9_calibration import build_calibration_actions, build_router_calibration_actions
```

在 [`__all__`](../../../engine/decision/__init__.py:53) 列表中 `"build_calibration_actions",` 之后新增一行：

```python
    "build_router_calibration_actions",
```

- [ ] **Step 2: 在 orchestrator 接线**

在 [`engine/decision/orchestrator.py`](../../../engine/decision/orchestrator.py) 的 import 行 `from engine.decision.l9_calibration import build_calibration_actions` 改为：

```python
from engine.decision.l9_calibration import build_calibration_actions, build_router_calibration_actions
```

找到：

```python
    calibration_actions = build_calibration_actions(case_id, feedback_attributions)
```

替换为：

```python
    calibration_actions = build_calibration_actions(case_id, feedback_attributions)
    calibration_actions = calibration_actions + build_router_calibration_actions(
        case_id, report_items, decisions, feedback_signals
    )
```

- [ ] **Step 3: 写集成测试**

在 [`tests/test_l9_router_calibration.py`](../../../tests/test_l9_router_calibration.py) 末尾追加：

```python
def test_run_decision_mvp_default_has_no_router_calibration() -> None:
    run = run_decision_mvp(WENZHEN)

    router_actions = [a for a in run.calibration_actions if a.target_type == "router"]

    assert router_actions == []
    assert run.validate_trace() == []
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_l9_router_calibration.py -v`
Expected: 3 PASS。

- [ ] **Step 5: 提交**

```bash
git add engine/decision/__init__.py engine/decision/orchestrator.py tests/test_l9_router_calibration.py && git commit -m "feat: orchestrator 接入 router 校准动作并导出新函数"
```

---

### Task 3: 接入 v5 生产链路（v5_adapter）

**Files:**
- Modify: `engine/decision/v5_adapter.py`
- Test: `tests/test_l9_router_calibration.py`（追加）

**Interfaces:**
- Consumes: `build_router_calibration_actions`。
- Produces: `decision_run_from_v5` 的 `calibration_actions` 同样追加 router 动作；默认无 miss 时不变。

- [ ] **Step 1: 在 v5_adapter 导入**

在 [`engine/decision/v5_adapter.py`](../../../engine/decision/v5_adapter.py:13) 的 `from engine.decision.l9_calibration import build_calibration_actions` 改为：

```python
from engine.decision.l9_calibration import build_calibration_actions, build_router_calibration_actions
```

- [ ] **Step 2: 在 decision_run_from_v5 接线**

在 [`decision_run_from_v5()`](../../../engine/decision/v5_adapter.py:251) 找到：

```python
    calibration_actions = build_calibration_actions(case_id, feedback_attributions)
```

替换为：

```python
    calibration_actions = build_calibration_actions(case_id, feedback_attributions)
    calibration_actions = calibration_actions + build_router_calibration_actions(
        case_id, report_items, decisions, feedback_signals
    )
```

- [ ] **Step 3: 写集成测试**

在 [`tests/test_l9_router_calibration.py`](../../../tests/test_l9_router_calibration.py) 顶部 import 区补充：

```python
from engine.v5 import run_v5
from engine.decision import decision_run_from_v5
```

在文件末尾追加：

```python
def test_v5_adapter_default_has_no_router_calibration() -> None:
    output = run_v5({"case_id": "C-TEST-R3-V5", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})

    run = decision_run_from_v5(output)

    router_actions = [a for a in run.calibration_actions if a.target_type == "router"]
    assert router_actions == []
    assert run.validate_trace() == []
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_l9_router_calibration.py -v`
Expected: 4 PASS。

- [ ] **Step 5: 提交**

```bash
git add engine/decision/v5_adapter.py tests/test_l9_router_calibration.py && git commit -m "feat: v5 生产链路接入 router 校准动作"
```

---

### Task 4: 全量回归 + 文档状态更新

**Files:**
- Modify: `plans/layered-decision-system.md`

**Interfaces:**
- Produces: §18 Phase R3 标记为已完成（含边界说明）。

- [ ] **Step 1: 全量 decision 测试回归**

Run: `python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py tests/test_l9_router_calibration.py -q`
Expected: 全部 PASS，0 FAIL。若 [`test_decision_run_from_v5_preserves_trace`](../../../tests/test_decision_v5_adapter.py:9) 或 MVP 中断言 `calibration_actions == []` 的测试 FAIL，说明默认 run 意外产出了 router 动作——回到 Task 1 检查"无 miss 返回 []"逻辑，不要放宽断言。

- [ ] **Step 2: 定位 Phase R3 标题**

用 search 工具在 [`plans/layered-decision-system.md`](../../../plans/layered-decision-system.md) 找 `### Phase R3：反馈归因回打到路由与层`。

- [ ] **Step 3: 插入状态行**

在该标题下第一行前插入：

```markdown
> 状态：部分完成（单 run 内 miss 反馈已能回打到责任流派、产出 router 校准动作，见 tests/test_l9_router_calibration.py）。跨 case 连续失验的聚合与真正改变未来路由属 R4，尚未实现。
```

- [ ] **Step 4: 提交**

```bash
git add plans/layered-decision-system.md && git commit -m "docs: 标记 Phase R3 单run反馈回打路由已完成，跨run聚合留待R4"
```

---

## 验收总清单（全部完成后执行一次）

- [ ] `python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py tests/test_l9_router_calibration.py -q` 全绿。
- [ ] 默认 run（无 miss）的 `calibration_actions` 不含任何 `target_type=="router"` 动作。
- [ ] 注入一条 miss 反馈后，产出的 router 动作 `target_id` 是流派名（非 report_item_id）。
- [ ] router 动作 `evidence_feedback_ids` 非空且绑定到已归因 feedback。
- [ ] `validate_trace()` 对含 router 动作的 run 返回 `[]`。

## 证伪口径（对照架构 §19.2）

- 若 miss 反馈回打出来的"责任流派"总是全部 6 派（无区分力），说明快照里 lead/co_lead 太宽，路由责任无法定位——需回到 R2 收紧角色，而不是在 R3 硬造区分。
- R3 只证明"失验能定位到责任流派并生成校准信号"；它**不**改变未来路由、**不**跨 case 学习。若有人据此认为"系统已经会自我纠正流派选择"，属误读——真正的闭环是 R4。
- 若未来重构切断了 `ArbitrationDecision.school_applicability_snapshot`，R3 立即失效，须在 R4 前修复。

## Self-Review 记录

- Spec 覆盖：架构 §18 Phase R3 目标（把 L8 归因接回 L1 适用性 + 触发 L9 对 router 的动作）由 Task 1（回打函数）+ Task 2/3（orchestrator 与 v5 接线）覆盖；"跨 run 连续失验触发 downgrade/review"部分在文档中显式标注延后 R4，避免假装完成。
- Placeholder 扫描：无 TBD / "适当处理"；每个代码步骤给出完整可粘贴代码。
- 类型一致：`build_router_calibration_actions` 签名（case_id, report_items, decisions, feedback_signals）在 Task 1 定义、Task 2/3 消费一致；`CalibrationAction` 字段与 [`models.py`](../../../engine/decision/models.py:280) 一致；`target_type="router"`、`action in {review,downgrade}` 均在 [`validate_trace()`](../../../engine/decision/models.py:497) 合法集合内。
- 已知风险显式化：默认 run 不得产出 router 动作（Task 2/3 集成测试守护）；范围边界（不跨 run、不持久化）写入 Global Constraints 与证伪口径。
- 已实测确认：回打链路可达、注入 miss 产出流派级动作、含动作的 run trace 干净。
