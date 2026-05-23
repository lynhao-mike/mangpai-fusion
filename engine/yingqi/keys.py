"""engine/yingqi/keys.py · v1.2 D3 任派 · domain → 关键字映射

严格按 04-gate-protocol.md § 三 (3.1 关键字映射表) 实现。

3 个对外 API（与契约 04 一致）：
    get_primary_keys(domain, bazi, energy, *, gender=None, sub_domain=None) -> list[str]
    get_secondary_keys(domain, bazi, energy, *, gender=None, sub_domain=None) -> list[str]
    get_required_dayun_chars(domain, energy, parsed, *, sub_domain=None) -> list[str]

辅助：
    infer_sub_domain(candidate_event) -> Optional[str]
        从 candidate_event 文字中推断 六亲 子域（父 / 母 / 兄弟 / 子女 / 配偶）

设计原则：
- 关键字 = 天干字 + 地支主气支字（Bazi.all_zhis 涉及的支位 → "字"）
- 关键字字符化（list[str]）：上层 layer1_check 用 in 检查
- 性别敏感的（婚姻、六亲-配偶、六亲-子女）从 parsed.birth["性别"] 取

作者：Track-C
"""
from __future__ import annotations

from typing import Optional

from engine.energy.types import EnergyFindings
from engine.predicates.ganzhi import gan_yinyang, gan_to_wuxing, zhi_to_wuxing
from engine.predicates.palace import get_shishen
from engine.predicates.types import (
    Bazi,
    Gan,
    GAN_LIST,
    ParsedInput,
    Shishen,
    ZHI_CANGGAN_TABLE,
    ZHI_LIST,
    Zhi,
)


# ============================================================
# 内部工具：十神 → 字
# ============================================================

def _gans_for_shishen(day_master: Gan, shishens: tuple[Shishen, ...]) -> list[str]:
    """该十神集合对应的所有天干字。

    例：day_master=壬, shishens=("正财","偏财") → ["丙","丁"]（火克水的两个）
    """
    out: list[str] = []
    for g in GAN_LIST:
        try:
            if get_shishen(g, day_master) in shishens:
                out.append(g)
        except (ValueError, RuntimeError):
            continue
    return out


def _zhis_for_shishen(day_master: Gan, shishens: tuple[Shishen, ...]) -> list[str]:
    """该十神集合对应的所有地支字（主气取十神）。

    例：day_master=壬, shishens=("正财","偏财")：
        丙藏巳/丁藏午 → ["巳","午"]
    """
    out: list[str] = []
    for z in ZHI_LIST:
        cangs = ZHI_CANGGAN_TABLE.get(z, [])
        if not cangs:
            continue
        zhuqi = cangs[0][0]  # 主气天干
        try:
            if get_shishen(zhuqi, day_master) in shishens:
                out.append(z)
        except (ValueError, RuntimeError):
            continue
    return out


def _gender_to_canonical(gender: Optional[str]) -> str:
    """归一化性别字符串。返回 'M' 或 'F'。默认 'M'（男）。"""
    if not gender:
        return "M"
    g = str(gender).strip().upper()
    if g in ("F", "FEMALE", "女", "坤", "坤造"):
        return "F"
    return "M"


def _spouse_shishens(gender: str) -> tuple[Shishen, ...]:
    """配偶星：男命=正/偏财，女命=正/七杀。"""
    return ("正官", "七杀") if _gender_to_canonical(gender) == "F" else ("正财", "偏财")


def _children_shishens(gender: str) -> tuple[Shishen, ...]:
    """子女星：男看官杀，女看食伤。"""
    return ("食神", "伤官") if _gender_to_canonical(gender) == "F" else ("正官", "七杀")


def _parent_shishens(sub: str) -> tuple[Shishen, ...]:
    """六亲映射：父=偏财，母=正印，兄弟=比劫。"""
    if sub == "父":
        return ("偏财",)
    if sub == "母":
        return ("正印",)
    if sub == "兄弟":
        return ("比肩", "劫财")
    return ()


