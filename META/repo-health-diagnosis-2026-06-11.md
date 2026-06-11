# 仓库问题诊断报告 · 2026-06-11

> 范围：当前仓库整体健康检查、主链路代码诊断、生产风险根因判断与解决方案备选。
> 方法：读取项目入口文档，运行测试与运行时扫描，检查 pipeline / report / production service 关键路径。

---

## 1. 执行摘要

当前仓库不是“测试失败型故障”，而是“生产交付语义风险”：全量测试、工具索引、规则扫描均通过，但正式报告链路中的关键交付物失败可能被降级为 warning，导致生产服务有机会返回 completed，却缺少正式报告、statement_index 或完整 artifact。

核心判断：系统已经从脚本工具进入生产服务雏形，必须把“正式交付物完整性”提升为一等契约；批处理容错可以保留，但生产正式分析不应沿用 warn-only 策略。

---

## 2. 健康检查结果

| 检查项 | 命令 / 来源 | 结果 | 结论 |
|---|---|---|---|
| 全量测试 | `python -m pytest tests/ -q --tb=short --maxfail=20` | `334 passed, 1 skipped` | 单测与验收测试整体通过 |
| 项目元数据测试 | `python -m pytest tests/test_project_metadata.py -q` | `13 passed` | 版本、入口、索引类约束通过 |
| 报告模板相关测试 | `python -m pytest tests/test_report_template_contract.py tests/test_parallel_domain_output_linter.py -q` | `10 passed` | 报告模板与并行分析输出 lint 相关测试通过 |
| 工具注册校验 | `python tools/tool_registry.py --check` | `tool registry check passed` | 工具索引与实现未发现漂移 |
| 规则状态扫描 | `python tools/rule_status_scan.py --check` | `rule status scan passed` | 规则状态扫描通过 |

健康结论：当前没有显性红灯；问题集中在“测试未覆盖的生产交付完整性语义”。

---

## 3. 仓库功能定位

根据入口文档，本仓库是面向命理师实战调用的四派盲派融合八字分析系统，核心数据流为：

```text
问真八字 APP 排盘
  → templates/input-from-wenzhen.md
  → cases/C-YYYY-NNN-{乾/坤}-{干支}/input.md
  → tools/preflight.py
  → engine/pipeline.py
  → tools/render_report.py
  → reports/*.md
  → cases/*/feedback.md
  → tools/feedback_ingest.py / tools/feedback_loop.py
  → theory/*/index.yaml + META/*
```

关键代码职责：

| 模块 | 职责 | 当前观察 |
|---|---|---|
| `engine/application/pipeline_runner.py` | 编排 D1 能量、D2 画像、D3 应期、D4 旁证、整合、可选渲染、自迭代 | 主流程可用，但 render / self_iter / findings 写盘失败默认不阻断 |
| `tools/render_report.py` | 从 AnalysisOutput 渲染统一报告，写 statement_index.json，运行 output_linter | 渲染器具备护栏，但 statement_index 写入失败只 warning |
| `tools/output_linter.py` | 报告出口格式、置信度、黑名单与样式护栏 | linter 模型存在并通过相关测试 |
| `engine/application/production_service.py` | 生产 MVP 同步服务：提交、缓存、任务状态、artifact inventory | 只感知未被上游吞掉的异常；若 render 被吞，可能无法标记失败 |
| `engine/pipeline.py` | 历史兼容 facade | 正常重导出 application 层入口 |

---

## 4. 关键证据

### 4.1 正式报告是任务完成条件

文档明确要求当用户要求分析或生成报告时，必须生成统一版命理师内容报告，同时完成 reports 单报告归档与 cases 结构化归档；case 目录至少包含 input.md、feedback.md、statement_index.json。

这意味着正式报告、case 归档和 statement_index 不是附属品，而是完成定义的一部分。

### 4.2 render 失败被吞

`engine/application/pipeline_runner.py` 的端到端流程中，`do_render=True` 时 renderer 异常被捕获并记录 warning，随后继续返回 output 和 timing。

