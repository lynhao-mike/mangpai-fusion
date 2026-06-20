# 格局判断 · mangpai-fusion 生产化方向

> 本文档按 geju skill 输出规范，提供高格局的系统设计方向判断。
> 生成时间：2026-06-20
> 当前版本：1.3.1
> 事实源：[`plans/production-mvp-architecture.md`](production-mvp-architecture.md)、[`engine/application/production_service.py`](../engine/application/production_service.py)

---

## Thesis（核心论断）

**这个系统真正需要扩展的维度不是 QPS，而是「按版本可复现的推理」。** 把 `cases/` 和 `reports/` 当成生产事实源、用同步 HTTP 直接驱动 D1-D4、用 SQLite 当主库——这三件事是把一个"内容寻址的推理服务"硬塞进"批处理脚本"的外壳。

正确的目标模型是：**结构化 [`AnalysisOutput`](../engine/domain/analysis.py) 是唯一规范产物，pipeline 是无状态、版本钉死的纯计算函数，Markdown 报告是派生渲染，执行默认异步。**

---

## Confidence

**中高置信度。**

确定的事实：
- 复用边界（[`run_pipeline_e2e`](../engine/application/pipeline_runner.py) / [`AnalysisOutput.to_dict`](../engine/domain/analysis.py) / [`render_from_output`](../tools/render_report.py)）已在仓库验证，是稳定的契约。
- 规则持续被反馈闭环校准（见 [`tools/feedback_ingest.py`](../tools/feedback_ingest.py)），`engine_version` 进缓存键是强需求。

不确定的前提：
- 真实并发量级未知：如果这永远是单命理师本地工具，异步队列就是过度设计。
- D1-D4 内部是否依赖 `cases/` 副作用尚未验证（见 Falsifier 部分）。

---

## The Trap（被继承的约束）

现有 [`plans/production-mvp-architecture.md`](production-mvp-architecture.md) 把三个东西当成必须保留的约束：

| 被继承的约束 | 是真约束吗 | 判定理由 |
|---|---|---|
| `cases/`、`reports/` 文件是事实源 | **否** | 这是离线脚本时代的惯性。真正的事实源是结构化 findings；文件只是当前的落盘形态，不该决定架构边界 |
| 同步执行（HTTP 连接里跑完 D1-D4） | **否** | 内部实现选择，没有任何外部契约要求同步返回 |
| SQLite 是数据库 | **半真** | MVP 够用，但被写成"数据库层"会让人误以为它是终态 |
| [`AnalysisOutput.to_dict()`](../engine/domain/analysis.py) 是序列化边界 | **是（真约束）** | 这是真实数据契约，必须保留并版本化 |

### 真正的约束

1. **数据契约**：[`AnalysisOutput`](../engine/domain/analysis.py) 结构必须稳定、可版本化、可序列化。
2. **规则版本化**：每次规则变更（通过 [`tools/feedback_ingest.py`](../tools/feedback_ingest.py) 触发）后，旧分析结果不能被污染。
3. **可复现性**：相同输入 + 相同 `engine_version` + 相同 schema 必须产出相同结果。

### 伪约束（应该删除的）

1. **文件系统依赖**：计算节点不该依赖共享磁盘上的 `cases/` 目录。
2. **同步强制**：报告生成不该阻塞"分析完成"的定义。
3. **双事实源**：DB + `cases/` 的歧义会让人不知道哪个是规范。

---

## High-格局 Direction（清晰目标模型）

### 终态架构

```text
内容寻址 + 版本钉死的推理服务

  HTTP Request(input)
    ↓
  canonical_input = normalize(input)
  content_hash = sha256(canonical_input)
  analysis_key = sha256(content_hash + engine_version + schema_version + profile)
    ↓
  [Cache Lookup] 命中 analysis_key?
    ├─ YES → 直接返回规范 AnalysisOutput（cache_hit=true）
    └─ NO  → enqueue job(analysis_id, analysis_key)
             返回 202 {analysis_id, status: "queued"}
               ↓
  [Worker] 从队列消费 analysis_id
    ├─ 拉 canonical_input（不读 cases/）
    ├─ output = run_pipeline_e2e(canonical_input)  ← 纯函数，无副作用
    ├─ ArtifactStore.put(analysis_key, output.to_dict())
    └─ MetadataStore.complete(analysis_id, analysis_key)
               ↓
  [Query] GET /v1/analyses/{id}
    └─ 返回 AnalysisOutput（规范产物）
               ↓
  [Report] GET /v1/analyses/{id}/report?template=X  ← lazy 派生
    ├─ report_key = sha256(analysis_key + template)
    └─ render_from_output(output) → 缓存 → 返回
```

### 三个关键反转

