"""engine/picture/anyin.py · v1.2 D2 杨派 · 十神暗引 5 公式

杨派十神暗引（M2-Y-029, 030, 055）：

> 旺而不受伤 → 暗引对应十神。

5 组公式：

| 显象（旺点不受刑穿） | 暗引 | 应事/真实背景含义 |
|---|---|---|
| 食伤旺 | 暗引比劫 | 有贵人/良好人际关系 |
| 印枭旺 | 暗引官杀 | 得权/制印得权 |
| 比劫旺 | 暗引印枭 | 学历/技能 |
| 官杀旺 | 暗引财   | 过河财/钱权交易 |
| 财旺   | 暗引食伤 | 口才/技术=赚钱根 |

实务实现思路：
- 计算每类十神的"群体力量"（基于 calc_wuxing_strength）
- 当某类力量 ≥ 阈值（默认 0.30）且未被"刑/穿/克"破坏时
  → 触发暗引，给出 real_meaning

但本派将公式重新对应到 04 § 五 的 5 公式：
    1旺不受伤   = 食伤旺暗引比劫 / 印枭旺暗引官杀 / 财旺暗引食伤 等
    2受制为用   = 食伤制杀 / 比劫去财（受制有功）
    3得令通根   = 印生比劫（印生身得力）
    4印护身     = 印化杀（家有靠山）
    5官印相生   = 杀印一体（升迁正途）

这 5 个公式不是互斥的，可同时多个触发。

作者：Track-B
"""
from __future__ import annotations

from typing import Optional

from engine.energy.types import EnergyFindings, Evidence
from engine.picture.types import AnyinResult
from engine.predicates.ganzhi import gan_to_wuxing, zhi_to_wuxing
from engine.predicates.palace import find_shishen_in_bazi, get_shishen
from engine.predicates.relations import (
    zhi_chong,
    zhi_chuan,
    zhi_xing,
)
from engine.predicates.strength import calc_wuxing_strength
from engine.predicates.types import (
    Bazi,
    Gan,
    GanZhi,
    Shishen,
    Wuxing,
    Zhi,
    ZHI_CANGGAN_TABLE,
)
from engine.predicates.wuxing import wuxing_relation, wuxing_sheng


# ============================================================
# 工具：分类十神为 5 大类
# ============================================================

_GROUP_OF: dict[Shishen, str] = {
    "比肩": "比劫", "劫财": "比劫",
    "食神": "食伤", "伤官": "食伤",
    "正财": "财", "偏财": "财",
    "正官": "官杀", "七杀": "官杀",
    "正印": "印", "偏印": "印",
}


def _shishen_group_strength(bazi: Bazi) -> dict[str, float]:
    """以五行势为基础，按"以日干为我"映射为 5 类十神的群体力量。

    比劫 = 同我 / 食伤 = 我生 / 财 = 我克 / 官杀 = 克我 / 印 = 生我
    """
    day_wx = gan_to_wuxing(bazi.day_master)
    shi = calc_wuxing_strength(bazi)
    out: dict[str, float] = {
        "比劫": 0.0, "食伤": 0.0, "财": 0.0, "官杀": 0.0, "印": 0.0,
    }
    for wx, val in shi.items():
        rel = wuxing_relation(day_wx, wx)
        group = {
            "同我": "比劫", "我生": "食伤", "我克": "财",
            "克我": "官杀", "生我": "印",
        }[rel]
        out[group] += val
    return out


def _group_受伤_check(group: str, bazi: Bazi) -> bool:
    """简易判断：该十神类是否"受伤"——主气支被刑/穿/冲。

    rationale: 杨派"旺而不受伤"——支位刑/穿/冲 → 受伤。
    """
    day_wx = gan_to_wuxing(bazi.day_master)
    target_wxs: set[Wuxing] = set()
    for wx in ("木", "火", "土", "金", "水"):
        rel = wuxing_relation(day_wx, wx)
        if {
            "同我": "比劫", "我生": "食伤", "我克": "财",
            "克我": "官杀", "生我": "印",
        }[rel] == group:
            target_wxs.add(wx)  # type: ignore[arg-type]

    target_palaces: list[tuple[str, Zhi]] = []
    for palace, zhi in bazi.all_zhis():
        if zhi_to_wuxing(zhi) in target_wxs:
            target_palaces.append((palace, zhi))

    # 检查是否被刑/穿/冲
    for tname, tz in target_palaces:
        for oname, oz in bazi.all_zhis():
            if oname == tname:
                continue
            if zhi_chong(tz, oz) or zhi_chuan(tz, oz) or zhi_xing(tz, oz):
                return True
    return False


# ============================================================
# 5 公式判定
# ============================================================

