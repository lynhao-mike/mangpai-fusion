"""L2 派别独立命题层最小实现。"""

from __future__ import annotations

import hashlib

from engine.decision.models import ChartFactLedger, SchoolApplicability, SchoolClaim


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]}"


def build_school_claims(case_id: str, applicability: list[SchoolApplicability], chart: ChartFactLedger) -> list[SchoolClaim]:
    """被 L1 授权的流派独立输出 SchoolClaim；不融合、不定最终结论。"""

    pillar_text = "".join(chart.four_pillars.get(key, "") for key in ("year", "month", "day", "hour")) or "四柱未完整"
    templates = {
        "ziping": ("总体", "structure", f"以四柱 {pillar_text} 建立格局、旺衰与用忌的结构命题。"),
        "ditiansui": ("总体", "structure", f"以四柱 {pillar_text} 审查寒暖燥湿与气机偏枯。"),
        "duan_jianye": ("事业", "event", "若结构审查通过，再审查事业 / 财富做功路径能否落地。"),
        "yang_qingjuan": ("婚姻", "event", "若结构审查通过，再审查婚姻人物画像与关系事件。"),
        "gao_dechen": ("健康", "evidence", "提供神煞、健康灾厄与旁证反证，不作孤证主审。"),
        "ren_fuhong": ("应期", "timing", "在事件成立后提供岁运触发与时间窗校验。"),
    }
    claims: list[SchoolClaim] = []
    for item in applicability:
        if item.role == "abstain":
            continue
        domain, claim_type, text = templates[item.school]
        claims.append(
            SchoolClaim(
                claim_id=_stable_id("dcl", case_id, item.school, domain, claim_type),
                school=item.school,
                role_granted_by_l1=item.role,
                domain=domain,
                claim_type=claim_type,
                statement=text,
                evidence_refs=["chart:four_pillars"],
                confidence=item.applicability_score,
                falsifier="若后续反馈证明该命题方向无现实对应，则回打 L2 或 L1。",
                dependencies=[f"l1:{item.school}"],
            )
        )
    return claims
