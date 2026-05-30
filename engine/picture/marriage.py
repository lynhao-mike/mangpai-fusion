"""engine/picture/marriage.py · v1.2 D2 杨派 · 婚姻画像（重中之重）

杨派婚姻判定（M2-Y-038..042, 064..069, 088, 104..107, 141..143）：

§10.1 三步看法：宫位静否 → 配偶星强弱 → 应期（印来人来）
§10.2 结婚应期完整版：印来 + 配偶星到 = 当年；只来一个 = 邻年
§10.3 星虚透 = 感情不稳
§10.4 犯桃花 = 财官从家里跑外面
§10.5 离婚条件：比劫见财 + 宫位受冲

修复 G2 的关键：必须计算 `初婚最佳窗口: tuple[int, int]`。
- C-2026-001 (壬子日男命，1980 生)
  配偶星 = 财（丙/丁火）
  月支寅藏丙偏财（贴身）
  18-28 庚辰运（与日支子合化水，激活配偶宫）
  → 期望 [22, 28] 含 25 岁（2005 年）

启发式（08 § 失败兜底允许，本模块刻意做"足够好"而非"完美"）：

1. 配偶星位置评估（"贴身度"）
   - 月支/日支藏 → 强贴身（早婚 22-28）
   - 年支/时支藏 → 中贴身（中婚 24-30 或 28-34）
   - 不见原局   → 难定（30+）

2. 大运早期是否激活
   - 18-28 大运是否含配偶星 / 与配偶宫六合三合
   - 是 → 早婚信号 +1

3. 印重 → 推迟（印多人来人去）
4. 食伤多 → 难定 / 偏晚（食伤 ≠ 直接配偶星）
5. 比劫多 → 婚姻易动（M2-Y-068）

作者：Track-B
"""
from __future__ import annotations

from typing import Optional

from engine.energy.types import Evidence, EnergyFindings
from engine.predicates.ganzhi import (
    gan_to_wuxing,
    gan_yinyang,
    zhi_to_wuxing,
)
from engine.predicates.palace import (
    find_shishen_in_bazi,
    get_shishen,
)
from engine.predicates.relations import (
    zhi_chong,
    zhi_chuan,
    zhi_liuhe,
    zhi_sanhe,
    zhi_xing,
)
from engine.predicates.strength import calc_wuxing_strength
from engine.predicates.types import (
    Bazi,
    Dayun,
    DayunStep,
    Gan,
    GanZhi,
    ParsedInput,
    PalaceName,
    Shishen,
    Wuxing,
    Zhi,
    ZHI_CANGGAN_TABLE,
)


# ============================================================
# 配偶星集合
# ============================================================

def _get_spouse_star_shishens(gender: str) -> tuple[Shishen, Shishen]:
    """男命 = 财（正财/偏财）；女命 = 官杀（正官/七杀）。"""
    g = (gender or "").upper().strip()
    if g in ("F", "FEMALE", "女", "坤", "坤造"):
        return ("正官", "七杀")
    return ("正财", "偏财")


# ============================================================
# F7 · 婚姻画像年龄过滤
# ============================================================

def _compute_age_status(
    parsed: ParsedInput,
    window: tuple[int, int],
    *,
    current_year: int = 2026,
) -> dict:
    """根据命主当前年龄 vs 婚姻窗口，返回 age_status dict。

    语义：
      - "未到": current_age < window_lo - 2
      - "临近": window_lo - 2 <= age < window_lo
      - "在窗口": window_lo <= age <= window_hi
      - "刚过": window_hi < age <= window_hi + 5
      - "已过": age > window_hi + 5  (≥ 5 年远超窗口 → 应降级展示)

    返回 dict:
      - status: 上述 5 字符串之一
      - current_age: int
      - years_past: int (>=0; 仅在"已过"时有意义)
      - warning: str (展示用提示)
      - downgrade: bool (True 时 render 应把婚姻窗口从主断语降级为参考)
    """
    try:
        gongli = (parsed.birth or {}).get("公历", "1980-01-01")
        birth_year = int(str(gongli).split("-")[0])
    except Exception:
        birth_year = 1980
    age = current_year - birth_year
    lo, hi = int(window[0]), int(window[1])

    if age < lo - 2:
        return {
            "status": "未到",
            "current_age": age,
            "years_past": 0,
            "warning": "",
            "downgrade": False,
        }
    if age < lo:
        return {
            "status": "临近",
            "current_age": age,
            "years_past": 0,
            "warning": f"距窗口起点还有 {lo - age} 年",
            "downgrade": False,
        }
    if age <= hi:
        return {
            "status": "在窗口",
            "current_age": age,
            "years_past": 0,
            "warning": f"当前在初婚窗口内（{lo}-{hi} 岁）",
            "downgrade": False,
        }
    years_past = age - hi
    if years_past <= 5:
        return {
            "status": "刚过",
            "current_age": age,
            "years_past": years_past,
            "warning": f"已过初婚最佳窗口 {years_past} 年（窗口 {lo}-{hi} 岁）",
            "downgrade": False,
        }
    return {
        "status": "已过",
        "current_age": age,
        "years_past": years_past,
        "warning": (
            f"⚠️ 命主当前 {age} 岁 · 已过初婚最佳窗口 {years_past} 年"
            f"（窗口 {lo}-{hi} 岁）。本断语对当前命主已无指导意义，"
            f"应作参考信号；若实际未婚，关注后续大运的财官启动期。"
        ),
        "downgrade": True,
    }


