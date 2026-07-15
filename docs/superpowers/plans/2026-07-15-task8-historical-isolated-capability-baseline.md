# Task 8 Historical Isolated Capability Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Execute this plan inline with explicit checkpoints; do not create commits because the user prohibited commits without separate authorization. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 使用 Tasks 1—7 已冻结的十任务目录、六来源 runner 与 Task 7 ExecutableRule，在严格先冻结、后揭示的两个独立进程中生成 2026-07-15 历史隔离能力基线，并只读核验既有 prospective prediction-first 采集链。

**Architecture:** 阶段 A 只从 `cases/shuru-input.md`、十任务目录和 Task 7 规则内容摘要构建六来源完整矩阵，在 `.task8-artifacts/` 写冻结制品并调用 `verify_frozen_run()`。阶段 B 作为新的独立进程先复验 freeze hash，再读取既有人工标签和已审核 manifest，重建六来源 routes、正式评分配置，并复用 `school_capability_baseline.py` 的 score/report 契约；最终聚合器仅从已验证的正式评分制品生成日期化 JSON/Markdown，不改变评分公式、门槛、runner、规则、路由或版本。

**Tech Stack:** Python 3、stdlib JSON/hashlib/pathlib、PyYAML、pytest、现有 `engine.evaluation` 与 `tools.school_capability_*` 模块。

## Global Constraints

- 分类固定为 `historical_blind_candidate`；不得写成 prospective、E3 或生产证据。
- 六来源固定为 `ziping`、`ditiansui`、`duan`、`ren`、`gao`、`yang`。
- 十任务必须由 `mapping/school-capability-task-catalog-v1.yaml` 加载并按批准 ID 筛选，不得手写任务定义。
- Task 7 规则身份必须由 `theory/production/claim-rules-v1.yaml` 文件内容 SHA-256 确定性派生。
- 阶段 A 不读取 labels、feedback、报告结论或旧 scores；阶段 B 必须在新进程中先复验冻结制品才可揭示标签。
- 只使用 `META/school-capability-historical-labels-2026-07-14.json` 已有人工标签；不得新增、修改或反推标签与负例。
- 不覆盖任何 2026-07-14 制品；最终仅创建 `META/six-month-capability-baseline-2026-07-15.json` 与 `.md`。
- 不修改 runner 命理逻辑、claim rules、评分/后验/gate 阈值、高风险成本、生产权重、L1 默认路由、报告入口、项目状态、状态文档或版本。
- 不运行 Task 9 learned/static 留出竞争；不创建 Git commit；不把 `.task8-artifacts/` 纳入归档。

---

### Task 1: 只读事实源、入口与回归预检

**Files:**
- Read: `README.md`
- Read: `AGENTS.md`
- Read: `META/project-state.json`
- Read: `STATUS.md`
- Read: `tools/README.md`
- Read: `engine/README.md`
- Read: `engine/contracts/00-OVERVIEW.md`
- Read: `plans/upgrade-guides/6-month-execution-plan-2026-07.md:377-412`
- Read: `META/school-capability-baseline-2026-07-14.md`
- Read: `META/school-capability-historical-batch-final-2026-07-14.json`
- Read: `META/school-capability-historical-labels-2026-07-14.json`
- Read: `META/school-capability-reviewed-manifest-2026-07-14.json`
- Read: `mapping/school-capability-task-catalog-v1.yaml`
- Read: `theory/production/claim-rules-v1.yaml`

**Interfaces:**
- Consumes: 仓库当前事实源、CLI 与测试。
- Produces: 是否允许进入数据生成的预检结论。

- [ ] **Step 1: 检查四个正式评估子命令帮助**

Run:
```bat
python -m tools.school_capability_baseline audit --help && python -m tools.school_capability_baseline freeze --help && python -m tools.school_capability_baseline score --help && python -m tools.school_capability_baseline report --help
```

Expected: 四个命令退出码均为 0。

- [ ] **Step 2: 检查两个 prospective 隔离子命令帮助**

Run:
```bat
python -m tools.school_capability_dataset prospective-intake --help && python -m tools.school_capability_dataset prepare-blind --help
```

Expected: 两个命令退出码均为 0。

- [ ] **Step 3: 跑 Claims 与 evaluation 预检**

Run:
```bat
python -m pytest tests/claims tests/evaluation -q
```

Expected: PASS；如失败，停止后续数据生成并只报告实际失败。

