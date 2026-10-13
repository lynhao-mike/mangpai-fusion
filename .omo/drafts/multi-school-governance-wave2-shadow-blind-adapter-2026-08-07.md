# W2-C2 Governance shadow → blind output semantic adapter CONTRACT

## Controller state

- Unit: `W2-C2`
- Stage: `CONTRACT`
- Contract revision: `R3`
- Verdict: `PASS`
- Review history: R1 received `REVISE`; R2 closed the upstream-attestation, typed-claim ownership, all-state rationale, exact-task-predicate, reference-grammar, and test-accounting defects but received `REVISE` for an ambiguous event conclusion predicate. R3 changed only that cited semantic defect and the required synchronized checks; an independent fresh reviewer returned `PASS` on 2026-08-07.
- Topology authority: W2-C2 is the independently reviewable `GovernanceShadowResult` → `BlindSchoolOutput` semantic adapter.
- Predecessor boundary: W2-C1 is frozen and handed off; none of its write, test, review, verification, publication, or production authority is inherited.
- Remote boundary: local-only work. Any GitHub service-side mutation is permanently forbidden.
- Local protection boundary: preserve all pre-existing tracked and untracked changes; no reset, clean, checkout, restore, stash, rebase, commit, or equivalent destructive/history-changing Git operation.

## Authority and source labels

| Fact | Source label | Authority |
|---|---|---|
| User approved W2-C2 | `USER_DECISION` | User message: `批准w2-c2` |
| W2-C2 topology identity | `PROJECT_STATE` | `.omo/drafts/multi-school-governance-wave2-yang-marriage-2026-08-06.md` topology ledger |
| Shadow result fields and digest | `TOOL_OBSERVATION` | `engine/application/governance_shadow_types.py` |
| Shadow runner construction | `TOOL_OBSERVATION` | `engine/application/governance_shadow_runner.py` |
| Blind output contracts | `TOOL_OBSERVATION` | `engine/evaluation/models.py` |
| Task semantics | `TOOL_OBSERVATION` | `mapping/school-capability-task-catalog-v1.yaml` |
| Existing freeze boundary | `TOOL_OBSERVATION` | `engine/evaluation/freeze.py` |
| Planning requirements | `PROJECT_STATE` | `.omo/evidence/wave2-plan-collect-freeze-scoring.md` |

## Anchor Ledger — Unit W2-C2

This ledger is frozen from the user-approved topology, observed source contracts, and Wave 2 planning authority rather than from any rejected revision. Only an explicit user instruction may change it.

| Frozen surface | Exact anchor | Source |
|---|---|---|
| Target | one pure deterministic `GovernanceShadowResult` → `tuple[BlindSchoolOutput, ...]` semantic adapter using an already validated task and explicit projections | `USER_DECISION` + `PROJECT_STATE` |
| Public call boundary | `adapt_governance_shadow_to_blind_outputs(result, task, projections)`; one immutable projection type and one immutable prediction-binding type; no CLI | `PROJECT_STATE` planning seam + observed Python boundaries |
| State set | exactly `claim`, `abstain`, `unsupported`; fail closed on invalid or ambiguous input | observed `BlindSchoolOutput` contract + `PROJECT_STATE` |
| Initial task | exact `marriage.divorce_or_remarriage` binary-event predicate and positive label `occurred`; relationship pressure is not the event | task catalog |
| Output ownership | one output per explicit source projection; preserve exact case/school/task identity; no aggregate or implicit grid expansion | `PROJECT_STATE` |
| Side-effect boundary | pure local conversion only; no freeze, scoring, label reveal, publication, routing, file/network/process/Git/GitHub effects | `USER_DECISION` + `PROJECT_STATE` |
| File whitelist | `engine/evaluation/governance_shadow_adapter.py`; `tests/evaluation/test_governance_shadow_adapter.py` | admitted W2-C2 seam |
| Protection boundary | preserve all existing tracked/untracked work; no reset, clean, checkout, restore, stash, rebase, commit; no GitHub mutation | `USER_DECISION` |

## Revision State Table

