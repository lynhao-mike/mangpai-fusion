"""engine/predicates/cycles.py · v1.2 大运流年谓词（9 函数）

实现 02-predicate-library.md § 4.5 全部 9 个函数。

所有判定都是纯函数：相同输入 → 相同输出，无副作用。

公元 4 年 = 甲子年（与现代万年历一致；1984=甲子是 1984-4=1980 整 60 倍数验证）。

作者：Track-C
"""
from __future__ import annotations

from typing import Optional, Union

from engine.predicates.types import (
    Bazi,
    Dayun,
    DayunStep,
    Gan,
    GanZhi,
    PalaceName,
    Wuxing,
    Zhi,
    GAN_LIST,
    ZHI_LIST,
)
from engine.predicates.relations import (
    zhi_chong,
    zhi_chuan,
    zhi_liuhe,
    zhi_sanhe,
    zhi_xing,
    gan_he,
)


# ============================================================
# 1. get_dayun_at_age
# ============================================================

def get_dayun_at_age(dayun: Dayun, age: int) -> DayunStep:
    """指定虚岁所在大运步。

    起运前（age < dayun.起运岁）抛 ValueError。
    末步之后用最后一步（"超过排布范围则按最后一运处理"，避免下游崩）。
    """
    if not dayun.排布:
        raise ValueError("Dayun.排布 为空")
    if age < int(dayun.起运岁):
        raise ValueError(
            f"年龄 {age} < 起运岁 {dayun.起运岁}，尚未交运"
        )
    for step in dayun.排布:
        if step.起岁 <= age <= step.止岁:
            return step
    # 超过最后一步 → 用最后一步
    return dayun.排布[-1]


# ============================================================
# 2. get_dayun_at_year
# ============================================================

def get_dayun_at_year(
    dayun: Dayun, birth_year: int, target_year: int
) -> DayunStep:
    """指定公历年所在大运步。

    优先按 DayunStep.起讫年 区间 [start, end) 匹配（这是 fixtures/cases.py
    构造时的真值）。若区间不足则退到 age 法 fallback。
    """
    if not dayun.排布:
        raise ValueError("Dayun.排布 为空")

    # 优先：起讫年区间
    for step in dayun.排布:
        if step.起讫年[0] <= target_year < step.起讫年[1]:
            return step

    # Fallback：用年龄法
    age = target_year - birth_year
    if age < int(dayun.起运岁):
        # 起运前
        raise ValueError(
            f"目标年 {target_year} 早于起运年 "
            f"({birth_year}+{dayun.起运岁:.1f}) → 尚未交运"
        )
    if target_year >= dayun.排布[-1].起讫年[1]:
        return dayun.排布[-1]
    return get_dayun_at_age(dayun, age)


# ============================================================
# 3. liunian_ganzhi
# ============================================================

def liunian_ganzhi(year: int) -> GanZhi:
    """公历年份的流年干支。

    公元 4 年 = 甲子年。年份 → 干支 = 60 甲子循环。

    验证锚点（与万年历一致）：
        1980 = 庚申     1984 = 甲子     2005 = 乙酉
        2013 = 癸巳     2020 = 庚子     2024 = 甲辰
    """
    offset = (year - 4) % 60
    if offset < 0:
        offset += 60
    gan_idx = offset % 10
    zhi_idx = offset % 12
    return GanZhi(gan=GAN_LIST[gan_idx], zhi=ZHI_LIST[zhi_idx])


# ============================================================
# 4. is_dayun_zhi_chong_bazi
# ============================================================

def is_dayun_zhi_chong_bazi(
    dayun_step: DayunStep, bazi: Bazi
) -> list[PalaceName]:
    """大运地支冲八字哪些柱地支。

    返回被冲的支位名列表（"年支" / "月支" / "日支" / "时支"）。
    """
    out: list[PalaceName] = []
    dy_zhi = dayun_step.干支.zhi
    for name, zhi in bazi.all_zhis():
        if zhi_chong(dy_zhi, zhi):
            out.append(name)  # type: ignore[arg-type]
    return out


# ============================================================
# 5. is_liunian_with_dayun_he
# ============================================================

