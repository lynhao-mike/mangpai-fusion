# Historical Isolation Incremental Batch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Execute this plan inline with explicit checkpoints. Do not create commits unless separately authorized. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `cases/shuru-input.md` 中未进入 2026-07-15 冻结制品的去重新命盘作为独立 `historical_blind_candidate` 批次，经先冻结、后揭示流程形成新的 03 评估制品，并生成独立的 04 L1 learned/static 路由竞争诊断。

**Architecture:** 从不可变的 2026-07-15 baseline 的 score case IDs 恢复旧冻结集合，以 `sex_marker + four_pillars` 为 subject identity 对当前输入做差集，生成仅含增量命盘的隔离输入。阶段 A 只读取增量输入、十任务目录与规则快照并冻结六来源输出；阶段 B 在独立进程先验证 freeze hash，再读取反馈并仅绑定低歧义、非高风险标签，随后复用正式 baseline `freeze → score → report` 契约。最终 L1 审计只消费新批次冻结事实和评分结果，不修改 runner、默认 static 路由或生产权重。

**Tech Stack:** Python 3、stdlib JSON/hashlib/pathlib、PyYAML、pytest、现有 `engine.evaluation`、`tools.school_capability_batch`、`tools.school_capability_task8`、`tools.school_capability_baseline` 与 `tools.l1_routing_holdout_audit`。

## Global Constraints

- 旧制品 `META/six-month-capability-baseline-2026-07-15.json` 与 `META/six-month-capability-baseline-2026-07-15.md` 必须保持字节不变；开始前记录 SHA-256，结束后复验。
- 新批次分类固定为 `historical_blind_candidate`，不得称为 prospective 或 E3。
- 新制品使用 `2026-07-16-incremental` 独立命名和独立中间目录，不覆盖任何旧制品。
- 阶段 A 不读取 feedback、labels、reports、known facts 或旧 scores；阶段 B 必须在新进程先验证 Stage A freeze hash 后才读取反馈。
- 只提取低歧义、精确年份、非推测语气的事件标签；高风险任务没有 A 级双审时保持不可评分。
- 不补造负例，不把“未提及”解释为 `not_observed`，不把风险描述解释为已发生事件。
- 不修改 `engine.application.pipeline_runner.run_pipeline()`、`engine.claims.runner_registry.DEFAULT_RUNNER_REGISTRY`、默认 static 路由、生产权重、runner 命理逻辑、评分公式或门禁阈值。
- `tools/feedback_ingest.py` 仅用于正式 case 反馈；本批评估标签由历史隔离批处理流程产生，不调用其他反馈入口。
- 所有会写文件的命令先用内存/临时路径 dry-run；正式目标必须预先验证不存在。
- 不创建 Git commit。

---

### Task 1: 恢复旧冻结集合并确定增量 subject

**Files:**
- Read: `META/six-month-capability-baseline-2026-07-15.json`
- Read: `cases/shuru-input.md`
- Create: `.historical-incremental-2026-07-16/incremental-input.md`
- Create: `.historical-incremental-2026-07-16/increment-audit.json`
- Test: `tests/evaluation/test_historical_incremental_batch.py`

**Interfaces:**
- Consumes: `parse_case_summary_with_audit(Path) -> BatchParseResult` 和旧 baseline 的唯一 `scores[*].case_id` 集合。
- Produces: `derive_incremental_cases(current_cases, frozen_case_ids) -> IncrementalAudit`；按 subject identity 排除旧冻结命主，保留真正新增 subject。

- [ ] **Step 1: 写失败测试**

覆盖：旧 frozen case 即使 base ID 不同也按 `sex_marker + four_pillars` 排除；当前重复 subject 只保留解析器审计选中的较完整记录；结果按 case ID 稳定排序；输出不含来源、反馈或报告文本。

- [ ] **Step 2: 运行失败测试**

Run:
```bat
python -m pytest tests/evaluation/test_historical_incremental_batch.py -q
```

Expected: FAIL，提示增量批次函数或 CLI 尚不存在。

