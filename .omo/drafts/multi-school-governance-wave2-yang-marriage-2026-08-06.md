---
slug: multi-school-governance-wave2-yang-marriage-2026-08-06
status: contract-pass
intent: clear
pending-action: write and fresh-review .omo/plans/multi-school-governance-wave2-yang-marriage-2026-08-06.md before activating Wave 2
approach: shadow-only typed Yang marriage governance boundary; no production publication
---

# Draft: multi-school-governance-wave2-yang-marriage-2026-08-06

## Controller state

- Current Gate: `CONTRACT`.
- Prior Gates: `RECOVER PASS`, `INVENTORY PASS`, `ADMISSION PASS`.
- Active independently reviewable unit: Yang marriage three-state discrimination to typed governance claim/loss boundary.
- Shared-worktree protection: preserve all pre-existing tracked and untracked changes; no reset, clean, checkout, restore, stash, rebase, commit, or unrelated edits.
- Remote boundary: local-only; no GitHub-mutating operation is permitted.
- Wave 2 remains inactive in Boulder/ledger until a complete implementation plan receives fresh adversarial review.

## Components (topology ledger)

| id | outcome | status | evidence path |
|---|---|---|---|
| W2-C1 | Typed Yang `event` to `GovernanceClaim` adapter with fail-closed `pressure`/`abstain` handling | active | `.omo/evidence/wave2-plan-collect-yang-marriage.md` |
| W2-C2 | `GovernanceShadowResult` to `BlindSchoolOutput` semantic adapter | deferred | `.omo/evidence/wave2-plan-collect-freeze-scoring.md` |
| W2-C3 | Frozen prediction, label-isolated scoring, and high-risk review chain | deferred | `.omo/evidence/wave2-plan-collect-freeze-scoring.md` |
| W2-C4 | Typed promotion-candidate artifact | deferred | `plans/multi-school-governance-design-2026-08-02.md:410` |
| W2-C5 | Explicit production publication receipt and human authorization boundary | deferred | `plans/multi-school-governance-design-2026-08-02.md:428` |

Only `W2-C1` is admitted by this contract. Deferred components must receive separate ADMISSION and CONTRACT Gates.

## Open assumptions (announced defaults)

| assumption | adopted default | rationale | reversible? |
|---|---|---|---|
| Governance evidence grade | `inferential` | User-selected conservative binding; matches the current generic adapter ceiling without claiming corroboration | yes, only through a new explicit contract decision |
| Adapter/capability version | `yang-marriage-discrimination/v1` | Binds the existing typed discriminator schema rather than inventing an unrelated version | yes, through versioned successor contract |
| Source-rule version | `sha256:e8be77f67246ff056770a35d618b4b3fc5694ba5fdec2f65c8d674708355e768` | Content-addresses the observed bytes of `theory/yang/index.yaml`; does not imply publication | yes, new bytes require a new digest and review |
| Temporal layer | `natal` only | Existing generic adapter and current slice expose no approved richer temporal mapping | yes, only after a separate temporal contract |
| Capability role | no registration in this unit | The registry is empty and role/publication is a distinct governance decision | yes, in a separate registry-publication unit |
| Claim confidence | `0.60` | Preserves the existing authoritative Yang event-claim boundary without introducing label-derived calibration | yes, through a versioned successor contract |

## Findings

1. The Wave 1 governance registry has an exact five-dimensional capability identity: school, task, claim kind, evidence grade, and version. Missing, mismatched, candidate, or proposed capability must abstain.
2. `theory/multi-school-governance-v1.yaml` currently has empty `certifications` and `capabilities`; this unit must not add guessed capability or certification entries.
3. Registry `published` means local lookup eligibility only. It is not a production-switch authorization.
4. The authoritative Yang discriminator returns exactly `pressure | event | abstain`. Only complete A+B independent evidence is `event`; `pressure` and `abstain` must not emit divorce/remarriage governance claims.
5. The authoritative discriminator emits schema `yang-marriage-discrimination/v1` and source refs `theory/yang/index.yaml#M2-Y-068` and `theory/yang/index.yaml#M2-Y-088`.
6. The generic decision-school adapter accepts only legacy `SchoolClaim`, fixes evidence grade to `inferential`, and depends on a metadata reference version. Expanding its metadata whitelist would weaken an existing isolation boundary.
7. No typed `GovernanceReferenceCatalog` producer exists for this Yang slice. The active unit therefore accepts an explicit catalog argument and fails closed when exact references or versions are absent.
8. Existing offline gates can permit a proposal only: `proposal_allowed=true` remains paired with `production_switch=false`. They do not implement a typed promotion artifact or production publication receipt.
9. The current applicable offline thresholds are 20 completed immediate subjects with one task having 15 positive-and-negative labels, and 10 future subjects with one task having 8 positive-and-negative labels; calibration error must be below 0.2 for the same eligible task. These thresholds are outside W2-C1 behavior and must not be copied into this adapter.

