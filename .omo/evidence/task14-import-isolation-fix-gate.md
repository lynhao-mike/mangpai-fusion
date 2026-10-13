# Task14 import-isolation fix adversarial gate

Date: 2026-08-06

## AdversarialVerify

**CONFIRMED** after rework (confidence: **0.99**).

The narrow DoneClaim in `task14-import-isolation-fix.md` is confirmed:

- a fresh import of `engine.application.governance_shadow_runner` no longer loads
  `engine.application.pipeline_runner`;
- the same import no longer loads `engine.v5.runner`;
- all ten original `engine.application` exports and both lazy
  `engine.decision.v5_adapter` exports retain defining-object identity;
- explicit access loads the real production modules and caches the same objects;
- unknown names and failed deferred imports preserve normal Python error behavior.

The earlier gate failure is resolved. The H2 evidence records the Task11 authority
as requiring no report/feedback/L7-L9/production-runner imports. A fresh shadow
import now leaves all five audited modules absent:

```text
engine.decision.l7_report_view
engine.decision.l8_feedback_attribution
engine.decision.l9_calibration
```

The rework moved the affected L7-L9 and orchestrator package exports into the
existing lazy resolver. Explicit access still resolves and caches their defining
objects. The historical failed-gate evidence below is retained as the reason for
the rework; the final rerun section supersedes its former `needs-fix` conclusion.

## Source and prior-evidence review

Reviewed read-only:

- `.omo/evidence/task14-import-isolation-fix.md`
- `.omo/evidence/task14-runtime-h2-side-effects.md`
- `engine/application/__init__.py`
- `engine/decision/__init__.py`
- `tests/application/test_application_import_isolation.py`

`engine.application` now resolves its ten legacy exports from `_LAZY_EXPORTS` via
module `__getattr__`. `engine.decision` does the same only for
`decision_run_from_snapshot` and `decision_run_from_v5`; its L7-L9 exports remain
ordinary eager imports.

## Fresh shadow-import probe

Exact command:

```powershell
@'
import json,sys
before=set(sys.modules)
from engine.application.governance_shadow_runner import run_governance_shadow
loaded=set(sys.modules)-before
watched=('engine.application.pipeline_runner','engine.v5.runner','engine.decision.l7_report_view','engine.decision.l8_feedback_attribution','engine.decision.l9_calibration','tools.render_report','tools.feedback_ingest','tools.feedback_loop','tools.conditional_learning')
print(json.dumps({'pipeline_runner_loaded':'engine.application.pipeline_runner' in loaded,'v5_runner_loaded':'engine.v5.runner' in loaded,'broader_watched_loaded':[n for n in watched if n in loaded]},sort_keys=True))
'@ | python -B -
```

Result: exit 0.

```json
{"broader_watched_loaded": ["engine.decision.l7_report_view", "engine.decision.l8_feedback_attribution", "engine.decision.l9_calibration"], "pipeline_runner_loaded": false, "v5_runner_loaded": false}
```

The required two module-presence checks pass. The broader authority check fails.

## Explicit export and production identity probe

Exact command:

```powershell
@'
import json,sys
import engine.application as app
import engine.decision as decision
before={'pipeline_runner':'engine.application.pipeline_runner' in sys.modules,'v5_runner':'engine.v5.runner' in sys.modules}
app_expected={
 'PipelineTiming':('engine.application.timing','PipelineTiming'),
 'RecomputeHardGateError':('engine.application.recompute','RecomputeHardGateError'),
 'RecomputeRequest':('engine.application.recompute','RecomputeRequest'),
 'RecomputeResult':('engine.application.recompute','RecomputeResult'),
 'StepTiming':('engine.application.timing','StepTiming'),
 'integrate':('engine.application.integration','integrate'),
 'recompute_wenzhen_case':('engine.application.recompute','recompute_wenzhen_case'),
 'run_pipeline':('engine.application.pipeline_runner','run_pipeline'),
 'run_pipeline_e2e':('engine.application.pipeline_runner','run_pipeline_e2e'),
 'verify_hash_chain':('engine.application.integration','verify_hash_chain'),
}
from importlib import import_module
app_identity={name:getattr(app,name) is getattr(import_module(mod),attr) for name,(mod,attr) in app_expected.items()}
dec_expected={name:getattr(import_module('engine.decision.v5_adapter'),name) for name in ('decision_run_from_snapshot','decision_run_from_v5')}
dec_identity={name:getattr(decision,name) is value for name,value in dec_expected.items()}
from engine.v5.runner import run_v5
print(json.dumps({'before':before,'application_all_identity':all(app_identity.values()),'application_failures':[n for n,v in app_identity.items() if not v],'decision_all_identity':all(dec_identity.values()),'decision_failures':[n for n,v in dec_identity.items() if not v],'after':{'pipeline_runner':'engine.application.pipeline_runner' in sys.modules,'v5_runner':'engine.v5.runner' in sys.modules},'production_objects':{'app_runner_module':app.run_pipeline.__module__,'decision_adapter_module':decision.decision_run_from_v5.__module__,'run_v5_module':run_v5.__module__}},sort_keys=True))
'@ | python -B -
```

