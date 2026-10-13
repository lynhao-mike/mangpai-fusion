# Task12 Static Isolation Notepad

Implemented architecture/static isolation guards for Wave1 Task12 without modifying product code.

Files changed:
- `tests/test_architecture_dependencies.py`
- `tests/governance/test_static_isolation.py`
- `tests/governance/static_isolation_scanner.py`
- `tests/governance/static_isolation_content.py`
- `.omo/start-work/artifacts/task12-static-isolation.txt`
- `.omo/notepads/multi-school-governance-wave1/task12-static-isolation.md`

Key guard surfaces:
- `engine/governance` cannot import `engine.application`, `engine.infrastructure`, or `tools`.
- `engine/governance` cannot reference report, feedback, learning, V5 runner, label, case, prediction, or sample-hit paths.
- Existing default pipelines, report templates, and feedback entrypoints cannot import or directly reference `engine.application.governance_shadow_runner`.
- `theory/multi-school-governance-v1.yaml` is parsed as YAML and checked for historical case IDs, prediction/result labels, sample hit results, and absolute paths.
- School View adapter surfaces cannot call `FactSnapshot`, `build_fact_snapshot`, or `build_governance_fact_snapshot`.
- New governance/governance-shadow code cannot read system time while deciding liunian.
- Legacy Yang static protection remains required by exact command and guard-presence check.

Final evidence artifact:
- `.omo/start-work/artifacts/task12-static-isolation.txt`
