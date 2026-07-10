"""L4 事件落地层最小实现。"""

from __future__ import annotations

import hashlib

from engine.decision.models import EventHypothesis, SchoolClaim, StructuralVerdict


def _stable_id(prefix: str, *parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]}"


# 从已有事件命题文本分类的启发式映射，不从命局结构推导事件。
_EVENT_TYPE_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("车祸", ("车祸", "交通", "撞")),
    ("手术", ("手术", "开刀")),
    ("疾病", ("疾病", "病", "体检", "慢病", "伤病", "健康问题")),
    ("婚变", ("离婚", "再婚", "晚婚", "多婚", "婚变", "分手")),
    ("结婚", ("结婚", "婚姻", "配偶", "婚恋", "成家")),
    ("发财", ("发财", "暴富", "冲开", "财库")),
    ("破财", ("破财", "亏损", "负债", "支出压力", "损失")),
    ("升迁", ("升迁", "升职", "职级", "提拔")),
    ("换岗", ("换岗", "调动", "岗位", "组织关系")),
    ("创业", ("创业", "自主", "合伙", "开业")),
    ("学历", ("学历", "考试", "证照", "培训", "技能升级", "学位")),
]

_DOMAIN_GENERIC_EVENT: dict[str, str] = {
    "事业": "事业变动",
    "财富": "财务变动",
    "婚姻": "婚恋变动",
    "健康": "健康风险",
    "学业": "学习节点",
}


def classify_event_type(event_label: str, domain: str) -> str:
    """把已有事件命题的字符串语义归为事件标签。"""

    text = event_label or ""
    for event_type, keywords in _EVENT_TYPE_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return event_type
    return _DOMAIN_GENERIC_EVENT.get(domain, "待具体化事件")


def build_event_hypotheses(case_id: str, verdicts: list[StructuralVerdict], claims: list[SchoolClaim]) -> list[EventHypothesis]:
    """把已有且通过自身结构审查的事件命题落成可反馈事件。"""

    supported_verdict_by_claim = {
        verdict.claim_id: verdict
        for verdict in verdicts
        if verdict.verdict in {"pass", "weaken"}
    }
    event_claims = [
        claim
        for claim in claims
        if claim.claim_type in {"event", "event_claim"}
        and claim.role_granted_by_l1 != "evidence_only"
        and claim.claim_id in supported_verdict_by_claim
    ]
    return [
        EventHypothesis(
            event_id=_stable_id("dev", case_id, claim.claim_id),
            source_verdict_ids=[supported_verdict_by_claim[claim.claim_id].verdict_id],
            domain=claim.domain,
            event_type=classify_event_type(claim.statement, claim.domain),
            subject=claim.school,
            concrete_event=claim.statement,
            landing_path="L4 只把通过自身结构审查的已有事件命题落成现实事件。",
            confidence=min(0.65, claim.confidence),
        )
        for claim in event_claims[:2]
    ]