# ============================================================
# 内部工具：取 EnergyFindings.tiyong.purpose 字符
# ============================================================

def _energy_purpose_chars(energy: Optional[EnergyFindings]) -> list[str]:
    """从 EnergyFindings.tiyong.purpose 提取所有"用神"字符（去重）。"""
    if energy is None:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in energy.tiyong.purpose:
        if item.char not in seen:
            seen.add(item.char)
            out.append(item.char)
    return out


def _energy_purpose_chars_with_role(
    energy: Optional[EnergyFindings],
    roles: tuple[str, ...],
) -> list[str]:
    """从 EnergyFindings.tiyong.purpose 提取符合特定 role 的字符。"""
    if energy is None:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in energy.tiyong.purpose:
        if item.role in roles and item.char not in seen:
            seen.add(item.char)
            out.append(item.char)
    return out


def _dedup(chars: list[str]) -> list[str]:
    """保序去重。"""
    seen: set[str] = set()
    out: list[str] = []
    for c in chars:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


# ============================================================
# 一、infer_sub_domain
# ============================================================

def infer_sub_domain(candidate_event: str) -> Optional[str]:
    """从 candidate_event 文字推断 六亲 sub_domain。

    返回："父" / "母" / "兄弟" / "子女" / "配偶" / None
    """
    cev = candidate_event or ""
    if any(k in cev for k in ("母亲", "妈妈", "母去", "母逝", "母亡", "母病")):
        return "母"
    if any(k in cev for k in ("父亲", "爸爸", "父去", "父逝", "父亡", "父病")):
        return "父"
    if any(k in cev for k in ("兄", "弟", "姐", "妹", "哥", "兄弟", "姐妹")):
        return "兄弟"
    if any(k in cev for k in ("子女", "孩子", "怀孕", "生子", "生女", "得子", "得女")):
        return "子女"
    if any(k in cev for k in ("结婚", "成婚", "嫁", "娶", "离婚", "妻", "夫", "丈夫", "妻子")):
        return "配偶"
    return None


# ============================================================
# 二、get_primary_keys
# ============================================================

