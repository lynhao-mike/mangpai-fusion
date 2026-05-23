"""engine/predicates/palace.py · v1.2 宫位与十神谓词（10 函数）

实现 02-predicate-library.md § 4.4 全部 10 个函数。

本派核心（杨派 + 段派共用）：
    十神 = 以日干为"我"的视角，看其余九字相对我的关系。
    五行关系五分（同/我生/我克/克我/生我）+ 阴阳同异 = 10 神。

阴阳同 = 偏；阴阳异 = 正：
    比肩(同行同阴阳)  劫财(同行异阴阳)
    食神(我生同阴阳)  伤官(我生异阴阳)
    偏财(我克同阴阳)  正财(我克异阴阳)
    七杀(克我同阴阳)  正官(克我异阴阳)
    偏印(生我同阴阳)  正印(生我异阴阳)

作者：Track-B
"""
from __future__ import annotations

from typing import Optional, Union

from engine.predicates.types import (
    Bazi,
    Canggan,
    Gan,
    GanZhi,
    PalaceName,
    Shishen,
    Zhi,
    ZHI_CANGGAN_TABLE,
)
from engine.predicates.ganzhi import (
    gan_to_wuxing,
    gan_yinyang,
    is_gan,
    is_zhi,
    zhi_to_wuxing,
    zhi_yinyang,
)
from engine.predicates.wuxing import wuxing_relation


# ============================================================
# 内部工具：地支主气 → 模拟天干（用于"地支取十神"）
# ============================================================

def _zhi_main_gan(z: Zhi) -> Gan:
    """地支主气天干（用于地支取十神时 fallback）。

    例：寅 → 甲 / 子 → 癸 / 戌 → 戊
    """
    cangs = ZHI_CANGGAN_TABLE.get(z, [])
    if not cangs:
        raise ValueError(f"非法地支 {z!r}")
    return cangs[0][0]  # 主气


# ============================================================
# 1. 取宫位
# ============================================================

def get_palace(bazi: Bazi, palace: PalaceName) -> Union[GanZhi, Zhi]:
    """取四柱中的指定宫位。

    "X柱" → 返回 GanZhi；"X支" → 返回 Zhi。
    """
    pillar_map: dict[str, GanZhi] = {
        "年柱": bazi.年柱,
        "月柱": bazi.月柱,
        "日柱": bazi.日柱,
        "时柱": bazi.时柱,
    }
    if palace in pillar_map:
        return pillar_map[palace]
    if palace == "年支":
        return bazi.年柱.zhi
    if palace == "月支":
        return bazi.月柱.zhi
    if palace == "日支":
        return bazi.日柱.zhi
    if palace == "时支":
        return bazi.时柱.zhi
    raise ValueError(f"非法宫位名: {palace!r}")


# ============================================================
# 2. 字是否在指定宫位（含藏干检查）
# ============================================================

def is_in_palace(
    c: Union[Gan, Zhi],
    bazi: Bazi,
    palace: PalaceName,
) -> bool:
    """字 c 是否出现在指定宫位（含藏干）。

    宫位语义：
    - X柱   → 检查该柱的天干、地支以及地支藏干
    - X支   → 检查该支本身 + 该支藏干
    - "any" → 在任一宫位出现（含藏干）
    """
    # any 特殊处理（契约中虽未声明但 04-gate 用到）
    if palace == "any":  # type: ignore[comparison-overlap]
        for p_name in ("年柱", "月柱", "日柱", "时柱"):
            if is_in_palace(c, bazi, p_name):  # type: ignore[arg-type]
                return True
        return False

    target = get_palace(bazi, palace)

    # 获取该宫位的"扫描清单" = 天干 + 地支 + 藏干
    palace_to_zhi_key = {
        "年柱": "年支", "月柱": "月支", "日柱": "日支", "时柱": "时支",
        "年支": "年支", "月支": "月支", "日支": "日支", "时支": "时支",
    }

    if isinstance(target, GanZhi):
        if c == target.gan or c == target.zhi:
            return True
        zhi_key = palace_to_zhi_key.get(palace)  # type: ignore[arg-type]
    else:
        # 单支
        if c == target:
            return True
        zhi_key = palace_to_zhi_key.get(palace)  # type: ignore[arg-type]

    # 藏干检查
    if zhi_key is None:
        return False
    cangs = bazi.藏干.get(zhi_key) or []
    if not cangs:
        # 用标准表 fallback
        zhi_val = target.zhi if isinstance(target, GanZhi) else target
        cangs = [
            Canggan(gan=g, type=t, li_liang=l)
            for (g, t, l) in ZHI_CANGGAN_TABLE.get(zhi_val, [])
        ]
    for cg in cangs:
        if c == cg.gan:
            return True
    return False


