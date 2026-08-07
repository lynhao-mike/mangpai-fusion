# W2-C3 Prospective staging integration — RECOVER / INVENTORY / ADMISSION

## Controller state

- Unit: `W2-C3`
- Authorized stages: `RECOVER`, `INVENTORY`, `ADMISSION`, and `CONTRACT` only
- Current stage: `CONTRACT COMPLETE / IMPLEMENT NOT AUTHORIZED`
- Verdict: `PASS`
- Boulder activation: forbidden at this stage; `.omo/boulder.json` keeps `active_work_id: null`
- Predecessor boundary: W2-C2 is evidence-bounded frozen and handed off; no contract, file whitelist, test authority, Gate PASS, publication authority, or production authority is inherited
- Remote boundary: local-only read and admission persistence; every GitHub service-side mutation remains permanently forbidden
- Local protection boundary: preserve all tracked and untracked changes; no reset, clean, checkout, restore, stash, rebase, commit, or equivalent destructive/history-changing Git operation

## User authorization

The user explicitly approved `W2-C3 RECOVER/ADMISSION` and later approved the sole pending W2-C3 CONTRACT action. Under the standing local controller envelope this authorizes the minimum local reads, CONTRACT drafting/revision, logically fresh CONTRACT review, TODO update, and this local persistence record. It does not authorize IMPLEMENT, test execution, Boulder activation, publication, routing, production switching, deployment, Git, or GitHub mutation.

## RECOVER

### Authoritative state

- `.omo/boulder.json` has `active_work_id: null`.
- W2-C1 and W2-C2 are recorded as completed predecessor units.
- `META/project-state.json` reports prospective engineering as landed but real cohort not ready, production ready false, and production switch not permitted.
- W2-C2 froze `adapt_governance_shadow_to_blind_outputs(result, task, projections)` as a pure semantic adapter. Projection creation, review, custody, publication, staging, freeze, label reveal, scoring, and high-risk review remained outside W2-C2.
- Wave 2 planning identifies prospective staging immediately before `freeze_outputs()` as the next candidate seam.

### Unique recovered objective

Evaluate whether one independently reviewable W2-C3 unit can integrate already reviewed governance-shadow projections into the existing single-case prospective staging path before final freeze, while preserving the complete six-school/task grid and all pre-release outcome-isolation guarantees.

## INVENTORY

### Existing staging chain

1. `prepare_single_case_blind_bundle()` creates a whitelist-only bundle containing intake, tasks, rule snapshot, future question, and canonical chart.
2. `build_single_case_staged_frozen_run()` re-verifies the bundle.
3. It calls legacy `tools.school_capability_prospective.build_staged_frozen_run()`.
4. The legacy builder generates each school/task row through `generate_blind_outputs()` and returns an already frozen `FrozenBlindRun`.
5. The single-case function extracts those outputs, applies timing fact-ref safety, enforces the exact six-school/task grid, then calls `freeze_outputs()` again at the registered freeze time.

The current path therefore has a legacy generation/freeze followed by single-case safety/final-freeze structure. W2-C2's governance-shadow adapter has no production caller.

### Candidate seams

1. **Replace the complete legacy generator:** rejected for admission. W2-C2 covers only one exact task lane and cannot generate the complete six-school/task grid.
2. **Replace only one matching grid slot after legacy generation:** technically plausible, but identity normalization and projection custody are not yet contracted.
3. **Accept a complete externally constructed output grid:** rejected for current admission because it bypasses the intended governance-shadow semantic boundary and broadens custody/API scope.
4. **Run governance shadow and create projections inside staging:** rejected for current admission because it combines governance execution, dependency loading, typed claim creation, projection attestation/custody, grid merge, and freeze into one unit.
5. **Consume already reviewed `GovernanceShadowResult` plus projections at a narrow pre-freeze merge seam:** preferred direction, subject to closing the two compatibility defects below and freezing a custody/input boundary.

### Outcome isolation

The single-case bundle rejects feedback, label, report, known-fact, observation, reveal, and related forbidden markers. Existing planning requires the adapter and school execution to remain before release. W2-C3 must not add any feedback reader, label path, observation path, report path, learned metric, high-risk review payload, or scoring input.

### Existing complete-grid contract

`_assert_complete_single_case_grid()` requires exactly one row for every `(case_id, school, task_id)` across the canonical six schools and assigned tasks, rejects duplicates, rejects missing or extra rows, and permits only `claim`, `abstain`, or `unsupported` states.

## ADMISSION REVIEW

### Proposed minimum target

Add one pre-final-freeze merge boundary that:

1. starts from the existing complete legacy six-school/task output grid;
2. consumes one already reviewed W2-C2 `GovernanceShadowResult` plus explicit projections for the admitted divorce/remarriage task;
3. calls the frozen W2-C2 adapter with an exact bundled `BlindTask`;
4. replaces only explicitly matched school/task slots;
5. rejects missing, extra, duplicate, ambiguous, or non-canonical replacement identities;
6. re-runs existing timing safety and complete-grid validation;
7. calls the existing final `freeze_outputs()` exactly once for the authoritative single-case frozen artifact.

This target deliberately does not run governance shadow, construct typed claims, certify capabilities, create/review projections, reveal labels, score, perform high-risk review, publish capability, alter routing, or switch production.

### Confirmed admission defects

#### A1 — Task metadata loss

- The authoritative task catalog includes exact `evaluation_note: 只评价是否发生，不把关系压力自动等同离婚`.
- `_TASK_BUNDLE_FIELDS` omits `evaluation_note` when preparing the blind bundle.
- The bundled task loader reconstructs missing notes as an empty string.
- W2-C2's exact task predicate requires the complete non-empty note.
- `tests/evaluation/test_dataset.py` explicitly asserts that `evaluation_note` is absent from bundled tasks.

