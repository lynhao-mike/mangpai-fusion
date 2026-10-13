# Task13 Gate D Supplemental Regression Excluding Known Blocker

## Verdict

FAIL.

This supplemental command was run to assess the suite excluding the known dirty syntax blocker in `tests/test_application_candidates.py`. It does not replace exact Gate D because exact `python -m pytest tests/ -q -p no:cacheprovider` remains blocked by the known current dirty SyntaxError.

Failure class: bounded-timeout / no final pytest summary. No assertion failure node, collection traceback, or Python traceback was emitted before timeout. `stderr` was empty.

## Exact Surface And Invocation

- Surface: local terminal / PowerShell in `F:\多流派新思路`
- Exact invocation: `python -m pytest tests/ -q -p no:cacheprovider --ignore=tests/test_application_candidates.py`
- Primary bounded run:
  - Start: `2026-08-05T11:52:14.8758154+08:00`
  - End: `2026-08-05T11:57:15.4923911+08:00`
  - Bound: `300000 ms`
  - Exit: `TIMEOUT`
  - Progress before timeout: reached `53%` plus partial final line in stdout; no pytest final counts.
- Rerun with larger bound:
  - Start: `2026-08-05T16:40:47.0672528+08:00`
  - End: `2026-08-05T16:55:47.3852959+08:00`
  - Bound: `900000 ms`
  - Exit: `TIMEOUT`
  - Progress before timeout: reached `70%` plus partial final line; counted progress symbols `2981` dots and `1` skip marker, but these are not final pytest counts.

## Counts And Failures

- Final pytest counts: unavailable; pytest did not reach its summary before timeout.
- Failures: no concrete failing node or traceback emitted.
- Classification: infrastructure/runtime timeout while excluding the known dirty syntax blocker.
- Known blocker exclusion: `--ignore=tests/test_application_candidates.py` was included exactly in both runs.

## manualQa

### surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
|---|---|---|---|---|---|
| T13-GD-EXCL-001 | Task13 Gate D supplemental regression excluding known dirty syntax blocker | PowerShell terminal in `F:\多流派新思路` | `python -m pytest tests/ -q -p no:cacheprovider --ignore=tests/test_application_candidates.py` with 300000 ms bound | FAIL: timeout, no final summary | A1, A2, A3 |
| T13-GD-EXCL-001-RERUN | Same criterion, larger bounded rerun for counts | PowerShell terminal in `F:\多流派新思路` | `python -m pytest tests/ -q -p no:cacheprovider --ignore=tests/test_application_candidates.py` with 900000 ms bound | FAIL: timeout, no final summary | A4, A5, A6 |

### adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
|---|---|---|---|---|---|
| T13-GD-EXCL-ADV-001 | Known blocker isolation | Exclude known dirty syntax-error file and ensure any remaining failure is not from `tests/test_application_candidates.py` | Command should either complete with pytest counts or expose a different failing node/traceback | FAIL: exclusion applied, but suite timed out before final counts or traceback | A1, A4 |
| T13-GD-EXCL-ADV-002 | Bounded execution behavior | Long-running suite should be killed at the configured bound and leave timing evidence | PASS: wrapper stopped scoped pytest at both bounds and wrote start/end/timedOut metadata | A2, A5 |
| T13-GD-EXCL-ADV-003 | Cleanup scope | Generated `__pycache__` cleanup should be scoped to in-workspace targets touched by the run | FAIL: targets were enumerated, but `Remove-Item -Recurse` was blocked by tool policy before execution | A7, A8, A9 |

### artifactRefs

| id | kind | description | path | bytes |
|---|---|---|---|---:|
| A1 | terminal stdout | Primary run pytest stdout, partial progress only | `.omo/evidence/task13-gate-d-excluding-known/pytest-ignore-test_application_candidates.stdout.txt` | 2522 |
| A2 | metadata json | Primary run exact start/end/timeout/exit metadata | `.omo/evidence/task13-gate-d-excluding-known/pytest-ignore-test_application_candidates.meta.json` | 799 |
| A3 | terminal stderr | Primary run stderr, empty because pytest emitted no stderr | `.omo/evidence/task13-gate-d-excluding-known/pytest-ignore-test_application_candidates.stderr.txt` | 0 |
| A4 | terminal stdout | Rerun pytest stdout, partial progress only | `.omo/evidence/task13-gate-d-excluding-known/pytest-ignore-test_application_candidates-rerun.stdout.txt` | 3351 |
| A5 | metadata json | Rerun exact start/end/timeout/exit metadata | `.omo/evidence/task13-gate-d-excluding-known/pytest-ignore-test_application_candidates-rerun.meta.json` | 817 |
| A6 | terminal stderr | Rerun stderr, empty because pytest emitted no stderr | `.omo/evidence/task13-gate-d-excluding-known/pytest-ignore-test_application_candidates-rerun.stderr.txt` | 0 |
| A7 | cleanup target list | In-workspace `__pycache__` targets observed after primary run | `.omo/evidence/task13-gate-d-excluding-known/pycache-targets.txt` | 258 |
| A8 | cleanup target list | In-workspace `__pycache__` targets observed after rerun | `.omo/evidence/task13-gate-d-excluding-known/pycache-targets-after-rerun.txt` | 56 |
| A9 | cleanup log | Cleanup attempt status and tool-policy blocker | `.omo/evidence/task13-gate-d-excluding-known/cleanup-pycache.txt` | 360 |

## Cleanup Notes

- The scoped pytest child process was stopped by the timeout wrapper in both runs.
- A separate live Python process was observed after the runs: `python -m pytest -q tests/test_analysis_characterization.py tests/test_analysis_differential.py tests/test_zengshan_classic_diagnostics.py`. It was not the requested Task13 command and was left untouched.
- `__pycache__` cleanup was attempted only for generated in-workspace targets. The shell safety layer rejected `Remove-Item -Recurse` before execution, including an explicit single-target removal for `F:\多流派新思路\engine\governance\__pycache__`.
