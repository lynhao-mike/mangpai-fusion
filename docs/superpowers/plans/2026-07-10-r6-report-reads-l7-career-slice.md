# R6 第一证明物：事业域报告改读 L7 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 v6 报告的「事业」域裁决结论改为消费 L7 ReportViewItem（经 DecisionRun 派生），而不是从 V5Output 的 arbitration 直渲染；其余五域保持旧渲染（双轨期）。证明分层裁判链能真正驱动报告。

**Architecture:** 现状 [`preprod.py`](../../../engine/v5/preprod.py:242) 先从 V5Output 渲染报告、再旁路派生 DecisionRun，两条路互不消费。本计划调整为：先派生 DecisionRun，把其 `report_items` 传入报告渲染；报告渲染时，事业域裁决结论优先用 L7 事业 display_text，缺省回退旧逻辑（零回归）。

**Tech Stack:** Python 3、pytest。纯内存数据流，无外部依赖、无 IO 新增。

## Global Constraints

- 事实源以 [`AGENTS.md`](../../../AGENTS.md) 为准；方向以 [`plans/layered-decision-system.md`](../../../plans/layered-decision-system.md) §18 Phase R6 与 [`plans/l0-l9-refactor-geju-judgment-2026-07-10.md`](../../../plans/l0-l9-refactor-geju-judgment-2026-07-10.md) 为准。
- **只改「事业」一个域**。其余五域（学业/财富/婚姻/健康）保持现有渲染，不动。
- **缺省零回归**：不传 `report_items` 时，[`render_report_v6_from_output`](../../../engine/v5/report_view.py:304) 与 [`build_report_v6_context`](../../../engine/v5/report_view.py:183) 输出必须与当前逐字一致。用现有 v5 报告测试证明。
- 不改 L1-L9 任何层的逻辑，不改 [`v5_adapter.py`](../../../engine/decision/v5_adapter.py)，不改 DecisionRun 结构。
- 不修复「婚姻域 display_text 写成车祸标志」这类 L4/L6 域归类错配问题——那是独立缺口，不在本切片范围。
- 每个任务结束跑绿相关测试；Windows cmd.exe：命令用 `&&` 串联，不用 `sed`/`grep`/`cat`；提交信息用中文。

## 背景事实（执行前必读，已实测确认）

1. 报告事业域裁决占位符 key = `"事业裁决结论"`，见 [`report_view.py:173`](../../../engine/v5/report_view.py:173)：`f"{domain}裁决结论": conclusion`，`conclusion` 来自 `event_result.conclusion`（V5 arbitration）。
2. L7 [`ReportViewItem`](../../../engine/decision/models.py:239) 字段：`report_item_id / decision_id / prediction_id / display_text / confidence_display / evidence_summary / feedback_prompt`——**无 domain 字段**。
3. 域反查路径：`report_item.decision_id` → `DecisionRun.arbitration_decisions[*].decision_id` 匹配 → 该 decision 的 `.domain`（中文，如"事业"）。已实测 C-2026-035 事业域 display_text = "事业：高德臣、段建业、杨清娟参与事件落地；结构约束来自：结构裁决（245条支持）…"，有实质内容。
4. [`preprod.py`](../../../engine/v5/preprod.py:242) 当前顺序：先 `report_md = render_report_v6_from_output(output, ...)`（242 行附近），后 `decision_run = decision_run_from_snapshot(snapshot)`（279 行附近）。R6 需调序：先算 decision_run，再渲染报告。
5. DOMAINS 常量见 [`report_view.py:17`](../../../engine/v5/report_view.py:17)，域名用中文。

---

### Task 1: 新增「从 report_items 取指定域裁决文本」纯函数（TDD）

**Files:**
- Modify: `engine/v5/report_view.py`
- Test: `tests/v5/test_report_reads_l7.py`（新建）

**Interfaces:**
- Produces: `_l7_conclusion_for_domain(domain: str, report_items: list, arbitration_decisions: list) -> str | None`
  - 输入 domain（中文）、L7 report_items（dict 或对象列表）、L6 arbitration_decisions（dict 或对象列表）。
  - 逻辑：建 `decision_id → domain` 映射；找到属于该 domain 的 report_item，返回其 `display_text`；找不到返回 None。
  - 为兼容 dict 与 dataclass 两种输入，用 `_get(obj, key)` 辅助读取。