def is_liunian_with_dayun_he(
    year: int, dayun_step: DayunStep
) -> Optional[Wuxing]:
    """流年与大运是否构成合（六合 / 三合半合 / 天干五合化神）。

    判定优先级：
        1. 地支六合（化神 = liuhe 化神）
        2. 地支三合（与大运地支 + 任一中神相邻 → 半合）
        3. 天干五合（化神）
    """
    ln = liunian_ganzhi(year)

    # 1) 地支六合
    h = zhi_liuhe(ln.zhi, dayun_step.干支.zhi)
    if h is not None:
        return h

    # 2) 三合半合（必须含三合中神）
    h2 = zhi_sanhe([ln.zhi, dayun_step.干支.zhi])
    if h2 is not None:
        return h2

    # 3) 天干五合（取化神，不论是否化成）
    gan_he_result = gan_he(ln.gan, dayun_step.干支.gan)
    if gan_he_result is not None:
        return gan_he_result[0]  # 化神

    return None


# ============================================================
# 6. is_liunian_with_bazi_he
# ============================================================

def is_liunian_with_bazi_he(
    year: int, bazi: Bazi
) -> list[tuple[PalaceName, Wuxing]]:
    """流年与八字哪些柱合，返回 [(柱名, 化神), ...]。

    扫描方式：
        - 流年地支 vs 4 个地支柱 → 六合 / 半三合
        - 流年天干 vs 4 个天干柱 → 五合（取化神）
        返回所有命中。
    """
    ln = liunian_ganzhi(year)
    out: list[tuple[PalaceName, Wuxing]] = []

    # 地支侧
    for name, zhi in bazi.all_zhis():
        h = zhi_liuhe(ln.zhi, zhi)
        if h is not None:
            out.append((name, h))  # type: ignore[arg-type]
            continue
        h2 = zhi_sanhe([ln.zhi, zhi])
        if h2 is not None:
            out.append((name, h2))  # type: ignore[arg-type]

    # 天干侧
    pillar_palace = {
        "年柱": "年柱", "月柱": "月柱",
        "日柱": "日柱", "时柱": "时柱",
    }
    for name, gan in bazi.all_gans():
        gh = gan_he(ln.gan, gan)
        if gh is not None:
            palace_name: PalaceName = pillar_palace[name]  # type: ignore[assignment]
            out.append((palace_name, gh[0]))

    return out


# ============================================================
# 7. is_liunian_chong_bazi
# ============================================================

def is_liunian_chong_bazi(year: int, bazi: Bazi) -> list[PalaceName]:
    """流年地支冲八字哪些柱地支。"""
    ln = liunian_ganzhi(year)
    out: list[PalaceName] = []
    for name, zhi in bazi.all_zhis():
        if zhi_chong(ln.zhi, zhi):
            out.append(name)  # type: ignore[arg-type]
    return out


# ============================================================
# 8. is_liunian_yingdong_bazi_zi
# ============================================================

def is_liunian_yingdong_bazi_zi(
    year: int, target_char: Union[Gan, Zhi], bazi: Bazi
) -> bool:
    """流年是否引动八字中的 target_char。

    引动 = 流年的天干或地支与 target_char 形成以下任一关系：
        - 同字（"本字到"）
        - 天干合 / 天干同字
        - 地支六合 / 三合半合 / 冲 / 刑 / 穿
    target_char 不必出现在原局；只要流年带来或与之形成关系即算引动。

    注意：此函数对 04 § 5 触发引擎的"本字到"和"合冲引动"提供基础。
    """
    ln = liunian_ganzhi(year)

    # 是天干？
    if target_char in GAN_LIST:
        # 流年带本字
        if ln.gan == target_char:
            return True
        # 天干合
        if gan_he(ln.gan, target_char) is not None:  # type: ignore[arg-type]
            return True
        return False

    # 是地支
    if target_char in ZHI_LIST:
        # 流年带本字
        if ln.zhi == target_char:
            return True
        # 六合
        if zhi_liuhe(ln.zhi, target_char) is not None:  # type: ignore[arg-type]
            return True
        # 三合半合（流年与 target 是同三合局的两支）
        if zhi_sanhe([ln.zhi, target_char]) is not None:  # type: ignore[arg-type]
            return True
        # 冲
        if zhi_chong(ln.zhi, target_char):  # type: ignore[arg-type]
            return True
        # 刑（任一刑式）
        if zhi_xing(ln.zhi, target_char) is not None:  # type: ignore[arg-type]
            return True
        # 穿
        if zhi_chuan(ln.zhi, target_char):  # type: ignore[arg-type]
            return True
        return False

    raise ValueError(f"target_char 必须是干或支: {target_char!r}")


