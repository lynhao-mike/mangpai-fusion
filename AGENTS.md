# AGENTS.md · mangpai-fusion AI 调用入口

> 本文件是任意 AI / LLM agent 进入本仓库后的第一入口。目标是在最短时间内明确：仓库用途、事实源、常用工作流、可执行工具与禁止事项。

---

## 1. 仓库目的

mangpai-fusion 是一个面向命理师实战调用的四派盲派融合八字分析系统，整合高德臣、段建业、杨清娟、任付红四派理论，输出带证据链、派别归属与双轨置信度（★ 等级 + 百分比）的分析报告，并通过案例反馈持续校准规则。

---

## 2. 必读顺序

AI agent 执行任务前按以下顺序读取：

1. [`README.md`](README.md)：人类入口与总体导航。
2. [`AGENTS.md`](AGENTS.md)：AI 调用规则与事实源矩阵。
3. [`META/project-state.json`](META/project-state.json)：机器可读当前项目状态。
4. [`STATUS.md`](STATUS.md)：稳定项目仪表盘。
5. [`tools/README.md`](tools/README.md)：唯一工具索引。
6. [`engine/README.md`](engine/README.md)：引擎接口说明。
7. [`engine/contracts/00-OVERVIEW.md`](engine/contracts/00-OVERVIEW.md)：契约总览。

不要从历史计划、旧 handoff 或 deprecated 工具开始推断当前流程。

---

## 3. 事实源矩阵

| 信息类型 | 唯一事实源 | 说明 |
|---|---|---|
| 产品版本 | [`VERSION`](VERSION) | 单行机器可读版本号；不要从阶段名推断。 |
| Python 包版本 | [`engine/__init__.py`](engine/__init__.py) | 必须与 [`VERSION`](VERSION) 一致。 |
| 当前项目状态 | [`META/project-state.json`](META/project-state.json) | 给 AI / 脚本读取的项目级状态；`current_phase` 是工作阶段，不等同于产品版本。 |
| 迭代计数状态 | [`META/iteration-state.json`](META/iteration-state.json) | 反馈完成案、迭代序号等机器状态。 |
| 工具状态 | [`tools/README.md`](tools/README.md) + [`tools/tool_registry.py`](tools/tool_registry.py) | 工具 active/deprecated/internal/missing 分类。 |
| 规则状态快照 | [`tools/rule_status_scan.py`](tools/rule_status_scan.py) | 易漂移规则数量、N_eff、review 清单运行时扫描。 |
| 规则生命周期 | [`engine/contracts/05-rule-lifecycle.md`](engine/contracts/05-rule-lifecycle.md) | 状态机与字段语义。 |
| 置信度模型 | [`engine/contracts/06-confidence-model.md`](engine/contracts/06-confidence-model.md) | 双轨置信度与 Beta 切换口径。 |
| 历史变更 | [`META/rule-changelog.md`](META/rule-changelog.md) | 只做历史追溯，不作为当前状态源。 |
| 人工裁决 | [`META/arbitration-log.md`](META/arbitration-log.md) | 冲突与规则 review 的人工决议。 |

---

## 4. 核心数据流

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

---

## 5. 常见任务

### 5.1 新增案例

1. 按 [`templates/input-from-wenzhen.md`](templates/input-from-wenzhen.md) 整理输入。
2. 建立 [`cases/`](cases/) 下的案例目录。
3. 运行入口校验：

```bash
python -m tools.preflight cases/C-YYYY-NNN-乾-干支/input.md
```

### 5.2 生成报告

1. 使用 [`engine/pipeline.py`](engine/pipeline.py) 的 pipeline 产出结构化 findings。
2. 使用 [`tools/render_report.py`](tools/render_report.py) 渲染报告。
3. 使用 [`tools/output_linter.py`](tools/output_linter.py) 做出口校验。
4. 报告归档到 [`reports/`](reports/)。

### 5.3 摄入反馈

1. 在案例目录维护 [`feedback.md`](templates/feedback.md) 格式反馈。
2. 运行：

```bash
python -m tools.feedback_ingest C-YYYY-NNN-乾-干支
```

3. 若批量处理，使用：

```bash
python -m tools.batch_review
```

### 5.4 查看工具索引

```bash
python tools/tool_registry.py --format markdown
python tools/tool_registry.py --check
```

### 5.5 查看规则状态

```bash
python tools/rule_status_scan.py --format markdown
python tools/rule_status_scan.py --check
```

### 5.6 跑测试

```bash
pytest tests/
pytest tests/test_project_metadata.py -q
```

---

## 6. 禁止事项

- 不要在多个文档中手写产品版本号；版本以 [`VERSION`](VERSION) 为准。
- 不要把 [`META/project-state.json`](META/project-state.json) 中的 `current_phase` 当成产品版本；它只是当前工作阶段。
- 不要把 N_eff、规则数量、flagged/deprecated 清单长期写入普通文档；运行 [`tools/rule_status_scan.py`](tools/rule_status_scan.py) 获取。
- 不要使用 [`tools/calibrate.py`](tools/calibrate.py) 作为新反馈入口；它是 deprecated 历史工具。
- 不要引用不存在的旧工具名作为可执行入口，例如 `seal_prediction.py`、`verify_evidence.py`。
- 不要把 [`handoff.md`](handoff.md) 当作长期真相源；它只保留短期下一步。
- 不要在报告标题遗漏性别命式（乾/坤）。

---

## 7. 文档分工

| 文件 | 定位 |
|---|---|
| [`README.md`](README.md) | 人类入口与总体导航。 |
| [`AGENTS.md`](AGENTS.md) | AI agent 操作手册。 |
| [`STATUS.md`](STATUS.md) | 稳定仪表盘。 |
| [`handoff.md`](handoff.md) | 短期下一步，不作事实源。 |
| [`tools/README.md`](tools/README.md) | 工具唯一索引。 |
| [`META/project-state.json`](META/project-state.json) | 机器可读项目状态。 |
| [`META/iteration-state.json`](META/iteration-state.json) | 机器可读迭代状态。 |
| [`META/rule-changelog.md`](META/rule-changelog.md) | 历史变更。 |
| [`plans/`](plans/) | 架构方案与历史计划。 |

---

## 8. 最小上下文原则

通用 AI 在执行小任务时，优先读取：

1. [`AGENTS.md`](AGENTS.md)
2. [`META/project-state.json`](META/project-state.json)
3. 任务直接相关文件
4. [`tools/README.md`](tools/README.md) 或对应工具源码

只有在涉及架构、版本、契约或历史回溯时，才读取 [`STATUS.md`](STATUS.md)、[`plans/`](plans/) 与 [`META/rule-changelog.md`](META/rule-changelog.md)。
