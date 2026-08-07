# Task13 G001 YAML Toggle Proof

Date: 2026-08-06 (Asia/Shanghai)

## Verdict

**ROOT CAUSE CONFIRMED by A-bad / B-good / C-bad toggle.**

The timeout at `tests/regression/test_g_iteration.py::test_g001_dry_run_idempotent` is caused by repeated uncached full-file YAML parsing in the dry-run rule lookup path:

`test_g001_dry_run_idempotent` -> `ingest_feedback(..., dry_run=True)` twice -> `_apply_rule_verdicts` -> `load_rule` -> `_locate_rule_in_yaml` -> `_read_yaml` for each candidate school index on every lookup.

With the existing uncached `_read_yaml`, the exact node failed to finish at both 35-second bounds. Replacing only `_read_yaml` in memory with a `Path`-keyed cache made the unchanged node and assertions pass. Starting a fresh interpreter without the cache reproduced the timeout.

Wave1 attribution: **pre-existing and unrelated to Wave1.** The test and its two direct product files have no working-tree diff, predate Wave1 by months, are absent from the Wave1 ownership ledger, and Wave1 explicitly excludes modifications to feedback/learning write paths.

## Unchanged Observable

All three toggles ran the same node through pytest:

```text
tests/regression/test_g_iteration.py::test_g001_dry_run_idempotent
```

Common pytest arguments:

```text
-vv -s --durations=20 -p no:cacheprovider
```

The harness was piped to `python -` and existed only in memory. It did not edit a source or test file. `PYTHONDONTWRITEBYTECODE=1` was set for every toggle.

## YAML Surface

| path | bytes |
|---|---:|
| `theory/duan/index.yaml` | 93,805 |
| `theory/yang/index.yaml` | 69,584 |
| `theory/gao/index.yaml` | 163,926 |
| `theory/ren/index.yaml` | 75,866 |
| `theory/ziping/index.yaml` | 2,613,702 |
| `theory/tiaohou_ditiansui/index.yaml` | 2,797,896 |
| **one physical load of all six** | **5,814,779** |

The case parse produced 13 conclusions and 25 unique rule IDs. `_locate_rule_in_yaml` may read several school indexes for each rule lookup, so YAML read-call count exceeds rule count.

## Toggle A - Uncached Bad

Change from product behavior: instrumentation counters only; `_read_yaml` delegated directly to the original function with no cache.

Bound: `35.0s`.

Result:

```text
TOGGLE_A_TIMEOUT duration=35.019s calls=29 parsed_bytes=10420726
last_path='...\theory\ziping\index.yaml'
per_path={
  duan: 12,
  yang: 9,
  gao: 3,
  ren: 2,
  ziping: 2,
  tiaohou_ditiansui: 1
}
```

- Pytest collected one item and printed the exact node, but emitted no `PASSED`, `FAILED`, duration table, or final summary.
- Harness timeout path called `os._exit(124)`; the outer PowerShell pipeline surfaced process exit `1` after the forced harness termination.
- Observable verdict: **BAD / TIMEOUT**.

## Toggle B - Cached Good

Change from product behavior: only `tools.rule_lifecycle._read_yaml` was monkeypatched in memory with an unbounded `functools.lru_cache` keyed by `Path`. The original parser still performed every cache miss. Test code and assertions were unchanged.

Bound: `60.0s`.

Result:

```text
tests/regression/test_g_iteration.py::test_g001_dry_run_idempotent PASSED
1 passed in 15.50s
TOGGLE_B_DONE duration=15.922s exit=0 logical_calls=182
physical_loads=6 cache_hits=176 physical_bytes=5814779
physical_per_path={duan: 1, yang: 1, gao: 1, ren: 1, ziping: 1, tiaohou_ditiansui: 1}
```

- Pytest exit: `0`.
- Pytest call duration: `15.24s`.
- Harness duration: `15.922s`.
- The original assertion ran and passed.
- Observable verdict: **GOOD / PASS**.

## Toggle C - Cache Removed, Bad Again

Change from product behavior: fresh Python interpreter, instrumentation counters only, original uncached `_read_yaml` restored by process isolation.

Bound: `35.0s`.

Result:

```text
TOGGLE_C_TIMEOUT duration=35.067s calls=30 parsed_bytes=13218622
last_path='...\theory\tiaohou_ditiansui\index.yaml'
per_path={
  duan: 12,
  yang: 9,
  gao: 3,
  ren: 2,
  ziping: 2,
  tiaohou_ditiansui: 2
}
```

- Pytest collected one item and printed the exact node, but emitted no outcome or final summary.
- Harness timeout path called `os._exit(124)`; the outer PowerShell pipeline surfaced process exit `1` after the forced harness termination.
- Observable verdict: **BAD / TIMEOUT**.

## Causal Conclusion

The captured value matches the hypothesis: the good run made 182 logical YAML lookups, but caching reduced physical parsing to exactly six files and 5,814,779 bytes. The uncached runs repeatedly parsed the same files and accumulated 10,420,726 and 13,218,622 attempted bytes before their respective bounds.

The result is reproducible and reversible:

| toggle | cache | result | duration | physical/counted reads | bytes |
|---|---|---|---:|---:|---:|
| A | off | timeout | 35.019s | 29 | 10,420,726 |
| B | on | 1 passed, exit 0 | 15.922s harness | 6 physical / 182 logical | 5,814,779 physical |
| C | off again | timeout | 35.067s | 30 | 13,218,622 |

Therefore repeated uncached parsing in `load_rule` / `_locate_rule_in_yaml` is the confirmed cause of the G001 timeout on this runtime. This evidence does not select or authorize a permanent fix.

## Wave1 Attribution

Targeted `git status --short`, `git diff --stat`, and `git diff --name-status` produced no output for:

- `tests/regression/test_g_iteration.py`
- `tools/feedback_loop.py`
- `tools/rule_lifecycle.py`
- all six scanned `theory/*/index.yaml` files

Latest commits:

| file | latest commit | commit date |
|---|---|---|
| `tests/regression/test_g_iteration.py` | `547f4542aed768178b810a935acd32b548f17ffd` | 2026-05-30 08:48:42 +0800 |
| `tools/feedback_loop.py` | `79e663c4a37d7afd2530c403dedd311e95db207f` | 2026-06-22 16:45:24 +0800 |
| `tools/rule_lifecycle.py` | `79e663c4a37d7afd2530c403dedd311e95db207f` | 2026-06-22 16:45:24 +0800 |

Wave1 is the active `multi-school-governance-wave1-2026-08-03` work. Its authority plan states: `Wave 1 does not modify report, feedback, learning-write, or production-release flows.` Its planned new data files are `theory/ziping/structure-catalog-v1.yaml` and `theory/multi-school-governance-v1.yaml`, not the six legacy `index.yaml` files scanned here. The Wave1 execution ledger/notepads/artifacts contain no ownership reference to the three candidate files.

Classification: **confirmed pre-existing, unrelated to Wave1**.

## Cleanup

- No product, test, config, or YAML file was edited.
- No harness file was created; all monkeypatches died with their Python processes.
- No scoped toggle Python process remained after A, B, or C.
- Target `.pyc` files already existed before the toggle with June timestamps; bytecode writes were disabled and those files were not modified or deleted.
- One Python process remained in the final machine-wide process list, but its command line is an unrelated pytest run targeting `test_web_accountability_browser_e2e.py` / `test_web_accountability_e2e.py`, not the G001 harness. It was left untouched.
- The only created artifact is this evidence file.
