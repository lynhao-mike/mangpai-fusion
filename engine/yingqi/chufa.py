"""engine/yingqi/chufa.py · v1.2 D3 任派 · 6 触发引擎

严格按 04-gate-protocol.md § 5.1 实现 6 大触发：

    1. 本字到       —— 流年地支或天干 = 原局某关键字
    2. 伏吟         —— 流年柱完全等于原局某柱
    3. 合冲引动     —— 流年支与原局支 / 大运支构成 合 / 冲 / 刑 / 穿
    4. 墓库开闭     —— 辰戌丑未墓库被流年/大运冲刑 → 开库应
    5. 藏干透出     —— 流年天干 = 原局某支藏干（"原本不透 → 现在透"）
    6. 倒象成立     —— 用神被多重相反作用（任派 §10 必凶铁律）

每个 detect_* 函数返回 list[TriggerEvent]（可能 0 / 1 / 多个）。
detect_all_triggers 汇总，pick_primary_trigger 按 04 § 5.2 优先级挑主。

倒象判定（任派 §10）—— 增量法：
  对比 baseline（仅原局）vs active（原局+大运+流年）的关系类型集，
  仅当大运/流年新增 ≥ 2 种新关系类型 + 生克合三态齐 → 倒象凶应。
  这避免对原局本就矛盾的命过敏。

作者：Track-C
"""
from __future__ import annotations

from typing import Optional

from engine.predicates.cycles import (
    get_dayun_at_year,
    liunian_ganzhi,
)
from engine.predicates.ganzhi import (
    gan_to_wuxing,
    get_canggan,
    zhi_to_wuxing,
)
from engine.predicates.relations import (
    gan_he,
    zhi_chong,
    zhi_chuan,
    zhi_liuhe,
    zhi_sanhe,
    zhi_xing,
)
from engine.predicates.tou_cang import is_canggan
from engine.predicates.types import (
    Bazi,
    DayunStep,
    GanZhi,
    ParsedInput,
    ZHI_CANGGAN_TABLE,
    GAN_LIST,
    ZHI_LIST,
)
from engine.predicates.wuxing import wuxing_ke, wuxing_sheng

from engine.yingqi.types import TriggerEvent, TRIGGER_PRIORITY


# ============================================================
# 辅助：取大运（容错版，起运前返回 None）
# ============================================================

def _get_dayun_step_safe(parsed: ParsedInput, year: int) -> Optional[DayunStep]:
    birth_year = int((parsed.birth or {}).get("公历年") or
                     parsed.dayun.起运年 - int(parsed.dayun.起运岁))
    try:
        return get_dayun_at_year(parsed.dayun, birth_year, year)
    except (ValueError, IndexError):
        return None


# ============================================================
# 1. 本字到（detect_benzi_dao）
# ============================================================

def detect_benzi_dao(
    parsed: ParsedInput, year: int, key_chars: list[str]
) -> list[TriggerEvent]:
    """流年地支或天干 = 原局某关键字。

    注：04 § 5.1 触发 1 的标准定义是"流年地支 = 原局某关键字"，
    但合理扩展到"流年天干 = 原局某关键字"（任派"本字到"含天干）。
    """
    ln = liunian_ganzhi(year)
    out: list[TriggerEvent] = []
    seen_chars: set[str] = set()

    for c in key_chars:
        if c not in seen_chars:
            if ln.gan == c:
                seen_chars.add(c)
                out.append(TriggerEvent(
                    type="本字到",
                    description=f"流年{ln} 的天干 {c} = 原局关键字",
                    target_chars=[c],
                ))
                continue
            if ln.zhi == c:
                seen_chars.add(c)
                out.append(TriggerEvent(
                    type="本字到",
                    description=f"流年{ln} 的地支 {c} = 原局关键字",
                    target_chars=[c],
                ))
    return out


# ============================================================
# 2. 伏吟（detect_fuyin）
# ============================================================

