# STATUS · 稳定项目仪表盘

> 本文件只保留稳定项目状态、当前阶段、主要入口与路线链接。易漂移数据（HEAD、N_eff、规则数量、flagged/deprecated 清单）不得在本文硬编码。

---

## 1. 当前状态

| 项目 | 当前值 / 事实源 |
|---|---|
| 产品版本 | 见 [`VERSION`](VERSION) |
| Python 包版本 | 见 [`engine/__init__.py`](engine/__init__.py) |
| 机器可读项目状态 | [`META/project-state.json`](META/project-state.json) |
| 迭代计数状态 | [`META/iteration-state.json`](META/iteration-state.json) |
| 契约总览 | [`engine/contracts/00-OVERVIEW.md`](engine/contracts/00-OVERVIEW.md) |
| 工具索引 | [`tools/README.md`](tools/README.md) |
| 工具注册校验 | [`tools/tool_registry.py`](tools/tool_registry.py) |
| 规则状态扫描 | [`tools/rule_status_scan.py`](tools/rule_status_scan.py) |
| 人工裁决 | [`META/arbitration-log.md`](META/arbitration-log.md) |
| 历史变更 | [`META/rule-changelog.md`](META/rule-changelog.md) |

当前阶段：v1.3 自迭代闭环已上线，v1.4 schema 与报告收口进行中。产品版本仍以 [`VERSION`](VERSION) 为准；阶段名只描述当前工作流，不表示已发布 v1.4 产品版本。报告出口已收敛到 C-2026-025 唯一标准，历史报告模板分叉不再作为入口。子平 / 滴天髓生产规则已接入 pipeline 与标准报告出口，规则来源以 [`theory/ziping/index.yaml`](theory/ziping/index.yaml) 与 [`theory/tiaohou_ditiansui/index.yaml`](theory/tiaohou_ditiansui/index.yaml) 为准，不从 raw candidate 文件旁路加载。

---

## 2. 已完成里程碑

| 里程碑 | 内容 | 状态 |
|---|---|---|
| M1 | 仓库骨架 + schema + 语料迁入 | ✅ 完成 |
| M2 | 高派 + 段派规律入库 | ✅ 完成 |
| M3 | 杨派 + 任派规律入库 | ✅ 完成 |
| M4 | 跨派映射矩阵 | ✅ 完成 |
| M5 | 双轨置信度引擎 + 仲裁引擎 | ✅ 完成 |
| M6 | 主分析器 + 输入输出模板 | ✅ 完成 |
| M7 | META 自迭代 + 校准工具 + 案例归档 | ✅ 完成 |
| M8 | v1.2 双层引擎契约与发布门槛 | ✅ 完成 |
| M9 | v1.2 维度引擎 + 三层护栏 | ✅ 完成 |
| M10 | v1.3 自迭代闭环 D1-D8 | ✅ 完成 |

---

## 3. 当前可用能力

- 四派融合分析：高德臣 / 段建业 / 杨清娟 / 任付红。
- 双轨制置信度：★ 等级 + 百分比，区间以 [`engine/contracts/06-confidence-model.md`](engine/contracts/06-confidence-model.md) 为准。
- 三层应期门：原局有、大运到位、流年引爆。
- C-2026-025 唯一标准报告（命主可读版；产品 v1.3.0 / pipeline schema v1.4.0）。
- 结构化反馈摄入：`[y]` / `[n]` / `[?]` / `[skip]`。
- 规则生命周期：candidate / confirmed / flagged_for_review / deprecated。
- 每 10 完成反馈案触发迭代报告。
- 工具索引与规则状态可运行时扫描。
- 子平 / 滴天髓生产规则库：经 [`engine/application/production_rule_loader.py`](engine/application/production_rule_loader.py) 加载，进入 [`engine/application/integration.py`](engine/application/integration.py) 的最终断语与证据链，并在标准报告模板展示。
- 多专家功能域裁判旁路：经 [`engine/application/parallel_domain_orchestrator.py`](engine/application/parallel_domain_orchestrator.py) 生成盲派专家组 / 子平 / 滴天髓在学业、事业、财运、婚姻、健康、性格六域的读数与裁判结果，并写入 [`AnalysisOutput.parallel_analysis`](engine/domain/analysis.py:179)。

---

## 4. 当前不可硬编码的信息

以下信息属于易漂移状态，不应写入 [`README.md`](README.md)、[`STATUS.md`](STATUS.md)、[`AGENTS.md`](AGENTS.md) 或计划文档正文：

- git HEAD / tag 推送状态。
- N_eff 当前值。
- candidate / confirmed / flagged_for_review / deprecated 当前数量。
- 当前 flagged_for_review 具体清单。
- 当前 deprecated 具体清单。

需要时运行：

```bash
git rev-parse HEAD
python tools/rule_status_scan.py --format markdown
python tools/rule_status_scan.py --check
```

---

## 5. 常用入口

| 任务 | 入口 |
|---|---|
| AI 快速理解仓库 | [`AGENTS.md`](AGENTS.md) |
| 新增案例入口校验 | [`tools/preflight.py`](tools/preflight.py) |
| 生成报告 | [`tools/render_report.py`](tools/render_report.py) |
| 报告出口校验 | [`tools/output_linter.py`](tools/output_linter.py) |
| 摄入单案反馈 | [`tools/feedback_ingest.py`](tools/feedback_ingest.py) |
| 批量复盘反馈 | [`tools/batch_review.py`](tools/batch_review.py) |
| 查看工具状态 | [`tools/tool_registry.py`](tools/tool_registry.py) |
| 查看规则状态 | [`tools/rule_status_scan.py`](tools/rule_status_scan.py) |

---

## 6. 近期路线

| 优先级 | 事项 | 参考 |
|---|---|---|
| P0 | 保持版本、工具索引、AI 入口一致性 | [`tests/test_project_metadata.py`](tests/test_project_metadata.py) |
| P1 | 继续摄入新案反馈，扩大有效样本 | [`tools/feedback_ingest.py`](tools/feedback_ingest.py) |
| P1 | 按运行时扫描结果处理 flagged_for_review 规则 | [`tools/rule_status_scan.py`](tools/rule_status_scan.py) |
| P2 | v1.4 findings schema 扩展 | [`plans/architecture-v1.4.md`](plans/architecture-v1.4.md) |
| P2 | 子平 / 滴天髓生产规则继续扩充触发器与回归样本 | [`theory/ziping/index.yaml`](theory/ziping/index.yaml)、[`theory/tiaohou_ditiansui/index.yaml`](theory/tiaohou_ditiansui/index.yaml) |
| P2 | 将多专家功能域裁判从旁路升级为反馈可动态调权的主裁判层 | [`engine/application/parallel_domain_orchestrator.py`](engine/application/parallel_domain_orchestrator.py)、[`tests/test_parallel_domain_orchestrator.py`](tests/test_parallel_domain_orchestrator.py) |
| P2 | 八字指纹相似案检索 | [`plans/`](plans/) |

---

## 7. 历史与追溯

- 详细历史变更：[`META/rule-changelog.md`](META/rule-changelog.md)
- 迭代日志：[`META/iteration-log.md`](META/iteration-log.md)
- 架构方案：[`plans/`](plans/)
- 短期交接：[`handoff.md`](handoff.md)，只作临时下一步，不作事实源