## User decisions

- Use `ClaimEvidenceGrade.INFERENTIAL` for the first Yang governance adapter.
- Bind adapter/capability version to `yang-marriage-discrimination/v1`.
- Bind source-rule references to the current `theory/yang/index.yaml` SHA-256 listed above.
- Three-state semantics have precedence over source validation: `pressure` and `abstain` always return `INSUFFICIENT_EVIDENCE`; only `event` validates exact source refs and catalog registration.
- Remain shadow-only.
- Production publication remains a separate explicit human authorization; this contract does not grant it.

## Anchor Ledger — Unit W2-C1

| frozen surface | exact anchor | source |
|---|---|---|
| Public API | `adapt_yang_marriage_discrimination(result: YangMarriageDiscrimination, catalog: GovernanceReferenceCatalog) -> AdaptationResult` | admitted unit and existing typed application boundary pattern |
| State machine and validation precedence | `pressure | event | abstain`; only `event` may emit one support claim or enter source/catalog validation; `pressure` and `abstain` terminate first with `INSUFFICIENT_EVIDENCE` | authoritative `YangMarriageDiscrimination` contract plus explicit user decision |
| Claim identity | `yang_qingjuan × marriage.divorce_or_remarriage × event × inferential × yang-marriage-discrimination/v1`; stance `support`; temporal layer `natal` | user decision plus existing Yang claim boundary |
| Source identity | discriminator-owned exact anchors, each versioned `sha256:e8be77f67246ff056770a35d618b4b3fc5694ba5fdec2f65c8d674708355e768` | user decision and observed source bytes |
| Error/status code set | existing `ClaimIssueCode` members only; no enum expansion in W2-C1 | protected Wave 1 governance values contract |
| Output schema | existing `AdaptationResult`; event is claim with zero issues, every loss is no claim with exactly one issue | existing application adapter values contract |
| File whitelist | the three exact paths in **Exact implementation whitelist**; package initializer only conditionally | ADMISSION minimum scope |
| Publication boundary | shadow-only; no registry row, runner integration, proposal, publication receipt, or production switch | explicit user decision |

Only an explicit user decision may change an Anchor Ledger entry. Contract revisions may clarify implementation against these anchors but must not alter them.

## Revision State Table

| Revision | Author role reset? | Reviewer role reset? | Verdict | Defect classes found | Repeated? | Anchor drift? |
|---|---:|---:|---|---|---:|---:|
| R1 | yes | yes | `REVISE` | confidence unspecified; pressure/abstain loss semantics unspecified | no | no |
| R2 | yes | yes | `REVISE` | impossible adapter-side malformed-state promise; governance rejection code mapping unspecified | no | no |
| R3 | yes | yes | `REVISE` | public adapter did not reject altered source anchors before catalog validation | no | no |
| R4 | yes | yes | `AUTHORIZATION_REQUIRED` | non-event loss precedence conflicts with altered-source loss precedence; revision round cap reached | no | no |
| R5 | yes | yes | `PASS` | none; explicit precedence decision resolves the final ambiguity | no | no |

## Contract target

Implement exactly one public typed boundary that consumes a concrete `YangMarriageDiscrimination` and an explicit `GovernanceReferenceCatalog`, and returns the existing `AdaptationResult`:

```python
adapt_yang_marriage_discrimination(
    result: YangMarriageDiscrimination,
    catalog: GovernanceReferenceCatalog,
) -> AdaptationResult
```

The function belongs in a dedicated module and must not route through a fabricated legacy `SchoolClaim`.

## Exact implementation whitelist

Implementation authority is not active. If and only if this contract receives fresh PASS and an IMPLEMENT sub-envelope is activated, the allowed files are:

1. Create `engine/application/governance_yang_marriage_adapter.py` solely for the typed adapter and immutable constants required by this contract.
2. Create `tests/application/test_governance_yang_marriage_adapter.py` solely for contract tests.
3. Modify `engine/application/__init__.py` only if an existing package-export convention requires the public function to be exported; otherwise leave it unchanged.

No wildcard paths are allowed. Any need to modify another file is a contract gap and STOP condition.

## Behavior invariants

1. Exact input type and domain ownership: any value whose concrete type is not `YangMarriageDiscrimination` returns one typed `ADAPTER_INPUT_INVALID` loss; no duck typing. A concrete instance is already domain-valid by its constructor contract, so the adapter must not reconstruct it, repeat its A+B/state validation, or catch constructor-time `ValueError` from callers creating malformed instances.
2. Exact identity: emitted claim uses school `yang_qingjuan`, task `marriage.divorce_or_remarriage`, kind `event`, stance `support`, temporal layer `natal`, and evidence grade `inferential`.
3. Three-state conservation and mandatory branch order:
   - inspect the concrete result state before any source-reference construction or catalog validation;
   - `event` with complete discriminator invariants proceeds to exact source and catalog validation and may emit exactly one governance claim;
   - `pressure` terminates immediately with no governance claim and exactly one typed `INSUFFICIENT_EVIDENCE` loss whose detail identifies `pressure` without asserting a negative outcome, regardless of its source refs or catalog contents;
   - `abstain` terminates immediately with no governance claim and exactly one typed `INSUFFICIENT_EVIDENCE` loss whose detail identifies `abstain` and preserves the discriminator blocking reason codes, regardless of its source refs or catalog contents;
   - neither non-event state may be represented as an opposing vote, negative label, unsupported school claim, reference-validation loss, or scored miss.
4. No semantic re-evaluation: the adapter must not count signals, infer A+B, rerun chart logic, reinterpret pressure as weak event evidence, or read chart/features.
5. Exact event source ownership and anchor equality: after and only after state `event` is established, the adapter accepts the event only when the discriminator's canonical `source_rule_refs` equal exactly `("theory/yang/index.yaml#M2-Y-068", "theory/yang/index.yaml#M2-Y-088")`. For an event, missing, additional, substituted, or otherwise altered anchors return exactly one `LEGACY_REFERENCE_INVALID` loss before catalog validation. Only those discriminator-owned exact refs may become source-rule references; no source ref may be invented, dropped, broadened, or converted to a school reason. Non-event states never enter this rule.
6. Exact source version: every source-rule reference uses the non-overridable adapter constant `sha256:e8be77f67246ff056770a35d618b4b3fc5694ba5fdec2f65c8d674708355e768`. Callers provide no source-version parameter. A catalog that lacks this exact version, including one registering the same anchors under another version, produces `LEGACY_REFERENCE_REJECTED`.
7. Exact catalog validation: every reference must be registered by exact category, ID, and version. Unknown or wrong-version references return auditable reference rejection loss.
8. Provenance: adapter ID is stable and Yang-specific; adapter version is `yang-marriage-discrimination/v1`; source claim ref is deterministically derived from the complete canonical discriminator payload, not from Python object identity or runtime hash randomization.
9. Derivation digest: binds at least the discriminator canonical payload, adapter provenance, school, task, kind, stance, temporal layer, evidence grade, source-rule version, and ordered exact source refs. Equivalent fresh-process inputs produce equal digests; any bound identity/version/ref change changes the digest.
10. Claim content: conclusion and falsifier must remain conservative and falsifiable. The adapter must not add `100%`, `必离`, `多婚命`, generalized marriage-quality claims, or timing claims.
11. Confidence: use the explicit contract constant `0.60`, preserving the existing authoritative Yang event-claim boundary. Do not derive confidence from labels, feedback, reports, historical scores, system time, or registry role. The constant must be named and asserted by tests.
12. Fail closed with an exact existing-code mapping:
    - for state `event` only, any `source_rule_refs` tuple not exactly equal to the two frozen canonical anchors—including empty, missing, additional, or substituted refs—returns exactly one `LEGACY_REFERENCE_INVALID` loss before claim construction or catalog validation;
    - for `pressure` or `abstain`, source refs and catalog contents are deliberately not validated and cannot override the mandatory `INSUFFICIENT_EVIDENCE` result;
    - a caught `GovernanceClaimContractError` whose issue code starts with `CLAIM.REFERENCE_` returns exactly one `LEGACY_REFERENCE_REJECTED` loss;
    - every other caught `GovernanceClaimContractError` returns exactly one `LEGACY_CLAIM_REJECTED` loss;
    - the loss detail preserves the governance issue code and diagnostic;
    - no other exception class is caught or converted, so programming defects are not swallowed.
    Empty falsifier and malformed state combinations are rejected when constructing `YangMarriageDiscrimination`; they are not adapter-reachable typed-loss branches for a concrete valid instance. Digest mismatch is tested as input-material sensitivity, not as a runtime comparison against an independently supplied digest.
