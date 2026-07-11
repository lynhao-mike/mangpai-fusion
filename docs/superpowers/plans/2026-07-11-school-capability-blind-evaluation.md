# School Capability Blind Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立流派能力评估协议与最小盲测数据包，使系统能够在不接触反馈标签的前提下冻结各流派输出，并用统一任务、四组对照、概率评分和条件化能力后验产出第一份不宣称永久专长的基线报告。

**Architecture:** 新增独立的 `engine/evaluation/` 包承载任务、案例清单、盲测输出、冻结包、评分与能力后验；新增 `tools/school_capability_baseline.py` 作为只读 CLI。评估层只消费标准化输入和冻结后的 runner 输出，不改生产路由、规则权重、反馈状态或报告出口；标签揭示通过独立文件和冻结哈希门禁完成。

**Tech Stack:** Python 3 标准库、`dataclasses`、`json`、`hashlib`、`statistics`、现有 pytest；不新增第三方依赖。

## Global Constraints

- 服从 [`docs/superpowers/specs/2026-07-11-bazi-intelligence-platform-core-design.md`](../specs/2026-07-11-bazi-intelligence-platform-core-design.md)。
- 服从 [`plans/bazi-intelligence-platform-roadmap.md`](../../../plans/bazi-intelligence-platform-roadmap.md) 第一推进单元边界。
- 任何流派输出必须是 `claim`、`abstain`、`unsupported` 三态之一。
- 预测冻结前不得读取反馈、旧报告结论或揭示标签。
- 静态权重只作为冷启动弱先验，不作为专长证明。
- 本计划不重写五派 runner、不切换生产入口、不自动修改规则权重、不构建在线学习服务。
- 评估产物必须只读地写入 `reports/` 或测试临时目录，不得改写 `cases/`、`theory/`、`META/` 与现有权重文件。
- 所有概率评分、后验和增量值必须可由输入文件完全复现。

---

## File Structure

### New evaluation package

- `engine/evaluation/__init__.py`：公开评估层稳定接口。
- `engine/evaluation/models.py`：任务、案例审计、三态流派输出、冻结包、揭示标签、评分和能力后验数据契约。
- `engine/evaluation/task_catalog.py`：加载和校验首批统一任务目录。
- `engine/evaluation/case_audit.py`：只读盘点案例输入、反馈、报告和潜在开发污染，生成候选清单。
- `engine/evaluation/freeze.py`：构建 canonical JSON、计算冻结哈希、拒绝冻结后篡改和提前揭示。
- `engine/evaluation/scoring.py`：Brier、Log Loss、时间窗、有序等级、克制和效用评分。
- `engine/evaluation/capability.py`：按流派、任务和原型聚合五维能力及 Beta 可信区间。
- `engine/evaluation/experiments.py`：执行单派、全派、去一派、基础事实+单派四组实验。
- `engine/evaluation/report.py`：渲染基线能力 Markdown，不发布永久专长。

### New protocol and data files

- `mapping/school-capability-task-catalog-v1.yaml`：首批统一任务定义，只含协议和标签口径，不含案例答案。
- `templates/school-capability-case-manifest.json`：案例可用性与污染盘点模板。
- `templates/school-capability-blind-output.json`：runner 三态输出模板，不含标签。
- `templates/school-capability-labels.json`：冻结后单独揭示的标签模板。

### New CLI

- `tools/school_capability_baseline.py`：`audit`、`freeze`、`score`、`report` 四个子命令。

### Tests

- `tests/evaluation/test_models.py`
- `tests/evaluation/test_task_catalog.py`
- `tests/evaluation/test_case_audit.py`
- `tests/evaluation/test_freeze.py`
- `tests/evaluation/test_scoring.py`
- `tests/evaluation/test_capability.py`
- `tests/evaluation/test_experiments.py`
- `tests/evaluation/test_report.py`
- `tests/evaluation/test_cli.py`
- `tests/fixtures/school_capability/`：完全合成的无泄漏测试数据。

---

### Task 1: Evaluation Contracts and Three-State Protocol

