# Wave2 Planning Collection - Collect, Freeze, And Scoring Contracts

Date: 2026-08-06 (Asia/Shanghai)  
Workspace: `F:\多流派新思路`  
Mode: read-only plan collection and targeted verification; no product or test edits; no subagents

## Verdict

- contract map: **confirmed against current source and tests**
- focused test result: **255 passed in 164.02s; exit code 0**
- confidence: **0.97**
- planning blocker: **one explicit Wave1 governance-shadow to blind-output adapter is missing**
- product/test edits: **none**

The existing evaluation package already has reusable and tested primitives for
canonical blind outputs, immutable content-hash freezing, label reveal, scoring,
posterior metrics, prospective custody, high-risk review, and offline gates.
Wave2 should reuse those primitives. It must not serialize a
`GovernanceShadowResult` directly into the frozen-run envelope: the types have
different identities and semantics, and no such adapter exists in the current
tree.

## Decisive Current APIs

### Blind output and freeze envelope

`engine/evaluation/models.py:110-157` is the persisted boundary:

- `BlindSchoolOutput` carries `case_id`, `school_id`, `task_id`, one of
  `claim | abstain | unsupported`, rationale, predictions, and counter-evidence.
- `FrozenBlindRun` binds task-catalog version, rule-snapshot identity, freeze
  time, normalized outputs, and `freeze_hash`; its schema is
  `school-capability-frozen-run/v1`.

`engine/evaluation/freeze.py:20-65` provides the reusable freeze primitive:

- `freeze_outputs()` normalizes prediction order by `prediction_id`, normalizes
  output order by `(case_id, task_id, school_id)`, and hashes the complete
  canonical payload.
- When `frozen_at` is omitted, the timestamp is content-derived, making
  identical freezes stable. Prospective runs should inject the registered
  observation-window start explicitly rather than rely on that fallback.
- `verify_frozen_run()` verifies content integrity only. It does not establish
  task eligibility, registry authorization, witness chronology, role
  separation, or label quality; those remain separate gates.

`engine/evaluation/freeze.py:68-91` is the label-reveal boundary. It verifies the
freeze before reading labels, requires the exact document keys
`schema_version`, `freeze_hash`, and `labels`, requires
`school-capability-labels/v1`, binds the matching freeze hash, and rejects
duplicate `(case_id, task_id)` label identities.

### Existing adapter is not the Wave2 adapter

`engine/evaluation/blind_adapter.py:16-44` only exposes
`adapt_v5_to_blind_outputs(V5Output, tasks, schools)`. It intentionally emits
`abstain` for a present runner with no task-specific event binding and
`unsupported` for a missing runner. It does not consume a governance shadow
result and it never fabricates a precise claim from broad domain similarity.

`engine/application/governance_shadow_types.py:186-224` defines
`GovernanceShadowResult` as an aggregate application trace: status, fact
snapshot identities, claim traces, unavailable schools, excluded claim refs,
trigger/composition traces, arbitration summary, issues, and a result digest.
It has no `BlindSchoolOutput` state contract, task-catalog binding, per-task
prediction envelope, or freeze hash. `run_governance_shadow()` returns this type
after fact construction, adaptation, triggers, composition, and arbitration
(`engine/application/governance_shadow_runner.py:214-264`).

A repository-wide source search found no `GovernanceShadowResult` consumer in
`engine/evaluation` and no converter to `BlindSchoolOutput` or
`FrozenBlindRun`. Therefore the adapter is a real Wave2 implementation seam,
not a rename or import task.

## Required Wave2 Adapter Contract

Add a narrow evaluation-boundary adapter, preferably a new module such as
`engine/evaluation/governance_shadow_adapter.py`, rather than changing the
Wave1 shadow result or the generic freeze/scoring primitives.

The adapter must:

1. Consume a verified `GovernanceShadowResult` plus an explicit, versioned
   task-specific projection/binding. The shadow result alone is insufficient to
   synthesize a divorce/remarriage probability.
