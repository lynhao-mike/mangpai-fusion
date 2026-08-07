# Task14 H3 scope adjudication independent gate

Date: 2026-08-06

## Verdict

**CONFIRMED** (confidence: **0.99**): the observed legacy
`engine.decision.l6_staged_arbitration._coerce_plan` partial-to-uniform behavior
is real, but it is **not a Wave1 blocker** under the paired Task7 authority. No
Wave1 product/test fix is required.

This verdict confirms the scope adjudication, not the desirability of the legacy
behavior. The legacy compatibility surface continues to expose
`uniform_fallback`; the independently tested Wave1 governance and shadow surfaces
do not accept an applicability plan, do not call the legacy arbitration function,
do not call `ApplicabilityPlan.uniform()`, and do not serialize a uniform marker.

## Authority reasoning

Task7 lines 593 and 600 must be applied together:

```text
593: no path from a partial plan may fall back to ApplicabilityPlan.uniform()
599: do not reuse legacy _weighted_sides accumulation as the new vote model
600: old arbitrate_staged() remains unchanged
```

Line 593 is a required property of the new Task7 seven-gate governance
arbitration. Line 600 explicitly withholds authority to change the pre-existing
`engine.decision.l6_staged_arbitration.arbitrate_staged()` compatibility API.
Reading line 593 as an order to change `_coerce_plan` would directly contradict
line 600 and the implementation instruction at line 599.

Task11 lines 710-741 define a new shadow runner:

- it builds facts, adapts claims, executes the seven-step arbitration, and returns
  a serializable shadow result;
- it is orchestration-only and receives explicit inputs/read-only registries;
- it does not change `run_decision_mvp()` or V5 default output.

Thus the scope boundary is:

| Surface | Entrypoint | Arbitration | Applicability/weight input | Authority result |
| --- | --- | --- | --- | --- |
| Wave1 new governance | `engine.governance.arbitration.arbitrate` | seven typed gates | none | line 593 applies |
| Wave1 shadow | `run_governance_shadow` | constructs `ArbitrationArena`, calls new `arbitrate` | none | line 593 applies |
| Legacy staged L6 | `arbitrate_staged` | legacy `_coerce_plan` and weighted sides | explicit plan | frozen by line 600 |

The original H3 audit correctly characterized the legacy runtime behavior but
called the legacy public API directly. That evidence does not establish
reachability from the Wave1 entrypoints.

## Source entrypoint mapping

Exact negative search:

```powershell
rg -n "ApplicabilityPlan|uniform_fallback|arbitrate_staged|l6_staged_arbitration|_coerce_plan" engine/governance engine/application/governance_shadow_runner.py engine/application/governance_shadow_types.py; if($LASTEXITCODE -eq 1){'NO_WAVE1_APPLICABILITY_OR_LEGACY_CALL_PATH';exit 0}
```

Result: exit 0, `NO_WAVE1_APPLICABILITY_OR_LEGACY_CALL_PATH`.

Exact positive Wave1 mapping:

```powershell
rg -n "from engine\.governance\.arbitration import arbitrate|arbitrate\(|def _arbitration_result|def run_governance_shadow" engine/application/governance_shadow_runner.py
rg -n "def arbitrate\(|class ArbitrationArena|class GovernanceShadowRequest|class GovernanceShadowDependencies" engine/governance engine/application/governance_shadow_types.py -g '*.py'
```

Relevant result:

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

Exact legacy-only mapping:

```powershell
rg -n "def _coerce_plan|ApplicabilityPlan\.uniform\(|return ApplicabilityPlan\.uniform|def arbitrate_staged" engine/decision/l6_staged_arbitration.py
rg -n "test_partial_l1_weights_fall_back_uniform_and_are_marked" tests/decision/test_staged_arbitration.py
```

Result:

```text
engine/decision/l6_staged_arbitration.py:215:def _coerce_plan(...)
engine/decision/l6_staged_arbitration.py:217:        return ApplicabilityPlan.uniform()
engine/decision/l6_staged_arbitration.py:227:        return ApplicabilityPlan.uniform()
engine/decision/l6_staged_arbitration.py:535:def arbitrate_staged(...)
tests/decision/test_staged_arbitration.py:521:def test_partial_l1_weights_fall_back_uniform_and_are_marked()
```

The fallback and its locked characterization are isolated to the legacy surface.

## Independent runtime reproduction

The fresh process imported the legacy module first, replaced both
`arbitrate_staged` and `ApplicabilityPlan.uniform` with raising spies, then used
the real public Wave1 shadow entrypoint twice. It also invoked the public new
`engine.governance.arbitration.arbitrate` twice. It compared typed semantics,
result equality, digests, serialized uniform markers, spy calls, and dataclass
boundary fields.

Exact command:

```powershell
@'
import json,runpy
from dataclasses import asdict,fields
import engine.decision.l6_staged_arbitration as legacy
legacy_calls=[];uniform_calls=[]
def legacy_spy(*args,**kwargs):
 legacy_calls.append({'args':len(args),'kwargs':sorted(kwargs)});raise AssertionError('legacy arbitrate_staged reached from Wave1')
def uniform_spy(cls):
 uniform_calls.append('uniform');raise AssertionError('legacy ApplicabilityPlan.uniform reached from Wave1')
legacy.arbitrate_staged=legacy_spy;legacy.ApplicabilityPlan.uniform=classmethod(uniform_spy)
shadow=runpy.run_path('tests/application/test_governance_shadow_runner.py')
request=shadow['_request'](shadow['SchoolViewOutcome']('ziping',(shadow['_legacy_claim']('ziping','reason:ziping'),)))
dependencies=shadow['_dependencies']();first=shadow['run_governance_shadow'](request,dependencies);second=shadow['run_governance_shadow'](request,dependencies)
shadow_serialized=json.dumps(first.to_canonical(),default=str,sort_keys=True)
gov=runpy.run_path('tests/governance/test_arbitration_gates.py');direct_first=gov['arbitrate'](gov['_arena'](gov['_claim']()));direct_second=gov['arbitrate'](gov['_arena'](gov['_claim']()))
direct_serialized=json.dumps(asdict(direct_first),default=str,sort_keys=True)
print(json.dumps({'shadow':{'status':first.status,'decision':first.arbitration.decision if first.arbitration else None,'digest':first.result_digest,'digest_stable':first.result_digest==second.result_digest,'canonical_stable':first.to_canonical()==second.to_canonical(),'uniform_marker':'uniform_fallback' in shadow_serialized},'direct':{'decision':direct_first.decision.value,'digest':direct_first.content_digest.value,'digest_stable':direct_first.content_digest==direct_second.content_digest,'result_stable':direct_first==direct_second,'uniform_marker':'uniform_fallback' in direct_serialized},'legacy_calls':legacy_calls,'legacy_uniform_calls':uniform_calls,'shadow_request_fields':[f.name for f in fields(shadow['GovernanceShadowRequest'])],'shadow_dependency_fields':[f.name for f in fields(shadow['GovernanceShadowDependencies'])]},sort_keys=True))
'@|python -B -
```

Result: exit 0.

```json
{"direct":{"decision":"consensus","digest":"1ce194959fcf252fa3b3e6cbe2d6e50390cbee4cfdd9677a5eb732ca21e7c4cf","digest_stable":true,"result_stable":true,"uniform_marker":false},"legacy_calls":[],"legacy_uniform_calls":[],"shadow":{"canonical_stable":true,"decision":"consensus","digest":"605c74a8111a9ae11bc02a0354dcdd852f0bf4e5d7682cd079c55c60e7c83979","digest_stable":true,"status":"ok","uniform_marker":false},"shadow_dependency_fields":["reference_catalog","school_registry","certification_registry","capability_version","trigger_registry","trigger_requests","composition_registry","composition_requests"],"shadow_request_fields":["case_id","raw_payload","chart","calculator_version","school_views","target_year","feature_vector","fact_conflicts"]}
```

Semantic conclusions:

- Shadow: `ok/consensus`, stable canonical value and digest.
- New governance API: `consensus`, stable result and digest.
- Legacy arbitration spy calls: zero.
- Legacy uniform spy calls: zero.
- Serialized `uniform_fallback` markers: zero on both surfaces.
- Request/dependency fields: no applicability plan, school weight, or fallback
  source can cross the public shadow boundary.

The first version of this probe reached the Wave1 results without tripping either
spy but attempted nonexistent `ArbitrationResult.to_canonical()`. The corrected
observation uses dataclass serialization and direct result equality. No product or
test edit was involved.

## Focused verification

Exact command:

```powershell
python -m pytest tests/governance/test_arbitration_gates.py tests/governance/test_arbitration_properties.py tests/application/test_governance_shadow_runner.py -q
```

Result: exit 0, `29 passed in 1.49s`.

## Cleanup and retained risk

- Process probe: `NO_H3_SCOPE_PYTHON_OR_PYTEST_PROCESSES`.
- Temp probe: `NO_H3_SCOPE_TEMP_ARTIFACTS`.
- Product/test files were not edited.
- No repository data was reset, reverted, stashed, checked out, or deleted.
- Existing untracked Wave1 files were left untouched.
- The only retained write from this gate is this evidence file.

Residual risk is explicit and out of scope: legacy `arbitrate_staged()` continues
to convert partial applicability data to uniform fallback. Changing that behavior
would require new authority to revise line 600's compatibility freeze and its
existing test. It is not reachable from the reviewed Wave1 governance/shadow path.
