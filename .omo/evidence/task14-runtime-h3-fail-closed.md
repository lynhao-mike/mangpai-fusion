# Task14 H3 fail-closed runtime audit

Date: 2026-08-06

## Overall verdict

**H3 CONFIRMED**.

The confirmation is specific: a partial task-scoped L1 weight plan is silently
converted to `ApplicabilityPlan.uniform()`. This changes provenance from
`l1_capability` to `uniform_fallback` and changes an arbitrated
`conflict_resolved` winner into `unresolved` with equal 1.0/1.0 support. The
post-adversarial valid control is identical to the first valid control, so this is
not stale state.

The other requested permissiveness/inference hypotheses are refuted by fresh
public-API runs. Exit code 0 was never treated as sufficient; every verdict below
uses returned semantic state, typed issue/error, arbitration state, and source or
provenance.

| Hypothesis under audit | Verdict | Runtime semantic result |
| --- | --- | --- |
| Unknown trigger is allowed to activate | **REFUTED** | inactive, typed `unknown_trigger` |
| Unregistered capability/school-task is accepted or arbitrated | **REFUTED** | capability `abstain`; school-task `unsupported`; unknown school typed construction error |
| Missing explicit year is inferred from current year/as-of/captured time | **REFUTED** | no liunian fact; trigger inactive with `missing_required_fact` |
| Global school weights are consumed as production task weights | **REFUTED** | empty global prior is `unsupported`; flat global weights reject before arbitration |
| Partial task weights remain partial or fail closed | **CONFIRMED defect** | silently becomes `uniform_fallback` and is arbitrated |

## H1 unknown trigger

Valid control: registered `synthetic.natal-present` with its declared natal fact.
Adversarial input: unregistered `synthetic.unknown` with the same valid snapshot.

Exact command:

```powershell
@'
import json,runpy
from engine.governance import TemporalLayer,TemporalScope
from engine.governance.trigger_registry import TriggerEvaluationContext,evaluate_governance_trigger
ns=runpy.run_path('tests/governance/test_trigger_registry.py'); registry=ns['_published_registry']()
def out(x):return {'active':x.active,'issues':[i.value for i in x.issues]}
known=evaluate_governance_trigger(registry,'synthetic.natal-present',ns['_snapshot'](ns['_fact']('chart.natal')),TriggerEvaluationContext())
unknown=evaluate_governance_trigger(registry,'synthetic.unknown',ns['_snapshot'](ns['_fact']('chart.natal')),TriggerEvaluationContext())
missing=evaluate_governance_trigger(registry,'synthetic.liunian-target',ns['_snapshot'](ns['_fact']('chart.natal')),TriggerEvaluationContext(as_of_date='2099-12-31',parsed_present=True))
explicit=evaluate_governance_trigger(registry,'synthetic.liunian-target',ns['_snapshot'](ns['_fact']('chart.liunian',TemporalScope(TemporalLayer.LIUNIAN,target_year=2026),('year','2026'))),TriggerEvaluationContext(as_of_date='1999-01-01'))
print(json.dumps({'known_control':out(known),'unknown_adversarial':out(unknown),'missing_year_adversarial':out(missing),'explicit_year_control':out(explicit)},sort_keys=True))
'@|python -B -
```

Result: exit 0.

```json
{"explicit_year_control":{"active":true,"issues":[]},"known_control":{"active":true,"issues":[]},"missing_year_adversarial":{"active":false,"issues":["missing_required_fact"]},"unknown_adversarial":{"active":false,"issues":["unknown_trigger"]}}
```

Verdict: **unknown-trigger permissiveness REFUTED**. The valid control activates;
the adversarial trigger is inactive with closed issue provenance.

## H2 unregistered capability and school-task

### Governance capability/arbitration

Valid control: exact published Ziping capability. Adversarial inputs: canonical
peer `gao_dechen` without the exact capability and noncanonical school `intruder`.

Exact command:

```powershell
@'
import json,runpy
from engine.governance.arbitration import arbitrate
from engine.governance.governance_claim_values import GovernanceClaimContractError
ns=runpy.run_path('tests/governance/test_arbitration_gates.py')
def out(r):return {'decision':r.decision.value,'retained':list(r.retained_claim_ids),'applicable':list(r.applicable_claim_ids),'audits':[{'gate':a.gate.value,'issue':a.issue_code.value} for a in r.audits]}
valid=arbitrate(ns['_arena'](ns['_claim']())); unregistered=arbitrate(ns['_arena'](ns['_claim'](school='gao_dechen')))
try:ns['_claim'](school='intruder')
except GovernanceClaimContractError as e:unknown={'accepted':False,'error_type':type(e).__name__,'issue_code':e.issue_code,'field_path':e.field_path,'diagnostic':e.diagnostic}
else:unknown={'accepted':True}
print(json.dumps({'valid_control':out(valid),'unregistered_capability':out(unregistered),'unknown_school':unknown},sort_keys=True))
'@|python -B -
```

Result: exit 0.

```json
{"unknown_school":{"accepted":false,"diagnostic":"school ID must be canonical","error_type":"GovernanceClaimContractError","field_path":"school_id","issue_code":"CLAIM.SCHOOL_ID"},"unregistered_capability":{"applicable":[],"audits":[{"gate":"applicability","issue":"ARBITRATION.CAPABILITY_ABSTAIN"}],"decision":"abstain","retained":[]},"valid_control":{"applicable":["governance_claim:6ef9df1ef701a5193e9a6ccee4317e337e6013a1da1b27e492d2a8ddde436275"],"audits":[],"decision":"consensus","retained":["governance_claim:6ef9df1ef701a5193e9a6ccee4317e337e6013a1da1b27e492d2a8ddde436275"]}}
```

The exact capability reaches `consensus`. The unregistered capability reaches the
applicability gate but produces typed `ARBITRATION.CAPABILITY_ABSTAIN`, no
applicable claim, and `abstain`. The unknown school is rejected even earlier by
typed `GovernanceClaimContractError/CLAIM.SCHOOL_ID`.

### Public school-task orchestrator

Exact command:

```powershell
@'
import json,runpy
from engine.claims.orchestrator import generate_blind_outputs
ns=runpy.run_path('tests/claims/test_runner_registry.py')
rows=generate_blind_outputs(ns['_chart'](),[ns['_task']('structure.overview'),ns['_task']('unregistered.task')],case_id='C-H3-SCHOOL-TASK',schools=['ziping'])
print(json.dumps([{'school':r.school_id,'task':r.task_id,'state':r.state,'prediction_count':len(r.predictions),'rationale':r.rationale} for r in rows],sort_keys=True))
'@|python -B -
```

Result: exit 0.

```json
[{"prediction_count":1,"school":"ziping","state":"claim","task":"structure.overview"},{"prediction_count":0,"rationale":"no independent L2 claim generator is registered for this school","school":"ziping","state":"unsupported","task":"unregistered.task"}]
```

Verdict: **unregistered capability/school-task permissiveness REFUTED**. The valid
task returns a real claim; the adversarial task is explicitly `unsupported`, has
zero predictions, and never masquerades as accepted/production output.

## H3 missing explicit year/current-year inference

The trigger contrast is included in H1. A direct fact-builder contrast also used
a future `captured_at=2099-12-31T23:59:59+08:00` so neither wall clock nor payload
timestamp could silently supply a target year.

Exact command:

```powershell
@'
import json,runpy
from dataclasses import replace
ns=runpy.run_path('tests/application/test_governance_fact_builder.py'); raw=replace(ns['_raw'](),captured_at='2099-12-31T23:59:59+08:00')
def out(s):return {'fact_kinds':[f.fact_kind for f in s.facts],'liunian_targets':[f.temporal_scope.target_year for f in s.facts if f.fact_kind=='chart.liunian'],'digest':s.content_digest.value}
print(json.dumps({'missing_year_adversarial':out(ns['_build'](target_year=None,raw_payload=raw)),'explicit_year_control':out(ns['_build'](target_year=2026,raw_payload=raw))},sort_keys=True))
'@|python -B -
```

Result: exit 0.

