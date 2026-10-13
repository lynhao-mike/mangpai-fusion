"""命盘职业关系图与可审计 trace 构建器。

本模块只接受四柱事实（``engine.predicates.types.Bazi``），依据
[`15-career-relation-inference-v1.md`](../contracts/15-career-relation-inference-v1.md)
的五步职业柱选择契约，构建：

- 干支/藏干/十神/宫位节点；
- 邻柱、透藏、原字根、六合/冲/刑/害等仓库已有确定性谓词支撑的关系边；
- 严格五步优先级的职业柱候选发现与选择 trace；
- 逐步记录候选发现、淘汰理由、冲突与 unresolved 信号。

本模块不读取 occupation、known_facts、标签或反馈；不计算浮点分数、
概率或权重。仅把天干原字存在于异柱藏干中的事实表达为 ``ROOTED``；
对完整通根强弱、力量四态、入库、成格星等契约未定义或无可靠谓词
支撑的判断，只显式输出 ``unresolved``，不伪实现。
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from enum import Enum
import json
from typing import Any

from engine.asof.career_relation_contract import (
    CareerPalace,
    CareerPillarCandidate,
    CareerRelation,
    CareerRelationInference,
    PillarPosition,
    RelationType,
    SelectionStage,
    infer_career_pillar,
    palace_for_pillar,
)
from engine.predicates.career import is_rooted
from engine.predicates.ganzhi import get_canggan, is_gan, is_valid_jiazi, is_zhi
from engine.predicates.palace import get_shishen
from engine.predicates.relations import gan_he, zhi_chong, zhi_chuan, zhi_liuhe, zhi_xing
from engine.predicates.tou_cang import tou_chu
from engine.predicates.types import Bazi, GanZhi

SCHEMA_VERSION = "career-relation-graph/v1"

_OFFICER_KILLING_SHISHEN = ("正官", "七杀")
_WEALTH_SHISHEN = ("正财", "偏财")

_PILLAR_FIELD = {
    PillarPosition.YEAR: "年柱",
    PillarPosition.MONTH: "月柱",
    PillarPosition.DAY: "日柱",
    PillarPosition.HOUR: "时柱",
}
_ZHI_KEY = {
    PillarPosition.YEAR: "年支",
    PillarPosition.MONTH: "月支",
    PillarPosition.DAY: "日支",
    PillarPosition.HOUR: "时支",
}
_PILLAR_ORDER = (
    PillarPosition.YEAR,
    PillarPosition.MONTH,
    PillarPosition.DAY,
    PillarPosition.HOUR,
)


class FrozenStringEnum(str, Enum):
    """可稳定序列化为字符串的领域枚举基类。"""


class UnresolvedTopic(FrozenStringEnum):
    """契约或仓库谓词尚不能可靠支撑的判断主题。"""

    ROOTING_STRENGTH = "rooting_strength"
    FOUR_STATE_POWER = "four_state_power"
    TOMB_RELATION = "tomb_relation"
    FORMATION_STAR = "formation_star"


_UNRESOLVED_REASONS: dict[UnresolvedTopic, str] = {
    UnresolvedTopic.ROOTING_STRENGTH: (
        "no_reliable_predicate: 完整通根强弱判定缺少可审计确定性谓词，"
        "本图不计算通根强弱结论"
    ),
    UnresolvedTopic.FOUR_STATE_POWER: (
        "no_reliable_predicate: 力量四态（旺相休囚死一类分级）缺少可审计"
        "确定性谓词，本图不计算力量等级"
    ),
    UnresolvedTopic.TOMB_RELATION: (
        "no_reliable_predicate: enters_tomb 关系缺少经过验证的通用确定性"
        "谓词（现有入库工具函数为财富模块私有实现），本图不生成 enters_tomb 边"
    ),
    UnresolvedTopic.FORMATION_STAR: (
        "no_reliable_predicate: 成格星缺少契约级定义与确定性谓词，"
        "step_5 不生成候选"
    ),
}


@dataclass(frozen=True, slots=True)
class HiddenStemNode:
    """地支藏干节点：字、类型、宫位所在柱、对应十神。"""

    gan: str
    canggan_type: str
    shishen: str


@dataclass(frozen=True, slots=True)
class PillarNode:
    """柱位节点：干支、天干十神、藏干节点列表。"""

    pillar: PillarPosition
    palace: CareerPalace
    gan: str
    zhi: str
    stem_shishen: str | None
    hidden_stems: tuple[HiddenStemNode, ...]


@dataclass(frozen=True, slots=True)
class StageAttempt:
    """单个五步阶段的候选发现记录（找到或未找到及原因）。"""

    stage: SelectionStage
    found_pillars: tuple[PillarPosition, ...]
    note: str


@dataclass(frozen=True, slots=True)
class UnresolvedSignal:
    """显式声明当前无法可靠计算的判断主题。"""

    topic: UnresolvedTopic
    reason: str


@dataclass(frozen=True, slots=True)
class LeftPillarCharacterization:
    """已选职业柱左邻柱的确定性命盘特征；年柱边界显式为空。"""

    career_pillar: PillarPosition
    pillar: PillarPosition | None
    gan: str | None
    zhi: str | None
    stem_shishen: str | None
    hidden_shishen: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CareerRelationGraph:
    """职业关系图：柱位节点 + 已证明的柱间关系边。"""

    schema_version: str
    pillars: tuple[PillarNode, ...]
    relations: tuple[CareerRelation, ...]

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        object.__setattr__(
            self, "relations", tuple(sorted(set(self.relations), key=_relation_sort_key))
        )


@dataclass(frozen=True, slots=True)
class CareerRelationGraphResult:
    """图 + 候选发现 trace + 契约推断 + unresolved 信号的完整可审计产物。"""

    schema_version: str
    graph: CareerRelationGraph
    stage_trace: tuple[StageAttempt, ...]
    inference: CareerRelationInference
    left_pillar_characterization: LeftPillarCharacterization | None
    unresolved: tuple[UnresolvedSignal, ...]

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
        object.__setattr__(
            self,
            "unresolved",
            tuple(sorted(set(self.unresolved), key=lambda item: item.topic.value)),
        )

    def to_canonical_dict(self) -> dict[str, Any]:
        """返回只含 JSON 基础类型、键和值顺序稳定的结构。"""

        return _canonical_value(self)

    def to_canonical_json(self) -> str:
        """返回确定性的紧凑 UTF-8 JSON 文本。"""

        return json.dumps(
            self.to_canonical_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )


def _pillar_ganzhi(bazi: Bazi, pillar: PillarPosition) -> tuple[str, str]:
    ganzhi = getattr(bazi, _PILLAR_FIELD[pillar])
    return ganzhi.gan, ganzhi.zhi


def _validate_bazi(bazi: Bazi) -> None:
    if not isinstance(bazi, Bazi):
        raise TypeError("bazi must be engine.predicates.types.Bazi")
    for pillar in _PILLAR_ORDER:
        gan, zhi = _pillar_ganzhi(bazi, pillar)
        if not is_gan(gan):
            raise ValueError(f"invalid gan for {pillar.value}: {gan!r}")
        if not is_zhi(zhi):
            raise ValueError(f"invalid zhi for {pillar.value}: {zhi!r}")
        if not is_valid_jiazi(GanZhi(gan, zhi)):
            raise ValueError(f"invalid jiazi for {pillar.value}: {gan}{zhi}")


def _build_pillar_nodes(bazi: Bazi, day_master: str) -> dict[PillarPosition, PillarNode]:
    nodes: dict[PillarPosition, PillarNode] = {}
    for pillar in _PILLAR_ORDER:
        gan, zhi = _pillar_ganzhi(bazi, pillar)
        stem_shishen = get_shishen(gan, day_master) if pillar != PillarPosition.DAY else None
        hidden = tuple(
            HiddenStemNode(
                gan=item.gan,
                canggan_type=item.type,
                shishen=get_shishen(item.gan, day_master),
            )
            for item in get_canggan(zhi)
        )
        nodes[pillar] = PillarNode(
            pillar=pillar,
            palace=palace_for_pillar(pillar),
            gan=gan,
            zhi=zhi,
            stem_shishen=stem_shishen,
            hidden_stems=hidden,
        )
    return nodes


def _pillar_shishen_set(node: PillarNode) -> set[str]:
    shishens = {hidden.shishen for hidden in node.hidden_stems}
    if node.stem_shishen is not None:
        shishens.add(node.stem_shishen)
    return shishens


def _adjacent_pairs() -> tuple[tuple[PillarPosition, PillarPosition], ...]:
    return tuple(
        (_PILLAR_ORDER[i], _PILLAR_ORDER[i + 1]) for i in range(len(_PILLAR_ORDER) - 1)
    )


def _build_relations(
    bazi: Bazi, nodes: dict[PillarPosition, PillarNode]
) -> tuple[CareerRelation, ...]:
    relations: list[CareerRelation] = []

    for left, right in _adjacent_pairs():
        relations.append(
            CareerRelation(
                source=left,
                target=right,
                relation_type=RelationType.ADJACENT,
                evidence_refs=(f"adjacent:{left.value}-{right.value}",),
            )
        )

    for i, source in enumerate(_PILLAR_ORDER):
        for target in _PILLAR_ORDER[i + 1 :]:
            source_node = nodes[source]
            target_node = nodes[target]

            if zhi_liuhe(source_node.zhi, target_node.zhi) is not None or (
                {source_node.zhi, target_node.zhi} == {"午", "未"}
            ):
                relations.append(
                    CareerRelation(
                        source=source,
                        target=target,
                        relation_type=RelationType.COMBINATION,
                        evidence_refs=(
                            f"zhi_liuhe:{source_node.zhi}-{target_node.zhi}",
                        ),
                    )
                )

            if gan_he(source_node.gan, target_node.gan) is not None:
                relations.append(
                    CareerRelation(
                        source=source,
                        target=target,
                        relation_type=RelationType.COMBINATION,
                        evidence_refs=(
                            f"gan_he:{source_node.gan}-{target_node.gan}",
                        ),
                    )
                )

            if zhi_chong(source_node.zhi, target_node.zhi):
                relations.append(
                    CareerRelation(
                        source=source,
                        target=target,
                        relation_type=RelationType.CLASH,
                        evidence_refs=(
                            f"zhi_chong:{source_node.zhi}-{target_node.zhi}",
                        ),
                    )
                )

            xing_kind = zhi_xing(source_node.zhi, target_node.zhi)
            if xing_kind is not None:
                relations.append(
                    CareerRelation(
                        source=source,
                        target=target,
                        relation_type=RelationType.PUNISHMENT,
                        evidence_refs=(
                            f"zhi_xing:{xing_kind}:{source_node.zhi}-{target_node.zhi}",
                        ),
                    )
                )

            if zhi_chuan(source_node.zhi, target_node.zhi):
                relations.append(
                    CareerRelation(
                        source=source,
                        target=target,
                        relation_type=RelationType.HARM,
                        evidence_refs=(
                            f"zhi_chuan:{source_node.zhi}-{target_node.zhi}",
                        ),
                    )
                )

    # 当前关系契约禁止同端点，因此只表达可审计的异柱原字根。
    # 这不是完整通根强弱结论；同柱根仍可由纯谓词独立查询。
    for source, source_node in nodes.items():
        for target, target_node in nodes.items():
            if source is target or not is_rooted(source_node.gan, target_node.zhi):
                continue
            relations.append(
                CareerRelation(
                    source=source,
                    target=target,
                    relation_type=RelationType.ROOTED,
                    evidence_refs=(
                        f"root_exists:{source_node.gan}:{target_node.zhi}:"
                        f"{source.value}-{target.value}",
                    ),
                )
            )

    for pillar, node in nodes.items():
        hit = tou_chu(node.gan, bazi)
        if hit is None:
            continue
        cang_zhi_key, tou_palace_name = hit
        cang_pillar = next(
            candidate for candidate, key in _ZHI_KEY.items() if key == cang_zhi_key
        )
        tou_pillar = next(
            candidate
            for candidate, field_name in _PILLAR_FIELD.items()
            if field_name == tou_palace_name
        )
        if cang_pillar == tou_pillar:
            continue
        relations.append(
            CareerRelation(
                source=cang_pillar,
                target=tou_pillar,
                relation_type=RelationType.HIDDEN_REVEALED,
                evidence_refs=(f"tou_chu:{node.gan}:{cang_pillar.value}-{tou_pillar.value}",),
            )
        )

    return tuple(relations)


def _relation_involves(relation: CareerRelation, pillar: PillarPosition) -> bool:
    return relation.source is pillar or relation.target is pillar


def _find_step1_step2_candidates(
    nodes: dict[PillarPosition, PillarNode],
) -> tuple[list[CareerPillarCandidate], StageAttempt]:
    found: list[CareerPillarCandidate] = []
    hits: list[PillarPosition] = []
    for pillar in (PillarPosition.DAY, PillarPosition.HOUR):
        node = nodes[pillar]
        shishens = _pillar_shishen_set(node)
        officer_hits = shishens & set(_OFFICER_KILLING_SHISHEN)
        if not officer_hits:
            continue
        hits.append(pillar)
        evidence = tuple(
            sorted(f"shishen:{pillar.value}:{name}" for name in officer_hits)
        )
        found.append(
            CareerPillarCandidate(
                pillar=pillar,
                palace=node.palace,
                stage=SelectionStage.SELF_OFFICER_KILLING,
                relations=(),
                evidence_refs=evidence,
            )
        )
    note = (
        f"self_palace officer/killing found at {[p.value for p in hits]}"
        if hits
        else "no officer/killing shishen in self palace (day/hour)"
    )
    return found, StageAttempt(
        stage=SelectionStage.SELF_OFFICER_KILLING,
        found_pillars=tuple(hits),
        note=note,
    )


def _find_step3_candidates(
    nodes: dict[PillarPosition, PillarNode],
    relations: tuple[CareerRelation, ...],
) -> tuple[list[CareerPillarCandidate], StageAttempt]:
    found: list[CareerPillarCandidate] = []
    hits: list[PillarPosition] = []
    for pillar in (PillarPosition.YEAR, PillarPosition.MONTH):
        node = nodes[pillar]
        shishens = _pillar_shishen_set(node)
        officer_hits = shishens & set(_OFFICER_KILLING_SHISHEN)
        if not officer_hits:
            continue
        hour_links = tuple(
            relation
            for relation in relations
            if _relation_involves(relation, pillar)
            and _relation_involves(relation, PillarPosition.HOUR)
        )
        if not hour_links:
            continue
        hits.append(pillar)
        evidence = tuple(
            sorted(f"shishen:{pillar.value}:{name}" for name in officer_hits)
        )
        found.append(
            CareerPillarCandidate(
                pillar=pillar,
                palace=node.palace,
                stage=SelectionStage.OTHER_OFFICER_KILLING_LINKED_TO_HOUR,
                relations=hour_links,
                evidence_refs=evidence,
            )
        )
    note = (
        f"other_palace officer/killing linked to hour at {[p.value for p in hits]}"
        if hits
        else "no other_palace officer/killing candidate with a proven hour link"
    )
    return found, StageAttempt(
        stage=SelectionStage.OTHER_OFFICER_KILLING_LINKED_TO_HOUR,
        found_pillars=tuple(hits),
        note=note,
    )


def _find_step4_candidates(
    nodes: dict[PillarPosition, PillarNode],
) -> tuple[list[CareerPillarCandidate], StageAttempt]:
    """财星候选：候选发现层先我宫、后他宫；先我宫命中即不再看他宫。"""

    self_hits: list[PillarPosition] = []
    other_hits: list[PillarPosition] = []
    found: list[CareerPillarCandidate] = []

    for pillar in (PillarPosition.DAY, PillarPosition.HOUR):
        node = nodes[pillar]
        wealth_hits = _pillar_shishen_set(node) & set(_WEALTH_SHISHEN)
        if wealth_hits:
            self_hits.append(pillar)
            evidence = tuple(
                sorted(f"shishen:{pillar.value}:{name}" for name in wealth_hits)
            )
            found.append(
                CareerPillarCandidate(
                    pillar=pillar,
                    palace=node.palace,
                    stage=SelectionStage.WEALTH_OR_WEALTH_TOMB,
                    relations=(),
                    evidence_refs=evidence,
                )
            )

    if not self_hits:
        for pillar in (PillarPosition.YEAR, PillarPosition.MONTH):
            node = nodes[pillar]
            wealth_hits = _pillar_shishen_set(node) & set(_WEALTH_SHISHEN)
            if wealth_hits:
                other_hits.append(pillar)
                evidence = tuple(
                    sorted(f"shishen:{pillar.value}:{name}" for name in wealth_hits)
                )
                found.append(
                    CareerPillarCandidate(
                        pillar=pillar,
                        palace=node.palace,
                        stage=SelectionStage.WEALTH_OR_WEALTH_TOMB,
                        relations=(),
                        evidence_refs=evidence,
                    )
                )

    hits = self_hits + other_hits
    if self_hits:
        note = f"self_palace wealth found at {[p.value for p in self_hits]}; other_palace not scanned"
    elif other_hits:
        note = (
            "no self_palace wealth; other_palace wealth found at "
            f"{[p.value for p in other_hits]}"
        )
    else:
        note = "no wealth shishen in self_palace or other_palace"

    return found, StageAttempt(
        stage=SelectionStage.WEALTH_OR_WEALTH_TOMB,
        found_pillars=tuple(hits),
        note=note,
    )


def _step2_attempt() -> StageAttempt:
    return StageAttempt(
        stage=SelectionStage.SELF_OFFICER_KILLING_TOMB,
        found_pillars=(),
        note="tomb relation unresolved: no reliable predicate to compute 官杀库",
    )


def _step5_attempt() -> StageAttempt:
    return StageAttempt(
        stage=SelectionStage.FORMATION_STAR_LINKED_TO_SELF,
        found_pillars=(),
        note="formation_star unresolved: no contract-level definition or predicate",
    )


def build_career_relation_graph(bazi: Bazi) -> CareerRelationGraphResult:
    """从四柱事实构建职业关系图、五步候选 trace 与契约推断。

    输入仅四柱（``Bazi``）；不读取藏干力量分数、occupation、known_facts
    或反馈。step_2（官杀库）与 step_5（成格星）因缺少可靠确定性谓词，
    始终不产生候选，并显式记录在 ``unresolved`` 与 stage trace 中。
    """

    _validate_bazi(bazi)
    day_master = bazi.日柱.gan

    nodes = _build_pillar_nodes(bazi, day_master)
    relations = _build_relations(bazi, nodes)
    graph = CareerRelationGraph(
        schema_version=SCHEMA_VERSION,
        pillars=tuple(nodes[pillar] for pillar in _PILLAR_ORDER),
        relations=relations,
    )

    step1_candidates, step1_attempt = _find_step1_step2_candidates(nodes)
    step2_attempt = _step2_attempt()
    step3_candidates, step3_attempt = _find_step3_candidates(nodes, relations)
    step4_candidates, step4_attempt = _find_step4_candidates(nodes)
    step5_attempt = _step5_attempt()

    all_candidates = (
        *step1_candidates,
        *step3_candidates,
        *step4_candidates,
    )
    inference = infer_career_pillar(all_candidates)

    stage_trace = (
        step1_attempt,
        step2_attempt,
        step3_attempt,
        step4_attempt,
        step5_attempt,
    )

    left_pillar_characterization: LeftPillarCharacterization | None = None
    if inference.left_pillar is not None:
        left_position = inference.left_pillar.pillar
        left_node = nodes[left_position] if left_position is not None else None
        left_pillar_characterization = LeftPillarCharacterization(
            career_pillar=inference.left_pillar.career_pillar,
            pillar=left_position,
            gan=left_node.gan if left_node is not None else None,
            zhi=left_node.zhi if left_node is not None else None,
            stem_shishen=left_node.stem_shishen if left_node is not None else None,
            hidden_shishen=(
                tuple(item.shishen for item in left_node.hidden_stems)
                if left_node is not None
                else ()
            ),
        )

    unresolved = tuple(
        UnresolvedSignal(topic=topic, reason=reason)
        for topic, reason in _UNRESOLVED_REASONS.items()
    )

    return CareerRelationGraphResult(
        schema_version=SCHEMA_VERSION,
        graph=graph,
        stage_trace=stage_trace,
        inference=inference,
        left_pillar_characterization=left_pillar_characterization,
        unresolved=unresolved,
    )


def _relation_sort_key(relation: CareerRelation) -> tuple[int, int, str, tuple[str, ...]]:
    order = {pillar: index for index, pillar in enumerate(_PILLAR_ORDER)}
    return (
        order[relation.source],
        order[relation.target],
        relation.relation_type.value,
        relation.evidence_refs,
    )


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {field.name: _canonical_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_canonical_value(item) for item in value]
    return value


__all__ = (
    "SCHEMA_VERSION",
    "UnresolvedTopic",
    "HiddenStemNode",
    "PillarNode",
    "StageAttempt",
    "UnresolvedSignal",
    "LeftPillarCharacterization",
    "CareerRelationGraph",
    "CareerRelationGraphResult",
    "build_career_relation_graph",
)
