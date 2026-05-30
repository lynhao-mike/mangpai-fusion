"""engine/picture/caifu.py · v1.2 D2 杨派 · 财富 7 等 + 官命 9 取

杨派财富级别（M2-Y-035）：
| 排序 | 类型 | 说明 |
|---|---|---|
| 1 | 官杀库 | 最大（开了=亿级） |
| 2 | 食伤库 | 次大 |
| 3 | 旺杀   | 制杀第一大=制和化一样 |
| 4 | 财库   | 中等 |
| 5 | 旺官   | — |
| 6 | 食伤当财 | 比财大但有限 |
| 7 | 纯财   | 直接以财为财最小 |

杨派官命 9 取（M2-Y-042）：
| 排序 | 取官方式 | 层次 |
|---|---|---|
| 1 | 化杀生枭 | 行政最高层 |
| 2 | 化官生印 | 行政官/书记 |
| 3 | 合完整官 | 官大 |
| 4 | 财生官+合官 | 官大但低于化杀 |
| 5 | 食神制杀 | 技术官/企业官 |
| 6 | 比劫生食伤制杀 | 吃皇粮 |
| 7 | 劫财制财 | 武职 |
| 8 | 伤官伤尽 | 当官（条件：伤官暗制官） |
| 9 | 制印得权 | 条件：印不化官杀+印与体打架 |

⚠️ 上游约束（08 § 失败兜底）：
    必须遵守 EnergyFindings.wealth_ceiling，D2 不能给"巨富级食伤库"
    若 D1=中富级·上 但本派触发官杀库（rank 1=亿级）→ 标记 violation 并降级到 rank ≤ 4。

作者：Track-B
"""
from __future__ import annotations

from typing import Optional

from engine.energy.types import EnergyFindings, Evidence
from engine.picture.types import CaifuRanking, GuanmingQufa
from engine.predicates.ganzhi import gan_to_wuxing, zhi_to_wuxing
from engine.predicates.palace import find_shishen_in_bazi, get_shishen
from engine.predicates.relations import zhi_chong, zhi_xing
from engine.predicates.types import (
    Bazi,
    Gan,
    GanZhi,
    Wuxing,
    Zhi,
    ZHI_CANGGAN_TABLE,
)


# ============================================================
# 工具：库支识别 + 库内含财官的支
# ============================================================

# 五行墓库表
_MUKU_TABLE: dict[Wuxing, Zhi] = {
    "水": "辰", "火": "戌", "木": "未", "金": "丑",
}


def _is_库_zhi(z: Zhi) -> bool:
    return z in ("辰", "戌", "丑", "未")


def _has_库_with_shishen(
    bazi: Bazi, shishens: set[str],
) -> Optional[tuple[str, Zhi, list[str]]]:
    """检查是否有库支藏 shishens 中的十神。

    返回 (palace, zhi, [shishens 中触发的字]) 或 None
    """
    day_master = bazi.day_master
    for palace, zhi in bazi.all_zhis():
        if not _is_库_zhi(zhi):
            continue
        cangs = ZHI_CANGGAN_TABLE.get(zhi, [])
        triggered_chars: list[str] = []
        for cg, _, _ in cangs:
            ss = get_shishen(cg, day_master)
            if ss in shishens:
                triggered_chars.append(cg)
        if triggered_chars:
            return (palace, zhi, triggered_chars)
    return None


def _is_库_開(zhi: Zhi, bazi: Bazi) -> bool:
    """库是否被冲/刑打开。"""
    for _, oz in bazi.all_zhis():
        if oz == zhi:
            continue
        if zhi_chong(zhi, oz) or zhi_xing(zhi, oz):
            return True
    return False


# ============================================================
# 财富 7 等：从高到低判定
# ============================================================

# wealth_ceiling 自然 rank 区间映射：
# 财富越大 → rank 越小
# 巨富 = rank 1（官杀库为主）
# 大富 = rank 1-2（官杀库/食伤库）
# 中富 = rank 3-4（旺杀/财库）
# 小富 = rank 5-6（旺官/食伤当财）
# 贫困 = rank 6-7（食伤当财/纯财）
_WEALTH_TO_RANK_RANGE: dict[str, tuple[int, int]] = {
    "巨富": (1, 2),
    "大富": (1, 3),
    "中富": (3, 5),
    "小富": (5, 6),
    "贫困": (6, 7),
}


def _wealth_rank_range(wc: str) -> tuple[int, int]:
    for prefix, rng in _WEALTH_TO_RANK_RANGE.items():
        if wc.startswith(prefix):
            return rng
    return (1, 7)


