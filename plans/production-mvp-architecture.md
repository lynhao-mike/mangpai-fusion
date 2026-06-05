# 生产级最小版本架构方案 · mangpai-fusion

> 目标：在不重写 D1-D4 命理核心、不引入新运行时依赖的前提下，把现有离线流水线封装为可部署、可追踪、可缓存、可演进的最小生产服务。

## 1. 架构目标

- **稳定入口**：对外提供版本化 API，内部复用现有 `preflight → pipeline → render → findings` 流水线。
- **可追踪**：每次分析都有 `analysis_id`、`case_id`、输入哈希、状态、错误、耗时和制品路径。
- **可缓存**：相同输入、相同引擎版本、相同渲染选项默认命中缓存，避免重复推理与重复落盘。
- **可横向演进**：MVP 采用同步执行 + SQLite；后续可替换为队列、PostgreSQL、对象存储与 Redis，而不改变核心用例边界。
- **遵守仓库事实源**：产品版本读取 `engine.__version__`；结构化分析继续以 `AnalysisOutput` 与 `findings/` 为事实制品。

## 2. 当前系统复用边界

现有仓库已经具备完整领域流水线：

```text
cases/<case_id>/input.md
  → tools.preflight.parse()
  → engine.application.pipeline_runner.run_pipeline_e2e()
  → engine.infrastructure.findings_repository.save_findings()
  → tools.render_report.render_from_output()
  → cases/<case_id>/findings/*.json + reports/*.md
```

生产 MVP 不直接调用 D1-D4 子引擎，而是只依赖应用层用例：

- `run_pipeline_e2e()`：唯一分析执行入口。
- `render_from_output()`：可选 Markdown 报告生成入口。
- `AnalysisOutput.to_dict()`：API 返回和数据库摘要的序列化边界。

## 3. 组件结构

新增组件如下：

```text
engine/
  application/
    production_service.py      # 生产用例编排：提交、缓存、执行、状态查询
  infrastructure/
    analysis_store.py          # SQLite 仓储：job、artifact、cache 元数据

tools/
  production_api.py            # stdlib HTTP JSON API，适合本地/内网 MVP 部署

tests/
  test_production_service.py   # MVP 服务层回归测试
```

组件职责：

| 组件 | 职责 | 禁止事项 |
|---|---|---|
| `ProductionAnalysisService` | 计算缓存键、创建 job、调用现有流水线、登记制品 | 不实现 D1-D4 规则 |
| `SQLiteAnalysisStore` | 初始化 schema、事务化写入 job/artifact/cache | 不解析命理输入 |
| `tools.production_api` | HTTP 请求解析、响应编码、服务实例装配 | 不直接读写规则库 |

## 4. 数据流

### 4.1 提交分析

```text
POST /v1/analyses
  → validate input_path is under workspace
  → read input.md bytes
  → compute input_sha256
  → cache_key = sha256(engine_version + schema_version + input_sha256 + render flag + template)
  → cache lookup
      ├─ hit  → create cached job/result envelope
      └─ miss → create running job
                → run_pipeline_e2e(input_path, do_render=render)
                → collect findings/report/timing artifacts
                → complete job + save cache
```

### 4.2 查询分析

```text
GET /v1/analyses/{analysis_id}
  → load job
  → load artifacts
  → return stable JSON envelope
```

### 4.3 列表查询

```text
GET /v1/analyses?status=completed&case_id=C-...&limit=50&offset=0
  → validate pagination bounds
  → query recent jobs by optional status / case filters
  → return items[] with the same stable job envelope
```

### 4.4 健康检查

```text
GET /v1/health
  → return service name, version, db path, status
```

## 5. API 设计

### 5.1 `POST /v1/analyses`

请求：

```json
{
  "input_path": "cases/C-2026-016-坤-甲子丙子丙戌戊子/input.md",
  "render": true,
  "force": false,
  "template_name": "report-v1.3.md",
  "cases_dir": "cases",
  "reports_dir": "reports"
}
```

响应：

```json
{
  "analysis_id": "AN-20260530-...",
  "status": "completed",
  "case_id": "C-2026-016-坤-甲子丙子丙戌戊子",
  "cache_hit": false,
  "input_sha256": "...",
  "cache_key": "...",
  "started_at": "2026-05-30T14:00:00Z",
  "completed_at": "2026-05-30T14:00:03Z",
  "artifacts": [
    {"kind": "analysis_output", "path": "cases/.../findings/analysis_output.json"},
    {"kind": "timing", "path": "cases/.../findings/timing.json"},
    {"kind": "report", "path": "reports/...-report.md"}
  ],
  "summary": {
    "final_conclusions_count": 12,
    "overall_confidence": {"star": 4, "percent": 82}
  }
}
```

### 5.2 `GET /v1/analyses/{analysis_id}`

返回与提交响应同构；未找到返回 `404`。

### 5.3 `GET /v1/analyses`

用于生产控制台、轮询客户端与批量排障。查询参数：

