"""多专家功能域裁判模型旁路实现。

本模块只消费各流派已经公开的 ExpertReading 外壳，不能读取或修改任一流派
内部中间态。它为子平、滴天髓、盲派专家组的并行功能域分析提供最小
可测试裁判骨架。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from engine.domain.parallel import (
    AdjudicationDecision,
    AdjudicationResult,
    ArbitrationReason,
    Ballot,
    ConsensusLayer,
    DomainConsensus,
    DomainName,
    EvidenceItem,
    ExpertJudgement,
    ExpertReading,
    ExpertSystem,
    MinorityView,
    OutputStrategy,
    ParallelConfidence,
    WeightProfile,
)

DEFAULT_WEIGHT_PROFILE_SOURCE = "theory/raw/yaml/domain_weight_profile_2026-06-05.yaml"
DEFAULT_WEIGHT_PROFILE_PATH = Path(DEFAULT_WEIGHT_PROFILE_SOURCE)
DEFAULT_WEIGHT_PROFILE_STATUS = "review_draft"
DEFAULT_EXPERT_SYSTEMS: tuple[ExpertSystem, ...] = ("blind", "ziping", "tiaohou_ditiansui")


@dataclass(frozen=True)
class AdjudicationConfig:
    """裁判模型最小配置。"""

    support_threshold: float = 0.03
    no_output_threshold: float = 0.01
    conflict_penalty: float = 0.0
    feedback_weight: float = 1.0


def build_weight_profile(
    domain: DomainName,
    *,
    weights_by_domain: Mapping[str, Mapping[str, float]] | None = None,
    profile_id: str | None = None,
    profile_version: str | None = None,
    source: str | None = None,
    workspace_root: str | Path = ".",
) -> WeightProfile:
    """构造本次裁判使用的领域权重版本。"""

    if weights_by_domain is None:
        payload = load_domain_weight_profile_payload(workspace_root=workspace_root)
        source_weights = payload["weights"]
        resolved_profile_id = str(payload["profile_id"])
        resolved_profile_version = str(payload["profile_version"])
        resolved_source = DEFAULT_WEIGHT_PROFILE_SOURCE
    else:
        source_weights = weights_by_domain
        resolved_profile_id = profile_id or "inline-domain-prior"
        resolved_profile_version = profile_version or "inline"
        resolved_source = source or "inline"

    domain_weights = source_weights.get(domain)
    if not domain_weights:
        domain_weights = {expert: 1 / len(DEFAULT_EXPERT_SYSTEMS) for expert in DEFAULT_EXPERT_SYSTEMS}
    normalized = _normalize_weights(domain_weights)
    return WeightProfile(
        profile_id=profile_id or resolved_profile_id,
        profile_version=profile_version or resolved_profile_version,
        source=source or resolved_source,
        domain_weights=normalized,
    )


def load_domain_weight_profile_payload(*, workspace_root: str | Path = ".") -> dict[str, Any]:
    """只读加载旁路领域权重 YAML。"""

    path = (Path(workspace_root) / DEFAULT_WEIGHT_PROFILE_PATH).resolve()
    root = Path(workspace_root).resolve()
    try:
        path.relative_to((root / "theory" / "raw" / "yaml").resolve())
    except ValueError as exc:
        raise ValueError(f"领域权重 profile 只能读取 theory/raw/yaml 下的文件：{path}") from exc
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"领域权重 profile 顶层必须是 mapping：{path}")
    if raw.get("status") != DEFAULT_WEIGHT_PROFILE_STATUS:
        raise ValueError(f"领域权重 profile status 必须为 review_draft，实际为 {raw.get('status')!r}")
    weights = raw.get("weights")
    if not isinstance(weights, dict):
        raise ValueError("领域权重 profile 缺少 weights mapping。")
    for domain, domain_weights in weights.items():
        if not isinstance(domain_weights, dict):
            raise ValueError(f"{domain} 权重必须是 mapping。")
        missing = set(DEFAULT_EXPERT_SYSTEMS) - set(domain_weights)
        if missing:
            raise ValueError(f"{domain} 缺少专家权重：{sorted(missing)}")
        total = sum(float(domain_weights[expert]) for expert in DEFAULT_EXPERT_SYSTEMS)
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"{domain} 权重和必须为 1.0，实际为 {total:.6f}")
    return raw


def adjudicate_domain(
    *,
    case_id: str,
    domain: DomainName,
    readings: Sequence[ExpertReading],
    claim: str | None = None,
    weight_profile: WeightProfile | None = None,
    config: AdjudicationConfig | None = None,
) -> AdjudicationResult:
    """对一个功能域的一组专家 reading 做最小加权裁判。"""

    cfg = config or AdjudicationConfig()
    profile = weight_profile or build_weight_profile(domain)
    main_claim = claim or _select_claim(readings)
    judgements = [
        _judge_reading(
            reading,
            index=index,
            claim=main_claim,
            weight_profile=profile,
            config=cfg,
        )
        for index, reading in enumerate(readings, start=1)
    ]

    support_score = sum(j.adjusted_score for j in judgements if j.ballot == "yes")
    oppose_score = sum(j.adjusted_score for j in judgements if j.ballot == "no")
    abstained: list[ExpertSystem] = [j.expert_system for j in judgements if j.ballot == "abstain"]
    winning_experts: list[ExpertSystem] = [j.expert_system for j in judgements if j.ballot == "yes"]
    dissenting_experts: list[ExpertSystem] = [j.expert_system for j in judgements if j.ballot == "no"]
    decision = _decide(support_score, oppose_score, judgements, cfg)
    raw_confidence = _bounded(abs(support_score - oppose_score) + max(support_score, oppose_score))
    confidence = _confidence_from_score(
        raw_confidence,
        reason=_confidence_reason(decision, winning_experts, dissenting_experts, abstained),
    )
    minority_views = _build_minority_views(readings, decision)
    arbitration_reason = _build_arbitration_reason(
        decision=decision,
        support_score=support_score,
        oppose_score=oppose_score,
        winning_experts=winning_experts,
        dissenting_experts=dissenting_experts,
        minority_views=minority_views,
    )

    return AdjudicationResult(
        adjudication_id=f"ADJ-{case_id}-{domain}",
        domain=domain,
        claim=main_claim,
        decision=decision,
        judgements=judgements,
        support_score=round(support_score, 6),
        oppose_score=round(oppose_score, 6),
        confidence=confidence,
        weight_profile=profile,
        winning_experts=winning_experts,
        dissenting_experts=dissenting_experts,
        abstained_experts=abstained,
        minority_views=minority_views,
        arbitration_reason=arbitration_reason,
        feedback_state="pending",
    )


def build_domain_consensus(
    *,
    case_id: str,
    domain: DomainName,
    readings: Sequence[ExpertReading],
    adjudication: AdjudicationResult,
) -> DomainConsensus:
    """把裁判结果转成报告层可读的功能域共识。"""

    layer = _consensus_layer(adjudication, len(readings))
    visible_evidence = _collect_evidence(readings)
    output_strategy = (
        adjudication.arbitration_reason.output_strategy
        if adjudication.arbitration_reason
        else "primary_only"
    )
    final_statement = _final_statement(adjudication)
    return DomainConsensus(
        conclusion_id=f"PDC-{case_id}-{domain}",
        domain=domain,
        headline=f"{domain}域多专家裁判：{layer}",
        final_statement=final_statement,
        layer=layer,
        contributing_experts=list(adjudication.winning_experts),
        dissenting_experts=list(adjudication.dissenting_experts),
        confidence=adjudication.confidence,
        evidence_items=visible_evidence,
        falsifiable=_select_falsifiable(readings),
        feedback_state=adjudication.feedback_state,
        weight_profile=adjudication.weight_profile,
        minority_views=list(adjudication.minority_views),
        arbitration_reason=adjudication.arbitration_reason,
        output_strategy=output_strategy,
    )


def _judge_reading(
    reading: ExpertReading,
    *,
    index: int,
    claim: str,
    weight_profile: WeightProfile,
    config: AdjudicationConfig,
) -> ExpertJudgement:
    ballot = _ballot_from_stance(reading.stance)
    raw_score = _raw_score_from_ballot(ballot, reading.confidence.raw)
    prior_domain_weight = weight_profile.domain_weights.get(reading.expert_system, 0.0)
    confidence_weight = _bounded(reading.confidence.raw)
    evidence_quality_weight = _evidence_quality_weight(reading.evidence_items)
    conflict_penalty = config.conflict_penalty if ballot in {"yes", "no"} else 0.0
    adjusted_score = (
        raw_score
        * prior_domain_weight
        * confidence_weight
        * config.feedback_weight
        * evidence_quality_weight
        - conflict_penalty
    )
    adjusted_score = max(0.0, adjusted_score)
    return ExpertJudgement(
        judgement_id=f"JDG-{reading.reading_id}-{index}",
        reading_id=reading.reading_id,
        expert_system=reading.expert_system,
        domain=reading.domain,
        claim=claim,
        ballot=ballot,
        raw_score=round(raw_score, 6),
        prior_domain_weight=round(prior_domain_weight, 6),
        confidence_weight=round(confidence_weight, 6),
        feedback_weight=round(config.feedback_weight, 6),
        evidence_quality_weight=round(evidence_quality_weight, 6),
        conflict_penalty=round(conflict_penalty, 6),
        adjusted_score=round(adjusted_score, 6),
        rationale=(
            f"{reading.expert_system} 在 {reading.domain} 域以 {reading.stance} 进入裁判；"
            f"先验权重 {prior_domain_weight:.2f}。"
        ),
    )


def _normalize_weights(weights: Mapping[str, float]) -> dict[ExpertSystem, float]:
    total = sum(float(weights.get(expert, 0.0)) for expert in DEFAULT_EXPERT_SYSTEMS)
    if total <= 0:
        return {expert: 1 / len(DEFAULT_EXPERT_SYSTEMS) for expert in DEFAULT_EXPERT_SYSTEMS}
    return {expert: float(weights.get(expert, 0.0)) / total for expert in DEFAULT_EXPERT_SYSTEMS}


def _select_claim(readings: Sequence[ExpertReading]) -> str:
    for reading in readings:
        if reading.stance not in {"abstain", "timing_only"} and reading.claim:
            return reading.claim
    for reading in readings:
        if reading.claim:
            return reading.claim
    return "本功能域暂无可裁判主命题"


def _ballot_from_stance(stance: str) -> Ballot:
    if stance == "support":
        return "yes"
    if stance == "oppose":
        return "no"
    if stance == "mixed":
        return "mixed"
    return "abstain"


def _raw_score_from_ballot(ballot: Ballot, confidence: float) -> float:
    if ballot in {"yes", "no"}:
        return _bounded(confidence)
    if ballot == "mixed":
        return _bounded(confidence) * 0.5
    return 0.0


def _evidence_quality_weight(evidence_items: Sequence[EvidenceItem]) -> float:
    if not evidence_items:
        return 0.70
    values = {"high": 1.0, "medium": 0.85, "low": 0.65}
    score = sum(values.get(item.strength, 0.85) for item in evidence_items) / len(evidence_items)
    if len(evidence_items) >= 2:
        score += 0.05
    return _bounded(score)


def _decide(
    support_score: float,
    oppose_score: float,
    judgements: Sequence[ExpertJudgement],
    config: AdjudicationConfig,
) -> AdjudicationDecision:
    active = [j for j in judgements if j.ballot in {"yes", "no", "mixed"}]
    if not active or max(support_score, oppose_score) < config.no_output_threshold:
        return "no_output"
    delta = support_score - oppose_score
    if delta > config.support_threshold:
        return "yes"
    if delta < -config.support_threshold:
        return "no"
    return "mixed"


def _confidence_from_score(score: float, *, reason: str) -> ParallelConfidence:
    percent = int(round(_bounded(score) * 100))
    if percent >= 85:
        star = 5
    elif percent >= 70:
        star = 4
    elif percent >= 50:
        star = 3
    elif percent >= 30:
        star = 2
    else:
        star = 1
    return ParallelConfidence(
        raw=_bounded(score),
        merged=_bounded(score),
        feedback_adjusted=None,
        star=star,
        percent=percent,
        reason=reason,
    )


def _confidence_reason(
    decision: AdjudicationDecision,
    winning_experts: Sequence[ExpertSystem],
    dissenting_experts: Sequence[ExpertSystem],
    abstained_experts: Sequence[ExpertSystem],
) -> str:
    if decision == "no_output":
        return "有效专家 reading 不足，按旁路模型不输出。"
    if decision == "mixed":
        return "多专家得分接近，保留冲突或并列表达。"
    return (
        f"胜出专家：{', '.join(winning_experts) or '无'}；"
        f"反对专家：{', '.join(dissenting_experts) or '无'}；"
        f"弃权专家：{', '.join(abstained_experts) or '无'}。"
    )


def _build_minority_views(
    readings: Sequence[ExpertReading],
    decision: AdjudicationDecision,
) -> list[MinorityView]:
    if decision not in {"yes", "no", "mixed"}:
        return []
    minority: list[MinorityView] = []
    for reading in readings:
        if decision == "yes" and reading.stance == "oppose":
            minority.append(_minority_from_reading(reading, "与主胜方方向相反，按少数派保留。"))
        elif decision == "no" and reading.stance == "support":
            minority.append(_minority_from_reading(reading, "支持方未胜出，但保留其证据链。"))
        elif reading.stance in {"mixed", "timing_only"}:
            minority.append(_minority_from_reading(reading, "该 reading 提供边界或时间层补充。"))
    return minority


def _minority_from_reading(reading: ExpertReading, reason: str) -> MinorityView:
    return MinorityView(
        expert_system=reading.expert_system,
        claim=reading.claim,
        reason_to_preserve=reason,
        confidence=reading.confidence.raw,
        output_visibility="report_note",
    )


def _build_arbitration_reason(
    *,
    decision: AdjudicationDecision,
    support_score: float,
    oppose_score: float,
    winning_experts: Sequence[ExpertSystem],
    dissenting_experts: Sequence[ExpertSystem],
    minority_views: Sequence[MinorityView],
) -> ArbitrationReason:
    if decision == "no_output":
        return ArbitrationReason(
            winner_reason="无足够有效 reading，按显式弃权原则不输出。",
            conflict_type="none",
            output_strategy="downgraded",
        )
    if decision == "mixed":
        return ArbitrationReason(
            winner_reason="支持与反对得分接近，不做机械多数决。",
            loser_reason="无明确败方。",
            conflict_type="evidence",
            output_strategy="parallel",
        )
    output_strategy: OutputStrategy = "primary_with_minority" if minority_views else "primary_only"
    winner = ", ".join(winning_experts) if decision == "yes" else ", ".join(dissenting_experts)
    loser = ", ".join(dissenting_experts) if decision == "yes" else ", ".join(winning_experts)
    return ArbitrationReason(
        winner_reason=(
            f"{winner or '主胜方'} 加权得分胜出；"
            f"support={support_score:.3f}, oppose={oppose_score:.3f}。"
        ),
        loser_reason=f"{loser or '无明确败方'} 未达到胜出得分。",
        conflict_type="evidence" if minority_views else "none",
        output_strategy=output_strategy,
    )


def _consensus_layer(adjudication: AdjudicationResult, reading_count: int) -> ConsensusLayer:
    if adjudication.decision == "no_output":
        return "不输出"
    if adjudication.decision == "mixed":
        return "冲突保留"
    winners = len(set(adjudication.winning_experts if adjudication.decision == "yes" else adjudication.dissenting_experts))
    active = reading_count - len(adjudication.abstained_experts)
    if winners >= 3:
        return "多专家共识"
    if winners == 2:
        return "双专家共识"
    if active == 1:
        return "独门"
    if adjudication.minority_views:
        return "主专家胜出"
    return "主专家胜出"


def _collect_evidence(readings: Sequence[ExpertReading]) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    for reading in readings:
        evidence.extend(reading.evidence_items)
    return evidence


def _select_falsifiable(readings: Sequence[ExpertReading]) -> str:
    for reading in readings:
        if reading.falsifiable:
            return reading.falsifiable
    return "后续反馈若与本域主断语相反，则应记录为 miss 或 partial。"


def _final_statement(adjudication: AdjudicationResult) -> str:
    if adjudication.decision == "no_output":
        return "当前多专家旁路模型未获得足够有效 reading，本域不输出确定断语。"
    if adjudication.decision == "mixed":
        return f"{adjudication.claim}；但多专家意见存在接近冲突，需并列保留。"
    if adjudication.decision == "no":
        return f"裁判层暂不支持：{adjudication.claim}。"
    return adjudication.claim


def _bounded(value: float) -> float:
    return max(0.0, min(float(value), 1.0))