def compute_caifu(
    energy: EnergyFindings,
    bazi: Bazi,
) -> CaifuRanking:
    """财富 7 等判定。

    优先级：从高到低（rank 1 → 7）依次判定，命中即返回。
    上游约束：D1 wealth_ceiling 决定 rank 自然区间。
    若结构匹配的 rank 高于（数值更小）允许范围 → 降到允许下限；
    若结构匹配的 rank 低于（数值更大）允许范围 → 抬到允许上限。
    """
    # ---- 上游约束 ----
    wc = energy.wealth_ceiling
    rank_lo, rank_hi = _wealth_rank_range(wc)

    evidences: list[Evidence] = [Evidence(
        rule_id="M2-Y-035",
        school="杨",
        description=(
            f"财富 7 等判定（上游 wealth_ceiling={wc}, "
            f"自然区间 rank∈[{rank_lo},{rank_hi}]）"
        ),
        weight=0.70,
    )]

    # ---- 结构识别（从最强到最弱）----
    sha_locs = find_shishen_in_bazi("七杀", bazi)
    guan_locs_only = find_shishen_in_bazi("正官", bazi)
    food_locs = (
        find_shishen_in_bazi("食神", bazi)
        + find_shishen_in_bazi("伤官", bazi)
    )
    cai_locs = (
        find_shishen_in_bazi("正财", bazi)
        + find_shishen_in_bazi("偏财", bazi)
    )

    candidates: list[tuple[int, str, str, list[Evidence]]] = []

    # rank 1 候选：官杀库
    res = _has_库_with_shishen(bazi, {"正官", "七杀"})
    if res is not None:
        palace, zhi, chars = res
        opened = _is_库_開(zhi, bazi)
        candidates.append((
            1, "官杀库",
            f"{palace}{zhi}库藏官杀{','.join(chars)}"
            f"{'（已开）' if opened else '（未开）'}",
            [Evidence(rule_id="M2-Y-034", school="杨",
                      description="开官杀库=亿级", weight=0.85)],
        ))

    # rank 2 候选：食伤库
    res = _has_库_with_shishen(bazi, {"食神", "伤官"})
    if res is not None:
        palace, zhi, chars = res
        opened = _is_库_開(zhi, bazi)
        candidates.append((
            2, "食伤库",
            f"{palace}{zhi}库藏食伤{','.join(chars)}"
            f"{'（已开）' if opened else '（未开）'}",
            [],
        ))

    # rank 3 候选：旺杀（七杀≥2 见 + 食伤）
    if sha_locs and food_locs and len(sha_locs) >= 2:
        candidates.append((
            3, "旺杀",
            f"七杀{len(sha_locs)}见 + 食伤{len(food_locs)}见 → 制杀有功",
            [Evidence(rule_id="M2-Y-052", school="杨",
                      description="制杀第一大=制和化一样", weight=0.75)],
        ))

    # rank 4 候选：财库
    res = _has_库_with_shishen(bazi, {"正财", "偏财"})
    if res is not None:
        palace, zhi, chars = res
        opened = _is_库_開(zhi, bazi)
        candidates.append((
            4, "财库",
            f"{palace}{zhi}库藏财{','.join(chars)}"
            f"{'（已开）' if opened else '（未开）'}",
            [],
        ))

    # rank 5 候选：旺官（≥2 个官杀字）
    all_guan = guan_locs_only + sha_locs
    if len(all_guan) >= 2:
        candidates.append((
            5, "旺官",
            f"官杀{len(all_guan)}见 → 旺官",
            [],
        ))

    # rank 6 候选：食伤当财（无财但食伤多）
    if food_locs and not cai_locs:
        candidates.append((
            6, "食伤当财",
            f"原局无财 + 食伤{len(food_locs)}见 → 食伤当财（M2-Y-109）",
            [Evidence(rule_id="M2-Y-109", school="杨",
                      description="伤官当财看", weight=0.65)],
        ))

    # rank 7 候选：纯财
    if cai_locs:
        candidates.append((
            7, "纯财",
            f"纯财格：{len(cai_locs)} 财字（直接以财为财最小）",
            [],
        ))

    # ---- 选择：偏好命中 [rank_lo, rank_hi] 的候选；其次邻近 ----
    # 1) 在区间内 → 选最高 rank（rank 数值最小）
    in_range = [c for c in candidates if rank_lo <= c[0] <= rank_hi]
    if in_range:
        chosen = min(in_range, key=lambda c: c[0])
    else:
        # 2) 区间外 → 选最接近区间的（取距离最小者）
        if candidates:
            def dist(c: tuple) -> int:
                rk = c[0]
                if rk < rank_lo:
                    return rank_lo - rk
                if rk > rank_hi:
                    return rk - rank_hi
                return 0
            chosen = min(candidates, key=lambda c: (dist(c), c[0]))
            # 强制将 rank 钳到允许区间（避免输出超出 wealth_ceiling 的级别）
            orig_rank, ctype, rationale, ev = chosen
            clamped = max(rank_lo, min(rank_hi, orig_rank))
            if clamped != orig_rank:
                rationale = (
                    f"{rationale} [上游 wealth_ceiling={wc} → "
                    f"由 rank{orig_rank}({ctype}) 钳到 rank{clamped}]"
                )
                chosen = (clamped, ctype, rationale, ev)
        else:
            # 3) 无任何候选 → 兜底 rank 7
            chosen = (7, "纯财", "原局财官信息不足 → 兜底 rank 7", [])

    rank, ctype, rationale, extra_ev = chosen
    return CaifuRanking(
        rank=rank, type=ctype, rationale=rationale,
        evidence=evidences + extra_ev,
    )


