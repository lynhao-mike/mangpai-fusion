from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import Never

from engine.governance.arbitration_contracts import ClaimVariantRef
from engine.governance.fact_values import DigestRef, TemporalScope
from engine.governance.governance_claim import GovernanceClaim
from engine.governance.governance_claim_values import ClaimEvidenceGrade, ClaimKind


class CompositionContractError(Exception):
    def __init__(self, issue_code: str, field_path: str, diagnostic: str) -> None:
        self.issue_code = issue_code
        self.field_path = field_path
        self.diagnostic = diagnostic
        super().__init__(issue_code, field_path, diagnostic)

    def __str__(self) -> str:
        return f"{self.issue_code}: {self.diagnostic}"


def reject(issue_code: str, field_path: str, diagnostic: str) -> Never:
    raise CompositionContractError(issue_code, field_path, diagnostic)


@unique
class CompositionExecutionMode(StrEnum):
    SHADOW = "shadow"
    PRODUCTION = "production"


@unique
class CompositionOutcome(StrEnum):
    COMPOSED = "composed"
    CONDITIONAL = "conditional"
    CONFLICT = "conflict"
    HUMAN_REVIEW = "human_review"
    UNSUPPORTED = "unsupported"


def _scope_material(
    scope: TemporalScope | None,
) -> tuple[str, int | None, int | None, int | None] | None:
    if scope is None:
        return None
    if type(scope) is not TemporalScope:
        reject("COMPOSITION.OUTPUT_SCOPE", "output_scope", "invalid temporal scope")
    return (
        scope.layer.value,
        scope.dayun_start_year,
        scope.dayun_end_year,
        scope.target_year,
    )


def composition_result_digest(
    outcome: CompositionOutcome,
    template_id: str,
    template_version: str,
    components: tuple[GovernanceClaim, ...],
    output_kind: ClaimKind | None,
    output_scope: TemporalScope | None,
    evidence_grade: ClaimEvidenceGrade | None,
    issue_code: str | None,
) -> DigestRef:
    material = (
        "governance.composition.v1",
        outcome.value,
        template_id,
        template_version,
        tuple((claim.claim_id, claim.content_digest.value) for claim in components),
        output_kind.value if output_kind is not None else None,
        _scope_material(output_scope),
        evidence_grade.value if evidence_grade is not None else None,
        issue_code,
    )
    return DigestRef.from_material(material)


@dataclass(frozen=True, slots=True)
class CompositionResult:
    outcome: CompositionOutcome
    template_id: str
    template_version: str
    content_digest: DigestRef
    components: tuple[GovernanceClaim, ...]
    output_kind: ClaimKind | None
    output_scope: TemporalScope | None
    evidence_grade: ClaimEvidenceGrade | None
    issue_code: str | None

    def __post_init__(self) -> None:
        if type(self.outcome) is not CompositionOutcome:
            reject("COMPOSITION.OUTCOME", "outcome", "invalid outcome")
        if type(self.components) is not tuple or any(
            type(item) is not GovernanceClaim for item in self.components
        ):
            reject("COMPOSITION.COMPONENTS", "components", "must be immutable claims")
        if (
            tuple(
                sorted(
                    self.components,
                    key=lambda claim: (claim.claim_id, claim.content_digest.value),
                )
            )
            != self.components
        ):
            reject(
                "COMPOSITION.COMPONENT_ORDER",
                "components",
                "components must be canonical",
            )
        if type(self.content_digest) is not DigestRef:
            reject(
                "COMPOSITION.RESULT_DIGEST", "content_digest", "invalid result digest"
            )
        if type(self.template_id) is not str or not self.template_id:
            reject(
                "COMPOSITION.TEMPLATE_ID", "template_id", "template ID must be nonempty"
            )
        if type(self.template_version) is not str or not self.template_version:
            reject(
                "COMPOSITION.VERSION",
                "template_version",
                "template version must be nonempty",
            )
        if self.output_kind is not None and type(self.output_kind) is not ClaimKind:
            reject("COMPOSITION.OUTPUT_KIND", "output_kind", "invalid output kind")
        if (
            self.evidence_grade is not None
            and type(self.evidence_grade) is not ClaimEvidenceGrade
        ):
            reject(
                "COMPOSITION.EVIDENCE_GRADE", "evidence_grade", "invalid evidence grade"
            )
        if self.issue_code is not None and (
            type(self.issue_code) is not str or not self.issue_code
        ):
            reject("COMPOSITION.ISSUE", "issue_code", "invalid issue code")
        if self.outcome is CompositionOutcome.COMPOSED:
            if (
                self.output_kind is None
                or self.output_scope is None
                or self.evidence_grade is None
                or self.issue_code is not None
            ):
                reject(
                    "COMPOSITION.COMPOSED_FIELDS", "result", "composed fields required"
                )
        elif any(
            value is not None
            for value in (self.output_kind, self.output_scope, self.evidence_grade)
        ):
            reject(
                "COMPOSITION.NONCLAIM_FIELDS",
                "result",
                "non-claim cannot assert output",
            )
        if self.content_digest != composition_result_digest(
            self.outcome,
            self.template_id,
            self.template_version,
            self.components,
            self.output_kind,
            self.output_scope,
            self.evidence_grade,
            self.issue_code,
        ):
            reject(
                "COMPOSITION.RESULT_DIGEST", "content_digest", "result digest mismatch"
            )

    @property
    def component_variants(self) -> tuple[ClaimVariantRef, ...]:
        return tuple(ClaimVariantRef.from_claim(claim) for claim in self.components)

    @property
    def component_claim_ids(self) -> tuple[str, ...]:
        return tuple(claim.claim_id for claim in self.components)
