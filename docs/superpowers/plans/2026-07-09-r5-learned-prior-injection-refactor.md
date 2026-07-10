# R5 执行计划：流派适用性学习先验注入（learned_prior）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给 [`route_schools()`](../../../engine/decision/l1_school_router.py:82) 增加可选入参 `learned_prior`：当某流派在历史反馈中命中率极低（样本足够）时，下调其在本次路由中的角色与分数；`learned_prior` 缺省时逐字回退到当前 R2 行为（零回归）。这是 R5 方向决策文档 §9 First Proof Point 的落地。

**Architecture:** 严格遵循 R5 方向决策（Option A）：engine 层 [`route_schools()`](../../../engine/decision/l1_school_router.py:82) 保持纯函数，学习结果只作为**纯 dict 入参注入**，engine 不做 IO、不 import tools。本计划**只做注入端**（可测、纯函数）；"用真实反馈聚合出 learned_prior 并持久化回灌"是数据/tools 层工作，显式延后到 R5-B，不在本计划范围。

**Tech Stack:** Python 3、dataclass、pytest。纯内存函数，无外部依赖、无 IO。

## Global Constraints

- 事实源以 [`AGENTS.md`](../../../AGENTS.md) 为准；方向以 [`docs/superpowers/plans/2026-07-09-r5-cross-run-routing-learning-direction.md`](2026-07-09-r5-cross-run-routing-learning-direction.md) 为准（已定 Option A）。
- **[`route_schools()`](../../../engine/decision/l1_school_router.py:82) 必须保持纯函数**：不读文件、不 import tools、不引入 IO 副作用。学习结果只能作为入参传入。
- **`learned_prior` 缺省（None）时，输出必须与当前 R2 逐字一致**——用现有 [`tests/test_l1_structural_signals.py`](../../../tests/test_l1_structural_signals.py) 与 [`tests/test_decision_mvp.py`](../../../tests/test_decision_mvp.py) 全绿证明零回归。
- 不新建平行 Beta / 升降级；本计划只消费"命中率 + 样本数"这一对已由 [`DomainRoleStats.hit_rate()`](../../../tools/rule_lifecycle.py:258) 提供的量，不自己算 Beta。
- 不接真实反馈数据、不持久化——那是 R5-B。
- 不改 orchestrator / v5_adapter 的默认行为（它们继续用缺省调用，等 R5-B 再决定是否传入真实 prior）。
- 每个任务结束跑绿相关测试；Windows cmd.exe：命令用 `&&` 串联，不用 `sed`/`grep`/`cat`；提交信息用中文。

## 背景事实（执行前必读，已实测确认）

1. [`route_schools(chart, context)`](../../../engine/decision/l1_school_router.py:82) 仅两个调用点：[`orchestrator.py:39`](../../../engine/decision/orchestrator.py:39)、[`v5_adapter.py:237`](../../../engine/decision/v5_adapter.py:237)。加末尾可选 keyword 参数不破坏它们。
2. 架构依赖测试 [`test_architecture_dependencies.py`](../../../tests/test_architecture_dependencies.py) 只禁 `engine/domain` 导入 tools；`engine/decision` 不在硬约束内，但方向文档要求它保持纯函数——本计划遵守更严的自律。
3. `SchoolApplicability` 的 `role` 是单值、`applicable_domains` 是列表、`applicability_score` 是浮点。降级即"role 沿 lead→co_lead→evidence_only→abstain 阶梯下移一档 + score 下调"。
4. 已实测注入原型：对完整四柱、无冲盘注入 `{"ziping": (0.1, 10)}`，ziping 的 role 从 lead 降为 co_lead、score 下降，其余派零变化；缺省时全盘不变。
5. 基线绿：`tests/test_l1_structural_signals.py + tests/test_decision_mvp.py` 当前 61 passed。

---

### Task 1: 定义 learned_prior 契约与降级纯函数（TDD）

**Files:**
- Modify: `engine/decision/l1_school_router.py`
- Test: `tests/test_l1_learned_prior.py`（新建）

**Interfaces:**
- Produces:
  - 模块常量 `_ROLE_LADDER = ("lead", "co_lead", "evidence_only", "abstain")`。
  - `_downgrade_role(role: str) -> str`：沿阶梯下移一档，abstain 到底不变。
  - `_apply_learned_prior(school: str, role: str, score: float, learned_prior: dict | None) -> tuple[str, float, list[str]]`：返回 `(new_role, new_score, extra_reasons)`；当 `learned_prior[school] = (hit_rate, n)` 满足 `n >= 5 and hit_rate < 0.35` 时降级并追加 reason；否则原样返回、reason 为空。
  - `learned_prior` 契约：`dict[str, tuple[float, int]]`，键为流派名，值为 `(历史命中率, 样本数)`。

