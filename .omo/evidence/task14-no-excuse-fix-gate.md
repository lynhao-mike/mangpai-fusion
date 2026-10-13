# Task14 No-Excuse Repair Gate Review

Date: 2026-08-06 (Asia/Shanghai)
Role: independent read-only product/test gate reviewer

## AdversarialVerify

- verdict: `confirmed`
- confidence: `0.99`
- blockers: none
- scope: current shared-worktree behavior and static quality of
  `engine/governance/fact_certification.py` and
  `engine/governance/school_registry.py`
- write scope: this evidence file only; no product or test file was edited

The Task14 no-excuse repair is confirmed. The original four
`missing-assert-never` findings are closed without adding an exhaustiveness
claim to either open string boundary. The exact bundled checker, focused tests,
Ruff check, Ruff format check, pure-LOC gate, repeated narrow tests, and a fresh
public-API adversarial process all passed.

## Authority And Inputs Read

- `.omo/plans/multi-school-governance-wave1-execution-2026-08-03.md`
- `plans/multi-school-governance-wave1-implementation-2026-08-02.md`, Task 14
- `engine/governance/fact_certification.py`
- `engine/governance/school_registry.py`
- `engine/governance/fact_values.py` for the authoritative `FactLevel` set
- `engine/governance/registries.py` and `engine/governance/__init__.py` for the
  public facade
- `tests/governance/test_fact_certification_registry.py`
- `tests/governance/test_school_registry.py`
- `tests/governance/test_wave1_baseline_contract.py`
- `.omo/evidence/task14-no-excuse-fix.md`

## Static Review

### Exhaustive FactLevel handling

`FactLevel` has exactly four members:

- `CANONICAL_OBSERVATION`
- `CANDIDATE_DERIVED`
- `CERTIFIED_TECHNICAL`
- `CERTIFIED_CROSS_SCHOOL`

Both target matches explicitly enumerate all four members separately and end
with `case unreachable: assert_never(unreachable)`:

- `CertificationIdentity.__post_init__`, lines 50-68
- `FactCertification.__post_init__`, lines 149-177

The L0 and L1 members fail closed with `CERTIFICATION.LEVEL`. L2A and L2B are
accepted at the identity boundary, after which `FactCertification` enforces
their distinct review constraints. No grouped enum pattern, catch-all runtime
raise, cast, ignored type, suppression, or widened annotation remains at these
sites.

### Open arbitrary string handling

The two school-input sites correctly do not use `assert_never` because `str` is
an open set:

- `normalize_school_input` validates nonblank text, accepts only four exact
  aliases or one of five exact canonical IDs, and otherwise raises typed
  `SCHOOL.INPUT_UNKNOWN`.
- `SchoolRegistry.lookup_school` validates nonblank text, returns a peer only
  for an exact canonical ID, returns the legacy compatibility type only for
  exact `ditiansui`, and returns `UnknownSchool` for every other nonblank
  string.

Aliases are boundary-only. Registry lookup deliberately does not guess or
normalize them. Ditiansui is not admitted to the peer set.

## Exact Commands And Results

Environment:

```text
python --version
Python 3.14.5

python -m pytest --version
pytest 8.4.2
```

Exact bundled no-excuse checker:

```text
python C:/Users/Administrator/.codex/plugins/cache/sisyphuslabs/omo/4.13.0/skills/programming/scripts/python/check-no-excuse-rules.py engine/governance/fact_certification.py engine/governance/school_registry.py
exit 0
no violations in 2 file(s)
```

Focused fact certification, school registry, and Wave1 baseline tests:

```text
python -m pytest tests/governance/test_fact_certification_registry.py tests/governance/test_school_registry.py tests/governance/test_wave1_baseline_contract.py -q
exit 0
29 passed, 1 warning in 17.79s
```

The warning is the existing deprecation from
`engine/application/pipeline_runner.py:11` for
`engine.application.dual_engine_adapter`.

Ruff:

```text
python -m ruff check engine/governance/fact_certification.py engine/governance/school_registry.py
exit 0
All checks passed!

python -m ruff format --check engine/governance/fact_certification.py engine/governance/school_registry.py
exit 0
2 files already formatted
```

Pure LOC, counting nonblank and non-comment lines:

```powershell
foreach ($file in @('engine/governance/fact_certification.py','engine/governance/school_registry.py')) { $lines=Get-Content -Encoding utf8 $file; $pure=($lines | Where-Object { $_ -notmatch '^\s*$' -and $_ -notmatch '^\s*#' }).Count; Write-Output "$file physical=$($lines.Count) pure=$pure" }
```

