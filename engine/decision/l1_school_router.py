"""L1 流派适用性路由最小实现。

先决定哪些流派有资格发言；不产生命题、不裁判。
"""

from __future__ import annotations

from collections import Counter

from engine.decision.models import ChartFactLedger, ContextFactLedger, SchoolApplicability

_ROLE_LADDER = ("lead", "co_lead", "evidence_only", "abstain")
_PRIOR_MIN_SAMPLE = 5
_PRIOR_LOW_HIT_RATE = 0.35
_PRIOR_SCORE_PENALTY = 0.2


def _downgrade_role(role: str) -> str:
    try:
        idx = _ROLE_LADDER.index(role)
    except ValueError:
        return role
    return _ROLE_LADDER[min(idx + 1, len(_ROLE_LADDER) - 1)]


def _apply_learned_prior(
    school: str,
    role: str,
    score: float,
    learned_prior: dict[str, tuple[float, int]] | None,
) -> tuple[str, float, list[str]]:
    if not learned_prior or school not in learned_prior:
        return role, score, []
    hit_rate, sample_n = learned_prior[school]
    if sample_n < _PRIOR_MIN_SAMPLE or hit_rate >= _PRIOR_LOW_HIT_RATE:
        return role, score, []
    return (
        _downgrade_role(role),
        max(0.0, round(score - _PRIOR_SCORE_PENALTY, 3)),
        [f"学习先验：该派历史命中率 {hit_rate}（样本 {sample_n}）偏低，下调路由角色。"],
    )


def _chart_signals(chart: ChartFactLedger) -> dict[str, object]:
    """只从 four_pillars 派生结构信号。"""

    from engine.predicates.ganzhi import gan_to_wuxing, is_gan, is_zhi, zhi_to_wuxing
    from engine.predicates.relations import zhi_chong

    gans: list[str] = []
    zhis: list[str] = []
    for value in chart.four_pillars.values():
        text = (value or "").strip()
        if len(text) >= 2 and is_gan(text[0]) and is_zhi(text[1]):
            gans.append(text[0])
            zhis.append(text[1])

    elements = [gan_to_wuxing(g) for g in gans] + [zhi_to_wuxing(z) for z in zhis]
    distribution = Counter(elements)
    missing_count = len({"木", "火", "土", "金", "水"} - set(distribution))
    total = len(elements)
    dominant = max(distribution.values()) if distribution else 0

    return {
        "complete": len(gans) == 4,
        "skewed": bool(total and (dominant / total >= 0.5 or missing_count >= 2)),
        "missing_count": missing_count,
        "has_chong": any(zhi_chong(zhis[i], zhis[j]) for i in range(len(zhis)) for j in range(i + 1, len(zhis))),
    }


SCHOOL_PROFILES: dict[str, dict[str, object]] = {
    "ziping": {
        "domains": ["事业", "财富", "学业", "总体"],
        "reason": "子平类适合格局、旺衰、用忌与结构层级审查。",
    },
    "ditiansui": {
        "domains": ["总体", "事业", "健康"],
        "reason": "滴天髓类适合气势、寒暖燥湿、调候与全局气机。",
    },
    "duan_jianye": {
        "domains": ["事业", "财富"],
        "reason": "段建业适合做功路径、体用宾主与财富事业落地。",
    },
    "yang_qingjuan": {
        "domains": ["婚姻", "家庭", "性格"],
        "reason": "杨清娟适合婚姻、人物画像、暗合与取象细节。",
    },
    "ren_fuhong": {
        "domains": ["应期", "事业", "婚姻", "健康"],
        "reason": "任付红适合岁运触发、时间窗与应期验证。",
    },
    "gao_dechen": {
        "domains": ["健康", "灾厄", "学业", "总体"],
        "reason": "高德臣适合神煞、健康灾厄、学业子女与旁证补强。",
    },
}


def _focus_domains(context: ContextFactLedger) -> set[str]:
    text = f"{context.analysis_focus_text}\n{context.known_fact_text}"
    domains = {domain for domain in ("学业", "事业", "财富", "婚姻", "健康", "性格") if domain in text}
    if any(token in text for token in ("工作", "职业", "升迁", "岗位")):
        domains.add("事业")
    if any(token in text for token in ("钱", "收入", "资产", "破财")):
        domains.add("财富")
    if any(token in text for token in ("结婚", "离婚", "配偶", "感情")):
        domains.add("婚姻")
    if any(token in text for token in ("身体", "疾病", "生病", "病灾")):
        domains.add("健康")
    return domains


def route_schools(
    chart: ChartFactLedger,
    context: ContextFactLedger,
    *,
    learned_prior: dict[str, tuple[float, int]] | None = None,
) -> list[SchoolApplicability]:
    """生成 L1 SchoolApplicabilityMatrix。"""

    focus = _focus_domains(context)
    has_four = len([v for v in chart.four_pillars.values() if v and v != "_"]) == 4
    has_dayun = bool(chart.dayun_steps)
    signals = _chart_signals(chart)
    result: list[SchoolApplicability] = []

    for school, profile in SCHOOL_PROFILES.items():
        domains = [str(item) for item in profile["domains"]]  # type: ignore[index]
        overlap = focus.intersection(domains)
        reasons = [str(profile["reason"])]
        blockers: list[str] = []
        score = 0.55 + 0.1 * min(2, len(overlap))
        role = "co_lead"

        if school in {"ziping", "ditiansui"}:
            role = "lead" if has_four else "evidence_only"
        if school == "ren_fuhong" and not has_dayun:
            role = "evidence_only"
            blockers.append("缺少大运 / 流年节点，不能单独主审应期。")
            score -= 0.2
        if school == "gao_dechen":
            role = "evidence_only"
            reasons.append("神煞与旁证不能孤证主审大结论。")
        if signals["skewed"] and school == "ditiansui":
            score += 0.1
            reasons.append("五行偏枯或缺行明显，调候气势派更适用。")
        if signals["has_chong"] and signals["complete"] and school in {"duan_jianye", "ren_fuhong"}:
            score += 0.05
            if role == "co_lead":
                role = "lead"
            reasons.append("地支见冲，做功 / 应期派可主审事件触发。")
        if focus and not overlap and school not in {"ziping", "ditiansui"}:
            role = "abstain"
            blockers.append("当前分析焦点与该派初始适用域无交集。")
            score = 0.2

        if not has_four:
            if role != "abstain":
                role = "evidence_only"
            blockers.append("四柱事实不完整，所有上层判断只能降级。")
            score = min(score, 0.35)

        role, score, prior_reasons = _apply_learned_prior(school, role, score, learned_prior)
        reasons += prior_reasons

        result.append(
            SchoolApplicability(
                school=school,
                role=role,  # type: ignore[arg-type]
                applicable_domains=domains,
                applicability_score=round(max(0.0, min(1.0, score)), 3),
                reasons=reasons,
                blockers=blockers,
                confidence=0.55 if not blockers else 0.4,
                falsifier="若该派在相同命盘结构、领域、事件类型中连续失验，则下调路由角色。",
            )
        )
    return result
