# Wave2 planning collection: Yang marriage lane

Status: COMPLETE (read-only planning collection)
Collected: 2026-08-06, Asia/Shanghai
Scope: Yang marriage semantics, Wave1 governance seam, tests, and hazards
Product changes: none
Git writes: none

## Decisive recommendation

Wave2 must preserve the newer Yang three-state discriminator as the sole semantic
source and add a new, typed Yang-to-governance application boundary. Do not route
the current Yang `SchoolClaim` through the generic legacy adapter, do not broaden
the generic metadata whitelist, and do not modify the frozen Yang claim builder or
slice serialization.

The new boundary must be event-only:

- `event` may yield exactly one governance claim, but only after the existing L1
  school role is non-abstaining and an exact published capability is eligible.
- `pressure` yields no divorce/remarriage governance claim.
- `abstain` yields no governance claim.
- Missing capability, temporal scope, reference version, role, or certified input
  remains a typed abstention/failure. None may be guessed from confidence or text.

## Authoritative semantic contract

The authoritative implementation is `engine/decision/yang_marriage.py`, not the
older V5 runner.

1. The output vocabulary is the closed three-state set `pressure | event |
   abstain` (`engine/decision/yang_marriage.py:13`).
2. Event requires both independent gates:
   - A: `spouse_palace_event_anchor`.
   - B for male charts: `spouse_star_peer_interaction`.
   - B for female charts: `spouse_star_output_interaction` or
     `mixed_official_kill`.
   The family declarations are at lines 16-18 and the sex-compatible event-family
   validation is at lines 397-403. The final A+B decision is at lines 502-531.
3. A spouse-palace clash alone is A-only. It must remain `pressure` with
   `missing_independent_spouse_interaction`; it is not a divorce event
   (`tests/yang_marriage/test_signal_families.py:351-382`).
4. Hard blockers, including unknown sex, incomplete evidence, invalid day pillar,
   and invalid relationship pairs, force `abstain` and clear both event gates
   (`engine/decision/yang_marriage.py:409-461` and
   `tests/yang_marriage/test_signal_families.py:403-439`).
5. Evidence is reduced by `family_key` and stably sorted, so each of the six
   evidence families contributes at most once (`engine/decision/yang_marriage.py:363`).
6. The discriminator is static and input-pure. It must not consume history,
   revealed labels, reports, feedback, or a numeric independent-signal threshold
   (`tests/yang_marriage/test_static_isolation.py:281-320`). Pair-order
   permutations must serialize identically
   (`tests/yang_marriage/test_synthetic_matrix.py:141-157`).

## Existing claim and slice behavior to freeze

`engine/decision/yang_marriage_claims.py:22` emits exactly one `SchoolClaim` only
for a complete event and a non-abstaining L1 role. Pressure and abstention emit an
empty tuple (`tests/yang_marriage/test_school_claim_adapter.py:30-58`). The emitted
legacy claim is:

- school: `yang_qingjuan`
- task: `marriage.divorce_or_remarriage`
- kind: `event_claim`
- stance: `support`
- confidence: `0.60`
- wording: conservative risk language, explicitly not inevitability

`engine/decision/yang_marriage_slice.py:69` removes only the obsolete Yang target,
preserves every non-target legacy object, and adds native L2-L5 objects only for an
event. Legacy and native L3-L5 are built separately to avoid the global L4 cap,
then all complete domains are jointly arbitrated once at L6. The slice stops at
L6: report, feedback, attribution, and calibration remain empty. The preservation
and joint-arbitration assertions are at
`tests/yang_marriage/test_slice_layers.py:96-202`; zero target objects for pressure
or abstention are asserted at lines 295-304.

These are regression contracts. Wave2 must not change them.

## Wave1 integration blocker

Directly calling `adapt_decision_school_claim()` on the current Yang legacy claim
is invalid by design:

- `SCHOOL_METADATA_KEYS` permits only `task_id`, `stance`, `temporal_scope`, and
  `reference_version`
  (`engine/application/governance_claim_adapter_values.py:41-43`).
- Yang currently writes `source_scope` and `family_keys` into metadata
  (`engine/decision/yang_marriage_claims.py:88-92`).
- Yang does not write `temporal_scope` or `reference_version`.
- The generic adapter rejects unapproved keys before requiring explicit scope and
  version (`engine/application/governance_claim_adapters.py:90-123`). Its
  fail-closed missing-scope behavior is intentional and tested at
  `tests/application/test_governance_claim_adapters.py:82-103`; metadata injection
  rejection is covered at
  `tests/application/test_governance_claim_adapter_boundaries.py:95-145`.

Therefore Wave2 must not loosen `SCHOOL_METADATA_KEYS`, strip information from a
legacy claim, or inject new metadata into the frozen builder. It needs a separate
typed boundary that maps the discriminator result and explicit governance context
directly into the governance envelope. `source_scope` and `family_keys` should be
represented through typed provenance/derivation inputs, not smuggled into generic
legacy metadata.

The formal registry is another fail-closed blocker:
`theory/multi-school-governance-v1.yaml:11` currently has `capabilities: []`. Even
a valid event envelope cannot pass eligibility until Wave2 publishes one exact
capability identity for canonical school `yang_qingjuan`, task
`marriage.divorce_or_remarriage`, kind `event_claim`, the explicitly selected
inferential grade, and the explicitly selected governance reference version.
Aliases, the historical school id `yang`, wrong grades, wrong kinds, and wrong
versions must remain misses.

