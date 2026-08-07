---
slug: ten-god-structure-production-closure
status: plan-written
intent: clear
pending-action: choose execution or dual Momus review
approach: Build a complete ten-god relation graph plus a corpus-closed 30-structure catalog, then carry one typed assessment snapshot through the compatibility pipeline and V5 with fail-closed namespaced triggers, exhaustive curated theory classification, explicit-only annual evaluation, report projection, feedback binding, and evidence-gated calibration. Do not switch the default production entrypoint.
---

# Draft: ten-god-structure-production-closure

## Components (topology ledger)
<!-- Lock the SHAPE before depth. One row per top-level component that can succeed or fail independently. -->
<!-- id | outcome (one line) | status: active|deferred | evidence path -->
1 | Eleven-node/110-directed-pair relation graph and 30-item catalog produce natal/dayun/explicit-liunian structure states | active | engine/predicates/ten_god_structures.py; mapping/ten-god-structure-catalog-v1.yaml
2 | Compatibility pipeline and V5 use the same fail-closed trigger semantics | active | engine/application/production_rule_triggers.py; engine/predicates/condition_evaluator.py; engine/v5/runner.py
3 | Every theory alias candidate is explicitly classified and mapped by semantic class rather than runtime text matching | active | theory/ziping/index.yaml; theory/tiaohou_ditiansui/index.yaml; mapping/ten-god-structure-rule-map-v1.yaml
4 | Analysis snapshots and reports expose structure state without internal IDs | active | engine/domain/analysis.py; engine/v5/domain.py; tools/render_report.py
5 | Statement feedback distinguishes structure, cycle phase, blocker, and annual timing errors | active | tools/render_report.py; tools/feedback_ingest.py
6 | Accuracy gates cover the full relation matrix, all 30 catalog entries, zero unclassified theory candidates, and isolated real-case replay | active | tests/predicates; tests/test_ten_god_structure_inventory.py; tests/test_production_rule_loader.py; cases/

## Open assumptions (announced defaults)
<!-- Record any default you adopt instead of asking, so the user can veto it at the gate. -->
<!-- assumption | adopted default | rationale | reversible? -->
Production route | Integrate compatibility pipeline and V5 without changing the default entrypoint | avoids a product-routing decision and follows engine/README.md migration constraints | yes
Completeness boundary | Day master plus ten gods form 11 nodes and all 110 non-self directed relation slots, plus 30 named structures evidenced by the current repository corpus | gives an objective closure gate without conflating single-pattern, follow-structure, climate, or shensha systems | yes
Annual semantics | Evaluate liunian only from an explicitly supplied target year or explicit year list | user rejected as-of/current-date inference | yes
Theory mapping | Add an explicit curated mapping artifact; never infer executable structure semantics from claim text at runtime | the production corpus contains general principles and chart-specific excerpts | yes
Learning | Record feedback and produce calibration candidates, but do not auto-promote rules or weights | current governance is human-gated | yes
Test strategy | TDD for every behavior change, with synthetic unit cases and pipeline/V5 integration scenarios | repository uses pytest and the current predicate slice already has focused tests | yes