def detect_fuyin(
    parsed: ParsedInput, year: int
) -> list[TriggerEvent]:
    """流年柱 = 原局某柱（干支同字）。

    扩展：大运柱 = 原局某柱也算（"大运伏吟"）。
    """
    ln = liunian_ganzhi(year)
    out: list[TriggerEvent] = []

    pillar_pairs = parsed.bazi.all_pillars()
    for name, pillar in pillar_pairs:
        if pillar.gan == ln.gan and pillar.zhi == ln.zhi:
            out.append(TriggerEvent(
                type="伏吟",
                description=f"流年{ln} 与原局{name} 完全伏吟",
                target_chars=[ln.gan, ln.zhi],
            ))
            return out  # 同一年最多 1 条柱级伏吟

    # 大运柱伏吟原局
    dy = _get_dayun_step_safe(parsed, year)
    if dy is not None:
        for name, pillar in pillar_pairs:
            if pillar.gan == dy.干支.gan and pillar.zhi == dy.干支.zhi:
                out.append(TriggerEvent(
                    type="伏吟",
                    description=f"大运{dy.干支} 与原局{name} 伏吟",
                    target_chars=[dy.干支.gan, dy.干支.zhi],
                ))
                break
    return out


# ============================================================
# 3. 合冲引动（detect_hechong）
# ============================================================

def detect_hechong(
    parsed: ParsedInput, year: int, key_chars: list[str]
) -> list[TriggerEvent]:
    """流年与原局/大运构成合/冲/刑/穿引动关键字。

    判定路径（04 § 5.1 触发 3）：
        a) 流年支 vs 原局支：六合 / 半三合 / 冲 / 刑 / 穿 → 引动该支
        b) 流年支 vs 大运支：同上
        c) 流年干 vs 原局干：五合
        d) 大运支 vs 原局支：同 a（大运的"动事"也算 L3 的辅助）
        e) 解合解冲：原局有合，流年来冲；原局有冲，流年来合
    """
    ln = liunian_ganzhi(year)
    dy = _get_dayun_step_safe(parsed, year)
    out: list[TriggerEvent] = []
    seen_descriptions: set[str] = set()  # 去重

    bazi_zhis = parsed.bazi.all_zhis()
    bazi_gans = parsed.bazi.all_gans()
    bazi_pillar_names = ("年", "月", "日", "时")

    def _add(t: TriggerEvent) -> None:
        if t.description not in seen_descriptions:
            seen_descriptions.add(t.description)
            out.append(t)

    # a) 流年支 vs 原局支
    for name, zhi in bazi_zhis:
        rel = _classify_zhi_relation(ln.zhi, zhi)
        if rel is None:
            continue
        # 仅当涉及 key_char 才计为关键字相关引动
        if zhi in key_chars or ln.zhi in key_chars:
            _add(TriggerEvent(
                type="合冲引动",
                description=f"流年{ln.zhi} 与原局{name}{zhi} {rel}",
                target_chars=list(dict.fromkeys([ln.zhi, zhi])),
            ))

    # b) 流年支 vs 大运支
    if dy is not None:
        rel = _classify_zhi_relation(ln.zhi, dy.干支.zhi)
        if rel is not None:
            _add(TriggerEvent(
                type="合冲引动",
                description=f"流年{ln.zhi} 与大运{dy.干支.zhi} {rel}",
                target_chars=list(dict.fromkeys([ln.zhi, dy.干支.zhi])),
            ))

    # c) 流年干 vs 原局干（天干五合）
    for name, gan in bazi_gans:
        gh = gan_he(ln.gan, gan)
        if gh is not None:
            if gan in key_chars or ln.gan in key_chars:
                _add(TriggerEvent(
                    type="合冲引动",
                    description=(
                        f"流年{ln.gan} 与原局{name}干{gan} 合化{gh[0]}"
                    ),
                    target_chars=[ln.gan, gan],
                ))

    # 流年干 vs 大运干
    if dy is not None:
        gh = gan_he(ln.gan, dy.干支.gan)
        if gh is not None:
            _add(TriggerEvent(
                type="合冲引动",
                description=f"流年{ln.gan} 与大运{dy.干支.gan} 合化{gh[0]}",
                target_chars=[ln.gan, dy.干支.gan],
            ))

    # d) 大运支 vs 原局支（核心：大运也"动事"）
    if dy is not None:
        for name, zhi in bazi_zhis:
            rel = _classify_zhi_relation(dy.干支.zhi, zhi)
            if rel is None:
                continue
            if zhi in key_chars or dy.干支.zhi in key_chars:
                _add(TriggerEvent(
                    type="合冲引动",
                    description=f"大运{dy.干支.zhi} 与原局{name}{zhi} {rel}",
                    target_chars=list(dict.fromkeys([dy.干支.zhi, zhi])),
                ))

    # e) 解合解冲（原局两支合 + 流年冲；原局两支冲 + 流年合）
    n = len(bazi_zhis)
    for i in range(n):
        for j in range(i + 1, n):
            zi = bazi_zhis[i][1]
            zj = bazi_zhis[j][1]
            if zi == zj:
                continue
            # 原局合 + 流年冲
            if zhi_liuhe(zi, zj) is not None:
                if zhi_chong(ln.zhi, zi) or zhi_chong(ln.zhi, zj):
                    _add(TriggerEvent(
                        type="合冲引动",
                        description=(
                            f"解合：原局{zi}{zj}六合 + 流年{ln.zhi} 冲开"
                        ),
                        target_chars=list(dict.fromkeys([zi, zj, ln.zhi])),
                    ))
            # 原局冲 + 流年合
            if zhi_chong(zi, zj):
                if zhi_liuhe(ln.zhi, zi) is not None or \
                   zhi_liuhe(ln.zhi, zj) is not None:
                    _add(TriggerEvent(
                        type="合冲引动",
                        description=(
                            f"解冲：原局{zi}{zj}六冲 + 流年{ln.zhi} 合住"
                        ),
                        target_chars=list(dict.fromkeys([zi, zj, ln.zhi])),
                    ))
    return out


