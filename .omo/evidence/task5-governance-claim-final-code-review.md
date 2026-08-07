# Task5 Governance Claim Final Re-Review

codeQualityStatus: BLOCK
recommendation: REQUEST_CHANGES

## Skill-Perspective Check

- `omo:remove-ai-slops` consulted: yes, reloaded for final review.
- `omo:programming` consulted: yes, reloaded with Python README and code-smells reference.
- Skill verdict: no broad catch was introduced and targeted tests are relevant, but one production invariant still violates the programming/remove-ai-slops expectation that public typed constructors enforce their own contract rather than relying on caller discipline.

## CRITICAL

- None.

## HIGH

1. Public `GovernanceClaim` construction still permits same digest with different public `specification` content.
   - References: `engine/governance/governance_claim.py:73`, `engine/governance/governance_claim.py:90`, `engine/governance/governance_claim_identity.py:81`, `engine/governance/governance_claim_identity.py:82`.
   - Builder path now stores `canonical_spec` and passes the prior duplicate-ref repro. However, `GovernanceClaim` is publicly exported and its `__post_init__` digest check still computes `content_material(content_from_claim(self))`; `content_material()` includes only `identity_material(content.specification)`, then the top-level ref fields. It does not include or compare `specification.public_fact_refs` / `certified_fact_refs` / `school_reason_refs` / `source_rule_refs` / `blockers` / `counterevidence` against the top-level canonical fields.
   - Minimal repro run in review: directly constructing `GovernanceClaim` with `specification.public_fact_refs=(fact, fact)` and top-level `public_fact_refs=(fact,)` was accepted with the same digest material. Output: `accepted ... (fact, fact) (fact,)`.
   - Why this blocks: the requested final invariant was “identity/digest与公开 spec同源，不存在同 digest不同 public content.” That is still false for the public envelope constructor, even though `build_governance_claim()` now normalizes correctly.

## MEDIUM

- `engine/application/governance_claim_adapters.py:50` maps any `GovernanceClaimContractError` to `LEGACY_REFERENCE_REJECTED`. This satisfies the requested no-broad-catch shape for catalog failures, and the original issue detail is preserved, but non-reference core errors such as `CLAIM.CONFIDENCE` would also be labeled as reference rejected. Not blocking for the specifically requested catalog-rejection repair, but worth tightening later if adapter issue taxonomy matters.

## LOW

- LOC warning band remains but no file exceeds 250 pure LOC: `engine/governance/governance_claim.py=245`, `engine/application/governance_claim_adapters.py=222`.
- Tests now cover builder-level canonical specification normalization and adapter catalog rejection, but they do not cover direct public `GovernanceClaim` construction invariants.

## Verification

- `python -m pytest tests/governance/test_governance_claim.py tests/application/test_governance_claim_adapters.py tests/application/test_governance_claim_adapter_boundaries.py tests/yang_marriage/test_static_isolation.py -q`: PASS, 29 passed, 1 pre-existing deprecation warning.
- `python -m ruff check <Task5 files>`: PASS.
- `python -m ruff format --check <Task5 files>`: PASS.
- `scripts/python/check-no-excuse-rules.py`: unavailable at repo path; not run.
- Minimal probes:
  - builder duplicate-ref path: PASS, same id/digest/envelope and canonical spec refs.
  - adapter empty-catalog path: PASS, typed `LEGACY_REFERENCE_REJECTED` with original `CLAIM.REFERENCE_UNKNOWN` detail.
  - direct public constructor invariant: FAIL, accepted divergent public spec/top-level refs under the same digest.

## Blockers

- Add constructor-level enforcement that the public `specification` and top-level canonical fields are same-source, or make direct `GovernanceClaim` construction impossible/unsupported. The current exported dataclass still permits same digest with different public content.
