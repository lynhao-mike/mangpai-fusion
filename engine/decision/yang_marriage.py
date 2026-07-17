"""杨派婚姻局部三态判别的不可变领域契约。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, cast

from engine.decision.models import ChartFactLedger
from engine.features.types import ChartFeatureVector
from engine.predicates.relations import zhi_chong, zhi_chuan, zhi_xing
from engine.predicates.types import Zhi

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
_STEMS = frozenset("甲乙丙丁戊己庚辛壬癸")
_BRANCHES = frozenset("子丑寅卯辰巳午未申酉戌亥")
_MALE_MARKERS = frozenset({"乾", "男", "男命", "乾造", "M", "male"})
_FEMALE_MARKERS = frozenset({"坤", "女", "女命", "坤造", "F", "female"})
_HARD_BLOCKING_REASON_CODES = frozenset({
    "missing_or_unknown_sex",
    "incomplete_evidence",
    "missing_or_invalid_day_pillar",
    "invalid_relationship_pair",
})
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


def _canonical_pair(pair: tuple[str, str]) -> CanonicalPair:
    if (
        len(pair) != 2
        or pair[0] not in _BRANCHES
        or pair[1] not in _BRANCHES
        or pair[0] == pair[1]
    ):
        raise ValueError("invalid relationship pair")
    return tuple(sorted(pair))  # type: ignore[return-value]


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
        if self.spouse_palace_branch and self.spouse_palace_branch not in _BRANCHES:
            raise ValueError("invalid spouse_palace_branch")
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


def extract_yang_marriage_signals(
    case_id: str,
    chart: ChartFactLedger,
    features: ChartFeatureVector,
) -> YangMarriageRawSignals:
    """只从命盘事实与 CFV 提取杨派婚姻结构原始信号。"""
    blockers: set[str] = set()
    marker = chart.sex_marker.strip()
    sex_basis: SexBasis = (
        "male_wealth"
        if marker in _MALE_MARKERS
        else "female_official"
        if marker in _FEMALE_MARKERS
        else "unknown"
    )
    if sex_basis == "unknown":
        blockers.add("missing_or_unknown_sex")
    if features.evidence_completeness != "full":
        blockers.add("incomplete_evidence")

    day = str(chart.four_pillars.get("day", chart.four_pillars.get("日柱", ""))).strip()
    day_branch = (
        day[1]
        if len(day) == 2 and day[0] in _STEMS and day[1] in _BRANCHES
        else ""
    )
    if not day_branch:
        blockers.add("missing_or_invalid_day_pillar")

    palace_pairs: set[CanonicalPair] = set()
    try:
        for pair in features.chong_pairs:
            canonical = _canonical_pair(pair)
            left, right = cast(tuple[Zhi, Zhi], canonical)
            if not zhi_chong(left, right):
                raise ValueError("invalid relationship pair")
            if day_branch and day_branch in canonical:
                palace_pairs.add(canonical)
        for pair in features.xing_hai_pairs:
            canonical = _canonical_pair(pair)
            left, right = cast(tuple[Zhi, Zhi], canonical)
            if zhi_xing(left, right) is None and not zhi_chuan(left, right):
                raise ValueError("invalid relationship pair")
            if day_branch and day_branch in canonical:
                palace_pairs.add(canonical)
    except ValueError:
        blockers.add("invalid_relationship_pair")
        palace_pairs.clear()

    wealth_count = sum(
        int(features.ten_god_counts.get(name, 0)) for name in ("正财", "偏财")
    )
    official_count = sum(
        int(features.ten_god_counts.get(name, 0)) for name in ("正官", "七杀")
    )
    spouse_count = (
        wealth_count
        if sex_basis == "male_wealth"
        else official_count
        if sex_basis == "female_official"
        else 0
    )
    spouse_present = (
        features.has_wealth and spouse_count > 0
        if sex_basis == "male_wealth"
        else features.has_official and spouse_count > 0
        if sex_basis == "female_official"
        else False
    )
    return YangMarriageRawSignals(
        case_id=case_id,
        sex_basis=sex_basis,
        spouse_palace_branch=day_branch,
        canonical_palace_pairs=tuple(sorted(palace_pairs)),
        spouse_star_present=spouse_present,
        spouse_star_count=spouse_count,
        peer_heavy=sum(
            int(features.ten_god_counts.get(name, 0)) for name in ("比肩", "劫财")
        )
        >= 3,
        output_heavy=sum(
            int(features.ten_god_counts.get(name, 0)) for name in ("食神", "伤官")
        )
        >= 4,
        mixed_official_kill=(
            sex_basis == "female_official" and features.mixed_official_kill
        ),
        blocking_reason_codes=tuple(sorted(blockers)),
    )


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


def reduce_yang_marriage_families(
    signals: YangMarriageRawSignals,
) -> tuple[YangMarriageFamilyEvidence, ...]:
    """把原始信号归并为固定六类家族；每个家族最多贡献一次。"""
    families: dict[FamilyKey, YangMarriageFamilyEvidence] = {}

    def add(
        key: FamilyKey,
        *,
        facts: tuple[str, ...],
        features: tuple[str, ...],
        reason: str,
        detail: str,
        pairs: tuple[CanonicalPair, ...] = (),
    ) -> None:
        families[key] = YangMarriageFamilyEvidence(
            key, True, facts, features, pairs, (reason,), detail
        )

    if signals.canonical_palace_pairs:
        add(
            "spouse_palace_event_anchor",
            facts=("four_pillars.day",),
            features=("chong_pairs", "xing_hai_pairs"),
            pairs=signals.canonical_palace_pairs,
            reason="day_branch_disrupted",
            detail="日支参与去重后的冲或刑害。",
        )
    if (
        signals.sex_basis == "male_wealth"
        and signals.spouse_star_present
        and signals.peer_heavy
    ):
        add(
            "spouse_star_peer_interaction",
            facts=("sex_marker",),
            features=(
                "has_wealth",
                "ten_god_counts.正财",
                "ten_god_counts.偏财",
                "ten_god_counts.比肩",
                "ten_god_counts.劫财",
            ),
            reason="male_wealth_peer_interaction",
            detail="男命财星上下文与比劫结构显式交互。",
        )
    if (
        signals.sex_basis == "female_official"
        and signals.spouse_star_present
        and signals.output_heavy
    ):
        add(
            "spouse_star_output_interaction",
            facts=("sex_marker",),
            features=(
                "has_official",
                "ten_god_counts.正官",
                "ten_god_counts.七杀",
                "ten_god_counts.食神",
                "ten_god_counts.伤官",
            ),
            reason="female_official_output_interaction",
            detail="女命官杀上下文与食伤结构显式交互。",
        )
    if signals.sex_basis == "female_official" and signals.mixed_official_kill:
        add(
            "spouse_star_configuration",
            facts=("sex_marker",),
            features=(
                "mixed_official_kill",
                "ten_god_counts.正官",
                "ten_god_counts.七杀",
            ),
            reason="female_mixed_official_configuration",
            detail="女命正官七杀复合配置按一个家族归并。",
        )
    if signals.sex_basis != "unknown" and (
        not signals.spouse_star_present or signals.spouse_star_count <= 1
    ):
        add(
            "spouse_star_context_pressure",
            facts=("sex_marker",),
            features=(
                "has_wealth",
                "has_official",
                "ten_god_counts.正财",
                "ten_god_counts.偏财",
                "ten_god_counts.正官",
                "ten_god_counts.七杀",
            ),
            reason="spouse_star_weak_or_missing",
            detail="配偶星弱或缺失只支持关系压力。",
        )
    ambient = (
        (signals.sex_basis != "male_wealth" or not signals.spouse_star_present)
        and signals.peer_heavy
    ) or (
        (signals.sex_basis != "female_official" or not signals.spouse_star_present)
        and signals.output_heavy
    )
    if ambient:
        add(
            "ambient_relationship_pressure",
            facts=("sex_marker",),
            features=(
                "ten_god_counts.比肩",
                "ten_god_counts.劫财",
                "ten_god_counts.食神",
                "ten_god_counts.伤官",
            ),
            reason="ambient_pressure_without_spouse_interaction",
            detail="全局压力缺少性别对应配偶星交互上下文。",
        )
    return tuple(sorted(families.values(), key=lambda item: item.family_key))


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
        allowed_interaction_families = {
            "male_wealth": frozenset({"spouse_star_peer_interaction"}),
            "female_official": frozenset({
                "spouse_star_output_interaction",
                "spouse_star_configuration",
            }),
            "unknown": frozenset(),
        }[self.sex_basis]
        if self.state in {"event", "pressure"} and (
            _EVENT_INTERACTION_FAMILY_KEYS.intersection(keys).difference(
                allowed_interaction_families
            )
        ):
            raise ValueError("interaction family is incompatible with sex_basis")
        if self.spouse_palace_branch and self.spouse_palace_branch not in _BRANCHES:
            raise ValueError("invalid spouse_palace_branch")
        if self.state == "pressure" and _HARD_BLOCKING_REASON_CODES.intersection(
            self.blocking_reason_codes
        ):
            raise ValueError("hard blocker requires abstain")
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
            self.sex_basis == "unknown" or not self.spouse_palace_branch.strip()
        ):
            raise ValueError("pressure requires known sex and spouse palace")
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
        if (
            self.state == "abstain"
            and self.families
            and not _HARD_BLOCKING_REASON_CODES.intersection(self.blocking_reason_codes)
        ):
            raise ValueError("abstain with families requires a hard blocker")
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


def discriminate_yang_marriage(
    case_id: str,
    chart: ChartFactLedger,
    features: ChartFeatureVector,
) -> YangMarriageDiscrimination:
    """按硬阻断、具名门 A+B、结构压力的优先级返回局部三态。"""
    signals = extract_yang_marriage_signals(case_id, chart, features)
    reduced_families = reduce_yang_marriage_families(signals)
    family_keys = frozenset(item.family_key for item in reduced_families)
    anchor = "spouse_palace_event_anchor" in family_keys
    interaction = bool(_EVENT_INTERACTION_FAMILY_KEYS.intersection(family_keys))
    blockers = list(signals.blocking_reason_codes)

    if blockers:
        state: YangMarriageState = "abstain"
        # DTO 禁止 abstain 携带完整事件载荷；硬阻断时不让诊断家族形成稳定反票。
        families = () if anchor and interaction else reduced_families
        result_anchor = False
        result_interaction = False
        falsifier = "补齐并校验输入后重算。"
    elif anchor and interaction:
        state = "event"
        families = reduced_families
        result_anchor = True
        result_interaction = True
        falsifier = "若婚姻史中没有离婚或再婚记录，则命题证伪。"
    elif reduced_families:
        state = "pressure"
        families = reduced_families
        result_anchor = anchor
        result_interaction = interaction
        if not anchor:
            blockers.append("missing_spouse_palace_event_anchor")
        if not interaction:
            blockers.append("missing_independent_spouse_interaction")
        falsifier = "存在关系压力不等于离婚或再婚事件成立。"
    else:
        state = "abstain"
        families = ()
        result_anchor = False
        result_interaction = False
        blockers.append("insufficient_yang_marriage_signal")
        falsifier = "当前无足够杨派婚姻信号；补充可验证结构后重算。"

    return YangMarriageDiscrimination(
        schema_version="yang-marriage-discrimination/v1",
        case_id=case_id,
        state=state,
        sex_basis=signals.sex_basis,
        spouse_palace_branch=signals.spouse_palace_branch,
        families=families,
        event_anchor_passed=result_anchor,
        independent_spouse_interaction_passed=result_interaction,
        blocking_reason_codes=tuple(sorted(set(blockers))),
        falsifier=falsifier,
        source_rule_refs=(
            "theory/yang/index.yaml#M2-Y-068",
            "theory/yang/index.yaml#M2-Y-088",
        ),
    )
