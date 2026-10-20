# 执行前最后修正 · Opus 阶段 1 会破坏它自己要保留的函数

> Claude 在准备执行 Opus v6 路线图前，最后一轮核实发现：
> **Opus 的阶段 1「删零调用函数」会直接让它阶段 3 要保留的
> `build_report_v6_context` 立刻 NameError。**

---

## 一、问题：删除候选是保留函数的依赖

Opus v6 的阶段 1 说删这些「0 外部调用」函数：

```
_arbitration_by_domain
_claims_by_domain_school
_l7_school_evidence_for_domain
_l7_conflict_for_domain
_first_prediction
_prediction_window
_prediction_trigger
_prediction_probability
_prediction_confidence_state
_prediction_star
_prediction_falsifier
_prediction_feedback
```

Opus v6 的阶段 3 说要保留：

```
build_report_v6_context（150 行）← render_report.py 依赖，不能删
```

### Claude 实测：保留函数内部调用了 14 个要删的函数

`engine/v5/report_view.py:253-402`（`build_report_v6_context`）内部：

| 行号 | 调用 |
|---|---|
| 267 | `_claims_by_domain_school(output)` |
| 302 | `_l7_school_evidence_for_domain(...)` |
| 308 | `_l7_conflict_for_domain(...)` |
| 311 | `_l7_conclusion_for_domain(...)` |
| 324 | `_l7_conclusion_for_domain(...)` |
| 384 | `_prediction_window(prediction)` |
| 385 | `_prediction_trigger(prediction)` |
| 386 | `_prediction_probability(prediction)` |
| 387 | `_prediction_confidence_state(prediction)` |
| 388 | `_prediction_star(prediction)` |
| 389 | `_prediction_falsifier(prediction)` |
| 390 | `_prediction_feedback(prediction)` |
| 396 | `_prediction_star(prediction)` |
| 397 | `_prediction_window(prediction)` |

**执行阶段 1 后，`build_report_v6_context` 立刻 NameError。**

---

## 二、这个错误的性质

Opus 的错误模式又一次显现：**它验证了「外部调用为 0」，但没验证「内部依赖关系」。**

「0 外部调用」不等于「可以删」。这 12 个函数是 `build_report_v6_context` 的私有辅助层，
只要那个函数还在，它们就都在用。

---

## 三、Claude 的修正：重新划定可删边界

### 真正可以安全删除的（无任何调用者，内部外部都没有）

逐个核实 `report_view.py` 和 `preprod.py`：

| 函数 | 外部调用 | 被保留函数调用 | 可删？ |
|---|---|---|---|
| `_extract_yaml_front_matter` | 0 | 需查 | 待确认 |
| `_report_relative_path` | 0 | 需查 | 待确认 |

### 不可删的（被 `build_report_v6_context` 依赖）

```
_claims_by_domain_school
_l7_school_evidence_for_domain
_l7_conflict_for_domain
_l7_conclusion_for_domain
_first_prediction
_prediction_window / trigger / probability / confidence_state / star / falsifier / feedback
_arbitration_by_domain（需再查调用者）
```

**结论：Opus v6 的「阶段 1 删 -150 行」基本不可执行。**

真正能删的只有极少数，可能只有 `_report_relative_path` 和 `_extract_yaml_front_matter`（待确认）。

---

## 四、这让整个方案要进一步收缩

Opus v6 的五个阶段：

| 阶段 | 内容 | 可执行性 |
|---|---|---|
| 1 | 删 0 调用函数（-150 行） | ❌ **会破坏保留函数** |
| 2 | 断点 4 域重分类（+20 行） | ✅ 可执行 |
| 3 | 修 22 处桩文本（~22 行） | ✅ 可执行 |
| 4 | CLI picture 子命令（+30 行） | ✅ 可执行 |
| 5 | 删仅测试调用的报告函数（-100 行） | ⚠️ 需逐个核实内部依赖 |

**只有阶段 2、3、4 现在可以确定执行。**

---

## 五、Claude 的最终判断：方案已经收敛到「最小可行」

回顾这五轮：

```
Opus v1: 砍 v5 报告生成，-800 行
Opus v2: 删 build_chart_from_input，测试改 CLI        → 断链
Opus v3: 保留 build_chart_from_input，-430 行
Opus v4: v5 终稿 -2657 行（render_report 零调用）      → 引爆生产链
Opus v5: 承认 render_report 是活代码，-250 行
Opus v6: 分层方案，但阶段 1 会破坏保留函数            → 本轮发现
```

**每轮都在发现新问题，每轮都在收缩。** 这不是失败，这是**逐步逼近真实边界**的过程。

但现在已经到达一个临界点：**继续在纸面上推演，边际收益已经很低。**

真正高杠杆的下一步是：**执行那三个确定可做的阶段（2/3/4），用实测结果代替推演。**

---

## 六、Claude 建议立即执行的三件事

```
阶段 2：断点 4 域重分类（+20 行）
  · runner.py:52-69 BLIND_TOPIC_DOMAINS
  · lifa/dayun 从「事业」改为「总体」
  · 这是 Opus 认定的「唯一必修」，且 Agent 走 CLI 路线时直接受益

阶段 3：修复 22 处桩文本为诚实声明（~22 行字符串替换）
  · report_view.py:288-353
  · 从「MVP 阶段待细化」改为「待补充（原因）」
  · 符合第一性原则：诚实声明缺失 > 冒充结论

阶段 4：CLI 增加 picture 子命令（+30 行）
  · engine/cli.py 新增 picture 子命令
  · 补全 Agent 的事实底座（当前缺杨派画面）
```

**三者都低风险、可独立验证、失败可回滚。**

**不再做**：阶段 1 和阶段 5 的代码删除（依赖关系复杂，收益小，风险高）。

---

## 七、给 Opus 的提示词（用户可直接复制）

```
Claude 在准备执行前最后一轮核实，发现你的阶段 1 不可执行：

你说删这 12 个「0 外部调用」函数：
  _claims_by_domain_school / _l7_school_evidence_for_domain /
  _l7_conflict_for_domain / _l7_conclusion_for_domain /
  _first_prediction / _prediction_window/trigger/probability/
  confidence_state/star/falsifier/feedback

但 Claude 实测，你要保留的 build_report_v6_context（253-402 行）
内部调用了其中 14 个：
  267 行 _claims_by_domain_school
  302 行 _l7_school_evidence_for_domain
  308 行 _l7_conflict_for_domain
  311/324 行 _l7_conclusion_for_domain
  384-397 行 _prediction_* 系列

「0 外部调用」不等于「可以删」——它们是 build_report_v6_context 的私有辅助层。

所以你的阶段 1（-150 行）基本不可执行。

Claude 的建议：五轮推演已经收敛到极限，继续在纸面上推演边际收益很低。
直接执行那三个确定可做的阶段：
  阶段 2：断点 4 域重分类（+20 行）
  阶段 3：修 22 处桩文本为诚实声明（~22 行）
  阶段 4：CLI picture 子命令（+30 行）

不再做阶段 1 和阶段 5 的代码删除。

你同意吗？如果同意，Claude 现在开始执行阶段 2。
```
