# 分层准确率看板（Phase R4）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用架构 §16 指标，把一批带反馈的 DecisionRun 聚合成"按 verdict / 按层 / 按域 / 按事件类型"的分层准确率报告——让系统能回答"哪一层准确、哪一层拖后腿"，而不是用一个总准确率掩盖问题。

**Architecture:** 纯跨-run 聚合。新增 `engine/decision/accuracy_report.py`，提供 `build_accuracy_report(runs) -> AccuracyReport` 与 `render_accuracy_markdown(report) -> str`。只读 DecisionRun 已有字段（feedback_signals.verdict、feedback_attributions.affected_layer、arbitration_decisions.domain、event_hypotheses.event_type），不改任何现有层、不接真实数据管道、不持久化。

**Tech Stack:** Python 3、dataclass、pytest。纯内存聚合，无外部依赖。

## Global Constraints

- 事实源以 [`AGENTS.md`](../../../AGENTS.md) 为准；架构判断以 [`plans/layered-decision-system.md`](../../../plans/layered-decision-system.md) 为准（§16 指标体系）。
- **R4 只做聚合与渲染，不改 L0-L9 任何层、不接真实反馈数据、不写文件持久化。** 真实数据接入依赖真实反馈样本，属数据工程，不是本次代码重构。
- 只读 DecisionRun 现有字段，不新增 DecisionRun 字段、不新增第三套模型。
- 报告只统计**可计算**的指标：verdict 分布、按层 miss 分布、按域命中率、按事件类型命中率。**不臆造**架构 §16 里当前数据支撑不了的指标（如 L5 timing distance 需要真实发生时间，本阶段不做，显式标注延后）。
- 每个任务结束跑绿相关测试；Windows cmd.exe：命令用 `&&` 串联，不用 `sed`/`grep`/`cat`；提交信息用中文。

## 背景事实（执行前必读，已实测确认）

1. 已实测可达：`feedback_signal.report_item_id → ReportViewItem.decision_id → ArbitrationDecision.domain`；`decision.competing_event_ids → EventHypothesis.event_type`；`feedback_attributions[*].affected_layer`；`feedback_signals[*].verdict`。
2. verdict 取值：`hit / miss / partial / unknown / skipped`（见 [`models.py`](../../../engine/decision/models.py:17)）。
3. 默认 run 的 verdict 全是 `unknown`——所以报告在"未回填反馈"时命中率分母应排除 unknown/skipped，避免把"没反馈"误算成"没命中"。
4. 已实测聚合原型：注入 miss + hit 后，按 verdict / 域 / miss 归属层聚合均正确产出。
5. [`FeedbackAttribution`](../../../engine/decision/models.py:266) 的 `affected_layer` 是 miss 的责任层来源（L0-L9）。

---

### Task 1: 定义 AccuracyReport 数据结构与聚合函数（TDD）

**Files:**
- Create: `engine/decision/accuracy_report.py`
- Test: `tests/test_accuracy_report.py`（新建）

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class AccuracyReport` 字段：
    - `total_feedback: int`
    - `verdict_counts: dict[str, int]`（键为 verdict）
    - `scored: int`（hit+miss+partial，即排除 unknown/skipped）
    - `overall_hit_rate: float`（hit / scored，scored=0 时为 0.0）
    - `miss_by_layer: dict[str, int]`（affected_layer → miss 数）
    - `hit_rate_by_domain: dict[str, float]`
    - `hit_rate_by_event_type: dict[str, float]`
    - `scored_by_domain: dict[str, int]`
    - `scored_by_event_type: dict[str, int]`
  - `build_accuracy_report(runs: list[DecisionRun]) -> AccuracyReport`。

- [ ] **Step 1: 写失败测试**

新建 [`tests/test_accuracy_report.py`](../../../tests/test_accuracy_report.py)：

```python
from __future__ import annotations

import dataclasses

from engine.decision import run_decision_mvp
from engine.decision.accuracy_report import AccuracyReport, build_accuracy_report


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


def _run_with_verdicts(*verdicts: str):
    run = run_decision_mvp(WENZHEN)
    signals = list(run.feedback_signals)
    assert len(signals) >= len(verdicts), "样例反馈信号不足以注入所需 verdict"
    for i, v in enumerate(verdicts):
        notes = "流派选错 主审失验" if v == "miss" else ""
        signals[i] = dataclasses.replace(signals[i], verdict=v, notes=notes)
    return dataclasses.replace(run, feedback_signals=signals)


