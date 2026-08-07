# Task10 Structure Catalog Manual QA

Verdict: PASS

Surface: public Python loader/API and public constructors from `engine.governance.structure_catalog`, `engine.governance.structure_catalog_types`, `engine.predicates.ten_god_structure_types`, plus temp YAML mutations under OS temp. Product files were read-only. No pytest-only claim.

Harness invocation: `@'<bounded Python harness>'@ | python -` from `F:\多流派新思路` in PowerShell. Harness exit: `0`.

Harness summary:
- scenarioCount: 29
- failureCount: 0
- catalogDigest: `1b746ca407ca17b653646fdaeb0f289acaeaa440bce780a81cc52ff70a3da8bc`
- entryDigestSample: `officer_generates_seal=94f5193e4d6da974b229ad539c9e681c68df2dac5a0a9ba9ddd83bb4b97811e9`
- production rule count before/after catalog load: `2041/2041`
- fact certification registration count before/after catalog load: `0/0`
- temp cleanup: no `structure_catalog_qa_*` temp dirs remained; harness started no child process.

## manualQa

### surfaceEvidence

| scenario id | criterion reference | surface | exact invocation | expected | actual | exit | verdict | artifactRefs |
|---|---|---|---|---|---|---:|---|---|
| formal-30 | C1 exactly30 unique IDs/keys | public loader | `python - <<HARNESS: load_structure_catalog(DEFAULT_STRUCTURE_CATALOG_PATH)` | 30 entries, 30 unique IDs, 30 unique canonical keys | `count=30; uniqueIds=30; uniqueCanonicalKeys=30` | 0 | PASS | qa-report |
| fields-closed | C2 required fields and closed statuses | public loader | `python - <<HARNESS: inspect typed catalog entries` | all required nonempty; status enums typed | `requiredOk=True; sourceStatuses=composite,direct,normalized,review; implementationStatuses=catalog_only_candidate,catalog_only_review,current_implemented` | 0 | PASS | qa-report |
| legacy-current | C3 exact legacy projection and only current three | public loader | `python - <<HARNESS: inspect legacy_projection/current entries` | 3 legacy mappings to exact TenGodStructureKind targets; only 3 current | current IDs are `food_god_controls_killing`, `hurting_officer_controls_killing`, `killing_generates_seal`; remaining catalog entries non-production | 0 | PASS | qa-report |
| digest-order | C4 order permutation digest stable | public loader + temp YAML | `python - <<HARNESS: reverse structures then load_structure_catalog(temp)` | catalog digest unchanged | baseline and reordered digest both `1b746ca407ca17b653646fdaeb0f289acaeaa440bce780a81cc52ff70a3da8bc` | 0 | PASS | qa-report |
| digest-rename | C5 display rename stable ID but content digest changes | public loader + temp YAML | `python - <<HARNESS: mutate display_name_zh only then load_structure_catalog(temp)` | same structure_id set; catalog digest changed | `idStable=True`; renamed digest `b3d6dec8fb3e4b5f3daeb1fe8952ee7a1e318ac1e80de86e119f3e4e8baa6267` | 0 | PASS | qa-report |
| side-effects | C6 no public fact/prod registration/count side effect | public loader + public production/fact APIs | `python - <<HARNESS: count production/fact registries before and after load_structure_catalog` | same production rule count/cache; same fact certification count | prod `2041 -> 2041`; fact certifications `0 -> 0`; production cache id stable | 0 | PASS | qa-report |
| old-enum | C7 old TenGodStructureKind unchanged | public enum | `python - <<HARNESS: list(TenGodStructureKind)` | exact three enum names unchanged | `FOOD_GOD_CONTROLS_KILLING`, `HURTING_OFFICER_CONTROLS_KILLING`, `KILLING_GENERATES_SEAL` | 0 | PASS | qa-report |
| no-executable-fields | C8 no executable NL/callback/expression fields | catalog YAML + loader closure | `python - <<HARNESS: recursive catalog key scan and injected expression rejection` | no executable keys present | `foundBadKeys=[]` | 0 | PASS | qa-report |
| source-refs-resolve | C9 source refs resolve | catalog YAML source refs | `python - <<HARNESS: validate each source_refs path:line exists under workspace` | all source_refs are contained existing path:line refs | `totalRefs=60; badRefs=[]` | 0 | PASS | qa-report |
| source-audit-honesty | C10 source audit/review/disputed flags honest | catalog YAML statuses | `python - <<HARNESS: inspect source_status review/disputed and catalog_only_review entries` | review/disputed not hidden; catalog_only_review retained; no disputed overclaimed | review source IDs: `hurting_officer_controls_killing`, `rob_wealth_combines_killing`, `overcontrolled_killing`; disputed IDs: none; catalog-only review IDs: `rob_wealth_combines_killing`, `overcontrolled_killing` | 0 | PASS | qa-report |
| cleanup | C11 cleanup/no residual process | OS temp/process surface | `python - <<HARNESS: TemporaryDirectory contexts closed; no harness child process started` | no residual temp dirs; no child process created | `residualTempDirsSample=[]; childProcessesStarted=0` | 0 | PASS | qa-report |

