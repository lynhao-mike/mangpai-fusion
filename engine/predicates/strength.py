"""engine/predicates/strength.py · v1.2 旺衰判定谓词（6 函数）

实现 02-predicate-library.md § 4.7 全部 6 个函数。

段派理念（M1 §17）：旺衰只是工具，不是目的。但量化"得令/得地/得势"
仍然是势/党/做功判定的基础数据。

calc_wuxing_strength：
- 输入 Bazi
- 计算 5 行总势力，返回 dict[Wuxing, float]，总和约为 1.0
- 加权：天干 1.0 / 月令支主气 1.5 / 其他支主气 1.0 / 中气 0.3 / 余气 0.2

作者：Track-A
"""
from __future__ import annotations

from typing import Optional

from engine.predicates.types import (
    CHANGSHENG_TABLE,
    GAN_LIST,
    WUXING_LIST,
    Bazi,
    ChangshengStatus,
    Gan,
    GanZhi,
    Wuxing,
    Zhi,
    ZHI_CANGGAN_TABLE,
)
from engine.predicates.ganzhi import gan_to_wuxing, zhi_to_wuxing
from engine.predicates.wuxing import wuxing_same


# 月令对天干的"得令"加权
_DELING_STATES: set[ChangshengStatus] = {"长生", "临官", "帝旺"}
# 旺/相 = 得令；衰/病/死/绝/胎/养 = 失令
# 段派表："冠带" 也算"得地" 但不算"得令"

_DEDI_STATES: set[ChangshengStatus] = {"长生", "冠带", "临官", "帝旺"}


# ============================================================
# 1. 长生状态查询
# ============================================================

def get_changsheng(g: Gan, z: Zhi) -> ChangshengStatus:
    """天干 g 在地支 z 的 12 长生状态。"""
    if g not in CHANGSHENG_TABLE:
        raise ValueError(f"非法天干: {g!r}")
    if z not in CHANGSHENG_TABLE[g]:
        raise ValueError(f"非法地支: {z!r}")
    return CHANGSHENG_TABLE[g][z]


# ============================================================
# 2. 得令
# ============================================================

def is_dejin(g: Gan, yueling_zhi: Zhi) -> bool:
    """天干是否得令（在月令上为长生/临官/帝旺）。

    段派"得令"严格定义 = 月令支主气与天干同行 OR 月令支为长生/临官/帝旺。
    """
    cs = get_changsheng(g, yueling_zhi)
    if cs in _DELING_STATES:
        return True
    # 备用：月令支五行 = 天干五行 → 同行也算得令
    if zhi_to_wuxing(yueling_zhi) == gan_to_wuxing(g):
        return True
    return False


# ============================================================
# 3. 得地
# ============================================================

def is_dishi(g: Gan, bazi: Bazi) -> bool:
    """天干是否得地（在四支中至少一支为长生/冠带/临官/帝旺）。

    注：契约文档拼写为 ``is_dishi``，含义为"得地"。
    """
    for _, zhi in bazi.all_zhis():
        if get_changsheng(g, zhi) in _DEDI_STATES:
            return True
    return False


# ============================================================
# 4. 得旺（得势）
# ============================================================

def is_dewang(g: Gan, bazi: Bazi) -> bool:
    """天干是否得势（在天干上有比劫帮扶）。

    比劫定义：与日干同五行的天干。
    """
    target_wx = gan_to_wuxing(g)
    count_same = 0
    for name, gan in bazi.all_gans():
        if gan == g and name == "日柱":
            # 日柱本干自身不计入"得势"
            continue
        if gan_to_wuxing(gan) == target_wx and gan != g:
            # 严格：同五行不同干（比劫互见）
            count_same += 1
        elif gan_to_wuxing(gan) == target_wx and gan == g:
            # 透干同字（自身比肩）
            count_same += 1
    return count_same >= 1


# ============================================================
# 5. 五行势力计算
# ============================================================

