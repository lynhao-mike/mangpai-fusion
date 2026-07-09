# L1 流派适用性路由前置重构 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把生产 v5→decision 链路中“先让流派发言、再从命题池反推适用性”的倒置依赖，改成“先用真实规则路由决定流派角色、再让被授权流派进入命题层”。

**Architecture:** 现有 [`engine/decision/`](../../../engine/decision/) 已落地完整 L0-L9 与 `DecisionRun.validate_trace()`。本重构只改一个函数依赖点：让 [`decision_run_from_v5()`](../../../engine/decision/v5_adapter.py:251) 调用已存在的 [`route_schools()`](../../../engine/decision/l1_school_router.py:52) 产出 L1 适用性，而不是调用 [`_school_applicability()`](../../../engine/decision/v5_adapter.py:70) 从命题反推。不新增模型、不切默认报告入口、不搬目录。

**Tech Stack:** Python 3、dataclass、pytest。全部为纯内存数据变换，无外部依赖。

## Global Constraints

- 事实源与规则以 [`AGENTS.md`](../../../AGENTS.md) 为准；架构判断以 [`plans/layered-decision-system.md`](../../../plans/layered-decision-system.md) 为准。
- 不新增第三套 run / decision 模型。
- 不切换默认报告入口（保持 [`tools/render_report.py`](../../../tools/render_report.py) 为 legacy 正式入口）。
- 不改 v5 命理规则本身，只改 L1 适用性的来源。
- 每个任务结束必须 `python -m pytest` 跑绿相关测试；`DecisionRun.validate_trace()` 必须返回 `[]`。
- 提交信息用中文，前缀 `refactor:` / `test:` / `feat:`。
- 全程 Windows cmd.exe：命令用 `&&` 串联；不要用 `sed`/`grep`/`cat`。

## 背景事实（执行前必读，避免踩坑）

1. [`decision_run_from_v5()`](../../../engine/decision/v5_adapter.py:251) 内部已经构造了 `chart = _chart_to_ledger(output, raw_hash)`，并用 `ContextFactLedger(preserved_text_blocks=["v5_adapter"])` 作为上下文。这两个正是 [`route_schools()`](../../../engine/decision/l1_school_router.py:52) 需要的入参。
2. [`route_schools()`](../../../engine/decision/l1_school_router.py:52) 产出 6 个流派（含 `ren_fuhong`），而 v5 只有 5 派（`ziping / ditiansui / gao_dechen / duan_jianye / yang_qingjuan`）。多出的 `ren_fuhong` 只有适用性、没有命题——这对 [`validate_trace()`](../../../engine/decision/models.py:320) 合法：校验只要求“claim.school 必须在 applicability 中”，不要求反向。
3. [`_claims()`](../../../engine/decision/v5_adapter.py:93) 已经按 `role_by_school.get(claim.school) != "abstain"` 过滤——它天然支持“被路由为 abstain 的流派不产出命题”。所以换成 route_schools 后，abstain 流派的命题会被正确丢弃，无需改 `_claims`。
4. 现有测试 [`test_decision_run_from_v5_preserves_trace`](../../../tests/test_decision_v5_adapter.py:9) 里有一条断言：
   `assert len(run.school_claims) == len([c for c in output.claims if c.stance != "abstain"])`
   这条断言把命题数量耦合到 **claim 的 stance**。重构后命题过滤依据变成 **L1 路由的 role**，两者口径不同。此断言很可能需要改写为“按 L1 授权角色过滤”。**这属于预期内的测试更新，不是回归 bug**，在 Task 3 显式处理。
5. `route_schools` 在 `analysis_focus_text` 为空时不会把任何派设成 abstain（无 focus 就无“焦点不匹配”）。空上下文下 6 派均为 `lead / co_lead / evidence_only`，因此 5 派 v5 命题都会保留。

---

### Task 1: 新增回归测试——L1 适用性必须来自路由而非命题反推

**Files:**
- Test: `tests/test_decision_v5_adapter.py`（在文件末尾追加）

**Interfaces:**
- Consumes: [`run_v5()`](../../../engine/v5/runner.py)（签名 `run_v5(chart: dict) -> V5Output`）、[`decision_run_from_v5()`](../../../engine/decision/v5_adapter.py:251)（签名 `decision_run_from_v5(output: V5Output, *, raw_text: str = "") -> DecisionRun`）。
- Produces: 两个测试函数，作为本次重构的验收护栏。

- [ ] **Step 1: 追加失败测试**

在 [`tests/test_decision_v5_adapter.py`](../../../tests/test_decision_v5_adapter.py) 末尾追加：

