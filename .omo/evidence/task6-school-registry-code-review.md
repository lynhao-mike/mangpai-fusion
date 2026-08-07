# Task 6 School Registry Code Review

Date: 2026-08-04 (Asia/Shanghai)
Workspace: `F:\多流派新思路`
Reviewer: independent read-only Task 6 reviewer
Review scope: Task 6 implementation plus the shared Task 4 certification loader/registry, canonical-ID primitive, legacy capability registry, YAML, and direct tests. Product files were not modified.

## Verdict

- `codeQualityStatus`: PASS_WITH_NOTES
- `recommendation`: APPROVE
- `blockers`: none
- `finalStatus`: APPROVED

No CRITICAL or HIGH finding was identified. The registry is an immutable, fail-closed boundary with exact five-dimensional capability identity and no observed application/report/learning dependency fanout.

## Findings

### CRITICAL

None.

### HIGH

None.

### MEDIUM

None.

### LOW

1. Test coverage does not directly lock every malformed capability-entry variant or the import-isolation rule.
   - Evidence: [test_school_registry.py](F:\多流派新思路\tests\governance\test_school_registry.py:187) tests peer data tampering, and [test_school_registry.py](F:\多流派新思路\tests\governance\test_school_registry.py:130) tests `evidence_only`, but there is no direct regression for candidate/proposed capability abstention, YAML `role: abstain` rejection, or prohibited-import fanout.
   - Current implementation is correct for the inspected paths: [school_registry.py](F:\多流派新思路\engine\governance\school_registry.py:140) rejects registrable `abstain`; [school_registry.py](F:\多流派新思路\engine\governance\school_registry.py:272) returns a typed abstention for unpublished entries; AST and cold-import probes were clean. Add narrow tests before the capability table is populated or extended.

## Contract Review

- Exact 5D identity: `school_id`, `task_id`, `claim_kind`, `evidence_grade`, and `version` are all closed/validated in [school_registry.py](F:\多流派新思路\engine\governance\school_registry.py:118). Lookup only accepts `CapabilityIdentity` and compares the complete value at [school_registry.py](F:\多流派新思路\engine\governance\school_registry.py:267).
- Canonical IDs and aliases: the peer set is exactly `ziping`, `gao_dechen`, `duan_jianye`, `yang_qingjuan`, and `ren_fuhong`; short aliases are accepted only by `normalize_school_input` ([school_registry.py](F:\多流派新思路\engine\governance\school_registry.py:47)). Registry lookup intentionally does not normalize aliases ([school_registry.py](F:\多流派新思路\engine\governance\school_registry.py:251)). `ditiansui` is legacy-only.
- Abstention and eligibility: missing identities produce `CAPABILITY.UNREGISTERED` abstention ([school_registry.py](F:\多流派新思路\engine\governance\school_registry.py:285)); unpublished entries abstain; only `lead` and `co_lead` are winner eligible ([school_registry.py](F:\多流派新思路\engine\governance\school_registry.py:161)).
- Read-only behavior: frozen, slotted data classes and tuples expose no registration mutation API. Capability output uses typed qualification or typed abstention.
- YAML/schema/path: loader enforces exact top-level and capability fields, duplicate-key rejection, scalar type discipline, exact peer/legacy sequences, and closed enum values ([school_registry_loader.py](F:\多流派新思路\engine\governance\school_registry_loader.py:75), [school_registry_loader.py](F:\多流派新思路\engine\governance\school_registry_loader.py:182)). It reuses Task 4's contained-path/symlink guard and validates the shared certification/digest contract before parsing Task 6 data ([school_registry_loader.py](F:\多流派新思路\engine\governance\school_registry_loader.py:185)).
- Task 4 compatibility: the Task 4 and Task 6 governance suites passed together (43 tests). The legacy `engine/decision/capability_registry.py` had no scoped modification; Task 6 does not alter its snapshot schema or fallback behavior.
- Static isolation: direct AST imports are limited to governance contracts, `pathlib`, typing/dataclasses, and YAML; the fresh-process probe found no `engine.application`, `engine.decision`, `engine.claims`, `engine.f09.application`, `engine.evaluation`, tool, or report dependency.
- Type/complexity/LOC: no `Any`, `object`, casts, ignored types, broad catches, or mutable registry containers observed. `school_registry.py` is 291 physical lines, `school_registry_loader.py` 230, `registries.py` 57, and its test 218; the primary module remains below the 250 pure-LOC threshold after blank lines are excluded. The split between values and YAML boundary is coherent.

## Executed Evidence

All commands ran from `F:\多流派新思路`.

| Start/end (local) | Command | Exit | Result |
| --- | --- | ---: | --- |
| 00:55:46.77-00:55:51.66 | `python -m pytest tests/governance/test_school_registry.py tests/test_l1_learned_prior.py tests/decision/test_staged_arbitration.py -q` | 0 | 50 passed; 1 pre-existing deprecation warning from `engine.application.pipeline_runner` |
| 00:55:16.57 (reported duration 3.03s) | `python -m pytest tests/governance/test_school_registry.py tests/governance/test_fact_certification_registry.py tests/governance/test_canonical.py -q` | 0 | 43 passed |
| 00:56:31.69-00:56:32.37 | `ruff check` and `ruff format --check` on Task 6 source/facade/test | 0 / 0 | all checks passed; 4 files already formatted |
| 00:56:31.64-00:56:32.14 | fresh-process import probe of `engine.governance.registries` | 0 | prohibited application/decision/claims/F09/evaluation module tuple was `()` |
| 00:56:31.69-00:56:32.15 | default registry load probe | 0 | exact five peer IDs loaded; capability lookup surface present |
| 00:57:52.55-00:57:53.31 | AST import probe | 0 | only governance, standard-library, and YAML imports; prohibited tuple `()` |

`basedpyright`: not run; it is not available in the local project toolchain. This is a residual tooling gap, not a release blocker because Ruff and all focused behavioral tests are green.

## Residual Risks

- The production YAML deliberately has `capabilities: []`; Task 6 therefore proves abstention by default but has no real published capability fixture. Populate it only with the additional LOW-priority tests above.
- No full-suite run was performed for this code review; focused Task 4/6 and required Task 6 acceptance suites passed.

