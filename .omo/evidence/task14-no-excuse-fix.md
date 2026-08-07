# Task 14 No-Excuse Exhaustiveness Fix Evidence

Date: 2026-08-06 (Asia/Shanghai)
Workspace: `F:\多流派新思路`

## DoneClaim

- `status`: DONE_WITH_RED_COLLISION_DISCLOSED
- `owned production files`:
  - `engine/governance/fact_certification.py`
  - `engine/governance/school_registry.py`
- `tests changed`: none
- `evidence file`: `.omo/evidence/task14-no-excuse-fix.md`

The final source clears all four assigned `missing-assert-never` sites. Both
`FactLevel` matches enumerate all four enum members separately and terminate
with `case unreachable: assert_never(unreachable)`. Open string school inputs
use bounded alias/canonical membership checks and retain typed unknown behavior;
they do not use `assert_never`, suppressions, casts, or widened types.

## Shared-Worktree / RED Record

The requested authentic four-failure RED could not be rerun from the shared
filesystem: both owned files were already untracked and had been modified by
another actor at `2026-08-06 11:17:09`, before this task's first inspection.
At first read they already contained the apparent four fixes: two terminating
`FactLevel` defaults, loop/membership alias normalization, and membership/if
school lookup. No source was reverted, stashed, checked out, or overwritten to
manufacture a RED.

Assigned upstream finding inventory (four sites):

1. `CertificationIdentity.__post_init__` FactLevel match.
2. `FactCertification.__post_init__` FactLevel match.
3. `normalize_school_input` open-string match.
4. `SchoolRegistry.lookup_school` open-string match.

Actual first checker execution before my edit:

```text
command: python C:/Users/Administrator/.codex/plugins/cache/sisyphuslabs/omo/4.13.0/skills/programming/scripts/python/check-no-excuse-rules.py engine/governance/fact_certification.py engine/governance/school_registry.py
exit: 0
stdout: no violations in 2 file(s)
```

This is not represented as RED. The collision was reported to the parent
immediately. The pre-edit focused behavioral baseline was still captured:

```text
command: python -m pytest tests/governance/test_fact_certification_registry.py tests/governance/test_school_registry.py tests/governance/test_wave1_baseline_contract.py -q
exit: 0
stdout: 29 passed, 1 warning in 19.00s
```

The warning is the existing `engine.application.dual_engine_adapter`
deprecation emitted by `engine/application/pipeline_runner.py:11`.

## Patch

The only edit made in this task was in
`engine/governance/fact_certification.py`: grouped enum alternatives were split
so both matches explicitly enumerate each actual `FactLevel` member. Rejection
messages and accepted/rejected behavior are unchanged:

- `CANONICAL_OBSERVATION`: rejected.
- `CANDIDATE_DERIVED`: rejected.
- `CERTIFIED_TECHNICAL`: accepted.
- `CERTIFIED_CROSS_SCHOOL`: accepted.

The concurrent open-string fixes in `engine/governance/school_registry.py` were
preserved unchanged. They retain exact aliases (`gao`, `duan`, `yang`, `ren`),
all five canonical IDs, stable peer iteration, legacy-only `ditiansui`, and
`UnknownSchool` for arbitrary query strings.

## GREEN Verification

Focused certification, school registry, and relevant Wave 1 baseline:

```text
command: python -m pytest tests/governance/test_fact_certification_registry.py tests/governance/test_school_registry.py tests/governance/test_wave1_baseline_contract.py -q
exit: 0
stdout: 29 passed, 1 warning in 14.07s
```

Static gates:

```text
command: ruff check engine/governance/fact_certification.py engine/governance/school_registry.py
exit: 0
stdout: All checks passed!

command: ruff format --check engine/governance/fact_certification.py engine/governance/school_registry.py
exit: 0
stdout: 2 files already formatted

command: python C:/Users/Administrator/.codex/plugins/cache/sisyphuslabs/omo/4.13.0/skills/programming/scripts/python/check-no-excuse-rules.py engine/governance/fact_certification.py engine/governance/school_registry.py
exit: 0
stdout: no violations in 2 file(s)
```

LOC measurement:

```text
command: PowerShell Get-Content physical/pure nonblank noncomment count
exit: 0
stdout:
engine/governance/fact_certification.py physical=255 pure=229
engine/governance/school_registry.py physical=280 pure=231
```

Both modules remain below the 250 pure-LOC ceiling and are in the 200-250
warning band. Their responsibilities remain nameable as `certification
contracts` and `school registry domain`; a future line-adding change should
split the relevant module before expanding it.

## Fresh-Process Manual QA

Command: a PowerShell here-string piped to a fresh `python -` process, importing
the public `engine.governance.registries` facade, loading the real default
registry, then probing canonical, alias, legacy, unknown, and all FactLevel
cases.

Exit: `0`

```text
normalize:ziping=ziping
normalize:gao_dechen=gao_dechen
normalize:gao=gao_dechen
lookup:ziping=PeerSchool
lookup:gao_dechen=PeerSchool
lookup:gao=UnknownSchool
lookup:ditiansui=LegacyCompatibilitySource
lookup:unknown_school=UnknownSchool
normalize_reject:'GAO'=SCHOOL.INPUT_UNKNOWN
normalize_reject:' gao'=SCHOOL.INPUT_UNKNOWN
normalize_reject:'gao_extra'=SCHOOL.INPUT_UNKNOWN
normalize_reject:'unknown_school'=SCHOOL.INPUT_UNKNOWN
fact_level:canonical_observation=rejected:CERTIFICATION.LEVEL
fact_level:candidate_derived=rejected:CERTIFICATION.LEVEL
fact_level:certified_technical=accepted
fact_level:certified_cross_school=accepted
manual_qa=PASS
```

Adversarial coverage confirms arbitrary strings reach `UnknownSchool` on
registry lookup and typed `SCHOOL.INPUT_UNKNOWN` rejection at normalization;
uppercase, whitespace-prefixed, suffixed, and wholly unknown inputs are not
guessed or normalized.

## Dirty-Worktree Preservation / Cleanup

- Initial scoped status: both production files were `??` (untracked).
- Initial total short-status count: `801` entries.
- No reset, checkout, stash, deletion, process termination, or unrelated edit
  was performed.
- No temporary QA files were created; the manual probe ran on stdin in a fresh
  process and exited normally.
- Final scoped production status remains `??` for both files. This evidence file
  is the only additional artifact created by this task.

## Residual Risks

- An authentic pre-fix four-failure checker transcript is unavailable because
  the fixes had already landed in the shared untracked files before inspection.
- The modules are untracked, so Git cannot provide a base diff that separates
  every concurrent line from this task's small enum-case refinement.
- No strict type checker was requested or run. Ruff, focused behavior tests,
  the exact no-excuse checker, public API QA, and LOC gates are green.
