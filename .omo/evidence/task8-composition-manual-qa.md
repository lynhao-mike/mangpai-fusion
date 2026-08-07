# Task 8 Composition Manual QA

Date: 2026-08-04  
Surface: Python public API, invoked from the repository root with PowerShell here-string piped to `python -`.  
Scope: Task8 constrained composition, legacy registry-loader compatibility, and old arbitration behavior. Product code was not modified.

## Command Evidence

Exact executed surface command shape:

```powershell
$before = @(Get-Process python,python3 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
$code = @'
# embedded bounded Python public-API harness:
# imports engine.governance.composition, legacy loaders, and arbitration public APIs;
# creates only TemporaryDirectory YAML copies; asserts 16 scenarios; prints manualQa JSON.
'@
$code | python -
$ec = $LASTEXITCODE
$after = @(Get-Process python,python3 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
$newResidual = @($after | Where-Object { $before -notcontains $_ })
Write-Output ("PROCESS_BEFORE=" + (($before | Sort-Object) -join ','))
Write-Output ("PROCESS_AFTER=" + (($after | Sort-Object) -join ','))
Write-Output ("NEW_PYTHON_RESIDUAL=" + (($newResidual | Sort-Object) -join ','))
Write-Output ("EXIT_CODE=" + $ec)
exit $ec
```

Final run result:

```text
pass_count=16
fail_count=0
PROCESS_BEFORE=25688
PROCESS_AFTER=25688
NEW_PYTHON_RESIDUAL=
EXIT_CODE=0
```

One earlier harness attempt exited `1` because the QA script read `FactCertificationRegistry.certifications`; the actual public field is `registrations`. That was a QA-script defect, not a product assertion failure. It also left no new Python process: `PROCESS_BEFORE=25688`, `PROCESS_AFTER=25688`, `NEW_PYTHON_RESIDUAL=`.

## manualQa

### surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | verdict | artifactRefs |
| --- | --- | --- | --- | --- | --- |
| S01 | formal template count/status | Python public API | `load_composition_registry(Path("theory/multi-school-governance-v1.yaml"))` | PASS: `1 synthetic_only synthetic.structure-consensus/1.0.0` | A1 |
| S02 | shadow valid | Python public API | `execute_composition(..., mode=CompositionExecutionMode.SHADOW)` with `ziping` + `gao_dechen` | PASS: `composed/structure/corroborated` | A1 |
| S03 | duplicate conditional | Python public API | `execute_composition(..., components=(ziping, ziping), mode=SHADOW)` | PASS: `conditional/COMPOSITION.INDEPENDENT_COMPONENTS_REQUIRED` | A1 |
| S04 | production forbidden | Python public API | `execute_composition(..., mode=CompositionExecutionMode.PRODUCTION)` | PASS: `unsupported/COMPOSITION.PRODUCTION_FORBIDDEN` | A1 |
| S05 | unknown id/version | Python public API | `execute_composition(..., template_id="synthetic.unknown")` and `version="9.9.9"` | PASS: both `unsupported/COMPOSITION.UNSUPPORTED_TEMPLATE` | A1 |
| S06 | missing required component | Python public API | `execute_composition(..., components=(ziping,), mode=SHADOW)` | PASS: `conditional/COMPOSITION.COMPONENTS_REQUIRED` | A1 |
| S07 | kind conflict | Python public API | `execute_composition(..., components=(structure claim, event claim), mode=SHADOW)` | PASS: `conflict/COMPOSITION.CLAIM_KIND_INCOMPATIBLE` | A1 |
| S08 | temporal conflict | Python public API | `execute_composition(..., natal + liunian target_year=2026, mode=SHADOW)` | PASS: `conflict/COMPOSITION.TEMPORAL_INCOMPATIBLE` | A1 |
| S09 | contradiction human_review | Python public API | `execute_composition(..., support + oppose, mode=SHADOW)` | PASS: `human_review/COMPOSITION.STRONG_CONTRADICTION` | A1 |
| S10 | permutation digest | Python public API | `execute_composition(...)` over both permutations of the same two claims | PASS: one digest, canonical claim-id order retained | A1 |
| S11 | evidence cap | Python public API | direct-grade components under formal template cap | PASS: output evidence grade `corroborated` | A1 |
| S12 | component/counterevidence/falsifier retention | Python public API | component with `counter` fact ref and explicit falsifier composed with second school | PASS: component ids, counterevidence, and falsifier retained | A1 |
| S13 | forged digests | Python public API | direct `CompositionResult(...)` with forged digest and `replace(template, specification_digest=...)` | PASS: `COMPOSITION.RESULT_DIGEST`; `COMPOSITION.DIGEST` | A1 |
| S14 | raw enum boundary | Python public API | `replace(template, output_kind="structure")`; `replace(template, evidence_cap="corroborated")` | PASS: typed `CompositionContractError`, no raw `AttributeError` | A1 |
| S15 | valid YAML + forbidden dynamic fields + duplicate key | Python public API | temp copied registry via `load_composition_registry(Path("theory/registry.yaml"), workspace_root=temp)` | PASS: valid copy loads; `callback/expression/predicate/module_path` reject as `COMPOSITION.YAML_FIELDS`; duplicate `version` rejects as `COMPOSITION.YAML_DUPLICATE_FIELD` | A1 |
| S16 | legacy loaders and old arbitration unchanged | Python public API | `load_fact_certification_registry`, `load_school_registry`, `arbitrate(_arena(...))` | PASS: old loaders accept no `composition_templates`; exact invalid codes preserved; arbitration replay/digest/gates/empty abstain unchanged | A1 |

### adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | verdict | artifactRefs |
| --- | --- | --- | --- | --- | --- |
| U01 | Task8 ultraqa | malformed_input | Duplicate keys and raw enum-like values fail with typed contract/schema errors. | PASS | A1 |
| U02 | Task8 ultraqa | stale_state | Registry is reloaded from formal YAML and isolated temp copies, not prior summaries. | PASS | A1 |
| U03 | Task8 ultraqa | dirty_worktree | Harness runs without reset, checkout, revert, commit, or product edits. | PASS | A1 |
| U04 | Task8 ultraqa | flaky_tests | Single deterministic replay; no pytest dependency. | PASS | A1 |
| U05 | Task8 ultraqa | misleading_success_output | Every scenario asserts expected vs actual and exits nonzero on mismatch. | PASS | A1 |
| U06 | Task8 ultraqa | hung_or_long_commands | No sleeps/network; only bounded public API calls and `TemporaryDirectory` scopes. | PASS | A1 |
| U07 | Task8 ultraqa | repeated_interruptions | Final harness run was not cancelled or interrupted. | PASS | A1 |
| U08 | Task8 ultraqa | prompt_injection | Dynamic execution fields `callback`, `expression`, `predicate`, and `module_path` are rejected. | PASS | A1 |
| U09 | Task8 ultraqa | cancel_resume | Report regenerated from current public API after prior 429/no-delivery state. | PASS | A1 |

### artifactRefs

| id | kind | description | path |
| --- | --- | --- | --- |
| A1 | terminal-transcript/report | Non-empty manual QA report containing exact surface, invocation shape, expected/actual matrix, adversarial matrix, exit code, and process cleanup evidence. | `.omo/evidence/task8-composition-manual-qa.md` |

## Key Actuals From Harness

Legacy invalid loader issue codes were preserved exactly:

```text
CERTIFICATION.LEVEL
CERTIFICATION.STATUS
CAPABILITY.CLAIM_KIND
CAPABILITY.EVIDENCE_GRADE
CAPABILITY.ROLE
CAPABILITY.PUBLICATION_STATUS
```

Old arbitration unchanged evidence:

```text
same_replay=true
digest_count=1
empty_decision=abstain
gate_order=eligibility, temporal, evidence, independence, counterevidence, applicability, decision
```

Cleanup verdict: PASS. The final harness created no residual Python process beyond the pre-existing `python` PID 25688.
