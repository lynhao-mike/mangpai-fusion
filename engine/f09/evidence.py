import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from engine.f09.contracts import (
    AbsentDeclarationBinding,
    EvidenceTrack,
    FrozenDeclarationBinding,
    FrozenDeclarationRef,
    ImmutableJsonSourceBinding,
    IntegrityIssue,
    MarkdownContractSourceBinding,
    NotApplicableDeclarationBinding,
    ResolvedDeclarationBinding,
    RunTrack,
    SourceLocator,
    UnavailableDeclarationBinding,
    UnresolvableDeclarationBinding,
)
from engine.f09.errors import F09Error
from engine.f09.json_source import load_snapshot, resolve_snapshot_field
from engine.f09.markdown_source import resolve_markdown_frozen_field


IntegrityState = Literal["READY", "INVALID", "BLOCKED"]
TransformationKind = Literal["MDFF_V1_COPY", "LOSSLESS_COPY"]
GateMember = Literal["RESOURCE", "OBJECT", "ALLOCATION", "RISK", "ATTRIBUTION", "TENSE"]

_GATE_MEMBERS = frozenset(("RESOURCE", "OBJECT", "ALLOCATION", "RISK", "ATTRIBUTION", "TENSE"))

_MARKDOWN_SOURCE_ID = "SRC-F09-REALITY-HARD-GATE"
_MARKDOWN_SNAPSHOT_ID = "REAL-WORLD-FUNCTION-EVIDENCE-CARDS-V1-2026-07-19"
_MARKDOWN_SCHEMA = "markdown-source.commonmark-0.31.2-mdff-v1"
_MARKDOWN_CONTRACT = "real-world-function-evidence-cards-v1"
_MARKDOWN_CAPTURED_AT = "2026-07-19T00:00:00Z"
_MARKDOWN_DIGEST = "30ea0f8b8a91f95bc0a52ff90188740c2cc2282fcab27cd20be70404253d7a2f"
_MARKDOWN_REF = (
    "mdff:v1/heading/4.9%20F09%20%E8%B5%84%E6%9C%AC%E9%85%8D%E7%BD%AE"
    "%E4%B8%8E%E9%A3%8E%E9%99%A9%E6%89%BF%E6%8B%85/card/F09/item/"
    "%E7%8E%B0%E5%AE%9E%E7%A1%AC%E9%97%A8%E4%B8%8E%E5%8F%8C%E5%8D%A1"
)
_VALIDATION_PLAN_VALUE = (
    "资源、对象、配置轴、风险轴、归属和时态分别过门；单轴仅限定成立，双轴才是强主。"
    "状态证明基准日持续位置，事件证明指定窗口变化；S1–S3、E1–E3 与动作、资本、责任后果正交。"
)

