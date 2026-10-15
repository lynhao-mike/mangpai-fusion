"""客观神煞查表事实；仅报告命中，不作吉凶判断或评分。"""
from __future__ import annotations

from dataclasses import dataclass

from engine.facts.types import ChartFacts


@dataclass(frozen=True)
class ShenshaHit:
    """一条可追溯的神煞命中记录。"""

    name: str
    anchor_addr: str
    target_addr: str
    method_note: str
    source_ref: str


_SOURCE = "sources/gao/盲派神煞应用宝典.md:"
_BRANCH_ADDRS = ("Y.b", "M.b", "D.b", "H.b")
_STEM_ADDRS = ("Y.s", "M.s", "D.s", "H.s")

# 三合局中神煞取支表；每项以起法支为键，命中支为值。
_TRAVEL_HORSE = {"申": "寅", "子": "寅", "辰": "寅", "寅": "申", "午": "申", "戌": "申",
                 "巳": "亥", "酉": "亥", "丑": "亥", "亥": "巳", "卯": "巳", "未": "巳"}
_FLOWER = {"申": "酉", "子": "酉", "辰": "酉", "寅": "卯", "午": "卯", "戌": "卯",
           "巳": "午", "酉": "午", "丑": "午", "亥": "子", "卯": "子", "未": "子"}
_CANOPY = {"寅": "戌", "午": "戌", "戌": "戌", "亥": "未", "卯": "未", "未": "未",
           "申": "辰", "子": "辰", "辰": "辰", "巳": "丑", "酉": "丑", "丑": "丑"}
_GENERAL = {"寅": "午", "午": "午", "戌": "午", "申": "子", "子": "子", "辰": "子",
            "亥": "卯", "卯": "卯", "未": "卯", "巳": "酉", "酉": "酉", "丑": "酉"}
_DECEASED_SPIRIT = {"寅": "巳", "午": "巳", "戌": "巳", "亥": "寅", "卯": "寅", "未": "寅",
                    "巳": "申", "酉": "申", "丑": "申", "申": "亥", "子": "亥", "辰": "亥"}
_ROBBERY = {"申": "巳", "子": "巳", "辰": "巳", "亥": "申", "卯": "申", "未": "申",
            "寅": "亥", "午": "亥", "戌": "亥", "巳": "寅", "酉": "寅", "丑": "寅"}
_DISASTER = {"申": "午", "子": "午", "辰": "午", "亥": "酉", "卯": "酉", "未": "酉",
             "寅": "子", "午": "子", "戌": "子", "巳": "卯", "酉": "卯", "丑": "卯"}
_LONE = {"亥": ("孤辰", "寅"), "子": ("孤辰", "寅"), "丑": ("孤辰", "寅"),
         "寅": ("孤辰", "巳"), "卯": ("孤辰", "巳"), "辰": ("孤辰", "巳"),
         "巳": ("孤辰", "申"), "午": ("孤辰", "申"), "未": ("孤辰", "申"),
         "申": ("孤辰", "亥"), "酉": ("孤辰", "亥"), "戌": ("孤辰", "亥")}
_LONELY_WIDOW = {"亥": "戌", "子": "戌", "丑": "戌", "寅": "丑", "卯": "丑", "辰": "丑",
                 "巳": "辰", "午": "辰", "未": "辰", "申": "未", "酉": "未", "戌": "未"}

# 天乙贵人：经典日干口诀，与文中另述昼夜贵人规则分开计算。
_TIAN_YI_CLASSIC = {
    "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
    "乙": ("申", "子"), "己": ("申", "子"),
    "丙": ("酉", "亥"), "丁": ("酉", "亥"),
    "辛": ("寅", "午"), "壬": ("卯", "巳"), "癸": ("卯", "巳"),
}
_TIAN_YI_YANG = {"甲": "丑", "戊": "丑", "庚": "丑", "乙": "子", "己": "子",
                 "丙": "亥", "丁": "亥", "辛": "寅", "壬": "卯", "癸": "卯"}
_TIAN_YI_YIN = {"甲": "未", "戊": "未", "庚": "未", "乙": "申", "己": "申",
                "丙": "酉", "丁": "酉", "辛": "午", "壬": "巳", "癸": "巳"}
# 此处按来源的命宫节阴阳：卯辰巳午未申为阳，其余为阴。
_DAY_BRANCH_YANG = frozenset("卯辰巳午未申")