Therefore the current bundled task cannot legally enter the W2-C2 adapter. Admission cannot silently relax W2-C2's predicate or synthesize the note from code constants.

#### A2 — School identity mismatch

- The prospective complete grid uses aliases including `yang`.
- W2-C1 typed governance claims and W2-C2 focused tests use canonical `yang_qingjuan`.
- `normalize_school_input("yang")` exists and returns `yang_qingjuan`, but current staging does not define whether normalization occurs before adapter projection matching, during merge, or in final output identity.
- Replacing a `yang` grid slot with a `yang_qingjuan` output without an explicit identity contract creates one missing and one extra grid identity.

Therefore admission cannot use an implicit alias conversion. It must freeze one reversible, testable identity rule without weakening source ownership.

#### A3 — Projection custody/input boundary not yet frozen

`GovernanceShadowResult` does not authenticate projection case/version/execution/capability assertions. W2-C3 must state where already reviewed in-memory projections enter the staging API, how they bind to verified bundle parents, and why neither disk outcome material nor unreviewed serialized projections can enter. This is a contract requirement, not permission to create a projection publication format.

### R1 verdict

`REVISE`

The candidate was technically plausible and did not require abandoning existing freeze or prospective primitives, but R1 could not pass until A1, A2, and A3 were resolved in the admission boundary. R2 below preserves this failure history and addresses only those cited defects.

## Required admission revision

A revised ADMISSION must freeze all of the following before CONTRACT:

1. **Task metadata rule:** preserve `evaluation_note` in the blind bundle and update the existing test that currently requires its deletion, or introduce a separately parent-bound exact task source without synthesizing semantic text. Relaxing the W2-C2 predicate is forbidden.
2. **School identity rule:** use the existing governance canonicalization only at an explicit input boundary, while defining whether final `BlindSchoolOutput.school_id` remains the prospective alias or the entire prospective grid migrates to canonical IDs. No mixed identity set is allowed.
3. **Projection custody rule:** accept only exact in-memory typed W2-C2 objects supplied by a separately reviewed caller and bind them to the verified bundle/result identities; do not add projection JSON loading, outcome paths, publication, or registry mutation.
4. **Merge invariant:** one admitted projection may replace exactly one existing grid identity; all other rows remain byte-semantically generated by the existing path; duplicate/reuse/missing/extra replacements fail closed.
5. **Freeze invariant:** the authoritative single-case artifact is produced by the existing final `freeze_outputs()` after timing safety and complete-grid validation. The legacy inner freeze is not evidence for W2-C3 correctness.

## ADMISSION R2 — minimum reversible boundary

R2 resolves A1, A2, and A3 without expanding W2-C3 into governance execution, projection publication, or a complete-grid rewrite.

### R2-A1 — Parent-bound task metadata is preserved

1. The blind bundle must retain the authoritative task catalog's exact `evaluation_note` alongside the existing task fields.
2. The staging path must construct the `BlindTask` only from the verified bundled task document; it must not recover, synthesize, default, or override semantic text from a code constant.
3. W2-C2's exact task predicate remains unchanged.
4. A later CONTRACT must explicitly include the bundle-field owner and the existing dataset contract test that currently requires note removal. This is a bounded contract revision, not permission to expose labels, feedback, observations, reports, or other outcome material.
5. The task note is admitted only because it is immutable catalog semantics and is parent-bound by the existing bundle manifest/digest chain. It is not evidence of an outcome and must still pass the existing forbidden-marker/value checks.

### R2-A2 — Canonical ownership check, prospective alias output

1. Governance-shadow projections and W2-C2 adapter outputs retain canonical governance school identity. For the admitted lane this identity is exactly `yang_qingjuan`.
2. The pre-freeze merge boundary performs an explicit one-to-one ownership comparison: the existing prospective slot alias `yang` must normalize through `normalize_school_input()` to the adapter output's canonical `yang_qingjuan` identity.
3. After that equality is proven, the replacement row is rebuilt with the original slot's exact prospective identity `school_id="yang"`; no canonical ID is inserted into the final prospective grid.
4. The final grid therefore keeps the existing `SIX_SCHOOLS` alias contract unchanged. Canonical and alias IDs may not coexist as separate rows, and no alias may match more than one canonical owner.
5. R2 admits only the already evidenced Yang divorce/remarriage lane. It does not authorize a generic canonical migration or mappings for unevidenced schools/tasks.

This rule preserves source ownership because canonical identity is checked before alias reconstruction; it does not infer that aliases are interchangeable outside this exact merge boundary.

### R2-A3 — Exact in-memory typed custody boundary

1. The staging integration may receive only exact in-memory W2-C2 typed values: one `GovernanceShadowResult` and an immutable sequence of `GovernanceShadowTaskProjection` values, together with the exact verified bundled `BlindTask` selected by `task_id`.
2. No mapping/dict coercion, JSON deserialization, projection file path, directory scan, registry lookup, environment lookup, feedback source, label source, observation source, report source, scoring source, or high-risk-review source is admitted.
3. The caller that creates or reviews those typed values remains outside W2-C3. Staging neither runs governance shadow nor creates, certifies, signs, publishes, or reloads projections.
4. Before replacement, the merge must fail closed unless all result-, projection-, task-, and output-visible identities agree with the verified bundle case and exact admitted task. W2-C2 adapter validation remains mandatory and may not be bypassed.
5. Result-visible identity is not treated as proof of facts that `GovernanceShadowResult` does not authenticate. W2-C3 proves only that the supplied reviewed typed objects are consistently bound at this merge boundary; it does not prove how the caller produced or reviewed them.
6. Because this is an in-memory-only seam, CLI and serialized staged-artifact schemas remain unchanged in W2-C3.

### R2 merge and authoritative-freeze invariant