| Revision | Author role reset? | Reviewer role reset? | Verdict | Defect classes found | Repeated from earlier revision? | Anchor Ledger drift found? |
|---|---:|---:|---|---|---:|---:|
| R1 | n/a | yes | `REVISE` | upstream attestation; task/source semantics; all-state rationale; exact task/ref/accounting predicates | no | no |
| R2 | yes | yes | `REVISE` | event conclusion/content predicate ambiguity | no | no |
| R3 | yes | yes | `PASS` | exact event-conclusion defect closed; no new defect | no | no |

R1 defects listed as closed by the R2 reviewer remain frozen and must not regress. The R3 author role receives only this ledger, the exact R2 event-conclusion finding, and authority to make the synchronized semantic-predicate edits identified by that finding.

## Exactly one target

Add one deterministic, side-effect-free evaluation-boundary adapter that consumes:

1. one exact `GovernanceShadowResult`;
2. one already validated `BlindTask`;
3. one or more exact, versioned, task-specific source projections;

and returns a canonical tuple of validated `BlindSchoolOutput` values, with one honest `claim`, `abstain`, or `unsupported` state per admitted source projection.

The adapter must verify shadow integrity and explicit identity/version bindings before interpreting any projection. The shadow result alone is never sufficient to synthesize a prediction.

## Proposed public contract

The exact names may be revised only by a fresh CONTRACT revision before implementation. R3 freezes the following intended shape:

```python
@dataclass(frozen=True, slots=True)
class ShadowPredictionBinding:
    source_claim: GovernanceClaim
    event_conclusion_id: Literal["yang.divorce_or_remarriage_event_risk/v1"]
    probability: float
    horizon: Literal["lifetime", "ten_year"]
    start_year: int | None
    end_year: int | None
    evidence_refs: tuple[str, ...]
    fact_refs: tuple[str, ...]
    falsifier: str

@dataclass(frozen=True, slots=True)
class GovernanceShadowTaskProjection:
    schema_version: str
    case_id: str
    school_id: str
    task_id: str
    task_catalog_version: str
    rule_version: str
    calculator_version: str
    expected_result_digest: str
    expected_fact_snapshot_id: str
    expected_fact_snapshot_digest: str
    expected_input_digest: str
    source_execution_state: Literal["executed", "unavailable"]
    capability_state: Literal["certified", "uncertified"]
    rationale: str
    prediction: ShadowPredictionBinding | None = None

def adapt_governance_shadow_to_blind_outputs(
    result: GovernanceShadowResult,
    task: BlindTask,
    projections: Sequence[GovernanceShadowTaskProjection],
) -> tuple[BlindSchoolOutput, ...]: ...
```

The projection is an explicit reviewed attestation and semantic binding, not a serialization bridge. The adapter can verify its internal consistency with result-visible identities and with an exact typed `GovernanceClaim`; it cannot independently prove the upstream truth of `case_id`, task/rule/calculator versions, successful zero-claim execution, or capability certification because those facts are absent from `GovernanceShadowResult`. Projection creation, review, custody, and publication remain outside W2-C2. A projection instance therefore proves only that these assertions were supplied to this boundary, never that upstream execution/certification truth was independently established.

## Frozen schema constants

- Projection schema: `governance-shadow-task-projection/v1`
- Initial event-conclusion ID: `yang.divorce_or_remarriage_event_risk/v1`
- Exact conclusion bound to that ID: `杨派原局夫妻宫事件锚与独立配偶结构交互同向，支持存在离婚或再婚事件风险，但不作必然判断。`
- Accepted shadow schema: `governance.shadow-result.v1`
- Accepted shadow runner: `governance-shadow-runner/v1`
- Initial admitted task: `marriage.divorce_or_remarriage`
- Exact domain: `婚姻`
- Exact task claim type: `binary_event`
- Exact scoring method: `binary_probability`
- Exact quantifiable flag: `true`
- Exact high-risk flag: `true`
- Exact allowed horizons after tuple freezing: `("lifetime", "ten_year")`
- Exact required inputs after tuple freezing: `("four_pillars", "sex_marker")`
- Exact label schema after mapping freezing: `{type: boolean, positive_label: occurred, negative_label: not_observed}` with no missing or additional keys
- Exact evaluation note: `只评价是否发生，不把关系压力自动等同离婚`
- Maximum predictions per output for this binary task: exactly one for `claim`, zero otherwise

No fixed probability value is frozen. In particular, W2-C1 governance confidence `0.60` is not a default forecast probability.

## Behavior invariants

### A. Typed boundary and result integrity

