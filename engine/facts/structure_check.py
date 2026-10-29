"""engine/facts/structure_check.py · 第 4 层 StructureCheck（structure-check/v1）。

两部分：
1. 目录驱动的构成要件核对器：``data/structures_mvp.yaml`` 逐条列出格局的要件 / 破格 / 救应，
   每条由一个受控小谓词（或 any / all 组合）核对，输出 met / unmet / not_evaluable / needs_judgment
   与证据地址或 Edge.id。凡涉及力量对比一律给 needs_judgment，交调用方裁决。
2. 段派体用视图与做功候选扫描（《开山之作》:1312-1317，M1-D-005..008、M1-D-116..121）。

刻意不输出：成格 / 破格结论、分数、做功层数、富贵档次。
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
from pathlib import Path
from typing import Any, Callable, Literal, Optional

import yaml

from engine.facts.chart_facts import REF_KAISHAN, _LU, _YANG_REN, binzhu_side, wuxing_relation
from engine.facts.types import Addr, ChartFacts, Edge, RelationGraph, StrengthFacts, _Dict
from engine.predicates.palace import get_shishen
from engine.predicates.types import GAN_TO_WUXING, ZHI_CANGGAN_TABLE, ZHI_TO_WUXING

SCHEMA_VERSION = "structure-check/v1"
CATALOG_PATH = Path(__file__).parent / "data" / "structures_mvp.yaml"
REF_D10 = "theory/raw/duan/d10-theory.md"

Status = Literal["met", "unmet", "not_evaluable", "needs_judgment"]
ItemKind = Literal["requirement", "breaker", "rescuer"]
TiYong = Literal["体", "用", "双属"]


# ── 数据结构 ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CheckItem(_Dict):
    id: str
    kind: ItemKind
    text: str
    status: Status
    evidence: tuple[str, ...]          # Addr 或 Edge.id


@dataclass(frozen=True)
class StructureCheck(_Dict):
    structure_id: str
    school: str
    display_name_zh: str
    source_refs: tuple[str, ...]
    items: tuple[CheckItem, ...]
    judgment_points: tuple[str, ...]


@dataclass(frozen=True)
class BinzhuReading(_Dict):
    layer: int                                   # 段派宾主 1-4 层
    sides: tuple[str, ...]                       # 与 members 一一对应：主 / 宾
    direction: Literal["正向", "反向", "同在主位", "同在宾位", "需判断"]


@dataclass(frozen=True)
class ZuogongCandidate(_Dict):
    mode: Literal["制用", "化用", "生泄用", "合用", "墓用", "sheng"]
    relation_kind: str                           # 边 kind；推得关系为 "sheng(main_qi)"；墓库为 "muku"
    edge_id: Optional[str]                       # 推得关系与墓库候选为 None
    members: tuple[Addr, ...]
    chars: tuple[str, ...]
    ten_gods: tuple[str, ...]
    tiyong: tuple[str, ...]
    actor: Optional[Addr]                        # 有方向关系（克/生/入墓）的发出方
    binzhu: tuple[BinzhuReading, ...]
    distance: Optional[int]
    related_edges: tuple[str, ...]
    source_refs: tuple[str, ...]
    notes: tuple[str, ...]


# ── 十神与角色 ──────────────────────────────────────────────────────────────

TEN_GODS = frozenset({"比肩", "劫财", "食神", "伤官", "偏财", "正财", "七杀", "正官", "偏印", "正印", "日主"})
_ROLE_ALIASES: dict[str, frozenset[str]] = {
    "财": frozenset({"正财", "偏财"}),
    "官杀": frozenset({"正官", "七杀"}),
    "印": frozenset({"正印", "偏印"}),
    "枭": frozenset({"偏印"}),
    "比劫": frozenset({"比肩", "劫财"}),
    "食伤": frozenset({"食神", "伤官"}),
}
_TIYONG: dict[str, TiYong] = {
    "日主": "体", "比肩": "体", "劫财": "体", "正印": "体", "偏印": "体",
    "正财": "用", "偏财": "用", "正官": "用", "七杀": "用",
    "食神": "双属", "伤官": "双属",
}


def roles(role: str) -> frozenset[str]:
    if role in _ROLE_ALIASES:
        return _ROLE_ALIASES[role]
    if role in TEN_GODS:
        return frozenset({role})
    raise ValueError(f"未注册的十神角色：{role!r}")


def _layer(addr: Addr) -> str:
    return addr.rsplit(".", 1)[1]


def _ten_god(addr: Addr, char: str, day_master: str) -> str:
    if addr == "D.s":
        return "日主"
    if _layer(addr) == "s":
        return get_shishen(char, day_master)
    return get_shishen(ZHI_CANGGAN_TABLE[char][0][0], day_master)


# ── 谓词上下文 ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class _Ctx:
    chart: ChartFacts
    graph: RelationGraph
    strength: Optional[StrengthFacts]

    @property
    def dm(self) -> str:
        return self.chart.day_master

    def tou(self, role: str) -> list[Addr]:
        rs = roles(role)
        return [p.stem.addr for p in self.chart.pillars if p.index != 2 and p.stem.ten_god in rs]

    def hidden_in(self, role: str) -> list[Addr]:
        rs = roles(role)
        return [p.branch.addr for p in self.chart.pillars if any(h.ten_god in rs for h in p.branch.hidden)]

    def node_god(self, addr: Addr) -> str:
        return _ten_god(addr, dict(self.graph.nodes)[addr], self.dm)


Result = tuple[Status, tuple[str, ...]]


def _hit(evidence: list[str]) -> Result:
    uniq = tuple(dict.fromkeys(evidence))
    return ("met", uniq) if uniq else ("unmet", ())


# ── 受控谓词表 ──────────────────────────────────────────────────────────────

def month_main_role(ctx: _Ctx, role: str) -> Result:
    """月令本气属于该角色。"""
    return _hit(["M.b"] if ctx.chart.pillars[1].branch.main_ten_god in roles(role) else [])


def month_hidden_role(ctx: _Ctx, role: str) -> Result:
    """月令任一藏干属于该角色。"""
    return _hit(["M.b"] if any(h.ten_god in roles(role) for h in ctx.chart.pillars[1].branch.hidden) else [])


def month_hidden_tou(ctx: _Ctx, role: str) -> Result:
    """月令藏干中属该角色者透出于年 / 月 / 时干。"""
    month = ctx.chart.pillars[1].branch
    chars = {h.char for h in month.hidden if h.ten_god in roles(role)}
    stems = [p.stem.addr for p in ctx.chart.pillars if p.index != 2 and p.stem.char in chars]
    return _hit(["M.b", *stems] if stems else [])


def role_tou(ctx: _Ctx, role: str) -> Result:
    return _hit(ctx.tou(role))


def role_present(ctx: _Ctx, role: str) -> Result:
    """透干或藏于任一地支。"""
    return _hit(ctx.tou(role) + ctx.hidden_in(role))


def role_absent(ctx: _Ctx, role: str, tou_only: bool = True) -> Result:
    found = ctx.tou(role) + ([] if tou_only else ctx.hidden_in(role))
    return ("unmet", tuple(found)) if found else ("met", ())


def role_rooted_tou(ctx: _Ctx, role: str) -> Result:
    """该角色透干，且地支藏有同五行之气（通根）。"""
    evidence: list[str] = []
    for addr in ctx.tou(role):
        wx = GAN_TO_WUXING[dict(ctx.graph.nodes)[addr]]
        rooted = [p.branch.addr for p in ctx.chart.pillars
                  if any(GAN_TO_WUXING[h.char] == wx for h in p.branch.hidden)]
        if rooted:
            evidence += [addr, *rooted]
    return _hit(evidence)


def role_count_at_least(ctx: _Ctx, role: str, n: int, tou_only: bool = False) -> Result:
    """透干字 + 地支本气字计数（不加权）。"""
    found = ctx.tou(role)
    if not tou_only:
        found += [p.branch.addr for p in ctx.chart.pillars if p.branch.main_ten_god in roles(role)]
    return ("met", tuple(found)) if len(found) >= n else ("unmet", ())


def month_branch_is(ctx: _Ctx, mark: str) -> Result:
    """月令为日主之 建禄 / 阳刃。"""
    month = ctx.chart.pillars[1].branch.char
    table = {"建禄": _LU, "阳刃": _YANG_REN}
    if mark not in table:
        raise ValueError(f"month_branch_is 只支持 建禄 / 阳刃：{mark!r}")
    return _hit(["M.b"] if table[mark].get(ctx.dm) == month else [])


def day_master_sits_on(ctx: _Ctx, mark: str) -> Result:
    """日柱自坐标记：坐禄 / 坐羊刃 / 坐长生 / 坐墓。"""
    return _hit(["D.b"] if mark in ctx.chart.pillars[2].self_sit.marks else [])


_DIRECTED = frozenset({"sheng", "ke"})


def _edge_matches(ctx: _Ctx, e: Edge, from_roles: Optional[frozenset[str]],
                  to_roles: Optional[frozenset[str]]) -> bool:
    if len(e.members) != 2:
        return False
    a, b = (ctx.node_god(m) for m in e.members)

    def ok(x: str, y: str) -> bool:
        return (from_roles is None or x in from_roles) and (to_roles is None or y in to_roles)

    return ok(a, b) if e.kind in _DIRECTED else ok(a, b) or ok(b, a)


def has_edge(ctx: _Ctx, kind: Any, from_role: Optional[str] = None, to_role: Optional[str] = None,
             scope: str = "natal") -> Result:
    """关系图中存在 kind 边且两端十神匹配；sheng/ke 按 from→to，其余不分方向。"""
    kinds = {kind} if isinstance(kind, str) else set(kind)
    if scope != "natal" and not any(e.scope == scope for e in ctx.graph.edges):
        return "not_evaluable", ()
    fr = roles(from_role) if from_role else None
    to = roles(to_role) if to_role else None
    return _hit([e.id for e in ctx.graph.edges
                 if e.kind in kinds and e.scope == scope and _edge_matches(ctx, e, fr, to)])


def coexist(ctx: _Ctx, role_a: str, role_b: str) -> Result:
    """role_a 透干且 role_b 在盘（透或藏）；附两者之间的原局边。"""
    a, b = ctx.tou(role_a), ctx.tou(role_b) + ctx.hidden_in(role_b)
    if not a or not b:
        return "unmet", ()
    edges = [e.id for e in ctx.graph.edges if len(e.members) == 2
             and set(e.members) & set(a) and set(e.members) & set(b) and e.scope == "natal"]
    return _hit([*a, *b, *edges])


def strength_judgment(ctx: _Ctx, roles_: list[str]) -> Result:
    """力量对比不由代码裁决：恒为 needs_judgment，附日主与相关角色的地址及其通根地址。"""
    evidence: list[str] = ["D.s"]
    for r in roles_:
        evidence += ctx.tou(r) + ctx.hidden_in(r)
    if ctx.strength is not None:
        evidence += [root.addr for root in ctx.strength.day_master.roots]
        for addr in list(evidence):
            if addr in ctx.strength.stems:
                evidence += [root.addr for root in ctx.strength.stems[addr].roots]
    return "needs_judgment", tuple(dict.fromkeys(evidence))


PREDICATES: dict[str, Callable[..., Result]] = {
    f.__name__: f for f in (
        month_main_role, month_hidden_role, month_hidden_tou, role_tou, role_present, role_absent,
        role_rooted_tou, role_count_at_least, month_branch_is, day_master_sits_on, has_edge, coexist,
        strength_judgment,
    )
}
_ROLE_ARGS = ("role", "role_a", "role_b", "from_role", "to_role")


# ── 目录加载与核对 ──────────────────────────────────────────────────────────

def _validate_node(node: dict[str, Any], where: str) -> None:
    for key in ("any", "all"):
        if key in node:
            for child in node[key]:
                _validate_node(child, where)
            return
    if node.get("pred") not in PREDICATES:
        raise ValueError(f"{where}: 未注册谓词 {node.get('pred')!r}")
    for arg in _ROLE_ARGS:
        if node.get(arg):
            roles(node[arg])
    for r in node.get("roles_", []):
        roles(r)


@lru_cache(maxsize=1)
def load_structures() -> dict[str, dict[str, Any]]:
    data = yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))
    out: dict[str, dict[str, Any]] = {}
    for s in data["structures"]:
        if not s.get("source_refs"):
            raise ValueError(f"结构 {s['id']} 缺少 source_refs")
        for item in s["items"]:
            if item["kind"] not in ("requirement", "breaker", "rescuer"):
                raise ValueError(f"{s['id']}.{item['id']}: 非法 kind {item['kind']!r}")
            _validate_node(item["check"], f"{s['id']}.{item['id']}")
        out[s["id"]] = s
    return out


def _eval(node: dict[str, Any], ctx: _Ctx) -> Result:
    for key in ("any", "all"):
        if key not in node:
            continue
        results = [_eval(child, ctx) for child in node[key]]
        statuses = [st for st, _ in results]
        evidence = [e for st, ev in results if st in ("met", "needs_judgment") for e in ev]
        if key == "any":
            for st in ("met", "needs_judgment", "not_evaluable"):
                if st in statuses:
                    return st, tuple(dict.fromkeys(evidence))
            return "unmet", ()
        if "unmet" in statuses:
            return "unmet", ()
        for st in ("not_evaluable", "needs_judgment"):
            if st in statuses:
                return st, tuple(dict.fromkeys(evidence))
        return "met", tuple(dict.fromkeys(evidence))
    args = {k: v for k, v in node.items() if k != "pred"}
    return PREDICATES[node["pred"]](ctx, **args)


def check_structure(structure_id: str, chart: ChartFacts, graph: RelationGraph,
                    strength: Optional[StrengthFacts] = None) -> StructureCheck:
    spec = load_structures()[structure_id]
    ctx = _Ctx(chart, graph, strength)
    items: list[CheckItem] = []
    refs: list[str] = list(spec["source_refs"])
    for item in spec["items"]:
        status, evidence = _eval(item["check"], ctx)
        if status == "met" and item.get("judgment"):
            status = "needs_judgment"          # 命中，但程度（夺 / 攻 / 是否得宜）需力量对比
        items.append(CheckItem(id=item["id"], kind=item["kind"], text=item["text"],
                               status=status, evidence=evidence))
        refs += item.get("source_refs", [])
    return StructureCheck(
        structure_id=structure_id,
        school=spec["school"],
        display_name_zh=spec["display_name_zh"],
        source_refs=tuple(dict.fromkeys(refs)),
        items=tuple(items),
        judgment_points=tuple(spec.get("judgment_points", [])),
    )


def check_structures(chart: ChartFacts, graph: RelationGraph, strength: Optional[StrengthFacts] = None,
                     ids: Optional[list[str]] = None) -> tuple[StructureCheck, ...]:
    return tuple(check_structure(sid, chart, graph, strength) for sid in (ids or load_structures()))


# ── 段派体用视图与做功候选 ──────────────────────────────────────────────────

_REF_ZUOGONG = (f"{REF_KAISHAN}:1314", f"{REF_KAISHAN}:1316", f"{REF_D10}:258")
_ZHI_KINDS = {"ke": "克", "stem_chong": "冲", "chong": "冲", "xing": "刑", "chuan": "穿"}
_HE_KINDS = frozenset({"wuhe", "liuhe", "zhi_anhe", "ganzhi_zihe"})
_PILLAR_ORDER = {"Y": 0, "M": 1, "D": 2, "H": 3}


def tiyong_of(ten_god: str) -> TiYong:
    return _TIYONG[ten_god]


def tiyong_view(chart: ChartFacts) -> dict[Addr, TiYong]:
    """原局 8 字的体 / 用 / 双属（地支按本气十神）。食神偏体、伤官偏用，统一标双属，不替调用方强择。"""
    out: dict[Addr, TiYong] = {}
    for p in chart.pillars:
        out[p.stem.addr] = tiyong_of(p.stem.ten_god)
        out[p.branch.addr] = tiyong_of(p.branch.main_ten_god)
    return out


def _ti_yong_ends(ty: tuple[str, str]) -> Optional[tuple[int, int]]:
    """返回 (体端下标, 用端下标)；双属按对端补位，两端皆双属返回 None。"""
    a, b = ty
    if a == "双属" and b == "双属":
        return None
    if a == "体" or b == "用":
        return 0, 1
    return 1, 0


def _binzhu(members: tuple[Addr, ...], ty: tuple[str, str]) -> tuple[BinzhuReading, ...]:
    natal = all(m.split(".", 1)[0] in ("Y", "M", "D", "H") for m in members)
    ends = _ti_yong_ends(ty)
    readings: list[BinzhuReading] = []
    for layer in ((1, 2, 3) if natal else (4,)):
        sides = tuple(binzhu_side(m, layer) for m in members)  # type: ignore[arg-type]
        if ends is None:
            direction = "需判断"
        else:
            ti, yong = sides[ends[0]], sides[ends[1]]
            direction = {("主", "宾"): "正向", ("宾", "主"): "反向",
                         ("主", "主"): "同在主位", ("宾", "宾"): "同在宾位"}[(ti, yong)]
        readings.append(BinzhuReading(layer, sides, direction))  # type: ignore[arg-type]
    return tuple(readings)


def _notes(ty: tuple[str, ...]) -> list[str]:
    return ["含双属（食神偏体、伤官偏用），宾主方向按对端补位推定，体用归属交调用方确认"] if "双属" in ty else []


def _derived_sheng(chart: ChartFacts) -> list[tuple[Addr, Addr, Optional[int]]]:
    """关系图不建地支生边：按本气五行推得地支两两相生，及同柱干支相生。"""
    out: list[tuple[Addr, Addr, Optional[int]]] = []
    for p, q in combinations(chart.pillars, 2):
        rel = wuxing_relation(ZHI_TO_WUXING[p.branch.char], ZHI_TO_WUXING[q.branch.char])
        if rel == "生":
            out.append((p.branch.addr, q.branch.addr, q.index - p.index))
        elif rel == "被生":
            out.append((q.branch.addr, p.branch.addr, q.index - p.index))
    for p in chart.pillars:
        rel = p.self_sit.stem_branch_relation
        if rel == "干生支":
            out.append((p.stem.addr, p.branch.addr, 0))
        elif rel == "支生干":
            out.append((p.branch.addr, p.stem.addr, 0))
    return out


def _addr_wuxing(addr: Addr, chars: dict[Addr, str]) -> str:
    return GAN_TO_WUXING[chars[addr]] if _layer(addr) == "s" else ZHI_TO_WUXING[chars[addr]]


def _derived_sheng_adjacent(chart: ChartFacts, chars: dict[Addr, str]) -> list[tuple[Addr, Addr, int]]:
    """同柱 / 相邻柱地址之间按五行推得的相生：返回 (生者, 被生者, 柱距)。

    只取同柱（干支）与相邻柱（年-月、月-日、日-时）；跨柱两柱以上不生成。
    """
    addrs = [a for p in chart.pillars for a in (p.stem.addr, p.branch.addr)]
    out: list[tuple[Addr, Addr, int]] = []
    for x, y in combinations(addrs, 2):
        dist = abs(_PILLAR_ORDER[x.split(".", 1)[0]] - _PILLAR_ORDER[y.split(".", 1)[0]])
        if dist > 1:
            continue
        rel = wuxing_relation(_addr_wuxing(x, chars), _addr_wuxing(y, chars))
        if rel == "生":
            out.append((x, y, dist))
        elif rel == "被生":
            out.append((y, x, dist))
    return out


def _derived_canggan_ke(chart: ChartFacts) -> list[tuple[Addr, Addr, str, str]]:
    """关系图不建「支→干」克边：按藏干五行推得地支克天干，供宫制星取 actor。

    每对（支, 干）只取表内第一个能克之藏干（主气优先），与 _derived_sheng 同一约定。
    """
    out: list[tuple[Addr, Addr, str, str]] = []
    seen: set[tuple[Addr, Addr]] = set()
    for p in chart.pillars:
        for g, qi, _ in ZHI_CANGGAN_TABLE[p.branch.char]:
            for q in chart.pillars:
                key = (p.branch.addr, q.stem.addr)
                if key in seen or wuxing_relation(GAN_TO_WUXING[g], GAN_TO_WUXING[q.stem.char]) != "克":
                    continue
                seen.add(key)
                out.append((p.branch.addr, q.stem.addr, g, qi))
    return out


def build_duan_zuogong_candidates(chart: ChartFacts, graph: RelationGraph) -> tuple[ZuogongCandidate, ...]:
    """扫描关系与同柱/相邻柱相生，列出做功候选。只列候选与宾主方位，不计层数、不折算富贵。"""
    chars = dict(graph.nodes)
    gods = {a: _ten_god(a, c, chart.day_master) for a, c in graph.nodes}
    ty = {a: tiyong_of(g) for a, g in gods.items()}
    out: list[ZuogongCandidate] = []

    def emit(mode: str, kind: str, edge_id: Optional[str], members: tuple[Addr, Addr], actor: Optional[Addr],
             distance: Optional[int], refs: tuple[str, ...], notes: list[str], related: tuple[str, ...] = ()):
        t = (ty[members[0]], ty[members[1]])
        out.append(ZuogongCandidate(
            mode=mode, relation_kind=kind, edge_id=edge_id, members=members,  # type: ignore[arg-type]
            chars=tuple(chars[m] for m in members), ten_gods=tuple(gods[m] for m in members), tiyong=t,
            actor=actor, binzhu=_binzhu(members, t), distance=distance, related_edges=related,
            source_refs=tuple(dict.fromkeys(refs + _REF_ZUOGONG)), notes=tuple(notes + _notes(t)),
        ))

    def sheng_view(src: Addr, dst: Addr) -> tuple[str, tuple[Addr, Addr], Addr]:
        """生/化候选的 mode、members 与 actor。

        生：生者 → 被生者，actor=生者；化（官杀→印，检测仍在生方向做）：被化者（生端）→
        化者（受生端），actor=化者（T-180 审计：化者恒为受生端）。只翻化用，不全局翻 sheng。
        """
        if gods[src] in roles("官杀") and gods[dst] in roles("印"):
            return "化用", (dst, src), dst
        return "生泄用", (src, dst), src

    for e in graph.edges:
        if len(e.members) != 2:
            continue
        members = (e.members[0], e.members[1])
        if e.kind in _ZHI_KINDS:
            actor = e.members[0] if e.kind == "ke" else None
            notes = [f"用克体（{gods[actor]}克{gods[e.members[1]]}）"] if actor and ty[actor] == "用" else []
            emit("制用", e.kind, e.id, members, actor, e.distance, e.source_refs, notes)
        elif e.kind == "sheng":
            mode, s_members, s_actor = sheng_view(*members)
            emit(mode, e.kind, e.id, s_members, s_actor, e.distance, e.source_refs, [])
        elif e.kind in _HE_KINDS:
            emit("合用", e.kind, e.id, members, None, e.distance, e.source_refs, [])

    for src, dst, dist in _derived_sheng(chart):
        mode, s_members, s_actor = sheng_view(src, dst)
        emit(mode, "sheng(main_qi)", None, s_members, s_actor,
             abs(dist) if dist is not None else None, (), ["关系图未建此生边，按本气五行推得"])

    sheng_edges = {e.members: e for e in graph.edges if e.kind == "sheng" and len(e.members) == 2}
    for src, dst, dist in _derived_sheng_adjacent(chart, chars):
        edge = sheng_edges.get((src, dst))
        emit("sheng", "sheng", edge.id if edge else None, (src, dst), src, dist,
             edge.source_refs if edge else (), ["同柱/相邻柱五行相生，按本气五行推得"])

    for br, st, via, qi in _derived_canggan_ke(chart):
        if br.split(".", 1)[0] == st.split(".", 1)[0]:
            continue  # 同柱干支相克属盖头/截脚，见 self_sit.stem_branch_relation，不是宫制星
        dist = abs(_PILLAR_ORDER[br.split(".", 1)[0]] - _PILLAR_ORDER[st.split(".", 1)[0]])
        emit("制用", "canggan_ke", None, (br, st), br, dist, (),
             [f"宫制星：{chars[br]}藏{via}克{chars[st]}（{qi[0]}气）"])

    for m in graph.muku:
        for c in m.candidates:
            if c.excluded:
                continue
            notes = list(c.requires_judgment)
            pi = [_PILLAR_ORDER.get(a.split(".", 1)[0]) for a in (c.addr, m.addr)]
            dist = None if None in pi else abs(pi[0] - pi[1])  # type: ignore[operator]
            # 墓的力向是「库 → 入库方」（T-178 审计 4/4 engine_wrong；actor-rules-v1 §4.9/§5.2）
            emit("墓用", "muku", None, (m.addr, c.addr), m.addr, dist,
                 tuple(h.source_ref for h in c.rule_hits), notes, c.ku_link_edges + c.damaged_by_edges)
    return tuple(out)


__all__ = [
    "BinzhuReading",
    "CheckItem",
    "PREDICATES",
    "StructureCheck",
    "ZuogongCandidate",
    "build_duan_zuogong_candidates",
    "check_structure",
    "check_structures",
    "load_structures",
    "roles",
    "tiyong_of",
    "tiyong_view",
]
