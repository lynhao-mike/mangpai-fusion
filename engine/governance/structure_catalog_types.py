from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum, unique
from importlib import import_module
from typing import TYPE_CHECKING, Final

from engine.governance.fact_values import DigestRef


if TYPE_CHECKING:
    from engine.governance.structure_catalog_models import (
        StructureCatalog,
        StructureCatalogEntry,
        expected_catalog_digest,
        expected_entry_digest,
    )


type StructureCatalogModelExport = (
    type["StructureCatalog"]
    | type["StructureCatalogEntry"]
    | Callable[["StructureCatalogEntry"], DigestRef]
    | Callable[[tuple["StructureCatalogEntry", ...]], DigestRef]
)

_MODEL_EXPORT_NAMES: Final = frozenset(
    {
        "StructureCatalog",
        "StructureCatalogEntry",
        "expected_catalog_digest",
        "expected_entry_digest",
    }
)

__all__ = (
    "CanonicalStructureKey",
    "ImplementationStatus",
    "SourceStatus",
    "StructureCatalog",
    "StructureCatalogContractError",
    "StructureCatalogEntry",
    "StructureConditionType",
    "StructureFamily",
    "StructureId",
    "StructureRole",
    "expected_catalog_digest",
    "expected_entry_digest",
)


@dataclass(frozen=True, slots=True)
class StructureId:
    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str or not self.value.strip():
            raise StructureCatalogContractError(
                "STRUCTURE.ID", "structure_id", "structure ID must be nonempty"
            )

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: StructureId | str) -> bool:
        if type(other) is StructureId:
            return self.value == other.value
        if type(other) is str:
            return self.value == other
        return False

    def __hash__(self) -> int:
        return hash(self.value)


@dataclass(frozen=True, slots=True)
class CanonicalStructureKey:
    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str or not self.value.strip():
            raise StructureCatalogContractError(
                "STRUCTURE.KEY", "canonical_key", "canonical key must be nonempty"
            )

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: CanonicalStructureKey | str) -> bool:
        if type(other) is CanonicalStructureKey:
            return self.value == other.value
        if type(other) is str:
            return self.value == other
        return False

    def __hash__(self) -> int:
        return hash(self.value)


@unique
class StructureFamily(StrEnum):
    FLOW_PROTECTION = "flow_protection"
    CONTROL_TRANSFORMATION = "control_transformation"
    CLEARING = "clearing"
    DAMAGE_IMBALANCE = "damage_imbalance"


@unique
class StructureRole(StrEnum):
    BODY = "body"
    PEER = "peer"
    ROB_WEALTH = "rob_wealth"
    FOOD_GOD = "food_god"
    HURTING_OFFICER = "hurting_officer"
    WEALTH = "wealth"
    OFFICER = "officer"
    KILLING = "killing"
    SEAL = "seal"
    OWL = "owl"
    BLADE = "blade"
    OUTPUT = "output"


@unique
class StructureConditionType(StrEnum):
    ROLE_PRESENCE = "role_presence"
    GENERATION_EDGE = "generation_edge"
    CONTROL_EDGE = "control_edge"
    COMBINATION_EDGE = "combination_edge"
    PROTECTIVE_FLOW = "protective_flow"
    CLEARING_RESOLUTION = "clearing_resolution"
    STRENGTH_BALANCE = "strength_balance"
    DAMAGE_CONFIRMED = "damage_confirmed"
    EDGE_MISSING = "edge_missing"
    ROLE_MISSING = "role_missing"
    MIXED_SIGNAL = "mixed_signal"
    OVERPOWERED = "overpowered"
    OVERDRAINED = "overdrained"
    SOURCE_DAMAGE = "source_damage"
    SELF_DAMAGE = "self_damage"
    HURTING_OFFICER_MEETS_OFFICER = "hurting_officer_meets_officer"
    OWL_ROBS_FOOD = "owl_robs_food"
    WEALTH_DAMAGES_SEAL = "wealth_damages_seal"
    PEERS_COMPETE_FOR_WEALTH = "peers_compete_for_wealth"
    WEALTH_AIDS_KILLING_ATTACK = "wealth_aids_killing_attack"
    OVERCONTROLLED_KILLING = "overcontrolled_killing"
    KILLING_ATTACKS_BODY = "killing_attacks_body"
    OUTPUT_OVERDRAINS_BODY = "output_overdrains_body"


@unique
class SourceStatus(StrEnum):
    DIRECT = "direct"
    NORMALIZED = "normalized"
    COMPOSITE = "composite"
    REVIEW = "review"
    DISPUTED = "disputed"


@unique
class ImplementationStatus(StrEnum):
    CURRENT_IMPLEMENTED = "current_implemented"
    CATALOG_ONLY_CANDIDATE = "catalog_only_candidate"
    CATALOG_ONLY_REVIEW = "catalog_only_review"


class StructureCatalogContractError(Exception):
    __slots__ = ("diagnostic", "field_path", "issue_code")

    def __init__(self, issue_code: str, field_path: str, diagnostic: str) -> None:
        super().__init__(issue_code, field_path, diagnostic)
        self.issue_code = issue_code
        self.field_path = field_path
        self.diagnostic = diagnostic

    def __str__(self) -> str:
        return self.diagnostic


def __getattr__(name: str) -> StructureCatalogModelExport:
    if name not in _MODEL_EXPORT_NAMES:
        raise AttributeError(name)
    module = import_module("engine.governance.structure_catalog_models")
    return getattr(module, name)