def get_primary_keys(
    domain: str,
    bazi: Bazi,
    energy: Optional[EnergyFindings],
    *,
    gender: Optional[str] = None,
    sub_domain: Optional[str] = None,
) -> list[str]:
    """领域的主关键字列表（去重，含天干 + 地支字符）。

    严格按 04-gate § 3.1 实现。
    """
    day_master = bazi.day_master
    chars: list[str] = []

    # ============ 婚姻 ============
    if domain == "婚姻":
        spouse_ss = _spouse_shishens(gender or "M")
        chars.extend(_gans_for_shishen(day_master, spouse_ss))
        chars.extend(_zhis_for_shishen(day_master, spouse_ss))
        # 婚宫支（日支）
        chars.append(bazi.日柱.zhi)

        # "无星借宫"豁免（04 § 9.1）：若配偶星完全不见原局含藏干 → 加食伤兜底
        spouse_in_yj = _has_any_in_yuanju(chars, bazi)
        if not spouse_in_yj:
            # 男无财借食伤；女无官借财
            fallback_ss: tuple[Shishen, ...] = (
                ("正财", "偏财") if _gender_to_canonical(gender) == "F"
                else ("食神", "伤官")
            )
            chars.extend(_gans_for_shishen(day_master, fallback_ss))
            chars.extend(_zhis_for_shishen(day_master, fallback_ss))

    # ============ 事业 ============
    elif domain == "事业":
        chars.extend(_gans_for_shishen(day_master, ("正官", "七杀")))
        chars.extend(_zhis_for_shishen(day_master, ("正官", "七杀")))
        # D1 用神（tiyong.purpose）
        chars.extend(_energy_purpose_chars(energy))
        # 无官杀 → 食伤为业（04 § 3.1 备注）
        if not _gans_for_shishen(day_master, ("正官", "七杀")):
            chars.extend(_gans_for_shishen(day_master, ("食神", "伤官")))

    # ============ 财运 ============
    elif domain == "财运":
        chars.extend(_gans_for_shishen(day_master, ("正财", "偏财")))
        chars.extend(_zhis_for_shishen(day_master, ("正财", "偏财")))
        # D1 用神中财类字（用 role="财"）
        chars.extend(_energy_purpose_chars_with_role(energy, ("财",)))

    # ============ 健康 ============
    elif domain == "健康":
        # 日干本身（太弱/太旺都是病根）
        chars.append(day_master)
        # 受刑冲穿破最重的支：简化为日支（最贴身）+ 月支
        chars.append(bazi.日柱.zhi)
        chars.append(bazi.月柱.zhi)

    # ============ 学业 ============
    elif domain == "学业":
        chars.extend(_gans_for_shishen(day_master, ("正印", "偏印")))
        chars.extend(_zhis_for_shishen(day_master, ("正印", "偏印")))
        chars.extend(_gans_for_shishen(day_master, ("食神", "伤官")))
        chars.extend(_zhis_for_shishen(day_master, ("食神", "伤官")))

    # ============ 六亲 ============
    elif domain == "六亲":
        if sub_domain == "配偶":
            spouse_ss = _spouse_shishens(gender or "M")
            chars.extend(_gans_for_shishen(day_master, spouse_ss))
            chars.extend(_zhis_for_shishen(day_master, spouse_ss))
            chars.append(bazi.日柱.zhi)
        elif sub_domain == "子女":
            ch_ss = _children_shishens(gender or "M")
            chars.extend(_gans_for_shishen(day_master, ch_ss))
            chars.extend(_zhis_for_shishen(day_master, ch_ss))
            # 子女宫 = 时柱（干 + 支）
            chars.append(bazi.时柱.gan)
            chars.append(bazi.时柱.zhi)
        elif sub_domain in ("父", "母", "兄弟"):
            ss = _parent_shishens(sub_domain)
            if ss:
                chars.extend(_gans_for_shishen(day_master, ss))
                chars.extend(_zhis_for_shishen(day_master, ss))
            # 各六亲宫位（04 § 3.1 secondary 中提及，作为主关键字也合理）
            if sub_domain == "父":
                chars.append(bazi.年柱.gan)
                chars.append(bazi.年柱.zhi)
            elif sub_domain == "母":
                # 母 = 正印 + 月柱
                chars.append(bazi.月柱.gan)
                chars.append(bazi.月柱.zhi)
            elif sub_domain == "兄弟":
                chars.append(bazi.月柱.zhi)
        else:
            # 通配六亲：父 + 母 + 配偶
            chars.extend(_gans_for_shishen(day_master, ("偏财",)))
            chars.extend(_zhis_for_shishen(day_master, ("偏财",)))
            chars.extend(_gans_for_shishen(day_master, ("正印",)))
            chars.extend(_zhis_for_shishen(day_master, ("正印",)))
            spouse_ss = _spouse_shishens(gender or "M")
            chars.extend(_gans_for_shishen(day_master, spouse_ss))
            chars.extend(_zhis_for_shishen(day_master, spouse_ss))
            # 各宫位
            chars.extend([
                bazi.年柱.gan, bazi.年柱.zhi,
                bazi.月柱.gan, bazi.月柱.zhi,
                bazi.日柱.zhi,
            ])

    # ============ 其他 ============
    elif domain == "其他":
        chars.append(day_master)
        chars.extend(_energy_purpose_chars(energy))
    else:
        raise ValueError(f"未知 domain: {domain!r}")

    return _dedup(chars)


# ============================================================
# 三、get_secondary_keys
# ============================================================