- [ ] **Step 3: 实现最小增量筛选与 dry-run 摘要**

在专用工具中读取旧 baseline case IDs 和当前解析结果，恢复旧 subject 集合，输出 `current_raw_count`、`current_deduplicated_count`、`frozen_subject_count`、`incremental_case_ids`、`duplicate_audit` 与隔离输入文本。dry-run 只打印摘要与内容 SHA-256，不创建目录。

- [ ] **Step 4: 运行专项测试并执行 dry-run**

Run:
```bat
python -m pytest tests/evaluation/test_historical_incremental_batch.py -q && python -m tools.school_capability_incremental prepare --source cases/shuru-input.md --baseline META/six-month-capability-baseline-2026-07-15.json --out-dir .historical-incremental-2026-07-16 --dry-run
```

Expected: 测试 PASS；dry-run 报告旧冻结 64 个去重 subject、当前末尾 P-2026-076，并列出独立增量 case IDs；磁盘上不创建目标目录。

- [ ] **Step 5: 创建独立增量输入制品**

Run:
```bat
python -m tools.school_capability_incremental prepare --source cases/shuru-input.md --baseline META/six-month-capability-baseline-2026-07-15.json --out-dir .historical-incremental-2026-07-16
```

Expected: 目标目录此前不存在；只写 `incremental-input.md` 和 `increment-audit.json`。

### Task 2: Stage A 仅输入冻结

**Files:**
- Read: `.historical-incremental-2026-07-16/incremental-input.md`
- Read: `mapping/school-capability-task-catalog-v1.yaml`
- Read: `theory/production/claim-rules-v1.yaml`
- Create: `.historical-incremental-2026-07-16/stage-a/`

**Interfaces:**
- Consumes: `tools.school_capability_task8.build_stage_a()`，六来源与批准十任务。
- Produces: 增量命盘的六来源 × 十任务完整矩阵、可复验 freeze hash、无 revealed marker 的 frozen run。

- [ ] **Step 1: 内存 dry-run Stage A**

Run:
```bat
python -m tools.school_capability_incremental stage-a --input .historical-incremental-2026-07-16/incremental-input.md --catalog mapping/school-capability-task-catalog-v1.yaml --rules theory/production/claim-rules-v1.yaml --frozen-at 2026-07-16T06:40:00Z --out-dir .historical-incremental-2026-07-16/stage-a --dry-run
```

Expected: 输入全部可解析；输出 identity 数等于 `增量 case 数 × 10 × 6`；forbidden marker 扫描为零；不创建 Stage A 目录。

- [ ] **Step 2: 写 Stage A 制品**

使用与 dry-run 相同的固定 `frozen-at` 重跑并写入尚不存在的 Stage A 目录。

- [ ] **Step 3: 用正式 freeze CLI 交叉冻结**

Run:
```bat
python -m tools.school_capability_baseline freeze --outputs .historical-incremental-2026-07-16/stage-a/outputs.json --tasks .historical-incremental-2026-07-16/stage-a/tasks.json --rule-snapshot .historical-incremental-2026-07-16/stage-a/rule-snapshot.json --out .historical-incremental-2026-07-16/formal-frozen-run.json
```

Expected: 正式 CLI 输出新 frozen run；任务与规则 digest 可复验；不写入 `META/` 旧路径。

- [ ] **Step 4: 比对两条冻结身份**

断言 Stage A frozen outputs 与正式 CLI frozen outputs 相同，允许 `frozen_at` 由 CLI 产生新值，但各自 freeze hash 均可由 `verify_frozen_run()` 复验；后续正式评分绑定正式 CLI freeze hash。

### Task 3: Stage B 保守标签揭示

**Files:**
- Read after freeze verification: `cases/fankui-feedback.md`
- Create: `.historical-incremental-2026-07-16/stage-b/candidate-labels.json`
- Create: `.historical-incremental-2026-07-16/stage-b/bound-labels.json`
- Create: `.historical-incremental-2026-07-16/stage-b/label-audit.json`
- Test: `tests/evaluation/test_historical_incremental_batch.py`

