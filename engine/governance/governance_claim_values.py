from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import Never


class GovernanceClaimContractError(Exception):
    def __init__(self, issue_code: str, field_path: str, diagnostic: str) -> None:
        self.issue_code = issue_code
        self.field_path = field_path
        self.diagnostic = diagnostic
        super().__init__(issue_code, field_path, diagnostic)

    def __str__(self) -> str:
        return f"{self.issue_code}: {self.diagnostic}"


def reject(issue_code: str, field_path: str, diagnostic: str) -> Never:
    raise GovernanceClaimContractError(issue_code, field_path, diagnostic)


def require_text(field_path: str, value: str) -> str:
    if type(value) is not str or not value.strip():
        reject("CLAIM.TEXT_REQUIRED", field_path, f"{field_path} must be nonempty")
    return value


@dataclass(frozen=True, slots=True)
class AdapterProvenance:
    adapter_id: str
    adapter_version: str
    source_claim_ref: str

    def __post_init__(self) -> None:
        require_text("adapter_id", self.adapter_id)
        require_text("adapter_version", self.adapter_version)
        require_text("source_claim_ref", self.source_claim_ref)


@unique
class ClaimKind(StrEnum):
    STRUCTURE = "structure"
    EVENT = "event"
    TIMING = "timing"
    SUPPORT = "support"
    RISK = "risk"


@unique
class ClaimStance(StrEnum):
    SUPPORT = "support"
    OPPOSE = "oppose"
    CONDITIONAL = "conditional"
    ABSTAIN = "abstain"


@unique
class ClaimEvidenceGrade(StrEnum):
    DIRECT = "direct"
    CORROBORATED = "corroborated"
    INFERENTIAL = "inferential"


@unique
class ClaimReferenceCategory(StrEnum):
    FACT = "fact"
    CERTIFIED_FACT = "certified_fact"
    SCHOOL_REASON = "school_reason"
    SOURCE_RULE = "source_rule"


@unique
class ClaimIssueCode(StrEnum):
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    TEMPORAL_SCOPE_MISSING = "TEMPORAL_SCOPE_MISSING"
    LEGACY_CONDITIONAL_LOSS = "LEGACY_CONDITIONAL_LOSS"
    LEGACY_ABSTENTION_LOSS = "LEGACY_ABSTENTION_LOSS"
    UNSUPPORTED_LEGACY_CLAIM = "UNSUPPORTED_LEGACY_CLAIM"
    LEGACY_METADATA_INVALID = "LEGACY_METADATA_INVALID"
    LEGACY_REFERENCE_INVALID = "LEGACY_REFERENCE_INVALID"
    ADAPTER_INPUT_INVALID = "ADAPTER_INPUT_INVALID"
    LEGACY_ROLE_ABSTAIN = "LEGACY_ROLE_ABSTAIN"
    LEGACY_METADATA_UNAPPROVED = "LEGACY_METADATA_UNAPPROVED"
    LEGACY_CONTEXT_UNAPPROVED = "LEGACY_CONTEXT_UNAPPROVED"
    LEGACY_REFERENCE_REJECTED = "LEGACY_REFERENCE_REJECTED"
    LEGACY_CLAIM_REJECTED = "LEGACY_CLAIM_REJECTED"


@dataclass(frozen=True, slots=True)
class ClaimIssue:
    code: ClaimIssueCode
    detail: str

    def __post_init__(self) -> None:
        if type(self.code) is not ClaimIssueCode:
            reject("CLAIM.ISSUE_CODE", "code", "issue code must be closed")
        require_text("detail", self.detail)


@dataclass(frozen=True, slots=True)
class ClaimReference:
    category: ClaimReferenceCategory
    reference_id: str
    version: str

    def __post_init__(self) -> None:
        if type(self.category) is not ClaimReferenceCategory:
            reject("CLAIM.REFERENCE_CATEGORY", "category", "invalid reference category")
        require_text("reference_id", self.reference_id)
        require_text("version", self.version)


@dataclass(frozen=True, slots=True)
class ReferenceRegistration:
    category: ClaimReferenceCategory
    reference_id: str
    version: str

    def __post_init__(self) -> None:
        ClaimReference(self.category, self.reference_id, self.version)


@dataclass(frozen=True, slots=True)
class GovernanceReferenceCatalog:
    registrations: tuple[ReferenceRegistration, ...]

    def __post_init__(self) -> None:
        if type(self.registrations) is not tuple:
            reject("CLAIM.CATALOG_TYPE", "registrations", "catalog must use a tuple")
        if any(type(item) is not ReferenceRegistration for item in self.registrations):
            reject("CLAIM.CATALOG_ENTRY", "registrations", "invalid catalog entry")
        ordered = tuple(
            sorted(
                self.registrations,
                key=lambda item: (item.category.value, item.reference_id, item.version),
            )
        )
        if len(ordered) != len(set(ordered)):
            reject(
                "CLAIM.CATALOG_DUPLICATE", "registrations", "duplicate catalog entry"
            )
        object.__setattr__(self, "registrations", ordered)

    def validate(self, reference: ClaimReference) -> None:
        matching = tuple(
            item
            for item in self.registrations
            if item.category is reference.category
            and item.reference_id == reference.reference_id
        )
        if not matching:
            reject(
                "CLAIM.REFERENCE_UNKNOWN", "reference_id", "reference is unregistered"
            )
        if all(item.version != reference.version for item in matching):
            reject(
                "CLAIM.REFERENCE_VERSION",
                "version",
                "version is not registered exactly",
            )


def normalize_references(
    field_path: str,
    references: tuple[ClaimReference, ...],
    expected: ClaimReferenceCategory | None = None,
) -> tuple[ClaimReference, ...]:
    if type(references) is not tuple:
        reject("CLAIM.REFERENCE_TYPE", field_path, "references must use tuples")
    if any(type(item) is not ClaimReference for item in references):
        reject("CLAIM.REFERENCE_ENTRY", field_path, "invalid claim reference")
    if expected is not None and any(
        item.category is not expected for item in references
    ):
        reject(
            "CLAIM.REFERENCE_CATEGORY",
            field_path,
            "reference category does not match field",
        )
    return tuple(
        sorted(
            set(references),
            key=lambda item: (item.category.value, item.reference_id, item.version),
        )
    )


def normalize_issues(issues: tuple[ClaimIssue, ...]) -> tuple[ClaimIssue, ...]:
    if type(issues) is not tuple or any(
        type(item) is not ClaimIssue for item in issues
    ):
        reject("CLAIM.ISSUE_TYPE", "blockers", "blockers must be typed issues")
    return tuple(sorted(set(issues), key=lambda item: (item.code.value, item.detail)))
