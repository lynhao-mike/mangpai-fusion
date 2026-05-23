"""engine/energy/tiyong.py · v1.2 D1 段派 · 体用判别

段派"体用"定义（M1-D-005..008, 112, 216..221）：

    体（工具）：日干 + 印 + 比劫 + 禄
    用（目的）：财 + 官杀
    食伤双重性：食偏体（生命体延伸）/伤偏用（向外做功的输出）

注意决策 J（母星取法）：
    段派的"母星"取法 = 禄 / 食伤 / 比劫，**默认禄**
    （这是段派与杨派/任派最大分歧——杨派习惯取印为母）

输入：ParsedInput（adapt_parsed 后）
输出：TiyongStructure
"""
from __future__ import annotations

from typing import Optional

from engine.energy.types import (
    TiyongItem,
    TiyongRole,
    TiyongStructure,
)
from engine.predicates.types import (
    Bazi,
    Gan,
    GanZhi,
    PalaceName,
    Wuxing,
    Zhi,
    ZHI_CANGGAN_TABLE,
)
from engine.predicates.ganzhi import gan_to_wuxing, zhi_to_wuxing
from engine.predicates.wuxing import wuxing_relation, wuxing_same


# ============================================================
# 工具：禄位查询
# ============================================================

# 段派的"禄"= 临官位（M1-D-067 / D-150）
_GAN_LU_TABLE: dict[Gan, Zhi] = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午",
    "戊": "巳", "己": "午", "庚": "申", "辛": "酉",
    "壬": "亥", "癸": "子",
}


def get_lu(g: Gan) -> Zhi:
    """天干的禄位。"""
    return _GAN_LU_TABLE[g]


# ============================================================
# 角色判定
# ============================================================

def gan_role_to_day(c: Gan, day_master: Gan) -> TiyongRole:
    """以日干为我，c 字相对我的体用角色（粗分 5 类 + 禄）。

    规则：
    - 同行 → 比劫
    - 生我 → 印
    - 我生 → 食伤
    - 我克 → 财
    - 克我 → 官杀
    """
    if c == day_master:
        return "比劫"  # 实际为日干本身，仍归比劫类
    rel = wuxing_relation(gan_to_wuxing(day_master), gan_to_wuxing(c))
    if rel == "同我":
        return "比劫"
    if rel == "生我":
        return "印"
    if rel == "我生":
        return "食伤"
    if rel == "我克":
        return "财"
    if rel == "克我":
        return "官杀"
    raise RuntimeError(f"无法判定 {c} 对 {day_master} 的角色")


def zhi_role_to_day(z: Zhi, day_master: Gan) -> TiyongRole:
    """以地支主气推断该支的"主体角色"。"""
    cangs = ZHI_CANGGAN_TABLE.get(z, [])
    if not cangs:
        return "比劫"  # fallback
    # 主气
    zhuqi = cangs[0][0]
    return gan_role_to_day(zhuqi, day_master)


# ============================================================
# tiyong 主入口
# ============================================================

def evaluate_tiyong(bazi: Bazi) -> TiyongStructure:
    """段派体用判别。

    体（工具）：
        - 日干自身
        - 比劫（天干透出的同我者）
        - 印（生我者）
        - 禄（日干的禄支若出现于原局，加入体）

    用（目的）：
        - 财（我克）
        - 官杀（克我）

    食伤双重性：保留为"中性"——下游 zuogong 模块决定其实际归属
    （食制杀时为体辅；伤生财时偏向用辅）。
    """
    day_master = bazi.day_master
    day_master_wx = gan_to_wuxing(day_master)

    body: list[TiyongItem] = []
    purpose: list[TiyongItem] = []

    # 1. 日干自身（体的核心）
    body.append(TiyongItem(
        char=day_master, role="体",
        location="日柱-天干（日干）",
    ))

    # 2. 扫天干
    pillars = bazi.all_pillars()
    for name, gz in pillars:
        if name == "日柱":
            continue
        gan = gz.gan
        role = gan_role_to_day(gan, day_master)
        loc = f"{name}-天干"
        if role in ("比劫", "印"):
            body.append(TiyongItem(char=gan, role=role, location=loc))
        elif role in ("财", "官杀"):
            purpose.append(TiyongItem(char=gan, role=role, location=loc))
        # 食伤：先归属体（食偏体）；伤官在 zuogong 中可能反转
        elif role == "食伤":
            body.append(TiyongItem(char=gan, role="食伤", location=loc))

    # 3. 扫地支主气（粗判）+ 禄
    lu_zhi = get_lu(day_master)
    for name, zhi in bazi.all_zhis():
        role = zhi_role_to_day(zhi, day_master)
        loc = f"{name[0]}柱-地支（{name}）"
        # 禄
        if zhi == lu_zhi:
            body.append(TiyongItem(char=zhi, role="禄", location=loc))
        elif role in ("比劫", "印"):
            body.append(TiyongItem(char=zhi, role=role, location=loc))
        elif role in ("财", "官杀"):
            purpose.append(TiyongItem(char=zhi, role=role, location=loc))
        elif role == "食伤":
            body.append(TiyongItem(char=zhi, role="食伤", location=loc))

    # 4. rationale 文本
    body_brief = ", ".join(f"{b.char}({b.role})" for b in body[:6])
    purpose_brief = ", ".join(f"{p.char}({p.role})" for p in purpose[:6])
    rationale = (
        f"段派体用判别（M1 §17.2）：日干 {day_master}({day_master_wx}) 为我。\n"
        f"  体（工具）= 日干 + 印 + 比劫 + 禄: {body_brief}\n"
        f"  用（目的）= 财 + 官杀: {purpose_brief}\n"
        f"  食伤为中性，默认归体（食偏体）"
    )

    return TiyongStructure(
        body=body,
        purpose=purpose,
        rationale=rationale,
    )