风险：生产服务调用该端到端入口时，如果 renderer 失败但异常被吞，外层服务可能继续将任务写为 completed。

### 4.3 statement_index 写入失败被吞

`tools/render_report.py` 在渲染后写入 `statement_index.json`，失败时仅 warnings.warn，不阻断报告返回。

风险：报告看似生成成功，但反馈闭环依赖的 statement_index 丢失或不完整，后续 feedback ingest 会静默降级或失败。

### 4.4 生产服务依赖异常判断失败

`engine/application/production_service.py` 的 `_run_existing_job()` 通过 try/except 判断 pipeline 是否失败；只有异常冒泡到生产服务层才会 `fail_job()`。如果 render / statement_index / artifact 缺失在内层被吞，生产层无法准确标记失败。

### 4.5 测试覆盖偏向功能成功路径

现有测试覆盖架构依赖、模板契约、parallel domain、metadata 与 v1.3/v2 合同，但未发现针对“生产模式下 renderer 抛错时任务不得 completed”的断言。

---

## 5. 可能来源分析

| 序号 | 可能来源 | 判断 | 证据 / 备注 |
|---:|---|---|---|
| 1 | 架构依赖方向破坏 | 低可能 | `tests/test_architecture_dependencies.py` 通过，application 不依赖 tools 的约束已守住 |
| 2 | 工具索引漂移 | 低可能 | `tool_registry.py --check` 通过 |
| 3 | 规则状态漂移 | 低可能 | `rule_status_scan.py --check` 通过 |
| 4 | 版本事实源不一致 | 低可能 | `META/project-state.json` 与 `engine/__init__.py` 表面一致 |
| 5 | output_linter 本身失效 | 中低可能 | linter 相关测试通过；风险更像上游吞异常，而非 linter 无效 |
| 6 | render / index / artifact 失败被吞 | 高可能 | pipeline_runner 与 render_report 均有 warn-only 路径 |
| 7 | 双引擎 / 回溯 / 并行分析旁路失败被吞 | 中可能 | 属于增强能力降级；不是第一交付物，但会影响完整分析质量 |

收敛后的根因：

1. `run_pipeline_e2e()` 没有区分批处理容错模式与生产正式交付模式。
2. `ProductionAnalysisService` 把“是否抛异常”当作成功判据，但上游若吞掉 render / index 错误，服务层无法识别交付物缺失。

---

## 6. 问题定义

### 6.1 当前不是测试失败问题

所有已运行测试和扫描均通过，因此不应把问题定位为某个具体断言失败或 import 失败。

### 6.2 当前是生产交付完整性问题

正式报告链路的核心交付物包括：

- `reports/*-content-report.md`
- `cases/*/input.md`
- `cases/*/feedback.md`
- `cases/*/statement_index.json`
- `cases/*/findings/*.json`
- `cases/*/findings/timing.json`

如果 render / linter / statement_index / artifact inventory 任一关键项失败，生产任务仍可能表现为成功，这会破坏后续反馈闭环和用户对报告生成的完成预期。

---

## 7. 方案备选

| 方案 | 做法 | 优点 | 缺点 | 适用场景 | 建议 |
|---|---|---|---|---|---|
| A. 保守补日志 | 保留现有 warn-only，只增强 logger 内容 | 改动小，兼容性最好 | 不改变成功语义；生产仍可能 completed 但缺报告 | 临时排查 | 不推荐作为最终方案 |
| B. 生产服务 artifact 后验校验 | 不改 pipeline；在 `ProductionAnalysisService` 完成前检查 report / statement_index / findings 是否存在 | 改动中等；能兜住缺交付物 | 仍保留内层吞异常；错误定位不如 strict 清晰 | 快速封堵生产假成功 | 可作为短期补丁 |
| C. 引入 error_policy | `run_pipeline_e2e(error_policy="tolerant" | "strict")`；CLI 默认 tolerant，生产服务使用 strict | 语义清晰；保留历史兼容；生产交付可严格失败 | 需要更新函数签名和测试 | 推荐主线方案 | 推荐 |
| D. 重构交付契约对象 | pipeline 返回 `AnalysisDelivery`，显式包含 output、report、statement_index、artifacts、lint_result、warnings | 长期最干净；状态表达完整 | 改动最大；调用方迁移成本高 | v1.5/v1.6 架构升级 | 中长期目标 |