def get_secondary_keys(
    domain: str,
    bazi: Bazi,
    energy: Optional[EnergyFindings],
    *,
    gender: Optional[str] = None,
    sub_domain: Optional[str] = None,
) -> list[str]:
    """领域的次关键字列表（与 primary 互不重复）。"""
    day_master = bazi.day_master
    chars: list[str] = []

    if domain == "婚姻":
        # 配偶星藏干所在地支：通过 spouse 的 zhis
        # （已在 primary 中包含主气支；这里加上含配偶星余气/中气的支）
        spouse_ss = _spouse_shishens(gender or "M")
        for z in ZHI_LIST:
            for cg, typ, _ in ZHI_CANGGAN_TABLE.get(z, []):
                if typ in ("中气", "余气"):
                    try:
                        if get_shishen(cg, day_master) in spouse_ss:
                            chars.append(z)
                            break
                    except (ValueError, RuntimeError):
                        pass
        # 月柱地支（杨派：父母给的婚配格局）
        chars.append(bazi.月柱.zhi)

    elif domain == "事业":
        # 官星藏干位置：包含官杀中/余气的支
        for z in ZHI_LIST:
            for cg, typ, _ in ZHI_CANGGAN_TABLE.get(z, []):
                if typ in ("中气", "余气"):
                    try:
                        if get_shishen(cg, day_master) in ("正官", "七杀"):
                            chars.append(z)
                            break
                    except (ValueError, RuntimeError):
                        pass
        # 月令（事业宫主要是月柱）
        chars.append(bazi.月柱.zhi)
        chars.append(bazi.月柱.gan)

    elif domain == "财运":
        # 财库（辰戌丑未中藏财的支）
        for z in ("辰", "戌", "丑", "未"):
            for cg, _, _ in ZHI_CANGGAN_TABLE.get(z, []):
                try:
                    if get_shishen(cg, day_master) in ("正财", "偏财"):
                        chars.append(z)
                        break
                except (ValueError, RuntimeError):
                    pass
        # 食伤生财链：食伤天干字
        chars.extend(_gans_for_shishen(day_master, ("食神", "伤官")))

    elif domain == "健康":
        # 食神（寿星）+ 偏印（枭神，伤食对冲）+ 各支
        chars.extend(_gans_for_shishen(day_master, ("食神",)))
        chars.extend(_gans_for_shishen(day_master, ("偏印",)))
        # 注：神煞挂柱由 D4 SupportFindings 提供，本层不计算

    elif domain == "学业":
        # 词馆/学堂/文昌神煞所挂柱 → D4 提供；这里给出"印官同时"信号
        chars.extend(_gans_for_shishen(day_master, ("正官", "七杀")))
        chars.extend(_zhis_for_shishen(day_master, ("正官", "七杀")))
        # 月柱（学习环境）
        chars.append(bazi.月柱.zhi)

    elif domain == "六亲":
        # 各宫位地支（年/月/日/时）
        chars.extend([
            bazi.年柱.zhi, bazi.月柱.zhi, bazi.日柱.zhi, bazi.时柱.zhi,
        ])

    elif domain == "其他":
        pass

    return _dedup(chars)


# ============================================================
# 四、get_required_dayun_chars (04 § 4.1)
# ============================================================

