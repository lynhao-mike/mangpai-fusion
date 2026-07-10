# R8 执行计划：L4 事件类型分类器（从 event_label 派生 event_type）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 L4 EventHypothesis 的 `event_type` 从硬编码占位符 `"v5_prediction"` 改为从 `event_label` 可读语义匹配出的具体事件类型枚举（升迁/换岗/破财/结婚/疾病…），匹配不到则归为按域的通用类型。

**Architecture:** L4 [`_events()`](../../../engine/decision/v5_adapter.py:114) 目前 `concrete_event=prediction.event_label` 已有可读语义（如"车祸标志组""财库发财""考试证照"），但 `event_type="v5_prediction"` 是硬编码占位。R8 新增一个 config 驱动的关键词分类器 `classify_event_type(event_label, domain)`，把可读语义映射到事件类型枚举。这是**文本语义分类**，不是从命局结构推导——后者依赖 L3 真实结构审查（仍是占位），属更后阶段。

**Tech Stack:** Python 3、pytest。纯函数 + 内置关键词表，无外部依赖、无 IO。

## Global Constraints

- 事实源以 [`AGENTS.md`](../../../AGENTS.md) 为准；方向以 [`plans/layered-decision-system.md`](../../../plans/layered-decision-system.md) §18 与 [`plans/l0-l9-refactor-geju-judgment-2026-07-10.md`](../../../plans/l0-l9-refactor-geju-judgment-2026-07-10.md) 为准。
- **只改 event_type 的来源**，不改 L4 的其余字段、不改 L3/L5/L6、不改 DecisionRun schema、不改 v5 runner。
- **诚实定位**：R8 是"从 event_label 文本分类事件类型"的过渡实现，**不是**"从命局结构推导事件"。event_type 枚举与分类规则必须在计划中显式标注为可迭代的启发式，不是命理终态。
- 分类不确定时**回退到按域通用类型**（如"事业变动/财务变动/婚恋变动/健康风险/学习节点"），绝不猜测具体事件——避免制造虚假精确。
- `validate_trace()` 必须仍返回空；`event_type` 只要非空字符串即合法（models.py 无枚举约束，分类器自己维护枚举）。
- 每个任务结束跑绿相关测试；Windows cmd.exe：命令用 `&&` 串联，不用 `sed`/`grep`/`cat`；提交信息用中文。

## 背景事实（执行前必读，已实测确认）

1. L4 [`_events()`](../../../engine/decision/v5_adapter.py:114)：`concrete_event=prediction.event_label`（141 行）已是可读语义；`event_type="v5_prediction"`（139 行）硬编码。
2. C-2026-035 五域 event_label 实测样本（含真实事件语义与规则原文混杂）：
   - 健康："…天异星在配偶宫→晚婚或多婚成定律…"
   - 事业："段建业规则参与：体的分类 — 工具（日干/比劫/印/禄/刃）"（纯规则文本，无具体事件）
   - 婚姻："天干戊土透出+地支有冲=车祸最明显标志组合…"
   - 财富："甲辰/丁丑/戊辰/辛未/壬戌 5 日为日坐财库→…冲开=发财"
   - 学业："考试、证照、培训、学历或技能升级出现可反馈节点"
3. `EventHypothesis.event_type` 无枚举约束（[`models.py`](../../../engine/decision/models.py:165)），[`validate_trace`](../../../engine/decision/models.py:414) 只要求 domain 非空、source_verdict_ids 非空，不校验 event_type 取值。
4. outcome-taxonomy-v1.yaml 是 L0-L14 程度评分轴，**不是**事件类型词表，不可直接复用为 event_type 来源。
5. R8 只动 [`v5_adapter.py`](../../../engine/decision/v5_adapter.py) 一处；R6/R7 已改的 report_view / _report_items 不受影响（它们读的是 decision.reason 与 claims，不读 event_type）。

---

### Task 1: 新增事件类型分类器纯函数（TDD）

