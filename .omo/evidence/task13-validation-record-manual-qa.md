# Task13 Validation Record Manual QA

Date: 2026-08-06 Asia/Shanghai
Workspace: `F:\多流派新思路`
Role: independent manual QA executor
Scope: validate Task13 evidence records by parsing the markdown records and opening referenced artifacts. No product, test, or original validation record edits were made.

## Verdict

PASS for evidence-record fidelity, with one required limitation: exact Gate D is still a real FAIL (`exitCode=2`, `1 error during collection`) and must not be represented as full-suite success. The `4195 passed, 7 skipped` result is supplemental evidence from a remaining-suite command that ignored both known blockers.

Scenario count: 14 surface scenarios, 11 adversarial cases.

## Expected / Actual Matrix

| criterion | expected | actual observed | verdict | artifactRefs |
|---|---|---|---|---|
| Gate A count | 212 passed, exit 0 | `gate-a-pytest-r2.log`: `exit_code: 0`, `passed=212`, pytest summary `212 passed` | PASS | A1 |
| Gate B count | 333 passed, exit 0 | `gate-b-pytest-r2.log`: `exit_code: 0`, `passed=333`, pytest summary `333 passed` | PASS | A2 |
| Gate C count | 24 passed, exit 0 | `gate-c-pytest-r2.log`: `exit_code: 0`, `passed=24`, pytest summary `24 passed` | PASS | A3 |
| Gate E exits | two formal entries, both exit 0 | `tool_registry.py --check` and `rule_status_scan.py --check` both record `exit_code: 0` and pass text | PASS | A4, A5 |
| Exact Gate D | exact `python -m pytest tests/ -q -p no:cacheprovider` fails with exit 2 and one collection error | metadata has `exitCode: 2`; log has `Interrupted: 1 error during collection` for `tests/test_application_candidates.py` | PASS | A6, A7 |
| Gate D syntax attribution timestamps | syntax blocker attributed with timestamp evidence | journal says file mtime `2026-08-02T17:22:11.8725934+08:00`, before Wave1 Boulder creation `2026-08-03T13:14:59.8291462+08:00`; classification strong pre-existing unrelated | PASS | A8 |
| G001 A/B/C toggle | bad/good/bad causal toggle documented | A timeout 35.019s, B `1 passed` exit 0 with cache, C timeout 35.067s; classification pre-existing unrelated | PASS | A9 |
| Remaining suite | 4195 passed, 7 skipped, exit 0, 1260.9s | remaining-suite meta has `exitCode: 0`, `durationSeconds: 1260.9`; output has `4195 passed, 7 skipped` | PASS | A10, A11 |
| Git status field | dirty worktree captured | ABCE record references `git-status-short.txt` and artifact is non-empty 86069 bytes; current scoped check saw 801 status lines before this report | PASS | A12, A18 |
| Versions field | Python and pytest versions present | ABCE record and version files show Python 3.14.5 and pytest 8.4.2; current command confirmed same | PASS | A13, A14, A18 |
| Command/start/end/count/classification fields | required Task13 run fields present | selected records contain exact invocations, starts/ends, exit/count fields, failure classifications, and `manualQa` sections | PASS | A15 |
| 15.1 mapping / plan mapping | Task13 gates mapped to authority plan section | plan excerpt contains Gate A/B/C/D/E command mapping; ledger ties Wave1 to `multi-school-governance-wave1-execution-2026-08-03.md` | PASS | A16, A17 |
| No unrun command inferred | verdicts rely on opened non-empty artifacts | A/B/C/E, exact D, remaining suite, syntax journal, and G001 proof are backed by non-empty artifacts; stale first-run summaries are explicitly excluded from verdict use | PASS | A1-A17 |

## manualQa

### surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
|---|---|---|---|---|---|
| QA-S01 | Locate Task13 evidence records | PowerShell filesystem listing | `Get-ChildItem -Recurse -Force 'F:\多流派新思路\.omo'` | PASS: Task13 records and artifacts found | A19 |
| QA-S02 | Search validation terms and requested counts | ripgrep evidence scan | `rg -n "validation\|Gate A\|Gate B\|Gate C\|Gate D\|Gate E\|4195\|1260\.9\|G001\|15\.1\|syntax\|collection\|212\|333" 'F:\多流派新思路\.omo\evidence'` | PASS: all requested Task13 topics surfaced | A19 |
| QA-S03 | Read ABCE validation markdown | PowerShell file read | `Get-Content -Raw '.omo\evidence\task13-gates-abce.md'` | PASS: Gate A/B/C/E summary and matrix present | A15 |
| QA-S04 | Read exact Gate D validation markdown | PowerShell file read | `Get-Content -Raw '.omo\evidence\task13-gate-d-full.md'` | PASS: exact Gate D failure documented | A6 |
| QA-S05 | Read remaining-suite markdown | PowerShell file read | `Get-Content -Raw '.omo\evidence\task13-gate-d-remaining-suite.md'` | PASS: supplemental command documented with two ignores | A10 |
| QA-S06 | Verify Gate A raw artifact | PowerShell file read | `Get-Content -Raw '.omo\evidence\task13-gates-abce\gate-a-pytest-r2.log'` | PASS: 212 passed, exit 0 | A1 |
| QA-S07 | Verify Gate B raw artifact | PowerShell file read | `Get-Content -Raw '.omo\evidence\task13-gates-abce\gate-b-pytest-r2.log'` | PASS: 333 passed, exit 0 | A2 |
| QA-S08 | Verify Gate C raw artifact | PowerShell file read | `Get-Content -Raw '.omo\evidence\task13-gates-abce\gate-c-pytest-r2.log'` | PASS: 24 passed, exit 0 | A3 |
| QA-S09 | Verify Gate E raw artifacts | PowerShell file read | `Get-Content -Raw gate-e-tool-registry-r2.log; Get-Content -Raw gate-e-rule-status-scan-r2.log` | PASS: both exit 0 | A4, A5 |
| QA-S10 | Verify exact Gate D raw artifacts | PowerShell file read | `Get-Content -Raw '.omo\evidence\task13-gate-d-full-meta-rerun.json'; Get-Content -Raw '.omo\evidence\task13-gate-d-full-pytest-rerun.log'` | PASS: exit 2 and one collection error | A6, A7 |
| QA-S11 | Verify remaining suite raw artifacts | PowerShell file read | `Get-Content -Raw '.omo\evidence\task13-gate-d-remaining-suite-pytest-meta.json'; Get-Content -Raw '.omo\evidence\task13-gate-d-remaining-suite-pytest-output.txt'` | PASS: exit 0, 4195 passed, 7 skipped, 1260.9s | A10, A11 |
| QA-S12 | Verify syntax attribution and G001 toggle | PowerShell file read | `Get-Content -Raw '.omo\evidence\task13-gate-d-syntax-debug-journal.md'; Get-Content -Raw '.omo\evidence\task13-g001-yaml-toggle.md'` | PASS: timestamps and A/B/C toggle present | A8, A9 |
| QA-S13 | Verify plan / 15.1 mapping | ripgrep plan and ledger scan | `rg -n "15\.1\|Task13\|Gate A\|Gate B\|Gate C\|Gate D\|Gate E\|multi-school-governance-wave1" ...` | PASS: Task13 gate mapping and Wave1 ledger linkage present | A16, A17 |
| QA-S14 | Verify current environment and dirty status | PowerShell terminal | `git status --short | Measure-Object -Line; python --version; python -m pytest --version` | PASS: dirty status observed, Python 3.14.5, pytest 8.4.2 | A18 |

### adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
|---|---|---|---|---|---|
| QA-A01 | Dirty worktree | dirty | Record captures dirt and QA does not reset/revert/stash. | PASS: existing dirty status captured; only this evidence file was added | A12, A18 |
| QA-A02 | Stale first-run summaries | stale | Stale or unreliable initial wrappers must not source verdicts. | PASS: ABCE and Gate D records explicitly use r2/primary rerun artifacts for verdicts | A15, A6 |
| QA-A03 | Misleading exact-vs-supplemental Gate D | misleading | Remaining-suite success must not be promoted to exact Gate D success. | PASS: exact Gate D remains FAIL; remaining suite is labeled supplemental with ignores | A6, A10 |
| QA-A04 | Hung commands | hung | Bounded metadata should show timeout state. | PASS: A/B/C/E timed_out false; exact D `timedOut false`; remaining suite `timedOut false` | A1-A7, A10 |
| QA-A05 | Flaky / repeated run consistency | flaky | Rerun counts should match raw pytest summaries. | PASS: r2 logs and raw summaries align for A/B/C/E; remaining suite has one completed raw run | A1-A5, A10, A11 |
| QA-A06 | Repeated interruptions / 429 | repeated-interruptions | Inconclusive 429 attempts must not be accepted as evidence. | PASS: ledger shows earlier 429s recorded as inconclusive; Task13 artifacts use concrete run logs | A17 |
| QA-A07 | Collection blocker attribution | classification | Syntax failure should be classified with source/timestamp basis. | PASS: attribution journal gives mtime, Wave1 start, diff, HEAD parse, and no ownership references | A8 |
| QA-A08 | G001 timeout attribution | classification | Timeout blocker should be separated from exact syntax blocker and classified. | PASS: A/B/C toggle records reproducible uncached timeout and cached pass, unrelated to Wave1 | A9 |
| QA-A09 | Cleanup limitations | cleanup limitations | QA should record what was and was not cleaned. | PASS: Gate D cleanup log/process check and remaining-suite process snapshots exist; unowned processes left untouched | A20, A21 |
| QA-A10 | Artifact non-emptiness | misleading | Every PASS artifact reference must be non-empty. | PASS: selected opened artifacts are non-empty; smallest checked was pytest version at 17 bytes | A22 |
| QA-A11 | No unrun command inferred | misleading | Commands without opened artifacts should not become PASS claims. | PASS: all accepted run claims are backed by opened logs/meta; G001 proof is self-contained and no source edits claimed | A1-A17 |