Result: exit 0.

```json
{"after": {"pipeline_runner": true, "v5_runner": true}, "application_all_identity": true, "application_failures": [], "before": {"pipeline_runner": false, "v5_runner": false}, "decision_all_identity": true, "decision_failures": [], "production_objects": {"app_runner_module": "engine.application.pipeline_runner", "decision_adapter_module": "engine.decision.v5_adapter", "run_v5_module": "engine.v5.runner"}}
```

This validates every application lazy export, both decision lazy exports, the
before/after module state, and the defining modules of the real production objects.

## Lazy error behavior

Exact command:

```powershell
@'
import json,sys
import engine.application as app
unknown_before=set(sys.modules)
try: app.no_such_export
except Exception as e: unknown={'type':type(e).__name__,'message':str(e)}
else: unknown={'type':'NO_ERROR'}
app._LAZY_EXPORTS['broken_for_gate']=('no.such.module.for.task14','missing')
try: app.broken_for_gate
except Exception as e: broken={'type':type(e).__name__,'message':str(e),'cached':'broken_for_gate' in app.__dict__}
else: broken={'type':'NO_ERROR'}
print(json.dumps({'unknown':unknown,'unknown_loaded_pipeline':'engine.application.pipeline_runner' in set(sys.modules)-unknown_before,'broken':broken,'dir_duplicate_count':len(dir(app))-len(set(dir(app)))},sort_keys=True))
'@ | python -B -
```

Result: exit 0.

```json
{"broken": {"cached": false, "message": "No module named 'no'", "type": "ModuleNotFoundError"}, "dir_duplicate_count": 0, "unknown": {"message": "module 'engine.application' has no attribute 'no_such_export'", "type": "AttributeError"}, "unknown_loaded_pipeline": false}
```

Unknown package attributes remain normal `AttributeError`s and do not load the
pipeline. A missing deferred module raises `ModuleNotFoundError` and the failed
lookup is not cached. `dir()` contained no duplicates in this state.

## Focused and related regressions

Exact focused command:

```powershell
python -m pytest tests/application/test_application_import_isolation.py -q
```

Result: exit 0, `3 passed in 2.93s`.

Exact related command:

```powershell
python -m pytest tests/application/test_governance_shadow_runner.py tests/governance/test_static_isolation.py tests/test_architecture_dependencies.py -q
```

Result: exit 0, `31 passed in 4.60s`.

Exact broader compatibility command:

```powershell
python -m pytest tests/application tests/governance/test_static_isolation.py tests/test_architecture_dependencies.py tests/test_production_entrypoints_unchanged.py tests/v2/test_v2_pipeline_compatibility.py tests/test_wenzhen_recompute.py tests/test_performance_and_ports.py tests/test_error_policy.py -q
```

Result: exit 0, `119 passed, 1 warning in 94.51s (0:01:34)`.

The warning is the existing `engine.application.dual_engine_adapter` deprecation
emitted when the compatibility suite explicitly loads the production pipeline.

An earlier invocation of the same broad command reached 79% and exited, but its
parallel wrapper did not preserve the final output tail. It was not counted as a
pass. The exact standalone rerun above captured the exit code and final pass line.

