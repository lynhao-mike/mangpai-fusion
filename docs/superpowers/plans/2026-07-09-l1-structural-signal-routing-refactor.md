# L1 路由接入盘面结构信号（Phase R2）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 [`route_schools()`](../../../engine/decision/l1_school_router.py:52) 不再只看四柱完整性与分析焦点，而是从四柱本身派生结构信号（五行偏枯、地支相冲），据此对相关流派做差异化打分与窄口径角色升级——使不同结构类型的命盘产出不同的适用性分布。

**Architecture:** R1 已让真实路由前置于生产命题层。R2 在同一个 [`route_schools()`](../../../engine/decision/l1_school_router.py:52) 里增加一个只读 `four_pillars` 的结构信号函数，并把信号接入既有打分逻辑。`applicability_score` 已被 [`l2_claims.py`](../../../engine/decision/l2_claims.py:46) 用作 SchoolClaim 的 confidence，因此调分有真实下游效果，不是橡皮图章。

**Tech Stack:** Python 3、dataclass、pytest、既有谓词库 [`engine/predicates/`](../../../engine/predicates/)。纯内存计算，无外部依赖。

## Global Constraints

- 事实源以 [`AGENTS.md`](../../../AGENTS.md) 为准；架构判断以 [`plans/layered-decision-system.md`](../../../plans/layered-decision-system.md) 为准。
- **R2 只允许从 `chart.four_pillars` 派生结构信号。** 禁止读取 `siling` / `pillar_details` / `void_by_pillar`——这些字段在生产与 MVP 两条 L0 路径上都未被填充（见 [`l0_wenzhen.py`](../../../engine/decision/l0_wenzhen.py:113) 与 `v5_adapter._chart_to_ledger`），读了就是空操作。
- 不新增第三套 run / decision 模型，不切默认报告入口，不搬目录，不改 v5 命理规则。
- 复用既有谓词，不自己重写五行 / 地支关系：[`gan_to_wuxing()`](../../../engine/predicates/ganzhi.py:65)、[`zhi_to_wuxing()`](../../../engine/predicates/ganzhi.py:72)、[`is_gan()`](../../../engine/predicates/ganzhi.py:33)、[`is_zhi()`](../../../engine/predicates/ganzhi.py:38)、[`zhi_chong()`](../../../engine/predicates/relations.py:246)。
- 每个任务结束跑绿相关测试；`DecisionRun.validate_trace()` 必须返回 `[]`。
- 角色调整必须**窄口径且单调**：只在明确结构条件下升级，不引入全局综合评分（违反架构 §3.2）。
- Windows cmd.exe：命令用 `&&` 串联；不要用 `sed`/`grep`/`cat`；提交信息用中文。

## 背景事实（执行前必读）

1. `chart.four_pillars` 是 `dict[str,str]`，键为 `year/month/day/hour`，值为干支串如 `"甲子"`；缺失柱值为 `"_"` 或空（见 [`l0_wenzhen.py`](../../../engine/decision/l0_wenzhen.py:65)）。
2. [`route_schools()`](../../../engine/decision/l1_school_router.py:52) 现有逻辑：`has_four = 完整四柱`；ziping/ditiansui 有四柱则 `lead`；gao_dechen 恒 `evidence_only`；ren_fuhong 无大运则 `evidence_only`；focus 与该派域无交集且非 ziping/ditiansui 则 `abstain`；无四柱统一降级。
3. `applicability_score` → [`l2_claims.py`](../../../engine/decision/l2_claims.py:46) 的 `confidence` → L3/L4/L5，间接影响 L6 winner。改分有真实效果。
4. [`test_l1_router_assigns_roles_and_abstains_irrelevant_schools`](../../../tests/test_decision_mvp.py:182) 硬钉了若干角色（含 `duan_jianye == "co_lead"`）。R2 的窄口径升级可能把 `duan_jianye` 在"地支见冲"的盘上提到 `lead`，因此该断言需改成结构性断言（`in {"co_lead","lead"}`）。**这是预期内测试更新，不是回归**，在 Task 4 处理。
5. 谓词是纯函数，用局部 import 引入以避免潜在导入环（与仓库测试里的局部 import 风格一致）。

---

### Task 1: 新增结构信号函数 _chart_signals（TDD）

**Files:**
- Modify: `engine/decision/l1_school_router.py`
- Test: `tests/test_l1_structural_signals.py`（新建）

**Interfaces:**
- Produces: `_chart_signals(chart: ChartFactLedger) -> dict[str, object]`，返回键：`complete: bool`（是否 4 柱齐全且合法）、`skewed: bool`（五行偏枯：某行占比≥0.5 或缺≥2 行）、`missing_count: int`、`has_chong: bool`（任意两地支相冲）。

- [ ] **Step 1: 写失败测试**

