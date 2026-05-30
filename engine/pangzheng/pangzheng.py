"""engine/pangzheng/pangzheng.py · v1.2 D4 高派旁证主入口

按 03-findings-schema.md § 八 + 08-agent-handoff.md § 二 D 实现。

核心 API：
    support_with_shensha(parsed, energy=None, picture=None, gates=None) -> SupportFindings

设计原则（03 § 八）：
    "D4 的 boost 只能**增强**已有 D1/D2/D3 结论，不能**新提**结论。
     这是'旁证'二字的本意。"

主流程：
    1. 自动加载 ParsedInput.shensha（若空则从 input.md 解析）
    2. 遍历神煞 → 按 shensha_lib 规则映射到各 domain → ShenshaSupport
    3. 评估学业辅佐（词馆/学堂/文昌/天乙）→ CiguanXuetang
    4. 评估健康灾厄（GP-CH 系列）→ HealthFinding
    5. 计算整体 confidence
    6. 收集 evidence + 返回 SupportFindings

作者：Track-D
"""
from __future__ import annotations

from typing import Optional

from engine.energy.types import (
    Confidence,
    Evidence,
    Magnitude,
)
from engine.predicates.shensha import get_shensha_at, has_shensha
from engine.predicates.types import ParsedInput

from engine.pangzheng.loader import attach_shensha
from engine.pangzheng.shensha_lib import (
    SHENSHA_RULES,
    evaluate_ciguan_xuetang,
    get_rule,
)
from engine.pangzheng.types import (
    CiguanXuetang,
    HealthFinding,
    ShenshaSupport,
    SupportFindings,
)


# ============================================================
# 一、神煞旁证扫描（核心）
# ============================================================

# 学业辅佐神煞（不再在 shensha_supports[education] 重复加 boost
# —— 它们由 CiguanXuetang 统一管理 + cap 0.10）
_EDUCATION_DEDUP_SHENSHA: tuple[str, ...] = (
    "词馆", "学堂", "文昌", "天乙贵人", "太极贵人",
)


def _scan_shensha_supports(
    parsed: ParsedInput,
) -> dict[str, list[ShenshaSupport]]:
    """扫描原局所有神煞，按 domain 聚合 ShenshaSupport。

    返回 {marriage: [...], career: [...], wealth: [...], health: [...], ...}

    特别处理：
      学业辅佐神煞（词馆/学堂/文昌/天乙/太极）的 education domain
      由 CiguanXuetang 统一管理（cap 0.10），此处不重复加。
    """
    out: dict[str, list[ShenshaSupport]] = {}

    # 取 ParsedInput.shensha 中所有神煞名 + 柱位
    shensha_dict = parsed.shensha or {}
    name_to_palaces: dict[str, list[str]] = {}
    for palace, names in shensha_dict.items():
        # 归一化 X支 → X柱
        normalized_palace = palace.replace("年支", "年柱").replace("月支", "月柱") \
            .replace("日支", "日柱").replace("时支", "时柱")
        for n in names:
            if not n or n in ("空亡", "—", "-"):
                continue
            name_to_palaces.setdefault(n, []).append(normalized_palace)

    # 对每个神煞名，查找规则库
    for name, palaces in name_to_palaces.items():
        canonical_name = _canonicalize_shensha_name(name)
        rule = get_rule(canonical_name)
        if rule is None:
            continue
        domains_map = rule.get("domains", {})
        for domain, props in domains_map.items():
            # 学业辅佐 dedup：跳过 education domain（由 CiguanXuetang 管）
            if (
                domain == "education"
                and canonical_name in _EDUCATION_DEDUP_SHENSHA
            ):
                continue
            boost = float(props.get("boost", 0.0))
            tags = list(props.get("tags", []))
            contribution = props.get("contribution", "")
            support = ShenshaSupport(
                name=canonical_name,
                palaces=palaces,  # type: ignore[arg-type]
                contribution=f"{contribution}（在 {','.join(palaces)}）",
                boost=boost,
                tags=tags,
            )
            out.setdefault(domain, []).append(support)
    return out


# 神煞别名归一化（输入"词馆贵人"等同于"词馆"等）
_ALIAS_MAP: dict[str, str] = {
    "词馆贵人": "词馆",
    "学堂贵人": "学堂",
    "文昌贵人": "文昌",
    "天厨贵人": "天厨",
    "天德": "天德贵人",
    "月德": "月德贵人",
    "国印贵人": "天乙贵人",  # 高派一些版本归为天乙类
    "福星贵人": "天乙贵人",  # 福星 = 贵人扶持
    "天罗地网": "羊刃",  # 牢狱象，简化映射到羊刃凶煞类
    "灾煞": "羊刃",  # 灾煞 = 凶煞类
    "亡神": "羊刃",  # 亡神 = 凶煞类
    "丧门": "羊刃",
    "孤辰": "孤鸾煞",  # 孤独类
    "寡宿": "孤鸾煞",
    "桃花": "红艳煞",  # 桃花一族
    "元辰": "羊刃",  # 元辰 = 凶
    "劫煞": "羊刃",  # 劫煞 = 凶
    "流霞": "血刃",  # 流霞 = 血光
    "十灵日": "天乙贵人",  # 十灵日 = 灵秀，归贵人类
}


