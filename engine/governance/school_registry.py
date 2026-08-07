from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import Final, Never, assert_never

from engine.governance.fact_certification import PublicationStatus
from engine.governance.governance_claim_values import ClaimEvidenceGrade, ClaimKind


PEER_SCHOOL_IDS: Final = (
    "ziping",
    "gao_dechen",
    "duan_jianye",
    "yang_qingjuan",
    "ren_fuhong",
)
_SCHOOL_ALIASES: Final = (
    ("gao", "gao_dechen"),
    ("duan", "duan_jianye"),
    ("yang", "yang_qingjuan"),
    ("ren", "ren_fuhong"),
)


@dataclass(frozen=True, slots=True)
class SchoolRegistryContractError(Exception):
    issue_code: str
    field_path: str
    diagnostic: str

    def __str__(self) -> str:
        return f"{self.issue_code}: {self.diagnostic}"


def _reject(issue_code: str, field_path: str, diagnostic: str) -> Never:
    raise SchoolRegistryContractError(issue_code, field_path, diagnostic)


def _text(field_path: str, value: str) -> str:
    if type(value) is not str or not value.strip():
        _reject("SCHOOL.TEXT_REQUIRED", field_path, f"{field_path} must be nonempty")
    return value


def _peer_school_id(field_path: str, school_id: str) -> str:
    _text(field_path, school_id)
    if school_id not in PEER_SCHOOL_IDS:
        _reject(
            "SCHOOL.CANONICAL_ID",
            field_path,
            "school ID must be an exact canonical peer ID",
        )
    return school_id


def normalize_school_input(raw_school_id: str) -> str:
    _text("school_id", raw_school_id)
    for alias, canonical in _SCHOOL_ALIASES:
        if raw_school_id == alias:
            return canonical
    if raw_school_id in PEER_SCHOOL_IDS:
        return raw_school_id
    _reject(
        "SCHOOL.INPUT_UNKNOWN", "school_id", f"unknown input school: {raw_school_id}"
    )


@unique
class CapabilityRole(StrEnum):
    LEAD = "lead"
    CO_LEAD = "co_lead"
    EVIDENCE_ONLY = "evidence_only"
    ABSTAIN = "abstain"


@unique
class SchoolRegistryIssueCode(StrEnum):
    UNKNOWN_SCHOOL = "SCHOOL.UNKNOWN"
    UNREGISTERED_CAPABILITY = "CAPABILITY.UNREGISTERED"
    UNPUBLISHED_CAPABILITY = "CAPABILITY.UNPUBLISHED"


@dataclass(frozen=True, slots=True)
class RegistryIssue:
    code: SchoolRegistryIssueCode
    detail: str

    def __post_init__(self) -> None:
        if type(self.code) is not SchoolRegistryIssueCode:
            _reject("SCHOOL.ISSUE_CODE", "code", "issue code must be closed")
        _text("detail", self.detail)


@dataclass(frozen=True, slots=True)
class PeerSchool:
    school_id: str

    def __post_init__(self) -> None:
        _peer_school_id("school_id", self.school_id)


@dataclass(frozen=True, slots=True)
class LegacyCompatibilitySource:
    source_id: str
    compatibility_status: str = "legacy_compatibility_source"

    def __post_init__(self) -> None:
        if self.source_id != "ditiansui":
            _reject("SCHOOL.LEGACY_SOURCE", "source_id", "only Ditiansui is approved")
        if self.compatibility_status != "legacy_compatibility_source":
            _reject("SCHOOL.LEGACY_STATUS", "compatibility_status", "status is fixed")


@dataclass(frozen=True, slots=True)
class UnknownSchool:
    requested_id: str
    issue_code: SchoolRegistryIssueCode = SchoolRegistryIssueCode.UNKNOWN_SCHOOL


@dataclass(frozen=True, slots=True)
class CapabilityIdentity:
    school_id: str
    task_id: str
    claim_kind: ClaimKind
    evidence_grade: ClaimEvidenceGrade
    version: str

    def __post_init__(self) -> None:
        _peer_school_id("school_id", self.school_id)
        _text("task_id", self.task_id)
        _text("version", self.version)
        if type(self.claim_kind) is not ClaimKind:
            _reject("CAPABILITY.CLAIM_KIND", "claim_kind", "claim kind must be closed")
        if type(self.evidence_grade) is not ClaimEvidenceGrade:
            _reject(
                "CAPABILITY.EVIDENCE_GRADE", "evidence_grade", "grade must be closed"
            )


