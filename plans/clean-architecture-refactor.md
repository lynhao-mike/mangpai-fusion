# Clean Architecture Refactor · Behavior-Preserving Target

> 目标：在行为不变的前提下，将现有引擎与工具入口进一步收敛为 Clean Architecture：分离关注点、提高模块化、降低 engine ↔ tools 与 use case ↔ framework 的耦合。
>
> 基线事实源：仓库入口见 [AGENTS.md](../AGENTS.md)，当前项目状态见 [META/project-state.json](../META/project-state.json)，引擎契约见 [engine/contracts/00-OVERVIEW.md](../engine/contracts/00-OVERVIEW.md)。

---

## 1. 当前观察

当前仓库已经有初步分层：

- [engine/pipeline.py](../engine/pipeline.py) 已经是兼容外观层，公开历史 API，实际实现转发到 [engine/application/pipeline_runner.py](../engine/application/pipeline_runner.py)、[engine/application/integration.py](../engine/application/integration.py)、[engine/domain/analysis.py](../engine/domain/analysis.py)、[engine/infrastructure/findings_repository.py](../engine/infrastructure/findings_repository.py)。
- [engine/domain/analysis.py](../engine/domain/analysis.py) 保存分析输出模型，但仍直接引用 D1-D4 findings 类型，属于“领域聚合模型 + schema DTO”混合。
- [engine/application/pipeline_runner.py](../engine/application/pipeline_runner.py) 负责 use case 编排，但仍延迟导入 [tools/preflight.py](../tools/preflight.py)、[tools/render_report.py](../tools/render_report.py)、[tools/feedback_loop.py](../tools/feedback_loop.py)，形成 engine → tools 反向依赖。
- [engine/application/production_service.py](../engine/application/production_service.py) 同时承担请求规范化、缓存键、job 生命周期、artifact 采集、store 调用，应用服务偏胖。
- [tools/render_report.py](../tools/render_report.py) 直接消费多个 engine 类型并承担渲染、归档、statement index 等职责，是报告输出侧的高耦合入口。

---

## 2. Clean Architecture 目标边界

依赖方向固定为：

```text
interfaces / tools / api
        ↓
infrastructure adapters
        ↓
application use cases
        ↓
domain core
```

硬性约束：

1. domain 不依赖 application、infrastructure、tools。
2. application 只依赖 domain 与抽象 port，不直接导入 tools 或具体文件系统实现。
3. infrastructure 实现 application 定义的 port。
4. tools / API 仅作为 interface adapters，组装依赖并调用 use case。
5. [engine/pipeline.py](../engine/pipeline.py) 保持兼容外观层，避免外部导入路径破坏。
6. 行为不变：findings schema、report 输出、feedback ingest、生产 API 响应 envelope 在迁移阶段不改变。

---

## 3. 新 folder structure

建议目标结构如下：

```text
engine/
  __init__.py
  pipeline.py                         # compatibility facade only

  domain/
    __init__.py
    models/
      analysis.py                     # AnalysisOutput / FinalConclusion / Conflict
      confidence.py                   # Confidence policy/value helpers
      ids.py                          # statement/rule/case id primitives
      social_clock.py                 # domain policy, no IO
    bazi/
      types.py                        # Bazi / GanZhi / Dayun domain value objects
      predicates/                     # pure predicates, currently engine/predicates
    rules/
      lifecycle.py                    # Rule lifecycle domain model only
      evidence.py                     # Evidence, trace chain, school ownership

  application/
    __init__.py
    ports/
      input_parser.py                 # InputParser port
      findings_writer.py              # FindingsRepository port
      report_renderer.py              # ReportRenderer port
      feedback_ingestor.py            # FeedbackIngestor port
      clock.py                        # Clock port
      job_store.py                    # AnalysisJobStore port
    use_cases/
      run_analysis.py                 # parsed input → AnalysisOutput
      run_analysis_e2e.py             # input path → output + timing via ports
      render_analysis_report.py       # output → rendered report via port
      submit_analysis_job.py          # production submit orchestration
      ingest_feedback.py              # feedback use case facade
    services/
      candidate_extraction.py
      integration.py
      timing.py
      artifact_inventory.py
      cache_key.py

  modules/
    energy/                           # D1 段派 module, current engine/energy
    picture/                          # D2 杨派 module, current engine/picture
    yingqi/                           # D3 任派 module, current engine/yingqi
    pangzheng/                        # D4 高派 module, current engine/pangzheng

  infrastructure/
    repositories/
      findings_file_repository.py     # current findings_repository
      sqlite_analysis_store.py        # current analysis_store
      theory_yaml_repository.py       # theory yaml persistence
    adapters/
      preflight_input_parser.py       # wraps tools/preflight parse behavior
      markdown_report_renderer.py     # wraps report rendering behavior
      feedback_loop_ingestor.py       # wraps feedback_loop behavior
      system_clock.py
    serializers/
      analysis_json.py
      findings_json.py
    config/
      confidence_loader.py
      calibration_loader.py

interfaces/
  cli/
    preflight.py                      # thin CLI wrapper, imports application
    render_report.py                  # thin CLI wrapper
    feedback_ingest.py                # thin CLI wrapper
    batch_intake.py
    batch_review.py
  http/
    production_api.py                 # thin HTTP adapter
  viewmodels/
    report_view_model.py              # v1.4 report ViewModel
    statement_index_view_model.py

tools/
  # Backward-compatible shims during migration.
  preflight.py                        # delegates to interfaces/cli or infrastructure adapter
  render_report.py                    # delegates to interfaces/cli + renderer adapter
  feedback_ingest.py                  # delegates to application use case
  production_api.py                   # delegates to interfaces/http
```