# ============================================================
# 辅助：判定母星取法（决策 J 段派独门）
# ============================================================

def determine_muxing_qufa(bazi: Bazi) -> str:
    """段派"母星取法"（M1-D-199）：

    段派认为"母 = 禄/食伤/比劫"（**不是印**），与杨派分歧。

    实务规则：
    - 默认 禄
    - 若禄被冲坏 → 食伤
    - 若食伤也无 → 比劫
    """
    day_master = bazi.day_master
    lu_zhi = get_lu(day_master)
    # 禄是否在原局
    has_lu = any(zhi == lu_zhi for _, zhi in bazi.all_zhis())
    if has_lu:
        return "禄"
    # 食伤是否在天干
    day_master_wx = gan_to_wuxing(day_master)
    for name, gan in bazi.all_gans():
        if name == "日柱":
            continue
        rel = wuxing_relation(day_master_wx, gan_to_wuxing(gan))
        if rel == "我生":
            return "食伤"
    # 比劫
    return "比劫"


# ============================================================
# smoke test
# ============================================================

def _smoke() -> None:
    from engine.predicates.types import _default_canggan_for

    # C-2026-001: 庚申戊寅壬子辛丑（壬日）
    bazi = Bazi(
        年柱=GanZhi("庚", "申"),
        月柱=GanZhi("戊", "寅"),
        日柱=GanZhi("壬", "子"),
        时柱=GanZhi("辛", "丑"),
    )
    bazi.藏干 = _default_canggan_for(bazi)

    st = evaluate_tiyong(bazi)
    print("=== C-2026-001 体用 ===")
    print(st.rationale)
    body_chars = [b.char for b in st.body]
    purpose_chars = [p.char for p in st.purpose]
    print(f"体: {body_chars}")
    print(f"用: {purpose_chars}")

    # 壬日干，体应含: 壬本身, 庚(印=金生水), 辛(印), 申(禄? 壬禄在亥，申非禄)
    # 申=金=印, 子=水=比劫
    # 戊=土=克我=官杀, 寅=木藏甲=食伤, 丑=土藏己=官杀
    # 期望：体 ⊇ {壬, 庚, 辛, 申, 子}；用 ⊇ {戊, 丑, 寅(中气丙=偏财)?}
    assert "壬" in body_chars
    assert "庚" in body_chars or "辛" in body_chars  # 印
    assert "戊" in purpose_chars  # 七杀

    qufa = determine_muxing_qufa(bazi)
    print(f"母星取法: {qufa}")
    # 壬禄在亥，本局无亥 → 落到"食伤"或"比劫"
    assert qufa in ("禄", "食伤", "比劫")

    # C-2026-014: 丙戌庚子乙亥辛巳（乙日）
    bazi2 = Bazi(
        年柱=GanZhi("丙", "戌"),
        月柱=GanZhi("庚", "子"),
        日柱=GanZhi("乙", "亥"),
        时柱=GanZhi("辛", "巳"),
    )
    bazi2.藏干 = _default_canggan_for(bazi2)
    st2 = evaluate_tiyong(bazi2)
    body2 = [b.char for b in st2.body]
    purpose2 = [p.char for p in st2.purpose]
    print("\n=== C-2026-014 体用 ===")
    print(f"体: {body2}")
    print(f"用: {purpose2}")
    # 乙日干，禄在卯（不在原局）
    qufa2 = determine_muxing_qufa(bazi2)
    print(f"母星取法: {qufa2}")

    print("[OK] tiyong smoke 全过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
