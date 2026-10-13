# Task9 Trigger Boundary Definitive Code Review

Date: 2026-08-04
Workdir: `F:\多流派新思路`
Mode: independent read-only rereview; no product code edits, no commit, no revert.

## Scope Reviewed

Task9-owned paths only:

- `engine/governance/trigger_registry.py`
- `engine/governance/trigger_loader.py`
- `engine/governance/fact_certification_loader.py`
- `engine/governance/school_registry_loader.py`
- `engine/governance/composition_loader.py`
- `engine/governance/registries.py`
- `engine/governance/__init__.py`
- `tests/governance/test_trigger_registry.py`
- `theory/multi-school-governance-v1.yaml`

Legacy `engine/application/production_rule_*.py` files and `tests/test_production_rule_loader.py` were treated only as compatibility/regression inputs, not Task9 lint/no-excuse scope.

Artifacts reread: `.omo/notepads/multi-school-governance-wave1/task9-trigger-boundary.md`, `.omo/start-work/artifacts/task9-trigger-boundary.txt`, `.omo/evidence/task9-trigger-boundary-stop-hook-verification.txt`, and `.omo/start-work/artifacts/task9-*`.

## Skill-Perspective Check

Required skill-perspective check ran:

- `omo:remove-ai-slops` consulted for deletion-only tests, tautological tests, implementation-mirroring tests, unnecessary production complexity, broad exception handling, dead code, oversized files, and false-confidence gates.
- `omo:programming` consulted with Python reference for frozen/slots value objects, typed errors, closed enum parsing, no untyped escape hatches, no broad except, no `cast`/ignore, and 250 pure LOC ceiling.

Result: no Task9 production-code or test violation requiring changes. Tests assert observable fail-closed outcomes rather than deletion/removal or implementation constants. `trigger_registry.py` is 240 pure LOC, below the hard 250 ceiling but in the warning band.

## Findings

### CRITICAL

None.

### HIGH

None.

### MEDIUM

None.

### LOW

1. `engine/governance/trigger_registry.py` is close to the file-size ceiling.
   - Fresh LOC: `engine/governance/trigger_registry.py 240`.
   - This is under the 250 hard limit, so it is not a blocker. Next trigger expansion should split value types, evaluator runtime, and loader-facing construction before adding more logic.

2. `tests/governance/test_trigger_registry.py:170-188` uses `TZ` mutation as part of the no-clock/as-of-date test.
   - This is acceptable as a side-effect guard, and the scoped forbidden scan found no production `datetime.now`, `date.today`, `time.time`, `getenv`, `condition_evaluator`, or `evaluate_trigger` use.

## Verification

Fresh stable governance gate:

- Command: `python -m pytest tests/governance -q`
- Result: `159 passed, 1 warning in 32.96s`.

Fresh plan focused + legacy production regression gate:

- Command: `python -m pytest tests/governance/test_trigger_registry.py tests/test_production_rule_loader.py tests/predicates/test_ten_god_structures.py -q`
- Result: `34 passed, 1 warning in 34.60s`.

Scoped Ruff/format:

- Command: `python -m ruff format --check` on the eight Task9 Python paths.
- Result: `8 files already formatted`.
- Command: `python -m ruff check` on the eight Task9 Python paths.
- Result: `All checks passed!`.

Scoped no-excuse / forbidden scan:

- Project no-excuse script: `scripts/python/check-no-excuse-rules.py` absent, so the substitute scan was used.
- Scan over the eight Task9 Python paths for `Any`, `object` annotations, `cast`, `type: ignore`, `pyright: ignore`, broad except, `asyncio`, `condition_evaluator`, `evaluate_trigger`, system-time reads, and env reads.
- Result: no matches.

Scoped pure LOC:

- `engine/governance/trigger_registry.py 240`
- `engine/governance/trigger_loader.py 119`
- `engine/governance/fact_certification_loader.py 192`
- `engine/governance/school_registry_loader.py 186`
- `engine/governance/composition_loader.py 177`
- `engine/governance/registries.py 100`
- `engine/governance/__init__.py 142`
- `tests/governance/test_trigger_registry.py 222`

Manual public-API replay:

- Unknown trigger returns inactive with `UNKNOWN_TRIGGER`.
- Candidate/unpublished trigger returns inactive with `UNPUBLISHED_TRIGGER`.
- Missing declared fact returns inactive with `MISSING_REQUIRED_FACT`.
- Liunian with only `as_of_date="2026-08-04"` and `parsed_present=True` returns inactive with `MISSING_REQUIRED_FACT`.
- Explicit `TemporalScope(TemporalLayer.LIUNIAN, target_year=2026)` fact activates the liunian trigger.
- Repeated liunian evaluation is deterministic; snapshot digest and identity remain unchanged.
- Default YAML registry exposes only `synthetic.natal-present` and `synthetic.liunian-target`, with statuses `candidate` and `synthetic_only`; no production trigger is registered.
- Malformed YAML fixtures fail closed:
  - `unknown_top.yaml`: `CERTIFICATION.YAML_FIELDS`
  - `duplicate_triggers.yaml`: `CERTIFICATION.YAML_DUPLICATE_FIELD`
  - `natural_expression.yaml`: `CERTIFICATION.YAML_PARSE`
  - `quoted_expression.yaml`: `TRIGGER.EVALUATOR_ID`
  - `production_status.yaml`: `TRIGGER.STATUS`
- Direct integrity guards:
  - Invalid `TriggerOutcome` issue tuple rejects with `TRIGGER.ISSUES`.
  - Unsupported evaluator version rejects with `TRIGGER.EVALUATOR_VERSION`.
  - Duplicate trigger IDs reject with `TRIGGER.DUPLICATE`.

Static code inspection:

- `engine/governance/trigger_registry.py:281-289` fail-closes unknown, unpublished, and missing-fact cases before evaluator execution.
- `engine/governance/trigger_registry.py:252-266` uses a closed `TriggerEvaluatorId` match with `assert_never`.
- `engine/governance/trigger_registry.py:260-263` requires an explicit `TemporalLayer.LIUNIAN` fact with non-null `target_year`; it does not infer from context.
- `engine/governance/trigger_loader.py:78-80` and `:92-108` require exact trigger fields and reject dynamic/natural expression escapes through closed scalar parsing and enum construction.
- `engine/governance/fact_certification_loader.py:194-199`, `engine/governance/school_registry_loader.py:178-183`, and `engine/governance/composition_loader.py:191-196` only add `triggers` as an optional top-level extension while preserving unknown/duplicate top-level rejection.
- `theory/multi-school-governance-v1.yaml:37-55` contains only synthetic/candidate trigger entries.

## Recommendation

`codeQualityStatus`: WATCH

`recommendation`: APPROVE

`blockers`: none.

Residual watch item: `trigger_registry.py` is 240 pure LOC; avoid adding more trigger logic without splitting.