# ============================================================
# 3. 十神判定主入口
# ============================================================

def get_shishen(c: Gan, day_master: Gan) -> Shishen:
    """以日干为我，c 字相对我的十神（10 神之一）。

    本派核心规则：
    - 五行关系（生/克/同/我生/我克）划五分
    - 阴阳关系（同/异）再二分
    - 共 10 神

    映射：
        同我 + 同阴阳 → 比肩
        同我 + 异阴阳 → 劫财
        我生 + 同阴阳 → 食神
        我生 + 异阴阳 → 伤官
        我克 + 同阴阳 → 偏财
        我克 + 异阴阳 → 正财
        克我 + 同阴阳 → 七杀
        克我 + 异阴阳 → 正官
        生我 + 同阴阳 → 偏印
        生我 + 异阴阳 → 正印
    """
    if not is_gan(c):
        raise ValueError(f"get_shishen: c 必须是天干, 实为 {c!r}")
    if not is_gan(day_master):
        raise ValueError(f"get_shishen: day_master 必须是天干, 实为 {day_master!r}")

    day_wx = gan_to_wuxing(day_master)
    c_wx = gan_to_wuxing(c)
    rel = wuxing_relation(day_wx, c_wx)

    same_yinyang = gan_yinyang(day_master) == gan_yinyang(c)

    if rel == "同我":
        return "比肩" if same_yinyang else "劫财"
    if rel == "我生":
        return "食神" if same_yinyang else "伤官"
    if rel == "我克":
        return "偏财" if same_yinyang else "正财"
    if rel == "克我":
        return "七杀" if same_yinyang else "正官"
    if rel == "生我":
        return "偏印" if same_yinyang else "正印"
    raise RuntimeError(f"无法识别 {c} ↔ {day_master} 关系")


# ============================================================
# 4-9. 单独十神判定
# ============================================================

def is_zhengyin(c: Gan, day_master: Gan) -> bool:
    """是否为正印（生我且阴阳异）。"""
    return get_shishen(c, day_master) == "正印"


def is_pianyin(c: Gan, day_master: Gan) -> bool:
    """是否为偏印（生我且阴阳同）。"""
    return get_shishen(c, day_master) == "偏印"


def is_zhengcai(c: Gan, day_master: Gan) -> bool:
    """是否为正财（我克且阴阳异）。"""
    return get_shishen(c, day_master) == "正财"


def is_piancai(c: Gan, day_master: Gan) -> bool:
    """是否为偏财（我克且阴阳同）。"""
    return get_shishen(c, day_master) == "偏财"


def is_zhengguan(c: Gan, day_master: Gan) -> bool:
    """是否为正官（克我且阴阳异）。"""
    return get_shishen(c, day_master) == "正官"


def is_qisha(c: Gan, day_master: Gan) -> bool:
    """是否为七杀（克我且阴阳同）。"""
    return get_shishen(c, day_master) == "七杀"


# ============================================================
# 10. 在整个八字中找十神出现的位置（含藏干）
# ============================================================

def find_shishen_in_bazi(
    shishen: Shishen,
    bazi: Bazi,
) -> list[tuple[PalaceName, Union[Gan, Zhi]]]:
    """在整个八字中找 shishen 出现的位置（含藏干）。

    返回：[(宫位名, 字符), ...]
    宫位名规则：
    - 天干透出 → 返回"X柱"（天干所在柱）
    - 地支主气 → 返回"X支"
    - 地支藏干 → 返回"X支"（不区分主/中/余气位置）

    去重：同一支的同一藏干字只返回一次。
    """
    day_master = bazi.day_master
    out: list[tuple[PalaceName, Union[Gan, Zhi]]] = []
    seen: set[tuple[str, str]] = set()  # (palace, char)

    # 1. 扫天干
    for name, gan in bazi.all_gans():
        if name == "日柱" and gan == day_master:
            # 日干本身是"我"，不计入十神搜索
            if shishen not in ("比肩", "劫财"):
                continue
        try:
            ss = get_shishen(gan, day_master)
        except Exception:
            continue
        if ss == shishen:
            key = (name, gan)
            if key not in seen:
                seen.add(key)
                out.append((name, gan))  # type: ignore[arg-type]

    # 2. 扫地支（主气 + 藏干）
    for zhi_key, zhi_val in bazi.all_zhis():
        # zhi_key 形如 "年支" "月支"
        cangs = bazi.藏干.get(zhi_key) or []
        if not cangs:
            cangs = [
                Canggan(gan=g, type=t, li_liang=l)
                for (g, t, l) in ZHI_CANGGAN_TABLE.get(zhi_val, [])
            ]
        for cg in cangs:
            try:
                ss = get_shishen(cg.gan, day_master)
            except Exception:
                continue
            if ss == shishen:
                key = (zhi_key, cg.gan)
                if key not in seen:
                    seen.add(key)
                    out.append((zhi_key, cg.gan))  # type: ignore[arg-type]
    return out


