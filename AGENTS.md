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
3. 若用户首次提交新命盘并要求“分析八字 / 看这个八字 / 分析这个八字 / 断这个八字”，默认自动生成命理师内部报告，并执行 5.2 的 [`reports/`](reports/) 与 [`cases/`](cases/) 双侧归档；不得只停留在会话分析。
   - “生成报告 / 形成报告 / 出报告 / 输出报告”仍默认理解为生成命理师报告，执行 5.2 的双侧归档。
   - 只有当用户明确说“生成用户报告 / 客户报告 / 命主可读报告 / 对外报告”时，才允许额外生成用户报告；不得把“报告”二字自动解释为用户报告。
   - 若用户明确要求“临时口头分析 / 不归档 / 不生成报告”，可先只答复分析；但必须在答复中标记“未归档、不可进入反馈闭环”，后续一旦要求报告，必须把首次分析内容补入同名 case 与 analyst report。
   - 所有正式命理师报告和 case [`analysis.md`](cases/_TEMPLATE/analysis.md) 必须覆盖学业 / 事业 / 财富 / 婚姻 / 健康 / 性格等主要事项；每个事项必须给出 15 层判断，格式至少包含“层级｜现实释义｜起止界限｜证伪条件”。
4. 运行入口校验：

```bash
python -m tools.preflight cases/C-YYYY-NNN-乾-干支/input.md
```

### 5.2 生成命理师报告

> **最高硬性约束**：当用户要求“分析八字 / 看这个八字 / 断这个八字 / 生成报告 / 形成报告 / 出报告 / 输出报告”时，默认生成命理师报告，并必须同时完成 [`reports/`](reports/) 与 [`cases/`](cases/) 两侧归档；只生成报告文件而不建立对应 case 目录与文件，视为未完成任务。
>
> **用户报告禁令**：除非用户明确要求“生成用户报告 / 客户报告 / 命主可读报告 / 对外报告”，否则不得生成用户报告；历史命主可读报告已删除，不再作为默认产物。
>
> **新案例首次分析约束**：新案例的首次正式分析默认需要输出命理师报告，必须在同一轮任务内生成命理师报告文件，并同步建立/更新同名 case 目录；不得先只给会话分析、事后遗漏报告或 case 归档。
>
> **15 层判断约束**：正式报告与 [`analysis.md`](cases/_TEMPLATE/analysis.md) 的每个主要事项 / 功能域都必须有 15 层判断；缺少任一主要事项的 15 层落点、现实释义、起止界限或证伪条件，视为报告未完成。

1. 使用 [`engine/pipeline.py`](engine/pipeline.py) 的 pipeline 产出结构化 findings。
2. 使用 [`tools/render_report.py`](tools/render_report.py) 渲染命理师报告。
3. 使用 [`tools/output_linter.py`](tools/output_linter.py) 做出口校验。
4. 命理师报告归档到 [`reports/`](reports/)，文件名必须包含 case_id、乾/坤与四柱，并默认使用 `-analyst-report.md` 后缀。
5. 同步在 [`cases/`](cases/) 下建立同名 case 目录：`cases/C-YYYY-NNN-{乾/坤}-{四柱}/`。
6. case 目录内至少生成：`input.md`、`analysis.md`、`feedback.md`、`statement_index.json`。
7. 命理师报告结尾与 case 文件中必须互相记录关联路径，确保后续反馈摄入可追踪。
8. 报告与 [`analysis.md`](cases/_TEMPLATE/analysis.md) 必须包含主要事项 15 层判断表，并把每个事项的层级判断挂入 `statement_index.json`，以便后续反馈校准。
9. 若是先会话分析、后要求报告，需把会话首次分析与后续反馈校准一并归档到 `analysis.md` / `feedback.md` / `statement_index.json`，再输出 analyst report。

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
