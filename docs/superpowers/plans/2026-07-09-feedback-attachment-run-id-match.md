# Feedback Attachment Run ID Match Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `tools.feedback_ingest._validate_v5_feedback_attachment()` select the `*.run.json` whose `V5RunSnapshot.run_id` matches the chosen `V5FeedbackAttachment.run_id`, preventing false mismatches in multi-run case directories.

**Architecture:** Keep the existing single helper in `tools/feedback_ingest.py`; change only its run snapshot selection strategy. The helper still returns the same summary shape and remains read-only, summary-only, and non-blocking for `ingest()`.

**Tech Stack:** Python 3, pathlib/json stdlib, pytest, existing `engine.v5.domain` contracts.

## Global Constraints

- Do not extend `V5FeedbackAttachment` schema.
- Do not use `V5CaseManifest` to find artifact bindings.
- Do not parse report Markdown.
- Do not change statement feedback, prediction feedback, Dynamic Confidence, or rule-learning logic.
- Do not add a service/repository/helper file.
- Keep the existing summary schema unchanged.
- Missing / invalid / mismatch states remain summary-only and must not block ingest.

---

## File Structure

- Modify: `tools/feedback_ingest.py`
  - Keep `_validate_v5_feedback_attachment(case_dir: pathlib.Path, full_case_id: str) -> dict[str, Any]` as the public internal helper.
  - Add a tiny internal loop in that helper to select a run snapshot by `attachment.run_id`.
  - Do not change `ingest()` call sites.
- Modify: `tests/v1_3_acceptance/test_h3_feedback_parsing.py`
  - Add focused tests for multi-run exact match and no matching run ID.

---

### Task 1: Select run snapshot by attachment.run_id

**Files:**
- Modify: `tools/feedback_ingest.py`
- Modify: `tests/v1_3_acceptance/test_h3_feedback_parsing.py`

**Interfaces:**
- Consumes: `_validate_v5_feedback_attachment(case_dir: pathlib.Path, full_case_id: str) -> dict[str, Any]`.
- Consumes: `V5FeedbackAttachment.from_json(value: str) -> V5FeedbackAttachment`.
- Consumes: `V5RunSnapshot.from_json(value: str) -> V5RunSnapshot`.
- Produces: same summary dict shape as before, with `run_snapshot_path` pointing to the matching `*.run.json` when `snapshot.run_id == attachment.run_id`.

- [ ] **Step 1: Write failing multi-run tests**

Add these tests to the end of `tests/v1_3_acceptance/test_h3_feedback_parsing.py`:

```python
def test_v5_feedback_attachment_validation_selects_matching_run_id_in_multi_run_case(tmp_path):
    from dataclasses import replace

    from engine.v5 import V5FeedbackAttachment, run_v5_snapshot
    from tools.feedback_ingest import _validate_v5_feedback_attachment

    case_dir = tmp_path / "C-TEST-ATTACH-MULTIRUN"
    case_dir.mkdir()
    right = run_v5_snapshot({"case_id": "C-TEST-ATTACH-MULTIRUN", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})
    wrong = replace(right, run_id="run-wrong-newer")
    right_path = case_dir / "right.run.json"
    wrong_path = case_dir / "wrong.run.json"
    attachment_path = case_dir / "case.feedback-attachment.json"
    right_path.write_text(right.to_json(), encoding="utf-8")
    wrong_path.write_text(wrong.to_json(), encoding="utf-8")
    attachment_path.write_text(V5FeedbackAttachment.from_run_snapshot(right).to_json(), encoding="utf-8")
    # Make the wrong snapshot newer; old implementation picked this and reported mismatch.
    wrong_path.touch()

    summary = _validate_v5_feedback_attachment(case_dir, "C-TEST-ATTACH-MULTIRUN")

    assert summary["status"] == "ok"
    assert summary["run_id"] == right.run_id
    assert summary["run_snapshot_path"] == right_path.as_posix()
    assert summary["issues"] == []


def test_v5_feedback_attachment_validation_reports_no_matching_run_id(tmp_path):
    from dataclasses import replace

    from engine.v5 import V5FeedbackAttachment, run_v5_snapshot
    from tools.feedback_ingest import _validate_v5_feedback_attachment

    case_dir = tmp_path / "C-TEST-ATTACH-NO-RUN-MATCH"
    case_dir.mkdir()
    snapshot = run_v5_snapshot({"case_id": "C-TEST-ATTACH-NO-RUN-MATCH", "pillars": ["甲子", "乙丑", "丙寅", "丁卯"]})
    wrong = replace(snapshot, run_id="run-not-the-attachment")
    (case_dir / "wrong.run.json").write_text(wrong.to_json(), encoding="utf-8")
    (case_dir / "case.feedback-attachment.json").write_text(
        V5FeedbackAttachment.from_run_snapshot(snapshot).to_json(),
        encoding="utf-8",
    )

    summary = _validate_v5_feedback_attachment(case_dir, "C-TEST-ATTACH-NO-RUN-MATCH")

    assert summary["status"] == "mismatch"
    assert summary["attachment_path"] == (case_dir / "case.feedback-attachment.json").as_posix()
    assert summary["run_snapshot_path"] == ""
    assert summary["case_id"] == "C-TEST-ATTACH-NO-RUN-MATCH"
    assert summary["run_id"] == snapshot.run_id
    assert summary["target_counts"] == {
        "claims": len(snapshot.claims),
        "predictions": len(snapshot.prediction_ledger.predictions),
        "signals": len(snapshot.learning_signals),
    }
    assert summary["issues"] == [
        f"run snapshot for feedback attachment run_id not found: {snapshot.run_id}"
    ]
```

