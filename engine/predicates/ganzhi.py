"""engine/predicates/ganzhi.py · v1.2 干支基础谓词（11 函数）

实现 02-predicate-library.md § 4.1 全部 11 个函数。
所有函数都是纯函数，零副作用。

作者：Track-A
"""
from __future__ import annotations

from typing import Optional

from engine.predicates.types import (
    GAN_LIST,
    GAN_TO_WUXING,
    GAN_YINYANG,
    ZHI_CANGGAN_TABLE,
    ZHI_LIST,
    ZHI_TO_WUXING,
    ZHI_YINYANG,
    Canggan,
    Gan,
    GanZhi,
    Wuxing,
    YinYang,
    Zhi,
)


# ============================================================
# 1-2. 是否为天干 / 地支
# ============================================================

def is_gan(c: str) -> bool:
    """是否为合法天干。"""
    return isinstance(c, str) and c in GAN_LIST


def is_zhi(c: str) -> bool:
    """是否为合法地支。"""
    return isinstance(c, str) and c in ZHI_LIST


# ============================================================
# 3-4. 干支序号
# ============================================================

def gan_index(g: Gan) -> int:
    """甲=0, 乙=1, ..., 癸=9。非法干 raise ValueError。"""
    if g not in GAN_LIST:
        raise ValueError(f"非法天干: {g!r}")
    return GAN_LIST.index(g)


def zhi_index(z: Zhi) -> int:
    """子=0, 丑=1, ..., 亥=11。"""
    if z not in ZHI_LIST:
        raise ValueError(f"非法地支: {z!r}")
    return ZHI_LIST.index(z)


# ============================================================
# 5-6. 干支 → 五行
# ============================================================

def gan_to_wuxing(g: Gan) -> Wuxing:
    """甲乙→木 / 丙丁→火 / 戊己→土 / 庚辛→金 / 壬癸→水"""
    if g not in GAN_TO_WUXING:
        raise ValueError(f"非法天干: {g!r}")
    return GAN_TO_WUXING[g]


def zhi_to_wuxing(z: Zhi) -> Wuxing:
    """寅卯→木 / 巳午→火 / 申酉→金 / 亥子→水 / 辰戌丑未→土"""
    if z not in ZHI_TO_WUXING:
        raise ValueError(f"非法地支: {z!r}")
    return ZHI_TO_WUXING[z]


# ============================================================
# 7-8. 阴阳
# ============================================================

def gan_yinyang(g: Gan) -> YinYang:
    """甲丙戊庚壬→阳 / 乙丁己辛癸→阴"""
    if g not in GAN_YINYANG:
        raise ValueError(f"非法天干: {g!r}")
    return GAN_YINYANG[g]


def zhi_yinyang(z: Zhi) -> YinYang:
    """子寅辰午申戌→阳 / 丑卯巳未酉亥→阴"""
    if z not in ZHI_YINYANG:
        raise ValueError(f"非法地支: {z!r}")
    return ZHI_YINYANG[z]


# ============================================================
# 9. 地支藏干
# ============================================================

def get_canggan(z: Zhi) -> list[Canggan]:
    """返回地支标准藏干列表（主气1.0 / 中气0.3 / 余气0.2）。

    返回新对象列表（每次调用产生独立 Canggan，避免污染）。
    """
    if z not in ZHI_CANGGAN_TABLE:
        raise ValueError(f"非法地支: {z!r}")
    return [
        Canggan(gan=g, type=t, li_liang=l)
        for (g, t, l) in ZHI_CANGGAN_TABLE[z]
    ]


# ============================================================
# 10-11. 60 甲子序号 / 合法性
# ============================================================

def jiazi_index(gz: GanZhi) -> int:
    """60 甲子序号 0-59，'甲子'=0, '癸亥'=59。

    非法（阴阳不配）的组合 raise ValueError。
    """
    if not is_valid_jiazi(gz):
        raise ValueError(f"非 60 甲子: {gz}")
    g_idx = GAN_LIST.index(gz.gan)
    z_idx = ZHI_LIST.index(gz.zhi)
    # n % 10 == g_idx 且 n % 12 == z_idx 的唯一 n ∈ [0, 60)
    for n in range(60):
        if n % 10 == g_idx and n % 12 == z_idx:
            return n
    # 不应到达
    raise ValueError(f"非 60 甲子: {gz}")


def is_valid_jiazi(gz: GanZhi) -> bool:
    """是否合法 60 甲子组合。

    规则：天干合法 + 地支合法 + 阴阳同性。
    """
    if not is_gan(gz.gan) or not is_zhi(gz.zhi):
        return False
    return GAN_YINYANG[gz.gan] == ZHI_YINYANG[gz.zhi]


# ============================================================
# smoke test
# ============================================================

def _smoke() -> None:
    # 基础合法性
    assert is_gan("甲") and not is_gan("子") and not is_gan("X")
    assert is_zhi("子") and not is_zhi("甲")

    assert gan_index("甲") == 0 and gan_index("癸") == 9
    assert zhi_index("子") == 0 and zhi_index("亥") == 11

    assert gan_to_wuxing("甲") == "木"
    assert gan_to_wuxing("壬") == "水"
    assert zhi_to_wuxing("寅") == "木"
    assert zhi_to_wuxing("丑") == "土"

    assert gan_yinyang("甲") == "阳" and gan_yinyang("乙") == "阴"
    assert zhi_yinyang("子") == "阳" and zhi_yinyang("丑") == "阴"

    # 藏干
    cangs = get_canggan("寅")
    assert len(cangs) == 3
    assert cangs[0].gan == "甲" and cangs[0].type == "主气"
    assert cangs[1].gan == "丙" and cangs[1].type == "中气"

    # 60 甲子
    assert is_valid_jiazi(GanZhi("甲", "子"))
    assert not is_valid_jiazi(GanZhi("甲", "丑"))  # 阳干配阴支
    assert jiazi_index(GanZhi("甲", "子")) == 0
    assert jiazi_index(GanZhi("癸", "亥")) == 59
    assert jiazi_index(GanZhi("壬", "子")) == 48
    assert jiazi_index(GanZhi("辛", "丑")) == 37

    # 异常路径
    try:
        jiazi_index(GanZhi("甲", "丑"))  # type: ignore[arg-type]
        raise AssertionError("应拒绝阴阳不配")
    except ValueError:
        pass
    try:
        gan_index("X")  # type: ignore[arg-type]
        raise AssertionError
    except ValueError:
        pass

    print("[OK] ganzhi smoke：11 函数全过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
