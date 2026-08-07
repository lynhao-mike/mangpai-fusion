# Task11 Shadow Runner Code Review

Review date: 2026-08-04
Workspace: F:\多流派新思路
Reviewer role: code quality reviewer, read-only for product/tests

## Scope Reviewed

- Plan boundary: `plans/multi-school-governance-wave1-implementation-2026-08-02.md`, Task 11, plus design/module boundaries from `plans/multi-school-governance-design-2026-08-02.md`.
- Done claim/evidence:
  - `.omo/notepads/multi-school-governance-wave1/task11-shadow-runner.md`
  - `.omo/start-work/artifacts/task11-shadow-runner.txt`
  - `.omo/start-work/artifacts/task11-audit-doneclaim.md`
  - `.omo/start-work/artifacts/task11-audit-public-api-replay.txt`
  - `.omo/evidence/task11-shadow-runner-manual-qa/*`
- Final files:
  - `engine/application/governance_shadow_runner.py`
  - `engine/application/governance_shadow_types.py`
  - `engine/application/governance_shadow_school_views.py`
  - `tests/application/test_governance_shadow_runner.py`
  - `engine/governance/__init__.py`

Note: the reviewed files are currently untracked in a heavily dirty worktree, so there is no reliable git diff for those paths. I reviewed the final file contents directly with line numbers and treated all prior evidence as untrusted until inspected.

## Skill Perspective Check

- `omo:remove-ai-slops` was loaded and applied as a read-only review lens over production and test code.
- `omo:programming` was loaded, including the Python reference and code-smell reference.
- Result: no blocking skill-perspective violations found. No `Any`, `object`, `cast`, `type: ignore`, broad `except`, mutable dataclass, oversized module, deletion-only test, tautological removal test, or implementation-mirroring test was found in the Task11 files.
- Watch item: the shadow result envelope is audit-light for arbitration details. This is a Task11/design-contract concern, not an AI-slop or Python-strictness blocker.

## Findings

### CRITICAL

None.

### HIGH

None.

### MEDIUM

1. `engine/application/governance_shadow_types.py:126` - `ShadowArbitrationTrace` serializes only decision, arbitration digest, retained claim IDs, and gate retained/rejected IDs. The underlying `ArbitrationResult` also carries applicable/minority/preserved variants, temporal groups, independent evidence groups, counterevidence traces, and capability audits, and its digest binds those fields. Task11/design language asks the shadow result to expose audit-ready gate trace, issues, versions, and governance arbitration context. Digest binding reduces tampering risk, but API consumers cannot inspect the omitted arbitration audit material from the shadow result itself. This is not a blocker for Wave1 isolation, but should be addressed before any Wave2 consumer treats the shadow result as the sole audit artifact.

### LOW

None.

## Test And Static Evidence

- Focused: `python -m pytest tests/application/test_governance_shadow_runner.py -q`
  - Result: 6 passed, 1 warning in 2.25s
- Exact Task11 plan command: `python -m pytest tests/application/test_governance_shadow_runner.py tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q`
  - Result: 94 passed, 1 warning in 58.09s
- Governance joint: `python -m pytest tests/governance tests/application/test_governance_fact_builder.py tests/application/test_governance_claim_adapters.py tests/application/test_governance_shadow_runner.py -q`
  - Result: 193 passed, 1 warning in 51.83s
- Representative compatibility suite: `python -m pytest tests/yang_marriage tests/ren_timing tests/decision/test_staged_arbitration.py tests/predicates/test_ten_god_structures.py tests/test_production_rule_loader.py tests/test_decision_mvp.py tests/test_decision_v5_adapter.py -q`
  - Result: 333 passed, 1 warning in 129.19s
- Ruff: `ruff check engine/application/governance_shadow_runner.py engine/application/governance_shadow_types.py engine/application/governance_shadow_school_views.py tests/application/test_governance_shadow_runner.py`
  - Result: all checks passed
- Ruff format: `ruff format --check engine/application/governance_shadow_runner.py engine/application/governance_shadow_types.py engine/application/governance_shadow_school_views.py tests/application/test_governance_shadow_runner.py`
  - Result: 4 files already formatted
- No-excuse: `python C:/Users/Administrator/.codex/plugins/cache/sisyphuslabs/omo/4.13.0/skills/programming/scripts/python/check-no-excuse-rules.py engine/application/governance_shadow_runner.py engine/application/governance_shadow_types.py engine/application/governance_shadow_school_views.py tests/application/test_governance_shadow_runner.py`
  - Result: no violations in 4 file(s)
- Compileall: `python -m compileall -q engine/application/governance_shadow_runner.py engine/application/governance_shadow_types.py engine/application/governance_shadow_school_views.py tests/application/test_governance_shadow_runner.py`
  - Result: exit 0
- Pure LOC:
  - `engine/application/governance_shadow_runner.py`: 242
  - `engine/application/governance_shadow_types.py`: 184
  - `engine/application/governance_shadow_school_views.py`: 55
  - `tests/application/test_governance_shadow_runner.py`: 233
- Type/slop scan: `rg -n "\bAny\b|\bobject\b|cast\(|type:\s*ignore|pyright:\s*ignore|except\s+(Exception|BaseException)|except\s*:|# noqa" ...`
  - Result: no matches in Task11 files

All pytest warnings were the existing `engine.application.dual_engine_adapter` deprecation warning, not a Task11 failure.

## Behavioral Review Notes

- Shadow-only isolation: no production/report/feedback/learning imports found in runner implementation.
- Compatibility: `run_decision_mvp` and V5 adapter representative tests passed.
- Fact conflict: explicit `FactConflictContext` returns `fail_closed` and no arbitration trace.
- Target year/liunian: no target year omits `chart.liunian`; liunian trigger remains inactive with `missing_required_fact`.
- Ditiansui: School View outcome with `school_id == "ditiansui"` is excluded before five-school arena adaptation.
- Single school failure: explicit `SchoolViewFailure` is preserved as unavailable and does not discard available school claims.
- Registry mutation: reviewed code path uses injected registries read-only; no mutation API is called.
- Manual QA artifacts under `.omo/evidence/task11-shadow-runner-manual-qa` contain two failing assertions for unknown-school and unknown-capability expectations. Inspection shows those are expectation mismatches: unknown legacy school is surfaced as an adaptation issue, and unregistered capability is rejected at the applicability gate. I do not count them as Task11 blockers.

## Recommendation

codeQualityStatus: WATCH
recommendation: APPROVE
blockers: None

Residual risk: the arbitration trace should be expanded before downstream consumers depend on this result as a complete audit envelope.