1. Reject duck-typed or subclass substitutes for `GovernanceShadowResult`, `BlindTask`, `GovernanceShadowTaskProjection`, `ShadowPredictionBinding`, and claim-bound `GovernanceClaim`; exact concrete boundary types are required.
2. Require non-empty projections; an empty conversion must fail closed rather than masquerade as a complete output grid.
3. Require exact accepted shadow schema and runner versions.
4. Recompute `shadow_result_digest(result)` and require equality with `result.result_digest`.
5. Require `result.status == "ok"`; `fail_closed` never becomes a scored claim, abstention, or unsupported row through this adapter.
6. Every projection must exactly match the result-visible `result_digest`, `fact_snapshot_id`, `fact_snapshot_digest`, and `input_digest`.
7. Every projection must have non-empty case, school, task-catalog, rule, and calculator assertions. Every projection in one call must share the same case ID, task-catalog version, rule version, calculator version, and expected shadow identities. This is an internal consistency check only; the adapter does not claim that result independently authenticates fields it does not contain.
8. Projection `task_id` must exactly equal `task.task_id`; every `BlindTask` field must satisfy the exact predicate frozen above, including tuple order and exact label-schema key/value equality.

### B. Output identity and ordering

1. Output identity is `(case_id, school_id, task_id)`.
2. Reject duplicate projection/output identities before returning any output.
3. Return outputs sorted deterministically by `(case_id, task_id, school_id)`.
4. Preserve exact source-school identity; never clone aggregate arbitration into multiple schools and never emit an unnamed ensemble.
5. One projection yields exactly one output; no implicit six-school expansion occurs.

### C. Honest three-state semantics

1. Every projection requires a non-empty rationale independent of prediction state; output rationale is copied only from this field after exact trim validation.
2. `unsupported` requires `source_execution_state == "unavailable"` or `capability_state == "uncertified"`.
3. An unavailable projection must match exactly one `result.unavailable_schools` entry for the same school. A projection marked executed must not match any unavailable entry. Uncertified capability without an unavailable trace remains an external projection assertion, not a result-proven fact.
4. `unsupported` must contain no prediction. Any supplied prediction with unavailable or uncertified state is rejected, not silently dropped.
5. `abstain` requires projected `source_execution_state == "executed"`, projected `capability_state == "certified"`, and no prediction binding. Because zero-claim execution/certification are not result-visible, this row is an attested state, not independently result-proven execution truth.
6. `claim` requires the same projected executed + certified assertions plus exactly one complete prediction binding whose typed source claim passes section D.
7. Neither an absent claim trace nor a retained arbitration claim alone chooses `abstain` or `claim`; the projection state is explicit and must satisfy all available consistency checks.

### D. Claim source ownership and exact event conclusion

1. A claim binding must contain one exact typed `GovernanceClaim`; its `claim_id` must match exactly one `result.claims` trace.
2. The typed claim school and matched trace school must both equal projection `school_id`.
3. The typed claim `content_digest.value` must equal the matched trace content digest; its adapter provenance source ref must equal the matched trace source ref.
4. The typed claim `task_id` must equal projection/task `marriage.divorce_or_remarriage`; `claim_kind` must be exact event, stance must be exact support, blockers must be empty, and falsifier must be non-empty.
5. The binding `event_conclusion_id` must equal the frozen token `yang.divorce_or_remarriage_event_risk/v1`, and the typed claim `specification.conclusion` must equal the complete frozen conclusion text byte-for-byte after requiring that the supplied value already equals its stripped form. The pair `(event_conclusion_id, exact conclusion)` is the executable event predicate for this initial lane.
6. No substring, tokenization, regular expression, synonym, embedding, report-text interpretation, task ID, claim kind, stance, or arbitration-retention inference may substitute for the exact predicate. A pressure-only, conflict-only, separation-tendency, or otherwise non-identical conclusion fails closed even if every other typed field matches.
7. The source claim must appear in `result.arbitration.retained_claim_ids`; missing arbitration, rejected-only, excluded, or unretained claims cannot produce a prediction.
8. Arbitration retention is necessary but never sufficient: no prediction exists without the complete explicit binding, exact conclusion predicate, and typed claim semantic checks.
9. A source claim may back at most one output identity per call. Ambiguous reuse fails closed.
10. The adapter verifies only the typed claim fields exposed at the boundary and their trace equality. It does not reconstruct omitted claim semantics from `ShadowClaimTrace`.

