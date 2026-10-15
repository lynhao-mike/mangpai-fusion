"""engine/facts/relation_graph.py · 带位置拓扑的关系图 RelationGraph。

每条边只记录客观事实：关系种类、参与地址、柱序距离、中间间隔的地址、组完整度、
客观条件。不消解"合解冲""贪合忘冲"之类的优先级，不判断合化成败、库开闭。

墓库层（MukuFact）按任付红《地支四墓库的使用方法》五条细则逐条标注命中，
细则要求"需判断"的地方原样标出，交给调用方（LLM）依据原文裁决。
"""
from __future__ import annotations

from dataclasses import replace
from itertools import combinations
from typing import Any, Iterable, Optional

from engine.facts.chart_facts import (
    REF_KAISHAN,
    alternatives,
    json_diff,
    validate_profile,
    wuxing_relation,
)
from engine.facts.types import (
    Addr,
    ChartFacts,
    Edge,
    HiddenStem,
    MukuCandidate,
    MukuFact,
    ProfileSet,
    RelationGraph,
    RuleHit,
    Variant,
)
from engine.predicates.cycles import year_ganzhi_of_lichun_year
from engine.predicates.types import GAN_TO_WUXING, ZHI_CANGGAN_TABLE, ZHI_TO_WUXING

SCHEMA_VERSION = "relation-graph/v1"

REF_REN_MUKU = "sources/ren/MinerU_markdown_16、任付红-民间实用八字-地支四墓库的使用方法_2056026785004060672.md"
REF_YANG_BASE = "sources/yang/MinerU_markdown_03清娟盲派八字命理讲座（基础篇）_2056033625439920128.md"
REF_GAO_XIANG = "sources/gao/2018弟子班_象法篇_83页.md"
REF_REN_18 = "sources/ren/MinerU_markdown_任付红十八道法门_2056029302244958208.md"
REF_D01 = "theory/raw/duan/d01-deep-read.md"

_NATAL_ORDER = {"Y": 0, "M": 1, "D": 2, "H": 3}

# ── 关系表 ──────────────────────────────────────────────────────────────────
_GAN_HE = {frozenset("甲己"): "土", frozenset("乙庚"): "金", frozenset("丙辛"): "水",
           frozenset("丁壬"): "木", frozenset("戊癸"): "火"}
_GAN_CHONG = {frozenset("甲庚"), frozenset("乙辛"), frozenset("丙壬"), frozenset("丁癸")}
_LIUHE = {frozenset("子丑"): "土", frozenset("寅亥"): "木", frozenset("卯戌"): "火",
          frozenset("辰酉"): "金", frozenset("巳申"): "水", frozenset("午未"): None}
_CHONG = {frozenset(p) for p in ("子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥")}
_CHUAN = {frozenset(p) for p in ("子未", "丑午", "寅巳", "卯辰", "申亥", "酉戌")}
_PO_CLASSIC = {frozenset(p) for p in ("子酉", "卯午", "辰丑", "未戌", "寅亥", "巳申")}
_PO_DUAN = {frozenset(p) for p in ("子卯", "卯午", "午酉")}
_ANHE = {frozenset("寅丑"), frozenset("午亥"), frozenset("卯申")}
_ANHE_REN_EXTRA = {frozenset("子巳")}
_XING_GROUPS = ("寅巳申", "丑戌未")
_HUXING = frozenset("子卯")
_ZIXING = frozenset("辰午酉亥")
# 三合：(生, 旺, 墓, 化神)
_SANHE = (("申", "子", "辰", "水"), ("亥", "卯", "未", "木"),
          ("寅", "午", "戌", "火"), ("巳", "酉", "丑", "金"))
_SANHUI = (("寅卯辰", "木"), ("巳午未", "火"), ("申酉戌", "金"), ("亥子丑", "水"))

# 同柱干支自合（段派《开山之作》:1338）
_GANZHI_ZIHE = {"丁亥", "己亥", "辛巳", "癸巳", "壬午", "甲午", "戊子", "丙戌", "壬戌"}
_ZIHE_BRANCH_CONTROLS = {"丁亥", "己亥", "辛巳", "癸巳"}
_ZIHE_NEEDS_XING = {"丙戌", "壬戌"}