def _canonicalize_shensha_name(name: str) -> str:
    """归一化神煞名（处理别名）。"""
    return _ALIAS_MAP.get(name, name)


# ============================================================
# 二、学业辅佐评估
# ============================================================

def _evaluate_education(parsed: ParsedInput) -> Optional[CiguanXuetang]:
    """评估词馆/学堂/文昌/天乙学业辅佐。"""
    shensha_dict = parsed.shensha or {}
    if not shensha_dict:
        return None

    result = evaluate_ciguan_xuetang(parsed)
    if result["boost"] == 0.0:
        return None  # 无任何学业辅佐 → 不输出
    return CiguanXuetang(
        has_ciguan=result["has_ciguan"],
        has_xuetang=result["has_xuetang"],
        has_wenchang=result["has_wenchang"],
        has_taiyi=result["has_taiyi"],
        contribution=result["contribution"],
        boost=result["boost"],
    )


# ============================================================
# 三、健康灾厄评估（高派 GP-CH-08~11）
# ============================================================

# 健康风险神煞
_HEALTH_RISK_SHENSHA: tuple[str, ...] = (
    "血刃", "羊刃", "童子煞", "孤鸾煞",
    "天罗地网", "灾煞", "亡神", "劫煞", "流霞",
)


def _evaluate_health(parsed: ParsedInput) -> list[HealthFinding]:
    """评估健康风险（GP-CH-08~11 寿元星 + 凶煞）。"""
    findings: list[HealthFinding] = []
    shensha_dict = parsed.shensha or {}
    if not shensha_dict:
        return findings

    # 1. 血刃 → 手术 / 外伤
    if has_shensha("血刃", parsed) or has_shensha("流霞", parsed):
        palaces = (
            get_shensha_at("血刃", parsed) + get_shensha_at("流霞", parsed)
        )
        findings.append(HealthFinding(
            organ="外伤/手术",
            risk_level=Magnitude(ordinal="弱", score=0.3),
            risk_years=[],  # 应期由 Track-C 给
            rationale=(
                f"血刃/流霞挂 {','.join(palaces)} → 一生有手术 / 外伤倾向；"
                f"应期需配合 Track-C 流年触发判定"
            ),
            evidence=[
                Evidence(rule_id="GP-CH-09", school="高",
                         description="血刃 = 手术 / 外伤神煞", weight=0.4),
            ],
        ))

    # 2. 羊刃 + 刑穿 → 下身伤残（GP-CH-08 第⑤条）
    if has_shensha("羊刃", parsed):
        palaces = get_shensha_at("羊刃", parsed)
        findings.append(HealthFinding(
            organ="下身/腿脚",
            risk_level=Magnitude(ordinal="弱", score=0.25),
            risk_years=[],
            rationale=(
                f"羊刃挂 {','.join(palaces)} → 阳刃为忌时主下身伤残 (GP-CH-08-5)；"
                f"应期看流年是否冲穿羊刃位"
            ),
            evidence=[
                Evidence(rule_id="GP-CH-08-5", school="高",
                         description="阳刃被刑穿 = 下身伤残", weight=0.45),
            ],
        ))

    # 3. 童子煞 → 幼年体弱
    if has_shensha("童子煞", parsed):
        findings.append(HealthFinding(
            organ="幼年体质",
            risk_level=Magnitude(ordinal="弱", score=0.2),
            risk_years=[],
            rationale="童子煞 = 童子身，主幼年体弱多病信号",
            evidence=[
                Evidence(rule_id="GP-BD-12", school="高",
                         description="童子煞 = 幼年体弱", weight=0.3),
            ],
        ))

    return findings


# ============================================================
# 四、置信度（D4 自身）
# ============================================================

