# Task12 Static Isolation Code Review

Review target: Wave1 Task12 static isolation guards.

Reviewed inputs:
- Authoritative plan/design: `.omo/plans/multi-school-governance-wave1-execution-2026-08-03.md`, `plans/multi-school-governance-design-2026-08-02.md`, `plans/multi-school-governance-wave1-implementation-2026-08-02.md`
- Changed files: `tests/test_architecture_dependencies.py`, `tests/governance/test_static_isolation.py`, `tests/governance/static_isolation_scanner.py`, `tests/governance/static_isolation_content.py`
- Evidence/notepad: `.omo/start-work/artifacts/task12-static-isolation.txt`, `.omo/notepads/multi-school-governance-wave1/task12-static-isolation.md`

Skill-perspective check:
- Loaded `omo:remove-ai-slops` and `omo:programming`, plus `programming` Python README and code-smells reference.
- Production code was not modified. Touched Python files pass no-excuse, Ruff, and the 250 pure LOC ceiling.
- The diff violates the remove-ai-slops/programming review perspective through under-specified static tests: several tests prove only the direct requested spelling, while simple equivalent violating forms pass. That creates false confidence and is a blocker for a guard-only task.

## CRITICAL

None.

## HIGH

1. Relative imports can bypass the core governance outward-import guard.

`tests/governance/static_isolation_scanner.py:40` returns immediately for every relative `ImportFrom`, and `tests/test_architecture_dependencies.py:37` makes the same assumption. That assumption is unsafe for `engine/governance`: `from ..application import governance_shadow_runner`, `from ..infrastructure import adapters`, or `from ...tools import x` are outward dependencies but are ignored. A no-write probe against `_ImportCollector` with `from ..application import governance_shadow_runner` returned `[]`.

Impact: the Task12 requirement that governance cannot import application/infrastructure/tools can be violated while both the new governance scanner and the architecture test stay green.

Required fix: resolve relative imports against the scanned package/module path, then add controlled failing fixtures for `..application`, `..infrastructure`, and tool escapes.

2. Shadow-runner default-consumer coverage is incomplete.

`tests/governance/static_isolation_scanner.py:117` hard-codes only `engine/pipeline.py`, `engine/application/pipeline_runner.py`, `engine/claims/runner_registry.py`, `engine/decision/orchestrator.py`, `tools/feedback_ingest.py`, `tools/feedback_loop.py`, `tools/render_report.py`, plus templates. The project metadata lists active feedback entrypoints at `META/project-state.json:61` including `tools/batch_review.py`, `tools/promote_expert_weight_feedback.py`, and `tools/domain_feedback.py`, and active report entrypoints at `META/project-state.json:77` including `tools/output_linter.py` and `tools/domain_analysis_cli.py`. `tools/README.md:20`, `tools/README.md:23`, `tools/README.md:26`, `tools/README.md:27`, and `tools/README.md:31` confirm those are live surfaces.

Impact: a default report/feedback consumer can import or reference `engine.application.governance_shadow_runner` without Task12 noticing, so the "shadow path remains opt-in only" claim is not fully guarded.

Required fix: derive this scan from the authoritative active entrypoint metadata/tool index or explicitly include every active default report/feedback/pipeline consumer, with a fixture proving a newly added active entrypoint is scanned.

3. FactSnapshot write detection misses aliases and future adapter files.

`tests/governance/static_isolation_scanner.py:155` reduces every call to a leaf name and `fact_snapshot_write_issues()` only compares that leaf against `FactSnapshot`, `build_fact_snapshot`, and `build_governance_fact_snapshot` at `tests/governance/static_isolation_scanner.py:164`. A no-write probe with `from engine.governance import build_fact_snapshot as make_snapshot; make_snapshot(None)` produced call leaf `make_snapshot` and no writer match. Also, `school_view_adapter_paths()` at `tests/governance/static_isolation_scanner.py:173` scans only three fixed files, so a new `governance_*school*_view*.py` adapter would be outside the guard unless someone remembers to edit the scanner.

Impact: School View adapters can write/build FactSnapshots through normal Python aliasing while the guard passes.

Required fix: track imports/aliases for the forbidden constructors/builders and broaden adapter path discovery to the school-view adapter surface, not a three-file allowlist.

4. The liunian system-time guard catches only direct spellings.

`SYSTEM_TIME_CALLS` at `tests/governance/static_isolation_scanner.py:21` covers `date.today`, `datetime.now`, and `time.time`, and `system_time_liunian_issues()` checks `call.endswith(name)` at `tests/governance/static_isolation_scanner.py:197`. This catches `_dt.datetime.now()` but misses common aliases such as `from datetime import datetime as dt; dt.now()` or `from time import time as now; now()` in a file mentioning liunian.

