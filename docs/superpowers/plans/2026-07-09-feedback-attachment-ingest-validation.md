# Feedback Attachment Ingest Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `tools.feedback_ingest.ingest()` read `feedback-attachment.json`, validate it against the matching run snapshot, and report the result in ingest summary without changing learning behavior.

**Architecture:** Add one small read-only helper inside `tools/feedback_ingest.py`; do not create a new service, repository, or file. The helper loads `V5FeedbackAttachment` and `V5RunSnapshot`, returns a stable summary dict, and `ingest()` attaches that dict under `phase_a_learning_summary["v5_feedback_attachment"]` in both existing ingest branches.

**Tech Stack:** Python 3, dataclasses already in use, pathlib/json stdlib, pytest, existing `engine.v5.domain` contracts.

## Global Constraints

- Do not parse report Markdown.
- Do not use attachment as a rule-learning source.
- Do not replace `statement_records.json`.
- Do not block the existing ingest main flow.
- Do not add an independent service/repository/helper file.
- Missing / invalid / mismatch attachment states are summary-only and must not change current learning counts.

---

## File Structure

- Modify: `tools/feedback_ingest.py`
  - Add `_validate_v5_feedback_attachment(case_dir: pathlib.Path, full_case_id: str) -> dict[str, Any]`.
  - Call it once after `case_dir` / `full_case_id` are resolved.
  - Include its result in `phase_a_learning_summary` for both early-return and normal paths.
- Modify: `tests/v1_3_acceptance/test_h3_feedback_parsing.py`
  - Add helper-level tests for ok / missing / mismatch.
  - Add one ingest dry-run summary test proving existing learning behavior is not blocked.

---

### Task 1: Add read-only attachment validation helper

**Files:**
- Modify: `tools/feedback_ingest.py`
- Test: `tests/v1_3_acceptance/test_h3_feedback_parsing.py`

**Interfaces:**
- Consumes: `V5FeedbackAttachment.from_json(value: str) -> V5FeedbackAttachment`, `V5RunSnapshot.from_json(value: str) -> V5RunSnapshot`, `V5FeedbackAttachment.validate_targets(snapshot: V5RunSnapshot) -> list[str]`.
- Produces: `_validate_v5_feedback_attachment(case_dir: pathlib.Path, full_case_id: str) -> dict[str, Any]`.

- [ ] **Step 1: Write failing helper tests**

Add these tests to the end of `tests/v1_3_acceptance/test_h3_feedback_parsing.py`:

```python
def test_v5_feedback_attachment_validation_ok(tmp_path):
    from engine.v5 import V5FeedbackAttachment, V5RunSnapshot, run_v5_snapshot
    from tools.feedback_ingest import _validate_v5_feedback_attachment

    case_dir = tmp_path / "C-TEST-ATTACH-OK"
    case_dir.mkdir()
    snapshot = run_v5_snapshot({"case_id": "C-TEST-ATTACH-OK", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})
    run_path = case_dir / "case.run.json"
    attachment_path = case_dir / "case.feedback-attachment.json"
    run_path.write_text(snapshot.to_json(), encoding="utf-8")
    attachment_path.write_text(
        V5FeedbackAttachment.from_run_snapshot(snapshot, feedback_path=(case_dir / "feedback.md").as_posix()).to_json(),
        encoding="utf-8",
    )

    summary = _validate_v5_feedback_attachment(case_dir, "C-TEST-ATTACH-OK")

    assert summary == {
        "status": "ok",
        "attachment_path": attachment_path.as_posix(),
        "run_snapshot_path": run_path.as_posix(),
        "case_id": "C-TEST-ATTACH-OK",
        "run_id": snapshot.run_id,
        "target_counts": {
            "claims": len(snapshot.claims),
            "predictions": len(snapshot.prediction_ledger.predictions),
            "signals": len(snapshot.learning_signals),
        },
        "issues": [],
    }


def test_v5_feedback_attachment_validation_missing(tmp_path):
    from tools.feedback_ingest import _validate_v5_feedback_attachment

    case_dir = tmp_path / "C-TEST-ATTACH-MISSING"
    case_dir.mkdir()

    summary = _validate_v5_feedback_attachment(case_dir, "C-TEST-ATTACH-MISSING")

    assert summary["status"] == "missing"
    assert summary["attachment_path"] == ""
    assert summary["run_snapshot_path"] == ""
    assert summary["case_id"] == "C-TEST-ATTACH-MISSING"
    assert summary["run_id"] == ""
    assert summary["target_counts"] == {"claims": 0, "predictions": 0, "signals": 0}
    assert summary["issues"] == ["feedback attachment not found"]


def test_v5_feedback_attachment_validation_reports_target_mismatch(tmp_path):
    from engine.v5 import V5FeedbackAttachment, run_v5_snapshot
    from tools.feedback_ingest import _validate_v5_feedback_attachment

    case_dir = tmp_path / "C-TEST-ATTACH-MISMATCH"
    case_dir.mkdir()
    snapshot = run_v5_snapshot({"case_id": "C-TEST-ATTACH-MISMATCH", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})
    payload = V5FeedbackAttachment.from_run_snapshot(snapshot).to_dict()
    payload["target_prediction_ids"].append("missing-prediction")
    (case_dir / "case.run.json").write_text(snapshot.to_json(), encoding="utf-8")
    (case_dir / "case.feedback-attachment.json").write_text(
        V5FeedbackAttachment.from_dict(payload).to_json(),
        encoding="utf-8",
    )

    summary = _validate_v5_feedback_attachment(case_dir, "C-TEST-ATTACH-MISMATCH")

    assert summary["status"] == "mismatch"
    assert "feedback target prediction_id not found in run snapshot: missing-prediction" in summary["issues"]
```