### Task 2: 补充最小可复现 Task 8 编排器（仅在现有 CLI schema 无法直接承接历史批次时）

**Files:**
- Create if necessary: `tools/school_capability_task8.py` — 只负责阶段 A、阶段 B 输入适配和最终日期化摘要编排。
- Modify if necessary: `tests/evaluation/test_school_capability_batch.py` — 回归两阶段读取边界、六来源 manifest、失败分类与确定性。
- Modify if necessary: `tests/evaluation/test_cli.py` — 回归 Task 8 编排 CLI 参数和安全输出边界。

**Interfaces:**
- Consumes: `load_task_catalog(Path) -> list[BlindTask]`、`build_historical_blind_artifacts(...) -> dict`、`verify_frozen_run(FrozenBlindRun) -> None`、`build_historical_reviewed_manifest(...) -> dict`、正式 baseline CLI。
- Produces: `freeze`、`reveal-score`、`finalize` 三个可重复命令；阶段 A 代码路径不接受 label/feedback/report/scores 参数。

- [ ] **Step 1: 证明现有 CLI 输入不兼容点**

检查正式 freeze 需要 JSON outputs/tasks/rule snapshot，而现有历史批次函数从 Markdown 输入生成；正式 score 需要 CLI tasks、六来源 reviewed manifest、bound labels、evaluation config。记录该 schema gap，禁止手工拼不可复现最终结果。

- [ ] **Step 2: 写失败测试**

测试至少断言：阶段 A 参数无 labels；十任务来自 catalog；规则 ID 含规则文件 SHA-256；64 个去重命主形成 `64 × 10 × 6 = 3840` 唯一输出；阶段 B 六来源 route 完整；既有标签字段逐项不变；高风险 B/C 标签不进入可评分 grid 并记录 `label_quality`；最终摘要含所有规定字段和失败分类。

- [ ] **Step 3: 运行失败测试**

Run:
```bat
python -m pytest tests/evaluation/test_school_capability_batch.py tests/evaluation/test_cli.py -q
```

Expected: 新增测试在最小编排实现前 FAIL。

- [ ] **Step 4: 实现最小编排**

实现仅做 schema 适配、身份绑定、完整性校验、失败归类和报告聚合；实际 score、posterior、四组实验、增量收益、gate evidence 必须调用现有正式评估实现，不复制或修改算法。

- [ ] **Step 5: 运行专项测试**

Run:
```bat
python -m pytest tests/evaluation/test_school_capability_batch.py tests/evaluation/test_cli.py tests/evaluation/test_dataset.py -q
```

Expected: PASS。

### Task 3: 阶段 A — 独立进程冻结六来源历史预测

**Files:**
- Create temporary: `.task8-artifacts/stage-a-historical-batch.json`
- Create temporary: `.task8-artifacts/stage-a-outputs.json`
- Create temporary: `.task8-artifacts/stage-a-cli-tasks.json`
- Create temporary: `.task8-artifacts/stage-a-rule-snapshot.json`
- Create temporary: `.task8-artifacts/stage-a-frozen-run.json`
- Read: `cases/shuru-input.md`

**Interfaces:**
- Consumes: 仅 case ID、性别、四柱、出生时间、大运、十任务目录、规则快照内容。
- Produces: 六来源 × 十任务完整冻结 grid、freeze hash、冻结时间与 identity provenance。

- [ ] **Step 1: 生成阶段 A 中间制品**

Run the Task 8 stage-A command with output root `.task8-artifacts/` and frozen timestamp equal to actual execution UTC time.

Expected: 保留既有一条重复盘去重结果，case identity 与 2026-07-14 历史 batch 一致。

- [ ] **Step 2: 使用正式 freeze CLI 冻结 outputs**

Run:
```bat
python -m tools.school_capability_baseline freeze --outputs .task8-artifacts/stage-a-outputs.json --tasks .task8-artifacts/stage-a-cli-tasks.json --rule-snapshot .task8-artifacts/stage-a-rule-snapshot.json --out .task8-artifacts/stage-a-frozen-run.json
```

Expected: 输出路径安全检查通过，冻结制品不写入 `META/`。

- [ ] **Step 3: 校验矩阵与 freeze hash 并退出进程**

调用 `FrozenBlindRun.from_dict()` 与 `verify_frozen_run()`；断言每个 case/task/school 恰好一条三态输出、无 labels/feedback/report/known facts 字段、规则与任务 identity 均含 SHA-256。

### Task 4: 阶段 B — 独立进程揭示既有标签并正式评分