def calc_wuxing_strength(
    bazi: Bazi,
    *,
    yueling_weight: float = 1.5,
    gan_weight: float = 1.0,
    zhi_zhuqi_weight: float = 1.0,
    zhi_zhongqi_weight: float = 0.3,
    zhi_yuqi_weight: float = 0.2,
) -> dict[Wuxing, float]:
    """计算五行在原局的总力量。

    加权规则：
    - 天干（4 干，每干 1.0）→ 天干贡献
    - 月令支主气：1.5 倍权重（段派"月令为提纲"）
    - 其他支主气：1.0 倍
    - 中气：0.3
    - 余气：0.2

    返回：归一化后 dict[Wuxing, float]，总和 = 1.0。
    """
    raw: dict[Wuxing, float] = {wx: 0.0 for wx in WUXING_LIST}

    # 天干
    for _, gan in bazi.all_gans():
        wx = gan_to_wuxing(gan)
        raw[wx] += gan_weight

    # 地支：先看月令位
    yueling = bazi.月令
    pillar_zhi_pairs = [
        ("年支", bazi.年柱.zhi),
        ("月支", bazi.月柱.zhi),
        ("日支", bazi.日柱.zhi),
        ("时支", bazi.时柱.zhi),
    ]
    for key, zhi in pillar_zhi_pairs:
        # 加载藏干（优先用 bazi.藏干 中的，缺则用标准表）
        if bazi.藏干 and key in bazi.藏干 and bazi.藏干[key]:
            cangs = [(c.gan, c.type, c.li_liang) for c in bazi.藏干[key]]
        else:
            cangs = [(g, t, l) for (g, t, l) in ZHI_CANGGAN_TABLE.get(zhi, [])]
        is_yueling = (key == "月支")
        for (gan, typ, li) in cangs:
            wx = gan_to_wuxing(gan)
            base_w = li
            if typ == "主气":
                base_w *= zhi_zhuqi_weight
            elif typ == "中气":
                base_w *= zhi_zhongqi_weight
            elif typ == "余气":
                base_w *= zhi_yuqi_weight
            if is_yueling:
                base_w *= yueling_weight
            raw[wx] += base_w

    # 归一化
    total = sum(raw.values())
    if total <= 0:
        return raw
    return {wx: v / total for wx, v in raw.items()}


# ============================================================
# 6. 单干势力
# ============================================================

def calc_gan_strength(g: Gan, bazi: Bazi) -> float:
    """单个天干在原局的力量（0.0-1.5）。

    维度：
    - 得令 +0.40
    - 得地 +0.30
    - 得势（天干透同行）+0.20 / 干
    - 透干（自己出现于天干）+0.20

    超过 1.0 表示极旺。
    """
    score = 0.0

    if is_dejin(g, bazi.月令):
        score += 0.40

    if is_dishi(g, bazi):
        score += 0.30

    target_wx = gan_to_wuxing(g)
    n_same_other_gan = 0
    n_self_tou = 0
    for name, gan in bazi.all_gans():
        if gan == g:
            n_self_tou += 1
        elif gan_to_wuxing(gan) == target_wx:
            n_same_other_gan += 1

    score += 0.20 * min(n_same_other_gan, 2)  # 上限 0.40
    score += 0.20 * min(n_self_tou, 2)        # 上限 0.40

    # 不超过 1.5
    return min(score, 1.5)


# ============================================================
# smoke test
# ============================================================

def _smoke() -> None:
    # 长生表
    assert get_changsheng("壬", "子") == "帝旺"
    assert get_changsheng("壬", "申") == "长生"
    assert get_changsheng("甲", "亥") == "长生"
    assert get_changsheng("乙", "午") == "长生"

    # C-2026-001: 庚申戊寅壬子辛丑（壬日）
    bazi = Bazi(
        年柱=GanZhi("庚", "申"),
        月柱=GanZhi("戊", "寅"),
        日柱=GanZhi("壬", "子"),
        时柱=GanZhi("辛", "丑"),
    )
    bazi.藏干 = {
        "年支": [],  # 让 calc_wuxing_strength 自动用标准表
        "月支": [],
        "日支": [],
        "时支": [],
    }

    # 壬在寅月 → "病" → 不得令；但壬日支子（帝旺）→ 得地
    assert not is_dejin("壬", bazi.月令)
    assert is_dishi("壬", bazi)

    # 壬日干，没有第二个壬，但有比劫癸（藏在子/丑中），故 is_dewang 看天干 → 不得势
    # 实际只看天干透出的比劫；本局天干无水
    assert not is_dewang("壬", bazi)

    # 五行势力计算
    s = calc_wuxing_strength(bazi)
    total = sum(s.values())
    assert abs(total - 1.0) < 1e-6, f"归一化失败: {total}"
    # 月令寅木 + 时支丑（土）→ 木势 + 土势比较高
    print(f"[debug] C-2026-001 五行势: {s}")

    # 单干强度
    ren_strength = calc_gan_strength("壬", bazi)
    print(f"[debug] 壬干强度: {ren_strength:.3f}")
    assert 0 <= ren_strength <= 1.5

    print("[OK] strength smoke：6 函数全过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