@dataclass(frozen=True, slots=True)
class CapabilityRegistration:
    identity: CapabilityIdentity
    role: CapabilityRole
    publication_status: PublicationStatus

    def __post_init__(self) -> None:
        if type(self.identity) is not CapabilityIdentity:
            _reject("CAPABILITY.IDENTITY", "identity", "identity is required")
        if type(self.role) is not CapabilityRole or self.role is CapabilityRole.ABSTAIN:
            _reject("CAPABILITY.ROLE", "role", "role must be a non-abstain closed role")
        if type(self.publication_status) is not PublicationStatus:
            _reject(
                "CAPABILITY.PUBLICATION_STATUS",
                "publication_status",
                "status is closed",
            )


@dataclass(frozen=True, slots=True)
class CapabilityQualification:
    identity: CapabilityIdentity
    role: CapabilityRole
    source: str = "school_registry"

    @property
    def winner_eligible(self) -> bool:
        match self.role:
            case CapabilityRole.LEAD | CapabilityRole.CO_LEAD:
                return True
            case CapabilityRole.EVIDENCE_ONLY | CapabilityRole.ABSTAIN:
                return False
            case unreachable:
                assert_never(unreachable)


@dataclass(frozen=True, slots=True)
class CapabilityAbstention:
    identity: CapabilityIdentity
    reason_issue: RegistryIssue
    source: str = "school_registry"
    role: CapabilityRole = CapabilityRole.ABSTAIN


CapabilityQueryResult = CapabilityQualification | CapabilityAbstention
SchoolQueryResult = PeerSchool | LegacyCompatibilitySource | UnknownSchool


@dataclass(frozen=True, slots=True)
class SchoolRegistry:
    peer_schools: tuple[PeerSchool, ...]
    legacy_compatibility_sources: tuple[LegacyCompatibilitySource, ...]
    capabilities: tuple[CapabilityRegistration, ...]

    def __post_init__(self) -> None:
        if type(self.peer_schools) is not tuple or any(
            type(x) is not PeerSchool for x in self.peer_schools
        ):
            _reject(
                "SCHOOL.REGISTRY_TYPE", "peer_schools", "peer schools must be a tuple"
            )
        if tuple(item.school_id for item in self.peer_schools) != PEER_SCHOOL_IDS:
            _reject("SCHOOL.PEER_SET", "peer_schools", "peer set is fixed")
        if self.legacy_compatibility_sources != (
            LegacyCompatibilitySource("ditiansui"),
        ):
            _reject(
                "SCHOOL.LEGACY_SET",
                "legacy_compatibility_sources",
                "legacy set is fixed",
            )
        if type(self.capabilities) is not tuple or any(
            type(x) is not CapabilityRegistration for x in self.capabilities
        ):
            _reject(
                "CAPABILITY.REGISTRY_TYPE",
                "capabilities",
                "capabilities must be a tuple",
            )
        identities = tuple(item.identity for item in self.capabilities)
        if len(identities) != len(set(identities)):
            _reject(
                "CAPABILITY.DUPLICATE_IDENTITY",
                "capabilities",
                "identities must be unique",
            )
        object.__setattr__(
            self,
            "capabilities",
            tuple(
                sorted(
                    self.capabilities,
                    key=lambda x: (
                        x.identity.school_id,
                        x.identity.task_id,
                        x.identity.claim_kind.value,
                        x.identity.evidence_grade.value,
                        x.identity.version,
                    ),
                )
            ),
        )

    @property
    def peer_school_ids(self) -> tuple[str, ...]:
        return tuple(item.school_id for item in self.peer_schools)

    def lookup_school(self, school_id: str) -> SchoolQueryResult:
        _text("school_id", school_id)
        if school_id in PEER_SCHOOL_IDS:
            return self.peer_schools[PEER_SCHOOL_IDS.index(school_id)]
        if school_id == "ditiansui":
            return self.legacy_compatibility_sources[0]
        return UnknownSchool(school_id)

    def lookup_capability(self, identity: CapabilityIdentity) -> CapabilityQueryResult:
        if type(identity) is not CapabilityIdentity:
            _reject("CAPABILITY.IDENTITY", "identity", "identity is required")
        for registration in self.capabilities:
            if registration.identity == identity:
                match registration.publication_status:
                    case PublicationStatus.PUBLISHED:
                        return CapabilityQualification(identity, registration.role)
                    case PublicationStatus.CANDIDATE | PublicationStatus.PROPOSED:
                        return CapabilityAbstention(
                            identity,
                            RegistryIssue(
                                SchoolRegistryIssueCode.UNPUBLISHED_CAPABILITY,
                                "capability is not published",
                            ),
                        )
                    case unreachable:
                        assert_never(unreachable)
        return CapabilityAbstention(
            identity,
            RegistryIssue(
                SchoolRegistryIssueCode.UNREGISTERED_CAPABILITY,
                "no exact five-dimensional published capability exists",
            ),
        )
