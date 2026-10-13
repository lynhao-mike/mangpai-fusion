# Task14 Review-Work Hands-On QA Final

Date: 2026-08-06 (Asia/Shanghai)  
Workspace: `F:\多流派新思路`  
Lane: final hands-on QA for Wave1; no subagents; no product/test edits  
Verdict: **PASS**  
Confidence: **high**

## Scope And Authority

This lane read and applied:

- `AGENTS.md`, including its fact-source and dirty-worktree rules.
- `plans/multi-school-governance-design-2026-08-02.md`, especially sections 4-15.1.
- `plans/multi-school-governance-wave1-implementation-2026-08-02.md`, especially completion definition 1.8 and Tasks 1-14.
- `.omo/evidence/task14-wave1-exit-audit-final.md` (13,335 bytes), which gives the bounded final exit-audit PASS.
- Task13 primary evidence, including `.omo/evidence/task13-gates-abce.md`, `.omo/evidence/task13-gate-d-full.md`, `.omo/evidence/task13-gate-d-remaining-suite.md`, and the dated Wave1 validation record.

S01-S23 each ran in a fresh interpreter from `F:\多流派新思路` using the exact command form `python -B -c "<scenario code>"`. `-B` disabled bytecode writes. The scenario table gives the exact public calls, controls, assertions, and observed semantic values. Test fixture helpers were imported only to construct typed inputs for arbitration, composition, trigger, and shadow scenarios; every operation under review called the public product surface directly.

S24 used exact focused commands reproduced below. The approximately 20-minute Task13 remaining-suite run was deliberately not repeated.

## Result Summary

| Item | Result |
|---|---|
| Planned scenarios | 24 |
| Executed scenarios | 24 |
| Scenario priorities | 19 P0, 5 P1, 0 P2 |
| Semantic PASS | 24 |
| Product failures | P0: 0; P1: 0; P2: 0 |
| 429 / unavailable execution | 0 |
| Timeout / hung owned process | 0 |
| Focused pytest | 134 passed; 222 passed, 1 known warning |
| Repository checks | tool registry PASS; rule status PASS |

## Prioritized Scenarios

### Canonical, Facts, Certification, And Schools

| ID | Pri | Exact calls / controls | Expected | Actual | Result |
|---|---|---|---|---|---|
| S01 | P0 | `canonical_digest()` on reordered/equal and changed mappings; `stable_object_id("fact", ...)` | Reordering stable; content change different; namespaced stable ID | Equal digest `90f74f...f5ad`; changed content differed; ID began `fact:` | PASS |
| S02 | P0 | `canonical_digest()` with NaN and a cyclic list; `stable_object_id("Fact", ...)` | Fail closed with typed issue codes | `CANONICAL.NON_FINITE_NUMBER`, `CANONICAL.CYCLE_DETECTED`, `CANONICAL.NAMESPACE_INVALID` | PASS |
| S03 | P0 | `build_governance_fact()` from mutable input, mutate source, then `build_fact_snapshot()` in forward/reverse order | Deep freeze; source mutation isolated; snapshot order independent | Payload stayed `{'items': ('a',)}`; both two-fact snapshots equal with digest `0130ca...0d9f` | PASS |
| S04 | P0 | Construct liunian `TemporalScope` without year; snapshot duplicate and same-ID/different-content facts | Missing year, duplicate, and conflict fail closed | `FACT.LIUNIAN_TARGET_REQUIRED`, `DuplicateFactIdError`, `ConflictingFactIdError` | PASS |
| S05 | P0 | Build a correctly content-bound published L2A `FactCertification`; exact and stale-version lookup | Exact lookup returns certification; no adjacent-version fallback | `FactCertification`; stale `1.0.1` returned `CERTIFICATION.UNSUPPORTED` | PASS |
| S06 | P0 | Partial `CertificationIdentity` with empty version; L2B certification with only one school review | Both malformed/partial cases rejected | `CERTIFICATION.TEXT_REQUIRED`, `CERTIFICATION.L2B_REVIEWS` | PASS |
| S07 | P0 | `load_school_registry()`, exact Ditiansui and unknown lookup, boundary alias normalization | Exactly five peers; Ditiansui legacy-only; unknown typed; `gao` boundary-normalized | Five IDs exact; `LegacyCompatibilitySource`; `SCHOOL.UNKNOWN`; alias became `gao_dechen` | PASS |

### Claim Adapters And Seven-Gate Arbitration