**Files:**
- Create: `engine/evaluation/__init__.py`
- Create: `engine/evaluation/models.py`
- Create: `tests/evaluation/test_models.py`

**Interfaces:**
- Produces: `OutputState = Literal["claim", "abstain", "unsupported"]`
- Produces: `BlindTask`, `CaseAuditRecord`, `BlindSchoolOutput`, `BlindPrediction`, `FrozenBlindRun`, `RevealedLabel`, `ScoreRecord`, `CapabilityPosterior` dataclasses.
- Produces: every dataclass implements `to_dict()` and `from_dict()` where persisted.

- [ ] **Step 1: Write failing contract tests**

```python
# tests/evaluation/test_models.py
import pytest

from engine.evaluation.models import BlindPrediction, BlindSchoolOutput, CapabilityPosterior


def test_three_state_output_rejects_claim_without_prediction() -> None:
    with pytest.raises(ValueError, match="claim requires at least one prediction"):
        BlindSchoolOutput(
            case_id="C-TEST-001",
            school_id="ziping",
            task_id="marriage.divorce",
            state="claim",
            rationale="structure supports event",
            predictions=[],
        )


def test_abstain_rejects_predictions() -> None:
    prediction = BlindPrediction(
        prediction_id="P-001",
        event_label="divorce",
        probability=0.7,
        time_window={"start_year": 2015, "end_year": 2020},
        evidence_refs=["F-001"],
        falsifier="no separation through 2020",
    )
    with pytest.raises(ValueError, match="abstain cannot contain predictions"):
        BlindSchoolOutput(
            case_id="C-TEST-001",
            school_id="yang_qingjuan",
            task_id="marriage.divorce",
            state="abstain",
            rationale="insufficient spouse-palace evidence",
            predictions=[prediction],
        )


def test_capability_posterior_round_trip() -> None:
    posterior = CapabilityPosterior(
        school_id="ziping",
        task_id="career.change",
        chart_prototype_id="prototype.structure-clear",
        claim_type="binary_event",
        time_horizon="ten_year",
        evidence_completeness_band="complete",
        coverage_rate=0.8,
        discrimination_score=0.2,
        accuracy_score=0.71,
        calibration_error=0.08,
        incremental_gain=0.04,
        posterior_mean=0.7,
        credible_interval=(0.51, 0.84),
        n_eff=18.0,
        evidence_grade="E2",
        last_evaluated_at="2026-07-11T00:00:00Z",
    )
    assert CapabilityPosterior.from_dict(posterior.to_dict()) == posterior
```

- [ ] **Step 2: Run tests and verify failure**

Run: `pytest tests/evaluation/test_models.py -v`

Expected: FAIL during import because `engine.evaluation.models` does not exist.

- [ ] **Step 3: Implement minimal validated contracts**

Implement frozen dataclasses. Required validation rules:

```python
OutputState = Literal["claim", "abstain", "unsupported"]

@dataclass(frozen=True)
class BlindPrediction:
    prediction_id: str
    event_label: str
    probability: float
    time_window: dict[str, int | str]
    evidence_refs: list[str]
    falsifier: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError("probability must be between 0 and 1")
        if not self.event_label.strip():
            raise ValueError("event_label is required")
        if not self.falsifier.strip():
            raise ValueError("falsifier is required")

@dataclass(frozen=True)
class BlindSchoolOutput:
    case_id: str
    school_id: str
    task_id: str
    state: OutputState
    rationale: str
    predictions: list[BlindPrediction] = field(default_factory=list)
    counter_evidence: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.state == "claim" and not self.predictions:
            raise ValueError("claim requires at least one prediction")
        if self.state != "claim" and self.predictions:
            raise ValueError(f"{self.state} cannot contain predictions")
        if not self.rationale.strip():
            raise ValueError("rationale is required")
```

Define the remaining persisted fields exactly as listed in File Structure and implement deterministic `to_dict()` / `from_dict()` conversion, converting tuple JSON fields back to tuples.

- [ ] **Step 4: Run contract tests**

Run: `pytest tests/evaluation/test_models.py -v`

Expected: all tests PASS.

- [ ] **Step 5: Commit contracts**