```text
exit 0
engine/governance/fact_certification.py physical=255 pure=229
engine/governance/school_registry.py physical=280 pure=231
```

Both files are below the 250 pure-LOC ceiling and in the 200-250 warning band.

Narrow fresh-process flake probe, executed twice with the same command:

```text
python -m pytest tests/governance/test_fact_certification_registry.py::test_loads_published_l2a_and_returns_unsupported_for_exact_missing_version tests/governance/test_school_registry.py::test_ditiansui_is_legacy_compatibility_not_a_peer_role tests/governance/test_school_registry.py::test_boundary_aliases_normalize_only_exact_explicit_input -q
run 1: exit 0, 6 passed in 0.55s
run 2: exit 0, 6 passed in 0.76s
```

## Fresh-Process Public API Matrix

Exact outer command: the following PowerShell here-string was piped to a new
`python -` process.

```powershell
@'
from pathlib import Path

from engine.governance import DigestRef, FactLevel, stable_object_id
from engine.governance.registries import (
    CertificationContractError,
    CertificationIdentity,
    FactCertification,
    LegacyCompatibilitySource,
    PeerSchool,
    PublicationStatus,
    SchoolRegistryContractError,
    SchoolRegistryIssueCode,
    UnknownSchool,
    load_school_registry,
    normalize_school_input,
)

registry = load_school_registry(workspace_root=Path.cwd())
canonical_ids = (
    "ziping", "gao_dechen", "duan_jianye", "yang_qingjuan", "ren_fuhong"
)
aliases = {
    "gao": "gao_dechen", "duan": "duan_jianye",
    "yang": "yang_qingjuan", "ren": "ren_fuhong",
}

for school_id in canonical_ids:
    assert normalize_school_input(school_id) == school_id
    result = registry.lookup_school(school_id)
    assert isinstance(result, PeerSchool)
    assert result.school_id == school_id

for raw, canonical in aliases.items():
    assert normalize_school_input(raw) == canonical
    result = registry.lookup_school(raw)
    assert isinstance(result, UnknownSchool)
    assert result.requested_id == raw
    assert result.issue_code is SchoolRegistryIssueCode.UNKNOWN_SCHOOL

legacy = registry.lookup_school("ditiansui")
assert isinstance(legacy, LegacyCompatibilitySource)
assert legacy.source_id == "ditiansui"
try:
    normalize_school_input("ditiansui")
except SchoolRegistryContractError as error:
    assert error.issue_code == "SCHOOL.INPUT_UNKNOWN"
else:
    raise AssertionError("ditiansui normalized into the peer set")

adversarial = (
    "unknown_school", "GAO", "Ziping", " gao", "gao ", "gao_extra",
    "gao/dechen", "../ziping", "ditiansui_extra", "ziping\n",
    "gao\u200b", "${{7*7}}", "__class__", "ren_fuhong_extra", "\x00gao",
)
for raw in adversarial:
    result = registry.lookup_school(raw)
    assert isinstance(result, UnknownSchool)
    assert result.requested_id == raw
    assert result.issue_code is SchoolRegistryIssueCode.UNKNOWN_SCHOOL
    try:
        normalize_school_input(raw)
    except SchoolRegistryContractError as error:
        assert error.issue_code == "SCHOOL.INPUT_UNKNOWN"
    else:
        raise AssertionError(f"adversarial school normalized: {raw!r}")

for raw in ("", " ", "\t", "\n"):
    for operation in (normalize_school_input, registry.lookup_school):
        try:
            operation(raw)
        except SchoolRegistryContractError as error:
            assert error.issue_code == "SCHOOL.TEXT_REQUIRED"
        else:
            raise AssertionError(f"blank school accepted: {raw!r}")

accepted_identities = []
for level in FactLevel:
    try:
        identity = CertificationIdentity(
            level, "chart.ten_god_map", "engine.ten_god", "1.0.0", "facts/v1"
        )
    except CertificationContractError as error:
        assert level in (
            FactLevel.CANONICAL_OBSERVATION, FactLevel.CANDIDATE_DERIVED
        )
        assert error.issue_code == "CERTIFICATION.LEVEL"
    else:
        assert level in (
            FactLevel.CERTIFIED_TECHNICAL, FactLevel.CERTIFIED_CROSS_SCHOOL
        )
        accepted_identities.append(identity)

assert [identity.fact_level for identity in accepted_identities] == [
    FactLevel.CERTIFIED_TECHNICAL, FactLevel.CERTIFIED_CROSS_SCHOOL
]

for identity in accepted_identities:
    refs = (
        () if identity.fact_level is FactLevel.CERTIFIED_TECHNICAL
        else ("review:ren_fuhong:r1", "review:ziping:r1")
    )
    registration_id = str(stable_object_id(
        "fact_certification",
        (identity.material(), PublicationStatus.PUBLISHED.value, refs),
    ))
    digest = DigestRef.from_material((
        "governance.fact-certification.v1", registration_id,
        *identity.material(), PublicationStatus.PUBLISHED.value, refs,
    ))
    certification = FactCertification(
        registration_id, identity, PublicationStatus.PUBLISHED, digest, refs
    )
    assert certification.identity.fact_level is identity.fact_level

for raw_level in (
    "certified_technical", "CERTIFIED_TECHNICAL", " certified_technical",
    "candidate_derived_extra", "unknown", "",
):
    try:
        CertificationIdentity(
            raw_level, "chart.ten_god_map", "engine.ten_god", "1.0.0", "facts/v1"
        )
    except CertificationContractError as error:
        assert error.issue_code == "CERTIFICATION.LEVEL"
    else:
        raise AssertionError(f"raw fact-level string accepted: {raw_level!r}")

print(
    "PUBLIC_API_MATRIX=PASS "
    f"fact_levels={len(tuple(FactLevel))} canonical={len(canonical_ids)} "
    f"aliases={len(aliases)} adversarial={len(adversarial)} blanks=4"
)
'@ | python -
```