def get_required_dayun_chars(
    domain: str,
    energy: Optional[EnergyFindings],
    parsed: ParsedInput,
    *,
    sub_domain: Optional[str] = None,
) -> list[str]:
    """L2 必需大运字（04 § 4.1 表）。

    含义：当前年所在大运的干 / 支 / 邻近大运字 中，至少含 1 个 → L2 通过。
    """
    bazi = parsed.bazi
    gender = (parsed.birth or {}).get("性别")

    # 主关键字一律纳入（04 § 4.1 表里"配偶星天干"等都是主关键字）
    chars = list(get_primary_keys(
        domain, bazi, energy, gender=gender, sub_domain=sub_domain,
    ))

    # 04 § 4.1 各 domain 的 specific 增补
    day_master = bazi.day_master

    if domain == "婚姻":
        # 桃花引动字：日支三合的"桃花"位（子午卯酉之一，按命主婚宫所在三合局）
        marriage_zhi = bazi.日柱.zhi
        taohua_map = {
            # 三合局 → 桃花位（中神 / 子午卯酉之一）
            ("申", "子", "辰"): "酉",
            ("寅", "午", "戌"): "卯",
            ("巳", "酉", "丑"): "午",
            ("亥", "卯", "未"): "子",
        }
        for group, taohua in taohua_map.items():
            if marriage_zhi in group:
                chars.append(taohua)
                break

    elif domain == "事业":
        # 印动字（官印相生）= 印星天干 / 主气支
        chars.extend(_gans_for_shishen(day_master, ("正印", "偏印")))
        chars.extend(_zhis_for_shishen(day_master, ("正印", "偏印")))

    elif domain == "财运":
        # 财库 + 食伤生财
        for z in ("辰", "戌", "丑", "未"):
            for cg, _, _ in ZHI_CANGGAN_TABLE.get(z, []):
                try:
                    if get_shishen(cg, day_master) in ("正财", "偏财"):
                        chars.append(z)
                        break
                except (ValueError, RuntimeError):
                    pass
        chars.extend(_gans_for_shishen(day_master, ("食神", "伤官")))

    elif domain == "健康":
        # 受刑冲穿的字（核心）
        chars.append(bazi.日柱.zhi)
        # 食神/枭神
        chars.extend(_gans_for_shishen(day_master, ("食神", "偏印")))

    elif domain == "学业":
        # 印星 + 文昌（文昌以日干起，简化用日支三合中神）
        chars.extend(_gans_for_shishen(day_master, ("正印", "偏印")))

    return _dedup(chars)


# ============================================================
# 五、辅助：判断 chars 是否在原局（含藏干）
# ============================================================

def _has_any_in_yuanju(chars: list[str], bazi: Bazi) -> bool:
    """这些字 是否有任一出现在原局四柱（含藏干）。"""
    in_8 = set()
    for _, gan in bazi.all_gans():
        in_8.add(gan)
    for _, zhi in bazi.all_zhis():
        in_8.add(zhi)
        for cg, _, _ in ZHI_CANGGAN_TABLE.get(zhi, []):
            in_8.add(cg)
    return any(c in in_8 for c in chars)