- [ ] **Step 2: Run helper tests to verify they fail**

Run:

```bash
pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_ok tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_missing tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_reports_target_mismatch -q
```

Expected: FAIL with `ImportError` for `_validate_v5_feedback_attachment`.

- [ ] **Step 3: Implement minimal helper**

In `tools/feedback_ingest.py`, add imports near existing imports:

```python
from engine.v5.domain import V5FeedbackAttachment, V5RunSnapshot
```

Add this helper before the `ingest()` section:

```python
def _empty_v5_attachment_summary(status: str, *, case_id: str, issue: str = "") -> dict[str, Any]:
    return {
        "status": status,
        "attachment_path": "",
        "run_snapshot_path": "",
        "case_id": case_id,
        "run_id": "",
        "target_counts": {"claims": 0, "predictions": 0, "signals": 0},
        "issues": [issue] if issue else [],
    }


def _validate_v5_feedback_attachment(case_dir: pathlib.Path, full_case_id: str) -> dict[str, Any]:
    """只读校验 feedback-attachment.json 与 run snapshot 的绑定关系。"""

    attachments = sorted(case_dir.glob("*.feedback-attachment.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not attachments:
        return _empty_v5_attachment_summary("missing", case_id=full_case_id, issue="feedback attachment not found")
    attachment_path = attachments[0]
    run_snapshots = sorted(case_dir.glob("*.run.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not run_snapshots:
        summary = _empty_v5_attachment_summary("missing", case_id=full_case_id, issue="run snapshot not found")
        summary["attachment_path"] = attachment_path.as_posix()
        return summary
    run_snapshot_path = run_snapshots[0]

    try:
        attachment = V5FeedbackAttachment.from_json(attachment_path.read_text(encoding="utf-8"))
        snapshot = V5RunSnapshot.from_json(run_snapshot_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return {
            "status": "invalid",
            "attachment_path": attachment_path.as_posix(),
            "run_snapshot_path": run_snapshot_path.as_posix(),
            "case_id": full_case_id,
            "run_id": "",
            "target_counts": {"claims": 0, "predictions": 0, "signals": 0},
            "issues": [f"invalid v5 feedback attachment payload: {exc}"],
        }

    issues: list[str] = []
    if attachment.case_id != full_case_id:
        issues.append(f"feedback attachment case_id mismatch: {attachment.case_id} != {full_case_id}")
    if snapshot.case_id != full_case_id:
        issues.append(f"run snapshot case_id mismatch: {snapshot.case_id} != {full_case_id}")
    if attachment.run_id != snapshot.run_id:
        issues.append(f"feedback attachment run_id mismatch: {attachment.run_id} != {snapshot.run_id}")
    issues.extend(attachment.validate_targets(snapshot))

    return {
        "status": "mismatch" if issues else "ok",
        "attachment_path": attachment_path.as_posix(),
        "run_snapshot_path": run_snapshot_path.as_posix(),
        "case_id": attachment.case_id,
        "run_id": attachment.run_id,
        "target_counts": {
            "claims": len(attachment.target_claim_ids),
            "predictions": len(attachment.target_prediction_ids),
            "signals": len(attachment.target_signal_ids),
        },
        "issues": issues,
    }
```

- [ ] **Step 4: Run helper tests to verify they pass**

Run:

```bash
pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_ok tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_missing tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_reports_target_mismatch -q
```

Expected: PASS.

---

### Task 2: Attach validation summary to ingest result without changing learning logic

**Files:**
- Modify: `tools/feedback_ingest.py`
- Test: `tests/v1_3_acceptance/test_h3_feedback_parsing.py`

**Interfaces:**
- Consumes: `_validate_v5_feedback_attachment(case_dir: pathlib.Path, full_case_id: str) -> dict[str, Any]`.
- Produces: `IngestResult.phase_a_learning_summary["v5_feedback_attachment"]` in both early-return and normal ingest paths.

