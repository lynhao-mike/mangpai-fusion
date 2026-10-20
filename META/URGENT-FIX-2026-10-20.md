# 紧急修正 · `render_report.py` 不是零调用，删除会引爆生产链

> Claude 在终稿交 Gemini 审核前，最后一轮核实发现了 Opus 的第四个错误，
> 且这是四个错误中最危险的一个——它会引爆一整片生产链。

---

## 一、Opus 的论断 vs Claude 的实测

Opus 第四轮说：

> **实测结果**：`tools/render_report.py` **零外部调用**（grep 未发现 import）

### Claude 实测

```bash
grep -rn "render_report" --include="*.py" tools/ engine/ tests/ | grep -iE "^.*(import|from)"
```

**实际调用方（至少 10 处）**：

| 调用方 | 性质 | 位置 |
|---|---|---|
| `tools/as_of_integration.py` | **生产工具** | `:35 from tools.render_report import render_from_output` |
| `tools/batch_intake.py` | **生产工具** | `:194, :204` |
| `tools/generate_wenzhen_fixed_reports.py` | **生产工具** | `:70` |
| **`engine/application/dual_engine_adapter.py`** | **引擎层，且是推荐用法** | `:8, :18` |
| `engine/application/timing.py` | 引擎层 | `:27` |
| `tests/application/test_governance_shadow_runner.py` | 测试 | — |
| `tests/application/test_staged_parallel_runner.py` | 测试 | — |
| `tests/asof/test_future_projection.py` | 测试 | — |

### 最关键的证据

`engine/application/dual_engine_adapter.py:8,18` 的 docstring：

```
新代码请使用 engine.v5.runner.run_v5 + tools.render_report.render_from_output。
"Use engine.v5.runner.run_v5 + tools.render_report.render_from_output instead."
```

**这不是死代码，这是被引擎层 docstring 明确推荐的调用路径。**

---

## 二、这个错误为什么最危险

Opus 的删除规模估计：

```
原估计：-430 行
修正后：-2657 行  ← 因为「render_report.py 零调用，直接删 2281 行」
```

**如果按这个执行，后果是**：

1. `tools/as_of_integration.py` ImportError → as-of 集成链路断
2. `tools/batch_intake.py` ImportError → 批量摄入断
3. `engine/application/dual_engine_adapter.py` 的推荐路径失效
4. `engine/application/timing.py` ImportError
5. 3 个测试文件集体失败
6. `tests/application/` 有**隔离性测试**（`test_application_import_isolation.py`），
   可能直接报「依赖违规」

**而且 `tests/asof/test_future_projection.py` 依赖它**——
`tests/asof` 是指标 A（盲断准确率）的评测套件。

---

## 三、Claude 的修正结论

### 3.1 `render_report.py` 不能删，至少现在不能

| 选项 | 可行性 |
|---|---|
| A. 删除 2281 行 | ❌ **不可行**，引爆生产链 |
| B. 改用 CLI（Opus 第一轮说的 20 行） | ❌ **不可行**，它是 400+ 行渲染器 |
| C. **保留，但标记为 deprecated** | ✅ **唯一可行** |

### 3.2 保留后的影响

Opus 的第三层删除（`build_report_v6_context` / `render_report_v6_from_output`）
**不能删**，因为 `render_report.py` 依赖它们。

**这意味着**：
- `render_report.py` 保留 → `report_view.py` 的两个函数必须保留
- 那 22 处桩文本也**暂时保留**
- 删除规模从 -2657 行回落到 **-370 行左右**

### 3.3 修正后的删除清单

| 层 | 内容 | 行数 | 状态 |
|---|---|---|---|
| 第一层 | 14 个 0 调用函数 | -150 | ✅ 可删 |
| 第二层 | 3 个仅测试调用的函数 + 删 13 个测试 | -230 | ✅ 可删 |
| `render_report.py` | — | **0** | ❌ **不能删** |
| `build_report_v6_context` | 22 处桩文本 | **0** | ❌ **暂留**（render_report 依赖） |
| `render_report_v6_from_output` | — | **0** | ❌ **暂留** |
| `render_v6_preprod_case` | preprod 报告渲染 | -80 | ⚠️ 待定（production_service no-op 后可删） |
| `render_v6_preprod_cases` | — | -20 | ⚠️ 待定 |

**净收益：约 -380 行**（不是 Opus 说的 -2657 行）

