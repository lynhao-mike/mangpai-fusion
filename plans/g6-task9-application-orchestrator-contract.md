# G6 Task 9 Explicit Opt-In Application Orchestrator CONTRACT

## 0. 合同状态

- Gate：`CONTRACT`。
- 裁决：**PASS**。
- 实现授权：**否**。本 PASS 只解锁 fresh independent CONTRACT review；不解锁 `IMPLEMENT`、`STATIC_REVIEW`、`VERIFY`、`EVIDENCE_REVIEW` 或 `FREEZE`。
- 本版逐项关闭首轮 `T9-C-01` 至 `T9-C-11`，不修改 Task 4–8 owner，不新增 builder、adapter、wrapper port、第三 port 或 production authority。
- 本轮仅修订本合同文档；未实现生产或测试代码，未运行 Python、pytest、collection、行为测试、Git 或 GitHub 操作。

## 1. 权威、优先级与证据边界

1. Task 9 范围与原始接口来自 [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:3056)。
2. Task 10 tests-only 边界来自 [`production-implementation-pi-500-r1-f09-implementation-plan.md`](production-implementation-pi-500-r1-f09-implementation-plan.md:3086)。Task 10 的 post-run adapters 不是 Task 9 production authority。
3. 后置 [`PI-500-A1`](production-implementation-pi-500-r1-f09-implementation-plan.md:7804) 对 Task 9 canonical port same-instance reuse 的要求优先于原始 Task 9 文字。
4. 当前 runtime identity owners 为：
   - [`RunTrack`](../engine/f09/contracts.py:21)、[`ContractVersionRef`](../engine/f09/contracts.py:70)、[`NormalizedEvidenceReadPort`](../engine/f09/contracts.py:742)、[`FrozenContractReadPort`](../engine/f09/contracts.py:761)；
   - [`EvidenceRecord`](../engine/f09/evidence.py:75)、[`build_f09_evidence_package()`](../engine/f09/evidence.py:355)；
   - [`GateEvaluationInput`](../engine/f09/decision.py:139)、[`CompetitionInput`](../engine/f09/decision.py:152)、[`RootInput`](../engine/f09/decision.py:158)、[`TimingInput`](../engine/f09/decision.py:165)、[`evaluate_f09()`](../engine/f09/decision.py:870)；
   - [`VersionedObjectRef`](../engine/f09/trace.py:53)、[`build_trace()`](../engine/f09/trace.py:593)、[`build_statement_set()`](../engine/f09/trace.py:824)、[`ProjectionValidationResult`](../engine/f09/trace.py:189)、[`validate_statement_projection()`](../engine/f09/trace.py:874)；
   - [`IdempotencyKey`](../engine/f09/artifacts.py:48)、[`ArtifactSetManifest`](../engine/f09/artifacts.py:113)、[`coordinate_artifact_operation()`](../engine/f09/artifacts.py:1005)；
   - [`bind_feedback_operation()`](../engine/f09/feedback.py:1857)、[`evaluate_learning_eligibility()`](../engine/f09/feedback.py:2031)；
   - [`F09Error`](../engine/f09/errors.py:4)、[`F09IntegrityError`](../engine/f09/errors.py:21)、[`F09SourceError`](../engine/f09/errors.py:25)、[`F09ContractError`](../engine/f09/errors.py:29)、[`F09WriteError`](../engine/f09/errors.py:33)。
5. PI-500 的历史 closeout 只证明 plan-text governance complete，不证明 parseability、collection、runtime conformance 或 production readiness。
6. 本合同中的 caller-supplied objects、bytes、ports、identities 与 timestamps 均为调用者在进入 Task 9 前已构造的 authority；Task 9 只验证边界、逐值转交和编排，不构造或推导这些 authority。

## 2. 目标与严格非目标

### 2.1 唯一目标

未来 Task 9 只实现一个隔离、显式 opt-in 的 application orchestrator：在 pre-I/O boundary 通过后，按 `SOURCE_PREFLIGHT → EVIDENCE → DECISION → TRACE → ARTIFACT` 顺序调用现有 canonical owners，返回不可变结果与不泄露内部内容的 observations。

