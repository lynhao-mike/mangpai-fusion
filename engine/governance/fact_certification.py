from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum, unique
from types import MappingProxyType
from typing import Final, Never, assert_never

from engine.governance.canonical import stable_object_id
from engine.governance.fact_values import DigestRef, FactLevel


_CERTIFICATION_SCHEMA: Final = "governance.fact-certification.v1"
_SCHOOLS: Final = frozenset(
    {"ziping", "gao_dechen", "duan_jianye", "yang_qingjuan", "ren_fuhong"}
)


@dataclass(frozen=True, slots=True)
class CertificationContractError(Exception):
    issue_code: str
    field_path: str
    diagnostic: str

    def __str__(self) -> str:
        return self.diagnostic


def _reject(issue_code: str, field_path: str, diagnostic: str) -> Never:
    raise CertificationContractError(issue_code, field_path, diagnostic)


@unique
class PublicationStatus(StrEnum):
    CANDIDATE = "candidate"
    PROPOSED = "proposed"
    PUBLISHED = "published"


@dataclass(frozen=True, slots=True)
class CertificationIdentity:
    fact_level: FactLevel
    fact_kind: str
    calculator_id: str
    calculator_version: str
    schema_version: str

    def __post_init__(self) -> None:
        if type(self.fact_level) is not FactLevel:
            _reject("CERTIFICATION.LEVEL", "certification_level", "invalid fact level")
        match self.fact_level:
            case FactLevel.CANONICAL_OBSERVATION:
                _reject(
                    "CERTIFICATION.LEVEL",
                    "certification_level",
                    "certifications must use L2A or L2B fact levels",
                )
            case FactLevel.CANDIDATE_DERIVED:
                _reject(
                    "CERTIFICATION.LEVEL",
                    "certification_level",
                    "certifications must use L2A or L2B fact levels",
                )
            case FactLevel.CERTIFIED_TECHNICAL:
                pass
            case FactLevel.CERTIFIED_CROSS_SCHOOL:
                pass
            case unreachable:
                assert_never(unreachable)
        for field_path, value in (
            ("fact_kind", self.fact_kind),
            ("calculator_id", self.calculator_id),
            ("calculator_version", self.calculator_version),
            ("schema_version", self.schema_version),
        ):
            if type(value) is not str or not value.strip():
                _reject(
                    "CERTIFICATION.TEXT_REQUIRED",
                    field_path,
                    f"{field_path} must be nonempty",
                )

    def material(self) -> tuple[str, str, str, str, str]:
        return (
            self.fact_level.value,
            self.fact_kind,
            self.calculator_id,
            self.calculator_version,
            self.schema_version,
        )


def _review_schools(refs: tuple[str, ...]) -> frozenset[str]:
    schools: set[str] = set()
    for ref in refs:
        parts = ref.split(":", maxsplit=2)
        if len(parts) != 3 or parts[0] != "review" or not parts[2].strip():
            _reject(
                "CERTIFICATION.CROSS_SCHOOL_REVIEW",
                "cross_school_review_refs",
                "review references must use review:<school>:<verifiable-reference>",
            )
        school = parts[1]
        if school not in _SCHOOLS:
            _reject(
                "CERTIFICATION.CROSS_SCHOOL_REVIEW",
                "cross_school_review_refs",
                "review references must name a canonical peer school",
            )
        schools.add(school)
    return frozenset(schools)