### E. Prediction semantics

1. Probability is mandatory, finite, numeric, and within `[0.0, 1.0]`; booleans are rejected as probabilities.
2. Probability comes only from the explicit prediction binding. It must not be inferred from governance confidence, evidence grade, arbitration decision, capability scores, learned weights, or report text.
3. Event label comes only from the admitted task's exact positive label `occurred`; the adapter never emits `not_observed`.
4. Horizon must be allowed by the task.
5. `lifetime` requires both years absent and emits `{"label": "lifetime"}`.
6. `ten_year` requires integer start/end years, excludes booleans, and requires `start_year <= end_year`; it emits the exact years and label.
7. Prediction ID is deterministic and source-bound, derived from canonical identity material including projection schema, case, school, task, typed source claim ID/content digest, exact `event_conclusion_id`, exact typed-claim conclusion, task/rule/calculator versions, horizon/window, probability, evidence refs, fact refs, and falsifier.
8. Evidence refs and fact refs must each be non-empty tuples of exact strings. Each item must equal its stripped form, contain no whitespace, and be unique before canonical sorting; duplicates are rejected rather than silently deduplicated.
9. Evidence-ref grammar is `^[^#\\s]+#[^#\\s]+$`: one non-empty repository/source locator, one `#`, and one non-empty anchor. Fact-ref grammar is `^[A-Za-z_][A-Za-z0-9_]*(?:\\.[A-Za-z0-9_\u4e00-\u9fff]+)*$`; any evidence/source-rule locator containing `#` is therefore invalid as a fact ref. Returned refs are lexicographically sorted.
10. Binding falsifier must be non-empty after exact trim validation and must equal the typed source claim falsifier; output rationale comes from the projection-level rationale, not from prediction or report text.
11. Counter-evidence is empty in W2-C2 unless a later CONTRACT revision introduces an explicit typed source; the adapter must not infer it from arbitration or issues.

### F. Semantic non-expansion

1. Never turn `excluded_claim_refs`, minority context, trigger/composition traces, arbitration retention, issues, report sentences, or broad relationship-pressure evidence into an event prediction.
2. Never map unknown, no-data, missing, immature, conflict, pressure, or abstention to `not_observed`.
3. Never read or accept labels, observations, feedback, reports, learned weights, capability posterior scores, review decisions, or outcome documents.
4. No file I/O, clock access, randomness, environment access, network access, subprocess, Git, or GitHub operation is allowed in the adapter.

## Structural and dependency invariants

1. New production module may import only standard-library typing/dataclass/math/regular-expression helpers plus:
   - `engine.application.governance_shadow_types`
   - `engine.evaluation.models`
   - `engine.governance.governance_claim`
   - `engine.governance.governance_claim_values` only for exact event/support enum comparison
   - `engine.governance.canonical` only if required for deterministic prediction identity
2. It must not import:
   - `engine.evaluation.freeze`, scoring, capability, high-risk review, prospective custody/gates;
   - reports, feedback, cases, tools, weights, labels, observations;
   - school runners, Yang domain logic, W2-C1 adapter, registry loaders, YAML loaders;
   - network, subprocess, pathlib, datetime, random, Git, or GitHub clients.
3. Existing application/governance/evaluation contracts remain unchanged unless fresh CONTRACT review proves a true blocker. R3 grants no such change.
4. No `from_dict()` bridge to `FrozenBlindRun` may be added.
5. No capability YAML or production routing/configuration file may change.

## Exact implementation whitelist

Only these local files may be created or modified during IMPLEMENT:

1. `engine/evaluation/governance_shadow_adapter.py` — new production module implementing only this contract.
2. `tests/evaluation/test_governance_shadow_adapter.py` — new focused contract tests.

No deletion is authorized. No wildcard path is authorized. CONTRACT and controller persistence files are governed separately and are not implementation files.

## Scope IN

- Typed immutable projection and prediction binding contracts.
- Pure deterministic conversion to validated `BlindSchoolOutput` values.
- Shadow digest/identity/version checks.
- Source-school/claim ownership checks.
- Honest three-state conversion.
- Binary event probability/window/reference validation.
- Duplicate identity and deterministic ordering checks.
- Focused contract tests and exact regression selectors after fresh review.