_JSON_FIELDS = (
    ("SRCLOC-STATE-LEVEL", "SOURCE-STATE-1", "/value/level"),
    ("SRCLOC-STATE-POSITION", "SOURCE-STATE-1", "/value/position"),
    ("SRCLOC-STATE-AS-OF", "SOURCE-STATE-1", "/value/as_of"),
    ("SRCLOC-EVENT-LEVEL", "SOURCE-EVENT-1", "/value/level"),
    ("SRCLOC-EVENT-CHANGE", "SOURCE-EVENT-1", "/value/change"),
    ("SRCLOC-EVENT-START", "SOURCE-EVENT-1", "/value/interval/start"),
    ("SRCLOC-EVENT-END", "SOURCE-EVENT-1", "/value/interval/end"),
    ("SRCLOC-EVENT-START-INCLUSIVE", "SOURCE-EVENT-1", "/value/interval/start_inclusive"),
    ("SRCLOC-EVENT-END-INCLUSIVE", "SOURCE-EVENT-1", "/value/interval/end_inclusive"),
    ("SRCLOC-OUTCOME-AXIS", "SOURCE-OUTCOME-1", "/value/axis"),
    ("SRCLOC-OUTCOME-ACTION", "SOURCE-OUTCOME-1", "/value/action"),
    ("SRCLOC-OUTCOME-OBJECT", "SOURCE-OUTCOME-1", "/value/object"),
    ("SRCLOC-OUTCOME-TENSE", "SOURCE-OUTCOME-1", "/value/tense"),
)
_REALITY_TEMPORAL_SCOPES = {
    "SOURCE-STATE-1": "STATE_AS_OF",
    "SOURCE-EVENT-1": "EVENT_INTERVAL",
    "SOURCE-OUTCOME-1": "OUTCOME_CURRENT",
}
_GATE_MEMBERS_BY_SOURCE_ID: dict[str, tuple[GateMember, ...]] = {
    "SRCLOC-STATE-LEVEL": (),
    "SRCLOC-STATE-POSITION": ("RESOURCE", "ALLOCATION", "ATTRIBUTION"),
    "SRCLOC-STATE-AS-OF": ("TENSE",),
    "SRCLOC-EVENT-LEVEL": (),
    "SRCLOC-EVENT-CHANGE": ("ALLOCATION", "ATTRIBUTION"),
    "SRCLOC-EVENT-START": ("TENSE",),
    "SRCLOC-EVENT-END": ("TENSE",),
    "SRCLOC-EVENT-START-INCLUSIVE": ("TENSE",),
    "SRCLOC-EVENT-END-INCLUSIVE": ("TENSE",),
    "SRCLOC-OUTCOME-AXIS": ("ALLOCATION",),
    "SRCLOC-OUTCOME-ACTION": ("RESOURCE", "ALLOCATION"),
    "SRCLOC-OUTCOME-OBJECT": ("OBJECT",),
    "SRCLOC-OUTCOME-TENSE": ("TENSE",),
}
_DECLARATION_MEMBERS = (
    ResolvedDeclarationBinding,
    AbsentDeclarationBinding,
    NotApplicableDeclarationBinding,
    UnavailableDeclarationBinding,
    UnresolvableDeclarationBinding,
)


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    track: EvidenceTrack
    locator: SourceLocator
    value: object
    temporal_scope: str
    transformation: TransformationKind
    gate_members: tuple[GateMember, ...] = ()

    def __post_init__(self) -> None:
        if type(self.evidence_id) is not str or not self.evidence_id:
            raise ValueError("evidence_id must be a nonempty string")
        if not isinstance(self.track, EvidenceTrack):
            raise TypeError("track must be EvidenceTrack")
        if not isinstance(self.locator, SourceLocator):
            raise TypeError("locator must be SourceLocator")
        if type(self.temporal_scope) is not str or not self.temporal_scope:
            raise ValueError("temporal_scope must be a nonempty string")
        if self.transformation not in ("MDFF_V1_COPY", "LOSSLESS_COPY"):
            raise ValueError("invalid transformation")
        if type(self.gate_members) is not tuple or any(
            type(member) is not str or member not in _GATE_MEMBERS
            for member in self.gate_members
        ):
            raise TypeError("gate_members must be a tuple of closed gate members")
        if len(self.gate_members) != len(set(self.gate_members)):
            raise ValueError("gate_members must not contain duplicates")


@dataclass(frozen=True)
class DeclarationObservation:
    binding: FrozenDeclarationBinding
    value: object
    source_state: str

    def __post_init__(self) -> None:
        if not isinstance(self.binding, _DECLARATION_MEMBERS):
            raise TypeError("binding must be a closed FrozenDeclarationBinding member")
        if type(self.source_state) is not str or not self.source_state:
            raise ValueError("source_state must be a nonempty string")


@dataclass(frozen=True)
class NormalizedEvidencePackage:
    package_id: str
    case_id: str
    track: RunTrack
    records: tuple[EvidenceRecord, ...]
    validation_plan: DeclarationObservation
    output_precision: DeclarationObservation
    issues: tuple[IntegrityIssue, ...]
    integrity_state: IntegrityState

    def __post_init__(self) -> None:
        if type(self.package_id) is not str or not self.package_id:
            raise ValueError("package_id must be a nonempty string")
        if type(self.case_id) is not str or not self.case_id:
            raise ValueError("case_id must be a nonempty string")
        if not isinstance(self.track, RunTrack):
            raise TypeError("track must be RunTrack")
        if not isinstance(self.records, tuple) or not all(
            isinstance(record, EvidenceRecord) for record in self.records
        ):
            raise TypeError("records must be a tuple of EvidenceRecord")
        if not isinstance(self.validation_plan, DeclarationObservation):
            raise TypeError("validation_plan must be DeclarationObservation")
        if not isinstance(self.output_precision, DeclarationObservation):
            raise TypeError("output_precision must be DeclarationObservation")
        if not isinstance(self.issues, tuple) or not all(
            isinstance(issue, IntegrityIssue) for issue in self.issues
        ):
            raise TypeError("issues must be a tuple of IntegrityIssue")
        if self.integrity_state not in ("READY", "INVALID", "BLOCKED"):
            raise ValueError("invalid integrity_state")


