# META · 自迭代元数据层

> 本目录保存 mangpai-fusion 的机器状态、迭代记录、规则变更、仲裁裁决与校准资料。它不是工具入口；工具入口统一见 [`tools/README.md`](../tools/README.md)。

---

## 1. 文件组织

```text
META/
├── INDEX.md                       本文件
├── project-state.json             机器可读项目级状态
├── iteration-state.json           机器可读迭代计数状态
├── ingestion-protocol.md          理论入库协议
├── calibration-methodology.md     双轨置信度校准方法论
├── source-trace.md                4 派来源追溯账本
├── rule-changelog.md              规则历史变更日志
├── arbitration-log.md             人工仲裁与 review 裁决
├── iteration-log.md               迭代日志
├── iteration-report-*.md          自动迭代报告
├── timing-summary.json            pipeline timing 聚合结果
└── calibration/                   校准快照归档
```

---

## 2. 事实源分工

| 信息类型 | 文件 |
|---|---|
| 当前项目机器状态 | [`project-state.json`](project-state.json) |
| 反馈完成案与迭代计数 | [`iteration-state.json`](iteration-state.json) |
| 规则历史变更 | [`rule-changelog.md`](rule-changelog.md) |
| 人工仲裁与 review 裁决 | [`arbitration-log.md`](arbitration-log.md) |
| 置信度校准方法 | [`calibration-methodology.md`](calibration-methodology.md) |
| 理论来源追溯 | [`source-trace.md`](source-trace.md) |
| 理论入库协议 | [`ingestion-protocol.md`](ingestion-protocol.md) |

---

## 3. 反馈与自迭代闭环

```text
cases/*/feedback.md
  → tools/feedback_ingest.py
  → tools/feedback_loop.py
  → tools/rule_lifecycle.py
  → theory/*/index.yaml
  → META/rule-changelog.md
  → META/iteration-state.json
  → META/iteration-report-*.md
```

当前反馈入口：

- 单案反馈：[`tools/feedback_ingest.py`](../tools/feedback_ingest.py)
- 批量复盘：[`tools/batch_review.py`](../tools/batch_review.py)
- 底层回流：[`tools/feedback_loop.py`](../tools/feedback_loop.py)

历史入口 [`tools/calibrate.py`](../tools/calibrate.py) 已 deprecated，不应用于新反馈。

---

## 4. 维护规则

1. 不手动篡改规则的 hit/miss 统计；通过反馈工具或明确人工裁决流程修改。
2. 所有规则状态变化必须能追溯到 [`rule-changelog.md`](rule-changelog.md) 或 [`arbitration-log.md`](arbitration-log.md)。
3. 易漂移规则数量、N_eff、flagged/deprecated 清单不写入普通文档；运行 [`tools/rule_status_scan.py`](../tools/rule_status_scan.py) 获取。
4. 工具状态不在本目录维护；以 [`tools/README.md`](../tools/README.md) 与 [`tools/tool_registry.py`](../tools/tool_registry.py) 为准。
5. AI agent 入口见 [`AGENTS.md`](../AGENTS.md)，不要从历史计划或旧 handoff 推断当前流程。
