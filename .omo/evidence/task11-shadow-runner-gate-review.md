# Task11 Shadow Runner Gate Review

Review date: 2026-08-04
Role: final gate / AdversarialVerify, read-only for product and tests
Scope: Task11 shadow runner only

## Verdict

verdict: confirmed
confidence: high

Functional behavior is confirmed, including the corrected unknown-school and unknown-capability QA assertions. Cleanup/evidence hygiene is now independently verified clean: the exact pyc path is absent, the exact `__pycache__` directory is absent, the refreshed path-check artifacts say `False`, the final process-check artifact is empty, and no live `python.exe` command line matched the Task11 QA harness or focused Task11 test.

No product-code, test-code, or evidence-cleanup blocker remains.

## Evidence Reviewed

- Code-review report: `.omo/evidence/task11-shadow-runner-code-review.md`
  - Fresh checks recorded: focused 6 passed; plan command 94 passed; governance joint 193 passed; compatibility 333 passed; Ruff pass; Ruff format pass; no-excuse pass; pure LOC 242/184/55/233.
  - Status: WATCH / APPROVE, no blockers.
- Final QA report: `.omo/evidence/task11-shadow-runner-manual-qa.md`
  - Final verdict PASS.
  - Counts: 16/16 fresh rerun scenario exits 0.
  - Corrected adversarial expectations recorded for unknown legacy school and absent exact capability.
  - Refreshed cleanup evidence records exact pyc path and `__pycache__` directory as absent.
- Sampled corrected QA transcripts:
  - `.omo/evidence/task11-shadow-runner-manual-qa/scenario-unknown_school-rerun.txt`
  - `.omo/evidence/task11-shadow-runner-manual-qa/scenario-unknown_capability-rerun.txt`
  - `.omo/evidence/task11-shadow-runner-manual-qa/scenario-success_full_trace-rerun.txt`
  - `.omo/evidence/task11-shadow-runner-manual-qa/scenario-stale_state_two_processes-rerun.txt`
  - `.omo/evidence/task11-shadow-runner-manual-qa/scenario-serializable_canonical-rerun.txt`
- Scoped current status:
  - Task11 product/test files remain untracked as already disclosed.
  - QA evidence/report artifacts are untracked as expected.
  - No broad rerun was performed because the request asked not to rerun broadly unless current state changed; current product/test status did not show a new tracked modification signal beyond the known untracked Task11 state.

## Adversarial Classes

- success path / seven-gate trace: confirmed. `scenario-success_full_trace-rerun.txt` reports `status=ok`, `decision=consensus`, gates `eligibility, temporal, evidence, independence, counterevidence, applicability, decision`, and a result digest.
- unknown legacy school: confirmed. `scenario-unknown_school-rerun.txt` reports `status=ok`, `decision=abstain`, issue `UNSUPPORTED_LEGACY_CLAIM`. This matches the adjudicated boundary: adapter-stage unknown legacy school need not emit exact `SCHOOL.UNKNOWN`.
- absent exact peer capability: confirmed. `scenario-unknown_capability-rerun.txt` reports one admitted `yang_qingjuan` claim, final `abstain`, and rejection at `applicability`. This matches design 8.6 full five-dimensional role lookup.
- fact conflict: confirmed by final QA report and code-review evidence as `fail_closed`, no arbitration trace, issue `ARBITRATION.FACT_CONFLICT`.
- no target year / liunian trigger: confirmed by final QA report as no `chart.liunian`, inactive trigger with `missing_required_fact`.
- Ditiansui exclusion: confirmed by final QA report as excluded refs and no arena claim.
- registry/input mutation: confirmed by final QA report as request/dependency objects unchanged.
- stale_state: confirmed. `scenario-stale_state_two_processes-rerun.txt` reports two fresh subprocess exits 0 and identical digest `227985ce9ea79dc1994fe831e3522928dc111292d941d4becd3d58f72f96684a`.
- dirty_worktree: mostly confirmed. Final QA scoped status records only Task11/evidence artifacts in its scope. Current scoped status additionally includes this code-review artifact and still shows the same Task11 untracked product/test state.
- misleading_success_output: confirmed. Final QA aggregate `scenario-run-summary-rerun.txt` records every rerun scenario exit as 0, and sampled scenario files contain JSON assertions rather than stdout-only success text.
- cleanup: confirmed. Exact `Test-Path` checks for `.omo/evidence/task11-shadow-runner-manual-qa/__pycache__/harness.cpython-314.pyc` and `.omo/evidence/task11-shadow-runner-manual-qa/__pycache__` both returned `False`; refreshed `pyc-test-path-final.txt` and `pycache-dir-test-path-final.txt` both contain `False`; `process-check-final.txt` is empty; live `python.exe` process scan found no Task11 QA harness or focused Task11 test command line.

## Lossy Trace Watch Adjudication

The code-review WATCH item on a lossy public arbitration envelope remains non-blocking for Task11.

Reason:
- Task11-required shadow surface has version/digest/gate trace/issues coverage sufficient for this wave:
  - `GovernanceShadowResult` contains `schema_version`, `runner_version`, fact snapshot digests, input digest, claim traces, unavailable/excluded refs, trigger/composition results, arbitration trace, issues, and `result_digest`.
  - `ShadowArbitrationTrace` contains decision, arbitration `content_digest`, retained claim IDs, and gate trace.
  - `shadow_result_digest()` binds the public canonical result.
  - Success QA transcript confirms digest and full seven gate names.
- The missing deeper arbitration internals are a downstream auditability risk, not a current Task11 gate blocker, because the underlying arbitration digest binds those internals and no Wave2 consumer is in scope here.

## Repro

No broad tests rerun by this gate. Repro commands used:

```powershell
git status --short -- engine/application/governance_shadow_runner.py engine/application/governance_shadow_types.py engine/application/governance_shadow_school_views.py tests/application/test_governance_shadow_runner.py engine/governance/__init__.py .omo/evidence/task11-shadow-runner-code-review.md .omo/evidence/task11-shadow-runner-manual-qa.md .omo/evidence/task11-shadow-runner-manual-qa
Get-Content -LiteralPath .omo\evidence\task11-shadow-runner-manual-qa.md -Raw
Get-Content -LiteralPath .omo\evidence\task11-shadow-runner-manual-qa\scenario-run-summary-rerun.txt -Raw
Get-Content -LiteralPath .omo\evidence\task11-shadow-runner-manual-qa\scenario-unknown_school-rerun.txt -Raw
Get-Content -LiteralPath .omo\evidence\task11-shadow-runner-manual-qa\scenario-unknown_capability-rerun.txt -Raw
Get-ChildItem -LiteralPath .omo\evidence\task11-shadow-runner-manual-qa\__pycache__ -Force -ErrorAction SilentlyContinue
Test-Path -LiteralPath .omo\evidence\task11-shadow-runner-manual-qa\__pycache__\harness.cpython-314.pyc
Test-Path -LiteralPath .omo\evidence\task11-shadow-runner-manual-qa\__pycache__
Get-Content -LiteralPath .omo\evidence\task11-shadow-runner-manual-qa\pyc-test-path-final.txt -Raw
Get-Content -LiteralPath .omo\evidence\task11-shadow-runner-manual-qa\pycache-dir-test-path-final.txt -Raw
Get-Content -LiteralPath .omo\evidence\task11-shadow-runner-manual-qa\process-check-final.txt -Raw
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object { $_.CommandLine -like '*task11-shadow-runner-manual-qa*' -or $_.CommandLine -like '*test_governance_shadow_runner*' } | Select-Object ProcessId,CommandLine
```

## Blockers

None.

## Required Product/Test Changes

None.