| 当前假设 | 终态真相 | 影响 |
|---|---|---|
| `cases/` 是事实源 | `AnalysisOutput` 是唯一规范产物，文件仅作导出 | 计算节点不再依赖共享磁盘，天然可水平扩展 |
| 报告是分析的一部分 | 报告是对 `AnalysisOutput` 的纯函数派生 | 报告渲染移出请求路径，可独立缓存、可重建 |
| 缓存以输入哈希为键 | 缓存以「内容 + 版本 + profile」三元组寻址 | 规则迭代自动失效，这才是这个产品的核心扩展轴 |

---

## Frame-Opening Move（开框架的手法）

使用 **Ten-Times 问题**：

> **如果要支撑 10 倍命理师并发交互，现在的设计最先断的地方是什么？**

答案：
1. **同步执行**：D1-D4 的秒级延迟压在 HTTP 连接上，连接池先崩。
2. **共享文件系统**：`cases/`/`reports/` 让你无法无脑加计算副本。
3. **SQLite 单写者**：并发写入锁住吞吐。

这三点暴露出共同病根——**计算与状态没有解耦**。

---

## Bold Takes（该删 / 合 / 拆的清单）

### 删除（Kill List）

1. **删**：请求路径里的 `do_render` 参数耦合。报告生成不该决定一次分析是否"完成"。
2. **删**：`cases/` + DB 的双事实源歧义。[`AnalysisOutput`](../engine/domain/analysis.py) 是唯一规范，文件是导出视图。
3. **删**：把 SQLite 写成"数据库层"的命名暗示。

### 合并（Merge）

- **合**：已存在的 [`engine/application/job_queue.py`](../engine/application/job_queue.py) 与 [`production_service.py`](../engine/application/production_service.py) 合并为统一的"提交→排队→执行→产物"用例，不要让同步路径和队列路径长期并存。

### 拆分（Split）

- **拆**：把 `ProductionAnalysisService` 拆成 `SubmissionService`（接单+缓存查找）和 `AnalysisWorker`（无状态执行），这是横向扩展的前提。

### 重命名（Reframe）

- **改名**：SQLite 仓储从 `AnalysisStore` 改为 `MetadataStore`，让它可被 PostgreSQL 平替而不改用例。

---

## 非妥协原则

在任何实现路径中，以下四条必须保持：

1. **[`AnalysisOutput`](../engine/domain/analysis.py) 结构化 findings 是唯一规范产物。** Markdown 报告、`cases/` 文件都是派生物。
2. **pipeline 是无状态纯计算，不得在执行中写 `cases/`。** Worker 可任意加副本。
3. **缓存键必须包含 `engine_version + schema_version`。** 规则一变即失效，保证"按版本可复现"。
4. **报告是派生物，可随时重建。** 不能因为报告生成失败就认为分析失败。

---

## Options（方案对比表）

| 方向 | 描述 | 横向扩展 | 版本隔离 | 迁移成本 | 裁决 |
|---|---|---|---|---|---|
| **Conservative path** | 保留现有同步 + SQLite + 文件事实源，只补 API 鉴权和分页 | ❌ 锁死 | ⚠️ 手动 | 低 | ❌ **不推荐**：锁死在批处理外壳，10x 必崩 |
| **Clean target** | 内容寻址 + 异步 worker + 对象存储 + Postgres/Redis，文件仅导出 | ✅ 天然 | ✅ 自动 | 高 | ⚠️ 终态正确，但一步到位风险高 |
| **Staged clean path** | 用例边界按终态切（Submission/Worker 分离、AnalysisOutput 为规范产物、缓存三元组寻址），存储层先用 SQLite+本地盘的可替换适配器 | ✅ 可渐进 | ✅ 自动 | 中 | ✅✅ **强烈推荐**：方向钉死，存储渐进迁移 |

### 推荐路径详细说明

**Staged clean path（分阶段清洁路径）**：

- **Phase 1（MVP）**：用例边界按终态设计（见 [`plans/production-system-architecture-v2.md`](production-system-architecture-v2.md)），存储用 SQLite + 本地文件，但通过 `ports.py` 抽象接口隔离。
- **Phase 2（量级确认后）**：只替换存储层实现（PostgreSQL + Redis + S3），用例层零改动。
- **Phase 3（真正高并发）**：Worker 独立部署、多副本、队列拆为独立服务。

这个路径的优势：
- 第一天就能跑（复用现有 [`run_pipeline_e2e`](../engine/application/pipeline_runner.py)）。
- 方向不妥协（计算/状态解耦、内容寻址、版本隔离）。
- 可根据真实量级按需投入（不提前过度设计）。

---

## What Not To Do（禁止清单）