Impact: the explicit-year/liunian isolation rule can regress through ordinary import aliases while the static guard stays green.

Required fix: track import aliases for `datetime.date.today`, `datetime.datetime.now`, and `time.time`; add fixtures for alias and module-alias forms.

## MEDIUM

1. YAML absolute-path detection is narrower than the requirement.

`ABSOLUTE_PATH_PATTERN` at `tests/governance/static_isolation_content.py:34` catches drive-letter paths and a small set of Unix roots, but misses UNC paths and common absolute Unix paths such as `/opt/project/case.json`. A no-write probe returned no matches for `\\server\share\case.json` and `/opt/project/case.json`, while `F:\cases\x.json` matched.

Impact: forbidden absolute paths can enter `theory/multi-school-governance-v1.yaml` in common forms without detection.

Required fix: parse absolute paths with `PureWindowsPath`/`PurePosixPath`-style logic or expand the anchored patterns, and add UNC plus non-home Unix root fixtures.

## LOW

1. `tests/test_architecture_dependencies.py:36` changed `elif isinstance(node, ast.ImportFrom)` to `if isinstance(node, ast.ImportFrom)`. This is behavior-neutral because an AST node cannot be both `Import` and `ImportFrom`, but it adds noise to a guard-only diff.

## Test And Gate Evidence

Fresh commands run by this reviewer:

- `python -m pytest tests/test_architecture_dependencies.py tests/governance/test_static_isolation.py tests/yang_marriage/test_static_isolation.py -q -p no:cacheprovider`
  - Result: PASS, 27 passed, 1 pre-existing deprecation warning in 3.59s.
- `python -m pytest tests/application/test_governance_shadow_runner.py tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q -p no:cacheprovider`
  - Result: PASS, 94 passed, 1 pre-existing deprecation warning in 33.53s.
- `python -m ruff check tests/test_architecture_dependencies.py tests/governance/test_static_isolation.py tests/governance/static_isolation_scanner.py tests/governance/static_isolation_content.py`
  - Result: PASS, all checks passed.
- `python -m ruff format --check tests/test_architecture_dependencies.py tests/governance/test_static_isolation.py tests/governance/static_isolation_scanner.py tests/governance/static_isolation_content.py`
  - Result: PASS, 4 files already formatted.
- `python C:\Users\Administrator\.codex\plugins\cache\sisyphuslabs\omo\4.13.0\skills\programming\scripts\python\check-no-excuse-rules.py tests/test_architecture_dependencies.py tests/governance/test_static_isolation.py tests/governance/static_isolation_scanner.py tests/governance/static_isolation_content.py`
  - Result: PASS, no violations in 4 files.
- `python -B -m compileall -q ...`
  - Result: PASS, exit 0. Used `PYTHONPYCACHEPREFIX` under `%TEMP%` to avoid repo pycache writes.
- `git diff --check -- tests/test_architecture_dependencies.py tests/governance/test_static_isolation.py tests/governance/static_isolation_scanner.py tests/governance/static_isolation_content.py`
  - Result: PASS.
- Pure LOC:
  - `tests/test_architecture_dependencies.py`: 75
  - `tests/governance/test_static_isolation.py`: 117
  - `tests/governance/static_isolation_scanner.py`: 173
  - `tests/governance/static_isolation_content.py`: 88

Scoped git status after review commands:
- `M tests/test_architecture_dependencies.py`
- `?? tests/governance/test_static_isolation.py`
- `?? tests/governance/static_isolation_scanner.py`
- `?? tests/governance/static_isolation_content.py`
- `?? .omo/start-work/artifacts/task12-static-isolation.txt`
- `?? .omo/notepads/multi-school-governance-wave1/task12-static-isolation.md`

Note: a temporary compileall pycache directory remains under `%TEMP%` because the cleanup command was rejected by the local policy wrapper before execution. It is outside the repository and did not change scoped git status.

## Verdict

codeQualityStatus: BLOCK

recommendation: REQUEST_CHANGES

blockers:
- Fix relative import resolution for architecture/governance import scans.
- Cover all active default report/feedback/pipeline consumers for shadow-runner isolation.
- Make FactSnapshot write detection alias-aware and broaden adapter surface discovery.
- Make liunian system-time detection alias-aware.
- Broaden YAML absolute-path detection to common Windows UNC and Unix absolute paths.
