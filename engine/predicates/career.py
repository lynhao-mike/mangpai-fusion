"""职业关系图专用的最小确定性谓词。

这里仅表达可由标准静态表独立验证的离散事实。``is_rooted`` 只判断
天干是否原字出现在地支藏干中；不判断根的强弱、受损、得令或开闭。
"""

from engine.predicates.ganzhi import get_canggan, is_gan, is_zhi
from engine.predicates.types import Gan, Zhi


def is_rooted(gan: Gan, zhi: Zhi) -> bool:
    """天干是否在地支的标准藏干中有原字根。

    本谓词有意采用窄语义：主气、中气、余气均算“存在根”，但同五行的
    另一阴阳天干不算；返回值不携带任何通根强弱结论。
    """

    if not is_gan(gan):
        raise ValueError(f"invalid gan: {gan!r}")
    if not is_zhi(zhi):
        raise ValueError(f"invalid zhi: {zhi!r}")
    return any(item.gan == gan for item in get_canggan(zhi))


__all__ = ("is_rooted",)