### adversarialCases

| scenario id | criterion reference | adversarial class | expected behavior | actual | exit | verdict | artifactRefs |
|---|---|---|---|---|---:|---|---|
| reject-dup-id | A1 duplicate ID fail closed | cardinality/identity collision | reject with `STRUCTURE.DUPLICATE_ID` | `STRUCTURE.DUPLICATE_ID:structures:duplicate structure ID` | 0 | PASS | qa-report |
| reject-dup-canonical-key | A2 duplicate canonical key fail closed | canonical key collision | reject with `STRUCTURE.DUPLICATE_KEY` | `STRUCTURE.DUPLICATE_KEY:structures:duplicate canonical key` | 0 | PASS | qa-report |
| reject-duplicate-yaml-key | A3 duplicate YAML key fail closed | duplicate YAML field/key | reject with `STRUCTURE.YAML_DUPLICATE_FIELD` | `STRUCTURE.YAML_DUPLICATE_FIELD:structures[0]:duplicate field` | 0 | PASS | qa-report |
| reject-dup-legacy | A4 duplicate legacy mapping fail closed | duplicate legacy projection | reject with `STRUCTURE.LEGACY_DUPLICATE` | `STRUCTURE.LEGACY_DUPLICATE:legacy_mapping:duplicate legacy mapping` | 0 | PASS | qa-report |
| reject-swapped-legacy | A5 swapped legacy mapping fail closed | swapped legacy target | reject with `STRUCTURE.LEGACY_TARGET` | `STRUCTURE.LEGACY_TARGET:legacy_mapping:legacy mapping target changed` | 0 | PASS | qa-report |
| reject-unknown-legacy | A6 unknown legacy mapping fail closed | unknown legacy enum | reject with `STRUCTURE.LEGACY_MAPPING` | `STRUCTURE.LEGACY_MAPPING:legacy_mapping:unknown legacy mapping` | 0 | PASS | qa-report |
| reject-missing-source-status | A7 missing source status fail closed | required field removal | reject with `STRUCTURE.YAML_FIELDS` | `STRUCTURE.YAML_FIELDS:structures[0]:unexpected fields` | 0 | PASS | qa-report |
| reject-unknown-source-status | A8 unknown source status fail closed | closed source status enum | reject with `STRUCTURE.SOURCE_STATUS` | `STRUCTURE.SOURCE_STATUS:source_status:unsupported source status` | 0 | PASS | qa-report |
| reject-unknown-implementation-status | A9 unknown implementation status fail closed | closed implementation status enum | reject with `STRUCTURE.IMPLEMENTATION_STATUS` | `STRUCTURE.IMPLEMENTATION_STATUS:implementation_status:unsupported implementation status` | 0 | PASS | qa-report |
| reject-unknown-enum-family | A10 unknown enum/family fail closed | closed family enum | reject with `STRUCTURE.FAMILY` | `STRUCTURE.FAMILY:family:unsupported family` | 0 | PASS | qa-report |
| reject-count-31 | A11 count not exactly 30 fail closed | catalog cardinality | reject with `STRUCTURE.COUNT` | `STRUCTURE.COUNT:structures:catalog must contain exactly 30` | 0 | PASS | qa-report |
| reject-executable-field | A12 executable/callback/expression field rejected | executable field injection | reject with `STRUCTURE.YAML_FIELDS` | `STRUCTURE.YAML_FIELDS:structures[0]:unexpected fields` | 0 | PASS | qa-report |
| ctor-raw-id | A13 direct constructor raw ID typed reject | raw scalar constructor input | reject with `STRUCTURE.ENTRY_TYPE` | `STRUCTURE.ENTRY_TYPE:structure_id:invalid structure ID` | 0 | PASS | qa-report |
| ctor-mutable-list | A14 direct constructor mutable list typed reject | mutable collection constructor input | reject with `STRUCTURE.ENTRY_TYPE` | `STRUCTURE.ENTRY_TYPE:required_roles:field must be a nonempty tuple` | 0 | PASS | qa-report |
| ctor-forged-entry-digest | A15 forged entry digest reject | forged entry digest | reject with `STRUCTURE.ENTRY_DIGEST` | `STRUCTURE.ENTRY_DIGEST:content_digest:entry digest mismatch` | 0 | PASS | qa-report |
| ctor-mutable-projection | A16 mutable projection reject | mutable legacy projection | reject with `STRUCTURE.CATALOG_TYPE` | `STRUCTURE.CATALOG_TYPE:legacy_projection:legacy projection must be immutable` | 0 | PASS | qa-report |
| ctor-forged-catalog-digest | A17 forged catalog digest reject | forged catalog digest | reject with `STRUCTURE.CATALOG_DIGEST` | `STRUCTURE.CATALOG_DIGEST:content_digest:catalog digest mismatch` | 0 | PASS | qa-report |
| ctor-nested-entry | A18 nested entry typed reject | nested entry/projection type integrity | reject with `STRUCTURE.CATALOG_TYPE` | `STRUCTURE.CATALOG_TYPE:entries:entries must be catalog entries` | 0 | PASS | qa-report |

