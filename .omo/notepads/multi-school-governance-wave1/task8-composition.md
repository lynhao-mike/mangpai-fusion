# Task 8 Composition Notepad

## Decisions

- Composition remains a separate frozen `CompositionResult`, never a synthetic school claim.
- Formal YAML ships one `synthetic_only` template; production authority returns a typed refusal.
- `independent_support` requires distinct claim variants and distinct school IDs.
- `composition_templates` is recognized as the only optional top-level extension by legacy fact and school loaders; the composition loader requires it.
- Raw YAML string parsers return typed errors through `Never`-typed rejection, without `assert_never` on unbounded input.

## Changed Files

- `engine/governance/fact_certification_loader.py`
- `engine/governance/school_registry_loader.py`

## Rework Evidence

- Pre-edit invalid-loader characterization: `CERTIFICATION.LEVEL`, `CERTIFICATION.STATUS`, `CAPABILITY.CLAIM_KIND`, `CAPABILITY.EVIDENCE_GRADE`, `CAPABILITY.ROLE`, `CAPABILITY.PUBLICATION_STATUS`.
- Post-edit loader focused: `24 passed`.
- Task8 focused: `27 passed`.
- Task1-8 joint: `135 passed, 1 existing warning`.
- Public loader replay preserved every characterized issue code.

## Pointers

- Artifact: `.omo/start-work/artifacts/task8-composition.txt`
- Code review: `.omo/evidence/task8-composition-code-review.md`
- Final gate review: `.omo/evidence/task8-composition-gate-review.md`
- Manual QA: `.omo/evidence/task8-composition-manual-qa.md`

## Environment And Cleanup

- `basedpyright`, `pyright`, and `uv` are unavailable; this is the remaining environment limitation.
- The shared worktree is intentionally dirty/untracked. No reset, checkout, revert, or commit was performed.
- No-excuse is clean for the 14 actual Task8 scoped source/test paths. The untouched Task4 fact-certification test remains outside this rework scope.
