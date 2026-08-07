# Wave2 Planning Collection - Actual Wave1 Interfaces

Date: 2026-08-06 (Asia/Shanghai)  
Workspace: `F:\多流派新思路`  
Mode: read-only interface collection and plan-claim falsification; no subagents

## Verdict

- interface map: **confirmed against current source and tests**
- confidence: **0.97**
- collection blockers: **none**
- product/test edits: **none**

Wave1 provides a deterministic, immutable, fail-closed path from public fact
construction through typed legacy-claim adaptation and seven-gate shadow
arbitration. It does **not** provide Wave2 freeze, label-isolated scoring,
promotion proposal, publication, or production-switch contracts. Those are new
Wave2 responsibilities and must not be inferred from similarly named Wave1
registry fields.

## Wave2 Authority Claims

Design section 15.2 at
`plans/multi-school-governance-design-2026-08-02.md:594-628` proposes:

```text
shared facts -> Yang marriage decision -> other-school claim/abstention
-> source folding -> arbitration -> frozen prediction -> isolated scoring
-> promotion proposal -> explicit production publication
```

Current code directly supports the first, adaptation, folding, arbitration, and
shadow-result portions only. The remaining downstream chain must be designed
against the contracts below.

## Public Import Boundaries

### Root governance facade

`engine/governance/__init__.py:80-143` exposes 62 explicit names. Stable Wave2
reuse should prefer this facade for canonical/fact/claim/school/arbitration/
composition/trigger contracts, including:

- `FactSpec`, `GovernanceFact`, `SnapshotSpec`, `FactSnapshot`,
  `build_governance_fact()`, `build_fact_snapshot()`;
- `GovernanceClaimSpec`, `GovernanceClaim`, `GovernanceReferenceCatalog`,
  `build_governance_claim()`;
- `CapabilityIdentity`, `CapabilityQualification`, `CapabilityAbstention`,
  `SchoolRegistry`, `load_school_registry()`;
- `ArbitrationArena`, `ArbitrationContext`, `ArbitrationDecision`,
  `FactConflictContext`, `arbitrate()`;
- `CompositionExecutionMode`, `CompositionResult`, `execute_composition()`;
- `TriggerRegistrationSpec`, `TriggerOutcome`, `build_trigger_registry()`,
  `evaluate_governance_trigger()`.

The root facade deliberately does **not** export the shadow runner, structure
catalog loader/types, full certification loader/types, composition loader, or
trigger loader. Use their reviewed submodule facades; do not widen root exports
merely for Wave2 convenience.

### Registry facade

`engine/governance/registries.py:58-102` is the public facade for certification,
school/capability, trigger, and composition registry types/loaders. It exposes
`load_fact_certification_registry()`, `load_school_registry()`,
`load_trigger_registry()`, and `load_composition_registry()`.

### Application package boundary

`engine/application/__init__.py:48-60` preserves ten legacy application exports
and does not export governance shadow APIs. Wave2 must import the opt-in surface
from `engine.application.governance_shadow_runner`, not register it implicitly
in `engine.application` or a default production pipeline.

## Facts And Canonical Identity