# ============================================================
# 9. find_year_when_zhi_appears
# ============================================================

def find_year_when_zhi_appears(
    start: int, end: int, target_zhi: Zhi
) -> list[int]:
    """[start, end] 闭区间内流年地支等于 target_zhi 的所有年份。

    每 12 年循环一次，返回升序列表。
    """
    if target_zhi not in ZHI_LIST:
        raise ValueError(f"非法地支: {target_zhi!r}")
    if start > end:
        return []
    out: list[int] = []
    for y in range(start, end + 1):
        if liunian_ganzhi(y).zhi == target_zhi:
            out.append(y)
    return out


# ============================================================
# 辅助：过渡期判定（04 § 4.2 layer2_check 使用，不在契约 9 函数内）
# ============================================================

def is_in_dayun_transition(
    year: int, dayun_step: DayunStep, threshold_years: int = 1
) -> bool:
    """该年是否处于大运过渡期（距起讫年端 ±threshold_years）。

    rationale: 04-gate § 4.2 "过渡期惩罚"——L2 仅靠相邻大运字通过时降 1 ★。
    """
    start_y, end_y = dayun_step.起讫年
    # 距起年 ≤ threshold 或距讫年 ≤ threshold
    return (
        abs(year - start_y) <= threshold_years
        or abs(year - (end_y - 1)) <= threshold_years
    )


def get_adjacent_dayun(
    dayun: Dayun, current: DayunStep
) -> Optional[DayunStep]:
    """取相邻大运（优先取下一步；若 current 是末步取上一步）。"""
    try:
        idx = dayun.排布.index(current)
    except ValueError:
        return None
    if idx + 1 < len(dayun.排布):
        return dayun.排布[idx + 1]
    if idx - 1 >= 0:
        return dayun.排布[idx - 1]
    return None


# ============================================================
# smoke test
# ============================================================