### artifactRefs

| id | kind | description | path |
|---|---|---|---|
| A1 | terminal transcript | Gate A r2 pytest log, 1428 bytes | `.omo/evidence/task13-gates-abce/gate-a-pytest-r2.log` |
| A2 | terminal transcript | Gate B r2 pytest log, 1655 bytes | `.omo/evidence/task13-gates-abce/gate-b-pytest-r2.log` |
| A3 | terminal transcript | Gate C r2 pytest log, 1236 bytes | `.omo/evidence/task13-gates-abce/gate-c-pytest-r2.log` |
| A4 | terminal transcript | Gate E tool registry r2 log, 476 bytes | `.omo/evidence/task13-gates-abce/gate-e-tool-registry-r2.log` |
| A5 | terminal transcript | Gate E rule status scan r2 log, 482 bytes | `.omo/evidence/task13-gates-abce/gate-e-rule-status-scan-r2.log` |
| A6 | validation markdown | Exact Gate D full evidence markdown, 4143 bytes | `.omo/evidence/task13-gate-d-full.md` |
| A7 | terminal transcript / metadata | Exact Gate D rerun log 2328 bytes and metadata 472 bytes | `.omo/evidence/task13-gate-d-full-pytest-rerun.log`; `.omo/evidence/task13-gate-d-full-meta-rerun.json` |
| A8 | debug journal | Gate D syntax attribution journal, 3499 bytes | `.omo/evidence/task13-gate-d-syntax-debug-journal.md` |
| A9 | debug proof | G001 YAML A/B/C toggle proof, 6932 bytes | `.omo/evidence/task13-g001-yaml-toggle.md` |
| A10 | validation markdown / metadata | Remaining-suite evidence markdown 4546 bytes and metadata 531 bytes | `.omo/evidence/task13-gate-d-remaining-suite.md`; `.omo/evidence/task13-gate-d-remaining-suite-pytest-meta.json` |
| A11 | terminal transcript | Remaining-suite pytest output, 7143 bytes | `.omo/evidence/task13-gate-d-remaining-suite-pytest-output.txt` |
| A12 | git transcript | Pre-gate dirty worktree snapshot, 86069 bytes | `.omo/evidence/task13-gates-abce/git-status-short.txt` |
| A13 | environment | Python version file, 18 bytes | `.omo/evidence/task13-gates-abce/python-version.txt` |
| A14 | environment | pytest version file, 17 bytes | `.omo/evidence/task13-gates-abce/pytest-version.txt` |
| A15 | validation markdown | Gate A/B/C/E validation markdown, 5507 bytes | `.omo/evidence/task13-gates-abce.md` |
| A16 | plan excerpt | Task13 plan excerpt with Gate A/B/C/D/E commands, 1828 bytes | `.omo/evidence/task13-gates-abce/task13-plan-excerpt.txt` |
| A17 | ledger / plan scan | Wave1 ledger and plan mapping scan output observed in QA terminal | `.omo/start-work/ledger.jsonl`; `.omo/plans/multi-school-governance-wave1-execution-2026-08-03.md` |
| A18 | terminal transcript | Current QA environment/status command output: 801 dirty status lines before this file, Python 3.14.5, pytest 8.4.2 | this QA session transcript |
| A19 | terminal transcript | Evidence listing and ripgrep discovery output for Task13 artifacts | this QA session transcript |
| A20 | process check | Exact Gate D post-run scoped process check | `.omo/evidence/task13-gate-d-full-process-check.txt` |
| A21 | cleanup / process snapshots | Exact Gate D pycache cleanup and remaining-suite before/mid/after process snapshots | `.omo/evidence/task13-gate-d-full-pycache-cleanup.txt`; `.omo/evidence/task13-gate-d-remaining-suite-processes-before.txt`; `.omo/evidence/task13-gate-d-remaining-suite-processes-midrun.txt`; `.omo/evidence/task13-gate-d-remaining-suite-processes-after.txt` |
| A22 | file-size probe | Corrected PowerShell non-empty artifact check output | this QA session transcript |

## Notes And Limitations

- No 429 occurred during this manual QA pass. Historical 429s in the Wave1 ledger are treated as inconclusive attempts, not evidence.
- One PowerShell artifact-size probe had a syntax error and was rerun correctly; it produced no filesystem changes.
- Cleanup evidence is limited to recorded process/cache artifacts. I did not terminate unowned processes or delete unowned caches.
- I did not rerun the 20-minute remaining suite or the exact failing Gate D suite; this QA was an evidence-record validation pass that opened raw artifacts and metadata. No PASS here depends on an unopened or empty artifact.
