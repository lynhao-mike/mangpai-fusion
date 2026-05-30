"""engine/picture/wubu.py · v1.2 D2 杨派 · 五步算命法

杨派算命切入点五步法（M2-Y-119）：

```
第1步：先在家里找财官（日时=家里）
  → 家里有 → 弱制就能得到
  → 家里没有 → 去外面找（年月=外面）→ 看力量

第2步：看财官从哪里出来（寻根基）
  → 从我坐下出 = 完全是我自己的
  → 从比劫宫出 = 两人的/合作
  → 从年月出/无出处 = 国家的/外面的

第3步：用什么取财官（定层次）
  → 用印/食伤取 = 管理者/白领（层次高）
  → 用比劫取 = 劳动者（层次低）
  → 禄克财 = 最底层

第4步：天干透什么定吃皇粮/民营（M2-Y-120）
  → 天干透官/印/食伤 = 端国家饭碗（吃皇粮）
  → 天干透比劫 = 端比劫饭碗（民营）
  → 财从比劫坐下出 = 民营/合作

第5步：地支做什么定具体职业（天地一气 M2-Y-121）
  → 天干地支做功一致 = 天地一气 = 表里如一
  → 不一致 = 表里不一/内心想法与表面不同
```

输入：EnergyFindings + ParsedInput
输出：list[WubuStep]，5 步全跑

作者：Track-B
"""
from __future__ import annotations

from typing import Optional

from engine.energy.types import EnergyFindings, Evidence
from engine.picture.types import WubuStep
from engine.predicates.ganzhi import gan_to_wuxing, zhi_to_wuxing
from engine.predicates.palace import (
    find_shishen_in_bazi,
    get_shishen,
)
from engine.predicates.types import (
    Bazi,
    Gan,
    GanZhi,
    ParsedInput,
    Shishen,
    ZHI_CANGGAN_TABLE,
)


# ============================================================
# Step 1：家里找财官
# ============================================================

# 家里 = 日柱 + 时柱（M2-Y-049）
_HOME_PALACES = {"日柱", "时柱", "日支", "时支"}
_OUTSIDE_PALACES = {"年柱", "月柱", "年支", "月支"}


def _step1_find_home_caiguan(bazi: Bazi) -> tuple[str, list[Evidence]]:
    """第 1 步：在家里（日时柱）找财官。"""
    home_caiguan: list[tuple[str, str, str]] = []  # (palace, char, ss)
    outside_caiguan: list[tuple[str, str, str]] = []

    cai_locs = (
        find_shishen_in_bazi("正财", bazi)
        + find_shishen_in_bazi("偏财", bazi)
    )
    guan_locs = (
        find_shishen_in_bazi("正官", bazi)
        + find_shishen_in_bazi("七杀", bazi)
    )
    for ss_locs, ss_label in [
        (cai_locs, "财"), (guan_locs, "官"),
    ]:
        for palace, char in ss_locs:
            tag = (palace, char, ss_label)
            if palace in _HOME_PALACES:
                home_caiguan.append(tag)
            elif palace in _OUTSIDE_PALACES:
                outside_caiguan.append(tag)

    if home_caiguan:
        items = "/".join(f"{p}{c}({s})" for p, c, s in home_caiguan)
        finding = (
            f"家里有财官：{items} → 弱制即得，自家拿（M2-Y-019/023）"
        )
    elif outside_caiguan:
        items = "/".join(f"{p}{c}({s})" for p, c, s in outside_caiguan)
        finding = (
            f"家里无财官，外面有：{items} → 须看力量是否制得住（M2-Y-019）"
        )
    else:
        finding = "家里和外面都未见财官 → 偏向食伤当财或纯比劫（M2-Y-109）"

    ev = [Evidence(
        rule_id="M2-Y-119", school="杨",
        description="第1步家里找财官", weight=0.72,
    ), Evidence(
        rule_id="M2-Y-019", school="杨",
        description="家里有先拿家里的", weight=0.65,
    )]
    return finding, ev


# ============================================================
# Step 2：出处（寻根基）
# ============================================================

