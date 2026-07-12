# 评估数据地基与真实标注回流 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立可审计、可冻结、可重放的真实评估数据包，先用 5 案证明链路，再扩展到 ≥30 个经人工复核的案例，并由现有评估框架产出诚实的 GO/HOLD 能力基线。

**Architecture:** 不修改推理引擎和现有评估核心；新增一个 stdlib-only 的数据集构建/校验工具，把原始反馈事实、案例污染分级、任务标签、reviewed manifest 与评估输入产物显式分离。自动化只做确定性抽取、契约校验和产物汇总；案例清洁性、语义标签和 reviewer 身份必须经过人工裁决，预测冻结后才将标签绑定 `freeze_hash`。

**Tech Stack:** Python 3、标准库 `json/pathlib/re/hashlib/argparse`、现有 `engine.evaluation`、pytest、JSON/JSONL、Markdown。

## Global Constraints

- 本单元只做数据与标注，不修改 `engine/` 推理逻辑、生产规则或生产权重。
- 标签只依据命主真实经历、第三方事实或档案，不得从旧报告、人工 school-claims 或系统预测反向生成。
- 无法证明清洁的案例默认 `development_only`；不得用污染案例凑满 30。
- 不知道不是负例；无法可靠映射则不生成标签并记 `no_data`。
- 标签记录必须包含 `source / observed_at / confidence_grade / quantifiable / conflict_state / reviewer`。
- runner 输出与标签物理隔离；冻结前不得读取标签。
- 指导 01 未就绪时，只允许 `prototype_provisional: true` 的粗粒度原型；但现有 manifest 严格契约不接受该额外字段，因此阶段 03 首版用 `chart_prototype_id=provisional_unclassified` 表达，不扩大契约。
- CLI 只读评估边界保持不变；写入 `cases/` 与 `META/` 的数据构建命令必须支持 `--dry-run`。
- 允许最终结论为 HOLD；不得降低 `N_eff < 5`、高风险或完整 gate 门槛来制造 GO。
- 用户工作区已有非本任务改动，不覆盖、不回退、不纳入提交。

---

## File Map

- Create: `tools/school_capability_dataset.py` — stdlib-only 数据盘点、候选抽取、人工裁决合并、标签/manifest/评估配置构建与 validate CLI；不运行预测引擎。
- Create: `tests/evaluation/test_dataset.py` — 数据工具的契约、污染默认、标签映射、泄漏隔离与 dry-run 测试。
- Create: `tests/fixtures/school_capability_dataset/` — 5 案最小合成夹具，覆盖 clean / contaminated / no_data / conflict / high-risk。
- Create: `META/school-capability-case-inventory.json` — 全 133 个当前正式 case 的机器可读分级清单。
- Create: `META/school-capability-review-decisions-2026-07-12.json` — 人工裁决输入；每案记录 provenance、污染结论、reviewer 与理由。
- Create: `META/school-capability-reviewed-manifest-2026-07-12.json` — reviewed manifest。
- Create: `META/school-capability-labels-unbound-2026-07-12.json` — 冻结前标签包；不得交给 runner。
- Create: `META/school-capability-blind-outputs-2026-07-12.json` — 受限任务的引擎盲输出；必须在标签 reveal 前生成。
- Create: `META/school-capability-rule-snapshot-2026-07-12.json` — 本轮规则来源快照。
- Create: `META/school-capability-tasks-2026-07-12.json` — 从 YAML 目录人工核对后固化的 CLI JSON 任务子集。
- Create: `META/school-capability-evaluation-config-2026-07-12.json` — eligible grid、metadata、baseline 与 gate thresholds。
- Create: `META/school-capability-frozen-2026-07-12.json` — 冻结预测产物。
- Create: `META/school-capability-labels-2026-07-12.json` — 仅在冻结后绑定准确 `freeze_hash` 的 revealed labels。
- Create: `META/school-capability-scores-2026-07-12.json` — 现有 score CLI 产物。
- Create: `META/school-capability-baseline-2026-07-12.md` — 现有 report CLI 产物。
- Create: `META/school-capability-data-foundation-summary-2026-07-12.md` — 数量、覆盖、污染、HOLD/GO、风险和人工签署摘要。
- Modify: `tools/README.md` — 仅在工具稳定后登记 dataset 工具状态与边界。
- Modify: `plans/bazi-intelligence-platform-roadmap.md` — 只写实际门禁结果，不预写 GO。