**Interfaces:**
- Consumes: 已验证正式 frozen run、增量 case IDs、`parse_feedback_labels()` 的精确年份规则。
- Produces: 与正式 freeze hash 绑定的低风险标签，以及高风险/模糊/无标签拒绝审计。

- [ ] **Step 1: 写保守标签测试**

覆盖：只接受四位精确年份表格事件；含“可能”“待核”“约”的事件不进入；不生成未观察负例；`marriage.divorce_or_remarriage`、`wealth.debt`、`health.system_risk`、`health.event_window`、`wealth.major_loss_window` 在无 A 级双审时全部进入 hold audit 而非 bound labels。

- [ ] **Step 2: 新进程先验证 freeze hash**

Stage B CLI 必须先读取并验证 `.historical-incremental-2026-07-16/formal-frozen-run.json`，验证成功后才打开 `cases/fankui-feedback.md`。

- [ ] **Step 3: 执行标签 dry-run**

Run:
```bat
python -m tools.school_capability_incremental stage-b --frozen-run .historical-incremental-2026-07-16/formal-frozen-run.json --increment-audit .historical-incremental-2026-07-16/increment-audit.json --feedback cases/fankui-feedback.md --tasks .historical-incremental-2026-07-16/stage-a/tasks.json --reviewer historical-public-feedback-curation-2026-07-16 --out-dir .historical-incremental-2026-07-16/stage-b --dry-run
```

Expected: 打印 accepted/rejected/held-by-risk 数量和标签 identity；不创建 Stage B 目录；任何高风险标签可评分数为 0。

- [ ] **Step 4: 写入独立 Stage B 制品**

重跑同一命令去掉 `--dry-run`，目标目录必须不存在。若低风险标签尚未有人类复核，则在 label audit 明确记录 curator 身份与 evidence grade，不伪造 A 级或双审。

### Task 4: 正式 freeze → score → report 独立基线

**Files:**
- Create: `.historical-incremental-2026-07-16/stage-b/reviewed-manifest.json`
- Create: `.historical-incremental-2026-07-16/stage-b/evaluation-config.json`
- Create: `META/six-month-capability-baseline-2026-07-16-incremental.json`
- Create: `META/six-month-capability-baseline-2026-07-16-incremental.md`

**Interfaces:**
- Consumes: 正式 frozen run、十任务 CLI 目录、规则快照、bound labels、只覆盖增量 case/task 的 reviewed manifest/config。
- Produces: 正式 `school-capability-scores/v1` 证据、报告及日期化 `six-month-capability-baseline/v1` 增量摘要。

- [ ] **Step 1: 生成 manifest/config dry-run**

验证每个可评分 case/task 有六来源 route；metadata 精确覆盖正式 frozen outputs；eligible grid 与 labels 完全一致；高风险标签不在 grid；目标归档路径均不存在。

- [ ] **Step 2: 运行正式 score**

Run:
```bat
python -m tools.school_capability_baseline score --frozen-run .historical-incremental-2026-07-16/formal-frozen-run.json --manifest .historical-incremental-2026-07-16/stage-b/reviewed-manifest.json --labels .historical-incremental-2026-07-16/stage-b/bound-labels.json --tasks .historical-incremental-2026-07-16/stage-a/tasks.json --rule-snapshot .historical-incremental-2026-07-16/stage-a/rule-snapshot.json --evaluation-config .historical-incremental-2026-07-16/stage-b/evaluation-config.json --out .historical-incremental-2026-07-16/stage-b/scores.json
```

Expected: 正式 score 完成 manifest/task/rule/freeze digest 复验并写入独立 scores。

- [ ] **Step 3: 运行正式 report**

Run:
```bat
python -m tools.school_capability_baseline report --scores .historical-incremental-2026-07-16/stage-b/scores.json --manifest .historical-incremental-2026-07-16/stage-b/reviewed-manifest.json --out .historical-incremental-2026-07-16/stage-b/formal-report.md
```

Expected: scores artifact digest 与 manifest digest 复验通过。

- [ ] **Step 4: 归档增量摘要**

