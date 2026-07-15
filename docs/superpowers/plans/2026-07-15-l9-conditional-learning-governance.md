# L9 Conditional Learning Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将反馈学习从 rule/family 全局线性微调升级为六维条件身份上的离线、分级、可审计、可回滚学习，并把获批的适用性后验写入 L1 可消费的独立能力快照。

**Architecture:** 在 `engine/learning/` 建立独立 L9 子系统：冻结契约负责信号与决策，纯函数治理器负责 N_eff 分级，文件仓储负责 append-only 信号、不可变快照和回滚，服务层负责编排且不触碰历史 run snapshot 或静态权重。L1 继续通过现有 `CapabilityRegistry.from_snapshot()` 读取标准 `posteriors` 快照，因此 L9 只生成兼容快照，不让 decision 层反向依赖 learning 层。

**Tech Stack:** Python 3、frozen dataclass、标准库 JSON/SHA-256/原子文件替换、PyYAML、pytest。

## Global Constraints

- 六维条件身份固定为 `school_id × task_id × chart_prototype_id × claim_type × time_horizon × evidence_completeness_band`。
- `attributable=false` 时 verdict 必须治理为 `no_data`，不得产生或分摊更新量。
- 阈值只从 `engine/conditional-learning.yaml` 注入，执行器不得硬编码样本阈值。
- 低样本只记录；中样本只建议/更新 applicability；成熟样本规则先验更新必须先人工批准。
- 高风险任务来自 `mapping/school-capability-task-catalog-v1.yaml` 的 `high_risk`，任意 N_eff 均要求人工审批。
- 不写 `engine/expert-weights.yaml`、`engine/domain-weights.yaml`、真实 `theory/` 规则或历史 run snapshot。
- 所有应用更新必须生成内容寻址 snapshot_ref，支持精确回滚并保留审计链。
- 正式入口保持离线、显式调用；不切换生产路由默认模式。

---

## File Structure

- Create `engine/learning/__init__.py`: L9 公共接口导出。
- Create `engine/learning/models.py`: 六维身份、条件化信号、治理阈值、学习决策和人工裁决项冻结契约。
- Create `engine/learning/governance.py`: 纯函数 N_eff 分级、Beta 建议后验、人工审查原因判定。
- Create `engine/learning/repository.py`: 能力快照加载/冻结/原子写入、append-only 审计、回滚实现。
- Create `engine/learning/service.py`: 信号处理、任务风险查找、审批应用、L1 兼容快照构建编排。
- Create `engine/conditional-learning.yaml`: 唯一治理阈值和变化幅度配置事实源。
- Create `tools/conditional_learning.py`: 离线 `decide/apply/rollback` CLI adapter。
- Create `tests/learning/test_models.py`: 契约及不可归因护栏。
- Create `tests/learning/test_governance.py`: 低/中/成熟/高风险分级测试。
- Create `tests/learning/test_repository.py`: 快照、原子性、回滚和历史文件字节不变测试。
- Create `tests/learning/test_service.py`: L8→L9→L1 registry 闭环与静态权重不变测试。
- Modify `engine/README.md`: 登记 L9 子系统和配置。
- Modify `tools/README.md`: 登记离线治理 CLI 边界。
- Modify `engine/contracts/00-OVERVIEW.md`: 补充条件化学习闭环及不可变治理边界。
- Modify `META/project-state.json`: 只记录 L9 落地状态和入口，不写易漂移统计。

### Task 1: 冻结条件化学习契约

**Files:**
- Create: `engine/learning/models.py`
- Create: `engine/learning/__init__.py`
- Test: `tests/learning/test_models.py`

**Interfaces:**
- Produces: `ConditionalIdentity`, `ConditionalLearningSignal`, `LearningThresholds`, `LearningDecision`, `ManualReviewItem`，均支持 `to_dict()` / `from_dict()`。

- [ ] **Step 1: Write the failing tests**

覆盖：六维字段任一为空即 `ValueError`；verdict 非 `hit/miss/partial/no_data` 即拒绝；`attributable=False` 且 verdict 非 `no_data` 即拒绝；序列化往返相等；映射字段冻结不可修改。

- [ ] **Step 2: Run tests to verify RED**

Run: `pytest tests/learning/test_models.py -q`
Expected: FAIL because `engine.learning.models` does not exist.

- [ ] **Step 3: Implement minimal frozen contracts**

