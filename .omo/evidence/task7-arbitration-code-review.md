# Task 7 Arbitration Final Re-Review

Timestamp: 2026-08-04T08:50:00+08:00

## Scope

Independent read-only re-review of the final Task 7 arbitration product, its Task 5 derivation-identity dependency, three arbitration test modules, and the frozen legacy L6 surface. Only this evidence file was modified.

## Prior Review History

The 2026-08-04 initial review returned `BLOCK` / `REQUEST_CHANGES` for two public-contract defects:

1. `ArbitrationResult.build()` accepted incomplete or unordered seven-gate histories.
2. Same-source grouping had no derivation-chain identity and could over-fold distinct sources.

Both blockers were rechecked against the final implementation rather than accepted from prior claims.

## Re-Review Evidence

- `GovernanceClaimSpec` and `GovernanceClaim` now require exact `DigestRef derivation_chain_digest`; it is included in claim content material (`engine/governance/governance_claim_identity.py:64`, `:92`) and is used by Task 7's `_source_identity()` (`engine/governance/arbitration_gates.py:145`).
- The source identity is also serialized through `EvidenceGroup.source_keys`, which is included in `ArbitrationResult` digest material (`engine/governance/arbitration_trace.py`).
- `ArbitrationResult` invokes `gate_history()` before direct construction or `build()` digesting (`engine/governance/arbitration_result.py:46`). `gate_history()` requires the exact ordered `tuple(GateName)`, partitions every input variant at every gate, and enforces the applicability/decision retained-set relationships (`engine/governance/arbitration_result_validation.py`).
- Recursive nested validation remains in place before gate-history validation. Tests exercise mutable values and `object.__new__` forged/missing nested values, requiring `ArbitrationContractError` rather than an incidental exception.
- Legacy L6 remains untouched: `git diff --quiet -- engine/decision/l6_staged_arbitration.py tests/decision/test_staged_arbitration.py` exited 0.

## Commands And Exits

| Command | Exit | Result |
|---|---:|---|
| `python -m pytest tests/governance/test_governance_claim.py tests/governance/test_arbitration_gates.py tests/governance/test_arbitration_properties.py tests/governance/test_arbitration_contract_boundaries.py -q` | 0 | 37 passed in 1.54s |
| `python -m pytest tests/governance tests/decision/test_staged_arbitration.py -q` | 0 | 148 passed in 20.50s; one pre-existing `pipeline_runner` deprecation warning |
| `python -m ruff check <Task7 final source/tests>` | 0 | all checks passed |
| `python -m ruff format --check <Task7 final source/tests>` | 0 | 12 files already formatted |
| frozen legacy L6 diff check | 0 | no legacy changes |
| direct builder / source-identity Python probe | 0 | all expected reject/group outcomes observed |

## Original Reproductions

| Probe | Observed Final Outcome |
|---|---|
| Build a result with `gates=()` | `empty=rejected` |
| Build a result with the first gate omitted | `missing=rejected` |
| Build a result with eligibility/temporal records swapped | `reordered=rejected` |
| Two claims with one identity but distinct derivation digests | `same_claim_id=True`, `different_content_digest=True`, `derivation_groups=2` |
| Nested forged direct values | covered by `test_arbitration_contract_boundaries.py`; green |

## Findings

### CRITICAL

None.

### HIGH

None.

### MEDIUM

None.

### LOW

- `engine/governance/arbitration_gates.py` remains 240 pure LOC, inside the warning band but below the enforced 250-LOC ceiling. No change is required for this narrow repair.
- No basedpyright project gate is configured/available; this review does not treat Ruff as a type-check substitute.

## Code Quality Status

`PASS`

The final implementation preserves immutable typed values, variant/digest binding, complete source grouping, counterevidence/minority retention, recursive direct integrity, fixed gate history, and old-L6 isolation. The two prior blockers are reproduced as rejected states, not merely covered by a claimed test result.

## Recommendation

`APPROVE`

## Blockers

None.

## Residuals

- The reported deprecation warning originates from the pre-existing `engine.application.pipeline_runner` import path, outside Task 7.
- The workspace has unrelated changes; no product file was modified during this re-review.
