"""多专家 reading 冲突检测 application service。

本模块只消费 ``engine.domain.parallel`` 的公开外壳，不读取任何专家体系内部中间态。
"""

from __future__ import annotations

from collections import defaultdict
from typing import Sequence

from engine.domain.parallel import AdjudicationResult, CrossExpertConflict, DomainName, ExpertReading, ExpertSystem

STRONG_CONFIDENCE_THRESHOLD = 0.60
HIGH_EVIDENCE_MINORITY_THRESHOLD = 0.55
DEFAULT_CONFLICT_PENALTY = 0.04


def detect_cross_expert_conflicts(
    *,
    case_id: str,
    domain: DomainName,
    readings: Sequence[ExpertReading],
    adjudication_result: AdjudicationResult | None = None,
    strong_confidence_threshold: float = STRONG_CONFIDENCE_THRESHOLD,
) -> list[CrossExpertConflict]:
    """检测同域专家强对立、少数派与高质量证据未胜出。

    函数只读 ``readings``，不会回写或修改任何原始 ``ExpertReading``。
    """

    conflicts: list[CrossExpertConflict] = []
    supporters = [
        reading for reading in readings
        if reading.stance == "support" and reading.confidence.raw >= strong_confidence_threshold
    ]
    opposers = [
        reading for reading in readings
        if reading.stance == "oppose" and reading.confidence.raw >= strong_confidence_threshold
    ]
    if supporters and opposers:
        involved = _stable_unique([r.expert_system for r in supporters + opposers])
        strongest_support = max(supporters, key=lambda r: r.confidence.raw)
        strongest_oppose = max(opposers, key=lambda r: r.confidence.raw)
        winner, loser = _winner_loser(strongest_support, strongest_oppose)
        conflicts.append(
            CrossExpertConflict(
                conflict_id=f"CEC-{case_id}-{domain}-YESNO-001",
                domain=domain,
                involved_experts=involved,
                conflict_type="evidence",
                arbitration_reason=(
                    f"{domain}域出现 yes/no 强对立："
                    f"支持方 {', '.join(r.expert_system for r in supporters)}；"
                    f"反对方 {', '.join(r.expert_system for r in opposers)}。"
                    "已进入裁判 penalty 与少数派保留。"
                ),
                winner=winner,
                loser=loser,
                output_strategy="parallel" if winner is None else "primary_with_minority",
            )
        )

    if adjudication_result is not None:
        conflicts.extend(
            _detect_adjudicated_minority_conflicts(
                case_id,
                domain,
                readings,
                adjudication_result,
                len(conflicts),
            )
        )
    return conflicts


def conflict_penalties_from_conflicts(
    conflicts: Sequence[CrossExpertConflict],
    *,
    penalty: float = DEFAULT_CONFLICT_PENALTY,
) -> dict[ExpertSystem, float]:
    """把冲突 severity 折算为 ``adjudicate_domain`` 的 penalty 输入。"""

    penalties: defaultdict[ExpertSystem, float] = defaultdict(float)
    for conflict in conflicts:
        severity = conflict_severity(conflict)
        resolved = penalty * severity
        for expert_system in conflict.involved_experts:
            penalties[expert_system] += resolved
    return {expert: round(value, 6) for expert, value in penalties.items()}


def conflict_severity(conflict: CrossExpertConflict) -> float:
    """返回冲突严重度倍率。"""

    if conflict.output_strategy == "parallel":
        return 1.5
    if conflict.winner is None:
        return 1.25
    if conflict.conflict_type == "scope":
        return 0.75
    return 1.0


def _detect_adjudicated_minority_conflicts(
    case_id: str,
    domain: DomainName,
    readings: Sequence[ExpertReading],
    adjudication_result: AdjudicationResult,
    offset: int,
) -> list[CrossExpertConflict]:
    winner_experts = set(
        adjudication_result.winning_experts
        if adjudication_result.decision == "yes"
        else adjudication_result.dissenting_experts
    )
    if not winner_experts:
        return []
    losers = [
        reading for reading in readings
        if reading.expert_system not in winner_experts
        and reading.stance in {"support", "oppose", "mixed", "timing_only"}
        and (
            reading.confidence.raw >= STRONG_CONFIDENCE_THRESHOLD
            or _has_high_quality_evidence(reading)
        )
    ]
    conflicts: list[CrossExpertConflict] = []
    winner = sorted(winner_experts)[0]
    for index, reading in enumerate(losers, start=offset + 1):
        conflict_type = "scope" if reading.stance in {"mixed", "timing_only"} else "evidence"
        reason = "高置信少数派" if reading.confidence.raw >= STRONG_CONFIDENCE_THRESHOLD else "证据质量高但未胜出"
        conflicts.append(
            CrossExpertConflict(
                conflict_id=f"CEC-{case_id}-{domain}-MINORITY-{index:03d}",
                domain=domain,
                involved_experts=_stable_unique([winner, reading.expert_system]),
                conflict_type=conflict_type,
                arbitration_reason=(
                    f"{domain}域保留{reason}：{reading.expert_system} 未成为主胜方，"
                    f"但 confidence={reading.confidence.raw:.2f} 且证据链达到保留阈值。"
                ),
                winner=winner,
                loser=reading.expert_system,
                output_strategy="primary_with_minority",
            )
        )
    return conflicts


def _has_high_quality_evidence(reading: ExpertReading) -> bool:
    high_items = [item for item in reading.evidence_items if item.strength == "high"]
    return bool(high_items) and reading.confidence.raw >= HIGH_EVIDENCE_MINORITY_THRESHOLD


def _winner_loser(support: ExpertReading, oppose: ExpertReading) -> tuple[ExpertSystem | None, ExpertSystem | None]:
    delta = support.confidence.raw - oppose.confidence.raw
    if abs(delta) < 0.05:
        return None, None
    if delta > 0:
        return support.expert_system, oppose.expert_system
    return oppose.expert_system, support.expert_system


def _stable_unique(items: Sequence[ExpertSystem]) -> list[ExpertSystem]:
    seen: set[ExpertSystem] = set()
    out: list[ExpertSystem] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out