def _markdown_binding() -> MarkdownContractSourceBinding:
    from engine.f09.contracts import DigestRef

    return MarkdownContractSourceBinding(
        binding_kind="MARKDOWN_CONTRACT",
        binding_schema_version="source-binding.markdown.v1",
        source_snapshot_id=_MARKDOWN_SNAPSHOT_ID,
        source_schema_version=_MARKDOWN_SCHEMA,
        contract_version=_MARKDOWN_CONTRACT,
        content_digest=DigestRef("sha256", "RAW-UTF8-NO-BOM-LF", _MARKDOWN_DIGEST),
        captured_at=_MARKDOWN_CAPTURED_AT,
    )


def _declaration(binding: MarkdownContractSourceBinding, kind: Literal["OUTPUT_PRECISION", "VALIDATION_PLAN"], suffix: str) -> ResolvedDeclarationBinding:
    return ResolvedDeclarationBinding(
        "RESOLVED",
        FrozenDeclarationRef(
            declaration_id=f"F09-{suffix}",
            declaration_type=kind,
            card_id="F09",
            contract_version=binding.contract_version,
            declaration_schema_version="declaration.v1",
            content_digest=binding.content_digest,
        ),
    )


def _reality_records(snapshot_path: Path) -> tuple[EvidenceRecord, ...]:
    snapshot = load_snapshot(snapshot_path)
    binding = ImmutableJsonSourceBinding(
        binding_kind="IMMUTABLE_JSON_SNAPSHOT",
        binding_schema_version="source-binding.immutable-json.v1",
        source_snapshot_id=snapshot.source_snapshot_id,
        source_schema_version=snapshot.snapshot_schema_version,
        contract_version=snapshot.contract_version,
        content_digest=snapshot.content_digest,
        captured_at=snapshot.captured_at,
    )
    observations = []
    for source_id, object_id, field_path in _JSON_FIELDS:
        locator = SourceLocator(
            source_id=source_id,
            source_type="INPUT_FIELD",
            path=str(snapshot_path),
            object_id=object_id,
            field_path=field_path,
            binding=binding,
        )
        observation = resolve_snapshot_field(snapshot, locator=locator)
        temporal_scope = _REALITY_TEMPORAL_SCOPES[object_id]
        observations.append(
            EvidenceRecord(
                evidence_id=source_id,
                track=EvidenceTrack.REALITY_FACT,
                locator=locator,
                value=observation.copied_value,
                temporal_scope=temporal_scope,
                transformation=observation.transformation,
                gate_members=_GATE_MEMBERS_BY_SOURCE_ID[source_id],
            )
        )
    return tuple(observations)


def _issue(issue_id: str, code: str, path: str, message: str) -> IntegrityIssue:
    return IntegrityIssue(issue_id, code, path, message, True)


def _declaration_state(
    observation: DeclarationObservation,
    *,
    declaration_type: Literal["OUTPUT_PRECISION", "VALIDATION_PLAN"],
) -> IntegrityState:
    binding = observation.binding
    if isinstance(binding, (UnavailableDeclarationBinding, UnresolvableDeclarationBinding)):
        return "BLOCKED"
    if isinstance(binding, (AbsentDeclarationBinding, NotApplicableDeclarationBinding)):
        return "INVALID"
    if not isinstance(binding, ResolvedDeclarationBinding):
        return "BLOCKED"
    suffix = (
        "output-precision"
        if declaration_type == "OUTPUT_PRECISION"
        else "validation-plan"
    )
    expected_binding = _declaration(_markdown_binding(), declaration_type, suffix)
    if binding != expected_binding:
        return "INVALID"
    if declaration_type == "OUTPUT_PRECISION":
        return (
            "READY"
            if observation.value is None
            and observation.source_state == "BOTH_NULL_AND_UNRESOLVED"
            else "INVALID"
        )
    return (
        "READY"
        if observation.value == _VALIDATION_PLAN_VALUE
        and observation.source_state == "RESOLVED"
        else "INVALID"
    )