说明：

- [engine/energy](../engine/energy)、[engine/picture](../engine/picture)、[engine/yingqi](../engine/yingqi)、[engine/pangzheng](../engine/pangzheng) 建议迁到 `engine/modules/`，保留旧包 shim 或通过 re-export 保持导入兼容。
- [engine/predicates](../engine/predicates) 本质是纯领域谓词，建议迁入 `engine/domain/bazi/predicates/`，短期保留 [engine/predicates](../engine/predicates) 兼容层。
- [tools](../tools) 不应长期承载业务逻辑；目标是 CLI facade + backward-compatible shim。

---

## 4. Architecture

### 4.1 Domain layer

职责：表达稳定业务概念和纯规则，不触碰文件、Markdown、SQLite、HTTP、CLI。

建议包含：

- 八字值对象：四柱、大运、干支、藏干、十神。
- 分析输出聚合：final conclusions、conflicts、yingqi table、confidence summary。
- 规则证据链：rule id、trace id、school、evidence。
- 置信度纯函数：star ↔ posterior、Beta 映射、降星策略。
- 社会时钟与行业路径等纯判断策略。

迁移重点：

- 将 [engine/domain/analysis.py](../engine/domain/analysis.py) 中 schema 序列化与业务聚合拆开：domain model 只表达概念，serializer 进入 infrastructure。
- 将 [engine/predicates](../engine/predicates) 归为 domain pure predicates。

### 4.2 Application layer

职责：编排 use case，定义 port，持有流程，不知道具体工具和存储。

核心 use cases：

1. `RunAnalysisUseCase`：接收 ParsedInput，调用 D1-D4 module service，返回 AnalysisOutput。
2. `RunAnalysisE2EUseCase`：通过 InputParser port 解析 input，再调用 RunAnalysis，按配置可选渲染与反馈。
3. `SubmitAnalysisJobUseCase`：生产提交：计算 cache key、创建 job、运行分析、收集 artifact、写 job 状态。
4. `RenderAnalysisReportUseCase`：把 AnalysisOutput 转为 ReportViewModel，再交给 ReportRenderer port。
5. `IngestFeedbackUseCase`：把 feedback 标注转换为 rule verdicts，经 RuleRepository port 持久化。

迁移重点：

- [engine/application/pipeline_runner.py](../engine/application/pipeline_runner.py) 当前直接导入 [tools/preflight.py](../tools/preflight.py)、[tools/render_report.py](../tools/render_report.py)、[tools/feedback_loop.py](../tools/feedback_loop.py)。应改为依赖 `InputParser`、`ReportRenderer`、`FeedbackIngestor` port。
- [engine/application/production_service.py](../engine/application/production_service.py) 应拆出 `SubmitAnalysisJobUseCase`、`CacheKeyService`、`ArtifactInventoryService`。

### 4.3 Infrastructure layer

职责：实现 port，封装外部细节。

建议适配器：

- `PreflightInputParser`：保持 [tools/preflight.py](../tools/preflight.py) 现有解析行为。
- `FileFindingsRepository`：封装 [engine/infrastructure/findings_repository.py](../engine/infrastructure/findings_repository.py) 的落盘行为。
- `MarkdownReportRenderer`：封装 [tools/render_report.py](../tools/render_report.py) 的渲染行为，后续迁移模板与 ViewModel。
- `SQLiteAnalysisStore`：从 [engine/infrastructure/analysis_store.py](../engine/infrastructure/analysis_store.py) 下沉到 repositories。
- `FeedbackLoopIngestor`：封装 [tools/feedback_loop.py](../tools/feedback_loop.py) 现有行为。

### 4.4 Interface adapters

职责：面向用户和外部系统，只做参数解析、依赖组装、响应转换。

入口包括：

- CLI：preflight、render、feedback、batch。
- HTTP：[tools/production_api.py](../tools/production_api.py) 可迁为 `interfaces/http/production_api.py`。
- Backward-compatible tools shim：迁移期间 [tools](../tools) 保持旧命令可用。

---

## 5. Dependency inversion ports

建议最小 port 集合：

```text
InputParser
  parse(input_path, cases_index_path=None) -> ParsedInput

FindingsRepository
  save(output, cases_dir=None) -> Path

ReportRenderer
  render(output, template_name, cases_dir=None, skip_findings_save=True) -> str

FeedbackIngestor
  ingest(case_id) -> FeedbackResult | None

AnalysisJobStore
  create_job(...)
  complete_job(...)
  fail_job(...)
  get_job(...)
  get_cached_job(...)
  save_cache(...)

Clock
  now_utc() -> datetime
  current_year() -> int
```

