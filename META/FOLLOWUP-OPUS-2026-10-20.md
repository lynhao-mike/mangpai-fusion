# 追问 Opus · 关于「废弃 v5 报告生成」的边界核实

> Claude 已独立核实 Opus 的裁决方向，但发现 3 处需要 Opus 重新界定范围的事实。
> 这些事实直接影响「阶段 1 废弃 -800 行」是否可行。

---

## 一、Opus 裁决中我同意的部分

| 裁决 | Claude 核实 |
|---|---|
| CLI 已含 shensha / strength / structures / duan_zuogong | ✅ 与 Claude 早前实测一致（`engine.cli all --json` exit 0） |
| picture 缺失 | ✅ 需补 `engine.cli picture` 子命令 |
| v5 报告生成废弃（report_view + preprod） | ✅ 方向认同——22 处桩文本违背第一性原则 |
| 保留 runner.py 供 p-series 度量 | ✅ 认同——否则指标 B 断链 |
| 断点 4 必修，其余取消 | ✅ 认同——断点 1/2/3/5/6 都在 v5 报告链内 |
| 新增指标 C（证据链完整率） | ✅ 认同 |

---

## 二、3 处需要 Opus 重新界定的事实

### 事实 1：`report_view.py` 的消费者有 10 处，不止 Opus 列的那些

Claude 实测 `grep -rln "report_view"`：

```
engine/decision/orchestrator.py          ← 隐藏链：决策编排器
engine/decision/__init__.py
engine/v5/domain_analysis_report.py      ← 域分析报告
engine/v5/domain_report_view.py
engine/v5/preprod.py
engine/v5/__init__.py
tools/render_report.py                   ← 生产工具
tests/application/test_application_import_isolation.py
tests/application/test_staged_parallel_runner.py
```

**Opus 只提到 `tools/render_report.py`，没提 `engine/decision/` 这条链。**

**问题 1**：`engine/decision/orchestrator.py` 是干什么的？它 import report_view 是为了什么？
如果 `engine/decision/` 也在用 v5 的报告上下文，那废弃 report_view 会牵连决策编排器——
**而决策编排器可能是「Agent 做最终裁决」的入口**，这个不能废。

请 Opus 读 `engine/decision/orchestrator.py` 后回答：
- 它是否必须依赖 `report_view`？
- 如果 report_view 废弃，`engine/decision/` 怎么改？

---

### 事实 2：8 个生产工具里，只有 2 个真正依赖报告生成

Claude 逐个核实 8 个工具的 import：

| 工具 | 实际依赖 | 是否依赖报告生成 |
|---|---|---|
| `domain_analysis_cli.py` | `engine.v5.domain` + `domain_analysis_report` + `domain_metadata_integrity` | **间接**（domain_analysis_report） |
| `domain_capability_status.py` | `engine.v5.domain` + `domain_capability_metrics` | ❌ 否 |
| `domain_feedback.py` | `engine.v5.domain` + `domain_feedback` | ❌ 否 |
| `domain_prospective_cohort.py` | `engine.v5.domain` | ❌ 否 |
| `feedback_ingest.py` | `engine.v5.domain` | ❌ 否 |
| `p_series_career_blind_harness.py` | `engine.v5.duan_runner._duan_structure` | ❌ 否（依赖 runner，不是 report_view） |
| `render_report.py` | `engine.v5.domain` + **`report_view`** | ✅ **是** |
| `render_report_v6.py` | **`engine.v5.preprod`** | ✅ **是** |

**结论**：Opus 说「迁移 8 个生产工具到 CLI 路线（+150 行）」**范围夸大了**。
真正需要迁移的只有 2 个（`render_report` 和 `render_report_v6`），
其余 6 个依赖的是 `engine/v5/domain.py`（数据结构）和 `runner.py`（度量），**不需要迁移**。

**问题 2**：Opus 是否同意把「迁移 8 个工具」缩小为「迁移 2 个工具」？
如果同意，阶段 4 从 +150 行降到约 +40 行。

---

### 事实 3：`report_view.py` 有 589 行，不是 Opus 暗示的可整体删除

```
engine/v5/report_view.py   589 行
engine/v5/preprod.py       346 行
engine/v5/runner.py       1313 行
```

Opus 说「废弃 -800 行」。但 589 + 346 = 935 行，且：

- `report_view.py` 里有 **L7 裁决接驳逻辑**（Opus 自己也提到「只有事业域接了 L7 裁决」）
- `preprod.py` 里有 **manifest 写入逻辑**（T-106 刚修过 `manifest_root` 参数）
- `preprod.py` 里有 **`build_chart_from_input`**——这是 v5 的输入解析，
  如果 p-series 度量链也要用它，就不能删

**问题 3**：请 Opus 精确列出「阶段 1 要删的函数/类清单」，
而不是给行数。Claude 需要逐行核对哪些逻辑是「报告专用」（可删）、
哪些是「度量链共用」（必须保留或搬迁）。

---

## 三、Claude 建议的修订方案（供 Opus 评估）

基于上述 3 个事实，我把 Opus 的四阶段修订为：

```
阶段 0（已完成）：P0 构建链

阶段 1：精确废弃，不是整体删除
  · 删除 report_view.py 中的 22 处桩文本相关函数
  · 删除 preprod.py 中的报告渲染路径
  · 保留 preprod.py 的 build_chart_from_input（度量链输入）
  · 保留 report_view.py 中的 L7 接驳逻辑（如果 engine/decision 需要）
  · 预期 -300 ~ -400 行（不是 -800）

阶段 2：CLI 增加 picture 子命令（+30 行）
  · engine.cli picture --pillars "..." --json
  · 调用 engine/facts/picture.py:match_picture()

阶段 3：修断点 4 域重分类（+20 行）
  · BLIND_TOPIC_DOMAINS：lifa/dayun 从「事业」剥离
  · 同时影响 tools/query_theory.py 的域检索

阶段 4：迁移 2 个工具（不是 8 个）
  · render_report.py → CLI + Agent 路线
  · render_report_v6.py → CLI + Agent 路线
  · 预期 +40 行

阶段 5（Opus 原方案没有，Claude 新增）：
  处理 engine/decision/ 对 report_view 的依赖
  · 如果 engine/decision 是「Agent 裁决入口」，它应该改成消费 CLI 输出
  · 这一步的风险最高，需要 Opus 先读代码再定
```

---

## 四、请 Opus 回答的 4 个问题

1. **`engine/decision/orchestrator.py` 是什么？** 它 import report_view 做什么？
   废弃 report_view 会不会牵连 Agent 的裁决入口？

2. **阶段 1 能否给函数级清单？** 不要行数，要「删哪些函数、留哪些函数、为什么」。

3. **阶段 4 是否同意从 8 个工具缩小为 2 个？**

4. **`build_chart_from_input` 删不删？** p-series 度量链是否需要它？
   （Claude 未验证，请 Opus 读 `tools/p_series_career_blind_harness.py` 后回答）

---

## 五、给 Opus 的提示词（用户可直接复制）

```
Claude 核实了你的四阶段方案，发现 3 处需要你重新界定范围。
请读 F:\综合盲派\mangpai-fusion\META\FOLLOWUP-OPUS-2026-10-20.md，
回答第四节的 4 个问题。

特别提醒：你自己说过「不把工具依赖等同于功能依赖」，
但「迁移 8 个生产工具」这个判断可能正犯了这个错——
Claude 实测只有 2 个真正依赖报告生成。

另外，report_view.py 有 10 处消费者，其中 engine/decision/orchestrator.py
是你没提到的隐藏链。请先读它再回答。
```