- [ ] **Step 2: Run new tests to verify they fail**

Run:

```bash
pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_selects_matching_run_id_in_multi_run_case tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_reports_no_matching_run_id -q
```

Expected: first test FAILS because current code picks the newest `wrong.run.json`; second test may fail with old mismatch wording/path behavior. At least one failure must prove the old behavior.

- [ ] **Step 3: Implement run_id selection in the helper**

In `tools/feedback_ingest.py`, replace the current run snapshot selection block inside `_validate_v5_feedback_attachment()`.

Current shape:

```python
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
```

Replace it with:

```python
    try:
        attachment = V5FeedbackAttachment.from_json(attachment_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return {
            "status": "invalid",
            "attachment_path": attachment_path.as_posix(),
            "run_snapshot_path": "",
            "case_id": full_case_id,
            "run_id": "",
            "target_counts": {"claims": 0, "predictions": 0, "signals": 0},
            "issues": [f"invalid v5 feedback attachment payload: {exc}"],
        }

    run_snapshots = sorted(case_dir.glob("*.run.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not run_snapshots:
        summary = _empty_v5_attachment_summary("missing", case_id=full_case_id, issue="run snapshot not found")
        summary["attachment_path"] = attachment_path.as_posix()
        summary["case_id"] = attachment.case_id
        summary["run_id"] = attachment.run_id
        summary["target_counts"] = {
            "claims": len(attachment.target_claim_ids),
            "predictions": len(attachment.target_prediction_ids),
            "signals": len(attachment.target_signal_ids),
        }
        return summary

    snapshot = None
    run_snapshot_path: pathlib.Path | None = None
    invalid_run_issues: list[str] = []
    for candidate in run_snapshots:
        try:
            candidate_snapshot = V5RunSnapshot.from_json(candidate.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            invalid_run_issues.append(f"invalid run snapshot {candidate.as_posix()}: {exc}")
            continue
        if candidate_snapshot.run_id == attachment.run_id:
            snapshot = candidate_snapshot
            run_snapshot_path = candidate
            break

    if snapshot is None or run_snapshot_path is None:
        return {
            "status": "mismatch",
            "attachment_path": attachment_path.as_posix(),
            "run_snapshot_path": "",
            "case_id": attachment.case_id,
            "run_id": attachment.run_id,
            "target_counts": {
                "claims": len(attachment.target_claim_ids),
                "predictions": len(attachment.target_prediction_ids),
                "signals": len(attachment.target_signal_ids),
            },
            "issues": [
                f"run snapshot for feedback attachment run_id not found: {attachment.run_id}",
                *invalid_run_issues,
            ],
        }
```

Keep the existing `issues` construction after this block unchanged, except `run_snapshot_path` is now guaranteed to be a `pathlib.Path` for the success/mismatch validation path.

- [ ] **Step 4: Run new tests to verify they pass**

Run:

```bash
pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_selects_matching_run_id_in_multi_run_case tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_v5_feedback_attachment_validation_reports_no_matching_run_id -q
```

Expected: PASS.

- [ ] **Step 5: Run focused regression tests**

Run:

```bash
pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add tools/feedback_ingest.py tests/v1_3_acceptance/test_h3_feedback_parsing.py
git commit -m "fix: match feedback attachment to run snapshot by run id"
```

Expected: commit created.

---

## Verification

After Task 1, run:

```bash
pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py tests/v5/test_v5_contracts.py tests/v5/test_render_report_v6.py tests/test_project_metadata.py -q
```

Expected: PASS.

---

## Risk Points

1. The helper must parse attachment before selecting run snapshot; invalid attachment should remain `status=invalid`.
2. Invalid run snapshot files should not block scanning other run snapshots.
3. The summary schema must not grow fields.
4. `ingest()` behavior must remain unchanged; only the helper's snapshot selection changes.

## Self-Review

- Spec coverage: The plan covers exact run_id selection, no matching run_id, unchanged schema, and final regression tests.
- Placeholder scan: No `TBD`, `TODO`, or unspecified implementation steps remain.
- Type consistency: `_validate_v5_feedback_attachment()` keeps the same signature and summary shape.
