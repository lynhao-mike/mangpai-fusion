# v1.3.0 已发布 · Handoff · 2026-05-26

> 本文记录 v1.3.0 发布后的项目状态，供下一个 session/agent 无损接续。

---

## 一、当前状态：v1.3.0 已发布 ✅

**版本**：`VERSION` = `1.3.0`
**主分支**：`main`，HEAD = `fa0e8e6`（W4 验收 + smoke 脚本已合并）
**tag**：`v1.3.0`（本地已建，需手动 `git push origin v1.3.0`）
**工作目录**：`/projects/sandbox/mangpai-fusion`

### W1-W4 全部完成并合并 main

| PR | 内容 | 关键产出 |
|---|---|---|
| #26 | 架构方案 D1-D8 锁定 | `plans/architecture-v1.3.md` |
| #27 | W1: D1+D2+D5 | statement_id / 双版报告 / feedback_ingest |
| #28 | W2: D6+D7 | batch_intake / batch_review / late_feedback / event_signature |
| #29 | W3: D3+D4+D8 | boundary_miner / veto_miner / iteration_report / 自动触发接入 |
| #37 | W4: 验收 + smoke 脚本 | H1-H6 全 PASS / 嵌套 if bug 修复 |

### v1.3.0 发布后已完成（本次 session）

| 任务 | 结果 |
|---|---|
| C-2026-015 反馈摄入 | ✅ 16 规律更新 / 5 状态变更 / 累计 11/30 |
| 轻量 metrics | ✅ pipeline.py PipelineTiming 已有 + tools/timing_report.py 全局聚合 |
| 决策 B 审查 | ✅ 已完全合规（YAML=metadata, Python=logic, check_consistency 通过）|

---

## 二、规律状态快照（截至本次 session）

| 类型 | 数量 |
|---|---|
| candidate（候选） | ~261 |
| confirmed（已确认）| ~645 |
| flagged_for_review（待人工审）| **7**（M2-Y-091 / M3-R-031 / M1-D-122 / M3-R-022 / M3-R-027 / M3-R-003 + 原有 3 条中 M3-R-005 已 deprecated）|
| deprecated（已弃用）| **1**（M3-R-005）|

### 新增 flagged_for_review（C-015 摄入触发）
- **M1-D-122**（段派）：累计 misses 3，posterior=0.33
- **M3-R-022**（任派）：累计 misses 3，posterior=0.43
- **M3-R-027**（任派）：累计 misses 3，posterior=0.20
- **M3-R-003**（任派）：累计 misses 3，posterior=0.20

### 新增 deprecated
- **M3-R-005**（任派）：从 flagged_for_review → deprecated（累计 4 miss / 0 hit）

---

## 三、决策 E 进度（Beta 切换）

- **累计反馈样本**：**11 / 30**（Beta 切换阈值）
- 当前置信度公式仍走**线性加权（4:6）**
- 还差 **19 案**

---

## 四、v1.3 工具速查

| 工具 | 路径 | CLI |
|---|---|---|
| 结构化反馈摄入 | `tools/feedback_ingest.py` | `python3 -m tools.feedback_ingest C-XXXX` |
| 批量入库 | `tools/batch_intake.py` | `python3 -m tools.batch_intake` |
| 批量复盘 | `tools/batch_review.py` | `python3 -m tools.batch_review` |
| 应期延迟反馈 | `tools/late_feedback.py` | `python3 -m tools.late_feedback C-XXX --year 2027 --event marriage --hit yes` |
| 边界自动挖掘 | `tools/boundary_miner.py` | `python3 -m tools.boundary_miner [rule_id]` |
| 候选否决兜底 | `tools/veto_miner.py` | `python3 -m tools.veto_miner [rule_id]` |
| 迭代报告调度 | `tools/iteration_report.py` | `python3 -m tools.iteration_report [--seq N]` |
| **Timing 聚合** | `tools/timing_report.py` | `python3 -m tools.timing_report [--human]` |

---

## 五、v1.3 新增模板 + 数据文件

| 文件 | 用途 |
|---|---|
| `templates/report-v1.3.md` | v1.3 双版报告模板（{% if is_master %} 控制反馈位） |
| `META/iteration-state.json` | D8 反馈完成案计数器（当前=11） |
| `META/timing-summary.json` | 全局 pipeline 耗时聚合 |
| `META/iteration-report-001.md` | 首次自迭代报告（10 案触发） |
| `cases/_TEMPLATE/feedback.md` | v1.3 反馈模板（报告即反馈表） |
| `plans/architecture-v1.3.md` | D1-D8 决策面板完整文档 |

---

## 六、沙箱约束提醒

- **无外网**（INTEGRATIONS_ONLY）→ pip install 全部失败
- **无 PyYAML** → 用 `ruamel.yaml`（已预装）做 shim：`smoke/run_ingest_c015.py` 有完整示例
- **无 pytest** → 用 `smoke/*.py` stdlib 脚本验证
- **git push** → 用 `mcp_sandbox_github_push_to_remote`
- **PR 创建** → 用 `mcp_sandbox_github_create_pull_request`

---

## 七、下一步行动

### 立即可做
1. **Review 7 条 flagged_for_review 规律** → 决定保留观察 / 收紧条件 / 退役
2. **继续摄入新案反馈**（还差 19 案达到 Beta 切换阈值 30）
3. **手动 `git push origin v1.3.0`** 推送 tag

### 短期（1-4 周）
4. 历史报告回溯扫描：`tools/output_linter.py` 跑 reports/*.md（验证 W9 cross-domain check）
5. 在 `engine/contracts/03-findings-schema.md` 增加 `industry_path` + `wealth_level.framework` 字段（CFL-C015-002）
6. v1.4 应期模型扩展 `event_type_hypotheses` 字段（CFL-C015-003）

### 中期（v1.4 路线图）
7. 跨维度输出耦合性 gate 完整落地（P(体制内)>0.7 时切换输出框架）
8. 命宫长生诀自动算法
9. 问真 APP input.md 直接解析
10. 八字指纹相似案检索器

---

## 八、新开对话的第一条指令

```
项目 mangpai-fusion v1.3.0 已发布。

当前状态：
- main HEAD = fa0e8e6，tag v1.3.0
- 累计反馈案 11/30（Beta 切换阈值）
- 7 条规律 flagged_for_review，1 条 deprecated

可选工作：
1. Review flagged 规律（M2-Y-091 / M3-R-031 / M1-D-122 / M3-R-022 / M3-R-027 / M3-R-003 / M3-R-005）
2. 摄入新案反馈（python3 -m tools.feedback_ingest C-XXXX）
3. 开始 v1.4 规划（CFL-C015-002 跨维度耦合 + CFL-C015-003 应期事件类型分流）

仓库：lynhao-mike/mangpai-fusion
工作目录：/projects/sandbox/mangpai-fusion
沙箱约束：无 PyYAML（用 ruamel.yaml shim）/ 无 pytest / 无外网
```

---

**本 handoff 由 v1.3.0 发布后收尾 session 于 2026-05-26 写入。**
**v1.3.0 全部完成。W4 验收 PASS。C-015 反馈已摄入。timing 聚合已上线。决策 B 合规。**