使用 `@dataclass(frozen=True)`；`ConditionalIdentity.key` 返回以 `|` 连接的稳定身份；`ConditionalLearningSignal.__post_init__()` 强制不可归因信号为 `no_data`；所有概率、质量和 N_eff 校验合法范围。

- [ ] **Step 4: Run tests to verify GREEN**

Run: `pytest tests/learning/test_models.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/learning tests/learning/test_models.py
git commit -m "feat: define conditional learning contracts"
```

### Task 2: 配置驱动的 N_eff 分级治理

**Files:**
- Create: `engine/conditional-learning.yaml`
- Create: `engine/learning/governance.py`
- Test: `tests/learning/test_governance.py`

**Interfaces:**
- Consumes: `ConditionalLearningSignal`, `CapabilityPosterior | None`, `LearningThresholds`, `is_high_risk`。
- Produces: `load_learning_thresholds(path) -> LearningThresholds`；`decide_learning_tier(...) -> LearningDecision`。

- [ ] **Step 1: Write failing tier tests**

用测试阈值 `medium_n_eff=5`、`mature_n_eff=20`：after N_eff 4.5 为 `record_only`；5 为 `adjust_applicability`；20 为 `adjust_rule_prior` 且待审批；高风险 50 仍待审批；partial 只增加配置权重；no_data 不增加 N_eff；单次 posterior delta 不超过配置上限。

- [ ] **Step 2: Run tests to verify RED**

Run: `pytest tests/learning/test_governance.py -q`
Expected: FAIL because governance functions do not exist.

- [ ] **Step 3: Implement pure governance functions**

以现有 posterior 反推伪计数 `hits=mean*n_eff`、`misses=(1-mean)*n_eff`，按 verdict 质量权重更新 Beta(1,1) 后验；tier 只由更新后 N_eff 与配置决定；成熟层和高风险层 `applied=False`、`requires_human_approval=True`；低样本 proposed_delta 为 0。

- [ ] **Step 4: Run tests to verify GREEN**

Run: `pytest tests/learning/test_governance.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/conditional-learning.yaml engine/learning/governance.py tests/learning/test_governance.py
git commit -m "feat: add tiered learning governance"
```

### Task 3: 不可变快照、审计与回滚仓储

**Files:**
- Create: `engine/learning/repository.py`
- Test: `tests/learning/test_repository.py`

**Interfaces:**
- Produces: `ConditionalLearningRepository(root)`；`record_signal()`；`freeze_snapshot()`；`apply_snapshot()`；`rollback(snapshot_ref)`；`load_active_snapshot()`。
- Snapshot schema: `conditional-capability-snapshot/v1`，包含标准 `posteriors`、`parent_snapshot_ref`、`decision_ids`、`created_at`、`content_hash`。

- [ ] **Step 1: Write failing repository tests**

覆盖：相同 canonical payload 得相同 hash；snapshot 文件创建后不覆写；active pointer 用原子替换；回滚恢复 parent 内容；不存在 snapshot 明确报错；运行服务前后给定历史 `.run.json` SHA-256 不变。

- [ ] **Step 2: Run tests to verify RED**

Run: `pytest tests/learning/test_repository.py -q`
Expected: FAIL because repository does not exist.

- [ ] **Step 3: Implement content-addressed repository**

仅在指定 L9 root 写 `signals.jsonl`、`decisions.jsonl`、`snapshots/<hash>.json`、`active.json`；canonical JSON 使用排序键和紧凑分隔符；已存在 snapshot 必须逐字节相同；写入经临时文件 `Path.replace()`；rollback 仅移动 active pointer，不删除历史。

- [ ] **Step 4: Run tests to verify GREEN**

Run: `pytest tests/learning/test_repository.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/learning/repository.py tests/learning/test_repository.py
git commit -m "feat: add immutable learning snapshots and rollback"
```

### Task 4: 条件化学习服务与 L1 回流

**Files:**
- Create: `engine/learning/service.py`
- Test: `tests/learning/test_service.py`

**Interfaces:**
- Consumes: 信号、task catalog、阈值配置、当前 capability snapshot、显式审批集合。
- Produces: `process_learning_signals(...) -> tuple[LearningDecision, ...]`；获批后生成 `CapabilityRegistry.from_snapshot()` 可直接加载的 `posteriors` 快照。

- [ ] **Step 1: Write failing end-to-end tests**

覆盖：中样本普通任务写 applicability posterior 后 L1 六维 query exact 命中；低样本 active snapshot 不变；成熟样本未审批不应用；审批后应用；高风险即使成熟且未审批也不应用；不可归因信号进入 manual review 且不分摊；规则先验决策只进入审计建议、不改 theory；静态权重文件测试前后字节一致。