_MONTH_VIRTUE = {"寅": "丙", "午": "丙", "戌": "丙", "申": "壬", "子": "壬", "辰": "壬",
                 "亥": "甲", "卯": "甲", "未": "甲", "巳": "庚", "酉": "庚", "丑": "庚"}
_HEAVENLY_VIRTUE = {"寅": ("丁", "丁"), "卯": ("申", "申"), "辰": ("壬", "壬"), "巳": ("辛", "辛"),
                    "午": ("亥", "亥"), "未": ("甲", "甲"), "申": ("癸", "癸"), "酉": ("寅", "寅"),
                    "戌": ("丙", "丙"), "亥": ("乙", "乙"), "子": ("巳", "巳"), "丑": ("庚", "庚")}
_KUI_GANG = frozenset(("壬辰", "庚戌", "庚辰", "戊戌"))

# 高派阴阳刃、飞刃(阴阳)取法：羊刃/阴刃起于日干，飞刃为相冲之支。
_YANG_BLADE = {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}
_YIN_BLADE = {"乙": "辰", "丁": "未", "己": "未", "辛": "戌", "癸": "丑"}
_FLYING_BLADE_YANG = {"甲": "酉", "丙": "子", "戊": "子", "庚": "卯", "壬": "午"}
_FLYING_BLADE_YIN = {"乙": "戌", "丁": "丑", "己": "丑", "辛": "辰", "癸": "未"}


def _branches(chart: ChartFacts) -> tuple[str, ...]:
    return tuple(p.branch.char for p in chart.pillars)


def _stems(chart: ChartFacts) -> tuple[str, ...]:
    return tuple(p.stem.char for p in chart.pillars)


def _dual_anchor_hits(
    chart: ChartFacts,
    table: dict[str, str],
    name: str,
    source_line: str,
    method: str,
) -> list[ShenshaHit]:
    branches = _branches(chart)
    hits: list[ShenshaHit] = []
    for anchor_index in (0, 2):
        anchor = branches[anchor_index]
        target = table[anchor]
        for target_index, branch in enumerate(branches):
            if target_index != anchor_index and branch == target:
                hits.append(ShenshaHit(
                    name, _BRANCH_ADDRS[anchor_index], _BRANCH_ADDRS[target_index],
                    method, _SOURCE + source_line,
                ))
    return hits


def _stem_rule_hits(
    chart: ChartFacts,
    table: dict[str, str | tuple[str, ...]],
    name: str,
    source_line: str,
    method: str,
) -> list[ShenshaHit]:
    stems = _stems(chart)
    branches = _branches(chart)
    anchor_stem = stems[2]
    targets = table.get(anchor_stem, ())
    if isinstance(targets, str):
        targets = (targets,)
    return [
        ShenshaHit(name, "D.s", _BRANCH_ADDRS[i], method, _SOURCE + source_line)
        for i, branch in enumerate(branches) if branch in targets
    ]


