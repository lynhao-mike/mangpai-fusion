# Run-Centric Proof Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the smallest testable run-centric vertical slice proving that `Run Snapshot` is the first truth object and case/report/feedback artifacts bind to it instead of defining domain truth.

**Architecture:** Keep the clean target model: `Run` owns lifecycle truth, `engine` performs pure inference, `tools` orchestrate, `cases`/`reports` store derived artifacts. Do not move directories yet; add only the missing binding/feedback surface needed to prove the target model.

**Tech Stack:** Python 3, dataclasses, JSON serialization, pytest, existing `engine.v5` and `tools.render_report_v6` preproduction flow.

## Global Constraints

- Use the staged clean path from `plans/geju-system-refactor-architecture-2026-07-08.md`: target model follows Clean target, migration stays minimal.
- `Run Snapshot` is the first fact object; reports and manifests are derived/bound artifacts.
- No compatibility shims unless a real public workflow needs them.
- No new dependencies.
- No new broad abstraction layer; prefer one focused dataclass/method over new services.
- Verification must include targeted v5 tests and project metadata tests.

---

## Geju Direction Lock

**Thesis:** The correct target is not another report/tool patch. The target is a run-centric inference factory where `V5RunSnapshot` is the lifecycle anchor and all artifacts become bindings.

**Keep:**
- `engine/v5/domain.py` as the current home for serializable v5 contracts.
- `engine/v5/runner.py::run_v5_snapshot` as the pure inference entry that returns a snapshot.
- `tools/render_report_v6.py` as operations-layer orchestration.
- Existing `cases/`, `reports/`, and `predictions/` physical directories as product workflow contracts.

**Delete / avoid:**
- Do not add a new `operations` package for this slice.
- Do not parse Markdown reports back into state.
- Do not make `engine/pipeline.py` the center of this proof.
- Do not add generic repository/service abstractions.

**Merge / reframe:**
- Reframe `manifest.json` as `case ↔ run ↔ artifact` binding, not a case database.
- Reframe feedback as attached learning signals against run targets, not comments on Markdown text.

**First proof point:** A single v5 render flow produces report markdown, v5 JSON, run JSON, decision-run JSON, manifest JSON, and a feedback attachment JSON that points at the run snapshot targets.

**Falsifier:** If feedback cannot be attached without reading report Markdown or case free text as truth, the thesis is incomplete.

---

## File Structure

- Modify: `engine/v5/domain.py`
  - Add the minimal `V5FeedbackAttachment` dataclass.
  - Responsibility: serialize feedback observations bound to one run and existing target IDs.
- Modify: `engine/v5/__init__.py`
  - Export `V5FeedbackAttachment`.
- Modify: `engine/v5/preprod.py`
  - During `render_v6_preprod_case`, write `<report>.feedback-attachment.json` derived from the run snapshot.
  - Add its path to `artifact_bindings` and the case manifest.
- Modify: `tests/v5/test_v5_contracts.py`
  - Test feedback attachment round-trip and target validation.
- Modify: `tests/v5/test_render_report_v6.py`
  - Test render flow writes feedback attachment and manifest binds it.

---

### Task 1: Add minimal feedback attachment contract

**Files:**
- Modify: `engine/v5/domain.py`
- Modify: `engine/v5/__init__.py`
- Test: `tests/v5/test_v5_contracts.py`

**Interfaces:**
- Consumes: `V5RunSnapshot.run_id`, `V5RunSnapshot.case_id`, `V5RunSnapshot.claims`, `V5RunSnapshot.prediction_ledger.predictions`, `V5RunSnapshot.learning_signals`.
- Produces: `V5FeedbackAttachment.from_run_snapshot(snapshot: V5RunSnapshot, feedback_path: str = "") -> V5FeedbackAttachment`, `V5FeedbackAttachment.to_dict() -> dict[str, Any]`, `V5FeedbackAttachment.from_dict(data: dict[str, Any]) -> V5FeedbackAttachment`, `V5FeedbackAttachment.to_json(indent: int | None = 2) -> str`, `V5FeedbackAttachment.from_json(value: str) -> V5FeedbackAttachment`, `V5FeedbackAttachment.validate_targets(snapshot: V5RunSnapshot) -> list[str]`.

