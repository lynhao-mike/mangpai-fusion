# G6 Task 4 · PI-210 Evidence Package and Declaration Resolver

> 状态：`CONTRACT_DRAFT_FOR_INDEPENDENT_REVIEW`
>
> 日期：2026-07-25（Asia/Shanghai）
>
> 权威范围：本文件是 G6 Task 4 的 durable Gate ledger。它记录 fresh ADMISSION 与现行 CONTRACT 草案；不证明现有实现正确，不授权修改、测试、Git 或任何 GitHub 操作。

## 1. 权威输入与优先级

本单元依次受以下事实源约束：

1. `production-implementation-pi-210-normalized-evidence-model.md`：三轨、来源、声明五分支、完整性与 PI-220/PI-230 读取边界；
2. `g6-task3-frozen-source-resolution-contract-amendment.md`：Task 3 resolver owner、成功 DTO 与唯一 typed-exception 失败通道；
3. `production-implementation-pi-500-r1-f09-implementation-plan.md` Task 4：本单元文件范围、Python 接口、专项 selector 与回归 selector；
4. 现行代码与测试：仅作为待审实现候选和消费者证据，不得反向改写上述合同。

冲突时，PI-210 与已冻结 Task 3 source contract 优先。旧测试结果、全量 F09 历史回归、代码存在和下游成功均不是本单元 fresh Gate evidence。

## 2. Fresh ADMISSION ledger

### 2.1 Gate record

```text
Gate: ADMISSION
Owner role: Analyst
Authorization envelope: local read-only inventory of Task 4 plan, owner paths, direct consumers and static test structure
Activation condition: Task 3 durable freeze exists and Task 4 is the first not-yet-parent-frozen PI-500 candidate
Required inputs: PI-210, Task 3 frozen contract, PI-500 Task 4, current three planned paths, bounded consumers
Verdict: PASS
Direct evidence boundary: enough information exists to draft one falsifiable Task 4 contract
Forbidden inference boundary: code existence, test breadth, fixture use and downstream consumers do not prove implementation correctness or Task 4 completion
```

### 2.2 Observed facts

- Task 3 source-resolution dependency is already evidence-bounded frozen.
- Task 4 is the first PI-500 parent Task after Task 3 for which no named durable parent freeze was found.
- All three planned paths exist: `engine/f09/evidence.py`, `tests/f09/conftest.py`, `tests/f09/test_evidence_contract.py`.
- Production consumers are bounded and identified:
  - `engine/f09/decision.py` consumes `EvidenceRecord` and `NormalizedEvidencePackage`;
  - `engine/f09/trace.py` consumes `NormalizedEvidencePackage` and `validate_for_pi220`;
  - `engine/f09/artifacts.py` consumes `NormalizedEvidencePackage`;
  - `engine/f09/application.py` consumes `EvidenceRecord`, `NormalizedEvidencePackage` and `build_f09_evidence_package`;
  - `engine/f09/contracts.py` has TYPE_CHECKING references and the normalized-evidence read protocol.
- Test consumers are bounded and identified: `tests/f09/conftest.py`, `tests/f09/test_trace_contract.py`, `tests/f09/test_artifact_lifecycle.py`, `tests/f09/test_application_opt_in.py`, `tests/f09/test_decision_contract.py`, and the Task 4 focused test module.
- `tests/f09/conftest.py::decision_case` directly constructs the three Task 4 DTOs and supplies a canonical fixture to Task 5+ consumers; it is a compatibility consumer, not the Task 4 owner.
- Read-only AST accounting of `tests/f09/test_evidence_contract.py` found exactly 47 top-level `test_*` declarations, 118 literal parameterized instances, no unknown parameter source and none of these collection hooks: `pytest_collect_file`, `pytest_collection_modifyitems`, `pytest_generate_tests`, `pytest_pycollect_makeitem`.
- Both PI-500 regression nodes remain uniquely locatable.

### 2.3 Inferences and unknowns

Inferences:

- Existing code is an implementation candidate that should be reviewed as-is before any repair; Task 4 must not be reimplemented merely because its parent Gate history is missing.
- Downstream consumers make public DTO shape and runtime identity compatibility part of the Task 4 boundary, but do not expand the owner write set.

Unknowns pending later Gates:

- Whether the current implementation satisfies every clause below;
- whether focused dynamic collection reconciles to 118;
- whether either regression selector currently passes;
- whether a bounded repair is needed after fresh STATIC_REVIEW.

## 3. CONTRACT target and exact scope

### 3.1 Exactly one target

The only target is the existing F09 Task 4 evidence package and declaration resolver boundary owned by `engine/f09/evidence.py`, with canonical fixture compatibility and focused falsifiers in the two planned test files.

### 3.2 Exact file whitelist

Potential implementation/repair whitelist, inactive until separately activated after CONTRACT PASS:

- `engine/f09/evidence.py` — Task 4 owner implementation only;
- `tests/f09/test_evidence_contract.py` — Task 4 focused falsifiers and static accounting oracle only;
- `tests/f09/conftest.py` — only if exact public DTO compatibility requires a fixture adjustment.

Read-only consumer review may inspect the bounded consumers listed in section 2.2. It does not authorize modifying them.

### 3.3 Explicit non-goals

This Task does not:

1. modify Task 3 Markdown/JSON source resolvers or their frozen error model;
2. modify `engine/f09/contracts.py` public types, unions or protocols;
3. change Task 5+ decision, trace, artifact, application, feedback or learning behavior;
4. execute mapping YAML or derive business gates, scores, priorities, winners, actions or report text;
5. inspect reports, labels, feedback, mapping YAML, historical cases or theory as runtime inputs;
6. change production-default behavior or import isolation;
7. add a second source-binding field to `EvidenceRecord`;
8. run Git or any GitHub service-side mutation.

## 4. Frozen public interface

The canonical runtime owner of these objects and functions is `engine/f09/evidence.py`:

```python
@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    track: EvidenceTrack
    locator: SourceLocator
    value: object
    temporal_scope: str
    transformation: Literal["MDFF_V1_COPY", "LOSSLESS_COPY"]

@dataclass(frozen=True)
class DeclarationObservation:
    binding: FrozenDeclarationBinding
    value: object
    source_state: str

@dataclass(frozen=True)
class NormalizedEvidencePackage:
    package_id: str
    case_id: str
    track: RunTrack
    records: tuple[EvidenceRecord, ...]
    validation_plan: DeclarationObservation
    output_precision: DeclarationObservation
    issues: tuple[IntegrityIssue, ...]
    integrity_state: Literal["READY", "INVALID", "BLOCKED"]

def build_f09_evidence_package(
    *,
    case_id: str,
    track: RunTrack,
    markdown_path: Path,
    snapshot_path: Path,
    chart_records: tuple[EvidenceRecord, ...],
    hypothesis_records: tuple[EvidenceRecord, ...],
) -> NormalizedEvidencePackage: ...

def validate_for_pi220(
    package: NormalizedEvidencePackage,
) -> Literal["READY", "INVALID", "BLOCKED"]: ...

def trace_to_sources(
    package: NormalizedEvidencePackage,
    object_id: str,
) -> tuple[SourceLocator, ...]: ...
```

No duplicate runtime owner, copied DTO, alias owner or shadow binding field is permitted. Existing consumers must continue receiving these canonical runtime identities.

## 5. Behavior invariants

### 5.1 Three-track isolation

1. Every `EvidenceRecord` belongs to exactly one of `CHART_STRUCTURE`, `REALITY_FACT`, `UNVERIFIED_HYPOTHESIS`.
2. `chart_records` accepts only `CHART_STRUCTURE`; `hypothesis_records` accepts only `UNVERIFIED_HYPOTHESIS`.
3. Chart or hypothesis evidence can never satisfy, replace or be promoted into a required reality coordinate.
4. A hypothesis with an immutable source remains `UNVERIFIED_HYPOTHESIS`.
5. `EvidenceRecord` stores source identity only through `locator.binding`.

### 5.2 Frozen reality package