13. Isolation: the module must not import labels, feedback, reports, learned metrics, evaluation scores, production routing, registry loaders, filesystem APIs, environment variables, network APIs, or system-clock APIs.
14. Determinism: no filesystem read occurs inside the adapter. The content digest is a frozen contract constant; changed source bytes require a new contract/version, not runtime lookup.
15. Shadow-only: the adapter must not edit or load the school registry, publish artifacts, change runner defaults, call production services, set `proposal_allowed`, set `production_switch`, or alter current pipeline behavior.

## Structural and dependency invariants

- Dependency direction is `engine.application` → `engine.decision.yang_marriage` and `engine.governance`; no reverse import is allowed.
- Reuse `AdaptationResult`, typed `ClaimIssue`, `GovernanceClaimSpec`, `build_governance_claim`, and canonical digest utilities where their contracts fit.
- Do not modify `SCHOOL_METADATA_KEYS`, the generic `_spec()`, or `adapt_decision_school_claim()`.
- Do not modify `discriminate_yang_marriage()` or `build_yang_marriage_school_claims()`.
- Do not add capability/certification rows to `theory/multi-school-governance-v1.yaml`.
- Do not integrate the adapter into `run_governance_shadow()` in W2-C1.
- No create-only publication in W2-C1; a successful constructor call is not artifact publication.

## Scope IN

- One typed Yang discrimination-to-governance adaptation boundary.
- Typed losses for non-event states and all fail-closed paths.
- Exact content-addressed rule-reference registration validation.
- Deterministic provenance and derivation binding.
- Focused unit, boundary, isolation, and fresh-process determinism tests.

## Scope OUT (Must NOT have)

- No `GovernanceShadowResult` to `BlindSchoolOutput` adapter.
- No prediction freeze, reveal, labels, scoring, cohort gates, high-risk dual review, or calibration implementation.
- No other-school claim execution or abstention implementation.
- No arbitration-runner, composition, trigger, or pipeline integration.
- No registry capability/certification publication.
- No typed promotion-candidate artifact.
- No production publication receipt, production role change, deployment, or production switch.
- No generic marriage quality, event timing, future-year inference, or remarriage-count prediction.
- No rewrite of legacy V5/claims adapters or existing Yang slice.
- No Git operations and no GitHub service-side mutation.

## Verification selectors and accounting

No verification command is authorized by this contract. After IMPLEMENT and fresh STATIC_REVIEW PASS, VERIFY requires a separate exact test sub-envelope.

Planned focused selectors:

```text
tests/application/test_governance_yang_marriage_adapter.py
tests/yang_marriage/test_domain_model.py
tests/yang_marriage/test_signal_families.py
tests/yang_marriage/test_school_claim_adapter.py
tests/application/test_governance_claim_adapter_boundaries.py
tests/application/test_governance_claim_adapter_derivation.py
```

Static instance accounting method for the new test file:

- enumerate every `test_*` function collected from the file;
- expand parametrized cases from pytest collection output;
- reconcile collected instance count with executed instance count;
- record all deselected, skipped, xfailed, failed, errored, and passed instances separately;
- a collection error supplies zero behavior evidence.

Required behavior partitions in the new test file:

1. concrete event success;
2. pressure always yields `INSUFFICIENT_EVIDENCE`, including altered refs and empty/wrong catalogs;
3. abstain always yields `INSUFFICIENT_EVIDENCE` with preserved blockers, including altered refs and empty/wrong catalogs;
4. wrong concrete input type;
5. missing, additional, or substituted source refs each map to `LEGACY_REFERENCE_INVALID` before catalog validation and emit no claim;
6. either exact frozen anchor missing from the catalog maps to `LEGACY_REFERENCE_REJECTED`;
7. either exact frozen anchor registered only under a wrong catalog version maps to `LEGACY_REFERENCE_REJECTED`;
8. malformed discriminator is rejected by the domain constructor before adapter invocation, while unexpected non-contract exceptions are not swallowed;
9. deterministic same-input replay;
10. fresh-process digest stability;
11. the derivation helper binds ordered source refs, while the public adapter rejects every altered source-ref tuple before claim construction;
12. the frozen source-version constant participates in derivation; callers cannot override it, and wrong catalog registration fails closed;
13. no forbidden imports/static leakage tokens;
14. no registry/pipeline/production side effect;
15. conservative conclusion/falsifier and exact identity assertions.

