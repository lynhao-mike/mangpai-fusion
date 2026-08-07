Task9 trigger boundary DoneClaim
Date: 2026-08-04T13:48:59+08:00
Workdir: F:\多流派新思路
Python: 3.14.5
Pytest: 8.4.2

Scope owned
- Added tests/governance/test_trigger_registry.py.
- Added engine/governance/trigger_registry.py and engine/governance/trigger_loader.py.
- Extended engine/governance/fact_certification_loader.py, school_registry_loader.py, composition_loader.py for the one optional top-level triggers field.
- Extended engine/governance/registries.py and engine/governance/__init__.py with minimal audit/public trigger exports.
- Extended theory/multi-school-governance-v1.yaml with top-level triggers only; registered entries are synthetic/candidate, not production.
- Did not touch Task10 implementation files.

Baseline before source changes
- Scenario: existing production rule loader + ten-god structures.
- Command: python -m pytest tests/test_production_rule_loader.py tests/predicates/test_ten_god_structures.py -q
- Exit: 0
- Observable: 20 passed, 1 warning.
- Artifact: .omo/start-work/artifacts/task9-baseline-production-ten-god.log

RED
- Scenario: new governance trigger surface missing.
- Command: python -m pytest tests/governance/test_trigger_registry.py -q
- Exit: 2
- Observable: ModuleNotFoundError: No module named 'engine.governance.trigger_registry'.
- Artifact: .omo/start-work/artifacts/task9-red-trigger-registry.log

GREEN focused
- Scenario: Task9 trigger registry focused tests.
- Command: python -m pytest tests/governance/test_trigger_registry.py -q
- Exit: 0
- Observable: 13 passed twice before evaluator-version hardening; final 14 passed after version hardening.
- Artifacts: task9-green-focused-1.log, task9-green-focused-2.log, task9-final-focused.log, task9-final2-focused.log

Plan command
- Scenario: required Task9 + production loader + ten-god regression.
- Command: python -m pytest tests/governance/test_trigger_registry.py tests/test_production_rule_loader.py tests/predicates/test_ten_god_structures.py -q
- Exit: 0
- Observable: final 34 passed, 1 warning.
- Artifact: .omo/start-work/artifacts/task9-final2-plan-command.log

Task1-9 joint
- Scenario: governance Task1-9 joint plus governance application adapters.
- Command: python -m pytest tests/governance tests/application/test_governance_fact_builder.py tests/application/test_governance_claim_adapters.py tests/application/test_governance_claim_adapter_boundaries.py tests/application/test_governance_claim_adapter_derivation.py -q
- Initial observable: 188 passed, 1 failed due optional top-level loader compatibility accepting only all-or-none optional fields.
- Fix: changed fact/school/composition loader optional field validation to required <= actual <= required|optional.
- Final exit: 0
- Final observable: 190 passed, 1 warning.
- Artifact: .omo/start-work/artifacts/task9-final2-task1-9-joint.log

Static / quality
- Ruff format check: python -m ruff format --check <changed python files>; exit 0; observable 8 files already formatted; artifact task9-final2-ruff-format-check.log.
- Ruff check: python -m ruff check <changed python files>; exit 0; observable All checks passed; artifact task9-final2-ruff-check.log.
- no-excuse entrypoint: scripts/python/check-no-excuse-rules.py absent; artifact task9-no-excuse-entrypoint.log records False.
- no-excuse strict scan substitute: rg for Any/object annotation/cast/type-ignore/broad except/asyncio/system date/evaluate_trigger over changed Python files; exit 0 with no matches; artifact task9-final2-no-excuse-strict-scan.log.
- LOC final: trigger_registry.py 240, trigger_loader.py 119, fact_certification_loader.py 192, school_registry_loader.py 186, composition_loader.py 177, registries.py 100, __init__.py 142, test_trigger_registry.py 222; artifact task9-final2-loc.log.
- YAML dynamic/prod scan: rg callback|lambda|expression|module|production|natural|condition over theory/multi-school-governance-v1.yaml; exit 0 no matches; artifact task9-yaml-scan.log.

Manual public API QA matrix
- Invocation: Python public API script via stdin.
- Artifact: .omo/start-work/artifacts/task9-manual-qa-rerun.log plus task9-manual-qa-quoted-expression.log.
- Unknown trigger: inactive, issue unknown_trigger.
- Unsupported evaluator version: TriggerRegistryContractError TRIGGER.EVALUATOR_VERSION.
- Candidate/unpublished trigger: inactive, issue unpublished_trigger.
- Missing required fact: inactive, issue missing_required_fact.
- Liunian without explicit target-year FactSnapshot fact: inactive even with as_of_date=2026-08-04 and parsed_present=True.
- Explicit target-year liunian fact: active.
- Same snapshot determinism and side-effect probe: repeated outcomes equal; snapshot digest unchanged.
- YAML valid zero-trigger fixture: loads count 0.
- YAML unknown top field: fail closed via SchoolRegistryContractError CERTIFICATION.YAML_FIELDS.
- YAML duplicate top triggers: fail closed via SchoolRegistryContractError CERTIFICATION.YAML_DUPLICATE_FIELD.
- YAML unquoted expression: fail closed at YAML parse.
- YAML quoted expression evaluator ID: fail closed via TriggerRegistryContractError TRIGGER.EVALUATOR_ID.
- YAML production status: fail closed via TriggerRegistryContractError TRIGGER.STATUS.

9 ultraqa classes covered
1. Unknown trigger fail closed.
2. Candidate/synthetic/unpublished trigger non-execution.
3. Missing required fact fail closed.
4. Liunian requires explicit target-year TemporalScope fact.
5. as_of_date/system/parsed object cannot substitute target year.
6. Closed evaluator ID and evaluator version; natural language/expression rejected.
7. Evaluator only reads declared fact kinds.
8. Deterministic repeated evaluation with no snapshot/environment side effects.
9. YAML schema escapes: unknown/duplicate top fields, dynamic expression/callback/module/prod status rejected or absent.

Changed files / status notes
- Scoped status artifact: .omo/start-work/artifacts/task9-scoped-status.log.
- The repository already had a very large dirty/untracked worktree before this task. The scoped Task9 files appear as untracked because engine/governance and theory governance files were already not tracked in this checkout; no commit was made and no unrelated work was reverted.

Risks / residuals
- Full repository pytest was not run because Task9 requested focused twice, plan command, and Task1-9 joint; broader dirty worktree contains many unrelated untracked files.
- trigger_registry.py is 240 pure LOC, below the 250 hard ceiling but in the warning band; next trigger edit should split value types/evaluator runtime if more logic is added.
- Existing warning remains: engine.application.pipeline_runner deprecation warning; unrelated to Task9.