def _classify_zhi_relation(a: str, b: str) -> Optional[str]:
    """返回两支的关系名（"六合" / "半三合" / "冲" / "刑" / "穿"），无则 None。"""
    if a == b:
        return None
    if zhi_liuhe(a, b) is not None:
        return "六合"
    if zhi_sanhe([a, b]) is not None:
        return "半三合"
    if zhi_chong(a, b):
        return "冲"
    if zhi_xing(a, b) is not None:
        return "刑"
    if zhi_chuan(a, b):
        return "穿"
    return None


# ============================================================
# 4. 墓库开闭（detect_muku）
# ============================================================

# 辰戌丑未的"库藏五行"（用于判断"该库装的是不是关键字"）
_KU_TO_WUXING: dict[str, str] = {
    "辰": "水",  # 申子辰水库
    "戌": "火",  # 寅午戌火库
    "丑": "金",  # 巳酉丑金库
    "未": "木",  # 亥卯未木库
}


def detect_muku(
    parsed: ParsedInput, year: int, key_chars: list[str]
) -> list[TriggerEvent]:
    """墓库开闭：原局有库 + 流年/大运冲刑该库 → 开库应。

    04 § 5.1 触发 4 简化定义：流年地支 = 辰戌丑未 + 大运冲该库 → 开库。
    扩展：原局支为辰戌丑未 + 流年/大运冲刑该库（更普遍的"开库"场景）。
    """
    ln = liunian_ganzhi(year)
    dy = _get_dayun_step_safe(parsed, year)
    out: list[TriggerEvent] = []

    bazi_zhis = parsed.bazi.all_zhis()

    # 场景 A：流年地支 = 库 + 大运冲（04 契约示例）
    if ln.zhi in _KU_TO_WUXING and dy is not None:
        if zhi_chong(ln.zhi, dy.干支.zhi):
            out.append(TriggerEvent(
                type="墓库开闭",
                description=f"流年{ln.zhi}（{_KU_TO_WUXING[ln.zhi]}库）被大运{dy.干支.zhi}冲开",
                target_chars=[ln.zhi, dy.干支.zhi],
            ))

    # 场景 B：原局某支 = 库 + 流年/大运冲刑该库 + 库藏关键字
    for name, zhi in bazi_zhis:
        if zhi not in _KU_TO_WUXING:
            continue
        # 检查库内是否藏关键字
        cangs_in_ku = [g for g, _, _ in ZHI_CANGGAN_TABLE.get(zhi, [])]
        key_in_ku = [c for c in cangs_in_ku if c in key_chars]
        if not key_in_ku:
            continue

        opened_by: list[str] = []
        # 流年冲 / 刑
        if zhi_chong(ln.zhi, zhi):
            opened_by.append(f"流年{ln.zhi}冲")
        elif zhi_xing(ln.zhi, zhi) is not None:
            opened_by.append(f"流年{ln.zhi}刑")
        # 大运冲 / 刑
        if dy is not None:
            if zhi_chong(dy.干支.zhi, zhi):
                opened_by.append(f"大运{dy.干支.zhi}冲")
            elif zhi_xing(dy.干支.zhi, zhi) is not None:
                opened_by.append(f"大运{dy.干支.zhi}刑")

        if opened_by:
            out.append(TriggerEvent(
                type="墓库开闭",
                description=(
                    f"原局{name}{zhi}（藏 {','.join(cangs_in_ku)}）"
                    f"含关键字 {','.join(key_in_ku)}，被 {','.join(opened_by)} 开库"
                ),
                target_chars=list(dict.fromkeys([zhi, *key_in_ku])),
            ))
        # 库被合住（合而不化）= 闭库 = 不应（不输出，记录为 debug 即可）

    return out