def _json_values_equal(left: object, right: object) -> bool:
    left_type = type(left)
    right_type = type(right)
    if left_type is type(None) or right_type is type(None):
        return left is None and right is None
    if left_type is bool or right_type is bool:
        return left_type is bool and right_type is bool and left == right
    if left_type in (int, float) or right_type in (int, float):
        return (
            left_type in (int, float)
            and right_type in (int, float)
            and left == right
        )
    if left_type is str or right_type is str:
        return left_type is str and right_type is str and left == right
    if left_type is list or right_type is list:
        return (
            left_type is list
            and right_type is list
            and len(left) == len(right)
            and all(_json_values_equal(a, b) for a, b in zip(left, right))
        )
    if left_type is dict or right_type is dict:
        return (
            left_type is dict
            and right_type is dict
            and all(type(key) is str for key in left)
            and all(type(key) is str for key in right)
            and left.keys() == right.keys()
            and all(_json_values_equal(left[key], right[key]) for key in left)
        )
    return False


def _content_issues(package: NormalizedEvidencePackage) -> tuple[IntegrityIssue, ...]:
    issues = []
    ids = tuple(record.evidence_id for record in package.records)
    if len(ids) != len(set(ids)):
        issues.append(_issue("F09-EVIDENCE-DUPLICATE", "EVIDENCE_ID_DUPLICATE", "/records", "evidence IDs must be unique"))
    reality_coordinates = tuple(
        (
            record.evidence_id,
            record.locator.object_id,
            record.locator.field_path,
        )
        for record in package.records
        if record.track is EvidenceTrack.REALITY_FACT
    )
    if len(reality_coordinates) != len(_JSON_FIELDS) or set(
        reality_coordinates
    ) != set(_JSON_FIELDS):
        issues.append(
            _issue(
                "F09-REALITY-COMPLETENESS",
                "REALITY_RECORD_SET_INVALID",
                "/records",
                "reality records must exactly match the 13 frozen source fields",
            )
        )
    snapshots = {}
    for index, record in enumerate(package.records):
        if record.track is EvidenceTrack.REALITY_FACT:
            if not isinstance(record.locator.binding, ImmutableJsonSourceBinding):
                issues.append(_issue(f"F09-REALITY-SOURCE-{index}", "REALITY_SOURCE_NOT_IMMUTABLE", f"/records/{index}/locator/binding", "reality facts require immutable JSON"))
            else:
                try:
                    snapshot = snapshots.get(record.locator.path)
                    if snapshot is None:
                        snapshot = load_snapshot(Path(record.locator.path))
                        snapshots[record.locator.path] = snapshot
                    observation = resolve_snapshot_field(
                        snapshot,
                        locator=record.locator,
                    )
                    if (
                        record.transformation != observation.transformation
                        or not _json_values_equal(
                            record.value, observation.copied_value
                        )
                    ):
                        issues.append(
                            _issue(
                                f"F09-REALITY-COPY-{index}",
                                "REALITY_FROZEN_COPY_MISMATCH",
                                f"/records/{index}",
                                "reality locator, transformation, and value must match the frozen snapshot",
                            )
                        )
                except (F09Error, OSError, ValueError, TypeError):
                    issues.append(
                        _issue(
                            f"F09-REALITY-SOURCE-{index}",
                            "REALITY_SOURCE_UNRESOLVABLE",
                            f"/records/{index}/locator",
                            "reality source identity must resolve against its frozen snapshot",
                        )
                    )
            expected_scope = _REALITY_TEMPORAL_SCOPES.get(record.locator.object_id)
            if expected_scope is None or record.temporal_scope != expected_scope:
                issues.append(_issue(f"F09-REALITY-TEMPORAL-{index}", "REALITY_TEMPORAL_SCOPE_INVALID", f"/records/{index}/temporal_scope", "reality state, event, and outcome scopes are closed"))
            expected_members = _GATE_MEMBERS_BY_SOURCE_ID.get(record.evidence_id)
            if expected_members is None or record.gate_members != expected_members:
                issues.append(_issue(f"F09-REALITY-GATE-MEMBERS-{index}", "REALITY_GATE_MEMBERS_INVALID", f"/records/{index}/gate_members", "reality gate members must match the frozen locator semantics"))
    validation_state = _declaration_state(package.validation_plan, declaration_type="VALIDATION_PLAN")
    if validation_state != "READY":
        issues.append(_issue("F09-VALIDATION-PLAN", f"VALIDATION_PLAN_{validation_state}", "/validation_plan", "validation plan declaration is not consumable"))
    precision_state = _declaration_state(package.output_precision, declaration_type="OUTPUT_PRECISION")
    if precision_state != "READY":
        issues.append(_issue("F09-OUTPUT-PRECISION", f"OUTPUT_PRECISION_{precision_state}", "/output_precision", "F09 precision must be resolved null and unresolved"))
    return tuple(issues)