```bash
git add engine/evaluation/__init__.py engine/evaluation/models.py tests/evaluation/test_models.py
git commit -m "feat: add blind evaluation contracts"
```

---

### Task 2: Unified Task Catalog

**Files:**
- Create: `mapping/school-capability-task-catalog-v1.yaml`
- Create: `engine/evaluation/task_catalog.py`
- Create: `tests/evaluation/test_task_catalog.py`

**Interfaces:**
- Consumes: `BlindTask` from Task 1.
- Produces: `load_task_catalog(path: Path) -> list[BlindTask]`.
- Produces: `task_by_id(tasks: Sequence[BlindTask]) -> dict[str, BlindTask]`.

- [ ] **Step 1: Write failing catalog tests**

```python
# tests/evaluation/test_task_catalog.py
from pathlib import Path

import pytest

from engine.evaluation.task_catalog import load_task_catalog


def test_catalog_has_unique_ids_and_supported_scorers() -> None:
    tasks = load_task_catalog(Path("mapping/school-capability-task-catalog-v1.yaml"))
    assert 15 <= len(tasks) <= 25
    assert len({task.task_id for task in tasks}) == len(tasks)
    assert {task.domain for task in tasks} >= {"婚姻", "财富", "事业", "学业", "健康", "性格"}
    assert {task.scoring_method for task in tasks} <= {
        "binary_probability", "multiclass_probability", "ordinal", "time_window", "portrait_agreement"
    }


def test_catalog_rejects_probability_task_without_label_schema(tmp_path: Path) -> None:
    path = tmp_path / "tasks.yaml"
    path.write_text(
        "schema_version: school-capability-tasks/v1\ntasks:\n"
        "  - task_id: marriage.divorce\n"
        "    domain: 婚姻\n"
        "    claim_type: binary_event\n"
        "    scoring_method: binary_probability\n"
        "    quantifiable: true\n"
        "    label_schema: {}\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="label_schema"):
        load_task_catalog(path)
```

- [ ] **Step 2: Run tests and verify failure**

Run: `pytest tests/evaluation/test_task_catalog.py -v`

Expected: FAIL because loader and catalog are absent.

- [ ] **Step 3: Create the first catalog**

Create 18 tasks:

```text
marriage.late_marriage
marriage.divorce_or_remarriage
marriage.relationship_pressure
marriage.event_window
wealth.income_band
wealth.volatility
wealth.debt
wealth.major_loss_window
career.path_type
career.role_change
career.change_window
education.attainment_band
education.continuing_credentials
health.system_risk
health.event_window
personality.decision_style
personality.pressure_response
portrait.partner_profile
```

Each YAML item must include:

```yaml
- task_id: marriage.divorce_or_remarriage
  domain: 婚姻
  claim_type: binary_event
  scoring_method: binary_probability
  quantifiable: true
  high_risk: true
  allowed_time_horizons: [lifetime, ten_year]
  required_input_fields: [four_pillars, sex_marker]
  label_schema:
    type: boolean
    positive_label: occurred
    negative_label: not_observed
  evaluation_note: 只评价是否发生，不把关系压力自动等同离婚
```

Personality and portrait tasks must use `portrait_agreement` and `quantifiable: false`.

- [ ] **Step 4: Implement strict loader**

Use the repository’s existing `yaml.safe_load`. Reject duplicate task IDs, unsupported scoring methods, missing domains, and quantifiable tasks without a non-empty label schema. Do not add schema libraries.

- [ ] **Step 5: Run catalog tests**

Run: `pytest tests/evaluation/test_task_catalog.py -v`

Expected: all tests PASS.

- [ ] **Step 6: Commit catalog**

```bash
git add mapping/school-capability-task-catalog-v1.yaml engine/evaluation/task_catalog.py tests/evaluation/test_task_catalog.py
git commit -m "feat: define school capability task catalog"
```

---

### Task 3: Read-Only Case Audit and Contamination Manifest

