# Run-Centric Proof Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the smallest run-centric vertical slice that proves case input can produce a stable run snapshot, artifact binding, case manifest, report, decision run, and feedback attachment path.

**Architecture:** Keep the clean target model: Run is the first lifecycle object; reports and case files are artifacts bound to a run. Ponytail constraint: do not move directories or invent a new application layer; extend the existing v5 preprod slice with one manifest write and one regression test.

**Tech Stack:** Python stdlib `pathlib` / `json`, existing `engine.v5.domain.V5RunSnapshot`, existing `engine.v5.domain.V5CaseManifest`, existing `engine.v5.preprod.render_v6_preprod_case`, pytest.

## Global Constraints

- Correct target model beats tiny diff, but implementation must stay minimal.
- No new dependencies.
- No directory move in this slice.
- `engine` owns run snapshot contracts; `tools` only orchestrates CLI.
- `cases/` is a fact container plus binding, not inference truth.
- `reports/` is a derived view, not a fact source.
- Verification must include focused v5 tests and project metadata tests.

---

## File Structure

- Modify: `engine/v5/preprod.py`
  - Responsibility: v6 preprod application service that turns `input.md` into report/json/run artifacts.
  - Add only manifest persistence beside existing run snapshot persistence.
- Modify: `tests/v5/test_render_report_v6.py`
  - Responsibility: regression test for the vertical slice artifact set.
  - Assert generated case manifest binds the generated run snapshot.

---

### Task 1: Persist Case Manifest from Run Snapshot

**Files:**
- Modify: `engine/v5/preprod.py:20`
- Modify: `engine/v5/preprod.py:250-260`
- Test: `tests/v5/test_render_report_v6.py:16-55`

**Interfaces:**
- Consumes: `V5RunSnapshot.from_output(output, artifact_bindings=artifact_bindings) -> V5RunSnapshot`
- Produces: `manifest.json` in the case directory using `V5CaseManifest.from_run_snapshot(snapshot, case_path=...)`

- [ ] **Step 1: Write the failing test**

Add these assertions to `test_render_report_v6_generates_report_and_v5_json` after loading `run_snapshot`:

```python
manifest_path = CASE_INPUT.parent / "manifest.json"
manifest = V5CaseManifest.from_json(manifest_path.read_text(encoding="utf-8"))
assert manifest.case_id == run_snapshot.case_id
assert manifest.active_run_id == run_snapshot.run_id
assert run_snapshot.run_id in manifest.run_ids
assert manifest.artifact_paths["run_json"].endswith(rendered_run_json.as_posix())
```

Also import `V5CaseManifest`:

```python
from engine.v5 import V5CaseManifest, V5RunSnapshot
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/v5/test_render_report_v6.py::test_render_report_v6_generates_report_and_v5_json -q`

Expected: FAIL with `FileNotFoundError` for `manifest.json`.

- [ ] **Step 3: Write minimal implementation**

In `engine/v5/preprod.py`, import `V5CaseManifest`:

```python
from engine.v5.domain import V5CaseManifest, V5RunSnapshot
```

Replace direct run snapshot write with a local `snapshot` variable and manifest write:

```python
artifact_bindings = {
    "report": _display_path(report_file, workspace_root=root),
    "v5_json": _display_path(json_file, workspace_root=root),
    "run_json": _display_path(run_json_file, workspace_root=root),
    "decision_run_json": _display_path(decision_json_file, workspace_root=root),
    "input": _display_path(input_file, workspace_root=root),
    "feedback": _display_path(feedback_path, workspace_root=root),
}
snapshot = V5RunSnapshot.from_output(output, artifact_bindings=artifact_bindings)
run_json_file.write_text(snapshot.to_json(), encoding="utf-8")
(case_dir / "manifest.json").write_text(
    V5CaseManifest.from_run_snapshot(
        snapshot,
        case_path=_display_path(case_dir, workspace_root=root),
    ).to_json(),
    encoding="utf-8",
)
```

- [ ] **Step 4: Run focused test**

Run: `pytest tests/v5/test_render_report_v6.py::test_render_report_v6_generates_report_and_v5_json -q`

Expected: PASS.

---

### Task 2: Verify Slice and Boundaries

**Files:**
- No further code files unless tests reveal a real failure.

**Interfaces:**
- Consumes: existing pytest suite.
- Produces: evidence that the run-centric slice did not break report bridge or metadata contracts.

- [ ] **Step 1: Run v5 focused tests**

Run: `pytest tests/v5 -q`

Expected: PASS.

- [ ] **Step 2: Run project metadata test**

Run: `pytest tests/test_project_metadata.py -q`

Expected: PASS.

- [ ] **Step 3: Request code review**

Review focus:

```text
Check whether the new manifest write preserves the target model:
- Run snapshot remains the structured truth for inference output.
- Case manifest only binds artifacts and active run.
- No tool-level domain logic was added.
- No compatibility shim or new abstraction was introduced.
```

---

## Geju Direction Summary

## Thesis
The right target model is not a cleaner script warehouse; it is a run-centric inference factory. This slice should prove that one `Run` can bind report, JSON, decision run, input, feedback, and case manifest without moving the whole repo.

## Confidence
- **Confidence level**: medium-high
- **Why not certain**: existing v5 contracts are already partly landed, so the remaining risk is whether downstream feedback tools actually consume the manifest or still depend on ad-hoc case files.

## The Trap
- **Inherited constraint**: preserve every old path and script as if it were architecture.
- **Is it real?**: partially.
- **Why**: paths such as `cases/` and `reports/` are real product contracts; old pipeline centrality and tool-owned workflow truth are inertia.

## High-格局 Direction
`Run` owns inference truth; case/report/prediction/feedback are bound artifacts. Do not make `tools/` smarter; make the run snapshot and case manifest more explicit.

## Frame-Opening Move
- **Move used**: zero-legacy thought experiment + tasteful deletion.
- **What it reveals**: no greenfield design would use Markdown reports or CLI scripts as the source of truth.

## Bold Takes
- Delete the idea that report Markdown is the result; it is only a view.
- Merge artifact binding into the run snapshot instead of scattering paths across tools.
- Split case fact storage from run output storage via `manifest.json`.
- Do not preserve `engine/pipeline.py` as the long-term center; keep it as facade only.

## Options
| Option | What it optimizes | Cost | Verdict |
|--------|-------------------|------|---------|
| Conservative path | Smaller diff around existing report writer | Keeps case/report as implicit truth | reject |
| Clean target | Physical knowledge/inference/artifacts/operations directories | Big migration before proof | not now |
| Staged clean path | Run snapshot plus case manifest in current directories | Temporary old directory names | recommended |

## What Not To Do
- Do not add a new `operations` package for one function.
- Do not add adapters around every old caller.
- Do not parse reports to recover run state.
- Do not move directories before the vertical slice is verified.

## First Proof Point
A single case render produces `*.run.json` plus `cases/<case_id>/manifest.json`, and the manifest active run matches the run snapshot.

## Falsifier
If feedback ingestion cannot attach to `run_id` / statement / prediction artifacts without reading report Markdown as truth, this slice is insufficient and the target contract needs another field before wider migration.

---

## Self-Review

- Spec coverage: covers geju target model, writing plan, ponytail minimum implementation, code review checkpoint, and verification commands.
- Placeholder scan: no TBD / TODO / implement later placeholders.
- Type consistency: `V5CaseManifest`, `V5RunSnapshot`, `artifact_bindings`, `run_json` names match existing v5 domain contracts.