| Surface | Exact contract | Input -> output / failure | Extension use |
|---|---|---|---|
| `canonical_digest()` | `engine/governance/canonical.py:135` | bounded canonical material -> SHA-256 canonical digest; rejects unsupported, cyclic, or non-finite data with `CanonicalizationError` | Reuse for any new content-bound Wave2 artifact. |
| `stable_object_id()` | `canonical.py:147` | validated namespace + identity material -> stable namespaced ID | New artifact namespaces must be explicit and domain-separated. |
| `FactLevel` | `fact_values.py:94-98` | exactly L0 `canonical_observation`, L1 `candidate_derived`, L2A `certified_technical`, L2B `certified_cross_school` | Do not introduce event labels as fact levels. |
| `TemporalScope` | `fact_values.py:130-190` | `layer`, optional dayun range, optional target year; layer-specific fields fail closed | Divorce/remarriage prediction windows must use explicit typed scope. |
| `FactSpec` | `fact_values.py:208-229` | fact kind/level/scope/source/input/calculator identity | New facts must declare provenance and calculator version. |
| `build_governance_fact()` | `contracts.py:123` | `FactSpec + CanonicalValue -> GovernanceFact` | Produces immutable payload, stable fact ID, and content digest. |
| `GovernanceFact` | `contracts.py:53-89` | ID, kind, level, scope, refs, calculator, frozen payload, digest | Read-only school inputs; never mutate or add school conclusions. |
| `SnapshotSpec` | `fact_values.py:232-244` | schema version, case ID, input digest | Bind each Wave2 frozen public-fact snapshot to exact input bytes. |
| `build_fact_snapshot()` | `contracts.py:220` | `SnapshotSpec + tuple[GovernanceFact] -> FactSnapshot` | Sorts deterministically; duplicate IDs reject; conflicting content raises typed integrity error. |
| `FactSnapshot` | `contracts.py:177-196` | snapshot ID/version/case/facts/input/content digests | Reusable upstream input for triggers and arbitration, not a prediction freeze artifact. |

Tests: `test_fact_contracts.py:52-258` covers closed domains, deep freeze,
identity/content separation, temporal fail-closure, order invariance, duplicate/
conflict handling, and version binding. `test_canonical.py:83-253` covers digest
determinism and unsafe-input rejection.

## Fact Builder

`build_governance_fact_snapshot()` at
`engine/application/governance_fact_builder.py:237` has the actual signature:

```python
build_governance_fact_snapshot(
    case_id: str,
    raw_payload: RawWenzhenPayload,
    chart: ChartFactLedger,
    *,
    target_year: int | None = None,
    calculator_version: str,
    feature_vector: ChartFeatureVector | None = None,
) -> FactSnapshot
```

Contract:

- emits only L0 chart facts and optional versioned L1 feature facts;
- requires an explicit valid `target_year` within declared dayun ranges before
  emitting liunian (`governance_fact_builder.py:142-194`);
- does not infer the current year or use `as_of_date` as target year;
- rejects stale source hashes, overlapping/invalid dayun ranges, mismatched
  feature vectors, and raw prompt text as facts.

Tests: `test_governance_fact_builder.py:88-334`. In particular, lines 110, 158,
202, 237, 274, 311, 321, and 334 lock missing-year omission, invalid-year
rejection, no school conclusions in facts, no raw prompt facts, temporal
separation, range validation, chart binding, and source-hash binding.

## Certification Registry

| Surface | Path:line | Contract |
|---|---|---|
| `CertificationIdentity` | `fact_certification.py:40-90` | exact `fact_level + fact_kind + calculator_id + calculator_version + schema_version`; only L2A/L2B identities are valid |
| `FactCertification` | `fact_certification.py:114-194` | registration ID, identity, publication status, specification digest, cross-school review refs; L2A/L2B rules remain distinct |
| `PublicationStatus` | `fact_certification.py:33-36` | candidate/proposed/published; only published entries enter lookup map |
| `FactCertificationRegistry.lookup()` | `fact_certification.py:249` | exact identity -> certification or typed `UnsupportedFactCertification`; no adjacent-version fallback |
| `load_fact_certification_registry()` | `fact_certification_loader.py:178` | strict local YAML path -> immutable registry; containment/symlink/schema checks |

Extension point: add reviewed, content-bound certification entries under the
existing YAML schema only when Wave2 needs L2A/L2B facts. Do not turn scored
prediction outcomes into certifications or use certification publication as a
production-role switch.

Current default state is empty:
`theory/multi-school-governance-v1.yaml:2` is `certifications: []`.

Tests: `test_fact_certification_registry.py:85-300` verifies exact-version
lookup, strict L2A/L2B separation, canonical peer review refs, candidate/
proposed exclusion, tamper/path rejection, and no mutation API.

## Governance Claims And Legacy Adapters

### Claim envelope

`GovernanceClaimSpec` at `engine/governance/governance_claim.py:29-46` requires:

- `school_id`, `task_id`, closed `ClaimKind`, closed `ClaimStance`, conclusion;
- separate public/certified/school-reason/source-rule references;
- explicit `TemporalScope`, blockers, counterevidence, falsifier, confidence;
- `ClaimEvidenceGrade`, derivation-chain digest, optional adapter provenance.

`build_governance_claim(spec, catalog)` at `governance_claim.py:91` returns a
content-bound immutable `GovernanceClaim` only after exact category/ID/version
reference validation. Closed values are at
`governance_claim_values.py:42-88`; `GovernanceReferenceCatalog.validate()` is
at `:145`.

Tests: `test_governance_claim.py:92-256` and
`test_governance_claim_derivation.py:73-147` cover immutability, abstention
reason, high-risk counterevidence/falsifier, exact reference versions,
identity/content separation, and source-bound derivation.

### Adapters

| Adapter | Path:line | Input -> output |
|---|---|---|
| `adapt_decision_school_claim()` | `engine/application/governance_claim_adapters.py:90-166` | exact legacy `SchoolClaim` + reference catalog -> `AdaptationResult(claim | None, issues)` |
| `adapt_domain_claim()` | `governance_claim_adapters.py:169-250` | exact legacy `Claim` + catalog + explicit scope + optional support/oppose stance -> `AdaptationResult` |
| `derivation_chain_digest()` | `engine/governance/governance_claim_derivation.py:12` | source refs + provenance + source metadata -> content-bound derivation digest |

The `SchoolClaim` adapter requires an approved role, canonical/boundary-mapped
school, supported claim type, explicit stance, explicit temporal scope,
`task_id`, `reference_version`, valid categorized references, and catalog
registrations (`governance_claim_adapters.py:93-165`). It returns typed losses;
it never guesses missing semantics.

Critical Wave2 boundary: an old Yang `claim_type="pressure"` is explicitly not
adapted into event support (`tests/application/test_governance_claim_adapters.py:176-203`).
Wave2 must preserve pressure as a separate boundary/output rather than relabel
it as divorce/remarriage evidence.

Also note: `adapt_school_views()` currently invokes only
`adapt_decision_school_claim()` (`governance_shadow_school_views.py:32-63`). The
domain `Claim` adapter is not part of the shadow runner path.

## School And Capability Registry

| Surface | Path:line | Contract |
|---|---|---|
| `CapabilityIdentity` | `school_registry.py:122-139` | exact school x task x claim kind x evidence grade x version identity |
| `CapabilityRole` | `school_registry.py:70-74` | lead, co-lead, evidence-only, abstain |
| `CapabilityQualification` | `school_registry.py:161-175` | exact published match; `winner_eligible` false for evidence-only |
| `CapabilityAbstention` | `school_registry.py:178-187` | typed reason and fixed abstain role for missing/unpublished registration |
| `SchoolRegistry.lookup_capability()` | `school_registry.py:256-280` | exact complete identity -> qualification or abstention; no nearest/global fallback |
| `SchoolRegistry.lookup_school()` | `school_registry.py:248-254` | canonical peer -> `PeerSchool`; `ditiansui` -> legacy source; other -> `UnknownSchool` |
| `load_school_registry()` | `school_registry_loader.py:158` | strict YAML -> immutable exact-five registry |

The peer set is exactly five at `school_registry.py:12-18`; Ditiansui is only a
`LegacyCompatibilitySource` (`:104-113`). The current default YAML has no
capability entries (`theory/multi-school-governance-v1.yaml:11`). Therefore a
Wave2 plan that uses the default registry without adding exact published
capabilities will cause every new claim to abstain at applicability.

Tests: `test_school_registry.py:11-197` fixes five-peer order, Ditiansui
exclusion, boundary-only aliases, exact no-fallback capability lookup,
evidence-only non-winning behavior, and YAML integrity.

## Seven-Gate Arbitration

`arbitrate(arena: ArbitrationArena) -> ArbitrationResult` is
`engine/governance/arbitration.py:29`.

`ArbitrationArena` at `arbitration_contracts.py:189-223` requires:

- immutable `claims: tuple[GovernanceClaim, ...]`;
- `ArbitrationContext(facts, FactCertificationRegistry)` (`:173-185`);
- exact `GovernanceReferenceCatalog` and `SchoolRegistry`;
- one `capability_version` and optional typed fact conflicts.

The fixed gate sequence is the `GateName` enum at
`arbitration_contracts.py:22-29`: eligibility, temporal, evidence,
independence, counterevidence, applicability, decision.

`ArbitrationResult` at `arbitration_result.py:50-149` returns the decision and
content digest plus retained/applicable/minority/preserved variants, temporal
groups, independent evidence groups, counterevidence traces, audits, and gate
history. It is an audit result, not a frozen prediction or promotion proposal.

Extension point: Wave2 may construct new event claims and an arena using exact
published capabilities. Do not modify gate order, add global school weights,
reuse legacy `_weighted_sides`, or route through legacy `arbitrate_staged()`.

Tests: `test_arbitration_gates.py:132-235` and
`test_arbitration_properties.py:26-291` cover gate order, exact capability
abstention, temporal separation, high-risk human review, permutation
invariance, idempotence, same-source folding, trace retention, empty-arena
abstention, and fact-conflict closure.

## Restricted Composition

`execute_composition()` at `composition_executor.py:111` accepts an immutable
`CompositionRegistry` and keyword-only template ID/version/components/mode,
returning `CompositionResult`.

Key contracts:

- modes are only shadow/production (`composition_contracts.py:29-31`);
- result fields are outcome/template/digest/components plus optional output
  kind/scope/grade/issue (`composition_contracts.py:83-180`);
- templates declare exact accepted kinds/stances/tasks/scopes, component slots,
  output kind, grade cap, preservation rules, review conditions, status, and
  digest (`composition_templates.py:39-55`);
- registry lookup is exact template ID + version
  (`composition_templates.py:206-222`);
- loader is `composition_loader.py:174`.

Current YAML supplies one `synthetic_only` template
(`theory/multi-school-governance-v1.yaml:12-35`). It rejects production mode.

Important falsification: `CompositionResult` is **not** a `GovernanceClaim`.
The shadow runner executes composition only into `CompositionTrace` and never
feeds a composed claim into arbitration (`governance_shadow_runner.py:140-177,
235-250`). Wave2 cannot claim a working claim-composition-arbitration chain
without a new approved claim-emission contract.

Tests: `test_composition_registry.py:19-221` and
`test_composition_execution.py:13-51` cover shadow-only authority, production
rejection, exact versions/components, evidence cap, independence,
counterevidence, and falsifier preservation.

## Trigger Registry

| Surface | Path:line | Contract |
|---|---|---|
| `TriggerRegistrationSpec` | `trigger_registry.py:79-86` | string boundary parsed into closed evaluator/status/scope fields |
| `build_trigger_registry()` | `trigger_registry.py:229` | specs -> immutable exact registry |
| `evaluate_governance_trigger()` | `trigger_registry.py:269` | registry + ID + snapshot + context -> `TriggerOutcome(active, typed issues)` |
| `load_trigger_registry()` | `trigger_loader.py:111`; convenience wrapper `trigger_registry.py:292` | strict governance YAML -> registry |

Closed evaluators are only `fact_kind_present` and
`liunian_target_year_present` (`trigger_registry.py:33-35`). Unknown,
unpublished, and missing facts are inactive (`:269-289`). `as_of_date` and a
parsed-object flag cannot replace an explicit target-year fact.

Current YAML triggers are `candidate` and `synthetic_only`, not published
(`theory/multi-school-governance-v1.yaml:37-55`).

Important falsification: the shadow runner records trigger outcomes but does
not use `active` to gate school claims, composition, or arbitration
(`governance_shadow_runner.py:117-149,235-250`). Wave2 must specify the exact
consumer and fail-closed control flow for any new divorce/remarriage trigger.

Tests: `test_trigger_registry.py:93-289` covers all closure and determinism
claims.

## Thirty-Structure Catalog

