# Task 13 Gate D Syntax Debug Journal

- Started: 2026-08-05 Asia/Shanghai
- Goal: classify `tests/test_application_candidates.py:21` collection SyntaxError as Wave1-introduced, pre-existing unrelated, or inconclusive without modifying user files.
- Runtime: CPython / pytest; exact environment evidence delegated.
- Entry: `python -m pytest tests/ -q -p no:cacheprovider`
- Working tree: dirty; no reset, checkout, restore, stash, commit, or source edit permitted.
- References read: `omo:debugging` Python runtime, setup, investigation; `omo:git-master` history mode.

## Hypotheses

1. **H1 local truncation**: the current uncommitted file contains a syntactically incomplete local edit unrelated to Wave1. Distinguishing evidence: current diff contains the unmatched bracket, HEAD parses, and no Wave1-owned artifact names this file.
2. **H2 baseline defect**: the committed baseline already contains the syntax defect, making it pre-existing. Distinguishing evidence: `git show HEAD:tests/test_application_candidates.py` fails the same isolated parse and history predates Wave1.
3. **H3 concurrent/transient state**: Gate D observed the file while another process was writing it. Distinguishing evidence: mtime/size/hash or parse result changes across bounded repeated read-only snapshots.

## Artifacts

- Gate D evidence: `.omo/evidence/task13-gate-d-full.md` and associated logs.
- Investigation reports: delegated read-only agents; no temporary source instrumentation or debugger ports.

## Findings

- HEAD source parses; current source has a stable `SyntaxError` at line 21 across three identical hashes.
- Current dirty delta is `+15/-0` and inserts a new test before the prior assertion list closes.
- File mtime is `2026-08-02T17:22:11.8725934+08:00`, about 19h53m before Wave1 Boulder creation at `2026-08-03T13:14:59.8291462+08:00`.
- Wave1 ledger/artifacts/notepads contain no ownership reference to this file. Classification: strong evidence of pre-existing unrelated dirty edit.
- Supplemental full suite excluding this file timed out twice: 300s at 53%, 900s at 70%, no failure node or stderr.

## Timeout Hypotheses

1. **T1 long but uniformly progressing**: refuted. Collection mapped the 70% endpoint to a fixed node, and isolated execution stalled on that node.
2. **T2 deterministic YAML-scan stall**: confirmed at symptom level. `tests/regression/test_g_iteration.py::test_g001_dry_run_idempotent` stalls alone; faulthandler shows `yaml.scanner.scan_plain`; no child process exists. Causal toggle pending.
3. **T3 shared resource contention**: refuted as root cause. An unrelated VS Code/Roo pytest in another workspace overlapped the run, but the G001 node reproduced alone without children. Contention may increase elapsed time only.

## Root Cause Confirmation

- A uncached: timeout at `35.019s`, 29 YAML reads, 10,420,726 bytes.
- B with an in-memory path-keyed YAML read cache: `1 passed in 15.50s`; 182 logical reads became 6 physical parses and 176 cache hits.
- C fresh uncached: timeout at `35.067s`, 30 YAML reads, 13,218,622 bytes.
- Mechanism: the pre-existing G001 regression test repeatedly invokes `load_rule` / `_locate_rule_in_yaml`, reparsing multi-megabyte YAML indexes on each lookup.
- Attribution: pre-existing unrelated to Wave1. Target test and product files have no current diff and their latest commits predate Wave1 by months.
- Evidence: `.omo/evidence/task13-g001-yaml-toggle.md`.

## Cleanup

- Complete: no source or test instrumentation was written.
- Complete: all scoped debug/pytest processes were terminated by their bounded wrappers.
- Complete: no debugger ports, breakpoints, environment overrides, or temporary repo fixtures remain.
- Preserved: unrelated VS Code/Roo pytest processes were not modified.
- Preserved as durable evidence: this `.omo/evidence/` journal and referenced reports.
