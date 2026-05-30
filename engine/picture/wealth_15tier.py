"""engine/picture/wealth_15tier.py · F5 · 15 层富贵分级映射

按 portrait-v2 § 二定义的 15 层标度（杨清娟盲派 + 业内通用）。
每个域（学业/事业/婚姻/财富/官命）输出 (low, mid, high) 区间。

输入：
- D1 段派 EnergyFindings.wealth_ceiling: 5 buckets
  · 贫寒 → L1-L3
  · 小康 → L4-L7
  · 中富级·下/中/上 → L8/L9/L10
  · 大富 → L11-L13
  · 巨富 → L14-L15
- D1 layer_count: 1-5+ 层（做功层数封顶 caifu）
- D2 杨派 CaifuRanking.rank: 1-7（1=最大，7=最小）
- D2 杨派 GuanmingQufa.rank: 1-9（1=化杀生枭最大，9=制印得权最小）
- D4 高派 ciguan/xuetang boost（学业辅佐神煞）

业务规则（保守，宁可窄不可放大）：
- 财富域：以 D1.wealth_ceiling 为骨架；做功层数对 mid 做 ±1 微调
- 事业域：以 D2.guanming.rank 为上限；D1.layer_count 决定实际兑现
- 学业域：D1.wealth_ceiling 基线 + D4 学业 boost 提一档
- 婚姻域：以 D4 高派婚姻旁证 net boost 对 D2.caifu 镜像微调
- 官命域：guanming.rank 直接映射理论上限 + layer 决定兑现

注意：
- 所有区间是**结构性区间**（structural bands），不带应期/铁断
- 真实命主可能由于人生选择、社会变迁等"低于结构上限"
- 用 Wealth15Tier.tier_disclaimer 字段提示这一点

作者：Kiro Agent · v1.3.1 (PR #33)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional


# ============================================================
# 一、15 层标度定义（house-defined）
# ============================================================

TIER_TABLE: list[dict[str, Any]] = [
    {"tier": 1,  "label": "极贫",   "society": "流民/乞讨",          "income_cny": "<1万"},
    {"tier": 2,  "label": "贫寒",   "society": "长工/苦力",          "income_cny": "1-3万"},
    {"tier": 3,  "label": "温饱",   "society": "小贩/散工",          "income_cny": "3-6万"},
    {"tier": 4,  "label": "普工",   "society": "蓝领/低技工",        "income_cny": "6-10万"},
    {"tier": 5,  "label": "工薪",   "society": "蓝领骨干/办事员",    "income_cny": "10-20万"},
    {"tier": 6,  "label": "小康下", "society": "白领基层/个体户",    "income_cny": "20-30万"},
    {"tier": 7,  "label": "小康中", "society": "普通公务员/国企科员","income_cny": "30-50万"},
    {"tier": 8,  "label": "小康上", "society": "科级/小老板/资深技术","income_cny": "50-100万"},
    {"tier": 9,  "label": "中富下", "society": "副处/民企中层",      "income_cny": "100-200万 / 千万级资产"},
    {"tier": 10, "label": "中富中", "society": "正处/民企高管",      "income_cny": "200-500万 / 千万级"},
    {"tier": 11, "label": "中富上", "society": "副厅/上市中层",      "income_cny": "500-1000万 / 数千万"},
    {"tier": 12, "label": "大富下", "society": "正厅/上市高管",      "income_cny": "1000-3000万 / 亿级起"},
    {"tier": 13, "label": "大富中", "society": "副部/产业头部",      "income_cny": "3000万-1亿 / 数亿"},
    {"tier": 14, "label": "大富上", "society": "正部/巨头创始人",    "income_cny": "1-3亿 / 十亿级"},
    {"tier": 15, "label": "巨富",   "society": "国级/全球巨头",      "income_cny": ">3亿 / 百亿+"},
]


# ============================================================
# 二、骨架映射函数
# ============================================================

def _wealth_ceiling_to_tier_band(wealth_ceiling: str) -> tuple[int, int]:
    """D1 段派 wealth_ceiling 文本 → 15 层骨架区间。

    支持的 wealth_ceiling 标签（来自 engine/energy/zuogong.py 输出）：
    - 贫寒
    - 小康级·上/中/下
    - 中富级·上/中/下
    - 大富级·上/中/下
    - 巨富级
    """
    s = (wealth_ceiling or "").strip()
    if "巨富" in s:
        return (14, 15)
    if "大富" in s:
        if "上" in s:
            return (12, 13)
        if "下" in s:
            return (11, 12)
        return (11, 13)  # 中或未指定
    if "中富" in s:
        if "上" in s:
            return (10, 11)
        if "下" in s:
            return (8, 9)
        return (9, 10)   # 中或未指定
    if "小康" in s:
        if "上" in s:
            return (7, 8)
        if "下" in s:
            return (4, 5)
        return (5, 7)
    if "贫寒" in s or "贫困" in s:
        return (1, 3)
    # 兜底：未知 → 普工区间（不偏不倚）
    return (4, 6)


def _layer_count_modifier(layer_count: int) -> int:
    """做功层数对 mid 的微调。

    层数越高，实际兑现越接近结构上限。
    - 0-1 层：mid -1（兑现偏低）
    - 2 层：mid 不变
    - 3 层：mid +0
    - 4+ 层：mid 不变（已封顶）
    """
    if layer_count <= 1:
        return -1
    return 0


def _guanming_rank_to_max_tier(rank: Optional[int]) -> int:
    """D2 杨派 GuanmingQufa.rank (1-9) → 事业理论上限 tier (1-15)。

    1 化杀生枭 → L13（理论上限副部）
    2 化官生印 → L12
    3 合完整官 → L11
    4 财生官+合官 → L10
    5 食神制杀 → L11（技术官）
    6 比劫生食伤制杀 → L10
    7 劫财制财 → L9
    8 伤官伤尽 → L9
    9 制印得权 → L8
    """
    if rank is None:
        return 9  # 兜底中等
    table = {1: 13, 2: 12, 3: 11, 4: 10, 5: 11, 6: 10, 7: 9, 8: 9, 9: 8}
    return table.get(int(rank), 9)


# ============================================================
# 三、Wealth15Tier dataclass
# ============================================================

@dataclass
class TierBand:
    """五维各域的 (low, mid, high) 区间 + 中位说明 + 旁注。"""
    low: int                     # L1-L15
    mid: int
    high: int
    label: str                   # 中位标签，如 "中富下"
    society: str                 # 中位社会对应
    income_cny: str              # 中位年入参考
    rationale: str = ""          # 一句话推断理由

    def to_dict(self) -> dict[str, Any]:
        return {
            "low": self.low, "mid": self.mid, "high": self.high,
            "label": self.label, "society": self.society,
            "income_cny": self.income_cny, "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "TierBand":
        return cls(
            low=int(d["low"]), mid=int(d["mid"]), high=int(d["high"]),
            label=d.get("label", ""), society=d.get("society", ""),
            income_cny=d.get("income_cny", ""),
            rationale=d.get("rationale", ""),
        )


@dataclass
class Wealth15Tier:
    """五维 15 层综合定位结果。"""
    xueye: Optional[TierBand] = None      # 学业
    shiye: Optional[TierBand] = None      # 事业
    hunyin: Optional[TierBand] = None     # 婚姻（妻家档次）
    caifu: Optional[TierBand] = None      # 财富
    guanming: Optional[TierBand] = None   # 官命取法

    # 元信息
    tier_table: list[dict[str, Any]] = field(default_factory=lambda: list(TIER_TABLE))
    tier_disclaimer: str = (
        "15 层为 house-defined 标度（杨清娟盲派业内常用版本）。区间为结构性带宽，"
        "实际兑现需 known_facts 校验；命主可能因人生选择低于结构上限。"
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "xueye": self.xueye.to_dict() if self.xueye else None,
            "shiye": self.shiye.to_dict() if self.shiye else None,
            "hunyin": self.hunyin.to_dict() if self.hunyin else None,
            "caifu": self.caifu.to_dict() if self.caifu else None,
            "guanming": self.guanming.to_dict() if self.guanming else None,
            "tier_table": self.tier_table,
            "tier_disclaimer": self.tier_disclaimer,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Wealth15Tier":
        def _opt(key: str) -> Optional[TierBand]:
            v = d.get(key)
            return TierBand.from_dict(v) if v else None
        return cls(
            xueye=_opt("xueye"),
            shiye=_opt("shiye"),
            hunyin=_opt("hunyin"),
            caifu=_opt("caifu"),
            guanming=_opt("guanming"),
            tier_table=list(d.get("tier_table") or TIER_TABLE),
            tier_disclaimer=d.get("tier_disclaimer", ""),
        )


def _label_for(tier: int) -> tuple[str, str, str]:
    """tier → (label, society, income_cny)；越界 clamp 到 1-15。"""
    t = max(1, min(15, int(tier)))
    row = TIER_TABLE[t - 1]
    return row["label"], row["society"], row["income_cny"]


def _make_band(low: int, mid: int, high: int, rationale: str) -> TierBand:
    """构造一个 TierBand，自动 clamp 到 [1,15] 并填中位标签。

    这里承担最后一道数据护栏：无论上游传入顺序如何，输出都必须满足
    ``1 <= low <= mid <= high <= 15``，避免报告出现 ``L13-L12`` 之类
    反向区间，或中位超过理论上限。
    """
    low = max(1, min(15, int(low)))
    high = max(1, min(15, int(high)))
    if low > high:
        low, high = high, low
    mid = max(low, min(high, int(mid)))
    label, society, income = _label_for(mid)
    return TierBand(
        low=low, mid=mid, high=high,
        label=label, society=society, income_cny=income,
        rationale=rationale,
    )


def _cap_band(band: TierBand, high_cap: int, rationale_suffix: str) -> TierBand:
    """按领域现实口径收束上限，保留 ordered invariant。"""
    cap = max(1, min(15, int(high_cap)))
    if band.high <= cap:
        return band
    high = cap
    low = min(band.low, max(1, high - 1))
    mid = min(max(low, band.mid), high)
    rationale = f"{band.rationale} · {rationale_suffix}"
    return _make_band(low, mid, high, rationale)


# ============================================================
# 四、核心：compute_wealth_15tier
# ============================================================

def compute_wealth_15tier(energy: Any, picture: Any) -> Wealth15Tier:
    """从 D1 + D2 + D4（如有）综合计算 5 维 15 层区间。

    Args:
        energy: EnergyFindings（含 wealth_ceiling, layer_count）
        picture: PictureFindings（含 caifu, guanming + 可选 D4 boost）

    Returns:
        Wealth15Tier 含 5 域 TierBand。
    """
    wealth_ceiling = getattr(energy, "wealth_ceiling", "") or ""
    layer_count = int(getattr(energy, "layer_count", 0) or 0)
    caifu = getattr(picture, "caifu", None)
    guanming = getattr(picture, "guanming", None)

    base_low, base_high = _wealth_ceiling_to_tier_band(wealth_ceiling)
    base_mid = (base_low + base_high) // 2
    layer_mod = _layer_count_modifier(layer_count)

    # ------------------------------------------------------------
    # 财富域：D1 wealth_ceiling 直骨架 + 做功层数微调
    # ------------------------------------------------------------
    caifu_low = base_low
    caifu_mid = base_mid + layer_mod
    caifu_high = base_high
    caifu_band = _make_band(
        caifu_low, caifu_mid, caifu_high,
        rationale=(
            f"D1 段派 wealth_ceiling={wealth_ceiling} (映射 L{base_low}-L{base_high})"
            f" · 做功层数={layer_count} (微调 {layer_mod:+d})"
        ),
    )

    # ------------------------------------------------------------
    # 事业域：D2 guanming 上限 + 做功层数兑现
    # ------------------------------------------------------------
    g_max = _guanming_rank_to_max_tier(getattr(guanming, "rank", None))
    g_type = getattr(guanming, "type", "?") if guanming else "?"
    # 实际兑现：结构上限 - (4 - layer_count，但封 0)。
    # 注意事业域的理论上限来自官命取法，不应被财富骨架 base_low 反向抬高；
    # 否则在 D1=巨富、D2=化官生印 时会出现 L13-L12 / mid > high。
    realize_gap = max(0, 4 - layer_count)
    shiye_high = g_max
    shiye_mid = max(1, min(shiye_high, g_max - realize_gap))
    shiye_low = max(1, shiye_mid - 2)
    shiye_band = _make_band(
        shiye_low, shiye_mid, shiye_high,
        rationale=(
            f"D2 杨派官命取法={g_type} (rank={getattr(guanming, 'rank', '?')}) "
            f"理论上限 L{g_max} · 做功 {layer_count} 层兑现差 {realize_gap}"
        ),
    )

    # ------------------------------------------------------------
    # 学业域：D1 骨架 + 学业辅佐神煞 boost
    # ------------------------------------------------------------
    # 试图从 picture 的 evidence 提取学业 boost 信号
    edu_boost = 0
    if hasattr(picture, "evidence"):
        for ev in (picture.evidence or []):
            rid = (getattr(ev, "rule_id", "") or "")
            if "词馆" in rid or "学堂" in rid or "天乙" in rid or "GP-CG" in rid:
                edu_boost += 1
    edu_lift = 1 if edu_boost >= 2 else 0
    xueye_low = max(1, base_low - 1)
    xueye_mid = base_mid + edu_lift
    xueye_high = min(15, base_high + edu_lift)
    xueye_band = _make_band(
        xueye_low, xueye_mid, xueye_high,
        rationale=(
            f"D1 骨架 L{base_low}-L{base_high} · 学业辅佐神煞 {edu_boost} 项 → "
            f"提 {edu_lift} 档"
        ),
    )
    xueye_band = _cap_band(
        xueye_band,
        8,
        "学业域不直接继承财富/官命上限，按学历资质现实口径封顶 L8",
    )

    # ------------------------------------------------------------
    # 婚姻域（妻家档次）：以 D2.caifu 镜像 + 高派婚姻 net boost
    # ------------------------------------------------------------
    # 婚姻看妻家档次，与命主财富档次正相关但偏低 1 档
    hun_low = max(1, base_low - 1)
    hun_high = base_high
    hun_mid = max(hun_low, base_mid - 1 + layer_mod)
    hunyin_band = _make_band(
        hun_low, hun_mid, hun_high,
        rationale=(
            f"D2 配偶宫+高派金舆等旁证 → 妻家档次约 L{hun_low}-L{hun_high}, "
            f"中位 L{hun_mid}（参考命主财富档次镜像偏低 1 档）"
        ),
    )
    hunyin_band = _cap_band(
        hunyin_band,
        9,
        "婚姻/妻家档次不按命主财富结构直推巨富，现实口径封顶 L9",
    )

    # ------------------------------------------------------------
    # 官命域：guanming.rank 1-9 直接转 tier
    # ------------------------------------------------------------
    if guanming is not None:
        gm_high = g_max
        gm_low = max(1, g_max - 4)
        gm_mid = max(gm_low, g_max - realize_gap)
        gm_band = _make_band(
            gm_low, gm_mid, gm_high,
            rationale=(
                f"杨派官命第 {guanming.rank} 取={g_type} → 理论上限 L{g_max}, "
                f"做功 {layer_count} 层兑现 L{gm_mid}"
            ),
        )
    else:
        gm_band = None

    caifu_band = _cap_band(
        caifu_band,
        12,
        "财富域以结构潜力作上沿但报告定位采用保守现实口径，封顶 L12",
    )

    return Wealth15Tier(
        xueye=xueye_band,
        shiye=shiye_band,
        hunyin=hunyin_band,
        caifu=caifu_band,
        guanming=gm_band,
    )


# ============================================================
# 五、smoke
# ============================================================

def _smoke() -> None:
    """构造伪 energy + picture，验证映射。"""
    class FakeCaifu: rank = 5; type = "旺官"
    class FakeGuanming: rank = 1; type = "化杀生枭"
    class FakeEvidence:
        def __init__(self, rid): self.rule_id = rid
    class FakePicture:
        caifu = FakeCaifu()
        guanming = FakeGuanming()
        evidence = [FakeEvidence("GP-CG-词馆"), FakeEvidence("GP-TY-天乙贵人")]
    class FakeEnergy:
        wealth_ceiling = "中富级·中"
        layer_count = 2

    w = compute_wealth_15tier(FakeEnergy(), FakePicture())
    s = json.dumps(w.to_dict(), ensure_ascii=False, indent=2)
    print(s[:500])
    print("...")
    assert w.caifu is not None and 7 <= w.caifu.mid <= 10
    assert w.shiye is not None and w.shiye.high == 13  # 化杀生枭
    assert w.xueye is not None
    assert w.guanming is not None and w.guanming.high == 13
    # round-trip
    w2 = Wealth15Tier.from_dict(w.to_dict())
    assert w2.to_dict() == w.to_dict()
    print("[OK] wealth_15tier smoke 通过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
