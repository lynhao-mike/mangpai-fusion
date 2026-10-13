# W2-C1 Yang marriage typed governance adapter — VERIFY evidence

## Gate status

- Unit: `W2-C1`
- Gate: `VERIFY`
- Verdict: `PASS` for the exact selectors listed below.
- Authority: `.omo/drafts/multi-school-governance-wave2-yang-marriage-2026-08-06.md` CONTRACT R5 PASS and `.omo/plans/multi-school-governance-wave2-yang-marriage-2026-08-06.md` plan R2 PASS.
- Latest prerequisite review: STATIC_REVIEW R7 `PASS` on the same final implementation and test files.
- Evidence boundary: this record proves only the typed adapter behavior covered by the exact selectors. It does not prove a full-repository pass, Wave 2 completion, capability eligibility, prediction accuracy, proposal readiness, publication, deployment, or production authorization.

## Final implementation scope

- `engine/application/governance_yang_marriage_adapter.py`
- `tests/application/test_governance_yang_marriage_adapter.py`
- `engine/application/__init__.py` was not modified.
- No registry, runner, pipeline, scoring, feedback, report, publication, or production-switch integration was added.

## Root-cause and failure history retained

1. TDD RED was valid: collection succeeded, while execution failed because `engine.application.governance_yang_marriage_adapter` did not yet exist.
2. The first minimal implementation reached an initial focused GREEN.
3. After the expanded final matrix, the first final focused VERIFY run produced `38 passed / 1 failed`. The failure was `test_first_import_has_no_forbidden_module_side_effect`.
4. Read-only diagnosis showed the only matching newly observed module was `engine.governance.school_registry_loader`.
5. Minimal fresh-process boundary probes established:
   - importing `engine.application.governance_claim_adapter_values` alone loads `engine.governance.school_registry_loader` through the existing `engine.governance` facade;
   - importing `engine.decision.yang_marriage` does not load that governance loader;
   - after preloading the target adapter's four explicit allowed dependencies, importing the target adapter adds no loader or registry module.
6. Root cause: the test attributed an existing allowed dependency facade's transitive import baseline to the target adapter. This was a test-boundary error, not an adapter-introduced registry-loader dependency.
7. The test was revised to establish a fresh-process baseline from the four explicit dependencies before measuring the target adapter's incremental imports. Static AST checks were strengthened in parallel to freeze exact module/symbol/alias bindings and reject forbidden or dynamic import paths, so the baseline does not conceal adapter dependency drift.
8. Every test revision invalidated the preceding static-review verdict. Fresh reviews R4, R5, and R6 returned `REVISE`; each concrete finding was corrected. STATIC_REVIEW R7 returned `PASS`. No VERIFY selector was rerun until that fresh PASS.
9. The failed `38 passed / 1 failed` run remains part of the audit history and is not overwritten by the final rerun.

## Root-cause diagnostic command

Working directory for every command in this record: `f:/多流派新思路`.

```text
python -B -c "import importlib,json,sys; before=set(sys.modules); importlib.import_module('engine.application.governance_claim_adapter_values'); print(json.dumps(sorted(x for x in set(sys.modules)-before if x.startswith('engine.') and ('loader' in x or 'registry' in x))))" && python -B -c "import importlib,json,sys; before=set(sys.modules); importlib.import_module('engine.decision.yang_marriage'); print(json.dumps(sorted(x for x in set(sys.modules)-before if x.startswith('engine.') and ('loader' in x or 'registry' in x))))" && python -B -c "import importlib,json,sys; importlib.import_module('engine.application.governance_claim_adapter_values'); importlib.import_module('engine.decision.yang_marriage'); before=set(sys.modules); importlib.import_module('engine.application.governance_yang_marriage_adapter'); print(json.dumps(sorted(x for x in set(sys.modules)-before if x.startswith('engine.') and ('loader' in x or 'registry' in x))))"
```

- Observed at: 2026-08-06 23:46 CST
- Exit code: `0`
- Output groups:
  - adapter-values baseline included `engine.governance.school_registry_loader`;
  - Yang decision import did not include it;
  - target adapter incremental import after allowed dependency baseline was `[]`.

## Fresh final selector accounting

### 1. Collection-only

