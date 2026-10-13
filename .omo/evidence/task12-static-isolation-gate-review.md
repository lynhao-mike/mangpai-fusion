# Task12 Static Isolation Gate Review

recommendation: REJECT
verdict: not_confirmed
confidence: 0.93

## originalIntent

Wave1 Task12 was intended to extend architecture and static-isolation guards only. The authoritative Task12 plan requires:

- governance package must not import application, infrastructure, or tools;
- governance package must not import or reference reports, feedback, learning, V5 runner, labels, case/prediction/sample-hit paths;
- shadow runner must not be consumed by default pipeline, report templates, or feedback entrypoints;
- `theory/multi-school-governance-v1.yaml` must not contain historical case IDs, prediction/result labels, sample hit results, or absolute paths;
- School View adapters must not write/build `FactSnapshot`;
- new governance code must not read system time to decide liunian;
- legacy Yang static protection remains in force.

Desired change scope was tests/helpers/evidence only, with no product code edits.

## desiredOutcome

The user-visible outcome is a trustworthy final gate answer for Task12: either `confirmed` if every prior blocker and artifact requirement is closed, or a non-pass verdict with exact blockers. The final gate must be read-only except this report.

## userOutcomeReview

The shipped guard code satisfies the Task12 behavior outcome in my direct review: all five original code-review blockers are closed by current tests/helpers, the exact focused suite passes fresh twice, five blocker-class no-write probes pass, malformed inputs fail closed, and six Task12 Python files remain under 250 pure LOC.

However, the approval artifact set is still incomplete under the final-gate instructions. The final code-review artifact does not explicitly show the required `remove-ai-slops` / `programming` skill-perspective check or overfit/slop criterion coverage for the repaired final state. The original BLOCK report includes that perspective, but it reviewed the pre-repair implementation. Because report coverage for the final approving review is missing, this gate cannot return `confirmed`.

## checkedArtifacts

- `plans/multi-school-governance-wave1-implementation-2026-08-02.md` Task12 authority lines 744-764.
- `.omo/plans/multi-school-governance-wave1-execution-2026-08-03.md`.
- `.omo/notepads/multi-school-governance-wave1/task12-static-isolation.md`.
- `.omo/start-work/artifacts/task12-static-isolation.txt`.
- `.omo/evidence/task12-static-isolation-code-review.md`.
- `.omo/evidence/task12-static-isolation-code-review-final.md`.
- `.omo/evidence/task12-static-isolation-manual-qa.md`.
- `.omo/evidence/task12-static-isolation-manual-qa/artifacts/retry2-probe.stdout.json`.
- `.omo/evidence/task12-static-isolation-manual-qa/artifacts/retry2-cleanup-status.json`.
- `META/project-state.json`.
- `tests/test_architecture_dependencies.py`.
- `tests/governance/test_static_isolation.py`.
- `tests/governance/static_isolation_scanner.py`.
- `tests/governance/static_isolation_imports.py`.
- `tests/governance/static_isolation_content.py`.
- `tests/governance/static_isolation_metadata.py`.
- `tests/yang_marriage/test_static_isolation.py`.

## directReview

Original blocker closure:

1. Relative import false negatives: closed. `static_isolation_imports.py` resolves relative `ImportFrom` nodes against package/module parts, and fixtures cover `..application`, `..infrastructure`, and `...tools`.
2. Shadow-runner default consumer coverage: closed. `static_isolation_metadata.py` reads active report/feedback entrypoints from current `META/project-state.json`, and tests require coverage for `output_linter`, `domain_analysis_cli`, `batch_review`, `promote_expert_weight_feedback`, and `domain_feedback`.
3. FactSnapshot aliases and adapter discovery: closed. Writer aliases from `engine.governance` and `engine.governance.contracts` are canonicalized, and adapter discovery is pattern-based for `governance_*adapter*.py` and `governance_*school*view*.py`.
4. Liunian system-time aliases: closed. Direct and aliased `datetime.datetime.now`, `datetime.date.today`, and `time.time` forms are detected.
5. YAML absolute paths: closed. Drive-letter, UNC, and Unix absolute paths are detected and covered by fixtures.

Slop/overfit pass:

- No production extraction, parser normalization, or abstraction was added to product code.
- Tests are guard-behavior tests over observable scanner outputs and real tree scans, not deletion-only tests or tests that merely verify a requested removal.
- Exact issue-string assertions are acceptable here because these helpers define the static guard contract; the tests also include real-tree negative assertions and benign controls.
- No weakening of the legacy Yang guard was found; Task12 explicitly checks the legacy guard file still contains `PUBLIC_FIELDS`, `APPROVED_BLOB_SHA256`, and `test_public_contract_fields_and_production_rule_bytes_are_unchanged`.
- Six current Task12 test/helper files are below the 250 pure LOC ceiling.

## freshCommands

Focused exact:

```text
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest tests/test_architecture_dependencies.py tests/governance/test_static_isolation.py tests/yang_marriage/test_static_isolation.py -q -p no:cacheprovider
34 passed, 1 warning in 10.20s
```

Focused repeat:

```text
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest tests/test_architecture_dependencies.py tests/governance/test_static_isolation.py tests/yang_marriage/test_static_isolation.py -q -p no:cacheprovider
34 passed, 1 warning in 7.82s
```

No-write direct probe matrix:

```text
5 original blocker classes plus malformed input: PASS
rows: relative_outward_imports, active_shadow_consumers, fact_snapshot_alias_and_discovery, liunian_system_time_aliases, yaml_absolute_paths, malformed_inputs_fail_closed
all_ok: true
```

Quality/accounting:

```text
python check-no-excuse-rules.py <six Task12 files>
no violations in 6 file(s)

python -m ruff check <six Task12 files>
All checks passed!

python -m ruff format --check <six Task12 files>
6 files already formatted

git diff --check -- <six Task12 files>
exit 0; warning only: LF will be replaced by CRLF for tests/test_architecture_dependencies.py
```

Pure LOC:

```text
tests/test_architecture_dependencies.py 76
tests/governance/test_static_isolation.py 208
tests/governance/static_isolation_scanner.py 172
tests/governance/static_isolation_imports.py 76
tests/governance/static_isolation_content.py 91
tests/governance/static_isolation_metadata.py 23
```

## adversarialReview

- dirty: repository has `total_dirty_entries=800`; scoped Task12 paths are one modified test, five untracked governance test/helper files, and evidence/notepad files. No product path is in the Task12 scoped set.
- stale: active entrypoints are read from current `META/project-state.json`; fresh focused tests and direct probes were run in this turn.
- misleading: direct probes compare expected and actual values and fail on mismatch; pytest counts are from fresh stdout.
- flaky: focused exact suite passed twice in this turn.
- hung: all commands exited; no timeout or inconclusive session remained.
- malformed: direct probe confirmed malformed Python raises `SyntaxError` and malformed YAML raises `ParserError`.
- cleanup: no `__pycache__` directories were found under `tests/governance`, `tests/yang_marriage`, or `tests/application`; only one unrelated existing pytest process was observed: PID 35664 with web-accountability ignores.

## blockers

1. Missing final review evidence: `.omo/evidence/task12-static-isolation-code-review-final.md` does not explicitly document the required `remove-ai-slops` / `programming` skill-perspective check or overfit/slop criterion coverage for the repaired final state. This is an artifact coverage gap, not a code-behavior blocker.

## evidenceGaps

- Final approving code-review report lacks explicit skill-perspective and overfit/slop coverage. The original BLOCK code review has that section, but it applies to the earlier failed implementation.