def _step2_chuchu(bazi: Bazi) -> tuple[str, list[Evidence]]:
    """第 2 步：财官从哪里出来。"""
    day_master = bazi.day_master
    cai_locs = (
        find_shishen_in_bazi("正财", bazi)
        + find_shishen_in_bazi("偏财", bazi)
    )
    guan_locs = (
        find_shishen_in_bazi("正官", bazi)
        + find_shishen_in_bazi("七杀", bazi)
    )
    all_locs = cai_locs + guan_locs

    if not all_locs:
        finding = "财官无出处 → 借食伤当财；或借比劫合伙（M2-Y-109）"
    else:
        # 看出在哪
        from_self = any(p == "日支" for p, _ in all_locs)
        from_bijie = False
        # 比劫宫 = 比劫所在柱
        bijie_locs = (
            find_shishen_in_bazi("比肩", bazi)
            + find_shishen_in_bazi("劫财", bazi)
        )
        bijie_palaces = {p for p, _ in bijie_locs}
        for p, c in all_locs:
            # 财官出自比劫坐下：比劫宫与财官在同支
            if p in bijie_palaces:
                from_bijie = True
                break
        from_outside = any(p in _OUTSIDE_PALACES for p, _ in all_locs)

        parts = []
        if from_self:
            parts.append("从坐下出 = 完全是我自己的")
        if from_bijie:
            parts.append("从比劫宫出 = 两人的/合作")
        if from_outside and not from_self:
            parts.append("从年月出 = 外面的/国家的")
        finding = "；".join(parts) if parts else (
            f"财官出自其他位置：{all_locs[:3]}"
        )

    ev = [Evidence(
        rule_id="M2-Y-119", school="杨",
        description="第2步看财官出处", weight=0.70,
    ), Evidence(
        rule_id="M2-Y-162", school="杨",
        description="寻根基", weight=0.65,
    )]
    return finding, ev


# ============================================================
# Step 3：取法（定层次）
# ============================================================

def _step3_qufa(
    energy: EnergyFindings, bazi: Bazi,
) -> tuple[str, list[Evidence]]:
    """第 3 步：用什么取财官（定层次）。"""
    # 看 D1 的 muxing_qufa（段派母星取法）
    duan_qufa = energy.muxing_qufa  # 禄/食伤/比劫/印
    # 杨派看法：用印 → 高，用食伤 → 中，用比劫 → 低
    if duan_qufa == "印":
        layer = "高（管理者/白领）"
    elif duan_qufa == "食伤":
        layer = "中（技术/销售/中介）"
    elif duan_qufa == "比劫":
        layer = "低（劳动者）"
    elif duan_qufa == "禄":
        # 禄能合财官 = 富贵；禄克财 = 卑微
        # 这里是粗判：默认中等
        layer = "中等（看禄是否合到财官）"
    else:
        layer = "中等"

    # 看 D1 的 layer_count 给"层次系数"
    if energy.layer_count >= 2:
        layer = f"{layer}（D1 层数={energy.layer_count}=做功扎实）"
    elif energy.layer_count == 1:
        layer = f"{layer}（D1 层数=1=单层有功）"
    else:
        layer = f"{layer}（D1 层数=0=做功未启动）"

    finding = (
        f"段派母星取法={duan_qufa} → 杨派对应层次={layer}（M2-Y-021/119）"
    )
    ev = [Evidence(
        rule_id="M2-Y-021", school="杨",
        description="体取财官层次排序", weight=0.72,
    )]
    return finding, ev


# ============================================================
# Step 4：皇粮 vs 民营
# ============================================================

def _step4_huangliang(bazi: Bazi) -> tuple[str, list[Evidence]]:
    """第 4 步：天干透什么定吃皇粮/民营（M2-Y-120）。"""
    day_master = bazi.day_master
    tou_shishens: dict[Shishen, list[str]] = {}
    for name, gan in bazi.all_gans():
        if name == "日柱":
            continue
        ss = get_shishen(gan, day_master)
        tou_shishens.setdefault(ss, []).append(f"{name[0]}干{gan}")

    has_guan = any(
        ss in tou_shishens for ss in ("正官", "七杀")
    )
    has_yin = any(
        ss in tou_shishens for ss in ("正印", "偏印")
    )
    has_food = any(
        ss in tou_shishens for ss in ("食神", "伤官")
    )
    has_bijie = any(
        ss in tou_shishens for ss in ("比肩", "劫财")
    )

    parts = []
    if has_guan:
        parts.append(f"天干透官杀{tou_shishens.get('正官',[]) + tou_shishens.get('七杀',[])} → 端国家饭碗")
    if has_yin:
        parts.append(f"天干透印{tou_shishens.get('正印',[]) + tou_shishens.get('偏印',[])} → 文教/管理（吃皇粮候选）")
    if has_food:
        parts.append(f"天干透食伤{tou_shishens.get('食神',[]) + tou_shishens.get('伤官',[])} → 技术/销售（吃皇粮候选）")

    if has_guan or has_yin or has_food:
        finding = (
            f"吃皇粮候选：{'；'.join(parts)}（M2-Y-120）"
        )
    elif has_bijie:
        finding = (
            f"天干透比劫{tou_shishens.get('比肩',[]) + tou_shishens.get('劫财',[])} → 端比劫饭碗=民营/合作"
        )
    else:
        finding = "天干无官印食伤透出 → 偏民营/自由"

    ev = [Evidence(
        rule_id="M2-Y-120", school="杨",
        description="吃皇粮判定", weight=0.75,
    )]
    return finding, ev