新建 [`tests/test_l1_structural_signals.py`](../../../tests/test_l1_structural_signals.py)：

```python
from __future__ import annotations

from engine.decision.l1_school_router import _chart_signals
from engine.decision.models import ChartFactLedger


def test_chart_signals_detects_complete_and_chong() -> None:
    # 子午相冲：day 子、hour 午
    chart = ChartFactLedger(four_pillars={"year": "甲寅", "month": "乙卯", "day": "丙子", "hour": "戊午"})

    signals = _chart_signals(chart)

    assert signals["complete"] is True
    assert signals["has_chong"] is True


def test_chart_signals_detects_skew_and_missing() -> None:
    # 全木盘：四干四支尽量集中在木，缺多行
    chart = ChartFactLedger(four_pillars={"year": "甲寅", "month": "乙卯", "day": "甲寅", "hour": "乙卯"})

    signals = _chart_signals(chart)

    assert signals["skewed"] is True
    assert signals["missing_count"] >= 2


def test_chart_signals_incomplete_marks_not_complete() -> None:
    chart = ChartFactLedger(four_pillars={"year": "甲子", "month": "_", "day": "丙寅", "hour": "丁卯"})

    signals = _chart_signals(chart)

    assert signals["complete"] is False
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_l1_structural_signals.py -v`
Expected: FAIL，`ImportError: cannot import name '_chart_signals'`。

- [ ] **Step 3: 实现 _chart_signals**

在 [`engine/decision/l1_school_router.py`](../../../engine/decision/l1_school_router.py) 顶部 import 块之后、`SCHOOL_PROFILES` 定义之前，新增函数：

```python
from collections import Counter


def _chart_signals(chart: ChartFactLedger) -> dict[str, object]:
    """只从 four_pillars 派生结构信号（R2 约束：不读 siling / pillar_details / void）。"""

    from engine.predicates.ganzhi import gan_to_wuxing, is_gan, is_zhi, zhi_to_wuxing
    from engine.predicates.relations import zhi_chong

    gans: list[str] = []
    zhis: list[str] = []
    for value in chart.four_pillars.values():
        text = (value or "").strip()
        if len(text) >= 2 and is_gan(text[0]) and is_zhi(text[1]):
            gans.append(text[0])
            zhis.append(text[1])

    complete = len(gans) == 4
    elements = [gan_to_wuxing(g) for g in gans] + [zhi_to_wuxing(z) for z in zhis]
    distribution = Counter(elements)
    present = set(distribution)
    missing_count = len({"木", "火", "土", "金", "水"} - present)
    total = len(elements)
    dominant = max(distribution.values()) if distribution else 0
    skewed = total > 0 and (dominant / total >= 0.5 or missing_count >= 2)
    has_chong = any(zhi_chong(zhis[i], zhis[j]) for i in range(len(zhis)) for j in range(i + 1, len(zhis)))

    return {
        "complete": complete,
        "skewed": bool(skewed),
        "missing_count": missing_count,
        "has_chong": bool(has_chong),
    }
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_l1_structural_signals.py -v`
Expected: 3 PASS。

- [ ] **Step 5: 提交**

```bash
git add engine/decision/l1_school_router.py tests/test_l1_structural_signals.py && git commit -m "feat: 新增 _chart_signals 从四柱派生五行偏枯与地支冲信号"
```

---

### Task 2: 把结构信号接入 route_schools 打分（TDD）

**Files:**
- Modify: `engine/decision/l1_school_router.py`（`route_schools` 函数体）
- Test: `tests/test_l1_structural_signals.py`（追加）

**Interfaces:**
- Consumes: `_chart_signals(chart)`（Task 1）。
- Produces: `route_schools` 在"五行偏枯"时提升 `ditiansui` 的 `applicability_score` 并追加 reason；在"地支见冲且四柱齐全"时提升 `duan_jianye` / `ren_fuhong` 的 score 并把其 `co_lead` 升为 `lead`，追加 reason。其余流派与既有逻辑不变。

- [ ] **Step 1: 写失败测试**

在 [`tests/test_l1_structural_signals.py`](../../../tests/test_l1_structural_signals.py) 末尾追加：