---

## 8. 推荐落地路径

推荐采用“C + B”的 staged clean path。

### 阶段 1：快速封堵生产假成功

1. 在 `ProductionAnalysisService._run_existing_job()` 中，在 `complete_job()` 前检查：
   - render=True 时必须存在报告 artifact 或 `output.report_md`。
   - 必须存在 `cases/<case_id>/statement_index.json`。
   - 必须存在 `cases/<case_id>/findings/timing.json` 与 `analysis_output.json`。
2. 缺失时抛出带阶段名的异常，进入 `fail_job()`。
3. 禁止缺关键 artifact 的任务进入 cache。

### 阶段 2：引入严格错误策略

1. 给 `run_pipeline_e2e()` 增加参数：

```python
error_policy: Literal["tolerant", "strict"] = "tolerant"
```

2. `strict` 模式下：
   - render 异常直接抛出。
   - self_iter 若开启则异常直接抛出。
   - findings / timing 落盘失败直接抛出。
3. `ProductionAnalysisService` 调用：

```python
run_pipeline_e2e(..., error_policy="strict")
```

4. CLI / 历史批处理继续默认 tolerant。

### 阶段 3：补测试与日志

新增测试建议：

1. fake renderer 抛错时，生产服务任务应 failed。
2. fake statement_index 写入失败时，strict 模式应失败。
3. report artifact 缺失时，不应 `complete_job()`，不应 `save_cache()`。
4. tolerant 模式下历史行为保持不变。

日志建议：

- render 失败日志包含 `case_id`、`template_name`、`variant`、`cases_dir`、异常类型。
- production failure error 包含 `stage=render` / `stage=artifact_validation` / `stage=statement_index`。
- artifact validation 失败列出 missing artifacts。

---

## 9. 不建议做的事

1. 不要只因为测试全绿就关闭问题；这不是测试红灯型 bug。
2. 不要继续堆兼容 shim；兼容性应通过 `error_policy` 明确表达。
3. 不要在 `tools/render_report.py` 继续扩大业务决策；正式交付状态应由 application / production service 层负责。
4. 不要让缺少 `statement_index.json` 的报告进入反馈闭环。
5. 不要把生产服务 completed 和“分析骨架生成成功”混为一谈。

---

## 10. 验证路径

### 第一证明点

构造 fake renderer failure：

- 在 pipeline e2e 中 renderer 抛出 RuntimeError。
- tolerant 模式：流程返回 output，但记录 warning。
- strict 模式：异常冒泡。
- production service：任务状态为 failed，error 中包含 render 阶段。

### 第二证明点

构造 artifact missing：

- renderer 返回 report_md，但报告文件或 statement_index 缺失。
- production service 不应 complete_job，不应 save_cache。

### 第三证明点

回归测试：

- `python -m pytest tests/test_production_service.py tests/test_performance_and_ports.py -q`
- `python -m pytest tests/ -q --tb=short --maxfail=20`
- `python tools/tool_registry.py --check`
- `python tools/rule_status_scan.py --check`

---

## 11. Falsifier

若产品契约明确规定“生产 completed 仅表示 D1-D4 findings 成功，报告和 statement_index 可异步补齐”，则当前诊断需要调整。但现有入口文档和 AGENTS 规则都把统一报告、case 结构化归档、statement_index 作为正式任务完成条件，因此该 falsifier 当前不成立。

---

## 12. 结论

当前仓库功能主体健康，失败点不在显性测试，而在生产交付语义：历史脚本式 warn-only 容错被带入生产正式报告路径，可能制造“任务成功但交付物不完整”的假成功。

推荐先通过生产服务 artifact 后验校验封堵，再引入 `error_policy` 区分 tolerant 与 strict，最终把正式分析升级为显式交付契约对象。