- [ ] **Step 1: Write the failing contract test**

Add this import in `tests/v5/test_v5_contracts.py`:

```python
from engine.v5.domain import (
    V5CaseManifest,
    V5Claim,
    V5Confidence,
    V5Evidence,
    V5FeedbackAttachment,
    V5Output,
    V5RunSnapshot,
    V5_SCHOOLS,
)
```

Add this test after `test_v5_case_manifest_rejects_cross_case_run_binding`:

```python
def test_v5_feedback_attachment_binds_to_run_targets_without_report_markdown():
    snapshot = run_v5_snapshot({"case_id": "C-TEST-FEEDBACK-ATTACH", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})

    attachment = V5FeedbackAttachment.from_run_snapshot(
        snapshot,
        feedback_path="cases/C-TEST-FEEDBACK-ATTACH/feedback.md",
    )
    restored = V5FeedbackAttachment.from_json(attachment.to_json())

    assert restored == attachment
    assert attachment.case_id == snapshot.case_id
    assert attachment.run_id == snapshot.run_id
    assert attachment.feedback_path == "cases/C-TEST-FEEDBACK-ATTACH/feedback.md"
    assert attachment.target_claim_ids == [claim.claim_id for claim in snapshot.claims]
    assert attachment.target_prediction_ids == [item.prediction_id for item in snapshot.prediction_ledger.predictions]
    assert attachment.target_signal_ids == [item.signal_id for item in snapshot.learning_signals]
    assert attachment.validate_targets(snapshot) == []


def test_v5_feedback_attachment_reports_missing_targets():
    snapshot = run_v5_snapshot({"case_id": "C-TEST-FEEDBACK-MISSING", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})
    payload = V5FeedbackAttachment.from_run_snapshot(snapshot).to_dict()
    payload["target_claim_ids"].append("missing-claim")
    payload["target_prediction_ids"].append("missing-prediction")
    payload["target_signal_ids"].append("missing-signal")
    attachment = V5FeedbackAttachment.from_dict(payload)

    assert attachment.validate_targets(snapshot) == [
        "feedback target claim_id not found in run snapshot: missing-claim",
        "feedback target prediction_id not found in run snapshot: missing-prediction",
        "feedback target signal_id not found in run snapshot: missing-signal",
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/v5/test_v5_contracts.py::test_v5_feedback_attachment_binds_to_run_targets_without_report_markdown tests/v5/test_v5_contracts.py::test_v5_feedback_attachment_reports_missing_targets -q
```

Expected: FAIL with `ImportError` or `NameError` for `V5FeedbackAttachment`.

- [ ] **Step 3: Implement the minimal dataclass**

Add `V5FeedbackAttachment` in `engine/v5/domain.py` after `V5CaseManifest` and before `V5Output`:

```python
@dataclass(frozen=True)
class V5FeedbackAttachment:
    """feedback.md 对一次 run 的最小挂载清单。

    ponytail: 只记录目标 ID，不解析 Markdown，不写反馈数据库；先证明反馈
    可以绑定 run snapshot，而不是绑定报告文本片段。
    """

    case_id: str
    run_id: str
    feedback_path: str = ""
    target_claim_ids: list[str] = field(default_factory=list)
    target_prediction_ids: list[str] = field(default_factory=list)
    target_signal_ids: list[str] = field(default_factory=list)
    attachment_schema_version: str = "feedback-attachment-v1"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_run_snapshot(
        cls,
        snapshot: V5RunSnapshot,
        *,
        feedback_path: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> "V5FeedbackAttachment":
        return cls(
            case_id=snapshot.case_id,
            run_id=snapshot.run_id,
            feedback_path=feedback_path,
            target_claim_ids=[item.claim_id for item in snapshot.claims],
            target_prediction_ids=[item.prediction_id for item in snapshot.prediction_ledger.predictions],
            target_signal_ids=[item.signal_id for item in snapshot.learning_signals],
            metadata=dict(metadata or {}),
        )

    def validate_targets(self, snapshot: V5RunSnapshot) -> list[str]:
        issues: list[str] = []
        claim_ids = {item.claim_id for item in snapshot.claims}
        prediction_ids = {item.prediction_id for item in snapshot.prediction_ledger.predictions}
        signal_ids = {item.signal_id for item in snapshot.learning_signals}
        for claim_id in self.target_claim_ids:
            if claim_id not in claim_ids:
                issues.append(f"feedback target claim_id not found in run snapshot: {claim_id}")
        for prediction_id in self.target_prediction_ids:
            if prediction_id not in prediction_ids:
                issues.append(f"feedback target prediction_id not found in run snapshot: {prediction_id}")
        for signal_id in self.target_signal_ids:
            if signal_id not in signal_ids:
                issues.append(f"feedback target signal_id not found in run snapshot: {signal_id}")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "attachment_schema_version": self.attachment_schema_version,
            "case_id": self.case_id,
            "run_id": self.run_id,
            "feedback_path": self.feedback_path,
            "target_claim_ids": list(self.target_claim_ids),
            "target_prediction_ids": list(self.target_prediction_ids),
            "target_signal_ids": list(self.target_signal_ids),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "V5FeedbackAttachment":
        return cls(
            case_id=str(data.get("case_id", "")),
            run_id=str(data.get("run_id", "")),
            feedback_path=str(data.get("feedback_path", "")),
            target_claim_ids=[str(x) for x in data.get("target_claim_ids", [])],
            target_prediction_ids=[str(x) for x in data.get("target_prediction_ids", [])],
            target_signal_ids=[str(x) for x in data.get("target_signal_ids", [])],
            attachment_schema_version=str(data.get("attachment_schema_version", "feedback-attachment-v1")),
            metadata=dict(data.get("metadata", {})),
        )

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_json(cls, value: str) -> "V5FeedbackAttachment":
        return cls.from_dict(json.loads(value))
```

Update `engine/v5/__init__.py` imports:

```python
from engine.v5.domain import (
    V5ArbitrationResult,
    V5CaseManifest,
    V5Claim,
    V5Confidence,
    V5Evidence,
    V5FeedbackAttachment,
    V5LearningSignal,
    V5Output,
    V5RunSnapshot,
    V5Prediction,
    V5PredictionLedger,
    V5StructureGraph,
)
```

Add to `__all__`:

```python
    "V5FeedbackAttachment",
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/v5/test_v5_contracts.py::test_v5_feedback_attachment_binds_to_run_targets_without_report_markdown tests/v5/test_v5_contracts.py::test_v5_feedback_attachment_reports_missing_targets -q
```

Expected: PASS.

---

### Task 2: Bind feedback attachment into the v6 render proof slice

**Files:**
- Modify: `engine/v5/preprod.py`
- Modify: `tests/v5/test_render_report_v6.py`

**Interfaces:**
- Consumes: `V5FeedbackAttachment.from_run_snapshot(snapshot, feedback_path=...)` from Task 1.
- Produces: `<report>.feedback-attachment.json` and an `artifact_bindings["feedback_attachment"]` path in both run snapshot and manifest.

- [ ] **Step 1: Inspect current preprod render binding flow**

Run:

```bash
python - <<'PY'
from pathlib import Path
text = Path('engine/v5/preprod.py').read_text(encoding='utf-8')
for needle in ['artifact_bindings', 'manifest.json', 'run.json']:
    print(f'--- {needle} ---')
    idx = text.find(needle)
    print(text[max(0, idx-500):idx+800])
PY
```

Expected: output shows where `artifact_bindings`, run snapshot JSON, and manifest are currently written.

- [ ] **Step 2: Write the failing render test**

In `tests/v5/test_render_report_v6.py`, update imports:

```python
from engine.v5 import V5CaseManifest, V5FeedbackAttachment, V5RunSnapshot
```

In `test_render_report_v6_generates_report_and_v5_json`, after `rendered_decision_json` definition, add:

```python
    rendered_feedback_attachment_json = rendered_report.with_suffix(".feedback-attachment.json")
```

After `assert rendered_decision_json.exists()`, add:

```python
    assert rendered_feedback_attachment_json.exists()
```

Update `expected_artifacts` to include:

```python
        "feedback_attachment": rendered_feedback_attachment_json.as_posix(),
```

After `assert manifest.artifact_paths == expected_artifacts`, add:

