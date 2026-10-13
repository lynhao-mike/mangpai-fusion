# Task12 Static Isolation Manual QA Retry2

Conclusion: PASS
Scenario count: 15 total = 9 surfaceEvidence + 6 adversarialCases.
Date: 2026-08-05 Asia/Shanghai.
Scope: current Wave1 Task12 static isolation implementation. No product or test files edited.

## manualQa.surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
|---|---|---|---|---|---|
| S01 | relative imports `..application`, `..infrastructure`, `...tools` | bounded Python CLI probe | `PYTHONPATH=F:\多流派新思路 python .\.omo\evidence\task12-static-isolation-manual-qa\qa_probe_retry2.py` row S01 | PASS | A1,A2 |
| S02 | active report/feedback entrypoints include `output_linter`, `domain_analysis_cli`, `batch_review`, `promote_expert_weight_feedback`, `domain_feedback` and are shadow-runner-clean | bounded Python CLI probe | same probe row S02 | PASS | A1,A2 |
| S03 | `FactSnapshot` direct + `as` alias builders/constructors and future school-view adapter discovery | bounded Python CLI probe | same probe row S03 | PASS | A1,A2 |
| S04 | `datetime`/`date`/`time` direct and alias forms including `dt.now()` and `now()` | bounded Python CLI probe | same probe row S04 | PASS | A1,A2 |
| S05 | YAML drive, UNC, `/opt/...` absolute paths | bounded Python CLI probe | same probe row S05 | PASS | A1,A2 |
| S06 | benign controls against false positives | bounded Python CLI probe | same probe row S06 | PASS | A1,A2 |
| S07 | exact Task12 focused suite | pytest CLI | `PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/test_architecture_dependencies.py tests/governance/test_static_isolation.py tests/yang_marriage/test_static_isolation.py -q -p no:cacheprovider` | PASS: 34 passed, 1 known warning | A3,A4 |
| S08 | Task11 compatibility suite | pytest CLI | `PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/application/test_governance_shadow_runner.py tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q -p no:cacheprovider` | PASS: 94 passed, 1 known warning | A5,A6 |
| S09 | cleanup/process accounting | OS/filesystem inspection | `Get-CimInstance Win32_Process ...`; pycache scan; cleanup status JSON write | PASS | A7 |

## manualQa.adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
|---|---|---|---|---|---|
| A01 | malformed Python/YAML static inputs | malformed_input | scanner fails closed with `SyntaxError`/`ParserError`, not silent success | PASS | A1,A2 |
| A02 | existing unrelated dirty worktree | dirty_worktree | QA runs without reset/revert and writes only allowed Task12 evidence paths | PASS | A7 |
| A03 | active entrypoint metadata may drift | stale_state | active entrypoints are loaded from current `META/project-state.json` at runtime | PASS | A1,A2 |
| A04 | green output could hide mismatched actuals | misleading_success_output | each probe row records exact expected and actual values before verdict | PASS | A1 |
| A05 | focused/compatibility flake risk | flaky_tests | current focused exact and Task11 compatibility both rerun successfully in this turn | PASS | A3,A5 |
| A06 | long command/hang risk | hung_or_long_commands | every command used an explicit timeout window; no timeout fired | PASS | A2,A4,A6 |

## manualQa.artifactRefs

| id | kind | description | path |
|---|---|---|---|
| A1 | JSON stdout | Retry2 probe expected/actual/exit matrix, 7 PASS rows | `.omo/evidence/task12-static-isolation-manual-qa/artifacts/retry2-probe.stdout.json` |
| A2 | meta | Retry2 probe invocation and timeout metadata | `.omo/evidence/task12-static-isolation-manual-qa/artifacts/retry2-probe.meta.txt` |
| A3 | pytest stdout | Task12 focused exact result: `34 passed, 1 warning in 6.73s` | `.omo/evidence/task12-static-isolation-manual-qa/artifacts/retry2-pytest-task12-focused.stdout.txt` |
| A4 | meta | Task12 focused invocation and timeout metadata | `.omo/evidence/task12-static-isolation-manual-qa/artifacts/retry2-pytest-task12-focused.meta.txt` |
| A5 | pytest stdout | Task11 compatibility result: `94 passed, 1 warning in 36.38s` | `.omo/evidence/task12-static-isolation-manual-qa/artifacts/retry2-pytest-task11-94.stdout.txt` |
| A6 | meta | Task11 compatibility invocation and timeout metadata | `.omo/evidence/task12-static-isolation-manual-qa/artifacts/retry2-pytest-task11-94.meta.txt` |
| A7 | JSON | Cleanup/process status: no pycache remaining in checked paths; QA temp fixtures removed; one unattributed existing pytest retained | `.omo/evidence/task12-static-isolation-manual-qa/artifacts/retry2-cleanup-status.json` |

## Cleanup

- QA temp fixtures: removed by `qa_probe_retry2.py` (`removed=true`).
- Task-related pycache: removed from `tests/governance`, `tests/yang_marriage`, and `tests/application`; final checked paths show none remaining.
- Task-related Python processes: none left to clean.
- Retained existing/unattributed Python process: PID 35664, command `python -m pytest --ignore=tests/test_web_accountability_browser_e2e.py --ignore=tests/test_web_accountability_e2e.py -q --tb=short`.
- An accidental empty QA directory under `F:\八字分析系统\ziweidoushu\.omo\evidence\task12-static-isolation-manual-qa` was removed; pre-existing evidence files in that other workspace were not touched.
