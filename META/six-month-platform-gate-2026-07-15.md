# 六个月平台门禁报告（2026-07-15）

**最终判定：HOLD**

本报告对应 Task 14（六个月生产候选验收，月 6），依据六项证据门槛逐条核查，形成 GO/HOLD/STOP 判定。判定不因任务完成数自动升为 GO；所有缺失证据均如实记录。

---

## 验证前置检查

| 检查项 | 结果 |
|---|---|
| `pytest tests -q` | ✓ PASS（1272 passed，6 skipped，无 failure/error） |
| `tools/tool_registry.py --check` | ✓ exit 0 |
| `tools/rule_status_scan.py --check` | ✓ exit 0，总规则 914，confirmed 647，candidate 261，pending_normalization 6，0 flagged，0 deprecated |
| `git diff --check` | ✓ 无输出，exit 0 |

---

## 八项证据评估

### 1. 六域 Claim 覆盖（structure / event / timing 三段均有非空输出）

**PARTIAL**

- 三段输出情况：
  - **structure 段**：ziping（58 条）、ditiansui（45 条）有 claim 输出，覆盖 structure.overview 任务。
  - **event 段**：duan（marriage.divorce_or_remarriage 29 条）、yang（42 条）、gao（wealth.debt 21 条）有 claim 输出。
  - **timing 段**：当前十任务矩阵中，timing 类任务（career.change_window、marriage.event_window、health.event_window、wealth.major_loss_window）的 claim 输出全为 0，任/段 runner 因缺少逐年流年序列大量 abstain，timing 段无实质 claim 覆盖。
- 总 claim 数：195；总 unsupported：2624；总 abstain：1021。
- 结论：structure 与 event 两段有非空输出，timing 段缺乏 claim 覆盖，判为 PARTIAL。

---

### 2. 独立效用（至少一个任务 learned 效用 ≥ static 且选择有变化）

**✗ 不满足**

- 留出可评分记录：15 条；多派竞争记录：9 条（career.change_window 2，career.role_change 2，marriage.event_window 5）。
- 选择变化数：**0**；learned 平均效用：-0.1000；static 平均效用：-0.1000。
- 15 条记录中，learned 与 static 选择完全相同，learned 路由尚未证明条件化路由增量。
- 竞争门槛（最低 5）仅 marriage.event_window 达到，但选择亦无变化。
- 结论：独立效用假设不成立，L1 留出报告结论为 HOLD。

---

### 3. 校准可用（至少一个任务有足够校准样本，calibration_error < 0.2）

**✗ 不满足**

- 所有任务校准状态：`insufficient`。
- binary 概率校准样本数：**0**；static/learned Brier 均为 None。
- 所有后验均值 0.500，95% CI [0.000, 1.000]，N_eff 均为 0——表明无有效校准样本。
- 六派中无 posterior > 0 的有效校准估计。
- 结论：无任何任务达到可校准门槛，该项不满足。

---

### 4. 高风险任务 A 级标签可评估

**✗ 不满足（但无假阳性）**

- 高风险假阳性分类数：**0**。
- 可评估的高风险记录数：**0**。
- Tasks 3—5 新增高风险任务缺少合格 A 级双审人工标签，未降级门槛。
- 没有把门槛降级来美化指标；高风险任务保持不可评分状态。
- 结论：0 假阳性但 0 可评估，无法对高风险任务进行有效评价，该项不满足。

---

### 5. 审计链可复现（冻结摘要一致，规则加载器生效，staged runner 隔离）

**✓ 满足**

- 冻结摘要已在能力基线中验证并绑定 Task 8 制品。
- 以下组件均已落地：[`engine/application/production_rule_loader.py`](../engine/application/production_rule_loader.py)（规则加载器）、[`engine/claims/`](../engine/claims/)（Claim 规则）、[`engine/application/staged_parallel_runner.py`](../engine/application/staged_parallel_runner.py)（staged runner 隔离）、[`tools/batch_rl_backtest.py`](../tools/batch_rl_backtest.py)（运行对照）。
- 制品摘要与冻结摘要可通过基线 JSON 独立校验。
- 结论：审计链可复现，该项满足。

---

### 6. 反馈归因完整（claim 可追溯到 evidence → fact_refs）

**✓ 满足**

- 所有 claim 均通过 [`engine/claims/domain.py`](../engine/claims/domain.py) 中 `Evidence` 结构挂载 `fact_refs`（`four_pillars.*`、`liunian_steps.*`、`dayun_steps.*`），`evidence_id` 由 SHA-256 派生保证稳定性。
- `validate_claim_evidence` 在测试中覆盖 fact_ref 合法性校验。
- 内部语句索引负责挂载每个事项的层级判断，feedback 可追溯到 Claim → evidence → fact_refs 链路。
- 结论：反馈归因完整，该项满足。

