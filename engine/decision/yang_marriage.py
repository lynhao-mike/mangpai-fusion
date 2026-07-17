"""杨派婚姻局部三态判别的不可变领域契约。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

YangMarriageState = Literal["pressure", "event", "abstain"]
SexBasis = Literal["male_wealth", "female_official", "unknown"]
FamilyKey = Literal[
    "spouse_palace_event_anchor",
    "spouse_star_peer_interaction",
    "spouse_star_output_interaction",
    "spouse_star_configuration",
    "spouse_star_context_pressure",
    "ambient_relationship_pressure",
]
CanonicalPair = tuple[str, str]

_STATES = frozenset({"pressure", "event", "abstain"})
_SEX_BASES = frozenset({"male_wealth", "female_official", "unknown"})
_EVENT_INTERACTION_FAMILY_KEYS = frozenset({
    "spouse_star_peer_interaction",
    "spouse_star_output_interaction",
    "spouse_star_configuration",
})
_FAMILY_KEYS = frozenset({
    "spouse_palace_event_anchor",
    "spouse_star_peer_interaction",
    "spouse_star_output_interaction",
    "spouse_star_configuration",
    "spouse_star_context_pressure",
    "ambient_relationship_pressure",
})


@dataclass(frozen=True)
class YangMarriageRawSignals:
    case_id: str
    sex_basis: SexBasis
    spouse_palace_branch: str
    canonical_palace_pairs: tuple[CanonicalPair, ...]
    spouse_star_present: bool
    spouse_star_count: int
    peer_heavy: bool
    output_heavy: bool
    mixed_official_kill: bool
    blocking_reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.sex_basis not in _SEX_BASES:
            raise ValueError("invalid sex_basis")
        boolean_values = (
            self.spouse_star_present,
            self.peer_heavy,
            self.output_heavy,
            self.mixed_official_kill,
        )
        if any(type(value) is not bool for value in boolean_values):
            raise ValueError("boolean fields must be boolean")
        if type(self.spouse_star_count) is not int or self.spouse_star_count < 0:
            raise ValueError("spouse_star_count must be non-negative")
        object.__setattr__(
            self,
            "canonical_palace_pairs",
            tuple(sorted(set(self.canonical_palace_pairs))),
        )
        object.__setattr__(
            self,
            "blocking_reason_codes",
            tuple(sorted(set(self.blocking_reason_codes))),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "sex_basis": self.sex_basis,
            "spouse_palace_branch": self.spouse_palace_branch,
            "canonical_palace_pairs": [list(pair) for pair in self.canonical_palace_pairs],
            "spouse_star_present": self.spouse_star_present,
            "spouse_star_count": self.spouse_star_count,
            "peer_heavy": self.peer_heavy,
            "output_heavy": self.output_heavy,
            "mixed_official_kill": self.mixed_official_kill,
            "blocking_reason_codes": list(self.blocking_reason_codes),
        }


@dataclass(frozen=True)
class YangMarriageFamilyEvidence:
    family_key: FamilyKey
    matched: bool
    fact_refs: tuple[str, ...]
    feature_refs: tuple[str, ...]
    canonical_pairs: tuple[CanonicalPair, ...]
    reason_codes: tuple[str, ...]
    detail: str

    def __post_init__(self) -> None:
        if self.family_key not in _FAMILY_KEYS:
            raise ValueError("invalid family_key")
        if type(self.matched) is not bool:
            raise ValueError("matched must be boolean")
        if not self.matched or not self.reason_codes or not self.detail.strip():
            raise ValueError("matched family requires reason_codes and detail")
        object.__setattr__(self, "fact_refs", tuple(sorted(set(self.fact_refs))))
        object.__setattr__(self, "feature_refs", tuple(sorted(set(self.feature_refs))))
        object.__setattr__(
            self,
            "canonical_pairs",
            tuple(sorted(set(self.canonical_pairs))),
        )
        object.__setattr__(self, "reason_codes", tuple(sorted(set(self.reason_codes))))

    def to_dict(self) -> dict[str, Any]:
        return {
            "family_key": self.family_key,
            "matched": self.matched,
            "fact_refs": list(self.fact_refs),
            "feature_refs": list(self.feature_refs),
            "canonical_pairs": [list(pair) for pair in self.canonical_pairs],
            "reason_codes": list(self.reason_codes),
            "detail": self.detail,
        }


@dataclass(frozen=True)
class YangMarriageDiscrimination:
    schema_version: str
    case_id: str
    state: YangMarriageState
    sex_basis: SexBasis
    spouse_palace_branch: str
    families: tuple[YangMarriageFamilyEvidence, ...]
    event_anchor_passed: bool
    independent_spouse_interaction_passed: bool
    blocking_reason_codes: tuple[str, ...]
    falsifier: str
    source_rule_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.state not in _STATES:
            raise ValueError("invalid state")
        if self.sex_basis not in _SEX_BASES:
            raise ValueError("invalid sex_basis")
        if type(self.event_anchor_passed) is not bool or type(
            self.independent_spouse_interaction_passed
        ) is not bool:
            raise ValueError("gate fields must be boolean")
        keys = [item.family_key for item in self.families]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate family_key")
        has_event_anchor_family = "spouse_palace_event_anchor" in keys
        has_event_interaction_family = bool(
            _EVENT_INTERACTION_FAMILY_KEYS.intersection(keys)
        )
        if self.state == "event" and (
            not has_event_anchor_family
            or not has_event_interaction_family
            or not self.event_anchor_passed
            or not self.independent_spouse_interaction_passed
            or self.sex_basis == "unknown"
            or not self.spouse_palace_branch.strip()
            or self.blocking_reason_codes
        ):
            raise ValueError(
                "event requires named A and B families, consistent gates, known sex, "
                "spouse palace, and no blockers"
            )
        if self.state == "pressure" and (
            self.event_anchor_passed != has_event_anchor_family
            or self.independent_spouse_interaction_passed != has_event_interaction_family
        ):
            raise ValueError("gate fields must match family payload")
        if self.state == "pressure" and (
            not self.families
            or (self.event_anchor_passed and self.independent_spouse_interaction_passed)
            or not self.blocking_reason_codes
        ):
            raise ValueError("pressure requires evidence, a failed gate, and blockers")
        if self.state == "abstain" and (
            self.event_anchor_passed or self.independent_spouse_interaction_passed
        ):
            raise ValueError("abstain cannot pass event gates")
        if self.state == "abstain" and (
            has_event_anchor_family and has_event_interaction_family
        ):
            raise ValueError("abstain cannot carry a complete event family payload")
        if self.state == "abstain" and not self.blocking_reason_codes:
            raise ValueError("abstain requires blocking reasons")
        if not self.case_id.strip() or not self.schema_version.strip() or not self.falsifier.strip():
            raise ValueError("identity and falsifier are required")
        object.__setattr__(
            self,
            "families",
            tuple(sorted(self.families, key=lambda item: item.family_key)),
        )
        object.__setattr__(
            self,
            "blocking_reason_codes",
            tuple(sorted(set(self.blocking_reason_codes))),
        )
        object.__setattr__(
            self,
            "source_rule_refs",
            tuple(sorted(set(self.source_rule_refs))),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "state": self.state,
            "sex_basis": self.sex_basis,
            "spouse_palace_branch": self.spouse_palace_branch,
            "families": [item.to_dict() for item in self.families],
            "event_anchor_passed": self.event_anchor_passed,
            "independent_spouse_interaction_passed": self.independent_spouse_interaction_passed,
            "blocking_reason_codes": list(self.blocking_reason_codes),
            "falsifier": self.falsifier,
            "source_rule_refs": list(self.source_rule_refs),
        }