- [ ] **Step 1: 写失败测试**

新建 [`tests/test_l1_learned_prior.py`](../../../tests/test_l1_learned_prior.py)：

```python
from __future__ import annotations

from engine.decision.l1_school_router import _apply_learned_prior, _downgrade_role


def test_downgrade_role_moves_one_step():
    assert _downgrade_role("lead") == "co_lead"
    assert _downgrade_role("co_lead") == "evidence_only"
    assert _downgrade_role("evidence_only") == "abstain"
    assert _downgrade_role("abstain") == "abstain"


def test_apply_prior_none_is_noop():
    role, score, reasons = _apply_learned_prior("ziping", "lead", 0.75, None)
    assert (role, score, reasons) == ("lead", 0.75, [])


def test_apply_prior_low_hit_downgrades():
    role, score, reasons = _apply_learned_prior("ziping", "lead", 0.75, {"ziping": (0.1, 10)})
    assert role == "co_lead"
    assert score < 0.75
    assert reasons  # 有解释


def test_apply_prior_insufficient_sample_is_noop():
    # n < 5 不触发
    role, score, reasons = _apply_learned_prior("ziping", "lead", 0.75, {"ziping": (0.1, 3)})
    assert (role, score, reasons) == ("lead", 0.75, [])


def test_apply_prior_high_hit_is_noop():
    role, score, reasons = _apply_learned_prior("ziping", "lead", 0.75, {"ziping": (0.9, 10)})
    assert (role, score, reasons) == ("lead", 0.75, [])


def test_apply_prior_other_school_untouched():
    role, score, reasons = _apply_learned_prior("duan_jianye", "co_lead", 0.6, {"ziping": (0.1, 10)})
    assert (role, score, reasons) == ("co_lead", 0.6, [])
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_l1_learned_prior.py -v`
Expected: FAIL，`ImportError: cannot import name '_apply_learned_prior'`。

- [ ] **Step 3: 实现常量与两个纯函数**

在 [`engine/decision/l1_school_router.py`](../../../engine/decision/l1_school_router.py) 的 `SCHOOL_PROFILES` 定义之前（`_chart_signals` 附近）新增：

```python
_ROLE_LADDER = ("lead", "co_lead", "evidence_only", "abstain")

# 学习先验降级门槛：样本足够且历史命中率过低才下调路由角色。
_PRIOR_MIN_SAMPLE = 5
_PRIOR_LOW_HIT_RATE = 0.35
_PRIOR_SCORE_PENALTY = 0.2


def _downgrade_role(role: str) -> str:
    """沿 lead→co_lead→evidence_only→abstain 下移一档；abstain 到底不变。"""

    try:
        idx = _ROLE_LADDER.index(role)
    except ValueError:
        return role
    return _ROLE_LADDER[min(idx + 1, len(_ROLE_LADDER) - 1)]


def _apply_learned_prior(
    school: str,
    role: str,
    score: float,
    learned_prior: dict[str, tuple[float, int]] | None,
) -> tuple[str, float, list[str]]:
    """按学习到的历史命中率下调低表现流派的路由角色与分数。

    learned_prior: {school: (hit_rate, sample_n)}；None 时零影响。
    仅在 sample_n >= _PRIOR_MIN_SAMPLE 且 hit_rate < _PRIOR_LOW_HIT_RATE 时降级。
    """

    if not learned_prior or school not in learned_prior:
        return role, score, []
    hit_rate, sample_n = learned_prior[school]
    if sample_n < _PRIOR_MIN_SAMPLE or hit_rate >= _PRIOR_LOW_HIT_RATE:
        return role, score, []
    new_role = _downgrade_role(role)
    new_score = max(0.0, round(score - _PRIOR_SCORE_PENALTY, 3))
    reason = f"学习先验：该派历史命中率 {hit_rate}（样本 {sample_n}）偏低，下调路由角色。"
    return new_role, new_score, [reason]
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_l1_learned_prior.py -v`
Expected: 6 PASS。

- [ ] **Step 5: 提交**

```bash
git add engine/decision/l1_school_router.py tests/test_l1_learned_prior.py && git commit -m "feat: 新增 learned_prior 降级纯函数与角色阶梯"
```

---

### Task 2: 把 learned_prior 接入 route_schools（TDD）

