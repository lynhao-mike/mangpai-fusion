# Task14 H3 Scope Adjudication

Date: 2026-08-06 (Asia/Shanghai)
Workspace: `F:\多流派新思路`
Status: `ADJUDICATED_NOT_A_WAVE1_DEFECT`

## Authority Interpretation

Task 7 authority lines 593 and 600 must be applied together:

- Line 593 forbids a **new Wave1 governance path** from converting a partial
  applicability plan into `ApplicabilityPlan.uniform()`.
- Line 600 freezes the pre-existing legacy `arbitrate_staged()` behavior.

Therefore the line-593 invariant governs the new Wave1 entrypoints without
authorizing a semantic change to the line-600 legacy compatibility API. The H3
runtime audit called `engine.decision.l6_staged_arbitration.arbitrate_staged()`
directly. Its observed partial-to-uniform behavior is real and deterministic,
but it belongs to the explicitly frozen legacy surface and is out of scope for
Wave1 defect remediation.

Root authority resolved the apparent conflict explicitly: do not modify
`engine/decision/l6_staged_arbitration.py`; confirm that the new Wave1
governance and shadow entrypoints do not have the fallback path.

## Entrypoint Mapping

| Surface | Public entrypoint | Applicability input | Arbitration implementation | Scope result |
| --- | --- | --- | --- | --- |
| Wave1 governance | `engine.governance.arbitration.arbitrate(arena)` | None | Seven typed governance gates | In scope; no uniform fallback path |
| Wave1 shadow | `run_governance_shadow(request, dependencies)` | No request/dependency field | Builds `ArbitrationArena`, calls Wave1 `arbitrate` | In scope; does not call legacy L6 |
| Legacy staged L6 | `arbitrate_staged(case_id, claims, applicability, ...)` | `ApplicabilityPlan`, route mapping, route plan, or `None` | Legacy `_coerce_plan` | Frozen out-of-scope compatibility behavior |

The Wave1 shadow request fields observed at runtime were exactly:

```text
case_id, raw_payload, chart, calculator_version, school_views, target_year,
feature_vector, fact_conflicts
```

No applicability plan or school-weight input crosses that boundary.

## Source Evidence

Command:

```powershell
rg -n "ApplicabilityPlan|uniform_fallback|arbitrate_staged|l6_staged_arbitration|_coerce_plan" engine/governance engine/application/governance_shadow_runner.py engine/application/governance_shadow_types.py
```

Exit was the expected no-match status, normalized to exit `0`; stdout:

```text
NO_WAVE1_APPLICABILITY_OR_LEGACY_CALL_PATH
```

Positive call-path command:

```powershell
rg -n "from engine\.governance\.arbitration import arbitrate|arbitrate\(|def _arbitration_result|def run_governance_shadow" engine/application/governance_shadow_runner.py
rg -n "def arbitrate\(|class ArbitrationArena|class GovernanceShadowRequest|class GovernanceShadowDependencies" engine/governance engine/application/governance_shadow_types.py -g '*.py'
```

Exit `0`; relevant stdout:

```text
engine/application/governance_shadow_runner.py:27:from engine.governance.arbitration import arbitrate
engine/application/governance_shadow_runner.py:197:def _arbitration_result(
engine/application/governance_shadow_runner.py:211:    return ShadowArbitrationTrace.from_result(arbitrate(arena))
engine/application/governance_shadow_runner.py:214:def run_governance_shadow(
engine/application/governance_shadow_types.py:48:class GovernanceShadowRequest:
engine/application/governance_shadow_types.py:60:class GovernanceShadowDependencies:
engine/governance/arbitration_contracts.py:189:class ArbitrationArena:
engine/governance/arbitration.py:29:def arbitrate(arena: ArbitrationArena) -> ArbitrationResult:
```

Legacy-only positive command:

```powershell
rg -n "def _coerce_plan|ApplicabilityPlan\.uniform\(|return ApplicabilityPlan\.uniform|def arbitrate_staged" engine/decision/l6_staged_arbitration.py
rg -n "test_partial_l1_weights_fall_back_uniform_and_are_marked" tests/decision/test_staged_arbitration.py
```

Exit `0`; stdout:

```text
engine/decision/l6_staged_arbitration.py:215:def _coerce_plan(applicability: Any | None, claims: Sequence[Claim]) -> ApplicabilityPlan:
engine/decision/l6_staged_arbitration.py:217:        return ApplicabilityPlan.uniform()
engine/decision/l6_staged_arbitration.py:227:        return ApplicabilityPlan.uniform()
engine/decision/l6_staged_arbitration.py:535:def arbitrate_staged(
tests/decision/test_staged_arbitration.py:521:def test_partial_l1_weights_fall_back_uniform_and_are_marked() -> None:
```

This isolates `_coerce_plan` and the old expectation to the frozen legacy module
and its legacy compatibility suite.

## Public Runtime Evidence

### Wave1 Shadow Control

A fresh `python -B -` process replaced the imported legacy
`arbitrate_staged()` function with a sentinel that raises if called, then ran
the public shadow entrypoint twice with a valid school view and real dependency
objects. Exit `0`; stdout:

```json
{"decision":"consensus","digest_stable":true,"legacy_calls":[],"request_fields":["case_id","raw_payload","chart","calculator_version","school_views","target_year","feature_vector","fact_conflicts"],"stable":true,"status":"ok","weight_fallback_present":false}
```

```text
wave1_shadow_scope_qa=PASS
```

Semantic success was checked, not inferred from exit code: status was `ok`, the
Wave1 arbitration decision was `consensus`, no legacy call occurred, serialized
output contained no `uniform_fallback`, and two independent runs were equal
with identical digests.

### Frozen Legacy Characterization

A second fresh `python -B -` process replayed the exact full/partial/post matrix
through the legacy public API. Exit `0`; stdout:

```json
{"full":{"oppose":0.1,"result":"conflict_resolved","source":"l1_capability","support":0.9,"winners":["known"]},"partial":{"oppose":1.0,"result":"unresolved","source":"uniform_fallback","support":1.0,"winners":[]},"post":{"oppose":0.1,"result":"conflict_resolved","source":"l1_capability","support":0.9,"winners":["known"]},"stale":false,"surface":"frozen_legacy"}
```

```text
legacy_compatibility_characterization=PASS
```

This confirms the H3 audit observation while attributing it to the correct
surface. The identical full/post controls refute stale state.

## Focused Verification

Command:

```powershell
python -m pytest tests/governance/test_arbitration_gates.py tests/governance/test_arbitration_properties.py tests/application/test_governance_shadow_runner.py -q
```

Exit `0`; stdout:

```text
29 passed in 1.12s
```

No failing-first test or red-green transition applies because authority forbade
a product semantic change and the adjudicated Wave1 path is already correct.

## Changes and Cleanup

- Product files changed: none.
- Test files changed: none.
- Legacy files changed: none.
- No reset, revert, stash, checkout, deletion of repository data, debugger
  attach, server, port, environment override, or background process was used.
- The temporary debug journal and its local exclude entry were removed after
  evidence capture.
- Fresh Python processes exited normally; no owned Python/pytest process was
  left running.
- This evidence file is the only retained Task14 H3 adjudication artifact.

## Residual Risk

The legacy API still intentionally converts partial applicability data to a
uniform fallback because line 600 freezes that compatibility behavior. Any
future request to change it requires explicit authority to revise the legacy
contract and its locked test. It is not reachable from the reviewed Wave1
governance/shadow call path.
