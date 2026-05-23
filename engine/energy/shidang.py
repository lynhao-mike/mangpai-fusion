"""engine/energy/shidang.py · v1.2 D1 段派 · 势 + 党

段派"势与党"（M1-D-017..020, 122..123, 123）：

势（M1-D-017..018）：
    单一五行强大 = 单势
    - 木旺势 / 火旺势 / 金旺势 / 水旺势
    - 土势二分：燥土（戌未为主） vs 湿土（辰丑为主）

党（M1-D-019..020）：
    多五行相生形成"党"
    双党 6 种（相生组合）：
      印比党（金水/水木 等）/ 比食党 / 食财党 /
      财官党 / 官印党 / 混党
    三五行党（含土）：常见为印比比党/食财官党 等

势/党的功能（M1-D-122）：
    - 富贵贫贱三档判定 = 势 + 功 / 有功无势 / 无功
    - 党即"我方阵营"，党党合 = 大势已成

输入：Bazi + TiyongStructure
输出：ShiDang
"""
from __future__ import annotations

from typing import Optional

from engine.energy.types import ShiDang, TiyongStructure
from engine.predicates.types import (
    Bazi,
    Gan,
    GanZhi,
    Wuxing,
    Zhi,
)
from engine.predicates.ganzhi import gan_to_wuxing, zhi_to_wuxing
from engine.predicates.strength import calc_wuxing_strength
from engine.predicates.wuxing import wuxing_relation, wuxing_sheng


# ============================================================
# 势/党 描述
# ============================================================

# 单势阈值：某五行 ≥ 0.40 = 单势成立
SINGLE_DOMINANT_THRESHOLD = 0.40
# 双党阈值：相生两五行各 ≥ 0.20 + 合计 ≥ 0.50
DUAL_PARTY_PAIR_MIN = 0.20
DUAL_PARTY_TOTAL_MIN = 0.50


def _classify_tu(bazi: Bazi) -> str:
    """土的二分：燥土 / 湿土。

    戌未 = 燥土；辰丑 = 湿土。两类都有则按数量多者算。
    """
    dry = sum(1 for _, z in bazi.all_zhis() if z in ("戌", "未"))
    wet = sum(1 for _, z in bazi.all_zhis() if z in ("辰", "丑"))
    if dry == 0 and wet == 0:
        return "土"
    if dry > wet:
        return "燥土"
    if wet > dry:
        return "湿土"
    return "燥湿土均"


def _detect_single_dominant(shi: dict[Wuxing, float], bazi: Bazi) -> list[tuple[str, str]]:
    """检测单势（单一五行独旺）。"""
    dang: list[tuple[str, str]] = []
    sorted_shi = sorted(shi.items(), key=lambda x: -x[1])
    top_wx, top_v = sorted_shi[0]
    if top_v >= SINGLE_DOMINANT_THRESHOLD:
        if top_wx == "土":
            tu_kind = _classify_tu(bazi)
            dang.append((top_wx, f"单势·{tu_kind}（势力 {top_v:.0%}）"))
        else:
            dang.append((top_wx, f"单势·{top_wx}旺（势力 {top_v:.0%}）"))
    return dang


def _detect_dual_party(shi: dict[Wuxing, float]) -> list[tuple[str, str]]:
    """检测双党：相生两五行联合占主导。

    返回类似 [("水金", "印生比党/印比党"), ...]
    """
    dang: list[tuple[str, str]] = []
    # 五行相生序
    sheng_pairs: list[tuple[Wuxing, Wuxing]] = [
        ("水", "木"), ("木", "火"), ("火", "土"),
        ("土", "金"), ("金", "水"),
    ]
    for a, b in sheng_pairs:
        sa, sb = shi.get(a, 0.0), shi.get(b, 0.0)
        total = sa + sb
        if sa >= DUAL_PARTY_PAIR_MIN and sb >= DUAL_PARTY_PAIR_MIN and total >= DUAL_PARTY_TOTAL_MIN:
            dang.append((f"{a}{b}", f"双党·{a}生{b}（合计 {total:.0%}）"))
    return dang