# ============================================================
# 官命 9 取
# ============================================================

def compute_guanming(
    energy: EnergyFindings,
    bazi: Bazi,
) -> Optional[GuanmingQufa]:
    """官命 9 取判定（最常见 3-5 种，其余可简版）。

    规则（按层次从高到低）：
    1 化杀生枭   = 七杀 + 偏印 + 七杀生偏印
    2 化官生印   = 正官 + 正印 + 正官生正印
    3 合完整官   = 天干合官（合到主位）
    4 财生官+合官 = 财生官的同时官被合
    5 食神制杀   = 食神 + 七杀 + 食神能克七杀
    6 比劫生食伤制杀 = 比劫+食伤+七杀
    7 劫财制财   = 劫财 + 财
    8 伤官伤尽   = 伤官旺 + 无官（M2-Y-098）
    9 制印得权   = 印 + 制印（如比劫制印）
    """
    day_master = bazi.day_master

    yin_zheng = find_shishen_in_bazi("正印", bazi)
    yin_pian = find_shishen_in_bazi("偏印", bazi)
    sha_locs = find_shishen_in_bazi("七杀", bazi)
    guan_locs = find_shishen_in_bazi("正官", bazi)
    food_locs = find_shishen_in_bazi("食神", bazi)
    shang_locs = find_shishen_in_bazi("伤官", bazi)
    bi_locs = find_shishen_in_bazi("比肩", bazi) + find_shishen_in_bazi("劫财", bazi)
    jie_locs = find_shishen_in_bazi("劫财", bazi)
    cai_locs = (
        find_shishen_in_bazi("正财", bazi)
        + find_shishen_in_bazi("偏财", bazi)
    )

    # ---- 1 化杀生枭 ----
    if sha_locs and yin_pian:
        return GuanmingQufa(
            rank=1, type="化杀生枭",
            rationale="七杀 + 偏印 同现 → 化杀生枭=行政最高层（罕）",
            evidence=[Evidence(
                rule_id="M2-Y-042", school="杨",
                description="化杀生枭=官命1层", weight=0.80,
            )],
        )

    # ---- 2 化官生印 ----
    if guan_locs and yin_zheng:
        return GuanmingQufa(
            rank=2, type="化官生印",
            rationale="正官 + 正印 同现 → 化官生印=行政官/党务",
            evidence=[Evidence(
                rule_id="M2-Y-042", school="杨",
                description="化官生印=官命2层", weight=0.78,
            )],
        )

    # ---- 5 食神制杀 ----
    if sha_locs and food_locs:
        return GuanmingQufa(
            rank=5, type="食神制杀",
            rationale="七杀 + 食神 同现 → 食神制杀=技术官/企业官",
            evidence=[Evidence(
                rule_id="M2-Y-042", school="杨",
                description="食神制杀=官命5层", weight=0.72,
            )],
        )

    # ---- 6 比劫生食伤制杀 ----
    if sha_locs and (food_locs or shang_locs) and bi_locs:
        return GuanmingQufa(
            rank=6, type="比劫生食伤制杀",
            rationale="比劫+食伤+七杀 → 比劫生食伤制杀=吃皇粮",
            evidence=[Evidence(
                rule_id="M2-Y-042", school="杨",
                description="比劫生食伤制杀=官命6层", weight=0.68,
            )],
        )

    # ---- 7 劫财制财 ----
    if jie_locs and cai_locs:
        return GuanmingQufa(
            rank=7, type="劫财制财",
            rationale="劫财 + 财 → 劫财制财=武职（M2-Y-042 / Y-068）",
            evidence=[Evidence(
                rule_id="M2-Y-042", school="杨",
                description="劫财制财=官命7层", weight=0.62,
            )],
        )

    # ---- 8 伤官伤尽 ----
    if shang_locs and not guan_locs:
        return GuanmingQufa(
            rank=8, type="伤官伤尽",
            rationale="伤官旺+无官 → 伤官伤尽（条件未必满足，仅候选）",
            evidence=[Evidence(
                rule_id="M2-Y-098", school="杨",
                description="伤官合杀=层次高", weight=0.55,
            )],
        )

    # 兜底：无明显官命结构
    return None


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
        "C-2026-011-乾-乙丑乙酉丁丑癸卯",
        "C-2026-012-坤-壬戌癸丑丙申壬辰",
    ]:
        parsed = load_case(cid)
        ef = evaluate_energy(parsed)
        cf = compute_caifu(ef, parsed.bazi)
        gm = compute_guanming(ef, parsed.bazi)
        print(f"\n=== {cid} ===")
        print(f"  D1 wealth_ceiling = {ef.wealth_ceiling}")
        print(f"  D2 caifu rank={cf.rank} ({cf.type}): {cf.rationale}")
        if gm:
            print(f"  D2 guanming rank={gm.rank} ({gm.type}): {gm.rationale}")
        else:
            print(f"  D2 guanming: 无明显官命结构")
    print("\n[OK] caifu smoke 通过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
