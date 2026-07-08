"""L1 流派适用性路由最小实现。

先决定哪些流派有资格发言；不产生命题、不裁判。
"""

from __future__ import annotations

from engine.decision.models import ChartFactLedger, ContextFactLedger, SchoolApplicability

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
    return domains


def route_schools(chart: ChartFactLedger, context: ContextFactLedger) -> list[SchoolApplicability]:
    """生成 L1 SchoolApplicabilityMatrix。"""

    focus = _focus_domains(context)
    has_four = len([v for v in chart.four_pillars.values() if v and v != "_"]) == 4
    has_dayun = bool(chart.dayun_steps)
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
        if focus and not overlap and school not in {"ziping", "ditiansui"}:
            role = "abstain"
            blockers.append("当前分析焦点与该派初始适用域无交集。")
            score = 0.2

        if not has_four:
            blockers.append("四柱事实不完整，所有上层判断只能降级。")
            score = min(score, 0.35)

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