## Findings (cited - path:lines)
- Precise assessments exist but are currently consumed mainly by the compatibility trigger helper: engine/predicates/ten_god_structures.py:39; engine/application/production_rule_triggers.py:80.
- Compatibility integration calls ProductionRuleLibrary.triggered_rules(): engine/application/integration.py:290.
- V5 ZiPing currently selects every quantifiable rule before trigger filtering: engine/v5/runner.py:163 and engine/v5/runner.py:175.
- V5 condition evaluation treats unknown triggers as true: engine/predicates/condition_evaluator.py:129 and engine/predicates/condition_evaluator.py:165.
- The six-source context derives current dayun and three future years from as_of_date and is therefore excluded from this implementation path: engine/v5/domain_slices/context.py:20, :24, :27.
- AnalysisOutput has no typed ten-god structure field: engine/domain/analysis.py:182.
- The current statement ledger builder is the feedback binding surface: tools/render_report.py:1779.
- Dynamic-confidence learning reads statement_records.json rather than statement_index.json: engine/statement_runtime.py:18-35; tools/feedback_ingest.py:925-989.
- V5 snapshots currently persist chart, claims, graph, arbitration, prediction ledger, and learning signals but no named ten-god structure field: engine/v5/domain.py:370-470 and engine/v5/domain.py:651-689.
- V5 chart adapters already recognize optional dayun_steps; when absent, the structure adapter must produce natal-only results instead of inventing cycle data: engine/decision/v5_adapter.py:66.
- The production indexes currently use eleven legacy trigger names: always, has_dayun, has_energy_structure, has_liunian, has_marriage_picture, has_official_picture, has_tianluodiwang, has_tiaohou_advice, has_wealth_picture, has_zhi_chong, wuxing_imbalanced. Structure triggers should use the validated `ten_god_structure/<catalog-id>` namespace; the original three trigger names remain compatibility aliases.
- Repository scans find general-principle support for flow/protection, control/transformation, officer-killing clearing, and destructive/imbalance structures. Representative high-signal rules include ZP-PROD-20260622-012/018/019/032/033/034/035/037/040/369/370/474/476 and DTS-PROD-20260622-088/657/788.
- The production theory indexes contain both general structure principles and chart-specific historical excerpts; runtime string matching would over-generalize them: theory/ziping/index.yaml; theory/tiaohou_ditiansui/index.yaml.
- The worktree contains extensive unrelated modified and untracked files; execution must use explicit path scopes and must never clean or reset globally.

## Decisions (with rationale)
- Introduce one immutable typed relation graph plus structure snapshot as the only cross-layer representation; do not pass ad hoc dictionaries.
- Define completeness as two enforceable gates: the day master plus ten gods form 11 nodes whose 110 non-self directed relation slots each have a typed relation or explicit none reason, and every catalog-alias hit in the current production corpora is classified. Do not claim universal coverage outside the repository corpus.
- Store the 30 named structures in `mapping/ten-god-structure-catalog-v1.yaml` as the sole exhaustive list; keep the original three-item enum/API only as a compatibility wrapper.
- Classify catalog evidence as `direct`, `normalized`, or `composite`; composite entries may only combine already evidenced directed relations from the same corpus, never free-form intuition.
- Restrict catalog recipes to typed operators with validated arity and operands: `role`, `edge`, `body_strength`, `chain`, `stem_combine`, `structure_state`, `all`, `any`, and `not`. Strength is limited to `weak/balanced/strong/excessive`; complex clearing, exhaustion, combine-control, and blade-killing balance use registered specialized evaluator keys.
- Add a batch assessment API accepting requested_years: tuple[int, ...]. Preserve the existing single-kind target_year keyword as a compatibility wrapper.
- Separate natal structure truth from cycle transitions. A dayun-completed structure cannot be reported as natal-established.
- An annual layer is absent when no explicit year is supplied. No system clock, analysis date, or current-year fallback may populate it.
- Replace boolean-only structure matching with typed RuleActivation records carrying structure kind, source layer, phase, dayun ganzhi/year range, and explicit annual year. Compatibility pipeline and V5 production selection must share this strict service; V5 must bypass the legacy condition evaluator's fail-open unknown-trigger default. This prevents cycle activations from being flattened into natal truth.
- Validate production trigger names against the eleven observed legacy names plus `ten_god_structure/<catalog-id>`. Normalize the original three trigger names to catalog IDs. All unknown production triggers and structure IDs fail closed and fail loader validation.
- Curate rule-to-structure mappings offline and validate them at load time. Every alias candidate is classified as general_principle/case_excerpt/explanation/counterexample/out_of_scope; chart-specific excerpts remain evidence/reference material and cannot become generic triggers.
- Store the catalog at mapping/ten-god-structure-catalog-v1.yaml and curated mappings at mapping/ten-god-structure-rule-map-v1.yaml. Each mapping includes rule_id, structure_id, semantic_class, executable, allowed_phases, rationale, source_digest, source_trigger, and effective_trigger. Only general_principle may be executable; an executable structure mapping uses its namespaced effective trigger without rewriting the large production indexes.
- Add a named typed ten_god_structures field to both AnalysisOutput and V5Output/V5RunSnapshot; include it in serialization and V5 output hashing. Do not hide it in generic metadata.
- Bind feedback to structure kind plus layer identity, cycle ganzhi/year range, explicit year when present, and evidence hashes.
- Extend statement records with a typed structure_context projection. Structure feedback writes to a dedicated append-only candidate ledger and is excluded from automatic rule lifecycle fanout until an explicit future promotion decision.
- A V5 chart with four valid pillars but no dayun_steps yields natal-only structure assessments. Incomplete pillars yield an explicit unsupported diagnostic and no structure claims.
- Before implementation, freeze `.omo/evidence/preflight-worktree-baseline.json` from NUL-delimited porcelain state plus file type/size/SHA-256 for every existing dirty path and the full `cases/`/`reports/` trees. Final QA may only accept changes under exact Todo allowlisted pathspecs and must prove every baseline out-of-scope hash unchanged.
- Do not claim improved real-world accuracy from passing tests. Promotion requires isolated case evidence and separate structure/phase/blocker/timing metrics.