```python
    attachment = V5FeedbackAttachment.from_json(rendered_feedback_attachment_json.read_text(encoding="utf-8"))
    assert attachment.case_id == run_snapshot.case_id
    assert attachment.run_id == run_snapshot.run_id
    assert attachment.feedback_path == (case_input.parent / "feedback.md").as_posix()
    assert attachment.validate_targets(run_snapshot) == []
```

In `test_render_report_v6_batch_generates_multiple_reports`, after `decision_json_path`, add:

```python
        feedback_attachment_path = report_path.with_suffix(".feedback-attachment.json")
```

After `assert decision_json_path.exists()`, add:

```python
        assert feedback_attachment_path.exists()
```

- [ ] **Step 3: Run test to verify it fails**

Run:

```bash
pytest tests/v5/test_render_report_v6.py::test_render_report_v6_generates_report_and_v5_json tests/v5/test_render_report_v6.py::test_render_report_v6_batch_generates_multiple_reports -q
```

Expected: FAIL because `.feedback-attachment.json` is not created or not bound.

- [ ] **Step 4: Implement minimal render binding**

In `engine/v5/preprod.py`, import `V5FeedbackAttachment` from `engine.v5.domain` wherever `V5RunSnapshot` and `V5CaseManifest` are imported:

```python
from engine.v5.domain import V5CaseManifest, V5FeedbackAttachment, V5RunSnapshot
```

Inside `render_v6_preprod_case`, use the existing local variables for paths and bindings. Add this path beside existing JSON paths:

```python
feedback_attachment_path = report_path.with_suffix(".feedback-attachment.json")
```

Add the new binding to the `artifact_bindings` dict:

```python
"feedback_attachment": feedback_attachment_path.as_posix(),
```

After the final `run_snapshot` is created with complete `artifact_bindings`, write the attachment JSON:

```python
feedback_attachment = V5FeedbackAttachment.from_run_snapshot(
    run_snapshot,
    feedback_path=feedback_path.as_posix(),
)
feedback_attachment_path.write_text(feedback_attachment.to_json(), encoding="utf-8")
```

Do not parse report Markdown. Do not add a separate service class.

- [ ] **Step 5: Run test to verify it passes**

Run:

```bash
pytest tests/v5/test_render_report_v6.py::test_render_report_v6_generates_report_and_v5_json tests/v5/test_render_report_v6.py::test_render_report_v6_batch_generates_multiple_reports -q
```

Expected: PASS.

---

### Task 3: Verify the proof slice and guard against drift

**Files:**
- No code changes expected.
- Test: `tests/v5/test_v5_contracts.py`, `tests/v5/test_render_report_v6.py`, `tests/test_project_metadata.py`

**Interfaces:**
- Consumes: Task 1 and Task 2 implementation.
- Produces: verification evidence for completion.

- [ ] **Step 1: Run v5 contract tests**

Run:

```bash
pytest tests/v5/test_v5_contracts.py -q
```

Expected: PASS.

- [ ] **Step 2: Run v6 render tests**

Run:

```bash
pytest tests/v5/test_render_report_v6.py -q
```

Expected: PASS.

- [ ] **Step 3: Run project metadata guard**

Run:

```bash
pytest tests/test_project_metadata.py -q
```

Expected: PASS.

- [ ] **Step 4: Run combined targeted verification**

Run:

```bash
pytest tests/v5/test_v5_contracts.py tests/v5/test_render_report_v6.py tests/test_project_metadata.py -q
```

Expected: PASS.

---

## Risk Points

1. `engine/v5/preprod.py` may already create `V5RunSnapshot` before all artifact paths are known. If so, reconstruct the snapshot once with full `artifact_bindings` instead of mutating it.
2. Path expectations in tests use `.as_posix()`. Keep existing style; do not introduce Windows backslashes into JSON payloads.
3. Large default `run_v5` can be slow because it loads production rules. Keep tests targeted and reuse existing patterns.
4. `V5FeedbackAttachment` intentionally does not parse `feedback.md`; adding parsing here would violate the proof slice.

## Self-Review

- Spec coverage: The plan keeps the Clean target as the goal and implements only the staged proof slice. It covers Run Snapshot, artifact binding, feedback attachment, tests, and verification.
- Placeholder scan: No `TBD`, `TODO`, or unspecified implementation steps remain.
- Type consistency: `V5FeedbackAttachment` method names and fields are consistent across tests, exports, and render binding.