**Files:**
- Create: `engine/evaluation/case_audit.py`
- Create: `templates/school-capability-case-manifest.json`
- Create: `tests/evaluation/test_case_audit.py`
- Create: `tests/fixtures/school_capability/cases/C-TEST-001/input.md`
- Create: `tests/fixtures/school_capability/cases/C-TEST-001/feedback.md`
- Create: `tests/fixtures/school_capability/reports/C-TEST-001-content-report.md`

**Interfaces:**
- Consumes: repository or fixture root `Path`.
- Produces: `audit_case(case_dir: Path, reports_dir: Path) -> CaseAuditRecord`.
- Produces: `audit_cases(cases_dir: Path, reports_dir: Path) -> list[CaseAuditRecord]`.
- Produces: `write_case_manifest(records: Sequence[CaseAuditRecord], path: Path) -> None`.

- [ ] **Step 1: Write failing audit tests**

```python
# tests/evaluation/test_case_audit.py
from pathlib import Path

from engine.evaluation.case_audit import audit_case

FIXTURES = Path("tests/fixtures/school_capability")


def test_audit_marks_feedback_calibrated_report_as_contaminated() -> None:
    record = audit_case(
        FIXTURES / "cases/C-TEST-001",
        FIXTURES / "reports",
    )
    assert record.has_input is True
    assert record.has_feedback is True
    assert record.feedback_quantifiable is True
    assert "feedback_calibrated_report" in record.contamination_flags
    assert record.eligibility == "development_only"


def test_audit_never_mutates_case_files() -> None:
    input_path = FIXTURES / "cases/C-TEST-001/input.md"
    before = input_path.read_bytes()
    audit_case(input_path.parent, FIXTURES / "reports")
    assert input_path.read_bytes() == before
```

- [ ] **Step 2: Run tests and verify failure**

Run: `pytest tests/evaluation/test_case_audit.py -v`

Expected: FAIL because audit module is absent.

- [ ] **Step 3: Implement conservative audit rules**

The audit must record:

```text
case_id
has_input
has_feedback
has_statement_index
has_existing_report
feedback_quantifiable
contamination_flags
eligibility
evidence_notes
```

Initial contamination flags:

```text
feedback_calibrated_report
known_facts_embedded_in_input
rule_development_reference
missing_birth_input
missing_feedback
unstructured_feedback
```

Eligibility values:

```text
blind_candidate
historical_blind_candidate
development_only
not_scorable
manual_review
```

Conservative rule: any explicit “反馈校准”“既有反馈”“已验” in report or analysis makes the case `development_only`; uncertain matches become `manual_review`, never automatically `blind_candidate`.

- [ ] **Step 4: Add manifest template**

The template must be valid JSON with `schema_version`, `generated_at`, `records`, and an empty example record documenting all fields. It must not contain real case labels.

- [ ] **Step 5: Run audit tests**

Run: `pytest tests/evaluation/test_case_audit.py -v`

Expected: all tests PASS.

- [ ] **Step 6: Commit audit slice**

```bash
git add engine/evaluation/case_audit.py templates/school-capability-case-manifest.json tests/evaluation/test_case_audit.py tests/fixtures/school_capability
git commit -m "feat: audit cases for blind evaluation eligibility"
```

---

### Task 4: Blind Output Templates, Freeze, and Label Reveal Gate

**Files:**
- Create: `engine/evaluation/freeze.py`
- Create: `templates/school-capability-blind-output.json`
- Create: `templates/school-capability-labels.json`
- Create: `tests/evaluation/test_freeze.py`

**Interfaces:**
- Consumes: `Sequence[BlindSchoolOutput]`, task catalog version, rule snapshot ID.
- Produces: `freeze_outputs(...) -> FrozenBlindRun`.
- Produces: `verify_frozen_run(run: FrozenBlindRun) -> None`.
- Produces: `reveal_labels(run: FrozenBlindRun, labels_path: Path) -> list[RevealedLabel]`.

- [ ] **Step 1: Write failing freeze tests**