# 墓库
_MU_BRANCH = {"辰": "水", "戌": "火", "丑": "金", "未": "木"}
_SI_SHENG = frozenset("寅申巳亥")
_SI_ZHENG = frozenset("子午卯酉")
_DAMAGE_BRANCH_KINDS = frozenset({"chong", "chuan", "po", "xing"})
_OPENER_KINDS = frozenset({"chong", "xing"})
_CHUAN_PO_KINDS = frozenset({"chuan", "po"})
_BINDER_KINDS = frozenset({"liuhe", "zhi_anhe"})
_BINDER_GROUP_KINDS = frozenset({"sanhe", "sanhui"})   # 只有三字齐全才算合住


# ── 节点 ────────────────────────────────────────────────────────────────────

def _nodes(chart: ChartFacts, dayun_index: Optional[int], liunian_year: Optional[int]) -> list[tuple[Addr, str]]:
    nodes: list[tuple[Addr, str]] = []
    for p in chart.pillars:
        nodes += [(p.stem.addr, p.stem.char), (p.branch.addr, p.branch.char)]
    if dayun_index is not None:
        if chart.cycles is None:
            raise ValueError("该盘没有大运信息，不能指定 dayun_index")
        step = next((s for s in chart.cycles.dayun if s.index == dayun_index), None)
        if step is None:
            raise ValueError(f"大运序号 {dayun_index} 不存在（已排 {[s.index for s in chart.cycles.dayun]}）")
        nodes += [(f"DY{dayun_index}.s", step.ganzhi[0]), (f"DY{dayun_index}.b", step.ganzhi[1])]
    if liunian_year is not None:
        gz = str(year_ganzhi_of_lichun_year(liunian_year))
        nodes += [(f"LN{liunian_year}.s", gz[0]), (f"LN{liunian_year}.b", gz[1])]
    return nodes


def _natal_index(addr: Addr) -> Optional[int]:
    return _NATAL_ORDER.get(addr.split(".", 1)[0])


def _layer_of(addr: Addr) -> str:
    return addr.rsplit(".", 1)[1]


def _scope(addrs: Iterable[Addr]) -> str:
    heads = {a.split(".", 1)[0][:2] for a in addrs}
    has_dy, has_ln = "DY" in heads, "LN" in heads
    if has_dy and has_ln:
        return "dayun+liunian"
    if has_dy:
        return "dayun"
    if has_ln:
        return "liunian"
    return "natal"


class _Builder:
    def __init__(self, nodes: list[tuple[Addr, str]]):
        self.nodes = nodes
        self.char = dict(nodes)
        self.edges: list[Edge] = []

    def stems(self) -> list[Addr]:
        return [a for a, _ in self.nodes if _layer_of(a) == "s"]

    def branches(self) -> list[Addr]:
        return [a for a, _ in self.nodes if _layer_of(a) == "b"]

    def _geometry(self, members: tuple[Addr, ...]) -> tuple[Optional[int], tuple[Addr, ...]]:
        idx = [_natal_index(a) for a in members]
        if any(i is None for i in idx):
            return None, ()
        lo, hi = min(idx), max(idx)  # type: ignore[type-var]
        if len({_layer_of(a) for a in members}) > 1:
            return hi - lo, ()
        layer = _layer_of(members[0])
        between = tuple(
            a for a, _ in self.nodes
            if _layer_of(a) == layer and _natal_index(a) is not None
            and lo < _natal_index(a) < hi and a not in members  # type: ignore[operator]
        )
        return hi - lo, between

    def add(self, layer: str, kind: str, members: tuple[Addr, ...], *, group: Optional[str] = None,
            completeness: Optional[str] = None, attrs: Optional[dict[str, Any]] = None,
            source_refs: tuple[str, ...] = ()) -> Edge:
        distance, between = self._geometry(members)
        edge = Edge(
            id=f"e{len(self.edges) + 1:03d}", layer=layer, kind=kind, members=members,  # type: ignore[arg-type]
            chars=tuple(self.char[a] for a in members), scope=_scope(members),  # type: ignore[arg-type]
            distance=distance, between=between, group=group, completeness=completeness,
            attrs=attrs or {}, source_refs=source_refs,
        )
        self.edges.append(edge)
        return edge


