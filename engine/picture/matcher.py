"""engine/picture/matcher.py · v1.2 D2 杨派 · 画面合拍主入口

主入口：``match_picture(energy, parsed) -> PictureFindings``

编排子模块（见 07 § 四 W2 内部 DAG）：
    wubu      - 五步算命法
    wuhe      - 天干五合
    anyin     - 十神暗引 5 公式
    caifu     - 财富 7 等
    guanming  - 官命 9 取
    marriage  - 婚姻画像（修复 G2 关键）
    tiaohou   - 调候改运 6 维

上游约束（D1 → D2 一致性）：
- D1 wealth_ceiling 决定 caifu rank 自然区间
- D1 layer_count 影响 wubu Step 3 的层次描述
- 上游约束违反时 → 写 violations 并降级置信度

作者：Track-B
"""
from __future__ import annotations

from typing import Any, Optional, Union

from engine.domain.confidence import posterior_to_star as _shared_posterior_to_star
from engine.energy.types import (
    Confidence,
    EnergyFindings,
    Evidence,
)
from engine.picture.anyin import scan_anyin
from engine.picture.caifu import compute_caifu, compute_guanming
from engine.picture.marriage import build_marriage_picture
from engine.picture.tiaohou import build_tiaohou_advice
from engine.picture.types import (
    PictureFindings,
    WubuStep,
)
from engine.picture.wubu import run_wubu
from engine.picture.wuhe import scan_wuhe
from engine.predicates.ganzhi import gan_to_wuxing, zhi_to_wuxing
from engine.predicates.strength import calc_wuxing_strength
from engine.predicates.types import (
    Bazi,
    ParsedInput,
    Wuxing,
    adapt_parsed,
)


# ============================================================
# 活死五行（M2-Y-149..151）
# ============================================================

def _build_huosi_wuxing(bazi: Bazi) -> dict[str, str]:
    """活死五行简版判定。

    - 木：有水火土光 → 活木；只见金 → 死木
    - 金：有火 → 活金；无火 + 多水 → 寒金
    - 水：有温度（火虚透/丙）→ 活水；只在库中 → 死水
    """
    shi = calc_wuxing_strength(bazi)
    out: dict[str, str] = {}

    has_fire = shi.get("火", 0) > 0.05
    has_water = shi.get("水", 0) > 0.10
    has_earth = shi.get("土", 0) > 0.10
    has_metal = shi.get("金", 0) > 0.10
    has_wood = shi.get("木", 0) > 0.10

    # 木
    if has_wood:
        if has_water and has_fire and has_earth:
            out["木"] = "活木"
        elif has_metal and not has_fire:
            out["木"] = "死木"
        else:
            out["木"] = "活木" if has_water else "木"
    # 金
    if has_metal:
        if has_fire:
            out["金"] = "活金"
        elif not has_fire and has_water:
            out["金"] = "寒金"
        else:
            out["金"] = "金"
    # 水
    if has_water:
        if has_fire:
            out["水"] = "活水"
        elif has_earth and not has_fire:
            out["水"] = "死水"
        else:
            out["水"] = "水"
    # 火
    if has_fire:
        out["火"] = "火"
    # 土
    if has_earth:
        out["土"] = "土"

    return out


# ============================================================
# 行业指引（M2-Y-070, 071, 158）
# ============================================================

def _build_industry_pointers(
    bazi: Bazi,
    energy: EnergyFindings,
    huosi: dict[str, str],
    huangliang_finding: str,
) -> list[str]:
    """从 D1 + D2 综合给出行业指引。

    核心判定：
    - 天干透官印 + 官印相生 → 公门/国企
    - 天干透食伤 + 财 → 服务/技术/中介
    - 比劫旺 + 财 → 民营/合作
    - 印旺 + 食伤 → 教育/管理
    """
    pointers: list[str] = []
    huang = huangliang_finding or ""
    if "端国家饭碗" in huang or "皇粮" in huang:
        # 杨派"吃皇粮"标志
        pointers.append("公门/国企")
    if "民营" in huang or "合作" in huang:
        pointers.append("民营/合作")
    if "技术/销售" in huang:
        pointers.append("技术/服务")
    if "文教" in huang or "管理" in huang:
        pointers.append("文教/管理")

    # 杨派活死五行 → 行业方向
    # 活木 + 活水 → 教育/医疗/文化
    # 死木 + 火 → 加工/手工艺
    # 活金 + 火 → 矿产/珠宝/金融
    if huosi.get("木") == "活木" and huosi.get("水") in ("活水", "水"):
        pointers.append("教育/医疗/文化（活木+水）")
    if huosi.get("金") == "活金":
        pointers.append("矿产/珠宝/金融（活金有火）")
    if huosi.get("水") == "活水":
        pointers.append("流通/贸易/运输（活水）")

    # 去重 + 保序
    seen: set[str] = set()
    out: list[str] = []
    for p in pointers:
        if p not in seen:
            seen.add(p)
            out.append(p)

    # 保底
    if not out:
        out.append("综合服务（结构待回测）")
    return out