- [ ] **Step 2: Run tests to verify RED**

Run: `pytest tests/learning/test_service.py -q`
Expected: FAIL because service does not exist.

- [ ] **Step 3: Implement orchestration**

从 task catalog 建 task_id→high_risk 映射；按 identity 聚合信号并顺序重算 posterior；`adjust_applicability` 可在非高风险中样本自动应用；`adjust_rule_prior` 仅在 approval id 明确存在时应用到独立快照的审计字段，绝不写 theory；人工队列记录无法归因、反馈矛盾、漂移、大变化和高风险。

- [ ] **Step 4: Run tests to verify GREEN**

Run: `pytest tests/learning/test_service.py tests/decision/test_capability_registry.py tests/decision/test_learnable_routing.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add engine/learning/service.py tests/learning/test_service.py
git commit -m "feat: close conditional learning loop into l1 registry"
```

### Task 5: 离线治理 CLI 与文档事实源同步

**Files:**
- Create: `tools/conditional_learning.py`
- Modify: `tools/README.md`
- Modify: `engine/README.md`
- Modify: `engine/contracts/00-OVERVIEW.md`
- Modify: `META/project-state.json`
- Test: `tests/learning/test_cli.py`

**Interfaces:**
- Produces CLI: `python -m tools.conditional_learning decide ...`、`apply --approval-file ...`、`rollback --snapshot-ref ...`；所有写命令支持 `--dry-run`。

- [ ] **Step 1: Write failing CLI tests**

覆盖：decide dry-run 不落盘；apply 无审批拒绝成熟/高风险更新；合法审批生成 snapshot；rollback 恢复父快照；错误输入返回非零且 stderr 可理解。

- [ ] **Step 2: Run tests to verify RED**

Run: `pytest tests/learning/test_cli.py -q`
Expected: FAIL because CLI does not exist.

- [ ] **Step 3: Implement CLI and update documentation**

CLI 只做 JSON 文件输入输出和 service adapter；文档明确旧 `update_confidence()`/`update_school_weights()` 为 legacy，不再作为 L9 生产学习入口；项目状态增加 `l9_conditional_learning_governance: landed_offline_staged` 和工具入口，不写 N_eff。

- [ ] **Step 4: Run targeted and metadata tests**

Run: `pytest tests/learning tests/test_project_metadata.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tools/conditional_learning.py tools/README.md engine/README.md engine/contracts/00-OVERVIEW.md META/project-state.json tests/learning/test_cli.py
git commit -m "feat: expose governed conditional learning workflow"
```

### Task 6: 验收门禁与回归

**Files:**
- Modify only if tests expose defects in files listed above.

**Interfaces:**
- Produces: 可重复的专项与全量验证证据。

- [ ] **Step 1: Run L9 and upstream dependency tests**

Run: `pytest tests/learning tests/evaluation tests/decision/test_capability_registry.py tests/decision/test_learnable_routing.py -q`
Expected: PASS.

- [ ] **Step 2: Run legacy learning compatibility tests**

Run: `pytest tests/test_phase_a_minimal_learning_loop.py -q`
Expected: PASS; legacy API remains compatible but is not the new governed entrypoint.

- [ ] **Step 3: Run repository governance checks**

Run: `python tools/tool_registry.py --check && python tools/rule_status_scan.py --check`
Expected: both exit 0; no tool-index drift and no illegal rule mutation.

- [ ] **Step 4: Run full regression**

Run: `pytest tests/ -q`
Expected: PASS; if pre-existing unrelated failures exist, record exact failing tests and prove L9 subset remains green.

- [ ] **Step 5: Review git diff**

Run: `git diff --check && git status --short`
Expected: no whitespace errors; changed paths limited to planned L9 implementation/tests/docs/state.

## Self-Review

- Spec coverage: T1/T2 cover six-dimensional attribution and no-distribution guard; T3 covers immutable snapshots/rollback; T4 covers tiering, high-risk approval and L1 registry feedback; T5 covers operator workflow and facts; T6 covers evaluation and regression gates.
- Placeholder scan: no TBD/TODO/implement-later placeholders are present.
- Type consistency: all downstream tasks consume the exact model, governance and repository names defined by earlier tasks; capability output preserves the existing top-level `posteriors` array required by `CapabilityRegistry.from_snapshot()`.