2. Bind exact `case_id`, `school_id`, `task_id`, task-catalog version,
   rule/calculator versions, horizon/window, probability, and structured fact
   refs before emitting `state="claim"`.
3. Preserve the source-school identity. The aggregate arbitration result must
   not silently become six per-school predictions or an unnamed ensemble.
4. Emit `abstain` when a registered/capable source ran but lacks an exact
   task-specific prediction binding. Emit `unsupported` only for genuinely
   unavailable or uncertified capability. Do not count a fail-closed run as a
   scored claim.
5. Never turn `excluded_claim_refs`, minority context, arbitration retention, a
   report sentence, or relationship-pressure evidence into an event outcome.
6. Be deterministic and side-effect free, producing only validated
   `BlindSchoolOutput` values. The caller then invokes existing
   `freeze_outputs()`; the adapter must not read labels, observations, feedback,
   reports, learned weights, or capability scores.
7. Fail closed on result-digest mismatch, case/task/version mismatch, ambiguous
   source ownership, missing probability, invalid probability, missing required
   facts, duplicate output identity, or more than the task's permitted
   prediction count.

Do not add a permissive `from_dict()` bridge from the shadow serialization to
`FrozenBlindRun`. That would bypass the semantic conversion and task binding
that the freeze hash cannot prove.

## Divorce/Remarriage Scoring Contract

The authoritative task catalog entry is
`mapping/school-capability-task-catalog-v1.yaml:23-32`, mirrored by
`META/prospective-go-task-catalog-v1.json:29-39`:

- task: `marriage.divorce_or_remarriage`
- claim/scoring: `binary_event` / `binary_probability`
- quantifiable: `true`
- high risk: `true`
- horizons: `lifetime`, `ten_year`
- required inputs: `four_pillars`, `sex_marker`
- positive/negative labels: `occurred` / `not_observed`
- relationship pressure is explicitly not equivalent to divorce/remarriage.

`engine/evaluation/scoring.py:18-33` requires a binary label to equal exactly
the configured positive or negative string. Unknown, `no_data`, pressure, and
missing evidence are not negative labels and raise if presented as a binary
label.

`score_output()` at `scoring.py:104-165` has these consequences:

- `unsupported` has no knowledge coverage and no score.
- `abstain` has knowledge coverage and can incur the fixed 0.1 opportunity cost
  when a quantifiable label exists.
- a claim with no label remains unscored; absence of a label is not a miss or a
  negative.
- a binary claim requires exactly one prediction and uses Brier accuracy.
- a high-risk false positive receives the `2.0` utility-loss multiplier defined
  at `scoring.py:9-10`; the multiplier affects utility, not the Brier value.

`engine/evaluation/capability.py:41-128` computes the downstream metrics:

- calibration error is `None` below five scored binary claims;
- coverage is the fraction of eligible cases whose state is not `unsupported`,
  so abstention remains visible as covered but non-claiming behavior;
- weighted proper-score count is `n_eff`; accepted weights are only
  `0`, `0.5`, or `1`;
- posterior mean/interval uses the weighted hit/miss counts with a Beta prior;
- discrimination is population standard deviation of claim probabilities.

Wave2 must keep claim coverage, abstention, and unsupported capability separate.
Combining them into one `coverage` number would reward fabricated claims and
erase honest capability gaps.

## Label Isolation And Custody Order

The current prospective chain already establishes the order Wave2 should reuse:

```text
register intake/future question
  -> prepare whitelist-only blind bundle
  -> run and freeze complete output grid
  -> witness/verify freeze chronology
  -> release custody access or wait for observation-window maturity
  -> collect observation without predictions
  -> independent high-risk review when required
  -> bind final label to immutable parents
  -> reveal/score
  -> cohort audit and offline gate
```

Supporting contracts:

- `prepare_single_case_blind_bundle()` accepts intake, future question, task and
  rule files, and a new target only (`prospective_single_case.py:602-690`). It
  does not accept feedback, labels, reports, or observations.