# ============================================================
# 5. 藏干透出（detect_canggan_tou）
# ============================================================

def detect_canggan_tou(
    parsed: ParsedInput, year: int, key_chars: list[str]
) -> list[TriggerEvent]:
    """流年/大运 把原局某支藏干透出（且原本不透）。

    任派核心信号：藏干透出 = 隐藏意图浮现。
    """
    ln = liunian_ganzhi(year)
    dy = _get_dayun_step_safe(parsed, year)
    out: list[TriggerEvent] = []

    bazi = parsed.bazi
    seen_chars: set[str] = set()

    # 在 bazi 已透天干列表
    bazi_gans = {gan for _, gan in bazi.all_gans()}

    def _check_tou(transparent_gan: str, tou_source: str) -> None:
        if transparent_gan in seen_chars:
            return
        if transparent_gan in bazi_gans:
            return  # 原局已透 → 不算"新透出"
        if transparent_gan not in key_chars:
            return
        # 找该 transparent_gan 藏在原局哪些支
        canggan_palaces = is_canggan(transparent_gan, bazi)
        if not canggan_palaces:
            return
        seen_chars.add(transparent_gan)
        out.append(TriggerEvent(
            type="藏干透出",
            description=(
                f"{tou_source} 透出原局 {','.join(canggan_palaces)} "
                f"藏干 {transparent_gan}（原本不透）"
            ),
            target_chars=[transparent_gan],
        ))

    # 流年天干透出
    _check_tou(ln.gan, f"流年{ln}")

    # 大运天干透出
    if dy is not None:
        _check_tou(dy.干支.gan, f"大运{dy.干支}")

    return out


# ============================================================
# 6. 倒象成立（detect_daoxiang）
# ============================================================
# 任派 §10：又制又生又合又冲成矛盾 = 倒象 → 必凶
#
# 增量法：
#   baseline = 仅原局对用神的关系集
#   active   = 原局 + 大运 + 流年对用神的关系集
#   delta = active - baseline（新增的关系类型）
#   倒象成立条件（任一）：
#     A. delta ≥ 2 种新类型 + 生克合三态齐全 + active 累计 ≥ 4 种类型
#     B. delta 中含凶煞（冲/穿/刑/天干克/地支克）+ active 累计 ≥ 4 种
#     C. 增量次数 ≥ 4（多重打击兜底）

_XIONG_REL_TYPES: set[str] = {"冲", "穿", "刑", "天干克", "地支克"}
_KE_TYPES: set[str] = {"天干克", "地支克", "冲", "穿", "刑"}
_SHENG_TYPES: set[str] = {"天干生", "地支生"}
_HE_TYPES: set[str] = {"六合", "半三合", "天干合"}


def _count_relations_to(
    target: str, gans: list[str], zhis: list[str]
) -> dict[str, int]:
    """以 target 为参照，统计 gans/zhis 对 target 的各种关系次数。"""
    rc: dict[str, int] = {}

    is_target_gan = target in GAN_LIST
    is_target_zhi = target in ZHI_LIST
    target_wx = (
        gan_to_wuxing(target) if is_target_gan
        else (zhi_to_wuxing(target) if is_target_zhi else None)
    )
    if target_wx is None:
        return rc

    # 干侧
    for g in gans:
        if g == target:
            continue
        if is_target_gan:
            # 天干合
            if gan_he(g, target) is not None:
                rc["天干合"] = rc.get("天干合", 0) + 1
        # 五行生克（不分干支身份）
        g_wx = gan_to_wuxing(g)
        if wuxing_ke(g_wx, target_wx):
            rc["天干克"] = rc.get("天干克", 0) + 1
        if wuxing_sheng(g_wx, target_wx):
            rc["天干生"] = rc.get("天干生", 0) + 1

    # 支侧
    for z in zhis:
        if z == target:
            continue
        z_wx = zhi_to_wuxing(z)
        if is_target_zhi:
            # 合 / 冲 / 刑 / 穿（地支专属）
            rel = _classify_zhi_relation(z, target)
            if rel is not None:
                rc[rel] = rc.get(rel, 0) + 1
        # 五行生克
        if wuxing_ke(z_wx, target_wx):
            rc["地支克"] = rc.get("地支克", 0) + 1
        if wuxing_sheng(z_wx, target_wx):
            rc["地支生"] = rc.get("地支生", 0) + 1

    return rc