```python
def test_l1_applicability_comes_from_router_not_claim_pool() -> None:
    # route_schools 覆盖 6 派（含 ren_fuhong），v5 只产 5 派命题。
    # 若 L1 来自真实路由，ren_fuhong 会出现在适用性里但没有命题；
    # 若 L1 仍从命题池反推，ren_fuhong 不会出现。
    output = run_v5({"case_id": "C-TEST-L1-ROUTER", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})

    run = decision_run_from_v5(output)

    applicability_schools = {item.school for item in run.school_applicability}
    claim_schools = {item.school for item in run.school_claims}

    assert "ren_fuhong" in applicability_schools, "L1 适用性应来自 route_schools（含 ren_fuhong），而非命题池反推"
    assert "ren_fuhong" not in claim_schools, "ren_fuhong 无 v5 命题，不应出现在命题层"
    assert run.validate_trace() == []


def test_l1_router_reasons_are_not_claim_pool_placeholder() -> None:
    output = run_v5({"case_id": "C-TEST-L1-REASON", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})

    run = decision_run_from_v5(output)

    joined_reasons = " ".join(reason for item in run.school_applicability for reason in item.reasons)
    assert "命题池反推" not in joined_reasons, "L1 reasons 不应再是命题池反推占位文案"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_decision_v5_adapter.py::test_l1_applicability_comes_from_router_not_claim_pool tests/test_decision_v5_adapter.py::test_l1_router_reasons_are_not_claim_pool_placeholder -v`
Expected: 两条 FAIL。第一条因 `ren_fuhong` 不在当前 `_school_applicability` 反推结果中；第二条因当前 reasons 含“命题池反推”占位文案（见 [`_school_applicability()`](../../../engine/decision/v5_adapter.py:70)）。

- [ ] **Step 3: 提交失败测试**

```bash
git add tests/test_decision_v5_adapter.py && git commit -m "test: 新增 L1 路由前置回归测试（当前预期失败）"
```

---

### Task 2: 让 decision_run_from_v5 用 route_schools 前置 L1

**Files:**
- Modify: `engine/decision/v5_adapter.py`

**Interfaces:**
- Consumes: [`route_schools(chart, context)`](../../../engine/decision/l1_school_router.py:52) → `list[SchoolApplicability]`；`chart: ChartFactLedger`；`context: ContextFactLedger`。
- Produces: 重构后的 [`decision_run_from_v5()`](../../../engine/decision/v5_adapter.py:251)，其 `school_applicability` 来自路由；`_claims()` 依赖不变。

- [ ] **Step 1: 在 v5_adapter.py 顶部导入 route_schools**

找到现有 import 块（[`engine/decision/v5_adapter.py`](../../../engine/decision/v5_adapter.py:10) 附近的 `from engine.decision.l9_calibration import build_calibration_actions`），在其后新增一行：

```python
from engine.decision.l1_school_router import route_schools
```

- [ ] **Step 2: 替换 decision_run_from_v5 中的 L1 来源**

在 [`decision_run_from_v5()`](../../../engine/decision/v5_adapter.py:251) 里，找到这一行：

```python
    applicability = _school_applicability(output)
```

替换为（`chart` 与 `context` 均在同函数内已可得；context 原本内联在 return 里构造，这里提前构造并复用）：

```python
    context = ContextFactLedger(preserved_text_blocks=["v5_adapter"])
    applicability = route_schools(chart, context)
```

- [ ] **Step 3: 复用同一个 context，避免重复构造**

在同函数结尾的 `return DecisionRun(...)` 中，找到：

```python
        context_ledger=ContextFactLedger(preserved_text_blocks=["v5_adapter"]),
```

替换为：

```python
        context_ledger=context,
```

- [ ] **Step 4: 运行 Task 1 的新测试确认通过**

Run: `python -m pytest tests/test_decision_v5_adapter.py::test_l1_applicability_comes_from_router_not_claim_pool tests/test_decision_v5_adapter.py::test_l1_router_reasons_are_not_claim_pool_placeholder -v`
Expected: 两条 PASS。

- [ ] **Step 5: 提交实现**

```bash
git add engine/decision/v5_adapter.py && git commit -m "refactor: L1 适用性改由 route_schools 前置产出，替换命题池反推"
```

---

### Task 3: 修复被 stance 耦合的历史断言，改为按 L1 授权角色

**Files:**
- Modify: `tests/test_decision_v5_adapter.py:9`（`test_decision_run_from_v5_preserves_trace`）

**Interfaces:**
- Consumes: `run.school_applicability`（`list[SchoolApplicability]`，字段 `school`、`role`）、`run.school_claims`（`list[SchoolClaim]`，字段 `school`）。
- Produces: 与新 L1 语义一致的断言。

- [ ] **Step 1: 运行全量 decision 测试，观察实际断点**

Run: `python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -v`
Expected: 除 Task 1 两条新测试 PASS 外，[`test_decision_run_from_v5_preserves_trace`](../../../tests/test_decision_v5_adapter.py:9) 可能 FAIL，原因是 `len(run.school_claims)` 不再等于 `len([c for c in output.claims if c.stance != "abstain"])`。若它意外仍 PASS，跳过 Step 2、直接进入 Step 3 并记录“无需改断言”。

- [ ] **Step 2: 把 stance 耦合断言改为 role 语义断言**

在 [`test_decision_run_from_v5_preserves_trace`](../../../tests/test_decision_v5_adapter.py:9) 中，找到：

```python
    assert len(run.school_claims) == len([c for c in output.claims if c.stance != "abstain"])
```

替换为（命题数量应等于：v5 命题里、其流派被 L1 授权为非 abstain 的那些）：