# ── 天干层 ──────────────────────────────────────────────────────────────────

def _month_branch(chart: ChartFacts) -> str:
    return chart.pillars[1].branch.char


def _stem_edges(b: _Builder, chart: ChartFacts) -> None:
    stems = b.stems()
    month = _month_branch(chart)
    for x, y in combinations(stems, 2):
        cx, cy = b.char[x], b.char[y]
        wx, wy = GAN_TO_WUXING[cx], GAN_TO_WUXING[cy]
        pair = frozenset((cx, cy))
        if pair in _GAN_HE:
            huashen = _GAN_HE[pair]
            others = [s for s in stems if s not in (x, y)]
            b.add("stem", "wuhe", (x, y), attrs={
                "huashen": huashen,
                "month_branch_wuxing_is_huashen": ZHI_TO_WUXING[month] == huashen,
                "month_hidden_has_huashen": any(GAN_TO_WUXING[g] == huashen for g, _, _ in ZHI_CANGGAN_TABLE[month]),
                "huashen_stem_tou": [s for s in others if GAN_TO_WUXING[b.char[s]] == huashen],
                "huashen_ke_stems": [s for s in others if wuxing_relation(GAN_TO_WUXING[b.char[s]], huashen) == "克"],
                "competing": [s for s in others if b.char[s] in (cx, cy)],
            })
        if pair in _GAN_CHONG:
            b.add("stem", "stem_chong", (x, y),
                  source_refs=(f"{REF_KAISHAN}:618", f"{REF_YANG_BASE}:198"))
        rel = wuxing_relation(wx, wy)
        if rel == "同":
            b.add("stem", "same_qi", (x, y))
        elif rel == "生":
            b.add("stem", "sheng", (x, y))
        elif rel == "被生":
            b.add("stem", "sheng", (y, x))
        elif rel == "克":
            b.add("stem", "ke", (x, y))
        else:
            b.add("stem", "ke", (y, x))


# ── 地支层 ──────────────────────────────────────────────────────────────────

def _anhe_pairs(za: str, zb: str) -> list[list[str]]:
    return [[ga, gb] for ga, _, _ in ZHI_CANGGAN_TABLE[za] for gb, _, _ in ZHI_CANGGAN_TABLE[zb]
            if frozenset((ga, gb)) in _GAN_HE]


def _branch_pair_edges(b: _Builder) -> None:
    branches = b.branches()
    present = {a: b.char[a] for a in branches}
    chars_present = set(present.values())
    for x, y in combinations(branches, 2):
        cx, cy = b.char[x], b.char[y]
        pair = frozenset((cx, cy))
        if cx == cy:
            if cx in _ZIXING:
                b.add("branch", "xing", (x, y), group=cx + cx, completeness="zixing")
            continue
        if pair in _CHONG:
            b.add("branch", "chong", (x, y))
        if pair in _LIUHE:
            b.add("branch", "liuhe", (x, y), attrs={"huashen": _LIUHE[pair]})
        if pair in _CHUAN:
            b.add("branch", "chuan", (x, y))
        systems = [s for s, table in (("classic", _PO_CLASSIC), ("duan", _PO_DUAN)) if pair in table]
        if systems:
            refs = []
            if "classic" in systems:
                refs.append(f"{REF_GAO_XIANG}:425")
            if "duan" in systems:
                refs.append(f"{REF_KAISHAN}:860")
            b.add("branch", "po", (x, y), attrs={"systems": systems}, source_refs=tuple(refs))
        if pair in _ANHE or pair in _ANHE_REN_EXTRA:
            ref = f"{REF_KAISHAN}:814" if pair in _ANHE else f"{REF_REN_18}:152"
            b.add("branch", "zhi_anhe", (x, y), attrs={"hidden_he": _anhe_pairs(cx, cy)}, source_refs=(ref,))
        if pair == _HUXING:
            b.add("branch", "xing", (x, y), group="子卯", completeness="huxing")
        for grp in _XING_GROUPS:
            if pair <= set(grp):
                b.add("branch", "xing", (x, y), group=grp, completeness="partial",
                      attrs={"group_full": set(grp) <= chars_present})
        for sheng, wang, mu, hua in _SANHE:
            if not pair <= {sheng, wang, mu}:
                continue
            if pair == frozenset((sheng, wang)):
                comp = "half_sheng"
            elif pair == frozenset((wang, mu)):
                comp = "half_mu"
            else:
                comp = "gong"
            b.add("branch", "sanhe", (x, y), group=sheng + wang + mu, completeness=comp,
                  attrs={"huashen": hua, "center": wang, "center_present": wang in chars_present})
        for grp, wx in _SANHUI:
            if pair <= set(grp):
                b.add("branch", "sanhui", (x, y), group=grp, completeness="partial",
                      attrs={"wuxing": wx, "group_full": set(grp) <= chars_present})


