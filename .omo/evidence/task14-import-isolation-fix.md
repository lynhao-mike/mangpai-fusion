# Task14 import-isolation fix evidence

Date: 2026-08-06
HEAD at start: `6caf5d0`

## DoneClaim

Fresh imports of `engine.application.governance_shadow_runner` no longer load
`engine.application.pipeline_runner` or `engine.v5.runner`. The original
`engine.application` exports and the two affected `engine.decision` v5 exports
remain in `__all__` and resolve to the same defining-module objects when accessed.
The gate rework also keeps `engine.decision.l7_report_view`,
`engine.decision.l8_feedback_attribution`, and `engine.decision.l9_calibration`
absent until an explicit public export requires them.

## Confirmed mechanism and toggle

The fresh-process regression was added first:

```text
python -m pytest tests/application/test_application_import_isolation.py -q
F.
AssertionError:
- '\n'
+ 'engine.application.pipeline_runner\nengine.v5.runner\n'
1 failed, 1 passed in 1.90s
```

The first minimal lazy `engine.application` boundary removed
`engine.application.pipeline_runner`, leaving only `engine.v5.runner`. That
runtime toggle proved a second independent eager chain:

```text
engine.application.governance_shadow_runner
-> engine.decision.models
-> engine.decision.__init__
-> engine.decision.v5_adapter
-> engine.v5.__init__
-> engine.v5.runner
```

After authorization, only the two `engine.decision.v5_adapter` package exports
were made lazy. Final focused result:

```text
python -m pytest tests/application/test_application_import_isolation.py -q
...                                                                      [100%]
3 passed in 2.48s
```

The same focused test was rerun twice after formatting: `3 passed in 1.69s` and
`3 passed in 2.38s`.

## Changed files and size

| File | Purpose | Pure LOC | Bytes |
| --- | --- | ---: | ---: |
| `engine/application/__init__.py` | Lazy-compatible application public exports | 61 | 2273 |
| `engine/decision/__init__.py` | Lazy-compatible decision public exports | 144 | 4792 |
| `tests/application/test_application_import_isolation.py` | Fresh-process isolation and identity regression | 96 | 6249 |
| `.omo/evidence/task14-import-isolation-fix.md` | This evidence | 157 | 8254 |

Tracked production diff: `118 insertions, 14 deletions` across the two package
initializers. The test and evidence files are new in the already-dirty worktree.
All changed Python files are below the 250 pure-LOC ceiling.

## Regression verification

Exact scoped suite:

```text
python -m pytest tests/application tests/governance/test_static_isolation.py tests/test_architecture_dependencies.py tests/test_production_entrypoints_unchanged.py tests/v2/test_v2_pipeline_compatibility.py tests/test_wenzhen_recompute.py tests/test_performance_and_ports.py tests/test_error_policy.py -q
119 passed, 1 warning in 107.63s (0:01:47)
```

Exit code was 0. The warning is the existing `dual_engine_adapter` deprecation
emitted by `engine.application.pipeline_runner`.

Quality gates:

```text
ruff check <three changed Python files>
All checks passed!

ruff format --check <three changed Python files>
3 files already formatted

python C:/Users/Administrator/.codex/plugins/cache/sisyphuslabs/omo/4.13.0/skills/programming/scripts/python/check-no-excuse-rules.py <three changed Python files>
no violations in 3 file(s)
```

`git diff --check` reported no whitespace errors; PowerShell only reported the
existing Git LF-to-CRLF working-copy warning for `engine/application/__init__.py`.

## Fresh-process manual QA

The exact fresh-process scenario was run twice. Both runs returned the identical
semantic result:

```json
{"decision_identity": true, "legacy_exports_present": true, "pipeline_identity": true, "pipeline_lazy_before_access": true, "production_runner_loaded_after_access": true, "shadow_forbidden": []}
```

This proves the shadow import keeps both forbidden modules absent, package-level
production runner access remains available, both runner exports retain identity,
and explicit access still loads the real production runner.