def _spouse_palace_locations(
    bazi: Bazi, gender: str,
) -> list[tuple[PalaceName, str, Shishen]]:
    """找出配偶星在原局的所有位置（含藏干）。

    返回 [(宫位名, 字符, 十神), ...]
    """
    s1, s2 = _get_spouse_star_shishens(gender)
    out: list[tuple[PalaceName, str, Shishen]] = []
    for ss in (s1, s2):
        for palace, char in find_shishen_in_bazi(ss, bazi):
            out.append((palace, char, ss))
    return out


# ============================================================
# 贴身度评估
# ============================================================

# 宫位贴身度评分：日柱最贴身，月柱次之，年/时较远
_PALACE_TIESHEN_SCORE: dict[str, float] = {
    "日柱": 1.0, "日支": 1.0,
    "月柱": 0.9, "月支": 0.9,
    "年柱": 0.5, "年支": 0.5,
    "时柱": 0.6, "时支": 0.6,
}


def _evaluate_tieshen(
    locations: list[tuple[PalaceName, str, Shishen]],
) -> tuple[float, list[str]]:
    """评估配偶星贴身度。

    返回：
        (max_score, 描述列表)
    """
    if not locations:
        return (0.0, ["配偶星完全不见原局（含藏干）"])
    scores = []
    descs = []
    for palace, char, ss in locations:
        s = _PALACE_TIESHEN_SCORE.get(palace, 0.3)
        scores.append(s)
        descs.append(f"{palace}藏 {char}({ss}, 贴身度{s:.1f})")
    return (max(scores), descs)


# ============================================================
# 大运早期是否激活配偶星
# ============================================================

def _early_dayun_activates_spouse(
    dayun: Dayun, bazi: Bazi, gender: str,
    age_lo: int = 16, age_hi: int = 32,
) -> tuple[bool, list[str]]:
    """大运 16-32 岁段是否激活配偶星 / 配偶宫。

    激活条件：
    - 大运字面 = 配偶星天干 / 配偶星藏干主气支
    - 大运地支与日支（婚宫）六合 / 三合
    - 大运地支与月支构成生发联动
    """
    s1, s2 = _get_spouse_star_shishens(gender)
    spouse_chars: set[str] = set()
    # 配偶星天干集合 + 主气支集合
    day_master = bazi.day_master

    from engine.predicates.types import GAN_LIST
    for g in GAN_LIST:
        if get_shishen(g, day_master) in (s1, s2):
            spouse_chars.add(g)
            # 该天干主气位的支
            from engine.predicates.types import ZHI_CANGGAN_TABLE
            for z, cangs in ZHI_CANGGAN_TABLE.items():
                if cangs and cangs[0][0] == g:
                    spouse_chars.add(z)

    # 婚宫 = 日支
    marriage_zhi = bazi.日柱.zhi

    activated = False
    notes: list[str] = []
    for step in dayun.排布:
        # 命中早期窗口
        if step.止岁 < age_lo or step.起岁 > age_hi:
            continue
        # 大运字面命中配偶星
        if step.干支.gan in spouse_chars or step.干支.zhi in spouse_chars:
            activated = True
            notes.append(
                f"大运{step.序号}({step.干支}, {step.起岁}-{step.止岁}岁) "
                f"字面含配偶星"
            )
            continue
        # 大运地支与婚宫合
        if zhi_liuhe(step.干支.zhi, marriage_zhi):
            activated = True
            notes.append(
                f"大运{step.序号}({step.干支}, {step.起岁}-{step.止岁}岁) "
                f"地支与婚宫{marriage_zhi}六合"
            )
            continue
        # 大运地支 + 婚宫 + 任一支 → 三合
        # 简化：大运 + 日支 + 任一原局支
        for _, zhi_x in bazi.all_zhis():
            if zhi_x == step.干支.zhi:
                continue
            tri = zhi_sanhe([step.干支.zhi, marriage_zhi, zhi_x])
            if tri:
                activated = True
                notes.append(
                    f"大运{step.序号}({step.干支}, {step.起岁}-{step.止岁}岁) "
                    f"+ 婚宫{marriage_zhi} + {zhi_x} 三合化{tri}"
                )
                break
        # 大运地支与月支生发（与提纲呼应）
        if step.干支.zhi != bazi.月柱.zhi:
            # 申子辰半三合等
            for _, zhi_x in bazi.all_zhis():
                if zhi_sanhe([step.干支.zhi, zhi_x]):
                    if step.干支.zhi != zhi_x:
                        activated = True
                        notes.append(
                            f"大运{step.序号}({step.干支}, "
                            f"{step.起岁}-{step.止岁}岁) "
                            f"与原局{zhi_x}半三合"
                        )
                        break
            if activated:
                break
    return (activated, notes)