## Catalog evidence closure
- Evidence modes: `direct` means the corpus states the structure; `normalized` means a documented variant or synonym maps to the canonical term; `composite` means the structure is composed only from two or more corpus-evidenced directed relations.
- Flow/protection (13): `officer_generates_seal`, `killing_generates_seal`, `wealth_generates_officer`, `wealth_generates_killing`, `food_god_generates_wealth`, `hurting_officer_generates_wealth`, `hurting_officer_uses_seal`, `food_god_uses_seal`, `seal_protects_officer`, `officer_protects_wealth`, `output_releases_excellence`, `wealth_officer_seal_flow`, `output_wealth_officer_flow`.
- Control/transformation (5): `food_god_controls_killing`, `hurting_officer_controls_killing`, `blade_killing_balanced`, `rob_wealth_combines_killing`, `hurting_officer_combines_killing`; `blade_killing_balanced` requires both blade and killing to be effective and mutually balancing, not a fabricated one-way blade-controls-killing edge.
- Clearing (3): `officer_killing_mixed`, `officer_killing_cleared`, `hurting_officer_exhausted`.
- Destructive/imbalance (9): `hurting_officer_meets_officer`, `owl_robs_food`, `wealth_damages_seal`, `peers_compete_for_wealth`, `wealth_aids_killing_attack`, `overcontrolled_killing`, `killing_attacks_body`, `output_overdrains_body`, `excess_seal_blocks_output`.

## Scope IN
- The complete 11-node/110-directed-pair ten-god role relation graph and the 30-item catalog defined in the approved work plan, including flow/protection, control/transformation, clearing, and destructive/imbalance families.
- Shared typed snapshots, serialization, compatibility pipeline attachment, V5 claim generation, report projection, statement ledger binding, feedback classification, and focused calibration status.
- Fail-closed namespaced structure triggers, compatibility aliases for the original three, and tests proving no implicit annual inference.
- Exhaustive offline inventory and curated theory classification for all current corpus alias candidates.
- Synthetic and isolated real-case verification artifacts.
- Contract documentation in engine/contracts/22-ten-god-structure-state-v1.md plus the required overview index update; merge requires the repository's contract-review process.

## Scope OUT (Must NOT have)
- No as-of date, system-date lookup, implicit current year, or automatic future-three-year generation.
- No single-pattern 格局, 从格, 专旺格, 化气格, 调候, or shensha expansion under the label of ten-god relation structures.
- No ad hoc 31st catalog item; new corpus terms must fail the inventory gate until a catalog version decision is made.
- No default production entrypoint switch.
- No automatic rule/weight promotion and no mutation of historical run snapshots.
- No runtime semantic inference from Chinese claim text or ancient-case excerpts.
- No broad cleanup of legacy dataclasses, oversized modules, unrelated tests, cases, reports, or dirty-worktree artifacts.
- No writes to cases/ or reports/ during verification; real-case replay must use read-only inputs and temp/output paths outside those roots.
- No global dirty-worktree diff as proof of scope; verification must compare the preflight manifest, exact allowlisted pathspecs, and all out-of-scope hashes.

## Open questions
None. The user approved the recommended defaults and scope.

## Approval gate
status: approved
approved-by: user
approved-scope: cover the complete current-corpus ten-god relation system through a full relation graph and 30 named structures; dual integration without default switch; explicit-only annual evaluation; no as-of date
<!-- When exploration is exhausted and unknowns are answered, set status: awaiting-approval. -->
<!-- That durable record is the loop guard: on a later turn read it and resume at the gate instead of re-running exploration. -->
