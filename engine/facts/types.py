"""engine/facts/types.py · 盘面事实层数据结构（chart-facts/v1）。

只承载客观事实与带出处的标签；不含旺衰定性、格局成败、用神喜忌或任何分数。
所有位置用统一地址 ``Addr`` 引用：
    原局  Y.s Y.b / M.s M.b / D.s D.b / H.s H.b
    大运  DY{n}.s DY{n}.b      流年  LN{year}.s LN{year}.b
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional

Addr = str
Palace = Literal["year", "month", "day", "hour"]
Scope = Literal["natal", "dayun", "liunian", "dayun+liunian"]

PALACES: tuple[Palace, ...] = ("year", "month", "day", "hour")
PALACE_PREFIX: dict[Palace, str] = {"year": "Y", "month": "M", "day": "D", "hour": "H"}


class _Dict:
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)  # type: ignore[call-overload]


# ── 出处与口径 ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SourceTag(_Dict):
    tag: str
    school: str
    source_ref: str            # "相对路径:行号"


@dataclass(frozen=True)
class ProfileSet(_Dict):
    """本次计算使用的争议口径；取值必须在 profiles.yaml 中注册且带出处。"""
    zi_shi: str = "late_zi_split"
    yin_changsheng: str = "yin_reverse"
    tu_jigong: str = "duan_split_earth"


@dataclass(frozen=True)
class Variant(_Dict):
    """另一口径下与默认口径不同的字段；无差异时不产生 Variant。"""
    axis: str
    alt_value: str
    diffs: tuple[tuple[str, Any], ...]     # (JSON Pointer, 另一口径下的值)
    alt_chart_id: Optional[str] = None     # 四柱本身改变时指向另一张盘


@dataclass(frozen=True)
class BoundaryWarning(_Dict):
    kind: Literal["late_zi", "early_zi", "near_jie", "hour_stem_next_day"]
    detail: str


# ── 柱 ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class StemSlot(_Dict):
    addr: Addr
    char: str
    wuxing: str
    yinyang: str
    ten_god: str               # 日干为 "日主"


@dataclass(frozen=True)
class HiddenStem(_Dict):
    char: str
    qi: Literal["本气", "中气", "余气"]
    ten_god: str


@dataclass(frozen=True)
class BranchSlot(_Dict):
    addr: Addr
    char: str
    wuxing: str
    yinyang: str
    hidden: tuple[HiddenStem, ...]
    main_ten_god: str


@dataclass(frozen=True)
class SelfSit(_Dict):
    stem_changsheng: str                               # 随 yin_changsheng 口径
    marks: tuple[str, ...]                             # 坐禄 / 坐羊刃 / 坐长生 / 坐墓
    stem_branch_relation: Literal["干生支", "支生干", "干克支", "支克干", "同气"]
    rooted_in_own_branch: tuple[str, ...]              # 本支中与干同五行的藏干气位


@dataclass(frozen=True)
class Pillar(_Dict):
    index: int
    palace: Palace
    ganzhi: str
    stem: StemSlot
    branch: BranchSlot
    nayin: str
    xun: str
    self_sit: SelfSit
    source_tags: tuple[SourceTag, ...] = ()


@dataclass(frozen=True)
class KongWang(_Dict):
    by_day_xun: tuple[str, str]
    by_year_xun: tuple[str, str]
    hits: tuple[tuple[Addr, Literal["day", "year"]], ...]


# ── 岁运 ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class QiyunVariant(_Dict):
    method: Literal["mangpai_rough", "precise"]
    start_age: float
    start_datetime: Optional[str]
    source_ref: str


@dataclass(frozen=True)
class DayunStep(_Dict):
    index: int                     # 1 起
    ganzhi: str
    start_year: Optional[int]      # lunar-python 精确法；直接输入四柱且未给年份时为 None
    end_year: Optional[int]        # 含当年


@dataclass(frozen=True)
class Cycles(_Dict):
    direction: Literal["顺", "逆"]
    qiyun: tuple[QiyunVariant, ...]
    dayun: tuple[DayunStep, ...]


# ── 顶层 ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class InputEcho(_Dict):
    mode: Literal["solar", "pillars"]
    solar_datetime: Optional[str]
    true_solar_corrected: Optional[bool]       # 调用方声明，引擎不核验
    supplied_dayun: Optional[tuple[str, ...]]


@dataclass(frozen=True)
class ChartFacts(_Dict):
    schema_version: str
    chart_id: str
    input: InputEcho
    profile: ProfileSet
    gender: Literal["乾", "坤"]
    day_master: str
    pillars: tuple[Pillar, Pillar, Pillar, Pillar]
    kongwang: KongWang
    cycles: Optional[Cycles]
    boundary_warnings: tuple[BoundaryWarning, ...] = ()
    variants: tuple[Variant, ...] = ()


# ── 关系图 ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Edge(_Dict):
    id: str
    layer: Literal["stem", "branch", "stem_branch"]
    kind: str
    members: tuple[Addr, ...]          # 有方向的关系（sheng/ke）按 from→to
    chars: tuple[str, ...]
    scope: Scope
    distance: Optional[int]            # 原局柱序差；同柱 0；涉及岁运为 None
    between: tuple[Addr, ...]          # 两成员之间同层的原局地址，只列不判
    group: Optional[str] = None
    completeness: Optional[str] = None
    attrs: dict[str, Any] = field(default_factory=dict)
    source_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class RuleHit(_Dict):
    rule: str
    effect: Literal["入墓", "一般作拱局", "不论入墓"]
    source_ref: str


@dataclass(frozen=True)
class MukuCandidate(_Dict):
    addr: Addr
    char: str
    wuxing: str
    char_class: Literal["四生支", "四正支", "土支", "天干"]
    same_wuxing_count: int
    rule_hits: tuple[RuleHit, ...]
    excluded: bool                         # 有细则明确"不论入墓"
    requires_judgment: tuple[str, ...]
    damaged_by_edges: tuple[str, ...]      # 指向该字的冲/穿/破/刑（及天干克、冲）边
    ku_link_edges: tuple[str, ...]         # 该字与本库之间的三合/拱边


@dataclass(frozen=True)
class MukuFact(_Dict):
    addr: Addr
    branch: str
    ku_of: tuple[str, ...]                 # 辰在 duan_split_earth 口径下为 ("水","土")
    hidden: tuple[HiddenStem, ...]
    candidates: tuple[MukuCandidate, ...]
    openers: tuple[str, ...]               # 成员含本库的冲、刑边
    chuan_po: tuple[str, ...]              # 成员含本库的穿、破边
    binders: tuple[str, ...]               # 成员含本库的合边（六合、暗合、三合、三会）
    stem_he_on_pillar: tuple[str, ...]     # 本柱天干参与的五合边（任派"合住控制库"）
    self_sit_excluded: tuple[Addr, ...]    # 同柱天干坐本五行墓，按任派(四)不论入墓


@dataclass(frozen=True)
class RelationGraph(_Dict):
    schema_version: str
    chart_id: str
    profile: ProfileSet
    nodes: tuple[tuple[Addr, str], ...]
    edges: tuple[Edge, ...]
    pair_index: dict[str, tuple[str, ...]]
    muku: tuple[MukuFact, ...]
    variants: tuple[Variant, ...] = ()


# ── 原子能量事实 ───────────────────────────────────────────────────────────

Qi = Literal["本气", "中气", "余气"]
FiveRelation = Literal["同我", "生我", "我生", "我克", "克我"]


@dataclass(frozen=True)
class Root(_Dict):
    """某天干在某地支藏干中的一处根气或印气（只记事实，不折算力量）。"""
    addr: Addr                 # 地支地址，例如 "M.b"
    hidden_char: str
    qi: Qi
    changsheng: str            # 该天干在该支的十二长生状态，随 yin_changsheng 口径
    distance: int              # 与该天干所在柱的柱序差 0..3


@dataclass(frozen=True)
class SilingFact(_Dict):
    """人元司令分野：出生时刻落在月令哪一藏干用事。"""
    stem: str
    source_ref: str


@dataclass(frozen=True)
class StemStrengthFacts(_Dict):
    addr: Addr
    char: str
    wuxing: str
    month_changsheng: str
    month_main_qi_relation: FiveRelation       # 月令本气对该干：同我 / 生我 / 我生 / 我克 / 克我
    siling: Optional[SilingFact]
    roots: tuple[Root, ...]                    # 同五行藏干
    resource_in_branches: tuple[Root, ...]     # 生该干的藏干（印气），不混入 roots
    tou_same_wuxing: tuple[Addr, ...]          # 其余三柱天干同五行，排除自身所在柱
    tou_resource: tuple[Addr, ...]             # 其余三柱天干生该干者


@dataclass(frozen=True)
class LayeredCount(_Dict):
    """按位置分层的字数，不加权、不归一化。"""
    stems: int
    main_qi: int
    mid_qi: int
    residual_qi: int
    month_main_qi: bool                        # 月令本气是否属于本组


@dataclass(frozen=True)
class TiaohouHit(_Dict):
    day_stem: str
    month_branch: str
    listed_stems: tuple[str, ...]              # 《穷通宝鉴》原文所列用字，按原文顺序
    present: dict[str, tuple[Addr, ...]]       # 盘中出现位置：.s 为透干，.b 为藏于该支
    raw_excerpt: str
    source_ref: str


@dataclass(frozen=True)
class ClimateFacts(_Dict):
    month_branch: str
    season: Literal["春", "夏", "秋", "冬"]
    wuxing_layered: dict[str, LayeredCount]    # 木火土金水，含日干
    dry_earth: tuple[Addr, ...]                # 戌、未
    wet_earth: tuple[Addr, ...]                # 辰、丑
    tiaohou_lookup: Optional[TiaohouHit]


@dataclass(frozen=True)
class StrengthFacts(_Dict):
    schema_version: str
    chart_id: str
    profile: ProfileSet
    day_master: StemStrengthFacts
    stems: dict[Addr, StemStrengthFacts]       # Y.s / M.s / H.s
    camp_counts: dict[str, LayeredCount]       # 印比 / 食伤 / 财 / 官杀 / 比劫 / 印；不含日干本身
    climate: ClimateFacts
    variants: tuple[Variant, ...] = ()