1. F09 reality facts are copied only from the immutable JSON snapshot through the frozen Task 3 public APIs.
2. The package contains exactly the contract-declared reality coordinates; missing, extra or relabelled coordinates block PI-220 consumption.
3. Reality state, event and outcome object identities remain separate.
4. State, event interval and outcome temporal scopes remain separate and cannot be swapped.
5. Every reality record uses `LOSSLESS_COPY`, an immutable JSON binding and exact locator/source identity.
6. Validation recomputes current source-backed content and does not trust a cached `READY` state.
7. Source unavailability, resolver failure, binding drift, locator drift, copied-value drift, transformation drift or temporal-scope drift fail closed as blocking integrity issues.
8. JSON value comparison must reject boolean/number aliasing and built-in subclasses; nested values and keys must remain exact bounded-JCS-compatible values. No string conversion, coercion or fuzzy equality is allowed.

### 5.3 Declaration preservation

1. `FrozenDeclarationBinding` remains the exact closed five-branch union: `RESOLVED`, `ABSENT`, `NOT_APPLICABLE`, `UNAVAILABLE`, `UNRESOLVABLE`.
2. Declaration reference presence and declaration value state remain separate.
3. F09 output precision is exactly `ResolvedDeclarationBinding + value=None + source_state="BOTH_NULL_AND_UNRESOLVED"`.
4. F09 validation plan is resolved independently from output precision and must preserve its complete stable reference, value and source state.
5. `ABSENT` and `NOT_APPLICABLE` make the relevant F09 package invalid for PI-220; `UNAVAILABLE` and `UNRESOLVABLE` block it and retain nonempty issues/attempted reference as defined by the canonical union.
6. Complete declaration identity is checked: declaration ID, type, card, contract version, declaration schema version and digest. Value and source-state mismatch are invalid.
7. No branch may be represented by bare null, an empty object, a default enum or a partially copied reference.

### 5.4 Integrity and trace boundary

1. `READY`, `INVALID` and `BLOCKED` describe package consumability only; they do not express a business gate, priority, winner or final action.
2. `validate_for_pi220` checks only Task 4 integrity concerns and must not execute PI-220 business semantics.
3. `trace_to_sources` is deterministic, stable-order and deduplicated by complete `SourceLocator` identity; distinct bindings at otherwise equal coordinates remain distinct.
4. Unknown object IDs return an empty tuple; malformed package or object ID inputs fail closed according to the public type contract.
5. Package identity is deterministic for the same accepted input sequence and must not inspect hidden repository state.

## 6. Structural and dependency invariants

1. `engine/f09/evidence.py` may consume only explicit arguments, canonical Task 1 contracts/types, Task 2 bounded JSON utilities where already transitively owned, Task 3 public source APIs and F09 typed errors.
2. It must not import or call reports, labels, feedback, mapping YAML, historical cases, default pipeline/registry/timing modules, or private Task 5+ owners.
3. Task 5+ modules are consumers; their existence does not authorize reverse calls from Task 4.
4. No dynamic pytest collection hook may alter focused accounting.
5. Tests must assert public behavior, immutable source identity and independent expected constants; they must not duplicate production algorithms as their oracle.
6. Existing implementation is reviewed before repair. Any repair invalidates prior static conclusions and requires a fresh STATIC_REVIEW.

## 7. Static accounting and exact verification selectors

### 7.1 Counting method

Parse `tests/f09/test_evidence_contract.py` with Python `ast`; count top-level `test_*` function declarations. For each `pytest.mark.parametrize` whose second positional argument is a literal list, tuple or set, multiply literal cardinalities across stacked decorators. Reject unknown/dynamic parameter sources. Separately scan top-level definitions for the four forbidden collection hooks.

Frozen current accounting:

```text
top-level test declarations = 47
static parameterized instances = 118
unknown parameter sources = 0
collection hooks = 0
```

STATIC_REVIEW must re-run this read-only accounting against the candidate under review. VERIFY must reconcile focused pytest collection and outcomes to exactly 118 instances; any mismatch is a selector/collection or contract-accounting failure, not behavior PASS.

### 7.2 Exact selectors, to remain inactive until STATIC_REVIEW PASS

Focused Task 4:

```text
python -m pytest tests/f09/test_evidence_contract.py -q
```

Expected collection on the frozen current accounting: exactly 118 instances.

Production-isolation regression:

```text
python -m pytest tests/application/test_staged_parallel_runner.py::test_parallel_and_comparison_modules_have_no_forbidden_imports tests/ziping_career/test_production_isolation.py::test_staged_modules_do_not_import_default_registry_pipeline_reports_or_timing -q
```

Expected collection: exactly 2 instances.