| 参数 | 含义 | 默认 |
|---|---|---|
| `status` | 可选 job 状态过滤：`queued` / `running` / `completed` / `failed` | 不过滤 |
| `case_id` | 可选案例过滤 | 不过滤 |
| `limit` | 返回条数，API 层上限 200 | 50 |
| `offset` | 分页偏移 | 0 |

响应：

```json
{
  "items": [
    {
      "analysis_id": "AN-20260530-...",
      "status": "completed",
      "case_id": "C-2026-016-坤-甲子丙子丙戌戊子",
      "cache_hit": false,
      "artifacts": []
    }
  ],
  "limit": 50,
  "offset": 0
}
```

### 5.4 `GET /v1/health`

```json
{
  "service": "mangpai-fusion-production-api",
  "status": "ok",
  "engine_version": "1.3.0",
  "database": "runtime/analysis.sqlite3"
}
```

## 6. 数据库 schema

MVP 使用 SQLite，未来可迁移 PostgreSQL；字段命名保持显式、可审计。

```sql
CREATE TABLE analysis_jobs (
  analysis_id TEXT PRIMARY KEY,
  case_id TEXT,
  status TEXT NOT NULL,
  input_path TEXT NOT NULL,
  input_sha256 TEXT NOT NULL,
  cache_key TEXT NOT NULL,
  engine_version TEXT NOT NULL,
  render INTEGER NOT NULL,
  template_name TEXT NOT NULL,
  cache_hit INTEGER NOT NULL DEFAULT 0,
  error TEXT,
  summary_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  started_at TEXT,
  completed_at TEXT
);

CREATE INDEX idx_analysis_jobs_cache_key ON analysis_jobs(cache_key);
CREATE INDEX idx_analysis_jobs_case_id ON analysis_jobs(case_id);

CREATE TABLE analysis_artifacts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  analysis_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  path TEXT NOT NULL,
  sha256 TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (analysis_id) REFERENCES analysis_jobs(analysis_id)
);

CREATE TABLE analysis_cache (
  cache_key TEXT PRIMARY KEY,
  analysis_id TEXT NOT NULL,
  case_id TEXT NOT NULL,
  input_sha256 TEXT NOT NULL,
  engine_version TEXT NOT NULL,
  summary_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY (analysis_id) REFERENCES analysis_jobs(analysis_id)
);
```

## 7. 缓存策略

### 7.1 缓存键

```text
sha256(
  engine_version + findings_schema_version + pipeline_schema_version
  + input_sha256
  + render flag
  + template_name
)
```

这样当规则版本、findings schema、pipeline schema 或输入文件发生变化时，自动失效。

### 7.2 命中策略

- 默认 `force=false`：命中 `analysis_cache` 时不再运行流水线，返回 `cache_hit=true` 的新响应 envelope。
- `force=true`：跳过缓存并重跑，完成后覆盖该 `cache_key` 指向的新 `analysis_id`。
- artifact 文件仍以 `cases/` 与 `reports/` 为事实制品；数据库只保存路径、哈希与摘要。

### 7.3 后续扩展

| MVP | 可扩展形态 |
|---|---|
| SQLite `analysis_cache` | Redis + PostgreSQL |
| 本地 `cases/` / `reports/` | S3/MinIO 对象存储 |
| 同步执行 | Celery/RQ/Arq 队列 |
| 单机 API | 多副本 API + 独立 worker |

## 8. 错误处理

| 场景 | API 状态 | job 状态 | 说明 |
|---|---|---|---|
| 输入路径缺失 | 400 | 不创建 job | 请求层错误 |
| `input.md` 不存在 | 400 | 不创建 job | 文件边界错误 |
| preflight 失败 | 200/500 | failed | 返回 `analysis_id` 和错误详情 |
| D1-D4 异常 | 200/500 | failed | 保留 job 便于审计 |
| render 失败 | completed 或 failed | 取决于核心分析是否成功 | 现有 e2e 中 render 是软失败；MVP 保留错误字段 |

## 9. 最小生产部署

本地启动：

```bash
python -m tools.production_api --host 127.0.0.1 --port 8765 --db runtime/analysis.sqlite3
```

示例请求：

```bash
python - <<'PY'
import json, urllib.request
payload = {
  "input_path": "cases/C-2026-016-坤-甲子丙子丙戌戊子/input.md",
  "render": True
}
req = urllib.request.Request(
  "http://127.0.0.1:8765/v1/analyses",
  data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
  headers={"Content-Type": "application/json"},
  method="POST",
)
print(urllib.request.urlopen(req).read().decode("utf-8"))
PY
```

## 10. 生产化路线图

1. **MVP**：同步 API + 可选单进程异步队列 + SQLite + 本地 artifact 路径 + job 列表查询。
2. **vNext**：将内存队列替换为持久化 worker；API 只提交任务并轮询状态。
3. **规模化**：PostgreSQL 存 job，Redis 存热缓存，S3/MinIO 存 artifact。
4. **治理化**：加入认证、限流、租户隔离、审计日志、指标上报。
5. **反馈闭环**：把 `feedback_ingest` 纳入生产 API，形成分析/反馈/校准完整闭环。
