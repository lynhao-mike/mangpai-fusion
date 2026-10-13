# Task9 Trigger Boundary Manual QA

Surface: Python public API (`engine.governance.trigger_loader.load_trigger_registry`, `engine.governance.trigger_registry.build_trigger_registry`, `engine.governance.trigger_registry.evaluate_governance_trigger`).

Main invocation: `@'...manual QA harness...'@ | python -` from `F:\多流派新思路`.

Harness calibration note: first attempt exited `1` before matrix emission because I passed an absolute temp YAML path to a loader that requires a relative contained path. The successful run below used relative temp paths under `theory/ziping/` and deleted them in `finally`.

Summary: PASS rows `17`; FAIL rows `0`; row count `17`; Python `3.14.5`.

## manualQa.surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | expected | actual | exit | verdict | artifactRefs |
|---|---|---|---|---|---|---:|---|---|
| S01 | formal registry status/count | Python public API | `load_trigger_registry()` | `{"count":2,"statuses":["candidate","synthetic_only"],"ids":["synthetic.natal-present","synthetic.liunian-target"]}` | same | 0 | PASS | A1 |
| S02 | known allowed trigger with required natal facts | Python public API | `evaluate_governance_trigger(published_registry,'synthetic.natal-present',snapshot(chart.natal),TriggerEvaluationContext())` | `{"active":true,"issues":[]}` | same | 0 | PASS | A1 |
| S03 | unknown id/version inactive+issue | Python public API | `evaluate unknown id; build_trigger_registry(evaluator_version='9.9.9')` | `{"unknown":{"active":false,"issues":["unknown_trigger"]},"version":{"raised":"TRIGGER.EVALUATOR_VERSION"}}` | same | 0 | PASS | A1 |
| S04 | candidate/unpublished inactive | Python public API | `status in ('candidate','synthetic_only')` | both inactive with `["unpublished_trigger"]` | same | 0 | PASS | A1 |
| S05 | missing fact inactive | Python public API | `snapshot(other.fact)` | `{"active":false,"issues":["missing_required_fact"]}` | same | 0 | PASS | A1 |
| S06 | evaluator ignores undeclared fact kinds | Python public API | `required chart.natal + evaluator liunian_target_year_present + snapshot(chart.natal, undeclared chart.liunian)` | `{"active":false,"issues":[]}` | same | 0 | PASS | A1 |
| S07 | liunian with explicit target-year fact evaluated | Python public API | `snapshot(chart.liunian TemporalScope(LIUNIAN,target_year=2026))` | `{"active":true,"issues":[]}` | same | 0 | PASS | A1 |
| S08 | without target year inactive | Python public API | `snapshot(chart.liunian TemporalScope(DAYUN,2020-2029))` | `{"active":false,"issues":["missing_required_fact"]}` | same | 0 | PASS | A1 |
| S09 | as_of_date only inactive | Python public API | `snapshot(chart.natal), context.as_of_date='2026-08-04'` | `{"active":false,"issues":["missing_required_fact"]}` | same | 0 | PASS | A1 |
| S10 | system current year monkeypatch/clock change does not affect | Python public API | `TZ changes + distant as_of_date values` | both inactive with `["missing_required_fact"]` | same | 0 | PASS | A1 |
| S11 | nonempty parsed object does not activate | Python public API | `TriggerEvaluationContext(parsed_present=True), no chart.liunian` | `{"active":false,"issues":["missing_required_fact"]}` | same | 0 | PASS | A1 |
| S15 | same snapshot repeat digest/result equal; input object/registry/file no side effects | Python public API | `digest registry/snapshot/default YAML; evaluate twice; compare` | `result_equal=true`, result active, registry/snapshot/file digests equal | same | 0 | PASS | A1 |
| S16 | old production trigger probe unchanged | Python public API | `import engine.application.production_rule_loader; hasattr(_rule_triggered/rule_triggered/evaluate_trigger)` | `_rule_triggered=true`, `rule_triggered=true`, `evaluate_trigger=false` | same | 0 | PASS | A1 |
| S17 | forbidden evaluate_trigger import/call absent | Python public API | `hasattr(import_module(mod), evaluate_trigger) for governance trigger modules` | `false` for `engine.governance.trigger_registry`, `engine.governance.trigger_loader`, `engine.governance.registries` | same | 0 | PASS | A1 |