## State and cleanup probes

- `stale_state`: refuted by two independent fresh interpreters with identical output.
- `dirty_worktree`: present before work; no unrelated dirty file was reset, reverted, stashed, checked out, deleted, or overwritten.
- `flaky_tests`: refuted by the focused pass plus two immediate reruns.
- `misleading_success_output`: refuted by semantic identity/load assertions, not exit code alone.
- `hung_commands`: the 107.63-second regression exited 0; final task-process probe returned `task_matching_processes=0`.
- `repeated_interruptions`: status messages did not start overlapping commands.
- Temp cleanup: `matching_temp_artifacts=0`; no debugger, bytecode, or fixture artifact was created.
- An unrelated pre-existing `ruff.exe server` process was observed and intentionally left untouched.

Scoped final status before this evidence write:

```text
 M engine/application/__init__.py
 M engine/decision/__init__.py
?? tests/application/test_application_import_isolation.py
```

## Residual risk

Import-time failures in defining modules are now intentionally deferred until the
corresponding public attribute is first accessed. `__all__`, `dir()`, explicit
package access, object identity, shadow behavior, and production pipeline tests
are covered. No public export was removed.

## Gate rework

The adversarial gate found that the narrow runner fix still loaded three
forbidden decision surfaces. The fresh-process test was extended before the
second production edit and reproduced the exact remaining fanout:

```text
F...                                                                     [100%]
AssertionError:
- '\n'
+ 'engine.decision.l7_report_view\nengine.decision.l8_feedback_attribution\nengine.decision.l9_calibration\n'
1 failed, 3 passed in 3.39s
```

Before editing `engine.decision.__init__`, the six direct L7/L8/L9 exports passed
an identity and `__all__` characterization. Static dependency inspection showed
that the seventh public export, `run_decision_mvp`, eagerly imports all three
surfaces through `engine.decision.orchestrator`; its identity characterization
also passed before the edit (`1 passed in 0.56s`).

The minimal rework moved these seven public exports into the existing lazy map:

- `build_report_items`
- `attribute_feedback`
- `build_feedback_attributions`
- `build_feedback_signals`
- `build_calibration_actions`
- `build_router_calibration_actions`
- `run_decision_mvp`

No implementation module, public name, import hook, or error escape hatch changed.
The same resolver continues to cache successful explicit access, raise normal
`AttributeError` for unknown names, propagate `ModuleNotFoundError` for a missing
deferred module, and avoid caching failed access.

Rework verification:

```text
focused: 4 passed in 1.61s
related: 31 passed in 2.78s
broader historical 119-suite command: 120 passed, 1 warning in 97.26s
```

The broader count is 120 because the gate rework added one focused export
characterization. The warning remains the pre-existing production adapter
deprecation. Five post-format focused repeats all exited 0:

```text
4 passed in 2.07s
4 passed in 2.45s
4 passed in 2.48s
4 passed in 2.28s
4 passed in 3.37s
```

Rework quality gates:

```text
ruff check: All checks passed!
ruff format --check: 3 files already formatted
exact no-excuse: no violations in 3 file(s)
```

Final fresh-process QA was run twice with identical output:

```json
{"application_identity": true, "decision_cached": true, "decision_exports_present": true, "decision_identity": true, "deferred_error": "ModuleNotFoundError", "failed_export_cached": false, "shadow_forbidden": [], "unknown_error": "AttributeError"}
```

The final five-module forbidden set was:

```text
engine.application.pipeline_runner
engine.v5.runner
engine.decision.l7_report_view
engine.decision.l8_feedback_attribution
engine.decision.l9_calibration
```

Final tracked production diff is `142 insertions, 16 deletions`. All changed
Python files remain below 250 pure LOC. `git diff --check` exited 0 with only the
existing LF-to-CRLF informational warning. Final cleanup probes returned
`task_matching_processes=0` and `matching_temp_artifacts=0`; unrelated dirty work
and the pre-existing Ruff server were left untouched.