# ============================================================
# 上游一致性校验（D1 → D2）
# ============================================================

def _check_against_energy(
    energy: EnergyFindings,
    findings: PictureFindings,
) -> tuple[bool, list[str]]:
    """检查 PictureFindings 是否违背 D1 EnergyFindings 的 wealth_ceiling 等。"""
    violations: list[str] = []
    wc = energy.wealth_ceiling

    # 1) caifu.rank 必须在自然区间内（如已被钳到则不算 violation）
    from engine.picture.caifu import _wealth_rank_range
    rank_lo, rank_hi = _wealth_rank_range(wc)
    if findings.caifu and not (rank_lo <= findings.caifu.rank <= rank_hi):
        # 若 rationale 已声明"钳到"则放过
        if "钳到" not in findings.caifu.rationale:
            violations.append(
                f"caifu.rank={findings.caifu.rank} 超出 wealth_ceiling={wc} "
                f"自然区间 [{rank_lo},{rank_hi}]"
            )

    # 2) caifu.rank=1（官杀库 = 亿级）但 wealth_ceiling != 巨富/大富 → violation
    if findings.caifu and findings.caifu.rank == 1 and not (
        wc.startswith("巨富") or wc.startswith("大富")
    ):
        violations.append(
            f"caifu rank=1（官杀库=亿级）与 wealth_ceiling={wc} 不一致"
        )

    return (len(violations) == 0, violations)


# ============================================================
# Confidence 聚合（参考 06 § 三）
# ============================================================

def _posterior_to_star(p: float) -> int:
    """兼容旧私有入口；实际阈值由 engine.domain.confidence 维护。"""
    return _shared_posterior_to_star(p)


def _aggregate_confidence(evidences: list[Evidence]) -> Confidence:
    """简版多规律联立聚合（与 Track-A energy.evaluator 一致）。"""
    if not evidences:
        return Confidence(star=2, percent=0.50, posterior=0.50,
                          variance=0.083, sample_n=0)

    sorted_ev = sorted(evidences, key=lambda e: -e.weight)
    base = sorted_ev[0].weight
    margin = sum(max(0, e.weight - 0.5) * 0.15 for e in sorted_ev[1:])

    posterior = min(0.95, base + margin)

    # 同质惩罚（杨派 D2 规律全是 杨 派 → -5%）
    schools = {e.school for e in evidences}
    if len(schools) == 1:
        posterior *= 0.95
    if len(schools) >= 3:
        posterior = min(posterior + 0.03, 0.95)

    return Confidence(
        star=_posterior_to_star(posterior),
        percent=round(posterior, 3),
        posterior=round(posterior, 3),
        variance=0.05,
        sample_n=len(evidences),
    )


# ============================================================
# 主入口
# ============================================================