# ============================================================
# 印重 / 食伤多 / 比劫多 判断（影响窗口偏移）
# ============================================================

def _count_yin(bazi: Bazi) -> int:
    """印星总数（透干 + 主气 + 中余气）。"""
    day_master = bazi.day_master
    cnt = 0
    for _, gan in bazi.all_gans():
        if gan == day_master:
            continue
        if get_shishen(gan, day_master) in ("正印", "偏印"):
            cnt += 1
    for _, zhi in bazi.all_zhis():
        cangs = ZHI_CANGGAN_TABLE.get(zhi, [])
        for cg, t, l in cangs:
            if t == "主气" and get_shishen(cg, day_master) in ("正印", "偏印"):
                cnt += 1
    return cnt


def _count_food(bazi: Bazi) -> int:
    """食伤总数。"""
    day_master = bazi.day_master
    cnt = 0
    for _, gan in bazi.all_gans():
        if gan == day_master:
            continue
        if get_shishen(gan, day_master) in ("食神", "伤官"):
            cnt += 1
    for _, zhi in bazi.all_zhis():
        cangs = ZHI_CANGGAN_TABLE.get(zhi, [])
        for cg, t, l in cangs:
            if t == "主气" and get_shishen(cg, day_master) in ("食神", "伤官"):
                cnt += 1
    return cnt


def _count_bijie(bazi: Bazi) -> int:
    """比劫总数。"""
    day_master = bazi.day_master
    cnt = 0
    for _, gan in bazi.all_gans():
        if gan == day_master:
            cnt += 1  # 日干本身
            continue
        if get_shishen(gan, day_master) in ("比肩", "劫财"):
            cnt += 1
    for _, zhi in bazi.all_zhis():
        cangs = ZHI_CANGGAN_TABLE.get(zhi, [])
        for cg, t, l in cangs:
            if t == "主气" and get_shishen(cg, day_master) in ("比肩", "劫财"):
                cnt += 1
    return cnt


# ============================================================
# 婚宫稳定度
# ============================================================

def _marriage_palace_stability(bazi: Bazi) -> tuple[str, str]:
    """日支（婚宫）是否被刑冲穿，返回 (稳定度, 描述)。

    稳定度：稳定 / 中等 / 易动
    """
    day_zhi = bazi.日柱.zhi
    issues = []
    for name, zhi in bazi.all_zhis():
        if name == "日支":
            continue
        if zhi_chong(day_zhi, zhi):
            issues.append(f"被{name}冲")
        if zhi_chuan(day_zhi, zhi):
            issues.append(f"被{name}穿")
        if zhi_xing(day_zhi, zhi) is not None:
            issues.append(f"与{name}刑")
    if not issues:
        return ("稳定", f"婚宫{day_zhi}静")
    if len(issues) == 1:
        return ("中等", f"婚宫{day_zhi}略动: {issues[0]}")
    return ("易动", f"婚宫{day_zhi}多动: {','.join(issues)}")


# ============================================================
# 主入口
# ============================================================