| ID | Pri | Exact calls / controls | Expected | Actual | Result |
|---|---|---|---|---|---|
| S08 | P0 | `adapt_decision_school_claim()` on a valid legacy Yang event claim with explicit natal scope and registered refs | Canonical school and source provenance retained | School `yang_qingjuan`; `adapter_provenance.source_claim_ref == "legacy-yang"`; stable derivation digest | PASS |
| S09 | P0 | Adapter inputs: duck-typed fake, missing temporal scope, Yang pressure claim | No claim manufactured; precise loss classification | `ADAPTER_INPUT_INVALID`, `TEMPORAL_SCOPE_MISSING`, `UNSUPPORTED_LEGACY_CLAIM` | PASS |
| S10 | P0 | `arbitrate()` for both permutations and replay of the same typed arena | Fixed seven gates; permutation invariant; idempotent | Gates: eligibility, temporal, evidence, independence, counterevidence, applicability, decision; consensus; one digest | PASS |
| S11 | P0 | `arbitrate()` with an exact same-source copy, then shared fact with distinct complete rule sources | Copy does not add an independent vote; distinct sources stay distinct | Folded group count 1 and retained variant count 1; distinct group count 2 | PASS |
| S12 | P0 | `arbitrate()` on empty arena and arena with explicit `FactConflictContext` | Empty abstains; fact conflict fails closed before theory decision | `abstain`; `ARBITRATION.FACT_CONFLICT: fact has incompatible contents` | PASS |

### Restricted Composition

| ID | Pri | Exact calls / controls | Expected | Actual | Result |
|---|---|---|---|---|---|
| S13 | P1 | `execute_composition()` for both component permutations in explicit `SHADOW` mode | Order-independent replay; cap evidence; preserve components | `composed`; `corroborated`; one digest; two components retained | PASS |
| S14 | P1 | Unknown template version, one missing component, duplicate same-source component, and `PRODUCTION` execution | Typed non-claim outcomes; no implicit authority | `UNSUPPORTED_TEMPLATE`, `COMPONENTS_REQUIRED`, `INDEPENDENT_COMPONENTS_REQUIRED`, `PRODUCTION_FORBIDDEN` | PASS |

### Trigger And Explicit-Year Boundaries

| ID | Pri | Exact calls / controls | Expected | Actual | Result |
|---|---|---|---|---|---|
| S15 | P0 | `evaluate_governance_trigger()` with explicit `chart.liunian` fact scoped to target year 2026 while `as_of_date=1999-01-01` | Explicit fact activates regardless of unrelated as-of date | `active=True`, no issues | PASS |
| S16 | P0 | Unknown trigger; liunian trigger with only natal fact plus `as_of_date` and parsed object; natural-language/lambda evaluator ID | Unknown and missing-year cases inactive; free expression rejected | `unknown_trigger`, `missing_required_fact`, `TRIGGER.EVALUATOR_ID`; both outcomes inactive | PASS |

### Structure Catalog And Projection

| ID | Pri | Exact calls / controls | Expected | Actual | Result |
|---|---|---|---|---|---|
| S17 | P1 | `load_structure_catalog()`; inspect entry count, current implementations, `legacy_projection`, and newly imported modules | Exactly 30; exactly three current mappings; no production loader/trigger import | 30 entries; current IDs are food-god-controls-killing, hurting-officer-controls-killing, killing-generates-seal; three legacy mappings; digest `1b746c...a8bc` | PASS |
| S18 | P1 | Direct `StructureCatalog` construction with forged digest and malformed nested entry | Public boundary rejects both | `STRUCTURE.CATALOG_DIGEST`, `STRUCTURE.CATALOG_TYPE` | PASS |

### Shadow End-To-End, Isolation, And Side Effects

| ID | Pri | Exact calls / controls | Expected | Actual | Result |
|---|---|---|---|---|---|
| S19 | P0 | `run_governance_shadow()` with two school-view orders and with one `SchoolViewFailure` | Order-stable result; available school preserved | Both canonical results/digests equal; status `ok`; decision `consensus`; Ren marked unavailable | PASS |
| S20 | P0 | Shadow run with `target_year=None`; second run includes peer plus Ditiansui legacy claim | No liunian fact; Ditiansui excluded from five-peer arena | Facts only dayun/four-pillars/sex-marker; excluded ref `legacy-ditiansui`; one peer claim retained | PASS |
| S21 | P0 | Shadow request with explicit conflicting fact digests | Arena stops fail closed | Status `fail_closed`; arbitration `None`; issue `ARBITRATION.FACT_CONFLICT` | PASS |
| S22 | P0 | Fresh import of `engine.application` then shadow submodule; inspect forbidden modules, application exports, and `_DEFAULT_SCHOOLS` | No eager production/report/feedback/learning load; shadow not default export; old defaults unchanged | Forbidden loaded `()`; shadow exported `False`; defaults remained `ziping, ditiansui, duan_jianye, yang_qingjuan, ren_fuhong, gao_dechen` | PASS |
| S23 | P0 | Patch `Path.write_text`, `write_bytes`, `mkdir`, and `touch` to fail; run public shadow path with injected read-only dependencies; compare registry | No write API call and no registry mutation | Write call counts `(0, 0, 0, 0)`; registry unchanged; status `ok` | PASS |

### Focused Regression And Repository Checks

| ID | Pri | Exact calls / controls | Expected | Actual | Result |
|---|---|---|---|---|---|
| S24 | P1 | Two exact focused pytest commands below, then both documented registry checks | All focused tests and checks pass; no full 20-minute suite | 134 passed; 222 passed with one pre-existing deprecation warning; both checks passed | PASS |