---

### 7. 前瞻证据（至少 30 个 prospective 或 E3 案例进入冻结评估链）

**✗ 不满足**

- 当前分类：`historical_blind_candidate`；状态：`VALID_READ_ONLY`。
- 本轮无新增前瞻样本；旧 bundle 标识为历史隔离批次，不会升级为 prospective 或 E3。
- prospective 案例数：**0**（距离 GO 门槛 30 差距为 30）。
- 历史反馈早于当前六来源 runner 预测，不满足前瞻隔离条件。
- 结论：前瞻证据为 0，远低于 GO 门槛 30，该项不满足。

---

### 8. 无内部 ID 泄露（Claim 与语句追踪标识不出现在公开报告中）

**✓ 满足**

- [`tests/v5/test_report_view.py`](../tests/v5/test_report_view.py) 通过正则断言公开报告中不含 Claim、预测、语句及语句索引等内部追踪字段。
- [`tests/test_output_linter.py`](../tests/test_output_linter.py) 亦覆盖出口校验，阻止内部 ID 出现在可读报告中。
- 所有测试在本次验证中通过。
- 结论：无内部 ID 泄露，该项满足。

---

## 八项汇总

| # | 证据维度 | 结果 | 说明 |
|---|---|---|---|
| 1 | 六域 Claim 覆盖 | PARTIAL | structure/event 有输出，timing 段 claim 为 0 |
| 2 | 独立效用 | ✗ | 选择变化 0，learned/static 效用完全相同 |
| 3 | 校准可用 | ✗ | binary 校准样本 0，所有任务 insufficient |
| 4 | 高风险任务可评估 | ✗ | 高风险可评估记录 0，无 A 级标签 |
| 5 | 审计链可复现 | ✓ | 冻结摘要验证，规则加载器与 staged runner 已落地 |
| 6 | 反馈归因完整 | ✓ | claim → evidence → fact_refs 链路完整 |
| 7 | 前瞻证据 | ✗ | prospective 案例 0，目标 ≥ 30 |
| 8 | 无内部 ID 泄露 | ✓ | 出口校验测试覆盖，全部通过 |

---

## 判定依据

**GO 条件逐条核查：**

- 六域覆盖：PARTIAL（timing 段缺失）→ **未达 GO**
- 独立效用：✗ → **未达 GO**
- 校准可用：✗ → **未达 GO**
- 高风险假阳性 = 0 且 A 级标签可评估：✗（可评估 = 0）→ **未达 GO**
- 前瞻证据 ≥ 30：✗（当前 0）→ **未达 GO**
- 测试全过、工具检查通过：✓

**结论：GO 条件有 5 项未满足，判定为 HOLD。**

不满足 GO 的项目数量（5）和证据缺口清晰明确，不存在 STOP 条件（learned 路由在真实竞争样本下效用未低于 static，效用相同而非退化）。

---

## HOLD 状态下的行动约束

1. 保持 staged 并跑（`staged_parallel_runner`），不切换默认入口。
2. 不修改 `run_pipeline()`、`DEFAULT_RUNNER_REGISTRY`、静态权重文件或 legacy 入口。
3. 不删除任何异常样本或 unsupported/abstain 输出记录，所有失败原因如实保留。

---

## 下一个不可逆决策所需的最小操作步骤

要从 HOLD 转为 GO，需按优先顺序完成以下步骤：

**步骤 1（前瞻证据，E6）**：
使用 `python -m tools.school_capability_dataset prospective-intake` 摄入至少 30 个真实新案例，为 career/marriage/wealth/health 任务提供含正负例的前瞻标签，使 prospective 或 E3 案例总数 ≥ 30。

**步骤 2（校准，E3）**：
对 career.role_change 或 marriage.divorce_or_remarriage 任务积累 ≥ 20 条带观测结果的 binary 概率校准样本，使 calibration_error < 0.2。

**步骤 3（独立效用，E2）**：
在三个竞争任务（career.change_window、career.role_change、marriage.event_window）上，使多派竞争样本 ≥ 5 且至少一个任务的 learned 选择与 static 有实质差异（选择变化 ≥ 1）。

**步骤 4（重跑门禁）**：
完成步骤 1—3 后，重跑 L1 留出对照门禁。若 E2/E3/E6 均满足，再提交独立契约变更提案将 staged 路径设为默认，旧路径保留显式 fallback；不在验收文档中直接切换生产入口。

---

## 制品路径

- JSON 制品：[`META/six-month-platform-gate-2026-07-15.json`](six-month-platform-gate-2026-07-15.json)
- 能力基线：[`META/six-month-capability-baseline-2026-07-15.json`](six-month-capability-baseline-2026-07-15.json)
- L1 留出报告：[`reports/l1-routing-holdout-comparison.md`](../reports/l1-routing-holdout-comparison.md)
