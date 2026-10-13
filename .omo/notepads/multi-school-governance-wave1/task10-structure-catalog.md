# Task 10 Structure Catalog Notepad

## Scope

Implemented Wave 1 Task 10 only:

- `tests/governance/test_structure_catalog.py`
- `engine/governance/structure_catalog.py`
- `engine/governance/structure_catalog_types.py`
- `theory/ziping/structure-catalog-v1.yaml`

No changes to `engine/governance/__init__.py`, `theory/multi-school-governance-v1.yaml`, `engine/governance/registries.py`, `TenGodStructureKind`, production loaders, report/feedback/learning paths, or public fact registration.

## Source Audit

The frozen 30-item list follows `.omo/plans/ten-god-structure-production-closure.md:55-86`:

- flow/protection: 13
- control/transformation: 5
- clearing: 3
- damage/imbalance: 9

The same source explicitly preserves only three legacy structures as compatibility mappings and says `TenGodStructureKind` is not the complete catalog source. It also excludes single-pattern 格, 从格, 专旺格, 化气格, 调候 and 神煞 from this 30-item relation catalog.

Ziping corpus cross-checks used `theory/_ir/ziping_rule_ir.yaml` around lines 1288, 1309, 1372, 1376, 1442, 1527, 1549, 3539, 3560, 3601, 3623, 3771 and 3950. DTS-only or normalized entries were frozen as `source_status=review` where the Ziping-only source trail is not direct.

## Verification

Baseline:

- `python -m pytest tests/predicates/test_ten_god_structures.py -q`
- Result: exit 0, 13 passed.
- Enum check result: `FOOD_GOD_CONTROLS_KILLING`, `HURTING_OFFICER_CONTROLS_KILLING`, `KILLING_GENERATES_SEAL`.

RED:

- `python -m pytest tests/governance/test_structure_catalog.py -q`
- Result: exit 1, 10 failed with missing `engine.governance.structure_catalog`.

GREEN:

- `python -m pytest tests/governance/test_structure_catalog.py -q`
- Result: exit 0, 10 passed.

Focused twice:

- `python -m pytest tests/governance/test_structure_catalog.py tests/predicates/test_ten_god_structures.py -q`
- Results: exit 0, 23 passed; exit 0, 23 passed.

Post-split/static:

- `python -m pytest tests/governance/test_structure_catalog.py tests/predicates/test_ten_god_structures.py -q`: exit 0, 23 passed.
- `python -m ruff check ...`: exit 0.
- `python -m ruff format --check ...`: exit 0.
- `check-no-excuse-rules.py ...`: exit 0.
- LOC: loader 225, types 95, test 157 pure LOC.
- `git diff --check -- ...`: exit 0.

Manual loader QA:

- count 30, unique IDs 30, unique keys 30.
- catalog digest `1b746ca407ca17b653646fdaeb0f289acaeaa440bce780a81cc52ff70a3da8bc`.
- source status counts: composite 1, direct 16, normalized 10, review 3.
- implementation status counts: catalog-only candidate 25, catalog-only review 2, current implemented 3.
- current implemented IDs: `food_god_controls_killing`, `hurting_officer_controls_killing`, `killing_generates_seal`.
- order change keeps digest; display-name change keeps stable ID and changes digest.
- duplicate ID/key, unknown legacy mapping, missing source status, unknown source status all fail closed.
- loading does not import `engine.application.production_rule_loader`.

## Known External Failure

`python -m pytest tests/governance -q` returned exit 1 with 153 passed and 1 failed. The failing test is `tests/governance/test_school_registry.py::test_evidence_only_capability_is_never_winner_eligible`, in existing school registry/fact certification code. No Task10-owned file is in that stack, so it is recorded as out of scope rather than repaired here.

## Artifact

Detailed evidence: `.omo/start-work/artifacts/task10-structure-catalog.txt`.

## REQUEST_CHANGES Rework

Fixed the two review blockers without expanding Task10 scope:

- Exact legacy mapping is fail-closed at the YAML boundary and constructor boundary: only the three known enum mappings are projected, catalog-only entries keep `legacy_mapping: null`, swapped known mappings reject with `STRUCTURE.LEGACY_TARGET`, and duplicate legacy enum values reject with `STRUCTURE.LEGACY_DUPLICATE` before dict projection collapse.
- `StructureCatalogEntry` and `StructureCatalog` direct constructors now exact-type validate branded IDs/keys, enums, nonempty tuples, immutable projection, nested entries, and digests; forged or mutable/raw inputs raise `StructureCatalogContractError` issue codes instead of leaking `AttributeError`.