```python
# tests/evaluation/test_freeze.py
import json
from pathlib import Path

import pytest

from engine.evaluation.freeze import freeze_outputs, reveal_labels, verify_frozen_run
from engine.evaluation.models import BlindPrediction, BlindSchoolOutput


def _output() -> BlindSchoolOutput:
    return BlindSchoolOutput(
        case_id="C-TEST-001",
        school_id="ziping",
        task_id="marriage.divorce_or_remarriage",
        state="claim",
        rationale="spouse structure is unstable",
        predictions=[BlindPrediction(
            prediction_id="P-001",
            event_label="occurred",
            probability=0.7,
            time_window={"start_year": 2015, "end_year": 2020},
            evidence_refs=["F-001"],
            falsifier="no divorce or remarriage observed",
        )],
    )


def test_freeze_is_order_independent_and_tamper_evident() -> None:
    first = freeze_outputs([_output()], "tasks-v1", "rules-v1")
    second = freeze_outputs([_output()], "tasks-v1", "rules-v1")
    assert first.freeze_hash == second.freeze_hash
    altered = first.to_dict()
    altered["outputs"][0]["rationale"] = "changed after freeze"
    with pytest.raises(ValueError, match="freeze hash mismatch"):
        verify_frozen_run(type(first).from_dict(altered))


def test_reveal_rejects_wrong_freeze_hash(tmp_path: Path) -> None:
    run = freeze_outputs([_output()], "tasks-v1", "rules-v1")
    path = tmp_path / "labels.json"
    path.write_text(json.dumps({
        "schema_version": "school-capability-labels/v1",
        "freeze_hash": "wrong",
        "labels": [],
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="freeze_hash"):
        reveal_labels(run, path)
```

- [ ] **Step 2: Run tests and verify failure**

Run: `pytest tests/evaluation/test_freeze.py -v`

Expected: FAIL because freeze module is absent.

- [ ] **Step 3: Implement canonical freeze**

Canonical payload rules:

```python
def canonical_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compute_freeze_hash(payload: dict[str, object]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
```

Sort outputs by `(case_id, task_id, school_id)` and predictions by `prediction_id`. Exclude `freeze_hash` from the hashed payload. `reveal_labels()` must verify the run before reading labels and require exact freeze hash equality.

- [ ] **Step 4: Create separate templates**

Blind output template contains task, state, rationale and predictions but no answer fields. Labels template contains `freeze_hash` and labels but no runner rationale. This physical separation is mandatory.

- [ ] **Step 5: Run freeze tests**

Run: `pytest tests/evaluation/test_freeze.py -v`

Expected: all tests PASS.

- [ ] **Step 6: Commit freeze protocol**

```bash
git add engine/evaluation/freeze.py templates/school-capability-blind-output.json templates/school-capability-labels.json tests/evaluation/test_freeze.py
git commit -m "feat: freeze blind outputs before label reveal"
```

---

### Task 5: Task-Aware Scoring and Abstention Utility

**Files:**
- Create: `engine/evaluation/scoring.py`
- Create: `tests/evaluation/test_scoring.py`

**Interfaces:**
- Produces: `brier_score(probability: float, observed: bool) -> float` where lower is better.
- Produces: `log_loss(probability: float, observed: bool, epsilon: float = 1e-15) -> float`.
- Produces: `time_window_score(predicted: dict[str, int], observed_year: int) -> float` in `[0, 1]`.
- Produces: `ordinal_score(predicted_rank: int, observed_rank: int, max_rank: int) -> float` in `[0, 1]`.
- Produces: `score_output(output, task, labels) -> ScoreRecord`.

- [ ] **Step 1: Write failing score tests**

```python
# tests/evaluation/test_scoring.py
from engine.evaluation.scoring import brier_score, log_loss, ordinal_score, time_window_score


def test_probability_scores_reward_calibrated_correct_prediction() -> None:
    assert brier_score(0.8, True) == 0.04
    assert brier_score(0.2, True) == 0.64
    assert log_loss(0.8, True) < log_loss(0.2, True)


def test_time_window_scores_inside_and_penalizes_distance() -> None:
    window = {"start_year": 2015, "end_year": 2020}
    assert time_window_score(window, 2018) == 1.0
    assert time_window_score(window, 2021) > time_window_score(window, 2025)
    assert 0.0 <= time_window_score(window, 2025) <= 1.0


def test_ordinal_score_is_normalized() -> None:
    assert ordinal_score(5, 5, 15) == 1.0
    assert ordinal_score(1, 15, 15) == 0.0
```