def build_f09_evidence_package(
    *,
    case_id: str,
    track: RunTrack,
    markdown_path: Path,
    snapshot_path: Path,
    chart_records: tuple[EvidenceRecord, ...],
    hypothesis_records: tuple[EvidenceRecord, ...],
) -> NormalizedEvidencePackage:
    if type(case_id) is not str or not case_id:
        raise ValueError("case_id must be a nonempty string")
    if not isinstance(track, RunTrack):
        raise TypeError("track must be RunTrack")
    if not isinstance(chart_records, tuple) or not isinstance(hypothesis_records, tuple):
        raise TypeError("record collections must be tuples")
    if any(record.track is not EvidenceTrack.CHART_STRUCTURE for record in chart_records):
        raise ValueError("chart_records must remain CHART_STRUCTURE")
    if any(record.track is not EvidenceTrack.UNVERIFIED_HYPOTHESIS for record in hypothesis_records):
        raise ValueError("hypothesis_records must remain UNVERIFIED_HYPOTHESIS")

    markdown_binding = _markdown_binding()
    markdown_locator = SourceLocator(
        source_id=_MARKDOWN_SOURCE_ID,
        source_type="FROZEN_CONTRACT_FIELD",
        path=str(markdown_path),
        object_id="F09",
        field_path=_MARKDOWN_REF,
        binding=markdown_binding,
    )
    validation_value = resolve_markdown_frozen_field(
        markdown_locator,
        _MARKDOWN_REF,
        expected_digest=markdown_binding.content_digest,
    ).copied_value
    if validation_value != _VALIDATION_PLAN_VALUE:
        raise ValueError("resolved validation plan does not match the frozen F09 declaration")
    validation_plan = DeclarationObservation(
        binding=_declaration(markdown_binding, "VALIDATION_PLAN", "validation-plan"),
        value=validation_value,
        source_state="RESOLVED",
    )
    output_precision = DeclarationObservation(
        binding=_declaration(markdown_binding, "OUTPUT_PRECISION", "output-precision"),
        value=None,
        source_state="BOTH_NULL_AND_UNRESOLVED",
    )
    records = chart_records + _reality_records(snapshot_path) + hypothesis_records
    identity = "|".join((case_id, track.value, *(record.evidence_id for record in records)))
    package = NormalizedEvidencePackage(
        package_id=f"F09-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:16]}",
        case_id=case_id,
        track=track,
        records=records,
        validation_plan=validation_plan,
        output_precision=output_precision,
        issues=(),
        integrity_state="READY",
    )
    issues = _content_issues(package)
    return NormalizedEvidencePackage(
        package_id=package.package_id,
        case_id=package.case_id,
        track=package.track,
        records=package.records,
        validation_plan=package.validation_plan,
        output_precision=package.output_precision,
        issues=issues,
        integrity_state="BLOCKED" if issues else "READY",
    )


def validate_for_pi220(package: NormalizedEvidencePackage) -> IntegrityState:
    if not isinstance(package, NormalizedEvidencePackage):
        raise TypeError("package must be NormalizedEvidencePackage")
    current_issues = _content_issues(package)
    declaration_states = (
        _declaration_state(package.validation_plan, declaration_type="VALIDATION_PLAN"),
        _declaration_state(package.output_precision, declaration_type="OUTPUT_PRECISION"),
    )
    if "BLOCKED" in declaration_states or current_issues or any(
        issue.blocking for issue in package.issues
    ):
        if "INVALID" in declaration_states and "BLOCKED" not in declaration_states and not any(
            issue.code.startswith(("REALITY_", "EVIDENCE_")) for issue in current_issues
        ):
            return "INVALID"
        return "BLOCKED"
    if "INVALID" in declaration_states or package.integrity_state == "INVALID":
        return "INVALID"
    if package.integrity_state == "BLOCKED":
        return "BLOCKED"
    return "READY"


def trace_to_sources(
    package: NormalizedEvidencePackage,
    object_id: str,
) -> tuple[SourceLocator, ...]:
    if not isinstance(package, NormalizedEvidencePackage):
        raise TypeError("package must be NormalizedEvidencePackage")
    if type(object_id) is not str or not object_id:
        raise ValueError("object_id must be a nonempty string")
    seen = set()
    locators = []
    for record in package.records:
        if object_id not in (record.evidence_id, record.locator.object_id):
            continue
        key = record.locator
        if key not in seen:
            seen.add(key)
            locators.append(record.locator)
    return tuple(locators)
