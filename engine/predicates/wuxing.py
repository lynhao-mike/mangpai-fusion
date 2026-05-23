"""engine/predicates/wuxing.py · v1.2 五行关系谓词（8 函数）

实现 02-predicate-library.md § 4.2 全部 8 个函数。

反生 / 反克 是段派的特殊概念（"金多水浊 / 水多木漂" 等）：
- 当 b 五行力量 > 阈值且 a 弱时，a 生 b 反而被埋。
- 阈值默认 0.45（即占总势 45% 以上 = 极旺）。

作者：Track-A
"""
from __future__ import annotations

from typing import Literal, Optional

from engine.predicates.types import (
    GAN_TO_WUXING,
    KE_MAP,
    SHENG_ORDER,
    WUXING_LIST,
    Gan,
    Wuxing,
)
from engine.predicates.ganzhi import gan_to_wuxing


# ============================================================
# 1-3. 基础生克同
# ============================================================

def wuxing_sheng(a: Wuxing, b: Wuxing) -> bool:
    """a 是否生 b（木→火 / 火→土 / 土→金 / 金→水 / 水→木）。"""
    if a not in SHENG_ORDER or b not in SHENG_ORDER:
        raise ValueError(f"非法五行: {a!r}, {b!r}")
    idx_a = SHENG_ORDER.index(a)
    return SHENG_ORDER[(idx_a + 1) % 5] == b


def wuxing_ke(a: Wuxing, b: Wuxing) -> bool:
    """a 是否克 b（木→土 / 土→水 / 水→火 / 火→金 / 金→木）。"""
    if a not in KE_MAP or b not in KE_MAP:
        raise ValueError(f"非法五行: {a!r}, {b!r}")
    return KE_MAP[a] == b


def wuxing_same(a: Wuxing, b: Wuxing) -> bool:
    """同行（比劫关系）。"""
    if a not in WUXING_LIST or b not in WUXING_LIST:
        raise ValueError(f"非法五行: {a!r}, {b!r}")
    return a == b


# ============================================================
# 4. 关系（以 a 为参照看 b）
# ============================================================

def wuxing_relation(
    a: Wuxing, b: Wuxing
) -> Literal["生我", "我生", "克我", "我克", "同我"]:
    """以 a 为参照，b 是何种关系。

    生我 = b 生 a / 我生 = a 生 b / 克我 = b 克 a / 我克 = a 克 b / 同我 = a==b
    """
    if a == b:
        return "同我"
    if wuxing_sheng(b, a):
        return "生我"
    if wuxing_sheng(a, b):
        return "我生"
    if wuxing_ke(b, a):
        return "克我"
    if wuxing_ke(a, b):
        return "我克"
    # 不应到达
    raise RuntimeError(f"无法识别 {a} ↔ {b} 关系")


# ============================================================
# 5-6. 天干生克
# ============================================================

def gan_sheng_gan(a: Gan, b: Gan) -> bool:
    """天干生天干（基于五行）。"""
    return wuxing_sheng(gan_to_wuxing(a), gan_to_wuxing(b))


def gan_ke_gan(a: Gan, b: Gan) -> bool:
    """天干克天干。"""
    return wuxing_ke(gan_to_wuxing(a), gan_to_wuxing(b))


# ============================================================
# 7-8. 反生 / 反克（段派核心：势力对比）
# ============================================================

def fan_sheng(
    a: Wuxing,
    b: Wuxing,
    *,
    strength_b: Optional[float] = None,
    strength_a: Optional[float] = None,
    overflow_threshold: float = 0.45,
) -> bool:
    """反生：当 b 过旺且 a 弱时，a 生 b 反被 b 埋。

    五种反生：金多水浊 / 水多木漂 / 木多火塞 / 火多土焦 / 土多金埋。

    判定逻辑：
    - 必须 a 生 b（即正向五行关系成立）
    - strength_b > overflow_threshold（默认 45%）且 strength_a < 0.20
    - 若不传力量参数，则只看五行类型（保守返回 False，等于"无量化数据=不判定"）

    注意：本函数不"产生"反生事实；只是把段派的反生模式"识别"出来。
    """
    if not wuxing_sheng(a, b):
        return False
    if strength_b is None or strength_a is None:
        return False
    return strength_b > overflow_threshold and strength_a < 0.20


def fan_ke(
    a: Wuxing,
    b: Wuxing,
    *,
    strength_b: Optional[float] = None,
    strength_a: Optional[float] = None,
    overflow_threshold: float = 0.45,
) -> bool:
    """反克：当 b 过旺时，反过来欺负本应克它的 a。

    五种反克：木旺金缺 / 火旺水竭 / 土旺木折 / 金旺火灭 / 水旺土流。

    判定逻辑：
    - 必须 a 克 b（正向克关系成立）
    - strength_b > overflow_threshold 且 strength_a < 0.20
    """
    if not wuxing_ke(a, b):
        return False
    if strength_b is None or strength_a is None:
        return False
    return strength_b > overflow_threshold and strength_a < 0.20


# ============================================================
# smoke test
# ============================================================

def _smoke() -> None:
    # 基础生克
    assert wuxing_sheng("木", "火")
    assert wuxing_sheng("水", "木")
    assert not wuxing_sheng("火", "木")  # 反向
    assert wuxing_ke("木", "土")
    assert wuxing_ke("金", "木")
    assert not wuxing_ke("木", "金")  # 反向

    # 同行
    assert wuxing_same("木", "木") and not wuxing_same("木", "火")

    # 关系
    assert wuxing_relation("木", "木") == "同我"
    assert wuxing_relation("木", "火") == "我生"
    assert wuxing_relation("木", "水") == "生我"
    assert wuxing_relation("木", "土") == "我克"
    assert wuxing_relation("木", "金") == "克我"

    # 天干生克
    assert gan_sheng_gan("甲", "丙")  # 木→火
    assert gan_ke_gan("甲", "戊")    # 木→土
    assert not gan_sheng_gan("丙", "甲")

    # 反生反克：默认（不传力量）= False
    assert not fan_sheng("水", "木")
    # 传力量：木势 50%，水势 5% → 水生木反埋
    assert fan_sheng("水", "木", strength_b=0.50, strength_a=0.05)
    assert not fan_sheng("水", "木", strength_b=0.50, strength_a=0.30)

    assert not fan_ke("木", "土")  # 默认无量化
    assert fan_ke("木", "土", strength_b=0.55, strength_a=0.10)

    print("[OK] wuxing smoke：8 函数全过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