## manualQa.adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | actual | exit | verdict | artifactRefs |
|---|---|---|---|---|---:|---|---|
| S03 | unknown id/version inactive+issue | unknown identity/version | unknown trigger returns inactive issue; unsupported version raises closed contract error | same | 0 | PASS | A1 |
| S04 | candidate/unpublished inactive | publication gate | candidate and synthetic-only registrations do not execute | same | 0 | PASS | A1 |
| S05 | missing fact inactive | missing input gate | no declared required fact returns inactive `missing_required_fact` | same | 0 | PASS | A1 |
| S06 | evaluator ignores undeclared fact kinds | declared fact boundary | liunian evaluator cannot see undeclared liunian fact when trigger declares only natal | same | 0 | PASS | A1 |
| S08 | without target year inactive | temporal target-year boundary | dayun-scoped same-kind fact cannot substitute liunian target-year fact | same | 0 | PASS | A1 |
| S09 | as_of_date only inactive | context boundary | context date does not synthesize target-year evidence | same | 0 | PASS | A1 |
| S10 | system current year monkeypatch/clock change does not affect | clock/environment boundary | timezone and distant dates do not affect trigger activation without explicit fact | same | 0 | PASS | A1 |
| S11 | nonempty parsed object does not activate | parsed object boundary | `parsed_present=True` does not substitute a governance fact | same | 0 | PASS | A1 |
| S12 | natural-language evaluator reject | evaluator parser boundary | natural text/expression evaluator IDs raise `TRIGGER.EVALUATOR_ID` | same | 0 | PASS | A1 |
| S13 | dynamic callback/expression/predicate/module_path reject | dynamic execution boundary | `lambda`, `predicate:`, `module_path:`, `callback://` evaluator IDs all raise `TRIGGER.EVALUATOR_ID` | same | 0 | PASS | A1 |
| S14 | duplicate YAML key/unknown top reject | YAML shape boundary | duplicate trigger key raises `TRIGGER.YAML_DUPLICATE_FIELD`; unknown top-level field raises `CERTIFICATION.YAML_FIELDS` | same | 0 | PASS | A1 |
| S15 | repeat deterministic/no mutation | determinism/immutability boundary | repeated result equal; registry, snapshot, and default file digests unchanged | same | 0 | PASS | A1 |
| S16 | old production trigger probe unchanged | legacy surface guard | old production loader still exposes `_rule_triggered`/`rule_triggered` and no `evaluate_trigger` | same | 0 | PASS | A1 |
| S17 | forbidden evaluate_trigger import/call absent | forbidden fallback guard | no `evaluate_trigger` symbol on governance trigger modules | same | 0 | PASS | A1 |

UltraQA classes covered: registry contract; known positive activation; unknown identity/version; publication gate; missing input gate; declared fact boundary; temporal target-year boundary; context/clock boundary; parsed object boundary; natural-language rejection; dynamic evaluator rejection; YAML shape validation; determinism/immutability; legacy surface guard; forbidden fallback absence; cleanup/no residual temp fixture.

## manualQa.artifactRefs

| id | kind | description | path |
|---|---|---|---|
| A1 | markdown evidence | This manual QA matrix and run transcript summary. Non-empty by construction; final byte count recorded below. | `.omo/evidence/task9-trigger-boundary-manual-qa.md` |

## Cleanup

Temp YAML files created by the successful harness:

| path | cleanup result |
|---|---|
| `theory/ziping/_task9_trigger_dup_tmp.yaml` | removed |
| `theory/ziping/_task9_trigger_unknown_top_tmp.yaml` | removed |

Post-run residual temp-file check: `Get-ChildItem theory/ziping/_task9_trigger_*_tmp.yaml -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count` returned `0`.

Process note: `Get-CimInstance Win32_Process -Filter "ProcessId=29244"` showed an unrelated `python -m pytest -q` process. The bounded manual QA harness itself exited `0` and left no Task9 temp YAML files.

Final report bytes: `8094`.
