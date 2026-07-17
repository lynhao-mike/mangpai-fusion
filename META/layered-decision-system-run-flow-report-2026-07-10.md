# 分层命理决策学习系统运行状态与流程结构报告

> 归档日期：2026-07-10  
> 定位：系统运行状态、现有流程结构与 R1-R5 分层学习链路说明。  
> 本文不是命理案例报告，不进入 `reports/`；作为系统级存档放入 `META/`。

---

## 1. 结论

现有系统**能跑起来**。

当前有两条可运行链路：

1. **正式兼容线**：`tools/render_report.py` + `tools/output_linter.py`，用于当前正式统一报告兼容。
2. **v6 / run-centric 预生产线**：`tools/render_report_v6.py`，用于后续 R1-R5 分层学习链路。

新鲜验证结果：

```text
python tools/tool_registry.py --check
→ tool registry check passed
```

```text
python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py tests/v5/test_render_report_v6.py -q
→ 91 passed, 1 warning
```

因此可以判断：工具入口可用，DecisionRun / v5_adapter / v6 报告渲染核心链路可运行。

---

## 2. 当前系统两条运行线

### 2.1 正式兼容报告线

用途：继续保持现有生产报告能力。

```text
cases/*/input.md
  ↓
tools/preflight.py
  ↓
engine/pipeline.py / application pipeline
  ↓
tools/render_report.py
  ↓
reports/*-content-report.md
  ↓
tools/output_linter.py
```

典型命令：

```bash
python -m tools.preflight cases/C-2026-001-乾-庚申戊寅壬子辛丑/input.md
python tools/render_report.py cases/C-2026-001-乾-庚申戊寅壬子辛丑/input.md
```

适用场景：

- 当前正式统一报告；
- 兼容旧反馈摄入；
- 不中断既有生产流程。

限制：

- 不是 run-centric；
- 不完整承载 R1-R5 所需的 DecisionRun / feedback attachment 学习链。

---

### 2.2 v6 / run-centric 预生产线

用途：承载分层命理决策学习系统后续主线。

入口：`tools/render_report_v6.py`

```text
cases/*/input.md
  ↓
tools/render_report_v6.py
  ↓
engine.v5.preprod
  ↓
engine.v5.runner.run_v5
  ↓
V5Output
  ↓
V5RunSnapshot
  ↓
DecisionRun
  ↓
Markdown report + JSON artifacts
```

典型命令：

```bash
python tools/render_report_v6.py cases/C-2026-001-乾-庚申戊寅壬子辛丑/input.md
```

预期产物：

```text
reports/C-...-v6-preprod-content-report.md
reports/C-...-v6-preprod-content-report.v5.json
reports/C-...-v6-preprod-content-report.run.json
reports/C-...-v6-preprod-content-report.decision-run.json
reports/C-...-v6-preprod-content-report.feedback-attachment.json
```

适用场景：

- R1-R5 分层学习；
- 追踪 L1 route_schools；
- 追踪 DecisionRun；
- 绑定 feedback attachment；
- 生成后续 R4 准确率看板与 R5 learned_prior。

---

## 3. 标准真实闭环流程

推荐用于真实学习样本。

```text
真实命盘
  ↓
整理成 cases/C-.../input.md
  ↓
跑 v6 / run-centric 分析
  ↓
生成 report + .v5.json + .run.json + .decision-run.json + .feedback-attachment.json
  ↓
命理师 / 命主反馈
  ↓
写入 cases/C-.../feedback.md
  ↓
feedback_ingest / feedback_loop
  ↓
R3：反馈回打责任流派
  ↓
R4：分层准确率看板
  ↓
R5：learned_prior 注入 route_schools
```

关键原则：

```text
必须先由系统独立分析，再给真实反馈。
```

原因：R5 学的是“系统当时怎么路由、哪派主审、哪条判断失验”。如果直接注入案例与结果，没有系统原始判断链，就不能高质量归因到 L1 / L2 / L4 / L5 / L6。

---

## 4. 输入与 case 结构

正式 case 位于：

```text
cases/C-YYYY-NNN-{乾/坤}-{四柱}/
```

至少包含：

```text
input.md
feedback.md
statement_index.json
```

新案例输入模板参考：

```text
templates/input-from-wenzhen.md
```

入口校验：

```bash
python -m tools.preflight cases/C-YYYY-NNN-乾-四柱/input.md
```

---

## 5. 反馈摄入流程

反馈文件：

```text
cases/C-.../feedback.md
```

推荐标注：