- `build_single_case_staged_frozen_run()` re-verifies the bundle and requires a
  complete, duplicate-free six-school/task grid
  (`prospective_single_case.py:873-966`). Its inputs are the bundle root and
  controlled timestamps/revision metadata, not outcome data.
- Witness validation requires exact event order
  `registered -> prepared -> freeze`, exact payload hashes, and strict time
  ordering (`prospective_evidence.py:250-323`).
- Feedback release requires a verified freeze, pairwise-separated human roles,
  and a zero-marker leakage scan; it cannot predate verification
  (`prospective_evidence.py:326-414`).
- Immediate retrospective custody is read only after release and is cut off at
  freeze time; duplicate label identities reject
  (`prospective_evidence.py:627-699`).
- `not_observed` for future evidence cannot become scorable before the complete
  registered window matures (`prospective_evidence.py:848-948` and
  `prospective_gates.py:529-549`).
- `evaluate_feedback_release()` invokes the feedback reader only after all
  release gates pass (`prospective_evidence.py:1257-1286`).

The Wave2 school execution and shadow-to-blind adapter must stay before the
release boundary. Passing a feedback reader, revealed-label path, report path,
known-fact/outcome document, or learned score into either API is a design error,
even if a later hash appears valid.

## High-Risk Review Boundary

`engine/evaluation/high_risk_review.py:11-15` lists
`marriage.divorce_or_remarriage` as high risk. For this task the only review
decisions are `occurred` and `not_observed` (`high_risk_review.py:49-53`). Review
payloads reject prediction, report, claim, and other-review leakage fields
(`high_risk_review.py:44-48,106-115`).

An A-grade final label requires two different reviewers who independently bind
the same observation/evidence/label identity and agree. Conflict remains HOLD
until a distinct third adjudicator resolves it; operational roles must remain
excluded (`high_risk_review.py:318-424`). Wave2 must not use model output as a
review, downgrade to a single review, or treat unresolved conflict/no-data as a
scorable negative.

The existing CLI surface already supports the lifecycle:
`tools/school_capability_review.py:256-305` provides
`prepare`, `submit`, `adjudicate`, `finalize`, and `audit`. Reuse it rather than
creating a Wave2-specific shortcut.

## Current Offline Gates Versus Historical Targets

The current executable candidate gate at
`engine/evaluation/prospective_gates.py:1015-1077` requires:

- at least 20 unique completed immediate-retrospective subjects;
- at least one task with 15 labels containing both positive and negative cases;
- calibration error strictly below 0.2 on the same eligible task;
- high-risk review PASS/NOT_APPLICABLE;
- at least five competitive cases on one task, at least one selection change,
  learned utility not below static utility, and hash/witness/leakage audits PASS;
- `proposal_allowed` only on GO and always `production_switch=false`.

The current future gate at `prospective_gates.py:1080-1124` independently
requires at least 10 completed subjects, one future task with at least eight
positive-and-negative labels and calibration below 0.2, fresh high-risk review,
the same competition/utility/audit requirements, and no production switch.

`plans/upgrade-guides/post-gate-action-plan-2026-07-15.md:3` explicitly marks
that document's operating instructions as superseded historical material. Its
older targets of 30 prospective cases, 20 scoreable binary labels, and a 20-case
divorce/remarriage collection quota (`:39-48,174-187`) remain useful design
history or a stricter user-selected collection target, but they are not the
current executable gate. The Wave2 plan must name which threshold source it is
using and must not accidentally claim that passing 20/15 current immediate gate
also satisfies the older 30/20 program target.

## Function/File/Test Plan For Wave2

1. Add a typed task-binding/projection contract and the explicit
   governance-shadow adapter under `engine/evaluation`; keep Wave1 application
   and governance contracts unchanged.
2. Integrate the adapter at the prospective staging boundary before
   `freeze_outputs()`. Preserve the complete school/task grid and existing
   timing/fact-ref fail-closure.
3. Reuse `FrozenBlindRun`, label custody/review, `score_output()`, capability
   posteriors, cohort evidence, and both offline gates unchanged unless a test
   demonstrates a true contract gap.