```python
    abstained_schools = {item.school for item in run.school_applicability if item.role == "abstain"}
    expected_claims = [
        c for c in output.claims
        if c.claim_id and c.school and c.domain and c.school not in abstained_schools
    ]
    assert len(run.school_claims) == len(expected_claims)
```

- [ ] **Step 3: 运行全量 decision 测试确认全绿**

Run: `python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -v`
Expected: 全部 PASS，无 FAIL。

- [ ] **Step 4: 提交测试更新**

```bash
git add tests/test_decision_v5_adapter.py && git commit -m "test: 命题数量断言改为按 L1 授权角色而非 claim stance"
```

---

### Task 4: 删除或降级不再使用的 _school_applicability

**Files:**
- Modify: `engine/decision/v5_adapter.py:70`

**Interfaces:**
- Consumes: 无（确认该函数在仓库内不再被引用后删除）。
- Produces: 更干净的 adapter，无死代码。

- [ ] **Step 1: 确认 _school_applicability 已无引用**

Run: `python -m pytest -q` 之前，先全仓搜索引用。用 search 工具或：
`python -c "import subprocess,sys; import pathlib; hits=[str(p) for p in pathlib.Path('.').rglob('*.py') if '_school_applicability' in p.read_text(encoding='utf-8')]; print(hits)"`
Expected: 输出仅包含 `engine\\decision\\v5_adapter.py` 一个文件（即只剩定义处，无其它调用）。若还有其它文件引用，停止并回到 Task 2 排查。

- [ ] **Step 2: 删除 _school_applicability 函数定义**

在 [`engine/decision/v5_adapter.py`](../../../engine/decision/v5_adapter.py:70) 删除整段 `def _school_applicability(output: V5Output) -> list[SchoolApplicability]:` 函数（从 `def` 行到其 `return result` 行，含函数体）。不要删除其它函数。

- [ ] **Step 3: 运行全量测试确认无回归**

Run: `python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q`
Expected: 全部 PASS。

- [ ] **Step 4: 运行更大范围回归，确认未波及 preprod / v5**

Run: `python -m pytest tests/test_decision_v5_adapter.py tests/test_decision_mvp.py tests/v5 -q`
Expected: 全部 PASS。（若 `tests/v5` 目录不存在或为空，忽略该路径，仅跑前两个。）

- [ ] **Step 5: 提交删除**

```bash
git add engine/decision/v5_adapter.py && git commit -m "refactor: 删除已弃用的 _school_applicability 命题反推逻辑"
```

---

### Task 5: 更新架构文档状态标记

**Files:**
- Modify: `plans/layered-decision-system.md`

**Interfaces:**
- Consumes: 无。
- Produces: 文档 §18 Phase R1 标记为已完成，避免后续执行者重复做。

- [ ] **Step 1: 在 §18 Phase R1 标题后追加完成标记**

在 [`plans/layered-decision-system.md`](../../../plans/layered-decision-system.md) 找到 `### Phase R1：扳正生产路由依赖（核心）`，在该标题下第一行前插入一行：

```markdown
> 状态：已完成（route_schools 已前置于生产 v5→decision，_school_applicability 已删除，回归测试见 tests/test_decision_v5_adapter.py）。
```

- [ ] **Step 2: 提交文档更新**

```bash
git add plans/layered-decision-system.md && git commit -m "docs: 标记 Phase R1 路由前置已完成"
```

---

## 验收总清单（全部完成后执行一次）

- [ ] `python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q` 全绿。
- [ ] 新测试 `test_l1_applicability_comes_from_router_not_claim_pool` 存在且 PASS。
- [ ] `engine/decision/v5_adapter.py` 中不再出现 `_school_applicability`。
- [ ] 生产链路 DecisionRun 的 `school_applicability` 含 `ren_fuhong`（证明来自路由）。
- [ ] `validate_trace()` 对生产链路返回 `[]`。

## 证伪口径（对照架构文档 §19.2）

- 若接入后几乎所有命盘所有流派恒为 `lead / co_lead`（路由无区分力），说明 L1 只是换了个橡皮图章，需回到 [`plans/layered-decision-system.md`](../../../plans/layered-decision-system.md) §0 重判方向，而不是继续加规则。
- 本计划只证明“路由已前置、依赖已扳正”；它**不**证明准确率提升。准确率验证属于 Phase R3/R4，需真实反馈样本，不在本计划范围。

## Self-Review 记录

- Spec 覆盖：Phase R1 的三项动作（route_schools 前置、删除反推、abstain 流派不产命题）分别由 Task 2 / Task 4 / Task 1+Task 3 覆盖。
- Placeholder 扫描：无 TBD / “适当处理” 类占位；每个代码步骤均给出完整可粘贴代码。
- 类型一致：`route_schools(chart, context)`、`SchoolApplicability.role`、`SchoolClaim.school` 均与 [`engine/decision/models.py`](../../../engine/decision/models.py) 现有定义一致。
- 已知风险显式化：stance vs role 口径差异在 Task 3 显式处理，并允许“意外仍 PASS 则跳过”。