def _detect_triple_party(shi: dict[Wuxing, float]) -> list[tuple[str, str]]:
    """检测三五行党（含土的三方相生组合）。"""
    dang: list[tuple[str, str]] = []
    sheng_chains: list[tuple[Wuxing, Wuxing, Wuxing]] = [
        ("水", "木", "火"),  # 印→比→食 或 财→官→印（视日干）
        ("木", "火", "土"),
        ("火", "土", "金"),
        ("土", "金", "水"),
        ("金", "水", "木"),
    ]
    for a, b, c in sheng_chains:
        s = shi.get(a, 0) + shi.get(b, 0) + shi.get(c, 0)
        # 三方各 ≥ 0.10 + 合计 ≥ 0.65
        if min(shi.get(a, 0), shi.get(b, 0), shi.get(c, 0)) >= 0.10 and s >= 0.65:
            dang.append((f"{a}{b}{c}", f"三党·{a}→{b}→{c}（合计 {s:.0%}）"))
    return dang


def _label_in_terms_of_day(bazi: Bazi, dual_pairs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """把"水生木"翻译成"印生比党"等十神语义（仅给 description 加注）。"""
    day_wx = gan_to_wuxing(bazi.day_master)
    role_map = {
        "同我": "比劫",
        "生我": "印",
        "我生": "食伤",
        "我克": "财",
        "克我": "官杀",
    }
    out: list[tuple[str, str]] = []
    for label, desc in dual_pairs:
        if len(label) == 2:
            a, b = label[0], label[1]
            ra = role_map[wuxing_relation(day_wx, a)]
            rb = role_map[wuxing_relation(day_wx, b)]
            out.append((label, f"{desc} = 段派 {ra}生{rb}党"))
        else:
            out.append((label, desc))
    return out


# ============================================================
# 主入口
# ============================================================

def evaluate_shidang(bazi: Bazi, tiyong: Optional[TiyongStructure] = None) -> ShiDang:
    """段派势 + 党判定。

    返回 ShiDang：含 5 行势力 + 党形态（12 种之一或多个组合）。
    """
    shi = calc_wuxing_strength(bazi)

    dang: list[tuple[str, str]] = []
    dang.extend(_detect_single_dominant(shi, bazi))
    dual = _detect_dual_party(shi)
    dang.extend(_label_in_terms_of_day(bazi, dual))
    dang.extend(_detect_triple_party(shi))

    if not dang:
        # 无势无党 → 杂混局
        dang.append(("杂", f"无单势无党，杂混局（最大五行 {max(shi.values()):.0%}）"))

    # 描述
    summary = ", ".join(f"{wx}={v:.0%}" for wx, v in sorted(shi.items(), key=lambda x: -x[1]))
    description = f"段派势/党（M1-D-122..123）：[{summary}]; 党形态：{len(dang)} 个"

    return ShiDang(
        shi={k: round(v, 4) for k, v in shi.items()},
        dang=dang,
        description=description,
    )


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    from engine.predicates.types import _default_canggan_for

    cases = {
        "C-2026-001": ("庚", "申", "戊", "寅", "壬", "子", "辛", "丑"),
        "C-2026-002": ("壬", "戌", "庚", "戌", "戊", "辰", "丙", "辰"),
        "C-2026-014": ("丙", "戌", "庚", "子", "乙", "亥", "辛", "巳"),
        "C-2026-011": ("乙", "丑", "乙", "酉", "丁", "丑", "癸", "卯"),
        "C-2026-012": ("壬", "戌", "癸", "丑", "丙", "申", "壬", "辰"),
    }
    for cid, parts in cases.items():
        b = Bazi(
            年柱=GanZhi(parts[0], parts[1]),
            月柱=GanZhi(parts[2], parts[3]),
            日柱=GanZhi(parts[4], parts[5]),
            时柱=GanZhi(parts[6], parts[7]),
        )
        b.藏干 = _default_canggan_for(b)
        sd = evaluate_shidang(b)
        print(f"\n=== {cid} 势/党 ===")
        print(f"  势: {sd.shi}")
        print(f"  党: {sd.dang}")

    print("\n[OK] shidang smoke 通过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