### 2.2 严格非目标

Task 9 不得：

- 接入默认 production pipeline、service、renderer、adapter、feedback ingest、registry 或配置；
- 修改 Task 4–8 owner、signature、dataclass、protocol 或默认行为；
- 执行 F08；F08 只保持 identity/reference-only；
- 调用 [`bind_feedback_operation()`](../engine/f09/feedback.py:1857)、[`evaluate_learning_eligibility()`](../engine/f09/feedback.py:2031) 或 [`validate_learning_eligibility()`](../engine/f09/feedback.py:2091)；
- 执行 feedback binding、learning、规则更新、publish 或 production persistence；
- 新增 serializer、projection builder、key builder、manifest discovery、clock、wrapper、adapter、dependency bundle、第三 port、compatibility alias 或 dict reconstruction；
- 从 paths、statement、digest、time、UUID、constant、fixtures 或异常文本推导 caller authority；
- 声称 feedback ready、learning eligible、runtime capability 或 production readiness。

## 3. Closed write set

未来 Task 9 implementation write set 恰为：

- [`engine/f09/application.py`](../engine/f09/application.py)
- [`engine/f09/__init__.py`](../engine/f09/__init__.py)
- [`tests/f09/test_application_opt_in.py`](../tests/f09/test_application_opt_in.py)
- [`tests/f09/test_production_isolation.py`](../tests/f09/test_production_isolation.py)

任何其他路径变化立即 STOP。特别冻结 [`engine/f09/contracts.py`](../engine/f09/contracts.py)、[`engine/f09/evidence.py`](../engine/f09/evidence.py)、[`engine/f09/decision.py`](../engine/f09/decision.py)、[`engine/f09/trace.py`](../engine/f09/trace.py)、[`engine/f09/artifacts.py`](../engine/f09/artifacts.py)、[`engine/f09/feedback.py`](../engine/f09/feedback.py)、默认 production 文件及 Task 10 文件。

本合同文件是 CONTRACT Gate 文档产物，不属于未来 implementation diff。

## 4. 最终公共 API

### 4.1 精确 DTO

[`engine/f09/application.py`](../engine/f09/application.py) 必须按以下字段、类型和顺序定义；不得增加、删除、改名、重排或提供额外 constructor：

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping

@dataclass(frozen=True)
class F09RunRequest:
    case_id: str
    mode: Literal[
        "STAGED_AUDIT",
        "PREPROD_SHADOW",
        "PRODUCTION_DEFAULT",
    ]
    chart_records: tuple[EvidenceRecord, ...]
    hypothesis_records: tuple[EvidenceRecord, ...]
    normalized_evidence_port: NormalizedEvidenceReadPort
    frozen_contract_port: FrozenContractReadPort
    request_id: str
    contract_ref: ContractVersionRef
    normative_contract_ref: VersionedObjectRef
    machine_appendix_ref: VersionedObjectRef
    artifact_projections: Mapping[str, bytes]
    artifact_key: IdempotencyKey
    existing_manifest: ArtifactSetManifest | None
    attempt_id: str
    enable_f09: bool = False
    markdown_path: Path = Path(
        "engine/contracts/12-real-world-function-evidence-cards-v1.md"
    )
    snapshot_path: Path = Path(
        "plans/production-implementation-pi-300-f09-source-snapshots-v1.json"
    )
    artifact_root: Path | None = None
    now: str = ""

@dataclass(frozen=True)
class F09Observation:
    event: Literal["F09_SLICE_PHASE"]
    case_id: str
    mode: str
    phase: Literal[
        "SOURCE_PREFLIGHT",
        "EVIDENCE",
        "DECISION",
        "TRACE",
        "ARTIFACT",
    ]
    status: Literal["SUCCEEDED", "FAILED", "REJECTED"]
    issue_codes: tuple[str, ...]
    artifact_set_state: str | None

@dataclass(frozen=True)
class F09RunResult:
    request: F09RunRequest
    evidence: NormalizedEvidencePackage | None
    decision: DecisionEvaluationResult | None
    trace: TraceEnvelope | None
    statement_set: StatementSet | None
    manifest: ArtifactSetManifest | None
    observations: tuple[F09Observation, ...]
    stopped_at: Literal[
        "SOURCE_PREFLIGHT",
        "EVIDENCE",
        "DECISION",
        "TRACE",
        "ARTIFACT",
    ] | None