**Files:**
- Modify: `engine/decision/v5_adapter.py`
- Test: `tests/test_l4_event_type.py`（新建）

**Interfaces:**
- Produces: `classify_event_type(event_label: str, domain: str) -> str`
  - 按关键词表匹配具体事件类型（如"车祸/疾病/婚变/破财/发财/升迁/换岗/创业/学历"）。
  - 匹配不到返回按域通用类型：事业→"事业变动"，财富→"财务变动"，婚姻→"婚恋变动"，健康→"健康风险"，学业→"学习节点"，其他→"待具体化事件"。
  - 关键词表作为模块级常量 `_EVENT_TYPE_KEYWORDS`，便于后续迭代。

- [ ] **Step 1: 写失败测试**

新建 [`tests/test_l4_event_type.py`](../../../tests/test_l4_event_type.py)：

```python
from __future__ import annotations

from engine.decision.v5_adapter import classify_event_type


def test_classifies_specific_events_from_label():
    assert classify_event_type("天干戊土透出+地支有冲=车祸最明显标志组合", "婚姻") == "车祸"
    assert classify_event_type("库有开关之分→冲开=发财", "财富") == "发财"
    assert classify_event_type("晚婚或多婚成定律", "婚姻") == "婚变"
    assert classify_event_type("考试、证照、培训、学历或技能升级出现可反馈节点", "学业") == "学历"


def test_falls_back_to_domain_generic_when_no_keyword():
    # 纯规则文本、无具体事件 → 按域通用
    assert classify_event_type("段建业规则参与：体的分类 — 工具", "事业") == "事业变动"
    assert classify_event_type("", "财富") == "财务变动"
    assert classify_event_type("无匹配文本", "婚姻") == "婚恋变动"
    assert classify_event_type("无匹配文本", "健康") == "健康风险"


def test_unknown_domain_falls_back_to_placeholder():
    assert classify_event_type("无匹配", "总体") == "待具体化事件"
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_l4_event_type.py -v`
Expected: FAIL，`ImportError: cannot import name 'classify_event_type'`。

- [ ] **Step 3: 实现分类器**

在 [`engine/decision/v5_adapter.py`](../../../engine/decision/v5_adapter.py) 的 `_events` 定义之前新增：

```python
# R8: 事件类型分类关键词表。这是从 event_label 文本分类的启发式过渡实现，
# 不是从命局结构推导事件类型（后者依赖 L3 真实结构审查，仍待建设）。
# 顺序敏感：越具体的关键词越靠前。
_EVENT_TYPE_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("车祸", ("车祸", "交通", "撞")),
    ("手术", ("手术", "开刀")),
    ("疾病", ("疾病", "病", "体检", "慢病", "伤病", "健康问题")),
    ("婚变", ("离婚", "再婚", "晚婚", "多婚", "婚变", "分手")),
    ("结婚", ("结婚", "婚姻", "配偶", "婚恋", "成家")),
    ("发财", ("发财", "暴富", "冲开", "财库")),
    ("破财", ("破财", "亏损", "负债", "支出压力", "损失")),
    ("升迁", ("升迁", "升职", "职级", "提拔")),
    ("换岗", ("换岗", "调动", "岗位", "组织关系")),
    ("创业", ("创业", "自主", "合伙", "开业")),
    ("学历", ("学历", "考试", "证照", "培训", "技能升级", "学位")),
]

_DOMAIN_GENERIC_EVENT: dict[str, str] = {
    "事业": "事业变动",
    "财富": "财务变动",
    "婚姻": "婚恋变动",
    "健康": "健康风险",
    "学业": "学习节点",
}


def classify_event_type(event_label: str, domain: str) -> str:
    """从 event_label 可读语义分类事件类型；匹配不到回退按域通用类型。

    R8 过渡实现：文本关键词匹配，不是从命局结构推导。
    """

    text = event_label or ""
    for event_type, keywords in _EVENT_TYPE_KEYWORDS:
        if any(kw in text for kw in keywords):
            return event_type
    return _DOMAIN_GENERIC_EVENT.get(domain, "待具体化事件")
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_l4_event_type.py -v`
Expected: 全部 PASS。