def detect_daoxiang(
    parsed: ParsedInput, year: int, yong_shen_chars: list[str]
) -> list[TriggerEvent]:
    """倒象成立判定（增量法）。"""
    ln = liunian_ganzhi(year)
    dy = _get_dayun_step_safe(parsed, year)
    bazi = parsed.bazi

    base_gans = [g for _, g in bazi.all_gans()]
    base_zhis = [z for _, z in bazi.all_zhis()]
    active_gans = list(base_gans)
    active_zhis = list(base_zhis)
    if dy is not None:
        active_gans.append(dy.干支.gan)
        active_zhis.append(dy.干支.zhi)
    active_gans.append(ln.gan)
    active_zhis.append(ln.zhi)

    out: list[TriggerEvent] = []
    seen_targets: set[str] = set()

    bazi_chars: set[str] = set(base_gans) | set(base_zhis)
    # 加原局藏干（用神可能藏在支中）
    for _, zhi in bazi.all_zhis():
        for cg, _, _ in ZHI_CANGGAN_TABLE.get(zhi, []):
            bazi_chars.add(cg)

    for ys in yong_shen_chars:
        if ys in seen_targets:
            continue
        # 仅检查在原局的用神
        if ys not in bazi_chars:
            continue
        seen_targets.add(ys)

        baseline = _count_relations_to(ys, base_gans, base_zhis)
        active = _count_relations_to(ys, active_gans, active_zhis)

        delta_types = set(active.keys()) - set(baseline.keys())
        delta_count = 0
        for k, v in active.items():
            delta_count += max(0, v - baseline.get(k, 0))

        n_distinct = len([r for r in active if active[r] >= 1])
        has_real_sheng = bool(set(active.keys()) & _SHENG_TYPES)
        has_real_ke = bool(set(active.keys()) & _KE_TYPES)
        has_he = bool(set(active.keys()) & _HE_TYPES)

        delta_has_xiong = bool(delta_types & _XIONG_REL_TYPES)

        cond_A = (
            len(delta_types) >= 2
            and has_real_sheng and has_real_ke and has_he
            and n_distinct >= 4
        )
        cond_B = delta_has_xiong and n_distinct >= 4
        cond_C = delta_count >= 4

        is_dao = cond_A or cond_B or cond_C
        if not is_dao:
            continue

        reason_tag = (
            "三态矛盾(A)" if cond_A
            else ("凶煞引动(B)" if cond_B else "多重打击(C)")
        )
        out.append(TriggerEvent(
            type="倒象成立",
            description=(
                f"用神 {ys} 倒象 [{reason_tag}]：大运/流年新增 {len(delta_types)} 种新关系"
                f"({','.join(sorted(delta_types)) or '无'})，累计 {n_distinct} 种"
                f"，增量次数 {delta_count}"
            ),
            target_chars=[ys],
            is_xiong=True,
        ))

    return out


# ============================================================
# 主入口：6 触发并行检测 + 主触发挑选
# ============================================================

def detect_all_triggers(
    parsed: ParsedInput,
    year: int,
    key_chars: list[str],
    yong_shen_chars: Optional[list[str]] = None,
) -> list[TriggerEvent]:
    """运行 6 大触发，返回所有触发事件（去重；未触发的不返回）。

    yong_shen_chars: 倒象判定专用。若 None，fallback 到 key_chars + 日干。
    """
    if yong_shen_chars is None:
        yong_shen_chars = list(key_chars[:4]) + [parsed.bazi.day_master]

    triggers: list[TriggerEvent] = []
    triggers.extend(detect_benzi_dao(parsed, year, key_chars))
    triggers.extend(detect_fuyin(parsed, year))
    triggers.extend(detect_hechong(parsed, year, key_chars))
    triggers.extend(detect_muku(parsed, year, key_chars))
    triggers.extend(detect_canggan_tou(parsed, year, key_chars))
    triggers.extend(detect_daoxiang(parsed, year, yong_shen_chars))
    return triggers