def find_shensha(chart: ChartFacts) -> tuple[ShenshaHit, ...]:
    """按固定口诀扫描原局神煞，返回带起法坐标与出处的客观命中。"""
    hits: list[ShenshaHit] = []
    dual_rules = (
        (_TRAVEL_HORSE, "驿马", "584", "年支、日支分别按申子辰马在寅等口诀起法，扫描其余三支。"),
        (_FLOWER, "桃花", "708", "年支、日支分别按三合局桃花表起法，扫描其余三支。"),
        (_CANOPY, "华盖", "652-654", "年支、日支分别按三合局华盖表起法，扫描其余三支。"),
        (_GENERAL, "将星", "322-324", "年支、日支分别按三合局中神起法，扫描其余三支。"),
        (_DECEASED_SPIRIT, "亡神", "993-995", "年支、日支分别起亡神；仅在四柱具备对应完整三合局时取用。"),
        (_ROBBERY, "劫煞", "1009-1014", "年支、日支分别按口诀起劫煞，扫描其余三支。"),
        (_DISASTER, "灾煞", "1036", "年支、日支分别按同一表扩展扫描；出处原文明确以年支为主，日支为扩展口径。"),
    )
    branches = _branches(chart)
    for table, name, line, method in dual_rules:
        for hit in _dual_anchor_hits(chart, table, name, line, method):
            if name != "亡神" or set(_SANHE[branches[(0 if hit.anchor_addr == "Y.b" else 2)]]) <= set(branches):
                hits.append(hit)

    for anchor_index in (0, 2):
        anchor = branches[anchor_index]
        name, target = _LONE[anchor]
        for target_index, branch in enumerate(branches):
            if target_index != anchor_index and branch == target:
                hits.append(ShenshaHit(
                    name, _BRANCH_ADDRS[anchor_index], _BRANCH_ADDRS[target_index],
                    "年支、日支分别起孤辰表，扫描其余三支。", _SOURCE + "945",
                ))
        for target_index, branch in enumerate(branches):
            if target_index != anchor_index and branch == _LONELY_WIDOW[anchor]:
                hits.append(ShenshaHit(
                    "寡宿", _BRANCH_ADDRS[anchor_index], _BRANCH_ADDRS[target_index],
                    "年支、日支分别起寡宿表，扫描其余三支。", _SOURCE + "945",
                ))

    hits.extend(_stem_rule_hits(
        chart, _TIAN_YI_CLASSIC, "天乙贵人", "263-268",
        "经典口诀‘甲戊庚牛羊…’，以日干起贵人，四柱地支见者记录。",
    ))
    day_stem = chart.day_master
    day_branch = branches[2]
    # 来源规定：日元地支属阴取阳贵人，属阳取阴贵人。
    day_night_target = _TIAN_YI_YIN[day_stem] if day_branch in _DAY_BRANCH_YANG else _TIAN_YI_YANG[day_stem]
    for i, branch in enumerate(branches):
        if branch == day_night_target:
            hits.append(ShenshaHit(
                "天乙贵人(昼夜贵人)", "D.s", _BRANCH_ADDRS[i],
                "依日元地支命宫节阴阳取贵：阴支取阳贵、阳支取阴贵；与经典日干法分开记录。",
                _SOURCE + "296-300",
            ))

    # 天德以月支起天干，月德依月令三合组起天干。
    month_branch = branches[1]
    heavenly_stem = _HEAVENLY_VIRTUE[month_branch][0]
    for i, stem in enumerate(_stems(chart)):
        if stem == heavenly_stem:
            hits.append(ShenshaHit(
                "天德贵人", "M.b", _STEM_ADDRS[i], "按月支对应天德干，四柱天干见者记录。", _SOURCE + "392",
            ))
    monthly_stem = _MONTH_VIRTUE[month_branch]
    for i, stem in enumerate(_stems(chart)):
        if stem == monthly_stem:
            hits.append(ShenshaHit(
                "月德贵人", "M.b", _STEM_ADDRS[i], "按月令三合组对应月德干，四柱天干见者记录。", _SOURCE + "411",
            ))

    hits.extend(_stem_rule_hits(
        chart, _YANG_BLADE, "羊刃", "1095", "五阳干按禄后一位起阳刃，以日干为起点，四柱地支见者记录。",
    ))
    hits.extend(_stem_rule_hits(
        chart, _YIN_BLADE, "阴刃", "1095", "五阴干按逆行禄前一位起阴刃，以日干为起点，四柱地支见者记录。",
    ))
    hits.extend(_stem_rule_hits(
        chart, _FLYING_BLADE_YANG, "飞刃(阳)", "1095-1098", "五阳干阳刃所冲之支为飞刃，以日干为起点。",
    ))
    hits.extend(_stem_rule_hits(
        chart, _FLYING_BLADE_YIN, "飞刃(阴)", "1095-1099", "五阴干阴刃所冲之支为飞刃(阴)，以日干为起点。",
    ))

    if chart.pillars[2].ganzhi in _KUI_GANG:
        hits.append(ShenshaHit(
            "魁罡", "D", "D", "仅以日柱干支查壬辰、庚戌、庚辰、戊戌四日。", _SOURCE + "470",
        ))
    return tuple(hits)


_SANHE = {
    "寅": ("寅", "午", "戌"), "午": ("寅", "午", "戌"), "戌": ("寅", "午", "戌"),
    "亥": ("亥", "卯", "未"), "卯": ("亥", "卯", "未"), "未": ("亥", "卯", "未"),
    "申": ("申", "子", "辰"), "子": ("申", "子", "辰"), "辰": ("申", "子", "辰"),
    "巳": ("巳", "酉", "丑"), "酉": ("巳", "酉", "丑"), "丑": ("巳", "酉", "丑"),
}


__all__ = ["ShenshaHit", "find_shensha"]