**Files:**
- Modify: `engine/decision/l1_school_router.py`（`route_schools` 签名与循环）
- Test: `tests/test_l1_learned_prior.py`（追加）

**Interfaces:**
- Consumes: `_apply_learned_prior`（Task 1）。
- Produces: `route_schools(chart, context, *, learned_prior=None)`；缺省时行为与 R2 逐字一致；传入低命中先验时对应流派 role 降级、score 下降、reasons 追加说明。

- [ ] **Step 1: 写失败测试**

在 [`tests/test_l1_learned_prior.py`](../../../tests/test_l1_learned_prior.py) 末尾追加：

```python
def test_route_schools_default_unchanged_by_prior_param():
    from engine.decision.l1_school_router import route_schools
    from engine.decision.models import ChartFactLedger, ContextFactLedger

    chart = ChartFactLedger(four_pillars={"year": "甲子", "month": "丁丑", "day": "庚辰", "hour": "癸未"})
    ctx = ContextFactLedger()

    without = {i.school: (i.role, i.applicability_score) for i in route_schools(chart, ctx)}
    with_none = {i.school: (i.role, i.applicability_score) for i in route_schools(chart, ctx, learned_prior=None)}

    assert without == with_none


def test_route_schools_downgrades_low_hit_school():
    from engine.decision.l1_school_router import route_schools
    from engine.decision.models import ChartFactLedger, ContextFactLedger

    chart = ChartFactLedger(four_pillars={"year": "甲子", "month": "丁丑", "day": "庚辰", "hour": "癸未"})
    ctx = ContextFactLedger()

    base = {i.school: i for i in route_schools(chart, ctx)}
    learned = {i.school: i for i in route_schools(chart, ctx, learned_prior={"ziping": (0.1, 10)})}

    assert base["ziping"].role == "lead"
    assert learned["ziping"].role == "co_lead"
    assert learned["ziping"].applicability_score < base["ziping"].applicability_score
    assert any("学习先验" in r for r in learned["ziping"].reasons)
    # 其它派不受影响
    for school in base:
        if school != "ziping":
            assert (learned[school].role, learned[school].applicability_score) == (
                base[school].role,
                base[school].applicability_score,
            )
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_l1_learned_prior.py::test_route_schools_downgrades_low_hit_school -v`
Expected: FAIL（`route_schools` 尚不接受 `learned_prior` 关键字参数 → TypeError）。

- [ ] **Step 3: 修改 route_schools 签名与循环**

在 [`route_schools()`](../../../engine/decision/l1_school_router.py:82) 的签名改为：

```python
def route_schools(
    chart: ChartFactLedger,
    context: ContextFactLedger,
    *,
    learned_prior: dict[str, tuple[float, int]] | None = None,
) -> list[SchoolApplicability]:
```

在 for 循环里，找到结构信号调整之后、`if not has_four:` 降级逻辑之后、`result.append(SchoolApplicability(...)` 构造之前的位置（即 role/score/reasons 都已算好、即将构造对象前），插入学习先验注入：

```python
        role, score, prior_reasons = _apply_learned_prior(school, role, score, learned_prior)
        reasons = reasons + prior_reasons
```

> 注意：必须放在 `result.append(...)` 之前、且在所有基础与结构信号调整之后，确保学习先验是"最后一层调整"。不要改动 `applicability_score=round(max(0.0, min(1.0, score)), 3)` 这行的钳制逻辑。

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_l1_learned_prior.py -v`
Expected: 全部 PASS（Task 1 六条 + Task 2 两条）。

- [ ] **Step 5: 零回归验证**

Run: `python -m pytest tests/test_l1_structural_signals.py tests/test_decision_mvp.py -q`
Expected: 全绿（应仍为既有数量，如 61 passed）。若任何用例 FAIL，说明缺省注入意外改变了行为——回到 Step 3 检查是否误把 learned_prior 默认值设成非 None，或注入位置错误，不要改这些既有测试。

- [ ] **Step 6: 提交**

```bash
git add engine/decision/l1_school_router.py tests/test_l1_learned_prior.py && git commit -m "feat: route_schools 支持 learned_prior 注入，缺省零回归"
```

---

### Task 3: 全量回归 + 文档状态更新

**Files:**
- Modify: `plans/layered-decision-system.md`
- Modify: `docs/superpowers/plans/2026-07-09-r5-cross-run-routing-learning-direction.md`

**Interfaces:**
- Produces: 架构文档记录 R5 注入端已完成、R5-B（真实反馈聚合与持久化）待做。

- [ ] **Step 1: 全量 decision 相关回归**

Run: `python -m pytest tests/test_l1_learned_prior.py tests/test_l1_structural_signals.py tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q`
Expected: 全部 PASS，0 FAIL。

- [ ] **Step 2: 在架构文档 §18 末尾追加 R5 状态**

在 [`plans/layered-decision-system.md`](../../../plans/layered-decision-system.md) 的 `### Phase R4：分层准确率看板` 小节之后，新增一节：

