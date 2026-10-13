# Task13 Timeout Stall Locator (T2)

## Verdict

**T2 CONFIRMED.** The excluding-known suite timeout localizes exactly to:

`tests/regression/test_g_iteration.py::test_g001_dry_run_idempotent`

The candidate reproduces in isolation. This is not a collection stall, and no nested pytest/subprocess child was present. The live Python stack was inside PyYAML's `yaml.scanner.scan_plain` while the node was unresolved. That stack supports expensive/repeated YAML parsing as the mechanism, but this bounded locator did not perform a causal toggle, so it is not presented as a fully confirmed product root cause.

## Source Evidence

- Prior command: `python -m pytest tests/ -q -p no:cacheprovider --ignore=tests/test_application_candidates.py`
- Prior rerun bound/result: 900 seconds, timeout, no final pytest summary.
- Prior rerun stdout shape: 41 complete progress rows of 72 outcomes plus 30 outcomes on the partial row.
- Exact completed outcomes before stall: `41 * 72 + 30 = 2982`.
- Prior stdout ended after `[ 70%]` followed by exactly 30 dots.

## Collection-Order Mapping

Command:

```powershell
python -m pytest tests/ --collect-only -q -p no:cacheprovider --ignore=tests/test_application_candidates.py
```

Result:

- Exit: `0`
- Collected: `4206 tests` in `12.83s`
- Ordinal 2981: `tests/regression/test_e_guardrails.py::test_E007_forbidden_phrase_warning`
- Ordinal 2982: `tests/regression/test_e_guardrails.py::test_E008_duplicate_fingerprint`
- Ordinal 2983: `tests/regression/test_g_iteration.py::test_g001_dry_run_idempotent`
- Ordinals 2983-2986 are the four nodes in `tests/regression/test_g_iteration.py`.

Therefore the first unreported outcome after the exact 2,982 progress symbols is ordinal 2,983, the first node in `test_g_iteration.py`.

## Candidate Inspection

Static inspection of `tests/regression/test_g_iteration.py` found:

- No `subprocess`, `Popen`, multiprocessing, nested `pytest`, sleep, or unbounded loop.
- The first node calls `ingest_feedback(CASE_001, dry_run=True)` twice.
- `tools.feedback_loop.ingest_feedback` calls `load_rule` once per derived rule ID during dry-run.
- `tools.rule_lifecycle.load_rule` calls `_locate_rule_in_yaml`, which reparses each school `index.yaml` in sequence for every lookup.
- The case produced 13 conclusions and 25 unique rule IDs in a read-only parse probe.
- The two largest scanned indexes were `theory/ziping/index.yaml` (`2,613,702` bytes) and `theory/tiaohou_ditiansui/index.yaml` (`2,797,896` bytes).

This module and its direct call path contain no nested pytest/subprocess invocation.

## Bounded Isolated QA

Exact required-style invocation:

```powershell
python -m pytest tests/regression/test_g_iteration.py -vv -s --durations=20 -p no:cacheprovider
```

Observed:

- Python: `C:\Python314\python.exe`, Python `3.14.5`, pytest `8.4.2`.
- Collection: `4 items`.
- Last/only node line: `tests/regression/test_g_iteration.py::test_g001_dry_run_idempotent`.
- No `PASSED`, `FAILED`, duration record, or final summary was emitted.
- Live process: PID `13360`, parent PowerShell PID `15264`.
- Command line: `C:\Python314\python.exe -m pytest tests/regression/test_g_iteration.py -vv -s --durations=20 -p no:cacheprovider`.
- Process tree: one pytest `python.exe`; no Python child process.
- Scoped PID was force-stopped after the node remained unresolved; resulting command exit was `1` due to termination.

Exact-node stack probe used the same `-vv -s --durations=20 -p no:cacheprovider` pytest arguments plus an in-memory `faulthandler.dump_traceback_later(10)` wrapper. It collected one item, remained on the same node, and emitted:

```text
Timeout (0:00:10)!
Thread ... (most recent call first):
  File "C:\Python314\Lib\site-packages\yaml\scanner.py", line ??? in scan_plain
  <invalid frame>
```

Probe process PID `14640` had no pytest/Python child and was force-stopped after the stack capture. No product or test file was edited.

## Hypothesis Disposition

- H1, collection-order boundary is `test_g_iteration.py` first node: **confirmed** by exact symbol count and 4,206-node collection order.
- H2, timeout is caused by nested subprocess/nested pytest: **refuted** by static scan and live single-process tree.
- H3, timeout requires cumulative prior-suite state: **refuted for reproduction** because the first node stalls when its four-test module is run alone.
- H4, repeated YAML parsing is the underlying performance mechanism: **supported, not causally confirmed** by source path plus live `yaml.scanner.scan_plain` stack; no toggle was authorized or performed.

## Cleanup

- Both scoped Python PIDs (`13360`, `14640`) were stopped.
- Final process check found no live `python.exe`.
- No source/test/config files were edited.
- Only this requested evidence file was created.
