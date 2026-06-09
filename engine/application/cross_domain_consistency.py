"""跨功能域一致性 application service。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Sequence

from engine.domain.parallel import DomainAnalysis, DomainName

ConsistencySeverity = Literal["warning", "arbitration_note"]


@dataclass(frozen=True)
class CrossDomainConsistencyNote:
    """跨域一致性提示，可进入报告与 statement_index。"""

    note_id: str
    domains: list[DomainName]
    severity: ConsistencySeverity
    message: str
    arbitration_note: str
    source: str = "engine.application.cross_domain_consistency"
    related_adjudication_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "note_id": self.note_id,
            "domains": list(self.domains),
            "severity": self.severity,
            "message": self.message,
            "arbitration_note": self.arbitration_note,
            "source": self.source,
            "related_adjudication_ids": list(self.related_adjudication_ids),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CrossDomainConsistencyNote":
        return cls(
            note_id=str(data["note_id"]),
            domains=list(data.get("domains", [])),
            severity=data.get("severity", "warning"),
            message=str(data.get("message", "")),
            arbitration_note=str(data.get("arbitration_note", "")),
            source=str(data.get("source", "engine.application.cross_domain_consistency")),
            related_adjudication_ids=[str(x) for x in data.get("related_adjudication_ids", [])],
        )


def evaluate_cross_domain_consistency(
    analyses: Sequence[DomainAnalysis],
    *,
    case_id: str,
) -> list[CrossDomainConsistencyNote]:
    """根据并行功能域裁判结果生成跨域 warning / arbitration note。"""

    by_domain: dict[DomainName, DomainAnalysis] = {analysis.domain: analysis for analysis in analyses}
    notes: list[CrossDomainConsistencyNote] = []

    notes.extend(_career_strong_wealth_weak(case_id, by_domain))
    notes.extend(_career_wealth_institutional_coupling(case_id, by_domain))
    notes.extend(_marriage_conflict_without_personality_explanation(case_id, by_domain))
    notes.extend(_health_high_risk_without_time_scope(case_id, by_domain))
    notes.extend(_marriage_conflict_health_high_risk(case_id, by_domain))
    return notes


def _career_strong_wealth_weak(case_id: str, by_domain: dict[DomainName, DomainAnalysis]) -> list[CrossDomainConsistencyNote]:
    career = by_domain.get("事业")
    wealth = by_domain.get("财运")
    if career is None or wealth is None:
        return []
    career_yes = career.adjudication_result.decision == "yes" and career.adjudication_result.confidence.percent >= 70
    wealth_weak = wealth.adjudication_result.decision in {"no", "mixed"} or _has_negative_signal(wealth)
    if not (career_yes and wealth_weak):
        return []
    return [_note(
        case_id=case_id,
        ordinal=1,
        domains=["事业", "财运"],
        severity="warning",
        message="事业域高置信走强，但财运域偏弱或存在负向裁判，禁止直接推出高财富兑现。",
        arbitration_note="事业强应优先表述为平台/职级/职责增强；财富需另列现金流与资产兑现边界。",
        analyses=[career, wealth],
    )]


def _career_wealth_institutional_coupling(case_id: str, by_domain: dict[DomainName, DomainAnalysis]) -> list[CrossDomainConsistencyNote]:
    career = by_domain.get("事业")
    wealth = by_domain.get("财运")
    if career is None or wealth is None:
        return []
    career_text = _analysis_text(career)
    wealth_text = _analysis_text(wealth)
    institutional = any(kw in career_text for kw in ("体制", "公门", "国企", "公务员", "编制"))
    market_wealth = any(kw in wealth_text for kw in ("中富", "大富", "巨富", "小富", "资产", "财富"))
    if not (institutional and market_wealth):
        return []
    return [_note(
        case_id=case_id,
        ordinal=2,
        domains=["事业", "财运"],
        severity="arbitration_note",
        message="事业域出现体制/公门路径，财运域使用市场财富分级，需显式耦合标注。",
        arbitration_note="报告中应说明财富分级是非体制路径对照值，或改用权力层级/职级框架。",
        analyses=[career, wealth],
    )]


def _marriage_conflict_without_personality_explanation(
    case_id: str,
    by_domain: dict[DomainName, DomainAnalysis],
) -> list[CrossDomainConsistencyNote]:
    marriage = by_domain.get("婚姻")
    personality = by_domain.get("性格")
    if marriage is None:
        return []
    marriage_conflict = bool(marriage.conflicts) or marriage.adjudication_result.decision == "mixed"
    personality_text = _analysis_text(personality) if personality is not None else ""
    explained = any(kw in personality_text for kw in ("关系", "沟通", "情绪", "边界", "控制", "解释", "婚姻"))
    if not marriage_conflict or explained:
        return []
    analyses = [marriage]
    if personality is not None:
        analyses.append(personality)
    return [_note(
        case_id=case_id,
        ordinal=3,
        domains=["婚姻", "性格"] if personality is not None else ["婚姻"],
        severity="warning",
        message="婚姻域存在强冲突，但性格域未提供关系模式解释，禁止孤立输出婚姻冲突。",
        arbitration_note="报告中需补充性格/沟通/边界机制，或明确婚姻冲突只来自配偶宫与事件层证据。",
        analyses=analyses,
    )]



def _health_high_risk_without_time_scope(case_id: str, by_domain: dict[DomainName, DomainAnalysis]) -> list[CrossDomainConsistencyNote]:
    health = by_domain.get("健康")
    if health is None:
        return []
    health_text = _analysis_text(health)
    health_high_risk = health.adjudication_result.decision == "yes" and any(
        kw in health_text for kw in ("高危", "手术", "重病", "病灾", "风险")
    )
    has_time_scope = health.consensus.time_scope is not None or any(
        kw in health_text for kw in ("应期", "流年", "大运", "年份", "年内", "阶段", "时间范围")
    )
    if not health_high_risk or has_time_scope:
        return []
    return [_note(
        case_id=case_id,
        ordinal=4,
        domains=["健康"],
        severity="warning",
        message="健康域输出高危风险，但结构化 consensus 未给时间范围。",
        arbitration_note="健康高危 statement 必须补 time_scope、应期边界或明确降级为长期倾向。",
        analyses=[health],
    )]



def _marriage_conflict_health_high_risk(case_id: str, by_domain: dict[DomainName, DomainAnalysis]) -> list[CrossDomainConsistencyNote]:
    marriage = by_domain.get("婚姻")
    health = by_domain.get("健康")
    if marriage is None or health is None:
        return []
    marriage_conflict = bool(marriage.conflicts) or marriage.adjudication_result.decision == "mixed"
    health_text = _analysis_text(health)
    health_high_risk = health.adjudication_result.decision == "yes" and any(
        kw in health_text for kw in ("高危", "手术", "重病", "病灾", "风险")
    )
    if not (marriage_conflict and health_high_risk):
        return []
    return [_note(
        case_id=case_id,
        ordinal=5,
        domains=["婚姻", "健康"],
        severity="warning",
        message="婚姻域存在专家冲突，同时健康域高危，家庭事件不可与健康事件机械合并。",
        arbitration_note="输出时应拆成婚姻关系压力与健康风险两条 statement，并分别设置证伪条件。",
        analyses=[marriage, health],
    )]


def _note(
    *,
    case_id: str,
    ordinal: int,
    domains: list[DomainName],
    severity: ConsistencySeverity,
    message: str,
    arbitration_note: str,
    analyses: Sequence[DomainAnalysis],
) -> CrossDomainConsistencyNote:
    return CrossDomainConsistencyNote(
        note_id=f"CDC-{case_id}-{ordinal:03d}",
        domains=domains,
        severity=severity,
        message=message,
        arbitration_note=arbitration_note,
        related_adjudication_ids=[a.adjudication_result.adjudication_id for a in analyses],
    )


def _analysis_text(analysis: DomainAnalysis) -> str:
    parts = [analysis.consensus.final_statement, analysis.adjudication_result.claim]
    parts.extend(reading.claim for reading in analysis.readings)
    parts.extend(conflict.arbitration_reason for conflict in analysis.conflicts)
    return "\n".join(parts)


def _has_negative_signal(analysis: DomainAnalysis) -> bool:
    text = _analysis_text(analysis)
    return any(kw in text for kw in ("弱", "破", "损", "不稳", "难聚", "风险", "不支持"))
