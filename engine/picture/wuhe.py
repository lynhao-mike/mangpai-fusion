"""engine/picture/wuhe.py · v1.2 D2 杨派 · 天干五合扫描

杨派天干五合（M2-Y-005, 024-028）：
- 天干五合做功效率最高
- 5 组：甲己土 / 乙庚金 / 丙辛水 / 丁壬木 / 戊癸火
- 三状态：化成 / 合绊 / 搅局
- 应事表：合财=得财得妻；合官=升职得权；合印=得学历得房；
         合食伤=得技术口才；合比劫=得朋友合伙

化成判定（M2-Y-025, 053）：
- 紧贴（相邻天干）
- 地支有化神根（化神得令或主气支为化神五行）
- 月令不克化神
- 无搅局星

搅局星（M2-Y-026）：
- 庚搅甲己 / 辛搅乙庚 / 壬搅丙辛 / 癸搅丁壬 / 甲搅戊癸
- 即"克合首者"——5 组各有自己的搅局星

输入：Bazi
输出：list[WuheRelation]

作者：Track-B
"""
from __future__ import annotations

from typing import Optional

from engine.energy.types import Evidence
from engine.picture.types import WuheRelation
from engine.predicates.ganzhi import (
    gan_to_wuxing,
    gan_yinyang,
    zhi_to_wuxing,
)
from engine.predicates.palace import get_shishen
from engine.predicates.relations import gan_he
from engine.predicates.strength import calc_wuxing_strength
from engine.predicates.types import (
    Bazi,
    Gan,
    GanZhi,
    Wuxing,
)


# ============================================================
# 五合应事表（M2-Y-027）
# ============================================================

# 化神 五行 → 应事关键词（结合合的角色）
_HUASHEN_IMAGERY: dict[Wuxing, str] = {
    "土": "药/化妆品/面粉/饮食/房地产",
    "金": "钞票/武器/首饰/工具/钢铁",
    "水": "酒/化学品/化工/发电/流通",
    "木": "文化/文字/木材/教育/印刷/传媒",
    "火": "西药/药物/颜色/信仰/名声",
}

# 角色 → 应事
_ROLE_IMAGERY: dict[str, str] = {
    "正财": "得妻得财/合作", "偏财": "得财/合作",
    "正官": "升职得权/考试", "七杀": "得权/竞争",
    "正印": "得学历得房/母助", "偏印": "得学历/技能/房产",
    "食神": "得技术/口才/子女缘", "伤官": "口才/才华/项目",
    "比肩": "得朋友/合伙", "劫财": "得助力/合伙",
}


# ============================================================
# 搅局星表（M2-Y-026）
# ============================================================
# 克合首者（合首=每对的"前位"=阳干）
_JIAOJU_TABLE: dict[frozenset, Gan] = {
    frozenset(("甲", "己")): "庚",   # 庚克甲
    frozenset(("乙", "庚")): "辛",   # 辛克庚?? 同行不克...
    frozenset(("丙", "辛")): "壬",   # 壬克丙
    frozenset(("丁", "壬")): "癸",   # 癸克丁?? 同行水不克水
    frozenset(("戊", "癸")): "甲",   # 甲克戊
}
# 修正：搅局星 = 克"该合化神来源"的字
# 严格按 M2-Y-026 经典 6 组：庚甲己 / 辛乙庚 / 壬丙辛 / 癸丁壬 / 甲戊癸 / 乙己甲
# 即每组合中阳干的克者（庚克甲、辛克庚等）
_JIAOJU_TABLE_STRICT: dict[frozenset, list[Gan]] = {
    frozenset(("甲", "己")): ["庚"],         # 庚克甲（克合首）
    frozenset(("乙", "庚")): ["辛", "丙"],   # 辛搅乙庚（辛同金来抢化神金）；丙克庚
    frozenset(("丙", "辛")): ["壬"],         # 壬克丙
    frozenset(("丁", "壬")): ["癸", "戊"],   # 癸克丁；戊克壬
    frozenset(("戊", "癸")): ["甲", "己"],   # 甲克戊；己合甲拐走
}


# ============================================================
# 化神得令判定
# ============================================================

def _huashen_dejin(huashen: Wuxing, yueling: str, shi: dict) -> bool:
    """化神是否得令（月令支为化神五行 OR 化神势力 ≥ 0.30）。"""
    if zhi_to_wuxing(yueling) == huashen:
        return True
    return shi.get(huashen, 0.0) >= 0.30


def _has_huashen_root_in_zhi(huashen: Wuxing, bazi: Bazi) -> bool:
    """是否有地支根（地支主气为化神五行）。"""
    for _, zhi in bazi.all_zhis():
        if zhi_to_wuxing(zhi) == huashen:
            return True
    return False


def _check_jiaoju(pair: frozenset, bazi: Bazi) -> Optional[Gan]:
    """检查是否有搅局星出现在原局天干（不算两干本身）。"""
    candidates = _JIAOJU_TABLE_STRICT.get(pair, [])
    pair_set = set(pair)
    for _, gan in bazi.all_gans():
        if gan in pair_set:
            continue
        if gan in candidates:
            return gan
    return None