## As-Built Baseline

2026-07-12 已运行现有 audit：133 个 case 中 `development_only=62`、`not_scorable=31`、`manual_review=40`；90 个被启发式判定具有量化反馈。40 个 `manual_review` 只是“未发现显式污染”，不是已证明清洁。大量 RF case 来源于先有真实经历、后生成系统报告的历史回填流程，因此不能自动提升为历史盲测；若人工 provenance 审查不能证明预测先于反馈，则必须标记 `development_only`。这意味着“≥30 真实标签”与“≥30 清洁盲测案例”是两个不同门槛，后者可能诚实 HOLD。

---

### Task 1: 锁定数据集契约与污染默认

**Files:**
- Create: `tests/evaluation/test_dataset.py`
- Create: `tests/fixtures/school_capability_dataset/cases/C-CLEAN-001/input.md`
- Create: `tests/fixtures/school_capability_dataset/cases/C-CLEAN-001/feedback.md`
- Create: `tests/fixtures/school_capability_dataset/review-decisions.json`
- Create: `tools/school_capability_dataset.py`

**Interfaces:**
- Consumes: `engine.evaluation.case_audit.audit_cases(cases_dir: Path, reports_dir: Path)`。
- Produces: `build_inventory(cases_dir: Path, reports_dir: Path, review_decisions: dict) -> dict`；schema `school-capability-case-inventory/v1`。

- [ ] **Step 1: 写失败测试：无人工清洁证据不得进入 blind**

```python
from pathlib import Path

from tools.school_capability_dataset import build_inventory


def test_inventory_defaults_manual_review_to_development_only() -> None:
    root = Path("tests/fixtures/school_capability_dataset")
    inventory = build_inventory(root / "cases", root / "reports", {"schema_version": "school-capability-review-decisions/v1", "records": []})
    row = next(item for item in inventory["records"] if item["case_id"] == "C-CLEAN-001")
    assert row["classification"] == "development_only"
    assert "human_clean_review_missing" in row["contamination_evidence"]
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `pytest tests/evaluation/test_dataset.py::test_inventory_defaults_manual_review_to_development_only -v`

Expected: FAIL，提示 `tools.school_capability_dataset` 不存在。

- [ ] **Step 3: 实现最小 inventory 映射**

实现 `build_inventory()`，严格输出：`case_id / birth_info_complete / feedback_present / feedback_grade / development_contaminated / contamination_evidence / classification / notes / reviewed_by / reviewed_at`。只有人工 decision 同时满足 `classification in {historical_blind, prospective}`、非空 reviewer、非空 provenance evidence 时才允许清洁分类；其余 `manual_review` 降为 `development_only`。

- [ ] **Step 4: 增加污染优先级测试**

```python
def test_explicit_contamination_cannot_be_overridden_by_review() -> None:
    root = Path("tests/fixtures/school_capability_dataset")
    decisions = {"schema_version": "school-capability-review-decisions/v1", "records": [{
        "case_id": "C-CONTAMINATED-001", "classification": "historical_blind",
        "reviewed_by": "human-a", "reviewed_at": "2026-07-12", "provenance_evidence": ["claimed clean"],
    }]}
    row = next(item for item in build_inventory(root / "cases", root / "reports", decisions)["records"] if item["case_id"] == "C-CONTAMINATED-001")
    assert row["classification"] == "development_only"
