# Task11 Shadow Runner Manual QA

Date: 2026-08-04
Surface: `engine.application.governance_shadow_runner` public API.
Invocation model: fresh Python CLI process per scenario, using explicit typed `GovernanceShadowRequest`, `GovernanceShadowDependencies`, registries, triggers, and school-view objects from `.omo/evidence/task11-shadow-runner-manual-qa/harness.py`.
Final verdict: PASS

Counts:
- Surface scenarios: 12 PASS, 0 FAIL
- Adversarial/UltraQA scenarios: 12 PASS/ASSESSED, 0 FAIL
- Pytest regression: 1 PASS
- Fresh rerun scenario exits: 16/16 exit 0

Superseded audit history:
- `scenario-unknown_school-superseded-overstrict.txt` preserved the old over-strict assertion requiring invented `SCHOOL.UNKNOWN`.
- `scenario-unknown_capability-superseded-overstrict.txt` preserved the old over-strict assertion requiring eligibility rejection.
- Current authoritative reruns are `scenario-unknown_school-rerun.txt` and `scenario-unknown_capability-rerun.txt`.

## manualQa.surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
|---|---|---|---|---|---|
| SE-01 | success result and full seven-gate trace | Python public API | `python .omo\evidence\task11-shadow-runner-manual-qa\harness.py success_full_trace` | PASS: `status=ok`, `decision=consensus`, gates `eligibility, temporal, evidence, independence, counterevidence, applicability, decision` | A03 |
| SE-02 | one school failure preserving others | Python public API | `python .omo\evidence\task11-shadow-runner-manual-qa\harness.py one_school_failure` | PASS: `ren_fuhong` unavailable, `ziping` retained | A04 |
| SE-03 | fact conflict stops arena | Python public API | `python .omo\evidence\task11-shadow-runner-manual-qa\harness.py fact_conflict` | PASS: `status=fail_closed`, `arbitration=null`, issue `ARBITRATION.FACT_CONFLICT` | A05 |
| SE-04 | deterministic digest under school-view ordering | Python public API | `python .omo\evidence\task11-shadow-runner-manual-qa\harness.py deterministic_ordering` | PASS: canonical output and digest equal | A06 |
| SE-05 | no target year => no liunian facts, trigger inactive | Python public API | `python .omo\evidence\task11-shadow-runner-manual-qa\harness.py no_target_year` | PASS: no `chart.liunian`; trigger inactive with `missing_required_fact` | A07 |
| SE-06 | Ditiansui excluded | Python public API | `python .omo\evidence\task11-shadow-runner-manual-qa\harness.py ditiansui_excluded` | PASS: `legacy-ditiansui` in excluded refs, no Ditiansui claim admitted | A08 |
| SE-07 | no mutation of injected registries/input | Python public API | `python .omo\evidence\task11-shadow-runner-manual-qa\harness.py no_mutation` | PASS: request and dependency objects unchanged | A09 |
| SE-08 | serializable canonical result | Python public API | `python .omo\evidence\task11-shadow-runner-manual-qa\harness.py serializable_canonical` | PASS: JSON round-trip preserves `result_digest` | A10 |
| SE-09 | banned production/report/feedback/learning imports absent | AST check | `python .omo\evidence\task11-shadow-runner-manual-qa\harness.py banned_imports` | PASS: banned import set absent | A11 |
| SE-10 | legacy `run_decision_mvp` and V5 adapter still work | Python public API | `python .omo\evidence\task11-shadow-runner-manual-qa\harness.py legacy_surfaces` | PASS: both legacy traces validate empty | A17 |
| SE-11 | Task11 + legacy regression suite | pytest | `python -m pytest tests/application/test_governance_shadow_runner.py tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q` | PASS: `94 passed, 1 warning in 27.49s` | A20 |
| SE-12 | import surface unchanged/isolated | AST check | PowerShell here-string piped to `python -`, output redirected to artifact | PASS: shadow runner imports governance/application-only orchestration dependencies; legacy surfaces import expected existing modules | A21 |

## manualQa.adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
|---|---|---|---|---|---|
| ADV-01 | malformed public input | malformed_input | typed fail-closed result, no crash | PASS: `FACT_BUILDER.RAW_SOURCE_HASH` | A16 |
| ADV-02 | unknown legacy school | malformed_input | no admitted claim, no winner, `abstain`, explicit typed issue; exact `SCHOOL.UNKNOWN` not required | PASS: `UNSUPPORTED_LEGACY_CLAIM`, `decision=abstain` | A12 |
| ADV-03 | absent exact five-dimensional peer capability | malformed_input | no uniform fallback; claim rejected at applicability; final `abstain` | PASS: applicability gate rejects only admitted claim | A13 |
| ADV-04 | unknown trigger | malformed_input | inactive with closed-domain issue | PASS: `unknown_trigger` | A18 |
| ADV-05 | unknown composition template | malformed_input | unsupported with closed-domain issue | PASS: `COMPOSITION.UNSUPPORTED_TEMPLATE` | A19 |
| ADV-06 | stale state | stale_state | two fresh subprocesses produce same digest | PASS | A22 |
| ADV-07 | dirty worktree | dirty_worktree | preserve shared dirty worktree; only evidence harness/report and QA artifacts added by QA | PASS: scoped status recorded | A23 |
| ADV-08 | hung or long command | hung_or_long_commands | bounded scenario subprocess inside harness for stale-state probe; pytest completed | PASS | A01, A20 |
| ADV-09 | misleading success output | misleading_success_output | evaluate exit code plus JSON assertions, not stdout alone | PASS: aggregate shows every rerun exit 0 | A01 |
| ADV-10 | flaky tests | flaky_tests | deterministic rerun and focused pytest pass | PASS | A06, A20 |
| ADV-11 | cancel/resume | cancel_resume | no public cancel token, checkpoint, async handle, or resume API exists on `run_governance_shadow`; assessed by signature and synchronous CLI surface | ASSESSED PASS: no applicable API surface to probe | A02 |
| ADV-12 | repeated interruptions | repeated_interruptions | no public interrupt/resume protocol beyond OS process termination; assessed by synchronous fresh-process invocation model | ASSESSED PASS: not applicable to this public API | A02 |