def _compute_support_confidence(
    shensha_supports: dict[str, list[ShenshaSupport]],
    health_findings: list[HealthFinding],
    ciguan_xuetang: Optional[CiguanXuetang],
) -> Confidence:
    """D4 整体输出的 confidence。

    简化规则（与 06 § 三 一致）：
        - 神煞数量越多，sample_n 越大，posterior 越接近基础值
        - 基础 posterior = 0.65（旁证一般非铁断）
        - boost 总量越大，star 越高
    """
    n_supports = sum(len(v) for v in shensha_supports.values())
    n_findings = len(health_findings)
    has_edu = ciguan_xuetang is not None and ciguan_xuetang.boost > 0
    sample_n = n_supports + n_findings + (1 if has_edu else 0)

    posterior = 0.65
    if n_supports >= 5:
        posterior += 0.05
    if n_supports >= 10:
        posterior += 0.05
    if has_edu and ciguan_xuetang.boost >= 0.08:
        posterior += 0.05
    posterior = min(posterior, 0.85)  # D4 旁证 cap 0.85（不能高过铁断 D3）

    if posterior < 0.55:
        star = 2
    elif posterior < 0.70:
        star = 3
    elif posterior < 0.85:
        star = 4
    else:
        star = 5

    return Confidence(
        star=star,
        percent=round(posterior, 3),
        posterior=round(posterior, 3),
        variance=0.08,  # 旁证 variance 略高于 gate（不确定性更大）
        sample_n=sample_n,
    )


# ============================================================
# 五、Evidence 收集
# ============================================================

def _collect_evidence(
    shensha_supports: dict[str, list[ShenshaSupport]],
    health_findings: list[HealthFinding],
    ciguan_xuetang: Optional[CiguanXuetang],
) -> list[Evidence]:
    """从 shensha_supports + health_findings + ciguan 收集 evidence 链。"""
    out: list[Evidence] = []

    # 神煞 evidence（每条规则一个）
    seen_rules: set[str] = set()
    for domain, supports in shensha_supports.items():
        for s in supports:
            rule = get_rule(s.name)
            if rule is None:
                continue
            rid = rule.get("rule_id", f"GP-BD-{s.name}")
            if rid in seen_rules:
                continue
            seen_rules.add(rid)
            out.append(Evidence(
                rule_id=rid,
                school="高",
                description=f"{s.name} 旁证 [{domain}]: {s.contribution[:40]}",
                weight=abs(s.boost) * 5,  # boost 0.05 → weight 0.25
            ))

    # 学业 evidence
    if ciguan_xuetang and ciguan_xuetang.boost > 0:
        out.append(Evidence(
            rule_id="GP-XL-MIX",
            school="高",
            description=f"词馆/学堂综合: {ciguan_xuetang.contribution[:50]}",
            weight=ciguan_xuetang.boost * 5,
        ))

    # 健康 evidence（已有内嵌，不再外加）

    return out


# ============================================================
# 六、主入口
# ============================================================

def support_with_shensha(
    parsed: ParsedInput,
    energy: Optional[object] = None,
    picture: Optional[object] = None,
    gates: Optional[list] = None,
) -> SupportFindings:
    """D4 高派旁证主入口（08 § 二 D）。

    Args:
        parsed: ParsedInput（必需，含 bazi/dayun/shensha；shensha 缺失会自动加载）
        energy: 上游 D1 EnergyFindings（可选，用于 hash 追溯）
        picture: 上游 D2 PictureFindings（可选）
        gates:   上游 D3 GateResult 列表（可选）

    Returns:
        SupportFindings: D4 旁证产出
    """
    # 0. 自动补充 shensha（若 ParsedInput 没有）
    if not parsed.shensha:
        attach_shensha(parsed)

    # 1. 神煞旁证扫描
    shensha_supports = _scan_shensha_supports(parsed)

    # 2. 学业辅佐
    ciguan = _evaluate_education(parsed)

    # 3. 健康灾厄
    health = _evaluate_health(parsed)

    # 4. 置信度
    confidence = _compute_support_confidence(shensha_supports, health, ciguan)

    # 5. Evidence
    evidence = _collect_evidence(shensha_supports, health, ciguan)

    # 6. 上游 hash
    e_hash = energy.hash() if energy is not None and hasattr(energy, "hash") else ""
    p_hash = picture.hash() if picture is not None and hasattr(picture, "hash") else ""
    g_hash = ""
    if gates:
        # 取所有 gate hash 拼接的 hash（多事件场景）
        import hashlib
        s = "|".join(g.hash() for g in gates if hasattr(g, "hash"))
        g_hash = hashlib.sha256(s.encode()).hexdigest()[:16] if s else ""

    # 7. Debug
    debug = {
        "n_shensha_total": sum(len(v) for v in shensha_supports.values()),
        "n_domains_covered": len(shensha_supports),
        "domains_covered": sorted(shensha_supports.keys()),
        "has_ciguan_xuetang": ciguan is not None,
        "n_health_findings": len(health),
        "shensha_input_size": sum(len(v) for v in (parsed.shensha or {}).values()),
    }

    return SupportFindings(
        shensha_supports=shensha_supports,
        health_findings=health,
        ciguan_xuetang=ciguan,
        confidence=confidence,
        evidence=evidence,
        case_id=parsed.case_id,
        upstream_energy_hash=e_hash,
        upstream_picture_hash=p_hash,
        upstream_gate_hash=g_hash,
        debug_info=debug,
    )