1. Build the existing complete legacy six-school/task output grid first.
2. For each admitted projection output, derive exactly one target key `(verified_case_id, "yang", "marriage.divorce_or_remarriage")` only after the canonical ownership check succeeds.
3. Reject zero matches, multiple matches, duplicate projections, duplicate target keys, target reuse, task mismatch, case mismatch, unsupported school mapping, or any replacement that changes grid cardinality.
4. Replace only the exact matched row. Every non-target row remains the output supplied by the existing path; W2-C3 does not reinterpret or regenerate it.
5. Apply existing timing safety to the merged rows, then run the existing exact complete-grid validator.
6. Only after both checks pass may the existing final `freeze_outputs()` create the authoritative single-case artifact. The legacy inner freeze remains an implementation parent and supplies no W2-C3 correctness claim.
7. Any failure before final freeze produces no authoritative W2-C3 frozen artifact.

### R2 compatibility and dependency decision

- Existing final prospective school IDs, grid cardinality, timing safety, freeze primitive, serialized frozen-run schema, CLI schema, and outcome-isolation boundary remain unchanged.
- The only admitted compatibility revision is retaining authoritative `evaluation_note` in the parent-bound task bundle and revising its owning contract test.
- The narrow dependency additions admitted for a later CONTRACT are the frozen W2-C2 adapter/types and `normalize_school_input()` at the single-case pre-freeze merge seam.
- No new production route, capability registration, publication state, configuration switch, dependency loader, or persistent projection artifact is admitted.

## Candidate file impact for a later CONTRACT

No file whitelist is authorized yet. The smallest currently evidenced candidates are:

- `engine/evaluation/prospective_single_case.py` — narrow merge/input boundary and final-grid checks;
- `tests/evaluation/test_prospective_frozen_run.py` — staging integration, complete-grid, tamper, outcome-isolation, and deterministic frozen-byte tests;
- the task-bundle producer/contract test owning `_TASK_BUNDLE_FIELDS` and the explicit note-removal assertion, only if the revised ADMISSION chooses metadata preservation.

Changing `engine/evaluation/governance_shadow_adapter.py`, governance shadow types/runner, generic freeze/scoring primitives, capability registry, YAML routing, production configuration, or label/custody/review modules is not admitted.

## Scope OUT

- Running governance shadow or loading governance dependencies inside prospective staging.
- Building or publishing projection attestations.
- Projection JSON/file schema or loader.
- Full governance conversion for every school/task.
- Label reveal, scoring, capability posterior, high-risk review, custody release, cohort gates, proposal publication, production switch, routing, deployment, or report generation.
- Claiming prediction accuracy, calibration, custody truth, publication readiness, production readiness, Wave 2 completion, or repository-wide correctness.

## STOP conditions

Stop with the applicable Gate verdict if:

- task semantics would need to be synthesized from a constant after the parent-bound catalog stripped them;
- canonical and alias school IDs coexist in one output grid;
- source-school ownership is weakened by alias conversion;
- projections can be read from an unreviewed file or outcome-bearing path;
- result-visible identities are treated as proof of projection custody assertions;
- complete-grid validation is bypassed or a single-task output replaces the full grid;
- label, feedback, report, observation, scoring, high-risk review, publication, routing, production, Git, or GitHub effects enter scope;
- existing tracked or untracked work would need destructive cleanup or overwrite.

## R2 logically fresh ADMISSION review

### Common Gate record

- Gate: `ADMISSION`
- Owner role: admission author
- Fresh reviewer role: logically fresh ADMISSION reviewer; prior author conclusion was not inherited
- Authorization envelope: read authoritative W2-C2/staging/identity contracts and persist this admission verdict only
- Activation condition: user-approved W2-C3 RECOVER/ADMISSION and completed R2 author revision
- Remaining inactive grants: none for CONTRACT, IMPLEMENT, tests, Boulder activation, publication, production, Git, or GitHub
- Required inputs: R1 defect ledger, R2 boundary, W2-C2 frozen adapter contract, current single-case grid/final-freeze path, current school alias normalization
- Observed facts: the current grid ends in prospective aliases; `yang` normalizes exactly to `yang_qingjuan`; W2-C2 preserves canonical source-school identity and exact task semantics; current final freeze occurs after timing safety and exact complete-grid validation
- Inferences: retaining parent-bound `evaluation_note`, canonical-checking then reconstructing the original alias slot, and accepting only exact in-memory typed objects are compatible with one narrow pre-final-freeze merge unit
- Unknowns deferred to CONTRACT: exact callable signature, exact file whitelist, exact implementation arrangement, exact test selectors/counts, and whether implementation satisfies the admitted invariants
- Required output: one bounded admission verdict and unique next legal action

### Falsifier review

- Outcome-bearing input or serialized projection loader admitted: no.
- Governance execution/projection creation/certification moved into staging: no.
- W2-C2 task predicate relaxed or semantic note synthesized: no.
- Canonical and alias IDs coexist in the final grid: no; canonical identity is comparison-only and the replacement retains the original exact alias slot.
- Source ownership weakened: no; canonical equality is required before alias reconstruction.
- Full grid replaced or cardinality changed: no; exactly one admitted target slot is replaced and all failure modes close before final freeze.
- Timing safety, exact grid validation, or final authoritative freeze bypassed: no.
- Publication, routing, production, deployment, Git, or GitHub effect admitted: no.
- Protected tracked/untracked changes require cleanup: no admission requirement does so.

### Fresh verdict

`PASS`

R2 establishes one independently reviewable candidate with known prerequisites, a bounded compatibility revision, explicit dependencies, a minimum impact surface, fail-closed merge/freeze invariants, and complete non-goals. No active blocker or admission STOP condition remains.

### Direct evidence boundary

