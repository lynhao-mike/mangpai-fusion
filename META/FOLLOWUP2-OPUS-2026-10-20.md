# 追问 Opus · 第二轮：删除清单会引爆 52 处外部调用

> Claude 核实了 Opus 的「阶段 1 删除清单」，发现它低估了牵连面。
> Opus 自己说「需二次确认」，这就是二次确认的结果。

---

## 一、Opus 漏掉的关键依赖：`engine/application/production_service.py`

Claude 实测，`render_v6_preprod_case` 有 **16 处外部调用**，分布在：

| 调用者 | 性质 | 删除影响 |
|---|---|---|
| **`engine/application/production_service.py`** | **生产服务层** | **致命** |
| `tools/render_report_v6.py` | Opus 已识别 | 需迁移 |
| `tests/r10/test_r10_ziping_career_acceptance.py` | 度量测试 | 牵连指标 B |
| `tests/v5/test_manifest_isolation.py` | Claude 刚加的隔离回归测试 | 牵连 T-106 成果 |
| `tests/v5/test_report_reads_l7.py` | L7 接驳测试 | 牵连 L7 决策层 |

**`engine/application/production_service.py` 是 Opus 完全没提到的。**

**问题 1**：这个文件是什么？它是不是生产入口？
如果它是 `engine.cli` 或某个 CLI 命令的背后服务，删 `render_v6_preprod_case`
等于**砍掉了正在被使用的生产路径**，而不只是「废弃一段报告代码」。

请 Opus 读 `engine/application/production_service.py` 后回答：
- 它调用 `render_v6_preprod_case` 做什么？
- 它服务的上游是谁（CLI 命令？外部调用？）
- 如果删除，这条生产路径怎么重建？

---

## 二、删除候选的真实牵连面（Claude 逐个核实）

```
render_v6_preprod_case:        16 处外部调用
build_report_v6_context:       18 处外部调用
build_chart_from_input:         7 处外部调用
build_report_context_from_frozen_run: 5 处
render_report_v6_from_output:    4 处
render_v6_preprod_cases:         2 处
─────────────────────────────────────
合计                            52 处
```

### 2.1 `build_report_v6_context` 的 18 处调用

| 调用者 | 性质 |
|---|---|
| `engine/v5/__init__.py` | **包导出**——删函数会破坏 import |
| `tools/render_report.py` | Opus 已识别 |
| `tests/r10/test_r10_ziping_career_acceptance.py` | 度量测试 |
| `tests/test_archive_links.py` | 归档链接测试 |
| `tests/v5/test_report_reads_l7.py` | L7 测试 |
| ...（共 18 处） |

**特别注意 `engine/v5/__init__.py`**：如果它 export 了这些函数，
删除就是**破坏公开 API**，不只是删内部实现。

### 2.2 `build_chart_from_input` 的 7 处调用

| 调用者 | 性质 |
|---|---|
| `tools/render_report_v6.py` | Opus 已识别 |
| `tests/r10/test_r10_ziping_career_acceptance.py` | 度量测试 |
| `tests/v5/test_render_report_v6.py` | v5 契约测试 |

**Opus 说「p-series 不依赖 build_chart_from_input，可以删」——这点我核实了，它是对的。**

**但 tests/r10 依赖它**。而 `tests/r10` 正是跑 `balanced_accuracy` 那条度量链的测试。

**问题 2**：删 `build_chart_from_input` 会让 `tests/r10` 集体失败（60 passed 里的大部分）。
指标 B 的度量链是通过 `tests/r10` 验证的。删了之后怎么验证指标 B 没退化？

---

## 三、Opus 的「保留项」判断也不成立

Opus 说这些访问器「需二次确认度量工具是否调用」。Claude 核实结果：

| 函数 | 外部调用 | Opus 的判断 | 实际 |
|---|---|---|---|
| `_arbitration_by_domain` | **0** | 保留 | ❌ 无人调用，可删 |
| `_claims_by_domain_school` | **0** | 保留 | ❌ 无人调用，可删 |
| `_l7_school_evidence_for_domain` | **0** | 保留 | ❌ 无人调用，可删 |
| `_l7_conflict_for_domain` | **0** | 保留 | ❌ 无人调用，可删 |
| `_l7_conclusion_for_domain` | **1**（仅测试） | 保留 | ⚠️ 只有测试调用 |
| `build_comparison_summary` | **2**（仅测试） | 保留 | ⚠️ 只有测试调用 |

**结论**：Opus 的保留清单**全是过度保守**——这些函数没有任何生产调用者，
只有测试在用。真实情况是**可删的面比 Opus 估计的更大**（在报告专用代码范围内），
但**牵连的测试面也比 Opus 估计的更大**。

