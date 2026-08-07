"""结构化大运阶段上下文与既有回溯时间容器的隔离适配层。"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from engine.asof.natal_capacity import EvidenceRef
from engine.predicates.palace import get_shishen
from engine.predicates.types import Bazi, GanZhi, ZHI_CANGGAN_TABLE


class DaiyunSegmentSignal(Protocol):
    """只声明允许从既有 ``DaiyunSegment`` 消费的信号表面。

    ``feature`` 与 ``typical_domains`` 是自由文本/粗分类，只能进入未裁决信号，
    不能自动映射为路径开放、关闭、放大、抑制、修复或改道。
    """

    seq: int
    ganzhi: str
    age_range: tuple[int, int]
    year_range: tuple[int, int]
    feature: str
    typical_domains: list[str]


@dataclass(frozen=True, slots=True)
class PathChange:
    """一条经过调用方显式裁决的阶段路径变化。"""

    path_id: str
    reason: str
    evidence: tuple[EvidenceRef, ...]

    def __post_init__(self) -> None:
        if not self.path_id.strip() or not self.reason.strip() or not self.evidence:
            raise ValueError("path change requires identity, reason and evidence")


@dataclass(frozen=True, slots=True)
class NatalRelation:
    """大运信号与原局承载节点之间的结构化有效关系。"""

    natal_node_id: str
    relation: str
    evidence: tuple[EvidenceRef, ...]

    def __post_init__(self) -> None:
        if not self.natal_node_id.strip() or not self.relation.strip() or not self.evidence:
            raise ValueError("natal relation requires node, relation and evidence")


@dataclass(frozen=True, slots=True)
class DaiyunStage:
    """as-of 阶段上下文，不是既有逐年回溯 ``DaiyunSegment``。

    本对象表达结构化路径约束；不包含流年列表、现实事件后果或阶段总分。
    """

    sequence: int
    ganzhi: str
    start_date: date
    end_date: date
    opened_paths: tuple[PathChange, ...]
    closed_paths: tuple[PathChange, ...]
    amplified_paths: tuple[PathChange, ...]
    suppressed_paths: tuple[PathChange, ...]
    repaired_paths: tuple[PathChange, ...]
    redirected_paths: tuple[PathChange, ...]
    natal_relations: tuple[NatalRelation, ...]
    domain_tendency: str
    applicability_conditions: tuple[str, ...]
    counter_evidence: tuple[EvidenceRef, ...]
    signal_refs: tuple[EvidenceRef, ...]
    unresolved_signal_refs: tuple[EvidenceRef, ...]

    def __post_init__(self) -> None:
        if self.sequence < 1 or not self.ganzhi.strip():
            raise ValueError("daiyun stage requires positive sequence and ganzhi")
        if self.start_date > self.end_date:
            raise ValueError("daiyun stage date range is reversed")
        if self.domain_tendency not in {"open", "constrained", "mixed", "undetermined"}:
            raise ValueError("unsupported career-stage tendency")
        if not self.signal_refs:
            raise ValueError("daiyun stage requires traceable base signals")
        if not self.applicability_conditions:
            raise ValueError("daiyun stage requires applicability conditions")


def adapt_daiyun_segment(
    segment: DaiyunSegmentSignal,
    *,
    opened_paths: tuple[PathChange, ...] = (),
    closed_paths: tuple[PathChange, ...] = (),
    amplified_paths: tuple[PathChange, ...] = (),
    suppressed_paths: tuple[PathChange, ...] = (),
    repaired_paths: tuple[PathChange, ...] = (),
    redirected_paths: tuple[PathChange, ...] = (),
    natal_relations: tuple[NatalRelation, ...] = (),
    domain_tendency: str = "undetermined",
    applicability_conditions: tuple[str, ...],
    counter_evidence: tuple[EvidenceRef, ...] = (),
) -> DaiyunStage:
    """把既有容器的基础时间信号适配为独立 ``DaiyunStage``。

    所有路径变化必须由调用方显式传入结构化裁决。自由文本 ``feature`` 与
    ``typical_domains`` 仅作为 ``unresolved_signal_refs`` 留痕，绝不自动推断路径。
    既有 ``year_range`` 是右开区间，因此转换为自然年的闭区间日期。
    """

    start_year, end_year_exclusive = segment.year_range
    if end_year_exclusive <= start_year:
        raise ValueError("segment year_range must be a non-empty half-open interval")
    base_signal = EvidenceRef(
        source="engine.yingqi.retrospective.DaiyunSegment",
        locator=f"segment[{segment.seq}].year_range",
        excerpt=f"{segment.ganzhi}:{start_year}-{end_year_exclusive}",
    )
    unresolved: list[EvidenceRef] = []
    if segment.feature.strip():
        unresolved.append(
            EvidenceRef(
                source="engine.yingqi.retrospective.DaiyunSegment",
                locator=f"segment[{segment.seq}].feature",
                excerpt=segment.feature,
            )
        )
    if segment.typical_domains:
        unresolved.append(
            EvidenceRef(
                source="engine.yingqi.retrospective.DaiyunSegment",
                locator=f"segment[{segment.seq}].typical_domains",
                excerpt="|".join(segment.typical_domains),
            )
        )
    return DaiyunStage(
        sequence=segment.seq,
        ganzhi=segment.ganzhi,
        start_date=date(start_year, 1, 1),
        end_date=date(end_year_exclusive - 1, 12, 31),
        opened_paths=opened_paths,
        closed_paths=closed_paths,
        amplified_paths=amplified_paths,
        suppressed_paths=suppressed_paths,
        repaired_paths=repaired_paths,
        redirected_paths=redirected_paths,
        natal_relations=natal_relations,
        domain_tendency=domain_tendency,
        applicability_conditions=applicability_conditions,
        counter_evidence=counter_evidence,
        signal_refs=(base_signal,),
        unresolved_signal_refs=tuple(unresolved),
    )


@dataclass(frozen=True, slots=True)
class PathTendencySuggestion:
    """大运干支对六类路径的倾向性建议；不是裁决，需调用方审核后显式传入。

    每个字段是建议受该大运影响的路径ID列表（路径由调用方定义，本函数只给十神大类）。
    open_hints/amplify_hints = 该大运干支十神属于命主"喜用"类时可能激活的路径。
    suppress_hints/close_hints = 该大运干支十神属于命主"忌神"类时可能抑制的路径。
    本函数不判断喜忌（这需要完整格局分析），只输出十神大类作为参考信号。
    """

    dayun_ganzhi: str
    stem_shishen: str
    branch_shishen_hint: str
    stem_class: str
    branch_class: str
    open_or_amplify_domains: tuple[str, ...]
    suppress_or_close_domains: tuple[str, ...]
    note: str


def suggest_daiyun_path_tendencies(
    dayun_gz: GanZhi,
    bazi: Bazi,
) -> PathTendencySuggestion:
    """根据大运干支十神给出路径倾向建议（启发式，非裁决）。

    只使用天干十神和地支主气估算，不做完整格局分析；
    调用方仍需结合格局判断才能确定喜忌，本函数只给"结构分类"。
    """

    _SHISHEN_DOMAIN_MAP = {
        "比劫": ("同业竞争", "自主创业", "团队协作"),
        "食伤": ("技术输出", "创作表达", "专业技能"),
        "财": ("财富收益", "婚恋关系", "实物资产"),
        "官杀": ("职位权力", "规则约束", "组织压力"),
        "印": ("学习积累", "文书权贵", "长辈支持"),
    }
    shishen_class_map = {
        "比肩": "比劫",
        "劫财": "比劫",
        "食神": "食伤",
        "伤官": "食伤",
        "正财": "财",
        "偏财": "财",
        "正官": "官杀",
        "七杀": "官杀",
        "正印": "印",
        "偏印": "印",
    }
    opposing_class_map = {
        "比劫": "财",
        "食伤": "官杀",
        "财": "印",
        "官杀": "比劫",
        "印": "食伤",
    }

    stem_shishen = get_shishen(dayun_gz.gan, bazi.day_master)
    branch_main_gan = ZHI_CANGGAN_TABLE[dayun_gz.zhi][0][0]
    branch_shishen = get_shishen(branch_main_gan, bazi.day_master)
    stem_class = shishen_class_map[stem_shishen]
    branch_class = shishen_class_map[branch_shishen]

    active_classes = tuple(dict.fromkeys((stem_class, branch_class)))
    opposite_classes = tuple(
        dict.fromkeys(opposing_class_map[class_name] for class_name in active_classes)
    )
    open_domains = tuple(
        domain
        for class_name in active_classes
        for domain in _SHISHEN_DOMAIN_MAP[class_name]
    )
    suppress_domains = tuple(
        domain
        for class_name in opposite_classes
        for domain in _SHISHEN_DOMAIN_MAP[class_name]
    )

    return PathTendencySuggestion(
        dayun_ganzhi=str(dayun_gz),
        stem_shishen=stem_shishen,
        branch_shishen_hint=branch_shishen,
        stem_class=stem_class,
        branch_class=branch_class,
        open_or_amplify_domains=open_domains,
        suppress_or_close_domains=suppress_domains,
        note="仅为十神结构分类的启发式信号，不构成喜忌或路径变化裁决。",
    )