```python
def test_route_schools_upgrades_ditiansui_score_on_skewed_chart() -> None:
    from engine.decision.l1_school_router import route_schools
    from engine.decision.models import ContextFactLedger

    skewed = {"year": "甲寅", "month": "乙卯", "day": "甲寅", "hour": "乙卯"}
    balanced = {"year": "甲子", "month": "丁丑", "day": "庚辰", "hour": "壬午"}

    skewed_dt = next(i for i in route_schools(ChartFactLedger(four_pillars=skewed), ContextFactLedger()) if i.school == "ditiansui")
    balanced_dt = next(i for i in route_schools(ChartFactLedger(four_pillars=balanced), ContextFactLedger()) if i.school == "ditiansui")

    assert skewed_dt.applicability_score > balanced_dt.applicability_score
    assert any("偏枯" in r or "气势" in r for r in skewed_dt.reasons)


def test_route_schools_upgrades_duan_ren_role_on_chong_chart() -> None:
    from engine.decision.l1_school_router import route_schools
    from engine.decision.models import ContextFactLedger

    chong = {"year": "甲寅", "month": "乙卯", "day": "丙子", "hour": "戊午"}
    routed = {i.school: i for i in route_schools(ChartFactLedger(four_pillars=chong), ContextFactLedger())}

    assert routed["duan_jianye"].role == "lead"
    assert any("冲" in r for r in routed["duan_jianye"].reasons)
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_l1_structural_signals.py::test_route_schools_upgrades_ditiansui_score_on_skewed_chart tests/test_l1_structural_signals.py::test_route_schools_upgrades_duan_ren_role_on_chong_chart -v`
Expected: 两条 FAIL（当前无信号调分逻辑，score 相等、role 仍 co_lead）。

- [ ] **Step 3: 在 route_schools 内接入信号**

在 [`route_schools()`](../../../engine/decision/l1_school_router.py:52) 里，找到：

```python
    focus = _focus_domains(context)
    has_four = len([v for v in chart.four_pillars.values() if v and v != "_"]) == 4
    has_dayun = bool(chart.dayun_steps)
    result: list[SchoolApplicability] = []
```

在其后新增一行获取信号：

```python
    signals = _chart_signals(chart)
```

然后在 for 循环内、`if not has_four:` 这段**之前**（即基础 role/score 已算好、降级逻辑之前），插入结构信号调整：

```python
        if signals["skewed"] and school == "ditiansui":
            score += 0.1
            reasons.append("五行偏枯或缺行明显，调候气势派更适用。")
        if signals["has_chong"] and signals["complete"] and school in {"duan_jianye", "ren_fuhong"}:
            score += 0.05
            if role == "co_lead":
                role = "lead"
            reasons.append("地支见冲，做功 / 应期派可主审事件触发。")
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_l1_structural_signals.py -v`
Expected: 全部 PASS（Task 1 三条 + Task 2 两条）。

- [ ] **Step 5: 提交**

```bash
git add engine/decision/l1_school_router.py tests/test_l1_structural_signals.py && git commit -m "feat: route_schools 按五行偏枯与地支冲做差异化打分与角色升级"
```

---

### Task 3: 新增"结构信号产生分布差异"的判别性回归测试

**Files:**
- Test: `tests/test_l1_structural_signals.py`（追加）

**Interfaces:**
- Consumes: `route_schools`。
- Produces: 一条证明"不同结构类型命盘产出不同适用性分布"的护栏测试，对应架构 §19.2 证伪口径（防止路由退化为橡皮图章）。

- [ ] **Step 1: 写测试**

在 [`tests/test_l1_structural_signals.py`](../../../tests/test_l1_structural_signals.py) 末尾追加：

```python
def test_different_chart_structures_produce_different_role_distributions() -> None:
    from engine.decision.l1_school_router import route_schools
    from engine.decision.models import ContextFactLedger

    chong = {"year": "甲寅", "month": "乙卯", "day": "丙子", "hour": "戊午"}
    no_chong = {"year": "甲子", "month": "丁丑", "day": "庚辰", "hour": "癸未"}

    roles_chong = {i.school: i.role for i in route_schools(ChartFactLedger(four_pillars=chong), ContextFactLedger())}
    roles_plain = {i.school: i.role for i in route_schools(ChartFactLedger(four_pillars=no_chong), ContextFactLedger())}

    # 至少在 duan_jianye / ren_fuhong 上，两类盘的角色分布不同（否则路由无区分力）。
    assert (roles_chong["duan_jianye"], roles_chong["ren_fuhong"]) != (
        roles_plain["duan_jianye"],
        roles_plain["ren_fuhong"],
    ), "地支冲盘与非冲盘的角色分布应不同，否则 R2 路由退化为橡皮图章"
```

- [ ] **Step 2: 运行确认通过**

Run: `python -m pytest tests/test_l1_structural_signals.py::test_different_chart_structures_produce_different_role_distributions -v`
Expected: PASS。若 FAIL，说明 Task 2 的信号调整没有产生分布差异，回到 Task 2 排查，不要放宽断言。

- [ ] **Step 3: 提交**

```bash
git add tests/test_l1_structural_signals.py && git commit -m "test: 新增结构信号路由区分力护栏测试"
```

---

### Task 4: 修复被静态角色钉死的历史 MVP 测试

**Files:**
- Modify: `tests/test_decision_mvp.py:201`（`test_l1_router_assigns_roles_and_abstains_irrelevant_schools`）