`load_structure_catalog()` is `engine/governance/structure_catalog.py:206` and
returns `StructureCatalog` (`structure_catalog_models.py:137-141`). Each entry
at `structure_catalog_models.py:70-84` is metadata: ID/key/display/family,
roles, candidate/clear/block/damage condition types, source status,
implementation status, optional legacy mapping, source refs, and digest.

This catalog contains exactly 30 entries. Only the three existing legacy
structures are `current_implemented`; all other entries are
`catalog_only_candidate` or `catalog_only_review`
(`theory/ziping/structure-catalog-v1.yaml:13-449`).

It provides no evaluator, school claim, event label, publication operation, or
production registration. Wave2 marriage work must not treat a catalog entry as
executable evidence.

Tests: `test_structure_catalog.py:15-230` and
`test_structure_catalog_integrity.py:14-85` cover count/IDs, closed fields,
legacy projection, digest integrity, malformed YAML, and no production import.

## Shadow Application Contract

### Request and dependencies

`GovernanceShadowRequest` at
`engine/application/governance_shadow_types.py:48-56` contains case/raw/chart/
calculator, precomputed school views, optional target year/feature vector, and
fact conflicts.

`GovernanceShadowDependencies` at `:60-68` injects the reference, school,
certification, trigger, and composition registries; exact capability version;
and requested triggers/compositions.

`SchoolViewOutcome` at `:22-25` contains a school ID and tuple of legacy
`SchoolClaim`; `SchoolViewFailure` at `:28-31` records unavailable school
diagnostics. The runner does not execute Yang or other school logic itself.

### Runner

`run_governance_shadow(request, dependencies) -> GovernanceShadowResult` is
`governance_shadow_runner.py:214-264`.

Actual flow:

1. build public fact snapshot;
2. adapt precomputed school views;
3. independently evaluate requested triggers;
4. independently execute requested composition traces in shadow mode;
5. fail closed on declared fact conflicts;
6. build arena and run the new seven-gate arbitration;
7. return deterministic trace/result digest.

`GovernanceShadowResult` at `governance_shadow_types.py:187-223` has status,
snapshot IDs/digests/kinds, adapted claim traces, unavailable/excluded schools,
trigger and composition traces, optional arbitration trace, issues, and result
digest. It is serializable via `to_canonical()` but does not persist itself.

Tests: `test_governance_shadow_runner.py:148-269` covers one-school failure,
fact-conflict closure, deterministic ordering, missing target year, Ditiansui
exclusion, and static production isolation. Import isolation is locked by
`test_application_import_isolation.py:7-87`.

## Plan-Claim Falsification Matrix

| Proposed Wave2 assumption | Current verdict | Evidence / required correction |
|---|---|---|
| Wave1 can create deterministic shared facts | TRUE | Fact builder + immutable fact/snapshot contracts are reusable. |
| Shadow runner executes Yang and other schools | FALSE | It accepts already-computed `SchoolViewOutcome`/failure only. Wave2 needs an explicit school-view execution/orchestration boundary. |
| Default registry authorizes Wave2 multi-school claims | FALSE | Default certifications and capabilities are empty. Add exact reviewed registrations and versions first. |
| Existing adapter can map Yang divorce/remarriage event claims | PARTIAL | Only explicitly supported legacy claim types/metadata/references map. Yang pressure is deliberately rejected as event support. Characterize actual Yang outputs before planning mappings. |
| Arbitration supplies deterministic source folding | TRUE | Seven-gate path and independence tests are reusable. |
| Trigger activation currently gates the shadow chain | FALSE | Trigger outcomes are traces only. Define consumer/control flow explicitly. |
| Composition currently emits claims into arbitration | FALSE | It returns `CompositionResult`/trace only; arena receives original adapted claims. |
| `FactSnapshot` is a frozen prediction artifact | FALSE | It freezes public facts, not prediction/label blindness. A separate content-addressed prediction-freeze contract is needed. |
| `ArbitrationResult` supports label-isolated scoring | FALSE | It has no label, reveal, score, calibration, coverage, or abstention-metric protocol. |
| Registry `PublicationStatus.PUBLISHED` is production promotion | FALSE | It controls local registry lookup eligibility only. Production role publication requires a separate explicit authority and audit artifact. |
| Structure catalog supplies executable marriage evaluators | FALSE | Catalog is metadata-only and predominantly catalog-only. |
| Wave1 provides coverage/abstention/calibration metrics | FALSE | No mapped public contract computes them. Wave2 must define denominators, abstention taxonomy, calibration inputs, and immutable results. |