```text
[y] 命中
[n] 失验
[?] 不确定
[skip] 不计
```

单案摄入：

```bash
python -m tools.feedback_ingest C-2026-001-乾-庚申戊寅壬子辛丑
```

批量复盘：

```bash
python -m tools.batch_review
```

现有反馈主链：

```text
feedback.md
  ↓
tools/feedback_ingest.py
  ↓
tools/feedback_loop.py
  ↓
theory/*/index.yaml hits/misses/confidence_cache
  ↓
META/calibration/*.snapshot.yaml
  ↓
META/iteration-log / iteration-report
```

---

## 6. R1-R5 分层学习链路位置

当前设计目标链：

```text
input.md
  ↓
render_report_v6.py
  ↓
V5Output
  ↓
V5RunSnapshot
  ↓
DecisionRun
  ↓
L1 route_schools
  ↓
L2 SchoolClaim
  ↓
L3 StructuralVerdict
  ↓
L4 EventHypothesis
  ↓
L5 TimingProbability
  ↓
L6 ArbitrationDecision
  ↓
L7 ReportViewItem
  ↓
feedback.md
  ↓
L8 FeedbackAttribution
  ↓
L9 CalibrationAction
  ↓
R4 AccuracyReport
  ↓
R5 learned_prior
  ↓
回灌 route_schools
```

当时的切片实施计划已执行并清理；当前实现与方向追溯改用以下 as-built 事实源：

- 分层决策系统现状与阶段状态：[`plans/layered-decision-system.md`](../plans/layered-decision-system.md:1)
- 平台长期路线与 L0—L9 落地边界：[`plans/bazi-intelligence-platform-roadmap.md`](../plans/bazi-intelligence-platform-roadmap.md:1)
- L1 路由当前实现：[`engine/decision/l1_school_router.py`](../engine/decision/l1_school_router.py:1)
- L9 条件化学习当前实现：[`engine/learning/`](../engine/learning/)

---

## 7. 最短可跑验证命令

用于确认系统当前能跑：

```bash
python tools/tool_registry.py --check
```

```bash
python -m pytest tests/test_decision_mvp.py tests/test_decision_v5_adapter.py tests/v5/test_render_report_v6.py -q
```

```bash
python tools/render_report_v6.py cases/C-2026-001-乾-庚申戊寅壬子辛丑/input.md
```

前两条已验证通过：

```text
tool registry check passed
91 passed, 1 warning
```

---

## 8. 真实反馈样本口径

R5 学习样本应优先来自：

```text
真实案例 → 系统先独立分析 → 再给真实反馈
```

不推荐直接注入“案例 + 真实结果”，因为没有系统原始判断链，无法判断：

- 当时 L1 选了哪派；
- 哪条报告结论对应哪个 decision；
- 失验应归因到哪一层；
- 应下调哪个流派、哪个领域、哪个角色。

样本质量排序：

| 样本类型 | 可用性 | 建议权重 |
|---|---|---|
| 前瞻闭环样本 | 最高 | 1.0 |
| 历史回填样本 | 可用但需降权 | 0.3-0.5 |
| 直接注入案例+反馈 | 不计入 R5，有审查/测试价值 | 0 |

---

## 9. 反馈样本数量建议

有效反馈不是原始案例数，而是：

```text
school × domain × role
```

下的可计分反馈数量。

推荐门槛：

| 目标 | 每桶有效反馈 | 说明 |
|---|---:|---|
| smoke / proof | 5 | 只验证链路，不做强学习 |
| 轻量先验 | 10-15 | 可 dry-run，不建议强自动降级 |
| 稳定调参 | 20-30 | 可小范围启用 learned_prior |
| 自动降级 / 冻结 | 50+ | 样本较稳后再做强动作 |

阶段性总量建议：

```text
150 条有效反馈：R5-B dry-run 起步
300 条有效反馈：高频领域小流量 learned_prior
600 条有效反馈：较认真地做流派适用性学习
1500+ 条有效反馈：全域生产级路由学习
```

---

## 10. 总结

当前系统可运行。

- 旧正式线可继续产正式报告。
- v6 / run-centric 线已通过核心测试，可承载 R1-R5 分层学习。
- 后续真实学习必须走“系统先分析 → 再反馈”的闭环。
- 直接注入案例与反馈只能作为冷启动审查或测试 fixture，不应计入 R5 有效样本。
- R5 的真实生产学习需要足够的可计分反馈样本，推荐先从 150 条有效反馈 dry-run 起步。
