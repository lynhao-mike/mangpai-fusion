# v1.3.0 已发布 · Handoff · 2026-05-26

> 本文记录 v1.3.0 发布后的项目状态，供下一个 session/agent 无损接续。
>
> **易漂移信息真相源**：当前 N_eff、规则状态数量、flagged/deprecated 清单只在本文 § 二/三维护；其他文档只链接本文，不复制数字。人工审查与最终裁决只写入 [`META/arbitration-log.md`](META/arbitration-log.md:245)。

---

## 一、当前状态：v1.3.0 已发布 ✅

**版本**：[`VERSION`](VERSION) = `1.3.0`
**主分支**：`main`（HEAD = `git rev-parse HEAD` 运行时查询；不在本文硬编码——见 [`engine/contracts/00-OVERVIEW.md`](engine/contracts/00-OVERVIEW.md) § 〇 单一信息源）
**契约版本**：v1.3.0-current（[`engine/contracts/00-OVERVIEW.md`](engine/contracts/00-OVERVIEW.md)）
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

> 维护规则：本节是短期交接快照，允许硬编码当前数量与清单；任何 feedback ingest、rule_lifecycle 降级/恢复、人工 review 执行后，必须同步更新本节。除本文外，不在 [`STATUS.md`](STATUS.md:110)、计划文档或 README 中复写这些数字。

| 类型 | 数量 |
|---|---|
| candidate（候选） | ~261 |
| confirmed（已确认）| ~645（含 v1.4 W1 architect-review 后从 flagged 恢复的 M3-R-031）|
| flagged_for_review（待人工审）| **3**（**M1-D-122** / **M3-R-003** / **M3-R-022**） |
| deprecated（已弃用）| **3**（**M2-Y-091** / **M3-R-005** / **M3-R-027**）|

### 当前 flagged_for_review（待架构师 review）
- **M1-D-122**（段派）：累计 misses 3，posterior=0.33
- **M3-R-003**（任派）：累计 misses 3，posterior=0.20。**已加 `quantifiable: false`**（v1.4 V1 → 后续 ingest 不再计分，但 status 维持 flagged 等明确 review 决议）
- **M3-R-022**（任派）：累计 misses 3，posterior=0.43

### 当前 deprecated
- **M2-Y-091**（杨派）：v1.4 W1 architect review 决议 deprecate
- **M3-R-005**（任派）：累计 4 miss / 0 hit
- **M3-R-027**（任派）：累计 misses 3，posterior=0.20，v1.4 W1 architect review 决议 deprecate

### v1.4 W1 architect review 恢复 confirmed
- **M3-R-031**（任派 · 六合婚姻应期）：5 hit / 3 miss，3 个 miss 均为"婚姻"域误用 → 加 `domain_restriction: [应期]` 收紧适用域，从 flagged 恢复 confirmed

---

## 三、决策 E 进度（Beta 切换）

- **N_eff（有效反馈样本数）**：**11 / 30**（Beta 切换阈值，截至 2026-05-26）
- 公式：`N_eff = N_y + N_n + 0.5·(N_late_hit + N_late_miss)`，详见 [`engine/contracts/06-confidence-model.md`](engine/contracts/06-confidence-model.md) § 2.1
- 当前置信度公式仍走**线性加权（4:6）**
- 还差 **19 案**（按 N_eff 增长率估）

> ⚠️ 本节是"易漂移"信息（每次 ingest 都在变）。手动维护时**只更新本节**，不要复制到其他文档；其他文档应链接回本节。

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
1. 按 [`META/arbitration-log.md`](META/arbitration-log.md:245) 的固定入口 review 当前 flagged_for_review 规律（清单以本文 § 二为准）→ 决定保留观察 / 收紧条件 / 退役
2. **继续摄入新案反馈**（N_eff 进度以本文 § 三为准）
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
- main HEAD = `git rev-parse HEAD`（不硬编码；详见 STATUS.md / 00-OVERVIEW.md § 〇）
- tag v1.3.0
- N_eff / 规则状态 / flagged 清单：只读本 handoff § 二/三，禁止复制到其他文档
- 人工 review 固定入口：META/arbitration-log.md § 九/十

可选工作：
1. Review 当前 flagged 规律（清单以本 handoff § 二为准）
2. 摄入新案反馈（python3 -m tools.feedback_ingest C-XXXX）
3. 按 plans/architecture-v1.4.md 状态矩阵继续收口 v1.4

仓库：lynhao-mike/mangpai-fusion
工作目录：/projects/sandbox/mangpai-fusion
沙箱约束：无 PyYAML（用 ruamel.yaml shim）/ 无 pytest / 无外网
```

---

**本 handoff 由 v1.3.0 发布后收尾 session 于 2026-05-26 写入。**
**v1.3.0 全部完成。W4 验收 PASS。C-015 反馈已摄入。timing 聚合已上线。决策 B 合规。**