This PASS proves only that a narrow W2-C3 CONTRACT can be drafted around the admitted in-memory Yang divorce/remarriage slot replacement while preserving the existing prospective alias grid and final-freeze envelope. It does not prove implementation feasibility beyond the inspected interfaces, runtime behavior, deterministic bytes, custody provenance, prediction accuracy, publication readiness, or production readiness.

### Forbidden inference boundary

`ADMISSION PASS` is not CONTRACT PASS, implementation authority, test authority, Boulder activation, freeze evidence, Wave 2 completion, publication authority, routing authority, or production-switch authority. The reviewed in-memory objects are accepted as boundary inputs; this review does not certify how an external caller created or reviewed them.

## CONTRACT R1 — prospective shadow slot merge

### Controller and authorization state

- Gate: `CONTRACT`
- Unit: `W2-C3`
- Authorization source: the user's `批准`, resolved against the sole pending action as approval for W2-C3 CONTRACT drafting and fresh CONTRACT review only
- Current contract verdict: `PASS` after the user-authorized final logically fresh review
- Boulder activation: not authorized
- IMPLEMENT, test execution, STATIC_REVIEW, VERIFY, EVIDENCE_REVIEW, FREEZE, and HANDOFF: not authorized
- Git/GitHub: no local Git operation is authorized; every GitHub service-side mutation remains permanently forbidden
- Protection: preserve every pre-existing tracked and untracked change; no reset, clean, checkout, restore, stash, rebase, commit, overwrite, or unrelated formatting/refactor

### Frozen target

Extend the existing single-case prospective staging function with one optional, exact in-memory governance-shadow replacement lane for `marriage.divorce_or_remarriage`. When supplied, the lane adapts one canonical `yang_qingjuan` projection through the frozen W2-C2 adapter, proves ownership of the existing prospective `yang` slot, rebuilds that replacement with the exact original alias identity, merges it into the already complete legacy grid, then preserves the existing timing-safety, complete-grid, time-window, final-freeze, verification, parent, revision, and artifact construction flow.

Legacy callers that supply no governance-shadow inputs must retain current staging behavior and deterministic replay. Newly prepared single-case bundles intentionally gain parent-bound task metadata and therefore new task/bundle/manifest/final-artifact hashes; byte identity with pre-W2-C3 artifacts is not required or possible.

### Exact implementation whitelist

Only the following production/test files may be modified during a later separately authorized IMPLEMENT:

1. `engine/evaluation/prospective_single_case.py`
   - retain authoritative `evaluation_note` in `_TASK_BUNDLE_FIELDS`;
   - preserve intake compatibility by comparing the intake catalog hash with the legacy canonical task projection that omits only `evaluation_note`, while the newly bundled task bytes and manifest bind the complete metadata;
   - define the narrow exact typed merge helper(s);
   - extend `build_single_case_staged_frozen_run()` with the frozen keyword-only input pair;
   - invoke the frozen W2-C2 adapter after legacy grid generation and verified bundled-task reconstruction, but before timing safety and final complete-grid validation.
2. `tests/evaluation/test_prospective_frozen_run.py`
   - add only W2-C3 single-case task-metadata, staging integration, fail-closure, deterministic-replay, and static isolation/accounting tests;
   - existing prospective tests may be minimally adjusted only where a helper task assignment must include the admitted task.

`tests/evaluation/test_dataset.py` is explicitly read-only. Its note-removal assertion covers the separate general-purpose `tools.school_capability_dataset.prepare_blind_bundle()` path and must remain unchanged.

No other file is writable. In particular, the following are frozen read-only dependencies: `engine/evaluation/governance_shadow_adapter.py`, `engine/application/governance_shadow_types.py`, `engine/governance/school_registry.py`, `engine/evaluation/models.py`, `engine/evaluation/freeze.py`, `tools/school_capability_prospective.py`, `tools/school_capability_dataset.py`, `tests/evaluation/test_dataset.py`, all task catalogs/rule snapshots, all governance runners/adapters/registries, all CLI/publication/custody/scoring modules, `.omo/boulder.json`, and project metadata.

### Frozen public API delta

The only admitted production API change is the following keyword-only extension; exact parameter names are frozen:

```python
def build_single_case_staged_frozen_run(
    bundle_root: Path,
    *,
    now_utc: str | None = None,
    freeze_at: str | None = None,
    executed_at: str | None = None,
    revision: Mapping[str, Any] | None = None,
    migration_context: Mapping[str, Any] | None = None,
    governance_shadow_result: GovernanceShadowResult | None = None,
    governance_shadow_projections: tuple[GovernanceShadowTaskProjection, ...] = (),
) -> dict[str, Any]: ...
```

Contract rules:

1. The two new arguments are in-memory only and keyword-only.
2. The legacy mode is exactly `governance_shadow_result is None` plus an exact empty tuple of projections.
3. Governance mode requires `type(governance_shadow_result) is GovernanceShadowResult`, `type(governance_shadow_projections) is tuple`, and exactly one exact `GovernanceShadowTaskProjection` item.
4. Supplying only one side, a list/other sequence, an empty governance tuple with a result, more than one projection, a duck type, or a subclass fails closed before final freeze.
5. No CLI parameter, serialized staged-artifact field, environment variable, path, loader, registry, or default projection is added.

### Task metadata and parent-binding invariants