Tests must assert externally observable contracts and independent expected identities; they must not copy the adapter's digest-building implementation to manufacture expected PASS values.

## Fresh-review questions

1. Is W2-C1 exactly one independently reviewable unit, or does it secretly include registry publication or freeze/scoring work?
2. Can `pressure` or `abstain` reach a `GovernanceClaim`, negative vote, or scoring denominator through any branch?
3. Does the proposed source identity bind both exact rule anchors and the user-approved content SHA-256 without reading the filesystem at runtime?
4. Does the whitelist omit any necessary consumer, or include an unnecessary generic module?
5. Are all adapter-owned contract failures mapped by the exact existing-code table while domain-construction and unexpected programming exceptions remain unmasked?
6. Does fixed confidence `0.60` preserve the existing Yang event-claim behavior without implying empirical calibration?
7. Can any output be mistaken for capability publication, proposal approval, or production authorization?
8. Are the planned tests independent of implementation logic and accountable at parametrized-instance level?

## Falsifiers

The contract must receive `REVISE` if any of the following is true:

- the adapter can be implemented only by changing generic metadata allowlists;
- `pressure` or `abstain` lacks an auditable non-claim representation;
- exact catalog identities cannot be built without runtime filesystem access;
- a stable source claim identity cannot bind the complete discriminator payload;
- implementation requires registry, shadow runner, freeze, scoring, or production changes;
- confidence must be inferred from labels, feedback, historical hit rate, or an unapproved business threshold;
- focused tests cannot distinguish source-ref, source-version, and payload changes;
- an existing public consumer requires behavior changes not listed in the whitelist.

## STOP conditions

Stop and return the appropriate Gate verdict when:

- any requested action may mutate GitHub service-side state (`BLOCKED`);
- any file outside the exact implementation whitelist is required (`REVISE`);
- pre-existing shared-worktree content would be overwritten, reset, cleaned, restored, stashed, committed, or mixed into this unit (`BLOCKED` or `AUTHORIZATION_REQUIRED` as applicable);
- the source YAML bytes differ from the frozen SHA-256 before implementation (`REVISE` and require a new contract decision);
- the discriminator schema or source-rule anchors differ from the observed contract (`REVISE`);
- a second independent target is needed (`REVISE`, return it to ADMISSION);
- a verification selector is missing, duplicated, or fails collection (zero behavior evidence; enter failure routing);
- implementation, testing, local Git, plan writing, Boulder activation, or ledger writing lacks its separate active sub-envelope;
- registry `published`, artifact publication, offline GO, or proposal permission is interpreted as production permission (`BLOCKED`).

## Direct evidence boundary

This draft is supported by observed Wave 1 interfaces, the authoritative Yang three-state implementation and tests, the empty governance registry, existing generic adapter contracts, the current content SHA-256, and offline gate/publication boundaries. It is sufficient only for fresh CONTRACT review.

## Forbidden inference boundary

Do not infer that the adapter exists, tests pass, Wave 2 is active, any capability is published, a promotion candidate is valid, prospective accuracy exists, production is ready, or production switching is authorized. `CONTRACT PASS` would authorize only a separately bounded local IMPLEMENT stage.

## Open questions

- None for W2-C1. Deferred components retain their own future ADMISSION decisions.

## Approval gate

status: contract-pass
verdict: PASS
fresh-review-round: R5
retained-decision: three-state semantics precede source validation; only event validates source refs and catalog registration
directly-proven: the W2-C1 contract is internally consistent, implementable within its exact whitelist, and preserves shadow-only and production-authorization boundaries
forbidden-inference: this PASS does not prove implementation existence, behavior correctness, test success, Wave 2 activation, capability publication, proposal eligibility, or production authorization
unique-next-legal-action: write the complete W2-C1 implementation plan, then obtain a fresh adversarial plan review before any Boulder/ledger activation or implementation