def _group_members(b: _Builder, chars: str) -> list[tuple[Addr, ...]]:
    """组内每个字取一个地址的全部组合（字重复出现时会有多组）。"""
    pools = [[a for a in b.branches() if b.char[a] == ch] for ch in chars]
    if any(not p for p in pools):
        return []
    out: list[tuple[Addr, ...]] = [()]
    for pool in pools:
        out = [prefix + (a,) for prefix in out for a in pool]
    return out


def _branch_group_edges(b: _Builder) -> None:
    for sheng, wang, mu, hua in _SANHE:
        for members in _group_members(b, sheng + wang + mu):
            b.add("branch", "sanhe", members, group=sheng + wang + mu, completeness="full",
                  attrs={"huashen": hua, "center": wang})
    for grp, wx in _SANHUI:
        for members in _group_members(b, grp):
            b.add("branch", "sanhui", members, group=grp, completeness="full", attrs={"wuxing": wx})
    for grp in _XING_GROUPS:
        for members in _group_members(b, grp):
            b.add("branch", "xing", members, group=grp, completeness="full")


# ── 干支层（同柱自合）───────────────────────────────────────────────────────

def _ganzhi_edges(b: _Builder) -> None:
    for s in b.stems():
        head = s.split(".", 1)[0]
        br = f"{head}.b"
        if br not in b.char:
            continue
        gz = b.char[s] + b.char[br]
        if gz not in _GANZHI_ZIHE:
            continue
        hidden = [g for g, _, _ in ZHI_CANGGAN_TABLE[gz[1]] if frozenset((gz[0], g)) in _GAN_HE]
        attrs: dict[str, Any] = {
            "hidden_partner": hidden,
            "branch_controls_stem": gz in _ZIHE_BRANCH_CONTROLS,
        }
        refs = [f"{REF_KAISHAN}:1338"]
        if gz in _ZIHE_NEEDS_XING:
            wei = [a for a in b.branches() if b.char[a] == "未"]
            chen = [a for a in b.branches() if b.char[a] == "辰"]
            attrs.update({"requires_xing": "戌未刑", "wei_present": wei, "chen_chong_present": chen})
            refs.append(f"{REF_D01}:373")
        b.add("stem_branch", "ganzhi_zihe", (s, br), attrs=attrs, source_refs=tuple(refs))


# ── 墓库层 ──────────────────────────────────────────────────────────────────

def _ku_of(branch: str, profile: ProfileSet) -> tuple[str, ...]:
    base = _MU_BRANCH[branch]
    if profile.tu_jigong == "duan_split_earth" and branch in ("辰", "戌"):
        return (base, "土")
    if profile.tu_jigong == "fire_earth" and branch == "戌":
        return (base, "土")
    return (base,)


