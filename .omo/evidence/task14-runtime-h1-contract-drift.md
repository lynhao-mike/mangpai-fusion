# Task14 H1 Runtime Contract-Drift Audit

Date: 2026-08-06 (Asia/Shanghai)
Scope: Wave1 legacy contract preservation
Method: hypothesis-driven Python runtime audit plus frozen-contract regressions

## Verdict

- contract-drift claim: `refuted`
- confidence: `0.98`
- DTO fields/serialization drift: `refuted`
- old three-structure enum/projection drift: `refuted`
- default router schools/semantics drift: `refuted`
- production rule-loader public contract drift: `refuted`
- product/test edits by this reviewer: none

The current shared-worktree runtime preserves all four H1 contracts. This is a
behavioral verdict, not a claim that every implementation file is byte-for-byte
unchanged. In particular, the production loader is structurally modified in
the dirty worktree and the old enum path is untracked, but their observed
public contracts match the frozen authority exactly.

## Authority

The audit used these approved constraints:

- `plans/multi-school-governance-wave1-implementation-2026-08-02.md:84-105`
  freezes `SchoolClaim`, `Claim`, `build_route_plan`, `rule_triggered`, and
  `TenGodStructureKind`; it requires old production rule counts, allowed expert
  systems, and default loading behavior to remain unchanged.
- The same plan at `:246` requires Ditiansui to remain in `_DEFAULT_SCHOOLS`
  and the existing production path while remaining outside the five-peer
  governance registry.
- Task14 checklist item 2 at `:824` requires an explicit search for drift in
  old claim fields, the old enum, default router schools, and production expert
  systems.
- `plans/multi-school-governance-design-2026-08-02.md:581-588` requires no
  regression in the old three structures and fresh Wave1 evidence.

## Debugging Hypotheses

| Hypothesis | Distinguishing runtime evidence | Result |
|---|---|---|
| H1-A: governance fields leaked into either legacy claim DTO or its serialized payload | Exact dataclass field tuple, exact `to_dict()` key tuple, JSON round trip, and forbidden governance-key scan | Refuted |
| H1-B: the 30-item catalog widened or changed the old enum/projection | Runtime enum `(name, value)` tuple plus exact immutable 3-to-3 projection | Refuted |
| H1-C: Wave1 changed the default router school set or made learned routing the default | `RoutingRiskConfig().schools`, default versus explicit-static equality, and emitted school/role rows | Refuted |
| H1-D: the refactored production loader changed systems, paths, counts, statuses, rule identity, candidate admission, or began consuming governance | Allowed systems, default files, per-system counts, total, first IDs, active/candidate scan, and `sys.modules` fanout | Refuted |

The hypotheses have different deciding values and therefore were not collapsed.
No two failed investigation rounds occurred, so Oracle Triple escalation was
not triggered.

## Fresh Runtime Evidence

### Production loader in a fresh process

Exact command form:

```powershell
@'
# Imports only engine.application.production_rule_loader, captures governance
# modules before/after a real default load, then asserts allowed systems,
# default paths, counts, first IDs, active status, and absence of candidate IDs.
'@ | python -
```

The executed assertion harness used these exact expected values:

```text
ALLOWED_PRODUCTION_EXPERT_SYSTEMS == ("ziping", "tiaohou_ditiansui")
DEFAULT_PRODUCTION_FILES == {
  "ziping": "theory/ziping/index.yaml",
  "tiaohou_ditiansui": "theory/tiaohou_ditiansui/index.yaml"
}
counts == {"ziping": 933, "tiaohou_ditiansui": 1108}
total == 2041
first IDs == ZP-PROD-20260622-001/002 and DTS-PROD-20260622-001/002
all statuses == active
candidate IDs == []
governance modules before/after == []/[]
```

Result, with semantic output rather than exit status alone:

```text
exit 0
{"active": true, "allowed": ["ziping", "tiaohou_ditiansui"], "candidate_ids": [], "counts": {"tiaohou_ditiansui": 1108, "ziping": 933}, "default_files": {"tiaohou_ditiansui": "theory/tiaohou_ditiansui/index.yaml", "ziping": "theory/ziping/index.yaml"}, "first_ids": {"tiaohou_ditiansui": ["DTS-PROD-20260622-001", "DTS-PROD-20260622-002"], "ziping": ["ZP-PROD-20260622-001", "ZP-PROD-20260622-002"]}, "governance_after": [], "governance_before": [], "total": 2041}
H1_PRODUCTION_CONTRACT=PASS
```

