"""engine/predicates/tou_cang.py · v1.2 透藏关系谓词（5 函数）

实现 02-predicate-library.md § 4.6 全部 5 个函数。

任派核心概念：藏干透出（地支藏干透到天干）= 6 触发之一。
段派也用：贼神捕神判定时常需透藏关系。

作者：Track-C
"""
from __future__ import annotations

from typing import Optional

from engine.predicates.types import (
    Bazi,
    Canggan,
    Gan,
    PalaceName,
    Zhi,
    GAN_LIST,
    ZHI_CANGGAN_TABLE,
    ZHI_LIST,
)


# ============================================================
# 内部工具
# ============================================================

# 4 个地支位（按柱顺序）
_ZHI_KEYS: tuple[str, ...] = ("年支", "月支", "日支", "时支")
# 与"X支"对应的"X柱"
_ZHI_TO_PILLAR: dict[str, str] = {
    "年支": "年柱", "月支": "月柱", "日支": "日柱", "时支": "时柱",
}


def _get_canggans_at(bazi: Bazi, zhi_key: str) -> list[Canggan]:
    """取 bazi.藏干[zhi_key]；若空，用 ZHI_CANGGAN_TABLE 标准表 fallback。"""
    cangs = bazi.藏干.get(zhi_key) if bazi.藏干 else None
    if cangs:
        return cangs
    # fallback
    pillar_name = _ZHI_TO_PILLAR[zhi_key]
    pillar = getattr(bazi, pillar_name)
    zhi = pillar.zhi
    return [
        Canggan(gan=g, type=t, li_liang=l)
        for (g, t, l) in ZHI_CANGGAN_TABLE.get(zhi, [])
    ]


# ============================================================
# 1. is_tou
# ============================================================

def is_tou(c: Gan, bazi: Bazi) -> bool:
    """天干 c 是否透出在四柱天干上（任一柱）。

    >>> 庚申戊寅壬子辛丑 中，庚 / 戊 / 壬 / 辛 透；甲 / 乙 / 丙 不透。
    """
    if c not in GAN_LIST:
        raise ValueError(f"非法天干: {c!r}")
    for _, gan in bazi.all_gans():
        if gan == c:
            return True
    return False


# ============================================================
# 2. is_canggan
# ============================================================

def is_canggan(c: Gan, bazi: Bazi) -> list[PalaceName]:
    """天干 c 是否藏在地支中，返回藏在哪些支位（含余气）。

    >>> 寅藏甲丙戊 → is_canggan('丙', bazi) == ['月支']（若月支为寅）
    """
    if c not in GAN_LIST:
        raise ValueError(f"非法天干: {c!r}")
    out: list[PalaceName] = []
    for zk in _ZHI_KEYS:
        for cg in _get_canggans_at(bazi, zk):
            if cg.gan == c:
                out.append(zk)  # type: ignore[arg-type]
                break  # 同一支只记一次
    return out


# ============================================================
# 3. tou_chu
# ============================================================

def tou_chu(c: Gan, bazi: Bazi) -> Optional[tuple[PalaceName, PalaceName]]:
    """c 是否"透出"——藏在某支且对应天干在四柱上出现。

    返回 (藏的支位, 透出的天干位置)，无则 None。

    任派核心：藏干透出 = 6 触发之一。
    段派也用：体用判定中"藏干透出能制约的字"是关键。

    优先级：返回最近的一对（先扫天干透出位 → 再扫藏干位）。
    """
    if c not in GAN_LIST:
        raise ValueError(f"非法天干: {c!r}")

    # 先扫天干位（确认有透出）
    tou_palace: Optional[PalaceName] = None
    pillar_to_palace: dict[str, str] = {
        "年柱": "年柱", "月柱": "月柱", "日柱": "日柱", "时柱": "时柱",
    }
    for name, gan in bazi.all_gans():
        if gan == c:
            tou_palace = pillar_to_palace[name]  # type: ignore[assignment]
            break
    if tou_palace is None:
        return None  # 不透 → 无所谓"透出"

    # 找藏支
    cang_palace: Optional[PalaceName] = None
    for zk in _ZHI_KEYS:
        for cg in _get_canggans_at(bazi, zk):
            if cg.gan == c:
                cang_palace = zk  # type: ignore[assignment]
                break
        if cang_palace:
            break

    if cang_palace is None:
        return None  # 透但不藏（外来字）→ 不算"透出"
    return (cang_palace, tou_palace)


# ============================================================
# 4. get_all_tou_chars
# ============================================================