## manualQa.artifactRefs

| id | kind | description | path |
|---|---|---|---|
| A01 | aggregate transcript | fresh rerun scenario invocations and exit codes | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\scenario-run-summary-rerun.txt` |
| A02 | QA harness | evidence-only typed public API harness with authoritative assertions | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\harness.py` |
| A03 | CLI transcript | success/full gate trace rerun | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\scenario-success_full_trace-rerun.txt` |
| A04 | CLI transcript | one school failure rerun | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\scenario-one_school_failure-rerun.txt` |
| A05 | CLI transcript | fact conflict rerun | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\scenario-fact_conflict-rerun.txt` |
| A06 | CLI transcript | deterministic ordering rerun | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\scenario-deterministic_ordering-rerun.txt` |
| A07 | CLI transcript | no target year rerun | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\scenario-no_target_year-rerun.txt` |
| A08 | CLI transcript | Ditiansui exclusion rerun | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\scenario-ditiansui_excluded-rerun.txt` |
| A09 | CLI transcript | no mutation rerun | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\scenario-no_mutation-rerun.txt` |
| A10 | CLI transcript | serializable canonical rerun | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\scenario-serializable_canonical-rerun.txt` |
| A11 | CLI transcript | banned imports rerun | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\scenario-banned_imports-rerun.txt` |
| A12 | CLI transcript | unknown school authoritative rerun | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\scenario-unknown_school-rerun.txt` |
| A13 | CLI transcript | unknown capability authoritative rerun | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\scenario-unknown_capability-rerun.txt` |
| A14 | superseded transcript | old unknown-school over-strict failure | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\scenario-unknown_school-superseded-overstrict.txt` |
| A15 | superseded transcript | old unknown-capability over-strict failure | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\scenario-unknown_capability-superseded-overstrict.txt` |
| A16 | CLI transcript | malformed input rerun | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\scenario-malformed_input-rerun.txt` |
| A17 | CLI transcript | legacy surfaces rerun | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\scenario-legacy_surfaces-rerun.txt` |
| A18 | CLI transcript | unknown trigger rerun | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\scenario-unknown_trigger-rerun.txt` |
| A19 | CLI transcript | unsupported composition rerun | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\scenario-unsupported_composition-rerun.txt` |
| A20 | pytest transcript | fresh scoped regression command | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\pytest-task11-legacy-regression-rerun.txt` |
| A21 | AST transcript | import surface rerun | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\import-surface-check-rerun.txt` |
| A22 | CLI transcript | stale-state two subprocesses rerun | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\scenario-stale_state_two_processes-rerun.txt` |
| A23 | git transcript | scoped dirty-worktree status | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\scoped-git-status-rerun.txt` |
| A24 | process transcript | no residual Python process after cleanup | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\process-check-final.txt` |
| A25 | cleanup transcript | exact pyc path absent after cleanup | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\pyc-test-path-final.txt` |
| A26 | cleanup transcript | `__pycache__` directory absent after cleanup | `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\pycache-dir-test-path-final.txt` |

## Cleanup

- No product or test files were edited by this QA rework.
- Old over-strict transcripts preserved as superseded audit history.
- Gate cleanup removed exact generated QA bytecode `F:\多流派新思路\.omo\evidence\task11-shadow-runner-manual-qa\__pycache__\harness.cpython-314.pyc` without importing or rerunning the harness.
- Fresh `Test-Path` for the exact pyc file returned `False` in `pyc-test-path-final.txt`.
- Fresh `Test-Path` for the `__pycache__` directory returned `False` in `pycache-dir-test-path-final.txt`.
- A lingering `python -m pytest` process tree from the earlier environment was recorded in `process-check-rerun.txt`, then terminated as residual test cleanup.
- Final process check artifact `process-check-final.txt` is empty, confirming no live `python.exe` process remained at that check.
- No Wave2/Wave3 work was performed.

## Conclusion

Manual QA PASS. The current public API satisfies the Task11 required surfaces and adversarial contract after correcting the two over-strict QA assertions. Unknown legacy school fails closed by admitting no claim and returning `UNSUPPORTED_LEGACY_CLAIM`; absent exact peer capability fails closed by rejection at applicability and final `abstain`, with no uniform fallback.
