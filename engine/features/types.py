"""命局特征向量的数据契约。"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Literal, Mapping

EvidenceCompleteness = Literal["full", "no_hour", "partial"]
Pair = tuple[str, str]


def _freeze_mapping(value: Mapping[str, int | float]) -> Mapping[str, int | float]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class ChartFeatureVector:
    schema_version: str
    chart_id: str

    element_counts: Mapping[str, int]
    element_energy: Mapping[str, float]
    dominant_element: str
    missing_elements: tuple[str, ...]
    element_concentration: float

    day_master: str
    day_master_element: str
    month_branch: str
    month_lord: str
    rooted_count: int
    supporting_count: int
    draining_count: int
    monthly_command_favorable: bool

    ten_god_counts: Mapping[str, int]
    has_official: bool
    has_wealth: bool
    has_output: bool
    has_resource: bool
    mixed_official_kill: bool

    chong_pairs: tuple[Pair, ...]
    he_pairs: tuple[Pair, ...]
    xing_hai_pairs: tuple[Pair, ...]
    branch_conflict_intensity: float

    cold_warm_axis: float
    dry_wet_axis: float
    climate_extreme: bool

    has_hour_pillar: bool
    evidence_completeness: EvidenceCompleteness

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("schema_version is required")
        if not self.chart_id:
            raise ValueError("chart_id is required")
        energy_total = sum(float(value) for value in self.element_energy.values())
        if abs(energy_total - 1.0) > 1e-9:
            raise ValueError("element_energy must sum to 1.0")
        if self.evidence_completeness not in {"full", "no_hour", "partial"}:
            raise ValueError("evidence_completeness must be full, no_hour, or partial")
        if not -1.0 <= self.cold_warm_axis <= 1.0:
            raise ValueError("cold_warm_axis must be between -1 and 1")
        if not -1.0 <= self.dry_wet_axis <= 1.0:
            raise ValueError("dry_wet_axis must be between -1 and 1")
        if not 0.0 <= self.element_concentration <= 1.0:
            raise ValueError("element_concentration must be between 0 and 1")
        if not 0.0 <= self.branch_conflict_intensity <= 1.0:
            raise ValueError("branch_conflict_intensity must be between 0 and 1")
        for name in ("rooted_count", "supporting_count", "draining_count"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")
        for name in ("chong_pairs", "he_pairs", "xing_hai_pairs"):
            pairs = getattr(self, name)
            if any(not isinstance(pair, tuple) or len(pair) != 2 for pair in pairs):
                raise ValueError(f"{name} must contain two-item pairs")

        object.__setattr__(self, "element_counts", _freeze_mapping(self.element_counts))
        object.__setattr__(self, "element_energy", _freeze_mapping(self.element_energy))
        object.__setattr__(self, "ten_god_counts", _freeze_mapping(self.ten_god_counts))
        object.__setattr__(self, "missing_elements", tuple(self.missing_elements))
        object.__setattr__(self, "chong_pairs", tuple(tuple(pair) for pair in self.chong_pairs))
        object.__setattr__(self, "he_pairs", tuple(tuple(pair) for pair in self.he_pairs))
        object.__setattr__(self, "xing_hai_pairs", tuple(tuple(pair) for pair in self.xing_hai_pairs))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "chart_id": self.chart_id,
            "element_counts": dict(self.element_counts),
            "element_energy": dict(self.element_energy),
            "dominant_element": self.dominant_element,
            "missing_elements": list(self.missing_elements),
            "element_concentration": self.element_concentration,
            "day_master": self.day_master,
            "day_master_element": self.day_master_element,
            "month_branch": self.month_branch,
            "month_lord": self.month_lord,
            "rooted_count": self.rooted_count,
            "supporting_count": self.supporting_count,
            "draining_count": self.draining_count,
            "monthly_command_favorable": self.monthly_command_favorable,
            "ten_god_counts": dict(self.ten_god_counts),
            "has_official": self.has_official,
            "has_wealth": self.has_wealth,
            "has_output": self.has_output,
            "has_resource": self.has_resource,
            "mixed_official_kill": self.mixed_official_kill,
            "chong_pairs": [list(pair) for pair in self.chong_pairs],
            "he_pairs": [list(pair) for pair in self.he_pairs],
            "xing_hai_pairs": [list(pair) for pair in self.xing_hai_pairs],
            "branch_conflict_intensity": self.branch_conflict_intensity,
            "cold_warm_axis": self.cold_warm_axis,
            "dry_wet_axis": self.dry_wet_axis,
            "climate_extreme": self.climate_extreme,
            "has_hour_pillar": self.has_hour_pillar,
            "evidence_completeness": self.evidence_completeness,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChartFeatureVector":
        copied = deepcopy(data)
        for name in ("chong_pairs", "he_pairs", "xing_hai_pairs"):
            raw_pairs = copied.get(name)
            if not isinstance(raw_pairs, (list, tuple)) or any(
                not isinstance(pair, (list, tuple)) or len(pair) != 2 for pair in raw_pairs
            ):
                raise ValueError(f"{name} must contain two-item pairs")
            copied[name] = tuple(tuple(pair) for pair in raw_pairs)
        copied["missing_elements"] = tuple(copied.get("missing_elements", ()))
        try:
            return cls(**copied)
        except (KeyError, TypeError) as exc:
            raise ValueError(f"invalid ChartFeatureVector payload: {exc}") from exc