- [ ] **Step 1: Write failing ingest summary test**

Add this test to `tests/v1_3_acceptance/test_h3_feedback_parsing.py`:

```python
def test_ingest_includes_v5_feedback_attachment_summary_without_unblocking_learning(tmp_path, monkeypatch):
    import tools.feedback_ingest as fi
    from engine.v5 import V5FeedbackAttachment, run_v5_snapshot

    case_dir = tmp_path / "C-TEST-INGEST-ATTACH"
    case_dir.mkdir()
    (case_dir / "feedback.md").write_text("反馈：[S-ATTACH-001] [y]", encoding="utf-8")
    snapshot = run_v5_snapshot({"case_id": "C-TEST-INGEST-ATTACH", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})
    (case_dir / "case.run.json").write_text(snapshot.to_json(), encoding="utf-8")
    (case_dir / "case.feedback-attachment.json").write_text(
        V5FeedbackAttachment.from_run_snapshot(snapshot).to_json(),
        encoding="utf-8",
    )
    monkeypatch.setattr(fi, "find_case_dir", lambda case_id: case_dir)

    result = fi.ingest("C-TEST-INGEST-ATTACH", dry_run=True)

    assert result.skipped_no_index is True
    assert result.learning_sample_count == 0
    assert result.phase_a_learning_summary["v5_feedback_attachment"]["status"] == "ok"
    assert result.phase_a_learning_summary["v5_feedback_attachment"]["run_id"] == snapshot.run_id
```

- [ ] **Step 2: Run ingest summary test to verify it fails**

Run:

```bash
pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_ingest_includes_v5_feedback_attachment_summary_without_unblocking_learning -q
```

Expected: FAIL because `phase_a_learning_summary` does not contain `v5_feedback_attachment`.

- [ ] **Step 3: Wire helper into `ingest()`**

In `tools/feedback_ingest.py`, after:

```python
    case_dir = find_case_dir(case_id)
    full_case_id = case_dir.name
```

add:

```python
    v5_feedback_attachment_summary = _validate_v5_feedback_attachment(case_dir, full_case_id)
```

In the early-return branch where `IngestResult(... phase_a_learning_summary={"v5_prediction_feedback": prediction_feedback_summary}, ...)` is built, replace that summary with:

```python
phase_a_learning_summary={
    "v5_prediction_feedback": prediction_feedback_summary,
    "v5_feedback_attachment": v5_feedback_attachment_summary,
},
```

In the normal result branch where `phase_a_learning_summary` is built, add the same key:

```python
phase_a_learning_summary={
    **phase_a_learning_summary,
    "v5_prediction_feedback": prediction_feedback_summary,
    "v5_feedback_attachment": v5_feedback_attachment_summary,
},
```

Do not alter `feedback_count`, `rule_count`, `learning_sample_count`, or `_apply_rule_verdicts()` behavior.

- [ ] **Step 4: Run ingest summary test to verify it passes**

Run:

```bash
pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_ingest_includes_v5_feedback_attachment_summary_without_unblocking_learning -q
```

Expected: PASS.

---

### Task 3: Verify targeted feedback ingest behavior

**Files:**
- No further code changes expected.
- Test: `tests/v1_3_acceptance/test_h3_feedback_parsing.py`, `tests/v5/test_v5_contracts.py`, `tests/v5/test_render_report_v6.py`

**Interfaces:**
- Consumes: Task 1 and Task 2 implementation.
- Produces: verification evidence for completion.

- [ ] **Step 1: Run focused H3 tests**

Run:

```bash
pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py -q
```

Expected: PASS.

- [ ] **Step 2: Run v5 contract and render regression tests**

Run:

```bash
pytest tests/v5/test_v5_contracts.py tests/v5/test_render_report_v6.py -q
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
pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py tests/v5/test_v5_contracts.py tests/v5/test_render_report_v6.py tests/test_project_metadata.py -q
```

Expected: PASS.

---

## Risk Points

1. `run_v5_snapshot()` is moderately expensive because it loads production rules. The new tests use only three snapshot constructions; keep them targeted.
2. `feedback_ingest.ingest()` currently has an early-return path when `statement_records.json` is absent. The attachment summary must be added to that branch too.
3. The helper must not raise for missing/invalid attachment files. All attachment problems are summary-only.
4. Sorting by `st_mtime` makes multiple attachment files deterministic enough for local operation; this is acceptable for the current minimal proof slice.

## Self-Review

- Spec coverage: Tasks cover helper, summary wiring, missing/invalid/mismatch/ok states, and verification.
- Placeholder scan: No `TBD`, `TODO`, or unspecified implementation steps remain.
- Type consistency: `_validate_v5_feedback_attachment()` returns the exact summary shape specified in the design and consumed by tests.