1. `_TASK_BUNDLE_FIELDS` adds exactly `evaluation_note`; no other task field is added or removed.
2. `tasks.json` contains the exact source catalog value. Missing, empty, altered, or forbidden-content `evaluation_note` fails through existing catalog extraction/validation or the W2-C2 exact task predicate.
3. No code constant, adapter private constant, alternate catalog read, or post-bundle patch may synthesize the note.
4. The bundled task is reconstructed from the already verified `root / "tasks.json"` document.
5. The selected task must be unique and exactly `marriage.divorce_or_remarriage`; zero or duplicate task rows fail closed.
6. Intake compatibility is computed from a legacy canonical projection of the same task rows that omits exactly `evaluation_note`; it is used only to validate the pre-existing intake `task_catalog_sha256` and is not written as bundled task content.
7. Newly bundled `tasks.json`, its manifest file hash, `bundle_sha256`, manifest hash, final `task_catalog_sha256`, freeze hash, and artifact digest bind the complete metadata including `evaluation_note`.
8. Existing pre-W2-C3 immutable artifacts are not rewritten, migrated, or claimed byte-identical. Replaying equal inputs against the same newly prepared bundle remains deterministic.
9. `evaluation_note` is immutable task semantics, not label/outcome material; existing forbidden marker/value checks remain active and are not weakened.

### Projection/result/bundle binding invariants

The integration must call `adapt_governance_shadow_to_blind_outputs()` exactly once in governance mode and must not duplicate any W2-C2 semantic predicate locally.

Before merge, all of the following are required:

1. W2-C2 adapter validation succeeds and returns exactly one `BlindSchoolOutput`.
2. Projection and adapter output case IDs exactly equal the verified single-case intake `case_id`.
3. Projection and output task IDs exactly equal the unique verified bundled task `marriage.divorce_or_remarriage` and that task is assigned in the single-case intake.
4. Projection and adapter output school IDs are exactly canonical `yang_qingjuan`.
5. Projection `task_catalog_version` exactly equals `generated_run.task_catalog_version`; projection `rule_version` exactly equals `generated_run.rule_snapshot_id`.
6. Projection result/snapshot/input assertions remain bound by the frozen W2-C2 adapter to the supplied exact `GovernanceShadowResult`.
7. `calculator_version` remains an explicit non-empty external projection attestation checked by W2-C2 for one-call consistency; W2-C3 must not claim that the bundle or result authenticates it.
8. W2-C3 must not reinterpret result absence, arbitration, pressure text, report text, governance confidence, capability data, or task metadata as a prediction.

### Canonical ownership and alias reconstruction invariants

1. The target legacy key is exactly `(verified_case_id, "yang", "marriage.divorce_or_remarriage")`.
2. `normalize_school_input("yang")` must equal the canonical adapter output identity `yang_qingjuan` before replacement.
3. No reverse alias table, string splitting, prefix matching, synonym lookup, or generic canonical migration may be introduced.
4. The accepted canonical output is rebuilt as a new `BlindSchoolOutput` with only `school_id` changed to the original exact alias `yang`; case, task, state, rationale, predictions, and counter-evidence remain semantically identical.
5. The canonical row itself is never inserted into the prospective grid or serialized artifact.
6. Zero target rows, multiple target rows, duplicate output identities, target reuse, school mismatch, case mismatch, task mismatch, catalog/rule mismatch, or cardinality drift fails closed.

### Merge, timing, grid, and freeze invariants

1. The legacy `tools.school_capability_prospective.build_staged_frozen_run()` path still constructs the complete base grid first.
2. Governance mode replaces exactly one row and preserves every non-target `BlindSchoolOutput` object/value unchanged.
3. Output count before and after replacement is identical.
4. `_safe_timing_outputs()` runs on the merged output sequence, not only on the replacement.
5. `_assert_complete_single_case_grid()` runs after timing safety and still enforces exactly `SIX_SCHOOLS × assigned task_ids`, unique identities, and the three legal states.
6. Existing freeze-time, execution-window, parent-time, future-question, revision, migration, artifact-path, and parent-chain checks remain in their current order and semantics.
7. The existing final `freeze_outputs()` is called only after the merged sequence passes timing and grid checks; `verify_frozen_run()` remains mandatory.
8. Any governance-input or merge failure occurs before the authoritative final freeze call and returns no W2-C3 artifact.
9. The legacy inner freeze is not removed or treated as W2-C3 proof; the final single-case freeze remains authoritative.
10. Legacy no-governance mode over the same newly prepared bundle and explicit times must produce deterministic identical returned dictionaries across replay and must preserve all output/grid/time/freeze behavior except hashes transitively changed by the intentional parent-bound `evaluation_note` addition.
11. No existing immutable bundle or frozen artifact is rewritten to obtain that compatibility.
12. Governance mode must produce deterministic identical returned dictionaries for replayed equal typed inputs and explicit times; changing the admitted projection's bound prediction material must change the final freeze hash/artifact digest.

### Outcome isolation and static dependency invariants

1. No feedback, label, reveal, observation, report, known-fact, scoring, posterior, high-risk-review, custody-release, cohort, publication, routing, production, network, subprocess, environment, clock, random, Git, or GitHub dependency may be added for this lane.
2. No file is read for governance inputs. The only new semantic input objects are the two exact keyword arguments.
3. No governance runner, dependency loader, projection creator, projection reviewer, certification registry, capability registry, YAML loader, or report parser may be imported or called.
4. The W2-C2 adapter and its public projection/result types plus `normalize_school_input()` are the only admitted governance dependencies in the staging module.
5. Imports should remain module-level unless an existing circular dependency requires a local import; any local import must still satisfy the exact static allowlist and must not hide an outcome-bearing dependency.
6. The serialized bundle and staged/frozen artifact schemas gain no projection, result, custody, review, or governance metadata fields.

### Scope IN

- Exact preservation of `evaluation_note` in the verified blind task bundle.
- One optional in-memory Yang divorce/remarriage projection replacement lane.
- Exact canonical ownership check and reconstruction to the existing `yang` slot.
- Fail-closed binding to verified case/task and generated catalog/rule identities.
- Existing timing safety, complete-grid validation, and final freeze over the merged grid.
- Focused tests and static AST/API/dependency accounting inside the exact whitelist.