- [ ] **Step 1: 写失败测试**

新建 [`tests/v5/test_report_reads_l7.py`](../../../tests/v5/test_report_reads_l7.py)：

```python
from __future__ import annotations

from engine.v5.report_view import _l7_conclusion_for_domain


def _decisions():
    return [
        {"decision_id": "d-career", "domain": "事业"},
        {"decision_id": "d-wealth", "domain": "财富"},
    ]


def _report_items():
    return [
        {"report_item_id": "r1", "decision_id": "d-career", "display_text": "事业：分层链裁决结论。"},
        {"report_item_id": "r2", "decision_id": "d-wealth", "display_text": "财富：分层链裁决结论。"},
    ]


def test_returns_display_text_for_matching_domain():
    text = _l7_conclusion_for_domain("事业", _report_items(), _decisions())
    assert text == "事业：分层链裁决结论。"


def test_returns_none_when_domain_absent():
    text = _l7_conclusion_for_domain("健康", _report_items(), _decisions())
    assert text is None


def test_returns_none_when_report_items_empty():
    assert _l7_conclusion_for_domain("事业", [], _decisions()) is None
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/v5/test_report_reads_l7.py -v`
Expected: FAIL，`ImportError: cannot import name '_l7_conclusion_for_domain'`。

- [ ] **Step 3: 实现纯函数**

在 [`engine/v5/report_view.py`](../../../engine/v5/report_view.py) 的 `build_report_v6_context` 定义之前新增：

```python
def _get(obj: Any, key: str) -> Any:
    """兼容 dict 与 dataclass 两种形态的字段读取。"""

    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _l7_conclusion_for_domain(domain: str, report_items: list, arbitration_decisions: list) -> str | None:
    """从 L7 report_items 取指定域的裁决文本；找不到返回 None（触发缺省回退）。"""

    if not report_items:
        return None
    domain_by_decision = {
        _get(d, "decision_id"): _get(d, "domain")
        for d in (arbitration_decisions or [])
    }
    for item in report_items:
        decision_id = _get(item, "decision_id")
        if domain_by_decision.get(decision_id) == domain:
            text = _get(item, "display_text")
            if text:
                return str(text)
    return None
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/v5/test_report_reads_l7.py -v`
Expected: 3 PASS。

- [ ] **Step 5: 提交**

```bash
git add engine/v5/report_view.py tests/v5/test_report_reads_l7.py && git commit -m "feat: 新增 _l7_conclusion_for_domain 从 L7 report_items 取域裁决文本"
```

---

### Task 2: build_report_v6_context 接受可选 report_items，事业域优先用 L7（TDD）

**Files:**
- Modify: `engine/v5/report_view.py`（`build_report_v6_context` 与 `render_report_v6_from_output` 签名）
- Test: `tests/v5/test_report_reads_l7.py`（追加）

**Interfaces:**
- Consumes: `_l7_conclusion_for_domain`（Task 1）。
- Produces:
  - `build_report_v6_context(output, *, template_text, report_path="", case_dir="", feedback_path="", report_items=None, arbitration_decisions=None)`。
  - `render_report_v6_from_output(output, *, template_path=..., report_path="", case_dir="", feedback_path="", report_items=None, arbitration_decisions=None)`。
  - 当 `report_items` 提供且能取到「事业」域 L7 文本时，`context["事业裁决结论"]` 用该文本；否则保持原 `event_result.conclusion`。**仅事业域走此覆盖**。

- [ ] **Step 1: 写失败测试**

在 [`tests/v5/test_report_reads_l7.py`](../../../tests/v5/test_report_reads_l7.py) 末尾追加：