def _wuxing_of(addr: Addr, char: str) -> str:
    return GAN_TO_WUXING[char] if _layer_of(addr) == "s" else ZHI_TO_WUXING[char]


def _edges_with(edges: list[Edge], addr: Addr, kinds: frozenset[str]) -> list[Edge]:
    return [e for e in edges if addr in e.members and e.kind in kinds]


def _damage_edges(edges: list[Edge], addr: Addr) -> tuple[str, ...]:
    if _layer_of(addr) == "b":
        return tuple(e.id for e in _edges_with(edges, addr, _DAMAGE_BRANCH_KINDS))
    hits = [e for e in edges if addr in e.members and (
        e.kind == "stem_chong" or (e.kind == "ke" and e.members[1] == addr))]
    return tuple(e.id for e in hits)


def _rule(n: str, effect: str, line: int, text: str) -> RuleHit:
    return RuleHit(rule=f"({n}){text}", effect=effect, source_ref=f"{REF_REN_MUKU}:{line}")  # type: ignore[arg-type]


def _muku(b: _Builder, chart: ChartFacts, profile: ProfileSet) -> tuple[MukuFact, ...]:
    natal = [(a, c) for a, c in b.nodes if _natal_index(a) is not None]
    edges = b.edges
    chong_chou_wei = any(e.kind == "chong" and set(e.chars) == {"丑", "未"} for e in edges if e.scope == "natal")
    facts: list[MukuFact] = []
    for p in chart.pillars:
        ku_addr, ku = p.branch.addr, p.branch.char
        if ku not in _MU_BRANCH:
            continue
        ku_of = _ku_of(ku, profile)
        candidates: list[MukuCandidate] = []
        self_excluded: list[Addr] = []
        for wx in ku_of:
            pool = [(a, c) for a, c in natal if a != ku_addr and _wuxing_of(a, c) == wx]
            if wx == "土":
                # 土墓：天干之土墓在戌；地支丑未入辰墓（duan_split_earth 才有后者）
                if ku == "戌":
                    pool = [(a, c) for a, c in pool if _layer_of(a) == "s"]
                else:
                    pool = [(a, c) for a, c in pool if c in ("丑", "未")]
            count = len([1 for a, c in natal if a != ku_addr and _wuxing_of(a, c) == wx])
            for addr, char in pool:
                hits: list[RuleHit] = []
                judgment: list[str] = []
                excluded = False
                is_stem = _layer_of(addr) == "s"
                same_pillar = addr.split(".", 1)[0] == ku_addr.split(".", 1)[0]
                if is_stem and same_pillar:
                    hits.append(_rule("四", "不论入墓", 107, "天干坐墓不以入墓论"))
                    excluded = True
                    self_excluded.append(addr)
                elif not is_stem and char in _SI_SHENG:
                    hits.append(_rule("一", "入墓", 29, "寅申巳亥见各自墓库为入墓"))
                elif not is_stem and char in _SI_ZHENG:
                    hits.append(_rule("二", "一般作拱局", 61, "子午卯酉见各自墓一般作拱局"))
                    judgment.append("四正支见墓一般作拱局，极弱（被制受伤）才入墓，需判断（:63、:71）")
                elif wx == "土" and not is_stem:
                    hits.append(_rule("五", "入墓", 111, "丑入辰墓、未也入辰墓"))
                    if chong_chou_wei:
                        hits.append(_rule("五", "不论入墓", 111, "丑未辰齐见因丑未冲不论入辰墓"))
                        excluded = True
                if wx != "土" and count >= 2 and not excluded:
                    hits.append(_rule("三", "入墓", 73, f"同五行{count}字见墓则入，不作拱看"))
                if not hits:
                    continue  # 单个天干且不属多而入墓：五条细则均未覆盖
                if is_stem and wx == "土" and not excluded:
                    judgment.append("天干戊己归戌墓依 tu_jigong 口径，任派五条细则未直接覆盖")
                if is_stem and not excluded and count < 2:
                    judgment.append("单个天干见墓，五条细则未直接覆盖")
                ku_link = tuple(e.id for e in edges if e.kind == "sanhe" and addr in e.members and ku_addr in e.members)
                candidates.append(MukuCandidate(
                    addr=addr, char=char, wuxing=wx,
                    char_class="天干" if is_stem else ("四生支" if char in _SI_SHENG else "四正支" if char in _SI_ZHENG else "土支"),  # type: ignore[arg-type]
                    same_wuxing_count=count, rule_hits=tuple(hits), excluded=excluded,
                    requires_judgment=tuple(judgment), damaged_by_edges=_damage_edges(edges, addr),
                    ku_link_edges=ku_link,
                ))
        stem_addr = p.stem.addr
        facts.append(MukuFact(
            addr=ku_addr, branch=ku, ku_of=ku_of,
            hidden=p.branch.hidden,
            candidates=tuple(candidates),
            openers=tuple(e.id for e in _edges_with(edges, ku_addr, _OPENER_KINDS)),
            chuan_po=tuple(e.id for e in _edges_with(edges, ku_addr, _CHUAN_PO_KINDS)),
            binders=tuple(
                e.id for e in edges if ku_addr in e.members and (
                    e.kind in _BINDER_KINDS
                    or (e.kind in _BINDER_GROUP_KINDS and e.completeness == "full"))
            ),
            stem_he_on_pillar=tuple(e.id for e in edges if e.kind == "wuhe" and stem_addr in e.members),
            self_sit_excluded=tuple(self_excluded),
        ))
    return tuple(facts)


