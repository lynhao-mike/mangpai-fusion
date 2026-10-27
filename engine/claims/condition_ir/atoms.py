"""engine/claims/atoms.py · 断语条件谓词表 v1（契约 23 §四）。

46 个原子（v1.2：新增 `suiyun_arrives` / `can_control`，见契约 23 §4.5、§4.8 与 §九），
全部只读 engine.facts 已产出的字段，返回 true / false / unknown（None）。
缺字段一律返回 unknown，不得猜测；不得在此处做命理判断。

岁运隔离（ADR-007 D3）：关系原子默认只扫 `scope == "natal"` 的边，
避免「原局静态断语」被流年干支错误点燃；`edge` 可用 `scope` 参数显式查岁运边。
岁运原子（§4.5）反过来专门消费 `scope != "natal"` 的边。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

# 禄（甲禄寅…癸禄子）的唯一定义处在事实层；与 structure_check 同源导入，不在本层另造表。
from engine.facts.chart_facts import _LU as LU_TABLE
from engine.facts.chart_facts import binzhu_side
from engine.predicates.types import GAN_TO_WUXING, KE_MAP, ZHI_TO_WUXING

Value = Optional[bool]  # True / False / None(=unknown)

STEM_ADDRS = ("Y.s", "M.s", "D.s", "H.s")
BRANCH_ADDRS = ("Y.b", "M.b", "D.b", "H.b")
ALL_ADDRS = ("Y.s", "M.s", "D.s", "H.s", "Y.b", "M.b", "D.b", "H.b")
PILLAR_INDEX = {"Y": 0, "M": 1, "D": 2, "H": 3}
NATAL_SCOPE = "natal"
ANY_SCOPE = ("any", "*", None)

GOD_ALIASES = {
    "印": ("正印", "偏印"),
    "财": ("正财", "偏财"),
    "官杀": ("正官", "七杀"),
    "食伤": ("食神", "伤官"),
    "比劫": ("比肩", "劫财"),
}
SPOUSE = {"乾": ("正财", "偏财"), "坤": ("正官", "七杀")}
CHILD = {"乾": ("正官", "七杀"), "坤": ("食神", "伤官")}

# he_at 默认只认「合他星」的合：六合（liuhe）、地支暗合（zhi_anhe）。
# 依据 sources/duan/MinerU_markdown_婚姻专辑_2056044010230448128.md:48
# 「不能被刑坏，冲破，穿倒，或六合，暗合他星」——原文只举这两种合。
# 排除：三合/三会的半局与拱局（completeness ∈ partial/half_*/gong）、完整三合三会
#      （原文无据，待中枢裁定，暂排除）、日柱自合 ganzhi_zihe（不涉他星）、天干五合 wuhe。
HE_KINDS = ("liuhe", "zhi_anhe")
HE_GROUP_HALF = frozenset({"partial", "half_sheng", "half_mu", "gong"})
HE_KINDS_EXCLUDED = ("wuhe", "sanhe", "sanhui", "ganzhi_zihe")


@dataclass
class AtomResult:
    value: Value
    bindings: dict[str, str] = field(default_factory=dict)
    note: str = ""


def _t(note: str = "", **bind: str) -> AtomResult:
    return AtomResult(True, dict(bind), note)


def _f(note: str = "") -> AtomResult:
    return AtomResult(False, {}, note)


def _u(note: str) -> AtomResult:
    return AtomResult(None, {}, note)


def build_context(facts: dict[str, Any]) -> dict[str, Any]:
    """把 engine.api.analyze_facts 的返回整理成原子可读的上下文。"""
    chart = facts.get("chart") or {}
    stems: dict[str, dict] = {}
    branches: dict[str, dict] = {}
    for p in chart.get("pillars") or []:
        if p.get("stem"):
            stems[p["stem"]["addr"]] = p["stem"]
        if p.get("branch"):
            branches[p["branch"]["addr"]] = p["branch"]

    kong = set()
    for hit in (chart.get("kongwang") or {}).get("hits") or []:
        if isinstance(hit, (list, tuple)) and hit:
            kong.add(hit[0])

    cycles = chart.get("cycles") or {}
    relations = facts.get("relations") or {}
    return {
        "gender": chart.get("gender"),
        "day_master": chart.get("day_master"),
        "stems": stems,
        "branches": branches,
        "kongwang": kong,
        "edges": relations.get("edges") or [],
        "nodes": relations.get("nodes") or [],
        "muku": relations.get("muku") or [],
        "strength": facts.get("strength") or {},
        "camp": (facts.get("strength") or {}).get("camp_counts") or {},
        "shensha": (facts.get("shensha") or {}).get("hits") or [],
        "structures": facts.get("structures") or [],
        "tiyong": (facts.get("duan_zuogong") or {}).get("tiyong") or {},
        "zuogong": (facts.get("duan_zuogong") or {}).get("candidates") or [],
        "dayun": cycles.get("dayun") or [],
        "liunian": cycles.get("liunian"),
        "cited": {},
    }


def _god_set(spec: str, ctx: dict) -> Optional[tuple[str, ...]]:
    """十神规格 → 具体十神元组；无法解析返回 None（调用方给 unknown）。"""
    if spec in GOD_ALIASES:
        return GOD_ALIASES[spec]
    if spec == "配偶星":
        return SPOUSE.get(ctx.get("gender"))
    if spec == "子女星":
        return CHILD.get(ctx.get("gender"))
    if spec in ("正印", "偏印", "正财", "偏财", "正官", "七杀", "食神", "伤官", "比肩", "劫财"):
        return (spec,)
    return None


def _chars_of_god(spec: str, ctx: dict) -> Optional[set[str]]:
    gods = _god_set(spec, ctx)
    if not gods:
        return None
    chars: set[str] = set()
    for s in ctx["stems"].values():
        if s.get("ten_god") in gods:
            chars.add(s.get("char"))
    for b in ctx["branches"].values():
        if b.get("main_ten_god") in gods:
            chars.add(b.get("char"))
        for h in b.get("hidden") or []:
            if h.get("g") in gods:
                chars.add(h.get("c"))
    return chars


# ---------------------------------------------------------------- 位置与透藏 8

def visible_god(ctx, args):
    gods = _god_set(args.get("god", ""), ctx)
    if not gods:
        return _u(f"无法解析十神规格 {args.get('god')!r}")
    at = args.get("at")
    for addr, s in ctx["stems"].items():
        if at and addr != at:
            continue
        if s.get("ten_god") in gods:
            return _t(f"{addr}={s.get('char')}({s.get('ten_god')})", addr=addr)
    return _f()


def hidden_god(ctx, args):
    gods = _god_set(args.get("god", ""), ctx)
    if not gods:
        return _u(f"无法解析十神规格 {args.get('god')!r}")
    at, qi = args.get("at"), args.get("qi")
    for addr, b in ctx["branches"].items():
        if at and addr != at:
            continue
        for h in b.get("hidden") or []:
            if qi and h.get("q") != qi:
                continue
            if h.get("g") in gods:
                return _t(f"{addr}藏{h.get('c')}({h.get('g')})", addr=addr)
    return _f()


def stem_is(ctx, args):
    s = ctx["stems"].get(args.get("at", ""))
    if not s:
        return _u("地址不存在")
    return _t() if s.get("char") == args.get("gan") else _f()


def branch_is(ctx, args):
    b = ctx["branches"].get(args.get("at", ""))
    if not b:
        return _u("地址不存在")
    return _t() if b.get("char") == args.get("zhi") else _f()


def sits_on(ctx, args):
    gods = _god_set(args.get("god", ""), ctx)
    if not gods:
        return _u("无法解析十神规格")
    for addr, s in ctx["stems"].items():
        if s.get("ten_god") in gods:
            b = ctx["branches"].get(addr.replace(".s", ".b"))
            if b and b.get("char") == args.get("zhi"):
                return _t(bind=addr)
    return _f()


def palace_holds(ctx, args):
    gods = _god_set(args.get("god", ""), ctx)
    if not gods:
        return _u("无法解析十神规格")
    palace = args.get("palace", "")
    addr = {"年柱": "Y", "月柱": "M", "日柱": "D", "时柱": "H",
            "年支": "Y.b", "月支": "M.b", "日支": "D.b", "时支": "H.b"}.get(palace)
    if not addr:
        return _u(f"未知宫位 {palace!r}")
    if "." in addr:
        b = ctx["branches"].get(addr)
        if not b:
            return _u("地址不存在")
        if b.get("main_ten_god") in gods:
            return _t(bind=addr)
        for h in b.get("hidden") or []:
            if h.get("g") in gods:
                return _t(bind=addr)
        return _f()
    s, b = ctx["stems"].get(addr + ".s"), ctx["branches"].get(addr + ".b")
    if not s or not b:
        return _u("地址不存在")
    if s.get("ten_god") in gods or b.get("main_ten_god") in gods:
        return _t(bind=addr + ".s")
    return _f()


def rooted(ctx, args):
    at = args.get("at")
    if at:
        info = (ctx["strength"].get("stems") or {}).get(at)
        if info is None:
            return _u(f"{at} 无根数据（非天干地址）")
        return _t(f"{at} 有根") if info.get("roots") else _f(f"{at} 无根")
    gods = _god_set(args.get("god", ""), ctx)
    if not gods:
        return _u("无法解析十神规格")
    min_qi = args.get("min_qi")
    order = {"本气": 3, "中气": 2, "余气": 1}
    for addr, s in ctx["stems"].items():
        if s.get("ten_god") not in gods:
            continue
        info = (ctx["strength"].get("stems") or {}).get(addr) or {}
        roots = info.get("roots") or []
        if min_qi:
            roots = [r for r in roots if order.get(r.get("qi"), 0) >= order.get(min_qi, 0)]
        if roots:
            return _t(bind=addr)
    return _f()


def day_master(ctx, args):
    dm = ctx.get("day_master")
    if not dm:
        return _u("无日主信息")
    char = dm.get("char") if isinstance(dm, dict) else str(dm)
    return _t() if char == args.get("gan") else _f()


# ---------------------------------------------------------------- 关系 10

def _edges(ctx, scope: Any = NATAL_SCOPE) -> list[dict]:
    """按 scope 取边。默认只取原局边（ADR-007 D3 的原局隔离）。"""
    edges = ctx["edges"]
    if scope in ANY_SCOPE:
        return edges
    return [e for e in edges if e.get("scope", NATAL_SCOPE) == scope]


def edge(ctx, args):
    kind, between = args.get("type"), args.get("between")
    scope = args.get("scope", NATAL_SCOPE)
    for e in _edges(ctx, scope):
        if e.get("kind") != kind:
            continue
        if between:
            members = set(e.get("members") or [])
            if not set(between).issubset(members):
                continue
        return _t(f"边 {e.get('id')}", edge_id=e.get("id"))
    return _f()


def edge_touches(ctx, args):
    kind, at = args.get("type"), args.get("at")
    for e in _edges(ctx):
        if e.get("kind") == kind and at in (e.get("members") or []):
            return _t(f"边 {e.get('id')}", edge_id=e.get("id"))
    return _f()


def _touch(ctx, at, kinds):
    for e in _edges(ctx):
        if e.get("kind") in kinds and at in (e.get("members") or []):
            return _t(f"{e.get('kind')} 边 {e.get('id')}", edge_id=e.get("id"))
    return _f()


def chong_at(ctx, args):
    return _touch(ctx, args.get("at"), ("chong", "stem_chong"))


def chuan_at(ctx, args):
    return _touch(ctx, args.get("at"), ("chuan",))


def xing_at(ctx, args):
    return _touch(ctx, args.get("at"), ("xing",))


def po_at(ctx, args):
    return _touch(ctx, args.get("at"), ("po",))


def he_at(ctx, args):
    """某地址被合（默认只认六合 / 地支暗合，且只扫原局边）。

    `with_god`：合它的是某十神（合他星）。
    `exclude_god`：排除「合它的是该十神」的边（如排除配偶星本星相合），默认不启用。
    """
    at, with_god = args.get("at"), args.get("with_god")
    exclude_god = args.get("exclude_god")
    gods = _god_set(with_god, ctx) if with_god else None
    if with_god and not gods:
        return _u("无法解析十神规格")
    excluded = _god_set(exclude_god, ctx) if exclude_god else None
    if exclude_god and not excluded:
        return _u("无法解析十神规格")
    for e in _edges(ctx):
        if not _is_he_edge(e):
            continue
        members = e.get("members") or []
        if at not in members:
            continue
        if not gods and not excluded:
            return _t(f"{e.get('kind')} 边 {e.get('id')}", edge_id=e.get("id"))
        for other in members:
            if other == at:
                continue
            tg = _ten_god_at(ctx, other)
            if excluded and tg in excluded:
                continue
            if gods and tg not in gods:
                continue
            return _t(f"{e.get('kind')} 合 {other}", edge_id=e.get("id"), other=other)
    return _f()


def _is_he_edge(e: dict) -> bool:
    """是否算「被合」：只认六合与地支暗合。

    排除半局/拱局（completeness ∈ partial/half_*/gong）、日柱自合 ganzhi_zihe、天干五合 wuhe。
    完整三合/三会（full）同样排除：原文只举「六合、暗合他星」，无据支持完整局算被合，
    该口径待中枢裁定（契约 23 §4.2）。
    """
    return e.get("kind") in HE_KINDS



def _ten_god_at(ctx, addr):
    if addr.endswith(".s"):
        return (ctx["stems"].get(addr) or {}).get("ten_god")
    return (ctx["branches"].get(addr) or {}).get("main_ten_god")


def group_complete(ctx, args):
    kind = args.get("type")
    if kind not in ("sanhe", "sanhui"):
        return _u("仅支持 sanhe / sanhui")
    for e in _edges(ctx):
        if e.get("kind") == kind and len(e.get("members") or []) >= 3:
            return _t(f"边 {e.get('id')}")
    return _f()


def distance_leq(ctx, args):
    a, b, n = args.get("a", ""), args.get("b", ""), int(args.get("n", 1))
    if a[:1] not in PILLAR_INDEX or b[:1] not in PILLAR_INDEX:
        return _u("地址无法定位柱位")
    return _t() if abs(PILLAR_INDEX[a[:1]] - PILLAR_INDEX[b[:1]]) <= n else _f()


def same_pillar(ctx, args):
    a, b = args.get("a", ""), args.get("b", "")
    return _t() if a[:1] == b[:1] and a[:1] in PILLAR_INDEX else _f()


# ---------------------------------------------------------------- 状态与力量 9

def kongwang(ctx, args):
    return _t() if args.get("at") in ctx["kongwang"] else _f()


def muku_present(ctx, args):
    zhi = args.get("zhi")
    if not ctx["muku"]:
        return _f()
    if zhi and not any(m.get("branch") == zhi for m in ctx["muku"]):
        return _f()
    return _t()


def muku_open(ctx, args):
    zhi = args.get("zhi")
    for m in ctx["muku"]:
        if m.get("branch") != zhi:
            continue
        addr = m.get("addr")
        if any(e.get("kind") in ("chong",) and addr in (e.get("members") or []) for e in _edges(ctx)):
            return _t(f"{zhi} 库在 {addr} 被冲开")
        return _f()
    return _f()


def ru_mu(ctx, args):
    chars = _chars_of_god(args.get("star", ""), ctx)
    if chars is None:
        return _u("无法解析十神规格")
    if not chars:
        return _f("命局无此十神，入墓无从谈起")
    for m in ctx["muku"]:
        for c in m.get("candidates") or []:
            if c.get("excluded"):
                continue
            if c.get("char") in chars:
                return _t(f"{c.get('char')} 入 {m.get('branch')} 墓")
    return _f()


def siling(ctx, args):
    info = ctx["strength"].get("siling")
    if not info:
        return _u("facts 未提供人元司令")
    god = (info or {}).get("ten_god") if isinstance(info, dict) else None
    if not god:
        return _u("人元司令字段为空")
    if not args.get("god"):
        return _t()
    gods = _god_set(args["god"], ctx)
    return _t() if gods and god in gods else _f()


def camp_count(ctx, args):
    side = args.get("side", "")
    rec = ctx["camp"].get(side)
    if rec is None:
        return _u(f"阵营 {side!r} 不在 camp_counts")
    total = sum(int(rec.get(k) or 0) for k in ("stems", "main_qi", "mid_qi", "residual_qi"))
    op, val = args.get("op", "gte"), int(args.get("value", 1))
    ok = {"gte": total >= val, "gt": total > val, "lte": total <= val,
          "lt": total < val, "eq": total == val}.get(op)
    if ok is None:
        return _u(f"未知比较符 {op!r}")
    return _t(f"{side} 计数={total}") if ok else _f(f"{side} 计数={total}")


def de_ling(ctx, args):
    gods = _god_set(args.get("god", ""), ctx)
    if not gods:
        return _u("无法解析十神规格")
    month = ctx["branches"].get("M.b") or {}
    return _t() if month.get("main_ten_god") in gods else _f()


def tiaohou_at(ctx, args):
    climate = ctx["strength"].get("climate") or {}
    tiao = climate.get("tiaohou") or climate.get("tiaohou_advice")
    if not tiao:
        return _u("facts 未提供调候建议")
    return _t() if args.get("char") in str(tiao) else _f()


def shensha(ctx, args):
    name, at = args.get("name"), args.get("at")
    for h in ctx["shensha"]:
        if h.get("name") != name:
            continue
        if at and at not in (h.get("anchor_addr"), h.get("target_addr")):
            continue
        return _t(bind=h.get("anchor_addr") or "")
    return _f()


# ---------------------------------------------------------------- 结构与做功 7

def _structure(structure_id=None):
    def pick(ctx):
        out = []
        for s in ctx["structures"]:
            if structure_id and s.get("structure_id") != structure_id:
                continue
            out.append(s)
        return out
    return pick


def _derived_state(s: dict) -> str:
    items = s.get("items") or []
    req = [i for i in items if i.get("kind") == "requirement"]
    brk = [i for i in items if i.get("kind") == "breaker"]
    if any(i.get("status") == "unmet" for i in req):
        return "unmet"
    if any(i.get("status") in ("needs_judgment", "not_evaluable") for i in req):
        return "needs_judgment"
    if all(i.get("status") == "met" for i in req) and req:
        if any(i.get("status") == "met" for i in brk):
            return "needs_judgment"
        return "met"
    return "needs_judgment"


def geju_met(ctx, args):
    sid = args.get("geju_type")
    cands = _structure(sid)(ctx)
    if not cands:
        return _f()
    states = [_derived_state(s) for s in cands]
    return _t(f"派生状态 {states}") if "met" in states else _f(f"派生状态 {states}")


def geju_state(ctx, args):
    sid, want = args.get("geju_type"), args.get("state")
    cands = _structure(sid)(ctx)
    if not cands:
        return _f()
    st = _derived_state(cands[0])
    return _t(f"{st}") if st == want else _f(f"{st}")


def zuogong(ctx, args):
    kind, involves = args.get("kind"), args.get("involves")
    target_god, actor_god = args.get("target_god"), args.get("actor_god")
    actor_at, target_at = args.get("actor_at"), args.get("target_at")
    gods = _god_set(involves, ctx) if involves else None
    tset = _god_set(target_god, ctx) if target_god else None
    aset = _god_set(actor_god, ctx) if actor_god else None
    for c in ctx["zuogong"]:
        if kind and c.get("mode") != kind:
            continue
        tgods = tuple(c.get("ten_gods") or ())
        if gods and not (set(tgods) & set(gods)):
            continue
        members = tuple(c.get("members") or ())
        ty = tuple(c.get("tiyong") or ())
        actor = c.get("actor")
        target = next((m for m, t in zip(members, ty) if t == "用"), members[-1] if members else None)
        ia = next((i for i, m in enumerate(members) if m == actor), None)
        it = next((i for i, m in enumerate(members) if m == target), None)
        if tset and (it is None or tgods[it] not in tset):
            continue
        if aset and (ia is None or tgods[ia] not in aset):
            continue
        if actor_at and actor != actor_at:
            continue
        if target_at and target != target_at:
            continue
        bind = {}
        if actor:
            bind["Z"] = actor          # 制者（做功的一方）
        if target:
            bind["T"] = target         # 被制者（用）
        return _t(f"{c.get('mode')} {c.get('edge_id') or c.get('relation_kind')}", **bind)
    return _f()


def tiyong(ctx, args):
    role, at = args.get("role"), args.get("at")
    for addr, r in ctx["tiyong"].items():
        if at and addr != at:
            continue
        if r == role:
            return _t(f"{addr}={r}", addr=addr)
    return _f()


def _suiyun_addrs(ctx) -> list[str]:
    """岁运层已出现的地址（从关系边的成员反推，不另建事实）。"""
    out: list[str] = []
    for e in ctx["edges"]:
        for m in e.get("members") or []:
            head = str(m).split(".", 1)[0]
            if head.startswith(("DY", "LN")) and m not in out:
                out.append(m)
    return out


def _binzhu_from_facts(ctx, addr, layer):
    """优先读事实：做功候选自带每层 (sides, direction)（structure_check._binzhu 产出）。"""
    for c in ctx["zuogong"]:
        members = list(c.get("members") or [])
        if addr not in members:
            continue
        pos = members.index(addr)
        for b in c.get("binzhu") or []:
            if b.get("layer") != layer:
                continue
            sides = b.get("sides") or []
            if pos < len(sides):
                return sides[pos], b.get("direction")
    return None


def binzhu(ctx, args):
    """宾主层级（段派 M1-D-001..004）：某地址在该层为主还是为宾。

    `layer`：1 日干为主 / 2 日柱为主 / 3 日柱+时柱为主 / 4 原局为主、岁运为宾。
    `side?`：主 / 宾；给定时要求该地址的层内身份相符。
    `at?`：限定地址；缺省则在该层可能出现的地址中找第一个符合 `side` 的。
    事实来源：做功候选的 `binzhu` 读数（事实层已产出）；候选未覆盖该地址时回落到
    事实层的纯位置函数 `chart_facts.binzhu_side`，同一 SSOT，不另算。
    """
    try:
        layer = int(args.get("layer"))
    except (TypeError, ValueError):
        return _u(f"宾主层必须是 1-4：{args.get('layer')!r}")
    if layer not in (1, 2, 3, 4):
        return _u(f"宾主层必须是 1-4：{layer}")
    side = args.get("side")
    if side is not None and side not in ("主", "宾"):
        return _u(f"宾主只有 主/宾：{side!r}")
    at = args.get("at")
    if at:
        addrs = [at]
    else:
        addrs = list(ALL_ADDRS) + (_suiyun_addrs(ctx) if layer == 4 else [])
    for addr in addrs:
        got = _binzhu_from_facts(ctx, addr, layer)
        if got is None:
            try:
                got = (binzhu_side(addr, layer), None)  # type: ignore[arg-type]
            except ValueError:
                continue
        cur, direction = got
        if side and cur != side:
            continue
        note = f"{addr} 第{layer}层为{cur}" + (f"（{direction}）" if direction else "")
        return _t(note, addr=addr)
    if layer == 4 and not _suiyun_addrs(ctx):
        return _f(f"本次输入未提供岁运节点，第 4 层只有原局主位，无{side or '宾'}可命中")
    return _f(f"第{layer}层没有{side or ''}位地址")


def lu_at(ctx, args):
    """某天干的禄支是否落在指定（或缺省＝任一）地支上。禄表取自事实层 `chart_facts._LU`。"""
    gan = args.get("gan")
    if not gan:
        dm = ctx.get("day_master")
        gan = dm.get("char") if isinstance(dm, dict) else (str(dm) if dm else "")
    if not gan:
        return _u("未指定 gan 且无日主信息")
    target = LU_TABLE.get(gan)
    if not target:
        return _u(f"未知天干 {gan!r}")
    at = args.get("at")
    if at and at not in BRANCH_ADDRS:
        return _u(f"禄只看地支地址：{at!r}")
    for addr in ([at] if at else BRANCH_ADDRS):
        b = ctx["branches"].get(addr)
        if b and b.get("char") == target:
            return _t(f"{gan}禄在{target}（{addr}）", addr=addr, zhi=target)
    return _f(f"{gan}禄在{target}，盘中{'该位' if at else '四支'}未见")


def needs_judgment(ctx, args):
    """显式未知占位（契约 23 §4.7，ADR-007 D12）：恒返回 unknown，说明缺哪一步判断。"""
    reason = args.get("reason")
    if not reason:
        return _u("needs_judgment 缺 reason（契约 23 §4.7 要求写明缺什么判断）")
    return _u(str(reason))


def _check_items(ctx, check, kinds):
    for s in ctx["structures"]:
        for i in s.get("items") or []:
            if check and i.get("id") != check:
                continue
            if i.get("kind") in kinds and i.get("status") == "met":
                return _t(f"{s.get('structure_id')}·{i.get('id')}")
    return _f()


def structure_break(ctx, args):
    return _check_items(ctx, args.get("check"), ("breaker",))


def structure_rescue(ctx, args):
    return _check_items(ctx, args.get("check"), ("rescue", "aux"))


# ---------------------------------------------------------------- 岁运 6
#
# 岁运原子专门消费 `scope != natal` 的边（ADR-007 D3 的镜像面）：原局原子被隔离在
# natal，岁运原子则只在岁运层找。建边由 relation_graph._nodes() 完成，本层不重造。
# 三值语义（ADR-007 D3 / 契约 23 §4.5）：
#   - 探测存在性（dayun_present / liunian_present）：未提供 → False（客观输入事实）。
#   - 实质关系（suiyun_edge / sanhe_with_suiyun / chong_kai_muku / suiyun_arrives）：
#     未提供 → unknown（让 state = needs_fact，Agent 据此追问年份）。
#   - 不引入「不适用」第四值；只问原局时由外层按 time_window == "natal" 过滤断语集合。

NO_SUIYUN = "未提供大运/流年上下文"
SUIYUN_HEADS = ("DY", "LN")
SUIYUN_SCOPES = ("dayun", "liunian", "dayun+liunian")
MUKU_OPENER_KINDS = ("chong", "xing")
MUKU_OPENER_SCOPES = ("dayun", "liunian")

# 「到位」两种机制（M1-D-042 反客为主：一为通禄，二为现原身）。
ARRIVE_MODES = ("通禄", "原身")

# 原身 = 禄的逆映射（D-02 M1-D-058 related_table）：
#   甲↔寅 / 乙↔卯 / 丙戊↔巳 / 丁己↔午 / 庚↔申 / 辛↔酉 / 壬↔亥 / 癸↔子
# 原文明言「辰戌丑未无原身，此 4 支不适用本规则」（同条 falsifiable_by），故不补造土支原身。
YUANSHEN: dict[str, tuple[str, ...]] = {}
for _gan, _zhi in LU_TABLE.items():          # _LU 的顺序保证 巳→(丙,戊)、午→(丁,己)
    YUANSHEN[_zhi] = YUANSHEN.get(_zhi, ()) + (_gan,)


def _suiyun_edges(ctx) -> list[dict]:
    """scope 不是 natal 的关系边。"""
    return [e for e in ctx["edges"] if e.get("scope", NATAL_SCOPE) != NATAL_SCOPE]


def _has_suiyun(ctx) -> bool:
    """本次输入是否带岁运上下文：以事实层是否真的建出岁运边为准。

    不读 ctx["dayun"]——只要出生数据可排，大运十步恒在，未指定 dayun_index 时
    并没有任何大运关系边，用它会误判「已提供岁运」。
    """
    return bool(_suiyun_edges(ctx))


def _suiyun_nodes(ctx) -> dict[str, str]:
    """岁运节点地址 → 干文字符（如 {"LN2027.b": "未"}）。

    优先读事实层 `relations.nodes`（权威）；节点被裁剪时回落到从关系边的
    members/chars 对齐反推。两种来源都不重算干支。
    """
    out: dict[str, str] = {}
    for pair in ctx.get("nodes") or []:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            continue
        addr, char = str(pair[0]), str(pair[1])
        if addr.split(".", 1)[0][:2] in SUIYUN_HEADS:
            out[addr] = char
    if out:
        return out
    for e in _suiyun_edges(ctx):
        members, chars = e.get("members") or [], e.get("chars") or []
        if len(members) != len(chars):
            continue
        for addr, char in zip(members, chars):
            if str(addr).split(".", 1)[0][:2] in SUIYUN_HEADS:
                out.setdefault(str(addr), str(char))
    return out


def _resolve_natal(ctx, spec) -> list[str]:
    """把 `at` 参数解析成原局地址：支持地址（"M.b"）与单字干支（"亥"）两种写法。"""
    if not spec:
        return []
    text = str(spec)
    if text in ctx["stems"] or text in ctx["branches"]:
        return [text]
    if len(text) != 1:
        return []
    hits = [a for a, v in ctx["stems"].items() if v.get("char") == text]
    hits += [a for a, v in ctx["branches"].items() if v.get("char") == text]
    return sorted(hits, key=ALL_ADDRS.index)


def dayun_present(ctx, args):
    return _t() if ctx["dayun"] else _f()


def liunian_present(ctx, args):
    """有指定流年。年份从岁运节点地址反推（facts 的 cycles.liunian 恒为 null）。"""
    years = sorted({a.split(".", 1)[0][2:] for a in _suiyun_nodes(ctx) if a.startswith("LN")})
    if not years:
        if not ctx.get("liunian"):
            return _f("本次输入未提供流年")
        years = [str(ctx["liunian"])]
    year = args.get("year")
    if year is None:
        return _t(f"已提供流年 {'/'.join(years)}", year=years[0])
    return _t(f"已提供流年 {year}") if str(year) in years else _f(f"未提供流年 {year}")


def suiyun_edge(ctx, args):
    """岁运与某地址构成某关系（只看 scope != natal 的边）。

    `scope?`：精确限定 dayun / liunian / dayun+liunian；缺省＝任一层。
    命中绑定 `edge_id` 与 `scope`。
    """
    kind, at = args.get("type"), args.get("at")
    scope = args.get("scope")
    if scope is not None and scope not in SUIYUN_SCOPES:
        return _u(f"scope 只有 {'/'.join(SUIYUN_SCOPES)}：{scope!r}")
    if not _has_suiyun(ctx):
        return _u(NO_SUIYUN)
    for e in _suiyun_edges(ctx):
        if e.get("kind") != kind:
            continue
        if scope and e.get("scope") != scope:
            continue
        if at not in (e.get("members") or []):
            continue
        return _t(f"{e.get('kind')} 边 {e.get('id')}（{e.get('scope')}）",
                  edge_id=e.get("id"), scope=e.get("scope"))
    return _f(f"岁运层无 {kind} 触及 {at} 的边")


def sanhe_with_suiyun(ctx, args):
    """岁运与原局共同构成完整三合 / 三会（`completeness == "full"`）。

    `zhi_set?`：限定必须包含的三支（字符串或列表），如 "亥子丑"。
    完整局由 relation_graph 判定，本层只读 `completeness`，不自己补齐。
    """
    if not _has_suiyun(ctx):
        return _u(NO_SUIYUN)
    want = args.get("zhi_set")
    if isinstance(want, str):
        want = list(want)
    want_set = {str(c) for c in (want or ())}
    for e in _suiyun_edges(ctx):
        if e.get("kind") not in ("sanhe", "sanhui"):
            continue
        if e.get("completeness") != "full":
            continue
        if e.get("layer") not in (None, "branch"):
            continue
        chars = {str(c) for c in (e.get("chars") or ())}
        if want_set and not want_set.issubset(chars):
            continue
        group = e.get("group") or "".join(sorted(chars))
        return _t(f"{group} 成局（{e.get('scope')}）边 {e.get('id')}",
                  edge_id=e.get("id"), scope=e.get("scope"))
    return _f("岁运层无完整三合/三会" + (f"（限定 {''.join(sorted(want_set))}）" if want_set else ""))


def chong_kai_muku(ctx, args):
    """原局墓库被岁运冲 / 刑冲开。

    只看 `scope ∈ {dayun, liunian}` 且 `kind ∈ {chong, xing}` 的边（MinerU_22 :1759
    「开则为开墓」、:1770「岁冲则冲动冲开」）。原文区分「运冲为冲破、岁冲为冲动冲开」，
    两者都计入，方向差异留在 note 的 scope 里。
    `zhi?`：限定墓库地支；`year?`：限定由该流年触发的冲开。
    """
    zhi, year = args.get("zhi"), args.get("year")
    if not _has_suiyun(ctx):
        return _u(NO_SUIYUN)
    if year is not None:
        nodes = _suiyun_nodes(ctx)
        if not any(a.startswith(f"LN{year}.") for a in nodes):
            return _u(f"未提供 {year} 流年上下文")
    kus = [m for m in ctx["muku"] if not zhi or m.get("branch") == zhi]
    if not kus:
        return _f(f"原局无{zhi or ''}墓库，无从冲开")
    want_nodes = {f"LN{year}.s", f"LN{year}.b"} if year is not None else set()
    for m in kus:
        addr = m.get("addr")
        for e in _suiyun_edges(ctx):
            if e.get("kind") not in MUKU_OPENER_KINDS:
                continue
            if e.get("scope") not in MUKU_OPENER_SCOPES:
                continue
            members = e.get("members") or []
            if addr not in members:
                continue
            if want_nodes and not (want_nodes & set(members)):
                continue
            return _t(f"{m.get('branch')}库（{addr}）被 {e.get('kind')} 边 {e.get('id')}（{e.get('scope')}）冲开",
                      edge_id=e.get("id"), addr=addr)
    return _f(f"{zhi or ''}墓库未被岁运冲刑触及")


def suiyun_arrives(ctx, args):
    """段派「到位」（M1-D-042 反客为主）：「运中出现八字中的字就为八字中的字到了」。

    原文两种方式（`theory/raw/duan/d01-deep-read.md:287`）：
      ① 通禄 —— 原局天干在运年地支见禄（M1-D-058「大运/流年的支是命中天干的禄」）；
      ② 现原身 —— 原局地支所藏之干在运年天干透出（同条「运年的干是命中地支的原身」；
         原身表见 YUANSHEN，辰戌丑未无原身不入此规则）。
    `at`：原局地址或单字干支；`via?`：显式指定 通禄 / 原身（缺省按地址层级自动选）。
    命中绑定原局地址 `addr` 与岁运节点 `sui_addr`。
    """
    at, via = args.get("at"), args.get("via")
    if via is not None and via not in ARRIVE_MODES:
        return _u(f"via 只有 {'/'.join(ARRIVE_MODES)}：{via!r}")
    if not _has_suiyun(ctx):
        return _u(NO_SUIYUN)
    addrs = _resolve_natal(ctx, at)
    if not addrs:
        return _u(f"无法把 {at!r} 定位到原局地址")
    nodes = _suiyun_nodes(ctx)
    for addr in addrs:
        is_stem = addr.endswith(".s")
        mode = via or ("通禄" if is_stem else "原身")
        if (mode == "通禄") != is_stem:
            return _u(f"via={mode} 与 {addr} 层级不符（通禄看原局天干，原身看原局地支）")
        char = (ctx["stems"] if is_stem else ctx["branches"])[addr].get("char") or ""
        if mode == "通禄":
            target = LU_TABLE.get(char)
            if not target:
                return _u(f"未知天干 {char!r}")
            for sui_addr, sui_char in nodes.items():
                if sui_addr.endswith(".b") and sui_char == target:
                    return _t(f"原局天干{char}（{addr}）的禄{target}落到 {sui_addr}",
                              addr=addr, sui_addr=sui_addr)
            return _f(f"原局天干{char}禄在{target}，本次岁运地支未见")
        yuanshen = YUANSHEN.get(char)
        if not yuanshen:
            return _f(f"{char}为墓库支，无原身（D-02 M1-D-058：辰戌丑未无原身）")
        for sui_addr, sui_char in nodes.items():
            if sui_addr.endswith(".s") and sui_char in yuanshen:
                return _t(f"原局地支{char}（{addr}）的原身{''.join(yuanshen)}透于 {sui_addr}",
                          addr=addr, sui_addr=sui_addr)
        return _f(f"原局地支{char}原身{''.join(yuanshen)}，本次岁运天干未见")
    return _f("未命中")


# ---------------------------------------------------------------- 力量比较 1
#
# 段派核心判据「制得住 / 制不住」（ADR-007 D4）。原文依据：
#   （行号按当前语料文件实测；任务卡 T-145 原引 :1759/:1844/:1850 有 3~30 行偏差）
#   MinerU_markdown_22.盲派初级命理学 :1762 ——「冲神之旺衰判断，以多则为旺，寡则为衰；
#     以合局会局为旺，以孤立受克为衰；以得令为旺，以失令为衰。」
#   同书 :1812「戌辰力量相当，互相制不了」/ :1824「谁也制不了谁」——力量相当即不可裁。
#   代码铁律 structure_check.py:255 strength_judgment：「力量对比不由代码裁决」。
# 因此本原子只在极端清晰的盘面给真/假，双方各有旺项时一律 unknown（不是骑墙，是原文口径）。

# ⚠ 以下阈值均为工程取值，不是原文数值（原文只说「多 / 寡」，未给数）：
DUO_MIN = 3        # 「以多则为旺」的显性字数下限（天干 + 地支本气）
GUA_MAX = 1        # 「寡则为衰」的显性字数上限
STRONG_MIN = 2     # 判真/假所需的旺项数（ADR-007 D4 设计值，非原文）

SIDE_KE_KINDS = ("chong", "ke", "stem_chong", "chuan")
SIDE_JU_KINDS = ("sanhe", "sanhui")


def _wx_at(ctx, addr) -> Optional[str]:
    """地址的五行：天干查干表，地支按本气（与 facts 的 main_qi 计数同源）。"""
    if addr.endswith(".s"):
        return GAN_TO_WUXING.get((ctx["stems"].get(addr) or {}).get("char"))
    return ZHI_TO_WUXING.get((ctx["branches"].get(addr) or {}).get("char"))


def _side_addrs(ctx, wx) -> list[str]:
    return [a for a in ALL_ADDRS if _wx_at(ctx, a) == wx]


def _side_ju(ctx, wx) -> Optional[str]:
    """原局是否有该五行的完整三合 / 三会（「以合局会局为旺」）。"""
    for e in _edges(ctx):
        if e.get("kind") not in SIDE_JU_KINDS or e.get("completeness") != "full":
            continue
        attrs = e.get("attrs") or {}
        if (attrs.get("huashen") or attrs.get("wuxing")) == wx:
            return f"{e.get('group') or ''}成局"
    return None


def _side_shou_ke(ctx, wx, occ) -> Optional[str]:
    """「以孤立受克为衰」：该方某字被原局冲/克/穿边触及，且对方五行克该方。"""
    for e in _edges(ctx):
        if e.get("kind") not in SIDE_KE_KINDS:
            continue
        members = e.get("members") or []
        if not any(a in members for a in occ):
            continue
        for other in members:
            if other in occ:
                continue
            other_wx = _wx_at(ctx, other)
            if other_wx and KE_MAP.get(other_wx) == wx:
                return f"{other}({other_wx})克{wx}"
    return None


def _side_profile(ctx, wx) -> Optional[dict]:
    """一侧的旺衰读数：旺项 / 衰项两条清单，逐项可追溯到原文口径。"""
    layered = ((ctx["strength"].get("climate") or {}).get("wuxing_layered") or {}).get(wx)
    if not layered:
        return None
    n_char = int(layered.get("stems") or 0) + int(layered.get("main_qi") or 0)
    de_ling = bool(layered.get("month_main_qi"))
    occ = _side_addrs(ctx, wx)
    strong: list[str] = []
    weak: list[str] = []
    if de_ling:
        strong.append(f"得令({(ctx['branches'].get('M.b') or {}).get('char')}月)")
    else:
        weak.append(f"失令({(ctx['branches'].get('M.b') or {}).get('char')}月)")
    if n_char >= DUO_MIN:
        strong.append(f"多({n_char}字)")
    elif n_char <= GUA_MAX:
        weak.append(f"寡({n_char}字)")
    ju = _side_ju(ctx, wx)
    if ju:
        strong.append(ju)
    ke = _side_shou_ke(ctx, wx, occ)
    if ke:
        weak.append(f"受克({ke})")
    return {"wx": wx, "n": n_char, "addrs": occ, "strong": strong, "weak": weak}


def _side_text(role: str, prof: dict) -> str:
    return (f"{role} {prof['wx']}（{'/'.join(prof['addrs']) or '无字'}）"
            f"旺项[{'、'.join(prof['strong']) or '无'}]"
            f"衰项[{'、'.join(prof['weak']) or '无'}]")


def can_control(ctx, args):
    """制得住 / 制不住（段派核心判据），三值：True 制得住 / False 制不住 / None 不可裁。

    `actor`：施制一方（制者）；`target`：被制一方。均可写地址（"M.b" / "D.s"）或单字干支（"亥"）。
    判据（ADR-007 D4，全部来自 MinerU_22 :1759 的四条对句）：
      True  —— actor 旺项 ≥2 且 target 无任何旺项、至少一项衰项；
      False —— target 旺项 ≥2 且 actor 无任何旺项、至少一项衰项；
      None  —— 其余（双方各有根气 / 两党对抗 / 力量相当）。
    note 恒附双方旺衰明细与原文出处；unknown 不是失败，是原文「力量相当即制不了」的断言。
    """
    actor, target = args.get("actor"), args.get("target")
    a_addrs, t_addrs = _resolve_natal(ctx, actor), _resolve_natal(ctx, target)
    if not a_addrs:
        return _u(f"无法把 actor={actor!r} 定位到原局地址")
    if not t_addrs:
        return _u(f"无法把 target={target!r} 定位到原局地址")
    a_wx, t_wx = _wx_at(ctx, a_addrs[0]), _wx_at(ctx, t_addrs[0])
    if not a_wx or not t_wx:
        return _u("双方五行不可得")
    if a_wx == t_wx:
        return _u(f"actor 与 target 同属{t_wx}，不构成对抗")
    a_prof, t_prof = _side_profile(ctx, a_wx), _side_profile(ctx, t_wx)
    if a_prof is None or t_prof is None:
        return _u("facts 未提供五行层次计数（strength.climate.wuxing_layered）")
    a_n, t_n = len(a_prof["strong"]), len(t_prof["strong"])
    detail = f"{_side_text('制者', a_prof)}；{_side_text('被制', t_prof)}"
    bind = {"actor_addr": a_addrs[0], "target_addr": t_addrs[0]}
    if a_n >= STRONG_MIN and t_n == 0 and t_prof["weak"]:
        return _t(f"{detail} → 制得住（MinerU_22:1762 旺衰对句）", **bind)
    if t_n >= STRONG_MIN and a_n == 0 and a_prof["weak"]:
        return _f(f"{detail} → 制不住（MinerU_22:1762 旺衰对句）")
    return _u(f"{detail} → 力量相当，不可裁（MinerU_22:1812/:1824「力量相当，互相制不了」）")


# ---------------------------------------------------------------- 元谓词 3

def _iter_atoms(ctx, spec):
    if not isinstance(spec, dict) or "atom" not in spec:
        return None
    fn = ATOMS.get(spec["atom"])
    if fn is None:
        return None
    required, optional = SIGNATURES.get(spec["atom"], ((), ()))
    args = dict(spec.get("args") or {})
    if "at" not in args and "at" not in optional and "at" not in required:
        return None
    out = []
    for addr in ALL_ADDRS:
        a = dict(args)
        a["at"] = addr
        out.append(fn(ctx, a))
    return out


def count(ctx, args):
    results = _iter_atoms(ctx, args.get("atom"))
    if results is None:
        return _u("count 仅支持带 at 参数的原子")
    n = sum(1 for r in results if r.value is True)
    op, val = args.get("op", "gte"), int(args.get("value", 1))
    ok = {"gte": n >= val, "gt": n > val, "lte": n <= val, "lt": n < val, "eq": n == val}.get(op)
    return _t(f"count={n}") if ok else _f(f"count={n}")


def exists(ctx, args):
    results = _iter_atoms(ctx, args.get("atom"))
    if results is None:
        return _u("exists 仅支持带 at 参数的原子")
    n = sum(1 for r in results if r.value is True)
    return _t(f"命中 {n} 处") if n else _f()


def cite(ctx, args):
    cid = args.get("claim_id")
    if cid in (ctx.get("cited") or {}):
        return _t() if ctx["cited"][cid] is True else _f()
    return _u(f"被引命题 {cid} 未在本次求值中裁决")


ATOMS: dict[str, Callable[[dict, dict], AtomResult]] = {
    # 位置与透藏
    "visible_god": visible_god, "hidden_god": hidden_god, "stem_is": stem_is,
    "branch_is": branch_is, "sits_on": sits_on, "palace_holds": palace_holds,
    "rooted": rooted, "day_master": day_master,
    # 关系
    "edge": edge, "edge_touches": edge_touches, "chong_at": chong_at, "he_at": he_at,
    "chuan_at": chuan_at, "xing_at": xing_at, "po_at": po_at,
    "group_complete": group_complete, "distance_leq": distance_leq, "same_pillar": same_pillar,
    # 状态与力量
    "kongwang": kongwang, "muku_present": muku_present, "muku_open": muku_open,
    "ru_mu": ru_mu, "siling": siling, "camp_count": camp_count,
    "de_ling": de_ling, "tiaohou_at": tiaohou_at, "shensha": shensha,
    # 结构与做功
    "geju_met": geju_met, "geju_state": geju_state, "zuogong": zuogong,
    "tiyong": tiyong, "binzhu": binzhu, "structure_break": structure_break,
    "structure_rescue": structure_rescue, "lu_at": lu_at,
    # 岁运
    "dayun_present": dayun_present, "liunian_present": liunian_present,
    "suiyun_edge": suiyun_edge, "sanhe_with_suiyun": sanhe_with_suiyun,
    "chong_kai_muku": chong_kai_muku, "suiyun_arrives": suiyun_arrives,
    # 力量比较
    "can_control": can_control,
    # 元谓词
    "count": count, "exists": exists, "cite": cite,
    # 显式未知占位（v1.1）
    "needs_judgment": needs_judgment,
}

SIGNATURES: dict[str, dict[str, tuple[str, ...]]] = {
    "visible_god": (("god",), ("at", "as")),
    "hidden_god": (("god",), ("at", "qi", "as")),
    "stem_is": (("at", "gan"), ()),
    "branch_is": (("at", "zhi"), ()),
    "sits_on": (("god", "zhi"), ()),
    "palace_holds": (("god", "palace"), ()),
    "rooted": ((), ("god", "at", "min_qi")),
    "day_master": (("gan",), ()),
    "edge": (("type",), ("between", "as", "scope")),
    "edge_touches": (("type", "at"), ()),
    "chong_at": (("at",), ()),
    "he_at": (("at",), ("with_god", "exclude_god")),
    "chuan_at": (("at",), ()),
    "xing_at": (("at",), ()),
    "po_at": (("at",), ()),
    "group_complete": (("type",), ()),
    "distance_leq": (("a", "b", "n"), ()),
    "same_pillar": (("a", "b"), ()),
    "kongwang": (("at",), ()),
    "muku_present": ((), ("zhi",)),
    "muku_open": (("zhi",), ()),
    "ru_mu": (("star",), ()),
    "siling": ((), ("god",)),
    "camp_count": (("side", "op", "value"), ()),
    "de_ling": (("god",), ()),
    "tiaohou_at": (("char",), ()),
    "shensha": (("name",), ("at",)),
    "geju_met": ((), ("geju_type",)),
    "geju_state": (("state",), ("geju_type",)),
    "zuogong": ((), ("kind", "involves", "target_god", "actor_god", "actor_at", "target_at")),
    "tiyong": (("role",), ("at",)),
    "binzhu": (("layer",), ("side", "at")),
    "structure_break": ((), ("check",)),
    "structure_rescue": ((), ("check",)),
    "dayun_present": ((), ()),
    "liunian_present": ((), ("year",)),
    "suiyun_edge": (("type", "at"), ("scope",)),
    "sanhe_with_suiyun": ((), ("zhi_set",)),
    "chong_kai_muku": ((), ("zhi", "year")),
    "suiyun_arrives": (("at",), ("via",)),
    "can_control": (("actor", "target"), ()),
    "count": (("atom", "op", "value"), ()),
    "exists": (("atom",), ()),
    "cite": (("claim_id",), ()),
    "lu_at": ((), ("gan", "at")),
    "needs_judgment": (("reason",), ()),
}

# v1.1 新增 2 个（lu_at / needs_judgment），依据契约 23 §4.7 与 §九变更登记、ADR-007 D3/D12。
# v1.2 新增 2 个（suiyun_arrives / can_control），依据契约 23 §4.5、§4.8 与 §九、ADR-007 D3/D4。
assert len(ATOMS) == 46, f"原子表应为 46 个，实际 {len(ATOMS)}"