The prospective catalog entry at
`META/prospective-go-task-catalog-v1.json:30` marks this task binary,
quantifiable, high risk, and lifetime/ten-year scoped, requiring four pillars and
a sex marker. The typed boundary must therefore require an explicit compatible
temporal scope; it must not silently treat a static pressure result as a dated or
lifetime divorce event.

## Wave2 implementation seams

1. Add a small typed application adapter, preferably a dedicated
   `engine/application/governance_yang_marriage_adapter.py`, rather than changing
   `engine/decision/yang_marriage_claims.py` or the generic legacy adapter.
2. Give the adapter typed inputs for the immutable `YangMarriageDiscrimination`,
   the granted canonical L1 role, explicit `TemporalScope`, explicit governance
   reference/version, and typed source/derivation references. Do not accept raw
   metadata dictionaries or duck-typed `object` values.
3. Encode the gate before claim construction: only `state == "event"`, A passed,
   sex-compatible B passed, and non-abstaining L1 can enter governance claim
   construction. Pressure and abstention return no claim without public event
   wording.
4. Bind constants at the Yang-specific boundary: canonical school
   `yang_qingjuan`, task `marriage.divorce_or_remarriage`, kind `event_claim`, and
   support stance. Keep confidence `0.60` as legacy evidence strength; never use it
   to infer scope, capability, or event completion.
5. Publish exactly one matching capability in
   `theory/multi-school-governance-v1.yaml` only after the inferential grade and
   reference version are explicit in the Wave2 contract. Registry absence or any
   dimension mismatch must remain ineligible.
6. Integrate this boundary in the Wave2 governance/shadow orchestration after Yang
   discrimination and L1 applicability, without calling the older count-based
   runner and without altering the existing L2-L6 slice.

## Tests required before implementation is accepted

- Keep the existing `tests/yang_marriage` suite green without edits to its frozen
  behavior assertions.
- Red-first test: A-only palace clash is pressure and creates zero governance
  claims.
- Red-first test: pressure and abstention create zero governance claims and no
  public divorce/remarriage wording.
- Red-first test: complete male and female A+B events each create exactly one
  deterministic governance envelope when L1, scope, references, and capability
  all match.
- Red-first test: unknown/abstaining L1, missing scope/version/reference, invalid
  source binding, or incomplete evidence fails closed.
- Registry matrix: exact canonical capability is eligible; `yang`, aliases,
  substring/case variants, wrong task, kind, grade, and version are ineligible.
- Boundary regression: the generic legacy adapter continues rejecting the current
  Yang metadata rather than learning Yang-specific exceptions.
- Provenance regression: family order and relationship-pair order do not change
  claim identity or serialization; duplicate families do not increase support.
- Slice regression: all non-target legacy L2-L5 objects remain field-for-field
  unchanged and L6 still arbitrates each domain once.
- Isolation regression: no history, reports, feedback, labels, or
  `independent_signal_count >= 2` dependency is introduced.

Suggested focused verification after Wave2 implementation:

```text
python -B -m pytest tests/yang_marriage -q -p no:cacheprovider
python -B -m pytest tests/application/test_governance_yang_marriage_adapter.py -q -p no:cacheprovider
python -B -m pytest tests/governance/test_school_registry.py tests/application/test_governance_claim_adapters.py -q -p no:cacheprovider
```

## Do-not-copy hazards

The historical V5 path is separate. `engine/v5/yang_runner.py:46` uses numeric
`independent_signal_count >= 2`, and `engine/claims/runner_registry.py:68`
registers it under school id `yang`. It must not be treated as the three-state
contract or as the canonical governance identity `yang_qingjuan`.

The three current Yang product files also predate Wave1 quality gates. A fresh
strict audit found 36 violations across them:

```text
python -B C:\Users\Administrator\.codex\plugins\cache\sisyphuslabs\omo\4.13.0\skills\programming\scripts\python\check-no-excuse-rules.py engine\decision\yang_marriage.py engine\decision\yang_marriage_claims.py engine\decision\yang_marriage_slice.py
result: exit 1, 36 violations in 3 files
```

Breakdown: 30 bare `ValueError` findings, three non-slotted dataclasses, one
`# type: ignore`, one `object` annotation, and one oversized module
(`yang_marriage.py`, 520 pure LOC). The slice also relies on private V5 adapter
helpers and duck typing. This does not authorize a legacy refactor in Wave2; it
means the new adapter must be a small, strict, slotted/immutable, typed module and
must not copy these patterns.

Primary behavioral hazards, in priority order:

1. Critical: inflating pressure into a divorce/remarriage event.
2. Critical: weakening the Wave1 metadata/capability fail-closed boundary.
3. High: using old count-based V5 semantics instead of named A+B families.
4. High: publishing capability under `yang` instead of `yang_qingjuan`, or using a
   guessed grade/version.
5. High: feeding native claims through the shared L4 cap and dropping unrelated
   legacy domains before L6 arbitration.
6. Medium: implying timing, reporting, calibration, or learning that this static
   L2-L6 slice does not produce.
7. Medium: copying legacy escape hatches into new Wave2 code.

## Fresh evidence

Behavioral suite:

```text
python -B -m pytest tests/yang_marriage -q -p no:cacheprovider
result: exit 0, 145 passed in 6.99s
```

This collection performed no product edits and no Git writes. The only write is
this planning evidence file.

Confidence: 0.97. The three-state and slice semantics are directly executable and
fully green. The adapter incompatibility and empty capability registry are direct
source facts. The remaining 0.03 is reserved for the Wave2 owner to select and
review the exact inferential grade and governance reference version before
publishing capability; this collection intentionally does not guess them.

Evidence bytes (UTF-8): 011951