```json
{"explicit_year_control":{"digest":"1c2aa74160aa5db9eb8d3eca7a7da4d8824a9853e38c2a06bb7159effc2b63e0","fact_kinds":["chart.sex_marker","chart.liunian","chart.dayun","chart.four_pillars"],"liunian_targets":[2026]},"missing_year_adversarial":{"digest":"bf0d84d986d19f94b158b40a60a66c7f4e355de2a0dfca273a9d0d30bb88e206","fact_kinds":["chart.sex_marker","chart.dayun","chart.four_pillars"],"liunian_targets":[]}}
```

Verdict: **current-year inference REFUTED**. Only the explicit control produces
`chart.liunian` and a target-year provenance value.

## H4 global school weight injection

### L1 global prior

An exact task-scoped posterior became the primary route. An empty capability
snapshot returned a `global_prior`, but it remained unsupported and insufficient.

```json
{"global_prior_adversarial":{"mean":0.5,"n_eff":0.0,"primary":[],"shrink_level":"global_prior","status":"insufficient","unsupported":["ziping"]},"task_scoped_control":{"mean":0.82,"n_eff":10.0,"primary":["ziping"],"shrink_level":"exact","status":"sufficient","unsupported":[]}}
```

### Direct L6 injection

Exact command used the public `ApplicabilityPlan` and `arbitrate_staged` APIs with
the same two opposing claims and explicit conflict rule:

```powershell
@'
import json,runpy
from engine.decision.l6_staged_arbitration import ApplicabilityPlan,ConflictRule,ConflictRuleSet,arbitrate_staged
ns=runpy.run_path('tests/decision/test_staged_arbitration.py')
claims=[ns['_claim']('known',school_id='ziping',claim_type='structure_claim',task_id='strength',domain='overall',polarity='positive'),ns['_claim']('missing',school_id='ditiansui',claim_type='structure_claim',task_id='strength',domain='overall',polarity='negative')];rules=ConflictRuleSet((ConflictRule('CR-H3','structure','polarity_opposition','structure_claim','capability_weighted',0.15,'fixture'),))
def run(plan):
 r=arbitrate_staged('C-H3',claims,plan,conflict_rules=rules);d=r.stage('structure');return {'source':r.weight_source,'result':d.result,'winners':list(d.winner_claim_ids),'minority':list(d.minority_claim_ids),'support':d.weighted_support,'oppose':d.weighted_oppose}
control=run(ApplicabilityPlan({'strength':{'ziping':0.9,'ditiansui':0.1}}))
try:flat=ApplicabilityPlan({'ziping':0.9,'ditiansui':0.1})
except Exception as e:flat_result={'accepted':False,'error_type':type(e).__name__,'message':str(e),'arbitrated':False}
else:flat_result={'accepted':True,'arbitrated':True,'result':run(flat)}
nested=run(ApplicabilityPlan({'global':{'ziping':0.9,'ditiansui':0.1}}))
print(json.dumps({'task_scoped_control':control,'flat_global_adversarial':flat_result,'nested_global_adversarial':nested},sort_keys=True))
'@|python -B -
```

Result: exit 0.

```json
{"flat_global_adversarial":{"accepted":false,"arbitrated":false,"error_type":"AttributeError","message":"'float' object has no attribute 'items'"},"nested_global_adversarial":{"minority":["known","missing"],"oppose":1.0,"result":"unresolved","source":"uniform_fallback","support":1.0,"winners":[]},"task_scoped_control":{"minority":["missing"],"oppose":0.1,"result":"conflict_resolved","source":"l1_capability","support":0.9,"winners":["known"]}}
```

Verdict: **direct global-weight consumption REFUTED**. Flat global weights do not
reach arbitration, although the exposed `AttributeError` is not a typed contract
error. A nested `global` scope is accepted as a task-shaped mapping but is not
consumed as global weights; it falls into the separately confirmed partial/missing
route and becomes uniform. No result reports global provenance.

## H5 partial weights to uniform fallback

Valid control: both schools have explicit `strength` weights 0.9/0.1.
Adversarial input: only Ziping has an explicit weight. Post-control: repeat the
complete plan after the adversarial run.

Exact command:

```powershell
@'
import json,runpy
from engine.decision.l6_staged_arbitration import ApplicabilityPlan,ConflictRule,ConflictRuleSet,arbitrate_staged
ns=runpy.run_path('tests/decision/test_staged_arbitration.py')
claims=[ns['_claim']('known',school_id='ziping',claim_type='structure_claim',task_id='strength',domain='overall',polarity='positive'),ns['_claim']('missing',school_id='ditiansui',claim_type='structure_claim',task_id='strength',domain='overall',polarity='negative')];rules=ConflictRuleSet((ConflictRule('CR-PARTIAL','structure','polarity_opposition','structure_claim','capability_weighted',0.15,'fixture'),))
def run(plan):
 r=arbitrate_staged('C-H3-PARTIAL',claims,plan,conflict_rules=rules);d=r.stage('structure');return {'source':r.weight_source,'result':d.result,'winners':list(d.winner_claim_ids),'minority':list(d.minority_claim_ids),'support':d.weighted_support,'oppose':d.weighted_oppose,'rule':d.resolution_rule_id}
full=run(ApplicabilityPlan({'strength':{'ziping':0.9,'ditiansui':0.1}}));partial=run(ApplicabilityPlan({'strength':{'ziping':0.9}}));post=run(ApplicabilityPlan({'strength':{'ziping':0.9,'ditiansui':0.1}}))
print(json.dumps({'full_control':full,'partial_adversarial':partial,'post_control':post,'stale':full!=post},sort_keys=True))
'@|python -B -
```

Result: exit 0.

```json
{"full_control":{"minority":["missing"],"oppose":0.1,"result":"conflict_resolved","rule":"CR-PARTIAL","source":"l1_capability","support":0.9,"winners":["known"]},"partial_adversarial":{"minority":["known","missing"],"oppose":1.0,"result":"unresolved","rule":"CR-PARTIAL","source":"uniform_fallback","support":1.0,"winners":[]},"post_control":{"minority":["missing"],"oppose":0.1,"result":"conflict_resolved","rule":"CR-PARTIAL","source":"l1_capability","support":0.9,"winners":["known"]},"stale":false}
```

Verdict: **partial-to-uniform fallback CONFIRMED**. The adversarial plan is not
rejected or marked partial; it is accepted, re-provenanced as uniform, and
arbitrated. This directly contradicts the Task7 invariant that no path from a
partial plan may fall back to `ApplicabilityPlan.uniform()`.

## Focused regressions

Exact command:

```powershell
python -m pytest tests/governance/test_trigger_registry.py tests/governance/test_school_registry.py tests/governance/test_arbitration_gates.py tests/application/test_governance_fact_builder.py tests/claims/test_runner_registry.py tests/decision/test_capability_registry.py tests/decision/test_learnable_routing.py tests/decision/test_staged_arbitration.py tests/application/test_staged_learning_integration.py -q
```

Result: exit 0, `115 passed, 1 warning in 4.64s`. The warning is the pre-existing
`dual_engine_adapter` deprecation. The green suite does not refute the finding:
`test_partial_l1_weights_fall_back_uniform_and_are_marked` currently codifies the
behavior that conflicts with the Task7 authority.

## Harness corrections and semantic-success check

Two earlier observation harnesses exited nonzero because the serializer guessed
`ClaimAudit.issue` instead of `ClaimAudit.issue_code`, and
`BlindSchoolOutput.prediction` instead of `predictions`. Corrected public-API
probes above exited 0 and printed the complete semantic fields. No product or test
change was made. The final verdict relies on `active`, `issues`, `state`,
`prediction_count`, `decision`, `applicable`, `audit gate/issue`, `fact_kinds`,
`liunian_targets`, `shrink_level`, `weight_source`, weighted support, winners, and
stale-control equality, not process success alone.

## Cleanup

- Process probe: `NO_H3_PYTHON_OR_PYTEST_PROCESSES`.
- Temp probe: `NO_H3_TEMP_ARTIFACTS`.
- No temporary fixture, debugger, server, port, or environment override remains.
- Product and test files were not edited.
- No repository data was reset, reverted, stashed, checked out, or deleted.
- Existing untracked product files were left untouched.
- The only H3 audit write is this evidence file.