## Flake repeat

Exact command:

```powershell
$ok=$true; 1..5 | ForEach-Object { $out = python -m pytest tests/application/test_application_import_isolation.py -q 2>&1; $code=$LASTEXITCODE; "RUN $_ EXIT $code"; $out | Select-Object -Last 2; if ($code -ne 0) { $ok=$false } }; if (-not $ok) { exit 1 }
```

Result: exit 0.

```text
RUN 1 EXIT 0 - 3 passed in 3.09s
RUN 2 EXIT 0 - 3 passed in 2.35s
RUN 3 EXIT 0 - 3 passed in 2.29s
RUN 4 EXIT 0 - 3 passed in 1.70s
RUN 5 EXIT 0 - 3 passed in 1.96s
```

Each test creates a new interpreter, so these repeats also refute stale module
state as the explanation for the narrow pass.

## Quality and LOC gates

Exact commands and results:

```powershell
ruff check engine/application/__init__.py engine/decision/__init__.py tests/application/test_application_import_isolation.py
```

Result: exit 0, `All checks passed!`.

```powershell
ruff format --check engine/application/__init__.py engine/decision/__init__.py tests/application/test_application_import_isolation.py
```

Result: exit 0, `3 files already formatted`.

```powershell
python C:/Users/Administrator/.codex/plugins/cache/sisyphuslabs/omo/4.13.0/skills/programming/scripts/python/check-no-excuse-rules.py engine/application/__init__.py engine/decision/__init__.py tests/application/test_application_import_isolation.py
```

Result: exit 0, `no violations in 3 file(s)`.

LOC/byte read-only measurement result:

| File | Physical lines | Nonblank/noncomment | Bytes |
| --- | ---: | ---: | ---: |
| `engine/application/__init__.py` | 74 | 61 | 2273 |
| `engine/decision/__init__.py` | 135 | 122 | 3934 |
| `tests/application/test_application_import_isolation.py` | 84 | 62 | 3669 |

All three remain below the 250 pure-LOC ceiling. The first LOC command had a
PowerShell parser error caused by piping directly after `foreach`; the corrected
read-only command wrapped the loop in an array and produced the table above.

`git diff --check` exited 0. Git emitted only the existing informational LF-to-CRLF
working-copy warning for `engine/application/__init__.py`.

## Dirty, stale, and misleading-success checks

- **Dirty state:** the two production initializers were already modified and the
  new test/fix evidence were already untracked when this gate began. No unrelated
  existing change was reset, reverted, stashed, checked out, deleted, or edited.
- **Stale state:** refuted for the narrow claim by standalone `python -B` probes,
  subprocess-based tests, and five focused repeats.
- **Misleading success:** refuted for the narrow claim by explicit `sys.modules`
  booleans, all-object identity comparisons, defining-module names, and lazy-error
  types rather than exit code alone.
- **Broader misleading success:** confirmed if the result were summarized only as
  "import isolation fixed"; the L7-L9 module list demonstrates why the gate remains
  `needs-fix` under the recorded authority.

## Cleanup

Exact process command returned `NO_IMPORT_GATE_PYTHON_OR_PYTEST_PROCESSES`.

Exact temp-artifact command returned `NO_TASK14_IMPORT_GATE_TEMP_ARTIFACTS`.

No debugger, server, port, temporary fixture, or environment override was created.
The only write made by this independent gate is this evidence file.

## Rework rerun - final authority

This section supersedes the historical failed-gate observations above.

### Five-module fresh-process proof

Exact command:

```powershell
@'
import json,sys
forbidden=('engine.application.pipeline_runner','engine.v5.runner','engine.decision.l7_report_view','engine.decision.l8_feedback_attribution','engine.decision.l9_calibration')
before={name:name in sys.modules for name in forbidden}
from engine.application.governance_shadow_runner import run_governance_shadow
after={name:name in sys.modules for name in forbidden}
print(json.dumps({'before':before,'after':after,'loaded':[name for name in forbidden if name in sys.modules]},sort_keys=True))
'@ | python -B -
```