---

## 四、Claude 的修正判断

Opus 的方向（废弃 v5 报告生成）我认同，但它把这件事想成了**纯删除**。
实际是**一次涉及 52 处调用点的重构**，必须分三层处理：

### 第 1 层：真正可安全删除的（无生产调用者）

```
report_view.py:
  _arbitration_by_domain          0 调用  → 删
  _claims_by_domain_school        0 调用  → 删
  _l7_school_evidence_for_domain  0 调用  → 删
  _l7_conflict_for_domain         0 调用  → 删

preprod.py:
  _extract_yaml_front_matter      0 调用  → 删（Opus 说保留，实际无人用）
```

### 第 2 层：有测试调用、无生产调用的（删函数 + 删测试）

```
report_view.py:
  _l7_conclusion_for_domain       1 测试调用 → 删函数 + 删 tests/v5/test_report_reads_l7.py
  build_comparison_summary        2 测试调用 → 删函数 + 删 tests/v5/test_report_view.py 部分

report_view.py:
  build_report_context_from_frozen_run  5 测试调用 → 删函数 + 删测试
  render_report_v6_from_output          4 调用（含 engine/v5/__init__.py）→ 删 + 改 __init__
```

**注意**：这些测试删除是否可接受？`tests/v5` 130 个测试会缩到多少？
如果删得太多，说明 v5 的价值本来就在报告层——**这反而是支持 Opus 决策的证据**。

### 第 3 层：有生产调用的（必须先迁移再删）

```
render_v6_preprod_case:
  engine/application/production_service.py  ← 必须先搞清这是什么
  tools/render_report_v6.py                 ← Opus 已规划迁移

build_chart_from_input:
  tools/render_report_v6.py
  tests/r10/...                             ← 指标 B 的度量测试
```

**这一层是真正的硬骨头，Opus 完全没规划。**

---

## 五、请 Opus 回答的 5 个问题

1. **`engine/application/production_service.py` 是什么？**
   它调用 `render_v6_preprod_case` 干什么？服务的上游是谁？
   **这是最关键的问题**——它决定删除是「废弃死代码」还是「砍生产路径」。

2. **删 `build_chart_from_input` 会让 `tests/r10` 大部分失败**，
   而 `tests/r10` 是指标 B 的度量链。删了之后指标 B 怎么验证？

3. **`engine/v5/__init__.py` export 了哪些函数？**
   如果它 export 了删除候选，那是破坏公开 API，需要先改所有 import 方。

4. **是否接受 Claude 的三层划分？**
   （第 1 层直接删 / 第 2 层删函数+删测试 / 第 3 层先迁移再删）

5. **删除后 `tests/v5` 会从 130 个降到几个？**
   如果降到 < 30，说明 v5 的测试价值几乎全在报告层——
   这反过来证明「废弃报告生成」是对的，但也意味着**指标 B 的度量能力也在削弱**。
   这个矛盾怎么解？

---

## 六、Claude 的建议：先做一次「删除演练」再动手

Opus 的路线图有个风险：**阶段 1 一次删 450 行，如果爆炸，回滚成本高**。

Claude 建议加一个阶段 0.5：

```
阶段 0.5：只读摸清删除爆炸半径（不改代码）
  · 列出 52 处调用点的完整清单（Claude 已给出一半）
  · 确认 engine/application/production_service.py 的性质
  · 确认 engine/v5/__init__.py 的 export 清单
  · 估算 tests/v5 删除后的剩余数量
  · 产出：一份「删除影响报告」，标注哪些删得、哪些删不得
```

**在此之前不要动 `report_view.py` 一行代码。**

---

## 七、给 Opus 的提示词（用户可直接复制）

```
Claude 核实了你的删除清单，发现 3 个你低估/高估的点：

1. 你漏了 engine/application/production_service.py —— 它调用
   render_v6_preprod_case（16 处外部调用之一）。这可能是生产路径，不是死代码。

2. 删 build_chart_from_input 会让 tests/r10 大部分失败，而 tests/r10
   是指标 B（balanced_accuracy）的度量链。删了之后怎么验证指标 B？

3. 你的「保留项」全是过度保守：_arbitration_by_domain 等 4 个函数
   外部调用为 0，没有任何生产调用者。真实可删面更大，但牵连测试面也更大。

合计 52 处外部调用点，你规划的是「删除」，实际是「重构」。

请读 F:\综合盲派\mangpai-fusion\META\FOLLOWUP2-OPUS-2026-10-20.md，
回答第五节的 5 个问题，特别是第 1 个。

在搞清 production_service.py 的性质之前，不要动 report_view.py 一行代码。
```
