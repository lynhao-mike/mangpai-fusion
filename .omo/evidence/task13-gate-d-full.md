# Wave1 Task13 Gate D Full Test Evidence

## Result

Gate D: FAIL

Surface: pytest full suite
Exact invocation: `python -m pytest tests/ -q -p no:cacheprovider`
Working directory: `F:\多流派新思路`
Timeout bound: 3600 seconds

Primary recorded run:
- start: 2026-08-05T10:55:41.9426514+08:00
- end: 2026-08-05T10:56:06.6983474+08:00
- durationSeconds: 24.756
- exit: 2
- passed: 0
- skipped: 0
- failed: 0
- errors: 1
- warnings: 1

Note: an initial run produced the same collection error, but its wrapper did not reliably preserve the native pytest exit code. The primary recorded run above re-ran the exact pytest command with process-level timeout and captured exit code 2.

## Failure Classification

Classification: inconclusive

Reason: failure is a collection-time SyntaxError in `tests/test_application_candidates.py`, which is modified in the dirty worktree. This QA pass cannot attribute the modified test file to Wave1 Task13 versus unrelated pre-existing local work without a trusted baseline/ownership record.

Full failure node:
- `ERROR tests/test_application_candidates.py`

First traceback / error:

```text
ERROR collecting tests/test_application_candidates.py
C:\Python314\Lib\site-packages\_pytest\python.py:498: in importtestmodule
    mod = import_path(
C:\Python314\Lib\site-packages\_pytest\pathlib.py:587: in import_path
    importlib.import_module(module_name)
C:\Python314\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
...
C:\Python314\Lib\ast.py:46: in parse
    return compile(source, filename, mode, flags,
E     File "F:\多流派新思路\tests\test_application_candidates.py", line 21
E       assert _extract_candidates(cast(ParsedInput, parsed)) == [
E                                                                ^
E   SyntaxError: '[' was never closed
```

## manualQa

### surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
|---|---|---|---|---|---|
| D-FULL-001 | Wave1 Task13 Gate D full tests | pytest full suite | `python -m pytest tests/ -q -p no:cacheprovider` from `F:\多流派新思路` | FAIL: collection interrupted with 1 error, exit 2 | A1, A2, A3 |

### adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
|---|---|---|---|---|---|
| D-FULL-ADV-001 | Gate D must tolerate full-suite collection | Syntax-invalid test module during collection | Suite should collect and run without SyntaxError; any failure should be executable test failure, not collection abort | FAIL: `tests/test_application_candidates.py` has unclosed `[` at line 21 | A1, A3 |
| D-FULL-ADV-002 | Gate D evidence hygiene | Residual scoped pytest/Python process or generated cache after run | No scoped pytest/Python process remains; task-scoped pycache is cleaned | PASS | A4, A5 |

### artifactRefs

| id | kind | description | path |
|---|---|---|---|
| A1 | pytest log | Full stdout/stderr for primary recorded rerun | `F:\多流派新思路\.omo\evidence\task13-gate-d-full-pytest-rerun.log` |
| A2 | metadata json | Start/end/duration/timeout/exit/byte counts for primary recorded rerun | `F:\多流派新思路\.omo\evidence\task13-gate-d-full-meta-rerun.json` |
| A3 | pytest log | Initial run output showing same collection error; native exit unreliable due wrapper, retained as corroborating artifact | `F:\多流派新思路\.omo\evidence\task13-gate-d-full-pytest.log` |
| A4 | process check | Scoped python/pytest process check after run | `F:\多流派新思路\.omo\evidence\task13-gate-d-full-process-check.txt` |
| A5 | cleanup log | Scoped `__pycache__` cleanup log | `F:\多流派新思路\.omo\evidence\task13-gate-d-full-pycache-cleanup.txt` |
| A6 | cleanup script | Evidence-directory script used for scoped process/cache cleanup | `F:\多流派新思路\.omo\evidence\task13-gate-d-full-cleanup.ps1` |
| A7 | initial metadata json | Initial run metadata; exit code not used for verdict because wrapper captured it unreliably | `F:\多流派新思路\.omo\evidence\task13-gate-d-full-meta.json` |
