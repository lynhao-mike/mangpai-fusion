# handoff · 短期下一步

> 本文件只服务当前/下一次 session 的短期交接，不作为版本、规则数量、N_eff、flagged/deprecated 清单的长期事实源。长期入口见 [`AGENTS.md`](AGENTS.md)，稳定状态见 [`STATUS.md`](STATUS.md)，机器状态见 [`META/project-state.json`](META/project-state.json)。

---

## 1. 当前工作状态

- 产品版本：见 [`VERSION`](VERSION)。
- 当前阶段：v1.4 schema/reporting convergence + 子平 / 滴天髓生产规则接入已完成；v1.5 多专家功能域裁判旁路第一版已落地。
- 本次重构结果：子平 / 滴天髓规则从候选池转入生产规则库，进入 pipeline 最终断语、标准报告展示、证据链与回归测试；新增多专家功能域裁判模型、调度器、报告展示与 statement_index 追踪。

---

## 2. 下一步行动

1. 继续摄入真实案例反馈，入口为 [`tools/feedback_ingest.py`](tools/feedback_ingest.py) 或 [`tools/batch_review.py`](tools/batch_review.py)。
2. 继续扩充子平 / 滴天髓生产规则时，只编辑 [`theory/ziping/index.yaml`](theory/ziping/index.yaml) 与 [`theory/tiaohou_ditiansui/index.yaml`](theory/tiaohou_ditiansui/index.yaml)，并同步补 [`tests/test_production_rule_loader.py`](tests/test_production_rule_loader.py) / 报告渲染回归。
3. 多专家功能域裁判下一步重点：把 [`statement_index.json`](templates/report-v1.3.md:118) 的 reading / vote 追踪接入反馈动态调权，并把 [`engine/application/parallel_domain_orchestrator.py`](engine/application/parallel_domain_orchestrator.py) 的静态权重迁移到可校准配置。
4. 需要查看规则状态时运行 [`tools/rule_status_scan.py`](tools/rule_status_scan.py)，不要从本文读取硬编码数量。
5. 需要查看工具可用性时运行 [`tools/tool_registry.py`](tools/tool_registry.py)。
6. 涉及架构扩展时优先查看 [`plans/architecture-v1.4.md`](plans/architecture-v1.4.md)、[`plans/parallel-domain-voting-architecture.md`](plans/parallel-domain-voting-architecture.md) 与 [`engine/contracts/00-OVERVIEW.md`](engine/contracts/00-OVERVIEW.md)。

---

## 3. 易漂移信息处理规则

不得在本文长期维护以下信息：

- git HEAD / tag 推送状态。
- N_eff 当前值。
- candidate / confirmed / flagged_for_review / deprecated 当前数量。
- flagged_for_review 具体规则清单。
- deprecated 具体规则清单。

使用以下命令获取实时状态：

```bash
git rev-parse HEAD
python tools/rule_status_scan.py --format markdown
python tools/rule_status_scan.py --check
python tools/tool_registry.py --check
```

---

## 4. 新开对话推荐指令

```text
请先读取 AGENTS.md 与 META/project-state.json，再根据任务读取相关文件。不要把 handoff.md 当作长期事实源；需要工具状态运行 tools/tool_registry.py，需要规则状态运行 tools/rule_status_scan.py。
```
