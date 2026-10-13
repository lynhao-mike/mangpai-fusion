# PI-500-R1 F09 One-Card Vertical Slice Implementation Plan

> **For implementers and reviewers:** 每个 Task 必须由 fresh implementation context 执行，并由不同的 fresh independent reviewer 按该 Task 的 review gate 验收；不得由实现者自验替代独立评审。本计划不要求或授权递归 delegation。

**Goal:** 在不改变 production-default、不执行 F01–F12 其余卡片的前提下，实现一个显式 opt-in、fail-closed、可审计、可重试且可回滚的 F09“资本配置与风险承担”单卡端到端切片。

**Architecture:** 新建隔离的 `engine/f09/` 包，按 immutable contracts、受限 RFC 8785 canonicalization、Markdown/JSON source resolution、PI-210 evidence、PI-220 decision、PI-230 trace/artifact/feedback、opt-in orchestration 分责。该切片不导入或修改默认 pipeline、默认 adapters、production service、legacy renderer 或 learning writer；legacy report/feedback 只允许经过完整性验证后的单向 audit projection，且绝不自动学习。

**Tech Stack:** Python 3.10+ 标准库（`dataclasses`、`enum`、`hashlib`、`json`、`pathlib`、`tempfile`、`typing`、`unicodedata`）、pytest 7–8；类型别名必须使用 Python 3.10 兼容的 `TypeAlias`/`Union` 语法，不使用 Python 3.12 的 `type` statement；不新增第三方 RFC 8785 依赖，不执行 declarative YAML。

## Global Constraints

- 本计划是 G5 实现计划，不是实现授权；创建本文件不表示实现完成，F01–F12 implementation 仍为 `false`。
- 只实现 F09；F08 仅为 identity-only competitor，禁止生成 F08 candidate、decision、action 或 statement。
- 不修改 `mapping/real-world-function-evidence-cards-v1.yaml`，实现与测试均不得执行该 YAML。
- 不修改 `engine/application/pipeline_runner.py`、`engine/application/ports.py`、`engine/application/production_service.py`、`engine/infrastructure/adapters/pipeline_adapters.py`、`tools/render_report.py`、`tools/feedback_ingest.py` 或默认 production 配置。
- 不改变 `run_pipeline()`、`run_pipeline_e2e()`、`PipelineAdapters`、`SubmitAnalysisRequest` 的签名或默认行为。
- 所有新运行入口必须要求 `enable_f09=True` 且只接受 application request mode `STAGED_AUDIT` 或 `PREPROD_SHADOW`；这两个 mode 不是 PI-210 `RunTrack`。唯一映射固定为 `STAGED_AUDIT -> STAGED_L6`、`PREPROD_SHADOW -> V5_V6_PREPROD`；缺省、false、未知 mode、`PRODUCTION_DEFAULT` request 均 fail closed 且在映射及任何 I/O 前拒绝。
- PI-210 是 `RunTrack` 的 sole owner；所有 canonical/runtime track 字段、fixture、baseline、mutator 与 assertion 必须逐字复用封闭五值 `PRODUCTION_DEFAULT | PARALLEL_DOMAIN | STAGED_L6 | V5_V6_PREPROD | MANUAL_IMPORT`，不得在 F09 声明 alias enum 或扩展值域。
- staged/preprod 与 production artifact、feedback、learning 分账；跨轨关系仅可为 `AUDIT_ONLY`。
- Markdown 唯一 selector grammar 为 `mdff:v1/heading/<H>/card/<C>/item/<L>`，profile 固定为 `markdown-source.commonmark-0.31.2-mdff-v1`，copy semantics 固定为 `MDFF_V1_COPY`。
- Markdown digest 固定为 `RAW-UTF8-NO-BOM-LF`：输入可为 LF 或 CRLF，摘要与 copy 前必须逐个将 CRLF 规范化为 LF；拒绝 UTF-8 BOM 与任何 bare CR；同时拒绝 selector 非 canonical 编码、非唯一 heading/card/label、fuzzy/regex/alias/fallback。冻结 Markdown 实际含 437 个 CRLF、0 个 bare CR 且无 BOM，是规范化后摘要命中的正例。
- JSON snapshot 固定读取 `plans/production-implementation-pi-300-f09-source-snapshots-v1.json`；digest 只覆盖 `payload`，`DigestRef.algorithm` 的 canonical token 固定为小写 `sha256`，canonicalization 为 `RFC8785-JCS-UTF8`；不得出现大写或带连字符的替代 token。
- RFC 8785 策略为严格受限标准域：只接受 object（字符串键）、array、Unicode scalar string、boolean、null；拒绝所有 integer/float/Decimal、NaN/Infinity、非字符串键、孤立 UTF-16 surrogate、重复键与自定义对象。键按 UTF-16 code units 排序，字符串按 RFC 8785/RFC 8259 最短合法转义输出，结果 UTF-8 编码。该受限域覆盖冻结 fixture 的完整 payload；任何域外值 fail closed。
- RFC 6901 pointer 从 matched object 的 `value` 根开始；禁止从 envelope 根开始、猜配、默认值与 prose 补齐。
- explicit null、absent、unavailable、unresolvable、not applicable、source unresolved、evaluator unknown、missing、conflict 必须保持不同状态。
- output precision 必须为 binding `RESOLVED`、declaration value `null`、source state `BOTH_NULL_AND_UNRESOLVED`；不得降级为 `ABSENT`。
- F09 六成员固定为 `RESOURCE/OBJECT/ALLOCATION/RISK/ATTRIBUTION/TENSE`；declaration 与 evaluation records 必须全双射、稳定身份、顺序无关、绑定摘要匹配。
- 六 participation roles 必须各有独立 record；不得互补或用容器 ID 冒充 record ID。
- action 仅允许 `OUTPUT/CONDITIONAL/ASK/ABSTAIN/HUMAN_REVIEW`；恰好一个 selected action、恰好一个匹配 payload、非空 basis；`UNKNOWN` 不是第六动作。
- UNKNOWN reason code 只接受注册值 `GATE.STATE_UNKNOWN`；未知 code fail closed。
- root 与 timing 分账，timing 永不改写 root。
- `CardIdentityRef.runtime_capability_status` 固定为 `REFERENCE_ONLY_NOT_IMPLEMENTATION_PROOF`。
- trace/statement 内部 ID 只写结构化 artifacts，禁止进入 public report prose。
- artifact item state 只允许 PI-230 八值；set state 只允许 `COMPLETE_VERIFIED/PARTIAL/STALE_MIXED_REVISION/DIGEST_MISMATCH/FAILED`。
- 只有 `COMPLETE_VERIFIED` 可继续 feedback-ready 检查；eligibility evaluation 不执行 learning。
- 单文件用同目录临时文件、flush、`os.fsync()`、`os.replace()`；跨文件不伪装事务。已提交 artifact 不删除、不覆盖未知内容，只能由新 revision supersede。
- Windows `cmd.exe` 命令不得使用 `rm`、`cp`、`mv`、`grep`、`sed`；pytest 命令均从仓库根执行。
- 每个 Task 必须按 failing test → minimal implementation → focused pass → related regression → commit → independent review → rollback 的顺序执行。
- 实现前创建独立 worktree/branch；本计划不指定不存在的命名 skill。建议分支名：`pi-500-r1-f09-slice`。

---

## File Structure Map

### 新建生产文件

| Path | 单一职责 |
|---|---|
| `engine/f09/__init__.py` | 只导出稳定的 opt-in request/result/entrypoint；无导入副作用。 |
| `engine/f09/errors.py` | `F09Error`、`F09IntegrityError`、`F09SourceError`、`F09ContractError`、`F09WriteError`。 |
| `engine/f09/contracts.py` | PI-210/220/230 所需 frozen dataclasses、enums、联合类型及结构验证；不含 I/O。 |
| `engine/f09/canonical_json.py` | 受限 RFC 8785 parser/canonicalizer/digest；不含 F09 业务规则。 |
| `engine/f09/markdown_source.py` | frozen Markdown selector 解析、exact span copy、binding 与 digest 验证。 |
| `engine/f09/json_source.py` | immutable snapshot envelope、五字段身份、RFC 6901 与 LOSSLESS COPY。 |
| `engine/f09/evidence.py` | 构建并验证 PI-210 三轨 evidence package 与 frozen declarations。 |
| `engine/f09/decision.py` | 六成员 gate、participation、F08 identity-only competition、root/timing、五动作决策。 |
| `engine/f09/trace.py` | PI-220 result → PI-230 trace/statement set；逐字段 binding/basis 保真。 |
| `engine/f09/artifacts.py` | artifact state machine、idempotency、原子单文件写、partial/retry/supersede/manifest。 |
| `engine/f09/feedback.py` | exact feedback binding 与 learning eligibility；无 learning side effect。 |
| `engine/f09/application.py` | 显式 opt-in staged/preprod 编排、观测事件、stop condition；不接 production pipeline。 |

### 新建测试文件

| Path | 覆盖责任 |
|---|---|
| `tests/f09/__init__.py` | 测试包标记。 |
| `tests/f09/conftest.py` | 只读 fixture builders；不得执行 YAML。 |
| `tests/f09/test_canonical_json.py` | 受限 RFC 8785、duplicate keys、域外值拒绝。 |
| `tests/f09/test_markdown_source.py` | mdff:v1、digest、唯一性、null/unresolved declaration。 |
| `tests/f09/test_json_source.py` | snapshot identity、JCS digest、RFC 6901、state/event/outcome LOSSLESS。 |
| `tests/f09/test_evidence_contract.py` | 三轨、declaration branches、required participation structures。 |
| `tests/f09/test_decision_contract.py` | 六成员双射、permutation defense、五 action、competition、root/timing。 |
| `tests/f09/test_trace_contract.py` | trace/statement required fields、basis 与 binding 漂移。 |
| `tests/f09/test_artifact_lifecycle.py` | item/set states、partial writes、retry、idempotency、supersede。 |
| `tests/f09/test_feedback_eligibility.py` | exact feedback binding、canonical identity、eligibility-only。 |
| `tests/f09/test_application_opt_in.py` | opt-in、staged/preprod isolation、observability、stop conditions。 |
| `tests/f09/test_f09_vertical_matrix.py` | T01–T104 参数化 vertical acceptance matrix。 |
| `tests/f09/test_production_isolation.py` | production signatures/defaults/import graph/无副作用回归。 |

### 明确不修改

本切片不需要依赖文件变更；不得修改 `requirements-dev.txt`、`pyproject.toml`、所有 mapping/template/META/case/report 文件，以及现有 production、renderer、statement runtime、feedback learning 文件。

---

## Task 1: Immutable Contracts and Closed State Space

**Files:**
- Create: `engine/f09/errors.py`
- Create: `engine/f09/contracts.py`
- Create: `tests/f09/__init__.py`
- Create: `tests/f09/conftest.py`
- Create: `tests/f09/test_evidence_contract.py`

**Interfaces:**
- Consumes: frozen semantics from PI-210/220/230 and PI-300 only.
- `engine/f09/errors.py` defines the closed typed failure carrier used by Tasks 6–8: every validator/coordinator rejection that is a frozen PI-300 issue must raise an `F09Error` subtype carrying immutable nonempty `issue_code: str` and canonical `field_path: str`; diagnostic text remains separate and must never be parsed to recover either field. This is transport typing only and does not add, rename, merge, or reprioritize any frozen issue semantic.
- Copy the following complete contiguous block literally into `engine/f09/errors.py`. It is the sole literal-copy scaffold for that module; constructors reject blank/non-string typed fields, while `diagnostic` is an independent human-readable field and is never a source for issue identity.
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class F09Error(Exception):
    issue_code: str
    field_path: str
    diagnostic: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.issue_code, str) or not self.issue_code.strip():
            raise ValueError("issue_code must be a nonempty string")
        if not isinstance(self.field_path, str) or not self.field_path.strip():
            raise ValueError("field_path must be a nonempty string")
        if not isinstance(self.diagnostic, str):
            raise TypeError("diagnostic must be a string")

    def __str__(self) -> str:
        return self.diagnostic

@dataclass(frozen=True)
class F09IntegrityError(F09Error):
    pass

@dataclass(frozen=True)
class F09SourceError(F09Error):
    pass

@dataclass(frozen=True)
class F09ContractError(F09Error):
    pass

@dataclass(frozen=True)
class F09WriteError(F09Error):
    pass
```
- Tasks 6–8 may catch or raise only the displayed existing subtype set. Every frozen rejection branch constructs the carrier with literal/canonical `issue_code=` and `field_path=` keyword values at detection time; no caller recovers either value from `diagnostic`, `str(error)`, exception class names, fixture values, or status inference.
- `engine/f09/contracts.py` is the one canonical implementation module for the PI-210 conversion ledger types `ObjectRef`, `FieldMapping`, and `TransformationRecord`, and for the transport-only `DetectedIssue` pair reused by Tasks 6–8. They are defined exactly once in this Task 1 interface; every trace module, fixture, and consumer imports and reuses these runtime identities.
- PI-210 remains the sole semantic owner of `RunTrack`; the implementation below is an exact runtime transcription of its five closed values, not an F09-owned alias or extension. Every F09 module imports this same runtime identity, and application request modes never enter canonical track fields.
- Produces the canonical PI-210 source, conversion-ledger, and declaration contracts below. Location (`path/object_id/field_path`) and immutable snapshot identity (`binding`) are deliberately separate; compatibility flattening and dual-write fields are invalid.
- Copy the fenced block into `engine/f09/contracts.py` starting with the displayed import block and ending with the displayed `TransformationRecord.__post_init__()` method. The imports are the complete module scaffolding required by this block; no implicit helper, alias enum, competing type, or undeclared dependency may be added. PI-210 remains the semantic source, while this block is its sole runtime transcription and all downstream modules import/reuse these identities.
```python
from dataclasses import dataclass
from enum import Enum
from typing import Literal, TypeAlias, Union

class RunTrack(str, Enum):
    PRODUCTION_DEFAULT = "PRODUCTION_DEFAULT"
    PARALLEL_DOMAIN = "PARALLEL_DOMAIN"
    STAGED_L6 = "STAGED_L6"
    V5_V6_PREPROD = "V5_V6_PREPROD"
    MANUAL_IMPORT = "MANUAL_IMPORT"

class EvidenceTrack(str, Enum):
    CHART_STRUCTURE = "CHART_STRUCTURE"
    REALITY_FACT = "REALITY_FACT"
    UNVERIFIED_HYPOTHESIS = "UNVERIFIED_HYPOTHESIS"

class GateEvidenceState(str, Enum):
    SATISFIED = "SATISFIED"
    MISSING = "MISSING"
    CONFLICT = "CONFLICT"
    UNKNOWN = "UNKNOWN"

class FieldEvaluatorState(str, Enum):
    EVALUATED = "EVALUATED"
    MISSING = "MISSING"
    CONFLICT = "CONFLICT"
    UNKNOWN = "UNKNOWN"
    NOT_EVALUATED = "NOT_EVALUATED"

class DecisionAction(str, Enum):
    OUTPUT = "OUTPUT"
    CONDITIONAL = "CONDITIONAL"
    ASK = "ASK"
    ABSTAIN = "ABSTAIN"
    HUMAN_REVIEW = "HUMAN_REVIEW"

class ArtifactItemState(str, Enum):
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    WRITING = "WRITING"
    WRITTEN_UNVERIFIED = "WRITTEN_UNVERIFIED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    STALE = "STALE"
    MISMATCH = "MISMATCH"
    SUPERSEDED = "SUPERSEDED"

class ArtifactSetState(str, Enum):
    COMPLETE_VERIFIED = "COMPLETE_VERIFIED"
    PARTIAL = "PARTIAL"
    STALE_MIXED_REVISION = "STALE_MIXED_REVISION"
    DIGEST_MISMATCH = "DIGEST_MISMATCH"
    FAILED = "FAILED"
@dataclass(frozen=True)
class DigestRef:
    algorithm: str
    canonicalization: str
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("value must be a string")
        if len(self.value) != 64 or any(char not in "0123456789abcdef" for char in self.value):
            raise ValueError("value must be a lowercase 64-hex digest")
@dataclass(frozen=True)
class MarkdownContractSourceBinding:
    binding_kind: Literal["MARKDOWN_CONTRACT"]
    binding_schema_version: Literal["source-binding.markdown.v1"]
    source_snapshot_id: str
    source_schema_version: Literal["markdown-source.commonmark-0.31.2-mdff-v1"]
    contract_version: str
    content_digest: DigestRef
    captured_at: str

    def __post_init__(self) -> None:
        if self.binding_kind != "MARKDOWN_CONTRACT":
            raise ValueError("binding_kind must be MARKDOWN_CONTRACT")
        if self.binding_schema_version != "source-binding.markdown.v1":
            raise ValueError("invalid markdown binding_schema_version")
        if self.source_schema_version != "markdown-source.commonmark-0.31.2-mdff-v1":
            raise ValueError("invalid markdown source_schema_version")
        if not isinstance(self.content_digest, DigestRef):
            raise TypeError("content_digest must be DigestRef")
@dataclass(frozen=True)
class ImmutableJsonSourceBinding:
    binding_kind: Literal["IMMUTABLE_JSON_SNAPSHOT"]
    binding_schema_version: Literal["source-binding.immutable-json.v1"]
    source_snapshot_id: str
    source_schema_version: str
    contract_version: str
    content_digest: DigestRef
    captured_at: str

    def __post_init__(self) -> None:
        if self.binding_kind != "IMMUTABLE_JSON_SNAPSHOT":
            raise ValueError("binding_kind must be IMMUTABLE_JSON_SNAPSHOT")
        if self.binding_schema_version != "source-binding.immutable-json.v1":
            raise ValueError("invalid immutable-json binding_schema_version")
        if not isinstance(self.content_digest, DigestRef):
            raise TypeError("content_digest must be DigestRef")
@dataclass(frozen=True)
class UnversionedSourceBinding:
    binding_kind: Literal["UNVERSIONED_SOURCE"]
    binding_schema_version: Literal["source-binding.unversioned.v1"]
    reason_code: Literal["SOURCE_IDENTITY_NOT_VERSIONED"]

    def __post_init__(self) -> None:
        if self.binding_kind != "UNVERSIONED_SOURCE":
            raise ValueError("binding_kind must be UNVERSIONED_SOURCE")
        if self.binding_schema_version != "source-binding.unversioned.v1":
            raise ValueError("invalid unversioned binding_schema_version")
        if self.reason_code != "SOURCE_IDENTITY_NOT_VERSIONED":
            raise ValueError("invalid unversioned reason_code")
SourceBinding: TypeAlias = Union[MarkdownContractSourceBinding, ImmutableJsonSourceBinding, UnversionedSourceBinding]
@dataclass(frozen=True)
class SourceLocator:
    source_id: str
    source_type: Literal["INPUT_FIELD", "FINDING_OBJECT", "CLAIM_OBJECT", "DECISION_OBJECT", "STATEMENT_OBJECT", "FEEDBACK_OBJECT", "FROZEN_CONTRACT_FIELD", "DECLARATIVE_APPENDIX_FIELD", "THEORY_RULE", "HUMAN_ATTESTATION", "TRANSFORMATION_OUTPUT"]
    path: str
    object_id: str | None
    field_path: str | None
    binding: SourceBinding

    def __post_init__(self) -> None:
        if not isinstance(self.binding, (MarkdownContractSourceBinding, ImmutableJsonSourceBinding, UnversionedSourceBinding)):
            raise TypeError("binding must be a closed SourceBinding member")
@dataclass(frozen=True)
class FrozenDeclarationRef:
    declaration_id: str
    declaration_type: Literal["OUTPUT_PRECISION", "VALIDATION_PLAN"]
    card_id: Literal["F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08", "F09", "F10", "F11", "F12"]
    contract_version: str
    declaration_schema_version: str
    content_digest: DigestRef

    def __post_init__(self) -> None:
        if self.declaration_type not in ("OUTPUT_PRECISION", "VALIDATION_PLAN"):
            raise ValueError("invalid declaration_type")
        if self.card_id not in ("F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08", "F09", "F10", "F11", "F12"):
            raise ValueError("invalid card_id")
        if not isinstance(self.content_digest, DigestRef):
            raise TypeError("content_digest must be DigestRef")
@dataclass(frozen=True)
class ResolvedDeclarationBinding:
    presence: Literal["RESOLVED"]
    ref: FrozenDeclarationRef

    def __post_init__(self) -> None:
        if self.presence != "RESOLVED":
            raise ValueError("presence must be RESOLVED")
        if not isinstance(self.ref, FrozenDeclarationRef):
            raise TypeError("ref must be FrozenDeclarationRef")
@dataclass(frozen=True)
class AbsentDeclarationBinding:
    presence: Literal["ABSENT"]
    reason_code: Literal["DECLARATION_NOT_PRESENT"]

    def __post_init__(self) -> None:
        if self.presence != "ABSENT" or self.reason_code != "DECLARATION_NOT_PRESENT":
            raise ValueError("invalid ABSENT declaration binding")
@dataclass(frozen=True)
class NotApplicableDeclarationBinding:
    presence: Literal["NOT_APPLICABLE"]
    reason_code: Literal["DECLARATION_NOT_APPLICABLE"]

    def __post_init__(self) -> None:
        if self.presence != "NOT_APPLICABLE" or self.reason_code != "DECLARATION_NOT_APPLICABLE":
            raise ValueError("invalid NOT_APPLICABLE declaration binding")
@dataclass(frozen=True)
class UnavailableDeclarationBinding:
    presence: Literal["UNAVAILABLE"]
    reason_code: Literal["DECLARATION_UNREAD", "DECLARATION_SOURCE_UNAVAILABLE"]
    issue_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.presence != "UNAVAILABLE":
            raise ValueError("presence must be UNAVAILABLE")
        if self.reason_code not in ("DECLARATION_UNREAD", "DECLARATION_SOURCE_UNAVAILABLE"):
            raise ValueError("invalid UNAVAILABLE reason_code")
        if not isinstance(self.issue_ids, tuple) or not self.issue_ids:
            raise ValueError("issue_ids must be a nonempty tuple")
@dataclass(frozen=True)
class UnresolvableDeclarationBinding:
    presence: Literal["UNRESOLVABLE"]
    attempted_ref: FrozenDeclarationRef
    reason_code: Literal["IDENTITY_MISMATCH", "CONTRACT_VERSION_MISMATCH", "DECLARATION_SCHEMA_VERSION_MISMATCH", "DIGEST_MISMATCH", "BROKEN_REFERENCE"]
    issue_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.presence != "UNRESOLVABLE":
            raise ValueError("presence must be UNRESOLVABLE")
        if not isinstance(self.attempted_ref, FrozenDeclarationRef):
            raise TypeError("attempted_ref must be FrozenDeclarationRef")
        if self.reason_code not in ("IDENTITY_MISMATCH", "CONTRACT_VERSION_MISMATCH", "DECLARATION_SCHEMA_VERSION_MISMATCH", "DIGEST_MISMATCH", "BROKEN_REFERENCE"):
            raise ValueError("invalid UNRESOLVABLE reason_code")
        if not isinstance(self.issue_ids, tuple) or not self.issue_ids:
            raise ValueError("issue_ids must be a nonempty tuple")
FrozenDeclarationBinding: TypeAlias = Union[ResolvedDeclarationBinding, AbsentDeclarationBinding, NotApplicableDeclarationBinding, UnavailableDeclarationBinding, UnresolvableDeclarationBinding]
@dataclass(frozen=True)
class FrozenDeclarationPresenceBindings:
    output_precision_binding: FrozenDeclarationBinding
    validation_plan_binding: FrozenDeclarationBinding

    def __post_init__(self) -> None:
        members = (ResolvedDeclarationBinding, AbsentDeclarationBinding, NotApplicableDeclarationBinding, UnavailableDeclarationBinding, UnresolvableDeclarationBinding)
        if not isinstance(self.output_precision_binding, members):
            raise TypeError("output_precision_binding must be a closed FrozenDeclarationBinding member")
        if not isinstance(self.validation_plan_binding, members):
            raise TypeError("validation_plan_binding must be a closed FrozenDeclarationBinding member")
@dataclass(frozen=True)
class IntegrityIssue:
    issue_id: str
    code: str
    path: str
    message: str
    blocking: bool
@dataclass(frozen=True)
class DetectedIssue:
    issue_code: str
    field_path: str

    def __post_init__(self) -> None:
        if not isinstance(self.issue_code, str) or not self.issue_code.strip():
            raise ValueError("issue_code must be a nonempty string")
        if not isinstance(self.field_path, str) or not self.field_path.strip():
            raise ValueError("field_path must be a nonempty string")
@dataclass(frozen=True)
class ObjectRef:
    object_type: Literal["PACKAGE", "EVIDENCE", "RELATION", "CANDIDATE", "SOURCE_OBJECT", "FINDING", "CLAIM", "DECISION", "STATEMENT", "FEEDBACK", "CARD_FIELD"]
    object_id: str
    external: bool
    source_locator_id: str | None
@dataclass(frozen=True)
class FieldMapping:
    source_field_path: str
    target_field_path: str
    operation: Literal["COPY", "RENAME", "TYPE_PRESERVING_PARSE", "STRUCTURAL_WRAP", "ENUM_EXACT_MAP", "TEXT_PRESERVE", "NO_MAP"]
    fidelity: Literal["LOSSLESS", "PARTIAL", "LOSSY", "UNSUPPORTED"]
@dataclass(frozen=True)
class TransformationRecord:
    transformation_id: str
    adapter_id: str
    adapter_version: str
    source_object_refs: tuple[ObjectRef, ...]
    target_object_refs: tuple[ObjectRef, ...]
    fidelity: Literal["LOSSLESS", "PARTIAL", "LOSSY", "UNSUPPORTED"]
    field_mappings: tuple[FieldMapping, ...]
    dropped_fields: tuple[str, ...]
    dropped_object_refs: tuple[ObjectRef, ...]
    synthesized_fields: tuple[str, ...]
    issues: tuple[str, ...]
    transformed_at: str

    def __post_init__(self) -> None:
        collections = (
            self.source_object_refs,
            self.target_object_refs,
            self.field_mappings,
            self.dropped_fields,
            self.dropped_object_refs,
            self.synthesized_fields,
            self.issues,
        )
        if any(not isinstance(value, tuple) for value in collections):
            raise TypeError("TransformationRecord collections must be tuples")
```
- `RESOLVED` 只允许 `ref`；`UNRESOLVABLE` 只允许 `attempted_ref + fixed reason_code + nonempty issue_ids`。`FrozenDeclarationPresenceBindings` 是 Task 1 对 closed union 的实际消费边界，只承载已经冻结的 output-precision/validation-plan presence bindings 并逐字段拒绝非 union member；它不承载、推断或新增 declaration value/source-state。声明 binding presence 与声明 value/source state 是 package 中两个独立字段，不能塞回 union；后者由拥有该 package 的 Task 4 定义和测试。
- `DetectedIssue` is transport-only and does not define issue semantics. A Task 6–8 validator/coordinator creates it only at the production detection branch that already owns the frozen issue, with code and path supplied together; it cannot be synthesized later from state, code-only `issue_ids`, reason codes, diagnostics, or test expectations.
- Tuple rejection in Task 1 is limited to the top-level containers of the seven fields explicitly listed by `TransformationRecord.__post_init__()`; Task 1 does not claim deep immutability or recursively validate their elements. All validators return new immutable results or raise `F09ContractError`.
- Canonical ownership invariant: the three conversion-ledger classes and `DetectedIssue` above occur only in `engine/f09/contracts.py`. No later task may redeclare, subclass, wrap with a competing element type, or define a structurally equivalent local class; imports are mandatory so `isinstance` and type identity remain stable across contracts, trace, artifacts, feedback, fixtures, and consumers. Task 1 proves identity only for the canonical identities it creates and the Task 1 fixture that can import them. Each later task that creates evidence, trace, artifact, or feedback modules must add its own runtime-identity assertion proving that module imports/reuses the exact `engine.f09.contracts.RunTrack`, `ObjectRef`, `FieldMapping`, `TransformationRecord`, and `DetectedIssue` identities it consumes; no assertion against a not-yet-created module belongs to Task 1.

- [ ] **Step 1: Write the failing tests.** Define exact `RunTrack` enum-value assertion equal to `PRODUCTION_DEFAULT | PARALLEL_DOMAIN | STAGED_L6 | V5_V6_PREPROD | MANUAL_IMPORT` with no alias/extension; frozen mutation rejection; `DigestRef.value` non-string rejection before lowercase 64-hex shape rejection; every declaration member's discriminant/reference rejection, including rejection of an `UNAVAILABLE` binding with empty `issue_ids`, plus `FrozenDeclarationPresenceBindings` rejection of non-union members; required-field rejection; and a runtime-identity assertion proving the Task 1 fixture imports the exact `engine.f09.contracts.RunTrack` runtime identity and exact conversion-ledger classes in `tests/f09/test_evidence_contract.py`. Explicit-null-vs-omitted tests in Task 1 are limited to Task 1-owned optional constructor fields such as `SourceLocator.object_id` and `SourceLocator.field_path`: explicit `None` constructs, while omitting a required constructor argument raises `TypeError`; these tests must not claim declaration value/source-state coverage. Declaration value/source-state explicit-null-vs-absent coverage is deferred to Task 4, which owns `DeclarationObservation` and the package. For collection shape, test only that mutable `list`/`dict` values supplied as the top-level containers of the seven tuple-declared `TransformationRecord` fields are rejected; do not claim deep immutability. Do not import or assert identity against evidence, trace, artifact, or feedback modules before their owning tasks create them; each owning task must add that module's import/reuse identity assertion when it is created.
- [ ] **Step 2: Verify RED.** Run `python -m pytest tests/f09/test_evidence_contract.py -q`. Expected: FAIL during collection with `ModuleNotFoundError: No module named 'engine.f09'`.
- [ ] **Step 3: Implement minimal contracts.** Copy the single complete `engine/f09/contracts.py` literal block above, including its displayed `__post_init__()` methods and the presence-only `FrozenDeclarationPresenceBindings` consumer, as the complete and unique implementation source. Those methods are the exhaustive Task 1 authorization for stable non-string rejection followed by lowercase 64-hex digest shape, closed `SourceBinding`/declaration discriminants and declaration-reference binding, closed-union consumption at the two frozen presence-binding fields, nonempty-tuple `UNAVAILABLE.issue_ids` and `UNRESOLVABLE.issue_ids`, and tuple-only top-level containers for the seven displayed `TransformationRecord` fields. Do not add a helper, validator, field, alias, dependency, declaration value/source-state, or extra semantic outside or beyond that block; dataclass construction supplies required-field mechanics, and enum construction supplies closed enum values.
- [ ] **Step 4: Verify GREEN.** Run `python -m pytest tests/f09/test_evidence_contract.py -q`. Expected: all tests PASS.
- [ ] **Step 5: Run regression.** Run `python -m pytest tests/test_production_entrypoints_unchanged.py::test_run_pipeline_signature_and_defaults_are_unchanged tests/test_performance_and_ports.py::test_run_pipeline_e2e_accepts_explicit_adapters -q`. Expected: `2 passed`.
- [ ] **Step 6: Commit.** Run `git add engine/f09/errors.py engine/f09/contracts.py tests/f09/__init__.py tests/f09/conftest.py tests/f09/test_evidence_contract.py && git commit -m "feat(f09): define closed vertical-slice contracts"`.
- [ ] **Independent review gate.** Fresh reviewer checks every enum against PI-210/220/230, confirms no local synonym such as `NOT_STARTED` or `WRITTEN`, searches the planned implementation for exactly one class definition of each canonical conversion-ledger type under `engine/f09/contracts.py`, verifies all other uses are imports, and runs the focused and regression commands.
- [ ] **Rollback.** Before later tasks depend on it: `git revert --no-edit HEAD`. After dependency exists: revert dependent commits newest-first; do not rewrite published contract artifacts.

> **Bounded remediation note (Task 1 only):** This edit records only the static closure of the fixed High finding: the sole literal-copy block now requires `UnavailableDeclarationBinding.issue_ids` to be a nonempty tuple, matching the already explicit `UnresolvableDeclarationBinding.issue_ids` invariant, and Task 1 Steps 1 and 3 state that same bounded requirement. No field, declaration semantic, copy boundary, enum/field graph, F09/F08 scope, or production default is changed. Static rereading proves only that these Task 1 plan lines are textually aligned; it does not prove implementation, parse, collection, runtime behavior, tests, G6, or any PASS status.

## Task 2: Bounded RFC 8785 Canonical JSON

**Files and read dependency:**
- Create only: `engine/f09/canonical_json.py`
- Create only: `tests/f09/test_canonical_json.py`
- Read-only immutable fixture dependency: `plans/production-implementation-pi-300-f09-source-snapshots-v1.json`; tests read its unique top-level `payload` member and never modify the fixture. No YAML/mapping file is read or executed.

**Closed domain and interfaces:** Task 2 intentionally implements only the number-free RFC 8785-compatible subset. It does not claim complete RFC 8785 number support. The accepted runtime graph uses exact built-in types only: `None`, `bool`, `str`, `tuple`, and `dict`; subclasses, every numeric type, `list`, arbitrary `Mapping`, bytes-like values, sets, custom objects, and cyclic containers are rejected recursively. `bool` is accepted before the numeric rejection because Python `bool` subclasses `int`. Parser objects are exact built-in `dict` instances and parser arrays are tuples. Duplicate-key semantics exist only for raw JSON object pairs; an already constructed `dict` cannot carry duplicate keys.

```python
from typing import TypeAlias, Union

from engine.f09.contracts import DigestRef

JcsValue: TypeAlias = Union[
    None,
    bool,
    str,
    tuple["JcsValue", ...],
    dict[str, "JcsValue"],
]

def parse_bounded_jcs(raw: bytes) -> JcsValue: ...
def canonicalize_bounded_jcs(value: JcsValue) -> bytes: ...
def bounded_jcs_sha256(value: JcsValue) -> DigestRef: ...
```

`bounded_jcs_sha256(value)` hashes exactly `canonicalize_bounded_jcs(value)` and returns exactly:

```python
DigestRef(
    algorithm="sha256",
    canonicalization="RFC8785-JCS-UTF8",
    value=hashlib.sha256(canonical_bytes).hexdigest(),
)
```

The digest value is therefore exactly 64 lowercase hexadecimal characters. The frozen digest oracle is the unique top-level `payload` value parsed from the read-only fixture above; its canonical digest is exactly `67517fe2d04fb0fe580e031643dab2ad53fcdb8c90707ba4d496c316dd87f5e7`. The digest is not computed over the fixture's raw file bytes or its outer envelope.

**Failure contract:** Every Task 2 rejection raises the canonical Task 1 `F09ContractError` imported from `engine.f09.errors`. The exact issue pairs are:

| Failure class | `issue_code` | `field_path` |
|---|---|---|
| non-`bytes` parser input, BOM, malformed UTF-8, JSON syntax/trailing data | `JCS.PARSE_INVALID` | `/raw` |
| duplicate object key | `JCS.DUPLICATE_KEY` | `/raw` |
| integer, float, exponent number, `NaN`, `Infinity`, `-Infinity` in raw JSON | `JCS.NUMBER_UNSUPPORTED` | `/raw` |
| raw parser graph deeper than `MAX_DEPTH = 64`, including a parser `RecursionError` | `JCS.DEPTH_EXCEEDED` | `/raw` |
| direct or nested runtime value outside the exact closed domain, including non-string keys and subclasses | `JCS.TYPE_UNSUPPORTED` | `/value` |
| lone or paired surrogate code units in any key or string value, raw escaped or direct | `JCS.INVALID_UNICODE` | `/value` |
| direct or indirect container cycle | `JCS.CYCLE_DETECTED` | `/value` |
| runtime graph deeper than `MAX_DEPTH = 64`, including a defensive `RecursionError` | `JCS.DEPTH_EXCEEDED` | `/value` |
| `_snapshot_dict()` raises `RuntimeError` while taking the single snapshot of a caller-controlled dict | `JCS.MUTATION_DETECTED` | `/value` |

Diagnostic text is non-normative. Root depth is zero and every array element or object value descent adds one; any descent whose depth is greater than `MAX_DEPTH = 64` is rejected. Validation covers the top level, every tuple element, and every dict key/value. A container identity is added to an active recursion set before descending and removed after that branch; repeated non-cyclic shared containers are allowed. For each public canonicalization operation, `_prepare()` uses an operation-local identity memo. Each memo entry strongly references its source exact dict and stores both the completed prepared object and that object's maximum relative descendant depth. Each exact built-in caller-controlled `dict` is snapshotted at most once; a repeated identity first confirms object identity against the strong reference, then rejects when `current_depth + relative_depth > MAX_DEPTH`, otherwise reuses the completed prepared object. An identity still active is a cycle, and incomplete objects never enter the memo. The prepared object is both the validation result and the sole encoder input. Callers must not modify any supplied dict concurrently with canonicalization. If `_snapshot_dict()` observes such interference by raising `RuntimeError`, that exception is converted deterministically to `JCS.MUTATION_DETECTED` at `/value`; concurrent mutation, including value replacement or ABA mutation, that does not cause `_snapshot_dict()` to raise `RuntimeError` is outside the detectable-mutation guarantee. Encoding never iterates caller data. Parser-created dicts may first be traversed by the private parser normalizer because they are newly owned by the parser rather than caller-controlled runtime inputs; subsequent validation still uses `_prepare()`.

**Parser contract:** `parse_bounded_jcs()` requires exact built-in `bytes`, rejects an `EF BB BF` prefix before decoding, decodes with strict UTF-8, rejects malformed UTF-8 and JSON syntax/trailing data as `JCS.PARSE_INVALID`, rejects duplicate keys in `object_pairs_hook`, rejects every number through both `parse_int` and `parse_float`, and rejects `NaN`/`Infinity`/`-Infinity` through `parse_constant`. Standard-library parsing creates an internal temporary graph in which objects are exact built-in `dict` and arrays are exact built-in `list`; those lists are not part of the public accepted runtime domain. `_normalize_parsed()` recursively converts every temporary exact list to tuple, recursively rebuilds parser-owned exact dict values as exact dicts, and leaves legal scalars unchanged while enforcing `MAX_DEPTH`. A `RecursionError` from JSON parsing or normalization is converted to `JCS.DEPTH_EXCEEDED` at `/raw`. The normalized graph is then passed to the same `_prepare()` recursive scalar/domain validation used by the canonicalizer. JSON booleans remain valid booleans.

**String and ordering contract:** Every key and string value, including nested and top-level values, must contain only Unicode scalar values; any code point in `U+D800..U+DFFF` is rejected before sorting, JSON escaping, or UTF-8 encoding. Object keys sort by `key.encode("utf-16-be")`, not Python code-point order. The two frozen discriminating pairs are `"\U00010000"` versus `"\uE000"` and `"\U00010001"` versus `"\uE001"`; in each pair UTF-16 code-unit order places the supplementary scalar first while Python code-point order places the BMP scalar first.

`_encode_string(value)` may call `json.dumps(value, ensure_ascii=False, separators=(",", ":"))` only after scalar validation and then encode the result as UTF-8. Exact escaping assertions are: quote → `\"`; reverse solidus → `\\`; U+0008/U+0009/U+000A/U+000C/U+000D → `\b`/`\t`/`\n`/`\f`/`\r`; another U+0000..U+001F character, including U+0000, uses lowercase `\u00xx`; solidus is not escaped; valid non-ASCII scalar values are emitted directly as UTF-8. Canonical output never contains a BOM. Arrays retain input order; object insertion order never affects output.

**Complete implementation source:** Implementers copy the following block continuously as the complete `engine/f09/canonical_json.py`; no additional public interface, dependency, fallback type, number support, custom Mapping support, or alternative digest path is authorized.

```python
import hashlib
import json
from dataclasses import dataclass
from typing import TypeAlias, Union

from engine.f09.contracts import DigestRef
from engine.f09.errors import F09ContractError

MAX_DEPTH = 64

JcsValue: TypeAlias = Union[
    None,
    bool,
    str,
    tuple["JcsValue", ...],
    dict[str, "JcsValue"],
]


@dataclass(frozen=True)
class _PNull:
    pass


@dataclass(frozen=True)
class _PBool:
    value: bool


@dataclass(frozen=True)
class _PString:
    value: str


@dataclass(frozen=True)
class _PArray:
    items: tuple["_Prepared", ...]


@dataclass(frozen=True)
class _PObject:
    items: tuple[tuple[str, "_Prepared"], ...]


_Prepared: TypeAlias = Union[_PNull, _PBool, _PString, _PArray, _PObject]


@dataclass(frozen=True)
class _MemoEntry:
    source: dict[object, object]
    prepared: _Prepared
    relative_depth: int


def _reject(issue_code: str, field_path: str) -> None:
    raise F09ContractError(
        issue_code=issue_code,
        field_path=field_path,
        diagnostic="bounded JCS contract rejection",
    )


def _validate_string(value: str) -> None:
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        _reject("JCS.INVALID_UNICODE", "/value")


def _snapshot_dict(value: dict[object, object]) -> tuple[tuple[object, object], ...]:
    return tuple(value.items())


def _prepare(
    value: object,
    active: set[int],
    memo: dict[int, _MemoEntry],
    depth: int,
) -> tuple[_Prepared, int]:
    if depth > MAX_DEPTH:
        _reject("JCS.DEPTH_EXCEEDED", "/value")
    if value is None:
        return (_PNull(), 0)
    if type(value) is bool:
        return (_PBool(value), 0)
    if type(value) is str:
        _validate_string(value)
        return (_PString(value), 0)
    if type(value) is tuple:
        identity = id(value)
        if identity in active:
            _reject("JCS.CYCLE_DETECTED", "/value")
        active.add(identity)
        try:
            children = tuple(
                _prepare(item, active, memo, depth + 1)
                for item in value
            )
            relative_depth = (
                0 if not children
                else 1 + max(child_depth for _, child_depth in children)
            )
            return (
                _PArray(tuple(child for child, _ in children)),
                relative_depth,
            )
        finally:
            active.remove(identity)
    if type(value) is dict:
        identity = id(value)
        if identity in active:
            _reject("JCS.CYCLE_DETECTED", "/value")
        if identity in memo:
            entry = memo[identity]
            if entry.source is not value:
                _reject("JCS.TYPE_UNSUPPORTED", "/value")
            if depth + entry.relative_depth > MAX_DEPTH:
                _reject("JCS.DEPTH_EXCEEDED", "/value")
            return (entry.prepared, entry.relative_depth)
        active.add(identity)
        try:
            try:
                items = _snapshot_dict(value)
            except RuntimeError:
                _reject("JCS.MUTATION_DETECTED", "/value")
            children = []
            for key, item in items:
                if type(key) is not str:
                    _reject("JCS.TYPE_UNSUPPORTED", "/value")
                _validate_string(key)
                child, child_depth = _prepare(
                    item,
                    active,
                    memo,
                    depth + 1,
                )
                children.append((key, child, child_depth))
            relative_depth = (
                0 if not children
                else 1 + max(child_depth for _, _, child_depth in children)
            )
            prepared = _PObject(tuple(
                (key, child) for key, child, _ in children
            ))
            memo[identity] = _MemoEntry(
                source=value,
                prepared=prepared,
                relative_depth=relative_depth,
            )
            return (prepared, relative_depth)
        finally:
            active.remove(identity)
    _reject("JCS.TYPE_UNSUPPORTED", "/value")


def _encode_string(value: str) -> bytes:
    _validate_string(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _encode(prepared: _Prepared) -> bytes:
    if isinstance(prepared, _PNull):
        return b"null"
    if isinstance(prepared, _PBool):
        return b"true" if prepared.value else b"false"
    if isinstance(prepared, _PString):
        return _encode_string(prepared.value)
    if isinstance(prepared, _PArray):
        return b"[" + b",".join(
            _encode(item) for item in prepared.items
        ) + b"]"
    if isinstance(prepared, _PObject):
        ordered = sorted(
            prepared.items,
            key=lambda item: item[0].encode("utf-16-be"),
        )
        return b"{" + b",".join(
            _encode_string(key) + b":" + _encode(item)
            for key, item in ordered
        ) + b"}"
    _reject("JCS.TYPE_UNSUPPORTED", "/value")


def _duplicate_checked_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _reject("JCS.DUPLICATE_KEY", "/raw")
        result[key] = value
    return result


def _reject_number(_value: str) -> None:
    _reject("JCS.NUMBER_UNSUPPORTED", "/raw")


def _normalize_parsed(value: object, depth: int) -> object:
    if depth > MAX_DEPTH:
        _reject("JCS.DEPTH_EXCEEDED", "/raw")
    if type(value) is list:
        return tuple(
            _normalize_parsed(item, depth + 1)
            for item in value
        )
    if type(value) is dict:
        return {
            key: _normalize_parsed(item, depth + 1)
            for key, item in value.items()
        }
    return value


def parse_bounded_jcs(raw: bytes) -> JcsValue:
    if type(raw) is not bytes or raw.startswith(b"\xef\xbb\xbf"):
        _reject("JCS.PARSE_INVALID", "/raw")
    try:
        text = raw.decode("utf-8", errors="strict")
        parsed = json.loads(
            text,
            object_pairs_hook=_duplicate_checked_object,
            parse_int=_reject_number,
            parse_float=_reject_number,
            parse_constant=_reject_number,
        )
        normalized = _normalize_parsed(parsed, 0)
    except F09ContractError:
        raise
    except RecursionError:
        _reject("JCS.DEPTH_EXCEEDED", "/raw")
    except (UnicodeDecodeError, json.JSONDecodeError):
        _reject("JCS.PARSE_INVALID", "/raw")
    try:
        _prepare(normalized, set(), {}, 0)
    except RecursionError:
        _reject("JCS.DEPTH_EXCEEDED", "/raw")
    return normalized


def canonicalize_bounded_jcs(value: JcsValue) -> bytes:
    try:
        prepared, _ = _prepare(value, set(), {}, 0)
        return _encode(prepared)
    except F09ContractError:
        raise
    except RecursionError:
        _reject("JCS.DEPTH_EXCEEDED", "/value")


def bounded_jcs_sha256(value: JcsValue) -> DigestRef:
    canonical_bytes = canonicalize_bounded_jcs(value)
    return DigestRef(
        algorithm="sha256",
        canonicalization="RFC8785-JCS-UTF8",
        value=hashlib.sha256(canonical_bytes).hexdigest(),
    )
```

- [ ] **Step 1: Write RED tests.** The focused file must collect exactly **46 parameter instances**, with no skip/xfail/xpass. The one-to-one instance ledger is: frozen fixture parse/canonical digest 1; two insertion-order variants 2; the frozen `U+10000/U+E000` and `U+10001/U+E001` UTF-16 discriminating pairs 2; legal `null/true/false/ASCII/non-ASCII` scalars 5; empty tuple/nested tuple/empty object/nested object-tuple 4; escaping instances fixed exactly as (E1) quote, (E2) reverse solidus, (E3) all five short escapes asserted together, (E4) U+0000 lowercase `\\u0000`, and (E5) unescaped solidus 5; raw BOM/malformed UTF-8/duplicate key/integer/float/exponent/NaN/Infinity/-Infinity rejection 9; direct non-string key/integer/float/list/bytes/custom object/key surrogate/value surrogate/nested illegal/cycle rejection 10; explicit true/false success versus integer `1/0` rejection 4; and bounded-safety instances fixed exactly as (B1) raw depth 65 rejects at `/raw`, (B2) one runtime graph places a shared dict-with-one-child first at depth 1 to populate memo and then at depth 64 so its descendant reaches depth 65, rejecting `JCS.DEPTH_EXCEEDED` at `/value`, (B3) one shared dict identity used twice produces equal output branches and one `_MemoEntry` whose `source is shared`, whose prepared branches are reused, and whose `relative_depth` is exact under a private `_prepare()` white-box assertion, and (B4) a deterministic monkeypatched private snapshot helper raises `RuntimeError` and proves only the stable mapping to `JCS.MUTATION_DETECTED` at `/value`, not comprehensive concurrent-mutation detection, 4. The literal implementation must expose private `_snapshot_dict(value)` solely so B4 can monkeypatch it; production code calls it exactly once per uncached dict identity. Each named item is one parameter instance except E3, which is one parameter instance carrying exactly five short-escape assertions. These 46 ledger instances may not be collapsed or regrouped.
- [ ] **Step 2: Verify RED under a separately authorized command envelope.** Run exactly `python -m pytest tests/f09/test_canonical_json.py -q`. Expected: collection fails only because `engine.f09.canonical_json` is absent; this is zero behavior evidence and does not authorize repair or rerun.
- [ ] **Step 3: Implement parser and canonicalizer.** Copy only the continuous implementation block above. Do not call `AnalysisOutput.hash()`, do not use `json.dumps(sort_keys=True)`, and do not add full-number or arbitrary-Mapping support.
- [ ] **Step 4: Verify GREEN under a new separately authorized command envelope.** Run exactly `python -m pytest tests/f09/test_canonical_json.py -q`. Expected: exactly `46 passed`, `0 failed`, `0 errors`, `0 skipped`, `0 xfailed`, `0 xpassed`, and the frozen payload digest exactly matches.
- [ ] **Step 5: Regression under the same explicit verification envelope only if separately listed there.** Run exactly `python -m pytest tests/evaluation/test_task8_baseline.py::test_canonical_digest_is_order_independent tests/test_production_entrypoints_unchanged.py -q`. Expected: exit 0 with all collected selectors passed; the first selector owns its existing baseline digest assertion. Task 2 does not rewrite or infer that baseline value.
- [ ] **Local Git delivery is outside the Task 2 default envelope.** No `git add`, commit, revert, branch, tag, remote, or GitHub operation is part of implementation or verification. A future local-Git action, if any, requires a separate exact non-inherited authorization. GitHub service-side mutation is permanently forbidden. Any authorized rollback must name exact local paths or an exact immutable commit identifier; floating `HEAD` is forbidden.
- [ ] **Independent review gate.** A fresh reviewer confirms exact two-path scope, continuous-block fidelity, canonical Task 1 imports, parser temporary-list normalization, operation-local identity memoization with source strong references and relative-depth checks on memo hits, one caller-controlled dict snapshot per identity per canonicalization, cycle-before-memo ordering, the caller prohibition on concurrent dict mutation, only the stable `_snapshot_dict()` `RuntimeError` mapping rather than comprehensive mutation detection, depth error mapping, closed prepared variants with exhaustive encoding, exact built-in recursive closure, all issue-code/path pairs, 46-instance static accounting including fixed E1–E5 and B1–B4 groups, both frozen discriminating key pairs, number rejection rather than approximate serialization, no YAML/mapping access, and no local/remote Git side effect.
- [ ] **STOP conditions.** Stop on any missing/duplicate Task 2 selector, deviation from the two-path whitelist or continuous block, unavailable/mutated fixture, digest mismatch, test count drift, skip/xfail/xpass, unexpected RED cause, any failed verification, need for a new dependency or full-number/Mapping support, production-default change, F08 execution, YAML/mapping access, unauthorized command/rerun/repair/Git/state write, or any possible GitHub mutation. A failure expires every inactive successor authorization.

> **Bounded remediation note (Task 2 only):** This replacement closes only the Task 2 mechanical contract gaps identified by the fresh CONTRACT reviews: canonical `DigestRef` ownership/construction; immutable payload oracle; typed failure pairs; exact built-in object domain; bool-before-number and complete recursive validation; cycle/subclass policy; explicit parser temporary-list-to-tuple normalization; operation-local shared-dict identity memoization with source strong references and maximum relative-depth enforcement on every reuse path; one prepared snapshot per dict identity; caller prohibition on concurrent dict mutation and stable mapping only when `_snapshot_dict()` raises `RuntimeError`, with no guarantee of detecting mutation that raises no such error; fixed depth failures; closed private prepared variants with exhaustive encoding; strict UTF-8/BOM behavior; all-string surrogate rejection; exact escaping with frozen E1–E5 grouping; two frozen discriminating UTF-16 pairs; 46-instance accounting with B1–B4 safety checks; and removal of Git/`HEAD` rollback from the default envelope. It does not modify Task 1, Task 3–10, frozen F01–F12 semantics, F08 identity-only status, production defaults, fixture content, implementation files, or dynamic evidence. Static text alignment does not prove parseability, collection, runtime, digest reproduction, tests, G6, or implementation PASS.

## Task 3: Frozen Markdown and Immutable JSON Source Resolution

**Files:**
- Create: `engine/f09/markdown_source.py`
- Create: `engine/f09/json_source.py`
- Create: `tests/f09/test_markdown_source.py`
- Create: `tests/f09/test_json_source.py`

**Interfaces:**
```python
@dataclass(frozen=True)
class FrozenFieldObservation: ref: str; copied_value: object; locator: SourceLocator; transformation: Literal["MDFF_V1_COPY", "LOSSLESS_COPY"]
def resolve_markdown_frozen_field(locator: SourceLocator, ref: str, *, expected_digest: DigestRef) -> FrozenFieldObservation
def load_snapshot(path: Path) -> ImmutableSnapshotEnvelope
def resolve_json_pointer(root: JcsValue, pointer: str) -> JcsValue
def resolve_snapshot_field(snapshot: ImmutableSnapshotEnvelope, *, locator: SourceLocator) -> FrozenFieldObservation
```
- Snapshot identity tuple is exactly `source_snapshot_id/snapshot_schema_version/contract_version/content_digest/captured_at`.

- [ ] **Step 1: Write Markdown RED tests.** Assert canonical F09 hard-gate selector resolves exact text in `engine/contracts/12-real-world-function-evidence-cards-v1.md`; the actual 437-CRLF file and an LF-only equivalent both normalize to LF and produce digest `30ea0f8b8a91f95bc0a52ff90188740c2cc2282fcab27cd20be70404253d7a2f`; null/unresolved declarations remain separate；BOM、bare CR、nonunique/noncanonical/fuzzy selectors fail。
- [ ] **Step 2: Write JSON RED tests.** Assert 13 frozen pointers resolve, escaped `~0/~1` behavior is RFC 6901-compliant, pointers are object-rooted, state/event/outcome identities cannot interchange, and any five-field identity or payload digest drift fails.
- [ ] **Step 3: Verify RED.** Run `python -m pytest tests/f09/test_markdown_source.py tests/f09/test_json_source.py -q`. Expected: collection FAIL for missing modules.
- [ ] **Step 4: Implement exact resolvers.** Parse Markdown line-by-line with exact ATX heading/card/label tokens and uniqueness counts; do not use regex/fuzzy aliases for semantic lookup. Read snapshot once, parse with `parse_bounded_jcs()`, digest only `payload`, then resolve pointers from selected object `value`.
- [ ] **Step 5: Verify GREEN.** Run the Step 3 command. Expected: all tests PASS.
- [ ] **Step 6: Regression.** Run `python -m pytest tests/test_project_metadata.py tests/test_production_entrypoints_unchanged.py -q`. Expected: PASS; no frozen file modified.
- [ ] **Step 7: Commit.** `git add engine/f09/markdown_source.py engine/f09/json_source.py tests/f09/test_markdown_source.py tests/f09/test_json_source.py && git commit -m "feat(f09): resolve frozen markdown and snapshot sources"`.
- [ ] **Independent review gate.** Reviewer recomputes both known digests through test APIs, inspects that the YAML mapping is never loaded, and confirms every failure returns a typed blocking issue or exception without fallback.
- [ ] **Rollback.** `git revert --no-edit HEAD`; frozen source files are never changed.

## Task 4: PI-210 Evidence Package and Declaration Resolver

**Files:**
- Create: `engine/f09/evidence.py`
- Modify: `tests/f09/conftest.py`
- Modify: `tests/f09/test_evidence_contract.py`

**Interfaces:**
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
def build_f09_evidence_package(*, case_id: str, track: RunTrack, markdown_path: Path, snapshot_path: Path, chart_records: tuple[EvidenceRecord, ...], hypothesis_records: tuple[EvidenceRecord, ...]) -> NormalizedEvidencePackage
def validate_for_pi220(package: NormalizedEvidencePackage) -> Literal["READY", "INVALID", "BLOCKED"]
def trace_to_sources(package: NormalizedEvidencePackage, object_id: str) -> tuple[SourceLocator, ...]
```
`EvidenceRecord` 不重复保存 `SourceBinding`；唯一 binding 位于 `locator.binding`。F09 output precision 的 `DeclarationObservation` 必须是 `ResolvedDeclarationBinding + value=None + source_state="BOTH_NULL_AND_UNRESOLVED"`。

- [ ] **Step 1: Add RED tests.** Cover three-track isolation, theory/hypothesis cannot satisfy reality, state/event separation, temporal scope separation, all five declaration branches, invalid F09 `NOT_APPLICABLE`, and F09 precision `RESOLVED + null + BOTH_NULL_AND_UNRESOLVED`.
- [ ] **Step 2: Verify RED.** `python -m pytest tests/f09/test_evidence_contract.py -q`; expected FAIL on missing `build_f09_evidence_package`.
- [ ] **Step 3: Implement minimal package builder.** Consume only explicit arguments and frozen source APIs; never inspect reports, labels, feedback, mapping YAML or historical cases.
- [ ] **Step 4: Verify GREEN.** Repeat Step 2; expected PASS.
- [ ] **Step 5: Regression.** `python -m pytest tests/application/test_staged_parallel_runner.py::test_parallel_and_comparison_modules_have_no_forbidden_imports tests/ziping_career/test_production_isolation.py::test_staged_modules_do_not_import_default_registry_pipeline_reports_or_timing -q`; expected `2 passed`.
- [ ] **Step 6: Commit.** `git add engine/f09/evidence.py tests/f09/conftest.py tests/f09/test_evidence_contract.py && git commit -m "feat(f09): normalize three-track evidence package"`.
- [ ] **Independent review gate.** Reviewer verifies every SATISFIED reality fact terminates at immutable JSON, no chart/hypothesis promotion exists, and every declaration branch preserves attempted refs/issues.
- [ ] **Rollback.** `git revert --no-edit HEAD` after first reverting Tasks that import `evidence.py`.

## Task 5: PI-220 Six-Member Decision Protocol

**Files:**
- Create: `engine/f09/decision.py`
- Create: `tests/f09/test_decision_contract.py`
- Modify: `tests/f09/conftest.py`

**Interfaces:** 以下字段图是 Task 5 的唯一 wire contract；实现者不得改名、扁平化、增加同义字段或跳回其他文档补字段。`IntegrityState`、`FrozenCardFieldRef`、`FrozenDeclarationBinding`、`DigestRef` 逐值复用 Task 1/4 已内联的 PI-210 类型；`ContractIntegrityResult` 是冻结契约端口的不可变返回对象，不得用 evaluator state 代替。
```python
FunctionId: TypeAlias = Literal["F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08", "F09", "F10", "F11", "F12"]
StructuralReadinessState: TypeAlias = Literal["READY", "INCOMPLETE", "DISPUTED", "BLOCKED"]
ConstraintCheckState: TypeAlias = Literal["SATISFIED", "VIOLATED", "UNKNOWN", "NOT_APPLICABLE"]
ParticipationRole: TypeAlias = Literal["SINGLE_SCHOOL_COMPLETE_NATAL_CHAIN", "DAIYUN_STAGE_EFFECT", "LIUNIAN_SPECIFIC_EVENT_TRIGGER", "REAL_WORLD_FUNCTION_GATE", "BREAK_CONDITION_OR_VALID_FALSIFIER", "SOURCE_GATE"]
ParticipationState: TypeAlias = Literal["SATISFIED", "MISSING", "CONFLICT", "UNKNOWN", "NOT_APPLICABLE"]
BasisRecordIds: TypeAlias = tuple[str, ...]  # nonempty; IDs resolve only inside this DecisionEvaluationResult
FieldPathIssueRef: TypeAlias = str

@dataclass(frozen=True)
class GateInputState:
    allocation_state: str; risk_state: str; reality_state: str; attribution_state: str; source_state: str; temporal_state: str
    risk_reason_codes: tuple[str, ...]; allocation_reason_codes: tuple[str, ...]; member_ids: tuple[str, ...]
    declared_member_ids: tuple[str, ...]; gate_definition_ref: str; record_gate_definition_refs: tuple[str, ...]
    evaluation_binding_digests: tuple[str, ...]; supporting_evidence_tracks: tuple[str, ...]; path_complete: bool

@dataclass(frozen=True)
class DeclarationInputState:
    precision_presence: str; precision_value: str | None; precision_unresolved: bool; precision_type: str
    precision_digest: str; precision_contract_version: str; validation_type: str; validation_digest: str
    attempted_digest: str | None; identity_complete: bool; statement_precision_digest: str; trace_precision_digest: str

@dataclass(frozen=True)
class DecisionInputState:
    selected_action: str; payload_type: str; payload_issue_ids: tuple[str, ...]; question_paths: tuple[str, ...]
    basis_gate_ids: tuple[str, ...]; basis_participation_ids: tuple[str, ...]; disposition_refs: tuple[str, ...]
    candidate_ids: tuple[str, ...]; dispositions: tuple[str, ...]; f08_runtime_objects: tuple[str, ...]
    require_two_candidates: bool; consequence_only: bool

@dataclass(frozen=True)
class ParticipationInputState:
    role_ids: tuple[str, ...]; reality_record_id: str; scenario_id: str; state_support_aligned: bool; source_decision_ref: str

@dataclass(frozen=True)
class RootTimingInputState:
    root_state: str; root_reason_code: str | None; root_issue_path: str | None
    timing_state: str; timing_reason_code: str | None; timing_issue_path: str | None; timing_rewrites_root: bool

@dataclass(frozen=True)
class SourceInputState:
    locator_available: bool; reality_track: str; state_object_id: str; state_pointer: str; state_fields: tuple[str, ...]
    event_object_id: str; event_pointer: str; event_fields: tuple[str, ...]; outcome_fields: tuple[str, ...]
    snapshot_id: str; snapshot_schema_version: str; contract_version: str; content_digest: str; captured_at: str
    payload_digest: str; source_field_present: bool; source_kind: str; canonical_nested_binding: bool

@dataclass(frozen=True)
class GateEvaluationInput:
    gate: GateInputState
    declarations: DeclarationInputState
    participation: ParticipationInputState
    source: SourceInputState

@dataclass(frozen=True)
class CompetitionInput:
    decision: DecisionInputState
    source: SourceInputState

@dataclass(frozen=True)
class RootInput:
    root_timing: RootTimingInputState
    source: SourceInputState

@dataclass(frozen=True)
class TimingInput:
    root_timing: RootTimingInputState
    source: SourceInputState

@dataclass(frozen=True)
class ContractVersionRef:
    normative_contract_path: str
    machine_appendix_path: str
    contract_version: str
    content_digest: str

@dataclass(frozen=True)
class PackageConsumptionCheck:
    package_id: str
    pi210_integrity: IntegrityState
    contract_integrity: ContractIntegrityResult
    candidate_reference_integrity: Literal["VALID", "INVALID"]
    evidence_reference_integrity: Literal["VALID", "INVALID"]
    relation_reference_integrity: Literal["VALID", "INVALID"]
    consumable: bool
    blocking_issue_ids: tuple[str, ...]

@dataclass(frozen=True)
class GateEvaluationBindingRef:
    binding_id: str
    binding_schema_version: str
    binding_version: str
    canonical_record_digest: DigestRef
    immutable_source_digest: DigestRef

@dataclass(frozen=True)
class GateDeclaredMember:
    declared_member_id: str
    declared_member_value: object  # non-null; F09 literals are RESOURCE/OBJECT/ALLOCATION/RISK/ATTRIBUTION/TENSE
    gate_definition_ref: FrozenCardFieldRef

@dataclass(frozen=True)
class GateMemberDeclarationSet:
    declaration_set_id: str
    declaration_source_id: str
    declaration_schema_version: str
    declaration_version: str
    content_digest: DigestRef
    members: tuple[GateDeclaredMember, ...]  # nonempty

@dataclass(frozen=True)
class GateEvaluationRecord:
    gate_record_id: str
    candidate_id: str
    gate_definition_ref: FrozenCardFieldRef
    declared_member_id: str
    evaluation_binding_ref: GateEvaluationBindingRef
    state: GateEvidenceState
    supporting_evidence_ids: tuple[str, ...]
    counterevidence_ids: tuple[str, ...]
    conflict_relation_ids: tuple[str, ...]
    missing_paths: tuple[FieldPathIssueRef, ...]
    conflict_paths: tuple[FieldPathIssueRef, ...]
    unknown_paths: tuple[FieldPathIssueRef, ...]
    reason_codes: tuple[str, ...]
    source_decision_ref: str | None

@dataclass(frozen=True)
class GateEvaluationSet:
    candidate_id: str
    function_id: FunctionId
    gate_definition_refs: tuple[FrozenCardFieldRef, ...]  # nonempty
    member_declaration_set: GateMemberDeclarationSet
    records: tuple[GateEvaluationRecord, ...]  # nonempty and bijective with members
    set_state: StructuralReadinessState
    issue_ids: tuple[str, ...]

@dataclass(frozen=True)
class ParticipationRoleRecord:
    participation_record_id: str
    participation_set_id: str
    role: ParticipationRole
    frozen_definition_refs: tuple[FrozenCardFieldRef, ...]  # nonempty
    state: ParticipationState
    supporting_evidence_ids: tuple[str, ...]
    counterevidence_ids: tuple[str, ...]
    missing_issue_ids: tuple[str, ...]
    conflict_issue_ids: tuple[str, ...]
    unknown_issue_ids: tuple[str, ...]
    relation_ids: tuple[str, ...]
    source_decision_ref: str | None

@dataclass(frozen=True)
class MinimumSufficientParticipationSet:
    participation_set_id: str
    candidate_id: str
    function_id: FunctionId
    required_roles: tuple[ParticipationRole, ...]  # nonempty
    role_records: tuple[ParticipationRoleRecord, ...]  # nonempty, one per required role
    structural_state: StructuralReadinessState
    issue_ids: tuple[str, ...]

CompetitionDimension: TypeAlias = Literal["primary_responsibility", "primary_action", "direct_object", "primary_deliverable", "primary_uncertainty", "stable_input", "strongest_competing_explanation"]
CompetitionDimensionState: TypeAlias = Literal["UNOBSERVED", "PARTIAL", "READY_FOR_DECISION", "DISPUTED"]
@dataclass(frozen=True)
class CompetitionDimensionEvaluation:
    dimension: CompetitionDimension
    candidate_evidence: Mapping[str, tuple[str, ...]]
    candidate_counterevidence: Mapping[str, tuple[str, ...]]
    comparison_relation_ids: tuple[str, ...]
    state: CompetitionDimensionState
    missing_paths: tuple[FieldPathIssueRef, ...]
    conflict_paths: tuple[FieldPathIssueRef, ...]
    unknown_paths: tuple[FieldPathIssueRef, ...]

@dataclass(frozen=True)
class CounterevidenceReference:
    reference_id: str
    candidate_id: str
    evidence_id: str
    relation_ids: tuple[str, ...]
    affected_gate_record_ids: tuple[str, ...]
    affected_dimension_records: tuple[str, ...]
    source_track: EvidenceTrack
    source_locator: str

@dataclass(frozen=True)
class CandidateDisposition:
    candidate_id: str
    disposition: Literal["INCLUDED", "CONDITIONAL", "EXCLUDED", "UNRESOLVED"]
    source_decision_ref: str
    supporting_record_ids: tuple[str, ...]
    limiting_record_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]

@dataclass(frozen=True)
class CompetitionSet:
    competition_id: str
    candidate_ids: tuple[str, ...]
    relation_ids: tuple[str, ...]
    dimension_records: tuple[CompetitionDimensionEvaluation, ...]
    counterevidence_records: tuple[CounterevidenceReference, ...]
    candidate_dispositions: tuple[CandidateDisposition, ...]
    structural_state: StructuralReadinessState
    issue_ids: tuple[str, ...]

@dataclass(frozen=True)
class RootLedgerEntry:
    root_evidence_id: str
    vocabulary_scope: Literal["COMMON", "CARD_SPECIFIC"]
    label: str  # STRONG_ROOT/WEAK_ROOT/NO_ROOT or frozen card-specific literal
    card_id: FunctionId | None
    object_refs: tuple[str, ...]
    rationale_source_refs: tuple[str, ...]
    source_track: Literal["CHART_STRUCTURE"]

@dataclass(frozen=True)
class RootConstraintLedger:
    candidate_id: str
    root_entries: tuple[RootLedgerEntry, ...]
    issue_ids: tuple[str, ...]

@dataclass(frozen=True)
class TimingLedgerEntry:
    timing_evidence_id: str
    completion_mode: Literal["ACTIVATE_EXISTING", "COMPLETE_LATENT", "REPAIR_DEFECT", "TEMPORARY_SUBSTITUTE", "INVALID_COMPLETION"]
    target_root_evidence_id: str | None
    timing_object_refs: tuple[str, ...]
    source_track: Literal["CHART_STRUCTURE"]

@dataclass(frozen=True)
class TimingConstraintLedger:
    candidate_id: str
    timing_entries: tuple[TimingLedgerEntry, ...]
    issue_ids: tuple[str, ...]

@dataclass(frozen=True)
class RootTimingConstraintCheck:
    check_id: str
    constraint_ref: FrozenConstraintRef
    root_entry_ids: tuple[str, ...]
    timing_entry_ids: tuple[str, ...]
    state: ConstraintCheckState
    source_decision_ref: str | None
    missing_paths: tuple[FieldPathIssueRef, ...]
    conflict_paths: tuple[FieldPathIssueRef, ...]
    unknown_paths: tuple[FieldPathIssueRef, ...]
    reason_codes: tuple[str, ...]

@dataclass(frozen=True)
class RootTimingConstraintSet:
    candidate_id: str
    checks: tuple[RootTimingConstraintCheck, ...]
    structural_state: StructuralReadinessState
    issue_ids: tuple[str, ...]

@dataclass(frozen=True)
class FieldPathIssue:
    issue_id: str
    issue_class: Literal["MISSING", "CONFLICT", "UNKNOWN"]
    severity: Literal["INFO", "BLOCKING"]
    owner_type: Literal["PACKAGE", "CANDIDATE", "GATE", "COMPETITION_DIMENSION", "ROOT_ENTRY", "TIMING_ENTRY", "ROOT_TIMING_CHECK", "ACTION"]
    owner_id: str
    source_object_type: str
    source_object_id: str
    path_dialect: Literal["JSON_POINTER"]
    field_path: str
    source_state: SourceFieldState
    evaluator_state: FieldEvaluatorState
    evidence_ids: tuple[str, ...]
    relation_ids: tuple[str, ...]
    frozen_field_refs: tuple[FrozenCardFieldRef, ...]
    reason_codes: tuple[str, ...]

@dataclass(frozen=True)
class OutputPayload:
    included_candidate_ids: tuple[str, ...]
    disposition_refs: tuple[str, ...]
    scope_refs: tuple[str, ...]
@dataclass(frozen=True)
class ConditionalPayload:
    included_candidate_ids: tuple[str, ...]
    disposition_refs: tuple[str, ...]
    condition_refs: tuple[str, ...]
    unresolved_issue_ids: tuple[str, ...]
    scope_refs: tuple[str, ...]
@dataclass(frozen=True)
class QuestionRequest:
    question_id: str
    target_issue_ids: tuple[str, ...]
    requested_field_paths: tuple[str, ...]
    expected_answer_shape: str
@dataclass(frozen=True)
class AskPayload:
    question_requests: tuple[QuestionRequest, ...]
    unresolved_issue_ids: tuple[str, ...]
    resume_token: str
@dataclass(frozen=True)
class AbstainPayload:
    abstained_candidate_ids: tuple[str, ...]
    blocking_issue_ids: tuple[str, ...]
    abstention_scope: str
@dataclass(frozen=True)
class HumanReviewPayload:
    review_case_id: str
    review_issue_ids: tuple[str, ...]
    review_record_ids: tuple[str, ...]
    requested_review_scope: str
DecisionPayload: TypeAlias = Union[OutputPayload, ConditionalPayload, AskPayload, AbstainPayload, HumanReviewPayload]

@dataclass(frozen=True)
class DecisionActionEnvelope:
    action_id: str
    selected_action: DecisionAction
    subject_candidate_ids: tuple[str, ...]
    payload: DecisionPayload  # exactly one instance; runtime class must match selected_action
    basis_record_ids: BasisRecordIds
    blocking_issue_ids: tuple[str, ...]
    nonblocking_issue_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    source_decision_refs: tuple[str, ...]
    output_precision_binding: FrozenDeclarationBinding
    validation_plan_binding: FrozenDeclarationBinding
    structural_validity: Literal["VALID", "INVALID"]
    validation_errors: tuple[str, ...]

@dataclass(frozen=True)
class DecisionEvaluationResult:
    result_id: str
    request_id: str
    package_id: str
    contract_ref: ContractVersionRef
    consumption_check: PackageConsumptionCheck
    gate_sets: tuple[GateEvaluationSet, ...]
    participation_sets: tuple[MinimumSufficientParticipationSet, ...]
    competition_sets: tuple[CompetitionSet, ...]
    root_ledgers: tuple[RootConstraintLedger, ...]
    timing_ledgers: tuple[TimingConstraintLedger, ...]
    root_timing_checks: tuple[RootTimingConstraintSet, ...]
    issues: tuple[FieldPathIssue, ...]
    action_envelope: DecisionActionEnvelope
    produced_at: str

def evaluate_f09(package: NormalizedEvidencePackage, *, request_id: str, contract_ref: ContractVersionRef, gate_inputs: tuple[GateEvaluationInput, ...], competition_input: CompetitionInput, root_input: RootInput, timing_input: TimingInput, produced_at: str) -> DecisionEvaluationResult
def validate_decision_result(result: DecisionEvaluationResult) -> None
```
`GateInputState`、`DeclarationInputState`、`DecisionInputState`、`ParticipationInputState`、`RootTimingInputState`、`SourceInputState` 以及四个 wrapper input 是 Task 5 的 canonical frozen evaluator-input graph；Task 9 和 Task 10 必须直接 import/reuse，禁止同名 test declarations、factory methods 或未展示 adapter helpers。`FrozenCardFieldRef` 的完整字段固定为 `card_id, contract_id, contract_version, field_path, declared_state, declared_value, source_locator_id`；`FrozenConstraintRef` 必须是冻结约束端口返回的不可变精确引用，不能用路径字符串替代。动作联合只有 `payload` 一个字段，不允许五个 nullable payload 字段。`OUTPUT/CONDITIONAL/ASK/ABSTAIN/HUMAN_REVIEW` 分别且仅分别接受 `OutputPayload/ConditionalPayload/AskPayload/AbstainPayload/HumanReviewPayload`；所有 branch signatures、basis、issues、reason/source refs、两个 declaration bindings 与结构错误均已在上方落字，禁止“参见 PI-220”式补全。
- Gate member ID derives from member name + declaration version + declaration digest, never array position.
- Record digest covers member identity/state/evidence/path/reason/source decisions; validation recomputes it.

- [ ] **Step 1: Write RED contract tests.** Cover the exact frozen evaluator-input graph and direct wrapper constructors first; then cover exact six-member cardinality, declaration-record bijection, unknown/duplicate/omitted members, shared-ref consistency, digest drift, state/evidence permutation attack, record-order invariance and registered reason codes. Assert no `from_frozen_fixture` or equivalent factory exists.
- [ ] **Step 2: Add five-action RED tests.** One test per payload plus mismatch/multiple payload/basis-empty; ASK must preserve question→issue→path→resume token; HUMAN_REVIEW preserves both conflict sides and review scope.
- [ ] **Step 3: Add competition/root/timing RED tests.** F08 appears only in evidence/relation/issue/source locator; F08 candidate is rejected. Root accepts only chart evidence and timing cannot mutate root.
- [ ] **Step 4: Verify RED.** `python -m pytest tests/f09/test_decision_contract.py -q`; expected missing-module FAIL.
- [ ] **Step 5: Implement minimal evaluator and validator.** Validate structure before selecting action; on ambiguity create blocking issue and safe action, never priority-fallback. Preserve all source records even when action is ABSTAIN/HUMAN_REVIEW.
- [ ] **Step 6: Verify GREEN.** Repeat Step 4; expected PASS.
- [ ] **Step 7: Regression.** `python -m pytest tests/decision/test_staged_arbitration.py::test_old_and_staged_l6_can_run_side_by_side tests/application/test_staged_parallel_runner.py -q`; expected PASS.
- [ ] **Step 8: Commit.** `git add engine/f09/decision.py tests/f09/test_decision_contract.py tests/f09/conftest.py && git commit -m "feat(f09): evaluate six-member five-action decision"`.
- [ ] **Independent review gate.** Reviewer first confirms the six input-state declarations and four wrapper declarations are complete, frozen, uniquely owned by Task 5, and directly constructible without factory/helper invention; then attempts a member-content swap with recomputed array order but stale binding, an F08 forged candidate, and an unknown reason code; all must fail closed.
- [ ] **Rollback.** `git revert --no-edit HEAD` newest-first; no persisted decision is overwritten—published data would require a new revision.

## Task 6: PI-230 Trace and Statement Projection

**Files:**
- Create: `engine/f09/trace.py`
- Create: `tests/f09/test_trace_contract.py`

**Interfaces:** 以下是完整 PI-230 引用图。所有 track 字段直接使用 Task 1 对 PI-210 五值 `RunTrack` 的唯一 runtime transcription，字段和值均不得变化；不存在本地 `Track` alias。摘要必须通过判别联合出现，不能再把 `DigestRef` 直接塞进 `VersionedObjectRef`。本模块不得拥有 PI-210 转换类型；必须逐字使用以下唯一具体 import，禁止相对 import、别名 import 或 fallback declaration：
```python
from engine.f09.contracts import DetectedIssue, FieldMapping, ObjectRef, TransformationRecord

@dataclass(frozen=True)
class DigestPresent:
    status: Literal["PRESENT"]
    digest: DigestRef
@dataclass(frozen=True)
class DigestMissing:
    status: Literal["MISSING"]
    digest: None
    issue_id: str
DigestBinding: TypeAlias = Union[DigestPresent, DigestMissing]

@dataclass(frozen=True)
class VersionedObjectRef:
    object_type: str
    object_id: str
    revision_id: str | None
    schema_version: str
    contract_version: str | None
    digest_binding: DigestBinding
    source_locator_id: str | None
    captured_at: str | None

@dataclass(frozen=True)
class SnapshotRef:
    source_snapshot_id: str
    source_type: Literal["INPUT", "CONTRACT", "MACHINE_APPENDIX", "FINDING", "DECISION", "REPORT_CONTEXT", "ARTIFACT", "FEEDBACK"]
    source_locator_ids: tuple[str, ...]  # nonempty
    schema_version: str | None
    contract_version: str | None
    content_digest: DigestRef
    captured_at: str
    immutability: Literal["IMMUTABLE", "MUTABLE_SOURCE_CAPTURE"]

@dataclass(frozen=True)
class DecisionTraceRef:
    result_ref: VersionedObjectRef
    action_id: str
    selected_action: DecisionAction
    basis_record_ids: BasisRecordIds
    blocking_issue_ids: tuple[str, ...]
    nonblocking_issue_ids: tuple[str, ...]
    source_decision_refs: tuple[str, ...]
    output_precision_binding: FrozenDeclarationBinding
    validation_plan_binding: FrozenDeclarationBinding
    structural_validity: Literal["VALID", "INVALID"]

@dataclass(frozen=True)
class TraceNode:
    object_ref: VersionedObjectRef
    object_role: Literal["SOURCE", "NORMALIZED_EVIDENCE", "DECISION_INPUT", "DECISION_OUTPUT", "STANDARD_STATEMENT", "ARTIFACT", "FEEDBACK", "LEARNING_ELIGIBILITY"]
    track: RunTrack
    integrity: Literal["VALID", "INVALID", "UNRESOLVED"]

@dataclass(frozen=True)
class TraceEdge:
    edge_id: str
    edge_type: Literal["LOCATED_AT", "SNAPSHOT_OF", "NORMALIZED_FROM", "DERIVED_FROM", "EVALUATED_BY", "BASIS_FOR", "RENDERED_AS", "PROJECTED_TO", "ANCHORED_TO", "FEEDBACK_TARGETS", "VALIDATED_AGAINST", "ELIGIBLE_FOR", "SUPERSEDES"]
    from_ref: VersionedObjectRef
    to_ref: VersionedObjectRef
    transformation_id: str | None
    fidelity: Literal["LOSSLESS", "PARTIAL", "LOSSY", "UNSUPPORTED"]
    track_crossing: Literal["NONE", "AUDIT_ONLY"]
    issue_ids: tuple[str, ...]

@dataclass(frozen=True)
class TraceEnvelope:
    trace_id: str
    trace_schema_version: str
    case_id: str
    track: RunTrack
    source_snapshot_refs: tuple[SnapshotRef, ...]  # nonempty
    normalized_package_ref: VersionedObjectRef
    decision_result_ref: VersionedObjectRef
    statement_set_ref: VersionedObjectRef | None
    nodes: tuple[TraceNode, ...]  # nonempty
    edges: tuple[TraceEdge, ...]
    transformations: tuple[TransformationRecord, ...]
    artifacts: tuple[ArtifactRecord, ...]
    feedback_bindings: tuple[FeedbackBinding, ...]
    integrity: Literal["VALID", "INVALID", "UNRESOLVED"]
    blocking_issue_ids: tuple[str, ...]
    created_at: str

@dataclass(frozen=True)
class CardIdentityRef:
    card_identity_ref_id: str
    card_id: FunctionId
    normative_contract_ref: VersionedObjectRef
    machine_appendix_ref: VersionedObjectRef
    field_path: str
    source_field_state: SourceFieldState
    evaluator_state: FieldEvaluatorState
    declaration_status: Literal["FROZEN_DECLARATION"]
    runtime_capability_status: Literal["REFERENCE_ONLY_NOT_IMPLEMENTATION_PROOF"]
    source_locator_ids: tuple[str, ...]  # nonempty
    issue_ids: tuple[str, ...]
@dataclass(frozen=True)
class StandardStatement:
    statement_id: str
    statement_revision_id: str
    statement_schema_version: str
    case_id: str
    statement_set_id: str
    track: RunTrack
    semantic_scope: str
    domain: str
    statement_text: str
    display_section: str | None
    decision_result_id: str
    action_id: str
    basis_record_ids: BasisRecordIds
    evidence_refs: tuple[VersionedObjectRef, ...]
    relation_ids: tuple[str, ...]
    source_locator_ids: tuple[str, ...]
    card_identity_refs: tuple[CardIdentityRef, ...]
    confidence_snapshot_ref: VersionedObjectRef | None
    output_precision_binding: FrozenDeclarationBinding
    validation_plan_binding: FrozenDeclarationBinding
    feedback_policy: Literal["FEEDBACK_ALLOWED", "HUMAN_REVIEW_ONLY", "NOT_FEEDBACK_TARGET"]
    content_digest: DigestRef
    integrity: Literal["VALID", "INVALID", "UNRESOLVED"]
    issue_ids: tuple[str, ...]
@dataclass(frozen=True)
class StatementSet:
    statement_set_id: str
    statement_schema_version: str
    case_id: str
    track: RunTrack
    source_package_ref: VersionedObjectRef
    decision_trace_ref: DecisionTraceRef
    statements: tuple[StandardStatement, ...]
    content_digest: DigestRef
    generated_at: str
    publication_state: Literal["DRAFT", "PUBLISHABLE", "BLOCKED", "SUPERSEDED"]
    issue_ids: tuple[str, ...]
@dataclass(frozen=True)
class ProjectionValidationResult:
    valid: bool
    detected_issues: tuple[DetectedIssue, ...]
def build_trace(package: NormalizedEvidencePackage, result: DecisionEvaluationResult, *, created_at: str) -> TraceEnvelope
def build_statement_set(trace: TraceEnvelope, result: DecisionEvaluationResult, *, generated_at: str) -> StatementSet
def validate_statement_projection(statement_set: StatementSet, trace: TraceEnvelope, result: DecisionEvaluationResult) -> ProjectionValidationResult
```
`TraceEnvelope.artifacts` 和 `TraceEnvelope.feedback_bindings` 使用 Task 7/8 已逐字段内联的 PI-230 类型；forward reference 只解决声明顺序，不允许省字段。`source_snapshot_refs` 与 `nodes` 非空；每个 copied source、唯一 PI-210 `TransformationRecord`、action basis、statement、artifact 与 feedback target 必须经 `VersionedObjectRef`/edge 可达。`ObjectRef` 以相同 `object_type + object_id` 唯一对应 trace node 的 `VersionedObjectRef`；无法唯一对应时 trace 为 `UNRESOLVED`。三个 PI-210 conversion-ledger 类型与 `DetectedIssue` 只允许由 Task 1 在 `engine/f09/contracts.py` 定义一次；`trace.py`、fixtures 与所有 consumers 只能具体 import/reuse。`TraceEnvelope.transformations` 必须保持 `tuple[TransformationRecord, ...]` 并因此引用同一 canonical runtime identity。`trace.py` 还必须具体导入 `F09ContractError`、`F09IntegrityError` 与 `F09SourceError` from `engine.f09.errors`; no local/fallback error declaration is allowed. `validate_statement_projection()` must return `ProjectionValidationResult(valid=False, detected_issues=(...))` when PI-300 permits preservation of an invalid projection as a typed result; every detection branch constructs each `DetectedIssue(issue_code, field_path)` together at that branch. A rejection that cannot return a coherent result raises the appropriate Task 1 `F09Error` subtype with the same two typed fields. It must never return `valid=False` with an empty tuple, and it must never derive a path from `StatementSet.issue_ids` or `TraceEnvelope.blocking_issue_ids`.

**R15 literal Task 6 producer source — copy continuously into `trace.py`; no predicate or prerequisite is supplied by prose or a test adapter.** The eight source predicates are the eight local booleans named `t93`, `t95`, `t96`, `t97`, `t98`, `t99`, `t100`, and `t101`. They consume only the displayed canonical graph. Required set/statement/result shapes are handled before every nullable or shape-sensitive dereference. A coherent invalid projection returns one branch-local pair; a malformed object that cannot form that return raises the exact branch-local constructor shown below. In particular, the canonical PI-220 field is `result.action_envelope`, never `result.action`.

```python
def validate_statement_projection(
    statement_set: StatementSet,
    trace: TraceEnvelope,
    result: DecisionEvaluationResult,
) -> ProjectionValidationResult:
    if not isinstance(statement_set, StatementSet):
        raise F09ContractError(
            issue_code="STATEMENT.SET_INVALID",
            field_path="/statement_set",
            diagnostic="statement projection requires a StatementSet",
        )
    if (
        not statement_set.statement_set_id
        or not statement_set.statement_schema_version
        or not statement_set.case_id
        or statement_set.source_package_ref is None
        or statement_set.decision_trace_ref is None
        or not statement_set.generated_at
        or not statement_set.content_digest
    ):
        return ProjectionValidationResult(
            valid=False,
            detected_issues=(DetectedIssue(
                issue_code="STATEMENT.SET_INVALID",
                field_path="/statement_set",
            ),),
        )  # T44
    if not isinstance(statement_set.decision_trace_ref, DecisionTraceRef):
        raise F09ContractError(
            issue_code="STATEMENT.SET_INVALID",
            field_path="/statement_set",
            diagnostic="statement set decision_trace_ref has invalid shape",
        )
    if not statement_set.statements:
        return ProjectionValidationResult(
            valid=False,
            detected_issues=(DetectedIssue(
                issue_code="STATEMENT.RECORD_INVALID",
                field_path="/statements/0",
            ),),
        )  # T45
    statement = statement_set.statements[0]
    if not isinstance(statement, StandardStatement):
        raise F09ContractError(
            issue_code="STATEMENT.RECORD_INVALID",
            field_path="/statements/0",
            diagnostic="first statement has invalid shape",
        )
    if (
        not statement.statement_id
        or not statement.statement_revision_id
        or not statement.statement_schema_version
        or not statement.semantic_scope
        or not statement.domain
        or not statement.statement_text
        or not statement.basis_record_ids
    ):
        return ProjectionValidationResult(
            valid=False,
            detected_issues=(DetectedIssue(
                issue_code="STATEMENT.RECORD_INVALID",
                field_path="/statements/0",
            ),),
        )  # T45
    if not isinstance(result, DecisionEvaluationResult):
        raise F09ContractError(
            issue_code="TRACE.BINDING_MISMATCH",
            field_path="/trace/declarations",
            diagnostic="projection result has invalid shape",
        )
    action_envelope = result.action_envelope
    if not isinstance(action_envelope, DecisionActionEnvelope):
        raise F09ContractError(
            issue_code="TRACE.BINDING_MISMATCH",
            field_path="/trace/declarations",
            diagnostic="decision action_envelope has invalid shape",
        )
    if not isinstance(trace, TraceEnvelope):
        raise F09SourceError(
            issue_code="SOURCE.LOCATOR_MISMATCH",
            field_path="/source_locators",
            diagnostic="projection trace has invalid shape",
        )
    if not isinstance(trace.transformations, tuple) or not isinstance(trace.nodes, tuple) or not isinstance(trace.edges, tuple) or not isinstance(trace.source_snapshot_refs, tuple):
        raise F09SourceError(
            issue_code="SOURCE.POINTER_UNRESOLVED",
            field_path="/transformations/LOSSLESS_COPY",
            diagnostic="trace traversal collections have invalid shape",
        )
    if any(not isinstance(item, TransformationRecord) for item in trace.transformations):
        raise F09IntegrityError(
            issue_code="TRANSFORMATION.UNSUPPORTED",
            field_path="/transformations/0",
            diagnostic="trace contains a noncanonical transformation record",
        )
    if any(not isinstance(node, TraceNode) for node in trace.nodes) or any(not isinstance(edge, TraceEdge) for edge in trace.edges):
        raise F09SourceError(
            issue_code="TRACE.EDGE_MISSING",
            field_path="/transformations/mappings",
            diagnostic="trace node or edge has invalid shape",
        )
    if any(not isinstance(snapshot, SnapshotRef) for snapshot in trace.source_snapshot_refs):
        raise F09SourceError(
            issue_code="SOURCE.IDENTITY_MISMATCH",
            field_path="/source_locators/binding",
            diagnostic="trace source snapshot has invalid shape",
        )

    lossless = tuple(item for item in trace.transformations if item.fidelity == "LOSSLESS")
    node_refs = tuple(node.object_ref for node in trace.nodes)
    node_keys = tuple((ref.object_type, ref.object_id) for ref in node_refs)
    source_locator_ids = tuple(
        ref.source_locator_id
        for item in lossless
        for ref in item.source_object_refs
        if ref.source_locator_id is not None
    )
    snapshot_locator_ids = tuple(
        locator_id
        for snapshot in trace.source_snapshot_refs
        for locator_id in snapshot.source_locator_ids
    )
    lossless_mappings = tuple(mapping for item in lossless for mapping in item.field_mappings)
    mapped_source_paths = tuple(mapping.source_field_path for mapping in lossless_mappings)
    mapped_target_paths = tuple(mapping.target_field_path for mapping in lossless_mappings)
    lossless_ids = tuple(item.transformation_id for item in lossless)
    terminal_ids = tuple(edge.transformation_id for edge in trace.edges if edge.transformation_id is not None)

    state_target_paths = (
        "/payload/value/level",
        "/payload/value/position",
        "/temporal_scope/as_of/value",
    )
    event_target_paths = (
        "/payload/value/level",
        "/payload/value/change",
        "/temporal_scope/interval/start/value",
        "/temporal_scope/interval/end/value",
        "/temporal_scope/interval/start_inclusive",
        "/temporal_scope/interval/end_inclusive",
    )
    outcome_target_paths = (
        "/payload/value/axis",
        "/payload/value/action",
        "/payload/value/object",
        "/payload/value/tense",
    )
    state_transformations = tuple(
        item
        for item in lossless
        if tuple(mapping.target_field_path for mapping in item.field_mappings)
        == state_target_paths
    )
    event_transformations = tuple(
        item
        for item in lossless
        if tuple(mapping.target_field_path for mapping in item.field_mappings)
        == event_target_paths
    )
    state_source_refs = tuple(
        ref for item in state_transformations for ref in item.source_object_refs
    )
    event_source_refs = tuple(
        ref for item in event_transformations for ref in item.source_object_refs
    )
    t93 = (
        len(state_transformations) != 1
        or len(event_transformations) != 1
        or len(state_source_refs) != 1
        or len(event_source_refs) != 1
        or state_source_refs[0].object_id != "SOURCE-STATE-1"
        or event_source_refs[0].object_id != "SOURCE-EVENT-1"
        or tuple(mapping.source_field_path for mapping in state_transformations[0].field_mappings)
        != ("/value/level", "/value/position", "/value/as_of")
        or tuple(mapping.source_field_path for mapping in event_transformations[0].field_mappings)
        != (
            "/value/level",
            "/value/change",
            "/value/interval/start",
            "/value/interval/end",
            "/value/interval/start_inclusive",
            "/value/interval/end_inclusive",
        )
    )
    t95 = any(
        not item.source_object_refs
        or any((ref.object_type, ref.object_id) not in node_keys for ref in item.source_object_refs)
        or any(not mapping.source_field_path.startswith("/") for mapping in item.field_mappings)
        for item in lossless
    )
    f09_source_snapshots = tuple(
        snapshot
        for snapshot in trace.source_snapshot_refs
        if "SRCLOC-STATE-LEVEL" in snapshot.source_locator_ids
        or "SRCLOC-EVENT-LEVEL" in snapshot.source_locator_ids
    )
    t96 = (
        len(f09_source_snapshots) != 1
        or f09_source_snapshots[0].source_snapshot_id
        != "PI-300-F09-SOURCE-SNAPSHOT-V1"
        or f09_source_snapshots[0].schema_version
        != "reality-fact-source-snapshot.v1"
        or f09_source_snapshots[0].contract_version
        != "pi-300-f09-source-snapshots-v1"
        or f09_source_snapshots[0].captured_at != "2026-07-19T00:00:00Z"
        or f09_source_snapshots[0].content_digest.algorithm != "sha256"
        or f09_source_snapshots[0].content_digest.canonicalization
        != "RFC8785-JCS-UTF8"
        or f09_source_snapshots[0].content_digest.value
        != "67517fe2d04fb0fe580e031643dab2ad53fcdb8c90707ba4d496c316dd87f5e7"
    ) or any(
        snapshot.content_digest.algorithm != "sha256"
        or snapshot.content_digest.canonicalization != "RFC8785-JCS-UTF8"
        or not snapshot.source_snapshot_id
        or not snapshot.schema_version
        or not snapshot.contract_version
        or not snapshot.captured_at
        for snapshot in trace.source_snapshot_refs
    ) or any(
        not isinstance(ref.digest_binding, DigestPresent)
        or not any(
            ref.source_locator_id in snapshot.source_locator_ids
            and ref.digest_binding.digest == snapshot.content_digest
            for snapshot in trace.source_snapshot_refs
        )
        for ref in node_refs
        if ref.source_locator_id is not None
    )
    t97 = any(not item.field_mappings for item in lossless) or any(transformation_id not in terminal_ids for transformation_id in lossless_ids)
    t98 = any(path not in mapped_target_paths for path in outcome_target_paths)
    t99 = any(
        item.fidelity == "LOSSLESS"
        and any(ref.object_type not in ("SOURCE_OBJECT", "EVIDENCE", "CARD_FIELD") for ref in item.source_object_refs)
        for item in trace.transformations
    )
    t100 = any(
        ref.source_locator_id is None
        or ref.source_locator_id not in snapshot_locator_ids
        for item in lossless
        for ref in item.source_object_refs
    )
    legal_copy_fields_intact = all(
        path in mapped_target_paths
        for path in (
            "/payload/value/axis",
            "/payload/value/action",
            "/payload/value/object",
            "/payload/value/tense",
        )
    )
    t101 = (
        action_envelope.selected_action is DecisionAction.OUTPUT
        and legal_copy_fields_intact
        and any(
            forbidden in statement.statement_text.lower()
            for forbidden in (
                "tool", "amount", "wealth outcome",
                "工具", "金额", "财富结果",
            )
        )
    )

    if statement.output_precision_binding != statement_set.decision_trace_ref.output_precision_binding:
        return ProjectionValidationResult(valid=False, detected_issues=(DetectedIssue(issue_code="TRACE.BINDING_MISMATCH", field_path="/statements/0/output_precision_binding"),))  # T19
    if len(statement.evidence_refs) > 1 and any(item.fidelity == "LOSSY" for item in trace.transformations):
        return ProjectionValidationResult(valid=False, detected_issues=(DetectedIssue(issue_code="PROJECTION.LOSSY", field_path="/transformations/records"),))  # T20
    if any(card_ref.runtime_capability_status != "REFERENCE_ONLY_NOT_IMPLEMENTATION_PROOF" for card_ref in statement.card_identity_refs):
        return ProjectionValidationResult(valid=False, detected_issues=(DetectedIssue(issue_code="CARD.IDENTITY_INVALID", field_path="/card_identity_refs/0/runtime_capability_status"),))  # T30
    if statement_set.decision_trace_ref.output_precision_binding != action_envelope.output_precision_binding or statement_set.decision_trace_ref.validation_plan_binding != action_envelope.validation_plan_binding:
        return ProjectionValidationResult(valid=False, detected_issues=(DetectedIssue(issue_code="TRACE.BINDING_MISMATCH", field_path="/trace/declarations"),))  # T37
    if statement.basis_record_ids != action_envelope.basis_record_ids:
        return ProjectionValidationResult(valid=False, detected_issues=(DetectedIssue(issue_code="TRACE.BASIS_MISMATCH", field_path="/statements/0/basis_record_ids"),))  # T89
    if t95:
        return ProjectionValidationResult(valid=False, detected_issues=(DetectedIssue(issue_code="SOURCE.POINTER_UNRESOLVED", field_path="/transformations/LOSSLESS_COPY"),))  # T95
    if t100:
        return ProjectionValidationResult(valid=False, detected_issues=(DetectedIssue(issue_code="SOURCE.BINDING_INVALID", field_path="/source_locators/0"),))  # T100
    if t93:
        return ProjectionValidationResult(valid=False, detected_issues=(DetectedIssue(issue_code="SOURCE.LOCATOR_MISMATCH", field_path="/source_locators"),))  # T93
    if t96:
        return ProjectionValidationResult(valid=False, detected_issues=(DetectedIssue(issue_code="SOURCE.IDENTITY_MISMATCH", field_path="/source_locators/binding"),))  # T96
    if t97:
        return ProjectionValidationResult(valid=False, detected_issues=(DetectedIssue(issue_code="TRACE.EDGE_MISSING", field_path="/transformations/mappings"),))  # T97
    if t98:
        return ProjectionValidationResult(valid=False, detected_issues=(DetectedIssue(issue_code="SOURCE.FIELD_MISSING", field_path="/outcome"),))  # T98
    if t99:
        return ProjectionValidationResult(valid=False, detected_issues=(DetectedIssue(issue_code="TRANSFORMATION.UNSUPPORTED", field_path="/transformations/0"),))  # T99
    if t101:
        return ProjectionValidationResult(valid=False, detected_issues=(DetectedIssue(issue_code="OUTPUT.SCOPE_EXCEEDED", field_path="/statements/0/statement_text"),))  # T101
    return ProjectionValidationResult(valid=True, detected_issues=())
```

The malformed-prerequisite exits above are exhaustive for the shapes dereferenced by this source and use full literal constructors. There are no ellipses, “reuse displayed pair” instructions, future helpers, test IDs, expected values, status-to-pair mappings, or adapter-owned repairs. T19/T20/T30/T37/T44/T45/T89 and all eight T93/T95–T101 predicates therefore choose one visible return or one visible typed raise before access; they never choose both.

- [ ] **Step 1: Write RED tests.** Delete each required StatementSet/StandardStatement field, drift each six-field declaration identity, alter/reorder/drop gate or participation basis, force implemented capability status, inject unresolved action as OUTPUT prose, and assert `trace.TransformationRecord is contracts.TransformationRecord`, `trace.ObjectRef is contracts.ObjectRef`, and `trace.FieldMapping is contracts.FieldMapping`.
- [ ] **Step 2: Verify RED.** `python -m pytest tests/f09/test_trace_contract.py -q`; expected missing-module FAIL.
- [ ] **Step 3: Implement projection.** Add the one concrete import shown above and no local conversion-ledger declaration. Copy binding and ordered basis tuples exactly; do not infer precision, amounts, tools or wealth outcome. For non-output actions, statement type is audit/question/review/abstention and cannot masquerade as formal outcome.
- [ ] **Step 4: Verify GREEN.** Repeat Step 2; expected PASS.
- [ ] **Step 5: Regression.** `python -m pytest tests/test_output_linter.py tests/v1_3_acceptance/test_h1_statement_id_stable.py::test_h1_sid_stable_under_rule_id_reordering -q`; expected PASS. Existing public statement IDs remain unchanged.
- [ ] **Step 6: Commit.** `git add engine/f09/trace.py tests/f09/test_trace_contract.py && git commit -m "feat(f09): bind decision trace and statement set"`.
- [ ] **Independent review gate.** Reviewer confirms internal IDs never enter a public text field, `runtime_capability_status` is immutable reference-only, Task 6 contains zero local declarations of the three PI-210 conversion-ledger types or `DetectedIssue`, imports all four canonical Task 1 runtime identities, every `TraceEnvelope.transformations` element has canonical identity, and every invalid returned `ProjectionValidationResult` carries at least one complete producer-owned pair.
- [ ] **Rollback.** `git revert --no-edit HEAD`; published statement sets are superseded by revision, never edited in place.

## Task 7: Artifact Lifecycle, Idempotency, Retry and Rollback

**Files:**
- Create: `engine/f09/artifacts.py`
- Create: `tests/f09/test_artifact_lifecycle.py`

**Interfaces:**
```python
from engine.f09.contracts import DetectedIssue

@dataclass(frozen=True)
class IdempotencyKey: operation: Literal["NORMALIZE", "DECIDE", "BUILD_STATEMENT_SET", "RENDER_REPORT", "PROJECT_INDEX", "PROJECT_RECORDS", "BIND_FEEDBACK", "EVALUATE_LEARNING_ELIGIBILITY", "INGEST_FEEDBACK"]; case_id: str; track: RunTrack; source_digest: DigestRef; schema_versions_digest: DigestRef; contract_digest: DigestRef | None; statement_set_id: str | None; feedback_id: str | None; canonical_key_digest: DigestRef
@dataclass(frozen=True)
class ArtifactWriteAttempt:
    attempt_id: str
    artifact_id: str
    idempotency_key: str
    attempt_number: int
    retry_of_attempt_id: str | None
    input_snapshot_refs: tuple[VersionedObjectRef, ...]
    started_at: str
    finished_at: str | None
    outcome: Literal["SUCCEEDED", "FAILED", "UNKNOWN"]
    observed_digest: DigestRef | None
    error_class: str | None
    error_message_digest: DigestRef | None
@dataclass(frozen=True)
class ArtifactRecord:
    artifact_id: str
    artifact_role: Literal["REPORT", "STATEMENT_INDEX", "STATEMENT_RECORDS", "RUN_SNAPSHOT", "DECISION_RUN", "FEEDBACK_ATTACHMENT", "MANIFEST", "FEEDBACK_SOURCE"]
    track: RunTrack
    case_id: str
    statement_set_id: str | None
    run_id: str | None
    path_locator: str
    schema_version: str | None
    expected_digest: DigestRef | None
    observed_digest: DigestRef | None
    state: ArtifactItemState
    attempts: tuple[ArtifactWriteAttempt, ...]
    issue_ids: tuple[str, ...]
@dataclass(frozen=True)
class ArtifactSetManifest:
    manifest_id: str
    key: IdempotencyKey
    records: tuple[ArtifactRecord, ...]
    state: ArtifactSetState
    digest: DigestRef
    detected_issues: tuple[DetectedIssue, ...]
def write_artifact_set(root: Path, statement_set: StatementSet, projections: Mapping[str, bytes], *, key: IdempotencyKey, attempt_id: str, now: str, fail_after: str | None = None) -> ArtifactSetManifest
def inspect_artifact_set(root: Path, manifest: ArtifactSetManifest) -> ArtifactSetManifest
def retry_artifact_set(root: Path, manifest: ArtifactSetManifest, projections: Mapping[str, bytes], *, key: IdempotencyKey, current_frozen_input_refs: tuple[VersionedObjectRef, ...], current_schema_version: str, current_statement_set_id: str, current_contract_digest: DigestRef | None, attempt_id: str, now: str) -> ArtifactSetManifest
def coordinate_artifact_operation(root: Path, statement_set: StatementSet, projections: Mapping[str, bytes], *, existing_manifest: ArtifactSetManifest | None, key: IdempotencyKey, attempt_id: str, now: str) -> ArtifactSetManifest
```
Every attempt appends to `attempts`; retry identity, input snapshots, timestamps, outcome, observed digest and typed error evidence are never collapsed into one mutable error field. `artifacts.py` imports Task 1 `DetectedIssue` and specifically imports `F09ContractError`, `F09IntegrityError`, and `F09WriteError` from `engine.f09.errors`; there is no local/fallback error type. The writer/inspector/retry coordinator adds a complete typed pair to `ArtifactSetManifest.detected_issues` at the branch that detects a partial write, stale revision, digest mismatch, illegal state, or idempotency conflict. Returned negative manifests therefore carry their own producer-owned pair. `ArtifactRecord.issue_ids` remains frozen audit data and cannot be paired with an adapter-invented path. A branch that cannot coherently return a manifest raises `F09WriteError`, `F09IntegrityError`, or `F09ContractError` with typed fields. No manifest state is mechanically mapped to an issue by a caller, and legal `SUPERSEDED` remains non-issue exactly as PI-300 T72 requires.

**R19 controlling Task 7 amendment.** This amendment supersedes every contradictory R15/R18 retry/path sentence and source fragment below while preserving the displayed interfaces and producer-owned receipt/error boundaries. Implement one common `resolve_artifact_operation_root(root, key)` preflight and invoke it before any `mkdir`, target construction that may be written, or filesystem mutation in both writer and retry. The preflight accepts only a canonical digest with `algorithm="sha256"`, canonicalization `RFC8785-JCS-UTF8`, and a value matching exactly 64 lowercase hexadecimal characters. It rejects empty values, uppercase, separators, drive/UNC/absolute syntax, `.`/`..`, alternate components, and every value whose `Path(value).parts` is not the one original component. It resolves the caller root, resolves `root / value` without creating it, and proves with `candidate != resolved_root` and `candidate.is_relative_to(resolved_root)` (or the equivalent fail-closed parent comparison on supported Python); failure raises the displayed typed contract/integrity error before any write. Only the returned contained path may be used by writer/retry. Thus no raw digest value is itself a trusted path and distinct valid keys remain disjoint beneath the authorized root.

Retry validation is record-local before current-state selection. Every retained `ArtifactRecord`, including `SUPERSEDED`, must have a nonempty tuple of canonical `ArtifactWriteAttempt`s; each attempt must name that record's `artifact_id`, carry nonempty canonical input refs, have a positive contiguous attempt number, and form an internally coherent `retry_of_attempt_id` chain. Each retained record is checked against the key, refs, revision/schema and contract identity that its own attempts actually record; historical revisions, schemas, statement-set IDs, input refs, and idempotency keys are not forced to equal current values. `SUPERSEDED` records remain byte-for-byte audit-visible, are never selected as current, never rewritten/dropped, and may legally carry old identity as required by T72. After this all-history validation, retry selects zero or one non-superseded current record per required role. Only those current records must match the incoming key's case, track, statement-set ID, current schema/contract and expected payload digest. A missing current role inherits current identity only from the incoming key plus the current operation's explicitly supplied nonempty frozen input-ref tuple/current schema authority; it never guesses from the first historical attempt. Replacing a current record retains all superseded records and the replaced record's attempts, and every returned manifest digest is recomputed from the exact returned ordered records rather than copied from a stale manifest.

**R15 literal Task 7 producer source — copy continuously at the three displayed ports, as amended by the controlling R19 rules above.** Every local used by a phase-owned branch is defined here. The raw state test first accepts canonical Enum instances and otherwise compares only a raw string against the explicit eight legal values; it never invokes raw Enum containment. A coherent manifest returns one exact pair. The only non-returnable branches are the full typed constructors displayed here; no pair is delegated to prose.

```python
def resolve_artifact_operation_root(root: Path, key: IdempotencyKey) -> Path:
    if not isinstance(root, Path) or not isinstance(key, IdempotencyKey):
        raise F09ContractError("ARTIFACT.STATE_INVALID", "/canonical_key_digest", "operation-root input has invalid shape")
    digest = key.canonical_key_digest
    value = digest.value if isinstance(digest, DigestRef) else ""
    if (
        not isinstance(digest, DigestRef)
        or digest.algorithm != "sha256"
        or digest.canonicalization != "RFC8785-JCS-UTF8"
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
        or Path(value).is_absolute()
        or Path(value).drive
        or Path(value).anchor
        or Path(value).parts != (value,)
        or value in (".", "..")
    ):
        raise F09IntegrityError("IDEMPOTENCY.DIGEST_MISMATCH", "/canonical_key_digest", "operation identity is not one lowercase SHA-256 path component")
    resolved_root = root.resolve(strict=False)
    candidate = (resolved_root / value).resolve(strict=False)
    if candidate == resolved_root or not candidate.is_relative_to(resolved_root):
        raise F09IntegrityError("IDEMPOTENCY.DIGEST_MISMATCH", "/canonical_key_digest", "operation root escapes the authorized artifact root")
    return candidate


def _digest_ref_material(digest: DigestRef | None) -> object:
    return None if digest is None else {
        "algorithm": digest.algorithm,
        "canonicalization": digest.canonicalization,
        "value": digest.value,
    }


def _versioned_ref_material(ref: VersionedObjectRef) -> dict[str, object]:
    binding = ref.digest_binding
    return {
        "object_type": ref.object_type,
        "object_id": ref.object_id,
        "revision_id": ref.revision_id,
        "schema_version": ref.schema_version,
        "contract_version": ref.contract_version,
        "digest_status": binding.status,
        "digest": _digest_ref_material(binding.digest),
        "source_locator_id": ref.source_locator_id,
        "captured_at": ref.captured_at,
    }


def canonicalize_artifact_records(records: tuple[ArtifactRecord, ...]) -> bytes:
    material = []
    for record in records:
        material.append({
            "artifact_id": record.artifact_id,
            "artifact_role": record.artifact_role,
            "track": record.track.value if isinstance(record.track, Enum) else record.track,
            "case_id": record.case_id,
            "statement_set_id": record.statement_set_id,
            "run_id": record.run_id,
            "path_locator": record.path_locator,
            "schema_version": record.schema_version,
            "expected_digest": _digest_ref_material(record.expected_digest),
            "observed_digest": _digest_ref_material(record.observed_digest),
            "state": record.state.value if isinstance(record.state, Enum) else record.state,
            "attempts": [{
                "attempt_id": attempt.attempt_id,
                "artifact_id": attempt.artifact_id,
                "idempotency_key": attempt.idempotency_key,
                "attempt_number": attempt.attempt_number,
                "retry_of_attempt_id": attempt.retry_of_attempt_id,
                "input_snapshot_refs": [_versioned_ref_material(ref) for ref in attempt.input_snapshot_refs],
                "started_at": attempt.started_at,
                "finished_at": attempt.finished_at,
                "outcome": attempt.outcome,
                "observed_digest": _digest_ref_material(attempt.observed_digest),
                "error_class": attempt.error_class,
                "error_message_digest": _digest_ref_material(attempt.error_message_digest),
            } for attempt in record.attempts],
            "issue_ids": list(record.issue_ids),
        })
    return json.dumps(material, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def digest_artifact_records(records: tuple[ArtifactRecord, ...]) -> DigestRef:
    return DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(canonicalize_artifact_records(records)).hexdigest())


def write_artifact_set(
    root: Path,
    statement_set: StatementSet,
    projections: Mapping[str, bytes],
    *,
    key: IdempotencyKey,
    attempt_id: str,
    now: str,
    fail_after: str | None = None,
) -> ArtifactSetManifest:
    if not isinstance(statement_set, StatementSet) or not isinstance(key, IdempotencyKey):
        raise F09ContractError(
            issue_code="ARTIFACT.STATE_INVALID",
            field_path="/artifacts/0/state",
            diagnostic="artifact write prerequisite has invalid shape",
        )
    required_roles = ("REPORT", "STATEMENT_RECORDS", "STATEMENT_INDEX")
    if (
        not isinstance(projections, Mapping)
        or set(projections) != set(required_roles)
        or any(not isinstance(projections[role], bytes) for role in required_roles)
    ):
        raise F09ContractError(
            issue_code="ARTIFACT.STATE_INVALID",
            field_path="/artifacts/0/state",
            diagnostic="artifact projections must contain exactly the three required byte roles",
        )
    if fail_after not in (None, "STATEMENT_RECORDS", "STATEMENT_INDEX"):
        raise ValueError(
            "only STATEMENT_RECORDS and STATEMENT_INDEX are phase-owned "
            "semantic failure injection points; T21 starts after REPORT succeeds"
        )
    operation_root = resolve_artifact_operation_root(root, key)  # R19: validated one-component lowercase sha256 and resolved containment before mutation
    records: tuple[ArtifactRecord, ...] = ()
    for role in required_roles:
        payload = projections[role]
        expected_digest = DigestRef("sha256", "RAW-UTF8", sha256(payload).hexdigest())
        target = operation_root / (role.lower() + ".bin")
        artifact_id = "ARTIFACT:" + key.canonical_key_digest.value + ":" + role
        try:
            operation_root.mkdir(parents=True, exist_ok=True)
            if fail_after == role:
                raise OSError("injected canonical write-boundary failure for " + role)
            target.write_bytes(payload)
            observed_digest = DigestRef("sha256", "RAW-UTF8", sha256(target.read_bytes()).hexdigest())
        except OSError as error:
            error_digest = DigestRef(
                "sha256", "RAW-UTF8",
                sha256((type(error).__name__ + ":" + str(error)).encode("utf-8")).hexdigest(),
            )
            failed_attempt = ArtifactWriteAttempt(
                attempt_id=attempt_id + ":" + role,
                artifact_id=artifact_id,
                idempotency_key=key.canonical_key_digest.value,
                attempt_number=1,
                retry_of_attempt_id=None,
                input_snapshot_refs=(statement_set.source_package_ref,),
                started_at=now,
                finished_at=now,
                outcome="FAILED",
                observed_digest=None,
                error_class=type(error).__name__,
                error_message_digest=error_digest,
            )
            failed_record = ArtifactRecord(
                artifact_id=artifact_id,
                artifact_role=role,
                track=statement_set.track,
                case_id=statement_set.case_id,
                statement_set_id=statement_set.statement_set_id,
                run_id=None,
                path_locator=target.as_posix(),
                schema_version=statement_set.statement_schema_version,
                expected_digest=expected_digest,
                observed_digest=None,
                state=ArtifactItemState.FAILED,
                attempts=(failed_attempt,),
                issue_ids=(),
            )
            failed_records = records + (failed_record,)
            failed_manifest = ArtifactSetManifest(
                manifest_id="MANIFEST:" + key.canonical_key_digest.value,
                key=key,
                records=failed_records,
                state=(ArtifactSetState.FAILED if role == "REPORT" else ArtifactSetState.PARTIAL),
                digest=digest_artifact_records(failed_records),
                detected_issues=(
                    ()
                    if role == "REPORT"
                    else (DetectedIssue(
                        issue_code="ARTIFACT.WRITE_FAILED",
                        field_path=(
                            "/artifacts/STATEMENT_RECORDS"
                            if role == "STATEMENT_RECORDS"
                            else "/artifacts/STATEMENT_INDEX"
                        ),
                    ),)
                ),
            )
            return failed_manifest
        attempt = ArtifactWriteAttempt(
            attempt_id=attempt_id + ":" + role,
            artifact_id=artifact_id,
            idempotency_key=key.canonical_key_digest.value,
            attempt_number=1,
            retry_of_attempt_id=None,
            input_snapshot_refs=(statement_set.source_package_ref,),
            started_at=now,
            finished_at=now,
            outcome="SUCCEEDED",
            observed_digest=observed_digest,
            error_class=None,
            error_message_digest=None,
        )
        records = records + (ArtifactRecord(
            artifact_id=artifact_id,
            artifact_role=role,
            track=statement_set.track,
            case_id=statement_set.case_id,
            statement_set_id=statement_set.statement_set_id,
            run_id=None,
            path_locator=target.as_posix(),
            schema_version=statement_set.statement_schema_version,
            expected_digest=expected_digest,
            observed_digest=observed_digest,
            state=ArtifactItemState.VERIFIED,
            attempts=(attempt,),
            issue_ids=(),
        ),)
    manifest_digest = digest_artifact_records(records)
    return ArtifactSetManifest(
        manifest_id="MANIFEST:" + key.canonical_key_digest.value,
        key=key,
        records=records,
        state=ArtifactSetState.COMPLETE_VERIFIED,
        digest=manifest_digest,
        detected_issues=(),
    )

def inspect_artifact_set(root: Path, manifest: ArtifactSetManifest) -> ArtifactSetManifest:
    if not isinstance(manifest, ArtifactSetManifest) or not isinstance(manifest.records, tuple):
        raise F09ContractError(
            issue_code="ARTIFACT.STATE_INVALID",
            field_path="/artifacts/0/state",
            diagnostic="artifact manifest has invalid shape",
        )
    if any(not isinstance(record, ArtifactRecord) for record in manifest.records):
        raise F09ContractError(
            issue_code="ARTIFACT.STATE_INVALID",
            field_path="/artifacts/0/state",
            diagnostic="artifact manifest contains a noncanonical record",
        )
    legal_state_values = (
        "NOT_ATTEMPTED",
        "WRITING",
        "WRITTEN_UNVERIFIED",
        "VERIFIED",
        "FAILED",
        "STALE",
        "MISMATCH",
        "SUPERSEDED",
    )
    illegal_state = next(
        (
            record.state
            for record in manifest.records
            if not (
                isinstance(record.state, ArtifactItemState)
                or isinstance(record.state, str)
                and record.state in legal_state_values
            )
        ),
        None,
    )
    if illegal_state is not None:
        raise F09ContractError(
            issue_code="ARTIFACT.STATE_INVALID",
            field_path="/artifacts/0/state",
            diagnostic="artifact item state is outside the eight legal ArtifactItemState values",
        )  # T68, T69
    statement_records = tuple(record for record in manifest.records if record.artifact_role == "STATEMENT_RECORDS")
    statement_indexes = tuple(record for record in manifest.records if record.artifact_role == "STATEMENT_INDEX")
    current_revisions = tuple(record.statement_set_id for record in statement_records if record.state not in (ArtifactItemState.SUPERSEDED, "SUPERSEDED") and record.statement_set_id is not None)
    index_revisions = tuple(record.statement_set_id for record in statement_indexes if record.statement_set_id is not None)
    stale_index = bool(current_revisions and index_revisions and any(revision not in current_revisions for revision in index_revisions))
    set_digest_mismatch = any(
        record.expected_digest is not None
        and record.observed_digest is not None
        and record.expected_digest != record.observed_digest
        for record in manifest.records
    )
    if stale_index:
        return replace(manifest, state=ArtifactSetState.STALE_MIXED_REVISION, detected_issues=(DetectedIssue(issue_code="ARTIFACT.STALE_REVISION", field_path="/artifacts/STATEMENT_INDEX"),))  # T23
    if set_digest_mismatch:
        return replace(manifest, state=ArtifactSetState.DIGEST_MISMATCH, detected_issues=(DetectedIssue(issue_code="ARTIFACT.DIGEST_MISMATCH", field_path="/artifacts/observed_digest"),))  # T24
    if manifest.records and manifest.records[0].state in (ArtifactItemState.STALE, "STALE"):
        return replace(manifest, state=ArtifactSetState.STALE_MIXED_REVISION, detected_issues=(DetectedIssue(issue_code="ARTIFACT.STALE_REVISION", field_path="/artifacts/0"),))  # T70
    if manifest.records and manifest.records[0].state in (ArtifactItemState.MISMATCH, "MISMATCH"):
        return replace(manifest, state=ArtifactSetState.DIGEST_MISMATCH, detected_issues=(DetectedIssue(issue_code="ARTIFACT.DIGEST_MISMATCH", field_path="/artifacts/0/observed_digest"),))  # T71
    return replace(manifest, detected_issues=())  # T67; T72 SUPERSEDED remains legal and issue-free


def retry_artifact_set(
    root: Path,
    manifest: ArtifactSetManifest,
    projections: Mapping[str, bytes],
    *,
    key: IdempotencyKey,
    current_frozen_input_refs: tuple[VersionedObjectRef, ...],
    current_schema_version: str,
    current_statement_set_id: str,
    current_contract_digest: DigestRef | None,
    attempt_id: str,
    now: str,
) -> ArtifactSetManifest:
    if (
        not isinstance(manifest, ArtifactSetManifest)
        or not isinstance(manifest.records, tuple)
        or not isinstance(key, IdempotencyKey)
        or key != manifest.key
        or not isinstance(current_frozen_input_refs, tuple)
        or not current_frozen_input_refs
        or any(not isinstance(ref, VersionedObjectRef) for ref in current_frozen_input_refs)
        or not current_schema_version
        or not current_statement_set_id
        or key.statement_set_id != current_statement_set_id
        or key.contract_digest != current_contract_digest
    ):
        raise F09ContractError(
            issue_code="ARTIFACT.STATE_INVALID",
            field_path="/artifacts/0/state",
            diagnostic="retry accepts only one canonical manifest and its identical key",
        )
    required_roles = ("REPORT", "STATEMENT_RECORDS", "STATEMENT_INDEX")
    if (
        not isinstance(projections, Mapping)
        or set(projections) != set(required_roles)
        or any(not isinstance(projections[role], bytes) for role in required_roles)
    ):
        raise F09ContractError(
            issue_code="ARTIFACT.STATE_INVALID",
            field_path="/artifacts/0/state",
            diagnostic="retry requires all three target payloads to preserve complete target identity",
        )
    projection_digests = {
        role: DigestRef("sha256", "RAW-UTF8", sha256(projections[role]).hexdigest())
        for role in required_roles
    }
    # R19 two-stage retry proof: retained history is validated against its own identity;
    # only non-superseded current records are compared with the incoming operation.
    retained_record_invalid = any(
        not isinstance(record, ArtifactRecord)
        or not isinstance(record.attempts, tuple)
        or not record.attempts
        or record.schema_version is None
        or any(
            not isinstance(attempt, ArtifactWriteAttempt)
            or attempt.artifact_id != record.artifact_id
            or attempt.attempt_number != attempt_index + 1
            or not attempt.input_snapshot_refs
            or (
                attempt.retry_of_attempt_id
                != (None if attempt_index == 0 else record.attempts[attempt_index - 1].attempt_id)
            )
            for attempt_index, attempt in enumerate(record.attempts)
        )
        for record in manifest.records
    )
    if retained_record_invalid:
        raise F09ContractError(
            issue_code="ARTIFACT.STATE_INVALID",
            field_path="/artifacts/0/attempts",
            diagnostic="every retained record must own a nonempty internally coherent append-only attempt chain",
        )
    current_records = tuple(
        record for record in manifest.records
        if record.state not in (ArtifactItemState.SUPERSEDED, "SUPERSEDED")
    )
    current_identity_invalid = any(
        record.case_id != key.case_id
        or record.track != key.track
        or record.statement_set_id != key.statement_set_id
        or any(attempt.idempotency_key != key.canonical_key_digest.value for attempt in record.attempts)
        for record in current_records
    )
    if current_identity_invalid:
        raise F09ContractError(
            issue_code="ARTIFACT.STATE_INVALID",
            field_path="/artifacts/0/attempts/0/idempotency_key",
            diagnostic="only current non-superseded records must match the incoming operation identity",
        )
    current_attempts = tuple(attempt for record in current_records for attempt in record.attempts)
    canonical_input_refs = current_frozen_input_refs
    canonical_schema_version = current_schema_version
    if any(attempt.input_snapshot_refs != canonical_input_refs for attempt in current_attempts) or any(record.schema_version != canonical_schema_version for record in current_records):
        raise F09ContractError(
            issue_code="ARTIFACT.STATE_INVALID",
            field_path="/artifacts/0/attempts/0/input_snapshot_refs",
            diagnostic="current records must share the current operation's frozen refs and schema; superseded history is excluded",
        )
    current_records_by_role = {
        role: tuple(
            record for record in manifest.records
            if record.artifact_role == role
            and record.state not in (ArtifactItemState.SUPERSEDED, "SUPERSEDED")
        )
        for role in required_roles
    }
    if any(len(current_records_by_role[role]) > 1 for role in required_roles):
        raise F09ContractError(
            issue_code="ARTIFACT.STATE_INVALID",
            field_path="/artifacts/0/state",
            diagnostic="retry manifest has multiple current records for one canonical role",
        )
    target_mismatch = any(
        current_records_by_role[role]
        and current_records_by_role[role][0].expected_digest != projection_digests[role]
        for role in required_roles
    )
    if target_mismatch:
        return replace(
            manifest,
            state=ArtifactSetState.DIGEST_MISMATCH,
            detected_issues=(DetectedIssue(
                issue_code="IDEMPOTENCY.DIGEST_MISMATCH",
                field_path="/canonical_key_digest",
            ),),
        )  # T28: same key, different target digest; never overwrite
    roles_requiring_write = tuple(
        role for role in required_roles
        if not current_records_by_role[role]
        or current_records_by_role[role][0].state
        not in (ArtifactItemState.VERIFIED, "VERIFIED")
        or current_records_by_role[role][0].observed_digest != projection_digests[role]
    )
    if not roles_requiring_write:
        return replace(manifest, detected_issues=())  # T27: same key, same complete verified targets
    operation_root = resolve_artifact_operation_root(root, key)  # R19 containment preflight precedes mkdir/write
    records = manifest.records
    for role in roles_requiring_write:
        previous = current_records_by_role[role][0] if current_records_by_role[role] else None
        artifact_id = (
            previous.artifact_id if previous is not None
            else "ARTIFACT:" + key.canonical_key_digest.value + ":" + role
        )
        target = operation_root / (role.lower() + ".bin")
        try:
            operation_root.mkdir(parents=True, exist_ok=True)
            target.write_bytes(projections[role])
            observed_digest = DigestRef(
                "sha256", "RAW-UTF8", sha256(target.read_bytes()).hexdigest()
            )
        except OSError as error:
            error_digest = DigestRef(
                "sha256", "RAW-UTF8",
                sha256((type(error).__name__ + ":" + str(error)).encode("utf-8")).hexdigest(),
            )
            failed_attempt = ArtifactWriteAttempt(
                attempt_id=attempt_id + ":" + role,
                artifact_id=artifact_id,
                idempotency_key=key.canonical_key_digest.value,
                attempt_number=(1 if previous is None else len(previous.attempts) + 1),
                retry_of_attempt_id=(None if previous is None or not previous.attempts else previous.attempts[-1].attempt_id),
                input_snapshot_refs=canonical_input_refs,
                started_at=now,
                finished_at=now,
                outcome="FAILED",
                observed_digest=None,
                error_class=type(error).__name__,
                error_message_digest=error_digest,
            )
            failed_record = ArtifactRecord(
                artifact_id=artifact_id,
                artifact_role=role,
                track=manifest.key.track,
                case_id=manifest.key.case_id,
                statement_set_id=manifest.key.statement_set_id,
                run_id=None,
                path_locator=target.as_posix(),
                schema_version=canonical_schema_version,
                expected_digest=projection_digests[role],
                observed_digest=None,
                state=ArtifactItemState.FAILED,
                attempts=((failed_attempt,) if previous is None else previous.attempts + (failed_attempt,)),
                issue_ids=(),
            )
            retained = tuple(record for record in records if record is not previous)
            failed_records = retained + (failed_record,)
            failed_records_digest = digest_artifact_records(failed_records)
            return ArtifactSetManifest(
                manifest_id=manifest.manifest_id,
                key=key,
                records=failed_records,
                state=(ArtifactSetState.FAILED if role == "REPORT" else ArtifactSetState.PARTIAL),
                digest=failed_records_digest,
                detected_issues=(
                    () if role == "REPORT" else
                    (DetectedIssue(
                        issue_code="ARTIFACT.WRITE_FAILED",
                        field_path=("/artifacts/STATEMENT_RECORDS" if role == "STATEMENT_RECORDS" else "/artifacts/STATEMENT_INDEX"),
                    ),)
                ),
            )
        successful_attempt = ArtifactWriteAttempt(
            attempt_id=attempt_id + ":" + role,
            artifact_id=artifact_id,
            idempotency_key=key.canonical_key_digest.value,
            attempt_number=(1 if previous is None else len(previous.attempts) + 1),
            retry_of_attempt_id=(None if previous is None or not previous.attempts else previous.attempts[-1].attempt_id),
            input_snapshot_refs=canonical_input_refs,
            started_at=now,
            finished_at=now,
            outcome="SUCCEEDED",
            observed_digest=observed_digest,
            error_class=None,
            error_message_digest=None,
        )
        verified_record = ArtifactRecord(
            artifact_id=artifact_id,
            artifact_role=role,
            track=manifest.key.track,
            case_id=manifest.key.case_id,
            statement_set_id=manifest.key.statement_set_id,
            run_id=None,
            path_locator=target.as_posix(),
            schema_version=canonical_schema_version,
            expected_digest=projection_digests[role],
            observed_digest=observed_digest,
            state=ArtifactItemState.VERIFIED,
            attempts=((successful_attempt,) if previous is None else previous.attempts + (successful_attempt,)),
            issue_ids=(),
        )
        records = tuple(record for record in records if record is not previous) + (verified_record,)
    return replace(
        manifest,
        records=records,
        state=ArtifactSetState.COMPLETE_VERIFIED,
        digest=digest_artifact_records(records),
        detected_issues=(),
    )


def coordinate_artifact_operation(
    root: Path,
    statement_set: StatementSet,
    projections: Mapping[str, bytes],
    *,
    existing_manifest: ArtifactSetManifest | None,
    key: IdempotencyKey,
    attempt_id: str,
    now: str,
) -> ArtifactSetManifest:
    if existing_manifest is None or existing_manifest.key != key:
        return write_artifact_set(
            root, statement_set, projections,
            key=key, attempt_id=attempt_id, now=now,
        )  # changed canonical key is mechanically routed to a new operation identity
    return retry_artifact_set(
        root, existing_manifest, projections,
        key=key,
        current_frozen_input_refs=(statement_set.source_package_ref,),
        current_schema_version=statement_set.statement_schema_version,
        current_statement_set_id=statement_set.statement_set_id,
        current_contract_digest=key.contract_digest,
        attempt_id=attempt_id,
        now=now,
    )
```

The displayed writer binds every path, digest, attempt, record, manifest identity, and partial tuple in its own continuous function body; no test fixture or prose supplies a local. Physical paths are rooted at `root / key.canonical_key_digest.value`: exact-key retry therefore resolves to the same operation directory, while a changed canonical key resolves to a disjoint directory and cannot overwrite any prior operation file. Prior operation directories, records, and attempts remain append-only audit evidence. The retry port receives the actual incoming canonical `IdempotencyKey` and the complete three-role target payload map, but permits each role to have zero or one non-superseded current record. Before target comparison or write, it proves every retained attempt carries the same nonempty frozen input-ref tuple and same canonical key, and proves every retained record carries the same case, track, statement-set revision, and one non-null schema version. A missing-role record inherits that proven canonical schema/revision/input identity, never `None` and never a first-arbitrary-attempt guess. For the same key, every existing role first proves its canonical expected target digest: any difference is T28 and blocks every write; a complete verified equal set is the T27 issue-free no-op; otherwise only missing, failed, or unverified equal-target roles are written, each with an appended canonical `ArtifactWriteAttempt`, so T21 can continue RECORDS then INDEX and T22 can continue INDEX without rerunning or duplicating verified roles. `coordinate_artifact_operation()` is the displayed authoritative caller transition: absent prior manifest or changed canonical key calls `write_artifact_set()` as a new isolated operation; only exact key equality calls `retry_artifact_set()`. No local control/error type represents new identity. REPORT has no phase-owned issue pair, but every REPORT filesystem failure returns a canonical FAILED `ArtifactRecord` and FAILED `ArtifactWriteAttempt` preserving input refs, target digest, outcome, error class, error-message digest, start/finish time, and an empty `detected_issues` tuple before T21/T22. T21/T22 and T23/T24/T28/T70/T71 coherent failures use only the frozen returned pairs; T27, T67, T72, REPORT failure, ordinary successes, and successful continuation explicitly carry no added semantic issue.

- [ ] **Step 1: Write RED state tests.** Parameterize all eight legal item states and reject `NOT_STARTED/WRITTEN`; test all five set states and readiness only for complete verified.
- [ ] **Step 2: Write RED failure-injection tests.** Assert REPORT filesystem failure returns a nonsemantic FAILED record plus canonical FAILED attempt with outcome/error digest/time and no phase-owned pair; inject the frozen semantic failures only at STATEMENT_RECORDS and STATEMENT_INDEX, assert successful prior files remain, and assert no feedback readiness occurs.
- [ ] **Step 3: Write RED idempotency tests.** Prove `coordinate_artifact_operation()` routes changed canonical key to a new write identity; same key plus complete verified equal targets is issue-free T27; same key plus any existing different target digest is T28 before writes; T21 partial continues only RECORDS/INDEX and T22 partial continues only INDEX with append-only attempts; old/new revisions produce STALE_MIXED_REVISION; superseded item remains auditable.
- [ ] **Step 4: Verify RED.** `python -m pytest tests/f09/test_artifact_lifecycle.py -q`; expected missing-module FAIL.
- [ ] **Step 5: Implement minimal coordinator.** Preflight target paths under caller root; write each temp in target directory; flush/fsync/replace; verify bytes and digest before VERIFIED. Never delete committed files to simulate rollback.
- [ ] **Step 6: Verify GREEN.** Repeat Step 4; expected PASS.
- [ ] **Step 7: Regression.** `python -m pytest tests/test_production_service.py::test_submit_hard_fails_when_required_artifact_is_missing tests/test_recompute_report_write.py::test_recompute_writes_rendered_report_md tests/v5/test_render_report_v6.py::test_render_report_v6_generates_report_and_v5_json -q`; expected `3 passed`.
- [ ] **Step 8: Commit.** `git add engine/f09/artifacts.py tests/f09/test_artifact_lifecycle.py && git commit -m "feat(f09): coordinate digest-bound artifact lifecycle"`.
- [ ] **Independent review gate.** Reviewer kills each write boundary, retries with same and conflicting payloads, confirms no overwrite/delete/production path escape, and checks every returned PARTIAL/stale/mismatch/invalid/conflict manifestation against its exact production-owned `detected_issues` pair; legal T27 no-op and T72 `SUPERSEDED` must remain issue-free.
- [ ] **Rollback.** Code rollback: `git revert --no-edit HEAD`. Data rollback: remove only uncommitted temp files; committed test artifacts are superseded by new revision and retained for audit.

## Task 8: Feedback Binding and Learning Eligibility Without Learning

**Files:**
- Create: `engine/f09/feedback.py`
- Create: `tests/f09/test_feedback_eligibility.py`

**Interfaces:** All seven canonical match dimensions are explicit. Mismatch, unmapped anchor and mixed revision are represented by dimension values plus issue IDs, never by invented top-level statuses. Submission source identity uses the complete `SnapshotRef`, not a generic ref or statement-set shortcut. Track uncertainty uses PI-230's literal typed source/target bindings; anchor availability is an independent fact and may neither create nor clear track uncertainty.
```python
from engine.f09.contracts import DetectedIssue

MatchRequired: TypeAlias = Literal["MATCH", "MISMATCH", "UNKNOWN"]
MatchOptional: TypeAlias = Literal["MATCH", "MISMATCH", "NOT_APPLICABLE", "UNKNOWN"]
TrackSourceState: TypeAlias = Literal["AVAILABLE_RESOLVED", "SOURCE_MISSING", "UNPARSABLE", "AMBIGUOUS", "INTEGRITY_FAILED"]
TrackSourceReasonCode: TypeAlias = Literal["TRACK_SOURCE_MISSING", "TRACK_SOURCE_UNPARSABLE", "TRACK_SOURCE_AMBIGUOUS", "TRACK_SOURCE_INTEGRITY_FAILED"]
@dataclass(frozen=True)
class TrackSourceBinding:
    track_source_binding_id: str
    side: Literal["SUBMISSION_SOURCE", "BINDING_TARGET"]
    track: RunTrack
    state: TrackSourceState
    source_evidence_ref: VersionedObjectRef
    parser_ref: VersionedObjectRef
    schema_version: str
    contract_version: str
    content_digest: DigestRef
    state_reason_codes: tuple[TrackSourceReasonCode, ...]
    captured_at: str
@dataclass(frozen=True)
class FeedbackItem:
    feedback_item_id: str
    feedback_id: str
    source_span_locator: str
    target_statement_id: str | None
    target_statement_revision_id: str | None
    target_run_id: str | None
    target_prediction_id: str | None
    verdict: str
    annotation: str
    integrity: Literal["VALID", "INVALID", "UNRESOLVED"]
    issue_ids: tuple[str, ...]
@dataclass(frozen=True)
class StatementProjectionRecord:
    projection_id: str
    projection_type: Literal["STATEMENT_INDEX", "STATEMENT_RECORDS"]
    statement_set_id: str
    statement_id: str
    statement_revision_id: str
    source_statement_digest: DigestRef
    projected_object_ref: VersionedObjectRef
    transformation_id: str
    fidelity: str
    dropped_refs: tuple[VersionedObjectRef, ...]
    synthesized_fields: tuple[str, ...]
    issue_ids: tuple[str, ...]
@dataclass(frozen=True)
class AnchorSelectionRecord:
    anchor_selection_id: str
    statement_id: str
    statement_revision_id: str
    all_rule_refs: tuple[VersionedObjectRef, ...]
    selected_anchor_rule_ref: VersionedObjectRef | None
    non_anchor_rule_refs: tuple[VersionedObjectRef, ...]
    selection_policy_id: str
    selection_policy_version: str
    source_order_digest: DigestRef
    fidelity: str
    fanout_scope: str
    issue_ids: tuple[str, ...]
@dataclass(frozen=True)
class FeedbackSubmission:
    feedback_id: str
    case_id: str
    track: RunTrack
    track_source_binding: TrackSourceBinding
    source_snapshot_ref: SnapshotRef
    parser_id: str
    parser_version: str
    feedback_items: tuple[FeedbackItem, ...]
    content_digest: DigestRef
    captured_at: str
@dataclass(frozen=True)
class FeedbackBinding:
    feedback_binding_id: str
    feedback_item_ref: VersionedObjectRef
    binding_protocol: Literal["PRODUCTION_STATEMENT", "PREPROD_RUN_TARGET"]
    source_track_binding_ref: VersionedObjectRef
    target_track_source_binding: TrackSourceBinding
    case_match: MatchRequired
    track_match: MatchRequired
    run_match: MatchOptional
    statement_match: MatchOptional
    revision_match: MatchOptional
    statement_set_match: MatchOptional
    artifact_digest_match: MatchRequired
    target_object_refs: tuple[VersionedObjectRef, ...]
    record_anchor_ref: VersionedObjectRef | None
    status: Literal["BOUND", "UNBOUND", "AMBIGUOUS", "INVALID"]
    issue_ids: tuple[str, ...]
    detected_issues: tuple[DetectedIssue, ...]
@dataclass(frozen=True)
class FeedbackOperationResult:
    operation_disposition: Literal["NEW_OPERATION", "REUSED_OPERATION", "TARGET_MISMATCH"]
    source_identity_relation: Literal["INITIAL", "SAME", "CHANGED"]
    prior_key: IdempotencyKey | None
    current_key: IdempotencyKey
    prior_target_digest: DigestRef | None
    current_target_digest: DigestRef
    bindings: tuple[FeedbackBinding, ...]
    overwrite_permitted: Literal[False]
    detected_issues: tuple[DetectedIssue, ...]
@dataclass(frozen=True)
class LearningEligibility:
    eligibility_id: str
    feedback_binding_id: str
    policy_id: str
    policy_version: str
    status: Literal["ELIGIBLE", "INELIGIBLE", "HUMAN_REVIEW"]
    learning_target_refs: tuple[VersionedObjectRef, ...]
    excluded_supporting_rule_refs: tuple[VersionedObjectRef, ...]
    blocking_reason_codes: tuple[str, ...]
    detected_issues: tuple[DetectedIssue, ...]
    evaluated_at: str
def validate_feedback_binding(submission: FeedbackSubmission, statement_set: StatementSet | None, manifest: ArtifactSetManifest, *, prior_key: IdempotencyKey | None, current_key: IdempotencyKey, prior_target_digest: DigestRef | None, current_target_digest: DigestRef, target_track_source_binding: TrackSourceBinding, statement_refs: Mapping[tuple[str, str], VersionedObjectRef], statement_set_ref: VersionedObjectRef | None, records_projection_refs: Mapping[str, VersionedObjectRef], records_projection_records: Mapping[str, StatementProjectionRecord], anchor_selections: Mapping[tuple[str, str], AnchorSelectionRecord], preprod_target_refs: Mapping[str, tuple[VersionedObjectRef, ...]], governing_statement_contract_version: str, governing_statement_set_contract_version: str, governing_statement_records_contract_version: str, governing_rule_contract_version: str) -> FeedbackOperationResult
def validate_feedback_binding_record(binding: FeedbackBinding) -> None
def evaluate_learning_eligibility(binding: FeedbackBinding, *, policy_id: str, policy_version: str, evaluated_at: str) -> LearningEligibility
def validate_learning_eligibility(eligibility: LearningEligibility) -> None
```
A submission with multiple `feedback_items` yields one canonical binding per item. 每个 item 的 `feedback_id` 必须逐值等于 submission；`source_span_locator` 必须定位 parser 输入 snapshot；nullable statement/revision 与 nullable run/prediction 是两类 target protocol 的原始身份材料，不得互相补值。`PRODUCTION_STATEMENT` requires case/track/statement/revision/statement-set/artifact-digest dimensions to be `MATCH` and explicitly permits only `run_match=NOT_APPLICABLE`; `PREPROD_RUN_TARGET` requires case/track/run/artifact-digest dimensions to be `MATCH` and explicitly permits only statement/revision/statement-set dimensions to be `NOT_APPLICABLE`. Any required dimension set to `NOT_APPLICABLE` is `UNBOUND`. The caller supplies prior/current canonical `IdempotencyKey` values and prior/current target digests: changed source digest must change `canonical_key_digest` and is T58 changed-input/new identity without last-write-wins; exact same key plus different target digest is a separate mismatch and cannot overwrite. Eligibility identity additionally covers target revision and policy version. `source_track_binding_ref` identifies the `TrackSourceBinding` itself by its own ID, schema version, contract version, and content digest, not its source evidence. Canonical statement, statement-set, statement-records projection, and selected rule-anchor refs resolve from their own objects, projection records, anchor-selection mapping, and metadata; feedback and manifest digests never fabricate them. Missing prerequisites enter `INVALID > AMBIGUOUS > UNBOUND > BOUND` aggregation before construction and yield a coherent non-BOUND record with an empty target graph. `AVAILABLE_RESOLVED` requires no reason code；each failure state requires exactly its corresponding code. There is no default `BOUND`, and `track_match=UNKNOWN` cannot yield `BOUND` or automatic `ELIGIBLE`. `issue_ids`, reason codes, status, and dimensions remain audit/state fields, not adapter issue oracles. `BOUND`/`ELIGIBLE` objects have empty `detected_issues`; any PI-300 negative requiring a pair carries it on the producer return.
**R19 controlling Task 8 clarification.** This paragraph supersedes contradictory R18 exact-triple and later dereference behavior. The binder performs a strict guard stage over every supplied statement, statement-set, projection, anchor, track-binding, and PREPROD ref before any nested attribute access. A usable canonical ref must be a `VersionedObjectRef` with nonblank object type/ID/schema, the authority-required revision and contract presence for that object kind, and `DigestPresent(DigestRef)` with canonical algorithm/canonicalization/value shape. Guard results are explicit tagged validated refs; later stages may dereference only those validated values. Any malformed ref, malformed digest binding, inconsistent object identity/version/digest, or malformed selection/projection record sets `canonical_material_invalid=True`, contributes to the first `INVALID` branch, emits an empty target graph, and cannot continue into a nested dereference. Valid absence remains `UNBOUND`; multiple otherwise valid candidates remain `AMBIGUOUS`; precedence stays `INVALID > AMBIGUOUS > UNBOUND > BOUND`.

Production validation requires the canonical statement, statement set, statement-records projection and selected `RULE` anchor. It compares object type/ID, statement revision, schema version, contract version, authoritative digest, set membership and record/projection identity. For the PI-230 first-valid-evidence-rule compatibility projection, policy ID/version must equal the policy identity supplied by the approved canonical configuration; R19 does not invent a new literal policy identity. The record must use `fidelity="LOSSY"` and `fanout_scope="SELECTED_ANCHOR_ONLY"`. Validation requires a nonempty ordered `all_rule_refs`, every ref as canonical `RULE`, no duplicate refs, selected ref occurring exactly once, selected ref absent from `non_anchor_rule_refs`, and `non_anchor_rule_refs` exactly equal to ordered all refs with the selected occurrence removed. It recomputes `source_order_digest` from the deterministic ordered full identities of `all_rule_refs`; merely type-checking or trusting the digest is forbidden.

PREPROD is run-only. It requires `target_run_id`, case/track/run agreement, a nonempty set of canonical run-related artifact refs backed by retained artifact records, usable observed/expected artifact digests, and PI-230's protocol-required run/artifact minimum conditions. A usable run snapshot is required; a feedback attachment without that run snapshot is insufficient. Additional legitimate protocol refs are permitted. No exact unique closed triple is asserted, and no production statement, statement records, statement set, projection, or `RULE` anchor is required or dereferenced. PREPROD always has `record_anchor_ref=None` and statement/revision/set dimensions `NOT_APPLICABLE`. Duplicate target refs, mixed case/track/run, missing required run snapshot, digest disagreement, or ref/record inconsistency fail closed according to the same precedence.

`current_target_digest` and `prior_target_digest` are each recomputed from the actual immutable protocol-specific target graph supplied for that operation, never copied from `manifest.digest`. Deterministic RFC8785/JCS input includes the protocol tag and each ordered target ref's object type, object ID, revision ID, schema version, contract version, digest-binding status and full digest identity, source locator ID, and captured time. Production input additionally includes statement/set/records identities, the selected `RULE` anchor, exact selection policy ID/version, and recomputed source-order digest. PREPROD input includes only its validated run ID and extensible validated run-artifact refs. Normalization rejects duplicate refs and sorts only where authority defines a set; authority-defined ordered sequences retain order. Replacing records therefore necessarily recomputes this graph digest.

**R18 protocol and operation clarification, as narrowed by R19.** Production BOUND resolves exactly `STATEMENT`/`STATEMENT_SET`/`STATEMENT_RECORDS` plus the selected `RULE` anchor. PREPROD BOUND resolves the authority-required nonempty extensible run-target graph, emits no production statement refs, and requires `record_anchor_ref=None`; the former exact three-role PREPROD tuple is withdrawn. Changed source plus changed canonical key returns producer-owned `FeedbackOperationResult(operation_disposition="NEW_OPERATION", source_identity_relation="CHANGED", overwrite_permitted=False)` without a semantic mismatch issue; exact same key plus different freshly recomputed target-graph digest alone returns `TARGET_MISMATCH` with `IDEMPOTENCY.DIGEST_MISMATCH`, and neither path permits last-write-wins.

**R15 literal Task 8 producer source — copy continuously into the two displayed functions.** The binder defines target resolution, protocol, references, all seven dimensions, aggregate status, issue selection, and return accumulation in one source. The evaluator defines identity, status, targets, exclusions, and reasons in one source and always starts with `detected_issues=()`. Statuses, dimensions, reason codes, and existing issue tuples are never converted into issue pairs.

```python
@dataclass(frozen=True)
class ValidatedVersionedRef:
    value: VersionedObjectRef


def validate_versioned_ref(
    raw_ref: object,
    *,
    required_object_type: str | None = None,
    require_revision: bool,
    require_contract: bool,
) -> ValidatedVersionedRef:
    if not isinstance(raw_ref, VersionedObjectRef):
        raise F09ContractError("FEEDBACK.TARGET_UNBOUND", "/feedback_bindings/0", "canonical target ref has invalid shape")
    binding = raw_ref.digest_binding
    if (
        not raw_ref.object_type
        or not raw_ref.object_id
        or not raw_ref.schema_version
        or required_object_type is not None and raw_ref.object_type != required_object_type
        or require_revision and not raw_ref.revision_id
        or require_contract and not raw_ref.contract_version
        or not isinstance(binding, DigestPresent)
        or not isinstance(binding.digest, DigestRef)
        or not binding.digest.algorithm
        or not binding.digest.canonicalization
        or not binding.digest.value
    ):
        raise F09ContractError("FEEDBACK.TARGET_UNBOUND", "/feedback_bindings/0", "canonical target ref is incomplete or inconsistent")
    return ValidatedVersionedRef(raw_ref)


def digest_ordered_rule_refs(refs: tuple[VersionedObjectRef, ...]) -> DigestRef:
    material = [_versioned_ref_material(ref) for ref in refs]
    encoded = json.dumps(material, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(encoded).hexdigest())


def digest_protocol_target_graph(
    protocol: Literal["PRODUCTION_STATEMENT", "PREPROD_RUN_TARGET"],
    target_refs: tuple[VersionedObjectRef, ...],
    *,
    target_run_id: str | None,
    selection: AnchorSelectionRecord | None,
) -> DigestRef:
    material: dict[str, object] = {
        "protocol": protocol,
        "target_run_id": target_run_id,
        "target_refs": [_versioned_ref_material(ref) for ref in target_refs],
    }
    if protocol == "PRODUCTION_STATEMENT":
        if not isinstance(selection, AnchorSelectionRecord):
            raise F09ContractError("FEEDBACK.TARGET_UNBOUND", "/feedback_bindings/0", "production target digest requires canonical anchor selection")
        selected = validate_versioned_ref(selection.selected_anchor_rule_ref, required_object_type="RULE", require_revision=True, require_contract=True).value
        all_rules = tuple(validate_versioned_ref(ref, required_object_type="RULE", require_revision=True, require_contract=True).value for ref in selection.all_rule_refs)
        non_anchor = tuple(validate_versioned_ref(ref, required_object_type="RULE", require_revision=True, require_contract=True).value for ref in selection.non_anchor_rule_refs)
        material["selection"] = {
            "selection_policy_id": selection.selection_policy_id,
            "selection_policy_version": selection.selection_policy_version,
            "selected_anchor_rule_ref": _versioned_ref_material(selected),
            "all_rule_refs": [_versioned_ref_material(ref) for ref in all_rules],
            "non_anchor_rule_refs": [_versioned_ref_material(ref) for ref in non_anchor],
            "source_order_digest": _digest_ref_material(digest_ordered_rule_refs(all_rules)),
            "fidelity": selection.fidelity,
            "fanout_scope": selection.fanout_scope,
        }
    elif selection is not None:
        raise F09ContractError("FEEDBACK.TARGET_UNBOUND", "/feedback_bindings/0", "PREPROD target digest cannot contain production anchor selection")
    encoded = json.dumps(material, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(encoded).hexdigest())


def validate_feedback_binding(
    submission: FeedbackSubmission,
    statement_set: StatementSet | None,
    manifest: ArtifactSetManifest,
    *,
    prior_key: IdempotencyKey | None,
    current_key: IdempotencyKey,
    prior_target_digest: DigestRef | None,
    current_target_digest: DigestRef,
    target_track_source_binding: TrackSourceBinding,
    statement_refs: Mapping[tuple[str, str], VersionedObjectRef],
    statement_set_ref: VersionedObjectRef | None,
    records_projection_refs: Mapping[str, VersionedObjectRef],
    records_projection_records: Mapping[str, StatementProjectionRecord],
    anchor_selections: Mapping[tuple[str, str], AnchorSelectionRecord],
    preprod_target_refs: Mapping[str, tuple[VersionedObjectRef, ...]],
    governing_statement_contract_version: str,
    governing_statement_set_contract_version: str,
    governing_statement_records_contract_version: str,
    governing_rule_contract_version: str,
) -> FeedbackOperationResult:
    if not isinstance(submission, FeedbackSubmission) or not isinstance(submission.feedback_items, tuple):
        raise F09ContractError(
            issue_code="FEEDBACK.TARGET_UNBOUND",
            field_path="/feedback_bindings/0",
            diagnostic="feedback submission has invalid shape",
        )
    if not isinstance(manifest, ArtifactSetManifest) or not isinstance(manifest.records, tuple):
        raise F09ContractError(
            issue_code="FEEDBACK.TARGET_UNBOUND",
            field_path="/feedback_bindings/0",
            diagnostic="feedback artifact target graph has invalid shape",
        )
    production_requested = any(item.target_statement_id is not None for item in submission.feedback_items if isinstance(item, FeedbackItem))
    if production_requested and (not isinstance(statement_set, StatementSet) or not isinstance(statement_set.statements, tuple)):
        raise F09ContractError(
            issue_code="FEEDBACK.TARGET_UNBOUND",
            field_path="/feedback_bindings/0",
            diagnostic="production feedback requires a canonical statement set; PREPROD does not",
        )
    if (
        not isinstance(statement_refs, Mapping)
        or production_requested and not isinstance(statement_set_ref, VersionedObjectRef)
        or not production_requested and statement_set_ref is not None
        or not isinstance(records_projection_refs, Mapping)
        or not isinstance(records_projection_records, Mapping)
        or not isinstance(anchor_selections, Mapping)
        or not isinstance(preprod_target_refs, Mapping)
        or not governing_statement_contract_version
        or not governing_statement_set_contract_version
        or not governing_statement_records_contract_version
        or not governing_rule_contract_version
    ):
        raise F09ContractError(
            issue_code="FEEDBACK.TARGET_UNBOUND",
            field_path="/feedback_bindings/0",
            diagnostic="canonical feedback reference maps have invalid shape",
        )
    if not isinstance(target_track_source_binding, TrackSourceBinding):
        raise F09ContractError(
            issue_code="FEEDBACK.TRACK_MISMATCH",
            field_path="/feedback_bindings/0/track_match",
            diagnostic="target track source binding has invalid shape",
        )
    if not isinstance(submission.track_source_binding, TrackSourceBinding):
        raise F09ContractError(
            issue_code="FEEDBACK.TRACK_MISMATCH",
            field_path="/feedback_bindings/0/track_match",
            diagnostic="submission track source binding has invalid shape",
        )
    if not isinstance(submission.source_snapshot_ref, SnapshotRef) or not isinstance(submission.source_snapshot_ref.content_digest, DigestRef):
        raise F09IntegrityError(
            issue_code="IDEMPOTENCY.DIGEST_MISMATCH",
            field_path="/feedback/source_snapshot_ref",
            diagnostic="feedback source snapshot identity has invalid shape",
        )

    if (
        not isinstance(current_key, IdempotencyKey)
        or prior_key is not None and not isinstance(prior_key, IdempotencyKey)
        or current_key.operation not in ("BIND_FEEDBACK", "INGEST_FEEDBACK")
        or current_key.feedback_id != submission.feedback_id
        or current_key.case_id != submission.case_id
        or current_key.track != submission.track
        or current_key.source_digest != submission.source_snapshot_ref.content_digest
    ):
        raise F09ContractError(
            issue_code="FEEDBACK.TARGET_UNBOUND",
            field_path="/feedback_bindings/0",
            diagnostic="current canonical feedback key does not bind the submission identity",
        )
    changed_input_new_identity = prior_key is not None and (
        prior_key.canonical_key_digest != current_key.canonical_key_digest
    )
    same_key_different_target = prior_key is not None and (
        prior_key == current_key
        and prior_target_digest is not None
        and prior_target_digest != current_target_digest
    )
    source_identity_relation: Literal["INITIAL", "SAME", "CHANGED"] = (
        "INITIAL" if prior_key is None else
        "CHANGED" if prior_key.source_digest != current_key.source_digest else "SAME"
    )
    operation_disposition: Literal["NEW_OPERATION", "REUSED_OPERATION", "TARGET_MISMATCH"] = (
        "TARGET_MISMATCH" if same_key_different_target else
        "NEW_OPERATION" if prior_key is None or changed_input_new_identity else
        "REUSED_OPERATION"
    )
    operation_issue = (
        (DetectedIssue("IDEMPOTENCY.DIGEST_MISMATCH", "/feedback/source_snapshot_ref"),)
        if same_key_different_target else ()
    )
    if prior_key is not None and (
        prior_key.source_digest != current_key.source_digest
        and prior_key.canonical_key_digest == current_key.canonical_key_digest
    ):
        raise F09IntegrityError(
            issue_code="IDEMPOTENCY.DIGEST_MISMATCH",
            field_path="/feedback/source_snapshot_ref",
            diagnostic="changed source digest must produce a changed canonical feedback identity",
        )

    if operation_disposition == "TARGET_MISMATCH":
        return FeedbackOperationResult(
            operation_disposition=operation_disposition,
            source_identity_relation=source_identity_relation,
            prior_key=prior_key,
            current_key=current_key,
            prior_target_digest=prior_target_digest,
            current_target_digest=current_target_digest,
            bindings=(),
            overwrite_permitted=False,
            detected_issues=operation_issue,
        )

    bindings: tuple[FeedbackBinding, ...] = ()
    for item_index, item in enumerate(submission.feedback_items):
        if not isinstance(item, FeedbackItem):
            raise F09ContractError(
                issue_code="FEEDBACK.TARGET_UNBOUND",
                field_path="/feedback_bindings/0",
                diagnostic="feedback item has invalid shape",
            )
        binding_protocol: Literal["PRODUCTION_STATEMENT", "PREPROD_RUN_TARGET"] = "PRODUCTION_STATEMENT" if item.target_statement_id is not None else "PREPROD_RUN_TARGET"
        matching_statements: tuple[StandardStatement, ...] = ()
        production_records: tuple[ArtifactRecord, ...] = ()
        preprod_records: tuple[ArtifactRecord, ...] = ()
        resolved_statement: StandardStatement | None = None
        resolved_production_record: ArtifactRecord | None = None
        anchor_selection: AnchorSelectionRecord | None = None
        canonical_target_refs: tuple[VersionedObjectRef, ...] = ()
        record_anchor_ref: VersionedObjectRef | None = None
        canonical_material_invalid = False
        canonical_material_ambiguous = False
        target_case_id: str | None = None

        try:
            if binding_protocol == "PRODUCTION_STATEMENT":
                if statement_set is None:
                    target_unbound = True
                else:
                    target_case_id = statement_set.case_id
                    matching_statements = tuple(statement for statement in statement_set.statements if statement.statement_id == item.target_statement_id)
                    production_records = tuple(record for record in manifest.records if record.artifact_role == "STATEMENT_RECORDS" and record.case_id == statement_set.case_id and record.statement_set_id == statement_set.statement_set_id and record.state not in (ArtifactItemState.SUPERSEDED, "SUPERSEDED"))
                    canonical_material_ambiguous = len(matching_statements) > 1 or len(production_records) > 1
                    resolved_statement = matching_statements[0] if len(matching_statements) == 1 else None
                    resolved_production_record = production_records[0] if len(production_records) == 1 else None
                    identity = None if resolved_statement is None else (resolved_statement.statement_id, resolved_statement.statement_revision_id)
                    raw_statement_ref = None if identity is None else statement_refs.get(identity)
                    raw_records_ref = None if resolved_production_record is None else records_projection_refs.get(resolved_production_record.artifact_id)
                    projection = None if resolved_production_record is None else records_projection_records.get(resolved_production_record.artifact_id)
                    anchor_selection = None if identity is None else anchor_selections.get(identity)
                    statement_ref = validate_versioned_ref(raw_statement_ref, required_object_type="STATEMENT", require_revision=True, require_contract=True).value
                    validated_set_ref = validate_versioned_ref(statement_set_ref, required_object_type="STATEMENT_SET", require_revision=False, require_contract=True).value
                    records_ref = validate_versioned_ref(raw_records_ref, required_object_type="STATEMENT_RECORDS", require_revision=True, require_contract=True).value
                    if not isinstance(projection, StatementProjectionRecord) or not isinstance(anchor_selection, AnchorSelectionRecord):
                        raise F09ContractError("FEEDBACK.TARGET_UNBOUND", "/feedback_bindings/0", "production projection or anchor selection is malformed")
                    all_rules = tuple(validate_versioned_ref(ref, required_object_type="RULE", require_revision=True, require_contract=True).value for ref in anchor_selection.all_rule_refs)
                    selected = validate_versioned_ref(anchor_selection.selected_anchor_rule_ref, required_object_type="RULE", require_revision=True, require_contract=True).value
                    non_anchor = tuple(validate_versioned_ref(ref, required_object_type="RULE", require_revision=True, require_contract=True).value for ref in anchor_selection.non_anchor_rule_refs)
                    expected_non_anchor = tuple(ref for ref in all_rules if ref != selected)
                    production_invalid = (
                        identity is None
                        or statement_ref.object_id != resolved_statement.statement_id
                        or statement_ref.revision_id != resolved_statement.statement_revision_id
                        or statement_ref.schema_version != resolved_statement.statement_schema_version
                        or statement_ref.contract_version != governing_statement_contract_version
                        or statement_ref.digest_binding.digest != resolved_statement.content_digest
                        or validated_set_ref.object_id != statement_set.statement_set_id
                        or validated_set_ref.schema_version != statement_set.statement_schema_version
                        or validated_set_ref.contract_version != governing_statement_set_contract_version
                        or validated_set_ref.digest_binding.digest != statement_set.content_digest
                        or resolved_production_record is None
                        or records_ref.object_id != resolved_production_record.artifact_id
                        or records_ref.revision_id != resolved_statement.statement_revision_id
                        or records_ref.contract_version != governing_statement_records_contract_version
                        or records_ref.digest_binding.digest != resolved_production_record.observed_digest
                        or any(ref.contract_version != governing_rule_contract_version for ref in all_rules)
                        or selected.contract_version != governing_rule_contract_version
                        or any(ref.contract_version != governing_rule_contract_version for ref in non_anchor)
                        or projection.projection_type != "STATEMENT_RECORDS"
                        or (projection.statement_id, projection.statement_revision_id) != identity
                        or projection.statement_set_id != statement_set.statement_set_id
                        or projection.projected_object_ref != records_ref
                        or projection.source_statement_digest != resolved_statement.content_digest
                        or anchor_selection.selection_policy_id != "PRODUCTION-STATEMENT-ELIGIBILITY"
                        or anchor_selection.selection_policy_version != "policy-v1"
                        or anchor_selection.fidelity != "LOSSY"
                        or anchor_selection.fanout_scope != "SELECTED_ANCHOR_ONLY"
                        or not all_rules
                        or len(set(all_rules)) != len(all_rules)
                        or all_rules.count(selected) != 1
                        or non_anchor != expected_non_anchor
                        or selected in non_anchor
                        or anchor_selection.source_order_digest != digest_ordered_rule_refs(all_rules)
                    )
                    canonical_material_invalid = production_invalid
                    if not production_invalid and not canonical_material_ambiguous:
                        canonical_target_refs = (statement_ref, validated_set_ref, records_ref)
                        record_anchor_ref = selected
                    target_unbound = not canonical_target_refs or record_anchor_ref is None
            else:
                raw_preprod_refs = () if item.target_run_id is None else preprod_target_refs.get(item.target_run_id, ())
                validated_preprod_refs = tuple(validate_versioned_ref(ref, require_revision=True, require_contract=True).value for ref in raw_preprod_refs)
                preprod_records = tuple(record for record in manifest.records if record.case_id == submission.case_id and record.run_id == item.target_run_id and record.artifact_role in {ref.object_type for ref in validated_preprod_refs} and record.state not in (ArtifactItemState.SUPERSEDED, "SUPERSEDED"))
                refs_by_identity = {(ref.object_type, ref.object_id): ref for ref in validated_preprod_refs}
                records_by_identity = {(record.artifact_role, record.artifact_id): record for record in preprod_records}
                canonical_material_invalid = (
                    len(refs_by_identity) != len(validated_preprod_refs)
                    or len(records_by_identity) != len(preprod_records)
                    or not any(ref.object_type == "RUN_SNAPSHOT" for ref in validated_preprod_refs)
                    or set(refs_by_identity) != set(records_by_identity)
                    or any(ref.digest_binding.digest not in (record.expected_digest, record.observed_digest) for identity_key, ref in refs_by_identity.items() for record in (records_by_identity[identity_key],))
                    or any(record.expected_digest is None and record.observed_digest is None for record in preprod_records)
                )
                if not canonical_material_invalid and item.target_run_id is not None and validated_preprod_refs:
                    canonical_target_refs = validated_preprod_refs
                target_case_id = submission.case_id
                target_unbound = not canonical_target_refs
        except F09ContractError:
            canonical_material_invalid = True
            target_unbound = True
            canonical_target_refs = ()
            record_anchor_ref = None

        case_match: MatchRequired = "UNKNOWN" if not submission.case_id or target_case_id is None else "MATCH" if submission.case_id == target_case_id else "MISMATCH"
        source_track_resolved = submission.track_source_binding.state == "AVAILABLE_RESOLVED"
        target_track_resolved = target_track_source_binding.state == "AVAILABLE_RESOLVED"
        track_match: MatchRequired = "UNKNOWN" if not source_track_resolved or not target_track_resolved else "MATCH" if submission.track == target_track_source_binding.track else "MISMATCH"
        run_match: MatchOptional = "NOT_APPLICABLE" if binding_protocol == "PRODUCTION_STATEMENT" else "UNKNOWN" if not item.target_run_id else "MATCH" if canonical_target_refs else "MISMATCH"
        statement_match: MatchOptional = "NOT_APPLICABLE" if binding_protocol == "PREPROD_RUN_TARGET" else "UNKNOWN" if not item.target_statement_id else "MATCH" if resolved_statement is not None else "MISMATCH"
        revision_match: MatchOptional = "NOT_APPLICABLE" if binding_protocol == "PREPROD_RUN_TARGET" else "UNKNOWN" if not item.target_statement_revision_id else "MATCH" if resolved_statement is not None and item.target_statement_revision_id == resolved_statement.statement_revision_id else "MISMATCH"
        statement_set_match: MatchOptional = "NOT_APPLICABLE" if binding_protocol == "PREPROD_RUN_TARGET" else "UNKNOWN" if resolved_production_record is None or resolved_production_record.statement_set_id is None else "MATCH" if resolved_production_record.statement_set_id == statement_set.statement_set_id else "MISMATCH"
        target_records = production_records if binding_protocol == "PRODUCTION_STATEMENT" else preprod_records
        artifact_digest_match: MatchRequired = "UNKNOWN" if not target_records or any(record.observed_digest is None for record in target_records) else "MATCH" if all(record.expected_digest == record.observed_digest for record in target_records) else "MISMATCH"
        dimensions = (case_match, track_match, run_match, statement_match, revision_match, statement_set_match, artifact_digest_match)
        required_indexes = (0, 1, 3, 4, 5, 6) if binding_protocol == "PRODUCTION_STATEMENT" else (0, 1, 2, 6)
        allowed_na_indexes = (2,) if binding_protocol == "PRODUCTION_STATEMENT" else (3, 4, 5)
        required_match = all(dimensions[index] == "MATCH" for index in required_indexes)
        allowed_na = all(dimensions[index] == "NOT_APPLICABLE" for index in allowed_na_indexes)
        source_integrity_invalid = submission.track_source_binding.state == "INTEGRITY_FAILED" or target_track_source_binding.state == "INTEGRITY_FAILED" or item.integrity == "INVALID" or item.feedback_id != submission.feedback_id or canonical_material_invalid
        source_ambiguous = submission.track_source_binding.state == "AMBIGUOUS" or target_track_source_binding.state == "AMBIGUOUS" or item.integrity == "UNRESOLVED" or canonical_material_ambiguous
        # PI-230 first-match aggregation is literal: malformed/inconsistent canonical
        # material is INVALID before ambiguity, valid absence, or match aggregation.
        if source_integrity_invalid:
            status: Literal["BOUND", "UNBOUND", "AMBIGUOUS", "INVALID"] = "INVALID"
        elif source_ambiguous:
            status = "AMBIGUOUS"
        elif target_unbound or not required_match or not allowed_na:
            status = "UNBOUND"
        else:
            status = "BOUND"

        binding_issue: DetectedIssue | None = None
        if target_unbound:
            binding_issue = DetectedIssue(issue_code="FEEDBACK.TARGET_UNBOUND", field_path="/feedback_bindings/0")  # T25
        elif binding_protocol == "PRODUCTION_STATEMENT" and revision_match == "MISMATCH":
            binding_issue = DetectedIssue(issue_code="FEEDBACK.REVISION_MISMATCH", field_path="/feedback_bindings/0/revision_match")  # T26
        elif track_match == "MISMATCH":
            binding_issue = DetectedIssue(issue_code="FEEDBACK.TRACK_MISMATCH", field_path="/feedback_bindings/0/track_match")  # T29
        feedback_item_ref = VersionedObjectRef("FEEDBACK", item.feedback_item_id, None, "feedback-item-v1", None, DigestPresent("PRESENT", submission.content_digest), submission.source_snapshot_ref.source_locator_ids[0] if submission.source_snapshot_ref.source_locator_ids else None, submission.captured_at)
        source_track_binding_ref = VersionedObjectRef(
            "TRACK_SOURCE_BINDING",
            submission.track_source_binding.track_source_binding_id,
            None,
            submission.track_source_binding.schema_version,
            submission.track_source_binding.contract_version,
            DigestPresent("PRESENT", submission.track_source_binding.content_digest),
            submission.track_source_binding.source_evidence_ref.source_locator_id,
            submission.track_source_binding.captured_at,
        )
        target_object_refs = canonical_target_refs
        binding = FeedbackBinding(
            feedback_binding_id=submission.feedback_id + ":" + item.feedback_item_id,
            feedback_item_ref=feedback_item_ref,
            binding_protocol=binding_protocol,
            source_track_binding_ref=source_track_binding_ref,
            target_track_source_binding=target_track_source_binding,
            case_match=case_match,
            track_match=track_match,
            run_match=run_match,
            statement_match=statement_match,
            revision_match=revision_match,
            statement_set_match=statement_set_match,
            artifact_digest_match=artifact_digest_match,
            target_object_refs=target_object_refs,
            record_anchor_ref=record_anchor_ref,
            status=status,
            issue_ids=item.issue_ids,
            detected_issues=(() if binding_issue is None else (binding_issue,)),
        )
        validate_feedback_binding_record(binding)
        bindings = bindings + (binding,)
    return FeedbackOperationResult(
        operation_disposition=operation_disposition,
        source_identity_relation=source_identity_relation,
        prior_key=prior_key,
        current_key=current_key,
        prior_target_digest=prior_target_digest,
        current_target_digest=current_target_digest,
        bindings=bindings,
        overwrite_permitted=False,
        detected_issues=(),
    )


def validate_feedback_binding_record(binding: FeedbackBinding) -> None:
    if not isinstance(binding, FeedbackBinding):
        raise F09ContractError(
            issue_code="FEEDBACK.TARGET_UNBOUND",
            field_path="/feedback_bindings/0",
            diagnostic="feedback binding record has invalid shape",
        )
    required_values = (
        binding.feedback_binding_id,
        binding.feedback_item_ref,
        binding.binding_protocol,
        binding.source_track_binding_ref,
        binding.target_track_source_binding,
        binding.case_match,
        binding.track_match,
        binding.run_match,
        binding.statement_match,
        binding.revision_match,
        binding.statement_set_match,
        binding.artifact_digest_match,
        binding.status,
    )
    if (
        any(value is None or value == "" for value in required_values)
        or not isinstance(binding.target_object_refs, tuple)
        or not isinstance(binding.issue_ids, tuple)
        or not isinstance(binding.detected_issues, tuple)
    ):
        raise F09ContractError(
            issue_code="FEEDBACK.TARGET_UNBOUND",
            field_path="/feedback_bindings/0",
            diagnostic="feedback binding record is incomplete",
        )
    required_domain = {"MATCH", "MISMATCH", "UNKNOWN"}
    optional_domain = required_domain | {"NOT_APPLICABLE"}
    if (
        binding.binding_protocol not in (
            "PRODUCTION_STATEMENT", "PREPROD_RUN_TARGET"
        )
        or binding.status not in (
            "BOUND", "UNBOUND", "AMBIGUOUS", "INVALID"
        )
        or binding.case_match not in required_domain
        or binding.track_match not in required_domain
        or binding.artifact_digest_match not in required_domain
        or any(value not in optional_domain for value in (
            binding.run_match, binding.statement_match,
            binding.revision_match, binding.statement_set_match,
        ))
    ):
        raise F09ContractError(
            issue_code="FEEDBACK.TARGET_UNBOUND",
            field_path="/feedback_bindings/0",
            diagnostic="feedback binding has an illegal protocol, status, or match dimension",
        )
    if binding.binding_protocol == "PRODUCTION_STATEMENT" and len(binding.target_object_refs) not in (0, 3):
        raise F09ContractError(
            issue_code="FEEDBACK.TARGET_UNBOUND",
            field_path="/feedback_bindings/0",
            diagnostic="production binding graph must be empty or its complete canonical triple",
        )
    if binding.binding_protocol == "PREPROD_RUN_TARGET" and binding.status == "BOUND" and not binding.target_object_refs:
        raise F09ContractError(
            issue_code="FEEDBACK.TARGET_UNBOUND",
            field_path="/feedback_bindings/0",
            diagnostic="BOUND PREPROD requires a nonempty authority-valid extensible run-target graph",
        )
    expected_target_types = ("STATEMENT", "STATEMENT_SET", "STATEMENT_RECORDS")
    if binding.binding_protocol == "PRODUCTION_STATEMENT" and binding.target_object_refs and tuple(ref.object_type for ref in binding.target_object_refs) != expected_target_types:
        raise F09ContractError(
            issue_code="FEEDBACK.TARGET_UNBOUND",
            field_path="/feedback_bindings/0",
            diagnostic="production target graph has noncanonical target kinds",
        )
    if (
        binding.record_anchor_ref is not None
        and binding.record_anchor_ref.object_type != "RULE"
    ):
        raise F09ContractError(
            issue_code="FEEDBACK.TARGET_UNBOUND",
            field_path="/feedback_bindings/0",
            diagnostic="record anchor must be the canonical selected RULE anchor",
        )
    bound_dimensions = (
        ("MATCH", "MATCH", "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "MATCH")
        if binding.binding_protocol == "PRODUCTION_STATEMENT"
        else ("MATCH", "MATCH", "MATCH", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "MATCH")
    )
    actual_dimensions = (
        binding.case_match, binding.track_match, binding.run_match,
        binding.statement_match, binding.revision_match,
        binding.statement_set_match, binding.artifact_digest_match,
    )
    anchor_coherent = (
        binding.record_anchor_ref is not None
        and binding.record_anchor_ref.object_type == "RULE"
        if binding.binding_protocol == "PRODUCTION_STATEMENT"
        else binding.record_anchor_ref is None
    )
    target_graph_coherent = (
        tuple(ref.object_type for ref in binding.target_object_refs) == expected_target_types
        if binding.binding_protocol == "PRODUCTION_STATEMENT"
        else bool(binding.target_object_refs)
    )
    if binding.status == "BOUND" and (
        actual_dimensions != bound_dimensions
        or not target_graph_coherent
        or not anchor_coherent
    ):
        raise F09ContractError(
            issue_code="FEEDBACK.TARGET_UNBOUND",
            field_path="/feedback_bindings/0",
            diagnostic=(
                "BOUND requires protocol-exact seven dimensions, the complete protocol-specific "
                "target graph, and a RULE anchor only for PRODUCTION_STATEMENT"
            ),
        )


def evaluate_learning_eligibility(
    binding: FeedbackBinding,
    *,
    policy_id: str,
    policy_version: str,
    evaluated_at: str,
) -> LearningEligibility:
    if (
        not isinstance(binding, FeedbackBinding)
        or not binding.feedback_binding_id
        or policy_id != "PRODUCTION-STATEMENT-ELIGIBILITY"
        or policy_version != "policy-v1"
        or not evaluated_at
    ):
        raise F09ContractError(
            issue_code="FEEDBACK.TARGET_UNBOUND",
            field_path="/feedback_bindings/0",
            diagnostic="learning eligibility prerequisite has invalid shape",
        )
    if binding.status == "BOUND" and binding.binding_protocol == "PRODUCTION_STATEMENT" and binding.track_match == "MATCH" and binding.record_anchor_ref is not None and binding.record_anchor_ref.object_type == "RULE" and len(binding.target_object_refs) == 3:
        eligibility_status: Literal["ELIGIBLE", "INELIGIBLE", "HUMAN_REVIEW"] = "ELIGIBLE"
        learning_target_refs = (binding.record_anchor_ref,)
        blocking_reason_codes: tuple[str, ...] = ()
    elif binding.status in ("AMBIGUOUS", "INVALID") or binding.track_match == "UNKNOWN":
        eligibility_status = "HUMAN_REVIEW"
        learning_target_refs = ()
        blocking_reason_codes = ("FEEDBACK_BINDING_REQUIRES_REVIEW",)
    else:
        eligibility_status = "INELIGIBLE"
        learning_target_refs = ()
        blocking_reason_codes = ("FEEDBACK_BINDING_NOT_BOUND",)
    eligibility = LearningEligibility(
        eligibility_id=binding.feedback_binding_id + ":" + policy_id + ":" + policy_version,
        feedback_binding_id=binding.feedback_binding_id,
        policy_id=policy_id,
        policy_version=policy_version,
        status=eligibility_status,
        learning_target_refs=learning_target_refs,
        excluded_supporting_rule_refs=(),
        blocking_reason_codes=blocking_reason_codes,
        detected_issues=(),
        evaluated_at=evaluated_at,
    )
    validate_learning_eligibility(eligibility)
    return eligibility
def validate_learning_eligibility(eligibility: LearningEligibility) -> None:
    if (
        not isinstance(eligibility, LearningEligibility)
        or not eligibility.eligibility_id
        or not eligibility.feedback_binding_id
        or eligibility.policy_id != "PRODUCTION-STATEMENT-ELIGIBILITY"
        or eligibility.policy_version != "policy-v1"
        or not eligibility.evaluated_at
        or not isinstance(eligibility.learning_target_refs, tuple)
        or not isinstance(eligibility.excluded_supporting_rule_refs, tuple)
        or not isinstance(eligibility.blocking_reason_codes, tuple)
        or not isinstance(eligibility.detected_issues, tuple)
    ):
        raise F09ContractError(
            issue_code="FEEDBACK.TARGET_UNBOUND",
            field_path="/feedback_bindings/0",
            diagnostic="learning eligibility record is incomplete",
        )
    if eligibility.status not in (
        "ELIGIBLE", "INELIGIBLE", "HUMAN_REVIEW"
    ):
        raise F09ContractError(
            issue_code="FEEDBACK.TARGET_UNBOUND",
            field_path="/feedback_bindings/0",
            diagnostic="learning eligibility status is outside the closed domain",
        )
    if eligibility.status == "ELIGIBLE" and (
        len(eligibility.learning_target_refs) != 1
        or eligibility.learning_target_refs[0].object_type != "RULE"
        or eligibility.blocking_reason_codes
    ):
        raise F09ContractError(
            issue_code="FEEDBACK.TARGET_UNBOUND",
            field_path="/feedback_bindings/0",
            diagnostic="ELIGIBLE must target exactly the canonical selected RULE anchor",
        )
    if eligibility.status != "ELIGIBLE" and (
        eligibility.learning_target_refs
        or not eligibility.blocking_reason_codes
    ):
        raise F09ContractError(
            issue_code="FEEDBACK.TARGET_UNBOUND",
            field_path="/feedback_bindings/0",
            diagnostic="non-eligible record requires reasons and cannot expose learning targets",
        )
```

T53 production `BOUND` and T54 `ELIGIBLE` are explicit no-issue constructions using the canonical selected `RULE` anchor. PREPROD `BOUND` is a separate run-only construction using the canonical `RUN_SNAPSHOT`/`DECISION_RUN`/`FEEDBACK_ATTACHMENT` graph and no statement or rule anchor. T58 compares explicit prior/current canonical feedback keys: changed source digest changes canonical identity and returns an observable `NEW_OPERATION` result with `source_identity_relation=CHANGED`, retained prior/current keys and digests, `overwrite_permitted=False`, and no mismatch issue; exact same key plus different target digest alone returns `TARGET_MISMATCH` with the canonical pair. A source digest is never compared with the whole-submission `content_digest`. Before aggregation, malformed or inconsistent canonical ref/record/selection material sets the invalid prerequisite fact; absent but structurally valid protocol targets set unbound, and multiple valid candidates set ambiguous. The two displayed validators fail closed on shape, closed-domain, protocol-specific cardinality, target-kind, RULE-anchor, or status-coherence defects. A fresh eligibility evaluation never copies `binding.detected_issues`, `issue_ids`, status, dimensions, or reason codes into a pair. The phase-owned binder detections are selected only by their canonical facts and each has one exact returned constructor; no ellipsis, future helper, fixture label, expected value, or status-to-pair oracle remains.

- Module must not import `tools.feedback_ingest`, `minimal_learning_loop`, weight repositories, rule writers or iteration triggers.

- [ ] **Step 1: Write RED binding tests.** Exact statement/revision/set/case/track/artifact digest/records anchor is BOUND; unknown ID, UNMAPPED anchor, old revision, mixed revision, cross-track, stale manifest and digest mismatch are not learnable. Use literal protocol cases to prove first-match aggregation: `PRODUCTION_STATEMENT` with allowed `run_match=NOT_APPLICABLE` remains BOUND, the same protocol with required `statement_match=NOT_APPLICABLE` is UNBOUND, `PREPROD_RUN_TARGET` with required run MATCH and allowed statement/revision/statement-set `NOT_APPLICABLE` remains BOUND, and the same protocol with required `run_match=NOT_APPLICABLE` is UNBOUND. Do not add a fifth status or change any dimension value.
- [ ] **Step 2: Write RED identity tests.** Source digest, item set, item target revision or policy version changes canonical operation identity; duplicate conflicting feedback never last-write-wins.
- [ ] **Step 3: Write RED no-side-effect test.** Snapshot filesystem before/after eligibility and monkeypatch existing learning functions to raise if called; result must be computed without writes/calls.
- [ ] **Step 4: Verify RED.** `python -m pytest tests/f09/test_feedback_eligibility.py -q`; expected missing-module FAIL.
- [ ] **Step 5: Implement strict binder/evaluator.** Preserve invalid submissions and issues as returned immutable objects; `validate_feedback_binding_record()` checks all required fields, the seven closed match dimensions, anchor/status coherence and target-ref cardinality; `validate_learning_eligibility()` checks every required field plus status/targets/reasons coherence. The binder calls the binding-record validator before returning, and the evaluator calls the eligibility validator before returning. Do not fan out to legacy rule IDs and do not call learning.
- [ ] **Step 6: Verify GREEN.** Repeat Step 4; expected PASS.
- [ ] **Step 7: Regression.** `python -m pytest tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_h3_standard_list_schema_without_rule_ids_is_blocked_from_learning tests/v1_3_acceptance/test_h3_feedback_parsing.py::test_ingest_includes_v5_feedback_attachment_summary_without_unblocking_learning tests/test_phase_a_minimal_learning_loop.py::test_statement_record_enforcement_marks_missing_as_unmapped -q`; expected `3 passed`.
- [ ] **Step 8: Commit.** `git add engine/f09/feedback.py tests/f09/test_feedback_eligibility.py && git commit -m "feat(f09): bind feedback without executing learning"`.
- [ ] **Independent review gate.** Reviewer performs import-graph scan and filesystem diff; eligibility must have zero learning side effects, cross-track attachments remain audit-only, every returned negative binding/eligibility record requiring a PI-300 issue carries an exact producer-owned `detected_issues` pair, and adapters contain no status/dimension/reason-to-pair mapping.
- [ ] **Rollback.** `git revert --no-edit HEAD`; feedback audit records are retained, never rewritten or deleted.

## Task 9: Explicit Opt-In Application Orchestrator and Observability

**Files:**
- Create: `engine/f09/application.py`
- Create: `engine/f09/__init__.py`
- Create: `tests/f09/test_application_opt_in.py`
- Create: `tests/f09/test_production_isolation.py`

**Interfaces:**
```python
@dataclass(frozen=True)
class F09RunRequest: case_id: str; mode: Literal["STAGED_AUDIT", "PREPROD_SHADOW", "PRODUCTION_DEFAULT"]; enable_f09: bool = False; markdown_path: Path = Path("engine/contracts/12-real-world-function-evidence-cards-v1.md"); snapshot_path: Path = Path("plans/production-implementation-pi-300-f09-source-snapshots-v1.json"); artifact_root: Path | None = None; now: str = ""
@dataclass(frozen=True)
class F09Observation: event: str; case_id: str; mode: str; phase: str; status: str; issue_codes: tuple[str, ...]; artifact_set_state: str | None
@dataclass(frozen=True)
class F09RunResult: request: F09RunRequest; evidence: NormalizedEvidencePackage | None; decision: DecisionEvaluationResult | None; trace: TraceEnvelope | None; statement_set: StatementSet | None; manifest: ArtifactSetManifest | None; observations: tuple[F09Observation, ...]; stopped_at: str | None
def run_f09_slice(request: F09RunRequest, *, gate_inputs: tuple[GateEvaluationInput, ...], competition_input: CompetitionInput, root_input: RootInput, timing_input: TimingInput) -> F09RunResult
```

- [ ] **Step 1: Write RED opt-in tests.** `enable_f09=False`, missing artifact root, unknown mode and `PRODUCTION_DEFAULT` stop before source read/write. Only explicit application request mode `STAGED_AUDIT`/`PREPROD_SHADOW` may run; assert their exact canonical outputs are respectively `RunTrack.STAGED_L6`/`RunTrack.V5_V6_PREPROD` in evidence, trace, statement set, artifact and feedback typed fields, and assert no request-mode token appears in any canonical track field.
- [ ] **Step 2: Write RED stop-condition tests.** Stop after source, evidence, decision, trace or artifact failure; later phases remain None; observations contain phase/status/issue codes but no source prose or internal statement IDs.
- [ ] **Step 3: Write RED isolation tests.** AST/import checks prove `engine/f09` is not imported by pipeline runner, ports, production service, default adapters, renderer or feedback ingest. Assert existing signatures/dataclass fields and default registry digests remain unchanged.
- [ ] **Step 4: Verify RED.** `python -m pytest tests/f09/test_application_opt_in.py tests/f09/test_production_isolation.py -q`; expected missing-module/export FAIL.
- [ ] **Step 5: Implement orchestrator.** Validate opt-in before any I/O. Apply the only static mapping table `{STAGED_AUDIT: RunTrack.STAGED_L6, PREPROD_SHADOW: RunTrack.V5_V6_PREPROD}` exactly once at the opt-in boundary; `PRODUCTION_DEFAULT` is a rejected request mode, not a route to `RunTrack.PRODUCTION_DEFAULT`. Pass only the mapped canonical `RunTrack` through evidence, trace, artifact and feedback phases; call each phase sequentially; catch only typed F09 errors into fail-closed observations; unexpected exceptions propagate in tests rather than silently downgrade.
- [ ] **Step 6: Verify GREEN.** Repeat Step 4; expected PASS.
- [ ] **Step 7: Regression.** `python -m pytest tests/test_production_entrypoints_unchanged.py tests/ziping_career/test_production_isolation.py tests/application/test_staged_parallel_runner.py tests/test_error_policy.py::test_ep004_production_service_strict_render_failure_marks_job_failed -q`; expected PASS.
- [ ] **Step 8: Commit.** `git add engine/f09/__init__.py engine/f09/application.py tests/f09/test_application_opt_in.py tests/f09/test_production_isolation.py && git commit -m "feat(f09): add isolated opt-in slice orchestrator"`.
- [ ] **Independent review gate.** Reviewer imports the normal production entrypoints in a clean process, confirms `engine.f09` is absent from `sys.modules`, runs default production tests, and confirms disabled requests perform zero reads/writes.
- [ ] **Rollback.** `git revert --no-edit HEAD`; because no production hook exists, rollback is code-only and production-default remains unaffected.

## Task 10: T01–T104 Vertical Acceptance Matrix — Tests Only

**Files (closed write set):**
- Create: `tests/f09/test_f09_vertical_matrix.py`
- Create: `tests/f09/test_f09_adapter_reachability.py`
- Modify: `tests/f09/conftest.py`
- Optional scenario data only: `tests/f09/data/f09_vertical_scenarios.py`

Task 10 may modify only tests, fixtures and scenario data. It must not modify `engine/f09/`, validators, production code, default configuration, or frozen sources. If a scenario exposes an implementation gap, stop Task 10 and return the defect to the owning preceding Task; if ownership is not already bounded, create a separate authorized implementation task. Test assertions may not be weakened to fit current behavior.

**Non-copy ownership index:** This subsection is descriptive only and contains no executable declaration. The sole copy source for `VerticalScenario`, `ScenarioExecution`, `execute_scenario`, baselines, adapters and all 104 mutators is the one continuous `tests/f09/conftest.py` module block under “Concrete frozen fixture graph and literal mutator bodies”. The sole copy source for the parameterized harness and its five assertion helpers is the one continuous `tests/f09/test_f09_vertical_matrix.py` module block after the scenario-data module. The scenario-data module alone owns the 104 literal constructors and `SCENARIOS`; `conftest.py` never imports scenario-data. Pytest initializes `conftest.py` first, the test module then imports the already-bound conftest symbols and finally imports `SCENARIOS`, so scenario-data's explicit reverse imports do not depend on a partially initialized conftest or a circular-import assumption.

The sole executable listings below fix the exact structure: all 104 constructors are literal, occur once in executable data, and their `pytest_node` values are complete literal nodes. Future collection evidence may use `python -m pytest --collect-only tests/f09/test_f09_vertical_matrix.py -q`; this planning remediation does not claim any node is currently collectable.

- [ ] **Step 1: Write matrix continuity RED test.** Read literal `SCENARIOS`; assert length 104, IDs exactly T01 through T104, no duplicate, every row has explicit purpose/mutation/state/issue/basis/binding/side-effect/node values, and node suffix equals its literal ID. AST-parse `tests/f09/conftest.py`; require exactly 104 top-level `mutate_tNN` definitions, T01 identity return, explicit nested frozen replacements in T02–T104, and reject symbol-reference-only coverage or any prohibited dynamic construct. AST-parse the sole vertical-matrix module and require every distinct literal in `expected_gate_or_state`, `basis_assertions`, `binding_assertions`, and `side_effect_assertion` to occur in the corresponding helper's explicit `match` alternatives; each helper must have exactly one fail-closed `case _` that raises `AssertionError`, and no expectation field may be consumed only by non-emptiness, heterogeneous membership, `eval`, `getattr`, registry, factory, table parser, wildcard dispatch, or a shared success default.
- [ ] **Step 2: Add parameterized RED vertical test.** Use the literal parameter structure above. Every case asserts action/state, issue code and path (or explicit no-issue expectation), basis, bindings and forbidden side effects. Each literal expectation branch must name its canonical typed field/value surface; the explicit no-issue branch must prove observation, decision/action-validation, trace, statement, artifact-record, feedback-binding, eligibility-reason, and all three phase-error surfaces empty.
- [ ] **Step 3: Verify RED.** Future implementation run: `python -m pytest tests/f09/test_f09_vertical_matrix.py -q`; expected failure identifies missing production behavior, not permission to edit it in Task 10.
- [ ] **Step 4: Resolve gaps outside Task 10.** Return each implementation gap to Task 1–9 owner or a new separately bounded implementation task; after that task is independently reviewed, resume Task 10 with tests/fixtures/scenario data only.
- [ ] **Step 5: Verify GREEN.** Future implementation run: `python -m pytest tests/f09/test_f09_vertical_matrix.py -q`; expected 105 passes only after the implementation-owning task is accepted.
- [ ] **Step 6: Run full F09 regression.** Future implementation run: `python -m pytest tests/f09 -q`.
- [ ] **Step 7: Run one deterministic related repository regression.** From the repository root in Windows `cmd.exe`, run exactly `python -m pytest tests/test_production_entrypoints_unchanged.py tests/ziping_career/test_production_isolation.py tests/application/test_staged_parallel_runner.py tests/test_error_policy.py::test_ep004_production_service_strict_render_failure_marks_job_failed -q`; Task 10 contributes no production correction.
- [ ] **Step 8: Commit.** `git add tests/f09/test_f09_vertical_matrix.py tests/f09/test_f09_adapter_reachability.py tests/f09/conftest.py tests/f09/data/f09_vertical_scenarios.py && git diff --cached --name-only`; abort unless every staged path is under `tests/f09/`, then commit `git commit -m "test(f09): cover T01 through T104 vertical matrix"`.
- [ ] **Independent review gate.** Fresh reviewer rejects any Task 10 diff outside `tests/f09/`, compares all 104 literal rows and all 104 concrete bodies against PI-300, verifies no duplicate/missing function, constructor, node, or tuple ID, confirms every non-baseline body names explicit field paths and literal values, verifies `execute_scenario()` passes all four production inputs explicitly with no nonexistent `decision_inputs` field or `**` expansion, and verifies the unconditional calls to all three named post-run phase consumers plus the leaf-to-port table below before any collect-only or executable test. The reviewer also performs a literal-token closure comparison for all four expectation fields against the four explicit helper dispatches, verifies every token reaches a named canonical typed field/value assertion, verifies unknown tokens raise immediately, and verifies no-issue rows exhaust every issue/error surface rather than returning early. A consumer that merely compares a fixture field with an expectation, rather than using it to construct or alter the concrete Task 6–8 call input, is a dead switch and fails review.
- [ ] **Rollback.** `git revert --no-edit HEAD`; because the commit is tests-only, no validator/production rollback is permitted or necessary.

---

## Literal T01–T104 Executable Scenario Definitions

The markers delimit the only table used for exactly-once static counting. Every row is one literal `VerticalScenario` definition source; no range, ellipsis, dynamic ID builder, or inferred expectation may replace a row. `none` is an explicit expectation of no issue. All nodes are future intended pytest nodes, not present collection evidence.

<!-- PI-570-R1-SCENARIOS-BEGIN -->
| ID | PI-300 row/purpose | Mutation/input delta | Expected action/gate/state | Expected issue code @ path | Basis assertions | Binding assertions | Side-effect assertion | Unique pytest node |
|---|---|---|---|---|---|---|---|---|
| T01 | OUTPUT 正常路径 | 完整全门/参与/竞争/root/timing | OUTPUT | none | nonempty; exact local records | declarations exact | staged writes only | `test_f09_vertical_matrix[T01]` |
| T02 | CONDITIONAL 单轴 | allocation 成立，risk 不补强 | CONDITIONAL | `ISSUE-RISK-UNKNOWN @ gate/RISK` | condition refs; six gates | risk UNKNOWN binding exact | no production/learning | `test_f09_vertical_matrix[T02]` |
| T03 | ASK 缺归属事实 | attribution=MISSING | ASK | `GATE.FIELD_MISSING @ gate/ATTRIBUTION` | question→issue→path→resume | missing path bound | no conclusion write | `test_f09_vertical_matrix[T03]` |
| T04 | ABSTAIN 竞争未解 | F08/F09 competition unresolved | ABSTAIN | `COMPETITION.UNRESOLVED @ competition/F09` | both candidate evidence retained | F08 reference-only | no formal outcome | `test_f09_vertical_matrix[T04]` |
| T05 | HUMAN_REVIEW 来源解释冲突 | evaluator conflict requiring review | HUMAN_REVIEW | `GATE.FIELD_CONFLICT @ gate/ATTRIBUTION` | both sides; review scope | conflict refs exact | no auto learning | `test_f09_vertical_matrix[T05]` |
| T06 | explicit null | output precision value=null | binding RESOLVED | none | declaration ref nonempty | RESOLVED ref exact | no inferred precision | `test_f09_vertical_matrix[T06]` |
| T07 | null + unresolved | precision null and unresolved | BOTH_NULL_AND_UNRESOLVED | `DECLARATION.VALUE_UNRESOLVED @ declarations/output_precision/value` | value/presence separate | RESOLVED ref retained | no fallback | `test_f09_vertical_matrix[T07]` |
| T08 | absent 负例 | synthetic declaration field absent | ABSENT/invalid | `DECLARATION.NOT_PRESENT @ declarations/output_precision` | no borrowed basis | ABSENT reason exact | frozen source unchanged | `test_f09_vertical_matrix[T08]` |
| T09 | evaluator unknown | risk input exists but unevaluable | safe action | `GATE.STATE_UNKNOWN @ gate/RISK` | unknown path retained | unknown record digest exact | UNKNOWN not action | `test_f09_vertical_matrix[T09]` |
| T10 | source unavailable | locator unreadable | blocking | `SOURCE.UNAVAILABLE @ records/source_locator` | no satisfied gate basis | UNAVAILABLE issues nonempty | no artifacts | `test_f09_vertical_matrix[T10]` |
| T11 | declaration unresolvable | attempted ref digest/version drift | UNRESOLVABLE | `DECLARATION.DIGEST_MISMATCH @ declarations/attempted_ref` | attempted ref retained | UNRESOLVABLE exact branch | no statement | `test_f09_vertical_matrix[T11]` |
| T12 | invalid N/A | required F09 declaration forged N/A | invalid | `DECLARATION.NOT_APPLICABLE_INVALID @ declarations/output_precision` | no action basis | N/A reason visible | no conclusion write | `test_f09_vertical_matrix[T12]` |
| T13 | 理论冒充事实 | CHART_STRUCTURE only for reality | gate MISSING | `EVIDENCE.TRACK_INVALID @ gate/reality` | chart refs retained only | track binding exact | no promotion | `test_f09_vertical_matrix[T13]` |
| T14 | hypothesis 冒充事实 | unverified narrative only | gate MISSING | `EVIDENCE.TRACK_INVALID @ gate/reality` | hypothesis refs retained | track binding exact | no promotion | `test_f09_vertical_matrix[T14]` |
| T15 | 竞争冲突 | F08 duty and F09 capital both strong | conflict/unresolved | `COMPETITION.UNRESOLVED @ competition/F09` | both evidence sets | F08 identity-only | no second card | `test_f09_vertical_matrix[T15]` |
| T16 | 后果反填 | profit/loss/debt only | gate MISSING | `GATE.FIELD_MISSING @ gate/ALLOCATION` | consequence excluded from gate basis | source refs retained | no backfill | `test_f09_vertical_matrix[T16]` |
| T17 | 根源/应期改写攻击 | timing substitute mutates root R1 | invalid | `ROOT_TIMING.REWRITE_INVALID @ root_timing_checks/0` | root/timing ledgers separate | both ledger refs exact | no decision write | `test_f09_vertical_matrix[T17]` |
| T18 | validation/precision 串线 | T0/T1/T2 placed in precision | invalid | `DECLARATION.IDENTITY_MISMATCH @ declarations/output_precision` | declaration refs separate | type/ID/path exact | no guessing | `test_f09_vertical_matrix[T18]` |
| T19 | decision→statement binding 漂移 | mutate branch/digest in statement | statement invalid | `TRACE.BINDING_MISMATCH @ statements/0/output_precision_binding` | action basis unchanged | both declarations exact | no publish | `test_f09_vertical_matrix[T19]` |
| T20 | 多规则 records 投影 | statement has three rule refs | LOSSY | `PROJECTION.LOSSY @ transformations/records` | one anchor + two dropped refs | source refs reachable | no learning-ready | `test_f09_vertical_matrix[T20]` |
| T21 | report 成功、records 失败 | inject records write failure | PARTIAL | `ARTIFACT.WRITE_FAILED @ artifacts/STATEMENT_RECORDS` | input snapshot refs logged | attempt ledger complete | no feedback readiness | `test_f09_vertical_matrix[T21]` |
| T22 | records 成功、index 失败 | inject index write failure | PARTIAL | `ARTIFACT.WRITE_FAILED @ artifacts/STATEMENT_INDEX` | prior records retained | attempt ledger complete | no rollback overwrite | `test_f09_vertical_matrix[T22]` |
| T23 | 新 records + 旧 index | stale revision index | STALE_MIXED_REVISION | `ARTIFACT.STALE_REVISION @ artifacts/STATEMENT_INDEX` | current/old refs visible | revisions exact | no feedback readiness | `test_f09_vertical_matrix[T23]` |
| T24 | digest mismatch | same key/different digest | DIGEST_MISMATCH | `ARTIFACT.DIGEST_MISMATCH @ artifacts/observed_digest` | original inputs retained | expected/observed separate | no overwrite | `test_f09_vertical_matrix[T24]` |
| T25 | unknown feedback mapping | unknown statement or anchor | UNBOUND/INELIGIBLE | `FEEDBACK.TARGET_UNBOUND @ feedback_bindings/0` | zero learning targets | seven dimensions explicit | learning calls=0 | `test_f09_vertical_matrix[T25]` |
| T26 | revision mismatch | target old revision | INVALID/INELIGIBLE | `FEEDBACK.REVISION_MISMATCH @ feedback_bindings/0/revision_match` | old target ref retained | revision=MISMATCH | no fuzzy match | `test_f09_vertical_matrix[T26]` |
| T27 | duplicate same payload | same idempotency key/digest retry | no-op success | none | same snapshots | same canonical key | no duplicate | `test_f09_vertical_matrix[T27]` |
| T28 | duplicate conflicting payload | same key/different digest | conflict | `IDEMPOTENCY.DIGEST_MISMATCH @ canonical_key_digest` | both attempt refs | digests separate | no overwrite/learning | `test_f09_vertical_matrix[T28]` |
| T29 | preprod 跨轨输入 | preprod attachment to production | INVALID/audit-only | `FEEDBACK.TRACK_MISMATCH @ feedback_bindings/0/track_match` | audit refs only | track=MISMATCH | no production learning | `test_f09_vertical_matrix[T29]` |
| T30 | card identity 误宣称 | capability changed to implemented | invalid | `CARD.IDENTITY_INVALID @ card_identity_refs/0/runtime_capability_status` | card ref retained | reference-only literal | no publish | `test_f09_vertical_matrix[T30]` |
| T31 | F08 identity-only 正例 | only CAND-F09; F08 in refs | consumable | none | F09 disposition only | F08 ref reachable | no F08 execution | `test_f09_vertical_matrix[T31]` |
| T32 | 伪造 F08 candidate | inject F08 candidate/action/statement | invalid | `COMPETITION.CANDIDATE_INVALID @ competition/candidate_ids` | forged object retained for issue | F08 reference-only | no silent deletion | `test_f09_vertical_matrix[T32]` |
| T33 | singleton 被实现拒绝 | validator demands two candidates | BLOCKED contract mismatch | `CONTRACT.CARDINALITY_MISMATCH @ competition/candidate_ids` | singleton basis retained | contract ref exact | no F08 repair | `test_f09_vertical_matrix[T33]` |
| T34 | validation ref 完整正例 | all six identity fields | RESOLVED | none | ref nonempty | field path only in locator | no inference | `test_f09_vertical_matrix[T34]` |
| T35 | precision ref 完整正例 | six fields; null+unresolved | RESOLVED | `DECLARATION.VALUE_UNRESOLVED @ declarations/output_precision/value` | ref nonempty | RESOLVED identity exact | no precision expansion | `test_f09_vertical_matrix[T35]` |
| T36 | declaration identity 缺字段 | delete identity field/path substitution | invalid | `DECLARATION.IDENTITY_MISMATCH @ declarations/ref` | attempted ref visible | no guessed match | no output | `test_f09_vertical_matrix[T36]` |
| T37 | cross-layer declaration drift | mutate one ref identity field | trace/statement invalid | `TRACE.BINDING_MISMATCH @ trace/declarations` | decision basis stable | both refs field-equal | no publish | `test_f09_vertical_matrix[T37]` |
| T38 | OUTPUT payload contract | complete output + basis | OUTPUT valid | none | nonempty exact basis | action/payload discriminator | staged only | `test_f09_vertical_matrix[T38]` |
| T39 | CONDITIONAL payload contract | complete condition/issues/scope | CONDITIONAL valid | `ISSUE-RISK-UNKNOWN @ action/payload/unresolved_issue_ids` | issue refs preserved | exact payload branch | no hidden resolution | `test_f09_vertical_matrix[T39]` |
| T40 | ASK payload contract | question/issue/path/resume | ASK valid | `GATE.FIELD_MISSING @ action/payload/question_requests/0` | nonempty original refs | exact ASK branch | no outcome | `test_f09_vertical_matrix[T40]` |
| T41 | ABSTAIN payload contract | candidates/issues/scope | ABSTAIN valid | `COMPETITION.UNRESOLVED @ action/payload` | blocking basis | exact ABSTAIN branch | no OUTPUT payload | `test_f09_vertical_matrix[T41]` |
| T42 | HUMAN_REVIEW payload contract | case/issues/records/scope | HUMAN_REVIEW valid | `GATE.FIELD_CONFLICT @ action/payload` | both conflict sides | exact review branch | no priority | `test_f09_vertical_matrix[T42]` |
| T43 | payload 判别错配 | ASK with output or multiple payloads | invalid | `ACTION.PAYLOAD_MISMATCH @ action_envelope` | basis retained for issue | exactly-one violated | no write | `test_f09_vertical_matrix[T43]` |
| T44 | StatementSet 必需字段 | delete each required set field | invalid | `STATEMENT.SET_INVALID @ statement_set` | trace ref required | source/version refs exact | no publish | `test_f09_vertical_matrix[T44]` |
| T45 | StandardStatement 必需字段 | delete each required statement field | invalid | `STATEMENT.RECORD_INVALID @ statements/0` | complete BasisRecordIds | declarations/revision exact | no publish | `test_f09_vertical_matrix[T45]` |
| T46 | 六 participation 完整正例 | one complete record per role | READY structure | none | six independent IDs | role refs exact | READY not SATISFIED | `test_f09_vertical_matrix[T46]` |
| T47 | participation 补偿攻击 | delete SOURCE; borrow REALITY evidence | invalid | `PARTICIPATION.ROLE_CARDINALITY_INVALID @ participation/roles` | no cross-role basis | missing role explicit | no repair | `test_f09_vertical_matrix[T47]` |
| T48 | participation fail-safe | state/evidence/issue/decision mismatch | invalid | `PARTICIPATION.PATH_INVALID @ participation/records` | each role closes path | source decision exact | no decision | `test_f09_vertical_matrix[T48]` |
| T49 | root ledger 完整正例 | complete root entry | valid | none | chart evidence only | root refs exact | timing cannot mutate | `test_f09_vertical_matrix[T49]` |
| T50 | timing ledger 完整正例 | complete timing entry | valid | none | timing evidence local | timing refs exact | root unchanged | `test_f09_vertical_matrix[T50]` |
| T51 | root/timing fail-safe | violated/unknown missing path/reason | invalid | `ROOT_TIMING.CHECK_INVALID @ root_timing_checks/0` | both ledgers referenced | source decision exact | no rewrite | `test_f09_vertical_matrix[T51]` |
| T52 | FeedbackSubmission/Item 全字段 | complete canonical submission/items | valid | none | item targets explicit | source ref/digests exact | no learning | `test_f09_vertical_matrix[T52]` |
| T53 | FeedbackBinding 全字段 | seven matches/targets/anchor/status/issues | BOUND or canonical failure | none | target refs explicit | seven dimensions exact | no local status | `test_f09_vertical_matrix[T53]` |
| T54 | LearningEligibility 全字段 | policy/targets/exclusions/reasons/time | canonical three-state | none | learning/excluded refs explicit | binding ID exact | evaluation only | `test_f09_vertical_matrix[T54]` |
| T55 | feedback revision 幂等变化 | only revision changes | key changes | none | revised target in input | revision identity included | no old-key reuse | `test_f09_vertical_matrix[T55]` |
| T56 | eligibility policy 幂等变化 | only policy version changes | key changes | none | same target refs | policy identity included | reevaluate only | `test_f09_vertical_matrix[T56]` |
| T57 | feedback item 集合变化 | add/remove canonical item | key changes | none | full item set included | item IDs canonicalized | no duplicate | `test_f09_vertical_matrix[T57]` |
| T58 | feedback source digest 变化 | same feedback ID/new source digest | NEW_OPERATION/changed identity | none | prior/current source refs and canonical keys retained | digest identity included and producer receipt asserted | no last-write-wins | `test_f09_vertical_matrix[T58]` |
| T59 | basis record type 正例 | exact six gates/local PR/competition/RTC | valid | none | three layers same ordered IDs | records resolve in result | no cross-result lookup | `test_f09_vertical_matrix[T59]` |
| T60 | wrong participation basis type | replace PR with set container | invalid | `BASIS.RECORD_TYPE_INVALID @ action/basis/participation_record_ids` | bad ID retained in issue | no container coercion | fail closed | `test_f09_vertical_matrix[T60]` |
| T61 | OUTPUT disposition 唯一解析 | one F09 INCLUDED disposition | OUTPUT valid | none | exact candidate basis | unique disposition ref | no fallback | `test_f09_vertical_matrix[T61]` |
| T62 | dangling disposition ref | CAND-NOT-IN-SET | invalid | `DISPOSITION.REFERENCE_DANGLING @ action/disposition_refs` | bad ref explicit | current-result scope | no guessing | `test_f09_vertical_matrix[T62]` |
| T63 | zero disposition matches | F09 ref but no disposition | invalid | `DISPOSITION.MATCH_COUNT_INVALID @ competition/dispositions` | zero match asserted | current result only | no repair | `test_f09_vertical_matrix[T63]` |
| T64 | multiple disposition matches | duplicate F09 dispositions | invalid | `DISPOSITION.MATCH_COUNT_INVALID @ competition/dispositions` | both records retained | uniqueness violated | no first-wins | `test_f09_vertical_matrix[T64]` |
| T65 | disposition/action incompatible | wrong disposition for action | invalid | `DISPOSITION.ACTION_INCOMPATIBLE @ action/selected_action` | disposition basis retained | action mapping exact | no downgrade | `test_f09_vertical_matrix[T65]` |
| T66 | CONDITIONAL disposition unique | one F09 CONDITIONAL | CONDITIONAL valid | none | condition/issues retained | unique disposition ref | no fallback | `test_f09_vertical_matrix[T66]` |
| T67 | artifact 八状态正例 | construct each canonical item state | valid | none | attempts appropriate per state | exact eight-value enum | no readiness inference | `test_f09_vertical_matrix[T67]` |
| T68 | illegal NOT_STARTED | item state old local value | invalid | `ARTIFACT.STATE_INVALID @ artifacts/0/state` | artifact ref retained | no enum coercion | no write | `test_f09_vertical_matrix[T68]` |
| T69 | illegal WRITTEN | item state old local value | invalid | `ARTIFACT.STATE_INVALID @ artifacts/0/state` | artifact ref retained | no enum coercion | no verified inference | `test_f09_vertical_matrix[T69]` |
| T70 | item STALE | old statement revision | STALE; set not ready | `ARTIFACT.STALE_REVISION @ artifacts/0` | old input refs | item/set states separate | no feedback | `test_f09_vertical_matrix[T70]` |
| T71 | item MISMATCH | observed != expected | MISMATCH; set not ready | `ARTIFACT.DIGEST_MISMATCH @ artifacts/0/observed_digest` | attempt retained | digests separate | no overwrite | `test_f09_vertical_matrix[T71]` |
| T72 | item SUPERSEDED | newer revision replaces old | SUPERSEDED | none | old/new refs auditable | old identity retained | not verified | `test_f09_vertical_matrix[T72]` |
| T73 | ABSTAIN unresolved disposition | unique F09 UNRESOLVED | ABSTAIN valid | `COMPETITION.UNRESOLVED @ competition/dispositions/0` | blocking competition basis | disposition exact | no outcome statement | `test_f09_vertical_matrix[T73]` |
| T74 | declaration/record 全覆盖 | six unique declarations and records | valid | none | bijection by member ID | shared whole ref | order independent | `test_f09_vertical_matrix[T74]` |
| T75 | duplicate/omitted member | duplicate or remove member | invalid | `GATE.MEMBER_CARDINALITY_INVALID @ gate_sets/0/records` | no inferred member | bijection fails | no repair | `test_f09_vertical_matrix[T75]` |
| T76 | unknown member | record member undeclared | invalid | `GATE.MEMBER_DECLARATION_INVALID @ gate_sets/0/records/member` | bad record retained | declaration mismatch | fail closed | `test_f09_vertical_matrix[T76]` |
| T77 | shared-ref inconsistency | one member uses subpath/other ref | invalid | `GATE.MEMBER_BINDING_MISMATCH @ gate_sets/0/gate_definition_ref` | six IDs retained | whole ref must equal | no coercion | `test_f09_vertical_matrix[T77]` |
| T78 | declaration version/digest 失败 | drift version/value/ref/digest | invalid | `GATE.MEMBER_DECLARATION_INVALID @ gate_sets/0/declaration_set` | member ID not enough | version+digest boundary | no stale reuse | `test_f09_vertical_matrix[T78]` |
| T79 | evaluation binding mismatch | mutate content, keep digests | invalid | `GATE.MEMBER_BINDING_MISMATCH @ gate_sets/0/records/0/evaluation_binding_ref` | mutated fields visible | both digests recomputed/checked | no accept | `test_f09_vertical_matrix[T79]` |
| T80 | permutation attack | swap member content, keep bindings | invalid | `GATE.PERMUTATION_BINDING_INVALID @ gate_sets/0/records` | member-local basis checked | identity/content bound | no positional repair | `test_f09_vertical_matrix[T80]` |
| T81 | record reorder invariance | reorder intact records only | semantics unchanged | none | basis values unchanged | bindings unchanged | no semantic drift | `test_f09_vertical_matrix[T81]` |
| T82 | 配置单轴完整 fixture | allocation SAT; risk UNKNOWN | CONDITIONAL allocation | `GATE.STATE_UNKNOWN @ gate/RISK` | six records and issue chain | member bindings exact | no risk strengthening | `test_f09_vertical_matrix[T82]` |
| T83 | 风险单轴完整 fixture | risk SAT; allocation UNKNOWN | limited risk | `GATE.STATE_UNKNOWN @ gate/ALLOCATION` | six records and issue chain | member bindings exact | no allocation strengthening | `test_f09_vertical_matrix[T83]` |
| T84 | 双轴完整 fixture | allocation/risk and four others SAT | dual-axis available | none | six satisfied records | bindings exact | no priority invented | `test_f09_vertical_matrix[T84]` |
| T85 | 六维 gate 断链 | break binding/evidence/path/relation/decision | invalid | `GATE.PATH_INVALID @ gate_sets/0/records` | each member independent | broken ref identified | fail closed | `test_f09_vertical_matrix[T85]` |
| T86 | 理论证据冒充现实 | SAT uses chart/hypothesis only | invalid gate | `EVIDENCE.TRACK_INVALID @ gate/supporting_evidence_ids` | invalid support retained | evidence track bound | no SAT promotion | `test_f09_vertical_matrix[T86]` |
| T87 | 五场景 participation 一致 | local PR-REALITY-X per scenario | valid | none | state/support/issues align gates | shared frozen ref | no cross-scenario reuse | `test_f09_vertical_matrix[T87]` |
| T88 | 共享全满足现实角色攻击 | non-output uses PR-REALITY-OUTPUT | invalid | `PARTICIPATION.SCENARIO_MISMATCH @ participation/records` | local basis required | scenario identity bound | no masking | `test_f09_vertical_matrix[T88]` |
| T89 | action→trace→statement basis 漂移 | delete/reorder/replace gate or PR ID | invalid | `TRACE.BASIS_MISMATCH @ statements/0/basis_record_ids` | three layers ordered-equal | record identity separately valid | no publish | `test_f09_vertical_matrix[T89]` |
| T90 | actual Markdown + JSON resolution | actual canonical selector and fixture | valid projection | none | both source chains reachable | two SourceBinding branches exact | no YAML/prose substitute | `test_f09_vertical_matrix[T90]` |
| T91 | state 来源字段完整 | level/position/as_of three pointers | valid projection | none | three LOSSLESS mappings | object-root locators exact | no synthesis | `test_f09_vertical_matrix[T91]` |
| T92 | event 来源字段完整 | six event fields/pointers | valid projection | none | six LOSSLESS mappings | same event object identity | no synthesis | `test_f09_vertical_matrix[T92]` |
| T93 | state/event 错配 | swap objects/windows or envelope-root pointer | invalid projection | `SOURCE.LOCATOR_MISMATCH @ source_locators` | bad chain explicit | object/pointer/temporal bound | no interchange | `test_f09_vertical_matrix[T93]` |
| T94 | bounded outcome 完整 | axis/action/object/tense four fields | valid projection | none | four LOSSLESS mappings | value_schema null; refs exact | no business synthesis | `test_f09_vertical_matrix[T94]` |
| T95 | source field/object/pointer missing | delete source but retain target | invalid LOSSLESS | `SOURCE.POINTER_UNRESOLVED @ transformations/LOSSLESS_COPY` | broken input ref shown | no metadata substitute | no output | `test_f09_vertical_matrix[T95]` |
| T96 | snapshot identity/JCS mismatch | drift any five identity/digest property | invalid projection | `SOURCE.IDENTITY_MISMATCH @ source_locators/binding` | envelope/payload refs retained | five fields and payload digest exact | no local bypass | `test_f09_vertical_matrix[T96]` |
| T97 | mapping/external termination incomplete | delete mapping or actual-file termination | invalid LOSSLESS | `TRACE.EDGE_MISSING @ transformations/mappings` | each target requires source chain | VersionedObjectRefs reachable | no claim | `test_f09_vertical_matrix[T97]` |
| T98 | bounded outcome 缺要素 | remove one of four source elements | incomplete | `SOURCE.FIELD_MISSING @ outcome` | remaining refs retained | missing locator explicit | no inference | `test_f09_vertical_matrix[T98]` |
| T99 | prose preview 结构化攻击 | parse Markdown/free text as LOSSLESS | invalid transformation | `TRANSFORMATION.UNSUPPORTED @ transformations/0` | prose ref segregated | JSON source binding required | no auto extraction | `test_f09_vertical_matrix[T99]` |
| T100 | value_schema/旧 locator 攻击 | use metadata or old top-level identity | invalid design | `SOURCE.BINDING_INVALID @ source_locators/0` | source chain absent | canonical nested binding required | no dual-write | `test_f09_vertical_matrix[T100]` |
| T101 | 输出工具/金额/财富结果 | expand beyond copied four fields | prohibited output | `OUTPUT.SCOPE_EXCEEDED @ statements/0/statement_text` | lawful four-field basis retained | LOSSLESS refs unchanged | no expanded publish | `test_f09_vertical_matrix[T101]` |
| T102 | UNKNOWN reason registry hit | unknown in conditional/risk-only | valid only registered | `GATE.STATE_UNKNOWN @ gate/*/reason_codes` | issue/path retained | registry code exact | unknown code fails | `test_f09_vertical_matrix[T102]` |
| T103 | CONDITIONAL risk issue 传播 | inspect payload/issues/trace/statement | valid iff preserved | `ISSUE-RISK-UNKNOWN @ action/payload` | same issue and basis all layers | refs field-equal | no dropped issue | `test_f09_vertical_matrix[T103]` |
| T104 | 综合 fail-closed | unknown member/binding/digest/reason attack | invalid | `GATE.MEMBER_DECLARATION_INVALID @ decision_result` | all attack evidence retained | locator/gate bindings checked | no downgrade repair | `test_f09_vertical_matrix[T104]` |
<!-- PI-570-R1-SCENARIOS-END -->

### Concrete frozen fixture graph and literal mutator bodies

`tests/f09/conftest.py` must copy the following frozen graph and baseline values literally. These are phase-specific fixture inputs, not boolean expected-result switches. `GateFixture`, `DeclarationFixture`, `DecisionFixture`, `ParticipationFixture`, `RootTimingFixture`, and `SourceFixture` below are aliases of Task 5's canonical frozen input-state types rather than competing test declarations. Gate/declaration/decision/participation/root-timing/source fields are converted by the explicit `materialize_f09_decision_inputs()` boundary into the four production inputs consumed by `run_f09_slice`. The three test-only post-run consumers named by `execute_scenario()` are mandatory concrete adapters: `exercise_trace_validation_phase()` constructs altered canonical Task 6 `TraceEnvelope`/`StatementSet` inputs and calls `validate_statement_projection()`; `exercise_artifact_lifecycle_phase()` constructs projections, idempotency input and prior manifest state, then calls `write_artifact_set()`, `inspect_artifact_set()` or `retry_artifact_set()` as selected by the literal fixture values; `exercise_feedback_binding_phase()` constructs canonical `FeedbackSubmission`/`FeedbackItem` input, calls `validate_feedback_binding()`, and calls `evaluate_learning_eligibility()` for each returned binding. All three consumers are called unconditionally after `run_f09_slice()` and return typed phase observations included in `ScenarioExecution`; a failed earlier production phase is represented as an explicit not-runnable phase observation rather than skipping fixture consumption. These adapters must use direct canonical constructors, explicit keyword arguments and nested `replace()` only. They may not read `scenario.test_id` or expected assertion fields and may not use mutable dict inputs, registries, parsers, dynamic attributes, factories, `**`, outcome dispatch or catch-all branches; the two displayed `MappingProxyType` values are the complete immutable `Mapping[str, bytes]` arguments required by the Task 7 ports, not fixture dispatch tables. `baseline_scenario_bundle()` constructs the complete graph with the shown values and the real frozen request.

The following leaf-to-port table is normative. Every right-hand port denotes construction of the concrete call input before validation; comparing the fixture leaf only after the call does not count as consumption.

| Fixture leaves | Mandatory concrete Task 6–8 input/port |
|---|---|
| `trace.statement_set_complete`, `trace.statement_complete` | Presence/completeness mutation of the canonical `StatementSet` and selected `StandardStatement` passed to `validate_statement_projection()` |
| `trace.statement_basis_ids`, `trace.rule_ref_ids`, `trace.statement_text`, `trace.issue_propagation_ids` | Canonical `StandardStatement.basis_record_ids`, rule/evidence reference projection, `statement_text`, and issue IDs passed through `validate_statement_projection()` |
| `trace.transformation_fidelity`, `trace.field_mapping_count`, `trace.external_source_terminated` | Both canonical state/event `TransformationRecord`s, their independent source/target nodes and terminal edges in the `TraceEnvelope` passed to `validate_statement_projection()`; zero mapping removes both mapping sets and the terminal edges before the call |
| `trace.card_runtime_status` | Canonical `CardIdentityRef.runtime_capability_status` in the `StandardStatement` passed to `validate_statement_projection()` |
| `artifacts.records_write_outcome`, `artifacts.index_write_outcome` | Literal `fail_after` boundary and concrete projection bytes supplied to `write_artifact_set()`; each failure name selects only its documented Task 7 write boundary |
| `artifacts.index_revision`, `artifacts.statement_revision`, `artifacts.supersedes_revision` | Statement/index revision identities and independently existing current/new plus old canonical `ArtifactRecord` identities supplied in the manifest to `inspect_artifact_set()` and `retry_artifact_set()`; the old record is `SUPERSEDED` and no identity is parsed from `issue_ids` |
| `artifacts.expected_digest`, `artifacts.observed_digest`, `artifacts.item_states` | Canonical `ArtifactRecord` digest/state fields in the manifest supplied to `inspect_artifact_set()` |
| `artifacts.retry_key_digest`, `artifacts.retry_report_payload`, `artifacts.retry_records_payload`, `artifacts.retry_index_payload` | Actual incoming canonical `IdempotencyKey.canonical_key_digest` plus the complete required-role byte payload set supplied to `retry_artifact_set()` |
| `feedback.target_statement_id`, `feedback.target_revision`, `feedback.source_track` | Canonical pre-call `FeedbackItem` target identities and `FeedbackSubmission.track` supplied to `validate_feedback_binding()` |
| `feedback.anchor_status` | Pre-call availability of the matching statement-record anchor in `ArtifactSetManifest.records`; `MAPPED` retains it and every other literal removes it before `validate_feedback_binding()` |
| `feedback.seven_matches` | Seven desired match stimuli translated before binding, in order, into submission case, submission track, target run identity/availability, target statement identity/availability, target revision identity/availability, statement-set identity/availability, and manifest digest identity/availability; the binder alone calculates all seven returned dimensions |
| `feedback.policy_version`, `feedback.prior_policy_version` | Current policy is invariantly `PRODUCTION-STATEMENT-ELIGIBILITY` / `policy-v1` for anchor selection, the current canonical key, and every `evaluate_learning_eligibility()` call. `prior_policy_version` is historical stimulus used only by the prior canonical key. `feedback.policy_version` is fixed at `policy-v1` as a fixture contract assertion and is not a variable active-evaluator input. |
| `feedback.item_ids`, `feedback.prior_source_digest`, `feedback.source_digest`, `feedback.submission_complete` | Canonical item identities plus explicit prior/current `IdempotencyKey`, prior/current target digests, statement/set/records refs, `StatementProjectionRecord`, `AnchorSelectionRecord`, and PREPROD run-target ref map are supplied to `validate_feedback_binding()`; changed source changes the canonical key and is asserted from returned `FeedbackOperationResult`, not from two submissions or an adapter-invented pair |
| `feedback.binding_complete`, `feedback.eligibility_complete` | After binding, only `feedback_binding_id` is cleared to form the record-validator negative case; no match dimension or `record_anchor_ref` is overwritten. The canonical `LearningEligibility.eligibility_id` is independently cleared before its validator; eligibility remains side-effect free |

The three adapters and their typed observation dataclasses must be defined literally in `tests/f09/conftest.py` beside `materialize_f09_decision_inputs()`. Their component tests mutate every listed leaf once and prove that the designated canonical call argument changes while all non-target arguments remain equal. No adapter definition may be omitted in favor of prose or an undefined helper.

**R13 typed phase-output rule:** each adapter owns one immutable `issues` tuple and appends a `PhaseIssueObservation(code, path)` only by mechanically projecting either (a) a caught `F09Error`'s exact `issue_code`/`field_path`, or (b) the invoked canonical port's returned `DetectedIssue.issue_code`/`field_path`. Successful returned state, dimensions, code-only `issue_ids`, and `blocking_reason_codes` are never interpreted by the adapter; Tasks 6–8 already emitted code and path together at their actual production detection branches. The adapter may still use fixtures to build call inputs and may retain string `errors` for diagnostics, but neither the adapter nor any downstream matrix helper may derive a pair from `VerticalScenario.expected_*`, `test_id`, mutation text/token, fixture field patterns, baseline-to-mutated differences, status/state mappings, code-only fields, or exception text. The following ownership is closed: trace issues are emitted by `validate_statement_projection()`, artifact issues by `write_artifact_set()`/`inspect_artifact_set()`/`retry_artifact_set()`, and feedback issues by `validate_feedback_binding()`/`evaluate_learning_eligibility()` or a typed validator exception; the three adapters only forward those pairs, and no second phase-issue scanner or re-judgment layer is permitted.

**R14 static phase-owned producer-surface inventory:** this is an inspection index into the literal Task 6–8 producer blocks above, not executable scenario logic. “Returned” means the named canonical production-owned `detected_issues` tuple; “exception” means typed `F09Error.issue_code` plus `F09Error.field_path`. Every path below is the exact leading-slash literal copied from the T01–T104 constructors. There is no shorthand, omitted leading slash, display normalization, path normalization or adapter-side prefixing. Rows genuinely owned by Task 5 decision outputs remain outside this table and continue to use canonical `DecisionIssue` pairs. No row below authorizes an adapter to infer a pair from observed state.

| PI-300 row | Frozen exact pair | Canonical port and producer surface | Concrete detection branch and constructor |
|---|---|---|---|
| T19 | `TRACE.BINDING_MISMATCH @ /statements/0/output_precision_binding` | `validate_statement_projection()` → `ProjectionValidationResult.detected_issues` | statement/decision precision binding inequality → branch-local `DetectedIssue(...)` |
| T20 | `PROJECTION.LOSSY @ /transformations/records` | `validate_statement_projection()` → `ProjectionValidationResult.detected_issues` | multi-evidence projection with a lossy transformation → branch-local `DetectedIssue(...)` |
| T21 | `ARTIFACT.WRITE_FAILED @ /artifacts/STATEMENT_RECORDS` | `write_artifact_set()` → returned partial `ArtifactSetManifest.detected_issues`, or `F09WriteError` only when non-returnable | records write-boundary failure → exact returned/exception constructor |
| T22 | `ARTIFACT.WRITE_FAILED @ /artifacts/STATEMENT_INDEX` | `write_artifact_set()` → returned partial `ArtifactSetManifest.detected_issues`, or `F09WriteError` only when non-returnable | index write-boundary failure → exact returned/exception constructor |
| T23 | `ARTIFACT.STALE_REVISION @ /artifacts/STATEMENT_INDEX` | `inspect_artifact_set()` → `ArtifactSetManifest.detected_issues` | index revision stale against current records → branch-local `DetectedIssue(...)` |
| T24 | `ARTIFACT.DIGEST_MISMATCH @ /artifacts/observed_digest` | `inspect_artifact_set()` → `ArtifactSetManifest.detected_issues` | observed set digest differs from expected → branch-local `DetectedIssue(...)` |
| T25 | `FEEDBACK.TARGET_UNBOUND @ /feedback_bindings/0` | `validate_feedback_binding()` → `FeedbackBinding.detected_issues`, or `F09ContractError` only when non-returnable | target/required anchor does not resolve uniquely → exact returned/exception constructor |
| T26 | `FEEDBACK.REVISION_MISMATCH @ /feedback_bindings/0/revision_match` | `validate_feedback_binding()` → `FeedbackBinding.detected_issues`, or `F09ContractError` only when non-returnable | requested and resolved statement revisions differ → exact returned/exception constructor |
| T27 | none | `retry_artifact_set()` → `ArtifactSetManifest.detected_issues=()` | same key and same payload digest → issue-free no-op constructor |
| T28 | `IDEMPOTENCY.DIGEST_MISMATCH @ /canonical_key_digest` | `retry_artifact_set()` → `ArtifactSetManifest.detected_issues` | same key and different payload digest → branch-local `DetectedIssue(...)` |
| T29 | `FEEDBACK.TRACK_MISMATCH @ /feedback_bindings/0/track_match` | `validate_feedback_binding()` → `FeedbackBinding.detected_issues`, or `F09ContractError` only when non-returnable | submission and target canonical tracks differ → exact returned/exception constructor |
| T30 | `CARD.IDENTITY_INVALID @ /card_identity_refs/0/runtime_capability_status` | `validate_statement_projection()` → `ProjectionValidationResult.detected_issues`, or `F09ContractError` | capability differs from reference-only literal → exact returned/exception constructor |
| T37 | `TRACE.BINDING_MISMATCH @ /trace/declarations` | `validate_statement_projection()` → `ProjectionValidationResult.detected_issues`, or `F09ContractError` | trace/result declarations differ → exact returned/exception constructor |
| T44 | `STATEMENT.SET_INVALID @ /statement_set` | `validate_statement_projection()` → `ProjectionValidationResult.detected_issues`, or `F09ContractError` | required set field absent → exact returned/exception constructor |
| T45 | `STATEMENT.RECORD_INVALID @ /statements/0` | `validate_statement_projection()` → `ProjectionValidationResult.detected_issues`, or `F09ContractError` | required statement field absent → exact returned/exception constructor |
| T58 | changed-source/new-canonical-key operation outcome; no semantic issue pair | `validate_feedback_binding()` → `FeedbackOperationResult` | changed source digest plus changed canonical key returns `NEW_OPERATION`, `source_identity_relation=CHANGED`, retained prior/current key and digest evidence, and `overwrite_permitted=False`; exact same-key/different-target alone owns `IDEMPOTENCY.DIGEST_MISMATCH @ /feedback/source_snapshot_ref` |
| T68 | `ARTIFACT.STATE_INVALID @ /artifacts/0/state` | `inspect_artifact_set()` → `F09ContractError` | raw `NOT_STARTED` is outside `ArtifactItemState` → exact exception constructor |
| T69 | `ARTIFACT.STATE_INVALID @ /artifacts/0/state` | `inspect_artifact_set()` → `F09ContractError` | raw `WRITTEN` is outside `ArtifactItemState` → exact exception constructor |
| T70 | `ARTIFACT.STALE_REVISION @ /artifacts/0` | `inspect_artifact_set()` → `ArtifactSetManifest.detected_issues` | first item is legal `STALE` → branch-local `DetectedIssue(...)` |
| T71 | `ARTIFACT.DIGEST_MISMATCH @ /artifacts/0/observed_digest` | `inspect_artifact_set()` → `ArtifactSetManifest.detected_issues` | first item is legal `MISMATCH` → branch-local `DetectedIssue(...)` |
| T89 | `TRACE.BASIS_MISMATCH @ /statements/0/basis_record_ids` | `validate_statement_projection()` → `ProjectionValidationResult.detected_issues`, or `F09ContractError` | statement/result ordered basis differs → exact returned/exception constructor |
| T93 | `SOURCE.LOCATOR_MISMATCH @ /source_locators` | `validate_statement_projection()` → `ProjectionValidationResult.detected_issues`, or `F09SourceError` | state/event object-pointer-temporal identity interchanged → exact returned/exception constructor |
| T95 | `SOURCE.POINTER_UNRESOLVED @ /transformations/LOSSLESS_COPY` | `validate_statement_projection()` → `ProjectionValidationResult.detected_issues`, or `F09SourceError` | lossless source object/pointer does not resolve → exact returned/exception constructor |
| T96 | `SOURCE.IDENTITY_MISMATCH @ /source_locators/binding` | `validate_statement_projection()` → `ProjectionValidationResult.detected_issues`, or `F09SourceError` | binding identity/payload digest differs from snapshot → exact returned/exception constructor |
| T97 | `TRACE.EDGE_MISSING @ /transformations/mappings` | `validate_statement_projection()` → `ProjectionValidationResult.detected_issues`, or `F09SourceError` | lossless mapping or actual-file terminal edge missing → exact returned/exception constructor |
| T98 | `SOURCE.FIELD_MISSING @ /outcome` | `validate_statement_projection()` → `ProjectionValidationResult.detected_issues`, or `F09SourceError` | bounded outcome lacks axis/action/object/tense → exact returned/exception constructor |
| T99 | `TRANSFORMATION.UNSUPPORTED @ /transformations/0` | `validate_statement_projection()` → `ProjectionValidationResult.detected_issues`, or `F09IntegrityError` | prose/Markdown used as structured lossless source → exact returned/exception constructor |
| T100 | `SOURCE.BINDING_INVALID @ /source_locators/0` | `validate_statement_projection()` → `ProjectionValidationResult.detected_issues`, or `F09SourceError` | metadata/legacy identity substitutes for canonical nested binding → exact returned/exception constructor |
| T101 | `OUTPUT.SCOPE_EXCEEDED @ /statements/0/statement_text` | `validate_statement_projection()` → `ProjectionValidationResult.detected_issues`, or `F09IntegrityError` | statement expands beyond copied four-field scope → exact returned/exception constructor |

Inventory closure is fail-closed: every phase-owned positive row T19–T26, T28–T30, T37, T44–T45, T58, T68–T71, T89, T93, and T95–T101 has one named producer surface above; T27 is explicitly reconciled to its real PI-300 no-issue expectation. T31–T36, T38–T43, T46–T57, T59–T67, T72–T88, T90–T92, T94, and T102–T104 remain decision-owned, no-issue, or otherwise governed by their existing matrix row and are not reclassified merely to populate this phase inventory.

The single fenced block below is the sole copy source for `tests/f09/conftest.py`. Copy from the first `from dataclasses import ...` import through the closing return of `mutate_t104`, inclusive, as one continuous module. The imports and displayed definitions are complete scaffolding: fixture aliases reuse Task 5 canonical input-state types; all production contracts come from the named `engine.f09` modules; `Callable`, `VerticalScenario`, `ScenarioExecution` and `execute_scenario` are bound inside this module before scenario-data can reverse-import any conftest symbol. This module never imports `tests.f09.data.f09_vertical_scenarios`; therefore there is no conftest↔scenario-data import cycle. No hidden helper, competing test type, registry, wildcard/dynamic import, or undeclared dependency is permitted.

```python
import json

from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Callable, Literal, Mapping

from engine.f09.application import F09RunRequest, F09RunResult, run_f09_slice
from engine.f09.artifacts import (
    ArtifactRecord,
    ArtifactSetManifest,
    ArtifactWriteAttempt,
    IdempotencyKey,
    digest_artifact_records,
    inspect_artifact_set,
    retry_artifact_set,
    write_artifact_set,
)
from engine.f09.contracts import DecisionAction, DetectedIssue, DigestRef, FieldMapping, ObjectRef, RunTrack, TransformationRecord
from engine.f09.decision import (
    CompetitionInput,
    DecisionInputState,
    DeclarationInputState,
    GateEvaluationInput,
    GateInputState,
    ParticipationInputState,
    RootInput,
    RootTimingInputState,
    SourceInputState,
    TimingInput,
)
from engine.f09.errors import F09Error
from engine.f09.feedback import (
    AnchorSelectionRecord,
    FeedbackBinding,
    FeedbackItem,
    FeedbackOperationResult,
    FeedbackSubmission,
    LearningEligibility,
    StatementProjectionRecord,
    TrackSourceBinding,
    TrackSourceReasonCode,
    TrackSourceState,
    digest_ordered_rule_refs,
    digest_protocol_target_graph,
    evaluate_learning_eligibility,
    validate_feedback_binding,
    validate_feedback_binding_record,
    validate_learning_eligibility,
    validate_versioned_ref,
)
from engine.f09.trace import (
    DigestPresent,
    SnapshotRef,
    StatementSet,
    TraceEdge,
    TraceEnvelope,
    TraceNode,
    VersionedObjectRef,
    validate_statement_projection,
)

GateFixture = GateInputState
DeclarationFixture = DeclarationInputState
DecisionFixture = DecisionInputState
ParticipationFixture = ParticipationInputState
RootTimingFixture = RootTimingInputState

@dataclass(frozen=True)
class TraceFixture:
    statement_set_complete: bool; statement_complete: bool; statement_basis_ids: tuple[str, ...]
    rule_ref_ids: tuple[str, ...]; transformation_fidelity: str; field_mapping_count: int
    external_source_terminated: bool; card_runtime_status: str; statement_text: str; issue_propagation_ids: tuple[str, ...]

@dataclass(frozen=True)
class ArtifactFixture:
    records_write_outcome: str; index_write_outcome: str; index_revision: str
    expected_digest: str; observed_digest: str; item_states: tuple[str, ...]; statement_revision: str
    supersedes_revision: str | None; retry_key_digest: str
    retry_report_payload: bytes; retry_records_payload: bytes; retry_index_payload: bytes

@dataclass(frozen=True)
class FeedbackFixture:
    binding_protocol: Literal["PRODUCTION_STATEMENT", "PREPROD_RUN_TARGET"]
    target_statement_id: str | None; target_revision: str | None; anchor_status: str; target_graph_relation: Literal["SAME", "CHANGED"]
    seven_matches: tuple[str, ...]
    source_track: RunTrack; source_track_state: TrackSourceState; source_track_evidence_id: str
    source_track_parser_id: str; source_track_parser_version: str; source_track_schema_version: str
    source_track_contract_version: str; source_track_digest: str
    source_track_reason_codes: tuple[TrackSourceReasonCode, ...]
    target_track: RunTrack; target_track_state: TrackSourceState; target_track_evidence_id: str
    target_track_parser_id: str; target_track_parser_version: str; target_track_schema_version: str
    target_track_contract_version: str; target_track_digest: str
    target_track_reason_codes: tuple[TrackSourceReasonCode, ...]
    policy_version: Literal["policy-v1"]; item_ids: tuple[str, ...]; prior_source_digest: str; source_digest: str
    submission_complete: bool; binding_complete: bool; eligibility_complete: bool
    preprod_authority_records: tuple[ArtifactRecord | object, ...]
    preprod_authority_refs: tuple[VersionedObjectRef | object, ...]
    prior_policy_version: str = "policy-v1"

SourceFixture = SourceInputState

@dataclass(frozen=True)
class F09DecisionInputs:
    gate_inputs: tuple[GateEvaluationInput, ...]
    competition_input: CompetitionInput
    root_input: RootInput
    timing_input: TimingInput

@dataclass(frozen=True)
class ScenarioBundle:
    request: F09RunRequest
    gate: GateFixture
    declarations: DeclarationFixture
    decision: DecisionFixture
    participation: ParticipationFixture
    root_timing: RootTimingFixture
    trace: TraceFixture
    artifacts: ArtifactFixture
    feedback: FeedbackFixture
    source: SourceFixture

@dataclass(frozen=True)
class VerticalScenario:
    test_id: str
    pi300_purpose: str
    mutation: str
    mutate: Callable[[ScenarioBundle], ScenarioBundle]
    expected_action: DecisionAction | None
    expected_gate_or_state: str
    expected_issue_code: str | None
    expected_issue_path: str | None
    basis_assertions: tuple[str, ...]
    binding_assertions: tuple[str, ...]
    side_effect_assertion: str
    pytest_node: str

# This required fixture adapter uses only the four canonical Task 5 constructors. It is not
# part of the 104-mutator acceptance count and may not inspect test_id, expected outcomes, or
# assertion labels. No helper/factory declaration or dynamic expansion is permitted. Its
# dedicated contract test mutates each ScenarioBundle decision-input leaf once and proves the
# corresponding canonical constructor argument changes exactly once.
def materialize_f09_decision_inputs(bundle: ScenarioBundle) -> F09DecisionInputs:
    return F09DecisionInputs(
        gate_inputs=(GateEvaluationInput(gate=bundle.gate, declarations=bundle.declarations, participation=bundle.participation, source=bundle.source),),
        competition_input=CompetitionInput(decision=bundle.decision, source=bundle.source),
        root_input=RootInput(root_timing=bundle.root_timing, source=bundle.source),
        timing_input=TimingInput(root_timing=bundle.root_timing, source=bundle.source),
    )

@dataclass(frozen=True)
class BoundaryCall:
    # Closed tests-only call topology: these are the only callable ports imported
    # or invoked by execute_scenario and its three phase adapters. F08 execution,
    # publication, production persistence, and learning persistence have no port
    # in this module and therefore cannot be represented as an observed call.
    port: Literal[
        "RUN_F09_SLICE",
        "VALIDATE_STATEMENT_PROJECTION",
        "WRITE_ARTIFACT_SET",
        "INSPECT_ARTIFACT_SET",
        "RETRY_ARTIFACT_SET",
        "VALIDATE_FEEDBACK_BINDING",
        "VALIDATE_FEEDBACK_BINDING_RECORD",
        "EVALUATE_LEARNING_ELIGIBILITY",
        "VALIDATE_LEARNING_ELIGIBILITY",
    ]
    track: RunTrack | None

@dataclass(frozen=True)
class PhaseIssueObservation:
    code: str
    path: str

@dataclass(frozen=True)
class TracePhaseObservation:
    status: Literal["VALID", "INVALID", "NOT_RUNNABLE"]
    runnable: bool
    input_trace: TraceEnvelope | None
    input_statement_set: StatementSet | None
    state_transformation: TransformationRecord | None
    event_transformation: TransformationRecord | None
    mapping_source_paths: tuple[str, ...]
    terminal_edge_count: int
    errors: tuple[str, ...]
    issues: tuple[PhaseIssueObservation, ...] = ()

@dataclass(frozen=True)
class ArtifactPhaseObservation:
    status: Literal["VALID", "INVALID", "NOT_RUNNABLE"]
    runnable: bool
    write_called: bool
    inspect_called: bool
    retry_called: bool
    write_manifest: ArtifactSetManifest | None
    inspection_input: ArtifactSetManifest | None
    inspected_manifest: ArtifactSetManifest | None
    retry_manifest: ArtifactSetManifest | None
    key: IdempotencyKey | None
    fail_after: str | None
    projection_digests: tuple[str, ...]
    errors: tuple[str, ...]
    issues: tuple[PhaseIssueObservation, ...] = ()

@dataclass(frozen=True)
class FeedbackPhaseObservation:
    status: Literal["VALID", "INVALID", "NOT_RUNNABLE"]
    runnable: bool
    submission: FeedbackSubmission | None
    input_statement_set: StatementSet | None
    input_manifest: ArtifactSetManifest | None
    bindings: tuple[FeedbackBinding, ...]
    eligibility_records: tuple[LearningEligibility, ...]
    errors: tuple[str, ...]
    issues: tuple[PhaseIssueObservation, ...] = ()
    operation_result: FeedbackOperationResult | None = None

@dataclass(frozen=True)
class ScenarioExecution:
    baseline_bundle: ScenarioBundle
    mutated_bundle: ScenarioBundle
    decision_inputs: F09DecisionInputs
    run_result: F09RunResult
    trace_phase: TracePhaseObservation
    artifact_phase: ArtifactPhaseObservation
    feedback_phase: FeedbackPhaseObservation
    overall_status: Literal["VALID", "INVALID"]
    boundary_calls: tuple[BoundaryCall, ...]

# This Task 6 adapter consumes source fixture values as stimulus only. It never receives a
# VerticalScenario and therefore cannot read test_id, expected action/state, or expected issues.
def exercise_trace_validation_phase(
    run_result: F09RunResult,
    fixture: TraceFixture,
    source: SourceFixture,
    boundary_calls: list[BoundaryCall] | None = None,
) -> TracePhaseObservation:
    if run_result.trace is None or run_result.statement_set is None or run_result.decision is None:
        return TracePhaseObservation(
            status="NOT_RUNNABLE",
            runnable=False,
            input_trace=None,
            input_statement_set=None,
            state_transformation=None,
            event_transformation=None,
            mapping_source_paths=(),
            terminal_edge_count=0,
            errors=("TRACE_PREREQUISITE_NOT_PRODUCED",),
        )
    if len(source.state_fields) < 3:
        return TracePhaseObservation("INVALID", False, None, None, None, None, (), 0, ("SOURCE_STATE_FIELD_SHAPE_INVALID",))
    if len(source.event_fields) < 6:
        return TracePhaseObservation("INVALID", False, None, None, None, None, (), 0, ("SOURCE_EVENT_FIELD_SHAPE_INVALID",))
    if len(run_result.trace.nodes) < 1:
        return TracePhaseObservation("INVALID", False, run_result.trace, run_result.statement_set, None, None, (), 0, ("TRACE_NODE_SHAPE_INVALID",))
    if len(run_result.statement_set.statements) < 1:
        return TracePhaseObservation("INVALID", False, run_result.trace, run_result.statement_set, None, None, (), 0, ("STATEMENT_SHAPE_INVALID",))
    guarded_statement = run_result.statement_set.statements[0]
    if len(guarded_statement.card_identity_refs) < 1:
        return TracePhaseObservation("INVALID", False, run_result.trace, run_result.statement_set, None, None, (), 0, ("CARD_REF_SHAPE_INVALID",))
    if len(guarded_statement.evidence_refs) < 1:
        return TracePhaseObservation("INVALID", False, run_result.trace, run_result.statement_set, None, None, (), 0, ("EVIDENCE_REF_SHAPE_INVALID",))

    state_mapping_1 = FieldMapping(
        source_field_path=source.state_pointer + "/" + source.state_fields[0],
        target_field_path="/payload/value/level",
        operation="COPY",
        fidelity="LOSSLESS",
    )
    state_mapping_2 = FieldMapping(
        source_field_path=source.state_pointer + "/" + source.state_fields[1],
        target_field_path="/payload/value/position",
        operation="COPY",
        fidelity="LOSSLESS",
    )
    state_mapping_3 = FieldMapping(
        source_field_path=source.state_pointer + "/" + source.state_fields[2],
        target_field_path="/temporal_scope/as_of/value",
        operation="COPY",
        fidelity="LOSSLESS",
    )
    mapping_1 = FieldMapping(
        source_field_path=source.event_pointer + "/" + source.event_fields[0],
        target_field_path="/payload/value/level",
        operation="COPY",
        fidelity="LOSSLESS",
    )
    mapping_2 = FieldMapping(
        source_field_path=source.event_pointer + "/" + source.event_fields[1],
        target_field_path="/payload/value/change",
        operation="COPY",
        fidelity="LOSSLESS",
    )
    mapping_3 = FieldMapping(
        source_field_path=source.event_pointer + "/" + source.event_fields[2],
        target_field_path="/temporal_scope/interval/start/value",
        operation="COPY",
        fidelity="LOSSLESS",
    )
    mapping_4 = FieldMapping(
        source_field_path=source.event_pointer + "/" + source.event_fields[3],
        target_field_path="/temporal_scope/interval/end/value",
        operation="COPY",
        fidelity="LOSSLESS",
    )
    mapping_5 = FieldMapping(
        source_field_path=source.event_pointer + "/" + source.event_fields[4],
        target_field_path="/temporal_scope/interval/start_inclusive",
        operation="COPY",
        fidelity="LOSSLESS",
    )
    mapping_6 = FieldMapping(
        source_field_path=source.event_pointer + "/" + source.event_fields[5],
        target_field_path="/temporal_scope/interval/end_inclusive",
        operation="COPY",
        fidelity="LOSSLESS",
    )
    all_state_mappings = (state_mapping_1, state_mapping_2, state_mapping_3)
    all_event_mappings = (mapping_1, mapping_2, mapping_3, mapping_4, mapping_5, mapping_6)
    selected_state_mappings = all_state_mappings if fixture.field_mapping_count > 0 else ()
    selected_event_mappings = all_event_mappings[:fixture.field_mapping_count]
    source_object_type = "PROSE_PREVIEW" if source.source_kind == "MARKDOWN_FREE_TEXT" else "SOURCE_OBJECT"
    source_locator_id = "SRCLOC-STATE-LEVEL" if source.canonical_nested_binding else None
    state_source_object_refs = (() if not source.source_field_present else (ObjectRef(
        object_type=source_object_type,
        object_id=source.state_object_id,
        external=True,
        source_locator_id=source_locator_id,
    ),))
    event_source_object_refs = (() if not source.source_field_present else (ObjectRef(
        object_type=source_object_type,
        object_id=source.event_object_id,
        external=True,
        source_locator_id=("SRCLOC-EVENT-LEVEL" if source.canonical_nested_binding else None),
    ),))
    state_transformation = TransformationRecord(
        transformation_id="TR-F09-STATE-1",
        adapter_id="RealityFactAdapter",
        adapter_version="design-v1",
        source_object_refs=state_source_object_refs,
        target_object_refs=(ObjectRef(
            object_type="EVIDENCE",
            object_id="STATE-F09-2026Q2",
            external=False,
            source_locator_id=None,
        ),),
        fidelity=fixture.transformation_fidelity,
        field_mappings=selected_state_mappings,
        dropped_fields=(),
        dropped_object_refs=(),
        synthesized_fields=(),
        issues=fixture.issue_propagation_ids,
        transformed_at="2026-07-19T00:00:00Z",
    )
    event_transformation = TransformationRecord(
        transformation_id="TR-F09-EVENT-1",
        adapter_id="RealityFactAdapter",
        adapter_version="design-v1",
        source_object_refs=event_source_object_refs,
        target_object_refs=(ObjectRef(
            object_type="EVIDENCE",
            object_id="EVENT-F09-2026Q2",
            external=False,
            source_locator_id=None,
        ),),
        fidelity=fixture.transformation_fidelity,
        field_mappings=selected_event_mappings,
        dropped_fields=(),
        dropped_object_refs=(),
        synthesized_fields=(),
        issues=fixture.issue_propagation_ids,
        transformed_at="2026-07-19T00:00:00Z",
    )
    # `source.content_digest` is the accepted lowercase sha256 of RFC8785/JCS UTF-8
    # canonicalization of the immutable JSON `payload` only, never of the envelope.
    source_content_digest = DigestRef(
        "sha256",
        "RFC8785-JCS-UTF8",
        source.content_digest,
    )
    source_snapshot = SnapshotRef(
        source.snapshot_id,
        "REALITY_FACT",
        ("SRCLOC-STATE-LEVEL", "SRCLOC-EVENT-LEVEL"),
        source.snapshot_schema_version,
        source.contract_version,
        source_content_digest,
        source.captured_at,
        "IMMUTABLE",
    )
    base_node = run_result.trace.nodes[0]
    state_source_ref = replace(base_node.object_ref, object_type=source_object_type, object_id=source.state_object_id, revision_id=None, digest_binding=DigestPresent("PRESENT", source_content_digest), source_locator_id=source_locator_id)
    event_source_ref = replace(base_node.object_ref, object_type=source_object_type, object_id=source.event_object_id, revision_id=None, digest_binding=DigestPresent("PRESENT", source_content_digest), source_locator_id=("SRCLOC-EVENT-LEVEL" if source.canonical_nested_binding else None))
    state_target_ref = replace(base_node.object_ref, object_type="EVIDENCE", object_id="STATE-F09-2026Q2", revision_id="STATE-REV-1", source_locator_id=None)
    event_target_ref = replace(base_node.object_ref, object_type="EVIDENCE", object_id="EVENT-F09-2026Q2", revision_id="EVENT-REV-1", source_locator_id=None)
    state_source_node = replace(base_node, object_ref=state_source_ref, object_role="SOURCE", integrity="VALID")
    event_source_node = replace(base_node, object_ref=event_source_ref, object_role="SOURCE", integrity="VALID")
    state_target_node = replace(base_node, object_ref=state_target_ref, object_role="NORMALIZED_EVIDENCE", integrity="VALID")
    event_target_node = replace(base_node, object_ref=event_target_ref, object_role="NORMALIZED_EVIDENCE", integrity="VALID")
    state_edge = TraceEdge("EDGE-F09-STATE-1", "NORMALIZED_FROM", state_target_ref, state_source_ref, "TR-F09-STATE-1", fixture.transformation_fidelity, "NONE", fixture.issue_propagation_ids)
    event_edge = TraceEdge("EDGE-F09-EVENT-1", "NORMALIZED_FROM", event_target_ref, event_source_ref, "TR-F09-EVENT-1", fixture.transformation_fidelity, "NONE", fixture.issue_propagation_ids)
    base_statement = guarded_statement
    card_ref = replace(
        base_statement.card_identity_refs[0],
        runtime_capability_status=fixture.card_runtime_status,
    )
    base_evidence_ref = base_statement.evidence_refs[0]
    padded_rule_ref_ids = fixture.rule_ref_ids + (
        "RULE-F09-PADDING-1",
        "RULE-F09-PADDING-2",
        "RULE-F09-PADDING-3",
    )
    if len(padded_rule_ref_ids) < 3:
        return TracePhaseObservation("INVALID", False, run_result.trace, run_result.statement_set, None, None, (), 0, ("RULE_REF_SHAPE_INVALID",))
    rule_ref_1 = replace(base_evidence_ref, object_type="CARD_FIELD", object_id=padded_rule_ref_ids[0])
    rule_ref_2 = replace(base_evidence_ref, object_type="CARD_FIELD", object_id=padded_rule_ref_ids[1])
    rule_ref_3 = replace(base_evidence_ref, object_type="CARD_FIELD", object_id=padded_rule_ref_ids[2])
    statement = replace(
        base_statement,
        statement_id=base_statement.statement_id if fixture.statement_complete else "",
        statement_text=fixture.statement_text,
        basis_record_ids=fixture.statement_basis_ids,
        evidence_refs=(rule_ref_1, rule_ref_2, rule_ref_3)[:len(fixture.rule_ref_ids)],
        card_identity_refs=(card_ref,),
        issue_ids=fixture.issue_propagation_ids,
    )
    statement_set = replace(
        run_result.statement_set,
        source_package_ref=(
            run_result.statement_set.source_package_ref
            if fixture.statement_set_complete else None
        ),
        statements=(statement,),
        issue_ids=fixture.issue_propagation_ids,
    )
    outcome_target_paths = tuple("/payload/value/" + field for field in source.outcome_fields)
    retained_transformations = tuple(
        replace(
            transformation,
            field_mappings=tuple(
                mapping
                for mapping in transformation.field_mappings
                if mapping.target_field_path not in (
                    "/payload/value/axis",
                    "/payload/value/action",
                    "/payload/value/object",
                    "/payload/value/tense",
                )
                or mapping.target_field_path in outcome_target_paths
            ),
        )
        for transformation in run_result.trace.transformations
    )
    trace = replace(
        run_result.trace,
        statement_set_ref=(
            run_result.trace.statement_set_ref
            if fixture.statement_set_complete else None
        ),
        source_snapshot_refs=run_result.trace.source_snapshot_refs + (source_snapshot,),
        nodes=run_result.trace.nodes + (state_source_node, event_source_node, state_target_node, event_target_node),
        transformations=retained_transformations + (state_transformation, event_transformation),
        edges=(run_result.trace.edges + (state_edge, event_edge) if fixture.external_source_terminated else ()),
        blocking_issue_ids=fixture.issue_propagation_ids,
    )
    errors: tuple[str, ...] = ()
    issues: tuple[PhaseIssueObservation, ...] = ()
    try:
        if boundary_calls is not None:
            boundary_calls.append(BoundaryCall("VALIDATE_STATEMENT_PROJECTION", statement_set.track))
        validation_result = validate_statement_projection(statement_set, trace, run_result.decision)
        issues = tuple(
            PhaseIssueObservation(issue.issue_code, issue.field_path)
            for issue in validation_result.detected_issues
        )
    except F09Error as error:
        errors = (type(error).__name__ + ":" + str(error),)
        issues = issues + (PhaseIssueObservation(error.issue_code, error.field_path),)
    all_mapping_source_paths = (
        state_mapping_1.source_field_path,
        state_mapping_2.source_field_path,
        state_mapping_3.source_field_path,
        mapping_1.source_field_path,
        mapping_2.source_field_path,
        mapping_3.source_field_path,
        mapping_4.source_field_path,
        mapping_5.source_field_path,
        mapping_6.source_field_path,
    )
    return TracePhaseObservation(
        status="VALID" if not errors and not issues else "INVALID",
        runnable=True,
        input_trace=trace,
        input_statement_set=statement_set,
        state_transformation=state_transformation,
        event_transformation=event_transformation,
        mapping_source_paths=(all_mapping_source_paths if fixture.field_mapping_count > 0 else ()),
        terminal_edge_count=len(trace.edges),
        errors=errors,
        issues=issues,
    )

# This Task 7 adapter always calls the write port first, then supplies an explicitly altered
# canonical manifest to inspection and retry. Fixture outcomes are stimulus; no scenario oracle
# is accepted by this function.
def exercise_artifact_lifecycle_phase(
    run_result: F09RunResult,
    fixture: ArtifactFixture,
    tmp_path: Path,
    boundary_calls: list[BoundaryCall] | None = None,
) -> ArtifactPhaseObservation:
    if run_result.statement_set is None:
        return ArtifactPhaseObservation(
            status="NOT_RUNNABLE",
            runnable=False,
            write_called=False,
            inspect_called=False,
            retry_called=False,
            write_manifest=None,
            inspection_input=None,
            inspected_manifest=None,
            retry_manifest=None,
            key=None,
            fail_after=None,
            projection_digests=(),
            errors=("STATEMENT_SET_PREREQUISITE_NOT_PRODUCED",),
        )

    source_digest = DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(fixture.expected_digest.encode("utf-8")).hexdigest())
    write_key = IdempotencyKey(
        operation="PROJECT_RECORDS",
        case_id=run_result.statement_set.case_id,
        track=run_result.statement_set.track,
        source_digest=source_digest,
        schema_versions_digest=DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(fixture.statement_revision.encode("utf-8")).hexdigest()),
        contract_digest=None,
        statement_set_id=run_result.statement_set.statement_set_id,
        feedback_id=None,
        canonical_key_digest=DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(b"IDEM-KEY-A").hexdigest()),
    )
    key = replace(
        write_key,
        canonical_key_digest=DigestRef(
            "sha256", "RFC8785-JCS-UTF8",
            sha256(fixture.retry_key_digest.encode("utf-8")).hexdigest(),
        ),
    )
    projections = MappingProxyType({
        "REPORT": b"F09 staged report\n",
        "STATEMENT_RECORDS": fixture.expected_digest.encode("utf-8"),
        "STATEMENT_INDEX": fixture.index_revision.encode("utf-8"),
    })
    fail_after = (
        "STATEMENT_RECORDS" if fixture.records_write_outcome == "FAILED" else
        "STATEMENT_INDEX" if fixture.index_write_outcome == "FAILED" else
        None
    )
    errors: tuple[str, ...] = ()
    issues: tuple[PhaseIssueObservation, ...] = ()
    write_called = False
    inspect_called = False
    retry_called = False
    write_manifest: ArtifactSetManifest | None = None
    inspection_input: ArtifactSetManifest | None = None
    inspected_manifest: ArtifactSetManifest | None = None
    retry_manifest: ArtifactSetManifest | None = None
    try:
        write_called = True
        if boundary_calls is not None:
            boundary_calls.append(BoundaryCall("WRITE_ARTIFACT_SET", key.track))
        write_manifest = write_artifact_set(
            tmp_path / "f09-artifacts",
            replace(
                run_result.statement_set,
                statement_schema_version=fixture.statement_revision,
            ),
            projections,
            key=write_key,
            attempt_id="ATTEMPT-F09-1",
            now="2026-07-20T00:00:00Z",
            fail_after=fail_after,
        )
        issues = issues + tuple(
            PhaseIssueObservation(issue.issue_code, issue.field_path)
            for issue in write_manifest.detected_issues
        )
        if not write_manifest.records:
            raise AssertionError("artifact writer returned no canonical records")
        base_record = write_manifest.records[0]
        padded_states = fixture.item_states + (
            "VERIFIED", "VERIFIED", "VERIFIED", "VERIFIED",
            "VERIFIED", "VERIFIED", "VERIFIED", "VERIFIED",
        )
        if len(padded_states) < 8:
            raise AssertionError("artifact state fixture is shorter than eight records")
        record_1 = replace(base_record, artifact_id="ART-F09-1", state=padded_states[0], schema_version=fixture.statement_revision, expected_digest=DigestRef("sha256", "RAW-UTF8", sha256(fixture.expected_digest.encode("utf-8")).hexdigest()), observed_digest=DigestRef("sha256", "RAW-UTF8", sha256(fixture.observed_digest.encode("utf-8")).hexdigest()), path_locator="records/" + fixture.statement_revision, statement_set_id=run_result.statement_set.statement_set_id, run_id=None, issue_ids=())
        record_2 = replace(base_record, artifact_id="ART-F09-2", state=padded_states[1], schema_version=fixture.index_revision, path_locator="index/" + fixture.index_revision, issue_ids=())
        record_3 = replace(base_record, artifact_id="ART-F09-3", state=padded_states[2], issue_ids=())
        record_4 = replace(base_record, artifact_id="ART-F09-4", state=padded_states[3], issue_ids=())
        record_5 = replace(base_record, artifact_id="ART-F09-5", state=padded_states[4], issue_ids=())
        record_6 = replace(base_record, artifact_id="ART-F09-6", state=padded_states[5], issue_ids=())
        record_7 = replace(base_record, artifact_id="ART-F09-7", state=padded_states[6], issue_ids=())
        record_8 = replace(base_record, artifact_id="ART-F09-8", state=padded_states[7], issue_ids=())
        current_record = replace(base_record, artifact_id="ART-F09-CURRENT-" + fixture.statement_revision, path_locator="records/" + fixture.statement_revision, schema_version=fixture.statement_revision, statement_set_id=run_result.statement_set.statement_set_id, run_id=None, expected_digest=record_1.expected_digest, observed_digest=record_1.observed_digest, state="VERIFIED", issue_ids=())
        old_record = replace(base_record, artifact_id="ART-F09-OLD-" + fixture.supersedes_revision, path_locator="records/" + fixture.supersedes_revision, schema_version=fixture.supersedes_revision, statement_set_id=run_result.statement_set.statement_set_id + "-OLD", run_id=None, expected_digest=record_1.expected_digest, observed_digest=record_1.observed_digest, state="SUPERSEDED", issue_ids=()) if fixture.supersedes_revision is not None else None
        selected_records = (
            (record_1, record_2)
            if len(fixture.item_states) == 1
            else (record_1, record_2, record_3, record_4, record_5, record_6, record_7, record_8)[:len(fixture.item_states)]
        )
        manifest_records = (old_record, current_record) if old_record is not None else selected_records
        inspection_input = replace(
            write_manifest,
            records=manifest_records,
        )
        inspect_called = True
        if boundary_calls is not None:
            boundary_calls.append(BoundaryCall("INSPECT_ARTIFACT_SET", inspection_input.key.track))
        inspected_manifest = inspect_artifact_set(tmp_path / "f09-artifacts", inspection_input)
        issues = issues + tuple(
            PhaseIssueObservation(issue.issue_code, issue.field_path)
            for issue in inspected_manifest.detected_issues
        )
        retry_called = write_manifest.key == key
        if boundary_calls is not None:
            boundary_calls.append(BoundaryCall(
                "RETRY_ARTIFACT_SET" if retry_called else "WRITE_ARTIFACT_SET",
                key.track,
            ))
        retry_manifest = coordinate_artifact_operation(
            tmp_path / "f09-artifacts",
            run_result.statement_set,
            MappingProxyType({
                "REPORT": fixture.retry_report_payload,
                "STATEMENT_RECORDS": fixture.retry_records_payload,
                "STATEMENT_INDEX": fixture.retry_index_payload,
            }),
            existing_manifest=write_manifest,
            key=key,
            attempt_id="ATTEMPT-F09-2",
            now="2026-07-20T00:00:01Z",
        )
        issues = issues + tuple(
            PhaseIssueObservation(issue.issue_code, issue.field_path)
            for issue in retry_manifest.detected_issues
        )
    except F09Error as error:
        errors = (type(error).__name__ + ":" + str(error),)
        issues = issues + (PhaseIssueObservation(error.issue_code, error.field_path),)
    return ArtifactPhaseObservation(
        status="VALID" if not errors and not issues else "INVALID",
        runnable=True,
        write_called=write_called,
        inspect_called=inspect_called,
        retry_called=retry_called,
        write_manifest=write_manifest,
        inspection_input=inspection_input,
        inspected_manifest=inspected_manifest,
        retry_manifest=retry_manifest,
        key=key,
        fail_after=fail_after,
        projection_digests=tuple(
            sha256(payload).hexdigest()
            for payload in (
                fixture.retry_report_payload,
                fixture.retry_records_payload,
                fixture.retry_index_payload,
            )
        ),
        errors=errors,
        issues=issues,
    )

# R19 controlling Task 10 adapter source supersedes the unindented R18 construction fragment
# below wherever it conflicts. The implementation must physically place production-only locals
# inside the PRODUCTION_STATEMENT branch; comments do not authorize unconditional evaluation.
# Branch on fixture.binding_protocol before every
# production-only prerequisite or dereference. PRODUCTION_STATEMENT may require statement/set/
# records/RULE material. PREPROD_RUN_TARGET is built only from target_run_id, track/case facts,
# and an extensible nonempty set of authority-valid run artifact records/refs including a usable
# RUN_SNAPSHOT; it passes empty production maps, no production anchor, and never inspects a
# production statement or STATEMENT_RECORDS record. anchor_status affects only production.
#
# Both prior/current feedback keys use one shared canonical serializer. Its RFC8785/JCS object has
# explicit fields: operation, case_id, canonical track value, feedback_id, full source digest,
# normalized feedback items as sorted {feedback_item_id,target_statement_revision_id} pairs,
# statement_set_id or null, policy_id, policy_version, full schema_versions_digest, and full
# contract_digest or null. Every digest is serialized as algorithm/canonicalization/value.
# Blank or duplicate item IDs are rejected; sorting never loses item-to-revision association;
# null remains distinct from a string. canonical_key_digest is lowercase sha256 of these canonical
# UTF-8 bytes, and all IdempotencyKey top-level fields must equal their serialized counterparts.
# T55 changes only one target revision, T56 only policy version, T57 only normalized item set, and
# T58 only source digest; each must observe a different canonical digest and no overwrite.
#
# Both protocol target digests use the Task 8 R19 target-graph serializer over the actual refs and
# records after fixture mutation. They are never input_manifest.digest. Production binds statement,
# set, records projection, selected RULE, authorized policy/version and recomputed ordered-source
# digest. PREPROD binds only run ID and validated extensible run refs. Duplicate refs or any stale
# ref/record identity makes canonical material INVALID before binder dereference.
#
# This Task 8 adapter translates every requested match/anchor stimulus into canonical submission,
# statement-set, or manifest facts before invoking the binder. Binder semantic output is immutable;
# only feedback_binding_id may be cleared afterward for the record-validator negative case.
def normalize_feedback_item_revisions(items: tuple[FeedbackItem, ...]) -> tuple[tuple[str, str | None], ...]:
    pairs = tuple((item.feedback_item_id, item.target_statement_revision_id) for item in items)
    if any(not item_id for item_id, _ in pairs) or len({item_id for item_id, _ in pairs}) != len(pairs):
        raise ValueError("canonical feedback items require unique nonblank IDs")
    return tuple(sorted(pairs, key=lambda pair: pair[0]))


def _digest_ref_material(digest: DigestRef | None) -> object:
    return None if digest is None else {
        "algorithm": digest.algorithm,
        "canonicalization": digest.canonicalization,
        "value": digest.value,
    }


def build_canonical_feedback_key(
    *,
    operation: str,
    case_id: str,
    track: RunTrack,
    feedback_id: str,
    source_digest: DigestRef,
    normalized_item_revisions: tuple[tuple[str, str | None], ...],
    statement_set_id: str | None,
    policy_id: str,
    policy_version: str,
    schema_versions_digest: DigestRef,
    contract_digest: DigestRef | None,
) -> IdempotencyKey:
    material = {
        "operation": operation,
        "case_id": case_id,
        "track": track.value,
        "feedback_id": feedback_id,
        "source_digest": _digest_ref_material(source_digest),
        "feedback_items": [{"feedback_item_id": item_id, "target_statement_revision_id": revision_id} for item_id, revision_id in normalized_item_revisions],
        "statement_set_id": statement_set_id,
        "policy_id": policy_id,
        "policy_version": policy_version,
        "schema_versions_digest": _digest_ref_material(schema_versions_digest),
        "contract_digest": _digest_ref_material(contract_digest),
    }
    canonical_bytes = json.dumps(material, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    canonical_digest = DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(canonical_bytes).hexdigest())
    return IdempotencyKey(operation, case_id, track, source_digest, schema_versions_digest, contract_digest, statement_set_id, feedback_id, canonical_digest)


_PI230_ARTIFACT_ROLES = (
    "REPORT",
    "STATEMENT_INDEX",
    "STATEMENT_RECORDS",
    "RUN_SNAPSHOT",
    "DECISION_RUN",
    "FEEDBACK_ATTACHMENT",
    "MANIFEST",
    "FEEDBACK_SOURCE",
)
_PI230_ARTIFACT_STATES = (
    "NOT_ATTEMPTED",
    "WRITING",
    "WRITTEN_UNVERIFIED",
    "VERIFIED",
    "FAILED",
    "STALE",
    "MISMATCH",
    "SUPERSEDED",
)
_PI230_ATTEMPT_OUTCOMES = ("SUCCEEDED", "FAILED", "UNKNOWN")


def _is_nonblank_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_nullable_nonblank_string(value: object) -> bool:
    return value is None or _is_nonblank_string(value)


def _is_complete_digest_ref(value: object) -> bool:
    return (
        isinstance(value, DigestRef)
        and isinstance(value.algorithm, str)
        and value.algorithm != ""
        and isinstance(value.canonicalization, str)
        and value.canonicalization != ""
        and isinstance(value.value, str)
        and value.value != ""
    )


def _is_nullable_complete_digest_ref(value: object) -> bool:
    return value is None or _is_complete_digest_ref(value)


def _is_complete_preprod_versioned_ref(value: object) -> bool:
    if not isinstance(value, VersionedObjectRef):
        return False
    binding = value.digest_binding
    return (
        _is_nonblank_string(value.object_type)
        and _is_nonblank_string(value.object_id)
        and _is_nullable_nonblank_string(value.revision_id)
        and _is_nonblank_string(value.schema_version)
        and _is_nullable_nonblank_string(value.contract_version)
        and isinstance(binding, DigestPresent)
        and binding.status == "PRESENT"
        and _is_complete_digest_ref(binding.digest)
        and _is_nullable_nonblank_string(value.source_locator_id)
        and _is_nullable_nonblank_string(value.captured_at)
    )


def _is_complete_preprod_attempt(
    attempt: object,
    record: ArtifactRecord,
    attempt_index: int,
) -> bool:
    if not isinstance(attempt, ArtifactWriteAttempt):
        return False
    expected_retry_id = None if attempt_index == 0 else record.attempts[attempt_index - 1].attempt_id
    return (
        _is_nonblank_string(attempt.attempt_id)
        and _is_nonblank_string(attempt.artifact_id)
        and attempt.artifact_id == record.artifact_id
        and _is_nonblank_string(attempt.idempotency_key)
        and isinstance(attempt.attempt_number, int)
        and not isinstance(attempt.attempt_number, bool)
        and attempt.attempt_number > 0
        and attempt.attempt_number == attempt_index + 1
        and (
            attempt.retry_of_attempt_id is None
            if attempt_index == 0
            else _is_nonblank_string(attempt.retry_of_attempt_id)
            and attempt.retry_of_attempt_id == expected_retry_id
        )
        and isinstance(attempt.input_snapshot_refs, tuple)
        and bool(attempt.input_snapshot_refs)
        and all(_is_complete_preprod_versioned_ref(ref) for ref in attempt.input_snapshot_refs)
        and _is_nonblank_string(attempt.started_at)
        and _is_nullable_nonblank_string(attempt.finished_at)
        and isinstance(attempt.outcome, str)
        and attempt.outcome in _PI230_ATTEMPT_OUTCOMES
        and _is_nullable_complete_digest_ref(attempt.observed_digest)
        and _is_nullable_nonblank_string(attempt.error_class)
        and _is_nullable_complete_digest_ref(attempt.error_message_digest)
        and (
            attempt.outcome != "SUCCEEDED"
            or (
                _is_nonblank_string(attempt.finished_at)
                and _is_complete_digest_ref(attempt.observed_digest)
                and attempt.error_class is None
                and attempt.error_message_digest is None
            )
        )
        and (
            attempt.outcome != "FAILED"
            or (
                _is_nonblank_string(attempt.finished_at)
                and _is_nonblank_string(attempt.error_class)
                and _is_complete_digest_ref(attempt.error_message_digest)
            )
        )
    )


def _is_complete_preprod_artifact_record(record: object) -> bool:
    if not isinstance(record, ArtifactRecord):
        return False
    return (
        _is_nonblank_string(record.artifact_id)
        and isinstance(record.artifact_role, str)
        and record.artifact_role in _PI230_ARTIFACT_ROLES
        and isinstance(record.track, RunTrack)
        and _is_nonblank_string(record.case_id)
        and _is_nullable_nonblank_string(record.statement_set_id)
        and _is_nullable_nonblank_string(record.run_id)
        and _is_nonblank_string(record.path_locator)
        and _is_nullable_nonblank_string(record.schema_version)
        and _is_nullable_complete_digest_ref(record.expected_digest)
        and _is_nullable_complete_digest_ref(record.observed_digest)
        and isinstance(record.state, str)
        and record.state in _PI230_ARTIFACT_STATES
        and isinstance(record.attempts, tuple)
        and bool(record.attempts)
        and isinstance(record.issue_ids, tuple)
        and all(isinstance(issue_id, str) for issue_id in record.issue_ids)
        and all(
            _is_complete_preprod_attempt(attempt, record, attempt_index)
            for attempt_index, attempt in enumerate(record.attempts)
        )
    )


def exercise_feedback_binding_phase(
    run_result: F09RunResult,
    fixture: FeedbackFixture,
    boundary_calls: list[BoundaryCall] | None = None,
    *,
    preprod_authority_records: tuple[ArtifactRecord | object, ...] | None = None,
    preprod_authority_refs: tuple[VersionedObjectRef | object, ...] | None = None,
) -> FeedbackPhaseObservation:
    supplied_preprod_records = fixture.preprod_authority_records if preprod_authority_records is None else preprod_authority_records
    supplied_preprod_refs = fixture.preprod_authority_refs if preprod_authority_refs is None else preprod_authority_refs
    authority_records: tuple[ArtifactRecord, ...] = ()
    validated_preprod_refs: tuple[VersionedObjectRef, ...] = ()
    preprod_canonical_case_id: str | None = None
    preprod_canonical_run_id: str | None = None
    authority_record_digest: DigestRef | None = None
    if fixture.binding_protocol == "PREPROD_RUN_TARGET":
        if supplied_preprod_records is None or supplied_preprod_refs is None:
            return FeedbackPhaseObservation(
                status="NOT_RUNNABLE", runnable=False, submission=None,
                input_statement_set=None, input_manifest=None, bindings=(),
                eligibility_records=(), errors=("PREPROD_RUN_AUTHORITY_NOT_SUPPLIED",),
                operation_result=None,
            )
        if (
            not isinstance(supplied_preprod_records, tuple)
            or not supplied_preprod_records
            or not isinstance(supplied_preprod_refs, tuple)
            or not supplied_preprod_refs
            or not all(_is_complete_preprod_artifact_record(record) for record in supplied_preprod_records)
            or not all(_is_complete_preprod_versioned_ref(ref) for ref in supplied_preprod_refs)
        ):
            return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        authority_records = tuple(supplied_preprod_records)
        if len({record.artifact_id for record in authority_records}) != len(authority_records):
            return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        if any(
            len({attempt.attempt_id for attempt in record.attempts}) != len(record.attempts)
            for record in authority_records
        ):
            return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        try:
            validated_preprod_refs = tuple(
                validate_versioned_ref(ref, require_revision=True, require_contract=True).value
                for ref in supplied_preprod_refs
            )
            authority_record_digest = digest_artifact_records(authority_records)
        except (F09Error, TypeError, ValueError):
            return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        if len({(ref.object_type, ref.object_id, ref.revision_id) for ref in validated_preprod_refs}) != len(validated_preprod_refs):
            return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        authority_by_id = {record.artifact_id: record for record in authority_records}
        if set(authority_by_id) != {ref.object_id for ref in validated_preprod_refs}:
            return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        if any(
            ref.object_type != authority_by_id[ref.object_id].artifact_role
            or ref.revision_id != authority_by_id[ref.object_id].run_id
            or ref.schema_version != authority_by_id[ref.object_id].schema_version
            or ref.digest_binding.digest != (authority_by_id[ref.object_id].observed_digest or authority_by_id[ref.object_id].expected_digest)
            for ref in validated_preprod_refs
        ):
            return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        authority_case_ids = {record.case_id for record in authority_records}
        authority_run_ids = {record.run_id for record in authority_records}
        authority_tracks = {record.track for record in authority_records}
        if len(authority_case_ids) != 1 or len(authority_run_ids) != 1 or len(authority_tracks) != 1:
            return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        preprod_canonical_case_id = next(iter(authority_case_ids))
        preprod_canonical_run_id = next(iter(authority_run_ids))
        if next(iter(authority_tracks)) != RunTrack(fixture.target_track):
            return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        if not any(
            record.artifact_role == "RUN_SNAPSHOT"
            and record.state == "VERIFIED"
            and (record.observed_digest is not None or record.expected_digest is not None)
            for record in authority_records
        ):
            return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_RUN_SNAPSHOT_REQUIRED",), (), None)
    if fixture.binding_protocol == "PRODUCTION_STATEMENT" and (
        run_result.statement_set is None or run_result.manifest is None
    ):
        return FeedbackPhaseObservation(
            status="NOT_RUNNABLE", runnable=False, submission=None,
            input_statement_set=None, input_manifest=None, bindings=(),
            eligibility_records=(), errors=("PRODUCTION_FEEDBACK_PREREQUISITE_NOT_PRODUCED",),
            operation_result=None,
        )
    if len(fixture.seven_matches) != 7:
        return FeedbackPhaseObservation(
            "INVALID", False, None, run_result.statement_set, run_result.manifest,
            (), (), ("FEEDBACK_MATCH_DIMENSION_SHAPE_INVALID",), (), None,
        )

    canonical_case_id = (
        run_result.statement_set.case_id
        if fixture.binding_protocol == "PRODUCTION_STATEMENT"
        else preprod_canonical_case_id
    )
    if not isinstance(canonical_case_id, str) or not canonical_case_id:
        return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
    case_fact = canonical_case_id
    if fixture.seven_matches[0] == "MISMATCH":
        case_fact = canonical_case_id + "-MISMATCH"
    if fixture.seven_matches[0] == "UNKNOWN":
        case_fact = ""

    track_fact = RunTrack(fixture.source_track)
    target_track_fact = RunTrack(fixture.target_track)
    source_track_digest = DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(fixture.source_track_digest.encode("utf-8")).hexdigest())
    target_track_digest = DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(fixture.target_track_digest.encode("utf-8")).hexdigest())
    source_track_evidence_ref = VersionedObjectRef("FEEDBACK", fixture.source_track_evidence_id, "TRACK-SOURCE-REV-1", fixture.source_track_schema_version, fixture.source_track_contract_version, DigestPresent("PRESENT", source_track_digest), "SRCLOC-FEEDBACK-TRACK", "2026-07-20T00:00:00Z")
    source_track_parser_ref = VersionedObjectRef("PARSER", fixture.source_track_parser_id, fixture.source_track_parser_version, "parser-ref-v1", fixture.source_track_contract_version, DigestPresent("PRESENT", DigestRef("sha256", "RAW-UTF8", sha256((fixture.source_track_parser_id + ":" + fixture.source_track_parser_version).encode("utf-8")).hexdigest())), None, "2026-07-20T00:00:00Z")
    source_track_binding = TrackSourceBinding("TSB-F09-SOURCE-1", "SUBMISSION_SOURCE", track_fact, fixture.source_track_state, source_track_evidence_ref, source_track_parser_ref, fixture.source_track_schema_version, fixture.source_track_contract_version, source_track_digest, fixture.source_track_reason_codes, "2026-07-20T00:00:00Z")
    target_track_evidence_ref = VersionedObjectRef("STATEMENT_SET", fixture.target_track_evidence_id, "STMT-REV-2", fixture.target_track_schema_version, fixture.target_track_contract_version, DigestPresent("PRESENT", target_track_digest), "SRCLOC-TARGET-TRACK", "2026-07-20T00:00:00Z")
    target_track_parser_ref = VersionedObjectRef("PARSER", fixture.target_track_parser_id, fixture.target_track_parser_version, "parser-ref-v1", fixture.target_track_contract_version, DigestPresent("PRESENT", DigestRef("sha256", "RAW-UTF8", sha256((fixture.target_track_parser_id + ":" + fixture.target_track_parser_version).encode("utf-8")).hexdigest())), None, "2026-07-20T00:00:00Z")
    target_track_source_binding = TrackSourceBinding("TSB-F09-TARGET-1", "BINDING_TARGET", target_track_fact, fixture.target_track_state, target_track_evidence_ref, target_track_parser_ref, fixture.target_track_schema_version, fixture.target_track_contract_version, target_track_digest, fixture.target_track_reason_codes, "2026-07-20T00:00:00Z")

    run_fact = "RUN-F09-1" if fixture.binding_protocol == "PRODUCTION_STATEMENT" else preprod_canonical_run_id
    if fixture.seven_matches[2] == "MISMATCH":
        run_fact = "RUN-F09-MISMATCH"
    if fixture.seven_matches[2] == "UNKNOWN":
        run_fact = ""
    if fixture.seven_matches[2] == "NOT_APPLICABLE":
        run_fact = None

    statement_fact = fixture.target_statement_id
    if fixture.seven_matches[3] == "MISMATCH":
        statement_fact = "STMT-F09-MISMATCH"
    if fixture.seven_matches[3] == "UNKNOWN":
        statement_fact = ""
    if fixture.seven_matches[3] == "NOT_APPLICABLE":
        statement_fact = None

    revision_fact = fixture.target_revision
    if fixture.seven_matches[4] == "MISMATCH":
        revision_fact = "STMT-REV-MISMATCH"
    if fixture.seven_matches[4] == "UNKNOWN":
        revision_fact = ""
    if fixture.seven_matches[4] == "NOT_APPLICABLE":
        revision_fact = None

    statement_set_fact = (
        run_result.statement_set.statement_set_id
        if fixture.binding_protocol == "PRODUCTION_STATEMENT"
        else None
    )
    if fixture.binding_protocol == "PRODUCTION_STATEMENT" and fixture.seven_matches[5] == "MISMATCH":
        statement_set_fact = run_result.statement_set.statement_set_id + "-MISMATCH"
    if fixture.seven_matches[5] == "UNKNOWN":
        statement_set_fact = ""
    if fixture.seven_matches[5] == "NOT_APPLICABLE":
        statement_set_fact = ""
    if len(fixture.item_ids) < 1:
        return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("FEEDBACK_ITEM_SHAPE_INVALID",), (), None)
    padded_item_ids = fixture.item_ids + ("FBI-PADDING-1", "FBI-PADDING-2")
    if len(padded_item_ids) < 2:
        return FeedbackPhaseObservation("INVALID", False, None, None, None, (), (), ("FEEDBACK_ITEM_PADDING_SHAPE_INVALID",), (), None)
    item_1 = FeedbackItem(padded_item_ids[0], "FB-F09-1" if fixture.submission_complete else "", "/feedback/items/0", statement_fact, revision_fact, run_fact, None, "CONFIRMED", "bounded fixture feedback", "VALID", ())
    item_2 = FeedbackItem(padded_item_ids[1], "FB-F09-1" if fixture.submission_complete else "", "/feedback/items/1", statement_fact, revision_fact, run_fact, None, "CONFIRMED", "bounded fixture feedback", "VALID", ())
    submission = FeedbackSubmission(
        feedback_id="FB-F09-1" if fixture.submission_complete else "",
        case_id=case_fact,
        track=track_fact,
        track_source_binding=source_track_binding,
        source_snapshot_ref=SnapshotRef("SNAP-F09-FEEDBACK-1", "FEEDBACK", ("/feedback",), "feedback-v1", "PI230-V1", DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(fixture.source_digest.encode("utf-8")).hexdigest()), "2026-07-20T00:00:00Z", "IMMUTABLE"),
        parser_id="F09FixtureParser",
        parser_version="1",
        feedback_items=(item_1, item_2)[:len(fixture.item_ids)],
        content_digest=DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(b"DG-FEEDBACK-A").hexdigest()),
        captured_at="2026-07-20T00:00:00Z",
    )
    prior_submission = replace(
        submission,
        source_snapshot_ref=replace(
            submission.source_snapshot_ref,
            content_digest=DigestRef(
                "sha256", "RFC8785-JCS-UTF8",
                sha256(fixture.prior_source_digest.encode("utf-8")).hexdigest(),
            ),
        ),
    )
    statement_refs: Mapping[tuple[str, str], VersionedObjectRef] = MappingProxyType({})
    statement_set_ref: VersionedObjectRef | None = None
    records_projection_refs: Mapping[str, VersionedObjectRef] = MappingProxyType({})
    records_projection_records: Mapping[str, StatementProjectionRecord] = MappingProxyType({})
    anchor_selections: Mapping[tuple[str, str], AnchorSelectionRecord] = MappingProxyType({})
    preprod_target_refs: Mapping[str, tuple[VersionedObjectRef, ...]] = MappingProxyType({})
    selection_for_digest: AnchorSelectionRecord | None = None
    target_run_id_for_digest: str | None = None
    if fixture.binding_protocol == "PRODUCTION_STATEMENT":
        if not run_result.statement_set.statements or not run_result.manifest.records:
            return FeedbackPhaseObservation("INVALID", False, submission, run_result.statement_set, run_result.manifest, (), (), ("PRODUCTION_TARGET_SHAPE_INVALID",), (), None)
        target_statement = replace(run_result.statement_set.statements[0], statement_revision_id=revision_fact)
        input_statement_set = replace(run_result.statement_set, statements=(target_statement,))
        base_record = run_result.manifest.records[0]
        observed_digest = base_record.expected_digest if fixture.seven_matches[6] != "UNKNOWN" else None
        if fixture.seven_matches[6] == "MISMATCH":
            observed_digest = DigestRef("sha256", "RAW-UTF8", sha256(b"feedback-mismatch").hexdigest())
        anchor_record = replace(base_record, artifact_role="STATEMENT_RECORDS", case_id=input_statement_set.case_id, statement_set_id=statement_set_fact, run_id=None, schema_version=target_statement.statement_schema_version, observed_digest=observed_digest, state="VERIFIED")
        input_manifest = replace(run_result.manifest, records=((anchor_record,) if fixture.anchor_status == "MAPPED" else ()))
        statement_ref = VersionedObjectRef("STATEMENT", target_statement.statement_id, target_statement.statement_revision_id, target_statement.statement_schema_version, "PI230-V1", DigestPresent("PRESENT", target_statement.content_digest), target_statement.source_locator_ids[0] if target_statement.source_locator_ids else None, input_statement_set.generated_at)
        statement_set_ref = VersionedObjectRef("STATEMENT_SET", input_statement_set.statement_set_id, None, input_statement_set.statement_schema_version, "PI230-V1", DigestPresent("PRESENT", input_statement_set.content_digest), None, input_statement_set.generated_at)
        records_ref = VersionedObjectRef("STATEMENT_RECORDS", anchor_record.artifact_id, target_statement.statement_revision_id, anchor_record.schema_version, "PI230-V1", DigestPresent("PRESENT", anchor_record.observed_digest or anchor_record.expected_digest), anchor_record.path_locator, input_statement_set.generated_at)
        projection = StatementProjectionRecord("PROJ-RECORDS-F09-1", "STATEMENT_RECORDS", input_statement_set.statement_set_id, target_statement.statement_id, target_statement.statement_revision_id, target_statement.content_digest, records_ref, "TRANSFORM-RECORDS-F09-1", "LOSSY", (), (), ())
        selected_rule_ref = VersionedObjectRef("RULE", "V-RULE-ANCHOR", "RULE-REV-1", "rule-v1", "PI300-V1", DigestPresent("PRESENT", DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(b"V-RULE-ANCHOR").hexdigest())), "SRCLOC-RULE-ANCHOR", input_statement_set.generated_at)
        selection_for_digest = AnchorSelectionRecord("ANCHOR-SELECTION-F09-1", target_statement.statement_id, target_statement.statement_revision_id, (selected_rule_ref,), selected_rule_ref, (), "PRODUCTION-STATEMENT-ELIGIBILITY", "policy-v1", digest_ordered_rule_refs((selected_rule_ref,)), "LOSSY", "SELECTED_ANCHOR_ONLY", ())
        statement_refs = MappingProxyType({(target_statement.statement_id, target_statement.statement_revision_id): statement_ref})
        records_projection_refs = MappingProxyType({anchor_record.artifact_id: records_ref})
        records_projection_records = MappingProxyType({anchor_record.artifact_id: projection})
        anchor_selections = MappingProxyType({(target_statement.statement_id, target_statement.statement_revision_id): selection_for_digest})
        target_refs_for_digest = (statement_ref, statement_set_ref, records_ref)
    else:
        input_statement_set = None
        if authority_record_digest is None or preprod_canonical_run_id is None:
            return FeedbackPhaseObservation("INVALID", False, submission, None, None, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        authority_key = IdempotencyKey(
            "BIND_FEEDBACK", canonical_case_id, target_track_fact, authority_record_digest,
            authority_record_digest, None, None, submission.feedback_id, authority_record_digest,
        )
        input_manifest = ArtifactSetManifest(
            "MANIFEST:CALLER-PREPROD-AUTHORITY", authority_key, authority_records,
            "COMPLETE_VERIFIED", authority_record_digest, (),
        )
        preprod_target_refs = MappingProxyType({preprod_canonical_run_id: validated_preprod_refs})
        target_run_id_for_digest = run_fact
        target_refs_for_digest = validated_preprod_refs
    prior_source_digest = prior_submission.source_snapshot_ref.content_digest
    current_source_digest = submission.source_snapshot_ref.content_digest
    schema_versions_digest = DigestRef("sha256", "RFC8785-JCS-UTF8", sha256((fixture.source_track_schema_version + ":" + fixture.target_track_schema_version).encode("utf-8")).hexdigest())
    contract_digest = DigestRef("sha256", "RFC8785-JCS-UTF8", sha256((fixture.source_track_contract_version + ":" + fixture.target_track_contract_version).encode("utf-8")).hexdigest())
    normalized_item_revisions = normalize_feedback_item_revisions(submission.feedback_items)
    prior_item_revisions = (("FBI-1", "STMT-REV-2"),)
    policy_id = "PRODUCTION-STATEMENT-ELIGIBILITY"
    prior_policy_version = fixture.prior_policy_version
    prior_key = build_canonical_feedback_key(
        operation="BIND_FEEDBACK", case_id=submission.case_id, track=submission.track,
        feedback_id=submission.feedback_id, source_digest=prior_source_digest,
        normalized_item_revisions=prior_item_revisions,
        statement_set_id=(input_statement_set.statement_set_id if input_statement_set is not None else None),
        policy_id=policy_id, policy_version=prior_policy_version,
        schema_versions_digest=schema_versions_digest, contract_digest=contract_digest,
    )
    current_key = build_canonical_feedback_key(
        operation="BIND_FEEDBACK", case_id=submission.case_id, track=submission.track,
        feedback_id=submission.feedback_id, source_digest=current_source_digest,
        normalized_item_revisions=normalized_item_revisions,
        statement_set_id=(input_statement_set.statement_set_id if input_statement_set is not None else None),
        policy_id=policy_id, policy_version="policy-v1",
        schema_versions_digest=schema_versions_digest, contract_digest=contract_digest,
    )
    prior_target_refs = target_refs_for_digest
    prior_selection_for_digest = selection_for_digest
    try:
        if fixture.target_graph_relation == "CHANGED":
            first_ref = validate_versioned_ref(target_refs_for_digest[0], require_revision=True, require_contract=True).value
            prior_revision = str(first_ref.revision_id) + "-PRIOR"
            prior_target_refs = (replace(first_ref, revision_id=prior_revision),) + target_refs_for_digest[1:]
            if fixture.binding_protocol == "PRODUCTION_STATEMENT":
                prior_selection_for_digest = replace(selection_for_digest, target_statement_revision_id=prior_revision)
        prior_target_digest = digest_protocol_target_graph(fixture.binding_protocol, prior_target_refs, target_run_id=target_run_id_for_digest, selection=prior_selection_for_digest)
        current_target_digest = digest_protocol_target_graph(fixture.binding_protocol, target_refs_for_digest, target_run_id=target_run_id_for_digest, selection=selection_for_digest)
    except (F09Error, TypeError, ValueError):
        if fixture.binding_protocol == "PREPROD_RUN_TARGET":
            return FeedbackPhaseObservation("INVALID", False, submission, None, input_manifest, (), (), ("PREPROD_TARGET_GRAPH_INVALID",), (), None)
        raise
    errors: tuple[str, ...] = ()
    issues: tuple[PhaseIssueObservation, ...] = ()
    validated_bindings: tuple[FeedbackBinding, ...] = ()
    eligibility_records: tuple[LearningEligibility, ...] = ()
    operation_result: FeedbackOperationResult | None = None
    try:
        if boundary_calls is not None:
            boundary_calls.append(BoundaryCall("VALIDATE_FEEDBACK_BINDING", submission.track))
        operation_result = validate_feedback_binding(
            submission,
            (input_statement_set if fixture.binding_protocol == "PRODUCTION_STATEMENT" else None),
            input_manifest,
            prior_key=prior_key,
            current_key=current_key,
            prior_target_digest=prior_target_digest,
            current_target_digest=current_target_digest,
            target_track_source_binding=target_track_source_binding,
            statement_refs=statement_refs,
            statement_set_ref=statement_set_ref,
            records_projection_refs=records_projection_refs,
            records_projection_records=records_projection_records,
            anchor_selections=anchor_selections,
            preprod_target_refs=preprod_target_refs,
            governing_statement_contract_version="PI230-V1",
            governing_statement_set_contract_version="PI230-V1",
            governing_statement_records_contract_version="PI230-V1",
            governing_rule_contract_version="PI300-V1",
        )
        issues = issues + tuple(PhaseIssueObservation(issue.issue_code, issue.field_path) for issue in operation_result.detected_issues)
        returned_bindings = operation_result.bindings
        issues = issues + tuple(
            PhaseIssueObservation(issue.issue_code, issue.field_path)
            for binding in returned_bindings
            for issue in binding.detected_issues
        )
        canonical_key_changed = prior_key.canonical_key_digest != current_key.canonical_key_digest
        if fixture.target_graph_relation == "CHANGED" and not canonical_key_changed:
            if (
                operation_result.operation_disposition != "TARGET_MISMATCH"
                or operation_result.overwrite_permitted is not False
                or operation_result.detected_issues != (
                    DetectedIssue("IDEMPOTENCY.DIGEST_MISMATCH", "/feedback/source_snapshot_ref"),
                )
            ):
                raise AssertionError("same-key/different-target must return a no-overwrite TARGET_MISMATCH receipt")
        elif canonical_key_changed:
            if (
                operation_result.operation_disposition != "NEW_OPERATION"
                or operation_result.source_identity_relation != (
                    "CHANGED" if fixture.prior_source_digest != fixture.source_digest else "SAME"
                )
                or operation_result.prior_key != prior_key
                or operation_result.current_key != current_key
                or operation_result.overwrite_permitted is not False
                or operation_result.detected_issues
            ):
                raise AssertionError("every changed canonical key must return a no-overwrite NEW_OPERATION receipt")
        elif operation_result.operation_disposition != "REUSED_OPERATION":
            raise AssertionError("same canonical feedback key and target must reuse its operation identity")
        if len(returned_bindings) != len(fixture.item_ids):
            raise AssertionError("feedback binder cardinality differs from canonical item graph")
        if len(returned_bindings) < 1:
            raise AssertionError("feedback binder returned no canonical binding")
        base_binding_1 = returned_bindings[0]
        if base_binding_1.binding_protocol != fixture.binding_protocol:
            raise AssertionError("feedback binder protocol differs from canonical target facts")
        returned_dimensions = (
            base_binding_1.case_match,
            base_binding_1.track_match,
            base_binding_1.run_match,
            base_binding_1.statement_match,
            base_binding_1.revision_match,
            base_binding_1.statement_set_match,
            base_binding_1.artifact_digest_match,
        )
        expected_track_match = "UNKNOWN"
        if (
            fixture.source_track_state == "AVAILABLE_RESOLVED"
            and fixture.target_track_state == "AVAILABLE_RESOLVED"
        ):
            expected_track_match = (
                "MATCH" if track_fact == target_track_fact else "MISMATCH"
            )
        expected_dimensions = (
            fixture.seven_matches[0],
            expected_track_match,
            fixture.seven_matches[2],
            fixture.seven_matches[3],
            fixture.seven_matches[4],
            fixture.seven_matches[5],
            fixture.seven_matches[6],
        )
        if returned_dimensions != expected_dimensions:
            raise AssertionError("feedback binder seven-dimension result differs from canonical input facts")
        expected_reason_codes = {
            "AVAILABLE_RESOLVED": (),
            "SOURCE_MISSING": ("TRACK_SOURCE_MISSING",),
            "UNPARSABLE": ("TRACK_SOURCE_UNPARSABLE",),
            "AMBIGUOUS": ("TRACK_SOURCE_AMBIGUOUS",),
            "INTEGRITY_FAILED": ("TRACK_SOURCE_INTEGRITY_FAILED",),
        }
        bindings_well_formed = (
            fixture.source_track_reason_codes == expected_reason_codes[fixture.source_track_state]
            and fixture.target_track_reason_codes == expected_reason_codes[fixture.target_track_state]
            and fixture.source_track_evidence_id != ""
            and fixture.target_track_evidence_id != ""
            and fixture.source_track_parser_id != ""
            and fixture.target_track_parser_id != ""
            and fixture.source_track_parser_version != ""
            and fixture.target_track_parser_version != ""
            and fixture.source_track_schema_version != ""
            and fixture.target_track_schema_version != ""
            and fixture.source_track_contract_version != ""
            and fixture.target_track_contract_version != ""
            and fixture.source_track_digest != ""
            and fixture.target_track_digest != ""
        )
        protocol_dimensions = {
            "PRODUCTION_STATEMENT": {
                "required": (0, 1, 3, 4, 5, 6),
                "allowed_not_applicable": (2,),
            },
            "PREPROD_RUN_TARGET": {
                "required": (0, 1, 2, 6),
                "allowed_not_applicable": (3, 4, 5),
            },
        }
        protocol_rule = protocol_dimensions[fixture.binding_protocol]
        required_dimensions_satisfied = all(
            returned_dimensions[index] == "MATCH"
            for index in protocol_rule["required"]
        )
        allowed_not_applicable_satisfied = all(
            returned_dimensions[index] == "NOT_APPLICABLE"
            for index in protocol_rule["allowed_not_applicable"]
        )
        canonical_input_invalid = (
            fixture.source_track_state == "INTEGRITY_FAILED"
            or fixture.target_track_state == "INTEGRITY_FAILED"
            or not fixture.submission_complete
            or not bindings_well_formed
        )
        canonical_input_ambiguous = (
            fixture.source_track_state == "AMBIGUOUS"
            or fixture.target_track_state == "AMBIGUOUS"
        )
        production_anchor_unmapped = (
            fixture.binding_protocol == "PRODUCTION_STATEMENT"
            and fixture.anchor_status != "MAPPED"
        )
        canonical_input_unbound = (
            fixture.source_track_state in ("SOURCE_MISSING", "UNPARSABLE")
            or fixture.target_track_state in ("SOURCE_MISSING", "UNPARSABLE")
            or not required_dimensions_satisfied
            or not allowed_not_applicable_satisfied
            or production_anchor_unmapped
        )
        if canonical_input_invalid:
            expected_status = "INVALID"
        elif canonical_input_ambiguous:
            expected_status = "AMBIGUOUS"
        elif canonical_input_unbound:
            expected_status = "UNBOUND"
        elif (
            fixture.source_track_state == "AVAILABLE_RESOLVED"
            and fixture.target_track_state == "AVAILABLE_RESOLVED"
            and required_dimensions_satisfied
            and allowed_not_applicable_satisfied
            and not production_anchor_unmapped
        ):
            expected_status = "BOUND"
        else:
            raise AssertionError("feedback aggregate oracle did not exhaust PI-230 first-match states")
        if base_binding_1.status != expected_status:
            raise AssertionError("feedback binder aggregate status differs from PI-230 priority table")
        # Contract-consistency assertion only: the preceding seven-dimension and aggregate-status
        # comparisons verify that returned canonical values agree with canonical call inputs.
        # They do not create, select, filter, map, validate, or supplement an expected issue pair.
        # Positive issue evidence remains exclusively binding.detected_issues,
        # eligibility.detected_issues, or one caught typed F09Error from the production port.
        binding_1 = replace(base_binding_1, feedback_binding_id=(base_binding_1.feedback_binding_id if fixture.binding_complete else ""))
        if boundary_calls is not None:
            boundary_calls.append(BoundaryCall("VALIDATE_FEEDBACK_BINDING_RECORD", submission.track))
        validate_feedback_binding_record(binding_1)
        if boundary_calls is not None:
            boundary_calls.append(BoundaryCall("EVALUATE_LEARNING_ELIGIBILITY", submission.track))
        eligibility_1 = evaluate_learning_eligibility(
            binding_1,
            policy_id="PRODUCTION-STATEMENT-ELIGIBILITY",
            policy_version="policy-v1",
            evaluated_at="2026-07-20T00:00:01Z",
        )
        issues = issues + tuple(
            PhaseIssueObservation(issue.issue_code, issue.field_path)
            for issue in eligibility_1.detected_issues
        )
        eligibility_1 = replace(
            eligibility_1,
            eligibility_id=(eligibility_1.eligibility_id if fixture.eligibility_complete else ""),
        )
        if boundary_calls is not None:
            boundary_calls.append(BoundaryCall("VALIDATE_LEARNING_ELIGIBILITY", submission.track))
        validate_learning_eligibility(eligibility_1)
        validated_bindings = (binding_1,)
        eligibility_records = (eligibility_1,)
        if len(returned_bindings) == 2:
            base_binding_2 = returned_bindings[1]
            binding_2 = replace(base_binding_2, feedback_binding_id=(base_binding_2.feedback_binding_id if fixture.binding_complete else ""))
            if boundary_calls is not None:
                boundary_calls.append(BoundaryCall("VALIDATE_FEEDBACK_BINDING_RECORD", submission.track))
            validate_feedback_binding_record(binding_2)
            if boundary_calls is not None:
                boundary_calls.append(BoundaryCall("EVALUATE_LEARNING_ELIGIBILITY", submission.track))
            eligibility_2 = evaluate_learning_eligibility(
                binding_2,
                policy_id="PRODUCTION-STATEMENT-ELIGIBILITY",
                policy_version="policy-v1",
                evaluated_at="2026-07-20T00:00:01Z",
            )
            issues = issues + tuple(
                PhaseIssueObservation(issue.issue_code, issue.field_path)
                for issue in eligibility_2.detected_issues
            )
            eligibility_2 = replace(
                eligibility_2,
                eligibility_id=(eligibility_2.eligibility_id if fixture.eligibility_complete else ""),
            )
            if boundary_calls is not None:
                boundary_calls.append(BoundaryCall("VALIDATE_LEARNING_ELIGIBILITY", submission.track))
            validate_learning_eligibility(eligibility_2)
            validated_bindings = (binding_1, binding_2)
            eligibility_records = (eligibility_1, eligibility_2)
    except F09Error as error:
        errors = (type(error).__name__ + ":" + str(error),)
        issues = issues + (PhaseIssueObservation(error.issue_code, error.field_path),)
    return FeedbackPhaseObservation(
        status="VALID" if not errors and not issues else "INVALID",
        runnable=True,
        submission=submission,
        input_statement_set=input_statement_set,
        input_manifest=input_manifest,
        bindings=validated_bindings,
        eligibility_records=eligibility_records,
        errors=errors,
        issues=issues,
        operation_result=operation_result,
    )

BASELINE_GATE = GateFixture("SATISFIED", "SATISFIED", "SATISFIED", "SATISFIED", "SATISFIED", "SATISFIED", (), (), ("ALLOCATION", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "TEMPORAL"), ("ALLOCATION", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "TEMPORAL"), "REF-GATE-F09-V1", ("REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1"), ("DG-ALLOC", "DG-RISK", "DG-REAL", "DG-ATTR", "DG-SOURCE", "DG-TEMP"), ("REALITY_FACT",), True)
BASELINE_DECLARATIONS = DeclarationFixture("RESOLVED", None, False, "OUTPUT_PRECISION", "DG-PRECISION-V1", "PI210-V1", "VALIDATION_PLAN", "DG-VALIDATION-V1", None, True, "DG-PRECISION-V1", "DG-PRECISION-V1")
BASELINE_DECISION = DecisionFixture("OUTPUT", "OutputPayload", (), (), ("GR-ALLOCATION", "GR-RISK", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL"), ("PR-REALITY-OUTPUT",), ("DISP-F09-INCLUDED",), ("CAND-F09",), ("DISP-F09-INCLUDED",), (), False, False)
BASELINE_PARTICIPATION = ParticipationFixture(("ROLE-ALLOCATION", "ROLE-RISK", "ROLE-REALITY", "ROLE-ATTRIBUTION", "ROLE-SOURCE", "ROLE-TEMPORAL"), "PR-REALITY-OUTPUT", "OUTPUT", True, "DEC-F09-BASE")
BASELINE_ROOT_TIMING = RootTimingFixture("SATISFIED", None, None, "SATISFIED", None, None, False)
BASELINE_TRACE = TraceFixture(True, True, ("GR-ALLOCATION", "GR-RISK", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL", "PR-REALITY-OUTPUT", "DISP-F09-INCLUDED", "RTC-ROOT", "RTC-TIMING"), ("RULE-F09-ANCHOR",), "LOSSLESS", 6, True, "REFERENCE_ONLY_NOT_IMPLEMENTATION_PROOF", "bounded outcome: allocation capital present", ())
BASELINE_ARTIFACTS = ArtifactFixture("SUCCEEDED", "SUCCEEDED", "STMT-REV-2", "DG-ARTIFACT-V2", "DG-ARTIFACT-V2", ("VERIFIED",), "STMT-REV-2", None, "IDEM-KEY-A", b"F09 staged report\n", b"DG-ARTIFACT-V2", b"STMT-REV-2")
PREPROD_AUTHORITY_DIGEST = DigestRef("sha256", "RFC8785-JCS-UTF8", sha256(b"PI230-PREPROD-RUN-AUTHORITY").hexdigest())
PREPROD_AUTHORITY_INPUT_REF = VersionedObjectRef(
    "RUN_INPUT_SNAPSHOT", "SNAP-PREPROD-AUTHORITY-1", "SNAP-REV-1", "run-input-snapshot-v1", "PI230-V1",
    DigestPresent("PRESENT", PREPROD_AUTHORITY_DIGEST), "preprod/input-snapshot.json", "2026-07-20T00:00:00Z",
)
PREPROD_AUTHORITY_ATTEMPT = ArtifactWriteAttempt(
    "ATTEMPT-PREPROD-AUTHORITY-1", "ART-RUN-SNAPSHOT-1", "PREPROD-AUTHORITY-KEY",
    1, None, (PREPROD_AUTHORITY_INPUT_REF,), "2026-07-20T00:00:00Z", "2026-07-20T00:00:00Z", "SUCCEEDED",
    PREPROD_AUTHORITY_DIGEST, None, None,
)
BASELINE_PREPROD_AUTHORITY_RECORDS = (
    ArtifactRecord(
        "ART-RUN-SNAPSHOT-1", "RUN_SNAPSHOT", RunTrack.STAGED_L6, "CASE-F09-PREPROD-AUTHORITY",
        None, "RUN-F09-1", "preprod/RUN_SNAPSHOT.json", "preprod-artifact-v1",
        PREPROD_AUTHORITY_DIGEST, PREPROD_AUTHORITY_DIGEST, "VERIFIED", (PREPROD_AUTHORITY_ATTEMPT,), (),
    ),
    ArtifactRecord(
        "ART-DECISION-RUN-1", "DECISION_RUN", RunTrack.STAGED_L6, "CASE-F09-PREPROD-AUTHORITY",
        None, "RUN-F09-1", "preprod/DECISION_RUN.json", "preprod-artifact-v1",
        PREPROD_AUTHORITY_DIGEST, PREPROD_AUTHORITY_DIGEST, "VERIFIED",
        (replace(PREPROD_AUTHORITY_ATTEMPT, attempt_id="ATTEMPT-PREPROD-DECISION-1", artifact_id="ART-DECISION-RUN-1"),), (),
    ),
)
BASELINE_PREPROD_AUTHORITY_REFS = tuple(
    VersionedObjectRef(
        record.artifact_role, record.artifact_id, record.run_id, record.schema_version, "PI230-V1",
        DigestPresent("PRESENT", record.observed_digest), record.path_locator, "2026-07-20T00:00:00Z",
    )
    for record in BASELINE_PREPROD_AUTHORITY_RECORDS
)
BASELINE_FEEDBACK = FeedbackFixture(
    "PRODUCTION_STATEMENT", "STMT-F09-1", "STMT-REV-2", "MAPPED", "SAME",
    ("MATCH", "MATCH", "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "MATCH"),
    RunTrack.STAGED_L6, "AVAILABLE_RESOLVED", "SNAP-F09-FEEDBACK-1",
    "F09FixtureParser", "1", "track-source-v1", "PI230-V1", "DG-TRACK-SOURCE-A", (),
    RunTrack.STAGED_L6, "AVAILABLE_RESOLVED", "STMTSET-F09-1",
    "F09TargetTrackResolver", "1", "track-source-v1", "PI230-V1", "DG-TRACK-TARGET-A", (),
    "policy-v1", ("FBI-1",), "DG-FEEDBACK-A", "DG-FEEDBACK-A", True, True, True,
    BASELINE_PREPROD_AUTHORITY_RECORDS, BASELINE_PREPROD_AUTHORITY_REFS,
)
BASELINE_SOURCE = SourceFixture(True, "REALITY_FACT", "SOURCE-STATE-1", "/value", ("level", "position", "as_of"), "SOURCE-EVENT-1", "/value", ("level", "change", "interval/start", "interval/end", "interval/start_inclusive", "interval/end_inclusive"), ("axis", "action", "object", "tense"), "PI-300-F09-SOURCE-SNAPSHOT-V1", "reality-fact-source-snapshot.v1", "pi-300-f09-source-snapshots-v1", "67517fe2d04fb0fe580e031643dab2ad53fcdb8c90707ba4d496c316dd87f5e7", "2026-07-19T00:00:00Z", "67517fe2d04fb0fe580e031643dab2ad53fcdb8c90707ba4d496c316dd87f5e7", True, "IMMUTABLE_JSON_SNAPSHOT", True)

def baseline_scenario_bundle(tmp_path: Path) -> ScenarioBundle:
    return ScenarioBundle(
        request=F09RunRequest(case_id="CASE-F09-VERTICAL", mode="STAGED_AUDIT", enable_f09=True, markdown_path=Path("engine/contracts/12-real-world-function-evidence-cards-v1.md"), snapshot_path=Path("plans/production-implementation-pi-300-f09-source-snapshots-v1.json"), artifact_root=tmp_path / "f09-artifacts", now="2026-07-20T00:00:00Z"),
        gate=BASELINE_GATE,
        declarations=BASELINE_DECLARATIONS,
        decision=BASELINE_DECISION,
        participation=BASELINE_PARTICIPATION,
        root_timing=BASELINE_ROOT_TIMING,
        trace=BASELINE_TRACE,
        artifacts=BASELINE_ARTIFACTS,
        feedback=BASELINE_FEEDBACK,
        source=BASELINE_SOURCE,
    )

def execute_scenario(scenario: VerticalScenario, tmp_path: Path) -> ScenarioExecution:
    bundle = baseline_scenario_bundle(tmp_path)
    mutated = scenario.mutate(bundle)
    decision_inputs = materialize_f09_decision_inputs(mutated)
    boundary_calls: list[BoundaryCall] = []
    boundary_calls.append(BoundaryCall("RUN_F09_SLICE", None))
    run_result = run_f09_slice(
        mutated.request,
        gate_inputs=decision_inputs.gate_inputs,
        competition_input=decision_inputs.competition_input,
        root_input=decision_inputs.root_input,
        timing_input=decision_inputs.timing_input,
    )
    trace_phase = exercise_trace_validation_phase(run_result, mutated.trace, mutated.source, boundary_calls)
    artifact_phase = exercise_artifact_lifecycle_phase(run_result, mutated.artifacts, tmp_path, boundary_calls)
    feedback_phase = exercise_feedback_binding_phase(
        run_result,
        mutated.feedback,
        boundary_calls,
        preprod_authority_records=mutated.feedback.preprod_authority_records,
        preprod_authority_refs=mutated.feedback.preprod_authority_refs,
    )
    run_invalid = (
        any(observation.issue_codes != () for observation in run_result.observations)
        or (
            run_result.decision is not None
            and run_result.decision.action_envelope.structural_validity == "INVALID"
        )
    )
    phase_invalid = trace_phase.status == "INVALID" or artifact_phase.status == "INVALID" or feedback_phase.status == "INVALID"
    return ScenarioExecution(
        baseline_bundle=bundle,
        mutated_bundle=mutated,
        decision_inputs=decision_inputs,
        run_result=run_result,
        trace_phase=trace_phase,
        artifact_phase=artifact_phase,
        feedback_phase=feedback_phase,
        overall_status="INVALID" if run_invalid or phase_invalid else "VALID",
        boundary_calls=tuple(boundary_calls),
    )

# The following 104 top-level mutators are literal; only T01 is the identity mutator.
def mutate_t01(bundle: ScenarioBundle) -> ScenarioBundle:
    return bundle

def mutate_t02(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, risk_state="UNKNOWN", risk_reason_codes=("ISSUE-RISK-UNKNOWN",)), decision=replace(bundle.decision, selected_action="CONDITIONAL", payload_type="ConditionalPayload", payload_issue_ids=("ISSUE-RISK-UNKNOWN",)))

def mutate_t03(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, attribution_state="MISSING"), decision=replace(bundle.decision, selected_action="ASK", payload_type="AskPayload", question_paths=("/gate/ATTRIBUTION",)))

def mutate_t04(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, selected_action="ABSTAIN", payload_type="AbstainPayload", candidate_ids=("CAND-F09",), dispositions=("DISP-F09-UNRESOLVED",), disposition_refs=("DISP-F09-UNRESOLVED",)))

def mutate_t05(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, attribution_state="CONFLICT"), decision=replace(bundle.decision, selected_action="HUMAN_REVIEW", payload_type="HumanReviewPayload", payload_issue_ids=("GATE.FIELD_CONFLICT",)))

def mutate_t06(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, precision_presence="RESOLVED", precision_value=None))

def mutate_t07(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, precision_value=None, precision_unresolved=True))

def mutate_t08(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, precision_presence="ABSENT"))

def mutate_t09(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, risk_state="UNKNOWN", risk_reason_codes=("GATE.STATE_UNKNOWN",)))

def mutate_t10(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, locator_available=False))

def mutate_t11(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, precision_presence="UNRESOLVABLE", attempted_digest="DG-PRECISION-DRIFT"))

def mutate_t12(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, precision_presence="NOT_APPLICABLE"))

def mutate_t13(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, reality_track="CHART_STRUCTURE"), gate=replace(bundle.gate, reality_state="MISSING", supporting_evidence_tracks=("CHART_STRUCTURE",)))

def mutate_t14(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, reality_track="UNVERIFIED_HYPOTHESIS"), gate=replace(bundle.gate, reality_state="MISSING", supporting_evidence_tracks=("UNVERIFIED_HYPOTHESIS",)))

def mutate_t15(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, candidate_ids=("CAND-F09",), dispositions=("DISP-F09-UNRESOLVED-F08-STRONG",)))

def mutate_t16(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, allocation_state="MISSING"), decision=replace(bundle.decision, consequence_only=True))

def mutate_t17(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, root_timing=replace(bundle.root_timing, timing_rewrites_root=True, root_state="VIOLATED"))

def mutate_t18(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, precision_type="VALIDATION_PLAN"))

def mutate_t19(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, statement_precision_digest="DG-PRECISION-STATEMENT-DRIFT"))

def mutate_t20(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, trace=replace(bundle.trace, rule_ref_ids=("RULE-F09-ANCHOR", "RULE-F09-DROPPED-1", "RULE-F09-DROPPED-2"), transformation_fidelity="LOSSY"))

def mutate_t21(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, records_write_outcome="FAILED"))

def mutate_t22(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, index_write_outcome="FAILED"))

def mutate_t23(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, index_revision="STMT-REV-1"))

def mutate_t24(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, observed_digest="DG-ARTIFACT-CONFLICT"))

def mutate_t25(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, feedback=replace(bundle.feedback, target_statement_id="STMT-UNKNOWN", anchor_status="UNMAPPED", source_track=RunTrack.V5_V6_PREPROD, seven_matches=("MISMATCH", "MISMATCH", "MISMATCH", "MISMATCH", "MISMATCH", "MISMATCH", "MISMATCH")))

def mutate_t26(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, feedback=replace(bundle.feedback, target_revision="STMT-REV-1"))

def mutate_t27(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, retry_key_digest="IDEM-KEY-A", retry_report_payload=b"F09 staged report\n", retry_records_payload=b"DG-ARTIFACT-V2", retry_index_payload=b"STMT-REV-2"))

def mutate_t28(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, retry_key_digest="IDEM-KEY-A", retry_report_payload=b"F09 staged report\n", retry_records_payload=b"DG-PAYLOAD-CONFLICT", retry_index_payload=b"STMT-REV-2"))

def mutate_t29(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, feedback=replace(bundle.feedback, source_track=RunTrack.V5_V6_PREPROD))

def mutate_t30(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, trace=replace(bundle.trace, card_runtime_status="IMPLEMENTED"))

def mutate_t31(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, candidate_ids=("CAND-F09",), f08_runtime_objects=()))

def mutate_t32(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, candidate_ids=("CAND-F09", "CAND-F08"), f08_runtime_objects=("CAND-F08", "ACTION-F08", "STMT-F08")))

def mutate_t33(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, require_two_candidates=True))

def mutate_t34(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, validation_type="VALIDATION_PLAN", validation_digest="DG-VALIDATION-V1", identity_complete=True))

def mutate_t35(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, precision_presence="RESOLVED", precision_value=None, precision_unresolved=True, identity_complete=True))

def mutate_t36(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, identity_complete=False))

def mutate_t37(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, declarations=replace(bundle.declarations, trace_precision_digest="DG-PRECISION-TRACE-DRIFT"))

def mutate_t38(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, selected_action="OUTPUT", payload_type="OutputPayload"))

def mutate_t39(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, selected_action="CONDITIONAL", payload_type="ConditionalPayload", payload_issue_ids=("ISSUE-RISK-UNKNOWN",)))

def mutate_t40(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, selected_action="ASK", payload_type="AskPayload", question_paths=("/gate/ATTRIBUTION",)))

def mutate_t41(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, selected_action="ABSTAIN", payload_type="AbstainPayload", payload_issue_ids=("COMPETITION.UNRESOLVED",)))

def mutate_t42(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, selected_action="HUMAN_REVIEW", payload_type="HumanReviewPayload", payload_issue_ids=("GATE.FIELD_CONFLICT",)))

def mutate_t43(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, selected_action="ASK", payload_type="OutputPayload", question_paths=("/gate/ATTRIBUTION",)))

def mutate_t44(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, trace=replace(bundle.trace, statement_set_complete=False))

def mutate_t45(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, trace=replace(bundle.trace, statement_complete=False))

def mutate_t46(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, participation=replace(bundle.participation, role_ids=("ROLE-ALLOCATION", "ROLE-RISK", "ROLE-REALITY", "ROLE-ATTRIBUTION", "ROLE-SOURCE", "ROLE-TEMPORAL")))

def mutate_t47(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, participation=replace(bundle.participation, role_ids=("ROLE-ALLOCATION", "ROLE-RISK", "ROLE-REALITY", "ROLE-ATTRIBUTION", "ROLE-TEMPORAL"), reality_record_id="PR-REALITY-BORROWED"))

def mutate_t48(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, participation=replace(bundle.participation, state_support_aligned=False, source_decision_ref="DEC-F09-MISMATCH"))

def mutate_t49(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, root_timing=replace(bundle.root_timing, root_state="SATISFIED", root_reason_code=None, root_issue_path=None))

def mutate_t50(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, root_timing=replace(bundle.root_timing, timing_state="SATISFIED", timing_reason_code=None, timing_issue_path=None))

def mutate_t51(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, root_timing=replace(bundle.root_timing, root_state="UNKNOWN", root_reason_code=None, root_issue_path=None))

def mutate_t52(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, feedback=replace(bundle.feedback, submission_complete=True, item_ids=("FBI-1", "FBI-2")))

def mutate_t53(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, feedback=replace(bundle.feedback, binding_complete=True, seven_matches=("MATCH", "MATCH", "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "MATCH")))

def mutate_t54(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, feedback=replace(bundle.feedback, eligibility_complete=True, policy_version="policy-v1"))

def mutate_t55(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, feedback=replace(bundle.feedback, target_revision="STMT-REV-3", item_ids=("FBI-1",), prior_source_digest="DG-FEEDBACK-A", source_digest="DG-FEEDBACK-A", policy_version="policy-v1", prior_policy_version="policy-v1"))

def mutate_t56(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, feedback=replace(bundle.feedback, target_revision="STMT-REV-2", item_ids=("FBI-1",), prior_source_digest="DG-FEEDBACK-A", source_digest="DG-FEEDBACK-A", policy_version="policy-v1", prior_policy_version="policy-v2"))

def mutate_t57(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, feedback=replace(bundle.feedback, target_revision="STMT-REV-2", item_ids=("FBI-1", "FBI-2"), prior_source_digest="DG-FEEDBACK-A", source_digest="DG-FEEDBACK-A", policy_version="policy-v1", prior_policy_version="policy-v1"))

def mutate_t58(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, feedback=replace(bundle.feedback, target_revision="STMT-REV-2", item_ids=("FBI-1",), prior_source_digest="DG-FEEDBACK-A", source_digest="DG-FEEDBACK-B", policy_version="policy-v1", prior_policy_version="policy-v1"))

def mutate_t59(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, basis_gate_ids=("GR-ALLOCATION", "GR-RISK", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL"), basis_participation_ids=("PR-REALITY-OUTPUT",), disposition_refs=("DISP-F09-INCLUDED",)))

def mutate_t60(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, basis_participation_ids=("PARTICIPATION-SET-CONTAINER",)))

def mutate_t61(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, selected_action="OUTPUT", dispositions=("DISP-F09-INCLUDED",), disposition_refs=("DISP-F09-INCLUDED",)))

def mutate_t62(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, disposition_refs=("CAND-NOT-IN-SET",)))

def mutate_t63(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, dispositions=()))

def mutate_t64(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, dispositions=("DISP-F09-INCLUDED-A", "DISP-F09-INCLUDED-B")))

def mutate_t65(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, selected_action="OUTPUT", dispositions=("DISP-F09-CONDITIONAL",)))

def mutate_t66(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, selected_action="CONDITIONAL", payload_type="ConditionalPayload", dispositions=("DISP-F09-CONDITIONAL",), disposition_refs=("DISP-F09-CONDITIONAL",)))

def mutate_t67(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, item_states=("NOT_ATTEMPTED", "WRITING", "WRITTEN_UNVERIFIED", "VERIFIED", "FAILED", "STALE", "MISMATCH", "SUPERSEDED")))

def mutate_t68(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, item_states=("NOT_STARTED",)))

def mutate_t69(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, item_states=("WRITTEN",)))

def mutate_t70(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, item_states=("STALE",), statement_revision="STMT-REV-1"))

def mutate_t71(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, item_states=("MISMATCH",), observed_digest="DG-ARTIFACT-MISMATCH"))

def mutate_t72(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, artifacts=replace(bundle.artifacts, item_states=("SUPERSEDED",), statement_revision="STMT-REV-2", supersedes_revision="STMT-REV-1"))

def mutate_t73(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, decision=replace(bundle.decision, selected_action="ABSTAIN", payload_type="AbstainPayload", dispositions=("DISP-F09-UNRESOLVED",), disposition_refs=("DISP-F09-UNRESOLVED",)))

def mutate_t74(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, member_ids=("ALLOCATION", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "TEMPORAL"), declared_member_ids=("ALLOCATION", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "TEMPORAL")))

def mutate_t75(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, member_ids=("ALLOCATION", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "SOURCE"), declared_member_ids=("ALLOCATION", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "TEMPORAL")))

def mutate_t76(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, member_ids=("ALLOCATION", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "UNKNOWN_MEMBER")))

def mutate_t77(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, record_gate_definition_refs=("REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1/SOURCE")))

def mutate_t78(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, declared_member_ids=("ALLOCATION@V2:DG-DRIFT", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "TEMPORAL")))

def mutate_t79(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, allocation_state="CONFLICT", evaluation_binding_digests=("DG-ALLOC", "DG-RISK", "DG-REAL", "DG-ATTR", "DG-SOURCE", "DG-TEMP")))

def mutate_t80(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, member_ids=("RISK", "ALLOCATION", "REALITY", "ATTRIBUTION", "SOURCE", "TEMPORAL"), evaluation_binding_digests=("DG-ALLOC", "DG-RISK", "DG-REAL", "DG-ATTR", "DG-SOURCE", "DG-TEMP")))

def mutate_t81(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, member_ids=("TEMPORAL", "SOURCE", "ATTRIBUTION", "REALITY", "RISK", "ALLOCATION"), evaluation_binding_digests=("DG-TEMP", "DG-SOURCE", "DG-ATTR", "DG-REAL", "DG-RISK", "DG-ALLOC")))

def mutate_t82(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, allocation_state="SATISFIED", risk_state="UNKNOWN", risk_reason_codes=("GATE.STATE_UNKNOWN",)), decision=replace(bundle.decision, selected_action="CONDITIONAL", payload_type="ConditionalPayload", payload_issue_ids=("GATE.STATE_UNKNOWN",)))

def mutate_t83(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, allocation_state="UNKNOWN", risk_state="SATISFIED", allocation_reason_codes=("GATE.STATE_UNKNOWN",)))

def mutate_t84(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, allocation_state="SATISFIED", risk_state="SATISFIED", reality_state="SATISFIED", attribution_state="SATISFIED", source_state="SATISFIED", temporal_state="SATISFIED"))

def mutate_t85(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, path_complete=False, record_gate_definition_refs=("REF-BROKEN", "REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1")))

def mutate_t86(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, reality_state="SATISFIED", supporting_evidence_tracks=("CHART_STRUCTURE", "UNVERIFIED_HYPOTHESIS")))

def mutate_t87(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, participation=replace(bundle.participation, scenario_id="ASK", reality_record_id="PR-REALITY-ASK", state_support_aligned=True))

def mutate_t88(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, participation=replace(bundle.participation, scenario_id="ASK", reality_record_id="PR-REALITY-OUTPUT"))

def mutate_t89(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, trace=replace(bundle.trace, statement_basis_ids=("GR-RISK", "GR-ALLOCATION", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL", "PR-REALITY-OUTPUT", "DISP-F09-INCLUDED", "RTC-ROOT", "RTC-TIMING")))

def mutate_t90(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, source_kind="IMMUTABLE_JSON_SNAPSHOT", canonical_nested_binding=True, locator_available=True))

def mutate_t91(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, state_fields=("level", "position", "as_of"), state_pointer="/value"))

def mutate_t92(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, event_object_id="SOURCE-EVENT-1", event_fields=("level", "change", "interval/start", "interval/end", "interval/start_inclusive", "interval/end_inclusive"), event_pointer="/value"))

def mutate_t93(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, state_object_id="SOURCE-EVENT-1", state_pointer="/value", event_object_id="SOURCE-STATE-1", event_pointer="/value"))

def mutate_t94(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, outcome_fields=("axis", "action", "object", "tense")))

def mutate_t95(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, source_field_present=False))

def mutate_t96(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, snapshot_id="SNAP-F09-DRIFT", snapshot_schema_version="snapshot-v2", contract_version="PI300-V2", content_digest="DG-SNAPSHOT-DRIFT", captured_at="2026-07-20T00:00:01Z", payload_digest="DG-PAYLOAD-DRIFT"))

def mutate_t97(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, trace=replace(bundle.trace, field_mapping_count=0, external_source_terminated=False))

def mutate_t98(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, outcome_fields=("axis", "action", "object")))

def mutate_t99(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, source_kind="MARKDOWN_FREE_TEXT"), trace=replace(bundle.trace, transformation_fidelity="LOSSLESS"))

def mutate_t100(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, source=replace(bundle.source, state_pointer="/metadata/state", canonical_nested_binding=False))

def mutate_t101(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, trace=replace(bundle.trace, statement_text="axis=wealth; action=use tool X; object=amount 100000; tense=future; guaranteed wealth outcome"))

def mutate_t102(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, risk_state="UNKNOWN", allocation_state="UNKNOWN", risk_reason_codes=("ISSUE-RISK-UNKNOWN",), allocation_reason_codes=("UNREGISTERED-UNKNOWN-REASON",)))

def mutate_t103(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, risk_state="UNKNOWN", risk_reason_codes=("ISSUE-RISK-UNKNOWN",)), decision=replace(bundle.decision, selected_action="CONDITIONAL", payload_type="ConditionalPayload", payload_issue_ids=("ISSUE-RISK-UNKNOWN",)), trace=replace(bundle.trace, issue_propagation_ids=("ISSUE-RISK-UNKNOWN",)))

def mutate_t104(bundle: ScenarioBundle) -> ScenarioBundle:
    return replace(bundle, gate=replace(bundle.gate, member_ids=("ALLOCATION", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "UNKNOWN_MEMBER"), record_gate_definition_refs=("REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-V1", "REF-GATE-F09-FORGED"), evaluation_binding_digests=("DG-ALLOC", "DG-RISK", "DG-REAL", "DG-ATTR", "DG-SOURCE", "DG-FORGED"), risk_state="UNKNOWN", risk_reason_codes=("UNREGISTERED-UNKNOWN-REASON",)), declarations=replace(bundle.declarations, precision_digest="DG-PRECISION-FORGED"), source=replace(bundle.source, payload_digest="DG-PAYLOAD-FORGED"))
```

Static acceptance AST-parses the sole continuous conftest block itself, not the constructor references below. It requires functions `mutate_t01` through `mutate_t104` exactly once; T01's sole return is `bundle`; every T02–T104 return contains an explicit `replace(bundle, ...)` and at least one nested `replace(bundle.<domain>, <literal field>=<literal value>)`; compound T43/T75/T96/T102/T104 must match their displayed ordered keyword sets exactly. For positive rows whose displayed canonical replacement equals the baseline value, acceptance checks the literal replacement keyword/value and non-target equality rather than falsely claiming runtime inequality. It rejects loops, comprehensions, ranges, factories, registries, dynamic IDs, `getattr`, shared dispatch, table parsing, omitted bodies, and nonliteral replacement values.

### Literal executable scenario-data module

The implementation must copy the following module block verbatim into `tests/f09/data/f09_vertical_scenarios.py`. Copy from the first `from engine.f09.contracts import DecisionAction` import through the closing literal `SCENARIOS` tuple, inclusive. `DecisionAction` is reused from the canonical Task 1 runtime module; `VerticalScenario` and every explicitly imported `mutate_tNN` are reused from the fully defined `tests/f09/conftest.py` block above. Import this scenario module only after those conftest symbols exist. The displayed imports and definitions are complete module scaffolding: no implicit helper, competing type, wildcard/dynamic import, `getattr`, mutation registry, ID parsing, range, loop, comprehension, factory, generated node, table parser, default expectation or shared catch-all mutator is permitted. Each mutator has signature `def mutate_tNN(bundle: ScenarioBundle) -> ScenarioBundle`; T01 returns the complete baseline unchanged, and T02–T104 each perform only their constructor's literal delta. This makes a missing mutator an import/collection error rather than an implementer inference point.

```python
from engine.f09.contracts import DecisionAction
from tests.f09.conftest import (
    VerticalScenario,
    mutate_t01, mutate_t02, mutate_t03, mutate_t04, mutate_t05, mutate_t06, mutate_t07, mutate_t08,
    mutate_t09, mutate_t10, mutate_t11, mutate_t12, mutate_t13, mutate_t14, mutate_t15, mutate_t16,
    mutate_t17, mutate_t18, mutate_t19, mutate_t20, mutate_t21, mutate_t22, mutate_t23, mutate_t24,
    mutate_t25, mutate_t26, mutate_t27, mutate_t28, mutate_t29, mutate_t30, mutate_t31, mutate_t32,
    mutate_t33, mutate_t34, mutate_t35, mutate_t36, mutate_t37, mutate_t38, mutate_t39, mutate_t40,
    mutate_t41, mutate_t42, mutate_t43, mutate_t44, mutate_t45, mutate_t46, mutate_t47, mutate_t48,
    mutate_t49, mutate_t50, mutate_t51, mutate_t52, mutate_t53, mutate_t54, mutate_t55, mutate_t56,
    mutate_t57, mutate_t58, mutate_t59, mutate_t60, mutate_t61, mutate_t62, mutate_t63, mutate_t64,
    mutate_t65, mutate_t66, mutate_t67, mutate_t68, mutate_t69, mutate_t70, mutate_t71, mutate_t72,
    mutate_t73, mutate_t74, mutate_t75, mutate_t76, mutate_t77, mutate_t78, mutate_t79, mutate_t80,
    mutate_t81, mutate_t82, mutate_t83, mutate_t84, mutate_t85, mutate_t86, mutate_t87, mutate_t88,
    mutate_t89, mutate_t90, mutate_t91, mutate_t92, mutate_t93, mutate_t94, mutate_t95, mutate_t96,
    mutate_t97, mutate_t98, mutate_t99, mutate_t100, mutate_t101, mutate_t102, mutate_t103, mutate_t104,
)

T01 = VerticalScenario(test_id="T01", pi300_purpose="OUTPUT 正常路径", mutation="完整全门/参与/竞争/root/timing", mutate=mutate_t01, expected_action=DecisionAction.OUTPUT, expected_gate_or_state="OUTPUT", expected_issue_code=None, expected_issue_path=None, basis_assertions=("nonempty", "exact_local_records"), binding_assertions=("declarations_exact",), side_effect_assertion="staged_writes_only", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T01]")
T02 = VerticalScenario(test_id="T02", pi300_purpose="CONDITIONAL 单轴", mutation="allocation SATISFIED; risk UNKNOWN", mutate=mutate_t02, expected_action=DecisionAction.CONDITIONAL, expected_gate_or_state="CONDITIONAL", expected_issue_code="ISSUE-RISK-UNKNOWN", expected_issue_path="/gate/RISK", basis_assertions=("condition_refs", "six_gates"), binding_assertions=("risk_unknown_exact",), side_effect_assertion="no_production_or_learning", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T02]")
T03 = VerticalScenario(test_id="T03", pi300_purpose="ASK 缺归属事实", mutation="attribution MISSING", mutate=mutate_t03, expected_action=DecisionAction.ASK, expected_gate_or_state="ASK", expected_issue_code="GATE.FIELD_MISSING", expected_issue_path="/gate/ATTRIBUTION", basis_assertions=("question_issue_path_resume",), binding_assertions=("missing_path_bound",), side_effect_assertion="no_conclusion_write", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T03]")
T04 = VerticalScenario(test_id="T04", pi300_purpose="ABSTAIN 竞争未解", mutation="F08/F09 competition unresolved", mutate=mutate_t04, expected_action=DecisionAction.ABSTAIN, expected_gate_or_state="ABSTAIN", expected_issue_code="COMPETITION.UNRESOLVED", expected_issue_path="/competition/F09", basis_assertions=("both_candidate_evidence",), binding_assertions=("f08_reference_absent",), side_effect_assertion="no_formal_outcome", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T04]")
T05 = VerticalScenario(test_id="T05", pi300_purpose="HUMAN_REVIEW 来源解释冲突", mutation="attribution evaluator CONFLICT", mutate=mutate_t05, expected_action=DecisionAction.HUMAN_REVIEW, expected_gate_or_state="HUMAN_REVIEW", expected_issue_code="GATE.FIELD_CONFLICT", expected_issue_path="/gate/ATTRIBUTION", basis_assertions=("both_sides", "review_scope"), binding_assertions=("conflict_refs_exact",), side_effect_assertion="no_auto_learning", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T05]")
T06 = VerticalScenario(test_id="T06", pi300_purpose="explicit null", mutation="output precision value null", mutate=mutate_t06, expected_action=None, expected_gate_or_state="RESOLVED", expected_issue_code=None, expected_issue_path=None, basis_assertions=("declaration_ref_nonempty",), binding_assertions=("resolved_ref_exact",), side_effect_assertion="no_inferred_precision", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T06]")
T07 = VerticalScenario(test_id="T07", pi300_purpose="null + unresolved", mutation="precision null and listed unresolved", mutate=mutate_t07, expected_action=None, expected_gate_or_state="BOTH_NULL_AND_UNRESOLVED", expected_issue_code="DECLARATION.VALUE_UNRESOLVED", expected_issue_path="/declarations/output_precision/value", basis_assertions=("value_presence_separate",), binding_assertions=("resolved_ref_retained",), side_effect_assertion="no_precision_fallback", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T07]")
T08 = VerticalScenario(test_id="T08", pi300_purpose="absent 负例", mutation="synthetic declaration field absent", mutate=mutate_t08, expected_action=None, expected_gate_or_state="ABSENT_INVALID", expected_issue_code="DECLARATION.NOT_PRESENT", expected_issue_path="/declarations/output_precision", basis_assertions=("no_borrowed_basis",), binding_assertions=("absent_reason_exact",), side_effect_assertion="frozen_source_unchanged", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T08]")
T09 = VerticalScenario(test_id="T09", pi300_purpose="evaluator unknown", mutation="risk present but unevaluable", mutate=mutate_t09, expected_action=None, expected_gate_or_state="SAFE_ACTION", expected_issue_code="GATE.STATE_UNKNOWN", expected_issue_path="/gate/RISK", basis_assertions=("unknown_path_retained",), binding_assertions=("unknown_digest_exact",), side_effect_assertion="unknown_not_action", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T09]")
T10 = VerticalScenario(test_id="T10", pi300_purpose="source unavailable", mutation="locator unreadable", mutate=mutate_t10, expected_action=None, expected_gate_or_state="BLOCKING", expected_issue_code="SOURCE.UNAVAILABLE", expected_issue_path="/records/source_locator", basis_assertions=("no_satisfied_gate_basis",), binding_assertions=("unavailable_issues_nonempty",), side_effect_assertion="no_artifacts", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T10]")
T11 = VerticalScenario(test_id="T11", pi300_purpose="declaration unresolvable", mutation="attempted ref digest/version drift", mutate=mutate_t11, expected_action=None, expected_gate_or_state="UNRESOLVABLE", expected_issue_code="DECLARATION.DIGEST_MISMATCH", expected_issue_path="/declarations/attempted_ref", basis_assertions=("attempted_ref_retained",), binding_assertions=("unresolvable_branch_exact",), side_effect_assertion="no_statement", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T11]")
T12 = VerticalScenario(test_id="T12", pi300_purpose="invalid N/A", mutation="required F09 declaration forged NOT_APPLICABLE", mutate=mutate_t12, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="DECLARATION.NOT_APPLICABLE_INVALID", expected_issue_path="/declarations/output_precision", basis_assertions=("no_action_basis",), binding_assertions=("not_applicable_reason_visible",), side_effect_assertion="no_conclusion_write", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T12]")
T13 = VerticalScenario(test_id="T13", pi300_purpose="理论冒充事实", mutation="CHART_STRUCTURE only for reality", mutate=mutate_t13, expected_action=None, expected_gate_or_state="GATE_MISSING", expected_issue_code="EVIDENCE.TRACK_INVALID", expected_issue_path="/gate/reality", basis_assertions=("chart_refs_context_only",), binding_assertions=("chart_track_exact",), side_effect_assertion="no_promotion", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T13]")
T14 = VerticalScenario(test_id="T14", pi300_purpose="hypothesis 冒充事实", mutation="UNVERIFIED_HYPOTHESIS only", mutate=mutate_t14, expected_action=None, expected_gate_or_state="GATE_MISSING", expected_issue_code="EVIDENCE.TRACK_INVALID", expected_issue_path="/gate/reality", basis_assertions=("hypothesis_refs_retained",), binding_assertions=("hypothesis_track_exact",), side_effect_assertion="no_promotion", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T14]")
T15 = VerticalScenario(test_id="T15", pi300_purpose="竞争冲突", mutation="F08 duty and F09 capital both strong", mutate=mutate_t15, expected_action=None, expected_gate_or_state="CONFLICT_UNRESOLVED", expected_issue_code="COMPETITION.UNRESOLVED", expected_issue_path="/competition/F09", basis_assertions=("both_evidence_sets",), binding_assertions=("f08_identity_only",), side_effect_assertion="no_second_card", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T15]")
T16 = VerticalScenario(test_id="T16", pi300_purpose="后果反填", mutation="profit/loss/debt only", mutate=mutate_t16, expected_action=None, expected_gate_or_state="GATE_MISSING", expected_issue_code="GATE.FIELD_MISSING", expected_issue_path="/gate/ALLOCATION", basis_assertions=("consequence_excluded",), binding_assertions=("source_refs_retained",), side_effect_assertion="no_backfill", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T16]")
T17 = VerticalScenario(test_id="T17", pi300_purpose="根源/应期改写攻击", mutation="timing substitute mutates root R1", mutate=mutate_t17, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="ROOT_TIMING.REWRITE_INVALID", expected_issue_path="/root_timing_checks/0", basis_assertions=("ledgers_separate",), binding_assertions=("ledger_refs_exact",), side_effect_assertion="no_decision_write", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T17]")
T18 = VerticalScenario(test_id="T18", pi300_purpose="validation/precision 串线", mutation="T0/T1/T2 placed in precision", mutate=mutate_t18, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="DECLARATION.IDENTITY_MISMATCH", expected_issue_path="/declarations/output_precision", basis_assertions=("declaration_refs_separate",), binding_assertions=("type_id_path_exact",), side_effect_assertion="no_guessing", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T18]")
T19 = VerticalScenario(test_id="T19", pi300_purpose="decision→statement binding 漂移", mutation="mutate statement declaration branch/digest", mutate=mutate_t19, expected_action=None, expected_gate_or_state="STATEMENT_INVALID", expected_issue_code="TRACE.BINDING_MISMATCH", expected_issue_path="/statements/0/output_precision_binding", basis_assertions=("action_basis_unchanged",), binding_assertions=("both_declarations_exact",), side_effect_assertion="no_publish", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T19]")
T20 = VerticalScenario(test_id="T20", pi300_purpose="多规则 records 投影", mutation="statement has three rule refs", mutate=mutate_t20, expected_action=None, expected_gate_or_state="LOSSY", expected_issue_code="PROJECTION.LOSSY", expected_issue_path="/transformations/records", basis_assertions=("one_anchor_two_dropped",), binding_assertions=("source_refs_reachable",), side_effect_assertion="no_learning_ready", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T20]")
T21 = VerticalScenario(test_id="T21", pi300_purpose="report 成功 records 失败", mutation="inject records write failure", mutate=mutate_t21, expected_action=None, expected_gate_or_state="PARTIAL_RECORDS_WRITE_FAILED", expected_issue_code="ARTIFACT.WRITE_FAILED", expected_issue_path="/artifacts/STATEMENT_RECORDS", basis_assertions=("input_snapshots_logged",), binding_assertions=("records_attempt_ledger_complete",), side_effect_assertion="no_feedback_readiness", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T21]")
T22 = VerticalScenario(test_id="T22", pi300_purpose="records 成功 index 失败", mutation="inject index write failure", mutate=mutate_t22, expected_action=None, expected_gate_or_state="PARTIAL_INDEX_WRITE_FAILED", expected_issue_code="ARTIFACT.WRITE_FAILED", expected_issue_path="/artifacts/STATEMENT_INDEX", basis_assertions=("prior_records_retained",), binding_assertions=("index_attempt_ledger_complete",), side_effect_assertion="no_rollback_overwrite", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T22]")
T23 = VerticalScenario(test_id="T23", pi300_purpose="新 records + 旧 index", mutation="stale revision index", mutate=mutate_t23, expected_action=None, expected_gate_or_state="STALE_MIXED_REVISION", expected_issue_code="ARTIFACT.STALE_REVISION", expected_issue_path="/artifacts/STATEMENT_INDEX", basis_assertions=("current_old_refs_visible",), binding_assertions=("revisions_exact",), side_effect_assertion="no_feedback_readiness", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T23]")
T24 = VerticalScenario(test_id="T24", pi300_purpose="digest mismatch", mutation="same key different digest", mutate=mutate_t24, expected_action=None, expected_gate_or_state="DIGEST_MISMATCH", expected_issue_code="ARTIFACT.DIGEST_MISMATCH", expected_issue_path="/artifacts/observed_digest", basis_assertions=("original_inputs_retained",), binding_assertions=("expected_observed_separate",), side_effect_assertion="no_overwrite", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T24]")
T25 = VerticalScenario(test_id="T25", pi300_purpose="unknown feedback mapping", mutation="unknown statement or UNMAPPED anchor", mutate=mutate_t25, expected_action=None, expected_gate_or_state="UNBOUND_INELIGIBLE", expected_issue_code="FEEDBACK.TARGET_UNBOUND", expected_issue_path="/feedback_bindings/0", basis_assertions=("zero_learning_targets",), binding_assertions=("seven_dimensions_explicit",), side_effect_assertion="learning_calls_zero", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T25]")
T26 = VerticalScenario(test_id="T26", pi300_purpose="revision mismatch", mutation="target old revision", mutate=mutate_t26, expected_action=None, expected_gate_or_state="INVALID_INELIGIBLE", expected_issue_code="FEEDBACK.REVISION_MISMATCH", expected_issue_path="/feedback_bindings/0/revision_match", basis_assertions=("old_target_retained",), binding_assertions=("revision_mismatch",), side_effect_assertion="no_fuzzy_match", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T26]")
T27 = VerticalScenario(test_id="T27", pi300_purpose="duplicate same payload", mutation="same idempotency key and digest retry", mutate=mutate_t27, expected_action=None, expected_gate_or_state="NO_OP_SUCCESS", expected_issue_code=None, expected_issue_path=None, basis_assertions=("same_snapshots",), binding_assertions=("same_canonical_key",), side_effect_assertion="no_artifact_duplicate", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T27]")
T28 = VerticalScenario(test_id="T28", pi300_purpose="duplicate conflicting payload", mutation="same key different digest", mutate=mutate_t28, expected_action=None, expected_gate_or_state="CONFLICT", expected_issue_code="IDEMPOTENCY.DIGEST_MISMATCH", expected_issue_path="/canonical_key_digest", basis_assertions=("both_attempt_refs",), binding_assertions=("retry_digest_separate",), side_effect_assertion="no_overwrite_or_learning", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T28]")
T29 = VerticalScenario(test_id="T29", pi300_purpose="preprod 跨轨输入", mutation="preprod attachment to production", mutate=mutate_t29, expected_action=None, expected_gate_or_state="INVALID_AUDIT_ONLY", expected_issue_code="FEEDBACK.TRACK_MISMATCH", expected_issue_path="/feedback_bindings/0/track_match", basis_assertions=("audit_refs_only",), binding_assertions=("track_mismatch",), side_effect_assertion="no_production_learning", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T29]")
T30 = VerticalScenario(test_id="T30", pi300_purpose="card identity 误宣称", mutation="capability changed to implemented", mutate=mutate_t30, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="CARD.IDENTITY_INVALID", expected_issue_path="/card_identity_refs/0/runtime_capability_status", basis_assertions=("card_ref_retained",), binding_assertions=("reference_only_literal",), side_effect_assertion="no_publish", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T30]")
T31 = VerticalScenario(test_id="T31", pi300_purpose="F08 identity-only 正例", mutation="only CAND-F09; F08 only in refs", mutate=mutate_t31, expected_action=None, expected_gate_or_state="CONSUMABLE", expected_issue_code=None, expected_issue_path=None, basis_assertions=("f09_disposition_only",), binding_assertions=("f08_ref_reachable",), side_effect_assertion="no_f08_execution", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T31]")
T32 = VerticalScenario(test_id="T32", pi300_purpose="伪造 F08 candidate", mutation="inject F08 candidate/action/statement", mutate=mutate_t32, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="COMPETITION.CANDIDATE_INVALID", expected_issue_path="/competition/candidate_ids", basis_assertions=("forged_object_retained",), binding_assertions=("f08_forged_objects_exact",), side_effect_assertion="no_silent_deletion", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T32]")
T33 = VerticalScenario(test_id="T33", pi300_purpose="singleton 被实现拒绝", mutation="validator demands two candidates", mutate=mutate_t33, expected_action=None, expected_gate_or_state="BLOCKED_CONTRACT_MISMATCH", expected_issue_code="CONTRACT.CARDINALITY_MISMATCH", expected_issue_path="/competition/candidate_ids", basis_assertions=("singleton_basis_retained",), binding_assertions=("contract_ref_exact",), side_effect_assertion="no_f08_repair", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T33]")
T34 = VerticalScenario(test_id="T34", pi300_purpose="validation ref 完整正例", mutation="all six declaration identity fields", mutate=mutate_t34, expected_action=None, expected_gate_or_state="RESOLVED", expected_issue_code=None, expected_issue_path=None, basis_assertions=("ref_nonempty",), binding_assertions=("field_path_locator_only",), side_effect_assertion="no_identity_inference", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T34]")
T35 = VerticalScenario(test_id="T35", pi300_purpose="precision ref 完整正例", mutation="six fields plus null and unresolved", mutate=mutate_t35, expected_action=None, expected_gate_or_state="RESOLVED", expected_issue_code="DECLARATION.VALUE_UNRESOLVED", expected_issue_path="/declarations/output_precision/value", basis_assertions=("ref_nonempty",), binding_assertions=("resolved_identity_exact",), side_effect_assertion="no_precision_expansion", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T35]")
T36 = VerticalScenario(test_id="T36", pi300_purpose="declaration identity 缺字段", mutation="delete identity field or path substitution", mutate=mutate_t36, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="DECLARATION.IDENTITY_MISMATCH", expected_issue_path="/declarations/ref", basis_assertions=("attempted_ref_visible",), binding_assertions=("no_guessed_match",), side_effect_assertion="no_output", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T36]")
T37 = VerticalScenario(test_id="T37", pi300_purpose="cross-layer declaration drift", mutation="mutate one ref identity field", mutate=mutate_t37, expected_action=None, expected_gate_or_state="TRACE_STATEMENT_INVALID", expected_issue_code="TRACE.BINDING_MISMATCH", expected_issue_path="/trace/declarations", basis_assertions=("decision_basis_stable",), binding_assertions=("both_refs_field_equal",), side_effect_assertion="no_publish", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T37]")
T38 = VerticalScenario(test_id="T38", pi300_purpose="OUTPUT payload contract", mutation="complete output payload and basis", mutate=mutate_t38, expected_action=DecisionAction.OUTPUT, expected_gate_or_state="VALID", expected_issue_code=None, expected_issue_path=None, basis_assertions=("nonempty_exact_basis",), binding_assertions=("output_discriminator",), side_effect_assertion="staged_only", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T38]")
T39 = VerticalScenario(test_id="T39", pi300_purpose="CONDITIONAL payload contract", mutation="complete condition issues scope", mutate=mutate_t39, expected_action=DecisionAction.CONDITIONAL, expected_gate_or_state="VALID", expected_issue_code="ISSUE-RISK-UNKNOWN", expected_issue_path="/action/payload/issues", basis_assertions=("issue_refs_preserved",), binding_assertions=("conditional_discriminator",), side_effect_assertion="no_hidden_resolution", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T39]")
T40 = VerticalScenario(test_id="T40", pi300_purpose="ASK payload contract", mutation="complete question issue path resume", mutate=mutate_t40, expected_action=DecisionAction.ASK, expected_gate_or_state="VALID", expected_issue_code="GATE.FIELD_MISSING", expected_issue_path="/action/payload/question_requests/0", basis_assertions=("original_refs_nonempty",), binding_assertions=("ask_discriminator",), side_effect_assertion="no_outcome", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T40]")
T41 = VerticalScenario(test_id="T41", pi300_purpose="ABSTAIN payload contract", mutation="complete candidates issues scope", mutate=mutate_t41, expected_action=DecisionAction.ABSTAIN, expected_gate_or_state="VALID", expected_issue_code="COMPETITION.UNRESOLVED", expected_issue_path="/action/payload", basis_assertions=("blocking_basis",), binding_assertions=("abstain_discriminator",), side_effect_assertion="no_output_payload", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T41]")
T42 = VerticalScenario(test_id="T42", pi300_purpose="HUMAN_REVIEW payload contract", mutation="complete case issues records scope", mutate=mutate_t42, expected_action=DecisionAction.HUMAN_REVIEW, expected_gate_or_state="VALID", expected_issue_code="GATE.FIELD_CONFLICT", expected_issue_path="/action/payload", basis_assertions=("both_conflict_sides",), binding_assertions=("review_discriminator",), side_effect_assertion="no_priority", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T42]")
T43 = VerticalScenario(test_id="T43", pi300_purpose="payload 判别错配", mutation="ASK with OutputPayload", mutate=mutate_t43, expected_action=DecisionAction.ASK, expected_gate_or_state="INVALID", expected_issue_code="ACTION.PAYLOAD_MISMATCH", expected_issue_path="/action_envelope", basis_assertions=("basis_retained_for_issue",), binding_assertions=("discriminator_mismatch",), side_effect_assertion="no_write", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T43]")
T44 = VerticalScenario(test_id="T44", pi300_purpose="StatementSet 必需字段", mutation="delete required set field", mutate=mutate_t44, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="STATEMENT.SET_INVALID", expected_issue_path="/statement_set", basis_assertions=("trace_ref_required",), binding_assertions=("source_version_refs_exact",), side_effect_assertion="no_publish", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T44]")
T45 = VerticalScenario(test_id="T45", pi300_purpose="StandardStatement 必需字段", mutation="delete required statement field", mutate=mutate_t45, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="STATEMENT.RECORD_INVALID", expected_issue_path="/statements/0", basis_assertions=("complete_basis_ids",), binding_assertions=("declarations_revision_exact",), side_effect_assertion="no_publish", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T45]")
T46 = VerticalScenario(test_id="T46", pi300_purpose="六 participation 完整正例", mutation="one complete record per role", mutate=mutate_t46, expected_action=None, expected_gate_or_state="READY", expected_issue_code=None, expected_issue_path=None, basis_assertions=("six_independent_ids",), binding_assertions=("role_refs_exact",), side_effect_assertion="ready_not_satisfied", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T46]")
T47 = VerticalScenario(test_id="T47", pi300_purpose="participation 补偿攻击", mutation="delete SOURCE_GATE and borrow reality evidence", mutate=mutate_t47, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="PARTICIPATION.ROLE_CARDINALITY_INVALID", expected_issue_path="/participation/roles", basis_assertions=("no_cross_role_basis",), binding_assertions=("missing_role_explicit",), side_effect_assertion="no_repair", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T47]")
T48 = VerticalScenario(test_id="T48", pi300_purpose="participation fail-safe", mutation="state evidence issue decision mismatch", mutate=mutate_t48, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="PARTICIPATION.PATH_INVALID", expected_issue_path="/participation/records", basis_assertions=("each_role_closes_path",), binding_assertions=("source_decision_exact",), side_effect_assertion="no_decision", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T48]")
T49 = VerticalScenario(test_id="T49", pi300_purpose="root ledger 完整正例", mutation="complete root entry", mutate=mutate_t49, expected_action=None, expected_gate_or_state="VALID", expected_issue_code=None, expected_issue_path=None, basis_assertions=("chart_evidence_only",), binding_assertions=("root_refs_exact",), side_effect_assertion="timing_cannot_mutate", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T49]")
T50 = VerticalScenario(test_id="T50", pi300_purpose="timing ledger 完整正例", mutation="complete timing entry", mutate=mutate_t50, expected_action=None, expected_gate_or_state="VALID", expected_issue_code=None, expected_issue_path=None, basis_assertions=("timing_evidence_local",), binding_assertions=("timing_refs_exact",), side_effect_assertion="root_unchanged", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T50]")
T51 = VerticalScenario(test_id="T51", pi300_purpose="root/timing fail-safe", mutation="violated or unknown without path/reason", mutate=mutate_t51, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="ROOT_TIMING.CHECK_INVALID", expected_issue_path="/root_timing_checks/0", basis_assertions=("both_ledgers_referenced",), binding_assertions=("source_decision_exact",), side_effect_assertion="no_rewrite", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T51]")
T52 = VerticalScenario(test_id="T52", pi300_purpose="FeedbackSubmission/Item 全字段", mutation="complete canonical submission and items", mutate=mutate_t52, expected_action=None, expected_gate_or_state="VALID", expected_issue_code=None, expected_issue_path=None, basis_assertions=("item_targets_explicit",), binding_assertions=("snapshot_parser_span_targets_integrity_exact",), side_effect_assertion="no_learning", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T52]")
T53 = VerticalScenario(test_id="T53", pi300_purpose="FeedbackBinding 全字段", mutation="seven matches targets anchor status issues", mutate=mutate_t53, expected_action=None, expected_gate_or_state="BOUND", expected_issue_code=None, expected_issue_path=None, basis_assertions=("target_refs_explicit",), binding_assertions=("seven_dimensions_exact",), side_effect_assertion="bound_status_exact", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T53]")
T54 = VerticalScenario(test_id="T54", pi300_purpose="LearningEligibility 全字段", mutation="policy targets exclusions reasons time", mutate=mutate_t54, expected_action=None, expected_gate_or_state="ELIGIBLE", expected_issue_code=None, expected_issue_path=None, basis_assertions=("learning_excluded_refs_explicit",), binding_assertions=("feedback_binding_id_exact",), side_effect_assertion="evaluation_only", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T54]")
T55 = VerticalScenario(test_id="T55", pi300_purpose="feedback revision 幂等变化", mutation="only target revision changes", mutate=mutate_t55, expected_action=None, expected_gate_or_state="REVISION_KEY_CHANGED", expected_issue_code=None, expected_issue_path=None, basis_assertions=("revised_target_input",), binding_assertions=("revision_in_identity",), side_effect_assertion="no_old_key_reuse", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T55]")
T56 = VerticalScenario(test_id="T56", pi300_purpose="eligibility policy 幂等变化", mutation="only policy version changes", mutate=mutate_t56, expected_action=None, expected_gate_or_state="POLICY_KEY_CHANGED", expected_issue_code=None, expected_issue_path=None, basis_assertions=("same_target_refs",), binding_assertions=("policy_in_identity",), side_effect_assertion="reevaluate_only", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T56]")
T57 = VerticalScenario(test_id="T57", pi300_purpose="feedback item 集合变化", mutation="add or remove canonical item", mutate=mutate_t57, expected_action=None, expected_gate_or_state="ITEM_SET_KEY_CHANGED", expected_issue_code=None, expected_issue_path=None, basis_assertions=("full_item_set_included",), binding_assertions=("item_ids_canonicalized",), side_effect_assertion="no_feedback_duplicate", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T57]")
T58 = VerticalScenario(test_id="T58", pi300_purpose="feedback source digest 变化", mutation="same feedback ID new source digest", mutate=mutate_t58, expected_action=None, expected_gate_or_state="NEW_OPERATION_CHANGED_SOURCE", expected_issue_code=None, expected_issue_path=None, basis_assertions=("prior_current_source_refs_and_keys_retained",), binding_assertions=("producer_receipt_changed_identity",), side_effect_assertion="no_last_write_wins", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T58]")
T59 = VerticalScenario(test_id="T59", pi300_purpose="basis record type 正例", mutation="exact six gates/local PR/competition/RTC", mutate=mutate_t59, expected_action=None, expected_gate_or_state="VALID", expected_issue_code=None, expected_issue_path=None, basis_assertions=("three_layers_same_ordered_ids",), binding_assertions=("records_resolve_current_result",), side_effect_assertion="no_cross_result_lookup", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T59]")
T60 = VerticalScenario(test_id="T60", pi300_purpose="wrong participation basis type", mutation="replace PR record ID with set container", mutate=mutate_t60, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="BASIS.RECORD_TYPE_INVALID", expected_issue_path="/action/basis/participation_record_ids", basis_assertions=("bad_id_retained",), binding_assertions=("no_container_coercion",), side_effect_assertion="fail_closed", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T60]")
T61 = VerticalScenario(test_id="T61", pi300_purpose="OUTPUT disposition 唯一解析", mutation="one F09 INCLUDED disposition", mutate=mutate_t61, expected_action=DecisionAction.OUTPUT, expected_gate_or_state="VALID", expected_issue_code=None, expected_issue_path=None, basis_assertions=("exact_candidate_basis",), binding_assertions=("unique_disposition_ref",), side_effect_assertion="no_output_disposition_fallback", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T61]")
T62 = VerticalScenario(test_id="T62", pi300_purpose="dangling disposition ref", mutation="CAND-NOT-IN-SET reference", mutate=mutate_t62, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="DISPOSITION.REFERENCE_DANGLING", expected_issue_path="/action/disposition_refs", basis_assertions=("bad_ref_explicit",), binding_assertions=("current_result_scope",), side_effect_assertion="no_guessing", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T62]")
T63 = VerticalScenario(test_id="T63", pi300_purpose="zero disposition matches", mutation="F09 ref with no disposition", mutate=mutate_t63, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="DISPOSITION.MATCH_COUNT_INVALID", expected_issue_path="/competition/candidate_dispositions", basis_assertions=("zero_match",), binding_assertions=("current_result_only",), side_effect_assertion="no_repair", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T63]")
T64 = VerticalScenario(test_id="T64", pi300_purpose="multiple disposition matches", mutation="duplicate F09 dispositions", mutate=mutate_t64, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="DISPOSITION.MATCH_COUNT_INVALID", expected_issue_path="/competition/candidate_dispositions", basis_assertions=("both_records_retained",), binding_assertions=("uniqueness_violated",), side_effect_assertion="no_first_wins", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T64]")
T65 = VerticalScenario(test_id="T65", pi300_purpose="disposition/action incompatible", mutation="wrong disposition for selected action", mutate=mutate_t65, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="DISPOSITION.ACTION_INCOMPATIBLE", expected_issue_path="/action/selected_action", basis_assertions=("disposition_basis_retained",), binding_assertions=("action_mapping_exact",), side_effect_assertion="no_downgrade", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T65]")
T66 = VerticalScenario(test_id="T66", pi300_purpose="CONDITIONAL disposition unique", mutation="one F09 CONDITIONAL disposition", mutate=mutate_t66, expected_action=DecisionAction.CONDITIONAL, expected_gate_or_state="VALID", expected_issue_code=None, expected_issue_path=None, basis_assertions=("condition_issues_retained",), binding_assertions=("unique_disposition_ref",), side_effect_assertion="no_conditional_disposition_fallback", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T66]")
T67 = VerticalScenario(test_id="T67", pi300_purpose="artifact 八状态正例", mutation="construct each canonical item state", mutate=mutate_t67, expected_action=None, expected_gate_or_state="VALID", expected_issue_code=None, expected_issue_path=None, basis_assertions=("attempts_state_appropriate",), binding_assertions=("exact_eight_value_enum",), side_effect_assertion="no_readiness_inference", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T67]")
T68 = VerticalScenario(test_id="T68", pi300_purpose="illegal NOT_STARTED", mutation="artifact item state NOT_STARTED", mutate=mutate_t68, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="ARTIFACT.STATE_INVALID", expected_issue_path="/artifacts/0/state", basis_assertions=("not_started_ref_retained",), binding_assertions=("not_started_not_coerced",), side_effect_assertion="no_write", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T68]")
T69 = VerticalScenario(test_id="T69", pi300_purpose="illegal WRITTEN", mutation="artifact item state WRITTEN", mutate=mutate_t69, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="ARTIFACT.STATE_INVALID", expected_issue_path="/artifacts/0/state", basis_assertions=("written_ref_retained",), binding_assertions=("written_not_coerced",), side_effect_assertion="no_verified_inference", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T69]")
T70 = VerticalScenario(test_id="T70", pi300_purpose="item STALE", mutation="artifact points to old statement revision", mutate=mutate_t70, expected_action=None, expected_gate_or_state="STALE_SET_NOT_READY", expected_issue_code="ARTIFACT.STALE_REVISION", expected_issue_path="/artifacts/0", basis_assertions=("old_input_refs",), binding_assertions=("item_set_states_separate",), side_effect_assertion="no_feedback", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T70]")
T71 = VerticalScenario(test_id="T71", pi300_purpose="item MISMATCH", mutation="observed digest differs expected", mutate=mutate_t71, expected_action=None, expected_gate_or_state="MISMATCH_SET_NOT_READY", expected_issue_code="ARTIFACT.DIGEST_MISMATCH", expected_issue_path="/artifacts/0/observed_digest", basis_assertions=("attempt_retained",), binding_assertions=("observed_digest_separate",), side_effect_assertion="no_overwrite", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T71]")
T72 = VerticalScenario(test_id="T72", pi300_purpose="item SUPERSEDED", mutation="new revision supersedes old", mutate=mutate_t72, expected_action=None, expected_gate_or_state="SUPERSEDED", expected_issue_code=None, expected_issue_path=None, basis_assertions=("old_new_refs_auditable",), binding_assertions=("old_identity_retained",), side_effect_assertion="not_verified", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T72]")
T73 = VerticalScenario(test_id="T73", pi300_purpose="ABSTAIN unresolved disposition", mutation="unique F09 UNRESOLVED disposition", mutate=mutate_t73, expected_action=DecisionAction.ABSTAIN, expected_gate_or_state="VALID", expected_issue_code="COMPETITION.UNRESOLVED", expected_issue_path="/competition/candidate_dispositions/0", basis_assertions=("blocking_competition_basis",), binding_assertions=("disposition_exact",), side_effect_assertion="no_outcome_statement", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T73]")
T74 = VerticalScenario(test_id="T74", pi300_purpose="declaration/record 全覆盖", mutation="six unique declarations and records", mutate=mutate_t74, expected_action=None, expected_gate_or_state="VALID", expected_issue_code=None, expected_issue_path=None, basis_assertions=("bijection_by_member_id",), binding_assertions=("shared_whole_ref",), side_effect_assertion="order_independent", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T74]")
T75 = VerticalScenario(test_id="T75", pi300_purpose="duplicate/omitted member", mutation="duplicate one member and omit another", mutate=mutate_t75, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="GATE.MEMBER_CARDINALITY_INVALID", expected_issue_path="/gate_sets/0/records", basis_assertions=("no_inferred_member",), binding_assertions=("bijection_fails",), side_effect_assertion="no_repair", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T75]")
T76 = VerticalScenario(test_id="T76", pi300_purpose="unknown member", mutation="record member undeclared", mutate=mutate_t76, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="GATE.MEMBER_DECLARATION_INVALID", expected_issue_path="/gate_sets/0/records/member", basis_assertions=("bad_record_retained",), binding_assertions=("declaration_mismatch",), side_effect_assertion="fail_closed", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T76]")
T77 = VerticalScenario(test_id="T77", pi300_purpose="shared-ref inconsistency", mutation="one member uses forged subpath ref", mutate=mutate_t77, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="GATE.MEMBER_BINDING_MISMATCH", expected_issue_path="/gate_sets/0/gate_definition_refs", basis_assertions=("six_ids_retained",), binding_assertions=("whole_ref_equal",), side_effect_assertion="no_coercion", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T77]")
T78 = VerticalScenario(test_id="T78", pi300_purpose="declaration version/digest 失败", mutation="drift declaration version/value/ref/digest", mutate=mutate_t78, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="GATE.MEMBER_DECLARATION_INVALID", expected_issue_path="/gate_sets/0/member_declaration_set", basis_assertions=("member_id_insufficient",), binding_assertions=("version_digest_boundary",), side_effect_assertion="no_stale_reuse", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T78]")
T79 = VerticalScenario(test_id="T79", pi300_purpose="evaluation binding mismatch", mutation="mutate record content keep binding digests", mutate=mutate_t79, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="GATE.MEMBER_BINDING_MISMATCH", expected_issue_path="/gate_sets/0/records/0/evaluation_binding_ref", basis_assertions=("mutated_fields_visible",), binding_assertions=("both_digests_checked",), side_effect_assertion="no_accept", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T79]")
T80 = VerticalScenario(test_id="T80", pi300_purpose="permutation attack", mutation="swap member content keep identity bindings", mutate=mutate_t80, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="GATE.PERMUTATION_BINDING_INVALID", expected_issue_path="/gate_sets/0/records", basis_assertions=("member_local_basis_checked",), binding_assertions=("identity_content_bound",), side_effect_assertion="no_positional_repair", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T80]")
T81 = VerticalScenario(test_id="T81", pi300_purpose="record reorder invariance", mutation="reorder intact records only", mutate=mutate_t81, expected_action=None, expected_gate_or_state="SEMANTICS_UNCHANGED", expected_issue_code=None, expected_issue_path=None, basis_assertions=("basis_values_unchanged",), binding_assertions=("bindings_unchanged",), side_effect_assertion="no_semantic_drift", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T81]")
T82 = VerticalScenario(test_id="T82", pi300_purpose="配置单轴完整 fixture", mutation="allocation SAT; risk UNKNOWN; other four SAT", mutate=mutate_t82, expected_action=DecisionAction.CONDITIONAL, expected_gate_or_state="LIMITED_ALLOCATION", expected_issue_code="GATE.STATE_UNKNOWN", expected_issue_path="/gate/RISK", basis_assertions=("risk_unknown_six_record_chain",), binding_assertions=("risk_unknown_member_bindings_exact",), side_effect_assertion="no_risk_strengthening", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T82]")
T83 = VerticalScenario(test_id="T83", pi300_purpose="风险单轴完整 fixture", mutation="risk SAT; allocation UNKNOWN; other four SAT", mutate=mutate_t83, expected_action=None, expected_gate_or_state="LIMITED_RISK", expected_issue_code="GATE.STATE_UNKNOWN", expected_issue_path="/gate/ALLOCATION", basis_assertions=("allocation_unknown_six_record_chain",), binding_assertions=("allocation_unknown_member_bindings_exact",), side_effect_assertion="no_allocation_strengthening", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T83]")
T84 = VerticalScenario(test_id="T84", pi300_purpose="双轴完整 fixture", mutation="allocation/risk and four others SAT", mutate=mutate_t84, expected_action=None, expected_gate_or_state="DUAL_AXIS_AVAILABLE", expected_issue_code=None, expected_issue_path=None, basis_assertions=("six_satisfied_records",), binding_assertions=("bindings_exact",), side_effect_assertion="no_priority_invented", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T84]")
T85 = VerticalScenario(test_id="T85", pi300_purpose="六维 gate 断链", mutation="break binding/evidence/path/relation/decision", mutate=mutate_t85, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="GATE.PATH_INVALID", expected_issue_path="/gate_sets/0/records", basis_assertions=("each_member_independent",), binding_assertions=("broken_ref_identified",), side_effect_assertion="fail_closed", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T85]")
T86 = VerticalScenario(test_id="T86", pi300_purpose="理论证据冒充现实", mutation="SAT uses chart or hypothesis only", mutate=mutate_t86, expected_action=None, expected_gate_or_state="INVALID_GATE", expected_issue_code="EVIDENCE.TRACK_INVALID", expected_issue_path="/gate/supporting_evidence_ids", basis_assertions=("invalid_support_retained",), binding_assertions=("evidence_track_bound",), side_effect_assertion="no_sat_promotion", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T86]")
T87 = VerticalScenario(test_id="T87", pi300_purpose="五场景 participation 一致", mutation="scenario-local PR-REALITY-X", mutate=mutate_t87, expected_action=None, expected_gate_or_state="VALID", expected_issue_code=None, expected_issue_path=None, basis_assertions=("state_support_issues_align",), binding_assertions=("shared_frozen_ref",), side_effect_assertion="no_cross_scenario_reuse", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T87]")
T88 = VerticalScenario(test_id="T88", pi300_purpose="共享全满足现实角色攻击", mutation="non-output uses PR-REALITY-OUTPUT", mutate=mutate_t88, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="PARTICIPATION.SCENARIO_MISMATCH", expected_issue_path="/participation/records", basis_assertions=("local_basis_required",), binding_assertions=("scenario_identity_bound",), side_effect_assertion="no_masking", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T88]")
T89 = VerticalScenario(test_id="T89", pi300_purpose="action→trace→statement basis 漂移", mutation="delete reorder or replace gate/PR ID", mutate=mutate_t89, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="TRACE.BASIS_MISMATCH", expected_issue_path="/statements/0/basis_record_ids", basis_assertions=("three_layers_ordered_equal",), binding_assertions=("record_identity_valid",), side_effect_assertion="no_publish", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T89]")
T90 = VerticalScenario(test_id="T90", pi300_purpose="actual Markdown + JSON resolution", mutation="canonical selector and actual fixture", mutate=mutate_t90, expected_action=None, expected_gate_or_state="VALID_PROJECTION", expected_issue_code=None, expected_issue_path=None, basis_assertions=("both_source_chains_reachable",), binding_assertions=("two_source_binding_branches",), side_effect_assertion="no_yaml_or_prose_substitute", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T90]")
T91 = VerticalScenario(test_id="T91", pi300_purpose="state 来源字段完整", mutation="level position as_of three pointers", mutate=mutate_t91, expected_action=None, expected_gate_or_state="VALID_PROJECTION", expected_issue_code=None, expected_issue_path=None, basis_assertions=("three_lossless_mappings",), binding_assertions=("object_root_locators_exact",), side_effect_assertion="no_synthesis", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T91]")
T92 = VerticalScenario(test_id="T92", pi300_purpose="event 来源字段完整", mutation="six event fields and pointers", mutate=mutate_t92, expected_action=None, expected_gate_or_state="VALID_PROJECTION", expected_issue_code=None, expected_issue_path=None, basis_assertions=("six_lossless_mappings",), binding_assertions=("same_event_identity",), side_effect_assertion="no_synthesis", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T92]")
T93 = VerticalScenario(test_id="T93", pi300_purpose="state/event 错配", mutation="swap objects/windows or envelope pointer", mutate=mutate_t93, expected_action=None, expected_gate_or_state="INVALID_PROJECTION", expected_issue_code="SOURCE.LOCATOR_MISMATCH", expected_issue_path="/source_locators", basis_assertions=("bad_chain_explicit",), binding_assertions=("object_pointer_temporal_bound",), side_effect_assertion="no_interchange", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T93]")
T94 = VerticalScenario(test_id="T94", pi300_purpose="bounded outcome 完整", mutation="axis action object tense four fields", mutate=mutate_t94, expected_action=None, expected_gate_or_state="VALID_PROJECTION", expected_issue_code=None, expected_issue_path=None, basis_assertions=("four_lossless_mappings",), binding_assertions=("value_schema_null_refs_exact",), side_effect_assertion="no_business_synthesis", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T94]")
T95 = VerticalScenario(test_id="T95", pi300_purpose="source field/object/pointer missing", mutation="delete source retain target", mutate=mutate_t95, expected_action=None, expected_gate_or_state="INVALID_LOSSLESS_SOURCE", expected_issue_code="SOURCE.POINTER_UNRESOLVED", expected_issue_path="/transformations/LOSSLESS_COPY", basis_assertions=("broken_input_ref_shown",), binding_assertions=("no_metadata_substitute",), side_effect_assertion="no_output", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T95]")
T96 = VerticalScenario(test_id="T96", pi300_purpose="snapshot identity/JCS mismatch", mutation="drift five-field identity or payload digest", mutate=mutate_t96, expected_action=None, expected_gate_or_state="INVALID_PROJECTION", expected_issue_code="SOURCE.IDENTITY_MISMATCH", expected_issue_path="/source_locators/binding", basis_assertions=("envelope_payload_refs_retained",), binding_assertions=("five_fields_payload_digest_exact",), side_effect_assertion="no_local_bypass", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T96]")
T97 = VerticalScenario(test_id="T97", pi300_purpose="mapping/external termination incomplete", mutation="delete mapping or actual-file termination", mutate=mutate_t97, expected_action=None, expected_gate_or_state="INVALID_LOSSLESS_EDGE", expected_issue_code="TRACE.EDGE_MISSING", expected_issue_path="/transformations/mappings", basis_assertions=("target_requires_source_chain",), binding_assertions=("versioned_refs_reachable",), side_effect_assertion="no_claim", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T97]")
T98 = VerticalScenario(test_id="T98", pi300_purpose="bounded outcome 缺要素", mutation="remove one of axis/action/object/tense", mutate=mutate_t98, expected_action=None, expected_gate_or_state="INCOMPLETE", expected_issue_code="SOURCE.FIELD_MISSING", expected_issue_path="/outcome", basis_assertions=("remaining_refs_retained",), binding_assertions=("missing_locator_explicit",), side_effect_assertion="no_outcome_field_inference", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T98]")
T99 = VerticalScenario(test_id="T99", pi300_purpose="prose preview 结构化攻击", mutation="parse Markdown free text as LOSSLESS", mutate=mutate_t99, expected_action=None, expected_gate_or_state="INVALID_TRANSFORMATION", expected_issue_code="TRANSFORMATION.UNSUPPORTED", expected_issue_path="/transformations/0", basis_assertions=("prose_ref_segregated",), binding_assertions=("json_source_required",), side_effect_assertion="no_auto_extraction", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T99]")
T100 = VerticalScenario(test_id="T100", pi300_purpose="value_schema/旧 locator 攻击", mutation="metadata or old top-level identity", mutate=mutate_t100, expected_action=None, expected_gate_or_state="INVALID_DESIGN", expected_issue_code="SOURCE.BINDING_INVALID", expected_issue_path="/source_locators/0", basis_assertions=("source_chain_absent",), binding_assertions=("canonical_nested_binding",), side_effect_assertion="no_dual_write", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T100]")
T101 = VerticalScenario(test_id="T101", pi300_purpose="输出工具/金额/财富结果", mutation="expand beyond copied four fields", mutate=mutate_t101, expected_action=None, expected_gate_or_state="PROHIBITED_OUTPUT", expected_issue_code="OUTPUT.SCOPE_EXCEEDED", expected_issue_path="/statements/0/statement_text", basis_assertions=("lawful_four_field_basis",), binding_assertions=("lossless_refs_unchanged",), side_effect_assertion="no_expanded_publish", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T101]")
T102 = VerticalScenario(test_id="T102", pi300_purpose="UNKNOWN reason registry hit", mutation="registered and unregistered UNKNOWN reason", mutate=mutate_t102, expected_action=None, expected_gate_or_state="VALID_ONLY_REGISTERED", expected_issue_code="GATE.STATE_UNKNOWN", expected_issue_path="/gate/*/reason_codes", basis_assertions=("issue_path_retained",), binding_assertions=("registry_code_exact",), side_effect_assertion="unknown_code_fails", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T102]")
T103 = VerticalScenario(test_id="T103", pi300_purpose="CONDITIONAL risk issue 传播", mutation="inspect payload issues trace statement", mutate=mutate_t103, expected_action=DecisionAction.CONDITIONAL, expected_gate_or_state="VALID_IFF_PRESERVED", expected_issue_code="ISSUE-RISK-UNKNOWN", expected_issue_path="/action/payload", basis_assertions=("same_issue_basis_all_layers",), binding_assertions=("refs_field_equal",), side_effect_assertion="no_dropped_issue", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T103]")
T104 = VerticalScenario(test_id="T104", pi300_purpose="综合 fail-closed", mutation="unknown member plus binding/digest/reason attacks", mutate=mutate_t104, expected_action=None, expected_gate_or_state="INVALID", expected_issue_code="GATE.MEMBER_DECLARATION_INVALID", expected_issue_path="/decision_result", basis_assertions=("all_attack_evidence_retained",), binding_assertions=("locator_gate_bindings_checked",), side_effect_assertion="no_downgrade_repair", pytest_node="tests/f09/test_f09_vertical_matrix.py::test_f09_vertical_matrix[T104]")

SCENARIOS = (T01, T02, T03, T04, T05, T06, T07, T08, T09, T10, T11, T12, T13, T14, T15, T16, T17, T18, T19, T20, T21, T22, T23, T24, T25, T26, T27, T28, T29, T30, T31, T32, T33, T34, T35, T36, T37, T38, T39, T40, T41, T42, T43, T44, T45, T46, T47, T48, T49, T50, T51, T52, T53, T54, T55, T56, T57, T58, T59, T60, T61, T62, T63, T64, T65, T66, T67, T68, T69, T70, T71, T72, T73, T74, T75, T76, T77, T78, T79, T80, T81, T82, T83, T84, T85, T86, T87, T88, T89, T90, T91, T92, T93, T94, T95, T96, T97, T98, T99, T100, T101, T102, T103, T104)
```

`tests/f09/conftest.py` must define all 104 concrete symbols in the preceding mutator block before the scenario module is imported. Each function is independently unit-tested by applying it to `baseline_scenario_bundle(tmp_path)` and asserting the exact changed field path/value plus equality of every non-target field. In particular, compound rows T43/T75/T96/T102/T104 use one fixed literal compound mutation exactly as written, not a parameterized family; additional variants belong in component tests and do not alter the exactly-once vertical node map.

### Literal vertical-matrix test module

The following single fenced block is the sole copy source for `tests/f09/test_f09_vertical_matrix.py`. Its imports are complete and ordered: `pytest` is explicit; `VerticalScenario`, `ScenarioExecution` and `execute_scenario` are owned by and imported from the already initialized `tests.f09.conftest`; `SCENARIOS` is owned by and imported from `tests.f09.data.f09_vertical_scenarios`. The five pure assertion helpers are locally owned and fully defined. There is no wildcard/dynamic import, registry, factory, table parser, hidden helper or implementer-supplied declaration.

```python
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import pytest

from engine.f09.contracts import ArtifactSetState, DecisionAction, DigestRef, RunTrack
from tests.f09.conftest import ScenarioExecution, VerticalScenario, execute_scenario
from tests.f09.data.f09_vertical_scenarios import SCENARIOS


def assert_action_and_state(
    execution: ScenarioExecution,
    expected_action: DecisionAction | None,
    expected_gate_or_state: str,
) -> None:
    run = execution.run_result
    decision = run.decision
    trace = execution.trace_phase
    artifact = execution.artifact_phase
    feedback = execution.feedback_phase
    if expected_action is not None:
        assert decision is not None
        assert decision.action_envelope.selected_action is expected_action
    match expected_gate_or_state:
        case "OUTPUT":
            assert decision is not None and decision.action_envelope.selected_action is DecisionAction.OUTPUT
        case "CONDITIONAL":
            assert decision is not None and decision.action_envelope.selected_action is DecisionAction.CONDITIONAL
        case "ASK":
            assert decision is not None and decision.action_envelope.selected_action is DecisionAction.ASK
        case "ABSTAIN":
            assert decision is not None and decision.action_envelope.selected_action is DecisionAction.ABSTAIN
        case "HUMAN_REVIEW":
            assert decision is not None and decision.action_envelope.selected_action is DecisionAction.HUMAN_REVIEW
        case "RESOLVED":
            assert execution.decision_inputs.gate_inputs[0].declarations.precision_presence == "RESOLVED"
        case "BOTH_NULL_AND_UNRESOLVED":
            declarations = execution.decision_inputs.gate_inputs[0].declarations
            assert (declarations.precision_presence, declarations.precision_value, declarations.precision_unresolved) == ("RESOLVED", None, True)
        case "ABSENT_INVALID":
            assert execution.decision_inputs.gate_inputs[0].declarations.precision_presence == "ABSENT"
            assert execution.overall_status == "INVALID"
        case "UNRESOLVABLE":
            declarations = execution.decision_inputs.gate_inputs[0].declarations
            assert declarations.attempted_digest is not None and declarations.attempted_digest != declarations.precision_digest
        case "VALID":
            assert decision is not None and decision.action_envelope.structural_validity == "VALID"
        case "INVALID":
            assert execution.overall_status == "INVALID"
        case "READY":
            assert decision is not None and len(decision.participation_sets) == 1
            assert decision.participation_sets[0].structural_state == "READY"
        case "CONSUMABLE":
            assert decision is not None and decision.consumption_check.consumable is True
        case "BLOCKED_CONTRACT_MISMATCH":
            assert decision is not None and decision.consumption_check.consumable is False
            assert "CONTRACT.CARDINALITY_MISMATCH" in decision.consumption_check.blocking_issue_ids
        case "CONFLICT_UNRESOLVED":
            assert decision is not None and len(decision.competition_sets) == 1
            assert decision.competition_sets[0].structural_state == "DISPUTED"
        case "GATE_MISSING":
            assert decision is not None and len(decision.gate_sets) == 1
            assert any(record.state == "MISSING" for record in decision.gate_sets[0].records)
        case "INVALID_GATE":
            assert decision is not None and len(decision.gate_sets) == 1
            assert decision.gate_sets[0].issue_ids != ()
        case "LIMITED_ALLOCATION":
            gate = execution.decision_inputs.gate_inputs[0].gate
            assert (gate.allocation_state, gate.risk_state) == ("SATISFIED", "UNKNOWN")
        case "LIMITED_RISK":
            gate = execution.decision_inputs.gate_inputs[0].gate
            assert (gate.allocation_state, gate.risk_state) == ("UNKNOWN", "SATISFIED")
        case "DUAL_AXIS_AVAILABLE":
            gate = execution.decision_inputs.gate_inputs[0].gate
            assert (gate.allocation_state, gate.risk_state) == ("SATISFIED", "SATISFIED")
        case "VALID_ONLY_REGISTERED":
            gate = execution.decision_inputs.gate_inputs[0].gate
            assert (gate.risk_state, gate.risk_reason_codes) == (
                "UNKNOWN",
                ("ISSUE-RISK-UNKNOWN",),
            )
            assert (gate.allocation_state, gate.allocation_reason_codes) == (
                "UNKNOWN",
                ("UNREGISTERED-UNKNOWN-REASON",),
            )
            assert decision is not None
            assert "ISSUE-RISK-UNKNOWN" in decision.action_envelope.reason_codes
            assert "UNREGISTERED-UNKNOWN-REASON" in decision.action_envelope.validation_errors
        case "SAFE_ACTION":
            assert decision is not None and decision.action_envelope.selected_action is not DecisionAction.OUTPUT
        case "BLOCKING":
            assert execution.overall_status == "INVALID"
        case "STATEMENT_INVALID":
            assert trace.status == "INVALID"
            assert trace.errors != ()
        case "TRACE_STATEMENT_INVALID":
            assert trace.status == "INVALID"
            assert trace.errors != ()
        case "VALID_PROJECTION":
            assert trace.status == "VALID" and trace.state_transformation is not None and trace.event_transformation is not None
        case "INVALID_PROJECTION":
            assert trace.status == "INVALID" and trace.errors != ()
        case "INVALID_LOSSLESS_SOURCE":
            assert trace.status == "INVALID"
            assert trace.mapping_source_paths == ()
        case "INVALID_LOSSLESS_EDGE":
            assert trace.status == "INVALID"
            assert trace.terminal_edge_count == 0
        case "INVALID_TRANSFORMATION":
            assert trace.state_transformation is not None and trace.state_transformation.fidelity == "UNSUPPORTED"
        case "INVALID_DESIGN":
            assert execution.decision_inputs.gate_inputs[0].source.canonical_nested_binding is False
        case "INCOMPLETE":
            assert len(execution.decision_inputs.gate_inputs[0].source.outcome_fields) != 4
        case "PROHIBITED_OUTPUT":
            assert trace.input_statement_set is not None and len(trace.input_statement_set.statements) == 1
            assert trace.input_statement_set.statements[0].statement_text == execution.mutated_bundle.trace.statement_text
            assert trace.errors != ()
        case "VALID_IFF_PRESERVED":
            assert decision is not None and trace.input_statement_set is not None and len(trace.input_statement_set.statements) == 1
            assert decision.action_envelope.nonblocking_issue_ids == trace.input_statement_set.statements[0].issue_ids
        case "LOSSY":
            assert trace.event_transformation is not None and trace.event_transformation.fidelity == "LOSSY"
        case "PARTIAL_RECORDS_WRITE_FAILED":
            assert artifact.write_called is True
            assert artifact.fail_after == "STATEMENT_RECORDS"
            assert artifact.status == "INVALID"
        case "PARTIAL_INDEX_WRITE_FAILED":
            assert artifact.write_called is True
            assert artifact.fail_after == "STATEMENT_INDEX"
            assert artifact.status == "INVALID"
        case "STALE_MIXED_REVISION":
            assert artifact.inspected_manifest is not None
            assert artifact.inspected_manifest.state is ArtifactSetState.STALE_MIXED_REVISION
        case "DIGEST_MISMATCH":
            assert artifact.inspected_manifest is not None
            assert artifact.inspected_manifest.state is ArtifactSetState.DIGEST_MISMATCH
        case "NO_OP_SUCCESS":
            assert artifact.write_manifest is not None and artifact.retry_manifest is not None
            assert artifact.write_manifest.digest == artifact.retry_manifest.digest
        case "CONFLICT":
            assert artifact.retry_manifest is None and artifact.errors != ()
        case "STALE_SET_NOT_READY":
            assert artifact.inspected_manifest is not None and any(record.state == "STALE" for record in artifact.inspected_manifest.records)
            assert artifact.inspected_manifest.state != "COMPLETE_VERIFIED"
        case "MISMATCH_SET_NOT_READY":
            assert artifact.inspected_manifest is not None and any(record.state == "MISMATCH" for record in artifact.inspected_manifest.records)
            assert artifact.inspected_manifest.state != "COMPLETE_VERIFIED"
        case "SUPERSEDED":
            assert artifact.inspection_input is not None and len(artifact.inspection_input.records) == 2
            assert artifact.inspection_input.records[0].state == "SUPERSEDED"
        case "UNBOUND_INELIGIBLE":
            assert len(feedback.bindings) == 1 and feedback.bindings[0].status == "UNBOUND"
            assert len(feedback.eligibility_records) == 1 and feedback.eligibility_records[0].status == "INELIGIBLE"
        case "INVALID_INELIGIBLE":
            assert len(feedback.bindings) == 1 and feedback.bindings[0].status == "INVALID"
            assert len(feedback.eligibility_records) == 1 and feedback.eligibility_records[0].status == "INELIGIBLE"
        case "INVALID_AUDIT_ONLY":
            assert len(feedback.bindings) == 1
            assert feedback.bindings[0].track_match == "MISMATCH"
            assert len(feedback.eligibility_records) == 1
            assert feedback.eligibility_records[0].status != "ELIGIBLE"
        case "BOUND":
            assert len(feedback.bindings) == 1
            assert feedback.bindings[0].status == "BOUND"
        case "ELIGIBLE":
            assert len(feedback.eligibility_records) == 1
            assert feedback.eligibility_records[0].status == "ELIGIBLE"
        case "REVISION_KEY_CHANGED":
            assert feedback.submission is not None
            assert len(feedback.submission.feedback_items) == 1
            assert feedback.submission.feedback_items[0].target_statement_revision_id == "STMT-REV-3"
        case "POLICY_KEY_CHANGED":
            assert len(feedback.eligibility_records) == 1
            assert feedback.eligibility_records[0].policy_id == "PRODUCTION-STATEMENT-ELIGIBILITY"
            assert feedback.eligibility_records[0].policy_version == "policy-v1"
            assert feedback.operation_result is not None
            assert feedback.operation_result.operation_disposition == "NEW_OPERATION"
        case "ITEM_SET_KEY_CHANGED":
            assert feedback.submission is not None
            assert len(feedback.submission.feedback_items) == 2
            assert tuple(item.feedback_item_id for item in feedback.submission.feedback_items) == ("FBI-1", "FBI-2")
        case "NEW_OPERATION_CHANGED_SOURCE":
            assert feedback.submission is not None
            baseline_digest = DigestRef(
                "sha256",
                "RFC8785-JCS-UTF8",
                sha256(
                    execution.baseline_bundle.feedback.source_digest.encode("utf-8")
                ).hexdigest(),
            )
            assert (
                feedback.submission.source_snapshot_ref.content_digest
                != baseline_digest
            )
            # The feedback adapter already asserts the producer-owned operation receipt;
            # source-snapshot and whole-submission digests are distinct identities and
            # are deliberately not compared here.
        case "SEMANTICS_UNCHANGED":
            assert decision is not None
            assert execution.mutated_bundle.gate != execution.baseline_bundle.gate
            assert tuple(record.declared_member_id for record in decision.gate_sets[0].records) == execution.baseline_bundle.gate.declared_member_ids
        case _:
            raise AssertionError("unknown expected_gate_or_state token: " + expected_gate_or_state)


# PhaseIssueObservation is owned by the sole conftest block and is populated only by
# the three adapters' actual validator/coordinator detection branches. The matrix
# module deliberately defines no phase scanner and performs no fixture re-judgment.


def assert_issue(
    execution: ScenarioExecution,
    expected_issue_code: str | None,
    expected_issue_path: str | None,
) -> None:
    run = execution.run_result
    decision_issue_pairs = tuple(
        (code, issue.field_path)
        for issue in (() if run.decision is None else run.decision.issues)
        for code in (issue.issue_id,) + issue.reason_codes
    )
    phase_issue_pairs = tuple(
        (issue.code, issue.path)
        for issue in (
            execution.trace_phase.issues
            + execution.artifact_phase.issues
            + execution.feedback_phase.issues
        )
    )
    action_issue_codes = () if run.decision is None else (
        run.decision.action_envelope.blocking_issue_ids
        + run.decision.action_envelope.nonblocking_issue_ids
        + run.decision.action_envelope.reason_codes
        + run.decision.action_envelope.validation_errors
    )
    trace_issue_codes = () if run.trace is None else run.trace.blocking_issue_ids
    statement_issue_codes = () if run.statement_set is None else (
        run.statement_set.issue_ids
        + tuple(code for statement in run.statement_set.statements for code in statement.issue_ids)
    )
    artifact_issue_codes = () if run.manifest is None else tuple(
        code for record in run.manifest.records for code in record.issue_ids
    )
    feedback_issue_codes = tuple(
        code for binding in execution.feedback_phase.bindings for code in binding.issue_ids
    ) + tuple(
        code
        for record in execution.feedback_phase.eligibility_records
        for code in record.blocking_reason_codes
    )
    phase_errors = execution.trace_phase.errors + execution.artifact_phase.errors + execution.feedback_phase.errors
    if expected_issue_code is None:
        assert expected_issue_path is None
        assert all(observation.issue_codes == () for observation in run.observations)
        if run.decision is not None:
            assert run.decision.issues == ()
            assert run.decision.action_envelope.blocking_issue_ids == ()
            assert run.decision.action_envelope.nonblocking_issue_ids == ()
            assert run.decision.action_envelope.reason_codes == ()
            assert run.decision.action_envelope.validation_errors == ()
        if run.trace is not None:
            assert run.trace.blocking_issue_ids == ()
        if run.statement_set is not None:
            assert run.statement_set.issue_ids == ()
            assert all(statement.issue_ids == () for statement in run.statement_set.statements)
        if run.manifest is not None:
            assert all(record.issue_ids == () for record in run.manifest.records)
        assert all(binding.issue_ids == () for binding in execution.feedback_phase.bindings)
        assert all(record.blocking_reason_codes == () for record in execution.feedback_phase.eligibility_records)
        assert phase_issue_pairs == ()
        assert phase_errors == ()
    else:
        assert expected_issue_path is not None
        # A positive pair must be emitted by one typed surface: either one
        # canonical DecisionIssue or one adapter-owned PhaseIssueObservation.
        # Code-only surfaces, exception text, fixture stimulus and baseline diffs
        # never supply a path and cannot be cross-joined with another surface.
        assert (expected_issue_code, expected_issue_path) in (
            decision_issue_pairs + phase_issue_pairs
        )
        if expected_issue_path == "/gate/*/reason_codes":
            # T102 retains an additional stimulus check, but this check cannot
            # replace the same-surface typed-pair assertion above.
            gate = execution.mutated_bundle.gate
            assert expected_issue_code == "GATE.STATE_UNKNOWN"
            assert gate.risk_reason_codes == ("ISSUE-RISK-UNKNOWN",)
            assert gate.allocation_reason_codes == ("UNREGISTERED-UNKNOWN-REASON",)
            assert execution.overall_status == "INVALID"


def assert_basis(execution: ScenarioExecution, expected_assertions: tuple[str, ...]) -> None:
    decision_input = execution.mutated_bundle.decision
    decision = execution.run_result.decision
    action_basis_ids = () if decision is None else decision.action_envelope.basis_record_ids
    statement_basis_ids = (
        ()
        if execution.trace_phase.input_statement_set is None
        else execution.trace_phase.input_statement_set.statements[0].basis_record_ids
    )
    gate_input = execution.mutated_bundle.gate
    participation_input = execution.mutated_bundle.participation
    root_timing_input = execution.mutated_bundle.root_timing
    source_input = execution.mutated_bundle.source
    trace_input = execution.mutated_bundle.trace
    artifact_input = execution.mutated_bundle.artifacts
    feedback_input = execution.mutated_bundle.feedback
    for token in expected_assertions:
        match token:
            case "nonempty":
                assert action_basis_ids == ("GR-ALLOCATION", "GR-RISK", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL", "PR-REALITY-OUTPUT", "DISP-F09-INCLUDED")
            case "exact_local_records":
                assert action_basis_ids == ("GR-ALLOCATION", "GR-RISK", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL", "PR-REALITY-OUTPUT", "DISP-F09-INCLUDED")
            case "condition_refs":
                assert decision_input.payload_issue_ids == ("ISSUE-RISK-UNKNOWN",)
            case "six_gates":
                assert action_basis_ids == ("GR-ALLOCATION", "GR-RISK", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL", "PR-REALITY-OUTPUT", "DISP-F09-INCLUDED")
            case "question_issue_path_resume":
                assert decision_input.question_paths == ("/gate/ATTRIBUTION",)
            case "both_candidate_evidence":
                assert decision_input.dispositions == ("DISP-F09-UNRESOLVED",)
            case "both_sides":
                assert gate_input.attribution_state == "CONFLICT" and decision_input.payload_issue_ids == ("GATE.FIELD_CONFLICT",)
            case "review_scope":
                assert decision_input.selected_action == "HUMAN_REVIEW" and decision_input.payload_type == "HumanReviewPayload"
            case "declaration_ref_nonempty":
                assert execution.mutated_bundle.declarations.precision_digest == "DG-PRECISION-V1"
            case "value_presence_separate":
                assert (execution.mutated_bundle.declarations.precision_value, execution.mutated_bundle.declarations.precision_unresolved) == (None, True)
            case "no_borrowed_basis":
                assert decision_input.basis_gate_ids == execution.baseline_bundle.decision.basis_gate_ids
            case "unknown_path_retained":
                assert gate_input.risk_reason_codes == ("GATE.STATE_UNKNOWN",)
            case "no_satisfied_gate_basis":
                assert source_input.locator_available is False and decision_input.basis_gate_ids == execution.baseline_bundle.decision.basis_gate_ids
            case "attempted_ref_retained":
                assert execution.mutated_bundle.declarations.attempted_digest == "DG-PRECISION-DRIFT"
            case "no_action_basis":
                assert execution.mutated_bundle.declarations.precision_presence == "NOT_APPLICABLE" and decision_input.basis_gate_ids == execution.baseline_bundle.decision.basis_gate_ids
            case "chart_refs_context_only":
                assert (source_input.reality_track, gate_input.supporting_evidence_tracks) == ("CHART_STRUCTURE", ("CHART_STRUCTURE",))
            case "hypothesis_refs_retained":
                assert (source_input.reality_track, gate_input.supporting_evidence_tracks) == ("UNVERIFIED_HYPOTHESIS", ("UNVERIFIED_HYPOTHESIS",))
            case "both_evidence_sets":
                assert decision_input.dispositions == ("DISP-F09-UNRESOLVED-F08-STRONG",)
            case "consequence_excluded":
                assert decision_input.consequence_only is True and gate_input.allocation_state == "MISSING"
            case "ledgers_separate":
                assert (root_timing_input.root_state, root_timing_input.timing_state, root_timing_input.timing_rewrites_root) == ("VIOLATED", "SATISFIED", True)
            case "declaration_refs_separate":
                declarations = execution.mutated_bundle.declarations
                assert declarations.precision_type == "VALIDATION_PLAN" and declarations.validation_type == "VALIDATION_PLAN"
                assert declarations.precision_digest != declarations.validation_digest
            case "action_basis_unchanged":
                assert decision_input.basis_gate_ids == execution.baseline_bundle.decision.basis_gate_ids
            case "one_anchor_two_dropped":
                assert trace_input.rule_ref_ids == ("RULE-F09-ANCHOR", "RULE-F09-DROPPED-1", "RULE-F09-DROPPED-2") and trace_input.transformation_fidelity == "LOSSY"
            case "input_snapshots_logged":
                assert artifact_input.records_write_outcome == "FAILED" and execution.artifact_phase.fail_after == "STATEMENT_RECORDS"
            case "prior_records_retained":
                assert artifact_input.index_write_outcome == "FAILED" and execution.artifact_phase.fail_after == "STATEMENT_INDEX"
            case "current_old_refs_visible":
                assert artifact_input.index_revision == "STMT-REV-1" and execution.artifact_phase.inspection_input is not None
            case "original_inputs_retained":
                assert len(execution.artifact_phase.projection_digests) == 3
            case "zero_learning_targets":
                assert feedback_input.target_statement_id == "STMT-UNKNOWN" and feedback_input.anchor_status == "UNMAPPED"
            case "old_target_retained":
                assert feedback_input.target_revision == "STMT-REV-1"
            case "same_snapshots":
                assert (artifact_input.retry_key_digest, artifact_input.retry_report_payload, artifact_input.retry_records_payload, artifact_input.retry_index_payload) == ("IDEM-KEY-A", b"F09 staged report\n", b"DG-ARTIFACT-V2", b"STMT-REV-2")
            case "both_attempt_refs":
                assert (artifact_input.retry_key_digest, artifact_input.retry_records_payload) == ("IDEM-KEY-A", b"DG-PAYLOAD-CONFLICT")
            case "audit_refs_only":
                assert feedback_input.source_track is RunTrack.V5_V6_PREPROD and feedback_input.target_track is RunTrack.STAGED_L6
            case "card_ref_retained":
                assert trace_input.card_runtime_status == "IMPLEMENTED"
            case "f09_disposition_only":
                assert decision_input.candidate_ids == ("CAND-F09",) and decision_input.f08_runtime_objects == ()
            case "forged_object_retained":
                assert decision_input.f08_runtime_objects == ("CAND-F08", "ACTION-F08", "STMT-F08")
            case "singleton_basis_retained":
                assert decision_input.candidate_ids == ("CAND-F09",) and decision_input.require_two_candidates is True
            case "ref_nonempty":
                declarations = execution.mutated_bundle.declarations
                assert (declarations.validation_type, declarations.validation_digest, declarations.identity_complete) == ("VALIDATION_PLAN", "DG-VALIDATION-V1", True)
            case "attempted_ref_visible":
                assert execution.mutated_bundle.declarations.identity_complete is False
            case "decision_basis_stable":
                assert decision_input.basis_gate_ids == execution.baseline_bundle.decision.basis_gate_ids and execution.mutated_bundle.declarations.trace_precision_digest == "DG-PRECISION-TRACE-DRIFT"
            case "nonempty_exact_basis":
                assert decision_input.basis_gate_ids == execution.baseline_bundle.decision.basis_gate_ids and decision_input.basis_participation_ids == ("PR-REALITY-OUTPUT",)
            case "issue_refs_preserved":
                assert decision_input.payload_issue_ids == ("ISSUE-RISK-UNKNOWN",)
            case "original_refs_nonempty":
                assert decision_input.question_paths == ("/gate/ATTRIBUTION",)
            case "blocking_basis":
                assert decision_input.payload_issue_ids == ("COMPETITION.UNRESOLVED",)
            case "both_conflict_sides":
                assert decision_input.payload_issue_ids == ("GATE.FIELD_CONFLICT",)
            case "basis_retained_for_issue":
                assert decision_input.basis_gate_ids == execution.baseline_bundle.decision.basis_gate_ids and decision_input.payload_type == "OutputPayload"
            case "trace_ref_required":
                assert trace_input.statement_set_complete is False
            case "complete_basis_ids":
                assert trace_input.statement_complete is False and trace_input.statement_basis_ids == execution.baseline_bundle.trace.statement_basis_ids
            case "six_independent_ids":
                assert participation_input.role_ids == ("ROLE-ALLOCATION", "ROLE-RISK", "ROLE-REALITY", "ROLE-ATTRIBUTION", "ROLE-SOURCE", "ROLE-TEMPORAL")
            case "no_cross_role_basis":
                assert "ROLE-SOURCE" not in participation_input.role_ids and participation_input.reality_record_id == "PR-REALITY-BORROWED"
            case "each_role_closes_path":
                assert participation_input.state_support_aligned is False and participation_input.source_decision_ref == "DEC-F09-MISMATCH"
            case "chart_evidence_only":
                assert (root_timing_input.root_state, root_timing_input.root_reason_code, root_timing_input.root_issue_path) == ("SATISFIED", None, None)
            case "timing_evidence_local":
                assert (root_timing_input.timing_state, root_timing_input.timing_reason_code, root_timing_input.timing_issue_path) == ("SATISFIED", None, None)
            case "both_ledgers_referenced":
                assert (root_timing_input.root_state, root_timing_input.root_reason_code, root_timing_input.root_issue_path) == ("UNKNOWN", None, None)
            case "item_targets_explicit":
                assert feedback_input.item_ids == ("FBI-1", "FBI-2")
            case "target_refs_explicit":
                assert feedback_input.seven_matches == ("MATCH", "MATCH", "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "MATCH")
            case "learning_excluded_refs_explicit":
                assert feedback_input.policy_version == "policy-v1" and feedback_input.eligibility_complete is True
            case "revised_target_input":
                assert feedback_input.target_revision == "STMT-REV-3"
            case "same_target_refs":
                assert feedback_input.prior_policy_version == "policy-v2" and feedback_input.policy_version == "policy-v1" and feedback_input.target_revision == execution.baseline_bundle.feedback.target_revision
            case "full_item_set_included":
                assert feedback_input.item_ids == ("FBI-1", "FBI-2")
            case "source_ref_retained":
                assert feedback_input.source_digest == "DG-FEEDBACK-B"
            case "three_layers_same_ordered_ids":
                assert action_basis_ids == ("GR-ALLOCATION", "GR-RISK", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL", "PR-REALITY-OUTPUT", "DISP-F09-INCLUDED")
                assert statement_basis_ids == ("GR-ALLOCATION", "GR-RISK", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL", "PR-REALITY-OUTPUT", "DISP-F09-INCLUDED", "RTC-ROOT", "RTC-TIMING")
            case "bad_id_retained":
                assert decision_input.basis_participation_ids == ("PARTICIPATION-SET-CONTAINER",)
            case "exact_candidate_basis":
                assert decision_input.candidate_ids == ("CAND-F09",) and decision_input.disposition_refs == ("DISP-F09-INCLUDED",)
            case "bad_ref_explicit":
                assert decision_input.disposition_refs == ("CAND-NOT-IN-SET",)
            case "zero_match":
                assert decision_input.dispositions == () and decision_input.disposition_refs == ("DISP-F09-INCLUDED",)
            case "both_records_retained":
                assert decision_input.dispositions == ("DISP-F09-INCLUDED-A", "DISP-F09-INCLUDED-B")
            case "disposition_basis_retained":
                assert decision_input.dispositions == ("DISP-F09-CONDITIONAL",) and decision_input.selected_action == "OUTPUT"
            case "condition_issues_retained":
                assert decision_input.dispositions == ("DISP-F09-CONDITIONAL",) and decision_input.selected_action == "CONDITIONAL"
            case "attempts_state_appropriate":
                assert artifact_input.item_states == ("NOT_ATTEMPTED", "WRITING", "WRITTEN_UNVERIFIED", "VERIFIED", "FAILED", "STALE", "MISMATCH", "SUPERSEDED")
            case "not_started_ref_retained":
                assert artifact_input.item_states == ("NOT_STARTED",)
            case "written_ref_retained":
                assert artifact_input.item_states == ("WRITTEN",)
            case "old_input_refs":
                assert (artifact_input.item_states, artifact_input.statement_revision) == (("STALE",), "STMT-REV-1")
            case "attempt_retained":
                assert (artifact_input.item_states, artifact_input.observed_digest) == (("MISMATCH",), "DG-ARTIFACT-MISMATCH")
            case "old_new_refs_auditable":
                assert (artifact_input.supersedes_revision, artifact_input.statement_revision) == ("STMT-REV-1", "STMT-REV-2")
            case "blocking_competition_basis":
                assert decision_input.dispositions == ("DISP-F09-UNRESOLVED",) and decision_input.selected_action == "ABSTAIN"
            case "bijection_by_member_id":
                assert gate_input.member_ids == ("ALLOCATION", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "TEMPORAL")
                assert gate_input.declared_member_ids == gate_input.member_ids
            case "no_inferred_member":
                assert gate_input.member_ids == ("ALLOCATION", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "SOURCE")
            case "bad_record_retained":
                assert len(gate_input.member_ids) == 6
                assert gate_input.member_ids[-1] == "UNKNOWN_MEMBER"
            case "six_ids_retained":
                assert len(gate_input.record_gate_definition_refs) == 6
                assert gate_input.record_gate_definition_refs[-1] == "REF-GATE-F09-V1/SOURCE"
            case "member_id_insufficient":
                assert len(gate_input.declared_member_ids) == 6
                assert gate_input.declared_member_ids[0] == "ALLOCATION@V2:DG-DRIFT"
            case "mutated_fields_visible":
                assert len(gate_input.evaluation_binding_digests) == 6
                assert gate_input.allocation_state == "CONFLICT"
                assert gate_input.evaluation_binding_digests[0] == "DG-ALLOC"
            case "member_local_basis_checked":
                assert gate_input.member_ids[:2] == ("RISK", "ALLOCATION") and gate_input.evaluation_binding_digests[:2] == ("DG-ALLOC", "DG-RISK")
            case "basis_values_unchanged":
                assert gate_input.member_ids == ("TEMPORAL", "SOURCE", "ATTRIBUTION", "REALITY", "RISK", "ALLOCATION")
                assert gate_input.evaluation_binding_digests == tuple(reversed(execution.baseline_bundle.gate.evaluation_binding_digests))
            case "risk_unknown_six_record_chain":
                assert len(gate_input.member_ids) == 6
                assert (gate_input.allocation_state, gate_input.risk_state, gate_input.risk_reason_codes) == ("SATISFIED", "UNKNOWN", ("GATE.STATE_UNKNOWN",))
            case "allocation_unknown_six_record_chain":
                assert len(gate_input.member_ids) == 6
                assert (gate_input.allocation_state, gate_input.allocation_reason_codes, gate_input.risk_state) == ("UNKNOWN", ("GATE.STATE_UNKNOWN",), "SATISFIED")
            case "six_satisfied_records":
                assert (gate_input.allocation_state, gate_input.risk_state, gate_input.reality_state, gate_input.attribution_state, gate_input.source_state, gate_input.temporal_state) == ("SATISFIED",) * 6
            case "each_member_independent":
                assert gate_input.path_complete is False and gate_input.record_gate_definition_refs[0] == "REF-BROKEN"
            case "invalid_support_retained":
                assert gate_input.supporting_evidence_tracks == ("CHART_STRUCTURE", "UNVERIFIED_HYPOTHESIS")
            case "state_support_issues_align":
                assert (participation_input.scenario_id, participation_input.reality_record_id, participation_input.state_support_aligned) == ("ASK", "PR-REALITY-ASK", True)
            case "local_basis_required":
                assert (participation_input.scenario_id, participation_input.reality_record_id) == ("ASK", "PR-REALITY-OUTPUT")
            case "three_layers_ordered_equal":
                assert action_basis_ids == ("GR-ALLOCATION", "GR-RISK", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL", "PR-REALITY-OUTPUT", "DISP-F09-INCLUDED")
                assert statement_basis_ids == ("GR-RISK", "GR-ALLOCATION", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL", "PR-REALITY-OUTPUT", "DISP-F09-INCLUDED", "RTC-ROOT", "RTC-TIMING")
                assert statement_basis_ids != execution.baseline_bundle.trace.statement_basis_ids
            case "both_source_chains_reachable":
                assert source_input.source_kind == "IMMUTABLE_JSON_SNAPSHOT" and source_input.canonical_nested_binding is True
            case "three_lossless_mappings":
                assert source_input.state_fields == ("level", "position", "as_of") and execution.trace_phase.state_transformation is not None and len(execution.trace_phase.state_transformation.field_mappings) == 3
            case "six_lossless_mappings":
                assert len(source_input.event_fields) == 6 and execution.trace_phase.event_transformation is not None and len(execution.trace_phase.event_transformation.field_mappings) == 6
            case "bad_chain_explicit":
                assert (source_input.state_object_id, source_input.event_object_id) == ("SOURCE-EVENT-1", "SOURCE-STATE-1")
            case "four_lossless_mappings":
                assert source_input.outcome_fields == ("axis", "action", "object", "tense")
            case "broken_input_ref_shown":
                assert source_input.source_field_present is False
            case "envelope_payload_refs_retained":
                assert (source_input.snapshot_id, source_input.snapshot_schema_version, source_input.contract_version, source_input.content_digest, source_input.payload_digest) == ("SNAP-F09-DRIFT", "snapshot-v2", "PI300-V2", "DG-SNAPSHOT-DRIFT", "DG-PAYLOAD-DRIFT")
            case "target_requires_source_chain":
                assert trace_input.field_mapping_count == 0 and trace_input.external_source_terminated is False
            case "remaining_refs_retained":
                assert source_input.outcome_fields == ("axis", "action", "object")
            case "prose_ref_segregated":
                assert source_input.source_kind == "MARKDOWN_FREE_TEXT" and trace_input.transformation_fidelity == "LOSSLESS"
            case "source_chain_absent":
                assert source_input.state_pointer == "/metadata/state" and source_input.canonical_nested_binding is False
            case "lawful_four_field_basis":
                assert source_input.outcome_fields == ("axis", "action", "object", "tense")
                assert execution.trace_phase.input_statement_set is not None
                assert execution.trace_phase.input_statement_set.statements[0].statement_text == "Use wealth tool X; invest amount 100000; guaranteed wealth result"
            case "issue_path_retained":
                assert (gate_input.risk_reason_codes, gate_input.allocation_reason_codes) == (("ISSUE-RISK-UNKNOWN",), ("UNREGISTERED-UNKNOWN-REASON",))
            case "same_issue_basis_all_layers":
                assert decision_input.payload_issue_ids == trace_input.issue_propagation_ids == ("ISSUE-RISK-UNKNOWN",)
            case "all_attack_evidence_retained":
                assert len(gate_input.member_ids) == 6
                assert len(gate_input.record_gate_definition_refs) == 6
                assert len(gate_input.evaluation_binding_digests) == 6
                assert gate_input.member_ids[-1] == "UNKNOWN_MEMBER"
                assert gate_input.record_gate_definition_refs[-1] == "REF-GATE-F09-FORGED"
                assert gate_input.evaluation_binding_digests[-1] == "DG-FORGED"
                assert execution.mutated_bundle.declarations.precision_digest == "DG-PRECISION-FORGED"
                assert source_input.payload_digest == "DG-PAYLOAD-FORGED"
            case _:
                raise AssertionError("unknown basis_assertion token: " + token)


def assert_bindings(execution: ScenarioExecution, expected_assertions: tuple[str, ...]) -> None:
    declarations = execution.decision_inputs.gate_inputs[0].declarations
    source = execution.decision_inputs.gate_inputs[0].source
    participation = execution.decision_inputs.gate_inputs[0].participation
    decision_input = execution.decision_inputs.competition_input.decision
    gate = execution.mutated_bundle.gate
    artifact = execution.artifact_phase
    feedback = execution.feedback_phase
    for token in expected_assertions:
        match token:
            case "declarations_exact":
                assert declarations == execution.mutated_bundle.declarations
                assert (declarations.precision_presence, declarations.precision_digest) == ("RESOLVED", "DG-PRECISION-V1")
            case "risk_unknown_exact":
                assert (gate.risk_state, gate.risk_reason_codes) == ("UNKNOWN", ("ISSUE-RISK-UNKNOWN",))
            case "missing_path_bound":
                assert (gate.attribution_state, decision_input.question_paths) == ("MISSING", ("/gate/ATTRIBUTION",))
            case "conflict_refs_exact":
                assert (gate.attribution_state, decision_input.payload_issue_ids) == ("CONFLICT", ("GATE.FIELD_CONFLICT",))
            case "resolved_ref_exact":
                assert (declarations.precision_presence, declarations.precision_value, declarations.precision_digest) == ("RESOLVED", None, "DG-PRECISION-V1")
            case "resolved_ref_retained":
                assert (declarations.precision_value, declarations.precision_unresolved, declarations.precision_digest) == (None, True, "DG-PRECISION-V1")
            case "absent_reason_exact":
                assert declarations.precision_presence == "ABSENT"
            case "unknown_digest_exact":
                assert (gate.risk_state, gate.risk_reason_codes, declarations.precision_digest) == ("UNKNOWN", ("GATE.STATE_UNKNOWN",), "DG-PRECISION-V1")
            case "unavailable_issues_nonempty":
                assert (source.locator_available, source.content_digest) == (False, "DG-SNAPSHOT-A")
            case "unresolvable_branch_exact":
                assert (declarations.precision_presence, declarations.attempted_digest) == ("UNRESOLVABLE", "DG-PRECISION-DRIFT")
            case "not_applicable_reason_visible":
                assert declarations.precision_presence == "NOT_APPLICABLE"
            case "both_declarations_exact":
                assert (declarations.precision_digest, declarations.statement_precision_digest) == ("DG-PRECISION-V1", "DG-PRECISION-STATEMENT-DRIFT")
            case "type_id_path_exact":
                assert (declarations.precision_type, declarations.validation_type) == ("VALIDATION_PLAN", "VALIDATION_PLAN")
            case "field_path_locator_only":
                assert (declarations.validation_type, declarations.validation_digest, declarations.identity_complete) == ("VALIDATION_PLAN", "DG-VALIDATION-V1", True)
            case "resolved_identity_exact":
                assert (declarations.precision_presence, declarations.precision_unresolved, declarations.identity_complete) == ("RESOLVED", True, True)
            case "no_guessed_match":
                assert declarations.identity_complete is False
            case "both_refs_field_equal":
                assert declarations.trace_precision_digest == "DG-PRECISION-TRACE-DRIFT"
                assert declarations.precision_digest == "DG-PRECISION-V1"
            case "source_version_refs_exact":
                assert (source.snapshot_schema_version, source.contract_version) == ("reality-fact-source-snapshot.v1", "pi-300-f09-source-snapshots-v1")
            case "declarations_revision_exact":
                assert (declarations.precision_contract_version, declarations.statement_precision_digest) == ("PI210-V1", "DG-PRECISION-V1")
            case "chart_track_exact":
                assert source.reality_track == "CHART_STRUCTURE"
            case "hypothesis_track_exact":
                assert source.reality_track == "UNVERIFIED_HYPOTHESIS"
            case "source_refs_retained":
                assert (source.reality_track, gate.allocation_state) == ("REALITY_FACT", "MISSING")
            case "source_refs_reachable":
                assert (source.snapshot_id, source.content_digest) == ("PI-300-F09-SOURCE-SNAPSHOT-V1", "67517fe2d04fb0fe580e031643dab2ad53fcdb8c90707ba4d496c316dd87f5e7")
            case "evidence_track_bound":
                assert (gate.reality_state, gate.supporting_evidence_tracks) == ("SATISFIED", ("CHART_STRUCTURE", "UNVERIFIED_HYPOTHESIS"))
            case "two_source_binding_branches":
                assert (source.source_kind, source.canonical_nested_binding) == ("IMMUTABLE_JSON_SNAPSHOT", True)
            case "object_root_locators_exact":
                assert (source.state_object_id, source.state_pointer, source.state_fields) == ("SOURCE-STATE-1", "/value", ("level", "position", "as_of"))
            case "same_event_identity":
                assert (source.event_object_id, source.event_pointer) == ("SOURCE-EVENT-1", "/value")
                assert len(source.event_fields) == 6
            case "object_pointer_temporal_bound":
                assert (source.state_object_id, source.event_object_id) == ("SOURCE-EVENT-1", "SOURCE-STATE-1")
            case "value_schema_null_refs_exact":
                assert source.outcome_fields == ("axis", "action", "object", "tense")
            case "no_metadata_substitute":
                assert (source.source_field_present, source.state_pointer) == (False, "/value")
            case "five_fields_payload_digest_exact":
                assert (source.snapshot_id, source.snapshot_schema_version, source.contract_version, source.content_digest, source.payload_digest) == ("SNAP-F09-DRIFT", "snapshot-v2", "PI300-V2", "DG-SNAPSHOT-DRIFT", "DG-PAYLOAD-DRIFT")
            case "versioned_refs_reachable":
                assert (source.snapshot_id, source.contract_version, execution.mutated_bundle.trace.external_source_terminated) == ("PI-300-F09-SOURCE-SNAPSHOT-V1", "pi-300-f09-source-snapshots-v1", False)
            case "missing_locator_explicit":
                assert source.outcome_fields == ("axis", "action", "object")
            case "json_source_required":
                assert source.source_kind == "MARKDOWN_FREE_TEXT"
            case "canonical_nested_binding":
                assert (source.state_pointer, source.canonical_nested_binding) == ("/metadata/state", False)
            case "lossless_refs_unchanged":
                assert (source.outcome_fields, source.content_digest) == (("axis", "action", "object", "tense"), "DG-SNAPSHOT-A")
            case "f08_reference_absent":
                assert decision_input.f08_runtime_objects == ()
            case "f08_forged_objects_exact":
                assert decision_input.f08_runtime_objects == ("CAND-F08", "ACTION-F08", "STMT-F08")
            case "f08_identity_only":
                assert decision_input.dispositions == ("DISP-F09-UNRESOLVED-F08-STRONG",)
                assert decision_input.candidate_ids == ("CAND-F09",)
            case "f08_ref_reachable":
                assert (decision_input.candidate_ids, decision_input.f08_runtime_objects) == (("CAND-F09",), ())
            case "contract_ref_exact":
                assert (decision_input.candidate_ids, decision_input.require_two_candidates) == (("CAND-F09",), True)
            case "output_discriminator":
                assert (decision_input.selected_action, decision_input.payload_type) == ("OUTPUT", "OutputPayload")
            case "conditional_discriminator":
                assert (decision_input.selected_action, decision_input.payload_type) == ("CONDITIONAL", "ConditionalPayload")
            case "ask_discriminator":
                assert (decision_input.selected_action, decision_input.payload_type) == ("ASK", "AskPayload")
            case "abstain_discriminator":
                assert (decision_input.selected_action, decision_input.payload_type) == ("ABSTAIN", "AbstainPayload")
            case "review_discriminator":
                assert (decision_input.selected_action, decision_input.payload_type) == ("HUMAN_REVIEW", "HumanReviewPayload")
            case "discriminator_mismatch":
                assert (decision_input.selected_action, decision_input.payload_type) == ("ASK", "OutputPayload")
            case "unique_disposition_ref":
                assert len(decision_input.dispositions) == 1
                assert len(decision_input.disposition_refs) == 1
                assert decision_input.dispositions == decision_input.disposition_refs
            case "current_result_scope":
                assert decision_input.disposition_refs == ("CAND-NOT-IN-SET",)
            case "current_result_only":
                assert (decision_input.dispositions, decision_input.disposition_refs) == ((), ("DISP-F09-INCLUDED",))
            case "uniqueness_violated":
                assert decision_input.dispositions == ("DISP-F09-INCLUDED-A", "DISP-F09-INCLUDED-B")
            case "action_mapping_exact":
                assert (decision_input.selected_action, decision_input.dispositions) == ("OUTPUT", ("DISP-F09-CONDITIONAL",))
            case "disposition_exact":
                assert (decision_input.selected_action, decision_input.dispositions, decision_input.disposition_refs) == ("ABSTAIN", ("DISP-F09-UNRESOLVED",), ("DISP-F09-UNRESOLVED",))
            case "scenario_identity_bound":
                assert (participation.scenario_id, participation.reality_record_id) == ("ASK", "PR-REALITY-OUTPUT")
            case "record_identity_valid":
                assert decision_input.basis_gate_ids == execution.baseline_bundle.decision.basis_gate_ids
                assert execution.mutated_bundle.trace.statement_basis_ids != execution.baseline_bundle.trace.statement_basis_ids
            case "refs_field_equal":
                assert decision_input.payload_issue_ids == execution.mutated_bundle.trace.issue_propagation_ids == ("ISSUE-RISK-UNKNOWN",)
            case "records_resolve_current_result":
                assert execution.run_result.decision is not None
                assert execution.run_result.decision.action_envelope.basis_record_ids == ("GR-ALLOCATION", "GR-RISK", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL", "PR-REALITY-OUTPUT", "DISP-F09-INCLUDED")
                assert execution.trace_phase.input_statement_set is not None
                assert execution.trace_phase.input_statement_set.statements[0].basis_record_ids == ("GR-ALLOCATION", "GR-RISK", "GR-REALITY", "GR-ATTRIBUTION", "GR-SOURCE", "GR-TEMPORAL", "PR-REALITY-OUTPUT", "DISP-F09-INCLUDED", "RTC-ROOT", "RTC-TIMING")
            case "no_container_coercion":
                assert decision_input.basis_participation_ids == ("PARTICIPATION-SET-CONTAINER",)
            case "ledger_refs_exact":
                assert execution.decision_inputs.root_input.root_timing == execution.mutated_bundle.root_timing
                assert execution.mutated_bundle.root_timing.timing_rewrites_root is True
            case "root_refs_exact":
                assert (execution.decision_inputs.root_input.root_timing.root_state, execution.decision_inputs.root_input.root_timing.root_reason_code) == ("SATISFIED", None)
            case "timing_refs_exact":
                assert (execution.decision_inputs.timing_input.root_timing.timing_state, execution.decision_inputs.timing_input.root_timing.timing_reason_code) == ("SATISFIED", None)
            case "source_decision_exact":
                assert execution.decision_inputs.root_input.root_timing == execution.decision_inputs.timing_input.root_timing == execution.mutated_bundle.root_timing
            case "role_refs_exact":
                assert participation.role_ids == ("ROLE-ALLOCATION", "ROLE-RISK", "ROLE-REALITY", "ROLE-ATTRIBUTION", "ROLE-SOURCE", "ROLE-TEMPORAL")
            case "missing_role_explicit":
                assert participation.role_ids == ("ROLE-ALLOCATION", "ROLE-RISK", "ROLE-REALITY", "ROLE-ATTRIBUTION", "ROLE-TEMPORAL")
            case "shared_frozen_ref":
                assert (participation.scenario_id, participation.reality_record_id, participation.state_support_aligned) == ("ASK", "PR-REALITY-ASK", True)
            case "records_attempt_ledger_complete":
                assert artifact.write_called is True
                assert artifact.fail_after == "STATEMENT_RECORDS"
            case "index_attempt_ledger_complete":
                assert artifact.write_called is True
                assert artifact.fail_after == "STATEMENT_INDEX"
            case "revisions_exact":
                assert artifact.inspection_input is not None
                assert execution.mutated_bundle.artifacts.index_revision == "STMT-REV-1"
            case "expected_observed_separate":
                assert (execution.mutated_bundle.artifacts.expected_digest, execution.mutated_bundle.artifacts.observed_digest) == ("DG-ARTIFACT-V2", "DG-ARTIFACT-CONFLICT")
            case "same_canonical_key":
                assert artifact.key is not None
                assert execution.mutated_bundle.artifacts.retry_key_digest == "IDEM-KEY-A"
                assert execution.mutated_bundle.artifacts.retry_records_payload == b"DG-ARTIFACT-V2"
            case "retry_digest_separate":
                assert execution.mutated_bundle.artifacts.retry_records_payload == b"DG-PAYLOAD-CONFLICT"
                assert execution.mutated_bundle.artifacts.observed_digest == "DG-ARTIFACT-V2"
            case "observed_digest_separate":
                assert execution.mutated_bundle.artifacts.retry_records_payload == b"DG-ARTIFACT-V2"
                assert execution.mutated_bundle.artifacts.observed_digest == "DG-ARTIFACT-MISMATCH"
            case "exact_eight_value_enum":
                assert execution.mutated_bundle.artifacts.item_states == ("NOT_ATTEMPTED", "WRITING", "WRITTEN_UNVERIFIED", "VERIFIED", "FAILED", "STALE", "MISMATCH", "SUPERSEDED")
            case "not_started_not_coerced":
                assert execution.mutated_bundle.artifacts.item_states == ("NOT_STARTED",)
                assert artifact.errors != ()
            case "written_not_coerced":
                assert execution.mutated_bundle.artifacts.item_states == ("WRITTEN",)
                assert artifact.errors != ()
            case "item_set_states_separate":
                assert (execution.mutated_bundle.artifacts.item_states, execution.mutated_bundle.artifacts.statement_revision) == (("STALE",), "STMT-REV-1")
            case "old_identity_retained":
                assert (execution.mutated_bundle.artifacts.statement_revision, execution.mutated_bundle.artifacts.supersedes_revision) == ("STMT-REV-2", "STMT-REV-1")
            case "seven_dimensions_explicit":
                assert execution.mutated_bundle.feedback.seven_matches == ("MISMATCH",) * 7
            case "revision_mismatch":
                assert execution.mutated_bundle.feedback.target_revision == "STMT-REV-1"
            case "track_mismatch":
                assert (execution.mutated_bundle.feedback.source_track, execution.mutated_bundle.feedback.target_track) == (RunTrack.V5_V6_PREPROD, RunTrack.STAGED_L6)
            case "snapshot_parser_span_targets_integrity_exact":
                assert execution.mutated_bundle.feedback.item_ids == ("FBI-1", "FBI-2")
                assert execution.mutated_bundle.feedback.submission_complete is True
            case "seven_dimensions_exact":
                assert execution.mutated_bundle.feedback.seven_matches == ("MATCH", "MATCH", "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "MATCH")
            case "feedback_binding_id_exact":
                assert execution.mutated_bundle.feedback.policy_version == "policy-v1"
                assert execution.mutated_bundle.feedback.eligibility_complete is True
            case "revision_in_identity":
                assert execution.mutated_bundle.feedback.target_revision == "STMT-REV-3"
            case "policy_in_identity":
                assert execution.mutated_bundle.feedback.prior_policy_version == "policy-v2"
                assert execution.mutated_bundle.feedback.policy_version == "policy-v1"
            case "item_ids_canonicalized":
                assert execution.mutated_bundle.feedback.item_ids == ("FBI-1", "FBI-2")
            case "digest_in_identity":
                assert execution.mutated_bundle.feedback.source_digest == "DG-FEEDBACK-B"
            case "reference_only_literal":
                assert execution.mutated_bundle.trace.card_runtime_status == "IMPLEMENTED"
                assert decision_input.f08_runtime_objects == ()
            case "shared_whole_ref":
                assert gate.gate_definition_ref == "REF-GATE-F09-V1"
                assert gate.record_gate_definition_refs == ("REF-GATE-F09-V1",) * 6
            case "bijection_fails":
                assert gate.member_ids == ("ALLOCATION", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "SOURCE")
                assert gate.declared_member_ids == ("ALLOCATION", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "TEMPORAL")
            case "declaration_mismatch":
                assert gate.member_ids == ("ALLOCATION", "RISK", "REALITY", "ATTRIBUTION", "SOURCE", "UNKNOWN_MEMBER")
            case "whole_ref_equal":
                assert gate.gate_definition_ref == "REF-GATE-F09-V1"
                assert len(gate.record_gate_definition_refs) == 6
                assert gate.record_gate_definition_refs[-1] == "REF-GATE-F09-V1/SOURCE"
            case "version_digest_boundary":
                assert len(gate.declared_member_ids) == 6
                assert gate.declared_member_ids[0] == "ALLOCATION@V2:DG-DRIFT"
            case "both_digests_checked":
                assert len(gate.evaluation_binding_digests) == 6
                assert (gate.allocation_state, gate.evaluation_binding_digests[0]) == ("CONFLICT", "DG-ALLOC")
            case "identity_content_bound":
                assert gate.member_ids[:2] == ("RISK", "ALLOCATION")
                assert gate.evaluation_binding_digests[:2] == ("DG-ALLOC", "DG-RISK")
            case "bindings_unchanged":
                assert gate.member_ids == ("TEMPORAL", "SOURCE", "ATTRIBUTION", "REALITY", "RISK", "ALLOCATION")
                assert gate.evaluation_binding_digests == ("DG-TEMP", "DG-SOURCE", "DG-ATTR", "DG-REAL", "DG-RISK", "DG-ALLOC")
            case "risk_unknown_member_bindings_exact":
                assert (gate.allocation_state, gate.risk_state, gate.evaluation_binding_digests) == ("SATISFIED", "UNKNOWN", execution.baseline_bundle.gate.evaluation_binding_digests)
            case "allocation_unknown_member_bindings_exact":
                assert (gate.allocation_state, gate.risk_state, gate.evaluation_binding_digests) == ("UNKNOWN", "SATISFIED", execution.baseline_bundle.gate.evaluation_binding_digests)
            case "bindings_exact":
                assert gate.evaluation_binding_digests == ("DG-ALLOC", "DG-RISK", "DG-REAL", "DG-ATTR", "DG-SOURCE", "DG-TEMP")
            case "broken_ref_identified":
                assert gate.path_complete is False
                assert len(gate.record_gate_definition_refs) == 6
                assert gate.record_gate_definition_refs[0] == "REF-BROKEN"
            case "registry_code_exact":
                assert (gate.risk_reason_codes, gate.allocation_reason_codes) == (("ISSUE-RISK-UNKNOWN",), ("UNREGISTERED-UNKNOWN-REASON",))
            case "locator_gate_bindings_checked":
                assert len(gate.member_ids) == 6
                assert len(gate.evaluation_binding_digests) == 6
                assert gate.member_ids[-1] == "UNKNOWN_MEMBER"
                assert gate.evaluation_binding_digests[-1] == "DG-FORGED"
                assert source.payload_digest == "DG-PAYLOAD-FORGED"
            case _:
                raise AssertionError("unknown binding_assertion token: " + token)


def assert_side_effect_boundary(execution: ScenarioExecution, expected_assertion: str) -> None:
    run = execution.run_result
    artifact = execution.artifact_phase
    feedback = execution.feedback_phase
    called_ports = tuple(call.port for call in execution.boundary_calls)
    called_tracks = tuple(call.track for call in execution.boundary_calls if call.track is not None)
    assert run.request.mode in ("STAGED_AUDIT", "PREPROD_SHADOW")
    assert run.request.enable_f09 is True
    match expected_assertion:
        case "staged_writes_only":
            assert artifact.write_called is True
            assert run.manifest is not None
            assert run.manifest.key.track is RunTrack.STAGED_L6
        case "staged_only":
            assert artifact.write_called is True
            assert run.manifest is not None
            assert run.manifest.key.track is RunTrack.STAGED_L6
        case "no_production_or_learning":
            assert all(call.track is not RunTrack.PRODUCTION_DEFAULT for call in execution.boundary_calls if call.track is not None)
            assert all(record.status != "ELIGIBLE" for record in feedback.eligibility_records)
        case "no_conclusion_write":
            assert artifact.write_called is False
            assert run.statement_set is None
        case "no_formal_outcome":
            assert artifact.write_called is False
            assert run.statement_set is None
        case "no_auto_learning":
            assert all(record.status != "ELIGIBLE" for record in feedback.eligibility_records)
        case "no_inferred_precision":
            declarations = execution.mutated_bundle.declarations
            assert (declarations.precision_presence, declarations.precision_value) == ("RESOLVED", None)
        case "no_precision_fallback":
            assert execution.mutated_bundle.declarations.precision_unresolved is True
            assert execution.mutated_bundle.declarations.precision_value is None
        case "no_output_disposition_fallback":
            assert execution.mutated_bundle.decision.selected_action == "OUTPUT"
            assert execution.mutated_bundle.decision.dispositions == ("DISP-F09-INCLUDED",)
        case "no_conditional_disposition_fallback":
            assert execution.mutated_bundle.decision.selected_action == "CONDITIONAL"
            assert execution.mutated_bundle.decision.dispositions == ("DISP-F09-CONDITIONAL",)
        case "frozen_source_unchanged":
            assert execution.decision_inputs.gate_inputs[0].source == execution.mutated_bundle.source
        case "unknown_not_action":
            assert execution.mutated_bundle.gate.risk_state == "UNKNOWN"
            assert execution.overall_status == "INVALID"
        case "no_artifacts":
            assert run.manifest is None
            assert artifact.write_called is False
        case "no_statement":
            assert run.statement_set is None
            assert artifact.write_called is False
        case "no_promotion":
            assert run.statement_set is None
        case "no_second_card":
            assert execution.mutated_bundle.decision.f08_runtime_objects == ()
            assert execution.mutated_bundle.decision.candidate_ids == ("CAND-F09",)
        case "no_backfill":
            assert execution.mutated_bundle.decision.consequence_only is True
            assert execution.mutated_bundle.gate.allocation_state == "MISSING"
        case "no_decision_write":
            assert artifact.write_called is False
            assert execution.overall_status == "INVALID"
        case "no_guessing":
            assert execution.overall_status == "INVALID"
        case "no_publish":
            assert run.statement_set is None
        case "no_learning_ready":
            assert all(record.status != "ELIGIBLE" for record in feedback.eligibility_records)
        case "no_feedback_readiness":
            assert feedback.status != "VALID"
        case "no_rollback_overwrite":
            assert artifact.write_manifest is not None
            assert artifact.fail_after == "STATEMENT_INDEX"
            assert artifact.retry_manifest is None
        case "no_overwrite":
            assert artifact.inspected_manifest is not None
            assert artifact.inspected_manifest.state is ArtifactSetState.DIGEST_MISMATCH
            assert artifact.retry_manifest is None
        case "learning_calls_zero":
            assert all(record.status != "ELIGIBLE" for record in feedback.eligibility_records)
        case "no_fuzzy_match":
            assert len(feedback.bindings) == 1
            assert feedback.bindings[0].status == "INVALID"
        case "no_artifact_duplicate":
            assert artifact.retry_called is True
            assert artifact.write_manifest is not None
            assert artifact.retry_manifest is not None
            assert artifact.write_manifest.digest == artifact.retry_manifest.digest
        case "no_feedback_duplicate":
            assert feedback.submission is not None
            assert len(feedback.submission.feedback_items) == 2
            assert tuple(item.feedback_item_id for item in feedback.submission.feedback_items) == ("FBI-1", "FBI-2")
            assert len(feedback.bindings) == 2
            assert tuple(binding.feedback_item_ref.object_id for binding in feedback.bindings) == ("FBI-1", "FBI-2")
        case "no_overwrite_or_learning":
            assert artifact.retry_called is True
            assert artifact.retry_manifest is None
            assert artifact.errors != ()
            assert all(record.status != "ELIGIBLE" for record in feedback.eligibility_records)
        case "no_production_learning":
            assert all(call.track is not RunTrack.PRODUCTION_DEFAULT for call in execution.boundary_calls if call.track is not None)
            assert all(record.status != "ELIGIBLE" for record in feedback.eligibility_records)
        case "no_f08_execution":
            assert execution.mutated_bundle.decision.f08_runtime_objects == ()
            assert execution.mutated_bundle.decision.candidate_ids == ("CAND-F09",)
        case "no_silent_deletion":
            assert execution.mutated_bundle.decision.f08_runtime_objects == ("CAND-F08", "ACTION-F08", "STMT-F08")
            assert execution.overall_status == "INVALID"
        case "no_f08_repair":
            assert execution.mutated_bundle.decision.require_two_candidates is True
            assert execution.overall_status == "INVALID"
        case "no_identity_inference":
            assert execution.mutated_bundle.declarations.identity_complete is True
            assert execution.mutated_bundle.declarations.validation_digest == "DG-VALIDATION-V1"
        case "no_outcome_field_inference":
            assert execution.mutated_bundle.source.outcome_fields == ("axis", "action", "object")
            assert execution.trace_phase.status == "INVALID"
        case "no_precision_expansion":
            assert execution.mutated_bundle.declarations.precision_value is None
            assert execution.mutated_bundle.declarations.precision_unresolved is True
        case "no_output":
            assert artifact.write_called is False
            assert run.statement_set is None
        case "no_hidden_resolution":
            assert execution.mutated_bundle.decision.payload_issue_ids == ("ISSUE-RISK-UNKNOWN",)
        case "no_outcome":
            assert execution.mutated_bundle.decision.question_paths == ("/gate/ATTRIBUTION",)
            assert artifact.write_called is False
        case "no_output_payload":
            assert execution.mutated_bundle.decision.payload_type == "AbstainPayload"
            assert artifact.write_called is False
        case "no_priority":
            assert execution.mutated_bundle.decision.payload_type == "HumanReviewPayload"
        case "no_write":
            assert artifact.write_called is False
            assert artifact.write_manifest is None
        case "ready_not_satisfied":
            assert execution.mutated_bundle.participation.role_ids == ("ROLE-ALLOCATION", "ROLE-RISK", "ROLE-REALITY", "ROLE-ATTRIBUTION", "ROLE-SOURCE", "ROLE-TEMPORAL")
        case "no_repair":
            assert execution.overall_status == "INVALID"
        case "no_decision":
            assert artifact.write_called is False
            assert execution.overall_status == "INVALID"
        case "timing_cannot_mutate":
            assert execution.decision_inputs.root_input.root_timing == execution.decision_inputs.timing_input.root_timing
            assert execution.mutated_bundle.root_timing.timing_rewrites_root is False
        case "root_unchanged":
            assert execution.mutated_bundle.root_timing.root_state == execution.baseline_bundle.root_timing.root_state
        case "no_rewrite":
            assert execution.mutated_bundle.root_timing.timing_rewrites_root is False
        case "no_learning":
            assert all(record.status != "ELIGIBLE" for record in feedback.eligibility_records)
        case "bound_status_exact":
            assert len(feedback.bindings) == 1
            assert feedback.bindings[0].status == "BOUND"
        case "evaluation_only":
            assert "EVALUATE_LEARNING_ELIGIBILITY" in called_ports
            assert len(feedback.eligibility_records) == 1
        case "no_old_key_reuse":
            assert feedback.submission is not None
            assert len(feedback.submission.feedback_items) == 1
            assert feedback.submission.feedback_items[0].target_statement_revision_id == "STMT-REV-3"
            assert all(record.status != "ELIGIBLE" for record in feedback.eligibility_records)
        case "reevaluate_only":
            assert len(feedback.eligibility_records) == 1
            assert feedback.eligibility_records[0].policy_version == "policy-v1"
            assert feedback.operation_result is not None
            assert feedback.operation_result.operation_disposition == "NEW_OPERATION"
        case "no_last_write_wins":
            assert feedback.submission is not None
            baseline_digest = DigestRef(
                "sha256",
                "RFC8785-JCS-UTF8",
                sha256(execution.baseline_bundle.feedback.source_digest.encode("utf-8")).hexdigest(),
            )
            assert feedback.submission.source_snapshot_ref.content_digest != baseline_digest
            assert feedback.submission.content_digest != feedback.submission.source_snapshot_ref.content_digest
            assert all(record.status != "ELIGIBLE" for record in feedback.eligibility_records)
        case "no_cross_result_lookup":
            assert execution.mutated_bundle.decision.disposition_refs == ("DISP-F09-INCLUDED",)
        case "fail_closed":
            assert execution.overall_status == "INVALID"
        case "no_first_wins":
            assert execution.mutated_bundle.decision.dispositions == ("DISP-F09-INCLUDED-A", "DISP-F09-INCLUDED-B")
            assert execution.overall_status == "INVALID"
        case "no_downgrade":
            assert execution.mutated_bundle.decision.dispositions == ("DISP-F09-CONDITIONAL",)
        case "no_readiness_inference":
            assert execution.mutated_bundle.artifacts.item_states == ("NOT_ATTEMPTED", "WRITING", "WRITTEN_UNVERIFIED", "VERIFIED", "FAILED", "STALE", "MISMATCH", "SUPERSEDED")
        case "no_verified_inference":
            assert execution.mutated_bundle.artifacts.item_states == ("WRITTEN",)
            assert artifact.status == "INVALID"
        case "no_feedback":
            assert artifact.inspected_manifest is not None
            assert artifact.inspected_manifest.state != "COMPLETE_VERIFIED"
            assert feedback.bindings == ()
            assert feedback.eligibility_records == ()
        case "not_verified":
            assert artifact.inspection_input is not None
            assert len(artifact.inspection_input.records) == 2
            assert artifact.inspection_input.records[0].state == "SUPERSEDED"
        case "no_outcome_statement":
            assert execution.mutated_bundle.decision.selected_action == "ABSTAIN"
            assert run.statement_set is None
        case "order_independent":
            assert execution.mutated_bundle.gate.member_ids == execution.mutated_bundle.gate.declared_member_ids
        case "no_coercion":
            assert len(execution.mutated_bundle.gate.record_gate_definition_refs) == 6
            assert execution.mutated_bundle.gate.record_gate_definition_refs[-1] == "REF-GATE-F09-V1/SOURCE"
        case "no_stale_reuse":
            assert len(execution.mutated_bundle.gate.declared_member_ids) == 6
            assert execution.mutated_bundle.gate.declared_member_ids[0] == "ALLOCATION@V2:DG-DRIFT"
        case "no_accept":
            assert execution.mutated_bundle.gate.allocation_state == "CONFLICT"
            assert execution.overall_status == "INVALID"
        case "no_positional_repair":
            assert execution.mutated_bundle.gate.member_ids[:2] == ("RISK", "ALLOCATION")
        case "no_semantic_drift":
            assert execution.mutated_bundle.gate.member_ids == ("TEMPORAL", "SOURCE", "ATTRIBUTION", "REALITY", "RISK", "ALLOCATION")
        case "no_risk_strengthening":
            assert (execution.mutated_bundle.gate.risk_state, execution.mutated_bundle.gate.risk_reason_codes) == ("UNKNOWN", ("GATE.STATE_UNKNOWN",))
        case "no_allocation_strengthening":
            assert (execution.mutated_bundle.gate.allocation_state, execution.mutated_bundle.gate.allocation_reason_codes) == ("UNKNOWN", ("GATE.STATE_UNKNOWN",))
        case "no_priority_invented":
            assert (execution.mutated_bundle.gate.allocation_state, execution.mutated_bundle.gate.risk_state) == ("SATISFIED", "SATISFIED")
        case "no_sat_promotion":
            assert execution.mutated_bundle.gate.supporting_evidence_tracks == ("CHART_STRUCTURE", "UNVERIFIED_HYPOTHESIS")
            assert execution.overall_status == "INVALID"
        case "no_cross_scenario_reuse":
            assert execution.mutated_bundle.participation.reality_record_id == "PR-REALITY-ASK"
        case "no_masking":
            assert execution.mutated_bundle.participation.reality_record_id == "PR-REALITY-OUTPUT"
            assert execution.overall_status == "INVALID"
        case "no_yaml_or_prose_substitute":
            assert execution.mutated_bundle.source.source_kind == "IMMUTABLE_JSON_SNAPSHOT"
        case "no_synthesis":
            assert execution.trace_phase.status == "VALID"
            assert execution.mutated_bundle.source.source_kind == "IMMUTABLE_JSON_SNAPSHOT"
        case "no_interchange":
            assert execution.mutated_bundle.source.state_object_id == "SOURCE-EVENT-1"
            assert execution.mutated_bundle.source.event_object_id == "SOURCE-STATE-1"
        case "no_business_synthesis":
            assert execution.mutated_bundle.source.outcome_fields == ("axis", "action", "object", "tense")
        case "no_local_bypass":
            assert execution.trace_phase.status == "INVALID"
            assert execution.mutated_bundle.source.payload_digest == "DG-PAYLOAD-DRIFT"
        case "no_claim":
            assert execution.trace_phase.status == "INVALID"
            assert run.statement_set is None
        case "no_auto_extraction":
            assert execution.mutated_bundle.source.source_kind == "MARKDOWN_FREE_TEXT"
            assert execution.trace_phase.status == "INVALID"
        case "no_dual_write":
            assert execution.mutated_bundle.source.canonical_nested_binding is False
            assert artifact.write_called is False
        case "no_expanded_publish":
            assert run.statement_set is None
        case "unknown_code_fails":
            assert execution.mutated_bundle.gate.allocation_reason_codes == ("UNREGISTERED-UNKNOWN-REASON",)
            assert execution.overall_status == "INVALID"
        case "no_dropped_issue":
            assert execution.mutated_bundle.decision.payload_issue_ids == execution.mutated_bundle.trace.issue_propagation_ids == ("ISSUE-RISK-UNKNOWN",)
        case "no_downgrade_repair":
            assert len(execution.mutated_bundle.gate.member_ids) == 6
            assert execution.mutated_bundle.gate.member_ids[-1] == "UNKNOWN_MEMBER"
            assert execution.overall_status == "INVALID"
        case _:
            raise AssertionError("unknown side_effect_assertion token: " + expected_assertion)
    assert set(called_ports) <= {
        "RUN_F09_SLICE",
        "VALIDATE_STATEMENT_PROJECTION",
        "WRITE_ARTIFACT_SET",
        "INSPECT_ARTIFACT_SET",
        "RETRY_ARTIFACT_SET",
        "VALIDATE_FEEDBACK_BINDING",
        "VALIDATE_FEEDBACK_BINDING_RECORD",
        "EVALUATE_LEARNING_ELIGIBILITY",
        "VALIDATE_LEARNING_ELIGIBILITY",
    }
    assert RunTrack.PRODUCTION_DEFAULT not in called_tracks
    if run.evidence is not None:
        assert run.evidence.track is not RunTrack.PRODUCTION_DEFAULT
    if run.trace is not None:
        assert run.trace.track is not RunTrack.PRODUCTION_DEFAULT
    if run.statement_set is not None:
        assert run.statement_set.track is not RunTrack.PRODUCTION_DEFAULT
    if run.manifest is not None:
        assert run.manifest.key.track is not RunTrack.PRODUCTION_DEFAULT
        assert all(record.track is not RunTrack.PRODUCTION_DEFAULT for record in run.manifest.records)
    if execution.feedback_phase.submission is not None:
        assert execution.feedback_phase.submission.track is not RunTrack.PRODUCTION_DEFAULT


@pytest.mark.parametrize(
    "scenario",
    SCENARIOS,
    ids=[scenario.test_id for scenario in SCENARIOS],
)
def test_f09_vertical_matrix(scenario: VerticalScenario, tmp_path: Path) -> None:
    execution = execute_scenario(scenario, tmp_path)
    assert_action_and_state(execution, scenario.expected_action, scenario.expected_gate_or_state)
    assert_issue(execution, scenario.expected_issue_code, scenario.expected_issue_path)
    assert_basis(execution, scenario.basis_assertions)
    assert_bindings(execution, scenario.binding_assertions)
    assert_side_effect_boundary(execution, scenario.side_effect_assertion)
```

### Thirty-one literal adapter component tests

The following module block is copied to `tests/f09/test_f09_adapter_reachability.py` literally. Copy from the first `from dataclasses import replace` import through the closing return/body assertion of `test_feedback_eligibility_complete_port`, inclusive. The imports are complete scaffolding and explicitly reuse the canonical Task 1 `RunTrack`, canonical Task 6 `DigestPresent`, the named conftest baselines/adapters, and literal scenario `T01`; no hidden helper, competing type, or undeclared dependency is permitted. The imports do not count toward the 31 definitions. The definitions comprise trace=10, artifact=10, feedback=11. There is no parameterization, loop, range, generator, dynamic ID, registry, factory, table parser, shared assertion helper, catch-all, or omitted body. Every definition names its target leaf, performs a literal baseline→mutation replacement, proves all non-target fixture fields equal by replacing only that target back, invokes the named adapter, and asserts the concrete pre-call argument/path or call observation changed. `execute_scenario(T01, tmp_path).run_result` is the already-defined baseline production result; it is not a new helper. Every nullable observation member is guarded by a separate `is not None` assertion, and every tuple index is preceded by a separate cardinality assertion in the same test.

```python
from dataclasses import replace

from engine.f09.contracts import RunTrack
from engine.f09.trace import DigestPresent
from tests.f09.conftest import (
    BASELINE_ARTIFACTS,
    BASELINE_FEEDBACK,
    BASELINE_SOURCE,
    BASELINE_TRACE,
    execute_scenario,
    exercise_artifact_lifecycle_phase,
    exercise_feedback_binding_phase,
    exercise_trace_validation_phase,
)
from tests.f09.data.f09_vertical_scenarios import T01

# trace: 10 literal definitions
def test_trace_statement_set_complete_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_TRACE
    changed = replace(base, statement_set_complete=False)
    assert base.statement_set_complete is True
    assert changed.statement_set_complete is False
    assert replace(changed, statement_set_complete=base.statement_set_complete) == base
    before = exercise_trace_validation_phase(run, base, BASELINE_SOURCE)
    after = exercise_trace_validation_phase(run, changed, BASELINE_SOURCE)
    assert before.input_statement_set is not None
    assert after.input_statement_set is not None
    assert before.input_statement_set.source_package_ref is not None
    assert after.input_statement_set.source_package_ref is None
    short_state = replace(BASELINE_SOURCE, state_fields=("level", "position"))
    short_event = replace(BASELINE_SOURCE, event_fields=("level", "change"))
    assert run.trace is not None
    assert run.statement_set is not None
    empty_nodes_run = replace(run, trace=replace(run.trace, nodes=()))
    empty_statements_run = replace(run, statement_set=replace(run.statement_set, statements=()))
    assert len(run.statement_set.statements) >= 1
    statement = run.statement_set.statements[0]
    empty_card_refs_run = replace(run, statement_set=replace(run.statement_set, statements=(replace(statement, card_identity_refs=()),)))
    empty_evidence_refs_run = replace(run, statement_set=replace(run.statement_set, statements=(replace(statement, evidence_refs=()),)))
    short_state_observation = exercise_trace_validation_phase(run, base, short_state)
    short_event_observation = exercise_trace_validation_phase(run, base, short_event)
    empty_nodes_observation = exercise_trace_validation_phase(empty_nodes_run, base, BASELINE_SOURCE)
    empty_statements_observation = exercise_trace_validation_phase(empty_statements_run, base, BASELINE_SOURCE)
    empty_card_refs_observation = exercise_trace_validation_phase(empty_card_refs_run, base, BASELINE_SOURCE)
    empty_evidence_refs_observation = exercise_trace_validation_phase(empty_evidence_refs_run, base, BASELINE_SOURCE)
    assert short_state_observation.errors == ("SOURCE_STATE_FIELD_SHAPE_INVALID",)
    assert short_event_observation.errors == ("SOURCE_EVENT_FIELD_SHAPE_INVALID",)
    assert empty_nodes_observation.errors == ("TRACE_NODE_SHAPE_INVALID",)
    assert empty_statements_observation.errors == ("STATEMENT_SHAPE_INVALID",)
    assert empty_card_refs_observation.errors == ("CARD_REF_SHAPE_INVALID",)
    assert empty_evidence_refs_observation.errors == ("EVIDENCE_REF_SHAPE_INVALID",)

def test_trace_statement_complete_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_TRACE
    changed = replace(base, statement_complete=False)
    assert base.statement_complete is True
    assert changed.statement_complete is False
    assert replace(changed, statement_complete=base.statement_complete) == base
    before = exercise_trace_validation_phase(run, base, BASELINE_SOURCE)
    after = exercise_trace_validation_phase(run, changed, BASELINE_SOURCE)
    assert before.input_statement_set is not None
    assert after.input_statement_set is not None
    assert len(before.input_statement_set.statements) >= 1
    assert len(after.input_statement_set.statements) >= 1
    assert before.input_statement_set.statements[0].statement_id != ""
    assert after.input_statement_set.statements[0].statement_id == ""

def test_trace_statement_basis_ids_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_TRACE
    changed = replace(base, statement_basis_ids=("GR-RISK",))
    assert base.statement_basis_ids != ("GR-RISK",)
    assert changed.statement_basis_ids == ("GR-RISK",)
    assert replace(changed, statement_basis_ids=base.statement_basis_ids) == base
    before = exercise_trace_validation_phase(run, base, BASELINE_SOURCE)
    after = exercise_trace_validation_phase(run, changed, BASELINE_SOURCE)
    assert before.input_statement_set is not None
    assert after.input_statement_set is not None
    assert len(before.input_statement_set.statements) >= 1
    assert len(after.input_statement_set.statements) >= 1
    assert before.input_statement_set.statements[0].basis_record_ids != after.input_statement_set.statements[0].basis_record_ids
    assert after.input_statement_set.statements[0].basis_record_ids == ("GR-RISK",)

def test_trace_rule_ref_ids_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_TRACE
    changed = replace(base, rule_ref_ids=("RULE-F09-DRIFT",))
    assert base.rule_ref_ids == ("RULE-F09-ANCHOR",)
    assert changed.rule_ref_ids == ("RULE-F09-DRIFT",)
    assert replace(changed, rule_ref_ids=base.rule_ref_ids) == base
    before = exercise_trace_validation_phase(run, base, BASELINE_SOURCE)
    after = exercise_trace_validation_phase(run, changed, BASELINE_SOURCE)
    assert before.input_statement_set is not None
    assert after.input_statement_set is not None
    assert len(before.input_statement_set.statements) >= 1
    assert len(after.input_statement_set.statements) >= 1
    before_statement = before.input_statement_set.statements[0]
    after_statement = after.input_statement_set.statements[0]
    assert len(after_statement.evidence_refs) >= 1
    assert before_statement.evidence_refs != after_statement.evidence_refs
    assert after_statement.evidence_refs[0].object_id == "RULE-F09-DRIFT"

def test_trace_transformation_fidelity_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_TRACE
    changed = replace(base, transformation_fidelity="LOSSY")
    assert base.transformation_fidelity == "LOSSLESS"
    assert changed.transformation_fidelity == "LOSSY"
    assert replace(changed, transformation_fidelity=base.transformation_fidelity) == base
    before = exercise_trace_validation_phase(run, base, BASELINE_SOURCE)
    after = exercise_trace_validation_phase(run, changed, BASELINE_SOURCE)
    assert before.state_transformation is not None
    assert before.event_transformation is not None
    assert after.state_transformation is not None
    assert after.event_transformation is not None
    assert before.state_transformation.fidelity == "LOSSLESS"
    assert before.event_transformation.fidelity == "LOSSLESS"
    assert after.state_transformation.fidelity == "LOSSY"
    assert after.event_transformation.fidelity == "LOSSY"

def test_trace_field_mapping_count_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_TRACE
    changed = replace(base, field_mapping_count=0)
    assert base.field_mapping_count == 6
    assert changed.field_mapping_count == 0
    assert replace(changed, field_mapping_count=base.field_mapping_count) == base
    before = exercise_trace_validation_phase(run, base, BASELINE_SOURCE)
    after = exercise_trace_validation_phase(run, changed, BASELINE_SOURCE)
    assert after.state_transformation is not None
    assert after.event_transformation is not None
    assert len(before.mapping_source_paths) == 9
    assert after.mapping_source_paths == ()
    assert after.state_transformation.field_mappings == ()
    assert after.event_transformation.field_mappings == ()

def test_trace_external_source_terminated_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_TRACE
    changed = replace(base, external_source_terminated=False)
    assert base.external_source_terminated is True
    assert changed.external_source_terminated is False
    assert replace(changed, external_source_terminated=base.external_source_terminated) == base
    before = exercise_trace_validation_phase(run, base, BASELINE_SOURCE)
    after = exercise_trace_validation_phase(run, changed, BASELINE_SOURCE)
    assert before.terminal_edge_count > 0
    assert after.terminal_edge_count == 0

def test_trace_card_runtime_status_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_TRACE
    changed = replace(base, card_runtime_status="IMPLEMENTED")
    assert base.card_runtime_status == "REFERENCE_ONLY_NOT_IMPLEMENTATION_PROOF"
    assert changed.card_runtime_status == "IMPLEMENTED"
    assert replace(changed, card_runtime_status=base.card_runtime_status) == base
    before = exercise_trace_validation_phase(run, base, BASELINE_SOURCE)
    after = exercise_trace_validation_phase(run, changed, BASELINE_SOURCE)
    assert before.input_statement_set is not None
    assert after.input_statement_set is not None
    assert len(before.input_statement_set.statements) >= 1
    assert len(after.input_statement_set.statements) >= 1
    before_statement = before.input_statement_set.statements[0]
    after_statement = after.input_statement_set.statements[0]
    assert len(before_statement.card_identity_refs) >= 1
    assert len(after_statement.card_identity_refs) >= 1
    assert before_statement.card_identity_refs[0].runtime_capability_status != after_statement.card_identity_refs[0].runtime_capability_status

def test_trace_statement_text_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_TRACE
    changed = replace(base, statement_text="drifted statement")
    assert base.statement_text != "drifted statement"
    assert changed.statement_text == "drifted statement"
    assert replace(changed, statement_text=base.statement_text) == base
    before = exercise_trace_validation_phase(run, base, BASELINE_SOURCE)
    after = exercise_trace_validation_phase(run, changed, BASELINE_SOURCE)
    assert before.input_statement_set is not None
    assert after.input_statement_set is not None
    assert len(before.input_statement_set.statements) >= 1
    assert len(after.input_statement_set.statements) >= 1
    assert before.input_statement_set.statements[0].statement_text != after.input_statement_set.statements[0].statement_text
    assert after.input_statement_set.statements[0].statement_text == "drifted statement"

def test_trace_issue_propagation_ids_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_TRACE
    changed = replace(base, issue_propagation_ids=("ISSUE-F09-DRIFT",))
    assert base.issue_propagation_ids == ()
    assert changed.issue_propagation_ids == ("ISSUE-F09-DRIFT",)
    assert replace(changed, issue_propagation_ids=base.issue_propagation_ids) == base
    before = exercise_trace_validation_phase(run, base, BASELINE_SOURCE)
    after = exercise_trace_validation_phase(run, changed, BASELINE_SOURCE)
    assert before.input_trace is not None
    assert after.input_trace is not None
    assert before.input_statement_set is not None
    assert after.input_statement_set is not None
    assert before.input_trace.blocking_issue_ids == ()
    assert after.input_trace.blocking_issue_ids == ("ISSUE-F09-DRIFT",)
    assert after.input_statement_set.issue_ids == ("ISSUE-F09-DRIFT",)

# artifact: 10 literal definitions
def test_artifact_records_write_outcome_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_ARTIFACTS
    changed = replace(base, records_write_outcome="FAILED")
    assert base.records_write_outcome == "SUCCEEDED"
    assert changed.records_write_outcome == "FAILED"
    assert replace(changed, records_write_outcome=base.records_write_outcome) == base
    before = exercise_artifact_lifecycle_phase(run, base, tmp_path / "before")
    after = exercise_artifact_lifecycle_phase(run, changed, tmp_path / "after")
    assert before.fail_after is None
    assert after.fail_after == "STATEMENT_RECORDS"

def test_artifact_index_write_outcome_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_ARTIFACTS
    changed = replace(base, index_write_outcome="FAILED")
    assert base.index_write_outcome == "SUCCEEDED"
    assert changed.index_write_outcome == "FAILED"
    assert replace(changed, index_write_outcome=base.index_write_outcome) == base
    before = exercise_artifact_lifecycle_phase(run, base, tmp_path / "before")
    after = exercise_artifact_lifecycle_phase(run, changed, tmp_path / "after")
    assert before.fail_after is None
    assert after.fail_after == "STATEMENT_INDEX"

def test_artifact_index_revision_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_ARTIFACTS
    changed = replace(base, index_revision="STMT-REV-1")
    assert base.index_revision == "STMT-REV-2"
    assert changed.index_revision == "STMT-REV-1"
    assert replace(changed, index_revision=base.index_revision) == base
    before = exercise_artifact_lifecycle_phase(run, base, tmp_path / "before")
    after = exercise_artifact_lifecycle_phase(run, changed, tmp_path / "after")
    assert before.inspection_input is not None
    assert after.inspection_input is not None
    assert len(before.inspection_input.records) >= 2
    assert len(after.inspection_input.records) >= 2
    assert before.inspection_input.records[1].schema_version != after.inspection_input.records[1].schema_version
    assert after.inspection_input.records[1].schema_version == "STMT-REV-1"

def test_artifact_expected_digest_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_ARTIFACTS
    changed = replace(base, expected_digest="DG-EXPECTED-DRIFT")
    assert base.expected_digest == "DG-ARTIFACT-V2"
    assert changed.expected_digest == "DG-EXPECTED-DRIFT"
    assert replace(changed, expected_digest=base.expected_digest) == base
    before = exercise_artifact_lifecycle_phase(run, base, tmp_path / "before")
    after = exercise_artifact_lifecycle_phase(run, changed, tmp_path / "after")
    assert before.inspection_input is not None
    assert after.inspection_input is not None
    assert len(before.inspection_input.records) >= 1
    assert len(after.inspection_input.records) >= 1
    assert len(after.projection_digests) >= 1
    assert before.inspection_input.records[0].expected_digest != after.inspection_input.records[0].expected_digest
    assert after.projection_digests[0] == "DG-EXPECTED-DRIFT"

def test_artifact_observed_digest_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_ARTIFACTS
    changed = replace(base, observed_digest="DG-OBSERVED-DRIFT")
    assert base.observed_digest == "DG-ARTIFACT-V2"
    assert changed.observed_digest == "DG-OBSERVED-DRIFT"
    assert replace(changed, observed_digest=base.observed_digest) == base
    before = exercise_artifact_lifecycle_phase(run, base, tmp_path / "before")
    after = exercise_artifact_lifecycle_phase(run, changed, tmp_path / "after")
    assert before.inspection_input is not None
    assert after.inspection_input is not None
    assert len(before.inspection_input.records) >= 1
    assert len(after.inspection_input.records) >= 1
    assert before.inspection_input.records[0].observed_digest != after.inspection_input.records[0].observed_digest

def test_artifact_item_states_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_ARTIFACTS
    changed = replace(base, item_states=("MISMATCH",))
    assert base.item_states == ("VERIFIED",)
    assert changed.item_states == ("MISMATCH",)
    assert replace(changed, item_states=base.item_states) == base
    before = exercise_artifact_lifecycle_phase(run, base, tmp_path / "before")
    after = exercise_artifact_lifecycle_phase(run, changed, tmp_path / "after")
    assert before.inspection_input is not None
    assert after.inspection_input is not None
    assert len(before.inspection_input.records) >= 1
    assert len(after.inspection_input.records) >= 1
    assert before.inspection_input.records[0].state == "VERIFIED"
    assert after.inspection_input.records[0].state == "MISMATCH"

def test_artifact_statement_revision_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_ARTIFACTS
    changed = replace(base, statement_revision="STMT-REV-1")
    assert base.statement_revision == "STMT-REV-2"
    assert changed.statement_revision == "STMT-REV-1"
    assert replace(changed, statement_revision=base.statement_revision) == base
    before = exercise_artifact_lifecycle_phase(run, base, tmp_path / "before")
    after = exercise_artifact_lifecycle_phase(run, changed, tmp_path / "after")
    assert before.key is not None
    assert after.key is not None
    assert after.inspection_input is not None
    assert len(after.inspection_input.records) >= 1
    assert before.key.schema_versions_digest != after.key.schema_versions_digest
    assert after.inspection_input.records[0].schema_version == "STMT-REV-1"

def test_artifact_supersedes_revision_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_ARTIFACTS
    changed = replace(base, supersedes_revision="STMT-REV-1")
    assert base.supersedes_revision is None
    assert changed.supersedes_revision == "STMT-REV-1"
    assert replace(changed, supersedes_revision=base.supersedes_revision) == base
    before = exercise_artifact_lifecycle_phase(run, base, tmp_path / "before")
    after = exercise_artifact_lifecycle_phase(run, changed, tmp_path / "after")
    assert before.inspection_input is not None
    assert after.inspection_input is not None
    assert len(before.inspection_input.records) == 2
    assert len(after.inspection_input.records) == 2
    before_record_1 = before.inspection_input.records[0]
    before_record_2 = before.inspection_input.records[1]
    old_record = after.inspection_input.records[0]
    current_record = after.inspection_input.records[1]
    assert before_record_1.state == "VERIFIED"
    assert before_record_2.state == "VERIFIED"
    assert before_record_1.artifact_id not in (old_record.artifact_id, current_record.artifact_id)
    assert before_record_2.artifact_id not in (old_record.artifact_id, current_record.artifact_id)
    assert after.inspection_input.records == (old_record, current_record)
    assert old_record.artifact_id == "ART-F09-OLD-STMT-REV-1"
    assert old_record.state == "SUPERSEDED"
    assert current_record.artifact_id == "ART-F09-CURRENT-STMT-REV-2"
    assert current_record.state == "VERIFIED"
    assert old_record.path_locator != current_record.path_locator
    assert old_record.schema_version != current_record.schema_version
    assert old_record.statement_set_id != current_record.statement_set_id
    assert old_record.state != "VERIFIED"
    assert current_record.state != "SUPERSEDED"
    assert after.inspected_manifest is not None
    assert after.retry_manifest is not None
    assert len(after.inspected_manifest.records) == 2
    assert len(after.retry_manifest.records) == 2
    inspected_old = after.inspected_manifest.records[0]
    inspected_current = after.inspected_manifest.records[1]
    retry_old = after.retry_manifest.records[0]
    retry_current = after.retry_manifest.records[1]
    assert inspected_old.artifact_id == old_record.artifact_id
    assert inspected_old.path_locator == old_record.path_locator
    assert inspected_old.state == "SUPERSEDED"
    assert inspected_current.artifact_id == current_record.artifact_id
    assert inspected_current.path_locator == current_record.path_locator
    assert inspected_current.state == "VERIFIED"
    assert retry_old.artifact_id == old_record.artifact_id
    assert retry_old.path_locator == old_record.path_locator
    assert retry_old.state == "SUPERSEDED"
    assert retry_current.artifact_id == current_record.artifact_id
    assert retry_current.path_locator == current_record.path_locator
    assert retry_current.state == "VERIFIED"

def test_artifact_retry_key_digest_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_ARTIFACTS
    changed = replace(base, retry_key_digest="IDEM-KEY-DRIFT")
    assert base.retry_key_digest == "IDEM-KEY-A"
    assert changed.retry_key_digest == "IDEM-KEY-DRIFT"
    assert replace(changed, retry_key_digest=base.retry_key_digest) == base
    before = exercise_artifact_lifecycle_phase(run, base, tmp_path / "before")
    after = exercise_artifact_lifecycle_phase(run, changed, tmp_path / "after")
    assert before.key is not None
    assert after.key is not None
    assert before.key.canonical_key_digest != after.key.canonical_key_digest
    assert before.retry_manifest is not None
    assert before.retry_manifest.detected_issues == ()
    assert after.retry_manifest is not None
    assert after.retry_manifest.key == after.key
    assert after.retry_manifest.manifest_id == "MANIFEST:" + after.key.canonical_key_digest.value
    assert after.retry_called is False
    assert after.errors == ()
    assert after.issues == ()

def test_artifact_retry_complete_payload_set_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_ARTIFACTS
    changed = replace(base, retry_records_payload=b"DG-PAYLOAD-DRIFT")
    assert (base.retry_report_payload, base.retry_records_payload, base.retry_index_payload) == (b"F09 staged report\n", b"DG-ARTIFACT-V2", b"STMT-REV-2")
    assert changed.retry_records_payload == b"DG-PAYLOAD-DRIFT"
    assert replace(changed, retry_records_payload=base.retry_records_payload) == base
    before = exercise_artifact_lifecycle_phase(run, base, tmp_path / "before")
    after = exercise_artifact_lifecycle_phase(run, changed, tmp_path / "after")
    assert len(before.projection_digests) == 3
    assert len(after.projection_digests) == 3
    assert before.projection_digests[1] != after.projection_digests[1]

# feedback: 11 literal definitions
def test_feedback_target_statement_id_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, target_statement_id="STMT-UNKNOWN")
    assert base.target_statement_id == "STMT-F09-1"
    assert changed.target_statement_id == "STMT-UNKNOWN"
    assert replace(changed, target_statement_id=base.target_statement_id) == base
    before = exercise_feedback_binding_phase(run, base)
    after = exercise_feedback_binding_phase(run, changed)
    assert before.submission is not None
    assert after.submission is not None
    assert len(before.submission.feedback_items) >= 1
    assert len(after.submission.feedback_items) >= 1
    assert before.submission.feedback_items[0].target_statement_id == "STMT-F09-1"
    assert after.submission.feedback_items[0].target_statement_id == "STMT-UNKNOWN"

def test_feedback_target_revision_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, target_revision="STMT-REV-1")
    assert base.target_revision == "STMT-REV-2"
    assert changed.target_revision == "STMT-REV-1"
    assert replace(changed, target_revision=base.target_revision) == base
    after = exercise_feedback_binding_phase(run, changed)
    assert after.submission is not None
    assert len(after.submission.feedback_items) >= 1
    assert after.submission.feedback_items[0].target_statement_revision_id == "STMT-REV-1"
    assert after.operation_result is not None
    assert after.operation_result.prior_key is not None
    assert after.operation_result.current_key is not None
    assert after.operation_result.prior_key.canonical_key_digest != after.operation_result.current_key.canonical_key_digest
    assert after.operation_result.operation_disposition == "NEW_OPERATION"
    assert after.operation_result.overwrite_permitted is False

def test_feedback_anchor_status_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, anchor_status="UNMAPPED")
    assert base.anchor_status == "MAPPED"
    assert changed.anchor_status == "UNMAPPED"
    assert replace(changed, anchor_status=base.anchor_status) == base
    before = exercise_feedback_binding_phase(run, base)
    after = exercise_feedback_binding_phase(run, changed)
    assert before.submission is not None
    assert after.submission is not None
    assert before.input_manifest is not None
    assert after.input_manifest is not None
    assert len(before.input_manifest.records) >= 1
    assert before.input_manifest.records[0].artifact_role == "STATEMENT_RECORDS"
    assert after.input_manifest.records == ()
    assert before.submission.track_source_binding.state == "AVAILABLE_RESOLVED"
    assert after.submission.track_source_binding.state == "AVAILABLE_RESOLVED"

def test_feedback_seven_matches_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    mismatch = ("MISMATCH", "MISMATCH", "MISMATCH", "MISMATCH", "MISMATCH", "MISMATCH", "MISMATCH")
    changed = replace(base, source_track=RunTrack.V5_V6_PREPROD, seven_matches=mismatch)
    production_required_na = replace(base, seven_matches=("MATCH", "MATCH", "NOT_APPLICABLE", "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH"))
    preprod_allowed_na = replace(base, binding_protocol="PREPROD_RUN_TARGET", target_statement_id=None, target_revision=None, seven_matches=("MATCH", "MATCH", "MATCH", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "MATCH"))
    preprod_required_na = replace(preprod_allowed_na, seven_matches=("MATCH", "MATCH", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "MATCH"))
    assert base.binding_protocol == "PRODUCTION_STATEMENT"
    assert base.seven_matches == ("MATCH", "MATCH", "NOT_APPLICABLE", "MATCH", "MATCH", "MATCH", "MATCH")
    assert changed.seven_matches == mismatch
    assert len(production_required_na.seven_matches) >= 4
    assert production_required_na.seven_matches[3] == "NOT_APPLICABLE"
    assert preprod_allowed_na.seven_matches[2:] == ("MATCH", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "MATCH")
    assert len(preprod_required_na.seven_matches) >= 3
    assert preprod_required_na.seven_matches[2] == "NOT_APPLICABLE"
    assert replace(changed, source_track=base.source_track, seven_matches=base.seven_matches) == base
    before = exercise_feedback_binding_phase(run, base)
    after = exercise_feedback_binding_phase(run, changed)
    production_required_na_observation = exercise_feedback_binding_phase(run, production_required_na)
    preprod_allowed_na_observation = exercise_feedback_binding_phase(run, preprod_allowed_na)
    preprod_required_na_observation = exercise_feedback_binding_phase(run, preprod_required_na)
    assert before.submission is not None
    assert after.submission is not None
    assert before.input_manifest is not None
    assert after.input_manifest is not None
    assert len(before.submission.feedback_items) >= 1
    assert len(after.submission.feedback_items) >= 1
    assert len(before.input_manifest.records) >= 1
    assert len(after.input_manifest.records) >= 1
    assert len(before.bindings) >= 1
    assert len(after.bindings) >= 1
    assert len(production_required_na_observation.bindings) >= 1
    assert len(preprod_allowed_na_observation.bindings) >= 1
    assert len(preprod_required_na_observation.bindings) >= 1
    before_binding = before.bindings[0]
    after_binding = after.bindings[0]
    production_required_na_binding = production_required_na_observation.bindings[0]
    preprod_allowed_na_binding = preprod_allowed_na_observation.bindings[0]
    preprod_required_na_binding = preprod_required_na_observation.bindings[0]
    assert before.submission.case_id != after.submission.case_id
    assert before.submission.track != after.submission.track
    assert before.submission.feedback_items[0].target_run_id != after.submission.feedback_items[0].target_run_id
    assert before.submission.feedback_items[0].target_statement_id != after.submission.feedback_items[0].target_statement_id
    assert before.submission.feedback_items[0].target_statement_revision_id != after.submission.feedback_items[0].target_statement_revision_id
    assert before.input_manifest.records[0].statement_set_id != after.input_manifest.records[0].statement_set_id
    assert before.input_manifest.records[0].observed_digest != after.input_manifest.records[0].observed_digest
    assert before_binding.binding_protocol == "PRODUCTION_STATEMENT"
    assert before_binding.status == "BOUND"
    assert before_binding.run_match == "NOT_APPLICABLE"
    assert before_binding.track_match == "MATCH"
    assert after_binding.status == "UNBOUND"
    assert after_binding.track_match == "MISMATCH"
    assert production_required_na_binding.binding_protocol == "PRODUCTION_STATEMENT"
    assert production_required_na_binding.statement_match == "NOT_APPLICABLE"
    assert production_required_na_binding.status == "UNBOUND"
    assert preprod_allowed_na_binding.binding_protocol == "PREPROD_RUN_TARGET"
    assert preprod_allowed_na_binding.run_match == "MATCH"
    assert preprod_allowed_na_binding.statement_match == "NOT_APPLICABLE"
    assert preprod_allowed_na_binding.revision_match == "NOT_APPLICABLE"
    assert preprod_allowed_na_binding.statement_set_match == "NOT_APPLICABLE"
    assert preprod_allowed_na_binding.status == "BOUND"
    assert preprod_required_na_binding.binding_protocol == "PREPROD_RUN_TARGET"
    assert preprod_required_na_binding.run_match == "NOT_APPLICABLE"
    assert preprod_required_na_binding.status == "UNBOUND"

def test_feedback_source_track_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, source_track=RunTrack.V5_V6_PREPROD)
    malformed_source_binding = replace(base, source_track_state="SOURCE_MISSING", source_track_reason_codes=())
    source_missing = replace(base, source_track_state="SOURCE_MISSING", source_track_reason_codes=("TRACK_SOURCE_MISSING",))
    source_unparsable = replace(base, source_track_state="UNPARSABLE", source_track_reason_codes=("TRACK_SOURCE_UNPARSABLE",))
    source_ambiguous = replace(base, source_track_state="AMBIGUOUS", source_track_reason_codes=("TRACK_SOURCE_AMBIGUOUS",))
    source_integrity_failed = replace(base, source_track_state="INTEGRITY_FAILED", source_track_reason_codes=("TRACK_SOURCE_INTEGRITY_FAILED",))
    target_missing = replace(base, target_track_state="SOURCE_MISSING", target_track_reason_codes=("TRACK_SOURCE_MISSING",))
    target_unparsable = replace(base, target_track_state="UNPARSABLE", target_track_reason_codes=("TRACK_SOURCE_UNPARSABLE",))
    target_ambiguous = replace(base, target_track_state="AMBIGUOUS", target_track_reason_codes=("TRACK_SOURCE_AMBIGUOUS",))
    target_integrity_failed = replace(base, target_track_state="INTEGRITY_FAILED", target_track_reason_codes=("TRACK_SOURCE_INTEGRITY_FAILED",))
    source_missing_unmapped = replace(source_missing, anchor_status="UNMAPPED")
    assert base.source_track == RunTrack.STAGED_L6
    assert changed.source_track == RunTrack.V5_V6_PREPROD
    assert replace(changed, source_track=base.source_track) == base
    before = exercise_feedback_binding_phase(run, base)
    after = exercise_feedback_binding_phase(run, changed)
    malformed_source_observation = exercise_feedback_binding_phase(run, malformed_source_binding)
    source_missing_observation = exercise_feedback_binding_phase(run, source_missing)
    source_unparsable_observation = exercise_feedback_binding_phase(run, source_unparsable)
    source_ambiguous_observation = exercise_feedback_binding_phase(run, source_ambiguous)
    source_integrity_observation = exercise_feedback_binding_phase(run, source_integrity_failed)
    target_missing_observation = exercise_feedback_binding_phase(run, target_missing)
    target_unparsable_observation = exercise_feedback_binding_phase(run, target_unparsable)
    target_ambiguous_observation = exercise_feedback_binding_phase(run, target_ambiguous)
    target_integrity_observation = exercise_feedback_binding_phase(run, target_integrity_failed)
    source_missing_unmapped_observation = exercise_feedback_binding_phase(run, source_missing_unmapped)
    assert before.submission is not None
    assert after.submission is not None
    assert malformed_source_observation.submission is not None
    assert len(before.bindings) >= 1
    assert len(after.bindings) >= 1
    assert len(malformed_source_observation.bindings) >= 1
    before_binding = before.bindings[0]
    after_binding = after.bindings[0]
    malformed_source_result = malformed_source_observation.bindings[0]
    assert before.submission.track == RunTrack.STAGED_L6
    assert after.submission.track == RunTrack.V5_V6_PREPROD
    assert before.submission.track_source_binding.track == RunTrack.STAGED_L6
    assert after.submission.track_source_binding.track == RunTrack.V5_V6_PREPROD
    assert before.submission.track_source_binding.state == "AVAILABLE_RESOLVED"
    assert after.submission.track_source_binding.state == "AVAILABLE_RESOLVED"
    assert before.submission.track_source_binding.state_reason_codes == ()
    assert after.submission.track_source_binding.state_reason_codes == ()
    assert before.submission.track_source_binding.source_evidence_ref.object_id == base.source_track_evidence_id
    assert before.submission.track_source_binding.parser_ref.object_id == base.source_track_parser_id
    assert before.submission.track_source_binding.parser_ref.revision_id == base.source_track_parser_version
    assert before.submission.track_source_binding.schema_version == base.source_track_schema_version
    assert before.submission.track_source_binding.contract_version == base.source_track_contract_version
    assert before.submission.track_source_binding.content_digest.algorithm == "sha256"
    assert before_binding.source_track_binding_ref.object_id == before.submission.track_source_binding.track_source_binding_id
    assert before_binding.source_track_binding_ref.schema_version == before.submission.track_source_binding.schema_version
    assert before_binding.source_track_binding_ref.contract_version == before.submission.track_source_binding.contract_version
    assert before_binding.source_track_binding_ref.digest_binding.status == "PRESENT"
    assert isinstance(before_binding.source_track_binding_ref.digest_binding, DigestPresent)
    assert before_binding.source_track_binding_ref.digest_binding.digest == before.submission.track_source_binding.content_digest
    assert before_binding.target_track_source_binding.track_source_binding_id == "TSB-F09-TARGET-1"
    assert run.statement_set is not None
    assert before_binding.target_track_source_binding.source_evidence_ref.object_id == base.target_track_evidence_id
    assert before_binding.target_track_source_binding.source_evidence_ref.object_id == run.statement_set.statement_set_id
    assert before_binding.target_track_source_binding.parser_ref.object_id == base.target_track_parser_id
    assert before_binding.target_track_source_binding.parser_ref.revision_id == base.target_track_parser_version
    assert before_binding.target_track_source_binding.schema_version == base.target_track_schema_version
    assert before_binding.target_track_source_binding.contract_version == base.target_track_contract_version
    assert before_binding.target_track_source_binding.content_digest.algorithm == "sha256"
    assert isinstance(before_binding.target_track_source_binding.source_evidence_ref.digest_binding, DigestPresent)
    assert before_binding.target_track_source_binding.content_digest == before_binding.target_track_source_binding.source_evidence_ref.digest_binding.digest
    assert malformed_source_result.track_match == "UNKNOWN"
    assert malformed_source_result.status == "INVALID"
    assert source_missing_observation.submission is not None
    assert source_unparsable_observation.submission is not None
    assert source_ambiguous_observation.submission is not None
    assert source_integrity_observation.submission is not None
    assert target_missing_observation.submission is not None
    assert target_unparsable_observation.submission is not None
    assert target_ambiguous_observation.submission is not None
    assert target_integrity_observation.submission is not None
    assert len(source_missing_observation.bindings) >= 1
    assert len(source_unparsable_observation.bindings) >= 1
    assert len(source_ambiguous_observation.bindings) >= 1
    assert len(source_integrity_observation.bindings) >= 1
    assert len(target_missing_observation.bindings) >= 1
    assert len(target_unparsable_observation.bindings) >= 1
    assert len(target_ambiguous_observation.bindings) >= 1
    assert len(target_integrity_observation.bindings) >= 1
    assert source_missing_observation.bindings[0].track_match == "UNKNOWN"
    assert source_unparsable_observation.bindings[0].track_match == "UNKNOWN"
    assert source_ambiguous_observation.bindings[0].track_match == "UNKNOWN"
    assert source_integrity_observation.bindings[0].track_match == "UNKNOWN"
    assert target_missing_observation.bindings[0].track_match == "UNKNOWN"
    assert target_unparsable_observation.bindings[0].track_match == "UNKNOWN"
    assert target_ambiguous_observation.bindings[0].track_match == "UNKNOWN"
    assert target_integrity_observation.bindings[0].track_match == "UNKNOWN"
    assert source_missing_observation.submission.track_source_binding.state_reason_codes == ("TRACK_SOURCE_MISSING",)
    assert source_unparsable_observation.submission.track_source_binding.state_reason_codes == ("TRACK_SOURCE_UNPARSABLE",)
    assert source_ambiguous_observation.submission.track_source_binding.state_reason_codes == ("TRACK_SOURCE_AMBIGUOUS",)
    assert source_integrity_observation.submission.track_source_binding.state_reason_codes == ("TRACK_SOURCE_INTEGRITY_FAILED",)
    assert source_missing_observation.bindings[0].status == "UNBOUND"
    assert source_unparsable_observation.bindings[0].status == "UNBOUND"
    assert source_ambiguous_observation.bindings[0].status == "AMBIGUOUS"
    assert source_integrity_observation.bindings[0].status == "INVALID"
    assert target_missing_observation.bindings[0].target_track_source_binding.state_reason_codes == ("TRACK_SOURCE_MISSING",)
    assert target_unparsable_observation.bindings[0].target_track_source_binding.state_reason_codes == ("TRACK_SOURCE_UNPARSABLE",)
    assert target_ambiguous_observation.bindings[0].target_track_source_binding.state_reason_codes == ("TRACK_SOURCE_AMBIGUOUS",)
    assert target_integrity_observation.bindings[0].target_track_source_binding.state_reason_codes == ("TRACK_SOURCE_INTEGRITY_FAILED",)
    assert target_missing_observation.bindings[0].status == "UNBOUND"
    assert target_unparsable_observation.bindings[0].status == "UNBOUND"
    assert target_ambiguous_observation.bindings[0].status == "AMBIGUOUS"
    assert target_integrity_observation.bindings[0].status == "INVALID"
    assert len(source_missing_unmapped_observation.bindings) >= 1
    assert source_missing_unmapped_observation.bindings[0].track_match == "UNKNOWN"
    assert source_missing_unmapped_observation.bindings[0].status == "UNBOUND"
    assert source_missing_observation.bindings[0].status == source_missing_unmapped_observation.bindings[0].status
    assert source_missing_observation.input_manifest is not None
    assert source_missing_unmapped_observation.input_manifest is not None
    assert len(source_missing_observation.input_manifest.records) >= 1
    assert (
        source_missing_unmapped_observation.input_manifest.records
        == ()
    )

def test_feedback_policy_version_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, prior_policy_version="policy-v2")
    assert base.prior_policy_version == "policy-v1"
    assert changed.prior_policy_version == "policy-v2"
    assert changed.policy_version == "policy-v1"
    assert replace(changed, prior_policy_version=base.prior_policy_version) == base
    after = exercise_feedback_binding_phase(run, changed)
    assert len(after.eligibility_records) >= 1
    assert after.eligibility_records[0].policy_id == "PRODUCTION-STATEMENT-ELIGIBILITY"
    assert after.eligibility_records[0].policy_version == "policy-v1"
    assert after.operation_result is not None
    assert after.operation_result.prior_key is not None
    assert after.operation_result.current_key is not None
    assert after.operation_result.prior_key.canonical_key_digest != after.operation_result.current_key.canonical_key_digest
    assert after.operation_result.operation_disposition == "NEW_OPERATION"
    assert after.operation_result.overwrite_permitted is False

def test_feedback_item_ids_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, item_ids=("FBI-DRIFT",))
    assert base.item_ids == ("FBI-1",)
    assert changed.item_ids == ("FBI-DRIFT",)
    assert replace(changed, item_ids=base.item_ids) == base
    after = exercise_feedback_binding_phase(run, changed)
    assert after.submission is not None
    assert len(after.submission.feedback_items) >= 1
    assert after.submission.feedback_items[0].feedback_item_id == "FBI-DRIFT"
    assert after.operation_result is not None
    assert after.operation_result.prior_key is not None
    assert after.operation_result.current_key is not None
    assert after.operation_result.prior_key.canonical_key_digest != after.operation_result.current_key.canonical_key_digest
    assert after.operation_result.operation_disposition == "NEW_OPERATION"
    assert after.operation_result.overwrite_permitted is False

def test_feedback_target_graph_relation_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, target_graph_relation="CHANGED")
    assert base.target_graph_relation == "SAME"
    assert changed.target_graph_relation == "CHANGED"
    assert replace(changed, target_graph_relation=base.target_graph_relation) == base
    observation = exercise_feedback_binding_phase(run, changed)
    assert observation.bindings == ()
    assert tuple((issue.code, issue.path) for issue in observation.issues) == (
        ("IDEMPOTENCY.DIGEST_MISMATCH", "/feedback/source_snapshot_ref"),
    )


def test_feedback_source_digest_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, source_digest="DG-FEEDBACK-DRIFT")
    assert base.source_digest == "DG-FEEDBACK-A"
    assert changed.source_digest == "DG-FEEDBACK-DRIFT"
    assert replace(changed, source_digest=base.source_digest) == base
    before = exercise_feedback_binding_phase(run, base)
    after = exercise_feedback_binding_phase(run, changed)
    assert before.submission is not None
    assert after.submission is not None
    assert before.submission.content_digest == after.submission.content_digest
    assert before.submission.source_snapshot_ref.content_digest != after.submission.source_snapshot_ref.content_digest
    assert before.submission.track_source_binding.content_digest == after.submission.track_source_binding.content_digest
    assert before.submission.track_source_binding.content_digest.algorithm == "sha256"
    assert after.submission.track_source_binding.content_digest.algorithm == "sha256"

def test_feedback_submission_complete_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, submission_complete=False)
    assert base.submission_complete is True
    assert changed.submission_complete is False
    assert replace(changed, submission_complete=base.submission_complete) == base
    before = exercise_feedback_binding_phase(run, base)
    after = exercise_feedback_binding_phase(run, changed)
    assert before.submission is not None
    assert after.submission is not None
    assert len(after.submission.feedback_items) >= 1
    assert before.submission.feedback_id == "FB-F09-1"
    assert after.submission.feedback_id == ""
    assert after.submission.feedback_items[0].feedback_id == ""
    assert after.status == "INVALID"

def test_feedback_binding_complete_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, binding_complete=False)
    assert base.binding_complete is True
    assert changed.binding_complete is False
    assert replace(changed, binding_complete=base.binding_complete) == base
    before = exercise_feedback_binding_phase(run, base)
    after = exercise_feedback_binding_phase(run, changed)
    assert len(before.bindings) >= 1
    assert before.bindings[0].feedback_binding_id != ""
    assert after.status == "INVALID"
    assert len(after.errors) >= 1
    assert after.submission == before.submission
    assert after.input_statement_set == before.input_statement_set
    assert after.input_manifest == before.input_manifest

def test_feedback_eligibility_complete_port(tmp_path):
    run = execute_scenario(T01, tmp_path).run_result
    base = BASELINE_FEEDBACK
    changed = replace(base, eligibility_complete=False)
    assert base.eligibility_complete is True
    assert changed.eligibility_complete is False
    assert replace(changed, eligibility_complete=base.eligibility_complete) == base
    before = exercise_feedback_binding_phase(run, base)
    after = exercise_feedback_binding_phase(run, changed)
    assert len(before.eligibility_records) >= 1
    assert before.eligibility_records[0].eligibility_id != ""
    assert after.status == "INVALID"
    assert len(after.errors) >= 1
    assert after.submission == before.submission
    assert after.bindings == before.bindings
```

Future independent acceptance must first run a static parser scoped to the two markers and require 104 body rows, each literal ID exactly once and each unique node exactly once. It must separately AST-parse both Python blocks: require 104 actual top-level `FunctionDef` nodes named `mutate_t01` through `mutate_t104`, enforce the body rules stated above, then require 104 literal constructor assignments, 104 distinct mutator references, 104 unique complete `pytest_node` strings, and a literal 104-element `SCENARIOS` tuple. Counting only `mutate=mutate_tNN` references is expressly insufficient. It must additionally AST-parse the component-test block and require exactly 31 literal top-level test definitions with trace=10, artifact=10 and feedback=11, and reject any loop, range, generator, dynamic ID, registry, factory, table parser, shared catch-all, omitted body, or undefined helper. It may then run `python -m pytest --collect-only tests/f09/test_f09_vertical_matrix.py -q` after tests exist. This plan neither executes that command nor claims current collection success.

---

## Rollout Phases, Gates, Observability and Stop Conditions

### Phase R0 — Code present, unreachable by defaults

- Gate: Tasks 1–10 independently accepted; import graph proves no default entrypoint imports `engine.f09`.
- Allowed: direct unit/component calls only.
- Production effect: none.
- Observation: test-only results.
- Stop: any default signature/hash/import drift.
- Rollback: revert F09 commits newest-first; no production data migration.

### Phase R1 — Staged audit opt-in

- Gate: caller passes `enable_f09=True`, `mode="STAGED_AUDIT"`, isolated `artifact_root`; T01–T104 and production isolation pass in an independent instance.
- Allowed: synthetic F09 fixtures only; no case/report/feedback production paths.
- Observation events: `F09_RUN_REQUESTED`, `SOURCE_VERIFIED`, `EVIDENCE_READY`, `DECISION_READY`, `TRACE_READY`, `ARTIFACT_SET_STATE`, `RUN_STOPPED`; fields limited to case/mode/phase/status/issue codes/digests.
- Stop: source digest mismatch, any unknown member/reason, action union invalid, partial artifact, path escape, or production import detected.
- Rollback: disable caller invocation; retain staged audit artifacts, mark superseded if a corrected revision is produced.

### Phase R2 — Preprod shadow opt-in

- Gate: R1 evidence accepted by a fresh reviewer; caller passes `mode="PREPROD_SHADOW"`; artifact root is preprod-only; cross-track links are `AUDIT_ONLY`.
- Allowed: read explicitly supplied preprod inputs and generate isolated F09 artifacts; no legacy report mutation and no learning.
- Observation: counts of action/state/issue code, artifact state, retries and mismatches; never output source prose or internal IDs to public report.
- Stop: any production artifact path, attempt to bind preprod attachment as production statement bridge, learning side effect, or `COMPLETE_VERIFIED` computed across revisions.
- Rollback: stop opt-in caller; keep immutable audit artifacts; new correction uses new revision/key.

### Phase R3 — Production-shadow decision package (future authorization required)

- Not authorized by this plan. Requires a separate explicit user approval, fresh implementation task and fresh independent acceptance.
- Must remain off by default and may not modify `SubmitAnalysisRequest` or pipeline defaults without reopening governance.
- No phase in this plan changes production-default behavior.

### Global falsifier

The slice is falsified and rollout stops if any one of the following occurs: output precision loses `RESOLVED + null + BOTH_NULL_AND_UNRESOLVED`; F08 becomes executable; a six-member identity can be swapped by permutation; payload-only JCS digest differs from the frozen digest; trace/statement basis drifts; a partial/mixed artifact becomes feedback-ready; eligibility calls learning; or normal production execution imports/runs F09.

---

## Final Independent Acceptance Checklist

- [ ] Fresh reviewer reads `README.md`, `AGENTS.md`, `META/project-state.json`, PI-210/220/230, PI-300 design and PI-400-R4 rereview before code review.
- [ ] Confirm only listed `engine/f09/` and `tests/f09/` implementation files changed; no mapping/template/META/case/report/default production file changed.
- [ ] From the repository root in Windows `cmd.exe`, establish the immutable comparison ref with `git merge-base HEAD origin/main > .git\PI500_F09_BASE` and require exit code 0; then run `for /f "usebackq delims=" %B in (".git\PI500_F09_BASE") do @git diff --name-only %B...HEAD` and reject any path outside the planned set. In a `.bat` file use `%%B` instead of `%B`. Do not substitute a mutable branch name directly into the diff command.
- [ ] Before any pytest, AST-parse `tests/f09/conftest.py` and require 104 unique concrete `def mutate_tNN` bodies, missing=0, duplicate=0, T01 identity return, T02–T104 explicit nested `dataclasses.replace` expressions with literal replacements, and prohibited dynamic/placeholder constructs=0; mutator symbol references do not satisfy this gate.
- [ ] Statically verify `ScenarioBundle`/harness compatibility: Task 10 fixture aliases resolve to Task 5 canonical frozen input-state identities; the materializer uses exactly four direct wrapper constructors; no `from_frozen_fixture`, undefined helper, `mutated.decision_inputs`, or `**` expansion exists; exactly four explicit `run_f09_slice` keyword inputs are passed; `execute_scenario()` unconditionally invokes exactly one trace, artifact and feedback post-run consumer; every trace/artifact/feedback leaf appears in its normative concrete Task 6–8 call-input construction; and each adapter has a component test proving target-argument mutation plus non-target equality. Reject competing input declarations, expectation-only comparisons and dead fixture switches.
- [ ] After implementation exists, run `python -m pytest --collect-only tests/f09/test_f09_vertical_matrix.py -q` and require 104 literal matrix nodes plus the continuity test; this plan records no current collection result.
- [ ] After implementation exists, run `python -m pytest tests/f09 -q` and the related repository regressions; require independent evidence rather than plan-author assertions.
- [ ] Parse only the scenario marker region; require 104 body rows, literal IDs T01 through T104 exactly once, unique node suffixes, and all nine columns populated.
- [ ] Verify frozen Markdown CRLF→LF normalization and JSON payload digests exactly match G4 evidence; bare CR and BOM must fail.
- [ ] Verify no flattened source locator/binding/declaration fields, no local gate/field states, and no local feedback/eligibility statuses exist in implementation.
- [ ] Verify `ObjectRef`, `FieldMapping`, `TransformationRecord`, and transport-only `DetectedIssue` are defined exactly once in `engine/f09/contracts.py`; Tasks 6–8 have zero local declarations, import those canonical runtime identities, and `TraceEnvelope.transformations` uses the imported canonical `TransformationRecord` type.
- [ ] Verify every Task 6–8 phase-owned row T19–T26, T28–T30, T37, T44–T45, T58, T68–T71, T89, T93, and T95–T101 reaches its named literal detection predicate and exactly one displayed constructor with the exact leading-slash code/path pair; reject shorthand, path normalization, status/dimension/reason/fixture mapping, or adapter reconstruction.
- [ ] Verify every canonical `ProjectionValidationResult`, `ArtifactSetManifest`, `FeedbackBinding`, and `LearningEligibility` success/no-issue constructor explicitly passes `detected_issues=()`; verify `replace()` resets the tuple across write/inspect/retry/new eligibility phases and preserves it only for the same immutable record; verify T27, T53/T54, T67 and T72 remain issue-free.
- [ ] Verify returned-vs-exception exclusivity: coherent canonical objects return exactly one producer-owned tuple, incoherent objects raise exactly one existing `F09Error` subtype with the same literal pair, and no detection both returns and raises. Verify adapters only project those fields and feedback consistency assertions are not an issue oracle.
- [ ] Verify no `json.dumps(sort_keys=True)` claim or numeric support exists in F09 JCS implementation.
- [ ] Verify no import/call to mapping YAML, legacy learning, default pipeline or production service exists.
- [ ] Verify disabled and production-default F09 requests perform zero writes.
- [ ] Verify all partial/mismatch/stale artifact cases remain not feedback-ready.
- [ ] Verify eligibility evaluation has no filesystem, rules, weights or iteration side effects.
- [ ] Verify Task 10 commit contains only `tests/f09/` paths; any production correction must have its own owning task and review.
- [ ] Search every changed file for unfinished placeholder markers, deferred-implementation prose, cross-task shorthand and vague error-handling instructions; reject the change if any occurrence remains.
- [ ] Record independent acceptance as a separate artifact/commit; implementation author and this remediation author may not self-approve or mark G5 complete.

## PI-570-R1 bounded remediation matrix

| Finding | Exact repaired sections | Bounded remediation result |
|---|---|---|
| PI590-H-01 | Parent governance only; outside this remediation | Closed by parent governance synchronization of G4=`COMPLETED` and G5=`IN_PROGRESS`; no authorization evidence was invented here. |
| PI590-H-02 | Global Constraints; Task 3; Final Independent Acceptance Checklist | LF and CRLF accepted, CRLF normalized to LF before digest/copy, bare CR and BOM rejected, actual CRLF frozen Markdown is positive evidence. |
| PI590-H-03 | Task 1; Task 3; Task 4 | Canonical six-field `SourceLocator`, closed three-branch `SourceBinding`, five-way `FrozenDeclarationBinding`, exact RESOLVED/UNRESOLVABLE shapes, and non-flattened consumers restored. |
| PI590-H-04 | Task 1; Task 5; Task 9 | Gate and field states separated; gate evidence/path accounting, `GateEvaluationBindingRef`, and complete top-level `DecisionEvaluationResult` restored and consumed. |
| PI590-H-05 | Task 6; Task 7; Task 9 | Complete trace graph, statement/set references, artifact roles/tracks/schema/issues, and append-only write-attempt ledger defined. |
| PI590-H-06 | Task 8; Task 6 trace consumer | Canonical four feedback statuses, three eligibility statuses, and all seven match dimensions restored; mismatch/unmapped/mixed revision use dimensions/issues. |
| PI590-H-07 | Task 10; Literal T01–T104 Executable Scenario Definitions; Final Independent Acceptance Checklist | Exactly 104 literal rows define mutation, expected result, issue code/path, basis, bindings, side effects, and unique intended node; no range/generator substitutes or collection claim. |
| PI590-M-08 | Task 10 closed write set, steps, commit/review/rollback | Task 10 is tests/fixtures/scenario-data only; implementation gaps return to an owning task or a separately bounded task. |

### PI-570-R1 static self-review record

- scenario marker body rows: static document search returned the continuous visible T01 through T104 literal definitions; the proposed local Python counting command was not approved and therefore was not executed or reported as evidence;
- prohibited normative local statuses: removed from interface definitions;
- flattened PI-210 compatibility fields: removed from interface definitions and consumers;
- CRLF rejection: removed; bare CR/BOM rejection retained;
- Task 10 production/validator write authority: removed;
- runtime evidence: `tests executed=0`;
- implementation state: `implementation=false`;
- declarative execution: `YAML not executed`;
- default behavior: `production-default unchanged`;
- independent acceptance and G5 completion remain external governance decisions.

## PI-570-R2 remediation matrix

| R2 finding | Exact repaired locations | Static remediation result |
|---|---|---|
| `PI590R2-H-01` | Task 5 `Interfaces` and invariants | Replaced local PI-220 shapes with the canonical contract/version consumption check, declaration/evaluation bijection, independent participation records, competition dimensions/counterevidence/dispositions, separate root/timing ledgers and checks, full field-path issues, top-level result, and one discriminated five-action payload union. No five-nullable-payload competitor remains. |
| `PI590R2-H-02` | Task 6 `Interfaces` and trace invariants | R2 restored the trace graph but its assertion of sole PI-210 reuse was not established: Task 6 still contained three competing local declarations. PI-570-R3 supersedes that inaccurate closure statement by moving the sole definitions to Task 1 and requiring one concrete Task 6 import. |
| `PI590R2-H-03` | Task 8 `Interfaces` | Restored every canonical `FeedbackSubmission` and `FeedbackItem` field, including source snapshot, parser identity, source span, nullable statement/revision/run/prediction targets, annotation, integrity, issues, digest, and capture time; retained canonical four-state binding, seven match dimensions, and three-state eligibility. |
| `PI590R2-H-04` | Task 10 harness; `Literal executable scenario-data module` | R2 supplied 104 constructor references and the tuple, but not the claimed concrete function bodies. PI-570-R3 supersedes that incomplete closure statement with the concrete frozen graph and 104 literal top-level definitions. |
| `PI590R2-M-05` | Task 5 payload signatures; Task 10 Step 7; Final Independent Acceptance Checklist | Inlined all five canonical payload signatures and their consumer mapping, replaced the cross-task regression shorthand with one exact command, and replaced the undefined base placeholder with deterministic Windows `cmd.exe` merge-base capture and diff commands. |

### PI-570-R2 static self-review record

- write scope: only this implementation-plan file was modified;
- canonical type review: Task 5/6/8 signatures were compared statically with the approved PI-210/220/230 plan contracts; no implementation was created;
- executable scenario review: R2 literal assignments visibly covered T01 through T104 and the tuple visibly enumerated T01 through T104, but R2 had zero concrete mutator definitions; no parser, generator, collection, or pytest command was executed;
- placeholder/shorthand review: the undefined diff-base placeholder and Task 10 cross-task command were removed; payload completion is inline;
- runtime evidence: `tests executed=0`;
- implementation state: `implementation=false`;
- declarative execution: `YAML executed=false`; `mapping executed=false`;
- default behavior: `production-default unchanged`;
- scope identity: `F09 only=true`; `F08 identity-only=true`;
- governance: `PI-500=BLOCKED`; `G5=IN_PROGRESS`; independent reacceptance and G5 completion remain external decisions, and this author does not self-accept them.

## PI-570-R3 remediation matrix

| R3 finding | Exact repaired locations | Static remediation result |
|---|---|---|
| `PI590R3-H-01` | Task 1 canonical contracts; Task 6 interfaces, invariants, RED/GREEN steps and review gate; final checklist; corrected R2 record | `ObjectRef`, `FieldMapping`, and `TransformationRecord` now have one planned owner, `engine/f09/contracts.py`. Task 6 local declarations are removed, one copyable import is mandatory, and `TraceEnvelope.transformations` retains the canonical `TransformationRecord` runtime identity. |
| `PI590R3-H-02` | Task 5 canonical frozen evaluator inputs; Task 10 harness and RED/review gate; concrete frozen fixture graph, direct decision-input materializer, three unconditional post-run consumers and normative leaf-to-port table; literal mutator block; AST acceptance; final checklist; corrected R2 record | Concrete immutable shapes and baseline literals are specified, followed by 104 top-level function definitions. T01 returns baseline; T02–T104 use explicit nested frozen replacements with literal values, including fixed compound order for T43/T75/T96/T102/T104. Task 10 aliases Task 5 input-state identities, uses four direct wrapper constructors, explicitly passes the four production inputs, and then consumes every trace/artifact/feedback leaf through concrete Task 6–8 call-input construction rather than expectation switches; constructors, nodes, and tuple remain literal exactly-once artifacts. |

### PI-570-R3 static self-review

- bounded write scope: only `plans/production-implementation-pi-500-r1-f09-implementation-plan.md` modified;
- Task 6 local class declarations: `0` excluding the three canonical Task 1 definitions;
- Task 6 concrete canonical import: `1`;
- concrete `def mutate_tNN` definitions: `104`;
- unique concrete mutator definitions: `104`;
- missing mutator definitions: `0`;
- duplicate mutator definitions: `0`;
- literal T01–T104 constructors: `104`;
- unique complete pytest nodes: `104`;
- literal `SCENARIOS` tuple IDs: `104`;
- mutator-body placeholders or omitted bodies: `0`;
- harness shape mismatch: `mutated.decision_inputs=0`; dynamic keyword expansion=`0`; undefined fixture factories/helpers=`0`; direct canonical wrapper constructors=`4`; explicit production inputs=`4`;
- post-run fixture boundary: unconditional named consumers=`3`; normative trace/artifact/feedback leaf groups=`12`; fixture leaves covered=`31`; expectation-only fixture switches permitted=`0`; each leaf requires concrete Task 6–8 call-input construction and a target-change/non-target-equality component test;
- positive same-value replacement policy: explicit constructor keyword/value assertion plus non-target equality; only T01 may return baseline directly;
- prohibited body mechanisms: `range=0`, `loop=0`, `comprehension=0`, `factory=0`, `registry=0`, `dynamic ID=0`, `getattr=0`, `table parser=0`, `shared catch-all=0`;
- runtime evidence: `tests executed=0`;
- implementation state: `implementation=false`;
- declarative execution: `YAML executed=false`; `mapping executed=false`;
- boundaries: `F09 only=true`; `F08 identity-only=true`; `frozen semantics=true`; `production-default unchanged`;
- governance: `PI-500=BLOCKED`; `G5=IN_PROGRESS`; PI-590-R4 must be performed by a different instance, and this remediation does not claim PASS or G5 completion.

## PI-570-R4 bounded remediation matrix

| R4 finding | Exact repaired locations | Static remediation result |
|---|---|---|
| `PI590R4-H-01` | Task 8 validators; Task 10 concrete adapter constraints, leaf-to-port table, three observation dataclasses, and three literal post-run adapter bodies | Added complete copyable Task 6–8 adapter definitions with canonical input construction, typed `NOT_RUNNABLE` observations, typed error aggregation, immutable Task 7 mapping arguments, explicit one-or-two feedback binding validation, and one eligibility evaluation/validation per returned binding. All 31 trace/artifact/feedback fixture leaves enter the named canonical constructor, validator, lifecycle, or evaluator inputs without reading scenario oracle fields. |
| `PI590R4-H-02` | `BASELINE_SOURCE`; trace adapter mappings; `mutate_t92`; retained `mutate_t93` and `mutate_t97`; T92/T93/T97 descriptions | The event source now uses `SOURCE-EVENT-1`, object-root `/value`, and the frozen six PI-300 event fields. The trace adapter constructs exactly six canonical `LOSSLESS` `FieldMapping` values terminating at immutable source-object paths; T93 remains an actual state/event identity mismatch and T97 remains a zero-mapping/missing-terminal-edge failure. |

### PI-570-R4 static remediation record

- bounded write scope requested: only `plans/production-implementation-pi-500-r1-f09-implementation-plan.md`; repository-wide changed-path confirmation was not available because the requested Git status operation was denied;
- observation dataclasses: `3`; literal post-run adapter bodies: `3`; explicit not-runnable representations: `3`;
- normative post-run fixture leaves: trace=`10`, artifact=`10`, feedback=`11`, total=`31`; each is routed by the displayed bodies to a canonical Task 6–8 constructor, port, validator, or evaluator input;
- event transformation: source object=`SOURCE-EVENT-1`; object-root pointer=`/value`; canonical event fields=`6`; explicit `LOSSLESS` mappings=`6`;
- concrete mutator definitions: `104`, unique=`104`; literal constructors: `104`, unique=`104`; mutator references: `104`, unique=`104`; complete pytest nodes: `104`, unique=`104`; literal `SCENARIOS` entries: `104`, unique=`104`;
- adapter placeholder scan: standalone `pass=0`; `TODO=0`; `NotImplemented=0`; deferred implementation shorthand=`0`;
- runtime evidence: `tests executed=0`; plan Python executed=`false`; YAML executed=`false`; mapping executed=`false`;
- boundaries: `implementation=false`; `F09 only=true`; `F08 identity-only=true`; `production-default unchanged`;
- governance: `PI-500=BLOCKED`; `G5=IN_PROGRESS`; only a fresh separated instance may conduct `PI-590-R5`; this remediation does not self-accept, claim PASS, or mark G5 complete.

## PI-570-R5 bounded remediation matrix

| R5 finding | Exact repaired locations | Static bounded remediation result |
|---|---|---|
| `PI590R5-H-01` | Task 10 normative leaf-to-port table; `FeedbackPhaseObservation`; `exercise_feedback_binding_phase()`; `BASELINE_FEEDBACK`; feedback component definitions | `anchor_status` and all seven desired dimensions now become pre-call submission/item/statement-set/manifest identity, digest, or availability facts. The binder alone computes `FeedbackBinding`; after return only `feedback_binding_id` may be cleared for the record-validator negative case. No seven-dimension or `record_anchor_ref` overwrite remains. Production-statement baseline run match is `NOT_APPLICABLE`. |
| `PI590R5-H-02` | Global digest constraint; every displayed Task 10 `DigestRef` constructor | Every canonical algorithm literal is exact lowercase `sha256`; contradictory uppercase/hyphenated token prose is removed. |
| `PI590R5-H-03` | `TracePhaseObservation`; `exercise_trace_validation_phase()`; T93 reachability; trace component definitions | Added independent state and event source nodes, target nodes, terminal edges and `TransformationRecord`s before `validate_statement_projection()`. State uses three literal state mappings including `as_of`; event retains six interval mappings. T93 swaps source object identities while fixed state/event targets remain independent, so the mismatch exists in the validator input graph rather than an expected label. |
| narrowed `PI590R5-H-04` | Task 10 artifact leaf-to-port table; `ArtifactPhaseObservation`; `exercise_artifact_lifecycle_phase()`; `mutate_t72`; artifact component definitions | Before inspect/retry, the manifest contains independently existing old and current records. The old record uses only PI-230 fields and remains `SUPERSEDED`; the current record has a distinct artifact/path/schema/set identity. `issue_ids` carries no supersession identity, no PI-230 field was invented, and no issue string is parsed. A `SUPERSEDES` trace edge remains optional trace-audit material only. |
| `PI590R5-M-01` | Task 10 “Thirty-one literal adapter component tests” | Added 31 copyable top-level definitions: trace=10, artifact=10, feedback=11. Each names one leaf in its function name, performs a literal baseline→mutation, restores the target to prove non-target equality, calls the adapter, and asserts the concrete pre-call argument/path or observation changed. No parameter loop, range, generator, dynamic ID, registry, factory, table parser, shared catch-all, omitted body, or undefined helper is used. |

### PI-570-R5 static record

- bounded write scope: only `plans/production-implementation-pi-500-r1-f09-implementation-plan.md` was edited; control state, R5 review artifact, handoff, META, production code, test code, YAML, mapping and all other files were not edited;
- static source review only: no Python, pytest, test collection, YAML, mapping, plan code, Git operation, or runtime verification was executed;
- canonical feedback boundary: pre-call canonical input mutations=`7 dimensions + anchor availability`; post-return semantic dimension overwrites=`0`; post-return anchor overwrites=`0`; permitted record-validator negative mutation=`feedback_binding_id only`;
- canonical digest constructors: lowercase `sha256`; uppercase/hyphenated `DigestRef.algorithm` literals=`0`;
- trace comparison graph: state transformations=`1`; state literal mappings=`3`; event transformations=`1`; event literal mappings=`6`; independent source/target node pairs=`2`; T93 stimulus enters the pre-call graph;
- T72 lifecycle identity: independently existing old records=`1`; independently existing current/new records=`1`; old state=`SUPERSEDED`; supersession identity in `issue_ids`=`0`; invented `ArtifactRecord` fields=`0`;
- literal component-test definitions: trace=`10`; artifact=`10`; feedback=`11`; total=`31`; dynamic generation mechanisms=`0`;
- preserved prior accounting: concrete mutator definitions=`104`; literal constructors=`104`; mutator references=`104`; complete pytest nodes=`104`; literal `SCENARIOS` entries=`104`; this is a static preservation statement, not collection or execution evidence;
- implementation/test claims: `implementation=false`; `tests executed=0`; `collection executed=false`; `G5 PASS claimed=false`; `production readiness claimed=false`; `production-default unchanged`;
- governance remains unchanged: `PI-500=BLOCKED`; `G5=IN_PROGRESS`;
- the only next action is independent reacceptance by a fresh separated `PI-590-R6` instance; this remediation does not self-accept or authorize implementation.

## PI-570-R6 remediation record

| R6 finding | Exact repaired locations | Static bounded remediation result |
|---|---|---|
| High — typed track-source UNKNOWN semantics | Task 8 `FeedbackFixture`; `exercise_feedback_binding_phase()`; `BASELINE_FEEDBACK`; `test_feedback_source_track_port()` | Both submission-source and binding-target facts are represented by canonical `TrackSourceBinding` values containing a legal non-empty PI-210 `RunTrack`, `TrackSourceState`, evidence/parser refs and versions, schema/contract versions, lowercase-`sha256` digest, and state-coherent reason codes. Resolved equal tracks produce `MATCH`, resolved unequal tracks produce `MISMATCH`, either failure state produces `UNKNOWN`, and malformed state/reason coherence produces `UNKNOWN + INVALID`. Seven binder dimensions are asserted, status precedence remains `INVALID > AMBIGUOUS > UNBOUND > BOUND`, and mapped/unmapped anchor availability is tested independently from source state. |
| High — T72 duplicate current-like records | `exercise_artifact_lifecycle_phase()`; `test_artifact_supersedes_revision_port()` | T72 selects one literal manifest tuple `(old_record, current_record)` rather than composing lifecycle and selected tuples. The component test proves exact two-record cardinality and tuple identity, one old `SUPERSEDED` record, one current canonical `VERIFIED` record, distinct identity/path/schema/set values, exact inspect/retry preservation, and both baseline non-T72 records isolated from both T72 IDs. |
| Medium — 31 literal component-test bodies | Task 10 “Thirty-one literal adapter component tests” block | The block contains 31 standard multiline top-level definitions (trace=`10`, artifact=`10`, feedback=`11`) with literal bodies. The source-track loop and T72 generators are removed; no component definition uses parameterization, loop, range, generator, dynamic ID, registry, factory, table parser, shared catch-all, or omitted body. |
| Medium — nullable and tuple-index guards | All 31 Task 10 component definitions, especially malformed trace, T72, seven-dimension, and source-track tests | Nullable members have separate `is not None` assertions before member access. Every tuple index has a preceding cardinality assertion in the same test; expanded source/target observations each carry their own submission and binding guards. |
| Medium — trace pre-index malformed handling | `exercise_trace_validation_phase()`; `test_trace_statement_set_complete_port()` | State fields, event fields, trace nodes, statements, card refs, and evidence refs are shape-checked before indexing. Empty/short inputs return typed `TracePhaseObservation` issue tuples rather than reaching an `IndexError`; literal malformed cases assert each issue code. |

### PI-570-R6 static evidence and boundary record

- bounded write scope: only `plans/production-implementation-pi-500-r1-f09-implementation-plan.md` was edited; canonical plans, PI-590 artifacts, control, handoff, META, production code, test code, YAML, mapping, and all other files were not edited;
- static component inventory: trace=`10`, artifact=`10`, feedback=`11`, total=`31`; component loops=`0`; component ranges=`0`; component generators=`0`; component parameterization=`0`; semicolon-compressed component bodies=`0`;
- typed track truth table: resolved equal=`MATCH`; resolved unequal=`MISMATCH`; source-state failure=`UNKNOWN`; target-state failure=`UNKNOWN`; malformed canonical binding=`UNKNOWN + INVALID`; source/target canonical identity, schema, contract, and digest links are asserted;
- T72 static identity: inspection tuple cardinality=`2`; old=`1 SUPERSEDED`; current=`1 VERIFIED`; baseline records checked=`2`; inspect/retry records checked=`2 + 2`; tuple addition/composition=`0`;
- trace malformed boundary: state/event/node/statement/card-ref/evidence-ref pre-index guards=`6`; typed malformed issue observations=`6`; uncaught `IndexError` path claimed=`0`;
- canonical digest constructors remain lowercase `sha256`; non-lowercase `DigestRef.algorithm` constructor literals=`0`;
- preserved static inventory: concrete mutator definitions span literal T01–T104 exactly once; literal constructors span T01–T104 exactly once; each constructor names its corresponding mutator and complete pytest node; `SCENARIOS` lists literal T01–T104 exactly once. Preserved accounting remains `104/104/104/104/104`; this is source-text evidence, not AST, collection, or runtime evidence;
- preserved no-regression boundaries: T92 six event mappings; T93 independent state/event graph; T97 pre-call mapping/termination stimulus; F09 six independent gate dimensions; allocation-only, risk-only, and strong-primary semantics; state/event identity; F08 identity-only; production-default unchanged;
- verification not performed: tests executed=`0`; collection executed=`false`; Python executed=`false`; pytest executed=`false`; plan code executed=`false`; YAML executed=`false`; mapping executed=`false`; Git executed=`false`; no runtime or PASS claim is made;
- residual risk: all evidence is bounded static plan inspection. Copyability, AST counts, collection, runtime behavior, repository-wide changed paths, and implementation conformance remain unverified. A prior remediation attempt used a PowerShell text-edit command; R6 itself used only static read/search/surgical edit operations, plus one non-mutating skill load;
- governance unchanged: `PI-500=BLOCKED`; `G5=IN_PROGRESS`; `G5 PASS claimed=false`; implementation authorization=`false`;
- the only next action is parent-instance static spot-check followed by handoff to a fresh separated `PI-590-R7` instance for independent reverification.

## PI-570-R7 remediation record

| R7 blocker | Canonical fact | Exact repaired locations | Static evidence and retained constraints |
|---|---|---|---|
| A — canonical RunTrack type conflict | PI-210 is the sole `RunTrack` owner; its closed values are exactly `PRODUCTION_DEFAULT | PARALLEL_DOMAIN | STAGED_L6 | V5_V6_PREPROD | MANUAL_IMPORT`. | Global Constraints; Task 1 interface/RED test; Task 6–8 canonical track annotations/imports; Task 9 opt-in RED test and implementation boundary; Task 10 `FeedbackFixture`, adapter, baseline, T25/T29 mutators, and feedback component assertions. | Local three-value `Track` declaration and every canonical use of request-mode tokens were removed. `STAGED_AUDIT` and `PREPROD_SHADOW` remain application request modes only; the unique fail-closed boundary mapping is `STAGED_AUDIT -> STAGED_L6` and `PREPROD_SHADOW -> V5_V6_PREPROD`, while `PRODUCTION_DEFAULT` request remains rejected before mapping/I/O. Typed source/target bindings, baseline, mutators and assertions now use canonical `RunTrack.STAGED_L6` / `RunTrack.V5_V6_PREPROD`. Production-default and F09 opt-in isolation remain unchanged. |
| B — non-exhaustive PI-230 aggregate status | PI-230 requires all seven dimensions to be independently computed and aggregate status to use first match `INVALID > AMBIGUOUS > UNBOUND > BOUND`; only protocol-explicit N/A is non-blocking, while required N/A is `UNBOUND`. | Task 8 protocol prose and RED binding coverage; Task 10 `FeedbackFixture.binding_protocol`; literal `exercise_feedback_binding_phase()` protocol table/oracle; existing `test_feedback_seven_matches_port()` body. | The prior `expected_status = "BOUND"` default was replaced by explicit invalid, ambiguous, unbound, bounded-proof, and non-exhaustive-error branches. The literal protocol table marks `PRODUCTION_STATEMENT` required indices `0,1,3,4,5,6` with only run index `2` allowed N/A, and `PREPROD_RUN_TARGET` required indices `0,1,2,6` with only statement/revision/set indices `3,4,5` allowed N/A. The existing feedback component test now supplies and asserts production allowed-N/A BOUND, production required-N/A UNBOUND, preprod allowed-N/A BOUND, and preprod required-N/A UNBOUND without adding a top-level test. Seven dimensions and four statuses are unchanged. |

### PI-570-R7 static evidence, preservation and boundary record

- bounded write scope: only `plans/production-implementation-pi-500-r1-f09-implementation-plan.md` was edited; PI-210, PI-230, total-control, handoff, code, tests, JSON, YAML, mapping and all other files were not edited;
- static canonical-track search: local `class Track` declarations=`0`; canonical `Track.STAGED_AUDIT` / `Track.PREPROD_SHADOW` uses=`0`; request-mode literals remain only in application request/boundary/rollout prose and request fixtures; canonical baseline/mutator/assertion values are `RunTrack.STAGED_L6` and `RunTrack.V5_V6_PREPROD`;
- static aggregate-oracle search: explicit protocol table=`1`; required-dimension proof=`1`; allowed-N/A proof=`1`; first-match invalid/ambiguous/unbound/bound branches=`4`; default initialization `expected_status = "BOUND"`=`0`; non-exhaustive fail-closed error branch=`1`;
- literal component inventory remains trace=`10`, artifact=`10`, feedback=`11`, total=`31`; required-N/A and allowed-N/A data/assertions were added inside the existing feedback seven-dimension test, so top-level count and `10/10/11` split are unchanged;
- R6 closed surfaces retained statically: T72 manifest input remains exactly `(old_record, current_record)` with old `SUPERSEDED` and current `VERIFIED`, no tuple composition/current-like pollution; trace state/event/node/statement/card/evidence shape guards remain before indexing; nullable/index accesses in the 31 multiline component tests retain local guards; source/target `TrackSourceBinding` identities remain complete; anchor availability remains orthogonal to track uncertainty; all seven dimensions remain independent; T92/T93/T97, five-part 104 inventory, lowercase `sha256`, and F08 identity-only constraints remain present;
- execution explicitly not performed: Python=`false`; pytest=`false`; collection=`false`; plan fragments=`false`; YAML=`false`; mapping=`false`; Git=`false`; CLI/PowerShell=`false`; implementation=`false`; runtime verification=`false`;
- governance unchanged: remediator self-acceptance=`false`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`; G5 completion marked=`false`; implementation authorization=`false`; PI-590-R7 is not started or authorized by this record;
- residual risk: evidence is static and scoped to plan text. Syntax/copyability, AST counts, collection, runtime behavior, repository-wide diff, and implementation conformance remain for a fresh separated reviewer; this record makes no acceptance or runtime claim.

## PI-570-R8 remediation record

- triggering verdict: fresh separated `PI-590-R7=BLOCKED` on one Medium residual defect; no PASS or G5-complete status is inherited or claimed;
- parent-instance verification: the parent instance directly verified that the sole PI-590-R7 Medium finding matches the actual PI-500 text before authorizing this bounded remediation;
- exact repair: inside the existing `test_feedback_seven_matches_port()` definition, a local `len(production_required_na.seven_matches) >= 4` assertion now immediately precedes direct index `[3]`, and a local `len(preprod_required_na.seven_matches) >= 3` assertion now immediately precedes direct index `[2]`;
- same-function static inspection: the remaining direct tuple indexes in this function already have local cardinality guards before access; the `[2:]` expression is a non-throwing slice and requires no direct-index cardinality repair; additional same-class gaps repaired=`0`;
- retained constraints: fixture data, protocol/status logic, assertion semantics, top-level test count, trace/artifact/feedback `10/10/11` split, canonical types, production-default behavior, F08/F09 boundaries, and all other design remain unchanged; unrelated formatting=`0`;
- bounded write scope: only `plans/production-implementation-pi-500-r1-f09-implementation-plan.md` was edited; PI-590-R7, canonical plans, total-control, handoff, code, tests, JSON, YAML, mapping, and all other files were not edited;
- not executed: Python=`false`; pytest=`false`; collection=`false`; plan fragments=`false`; YAML=`false`; mapping=`false`; Git=`false`; CLI/PowerShell=`false`; runtime verification=`false`;
- governance: remediator self-acceptance=`false`; PASS claimed=`false`; G5 completion marked=`false`; implementation authorization=`false`; the only next action is independent review by a fresh separated `PI-590-R8` instance.

## PI-570-R9 remediation record

- triggering verdict: fresh separated `PI-590-R8=BLOCKED` on two High static-plan defects plus copyability/import/scaffolding gaps; no PASS, runtime correctness, or G5-complete status is inherited or claimed;
- exact Enum repair: Task 1 now displays complete `dataclass`/`Enum`/typing imports and seven legal multiline Enum declarations whose members each have explicit same-name string values. `RunTrack` remains exactly `PRODUCTION_DEFAULT | PARALLEL_DOMAIN | STAGED_L6 | V5_V6_PREPROD | MANUAL_IMPORT`; PI-210 remains sole semantic owner, Task 1 remains the sole runtime transcription, and no alias enum or second runtime identity was introduced;
- mechanical syntax repair: a full-plan static decorator/class same-line search identified four physical lines containing six decorated classes; all six decorators now precede their classes on separate physical lines, with fields, annotations, defaults, and semantics unchanged;
- literal-copy closure: Task 1 contracts, `tests/f09/conftest.py`, `tests/f09/data/f09_vertical_scenarios.py`, and `tests/f09/test_f09_adapter_reachability.py` now state target modules, complete displayed imports/scaffolding, canonical import/reuse ownership, and inclusive copy boundaries. The conftest imports now include `TrackSourceState` and `TrackSourceReasonCode`; scenario data explicitly imports `DecisionAction`, `VerticalScenario`, and all 104 mutators; reachability tests explicitly import `replace`, `RunTrack`, `DigestPresent`, all named baselines/adapters, and `T01`. Hidden helpers, competing types, wildcard/dynamic imports, undeclared dependencies, and expanded implementation scope remain prohibited;
- Task 10 authorization repair: `tests/f09/test_f09_adapter_reachability.py` is now in the closed write set and Step 8 commit path list; this is plan authorization only and no test file was created;
- frozen preservation: the 31 top-level multiline component tests and trace/artifact/feedback split `10/10/11` were not edited; T01–T104 body rows, 104 concrete mutators, 104 literal constructors, 104 mutator references, 104 complete pytest nodes, and the 104-element literal `SCENARIOS` tuple were not edited. Nullable/index local guards, T72 old/current identity, T92 six event mappings, T93 state/event identity separation, T97 mapping/external termination, lowercase `sha256`, F09-only/F08-identity-only boundaries, six gate dimensions, allocation-only/risk-only/strong-primary semantics, state/event accounting, and production-default behavior remain textually unchanged;
- bounded write scope: only `plans/production-implementation-pi-500-r1-f09-implementation-plan.md` was edited; PI-590-R8, PI-210/220/230/300, total control, handoff, production code, test code, JSON, YAML, mapping, and all other files were not edited;
- not executed: Python=`false`; pytest=`false`; collection=`false`; fenced plan code=`false`; YAML=`false`; mapping=`false`; Git=`false`; CLI/PowerShell=`false`; runtime verification=`false`; static text remediation is not implementation or runtime evidence;
- residual unknowns: Python parseability of copied modules, AST inventories, test collection, runtime behavior, repository-wide implementation conformance, and changed-path evidence remain unverified by this remediation;
- governance: remediator self-acceptance=`false`; PASS claimed=`false`; G5 completion marked=`false`; implementation authorization=`false`; the only next action is independent reverification by a fresh, independent, separated `PI-590-R9` instance.

## PI-570-R10 remediation record

- triggering finding: fresh separated `PI-590-R9` reported `PI590R9-H-01`; this record addresses only the static copy-boundary and module-ownership defect and does not inherit or claim PASS, runtime correctness, or G5 completion;
- actual static changes: the earlier Task 10 executable interface sketch was replaced by a non-copy ownership index; the later conftest listing is now one continuous fenced module from complete imports through `mutate_t104`; `Callable` and canonical `DecisionAction` are imported; `VerticalScenario`, `ScenarioExecution`, and `execute_scenario` are defined in that sole conftest module before any scenario-data reverse import can occur; conftest does not import scenario-data;
- vertical-matrix copy boundary: one continuous `tests/f09/test_f09_vertical_matrix.py` module block now explicitly imports `Path`, `pytest`, canonical `DecisionAction`/`RunTrack`, conftest-owned types/executor, and scenario-data-owned `SCENARIOS`; it locally defines `assert_action_and_state`, `assert_issue`, `assert_basis`, `assert_bindings`, and `assert_side_effect_boundary` before the parameterized test;
- static inspection performed: ownership, textual import order, named-symbol availability, single-copy-source prose, and absence of wildcard/dynamic imports, registries, factories, table parsers, and undefined assertion-helper calls were inspected in the edited plan text only; `assert_basis` consumes canonical tuple-typed `BasisRecordIds` through tuple non-emptiness and cross-layer tuple equality, with no nonexistent named-field access;
- preserved boundaries: Task 10 remains tests-only with the same four authorized paths; seven Enums and canonical five-value `RunTrack` ownership are unchanged; the 31 component tests and `10/10/11` split, all five 104-item inventories, nullable/index guards, T72/T92/T93/T97, feedback precedence/protocol N/A/provenance, lowercase `sha256`, F09-only/F08 identity-only, six gates, allocation-only/risk-only/dual-axis boundary, state/event accounting, and production-default behavior were not intentionally changed;
- not executed: Python=`false`; pytest=`false`; collection=`false`; fenced snippets=`false`; YAML=`false`; mapping=`false`; Git=`false`; CLI/PowerShell=`false`; implementation or test files created=`false`; runtime verification=`false`;
- remaining unknowns: copied-module parseability, import/collection behavior, AST counts, runtime assertion behavior, repository-wide implementation conformance, changed-path evidence, and semantic correctness remain unverified and are not claimed by this static remediation;
- governance: remediator self-acceptance=`false`; PASS claimed=`false`; G5 completion marked=`false`; implementation authorization=`false`; `PI-500` status is not changed by this record; the sole next receiver is a fresh, independent, separated `PI-590-R10` instance.

## PI-570-R11 remediation record

- triggering finding: the parent instance rejected R10 because Task 10's five vertical-matrix helpers did not semantically close the literal expectations: action/state used heterogeneous membership, basis and binding tokens were only checked for non-emptiness before generic assertions, side-effect tokens shared one undifferentiated boundary check, and the explicit no-issue branch returned without proving all issue/error surfaces empty;
- actual bounded static changes: `ScenarioExecution` carries the baseline bundle, mutated bundle, four canonical decision inputs, and three typed phase observations without reading any scenario expectation; the four literal expectation families are consumed by explicit `match` branches against named canonical decision-input, decision, trace, artifact, feedback, baseline/mutated, and track fields; each dispatch has an immediate fail-closed unknown-token branch;
- canonical-field correction in this final R11 pass: artifact-set assertions now import and compare the canonical `ArtifactSetState.STALE_MIXED_REVISION` / `ArtifactSetState.DIGEST_MISMATCH` enum values rather than the item-state literal `MISMATCH`; revision assertions traverse `FeedbackSubmission.feedback_items[*].target_statement_revision_id`; item-set assertions traverse canonical `FeedbackItem.feedback_item_id` and `FeedbackBinding.feedback_item_ref.object_id`. The nonexistent `FeedbackSubmission.target_revision` and `FeedbackBinding.feedback_item_id` accesses are removed from the vertical helper block;
- no-issue closure: the `expected_issue_code is None` branch checks observation issue codes, decision issues, action blocking/nonblocking/reason/validation surfaces, trace blocking issues, statement-set and statement issues, artifact-record issues, feedback-binding issues, eligibility blocking reasons, and trace/artifact/feedback errors, with no early return; positive issue checking requires one same-surface code/path pair from a canonical `DecisionIssue` or the typed test-only phase observation assembled from canonical phase outputs and their exact pre-call canonical inputs;
- static review hardening: Task 10 continuity and independent-review prose requires exact literal-token inventory closure, canonical typed field/value mapping, unknown-token failure, and full no-issue surface exhaustion; non-emptiness-only consumption, heterogeneous membership, dynamic dispatch, registry/factory/table parsing, and shared success defaults are rejected;
- preserved R10 boundaries: the single continuous conftest owner, single continuous vertical-matrix owner, scenario-data ownership/import order, four Task 10 paths, 104 mutators/constructors/references/nodes/tuple entries, 31 adapter tests with `10/10/11` split, seven Enums, F09-only scope, F08 identity-only semantics, and production-default isolation were not intentionally changed;
- not executed: Python=`false`; pytest=`false`; collection=`false`; fenced snippets=`false`; YAML=`false`; mapping=`false`; Git=`false`; CLI/PowerShell=`false`; implementation/test files created=`false`; runtime verification=`false`;
- residual unknowns: copied-module parseability, exact AST inventory, collection, runtime behavior, phase-observation fidelity, repository-wide changed paths, and implementation conformance remain unverified; canonical field names above were checked only against the frozen PI-230 text and this plan's Task 7/8 interfaces; this static remediation does not self-accept or establish runtime correctness;
- governance: status=`READY_FOR_REVIEW`; remediator self-acceptance=`false`; PASS claimed=`false`; G5 completion marked=`false`; implementation authorization=`false`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`; the only next action is parent-instance verification of R11 and, if accepted, independent reverification by a fresh separated `PI-590-R11` instance.

## PI-570-R12 remediation record

- triggering finding: the parent instance rejected R11 with one High blocker because matrix-side `observe_phase_issues(execution)` reconstructed issue code/path pairs from scenario mutations, fixture patterns, baseline values, and baseline-to-mutated differences, making the positive phase oracle circular rather than evidence of validator/coordinator output;
- actual bounded static repair: `PhaseIssueObservation` is owned by the sole continuous Task 10 conftest block; `TracePhaseObservation`, `ArtifactPhaseObservation`, and `FeedbackPhaseObservation` each carry an immutable `issues` tuple; their adapters populate a pair only from a typed `F09Error` raised by the invoked Task 6–8 validator/coordinator detection branch. `ScenarioExecution` carries those observations unchanged. The matrix-side scanner and all mutation/baseline issue reconstruction branches are deleted;
- typed transport boundary: frozen semantic rejections use immutable nonempty `F09Error.issue_code` and canonical `F09Error.field_path`, while exception text remains diagnostic-only and is never parsed. Adapter-owned cardinality, shape, protocol, and oracle consistency defects now raise `AssertionError`, so harness diagnostics cannot masquerade as frozen semantic issues or enter the phase issue tuple;
- same-surface oracle closure: `assert_issue()` aggregates only canonical run/decision typed issues and the three adapter-owned actual phase issue tuples. A positive assertion requires the complete expected `(code, path)` pair on one typed surface; code-only surfaces, scenario expectations, test IDs, mutation tokens, fixture values, baseline diffs, and exception strings cannot supply or cross-join a pair. T102 first satisfies that same pair assertion; its gate-fixture checks remain stimulus-only additions;
- no-issue and dispatch preservation: the no-issue branch still proves canonical observation, decision/action, trace, statement, artifact, feedback, eligibility, all three phase issue tuples, and all three phase error tuples empty. The five expectation helpers retain literal `match` dispatch and immediate unknown-token fail-closed behavior;
- frozen semantic and inventory preservation: T53/T54 retain PI-300 conditional authority; T01–T104 and all five 104-item inventories, 31 literal component tests with `10/10/11` split, four Task 10 paths, one conftest block, one matrix block, seven Enums, lowercase `sha256`, F09-only scope, F08 identity-only behavior, and production-default isolation were not intentionally changed;
- bounded scope and non-execution: only this PI-500 plan and the total-control ledger are authorized for R12 edits. Production code, test code, handoff, canonical contracts, JSON, YAML, mapping, and all other files remain unmodified; Python=`false`; pytest=`false`; collection=`false`; fenced snippets=`false`; CLI/PowerShell=`false`; Git=`false`; YAML=`false`; mapping=`false`; runtime verification=`false`;
- residual unknowns: copied-module parseability, AST inventories, collection, runtime behavior, whether every implementation rejection supplies the planned typed carrier, repository-wide changed-path evidence, and implementation conformance remain unverified. This static remediation does not self-accept, claim PASS, complete G5, or authorize implementation;
- governance: status=`READY_FOR_REVIEW`; remediator self-acceptance=`false`; PASS claimed=`false`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`; the only next action is parent-instance verification of R12. Only after parent acceptance may a fresh, independent, role-separated `PI-590-R12` instance be started.

## PI-570-R13 remediation record

- triggering findings: the parent rejected R12 with two High blockers. First, the three literal Task 10 adapters populated `PhaseIssueObservation` only in `except F09Error`, although canonical Task 7/8 ports preserve several negative outcomes as successful typed returns; therefore T21–T29, T58, and T68–T71 could lack a returned-output same-surface pair. Second, Task 1 named and imported `F09Error` but supplied no complete contiguous literal-copy `engine/f09/errors.py` module.
- actual bounded static changes: Task 1 now contains the complete immutable typed `F09Error` literal block with the existing four subtypes, nonempty typed-field checks, separate diagnostic text, and no diagnostic parsing. Task 1 also owns one immutable transport-only `DetectedIssue(issue_code, field_path)` runtime identity. Tasks 6–8 import that identity and add production-owned typed return surfaces: `ProjectionValidationResult.detected_issues`, `ArtifactSetManifest.detected_issues`, `FeedbackBinding.detected_issues`, and `LearningEligibility.detected_issues`.
- detection ownership: Tasks 6–8 must create code and path together at the actual frozen rejection branch. Coherent negative results return their typed records; incoherent/non-returnable rejection paths raise only the existing typed `F09Error` subtypes with both fields. Code-only issue IDs, blocking reason codes, statuses, dimensions, diagnostics, and exception class names cannot be converted into pairs downstream.
- adapter closure: the literal trace, artifact, and feedback adapters now mechanically forward every returned canonical `DetectedIssue` pair and append a caught `F09Error` pair without parsing text. They do not read expected fields, test IDs, mutation tokens, fixture patterns, baseline differences, or map status/state/dimensions/reasons to issue identity. `assert_issue()` remains the exact same-surface pair assertion; no code/path cross join was introduced, and no-issue rows still require all canonical and phase issue/error surfaces empty.
- static producer inventory: the plan now names a non-dangling canonical producer for phase-owned positive rows T19–T26, T28–T30, T37, T44–T45, T58, T68–T71, T89, T93, and T95–T101. T27 is explicitly retained as PI-300 no-issue idempotent success; decision-owned and no-issue rows are not reclassified to manufacture phase issues.
- preserved frozen boundaries: the five helpers retain literal token-by-token `match` and unknown-token fail-closed dispatch. T01–T104 semantics, all five 104-item inventories, 31 adapter component tests with `10/10/11` split, four Task 10 paths, one conftest block, one vertical-matrix block, seven Enums, dataclasses, lowercase `sha256`, F09-only scope, F08 identity-only behavior, and production-default isolation were not intentionally changed.
- static evidence only: the R12 prose/code mismatch, Task 6–8 return shapes, literal adapters, exact-pair assertion architecture, no-issue closure, helper dispatch locations, and inventory text were inspected statically. This is plan text and not proof that copied modules parse, collect, execute, or conform at runtime.
- bounded scope and non-execution: only this PI-500 plan and the total-control ledger are modified. Production code, test code, `handoff.md`, canonical PI-210/220/230/300 documents, JSON, YAML, mapping, and all other files remain unmodified; Python=`false`; pytest=`false`; collection=`false`; fenced snippets=`false`; CLI/PowerShell=`false`; Git=`false`; YAML=`false`; mapping=`false`; runtime verification=`false`.
- unproven items: copied-module parseability, dataclass/exception runtime behavior, AST inventories, test collection, runtime issue-producer coverage, exact row execution, repository-wide changed-path evidence, and implementation conformance remain unverified. R13 does not self-accept, claim PASS, complete G5, or authorize implementation.
- governance: status=`READY_FOR_REVIEW`; remediator self-acceptance=`false`; PASS claimed=`false`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`; the sole next action is parent-instance verification of R13. Only after parent acceptance may a fresh, independent, role-separated `PI-590-R13` instance be opened.

## PI-570-R14 remediation record

- triggering findings treated as fixed blockers: the parent instance rejected R13 as `BLOCKED`. High 1: adding `detected_issues` closed only return shapes, while Tasks 6–8 lacked continuous literal detection-branch and constructor coverage for every phase-owned positive row. High 2: the R13 inventory omitted leading slashes while literal scenario constructors used leading-slash paths, so its “exact PI-300 path” claim was ambiguous. Medium closure: required-field success construction, imports/type identity, `replace()` preservation/reset behavior, legal no-issue states, and returned-versus-exception exclusivity were not mechanically closed.
- actual bounded static repair: Task 6 now has one continuous ordered branch block for T19, T20, T30, T37, T44, T45, T89, T93 and T95–T101; Task 7 has literal write/inspect/retry blocks for T21–T24, T27–T28 and T67–T72; Task 8 has literal binder constructors for T25, T26, T29 and T58 plus explicit eligibility construction. Each positive branch names its canonical port predicate, exact code, exact leading-slash path and returned or existing typed-exception constructor.
- constructor/import closure: Tasks 6–8 specifically import the sole Task 1 `DetectedIssue` runtime identity and only existing `F09Error` subtypes. Every displayed canonical success/no-issue construction passes `detected_issues=()`. Cross-phase `replace()` calls reset the tuple; only validation of the same immutable record preserves it. T27 no-op, T53 BOUND, T54 ELIGIBLE, T67 eight legal states and T72 `SUPERSEDED` are explicitly issue-free, and stale issues may not leak from write to inspect/retry or from binding to a new eligibility evaluation.
- returned-versus-exception closure: a coherent canonical negative returns exactly one typed pair; a non-returnable malformed input raises exactly one existing subtype carrying the same literal pair. The same detection cannot return and raise, and no adapter may add or repair a pair.
- exact-path closure: every R14 inventory path is copied byte-for-byte from the literal T01–T104 constructors and begins with `/`; T21 and T22 are separate exact rows rather than a `|` shorthand. No shorthand, normalization, prefixing or adapter-side path reconstruction exists.
- feedback oracle boundary: the seven-dimension and aggregate-status checks in `exercise_feedback_binding_phase()` remain independent contract-consistency assertions only. They cannot create, select, filter, map, validate or supplement an expected issue pair; positive issue evidence still comes only from returned binder/evaluator `detected_issues` or a typed exception.
- preserved static non-regression: the continuous conftest owner, continuous vertical-matrix owner, scenario-data import direction and four Task 10 paths were not edited. The 104 mutators, 104 constructors, 104 references, 104 nodes and 104-element tuple remain textually present; the 31 literal component tests and `10/10/11` split were not edited. Seven Enums, multiline dataclasses, lowercase `sha256`, F09-only/F08-reference-only boundaries, six independent gates, allocation/risk/dual-axis semantics, state/event separation, T72 old/current identity, T92 six mappings, T93 mismatch, T97 termination and production-default isolation were not intentionally changed.
- bounded scope and non-execution: only this PI-500 plan and the total-control ledger are modified. Production code, test code, `handoff.md`, PI-210/220/230/300, frozen F01–F12/F09 semantics, JSON, YAML, mappings and all other files remain unmodified. Python=`false`; pytest=`false`; collection=`false`; fenced-snippet execution=`false`; CLI/PowerShell=`false`; Git=`false`; GitHub mutation=`false`; runtime verification=`false`.
- unproven items: copied-module parseability, type checking, AST inventories, test collection, runtime branch reachability, actual producer behavior, exact row execution, repository-wide diff and implementation conformance remain unverified. This remediation cannot infer PASS, runtime correctness, G5 completion or PI-500 completion from static plan text.
- governance: status=`READY_FOR_REVIEW`; remediator self-acceptance=`false`; PASS claimed=`false`; `PI-570-R13=BLOCKED`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`; the sole next action is parent-instance verification of R14. Only after parent acceptance may a fresh, independent, role-separated `PI-590-R14` instance be opened.

READY_FOR_REVIEW

## Parent-instance PI-570-R14 static adjudication

- verdict: `BLOCKED`; parent acceptance=`false`; independent `PI-590-R14` is not authorized. The exact leading-slash inventory, explicit successful-return empty tuples, cross-phase reset prose, and feedback consistency/non-oracle boundary are accepted as bounded static improvements, but they do not close the producer implementation contract.
- High 1 — Task 6 is not fail-closed or mechanically copyable in its displayed order. T19 and T37 dereference `statement_set.decision_trace_ref` before T44 checks whether that required structure is absent; T37 and T89 dereference `result.action` without a displayed prerequisite-shape guard. A malformed input can therefore fail before either the planned returned `DetectedIssue` or typed `F09Error` producer is reached.
- High 2 — non-returnable branches still lack literal constructor closure. Task 6 uses placeholder `F09ContractError(issue_code="...", field_path="/...", diagnostic="...")` / subtype prose, and Tasks 7–8 similarly instruct the implementer to reuse displayed pairs instead of showing every exact branch-local exception constructor. This contradicts R14's claim that every row has an exact returned/exception constructor and leaves identity, ordering, reachability, and return-versus-raise selection to implementer inference.
- High 3 — the Task 6–8 blocks remain dependent on undeclared producer logic and values. Task 6 calls eight undefined semantic predicates for T93 and T95–T101 while describing them as five; Task 7 calls undefined stale/digest/idempotency comparison predicates; Task 8 references undefined target resolution, `resolved_statement`, identity comparison, seven-dimension locals, aggregate-status logic, and eligibility-fact evaluation. Consequently the displayed snippets are constructor sketches, not continuous mechanically copyable production-port implementations, and branch ownership/reachability cannot be statically verified.
- Medium 1 — Task 7's illegal-state guard `record.state not in ArtifactItemState` is not statically closed for the raw string stimuli intentionally used by T68/T69. The plan must use an explicit, mechanically legal type/value membership predicate before the exact typed exception constructor rather than rely on unspecified Enum containment behavior.
- non-regression boundary: no production code, test code, canonical PI-210/220/230/300 authority, JSON, YAML, mapping, `handoff.md`, production default, F08 behavior, or frozen F01–F12/F09 semantics was modified or authorized by this adjudication. No Python, pytest, collection, fenced snippet, CLI/PowerShell, Git, or GitHub operation was executed.
- required bounded remediation: a fresh role-separated `PI-570-R15` writer may modify only this plan and the control ledger. It must place structural guards before all nullable/shape-sensitive dereferences; provide every exact literal returned and non-returnable exception branch without ellipses; define or inline every producer predicate/helper and all prerequisite locals needed by the Task 6–8 copy blocks; correct the eight-predicate inventory; and replace the illegal-state check with an explicit raw-value-safe predicate. It must preserve the accepted exact-path, no-issue/reset, same-surface oracle, Task 10 ownership/accounting, F09/F08, and production-isolation boundaries.
- governance: `PI-570-R14=BLOCKED`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`; unique next legal action=`PI-570-R15` bounded remediation. Runtime correctness, parseability, collection, implementation conformance, PI-500 completion, and G5 completion remain unproven.

BLOCKED

## PI-570-R15 remediation record

- fixed parent findings: R15 treats the parent-instance R14 adjudication as fixed at exactly three High findings and one Medium finding. It does not reopen the accepted R14 exact-path, no-issue/reset, same-surface oracle, Task 10 ownership/accounting, F09/F08, or production-isolation boundaries.
- High 1 static closure: the Task 6 continuous producer now guards `StatementSet`, required statement-set fields, `decision_trace_ref`, the first statement, `DecisionEvaluationResult`, canonical `result.action_envelope`, `TraceEnvelope`, and each traversed collection/member shape before the corresponding sensitive dereference. Every coherent negative returns its branch-local pair; every non-returnable malformed prerequisite raises one displayed typed constructor.
- High 2 static closure: Tasks 6–8 now display complete branch-local `F09Error` subtype constructors with literal issue code, literal leading-slash path, and literal diagnostic. Task 7 no longer builds semantic issue paths from `role`; REPORT, STATEMENT_RECORDS, and STATEMENT_INDEX absence, partial-write, and filesystem-error branches each carry their own literal path. No detection is specified to both return and raise.
- High 3 static closure: the Task 6 block defines exactly eight booleans (`t93`, `t95`, `t96`, `t97`, `t98`, `t99`, `t100`, `t101`) and all graph/path/source locals in the same continuous source. Task 7 defines writer, inspection, retry, digest, stale-revision, payload-comparison, and eligibility inputs locally. Task 8 defines target resolution, seven dimensions, aggregate precedence, identity conflict, references, eligibility status, targets, exclusions, and reasons in its two continuous functions. Task 10 preserves upstream outcome transformations while adding state/event transformations and converts T95/T96/T98/T99/T100 fixture deltas into the canonical graph consumed by Task 6; T58 changes the source snapshot digest while preserving the baseline submission content digest.
- Medium static closure: T68/T69 use an explicit raw-value-safe predicate: canonical `ArtifactItemState` instances are accepted; raw strings are compared only with the explicit eight-value tuple. The rejected `record.state not in ArtifactItemState` form is absent from the active R15 producer source.
- preserved no-issue and transport boundaries: canonical Task 6 success, artifact write success, T27 retry no-op, T67/T72 inspection, each no-issue feedback binding, and every fresh eligibility construction explicitly use or reset `detected_issues=()`. T53, T54, T67, and T72 remain issue-free. Task 10 forwards only returned `DetectedIssue` pairs or caught typed `F09Error` pairs; feedback dimension/status checks remain consistency assertions and never issue oracles.
- preserved structural boundaries: one conftest owner, one matrix owner, four Task 10 paths, five 104-item inventories, 31 component tests split 10/10/11, seven Enums, multiline dataclasses, lowercase `sha256`, F09-only scope, F08 identity-only behavior, unchanged production defaults, T72 old/current identity and legal `SUPERSEDED` semantics, and frozen F01–F12/F09 semantics remain required and were not reclassified.
- bounded scope and non-execution: only this plan and the control ledger were authorized for modification. No production code, test code, PI-210/220/230/300 authority, `handoff.md`, JSON, YAML, mapping, or other repository file was modified or authorized. Python=`false`; pytest=`false`; collection=`false`; fenced-snippet execution=`false`; CLI/PowerShell=`false`; Git=`false`; GitHub mutation=`false`; runtime verification=`false`.
- evidence limit: this record reports static text reconciliation only. Parseability, type checking, AST inventories, collection, runtime branch reachability, actual producer behavior, exact row execution, repository-wide diff, and implementation conformance remain unverified. R15 does not claim `PASS`, parent acceptance, PI-500 completion, G5 completion, or implementation authorization.
- governance: status=`READY_FOR_REVIEW`; remediator self-acceptance=`false`; PASS claimed=`false`; `PI-570-R14=BLOCKED`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`. The sole next action is parent-instance verification of R15. A fresh independent role-separated `PI-590-R15` may be opened only after parent acceptance.

READY_FOR_REVIEW

## Parent-instance PI-570-R15 static adjudication

- verdict: `BLOCKED`; parent acceptance=`false`; independent `PI-590-R15` is not authorized. The parent accepts only the bounded R15 improvements that are directly visible: Task 6 now guards the principal container shapes before their former dereferences and uses canonical `result.action_envelope`; Task 7 replaces raw Enum containment with an explicit eight-value guard; many returned and raised pairs are now literal; the eight Task 6 predicate names are textually accounted for. These improvements do not close producer semantics or mechanical reachability.
- High 1 — Task 7 cannot implement the frozen T27/T28 idempotency distinction. `retry_artifact_set()` receives no incoming `IdempotencyKey` and never compares an incoming key with `manifest.key`; it only compares retry projection digests with whichever non-superseded records happen to be comparable. It can therefore label a different-key request as T27 no-op or T28 conflict, and `bool(comparable_records) + all(...)` can accept a strict subset of required roles. PI-230 requires same-key/same-digest no-op and same-key/different-digest mismatch, while changed canonical input requires a new operation identity. The displayed port and branch are not sufficient to prove those predicates.
- High 2 — Task 8's T58 producer contradicts canonical feedback identity. `digest_conflict = submission.source_snapshot_ref.content_digest != submission.content_digest` compares the feedback-source digest with the whole-submission digest, although PI-300 explicitly models these as distinct `D-FEEDBACK-SOURCE` and `D-FEEDBACK-SUBMISSION` values. T58 requires comparison with a prior operation carrying the same feedback operation identity and a changed source digest; the displayed binder receives no prior key, ingest attempt, receipt, or prior submission. The Task 10 assertion that forces both unrelated digests equal is a fixture-shaped oracle rather than the canonical cross-operation invariant. A valid canonical PI-300 submission can therefore be falsely rejected, while same-key conflict cannot be established.
- High 3 — Task 8 remains mechanically and semantically open. Its claimed continuous source calls `validate_feedback_binding_record()` and `validate_learning_eligibility()` without literal implementations, leaving required-field, seven-dimension, status/anchor coherence, target cardinality, and fail-closed checks to future inference. It also assigns `resolved_statement.evidence_refs` to `target_object_refs` and then reuses those refs as `learning_target_refs`; PI-230/PI-300 require versioned statement/set/records targets for the binding and the mapped rule anchor for learning. `record_anchor_ref` is instead taken from an artifact attempt input snapshot, which does not prove the required rule anchor or metadata. The displayed positive T53/T54 path therefore does not implement the canonical binding/learning target contract.
- High 4 — Task 6 does not preserve canonical baseline identity or prove T101 reachability. T96 hardcodes `SNAP-F09-1`, `snapshot-v1`, `PI300-V1`, and `2026-07-20T00:00:00Z`, but the accepted immutable PI-300 fixture defines `PI-300-F09-SOURCE-SNAPSHOT-V1`, `reality-fact-source-snapshot.v1`, `pi-300-f09-source-snapshots-v1`, and `2026-07-19T00:00:00Z`; a valid canonical fixture therefore satisfies the displayed mismatch predicate. Separately, T101 requires all copied terminal names `axis/action/object/tense` to occur in `statement_text`, while its literal mutation text contains none of those four names, so its own `OUTPUT.SCOPE_EXCEEDED` branch is not reachable from the planned scenario after otherwise-valid transformations are preserved.
- Medium 1 — Task 7 adds `ARTIFACT.WRITE_FAILED @ /artifacts/REPORT` returned and exception semantics although the frozen phase-owned T21/T22 inventory assigns write-failure pairs only to STATEMENT_RECORDS and STATEMENT_INDEX, and T21 explicitly starts after report success. The broader failure-injection checklist mentions killing report writes but does not canonically define this new pair. Exact authority and inventory treatment are therefore ambiguous; R15 may not silently expand the frozen issue surface while claiming unchanged T01–T104 semantics.
- non-regression boundary: this adjudication does not reopen or reject the previously accepted leading-slash paths, explicit no-issue/reset rules, same-surface transport rule, Task 10 ownership/accounting, raw-state guard improvement, F09-only/F08-identity-only scope, or production-default isolation. It modifies no production code, test code, canonical PI-210/220/230/300 authority, JSON, YAML, mapping, or `handoff.md`; no Python, pytest, collection, fenced-snippet, CLI/PowerShell, Git, or GitHub operation was executed.
- required bounded remediation: a fresh role-separated `PI-570-R16` writer may modify only this plan and the control ledger. It must give T27/T28 an actual same-key plus complete-payload identity comparison; model T58 against an explicit prior canonical operation/receipt rather than equating source and submission digests; provide literal binding/eligibility validators and canonical statement/set/records plus rule-anchor refs; consume the exact accepted PI-300 source snapshot identity; make T101's scenario reach its producer without fixture-derived issue inference; and reconcile or remove the unauthorized REPORT issue pair. It must preserve all accepted R13–R15 local improvements and every governance/nonexecution boundary.
- governance: `PI-570-R15=BLOCKED`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`; unique next legal action=`PI-570-R16` bounded plan-only remediation. Runtime correctness, parseability, collection, implementation conformance, PI-500 completion, and G5 completion remain unproven.

BLOCKED

## PI-570-R16 remediation record

- fixed parent findings: R16 closes only the parent-instance R15 inventory fixed at exactly `4 High + 1 Medium`; it does not reopen any accepted R13–R15 non-regression boundary and does not adjudicate itself.
- High 1 static closure: Task 7 retry now receives an actual incoming canonical `IdempotencyKey`, proves equality across every identity field and `canonical_key_digest` before payload comparison, and requires exactly one current expected digest for each complete required role (`REPORT`, `STATEMENT_RECORDS`, `STATEMENT_INDEX`). Changed-key input emits a nonsemantic new-operation control signal outside T27/T28; same key plus the identical complete role set is T27, and same key plus any complete-set difference is T28. Task 10 constructs the incoming key and all three byte payloads explicitly.
- High 2 static closure: Task 8 receives an explicit `prior_submission` and defines same feedback operation using existing canonical submission fields. T58 compares only prior/current `source_snapshot_ref.content_digest` after those operation fields match; source digest is never compared with whole-submission `content_digest`. Task 10 independently constructs prior/current canonical submissions and changes only current source digest for T58.
- High 3 static closure: Task 8 now contains continuously copyable literal implementations of `validate_feedback_binding_record()` and `validate_learning_eligibility()`. A BOUND target graph is exactly canonical statement, statement-set, and statement-records `VersionedObjectRef`s; `record_anchor_ref` is the mapped first rule-anchor evidence ref; ELIGIBLE contains only that rule-anchor ref in `learning_target_refs`. Evidence refs and artifact attempt input snapshots no longer substitute for the three binding targets.
- High 4 static closure: Task 6 and Task 10 baseline use the exact immutable identity `PI-300-F09-SOURCE-SNAPSHOT-V1`, `reality-fact-source-snapshot.v1`, `pi-300-f09-source-snapshots-v1`, and `2026-07-19T00:00:00Z`, retain lowercase `sha256`, retain `RFC8785-JCS-UTF8`, and bind the accepted digest to the immutable JSON payload-only boundary. T101 now tests intact literal COPY targets and its mutation keeps `axis`, `action`, `object`, and `tense` explicit while adding prohibited tool/amount/wealth-outcome scope, so the producer predicate is literal rather than adapter-inferred.
- Medium static closure: `/artifacts/REPORT` is removed from the phase-owned `DetectedIssue` and typed F09 issue inventory. REPORT must succeed before frozen T21; REPORT filesystem failure remains a nonsemantic `OSError` before the T21/T22 semantic boundary and cannot expand the frozen issue pair inventory.
- bounded scope and non-execution: modified files are limited to this plan and the control ledger. No production code, test code, canonical PI-210/220/230/300 authority, JSON, YAML, mapping, `handoff.md`, or other repository file was modified. Python=`false`; pytest=`false`; collection=`false`; fenced-snippet execution=`false`; CLI/PowerShell=`false`; Git=`false`; GitHub mutation=`false`; runtime verification=`false`.
- evidence limit: this record is static plan-text remediation only. Parseability, type checking, AST inventories, collection, runtime branch reachability, actual producer behavior, repository-wide diff, and implementation conformance remain unverified. R16 does not claim `PASS`, parent acceptance, PI-500 completion, G5 completion, implementation authorization, or independent review launch.
- governance: status=`READY_FOR_REVIEW`; remediator self-acceptance=`false`; PASS claimed=`false`; `PI-570-R15=BLOCKED`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`. The unique next action is parent-instance verification of R16. No `PI-590-R16` may start before parent acceptance.

READY_FOR_REVIEW

## PI-570-R16 parent static adjudication

- verdict: `BLOCKED`; parent acceptance=`false`; independent `PI-590-R16` is not authorized. The parent directly inspected the actual R16 Task 6, Task 7, Task 8, Task 10 adapter/mutator text, the PI-230 identity/retry/feedback authority, the PI-300 idempotency authority, the R16 remediation record, and the control ledger. The parent accepts only the bounded improvements directly visible in the plan: T96 now uses the accepted immutable source identity; T101 has a literal reachable prohibited-output stimulus while preserving the four COPY paths; retry receives and compares an incoming key; the two validator bodies are no longer dangling; and the unauthorized REPORT semantic issue pair was removed. These improvements do not close the remaining canonical identity and retry contradictions.
- High 1 — Task 7 makes the canonical partial-artifact retry path impossible. PI-230 requires artifact single-item retry and PI-300 expressly permits same-key continuation of missing steps, but `retry_artifact_set()` rejects every manifest unless REPORT, STATEMENT_RECORDS, and STATEMENT_INDEX each already have exactly one current expected digest. T21/T22 partial manifests necessarily lack at least the failed role and therefore cannot be retried through this port. The newly invented `NewArtifactOperationRequired` control exception also has no canonical PI-230/PI-300 type or displayed ordinary new-operation caller transition; Task 10 merely converts it to an error string. R16 therefore does not provide the complete fail-closed retry lifecycle it claims.
- High 2 — T58 still contradicts canonical feedback operation identity and does not satisfy the fixed R15 requirement for a prior canonical operation or receipt. PI-300 requires feedback source digest to participate in `canonical_key_digest` and states that changing it creates a different operation identity. R16 instead defines `same_feedback_operation` by omitting source digest and without receiving either prior/current `IdempotencyKey`, eligibility policy identity, ingest attempt, or receipt, then emits `IDEMPOTENCY.DIGEST_MISMATCH` solely from two `FeedbackSubmission` values. This cannot distinguish same-key/different-target mismatch from changed-canonical-input/new-operation identity and leaves T58 fixture-shaped rather than authority-shaped.
- High 3 — `source_track_binding_ref` violates the explicit PI-230 binding contract. R16 assigns `submission.track_source_binding.source_evidence_ref`, although PI-230 requires a `VersionedObjectRef` that exactly references the `TrackSourceBinding` itself by `track_source_binding_id`, schema version, contract version, and content digest. The existing Task 10 positive assertions expect that exact binding identity, so the displayed producer and its own acceptance surface disagree. A BOUND feedback record cannot be canonical under this source.
- High 4 — the claimed canonical target and rule-anchor graph remains fabricated from unrelated values rather than resolved identities. The statement ref is bound to the whole feedback-submission digest; the statement-set ref is bound to the artifact manifest digest and reuses a statement revision; the records ref uses `schema_version` as both revision and schema identity; and `record_anchor_ref` blindly takes `resolved_statement.evidence_refs[0]`. No records projection mapping proves that the first evidence ref is the unique selected rule anchor, nor are required anchor metadata, revision, schema/contract identity, or digest resolution established. The validator checks only object type/cardinality and then raises if a producer-computed `BOUND` lacks these refs; it does not turn missing canonical binding prerequisites into the required coherent fail-closed aggregate status. T53/T54 BOUND/ELIGIBLE therefore remain unproven and may target a generic evidence ref.
- Medium 1 — removing `/artifacts/REPORT` from the semantic issue inventory closes the unauthorized pair expansion, but replacing it with a raw `OSError` before any `ArtifactWriteAttempt` or manifest evidence is recorded leaves the general PI-230 audit boundary open. PI-230 requires every artifact and attempt to preserve outcome, digest/error evidence, and time independently; a REPORT filesystem failure currently escapes without the typed/auditable attempt representation used by the other roles. R16 must reconcile nonsemantic pre-T21 failure with the canonical artifact audit model without inventing a phase-owned issue pair.
- non-regression boundary: this adjudication does not reopen the accepted T96 identity correction, T101 literal reachability correction, leading-slash paths, explicit no-issue/reset rules, same-surface issue transport, raw-state guard, Task 10 ownership/accounting, F09-only/F08-identity-only scope, frozen F01–F12/F09 semantics, or production-default isolation. It modifies only this plan adjudication and the control ledger. No production code, test code, canonical PI-210/220/230/300 authority, JSON, YAML, mapping, or `handoff.md` is modified; no Python, pytest, collection, fenced-snippet, CLI/PowerShell, Git, or GitHub operation is executed.
- required bounded remediation: a fresh role-separated `PI-570-R17` writer may modify only this plan and the control ledger. It must support same-key continuation of canonical partial artifact sets while preserving complete target identity; use only canonical control/error surfaces or display the authoritative caller transition; model T58 with explicit prior/current canonical keys or receipts so changed source digest is a new identity rather than an invented same-operation predicate; construct `source_track_binding_ref` from the TrackSourceBinding identity/version/digest; resolve statement/set/records refs and the selected rule anchor from their canonical records and metadata rather than unrelated digests or evidence ordering; return coherent non-BOUND records when required canonical inputs are absent; and retain auditable REPORT failure without expanding the frozen issue pair inventory. All accepted R13–R16 local improvements and nonexecution boundaries remain mandatory.
- governance: `PI-570-R16=BLOCKED`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`; unique next legal action=`PI-570-R17` bounded plan-only remediation by a fresh writer. `PI-590-R16` is permanently unauthorized. Parseability, collection, runtime behavior, implementation conformance, PI-500 completion, and G5 completion remain unproven.

BLOCKED

## PI-570-R17 remediation record

- triggering findings: the fixed parent adjudication remains exactly `4 High + 1 Medium`; `PI-570-R16=BLOCKED` is not rejudged here.
- High 1 bounded static repair: Task 7 permits zero or one current non-superseded record per required role, proves every present expected target digest before writing, returns T27 only for the complete verified equal set, returns T28 for same-key/different-target without overwrite, and continues only missing/failed/unverified roles. `coordinate_artifact_operation()` mechanically routes absent/changed key to the ordinary new write path and exact key equality to retry; the unauthorized local control exception is removed.
- High 2 bounded static repair: Task 8 consumes prior/current canonical `IdempotencyKey` and prior/current target digest evidence. Changed source digest must change `canonical_key_digest` and is represented as changed-input/new identity; exact same-key/different-target remains the separate mismatch branch. Both preserve T58 `mismatch/new identity; no last-write-wins` without an identity predicate that omits source digest.
- High 3 bounded static repair: `source_track_binding_ref` now references `FeedbackSubmission.track_source_binding` itself with `track_source_binding_id`, its schema version, contract version, content digest, locator, and capture time.
- High 4 bounded static repair: Task 8 receives canonical statement refs, the canonical statement-set ref, statement-records projection refs, and `AnchorSelectionRecord` mapping from their own objects/records/metadata. The selected rule anchor is explicit rather than inferred from evidence order. Missing prerequisites alter dimensions before priority aggregation and produce a coherent non-BOUND empty target graph; `ELIGIBLE` requires the resolved selected object of type `RULE` and targets only that ref.
- Medium 1 bounded static repair: REPORT filesystem failure remains outside the frozen phase-owned semantic issue-pair inventory, but writer/retry returns a canonical FAILED `ArtifactRecord` with append-only FAILED `ArtifactWriteAttempt`, target digest, input refs, outcome, error class, error-message digest, and start/finish time. T21/T22 injected failures use the same audited path.
- Task 10 alignment: the artifact adapter calls the displayed coordinator and no longer catches or asserts the removed control type. Its planned partial-retry assertions cover T21/T22 continuation and T27/T28 separation. The feedback adapter is required to build prior/current canonical keys, canonical projection refs, and anchor-selection records before calling the revised binder; T53/T54 remain issue-free and T58 separately asserts changed source digest, changed canonical key, and no overwrite. Ownership remains one conftest owner, one matrix owner, five 104-item inventories, 31 component tests split `10/10/11`, and the four existing Task 10 paths.
- preserved accepted boundaries: exact T96 source identity and payload-only digest boundary, literal T101 reachability, leading-slash paths, producer-owned same-surface issue transport, explicit no-issue/reset behavior, raw-state-safe guard, T27/T53/T54/T67/T72 issue-free behavior subject only to canonical coherent non-BOUND authority, F09-only scope, F08 identity-only behavior, unchanged production defaults, and frozen F01–F12/F09 semantics are not reopened.
- bounded scope and non-execution: modified files are limited to this plan and the control ledger. Production/test code, canonical authority, JSON, YAML, mapping, and `handoff.md` are untouched. Python=`false`; pytest=`false`; collection=`false`; fenced-snippet execution=`false`; CLI/PowerShell=`false`; Git=`false`; GitHub mutation=`false`; runtime verification=`false`.
- evidence limit: this is static plan-text remediation only. Parseability, type checking, AST/accounting checks, collection, runtime branch reachability, implementation conformance, PI-500 completion, and G5 completion remain unverified. No `PASS` or parent acceptance is claimed.
- governance: status=`READY_FOR_REVIEW`; remediator self-acceptance=`false`; `PI-570-R16=BLOCKED`; `PI-570-R17=READY_FOR_REVIEW`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`. Unique next action is parent-instance verification of R17. No `PI-590-R17` may start before parent acceptance.

READY_FOR_REVIEW

## PI-570-R17 parent static adjudication

- verdict: `BLOCKED`; parent acceptance=`false`; independent `PI-590-R17` is not authorized. The parent directly inspected the actual R17 Task 7 writer/retry/coordinator, Task 8 binder/evaluator/validators, Task 10 artifact and feedback adapters, the R17 remediation record, PI-230 feedback-binding and retry authority, PI-300 canonical feedback target/idempotency authority, and the control ledger. The parent accepts only the bounded improvements directly visible in the plan: partial manifests can now enter retry; the unauthorized local new-operation exception is removed; REPORT failure returns an auditable failed record/attempt without expanding the semantic issue inventory; and `source_track_binding_ref` now identifies the TrackSourceBinding itself. These local improvements do not close the active copyability, canonical target, identity, or operation-isolation contradictions.
- High 1 — Task 10 still calls the removed R16 feedback port and therefore cannot copy or exercise the displayed R17 binder. The adapter passes `prior_submission=prior_submission`, while `validate_feedback_binding()` no longer accepts that keyword and instead requires `prior_key`, `current_key`, `prior_target_digest`, `current_target_digest`, `statement_refs`, `statement_set_ref`, `records_projection_refs`, and `anchor_selections`. No later adapter code constructs or passes those canonical inputs. The R17 remediation claim that Task 10 builds them is contradicted by the actual call site; T53/T54/T58 and the 104-row matrix are not mechanically reachable through this adapter.
- High 2 — the positive rule-anchor path is internally impossible. The producer/evaluator permits `ELIGIBLE` only when `record_anchor_ref.object_type == "RULE"`, consistent with PI-300's `V-RULE-ANCHOR`, but `validate_feedback_binding_record()` rejects every non-`CARD_FIELD` anchor and `validate_learning_eligibility()` rejects every ELIGIBLE target whose type is not `CARD_FIELD`. A RULE anchor fails both validators; a CARD_FIELD anchor can never enter the evaluator's ELIGIBLE branch. T53 BOUND plus T54 ELIGIBLE is therefore statically unreachable.
- High 3 — the PREPROD positive protocol is also internally impossible. `canonical_prerequisites_resolved` requires a resolved statement/ref and selected statement anchor even for `PREPROD_RUN_TARGET`; consequently the target graph is empty for a legitimate run-only target. Status aggregation can nevertheless produce `BOUND` because PREPROD does not set `target_unbound` merely for absent statement prerequisites, after which `validate_feedback_binding_record()` rejects every BOUND record lacking the three production statement refs and an anchor. The plan's own required PREPROD BOUND case cannot pass its producer-owned validator.
- High 4 — T58 has no producer-owned observable changed-input/new-identity outcome. `changed_input_new_identity` is computed and used only to reject the invalid case where source digest changes without canonical-key change; the returned `IDEMPOTENCY.DIGEST_MISMATCH` pair is instead attached solely to `same_key_different_target`. The active prose still says all operation identity fields remain equal while source digest changes, directly contradicting PI-300's rule that source digest participates in canonical identity. Thus the frozen T58 result `mismatch/new identity; no last-write-wins` is neither represented by a canonical operation result/receipt nor reachable as the claimed returned pair.
- High 5 — changed-key artifact routing creates a new manifest identity but not an isolated artifact operation. `coordinate_artifact_operation()` calls `write_artifact_set()` with the same caller root, and both writer and retry use fixed role paths such as `root / "report.bin"`. A changed canonical key therefore overwrites the prior operation's committed role files while merely changing artifact/manifest IDs. This violates new-operation identity, retained auditability, and the plan's own no-overwrite review boundary.
- Medium 1 — canonical feedback inputs are trusted by map lookup rather than validated as the PI-230 canonical inputs that determine `INVALID > AMBIGUOUS > UNBOUND > BOUND`. The binder dereferences `statement_set_ref.object_id` before validating its shape; checks only statement-set object ID; and does not prove statement, records projection, or anchor-selection object type, revision, schema, contract, digest, membership, policy, fidelity, partition, or source-order identity. Missing refs are generally downgraded to `UNBOUND`, although PI-230 requires malformed or inconsistent canonical identity/version/digest inputs to be `INVALID`.
- Medium 2 — partial retry does not preserve a complete canonical target identity for a missing role. A newly reconstructed record receives `schema_version=None`, and retry chooses `canonical_input_refs` from the first nonempty attempt anywhere in the manifest rather than proving one identical frozen input tuple across all retained attempts. This leaves schema/revision/input binding underdetermined for T21/T22 continuation despite the claimed frozen-input preservation.
- non-regression boundary: this adjudication does not reopen the accepted R13–R17 local improvements, T96 immutable source identity, T101 literal reachability, leading-slash paths, producer-owned same-surface issue transport, explicit no-issue/reset rules, raw-state guard, fixed Task 10 ownership/accounting, F09-only/F08-identity-only scope, frozen F01–F12/F09 semantics, or production-default isolation. It modifies only this plan adjudication and the control ledger. No production code, test code, canonical PI-210/220/230/300 authority, JSON, YAML, mapping, or `handoff.md` is modified; no Python, pytest, collection, fenced-snippet, CLI/PowerShell, Git, or GitHub operation is executed.
- required bounded remediation: a fresh role-separated `PI-570-R18` writer may modify only this plan and the control ledger. It must align the Task 10 feedback call with the displayed canonical R17 interface and literally construct all required keys/digests/ref maps/anchor selections; use one canonical rule-anchor object type consistently through binder, validators, evaluator, and PI-300 positive cases; give PREPROD its canonical run-target graph and validator rules without fabricating production statement refs; represent T58 changed-source/new-key as an observable new-operation outcome distinct from same-key/different-target mismatch and remove contradictory prose; isolate artifact paths by canonical operation identity so changed keys cannot overwrite prior files; validate every canonical feedback ref/selection dimension before status aggregation; and preserve schema/revision/frozen input identity for missing-role continuation. All accepted non-regression and nonexecution boundaries remain mandatory.
- governance: `PI-570-R17=BLOCKED`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`; unique next legal action=`PI-570-R18` bounded plan-only remediation by a fresh writer. `PI-590-R17` is permanently unauthorized. Parseability, collection, runtime behavior, implementation conformance, PI-500 completion, and G5 completion remain unproven.

BLOCKED

## PI-570-R18 remediation record

- triggering findings: the fixed parent adjudication remains exactly `5 High + 2 Medium`; `PI-570-R17=BLOCKED` is not re-adjudicated here.
- High 1 bounded static repair: Task 10 now constructs and passes actual prior/current canonical `IdempotencyKey` values, prior/current target digests, statement/set/records refs, `StatementProjectionRecord`, `AnchorSelectionRecord`, and PREPROD target refs to the current Task 8 binder. It consumes `FeedbackOperationResult.detected_issues` and `.bindings`; T53/T54 proceed through the returned bindings and T58 asserts the returned operation receipt.
- High 2 bounded static repair: the canonical selected anchor is consistently `RULE` through the binder, binding validator, evaluator, eligibility validator, and Task 10 `V-RULE-ANCHOR` positive construction. `CARD_FIELD` is not used as the feedback learning anchor.
- High 3 bounded static repair: Task 8 resolves PREPROD from its own `RUN_SNAPSHOT`/`DECISION_RUN`/`FEEDBACK_ATTACHMENT` records and refs, emits no production statement refs, and requires `record_anchor_ref=None`; the validator selects target kinds and anchor coherence by protocol.
- High 4 bounded static repair: changed source plus changed canonical key now returns producer-owned `FeedbackOperationResult(operation_disposition="NEW_OPERATION", source_identity_relation="CHANGED", overwrite_permitted=False)` with prior/current key and target-digest evidence. Same-key/different-target remains the distinct `TARGET_MISMATCH` result and no last-write-wins is permitted.
- High 5 bounded static repair: Task 7 writer and retry root every physical artifact path under `root / key.canonical_key_digest.value`; exact-key retry reuses that operation directory, while changed keys use disjoint directories and retain prior files and append-only audit evidence.
- Medium 1 bounded static repair: Task 8 checks canonical map/ref shapes before lookup and validates object kind, identity/revision, schema/contract, digest, records projection membership, selected/non-anchor relationship, policy, fidelity, partition/fanout scope, source order, and protocol graph coherence before `INVALID > AMBIGUOUS > UNBOUND > BOUND` aggregation. Malformed/inconsistent material is `INVALID`, multiple valid candidates are `AMBIGUOUS`, and valid absence/mismatch is `UNBOUND`.
- Medium 2 bounded static repair: Task 7 retry proves every retained attempt has the same nonempty frozen input-ref tuple and exact canonical key, and every retained record shares non-null identical schema version plus case/track/statement-set identity. Missing-role records inherit the proven schema and frozen input refs; `schema_version=None` is no longer synthesized or accepted.
- preserved boundaries: R13–R17 accepted local improvements, T96/T101 identity and reachability, exact leading-slash transport, no-issue/reset behavior, F09-only/F08-identity-only scope, frozen F01–F12/F09 semantics, production-default isolation, four Task 10 paths, five 104-item inventories, and 31 component tests split `10/10/11` are not reopened.
- bounded scope and non-execution: only this plan and the control ledger are modified. Production/test code, canonical PI-210/220/230/300 authority, JSON, YAML, mapping, `handoff.md`, and all other files remain untouched. Python=`false`; pytest=`false`; collection=`false`; fenced-snippet execution=`false`; CLI/PowerShell=`false`; Git=`false`; GitHub mutation=`false`; runtime verification=`false`.
- evidence limit: this is static plan-text remediation only. Parseability, type checking, AST/accounting checks, collection, runtime branch reachability, implementation conformance, PI-500 completion, and G5 completion remain unverified. No `PASS` or parent acceptance is claimed.
- governance: status=`READY_FOR_REVIEW`; remediator self-acceptance=`false`; `PI-570-R17=BLOCKED`; `PI-570-R18=READY_FOR_REVIEW`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`. Unique next action is parent-instance static verification of R18. No `PI-590-R18` may start before parent acceptance.

READY_FOR_REVIEW

## PI-570-R18 parent static adjudication

- verdict: `BLOCKED`; parent acceptance=`false`; independent `PI-590-R18` is not authorized. The parent directly inspected the actual R18 Task 7 retry/path logic, Task 8 operation receipt/protocol graph/canonical validation, Task 10 canonical-input construction and binder call, the R18 remediation record, PI-230 feedback-binding authority, PI-300 idempotency/T53/T54/T58 authority, and the control ledger. The parent accepts only the bounded improvements directly visible in the plan: the Task 10 call now matches the displayed binder signature; the positive learning anchor is consistently `RULE`; changed-source/new-key has a producer-owned operation receipt; and changed artifact keys select distinct operation directories. Those local improvements do not close the canonical identity, target-digest, PREPROD independence, malformed-input, or retry-history gates.
- High 1 — Task 10 does not construct the PI-300 canonical feedback key it claims to pass. `canonical_key_digest` hashes only `feedback_id + source_digest`; it omits normalized feedback item IDs, every target statement revision, eligibility `policy_id + policy_version`, top-level case/track/statement-set identity, and the schema/contract digests themselves. Consequently T55/T56/T57 are not represented by the operation identity and T58 proves only a fixture-specific string change, contrary to PI-300 lines 1196–1209.
- High 2 — the prior/current target evidence is not producer-owned canonical target-graph evidence. Task 10 assigns both `prior_target_digest` and `current_target_digest` to `input_manifest.digest` after replacing `records` without recomputing that digest, and it never binds the protocol-specific statement/set/records/anchor or run-target graph into a fresh digest. The same-key/different-target branch therefore cannot mechanically observe the displayed changed target, and the operation receipt can report stale equal target digests.
- High 3 — PREPROD remains structurally dependent on production-only material and on a locally asserted target graph without sufficient canonical authority. The adapter rejects a run target unless a production statement and a manifest record exist, always constructs statement/set/records/`RULE`-anchor inputs, and removes the PREPROD records whenever the shared `anchor_status` is not `MAPPED`; its aggregate oracle likewise requires that production anchor status for every protocol. PI-230 defines `PREPROD_RUN_TARGET`, protocol-required dimensions, and available artifact roles, but does not establish R18's exact three-object tuple as the sole canonical minimum. Thus the claimed run-only BOUND path is still fixture-coupled to production prerequisites and rests on a material authority gap.
- High 4 — the claimed guard-before-dereference property is false. `supplied_ref_shape_invalid` records malformed `VersionedObjectRef`/digest bindings, but later separately evaluates `statement_ref.digest_binding.digest`, `statement_set_ref.digest_binding.digest`, `records_projection_ref.digest_binding.digest`, and PREPROD ref digests. A malformed canonical ref can therefore raise an untyped attribute error before coherent `INVALID > AMBIGUOUS > UNBOUND > BOUND` aggregation, rather than deterministically returning `INVALID`.
- High 5 — Task 7's retry-wide frozen-identity proof conflicts with legal superseded audit history. It validates every retained record and attempt, including `SUPERSEDED` old-revision records, against the current key's statement-set identity and one identical schema version before it filters current records by role. PI-300 requires superseded old revisions to remain auditable, while T72 must remain legal and retryable; the R18 predicate can reject precisely that retained old/new history. It also does not prove that every retained record owns at least one attempt, because only the flattened attempts are checked.
- Medium 1 — canonical-material validation remains materially incomplete despite the remediation claim. Visible checks do not compare contract versions to canonical object authority, do not fully validate statement-set/projection/PREPROD revision relationships, accept any nonempty anchor policy rather than the authorized policy identity/version, and only type-check `source_order_digest` instead of recomputing it from the ordered rule refs. Duplicate rule refs and exact uniqueness/partition invariants also remain underconstrained.
- Medium 2 — key-derived artifact path isolation lacks a fail-closed path-component contract. Both writer and retry append raw `key.canonical_key_digest.value` beneath `root`, but the displayed ports do not prove that value is a single validated lowercase-hex component, reject separators/absolute components, or resolve-and-check containment before mkdir/write. Distinct logical keys therefore do not yet statically prove no path escape or collision under the authorized root.
- non-regression boundary: this adjudication does not reopen the accepted R13–R18 local improvements, T96 immutable source identity, T101 literal reachability, leading-slash issue paths, producer-owned same-surface issue transport, explicit no-issue/reset behavior, raw-state-safe guards outside the findings above, fixed Task 10 ownership/accounting, F09-only/F08-identity-only scope, frozen F01–F12/F09 semantics, or production-default isolation. It modifies only this plan adjudication and the control ledger. No production code, test code, canonical PI-210/220/230/300 authority, JSON, YAML, mapping, or `handoff.md` is modified; no Python, pytest, collection, fenced snippet, CLI/PowerShell, Git, or GitHub operation is executed.
- required bounded remediation: a fresh role-separated `PI-570-R19` writer may modify only this plan and the control ledger. It must construct canonical feedback key digests from every PI-300-required input using one explicit deterministic serialization; compute prior/current protocol-target digests from their actual immutable target graphs; make PREPROD mechanically run-only and either cite existing canonical authority for its exact graph or avoid inventing a stronger closed tuple; make malformed canonical material branch to `INVALID` before every dereference; separate current retry identity from retained superseded audit history while requiring an attempt on every retained record; complete contract/revision/policy/order/uniqueness validation; and preflight the key directory as one validated contained digest component. All accepted non-regression and nonexecution boundaries remain mandatory.
- governance: `PI-570-R18=BLOCKED`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`; unique next legal action=`PI-570-R19` bounded plan-only remediation by a fresh writer. `PI-590-R18` is permanently unauthorized. Parseability, collection, runtime behavior, implementation conformance, PI-500 completion, and G5 completion remain unproven.

BLOCKED

## PI-570-R19 remediation record

- fixed adjudication boundary: this writer preserves the R18 parent adjudication at exactly `5 High + 2 Medium`. `PI-570-R18=BLOCKED`; no finding is deleted, downgraded, reclassified, or independently accepted.
- High 1 bounded static remediation: Task 10 now specifies one shared RFC8785/JCS canonical feedback-key serialization covering operation, full source digest, normalized nonblank unique item-ID/revision pairs, canonical target revisions including explicit nulls, approved policy ID/version, case, track, statement set or null, feedback ID, and full schema/contract digest identities. The top-level key fields must agree with serialized fields. T55, T56, T57, and T58 each mutate exactly one named input and require a changed lowercase sha256 key digest.
- High 2 bounded static remediation: prior/current target digests are freshly computed from each actual immutable protocol-specific graph after mutation. Production includes statement/set/records/selected RULE and selection metadata; PREPROD includes only run ID plus validated extensible run-artifact refs. Full versioned-ref identity is canonicalized, duplicate refs are rejected, authority-defined ordering is preserved, and stale `manifest.digest` reuse is forbidden.
- High 3 bounded static remediation: PREPROD branches before production-only guards, does not require or dereference a production statement, statement records, statement set, projection, anchor status, or RULE anchor, and always uses `record_anchor_ref=None` with statement/revision/set dimensions `NOT_APPLICABLE`. It requires only PI-230-supported run/artifact minimums, including a usable run snapshot, while allowing additional legitimate run refs; the unauthorized exact closed triple is withdrawn.
- High 4 bounded static remediation: Task 8 has a first-stage canonical-material guard that produces tagged validated refs. All malformed refs, digest bindings, revisions, contracts, or graph records enter `INVALID` before nested dereference; subsequent stages may access nested members only through validated refs. Valid absence remains `UNBOUND`, ambiguity remains `AMBIGUOUS`, and precedence remains `INVALID > AMBIGUOUS > UNBOUND > BOUND`.
- High 5 bounded static remediation: Task 7 validates each retained record's own nonempty coherent attempt chain, then separates non-superseded current identity from retained `SUPERSEDED` audit history. Historical revision/schema/key values are not forced to current values; superseded records are retained and never selected or rewritten. Current records alone match incoming identity, and every returned manifest digest is recomputed from the exact returned record set.
- Medium 1 bounded static remediation: canonical validation now covers object contract and revision relationships, statement/projection membership, approved configured policy ID/version, lossy selected-anchor scope, deterministic source-order digest recomputation, duplicate RULE/target-ref rejection, selected-anchor uniqueness, and exact ordered selected/non-anchor partition. R19 introduces no new policy literal or PREPROD closed business tuple.
- Medium 2 bounded static remediation: both artifact writer and retry must call one common preflight before mutation. It accepts only an RFC8785/JCS sha256 digest containing exactly one 64-character lowercase-hex path component, rejects separator/absolute/drive/UNC/dot forms, resolves root and candidate, and proves strict containment before `mkdir` or write.
- preserved non-regression boundaries: canonical `RULE` anchor; producer-owned operation receipt and current binder signature; T96 and T101; leading-slash issue paths; producer-owned issue transport; four Task 10 paths; five 104-item inventories; 31 component tests split `10/10/11`; F09-only/F08 identity-only; unchanged production-default behavior; and all previously accepted local improvements remain outside this remediation inventory.
- bounded scope and observed evidence: modified plan text is limited to Task 7, Task 8, Task 10, this R19 record, and the control ledger. No production/test code, authority document, JSON, YAML, mapping, or `handoff.md` is modified. No Python, pytest, collection, fenced snippet, CLI/PowerShell, Git, or GitHub operation is executed.
- residual unknowns: this is static plan-text closure only. Parseability, type checking, AST/accounting, collection, runtime branch reachability, implementation conformance, repository-wide diff, PI-500 completion, and G5 completion remain unproven. No `PASS`, parent acceptance, self-acceptance, or implementation authorization is claimed.
- governance: status=`READY_FOR_REVIEW`; remediator self-acceptance=`false`; `PI-570-R18=BLOCKED`; `PI-570-R19=READY_FOR_REVIEW`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`. Unique next action is fresh parent-instance static verification of R19. `PI-590-R19` remains unauthorized until parent acceptance.

READY_FOR_REVIEW

## PI-570-R19 parent static adjudication

- verdict: `BLOCKED`; parent acceptance=`false`; independent `PI-590-R19` is not authorized. The parent directly inspected the actual R19 Task 7 writer/retry/coordinator, Task 8 binder and validators, Task 10 feedback adapter, R19 remediation record, PI-300 policy authority, and the control ledger. The parent accepts only the bounded improvements literally visible in continuous source: retry now excludes `SUPERSEDED` records from incoming-current identity comparison and requires every retained record to own a nonempty coherent attempt chain; Task 7 writer/retry call one named operation-root preflight; Task 10 calls named canonical-key and target-graph digest helpers; and the prose correctly states the intended run-only PREPROD and validation boundaries. Those names and prose do not replace contradictory or missing mechanically copyable source.
- High 1 — Task 8's continuous binder still contradicts the R19 PREPROD and guard-first amendment. It unconditionally reads `statement_set.statements`, `statement_set.case_id`, and `statement_set.statement_set_id` after the interface permits `statement_set=None`; still restricts PREPROD to the exact ordered `RUN_SNAPSHOT`/`DECISION_RUN`/`FEEDBACK_ATTACHMENT` triple and cardinality three; and computes `supplied_ref_shape_invalid` before later directly dereferencing `.digest_binding.digest`. Therefore a legitimate run-only PREPROD input is not mechanically executable and malformed refs can still raise before coherent `INVALID > AMBIGUOUS > UNBOUND > BOUND` aggregation.
- High 2 — Task 10's continuous adapter does not implement its stated protocol-first branch. After assigning `target_statement=None` for PREPROD it still unconditionally builds `input_statement_set` containing that value, indexes the first manifest record, constructs production statement/set/records/`RULE`-anchor material, dereferences `target_statement`, and gates both protocols' records and aggregate oracle through production `anchor_status`. Comments saying that the complete block must be indented do not physically indent or replace it, so PREPROD remains production-dependent.
- High 3 — canonical feedback identity is still not mechanically closed. The plan calls `build_canonical_feedback_key()` and `normalize_feedback_item_revisions()` but contains no literal definitions for either helper. Moreover the displayed adapter creates one shared `normalized_item_revisions` and one shared policy version for prior/current keys; only source digest visibly differs. T55 revision-only, T56 policy-only, and T57 item-set-only mutations therefore have no displayed prior/current producer stimulus or observable key comparison, and the full PI-300 canonical-key claim remains future inference.
- High 4 — target-graph identity and mismatch evidence remain mechanically open. The plan calls undefined `digest_protocol_target_graph()` and `digest_ordered_rule_refs()` helpers; the displayed prior/current target-digest calls consume the same refs, run ID, policy, version, and source-order digest. No immutable prior target graph differs from the current graph, so same-key/different-target behavior cannot be observed from the displayed producer and the claimed fresh graph digest cannot be reviewed for canonical serialization, duplicate handling, or ordering.
- High 5 — Task 7 retry cannot satisfy its own missing-role/current-authority rule. Its interface receives no explicit current frozen input refs, schema authority, revision authority, or contract identity; it derives refs and schema from the first non-superseded current attempt/record and rejects the manifest when no current record exists. Thus a retained superseded-only history or a canonical partial set with no surviving current record cannot reconstruct a missing role without guessing history. `ArtifactRecord` and `ArtifactWriteAttempt` also expose no contract-version field against which the prose's record-local contract check can be performed.
- Medium 1 — the claimed complete canonical-material validation exists only in controlling prose and remains contradicted by continuous code. The binder still accepts any nonempty anchor policy, uses `fidelity="LOSSLESS"` and `fanout_scope="STATEMENT"` rather than the R19 `LOSSY`/`SELECTED_ANCHOR_ONLY` rule, trusts rather than recomputes `source_order_digest`, and does not literally close contract/revision/duplicate/selected-anchor partition checks. No tagged validated-ref type or guard implementation is displayed.
- Medium 2 — path and policy authority remain unresolved in executable plan text. `resolve_artifact_operation_root()` and `canonical_anchor_policy` have no literal definitions, while Task 10 introduces `PI300-FEEDBACK-ELIGIBILITY` for the key, later evaluates with `LEARN-POLICY-F09`, and PI-300's canonical positive policy is `PRODUCTION-STATEMENT-ELIGIBILITY` / `policy-v1`. Therefore containment preflight is an undefined call and one approved policy identity is not consistently bound through key, anchor selection, and eligibility.
- non-regression boundary: this adjudication does not reopen the accepted record-local attempt-chain improvement, exclusion of superseded history from current comparison, current binder call shape, canonical `RULE` anchor, producer-owned changed-source receipt, T96/T101, leading-slash issue paths, same-surface issue transport, Task 10 ownership/accounting, F09-only/F08-identity-only scope, frozen F01–F12/F09 semantics, or production-default isolation. It modifies only this plan adjudication and the control ledger. No production/test code, canonical authority, JSON, YAML, mapping, or `handoff.md` is modified; no Python, pytest, collection, fenced snippet, CLI/PowerShell, Git, or GitHub operation is executed.
- required bounded remediation: a fresh role-separated `PI-570-R20` writer may modify only this plan and the control ledger. It must replace—not merely supersede by prose—the contradictory Task 7/8/10 continuous blocks; provide literal mechanically copyable definitions for all new helpers; branch PREPROD before every production dereference; remove the exact closed PREPROD triple; implement tagged guard-before-dereference and complete canonical validation; provide real prior/current single-input mutations for T55–T58 and target-mismatch evidence; pass explicit current retry authority for missing-role reconstruction; and use one PI-300-authorized policy identity end to end. All accepted non-regression and nonexecution boundaries remain mandatory.
- governance: `PI-570-R19=BLOCKED`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`; unique next legal action=`PI-570-R20` bounded plan-only remediation by a fresh writer. `PI-590-R19` is permanently unauthorized. Parseability, collection, runtime behavior, implementation conformance, PI-500 completion, and G5 completion remain unproven.

BLOCKED

## PI-570-R20 remediation record

- fixed adjudication boundary: this writer preserves the immutable R19 parent adjudication at exactly `5 High + 2 Medium`. `PI-570-R19=BLOCKED`; no finding is reopened, deleted, downgraded, reclassified, or independently accepted.
- High 1 bounded static remediation: Task 8's continuous binder now branches by protocol before production-only statement/set/records/RULE work, accepts `statement_set=None` and empty production maps for PREPROD, validates raw refs into `ValidatedVersionedRef` before nested digest access, requires a usable `RUN_SNAPSHOT` in an extensible nonempty run-ref graph, and keeps `record_anchor_ref=None` for PREPROD. The public and implementation signatures now both make `statement_set_ref` nullable.
- High 2 bounded static remediation: Task 10 physically separates production and PREPROD construction. PREPROD builds only run artifact records/refs and its aggregate oracle uses a production-only anchor predicate; it does not read a production statement, statement set, `STATEMENT_RECORDS`, production maps, RULE anchor, or `anchor_status` as a PREPROD condition.
- High 3 bounded static remediation: literal `normalize_feedback_item_revisions()` and `build_canonical_feedback_key()` definitions serialize operation, case, track, feedback ID, full source/schema/contract digests, sorted unique item/revision pairs, nullable statement-set identity, and approved policy ID/version. T55 changes only target revision, T56 only policy version, T57 only canonical item set, and T58 only source digest against explicit prior baselines; every canonical-key change is a no-overwrite `NEW_OPERATION`, while source relation remains independently observable.
- High 4 bounded static remediation: literal `digest_ordered_rule_refs()` and `digest_protocol_target_graph()` definitions bind protocol, full ordered target refs, run ID, and, for production, the selected RULE's full identity plus full ordered selection graph, approved policy, recomputed source-order digest, fidelity, and fanout scope. Task 10 has a defined `target_graph_relation` stimulus that constructs genuinely different prior/current immutable graphs and observes same-key/different-target as `TARGET_MISMATCH` without overwrite.
- High 5 bounded static remediation: Task 7's public retry interface now exactly receives current frozen input refs, schema authority, statement-set/revision authority, and contract authority, matching the continuous implementation. Record-local historical attempts remain audit-visible, `SUPERSEDED` records are excluded from current selection, missing current roles use only explicitly supplied current authority, and the returned record-set digest is recomputed.
- Medium 1 bounded static remediation: production canonical validation now enforces the approved `PRODUCTION-STATEMENT-ELIGIBILITY` / `policy-v1` identity, required contracts/revisions, projection membership, ordered RULE uniqueness and partition, recomputed source-order digest, `LOSSY`, and `SELECTED_ANCHOR_ONLY`. The same approved policy identity is used by key construction, anchor selection, eligibility evaluation, baseline, mutators, and assertions.
- Medium 2 bounded static remediation: literal `resolve_artifact_operation_root()` rejects every non-lowercase-64-hex SHA-256 component, separator/absolute/drive/UNC/dot form, resolves candidate containment before mutation, and is used by writer/retry. Literal artifact-record canonicalization and digest helpers preserve changed-key directory isolation and exact returned-record identity.
- bounded scope and evidence: only this plan and the control ledger are modified. No production/test implementation, canonical PI-210/220/230/300 authority, JSON, YAML, mapping, `handoff.md`, runtime default, or F01–F12/F09 semantic boundary is changed. F08 remains identity-only.
- residual unknowns: this record reports static plan-text remediation only. Parseability, type checking, AST/accounting, test collection, runtime branch reachability, implementation conformance, repository-wide diff, PI-500 completion, and G5 completion remain unproven because no Python, pytest, fenced snippet, CLI/PowerShell, Git, or GitHub operation was executed.
- governance: status=`READY_FOR_REVIEW`; remediator self-acceptance=`false`; self-verification PASS=`false`; `PI-570-R19=BLOCKED`; `PI-570-R20=READY_FOR_REVIEW`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`. Unique next action is fresh parent-instance static verification of R20. `PI-590-R20` remains unauthorized until parent acceptance.

READY_FOR_REVIEW

## PI-570-R20 parent static adjudication

- verdict: `BLOCKED`; parent acceptance=`false`; independent `PI-590-R20` is not authorized. The parent directly inspected the actual R20 Task 7 path/digest/retry/coordinator block, Task 8 tagged-ref helpers/binder/validators, Task 10 key/target-graph helpers and feedback adapter, T55–T58 mutators, component-test surfaces, the R20 remediation record, and the control ledger. The parent accepts only the bounded improvements literally visible in continuous text: the missing helpers now have literal definitions; production and PREPROD branches are physically separated in the binder; nested digest access in that binder follows `validate_versioned_ref()` tagging; explicit current retry refs/schema/statement-set/contract arguments replace the former first-history guess; and the active positive anchor literal is `PRODUCTION-STATEMENT-ELIGIBILITY` / `policy-v1`.
- High 1 — Task 10's claimed run-only PREPROD construction is not authority-owned. It derives `canonical_case_id` with `next(record.case_id for record in run_result.manifest.records)`, then indexes `run_result.manifest.records[0]` and fabricates `RUN_SNAPSHOT` and `DECISION_RUN` records/refs by replacing that arbitrary first record. The PREPROD prerequisite checks only `manifest is not None`, not a nonempty authority-valid run-artifact graph. An empty manifest raises `StopIteration`/`IndexError`; a production artifact can be relabelled into run authority. This does not mechanically prove the required usable `RUN_SNAPSHOT` or an independently supplied run-only target graph.
- High 2 — Task 7 still contradicts its exact returned-record digest claim. Initial write failure computes a `RAW-UTF8` digest from concatenated artifact IDs, initial complete success computes a `RAW-UTF8` digest from concatenated observed digest strings, while retry success/failure uses the RFC8785-labelled full-record serializer. Thus equal returned record sets can have different manifest-digest semantics by branch, and the initial failure/success returns do not recompute the digest from the exact canonical returned record set through `digest_artifact_records()`.
- High 3 — approved policy identity is not end-to-end closed. T56 sets `fixture.policy_version="policy-v2"`; the current key and both eligibility evaluations consume that value, while the production `AnchorSelectionRecord` and binder require `policy-v1`. `evaluate_learning_eligibility()` accepts any nonempty policy ID/version and the component test explicitly expects a `policy-v2` eligibility record. Therefore the displayed plan both claims one approved PI-300 identity and exercises an unauthorized second active policy identity without a policy-authority transition.
- Medium 1 — production canonical contract authority remains presence-only rather than identity-equal. `validate_versioned_ref(... require_contract=True)` proves only a nonblank `contract_version`; the production checks never compare statement, statement-set, records, or RULE contract versions with their governing canonical contract identities. A graph with arbitrary nonempty contract literals can pass the claimed complete canonical validation.
- Medium 2 — the R20 component surfaces do not directly observe the claimed T55–T57 canonical-key changes. The target-revision, policy-version, and item-ID component tests assert only mutated submission or eligibility fields; unlike the target-mismatch component, they do not assert returned prior/current keys, changed canonical digests, `NEW_OPERATION`, or no-overwrite. The shared adapter contains a generic changed-key assertion, but the named leaf tests do not independently establish that each advertised single-axis stimulus reached and changed canonical operation identity.
- non-regression boundary: this adjudication does not reopen the accepted physical protocol branch, tagged binder dereference guard, literal helper presence, explicit retry call shape, selected `RULE` anchor, source-digest T58 receipt, target-mismatch branch, T72 superseded-history visibility, exact issue paths, issue transport, matrix ownership/accounting, F09-only/F08-identity-only scope, frozen F01–F12/F09 semantics, or production-default isolation. Static text cannot prove parseability, typing, AST accounting, collection, runtime behavior, implementation conformance, or test success.
- governance: `PI-570-R20=BLOCKED`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`; independent `PI-590-R20` is permanently unauthorized. Unique next legal action=`PI-570-R21` bounded plan-only remediation by a fresh role-separated writer. No production/test implementation, Python, pytest, fenced snippet, CLI/PowerShell, Git, GitHub mutation, or `handoff.md` synchronization is authorized.

BLOCKED

## PI-570-R21 remediation record

- fixed adjudication boundary: this writer preserves the immutable R20 parent adjudication at exactly `3 High + 2 Medium`. `PI-570-R20=BLOCKED`; no finding is reopened, deleted, downgraded, reclassified, or independently accepted.
- High 1 bounded static remediation: Task 10 PREPROD no longer derives case identity with `next()` or indexes/relabels an arbitrary manifest record. Its independent authority block constructs canonical PI-230 run `ArtifactRecord`/`ArtifactWriteAttempt` evidence, guards nonempty and well-formed authority records before use, requires a usable `RUN_SNAPSHOT`, retains additional legitimate run refs, and supplies no statement, statement-set, statement-records, RULE, or anchor-status dependency to the PREPROD graph.
- High 2 bounded static remediation: Task 7 initial failure, initial success, retry failure, and retry success now all call `digest_artifact_records()` over the exact returned record tuple. The contradictory initial `RAW-UTF8` artifact-ID and observed-digest concatenation branches were physically removed.
- High 3 bounded static remediation: active binding selection, current canonical key, both eligibility evaluations, validation, matrix assertions, and component observations are hard-locked to `PRODUCTION-STATEMENT-ELIGIBILITY` / `policy-v1`. T56 carries `policy-v2` only as explicit historical `prior_policy_version`; it cannot enter current anchor validation or active eligibility.
- Medium 1 bounded static remediation: the public Task 8 signature, continuous implementation, and Task 10 caller now carry explicit governing statement, statement-set, statement-records, and RULE contract authorities. Production validation compares every corresponding `contract_version` for identity equality after the existing shape/presence guard.
- Medium 2 bounded static remediation: `FeedbackPhaseObservation` exposes the producer-owned operation receipt. Each named T55/T56/T57 leaf test proves its fixture returns to baseline when its one axis is restored, then directly checks non-null prior/current keys, unequal canonical digests, `NEW_OPERATION`, and `overwrite_permitted is False`; T56 additionally proves active policy-v1 remains unchanged.
- preserved non-regression boundary: R20's accepted literal helpers, physical protocol split, tagged nested-digest guard, explicit retry authority parameters, active positive RULE/policy literal, T58 changed-source receipt, target-mismatch branch, T72 superseded audit history, exact issue paths, matrix ownership/accounting, F09-only/F08-identity-only scope, frozen F01–F12/F09 semantics, and production-default isolation remain unchanged outside these five findings.
- bounded scope and nonexecution: only this plan and the control ledger are modified. No production code, real test code, canonical PI-210/220/230/300 authority, JSON, YAML, mapping, `handoff.md`, runtime default, or F01–F12/F09 semantic boundary is changed. No Python, pytest, collection, fenced snippet, CLI/PowerShell, Git, or GitHub operation was executed.
- residual unknowns: this is static plan-text remediation only. Parseability, type checking, AST/accounting, collection, runtime branch reachability, implementation conformance, repository-wide diff, PI-500 completion, and G5 completion remain unproven. No `PASS`, parent acceptance, self-acceptance, or implementation authorization is claimed.
- governance: status=`READY_FOR_REVIEW`; remediator self-acceptance=`false`; self-verification PASS=`false`; `PI-570-R20=BLOCKED`; `PI-570-R21=READY_FOR_REVIEW`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`. Unique next action is fresh parent-instance static verification of R21. `PI-590-R21` is not authorized.

READY_FOR_REVIEW

## PI-570-R21 parent static adjudication

- verdict: `BLOCKED`; parent acceptance=`false`; independent `PI-590-R21` is permanently unauthorized. The parent directly inspected the R21 Task 7 write/retry return paths, Task 8 binder signature and production/PREPROD branches, Task 10 PREPROD construction/current-policy/caller/observation return path, T55–T57 leaf tests, the R21 remediation record, and the control ledger. The parent accepts only these bounded static improvements: all four artifact write/retry materialized return paths now use `digest_artifact_records()`; production refs compare four explicit governing contract identities; current key, anchor selection, and both eligibility calls use approved `PRODUCTION-STATEMENT-ELIGIBILITY` / `policy-v1`; T56 carries `policy-v2` only in a prior-key input.
- High 1 — PREPROD authority remains adapter-fabricated rather than supplied as an explicit authority-owned input graph. The adapter itself constructs fixed `ArtifactWriteAttempt`, `RUN_SNAPSHOT`, and `DECISION_RUN` objects, then replaces the production manifest with them. Its nonempty/type and usable-snapshot guards are tautological over that locally manufactured two-record tuple, so no caller-owned empty, malformed, or extensible authority graph can reach those guards. This closes arbitrary-first-record relabelling but does not close the fixed R20 requirement that PREPROD accept and validate an independently supplied nonempty authority-valid run-artifact graph.
- High 2 — the claimed producer-owned receipt observation is mechanically disconnected. `operation_result` was added to `ArtifactPhaseObservation`, not `FeedbackPhaseObservation`; the latter has no such field, and the final `FeedbackPhaseObservation(...)` return does not carry the local `operation_result`. T55–T57 then dereference `after.operation_result`, so their new receipt assertions cannot observe the producer result from the displayed continuous plan. R20 Medium 2 therefore remains open and the change introduces a direct mechanical-copyability failure.
- Medium 1 — the frozen fixture-field translation table still states that `feedback.policy_version` is supplied to `evaluate_learning_eligibility()`, while the displayed adapter now hard-codes both evaluator calls to `policy-v1` and uses the historical `prior_policy_version` only for the prior canonical key. The active path is correctly locked, but the controlling fixture contract now contradicts its implementation and leaves T56's one-axis semantics ambiguous.
- preserved findings: no R20 finding is deleted, downgraded, reclassified, or independently accepted. High 2 manifest digest, High 3 active-policy closure, and Medium 1 governing contract equality are accepted only as bounded static R21 improvements; High 1 and Medium 2 are not closed. No parseability, typing, AST/accounting, collection, runtime behavior, implementation conformance, PI-500 completion, or G5 completion is inferred.
- governance persisted fail-closed: `PI-570-R21=BLOCKED`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`; `PI-590-R21` is permanently unauthorized. The unique next legal action is a fresh role-separated `PI-570-R22` writer limited to these fixed `2 High + 1 Medium`: thread caller-owned PREPROD run authority records/refs through the fixture/public adapter and validate them before use; place and return `operation_result` on `FeedbackPhaseObservation`; align the fixture translation contract with prior-versus-current policy semantics. No production/test implementation, execution, Git, GitHub mutation, or `handoff.md` synchronization is authorized.

BLOCKED

## PI-570-R22 remediation record

- fixed adjudication boundary: this writer preserves the immutable R21 parent adjudication as `PI-570-R21=BLOCKED` with exactly `2 High + 1 Medium`. No finding is deleted, downgraded, reclassified, rejudged, or self-accepted.
- High 1 bounded plan repair: PREPROD authority evidence is caller-owned at both `FeedbackFixture` and the public `exercise_feedback_binding_phase()` boundary as independently supplied records and refs. The baseline caller owns only sample authority input; the adapter no longer constructs, replaces, relabels, or derives authority records from a production manifest. Empty, malformed, duplicate, record/ref-disagreeing, and extensible graphs can reach the public guard. The adapter checks tuple shape, nonemptiness, runtime identities, uniqueness, record/ref identity and digest agreement before nested ref use, requires at least one usable authority-backed `RUN_SNAPSHOT`, and then preserves every supplied legitimate ref. No PREPROD authority is inferred from or relabelled out of a production manifest.
- High 2 bounded plan repair: `operation_result` is removed from `ArtifactPhaseObservation` and declared on `FeedbackPhaseObservation`. Every feedback early return supplies `None`; the final feedback return supplies the local producer result returned by `validate_feedback_binding()`. T55–T57 leaf assertions therefore target the feedback observation's direct receipt surface rather than an artifact observation or adapter-reconstructed identity result.
- Medium 1 bounded plan repair: the fixture-field translation contract now fixes current policy to `PRODUCTION-STATEMENT-ELIGIBILITY` / `policy-v1` for current key, anchor selection, and every eligibility evaluation. `prior_policy_version` is used only in the prior canonical key; `policy_version` is a literal current-policy fixture invariant and is no longer described as a variable active-evaluator input.
- preserved non-regression boundary: R21's accepted exact returned-record digest helper usage, four governing production contract equalities, current active policy closure, prior/current canonical key and protocol-target digest helpers, tagged ref guard, selected `RULE` anchor, T58 receipt, T72 superseded audit history, same-surface issue transport, Task 10 ownership/accounting, F09-only/F08-identity-only scope, frozen F01–F12/F09 semantics, and production-default isolation remain unchanged outside the fixed R22 inventory.
- bounded scope and nonexecution: modifications are limited to this plan and the control ledger. No production or real test code, canonical authority, JSON, YAML, mapping, `handoff.md`, runtime default, or implementation artifact is modified. Python=`false`; pytest=`false`; collection=`false`; fenced-snippet execution=`false`; CLI/PowerShell=`false`; Git=`false`; GitHub mutation=`false`.
- static unknowns: parseability, typing, AST/accounting, collection, runtime branch reachability, implementation conformance, repository-wide diff, PI-500 completion, and G5 completion remain unproven. This writer performs no self-verification and makes no `PASS`, parent acceptance, implementation authorization, PI-500 completion, or G5 completion claim.
- governance: status=`READY_FOR_REVIEW`; remediator self-acceptance=`false`; self-verification PASS=`false`; `PI-570-R21=BLOCKED`; `PI-570-R22=READY_FOR_REVIEW`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`. The unique next action is fresh parent-instance static verification of R22. `PI-590-R22` is not authorized.

READY_FOR_REVIEW

## PI-570-R22 parent static adjudication

- verdict: `BLOCKED`; parent acceptance=`false`; independent `PI-590-R22` is permanently unauthorized. The parent directly inspected the R22 sole-copy imports, `FeedbackFixture`, both phase-observation types, every displayed feedback early return, the PREPROD branch, baseline authority records/refs, final receipt return, T55–T57 leaf assertions, PI-230 artifact-attempt authority, the R22 remediation record, and the control ledger. The parent accepts only these bounded static improvements: `operation_result` is now on and returned through `FeedbackPhaseObservation`; T55–T57 directly inspect that returned receipt; and the fixture translation contract now agrees with the fixed current `policy-v1` versus historical prior-policy semantics.
- High 1 — the sole-copy Task 10 module is not mechanically copyable: it constructs `ArtifactWriteAttempt` and annotates locals/fields with `FeedbackOperationResult`, but the displayed complete import block imports neither symbol. Static plan text cannot prove deferred annotations or an alternative hidden import, and the plan expressly forbids hidden dependencies.
- High 2 — caller ownership is still not closed as an authority-valid PI-230 graph. The adapter fixes PREPROD `canonical_case_id` to `CASE-F09-PREPROD-AUTHORITY` and `run_fact` to `RUN-F09-1` before examining the supplied records, rather than deriving and coherently validating common case/run identity from caller authority. A legitimate caller-owned graph with another coherent case/run identity is therefore rejected. In addition, the displayed baseline `ArtifactWriteAttempt` has `input_snapshot_refs=()`, contradicting PI-230's required nonempty list and this plan's own record-local nonempty-attempt-ref invariant; the public guard checks record/ref shape and selected fields but never validates each retained attempt chain. Thus the claimed positive authority fixture is not authority-valid and malformed attempt evidence can pass preflight.
- High 3 — malformed caller refs do not have a coherent fail-closed observation path. `validate_versioned_ref(...)` is evaluated in the PREPROD preflight before the later `try/except F09Error`; therefore a typed malformed revision/contract/digest ref can escape `exercise_feedback_binding_phase()` instead of returning the advertised `PREPROD_TARGET_GRAPH_INVALID` observation. The same pre-try region subsequently calls target-graph validation/digest logic, so the claim that malformed public inputs are guarded and returned as an observation is not mechanically established.
- preserved findings: no R21 finding is deleted, downgraded, reclassified, or independently accepted. R22 receipt transport and policy-contract alignment are accepted only as bounded static improvements; caller-owned PREPROD authority remains open. R21's earlier accepted exact-record digest and production governing-contract equality improvements remain unchanged. No parseability, typing, AST/accounting, collection, runtime behavior, implementation conformance, PI-500 completion, or G5 completion is inferred.
- governance persisted fail-closed: `PI-570-R22=BLOCKED`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`; `PI-590-R22` is permanently unauthorized. The unique next legal action is a fresh role-separated `PI-570-R23` writer limited to these fixed `3 High`: add the missing sole-copy imports; make PREPROD case/run identity authority-owned and validate complete PI-230 record-local attempt chains with a genuinely valid baseline; and move/catch all malformed-ref validation into a coherent observation-producing fail-closed boundary before any unsafe use. No production/test implementation, execution, Git, GitHub mutation, or `handoff.md` synchronization is authorized.

BLOCKED

## PI-570-R23 remediation record

- fixed adjudication boundary: this writer preserves the R22 parent verdict exactly as `PI-570-R22=BLOCKED` with exactly `3 High`. No finding is deleted, downgraded, reclassified, rejudged, or self-accepted; `PI-590-R22` remains permanently unauthorized.
- High 1 bounded plan repair: the sole continuous Task 10 copy source now explicitly imports both `ArtifactWriteAttempt` from `engine.f09.artifacts` and `FeedbackOperationResult` from `engine.f09.feedback`. The displayed constructors and annotations therefore have declared module-local symbols without hidden imports or deferred dependency assumptions.
- High 2 bounded plan repair: PREPROD case ID and run ID are derived only after validating the caller-supplied authority records as one nonempty coherent case/run/track graph; no adapter case/run constant decides authority. Every retained `ArtifactRecord` is checked for nonblank/type-correct PI-230 identity and locator fields, legal digest/state surfaces, a nonempty tuple of `ArtifactWriteAttempt`, unique artifact identity, and graph-wide case/run/track agreement. Every attempt is checked record-locally for nonblank identity/key, matching artifact ID, positive contiguous numbering, exact retry predecessor linkage, unique attempt ID, nonempty `VersionedObjectRef` input snapshots, legal times/outcome, and typed digest/error surfaces. The baseline now supplies one genuinely nonempty validated input snapshot ref to each record-local attempt. The target-ref map remains extensible: every additional legal caller ref is retained when the complete record/ref graph agrees.
- High 3 bounded plan repair: all caller authority and attempt `VersionedObjectRef` values are shape-guarded before nested use and then validated inside the public adapter's explicit `F09Error` boundary. Authority record digesting is inside the same boundary. Later protocol target mutation/digest construction has its own public-adapter `F09Error` boundary; PREPROD typed failures return one coherent `FeedbackPhaseObservation` with `PREPROD_TARGET_GRAPH_INVALID` rather than escaping. No authority ref or attempt ref reaches nested digest comparison, target-map construction, or protocol graph digesting before these guards.
- preserved non-regression boundary: R22 receipt transport and prior/current policy alignment, R21 exact returned-record digest and governing contract equality improvements, selected `RULE` anchor, T58 receipt, T72 superseded audit history, same-surface issue transport, Task 10 ownership/accounting, F09-only/F08-identity-only scope, frozen F01–F12/F09 semantics, and production-default isolation remain unchanged outside these fixed three repairs.
- bounded scope and nonexecution: modifications are limited to this plan and the control ledger. No production/test implementation, canonical authority, JSON, YAML, mapping, `handoff.md`, production default, or other repository artifact is modified. Python=`false`; pytest=`false`; collection=`false`; fenced-snippet execution=`false`; CLI/PowerShell=`false`; Git=`false`; GitHub mutation=`false`.
- static unknowns: parseability, typing, AST/accounting, collection, runtime reachability, implementation conformance, repository-wide diff, PI-500 completion, and G5 completion remain unproven. This writer performs no self-verification and makes no `PASS`, parent acceptance, implementation authorization, PI-500 completion, or G5 completion claim.
- governance: status=`READY_FOR_REVIEW`; remediator self-acceptance=`false`; self-verification PASS=`false`; `PI-570-R22=BLOCKED`; `PI-570-R23=READY_FOR_REVIEW`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`; `PI-590-R23` is unauthorized. The unique next action is fresh parent-instance static verification of R23.

READY_FOR_REVIEW

## PI-570-R23 parent static adjudication

- verdict: `BLOCKED`; parent acceptance=`false`; independent `PI-590-R23` is permanently unauthorized. The parent directly inspected the R23 sole-copy imports, complete PREPROD preflight, authority case/run/track derivation, record/ref and attempt-chain checks, target-digest exception boundary, baseline authority graph, PI-230 12.1 field authority, the R23 remediation record, and the control ledger. The parent accepts only these bounded static improvements: both missing imports are now explicit; case/run identity is derived from caller records rather than adapter constants; baseline attempts carry nonempty refs; and typed `F09Error` from the displayed ref validators is mapped to a feedback observation.
- High 1 — the claimed complete PI-230 authority validation remains mechanically incomplete. The preflight accepts any nonempty `artifact_role` string rather than the closed PI-230 artifact-role set, does not validate `issue_ids`, and treats typed `DigestRef` shells as sufficient without validating their required scalar fields. A caller can therefore supply a noncanonical role or malformed nested digest material, pair it with an equally fabricated matching ref, and pass the advertised record/ref authority check. This is not an authority-valid extensible run graph; extensibility permits additional legitimate PI-230 records, not new artifact-role semantics.
- High 2 — the coherent malformed-input boundary remains open to non-`F09Error` failures created by accepted malformed dataclass contents. `validate_versioned_ref()` checks truthiness rather than scalar field types, while the preflight likewise checks only outer `DigestRef` identity. `digest_artifact_records()` and later target-graph JSON serialization can consequently raise `TypeError` from malformed-but-truthy digest/ref fields; the new boundaries catch only `F09Error`. The public adapter therefore still does not guarantee the claimed `PREPROD_TARGET_GRAPH_INVALID` observation for malformed caller refs/records before nested serialization.
- Medium 1 — attempt-number validation is not type-closed: `attempt.attempt_number != attempt_index + 1` accepts booleans because `True == 1`, despite PI-230 requiring an integer and the remediation record claiming positive contiguous numbering. The same block does not enforce scalar type/nonnull coherence for every required attempt field beyond selected truthiness checks. This leaves the record-local attempt-chain claim mechanically broader than its authority.
- preserved findings: no R22 finding is deleted, downgraded, reclassified, or independently accepted. R23 imports, caller-derived case/run identity, nonempty baseline refs, and typed-`F09Error` observation routing are accepted only as bounded static improvements. R22 receipt transport and policy alignment plus R21 exact-record digest and governing-contract equality remain unchanged. No parseability, typing, AST/accounting, collection, runtime behavior, implementation conformance, PI-500 completion, or G5 completion is inferred.
- governance persisted fail-closed: `PI-570-R23=BLOCKED`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`; `PI-590-R23` is permanently unauthorized. The unique next legal action is a fresh role-separated `PI-570-R24` writer limited to these fixed `2 High + 1 Medium`: validate the complete closed PI-230 record/attempt/ref/digest scalar surface while retaining additional legitimate roles; guarantee all malformed caller-material serialization failures become one coherent feedback observation without masking production failures; and type-close integer/scalar attempt fields. No production/test implementation, execution, Git, GitHub mutation, or `handoff.md` synchronization is authorized.

BLOCKED

## PI-570-R24 remediation record

- fixed adjudication boundary: this writer preserves the R23 parent verdict exactly as `PI-570-R23=BLOCKED` with exactly `2 High + 1 Medium`. No R22/R23 finding is deleted, downgraded, reclassified, rejudged, or self-accepted; `PI-590-R23` remains permanently unauthorized.
- High 1 bounded plan repair: the sole continuous Task 10 copy source now validates caller-supplied PREPROD `ArtifactRecord` values against the exact closed PI-230 role set `REPORT | STATEMENT_INDEX | STATEMENT_RECORDS | RUN_SNAPSHOT | DECISION_RUN | FEEDBACK_ATTACHMENT | MANIFEST | FEEDBACK_SOURCE`, the eight authoritative states, every required scalar/nullable record field, tuple-typed string-only `issue_ids`, and complete nullable `DigestRef` scalar surfaces. The PREPROD `VersionedObjectRef.object_type` validator remains an unrestricted nonblank string and is not incorrectly narrowed to the ArtifactRecord role set. Every `DigestPresent` requires literal `PRESENT` plus a complete `DigestRef`; every digest algorithm, canonicalization, and value is a nonempty string before nested use.
- High 2 bounded plan repair: explicit PREPROD-only scalar guards now validate each caller authority ref and each attempt input ref, including all `VersionedObjectRef`, `DigestPresent`, and nested `DigestRef` scalar/type/nullability fields, before comparison, map/set construction, replacement, record digesting, or target-graph JSON serialization. The two PREPROD caller-material serialization boundaries map typed validation failures and caller-caused `TypeError`/`ValueError` to one coherent `PREPROD_TARGET_GRAPH_INVALID` `FeedbackPhaseObservation`; the production branch immediately re-raises the same exception classes and is not masked or reclassified.
- Medium bounded plan repair: every attempt now requires `attempt_number` to be an `int` but not `bool`, positive, and equal to its 1-based tuple position. The first `retry_of_attempt_id` is exactly `None`; every later value is a nonblank string exactly equal to the immediately preceding attempt ID. Attempt ID, artifact ID, idempotency key, input-ref tuple, timestamps, outcome, digest/error scalar/nullability, uniqueness, record ownership, successful-outcome evidence, and failed-outcome evidence are mechanically guarded in the sole-copy literal.
- preserved non-regression boundary: R22/R23 history and accepted local improvements remain unchanged. This remediation does not alter Task 6–8 production behavior, Task 10 ownership/accounting, T55–T58 semantics, selected `RULE` anchor, T72 history, F09-only/F08-identity-only scope, frozen F01–F12/F09 semantics, production-default isolation, or any authority document.
- bounded scope and nonexecution: modifications are limited to this plan and the control ledger. No production/test implementation, test artifact, canonical authority, JSON, YAML, mapping, `handoff.md`, production default, or other repository artifact is modified. Python=`false`; pytest=`false`; collection=`false`; fenced-snippet execution=`false`; CLI/PowerShell=`false`; Git=`false`; GitHub mutation=`false`.
- unproved surfaces: parseability, typing, AST/accounting, collection, runtime reachability, runtime behavior, serialization behavior under execution, implementation conformance, repository-wide diff, PI-500 completion, and G5 completion remain unproven. This writer performed no self-verification and makes no `PASS`, parent acceptance, implementation authorization, PI-500 completion, or G5 completion claim.
- governance: status=`READY_FOR_REVIEW`; writer self-acceptance=`false`; self-verification PASS=`false`; `PI-570-R23=BLOCKED`; `PI-570-R24=READY_FOR_REVIEW`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`; `PI-590-R24` is unauthorized. The unique next action is direct parent-instance static verification of R24; parent acceptance is not claimed.

READY_FOR_REVIEW

## PI-570-R24 parent static adjudication

- verdict: `ACCEPTED_FOR_INDEPENDENT_REVIEW`; parent acceptance=`true` for bounded plan-text completeness only. The parent directly inspected the actual R24 sole-copy helpers, complete PREPROD record/attempt/ref preflight, both serialization exception boundaries, target-graph construction, R24 remediation record, PI-230 12.1 authority, and the control ledger rather than relying on the writer summary.
- fixed High 1 closure accepted: `ArtifactRecord.artifact_role` is mechanically restricted to the exact eight-role PI-230 set; state is restricted to the exact eight-state set; required and nullable record fields, tuple/string `issue_ids`, and every nullable/non-null `DigestRef` shell plus algorithm/canonicalization/value scalar are explicitly guarded. `VersionedObjectRef.object_type` remains an unrestricted nonblank string rather than being incorrectly narrowed to artifact roles.
- fixed High 2 closure accepted: every caller-supplied PREPROD authority ref and every attempt input ref is fully shape/type/scalar guarded before map/set lookup, nested digest use, replacement, record digesting, or target-graph serialization. Initial record digesting catches only the bounded PREPROD caller-material `F09Error | TypeError | ValueError`; the later shared target-digest boundary converts those exception classes only when the selected protocol is PREPROD and immediately re-raises them for production. No production-path masking is accepted or inferred.
- fixed Medium closure accepted: `attempt_number` explicitly requires `int` and excludes `bool`, is positive, and equals its 1-based position; retry linkage is exactly `None` for the first attempt and a nonblank exact predecessor ID thereafter. Attempt identity/key/ownership, nonempty input refs, timestamps, outcome enum, nullable digest/error fields, per-record attempt-ID uniqueness, and displayed success/failure evidence coherence are mechanically guarded.
- bounded caveat: PI-230 12.1 itself does not prescribe additional cross-field semantics for `UNKNOWN`, blank prohibition for `issue_ids`, or datetime parsing beyond the declared datetime/string representation, so no invented authority is required for this acceptance. Parseability, typing, AST/accounting, collection, runtime behavior, serialization behavior under execution, implementation conformance, repository-wide completeness, PI-500 completion, and G5 completion remain unproven.
- governance: `PI-570-R24=ACCEPTED_FOR_INDEPENDENT_REVIEW`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`. This parent acceptance activates only a fresh role-separated `PI-590-R24` static independent review of the plan. It does not authorize implementation, execution, Git/GitHub operations, or `handoff.md` synchronization. The unique next legal action is that independent review.

ACCEPTED_FOR_INDEPENDENT_REVIEW

## PI-590-R24 independent static review

- verdict: `BLOCKED`; independent plan-text review=`failed`; High=`1`; Medium=`0`. The reviewer directly inspected the R23 parent adjudication, the actual R24 sole-copy import block and continuous PREPROD adapter, the record/ref/attempt preflight helpers, both exception boundaries, target-digest path, R24 remediation record and parent adjudication, PI-230 7.1 and 12.1 authority, and the control ledger. The bounded R24 scalar/nullability, open `object_type`, PREPROD exception-routing, and attempt-chain repairs are not rejected, but they cannot produce Gate PASS while the sole copy remains mechanically open.
- High 1 — the declared sole-copy module still has hidden import/symbol dependencies and therefore is not mechanically copyable. Its complete import block imports only `Callable` and `Literal` from `typing`, but the copied module evaluates multiple `Mapping[...]` annotations. It calls `digest_artifact_records()`, `validate_versioned_ref()`, `digest_protocol_target_graph()`, and `digest_ordered_rule_refs()` without importing or defining them inside the sole copy; `build_canonical_feedback_key()` likewise calls `_digest_ref_material()` without a local definition/import. It also constructs `DetectedIssue(...)` without importing that symbol in the sole-copy block. These are concrete symbol-resolution and copy-boundary contradictions, not parseability/runtime speculation, and directly falsify the no-hidden-dependency requirement stated immediately above the block.
- direct evidence: the sole-copy boundary begins at the import block and declares imports complete; the visible imports omit every symbol named above, while the same continuous block uses `Mapping` in feedback graph annotations, uses `_digest_ref_material()` in canonical-key serialization, uses the four digest/ref helpers in PREPROD preflight and target construction, and constructs `DetectedIssue` in the mismatch receipt assertion. The corresponding helper definitions exist only in other Task 7/8 fenced module sources, which the sole-copy instruction does not include and does not import. PI-230 authority itself remains unchanged: `VersionedObjectRef.object_type` is an open required string; R24's require-revision/require-contract caller path is preceded by scalar guards; the exact eight artifact roles/states and 12.1 record/attempt declared fields remain represented; no additional PI-230 rule is invented by this finding.
- fixed finding boundary: `PI590-R24-H-01` is the sole independent finding. No Medium, separate authority conflict, or R22/R23 semantic regression is asserted beyond this mechanical-copyability defect. Because any mechanical-copyability gap is blocking under the independent Gate, `PI-500` and `G5` remain blocked and may not be completed.
- unproved surfaces: parseability, annotation evaluation, imports at collection, typing, AST/accounting, test collection, runtime behavior, serialization behavior under execution, implementation conformance, repository-wide changed paths, PI-500 completion, and G5 completion remain unproven. This review ran no Python, pytest, collection, fenced snippet, YAML/mapping, CLI/PowerShell, Git, or GitHub operation and does not authorize implementation or `handoff.md` synchronization.
- governance: `PI-590-R24=BLOCKED`; `PI-570-R24` retains only its bounded parent acceptance history; `PI-500=BLOCKED`; `G5=IN_PROGRESS`. The unique next legal action is a fresh role-separated `PI-570-R25` bounded writer limited to this plan and the control ledger, repairing only `PI590-R24-H-01` by making the declared sole-copy module's imports/local definitions mechanically complete without changing accepted behavior or authority. The independent reviewer does not repair the finding.

BLOCKED

## PI-570-R25 remediation record

- fixed adjudication boundary: this writer directly accepts `PI-590-R24=BLOCKED` with exactly one High, `PI590-R24-H-01`, and zero Medium. No other finding, behavior, signature, test matrix, authority, R24 accepted semantic, F09 scope, or production-default boundary is reopened or changed.
- bounded mechanical repair: the declared sole-copy Task 10 module now imports `Mapping` from `typing`; imports the sole canonical `DetectedIssue` runtime identity from `engine.f09.contracts`; imports `digest_artifact_records` from its Task 7 public owner `engine.f09.artifacts`; and imports `validate_versioned_ref`, `digest_protocol_target_graph`, and `digest_ordered_rule_refs` from their Task 8 public owner `engine.f09.feedback`. The copy source no longer assumes visibility across fenced modules for those symbols.
- canonical serialization closure: the sole-copy module now contains the necessary minimal `_digest_ref_material(digest: DigestRef | None)` definition immediately before `build_canonical_feedback_key()`. It preserves the plan's existing canonical material shape `algorithm` / `canonicalization` / `value`, returns JSON `null` material for nullable digests, and changes no canonical-key inputs or behavior.
- same-finding boundary check: the directly visible hidden symbols named by `PI590-R24-H-01` are declared through explicit public imports or the minimal local digest-material helper. No production/test implementation, test matrix, signature, authority source, or unrelated helper is changed.
- bounded scope and nonexecution: modifications are limited to this plan and the control ledger. No production/test code, canonical authority, JSON, YAML, mapping, `handoff.md`, production default, or other repository artifact is modified. Python=`false`; pytest=`false`; collection=`false`; fenced-snippet execution=`false`; CLI/PowerShell=`false`; Git=`false`; GitHub mutation=`false`.
- unproved surfaces: parseability, annotation evaluation, import resolution at collection, typing, AST/accounting, test collection, runtime reachability, runtime behavior, serialization behavior under execution, implementation conformance, repository-wide changed paths, PI-500 completion, and G5 completion remain unproven.
- governance: status=`READY_FOR_REVIEW`; writer self-acceptance=`false`; self-verification PASS=`false`; `PI-590-R24=BLOCKED`; `PI-570-R25=READY_FOR_REVIEW`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`; `PI-590-R25` is unauthorized. The unique next action is direct parent-instance static verification of R25; parent acceptance is not claimed.

READY_FOR_REVIEW

## PI-570-R25 parent static adjudication

- verdict: `ACCEPTED_FOR_INDEPENDENT_REVIEW`; parent acceptance=`true` for the single fixed mechanical-copyability finding only. The parent directly inspected the declared sole-copy boundary, actual import block, each symbol named by `PI590-R24-H-01`, the local `_digest_ref_material()` definition and call surface, the corresponding Task 1/7/8 public-owner definitions/import precedent, R24/R25 records, and the control ledger rather than relying on the writer summary.
- fixed High closure accepted: `Mapping` is now imported from `typing`; canonical `DetectedIssue` is imported from `engine.f09.contracts`; `digest_artifact_records` is imported from `engine.f09.artifacts`; and `validate_versioned_ref`, `digest_protocol_target_graph`, and `digest_ordered_rule_refs` are imported from `engine.f09.feedback`. These module owners match the displayed Task 1/7/8 contract sources and remove the cross-fenced-block visibility assumption identified by the independent reviewer.
- local helper closure accepted: `_digest_ref_material(digest: DigestRef | None)` is defined inside the sole copy before use, returns `None` for nullable digests, and otherwise preserves the existing `algorithm` / `canonicalization` / `value` material shape. No canonical-key input, behavior, authority, signature, test matrix, R24 accepted semantic, F09 boundary, or production-default is changed by the displayed repair.
- bounded unknowns: this is static plan-text acceptance only. Parseability, annotation/import resolution, typing, AST/accounting, collection, runtime behavior, serialization execution, implementation conformance, repository-wide changed paths, PI-500 completion, and G5 completion remain unproven.
- governance: `PI-570-R25=ACCEPTED_FOR_INDEPENDENT_REVIEW`; `PI-500=BLOCKED`; `G5=IN_PROGRESS`. This activates only a fresh role-separated `PI-590-R25` independent static review; it does not authorize implementation, execution, Git/GitHub operations, completion, or `handoff.md` synchronization. The unique next legal action is that independent review.

ACCEPTED_FOR_INDEPENDENT_REVIEW

## PI-590-R25 independent static review

- verdict: `PASS`; independent plan-text review=`passed`; High=`0`; Medium=`0`; critical ambiguity=`0`; material evidence gap=`0`; mechanical-copyability gap=`0`; authority conflict=`0`; regression=`0`. The reviewer directly inspected the complete continuous Task 10 sole-copy boundary from its import block through `mutate_t104`, every use point named by fixed finding `PI590-R24-H-01`, the R25 imports and local digest-material helper, the displayed Task 1/7/8 owner definitions and import precedent, the R24/R25 remediation and adjudication records, relevant PI-230 authority, and the control ledger rather than relying on writer or parent summaries.
- direct evidence: the sole-copy import block imports `Mapping` from `typing`, the sole canonical `DetectedIssue` identity from `engine.f09.contracts`, `digest_artifact_records` from `engine.f09.artifacts`, and `validate_versioned_ref`, `digest_protocol_target_graph`, and `digest_ordered_rule_refs` from `engine.f09.feedback`. Task 1 defines `DetectedIssue` exactly once and requires downstream identity reuse; Task 7 displays `digest_artifact_records` as its public digest owner; Task 8 displays all three ref/graph helpers as public functions. Task 10 has no local competing declaration of those identities, and Tasks 1/7/8 do not import `tests.f09.conftest`, so the displayed dependency direction creates neither a conftest-to-owner cycle nor a runtime identity split.
- fixed finding closure: every named use is bound inside the sole-copy module: `Mapping[...]` annotations for feedback maps, `digest_artifact_records()` in PREPROD authority material, `validate_versioned_ref()` in PREPROD and target-graph validation, `digest_ordered_rule_refs()` in production anchor material, `digest_protocol_target_graph()` for prior/current target graphs, and `DetectedIssue(...)` in the mismatch receipt assertion. `_digest_ref_material(digest: DigestRef | None)` is locally defined before `build_canonical_feedback_key()` and all three calls; it returns `None` for an absent digest and otherwise emits exactly `algorithm`, `canonicalization`, and `value`, matching the existing Task 7 serializer shape and PI-230 `DigestRef` material. No same-class hidden symbol/import named by `PI590-R24-H-01` remains.
- non-regression: R25 is confined to explicit imports and the minimal local serializer helper. The continuous Task 10 behavior, signatures, 104-mutator matrix, accepted R24 PREPROD validation semantics, PI-230 authority, F09-only scope with F08 identity-only competition, and unchanged production-default boundary remain as displayed; no production/test implementation or execution is introduced.
- unproved surfaces: parseability, annotation/import resolution during collection, typing, AST/accounting, test collection, runtime reachability, runtime behavior, serialization behavior under execution, implementation conformance, repository-wide changed paths, PI-500 completion, and G5 completion remain unproven. This static review ran no Python, pytest, collection, fenced snippet, YAML/mapping, CLI/PowerShell, Git, or GitHub operation and does not authorize implementation or `handoff.md` synchronization.
- governance: `PI-590-R25=PASS_PENDING_PARENT_ACCEPTANCE`; awaiting parent acceptance. `PI-500=BLOCKED`; `G5=IN_PROGRESS`. This independent PASS does not itself complete PI-500/G5. The unique next legal action is direct parent-instance verification and acceptance of this PASS; only that parent may then decide the governed completion transition.

PASS_PENDING_PARENT_ACCEPTANCE

## PI-590-R25 parent acceptance and G5 closeout

- verdict: `ACCEPTED_PASS`; parent acceptance=`true`. The parent directly re-read the persisted independent review, the complete Task 10 sole-copy import boundary, the local `_digest_ref_material()` definition-before-use, the Task 1/7/8 public owners, the PI-590-R25 control-ledger row, and the then-current unique next action rather than accepting the reviewer summary as evidence.
- skeptical reconciliation: the actual sole copy explicitly binds `Mapping`, canonical `DetectedIssue`, `digest_artifact_records`, `validate_versioned_ref`, `digest_protocol_target_graph`, and `digest_ordered_rule_refs`; the nullable local serializer preserves the three-field digest material and precedes its calls. No competing declaration, reverse conftest owner import, cycle, runtime identity split, reopened authority, changed behavior/signature/matrix, F09 scope expansion, F08 implementation claim, or production-default change is visible in the accepted R25 delta.
- accepted Gate result: High=`0`; Medium=`0`; critical ambiguity=`0`; material evidence gap=`0`; mechanical-copyability gap=`0`; authority conflict=`0`; regression=`0`. The fixed `PI590-R24-H-01` is closed and the role-separated PI-590-R25 plan-text Gate is accepted.
- evidence boundary: this acceptance proves only that the approved F09 implementation plan is statically complete enough for the governed G5 plan Gate. Parseability, annotation/import resolution during collection, typing, AST/accounting, collection, runtime reachability, runtime behavior, serialization execution, implementation conformance, repository-wide changed paths, production readiness, deployment, and GitHub synchronization remain unproven. No production/test code, Python, pytest, collection, fenced snippet, YAML/mapping execution, CLI/PowerShell, Git, or GitHub operation occurred in this closeout.
- governance closeout: `PI-590-R25=COMPLETED`; `PI-500=COMPLETED`; `G5=COMPLETED`. This closes implementation-plan governance only and grants no production implementation, test execution, production-default change, local Git, or GitHub authority.

ACCEPTED_PASS

---

## PI-500-A1 — Task 5 retained-contract implementation amendment（2026-07-21）

### A1.1 优先级、来源与授权边界

本节是版本化 `PI-500-A1`，实施权威为 `PI-220-A1`，裁决来源为 2026-07-21 Task 5 保留合同裁决及对最保守 relation/status/OUTPUT 闭集的明确批准。它仅对 Task 5 authority binding、Gate conflict、`OUTPUT`，以及 Task 9/10 对新增 identity/port 的复用要求具有最高优先级；与既有 Task 5/9/10 文字冲突时以本节为准。此前 `PI-590-R25` 与 G5 closeout 仍是当时计划文本的历史事实，不证明本 amendment 已实施、测试或复核。

本次未来实现的 closed write set 恰为：

- `engine/f09/contracts.py`
- `engine/f09/decision.py`
- `tests/f09/conftest.py`
- `tests/f09/test_decision_contract.py`

任何其他路径变化立即 STOP。不得修改 PI-210、frozen sources、Task 9 application 文件或 Task 10 matrix/scenario 文件；不得新增 port/module/adapter/helper 来绕过 canonical identities。既有 `FrozenGateEvaluationBinding` 与 `get_gate_evaluation_binding()` 零语义变化。

### A1.2 canonical runtime identities 与输入图

`engine/f09/contracts.py` 是 `FrozenParticipationRoleBinding`、`FrozenRootTimingOutcomeBinding` 和 `NormalizedEvidenceReadPort` 的唯一 owner。两个 binding 的精确六字段 envelope、closed payload、state surfaces、RFC 8785 JCS/lowercase-sha256 摘要、source 摘要及失败语义逐字采用 `PI-220-A1`，不得在本计划另造变体。

Task 5 frozen evaluator-input graph 作以下最小版本化扩充：

```python
ParticipationAuthorityBindingId: TypeAlias = tuple[ParticipationRole, str]
RootTimingAuthorityBindingId: TypeAlias = tuple[str, str]

@dataclass(frozen=True)
class ParticipationInputState:
    role_ids: tuple[str, ...]
    role_authority_binding_ids: tuple[ParticipationAuthorityBindingId, ...]
    scenario_id: str

@dataclass(frozen=True)
class RootTimingInputState:
    root_state: str
    root_reason_code: str | None
    root_issue_path: str | None
    timing_state: str
    timing_reason_code: str | None
    timing_issue_path: str | None
    timing_rewrites_root: bool
    authority_binding_ids: tuple[RootTimingAuthorityBindingId, ...]
```

这两个新 tuple-pair aliases 只表达显式 input identity，不是 authority object。`role_authority_binding_ids` 必须与六个 canonical roles 构成全双射：恰六项、role 唯一、binding ID 非空且全局唯一；禁止位置配对。旧的 aggregate `reality_record_id`、`state_support_aligned`、`source_decision_ref` 从 `ParticipationInputState` 删除，禁止兼容读取或 fallback。

`authority_binding_ids` 是 `(candidate_id, binding_id)` 全双射：恰好覆盖 `DecisionInputState.candidate_ids`，两列分别唯一且非空；root/timing wrappers 中该 tuple 必须逐值相同，禁止按候选位置配对。既有 root/timing stimulus 字段只用于验证 ledger source 输入，绝不授权 check outcome；check 的 constraint ref、entry IDs、state、source decision、paths 和 reasons 全部来自 resolver binding。

`ParticipationRoleRecord` 和 `RootTimingConstraintCheck` 分别新增一个非空 `authority_binding_id` 字段；构造记录时必须逐值复制 authority payload 并验证 payload 内 record/check identity，不得从 ID 文本或其他输入重建。

### A1.3 同一 canonical port 的精确使用

`NormalizedEvidenceReadPort` 在既有 gate resolver 旁追加且只追加：

```python
def get_participation_role_binding(
    self,
    binding_id: str,
) -> FrozenParticipationRoleBinding: ...

def get_root_timing_outcome_binding(
    self,
    binding_id: str,
) -> FrozenRootTimingOutcomeBinding: ...
```

`evaluate_f09()` 保留现有单一 `normalized_evidence_port: NormalizedEvidenceReadPort` 参数；不得增加 participation/root/timing/source port 参数。调用顺序必须先确认 exact package、`validate_for_pi220(package_id) == READY` 和 contract integrity，再解析 gate/participation/root-timing bindings；任一 resolver 失败按 `PI-220-A1` fail closed，不能捕获后生成默认 record。

Task 9 的 `run_f09_slice()` 必须将同一个 canonical port instance 传给 evidence read 与 `evaluate_f09()`，并 import/reuse 两个 binding class identity；禁止 application wrapper port 或 dict reconstruction。Task 10 的 fixture/harness 必须直接 import/reuse Task 5 的 expanded input dataclasses、pair aliases、两个 binding class 和同一个 port protocol；不得有同名 test declarations、factory-generated authority、fake third port 或兼容旧 aggregate participation fields。Task 9/10 后续若需要改动，必须另开各自 closed write task；本 A1 不授权修改其文件。

### A1.4 Gate conflict 与 `OUTPUT` 实现条件

Gate conflict relation 只有同时通过以下 closed predicate 才可采纳：

```text
relation_type in {COUNTERS, COMPETES_WITH}
status in {ASSERTED, OBSERVED}
scope.function_id == F09
to_ref.object_type == EVIDENCE
to_ref.object_id in current_member.supporting_evidence_ids ∪ current_member.counterevidence_ids
from_ref.object_type == EVIDENCE
from_ref.object_id != to_ref.object_id
source_refs is nonempty
PI-210 validate_for_pi220(package_id) == READY
```

方向固定；反向、`CONTRADICTS`、`PROPOSED`、`DISPUTED`、null/非 F09 scope、其他 member endpoint、非 evidence endpoint、自环或空 source refs 全部 fail closed。Task 5 不解析 `source_refs`，而依赖成功 PI-210 referential integrity；禁止 source resolver。

`OUTPUT` validator 必须逐层验证：每个必要 gate record 是 `GateEvidenceState.SATISFIED`；每个 canonical participation role 有且只有一个独立 binding-backed record 且是 `SATISFIED`；每个 candidate 有且只有一个 binding-backed root/timing check 且是 `SATISFIED`。`NOT_APPLICABLE` 不满足 participation OUTPUT。Gate set/check set 的 `READY` 只表示结构完整，不得替代 record/check state。

### A1.5 RED falsifier matrix、命令与 reviewer gate

`tests/f09/test_decision_contract.py` 必须至少以独立测试冻结：

| Falsifier | 必须观察到的结果 |
|---|---|
| 任一新 binding ID 缺失、重复、空值、错误 runtime class | fail closed |
| 任一 closed payload 缺 key、多 key、错类型或 state surface 违规 | fail closed |
| payload 值/tuple 顺序改变但 canonical digest 未同步 | fail closed |
| immutable source 不存在、不不可变、locator/version/source digest 不匹配 | fail closed |
| role swap、共享 binding、共享 aggregate evidence、跨 role 借证 | fail closed |
| participation 旧 aggregate fields/fallback 被使用 | fail closed |
| constraint/check/candidate/root-entry/timing-entry swap | fail closed |
| `VIOLATED` 或 `UNKNOWN` 缺任一所需 path/reason | fail closed |
| evaluator 自行生成 source decision 或硬编码 `SATISFIED` | fail closed |
| relation type/status/scope/direction/endpoint/self-loop/source_refs 每轴单独非法 | fail closed |
| PI-210 integrity 是 `INVALID` 或 `BLOCKED` | fail closed before authority consumption |
| gate set `READY` 但任一 gate record 非 `SATISFIED` | `OUTPUT` rejected |
| 任一 participation role 为 `MISSING/CONFLICT/UNKNOWN/NOT_APPLICABLE` | `OUTPUT` rejected |
| 任一 root/timing check 为 `VIOLATED/UNKNOWN/NOT_APPLICABLE` | `OUTPUT` rejected |
| 六个合法独立 role bindings、合法 satisfied check bindings、合法 relations、逐 gate satisfied | authority surfaces 逐值保留且结构可通过；不证明业务结论正确 |

Focused 与 regression 命令保持原样，不得改写 selector：

```text
python -m pytest tests/f09/test_decision_contract.py -q
```

```text
python -m pytest tests/decision/test_staged_arbitration.py::test_old_and_staged_l6_can_run_side_by_side tests/application/test_staged_parallel_runner.py -q
```

本 CONTRACT REVISE 阶段不运行上述命令。未来 implementer 先执行 focused RED，修改仅限四文件，再执行 focused GREEN 与原 regression；任何 selector 无法收集、非白名单变化、第三 port、旧 aggregate fallback、source resolver、gate binding 语义变化或 production-default 变化均 STOP。

fresh independent reviewer 必须核对 exact class/Protocol runtime identity、六字段/closed payload、摘要重算、role/candidate 双射、resolver 失败分支、relation 每轴 predicate、逐记录 `OUTPUT`，并逐一实施上表 falsifiers；implementer 不得自评。永久禁止 GitHub 服务端变更。本 amendment 只完成合同收敛，不授权实现、测试、Git、GitHub、部署或 G5 再关闭。

CONTRACT_AMENDMENT_FROZEN