这样 [engine/application/pipeline_runner.py](../engine/application/pipeline_runner.py) 不再依赖 [tools](../tools)，[engine/application/production_service.py](../engine/application/production_service.py) 不再直接关心 SQLite 细节。

---

## 6. Behavior-preserving migration plan

### Phase 0 · Characterization tests

先冻结行为：

- 对当前 [engine/pipeline.py](../engine/pipeline.py) 公开 API 做 snapshot/round-trip 测试。
- 对 [tools/render_report.py](../tools/render_report.py) 输出做模板快照测试。
- 对 [tools/feedback_ingest.py](../tools/feedback_ingest.py) 与 [tools/feedback_loop.py](../tools/feedback_loop.py) 做 skip/hit/miss 行为测试。
- 对 [tools/production_api.py](../tools/production_api.py) response envelope 做兼容测试。

### Phase 1 · Introduce ports, no behavior change

- 新增 `engine/application/ports/`。
- 为现有实现写 adapter，但内部仍调用旧模块。
- `run_pipeline_e2e` 增加可选 dependency 参数；默认 adapter 保持旧行为。

### Phase 2 · Split application services

- 从 [engine/application/production_service.py](../engine/application/production_service.py) 提取 cache key、artifact inventory、submit use case。
- 保持 `ProductionAnalysisService.submit()` 方法签名不变，仅内部委派。

### Phase 3 · Move report boundary

- 新增 `interfaces/viewmodels/report_view_model.py`。
- [tools/render_report.py](../tools/render_report.py) 保持 CLI 与兼容函数，核心渲染迁到 infrastructure renderer。
- v1.4 默认模板切换前先完成 linter 与快照验收。

### Phase 4 · Module relocation with shims

- 将 D1-D4 包逐步迁入 `engine/modules/`。
- 旧路径 [engine/energy](../engine/energy)、[engine/picture](../engine/picture)、[engine/yingqi](../engine/yingqi)、[engine/pangzheng](../engine/pangzheng) 保留 re-export，直到全部内部导入改完。

### Phase 5 · Tools become adapters

- [tools](../tools) 中 active 入口逐步瘦身为 CLI shim。
- 业务逻辑进入 application use cases 或 infrastructure adapters。

---

## 7. Coupling reduction checklist

| 当前耦合 | 目标处理 |
|---|---|
| [engine/application/pipeline_runner.py](../engine/application/pipeline_runner.py) → [tools/preflight.py](../tools/preflight.py) | 改为 `InputParser` port |
| [engine/application/pipeline_runner.py](../engine/application/pipeline_runner.py) → [tools/render_report.py](../tools/render_report.py) | 改为 `ReportRenderer` port |
| [engine/application/pipeline_runner.py](../engine/application/pipeline_runner.py) → [tools/feedback_loop.py](../tools/feedback_loop.py) | 改为 `FeedbackIngestor` port |
| [engine/application/production_service.py](../engine/application/production_service.py) 同时管 cache/job/artifacts | 拆为 use case + domain service + repository port |
| [tools/render_report.py](../tools/render_report.py) 直接绑定 engine 多类型 | 引入 ReportViewModel，隔离模板与领域模型 |
| [engine/domain/analysis.py](../engine/domain/analysis.py) 混合 domain 与 JSON schema | serializer 下沉到 infrastructure |

---

## 8. Acceptance criteria

迁移完成后必须满足：

1. [engine/pipeline.py](../engine/pipeline.py) 的 `run_pipeline` 与 `run_pipeline_e2e` 旧导入路径仍可用。
2. [tools/README.md](../tools/README.md) 中 active 工具命令仍可执行。
3. `analysis_output.json` schema 与现有契约兼容。
4. 报告输出内容与迁移前 snapshot 一致，除非另有 v1.4 模板切换决策。
5. feedback ingest 的 hit/miss/skip 计数行为不变。
6. production API health、submit、get response envelope 不变。
7. application 层不得再出现 `from tools.` 或 `import tools.`。
8. domain 层不得导入 application、infrastructure、tools。

---

## 9. Recommended first implementation slice

第一刀建议只做“反向依赖切断”，低风险且收益最高：

1. 新增 `engine/application/ports/input_parser.py`、`report_renderer.py`、`feedback_ingestor.py`、`findings_writer.py`。
2. 新增 `engine/infrastructure/adapters/preflight_input_parser.py`、`markdown_report_renderer.py`、`feedback_loop_ingestor.py`。
3. 修改 [engine/application/pipeline_runner.py](../engine/application/pipeline_runner.py)，让 `run_pipeline_e2e` 使用 port 默认实现，而不是在 use case 内直接导入 [tools](../tools)。
4. 保持 [engine/pipeline.py](../engine/pipeline.py) 外观层不变。
5. 跑全量测试与工具 registry 检查。

这一 slice 不移动 D1-D4 包、不改 schema、不改报告模板，最符合“Behavior remains unchanged — structure is improved”。