```

`artifact_projections` 的 runtime authority 是 caller-owned `Mapping[str, bytes]`。application 不复制、不转换、不排序、不包装、不生成 payload；它把同一 mapping object 原样传给 [`coordinate_artifact_operation()`](../engine/f09/artifacts.py:1005)，由 artifact owner 执行恰三角色 shape validation。

### 4.2 精确入口

```python
def run_f09_slice(
    request: F09RunRequest,
    *,
    gate_inputs: tuple[GateEvaluationInput, ...],
    competition_input: CompetitionInput,
    root_input: RootInput,
    timing_input: TimingInput,
) -> F09RunResult:
    ...
```

四个 keyword-only decision inputs保持原始 Task 9 surface。所有新增 caller authority 只放入 [`F09RunRequest`](../engine/f09/application.py)，不得另增参数、context 或 bundle。

### 4.3 精确 package exports

[`engine/f09/__init__.py`](../engine/f09/__init__.py) 只允许：

```python
from engine.f09.application import (
    F09Observation,
    F09RunRequest,
    F09RunResult,
    run_f09_slice,
)

__all__ = (
    "F09Observation",
    "F09RunRequest",
    "F09RunResult",
    "run_f09_slice",
)
```

不得 re-export helper、port、owner、feedback/learning function 或 compatibility alias。

## 5. Pre-I/O boundary 与 mode mapping

### 5.1 精确 rejection 顺序

application 在任何 source read、port call、filesystem resolution/inspection、mkdir 或 write 前，按以下顺序只判定首个 rejection，并返回恰一条 `SOURCE_PREFLIGHT/REJECTED` observation：

| 顺序 | 条件 | application-owned typed identity | `field_path` | `stopped_at` |
|---|---|---|---|---|
| 1 | `request.enable_f09 is not True` | `APPLICATION.OPT_IN_REQUIRED` | `/enable_f09` | `SOURCE_PREFLIGHT` |
| 2 | `request.mode == "PRODUCTION_DEFAULT"` | `APPLICATION.PRODUCTION_DEFAULT_FORBIDDEN` | `/mode` | `SOURCE_PREFLIGHT` |
| 3 | mode 不在两个允许值中 | `APPLICATION.MODE_UNSUPPORTED` | `/mode` | `SOURCE_PREFLIGHT` |
| 4 | `request.artifact_root is None` | `APPLICATION.ARTIFACT_ROOT_REQUIRED` | `/artifact_root` | `SOURCE_PREFLIGHT` |

每个 rejection 必须构造一个 [`F09ContractError`](../engine/f09/errors.py:29)，然后机械投影其 `issue_code`；`diagnostic` 固定为空字符串。由于 DTO 无 field-path 字段，`field_path` 不进入 observation。拒绝结果的 `evidence`、`decision`、`trace`、`statement_set`、`manifest` 全为 `None`。

不属于上述四项的 DTO/type/content错误不在 application rejection surface；由 canonical owner抛出的非 [`F09Error`](../engine/f09/errors.py:4) 原样传播。

### 5.2 唯一 mapping

application 只允许一个静态 mapping site，恰为：

```python
{
    "STAGED_AUDIT": RunTrack.STAGED_L6,
    "PREPROD_SHADOW": RunTrack.V5_V6_PREPROD,
}
```

`PRODUCTION_DEFAULT` 不映射到 [`RunTrack.PRODUCTION_DEFAULT`](../engine/f09/contracts.py:21)。mapping 后只传 canonical [`RunTrack`](../engine/f09/contracts.py:21)；canonical outputs 不得保存 request mode token。

preflight通过后追加恰一条 `SOURCE_PREFLIGHT/SUCCEEDED` observation，`issue_codes=()`，`artifact_set_state=None`。

## 6. Canonical phase 调用与 cardinality

### 6.1 EVIDENCE

恰调用一次：

```python
build_f09_evidence_package(
    case_id=request.case_id,
    track=mapped_track,
    markdown_path=request.markdown_path,
    snapshot_path=request.snapshot_path,
    chart_records=request.chart_records,
    hypothesis_records=request.hypothesis_records,
)
```

成功后追加恰一条 `EVIDENCE/SUCCEEDED`。application 不单独调用 normalized port；authoritative package read由后续 [`evaluate_f09()`](../engine/f09/decision.py:870) 内部完成。

### 6.2 DECISION 与 same-instance ports

恰调用一次：

```python
evaluate_f09(
    evidence,
    normalized_evidence_port=request.normalized_evidence_port,
    frozen_contract_port=request.frozen_contract_port,
    request_id=request.request_id,
    contract_ref=request.contract_ref,
    gate_inputs=gate_inputs,
    competition_input=competition_input,
    root_input=root_input,
    timing_input=timing_input,
    produced_at=request.now,
)
```

[`evaluate_f09()`](../engine/f09/decision.py:892) 对 package 的 authoritative read和其全部后续 evidence reads必须使用 `request.normalized_evidence_port` 同一个对象实例。不得 wrapper、proxy、cache reconstruction、dict reconstruction或第三 port。`request.frozen_contract_port` 也原样传入。成功后追加恰一条 `DECISION/SUCCEEDED`。

### 6.3 TRACE

按顺序各调用恰一次：

```python
trace = build_trace(
    evidence,
    decision,
    normative_contract_ref=request.normative_contract_ref,
    machine_appendix_ref=request.machine_appendix_ref,
    created_at=request.now,
)

