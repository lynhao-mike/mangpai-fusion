# Task14 H2 runtime side-effect audit

Date: 2026-08-06

## Verdict

**CONFIRMED**, narrowly, for the strict Task11 import-isolation invariant.

A fresh import of `engine.application.governance_shadow_runner` necessarily executes
`engine.application.__init__`; line 4 of that package initializer eagerly imports
`engine.application.pipeline_runner`. The same fresh import also loads
`engine.v5.runner` through package fanout. Therefore the requirement "no
production-runner imports" is not met, even though the shadow module has no direct
production import and is not exported or registered in a default pipeline.

The operational side-effect hypotheses were **REFUTED** by the runtime probes:

- no default runner-registry mutation;
- no production-rule cache mutation;
- no report, feedback, learning, conditional-learning, production-service, or
  `engine.pipeline` module import;
- no report, feedback, learning, publication, or filesystem write observed on
  shadow import/run;
- no stale result after a typed fail-closed run;
- no exit-zero semantic failure in either the success or conflict result.

This is an import-boundary defect, not evidence that the shadow runner executes,
publishes, learns from, renders, or writes production output.

## Authority and static wiring

Task11 in `plans/multi-school-governance-wave1-implementation-2026-08-02.md`
requires the shadow runner to remain opt-in, avoid filesystem/learning/registry
writes, avoid report/feedback/L7-L9/production-runner imports, and avoid default
pipeline registration.

Exact command:

```powershell
rg -n "governance_shadow_runner|run_governance_shadow" engine\application\__init__.py engine\pipeline.py engine\application\pipeline_runner.py engine\application\production_service.py engine\claims tools templates 2>$null; if ($LASTEXITCODE -eq 1) { 'NO_MATCHES'; exit 0 }
```

Result: exit 0, `NO_MATCHES`.

The shadow runner is not referenced by the searched default/production entrypoints,
claims wiring, tools, or templates. `engine.application.__all__` also omits it.

The relevant eager package wiring is:

```text
engine/application/__init__.py:4:
from engine.application.pipeline_runner import run_pipeline, run_pipeline_e2e
```

## Fresh import probe

Exact command:

```powershell
@'
import json,sys
before=set(sys.modules)
from engine.application.governance_shadow_runner import run_governance_shadow
app=sys.modules["engine.application"]
after=set(sys.modules)
watched={"engine.pipeline","engine.application.pipeline_runner","engine.application.production_service","engine.v5.runner","engine.learning","tools.render_report","tools.feedback_ingest","tools.feedback_loop","tools.conditional_learning"}
print(json.dumps({"shadow_exported":"run_governance_shadow" in app.__all__,"watched_loaded":sorted(name for name in after-before if name in watched or name.startswith("engine.learning."))},sort_keys=True))
'@ | python -B -
```

Result: exit 0.

```json
{"shadow_exported": false, "watched_loaded": ["engine.application.pipeline_runner", "engine.v5.runner"]}
```

This fresh process establishes causality: the production-runner modules were absent
before the direct shadow-submodule import and present afterward. No forbidden
report/feedback/learning/production-service module was present.

## Runtime mutation and write probe

Exact command:

```powershell
@'
import json, os, sys, tempfile
from dataclasses import replace
from pathlib import Path

repo = Path.cwd().resolve()
temp = Path(tempfile.mkdtemp(prefix="task14-h2-shadow-"))
os.chdir(temp)
sys.dont_write_bytecode = True
write_events = []

def audit(event, args):
    if event == "open":
        path, mode, flags = args
        mode_text = mode or ""
        if any(ch in mode_text for ch in "wax+") or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            write_events.append((event, str(path), mode_text, flags))
    elif event in {"os.mkdir", "os.remove", "os.rename", "os.replace", "os.rmdir", "os.link", "os.symlink", "os.truncate"}:
        write_events.append((event, tuple(str(item) for item in args)))

sys.addaudithook(audit)

from engine.claims.runner_registry import DEFAULT_RUNNER_REGISTRY
runner_before = tuple(sorted((school, task, fn.__module__, fn.__name__) for (school, task), fn in DEFAULT_RUNNER_REGISTRY._runners.items()))
modules_before = set(sys.modules)

from engine.application.governance_shadow_runner import run_governance_shadow
import engine.application as application
from engine.application import production_rule_loader
from engine.application.governance_shadow_types import GovernanceShadowRequest, SchoolViewOutcome
from engine.decision.models import ChartFactLedger, RawWenzhenPayload, SchoolClaim
from engine.governance import ClaimEvidenceGrade, ClaimKind, ClaimReferenceCategory, DigestRef, FactConflictContext, GovernanceReferenceCatalog, ReferenceRegistration
from engine.governance.registries import CapabilityIdentity, CapabilityRegistration, CapabilityRole, FactCertificationRegistry, LegacyCompatibilitySource, PeerSchool, PublicationStatus, SchoolRegistry

catalog = GovernanceReferenceCatalog((
    ReferenceRegistration(ClaimReferenceCategory.SCHOOL_REASON, "reason:ziping", "legacy-v1"),
    ReferenceRegistration(ClaimReferenceCategory.SOURCE_RULE, "rule:structure", "legacy-v1"),
))
registry = SchoolRegistry(
    tuple(PeerSchool(s) for s in ("ziping", "gao_dechen", "duan_jianye", "yang_qingjuan", "ren_fuhong")),
    (LegacyCompatibilitySource("ditiansui"),),
    (CapabilityRegistration(CapabilityIdentity("ziping", "structure.assessment", ClaimKind.STRUCTURE, ClaimEvidenceGrade.INFERENTIAL, "governance/v1"), CapabilityRole.LEAD, PublicationStatus.PUBLISHED),),
)
certs = FactCertificationRegistry(())
from engine.application.governance_shadow_types import GovernanceShadowDependencies
deps = GovernanceShadowDependencies(catalog, registry, certs, "governance/v1")
claim = SchoolClaim(
    claim_id="legacy-ziping", school="ziping", role_granted_by_l1="lead", domain="structure",
    claim_type="structure_claim", statement="ziping structure view",
    evidence_refs=["reason:ziping", "rule:structure"], confidence=0.64, falsifier="",
    metadata={"task_id":"structure.assessment", "stance":"support", "temporal_scope":"natal", "reference_version":"legacy-v1"},
)
request = GovernanceShadowRequest(
    case_id="C-SHADOW-001",
    raw_payload=RawWenzhenPayload(raw_text="fixture", raw_hash="raw-shadow-001"),
    chart=ChartFactLedger(
        sex_marker="qian",
        four_pillars={"year":"jiazi", "month":"yichou", "day":"bingyin"},
        dayun_steps=[{"ganzhi":"wuchen", "start_year":2018, "end_year":2027}],
        liunian_steps=[{"year":2026, "ganzhi":"bingwu"}],
        raw_source_hash="raw-shadow-001",
    ),
    target_year=2026,
    calculator_version="governance-fact-builder-v1",
    school_views=(SchoolViewOutcome("ziping", (claim,)),),
)
first = run_governance_shadow(request, deps)
second = run_governance_shadow(request, deps)
conflict = FactConflictContext("fact:shared", DigestRef.from_material(("first",)).value, DigestRef.from_material(("second",)).value)
failed = run_governance_shadow(replace(request, fact_conflicts=(conflict,)), deps)
third = run_governance_shadow(request, deps)

runner_after = tuple(sorted((school, task, fn.__module__, fn.__name__) for (school, task), fn in DEFAULT_RUNNER_REGISTRY._runners.items()))
forbidden = sorted(name for name in sys.modules if name in {
    "engine.pipeline", "engine.application.production_service", "engine.learning",
    "tools.render_report", "tools.feedback_ingest", "tools.feedback_loop", "tools.conditional_learning"
} or name.startswith("engine.learning."))
temp_entries = sorted(str(path.relative_to(temp)) for path in temp.rglob("*"))
result = {
    "application_exports_shadow": "run_governance_shadow" in application.__all__,
    "new_modules": len(set(sys.modules) - modules_before),
    "forbidden_modules": forbidden,
    "package_fanout": sorted(name for name in sys.modules if name in {"engine.application.pipeline_runner", "engine.v5.runner"}),
    "production_cache_is_none": production_rule_loader._DEFAULT_LIBRARY_CACHE is None,
    "runner_registry_unchanged": runner_before == runner_after,
    "success": {
        "status": first.status,
        "decision": first.arbitration.decision if first.arbitration else None,
        "retained": list(first.arbitration.retained_claim_ids) if first.arbitration else [],
        "issues": [issue.issue_code for issue in first.issues],
        "digest": first.result_digest,
    },
    "deterministic": first.to_canonical() == second.to_canonical() and first.result_digest == second.result_digest,
    "conflict": {"status": failed.status, "arbitration": failed.arbitration is not None, "issues": [issue.issue_code for issue in failed.issues]},
    "post_failure_stable": first.to_canonical() == third.to_canonical() and first.result_digest == third.result_digest,
    "write_events": write_events,
    "temp_entries": temp_entries,
}
print(json.dumps(result, ensure_ascii=True, sort_keys=True))
os.chdir(repo)
try:
    temp.rmdir()
except OSError:
    pass
'@ | python -B -
```

Result: exit 0.