def match_picture(
    energy: EnergyFindings,
    parsed: Union[ParsedInput, Any],
) -> PictureFindings:
    """杨派 D2 画面合拍主入口。

    输入：
        energy: 上游 D1 EnergyFindings
        parsed: ParsedInput（本地或 preflight 适配后）

    输出：PictureFindings（完整画面 + 上游一致性校验 + 聚合 confidence）
    """
    # 适配 parsed
    if not isinstance(parsed, ParsedInput):
        parsed = adapt_parsed(parsed)

    bazi = parsed.bazi

    # 1. 五步法
    wubu_steps = run_wubu(energy, parsed)

    # 2. 天干五合
    wuhe_relations = scan_wuhe(bazi)

    # 3. 十神暗引
    anyin_results = scan_anyin(bazi, energy)

    # 4. 财富 / 官命
    caifu = compute_caifu(energy, bazi)
    guanming = compute_guanming(energy, bazi)

    # 5. 活死五行 + 行业指引
    huosi = _build_huosi_wuxing(bazi)
    huangliang_finding = wubu_steps[3].finding if len(wubu_steps) >= 4 else ""
    industry_pointers = _build_industry_pointers(
        bazi, energy, huosi, huangliang_finding
    )

    # 6. 婚姻画像（重中之重）
    marriage_picture = build_marriage_picture(energy, parsed)

    # 7. 调候改运
    tiaohou_advice = build_tiaohou_advice(energy, bazi)

    # ---- 8. 收集 evidence ----
    evidence: list[Evidence] = []
    for s in wubu_steps:
        evidence.extend(s.evidence)
    if caifu and caifu.evidence:
        evidence.extend(caifu.evidence)
    if guanming and guanming.evidence:
        evidence.extend(guanming.evidence)
    for a in anyin_results:
        evidence.extend(a.evidence)
    # 婚姻
    mp_ev = marriage_picture.get("evidence", []) if marriage_picture else []
    evidence.extend(mp_ev)
    # 五合（每条作 1 条）
    for r in wuhe_relations:
        evidence.append(Evidence(
            rule_id="M2-Y-024",
            school="杨",
            description=f"{r.pair[0]}{r.pair[1]}合化{r.化神}[{r.state}]",
            weight=0.65 if r.state == "化成" else 0.50,
        ))

    confidence = _aggregate_confidence(evidence)

    # ---- 9. 组装 PictureFindings ----
    findings = PictureFindings(
        wubu_steps=wubu_steps,
        wuhe_relations=wuhe_relations,
        anyin_results=anyin_results,
        caifu=caifu,
        guanming=guanming,
        huosi_wuxing=huosi,  # type: ignore[arg-type]
        industry_pointers=industry_pointers,
        marriage_picture=marriage_picture,
        tiaohou_advice=tiaohou_advice,
        energy_consistent=True,  # 先设 True，下方 check 修正
        energy_violations=[],
        confidence=confidence,
        evidence=evidence,
        case_id=parsed.case_id,
        upstream_hash=energy.hash(),
        debug_info={
            "wealth_ceiling_in": energy.wealth_ceiling,
            "layer_count_in": energy.layer_count,
            "muxing_qufa_in": energy.muxing_qufa,
            "industry_pointers": industry_pointers,
            "marriage_window": list(marriage_picture["初婚最佳窗口"])
            if marriage_picture and "初婚最佳窗口" in marriage_picture
            else None,
        },
    )

    # ---- 10. 上游一致性校验 ----
    consistent, violations = _check_against_energy(energy, findings)
    findings.energy_consistent = consistent
    findings.energy_violations = violations
    if not consistent:
        # confidence 降级
        findings.confidence = Confidence(
            star=max(1, findings.confidence.star - 1),
            percent=max(0, findings.confidence.percent - 0.10),
            posterior=max(0, findings.confidence.posterior - 0.10),
            variance=findings.confidence.variance,
            sample_n=findings.confidence.sample_n,
        )

    # ---- 11. F5 · 计算 15 层富贵分级（学/职/婚/财/官 五维）----
    try:
        from engine.picture.wealth_15tier import compute_wealth_15tier
        findings.wealth_15tier = compute_wealth_15tier(energy, findings)
    except Exception as e:  # noqa: BLE001
        # 不阻断主流程：失败时 wealth_15tier 留 None
        findings.debug_info["wealth_15tier_error"] = str(e)

    return findings


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
        pf = match_picture(energy, parsed)
        print(f"\n=== {cid} match_picture 结果 ===")
        print(f"  wealth_ceiling(D1) = {energy.wealth_ceiling}")
        print(f"  caifu rank={pf.caifu.rank} ({pf.caifu.type})")
        print(f"  guanming = {pf.guanming.type if pf.guanming else 'None'}")
        print(f"  industry_pointers = {pf.industry_pointers}")
        if pf.marriage_picture:
            print(f"  marriage_picture.初婚最佳窗口 = "
                  f"{pf.marriage_picture['初婚最佳窗口']}")
            print(f"  marriage_picture.早婚信号 = "
                  f"{pf.marriage_picture['早婚信号']}")
        print(f"  energy_consistent = {pf.energy_consistent}")
        if pf.energy_violations:
            print(f"  ⚠ violations: {pf.energy_violations}")
        print(f"  upstream_hash = {pf.upstream_hash}")
        print(f"  ★{pf.confidence.star} ({pf.confidence.percent:.0%}, "
              f"{len(pf.evidence)} evidences)")

        # round-trip
        s = pf.to_json()
        pf2 = PictureFindings.from_json(s)
        assert pf.to_dict() == pf2.to_dict()

    print("\n[OK] match_picture smoke 通过")


if __name__ == "__main__":  # pragma: no cover
    _smoke()