statement_set = build_statement_set(
    trace,
    decision,
    normative_contract_ref=request.normative_contract_ref,
    machine_appendix_ref=request.machine_appendix_ref,
    generated_at=request.now,
)

projection_validation = validate_statement_projection(
    statement_set,
    trace,
    decision,
    evidence,
    normative_contract_ref=request.normative_contract_ref,
    machine_appendix_ref=request.machine_appendix_ref,
)
```

两个 [`VersionedObjectRef`](../engine/f09/trace.py:53) 必须逐对象原样复用于三个调用。若 `projection_validation.valid is True`，则 `detected_issues` 必须为空并追加恰一条 `TRACE/SUCCEEDED`。若 `valid is False` 或 `detected_issues` 非空，则不调用 artifact；保留已成功构造的 `trace` 与 `statement_set`，机械投影 returned issue codes到恰一条 `TRACE/FAILED`，并令 `manifest=None`、`stopped_at="TRACE"`。不得从 `valid` 自行创造 issue code。

### 6.4 ARTIFACT

仅在 projection validation成功后恰调用一次：

```python
manifest = coordinate_artifact_operation(
    request.artifact_root,
    statement_set,
    request.artifact_projections,
    existing_manifest=request.existing_manifest,
    key=request.artifact_key,
    attempt_id=request.attempt_id,
    now=request.now,
)
```

application 不检查目录、不读取 manifest、不生成 bytes/key/attempt/time，不比较 key，也不绕过 coordinator直接调用 write/retry。

- manifest state为 [`ArtifactSetState.COMPLETE_VERIFIED`](../engine/f09/contracts.py:64)：追加恰一条 `ARTIFACT/SUCCEEDED`，`issue_codes`机械投影 `manifest.detected_issues`且必须为空，`artifact_set_state="COMPLETE_VERIFIED"`，`stopped_at=None`。
- state为 [`ArtifactSetState.PARTIAL`](../engine/f09/contracts.py:65)、[`ArtifactSetState.STALE_MIXED_REVISION`](../engine/f09/contracts.py:66)、[`ArtifactSetState.DIGEST_MISMATCH`](../engine/f09/contracts.py:67) 或 [`ArtifactSetState.FAILED`](../engine/f09/contracts.py:68)：保留 manifest，追加恰一条 `ARTIFACT/FAILED`，只机械投影 returned issues，`artifact_set_state=manifest.state.value`，`stopped_at="ARTIFACT"`。空 returned issues保持空，不得从 state造 code。

### 6.5 Feedback 终止语义

Task 9 没有 feedback phase token、feedback DTO、feedback output或feedback observation。artifact成功是本 orchestrator唯一正常终点，不等于 feedback ready。

[`bind_feedback_operation()`](../engine/f09/feedback.py:1857)、[`evaluate_learning_eligibility()`](../engine/f09/feedback.py:2031)、[`validate_learning_eligibility()`](../engine/f09/feedback.py:2091) 调用计数必须全部为零。Task 10 在 [`run_f09_slice()`](production-implementation-pi-500-r1-f09-implementation-plan.md:3072) 之后调用的 tests-only feedback adapter不得反向成为 Task 9 authority。

## 7. Typed failure 与 downstream `None` 矩阵

application 只允许捕获基类 [`F09Error`](../engine/f09/errors.py:4)。捕获后只投影 exact `issue_code`；不得解析 `diagnostic`、异常文本或 `field_path`来生成新 code。禁止捕获 `Exception`、`BaseException`、裸 except及任何原生异常类；unexpected exceptions原样传播且不返回降级结果。

| 失败位置 | observation | 保留字段 | 必须为 `None` | `stopped_at` |
|---|---|---|---|---|
| pre-I/O rejection | `SOURCE_PREFLIGHT/REJECTED` | `request`, observations | evidence, decision, trace, statement_set, manifest | `SOURCE_PREFLIGHT` |
| evidence owner typed failure | `EVIDENCE/FAILED` | `request`, observations | evidence, decision, trace, statement_set, manifest | `EVIDENCE` |
| decision owner typed failure | `DECISION/FAILED` | request, evidence, observations | decision, trace, statement_set, manifest | `DECISION` |
| trace builder typed failure | `TRACE/FAILED` | request, evidence, decision, observations | trace, statement_set, manifest | `TRACE` |
| statement builder typed failure | `TRACE/FAILED` | request, evidence, decision, trace, observations | statement_set, manifest | `TRACE` |
| projection validator typed failure | `TRACE/FAILED` | request, evidence, decision, trace, statement_set, observations | manifest | `TRACE` |
| projection invalid returned result | `TRACE/FAILED` | request, evidence, decision, trace, statement_set, observations | manifest | `TRACE` |
| artifact coordinator typed failure | `ARTIFACT/FAILED` | request, evidence, decision, trace, statement_set, observations | manifest | `ARTIFACT` |
| non-ready manifest returned | `ARTIFACT/FAILED` | request, evidence, decision, trace, statement_set, manifest, observations | 无 | `ARTIFACT` |
| complete manifest returned | `ARTIFACT/SUCCEEDED` | 全部 | 无 | `None` |

每个成功 phase恰一条 observation；失败 phase恰一条 observation；失败后不追加未运行 phase。完整成功恰五条 observations，顺序固定为五个 phase token。observations为 tuple，不排序、不去重、不回填。

## 8. Observation 数据限制

observations 不得包含 source prose、statement text、statement ID/revision ID、共识/冲突 ID、trace node/edge ID、artifact path、digest、exception diagnostic、stack trace或Agent记录。

`event`恒为 `F09_SLICE_PHASE`。`issue_codes`只来自 application preflight表中的 typed identity、caught [`F09Error.issue_code`](../engine/f09/errors.py:5)、[`ProjectionValidationResult.detected_issues`](../engine/f09/trace.py:191) 或 [`ArtifactSetManifest.detected_issues`](../engine/f09/artifacts.py:119)。不得从 action、state、status、reason、None或空值推导 code。

`artifact_set_state`仅在 coordinator已返回 manifest时取 `manifest.state.value`，其余恒为 `None`。

## 9. T9-C-01 至 T9-C-11 reconciliation

| ID | 裁决 | 唯一闭合语义 | 证据 |
|---|---|---|---|
| T9-C-01 | `CLOSED` | 两类 caller-owned immutable tuples按固定顺序进入 request并原样传给 evidence builder；无新 owner | [`build_f09_evidence_package()`](../engine/f09/evidence.py:355) |
| T9-C-02 | `CLOSED` | 两个 canonical ports进入 request；normalized port同一实例由 evaluator完成authoritative read及全部后续读取；无 wrapper/第三 port | [`evaluate_f09()`](../engine/f09/decision.py:870)、[`PI-500-A1`](production-implementation-pi-500-r1-f09-implementation-plan.md:7871) |
| T9-C-03 | `CLOSED` | caller-owned `request_id`、[`ContractVersionRef`](../engine/f09/contracts.py:70) 与 `now`分别原样进入 evaluator；禁止推导 | [`evaluate_f09()`](../engine/f09/decision.py:875) |
| T9-C-04 | `CLOSED` | 两个 caller-owned [`VersionedObjectRef`](../engine/f09/trace.py:53) 原样复用于 trace、statement和projection validation | [`build_trace()`](../engine/f09/trace.py:593)、[`build_statement_set()`](../engine/f09/trace.py:824) |
| T9-C-05 | `CLOSED` | caller提供三角色 bytes mapping；application零序列化并把同一 mapping交给artifact coordinator；不改Task 6/7 | [`coordinate_artifact_operation()`](../engine/f09/artifacts.py:1005) |
| T9-C-06 | `CLOSED` | caller提供已构造 canonical [`IdempotencyKey`](../engine/f09/artifacts.py:48)；application不构造、不摘要、不校正 | [`coordinate_artifact_operation()`](../engine/f09/artifacts.py:1011) |
| T9-C-07 | `CLOSED` | caller提供 `existing_manifest`、`attempt_id`、artifact root与`now`；application不目录发现或生成identity | [`coordinate_artifact_operation()`](../engine/f09/artifacts.py:1010) |
| T9-C-08 | `CLOSED` | application-owned四类pre-I/O typed rejection、closed observation tokens、固定cardinality与停止表已冻结 | [`Task 9 stop tests`](production-implementation-pi-500-r1-f09-implementation-plan.md:3075)、[`F09ContractError`](../engine/f09/errors.py:29) |
| T9-C-09 | `CLOSED` | projection invalid在artifact前STOP；仅complete manifest成功；其余manifest保留并在ARTIFACT停止；returned issues机械投影 | [`ProjectionValidationResult`](../engine/f09/trace.py:189)、[`ArtifactSetState`](../engine/f09/contracts.py:63) |
| T9-C-10 | `CLOSED` | feedback/eligibility/learning明确零调用；Task 9在artifact结束，不制造feedback readiness | [`Task 10 boundary`](production-implementation-pi-500-r1-f09-implementation-plan.md:3094)、[`evaluate_learning_eligibility()`](../engine/f09/feedback.py:2031) |
| T9-C-11 | `CLOSED` | package只导出三个DTO与入口，顺序和`__all__`已冻结 | [`engine/f09/__init__.py`](../engine/f09/__init__.py) |

11项均无 `STILL_OPEN` 或 `OUT_OF_SCOPE`。本闭合不要求修改Task 6/7 owner，因此不触发前置任务或 `BLOCKED`。

## 10. 未来验证合同

以下命令仅在 fresh independent CONTRACT review PASS、用户另行授权并切换实现模式后可执行；本轮未运行。

### 10.1 Focused selector

`python -m pytest tests/f09/test_application_opt_in.py tests/f09/test_production_isolation.py -q`

### 10.2 Regression selector

`python -m pytest tests/test_production_entrypoints_unchanged.py tests/ziping_career/test_production_isolation.py tests/application/test_staged_parallel_runner.py tests/test_error_policy.py::test_ep004_production_service_strict_render_failure_marks_job_failed -q`

### 10.3 静态 AST 与精确计数

Fresh reviewer必须证明：

1. implementation diff恰为第3节四个路径。
2. [`F09RunRequest`](../engine/f09/application.py)、[`F09Observation`](../engine/f09/application.py)、[`F09RunResult`](../engine/f09/application.py) 的 dataclass fields、annotation文本与顺序精确等于第4节；额外字段/constructor为零。
3. [`run_f09_slice()`](../engine/f09/application.py) 只有request加四个keyword-only decision inputs；`**kwargs`、dependency bundle和overload为零。
4. mode mapping literal恰两项且mapping site恰一处；`RunTrack.PRODUCTION_DEFAULT`在application executable AST中出现零次。
5. application对 [`build_f09_evidence_package()`](../engine/f09/evidence.py:355)、[`evaluate_f09()`](../engine/f09/decision.py:870)、[`build_trace()`](../engine/f09/trace.py:593)、[`build_statement_set()`](../engine/f09/trace.py:824)、[`validate_statement_projection()`](../engine/f09/trace.py:874)、[`coordinate_artifact_operation()`](../engine/f09/artifacts.py:1005) 的call site各恰一处。
6. normalized evidence port的同一 attribute load原样进入 evaluator；wrapper、adapter、proxy、dict reconstruction、第三port声明为零。
7. catch handler只捕获 [`F09Error`](../engine/f09/errors.py:4)；catch-all与原生异常捕获为零。
8. feedback bind、eligibility、learning、F08 executor、production pipeline、renderer、test module import/call均为零。
9. artifact write/retry/inspect直接调用为零；唯一artifact callable是coordinator。
10. observation token literal闭集、每阶段成功/失败cardinality与downstream `None`矩阵逐项满足。
11. disabled、production-default、unknown、missing-root测试按固定优先级证明source/port/filesystem call均为零。
12. production-default files对 `engine.f09` import count为零；clean process导入默认production entrypoints后 `engine.f09`不在 `sys.modules`。
13. tests不得从fixtures导入production authority、使用expectation-derived dynamic dispatch、monkeypatch assertion weakness或伪canonical owner制造通过。

### 10.4 Reviewer checks

Fresh reviewer逐项核对：closed write set、exact DTO/API/exports、same-instance port、mode mapping、pre-I/O priority、phase order、owner call counts、typed catch、unexpected propagation、projection STOP、manifest状态矩阵、downstream `None`、feedback零调用、production isolation、F08零执行、selectors及AST计数。合同作者和implementer不得自评。

## 11. STOP conditions

任一条件立即 STOP并返回CONTRACT或owning task：

- 修改第3节以外路径；
- 改变第4节字段、类型、顺序、defaults、signature或exports；
- 发明projection bytes、serialization、key material、attempt identity、manifest discovery、clock或feedback authority；
- wrapper/adapter/proxy/dict reconstruction/third port/旧aggregate fallback；
- pre-I/O rejection前发生任一I/O或port call，或rejection优先级变化；
- `PRODUCTION_DEFAULT`被映射为canonical production track；
- phase缺失、重排、重复调用、失败后继续下游或覆盖upstream object；
- projection invalid后调用artifact，或非complete manifest被标记成功；
- 从manifest state、validation bool、异常文本或空issue推导新code；
- 捕获非 [`F09Error`](../engine/f09/errors.py:4) 或吞掉unexpected exception；
- 调用F08、feedback、learning、direct artifact write/retry/inspect、production pipeline或renderer；
- selector不可收集、测试削弱、AST/count/isolation不满足；
- 用户工作树改动被覆盖、混入或清理；
- Git mutation、GitHub service-side mutation、部署、发布或远端操作；
- implementer仍需作本文未冻结的接口、token、serializer、digest、authority placement或stop-policy选择。

## 12. CONTRACT Gate 裁决与唯一下一合法动作

**裁决：PASS。**

- `T9-C-01` 至 `T9-C-11` 全部 `CLOSED`。
- Task 6/7 owner无需修改；closed implementation write set仍恰为四个Task 9文件。
- PASS只证明本文形成唯一、无开放选择的document-only implementation contract；不证明代码存在、可导入、可收集、测试通过或production ready。
- 实现授权仍为否。

**唯一下一合法动作：** 对本修订合同执行一次 fresh、独立、只读、证据限定的 CONTRACT review。只有该review明确PASS且用户随后另行授权，才可切换到实现模式开启独立IMPLEMENT任务；不得由本合同作者直接进入实现。

## 13. 永久禁止事项

永久禁止任何GitHub service-side mutation，包括创建或修改PR、Issue、评论、标签、分支、release、workflow、repository settings或远端ref。本子任务同样禁止Git mutation、commit、revert、stash、branch、worktree、push、deploy与publish。
