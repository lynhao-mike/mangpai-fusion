"""engine/energy/zuogong.py · v1.2 D1 段派 · 6 种做功扫描

段派"做功"理论（M1-D-009..014, 113..121, 222..226）：

    做功 = 体（工具）作用于 用（目的）产生效率
    没有做功 = 平庸命；做功层数越多 = 富贵层级越高

6 种做功方式（M1-D-009..014）：
    1. 制 (M1-D-009)：用神被克/冲/穿（80% 命局靠此）
       例：食神制杀 / 比劫去财（"去财格"=反贵）
    2. 化 (M1-D-010)：印化杀 / 杀印相生 / 合化生用
    3. 生泄 (M1-D-011)：顺生链——食伤生财、财生官杀、印生身
    4. 合 (M1-D-012)：五合化神成"有用之物"
    5. 墓 (M1-D-013)：财官入辰戌丑未墓库
    6. 复合 (M1-D-014)：多种做功叠加（一命多功）

层数判定（M1-D-173）：
    1 层 = 百万级 / 2 层 = 千万级 / 3 层 = 亿级 / 4 层 = 百亿级

实务做法：
    - 每发现一条独立做功路径 → +1 层
    - 同一用神被多种做功作用 → 仅算第一种为独立层，其余加权计入"复合"
    - layer_count 上限 4

⚠️ 失败兜底（08 § 失败兜底）：
    本模块完整实现 制/化/生泄/合 四种；
    墓 = 简化实现（只检测财官入辰戌丑未）；
    复合 = 启发式（≥2 种做功类型重叠在同一用神 → 标记）。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from engine.energy.types import Magnitude, ZuogongPath, ZuogongType
from engine.energy.tiyong import (
    gan_role_to_day,
    get_lu,
    zhi_role_to_day,
)
from engine.predicates.types import (
    Bazi,
    Gan,
    GanZhi,
    Wuxing,
    Zhi,
    ZHI_CANGGAN_TABLE,
)
from engine.predicates.ganzhi import gan_to_wuxing, zhi_to_wuxing
from engine.predicates.relations import (
    gan_he,
    gan_zhi_anhe,
    relation_strength,
    zhi_chong,
    zhi_chuan,
    zhi_liuhe,
    zhi_po,
    zhi_sanhe,
    zhi_sanhui,
    zhi_xing,
)
from engine.predicates.wuxing import (
    gan_ke_gan,
    gan_sheng_gan,
    wuxing_ke,
    wuxing_relation,
    wuxing_sheng,
)


# ============================================================
# 工具函数
# ============================================================

def _is_yongshen_gan(gan: Gan, day_master: Gan) -> bool:
    """是否为用神（财 / 官杀）。"""
    role = gan_role_to_day(gan, day_master)
    return role in ("财", "官杀")


def _is_yongshen_zhi(zhi: Zhi, day_master: Gan) -> bool:
    """地支主气是否为用神（财 / 官杀）。"""
    role = zhi_role_to_day(zhi, day_master)
    return role in ("财", "官杀")


def _is_zhibody_gan(gan: Gan, day_master: Gan) -> bool:
    """是否为体方天干（印 / 比劫 / 食伤）。"""
    role = gan_role_to_day(gan, day_master)
    return role in ("印", "比劫", "食伤")


def _yongshen_in_zhi_canggan(zhi: Zhi, day_master: Gan) -> list[tuple[Gan, str]]:
    """返回该支藏干中所有"用神"。返回 [(gan, type), ...]"""
    out: list[tuple[Gan, str]] = []
    for (g, t, _) in ZHI_CANGGAN_TABLE.get(zhi, []):
        if _is_yongshen_gan(g, day_master):
            out.append((g, t))
    return out


# ============================================================
# 1. 制 路径
# ============================================================

def _scan_zhi_pair_actions(bazi: Bazi) -> list[tuple[str, str, Zhi, Zhi, str]]:
    """扫描所有地支两两关系（冲/穿/刑/破/六合/三合）。

    返回 [(柱A, 柱B, 支A, 支B, 关系名), ...]
    """
    pairs: list[tuple[str, str, Zhi, Zhi, str]] = []
    zhis = bazi.all_zhis()
    for i in range(len(zhis)):
        for j in range(i + 1, len(zhis)):
            (na, za), (nb, zb) = zhis[i], zhis[j]
            if zhi_chong(za, zb):
                pairs.append((na, nb, za, zb, "冲"))
            if zhi_chuan(za, zb):
                pairs.append((na, nb, za, zb, "穿"))
            if zhi_xing(za, zb) is not None:
                pairs.append((na, nb, za, zb, "刑"))
            if zhi_po(za, zb):
                pairs.append((na, nb, za, zb, "破"))
            if zhi_liuhe(za, zb) is not None:
                pairs.append((na, nb, za, zb, "六合"))
    return pairs


def _scan_gan_pair_actions(bazi: Bazi) -> list[tuple[str, str, Gan, Gan, str]]:
    """扫描天干两两关系（克/合）。

    返回 [(柱A, 柱B, 干A, 干B, 关系名), ...]
    """
    pairs: list[tuple[str, str, Gan, Gan, str]] = []
    gans = bazi.all_gans()
    for i in range(len(gans)):
        for j in range(i + 1, len(gans)):
            (na, ga), (nb, gb) = gans[i], gans[j]
            if gan_ke_gan(ga, gb):
                pairs.append((na, nb, ga, gb, "克"))
            if gan_he(ga, gb) is not None:
                pairs.append((na, nb, ga, gb, "合"))
    return pairs


def detect_zhi_paths(bazi: Bazi, day_master: Gan) -> list[ZuogongPath]:
    """扫描"地支制路径"——任何用神支被冲/穿/刑/破/合作用。

    制 = 冲/穿/刑/破 (主动破坏)
    合 = 六合 (吸合)
    """
    out: list[ZuogongPath] = []
    seen_keys: set[tuple[str, str]] = set()  # 去重 (yongshen, action)

    for (na, nb, za, zb, rel) in _scan_zhi_pair_actions(bazi):
        # 找出哪个支是用神（含主气 / 中气含用神）
        ya = _is_yongshen_zhi(za, day_master)
        yb = _is_yongshen_zhi(zb, day_master)
        ya_canggan_yong = _yongshen_in_zhi_canggan(za, day_master)
        yb_canggan_yong = _yongshen_in_zhi_canggan(zb, day_master)

        # 用神 = 主气用神 OR 含用神藏干
        is_a_yong = ya or len(ya_canggan_yong) > 0
        is_b_yong = yb or len(yb_canggan_yong) > 0
        if not (is_a_yong or is_b_yong):
            continue

        # 类型映射
        if rel in ("冲", "穿", "刑", "破"):
            ztype: ZuogongType = "制"
        else:  # 六合
            ztype = "合"

        # 角色描述
        target_zhi = za if is_a_yong else zb
        target_role = zhi_role_to_day(target_zhi, day_master)
        # 若主气不是用神但藏干是 → 角色用藏干那个
        if not (ya if is_a_yong == ya else yb):
            yong_in = ya_canggan_yong if is_a_yong else yb_canggan_yong
            if yong_in:
                target_role = gan_role_to_day(yong_in[0][0], day_master)

        key = (target_zhi, ztype)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        # 强度 = relation_strength
        strength_score = relation_strength({"冲": "冲", "穿": "穿", "刑": "刑", "破": "破", "六合": "合"}[rel])
        ord_label = "强" if strength_score >= 0.85 else ("中" if strength_score >= 0.65 else "弱")

        chain = [za, zb] if is_a_yong else [zb, za]
        desc = (
            f"{na}支{za} ↔ {nb}支{zb} 之 {rel}"
            f" → 作用于用神{target_zhi}({target_role})"
        )
        out.append(ZuogongPath(
            type=ztype, chain=list(chain), description=desc,
            strength=Magnitude(ordinal=ord_label, score=strength_score),
            layer_count=1,
        ))
    return out


def detect_gan_paths(bazi: Bazi, day_master: Gan) -> list[ZuogongPath]:
    """天干制路径：食伤克官杀 / 比劫克财 / 印护身。

    重点：食神制杀（M1-D-029）、比劫去财（M1-D-152）、印化杀（M1-D-028）。
    """
    out: list[ZuogongPath] = []
    seen_keys: set[tuple[str, Gan]] = set()

    for (na, nb, ga, gb, rel) in _scan_gan_pair_actions(bazi):
        # 同一柱（自合不参与做功）
        if rel == "克":
            # 找出 体 → 用 哪个克哪个
            ra = gan_role_to_day(ga, day_master)
            rb = gan_role_to_day(gb, day_master)
            # 体克用 = 制
            if ra in ("食伤", "比劫", "印") and rb in ("财", "官杀"):
                if gan_ke_gan(ga, gb):
                    body, body_r = ga, ra
                    user, user_r = gb, rb
                    role_pair = f"{body_r}制{user_r}"
                    desc = f"{na}干{body}({body_r}) 克 {nb}干{user}({user_r}) → {role_pair}"
                    key = ("制", user)
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    score = 0.85 if user_r == "官杀" and body_r == "食伤" else 0.75
                    ord_label = "强" if score >= 0.80 else "中"
                    out.append(ZuogongPath(
                        type="制", chain=[body, user], description=desc,
                        strength=Magnitude(ordinal=ord_label, score=score),
                        layer_count=1,
                    ))
                    continue
            elif rb in ("食伤", "比劫", "印") and ra in ("财", "官杀"):
                if gan_ke_gan(gb, ga):
                    body, body_r = gb, rb
                    user, user_r = ga, ra
                    role_pair = f"{body_r}制{user_r}"
                    desc = f"{nb}干{body}({body_r}) 克 {na}干{user}({user_r}) → {role_pair}"
                    key = ("制", user)
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    score = 0.85 if user_r == "官杀" and body_r == "食伤" else 0.75
                    ord_label = "强" if score >= 0.80 else "中"
                    out.append(ZuogongPath(
                        type="制", chain=[body, user], description=desc,
                        strength=Magnitude(ordinal=ord_label, score=score),
                        layer_count=1,
                    ))
                    continue

        elif rel == "合":
            ra = gan_role_to_day(ga, day_master)
            rb = gan_role_to_day(gb, day_master)
            # 五合化神是否为"用"（财/官）OR "体辅"（印/比/食伤）— 段派关心化神是否有用
            he_result = gan_he(ga, gb)
            assert he_result is not None
            huashen, state = he_result
            # 化神角色
            day_wx = gan_to_wuxing(day_master)
            hua_rel = wuxing_relation(day_wx, huashen)
            hua_role = {
                "同我": "比劫", "生我": "印", "我生": "食伤",
                "我克": "财", "克我": "官杀",
            }[hua_rel]

            # 是否涉及用神
            involves_yong = (ra in ("财", "官杀")) or (rb in ("财", "官杀"))
            if not involves_yong and hua_role not in ("财", "官杀"):
                # 合不涉及用神，且化神也不是用神 → 不算做功
                continue

            key = ("合", ga + gb)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            score = 0.6
            if hua_role in ("财", "官杀"):
                # 合化为用 = 合用
                desc = f"{na}干{ga}({ra}) 合 {nb}干{gb}({rb}) 化{huashen}={hua_role} [{state}]"
                score = 0.7 if state == "化成" else 0.55
            else:
                desc = f"{na}干{ga}({ra}) 合 {nb}干{gb}({rb}) → 用神被合 [{state}]"
                score = 0.55

            ord_label = "中" if score >= 0.6 else "弱"
            out.append(ZuogongPath(
                type="合", chain=[ga, gb], description=desc,
                strength=Magnitude(ordinal=ord_label, score=score),
                layer_count=1,
            ))
    return out


# ============================================================
# 2. 化 路径（印化杀 / 杀印相生）
# ============================================================

def detect_hua_paths(bazi: Bazi, day_master: Gan) -> list[ZuogongPath]:
    """印化杀 / 杀印相生 = 化用做功。

    判定：原局含 官杀 + 印 + 印能化杀（官杀生印的相邻关系）。
    """
    out: list[ZuogongPath] = []
    day_wx = gan_to_wuxing(day_master)

    # 找天干 + 地支主气中所有 官杀 与 印
    yin_chars: list[tuple[str, str, str]] = []     # (柱, 字, 五行)
    sha_chars: list[tuple[str, str, str]] = []
    for name, gan in bazi.all_gans():
        role = gan_role_to_day(gan, day_master)
        if role == "印":
            yin_chars.append((name, gan, gan_to_wuxing(gan)))
        if role == "官杀":
            sha_chars.append((name, gan, gan_to_wuxing(gan)))
    for name, zhi in bazi.all_zhis():
        role = zhi_role_to_day(zhi, day_master)
        wx = zhi_to_wuxing(zhi)
        if role == "印":
            yin_chars.append((f"{name[0]}支", zhi, wx))
        if role == "官杀":
            sha_chars.append((f"{name[0]}支", zhi, wx))

    # 印化杀 = 官杀生印（即 印的五行 受 官杀的五行 生）
    for (sn, sc, swx) in sha_chars:
        for (yn, yc, ywx) in yin_chars:
            if wuxing_sheng(swx, ywx):
                desc = f"{sn}{sc}(官杀,{swx}) → 生 → {yn}{yc}(印,{ywx}) → 生身 [印化杀]"
                out.append(ZuogongPath(
                    type="化", chain=[sc, yc, day_master],
                    description=desc,
                    strength=Magnitude(ordinal="强", score=0.80),
                    layer_count=1,
                ))
                # 一对印化杀就够了，只取第一个，避免重复
                return out
    return out


# ============================================================
# 3. 生泄 路径（顺生链）
# ============================================================

def detect_shengxie_paths(bazi: Bazi, day_master: Gan) -> list[ZuogongPath]:
    """顺生链：食伤生财 / 财生官 / 印生身 / 比劫生食伤。

    重点找两类：
    - 食伤 → 财（生发财源）
    - 财 → 官杀（财生官）
    """
    out: list[ZuogongPath] = []

    food: list[tuple[str, str, str]] = []
    cai: list[tuple[str, str, str]] = []
    guan: list[tuple[str, str, str]] = []

    def collect(role_target: str, bucket: list):
        for name, gan in bazi.all_gans():
            if gan_role_to_day(gan, day_master) == role_target:
                bucket.append((name, gan, gan_to_wuxing(gan)))
        for name, zhi in bazi.all_zhis():
            if zhi_role_to_day(zhi, day_master) == role_target:
                bucket.append((f"{name[0]}支", zhi, zhi_to_wuxing(zhi)))

    collect("食伤", food)
    collect("财", cai)
    collect("官杀", guan)

    seen: set[tuple[str, str]] = set()

    # 食 → 财
    for (sn, sc, swx) in food:
        for (cn, cc, cwx) in cai:
            if wuxing_sheng(swx, cwx):
                key = ("食生财", sc + cc)
                if key in seen:
                    continue
                seen.add(key)
                desc = f"{sn}{sc}(食伤,{swx}) → 生 → {cn}{cc}(财,{cwx}) [食伤生财]"
                out.append(ZuogongPath(
                    type="生泄", chain=[sc, cc],
                    description=desc,
                    strength=Magnitude(ordinal="中", score=0.65),
                    layer_count=1,
                ))
                break  # 每个 sc 只算一次
    # 财 → 官
    for (cn, cc, cwx) in cai:
        for (gn, gc, gwx) in guan:
            if wuxing_sheng(cwx, gwx):
                key = ("财生官", cc + gc)
                if key in seen:
                    continue
                seen.add(key)
                desc = f"{cn}{cc}(财,{cwx}) → 生 → {gn}{gc}(官杀,{gwx}) [财生官]"
                out.append(ZuogongPath(
                    type="生泄", chain=[cc, gc],
                    description=desc,
                    strength=Magnitude(ordinal="中", score=0.65),
                    layer_count=1,
                ))
                break
    return out


# ============================================================
# 4. 合 路径（地支三合 + 五合化用）已在 zhi/gan_paths 中处理
# ============================================================

def detect_sanhe_paths(bazi: Bazi, day_master: Gan) -> list[ZuogongPath]:
    """三合局 / 三会方化用判断。"""
    out: list[ZuogongPath] = []
    zhis = [z for _, z in bazi.all_zhis()]

    # 三合
    for combo_size in (3, 4):
        # 简单实现：直接 zhi_sanhe([全部]) 看是否成局
        pass

    sanhe = zhi_sanhe(zhis)
    if sanhe is not None:
        # 化神是否为用？
        day_wx = gan_to_wuxing(day_master)
        rel = wuxing_relation(day_wx, sanhe)
        role = {
            "同我": "比劫", "生我": "印", "我生": "食伤",
            "我克": "财", "克我": "官杀",
        }[rel]
        if role in ("财", "官杀"):
            # 合用大喜
            desc = f"四支三合化{sanhe}({role}) → 合用做功"
            out.append(ZuogongPath(
                type="合", chain=zhis, description=desc,
                strength=Magnitude(ordinal="强", score=0.80),
                layer_count=1,
            ))

    sanhui = zhi_sanhui(zhis)
    if sanhui is not None:
        day_wx = gan_to_wuxing(day_master)
        rel = wuxing_relation(day_wx, sanhui)
        role = {
            "同我": "比劫", "生我": "印", "我生": "食伤",
            "我克": "财", "克我": "官杀",
        }[rel]
        if role in ("财", "官杀"):
            desc = f"四支三会{sanhui}方({role}) → 合用做功"
            out.append(ZuogongPath(
                type="合", chain=zhis, description=desc,
                strength=Magnitude(ordinal="强", score=0.80),
                layer_count=1,
            ))
    return out


# ============================================================
# 5. 墓 路径（财官入辰戌丑未）
# ============================================================

# 五行墓库：水墓辰 / 火墓戌 / 木墓未 / 金墓丑
_MUKU_TABLE: dict[Wuxing, Zhi] = {
    "水": "辰", "火": "戌", "木": "未", "金": "丑",
}


def detect_mu_paths(bazi: Bazi, day_master: Gan) -> list[ZuogongPath]:
    """墓库做功（M1-D-013, 069, 074, 120, 237..238）：
    财官入辰戌丑未 = 库存财官，需有刑冲打开方能得（M1-D-253 财库喜刑冲）。

    简化判定：原局有 财/官 五行 + 辰戌丑未 含财官藏干 + 至少一个刑冲。
    """
    out: list[ZuogongPath] = []
    mu_zhis: list[tuple[str, Zhi]] = []
    for name, z in bazi.all_zhis():
        if z in ("辰", "戌", "丑", "未"):
            mu_zhis.append((name, z))
    if not mu_zhis:
        return out

    # 是否有刑/冲打开
    all_pairs = _scan_zhi_pair_actions(bazi)
    has_chong_xing_on_mu = any(
        (rel in ("冲", "刑")) and (za in ("辰", "戌", "丑", "未") or zb in ("辰", "戌", "丑", "未"))
        for (_, _, za, zb, rel) in all_pairs
    )

    seen_keys: set[Zhi] = set()
    for name, z in mu_zhis:
        if z in seen_keys:
            continue
        cangs = _yongshen_in_zhi_canggan(z, day_master)
        if not cangs:
            continue
        seen_keys.add(z)
        # 库内含财/官
        canggan_str = ",".join(f"{c[0]}({c[1]})" for c in cangs)
        if has_chong_xing_on_mu:
            desc = f"{name}{z}库藏 {canggan_str} 财官 + 有冲刑打开 → 墓库做功"
            score = 0.65
        else:
            desc = f"{name}{z}库藏 {canggan_str} 财官 (未冲刑→关库)"
            score = 0.40
        out.append(ZuogongPath(
            type="墓", chain=[z],
            description=desc,
            strength=Magnitude(ordinal="中" if score >= 0.6 else "弱", score=score),
            layer_count=1 if score >= 0.6 else 0,
        ))
    return out


# ============================================================
# 6. 复合 + 主入口
# ============================================================

def evaluate_zuogong(bazi: Bazi, tiyong) -> list[ZuogongPath]:
    """段派 6 种做功扫描入口。

    输出排序：按 strength.score 降序，同 score 按 type 字典序。
    """
    day_master = bazi.day_master
    paths: list[ZuogongPath] = []

    paths.extend(detect_zhi_paths(bazi, day_master))
    paths.extend(detect_gan_paths(bazi, day_master))
    paths.extend(detect_hua_paths(bazi, day_master))
    paths.extend(detect_shengxie_paths(bazi, day_master))
    paths.extend(detect_sanhe_paths(bazi, day_master))
    paths.extend(detect_mu_paths(bazi, day_master))

    # 去重：同类型同 chain 的路径合并
    dedup: dict[tuple[str, tuple[str, ...]], ZuogongPath] = {}
    for p in paths:
        key = (p.type, tuple(sorted(p.chain)))
        if key not in dedup:
            dedup[key] = p
        else:
            # 取强度更高者
            if p.strength.score > dedup[key].strength.score:
                dedup[key] = p
    paths = list(dedup.values())
    paths.sort(key=lambda p: (-p.strength.score, p.type))

    # 复合识别：≥2 种不同 type 的有效路径 → 增加一条 "复合" path 标记
    valid_types = {p.type for p in paths if p.layer_count >= 1}
    if len(valid_types) >= 3:
        # 复合做功（M1-D-014）
        comp_chain = []
        for p in paths[:3]:
            comp_chain.extend(p.chain)
        paths.append(ZuogongPath(
            type="复合",
            chain=comp_chain[:6],
            description=f"复合做功 = {' + '.join(sorted(valid_types))} 多种叠加（M1-D-014）",
            strength=Magnitude(ordinal="强", score=0.85),
            layer_count=0,  # 复合不计入独立层数，只是标记
        ))

    return paths


def calc_layer_count(paths: list[ZuogongPath], bazi: Bazi) -> int:
    """计算总做功层数（段派 M1-D-173）。

    段派核心理念：层数 = 命局内"被有效做功的用神数量"。

    严格定义（避免过度计数）：
    1. 用神字符 = **透出天干**的财/官杀 + **主气支**为财/官杀
       - 中气/余气藏干用神不独立成神（M1-D-228）
       - 透出 = 干上明出现该字
    2. 一个 用神字符 被 ≥1 条有效 path 涉及 = 1 层
    3. 上限 4

    实务：
    - C-2026-001 (壬子日): 戊七杀 + 丑主气己正官 = 2 层
    - C-2026-002 (戊辰日): 壬偏财 = 1 层
    - C-2026-014 (乙亥日): 庚正官 + 辛七杀 + 戌主气戊正财 ≈ 3 (段派可能视为 杀印相生 1 层)
    - C-2026-011 (丁丑日): 癸七杀 + 酉主气辛偏财 ≈ 2
    - C-2026-012 (丙申日): 壬癸官杀 + 申主气庚偏财 ≈ 2

    返回：layer_count ∈ [0, 4]
    """
    day_master = bazi.day_master

    # 主气支用神
    main_qi_user_zhis: set[Zhi] = set()
    for _, zhi in bazi.all_zhis():
        if zhi_role_to_day(zhi, day_master) in ("财", "官杀"):
            main_qi_user_zhis.add(zhi)

    # 透出干用神
    tou_user_gans: set[Gan] = set()
    for _, gan in bazi.all_gans():
        if gan == day_master:
            continue
        if gan_role_to_day(gan, day_master) in ("财", "官杀"):
            tou_user_gans.add(gan)

    # 收集 engage 的 用神字符
    engaged_chars: set[str] = set()
    for p in paths:
        if p.layer_count <= 0:
            continue
        if p.type == "复合":
            continue
        for c in p.chain:
            if not isinstance(c, str) or len(c) != 1:
                continue
            if c in tou_user_gans:
                engaged_chars.add(c)
            elif c in main_qi_user_zhis:
                engaged_chars.add(c)

    layers = len(engaged_chars)
    # TODO(track-A): 段派"杀印相生"主结构整合（M1-D-028）应将官杀类
    # 用神字符合并为 1，但简单合并会破坏 A-001（戊+丑 同为官杀但
    # 各自独立做功）。需更精细的"是否被同一印化杀链吸收"判定。
    # 暂保持字符级计数，A-003（C-2026-014, 19岁未显的杀印格）将报告
    # layer=3 而非期望的 1，差异写入 PR notes。

    # 注意：过河拆桥 (M1-D-171) 仅在 has_guoheqiaoqiao 标记上记录，
    # 不再直接 +1 层（避免与"engaged_chars"重复加权）。
    # 实际富贵层级在 evaluator.py 的 wealth_ceiling 折算中体现。

    return min(layers, 4) if layers >= 1 else 0


def detect_guoheqiaoqiao(paths: list[ZuogongPath]) -> bool:
    """过河拆桥结构判定（M1-D-171）。

    简化：原局同时存在 食伤生财 + 财生官 的 生泄链 = 候选成立。
    """
    has_food_money = any(p.type == "生泄" and "[食伤生财]" in p.description
                         for p in paths if p.layer_count >= 1)
    has_money_official = any(p.type == "生泄" and "[财生官]" in p.description
                             for p in paths if p.layer_count >= 1)
    return has_food_money and has_money_official


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    from engine.predicates.types import _default_canggan_for
    from engine.energy.tiyong import evaluate_tiyong

    cases = {
        "C-2026-001": ("庚", "申", "戊", "寅", "壬", "子", "辛", "丑"),
        "C-2026-002": ("壬", "戌", "庚", "戌", "戊", "辰", "丙", "辰"),
        "C-2026-014": ("丙", "戌", "庚", "子", "乙", "亥", "辛", "巳"),
        "C-2026-011": ("乙", "丑", "乙", "酉", "丁", "丑", "癸", "卯"),
        "C-2026-012": ("壬", "戌", "癸", "丑", "丙", "申", "壬", "辰"),
    }
    for cid, parts in cases.items():
        b = Bazi(
            年柱=GanZhi(parts[0], parts[1]),
            月柱=GanZhi(parts[2], parts[3]),
            日柱=GanZhi(parts[4], parts[5]),
            时柱=GanZhi(parts[6], parts[7]),
        )
        b.藏干 = _default_canggan_for(b)
        ty = evaluate_tiyong(b)
        paths = evaluate_zuogong(b, ty)
        layers = calc_layer_count(paths, b)
        print(f"\n=== {cid} 做功扫描 ===")
        for p in paths:
            print(f"  [{p.type}](layer={p.layer_count} score={p.strength.score:.2f}) "
                  f"{p.description}")
        print(f"  → layer_count = {layers}")

    print("\n[OK] zuogong smoke 通过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