def chars_in_yuanju(chars: list[str], bazi: Bazi) -> list[str]:
    """子集：哪些字在原局四柱（含藏干）出现。"""
    in_8: set[str] = set()
    for _, gan in bazi.all_gans():
        in_8.add(gan)
    for _, zhi in bazi.all_zhis():
        in_8.add(zhi)
        for cg, _, _ in ZHI_CANGGAN_TABLE.get(zhi, []):
            in_8.add(cg)
    return [c for c in chars if c in in_8]


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    from engine.predicates.types import GanZhi, _default_canggan_for

    # C-2026-001：庚申戊寅壬子辛丑（壬日干，男）
    bazi = Bazi(
        年柱=GanZhi("庚", "申"),
        月柱=GanZhi("戊", "寅"),
        日柱=GanZhi("壬", "子"),
        时柱=GanZhi("辛", "丑"),
    )
    bazi.藏干 = _default_canggan_for(bazi)

    # 婚姻 男命 → 财（丙/丁）+ 妻宫（子）
    keys = get_primary_keys("婚姻", bazi, None, gender="M")
    assert "丙" in keys, f"丙财应在: {keys}"
    assert "丁" in keys
    assert "子" in keys, f"妻宫子应在: {keys}"
    # 主气支：丙在巳，丁在午
    assert "巳" in keys
    assert "午" in keys
    print(f"[OK] 婚姻 男命 keys: {keys}")

    # 婚姻 女命（戊日干 → 官杀=甲乙）
    bazi2 = Bazi(
        年柱=GanZhi("壬", "戌"),
        月柱=GanZhi("庚", "戌"),
        日柱=GanZhi("戊", "辰"),
        时柱=GanZhi("丙", "辰"),
    )
    bazi2.藏干 = _default_canggan_for(bazi2)
    keys = get_primary_keys("婚姻", bazi2, None, gender="F")
    assert "甲" in keys, f"七杀甲应在: {keys}"
    assert "乙" in keys
    assert "辰" in keys, f"夫宫辰应在: {keys}"
    print(f"[OK] 婚姻 女命 keys（部分）: {keys[:8]}")

    # 学业（壬日干 → 印=庚辛 + 食伤=甲乙）
    keys = get_primary_keys("学业", bazi, None)
    assert "庚" in keys
    assert "辛" in keys
    assert "甲" in keys
    assert "乙" in keys
    print(f"[OK] 学业 keys: {keys}")

    # 事业（壬日干 → 官杀=戊己）
    keys = get_primary_keys("事业", bazi, None)
    assert "戊" in keys
    assert "己" in keys
    print(f"[OK] 事业 keys: {keys}")

    # 六亲 母 → 正印
    keys = get_primary_keys("六亲", bazi, None, sub_domain="母")
    # 壬日干 → 正印 = 辛
    assert "辛" in keys
    # 母位 = 月柱
    assert "戊" in keys or "寅" in keys
    print(f"[OK] 六亲-母 keys: {keys}")

    # 健康 → 日干 + 日支
    keys = get_primary_keys("健康", bazi, None)
    assert "壬" in keys
    assert "子" in keys
    print(f"[OK] 健康 keys: {keys}")

    # 财运 → 财（丙/丁/巳/午）
    keys = get_primary_keys("财运", bazi, None)
    assert "丙" in keys and "丁" in keys
    print(f"[OK] 财运 keys: {keys}")

    # 其他 → 日干
    keys = get_primary_keys("其他", bazi, None)
    assert "壬" in keys
    print(f"[OK] 其他 keys: {keys}")

    # secondary：婚姻 → 月柱地支
    skeys = get_secondary_keys("婚姻", bazi, None, gender="M")
    assert "寅" in skeys, f"月柱地支寅应在 secondary: {skeys}"
    print(f"[OK] 婚姻 secondary: {skeys}")

    # required_dayun_chars 婚姻：含妻宫子三合的桃花 = 酉（申子辰桃花在酉）
    bazi.藏干 = _default_canggan_for(bazi)
    parsed = ParsedInput(
        case_id="test", bazi=bazi,
        dayun=__import__("engine.predicates.types", fromlist=["Dayun"]).Dayun(
            起运岁=8, 起运年=1988, 顺逆="顺", 排布=[]
        ),
        birth={"性别": "M", "公历年": 1980},
    )
    rkeys = get_required_dayun_chars("婚姻", None, parsed)
    assert "酉" in rkeys, f"婚姻桃花酉应在 required: {rkeys}"
    print(f"[OK] 婚姻 required_dayun_chars 含桃花酉: {rkeys[:8]}")

    # infer_sub_domain
    assert infer_sub_domain("母亲去世") == "母"
    assert infer_sub_domain("提副科") is None
    assert infer_sub_domain("结婚") == "配偶"
    assert infer_sub_domain("生子") == "子女"
    assert infer_sub_domain("姐姐生病") == "兄弟"
    print("[OK] infer_sub_domain")

    # chars_in_yuanju
    sub = chars_in_yuanju(["丙", "丁", "庚", "壬", "癸"], bazi)
    assert "丙" in sub  # 寅藏丙
    assert "庚" in sub  # 年干透 + 申主气
    assert "壬" in sub  # 日干
    assert "癸" in sub  # 子主气 + 丑余气 + 辰余气
    assert "丁" not in sub  # 不在原局也不藏
    print("[OK] chars_in_yuanju")

    print("\n[OK] yingqi.keys smoke 全过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