### Scope OUT

- Running governance shadow, typed claim production, projection construction/review/signing/certification/publication/reload, or caller custody proof.
- Multiple projections, multiple slots, another school/task, a generic merge framework, canonical migration of `SIX_SCHOOLS`, or replacement of the complete legacy generator.
- New dataclass, protocol, registry, loader, serializer, CLI option, artifact schema, projection file, or configuration switch.
- Editing the W2-C2 adapter/types, governance runner, school registry, generic freeze/model/scoring code, task catalogs, rule snapshots, routing, production API, or project state.
- Label reveal, scoring, posterior updates, high-risk review, cohort gates, capability publication, routing, production switch, deployment, reports, Git, or GitHub.
- Claims of projection provenance truth, calculator-version authentication, prediction accuracy, calibration, publication readiness, production readiness, Wave 2 completion, or repository-wide correctness.

### Required implementation behavior partitions

A later IMPLEMENT must create focused coverage for at least these partitions without deleting existing coverage:

1. single-case task bundle preserves exact `evaluation_note`, remains manifest/hash parent-bound, and accepts the pre-existing intake hash only through the exact note-omitting legacy comparison;
2. legacy no-input path is behavior-compatible and deterministic on replay, with only the admitted task-metadata parent/hash delta versus pre-W2-C3 artifacts;
3. valid exact Yang claim replaces only the `yang × marriage.divorce_or_remarriage` slot and freezes a complete unique alias grid;
4. valid abstain and unsupported projections preserve honest states without predictions;
5. exact typed boundary rejects half-binding, list/duck/subclass, empty, and multi-projection inputs;
6. case, task, school, task-catalog version, rule version, result-visible identity, target uniqueness, and cardinality mismatches fail before final freeze;
7. canonical `yang_qingjuan` never appears in final grid while ownership normalization is mandatory;
8. all non-target rows remain unchanged;
9. timing safety and complete-grid validation still apply after merge;
10. equal typed input replay freezes deterministically, while changed prediction material changes final hashes;
11. outcome-bearing files/material cannot affect or enter the governance merge API;
12. static AST/API accounting proves no forbidden dependencies/calls/schema fields and confirms exact public signature.

### Exact future verification selectors

Test execution is not authorized by this CONTRACT. If IMPLEMENT and VERIFY are separately authorized, the initial exact selectors are:

```text
pytest -q tests/evaluation/test_prospective_frozen_run.py -k "governance_shadow or evaluation_note or single_case_frozen_run_is_complete_unique_parent_bound_grid or single_case_frozen_run_rejects_incomplete_or_duplicate_grid or single_case_frozen_run_keeps_timing_claim_with_structured_liunian_fact_ref or single_case_frozen_run_never_freezes_unresolved_liunian_fact_ref or single_case_frozen_run_never_freezes_timing_claim_without_liunian_fact_ref"
pytest -q tests/evaluation/test_governance_shadow_adapter.py
```

The W2-C2 adapter suite is read-only regression evidence; W2-C3 implementation must not alter it. No `tests/evaluation/test_dataset.py` selector is included because the general-purpose bundle contract is outside W2-C3 and remains unchanged.

Broader regression, if later authorized after focused PASS:

```text
pytest -q tests/evaluation/test_prospective_frozen_run.py tests/evaluation/test_governance_shadow_adapter.py
```

No full-suite or repository-wide correctness claim follows from these selectors.

### Static accounting required before dynamic verification

A fresh STATIC_REVIEW must account for:

- exact changed files equal a subset of the two-file whitelist;
- no W2-C2 adapter/type or other read-only dependency changed;
- exact public function signature and defaults;
- exact `_TASK_BUNDLE_FIELDS` delta;
- no serializer/CLI/artifact schema delta;
- AST imports/calls in the staging module introduce only the admitted governance adapter/types and school normalization;
- no forbidden marker/dependency/path/environment/network/subprocess/Git/GitHub surface;
- adapter called once only in governance mode;
- timing/grid/final-freeze ordering preserved;
- test collection counts and parameterized instance counts recorded before interpreting results.

### Reviewer questions

1. Is one independently reviewable behavior target frozen, with legacy mode preserved?
2. Is the exact two-file whitelist both necessary and sufficient, with every other dependency read-only?
3. Does the exact API prohibit serialized/unreviewed projection loading and partial inputs?
4. Are A1 task semantics parent-bound without synthesis?
5. Are projection identities bound only where evidence exists, especially leaving calculator version externally attested?
6. Does canonical ownership remain exact while the final grid remains alias-only?
7. Can exactly one slot be replaced without changing cardinality or non-target rows?
8. Are timing, grid, freeze, verification, parent, and artifact invariants preserved?
9. Are outcome isolation and static dependency restrictions executable rather than aspirational?
10. Are selectors narrow, discoverable, and explicitly non-authorizing?

### Falsifiers and STOP conditions

Return `REVISE`, `BLOCKED`, or `AUTHORIZATION_REQUIRED` as applicable if:

- exact task semantics cannot remain parent-bound without a second source of truth;
- changing bundled task bytes breaks an immutable parent contract that cannot be revised within the whitelist;
- projection case/catalog/rule identity cannot bind to verified staging identities;
- a canonical output must coexist with aliases or source ownership requires weakening;
- more than one projection/slot or a generic framework is required;
- implementation requires changing W2-C2, governance runners/types/registries, generic freeze/models, catalogs, CLI, schema, publication/custody/scoring/routing/production code, Boulder, or project metadata;
- any governance input must be loaded from disk/environment/network or an outcome-bearing source;
- timing/grid/final-freeze ordering must be bypassed;
- an existing protected change must be overwritten or destructive Git cleanup is required;
- any GitHub mutation is proposed; this is permanently `BLOCKED` and cannot be authorized;
- behavior conclusions would depend on unexecuted, stale, partial, or unauthorized tests.