No full F09 or repository suite is part of the minimum Task 4 contract. A broader suite may only be separately derived after focused evidence and cannot replace either selector above.

## 8. Fresh STATIC_REVIEW questions

A logically fresh reviewer must answer all of the following without relying on this draft's conclusions:

1. Are the target and three-path whitelist unique, with Task 5+ consumers kept read-only?
2. Do the public DTOs and function signatures exactly preserve the frozen interface and canonical runtime identity?
3. Can any chart/hypothesis record enter or satisfy the frozen reality coordinate set?
4. Does every accepted reality record terminate at the immutable JSON source through Task 3 public APIs, with complete binding/locator/value/transformation/temporal validation?
5. Are source and parse failures converted into nonempty blocking integrity issues without fallback, coercion or swallowed exceptions?
6. Are all five declaration branches consumed distinctly, with F09 precision exactly resolved-null-and-unresolved and validation plan independent?
7. Does validation recompute current source-backed integrity rather than trust cached status or caller issues?
8. Is tracing deterministic and deduplicated only by complete locator identity?
9. Are hidden repository inputs, mapping execution, private/downstream calls and production-default imports absent?
10. Does AST accounting reproduce 47 declarations, 118 instances, zero unknown parameter sources and zero collection hooks?
11. Do focused tests use independent expectations rather than copy the implementation?
12. Is there any High/Medium contract ambiguity that prevents exact review, bounded repair or exact verification?

## 9. Falsifiers

Any one of the following falsifies STATIC_REVIEW PASS or later verification eligibility:

- a duplicate owner or incompatible public DTO shape;
- a consumer requiring modification outside the three-path whitelist;
- chart/hypothesis promotion or reality coordinate substitution;
- missing, extra, relabelled or temporally swapped reality coordinates accepted as READY;
- mutable, unversioned or identity-drifted reality source accepted as READY;
- bool/number alias, built-in subclass or coercive equality accepted as exact copied JSON;
- declaration branch collapse, bare null binding, missing attempted ref/issues, or F09 precision branch/value/state drift;
- cached READY trusted after content tampering;
- hidden report/feedback/mapping/history/default-production dependency;
- tests mirroring private implementation logic;
- static count other than 47/118/0/0 without a reviewed contract amendment;
- missing or nonunique selector;
- any GitHub-mutating effect.

## 10. STOP conditions and authority boundary

Stop and return the applicable Gate verdict if:

- the target, owner or required consumer compatibility is nonunique;
- any required repair touches a file outside the exact whitelist;
- a public API/schema tradeoff not fixed by authority sources appears;
- Task 3 frozen APIs must change;
- a selector is missing, duplicated, dynamically altered or collects unexpectedly;
- any command may mutate GitHub service-side state;
- fresh review finds an unresolved High/Medium gap.

This contract grants no implementation, test, local Git, remote-read or GitHub-write authority. GitHub service-side mutation remains permanently forbidden. The PI-500 commit and rollback instructions are not correctness Gates and are excluded from this controlled unit.

## 11. Direct evidence and forbidden inference boundaries

Directly established by ADMISSION and contract construction:

- Task 4 is a unique parent candidate with frozen prerequisites;
- its owner, consumer surface, compatibility boundary, intended whitelist, static counting method and exact selectors are identifiable;
- a bounded fresh STATIC_REVIEW is mechanically possible.

Not established and forbidden to infer:

- current implementation correctness;
- any test PASS;
- downstream Task 5–Task 10 correctness;
- Task 4 freeze, G6 completion, deployment or GitHub synchronization.

## 12. Current Gate state

```text
ADMISSION: PASS
CONTRACT draft: complete; awaiting logically fresh independent CONTRACT review
IMPLEMENT: not started; existing code is only an implementation candidate
STATIC_REVIEW: not authorized by this draft
VERIFY: not authorized by this draft
EVIDENCE_REVIEW: not started
FREEZE: not eligible
```

Unique next legal action: perform a logically fresh, read-only CONTRACT review using this draft, the explicit local/GitHub boundary, PI-210, the frozen Task 3 dependency and PI-500 Task 4 facts. CONTRACT PASS may only unlock a separately bounded STATIC_REVIEW of the existing implementation; it does not require or justify rewriting it.