def get_all_tou_chars(bazi: Bazi) -> list[Gan]:
    """所有"透出"的天干清单（去重）。

    透出 = 既藏在某支 + 又出现在某天干。
    """
    out: list[Gan] = []
    for g in GAN_LIST:
        if tou_chu(g, bazi) is not None:
            out.append(g)
    return out


# ============================================================
# 5. is_tou_at
# ============================================================

def is_tou_at(c: Gan, palace: PalaceName, bazi: Bazi) -> bool:
    """c 是否透出在指定柱位的天干上。

    palace 必须是"X柱"形式（含天干）。如传 "X支" 则视为该柱。
    """
    if c not in GAN_LIST:
        raise ValueError(f"非法天干: {c!r}")

    palace_to_pillar: dict[str, str] = {
        "年柱": "年柱", "月柱": "月柱", "日柱": "日柱", "时柱": "时柱",
        "年支": "年柱", "月支": "月柱", "日支": "日柱", "时支": "时柱",
    }
    pillar_attr = palace_to_pillar.get(palace)  # type: ignore[arg-type]
    if pillar_attr is None:
        raise ValueError(f"非法宫位: {palace!r}")

    pillar = getattr(bazi, pillar_attr)
    return pillar.gan == c


# ============================================================
# smoke test
# ============================================================

def _smoke() -> None:
    from engine.predicates.types import GanZhi, _default_canggan_for

    # C-2026-001：庚申戊寅壬子辛丑
    bazi = Bazi(
        年柱=GanZhi("庚", "申"),
        月柱=GanZhi("戊", "寅"),
        日柱=GanZhi("壬", "子"),
        时柱=GanZhi("辛", "丑"),
    )
    bazi.藏干 = _default_canggan_for(bazi)

    # is_tou: 庚 / 戊 / 壬 / 辛 透
    assert is_tou("庚", bazi)
    assert is_tou("戊", bazi)
    assert is_tou("壬", bazi)
    assert is_tou("辛", bazi)
    assert not is_tou("甲", bazi)
    assert not is_tou("乙", bazi)
    assert not is_tou("丙", bazi)
    assert not is_tou("丁", bazi)

    # is_canggan: 寅藏甲丙戊 → 丙在月支
    cs = is_canggan("丙", bazi)
    assert cs == ["月支"], f"丙仅藏月支(寅): {cs}"
    # 辛在年支(申: 庚壬戊)? 不藏 / 时支(丑: 己癸辛)? 藏 / 戌? 戌主气戊,中辛余丁 → 时支
    cs = is_canggan("辛", bazi)
    assert "时支" in cs
    # 戊：申(庚壬戊余气) + 寅(甲丙戊余气) → 年支 月支
    cs = is_canggan("戊", bazi)
    assert "年支" in cs and "月支" in cs

    # tou_chu: 庚透在年柱 + 藏在年支(申主气) → ("年支", "年柱")
    tc = tou_chu("庚", bazi)
    assert tc == ("年支", "年柱"), f"庚 tou_chu: {tc}"
    # 戊透在月柱 + 藏在年支(申余气)/月支(寅余气) → 取第一个 ("年支", "月柱")
    tc = tou_chu("戊", bazi)
    assert tc is not None and tc[1] == "月柱", f"戊 tou_chu: {tc}"
    # 辛透在时柱 + 藏在时支 → ("时支", "时柱")
    tc = tou_chu("辛", bazi)
    assert tc == ("时支", "时柱"), f"辛 tou_chu: {tc}"
    # 壬透在日柱 + 藏在年支(申中气) → ("年支", "日柱")
    tc = tou_chu("壬", bazi)
    assert tc is not None and tc[1] == "日柱", f"壬 tou_chu: {tc}"
    # 丙不透 → None
    assert tou_chu("丙", bazi) is None
    # 甲不透 → None
    assert tou_chu("甲", bazi) is None

    # get_all_tou_chars: 庚 / 戊 / 壬 / 辛 都既透又藏
    tous = get_all_tou_chars(bazi)
    assert set(tous) == {"庚", "戊", "壬", "辛"}, f"tous: {tous}"

    # is_tou_at
    assert is_tou_at("庚", "年柱", bazi)
    assert is_tou_at("庚", "年支", bazi)  # 别名 → 年柱
    assert not is_tou_at("庚", "月柱", bazi)
    assert is_tou_at("辛", "时柱", bazi)
    assert is_tou_at("壬", "日柱", bazi)

    # 异常路径
    try:
        is_tou("X", bazi)  # type: ignore[arg-type]
        raise AssertionError
    except ValueError:
        pass

    print("[OK] tou_cang smoke：5 函数全过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