- [ ] **Step 2: Run tests and verify failure**

Run: `pytest tests/evaluation/test_scoring.py -v`

Expected: FAIL because scoring module is absent.

- [ ] **Step 3: Implement pure score functions**

Use standard definitions:

```python
def brier_score(probability: float, observed: bool) -> float:
    return round((probability - float(observed)) ** 2, 12)


def log_loss(probability: float, observed: bool, epsilon: float = 1e-15) -> float:
    p = min(max(probability, epsilon), 1.0 - epsilon)
    return -math.log(p if observed else 1.0 - p)


def ordinal_score(predicted_rank: int, observed_rank: int, max_rank: int) -> float:
    if max_rank <= 1:
        raise ValueError("max_rank must be greater than 1")
    return 1.0 - abs(predicted_rank - observed_rank) / (max_rank - 1)
```

For time windows: score `1.0` inside the window; outside, use `1 / (1 + distance_years)`.

- [ ] **Step 4: Implement task-aware output scoring**

Rules:

- `claim`: score according to task method;
- `abstain`: store `abstained=True`, no fabricated accuracy; utility applies a configurable opportunity cost only when a valid label exists;
- `unsupported`: excluded from accuracy and marked `knowledge_coverage=False`;
- high-risk tasks multiply false-positive cost by `2.0` in the initial protocol;
- non-quantifiable portrait tasks emit agreement fields but do not enter accuracy posterior.

Keep coefficients as named constants in `scoring.py`; do not load production config.

- [ ] **Step 5: Run scoring tests**

Run: `pytest tests/evaluation/test_scoring.py -v`

Expected: all tests PASS.

- [ ] **Step 6: Commit scoring**

```bash
git add engine/evaluation/scoring.py tests/evaluation/test_scoring.py
git commit -m "feat: score blind predictions by task type"
```

---

### Task 6: Capability Posterior and Four-Group Experiments

**Files:**
- Create: `engine/evaluation/capability.py`
- Create: `engine/evaluation/experiments.py`
- Create: `tests/evaluation/test_capability.py`
- Create: `tests/evaluation/test_experiments.py`

**Interfaces:**
- Consumes: `Sequence[ScoreRecord]`.
- Produces: `beta_posterior(hit_weight: float, miss_weight: float) -> tuple[float, tuple[float, float]]`.
- Produces: `build_capability_posteriors(scores, evidence_grade, evaluated_at) -> list[CapabilityPosterior]`.
- Produces: `run_four_group_experiment(outputs, labels, tasks, schools) -> ExperimentResult`.
- Produces: experiment groups `school_only`, `all_schools`, `leave_one_school_out`, `baseline_plus_school`.

- [ ] **Step 1: Write failing posterior tests**

```python
# tests/evaluation/test_capability.py
from engine.evaluation.capability import beta_posterior


def test_beta_posterior_uses_uniform_prior_and_widens_for_small_samples() -> None:
    small_mean, small_interval = beta_posterior(2.0, 0.0)
    large_mean, large_interval = beta_posterior(20.0, 0.0)
    assert small_mean == 0.75
    assert large_mean > small_mean
    assert small_interval[1] - small_interval[0] > large_interval[1] - large_interval[0]
```

- [ ] **Step 2: Write failing experiment tests**

```python
# tests/evaluation/test_experiments.py
from engine.evaluation.experiments import experiment_group_ids


def test_four_group_protocol_is_complete() -> None:
    groups = experiment_group_ids(["ziping", "yang_qingjuan"])
    assert groups == {
        "school_only:ziping",
        "school_only:yang_qingjuan",
        "all_schools",
        "leave_one_school_out:ziping",
        "leave_one_school_out:yang_qingjuan",
        "baseline_plus_school:ziping",
        "baseline_plus_school:yang_qingjuan",
    }
```

- [ ] **Step 3: Run tests and verify failure**

Run: `pytest tests/evaluation/test_capability.py tests/evaluation/test_experiments.py -v`