**Files:**
- Create temporary: `.task8-artifacts/stage-b-reviewed-manifest.json`
- Create temporary: `.task8-artifacts/stage-b-bound-labels.json`
- Create temporary: `.task8-artifacts/stage-b-evaluation-config.json`
- Create temporary: `.task8-artifacts/stage-b-scores.json`
- Create temporary: `.task8-artifacts/stage-b-formal-report.md`
- Read after freeze verification: `META/school-capability-historical-labels-2026-07-14.json`
- Read after freeze verification: `META/school-capability-reviewed-manifest-2026-07-14.json`

**Interfaces:**
- Consumes: 已复验的阶段 A frozen run、与当前 case/task identity 相交的既有人工标签、旧 manifest 的人工 review provenance。
- Produces: 六来源 reviewed manifest、bound labels、正式 evaluation config、scores artifact、正式报告。

- [ ] **Step 1: 新进程先复验阶段 A hash**

在打开 labels 和旧 manifest 前调用 `verify_frozen_run()`；若 hash 不一致立即 STOP。

- [ ] **Step 2: 过滤而不修改既有标签**

只保留冻结 grid 中十任务的既有标签；逐字段保持 `label`、`source`、`observed_at`、`reviewer`、`confidence_grade`、`conflict_state`、`quantifiable`。高风险标签不满足 A 级与双审时不进入评分 grid，记录 `label_quality`，不得降级门槛。

- [ ] **Step 3: 重建六来源 manifest 与 config**

每个 eligible case/task 为六来源各生成一条 route；所有 frozen outputs 必须与 manifest routes 完全一致。未被批准标签覆盖的 case/task 不进入正式 eligible grid，但三态与失败分类仍在最终基线保留。

- [ ] **Step 4: 运行正式 score CLI**

Run:
```bat
python -m tools.school_capability_baseline score --frozen-run .task8-artifacts/stage-a-frozen-run.json --manifest .task8-artifacts/stage-b-reviewed-manifest.json --labels .task8-artifacts/stage-b-bound-labels.json --tasks .task8-artifacts/stage-a-cli-tasks.json --rule-snapshot .task8-artifacts/stage-a-rule-snapshot.json --evaluation-config .task8-artifacts/stage-b-evaluation-config.json --out .task8-artifacts/stage-b-scores.json
```

Expected: 正式 CLI 重算 task/rule/manifest digest、四组实验、后验、增量收益、高风险审计和 gate evidence。

- [ ] **Step 5: 运行正式 report CLI**

Run:
```bat
python -m tools.school_capability_baseline report --scores .task8-artifacts/stage-b-scores.json --manifest .task8-artifacts/stage-b-reviewed-manifest.json --out .task8-artifacts/stage-b-formal-report.md
```

Expected: scores artifact digest 与 manifest digest 均通过复验。

### Task 5: 只读验证旧 prospective prediction-first 链

**Files:**
- Read: `META/school-capability-prospective-intake-2026-07-13.json`
- Read: `META/school-capability-blind-bundle-2026-07-13/`
- Read: `META/school-capability-rule-snapshot-prospective-v1.json`

**Interfaces:**
- Consumes: 旧 intake、bundle manifest 和白名单文件。
- Produces: schema/hash/禁入字段/旧规则身份验证状态；不创建新 prospective case。

- [ ] **Step 1: 校验 intake schema 与唯一命主**

复用 dataset validator 的 schema 规则，确认任务、subject hash 与 intake 文件 identity 一致。

- [ ] **Step 2: 校验 bundle 白名单与内容 hash**

确认实际文件集合严格等于 manifest 白名单，逐文件 SHA-256 和 bundle hash 一致，且无 symlink。

- [ ] **Step 3: 扫描禁入信息**

扫描 bundle 文件名、JSON key/value，确认不含 feedback、labels、report、known facts。

- [ ] **Step 4: 保留旧规则快照身份**

确认旧 bundle 的规则快照仍指向 `l2-engine-rules-prospective-v1`，不将其静默改写为 Task 7 新规则。记录“本轮无新增前瞻样本”及下一批新目录命令模板。

### Task 6: 生成日期化最终 JSON 与 Markdown

**Files:**
- Create: `META/six-month-capability-baseline-2026-07-15.json`
- Create: `META/six-month-capability-baseline-2026-07-15.md`