# ============================================================
# smoke test
# ============================================================

def _smoke() -> None:
    from engine.predicates.types import _default_canggan_for

    # C-2026-001 壬日
    bazi = Bazi(
        年柱=GanZhi("庚", "申"),
        月柱=GanZhi("戊", "寅"),
        日柱=GanZhi("壬", "子"),
        时柱=GanZhi("辛", "丑"),
    )
    bazi.藏干 = _default_canggan_for(bazi)
    dm: Gan = "壬"

    # 十神判定（关键）
    # 庚=偏印（金生水，庚阳壬阳同→偏印）
    assert get_shishen("庚", dm) == "偏印"
    # 辛=正印（金生水，辛阴壬阳异→正印）
    assert get_shishen("辛", dm) == "正印"
    # 戊=七杀（土克水，戊阳壬阳同→七杀）
    assert get_shishen("戊", dm) == "七杀"
    # 己=正官（土克水，己阴壬阳异→正官）
    assert get_shishen("己", dm) == "正官"
    # 丙=偏财（水克火则反为我克，但水克火即火，水到火是我克。壬阳丙阳同→偏财）
    assert get_shishen("丙", dm) == "偏财"
    # 丁=正财（壬阳丁阴异→正财）
    assert get_shishen("丁", dm) == "正财"
    # 甲=食神（水生木为我生，壬阳甲阳同→食神）
    assert get_shishen("甲", dm) == "食神"
    # 乙=伤官
    assert get_shishen("乙", dm) == "伤官"
    # 壬=比肩
    assert get_shishen("壬", dm) == "比肩"
    # 癸=劫财
    assert get_shishen("癸", dm) == "劫财"

    # 单独判定
    assert is_zhengyin("辛", dm)
    assert is_pianyin("庚", dm)
    assert is_qisha("戊", dm)
    assert is_zhengguan("己", dm)
    assert is_piancai("丙", dm)
    assert is_zhengcai("丁", dm)
    assert not is_zhengcai("丙", dm)
    assert not is_qisha("己", dm)

    # 取宫位
    assert get_palace(bazi, "年柱") == GanZhi("庚", "申")
    assert get_palace(bazi, "月支") == "寅"

    # is_in_palace
    assert is_in_palace("庚", bazi, "年柱")  # 庚在年干
    assert is_in_palace("申", bazi, "年柱")  # 申在年支
    assert is_in_palace("壬", bazi, "年柱")  # 申中藏壬
    assert is_in_palace("丙", bazi, "月柱")  # 寅藏丙
    assert not is_in_palace("丙", bazi, "时柱")  # 丑无丙
    assert is_in_palace("丙", bazi, "any")  # type: ignore[arg-type]

    # find_shishen_in_bazi
    # 偏财（丙）：寅中含丙 → 月支
    pians = find_shishen_in_bazi("偏财", bazi)
    pian_palaces = {p[0] for p in pians}
    pian_chars = {p[1] for p in pians}
    assert "月支" in pian_palaces, f"偏财应在月支: {pian_palaces}"
    assert "丙" in pian_chars, f"偏财字应含丙: {pian_chars}"

    # 七杀（戊）：戊在月干 + 申、寅藏戊 + 辰...
    qishas = find_shishen_in_bazi("七杀", bazi)
    sha_palaces = {p[0] for p in qishas}
    assert "月柱" in sha_palaces, f"戊七杀应在月柱: {sha_palaces}"

    # 正印（辛）：辛在时干 + 申中？申主气庚=偏印，无辛
    # 但戌、丑中含辛
    zhengyins = find_shishen_in_bazi("正印", bazi)
    yin_palaces = {p[0] for p in zhengyins}
    assert "时柱" in yin_palaces, f"辛正印应在时柱: {yin_palaces}"

    print("[OK] palace smoke：10 函数全过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