**Interfaces:**
- Consumes: `route_schools` 结果。
- Produces: 对 `duan_jianye` 改为结构性断言，兼容信号驱动的角色升级。

- [ ] **Step 1: 运行全量 decision 测试，观察实际断点**

Run: `python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -v`
Expected: 若 [`test_l1_router_assigns_roles_and_abstains_irrelevant_schools`](../../../tests/test_decision_mvp.py:182) FAIL，通常是 `duan_jianye` 角色因该盘地支冲被升为 `lead`。若它仍 PASS（该盘无冲），跳过 Step 2，直接进 Step 3 并记录"无需改断言"。

- [ ] **Step 2: 把 duan_jianye 等值断言改为结构性断言**

在 [`test_l1_router_assigns_roles_and_abstains_irrelevant_schools`](../../../tests/test_decision_mvp.py:182) 中找到：

```python
    assert routed["duan_jianye"].role == "co_lead"
```

替换为：

```python
    assert routed["duan_jianye"].role in {"co_lead", "lead"}
```

其余断言（ziping/ditiansui==lead、gao_dechen==abstain）保持不变——它们不受 R2 信号影响。

- [ ] **Step 3: 运行全量 decision 测试确认全绿**

Run: `python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py tests/test_l1_structural_signals.py -q`
Expected: 全部 PASS，0 FAIL。

- [ ] **Step 4: 提交**

```bash
git add tests/test_decision_mvp.py && git commit -m "test: L1 路由角色断言改为兼容结构信号升级"
```

---

### Task 5: 更新架构文档 Phase R2 状态

**Files:**
- Modify: `plans/layered-decision-system.md`

**Interfaces:**
- Produces: §18 Phase R2 标记为已完成。

- [ ] **Step 1: 定位 Phase R2 标题**

用 search 工具在 [`plans/layered-decision-system.md`](../../../plans/layered-decision-system.md) 找 `### Phase R2：路由输入从盘面事实取信号`。

- [ ] **Step 2: 在标题下插入状态行**

在该标题下第一行前插入：

```markdown
> 状态：已完成（route_schools 已接入 _chart_signals：五行偏枯提升 ditiansui 分数、地支冲提升 duan_jianye / ren_fuhong 角色；区分力护栏见 tests/test_l1_structural_signals.py）。R2 仅从 four_pillars 派生信号，未读取未填充字段。
```

- [ ] **Step 3: 提交**

```bash
git add plans/layered-decision-system.md && git commit -m "docs: 标记 Phase R2 结构信号路由已完成"
```

---

## 验收总清单（全部完成后执行一次）

- [ ] `python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py tests/test_l1_structural_signals.py -q` 全绿。
- [ ] `_chart_signals` 只读 `four_pillars`，未引用 `siling` / `pillar_details` / `void_by_pillar`。
- [ ] 地支冲盘与非冲盘在 `duan_jianye` / `ren_fuhong` 上角色分布不同（区分力护栏 PASS）。
- [ ] 五行偏枯盘的 `ditiansui` 分数高于均衡盘。
- [ ] `validate_trace()` 对 `run_decision_mvp` 返回 `[]`（Task 4 全量测试已隐含覆盖）。

## 证伪口径（对照架构 §19.2）

- 若接入信号后各类命盘的角色分布仍几乎相同（区分力护栏只能靠人为极端盘勉强通过），说明信号选得没有区分力，应回到 [`plans/layered-decision-system.md`](../../../plans/layered-decision-system.md) §0 重判信号选择，而不是继续堆更多信号。
- R2 只证明"路由有结构区分力且分数流入下游"；它**不**证明准确率提升。准确率验证依赖真实反馈，属 Phase R3/R4。
- 若发现 score 差异并未流入任何下游判断（例如未来重构切断了 L2 claim confidence = applicability_score 的链路），R2 立即退化为橡皮图章，须在 R3 前修复。

## Self-Review 记录

- Spec 覆盖：架构 §18 Phase R2 目标（路由不只看四柱完整性、按结构信号区分、每 role 有 reasons/blockers）由 Task 1（信号）+ Task 2（接入打分与角色）+ Task 3（区分力护栏）覆盖。
- Placeholder 扫描：无 TBD / "适当处理"；每个代码步骤给出完整可粘贴代码。
- 类型一致：`_chart_signals` 返回键（complete/skewed/missing_count/has_chong）在 Task 1 定义、Task 2 消费，一致；谓词签名 `gan_to_wuxing/zhi_to_wuxing/is_gan/is_zhi/zhi_chong` 与 [`engine/predicates/`](../../../engine/predicates/) 现有定义一致。
- 已知风险显式化：静态角色钉死测试在 Task 4 用"观察实际→改结构性断言"处理，并允许"意外仍 PASS 则跳过"。
- 边界约束显式化：Global Constraints 明确禁止读取未填充字段，堵住 R2 最易踩的空操作坑。