# ============================================================
# 主入口
# ============================================================

def scan_wuhe(bazi: Bazi) -> list[WuheRelation]:
    """扫描原局所有天干五合关系。

    遍历 4 干两两组合，判定：
    - 是否构成五合
    - 状态（化成/合绊/搅局）
    - 应事映射
    """
    out: list[WuheRelation] = []
    gans_with_palace = bazi.all_gans()
    day_master = bazi.day_master
    yueling = bazi.月令
    shi = calc_wuxing_strength(bazi)

    seen: set[frozenset] = set()

    for i in range(len(gans_with_palace)):
        for j in range(i + 1, len(gans_with_palace)):
            (pa, ga), (pb, gb) = gans_with_palace[i], gans_with_palace[j]
            if ga == gb:
                continue
            pair_set = frozenset((ga, gb))
            if pair_set in seen:
                continue
            he_result = gan_he(ga, gb)
            if he_result is None:
                continue
            seen.add(pair_set)
            huashen, _default_state = he_result

            # 紧贴度判断（相邻 = 紧贴；相隔 = 间合）
            palace_order = ("年柱", "月柱", "日柱", "时柱")
            try:
                idx_a = palace_order.index(pa)
                idx_b = palace_order.index(pb)
                adjacent = abs(idx_a - idx_b) == 1
            except ValueError:
                adjacent = False

            # 判化成 4 条件
            jiaoju_gan = _check_jiaoju(pair_set, bazi)
            has_root = _has_huashen_root_in_zhi(huashen, bazi)
            dejin = _huashen_dejin(huashen, yueling, shi)
            yueling_does_not_克_huashen = (
                zhi_to_wuxing(yueling) != _wuxing_kemy(huashen)
            )

            if jiaoju_gan is not None:
                state = "搅局"
                rationale = (
                    f"{ga}{gb}合化{huashen}，"
                    f"但天干{jiaoju_gan}搅局 → 合被拆"
                )
            elif adjacent and has_root and dejin and yueling_does_not_克_huashen:
                state = "化成"
                rationale = (
                    f"{ga}{gb}合化{huashen}：紧贴+地支有根+化神得令+月令不克 → 真化"
                )
            else:
                state = "合绊"
                missing = []
                if not adjacent:
                    missing.append("不紧贴")
                if not has_root:
                    missing.append("无化神根")
                if not dejin:
                    missing.append("化神不得令")
                if not yueling_does_not_克_huashen:
                    missing.append("月令克化神")
                rationale = (
                    f"{ga}{gb}合化{huashen}：{','.join(missing) or '条件不全'}"
                    f" → 合而不化（合绊）"
                )

            # 应事：以"合到主位（日干所在合）"判断角色
            yingshi_parts = [_HUASHEN_IMAGERY.get(huashen, "")]
            # 合的角色（合的对象的十神）
            if ga == day_master:
                # 日干合 → 看 gb 的十神
                ss_gb = get_shishen(gb, day_master)
                yingshi_parts.append(_ROLE_IMAGERY.get(ss_gb, ""))
                yingshi_parts.append(f"日主合{ss_gb}=亲身得")
            elif gb == day_master:
                ss_ga = get_shishen(ga, day_master)
                yingshi_parts.append(_ROLE_IMAGERY.get(ss_ga, ""))
                yingshi_parts.append(f"日主合{ss_ga}=亲身得")
            else:
                # 双方都非日干 → 环境象
                ss_ga = get_shishen(ga, day_master)
                ss_gb = get_shishen(gb, day_master)
                yingshi_parts.append(
                    f"{ga}({ss_ga}) ↔ {gb}({ss_gb}) = 环境象"
                )
            yingshi = "；".join([p for p in yingshi_parts if p])

            out.append(WuheRelation(
                pair=(ga, gb),
                化神=huashen,
                state=state,
                palaces=(pa, pb),
                应事=yingshi,
                rationale=rationale,
            ))
    return out


def _wuxing_kemy(w: Wuxing) -> Wuxing:
    """返回克 w 的五行（"克我者"）。"""
    return {"金": "火", "木": "金", "水": "土", "火": "水", "土": "木"}[w]


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    from tests.fixtures.cases import load_case

    for cid in [
        "C-2026-001-庚申戊寅壬子辛丑",
        "C-2026-002-壬戌庚戌戊辰丙辰",
        "C-2026-014-丙戌庚子乙亥辛巳",
        "C-2026-011-乙丑乙酉丁丑癸卯",
    ]:
        parsed = load_case(cid)
        rels = scan_wuhe(parsed.bazi)
        print(f"\n=== {cid} 五合扫描 ===")
        if not rels:
            print("  （无五合）")
        for r in rels:
            print(
                f"  [{r.state}] {r.pair[0]}{r.pair[1]} 化{r.化神} "
                f"({r.palaces[0]}+{r.palaces[1]}) - {r.rationale}"
            )
            print(f"     应事: {r.应事}")

    print("\n[OK] wuhe smoke 通过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