> 若某条断言因关键词顺序未命中（如"婚姻"文本同时含"婚姻"与"晚婚"，应先命中"婚变"），调整 `_EVENT_TYPE_KEYWORDS` 顺序使更具体的类型靠前，直到测试全绿。不要放宽测试。

- [ ] **Step 5: 提交**

```bash
git add engine/decision/v5_adapter.py tests/test_l4_event_type.py && git commit -m "feat: 新增 L4 事件类型分类器 classify_event_type（文本启发式过渡实现）"
```

---

### Task 2: _events 使用分类器替换硬编码 event_type（TDD）

**Files:**
- Modify: `engine/decision/v5_adapter.py`（`_events` 第 139 行）
- Test: `tests/test_l4_event_type.py`（追加）

**Interfaces:**
- Consumes: `classify_event_type`（Task 1）。
- Produces: `_events` 产出的 EventHypothesis，`event_type` 来自 `classify_event_type(prediction.event_label, prediction.domain)`，不再是 `"v5_prediction"`。

- [ ] **Step 1: 写失败测试（端到端）**

在 [`tests/test_l4_event_type.py`](../../../tests/test_l4_event_type.py) 末尾追加：

```python
def test_events_no_longer_use_placeholder_event_type():
    from engine.decision import run_decision_mvp
    from engine.v5 import run_v5
    from engine.decision import decision_run_from_v5

    output = run_v5({"case_id": "C-TEST-R8", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})
    run = decision_run_from_v5(output)

    event_types = {e.event_type for e in run.event_hypotheses}
    assert "v5_prediction" not in event_types, "event_type 不应再是占位符"
    assert event_types, "应有事件"
    # 至少能落到已知枚举或按域通用类型
    allowed = {"车祸","手术","疾病","婚变","结婚","发财","破财","升迁","换岗","创业","学历",
               "事业变动","财务变动","婚恋变动","健康风险","学习节点","待具体化事件"}
    assert event_types <= allowed, f"出现未定义的 event_type: {event_types - allowed}"
    assert run.validate_trace() == []
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_l4_event_type.py::test_events_no_longer_use_placeholder_event_type -v`
Expected: FAIL（当前 event_type 仍为 "v5_prediction"）。

- [ ] **Step 3: 替换硬编码**

在 [`engine/decision/v5_adapter.py`](../../../engine/decision/v5_adapter.py:139) 把：

```python
                event_type="v5_prediction",
```

替换为：

```python
                event_type=classify_event_type(prediction.event_label, prediction.domain),
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_l4_event_type.py -v`
Expected: 全部 PASS。

- [ ] **Step 5: decision 回归**

Run: `python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q`
Expected: 全绿。若 `test_decision_v5_adapter.py` 有断言 `event_type == "v5_prediction"`，用 search 确认后改为断言"非 v5_prediction 且在 allowed 集合内"——这是预期内的断言更新，不是放宽。

- [ ] **Step 6: 提交**

```bash
git add engine/decision/v5_adapter.py tests/test_l4_event_type.py && git commit -m "feat: L4 _events 用分类器产出 event_type，移除 v5_prediction 占位符"
```

---

### Task 3: 重跑 C-2026-035 验证 + 文档状态更新

**Files:**
- Modify: `plans/layered-decision-system.md`

**Interfaces:**
- Produces: §18 记录 R8 已让 L4 event_type 具体化（文本启发式过渡）。

- [ ] **Step 1: 重跑真实 case**

Run: `python tools/render_report_v6.py cases/C-2026-035-乾-戊辰癸亥甲戌庚午/input.md --output-dir reports`
Expected: 退出码 0。

- [ ] **Step 2: 验证 event_type 已具体化**