Expected: FAIL because modules are absent.

- [ ] **Step 4: Implement dependency-free Beta approximation**

Use Beta(1+hit, 1+miss). Mean is exact. Credible interval uses a documented normal approximation clipped to `[0, 1]`:

```python
mean = alpha / (alpha + beta)
variance = alpha * beta / ((alpha + beta) ** 2 * (alpha + beta + 1))
half_width = 1.96 * math.sqrt(variance)
interval = (max(0.0, mean - half_width), min(1.0, mean + half_width))
```

Name the interval field `credible_interval_approx` in internal comments, while persisted contract remains `credible_interval`. Do not claim exact Bayesian quantiles.

- [ ] **Step 5: Aggregate five capability dimensions**

For each identity tuple `(school_id, task_id, chart_prototype_id, claim_type, time_horizon, evidence_completeness_band)` compute:

- coverage rate: non-unsupported / eligible cases;
- discrimination score: standard deviation of claim probabilities, zero when fewer than two claims;
- accuracy score: `1 - mean_brier` for binary probability tasks;
- calibration error: mean absolute difference between probability bins and observed rates, omitted when fewer than five scored claims;
- incremental gain: injected later from experiment results;
- N_eff: hit weight + miss weight, with `partial` contributing `0.5` only if the task protocol defines it.

- [ ] **Step 6: Implement deterministic fusion for experiments**

Initial evaluation-only fusion:

- all contributing claims are equal-weighted;
- unsupported is excluded;
- abstain contributes no probability;
- if no claim remains, group result is no-output;
- baseline probability is empirical task prevalence computed only from the designated development split, never from the evaluated case labels;
- leave-one-out removes exactly one school before fusion.

This is a neutral measurement baseline, not the future production arbitrator.

- [ ] **Step 7: Run capability and experiment tests**

Run: `pytest tests/evaluation/test_capability.py tests/evaluation/test_experiments.py -v`

Expected: all tests PASS.

- [ ] **Step 8: Commit capability experiments**

```bash
git add engine/evaluation/capability.py engine/evaluation/experiments.py tests/evaluation/test_capability.py tests/evaluation/test_experiments.py
git commit -m "feat: estimate conditional school capability"
```

---

### Task 7: Baseline Report and Read-Only CLI

**Files:**
- Create: `engine/evaluation/report.py`
- Create: `tools/school_capability_baseline.py`
- Create: `tests/evaluation/test_report.py`
- Create: `tests/evaluation/test_cli.py`
- Modify: `tools/README.md` at the active tool index section.

**Interfaces:**
- Produces: `render_capability_report(manifest, experiment, posteriors) -> str`.
- Produces CLI commands:
  - `python -m tools.school_capability_baseline audit --cases-dir ... --reports-dir ... --out ...`
  - `python -m tools.school_capability_baseline freeze --outputs ... --tasks ... --rule-snapshot ... --out ...`
  - `python -m tools.school_capability_baseline score --frozen-run ... --labels ... --tasks ... --out ...`
  - `python -m tools.school_capability_baseline report --scores ... --manifest ... --out ...`

- [ ] **Step 1: Write failing report test**

```python
# tests/evaluation/test_report.py
from engine.evaluation.report import render_capability_report


def test_report_refuses_to_publish_permanent_expertise_language() -> None:
    text = render_capability_report(
        manifest_summary={"blind_candidate": 3, "development_only": 2},
        experiment_summary={"all_schools": {"utility": 0.61}},
        posteriors=[],
    )
    assert "暂定能力基线" in text
    assert "永久专长" not in text
    assert "样本与证据限制" in text
    assert "标签泄漏" in text
```

- [ ] **Step 2: Write failing CLI audit test**

```python
# tests/evaluation/test_cli.py
import json
import subprocess
import sys
from pathlib import Path


def test_cli_audit_writes_manifest_without_mutating_cases(tmp_path: Path) -> None:
    fixture_root = Path("tests/fixtures/school_capability")
    output = tmp_path / "manifest.json"
    result = subprocess.run(
        [
            sys.executable, "-m", "tools.school_capability_baseline", "audit",
            "--cases-dir", str(fixture_root / "cases"),
            "--reports-dir", str(fixture_root / "reports"),
            "--out", str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "school-capability-case-manifest/v1"
```