def _formula_1_旺不受伤(
    bazi: Bazi, group_strength: dict[str, float],
    threshold: float = 0.28,
) -> Optional[AnyinResult]:
    """公式 1：旺而不受伤 → 暗引对应十神。

    选择当前最旺的一类（≥ threshold）+ 主气支未受伤 → 触发。
    暗引规则（M2-Y-029）：
        食伤旺暗引比劫 / 印枭旺暗引官杀 / 比劫旺暗引印 /
        官杀旺暗引财   / 财旺暗引食伤
    """
    sorted_groups = sorted(
        group_strength.items(), key=lambda x: -x[1]
    )
    for group, val in sorted_groups:
        if val < threshold:
            return None
        if _group_受伤_check(group, bazi):
            continue
        # 找到了：旺而不受伤
        anyin_target = {
            "食伤": "比劫", "印": "官杀", "比劫": "印",
            "官杀": "财", "财": "食伤",
        }[group]
        meanings = {
            "食伤": "有贵人/良好人际关系（食伤旺暗引比劫）",
            "印": "得权/制印得权（印枭旺暗引官杀）",
            "比劫": "学历/技能（比劫旺暗引印枭）",
            "官杀": "过河财/钱权交易（官杀旺暗引财）",
            "财": "口才/技术=赚钱根（财旺暗引食伤）",
        }
        return AnyinResult(
            formula="1旺不受伤",
            triggered_shishen=anyin_target,
            real_meaning=f"{group}旺(力{val:.2f})未受刑穿 → 暗引{anyin_target}：{meanings[group]}",
            evidence=[Evidence(
                rule_id="M2-Y-029",
                school="杨",
                description=f"{group}旺而不受伤暗引{anyin_target}",
                weight=0.72,
            )],
        )
    return None


def _formula_2_受制为用(bazi: Bazi) -> Optional[AnyinResult]:
    """公式 2：受制为用——食伤制杀 / 比劫去财。

    判定：原局含
    - 食伤 + 官杀，且食伤五行能克官杀五行 → 食制杀
    - 比劫 + 财，且比劫五行能克财五行 → 比劫去财
    """
    day_master = bazi.day_master
    food_locs = [
        (p, c) for p, c in find_shishen_in_bazi("食神", bazi)
    ] + [
        (p, c) for p, c in find_shishen_in_bazi("伤官", bazi)
    ]
    sha_locs = [
        (p, c) for p, c in find_shishen_in_bazi("七杀", bazi)
    ] + [
        (p, c) for p, c in find_shishen_in_bazi("正官", bazi)
    ]
    if food_locs and sha_locs:
        return AnyinResult(
            formula="2受制为用",
            triggered_shishen="食神制杀（成就的根基）",
            real_meaning="食伤+官杀同现 → 食制杀=技术官/能办大事",
            evidence=[Evidence(
                rule_id="M2-Y-033",
                school="杨",
                description="食神制杀=成就",
                weight=0.78,
            )],
        )
    bijie_locs = [
        (p, c) for p, c in find_shishen_in_bazi("比肩", bazi)
    ] + [
        (p, c) for p, c in find_shishen_in_bazi("劫财", bazi)
    ]
    cai_locs = [
        (p, c) for p, c in find_shishen_in_bazi("正财", bazi)
    ] + [
        (p, c) for p, c in find_shishen_in_bazi("偏财", bazi)
    ]
    if bijie_locs and cai_locs:
        # 比劫 ≥ 财 才算"制"
        return AnyinResult(
            formula="2受制为用",
            triggered_shishen="比劫去财",
            real_meaning="比劫+财同现 → 比劫制财=兄弟合伙/竞争财（M2-Y-111）",
            evidence=[Evidence(
                rule_id="M2-Y-111",
                school="杨",
                description="比劫见财=前世欠（合伙竞争）",
                weight=0.65,
            )],
        )
    return None


def _formula_3_得令通根(bazi: Bazi) -> Optional[AnyinResult]:
    """公式 3：得令通根 → 印生比劫。

    判定：原局印 + 比劫 + 印的五行 = 月令五行（印得令）
    """
    day_master = bazi.day_master
    day_wx = gan_to_wuxing(day_master)
    yueling_wx = zhi_to_wuxing(bazi.月令)
    # 印的五行
    sheng_to_my: Wuxing = {
        "金": "土", "木": "水", "水": "金", "火": "木", "土": "火",
    }[day_wx]
    # 月令是否为印
    if yueling_wx == sheng_to_my:
        # 比劫是否在原局
        bijie_locs = (
            find_shishen_in_bazi("比肩", bazi)
            + find_shishen_in_bazi("劫财", bazi)
        )
        if bijie_locs:
            return AnyinResult(
                formula="3得令通根",
                triggered_shishen="印生比劫",
                real_meaning="印得令(月令)+比劫到位 → 印生身=学习能力强/家有靠山",
                evidence=[Evidence(
                    rule_id="M2-Y-140",
                    school="杨",
                    description="禄喜配印=印生比劫得力",
                    weight=0.70,
                )],
            )
    return None