## Scope OUT / Must NOT have

- W2-C3 staging integration, `freeze_outputs()`, frozen-run construction, label reveal, scoring, high-risk review, custody, cohort gates, or prospective workflow changes.
- Capability publication, registry YAML changes, promotion candidates, production publication receipts, production switch, routing weights, deployment, report generation, feedback ingestion, or learned calibration.
- Changes to Wave 1 shadow types/runner, W2-C1 adapter, generic evaluation models, existing adapters, or generic freeze/scoring primitives.
- Full school/task-grid completion logic.
- Any claim that output accuracy, calibration, proposal readiness, production readiness, Wave 2 completion, or production authorization has been proven.

## Focused test behavior partitions and static accounting

The focused test file must cover the following 20 named behavior partitions. A partition may use one test function with parameterized cases, but STATIC_REVIEW must report exactly: unique test-function count, each parameterized function's concrete case count, non-parameterized item count, and their arithmetic sum as expected pytest items. The number 20 is a semantic partition count only and must never be reported as the pytest item count unless static collection arithmetic independently equals 20.

1. exact valid claim conversion;
2. deterministic output ordering and prediction identity;
3. exact accepted shadow schema/runner versions;
4. result digest tamper rejection;
5. fail-closed status rejection;
6. expected result/snapshot/input identity mismatch rejection and explicit proof that case/version assertions are not claimed as result-authenticated;
7. exact all-field task predicate plus catalog/rule/calculator/case assertion validation;
8. exact type/duck-type rejection, including typed source claim;
9. duplicate output identity and source-claim reuse rejection;
10. unavailable → unsupported and exact unavailable trace matching;
11. uncertified → unsupported;
12. attested executed+certified+no binding → abstain, without treating absent trace as execution proof;
13. projection-level rationale is required for all states and unsupported/abstain cannot carry predictions;
14. typed source claim missing/wrong task/kind/stance/school/content/source-ref/falsifier rejection, plus exact event-conclusion ID and byte-for-byte typed conclusion acceptance/rejection proving that pressure-only or merely similar text cannot map to `occurred`;
15. missing arbitration/unretained/excluded source rejection;
16. probability missing/bool/non-finite/out-of-range rejection;
17. horizon/window validation for lifetime and ten-year;
18. exact evidence/fact-ref grammar, trim, duplicate, canonical sorting, falsifier, and rationale validation;
19. pressure/excluded/minority/arbitration-only material cannot manufacture claims;
20. static AST/API isolation proving no forbidden inputs, imports, file/network/clock/random/subprocess/freeze/scoring/label paths.

Tests must assert observable contract behavior; they must not copy the production digest/normalization implementation wholesale.

## Exact verification selectors and accounting

### Focused selector

```text
python -B -m pytest tests/evaluation/test_governance_shadow_adapter.py -q -p no:cacheprovider
```

Expected collection is not frozen until STATIC_REVIEW reads the completed test file and reports:

- collected test functions;
- parameterized test instances;
- expected total pytest items;
- AST isolation checks;
- no skipped/xfailed/deselected items unless explicitly revised into the contract.

### Narrow regressions

```text
python -B -m pytest tests/application/test_governance_shadow_runner.py tests/evaluation/test_blind_adapter.py tests/evaluation/test_models.py tests/evaluation/test_task_catalog.py tests/evaluation/test_freeze.py tests/evaluation/test_scoring.py -q -p no:cacheprovider
```

### Broader evaluation/prospective regression

Only after focused and narrow regressions pass, and only under a separately activated exact VERIFY envelope:

```text
python -B -m pytest tests/evaluation/test_governance_shadow_adapter.py tests/evaluation/test_freeze.py tests/evaluation/test_scoring.py tests/evaluation/test_task_catalog.py tests/evaluation/test_high_risk_review.py tests/evaluation/test_prospective_frozen_run.py tests/evaluation/test_prospective_evidence.py tests/evaluation/test_prospective_gates.py tests/evaluation/test_prospective_cohort.py tests/evaluation/test_school_capability_batch.py -q -p no:cacheprovider
```

The historical `255 passed` planning run is stale planning evidence and cannot satisfy W2-C2 VERIFY.

The historical Wave 1 `tests/test_application_candidates.py:21` collection `SyntaxError` remains outside W2-C2 and must not be hidden or reclassified.

