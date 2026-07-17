from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping

from engine.decision.models import ChartFactLedger
from engine.decision.ziping_career_rules import (
    ZipingCareerRuleMapping,
    load_ziping_career_rule_mapping,
    mapping_digest,
)
from engine.features.types import ChartFeatureVector


class LocalStructureState(str, Enum):
    SUPPORTED = "supported"
    WEAKENED = "weakened"
    CONTRADICTED = "contradicted"
    ABSTAIN = "abstain"


class PublicationState(str, Enum):
    EMIT = "emit"
    HOLD = "hold"
    ABSTAIN = "abstain"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class CareerStructureFacts:
    official_count: int
    output_count: int
    wealth_count: int
    resource_count: int
    direct_hurting_official: bool
    output_official_coexistence: bool
    geju_type: str
    favor_shishen: tuple[str, ...]
    avoid_shishen: tuple[str, ...]
    branch_conflict_intensity: float


@dataclass(frozen=True)
class CareerEvidenceFamily:
    family_key: str
    matched: bool
    fact_refs: tuple[str, ...]
    feature_refs: tuple[str, ...]
    production_rule_refs: tuple[str, ...]
    reason_codes: tuple[str, ...]
    detail: str


@dataclass(frozen=True)
class ZipingCareerDiscrimination:
    task_id: str
    task_rule_id: str
    mapping_digest: str
    local_state: LocalStructureState
    publication_state: PublicationState
    coarse_trigger_observed: bool
    gates: Mapping[str, bool]
    families: tuple[CareerEvidenceFamily, ...]
    failed_gates: tuple[str, ...]
    matched_counter_families: tuple[str, ...]
    exclusions: tuple[str, ...]
    diagnostic_reasons: tuple[str, ...]
    remediation: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "gates", MappingProxyType(dict(self.gates)))
        object.__setattr__(self, "families", tuple(self.families))
        object.__setattr__(self, "failed_gates", tuple(self.failed_gates))
        object.__setattr__(
            self, "matched_counter_families", tuple(self.matched_counter_families)
        )
        object.__setattr__(self, "exclusions", tuple(self.exclusions))
        object.__setattr__(self, "diagnostic_reasons", tuple(self.diagnostic_reasons))


def _count(features: ChartFeatureVector, *names: str) -> int:
    return sum(int(features.ten_god_counts.get(name, 0)) for name in names)