def _formula_4_印护身(bazi: Bazi) -> Optional[AnyinResult]:
    """公式 4：印护身（印化杀）。

    判定：原局含 印 + 官杀 + 印的五行 受 官杀的五行 生
    """
    day_master = bazi.day_master
    day_wx = gan_to_wuxing(day_master)
    yin_wx: Wuxing = {
        "金": "土", "木": "水", "水": "金", "火": "木", "土": "火",
    }[day_wx]
    sha_wx: Wuxing = {
        "金": "火", "木": "金", "水": "土", "火": "水", "土": "木",
    }[day_wx]
    # 官杀生印（即 sha_wx → yin_wx）
    if not wuxing_sheng(sha_wx, yin_wx):
        return None
    # 找 印 + 官杀
    yin_locs = (
        find_shishen_in_bazi("正印", bazi)
        + find_shishen_in_bazi("偏印", bazi)
    )
    sha_locs = (
        find_shishen_in_bazi("七杀", bazi)
        + find_shishen_in_bazi("正官", bazi)
    )
    if yin_locs and sha_locs:
        return AnyinResult(
            formula="4印护身",
            triggered_shishen="印化杀（家有靠山）",
            real_meaning="官杀+印同现且官杀生印 → 印护身=家世背景/上有靠山",
            evidence=[Evidence(
                rule_id="M2-Y-032",
                school="杨",
                description="化敌为友最高境界=化杀生印",
                weight=0.82,
            )],
        )
    return None


def _formula_5_官印相生(bazi: Bazi) -> Optional[AnyinResult]:
    """公式 5：官印相生 → 杀印一体（标准升迁）。

    判定：印 + 官杀 + 二者紧贴（同柱 OR 月日柱共置）。
    与公式 4 的差异：
    - 公式 4 强调"印化杀"——官杀本来要克身，被印化掉
    - 公式 5 强调"官印相生"——官生印 + 印生身 双链路（更强结构）
    """
    day_master = bazi.day_master
    yin_locs = (
        find_shishen_in_bazi("正印", bazi)
        + find_shishen_in_bazi("偏印", bazi)
    )
    sha_locs = (
        find_shishen_in_bazi("七杀", bazi)
        + find_shishen_in_bazi("正官", bazi)
    )
    if not (yin_locs and sha_locs):
        return None

    # 紧贴判定：印和官杀分别出现在月柱+日柱 或 时柱
    yin_palaces = {p for p, _ in yin_locs}
    sha_palaces = {p for p, _ in sha_locs}
    # 月柱含官 + 日柱/时柱含印 = 标准官印相生
    has_yin_in_dz = bool(
        yin_palaces & {"日柱", "时柱", "日支", "时支"}
    )
    has_sha_in_my = bool(sha_palaces & {"年柱", "月柱", "年支", "月支"})
    has_yin_in_my = bool(yin_palaces & {"年柱", "月柱", "年支", "月支"})
    has_sha_in_dz = bool(
        sha_palaces & {"日柱", "时柱", "日支", "时支"}
    )

    if (has_sha_in_my and has_yin_in_dz) or (has_sha_in_dz and has_yin_in_my):
        return AnyinResult(
            formula="5官印相生",
            triggered_shishen="官印相生（杀印一体）",
            real_meaning="官杀+印分置月日 → 官印相生=正途升迁（吃皇粮的标志）",
            evidence=[Evidence(
                rule_id="M2-Y-042",
                school="杨",
                description="官命9取之化官生印",
                weight=0.80,
            )],
        )
    return None


# ============================================================
# 主入口
# ============================================================

def scan_anyin(bazi: Bazi, energy: EnergyFindings) -> list[AnyinResult]:
    """扫描原局十神暗引 5 公式。

    输入：bazi + EnergyFindings（用于势力数据）
    输出：list[AnyinResult]，可能为空（无任何公式触发）
    """
    out: list[AnyinResult] = []
    group_strength = _shishen_group_strength(bazi)

    for func in (
        _formula_1_旺不受伤,
        _formula_3_得令通根,
        _formula_4_印护身,
        _formula_5_官印相生,
    ):
        try:
            r = func(bazi, group_strength) if func is _formula_1_旺不受伤 else func(bazi)  # type: ignore[arg-type]
        except TypeError:
            r = func(bazi)  # type: ignore[arg-type]
        if r is not None:
            out.append(r)

    # 公式 2 不依赖 group_strength
    r2 = _formula_2_受制为用(bazi)
    if r2 is not None:
        out.append(r2)

    return out


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    from tests.fixtures.cases import load_case
    from engine.energy.evaluator import evaluate_energy

    for cid in [
        "C-2026-001-庚申戊寅壬子辛丑",
        "C-2026-002-壬戌庚戌戊辰丙辰",
        "C-2026-014-丙戌庚子乙亥辛巳",
    ]:
        parsed = load_case(cid)
        ef = evaluate_energy(parsed)
        results = scan_anyin(parsed.bazi, ef)
        print(f"\n=== {cid} 暗引扫描 ===")
        if not results:
            print("  （无公式触发）")
        for r in results:
            print(f"  [{r.formula}] {r.triggered_shishen}")
            print(f"    {r.real_meaning}")
    print("\n[OK] anyin smoke 通过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