def pick_primary_trigger(
    triggers: list[TriggerEvent]
) -> Optional[TriggerEvent]:
    """按 04 § 5.2 优先级挑主触发。

    优先级（高 → 低）：
        倒象成立 > 伏吟 > 本字到 ~ 合冲引动 > 墓库开闭 > 藏干透出
    同优先级按出现顺序保留第一个。
    """
    if not triggers:
        return None
    # 排序 by priority asc，stable
    sorted_t = sorted(
        triggers,
        key=lambda t: TRIGGER_PRIORITY.get(t.type, 99),
    )
    return sorted_t[0]


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    from tests.fixtures.cases import load_case

    # C-2026-001
    parsed = load_case("C-2026-001-庚申戊寅壬子辛丑")
    # 婚姻关键字（粗判，避免依赖 Track-A energy）
    keys = ["丙", "丁", "巳", "午", "子"]
    yong = ["丙", "子"]

    print("\n=== C-2026-001 婚姻 2005 ===")
    trigs = detect_all_triggers(parsed, 2005, keys, yong)
    by_type = {}
    for t in trigs:
        by_type.setdefault(t.type, []).append(t)
    for typ, ts in by_type.items():
        print(f"  {typ}: {len(ts)}")
        for t in ts[:2]:
            print(f"    · {t.description}")
    primary = pick_primary_trigger(trigs)
    print(f"  primary: {primary.type if primary else None}")
    # 2005 乙酉：乙合年干庚 + 大运庚辰半合日支子？申子辰半合 → 合冲引动应触发
    assert any(t.type == "合冲引动" for t in trigs), "2005 应触发合冲引动"

    print("\n=== C-2026-001 婚姻 2026（丙午年）===")
    trigs = detect_all_triggers(parsed, 2026, keys, yong)
    by_type = {}
    for t in trigs:
        by_type.setdefault(t.type, []).append(t)
    for typ, ts in by_type.items():
        print(f"  {typ}: {len(ts)}")
    # 丙午：丙=本字 + 午=本字 + 午冲子 → 本字到 + 合冲
    assert any(t.type == "本字到" for t in trigs), "2026 丙午应触发本字到"
    assert any(t.type == "合冲引动" for t in trigs), "2026 午冲子应触发合冲"

    print("\n=== C-2026-001 婚姻 2013 ===")
    trigs = detect_all_triggers(parsed, 2013, keys, yong)
    by_type = {}
    for t in trigs:
        by_type.setdefault(t.type, []).append(t)
    for typ, ts in by_type.items():
        print(f"  {typ}: {len(ts)}")
    # 2013 癸巳：巳=本字 + 大运辛巳 + 巳寅相邻
    assert any(t.type == "本字到" for t in trigs), "2013 癸巳应触发本字到（巳）"

    # 倒象（举例：母 2020 庚子，使用印=辛庚 子作 yong shen）
    print("\n=== C-2026-001 母 2020（庚子）===")
    yong_mu = ["辛", "庚", "子"]
    trigs = detect_all_triggers(parsed, 2020, yong_mu, yong_mu)
    by_type = {}
    for t in trigs:
        by_type.setdefault(t.type, []).append(t)
    for typ, ts in by_type.items():
        print(f"  {typ}: {len(ts)}")
        for t in ts[:1]:
            print(f"    · {t.description[:80]}")
    # 庚子年 = 流年柱伏吟年柱（庚申）的天干？年柱=庚申，流年=庚子 → 不完全伏吟
    # 但庚 = 本字 + 子 = 本字（日支）

    print("\n=== C-2026-014 学业 2024 ===")
    parsed014 = load_case("C-2026-014-丙戌庚子乙亥辛巳")
    keys_xue = ["庚", "辛", "申", "酉", "壬", "癸", "丙", "丁"]
    trigs = detect_all_triggers(parsed014, 2024, keys_xue, ["壬", "癸"])
    by_type = {}
    for t in trigs:
        by_type.setdefault(t.type, []).append(t)
    for typ, ts in by_type.items():
        print(f"  {typ}: {len(ts)}")
        for t in ts[:1]:
            print(f"    · {t.description[:80]}")

    print("\n[OK] chufa smoke 全过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
