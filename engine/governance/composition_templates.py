from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique

from engine.governance.composition_contracts import reject
from engine.governance.fact_values import DigestRef, TemporalLayer
from engine.governance.governance_claim_values import (
    ClaimEvidenceGrade,
    ClaimKind,
    ClaimStance,
)


_CLOSED_HUMAN_REVIEW_CONDITIONS = frozenset({"strong_contradiction"})


@unique
class CompositionTemplateStatus(StrEnum):
    SYNTHETIC_ONLY = "synthetic_only"
    PUBLISHED = "published"


@dataclass(frozen=True, slots=True)
class RequiredComponentSlot:
    slot_id: str
    count: int

    def __post_init__(self) -> None:
        if type(self.slot_id) is not str or not self.slot_id.strip():
            reject("COMPOSITION.SLOT_ID", "slot_id", "slot ID must be nonempty")
        if self.slot_id != "independent_support":
            reject("COMPOSITION.SLOT_ID", "slot_id", "unsupported component slot")
        if type(self.count) is not int or self.count < 1:
            reject("COMPOSITION.SLOT_COUNT", "count", "slot count must be positive")


@dataclass(frozen=True, slots=True)
class CompositionTemplate:
    template_id: str
    version: str
    accepted_claim_kinds: tuple[ClaimKind, ...]
    accepted_stances: tuple[str, ...]
    accepted_task_ids: tuple[str, ...]
    accepted_temporal_layers: tuple[str, ...]
    required_component_slots: tuple[RequiredComponentSlot, ...]
    output_kind: ClaimKind
    event_scope_rule: str
    temporal_rule: str
    evidence_cap: ClaimEvidenceGrade
    preserve_counterevidence: bool
    preserve_falsifier: bool
    human_review_conditions: tuple[str, ...]
    status: CompositionTemplateStatus
    specification_digest: DigestRef

    def __post_init__(self) -> None:
        if type(self.template_id) is not str or not self.template_id.strip():
            reject(
                "COMPOSITION.TEMPLATE_ID", "template_id", "template ID must be nonempty"
            )
        if type(self.version) is not str or not self.version.strip():
            reject(
                "COMPOSITION.VERSION", "version", "template version must be nonempty"
            )
        if (
            type(self.accepted_claim_kinds) is not tuple
            or not self.accepted_claim_kinds
        ):
            reject(
                "COMPOSITION.CLAIM_KINDS",
                "accepted_claim_kinds",
                "claim kinds required",
            )
        if any(type(item) is not ClaimKind for item in self.accepted_claim_kinds):
            reject(
                "COMPOSITION.CLAIM_KINDS", "accepted_claim_kinds", "invalid claim kind"
            )
        if type(self.output_kind) is not ClaimKind:
            reject("COMPOSITION.OUTPUT_KIND", "output_kind", "invalid output kind")
        if type(self.evidence_cap) is not ClaimEvidenceGrade:
            reject("COMPOSITION.EVIDENCE_CAP", "evidence_cap", "invalid evidence cap")
        if self.output_kind not in self.accepted_claim_kinds:
            reject(
                "COMPOSITION.OUTPUT_KIND", "output_kind", "output kind must be accepted"
            )
        fields = (
            ("accepted_stances", self.accepted_stances),
            ("accepted_task_ids", self.accepted_task_ids),
            ("accepted_temporal_layers", self.accepted_temporal_layers),
            ("human_review_conditions", self.human_review_conditions),
        )
        for field_path, values in fields:
            if type(values) is not tuple or any(
                type(value) is not str or not value for value in values
            ):
                reject(
                    "COMPOSITION.TEXT_VALUES", field_path, "must be immutable strings"
                )
        if any(
            value not in {item.value for item in ClaimStance}
            for value in self.accepted_stances
        ):
            reject(
                "COMPOSITION.STANCES", "accepted_stances", "unsupported claim stance"
            )
        if any(
            value not in {item.value for item in TemporalLayer}
            for value in self.accepted_temporal_layers
        ):
            reject(
                "COMPOSITION.TEMPORAL_LAYERS",
                "accepted_temporal_layers",
                "unsupported temporal layer",
            )
        if any(
            value not in _CLOSED_HUMAN_REVIEW_CONDITIONS
            for value in self.human_review_conditions
        ):
            reject(
                "COMPOSITION.HUMAN_REVIEW",
                "human_review_conditions",
                "unsupported review condition",
            )
        if (
            type(self.required_component_slots) is not tuple
            or not self.required_component_slots
        ):
            reject(
                "COMPOSITION.SLOTS",
                "required_component_slots",
                "component slots required",
            )
        if any(
            type(slot) is not RequiredComponentSlot
            for slot in self.required_component_slots
        ):
            reject(
                "COMPOSITION.SLOTS",
                "required_component_slots",
                "invalid component slot",
            )
        if len({slot.slot_id for slot in self.required_component_slots}) != len(
            self.required_component_slots
        ):
            reject("COMPOSITION.SLOTS", "required_component_slots", "duplicate slot ID")
        if self.event_scope_rule != "component_only":
            reject(
                "COMPOSITION.EVENT_SCOPE_RULE",
                "event_scope_rule",
                "unsupported event scope rule",
            )
        if self.temporal_rule != "equal_only":
            reject(
                "COMPOSITION.TEMPORAL_RULE",
                "temporal_rule",
                "unsupported temporal rule",
            )
        if (
            type(self.preserve_counterevidence) is not bool
            or not self.preserve_counterevidence
        ):
            reject(
                "COMPOSITION.COUNTEREVIDENCE",
                "preserve_counterevidence",
                "must preserve",
            )
        if type(self.preserve_falsifier) is not bool or not self.preserve_falsifier:
            reject("COMPOSITION.FALSIFIER", "preserve_falsifier", "must preserve")
        if type(self.status) is not CompositionTemplateStatus:
            reject("COMPOSITION.STATUS", "status", "invalid template status")
        if type(self.specification_digest) is not DigestRef:
            reject("COMPOSITION.DIGEST", "specification_digest", "invalid digest")
        material = (
            "governance.composition-template.v1",
            self.template_id,
            self.version,
            tuple(item.value for item in self.accepted_claim_kinds),
            self.accepted_stances,
            self.accepted_task_ids,
            self.accepted_temporal_layers,
            tuple((slot.slot_id, slot.count) for slot in self.required_component_slots),
            self.output_kind.value,
            self.event_scope_rule,
            self.temporal_rule,
            self.evidence_cap.value,
            self.preserve_counterevidence,
            self.preserve_falsifier,
            self.human_review_conditions,
            self.status.value,
        )
        if self.specification_digest != DigestRef.from_material(material):
            reject(
                "COMPOSITION.DIGEST", "specification_digest", "template digest mismatch"
            )


@dataclass(frozen=True, slots=True)
class UnsupportedCompositionTemplate:
    template_id: str
    version: str
    issue_code: str = "COMPOSITION.UNSUPPORTED_TEMPLATE"


@dataclass(frozen=True, slots=True)
class CompositionRegistry:
    templates: tuple[CompositionTemplate, ...]

    def __post_init__(self) -> None:
        if type(self.templates) is not tuple or any(
            type(item) is not CompositionTemplate for item in self.templates
        ):
            reject("COMPOSITION.REGISTRY", "templates", "must be immutable templates")
        identities = tuple((item.template_id, item.version) for item in self.templates)
        if len(identities) != len(set(identities)):
            reject("COMPOSITION.DUPLICATE", "templates", "duplicate template identity")

    def lookup(
        self, template_id: str, version: str
    ) -> CompositionTemplate | UnsupportedCompositionTemplate:
        for template in self.templates:
            if (template.template_id, template.version) == (template_id, version):
                return template
        return UnsupportedCompositionTemplate(template_id, version)