# ============================================================
# Step 5：天地一气
# ============================================================

def _step5_tiandi(bazi: Bazi) -> tuple[str, list[Evidence]]:
    """第 5 步：天干地支做功是否一致 = 天地一气（M2-Y-121）。"""
    day_master = bazi.day_master

    # 天干十神类
    gan_groups: set[str] = set()
    for name, gan in bazi.all_gans():
        if name == "日柱":
            continue
        ss = get_shishen(gan, day_master)
        gan_groups.add(_shishen_group(ss))

    # 地支主气十神类
    zhi_groups: set[str] = set()
    for _, zhi in bazi.all_zhis():
        cangs = ZHI_CANGGAN_TABLE.get(zhi, [])
        if cangs:
            ss = get_shishen(cangs[0][0], day_master)
            zhi_groups.add(_shishen_group(ss))

    overlap = gan_groups & zhi_groups
    if "财" in overlap and "官杀" in overlap:
        finding = "天干地支均含财/官 → 天地一气（表里如一）（M2-Y-121）"
    elif "印" in overlap and ("官杀" in gan_groups or "比劫" in zhi_groups):
        finding = "印作天干、官杀作天干 → 官印呼应（吃皇粮的标志）"
    elif overlap:
        finding = (
            f"天干十神类({sorted(gan_groups)}) 与地支主气({sorted(zhi_groups)})"
            f"重叠在 {sorted(overlap)} → 部分一致"
        )
    else:
        finding = (
            f"天干({sorted(gan_groups)}) 与地支({sorted(zhi_groups)})无重叠"
            f" → 表里不一（内心与外表分离）"
        )

    ev = [Evidence(
        rule_id="M2-Y-121", school="杨",
        description="天地一气原则", weight=0.70,
    )]
    return finding, ev


def _shishen_group(ss: Shishen) -> str:
    return {
        "比肩": "比劫", "劫财": "比劫",
        "食神": "食伤", "伤官": "食伤",
        "正财": "财", "偏财": "财",
        "正官": "官杀", "七杀": "官杀",
        "正印": "印", "偏印": "印",
    }[ss]


# ============================================================
# 主入口
# ============================================================

def run_wubu(
    energy: EnergyFindings,
    parsed: ParsedInput,
) -> list[WubuStep]:
    """五步算命法主入口（5 步全跑）。"""
    bazi = parsed.bazi

    f1, e1 = _step1_find_home_caiguan(bazi)
    f2, e2 = _step2_chuchu(bazi)
    f3, e3 = _step3_qufa(energy, bazi)
    f4, e4 = _step4_huangliang(bazi)
    f5, e5 = _step5_tiandi(bazi)

    return [
        WubuStep(step=1, name="家里找财官", finding=f1, evidence=e1),
        WubuStep(step=2, name="出处", finding=f2, evidence=e2),
        WubuStep(step=3, name="取法", finding=f3, evidence=e3),
        WubuStep(step=4, name="皇粮民营", finding=f4, evidence=e4),
        WubuStep(step=5, name="天地一气", finding=f5, evidence=e5),
    ]


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    from tests.fixtures.cases import load_case
    from engine.energy.evaluator import evaluate_energy

    for cid in [
        "C-2026-001-乾-庚申戊寅壬子辛丑",
        "C-2026-002-坤-壬戌庚戌戊辰丙辰",
        "C-2026-014-乾-丙戌庚子乙亥辛巳",
    ]:
        parsed = load_case(cid)
        energy = evaluate_energy(parsed)
        steps = run_wubu(energy, parsed)
        print(f"\n=== {cid} 五步法 ===")
        for s in steps:
            print(f"  Step {s.step}: {s.name}")
            print(f"    → {s.finding}")
        assert len(steps) == 5
    print("\n[OK] wubu smoke 通过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