| 错误做法 | 为什么错 | 正确做法 |
|---|---|---|
| 现在就上 Celery/Kafka/K8s | 在确认并发量级前是过度设计 | 先用进程内队列，量级确认后再换 Redis |
| 优化 SQLite 的索引细节 | 它是要被替换的，别在将死的层上花时间 | 把它当临时实现，优化 PostgreSQL schema |
| 保留同步与异步两条长期并存的执行路径 | 双入口增加维护成本，且会让调用方困惑 | 统一到异步（同步只是"立即消费队列"的特例） |
| 在 Worker 里写 `cases/` 目录 | 破坏无状态假设，锁死横向扩展能力 | `cases/` 导出移到独立工具（按需、离线） |
| 把报告生成放在请求路径 | 耦合渲染成功与分析完成，报告模板变化会导致缓存失效 | 报告改为 lazy 派生，独立缓存键 |

---

## First Proof Point（第一个证明点）

最小可证明物：

**把 [`run_pipeline_e2e`](../engine/application/pipeline_runner.py) 包成一个不写 `cases/` 的无状态函数**，输入 canonical input 字符串、输出 [`AnalysisOutput`](../engine/domain/analysis.py)，并用 `(content_hash, engine_version)` 做缓存键跑通两次（第二次命中缓存、零重算）。

### 验证步骤

1. 创建 `canonical_input = "乾造 庚申 戊寅 壬子 辛丑 ..."` 测试输入。
2. 第一次调用：`output1 = run_pipeline_e2e(canonical_input)`，记录耗时 T1。
3. 第二次调用：`output2 = run_pipeline_e2e(canonical_input)`，记录耗时 T2。
4. 验证：`output1.to_dict() == output2.to_dict()` 且 T2 < 100ms（缓存命中）。

**这一个动作就证明了"计算与状态解耦"成立。** 如果这个验证通过，整个方向的技术风险降为零。

---

## Falsifier（证伪条件）

**如果发现 D1-D4 内部强依赖 `cases/` 目录的副作用**（中途读写案例文件、依赖落盘顺序），那么"pipeline 是无状态纯函数"的前提不成立，整个方向要退回到"有状态批处理 + 编排"模型。

### 需要检查的文件

- [`engine/energy/`](../engine/energy/)（段派做功）
- [`engine/picture/`](../engine/picture/)（杨派画像）
- [`engine/yingqi/`](../engine/yingqi/)（任派应期）
- [`engine/pangzheng/`](../engine/pangzheng/)（高派神煞）

检查点：搜索 `cases/`、`Path("cases")`、`open(`、`write_text`，确认这些操作是否在 [`run_pipeline_e2e`](../engine/application/pipeline_runner.py) 的调用链内。

### 应对策略

- **如果无副作用**：按 Staged clean path 继续。
- **如果有副作用但可隔离**：把副作用操作改为"返回待写入数据"，由外层决定落盘。
- **如果副作用深度耦合**：降级为"有状态 worker + 本地 workspace"模式，放弃多副本扩展，改走"单 worker + 队列"路径。

---

## 验证路径总结

| 步骤 | 产出 | Go/No-Go 决策点 |
|---|---|---|
| 1. 跑 First Proof Point | 证明 pipeline 可无状态化 | **关键**：如果失败，见 Falsifier |
| 2. 实现 ports.py + MVP 适配器 | 可替换的存储抽象 | - |
| 3. 实现 SubmissionService / AnalysisWorker | 用例边界按终态切分 | - |
| 4. 报告改为 lazy 派生 | 移出请求路径 | - |
| 5. 暴露网络前加鉴权 | API Key / mTLS | **关键**：不加鉴权禁止上生产 |
| 6. 量级确认后换存储 | Redis + PG + S3 | 只在真实需求出现后做 |

---

## 后续行动建议

1. **立即验证 Falsifier**：花半天确认 D1-D4 是否依赖 `cases/` 副作用。
2. **如果验证通过**：按 [`plans/production-system-architecture-v2.md`](production-system-architecture-v2.md) 实施 Staged clean path。
3. **如果验证失败**：回到我标的 Falsifier 应对策略，选择降级路径。

**不要跳过第 1 步直接开始写代码。** 这个方向的整个赌注在"pipeline 可无状态化"，必须先验证这一条。

---

## 附录：关键文件清单

| 文件 | 作用 |
|---|---|
| [`engine/application/pipeline_runner.py`](../engine/application/pipeline_runner.py) | 当前分析入口，需验证无状态性 |
| [`engine/domain/analysis.py`](../engine/domain/analysis.py) | `AnalysisOutput` 数据契约 |
| [`engine/infrastructure/findings_repository.py`](../engine/infrastructure/findings_repository.py) | 当前 findings 落盘逻辑（需重构） |
| [`tools/feedback_ingest.py`](../tools/feedback_ingest.py) | 规则校准入口，触发版本变化 |
| [`META/project-state.json`](../META/project-state.json) | 当前产品版本 `1.3.1` |
| [`VERSION`](../VERSION) | 版本号事实源 |

---

**最后提醒**：这是一个格局判断，不是保证正确的答案。它的价值在于提供高杠杆的假设 + 严谨的验证路径。请先跑 First Proof Point，再决定是否投入后续工程。