Result:

```text
exit 0
PUBLIC_API_MATRIX=PASS fact_levels=4 canonical=5 aliases=4 adversarial=15 blanks=4
```

The process asserted, rather than merely printed, every accepted type,
canonical value, typed exception code, unknown result, legacy result, and
L2A/L2B certification construction outcome.

## Adversarial Classes

| Class | Result |
|---|---|
| Enum expansion / missing exhaustiveness | Confirmed closed: both matches enumerate four members and terminate with `assert_never`. |
| L0/L1 impersonating certified facts | Confirmed fail closed with `CERTIFICATION.LEVEL`. |
| Raw strings impersonating `FactLevel` | Confirmed fail closed, including the exact enum value spelling. |
| Alias leakage into registry identity | Confirmed fail closed as `UnknownSchool`; aliases work only at normalization. |
| Case, prefix, suffix, whitespace, path-like, template-like, NUL, and zero-width strings | Confirmed no guessing; normalization raises `SCHOOL.INPUT_UNKNOWN`, lookup returns typed `UnknownSchool`. |
| Empty and whitespace-only strings | Confirmed fail closed with `SCHOOL.TEXT_REQUIRED`. |
| Ditiansui peer promotion | Confirmed absent; exact lookup yields `LegacyCompatibilitySource` and normalization rejects it. |
| Misleading success output | Mitigated by exit-code checks plus internal assertions on types, values, and issue codes. |
| Flaky focused behavior | Mitigated by two additional fresh runs, both `6 passed`. |
| Dirty shared worktree | Preserved; target product files and tests remain untracked and were not reset, reverted, stashed, checked out, or edited. |
| Hung verification command | None; every command exited normally. |

## Cleanup And Residual Risk

Final process audit:

```powershell
$matches = @(Get-CimInstance Win32_Process | Where-Object { ($_.Name -match '^(python|pythonw|ruff)(\.exe)?$') -and ($_.CommandLine -match 'fact_certification|school_registry|test_wave1_baseline_contract|check-no-excuse-rules') }); Write-Output "matching_verification_processes=$($matches.Count)"
```

```text
exit 0
matching_verification_processes=0
```

No server, port, container, temporary harness file, or verification process was
left running. No reset, revert, stash, checkout, deletion, process termination,
or unrelated edit was performed.

Residual notes do not change the verdict:

- Both production modules are untracked in a heavily dirty shared worktree, so
  this gate confirms the current filesystem behavior and quality, not patch
  provenance.
- Both modules are in the 200-250 pure-LOC warning band. Future line-adding
  work should split the relevant responsibility before expansion.
- The repository tests do not directly enumerate every `FactLevel` at the two
  repaired constructors; the fresh-process assertion matrix closes that gate
  for this review.