```

- [ ] **Step 5: 运行测试**

Run: `pytest tests/evaluation/test_dataset.py -v`

Expected: PASS。

- [ ] **Step 6: 提交**

```bat
git add tools/school_capability_dataset.py tests/evaluation/test_dataset.py tests/fixtures/school_capability_dataset
git commit -m "feat(evaluation): add conservative case inventory builder"
```

### Task 2: 建立事实观察到任务标签的最小映射器

**Files:**
- Modify: `tools/school_capability_dataset.py`
- Modify: `tests/evaluation/test_dataset.py`
- Create: `tests/fixtures/school_capability_dataset/observations.jsonl`

**Interfaces:**
- Consumes: 人工核对过的 observation records，不直接消费旧报告断语。
- Produces: `build_unbound_labels(observations: list[dict], task_catalog: dict, reviewer: str) -> dict`；schema `school-capability-labels-unbound/v1`。

- [ ] **Step 1: 写失败测试：事实字段齐全才能形成标签**

```python
def test_build_unbound_labels_requires_six_metadata_fields() -> None:
    observations = [{
        "case_id": "C-CLEAN-001", "task_id": "career.role_change", "label": "occurred",
        "source": "feedback.md:12", "observed_at": "2023-01-01", "confidence_grade": "A",
        "quantifiable": True, "conflict_state": "none", "reviewer": "human-a",
    }]
    labels = build_unbound_labels(observations, _task_catalog())
    assert labels["labels"][0]["label"] == "occurred"
```

- [ ] **Step 2: 写失败测试：未知不得转成负例**

```python
def test_unknown_observation_is_omitted_not_negative() -> None:
    observations = [{
        "case_id": "C-CLEAN-001", "task_id": "wealth.debt", "label": None,
        "source": "feedback.md:13", "observed_at": "2026-07-12", "confidence_grade": "B",
        "quantifiable": False, "conflict_state": "none", "reviewer": "human-a",
        "disposition": "no_data",
    }]
    assert build_unbound_labels(observations, _task_catalog())["labels"] == []
```

- [ ] **Step 3: 实现严格校验与最小映射**

只支持现有四种评分协议的 schema 值；验证 task_id、label_schema、reviewer、source、日期、冲突状态。`no_data` 忽略；`conflicting_sources` 保留但默认 `quantifiable=false`；高风险标签要求 `confidence_grade=A` 和非空 `secondary_reviewed_by`，否则拒绝。

- [ ] **Step 4: 测试高风险双审**

```python
def test_high_risk_label_requires_secondary_human_review() -> None:
    observation = _valid_observation(task_id="wealth.debt", label="occurred")
    with pytest.raises(ValueError, match="secondary_reviewed_by"):
        build_unbound_labels([observation], _task_catalog())
```

- [ ] **Step 5: 运行测试**

Run: `pytest tests/evaluation/test_dataset.py -v`

Expected: PASS。

- [ ] **Step 6: 提交**

```bat
git add tools/school_capability_dataset.py tests/evaluation/test_dataset.py tests/fixtures/school_capability_dataset/observations.jsonl
git commit -m "feat(evaluation): validate task-aligned feedback labels"
```

### Task 3: 构建 reviewed manifest 与评估配置，不扩张现有 CLI

**Files:**
- Modify: `tools/school_capability_dataset.py`
- Modify: `tests/evaluation/test_dataset.py`

**Interfaces:**
- Produces: `build_reviewed_manifest(inventory: dict, labels: dict, expected_schools: list[str], reviewed_by: str) -> dict`。
- Produces: `build_evaluation_config(manifest: dict, labels: dict, evaluated_at: str) -> dict`。

- [ ] **Step 1: 写失败测试：只有清洁且有标签的 case 可进 grid**

```python
def test_manifest_excludes_development_and_unlabelled_cases() -> None:
    manifest = build_reviewed_manifest(_inventory(), _labels(), ["ziping"], "human-a")
    assert [row["case_id"] for row in manifest["records"] if row["eligibility"] == "historical_blind_candidate"] == ["C-CLEAN-001"]
```

- [ ] **Step 2: 实现 manifest 构建**

复用现有 exact schema。每个标签 × expected school 生成 route；`chart_prototype_id="provisional_unclassified"`，`claim_type/time_horizon` 来自 task catalog，`evidence_completeness_band` 由 birth/feedback 字段确定。development_only 记录保留在 manifest 盘点中但 routes 为空。

- [ ] **Step 3: 写失败测试：配置与 manifest routes 精确一致**

```python
def test_evaluation_config_grid_matches_manifest_routes() -> None:
    config = build_evaluation_config(_manifest(), _labels(), "2026-07-12T00:00:00Z")
    assert config["eligible_case_tasks"] == [["C-CLEAN-001", "career.role_change"]]
    assert set(config["gate_thresholds"]) == {"coverage_complete", "calibration_min_samples", "calibration_max_error", "high_risk_min_utility"}