```markdown
### Phase R5：流派适用性学习先验注入（注入端）

> 状态：注入端已完成（route_schools 支持可选 learned_prior，缺省零回归，低命中先验可下调对应流派角色与分数，见 tests/test_l1_learned_prior.py）。真实反馈聚合出 learned_prior 并持久化回灌（R5-B）尚未实现，依赖真实反馈样本与 tools 层落盘，属数据工程而非纯路由重构。方向依据见 docs/superpowers/plans/2026-07-09-r5-cross-run-routing-learning-direction.md。
```

- [ ] **Step 3: 在方向文档末尾标注 First Proof Point 已落地**

在 [`docs/superpowers/plans/2026-07-09-r5-cross-run-routing-learning-direction.md`](2026-07-09-r5-cross-run-routing-learning-direction.md) 的 §9 First Proof Point 小节标题下第一行前插入：

```markdown
> 状态：已落地。route_schools(chart, context, *, learned_prior=None) 已实现，缺省零回归、合成低命中先验能下调对应流派，见 tests/test_l1_learned_prior.py 与执行计划 docs/superpowers/plans/2026-07-09-r5-learned-prior-injection-refactor.md。R5-B（真实反馈聚合 + 持久化回灌）待启动。
```

- [ ] **Step 4: 提交**

```bash
git add plans/layered-decision-system.md docs/superpowers/plans/2026-07-09-r5-cross-run-routing-learning-direction.md && git commit -m "docs: 标记 R5 learned_prior 注入端已完成，R5-B 待启动"
```

---

## 验收总清单（全部完成后执行一次）

- [ ] `python -m pytest tests/test_l1_learned_prior.py -q` 全绿。
- [ ] `route_schools(..., learned_prior=None)` 与 `route_schools(...)`（不传）输出逐字一致。
- [ ] 现有 `tests/test_l1_structural_signals.py` + `tests/test_decision_mvp.py` 零回归（数量不减、无新 FAIL）。
- [ ] 注入 `{"ziping": (0.1, 10)}` 后 ziping 从 lead 降为 co_lead、score 下降、reasons 含"学习先验"；其它派不变。
- [ ] [`route_schools()`](../../../engine/decision/l1_school_router.py:82) 未 import tools、未做任何文件 IO。

## 证伪口径（对照方向文档 §10）

- 若为了接入 learned_prior 不得不让 [`route_schools()`](../../../engine/decision/l1_school_router.py:82) 读文件或 import tools，则违反"纯函数"原则，方向需回到决策文档 §4 重议——不要为省事把 IO 塞进 engine。
- 若缺省 learned_prior 无法逐字回退（既有测试 FAIL），说明注入不是"最后一层可选调整"，实现有误，须修复而非改基线测试。
- 本计划**只**证明"注入端可用且零回归"；它**不**代表系统已在用真实反馈学习——真实 learned_prior 的来源（聚合 DomainRoleStats / R3 router 校准信号）与持久化是 R5-B，未做即未做，不得对外宣称"路由已自我学习"。

## Self-Review 记录

- Spec 覆盖：方向文档 §9 First Proof Point 的三条（加可选入参、缺省逐字回退、合成低命中先验能降级）分别由 Task 1（降级函数）+ Task 2（接入 + 零回归验证）覆盖。
- Placeholder 扫描：无 TBD / "适当处理"；每个代码步骤给出完整可粘贴代码。
- 类型一致：`learned_prior: dict[str, tuple[float, int]] | None` 在 `_apply_learned_prior` 与 `route_schools` 两处签名一致；`_ROLE_LADDER` 与 `_downgrade_role` 前后一致；`SchoolApplicability` 字段（role/applicability_score/reasons）与 [`models.py`](../../../engine/decision/models.py:90) 一致。
- 已知风险显式化：纯函数约束、缺省零回归、不接真实数据（R5-B 延后）均写入 Global Constraints 与证伪口径。
- 已实测确认：基线 61 passed；注入原型（ziping 低命中→降级、余者不变、缺省不变）退出码 0 通过。