## Fresh-review questions

1. Does the contract keep exactly one target and avoid merging capability publication or W2-C3 integration?
2. Does the contract distinguish adapter-verifiable result/claim content from externally attested case/version/execution/capability assertions without claiming upstream truth?
3. Can any `claim` be emitted without exact result integrity, full typed claim task/kind/stance/source ownership, the frozen event-conclusion ID paired with the byte-for-byte frozen typed conclusion, probability, window, and grammar-valid structured fact refs?
4. Are `abstain` and `unsupported` explicit attested states without guessing from absent shadow traces, and is rationale available for every state?
5. Could pressure, excluded/minority/arbitration-only context, labels, reports, or learned outcomes enter the API or affect output?
6. Are duplicate output/source identities and prediction counts fail-closed?
7. Is W2-C3 freeze/scoring/high-risk work strictly excluded?
8. Is the implementation whitelist exact and minimal?
9. Are test selectors and post-implementation static accounting falsifiable?
10. Does any clause accidentally imply production publication, empirical accuracy, or Wave 2 completion?

## Falsifiers

Any one of the following falsifies CONTRACT PASS:

- target or API remains materially ambiguous;
- projection or exact typed source claim can be omitted for a claim;
- result digest or result-visible expected identities are not checked;
- case/version/execution/capability assertions are presented as independently authenticated by a result that does not contain them;
- governance confidence can silently become forecast probability;
- school ownership can be inferred from aggregate arbitration;
- absent claim trace automatically chooses abstain or unsupported;
- the event-conclusion ID is absent, extensible, or accepted without byte-for-byte equality to the frozen typed-claim conclusion;
- relationship pressure, similar wording, or keyword inference can become divorce/remarriage event;
- labels/outcomes/reports/feedback/weights can enter the adapter;
- duplicate output identities or source reuse are not rejected;
- adapter invokes freeze, scoring, review, custody, registry publication, or production routing;
- whitelist includes wildcard or unrelated existing files;
- focused tests copy implementation logic or lack static dependency isolation;
- task predicates or reference grammars are not exact and executable;
- semantic partition count is confused with concrete pytest item accounting;
- verification counts cannot be reconciled;
- any GitHub-mutating effect is possible.

## STOP conditions

Stop and return the applicable Gate verdict if:

1. a required change outside the exact whitelist is discovered;
2. the existing shadow result cannot support a required consistency check even with explicit projection;
3. projection custody or capability/execution certification requires a new public schema or materially different architecture;
4. a second candidate is needed to complete this unit;
5. implementation would require capability publication, production routing, freeze/scoring integration, labels, outcomes, reports, feedback, or learned weights;
6. any operation risks overwriting user changes or mutating local Git history;
7. any operation may mutate GitHub service-side state;
8. a test collection/selector is missing, ambiguous, broader than authorized, or returns an unexpected result.

## Direct evidence boundary

A CONTRACT PASS would prove only that W2-C2 has one unique, bounded, falsifiable, implementable local contract with exact proposed files and verification selectors. It would not prove that implementation exists, tests pass, projections are operationally produced, projection attestations are true or under custody, case/version/execution/capability assertions are authenticated by the shadow result, school capability is published, outputs are frozen or scored, predictions are accurate, production is ready, Wave 2 is complete, or GitHub is synchronized.

## Forbidden inference boundary

Never infer:

- W2-C1 confidence equals forecast probability;
- retained arbitration equals a source-owned prediction;
- missing data equals `not_observed`;
- a typed projection instance proves upstream case/version/execution/capability truth without its own custody process;
- task ID, event kind, support stance, arbitration retention, or words resembling divorce/remarriage prove the frozen event conclusion;
- CONTRACT PASS equals implementation/behavior/verification PASS;
- local evidence equals production authorization or GitHub state.

## Approval gate

R3 received an independent fresh `PASS` after the reviewer reset prior assumptions, received the Anchor Ledger verbatim, re-read the complete candidate and minimum authoritative source facts, and verified the exact event-conclusion predicate, all synchronized checks, R1 non-regression, and absence of Anchor Ledger drift.

This PASS proves only CONTRACT eligibility. No test command is legal until IMPLEMENT completes and a fresh STATIC_REVIEW PASS activates a separately recorded VERIFY envelope.