摘要必须记录增量 case IDs、case/label/output 数量、freeze hash、artifact digest、三态覆盖、后验、失败分类、标签限制与 `historical_blind_candidate` 身份；不得覆盖 2026-07-15 制品。

### Task 5: L1 路由竞争诊断

**Files:**
- Create: `META/l1-routing-holdout-audit-2026-07-16-incremental.json`
- Create: `reports/l1-routing-holdout-comparison-2026-07-16-incremental.md`
- Read: `mapping/school-capability-runner-coverage-v1.yaml`

**Interfaces:**
- Consumes: 新增量 historical batch/scores 或日期化 baseline adapter。
- Produces: 独立 deterministic split、竞争覆盖、learned/static selection changes、utility、校准、高风险和 prototype 诊断。

- [ ] **Step 1: dry-run 内存构建 L1 artifact**

使用固定 salt `historical-incremental-l1-routing-2026-07-16-v1` 和 `holdout_fraction=0.25`，先打印 holdout subject、竞争 case/task、选择变化、static/learned utility 与 gate status，不写文件。

- [ ] **Step 2: 写独立 L1 制品**

Run:
```bat
python -m tools.l1_routing_holdout_audit --batch .historical-incremental-2026-07-16/stage-a/historical-batch.json --scores .historical-incremental-2026-07-16/stage-b/historical-scores.json --static-coverage mapping/school-capability-runner-coverage-v1.yaml --salt historical-incremental-l1-routing-2026-07-16-v1 --out META/l1-routing-holdout-audit-2026-07-16-incremental.json --report reports/l1-routing-holdout-comparison-2026-07-16-incremental.md --generated-at 2026-07-16T07:00:00Z
```

Expected: 输出仅为诊断；无论 HOLD/STOP/GO 都不修改默认路由。若样本不足以切分或竞争覆盖为零，保留真实 HOLD 结果而不降低门槛。

- [ ] **Step 3: 与 2026-07-15 诊断对比**

报告新增量的 `competitive_case_task_count`、`selection_changes`、static/learned mean utility 是否改善；明确区分“覆盖增加”“选择变化”和“准确率/校准改善”，不得混称。

### Task 6: 更新短期交接并完成验证

**Files:**
- Modify: `handoff.md`
- Verify: `META/six-month-capability-baseline-2026-07-15.json`
- Verify: `META/six-month-capability-baseline-2026-07-15.md`
- Verify: all `2026-07-16-incremental` artifacts

**Interfaces:**
- Consumes: 新批次实际统计、freeze hash、artifact digest、L1 gate 结果和验证日志。
- Produces: 可供下一会话直接接手的最新历史隔离扩展状态。

- [ ] **Step 1: 更新 handoff**

替换过时的“Task 1 尚未开始”等陈述，记录 post-gate Task 1—2 已完成、Task 3 prospective 为 HOLD、本轮历史增量 case IDs、Stage A/B 制品、正式 baseline 结果、L1 竞争诊断、仍未满足的 prospective/E3 与高风险 A 级双审门槛。

- [ ] **Step 2: 复验不可变旧制品**

重新计算两个 2026-07-15 baseline 文件 SHA-256，与任务开始时记录完全一致；检查 Git diff 不包含旧制品。

- [ ] **Step 3: 运行专项测试**

Run:
```bat
python -m pytest tests/evaluation/test_historical_incremental_batch.py tests/evaluation/test_task8_baseline.py tests/decision/test_six_month_routing_holdout.py -q
```

Expected: PASS。

- [ ] **Step 4: 运行仓库护栏**

Run:
```bat
python tools/tool_registry.py --check && python tools/rule_status_scan.py --check && git diff --check
```

Expected: 全部退出码 0。

- [ ] **Step 5: 最终范围审查**

确认未修改 `run_pipeline()`、`DEFAULT_RUNNER_REGISTRY`、static coverage、生产权重、runner、规则、评分公式和门槛；所有新增评估制品分类均为 `historical_blind_candidate`；高风险无 A 级双审记录的可评分数为 0；无旧制品被覆盖。