```

- [ ] **Step 4: 实现配置构建**

门槛固定复用评估框架安全值；score weight 按标签可信度映射 `A=1 / B=0.5 / C=0`，不得使用其他值。baseline prevalence 仅从 development baseline 或显式人工配置读取，不从盲测标签计算。

- [ ] **Step 5: 运行 dataset 与现有 CLI 测试**

Run: `pytest tests/evaluation/test_dataset.py tests/evaluation/test_cli.py -v`

Expected: PASS。

- [ ] **Step 6: 提交**

```bat
git add tools/school_capability_dataset.py tests/evaluation/test_dataset.py
git commit -m "feat(evaluation): build reviewed manifest and score config"
```

### Task 4: 增加 CLI、dry-run 与数据集自检

**Files:**
- Modify: `tools/school_capability_dataset.py`
- Modify: `tests/evaluation/test_dataset.py`
- Modify: `tools/README.md`

**Interfaces:**
- CLI: `python -m tools.school_capability_dataset inventory|labels|manifest|validate`。
- `validate` 返回 0 表示契约一致；返回 2 表示 HOLD 但产物合法；非法数据返回非零并输出原因。

- [ ] **Step 1: 写 CLI dry-run 失败测试**

```python
def test_inventory_dry_run_does_not_write_target(tmp_path: Path) -> None:
    target = tmp_path / "inventory.json"
    result = _run_dataset("inventory", "--cases-dir", str(FIXTURE_CASES), "--reports-dir", str(FIXTURE_REPORTS), "--review-decisions", str(FIXTURE_DECISIONS), "--out", str(target), "--dry-run")
    assert result.returncode == 0
    assert not target.exists()