---

## 四、这个修正暴露的更深问题

### 4.1 「废弃 v5 报告生成」这个目标本身要重新评估

Opus 的战略前提是「22 处桩文本违背第一性原则，应废弃」。
但如果 `render_report.py` + `report_view.py` 是**被生产链和引擎 docstring 依赖的活代码**，
那它们不是「该废弃的死代码」，而是「有缺陷的活代码」。

**对活代码，正确做法是修桩文本，不是删链路。**

### 4.2 第一性原则的重新应用

用户的第一性原则：**证据链可追溯**。

22 处桩文本的问题不是「它是报告渲染」，而是「它用硬编码字符串冒充分析结论」。

```
❌ 体结构资源: "由五派结构裁判汇总，MVP 阶段待细化。"   ← 冒充结论
✅ 体结构资源: "待补充（引擎未产出该域的结构裁决）"      ← 诚实声明缺失
```

**修正方向可能是「把桩文本改成诚实的缺失声明」，而不是「删掉整个渲染器」。**

### 4.3 需要用户决策的新问题

| 问题 | 选项 |
|---|---|
| v5 报告生成废弃，还是修复？ | A 废弃（但发现删不掉，规模从 -2657 降到 -380）<br>B 修复桩文本为诚实声明（改动小，保留能力）<br>C 分层：核心渲染保留，桩文本字段修复 |

**Claude 倾向 C**：
- 保留渲染能力（生产链需要）
- 把 22 处「冒充结论」的桩文本改成「诚实声明缺失」
- 这既符合第一性原则，又不破坏生产链

---

## 五、给 Opus 的提示词（用户可直接复制）

```
Claude 最后一轮核实发现你第四个错误，也是最危险的一个：

你说 render_report.py「零外部调用（grep 未发现 import）」。
Claude 实测至少 10 处调用：

- tools/as_of_integration.py:35
- tools/batch_intake.py:194, 204
- tools/generate_wenzhen_fixed_reports.py:70
- engine/application/dual_engine_adapter.py:8, 18   ← 这个最关键
- engine/application/timing.py:27
- tests/application/test_governance_shadow_runner.py
- tests/application/test_staged_parallel_runner.py
- tests/asof/test_future_projection.py

特别是 engine/application/dual_engine_adapter.py 的 docstring 明确写着：
「新代码请使用 engine.v5.runner.run_v5 + tools.render_report.render_from_output」

这不是死代码，是被引擎层推荐的调用路径。

后果：
1. 你的 -2657 行估计不成立，实际只能删约 -380 行
2. build_report_v6_context / render_report_v6_from_output 不能删
  （render_report.py 依赖它们），22 处桩文本暂留
3. 「废弃 v5 报告生成」这个目标要重新评估

Claude 的新判断：
既然 render_report + report_view 是活代码，那正确做法不是「删链路」，
而是「修桩文本」——把 22 处冒充结论的硬编码改成诚实的缺失声明：
  ❌ 体结构资源: "由五派结构裁判汇总，MVP 阶段待细化。"
  ✅ 体结构资源: "待补充（引擎未产出该域的结构裁决）"

这既符合第一性原则，又不破坏生产链。

请读 F:\综合盲派\mangpai-fusion\META\URGENT-FIX-2026-10-20.md，
回答第三节的新问题：废弃、修复、还是分层？
```

---

## 六、Claude 的诚实记录

今天我和 Opus 互相抓到的错误：

| # | 谁 | 错什么 | 谁抓的 |
|---|---|---|---|
| 1 | Claude | 「236 条质量高」（没查 ID 唯一性） | Gemini |
| 2 | Claude | 报告 T-108 成功没查 score | Gemini |
| 3 | Claude | `_prediction_feedback` 28 处调用（子串误匹配） | 我自己（写终稿时） |
| 4 | Opus | CLI 能喂 run_v5（5 行） | Claude |
| 5 | Opus | render_report 是薄包装（20 行） | Claude |
| 6 | Opus | render_report 零调用（删 2281 行） | Claude |

**错误 6 是最危险的**——如果没拦住，会一次性引爆 5 个生产工具 + 3 个测试文件。

**教训**：Opus 的错误模式是「方向对就推进」，我的错误模式是「数字对就推进」。
两种模式都需要独立 Review 兜底，且**删除操作的核实标准应该比新增更严**。