## S24 Exact Commands

Core public-surface suite:

```text
python -B -m pytest tests/governance/test_canonical.py tests/governance/test_fact_contracts.py tests/governance/test_fact_certification_registry.py tests/governance/test_school_registry.py tests/application/test_governance_claim_adapter_boundaries.py tests/governance/test_arbitration_gates.py tests/governance/test_arbitration_properties.py tests/governance/test_composition_execution.py tests/governance/test_trigger_registry.py tests/governance/test_structure_catalog.py tests/application/test_governance_shadow_runner.py tests/application/test_application_import_isolation.py -q -p no:cacheprovider
```

Actual: exit 0; `134 passed in 15.82s`.

Focused compatibility suite:

```text
python -B -m pytest tests/test_architecture_dependencies.py tests/governance/test_static_isolation.py tests/yang_marriage/test_static_isolation.py tests/decision/test_staged_arbitration.py tests/predicates/test_ten_god_structures.py tests/ren_timing tests/test_production_rule_loader.py tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q -p no:cacheprovider
```

Actual: exit 0; `222 passed, 1 warning in 157.32s`. The warning is the already-disclosed `engine.application.dual_engine_adapter` deprecation warning emitted from `engine/application/pipeline_runner.py:11`; it is not a Wave1 regression.

Repository checks:

```text
python -B tools/tool_registry.py --check
python -B tools/rule_status_scan.py --check
```

Actual: both exit 0; `tool registry check passed`; `rule status scan passed`.

## Harness Corrections

Three initial probe attempts exited 1 because of QA-only output/assertion assumptions. Each scenario was corrected and rerun in a new process; no product behavior was changed and no scenario remained unexecuted.

1. S08 initially looked for `GovernanceClaim.source_claim_refs`. The approved source reference is represented by `adapter_provenance.source_claim_ref`; the corrected semantic assertion passed.
2. S12 initially looked for `ArbitrationIntegrityError.issue_code`. The public typed error renders the code in `str(error)`; the corrected assertion confirmed `ARBITRATION.FACT_CONFLICT` and passed.
3. S17 passed its catalog assertions, then the QA print attempted to sort opaque `StructureId` values. The corrected print converted IDs to strings; all original semantic assertions passed again.

These are harness mistakes, not P0/P1/P2 product findings. They are disclosed so exit-0-only accounting cannot obscure the actual execution history.

## Task13 Boundary

Task13 is cited as follows, without upgrading supplemental evidence into an exact full-suite pass:

- Gate A: 212 passed, exit 0.
- Gate B: 333 passed, exit 0.
- Gate C: 24 passed, exit 0.
- Gate E tool and rule checks: exit 0.
- Exact Gate D, `python -m pytest tests/ -q -p no:cacheprovider`: **FAIL**, exit 2 at collection because dirty `tests/test_application_candidates.py:21` has an unclosed list.
- Task13 attributes that syntax edit to pre-Wave1 unrelated work and separately establishes the unchanged pre-Wave1 G001 repeated uncached YAML parse timeout mechanism.
- The supplemental remaining suite excludes all of `tests/test_application_candidates.py` and all of `tests/regression/test_g_iteration.py`; it passed `4195`, skipped `7`, emitted `1` warning, and took `1260.9s`.
- This QA did not rerun that approximately 20-minute command and does not claim the excluded non-G001 tests were covered by it.

The accepted Wave1 completion path is therefore the authority's explicit pre-existing-and-unrelated-failure branch, not exact Gate D success.

## Failures, Blockers, And Residuals

Product failures: none (`P0=0`, `P1=0`, `P2=0`).  
Blockers: none.  
429 / missing execution: none.  
Final verdict: **PASS**.

Residual disclosures:

- Exact Task13 Gate D remains failed as described above.
- The focused compatibility suite emits the known `dual_engine_adapter` deprecation warning.
- The repository remains heavily dirty; this lane does not attribute, reset, revert, stash, or reformat concurrent work.
- S23 covers the injected shadow execution's direct `Path` write APIs and registry object. Architecture/import suites add static and fresh-import coverage, but this is not a machine-wide I/O tracer.

## Cleanup And Preservation

- No product, test, YAML, report, feedback, learning, release, or production file was edited by this lane.
- The only intentional repository write is this evidence report.
- No subagent, server, port, container, debugger, reset, revert, checkout, stash, deletion, or process termination was used.
- All QA Python commands used `-B`; both pytest commands also disabled the cache provider.
- No 429, timeout, or abandoned owned command occurred. The 157.32-second compatibility pytest process was polled to exit 0 before closeout.
- Existing ignored `__pycache__` directories were present before this lane. They were not deleted because ownership is shared and the lane is read-only; no cleanup claim is made for unowned caches.
- Unrelated dirty work was preserved.

## Stop Gate

Wave1 final hands-on QA may stop with PASS. This evidence does not authorize or begin Wave2 or Wave3.