```

- [ ] **Step 2: 实现四个子命令与原子写入**

沿用现有 CLI 的 JSON 错误风格；不新增依赖。`validate` 检查：样本数、污染、标签字段、route/grid 一致、freeze 是否已绑定、内部 ID 不进入 Markdown、runner input 路径不包含 labels。

- [ ] **Step 3: 登记工具边界**

在 `tools/README.md` 将其列为 historical/data-governance 辅助入口，明确“不会生成预测、不更新 production、不自动批准 reviewer”。

- [ ] **Step 4: 运行测试**

Run: `pytest tests/evaluation/test_dataset.py tests/evaluation/test_cli.py -q`

Expected: 全部 PASS。

- [ ] **Step 5: 提交**

```bat
git add tools/school_capability_dataset.py tests/evaluation/test_dataset.py tools/README.md
git commit -m "feat(evaluation): add audited dataset preparation CLI"
```

### Task 5: 5 案 proof slice 与人工审查门

**Files:**
- Create: `META/school-capability-review-decisions-2026-07-12.json`
- Create: `META/school-capability-case-inventory.json`
- Create: `META/school-capability-labels-unbound-2026-07-12.json`
- Create: `META/school-capability-reviewed-manifest-2026-07-12.json`
- Create: `META/school-capability-tasks-2026-07-12.json`
- Create: `META/school-capability-evaluation-config-2026-07-12.json`

**Interfaces:**
- 人工输入：5 案 provenance 与标签语义签署。
- 机器输出：可校验 proof slice；未签署时必须 HOLD。

- [ ] **Step 1: 从 40 个 manual_review 候选中抽 5 案 provenance slice**

优先选择有原始 source 行号、完整四柱、真实事件年表且没有反馈校准报告标记的案例。逐案核对：原始反馈产生时间、首次预测产生时间、是否参与规则开发、是否由 raw feedback 先生成报告。

- [ ] **Step 2: 人工写入 review decisions**

每案必须有 `reviewed_by`、`reviewed_at`、`classification`、`provenance_evidence`、`notes`。若原始反馈先于预测，分类只能是 `development_only`，即使事实适合做标签。

- [ ] **Step 3: 从原始反馈抽取 observation，不读报告结论**

每条 source 使用可定位形式，如 `cases/raw_feedback/source/实战案例反馈990个案例_part1.md:123` 或 `cases/<case>/feedback.md:14`。高风险标签要求第二 reviewer。

- [ ] **Step 4: 生成并验证 proof slice**

Run:

```bat
python -m tools.school_capability_dataset inventory --cases-dir cases --reports-dir reports --review-decisions META/school-capability-review-decisions-2026-07-12.json --out META/school-capability-case-inventory.json
python -m tools.school_capability_dataset labels --observations META/school-capability-observations-2026-07-12.jsonl --tasks META/school-capability-tasks-2026-07-12.json --out META/school-capability-labels-unbound-2026-07-12.json
python -m tools.school_capability_dataset manifest --inventory META/school-capability-case-inventory.json --labels META/school-capability-labels-unbound-2026-07-12.json --tasks META/school-capability-tasks-2026-07-12.json --out META/school-capability-reviewed-manifest-2026-07-12.json
python -m tools.school_capability_dataset validate --inventory META/school-capability-case-inventory.json --labels META/school-capability-labels-unbound-2026-07-12.json --manifest META/school-capability-reviewed-manifest-2026-07-12.json
```

Expected: 数据合法；若少于 30 个 clean case，明确输出 HOLD（exit 2），不能伪称 GO。

- [ ] **Step 5: 请求关键阶段代码与数据审查**

审查重点：标签是否从报告反抄、时间顺序是否能证明盲性、未知是否误作负例、高风险是否双审、source 是否可定位、同一事实是否重复计数。

- [ ] **Step 6: 处理审查发现并重跑 proof slice**

Run: `pytest tests/evaluation -q && python -m tools.school_capability_dataset validate ...`

Expected: 测试 PASS；数据 gate 为合法 GO-to-expand 或诚实 HOLD。

### Task 6: 扩展到 ≥30 个真实标注案例

**Files:**
- Modify: `META/school-capability-review-decisions-2026-07-12.json`
- Create: `META/school-capability-observations-2026-07-12.jsonl`
- Modify: `META/school-capability-case-inventory.json`
- Modify: `META/school-capability-labels-unbound-2026-07-12.json`
- Modify: `META/school-capability-reviewed-manifest-2026-07-12.json`
- Modify: `META/school-capability-evaluation-config-2026-07-12.json`

**Interfaces:**
- Produces ≥30 个有至少一条可靠标签的案例；盲测 eligibility 数量单独统计。

- [ ] **Step 1: 按 proof slice 同一协议审查剩余候选**

不得批量假定 clean。每案独立记录 provenance 与 reviewer。

- [ ] **Step 2: 扩展 observation 与 labels**

优先覆盖低歧义任务：`education.attainment_band`、`career.path_type`、`career.role_change`、`career.change_window`、`marriage.event_window`。高风险与画像任务不为覆盖率硬凑。

- [ ] **Step 3: 运行完整数据校验**

Run: `python -m tools.school_capability_dataset validate ...`

Expected: `labelled_case_count >= 30`；如果 `blind_eligible_case_count < 30`，输出 HOLD 并给出 prospective collection 缺口。

- [ ] **Step 4: 人工抽查 20% 标签**

随机但可复现地按 case_id 排序后每 5 案抽 1 案；复核 source、label、task schema 和置信等级。发现系统性错误则整批回到 Task 2，不只修抽中项。

- [ ] **Step 5: 提交数据包**

```bat
git add META/school-capability-*.json META/school-capability-observations-2026-07-12.jsonl
git commit -m "data(evaluation): add reviewed real-case capability labels"
```

### Task 7: 冻结、揭示、评分与报告

**Files:**
- Create: `META/school-capability-blind-outputs-2026-07-12.json`
- Create: `META/school-capability-rule-snapshot-2026-07-12.json`
- Create: `META/school-capability-frozen-2026-07-12.json`
- Create: `META/school-capability-labels-2026-07-12.json`
- Create: `META/school-capability-scores-2026-07-12.json`
- Create: `META/school-capability-baseline-2026-07-12.md`

**Interfaces:**
- Consumes: 受限 binary 任务的真实引擎输出。不得用手写“完美答案”冒充引擎预测。
- Produces: 现有 CLI 契约的 frozen run、scores、report。

- [ ] **Step 1: 在 labels 隔离条件下生成 blind outputs**

执行环境只提供 case input、tasks 和 rule snapshot；不得提供 observations、feedback、labels 或反馈校准报告。若当前引擎无法生成合法任务输出，记录 HOLD，不手写替代。

- [ ] **Step 2: 冻结输出**

Run:

```bat
python -m tools.school_capability_baseline freeze --outputs META/school-capability-blind-outputs-2026-07-12.json --tasks META/school-capability-tasks-2026-07-12.json --rule-snapshot META/school-capability-rule-snapshot-2026-07-12.json --out META/school-capability-frozen-2026-07-12.json
```

Expected: exit 0，生成稳定 `freeze_hash`。

- [ ] **Step 3: 冻结后绑定 labels hash**

仅复制 unbound labels 并加入 frozen run 的精确 `freeze_hash`，schema 改为 `school-capability-labels/v1`；不得修改标签内容。

- [ ] **Step 4: 评分**

Run:

```bat
python -m tools.school_capability_baseline score --frozen-run META/school-capability-frozen-2026-07-12.json --manifest META/school-capability-reviewed-manifest-2026-07-12.json --labels META/school-capability-labels-2026-07-12.json --tasks META/school-capability-tasks-2026-07-12.json --rule-snapshot META/school-capability-rule-snapshot-2026-07-12.json --evaluation-config META/school-capability-evaluation-config-2026-07-12.json --out META/school-capability-scores-2026-07-12.json
```

Expected: exit 0；`posteriors_computed=true`。若 posterior 为空或 `N_eff < 5`，保留原结果。

- [ ] **Step 5: 报告**

Run:

```bat
python -m tools.school_capability_baseline report --scores META/school-capability-scores-2026-07-12.json --manifest META/school-capability-reviewed-manifest-2026-07-12.json --out META/school-capability-baseline-2026-07-12.md
```

Expected: exit 0；建议为现有 gate 重算结果，不手写覆盖。

- [ ] **Step 6: 检查展示层 ID 泄漏**

Run: `python -c "from pathlib import Path; t=Path('META/school-capability-baseline-2026-07-12.md').read_text(encoding='utf-8'); forbidden=('statement_id','statement_index','S-','P-','F-'); assert not any(x in t for x in forbidden)"`

Expected: exit 0。

### Task 8: 端到端追溯证明与盘点摘要

**Files:**
- Create: `META/school-capability-data-foundation-summary-2026-07-12.md`
- Modify: `plans/bazi-intelligence-platform-roadmap.md`

**Interfaces:**
- Produces: 一条内部 trace proof（仅结构化审计摘要引用，不进入能力报告）和阶段 GO/HOLD。

- [ ] **Step 1: 选择至少一个合法冻结任务追溯**

验证对应运行结构满足 `Fact → Claim → ArbitrationResult → Prediction`，优先复用 `DecisionRun.validate_trace()`；追溯证据只在 summary 中写文件路径与对象类型，不泄露内部 ID 到 baseline report。

- [ ] **Step 2: 生成 summary**

必须写：总 case 数、各 classification 数、labelled case 数、blind eligible 数、各 task 标签覆盖、冲突数、高风险双审数、posterior 数、各 posterior N_eff、最终 gate、主要 HOLD 原因、prospective collection 下一步。

- [ ] **Step 3: 只按事实更新路线状态**

若 ≥30 标签但没有 ≥30 清洁盲测，路线写“数据标注完成 / 盲测基线 HOLD”；若全链与门禁均满足，再写 Phase 0 GO。不得把“命令成功”写成 GO。

- [ ] **Step 4: 请求最终代码审查**

审查范围：工具代码、测试、review decisions、30 案标签、manifest、冻结 provenance、scores、报告和路线状态。

- [ ] **Step 5: 处理审查发现**

每个 finding 必须分类为 correctness / leakage / provenance / label quality / reporting / non-blocking；correctness、leakage、provenance 未清零不得完成。

### Task 9: 最终验证

**Files:**
- Verify only。

- [ ] **Step 1: 数据工具与 evaluation 测试**

Run: `pytest tests/evaluation -q`

Expected: 全部 PASS。

- [ ] **Step 2: 全仓测试**

Run: `pytest tests/`

Expected: 全部 PASS；任何失败先按 systematic-debugging 定位，不能归因于“无关旧失败”而跳过。

- [ ] **Step 3: 项目元数据测试**

Run: `pytest tests/test_project_metadata.py -q`

Expected: PASS。

- [ ] **Step 4: 工具与规则状态检查**

Run:

```bat
python tools/tool_registry.py --check
python tools/rule_status_scan.py --check
```

Expected: exit 0。

- [ ] **Step 5: 重跑完整评估链**

依次重跑 Task 7 的 freeze、score、report，并比较 frozen hash 与 committed artifact。

Expected: 相同输入得到相同 freeze hash；report 从 scores 基础事实重算 gate。

- [ ] **Step 6: 工作区审计**

Run: `git status --short && git diff --check`

Expected: 无 whitespace error；不包含用户已有的非本任务文件改动；临时 `_phase03-case-audit.json` 已删除。

- [ ] **Step 7: 最终提交**

```bat
git add tools/school_capability_dataset.py tools/README.md tests/evaluation/test_dataset.py tests/fixtures/school_capability_dataset META/school-capability-* plans/bazi-intelligence-platform-roadmap.md
git commit -m "feat(evaluation): establish reviewed real-case capability baseline"
```

## Verification Points

1. **V1 污染保守性**：自动 audit 的 `manual_review` 不会自动变成 blind candidate。
2. **V2 标签来源**：每条标签 source 可定位到真实反馈，不指向 report/analysis/school-claims。
3. **V3 标签语义**：未知缺失，不转负例；高风险双审；冲突不可静默量化。
4. **V4 物理隔离**：freeze 在 labels 文件被读取前完成；hash 绑定任务和规则快照全文。
5. **V5 六维身份**：manifest route、frozen output metadata、score identity 精确一致。
6. **V6 非空后验**：至少一个 binary task 产生 posterior；若引擎输出不合法则明确 HOLD。
7. **V7 追溯**：至少一个任务通过现有结构验证完整 trace。
8. **V8 展示安全**：baseline report 无内部 ID。
9. **V9 可重放**：同输入重跑 freeze hash 一致，report gate 不能手写注入。
10. **V10 诚实门禁**：`N_eff < 5`、高风险不可评估或增量收益为空时保持 HOLD。

## Risk Register

| 风险 | 早期信号 | 处理 | 阻断级别 |
|---|---|---|---|
| 40 个 manual_review 实为反馈先于预测 | RF promotion 时间线显示先有 raw_text | 全部标 development_only；启动 prospective collection | Blocker for blind baseline |
| 缺少可识别人工 reviewer | reviewer 只能填写 agent 名 | 产物保持 unreviewed/HOLD，不伪造人审 | Blocker |
| 指导 02 未完成，无法生成任务输出 | 当前 runner 不能输出 task catalog contract | 只跑受限 binary 子集；仍不行则交付数据包 + HOLD | Blocker for posterior |
| 任务目录与事实不稳定映射 | 5 案标注一致性低 | 停止扩量，修订 observation 协议并复审 | Blocker |
| 高风险标签来源不足 | 只有模糊自述或无第二审 | 不纳入高风险评分 | Non-blocking for low-risk slice |
| 粗粒度 prototype 稀释六维后验 | 全部 provisional_unclassified | 明示 provisional，待指导 01 后重切片 | Accepted temporary |
| 现有 CLI 禁止写 META | `_safe_output` 明确拦截 | 评估先输出隔离 staging，再由经审查的数据构建工具 dry-run/原子发布；不要放宽评估 CLI | Design constraint |
| baseline report 暴露内部 ID | report 文本出现 S-/P-/F- | 出口检查失败，阻断发布 | Blocker |

## Self-Review

- Spec coverage：覆盖 03-A inventory、03-B 六字段标签、03-C reviewed manifest、03-D audit/freeze/score/report、≥30、污染红线、trace、报告禁显与路线状态回写。
- Placeholder scan：实施步骤没有以 TBD/TODO 替代决策；真正需要人工判断的 provenance 和 reviewer 被明确设为人工门禁，而非伪自动化。
- Type consistency：unbound labels 与现有 revealed labels 分开；最终 labels 精确采用 `school-capability-labels/v1`；manifest 保持现有 CLI exact schema；六维 route 名称与 `_score()` 一致。