```text
python -B -m pytest --collect-only -q -p no:cacheprovider tests/application/test_governance_yang_marriage_adapter.py
```

- Started: 2026-08-07 00:03 CST
- Finished: 2026-08-07 00:03 CST
- Exit code: `0`
- Collected: `39`
- Executed: `0`
- Deselected: `0`
- Skipped: `0`
- Xfailed: `0`
- Failed: `0`
- Errored: `0`
- Passed: not applicable to collection-only
- Pytest summary: `39 tests collected in 0.41s`

### 2. Focused W2-C1 contract tests

```text
python -B -m pytest -q -p no:cacheprovider tests/application/test_governance_yang_marriage_adapter.py
```

- Started: 2026-08-07 00:03 CST
- Finished: 2026-08-07 00:03 CST
- Exit code: `0`
- Collected: `39`
- Executed: `39`
- Deselected: `0`
- Skipped: `0`
- Xfailed: `0`
- Failed: `0`
- Errored: `0`
- Passed: `39`
- Pytest summary: `39 passed in 2.87s`

This selector contains the fresh-process source-ref/derivation/claim/content stability check, subprocess return/stderr assertions, static AST isolation check, and dependency-baselined first-import side-effect check.

### 3. Yang marriage regressions

```text
python -B -m pytest -q -p no:cacheprovider tests/yang_marriage/test_domain_model.py tests/yang_marriage/test_signal_families.py tests/yang_marriage/test_school_claim_adapter.py
```

- Started: 2026-08-07 00:03 CST
- Finished: 2026-08-07 00:03 CST
- Exit code: `0`
- Collected: `81`
- Executed: `81`
- Deselected: `0`
- Skipped: `0`
- Xfailed: `0`
- Failed: `0`
- Errored: `0`
- Passed: `81`
- Pytest summary: `81 passed in 0.76s`

### 4. Governance adapter regressions

```text
python -B -m pytest -q -p no:cacheprovider tests/application/test_governance_claim_adapter_boundaries.py tests/application/test_governance_claim_adapter_derivation.py
```

- Started: 2026-08-07 00:04 CST
- Finished: 2026-08-07 00:04 CST
- Exit code: `0`
- Collected: `7`
- Executed: `7`
- Deselected: `0`
- Skipped: `0`
- Xfailed: `0`
- Failed: `0`
- Errored: `0`
- Passed: `7`
- Pytest summary: `7 passed in 1.85s`

## Aggregate accounting

- Collection-only instances: `39` collected, zero collection errors.
- Behavioral instances executed across final selectors: `127`.
- Passed: `127`.
- Failed: `0`.
- Errored: `0`.
- Skipped: `0`.
- Xfailed: `0`.
- Deselected: `0`.
- Every final command exited `0`.

## Frozen source and semantics witness

- School: `yang_qingjuan`
- Task: `marriage.divorce_or_remarriage`
- Kind/stance/scope/grade: `event` / `support` / `natal` / `inferential`
- Confidence: `0.60`
- Adapter version: `yang-marriage-discrimination/v1`
- Source SHA-256: `e8be77f67246ff056770a35d618b4b3fc5694ba5fdec2f65c8d674708355e768`
- Exact anchors:
  - `theory/yang/index.yaml#M2-Y-068`
  - `theory/yang/index.yaml#M2-Y-088`
- Three-state order remains: concrete type → state → event exact refs → typed provenance/derivation/spec → catalog/claim.
- `pressure` and `abstain` remain typed `INSUFFICIENT_EVIDENCE` losses and cannot reach source/catalog validation.

## Historical and authorization boundary

- The historical Wave 1 exact Gate D collection failure at `tests/test_application_candidates.py:21` remains explicitly outside these focused selectors. This W2-C1 PASS does not erase, supersede, or reclassify it.
- Pre-existing tracked and untracked workspace changes were preserved.
- No reset, clean, checkout, restore, stash, rebase, commit, or GitHub service-side mutation was performed.
- The adapter remains shadow-only and unregistered. Production release remains an independent manual authorization.

## VERIFY verdict

`PASS` — exact W2-C1 selectors are fresh, complete, replayable, and internally consistent with STATIC_REVIEW R7. Next legal gate: fresh `EVIDENCE_REVIEW`; no freeze or handoff is implied by this VERIFY record alone.