```python
def test_context_career_uses_l7_when_provided():
    from engine.v5 import run_v5
    from engine.v5.report_view import build_report_v6_context

    output = run_v5({"case_id": "C-TEST-R6", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})
    template_text = "{{ 事业裁决结论 }}|{{ 财富裁决结论 }}"

    report_items = [{"report_item_id": "r1", "decision_id": "d-c", "display_text": "事业：来自L7的裁决。"}]
    decisions = [{"decision_id": "d-c", "domain": "事业"}]

    ctx = build_report_v6_context(
        output, template_text=template_text,
        report_items=report_items, arbitration_decisions=decisions,
    )

    assert ctx["事业裁决结论"] == "事业：来自L7的裁决。"


def test_context_default_unchanged_without_report_items():
    from engine.v5 import run_v5
    from engine.v5.report_view import build_report_v6_context

    output = run_v5({"case_id": "C-TEST-R6-DEF", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})
    template_text = "{{ 事业裁决结论 }}"

    with_none = build_report_v6_context(output, template_text=template_text)
    explicit_none = build_report_v6_context(output, template_text=template_text, report_items=None)

    assert with_none["事业裁决结论"] == explicit_none["事业裁决结论"]
    # 缺省时事业裁决结论仍来自 V5 arbitration，不为空
    assert with_none["事业裁决结论"]
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/v5/test_report_reads_l7.py::test_context_career_uses_l7_when_provided -v`
Expected: FAIL（`build_report_v6_context` 尚不接受 `report_items` 关键字 → TypeError）。

- [ ] **Step 3: 改 build_report_v6_context 签名与逻辑**

在 [`build_report_v6_context`](../../../engine/v5/report_view.py:183) 的签名末尾加两个可选参数：

```python
def build_report_v6_context(
    output: V5Output,
    *,
    template_text: str,
    report_path: str = "",
    case_dir: str = "",
    feedback_path: str = "",
    report_items: list | None = None,
    arbitration_decisions: list | None = None,
) -> dict[str, str]:
```

在该函数**返回 context 之前**（即 `return {key: str(value) ...}` 那一行之前），插入事业域 L7 覆盖：

```python
    l7_career = _l7_conclusion_for_domain("事业", report_items or [], arbitration_decisions or [])
    if l7_career:
        context["事业裁决结论"] = l7_career
        context["事业共识结论"] = l7_career
```

> 注意：只覆盖「事业」。不要循环所有域。`context` 变量此时应已被各域裁决填充；若 return 行是 `return {key: str(value) for key, value in context.items()}`，把上面这段插在它前面即可。

- [ ] **Step 4: 改 render_report_v6_from_output 透传参数**

在 [`render_report_v6_from_output`](../../../engine/v5/report_view.py:304) 的签名末尾加同样两个可选参数，并透传给 `build_report_v6_context`：

```python
def render_report_v6_from_output(
    output: V5Output,
    *,
    template_path: str | Path = "templates/report-v6.md",
    report_path: str = "",
    case_dir: str = "",
    feedback_path: str = "",
    report_items: list | None = None,
    arbitration_decisions: list | None = None,
) -> str:
    template_text = Path(template_path).read_text(encoding="utf-8")
    context = build_report_v6_context(
        output,
        template_text=template_text,
        report_path=report_path,
        case_dir=case_dir,
        feedback_path=feedback_path,
        report_items=report_items,
        arbitration_decisions=arbitration_decisions,
    )
    return render_template_text(template_text, context)
```

- [ ] **Step 5: 运行确认通过**

Run: `python -m pytest tests/v5/test_report_reads_l7.py -v`
Expected: 全部 PASS（Task 1 三条 + Task 2 两条）。

- [ ] **Step 6: 零回归验证**

Run: `python -m pytest tests/v5/test_render_report_v6.py tests/v5/test_v5_contracts.py -q`
Expected: 全绿。若 FAIL，说明缺省路径被改动——检查是否误把覆盖逻辑作用到 report_items=None 的情况，不要改既有测试。

- [ ] **Step 7: 提交**

```bash
git add engine/v5/report_view.py tests/v5/test_report_reads_l7.py && git commit -m "feat: 报告事业域裁决结论可选改读 L7，缺省零回归"
```

---

### Task 3: preprod 调序——先派生 DecisionRun，再把 report_items 传给报告（TDD）

**Files:**
- Modify: `engine/v5/preprod.py`
- Test: `tests/v5/test_report_reads_l7.py`（追加端到端断言）