Verification after rework:

- `python -m pytest tests/governance/test_structure_catalog.py tests/predicates/test_ten_god_structures.py -q`: exit 0, 27 passed. Repeated result: exit 0, 27 passed. Final post-format result: exit 0, 27 passed.
- `python -m pytest tests/governance -q`: exit 0, 159 passed, 1 warning. Final post-format result: exit 0, 159 passed, 1 warning.
- `python -m ruff check ...`: exit 0, all checks passed.
- `python -m ruff format --check ...`: exit 0, 3 files already formatted.
- `python -m compileall ...`: exit 0.
- `check-no-excuse-rules.py ...`: exit 0, no violations in 3 files.
- LOC audit: loader 290, types 331, tests 290; each has an explicit first-10-lines `SIZE_OK` exception because these are cohesive Task10 catalog/enum/contract-test surfaces and splitting would broaden the wave task.

Manual replay observables:

- count 30, unique IDs 30, unique keys 30.
- exact projection: `FOOD_GOD_CONTROLS_KILLING -> food_god_controls_killing`, `HURTING_OFFICER_CONTROLS_KILLING -> hurting_officer_controls_killing`, `KILLING_GENERATES_SEAL -> killing_generates_seal`.
- swapped legacy mapping rejected with `STRUCTURE.LEGACY_TARGET`.
- duplicate legacy mapping rejected with `STRUCTURE.LEGACY_DUPLICATE`.
- forged entry digest rejected with `STRUCTURE.ENTRY_DIGEST`.
- raw family string and mutable roles rejected with `STRUCTURE.ENTRY_TYPE`.
- forged catalog digest rejected with `STRUCTURE.CATALOG_DIGEST`.
- mutable projection rejected with `STRUCTURE.CATALOG_TYPE`.
- wrong known legacy projection rejected with `STRUCTURE.LEGACY_TARGET`.
- wrong nested entry rejected with `STRUCTURE.CATALOG_TYPE`.
- loading the catalog did not import `engine.application.production_rule_loader`.

## Safe Refactor: Remove SIZE_OK

Parent rejected the hard-plan violation even though the reviewer accepted `SIZE_OK`. I removed every `SIZE_OK` escape and split by responsibility with no public behavior/API change.

Codemap and split:

- `structure_catalog.py`: public YAML loader facade, path/YAML compose orchestration, duplicate ID/key/legacy pre-scan, catalog projection construction, and compatibility re-exports.
- `structure_catalog_loader_values.py`: YAML node/scalar/list/closed-enum parsing.
- `structure_catalog_types.py`: branded IDs, enums, typed error, and lazy model/digest re-exports.
- `structure_catalog_models.py`: `StructureCatalogEntry`, `StructureCatalog`, digest derivation, tuple/projection/nested-entry validation, exact legacy target checks.
- `test_structure_catalog.py`: catalog/loader/digest/YAML matrix/side-effect tests.
- `test_structure_catalog_integrity.py`: constructor forgery and integrity tests.

Per-step checks:

- Model extraction targeted: `27 passed`; LOC after step: types 147, models 238.
- Loader parsing extraction first run: `2 failed, 25 passed` due two stale `_reject` calls; fixed immediately.
- Loader parsing extraction rerun: `27 passed`; LOC after step: loader facade 248, loader values 118.
- Test split targeted: `27 passed`; LOC after step: loader tests 177, integrity tests 117.
- Facade re-export compatibility fix targeted: `27 passed`.

Final checks:

- Focused twice: `27 passed`; `27 passed`.
- Governance: `159 passed, 1 warning`.
- Ruff check: pass.
- Ruff format check: `6 files already formatted`.
- No-excuse: `no violations in 6 file(s)`.
- Compileall: exit 0.
- `rg "SIZE_OK" ...`: exit 1 with no output, so no `SIZE_OK` escapes remain.
- Final LOC: `structure_catalog.py 248`, `structure_catalog_loader_values.py 118`, `structure_catalog_types.py 149`, `structure_catalog_models.py 238`, `test_structure_catalog.py 177`, `test_structure_catalog_integrity.py 117`.
- Public replay: count/projection/error-code/manual import side-effect matrix passed, including `type_reexport_entry_digest_matches=True` and `direct_model_import_matches=True`.