# ── 入口 ────────────────────────────────────────────────────────────────────

def _pair_index(edges: list[Edge]) -> dict[str, tuple[str, ...]]:
    index: dict[str, list[str]] = {}
    for e in edges:
        index.setdefault("|".join(sorted(e.members)), []).append(e.id)
    return {k: tuple(v) for k, v in index.items()}


def _build_graph(chart: ChartFacts, profile: ProfileSet, dayun_index: Optional[int],
                 liunian_year: Optional[int]) -> RelationGraph:
    b = _Builder(_nodes(chart, dayun_index, liunian_year))
    _stem_edges(b, chart)
    _branch_pair_edges(b)
    _branch_group_edges(b)
    _ganzhi_edges(b)
    return RelationGraph(
        schema_version=SCHEMA_VERSION, chart_id=chart.chart_id, profile=profile,
        nodes=tuple(b.nodes), edges=tuple(b.edges), pair_index=_pair_index(b.edges),
        muku=_muku(b, chart, profile),
    )


def build_relation_graph(
    chart: ChartFacts,
    *,
    dayun_index: Optional[int] = None,
    liunian_year: Optional[int] = None,
) -> RelationGraph:
    """构造关系图。墓库口径（tu_jigong）的另一取值只在墓库结果不同时写进 variants。"""
    profile = validate_profile(chart.profile)
    graph = _build_graph(chart, profile, dayun_index, liunian_year)
    base_muku = [m.to_dict() for m in graph.muku]
    variants: list[Variant] = []
    for alt in alternatives("tu_jigong", profile.tu_jigong):
        other = _build_graph(chart, replace(profile, tu_jigong=alt), dayun_index, liunian_year)
        diffs = json_diff(base_muku, [m.to_dict() for m in other.muku], "/muku")
        if diffs:
            variants.append(Variant("tu_jigong", alt, tuple(diffs)))
    return replace(graph, variants=tuple(variants))


def edges_between(graph: RelationGraph, *addrs: Addr) -> list[Edge]:
    """成员恰好是给定地址集合的边。"""
    key = "|".join(sorted(addrs))
    ids = set(graph.pair_index.get(key, ()))
    return [e for e in graph.edges if e.id in ids]


def edge_by_id(graph: RelationGraph, edge_id: str) -> Edge:
    return next(e for e in graph.edges if e.id == edge_id)


def muku_at(graph: RelationGraph, addr: Addr) -> MukuFact:
    return next(m for m in graph.muku if m.addr == addr)


__all__ = ["build_relation_graph", "edge_by_id", "edges_between", "muku_at"]