def test_report_counts_verdicts_and_excludes_unknown_from_scored() -> None:
    run = _run_with_verdicts("hit", "miss")

    report = build_accuracy_report([run])

    assert isinstance(report, AccuracyReport)
    assert report.verdict_counts.get("hit", 0) >= 1
    assert report.verdict_counts.get("miss", 0) >= 1
    # scored 只含 hit/miss/partial，不含 unknown
    assert report.scored == report.verdict_counts.get("hit", 0) + report.verdict_counts.get("miss", 0) + report.verdict_counts.get("partial", 0)
    assert 0.0 <= report.overall_hit_rate <= 1.0


def test_report_attributes_miss_to_layer() -> None:
    run = _run_with_verdicts("miss")

    report = build_accuracy_report([run])

    assert sum(report.miss_by_layer.values()) >= 1


def test_report_empty_runs_is_safe() -> None:
    report = build_accuracy_report([])

    assert report.total_feedback == 0
    assert report.scored == 0
    assert report.overall_hit_rate == 0.0
    assert report.miss_by_layer == {}
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_accuracy_report.py -v`
Expected: FAIL，`ModuleNotFoundError: engine.decision.accuracy_report`。

- [ ] **Step 3: 实现 accuracy_report.py**

新建 [`engine/decision/accuracy_report.py`](../../../engine/decision/accuracy_report.py)：

```python
"""分层准确率看板（Phase R4）。

只读 DecisionRun 现有字段做跨 run 聚合，不改任何层、不持久化。
回答架构核心问题：哪一层准确、哪一层拖后腿。
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from engine.decision.models import DecisionRun

_SCORED = {"hit", "miss", "partial"}


@dataclass(frozen=True)
class AccuracyReport:
    total_feedback: int = 0
    verdict_counts: dict[str, int] = field(default_factory=dict)
    scored: int = 0
    overall_hit_rate: float = 0.0
    miss_by_layer: dict[str, int] = field(default_factory=dict)
    hit_rate_by_domain: dict[str, float] = field(default_factory=dict)
    hit_rate_by_event_type: dict[str, float] = field(default_factory=dict)
    scored_by_domain: dict[str, int] = field(default_factory=dict)
    scored_by_event_type: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_feedback": self.total_feedback,
            "verdict_counts": dict(self.verdict_counts),
            "scored": self.scored,
            "overall_hit_rate": self.overall_hit_rate,
            "miss_by_layer": dict(self.miss_by_layer),
            "hit_rate_by_domain": dict(self.hit_rate_by_domain),
            "hit_rate_by_event_type": dict(self.hit_rate_by_event_type),
            "scored_by_domain": dict(self.scored_by_domain),
            "scored_by_event_type": dict(self.scored_by_event_type),
        }


def _rate(hit: int, scored: int) -> float:
    return round(hit / scored, 3) if scored else 0.0


def build_accuracy_report(runs: list[DecisionRun]) -> AccuracyReport:
    verdict_counts: dict[str, int] = defaultdict(int)
    miss_by_layer: dict[str, int] = defaultdict(int)
    hit_by_domain: dict[str, int] = defaultdict(int)
    scored_by_domain: dict[str, int] = defaultdict(int)
    hit_by_event: dict[str, int] = defaultdict(int)
    scored_by_event: dict[str, int] = defaultdict(int)
    total = 0
    hit_total = 0
    scored_total = 0

    for run in runs:
        report_by_id = {r.report_item_id: r for r in run.report_items}
        decision_by_id = {d.decision_id: d for d in run.arbitration_decisions}
        event_type_by_id = {e.event_id: e.event_type for e in run.event_hypotheses}
        layer_by_feedback = {a.feedback_id: a.affected_layer for a in run.feedback_attributions}

        for signal in run.feedback_signals:
            total += 1
            verdict_counts[signal.verdict] += 1
            is_scored = signal.verdict in _SCORED
            is_hit = signal.verdict == "hit"
            if is_scored:
                scored_total += 1
                if is_hit:
                    hit_total += 1
            if signal.verdict == "miss":
                layer = layer_by_feedback.get(signal.feedback_id)
                if layer:
                    miss_by_layer[layer] += 1

            report_item = report_by_id.get(signal.report_item_id)
            decision = decision_by_id.get(report_item.decision_id) if report_item else None
            if decision and is_scored:
                scored_by_domain[decision.domain] += 1
                if is_hit:
                    hit_by_domain[decision.domain] += 1
                for event_id in decision.competing_event_ids:
                    event_type = event_type_by_id.get(event_id)
                    if event_type:
                        scored_by_event[event_type] += 1
                        if is_hit:
                            hit_by_event[event_type] += 1

    hit_rate_by_domain = {d: _rate(hit_by_domain[d], scored_by_domain[d]) for d in scored_by_domain}
    hit_rate_by_event_type = {e: _rate(hit_by_event[e], scored_by_event[e]) for e in scored_by_event}

    return AccuracyReport(
        total_feedback=total,
        verdict_counts=dict(verdict_counts),
        scored=scored_total,
        overall_hit_rate=_rate(hit_total, scored_total),
        miss_by_layer=dict(miss_by_layer),
        hit_rate_by_domain=hit_rate_by_domain,
        hit_rate_by_event_type=hit_rate_by_event_type,
        scored_by_domain=dict(scored_by_domain),
        scored_by_event_type=dict(scored_by_event),
    )
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_accuracy_report.py -v`
Expected: 3 PASS。

- [ ] **Step 5: 提交**

```bash
git add engine/decision/accuracy_report.py tests/test_accuracy_report.py && git commit -m "feat: 新增分层准确率聚合 build_accuracy_report"
```

---

### Task 2: 新增 Markdown 渲染并导出（TDD）

**Files:**
- Modify: `engine/decision/accuracy_report.py`
- Modify: `engine/decision/__init__.py`
- Test: `tests/test_accuracy_report.py`（追加）

**Interfaces:**
- Consumes: `AccuracyReport`（Task 1）。
- Produces: `render_accuracy_markdown(report: AccuracyReport) -> str`，输出含"总体命中率 / 按层 miss / 按域命中率 / 按事件类型命中率"四段的 Markdown；`engine.decision` 导出 `AccuracyReport / build_accuracy_report / render_accuracy_markdown`。

- [ ] **Step 1: 写失败测试**

在 [`tests/test_accuracy_report.py`](../../../tests/test_accuracy_report.py) 末尾追加：

```python
def test_render_markdown_contains_all_sections() -> None:
    from engine.decision.accuracy_report import render_accuracy_markdown

    run = _run_with_verdicts("hit", "miss")
    report = build_accuracy_report([run])

    md = render_accuracy_markdown(report)

    assert "# 分层准确率看板" in md
    assert "总体命中率" in md
    assert "按层 miss" in md
    assert "按域命中率" in md
    assert "按事件类型命中率" in md


def test_render_markdown_flags_no_feedback():
    from engine.decision.accuracy_report import render_accuracy_markdown

    md = render_accuracy_markdown(build_accuracy_report([]))

    assert "尚无可计分反馈" in md


def test_exports_from_decision_package():
    from engine.decision import AccuracyReport as ExportedReport
    from engine.decision import build_accuracy_report as exported_build
    from engine.decision import render_accuracy_markdown as exported_render

    assert ExportedReport is not None
    assert exported_build is not None
    assert exported_render is not None
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_accuracy_report.py::test_render_markdown_contains_all_sections tests/test_accuracy_report.py::test_exports_from_decision_package -v`
Expected: FAIL（`render_accuracy_markdown` 未定义 / 包未导出）。

- [ ] **Step 3: 实现渲染函数**

在 [`engine/decision/accuracy_report.py`](../../../engine/decision/accuracy_report.py) 末尾追加：

```python
def render_accuracy_markdown(report: AccuracyReport) -> str:
    lines: list[str] = ["# 分层准确率看板", ""]

    if report.scored == 0:
        lines.append("> 尚无可计分反馈（hit/miss/partial 为 0）；以下仅反映反馈登记情况，不代表准确率。")
        lines.append("")

    lines.append(f"- 反馈总数：{report.total_feedback}")
    lines.append(f"- 可计分数（hit/miss/partial）：{report.scored}")
    lines.append(f"- 总体命中率：{report.overall_hit_rate}")
    lines.append("")

    lines.append("## 按层 miss 分布")
    if report.miss_by_layer:
        for layer in sorted(report.miss_by_layer):
            lines.append(f"- {layer}：{report.miss_by_layer[layer]}")
    else:
        lines.append("- 无 miss 记录")
    lines.append("")

    lines.append("## 按域命中率")
    if report.hit_rate_by_domain:
        for domain in sorted(report.hit_rate_by_domain):
            lines.append(f"- {domain}：命中率 {report.hit_rate_by_domain[domain]}（计分 {report.scored_by_domain.get(domain, 0)}）")
    else:
        lines.append("- 无可计分域")
    lines.append("")

    lines.append("## 按事件类型命中率")
    if report.hit_rate_by_event_type:
        for event_type in sorted(report.hit_rate_by_event_type):
            lines.append(f"- {event_type}：命中率 {report.hit_rate_by_event_type[event_type]}（计分 {report.scored_by_event_type.get(event_type, 0)}）")
    else:
        lines.append("- 无可计分事件类型")
    lines.append("")

    return "\n".join(lines)
```

- [ ] **Step 4: 在 __init__.py 导出**

在 [`engine/decision/__init__.py`](../../../engine/decision/__init__.py) 的 import 区（如 `from engine.decision.orchestrator import run_decision_mvp` 附近）新增：

```python
from engine.decision.accuracy_report import AccuracyReport, build_accuracy_report, render_accuracy_markdown
```

在 `__all__` 列表中新增三行（保持字母序附近即可）：

```python
    "AccuracyReport",
    "build_accuracy_report",
    "render_accuracy_markdown",
```

- [ ] **Step 5: 运行确认通过**

Run: `python -m pytest tests/test_accuracy_report.py -v`
Expected: 全部 PASS（Task 1 三条 + Task 2 三条）。

- [ ] **Step 6: 提交**

```bash
git add engine/decision/accuracy_report.py engine/decision/__init__.py tests/test_accuracy_report.py && git commit -m "feat: 分层准确率看板 Markdown 渲染并导出"
```

---

### Task 3: 全量回归 + 文档状态更新

**Files:**
- Modify: `plans/layered-decision-system.md`

**Interfaces:**
- Produces: §18 Phase R4 标记为已完成（含边界说明）。

- [ ] **Step 1: 全量 decision 测试回归**

Run: `python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py tests/test_accuracy_report.py -q`
Expected: 全部 PASS，0 FAIL。（若 R2/R3 的测试文件已存在，一并纳入：`tests/test_l1_structural_signals.py tests/test_l9_router_calibration.py`。）

- [ ] **Step 2: 定位 Phase R4 标题**

用 search 工具在 [`plans/layered-decision-system.md`](../../../plans/layered-decision-system.md) 找 `### Phase R4：分层准确率看板`。

- [ ] **Step 3: 插入状态行**

在该标题下第一行前插入：

```markdown
> 状态：聚合与渲染已完成（build_accuracy_report + render_accuracy_markdown，按 verdict / 层 / 域 / 事件类型统计，见 tests/test_accuracy_report.py）。真实反馈样本接入与 L5 timing distance 等需真实发生时间的指标尚未实现，依赖数据而非代码重构。
```

- [ ] **Step 4: 提交**

```bash
git add plans/layered-decision-system.md && git commit -m "docs: 标记 Phase R4 分层准确率看板聚合与渲染已完成"
```

---

## 验收总清单（全部完成后执行一次）

- [ ] `python -m pytest tests/test_accuracy_report.py -q` 全绿。
- [ ] `build_accuracy_report([])` 安全返回空报告，`overall_hit_rate == 0.0`。
- [ ] scored 只含 hit/miss/partial，不含 unknown/skipped。
- [ ] miss 能归到 affected_layer；域与事件类型命中率可分别计算。
- [ ] `render_accuracy_markdown` 输出含四段（总体 / 按层 miss / 按域 / 按事件类型）。
- [ ] `engine.decision` 可导出 `AccuracyReport / build_accuracy_report / render_accuracy_markdown`。

## 证伪口径（对照架构 §16 / §19.2）

- 若报告只有总体命中率、无法按层/域/事件类型拆分，则未达成 §16"不要用一个总准确率掩盖问题"的目标，需回到 Task 1 补齐分组，而不是交付单一数字。
- R4 只证明"分层准确率可被计算与呈现"；它**不**代表系统已有真实准确率数据。当前样例数据的命中率是注入的合成 verdict，不能对外当作真实表现——真实数字依赖反馈样本回填。
- 若 unknown/skipped 被误算进分母导致命中率虚低，属实现错误，须修复（Task 1 测试已守 scored 口径）。

## Self-Review 记录

- Spec 覆盖：架构 §16 的"按层 / 按域 / 按事件类型统计、回答哪一层拖后腿"由 Task 1（聚合）+ Task 2（渲染）覆盖；§16 中依赖真实发生时间的指标（L5 timing distance、L9 calibration gain）显式标注延后，不臆造。
- Placeholder 扫描：无 TBD / "适当处理"；每个代码步骤给出完整可粘贴代码。
- 类型一致：`AccuracyReport` 字段在 Task 1 定义、Task 2 渲染消费一致；`build_accuracy_report(runs: list[DecisionRun])` 签名前后一致；只读字段（verdict/affected_layer/domain/event_type）均已实测可达。
- 已知风险显式化：unknown 不计分（Task 1 测试守护）；空输入安全（Task 1 测试守护）；不接真实数据、不持久化（Global Constraints + 证伪口径）。
- 已实测确认：字段可达性与聚合原型均以退出码 0 通过。