**Interfaces:**
- Consumes: 阶段 A frozen run、阶段 B 正式 scores/manifest、prospective 只读审计结果、2026-07-14 历史基线。
- Produces: 用户要求的 Task 8 唯一归档制品。

- [ ] **Step 1: 生成 JSON**

JSON 至少包含：`schema_version`、`generated_at`、`classification`、`task_catalog_identity`、`rule_snapshot_identity`、`freeze_hash`、`artifact_digest`、`case_count`、`labelled_case_count`、`label_count`、`expected_schools`、`task_ids`、`state_counts`、`scores`、`posteriors`、`incremental_gains`、`gate_status`、`gate_reasons`、`failure_classification_counts`、`provenance`、`prospective_status`。`artifact_digest` 按移除自身后的 canonical JSON 重算。

- [ ] **Step 2: 生成 Markdown**

分别陈述 artifact validity、capability evidence、routing readiness、prospective evidence；展示六来源 × 十任务三态覆盖、非空后验与区间、四组增量、高风险假阳性/不可评估项、失败分类、与 2026-07-14 可比变化、标签/输入限制、无新增真实 prospective 样本和是否可进入 Task 9。不得把 coverage/claim/rule 数增加称作准确率提升。

- [ ] **Step 3: 安全归档**

先在 `.task8-artifacts/` 生成和完整校验，再复制只读最终制品到 `META/`；不绕过 `school_capability_baseline.py` 的安全输出检查。

### Task 7: 确定性、完整性与仓库护栏验证

**Files:**
- Verify: `.task8-artifacts/`
- Verify: `META/six-month-capability-baseline-2026-07-15.json`
- Verify: `META/six-month-capability-baseline-2026-07-15.md`

**Interfaces:**
- Consumes: 所有本轮制品。
- Produces: 可报告的实际验证证据。

- [ ] **Step 1: 重验 freeze hash 与最终 digest**

调用 `verify_frozen_run()`，并按 canonical JSON 重算最终 `artifact_digest`。

- [ ] **Step 2: 重跑同版本链验证确定性**

使用相同任务、规则、case 与固定 frozen/evaluated 时间重跑至第二临时目录；断言 frozen outputs、freeze hash、scores、posteriors、incremental gains 和 gate evidence 一致。

- [ ] **Step 3: 扫描 evidence classification**

断言最终 JSON/Markdown 的 classification 为 historical blind candidate，明确历史反馈先于新 runner 重冻；不得出现将本批称为 prospective/E3 的陈述。

- [ ] **Step 4: 跑相关测试**

Run:
```bat
python -m pytest tests/claims tests/evaluation -q
```

Expected: PASS。

- [ ] **Step 5: 若有工具改造，跑专项测试**

Run:
```bat
python -m pytest tests/evaluation/test_school_capability_batch.py tests/evaluation/test_cli.py tests/evaluation/test_dataset.py -q
```

Expected: PASS。

- [ ] **Step 6: 跑仓库护栏**

Run:
```bat
python tools/tool_registry.py --check && python tools/rule_status_scan.py --check && git diff --check
```

Expected: 全部退出码 0。

- [ ] **Step 7: 时间允许时跑全量测试**

Run:
```bat
python -m pytest tests -q
```

Expected: PASS；若未运行，完成报告必须明确写“未运行”，不得声称通过。

### Task 8: 完成前范围审查与结果汇报

**Files:**
- Inspect: `git diff -- META/six-month-capability-baseline-2026-07-15.json META/six-month-capability-baseline-2026-07-15.md tools/ tests/evaluation/`

**Interfaces:**
- Consumes: Git diff、命令日志、最终制品。
- Produces: 最终 Task 8 完成报告。

- [ ] **Step 1: 审查范围红线**

确认未修改 runner 命理逻辑、规则快照、评分公式、门槛、权重、路由、报告入口、版本、项目状态与历史制品；未创建 prospective case；未运行 Task 9；未创建 commit。

- [ ] **Step 2: 审查数据纪律**

确认 freeze 进程未读 labels/feedback/report/scores；标签只在后续独立进程读取；六来源和十任务完整；高风险不合格标签保持不可评分；未删除异常样本、unsupported、abstain 或 miss；重复盘未重复计数。

- [ ] **Step 3: 汇报实际结果**

列出生成文件、必要工具/测试修改、实际命令与退出结果、freeze hash、artifact digest、artifact/capability/routing/prospective 四类结论、gate 状态与原因、失败分类计数。仅给出建议暂存命令，不实际执行 `git add` 或 commit。