UltraQA class coverage:
- U1 formal catalog closure: `formal-30`, `reject-count-31`
- U2 required field and closed enum gates: `fields-closed`, `reject-missing-source-status`, `reject-unknown-source-status`, `reject-unknown-implementation-status`, `reject-unknown-enum-family`
- U3 identity uniqueness: `reject-dup-id`, `reject-dup-canonical-key`, `reject-duplicate-yaml-key`
- U4 legacy compatibility and fail-closed projection: `legacy-current`, `reject-dup-legacy`, `reject-swapped-legacy`, `reject-unknown-legacy`, `old-enum`
- U5 digest invariants: `digest-order`, `digest-rename`, `ctor-forged-entry-digest`, `ctor-forged-catalog-digest`
- U6 public constructor type boundary: `ctor-raw-id`, `ctor-mutable-list`, `ctor-mutable-projection`, `ctor-nested-entry`
- U7 production/fact side-effect isolation: `side-effects`
- U8 no executable surface: `no-executable-fields`, `reject-executable-field`
- U9 source audit integrity and cleanup: `source-refs-resolve`, `source-audit-honesty`, `cleanup`

### artifactRefs

| id | kind | description | path |
|---|---|---|---|
| qa-report | markdown evidence | This non-empty manual QA report containing the harness invocation, expected/actual/exit matrix, adversarial cases, and cleanup proof. | `.omo/evidence/task10-structure-catalog-manual-qa.md` |

Notes:
- The first attempted harness run was discarded because the QA harness emitter call for the duplicate YAML key row had a missing argument after the product loader had already rejected the mutation. The corrected harness was run once to completion and is the evidence recorded above.
- The product tree was not modified by QA. Only this evidence file was written.