## Non-Negotiable Boundaries For Wave2

1. Narrow event target: divorce/remarriage only; pressure and generalized
   marriage quality remain distinct.
2. No historical labels, feedback, report data, or known outcomes may enter
   fact construction, claims, routing, or prediction before freeze.
3. Explicit `target_year` and typed temporal scope are mandatory; no current/
   as-of inference.
4. Five peers only. Ditiansui remains legacy compatibility and outside the
   arena.
5. Capability authority is exact school/task/kind/grade/version; missing or
   unpublished entries abstain. No global weight or uniform fallback.
6. Same-source duplication must not add a vote; retain counterevidence,
   falsifier, minority, and gate trace.
7. Yang pressure cannot be relabeled as event support.
8. Catalog-only entries are not evaluators or production rules.
9. Shadow execution remains opt-in and write-free until an explicit Wave2
   publication boundary is approved.
10. Legacy `SchoolClaim`, `Claim`, staged L6, router defaults, production loader,
    report/feedback/learning entrypoints, and package exports remain frozen.

## Integration Hazards

1. **Missing downstream contracts:** freeze, reveal, label isolation, score,
   calibration, coverage/abstention metrics, promotion proposal, approval, and
   publication are absent from Wave1.
2. **Empty default authority:** new claims will abstain unless exact published
   capabilities and reference registrations are deliberately added.
3. **Precomputed-school-view seam:** runner does not call school engines; errors,
   timeouts, and provenance must be captured by a new application boundary.
4. **Adapter loss:** unsupported Yang claim kinds or missing metadata silently
   become auditable losses, not claims. Planning must enumerate every expected
   legacy output class before implementation.
5. **Trigger/composition are observational:** current traces do not affect arena
   inputs. Do not draw a connected Wave2 flow diagram without adding explicit
   typed consumers.
6. **Certification is not scoring:** L2 certification governs facts and exact
   calculator versions, not prediction truth or model promotion.
7. **Publication naming collision:** registry publication means lookup-eligible,
   not production-switch authorized.
8. **Public import discipline:** shadow/catalog/full loaders are submodule APIs;
   widening root package exports risks import fanout and compatibility drift.
9. **No clean Git provenance:** most Wave1 artifacts are untracked; pin content
   hashes or establish a reviewed baseline before Wave2 depends on them.
10. **Local registry check/read race:** the final security lane records a
    nonblocking local consistency risk. Resolve it before registry bytes become
    remote/adversarial or production-authoritative.

## Recommended Wave2 Planning Seams

These are planning seams, not implementation authorization:

1. typed school-view executor that returns existing `SchoolViewOutcome |
   SchoolViewFailure` with source/version provenance;
2. exact Yang divorce/remarriage legacy-output characterization and adapter
   mapping table, preserving event/pressure/abstention distinctions;
3. reviewed reference and capability registry additions for every participating
   school/task/kind/grade/version;
4. content-addressed prediction-freeze artifact separate from `FactSnapshot`;
5. one-way reveal and label-isolated scoring contracts with accuracy, coverage,
   abstention, and calibration outputs;
6. immutable promotion proposal and separately authorized publication receipt;
7. an explicit rule for whether trigger/composition outcomes gate, create, or
   merely annotate claims, with tests proving the chosen flow.

## Cleanup

- No product, test, YAML, plan, registry, package export, or Git state was
  modified.
- AST/signature inspection ran from stdin with `python -B`; no bytecode or temp
  script was created.
- No tests, server, process, port, debugger, network request, or subagent was
  started.
- This evidence file is the only repository write.