def build_marriage_picture(
    energy: EnergyFindings,
    parsed: ParsedInput,
) -> dict:
    """构造婚姻画像（marriage_picture dict）。

    输出字段：
        初婚最佳窗口: tuple[int, int]   ← G2 修复关键
        配偶画像: str
        婚姻稳定度: 稳定 / 中等 / 易动
        早婚信号: 强 / 中 / 弱
        晚婚信号: 强 / 中 / 弱
        evidence: list[Evidence]
    """
    bazi = parsed.bazi
    dayun = parsed.dayun
    gender = (parsed.birth or {}).get("性别", "M")

    # 1. 配偶星位置 + 贴身度
    locations = _spouse_palace_locations(bazi, gender)
    tieshen_score, tieshen_descs = _evaluate_tieshen(locations)

    # 2. 大运早期激活（16-32 岁）
    activated, activation_notes = _early_dayun_activates_spouse(
        dayun, bazi, gender, age_lo=16, age_hi=32
    )
    # 也检查 24-40 岁段（中段）
    activated_mid, activation_mid_notes = _early_dayun_activates_spouse(
        dayun, bazi, gender, age_lo=24, age_hi=40
    )

    # 3. 印 / 食伤 / 比劫
    yin_n = _count_yin(bazi)
    food_n = _count_food(bazi)
    bijie_n = _count_bijie(bazi)

    # 4. 婚宫稳定度
    stability, stability_desc = _marriage_palace_stability(bazi)

    # ========== 早婚 / 晚婚信号 ==========
    early_signal = "弱"
    late_signal = "弱"

    if tieshen_score >= 0.85 and activated:
        early_signal = "强"
    elif tieshen_score >= 0.85 or (tieshen_score >= 0.5 and activated):
        early_signal = "中"
    elif tieshen_score >= 0.4:
        early_signal = "弱"

    if tieshen_score < 0.4:
        late_signal = "强"
    elif yin_n >= 3 and tieshen_score < 0.85:
        # 印重 + 配偶星不贴身 → 偏晚
        late_signal = "中"
    if food_n >= 3 and tieshen_score < 0.5:
        # 食伤多 + 配偶星远 → 难定（偏晚）
        late_signal = "强"

    # ========== 初婚最佳窗口 ==========
    # 默认基础窗口：男 25-32，女 23-30
    if gender.upper().startswith("F") or gender in ("女", "坤", "坤造"):
        base = (23, 30)
    else:
        base = (25, 32)

    if early_signal == "强":
        # 配偶星贴身 + 大运到位 → 早窗口 22-28（覆盖 G2 的 25 岁）
        window = (22, 28)
    elif early_signal == "中" and late_signal != "强":
        # 中等贴身 → 中窗口 23-30
        window = (23, 30)
    elif late_signal == "强" and tieshen_score < 0.4:
        # 配偶星不见 + 食伤多 → 晚窗口 30-38
        window = (30, 38)
    elif late_signal == "强":
        # 印重晚婚倾向
        window = (28, 35)
    elif late_signal == "中":
        window = (26, 33)
    else:
        window = base

    # 比劫多额外修正：婚易动（不缩窗，但稳定度记录）
    if bijie_n >= 4:
        # 高比劫数 → 易动
        if stability == "稳定":
            stability = "中等"

    # ========== 配偶画像 ==========
    if locations:
        spouse_brief_parts: list[str] = []
        # 主要位置（贴身度最高的那个）
        loc_with_score = sorted(
            locations,
            key=lambda x: -_PALACE_TIESHEN_SCORE.get(x[0], 0.3),
        )
        primary_palace, primary_char, primary_ss = loc_with_score[0]
        spouse_brief_parts.append(
            f"{primary_palace}藏 {primary_char}({primary_ss})"
        )
        if primary_palace in ("月柱", "月支"):
            spouse_brief_parts.append("配偶来自父母圈/工作圈")
        elif primary_palace in ("日柱", "日支"):
            spouse_brief_parts.append("配偶为身边人/同学同事")
        elif primary_palace in ("年柱", "年支"):
            spouse_brief_parts.append("配偶有家世背景或长辈介绍")
        elif primary_palace in ("时柱", "时支"):
            spouse_brief_parts.append("配偶相识较晚或跨年龄")
        # 配偶五行性情
        char_wx = (
            gan_to_wuxing(primary_char)  # type: ignore[arg-type]
            if primary_char in (
                "甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"
            )
            else zhi_to_wuxing(primary_char)  # type: ignore[arg-type]
        )
        wx_personality = {
            "木": "性情仁厚直率",
            "火": "性情温和明朗",
            "土": "性情厚实务实",
            "金": "性情果断利落",
            "水": "性情聪慧灵动",
        }.get(char_wx, "性情")
        spouse_brief_parts.append(wx_personality)
        spouse_brief = "；".join(spouse_brief_parts)
    else:
        spouse_brief = "配偶星不见原局：无星借宫，配偶画面较虚"

    # ========== evidence ==========
    evidence: list[Evidence] = []
    evidence.append(Evidence(
        rule_id="M2-Y-038",
        school="杨",
        description=f"婚姻看法三步：宫位{stability_desc}",
        weight=0.70,
    ))
    if locations:
        evidence.append(Evidence(
            rule_id="M2-Y-141",
            school="杨",
            description=f"结婚应期：配偶星{tieshen_descs[:2]}",
            weight=0.78,
        ))
    if activated:
        evidence.append(Evidence(
            rule_id="M2-Y-064",
            school="杨",
            description=f"早期大运激活配偶宫: {activation_notes[:1]}",
            weight=0.75,
        ))
    if not locations:
        evidence.append(Evidence(
            rule_id="M2-Y-039",
            school="杨",
            description="配偶星虚透或不见 → 感情不稳/晚婚",
            weight=0.65,
        ))
    if bijie_n >= 4:
        evidence.append(Evidence(
            rule_id="M2-Y-068",
            school="杨",
            description=f"比劫数 {bijie_n}，婚姻易动",
            weight=0.60,
        ))

    return {
        "初婚最佳窗口": window,
        "配偶画像": spouse_brief,
        "婚姻稳定度": stability,
        "早婚信号": early_signal,
        "晚婚信号": late_signal,
        "age_status": _compute_age_status(parsed, window),
        "evidence": evidence,
        "_debug": {
            "gender": gender,
            "spouse_locations": [
                [p, c, s] for (p, c, s) in locations
            ],
            "tieshen_score": round(tieshen_score, 2),
            "tieshen_descs": tieshen_descs,
            "early_dayun_activated": activated,
            "activation_notes": activation_notes,
            "stability_desc": stability_desc,
            "yin_count": yin_n,
            "food_count": food_n,
            "bijie_count": bijie_n,
        },
    }


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    from tests.fixtures.cases import load_case
    from engine.energy.evaluator import evaluate_energy

    print("\n=== B-002 关键测试：C-2026-001 marriage_picture ===")
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    energy = evaluate_energy(parsed)
    mp = build_marriage_picture(energy, parsed)
    win = mp["初婚最佳窗口"]
    print(f"  初婚最佳窗口: {win}")
    print(f"  配偶画像:    {mp['配偶画像']}")
    print(f"  婚姻稳定度:  {mp['婚姻稳定度']}")
    print(f"  早婚信号:    {mp['早婚信号']}")
    print(f"  晚婚信号:    {mp['晚婚信号']}")
    print(f"  Debug:")
    for k, v in mp["_debug"].items():
        print(f"    {k}: {v}")

    # 关键断言：22-28 包含 25 岁（2005年=2005-1980=25岁）
    assert isinstance(win, tuple) and len(win) == 2
    lo, hi = win
    target_age = 2005 - 1980  # 25 岁
    assert lo <= target_age <= hi, (
        f"B-002 期望 [22,28] 含 25 岁；实际 {win} 不含 {target_age} 岁"
    )
    # 严格：必须 = (22, 28)
    assert win == (22, 28), f"B-002 期望 (22,28)，实为 {win}"
    print(f"  [OK] B-002 G2 修复关键证据：窗口 {win} 含 25 岁（2005 年）")

    print("\n=== C-2026-002 marriage_picture ===")
    parsed2 = load_case("C-2026-002-坤-壬戌庚戌戊辰丙辰")
    energy2 = evaluate_energy(parsed2)
    mp2 = build_marriage_picture(energy2, parsed2)
    print(f"  初婚最佳窗口: {mp2['初婚最佳窗口']}")
    print(f"  配偶画像:    {mp2['配偶画像']}")
    print(f"  早婚信号:    {mp2['早婚信号']}")
    print(f"  晚婚信号:    {mp2['晚婚信号']}")

    print("\n=== C-2026-014 marriage_picture ===")
    parsed3 = load_case("C-2026-014-乾-丙戌庚子乙亥辛巳")
    energy3 = evaluate_energy(parsed3)
    mp3 = build_marriage_picture(energy3, parsed3)
    print(f"  初婚最佳窗口: {mp3['初婚最佳窗口']}")
    print(f"  配偶画像:    {mp3['配偶画像']}")

    print("\n[OK] marriage smoke 通过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