# ============================================================
# smoke
# ============================================================

def _smoke() -> None:
    from tests.fixtures.cases import load_case

    print("\n" + "=" * 78)
    print("           Track-D D4 高派旁证 smoke 测试")
    print("=" * 78)

    # ---- C-2026-001 ----
    parsed = load_case("C-2026-001-乾-庚申戊寅壬子辛丑")
    attach_shensha(parsed)
    print(f"\n[C-001] shensha 加载: {len(parsed.shensha)} 柱")

    support = support_with_shensha(parsed)
    print(f"  神煞旁证 domains: {sorted(support.shensha_supports.keys())}")
    for dom in sorted(support.shensha_supports.keys()):
        names = [s.name for s in support.shensha_supports[dom]]
        boost = support.total_boost_for(dom)
        print(f"    [{dom}] {names} → total_boost={boost:.3f}")

    print(f"\n  健康风险 ({len(support.health_findings)}):")
    for h in support.health_findings:
        print(f"    · {h.organ} ({h.risk_level.ordinal}): {h.rationale[:50]}")

    if support.ciguan_xuetang:
        print(f"\n  词馆学堂: boost={support.ciguan_xuetang.boost:.3f}")

    print(f"\n  Confidence: ★{support.confidence.star} ({support.confidence.percent:.0%})")

    # 验收 D-001: 金舆在时柱 → boost marriage ≥ 0.04
    # 语义：金舆本身的贡献（ShenshaSupport.boost）≥ 0.04，且作用域含 marriage
    marriage_supports = support.shensha_supports.get("marriage", [])
    jinyu = next((s for s in marriage_supports if s.name == "金舆"), None)
    assert jinyu is not None, "C-001 marriage 应含金舆旁证"
    assert "时柱" in jinyu.palaces, f"金舆应在时柱：{jinyu.palaces}"
    assert jinyu.boost >= 0.04, f"D-001 金舆 boost 应 ≥ 0.04，实 {jinyu.boost:.3f}"
    marriage_boost_total = support.total_boost_for("marriage")
    print(f"\n[D-001 验证] 金舆 boost = {jinyu.boost:.3f}（在 {jinyu.palaces}）")
    print(f"  marriage 总 boost = {marriage_boost_total:.3f}（含负向神煞抵消）")
    print("  ✓ D-001 通过：金舆在时柱单条 boost ≥ 0.04")

    # 验收 D-003: 驿马 → boost 含"奔波/调动"标签
    career_supports = support.shensha_supports.get("career", [])
    yima = next((s for s in career_supports if s.name == "驿马"), None)
    assert yima is not None, "C-001 应有驿马旁证"
    assert any("奔波" in t or "调动" in t for t in yima.tags), \
        f"驿马 tags 应含'奔波/调动'：{yima.tags}"
    print(f"\n[D-003 验证] 驿马 tags = {yima.tags}")
    print("  ✓ D-003 通过：驿马含'奔波/调动'标签")

    # ---- C-2026-014 (学业案) ----
    parsed014 = load_case("C-2026-014-乾-丙戌庚子乙亥辛巳")
    attach_shensha(parsed014)
    print(f"\n[C-014] shensha 加载: {len(parsed014.shensha)} 柱")

    support014 = support_with_shensha(parsed014)
    edu_boost = support014.total_boost_for("education")
    print(f"  education total_boost = {edu_boost:.3f}")

    # 验收 D-002: 词馆+天乙×2 → boost 学业 ≤ 0.10
    print(f"\n[D-002 验证] C-014 education boost = {edu_boost:.3f}")
    assert edu_boost <= 0.10, f"D-002 应 ≤ 0.10（cap），实 {edu_boost:.3f}"
    if support014.ciguan_xuetang:
        print(f"  词馆: {support014.ciguan_xuetang.has_ciguan}, "
              f"天乙: {support014.ciguan_xuetang.has_taiyi}")
    print("  ✓ D-002 通过：词馆+天乙×2 boost 已 cap 到 ≤ 0.10")

    # 序列化 round-trip
    s = support.to_json()
    s2 = SupportFindings.from_json(s)
    assert s2.hash() == support.hash()
    print(f"\n  JSON round-trip OK · hash={support.hash()}")

    print("\n[OK] pangzheng smoke + D-001/002/003 验收全过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