Result: exit 0.

```json
{"after": {"engine.application.pipeline_runner": false, "engine.decision.l7_report_view": false, "engine.decision.l8_feedback_attribution": false, "engine.decision.l9_calibration": false, "engine.v5.runner": false}, "before": {"engine.application.pipeline_runner": false, "engine.decision.l7_report_view": false, "engine.decision.l8_feedback_attribution": false, "engine.decision.l9_calibration": false, "engine.v5.runner": false}, "loaded": []}
```

The five-module authority passes in one genuinely fresh interpreter.

### Explicit export identity, cache, and errors

An independent `python -B -` probe enumerated `app._LAZY_EXPORTS` and
`decision._LAZY_EXPORTS`, resolved every target against its defining module,
accessed each export twice, and inspected the package cache. It then tested an
unknown name and a deliberately missing deferred module.

Result: exit 0.

```json
{"after": {"engine.application.pipeline_runner": true, "engine.decision.l7_report_view": true, "engine.decision.l8_feedback_attribution": true, "engine.decision.l9_calibration": true, "engine.v5.runner": true}, "application_all_identity": true, "application_count": 10, "application_failures": [], "before": {"engine.application.pipeline_runner": false, "engine.decision.l7_report_view": false, "engine.decision.l8_feedback_attribution": false, "engine.decision.l9_calibration": false, "engine.v5.runner": false}, "broken": {"cached": false, "message": "No module named 'no'", "type": "ModuleNotFoundError"}, "decision_all_identity": true, "decision_count": 9, "decision_failures": [], "unknown": {"message": "module 'engine.decision' has no attribute 'missing_export'", "type": "AttributeError"}}
```

All ten application exports and all nine affected decision exports retain object
identity, repeat identity, and successful cache identity. Explicit access loads
the five real modules. Unknown access remains `AttributeError`; failed deferred
import remains `ModuleNotFoundError` and is not cached.

### Regressions and repeatability

```powershell
python -m pytest tests/application/test_application_import_isolation.py -q
```

Result: exit 0, `4 passed in 3.21s`.

```powershell
python -m pytest tests/application/test_governance_shadow_runner.py tests/governance/test_static_isolation.py tests/test_architecture_dependencies.py -q
```

Result: exit 0, `31 passed in 4.32s`.

```powershell
python -m pytest tests/application tests/governance/test_static_isolation.py tests/test_architecture_dependencies.py tests/test_production_entrypoints_unchanged.py tests/v2/test_v2_pipeline_compatibility.py tests/test_wenzhen_recompute.py tests/test_performance_and_ports.py tests/test_error_policy.py -q
```

Result: exit 0, `120 passed, 1 warning in 94.19s (0:01:34)`. The warning is the
pre-existing `dual_engine_adapter` deprecation reached by explicit production
pipeline coverage.

Five immediate focused reruns all exited 0:

```text
RUN 1 - 4 passed in 3.35s
RUN 2 - 4 passed in 2.43s
RUN 3 - 4 passed in 1.66s
RUN 4 - 4 passed in 2.88s
RUN 5 - 4 passed in 1.82s
```

### Rework quality and LOC

```text
ruff check: All checks passed!
ruff format --check: 3 files already formatted
no-excuse: no violations in 3 file(s)
git diff --check: exit 0; existing LF-to-CRLF informational warning only
```

| File | Physical lines | Nonblank/noncomment | Bytes |
| --- | ---: | ---: | ---: |
| `engine/application/__init__.py` | 74 | 61 | 2273 |
| `engine/decision/__init__.py` | 157 | 144 | 4792 |
| `tests/application/test_application_import_isolation.py` | 125 | 96 | 6249 |

All changed Python files remain below the 250 pure-LOC ceiling.

### Final cleanup

- Process probe: `NO_IMPORT_GATE_PYTHON_OR_PYTEST_PROCESSES`.
- Temp probe: `NO_TASK14_IMPORT_GATE_TEMP_ARTIFACTS`.
- No product/test file was edited by this rerun.
- No existing dirty change was reset, reverted, stashed, checked out, or deleted.
- The only rerun write was this evidence update.