- [ ] **Step 3: Run tests and verify failure**

Run: `pytest tests/evaluation/test_report.py tests/evaluation/test_cli.py -v`

Expected: FAIL because report and CLI modules are absent.

- [ ] **Step 4: Implement report renderer**

Report sections:

```text
1. 评估范围与证据等级
2. 案例可用性与污染盘点
3. 任务覆盖与三态输出
4. 五维能力基线
5. 四组增量实验
6. 条件化能力后验
7. 校准与高风险误差
8. 样本与证据限制
9. GO / HOLD / STOP 建议
```

If all posterior N_eff values are below the initial review threshold, report must say `HOLD` and must not rank permanent specialties.

- [ ] **Step 5: Implement argparse CLI**

Each subcommand validates inputs before writing. Writes use UTF-8 and atomic replacement through a temporary sibling file. `score` must call `verify_frozen_run()` before loading labels. No command may write under `cases/`, `theory/`, `META/` or overwrite [`engine/expert-weights.yaml`](../../../engine/expert-weights.yaml).

- [ ] **Step 6: Register the tool**

Add one active entry to [`tools/README.md`](../../../tools/README.md) describing the CLI as read-only capability evaluation, not a production calibration entrypoint.

- [ ] **Step 7: Run focused tests**

Run: `pytest tests/evaluation/ -v`

Expected: all evaluation tests PASS.

- [ ] **Step 8: Run repository regression gates**

Run: `pytest tests/test_project_metadata.py tests/test_decision_mvp.py tests/test_l9_router_calibration.py tests/v5/ -q`

Expected: all selected existing tests PASS.

- [ ] **Step 9: Run a fixture end-to-end smoke**

```bat
python -m tools.school_capability_baseline audit --cases-dir tests\fixtures\school_capability\cases --reports-dir tests\fixtures\school_capability\reports --out .pytest_cache\school-capability-manifest.json
```

Expected: exit code 0; manifest reports the contaminated fixture as `development_only`.

Do not run score against real case feedback in this task; real-label use requires a reviewed manifest and separate execution approval.

- [ ] **Step 10: Commit report and CLI**

```bash
git add engine/evaluation/report.py tools/school_capability_baseline.py tools/README.md tests/evaluation/test_report.py tests/evaluation/test_cli.py
git commit -m "feat: report blind school capability baseline"
```

---

## Final Verification Gate

- [ ] Run all new tests: `pytest tests/evaluation/ -q`
- [ ] Run relevant existing tests: `pytest tests/test_decision_mvp.py tests/test_l1_learned_prior.py tests/test_l9_router_calibration.py tests/test_accuracy_report.py tests/v5/ -q`
- [ ] Run metadata tests: `pytest tests/test_project_metadata.py -q`
- [ ] Run whitespace check: `git diff --check`
- [ ] Confirm no production state changed: `git status --short cases theory META engine/expert-weights.yaml engine/domain-weights.yaml`
- [ ] Review final diff for forbidden scope: no runner rewrite, no production entry switch, no automatic rule update, no online service.
- [ ] Produce the first fixture-only baseline report and record its path in the implementation completion summary.

## Completion Criteria

This plan is complete only when:

1. The repository can audit cases conservatively for blind-evaluation eligibility and contamination;
2. A versioned 15—25 task catalog exists across all six domains;
3. School outputs use validated `claim / abstain / unsupported` states;
4. Outputs are frozen with a deterministic hash before labels can be revealed;
5. Task-aware scores distinguish probability, timing, ordinal and non-quantifiable portrait tasks;
6. Four experiment groups run deterministically;
7. Capability posterior output includes coverage, discrimination, accuracy, calibration, incremental gain, uncertainty and N_eff;
8. The baseline report explicitly distinguishes weak prior, historical blind evidence and future prospective evidence;
9. The CLI remains read-only with respect to production cases, theory, metadata and weights;
10. No document or report claims a permanent school specialty from the initial sample.