**Interfaces:**
- Consumes: `render_report_v6_from_output` 的新 `report_items` / `arbitration_decisions` 参数。
- Produces: preprod 渲染报告时传入 DecisionRun 的 `report_items` 与 `arbitration_decisions`，使事业域走 L7。

- [ ] **Step 1: 读 preprod 当前渲染与派生顺序**

用 search 工具确认 [`engine/v5/preprod.py`](../../../engine/v5/preprod.py) 中 `render_report_v6_from_output(` 调用行与 `decision_run_from_snapshot(` 调用行的先后。目标：`decision_run` 必须在 `render_report_v6_from_output` 之前算出。

- [ ] **Step 2: 调整顺序并传参**

在 [`engine/v5/preprod.py`](../../../engine/v5/preprod.py) 中：

1. 把 `decision_run = decision_run_from_snapshot(snapshot)` 移动到 `render_report_v6_from_output(...)` 调用**之前**。
2. 给该 `render_report_v6_from_output(...)` 调用补两个参数：

```python
    report_md = render_report_v6_from_output(
        output,
        template_path=template_path,
        report_path=...,          # 保持原有实参
        case_dir=...,             # 保持原有实参
        feedback_path=...,        # 保持原有实参
        report_items=decision_run.report_items,
        arbitration_decisions=decision_run.arbitration_decisions,
    )
```

> 保留原有位置/关键字实参不变，只在末尾补 `report_items` 与 `arbitration_decisions`。若原调用用的是位置参数，改为关键字参数以避免顺序错误。

- [ ] **Step 3: 写端到端测试**

在 [`tests/v5/test_report_reads_l7.py`](../../../tests/v5/test_report_reads_l7.py) 末尾追加：

```python
def test_preprod_career_report_matches_l7(tmp_path):
    import pathlib
    from engine.v5.preprod import render_v6_preprod_case

    input_path = "cases/C-2026-035-乾-戊辰癸亥甲戌庚午/input.md"
    report_path, _ = render_v6_preprod_case(
        input_path, output_dir=str(tmp_path), workspace_root="."
    )
    report_text = pathlib.Path(report_path).read_text(encoding="utf-8")
    decision_json = pathlib.Path(str(report_path).replace(".md", ".decision-run.json"))
    import json
    d = json.loads(decision_json.read_text(encoding="utf-8"))
    # 找事业域 L7 文本
    dom_by_dec = {x["decision_id"]: x["domain"] for x in d["arbitration_decisions"]}
    career_text = next(
        (ri["display_text"] for ri in d["report_items"] if dom_by_dec.get(ri["decision_id"]) == "事业"),
        None,
    )
    assert career_text, "事业域应有 L7 report_item"
    # 报告正文应包含该 L7 事业裁决文本
    assert career_text in report_text
```