```json
{
  "application_exports_shadow": false,
  "conflict": {
    "arbitration": false,
    "issues": ["ARBITRATION.FACT_CONFLICT"],
    "status": "fail_closed"
  },
  "deterministic": true,
  "forbidden_modules": [],
  "new_modules": 41,
  "package_fanout": [
    "engine.application.pipeline_runner",
    "engine.v5.runner"
  ],
  "post_failure_stable": true,
  "production_cache_is_none": true,
  "runner_registry_unchanged": true,
  "success": {
    "decision": "consensus",
    "digest": "605c74a8111a9ae11bc02a0354dcdd852f0bf4e5d7682cd079c55c60e7c83979",
    "issues": [],
    "retained": [
      "governance_claim:7866349838861826a4e525c1cbc8b665d4c1674b9529be59ea7373aeb33678f4"
    ],
    "status": "ok"
  },
  "temp_entries": [],
  "write_events": []
}
```

The success result was semantically `ok/consensus`, retained exactly one claim,
had no issues, and was deterministic. The explicit conflict was semantically
`fail_closed`, had no arbitration result, and emitted the typed issue. A subsequent
success was byte-for-byte canonical/digest equivalent to the first success.

## Formal-registry probe

Exact command:

```powershell
@'
import json, runpy
from dataclasses import replace
from engine.governance.registries import load_fact_certification_registry, load_school_registry
ns = runpy.run_path("tests/application/test_governance_shadow_runner.py")
deps = replace(ns["_dependencies"](), school_registry=load_school_registry(), certification_registry=load_fact_certification_registry())
result = ns["run_governance_shadow"](ns["_request"](), deps)
print(json.dumps({"status":result.status,"claims":len(result.claims),"school_capabilities":len(deps.school_registry.capabilities),"certifications":len(deps.certification_registry.registrations),"decision":result.arbitration.decision if result.arbitration else None,"retained":list(result.arbitration.retained_claim_ids) if result.arbitration else [],"gates":[g.gate for g in result.arbitration.gate_trace] if result.arbitration else [],"issues":[i.issue_code for i in result.issues],"digest":result.result_digest},sort_keys=True))
'@ | python -B -
```

Result: exit 0.

```json
{"certifications": 0, "claims": 0, "decision": "abstain", "digest": "b311c63fb9d4126d93baeb21eb1c4107b13934dc30fab38d490c4813bcc6c6da", "gates": ["eligibility", "temporal", "evidence", "independence", "counterevidence", "applicability", "decision"], "issues": [], "retained": [], "school_capabilities": 0, "status": "ok"}
```

The real formal registry behavior is `ok/abstain`, not `reject_all`; exit 0 matched
the returned semantic fields.

## Regression result

Exact command:

```powershell
python -m pytest tests/application/test_governance_shadow_runner.py tests/governance/test_static_isolation.py tests/test_architecture_dependencies.py -q
```

Result: exit 0, `31 passed, 1 warning in 3.75s`. The warning is the existing
deprecation warning emitted by `engine.application.pipeline_runner` importing
`engine.application.dual_engine_adapter`.

The passing direct-import AST test is insufficient to catch this finding because
it examines imports written in `governance_shadow_runner.py`, not the eager imports
executed first by `engine.application.__init__`.

## Failed harnesses and Oracle limitation

The first combined harness incorrectly asserted that the empty formal registry
would decide `reject_all`; the observed decision was `abstain`. It also attempted
to remove its current working directory on Windows. The exact leftover directory,
`C:\Users\Administrator\AppData\Local\Temp\task14-h2-shadow-iiggas2r`, was verified
empty and removed with `[System.IO.Directory]::Delete(...)`. No repository data was
deleted.

The corrected second harness restored the repository current directory in a
`finally` block but stopped at stdin line 61. The diagnostic probe above replaced
late assertions with named observables and then established that the core result,
mutation, import, write-event, and temp-tree checks were clean.

After two failed investigation rounds, three independent Oracle passes were
started for obvious, boundary, and invariant review. All three failed before
producing analysis with the same service result: `429 Too Many Requests`, retry
limit exceeded. This limits independent review but does not make the direct fresh
process observations inconclusive.

## Cleanup and final process state

Exact commands and results:

```powershell
$dirs = Get-ChildItem -LiteralPath $env:TEMP -Directory -Filter 'task14-h2-shadow-*' -ErrorAction SilentlyContinue; if ($dirs) { $dirs.FullName } else { 'NO_TASK14_TEMP_DIRS' }
```

Result: `NO_TASK14_TEMP_DIRS`.

```powershell
$matches = Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(python|pytest)(\.exe)?$' -and $_.CommandLine -match 'governance_shadow_runner|test_governance_shadow_runner|task14-h2-shadow' }; if ($matches) { $matches | Select-Object ProcessId,Name,CommandLine | Format-List | Out-String } else { 'NO_H2_PYTHON_OR_PYTEST_PROCESSES' }
```

Result: `NO_H2_PYTHON_OR_PYTEST_PROCESSES`.

The repository was already heavily dirty. No existing product, test, metadata, or
repository data was reset, reverted, stashed, checked out, deleted, or intentionally
modified by this audit. The only authorized audit write is this evidence file.