### Direct evidence boundary

A future CONTRACT PASS would prove only that this exact two-file implementation target and its review/verification obligations are sufficiently frozen to request IMPLEMENT authorization. It would not prove implementation, behavior, test PASS, projection custody provenance, prediction quality, publication readiness, production readiness, or Wave 2 completion.

### Forbidden inference boundary

CONTRACT approval cannot be interpreted as permission to activate Boulder, edit files, run tests, execute STATIC_REVIEW/VERIFY, publish, route, switch production, deploy, mutate Git/GitHub, or proceed to any successor Gate without its own authorization.

## CONTRACT review history

### R1 logically fresh verdict

`REVISE`

Cited defects:

1. The first draft simultaneously required adding parent-bound `evaluation_note` bytes and pre-W2-C3 artifact byte identity; those requirements are mutually exclusive.
2. The first draft misclassified the general-purpose bundle assertion in `tests/evaluation/test_dataset.py` as the single-case contract owner. That test covers `tools.school_capability_dataset.prepare_blind_bundle()` and must remain unchanged.
3. The first draft did not explicitly freeze how the existing intake hash remains compatible after the single-case bundled task gains `evaluation_note`.

R2 repairs only those cited defects: it narrows the whitelist to two files, preserves the general-purpose bundle contract, freezes the exact note-omitting legacy hash comparison, and limits legacy compatibility to behavior plus deterministic replay with an explicit metadata/hash delta.

### R2 logically fresh verdict

`REVISE`

The reviewer role and prior conclusions were reset. The full candidate contract, authorization boundary, ADMISSION PASS, exact whitelist, invariants, selectors, falsifiers, STOP conditions, direct-evidence boundary, and forbidden-inference boundary were re-read. Two bounded consistency defects remain:

1. Reviewer question 2 still says `three-file whitelist`, contradicting the exact two-file whitelist and static accounting.
2. The top-level controller state still says CONTRACT is not authorized, contradicting the recorded user authorization and active CONTRACT Gate.

No implementation feasibility, behavior, test, custody-provenance, publication, production, or successor-Gate conclusion was reviewed or granted.

### Sub-Contract Revision Loop — Anchor Ledger

The second CONTRACT `REVISE` activates the bounded revision loop. These anchors come from the user authorization, ADMISSION PASS, inspected existing interfaces, and predecessor frozen boundaries—not from a rejected draft.

- Unit: `W2-C3`
- Frozen public API surface: only the keyword-only pair `governance_shadow_result: GovernanceShadowResult | None = None` and `governance_shadow_projections: tuple[GovernanceShadowTaskProjection, ...] = ()` may be added to `build_single_case_staged_frozen_run()`; all existing parameters and returned artifact schema remain unchanged.
- Frozen CLI grammar: no CLI addition or change.
- Frozen state/transition surface: optional legacy mode or exact one-projection governance mode; no governance runner, projection creation/reload, reveal, scoring, publication, routing, or production transition.
- Frozen error semantics: all half-bound, wrong-type, wrong-cardinality, identity/version/target mismatch, mixed-school identity, and pre-final-freeze merge failures fail closed without an authoritative W2-C3 artifact.
- Frozen idempotence/conflict semantics: equal inputs over the same newly prepared bundle and explicit times replay deterministically; no immutable artifact is rewritten; changed admitted prediction material changes final hashes.
- Frozen output schema: existing prospective alias-only complete grid and existing serialized frozen-run/artifact schemas; only parent-bound task metadata and transitive hashes intentionally evolve.
- Frozen file whitelist: exactly `engine/evaluation/prospective_single_case.py` and `tests/evaluation/test_prospective_frozen_run.py`.
- Protected dependencies: all other files are read-only; Boulder, Git, GitHub mutation, deployment, publication, routing, and production switching remain forbidden.

### Revision State Table

| Revision | Author role reset? | Reviewer role reset? | Verdict | Defect classes found | Repeated from earlier revision? | Anchor drift found? |
|---|---:|---:|---|---|---:|---:|
| R1 | n/a | yes | `REVISE` | artifact compatibility; generic/single-case owner and whitelist; legacy intake hash | n/a | n/a |
| R2 | yes | yes | `REVISE` | stale whitelist wording; stale authorization/controller state | whitelist class remains from R1 | yes: whitelist/state wording |
| R3 | yes | yes | `REVISE` | stale authorization text remained in two additional contract locations | yes: authorization/controller-state class was incompletely repaired | yes: authorization/state wording |
| R4 | yes | yes | `AUTHORIZATION_REQUIRED` | top-level state still names R3 pending after R4 literal patch | yes: authorization/controller-state class remains | yes: controller-state wording; round cap reached |

### R3 bounded author revision

The author role was reset and received only the Anchor Ledger plus the two R2-cited defects. The revision is limited to these literal corrections:

1. `three-file whitelist` → `exact two-file whitelist` in reviewer question 2.
2. Top-level controller authorization/current-stage/verdict lines now record CONTRACT authorization and `R3 AUTHOR REVISION COMPLETE / FRESH REVIEW PENDING` while retaining all successor prohibitions.

No API, whitelist entry, invariant, selector, STOP condition, production/test file, Boulder state, Git state, or successor authorization was changed.

### R3 logically fresh verdict

`REVISE`

The reviewer role and prior conclusions were reset, and the Anchor Ledger plus full current candidate were re-read. The two R2-cited locations were corrected, but the same authorization/controller-state defect class remained in two additional locations:

1. The `User authorization` paragraph still said CONTRACT was not authorized.
2. The CONTRACT controller record still said `PENDING FRESH REVIEW` without identifying the active revision, conflicting with the top-level R3 state.