4. Add focused adapter tests first: deterministic conversion; exact identity
   binding; no claim without one task-specific probability; fail-closed,
   unavailable, excluded, pressure-only, wrong-version, duplicate, and
   ambiguous-source cases; and proof that feedback/labels/reports are not API
   inputs.
5. Extend prospective frozen-run integration tests with one valid Yang marriage
   claim plus abstain/unsupported peers, tamper failure, and a failure proving
   that outcome material cannot alter pre-release frozen bytes.
6. Keep existing scoring and high-risk tests as regression gates, including
   unknown-not-negative, one-prediction-only, high-risk false-positive utility,
   dual-review identity separation, conflict adjudication, observation-window
   maturity, and no-data non-scorability.
7. Run the focused suite below, then run the repository's standard broader gate
   before any implementation is called complete. No Wave2 GO may publish a
   production route or mutate production weights.

Suggested focused command after implementation:

```powershell
python -B -m pytest tests/evaluation/test_governance_shadow_adapter.py tests/evaluation/test_freeze.py tests/evaluation/test_scoring.py tests/evaluation/test_task_catalog.py tests/evaluation/test_high_risk_review.py tests/evaluation/test_prospective_frozen_run.py tests/evaluation/test_prospective_evidence.py tests/evaluation/test_prospective_gates.py tests/evaluation/test_prospective_cohort.py tests/evaluation/test_school_capability_batch.py -q -p no:cacheprovider
```

## Verification Performed

Executed against the current worktree:

```powershell
python -B -m pytest tests/evaluation/test_freeze.py tests/evaluation/test_scoring.py tests/evaluation/test_task_catalog.py tests/evaluation/test_high_risk_review.py tests/evaluation/test_prospective_frozen_run.py tests/evaluation/test_prospective_evidence.py tests/evaluation/test_prospective_gates.py tests/evaluation/test_prospective_cohort.py tests/evaluation/test_school_capability_batch.py -q -p no:cacheprovider
```

Result: **255 passed in 164.02s (0:02:44), exit code 0**.

This confirms the reusable evaluation/prospective contracts. It does not test a
governance-shadow adapter because no such implementation or test exists yet.

## Hazards To Carry Into The Plan

1. **Critical - semantic-envelope bypass:** direct shadow-result serialization
   into a frozen run would hash an invalid semantic conversion rather than prove
   a valid prediction.
2. **Critical - outcome leakage:** any feedback, label, observation, report, or
   learned metric reachable before freeze invalidates prospective evidence.
3. **High - pressure/event conflation:** Yang relationship pressure must never
   be auto-labeled as divorce/remarriage `occurred`.
4. **High - aggregate/source ambiguity:** arbitration retention does not by
   itself identify a per-school probability or authorize cloning one result
   across schools.
5. **High - false negative manufacture:** unknown, missing, no-data, immature
   observation, review conflict, and abstention are not `not_observed`.
6. **High - review shortcut:** high-risk labels remain unscorable without two
   independent reviews or valid third-party adjudication.
7. **Medium - coverage inflation:** abstain is covered but is not a claim;
   unsupported is not covered. Report all three states separately.
8. **Medium - threshold drift:** current executable 20/15 and 10/8 gates differ
   from the superseded historical 30/20 target. Cite the chosen authority.
9. **Medium - integrity overclaim:** `verify_frozen_run()` proves content-hash
   integrity only; it is not witness, eligibility, registry, or custody proof.
10. **Medium - premature promotion:** all existing gates are offline proposals
    with `production_switch=false`; passing them does not authorize publication.

## Final Collection Assessment

Confidence is **0.97**. The reusable freeze, scoring, custody, review, and gate
contracts are well covered by the focused suite. The remaining uncertainty is
not about those primitives; it is the exact Wave2 task-specific projection from
Yang/governance semantics into a single, source-owned blind probability. The
implementation plan should make that projection an explicit reviewed contract
and must not hide it inside serialization or staging code.