@dataclass(frozen=True, slots=True)
class FactCertification:
    registration_id: str
    identity: CertificationIdentity
    publication_status: PublicationStatus
    specification_digest: DigestRef
    cross_school_review_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.publication_status) is not PublicationStatus:
            _reject(
                "CERTIFICATION.STATUS",
                "publication_status",
                "invalid publication status",
            )
        if type(self.specification_digest) is not DigestRef:
            _reject("CERTIFICATION.DIGEST", "specification_digest", "invalid digest")
        refs = tuple(sorted(self.cross_school_review_refs))
        if len(refs) != len(set(refs)) or any(not ref.strip() for ref in refs):
            _reject(
                "CERTIFICATION.REVIEW_REFS",
                "cross_school_review_refs",
                "review refs must be unique nonempty strings",
            )
        expected_id = str(
            stable_object_id(
                "fact_certification",
                (self.identity.material(), self.publication_status.value, refs),
            )
        )
        if self.registration_id != expected_id:
            _reject(
                "CERTIFICATION.REGISTRATION_ID",
                "registration_id",
                "registration ID does not bind certification content",
            )
        match self.identity.fact_level:
            case FactLevel.CERTIFIED_TECHNICAL:
                if refs:
                    _reject(
                        "CERTIFICATION.L2A_REVIEWS",
                        "cross_school_review_refs",
                        "L2A cannot claim cross-school consensus",
                    )
            case FactLevel.CERTIFIED_CROSS_SCHOOL:
                if len(_review_schools(refs)) < 2:
                    _reject(
                        "CERTIFICATION.L2B_REVIEWS",
                        "cross_school_review_refs",
                        "L2B requires two distinct school reviews",
                    )
            case FactLevel.CANONICAL_OBSERVATION:
                _reject(
                    "CERTIFICATION.LEVEL",
                    "certification_level",
                    "invalid certification level",
                )
            case FactLevel.CANDIDATE_DERIVED:
                _reject(
                    "CERTIFICATION.LEVEL",
                    "certification_level",
                    "invalid certification level",
                )
            case unreachable:
                assert_never(unreachable)
        expected_digest = DigestRef.from_material(
            (
                _CERTIFICATION_SCHEMA,
                self.registration_id,
                *self.identity.material(),
                self.publication_status.value,
                refs,
            )
        )
        if self.specification_digest != expected_digest:
            _reject(
                "CERTIFICATION.DIGEST_MISMATCH",
                "specification_digest",
                "certification digest does not bind its content",
            )
        object.__setattr__(self, "cross_school_review_refs", refs)


@dataclass(frozen=True, slots=True)
class UnsupportedFactCertification:
    identity: CertificationIdentity
    issue_code: str = "CERTIFICATION.UNSUPPORTED"


@dataclass(frozen=True, slots=True)
class FactCertificationRegistry:
    registrations: tuple[FactCertification, ...]
    _published: MappingProxyType[CertificationIdentity, FactCertification] = field(
        init=False, repr=False
    )

    def __post_init__(self) -> None:
        if type(self.registrations) is not tuple:
            _reject(
                "CERTIFICATION.REGISTRY_TYPE",
                "certifications",
                "certifications must be a tuple",
            )
        registration_ids: set[str] = set()
        identities: set[CertificationIdentity] = set()
        published: dict[CertificationIdentity, FactCertification] = {}
        for registration in self.registrations:
            if type(registration) is not FactCertification:
                _reject(
                    "CERTIFICATION.ENTRY_TYPE",
                    "certifications",
                    "registry contains invalid entry",
                )
            if registration.registration_id in registration_ids:
                _reject(
                    "CERTIFICATION.DUPLICATE_ID",
                    "registration_id",
                    "duplicate registration ID",
                )
            if registration.identity in identities:
                _reject(
                    "CERTIFICATION.CONFLICTING_IDENTITY",
                    "certifications",
                    "same certification identity has different content",
                )
            registration_ids.add(registration.registration_id)
            identities.add(registration.identity)
            if registration.publication_status is PublicationStatus.PUBLISHED:
                published[registration.identity] = registration
        object.__setattr__(
            self,
            "registrations",
            tuple(sorted(self.registrations, key=lambda item: item.registration_id)),
        )
        object.__setattr__(self, "_published", MappingProxyType(published))

    def lookup(
        self, identity: CertificationIdentity
    ) -> FactCertification | UnsupportedFactCertification:
        certification = self._published.get(identity)
        if certification is None:
            return UnsupportedFactCertification(identity)
        return certification