This is an incomplete repair of the previously cited authorization/controller-state class. The repeat-defect control therefore forbids another free-form rewrite and limits R4 to the two literal corrections below.

### R4 literal-patch author revision

The author role was reset. Against the Anchor Ledger, only these literal corrections were applied:

1. The authorization paragraph now records the later CONTRACT approval and continues to deny IMPLEMENT, tests, Boulder, publication, routing, production, deployment, Git, and GitHub mutation.
2. The CONTRACT controller record now states `REVISE until a logically fresh R4 review`.

No other contract clause, API, whitelist entry, invariant, selector, STOP condition, production/test file, Boulder state, Git state, or successor authorization changed.

### R4 logically fresh verdict and loop STOP

`AUTHORIZATION_REQUIRED`

The reviewer role and prior conclusions were reset, and the Anchor Ledger plus full current candidate were re-read. The two intended R4 literal corrections are present in the authorization paragraph and CONTRACT controller record. However, the top-level controller state still says `CONTRACT R3 AUTHOR REVISION COMPLETE / FRESH REVIEW PENDING` and `REVISE until a logically fresh R3 review`. That directly contradicts the active R4 review and is the same repeatedly cited authorization/controller-state defect class.

The default cap of three revision rounds after R1 has now been reached: R2, R3, and R4. The Sub-Contract Revision Loop forbids another autonomous draft. No substantive API, whitelist, compatibility, invariant, selector, falsifier, STOP-condition, or evidence-boundary defect was found in R4; nevertheless, unresolved controller-state contradiction prevents CONTRACT PASS.

Direct evidence boundary: this verdict proves only that the revision loop reached its cap with one bounded stale-state defect still present. It does not prove implementation feasibility, behavior, test PASS, custody provenance, publication readiness, production readiness, or CONTRACT PASS.

Forbidden inference boundary: no IMPLEMENT, test, Boulder, Git/GitHub, successor Gate, deployment, publication, routing, or production authority follows.

### User-authorized final logically fresh CONTRACT review

`PASS`

The reviewer role and all prior conclusions were reset. The review used the Anchor Ledger, the full current candidate contract, the explicit authorization/protection boundary, ADMISSION PASS, and the inspected authoritative interfaces. The user-authorized literal correction removes the only R4 blocker: the top-level state no longer names R3 or claims that an R3 review is pending.

PASS-condition accounting:

1. Exactly one target is frozen: an optional, exact in-memory Yang divorce/remarriage replacement at the single-case pre-final-freeze seam.
2. Scope OUT and negative behavior are explicit; governance execution, serialized projection custody, reveal/scoring/publication/routing/production, Boulder, Git, and GitHub remain excluded.
3. The implementation whitelist is exactly two files, while the generic dataset bundle/test and all predecessor dependencies remain read-only.
4. The public API pair, legacy/governance modes, exact-type/cardinality failures, task-note parent binding, legacy intake-hash projection, canonical ownership/alias reconstruction, one-slot merge, timing/grid/final-freeze order, deterministic replay, and intentional metadata/hash delta are explicit and non-contradictory.
5. Required behavior partitions, exact future selectors, static accounting method, reviewer questions, falsifiers, STOP conditions, direct-evidence boundary, and forbidden-inference boundary are present.
6. No test was run, no implementation was performed, and no successor Gate or remote side effect was inferred.

No active CONTRACT falsifier or STOP condition remains. This PASS establishes only that the contract is unique, bounded, falsifiable, and implementable under a separately authorized exact IMPLEMENT action. It is not implementation correctness, behavior evidence, custody provenance, prediction quality, publication readiness, production readiness, or Wave 2 completion.

## Unique next legal action

Stop at CONTRACT PASS. A separate explicit user authorization is required before W2-C3 IMPLEMENT; until then no production/test edit, test execution, Boulder activation, Git/GitHub action, or successor Gate is legal.

## W2-C3 final evidence-bounded freeze and handoff

- Final controller state: `HANDOFF`.
- CONTRACT: user-authorized logically fresh `PASS`.
- IMPLEMENT: limited to `engine/evaluation/prospective_single_case.py` and `tests/evaluation/test_prospective_frozen_run.py`.
- STATIC_REVIEW R2: logically fresh `PASS`; the exact two-file scope, public API, admitted dependencies, one adapter call site, merge → timing safety → complete-grid validation → final freeze order, and 44 collected test instances were accounted.
- VERIFY run 1: the frozen W2-C3 selector collected 20 selected instances, passed 20, deselected 24, failed 0, and exited 0.
- VERIFY run 2: the read-only W2-C2 adapter regression selector collected and passed 123 instances, failed 0, and exited 0.
- EVIDENCE_REVIEW: logically fresh `PASS`; selector discovery, static/dynamic accounting, prior RED/GREEN and STATIC_REVIEW `REVISE` history, falsifiers, and evidence limits were reviewed.
- Freeze verdict: `PASS / COMPLETE — EVIDENCE-BOUNDED FREEZE`.
- Directly proven: the selected W2-C3 integration behavior and the selected W2-C2 adapter regression surface pass under the observed local test environment.
- Not proven: full-suite or repository-wide correctness, projection provenance truth, prediction quality, calibration, performance, security, publication readiness, deployment readiness, routing correctness, production readiness, Wave 2 completion, or any GitHub state.
- Side-effect boundary: no Boulder activation, Git/GitHub mutation, deployment, publication, routing, or production switch was performed by this controlled unit.
- Handoff status: `COMPLETE`; this append is minimum local controller persistence after the concluded two-file IMPLEMENT stage and does not expand the frozen implementation whitelist.
- Successor rule: any successor unit must independently RECOVER and obtain its own ADMISSION, CONTRACT, authorization, verification, and evidence review; no W2-C3 authority or PASS is inherited.