Run:
```bash
python -c "import json,pathlib,sys; d=json.loads(pathlib.Path('reports/C-2026-035-乾-戊辰癸亥甲戌庚午-v6-preprod-content-report.decision-run.json').read_text(encoding='utf-8')); types=sorted({e['event_type'] for e in d['event_hypotheses']}); sys.stdout.buffer.write(('event_types: '+str(types)).encode('utf-8')); sys.stdout.buffer.write(b'\n'); sys.exit(0 if 'v5_prediction' not in types else 1)"
```
Expected: 退出码 0，打印出的 event_types 不含 "v5_prediction"（应出现如 车祸/发财/婚变/学历/事业变动 等）。

- [ ] **Step 3: 在 §18 R8 追加状态**

在 [`plans/layered-decision-system.md`](../../../plans/layered-decision-system.md) §18 Phase R6 段之后新增：

```markdown
### Phase R8：L4 事件类型分类（文本启发式过渡）

> 状态：已落地（L4 event_type 从占位符 v5_prediction 改为从 event_label 关键词分类，匹配不到回退按域通用类型，见 tests/test_l4_event_type.py）。**这是文本分类过渡，不是从命局结构推导事件**——真正的结构推导依赖 L3 真实审查（仍是占位），属后续阶段。分类关键词表 _EVENT_TYPE_KEYWORDS 是可迭代启发式，不是命理终态。
```

- [ ] **Step 4: 提交**

```bash
git add plans/layered-decision-system.md && git commit -m "docs: 标记 R8 L4 事件类型分类已落地（文本启发式过渡）"
```

---

## 验收总清单（全部完成后执行一次）

- [ ] `python -m pytest tests/test_l4_event_type.py tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q` 全绿。
- [ ] `classify_event_type` 能从 event_label 匹配具体事件，匹配不到回退按域通用类型。
- [ ] 重跑 C-2026-035 后，decision-run.json 的 event_type 不再含 "v5_prediction"。
- [ ] 所有 event_type 落在已定义枚举或按域通用类型内（无自由文本泄漏）。
- [ ] `validate_trace()` 仍返回空。

## 证伪口径（对照架构 §18）

- 若分类器为了提高命中率开始"猜测"具体事件（event_label 无依据却硬分到"升迁"），违反"不确定回退通用类型"原则，须回到 Task 1 收紧关键词。
- R8 **只**证明"event_type 不再是占位符、能反映 event_label 语义"，**不**代表事件类型来自命局结构推导。真正的 L4（从 L3 结构命题推导现实事件）仍未做，依赖 L3 真实审查建模。
- 若发现 event_label 本身就是错的（如婚姻域 label 写成车祸规则），分类器会忠实地把它分成"车祸"——这暴露的是上游 L2/L4 命题域归类或规则选择问题，不是分类器的错，属 L3 命局建模阶段处理。

## Self-Review 记录

- Spec 覆盖：R8 目标（event_type 从占位符改为语义分类）由 Task 1（分类器）+ Task 2（接入 _events）+ Task 3（真实 case 验证）覆盖。
- Placeholder 扫描：无 TBD；每步给完整可粘贴代码；仅 Task 2 Step 5 要求 search 确认既有断言（已标注为预期内更新）。
- 类型一致：`classify_event_type(event_label: str, domain: str) -> str` 在 Task 1 定义、Task 2 调用一致；`_EVENT_TYPE_KEYWORDS` / `_DOMAIN_GENERIC_EVENT` 常量前后一致。
- 已知风险显式化：过渡定位（Global Constraints + 证伪口径 + 文档状态三处强调"不是从结构推导"）、不确定回退通用类型（Task 1 测试 + 证伪口径）、上游 label 错误不归咎分类器（证伪口径）。
- 已实测确认：event_label 已含真实事件语义；event_type 无枚举约束、validate_trace 不校验其取值；R8 只动 v5_adapter 一处。