def _string_values(profile: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = profile.get(key, ())
    if not isinstance(value, (list, tuple, set, frozenset)):
        return ()
    return tuple(str(item) for item in value)


def _extract_facts(
    features: ChartFeatureVector, geju_profile: Mapping[str, object]
) -> CareerStructureFacts:
    official_count = _count(features, "正官", "七杀")
    output_count = _count(features, "食神", "伤官")
    return CareerStructureFacts(
        official_count=official_count,
        output_count=output_count,
        wealth_count=_count(features, "正财", "偏财"),
        resource_count=_count(features, "正印", "偏印"),
        direct_hurting_official=_count(features, "伤官") > 0
        and _count(features, "正官") > 0,
        output_official_coexistence=official_count > 0 and output_count > 0,
        geju_type=str(geju_profile.get("geju_type") or ""),
        favor_shishen=_string_values(geju_profile, "favor_shishen"),
        avoid_shishen=_string_values(geju_profile, "avoid_shishen"),
        branch_conflict_intensity=features.branch_conflict_intensity,
    )


def _family(
    family_key: str,
    matched: bool,
    *,
    fact_refs: tuple[str, ...],
    feature_refs: tuple[str, ...],
    rule_refs: tuple[str, ...],
    reason_code: str,
    detail: str,
) -> CareerEvidenceFamily:
    return CareerEvidenceFamily(
        family_key=family_key,
        matched=matched,
        fact_refs=fact_refs,
        feature_refs=feature_refs,
        production_rule_refs=rule_refs,
        reason_codes=(reason_code,),
        detail=detail,
    )


def _empty_result(
    *,
    task_id: str,
    mapping: ZipingCareerRuleMapping,
    publication: PublicationState,
    failed_gates: tuple[str, ...],
    exclusions: tuple[str, ...],
    reason: str,
    remediation: str,
) -> ZipingCareerDiscrimination:
    return ZipingCareerDiscrimination(
        task_id=task_id,
        task_rule_id=mapping.task_rule_id,
        mapping_digest=mapping_digest(mapping),
        local_state=LocalStructureState.ABSTAIN,
        publication_state=publication,
        coarse_trigger_observed=False,
        gates={gate: False for gate in mapping.required_gates},
        families=(),
        failed_gates=failed_gates,
        matched_counter_families=(),
        exclusions=exclusions,
        diagnostic_reasons=(reason,),
        remediation=remediation,
    )


def discriminate_ziping_career_structure(
    chart: ChartFactLedger,
    features: ChartFeatureVector,
    geju_profile: Mapping[str, object],
    *,
    task_id: str = "career.role_change",
    mapping: ZipingCareerRuleMapping | None = None,
) -> ZipingCareerDiscrimination:
    if not isinstance(chart, ChartFactLedger):
        raise TypeError("chart must be ChartFactLedger")
    if not isinstance(features, ChartFeatureVector):
        raise TypeError("features must be ChartFeatureVector")
    rule_mapping = mapping or load_ziping_career_rule_mapping()
    if task_id != rule_mapping.task_id:
        return _empty_result(
            task_id=task_id,
            mapping=rule_mapping,
            publication=PublicationState.UNSUPPORTED,
            failed_gates=tuple(rule_mapping.required_gates),
            exclusions=("unsupported_task",),
            reason="task_not_mapped",
            remediation="Use the task ID declared by the rule mapping.",
        )
    if features.evidence_completeness != "full" or not geju_profile.get("geju_type"):
        return _empty_result(
            task_id=task_id,
            mapping=rule_mapping,
            publication=PublicationState.ABSTAIN,
            failed_gates=("complete_fact_closure",),
            exclusions=("incomplete_fact_closure",),
            reason="complete_chart_and_geju_profile_required",
            remediation="Provide full chart facts and an explicit geju_type.",
        )

    facts = _extract_facts(features, geju_profile)
    gates = {
        "complete_fact_closure": True,
        "official_path_anchor": facts.official_count > 0,
        "output_interference_present": facts.output_count > 0,
        "structure_qualification": facts.direct_hurting_official
        or facts.output_official_coexistence,
    }
    source_refs = tuple(item.production_rule_id for item in rule_mapping.source_anchors)
    favored_protection = bool(
        {"正官", "正印"}.intersection(facts.favor_shishen)
        or {"食神", "伤官"}.intersection(facts.avoid_shishen)
    )
    protected = (
        facts.wealth_count >= 1
        and facts.resource_count >= 1
        and favored_protection
    )
    families = (
        _family(
            "official_path_anchor",
            gates["official_path_anchor"],
            fact_refs=("ten_god_counts.正官", "ten_god_counts.七杀"),
            feature_refs=("has_official",),
            rule_refs=source_refs,
            reason_code="official_count_positive",
            detail="官杀事实归并为单一职业路径锚点家族。",
        ),
        _family(
            "output_interference",
            gates["output_interference_present"],
            fact_refs=("ten_god_counts.食神", "ten_god_counts.伤官"),
            feature_refs=("has_output",),
            rule_refs=source_refs,
            reason_code="output_count_positive",
            detail="食伤事实归并为单一干扰家族。",
        ),
        _family(
            "geju_direction",
            bool(facts.geju_type),
            fact_refs=("geju_profile.geju_type",),
            feature_refs=(),
            rule_refs=source_refs,
            reason_code="explicit_geju_type",
            detail="格局方向来自显式 profile。",
        ),
        _family(
            "official_path_protection",
            protected,
            fact_refs=(
                "ten_god_counts.正财",
                "ten_god_counts.偏财",
                "ten_god_counts.正印",
                "ten_god_counts.偏印",
            ),
            feature_refs=("has_wealth", "has_resource"),
            rule_refs=source_refs,
            reason_code="wealth_resource_geju_counter",
            detail="财印同时存在且格局方向明确支持护官反条件。",
        ),
        _family(
            "branch_environment_conflict",
            facts.branch_conflict_intensity > 0,
            fact_refs=("branch_relations",),
            feature_refs=("branch_conflict_intensity",),
            rule_refs=(),
            reason_code="environment_only",
            detail="地支冲突仅作环境证据，不能替代官杀或食伤必要门。",
        ),
    )

    if not gates["official_path_anchor"] or not gates["output_interference_present"]:
        local_state, publication = LocalStructureState.WEAKENED, PublicationState.HOLD
        reason = "required_official_or_output_gate_failed"
    elif protected:
        local_state, publication = LocalStructureState.CONTRADICTED, PublicationState.HOLD
        reason = "explicit_official_path_protection"
    elif all(gates.values()):
        local_state, publication = LocalStructureState.SUPPORTED, PublicationState.EMIT
        reason = "all_required_structure_gates_passed"
    else:
        local_state, publication = LocalStructureState.WEAKENED, PublicationState.HOLD
        reason = "structure_qualification_failed"

    # 仅模拟 production has_official_picture/always 粗入口已触发；它不是结构必要门替代物。
    coarse_trigger_observed = facts.official_count > 0
    failed_gates = tuple(name for name, passed in gates.items() if not passed)
    return ZipingCareerDiscrimination(
        task_id=task_id,
        task_rule_id=rule_mapping.task_rule_id,
        mapping_digest=mapping_digest(rule_mapping),
        local_state=local_state,
        publication_state=publication,
        coarse_trigger_observed=coarse_trigger_observed,
        gates=gates,
        families=families,
        failed_gates=failed_gates,
        matched_counter_families=("official_path_protection",) if protected else (),
        exclusions=(),
        diagnostic_reasons=(reason,),
        remediation="" if publication is PublicationState.EMIT else rule_mapping.falsifier,
    )
