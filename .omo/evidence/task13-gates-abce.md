# Task13 Gate A/B/C/E Manual QA

Date: 2026-08-05 Asia/Shanghai
Workspace: `F:\多流派新思路`
Scope: Wave1 authority plan Task13 Gate A/B/C/E only. No product or test code changes.

## Verdict Summary

| Gate | Verdict | Exit | Counts | Warnings | Artifact | Bytes |
|---|---|---:|---|---:|---|---:|
| A | PASS | 0 | 212 passed, 0 failed, 0 errors, 0 skipped | 1 | `.omo/evidence/task13-gates-abce/gate-a-pytest-r2.log` | 1428 |
| B | PASS | 0 | 333 passed, 0 failed, 0 errors, 0 skipped | 1 | `.omo/evidence/task13-gates-abce/gate-b-pytest-r2.log` | 1655 |
| C | PASS | 0 | 24 passed, 0 failed, 0 errors, 0 skipped | 1 | `.omo/evidence/task13-gates-abce/gate-c-pytest-r2.log` | 1236 |
| E1 | PASS | 0 | `tool registry check passed` | 0 | `.omo/evidence/task13-gates-abce/gate-e-tool-registry-r2.log` | 476 |
| E2 | PASS | 0 | `rule status scan passed` | 0 | `.omo/evidence/task13-gates-abce/gate-e-rule-status-scan-r2.log` | 482 |

Python: `Python 3.14.5` (`.omo/evidence/task13-gates-abce/python-version.txt`, 18 bytes)
pytest: `pytest 8.4.2` (`.omo/evidence/task13-gates-abce/pytest-version.txt`, 17 bytes)
Dirty worktree captured before gates: `.omo/evidence/task13-gates-abce/git-status-short.txt` (86069 bytes)

## manualQa

### surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
|---|---|---|---|---|---|
| gate-a-pytest-r2 | Task13 Gate A governance unit tests | terminal pytest | `python -m pytest tests/governance tests/application/test_governance_fact_builder.py tests/application/test_governance_claim_adapters.py tests/application/test_governance_shadow_runner.py -q -p no:cacheprovider` | PASS | A1 |
| gate-b-pytest-r2 | Task13 Gate B core compatibility tests | terminal pytest | `python -m pytest tests/yang_marriage tests/ren_timing tests/decision/test_staged_arbitration.py tests/predicates/test_ten_god_structures.py tests/test_production_rule_loader.py tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q -p no:cacheprovider` | PASS | B1 |
| gate-c-pytest-r2 | Task13 Gate C architecture and project metadata tests | terminal pytest | `python -m pytest tests/test_architecture_dependencies.py tests/test_project_metadata.py -q -p no:cacheprovider` | PASS | C1 |
| gate-e-tool-registry-r2 | Task13 Gate E formal tool registry check | terminal CLI | `python tools/tool_registry.py --check` | PASS | E1 |
| gate-e-rule-status-scan-r2 | Task13 Gate E formal rule status scan check | terminal CLI | `python tools/rule_status_scan.py --check` | PASS | E2 |

### adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
|---|---|---|---|---|---|
| dirty-worktree-capture | Task13 preserve dirty worktree | dirty | Existing dirty worktree is captured and not reverted. | PASS | M1 |
| bounded-no-hung | Task13 bounded subprocess | hung | Each scoped command records start/end/exit and `timed_out: False`. | PASS | A1, B1, C1, E1, E2 |
| stale-first-run-excluded | ultraqa stale/misleading | stale, misleading | First instrumentation run with missing exit-code capture is not used for verdict; r2 logs carry exit code 0. | PASS | S1, S2 |
| sequential-rerun-consistency | ultraqa flaky | flaky | Rerun counts match the initial completed stdout counts for A/B/C/E. | PASS | S1, S2, A1, B1, C1, E1, E2 |
| formal-entry-confirmed | Gate E formal entry | misleading | Gate E uses repository documented formal entries only: `tool_registry.py --check` and `rule_status_scan.py --check`. | PASS | M2, E1, E2 |

### artifactRefs

| id | kind | description | path |
|---|---|---|---|
| A1 | terminal transcript | Gate A r2 bounded pytest log with exit/count/warning/classification. | `.omo/evidence/task13-gates-abce/gate-a-pytest-r2.log` |
| B1 | terminal transcript | Gate B r2 bounded pytest log with exit/count/warning/classification. | `.omo/evidence/task13-gates-abce/gate-b-pytest-r2.log` |
| C1 | terminal transcript | Gate C r2 bounded pytest log with exit/count/warning/classification. | `.omo/evidence/task13-gates-abce/gate-c-pytest-r2.log` |
| E1 | terminal transcript | Gate E tool registry check r2 log. | `.omo/evidence/task13-gates-abce/gate-e-tool-registry-r2.log` |
| E2 | terminal transcript | Gate E rule status scan r2 log. | `.omo/evidence/task13-gates-abce/gate-e-rule-status-scan-r2.log` |
| M1 | git transcript | Pre-gate dirty worktree snapshot. | `.omo/evidence/task13-gates-abce/git-status-short.txt` |
| M2 | plan excerpt | Task13 plan excerpt including Gate A/B/C/E commands and Gate E entry rule. | `.omo/evidence/task13-gates-abce/task13-plan-excerpt.txt` |
| M3 | environment | Python version. | `.omo/evidence/task13-gates-abce/python-version.txt` |
| M4 | environment | pytest version. | `.omo/evidence/task13-gates-abce/pytest-version.txt` |
| S1 | instrumentation transcript | First run summary retained as stale/misleading instrumentation evidence; not verdict source because exit fields were blank. | `.omo/evidence/task13-gates-abce/results-summary.json` |
| S2 | json summary | Authoritative r2 summary with exit code 0 for all scoped commands. | `.omo/evidence/task13-gates-abce/results-summary-r2.json` |

## Notes

- No 429 occurred.
- No product or test code was edited.
- A separate Python process observed after this QA had command line outside this Task13 exact-command scope, so it was not killed.
- `PYTHONDONTWRITEBYTECODE=1` was set for the scoped gate subprocesses; no scoped pytest cache provider was used.