The fresh load was long but not hung. It completed normally in the next bounded
30-second poll; no indefinite wait or process termination was used.

### DTO, router, enum, and projection in a fresh process

Exact outer command:

```powershell
@'
# ASCII-safe Python assertion harness using \u escapes for all CJK literals.
# Constructs fully populated SchoolClaim and Claim values, asserts field/key
# order and JSON round trips, drives route_schools through default and explicit
# static modes, and loads the real 30-item structure catalog.
'@ | python -
```

Result:

```text
exit 0
H1_DTO_ROUTER_STRUCTURE_MATRIX=PASS
{"claim_dto":{"Claim_fields":["claim_id","school_id","task_id","claim_type","stance","statement","evidence","falsifier","time_window","confidence_basis","applicability_snapshot","domain","polarity","magnitude","confidence","high_risk","target_id"],"Claim_keys":["claim_id","school_id","task_id","claim_type","stance","statement","evidence","falsifier","time_window","confidence_basis","applicability_snapshot","domain","polarity","magnitude","confidence","high_risk","target_id"],"SchoolClaim_fields":["claim_id","school","role_granted_by_l1","domain","claim_type","statement","evidence_refs","confidence","falsifier","dependencies","metadata"],"SchoolClaim_keys":["claim_id","school","role_granted_by_l1","domain","claim_type","statement","evidence_refs","confidence","falsifier","dependencies","metadata"],"governance_fields_added":false,"json_roundtrip":true},"router":{"config_schools":["ziping","ditiansui","duan_jianye","yang_qingjuan","ren_fuhong","gao_dechen"],"default_equals_explicit_static":true,"runtime_roles":[["ziping","lead"],["ditiansui","lead"],["duan_jianye","lead"],["yang_qingjuan","abstain"],["ren_fuhong","lead"],["gao_dechen","abstain"]]},"structures":{"catalog_count":30,"enum":[["FOOD_GOD_CONTROLS_KILLING","\u98df\u795e\u5236\u6740"],["HURTING_OFFICER_CONTROLS_KILLING","\u4f24\u5b98\u9a7e\u6740"],["KILLING_GENERATES_SEAL","\u6740\u5370\u76f8\u751f"]],"projection":{"FOOD_GOD_CONTROLS_KILLING":"food_god_controls_killing","HURTING_OFFICER_CONTROLS_KILLING":"hurting_officer_controls_killing","KILLING_GENERATES_SEAL":"killing_generates_seal"}}}
```

The DTO assertions additionally checked exact nested evidence serialization,
`TimeWindow` serialization, `applicability_snapshot`, and absence of
`governance_claim_id`, `school_view_id`, `fact_snapshot_id`, `adapter_version`,
and `loss_items` from both legacy payloads.

### Harness false failure and confirmation

The first combined stdin probe returned:

```text
exit 1
Traceback (most recent call last):
  File "<stdin>", line 141, in <module>
AssertionError
```

This was investigated rather than classified as product drift. The decisive
transport toggle was:

```powershell
@'
from engine.predicates.ten_god_structure_types import TenGodStructureKind
piped_literal = "<literal CJK text>"
escaped_literal = "\u98df\u795e\u5236\u6740"
print(f"piped={ascii(piped_literal)}")
print(f"escaped={ascii(escaped_literal)}")
print(f"runtime={ascii(TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING.value)}")
print(f"piped_matches={piped_literal == TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING.value}")
print(f"escaped_matches={escaped_literal == TenGodStructureKind.FOOD_GOD_CONTROLS_KILLING.value}")
'@ | python -
```

```text
exit 0
piped='????'
escaped='\u98df\u795e\u5236\u6740'
runtime='\u98df\u795e\u5236\u6740'
piped_matches=False
escaped_matches=True
```

Changing only the harness representation from literal CJK to ASCII `\u`
escapes toggled the assertion from failure to pass. Root cause: PowerShell's
stdin pipeline replaced literal CJK source text with question marks. This is a
confirmed probe-transport defect, not a product defect.

## Targeted Regressions

Primary bounded regression command:

```text
python -m pytest tests/governance/test_wave1_baseline_contract.py tests/governance/test_structure_catalog.py::test_legacy_projection_maps_only_current_three_structure_kinds tests/governance/test_structure_catalog_integrity.py::test_catalog_constructor_rejects_forged_digest_projection_and_entries tests/predicates/test_ten_god_structures.py tests/decision/test_learnable_routing.py::test_static_mode_remains_default_and_learned_mode_is_explicit tests/test_production_rule_loader.py::test_load_default_production_library_loads_ziping_and_ditiansui tests/test_production_rule_loader.py::test_production_loader_rejects_bypass_candidate_path tests/test_production_rule_loader.py::test_production_loader_rejects_duplicate_expert_system -q
exit 0
24 passed, 1 warning in 19.96s
```

Secondary DTO/serialization and frozen-byte regression command:

```text
python -m pytest tests/claims/test_claim_engine.py::test_claim_contract_rejects_dangling_evidence_and_has_stable_identity tests/ziping_career/test_production_isolation.py::test_public_schema_has_not_been_extended_for_slice tests/yang_marriage/test_static_isolation.py::test_public_contract_fields_and_production_rule_bytes_are_unchanged -q
exit 0
3 passed, 1 warning in 1.33s
```

Both warnings are the existing deprecation from
`engine/application/pipeline_runner.py:11` for
`engine.application.dual_engine_adapter`.

## Drift Classification By Surface

### Legacy claim DTOs

`SchoolClaim` remains 11 fields and `Claim` remains 17 fields in the exact
frozen order. Their `to_dict()` outputs use exactly those keys, nested tuples
become JSON-compatible lists, the mapping proxy becomes a plain mapping, and
JSON round trips reproduce the payloads. No governance-envelope field leaked
into either DTO.

Result: `refuted`.

### Old three structures

The runtime enum remains exactly:

```text
FOOD_GOD_CONTROLS_KILLING = \u98df\u795e\u5236\u6740
HURTING_OFFICER_CONTROLS_KILLING = \u4f24\u5b98\u9a7e\u6740
KILLING_GENERATES_SEAL = \u6740\u5370\u76f8\u751f
```

The catalog contains 30 entries but projects only those three old enum members
to their same-name stable IDs. No catalog-only entry was backfilled into the
legacy enum.

Result: `refuted`.

### Default router

`RoutingRiskConfig().schools` remains:

```text
ziping, ditiansui, duan_jianye, yang_qingjuan, ren_fuhong, gao_dechen
```

The default runtime result equals an explicit `routing_mode="static"` result
and emits those six schools in that order. Learned routing remains opt-in.

Result: `refuted`.

### Production loader

The default loader exposes only `ziping` and `tiaohou_ditiansui`, loads the
approved two files, returns `933 + 1108 = 2041` active rules, preserves the
first canonical production IDs, admits no candidate IDs, and loads no
`engine.governance` module.

Result: `refuted`.

## Dirty Worktree And Cleanup

Scoped status before writing this evidence:

```text
git status --short -- engine/claims/domain.py engine/decision/models.py engine/predicates/ten_god_structure_types.py engine/decision/l1_school_router.py engine/application/production_rule_loader.py .omo/evidence/task14-runtime-h1-contract-drift.md
 M engine/application/production_rule_loader.py
?? engine/predicates/ten_god_structure_types.py
```

`engine/claims/domain.py`, `engine/decision/models.py`, and
`engine/decision/l1_school_router.py` have no scoped status entry. The loader's
current tracked diff is `77` additions and `414` deletions, consistent with a
large structural split. This reviewer did not attribute that dirty change to
Wave1 and did not modify or revert it; runtime evidence shows its frozen public
contract remains intact.

Final process audit command:

```powershell
$matches=@(Get-CimInstance Win32_Process | Where-Object { ($_.Name -match '^(python|pythonw)(\.exe)?$') -and ($_.CommandLine -match 'test_wave1_baseline_contract|test_ten_god_structures|test_production_rule_loader|H1_RUNTIME|load_default_production_library|test_claim_engine') }); Write-Output "matching_h1_processes=$($matches.Count)"
```

```text
exit 0
matching_h1_processes=0
```

No server, port, container, temp script, debugger, breakpoint, environment
override, or verification process remains. No reset, revert, stash, checkout,
delete, process termination, product edit, test edit, or unrelated edit was
performed.