def _smoke() -> None:
    # 1) liunian_ganzhi 锚点
    anchors = [
        (1980, "庚", "申"),
        (1982, "壬", "戌"),
        (1984, "甲", "子"),  # 60 甲子起点
        (2005, "乙", "酉"),
        (2006, "丙", "戌"),
        (2013, "癸", "巳"),
        (2020, "庚", "子"),
        (2024, "甲", "辰"),
        (2026, "丙", "午"),
    ]
    for y, expg, expz in anchors:
        gz = liunian_ganzhi(y)
        assert gz.gan == expg and gz.zhi == expz, \
            f"liunian_ganzhi({y}) = {gz} expected {expg}{expz}"
    print("[OK] liunian_ganzhi 9 个锚点全过")

    # 2) Build C-001 dayun for further tests
    from engine.predicates.types import GanZhi, DayunStep
    paibu = [
        DayunStep(序号=1, 干支=GanZhi("己", "卯"), 起岁=8,  止岁=17, 起讫年=(1988, 1998)),
        DayunStep(序号=2, 干支=GanZhi("庚", "辰"), 起岁=18, 止岁=27, 起讫年=(1998, 2008)),
        DayunStep(序号=3, 干支=GanZhi("辛", "巳"), 起岁=28, 止岁=37, 起讫年=(2008, 2018)),
        DayunStep(序号=4, 干支=GanZhi("壬", "午"), 起岁=38, 止岁=47, 起讫年=(2018, 2028)),
        DayunStep(序号=5, 干支=GanZhi("癸", "未"), 起岁=48, 止岁=57, 起讫年=(2028, 2038)),
    ]
    dy = Dayun(起运岁=8.5, 起运年=1988, 顺逆="顺", 排布=paibu)

    # 3) get_dayun_at_age
    assert get_dayun_at_age(dy, 25).干支 == GanZhi("庚", "辰")
    assert get_dayun_at_age(dy, 33).干支 == GanZhi("辛", "巳")
    try:
        get_dayun_at_age(dy, 5)
        raise AssertionError("起运前应 raise")
    except ValueError:
        pass

    # 4) get_dayun_at_year
    assert get_dayun_at_year(dy, 1980, 2005).干支 == GanZhi("庚", "辰")
    assert get_dayun_at_year(dy, 1980, 2013).干支 == GanZhi("辛", "巳")
    assert get_dayun_at_year(dy, 1980, 2020).干支 == GanZhi("壬", "午")

    # 5) C-001 bazi 构造
    from engine.predicates.types import _default_canggan_for
    bazi = Bazi(
        年柱=GanZhi("庚", "申"),
        月柱=GanZhi("戊", "寅"),
        日柱=GanZhi("壬", "子"),
        时柱=GanZhi("辛", "丑"),
    )
    bazi.藏干 = _default_canggan_for(bazi)

    # 6) is_dayun_zhi_chong_bazi
    # 大运壬午(38-47岁=2018-2028) → 午冲子（日支）
    chongs = is_dayun_zhi_chong_bazi(paibu[3], bazi)
    assert "日支" in chongs, f"壬午冲子应在日支: {chongs}"

    # 7) is_liunian_with_dayun_he
    # 2005 乙酉 vs 庚辰 → 乙庚合(化金) + 辰酉合(化金) → 任一返回金
    h = is_liunian_with_dayun_he(2005, paibu[1])
    assert h == "金", f"2005 乙酉 + 庚辰 应化金: {h}"

    # 8) is_liunian_with_bazi_he
    # 2005 乙酉 → 乙合年干庚(化金) + 酉合时支辰? 时支=丑 不合 → 仅年柱
    he_list = is_liunian_with_bazi_he(2005, bazi)
    palaces = [p for p, _ in he_list]
    assert "年柱" in palaces, f"2005 乙合年干庚应在年柱: {he_list}"

    # 9) is_liunian_chong_bazi
    # 2026 丙午 → 午冲日支子
    chongs = is_liunian_chong_bazi(2026, bazi)
    assert "日支" in chongs, f"2026 午冲子: {chongs}"

    # 10) is_liunian_yingdong_bazi_zi
    # 2005 乙酉 → 引动 庚（年干, 乙庚合）
    assert is_liunian_yingdong_bazi_zi(2005, "庚", bazi)
    # 2005 乙酉 → 引动 子？酉与子无关
    assert not is_liunian_yingdong_bazi_zi(2005, "子", bazi)
    # 2005 乙酉 → 引动 申（年支, 申子半合 vs 酉？酉与申无合冲）→ False
    assert not is_liunian_yingdong_bazi_zi(2005, "申", bazi)
    # 2026 丙午 → 引动 子（午冲子）
    assert is_liunian_yingdong_bazi_zi(2026, "子", bazi)
    # 2024 甲辰 → 引动 子（申子辰三合）
    assert is_liunian_yingdong_bazi_zi(2024, "子", bazi)

    # 11) find_year_when_zhi_appears
    years = find_year_when_zhi_appears(2000, 2030, "辰")
    assert 2024 in years and 2012 in years, f"2024/2012 应是辰年: {years}"
    assert len(years) == 3, f"2000-2030 间应有 3 个辰年: {years}"  # 2000,2012,2024

    # 12) 过渡期辅助
    # 2017 在辛巳运(2008-2018)末年(2017 距讫年 2018 = 1) → 过渡期
    assert is_in_dayun_transition(2017, paibu[2], threshold_years=1)
    # 2010 在辛巳运中段 → 不过渡
    assert not is_in_dayun_transition(2010, paibu[2], threshold_years=1)
    # 相邻大运
    adj = get_adjacent_dayun(dy, paibu[2])
    assert adj == paibu[3]

    print("[OK] cycles smoke：9 函数 + 2 辅助全过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