> 注意：`render_v6_preprod_case` 的实际签名以 [`engine/v5/preprod.py`](../../../engine/v5/preprod.py) 为准；若参数名不同（如 `output_path` 而非 `output_dir`），按实际签名调整本测试调用。先用 search 确认签名再写。

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/v5/test_report_reads_l7.py -v`
Expected: 全部 PASS。

- [ ] **Step 5: 全量 v5 回归**

Run: `python -m pytest tests/v5 -q`
Expected: 全绿。

- [ ] **Step 6: 提交**

```bash
git add engine/v5/preprod.py tests/v5/test_report_reads_l7.py && git commit -m "feat: preprod 先派生 DecisionRun 并把事业域 L7 report_items 注入报告渲染"
```

---

### Task 4: 重跑 C-2026-035 验证 + 文档状态更新

**Files:**
- Modify: `plans/layered-decision-system.md`

**Interfaces:**
- Produces: §18 Phase R6 状态从"方向已定，待落地"更新为"第一证明物已落地（事业域）"。

- [ ] **Step 1: 重跑真实 case**

Run: `python tools/render_report_v6.py cases/C-2026-035-乾-戊辰癸亥甲戌庚午/input.md --output-dir reports`
Expected: 退出码 0，5 个 artifact 重新生成。

- [ ] **Step 2: 验证报告事业域文本来自 L7**

Run:
```bash
python -c "import json,pathlib,sys; d=json.loads(pathlib.Path('reports/C-2026-035-乾-戊辰癸亥甲戌庚午-v6-preprod-content-report.decision-run.json').read_text(encoding='utf-8')); dom={x['decision_id']:x['domain'] for x in d['arbitration_decisions']}; c=next((ri['display_text'] for ri in d['report_items'] if dom.get(ri['decision_id'])=='事业'),None); r=pathlib.Path('reports/C-2026-035-乾-戊辰癸亥甲戌庚午-v6-preprod-content-report.md').read_text(encoding='utf-8'); sys.exit(0 if c and c in r else 1)"
```
Expected: 退出码 0（报告正文含事业域 L7 文本）。

- [ ] **Step 3: 更新 Phase R6 状态**

在 [`plans/layered-decision-system.md`](../../../plans/layered-decision-system.md) §18 Phase R6 的 `> 状态：方向已定，待落地。` 改为：

```markdown
> 状态：第一证明物已落地（事业域报告改读 L7 ReportViewItem，缺省零回归，见 tests/v5/test_report_reads_l7.py）。其余五域仍走旧渲染（双轨期）。北极星仍是 v5 runner 下沉为 L2、报告全域读 L7、L3 接真实命局审查。
```

- [ ] **Step 4: 提交**

```bash
git add plans/layered-decision-system.md && git commit -m "docs: 标记 R6 事业域报告改读 L7 第一证明物已落地"
```

---

## 验收总清单（全部完成后执行一次）

- [ ] `python -m pytest tests/v5/test_report_reads_l7.py tests/v5/test_render_report_v6.py -q` 全绿。
- [ ] 不传 `report_items` 时报告输出与改动前逐字一致（缺省零回归）。
- [ ] 重跑 C-2026-035 后，报告正文「事业」域裁决文本与 decision-run.json 事业域 L7 display_text 一致。
- [ ] 其余五域（学业/财富/婚姻/健康/总体）未改变渲染来源。
- [ ] [`render_report_v6_from_output`](../../../engine/v5/report_view.py:304) 未新增文件 IO、未 import tools。

## 证伪口径（对照架构 §18 R6）

- 若为了让事业域读 L7，不得不改 5 域全部逻辑或改 DecisionRun 结构，说明"单域切片"不成立，需回到 R6 §Options 重议是否直接走 B。
- 若事业域 L7 文本与旧 V5 渲染文本语义矛盾（不是同一裁决的两种说法，而是结论相反），说明 V5Output 与 DecisionRun 已语义漂移，须先对齐再继续 R6。
- 本切片只证明"报告能被 L7 驱动"，**不**代表分层链已全域当家，也**不**修复 L3 无 reject / L4 event_type 占位 / 婚姻域归类错配——那些是 R6 后续与 L3 命局建模的独立工作。

## Self-Review 记录

- Spec 覆盖：R6 第一证明物"C-2026-035 事业域改读 L7、双轨期、文本一致"由 Task 1（取数函数）+ Task 2（context 覆盖）+ Task 3（preprod 调序注入）+ Task 4（真实 case 验证）覆盖。
- Placeholder 扫描：无 TBD；每个代码步骤给出完整可粘贴代码；仅 Task 3 的 `render_v6_preprod_case` 签名要求先 search 确认（已显式标注）。
- 类型一致：`_l7_conclusion_for_domain(domain, report_items, arbitration_decisions)` 与 `build_report_v6_context` / `render_report_v6_from_output` 的 `report_items` / `arbitration_decisions` 参数前后一致；`ReportViewItem` 无 domain、需经 decision 反查，已在背景事实与函数实现中体现。
- 已知风险显式化：缺省零回归（Task 2 Step 6 + 验收）、只改事业域（Global Constraints）、preprod 调序（Task 3）均已固化为步骤或约束。
- 已实测确认：L7 事业 display_text 有实质内容（245 条结构支持）；域裁决占位符 key 为"事业裁决结论"；preprod 当前顺序为先渲染后派生，需调序。
